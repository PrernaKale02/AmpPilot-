import { create } from "zustand";

export const useSimulationStore = create((set) => ({
  session: null,
  statusLoaded: false,
  statusError: null,
  config: {
    durationMinutes: 15,
    speedMultiplier: 1,
    telemetryIntervalSeconds: 1,
  },
  setSession: (session) => set({ session, statusLoaded: true, statusError: null }),
  setStatusError: (statusError) => set({ statusError, statusLoaded: true }),
  setConfig: (config) => set((state) => ({ config: { ...state.config, ...config } })),
}));
