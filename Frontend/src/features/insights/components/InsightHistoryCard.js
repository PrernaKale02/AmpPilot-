import { Text, View, StyleSheet } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { Card } from "../../../components/ui/Card";
import { Theme } from "../../../theme/theme";
import { getSeverityStyle } from "./severityStyles";

/**
 * Formats an ISO date string as e.g. "Jul 22".
 *
 * @param {string} isoDate
 * @returns {string}
 */
function formatInsightDate(isoDate) {
  return new Date(isoDate).toLocaleDateString(undefined, { month: "short", day: "numeric" });
}

/**
 * Single entry in the Insights history list.
 *
 * @param {object} props
 * @param {object} props.insight - Insight history record.
 * @param {string} props.insight.title - Insight title.
 * @param {string} props.insight.message - Insight body copy.
 * @param {"good"|"info"|"warning"} props.insight.severity - Visual severity of the insight.
 * @param {string} props.insight.createdAt - ISO timestamp the insight was generated.
 * @returns {React.JSX.Element}
 */
export function InsightHistoryCard({ insight }) {
  const { title, message, severity, createdAt } = insight;
  const { icon, color } = getSeverityStyle(severity);

  return (
    <Card style={styles.card}>
      <Ionicons name={icon} size={18} color={color} />
      <View style={styles.text}>
        <View style={styles.titleRow}>
          <Text style={styles.title}>{title}</Text>
          <Text style={styles.date}>{formatInsightDate(createdAt)}</Text>
        </View>
        <Text style={styles.message}>{message}</Text>
      </View>
    </Card>
  );
}

const styles = StyleSheet.create({
  card: {
    flexDirection: "row",
    gap: Theme.spacing.sm,
  },
  text: {
    flex: 1,
    gap: 2,
  },
  titleRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
  },
  title: {
    ...Theme.typography.body,
    color: Theme.colors.textPrimary,
    fontWeight: "600",
    flexShrink: 1,
  },
  date: {
    ...Theme.typography.caption,
    color: Theme.colors.textSecondary,
  },
  message: {
    ...Theme.typography.caption,
    color: Theme.colors.textSecondary,
  },
});
