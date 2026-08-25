import { useEffect, useState } from "react";
import { StyleSheet, Text, View } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { useNavigation } from "@react-navigation/native";
import { Screen, AppHeader } from "../../../components/layout";
import { Card } from "../../../components/ui/Card";
import { Theme } from "../../../theme/theme";
import { getChargingOverview } from "../services/chargingService";
import { ChargingOverviewCard } from "../components/ChargingOverviewCard";
import { ChargingSummaryCard } from "../components/ChargingSummaryCard";
import { ChargingSessionCard } from "../components/ChargingSessionCard";
import { ChargingRecommendationCard } from "../components/ChargingRecommendationCard";

/**
 * Charging Overview screen — current charging status, weekly summary,
 * recent charging sessions, and a habit recommendation. Reads from
 * `chargingService.getChargingOverview()` so the UI is ready for a real
 * backend without changes.
 *
 * @returns {React.JSX.Element}
 */
export default function ChargingScreen() {
  const navigation = useNavigation();
  const [overview, setOverview] = useState(null);

  useEffect(() => {
    let isMounted = true;
    getChargingOverview().then((data) => {
      if (isMounted) setOverview(data);
    });
    return () => {
      isMounted = false;
    };
  }, []);

  if (!overview) {
    return <Screen />;
  }

  const { currentStatus, lastCharge, batteryPercent, weeklySummary, recentSessions, recommendation } =
    overview;

  return (
    <Screen scroll contentContainerStyle={styles.content}>
      <AppHeader title="Charging" subtitle="Track your charging sessions." />

      <ChargingOverviewCard status={currentStatus} lastCharge={lastCharge} batteryPercent={batteryPercent} />

      <ChargingSummaryCard
        sessions={weeklySummary.sessions}
        energyAddedKwh={weeklySummary.energyAddedKwh}
        cost={weeklySummary.cost}
      />

      <Card style={styles.nearbyCard} onPress={() => navigation.navigate("NearbyStations")}>
        <View style={styles.nearbyIcon}>
          <Ionicons name="flash" size={22} color={Theme.colors.primary} />
        </View>
        <View style={styles.nearbyText}>
          <Text style={styles.nearbyTitle}>Find Nearby Stations</Text>
          <Text style={styles.nearbySubtitle}>Discover charging points around you.</Text>
        </View>
        <Ionicons name="chevron-forward" size={18} color={Theme.colors.textMuted} />
      </Card>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Recent Charging Sessions</Text>
        <View style={styles.sessionList}>
          {recentSessions.map((session) => (
            <ChargingSessionCard key={session.id} session={session} />
          ))}
        </View>
      </View>

      <ChargingRecommendationCard message={recommendation} />
    </Screen>
  );
}

const styles = StyleSheet.create({
  content: {
    gap: Theme.spacing.lg,
    paddingBottom: Theme.spacing.lg,
  },
  section: {
    gap: Theme.spacing.sm,
  },
  sectionTitle: {
    ...Theme.typography.overline,
    color: Theme.colors.textSecondary,
    textTransform: "uppercase",
  },
  sessionList: {
    gap: Theme.spacing.sm,
  },
  nearbyCard: {
    flexDirection: "row",
    alignItems: "center",
    gap: Theme.spacing.md,
  },
  nearbyIcon: {
    width: 48,
    height: 48,
    borderRadius: Theme.radius.pill,
    backgroundColor: Theme.colors.surfaceElevated,
    alignItems: "center",
    justifyContent: "center",
  },
  nearbyText: {
    flex: 1,
    gap: 2,
  },
  nearbyTitle: {
    ...Theme.typography.h3,
    color: Theme.colors.textPrimary,
  },
  nearbySubtitle: {
    ...Theme.typography.caption,
    color: Theme.colors.textSecondary,
  },
});
