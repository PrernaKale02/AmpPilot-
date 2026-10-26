export function getSimulationTelemetry(session) {
  return session?.latestTelemetry ?? null;
}

export function getSimulationElapsedLabel(session) {
  const totalMinutes = Math.floor((session?.elapsedSimulatedSeconds || 0) / 60);
  return `${totalMinutes} min`;
}

export function getSimulatedChargingSession(session) {
  const telemetry = getSimulationTelemetry(session);
  if (!telemetry || telemetry.direction !== "charging") return null;

  const history = session.telemetryHistory || [];
  let firstIndex = history.length - 1;
  while (firstIndex > 0 && history[firstIndex - 1].direction === "charging") {
    firstIndex -= 1;
  }
  const chargingReadings = history.slice(firstIndex);
  if (chargingReadings.length === 0) return null;

  let energyKwh = 0;
  for (let index = 1; index < chargingReadings.length; index += 1) {
    const previous = chargingReadings[index - 1];
    const current = chargingReadings[index];
    const elapsedSeconds = current.simulatedSeconds - previous.simulatedSeconds;
    const averagePower =
      (Math.abs(previous.voltageV * previous.currentA) +
        Math.abs(current.voltageV * current.currentA)) /
      2;
    energyKwh += (averagePower * elapsedSeconds) / 3_600_000;
  }

  const firstReading = chargingReadings[0];
  const lastReading = chargingReadings[chargingReadings.length - 1];
  return {
    id: `simulation-${session.startedAt || "session"}`,
    date: session.startedAt || new Date().toISOString(),
    startSoc: Math.round(firstReading.stateOfChargePercent),
    endSoc: Math.round(lastReading.stateOfChargePercent),
    durationMinutes: Math.max(
      1,
      Math.round(
        (lastReading.simulatedSeconds - firstReading.simulatedSeconds) / 60,
      ),
    ),
    energyAddedKwh: Math.round(energyKwh * 10) / 10,
    location: "Virtual EV",
    chargerType: "Simulated",
  };
}

/**
 * Short, unambiguous label for a recorded demo car. Titles repeat ("Faulty car
 * (dataset 1)" for two different cars), so the label is built from the id.
 *
 * @param {{id: string, title?: string}} demoSession
 * @returns {string}
 */
export function demoSessionLabel(demoSession) {
  const match = /^(faulty|healthy)_ds(\d)_([a-z])$/.exec(demoSession.id);
  if (match) {
    const kind = match[1] === "faulty" ? "Faulty" : "Healthy";
    return `${kind} \u00b7 DS${match[2]} \u00b7 ${match[3].toUpperCase()}`;
  }
  return demoSession.title || demoSession.id;
}
