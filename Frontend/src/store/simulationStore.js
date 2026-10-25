import { create } from "zustand";

export const useSimulationStore = create((set) => ({
  session: null,
  statusLoaded: false,
  statusError: null,
  // Recorded demo cars the backend can replay (see GET /battery/demo-sessions).
  demoSessions: [],
  config: {
    // Short and fast by default: a recorded session is about 21 minutes long,
    // so 10x finishes the whole replay in roughly two minutes.
    durationMinutes: 3,
    speedMultiplier: 10,
    telemetryIntervalSeconds: 1,
    // Which recorded car to replay. null falls back to generated readings.
    demoSessionId: null,
  },
  setSession: (session) =>
    set({ session, statusLoaded: true, statusError: null }),
  setStatusError: (statusError) => set({ statusError, statusLoaded: true }),
  setConfig: (config) =>
    set((state) => ({ config: { ...state.config, ...config } })),
  setDemoSessions: (demoSessions) => set({ demoSessions }),
}));
