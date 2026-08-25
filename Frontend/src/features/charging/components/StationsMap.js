import { useMemo, useRef, useState } from "react";
import { Pressable, StyleSheet, View } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import MapView, { Marker } from "react-native-maps";
import { Theme } from "../../../theme/theme";
import { getStationStatusStyle } from "./stationStatusStyles";
import { StationCard } from "./StationCard";

/** Span used when there are no stations to frame, in degrees (~9 km tall). */
const FALLBACK_DELTA = 0.08;

/** Never zoom in tighter than this, so a station 100 m away isn't magnified. */
const MIN_DELTA = 0.02;

/** Never zoom out further than this, whatever the search radius. */
const MAX_DELTA = 0.5;

/** Multiplies the farthest station offset to leave the markers some margin. */
const REGION_PADDING = 2.6;

/**
 * Open Charge Map records occasionally arrive without usable coordinates.
 * A marker cannot be placed for those, so they are dropped rather than
 * pinned at (0, 0).
 *
 * @param {object} station - Charging station record.
 * @returns {boolean}
 */
function hasValidCoordinates(station) {
  const { latitude, longitude } = station ?? {};

  return (
    Number.isFinite(latitude) &&
    Number.isFinite(longitude) &&
    latitude >= -90 &&
    latitude <= 90 &&
    longitude >= -180 &&
    longitude <= 180
  );
}

/**
 * Clamps a map span to the range the screen is willing to open at.
 *
 * @param {number} delta - Proposed span, in degrees.
 * @returns {number}
 */
function clampDelta(delta) {
  return Math.min(MAX_DELTA, Math.max(MIN_DELTA, delta));
}

/**
 * Builds the region the map opens at: centred on the user, wide enough for
 * the stations that were actually returned.
 *
 * @param {{ latitude: number, longitude: number }} userLocation - Where the user is.
 * @param {Array<object>} stations - Stations with valid coordinates.
 * @returns {{ latitude: number, longitude: number, latitudeDelta: number, longitudeDelta: number }}
 */
function getInitialRegion(userLocation, stations) {
  if (stations.length === 0) {
    return {
      ...userLocation,
      latitudeDelta: FALLBACK_DELTA,
      longitudeDelta: FALLBACK_DELTA,
    };
  }

  let farthestLatitude = 0;
  let farthestLongitude = 0;

  for (const station of stations) {
    farthestLatitude = Math.max(
      farthestLatitude,
      Math.abs(station.latitude - userLocation.latitude),
    );
    farthestLongitude = Math.max(
      farthestLongitude,
      Math.abs(station.longitude - userLocation.longitude),
    );
  }

  return {
    ...userLocation,
    latitudeDelta: clampDelta(farthestLatitude * REGION_PADDING),
    longitudeDelta: clampDelta(farthestLongitude * REGION_PADDING),
  };
}

/**
 * Map view for the Nearby Stations screen.
 *
 * Renders the stations the screen already fetched - it never loads data of
 * its own, so toggling List/Map costs nothing.
 *
 * @param {object} props
 * @param {{ latitude: number, longitude: number }} props.userLocation - Coordinates the station search ran from.
 * @param {Array<object>} props.stations - Stations as returned by the API, nearest first.
 * @param {(station: object) => void} props.onSelectStation - Called when the station preview is pressed.
 * @returns {React.JSX.Element}
 */
