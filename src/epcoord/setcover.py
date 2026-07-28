from __future__ import annotations

from dataclasses import dataclass
from typing import Hashable, Iterable, Sequence

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp
from scipy.sparse import coo_matrix


@dataclass(frozen=True)
class HittingSetResult:
    size: int
    selected: tuple[Hashable, ...]


@dataclass(frozen=True)
class GraphColoringResult:
    size: int
    colors: tuple[int, ...]


def _greedy_dsatur_coloring(adjacency: np.ndarray) -> GraphColoringResult:
    """Return a deterministic DSATUR upper bound."""

    matrix = np.asarray(adjacency, dtype=bool)
    if matrix.ndim != 2 or matrix.shape[0] != matrix.shape[1]:
        raise ValueError("adjacency must be a square matrix")
    if np.any(np.diag(matrix)) or not np.array_equal(matrix, matrix.T):
        raise ValueError("adjacency must be symmetric with a zero diagonal")
    n = matrix.shape[0]
    if n == 0:
        return GraphColoringResult(0, ())

    colors = [-1] * n
    neighbor_colors = [set() for _ in range(n)]
    degrees = matrix.sum(axis=1).astype(int).tolist()
    for _ in range(n):
        vertex = max(
            (i for i in range(n) if colors[i] < 0),
            key=lambda i: (len(neighbor_colors[i]), degrees[i], -i),
        )
        forbidden = neighbor_colors[vertex]
        color = 0
        while color in forbidden:
            color += 1
        colors[vertex] = color
        for neighbor in np.flatnonzero(matrix[vertex]):
            if colors[int(neighbor)] < 0:
                neighbor_colors[int(neighbor)].add(color)
    return GraphColoringResult(max(colors) + 1, tuple(colors))


def _k_colorable_milp(
    adjacency: np.ndarray,
    num_colors: int,
    *,
    time_limit: float | None = None,
) -> GraphColoringResult | None:
    matrix = np.asarray(adjacency, dtype=bool)
    n = matrix.shape[0]
    if n == 0:
        return GraphColoringResult(0, ())
    if num_colors < 1:
        return None

    # z[v,c] indicates that vertex v receives color c.
    num_variables = n * num_colors
    rows: list[int] = []
    cols: list[int] = []
    data: list[float] = []
    lower: list[float] = []
    upper: list[float] = []

    def add(coefficients, lo=-np.inf, hi=np.inf):
        row = len(lower)
        for col, value in coefficients:
            rows.append(row)
            cols.append(col)
            data.append(float(value))
        lower.append(float(lo))
        upper.append(float(hi))

    def z(vertex: int, color: int) -> int:
        return vertex * num_colors + color

    for vertex in range(n):
        add(((z(vertex, color), 1.0) for color in range(num_colors)), 1.0, 1.0)
    edge_rows, edge_cols = np.where(np.triu(matrix, k=1))
    for first, second in zip(edge_rows.tolist(), edge_cols.tolist()):
        for color in range(num_colors):
            add(((z(first, color), 1.0), (z(second, color), 1.0)), hi=1.0)

    # Break color-permutation symmetry by fixing vertex zero to color zero.
    add(((z(0, 0), 1.0),), 1.0, 1.0)

    constraint_matrix = coo_matrix(
        (data, (rows, cols)), shape=(len(lower), num_variables)
    ).tocsr()
    options: dict[str, float | bool] = {"disp": False}
    if time_limit is not None:
        options["time_limit"] = float(time_limit)
    result = milp(
        c=np.zeros(num_variables),
        integrality=np.ones(num_variables, dtype=int),
        bounds=Bounds(np.zeros(num_variables), np.ones(num_variables)),
        constraints=LinearConstraint(
            constraint_matrix, np.asarray(lower), np.asarray(upper)
        ),
        options=options,
    )
    if not result.success or result.x is None:
        return None
    values = np.asarray(result.x).reshape(n, num_colors)
    colors = tuple(int(np.argmax(values[vertex])) for vertex in range(n))
    return GraphColoringResult(num_colors, colors)


def _maximum_clique_size(adjacency: np.ndarray) -> int:
    """Exact maximum clique size for the small graphs used in experiments."""

    matrix = np.asarray(adjacency, dtype=bool)
    n = matrix.shape[0]
    masks = [
        sum(1 << int(neighbor) for neighbor in np.flatnonzero(matrix[vertex]))
        for vertex in range(n)
    ]
    best = 0

    def expand(size: int, candidates: int) -> None:
        nonlocal best
        if size + candidates.bit_count() <= best:
            return
        while candidates:
            if size + candidates.bit_count() <= best:
                return
            # A high-degree candidate generally tightens the bound sooner.
            options = [i for i in range(n) if candidates & (1 << i)]
            vertex = max(
                options, key=lambda i: (masks[i] & candidates).bit_count()
            )
            bit = 1 << vertex
            expand(size + 1, candidates & masks[vertex])
            candidates &= ~bit
        best = max(best, size)

    expand(0, (1 << n) - 1)
    return best


