/**
 * Mock insights overview: battery score, today's insight, a recommendation
 * with its expected benefit, and a history of past insights.
 *
 * `severity` on each insight is one of "good", "info", or "warning" and
 * drives how the insight is visually treated on screen.
 *
 * Shape mirrors what the future FastAPI `GET /insights` endpoint — backed
 * by AI predictions — will return.
 */
export const insightsOverviewMock = {
  batteryScore: 96,
  scoreStatus: "Excellent",
  todaysInsight: {
    title: "Battery temperature is optimal",
    message: "Your battery has stayed within its ideal temperature range this week.",
    severity: "good",
  },
  recommendation: {
    title: "Avoid frequent full charges",
    message: "Charging above 90% regularly accelerates long-term battery wear.",
    expectedBenefit: "+8% estimated battery lifespan over 2 years",
    severity: "info",
  },
  history: [
    {
      id: "insight-004",
      title: "Fast charging used often this week",
      message: "3 of your last 5 sessions used DC fast charging, which adds heat stress over time.",
      severity: "warning",
      createdAt: "2026-07-22T08:00:00Z",
    },
    {
      id: "insight-003",
      title: "Battery temperature is optimal",
      message: "Your battery has stayed within its ideal temperature range this week.",
      severity: "good",
      createdAt: "2026-07-20T08:00:00Z",
    },
    {
      id: "insight-002",
      title: "Avoid frequent full charges",
      message: "Avoid charging above 90% to improve long-term battery life.",
      severity: "info",
      createdAt: "2026-07-18T08:00:00Z",
    },
    {
      id: "insight-001",
      title: "State of health trending well",
      message: "Your battery's state of health has stayed steady for the past 30 days.",
      severity: "good",
      createdAt: "2026-07-12T08:00:00Z",
    },
  ],
};
