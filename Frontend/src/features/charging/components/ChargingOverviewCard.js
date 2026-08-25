import { Text, View, StyleSheet } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { Card } from "../../../components/ui/Card";
import { Theme } from "../../../theme/theme";

/**
 * Top summary card for the Charging Overview screen — shows whether the
 * vehicle is currently charging, when it last charged, and the current
 * battery level.
 *
 * @param {object} props
 * @param {string} props.status - Current charging status, e.g. "Not Charging".
 * @param {string} props.lastCharge - When the vehicle last charged, e.g. "Today, 7:45 PM".
 * @param {number} props.batteryPercent - Current battery level, 0-100.
 * @returns {React.JSX.Element}
 */
export function ChargingOverviewCard({ status, lastCharge, batteryPercent }) {
  return (
    <Card style={styles.card}>
      <View style={styles.statusRow}>
        <Ionicons name="flash-outline" size={20} color={Theme.colors.primary} />
        <Text style={styles.status}>{status}</Text>
      </View>

      <View style={styles.row}>
        <View style={styles.field}>
          <Text style={styles.label}>Last Charge</Text>
          <Text style={styles.value}>{lastCharge}</Text>
        </View>
        <View style={styles.field}>
          <Text style={styles.label}>Battery</Text>
          <Text style={styles.value}>{batteryPercent}%</Text>
        </View>
      </View>
    </Card>
  );
}

const styles = StyleSheet.create({
  card: {
    gap: Theme.spacing.md,
  },
  statusRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: Theme.spacing.xs,
  },
  status: {
    ...Theme.typography.h3,
    color: Theme.colors.textPrimary,
  },
  row: {
    flexDirection: "row",
    gap: Theme.spacing.lg,
  },
  field: {
    flex: 1,
    gap: 2,
  },
  label: {
    ...Theme.typography.caption,
    color: Theme.colors.textSecondary,
  },
  value: {
    ...Theme.typography.h3,
    color: Theme.colors.textPrimary,
  },
});
