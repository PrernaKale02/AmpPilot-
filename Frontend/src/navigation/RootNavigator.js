import { NavigationContainer } from "@react-navigation/native";
import { AppNavigator } from "./AppNavigator";

/**
 * Root of the app's navigation tree.
 *
 * Owns the single NavigationContainer and delegates all flow decisions
 * to AppNavigator.
 *
 * @returns {React.JSX.Element}
 */
export function RootNavigator() {
  return (
    <NavigationContainer>
      <AppNavigator />
    </NavigationContainer>
  );
}
