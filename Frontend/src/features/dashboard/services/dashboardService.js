import { dashboardMock } from "../data/dashboard";
import { getSimulationTelemetry } from "../../battery/services/simulationData";

/**
 * Fetches the dashboard summary.
 *
 * Reads local mock data today; will call `GET /dashboard` on the FastAPI
 * backend later. The returned shape stays the same either way, so
 * DashboardScreen never needs to change.
 *
 * @returns {Promise<typeof dashboardMock>}
 */
export async function getDashboard(session) {
  const telemetry = getSimulationTelemetry(session);
  if (!telemetry) return dashboardMock;

  return {
    ...dashboardMock,
    simulation: {
      status: session.status,
      stateOfChargePercent: telemetry.stateOfChargePercent,
      temperatureC: telemetry.temperatureC,
      direction: telemetry.direction,
      batteryStatus: telemetry.batteryStatus,
    },
    vehicle: {
      ...dashboardMock.vehicle,
      connected: true,
      name: "Virtual EV",
      summary: `Virtual EV · ${telemetry.stateOfChargePercent}% charge`,
    },
    insight: {
      ...dashboardMock.insight,
      message: `Simulated battery is ${telemetry.batteryStatus} and ${telemetry.direction}.`,
    },
  };
}
