import { createNativeStackNavigator } from "@react-navigation/native-stack";
import SplashScreen from "../features/auth/screens/SplashScreen";
import OnboardingScreen from "../features/auth/screens/OnboardingScreen";
import LoginScreen from "../features/auth/screens/LoginScreen";
import { Theme } from "../theme/theme";

const Stack = createNativeStackNavigator();

/**
 * Pre-authentication flow: splash, onboarding, then login.
 *
 * @returns {React.JSX.Element}
 */
export function AuthNavigator() {
  return (
    <Stack.Navigator
      screenOptions={{
        headerShown: false,
        animation: "fade",
        contentStyle: { backgroundColor: Theme.colors.background },
      }}
    >
      <Stack.Screen name="Splash" component={SplashScreen} />
      <Stack.Screen name="Onboarding" component={OnboardingScreen} />
      <Stack.Screen name="Login" component={LoginScreen} />
    </Stack.Navigator>
  );
}
