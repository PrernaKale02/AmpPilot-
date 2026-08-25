import { useEffect, useState } from "react";
import { StyleSheet, Text, View } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { Screen, AppHeader } from "../../../components/layout";
import { Card, SettingRow, SettingsSection } from "../../../components/ui";
import { Theme } from "../../../theme/theme";
import { getProfile } from "../services/profileService";
import { ProfileHeader } from "../components/ProfileHeader";
import { ConnectedVehicleCard } from "../components/ConnectedVehicleCard";
import { ProfileStatCard } from "../components/ProfileStatCard";
import { AchievementCard } from "../components/AchievementCard";
import { AccountStatusCard } from "../components/AccountStatusCard";

const STAT_ICONS = {
  totalDistance: "map-outline",
  averageEfficiency: "speedometer-outline",
  ownership: "calendar-outline",
};

const STAT_LABELS = {
  totalDistance: "Total Distance",
  averageEfficiency: "Average Efficiency",
  ownership: "Ownership",
};

/**
 * Profile screen — the complete "You" section of the app. A read-only
 * overview of the owner's account, connected vehicle, and driving summary,
 * followed by the app preferences, support links, and app info that used
 * to live on a separate Settings tab. Reads from
 * `profileService.getProfile()` so the UI is ready for a real backend
 * without changes.
 *
 * Notifications and Units are controlled locally in React state, seeded
 * from the fetched preferences; toggling them does not (yet) round-trip
 * to a backend.
 *
 * @returns {React.JSX.Element}
 */
export default function ProfileScreen() {
  const [data, setData] = useState(null);
  const [notificationsEnabled, setNotificationsEnabled] = useState(false);
  const [units, setUnits] = useState("Metric");

  useEffect(() => {
    let isMounted = true;
    getProfile().then((result) => {
      if (isMounted) {
        setData(result);
        setNotificationsEnabled(result.preferences.notifications);
        setUnits(result.preferences.units);
      }
    });
    return () => {
      isMounted = false;
    };
  }, []);

  if (!data) {
    return <Screen />;
  }

  const { profile, vehicle, stats, achievements, account, preferences, version } = data;

  return (
    <Screen scroll contentContainerStyle={styles.content}>
      <AppHeader title="Profile" subtitle="Your EV journey at a glance." />

      <ProfileHeader name={profile.name} email={profile.email} />

      <ConnectedVehicleCard name={vehicle.name} status={vehicle.status} />

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Driving Summary</Text>
        <View style={styles.statsGrid}>
          {Object.entries(stats).map(([key, value]) => (
            <ProfileStatCard key={key} icon={STAT_ICONS[key]} label={STAT_LABELS[key]} value={value} />
          ))}
        </View>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Achievements</Text>
        <View style={styles.achievementList}>
          {achievements.map((achievement) => (
            <AchievementCard
              key={achievement.id}
              title={achievement.title}
              description={achievement.description}
            />
          ))}
        </View>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Account Status</Text>
        <AccountStatusCard mode={account.mode} lastSync={account.lastSync} />
      </View>

      <SettingsSection title="Preferences">
        <SettingRow
          icon="notifications-outline"
          label="Notifications"
          switchValue={notificationsEnabled}
          onSwitchChange={setNotificationsEnabled}
        />
        <SettingRow
          icon="speedometer-outline"
          label="Units"
          value={units}
          onPress={() => setUnits((current) => (current === "Metric" ? "Imperial" : "Metric"))}
        />
        <SettingRow
          icon="moon-outline"
          label="Theme"
          value={preferences.theme}
          subtitle="System themes coming soon."
          last
        />
      </SettingsSection>

      <SettingsSection title="Support">
        <SettingRow icon="shield-checkmark-outline" label="Privacy Policy" chevron onPress={() => {}} />
        <SettingRow icon="help-circle-outline" label="Help & Support" chevron onPress={() => {}} />
        <SettingRow icon="information-circle-outline" label="About" chevron onPress={() => {}} last />
      </SettingsSection>

      <SettingsSection title="About" card={false}>
        <Card style={styles.aboutCard}>
          <Ionicons name="flash" size={28} color={Theme.colors.primary} />
          <Text style={styles.aboutTitle}>AmpPilot</Text>
          <Text style={styles.aboutVersion}>Version {version}</Text>
          <Text style={styles.aboutTagline}>Made with ❤️ for EV owners.</Text>
        </Card>
      </SettingsSection>
    </Screen>
  );
}

const styles = StyleSheet.create({
  content: {
    gap: Theme.spacing.lg,
    paddingBottom: Theme.spacing.lg,
  },
  section: {
    gap: Theme.spacing.sm,
  },
  sectionTitle: {
    ...Theme.typography.overline,
    color: Theme.colors.textSecondary,
    textTransform: "uppercase",
  },
  statsGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: Theme.spacing.md,
  },
  achievementList: {
    gap: Theme.spacing.sm,
  },
  aboutCard: {
    alignItems: "center",
    gap: Theme.spacing.xs,
    paddingVertical: Theme.spacing.xl,
  },
  aboutTitle: {
    ...Theme.typography.h3,
    color: Theme.colors.textPrimary,
    marginTop: Theme.spacing.xs,
  },
  aboutVersion: {
    ...Theme.typography.caption,
    color: Theme.colors.textSecondary,
  },
  aboutTagline: {
    ...Theme.typography.caption,
    color: Theme.colors.textSecondary,
    marginTop: Theme.spacing.xs,
  },
});
