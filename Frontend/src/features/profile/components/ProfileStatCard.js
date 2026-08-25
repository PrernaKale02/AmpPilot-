import { Text, View, StyleSheet } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { Card } from "../../../components/ui/Card";
import { Theme } from "../../../theme/theme";

/**
 * Single statistic tile for the Profile screen's Driving Summary grid
 * (Total Distance, Average Efficiency, Ownership).
 *
 * @param {object} props
 * @param {string} props.icon - Ionicons glyph name.
 * @param {string} props.label - Stat label, e.g. "Total Distance".
 * @param {string} props.value - Stat value, e.g. "18,240 km".
 * @returns {React.JSX.Element}
 */
export function ProfileStatCard({ icon, label, value }) {
  return (
    <Card style={styles.card}>
      <Ionicons name={icon} size={20} color={Theme.colors.textSecondary} />
      <Text style={styles.value}>{value}</Text>
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
  value: {
    ...Theme.typography.h3,
    color: Theme.colors.textPrimary,
  },
  label: {
    ...Theme.typography.caption,
    color: Theme.colors.textSecondary,
  },
});
