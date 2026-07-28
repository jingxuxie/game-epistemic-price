from __future__ import annotations

from dataclasses import dataclass
from math import ceil, log2
from typing import Iterable, Mapping

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp
from scipy.sparse import coo_matrix

from .model import EpistemicGame, Protocol


@dataclass(frozen=True)
class FeasibilityResult:
    feasible: bool
    protocol: Protocol | None
    status: int
    message: str


class _MILPBuilder:
    def __init__(self) -> None:
        self.objective: list[float] = []
        self.lower_bounds: list[float] = []
        self.upper_bounds: list[float] = []
        self.integrality: list[int] = []
        self.rows: list[int] = []
        self.cols: list[int] = []
        self.data: list[float] = []
        self.constraint_lower: list[float] = []
        self.constraint_upper: list[float] = []

    def add_variable(
        self,
        *,
        objective: float = 0.0,
        lower: float = 0.0,
        upper: float = 1.0,
        integer: bool = True,
    ) -> int:
        index = len(self.objective)
        self.objective.append(float(objective))
        self.lower_bounds.append(float(lower))
        self.upper_bounds.append(float(upper))
        self.integrality.append(1 if integer else 0)
        return index

    def add_constraint(
        self,
        coefficients: Iterable[tuple[int, float]],
        *,
        lower: float = -np.inf,
        upper: float = np.inf,
    ) -> None:
        row = len(self.constraint_lower)
        for column, value in coefficients:
            if value != 0:
                self.rows.append(row)
                self.cols.append(column)
                self.data.append(float(value))
        self.constraint_lower.append(float(lower))
        self.constraint_upper.append(float(upper))

    def solve(self, *, time_limit: float | None = None):
        matrix = coo_matrix(
            (self.data, (self.rows, self.cols)),
            shape=(len(self.constraint_lower), len(self.objective)),
        ).tocsr()
        options: dict[str, float | bool] = {"disp": False}
        if time_limit is not None:
            options["time_limit"] = float(time_limit)
        return milp(
            c=np.asarray(self.objective),
            integrality=np.asarray(self.integrality),
            bounds=Bounds(
                np.asarray(self.lower_bounds), np.asarray(self.upper_bounds)
            ),
            constraints=LinearConstraint(
                matrix,
                np.asarray(self.constraint_lower),
                np.asarray(self.constraint_upper),
            ),
            options=options,
        )


