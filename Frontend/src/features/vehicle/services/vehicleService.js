import { vehicleMock } from "../data/vehicle";

/**
 * Fetches the paired vehicle, if any.
 *
 * Reads local mock data today; will call `GET /vehicle` on the FastAPI
 * backend later.
 *
 * @returns {Promise<typeof vehicleMock>}
 */
export async function getVehicle() {
  return vehicleMock;
}

/**
 * Pairs the vehicle.
 *
 * Resolves immediately today; will begin BLE scanning for nearby OBD-II
 * adapters and call the FastAPI backend once that integration exists.
 *
 * @returns {Promise<typeof vehicleMock>}
 */
export async function pairVehicle() {
  return { ...vehicleMock, connected: true, lastSyncedAt: new Date().toISOString() };
}
