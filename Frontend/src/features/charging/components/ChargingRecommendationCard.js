import { Text, View, StyleSheet } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { Card } from "../../../components/ui/Card";
import { Theme } from "../../../theme/theme";

/**
 * Recommendation card explaining a healthier charging habit, mirroring the
 * recommendation card on the Battery screen.
 *
 * @param {object} props
 * @param {string} props.message - Recommendation copy to display.
 * @returns {React.JSX.Element}
 */
export function ChargingRecommendationCard({ message }) {
  return (
    <Card style={styles.card}>
      <View style={styles.header}>
        <Ionicons name="bulb-outline" size={18} color={Theme.colors.primary} />
        <Text style={styles.label}>Recommendation</Text>
      </View>
      <Text style={styles.body}>{message}</Text>
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
    ...Theme.typography.body,
    color: Theme.colors.textPrimary,
  },
});
