import { api } from "../../../services/api";
import { useSimulationStore } from "../../../store/simulationStore";
import { getDemoSessions } from "./batteryService";

/** Calls the local-development virtual EV simulation API. */
export async function getSimulationStatus() {
  const response = await api.get("/api/simulation/status");
  return response.data;
}

export async function startSimulation(config) {
  const response = await api.post("/api/simulation/start", config);
  return response.data;
}

export async function pauseSimulation() {
  const response = await api.post("/api/simulation/pause");
  return response.data;
}

export async function resumeSimulation() {
  const response = await api.post("/api/simulation/resume");
  return response.data;
}

export async function stopSimulation() {
  const response = await api.post("/api/simulation/stop");
  return response.data;
}

/** Car the simulation replays unless the user picks another (the notebook's explained faulty car). */
const PREFERRED_DEMO_ID = "faulty_3_515";

/**
 * Loads the recorded demo cars into the simulation store and, if none is chosen
 * yet, selects a default so Simulation Mode replays real data, not generated
 * readings. Safe to call repeatedly; failures leave the store unchanged.
 *
 * @returns {Promise<void>}
 */
export async function loadDemoSessions() {
  try {
    const list = await getDemoSessions();
    const { setDemoSessions, setConfig, config } =
      useSimulationStore.getState();
    setDemoSessions(list);
    if (config.demoSessionId || list.length === 0) return;
    const pick =
      list.find((item) => item.id === PREFERRED_DEMO_ID) ??
      list.find((item) => item.id !== "sample_session") ??
      list[0];
    setConfig({ demoSessionId: pick.id });
  } catch {
    // Backend not reachable yet: the screen offers a retry and the simulation
    // falls back to generated readings.
  }
}
