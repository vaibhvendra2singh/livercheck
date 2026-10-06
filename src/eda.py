"""
LiverCheck – Exploratory Data Analysis (EDA)
=============================================
Generates publication-quality figures saved to ./outputs/figures/.
Palette: strictly black, white, and grays (no colour).

Run:
    python3 src/eda.py
"""

import os
import sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")          # non-interactive backend for server / script
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRAIN_CSV = os.path.join(BASE_DIR, "train.csv")
FIG_DIR   = os.path.join(BASE_DIR, "outputs", "figures")
os.makedirs(FIG_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# Global style – black / white / gray only
# ---------------------------------------------------------------------------
plt.rcParams.update({
    "font.family":       "DejaVu Sans",
    "font.size":         11,
    "axes.spines.top":   False,
    "axes.spines.right": False,
    "axes.edgecolor":    "#333333",
    "axes.labelcolor":   "#111111",
    "xtick.color":       "#333333",
    "ytick.color":       "#333333",
    "figure.facecolor":  "white",
    "axes.facecolor":    "white",
    "grid.color":        "#dddddd",
    "grid.linewidth":    0.6,
    "savefig.dpi":       150,
    "savefig.bbox":      "tight",
})


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------
def save(fig, name):
    """Save figure to FIG_DIR."""
    path = os.path.join(FIG_DIR, name)
    fig.savefig(path)
    plt.close(fig)
    print(f"  Saved -> {path}")


# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------
print("=" * 60)
print("LiverCheck - EDA")
print("=" * 60)

df = pd.read_csv(TRAIN_CSV)
print(f"\nTraining data shape: {df.shape}")
print(df.dtypes)

# Feature groups (never use leakage columns)
TARGETS  = ["fibrosis_8", "fibrosis_12", "steatosis"]
CORE_FEATURES = ["RIDAGEYR", "RIAGENDR", "BMXBMI", "BMXWAIST",
                 "LBXSATSI", "LBXSASSI", "LBXSGTSI", "LBXPLTSI"]
EXTENDED_FEATURES = CORE_FEATURES + ["LBDTRSI", "LBXGLU"]

FEAT_LABELS = {
    "RIDAGEYR":  "Age (years)",
    "RIAGENDR":  "Sex (1=M, 2=F)",
    "BMXBMI":    "BMI",
    "BMXWAIST":  "Waist (cm)",
    "LBXSATSI":  "ALT (U/L)",
    "LBXSASSI":  "AST (U/L)",
    "LBXSGTSI":  "GGT (U/L)",
    "LBXPLTSI":  "Platelets (10^3/uL)",
    "LBDTRSI":   "Triglycerides (mmol/L)",
    "LBXGLU":    "Glucose (mg/dL)",
}

# ---------------------------------------------------------------------------
# 1. Missingness
# ---------------------------------------------------------------------------
print("\n--- Missingness ---")
miss = df[EXTENDED_FEATURES + TARGETS].isnull().mean().sort_values(ascending=False)
print(miss.to_string())

fig, ax = plt.subplots(figsize=(8, 4))
ax.barh(
    [FEAT_LABELS.get(c, c) for c in miss.index],
    miss.values * 100,
    color="#555555",
    edgecolor="white",
    linewidth=0.4,
)
ax.set_xlabel("Missing (%)")
ax.set_title("Missingness by variable (training data)")
ax.axvline(50, color="#aaaaaa", lw=1, linestyle="--")
ax.xaxis.set_major_formatter(mticker.PercentFormatter())
fig.tight_layout()
save(fig, "01_missingness.png")

# ---------------------------------------------------------------------------
# 2. Class balance
# ---------------------------------------------------------------------------
print("\n--- Class balance ---")
for tgt in TARGETS:
    vc = df[tgt].value_counts()
    pct = df[tgt].mean() * 100
    print(f"  {tgt}: positive = {vc.get(1, 0)} ({pct:.1f}%)")

fig, axes = plt.subplots(1, 3, figsize=(11, 4))
for ax, tgt in zip(axes, TARGETS):
    counts = df[tgt].value_counts().sort_index()
    labels = ["Negative", "Positive"]
    ax.bar(labels, counts.values, color=["#dddddd", "#333333"],
           edgecolor="#555555", linewidth=0.7)
    ax.set_title(tgt.replace("_", " ").title(), fontsize=11)
    ax.set_ylabel("Count")
    for i, v in enumerate(counts.values):
        ax.text(i, v + 20, str(v), ha="center", fontsize=9)
fig.suptitle("Class distribution - training data", y=1.02)
fig.tight_layout()
save(fig, "02_class_balance.png")

# ---------------------------------------------------------------------------
# 3. Feature distributions (violin)
# ---------------------------------------------------------------------------
print("\n--- Feature distributions ---")
fig, axes = plt.subplots(2, 5, figsize=(18, 8))
axes = axes.flatten()

for i, col in enumerate(EXTENDED_FEATURES):
    ax = axes[i]
    data_col = df[col].dropna()
    parts = ax.violinplot(data_col, positions=[0], showmedians=True, bw_method=0.3)
    for pc in parts["bodies"]:
        pc.set_facecolor("#aaaaaa")
        pc.set_edgecolor("#333333")
        pc.set_alpha(0.8)
    for key in ["cbars", "cmins", "cmaxes", "cmedians"]:
        if key in parts:
            parts[key].set_color("#333333")
    ax.set_title(FEAT_LABELS.get(col, col), fontsize=9)
    ax.set_xticks([])
    ax.grid(axis="y", linewidth=0.5)

for j in range(len(EXTENDED_FEATURES), len(axes)):
    axes[j].set_visible(False)

fig.suptitle("Feature distributions (training data)", y=1.01)
fig.tight_layout()
save(fig, "03_distributions.png")

# ---------------------------------------------------------------------------
# 4. Feature distributions by fibrosis_8 status
# ---------------------------------------------------------------------------
fig, axes = plt.subplots(2, 4, figsize=(16, 8))
axes = axes.flatten()

for i, col in enumerate(CORE_FEATURES):
    ax = axes[i]
    groups = [df.loc[df["fibrosis_8"] == 0, col].dropna(),
              df.loc[df["fibrosis_8"] == 1, col].dropna()]
    bp = ax.boxplot(groups, patch_artist=True,
                    medianprops={"color": "black", "linewidth": 2})
    bp["boxes"][0].set_facecolor("#dddddd")
    bp["boxes"][1].set_facecolor("#555555")
    ax.set_xticklabels(["No fibrosis", "Fibrosis"], fontsize=9)
    ax.set_title(FEAT_LABELS.get(col, col), fontsize=9)
    ax.grid(axis="y", linewidth=0.5)

fig.suptitle("Features by fibrosis_8 status (training data)", y=1.01)
fig.tight_layout()
save(fig, "04_feature_by_target.png")

# ---------------------------------------------------------------------------
# 5. Correlation heatmap
# ---------------------------------------------------------------------------
print("\n--- Correlation heatmap ---")
corr_cols = EXTENDED_FEATURES + TARGETS
corr_df   = df[corr_cols].copy()
corr_df.rename(columns=FEAT_LABELS, inplace=True)
corr = corr_df.corr(numeric_only=True)

fig, ax = plt.subplots(figsize=(10, 8))
im = ax.imshow(corr.values, cmap="Greys", vmin=-1, vmax=1, aspect="auto")
labels = corr.columns.tolist()
ax.set_xticks(range(len(labels)))
ax.set_yticks(range(len(labels)))
ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=8)
ax.set_yticklabels(labels, fontsize=8)

