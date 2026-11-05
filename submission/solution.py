"""Competition inference entry point for repeat demand and customer value."""

import json
import math
import sys
from pathlib import Path

import numpy as np


_SUBMISSION_DIR = str(Path(__file__).resolve().parent)
if _SUBMISSION_DIR not in sys.path:
    # The grader imports this file directly from the flat submission ZIP.
    sys.path.insert(0, _SUBMISSION_DIR)

from features import FEATURE_NAMES, matrix


_MODEL_PATH = Path(__file__).with_name("starter_model.json")
_VALUE_CAP = 2000.0
_MODEL = None
_LOG_COLUMNS = (1, 2, 3, 4)


def _numeric_vector(values, length, name):
    if not isinstance(values, list) or len(values) != length:
        raise ValueError(f"Model {name} must contain {length} numbers")
    if any(isinstance(value, bool) or not isinstance(value, (int, float)) for value in values):
        raise ValueError(f"Model {name} must contain numeric values")
    result = np.asarray(values, dtype=np.float64)
    if not np.isfinite(result).all():
        raise ValueError(f"Model {name} must contain finite numbers")
    return result


def _load_model():
    global _MODEL
    if _MODEL is not None:
        return _MODEL

    try:
        model = json.loads(_MODEL_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Could not load model parameters from {_MODEL_PATH.name}") from exc

    expected_keys = {"feature_names", "mean", "scale", "repeat", "value"}
    if not isinstance(model, dict) or set(model) != expected_keys:
        raise ValueError("Model file does not match the agreed parameter schema")
    if model["feature_names"] != list(FEATURE_NAMES):
        raise ValueError("Model feature order does not match submission/features.py")

    feature_count = len(FEATURE_NAMES)
    mean = _numeric_vector(model["mean"], feature_count, "mean")
    scale = _numeric_vector(model["scale"], feature_count, "scale")
    if np.any(scale <= 0.0):
        raise ValueError("Model scales must be positive")

    heads = {}
    for name in ("repeat", "value"):
        head = model[name]
        if not isinstance(head, dict) or set(head) != {"intercept", "coefficients"}:
            raise ValueError(f"Model {name} head has an invalid schema")
        intercept = head["intercept"]
        if isinstance(intercept, bool) or not isinstance(intercept, (int, float)):
            raise ValueError(f"Model {name} intercept must be numeric")
        if not math.isfinite(float(intercept)):
            raise ValueError(f"Model {name} intercept must be finite")
        coefficients = _numeric_vector(
            head["coefficients"], feature_count, f"{name} coefficients"
        )
        heads[name] = {
            "intercept": float(intercept),
            "coefficients": coefficients,
        }

    _MODEL = {"mean": mean, "scale": scale, **heads}
    return _MODEL


def _transform_features(observation):
    customer_ids = observation["customers"]
    if not isinstance(customer_ids, list) or any(
        not isinstance(customer_id, str) for customer_id in customer_ids
    ):
        raise ValueError("customers must be a list of string IDs")
    if len(set(customer_ids)) != len(customer_ids):
        raise ValueError("customers must contain unique IDs")

    budget = observation["budget"]
    if (
        isinstance(budget, bool)
        or not isinstance(budget, int)
        or budget < 1
        or budget > len(customer_ids)
    ):
        raise ValueError("budget must be a positive integer no greater than the roster size")

    value_cap = observation["value_cap"]
    if (
        isinstance(value_cap, bool)
        or not isinstance(value_cap, (int, float))
        or not math.isfinite(float(value_cap))
        or float(value_cap) != _VALUE_CAP
    ):
        raise ValueError("value_cap does not match the trained model")

    values = np.asarray(matrix(observation), dtype=np.float64)
    expected_shape = (len(customer_ids), len(FEATURE_NAMES))
    if values.shape != expected_shape or not np.isfinite(values).all():
        raise ValueError("Feature matrix has an invalid shape or non-finite values")

    values = values.copy()
    for column in _LOG_COLUMNS:
        values[:, column] = np.log1p(np.maximum(0.0, values[:, column]))
    values = np.clip(values, -1e6, 1e6)
    if not np.isfinite(values).all():
        raise ValueError("Transformed feature matrix must be finite")
    return customer_ids, budget, values


def decide(observation, state):
    """Return predictions for every roster customer and the fixed-budget shortlist."""
    del state  # State is reset for every case; inference is stateless.
    customer_ids, budget, features = _transform_features(observation)
    model = _load_model()
    scaled = (features - model["mean"]) / model["scale"]

    repeat = model["repeat"]
    logits = repeat["intercept"] + scaled @ repeat["coefficients"]
    probabilities = 1.0 / (1.0 + np.exp(-np.clip(logits, -700.0, 700.0)))

    value = model["value"]
    conditional_log_values = value["intercept"] + scaled @ value["coefficients"]
    conditional_values = np.expm1(
        np.clip(conditional_log_values, 0.0, np.log1p(_VALUE_CAP))
    )
    values = probabilities * conditional_values
    if (
        not np.isfinite(probabilities).all()
        or not np.isfinite(values).all()
        or np.any(probabilities < 0.0)
        or np.any(probabilities > 1.0)
        or np.any(values < 0.0)
        or np.any(values > _VALUE_CAP)
    ):
        raise ValueError("Model produced predictions outside the contract bounds")

    predictions = {
        customer_id: {
            "probability": float(probability),
            "value": float(predicted_value),
        }
        for customer_id, probability, predicted_value in zip(
            customer_ids, probabilities, values
        )
    }
    selected = sorted(
        customer_ids,
        key=lambda customer_id: (-predictions[customer_id]["value"], customer_id),
    )[:budget]

    return {
        "action": {"predictions": predictions, "selected": selected},
        "state": {},
    }
