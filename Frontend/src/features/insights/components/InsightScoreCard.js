import { Text, View, StyleSheet } from "react-native";
import { Card } from "../../../components/ui/Card";
import { Theme } from "../../../theme/theme";

/**
 * Battery Score card for the Insights screen — the overall score behind
 * the insights and recommendations below it.
 *
 * @param {object} props
 * @param {number} props.score - Battery score out of 100.
 * @param {string} props.status - Score label, e.g. "Excellent".
 * @returns {React.JSX.Element}
 */
export function InsightScoreCard({ score, status }) {
  return (
    <Card style={styles.card}>
      <View style={styles.scoreRow}>
        <Text style={styles.score}>{score}</Text>
        <Text style={styles.scoreMax}>/ 100</Text>
      </View>
      <Text style={styles.status}>{status}</Text>
      <Text style={styles.label}>Battery Score</Text>
    </Card>
  );
}

const styles = StyleSheet.create({
  card: {
    alignItems: "center",
    gap: Theme.spacing.xs,
    paddingVertical: Theme.spacing.xl,
  },
  scoreRow: {
    flexDirection: "row",
    alignItems: "flex-end",
    gap: Theme.spacing.xs,
  },
  score: {
    ...Theme.typography.display,
    color: Theme.colors.textPrimary,
  },
  scoreMax: {
    ...Theme.typography.h3,
    color: Theme.colors.textSecondary,
    marginBottom: Theme.spacing.sm,
  },
  status: {
    ...Theme.typography.h3,
    color: Theme.colors.success,
  },
  label: {
    ...Theme.typography.caption,
    color: Theme.colors.textSecondary,
    marginTop: Theme.spacing.xs,
  },
});
