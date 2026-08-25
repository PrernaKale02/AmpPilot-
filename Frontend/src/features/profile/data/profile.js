/**
 * Mock profile overview: account owner, connected vehicle, driving
 * summary, achievements, account status, and app preferences.
 *
 * Shape mirrors what the future FastAPI `GET /profile` endpoint will
 * return. Preferences (notifications, units, theme) live here too so the
 * Profile screen — which now also covers what used to be the separate
 * Settings tab — can read everything through a single `getProfile()` call.
 */
export const profileMock = {
  profile: {
    name: "Priya Sharma",
    email: "priya.sharma@example.com",
  },
  vehicle: {
    name: "Tesla Model 3 Long Range",
    status: "Connected",
  },
  stats: {
    totalDistance: "18,240 km",
    averageEfficiency: "15.4 kWh / 100 km",
    ownership: "2 Years",
  },
  achievements: [
    {
      id: "1",
      title: "Efficient Driver",
      description: "Maintained efficient driving habits for 30 consecutive days.",
    },
    {
      id: "2",
      title: "Smart Charging",
      description: "Mostly used battery-friendly charging sessions.",
    },
    {
      id: "3",
      title: "Eco Friendly",
      description: "Reduced energy consumption compared to average usage.",
    },
  ],
  account: {
    mode: "Guest Mode",
    lastSync: "Today • 8:45 PM",
  },
  preferences: {
    notifications: true,
    units: "Metric",
    theme: "Dark",
  },
  version: "1.0 MVP",
};
