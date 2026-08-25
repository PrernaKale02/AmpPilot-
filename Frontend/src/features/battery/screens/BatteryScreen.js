import { useEffect, useState } from "react";
import { StyleSheet, Text, View } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { Screen, AppHeader } from "../../../components/layout";
import { Card } from "../../../components/ui/Card";
import { Theme } from "../../../theme/theme";
import { getBattery } from "../services/batteryService";
import { BatteryMetricCard } from "../components/BatteryMetricCard";

const METRIC_ICONS = {
  stateOfHealth: "pulse-outline",
  stateOfCharge: "battery-half-outline",
  estimatedRange: "speedometer-outline",
  temperature: "thermometer-outline",
  chargeCycles: "sync-outline",
};

const METRIC_LABELS = {
  stateOfHealth: "State of Health",
  stateOfCharge: "State of Charge",
  estimatedRange: "Estimated Range",
  temperature: "Temperature",
  chargeCycles: "Charge Cycles",
};

/**
 * Battery Overview screen — the flagship view of AmpPilot. Shows the
 * overall battery score, key health metrics, and a charging
 * recommendation. Reads from `batteryService.getBattery()` so the UI is
 * ready for a real backend without changes.
 *
 * @returns {React.JSX.Element}
 */
export default function BatteryScreen() {
  const [battery, setBattery] = useState(null);

  useEffect(() => {
    let isMounted = true;
    getBattery().then((data) => {
      if (isMounted) setBattery(data);
    });
    return () => {
      isMounted = false;
    };
  }, []);

  if (!battery) {
    return <Screen />;
  }

  const { score, status, subtitle, metrics, recommendation } = battery;

  return (
    <Screen scroll contentContainerStyle={styles.content}>
      <AppHeader title="Battery" subtitle="Monitor your battery health." />

      <Card style={styles.scoreCard}>
        <View style={styles.scoreRow}>
          <Text style={styles.score}>{score}</Text>
          <Text style={styles.scoreMax}>/ 100</Text>
        </View>
        <Text style={styles.status}>{status}</Text>
        <Text style={styles.scoreSubtitle}>{subtitle}</Text>
      </Card>

      <View style={styles.metricsGrid}>
        {Object.entries(metrics).map(([key, metric]) => (
          <BatteryMetricCard
            key={key}
            icon={METRIC_ICONS[key]}
            label={METRIC_LABELS[key]}
            value={metric.value}
            unit={metric.unit}
          />
        ))}
      </View>

      <Card style={styles.recommendationCard}>
        <View style={styles.recommendationHeader}>
          <Ionicons name="bulb-outline" size={18} color={Theme.colors.primary} />
          <Text style={styles.recommendationLabel}>Recommendation</Text>
        </View>
        <Text style={styles.recommendationBody}>{recommendation}</Text>
      </Card>
    </Screen>
  );
}

const styles = StyleSheet.create({
  content: {
    gap: Theme.spacing.lg,
    paddingBottom: Theme.spacing.lg,
  },
  scoreCard: {
    alignItems: "center",
    gap: Theme.spacing.xs,
    paddingVertical: Theme.spacing.xl,
  },
  scoreRow: {
    flexDirection: "row",
    alignItems: "flex-end",
    gap: Theme.spacing.xs,
  },
  score: {
    ...Theme.typography.display,
    color: Theme.colors.textPrimary,
  },
  scoreMax: {
    ...Theme.typography.h3,
    color: Theme.colors.textSecondary,
    marginBottom: Theme.spacing.sm,
  },
  status: {
    ...Theme.typography.h3,
    color: Theme.colors.success,
  },
  scoreSubtitle: {
    ...Theme.typography.body,
    color: Theme.colors.textSecondary,
    textAlign: "center",
    marginTop: Theme.spacing.xs,
  },
  metricsGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: Theme.spacing.md,
  },
  recommendationCard: {
    gap: Theme.spacing.sm,
  },
  recommendationHeader: {
    flexDirection: "row",
    alignItems: "center",
    gap: Theme.spacing.xs,
  },
  recommendationLabel: {
    ...Theme.typography.overline,
    color: Theme.colors.textSecondary,
    textTransform: "uppercase",
  },
  recommendationBody: {
    ...Theme.typography.body,
    color: Theme.colors.textPrimary,
  },
});
