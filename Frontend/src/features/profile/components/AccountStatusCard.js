import { Text, View, StyleSheet } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { Card } from "../../../components/ui/Card";
import { Theme } from "../../../theme/theme";

/**
 * Account status card for the Profile screen — account mode and last sync
 * time.
 *
 * @param {object} props
 * @param {string} props.mode - Account mode, e.g. "Guest Mode".
 * @param {string} props.lastSync - Last sync time, e.g. "Today • 8:45 PM".
 * @returns {React.JSX.Element}
 */
export function AccountStatusCard({ mode, lastSync }) {
  return (
    <Card style={styles.card}>
      <View style={styles.header}>
        <Ionicons name="person-circle-outline" size={18} color={Theme.colors.primary} />
        <Text style={styles.label}>Account</Text>
      </View>

      <View style={styles.row}>
        <View style={styles.field}>
          <Text style={styles.fieldLabel}>Mode</Text>
          <Text style={styles.fieldValue}>{mode}</Text>
        </View>
        <View style={styles.field}>
          <Text style={styles.fieldLabel}>Last Sync</Text>
          <Text style={styles.fieldValue}>{lastSync}</Text>
        </View>
      </View>
    </Card>
  );
}

const styles = StyleSheet.create({
  card: {
    gap: Theme.spacing.md,
  },
  header: {
    flexDirection: "row",
    alignItems: "center",
    gap: Theme.spacing.xs,
  },
  label: {
    ...Theme.typography.overline,
    color: Theme.colors.textSecondary,
    textTransform: "uppercase",
  },
  row: {
    flexDirection: "row",
    gap: Theme.spacing.lg,
  },
  field: {
    flex: 1,
    gap: 2,
  },
  fieldLabel: {
    ...Theme.typography.caption,
    color: Theme.colors.textSecondary,
  },
  fieldValue: {
    ...Theme.typography.h3,
    color: Theme.colors.textPrimary,
  },
});
