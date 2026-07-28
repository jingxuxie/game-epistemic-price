from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

# Embed TrueType outlines rather than Type 3 glyphs in submission figures.
plt.rcParams["pdf.fonttype"] = 42
plt.rcParams["ps.fonttype"] = 42

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
FIGURES = ROOT / "paper" / "figures"
FIGURES.mkdir(parents=True, exist_ok=True)


def save_both(name: str) -> None:
    plt.tight_layout()
    plt.savefig(FIGURES / f"{name}.pdf", bbox_inches="tight")
    plt.savefig(FIGURES / f"{name}.png", dpi=220, bbox_inches="tight")
    plt.close()


def plot_projective_gap() -> None:
    data = pd.read_csv(RESULTS / "projective_planes.csv")
    plt.figure(figsize=(4.7, 3.2))
    plt.plot(data["q"], data["exact_messages"], marker="o", label="Exact / theorem")
    plt.plot(
        data["q"],
        data["pairwise_graph_messages"],
        marker="s",
        linestyle="--",
        label="Pairwise graph",
    )
    plt.xlabel("Projective-plane order $q$")
    plt.ylabel("Minimum messages")
    plt.xticks(data["q"])
    plt.legend(frameon=False)
    save_both("projective_gap")


def plot_lever_frontier() -> None:
    data = pd.read_csv(RESULTS / "private_levers.csv")
    plt.figure(figsize=(4.7, 3.2))
    for (radius, bias), group in data.groupby(
        ["noise_radius", "receiver_bias_radius"]
    ):
        plt.plot(
            group["bits"],
            group["epoc"],
            marker="o",
            label=f"$r={int(radius)}, s={int(bias)}$",
        )
    plt.xlabel("Handshake budget (bits)")
    plt.ylabel("Worst-case regret (EPoC)")
    plt.xticks(sorted(data["bits"].unique()))
    plt.ylim(bottom=-0.02)
    plt.legend(frameon=False, fontsize=8, ncol=2)
    save_both("lever_frontier")


def plot_grid_map_alignment() -> None:
    data = pd.read_csv(RESULTS / "grid_map_alignment.csv")
    plt.figure(figsize=(4.7, 3.2))
    plt.plot(
        data["bits"], data["exact_epoc"], marker="o", label="Exact metric center"
    )
    plt.plot(
        data["bits"],
        data["farthest_first_epoc"],
        marker="s",
        linestyle="--",
        label="Farthest-first",
    )
    checked = data.dropna(subset=["general_milp_epoc"])
    plt.scatter(
        checked["bits"],
        checked["general_milp_epoc"],
        marker="x",
        s=42,
        label="General protocol MILP",
    )
    plt.xlabel("Handshake budget (bits)")
    plt.ylabel("Worst-case regret (EPoC)")
    plt.xticks(sorted(data["bits"].unique()))
    plt.ylim(bottom=-0.02)
    plt.legend(frameon=False, fontsize=8)
    save_both("grid_map_alignment")


def plot_dictionary_ambiguity() -> None:
    data = pd.read_csv(RESULTS / "dictionary_ambiguity.csv")
    plt.figure(figsize=(4.7, 3.2))
    plt.plot(
        data["bits"], data["nominal_epoc"], marker="o", label="Nominal (in model)"
    )
    plt.plot(
        data["bits"],
        data["best_nominal_optimum_on_ambiguity"],
        marker="s",
        linestyle="--",
        label="Best nominal optimum",
    )
    plt.plot(
        data["bits"], data["robust_epoc"], marker="^", label="Robust design"
    )
    plt.xlabel("Handshake budget (bits)")
    plt.ylabel("Worst-case regret")
    plt.xticks(sorted(data["bits"].unique()))
    plt.ylim(bottom=-0.02)
    plt.legend(frameon=False, fontsize=8)
    save_both("dictionary_ambiguity")


def plot_random_set_systems() -> None:
    data = pd.read_csv(RESULTS / "random_set_systems.csv")
    grouped = data.groupby("set_size").agg(
        pairwise=("pairwise_graph_messages", "mean"),
        exact=("exact_messages", "mean"),
        greedy=("greedy_messages", "mean"),
    )
    plt.figure(figsize=(4.7, 3.2))
    plt.plot(
        grouped.index,
        grouped["pairwise"],
        marker="^",
        linestyle="--",
        label="Pairwise graph",
    )
    plt.plot(grouped.index, grouped["exact"], marker="o", label="Exact")
    plt.plot(grouped.index, grouped["greedy"], marker="s", label="Greedy")
    plt.xlabel("Acceptable receiver actions per sender type")
    plt.ylabel("Messages")
    plt.legend(frameon=False, fontsize=8)
    save_both("random_set_systems")


def plot_interval_scaling() -> None:
    data = pd.read_csv(RESULTS / "interval_scaling.csv")
    plt.figure(figsize=(4.7, 3.2))
    plt.plot(data["num_types"], data["mean_seconds"], marker="o")
    plt.xscale("log")
    plt.yscale("log")
    plt.xlabel("Sender types (intervals)")
    plt.ylabel("Greedy solve time (seconds)")
    save_both("interval_scaling")


def main() -> None:
    plot_projective_gap()
    plot_lever_frontier()
    plot_grid_map_alignment()
    plot_dictionary_ambiguity()
    plot_random_set_systems()
    plot_interval_scaling()


if __name__ == "__main__":
    main()
