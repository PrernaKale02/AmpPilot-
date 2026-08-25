import { Pressable, StyleSheet, Text, View } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { useNavigation, useRoute } from "@react-navigation/native";
import { Screen } from "../../../components/layout";
import { Card, Button, SettingRow, SettingsSection } from "../../../components/ui";
import { Theme } from "../../../theme/theme";
import { getStationStatusStyle } from "../components/stationStatusStyles";

const CHARGER_TYPE_LABELS = {
  AC: "AC Charging",
  DC: "DC Fast Charging",
  BOTH: "AC & DC Charging",
};

const CURRENCY_SYMBOLS = {
  INR: "₹",
  USD: "$",
  EUR: "€",
  GBP: "£",
};

/**
 * Formats a per-kWh price, e.g. "₹18.50 / kWh".
 *
 * @param {number|null} pricePerKwh - Price per kWh, or null when unpublished.
 * @param {string} currency - ISO 4217 code, e.g. "INR".
 * @returns {string|null}
 */
function formatPrice(pricePerKwh, currency) {
  if (pricePerKwh === null || pricePerKwh === undefined) {
    return null;
  }

  const symbol = CURRENCY_SYMBOLS[currency] ?? `${currency} `;
  return `${symbol}${pricePerKwh.toFixed(2)} / kWh`;
}

/**
 * Formats an ISO date string as e.g. "Aug 14, 9:20 AM", matching how
 * charging sessions are stamped elsewhere in this feature.
 *
 * @param {string} isoDate
 * @returns {string}
 */
function formatUpdatedAt(isoDate) {
  const date = new Date(isoDate);
  const datePart = date.toLocaleDateString(undefined, { month: "short", day: "numeric" });
  const timePart = date.toLocaleTimeString(undefined, { hour: "numeric", minute: "2-digit" });
  return `${datePart}, ${timePart}`;
}

/**
 * Station Details screen - everything known about a single charging station,
 * reached by tapping a card on the Nearby Stations screen.
 *
 * The station is passed through navigation params rather than refetched,
 * since the list already holds the full record.
 *
 * @returns {React.JSX.Element}
 */
