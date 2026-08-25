import { Text, View, StyleSheet } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { Card } from "../../../components/ui/Card";
import { Theme } from "../../../theme/theme";

const CHARGER_ICONS = {
  "AC Level 2": "home-outline",
  "DC Fast Charge": "flash-outline",
};

/**
 * Formats an ISO date string as e.g. "Jul 22, 7:10 PM".
 *
 * @param {string} isoDate
 * @returns {string}
 */
function formatSessionDate(isoDate) {
  const date = new Date(isoDate);
  const datePart = date.toLocaleDateString(undefined, { month: "short", day: "numeric" });
  const timePart = date.toLocaleTimeString(undefined, { hour: "numeric", minute: "2-digit" });
  return `${datePart}, ${timePart}`;
}

/**
 * Single entry in the Recent Charging Sessions list.
 *
 * @param {object} props
 * @param {object} props.session - Charging session record.
 * @param {string} props.session.date - ISO timestamp the session occurred.
 * @param {number} props.session.startSoc - State of charge at session start, 0-100.
 * @param {number} props.session.endSoc - State of charge at session end, 0-100.
 * @param {number} props.session.durationMinutes - Session duration in minutes.
 * @param {number} props.session.energyAddedKwh - Energy added during the session, in kWh.
 * @param {string} props.session.location - Where the session took place, e.g. "Home".
 * @param {string} props.session.chargerType - Charger type, e.g. "AC Level 2".
 * @returns {React.JSX.Element}
 */
export function ChargingSessionCard({ session }) {
  const { date, startSoc, endSoc, durationMinutes, energyAddedKwh, location, chargerType } = session;

  return (
    <Card style={styles.card}>
      <View style={styles.topRow}>
        <View style={styles.locationRow}>
          <Ionicons
            name={CHARGER_ICONS[chargerType] ?? "flash-outline"}
            size={18}
            color={Theme.colors.primary}
          />
          <Text style={styles.location}>{location}</Text>
        </View>
        <Text style={styles.date}>{formatSessionDate(date)}</Text>
      </View>

      <Text style={styles.socRange}>
        {startSoc}% → {endSoc}%
      </Text>

      <View style={styles.footerRow}>
        <Text style={styles.footerText}>{chargerType}</Text>
        <Text style={styles.footerText}>{durationMinutes} min</Text>
        <Text style={styles.footerText}>{energyAddedKwh} kWh</Text>
      </View>
    </Card>
  );
}

const styles = StyleSheet.create({
  card: {
    gap: Theme.spacing.xs,
  },
  topRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
  },
  locationRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: Theme.spacing.xs,
  },
  location: {
    ...Theme.typography.body,
    color: Theme.colors.textPrimary,
    fontWeight: "600",
  },
  date: {
    ...Theme.typography.caption,
    color: Theme.colors.textSecondary,
  },
  socRange: {
    ...Theme.typography.h3,
    color: Theme.colors.textPrimary,
  },
  footerRow: {
    flexDirection: "row",
    gap: Theme.spacing.md,
  },
  footerText: {
    ...Theme.typography.caption,
    color: Theme.colors.textSecondary,
  },
});
