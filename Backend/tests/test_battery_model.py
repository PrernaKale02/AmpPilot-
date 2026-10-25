"""Pure-numpy tests for the battery model service (no torch, no weights)."""

import json
from pathlib import Path

import numpy as np
import pytest

from app.services import battery_model as bm

SAMPLE = json.loads(bm.SAMPLE_SESSION_PATH.read_text(encoding="utf-8"))["readings"]
SHIPPED_CONFIG = bm.ML_DIR / "model_config.json"


def _config_dict(**overrides):
    cfg = {k: v for k, v in bm._DEFAULT_CONFIG.items()}
    cfg.update(overrides)
    return cfg


def _write(tmp_path: Path, cfg: dict) -> Path:
    path = tmp_path / "model_config.json"
    path.write_text(json.dumps(cfg), encoding="utf-8")
    return path


def test_sample_session_has_expected_shape():
    assert len(SAMPLE) == bm.N_STEPS
    assert all(len(row) == bm.N_CHANNELS for row in SAMPLE)


def test_missing_config_falls_back_to_original_constants(tmp_path):
    config = bm.load_config(tmp_path / "does_not_exist.json")
    assert config.model_name == "final_model_no_mfg"
    assert config.fault_threshold == 0.5
    assert config.per_dataset == {}


def test_shipped_config_matches_builtin_constants():
    """The committed model_config.json must describe the committed model."""
    shipped = bm.load_config(SHIPPED_CONFIG)
    builtin = bm.load_config(None)
    np.testing.assert_allclose(shipped.sensor_mean, builtin.sensor_mean)
    np.testing.assert_allclose(shipped.sensor_std, builtin.sensor_std)
    assert shipped.capacity_mean == builtin.capacity_mean
    assert shipped.fault_threshold == builtin.fault_threshold


def test_global_normalisation_of_first_row():
    config = bm.load_config(None)
    arr, mode = bm.normalise(SAMPLE, config)
    assert mode == "global"
    assert arr.shape == (128, 8)
    # voltage, current, SOC and time of row 1 (worked example in the report)
    assert arr[0, 0] == pytest.approx(0.61, abs=0.01)
    assert arr[0, 1] == pytest.approx(0.40, abs=0.01)
    assert arr[0, 2] == pytest.approx(0.83, abs=0.01)
    assert arr[0, 7] == pytest.approx(-1.72, abs=0.01)


def test_per_dataset_constants_are_used_only_when_requested_and_present(tmp_path):
    per = {"2": {"sensor_mean": [0.0] * 8, "sensor_std": [1.0] * 8}}
    config = bm.load_config(_write(tmp_path, _config_dict(per_dataset=per)))

    arr2, mode2 = bm.normalise(SAMPLE, config, dataset=2)
    assert mode2 == "per_dataset"
    np.testing.assert_allclose(arr2, np.asarray(SAMPLE, dtype=np.float32))

    _, mode1 = bm.normalise(SAMPLE, config, dataset=1)  # no constants for 1
    assert mode1 == "global"
    _, mode_none = bm.normalise(SAMPLE, config, dataset=None)
    assert mode_none == "global"


def test_normalise_rejects_wrong_shape():
    config = bm.load_config(None)
    with pytest.raises(ValueError):
        bm.normalise(SAMPLE[:127], config)


@pytest.mark.parametrize(
    "overrides",
    [
        {"sensor_mean": [0.0] * 7},
        {"sensor_std": [1.0] * 7},
        {"sensor_std": [0.0] * 8},
        {"per_dataset": {"1": {"sensor_mean": [0.0] * 8, "sensor_std": [0.0] * 8}}},
    ],
)
def test_malformed_config_is_rejected(tmp_path, overrides):
    with pytest.raises(ValueError):
        bm.load_config(_write(tmp_path, _config_dict(**overrides)))


def test_invalid_json_config_is_rejected(tmp_path):
    path = tmp_path / "model_config.json"
    path.write_text("{not json", encoding="utf-8")
    with pytest.raises(ValueError):
        bm.load_config(path)


