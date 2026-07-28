from __future__ import annotations

from itertools import product

import numpy as np
import pytest

from epcoord.families import (
    higher_order_triangle_game,
    interval_game,
    private_lever_game,
    projective_plane_game,
    projective_plane_incidence,
    random_intervals,
)
from epcoord.milp import epoc_for_messages, feasible_protocol, minimum_messages
from epcoord.model import EpistemicGame, World
from epcoord.setcover import exact_hitting_set, greedy_interval_stabbing
from epcoord.twosat import solve_binary_coordination


def brute_force_zero_communication(game: EpistemicGame, epsilon: float) -> bool:
    for sender_actions in product(
        range(game.num_sender_actions), repeat=len(game.sender_types)
    ):
        for receiver_actions in product(
            range(game.num_receiver_actions), repeat=len(game.receiver_types)
        ):
            feasible = True
            for world in game.worlds:
                a = sender_actions[game.sender_type_index[world.sender_type]]
                b = receiver_actions[game.receiver_type_index[world.receiver_type]]
                if world.regret(a, b) > epsilon + 1e-10:
                    feasible = False
                    break
            if feasible:
                return True
    return False


def test_higher_order_pairwise_but_not_joint() -> None:
    game = higher_order_triangle_game()
    one = feasible_protocol(game, num_messages=1, epsilon=0.0)
    two = feasible_protocol(game, num_messages=2, epsilon=0.0)
    assert not one.feasible
    assert two.feasible


def test_projective_plane_cardinality_and_message_number() -> None:
    for q in (2, 3):
        points, incidence = projective_plane_incidence(q)
        assert len(points) == q * q + q + 1
        assert all(len(line) == q + 1 for line in incidence)
        exact = exact_hitting_set(incidence, universe=range(len(points)))
        assert exact.size == q + 1
        game = projective_plane_game(q)
        messages, _ = minimum_messages(game, epsilon=0.0)
        assert messages == q + 1


def test_interval_greedy_matches_exact() -> None:
    for seed in range(8):
        intervals = random_intervals(
            num_types=18, num_actions=25, max_width=9, seed=seed
        )
        greedy = greedy_interval_stabbing(intervals)
        sets = [set(range(left, right + 1)) for left, right in intervals]
        exact = exact_hitting_set(sets, universe=range(25))
        assert greedy.size == exact.size
        game = interval_game(intervals, num_actions=25)
        messages, _ = minimum_messages(game, epsilon=0.0)
        assert messages == exact.size


def test_twosat_matches_bruteforce_and_milp() -> None:
    rng = np.random.default_rng(7)
    for _ in range(30):
        n_x, n_y = 3, 3
        worlds: list[World] = []
        forbidden: list[tuple[int, int, int, int]] = []
        for x in range(n_x):
            for y in range(n_y):
                payoff = np.ones((2, 2), dtype=float)
                for a in range(2):
                    for b in range(2):
                        if rng.random() < 0.28:
                            payoff[a, b] = 0.0
                if np.max(payoff) > 0.0:
                    for a in range(2):
                        for b in range(2):
                            if payoff[a, b] == 0.0:
                                forbidden.append((x, y, a, b))
                worlds.append(World(f"{x}-{y}", x, y, payoff))
        game = EpistemicGame(worlds, (0, 1), (0, 1))
        expected = brute_force_zero_communication(game, 0.0)
        two_sat = solve_binary_coordination(n_x, n_y, forbidden)
        milp = feasible_protocol(game, 1, 0.0)
        assert (two_sat is not None) == expected
        assert milp.feasible == expected


def test_epoc_frontier_is_monotone_and_has_noise_floor() -> None:
    game = private_lever_game(
        num_levers=7, noise_radius=1, num_receiver_frames=3
    )
    values = [epoc_for_messages(game, messages)[0] for messages in range(1, 8)]
    assert all(first >= second - 1e-10 for first, second in zip(values, values[1:]))
    # Even full revelation of the sender estimate cannot identify the true target
    # inside a radius-one ambiguity set.
    assert values[-1] == pytest.approx(1.0 / 3.0)


def test_milp_matches_bruteforce_for_zero_communication() -> None:
    rng = np.random.default_rng(11)
    for _ in range(12):
        worlds = []
        for x in range(2):
            for y in range(2):
                payoff = rng.integers(0, 4, size=(2, 3)).astype(float) / 3.0
                worlds.append(World(f"{x}-{y}", x, y, payoff))
        game = EpistemicGame(worlds, (0, 1), (0, 1, 2))
        for epsilon in game.regret_levels():
            milp = feasible_protocol(game, 1, epsilon)
            assert milp.feasible == brute_force_zero_communication(game, epsilon)


def test_dictionary_ambiguity_robust_design_dominates_nominal_deployment() -> None:
    from epcoord.families import dictionary_ambiguity_game

    nominal = dictionary_ambiguity_game(
        num_actions=7,
        frame_bias_options=((0,), (0,)),
    )
    robust = dictionary_ambiguity_game(
        num_actions=7,
        frame_bias_options=((0,), (0, 2)),
    )
    nominal_value, nominal_protocol = epoc_for_messages(nominal, 7)
    robust_value, _ = epoc_for_messages(robust, 7)
    deployed_value = robust.worst_case_regret(nominal_protocol)
    assert nominal_value == pytest.approx(0.0)
    assert robust_value <= deployed_value + 1e-10
    assert robust_value == pytest.approx(1.0 / 3.0)
    assert deployed_value == pytest.approx(2.0 / 3.0)

def test_world_specific_thresholds_support_lexicographic_robustness() -> None:
    # The same local types occur in two worlds that prefer opposite receiver
    # actions. Exact uniform coordination is impossible, but preserving world 0
    # exactly while allowing unit regret in world 1 is feasible.
    worlds = [
        World("world-0", "x", "y", np.asarray([[1.0, 0.0]])),
        World("world-1", "x", "y", np.asarray([[0.0, 1.0]])),
    ]
    game = EpistemicGame(worlds, (0,), (0, 1))
    assert not feasible_protocol(game, 1, 0.0).feasible

    result = feasible_protocol(
        game,
        1,
        0.0,
        world_epsilon={"world-0": 0.0, "world-1": 1.0},
    )
    assert result.feasible
    assert result.protocol is not None
    assert result.protocol.receiver_action[("y", 0)] == 0

