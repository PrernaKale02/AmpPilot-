import { createNativeStackNavigator } from "@react-navigation/native-stack";
import PairVehicleScreen from "../features/vehicle/screens/PairVehicleScreen";
import { MainTabNavigator } from "./MainTabNavigator";
import { Theme } from "../theme/theme";

const Stack = createNativeStackNavigator();

/**
 * Post-authentication flow: pair a vehicle, then the tabbed app shell.
 *
 * @returns {React.JSX.Element}
 */
export function MainNavigator() {
  return (
    <Stack.Navigator
      screenOptions={{
        headerShown: false,
        animation: "fade",
        contentStyle: { backgroundColor: Theme.colors.background },
      }}
    >
      <Stack.Screen name="PairVehicle" component={PairVehicleScreen} />
      <Stack.Screen name="MainTabs" component={MainTabNavigator} />
    </Stack.Navigator>
  );
}
