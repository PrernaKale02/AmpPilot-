import * as Speech from "expo-speech";

const spoken = new Set(); // keys of alerts already announced

export function speakOnce(key, message, language = "en-IN") {
  if (spoken.has(key)) return;
  spoken.add(key);
  Speech.speak(message, { language, rate: 0.95 });
}

export function resetAlert(key) {
  spoken.delete(key);
}

/** Speaks immediately, every time it's called (used for button feedback). */
export function speakNow(message, language = "en-IN") {
  Speech.speak(message, { language, rate: 0.95 });
}

/**
 * Speaks new warning/critical simulation events once each.
 * silent=true marks existing events as heard without speaking
 * (used on first load so old events aren't read out).
 */
export function announceSimulationEvents(events = [], { silent = false } = {}) {
  for (const event of events) {
    if (event.kind !== "warning" && event.kind !== "critical") continue;

    const key = `sim:${event.timestamp}:${event.kind}:${event.message}`;
    if (silent) {
      spoken.add(key);
      continue;
    }
    const prefix = event.kind === "critical" ? "Critical alert." : "Warning.";
    speakOnce(key, `${prefix} ${event.message}`);
  }
}