import { Text, View, StyleSheet } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { Card } from "../../../components/ui/Card";
import { Theme } from "../../../theme/theme";

/**
 * Single earned achievement on the Profile screen.
 *
 * @param {object} props
 * @param {string} props.title - Achievement title, e.g. "Efficient Driver".
 * @param {string} props.description - Achievement description.
 * @returns {React.JSX.Element}
 */
export function AchievementCard({ title, description }) {
  return (
    <Card style={styles.card}>
      <View style={styles.iconWrap}>
        <Ionicons name="trophy-outline" size={18} color={Theme.colors.warning} />
      </View>
      <View style={styles.textGroup}>
        <Text style={styles.title}>{title}</Text>
        <Text style={styles.description}>{description}</Text>
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
    width: 40,
    height: 40,
    borderRadius: Theme.radius.pill,
    backgroundColor: Theme.colors.surfaceElevated,
    alignItems: "center",
    justifyContent: "center",
  },
  textGroup: {
    flex: 1,
    gap: 2,
  },
  title: {
    ...Theme.typography.body,
    color: Theme.colors.textPrimary,
    fontWeight: "600",
  },
  description: {
    ...Theme.typography.caption,
    color: Theme.colors.textSecondary,
  },
});
