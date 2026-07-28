from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class Literal:
    variable: int
    positive: bool

    def evaluate(self, assignment: list[bool]) -> bool:
        value = assignment[self.variable]
        return value if self.positive else not value


class TwoSAT:
    """Linear-time 2-SAT solver using strongly connected components."""

    def __init__(self, num_variables: int) -> None:
        if num_variables < 0:
            raise ValueError("num_variables must be non-negative")
        self.num_variables = num_variables
        self.graph: list[list[int]] = [[] for _ in range(2 * num_variables)]
        self.reverse: list[list[int]] = [[] for _ in range(2 * num_variables)]

    @staticmethod
    def _node(literal: Literal) -> int:
        return 2 * literal.variable + (0 if literal.positive else 1)

    @staticmethod
    def _neg_node(node: int) -> int:
        return node ^ 1

    def _add_implication(self, source: int, target: int) -> None:
        self.graph[source].append(target)
        self.reverse[target].append(source)

    def add_clause(self, first: Literal, second: Literal) -> None:
        """Add ``first OR second``."""

        a = self._node(first)
        b = self._node(second)
        self._add_implication(self._neg_node(a), b)
        self._add_implication(self._neg_node(b), a)

    def solve(self) -> list[bool] | None:
        n_nodes = 2 * self.num_variables
        visited = [False] * n_nodes
        order: list[int] = []

        def dfs(start: int) -> None:
            stack: list[tuple[int, int]] = [(start, 0)]
            visited[start] = True
            while stack:
                node, index = stack[-1]
                if index < len(self.graph[node]):
                    nxt = self.graph[node][index]
                    stack[-1] = (node, index + 1)
                    if not visited[nxt]:
                        visited[nxt] = True
                        stack.append((nxt, 0))
                else:
                    order.append(node)
                    stack.pop()

        for node in range(n_nodes):
            if not visited[node]:
                dfs(node)

        component = [-1] * n_nodes

        def reverse_dfs(start: int, label: int) -> None:
            stack = [start]
            component[start] = label
            while stack:
                node = stack.pop()
                for nxt in self.reverse[node]:
                    if component[nxt] == -1:
                        component[nxt] = label
                        stack.append(nxt)

        label = 0
        for node in reversed(order):
            if component[node] == -1:
                reverse_dfs(node, label)
                label += 1

        assignment = [False] * self.num_variables
        for variable in range(self.num_variables):
            positive = 2 * variable
            negative = positive + 1
            if component[positive] == component[negative]:
                return None
            assignment[variable] = component[positive] > component[negative]
        return assignment


def solve_binary_coordination(
    num_sender_types: int,
    num_receiver_types: int,
    forbidden: Iterable[tuple[int, int, int, int]],
) -> tuple[list[int], list[int]] | None:
    """Solve a binary-action zero-communication instance.

    Each tuple ``(x, y, a, b)`` forbids the joint assignment
    ``sender[x] = a`` and ``receiver[y] = b``.
    """

    solver = TwoSAT(num_sender_types + num_receiver_types)
    for x, y, a, b in forbidden:
        if a not in (0, 1) or b not in (0, 1):
            raise ValueError("binary actions must be 0 or 1")
        # A_x != a OR B_y != b.
        first = Literal(x, positive=(a == 0))
        second = Literal(num_sender_types + y, positive=(b == 0))
        solver.add_clause(first, second)
    assignment = solver.solve()
    if assignment is None:
        return None
    sender = [int(value) for value in assignment[:num_sender_types]]
    receiver = [int(value) for value in assignment[num_sender_types:]]
    return sender, receiver
