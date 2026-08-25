import { ActivityIndicator, Pressable, StyleSheet, Text } from "react-native";
import { Theme } from "../../theme/theme";

const VARIANT_TEXT_COLOR = {
  primary: Theme.colors.white,
  secondary: Theme.colors.white,
  ghost: Theme.colors.textSecondary,
};

/**
 * Standard app button.
 *
 * @param {object} props
 * @param {string} props.title - Button label.
 * @param {() => void} props.onPress - Press handler.
 * @param {"primary"|"secondary"|"ghost"} [props.variant="primary"] - Visual style.
 * @param {boolean} [props.disabled=false] - Disables presses and dims the button.
 * @param {boolean} [props.loading=false] - Disables presses and shows an ActivityIndicator instead of the title.
 * @param {boolean} [props.fullWidth=true] - Stretch to the available width, or size to content when false.
 * @param {import("react-native").StyleProp<import("react-native").ViewStyle>} [props.style] - Style for the button container.
 * @param {import("react-native").StyleProp<import("react-native").TextStyle>} [props.textStyle] - Style for the label text.
 * @returns {React.JSX.Element}
 */
export function Button({
  title,
  onPress,
  variant = "primary",
  disabled = false,
  loading = false,
  fullWidth = true,
  style,
  textStyle,
}) {
  const isDisabled = disabled || loading;

  return (
    <Pressable
      onPress={onPress}
      disabled={isDisabled}
      accessibilityRole="button"
      accessibilityState={{ disabled: isDisabled, busy: loading }}
      style={({ pressed }) => [
        styles.base,
        styles[variant],
        fullWidth ? styles.fullWidth : styles.hugContent,
        isDisabled && styles.disabled,
        pressed && !isDisabled && styles.pressed,
        style,
      ]}
    >
      {loading ? (
        <ActivityIndicator color={VARIANT_TEXT_COLOR[variant]} />
      ) : (
        <Text style={[styles.text, { color: VARIANT_TEXT_COLOR[variant] }, textStyle]}>
          {title}
        </Text>
      )}
    </Pressable>
  );
}

const styles = StyleSheet.create({
  base: {
    minHeight: 48,
    borderRadius: Theme.radius.md,
    paddingHorizontal: Theme.spacing.lg,
    alignItems: "center",
    justifyContent: "center",
    flexDirection: "row",
  },
  fullWidth: {
    width: "100%",
  },
  hugContent: {
    alignSelf: "flex-start",
  },
  primary: {
    backgroundColor: Theme.colors.primary,
  },
  secondary: {
    backgroundColor: "transparent",
    borderWidth: 1,
    borderColor: Theme.colors.border,
  },
  ghost: {
    backgroundColor: "transparent",
  },
  disabled: {
    opacity: 0.5,
  },
  pressed: {
    opacity: 0.9,
  },
  text: {
    ...Theme.typography.body,
  },
});
