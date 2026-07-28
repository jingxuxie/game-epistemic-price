from __future__ import annotations

from itertools import combinations
from random import Random
from typing import Hashable, Iterable, Sequence

import numpy as np

from .model import EpistemicGame, World


def set_system_game(
    acceptable_sets: Sequence[Iterable[Hashable]],
    *,
    action_universe: Sequence[Hashable] | None = None,
    name: str = "set-system",
) -> EpistemicGame:
    """One-receiver, one-sender-action coordination game.

    Sender type ``x`` can be coordinated by a receiver action in
    ``acceptable_sets[x]``. The minimum zero-regret message alphabet is exactly
    the transversal (hitting-set) number of the set family.
    """

    sets = [set(values) for values in acceptable_sets]
    if not sets:
        raise ValueError("acceptable_sets must be non-empty")
    if any(not values for values in sets):
        raise ValueError("every sender type needs at least one acceptable action")
    if action_universe is None:
        universe = tuple(dict.fromkeys(value for values in sets for value in values))
    else:
        universe = tuple(action_universe)
    action_index = {action: index for index, action in enumerate(universe)}
    if any(value not in action_index for values in sets for value in values):
        raise ValueError("an acceptable set contains an action outside the universe")

    worlds: list[World] = []
    for x, values in enumerate(sets):
        payoff = np.zeros((1, len(universe)), dtype=float)
        for value in values:
            payoff[0, action_index[value]] = 1.0
        worlds.append(World(f"type-{x}", x, "receiver", payoff))
    return EpistemicGame(worlds, ("noop",), universe, name=name)


def higher_order_triangle_game() -> EpistemicGame:
    """Three sender types that are pairwise but not jointly compatible."""

    return set_system_game(
        [{"A", "B"}, {"B", "C"}, {"A", "C"}],
        action_universe=("A", "B", "C"),
        name="higher-order-triangle",
    )


def _canonical_projective_vector(vector: tuple[int, int, int], q: int) -> tuple[int, int, int]:
    for value in vector:
        if value % q != 0:
            inverse = pow(value % q, -1, q)
            return tuple((coordinate * inverse) % q for coordinate in vector)
    raise ValueError("the zero vector has no projective representative")


def projective_plane_incidence(q: int) -> tuple[list[tuple[int, int, int]], list[set[int]]]:
    """Return points and line-incidence sets for PG(2,q), with prime ``q``."""

    if q < 2:
        raise ValueError("q must be at least 2")
    # ``pow(a, -1, q)`` exists for every nonzero a only when q is prime here.
    for divisor in range(2, int(q**0.5) + 1):
        if q % divisor == 0:
            raise ValueError("this lightweight generator currently requires prime q")

    representatives = {
        _canonical_projective_vector((a, b, c), q)
        for a in range(q)
        for b in range(q)
        for c in range(q)
        if (a, b, c) != (0, 0, 0)
    }
    points = sorted(representatives)
    lines = sorted(representatives)
    incidence: list[set[int]] = []
    for line in lines:
        members = {
            index
            for index, point in enumerate(points)
            if sum(line[i] * point[i] for i in range(3)) % q == 0
        }
        incidence.append(members)

    expected = q * q + q + 1
    if len(points) != expected or len(lines) != expected:
        raise RuntimeError("invalid projective-plane cardinality")
    if any(len(members) != q + 1 for members in incidence):
        raise RuntimeError("invalid projective-plane line size")
    return points, incidence


def projective_plane_game(q: int) -> EpistemicGame:
    points, incidence = projective_plane_incidence(q)
    return set_system_game(
        incidence,
        action_universe=tuple(range(len(points))),
        name=f"projective-plane-q{q}",
    )


def interval_game(
    intervals: Sequence[tuple[int, int]],
    *,
    num_actions: int,
    name: str = "interval-game",
) -> EpistemicGame:
    acceptable: list[set[int]] = []
    for left, right in intervals:
        if not (0 <= left <= right < num_actions):
            raise ValueError(f"invalid interval {(left, right)}")
        acceptable.append(set(range(left, right + 1)))
    return set_system_game(
        acceptable,
        action_universe=tuple(range(num_actions)),
        name=name,
    )


