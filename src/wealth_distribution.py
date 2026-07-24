from __future__ import annotations

import csv
import math
import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/wealth-distribution-matplotlib")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUTPUTS = ROOT / "outputs"
ADULTS_2021 = 5_298_500_000
WEALTH_2021_BN = 463_600
ADULTS_2024 = 3_808_000_000
WEALTH_2024_BN = 470_510
MILLIONAIRE_WEALTH_2024_BN = 226_470
BAR_COLOR = "#3274A1"
ESTIMATE_COLOR = "#8DB9D5"

WEALTH_TIER_NAMES = {
    "$1m–$5m": "Millionaire",
    "$5m–$1b": "Multimillionaire",
    "$1m–$10m": "Millionaire",
    "$10m–$100m": "Decamillionaire",
    "$100m–$1b": "Centimillionaire",
    "$1b–$10b": "Billionaire",
    "$10b–$100b": "Decabillionaire",
    "$100b–$1t": "Centibillionaire",
}


def wealth_band_label(label: str) -> str:
    escaped_label = label.replace("$", r"\$")
    tier_name = WEALTH_TIER_NAMES.get(label)
    return f"{escaped_label}\n{tier_name}" if tier_name else escaped_label


def style_bar_axis(ax, show_grid: bool = True) -> None:
    ax.set_axisbelow(True)
    if show_grid:
        ax.grid(axis="y", color="#D9DEE3", linewidth=0.8)
    else:
        ax.grid(False)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


def hide_y_ticks_and_grid(ax) -> None:
    ax.tick_params(axis="y", which="both", left=False, labelleft=False)
    ax.grid(False)


def load_rows(year: int = 2021) -> list[dict]:
    with (DATA / f"decade_bands_{year}.csv").open(newline="", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))
    if len(rows) != 8:
        raise ValueError("Expected eight decade-wide wealth bands")
    for row in rows:
        row["lower_usd"] = float(row["lower_usd"])
        row["upper_usd"] = float(row["upper_usd"])
        row["count"] = float(row["count"])
        if row["measurement_year"] != str(year) or min(row["lower_usd"], row["count"]) <= 0:
            raise ValueError(f"Values must be positive and measured in {year}")
        if row["upper_usd"] / row["lower_usd"] != 10:
            raise ValueError("Every wealth band must span exactly one decade")
    return rows


def log_correlation(rows: list[dict]) -> float:
    x = [math.log10(math.sqrt(row["lower_usd"] * row["upper_usd"])) for row in rows]
    y = [math.log10(row["count"]) for row in rows]
    x_mean, y_mean = sum(x) / len(x), sum(y) / len(y)
    numerator = sum((a - x_mean) * (b - y_mean) for a, b in zip(x, y))
    denominator = math.sqrt(sum((a - x_mean) ** 2 for a in x) * sum((b - y_mean) ** 2 for b in y))
    return numerator / denominator


def human_count(value: float) -> str:
    for scale, suffix in ((1e9, "B"), (1e6, "M"), (1e3, "K")):
        if value >= scale:
            return f"{value / scale:.3g}{suffix}"
    return f"{value:.3g}"


def percentage(value: float) -> str:
    if value >= 1:
        decimals = 2
    elif value >= 0.01:
        decimals = 4
    elif value >= 0.001:
        decimals = 5
    else:
        decimals = 9
    return f"{value:.{decimals}f}".rstrip("0").rstrip(".") + "%"


def prevalence(count: float, total: float) -> str:
    return f"1 in {human_count(total / count)}"


def load_paired_rows() -> list[dict]:
    with (DATA / "paired_shares_2021.csv").open(newline="", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))
    for row in rows:
        for field in ("reported_count", "reconciled_count", "adult_share_pct", "total_wealth_bn", "wealth_share_pct"):
            row[field] = float(row[field])

    if not math.isclose(sum(row["adult_share_pct"] for row in rows), 100, abs_tol=1e-9):
        raise ValueError("2021 adult shares do not reconcile to 100%")
    if not math.isclose(sum(row["reconciled_count"] for row in rows), ADULTS_2021, abs_tol=1):
        raise ValueError("2021 adult counts do not reconcile to the global adult total")
    if not math.isclose(sum(row["total_wealth_bn"] for row in rows), WEALTH_2021_BN, abs_tol=1e-6):
        raise ValueError("2021 wealth does not reconcile to the global total")
    return rows


