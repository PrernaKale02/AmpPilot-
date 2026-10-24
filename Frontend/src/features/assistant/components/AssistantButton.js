import { useRef, useState } from "react";
import { ActivityIndicator, Platform, Pressable, StyleSheet, Text, TextInput, View } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import * as Location from "expo-location";
import * as Speech from "expo-speech";
import { AudioModule, RecordingPresets, setAudioModeAsync, useAudioRecorder } from "expo-audio";
import { Theme } from "../../../theme/theme";
import { askAssistant, askAssistantByVoice } from "../services/assistantService";

const MAX_RECORDING_MS = 10000; // auto-stop long recordings

/** Browser speech recognition (Safari/Chrome). Returns null where unavailable. */
function createRecognizer() {
  if (Platform.OS !== "web" || typeof window === "undefined") return null;
  const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  return Recognition ? new Recognition() : null;
}

async function getLocation() {
  try {
    const { status } = await Location.requestForegroundPermissionsAsync();
    if (status !== "granted") return {};
    const position = await Location.getCurrentPositionAsync({});
    return { latitude: position.coords.latitude, longitude: position.coords.longitude };
  } catch {
    return {};
  }
}

function say(text) {
  Speech.stop();
  Speech.speak(text, { language: "en-IN", rate: 0.95 });
}

/**
 * Floating mic: listen → ask the backend assistant → speak the reply → act.
 * Web: browser speech recognition. Phone app: records audio, the backend
 * transcribes it with Gemini.
 */
export function AssistantButton({ navigation }) {
  const [open, setOpen] = useState(false);
  const [state, setState] = useState("idle"); // idle | listening | thinking
  const [heard, setHeard] = useState("");
  const [reply, setReply] = useState("");
  const [typed, setTyped] = useState("");
  const recognizerRef = useRef(null);
  const stopTimerRef = useRef(null);
  const recorder = useAudioRecorder(RecordingPresets.HIGH_QUALITY);

  const handleResult = (result) => {
    setReply(result.reply);
    say(result.reply);
    if (result.action === "show_stations") {
      navigation.navigate("Charging", { screen: "NearbyStations" });
    }
  };

  const handleFailure = () => {
    const message = "Sorry, the assistant is unavailable right now.";
    setReply(message);
    say(message);
  };

  // Typed question, or a transcript from browser speech recognition
  const ask = async (message) => {
    const text = message.trim();
    if (!text) return;
    setHeard(text);
    setReply("");
    setState("thinking");
    try {
      const location = await getLocation();
      handleResult(await askAssistant({ message: text, ...location }));
    } catch {
      handleFailure();
    } finally {
      setState("idle");
    }
  };

  // ---- Phone app: record, then send the audio ----
  const startRecording = async () => {
    const { granted } = await AudioModule.requestRecordingPermissionsAsync();
    if (!granted) {
      setReply("Microphone permission is needed to ask by voice. You can type your question below.");
      return;
    }
    Speech.stop();
    await setAudioModeAsync({ playsInSilentMode: true, allowsRecording: true });
    await recorder.prepareToRecordAsync();
    recorder.record();
    setHeard("");
    setReply("");
    setState("listening");
    stopTimerRef.current = setTimeout(() => stopRecording(), MAX_RECORDING_MS);
  };

  const stopRecording = async () => {
    clearTimeout(stopTimerRef.current);
    setState("thinking");
    try {
      await recorder.stop();
      // switch back to playback so the reply plays through the speaker
      await setAudioModeAsync({ playsInSilentMode: true, allowsRecording: false });
      const uri = recorder.uri;
      if (!uri) throw new Error("No recording");
      const location = await getLocation();
      const result = await askAssistantByVoice({ uri, ...location });
      setHeard(result.transcript || "(didn't catch that)");
      handleResult(result);
    } catch {
      handleFailure();
    } finally {
      setState("idle");
    }
  };

  // ---- Web: browser speech recognition ----
  const startWebListening = () => {
    const recognizer = createRecognizer();
    if (!recognizer) {
      setReply("Voice input isn't supported in this browser. Please use Chrome or Safari, or type below.");
      return;
    }
    recognizerRef.current = recognizer;
    recognizer.lang = "en-IN";
    recognizer.interimResults = false;
    recognizer.maxAlternatives = 1;
    recognizer.onresult = (event) => ask(event.results[0][0].transcript);
    recognizer.onerror = () => setState("idle");
    recognizer.onend = () => setState((current) => (current === "listening" ? "idle" : current));
    Speech.stop();
    setHeard("");
    setReply("");
    setState("listening");
    recognizer.start();
  };

  const onMicPress = () => {
    setOpen(true);
    if (state === "thinking") return;
    if (Platform.OS === "web") {
      if (state === "listening") recognizerRef.current?.stop();
      else startWebListening();
      return;
    }
    if (state === "listening") stopRecording();
    else startRecording();
  };

  const sendTyped = () => {
    ask(typed);
    setTyped("");
  };

  const statusText =
    state === "listening"
      ? Platform.OS === "web" ? "Listening…" : "Listening… tap to stop"
      : state === "thinking" ? "Thinking…" : "Ask AmpPilot";

  return (
    <>
      {open ? (
        <View style={styles.panel}>
          <View style={styles.panelHeader}>
            <Text style={styles.panelTitle}>{statusText}</Text>
            <Pressable accessibilityRole="button" accessibilityLabel="Close assistant" onPress={() => setOpen(false)} hitSlop={12}>
              <Ionicons name="close" size={20} color={Theme.colors.textSecondary} />
            </Pressable>
          </View>
          {heard ? <Text style={styles.heard}>“{heard}”</Text> : null}
          {state === "thinking" ? <ActivityIndicator color={Theme.colors.primary} /> : null}
          {reply ? <Text style={styles.reply}>{reply}</Text> : null}
          <View style={styles.inputRow}>
            <TextInput
              value={typed}
              onChangeText={setTyped}
              onSubmitEditing={sendTyped}
              placeholder="Or type a question…"
              placeholderTextColor={Theme.colors.textMuted}
              style={styles.input}
              accessibilityLabel="Type a question for the assistant"
            />
            <Pressable accessibilityRole="button" accessibilityLabel="Send question" onPress={sendTyped} style={styles.send}>
              <Ionicons name="send" size={18} color={Theme.colors.primary} />
            </Pressable>
          </View>
        </View>
      ) : null}

      <Pressable
        accessibilityRole="button"
        accessibilityLabel={state === "listening" ? "Stop listening" : "Ask the assistant"}
        onPress={onMicPress}
        style={[styles.fab, state === "listening" && styles.fabListening]}
      >
        <Ionicons name={state === "listening" ? "stop" : "mic"} size={26} color="#fff" />
      </Pressable>
    </>
  );
}

