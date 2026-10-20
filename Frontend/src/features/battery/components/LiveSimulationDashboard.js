import { useEffect, useRef } from "react";
import { Animated, StyleSheet, Text, View } from "react-native";
import Svg, { Circle, Line, Polyline } from "react-native-svg";
import { Ionicons } from "@expo/vector-icons";
import { Card } from "../../../components/ui";
import { Theme } from "../../../theme/theme";

const AnimatedCircle = Animated.createAnimatedComponent(Circle);
const RING_SIZE = 132;
const RING_RADIUS = 54;
const RING_CIRCUMFERENCE = 2 * Math.PI * RING_RADIUS;

function formatSimulatedTime(seconds) {
  const total = Math.floor(seconds || 0);
  return `${Math.floor(total / 60)}:${String(total % 60).padStart(2, "0")}`;
}

/** Live, explicitly simulated battery dashboard rendered from API telemetry. */
export function LiveSimulationDashboard({ session }) {
  const telemetry = session?.latestTelemetry;
  const ringOffset = useRef(new Animated.Value(RING_CIRCUMFERENCE)).current;

  useEffect(() => {
    const nextSoc = telemetry?.stateOfChargePercent || 0;
    Animated.timing(ringOffset, {
      toValue: RING_CIRCUMFERENCE * (1 - nextSoc / 100),
      duration: 350,
      useNativeDriver: false,
    }).start();
  }, [telemetry?.stateOfChargePercent, ringOffset]);

  if (!telemetry) {
    return (
      <Card style={styles.emptyCard}>
        <Ionicons name="pulse-outline" size={24} color={Theme.colors.textMuted} />
        <Text style={styles.emptyTitle}>No simulated readings yet</Text>
        <Text style={styles.emptyText}>Start a session to populate the live battery dashboard.</Text>
      </Card>
    );
  }

  const stateLabel = telemetry.batteryStatus[0].toUpperCase() + telemetry.batteryStatus.slice(1);
  const stateColor = statusColor(telemetry.batteryStatus);
  const isRunning = session.status === "running";
  const direction = directionFromCurrent(telemetry.currentA);

  return (
    <View style={styles.container}>
      <Card style={styles.overviewCard}>
        <View style={styles.overviewTop}>
          <View>
            <Text style={styles.sectionLabel}>Live battery overview</Text>
            <Text style={[styles.statusText, { color: stateColor }]}>{stateLabel}</Text>
          </View>
          {isRunning ? <Text style={styles.activeBadge}>SIMULATION ACTIVE</Text> : null}
        </View>
        <View style={styles.ringRow}>
          <Svg width={RING_SIZE} height={RING_SIZE} viewBox="0 0 132 132">
            <Circle cx="66" cy="66" r={RING_RADIUS} stroke={Theme.colors.surfaceElevated} strokeWidth="12" fill="none" />
            <AnimatedCircle
              cx="66"
              cy="66"
              r={RING_RADIUS}
              stroke={stateColor}
              strokeWidth="12"
              strokeLinecap="round"
              fill="none"
              strokeDasharray={RING_CIRCUMFERENCE}
              strokeDashoffset={ringOffset}
              transform="rotate(-90 66 66)"
            />
          </Svg>
          <View style={styles.socLabel} pointerEvents="none">
            <Text style={styles.socValue}>{telemetry.stateOfChargePercent.toFixed(0)}%</Text>
            <Text style={styles.socCaption}>SIMULATED SOC</Text>
          </View>
          <View style={styles.directionBlock}>
            <Ionicons name={directionIcon(direction)} size={22} color={Theme.colors.primary} />
            <Text style={styles.direction}>{direction}</Text>
            <Text style={styles.directionHint}>Virtual battery flow</Text>
          </View>
        </View>
      </Card>

      <View style={styles.metrics}>
        <Metric icon="flash-outline" label="Voltage" value={`${telemetry.voltageV} V`} />
        <Metric icon="speedometer-outline" label="Current" value={formatCurrent(telemetry.currentA)} />
        <Metric icon="thermometer-outline" label="Temperature" value={`${telemetry.temperatureC} °C`} />
      </View>

      <TelemetryChart
        title="State of charge"
        unit="%"
        color={Theme.colors.primary}
        history={session.telemetryHistory}
        valueKey="stateOfChargePercent"
      />
      <TelemetryChart
        title="Temperature trend"
        unit="°C"
        color={Theme.colors.warning}
        history={session.telemetryHistory}
        valueKey="temperatureC"
      />
      <SimulationEvents events={session.events} />
    </View>
  );
}

function Metric({ icon, label, value }) {
  return (
    <Card style={styles.metricCard}>
      <Ionicons name={icon} size={18} color={Theme.colors.primary} />
      <Text style={styles.metricLabel}>{label}</Text>
      <Text style={styles.metricValue}>{value}</Text>
    </Card>
  );
}

function TelemetryChart({ title, unit, color, history = [], valueKey }) {
  if (history.length < 2) {
    return <ChartCard title={title} message="Waiting for another simulated reading…" />;
  }
  const values = history.map((entry) => entry[valueKey]);
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;
  const width = 300;
  const height = 108;
  const points = values
    .map((value, index) => {
      const x = (index / (values.length - 1)) * width;
      const y = height - ((value - min) / range) * (height - 12) - 6;
      return `${x},${y}`;
    })
    .join(" ");

  return (
    <Card style={styles.chartCard}>
      <View style={styles.chartHeader}>
        <Text style={styles.chartTitle}>{title}</Text>
        <Text style={styles.chartValue}>{values[values.length - 1].toFixed(1)} {unit}</Text>
      </View>
      <Svg width="100%" height="126" viewBox={`0 0 ${width} 126`} preserveAspectRatio="none">
        <Line x1="0" y1="30" x2={width} y2="30" stroke={Theme.colors.divider} />
        <Line x1="0" y1="78" x2={width} y2="78" stroke={Theme.colors.divider} />
        <Polyline points={points} fill="none" stroke={color} strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
      </Svg>
      <View style={styles.chartAxis}>
        <Text style={styles.axisLabel}>{formatSimulatedTime(history[0].simulatedSeconds)}</Text>
        <Text style={styles.axisLabel}>Simulated time</Text>
        <Text style={styles.axisLabel}>{formatSimulatedTime(history[history.length - 1].simulatedSeconds)}</Text>
      </View>
    </Card>
  );
}

