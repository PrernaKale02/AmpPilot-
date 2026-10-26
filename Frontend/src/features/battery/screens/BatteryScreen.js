import { useEffect, useState } from "react";
import { StyleSheet, Text, View } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { useNavigation } from "@react-navigation/native";
import { Screen, AppHeader } from "../../../components/layout";
import { Card } from "../../../components/ui/Card";
import { Theme } from "../../../theme/theme";
import {
  getBattery,
  getDemoPrediction,
  getDemoSessions,
} from "../services/batteryService";
import { BatteryMetricCard } from "../components/BatteryMetricCard";
import { ModelPredictionCard } from "../components/ModelPredictionCard";
import { ErrorBoundary } from "../../../components/ErrorBoundary";

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
  const navigation = useNavigation();
  const [battery, setBattery] = useState(null);
  const [prediction, setPrediction] = useState(null);
  const [demoSessions, setDemoSessions] = useState([]);
  const [selectedSessionId, setSelectedSessionId] = useState(null);
  const [predictionStatus, setPredictionStatus] = useState("loading");
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    let isMounted = true;
    getBattery().then((data) => {
      if (isMounted) setBattery(data);
    });
    return () => {
      isMounted = false;
    };
  }, []);

  // Independent of the overview above: a missing backend or model must not
  // block the screen, it only turns the model card into an error message.
  useEffect(() => {
    let isMounted = true;
    getDemoSessions()
      .then((response) => {
        if (!isMounted) return;
        // Ignore anything that is not a session object: one bad entry must not crash the screen.
        const list = Array.isArray(response)
          ? response.filter((item) => item && typeof item.id === "string")
          : [];
        setDemoSessions(list);
        if (list.length > 0)
          setSelectedSessionId((current) => current ?? list[0].id);
        else setPredictionStatus("error");
      })
      .catch(() => {
        if (isMounted) setPredictionStatus("error");
      });
    return () => {
      isMounted = false;
    };
  }, [reloadKey]);

  useEffect(() => {
    if (!selectedSessionId) return undefined;
    let isMounted = true;
    setPredictionStatus("loading");
    getDemoPrediction(selectedSessionId)
      .then((data) => {
        if (!isMounted) return;
        setPrediction(data);
        setPredictionStatus("ready");
      })
      .catch(() => {
        if (isMounted) setPredictionStatus("error");
      });
    return () => {
      isMounted = false;
    };
  }, [selectedSessionId, reloadKey]);

  const handleRetry = () => {
    setPredictionStatus("loading");
    setReloadKey((key) => key + 1);
  };

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

      <ErrorBoundary label="Health model">
        <ModelPredictionCard
          status={predictionStatus}
          prediction={prediction}
          sessions={demoSessions}
          selectedId={selectedSessionId}
          onSelect={setSelectedSessionId}
          onRetry={handleRetry}
        />
      </ErrorBoundary>

      <Card style={styles.recommendationCard}>
        <View style={styles.recommendationHeader}>
          <Ionicons
            name="bulb-outline"
            size={18}
            color={Theme.colors.primary}
          />
          <Text style={styles.recommendationLabel}>Recommendation</Text>
        </View>
        <Text style={styles.recommendationBody}>{recommendation}</Text>
      </Card>

      <Card
        style={styles.simulationCard}
        onPress={() => navigation.navigate("SimulationMode")}
      >
        <View style={styles.simulationIcon}>
          <Ionicons
            name="flask-outline"
            size={20}
            color={Theme.colors.primary}
          />
        </View>
        <View style={styles.simulationText}>
          <Text style={styles.simulationTitle}>Simulation Mode</Text>
          <Text style={styles.simulationSubtitle}>
            Run a virtual EV session for local testing.
          </Text>
        </View>
        <Ionicons
          name="chevron-forward"
          size={18}
          color={Theme.colors.textMuted}
        />
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
  simulationCard: {
    flexDirection: "row",
    alignItems: "center",
    gap: Theme.spacing.md,
  },
  simulationIcon: {
    width: 44,
    height: 44,
    borderRadius: Theme.radius.pill,
    backgroundColor: Theme.colors.surfaceElevated,
    alignItems: "center",
    justifyContent: "center",
  },
  simulationText: {
    flex: 1,
    gap: 2,
  },
  simulationTitle: {
    ...Theme.typography.h3,
    color: Theme.colors.textPrimary,
  },
  simulationSubtitle: {
    ...Theme.typography.caption,
    color: Theme.colors.textSecondary,
  },
});
