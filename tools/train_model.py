r"""Fit and compare portable probability/value model heads.

Run from the repository root with:

    .\.venv\Scripts\python.exe tools/train_model.py  # Windows PowerShell
    .venv/bin/python tools/train_model.py      # Linux/macOS

Only the public training partition is used. Hyperparameters are selected by
leave-one-group-out validation; the practice partition is not used for tuning.
"""

import argparse
import gzip
import importlib.util
import json
import math
import sys
from pathlib import Path

import numpy as np
from sklearn.linear_model import LogisticRegression, Ridge


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from submission import features as submission_features


PACKET = ROOT / "Initial-Data"
TRAINING_PATH = PACKET / "training.json.gz"
GROUPS_PATH = PACKET / "dataset_info.json"
DEFAULT_OUTPUT = ROOT / "submission" / "starter_model.json"
LOG_CANDIDATES = (0.01, 0.1, 1.0, 10.0)
RIDGE_CANDIDATES = (0.01, 0.1, 1.0, 10.0, 100.0)
VALUE_CAP = 2000.0


def _load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _load_cases(path):
    return json.loads(gzip.decompress(path.read_bytes()))


def _load_baseline_features():
    path = PACKET / "features.py"
    spec = importlib.util.spec_from_file_location("supplied_baseline_features", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load supplied baseline features: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _check_group_metadata(cases, entries):
    groups_by_index = {}
    customers_by_index = {}
    for entry in entries:
        index = entry["example_index"]
        if index in groups_by_index:
            raise ValueError(f"Duplicate group entry for training case {index}")
        groups_by_index[index] = entry["group_id"]
        customers_by_index[index] = set(entry["customer_ids"])

    if set(groups_by_index) != set(range(len(cases))):
        raise ValueError("Group metadata must cover every training case exactly once")

    for index, case in enumerate(cases):
        roster = set(case["observation"]["customers"])
        if customers_by_index[index] != roster:
            raise ValueError(f"Group metadata roster mismatch for case {index}")
    return groups_by_index


def _transform(raw_features):
    """Apply the exact baseline log transforms, without fitting any statistics."""
    values = np.asarray(raw_features, dtype=np.float64).copy()
    if values.ndim != 2 or values.shape[1] != len(submission_features.FEATURE_NAMES):
        raise ValueError("Feature matrix has an unexpected shape")
    for column in (1, 2, 3, 4):
        values[:, column] = np.log1p(np.maximum(0.0, values[:, column]))
    values = np.clip(values, -1e6, 1e6)
    if not np.isfinite(values).all():
        raise ValueError("Transformed training features must be finite")
    return values


def _prepare_cases(cases):
    prepared = []
    for case in cases:
        observation = case["observation"]
        customer_ids = observation["customers"]
        raw_features = submission_features.matrix(observation)
        transformed = _transform(raw_features)
        targets = [case["targets"][customer_id] for customer_id in customer_ids]
        repeat_targets = np.asarray([target[0] for target in targets], dtype=np.float64)
        value_targets = np.asarray(
            [target[1] / VALUE_CAP for target in targets], dtype=np.float64
        )
        if len(transformed) != len(customer_ids):
            raise ValueError(f"Feature/customer count mismatch for {case['id']}")
        if not np.isfinite(repeat_targets).all() or not np.isfinite(value_targets).all():
            raise ValueError(f"Targets must be finite for {case['id']}")
        prepared.append(
            {
                "case": case,
                "customer_ids": customer_ids,
                "features": transformed,
                "repeat_targets": repeat_targets,
                "value_targets": value_targets,
            }
        )
    return prepared


def _stack_cases(cases):
    return (
        np.concatenate([case["features"] for case in cases], axis=0),
        np.concatenate([case["repeat_targets"] for case in cases]),
        np.concatenate([case["value_targets"] for case in cases]),
    )


def _fit_scaler(features):
    mean = features.mean(axis=0)
    scale = features.std(axis=0)
    scale[scale < 1e-8] = 1.0
    return mean, scale


def _scale(features, mean, scale):
    return (features - mean) / scale


def _fit_conditional_value_head(features, repeat_targets, value_targets, alpha):
    """Fit log capped amount among repeat buyers, emphasizing larger amounts."""
    positive = repeat_targets > 0.5
    if not np.any(positive):
        raise ValueError("Conditional value training requires at least one repeat buyer")
    positive_values = value_targets[positive]
    sample_weight = np.sqrt(np.maximum(positive_values, 1e-6))
    sample_weight /= sample_weight.mean()
    return Ridge(alpha=alpha).fit(
        features[positive],
        np.log1p(positive_values * VALUE_CAP),
        sample_weight=sample_weight,
    )


def _conditional_amount_from_log(log_amount):
    """Convert a fitted log1p amount to a bounded normalized capped amount."""
    return np.expm1(np.clip(log_amount, 0.0, math.log1p(VALUE_CAP))) / VALUE_CAP


def _earned_components(metrics):
    return {
        "probability": 40.0 * (1.0 - metrics["brier"]),
        "value": 30.0 * (1.0 - metrics["value_mse"] / VALUE_CAP**2),
        "selection": 30.0 * metrics["value_capture"],
    }


def _score_predictions(cases, probabilities, normalized_values):
    """Score normalized predictions using the supplied customer-weighted rules."""
    case_metrics = []
    offset = 0
    for case in cases:
        count = len(case["customer_ids"])
        stop = offset + count
        actual_repeat = case["repeat_targets"]
        actual_value = case["value_targets"]
        predicted_repeat = probabilities[offset:stop]
        predicted_value = normalized_values[offset:stop]

        brier = float(np.mean((predicted_repeat - actual_repeat) ** 2))
        normalized_mse = float(np.mean((predicted_value - actual_value) ** 2))
        budget = case["case"]["observation"]["budget"]
        oracle = float(np.sum(np.sort(actual_value)[::-1][:budget]))
        selected_indices = sorted(
            range(count),
            key=lambda index: (-float(predicted_value[index]), case["customer_ids"][index]),
        )[:budget]
        realized = float(sum(actual_value[index] for index in selected_indices))
        capture = realized / oracle if oracle else 1.0
        case_metrics.append(
            {
                "customers": count,
                "brier": brier,
                "value_mse": normalized_mse * VALUE_CAP**2,
                "value_capture": capture,
            }
        )
        offset = stop

    if offset != len(probabilities) or offset != len(normalized_values):
        raise ValueError("Prediction count does not match the validation rosters")

    total_customers = sum(item["customers"] for item in case_metrics)
    metrics = {
        key: sum(item[key] * item["customers"] for item in case_metrics)
        / total_customers
        for key in ("brier", "value_mse", "value_capture")
    }
    metrics["customers"] = total_customers
    metrics["score"] = sum(_earned_components(metrics).values())
    metrics["components"] = _earned_components(metrics)
    return metrics


def _fit_candidate_models(training_cases, validation_cases):
    x_train, y_repeat, y_value = _stack_cases(training_cases)
    x_validation, _, _ = _stack_cases(validation_cases)
    mean, scale = _fit_scaler(x_train)
    x_train_scaled = _scale(x_train, mean, scale)
    x_validation_scaled = _scale(x_validation, mean, scale)

    probabilities_by_c = {}
    for c_value in LOG_CANDIDATES:
        classifier = LogisticRegression(
            C=c_value,
            solver="lbfgs",
            max_iter=2000,
        )
        classifier.fit(x_train_scaled, y_repeat)
        positive_column = list(classifier.classes_).index(1)
        probabilities_by_c[c_value] = classifier.predict_proba(x_validation_scaled)[
            :, positive_column
        ]

    conditional_values_by_alpha = {}
    for alpha in RIDGE_CANDIDATES:
        regressor = _fit_conditional_value_head(
            x_train_scaled, y_repeat, y_value, alpha
        )
        conditional_values_by_alpha[alpha] = _conditional_amount_from_log(
            regressor.predict(x_validation_scaled)
        )
    return probabilities_by_c, conditional_values_by_alpha


def _fit_starter_fold(raw_training_cases, raw_validation_cases, baseline_features):
    model = baseline_features.fit(
        raw_training_cases, lambda _domain, observation: observation
    )
    probabilities = []
    values = []
    for case in raw_validation_cases:
        action = baseline_features.predict(case["observation"], model)
        for customer_id in case["observation"]["customers"]:
            prediction = action["predictions"][customer_id]
            probabilities.append(prediction["probability"])
            values.append(prediction["value"] / VALUE_CAP)
    return np.asarray(probabilities), np.asarray(values)


def _aggregate_fold_metrics(folds):
    total_customers = sum(fold["metrics"]["customers"] for fold in folds)
    metrics = {
        key: sum(
            fold["metrics"][key] * fold["metrics"]["customers"] for fold in folds
        )
        / total_customers
        for key in ("brier", "value_mse", "value_capture")
    }
    metrics["customers"] = total_customers
    metrics["score"] = sum(_earned_components(metrics).values())
    metrics["components"] = _earned_components(metrics)
    return metrics


def _cross_validate(raw_cases, prepared_cases, groups_by_index, baseline_features):
    group_ids = sorted(set(groups_by_index.values()))
    if len(group_ids) < 2:
        raise ValueError("Grouped validation requires at least two groups")

    grid_folds = {
        (c_value, alpha): []
        for c_value in LOG_CANDIDATES
        for alpha in RIDGE_CANDIDATES
    }
    starter_folds = []

    for group_id in group_ids:
        train_indices = [
            index for index in range(len(raw_cases)) if groups_by_index[index] != group_id
        ]
        validation_indices = [
            index for index in range(len(raw_cases)) if groups_by_index[index] == group_id
        ]
        raw_training = [raw_cases[index] for index in train_indices]
        raw_validation = [raw_cases[index] for index in validation_indices]
        prepared_training = [prepared_cases[index] for index in train_indices]
        prepared_validation = [prepared_cases[index] for index in validation_indices]

        probabilities_by_c, conditional_values_by_alpha = _fit_candidate_models(
            prepared_training, prepared_validation
        )
        validation_cases = [item for item in prepared_validation]
        starter_probabilities, starter_values = _fit_starter_fold(
            raw_training, raw_validation, baseline_features
        )
        starter_metrics = _score_predictions(
            validation_cases, starter_probabilities, starter_values
        )
        starter_folds.append(
            {
                "group_id": group_id,
                "validation_cases": len(validation_cases),
                "metrics": starter_metrics,
            }
        )

        for c_value in LOG_CANDIDATES:
            for alpha in RIDGE_CANDIDATES:
                metrics = _score_predictions(
                    validation_cases,
                    probabilities_by_c[c_value],
                    probabilities_by_c[c_value]
                    * conditional_values_by_alpha[alpha],
                )
                grid_folds[(c_value, alpha)].append(
                    {
                        "group_id": group_id,
                        "validation_cases": len(validation_cases),
                        "metrics": metrics,
                    }
                )

    grid_results = []
    for (c_value, alpha), folds in grid_folds.items():
        grid_results.append(
            {
                "repeat_C": c_value,
                "value_alpha": alpha,
                "metrics": _aggregate_fold_metrics(folds),
                "folds": folds,
            }
        )
    # Prefer stronger regularization if scores tie: lower logistic C, higher ridge alpha.
    best = max(
        grid_results,
        key=lambda result: (
            result["metrics"]["score"],
            -result["repeat_C"],
            result["value_alpha"],
        ),
    )
    return {
        "method": "leave-one-group-out",
        "group_count": len(group_ids),
        "starter": {
            "metrics": _aggregate_fold_metrics(starter_folds),
            "folds": starter_folds,
        },
        "grid": grid_results,
        "selected": {
            "repeat_C": best["repeat_C"],
            "value_alpha": best["value_alpha"],
            "metrics": best["metrics"],
            "folds": best["folds"],
        },
    }


def _fit_final_model(prepared_cases, repeat_c, value_alpha):
    x_train, y_repeat, y_value = _stack_cases(prepared_cases)
    mean, scale = _fit_scaler(x_train)
    x_scaled = _scale(x_train, mean, scale)

    classifier = LogisticRegression(
        C=repeat_c,
        solver="lbfgs",
        max_iter=2000,
    )
    classifier.fit(x_scaled, y_repeat)
    positive_column = list(classifier.classes_).index(1)

    regressor = _fit_conditional_value_head(
        x_scaled, y_repeat, y_value, value_alpha
    )

    model = {
        "feature_names": list(submission_features.FEATURE_NAMES),
        "mean": mean.tolist(),
        "scale": scale.tolist(),
        "repeat": {
            "intercept": float(classifier.intercept_[0]),
            "coefficients": classifier.coef_[0].astype(float).tolist(),
        },
        "value": {
            "intercept": float(regressor.intercept_),
            "coefficients": regressor.coef_.astype(float).tolist(),
        },
    }
    _validate_model(model)
    return model


def _validate_model(model):
    expected_keys = {"feature_names", "mean", "scale", "repeat", "value"}
    if set(model) != expected_keys:
        raise ValueError("Exported model does not match the agreed JSON schema")
    feature_count = len(submission_features.FEATURE_NAMES)
    if model["feature_names"] != list(submission_features.FEATURE_NAMES):
        raise ValueError("Exported feature order does not match the inference contract")
    if len(model["mean"]) != feature_count or len(model["scale"]) != feature_count:
        raise ValueError("Exported scaling vectors have an invalid length")
    for head_name in ("repeat", "value"):
        head = model[head_name]
        if set(head) != {"intercept", "coefficients"}:
            raise ValueError(f"Invalid {head_name} model head")
        if len(head["coefficients"]) != feature_count:
            raise ValueError(f"Invalid {head_name} coefficient count")
    numbers = model["mean"] + model["scale"]
    for head_name in ("repeat", "value"):
        numbers.extend(
            [model[head_name]["intercept"], *model[head_name]["coefficients"]]
        )
    if not all(math.isfinite(float(number)) for number in numbers):
        raise ValueError("Exported parameters must be finite numbers")
    if any(float(number) <= 0.0 for number in model["scale"]):
        raise ValueError("Exported scales must be positive")


def _check_exported_predictions(model, prepared_cases):
    """Check the exported JSON head math stays finite and within contract bounds."""
    checked_customers = 0
    mean = np.asarray(model["mean"])
    scale = np.asarray(model["scale"])
    for case in prepared_cases:
        x_scaled = _scale(case["features"], mean, scale)
        repeat = model["repeat"]
        value = model["value"]
        logits = float(repeat["intercept"]) + x_scaled @ np.asarray(
            repeat["coefficients"]
        )
        # Clipping logits is numerically stable and equivalent to sigmoid at
        # probabilities indistinguishable from zero or one in float64.
        probabilities = 1.0 / (1.0 + np.exp(-np.clip(logits, -700.0, 700.0)))
        conditional_log_values = float(value["intercept"]) + x_scaled @ np.asarray(
            value["coefficients"]
        )
        conditional_values = np.expm1(
            np.clip(conditional_log_values, 0.0, math.log1p(VALUE_CAP))
        )
        values = probabilities * conditional_values
        if (
            not np.isfinite(probabilities).all()
            or not np.isfinite(values).all()
            or np.any(probabilities < 0.0)
            or np.any(probabilities > 1.0)
            or np.any(values < 0.0)
            or np.any(values > VALUE_CAP)
        ):
            raise ValueError("Exported model produced an invalid prediction")
        checked_customers += len(probabilities)
    return checked_customers


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--training", type=Path, default=TRAINING_PATH)
    parser.add_argument("--groups", type=Path, default=GROUPS_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    raw_cases = _load_cases(args.training)
    metadata = _load_json(args.groups)
    entries = metadata["group_index"][args.training.name]
    groups_by_index = _check_group_metadata(raw_cases, entries)
    prepared_cases = _prepare_cases(raw_cases)
    baseline_features = _load_baseline_features()
    validation = _cross_validate(
        raw_cases, prepared_cases, groups_by_index, baseline_features
    )

    selected = validation["selected"]
    model = _fit_final_model(
        prepared_cases,
        repeat_c=selected["repeat_C"],
        value_alpha=selected["value_alpha"],
    )
    checked_customers = _check_exported_predictions(model, prepared_cases)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(model, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )

    starter_score = validation["starter"]["metrics"]["score"]
    candidate_score = selected["metrics"]["score"]
    report = {
        "training_cases": len(raw_cases),
        "final_fit_customers": sum(len(case["customer_ids"]) for case in prepared_cases),
        "validation": {
            "method": validation["method"],
            "groups": validation["group_count"],
            "selected_hyperparameters": {
                "repeat_C": selected["repeat_C"],
                "value_alpha": selected["value_alpha"],
            },
            "starter": validation["starter"],
            "selected_candidate": {
                "metrics": selected["metrics"],
                "folds": selected["folds"],
            },
            "candidate_grid": [
                {
                    "repeat_C": result["repeat_C"],
                    "value_alpha": result["value_alpha"],
                    "metrics": result["metrics"],
                }
                for result in validation["grid"]
            ],
            "score_delta_vs_starter": candidate_score - starter_score,
        },
        "model_output": str(args.output),
        "inference_schema_valid": True,
        "bounded_predictions_checked": checked_customers,
    }
    print(json.dumps(report, indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
