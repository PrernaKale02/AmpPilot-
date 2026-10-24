import { useEffect, useRef } from "react";
import { getSimulationStatus } from "../services/simulationService";
import { announceSimulationEvents } from "../../notifications/services/voiceAlerts";
import { useSimulationStore } from "../../../store/simulationStore";

function messageFrom(error) {
  return error.response?.data?.detail || "Unable to reach the simulation service.";
}

export function SimulationSync() {
  const session = useSimulationStore((state) => state.session);
  const statusLoaded = useSimulationStore((state) => state.statusLoaded);
  const setSession = useSimulationStore((state) => state.setSession);
  const setStatusError = useSimulationStore((state) => state.setStatusError);
  const voicePrimedRef = useRef(false);

  useEffect(() => {
    let mounted = true;
    let timer;

    const refreshStatus = async () => {
      try {
        const nextSession = await getSimulationStatus();
        if (!mounted) return;
        setSession(nextSession);
        announceSimulationEvents(nextSession?.events, { silent: !voicePrimedRef.current });
        voicePrimedRef.current = true;
      } catch (error) {
        if (mounted) setStatusError(messageFrom(error));
      }
    };

    if (!statusLoaded) {
      void refreshStatus();
    } else if (session?.status === "running") {
      const intervalSeconds = session.config?.telemetryIntervalSeconds || 1;
      timer = globalThis.setInterval(refreshStatus, intervalSeconds * 1000);
    }

    return () => {
      mounted = false;
      if (timer) globalThis.clearInterval(timer);
    };
  }, [
    session?.status,
    session?.config?.telemetryIntervalSeconds,
    setSession,
    setStatusError,
    statusLoaded,
  ]);

  return null;
}