def load_paired_2024_wealth() -> list[dict]:
    with (DATA / "paired_shares_2024.csv").open(newline="", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))
    for row in rows:
        for field in ("start_index", "span"):
            row[field] = int(row[field])
        row["total_wealth_bn"] = float(row["total_wealth_bn"])
        row["wealth_share_pct"] = row["total_wealth_bn"] / WEALTH_2024_BN * 100
    if not math.isclose(sum(row["total_wealth_bn"] for row in rows), WEALTH_2024_BN, abs_tol=1e-6):
        raise ValueError("2024 wealth bands do not reconcile to the UBS total")
    estimates = estimate_decade_wealth_2024(sum(row["total_wealth_bn"] for row in rows if row["source"] == "Forbes"))
    modelled_rows = [row for row in rows if row["source"] == "Modelled estimate"]
    if any(not math.isclose(row["total_wealth_bn"], estimate, abs_tol=1e-3) for row, estimate in zip(modelled_rows, estimates)):
        raise ValueError("2024 modelled wealth bands do not match the documented estimate")
    return rows


def estimate_decade_wealth_2024(billionaire_wealth_bn: float) -> list[float]:
    thresholds = (
        (1e6, 1e7, 60_000_000, 2_341_378),
        (1e7, 1e8, 2_341_378, 104_060),
        (1e8, 1e9, 104_060, 2_781),
    )
    raw_totals = []
    for lower, upper, lower_count, upper_count in thresholds:
        alpha = math.log(lower_count / upper_count) / math.log(upper / lower)
        total_usd = (
            alpha
            * lower_count
            * lower**alpha
            * (upper ** (1 - alpha) - lower ** (1 - alpha))
            / (1 - alpha)
        )
        raw_totals.append(total_usd / 1e9)
    scale = (MILLIONAIRE_WEALTH_2024_BN - billionaire_wealth_bn) / sum(raw_totals)
    return [total * scale for total in raw_totals]


def load_population_rows_2024() -> list[dict]:
    return [
        {"label": "<$10k", "count": 1_550_000_000, "source": "UBS"},
        *load_rows(2024),
    ]


