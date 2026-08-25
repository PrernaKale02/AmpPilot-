import { Text, View, StyleSheet } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { Card } from "../../../components/ui/Card";
import { Theme } from "../../../theme/theme";
import { getSeverityStyle } from "./severityStyles";

/**
 * Highlighted "Today's Insight" card at the top of the Insights screen.
 *
 * @param {object} props
 * @param {string} props.title - Insight title.
 * @param {string} props.message - Insight body copy.
 * @param {"good"|"info"|"warning"} props.severity - Visual severity of the insight.
 * @returns {React.JSX.Element}
 */
export function TodaysInsightCard({ title, message, severity }) {
  const { icon, color } = getSeverityStyle(severity);

  return (
    <Card style={styles.card}>
      <View style={styles.header}>
        <Ionicons name="sparkles-outline" size={18} color={Theme.colors.primary} />
        <Text style={styles.label}>Today's Insight</Text>
      </View>
      <View style={styles.body}>
        <Ionicons name={icon} size={20} color={color} style={styles.bodyIcon} />
        <View style={styles.bodyText}>
          <Text style={styles.title}>{title}</Text>
          <Text style={styles.message}>{message}</Text>
        </View>
      </View>
    </Card>
  );
}

const styles = StyleSheet.create({
  card: {
    gap: Theme.spacing.sm,
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
  body: {
    flexDirection: "row",
    gap: Theme.spacing.sm,
  },
  bodyIcon: {
    marginTop: 2,
  },
  bodyText: {
    flex: 1,
    gap: 2,
  },
  title: {
    ...Theme.typography.h3,
    color: Theme.colors.textPrimary,
  },
  message: {
    ...Theme.typography.body,
    color: Theme.colors.textSecondary,
  },
});
