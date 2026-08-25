import { Theme } from "../../../theme/theme";

const STATION_STATUS_STYLES = {
  available: {
    icon: "checkmark-circle-outline",
    color: Theme.colors.success,
    label: "Available",
  },
  busy: {
    icon: "time-outline",
    color: Theme.colors.warning,
    label: "Busy",
  },
  offline: {
    icon: "close-circle-outline",
    color: Theme.colors.danger,
    label: "Offline",
  },
};

/**
 * Resolves the icon, color, and label used to visually distinguish a
 * charging station by its current availability.
 *
 * Mirrors the insights feature's `getSeverityStyle` so status treatment
 * stays consistent across the app.
 *
 * @param {"available"|"busy"|"offline"|null} status
 * @returns {{ icon: string, color: string, label: string } | null}
 */
export function getStationStatusStyle(status) {
  return status ? STATION_STATUS_STYLES[status] ?? null : null;
}
