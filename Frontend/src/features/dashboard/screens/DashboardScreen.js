import { useEffect, useState } from "react";
import { Text, View, StyleSheet } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { Screen, AppHeader } from "../../../components/layout";
import { Card } from "../../../components/ui/Card";
import { Theme } from "../../../theme/theme";
import { getDashboard } from "../services/dashboardService";

/**
 * Dashboard screen. Gives a calm, at-a-glance overview of the user's
 * EV battery: health, vehicle connection, an insight, and recent charging.
 *
 * @returns {React.JSX.Element}
 */
export default function DashboardScreen() {
  const [dashboard, setDashboard] = useState(null);

  useEffect(() => {
    let isMounted = true;
    getDashboard().then((data) => {
      if (isMounted) setDashboard(data);
    });
    return () => {
      isMounted = false;
    };
  }, []);

  if (!dashboard) {
    return <Screen />;
  }

  const { greeting, batteryHealth, vehicle, insight, recentCharging } = dashboard;

  return (
    <Screen scroll contentContainerStyle={styles.content}>
      <AppHeader title={greeting.title} subtitle={greeting.subtitle} />

      <Card style={styles.card}>
        <View style={styles.cardHeader}>
          <Ionicons
            name="battery-charging-outline"
            size={18}
            color={Theme.colors.textSecondary}
          />
          <Text style={styles.cardLabel}>Battery Health</Text>
        </View>
        <Text style={styles.batteryPercentage}>{batteryHealth.percentage}%</Text>
        <Text style={styles.batteryStatus}>{batteryHealth.status}</Text>
      </Card>

      <Card style={styles.card}>
        <View style={styles.cardHeader}>
          <Ionicons
            name="car-sport-outline"
            size={16}
            color={Theme.colors.textSecondary}
          />
          <Text style={styles.cardLabel}>Vehicle</Text>
        </View>
        <Text style={styles.cardContent}>{vehicle.summary}</Text>
      </Card>

      <Card style={styles.card}>
        <View style={styles.cardHeader}>
          <Ionicons
            name="bulb-outline"
            size={16}
            color={Theme.colors.textSecondary}
          />
          <Text style={styles.cardLabel}>Today's Insight</Text>
        </View>
        <Text style={styles.cardContent}>{insight.message}</Text>
      </Card>

      <Card style={styles.card}>
        <View style={styles.cardHeader}>
          <Ionicons
            name="flash-outline"
            size={16}
            color={Theme.colors.textSecondary}
          />
          <Text style={styles.cardLabel}>Recent Charging</Text>
        </View>
        <Text style={styles.cardContent}>{recentCharging.summary}</Text>
      </Card>
    </Screen>
  );
}

const styles = StyleSheet.create({
  content: {
    gap: Theme.spacing.lg,
    paddingBottom: Theme.spacing.lg,
  },
  card: {
    gap: Theme.spacing.xs,
  },
  cardHeader: {
    flexDirection: "row",
    alignItems: "center",
    gap: Theme.spacing.xs,
  },
  cardLabel: {
    ...Theme.typography.overline,
    color: Theme.colors.textSecondary,
    textTransform: "uppercase",
  },
  cardContent: {
    ...Theme.typography.body,
    color: Theme.colors.textPrimary,
  },
  batteryPercentage: {
    ...Theme.typography.display,
    color: Theme.colors.textPrimary,
    marginTop: Theme.spacing.xs,
  },
  batteryStatus: {
    ...Theme.typography.body,
    color: Theme.colors.success,
    fontWeight: "600",
  },
});
