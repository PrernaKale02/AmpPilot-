import { insightsOverviewMock } from "../data/insights";
import { getSimulationTelemetry } from "../../battery/services/simulationData";

/**
 * Fetches the insights overview: battery score, today's insight, a
 * recommendation with its expected benefit, and insight history.
 *
 * Reads local mock data today; will call `GET /insights` once the FastAPI
 * backend and AI prediction pipeline are available.
 *
 * @returns {Promise<typeof insightsOverviewMock>}
 */
export async function getInsights(session) {
  const telemetry = getSimulationTelemetry(session);
  if (!telemetry) return insightsOverviewMock;

  const status = telemetry.batteryStatus;
  const severity = status === "critical" ? "warning" : status === "warning" ? "warning" : "good";
  const events = (session.events || []).slice(-4).reverse().map((event, index) => ({
    id: `simulation-${index}-${event.timestamp}`,
    title: "Simulation event",
    message: event.message,
    severity: event.kind === "critical" || event.kind === "warning" ? "warning" : "info",
    createdAt: event.timestamp,
  }));

  return {
    ...insightsOverviewMock,
    todaysInsight: {
      ...insightsOverviewMock.todaysInsight,
      title: `Simulated battery ${status}`,
      message: `The virtual battery is ${telemetry.direction} at ${telemetry.stateOfChargePercent}% charge and ${telemetry.temperatureC} °C.`,
      severity,
    },
    recommendation: {
      ...insightsOverviewMock.recommendation,
      title: status === "normal" ? "Simulation readings are within configured limits" : "Review simulated battery readings",
      message: `Current simulated state: ${status} · ${telemetry.direction}.`,
      severity,
    },
    history: [...events, ...insightsOverviewMock.history],
  };
}
