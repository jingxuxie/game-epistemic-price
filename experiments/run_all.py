from __future__ import annotations

import json
import math
import sys
import time
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from epcoord.families import (  # noqa: E402
    dictionary_ambiguity_game,
    grid_isometry_names,
    grid_map_alignment_game,
    private_lever_game,
    projective_plane_incidence,
    random_intervals,
    random_set_system,
    square_grid_points,
)
from epcoord.metric import (  # noqa: E402
    exact_metric_center,
    farthest_first_metric_center,
    manhattan_distance,
)
from epcoord.milp import epoc_for_messages, feasible_protocol  # noqa: E402
from epcoord.setcover import (  # noqa: E402
    exact_graph_coloring,
    exact_hitting_set,
    greedy_hitting_set,
    greedy_interval_stabbing,
    pairwise_conflict_graph,
)
from epcoord.theory import private_lever_epoc_formula  # noqa: E402


def run_projective_planes() -> pd.DataFrame:
    rows = []
    for q in (2, 3, 5, 7, 11, 13):
        points, incidence = projective_plane_incidence(q)
        start = time.perf_counter()
        exact = exact_hitting_set(
            incidence, universe=range(len(points)), time_limit=120.0
        )
        elapsed = time.perf_counter() - start
        if exact.size != q + 1:
            raise AssertionError("projective-plane hitting number disagrees with q+1")
        rows.append(
            {
                "q": q,
                "sender_types": len(incidence),
                "receiver_actions": len(points),
                "pairwise_graph_messages": 1,
                "exact_messages": exact.size,
                "theory_messages": q + 1,
                "exact_bits": (exact.size - 1).bit_length(),
                "seconds": elapsed,
            }
        )
    return pd.DataFrame(rows)


def run_private_levers() -> pd.DataFrame:
    rows = []
    num_levers = 13
    scenarios = ((0, 0), (1, 0), (0, 1), (1, 1), (2, 1))
    for noise_radius, bias_radius in scenarios:
        game = private_lever_game(
            num_levers=num_levers,
            noise_radius=noise_radius,
            receiver_bias_radius=bias_radius,
            num_receiver_frames=2,
        )
        for bits in range(5):
            messages = min(2**bits, num_levers)
            start = time.perf_counter()
            epoc, _ = epoc_for_messages(game, messages, time_limit=120.0)
            elapsed = time.perf_counter() - start
            theory_epoc = private_lever_epoc_formula(
                num_levers=num_levers,
                noise_radius=noise_radius,
                receiver_bias_radius=bias_radius,
                num_messages=messages,
            )
            if abs(epoc - theory_epoc) > 1e-8:
                raise AssertionError("private-lever MILP disagrees with closed form")
            rows.append(
                {
                    "num_levers": num_levers,
                    "noise_radius": noise_radius,
                    "receiver_bias_radius": bias_radius,
                    "bits": bits,
                    "messages": messages,
                    "epoc": epoc,
                    "theory_epoc": theory_epoc,
                    "seconds": elapsed,
                    "worlds": len(game.worlds),
                }
            )
    return pd.DataFrame(rows)


def run_small_cycle_exhaustive() -> pd.DataFrame:
    """Exhaust every admissible radius pair and message count for K=3,5,7."""

    rows = []
    for num_levers in (3, 5, 7):
        half = num_levers // 2
        for noise_radius in range(half + 1):
            for bias_radius in range(half + 1):
                game = private_lever_game(
                    num_levers=num_levers,
                    noise_radius=noise_radius,
                    receiver_bias_radius=bias_radius,
                    num_receiver_frames=2,
                )
                for messages in range(1, num_levers + 1):
                    exact, _ = epoc_for_messages(
                        game, messages, time_limit=120.0
                    )
                    predicted = private_lever_epoc_formula(
                        num_levers=num_levers,
                        noise_radius=noise_radius,
                        receiver_bias_radius=bias_radius,
                        num_messages=messages,
                    )
                    match = abs(exact - predicted) <= 1e-8
                    if not match:
                        raise AssertionError(
                            "exhaustive small-cycle MILP disagrees with theorem"
                        )
                    rows.append(
                        {
                            "num_levers": num_levers,
                            "noise_radius": noise_radius,
                            "receiver_bias_radius": bias_radius,
                            "messages": messages,
                            "exact_epoc": exact,
                            "theory_epoc": predicted,
                            "match": match,
                        }
                    )
    table = pd.DataFrame(rows)
    if len(table) != 169:
        raise AssertionError(f"expected 169 exhaustive configurations, got {len(table)}")
    return table