def test_finalise_converts_to_real_units_without_a_yes_no_decision():
    config = bm.load_config(None)
    out = bm.finalise(0.0, 0.0, 0.0, config)
    assert out["capacity"] == pytest.approx(config.capacity_mean, abs=0.01)
    assert out["soh_percent"] == pytest.approx(config.soh_mean, abs=0.01)
    assert out["fault_probability"] == 0.5
    assert out["fault_probability_experimental"] is True
    assert "is_faulty" not in out and "fault_threshold" not in out


def test_finalise_converts_the_logit_with_a_sigmoid():
    config = bm.load_config(None)
    assert bm.finalise(0.0, 0.0, -2.0, config)["fault_probability"] == pytest.approx(0.119, abs=0.001)
    assert bm.finalise(0.0, 0.0, 2.0, config)["fault_probability"] == pytest.approx(0.881, abs=0.001)


def test_finalise_clamps_soh_and_survives_extreme_logits():
    config = bm.load_config(None)
    assert bm.finalise(0.0, 100.0, 0.0, config)["soh_percent"] == 100.0
    assert bm.finalise(0.0, -100.0, 0.0, config)["soh_percent"] == 0.0
    assert bm.finalise(0.0, 0.0, 1e9, config)["fault_probability"] == 1.0
    assert bm.finalise(0.0, 0.0, -1e9, config)["fault_probability"] == 0.0


# ---- config written by the v2 training notebook ------------------------------

def _notebook_config(**overrides):
    cfg = {
        "arch": "BiLSTM+Attn", "input_size": 8, "seq_len": 128,
        "channels": ["voltage", "current", "SOC", "max_cell_v", "min_cell_v", "max_temp", "min_temp", "time"],
        "fault_threshold": 0.0124, "rul_threshold_soh": 80.0,
        "cap_mean": 40.5, "cap_std": 2.0, "soh_mean": 94.0, "soh_std": 4.0,
        "ds_mean": {"1": [1.0] * 8, "2": [3.0] * 8, "3": [5.0] * 8},
        "ds_std": {"1": [2.0] * 8, "2": [2.0] * 8, "3": [4.0] * 8},
        "pos_weight": 4.9,
    }
    cfg.update(overrides)
    return cfg


def test_notebook_config_is_converted(tmp_path):
    config = bm.load_config(_write(tmp_path, _notebook_config()))
    assert config.fault_threshold == 0.0124
    assert (config.capacity_mean, config.capacity_std) == (40.5, 2.0)
    assert (config.soh_mean, config.soh_std) == (94.0, 4.0)
    assert sorted(config.per_dataset) == ["1", "2", "3"]
    np.testing.assert_allclose(config.per_dataset["3"][0], [5.0] * 8)
    # pooled fallback is the plain average of the datasets, and flagged as such
    np.testing.assert_allclose(config.sensor_mean, [3.0] * 8)
    np.testing.assert_allclose(config.sensor_std, [8 / 3] * 8)
    assert config.pooled_is_approximate is True


def test_notebook_config_normalisation_modes(tmp_path):
    config = bm.load_config(_write(tmp_path, _notebook_config()))
    row = [[5.0] * 8] * 128
    arr3, mode3 = bm.normalise(row, config, dataset=3)
    assert mode3 == "per_dataset"
    np.testing.assert_allclose(arr3, np.zeros((128, 8)), atol=1e-6)  # (5 - 5) / 4
    arr, mode = bm.normalise(row, config, dataset=None)
    assert mode == "approximate"
    assert arr[0, 0] == pytest.approx((5.0 - 3.0) / (8 / 3), abs=1e-4)


def test_legacy_config_is_not_flagged_approximate():
    config = bm.load_config(None)
    assert config.pooled_is_approximate is False
    assert bm.normalise(SAMPLE, config)[1] == "global"


