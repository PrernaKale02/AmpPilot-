/**
 * Mock notifications, most recent first.
 *
 * Shape mirrors what the future FastAPI `GET /notifications` endpoint will
 * return.
 */
export const notificationsMock = [
  {
    id: "note-002",
    title: "Charging complete",
    body: "Your vehicle finished charging to 90%.",
    read: false,
    createdAt: "2026-07-22T09:15:00Z",
  },
  {
    id: "note-001",
    title: "New insight available",
    body: "We found a way to improve your battery's long-term health.",
    read: true,
    createdAt: "2026-07-20T08:05:00Z",
  },
];
