import { useEffect, useRef } from "react";
import { Animated, StyleSheet, Text } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { useNavigation } from "@react-navigation/native";
import { Screen } from "../../../components/layout/Screen";
import { Theme } from "../../../theme/theme";

const ANIMATION_DURATION = 600;
const NAVIGATE_DELAY = 1500;

/**
 * First screen shown on app launch.
 *
 * Fades and scales the AmpPilot brand mark in, then hands off to the next
 * screen in the auth flow once navigation is wired up.
 *
 * @returns {React.JSX.Element}
 */
export default function SplashScreen() {
  const navigation = useNavigation();
  const opacity = useRef(new Animated.Value(0)).current;
  const scale = useRef(new Animated.Value(0.98)).current;

  useEffect(() => {
    Animated.parallel([
      Animated.timing(opacity, {
        toValue: 1,
        duration: ANIMATION_DURATION,
        useNativeDriver: true,
      }),
      Animated.timing(scale, {
        toValue: 1,
        duration: ANIMATION_DURATION,
        useNativeDriver: true,
      }),
    ]).start();

    const timer = setTimeout(() => {
      navigation.replace("Onboarding");
    }, NAVIGATE_DELAY);

    return () => clearTimeout(timer);
  }, [opacity, scale, navigation]);

  return (
    <Screen style={styles.screen} contentContainerStyle={styles.content}>
      <Animated.View style={[styles.brand, { opacity, transform: [{ scale }] }]}>
        <Ionicons name="battery-charging-outline" size={64} color={Theme.colors.primary} />
        <Text style={styles.title}>AmpPilot</Text>
        <Text style={styles.subtitle}>Battery Intelligence</Text>
      </Animated.View>
    </Screen>
  );
}

const styles = StyleSheet.create({
  screen: {
    backgroundColor: Theme.colors.background,
  },
  content: {
    alignItems: "center",
    justifyContent: "center",
  },
  brand: {
    alignItems: "center",
  },
  title: {
    ...Theme.typography.h1,
    color: Theme.colors.textPrimary,
    marginTop: Theme.spacing.md,
  },
  subtitle: {
    ...Theme.typography.body,
    color: Theme.colors.textSecondary,
    marginTop: Theme.spacing.xs,
    maxWidth: 220,
    textAlign: "center",
  },
});
