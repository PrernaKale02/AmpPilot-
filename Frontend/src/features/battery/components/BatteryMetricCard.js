import { Text, View, StyleSheet } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { Card } from "../../../components/ui/Card";
import { Theme } from "../../../theme/theme";

/**
 * Single metric tile for the Battery Overview screen (State of Health,
 * State of Charge, Estimated Range, Temperature, Charge Cycles, etc).
 *
 * @param {object} props
 * @param {string} props.icon - Ionicons glyph name.
 * @param {string} props.label - Metric label, e.g. "State of Health".
 * @param {string|number} props.value - Metric value, e.g. 96.
 * @param {string} [props.unit] - Unit suffix appended to the value, e.g. "%".
 * @returns {React.JSX.Element}
 */
export function BatteryMetricCard({ icon, label, value, unit }) {
  return (
    <Card style={styles.card}>
      <Ionicons name={icon} size={20} color={Theme.colors.textSecondary} />
      <View style={styles.valueRow}>
        <Text style={styles.value}>{value}</Text>
        {unit ? <Text style={styles.unit}>{unit}</Text> : null}
      </View>
      <Text style={styles.label}>{label}</Text>
    </Card>
  );
}

const styles = StyleSheet.create({
  card: {
    flexBasis: "47%",
    flexGrow: 1,
    gap: Theme.spacing.xs,
  },
  valueRow: {
    flexDirection: "row",
    alignItems: "flex-end",
    gap: Theme.spacing.xs,
  },
  value: {
    ...Theme.typography.h2,
    color: Theme.colors.textPrimary,
  },
  unit: {
    ...Theme.typography.body,
    color: Theme.colors.textSecondary,
    marginBottom: 2,
  },
  label: {
    ...Theme.typography.caption,
    color: Theme.colors.textSecondary,
  },
});
