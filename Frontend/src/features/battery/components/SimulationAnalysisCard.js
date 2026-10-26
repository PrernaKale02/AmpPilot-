import { StyleSheet, Text, View } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { Card } from "../../../components/ui";
import { Theme } from "../../../theme/theme";
import { formatNumber, formatPercent } from "../utils/formatNumber";

const LABEL_TEXT = { 0: "Healthy", 1: "Faulty" };

/**
 * One labelled number in the assessment row.
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

function riskColor(level) {
  if (level === "high") return Theme.colors.danger;
  if (level === "moderate") return Theme.colors.warning;
  return Theme.colors.success;
}

/**
 * Shows the health model's verdict, and why, once a replayed recorded session has finished.
 * Renders nothing for the synthetic cycle. While the session plays it shows progress,
 * because the model needs the whole session before it can assess it.
 *
 * The fault output is an experimental risk score. The reasons describe how the model
 * behaves on this session; they are not proof of the physical cause of a fault.
 *
 * @param {object} props
 * @param {object|null} props.session - Simulation status from the backend.
 * @returns {React.JSX.Element|null}
 */
export function SimulationAnalysisCard({ session }) {
  const replay = session?.replay;
  if (!replay) return null;

  const analysis = session.analysis;
  const percent = Math.round((replay.progress || 0) * 100);
  const trueLabel = LABEL_TEXT[replay.trueLabel];

  return (
    <Card style={styles.card}>
      <View style={styles.header}>
        <Ionicons
          name="analytics-outline"
          size={18}
          color={Theme.colors.primary}
        />
        <Text style={styles.overline}>Recorded session</Text>
      </View>
      <Text style={styles.title}>{replay.title}</Text>
      <Text style={styles.note}>
        Real charging data from the dataset, replayed. This is not live
        telemetry.
      </Text>

      {!analysis ? (
        <Text style={styles.message}>
          Collecting session data… {percent}%. The model needs the whole session
          before it can assess it.
        </Text>
      ) : null}

      {analysis && !analysis.available ? (
        <>
          <Text style={styles.headline}>{analysis.headline}</Text>
          <Text style={styles.message}>{analysis.note}</Text>
        </>
      ) : null}

      {analysis && analysis.available ? (
        <>
          <Text
            style={[styles.headline, { color: riskColor(analysis.riskLevel) }]}
          >
            {analysis.headline}
          </Text>
          <View style={styles.stats}>
            <Stat
              label="State of Health"
              value={formatNumber(analysis.sohPercent)}
              unit="%"
            />
            <Stat label="Capacity" value={formatNumber(analysis.capacity)} />
            <Stat
              label="Fault risk (experimental)"
              value={formatPercent(analysis.faultProbability)}
              unit="%"
            />
          </View>

          <Text style={styles.sectionLabel}>Why the model says this</Text>
          {(analysis.reasons || []).map((reason) => (
            <Text key={reason} style={styles.reason}>
              • {reason}
            </Text>
          ))}
          {analysis.attentionSummary ? (
            <Text style={styles.reason}>• {analysis.attentionSummary}</Text>
          ) : null}

          {trueLabel ? (
            <Text style={styles.footer}>Label in the dataset: {trueLabel}</Text>
          ) : null}
          <Text style={styles.footer}>{analysis.note}</Text>
        </>
      ) : null}
    </Card>
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
  title: { ...Theme.typography.h3, color: Theme.colors.textPrimary },
  note: { ...Theme.typography.caption, color: Theme.colors.textSecondary },
  message: { ...Theme.typography.body, color: Theme.colors.textSecondary },
  headline: { ...Theme.typography.h2, color: Theme.colors.textPrimary },
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
  label: { ...Theme.typography.caption, color: Theme.colors.textSecondary },
  sectionLabel: {
    ...Theme.typography.overline,
    color: Theme.colors.textSecondary,
    textTransform: "uppercase",
    marginTop: Theme.spacing.xs,
  },
  reason: { ...Theme.typography.body, color: Theme.colors.textPrimary },
  footer: { ...Theme.typography.caption, color: Theme.colors.textMuted },
});