def feasible_protocol(
    game: EpistemicGame,
    num_messages: int,
    epsilon: float,
    *,
    world_epsilon: Mapping[str, float] | None = None,
    time_limit: float | None = None,
) -> FeasibilityResult:
    """Find a deterministic protocol meeting world-wise regret thresholds.

    By default every world uses ``epsilon``. ``world_epsilon`` can override the
    threshold for named worlds, which is useful for lexicographic robustness
    experiments while preserving the standard uniform-threshold formulation.
    """

    if num_messages < 1:
        raise ValueError("num_messages must be positive")
    n_x = len(game.sender_types)
    n_y = len(game.receiver_types)
    n_a = game.num_sender_actions
    n_b = game.num_receiver_actions

    builder = _MILPBuilder()

    # s[x,m,a] = 1 iff sender type x emits message m and takes action a.
    s = np.empty((n_x, num_messages, n_a), dtype=int)
    for x in range(n_x):
        for m in range(num_messages):
            for a in range(n_a):
                s[x, m, a] = builder.add_variable()

    # r[y,m,b] = 1 iff receiver type y responds to message m with action b.
    r = np.empty((n_y, num_messages, n_b), dtype=int)
    for y in range(n_y):
        for m in range(num_messages):
            for b in range(n_b):
                r[y, m, b] = builder.add_variable()

    for x in range(n_x):
        builder.add_constraint(
            ((s[x, m, a], 1.0) for m in range(num_messages) for a in range(n_a)),
            lower=1.0,
            upper=1.0,
        )
    for y in range(n_y):
        for m in range(num_messages):
            builder.add_constraint(
                ((r[y, m, b], 1.0) for b in range(n_b)),
                lower=1.0,
                upper=1.0,
            )

    tolerance = 1e-10
    for world in game.worlds:
        x = game.sender_type_index[world.sender_type]
        y = game.receiver_type_index[world.receiver_type]
        optimum = world.oracle_value
        limit = epsilon if world_epsilon is None else world_epsilon.get(
            world.name, epsilon
        )
        for a in range(n_a):
            for b in range(n_b):
                if optimum - float(world.payoff[a, b]) > limit + tolerance:
                    for m in range(num_messages):
                        builder.add_constraint(
                            ((s[x, m, a], 1.0), (r[y, m, b], 1.0)),
                            upper=1.0,
                        )

    result = builder.solve(time_limit=time_limit)
    status = int(result.status)
    solver_message = str(result.message)

    # HiGHS status 2 is a certificate of infeasibility.  A resource limit
    # (status 1) is not: it may contain a feasible incumbent, or it may have
    # found nothing.  Treating every non-success status as infeasible would make
    # the outer binary search silently overestimate EPoC.
    if status == 2:
        return FeasibilityResult(False, None, status, solver_message)
    if result.x is None:
        if status == 1:
            raise TimeoutError(
                "protocol MILP hit a resource limit without a feasible incumbent: "
                + solver_message
            )
        raise RuntimeError(
            f"protocol MILP ended without a feasibility certificate or incumbent "
            f"(status={status}): {solver_message}"
        )

    values = np.asarray(result.x)
    message: dict[object, int] = {}
    sender_action: dict[object, int] = {}
    receiver_action: dict[tuple[object, int], int] = {}
    for x_index, x_type in enumerate(game.sender_types):
        flat = values[s[x_index].ravel()]
        chosen = int(np.argmax(flat))
        m, a = divmod(chosen, n_a)
        message[x_type] = m
        sender_action[x_type] = a
    for y_index, y_type in enumerate(game.receiver_types):
        for m in range(num_messages):
            b = int(np.argmax(values[r[y_index, m]]))
            receiver_action[(y_type, m)] = b

    protocol = Protocol(message, sender_action, receiver_action, num_messages)
    for world in game.worlds:
        limit = epsilon if world_epsilon is None else world_epsilon.get(
            world.name, epsilon
        )
        x, y = world.sender_type, world.receiver_type
        regret = world.regret(
            protocol.sender_action[x],
            protocol.receiver_action[(y, protocol.message[x])],
        )
        if regret > limit + 1e-7:
            raise RuntimeError(
                "MILP decoder returned a protocol violating a world threshold"
            )
    return FeasibilityResult(True, protocol, status, solver_message)


def minimum_messages(
    game: EpistemicGame,
    epsilon: float,
    *,
    max_messages: int | None = None,
    time_limit: float | None = None,
) -> tuple[int, Protocol]:
    """Return the minimum message alphabet size achieving regret ``epsilon``."""

    if max_messages is None:
        max_messages = len(game.sender_types)
    for num_messages in range(1, max_messages + 1):
        result = feasible_protocol(
            game, num_messages, epsilon, time_limit=time_limit
        )
        if result.feasible and result.protocol is not None:
            return num_messages, result.protocol
    raise ValueError(
        f"no protocol found with at most {max_messages} messages at epsilon={epsilon}"
    )


def epoc_for_messages(
    game: EpistemicGame,
    num_messages: int,
    *,
    time_limit: float | None = None,
) -> tuple[float, Protocol]:
    """Compute exact worst-case EPoC for a fixed message alphabet size."""

    levels = game.regret_levels()
    low, high = 0, len(levels) - 1
    best_protocol: Protocol | None = None
    while low < high:
        middle = (low + high) // 2
        result = feasible_protocol(
            game, num_messages, levels[middle], time_limit=time_limit
        )
        if result.feasible:
            high = middle
            best_protocol = result.protocol
        else:
            low = middle + 1
    epsilon = levels[low]
    if best_protocol is None or game.worst_case_regret(best_protocol) > epsilon + 1e-8:
        result = feasible_protocol(game, num_messages, epsilon, time_limit=time_limit)
        if not result.feasible or result.protocol is None:
            raise RuntimeError("binary search ended at an infeasible regret level")
        best_protocol = result.protocol
    return epsilon, best_protocol


def epoc_frontier(
    game: EpistemicGame,
    *,
    max_messages: int | None = None,
    time_limit: float | None = None,
) -> list[dict[str, float | int]]:
    """Compute the exact loss--communication frontier."""

    if max_messages is None:
        max_messages = len(game.sender_types)
    rows: list[dict[str, float | int]] = []
    for messages in range(1, max_messages + 1):
        epsilon, _ = epoc_for_messages(game, messages, time_limit=time_limit)
        rows.append(
            {
                "messages": messages,
                "bits": int(ceil(log2(messages))) if messages > 1 else 0,
                "epoc": float(epsilon),
            }
        )
    return rows
