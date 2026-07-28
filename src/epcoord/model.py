from __future__ import annotations

from dataclasses import dataclass
from typing import Hashable, Iterable, Mapping, Sequence

import numpy as np

Type = Hashable
Action = Hashable


@dataclass(frozen=True)
class World:
    """A possible world in a two-agent common-payoff game.

    ``payoff[a, b]`` is the common payoff when the sender takes action ``a``
    and the receiver takes action ``b``. The agents observe only ``sender_type``
    and ``receiver_type`` respectively.
    """

    name: str
    sender_type: Type
    receiver_type: Type
    payoff: np.ndarray
    probability: float = 1.0

    def __post_init__(self) -> None:
        payoff = np.asarray(self.payoff, dtype=float)
        if payoff.ndim != 2:
            raise ValueError("payoff must be a two-dimensional array")
        if not np.all(np.isfinite(payoff)):
            raise ValueError("payoff contains a non-finite entry")
        if self.probability < 0:
            raise ValueError("world probability must be non-negative")
        object.__setattr__(self, "payoff", payoff)

    @property
    def oracle_value(self) -> float:
        return float(np.max(self.payoff))

    def regret(self, sender_action: int, receiver_action: int) -> float:
        return self.oracle_value - float(self.payoff[sender_action, receiver_action])


@dataclass(frozen=True)
class Protocol:
    """A deterministic one-way protocol.

    ``message[x]`` and ``sender_action[x]`` depend only on the sender type.
    ``receiver_action[(y, m)]`` depends on the receiver type and message.
    """

    message: Mapping[Type, int]
    sender_action: Mapping[Type, int]
    receiver_action: Mapping[tuple[Type, int], int]
    num_messages: int


class EpistemicGame:
    """Finite epistemic coordination instance."""

    def __init__(
        self,
        worlds: Iterable[World],
        sender_actions: Sequence[Action],
        receiver_actions: Sequence[Action],
        name: str = "instance",
    ) -> None:
        self.worlds = tuple(worlds)
        if not self.worlds:
            raise ValueError("an epistemic game needs at least one world")
        self.sender_actions = tuple(sender_actions)
        self.receiver_actions = tuple(receiver_actions)
        if not self.sender_actions or not self.receiver_actions:
            raise ValueError("both agents need at least one action")
        expected_shape = (len(self.sender_actions), len(self.receiver_actions))
        for world in self.worlds:
            if world.payoff.shape != expected_shape:
                raise ValueError(
                    f"world {world.name!r} has shape {world.payoff.shape}; "
                    f"expected {expected_shape}"
                )
        self.name = name
        self.sender_types = tuple(dict.fromkeys(w.sender_type for w in self.worlds))
        self.receiver_types = tuple(dict.fromkeys(w.receiver_type for w in self.worlds))
        self.sender_type_index = {x: i for i, x in enumerate(self.sender_types)}
        self.receiver_type_index = {y: i for i, y in enumerate(self.receiver_types)}

    @property
    def num_sender_actions(self) -> int:
        return len(self.sender_actions)

    @property
    def num_receiver_actions(self) -> int:
        return len(self.receiver_actions)

    def regret_levels(self) -> list[float]:
        """All distinct worst-case regrets attainable in a world."""

        values = {0.0}
        for world in self.worlds:
            optimum = world.oracle_value
            for value in world.payoff.ravel():
                values.add(float(optimum - value))
        return sorted(values)

    def worst_case_regret(self, protocol: Protocol) -> float:
        worst = 0.0
        for world in self.worlds:
            x, y = world.sender_type, world.receiver_type
            m = protocol.message[x]
            a = protocol.sender_action[x]
            b = protocol.receiver_action[(y, m)]
            worst = max(worst, world.regret(a, b))
        return worst

    def expected_regret(self, protocol: Protocol) -> float:
        total_probability = sum(w.probability for w in self.worlds)
        if total_probability <= 0:
            raise ValueError("at least one world must have positive probability")
        return sum(
            w.probability
            * w.regret(
                protocol.sender_action[w.sender_type],
                protocol.receiver_action[
                    (w.receiver_type, protocol.message[w.sender_type])
                ],
            )
            for w in self.worlds
        ) / total_probability
