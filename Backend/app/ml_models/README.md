# ML model files

| File | In git? | What it is |
|---|---|---|
| `final_model.pt` (any `*.pt`) | **No** (gitignored) | Trained PyTorch weights. Copy them onto the server yourself. |
| `model_config.json` | Yes | Normalisation constants, target scaling, fault and RUL thresholds of the deployed model. |
| `models.py` | Yes | Network definitions, copied unchanged from the training notebook. |
| `rul_estimates.csv` | Yes | Per-car remaining-life table from the notebook (optional; for `GET /battery/rul/{car_id}`). |
| `sample_session.json` | Yes | One real 128 x 8 charging session (no label, no dataset), the first demo session. |
| `demo/*.json` | Yes | Healthy and faulty demo cars made by `make_demo_sessions_colab.py`. |

## Deploying the v2 model (battery_multitask_v2 notebook)

The notebook's last cell writes everything the backend needs to `processed_v2/`.
Copy these into this folder:

1. `final_model.pt` (the BiLSTM + attention, no manufacturer flag)
2. `model_config.json` (replaces the old file; the backend reads the notebook's format directly)
3. `models.py` (only if the notebook's copy differs from the one here)
4. `rul_estimates.csv`

Then in `Backend/.env` set `MODEL_WEIGHTS_FILE=final_model.pt`, restart, and open
`GET /battery/model-info`: `loaded` and `per_dataset_normalisation` must be `true`.

Checkpoints from the first notebook (capacity head named `capacity_head`) also
load; the backend renames the key. Models with a manufacturer flag (11 inputs)
are not supported.

## Normalisation (read this)

The v2 model was trained with **per-dataset** (per-manufacturer) mean/std and does
not receive the manufacturer as an input. So:

* `"dataset": 1|2|3` in the request normalises exactly as in training
  (`"normalisation": "per_dataset"`).
* Without `dataset` the notebook's config has no pooled constants, so the backend
  averages the three datasets' constants and reports `"normalisation": "approximate"`.
  The demo files carry their dataset, so they are always exact.

## Outputs

* Capacity and SoH leave the network standardised; the backend converts them with
  the config's means and stds. SoH is clipped to 0-100.
* Fault leaves as a logit; the backend applies a sigmoid. The config's
  `fault_threshold` (validation-chosen, very low) is informational only and is
  never applied: the API returns the probability as an experimental risk score.

## Demo sessions (healthy and faulty cars)

1. In Colab, copy `processed_v2` from Drive and run `make_demo_sessions_colab.py`.
   It needs `X.npy, y_label.npy, car_ids.npy, dataset_num.npy, car_split.csv`
   and writes sessions from held-out test cars only. Cars in `CHOSEN_CARS`
   (default `3_515`, the faulty car the notebook explains) are picked in advance.
2. Copy the files into `demo/` and restart the backend.
3. `GET /battery/demo-sessions` lists them; the app shows them in a picker.
4. For Swagger, paste a file's content into `POST /battery/predict`. The extra
   keys (`title`, `true_label`, ...) are ignored, so the file works unchanged.
