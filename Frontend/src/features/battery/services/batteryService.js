import { api } from "../../../services/api";
import { batteryMock } from "../data/battery";

// The first prediction after the server starts can take a while (the model loads
// on demand), so these calls get more time than the shared 10 s default.
const MODEL_TIMEOUT_MS = 30000;

/**
 * Fetches the current battery overview: score, status, key metrics, and a
 * charging recommendation.
 *
 * Reads local mock data today; will call `GET /battery` once the FastAPI
 * backend and BLE integration are available.
 *
 * @returns {Promise<typeof batteryMock>}
 */
export async function getBattery() {
  return batteryMock;
}

/**
 * Lists the demo sessions the backend can run through the model: a bundled
 * sample plus any healthy/faulty cars exported from the training notebook.
 *
 * @returns {Promise<Array<{
 *   id: string,
 *   title: string,
 *   description: string,
 *   dataset: 1 | 2 | 3 | null,
 *   true_label: 0 | 1 | null
 * }>>}
 */
export async function getDemoSessions() {
  const response = await api.get("/battery/demo-sessions", {
    timeout: MODEL_TIMEOUT_MS,
  });
  return response.data;
}

/**
 * Asks the backend model to predict one demo session. The app has no live
 * telemetry source yet, so this is how the Battery screen shows real model
 * output. The result describes the demo session, not the user's own battery.
 * `true_label` is the dataset's label (0 healthy, 1 faulty), not a model output.
 * `fault_probability` is an experimental risk score; the API gives no yes/no.
 *
 * @param {string} [sessionId="sample_session"] - Id from `getDemoSessions()`.
 * @returns {Promise<{
 *   capacity: number,
 *   soh_percent: number,
 *   fault_probability: number,
 *   model_name: string,
 *   normalisation: "global" | "per_dataset" | "approximate",
 *   session_id: string,
 *   title: string,
 *   dataset: 1 | 2 | 3 | null,
 *   true_label: 0 | 1 | null
 * }>}
 */
export async function getDemoPrediction(sessionId = "sample_session") {
  const response = await api.get(
    `/battery/demo-sessions/${encodeURIComponent(sessionId)}`,
    {
      timeout: MODEL_TIMEOUT_MS,
    },
  );
  return response.data;
}

/**
 * Sends one real 128 x 8 charging-session reading sequence to the backend
 * battery model. Not used by the Battery screen until the app has a live
 * telemetry source.
 *
 * @param {number[][]} readings - 128 timesteps of the backend's eight sensor channels.
 * @param {object} [options]
 * @param {1|2|3} [options.dataset] - Training dataset (manufacturer) the session comes from; enables the exact training normalisation.
 * @param {boolean} [options.includeAttention=false] - Also return the 128 attention weights.
 * @returns {Promise<{capacity: number, soh_percent: number, fault_probability: number, model_name: string, normalisation: string, attention_weights?: number[], top_attention_rows?: number[]}>}
 */
export async function predictBattery(readings, options = {}) {
  const { dataset, includeAttention = false } = options;
  const body = { readings };
  if (dataset) body.dataset = dataset;
  if (includeAttention) body.include_attention = true;
  const response = await api.post("/battery/predict", body, {
    timeout: MODEL_TIMEOUT_MS,
  });
  return response.data;
}
