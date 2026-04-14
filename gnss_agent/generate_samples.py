"""
Generate realistic sample GNSS engineering visuals for the multimodal agent.

Produces three artifacts:
  1. Sky plot  (satellite polar plot)
  2. DOP table (dilution of precision over time)
  3. C/N0 bar chart (signal strength per satellite)

Ground-truth data is also saved as JSON so the extractor can be evaluated.

Enhanced with scientific-visualization best practices:
  - Colorblind-safe palette (Okabe-Ito inspired)
  - Clean typography and spines
  - High-resolution output (300 DPI)
  - Consistent styling across all figures
"""
import json
import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use("Agg")

from config import SAMPLES_DIR

# ── Publication-quality style setup ───────────────────────────────────────────
plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "DejaVu Sans", "Helvetica"],
    "font.size": 10,
    "axes.titlesize": 13,
    "axes.labelsize": 11,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "legend.fontsize": 9,
    "figure.dpi": 150,
    "savefig.dpi": 300,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.alpha": 0.3,
    "grid.linewidth": 0.5,
})

# ── Colorblind-safe palette (Okabe-Ito inspired) ─────────────────────────────
COLORS = {
    "strong":   "#009E73",   # bluish green (replaces pure green)
    "moderate": "#E69F00",   # orange
    "weak":     "#D55E00",   # vermillion (replaces pure red)
    "header":   "#0072B2",   # blue
    "accent":   "#CC79A7",   # reddish purple
    "text":     "#1a1a2e",   # dark navy
    "grid":     "#CCCCCC",
    "bg_good":  "#d4edda",
    "bg_ok":    "#d1ecf1",
    "bg_warn":  "#fff3cd",
    "bg_bad":   "#f8d7da",
}

# ── Satellite constellation data (simulated GPS + GLONASS mix) ────────────────
# Some satellites are at low elevation to simulate degraded urban conditions.
SATELLITES = [
    {"prn": "G01", "system": "GPS",     "elevation": 72, "azimuth": 45,  "cn0": 47.2},
    {"prn": "G03", "system": "GPS",     "elevation": 55, "azimuth": 120, "cn0": 44.8},
    {"prn": "G07", "system": "GPS",     "elevation": 38, "azimuth": 200, "cn0": 40.1},
    {"prn": "G08", "system": "GPS",     "elevation": 12, "azimuth": 310, "cn0": 25.3},  # low elev
    {"prn": "G10", "system": "GPS",     "elevation": 65, "azimuth": 85,  "cn0": 46.0},
    {"prn": "G14", "system": "GPS",     "elevation": 5,  "azimuth": 170, "cn0": 18.5},  # very low
    {"prn": "G22", "system": "GPS",     "elevation": 48, "azimuth": 290, "cn0": 42.7},
    {"prn": "G31", "system": "GPS",     "elevation": 28, "azimuth": 15,  "cn0": 36.9},
    {"prn": "R02", "system": "GLONASS", "elevation": 60, "azimuth": 150, "cn0": 43.5},
    {"prn": "R08", "system": "GLONASS", "elevation": 8,  "azimuth": 240, "cn0": 21.0},  # low elev
    {"prn": "R15", "system": "GLONASS", "elevation": 42, "azimuth": 330, "cn0": 39.8},
    {"prn": "R17", "system": "GLONASS", "elevation": 70, "azimuth": 60,  "cn0": 45.1},
]

# ── DOP time series (simulated 2-hour window, 15-min epochs) ─────────────────
DOP_EPOCHS = [
    {"time": "08:00", "gdop": 2.1, "pdop": 1.8, "hdop": 1.0, "vdop": 1.5, "tdop": 0.9, "num_sats": 10},
    {"time": "08:15", "gdop": 2.3, "pdop": 2.0, "hdop": 1.1, "vdop": 1.7, "tdop": 1.0, "num_sats": 10},
    {"time": "08:30", "gdop": 3.8, "pdop": 3.4, "hdop": 2.0, "vdop": 2.8, "tdop": 1.5, "num_sats": 8},
    {"time": "08:45", "gdop": 6.5, "pdop": 5.9, "hdop": 3.5, "vdop": 4.8, "tdop": 2.7, "num_sats": 6},  # degraded
    {"time": "09:00", "gdop": 8.2, "pdop": 7.5, "hdop": 4.2, "vdop": 6.2, "tdop": 3.4, "num_sats": 5},  # degraded
    {"time": "09:15", "gdop": 4.1, "pdop": 3.7, "hdop": 2.1, "vdop": 3.0, "tdop": 1.6, "num_sats": 8},
    {"time": "09:30", "gdop": 2.5, "pdop": 2.2, "hdop": 1.2, "vdop": 1.8, "tdop": 1.1, "num_sats": 9},
    {"time": "09:45", "gdop": 1.9, "pdop": 1.6, "hdop": 0.9, "vdop": 1.3, "tdop": 0.8, "num_sats": 11},
]


