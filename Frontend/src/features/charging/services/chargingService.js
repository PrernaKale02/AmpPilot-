import { api } from "../../../services/api";
import { chargingHistoryMock, chargingOverviewMock } from "../data/charging";

/**
 * Fetches charging session history, most recent first.
 *
 * Reads local mock data today; will call `GET /charging/history` on the
 * FastAPI backend later.
 *
 * @returns {Promise<typeof chargingHistoryMock>}
 */
export async function getChargingHistory() {
  return chargingHistoryMock;
}

/**
 * Fetches the charging overview: current status, weekly summary, recent
 * sessions, and a charging habit recommendation.
 *
 * Reads local mock data today; will call `GET /charging/overview` once the
 * FastAPI backend and BLE integration are available.
 *
 * @returns {Promise<typeof chargingOverviewMock>}
 */
export async function getChargingOverview() {
  return chargingOverviewMock;
}

/**
 * Fetches charging stations near a coordinate, nearest first.
 *
 * @param {object} params
 * @param {number} params.latitude - Search origin latitude, WGS84 decimal degrees.
 * @param {number} params.longitude - Search origin longitude, WGS84 decimal degrees.
 * @param {number} [params.radiusKm=10] - Search radius, in kilometres.
 * @returns {Promise<Array<object>>}
 */
export async function getNearbyChargingStations({ latitude, longitude, radiusKm = 10 }) {
  const response = await api.get("/api/charging-stations", {
    params: {
      latitude,
      longitude,
      radius_km: radiusKm,
    },
  });

  if (!response?.data || !Array.isArray(response.data.stations)) {
    throw new Error("Invalid charging stations response.");
  }

  return response.data.stations;
}
