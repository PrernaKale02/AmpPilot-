/**
 * Mock dashboard summary.
 *
 * Shape mirrors what the future FastAPI `GET /dashboard` endpoint will
 * return, so dashboardService can swap its implementation without any
 * change to the screen.
 */
export const dashboardMock = {
  greeting: {
    title: "Good Morning 👋",
    subtitle: "Your battery looks healthy today.",
  },
  batteryHealth: {
    percentage: 96,
    status: "Excellent",
  },
  vehicle: {
    connected: false,
    name: null,
    summary: "No vehicle connected",
  },
  insight: {
    id: "insight-001",
    message: "Avoid charging above 90% to improve long-term battery life.",
  },
  recentCharging: {
    hasSessions: false,
    summary: "No charging sessions yet.",
  },
};