def generate_sky_plot():
    """Create a publication-quality GNSS satellite sky plot (polar projection)."""
    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw={"projection": "polar"})

    # Convert to radians for polar plot; elevation maps to radius (90 at center, 0 at edge)
    for sat in SATELLITES:
        az_rad = np.radians(sat["azimuth"])
        r = 90 - sat["elevation"]  # invert so zenith is center

        # Colorblind-safe signal strength encoding
        if sat["cn0"] >= 40:
            color, marker = COLORS["strong"], "o"
        elif sat["cn0"] >= 30:
            color, marker = COLORS["moderate"], "s"      # square for moderate
        else:
            color, marker = COLORS["weak"], "^"          # triangle for weak

        # Satellite marker with system-specific edge color
        edge = COLORS["header"] if sat["system"] == "GPS" else COLORS["accent"]
        ax.scatter(az_rad, r, c=color, s=140, zorder=5,
                   edgecolors=edge, linewidth=1.2, marker=marker)
        ax.annotate(f"{sat['prn']}\n{sat['cn0']:.0f}",
                    (az_rad, r), textcoords="offset points", xytext=(8, 5),
                    fontsize=7, fontweight="bold", color=COLORS["text"])

    # Configure polar axes
    ax.set_theta_zero_location("N")
    ax.set_theta_direction(-1)
    ax.set_ylim(0, 90)
    ax.set_yticks([0, 15, 30, 45, 60, 75, 90])
    ax.set_yticklabels(["90\u00b0", "75\u00b0", "60\u00b0", "45\u00b0", "30\u00b0", "15\u00b0", "0\u00b0"],
                       fontsize=7, color=COLORS["text"])
    ax.set_rlabel_position(22.5)
    ax.set_title("GNSS Satellite Sky Plot\nLocation: 39.9\u00b0N, 116.4\u00b0E  |  Time: 08:45 UTC",
                 fontsize=13, fontweight="bold", pad=20, color=COLORS["text"])
    ax.grid(True, alpha=0.3, linewidth=0.5)

    # Elevation mask ring (15 degrees)
    mask_theta = np.linspace(0, 2 * np.pi, 100)
    ax.plot(mask_theta, [75] * 100, ":", color=COLORS["weak"], alpha=0.6, linewidth=1.0)
    ax.annotate("15\u00b0 mask", (np.radians(135), 77), fontsize=7, color=COLORS["weak"], alpha=0.8)

    # Legend
    from matplotlib.lines import Line2D
    legend_elements = [
        Line2D([0], [0], marker="o", color="w", markerfacecolor=COLORS["strong"],
               markersize=10, label="Strong (C/N0 \u2265 40 dBHz)"),
        Line2D([0], [0], marker="s", color="w", markerfacecolor=COLORS["moderate"],
               markersize=10, label="Moderate (30\u201340 dBHz)"),
        Line2D([0], [0], marker="^", color="w", markerfacecolor=COLORS["weak"],
               markersize=10, label="Weak (< 30 dBHz)"),
        Line2D([0], [0], marker="o", color="w", markeredgecolor=COLORS["header"],
               markerfacecolor="white", markersize=10, markeredgewidth=1.5, label="GPS"),
        Line2D([0], [0], marker="o", color="w", markeredgecolor=COLORS["accent"],
               markerfacecolor="white", markersize=10, markeredgewidth=1.5, label="GLONASS"),
    ]
    ax.legend(handles=legend_elements, loc="lower right", bbox_to_anchor=(1.35, -0.08),
              fontsize=8, framealpha=0.9, edgecolor=COLORS["grid"])

    path = os.path.join(SAMPLES_DIR, "sky_plot.png")
    fig.savefig(path, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"  Sky plot saved: {path}")
    return path


def generate_dop_table():
    """Create a publication-quality DOP values table as an image."""
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.axis("off")

    # Table data
    headers = ["Time (UTC)", "GDOP", "PDOP", "HDOP", "VDOP", "TDOP", "Sats", "Quality"]
    rows = []
    cell_colors = []
    for epoch in DOP_EPOCHS:
        gdop = epoch["gdop"]
        if gdop <= 2:
            quality, qcolor = "Excellent", COLORS["bg_good"]
        elif gdop <= 5:
            quality, qcolor = "Good", COLORS["bg_ok"]
        elif gdop <= 10:
            quality, qcolor = "Moderate", COLORS["bg_warn"]
        else:
            quality, qcolor = "Poor", COLORS["bg_bad"]

        row = [epoch["time"], f"{epoch['gdop']:.1f}", f"{epoch['pdop']:.1f}",
               f"{epoch['hdop']:.1f}", f"{epoch['vdop']:.1f}", f"{epoch['tdop']:.1f}",
               str(epoch["num_sats"]), quality]
        rows.append(row)
        cell_colors.append(["white"] * 7 + [qcolor])

    table = ax.table(cellText=rows, colLabels=headers, cellLoc="center", loc="center",
                     cellColours=cell_colors,
                     colColours=[COLORS["header"]] * len(headers))
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1, 1.6)

    # Style header
    for j in range(len(headers)):
        cell = table[0, j]
        cell.set_text_props(color="white", fontweight="bold")
        cell.set_facecolor(COLORS["header"])

    # Bold the degraded rows
    for i, epoch in enumerate(DOP_EPOCHS):
        if epoch["gdop"] > 5:
            for j in range(len(headers)):
                table[i + 1, j].set_text_props(fontweight="bold", color=COLORS["weak"])

    ax.set_title("GNSS Dilution of Precision (DOP) Values\nDate: 2026-04-11  |  Station: BUAA-REF",
                 fontsize=13, fontweight="bold", pad=20, color=COLORS["text"])

    path = os.path.join(SAMPLES_DIR, "dop_table.png")
    fig.savefig(path, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"  DOP table saved: {path}")
    return path