def exact_graph_coloring(
    adjacency: np.ndarray, *, time_limit: float | None = None
) -> GraphColoringResult:
    """Compute the exact chromatic number with DSATUR branch-and-bound.

    This implementation is intended for the small pairwise-conflict graphs in
    the paper. It uses a greedy DSATUR coloring as an upper bound and an exact
    maximum-clique lower bound.
    """

    import time

    matrix = np.asarray(adjacency, dtype=bool)
    if matrix.ndim != 2 or matrix.shape[0] != matrix.shape[1]:
        raise ValueError("adjacency must be a square matrix")
    if np.any(np.diag(matrix)) or not np.array_equal(matrix, matrix.T):
        raise ValueError("adjacency must be symmetric with a zero diagonal")
    n = matrix.shape[0]
    if n == 0:
        return GraphColoringResult(0, ())

    greedy = _greedy_dsatur_coloring(matrix)
    lower_bound = _maximum_clique_size(matrix)
    if greedy.size == lower_bound:
        return greedy

    best_size = greedy.size
    best_colors = list(greedy.colors)
    colors = [-1] * n
    degrees = matrix.sum(axis=1).astype(int).tolist()
    neighbors = [np.flatnonzero(matrix[v]).astype(int).tolist() for v in range(n)]
    start = time.perf_counter()

    def check_time() -> None:
        if time_limit is not None and time.perf_counter() - start > time_limit:
            raise TimeoutError("exact graph coloring exceeded its time limit")

    def search(colored: int, used_colors: int) -> None:
        nonlocal best_size, best_colors
        check_time()
        if used_colors >= best_size:
            return
        if colored == n:
            best_size = used_colors
            best_colors = colors.copy()
            return

        uncolored = [v for v in range(n) if colors[v] < 0]
        vertex = max(
            uncolored,
            key=lambda v: (
                len({colors[u] for u in neighbors[v] if colors[u] >= 0}),
                sum(colors[u] < 0 for u in neighbors[v]),
                degrees[v],
                -v,
            ),
        )
        forbidden = {colors[u] for u in neighbors[vertex] if colors[u] >= 0}

        # Existing colors first; equivalent color permutations are avoided by
        # introducing at most the next new color.
        for color in range(used_colors):
            if color in forbidden:
                continue
            colors[vertex] = color
            search(colored + 1, used_colors)
            colors[vertex] = -1

        if used_colors + 1 < best_size:
            colors[vertex] = used_colors
            search(colored + 1, used_colors + 1)
            colors[vertex] = -1

    # Fix the first highest-degree vertex to color zero to remove global color
    # symmetry.
    first = max(range(n), key=lambda v: (degrees[v], -v))
    colors[first] = 0
    search(1, 1)
    return GraphColoringResult(best_size, tuple(best_colors))


def exact_hitting_set(
    sets: Sequence[Iterable[Hashable]],
    *,
    universe: Sequence[Hashable] | None = None,
    time_limit: float | None = None,
) -> HittingSetResult:
    family = [set(values) for values in sets]
    if not family or any(not values for values in family):
        raise ValueError("the family must contain non-empty sets")
    if universe is None:
        universe_values = tuple(
            dict.fromkeys(value for values in family for value in values)
        )
    else:
        universe_values = tuple(universe)
    index = {value: position for position, value in enumerate(universe_values)}

    rows: list[int] = []
    cols: list[int] = []
    data: list[float] = []
    for row, values in enumerate(family):
        for value in values:
            if value not in index:
                raise ValueError("set contains an element outside the universe")
            rows.append(row)
            cols.append(index[value])
            data.append(1.0)
    matrix = coo_matrix(
        (data, (rows, cols)), shape=(len(family), len(universe_values))
    ).tocsr()
    options: dict[str, float | bool] = {"disp": False}
    if time_limit is not None:
        options["time_limit"] = float(time_limit)
    result = milp(
        c=np.ones(len(universe_values)),
        integrality=np.ones(len(universe_values), dtype=int),
        bounds=Bounds(np.zeros(len(universe_values)), np.ones(len(universe_values))),
        constraints=LinearConstraint(
            matrix, np.ones(len(family)), np.full(len(family), np.inf)
        ),
        options=options,
    )
    if not result.success or result.x is None:
        raise RuntimeError(f"hitting-set MILP failed: {result.message}")
    selected = tuple(
        universe_values[i] for i, value in enumerate(result.x) if value > 0.5
    )
    return HittingSetResult(len(selected), selected)


def greedy_hitting_set(
    sets: Sequence[Iterable[Hashable]],
    *,
    universe: Sequence[Hashable] | None = None,
) -> HittingSetResult:
    family = [set(values) for values in sets]
    if not family or any(not values for values in family):
        raise ValueError("the family must contain non-empty sets")
    if universe is None:
        universe_values = tuple(
            dict.fromkeys(value for values in family for value in values)
        )
    else:
        universe_values = tuple(universe)

    uncovered = set(range(len(family)))
    selected: list[Hashable] = []
    while uncovered:
        best = max(
            universe_values,
            key=lambda value: sum(value in family[index] for index in uncovered),
        )
        covered = {index for index in uncovered if best in family[index]}
        if not covered:
            raise RuntimeError("universe does not hit every set")
        selected.append(best)
        uncovered -= covered
    return HittingSetResult(len(selected), tuple(selected))


def greedy_interval_stabbing(
    intervals: Sequence[tuple[int, int]],
) -> HittingSetResult:
    """Optimal right-endpoint greedy algorithm for discrete intervals."""

    remaining = sorted(intervals, key=lambda interval: (interval[1], interval[0]))
    selected: list[int] = []
    while remaining:
        point = remaining[0][1]
        selected.append(point)
        remaining = [
            interval
            for interval in remaining
            if not (interval[0] <= point <= interval[1])
        ]
    return HittingSetResult(len(selected), tuple(selected))


def pairwise_conflict_graph(sets: Sequence[Iterable[Hashable]]) -> np.ndarray:
    family = [set(values) for values in sets]
    adjacency = np.zeros((len(family), len(family)), dtype=bool)
    for i in range(len(family)):
        for j in range(i + 1, len(family)):
            if not family[i].intersection(family[j]):
                adjacency[i, j] = adjacency[j, i] = True
    return adjacency
