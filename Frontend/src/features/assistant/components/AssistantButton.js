import { useRef, useState } from "react";
import { ActivityIndicator, Platform, Pressable, StyleSheet, Text, TextInput, View } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import * as Location from "expo-location";
import * as Speech from "expo-speech";
import { AudioModule, RecordingPresets, setAudioModeAsync, useAudioRecorder } from "expo-audio";
import { Theme } from "../../../theme/theme";
import { askAssistant, askAssistantByVoice } from "../services/assistantService";
import { logAssistantError, logAssistantWarning } from "../services/assistantLogger";

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
    if (status !== "granted") {
      logAssistantWarning("location_permission_denied");
      return {};
    }
    const position = await Location.getCurrentPositionAsync({});
    return { latitude: position.coords.latitude, longitude: position.coords.longitude };
  } catch (error) {
    logAssistantError("location_lookup", error, { fallback: "continue_without_location" });
    return {};
  }
}

function stopSpeech() {
  try {
    Promise.resolve(Speech.stop()).catch((error) => logAssistantError("speech_stop", error));
  } catch (error) {
    logAssistantError("speech_stop", error);
  }
}

function say(text) {
  stopSpeech();
  try {
    Speech.speak(text, {
      language: "en-IN",
      rate: 0.95,
      onError: (error) => logAssistantError("speech_playback", error),
    });
  } catch (error) {
    logAssistantError("speech_playback", error);
  }
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

  const handleFailure = (stage, error) => {
    logAssistantError(stage, error, { platform: Platform.OS });
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
    } catch (error) {
      handleFailure("question_processing", error);
    } finally {
      setState("idle");
    }
  };

  // ---- Phone app: record, then send the audio ----
  const startRecording = async () => {
    try {
      const { granted } = await AudioModule.requestRecordingPermissionsAsync();
      if (!granted) {
        logAssistantWarning("microphone_permission_denied", { platform: Platform.OS });
        setReply("Microphone permission is needed to ask by voice. You can type your question below.");
        return;
      }
      stopSpeech();
      await setAudioModeAsync({ playsInSilentMode: true, allowsRecording: true });
      await recorder.prepareToRecordAsync();
      recorder.record();
      setHeard("");
      setReply("");
      setState("listening");
      stopTimerRef.current = setTimeout(() => stopRecording(), MAX_RECORDING_MS);
    } catch (error) {
      handleFailure("recording_start", error);
      setState("idle");
    }
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
    } catch (error) {
      handleFailure("recording_submit", error);
    } finally {
      setState("idle");
    }
  };

  // ---- Web: browser speech recognition ----
  const startWebListening = () => {
    try {
      const recognizer = createRecognizer();
      if (!recognizer) {
        logAssistantWarning("speech_recognition_unsupported", { platform: Platform.OS });
        setReply("Voice input isn't supported in this browser. Please use Chrome or Safari, or type below.");
        return;
      }
      recognizerRef.current = recognizer;
      recognizer.lang = "en-IN";
      recognizer.interimResults = false;
      recognizer.maxAlternatives = 1;
      recognizer.onresult = (event) => {
        const transcript = event.results?.[0]?.[0]?.transcript;
        if (!transcript) {
          logAssistantWarning("speech_recognition_empty_result");
          setState("idle");
          return;
        }
        ask(transcript);
      };
      recognizer.onerror = (event) => {
        logAssistantError("speech_recognition", event.error || event.message || "Recognition failed", {
          code: event.error,
        });
        setState("idle");
      };
      recognizer.onend = () => setState((current) => (current === "listening" ? "idle" : current));
      stopSpeech();
      setHeard("");
      setReply("");
      setState("listening");
      recognizer.start();
    } catch (error) {
      handleFailure("speech_recognition_start", error);
      setState("idle");
    }
  };

  const onMicPress = () => {
    setOpen(true);
    if (state === "thinking") return;
    if (Platform.OS === "web") {
      if (state === "listening") {
        try {
          recognizerRef.current?.stop();
        } catch (error) {
          handleFailure("speech_recognition_stop", error);
          setState("idle");
        }
      }
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