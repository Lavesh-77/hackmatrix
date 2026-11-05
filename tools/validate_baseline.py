"""Reproduce the supplied starter scores and run grouped training validation.

Run from the repository root with ``py tools/validate_baseline.py`` on Windows
or ``python tools/validate_baseline.py`` on Linux/macOS. The script only reads
the supplied packet and prints its results as JSON.
"""

import gzip
import importlib.util
import json
import math
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / "Initial-Data"
DATA_FILES = ("smoke.json.gz", "training.json.gz", "practice.json.gz")


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_cases(path):
    return json.loads(gzip.decompress(path.read_bytes()))


def load_feature_helper():
    path = PACKET / "features.py"
    spec = importlib.util.spec_from_file_location("supplied_features", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load supplied feature helper: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def earned_components(metrics):
    return {
        "probability": 40.0 * (1.0 - metrics["brier"]),
        "value": 30.0 * (1.0 - metrics["value_mse"] / (2000.0**2)),
        "selection": 30.0 * metrics["capture"],
    }


def score_cases(cases, model, features):
    """Score predictions with the same customer-weighted formula as local_check."""
    totals = {"brier": 0.0, "value_mse": 0.0, "capture": 0.0}
    customer_count = 0

    for case in cases:
        observation = case["observation"]
        action = features.predict(observation, model)
        predictions = action["predictions"]
        targets = case["targets"]
        customers = observation["customers"]
        count = len(customers)

        brier = sum(
            (predictions[cid]["probability"] - targets[cid][0]) ** 2
            for cid in customers
        ) / count
        value_mse = sum(
            (predictions[cid]["value"] - targets[cid][1]) ** 2
            for cid in customers
        ) / count
        oracle_value = sum(
            sorted((target[1] for target in targets.values()), reverse=True)[
                : observation["budget"]
            ]
        )
        selected_value = sum(targets[cid][1] for cid in action["selected"])
        capture = selected_value / oracle_value if oracle_value else 1.0

        totals["brier"] += brier * count
        totals["value_mse"] += value_mse * count
        totals["capture"] += capture * count
        customer_count += count

    metrics = {
        key: value / customer_count for key, value in totals.items()
    }
    metrics["customers"] = customer_count
    metrics["score"] = sum(earned_components(metrics).values())
    metrics["components"] = earned_components(metrics)
    return metrics


def validate_group_metadata(cases, entries):
    """Return the declared group for each case, rejecting incomplete metadata."""
    groups_by_index = {}
    entries_by_index = {}
    for entry in entries:
        index = entry["example_index"]
        if index in groups_by_index:
            raise ValueError(f"Duplicate group metadata for example {index}")
        groups_by_index[index] = entry["group_id"]
        entries_by_index[index] = entry

    expected_indices = set(range(len(cases)))
    if set(groups_by_index) != expected_indices:
        raise ValueError("Group metadata does not cover the training cases exactly")

    for index, case in enumerate(cases):
        metadata_customers = set(entries_by_index[index]["customer_ids"])
        observation_customers = set(case["observation"]["customers"])
        if metadata_customers != observation_customers:
            raise ValueError(f"Customer roster mismatch for training example {index}")

    return groups_by_index


def grouped_validation(training_cases, groups_by_index, features):
    """Leave one declared source/world group out per repeatable fold."""
    group_ids = sorted(set(groups_by_index.values()))
    if len(group_ids) < 2:
        raise ValueError("Grouped validation requires at least two training groups")

    folds = []
    weighted_totals = {
        "brier": 0.0,
        "value_mse": 0.0,
        "capture": 0.0,
        "score": 0.0,
    }
    customer_count = 0

    for held_out_group in group_ids:
        training = [
            case
            for index, case in enumerate(training_cases)
            if groups_by_index[index] != held_out_group
        ]
        validation = [
            case
            for index, case in enumerate(training_cases)
            if groups_by_index[index] == held_out_group
        ]
        model = features.fit(training, lambda _domain, observation: observation)
        metrics = score_cases(validation, model, features)

        folds.append(
            {
                "held_out_group": held_out_group,
                "training_cases": len(training),
                "validation_cases": len(validation),
                "validation_customers": metrics["customers"],
                "score": metrics["score"],
                "brier": metrics["brier"],
                "value_mse": metrics["value_mse"],
                "value_capture": metrics["capture"],
                "components": metrics["components"],
            }
        )
        for key in weighted_totals:
            weighted_totals[key] += metrics[key] * metrics["customers"]
        customer_count += metrics["customers"]

    summary = {
        key: value / customer_count for key, value in weighted_totals.items()
    }
    return {
        "method": "leave-one-group-out",
        "group_count": len(group_ids),
        "customer_count": customer_count,
        "folds": folds,
        "customer_weighted_summary": {
            **summary,
            "components": earned_components(summary),
        },
    }


def run_local_check(data_file):
    command = [
        sys.executable,
        str(PACKET / "local_check.py"),
        "--solution",
        str(PACKET / "starter.py"),
        "--data",
        str(PACKET / data_file),
        "--scoring",
        str(PACKET / "scoring.json"),
    ]
    result = subprocess.run(
        command,
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


def compare_with_published(actual, published):
    if published is None:
        return None

    expected = published["summary"]
    expected_metrics = {
        "score": published["mean_score"],
        "brier": expected["diagnostics"]["brier"],
        "value_mse": expected["diagnostics"]["value_mse"],
        "capture": expected["diagnostics"]["value_capture"],
    }
    actual_metrics = {
        "score": actual["score"],
        "brier": actual["brier"],
        "value_mse": actual["value_mse"],
        "capture": actual["capture"],
    }
    expected_metrics["components"] = {
        name: component["earned"]
        for name, component in expected["components"].items()
    }
    actual_metrics["components"] = earned_components(actual_metrics)

    differences = {}
    for metric in ("score", "brier", "value_mse", "capture"):
        differences[metric] = actual_metrics[metric] - expected_metrics[metric]
    differences["components"] = {
        name: actual_metrics["components"][name] - expected_metrics["components"][name]
        for name in ("probability", "value", "selection")
    }
    matches = all(
        math.isclose(value, 0.0, rel_tol=0.0, abs_tol=1e-8)
        for value in differences.values()
        if isinstance(value, float)
    ) and all(
        math.isclose(value, 0.0, rel_tol=0.0, abs_tol=1e-8)
        for value in differences["components"].values()
    )
    return {
        "published": expected_metrics,
        "actual": actual_metrics,
        "delta_actual_minus_published": differences,
        "matches_within_1e-8": matches,
    }


def main():
    features = load_feature_helper()
    cases_by_file = {
        filename: load_cases(PACKET / filename) for filename in DATA_FILES
    }
    published = load_json(PACKET / "baseline_results.json")["results"]

    checker_results = {}
    for filename in DATA_FILES:
        result = run_local_check(filename)
        reference = published.get(filename.removesuffix(".json.gz"))
        checker_results[filename] = {
            **result,
            "components": earned_components(result),
            "published_comparison": compare_with_published(result, reference),
        }

    metadata = load_json(PACKET / "dataset_info.json")
    training_cases = cases_by_file["training.json.gz"]
    groups_by_index = validate_group_metadata(
        training_cases, metadata["group_index"]["training.json.gz"]
    )

    print(
        json.dumps(
            {
                "checker": "Initial-Data/local_check.py with supplied starter",
                "baseline_checker_results": checker_results,
                "grouped_training_validation": grouped_validation(
                    training_cases, groups_by_index, features
                ),
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