def plot_paired_shares(population_log: bool = True) -> None:
    rows = load_paired_rows()

    labels = [wealth_band_label(row["label"]) for row in rows]
    fig, (population_ax, wealth_ax) = plt.subplots(2, 1, figsize=(12, 9), sharex=True)

    population_values = [row["reconciled_count"] if population_log else row["reconciled_count"] / 1e9 for row in rows]
    population_bars = population_ax.bar(labels, population_values, color=BAR_COLOR)
    if population_log:
        population_ax.set_yscale("log")
        population_ax.set_ylim(5, 60_000_000_000)
        population_ax.set_ylabel("Adults (log scale)")
    else:
        population_ax.set_ylim(0, max(population_values) * 1.16)
        population_ax.set_ylabel("Adults (billions, linear scale)")
    style_bar_axis(population_ax)
    if not population_log:
        hide_y_ticks_and_grid(population_ax)
    population_ax.set_title("How many adults are in each band?", loc="left", fontsize=11, weight="bold")
    population_ax.tick_params(axis="x", labelbottom=True, rotation=0, labelsize=8)

    wealth_bars = wealth_ax.bar(labels, [row["wealth_share_pct"] for row in rows], color=BAR_COLOR)
    wealth_ax.set_ylabel("Share of global wealth (%)")
    wealth_ax.set_ylim(0, 42)
    style_bar_axis(wealth_ax)
    hide_y_ticks_and_grid(wealth_ax)
    wealth_ax.set_title("How much global wealth do they own?", loc="left", y=1.04, fontsize=11, weight="bold")
    wealth_ax.tick_params(axis="x", rotation=0, labelsize=8)

    for index, (bar, row, value) in enumerate(zip(population_bars, rows, population_values)):
        frequency = (
            prevalence(row["reconciled_count"], ADULTS_2021)
            if index >= 4
            else percentage(row["adult_share_pct"])
        )
        label = f"{human_count(row['reported_count'])}\n({frequency})"
        if population_log or index < 3:
            label_y = value * 1.25 if population_log else value + max(population_values) * 0.025
            population_ax.text(bar.get_x() + bar.get_width() / 2, label_y, label, ha="center", va="bottom", fontsize=8)
        else:
            population_ax.text(
                bar.get_x() + bar.get_width() / 2,
                max(population_values) * 0.02,
                label,
                ha="center",
                va="bottom",
                fontsize=7,
            )
    for index, (left, right) in enumerate(zip(rows, rows[1:])):
        population_ax.text(
            index + 0.5,
            -0.18,
            f"{left['reconciled_count'] / right['reconciled_count']:.1f}× less",
            transform=population_ax.get_xaxis_transform(),
            ha="center",
            va="center",
            color="#555555",
            fontsize=7,
        )
    for bar, row in zip(wealth_bars, rows):
        value = row["wealth_share_pct"]
        wealth_ax.text(bar.get_x() + bar.get_width() / 2, value + 0.6, f"{value:.2f}%", ha="center", va="bottom", fontsize=8)

    fig.suptitle("Adult population and wealth share by net-wealth band, 2021", x=0.04, y=0.955, ha="left", weight="bold", fontsize=16)
    fig.text(0.04, 0.13, "Sources: Credit Suisse Global Wealth Databook 2022 (broad totals);", fontsize=8.2)
    fig.text(0.04, 0.103, r"World Inequality Report 2022, Table 7.1 (\$1m+ splits).", fontsize=8.2)
    fig.text(0.04, 0.076, r"All bands sum to 5.2985B adults and \$463.6T (100% each). Children are excluded.", fontsize=8.2)
    fig.subplots_adjust(left=0.075, right=0.995, top=0.885, bottom=0.22, hspace=0.46)

    suffix = "" if population_log else "_linear"
    fig.savefig(OUTPUTS / f"population_vs_wealth_share_2021{suffix}.png", dpi=300, bbox_inches="tight", pad_inches=0.04)
    plt.close(fig)


