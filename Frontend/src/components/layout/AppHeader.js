import { Text, View, StyleSheet } from "react-native";
import { Theme } from "../../theme/theme";
import { SimulationControls } from "../../features/battery/components/SimulationControls";

/**
 * Global screen header — the AmpPilot wordmark followed by a page title
 * and optional subtitle. Every top-level screen starts with this so the
 * app reads as one cohesive product rather than a set of loose screens.
 *
 * Simulation controls share this row so they stay reachable without adding
 * content above the safe-area-aware screen title.
 *
 * @param {object} props
 * @param {string} props.title - Page title, e.g. "Battery".
 * @param {string} [props.subtitle] - Optional page subtitle.
 * @param {boolean} [props.simulationControls=true] - Show app-wide simulation controls.
 * @returns {React.JSX.Element}
 */
export function AppHeader({ title, subtitle, simulationControls = true }) {
  return (
    <View style={styles.container}>
      <View style={styles.textGroup}>
        <Text style={styles.brand}>AmpPilot</Text>
        <Text style={styles.title}>{title}</Text>
        {subtitle ? <Text style={styles.subtitle}>{subtitle}</Text> : null}
      </View>
      {simulationControls ? <SimulationControls /> : null}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: "row",
    alignItems: "center",
    gap: Theme.spacing.sm,
    marginTop: Theme.spacing.sm,
  },
  textGroup: {
    flex: 1,
  },
  brand: {
    fontSize: 13,
    fontWeight: "700",
    letterSpacing: 0.4,
    color: Theme.colors.primary,
    // textTransform: "uppercase",
    marginBottom: 2,
  },
  title: {
    ...Theme.typography.h1,
    color: Theme.colors.textPrimary,
  },
  subtitle: {
    ...Theme.typography.body,
    color: Theme.colors.textSecondary,
    marginTop: Theme.spacing.xs,
  },
});
