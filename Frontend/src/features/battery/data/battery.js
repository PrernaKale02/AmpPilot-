/**
 * Mock battery telemetry.
 *
 * Shape mirrors what the future FastAPI `GET /battery` endpoint — backed by
 * real BLE/OBD-II readings — will return.
 */
export const batteryMock = {
  score: 96,
  status: "Excellent",
  subtitle: "Your battery is performing above average.",
  metrics: {
    stateOfHealth: { value: 96, unit: "%" },
    stateOfCharge: { value: 90, unit: "%" },
    estimatedRange: { value: 210, unit: "km" },
    temperature: { value: 31, unit: "°C" },
    chargeCycles: { value: 142, unit: "" },
  },
  recommendation:
    "Avoid charging above 90% for routine charging to maximize long-term battery health.",
};
