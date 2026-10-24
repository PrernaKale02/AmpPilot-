import { api } from "../../../services/api";

/** Sends a typed question to the backend assistant. Gemini can take a while, so allow 45 s. */
export async function askAssistant({ message, latitude, longitude }) {
  const response = await api.post(
    "/api/assistant",
    { message, latitude, longitude },
    { timeout: 45000 }
  );
  return response.data; // { reply, action }
}

/** Uploads a recorded question (phone app); the backend transcribes it with Gemini. */
export async function askAssistantByVoice({ uri, latitude, longitude }) {
  const form = new FormData();
  form.append("audio", { uri, name: "question.m4a", type: "audio/mp4" });
  if (latitude != null) form.append("latitude", String(latitude));
  if (longitude != null) form.append("longitude", String(longitude));

  const response = await fetch(`${process.env.EXPO_PUBLIC_API_URL}/api/assistant/voice`, {
    method: "POST",
    body: form,
  });
  if (!response.ok) throw new Error(`Voice request failed: ${response.status}`);
  return response.json(); // { transcript, reply, action }
}