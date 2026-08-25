import { useEffect, useState } from "react";
import { StyleSheet, Text, View } from "react-native";
import { Screen, AppHeader } from "../../../components/layout";
import { Theme } from "../../../theme/theme";
import { getInsights } from "../services/insightsService";
import { InsightScoreCard } from "../components/InsightScoreCard";
import { TodaysInsightCard } from "../components/TodaysInsightCard";
import { InsightRecommendationCard } from "../components/InsightRecommendationCard";
import { InsightHistoryCard } from "../components/InsightHistoryCard";

/**
 * Insights screen — battery score, today's insight, a recommendation with
 * its expected benefit, and a history of past insights. Reads from
 * `insightsService.getInsights()` so the UI is ready for a real backend
 * without changes.
 *
 * @returns {React.JSX.Element}
 */
export default function InsightsScreen() {
  const [insights, setInsights] = useState(null);

  useEffect(() => {
    let isMounted = true;
    getInsights().then((data) => {
      if (isMounted) setInsights(data);
    });
    return () => {
      isMounted = false;
    };
  }, []);

  if (!insights) {
    return <Screen />;
  }

  const { batteryScore, scoreStatus, todaysInsight, recommendation, history } = insights;

  return (
    <Screen scroll contentContainerStyle={styles.content}>
      <AppHeader title="Insights" subtitle="Personalized battery recommendations." />

      <InsightScoreCard score={batteryScore} status={scoreStatus} />

      <TodaysInsightCard
        title={todaysInsight.title}
        message={todaysInsight.message}
        severity={todaysInsight.severity}
      />

      <InsightRecommendationCard
        title={recommendation.title}
        message={recommendation.message}
        expectedBenefit={recommendation.expectedBenefit}
        severity={recommendation.severity}
      />

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>History</Text>
        <View style={styles.historyList}>
          {history.map((insight) => (
            <InsightHistoryCard key={insight.id} insight={insight} />
          ))}
        </View>
      </View>
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
  historyList: {
    gap: Theme.spacing.sm,
  },
});
