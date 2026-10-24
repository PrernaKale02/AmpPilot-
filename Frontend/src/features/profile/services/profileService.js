import { profileMock } from "../data/profile";
import { getSimulationTelemetry } from "../../battery/services/simulationData";

/**
 * Fetches the profile overview: account owner, connected vehicle, driving
 * summary, achievements, account status, and app preferences.
 *
 * Reads local mock data today; will call `GET /profile` once the FastAPI
 * backend is available.
 *
 * @returns {Promise<typeof profileMock>}
 */
export async function getProfile(session) {
  const telemetry = getSimulationTelemetry(session);
  if (!telemetry) return profileMock;

  return {
    ...profileMock,
    vehicle: {
      ...profileMock.vehicle,
      name: "Virtual EV",
      status: `Simulation ${session.status}`,
    },
  };
}
