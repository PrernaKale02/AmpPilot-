# Demo guide: battery health model

Two ways to show it: **Swagger** (the API with real input and output) and the
**app** (the Battery screen). Do the setup once, then pick either.

## Setup (once)

1. Copy from `processed_v2/` into `Backend/app/ml_models/`: `final_model.pt`,
   `model_config.json` (replace the old one) and `rul_estimates.csv`.
2. In `Backend/.env` set `MODEL_WEIGHTS_FILE=final_model.pt`.
3. **Faulty and healthy cars:** in Colab, copy `processed_v2` from Drive and run
   `make_demo_sessions_colab.py`. Copy the JSON files it writes into
   `Backend/app/ml_models/demo/`. They are sessions from held-out test cars.
4. Start the backend: `uvicorn app.main:app --host 0.0.0.0 --port 8001`
   (the Frontend `.env.example` shows 8010: use one port in both places).
5. Open `http://localhost:8001/battery/model-info`: `loaded` and
   `per_dataset_normalisation` must be `true`.
6. Open `http://localhost:8001/battery/demo-sessions`: you should see
   `healthy_ds1_a`, `faulty_ds1_a`, `faulty_3_515`, ... (plus `sample_session`).

## Demo 1: Swagger (`http://localhost:8001/docs`)

1. `GET /battery/demo-sessions`: the available cars.
2. `GET /battery/demo-sessions/healthy_ds1_a`, then `.../faulty_ds1_a` and
   `.../faulty_3_515`. Read out `soh_percent`, `capacity`, `fault_probability`
   and `true_label` (the dataset's label, not a model output).
3. **Explain a faulty car:** open `demo/faulty_3_515.json`, paste its whole content
   into `POST /battery/explain`, Execute. In the notebook, setting `max_cell_v`
   to its average moved this car's fault score by 0.98 and every other sensor by
   under 0.01. The attention was on the first time steps. Say this is how the
   model behaves on one session, not proof of the cause of a fault.
4. **Remaining life:** `GET /battery/rul/1_105` (precomputed table), or
   `POST /battery/rul` with at least 5 `{mileage_km, soh_percent}` points.
5. To show the raw input: paste any demo file into `POST /battery/predict`.
   Extra keys (`title`, `true_label`, ...) are ignored.

## Demo 2: the app

1. Set `EXPO_PUBLIC_API_URL=http://<your-PC-LAN-IP>:8001` in `Frontend/.env`
   (a phone cannot use `localhost`) and start Expo.
2. Open the Battery tab, scroll to the **Health model** card.
3. Tap the chips to switch between healthy and faulty cars. "Label in the dataset"
   shows the true label under the model's numbers.
4. The first request after starting the server can take a few seconds. If the
   card shows an error, tap "Try again".

## What to say (and not say)

* The model is the v2 BiLSTM with attention. It reads one 21-minute charging
  session (128 readings x 8 sensors) and estimates capacity, State of Health and
  a fault risk score.
* Capacity and SoH are modest (R2 about 0.35 and 0.21; SoH error about 2.5 points).
* **Faulty labels are per vehicle** (fire or lithium-plating reports), so a faulty
  car's session can look normal. A single faulty example may show a LOW fault
  risk. That is expected. Per car (average over its sessions) the fault AUC is
  about 0.87 in 5-fold cross-validation over all 48 faulty cars.
* The fault output is a risk score, not a diagnosis. The API gives no yes/no because
  the validation-chosen threshold (0.012) would flag almost every session.
* The BiLSTM was chosen by design (no manufacturer needed, attention for
  explanation, the one that was cross-validated), not as the metric winner: the
  architectures are close on only 9 faulty test cars.
* Do not run simulated or charging-station data through the model. It was
  trained on real sessions only.
* The Battery screen's big score and the other tiles are still mock data. Only
  the Health model card is real.

## If something fails

| Symptom | Fix |
|---|---|
| 503 `MODEL_UNAVAILABLE` | Weights, `models.py` or the config is missing/invalid. Check `/battery/model-info`. |
| `/battery/demo-sessions` shows only `sample_session` | Demo JSON files are not in `app/ml_models/demo/`. |
| `/battery/rul/{car}` gives 404 | That car has no precomputed estimate (fewer than 5 sessions or SoH not falling). |
| Card says "Model unavailable" | Backend not running, wrong `EXPO_PUBLIC_API_URL`, or phone not on the same Wi-Fi. |
| `normalisation: "approximate"` | No `dataset` was sent. Demo files always include it. |