def random_set_system(
    *,
    num_types: int,
    num_actions: int,
    set_size: int,
    seed: int,
) -> list[set[int]]:
    if not (1 <= set_size <= num_actions):
        raise ValueError("set_size must lie in [1, num_actions]")
    rng = Random(seed)
    universe = list(range(num_actions))
    return [set(rng.sample(universe, set_size)) for _ in range(num_types)]


def random_intervals(
    *,
    num_types: int,
    num_actions: int,
    max_width: int,
    seed: int,
) -> list[tuple[int, int]]:
    rng = Random(seed)
    intervals: list[tuple[int, int]] = []
    for _ in range(num_types):
        left = rng.randrange(num_actions)
        width = rng.randrange(1, min(max_width, num_actions - left) + 1)
        intervals.append((left, left + width - 1))
    return intervals


def cyclic_distance(first: int, second: int, size: int) -> int:
    direct = abs(first - second)
    return min(direct, size - direct)


def private_lever_game(
    *,
    num_levers: int,
    noise_radius: int,
    receiver_bias_radius: int = 0,
    num_receiver_frames: int | None = None,
    name: str | None = None,
) -> EpistemicGame:
    """Noisy cyclic lever selection with a latent receiver dictionary bias.

    The sender observes an estimated physical target ``x``; the true target may
    lie within cyclic radius ``noise_radius``.  Receiver type ``shift`` is a
    nominal local-to-physical coordinate frame.  The realized dictionary may
    additionally contain an unobserved cyclic bias within
    ``receiver_bias_radius``.  Thus communication can quantize and reveal the
    sender estimate, but it cannot identify either latent disturbance.
    """

    if num_levers < 3 or num_levers % 2 == 0:
        raise ValueError("num_levers must be odd and at least 3")
    half = num_levers // 2
    if not (0 <= noise_radius <= half):
        raise ValueError("invalid noise radius")
    if not (0 <= receiver_bias_radius <= half):
        raise ValueError("invalid receiver bias radius")
    if num_receiver_frames is None:
        num_receiver_frames = num_levers
    if not (1 <= num_receiver_frames <= num_levers):
        raise ValueError("invalid number of receiver frames")

    frames = tuple(range(num_receiver_frames))
    biases = tuple(range(-receiver_bias_radius, receiver_bias_radius + 1))
    worlds: list[World] = []
    for estimate in range(num_levers):
        possible_targets = [
            target
            for target in range(num_levers)
            if cyclic_distance(estimate, target, num_levers) <= noise_radius
        ]
        for shift in frames:
            for target in possible_targets:
                for bias in biases:
                    payoff = np.empty((1, num_levers), dtype=float)
                    for local_action in range(num_levers):
                        physical_action = (local_action + shift + bias) % num_levers
                        distance = cyclic_distance(
                            physical_action, target, num_levers
                        )
                        payoff[0, local_action] = 1.0 - distance / half
                    worlds.append(
                        World(
                            (
                                f"estimate-{estimate}-frame-{shift}-"
                                f"target-{target}-bias-{bias}"
                            ),
                            estimate,
                            shift,
                            payoff,
                        )
                    )
    return EpistemicGame(
        worlds,
        sender_actions=("noop",),
        receiver_actions=tuple(range(num_levers)),
        name=name
        or (
            f"private-lever-k{num_levers}-r{noise_radius}-"
            f"s{receiver_bias_radius}"
        ),
    )



_D4_NAMES = (
    "identity",
    "rot90",
    "rot180",
    "rot270",
    "reflect_vertical",
    "reflect_horizontal",
    "reflect_diagonal",
    "reflect_antidiagonal",
)


def square_grid_points(side_length: int) -> tuple[tuple[int, int], ...]:
    if side_length < 2:
        raise ValueError("side_length must be at least 2")
    return tuple(
        (row, column)
        for row in range(side_length)
        for column in range(side_length)
    )


def grid_isometry_names() -> tuple[str, ...]:
    return _D4_NAMES


