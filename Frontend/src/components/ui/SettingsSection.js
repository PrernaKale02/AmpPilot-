import { Text, View, StyleSheet } from "react-native";
import { Card } from "./Card";
import { Theme } from "../../theme/theme";

/**
 * Titled section of settings-style rows, shared across features (e.g. the
 * Profile screen's Preferences and Support sections). By default wraps its
 * children in a single Card — used for grouped SettingRow lists and static
 * content blocks. Pass `card={false}` for sections whose children already
 * render their own Card.
 *
 * @param {object} props
 * @param {string} props.title - Section title, e.g. "Preferences".
 * @param {React.ReactNode} props.children - Section content.
 * @param {boolean} [props.card=true] - Wrap children in a Card.
 * @returns {React.JSX.Element}
 */
export function SettingsSection({ title, children, card = true }) {
  return (
    <View style={styles.section}>
      <Text style={styles.title}>{title}</Text>
      {card ? (
        <Card style={styles.card} padded={false}>
          {children}
        </Card>
      ) : (
        children
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  section: {
    gap: Theme.spacing.sm,
  },
  title: {
    ...Theme.typography.overline,
    color: Theme.colors.textSecondary,
    textTransform: "uppercase",
  },
  card: {
    overflow: "hidden",
  },
});
