import { Text, View, StyleSheet } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { Card } from "../../../components/ui/Card";
import { Theme } from "../../../theme/theme";
import { getStationStatusStyle } from "./stationStatusStyles";

/**
 * Single entry in the Nearby Stations list. Mirrors the layout of
 * ChargingSessionCard so both charging lists read the same way.
 *
 * @param {object} props
 * @param {object} props.station - Charging station record.
 * @param {string} props.station.name - Station display name.
 * @param {string|null} props.station.network - Operator running the station, e.g. "Tata Power".
 * @param {number} props.station.distanceKm - Distance from the search origin, in km.
 * @param {"available"|"busy"|"offline"|null} props.station.status - Current availability.
 * @param {number|null} props.station.availableConnectors - Connectors currently free.
 * @param {number|null} props.station.totalConnectors - Connectors installed at the site.
 * @param {number|null} props.station.maxPowerKw - Peak power of the fastest connector, in kW.
 * @param {string[]|null} props.station.connectorTypes - e.g. ["CCS2", "Type2"].
 * @param {() => void} props.onPress - Called when the card is pressed.
 * @returns {React.JSX.Element}
 */
export function StationCard({ station, onPress }) {
  const {
    name,
    network,
    distanceKm,
    status,
    availableConnectors,
    totalConnectors,
    connectorTypes,
    maxPowerKw,
  } = station;
  const statusStyle = getStationStatusStyle(status);
  const connectorSummary =
    availableConnectors != null && totalConnectors != null
      ? `${availableConnectors} of ${totalConnectors} free`
      : totalConnectors != null
        ? `${totalConnectors} connector${totalConnectors === 1 ? "" : "s"}`
        : availableConnectors != null
          ? `${availableConnectors} free`
          : null;
  const connectorTypesText =
    Array.isArray(connectorTypes) && connectorTypes.length > 0
      ? connectorTypes.join(", ")
      : null;
  const maxPowerText = maxPowerKw != null ? `Up to ${maxPowerKw} kW` : null;

  return (
    <Card style={styles.card} onPress={onPress}>
      <View style={styles.topRow}>
        <View style={styles.nameRow}>
          <Ionicons name="flash-outline" size={18} color={Theme.colors.primary} />
          <Text style={styles.name} numberOfLines={1}>
            {name}
          </Text>
        </View>
        <Text style={styles.distance}>{distanceKm} km</Text>
      </View>

      {network ? <Text style={styles.network}>{network}</Text> : null}

      {statusStyle || connectorSummary ? (
        <View style={styles.statusRow}>
          {statusStyle ? (
            <>
              <Ionicons name={statusStyle.icon} size={16} color={statusStyle.color} />
              <Text style={[styles.status, { color: statusStyle.color }]}>{statusStyle.label}</Text>
            </>
          ) : null}
          {connectorSummary ? <Text style={styles.connectors}>{connectorSummary}</Text> : null}
        </View>
      ) : null}

      {connectorTypesText || maxPowerText ? (
        <View style={styles.footerRow}>
          {connectorTypesText ? <Text style={styles.footerText}>{connectorTypesText}</Text> : null}
          {maxPowerText ? <Text style={styles.footerText}>{maxPowerText}</Text> : null}
        </View>
      ) : null}
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
    gap: Theme.spacing.sm,
  },
  nameRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: Theme.spacing.xs,
    flexShrink: 1,
  },
  name: {
    ...Theme.typography.body,
    color: Theme.colors.textPrimary,
    fontWeight: "600",
    flexShrink: 1,
  },
  distance: {
    ...Theme.typography.caption,
    color: Theme.colors.textSecondary,
  },
  network: {
    ...Theme.typography.caption,
    color: Theme.colors.textSecondary,
  },
  statusRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: Theme.spacing.xs,
    marginTop: Theme.spacing.xs,
    flexWrap: "wrap",
  },
  status: {
    ...Theme.typography.body,
    fontWeight: "600",
  },
  connectors: {
    ...Theme.typography.caption,
    color: Theme.colors.textSecondary,
    marginLeft: "auto",
  },
  footerRow: {
    flexDirection: "row",
    gap: Theme.spacing.md,
    flexWrap: "wrap",
  },
  footerText: {
    ...Theme.typography.caption,
    color: Theme.colors.textSecondary,
  },
});
