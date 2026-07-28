from __future__ import annotations

from math import ceil, floor

from .model import EpistemicGame


def odd_cycle_cover_radius(num_vertices: int, num_centers: int) -> int:
    """Minimum graph radius for covering an odd cycle by ``num_centers`` balls."""

    if num_vertices < 3 or num_vertices % 2 == 0:
        raise ValueError("num_vertices must be odd and at least 3")
    if not (1 <= num_centers <= num_vertices):
        raise ValueError("num_centers must lie in [1, num_vertices]")
    return ceil((num_vertices - num_centers) / (2 * num_centers))


def private_lever_epoc_formula(
    *,
    num_levers: int,
    noise_radius: int,
    num_messages: int,
    receiver_bias_radius: int = 0,
) -> float:
    """Exact EPoC for the odd cyclic private-lever family.

    Communication contributes the optimal cycle-covering radius, while sender
    target uncertainty and latent receiver-dictionary uncertainty add before the
    physical diameter cap.
    """

    if num_levers < 3 or num_levers % 2 == 0:
        raise ValueError("the closed form is stated for odd cycles")
    half = num_levers // 2
    if not (0 <= noise_radius <= half):
        raise ValueError("invalid noise radius")
    if not (0 <= receiver_bias_radius <= half):
        raise ValueError("invalid receiver bias radius")
    cover = odd_cycle_cover_radius(num_levers, num_messages)
    return min(half, cover + noise_radius + receiver_bias_radius) / half


def private_lever_min_messages_for_epsilon(
    *,
    num_levers: int,
    noise_radius: int,
    receiver_bias_radius: int,
    epsilon: float,
) -> int | None:
    """Invert the additive odd-cycle frontier at tolerance ``epsilon``.

    Returns ``None`` when the requested tolerance lies below the irreducible
    uncertainty floor, even with full sender-type revelation.
    """

    if num_levers < 3 or num_levers % 2 == 0:
        raise ValueError("the inverse is stated for odd cycles")
    half = num_levers // 2
    if not (0 <= noise_radius <= half):
        raise ValueError("invalid noise radius")
    if not (0 <= receiver_bias_radius <= half):
        raise ValueError("invalid receiver bias radius")
    if epsilon < 0:
        raise ValueError("epsilon must be non-negative")
    if epsilon >= 1:
        return 1

    admissible_cover = floor(epsilon * half + 1e-12) - noise_radius - receiver_bias_radius
    if admissible_cover < 0:
        return None
    return min(num_levers, ceil(num_levers / (2 * admissible_cover + 1)))


def receiver_only_full_revelation_floor(
    game: EpistemicGame,
) -> tuple[float, dict[tuple[object, object], int]]:
    """Exact full-sender-type revelation floor for receiver-only games.

    The sender must have one (strategically trivial) action. With at least one
    distinct message per sender type, the receiver can condition on ``(x, y)``
    but cannot distinguish latent worlds sharing that observed type pair.
    """

    if game.num_sender_actions != 1:
        raise ValueError("the receiver-only floor requires one sender action")

    cells: dict[tuple[object, object], list] = {}
    for world in game.worlds:
        cells.setdefault((world.sender_type, world.receiver_type), []).append(world)

    response: dict[tuple[object, object], int] = {}
    floor_value = 0.0
    for key, worlds in cells.items():
        best_action = 0
        best_regret = float("inf")
        for receiver_action in range(game.num_receiver_actions):
            cell_regret = max(world.regret(0, receiver_action) for world in worlds)
            if cell_regret < best_regret - 1e-12:
                best_regret = cell_regret
                best_action = receiver_action
        response[key] = best_action
        floor_value = max(floor_value, best_regret)
    return float(floor_value), response
