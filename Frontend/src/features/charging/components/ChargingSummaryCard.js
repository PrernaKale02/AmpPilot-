import { Text, View, StyleSheet } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { Card } from "../../../components/ui/Card";
import { Theme } from "../../../theme/theme";

/**
 * Weekly charging summary card — sessions, energy added, and estimated
 * cost for the current week.
 *
 * @param {object} props
 * @param {number} props.sessions - Number of charging sessions this week.
 * @param {number} props.energyAddedKwh - Total energy added this week, in kWh.
 * @param {number} props.cost - Estimated cost of charging this week, in currency units.
 * @returns {React.JSX.Element}
 */
export function ChargingSummaryCard({ sessions, energyAddedKwh, cost }) {
  return (
    <Card style={styles.card}>
      <Text style={styles.title}>Weekly Summary</Text>
      <View style={styles.row}>
        <View style={styles.stat}>
          <Ionicons name="flash-outline" size={18} color={Theme.colors.textSecondary} />
          <Text style={styles.value}>{sessions}</Text>
          <Text style={styles.label}>Sessions</Text>
        </View>
        <View style={styles.stat}>
          <Ionicons name="battery-charging-outline" size={18} color={Theme.colors.textSecondary} />
          <Text style={styles.value}>{energyAddedKwh} kWh</Text>
          <Text style={styles.label}>Energy Added</Text>
        </View>
        <View style={styles.stat}>
          <Ionicons name="cash-outline" size={18} color={Theme.colors.textSecondary} />
          <Text style={styles.value}>${cost.toFixed(2)}</Text>
          <Text style={styles.label}>Cost</Text>
        </View>
      </View>
    </Card>
  );
}

const styles = StyleSheet.create({
  card: {
    gap: Theme.spacing.md,
  },
  title: {
    ...Theme.typography.overline,
    color: Theme.colors.textSecondary,
    textTransform: "uppercase",
  },
  row: {
    flexDirection: "row",
    justifyContent: "space-between",
  },
  stat: {
    flex: 1,
    alignItems: "center",
    gap: Theme.spacing.xs,
  },
  value: {
    ...Theme.typography.h3,
    color: Theme.colors.textPrimary,
  },
  label: {
    ...Theme.typography.caption,
    color: Theme.colors.textSecondary,
  },
});
