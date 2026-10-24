// Web-only stand-in: react-native-maps does not run in browsers.
// Phones still use StationsMap.js.
import { StyleSheet, Text, View } from "react-native";

export function StationsMap({ stations = [] }) {
  return (
    <View style={styles.box}>
      <Text style={styles.text}>
        Map view is available in the mobile app ({stations.length} stations found).
      </Text>
    </View>
  );
}

export default StationsMap;

const styles = StyleSheet.create({
  box: { height: 200, alignItems: "center", justifyContent: "center", borderRadius: 12, backgroundColor: "#1f2937", padding: 16 },
  text: { color: "#9ca3af", textAlign: "center" },
});
