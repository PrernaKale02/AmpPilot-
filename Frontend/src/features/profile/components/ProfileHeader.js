import { Text, View, StyleSheet } from "react-native";
import { Card } from "../../../components/ui/Card";
import { Theme } from "../../../theme/theme";

/**
 * Hero header for the Profile screen — an avatar circle showing the first
 * letter of the owner's name, their name, and their email.
 *
 * @param {object} props
 * @param {string} props.name - Owner's display name.
 * @param {string} props.email - Owner's email.
 * @returns {React.JSX.Element}
 */
export function ProfileHeader({ name, email }) {
  return (
    <Card style={styles.card}>
      <View style={styles.avatar}>
        <Text style={styles.avatarLetter}>{name.charAt(0).toUpperCase()}</Text>
      </View>
      <Text style={styles.name}>{name}</Text>
      <Text style={styles.email}>{email}</Text>
    </Card>
  );
}

const styles = StyleSheet.create({
  card: {
    alignItems: "center",
    gap: Theme.spacing.xs,
    paddingVertical: Theme.spacing.xl,
  },
  avatar: {
    width: 72,
    height: 72,
    borderRadius: Theme.radius.pill,
    backgroundColor: Theme.colors.surfaceElevated,
    alignItems: "center",
    justifyContent: "center",
    marginBottom: Theme.spacing.xs,
  },
  avatarLetter: {
    ...Theme.typography.h1,
    color: Theme.colors.primary,
  },
  name: {
    ...Theme.typography.h3,
    color: Theme.colors.textPrimary,
  },
  email: {
    ...Theme.typography.body,
    color: Theme.colors.textSecondary,
  },
});
