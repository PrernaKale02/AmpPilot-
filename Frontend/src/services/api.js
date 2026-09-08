import axios from "axios";

/**
 * Shared HTTP client for feature services.
 *
 * Set `EXPO_PUBLIC_API_URL` to the backend base URL, for example
 * `http://192.168.x.x:8001`.
 *
 * Physical devices cannot reach a dev machine through `localhost`, so the
 * backend address must point at the machine's LAN IP during device testing.
 */
export const api = axios.create({
  baseURL: process.env.EXPO_PUBLIC_API_URL,
  timeout: 10000,
});

/**
 * Confirms that the configured backend is reachable.
 *
 * @returns {Promise<{ status: string }>}
 */
export async function healthCheck() {
  const response = await api.get("/health");
  return response.data;
}
