import { Theme } from "../../../theme/theme";

const SEVERITY_STYLES = {
  good: { icon: "checkmark-circle-outline", color: Theme.colors.success },
  info: { icon: "information-circle-outline", color: Theme.colors.primary },
  warning: { icon: "alert-circle-outline", color: Theme.colors.warning },
};

/**
 * Resolves the icon and color used to visually distinguish an insight by
 * its severity.
 *
 * @param {"good"|"info"|"warning"} severity
 * @returns {{ icon: string, color: string }}
 */
export function getSeverityStyle(severity) {
  return SEVERITY_STYLES[severity] ?? SEVERITY_STYLES.info;
}
