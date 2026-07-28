from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Hashable, Sequence, TypeVar

from .setcover import exact_hitting_set

Point = TypeVar("Point", bound=Hashable)
Distance = Callable[[Point, Point], float]


@dataclass(frozen=True)
class MetricCenterResult:
    """A finite metric ``k``-center solution."""

    radius: float
    centers: tuple[Point, ...]


def manhattan_distance(first: tuple[int, int], second: tuple[int, int]) -> int:
    return abs(first[0] - second[0]) + abs(first[1] - second[1])


def exact_metric_center(
    points: Sequence[Point],
    num_centers: int,
    *,
    distance: Distance,
    time_limit: float | None = None,
) -> MetricCenterResult:
    """Solve finite metric ``k``-center exactly by radius feasibility.

    Candidate centers and clients are both ``points``.  For a candidate radius,
    every client induces the set of centers that cover it; feasibility is thus a
    hitting-set decision.  Binary search is unnecessary because the finite set
    of pairwise distances can simply be scanned in increasing order.
    """

    values = tuple(points)
    if not values:
        raise ValueError("points must be non-empty")
    if not (1 <= num_centers <= len(values)):
        raise ValueError("num_centers must lie in [1, len(points)]")

    distance_levels = sorted(
        {float(distance(client, center)) for client in values for center in values}
    )
    for radius in distance_levels:
        covering_sets = [
            {center for center in values if distance(client, center) <= radius + 1e-12}
            for client in values
        ]
        hitting = exact_hitting_set(
            covering_sets, universe=values, time_limit=time_limit
        )
        if hitting.size <= num_centers:
            return MetricCenterResult(radius, tuple(hitting.selected))
    raise RuntimeError("the largest pairwise distance should always be feasible")


def farthest_first_metric_center(
    points: Sequence[Point],
    num_centers: int,
    *,
    distance: Distance,
) -> MetricCenterResult:
    """Deterministic Gonzalez farthest-first traversal for finite metric center."""

    values = tuple(points)
    if not values:
        raise ValueError("points must be non-empty")
    if not (1 <= num_centers <= len(values)):
        raise ValueError("num_centers must lie in [1, len(points)]")

    centers: list[Point] = [values[0]]
    while len(centers) < num_centers:
        next_center = max(
            (point for point in values if point not in centers),
            key=lambda point: (
                min(distance(point, center) for center in centers),
                -values.index(point),
            ),
        )
        centers.append(next_center)

    radius = max(min(distance(point, center) for center in centers) for point in values)
    return MetricCenterResult(float(radius), tuple(centers))
