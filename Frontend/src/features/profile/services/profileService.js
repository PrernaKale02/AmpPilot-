import { profileMock } from "../data/profile";

/**
 * Fetches the profile overview: account owner, connected vehicle, driving
 * summary, achievements, account status, and app preferences.
 *
 * Reads local mock data today; will call `GET /profile` once the FastAPI
 * backend is available.
 *
 * @returns {Promise<typeof profileMock>}
 */
export async function getProfile() {
  return profileMock;
}