def plot_paired_shares_2024(population_log: bool = True) -> None:
    population_rows = load_population_rows_2024()
    wealth_rows = load_paired_2024_wealth()
    if not math.isclose(sum(row["count"] for row in population_rows), ADULTS_2024, abs_tol=1):
        raise ValueError("2024 adult bands do not reconcile to the UBS covered population")

    labels = [wealth_band_label(row["label"]) for row in population_rows]
    x = list(range(len(population_rows)))
    fig, (population_ax, wealth_ax) = plt.subplots(2, 1, figsize=(12, 9))

    population_values = [row["count"] if population_log else row["count"] / 1e9 for row in population_rows]
    population_bars = population_ax.bar(x, population_values, color=BAR_COLOR)
    if population_log:
        population_ax.set_yscale("log")
        population_ax.set_ylim(5, 60_000_000_000)
        population_ax.set_ylabel("Adults (log scale)")
    else:
        population_ax.set_ylim(0, max(population_values) * 1.16)
        population_ax.set_ylabel("Adults (billions, linear scale)")
    population_ax.set_title("How many adults are in each band?", loc="left", fontsize=11, weight="bold")
    population_ax.set_xticks(x, labels)
    population_ax.tick_params(axis="x", labelbottom=True, rotation=0, labelsize=8)
    style_bar_axis(population_ax)
    if not population_log:
        hide_y_ticks_and_grid(population_ax)

    for index, (bar, row, value) in enumerate(zip(population_bars, population_rows, population_values)):
        share = row["count"] / ADULTS_2024 * 100
        frequency = prevalence(row["count"], ADULTS_2024) if index >= 4 else percentage(share)
        label = f"{human_count(row['count'])}\n({frequency})"
        if population_log or index < 3:
            label_y = value * 1.25 if population_log else value + max(population_values) * 0.025
            population_ax.text(bar.get_x() + bar.get_width() / 2, label_y, label, ha="center", va="bottom", fontsize=8)
        else:
            population_ax.text(
                bar.get_x() + bar.get_width() / 2,
                max(population_values) * 0.02,
                label,
                ha="center",
                va="bottom",
                fontsize=7,
            )
    for index, (left, right) in enumerate(zip(population_rows, population_rows[1:])):
        population_ax.text(
            index + 0.5,
            -0.18,
            f"{left['count'] / right['count']:.1f}× less",
            transform=population_ax.get_xaxis_transform(),
            ha="center",
            va="center",
            color="#555555",
            fontsize=7,
        )

    wealth_bars = []
    wealth_centers = []
    for row in wealth_rows:
        width = 0.8
        center = row["start_index"] + (row["span"] - 1) / 2
        wealth_centers.append(center)
        color = ESTIMATE_COLOR if row["source"] == "Modelled estimate" else BAR_COLOR
        wealth_bars.append(
            wealth_ax.bar(center, row["wealth_share_pct"], width=width, color=color)[0]
        )

    wealth_ax.set_ylabel("Share of global wealth (%)")
    wealth_ax.set_ylim(0, 50)
    wealth_ax.set_xlim(-0.5, 8.5)
    wealth_ax.set_title("How much global wealth do they own?", loc="left", fontsize=11, weight="bold")
    wealth_ax.set_xticks(wealth_centers, [wealth_band_label(row["label"]) for row in wealth_rows])
    wealth_ax.tick_params(axis="x", rotation=0, labelsize=8)
    style_bar_axis(wealth_ax)
    hide_y_ticks_and_grid(wealth_ax)
    wealth_ax.legend(
        handles=(
            Patch(facecolor=BAR_COLOR, label="Reported"),
            Patch(facecolor=ESTIMATE_COLOR, label="Modelled estimate"),
        ),
        frameon=False,
        loc="upper right",
        fontsize=8,
    )
    for bar, row in zip(wealth_bars, wealth_rows):
        value = row["wealth_share_pct"]
        wealth_ax.text(bar.get_x() + bar.get_width() / 2, value + 0.6, f"{value:.2f}%", ha="center", va="bottom", fontsize=8)

    fig.suptitle("Adult population and wealth share by net-wealth band, 2024", x=0.055, y=0.955, ha="left", weight="bold", fontsize=16)
    fig.text(0.055, 0.13, "Sources: UBS (broad totals), Knight Frank (wealth-threshold counts), and Forbes (billionaire wealth).", fontsize=8.2)
    fig.text(0.055, 0.103, r"\$1m–\$1b decade-band wealth is modelled from published 2024 counts, then calibrated to the UBS total.", fontsize=8.2)
    fig.text(0.055, 0.076, "Billionaire-band wealth is summed directly from the Forbes 2024 annual list, valued 8 March 2024.", fontsize=8.2)
    fig.subplots_adjust(left=0.085, right=0.995, top=0.885, bottom=0.22, hspace=0.43)

    suffix = "" if population_log else "_linear"
    fig.savefig(OUTPUTS / f"population_vs_wealth_share_2024{suffix}.png", dpi=300, bbox_inches="tight", pad_inches=0.04)
    plt.close(fig)