export default function StationDetailsScreen() {
  const navigation = useNavigation();
  const route = useRoute();
  const { station } = route.params;

  const {
    name,
    network,
    address,
    distanceKm,
    status,
    availableConnectors,
    totalConnectors,
    maxPowerKw,
    connectorTypes,
    chargerType,
    pricePerKwh,
    currency,
    isOpen24Hours,
    hours,
    lastUpdatedAt,
  } = station;

  const statusStyle = getStationStatusStyle(status);
  const chargingRows = [];

  if (chargerType != null) {
    chargingRows.push({
      key: "charger-type",
      icon: "flash-outline",
      label: "Charger Type",
      value: CHARGER_TYPE_LABELS[chargerType] ?? chargerType,
    });
  }

  if (maxPowerKw != null) {
    chargingRows.push({
      key: "maximum-power",
      icon: "speedometer-outline",
      label: "Maximum Power",
      value: `${maxPowerKw} kW`,
    });
  }

  if (Array.isArray(connectorTypes) && connectorTypes.length > 0) {
    chargingRows.push({
      key: "connector-types",
      icon: "git-branch-outline",
      label: "Connector Types",
      value: connectorTypes.join(", "),
    });
  }

  if (availableConnectors != null) {
    chargingRows.push({
      key: "available-connectors",
      icon: "battery-charging-outline",
      label: "Available Connectors",
      value: `${availableConnectors}`,
    });
  }

  if (totalConnectors != null) {
    chargingRows.push({
      key: "total-connectors",
      icon: "layers-outline",
      label: "Total Connectors",
      value: `${totalConnectors}`,
    });
  }

  const priceText = formatPrice(pricePerKwh, currency);
  const operatingHoursRow =
    isOpen24Hours === true ? (
      <SettingRow icon="time-outline" label="Open 24/7" value="Always open" last />
    ) : hours != null ? (
      <SettingRow icon="time-outline" label="Hours" value={hours} last />
    ) : null;

  const handleDirectionsPress = () => {
    // TODO: hand off to the OS maps app via Linking once the map/location
    // phase lands. Intentionally inert for this UI-only phase.
    console.log("Get Directions pressed for station:", station.id);
  };

  return (
    <Screen scroll contentContainerStyle={styles.content}>
      <View style={styles.header}>
        <Pressable
          onPress={() => navigation.goBack()}
          accessibilityRole="button"
          accessibilityLabel="Go back"
          hitSlop={8}
          style={({ pressed }) => [styles.backButton, pressed && styles.pressed]}
        >
          <Ionicons name="chevron-back" size={22} color={Theme.colors.textSecondary} />
        </Pressable>

        <Card style={styles.heroCard}>
          <View style={styles.heroTop}>
            <View style={styles.heroIcon}>
              <Ionicons name="flash" size={24} color={Theme.colors.primary} />
            </View>
            <View style={styles.heroText}>
              <Text style={styles.heroName}>{name}</Text>
              {network ? <Text style={styles.heroNetwork}>{network}</Text> : null}
            </View>
          </View>

          {address ? <Text style={styles.heroAddress}>{address}</Text> : null}

          <View style={styles.heroMetaRow}>
            <View style={styles.heroMeta}>
              <Ionicons name="navigate-outline" size={16} color={Theme.colors.textSecondary} />
              <Text style={styles.heroMetaText}>{distanceKm} km away</Text>
            </View>
            {statusStyle ? (
              <View style={styles.heroMeta}>
                <Ionicons name={statusStyle.icon} size={16} color={statusStyle.color} />
                <Text style={[styles.heroStatus, { color: statusStyle.color }]}>
                  {statusStyle.label}
                </Text>
              </View>
            ) : null}
          </View>

          {lastUpdatedAt ? (
            <Text style={styles.heroUpdated}>Updated {formatUpdatedAt(lastUpdatedAt)}</Text>
          ) : null}
        </Card>
      </View>

      {chargingRows.length > 0 ? (
        <SettingsSection title="Charging">
          {chargingRows.map((row, index) => (
            <SettingRow
              key={row.key}
              icon={row.icon}
              label={row.label}
              value={row.value}
              last={index === chargingRows.length - 1}
            />
          ))}
        </SettingsSection>
      ) : null}

      {priceText ? (
        <SettingsSection title="Pricing">
          <SettingRow icon="cash-outline" label="Price" value={priceText} last />
        </SettingsSection>
      ) : null}

      {operatingHoursRow ? (
        <SettingsSection title="Operating Hours">{operatingHoursRow}</SettingsSection>
      ) : null}

      <Button title="Get Directions" onPress={handleDirectionsPress} />
    </Screen>
  );
}

const styles = StyleSheet.create({
  content: {
    gap: Theme.spacing.lg,
    paddingBottom: Theme.spacing.lg,
  },
  header: {
    gap: Theme.spacing.md,
  },
  backButton: {
    width: 40,
    height: 40,
    borderRadius: Theme.radius.pill,
    backgroundColor: Theme.colors.surface,
    borderWidth: 1,
    borderColor: Theme.colors.border,
    alignItems: "center",
    justifyContent: "center",
    marginTop: Theme.spacing.sm,
  },
  pressed: {
    opacity: 0.7,
  },
  heroCard: {
    gap: Theme.spacing.sm,
  },
  heroTop: {
    flexDirection: "row",
    alignItems: "center",
    gap: Theme.spacing.md,
  },
  heroIcon: {
    width: 48,
    height: 48,
    borderRadius: Theme.radius.pill,
    backgroundColor: Theme.colors.surfaceElevated,
    alignItems: "center",
    justifyContent: "center",
  },
  heroText: {
    flex: 1,
    gap: 2,
  },
  heroName: {
    ...Theme.typography.h3,
    color: Theme.colors.textPrimary,
  },
  heroNetwork: {
    ...Theme.typography.caption,
    color: Theme.colors.textSecondary,
  },
  heroAddress: {
    ...Theme.typography.body,
    color: Theme.colors.textSecondary,
  },
  heroMetaRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: Theme.spacing.lg,
    marginTop: Theme.spacing.xs,
    flexWrap: "wrap",
  },
  heroMeta: {
    flexDirection: "row",
    alignItems: "center",
    gap: Theme.spacing.xs,
  },
  heroMetaText: {
    ...Theme.typography.body,
    color: Theme.colors.textSecondary,
  },
  heroStatus: {
    ...Theme.typography.body,
    fontWeight: "600",
  },
  heroUpdated: {
    ...Theme.typography.caption,
    color: Theme.colors.textMuted,
  },
});
