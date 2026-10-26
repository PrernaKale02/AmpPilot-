import { Pressable, StyleSheet, Text, View } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { Card } from "../../../components/ui/Card";
import { Theme } from "../../../theme/theme";
import { formatNumber, formatPercent } from "../utils/formatNumber";

const LABEL_TEXT = { 0: "Healthy", 1: "Faulty" };

/**
 * One labelled number inside the card.
 *
 * @param {object} props
 * @param {string} props.label - Short caption under the value.
 * @param {string|number} props.value - The number to show.
 * @param {string} [props.unit] - Unit suffix, e.g. "%".
 * @returns {React.JSX.Element}
 */
function Stat({ label, value, unit }) {
  return (
    <View style={styles.stat}>
      <View style={styles.valueRow}>
        <Text style={styles.value}>{value}</Text>
        {unit ? <Text style={styles.unit}>{unit}</Text> : null}
      </View>
      <Text style={styles.label}>{label}</Text>
    </View>
  );
}

/**
 * Shows what the backend health model predicts for a demo charging session,
 * with a picker for the available demo sessions (healthy and faulty cars).
 * The fault output is presented as an experimental risk score, never as a
 * diagnosis: fault detection on unseen cars is weak. The dataset's own label
 * is shown separately so the two are never confused.
 *
 * @param {object} props
 * @param {"loading"|"ready"|"error"} props.status - Request state.
 * @param {{soh_percent: number, capacity: number, fault_probability: number, model_name: string, title?: string, true_label?: 0|1|null}|null} props.prediction - Backend response when `status` is "ready".
 * @param {Array<{id: string, title: string}>} props.sessions - Demo sessions to choose from.
 * @param {string|null} props.selectedId - Currently selected session id.
 * @param {(id: string) => void} props.onSelect - Called when a session is chosen.
 * @param {() => void} props.onRetry - Called when the user taps "Try again" after an error.
 * @returns {React.JSX.Element}
 */
export function ModelPredictionCard({
  status,
  prediction,
  sessions,
  selectedId,
  onSelect,
  onRetry,
}) {
  const trueLabel = prediction ? LABEL_TEXT[prediction.true_label] : undefined;

  return (
    <Card style={styles.card}>
      <View style={styles.header}>
        <Ionicons
          name="hardware-chip-outline"
          size={18}
          color={Theme.colors.primary}
        />
        <Text style={styles.overline}>Health model</Text>
      </View>
      <Text style={styles.note}>
        Estimated from a demo charging session, not your live battery.
      </Text>

      {sessions.length > 1 ? (
        <View style={styles.chips}>
          {sessions.filter(Boolean).map((session) => {
            const selected = session.id === selectedId;
            return (
              <Pressable
                key={session.id}
                onPress={() => onSelect(session.id)}
                accessibilityRole="button"
                accessibilityState={{ selected }}
                style={[styles.chip, selected && styles.chipSelected]}
              >
                <Text
                  style={[styles.chipText, selected && styles.chipTextSelected]}
                >
                  {session.title}
                </Text>
              </Pressable>
            );
          })}
        </View>
      ) : null}

      {status === "loading" ? (
        <Text style={styles.message}>Running the model…</Text>
      ) : null}

      {status === "error" ? (
        <>
          <Text style={styles.message}>
            Model unavailable. Check that the backend is running and the model
            is installed.
          </Text>
          <Pressable
            onPress={onRetry}
            accessibilityRole="button"
            style={styles.retry}
          >
            <Text style={styles.retryText}>Try again</Text>
          </Pressable>
        </>
      ) : null}

      {status === "ready" && prediction ? (
        <>
          <View style={styles.stats}>
            <Stat
              label="State of Health"
              value={formatNumber(prediction.soh_percent)}
              unit="%"
            />
            <Stat label="Capacity" value={formatNumber(prediction.capacity)} />
            <Stat
              label="Fault risk (experimental)"
              value={formatPercent(prediction.fault_probability)}
              unit="%"
            />
          </View>
          {trueLabel ? (
            <Text style={styles.footer}>Label in the dataset: {trueLabel}</Text>
          ) : null}
          {prediction.normalisation === "approximate" ? (
            <Text style={styles.footer}>
              Manufacturer unknown, so input scaling is approximate.
            </Text>
          ) : null}
          <Text style={styles.footer}>Model: {prediction.model_name}</Text>
        </>
      ) : null}
    </Card>
  );
}

const styles = StyleSheet.create({
  card: {
    gap: Theme.spacing.sm,
  },
  header: {
    flexDirection: "row",
    alignItems: "center",
    gap: Theme.spacing.xs,
  },
  overline: {
    ...Theme.typography.overline,
    color: Theme.colors.textSecondary,
    textTransform: "uppercase",
  },
  note: {
    ...Theme.typography.caption,
    color: Theme.colors.textSecondary,
  },
  chips: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: Theme.spacing.xs,
  },
  chip: {
    borderWidth: 1,
    borderColor: Theme.colors.border,
    borderRadius: Theme.radius.pill,
    backgroundColor: Theme.colors.surfaceElevated,
    paddingVertical: Theme.spacing.xs,
    paddingHorizontal: Theme.spacing.sm,
  },
  chipSelected: {
    borderColor: Theme.colors.primary,
  },
  chipText: {
    ...Theme.typography.caption,
    color: Theme.colors.textSecondary,
  },
  chipTextSelected: {
    color: Theme.colors.primary,
  },
  message: {
    ...Theme.typography.body,
    color: Theme.colors.textSecondary,
  },
  retry: {
    alignSelf: "flex-start",
    borderWidth: 1,
    borderColor: Theme.colors.primary,
    borderRadius: Theme.radius.pill,
    paddingVertical: Theme.spacing.xs,
    paddingHorizontal: Theme.spacing.md,
  },
  retryText: {
    ...Theme.typography.caption,
    color: Theme.colors.primary,
  },
  stats: {
    flexDirection: "row",
    justifyContent: "space-between",
    gap: Theme.spacing.md,
  },
  stat: {
    flex: 1,
    gap: 2,
  },
  valueRow: {
    flexDirection: "row",
    alignItems: "flex-end",
    gap: Theme.spacing.xs,
  },
  value: {
    ...Theme.typography.h2,
    color: Theme.colors.textPrimary,
  },
  unit: {
    ...Theme.typography.body,
    color: Theme.colors.textSecondary,
    marginBottom: 2,
  },
  label: {
    ...Theme.typography.caption,
    color: Theme.colors.textSecondary,
  },
  footer: {
    ...Theme.typography.caption,
    color: Theme.colors.textMuted,
  },
});