def run_dictionary_ambiguity() -> pd.DataFrame:
    rows = []
    num_actions = 13
    nominal = dictionary_ambiguity_game(
        num_actions=num_actions,
        frame_bias_options=((0,), (0,), (0,), (0,)),
        name="nominal-dictionary",
    )
    robust = dictionary_ambiguity_game(
        num_actions=num_actions,
        frame_bias_options=((0,), (0, 2), (0, 4), (0, 6)),
        name="ambiguous-dictionary",
    )
    for bits in range(5):
        messages = min(2**bits, num_actions)
        start = time.perf_counter()
        nominal_epoc, _ = epoc_for_messages(nominal, messages, time_limit=120.0)
        nominal_seconds = time.perf_counter() - start

        # Among all nominal-optimal protocols, choose the one with the best
        # worst-case transfer to the ambiguity set.  This avoids attributing a
        # solver tie break to nominal design.
        transfer_start = time.perf_counter()
        transfer_epoc = None
        for candidate in robust.regret_levels():
            limits = {
                world.name: (
                    min(candidate, nominal_epoc)
                    if world.name.endswith("bias-0")
                    else candidate
                )
                for world in robust.worlds
            }
            feasible = feasible_protocol(
                robust,
                messages,
                candidate,
                world_epsilon=limits,
                time_limit=120.0,
            )
            if feasible.feasible:
                transfer_epoc = candidate
                break
        if transfer_epoc is None:
            raise RuntimeError("failed to find a nominal-optimal transfer protocol")
        transfer_seconds = time.perf_counter() - transfer_start

        start = time.perf_counter()
        robust_epoc, _ = epoc_for_messages(robust, messages, time_limit=120.0)
        robust_seconds = time.perf_counter() - start
        rows.append(
            {
                "num_actions": num_actions,
                "bits": bits,
                "messages": messages,
                "nominal_epoc": nominal_epoc,
                "best_nominal_optimum_on_ambiguity": transfer_epoc,
                "robust_epoc": robust_epoc,
                "nominal_seconds": nominal_seconds,
                "transfer_seconds": transfer_seconds,
                "robust_seconds": robust_seconds,
            }
        )
    return pd.DataFrame(rows)


def run_grid_map_alignment() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    side = 5
    points = square_grid_points(side)
    diameter = 2 * (side - 1)
    all_frames = grid_isometry_names()
    # Metric reduction is frame-invariant.  The direct MILP cross-check uses
    # two nontrivial private frames to keep the all-experiments run lightweight;
    # a separate audit below varies the frame set through all eight D4 frames.
    milp_frames = all_frames[:2]
    game = grid_map_alignment_game(side_length=side, frame_names=milp_frames)
    rows = []
    for messages in (1, 2, 4, 8, 16, 25):
        start = time.perf_counter()
        exact = exact_metric_center(
            points,
            messages,
            distance=manhattan_distance,
            time_limit=120.0,
        )
        metric_seconds = time.perf_counter() - start
        heuristic = farthest_first_metric_center(
            points, messages, distance=manhattan_distance
        )
        if exact.radius == 0:
            approximation_ratio = 1.0 if heuristic.radius == 0 else math.inf
        else:
            approximation_ratio = heuristic.radius / exact.radius
        if approximation_ratio > 2 + 1e-10:
            raise AssertionError("farthest-first violated the metric 2-approximation")

        milp_value = math.nan
        milp_seconds = math.nan
        if messages <= 8:
            start = time.perf_counter()
            milp_value, _ = epoc_for_messages(game, messages, time_limit=120.0)
            milp_seconds = time.perf_counter() - start
            if abs(milp_value - exact.radius / diameter) > 1e-8:
                raise AssertionError("map protocol MILP disagrees with metric center")
        rows.append(
            {
                "side_length": side,
                "frames": len(all_frames),
                "milp_frames": len(milp_frames),
                "messages": messages,
                "bits": 0 if messages == 1 else math.ceil(math.log2(messages)),
                "exact_radius": exact.radius,
                "exact_epoc": exact.radius / diameter,
                "farthest_first_radius": heuristic.radius,
                "farthest_first_epoc": heuristic.radius / diameter,
                "approximation_ratio": approximation_ratio,
                "general_milp_epoc": milp_value,
                "metric_seconds": metric_seconds,
                "milp_seconds": milp_seconds,
            }
        )

    invariance_rows = []
    messages = 4
    predicted = exact_metric_center(
        points, messages, distance=manhattan_distance
    ).radius / diameter
    for frame_count in (1, 2, 4, 8):
        frame_game = grid_map_alignment_game(
            side_length=side, frame_names=all_frames[:frame_count]
        )
        exact_value, _ = epoc_for_messages(
            frame_game, messages, time_limit=120.0
        )
        if abs(exact_value - predicted) > 1e-8:
            raise AssertionError("map-frame invariance failed")
        invariance_rows.append(
            {
                "side_length": side,
                "frames": frame_count,
                "messages": messages,
                "epoc": exact_value,
                "metric_prediction": predicted,
            }
        )

    audit_rows = []
    for audit_side in (3, 4, 5):
        audit_points = square_grid_points(audit_side)
        for messages in range(1, len(audit_points) + 1):
            exact = exact_metric_center(
                audit_points, messages, distance=manhattan_distance
            )
            heuristic = farthest_first_metric_center(
                audit_points, messages, distance=manhattan_distance
            )
            ratio = (
                1.0
                if exact.radius == 0 and heuristic.radius == 0
                else heuristic.radius / exact.radius
            )
            if ratio > 2 + 1e-10:
                raise AssertionError("grid farthest-first audit exceeded factor two")
            audit_rows.append(
                {
                    "side_length": audit_side,
                    "messages": messages,
                    "exact_radius": exact.radius,
                    "farthest_first_radius": heuristic.radius,
                    "approximation_ratio": ratio,
                }
            )
    return (
        pd.DataFrame(rows),
        pd.DataFrame(invariance_rows),
        pd.DataFrame(audit_rows),
    )


