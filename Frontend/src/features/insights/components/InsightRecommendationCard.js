import { Text, View, StyleSheet } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { Card } from "../../../components/ui/Card";
import { Theme } from "../../../theme/theme";
import { getSeverityStyle } from "./severityStyles";

/**
 * Recommendation card on the Insights screen — a suggested habit change
 * plus the expected benefit of following it.
 *
 * @param {object} props
 * @param {string} props.title - Recommendation title.
 * @param {string} props.message - Recommendation body copy.
 * @param {string} props.expectedBenefit - Expected benefit of following the recommendation, e.g. "+8% estimated battery lifespan over 2 years".
 * @param {"good"|"info"|"warning"} props.severity - Visual severity of the recommendation.
 * @returns {React.JSX.Element}
 */
export function InsightRecommendationCard({ title, message, expectedBenefit, severity }) {
  const { icon, color } = getSeverityStyle(severity);

  return (
    <Card style={styles.card}>
      <View style={styles.header}>
        <Ionicons name="bulb-outline" size={18} color={Theme.colors.primary} />
        <Text style={styles.label}>Recommendation</Text>
      </View>

      <View style={styles.body}>
        <Ionicons name={icon} size={20} color={color} style={styles.bodyIcon} />
        <View style={styles.bodyText}>
          <Text style={styles.title}>{title}</Text>
          <Text style={styles.message}>{message}</Text>
        </View>
      </View>

      <View style={styles.benefitRow}>
        <Ionicons name="trending-up-outline" size={16} color={Theme.colors.success} />
        <Text style={styles.benefit}>{expectedBenefit}</Text>
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
  benefitRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: Theme.spacing.xs,
    paddingTop: Theme.spacing.xs,
    borderTopWidth: 1,
    borderTopColor: Theme.colors.divider,
  },
  benefit: {
    ...Theme.typography.caption,
    color: Theme.colors.success,
    fontWeight: "600",
  },
});
