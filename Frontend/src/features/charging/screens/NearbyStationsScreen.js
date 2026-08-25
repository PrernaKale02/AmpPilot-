import { useEffect, useRef, useState } from "react";
import { ActivityIndicator, Linking, Pressable, StyleSheet, Text, View } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { useNavigation } from "@react-navigation/native";
import * as Location from "expo-location";
import { Screen, AppHeader } from "../../../components/layout";
import { Button, Card } from "../../../components/ui";
import { Theme } from "../../../theme/theme";
import { getNearbyChargingStations } from "../services/chargingService";
import { StationCard } from "../components/StationCard";
import { StationsMap } from "../components/StationsMap";

const SEARCH_RADIUS_KM = 15;

const VIEW_MODES = [
  { key: "list", label: "List", icon: "list-outline" },
  { key: "map", label: "Map", icon: "map-outline" },
];

/**
 * Nearby Stations screen - charging stations around the user, nearest
 * first.
 *
 * @returns {React.JSX.Element}
 */
export default function NearbyStationsScreen() {
  const navigation = useNavigation();
  const mountedRef = useRef(true);
  const [stations, setStations] = useState([]);
  const [userLocation, setUserLocation] = useState(null);
  const [viewMode, setViewMode] = useState("list");
  const [screenState, setScreenState] = useState({
    status: "loading",
    permissionCanAskAgain: true,
  });

  useEffect(() => {
    return () => {
      mountedRef.current = false;
    };
  }, []);

  const loadStations = async () => {
    setScreenState({ status: "loading", permissionCanAskAgain: true });

    try {
      const permission = await Location.requestForegroundPermissionsAsync();

      if (permission.status !== "granted") {
        if (!mountedRef.current) {
          return;
        }

        setScreenState({
          status: "permissionDenied",
          permissionCanAskAgain: permission.canAskAgain ?? true,
        });
        return;
      }

      const location = await Location.getCurrentPositionAsync({
        accuracy: Location.Accuracy.Balanced,
      });

      const origin = {
        latitude: location.coords.latitude,
        longitude: location.coords.longitude,
      };

      const data = await getNearbyChargingStations({
        ...origin,
        radiusKm: SEARCH_RADIUS_KM,
      });

      if (!mountedRef.current) {
        return;
      }

      setStations(data);
      setUserLocation(origin);
      setScreenState({
        status: "ready",
        permissionCanAskAgain: true,
      });
    } catch (error) {
      if (!mountedRef.current) {
        return;
      }

      setScreenState({
        status: "error",
        permissionCanAskAgain: true,
      });
    }
  };

  useEffect(() => {
    void loadStations();
  }, []);

  const handleRetry = () => {
    void loadStations();
  };

  const handleLocationAction = () => {
    if (screenState.permissionCanAskAgain) {
      void loadStations();
      return;
    }

    void Linking.openSettings();
  };

  const handleOpenStation = (station) => {
    navigation.navigate("StationDetails", { station });
  };

  // The map fills the screen, so it opts out of the Screen's ScrollView -
  // otherwise the two compete for the same vertical pan gesture.
  const showMap =
    screenState.status === "ready" && viewMode === "map" && userLocation !== null;

  const renderStateCard = (icon, title, body, actionLabel, onAction, loading = false) => (
    <Card style={styles.placeholderCard}>
      {loading ? (
        <ActivityIndicator color={Theme.colors.primary} />
      ) : (
        <Ionicons name={icon} size={32} color={Theme.colors.textMuted} />
      )}
      <Text style={styles.placeholderTitle}>{title}</Text>
      <Text style={styles.placeholderBody}>{body}</Text>
      {onAction ? <Button title={actionLabel} onPress={onAction} fullWidth={false} /> : null}
    </Card>
  );

  return (
    <Screen scroll={!showMap} contentContainerStyle={styles.content}>
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

        <AppHeader
          title="Nearby Stations"
          subtitle="Find charging stations near your current location."
        />
      </View>

      <View style={styles.toggle}>
        {VIEW_MODES.map((mode) => {
          const isActive = viewMode === mode.key;
          return (
            <Pressable
              key={mode.key}
              onPress={() => setViewMode(mode.key)}
              accessibilityRole="button"
              accessibilityState={{ selected: isActive }}
              style={({ pressed }) => [
                styles.toggleOption,
                isActive && styles.toggleOptionActive,
                pressed && styles.pressed,
              ]}
            >
              <Ionicons
                name={mode.icon}
                size={16}
                color={isActive ? Theme.colors.white : Theme.colors.textSecondary}
              />
              <Text style={[styles.toggleLabel, isActive && styles.toggleLabelActive]}>
                {mode.label}
              </Text>
            </Pressable>
          );
        })}
      </View>

      {screenState.status === "loading" ? (
        renderStateCard(
          "locate-outline",
          "Finding nearby stations",
          "Getting your current location and checking for charging stations nearby.",
          null,
          null,
          true,
        )
      ) : screenState.status === "permissionDenied" ? (
        renderStateCard(
          "location-outline",
          "Location access is required",
          "Turn on location access so AmpPilot can find charging stations near you.",
          screenState.permissionCanAskAgain ? "Try Again" : "Open Settings",
          handleLocationAction,
        )
      ) : screenState.status === "error" ? (
        renderStateCard(
          "warning-outline",
          "Couldn't load charging stations.",
          "Please try again in a moment.",
          "Retry",
          handleRetry,
        )
      ) : showMap ? (
        <StationsMap
          userLocation={userLocation}
          stations={stations}
          onSelectStation={handleOpenStation}
        />
      ) : (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Nearby</Text>

          {stations.length === 0 ? (
            <Card style={styles.placeholderCard}>
              <Ionicons name="flash-off-outline" size={32} color={Theme.colors.textMuted} />
              <Text style={styles.placeholderTitle}>No charging stations found</Text>
              <Text style={styles.placeholderBody}>
                There aren't any charging stations to show right now.
              </Text>
            </Card>
          ) : (
            <View style={styles.stationList}>
              {stations.map((station) => (
                <StationCard
                  key={station.id}
                  station={station}
                  onPress={() => handleOpenStation(station)}
                />
              ))}
            </View>
          )}
        </View>
      )}
    </Screen>
  );
}