def generate_cn0_chart():
    """Create a publication-quality C/N0 (signal strength) bar chart."""
    fig, ax = plt.subplots(figsize=(10, 5))

    prns = [s["prn"] for s in SATELLITES]
    cn0s = [s["cn0"] for s in SATELLITES]
    systems = [s["system"] for s in SATELLITES]

    # Colorblind-safe colors with hatching to distinguish systems
    colors = []
    hatches = []
    for c, sys in zip(cn0s, systems):
        if c >= 40:
            colors.append(COLORS["strong"])
        elif c >= 30:
            colors.append(COLORS["moderate"])
        else:
            colors.append(COLORS["weak"])
        hatches.append("" if sys == "GPS" else "//")

    bars = ax.bar(prns, cn0s, color=colors, edgecolor=COLORS["text"],
                  linewidth=0.6, width=0.7)

    # Apply hatching for GLONASS
    for bar, hatch in zip(bars, hatches):
        bar.set_hatch(hatch)

    # Value labels on bars
    for bar, val in zip(bars, cn0s):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
                f"{val:.1f}", ha="center", va="bottom", fontsize=8,
                fontweight="bold", color=COLORS["text"])

    # Threshold lines
    ax.axhline(y=40, color=COLORS["strong"], linestyle="--", alpha=0.6, linewidth=1.0,
               label="Strong threshold (40 dBHz)")
    ax.axhline(y=30, color=COLORS["moderate"], linestyle="--", alpha=0.6, linewidth=1.0,
               label="Moderate threshold (30 dBHz)")
    ax.axhline(y=20, color=COLORS["weak"], linestyle="--", alpha=0.6, linewidth=1.0,
               label="Weak threshold (20 dBHz)")

    ax.set_xlabel("Satellite PRN", fontsize=11, color=COLORS["text"])
    ax.set_ylabel("C/N0 (dBHz)", fontsize=11, color=COLORS["text"])
    ax.set_title("GNSS Signal Strength (Carrier-to-Noise Ratio)\nTime: 08:45 UTC  |  Mask Angle: 5\u00b0",
                 fontsize=13, fontweight="bold", color=COLORS["text"])
    ax.set_ylim(0, 55)

    # Combined legend
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor=COLORS["strong"], edgecolor=COLORS["text"], label="Strong (\u226540)"),
        Patch(facecolor=COLORS["moderate"], edgecolor=COLORS["text"], label="Moderate (30\u201340)"),
        Patch(facecolor=COLORS["weak"], edgecolor=COLORS["text"], label="Weak (<30)"),
        Patch(facecolor="white", edgecolor=COLORS["text"], label="GPS"),
        Patch(facecolor="white", edgecolor=COLORS["text"], hatch="//", label="GLONASS"),
    ]
    ax.legend(handles=legend_elements, loc="upper right", fontsize=8,
              framealpha=0.9, edgecolor=COLORS["grid"])
    ax.grid(axis="y", alpha=0.3)

    path = os.path.join(SAMPLES_DIR, "cn0_chart.png")
    fig.savefig(path, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"  C/N0 chart saved: {path}")
    return path


def save_ground_truth():
    """Save the ground-truth data as JSON for evaluation."""
    ground_truth = {
        "satellites": SATELLITES,
        "dop_epochs": DOP_EPOCHS,
        "metadata": {
            "location": {"lat": 39.9, "lon": 116.4},
            "date": "2026-04-11",
            "time": "08:45 UTC",
            "station": "BUAA-REF",
            "mask_angle_deg": 5
        }
    }
    path = os.path.join(SAMPLES_DIR, "ground_truth.json")
    with open(path, "w") as f:
        json.dump(ground_truth, f, indent=2)
    print(f"  Ground truth saved: {path}")
    return path


if __name__ == "__main__":
    os.makedirs(SAMPLES_DIR, exist_ok=True)
    print("Generating GNSS sample visuals (publication-quality)...")
    generate_sky_plot()
    generate_dop_table()
    generate_cn0_chart()
    save_ground_truth()
    print("Done! All samples generated.")