def plot_wealth_population_ratio(rows: list[dict], year: int = 2021) -> None:
    labels = [wealth_band_label(row["label"]) for row in rows]
    multiples = [row["wealth_share_pct"] / row["adult_share_pct"] for row in rows]
    fig, ax = plt.subplots(figsize=(11, 5.8))
    colors = [ESTIMATE_COLOR if row.get("estimated") else BAR_COLOR for row in rows]
    bars = ax.bar(labels, multiples, color=colors)

    ax.set_yscale("log")
    ax.set_ylim(0.01, 5_000_000)
    ticks = (0.01, 0.1, 1, 10, 100, 1_000, 10_000, 100_000, 1_000_000)
    tick_labels = (
        r"$10^{-2}$× avg",
        r"$10^{-1}$× avg",
        "Average",
        r"$10^{1}$× avg",
        r"$10^{2}$× avg",
        r"$10^{3}$× avg",
        r"$10^{4}$× avg",
        r"$10^{5}$× avg",
        r"$10^{6}$× avg",
    )
    ax.set_yticks(ticks, tick_labels)
    ax.tick_params(axis="x", rotation=0, labelsize=8)
    style_bar_axis(ax)
    if year == 2024:
        ax.legend(
            handles=(
                Patch(facecolor=BAR_COLOR, label="Reported"),
                Patch(facecolor=ESTIMATE_COLOR, label="Modelled estimate"),
            ),
            frameon=False,
            loc="upper left",
            fontsize=8,
        )
    for bar, multiple in zip(bars, multiples):
        if multiple < 1:
            below = 1 / multiple
            label = f"{below:.2g}× below\naverage"
        else:
            label = f"{compact_multiple(multiple)[:-1]}×\naverage"
        ax.text(bar.get_x() + bar.get_width() / 2, multiple * 1.35, label, ha="center", va="bottom", fontsize=8)
    for index, (left, right) in enumerate(zip(multiples, multiples[1:])):
        ax.text(
            index + 0.5,
            -0.16,
            f"{right / left:.1f}× more",
            transform=ax.get_xaxis_transform(),
            ha="center",
            va="center",
            color="#555555",
            fontsize=7,
        )

    fig.suptitle(
        f"Average wealth by wealth band compared with the worldwide average, {year}",
        x=0.07,
        y=0.97,
        ha="left",
        weight="bold",
        fontsize=15,
    )
    fig.text(0.07, 0.91, "Values are multiples of worldwide average wealth per adult · logarithmic scale.")
    source = (
        "Sources: Credit Suisse Global Wealth Databook 2022; World Inequality Report 2022, Table 7.1."
        if year == 2021
        else "Sources: UBS, Knight Frank and Forbes. Pale bars use the modelled 2024 decade-band wealth estimates."
    )
    fig.text(0.07, 0.085, source, fontsize=8)
    fig.subplots_adjust(left=0.10, right=0.99, top=0.84, bottom=0.24)
    fig.savefig(OUTPUTS / f"wealth_population_ratio_{year}.png", dpi=300, bbox_inches="tight", pad_inches=0.04)
    plt.close(fig)


def plot_wealth_population_ratio_2024() -> None:
    plot_wealth_population_ratio(ratio_rows_2024(), year=2024)


def ratio_rows_2024() -> list[dict]:
    population_rows = load_population_rows_2024()
    wealth_by_label = {row["label"]: row for row in load_paired_2024_wealth()}
    return [
        {
            "label": row["label"],
            "adult_share_pct": row["count"] / ADULTS_2024 * 100,
            "wealth_share_pct": wealth_by_label[row["label"]]["wealth_share_pct"],
            "multiple": wealth_by_label[row["label"]]["wealth_share_pct"]
            / (row["count"] / ADULTS_2024 * 100),
            "estimated": wealth_by_label[row["label"]]["source"] == "Modelled estimate",
        }
        for row in population_rows
    ]


def compact_multiple(value: float) -> str:
    if value >= 1_000_000:
        return f"{value / 1_000_000:.2g}M×"
    if value >= 1_000:
        return f"{value / 1_000:.3g}K×"
    if value >= 10:
        return f"{value:.0f}×"
    return f"{value:.2g}×"


