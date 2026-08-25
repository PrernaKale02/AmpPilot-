import { dashboardMock } from "../data/dashboard";

/**
 * Fetches the dashboard summary.
 *
 * Reads local mock data today; will call `GET /dashboard` on the FastAPI
 * backend later. The returned shape stays the same either way, so
 * DashboardScreen never needs to change.
 *
 * @returns {Promise<typeof dashboardMock>}
 */
export async function getDashboard() {
  return dashboardMock;
}
