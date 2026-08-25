import { insightsOverviewMock } from "../data/insights";

/**
 * Fetches the insights overview: battery score, today's insight, a
 * recommendation with its expected benefit, and insight history.
 *
 * Reads local mock data today; will call `GET /insights` once the FastAPI
 * backend and AI prediction pipeline are available.
 *
 * @returns {Promise<typeof insightsOverviewMock>}
 */
export async function getInsights() {
  return insightsOverviewMock;
}