def apply_grid_isometry(
    point: tuple[int, int], side_length: int, isometry: str
) -> tuple[int, int]:
    """Apply one of the eight square-grid rotations/reflections."""

    if isometry not in _D4_NAMES:
        raise ValueError(f"unknown grid isometry: {isometry}")
    row, column = point
    n = side_length - 1
    if not (0 <= row <= n and 0 <= column <= n):
        raise ValueError("point lies outside the square grid")
    transforms = {
        "identity": (row, column),
        "rot90": (column, n - row),
        "rot180": (n - row, n - column),
        "rot270": (n - column, row),
        "reflect_vertical": (row, n - column),
        "reflect_horizontal": (n - row, column),
        "reflect_diagonal": (column, row),
        "reflect_antidiagonal": (n - column, n - row),
    }
    return transforms[isometry]


def grid_map_alignment_game(
    *,
    side_length: int,
    frame_names: Sequence[str] | None = None,
    name: str | None = None,
) -> EpistemicGame:
    """Private-map alignment on a square grid with Manhattan team payoff.

    The sender observes a target in physical coordinates.  The receiver knows
    its own rotation/reflection frame and chooses a local grid coordinate.  The
    realized physical action is the frame isometry applied to that local point.
    """

    points = square_grid_points(side_length)
    frames = tuple(frame_names or _D4_NAMES)
    if not frames:
        raise ValueError("at least one receiver frame is required")
    if any(frame not in _D4_NAMES for frame in frames):
        raise ValueError("frame_names contains an unknown isometry")

    diameter = 2 * (side_length - 1)
    worlds: list[World] = []
    for target in points:
        for frame in frames:
            payoff = np.empty((1, len(points)), dtype=float)
            for action_index, local_point in enumerate(points):
                physical = apply_grid_isometry(local_point, side_length, frame)
                distance = abs(physical[0] - target[0]) + abs(
                    physical[1] - target[1]
                )
                payoff[0, action_index] = 1.0 - distance / diameter
            worlds.append(
                World(
                    f"target-{target[0]}-{target[1]}-frame-{frame}",
                    target,
                    frame,
                    payoff,
                )
            )
    return EpistemicGame(
        worlds,
        sender_actions=("noop",),
        receiver_actions=points,
        name=name or f"grid-map-{side_length}x{side_length}",
    )

def pairwise_compatible_sets(acceptable_sets: Sequence[set[Hashable]]) -> bool:
    return all(first & second for first, second in combinations(acceptable_sets, 2))


def dictionary_ambiguity_game(
    *,
    num_actions: int,
    frame_bias_options: Sequence[Sequence[int]],
    name: str = "dictionary-ambiguity",
) -> EpistemicGame:
    """Cyclic target selection with an ambiguous receiver action dictionary.

    The sender observes the physical target. Receiver type ``frame`` identifies
    a nominal coordinate shift, but the true local-to-physical action mapping
    may additionally contain any bias listed for that frame. The bias itself is
    not observed, so adding options represents ambiguity about the model channel.
    """

    if num_actions < 3 or num_actions % 2 == 0:
        raise ValueError("num_actions must be odd and at least 3")
    if not frame_bias_options:
        raise ValueError("at least one receiver frame is required")
    normalized = [tuple(dict.fromkeys(int(b) % num_actions for b in biases)) for biases in frame_bias_options]
    if any(not biases for biases in normalized):
        raise ValueError("every receiver frame needs at least one possible bias")

    max_distance = num_actions // 2
    worlds: list[World] = []
    for target in range(num_actions):
        for frame, biases in enumerate(normalized):
            for bias in biases:
                payoff = np.empty((1, num_actions), dtype=float)
                for local_action in range(num_actions):
                    physical_action = (
                        local_action + frame + bias
                    ) % num_actions
                    payoff[0, local_action] = 1.0 - cyclic_distance(
                        physical_action, target, num_actions
                    ) / max_distance
                worlds.append(
                    World(
                        f"target-{target}-frame-{frame}-bias-{bias}",
                        target,
                        frame,
                        payoff,
                    )
                )
    return EpistemicGame(
        worlds,
        sender_actions=("noop",),
        receiver_actions=tuple(range(num_actions)),
        name=name,
    )
