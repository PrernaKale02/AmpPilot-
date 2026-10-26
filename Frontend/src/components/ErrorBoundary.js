import { Component } from "react";
import { StyleSheet, Text } from "react-native";
import { Card } from "./ui/Card";
import { Theme } from "../theme/theme";

/**
 * Keeps one broken section from blanking the whole screen.
 *
 * Without a boundary, an error thrown while rendering unmounts the entire app
 * and leaves a white page. With it, only this section is replaced by a short
 * message that includes the error text, so the cause is visible without devtools.
 */
export class ErrorBoundary extends Component {
  state = { error: null };

  static getDerivedStateFromError(error) {
    return { error };
  }

  componentDidCatch(error, info) {
    console.error(
      `[${this.props.label || "section"}] render failed:`,
      error,
      info?.componentStack,
    );
  }

  render() {
    if (!this.state.error) return this.props.children;
    return (
      <Card style={styles.card}>
        <Text style={styles.title}>
          {this.props.label || "This section"} could not be shown.
        </Text>
        <Text style={styles.detail}>
          {String(this.state.error?.message || this.state.error)}
        </Text>
      </Card>
    );
  }
}

const styles = StyleSheet.create({
  card: { gap: Theme.spacing.xs },
  title: { ...Theme.typography.body, color: Theme.colors.textPrimary },
  detail: { ...Theme.typography.caption, color: Theme.colors.textSecondary },
});
