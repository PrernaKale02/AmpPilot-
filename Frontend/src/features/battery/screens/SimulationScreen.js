import { useEffect, useRef, useState } from "react";
import { Pressable, StyleSheet, Text, TextInput, View } from "react-native";
import { useNavigation } from "@react-navigation/native";
import { Ionicons } from "@expo/vector-icons";
import { AppHeader, Screen } from "../../../components/layout";
import { Button, Card } from "../../../components/ui";
import { Theme } from "../../../theme/theme";
import {
  getSimulationStatus,
  pauseSimulation,
  resumeSimulation,
  startSimulation,
  stopSimulation,
} from "../services/simulationService";
import { LiveSimulationDashboard } from "../components/LiveSimulationDashboard";
import { announceSimulationEvents } from "../../notifications/services/voiceAlerts";

const SPEEDS = [1, 2, 5, 10, 30];
const INTERVALS = [0.5, 1, 5];

function formatDuration(seconds) {
  const totalSeconds = Math.max(0, Math.floor(seconds || 0));
  const minutes = Math.floor(totalSeconds / 60);
  const remainder = totalSeconds % 60;
  return `${minutes}:${String(remainder).padStart(2, "0")}`;
}

function messageFrom(error) {
  return error.response?.data?.detail || "Unable to reach the simulation service.";
}

/** Configures a local virtual-EV session; it never represents live telemetry. */
export default function SimulationScreen() {
  const navigation = useNavigation();
  const [session, setSession] = useState(null);
  const [duration, setDuration] = useState("15");
  const [speed, setSpeed] = useState(1);
  const [interval, setInterval] = useState(1);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [configExpanded, setConfigExpanded] = useState(false);
  // false until the first status load; old events are then marked heard, not spoken
  const voicePrimedRef = useRef(false);

  const refreshStatus = async () => {
    try {
      const nextSession = await getSimulationStatus();
      setSession(nextSession);
      announceSimulationEvents(nextSession?.events, { silent: !voicePrimedRef.current });
      voicePrimedRef.current = true;
      setError("");
    } catch (requestError) {
      setError(messageFrom(requestError));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refreshStatus();
  }, []);

  useEffect(() => {
    if (session?.status !== "running") return undefined;

    const pollEveryMs = (session.config?.telemetryIntervalSeconds || interval) * 1000;
    const timer = globalThis.setInterval(refreshStatus, pollEveryMs);
    return () => clearInterval(timer);
  }, [session?.status, session?.config?.telemetryIntervalSeconds, interval]);

  const isConfigurable = !session || ["idle", "completed"].includes(session.status);

  const applyAction = async (action) => {
    setSubmitting(true);
    setError("");
    try {
      setSession(await action());
    } catch (requestError) {
      setError(messageFrom(requestError));
    } finally {
      setSubmitting(false);
    }
  };

  const handleStart = () => {
    const durationMinutes = Number(duration);
    if (!Number.isInteger(durationMinutes) || durationMinutes < 1 || durationMinutes > 60) {
      setError("Enter a whole duration between 1 and 60 minutes.");
      return;
    }
    applyAction(() =>
      startSimulation({
        durationMinutes,
        speedMultiplier: speed,
        telemetryIntervalSeconds: interval,
      })
    );
  };

  const status = session?.status || "idle";
  const statusLabel = status.charAt(0).toUpperCase() + status.slice(1);

  return (
    <Screen scroll contentContainerStyle={styles.content}>
      <View style={styles.topRow}>
        <Pressable
          accessibilityRole="button"
          accessibilityLabel="Back to Battery"
          onPress={() => navigation.goBack()}
          style={styles.backButton}
        >
          <Ionicons name="chevron-back" size={24} color={Theme.colors.textPrimary} />
        </Pressable>
      </View>
      <AppHeader title="Simulation Mode" subtitle="Monitor a virtual EV battery in real time." />

      <Card style={styles.noticeCard}>
        <Ionicons name="flask-outline" size={20} color={Theme.colors.primary} />
        <Text style={styles.noticeText}>This is simulated data, not live EV telemetry.</Text>
      </Card>

      <LiveSimulationDashboard session={session} />

      <Card style={styles.statusCard}>
        <View style={styles.statusHeader}>
          <Text style={styles.sectionLabel}>Session status</Text>
          <Text style={[styles.status, status === "completed" && styles.completed]}>{statusLabel}</Text>
        </View>
        <View style={styles.timeGrid}>
          <TimeValue label="Elapsed real time" value={formatDuration(session?.elapsedRealSeconds)} />
          <TimeValue label="Simulated time" value={formatDuration(session?.elapsedSimulatedSeconds)} />
          <TimeValue label="Remaining real time" value={formatDuration(session?.remainingRealSeconds)} />
        </View>
      </Card>

      <Card style={styles.settingsCard}>
        <Pressable
          accessibilityRole="button"
          accessibilityState={{ expanded: configExpanded }}
          onPress={() => setConfigExpanded((expanded) => !expanded)}
          style={styles.configHeader}
        >
          <View>
            <Text style={styles.sectionLabel}>Simulation configuration</Text>
            <Text style={styles.configSummary}>{duration} min · {speed}× · every {interval}s</Text>
          </View>
          <Ionicons name={configExpanded ? "chevron-up" : "chevron-down"} size={20} color={Theme.colors.textSecondary} />
        </Pressable>
        {configExpanded ? (
          <View style={styles.configBody}>
            <Text style={styles.fieldLabel}>Duration (real-time minutes)</Text>
            <TextInput
              value={duration}
              onChangeText={setDuration}
              editable={isConfigurable && !submitting}
              keyboardType="number-pad"
              maxLength={2}
              accessibilityLabel="Simulation duration in minutes"
              style={[styles.input, !isConfigurable && styles.disabledInput]}
            />
            <OptionGroup
              label="Simulation speed"
              options={SPEEDS}
              value={speed}
              format={(value) => `${value}×`}
              disabled={!isConfigurable || submitting}
              onChange={setSpeed}
            />
            <OptionGroup
              label="Telemetry update interval"
              options={INTERVALS}
              value={interval}
              format={(value) => `${value} seconds`}
              disabled={!isConfigurable || submitting}
              onChange={setInterval}
            />
            <Text style={styles.autoStop}>The session automatically stops when its duration is reached.</Text>
          </View>
        ) : null}
      </Card>

      {error ? <Text style={styles.error}>{error}</Text> : null}
      {loading ? <Text style={styles.loading}>Loading simulation status…</Text> : null}

      <View style={styles.actions}>
        {["idle", "completed"].includes(status) ? (
          <Button title={status === "completed" ? "Start New Session" : "Start"} onPress={handleStart} loading={submitting} disabled={loading} />
        ) : null}
        {status === "running" ? <Button title="Pause" variant="secondary" onPress={() => applyAction(pauseSimulation)} loading={submitting} /> : null}
        {status === "paused" ? <Button title="Resume" onPress={() => applyAction(resumeSimulation)} loading={submitting} /> : null}
        {status !== "idle" ? <Button title={status === "completed" ? "Reset" : "Stop / Reset"} variant="ghost" onPress={() => applyAction(stopSimulation)} disabled={submitting} /> : null}
      </View>
    </Screen>
  );
}

