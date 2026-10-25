import { useEffect, useState } from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { Card } from "../../../components/ui";
import { Theme } from "../../../theme/theme";
import { getDemoExplanation } from "../services/batteryService";

const LABEL_TEXT = { 0: "Healthy", 1: "Faulty" };

function formatSeconds(seconds) {
  const total = Math.max(0, Math.round(seconds || 0));
  return `${Math.floor(total / 60)}:${String(total % 60).padStart(2, "0")}`;
}

/**
 * Health-model result for the recorded car that Simulation Mode is replaying,
 * with a "why" explanation. When the experimental fault score is elevated the
 * explanation opens by itself; otherwise it is one tap away.
 *
 * The explanation shows how the model reacts on this one recording (which
 * sensors move the score) next to facts measured from the recording. It is not
 * proof of a cause, and the fault score is not a diagnosis.
 *
 * @param {object} props
 * @param {object|null} props.session - Simulation status from the backend.
 * @returns {React.JSX.Element|null} Nothing unless a recorded session is active.
 */
export function SimulationHealthCard({ session }) {
  const demoSessionId = session?.config?.demoSessionId ?? null;
  const active =
    Boolean(session) &&
    session.status !== "idle" &&
    session.dataSource === "recorded";
  const [state, setState] = useState({ status: "loading", data: null });
  const [open, setOpen] = useState(false);
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    if (!active || !demoSessionId) return undefined;
    let isMounted = true;
    setState({ status: "loading", data: null });
    getDemoExplanation(demoSessionId)
      .then((data) => {
        if (!isMounted) return;
        setState({ status: "ready", data });
        setOpen(data.risk_level === "elevated");
      })
      .catch(() => {
        if (isMounted) setState({ status: "error", data: null });
      });
    return () => {
      isMounted = false;
    };
  }, [active, demoSessionId, session?.startedAt, reloadKey]);

  if (!active || !demoSessionId) return null;

  const { status, data } = state;
  const elevated = data?.risk_level === "elevated";
  const accent = elevated ? Theme.colors.danger : Theme.colors.success;
  const trueLabel = data ? LABEL_TEXT[data.true_label] : undefined;

  return (
    <Card style={styles.card}>
      <View style={styles.header}>
        <Ionicons
          name="hardware-chip-outline"
          size={18}
          color={Theme.colors.primary}
        />
        <Text style={styles.overline}>Health model · recorded car</Text>
      </View>

      {status === "loading" ? (
        <Text style={styles.message}>
          Running the health model on this recording…
        </Text>
      ) : null}

      {status === "error" ? (
        <>
          <Text style={styles.message}>
            Health model unavailable. Check that the backend is running and the
            model file is installed.
          </Text>
          <Pressable
            onPress={() => setReloadKey((key) => key + 1)}
            accessibilityRole="button"
            style={styles.retry}
          >
            <Text style={styles.retryText}>Try again</Text>
          </Pressable>
        </>
      ) : null}

      {status === "ready" && data ? (
        <>
          <View style={[styles.banner, { borderColor: accent }]}>
            <View style={[styles.dot, { backgroundColor: accent }]} />
            <View style={styles.bannerText}>
              <Text style={[styles.headline, { color: accent }]}>
                {data.headline}
              </Text>
              <Text style={styles.caption}>
                Experimental score · {Math.round(data.fault_probability * 100)}%
                fault risk
              </Text>
            </View>
          </View>

          <View style={styles.stats}>
            <Stat
              label="State of Health"
              value={data.soh_percent.toFixed(1)}
              unit="%"
            />
            <Stat label="Capacity" value={data.capacity.toFixed(1)} />
            <Stat
              label="Fault risk"
              value={Math.round(data.fault_probability * 100)}
              unit="%"
            />
          </View>

          {trueLabel ? (
            <Text style={styles.footer}>Label in the dataset: {trueLabel}</Text>
          ) : null}
          {data.context_note ? (
            <Text style={styles.context}>{data.context_note}</Text>
          ) : null}

          <Pressable
            onPress={() => setOpen((value) => !value)}
            accessibilityRole="button"
            accessibilityState={{ expanded: open }}
            style={styles.toggle}
          >
            <Text style={styles.toggleText}>
              {open ? "Hide explanation" : "Why this score?"}
            </Text>
            <Ionicons
              name={open ? "chevron-up" : "chevron-down"}
              size={18}
              color={Theme.colors.primary}
            />
          </Pressable>

          {open ? (
            <View style={styles.explanation}>
              {data.reasons.length === 0 ? (
                <Text style={styles.caption}>
                  No single sensor moves the score much on this recording.
                </Text>
              ) : (
                data.reasons.map((reason) => (
                  <View key={reason.channel} style={styles.reason}>
                    <View style={styles.reasonHeader}>
                      <Text style={styles.reasonLabel}>{reason.label}</Text>
                      <Text style={[styles.reasonPoints, { color: accent }]}>
                        {reason.effect_points} pts
                      </Text>
                    </View>
                    <Text style={styles.caption}>{reason.detail}</Text>
                  </View>
                ))
              )}
              {data.top_attention_seconds?.length ? (
                <Text style={styles.caption}>
                  The model paid most attention at{" "}
                  {data.top_attention_seconds
                    .slice(0, 3)
                    .map(formatSeconds)
                    .join(", ")}{" "}
                  into the session.
                </Text>
              ) : null}
              <Text style={styles.footer}>{data.note}</Text>
            </View>
          ) : null}
        </>
      ) : null}
    </Card>
  );
}

