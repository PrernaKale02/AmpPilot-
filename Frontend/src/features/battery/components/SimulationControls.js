import { useState } from "react";
import { ActivityIndicator, Alert, Pressable, StyleSheet, Text, View } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import {
  pauseSimulation,
  resumeSimulation,
  startSimulation,
  stopSimulation,
} from "../services/simulationService";
import { useSimulationStore } from "../../../store/simulationStore";
import { Theme } from "../../../theme/theme";

function messageFrom(error) {
  return error.response?.data?.detail || "Unable to reach the simulation service.";
}

export function SimulationControls() {
  const session = useSimulationStore((state) => state.session);
  const statusLoaded = useSimulationStore((state) => state.statusLoaded);
  const config = useSimulationStore((state) => state.config);
  const setSession = useSimulationStore((state) => state.setSession);
  const setStatusError = useSimulationStore((state) => state.setStatusError);
  const [submitting, setSubmitting] = useState(false);
  const status = session?.status || "idle";
  const isOn = status === "running" || status === "paused";
  const canPause = isOn;

  const runAction = async (action) => {
    setSubmitting(true);
    setStatusError(null);
    try {
      setSession(await action());
    } catch (error) {
      const message = messageFrom(error);
      setStatusError(message);
      Alert.alert("Simulation unavailable", message);
    } finally {
      setSubmitting(false);
    }
  };

  const toggleSimulation = () => {
    if (isOn) {
      void runAction(stopSimulation);
      return;
    }
    void runAction(() => startSimulation(config));
  };

  const togglePause = () => {
    void runAction(status === "running" ? pauseSimulation : resumeSimulation);
  };

  return (
    <View style={styles.controls}>
      <Pressable
        accessibilityRole="button"
        accessibilityLabel={isOn ? "Turn simulation off" : "Turn simulation on"}
        accessibilityState={{ checked: isOn, disabled: submitting || !statusLoaded }}
        disabled={submitting || !statusLoaded}
        onPress={toggleSimulation}
        style={[styles.toggle, isOn && styles.toggleOn, submitting && styles.disabled]}
      >
        {submitting ? (
          <ActivityIndicator size="small" color={isOn ? Theme.colors.background : Theme.colors.textSecondary} />
        ) : (
          <View style={[styles.indicator, isOn && styles.indicatorOn]} />
        )}
        <Text style={[styles.toggleText, isOn && styles.toggleTextOn]}>{isOn ? "SIM ON" : "SIM OFF"}</Text>
      </Pressable>
      {canPause ? (
        <Pressable
          accessibilityRole="button"
          accessibilityLabel={status === "running" ? "Pause simulation" : "Resume simulation"}
          disabled={submitting || !statusLoaded}
          onPress={togglePause}
          style={[styles.pauseButton, submitting && styles.disabled]}
        >
          <Ionicons
            name={status === "running" ? "pause" : "play"}
            size={18}
            color={Theme.colors.textPrimary}
          />
        </Pressable>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  controls: {
    flexDirection: "row",
    alignItems: "center",
    gap: Theme.spacing.xs,
  },
  toggle: {
    minHeight: 36,
    flexDirection: "row",
    alignItems: "center",
    gap: Theme.spacing.xs,
    borderWidth: 1,
    borderColor: Theme.colors.border,
    borderRadius: Theme.radius.pill,
    paddingHorizontal: Theme.spacing.sm,
  },
  toggleOn: {
    backgroundColor: Theme.colors.primary,
    borderColor: Theme.colors.primary,
  },
  indicator: {
    width: 8,
    height: 8,
    borderRadius: Theme.radius.pill,
    backgroundColor: Theme.colors.textMuted,
  },
  indicatorOn: {
    backgroundColor: Theme.colors.background,
  },
  toggleText: {
    ...Theme.typography.caption,
    color: Theme.colors.textSecondary,
    fontWeight: "700",
  },
  toggleTextOn: {
    color: Theme.colors.background,
  },
  pauseButton: {
    width: 36,
    height: 36,
    alignItems: "center",
    justifyContent: "center",
    borderRadius: Theme.radius.pill,
    backgroundColor: Theme.colors.surfaceElevated,
  },
  disabled: {
    opacity: 0.5,
  },
});