function TimeValue({ label, value }) {
  return (
    <View style={styles.timeValue}>
      <Text style={styles.timeLabel}>{label}</Text>
      <Text style={styles.timeText}>{value}</Text>
    </View>
  );
}

function OptionGroup({ label, options, value, format, disabled, onChange }) {
  return (
    <View style={styles.optionGroup}>
      <Text style={styles.fieldLabel}>{label}</Text>
      <View style={styles.options}>
        {options.map((option) => (
          <Pressable
            key={option}
            accessibilityRole="button"
            accessibilityState={{ selected: option === value, disabled }}
            disabled={disabled}
            onPress={() => onChange(option)}
            style={[styles.option, option === value && styles.optionSelected, disabled && styles.optionDisabled]}
          >
            <Text style={[styles.optionText, option === value && styles.optionTextSelected]}>{format(option)}</Text>
          </Pressable>
        ))}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  content: { gap: Theme.spacing.lg, paddingBottom: Theme.spacing.lg },
  topRow: { marginBottom: -Theme.spacing.md },
  backButton: { alignSelf: "flex-start", padding: Theme.spacing.xs },
  noticeCard: { flexDirection: "row", alignItems: "center", gap: Theme.spacing.sm },
  noticeText: { ...Theme.typography.caption, color: Theme.colors.textSecondary, flex: 1 },
  statusCard: { gap: Theme.spacing.sm },
  statusHeader: { flexDirection: "row", justifyContent: "space-between", alignItems: "center", gap: Theme.spacing.md },
  sectionLabel: { ...Theme.typography.overline, color: Theme.colors.textSecondary, textTransform: "uppercase" },
  status: { ...Theme.typography.h2, color: Theme.colors.success },
  completed: { color: Theme.colors.primary },
  timeGrid: { gap: Theme.spacing.sm, marginTop: Theme.spacing.xs },
  timeValue: { flexDirection: "row", justifyContent: "space-between", gap: Theme.spacing.md },
  timeLabel: { ...Theme.typography.caption, color: Theme.colors.textSecondary },
  timeText: { ...Theme.typography.body, color: Theme.colors.textPrimary, fontVariant: ["tabular-nums"] },
  settingsCard: { gap: Theme.spacing.md },
  configHeader: { flexDirection: "row", alignItems: "center", justifyContent: "space-between", gap: Theme.spacing.md },
  configSummary: { ...Theme.typography.caption, color: Theme.colors.textSecondary, marginTop: 2 },
  configBody: { gap: Theme.spacing.md },
  fieldLabel: { ...Theme.typography.caption, color: Theme.colors.textSecondary },
  input: { ...Theme.typography.body, color: Theme.colors.textPrimary, borderColor: Theme.colors.border, borderWidth: 1, borderRadius: Theme.radius.md, paddingHorizontal: Theme.spacing.md, minHeight: 48 },
  disabledInput: { opacity: 0.5 },
  optionGroup: { gap: Theme.spacing.sm },
  options: { flexDirection: "row", flexWrap: "wrap", gap: Theme.spacing.sm },
  option: { borderWidth: 1, borderColor: Theme.colors.border, borderRadius: Theme.radius.md, paddingHorizontal: Theme.spacing.md, paddingVertical: Theme.spacing.sm },
  optionSelected: { borderColor: Theme.colors.primary, backgroundColor: Theme.colors.surfaceElevated },
  optionDisabled: { opacity: 0.5 },
  optionText: { ...Theme.typography.caption, color: Theme.colors.textSecondary },
  optionTextSelected: { color: Theme.colors.white },
  autoStop: { ...Theme.typography.caption, color: Theme.colors.textMuted },
  error: { ...Theme.typography.caption, color: Theme.colors.danger },
  loading: { ...Theme.typography.caption, color: Theme.colors.textSecondary },
  actions: { gap: Theme.spacing.sm },
});