def test_notebook_config_keeps_the_architecture_name_and_channels(tmp_path):
    config = bm.load_config(_write(tmp_path, _notebook_config(arch="CNN-LSTM")))
    assert config.arch == "CNN-LSTM"
    assert config.channels[3] == "max_cell_v"
    assert config.rul_threshold_soh == 80.0


def test_config_for_a_model_with_a_manufacturer_flag_is_rejected(tmp_path):
    with pytest.raises(ValueError, match="manufacturer flag"):
        bm.load_config(_write(tmp_path, _notebook_config(input_size=11)))


def test_config_with_wrong_number_of_channel_names_is_rejected(tmp_path):
    with pytest.raises(ValueError):
        bm.load_config(_write(tmp_path, _notebook_config(channels=["a", "b"])))


def test_notebook_config_missing_keys_is_rejected(tmp_path):
    cfg = _notebook_config()
    del cfg["cap_mean"]
    with pytest.raises(ValueError):
        bm.load_config(_write(tmp_path, cfg))


def test_remap_state_dict_keys_renames_only_the_capacity_head():
    old = {"lstm.weight": 1, "capacity_head.0.weight": 2, "soh_head.0.weight": 3, "fault_head.3.bias": 4}
    new = bm.remap_state_dict_keys(old)
    assert new == {"lstm.weight": 1, "cap_head.0.weight": 2, "soh_head.0.weight": 3, "fault_head.3.bias": 4}
    assert bm.remap_state_dict_keys(new) == new  # v2 checkpoints pass through unchanged


def test_warm_up_never_raises_and_reports_missing_weights(monkeypatch):
    from app.core import config

    monkeypatch.setenv("MODEL_WEIGHTS_FILE", "definitely_missing.pt")
    config.get_settings.cache_clear()
    bm.reset_model_cache()
    try:
        assert bm.warm_up() is False
    finally:
        config.get_settings.cache_clear()


# ---- explanation helpers ------------------------------------------------------

def test_top_rows_orders_by_weight():
    weights = [0.01] * 128
    weights[7], weights[3], weights[90] = 0.5, 0.3, 0.2
    assert bm.top_rows(weights, 3) == [7, 3, 90]
    assert len(bm.top_rows(weights)) == bm.TOP_ATTENTION_ROWS


def test_channel_sensitivities_are_absolute_shifts_by_name():
    names = bm.DEFAULT_CHANNELS
    base = 1.0
    ablated = [1.0, 0.99, 0.995, 0.016, 1.0, 1.0, 1.0, 1.0]
    out = bm.channel_sensitivities(base, ablated, names)
    assert list(out) == list(names)
    assert out["max_cell_v"] == pytest.approx(0.984)  # the notebook's explained faulty car
    assert out["voltage"] == 0.0


def test_channel_sensitivities_need_one_value_per_channel():
    with pytest.raises(ValueError):
        bm.channel_sensitivities(0.5, [0.5] * 7, bm.DEFAULT_CHANNELS)


def test_get_config_reads_the_shipped_file():
    config = bm.get_config()
    assert config.arch == "BiLSTM+Attn" and config.input_size == 8


def test_build_network_reports_a_missing_models_file(tmp_path, monkeypatch):
    from app.core.exceptions import ModelUnavailable

    monkeypatch.setattr(bm, "MODELS_FILE", tmp_path / "models.py")
    with pytest.raises(ModelUnavailable):
        bm._build_network(bm.load_config(None))


def test_shipped_models_file_defines_the_expected_architectures():
    """Static check (no torch): the notebook's three architectures and the v2 head names."""
    import ast

    tree = ast.parse(bm.MODELS_FILE.read_text(encoding="utf-8"))
    classes = {node.name for node in tree.body if isinstance(node, ast.ClassDef)}
    functions = {node.name for node in tree.body if isinstance(node, ast.FunctionDef)}
    assert {"BiLSTMAttention", "DeepLSTM", "CNNLSTM"} <= classes
    assert "build_model" in functions
    source = bm.MODELS_FILE.read_text(encoding="utf-8")
    assert "self.cap_head" in source and "capacity_head" not in source