def plot_wealth_population_ratio_comparison() -> None:
    rows_2021 = load_paired_rows()
    rows_2024 = ratio_rows_2024()
    multiples_2021 = {
        row["label"]: row["wealth_share_pct"] / row["adult_share_pct"]
        for row in rows_2021
    }

    fig, ax = plt.subplots(figsize=(11, 7.2))
    y_positions = list(range(len(rows_2024)))
    for y, row in zip(y_positions, rows_2024):
        old, new = multiples_2021[row["label"]], row["multiple"]
        ax.plot((old, new), (y, y), color="#C7CDD2", linewidth=2, zorder=1)
        ax.scatter(old, y, s=52, color="#8A9197", zorder=2)
        ax.scatter(
            new,
            y,
            s=68,
            facecolor="white" if row["estimated"] else BAR_COLOR,
            edgecolor=ESTIMATE_COLOR if row["estimated"] else BAR_COLOR,
            linewidth=2,
            zorder=3,
        )
        ax.annotate(
            compact_multiple(old),
            (old, y),
            xytext=(0, 10),
            textcoords="offset points",
            ha="center",
            va="bottom",
            color="#6F767C",
            fontsize=7.5,
        )
        ax.annotate(
            compact_multiple(new),
            (new, y),
            xytext=(0, -11),
            textcoords="offset points",
            ha="center",
            va="top",
            color=ESTIMATE_COLOR if row["estimated"] else BAR_COLOR,
            fontsize=7.5,
            weight="bold",
        )

    ax.set_xscale("log")
    ax.set_xlim(0.008, 2_500_000)
    ticks = (0.01, 0.1, 1, 10, 100, 1_000, 10_000, 100_000, 1_000_000)
    ax.set_xticks(ticks, ("1/100×", "1/10×", "1×", "10×", "100×", "1K×", "10K×", "100K×", "1M×"))
    ax.set_yticks(y_positions, [wealth_band_label(row["label"]) for row in rows_2024])
    ax.tick_params(axis="y", length=0, labelsize=9, pad=8)
    ax.tick_params(axis="x", labelsize=8)
    ax.axvline(1, color="#4D5358", linewidth=1.2)
    ax.grid(axis="x", which="major", color="#E4E8EB", linewidth=0.8)
    ax.set_axisbelow(True)
    for spine in ("top", "right", "left"):
        ax.spines[spine].set_visible(False)

    legend = (
        Line2D([], [], marker="o", linestyle="none", color="#8A9197", label="2021", markersize=6),
        Line2D([], [], marker="o", linestyle="none", color=BAR_COLOR, label="2024", markersize=7),
        Line2D(
            [], [], marker="o", linestyle="none", markerfacecolor="white",
            markeredgecolor=ESTIMATE_COLOR, markeredgewidth=2,
            label="2024 modelled estimate", markersize=7,
        ),
    )
    ax.legend(handles=legend, frameon=False, ncol=3, loc="lower right", bbox_to_anchor=(1, 1.015), fontsize=8)

    fig.suptitle(
        "Average wealth per adult in each band, relative to the global average",
        x=0.11,
        y=0.975,
        ha="left",
        weight="bold",
        fontsize=15,
    )
    fig.text(0.11, 0.915, "A value of 1× means the band’s average equals the worldwide average. Logarithmic scale.", fontsize=9)
    fig.text(
        0.11,
        0.06,
        "Sources: Credit Suisse and World Inequality Report (2021); UBS, Knight Frank and Forbes (2024).",
        fontsize=8,
    )
    fig.text(0.11, 0.038, "Hollow 2024 points use modelled wealth estimates calibrated to the UBS total.", fontsize=8)
    fig.subplots_adjust(left=0.18, right=0.93, top=0.86, bottom=0.15)
    fig.savefig(
        OUTPUTS / "wealth_population_ratio_2021_vs_2024.png",
        dpi=300,
        bbox_inches="tight",
        pad_inches=0.04,
    )
    plt.close(fig)


def write_output(rows: list[dict], year: int) -> None:
    fields = ["lower_usd", "upper_usd", "label", "count", "source"]
    with (OUTPUTS / f"decade_bands_{year}.csv").open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    OUTPUTS.mkdir(exist_ok=True)
    for year in (2021, 2024):
        rows = load_rows(year)
        write_output(rows, year)
        print(f"Wrote {year} data (Pearson r={log_correlation(rows):.3f})")
    plot_paired_shares()
    plot_paired_shares(population_log=False)
    plot_paired_shares_2024()
    plot_paired_shares_2024(population_log=False)
    paired_rows = load_paired_rows()
    plot_wealth_population_ratio(paired_rows)
    plot_wealth_population_ratio_2024()
    plot_wealth_population_ratio_comparison()
    print("Wrote paired 2021/2024 and wealth-to-population ratio charts")


if __name__ == "__main__":
    main()