export function StationsMap({ userLocation, stations, onSelectStation }) {
  const mapRef = useRef(null);
  const [selectedStation, setSelectedStation] = useState(null);
  const mappableStations = useMemo(() => stations.filter(hasValidCoordinates), [stations]);
  const initialRegion = useMemo(
    () => getInitialRegion(userLocation, mappableStations),
    [userLocation, mappableStations],
  );

  const handleRecenter = () => {
    mapRef.current?.animateToRegion(
      {
        ...userLocation,
        latitudeDelta: initialRegion.latitudeDelta,
        longitudeDelta: initialRegion.longitudeDelta,
      },
      400,
    );
  };

  return (
    <View style={styles.container}>
      <MapView
        ref={mapRef}
        style={styles.map}
        initialRegion={initialRegion}
        showsUserLocation
        showsMyLocationButton={false}
        toolbarEnabled={false}
        onPress={() => setSelectedStation(null)}
      >
        {mappableStations.map((station) => (
          <StationMarker key={station.id} station={station} onSelect={setSelectedStation} />
        ))}
      </MapView>

      <View style={styles.overlay} pointerEvents="box-none">
        <Pressable
          onPress={handleRecenter}
          accessibilityRole="button"
          accessibilityLabel="Recenter on my location"
          hitSlop={8}
          style={({ pressed }) => [styles.recenterButton, pressed && styles.pressed]}
        >
          <Ionicons name="locate" size={20} color={Theme.colors.textPrimary} />
        </Pressable>

        {selectedStation ? (
          <StationCard
            station={selectedStation}
            onPress={() => onSelectStation(selectedStation)}
          />
        ) : null}
      </View>
    </View>
  );
}

/**
 * A single station pin.
 *
 * The pin is drawn small to suit the map, but sits inside a larger
 * transparent box: Google Maps hit-tests the marker's whole bitmap, so the
 * padding widens the tap target without changing how the pin looks.
 *
 * @param {object} props
 * @param {object} props.station - Charging station record with valid coordinates.
 * @param {(station: object) => void} props.onSelect - Called when the pin is tapped.
 * @returns {React.JSX.Element}
 */
function StationMarker({ station, onSelect }) {
  // While tracksViewChanges is on, react-native-maps swaps this marker's
  // icon on a 40ms loop forever, which burns CPU and keeps resetting the
  // pin Google Maps is hit-testing against. Track only until the pin has
  // laid out once, then stop.
  const [tracksViewChanges, setTracksViewChanges] = useState(true);

  const { latitude, longitude, status } = station;
  const markerColor = getStationStatusStyle(status)?.color ?? Theme.colors.primary;

  return (
    <Marker
      coordinate={{ latitude, longitude }}
      anchor={{ x: 0.5, y: 0.5 }}
      tracksViewChanges={tracksViewChanges}
      onPress={() => onSelect(station)}
    >
      <View style={styles.markerHitArea} onLayout={() => setTracksViewChanges(false)}>
        <View style={[styles.marker, { backgroundColor: markerColor }]}>
          <View style={styles.markerCore} />
        </View>
      </View>
    </Marker>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    minHeight: 260,
    borderRadius: Theme.radius.lg,
    borderWidth: 1,
    borderColor: Theme.colors.border,
    overflow: "hidden",
  },
  map: {
    flex: 1,
  },
  pressed: {
    opacity: 0.7,
  },
  // Sits over the map, anchored to the bottom. box-none so the empty area
  // still passes pan and zoom gestures through to the map underneath.
  overlay: {
    ...StyleSheet.absoluteFillObject,
    justifyContent: "flex-end",
    padding: Theme.spacing.md,
    gap: Theme.spacing.sm,
  },
  recenterButton: {
    alignSelf: "flex-end",
    width: 44,
    height: 44,
    borderRadius: Theme.radius.pill,
    backgroundColor: Theme.colors.surface,
    borderWidth: 1,
    borderColor: Theme.colors.border,
    alignItems: "center",
    justifyContent: "center",
  },
  // Transparent padding around the pin. Google Maps hit-tests the whole
  // marker bitmap, so this is what makes the pin comfortably tappable.
  markerHitArea: {
    width: 44,
    height: 44,
    alignItems: "center",
    justifyContent: "center",
  },
  marker: {
    width: 22,
    height: 22,
    borderRadius: Theme.radius.pill,
    borderWidth: 2,
    borderColor: Theme.colors.white,
    alignItems: "center",
    justifyContent: "center",
  },
  markerCore: {
    width: 6,
    height: 6,
    borderRadius: Theme.radius.pill,
    backgroundColor: Theme.colors.white,
  },
});
