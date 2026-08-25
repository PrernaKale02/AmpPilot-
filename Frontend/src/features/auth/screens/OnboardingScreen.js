import { useCallback, useRef, useState } from "react";
import { FlatList, StyleSheet, Text, View, useWindowDimensions } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { useNavigation } from "@react-navigation/native";
import { Screen } from "../../../components/layout/Screen";
import { Button } from "../../../components/ui/Button";
import { Theme } from "../../../theme/theme";

const PAGES = [
  {
    icon: "battery-charging-outline",
    title: "Welcome to AmpPilot",
    subtitle: "Understand your EV battery with clear insights and intelligent recommendations.",
  },
  {
    icon: "flash-outline",
    title: "Charge Smarter",
    subtitle: "Track charging habits and discover ways to improve long-term battery health.",
  },
  {
    icon: "shield-checkmark-outline",
    title: "Stay Ahead",
    subtitle: "Receive proactive insights before small battery issues become expensive problems.",
  },
];

/**
 * Single swipeable onboarding page: an icon illustration, title, and subtitle.
 *
 * @param {object} props
 * @param {{icon: string, title: string, subtitle: string}} props.page - Page content.
 * @param {number} props.width - Page width, matched to the window so FlatList paging works.
 * @returns {React.JSX.Element}
 */
function OnboardingPage({ page, width }) {
  return (
    <View style={[styles.page, { width }]}>
      <View style={styles.illustration}>
        <Ionicons name={page.icon} size={72} color={Theme.colors.primary} />
      </View>
      <Text style={styles.title}>{page.title}</Text>
      <Text style={styles.subtitle}>{page.subtitle}</Text>
    </View>
  );
}

/**
 * Row of dots indicating which onboarding page is active.
 *
 * @param {object} props
 * @param {number} props.count - Total number of pages.
 * @param {number} props.activeIndex - Index of the currently visible page.
 * @returns {React.JSX.Element}
 */
function PageIndicator({ count, activeIndex }) {
  return (
    <View style={styles.indicatorRow}>
      {Array.from({ length: count }).map((_, index) => (
        <View
          key={index}
          style={[styles.dot, index === activeIndex && styles.dotActive]}
        />
      ))}
    </View>
  );
}

/**
 * Three-page introduction to AmpPilot shown before login.
 *
 * Lets the user swipe through the value proposition, or skip straight
 * to login at any point.
 *
 * @returns {React.JSX.Element}
 */
export default function OnboardingScreen() {
  const navigation = useNavigation();
  const { width } = useWindowDimensions();
  const [activeIndex, setActiveIndex] = useState(0);
  const listRef = useRef(null);
  const isLastPage = activeIndex === PAGES.length - 1;

  const goToLogin = useCallback(() => {
    navigation.replace("Login");
  }, [navigation]);

  const handleNext = useCallback(() => {
    if (isLastPage) {
      goToLogin();
      return;
    }
    listRef.current?.scrollToIndex({ index: activeIndex + 1, animated: true });
  }, [activeIndex, isLastPage, goToLogin]);

  const handleBack = useCallback(() => {
    listRef.current?.scrollToIndex({ index: activeIndex - 1, animated: true });
  }, [activeIndex]);

  const handleMomentumScrollEnd = useCallback(
    (event) => {
      const index = Math.round(event.nativeEvent.contentOffset.x / width);
      setActiveIndex(index);
    },
    [width]
  );

  return (
    <Screen noPadding style={styles.screen}>
      <FlatList
        ref={listRef}
        data={PAGES}
        keyExtractor={(page) => page.title}
        renderItem={({ item }) => <OnboardingPage page={item} width={width} />}
        horizontal
        pagingEnabled
        showsHorizontalScrollIndicator={false}
        onMomentumScrollEnd={handleMomentumScrollEnd}
        getItemLayout={(_, index) => ({ length: width, offset: width * index, index })}
      />

      <View style={styles.footer}>
        <PageIndicator count={PAGES.length} activeIndex={activeIndex} />

        <View style={styles.controls}>
          <Button
            title={isLastPage ? "Back" : "Skip"}
            variant="ghost"
            fullWidth={false}
            onPress={isLastPage ? handleBack : goToLogin}
            style={styles.skipButton}
          />
          <Button
            title={isLastPage ? "Get Started" : "Next"}
            fullWidth={false}
            onPress={handleNext}
            style={styles.nextButton}
          />
        </View>
      </View>
    </Screen>
  );
}

const styles = StyleSheet.create({
  screen: {
    backgroundColor: Theme.colors.background,
  },
  page: {
    alignItems: "center",
    justifyContent: "center",
    paddingHorizontal: Theme.spacing.xl,
  },
  illustration: {
    width: 160,
    height: 160,
    borderRadius: Theme.radius.pill,
    backgroundColor: Theme.colors.surfaceElevated,
    alignItems: "center",
    justifyContent: "center",
    marginBottom: Theme.spacing.xxl,
  },
  title: {
    ...Theme.typography.h1,
    color: Theme.colors.textPrimary,
    textAlign: "center",
  },
  subtitle: {
    ...Theme.typography.body,
    color: Theme.colors.textSecondary,
    textAlign: "center",
    marginTop: Theme.spacing.md,
    maxWidth: 300,
  },
  footer: {
    paddingHorizontal: Theme.spacing.lg,
    paddingTop: Theme.spacing.lg,
    paddingBottom: Theme.spacing.xl,
  },
  indicatorRow: {
    flexDirection: "row",
    justifyContent: "center",
    marginBottom: Theme.spacing.xl,
  },
  dot: {
    width: 8,
    height: 8,
    borderRadius: Theme.radius.pill,
    backgroundColor: Theme.colors.surfaceElevated,
    marginHorizontal: Theme.spacing.xs,
  },
  dotActive: {
    backgroundColor: Theme.colors.primary,
    width: 20,
  },
  controls: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
  },
  skipButton: {
    paddingHorizontal: Theme.spacing.sm,
  },
  nextButton: {
    minWidth: 140,
  },
});
