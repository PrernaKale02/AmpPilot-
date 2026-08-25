import { createNativeStackNavigator } from "@react-navigation/native-stack";
import { AuthNavigator } from "./AuthNavigator";
import { MainNavigator } from "./MainNavigator";
import { Theme } from "../theme/theme";

const Stack = createNativeStackNavigator();

/**
 * Root stack nesting the auth and main flows as screens.
 *
 * Nesting both (rather than swapping which one renders) lets screens inside
 * the auth flow navigate straight into the main flow, e.g. `navigation.replace("Main", { screen: "PairVehicle" })`.
 *
 * @returns {React.JSX.Element}
 */
export function AppNavigator() {
  // TODO: once authentication state is available, set initialRouteName to
  // "Main" when signed in and "Auth" when signed out.
  return (
    <Stack.Navigator
      screenOptions={{
        headerShown: false,
        animation: "fade",
        contentStyle: { backgroundColor: Theme.colors.background },
      }}
    >
      <Stack.Screen name="Auth" component={AuthNavigator} />
      <Stack.Screen name="Main" component={MainNavigator} />
    </Stack.Navigator>
  );
}
