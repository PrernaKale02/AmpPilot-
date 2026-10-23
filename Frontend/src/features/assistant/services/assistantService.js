import { api } from "../../../services/api";

/** Sends a question to the backend assistant. Gemini can take a while, so allow 45 s. */
export async function askAssistant({ message, latitude, longitude }) {
  const response = await api.post(
    "/api/assistant",
    { message, latitude, longitude },
    { timeout: 45000 }
  );
  return response.data; // { reply, action }
}