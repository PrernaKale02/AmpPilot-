import { createNativeStackNavigator } from "@react-navigation/native-stack";
import ChargingScreen from "../features/charging/screens/ChargingScreen";
import NearbyStationsScreen from "../features/charging/screens/NearbyStationsScreen";
import StationDetailsScreen from "../features/charging/screens/StationDetailsScreen";
import { Theme } from "../theme/theme";

const Stack = createNativeStackNavigator();

/**
 * Charging tab flow: the charging overview, the nearby charging stations
 * list, and a single station's details.
 *
 * Nested inside the Charging tab rather than the root stack so the bottom
 * tab bar stays visible while browsing stations.
 *
 * @returns {React.JSX.Element}
 */
export function ChargingNavigator() {
  return (
    <Stack.Navigator
      screenOptions={{
        headerShown: false,
        animation: "fade",
        contentStyle: { backgroundColor: Theme.colors.background },
      }}
    >
      <Stack.Screen name="ChargingHome" component={ChargingScreen} />
      <Stack.Screen name="NearbyStations" component={NearbyStationsScreen} />
      <Stack.Screen name="StationDetails" component={StationDetailsScreen} />
    </Stack.Navigator>
  );
}
