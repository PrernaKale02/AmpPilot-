import { ScrollView, StyleSheet, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { StatusBar } from "expo-status-bar";
import { Theme } from "../../theme/theme";

/**
 * Base layout wrapper for screens.
 *
 * Handles safe area insets, the status bar, and optional scrolling/padding
 * so individual screens don't have to repeat this boilerplate.
 *
 * @param {object} props
 * @param {React.ReactNode} props.children - Screen content.
 * @param {boolean} [props.scroll=false] - Render content inside a ScrollView instead of a plain View.
 * @param {boolean} [props.noPadding=false] - Skip the default screen padding.
 * @param {Array<"top"|"right"|"bottom"|"left">} [props.edges=["top","bottom"]] - Safe area edges to apply.
 * @param {import("react-native").StyleProp<import("react-native").ViewStyle>} [props.style] - Style for the outer safe area container.
 * @param {import("react-native").StyleProp<import("react-native").ViewStyle>} [props.contentContainerStyle] - Style for the inner content container (or ScrollView content container when `scroll` is true).
 * @returns {React.JSX.Element}
 */
export function Screen({
  children,
  scroll = false,
  noPadding = false,
  edges = ["top", "bottom"],
  style,
  contentContainerStyle,
}) {
  const contentStyle = [styles.content, !noPadding && styles.padded, contentContainerStyle];

  return (
    <SafeAreaView style={[styles.container, style]} edges={edges}>
      <StatusBar style="light" backgroundColor={Theme.colors.background} />
      {scroll ? (
        <ScrollView
          contentContainerStyle={contentStyle}
          showsVerticalScrollIndicator={false}
        >
          {children}
        </ScrollView>
      ) : (
        <View style={contentStyle}>{children}</View>
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Theme.colors.background,
  },
  content: {
    flexGrow: 1,
  },
  padded: {
    padding: Theme.spacing.md,
  },
});
