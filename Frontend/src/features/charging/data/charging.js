/**
 * Mock charging session history, most recent first.
 *
 * Shape mirrors what the future FastAPI `GET /charging/history` endpoint
 * will return.
 */
export const chargingHistoryMock = [
  {
    id: "chg-003",
    date: "2026-07-22T19:10:00Z",
    startSoc: 35,
    endSoc: 90,
    durationMinutes: 72,
    energyAddedKwh: 19.8,
    location: "Home",
    chargerType: "AC Level 2",
  },
  {
    id: "chg-002",
    date: "2026-07-19T08:45:00Z",
    startSoc: 20,
    endSoc: 80,
    durationMinutes: 38,
    energyAddedKwh: 22.4,
    location: "Highway Fast Charger",
    chargerType: "DC Fast Charge",
  },
  {
    id: "chg-001",
    date: "2026-07-15T21:00:00Z",
    startSoc: 50,
    endSoc: 100,
    durationMinutes: 95,
    energyAddedKwh: 24.1,
    location: "Home",
    chargerType: "AC Level 2",
  },
];

/**
 * Mock charging overview: current status, weekly summary, recent sessions,
 * and a habit recommendation.
 *
 * Shape mirrors what the future FastAPI `GET /charging/overview` endpoint
 * will return.
 */
export const chargingOverviewMock = {
  currentStatus: "Not Charging",
  lastCharge: "Today, 7:45 PM",
  batteryPercent: 90,
  weeklySummary: {
    sessions: 3,
    energyAddedKwh: 66.3,
    cost: 9.82,
  },
  recentSessions: chargingHistoryMock,
  recommendation:
    "Try to keep regular charging sessions between 20% and 80% — frequent full charges to 100% accelerate long-term battery wear.",
};
