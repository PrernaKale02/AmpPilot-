import { api } from "../../../services/api";

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
