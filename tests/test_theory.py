from __future__ import annotations

import pytest

from epcoord.families import dictionary_ambiguity_game, private_lever_game
from epcoord.milp import epoc_for_messages
from epcoord.theory import (
    private_lever_epoc_formula,
    receiver_only_full_revelation_floor,
)


@pytest.mark.parametrize("num_levers", [5, 7, 9])
@pytest.mark.parametrize("noise_radius", [0, 1])
def test_private_lever_closed_form(num_levers: int, noise_radius: int) -> None:
    if noise_radius > num_levers // 2:
        return
    game = private_lever_game(
        num_levers=num_levers,
        noise_radius=noise_radius,
        num_receiver_frames=min(3, num_levers),
    )
    for messages in range(1, num_levers + 1):
        exact, _ = epoc_for_messages(game, messages)
        theory = private_lever_epoc_formula(
            num_levers=num_levers,
            noise_radius=noise_radius,
            num_messages=messages,
        )
        assert exact == pytest.approx(theory)



def test_receiver_only_full_revelation_floor_matches_exact_milp() -> None:
    game = dictionary_ambiguity_game(
        num_actions=9,
        frame_bias_options=((0,), (0, 2), (0, 4)),
    )
    floor, response = receiver_only_full_revelation_floor(game)
    exact, _ = epoc_for_messages(game, len(game.sender_types))
    assert floor == pytest.approx(exact)
    assert set(response) == {
        (x, y) for x in game.sender_types for y in game.receiver_types
    }
