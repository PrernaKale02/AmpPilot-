import { batteryMock } from "../data/battery";

/**
 * Fetches the current battery overview: score, status, key metrics, and a
 * charging recommendation.
 *
 * Reads local mock data today; will call `GET /battery` once the FastAPI
 * backend and BLE integration are available.
 *
 * @returns {Promise<typeof batteryMock>}
 */
export async function getBattery() {
  return batteryMock;
}
