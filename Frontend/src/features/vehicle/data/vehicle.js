/**
 * Mock paired vehicle.
 *
 * Shape mirrors what the future FastAPI `GET /vehicle` endpoint will
 * return.
 */
export const vehicleMock = {
  id: "veh-001",
  make: "Tata",
  model: "Nexon EV",
  year: 2023,
  nickname: "My Nexon",
  connected: false,
  connectionType: "Bluetooth OBD-II",
  lastSyncedAt: null,
  odometer: 12450,
};
