"""Small in-memory lifecycle engine for local virtual-EV simulations."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from math import sin
from time import monotonic

import numpy as np

from app.schemas.simulation import (
    SimulatedTelemetry,
    SimulationConfig,
    SimulationEvent,
    SimulationStatus,
)
from app.services import battery_model

MAX_TELEMETRY_HISTORY = 120
SIMULATION_CYCLE_SECONDS = 1_800
DISCHARGE_SECONDS = 900
IDLE_SECONDS = 180
IDLE_CURRENT_THRESHOLD_A = 0.5

# Column order of a recorded session (the same 128 x 8 layout the model reads).
_VOLTAGE, _CURRENT, _SOC, _MAX_TEMP, _TIME = 0, 1, 2, 5, 7
# Used only if a recorded file has no usable time column.
_FALLBACK_STEP_SECONDS = 10.0


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class _Replay:
    """A recorded charging session played back as simulated telemetry."""

    session_id: str
    title: str
    seconds: np.ndarray  # strictly increasing, starts at 0
    readings: np.ndarray  # (128, 8), raw sensor values

    @property
    def total_seconds(self) -> float:
        return float(self.seconds[-1])


def _load_replay(session_id: str) -> _Replay:
    """Loads a demo session for playback.

    :raises DemoSessionNotFound: unknown or malformed id.
    :raises ModelUnavailable: the file exists but is not a valid session.
    """
    data = battery_model.load_demo_session(session_id)
    readings = np.asarray(data["readings"], dtype=float)
    seconds = readings[:, _TIME] - readings[0, _TIME]
    if not np.all(np.diff(seconds) > 0):
        seconds = np.arange(len(readings)) * _FALLBACK_STEP_SECONDS
    return _Replay(
        session_id=data["id"], title=data["title"], seconds=seconds, readings=readings
    )


@dataclass
class _Session:
    config: SimulationConfig
    status: str
    active_started_at: float
    elapsed_active_seconds: float
    started_at: str
    paused_at: str | None = None
    resumed_at: str | None = None
    stopped_at: str | None = None
    telemetry_history: list[SimulatedTelemetry] = field(default_factory=list)
    events: list[SimulationEvent] = field(default_factory=list)
    next_telemetry_real_seconds: float = 0
    battery_status: str = "normal"
    replay: _Replay | None = None


class SimulationService:
    """Owns one local session; elapsed time is derived from a monotonic clock.

    No worker loop is needed for this first version. Status polling materializes
    readings at the configured cadence; elapsed time always comes from the
    monotonic clock rather than the telemetry schedule.
    """

    def __init__(self) -> None:
        self._session: _Session | None = None
        self._last_stopped_at: str | None = None

    def start(self, config: SimulationConfig) -> SimulationStatus:
        # Load first: an unknown demo id must not destroy the session that is running.
        replay = _load_replay(config.demo_session_id) if config.demo_session_id else None
        now = monotonic()
        # Replacing the single session makes a second start deterministic and
        # avoids leaving a second local scheduler/session behind.
        self._session = _Session(
            config=config,
            status="running",
            active_started_at=now,
            elapsed_active_seconds=0,
            started_at=_timestamp(),
            replay=replay,
        )
        message = (
            f"Replaying recorded charging session: {replay.title}."
            if replay
            else "Simulation session started."
        )
        self._add_event(self._session, "session", message, 0)
        self._last_stopped_at = None
        return self.status()

    def pause(self) -> SimulationStatus:
        session = self._require_session("running")
        session.elapsed_active_seconds = self._elapsed_real(session)
        session.status = "paused"
        session.paused_at = _timestamp()
        self._record_telemetry(session, session.elapsed_active_seconds)
        self._add_event(session, "session", "Simulation session paused.", session.elapsed_active_seconds)
        return self.status()

    def resume(self) -> SimulationStatus:
        session = self._require_session("paused")
        session.status = "running"
        session.active_started_at = monotonic()
        session.resumed_at = _timestamp()
        self._add_event(session, "session", "Simulation session resumed.", session.elapsed_active_seconds)
        return self.status()

    def stop(self) -> SimulationStatus:
        self._last_stopped_at = _timestamp()
        self._session = None
        return self.status()

    def status(self) -> SimulationStatus:
        session = self._session
        if session is None:
            return SimulationStatus(status="idle", stopped_at=self._last_stopped_at)

        elapsed = self._elapsed_real(session)
        duration_seconds = self._duration_seconds(session)
        if session.status == "running" and elapsed >= duration_seconds:
            session.elapsed_active_seconds = duration_seconds
            session.status = "completed"
            session.stopped_at = _timestamp()
            elapsed = duration_seconds

        self._record_telemetry(session, elapsed)
        if session.status == "completed" and not any(
            event.message == "Simulation session completed." for event in session.events
        ):
            self._add_event(session, "session", "Simulation session completed.", elapsed)

        elapsed = min(elapsed, duration_seconds)
        return SimulationStatus(
            status=session.status,
            config=session.config,
            elapsed_real_seconds=elapsed,
            elapsed_simulated_seconds=elapsed * session.config.speed_multiplier,
            remaining_real_seconds=max(0, duration_seconds - elapsed),
            started_at=session.started_at,
            paused_at=session.paused_at,
            resumed_at=session.resumed_at,
            stopped_at=session.stopped_at,
            data_source="recorded" if session.replay else "generated",
            replay_total_seconds=session.replay.total_seconds if session.replay else None,
            latest_telemetry=session.telemetry_history[-1] if session.telemetry_history else None,
            telemetry_history=session.telemetry_history,
            events=session.events,
        )

    @staticmethod
    def _duration_seconds(session: _Session) -> float:
        """Real seconds the session runs: the configured duration, or less when
        a recorded session ends sooner (it stops when the recording ends)."""
        configured = float(session.config.duration_minutes * 60)
        if session.replay is None:
            return configured
        return min(configured, session.replay.total_seconds / session.config.speed_multiplier)

    @staticmethod
    def _elapsed_real(session: _Session) -> float:
        if session.status == "running":
            return session.elapsed_active_seconds + (monotonic() - session.active_started_at)
        return session.elapsed_active_seconds

    def _require_session(self, expected_status: str) -> _Session:
        if self._session is None or self._session.status != expected_status:
            raise ValueError(f"A simulation must be {expected_status} for this action.")
        return self._session

    def _record_telemetry(self, session: _Session, elapsed_real_seconds: float) -> None:
        """Generate all due samples, retaining a bounded history for charts."""
        interval = session.config.telemetry_interval_seconds
        while session.next_telemetry_real_seconds <= elapsed_real_seconds:
            simulated_seconds = (
                session.next_telemetry_real_seconds * session.config.speed_multiplier
            )
            if session.replay is not None:
                telemetry = self._replay_telemetry(session.config, session.replay, simulated_seconds)
            else:
                telemetry = self._telemetry_at(session.config, simulated_seconds)
            session.telemetry_history.append(telemetry)
            if len(session.telemetry_history) > MAX_TELEMETRY_HISTORY:
                session.telemetry_history.pop(0)
            self._record_threshold_event(session, telemetry)
            session.next_telemetry_real_seconds += interval

    @staticmethod
    def _telemetry_at(config: SimulationConfig, simulated_seconds: float) -> SimulatedTelemetry:
        """Generate a deterministic development-only discharge/idle/charge cycle.

        Current convention: positive values discharge the battery, negative
        values charge it, and values near zero are idle. This is a predictable
        UI test profile, not a validated EV battery-physics model.
        """
        cycle_seconds = simulated_seconds % SIMULATION_CYCLE_SECONDS
        if cycle_seconds < DISCHARGE_SECONDS:
            direction = "discharging"
            current = 42 + 3 * sin(cycle_seconds / 180)
            state_of_charge = 82 - (cycle_seconds / DISCHARGE_SECONDS) * 12
            temperature_offset = 2
        elif cycle_seconds < DISCHARGE_SECONDS + IDLE_SECONDS:
            direction = "idle"
            current = 0.0
            state_of_charge = 70
            temperature_offset = 0
        else:
            direction = "charging"
            charge_seconds = cycle_seconds - DISCHARGE_SECONDS - IDLE_SECONDS
            current = -30 - 2 * sin(charge_seconds / 180)
            state_of_charge = 70 + (charge_seconds / (SIMULATION_CYCLE_SECONDS - DISCHARGE_SECONDS - IDLE_SECONDS)) * 12
            temperature_offset = 1

        state_of_charge = min(100.0, max(0.0, state_of_charge))
        temperature = min(
            58.0,
            31 + (simulated_seconds / 3600) * 2.5 + temperature_offset + sin(simulated_seconds / 300),
        )
        voltage = min(450.0, max(300.0, 345 + state_of_charge * 0.65 - current * 0.03))
        if abs(current) <= IDLE_CURRENT_THRESHOLD_A:
            direction = "idle"
        battery_status = SimulationService._classify(config, temperature, state_of_charge)
        return SimulatedTelemetry(
            simulated_seconds=round(simulated_seconds, 1),
            state_of_charge_percent=round(state_of_charge, 1),
            voltage_v=round(voltage, 1),
            current_a=round(current, 1),
            temperature_c=round(temperature, 1),
            direction=direction,
            battery_status=battery_status,
        )

    @staticmethod
    def _classify(config: SimulationConfig, temperature: float, state_of_charge: float) -> str:
        """Maps a reading onto normal / warning / critical using the config thresholds."""
        if (
            temperature >= config.critical_temperature_c
            or state_of_charge <= config.critical_soc_percent
        ):
            return "critical"
        if (
            temperature >= config.warning_temperature_c
            or state_of_charge <= config.warning_soc_percent
        ):
            return "warning"
        return "normal"

    @staticmethod
    def _replay_telemetry(
        config: SimulationConfig, replay: _Replay, simulated_seconds: float
    ) -> SimulatedTelemetry:
        """One reading from a recorded session, interpolated at ``simulated_seconds``.

        Real dataset values: nothing is invented. Negative current is charging
        (the dataset's convention), so direction follows the current's sign.
        After the recording ends the last reading is held.
        """
        t = min(max(simulated_seconds, 0.0), replay.total_seconds)

        def at(channel: int) -> float:
            return float(np.interp(t, replay.seconds, replay.readings[:, channel]))

        current = at(_CURRENT)
        state_of_charge = min(100.0, max(0.0, at(_SOC)))
        temperature = at(_MAX_TEMP)
        if abs(current) <= IDLE_CURRENT_THRESHOLD_A:
            direction = "idle"
        else:
            direction = "charging" if current < 0 else "discharging"
        return SimulatedTelemetry(
            simulated_seconds=round(t, 1),
            state_of_charge_percent=round(state_of_charge, 1),
            voltage_v=round(at(_VOLTAGE), 3),
            current_a=round(current, 1),
            temperature_c=round(temperature, 1),
            direction=direction,
            battery_status=SimulationService._classify(config, temperature, state_of_charge),
        )

    def _record_threshold_event(self, session: _Session, telemetry: SimulatedTelemetry) -> None:
        severity = telemetry.battery_status
        if severity == session.battery_status:
            return
        if severity == "warning":
            message = "Simulated battery warning threshold reached."
        elif severity == "critical":
            message = "Simulated battery critical threshold reached."
        else:
            message = "Simulated battery readings returned to normal."
        kind = severity if severity in ("warning", "critical") else "session"
        self._add_event(session, kind, message, telemetry.simulated_seconds)
        session.battery_status = severity

    @staticmethod
    def _add_event(
        session: _Session, kind: str, message: str, simulated_seconds: float
    ) -> None:
        session.events.append(
            SimulationEvent(
                timestamp=_timestamp(),
                simulated_seconds=round(simulated_seconds, 1),
                kind=kind,
                message=message,
            )
        )


simulation_service = SimulationService()