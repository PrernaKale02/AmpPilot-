import { notificationsMock } from "../data/notifications";

/**
 * Fetches notifications, most recent first.
 *
 * Reads local mock data today; will call `GET /notifications` on the
 * FastAPI backend later.
 *
 * @returns {Promise<typeof notificationsMock>}
 */
export async function getNotifications() {
  return notificationsMock;
}