for r in range(len(labels)):
    for c in range(len(labels)):
        val = corr.values[r, c]
        color = "white" if abs(val) > 0.6 else "black"
        ax.text(c, r, f"{val:.2f}", ha="center", va="center",
                fontsize=6, color=color)

plt.colorbar(im, ax=ax, fraction=0.03, pad=0.02, label="Pearson r")
ax.set_title("Correlation heatmap (training data)")
fig.tight_layout()
save(fig, "05_correlation_heatmap.png")

# ---------------------------------------------------------------------------
# 6. FIB-4 distribution by fibrosis status
# ---------------------------------------------------------------------------
print("\n--- FIB-4 distribution ---")
fib4_data = df[["FIB4", "fibrosis_8"]].dropna()
fig, ax = plt.subplots(figsize=(8, 4))
ax.hist(fib4_data.loc[fib4_data["fibrosis_8"] == 0, "FIB4"],
        bins=60, color="#cccccc", edgecolor="white", alpha=0.8,
        label="No fibrosis", density=True)
ax.hist(fib4_data.loc[fib4_data["fibrosis_8"] == 1, "FIB4"],
        bins=60, color="#333333", edgecolor="white", alpha=0.8,
        label="Fibrosis (>=8 kPa)", density=True)
ax.axvline(1.3, color="black", lw=1.5, linestyle="--", label="FIB-4=1.3 cutoff")
ax.axvline(2.67, color="black", lw=1.5, linestyle=":",  label="FIB-4=2.67 cutoff")
ax.set_xlabel("FIB-4 score")
ax.set_ylabel("Density")
ax.set_xlim(0, 8)
ax.set_title("FIB-4 distribution by fibrosis status (training data)")
ax.legend()
fig.tight_layout()
save(fig, "06_fib4_distribution.png")

print("\nEDA complete. All figures saved to:", FIG_DIR)
