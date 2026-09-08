import { api } from "../../../services/api";
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

/**
 * Sends one real 128 x 8 charging-session reading sequence to the backend
 * battery model. This is intentionally not called by `getBattery()` because
 * the app has no live telemetry source yet.
 *
 * @param {number[][]} readings - 128 timesteps of the backend's eight sensor channels.
 * @returns {Promise<{capacity: number, soh_percent: number, fault_probability: number, is_faulty: boolean}>}
 */
export async function predictBattery(readings) {
  const response = await api.post("/battery/predict", { readings });
  return response.data;
}