function ChartCard({ title, message }) {
  return (
    <Card style={styles.chartCard}>
      <Text style={styles.chartTitle}>{title}</Text>
      <Text style={styles.emptyText}>{message}</Text>
    </Card>
  );
}

function SimulationEvents({ events = [] }) {
  return (
    <View style={styles.events}>
      <Text style={styles.sectionLabel}>Simulated event timeline</Text>
      {events.length === 0 ? <Text style={styles.emptyText}>No simulated session events yet.</Text> : null}
      {events.slice(-8).reverse().map((event, index) => (
        <Card key={`${event.timestamp}-${index}`} style={styles.eventCard}>
          <View style={[styles.eventDot, { backgroundColor: eventColor(event.kind) }]} />
          <View style={styles.eventText}>
            <Text style={styles.eventMessage}>{event.message}</Text>
            <Text style={styles.eventTime}>SIMULATED · {formatSimulatedTime(event.simulatedSeconds)}</Text>
          </View>
        </Card>
      ))}
    </View>
  );
}

function statusColor(status) {
  if (status === "critical") return Theme.colors.danger;
  if (status === "warning") return Theme.colors.warning;
  return Theme.colors.success;
}

function eventColor(kind) {
  if (kind === "critical") return Theme.colors.danger;
  if (kind === "warning") return Theme.colors.warning;
  return Theme.colors.primary;
}

function directionFromCurrent(currentA) {
  if (Math.abs(currentA) <= 0.5) return "idle";
  return currentA > 0 ? "discharging" : "charging";
}

function directionIcon(direction) {
  if (direction === "charging") return "arrow-down-circle-outline";
  if (direction === "idle") return "pause-circle-outline";
  return "arrow-up-circle-outline";
}

function formatCurrent(currentA) {
  const prefix = currentA > 0 ? "+" : "";
  return `${prefix}${currentA.toFixed(1)} A`;
}

const styles = StyleSheet.create({
  container: { gap: Theme.spacing.lg },
  overviewCard: { gap: Theme.spacing.md },
  overviewTop: { flexDirection: "row", justifyContent: "space-between", gap: Theme.spacing.sm },
  sectionLabel: { ...Theme.typography.overline, color: Theme.colors.textSecondary, textTransform: "uppercase" },
  statusText: { ...Theme.typography.h2, marginTop: 2 },
  activeBadge: { ...Theme.typography.overline, color: Theme.colors.primary, borderWidth: 1, borderColor: Theme.colors.primary, borderRadius: Theme.radius.pill, paddingHorizontal: Theme.spacing.sm, paddingVertical: Theme.spacing.xs, alignSelf: "flex-start" },
  ringRow: { flexDirection: "row", alignItems: "center", justifyContent: "space-between", minHeight: RING_SIZE },
  socLabel: { position: "absolute", left: 26, width: 80, top: 43, alignItems: "center" },
  socValue: { ...Theme.typography.h2, color: Theme.colors.textPrimary },
  socCaption: { ...Theme.typography.overline, color: Theme.colors.textMuted, fontSize: 9 },
  directionBlock: { alignItems: "flex-end", flex: 1, gap: 2 },
  direction: { ...Theme.typography.body, color: Theme.colors.textPrimary, textTransform: "capitalize" },
  directionHint: { ...Theme.typography.caption, color: Theme.colors.textSecondary, textAlign: "right" },
  metrics: { flexDirection: "row", gap: Theme.spacing.sm },
  metricCard: { flex: 1, padding: Theme.spacing.sm, gap: Theme.spacing.xs },
  metricLabel: { ...Theme.typography.overline, color: Theme.colors.textMuted },
  metricValue: { ...Theme.typography.caption, color: Theme.colors.textPrimary, fontWeight: "600" },
  chartCard: { gap: Theme.spacing.sm },
  chartHeader: { flexDirection: "row", justifyContent: "space-between", gap: Theme.spacing.md },
  chartTitle: { ...Theme.typography.h3, color: Theme.colors.textPrimary },
  chartValue: { ...Theme.typography.body, color: Theme.colors.textSecondary },
  chartAxis: { flexDirection: "row", justifyContent: "space-between", gap: Theme.spacing.xs },
  axisLabel: { ...Theme.typography.overline, color: Theme.colors.textMuted },
  events: { gap: Theme.spacing.sm },
  eventCard: { flexDirection: "row", alignItems: "flex-start", gap: Theme.spacing.sm, padding: Theme.spacing.sm },
  eventDot: { width: 8, height: 8, borderRadius: Theme.radius.pill, marginTop: 6 },
  eventText: { flex: 1, gap: 2 },
  eventMessage: { ...Theme.typography.caption, color: Theme.colors.textPrimary },
  eventTime: { ...Theme.typography.overline, color: Theme.colors.textMuted },
  emptyCard: { alignItems: "center", gap: Theme.spacing.sm, paddingVertical: Theme.spacing.xl },
  emptyTitle: { ...Theme.typography.h3, color: Theme.colors.textPrimary },
  emptyText: { ...Theme.typography.caption, color: Theme.colors.textSecondary, textAlign: "center" },
});