function Stat({ label, value, unit }) {
  return (
    <View style={styles.stat}>
      <View style={styles.valueRow}>
        <Text style={styles.value}>{value}</Text>
        {unit ? <Text style={styles.unit}>{unit}</Text> : null}
      </View>
      <Text style={styles.caption}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  card: { gap: Theme.spacing.sm },
  header: { flexDirection: "row", alignItems: "center", gap: Theme.spacing.xs },
  overline: {
    ...Theme.typography.overline,
    color: Theme.colors.textSecondary,
    textTransform: "uppercase",
  },
  message: { ...Theme.typography.body, color: Theme.colors.textSecondary },
  retry: {
    alignSelf: "flex-start",
    borderWidth: 1,
    borderColor: Theme.colors.primary,
    borderRadius: Theme.radius.pill,
    paddingVertical: Theme.spacing.xs,
    paddingHorizontal: Theme.spacing.md,
  },
  retryText: { ...Theme.typography.caption, color: Theme.colors.primary },
  banner: {
    flexDirection: "row",
    alignItems: "center",
    gap: Theme.spacing.sm,
    borderWidth: 1,
    borderRadius: Theme.radius.md,
    padding: Theme.spacing.sm,
  },
  dot: { width: 10, height: 10, borderRadius: Theme.radius.pill },
  bannerText: { flex: 1, gap: 2 },
  headline: { ...Theme.typography.h3 },
  stats: {
    flexDirection: "row",
    justifyContent: "space-between",
    gap: Theme.spacing.md,
  },
  stat: { flex: 1, gap: 2 },
  valueRow: {
    flexDirection: "row",
    alignItems: "flex-end",
    gap: Theme.spacing.xs,
  },
  value: { ...Theme.typography.h2, color: Theme.colors.textPrimary },
  unit: {
    ...Theme.typography.body,
    color: Theme.colors.textSecondary,
    marginBottom: 2,
  },
  caption: { ...Theme.typography.caption, color: Theme.colors.textSecondary },
  footer: { ...Theme.typography.caption, color: Theme.colors.textMuted },
  context: { ...Theme.typography.caption, color: Theme.colors.warning },
  toggle: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    borderTopWidth: 1,
    borderTopColor: Theme.colors.divider,
    paddingTop: Theme.spacing.sm,
  },
  toggleText: { ...Theme.typography.body, color: Theme.colors.primary },
  explanation: { gap: Theme.spacing.sm },
  reason: { gap: 2 },
  reasonHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    gap: Theme.spacing.md,
  },
  reasonLabel: {
    ...Theme.typography.body,
    color: Theme.colors.textPrimary,
    fontWeight: "600",
  },
  reasonPoints: { ...Theme.typography.body, fontVariant: ["tabular-nums"] },
});
