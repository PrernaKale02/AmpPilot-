import { Pressable, StyleSheet, View } from "react-native";
import { Theme } from "../../theme/theme";

/**
 * Standard container used throughout the app (dashboard widgets, battery
 * info, charging sessions, insights, alerts, settings rows, etc.).
 *
 * Renders a Pressable when `onPress` is provided or `pressable` is true,
 * otherwise renders a plain View.
 *
 * @param {object} props
 * @param {React.ReactNode} props.children - Card content.
 * @param {import("react-native").StyleProp<import("react-native").ViewStyle>} [props.style] - Style for the card container.
 * @param {boolean} [props.padded=true] - Apply the default inner padding.
 * @param {boolean} [props.pressable=false] - Force rendering as a Pressable even without an `onPress` handler.
 * @param {() => void} [props.onPress] - Press handler. Implies `pressable`.
 * @returns {React.JSX.Element}
 */
export function Card({ children, style, padded = true, pressable = false, onPress }) {
  const isPressable = pressable || !!onPress;
  const cardStyle = [styles.base, padded && styles.padded, style];

  if (isPressable) {
    return (
      <Pressable
        onPress={onPress}
        accessibilityRole="button"
        style={({ pressed }) => [...cardStyle, pressed && styles.pressed]}
      >
        {children}
      </Pressable>
    );
  }

  return <View style={cardStyle}>{children}</View>;
}

const styles = StyleSheet.create({
  base: {
    backgroundColor: Theme.colors.surface,
    borderWidth: 1,
    borderColor: Theme.colors.border,
    borderRadius: Theme.radius.lg,
  },
  padded: {
    padding: Theme.spacing.md,
  },
  pressed: {
    opacity: 0.95,
  },
});