def run_random_set_systems() -> pd.DataFrame:
    rows = []
    num_types = 30
    num_actions = 20
    for set_size in (2, 3, 4, 5, 6, 8, 10):
        for seed in range(20):
            sets = random_set_system(
                num_types=num_types,
                num_actions=num_actions,
                set_size=set_size,
                seed=10_000 * set_size + seed,
            )
            start = time.perf_counter()
            exact = exact_hitting_set(sets, universe=range(num_actions), time_limit=60)
            exact_seconds = time.perf_counter() - start
            start = time.perf_counter()
            greedy = greedy_hitting_set(sets, universe=range(num_actions))
            greedy_seconds = time.perf_counter() - start
            conflict_graph = pairwise_conflict_graph(sets)
            pairwise_conflicts = int(conflict_graph.sum() // 2)
            start = time.perf_counter()
            pairwise_coloring = exact_graph_coloring(
                conflict_graph, time_limit=60
            )
            coloring_seconds = time.perf_counter() - start
            rows.append(
                {
                    "num_types": num_types,
                    "num_actions": num_actions,
                    "set_size": set_size,
                    "seed": seed,
                    "pairwise_graph_messages": pairwise_coloring.size,
                    "exact_messages": exact.size,
                    "greedy_messages": greedy.size,
                    "higher_order_gap": exact.size / pairwise_coloring.size,
                    "approximation_ratio": greedy.size / exact.size,
                    "pairwise_conflicts": pairwise_conflicts,
                    "coloring_seconds": coloring_seconds,
                    "exact_seconds": exact_seconds,
                    "greedy_seconds": greedy_seconds,
                }
            )
    return pd.DataFrame(rows)


def run_intervals() -> pd.DataFrame:
    rows = []
    num_actions = 20_000
    for num_types in (50, 100, 250, 500, 1_000, 2_500, 5_000, 10_000):
        timings = []
        sizes = []
        for seed in range(10):
            intervals = random_intervals(
                num_types=num_types,
                num_actions=num_actions,
                max_width=1_000,
                seed=77_000 + num_types + seed,
            )
            start = time.perf_counter()
            greedy = greedy_interval_stabbing(intervals)
            timings.append(time.perf_counter() - start)
            sizes.append(greedy.size)
        rows.append(
            {
                "num_types": num_types,
                "num_actions": num_actions,
                "mean_messages": sum(sizes) / len(sizes),
                "mean_seconds": sum(timings) / len(timings),
                "max_seconds": max(timings),
            }
        )

    # Validate exactness against MILP on 20 deterministic audit instances.
    for num_types in (20, 40, 80, 120):
        for seed in range(5):
            intervals = random_intervals(
                num_types=num_types,
                num_actions=300,
                max_width=50,
                seed=91_000 + num_types + seed,
            )
            greedy = greedy_interval_stabbing(intervals)
            sets = [set(range(left, right + 1)) for left, right in intervals]
            exact = exact_hitting_set(sets, universe=range(300), time_limit=60)
            if greedy.size != exact.size:
                raise AssertionError("interval greedy disagrees with exact MILP")
    return pd.DataFrame(rows)


def main() -> None:
    results = ROOT / "results"
    results.mkdir(exist_ok=True)

    grid, frame_invariance, grid_audit = run_grid_map_alignment()
    tables = {
        "projective_planes": run_projective_planes(),
        "private_levers": run_private_levers(),
        "small_cycle_exhaustive": run_small_cycle_exhaustive(),
        "dictionary_ambiguity": run_dictionary_ambiguity(),
        "grid_map_alignment": grid,
        "map_frame_invariance": frame_invariance,
        "grid_farthest_first_audit": grid_audit,
        "random_set_systems": run_random_set_systems(),
        "interval_scaling": run_intervals(),
    }
    for name, table in tables.items():
        table.to_csv(results / f"{name}.csv", index=False)
        print(f"[{name}]\n{table.head()}\n")

    projective = tables["projective_planes"]
    levers = tables["private_levers"]
    exhaustive = tables["small_cycle_exhaustive"]
    ambiguity = tables["dictionary_ambiguity"]
    grid = tables["grid_map_alignment"]
    frame_invariance = tables["map_frame_invariance"]
    grid_audit = tables["grid_farthest_first_audit"]
    random_sets = tables["random_set_systems"]
    intervals = tables["interval_scaling"]

    lever_frontiers = {}
    for (radius, bias), group in levers.groupby(
        ["noise_radius", "receiver_bias_radius"]
    ):
        lever_frontiers[f"r{int(radius)}_s{int(bias)}"] = {
            str(int(row.bits)): float(row.epoc) for row in group.itertuples()
        }

    compared_grid = grid.dropna(subset=["general_milp_epoc"])
    summary = {
        "projective_verified_q": projective["q"].tolist(),
        "largest_projective_message_gap": int(
            projective["exact_messages"].max()
            - projective["pairwise_graph_messages"].min()
        ),
        "projective_all_match_theory": bool(
            (projective["exact_messages"] == projective["theory_messages"]).all()
        ),
        "additive_cycle_all_match_theory": bool(
            (abs(levers["epoc"] - levers["theory_epoc"]) <= 1e-8).all()
        ),
        "small_cycle_exhaustive_all_match": bool(exhaustive["match"].all()),
        "small_cycle_exhaustive_configurations": int(len(exhaustive)),
        "lever_epoc_by_r_s_and_bits": lever_frontiers,
        "dictionary_full_message_best_nominal_transfer_regret": float(
            ambiguity.iloc[-1]["best_nominal_optimum_on_ambiguity"]
        ),
        "dictionary_full_message_robust_epoc": float(
            ambiguity.iloc[-1]["robust_epoc"]
        ),
        "grid_general_milp_all_match_metric_reduction": bool(
            (
                abs(
                    compared_grid["general_milp_epoc"]
                    - compared_grid["exact_epoc"]
                )
                <= 1e-8
            ).all()
        ),
        "grid_farthest_first_max_ratio": float(
            grid_audit["approximation_ratio"].max()
        ),
        "map_frame_invariance_all_match": bool(
            (
                abs(
                    frame_invariance["epoc"]
                    - frame_invariance["metric_prediction"]
                )
                <= 1e-8
            ).all()
        ),
        "random_set_pairwise_mean_gap": float(
            random_sets["higher_order_gap"].mean()
        ),
        "random_set_pairwise_max_gap": float(
            random_sets["higher_order_gap"].max()
        ),
        "random_set_greedy_mean_ratio": float(
            random_sets["approximation_ratio"].mean()
        ),
        "random_set_greedy_max_ratio": float(
            random_sets["approximation_ratio"].max()
        ),
        "largest_interval_instance": int(intervals["num_types"].max()),
        "largest_interval_mean_seconds": float(
            intervals.loc[intervals["num_types"].idxmax(), "mean_seconds"]
        ),
    }
    (results / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
