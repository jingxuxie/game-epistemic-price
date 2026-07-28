#!/usr/bin/env python3
"""Fail loudly when committed result tables no longer satisfy paper claims."""
from __future__ import annotations

import csv
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def close(a: float, b: float, tol: float = 1e-9) -> bool:
    return math.isclose(a, b, rel_tol=tol, abs_tol=tol)


def read_csv(name: str) -> list[dict[str, str]]:
    path = RESULTS / name
    require(path.is_file(), f"missing {path}")
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def main() -> None:
    summary_path = RESULTS / "summary.json"
    require(summary_path.is_file(), f"missing {summary_path}")
    summary = json.loads(summary_path.read_text(encoding="utf-8"))

    require(summary["projective_verified_q"] == [2, 3, 5, 7, 11, 13], "projective audit orders changed")
    require(summary["projective_all_match_theory"], "projective theorem mismatch")
    require(summary["largest_projective_message_gap"] == 13, "q=13 gap changed")
    require(summary["additive_cycle_all_match_theory"], "K=13 additive-cycle mismatch")
    require(summary["small_cycle_exhaustive_all_match"], "exhaustive small-cycle mismatch")
    require(summary["small_cycle_exhaustive_configurations"] == 169, "small-cycle audit count changed")
    require(summary["grid_general_milp_all_match_metric_reduction"], "grid MILP/metric mismatch")
    require(summary["map_frame_invariance_all_match"], "map frame-invariance mismatch")
    require(summary["grid_farthest_first_max_ratio"] <= 2.0 + 1e-12, "farthest-first exceeded factor two")
    require(close(summary["dictionary_full_message_best_nominal_transfer_regret"], 1.0), "nominal transfer result changed")
    require(close(summary["dictionary_full_message_robust_epoc"], 0.5), "robust dictionary floor changed")
    require(summary["random_set_pairwise_max_gap"] >= 3.0 - 1e-12, "random higher-order gap weakened")
    require(summary["random_set_greedy_max_ratio"] <= 1.5 + 1e-12, "random greedy audit changed")
    require(summary["largest_interval_instance"] == 10000, "interval scaling endpoint changed")

    expected = {
        "r0_s0": [1.0, 0.5, 1 / 3, 1 / 6, 0.0],
        "r1_s0": [1.0, 2 / 3, 0.5, 1 / 3, 1 / 6],
        "r0_s1": [1.0, 2 / 3, 0.5, 1 / 3, 1 / 6],
        "r1_s1": [1.0, 5 / 6, 2 / 3, 0.5, 1 / 3],
        "r2_s1": [1.0, 1.0, 5 / 6, 2 / 3, 0.5],
    }
    got = summary["lever_epoc_by_r_s_and_bits"]
    for key, values in expected.items():
        require(key in got, f"missing cycle setting {key}")
        for bits, value in enumerate(values):
            require(close(float(got[key][str(bits)]), value), f"cycle frontier mismatch: {key}, bits={bits}")

    expected_files = [
        "projective_planes.csv",
        "private_levers.csv",
        "small_cycle_exhaustive.csv",
        "dictionary_ambiguity.csv",
        "grid_map_alignment.csv",
        "map_frame_invariance.csv",
        "grid_farthest_first_audit.csv",
        "random_set_systems.csv",
        "interval_scaling.csv",
    ]
    rows = {name: read_csv(name) for name in expected_files}
    require(len(rows["small_cycle_exhaustive.csv"]) == 169, "small-cycle CSV length changed")
    require(len(rows["private_levers.csv"]) == 25, "K=13 cycle CSV length changed")
    require(len(rows["map_frame_invariance.csv"]) == 4, "frame audit length changed")

    print("result invariants: OK")


if __name__ == "__main__":
    main()