const styles = StyleSheet.create({
  content: {
    gap: Theme.spacing.lg,
    paddingBottom: Theme.spacing.lg,
  },
  header: {
    gap: Theme.spacing.xs,
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
  },
  pressed: {
    opacity: 0.7,
  },
  toggle: {
    flexDirection: "row",
    gap: Theme.spacing.xs,
    padding: Theme.spacing.xs,
    backgroundColor: Theme.colors.surface,
    borderWidth: 1,
    borderColor: Theme.colors.border,
    borderRadius: Theme.radius.md,
  },
  toggleOption: {
    flex: 1,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: Theme.spacing.xs,
    paddingVertical: Theme.spacing.sm,
    borderRadius: Theme.radius.sm,
  },
  toggleOptionActive: {
    backgroundColor: Theme.colors.primary,
  },
  toggleLabel: {
    ...Theme.typography.caption,
    color: Theme.colors.textSecondary,
    fontWeight: "600",
  },
  toggleLabelActive: {
    color: Theme.colors.white,
  },
  section: {
    gap: Theme.spacing.sm,
  },
  sectionTitle: {
    ...Theme.typography.overline,
    color: Theme.colors.textSecondary,
    textTransform: "uppercase",
  },
  stationList: {
    gap: Theme.spacing.sm,
  },
  placeholderCard: {
    alignItems: "center",
    gap: Theme.spacing.xs,
    paddingVertical: Theme.spacing.xl,
  },
  placeholderTitle: {
    ...Theme.typography.h3,
    color: Theme.colors.textPrimary,
    marginTop: Theme.spacing.xs,
    textAlign: "center",
  },
  placeholderBody: {
    ...Theme.typography.caption,
    color: Theme.colors.textSecondary,
    textAlign: "center",
    maxWidth: 280,
  },
});