const styles = StyleSheet.create({
  fab: {
    position: "absolute",
    right: 20,
    bottom: 24,
    width: 60,
    height: 60,
    borderRadius: 30,
    backgroundColor: Theme.colors.primary,
    alignItems: "center",
    justifyContent: "center",
    elevation: 6,
    shadowColor: "#000",
    shadowOpacity: 0.3,
    shadowRadius: 8,
    shadowOffset: { width: 0, height: 4 },
  },
  fabListening: { backgroundColor: Theme.colors.danger },
  panel: {
    position: "absolute",
    right: 20,
    left: 20,
    bottom: 96,
    maxWidth: 420,
    alignSelf: "flex-end",
    backgroundColor: Theme.colors.surface,
    borderColor: Theme.colors.border,
    borderWidth: 1,
    borderRadius: 16,
    padding: 16,
    gap: 10,
  },
  panelHeader: { flexDirection: "row", justifyContent: "space-between", alignItems: "center" },
  panelTitle: { ...Theme.typography.h3, color: Theme.colors.textPrimary },
  heard: { ...Theme.typography.body, color: Theme.colors.textSecondary, fontStyle: "italic" },
  reply: { ...Theme.typography.body, color: Theme.colors.textPrimary },
  inputRow: { flexDirection: "row", alignItems: "center", gap: 8 },
  input: {
    flex: 1,
    ...Theme.typography.body,
    color: Theme.colors.textPrimary,
    borderColor: Theme.colors.border,
    borderWidth: 1,
    borderRadius: 12,
    paddingHorizontal: 12,
    minHeight: 44,
  },
  send: { width: 44, height: 44, alignItems: "center", justifyContent: "center" },
});