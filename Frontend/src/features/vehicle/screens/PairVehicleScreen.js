import { StyleSheet, Text, View } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { useNavigation } from "@react-navigation/native";
import { Screen } from "../../../components/layout/Screen";
import { Button } from "../../../components/ui/Button";
import { Theme } from "../../../theme/theme";
import { pairVehicle } from "../services/vehicleService";

/**
 * Introductory vehicle-pairing screen.
 *
 * First touchpoint for vehicle connectivity. Explains the value of pairing
 * before any real Bluetooth functionality exists.
 *
 * @returns {React.JSX.Element}
 */
export default function PairVehicleScreen() {
  const navigation = useNavigation();

  const handleConnectPress = async () => {
    await pairVehicle();
    navigation.replace("MainTabs");
  };

  return (
    <Screen contentContainerStyle={styles.content}>
      <View style={styles.illustration}>
        <Ionicons name="car-sport-outline" size={72} color={Theme.colors.primary} />
      </View>

      <Text style={styles.title}>Connect Your Vehicle</Text>
      <Text style={styles.subtitle}>
        Pair your EV or connect your Bluetooth OBD-II adapter to unlock battery
        health, charging insights, and intelligent recommendations.
      </Text>

      <Button
        title="Connect Vehicle"
        onPress={handleConnectPress}
        style={styles.connectButton}
      />

      <Text style={styles.footer}>
        Works with most EVs using Bluetooth OBD-II adapters.
      </Text>
    </Screen>
  );
}

const styles = StyleSheet.create({
  content: {
    alignItems: "center",
    justifyContent: "center",
    paddingHorizontal: Theme.spacing.xl,
  },
  illustration: {
    width: 160,
    height: 160,
    borderRadius: Theme.radius.pill,
    backgroundColor: Theme.colors.surfaceElevated,
    alignItems: "center",
    justifyContent: "center",
    marginBottom: Theme.spacing.xxl,
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
    maxWidth: 320,
  },
  connectButton: {
    marginTop: Theme.spacing.xxl,
    width: "100%",
  },
  footer: {
    ...Theme.typography.caption,
    color: Theme.colors.textMuted,
    textAlign: "center",
    marginTop: Theme.spacing.lg,
  },
});
