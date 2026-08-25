import { Pressable, Switch, Text, View, StyleSheet } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { Theme } from "../../theme/theme";

/**
 * Single row inside a SettingsSection — a leading icon, a label with an
 * optional subtitle, and a trailing control: static value text, a
 * chevron, a Switch, or a combination.
 *
 * @param {object} props
 * @param {string} props.icon - Ionicons glyph name.
 * @param {string} props.label - Row label.
 * @param {string} [props.subtitle] - Secondary line under the label.
 * @param {string} [props.value] - Trailing value text, e.g. "Metric".
 * @param {boolean} [props.chevron=false] - Show a trailing chevron.
 * @param {boolean} [props.switchValue] - When set, renders a Switch reflecting this value instead of value text/chevron.
 * @param {(value: boolean) => void} [props.onSwitchChange] - Called when the Switch is toggled.
 * @param {() => void} [props.onPress] - Row press handler. The row renders as a Pressable when provided.
 * @param {boolean} [props.last=false] - Omit the bottom divider (last row in a section).
 * @returns {React.JSX.Element}
 */
export function SettingRow({
  icon,
  label,
  subtitle,
  value,
  chevron = false,
  switchValue,
  onSwitchChange,
  onPress,
  last = false,
}) {
  const hasSwitch = typeof switchValue === "boolean";
  const rowStyle = [styles.row, !last && styles.divider];

  const content = (
    <>
      <Ionicons name={icon} size={20} color={Theme.colors.textSecondary} />
      <View style={styles.textGroup}>
        <Text style={styles.label}>{label}</Text>
        {subtitle ? <Text style={styles.subtitle}>{subtitle}</Text> : null}
      </View>
      {hasSwitch ? (
        <Switch
          value={switchValue}
          onValueChange={onSwitchChange}
          trackColor={{ false: Theme.colors.border, true: Theme.colors.primary }}
          thumbColor={Theme.colors.white}
        />
      ) : (
        <View style={styles.trailing}>
          {value ? <Text style={styles.value}>{value}</Text> : null}
          {chevron ? (
            <Ionicons name="chevron-forward" size={18} color={Theme.colors.textMuted} />
          ) : null}
        </View>
      )}
    </>
  );

  if (onPress) {
    return (
      <Pressable
        onPress={onPress}
        accessibilityRole="button"
        style={({ pressed }) => [...rowStyle, pressed && styles.pressed]}
      >
        {content}
      </Pressable>
    );
  }

  return <View style={rowStyle}>{content}</View>;
}

const styles = StyleSheet.create({
  row: {
    flexDirection: "row",
    alignItems: "center",
    gap: Theme.spacing.sm,
    paddingVertical: Theme.spacing.md,
    paddingHorizontal: Theme.spacing.md,
  },
  divider: {
    borderBottomWidth: 1,
    borderBottomColor: Theme.colors.divider,
  },
  textGroup: {
    flex: 1,
    gap: 2,
  },
  label: {
    ...Theme.typography.body,
    color: Theme.colors.textPrimary,
  },
  subtitle: {
    ...Theme.typography.caption,
    color: Theme.colors.textSecondary,
  },
  trailing: {
    flexDirection: "row",
    alignItems: "center",
    gap: Theme.spacing.xs,
  },
  value: {
    ...Theme.typography.body,
    color: Theme.colors.textSecondary,
  },
  pressed: {
    opacity: 0.7,
  },
});
