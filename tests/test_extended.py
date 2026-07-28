from __future__ import annotations

from types import SimpleNamespace

import pytest

import epcoord.milp as milp_module
from epcoord.families import (
    apply_grid_isometry,
    grid_isometry_names,
    grid_map_alignment_game,
    private_lever_game,
    square_grid_points,
)
from epcoord.metric import (
    exact_metric_center,
    farthest_first_metric_center,
    manhattan_distance,
)
from epcoord.milp import epoc_for_messages, feasible_protocol
from epcoord.theory import (
    private_lever_epoc_formula,
    private_lever_min_messages_for_epsilon,
)


@pytest.mark.parametrize(
    "num_levers,noise_radius,bias_radius,messages",
    [
        (5, 0, 1, 2),
        (5, 1, 1, 3),
        (7, 1, 0, 2),
        (7, 1, 1, 4),
    ],
)
def test_additive_cycle_formula_matches_milp(
    num_levers: int,
    noise_radius: int,
    bias_radius: int,
    messages: int,
) -> None:
    game = private_lever_game(
        num_levers=num_levers,
        noise_radius=noise_radius,
        receiver_bias_radius=bias_radius,
        num_receiver_frames=2,
    )
    exact, _ = epoc_for_messages(game, messages)
    predicted = private_lever_epoc_formula(
        num_levers=num_levers,
        noise_radius=noise_radius,
        receiver_bias_radius=bias_radius,
        num_messages=messages,
    )
    assert exact == pytest.approx(predicted)


@pytest.mark.parametrize("epsilon", [0.25, 0.5, 1.0])
def test_inverse_cycle_threshold_matches_forward_formula(epsilon: float) -> None:
    num_levers = 9
    noise_radius = 1
    bias_radius = 0
    messages = private_lever_min_messages_for_epsilon(
        num_levers=num_levers,
        noise_radius=noise_radius,
        receiver_bias_radius=bias_radius,
        epsilon=epsilon,
    )
    if messages is None:
        assert epsilon < (noise_radius + bias_radius) / (num_levers // 2)
        return
    achieved = private_lever_epoc_formula(
        num_levers=num_levers,
        noise_radius=noise_radius,
        receiver_bias_radius=bias_radius,
        num_messages=messages,
    )
    assert achieved <= epsilon + 1e-12
    if messages > 1:
        previous = private_lever_epoc_formula(
            num_levers=num_levers,
            noise_radius=noise_radius,
            receiver_bias_radius=bias_radius,
            num_messages=messages - 1,
        )
        assert previous > epsilon - 1e-12


def test_grid_isometries_are_distinct_bijections() -> None:
    side = 4
    points = square_grid_points(side)
    images = []
    for frame in grid_isometry_names():
        transformed = tuple(apply_grid_isometry(point, side, frame) for point in points)
        assert set(transformed) == set(points)
        images.append(transformed)
    assert len(set(images)) == 8


def test_grid_protocol_milp_matches_metric_center() -> None:
    side = 3
    points = square_grid_points(side)
    game = grid_map_alignment_game(side_length=side)
    diameter = 2 * (side - 1)
    for messages in (1, 2, 4):
        metric = exact_metric_center(
            points, messages, distance=manhattan_distance
        )
        epoc, _ = epoc_for_messages(game, messages)
        assert epoc == pytest.approx(metric.radius / diameter)


def test_farthest_first_respects_two_approximation_on_grids() -> None:
    for side in (3, 4, 5):
        points = square_grid_points(side)
        candidates = sorted(
            {1, 2, 3, 4, min(8, len(points)), max(1, len(points) - 1)}
        )
        for messages in candidates:
            exact = exact_metric_center(
                points, messages, distance=manhattan_distance
            )
            heuristic = farthest_first_metric_center(
                points, messages, distance=manhattan_distance
            )
            if exact.radius == 0:
                assert heuristic.radius == 0
            else:
                assert heuristic.radius <= 2 * exact.radius + 1e-12


def test_solver_timeout_is_not_reported_as_infeasible(monkeypatch: pytest.MonkeyPatch) -> None:
    game = private_lever_game(
        num_levers=3,
        noise_radius=0,
        num_receiver_frames=1,
    )

    def fake_solve(self, *, time_limit=None):  # noqa: ANN001, ARG001
        return SimpleNamespace(
            success=False,
            status=1,
            x=None,
            message="time limit reached",
        )

    monkeypatch.setattr(milp_module._MILPBuilder, "solve", fake_solve)
    with pytest.raises(TimeoutError):
        feasible_protocol(game, 1, 0.0)


def test_solver_failure_is_not_reported_as_infeasible(monkeypatch: pytest.MonkeyPatch) -> None:
    game = private_lever_game(
        num_levers=3,
        noise_radius=0,
        num_receiver_frames=1,
    )

    def fake_solve(self, *, time_limit=None):  # noqa: ANN001, ARG001
        return SimpleNamespace(
            success=False,
            status=4,
            x=None,
            message="numerical failure",
        )

    monkeypatch.setattr(milp_module._MILPBuilder, "solve", fake_solve)
    with pytest.raises(RuntimeError):
        feasible_protocol(game, 1, 0.0)
