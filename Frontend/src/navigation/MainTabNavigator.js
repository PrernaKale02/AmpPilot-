import { createBottomTabNavigator } from "@react-navigation/bottom-tabs";
import { Ionicons } from "@expo/vector-icons";
import DashboardScreen from "../features/dashboard/screens/DashboardScreen";
import BatteryScreen from "../features/battery/screens/BatteryScreen";
import { ChargingNavigator } from "./ChargingNavigator";
import InsightsScreen from "../features/insights/screens/InsightsScreen";
import ProfileScreen from "../features/profile/screens/ProfileScreen";
import { Theme } from "../theme/theme";

const Tab = createBottomTabNavigator();

const TAB_ICONS = {
  Home: "home-outline",
  Battery: "battery-half-outline",
  Charging: "flash-outline",
  Insights: "bulb-outline",
  Profile: "person-circle-outline",
};

/**
 * Permanent post-pairing app shell.
 *
 * Hosts the five top-level sections behind a bottom tab bar. Profile is
 * the complete "You" section — account, vehicle, preferences, support,
 * and app info all live there; there is no separate Settings tab.
 *
 * @returns {React.JSX.Element}
 */
export function MainTabNavigator() {
  return (
    <Tab.Navigator
      screenOptions={({ route }) => ({
        headerShown: false,
        tabBarActiveTintColor: Theme.colors.primary,
        tabBarInactiveTintColor: Theme.colors.textMuted,
        tabBarStyle: {
          backgroundColor: Theme.colors.surface,
          borderTopColor: Theme.colors.border,
        },
        tabBarIcon: ({ color, size }) => (
          <Ionicons name={TAB_ICONS[route.name]} size={size} color={color} />
        ),
      })}
    >
      <Tab.Screen name="Home" component={DashboardScreen} />
      <Tab.Screen name="Battery" component={BatteryScreen} />
      <Tab.Screen name="Charging" component={ChargingNavigator} />
      <Tab.Screen name="Insights" component={InsightsScreen} />
      <Tab.Screen name="Profile" component={ProfileScreen} />
    </Tab.Navigator>
  );
}
