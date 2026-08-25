import { StyleSheet, Text, View } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { useNavigation } from "@react-navigation/native";
import { Screen } from "../../../components/layout/Screen";
import { Button } from "../../../components/ui/Button";
import { Theme } from "../../../theme/theme";
import { signInWithGoogle, continueAsGuest } from "../services/authService";

/**
 * Pre-authentication login screen.
 *
 * Offers modern, passwordless entry points (Google, guest) instead of a
 * traditional email/password form. Both actions are placeholders for now
 * and simply continue the flow into vehicle pairing.
 *
 * @returns {React.JSX.Element}
 */
export default function LoginScreen() {
  const navigation = useNavigation();

  const handleGoogleSignIn = async () => {
    await signInWithGoogle();
    navigation.replace("Main", { screen: "PairVehicle" });
  };

  const handleGuestContinue = async () => {
    await continueAsGuest();
    navigation.replace("Main", { screen: "PairVehicle" });
  };

  return (
    <Screen contentContainerStyle={styles.content}>
      <View style={styles.hero}>
        <View style={styles.logo}>
          <Ionicons name="battery-charging-outline" size={56} color={Theme.colors.primary} />
        </View>
        <Text style={styles.title}>Welcome Back</Text>
        <Text style={styles.subtitle}>Sign in to unlock personalized battery insights.</Text>
      </View>

      <View style={styles.actions}>
        <Button title="Continue with Google" onPress={handleGoogleSignIn} />
        <Button
          title="Continue as Guest"
          variant="ghost"
          onPress={handleGuestContinue}
          style={styles.guestButton}
        />
      </View>
    </Screen>
  );
}

const styles = StyleSheet.create({
  content: {
    alignItems: "center",
    justifyContent: "center",
    paddingHorizontal: Theme.spacing.xl,
  },
  hero: {
    alignItems: "center",
    marginBottom: Theme.spacing.xxl,
  },
  logo: {
    width: 96,
    height: 96,
    borderRadius: Theme.radius.pill,
    backgroundColor: Theme.colors.surfaceElevated,
    alignItems: "center",
    justifyContent: "center",
    marginBottom: Theme.spacing.xl,
  },
  title: {
    ...Theme.typography.h1,
    color: Theme.colors.textPrimary,
    textAlign: "center",
  },
  subtitle: {
    ...Theme.typography.body,
    color: Theme.colors.textSecondary,
    textAlign: "center",
    marginTop: Theme.spacing.md,
    maxWidth: 300,
  },
  actions: {
    width: "100%",
  },
  guestButton: {
    marginTop: Theme.spacing.sm,
  },
});
