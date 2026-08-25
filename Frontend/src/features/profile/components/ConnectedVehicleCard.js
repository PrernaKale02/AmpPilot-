import { Text, View, StyleSheet } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { Card } from "../../../components/ui/Card";
import { Theme } from "../../../theme/theme";

const STATUS_COLOR = {
  Connected: Theme.colors.success,
  Disconnected: Theme.colors.textMuted,
};

/**
 * Connected vehicle summary card for the Profile screen — vehicle name,
 * connection status, and a status indicator dot.
 *
 * @param {object} props
 * @param {string} props.name - Vehicle name, e.g. "Tesla Model 3 Long Range".
 * @param {string} props.status - Connection status, e.g. "Connected".
 * @returns {React.JSX.Element}
 */
export function ConnectedVehicleCard({ name, status }) {
  const statusColor = STATUS_COLOR[status] ?? Theme.colors.textMuted;

  return (
    <Card style={styles.card}>
      <View style={styles.iconWrap}>
        <Ionicons name="car-sport-outline" size={24} color={Theme.colors.primary} />
      </View>
      <View style={styles.textGroup}>
        <Text style={styles.name}>{name}</Text>
        <View style={styles.statusRow}>
          <View style={[styles.dot, { backgroundColor: statusColor }]} />
          <Text style={[styles.status, { color: statusColor }]}>{status}</Text>
        </View>
      </View>
    </Card>
  );
}

const styles = StyleSheet.create({
  card: {
    flexDirection: "row",
    alignItems: "center",
    gap: Theme.spacing.md,
  },
  iconWrap: {
    width: 48,
    height: 48,
    borderRadius: Theme.radius.pill,
    backgroundColor: Theme.colors.surfaceElevated,
    alignItems: "center",
    justifyContent: "center",
  },
  textGroup: {
    flex: 1,
    gap: 2,
  },
  name: {
    ...Theme.typography.h3,
    color: Theme.colors.textPrimary,
  },
  statusRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: Theme.spacing.xs,
  },
  dot: {
    width: 8,
    height: 8,
    borderRadius: 4,
  },
  status: {
    ...Theme.typography.body,
    fontWeight: "600",
  },
});
