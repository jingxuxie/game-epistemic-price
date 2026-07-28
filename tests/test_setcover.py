from __future__ import annotations

from epcoord.families import random_set_system
from epcoord.setcover import exact_hitting_set, greedy_hitting_set


def test_greedy_hitting_set_is_feasible() -> None:
    for seed in range(10):
        sets = random_set_system(
            num_types=25, num_actions=15, set_size=4, seed=seed
        )
        exact = exact_hitting_set(sets, universe=range(15))
        greedy = greedy_hitting_set(sets, universe=range(15))
        assert greedy.size >= exact.size
        assert all(set(values).intersection(greedy.selected) for values in sets)


def test_exact_graph_coloring() -> None:
    import numpy as np

    from epcoord.setcover import exact_graph_coloring

    triangle = np.ones((3, 3), dtype=bool)
    np.fill_diagonal(triangle, False)
    assert exact_graph_coloring(triangle).size == 3

    cycle = np.zeros((5, 5), dtype=bool)
    for i in range(5):
        cycle[i, (i + 1) % 5] = True
        cycle[(i + 1) % 5, i] = True
    assert exact_graph_coloring(cycle).size == 3

    empty = np.zeros((8, 8), dtype=bool)
    assert exact_graph_coloring(empty).size == 1
