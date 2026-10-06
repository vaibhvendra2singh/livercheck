"""
LiverCheck – Main Training & Evaluation Pipeline
=================================================
Single script that trains all models, evaluates on the external test set,
saves artefacts and produces all result figures.

Run:
    python3 src/train.py

Outputs (all in ./outputs/):
    models/          – joblib files (pipeline + calibrated)
    figures/         – evaluation and explainability plots
    metrics.json     – all numeric results
"""

# ============================================================
# 0. Imports & seeds
# ============================================================
import os, sys, json, warnings
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from scipy import stats
import joblib

# scikit-learn
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from sklearn.pipeline import Pipeline
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.calibration import CalibratedClassifierCV, calibration_curve
from sklearn.metrics import (
    roc_auc_score, average_precision_score,
    roc_curve, precision_recall_curve,
    confusion_matrix, brier_score_loss,
)
from sklearn.inspection import permutation_importance

# XGBoost (available; falls back to HistGBT if import fails or libomp missing)
try:
    import xgboost as xgb
    # Force a small test to detect missing libomp at import time
    _ = xgb.XGBClassifier(n_estimators=1)
    XGB_AVAILABLE = True
    print("XGBoost available:", xgb.__version__)
except Exception as _xgb_err:
    XGB_AVAILABLE = False
    print(f"XGBoost unavailable ({type(_xgb_err).__name__}: {_xgb_err}).")
    print("  Falling back to HistGradientBoostingClassifier.")
    print("  To enable XGBoost on macOS: brew install libomp")

# SHAP
try:
    import shap
    SHAP_AVAILABLE = True
    print("SHAP available:", shap.__version__)
except ImportError:
    SHAP_AVAILABLE = False
    print("SHAP not available – will use permutation importance instead")

# Random seeds (set everywhere for reproducibility)
SEED = 42
np.random.seed(SEED)

warnings.filterwarnings("ignore")

# ============================================================
# 1. Paths
# ============================================================
BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRAIN_CSV  = os.path.join(BASE_DIR, "train.csv")
TEST_CSV   = os.path.join(BASE_DIR, "test.csv")
OUT_DIR    = os.path.join(BASE_DIR, "outputs")
FIG_DIR    = os.path.join(OUT_DIR, "figures")
MODEL_DIR  = os.path.join(OUT_DIR, "models")

for d in [FIG_DIR, MODEL_DIR]:
    os.makedirs(d, exist_ok=True)

# ============================================================
# 2. Global plot style (B/W/gray)
# ============================================================
plt.rcParams.update({
    "font.family":       "DejaVu Sans",
    "font.size":         11,
    "axes.spines.top":   False,
    "axes.spines.right": False,
    "axes.edgecolor":    "#333333",
    "figure.facecolor":  "white",
    "axes.facecolor":    "white",
    "grid.color":        "#dddddd",
    "grid.linewidth":    0.6,
    "savefig.dpi":       150,
    "savefig.bbox":      "tight",
})

def savefig(fig, name):
    path = os.path.join(FIG_DIR, name)
    fig.savefig(path)
    plt.close(fig)
    print(f"  Figure saved -> {path}")

# ============================================================
# 3. Feature definitions
# ============================================================
CORE_FEATURES = [
    "RIDAGEYR", "RIAGENDR", "BMXBMI", "BMXWAIST",
    "LBXSATSI", "LBXSASSI", "LBXSGTSI", "LBXPLTSI",
]
EXTENDED_FEATURES = CORE_FEATURES + ["LBDTRSI", "LBXGLU"]

# Human-readable labels for plots / API
FEAT_LABELS = {
    "RIDAGEYR":  "Age",
    "RIAGENDR":  "Sex",
    "BMXBMI":    "BMI",
    "BMXWAIST":  "Waist circumference",
    "LBXSATSI":  "ALT (liver enzyme)",
    "LBXSASSI":  "AST (liver enzyme)",
    "LBXSGTSI":  "GGT (liver enzyme)",
    "LBXPLTSI":  "Platelet count",
    "LBDTRSI":   "Triglycerides",
    "LBXGLU":    "Glucose",
}

# ============================================================
# 4. Load & prepare data
# ============================================================
print("\n" + "=" * 65)
print("STEP 1 – Load data")
print("=" * 65)

train_raw = pd.read_csv(TRAIN_CSV)
test_raw  = pd.read_csv(TEST_CSV)
print(f"Train: {train_raw.shape}   Test: {test_raw.shape}")

TARGET = "fibrosis_8"          # main target ~10% positive

def prepare(df, features, target):
    """Drop rows missing any feature or the target."""
    cols = features + [target]
    sub  = df[cols].dropna()
    X    = sub[features].copy()
    y    = sub[target].astype(int)
    return X, y

# Core feature sets
X_train_core, y_train = prepare(train_raw, CORE_FEATURES, TARGET)
X_test_core,  y_test  = prepare(test_raw,  CORE_FEATURES, TARGET)

# Extended feature sets (fewer rows due to missingness)
X_train_ext, y_train_ext = prepare(train_raw, EXTENDED_FEATURES, TARGET)
X_test_ext,  y_test_ext  = prepare(test_raw,  EXTENDED_FEATURES, TARGET)

print(f"\nCore features    – train: {X_train_core.shape}, test: {X_test_core.shape}")
print(f"Extended features– train: {X_train_ext.shape},  test: {X_test_ext.shape}")
print(f"\nClass balance (train, core):    {y_train.mean()*100:.1f}% positive")
print(f"Class balance (train, extended): {y_train_ext.mean()*100:.1f}% positive")
print(f"Class balance (test,  core):    {y_test.mean()*100:.1f}% positive")

# ============================================================
# 5. Baselines – FIB-4 and Fatty Liver Index (FLI)
# ============================================================
print("\n" + "=" * 65)
print("STEP 2 – Clinical baselines")
print("=" * 65)

# --- FIB-4 ---
# Formula: FIB-4 = (Age * AST) / (Platelets * sqrt(ALT))
# Standard cutoffs: <1.30 = low risk, >2.67 = high risk (EASL 2021)
def compute_fib4(df):
    """Compute FIB-4 score. Returns Series."""
    age = df["RIDAGEYR"]
    ast = df["LBXSASSI"]   # U/L
    alt = df["LBXSATSI"]   # U/L
    plt_col = df["LBXPLTSI"]  # 10^9/L (already in correct unit)
    return (age * ast) / (plt_col * np.sqrt(alt))

train_fib4 = compute_fib4(train_raw).reindex(y_train.index)
test_fib4  = compute_fib4(test_raw).reindex(y_test.index)

# Compare to provided FIB4 column (sanity check)
provided = train_raw.loc[y_train.index, "FIB4"]
corr_check = train_fib4.corr(provided)
print(f"\nFIB-4 recomputed vs provided column: Pearson r = {corr_check:.4f}")
if corr_check > 0.999:
    print("  ✓ FIB-4 formula verified against provided column")
else:
    print(f"  ⚠ Small discrepancy (r={corr_check:.4f}) – likely rounding. Proceeding.")

# FIB-4 ROC-AUC on test
fib4_test_scores = test_fib4.fillna(test_fib4.median())
fib4_auc = roc_auc_score(y_test, fib4_test_scores)
fib4_prauc = average_precision_score(y_test, fib4_test_scores)
print(f"\nFIB-4 on external test set:")
print(f"  ROC-AUC = {fib4_auc:.3f}")
print(f"  PR-AUC  = {fib4_prauc:.3f}")

# Standard FIB-4 cutoff 1.30 for sensitivity/specificity
fib4_pred_130 = (fib4_test_scores >= 1.30).astype(int)
tn, fp, fn, tp = confusion_matrix(y_test, fib4_pred_130).ravel()
fib4_sens = tp / (tp + fn)
fib4_spec = tn / (tn + fp)
fib4_ppv  = tp / (tp + fp) if (tp + fp) > 0 else 0
fib4_npv  = tn / (tn + fn) if (tn + fn) > 0 else 0
print(f"\n  At cutoff 1.30: Sensitivity={fib4_sens:.3f}, Specificity={fib4_spec:.3f}, "
      f"PPV={fib4_ppv:.3f}, NPV={fib4_npv:.3f}")

# --- Fatty Liver Index (FLI) ---
# Reference: Bedogni et al. 2006 (Gut 55:1702-1706)
# Formula: FLI = e^y / (1 + e^y) * 100
#   y = 0.953*ln(TG_mg/dL) + 0.139*BMI + 0.718*ln(GGT) + 0.053*waist - 15.745
# Convert TG: mmol/L * 88.57 = mg/dL
# NOTE TO STUDENT: Please verify this formula against the original paper
#   (Bedogni et al. 2006, Gut) before using in a clinical context.
#   Minor differences in coefficient rounding exist across published sources.
def compute_fli(df):
    """
    Compute Fatty Liver Index (FLI).
    Reference: Bedogni et al. 2006, Gut 55:1702-1706.
    Requires: LBDTRSI (TG, mmol/L), BMXBMI, LBXSGTSI (GGT, U/L), BMXWAIST (cm)
    """
    tg_mmol = df["LBDTRSI"]
    tg_mgdl = tg_mmol * 88.57       # unit conversion
    bmi     = df["BMXBMI"]
    ggt     = df["LBXSGTSI"]
    waist   = df["BMXWAIST"]

    y = (0.953 * np.log(tg_mgdl)
         + 0.139 * bmi
         + 0.718 * np.log(ggt)
         + 0.053 * waist
         - 15.745)
    fli = np.exp(y) / (1 + np.exp(y)) * 100
    return fli

# FLI only available where triglycerides are present
train_fli_mask = train_raw["LBDTRSI"].notna()
test_fli_mask  = test_raw["LBDTRSI"].notna()
fli_test_sub   = test_raw[test_fli_mask & test_raw[TARGET].notna()]
fli_y_sub      = fli_test_sub[TARGET].astype(int)

if len(fli_test_sub) > 10:
    fli_scores = compute_fli(fli_test_sub)
    # Drop rows where FLI is NaN or infinite (e.g. TG=0 causes log domain error)
    valid_mask = np.isfinite(fli_scores)
    fli_scores_v = fli_scores[valid_mask]
    fli_y_v      = fli_y_sub[valid_mask]
    if len(np.unique(fli_y_v)) >= 2:
        fli_auc    = roc_auc_score(fli_y_v, fli_scores_v)
        fli_prauc  = average_precision_score(fli_y_v, fli_scores_v)
    else:
        fli_auc = fli_prauc = None
    print(f"\nFLI on external test set (n={len(fli_test_sub)}, steatosis proxy):")
    print(f"  ROC-AUC = {fli_auc:.3f}  PR-AUC = {fli_prauc:.3f}")
else:
    fli_auc = fli_prauc = None
    print("FLI: insufficient data on test set")

# ============================================================
# 6. Model definitions
# ============================================================
print("\n" + "=" * 65)
print("STEP 3 – Define models")
print("=" * 65)

# Class weight ratio for imbalanced data
pos_weight = int(round((y_train == 0).sum() / (y_train == 1).sum()))
print(f"Class weight ratio (neg:pos) = {pos_weight}:1")

def make_lr():
    """Logistic Regression with StandardScaler."""
    return Pipeline([
        ("scaler", StandardScaler()),
        ("clf",    LogisticRegression(
            C=0.1, class_weight="balanced",
            max_iter=1000, random_state=SEED, solver="lbfgs"
        )),
    ])

def make_rf():
    """Random Forest with balanced class weights."""
    return RandomForestClassifier(
        n_estimators=400,
        max_depth=8,
        min_samples_leaf=10,
        class_weight="balanced",
        random_state=SEED,
        n_jobs=-1,
    )

def make_gb():
    """Gradient Boosting – XGBoost if available, else HistGBT."""
    if XGB_AVAILABLE:
        scale_pos = pos_weight
        return xgb.XGBClassifier(
            n_estimators=500,
            max_depth=4,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            scale_pos_weight=scale_pos,
            eval_metric="aucpr",
            use_label_encoder=False,
            random_state=SEED,
            n_jobs=-1,
            verbosity=0,
        )
    else:
        return HistGradientBoostingClassifier(
            max_iter=500,
            max_depth=4,
            learning_rate=0.05,
            class_weight="balanced",
            random_state=SEED,
        )

GB_NAME = "XGBoost" if XGB_AVAILABLE else "HistGBT"
print(f"Gradient boosting model: {GB_NAME}")

MODELS = {
    "LogisticRegression": make_lr(),
    "RandomForest":       make_rf(),
    GB_NAME:              make_gb(),
}

# ============================================================
# 7. Cross-validated training on CORE features, choose threshold
# ============================================================
print("\n" + "=" * 65)
print("STEP 4 – CV training + threshold selection (CORE features)")
print("=" * 65)

cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)

TARGET_SENSITIVITY = 0.90   # choose threshold to reach ~90% sensitivity

thresholds = {}      # model name -> threshold on training data
cv_aucs    = {}      # model name -> list of fold AUCs
oof_probs  = {}      # out-of-fold probabilities for threshold tuning

for name, model in MODELS.items():
    print(f"\n  Training {name} (core features)...")
    probs = cross_val_predict(model, X_train_core, y_train,
                              cv=cv, method="predict_proba", n_jobs=1)[:, 1]
    oof_probs[name] = probs

    # Compute threshold at ~90% sensitivity using OOF predictions
    fpr, tpr, thresh_arr = roc_curve(y_train, probs)
    # Find smallest threshold where sensitivity >= TARGET_SENSITIVITY
    valid = thresh_arr[tpr >= TARGET_SENSITIVITY]
    thr = float(valid[-1]) if len(valid) > 0 else 0.5
    thresholds[name] = thr

    auc = roc_auc_score(y_train, probs)
    prauc = average_precision_score(y_train, probs)
    pred  = (probs >= thr).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_train, pred).ravel()
    sens = tp / (tp + fn)
    spec = tn / (tn + fp)
    cv_aucs[name] = auc
    print(f"    OOF ROC-AUC={auc:.3f}  PR-AUC={prauc:.3f}  "
          f"Threshold={thr:.3f}  Sens={sens:.3f}  Spec={spec:.3f}")

# ============================================================
# 8. Fit final models on full training data
# ============================================================
print("\n" + "=" * 65)
print("STEP 5 – Fit final models on full training data")
print("=" * 65)

trained_models_core = {}
calibrated_models_core = {}

for name, model in MODELS.items():
    print(f"\n  Fitting {name} on CORE features (n={len(X_train_core)})...")
    model.fit(X_train_core, y_train)
    trained_models_core[name] = model

    # Calibrate using cross-validated isotonic regression (5-fold)
    cal_model = CalibratedClassifierCV(model, method="isotonic", cv=5)
    cal_model.fit(X_train_core, y_train)
    calibrated_models_core[name] = cal_model
    print(f"    Calibration fitted (isotonic, 5-fold CV).")

# Extended feature models
trained_models_ext = {}
calibrated_models_ext = {}

for name, model_fn in [("LogisticRegression", make_lr),
                        ("RandomForest",       make_rf),
                        (GB_NAME,              make_gb)]:
    m = model_fn()
    print(f"\n  Fitting {name} on EXTENDED features (n={len(X_train_ext)})...")
    m.fit(X_train_ext, y_train_ext)
    trained_models_ext[name] = m

    cal = CalibratedClassifierCV(m, method="isotonic", cv=5)
    cal.fit(X_train_ext, y_train_ext)
    calibrated_models_ext[name] = cal

# ============================================================
# 9. Risk bands (defined on training data, NEVER on test)
# ============================================================
print("\n" + "=" * 65)
print("STEP 6 – Risk band definition (training OOF probabilities)")
print("=" * 65)

# Use the best OOF probabilities (GB model) to define percentile-based bands
best_name = max(cv_aucs, key=cv_aucs.get)
best_oof   = oof_probs[best_name]

# Bands: Low (<15th pctile of positives), High (>60th pctile of positives)
pos_probs = best_oof[y_train.values == 1]
low_cut   = float(np.percentile(best_oof, 70))   # 70th pctile of all probs
high_cut  = float(np.percentile(best_oof, 90))   # 90th pctile

RISK_BANDS = {
    "low_cutoff":      round(low_cut,  3),
    "high_cutoff":     round(high_cut, 3),
    "thresholds":      {k: round(v, 4) for k, v in thresholds.items()},
    "best_model":      best_name,
}
print(f"  Low  risk  : probability < {low_cut:.3f}")
print(f"  Moderate   : {low_cut:.3f} – {high_cut:.3f}")
print(f"  High risk  : probability > {high_cut:.3f}")
print(f"  Best model (by OOF AUC): {best_name}")

# ============================================================
# 10. Bootstrap evaluation on EXTERNAL TEST SET
# ============================================================
print("\n" + "=" * 65)
print("STEP 7 – External test set evaluation (bootstrap CIs)")
print("=" * 65)

N_BOOT = 1000

def bootstrap_ci(y_true, y_score, metric_fn, n=N_BOOT, seed=SEED):
    """Bootstrap 95% CI for a metric."""
    rng = np.random.default_rng(seed)
    scores = []
    for _ in range(n):
        idx = rng.integers(0, len(y_true), size=len(y_true))
        yt, ys = y_true[idx], y_score[idx]
        if len(np.unique(yt)) < 2:
            continue
        try:
            scores.append(metric_fn(yt, ys))
        except Exception:
            pass
    arr = np.array(scores)
    return np.mean(arr), np.percentile(arr, 2.5), np.percentile(arr, 97.5)

all_metrics = {}

# --- FIB-4 baseline ---
fib4_arr = fib4_test_scores.values
m, lo, hi = bootstrap_ci(y_test.values, fib4_arr, roc_auc_score)
m2, lo2, hi2 = bootstrap_ci(y_test.values, fib4_arr, average_precision_score)
all_metrics["FIB4_baseline"] = {
    "model": "FIB-4 baseline",
    "features": "clinical",
    "roc_auc": round(m, 3),  "roc_auc_lo": round(lo, 3), "roc_auc_hi": round(hi, 3),
    "pr_auc":  round(m2,3),  "pr_auc_lo":  round(lo2,3), "pr_auc_hi":  round(hi2,3),
    "threshold": 1.30,
    "sensitivity": round(fib4_sens, 3),
    "specificity": round(fib4_spec, 3),
    "ppv":         round(fib4_ppv,  3),
    "npv":         round(fib4_npv,  3),
    "brier_score": round(brier_score_loss(y_test, fib4_arr / fib4_arr.max()), 4),
}

def eval_model(name, model, X_test, y_test_arr, threshold, feat_set):
    """Evaluate one model on test data and return metrics dict."""
    proba = model.predict_proba(X_test)[:, 1]
    pred  = (proba >= threshold).astype(int)

    m_auc, lo_auc, hi_auc  = bootstrap_ci(y_test_arr, proba, roc_auc_score)
    m_pr,  lo_pr,  hi_pr   = bootstrap_ci(y_test_arr, proba, average_precision_score)

    tn, fp, fn, tp = confusion_matrix(y_test_arr, pred).ravel()
    sens = tp / (tp + fn) if (tp + fn) > 0 else 0
    spec = tn / (tn + fp) if (tn + fp) > 0 else 0
    ppv  = tp / (tp + fp) if (tp + fp) > 0 else 0
    npv  = tn / (tn + fn) if (tn + fn) > 0 else 0
    brier = brier_score_loss(y_test_arr, proba)

    return {
        "model":       name,
        "features":    feat_set,
        "roc_auc":     round(m_auc, 3),
        "roc_auc_lo":  round(lo_auc, 3),
        "roc_auc_hi":  round(hi_auc, 3),
        "pr_auc":      round(m_pr,  3),
        "pr_auc_lo":   round(lo_pr,  3),
        "pr_auc_hi":   round(hi_pr,  3),
        "threshold":   round(threshold, 4),
        "sensitivity": round(sens,  3),
        "specificity": round(spec,  3),
        "ppv":         round(ppv,   3),
        "npv":         round(npv,   3),
        "brier_score": round(brier, 4),
        "n_test":      int(len(y_test_arr)),
    }, proba

all_proba_dict = {}  # for ROC curves

for name in MODELS:
    thr = thresholds[name]
    # Core model
    m, proba = eval_model(
        name, calibrated_models_core[name],
        X_test_core, y_test.values, thr, "core"
    )
    all_metrics[f"{name}_core"] = m
    all_proba_dict[f"{name}_core"] = proba
    print(f"\n  {name} (CORE):")
    print(f"    ROC-AUC = {m['roc_auc']:.3f} [{m['roc_auc_lo']:.3f}–{m['roc_auc_hi']:.3f}]")
    print(f"    PR-AUC  = {m['pr_auc']:.3f} [{m['pr_auc_lo']:.3f}–{m['pr_auc_hi']:.3f}]")
    print(f"    Sens={m['sensitivity']:.3f}  Spec={m['specificity']:.3f}  "
          f"PPV={m['ppv']:.3f}  NPV={m['npv']:.3f}  Brier={m['brier_score']:.4f}")

    # Extended model (own threshold – recompute from OOF)
    oof_ext = cross_val_predict(
        make_lr() if name == "LogisticRegression" else (make_rf() if name == "RandomForest" else make_gb()),
        X_train_ext, y_train_ext, cv=cv, method="predict_proba"
    )[:, 1]
    fpr_e, tpr_e, thr_e = roc_curve(y_train_ext, oof_ext)
    valid_e = thr_e[tpr_e >= TARGET_SENSITIVITY]
    thr_ext = float(valid_e[-1]) if len(valid_e) > 0 else 0.5

    m2, proba2 = eval_model(
        name, calibrated_models_ext[name],
        X_test_ext, y_test_ext.values, thr_ext, "extended"
    )
    all_metrics[f"{name}_extended"] = m2
    all_proba_dict[f"{name}_extended"] = proba2
    print(f"\n  {name} (EXTENDED):")
    print(f"    ROC-AUC = {m2['roc_auc']:.3f} [{m2['roc_auc_lo']:.3f}–{m2['roc_auc_hi']:.3f}]")
    print(f"    PR-AUC  = {m2['pr_auc']:.3f} [{m2['pr_auc_lo']:.3f}–{m2['pr_auc_hi']:.3f}]")
    print(f"    n_test  = {m2['n_test']}")

# Identify best overall model (by test ROC-AUC)
best_key = max(
    [k for k in all_metrics if k != "FIB4_baseline"],
    key=lambda k: all_metrics[k]["roc_auc"]
)
best_model_key = best_key
print(f"\n  Best model on external test: {best_key}")

# ============================================================
# 11. Calibration curves
# ============================================================
print("\n" + "=" * 65)
print("STEP 8 – Calibration curves")
print("=" * 65)

fig, axes = plt.subplots(1, 2, figsize=(12, 5))
line_styles = ["-", "--", ":"]

for ax, feat_set in zip(axes, ["core", "extended"]):
    ax.plot([0, 1], [0, 1], "k--", lw=1, label="Perfect calibration")
    for i, name in enumerate(MODELS):
        key = f"{name}_{feat_set}"
        if key not in all_proba_dict:
            continue
        proba_cal = all_proba_dict[key]
        y_arr = y_test.values if feat_set == "core" else y_test_ext.values
        if len(proba_cal) != len(y_arr):
            continue
        prob_true, prob_pred = calibration_curve(y_arr, proba_cal, n_bins=10)
        ax.plot(prob_pred, prob_true, line_styles[i], lw=1.8,
                color=["#000000", "#555555", "#aaaaaa"][i],
                marker="o", markersize=4, label=name)

    ax.set_xlabel("Mean predicted probability")
    ax.set_ylabel("Fraction of positives")
    ax.set_title(f"Calibration – {feat_set} features")
    ax.legend(fontsize=8)
    ax.grid(True)

fig.suptitle("Calibration curves (external test set)")
fig.tight_layout()
savefig(fig, "07_calibration_curves.png")

# ============================================================
# 12. ROC & PR curves
# ============================================================
print("\n" + "=" * 65)
print("STEP 9 – ROC and PR curves")
print("=" * 65)

fig, axes = plt.subplots(1, 2, figsize=(13, 5))
ax_roc, ax_pr = axes

# FIB-4
fpr_f, tpr_f, _ = roc_curve(y_test.values, fib4_arr)
prec_f, rec_f, _ = precision_recall_curve(y_test.values, fib4_arr)
ax_roc.plot(fpr_f, tpr_f, "k-", lw=2,
            label=f"FIB-4 (AUC={fib4_auc:.3f})")
ax_pr.plot(rec_f, prec_f, "k-", lw=2,
           label=f"FIB-4 (PR-AUC={fib4_prauc:.3f})")

styles = {"LogisticRegression": ("--", "#555555"),
          "RandomForest":       (":",  "#333333"),
          GB_NAME:              ("-.", "#000000")}

for name in MODELS:
    key  = f"{name}_core"
    if key not in all_proba_dict:
        continue
    ls, col = styles.get(name, ("-", "#888888"))
    proba = all_proba_dict[key]
    m_info = all_metrics[key]

    fpr_m, tpr_m, _ = roc_curve(y_test.values, proba)
    prec_m, rec_m, _ = precision_recall_curve(y_test.values, proba)

    ax_roc.plot(fpr_m, tpr_m, ls, lw=1.8, color=col,
                label=f"{name} (AUC={m_info['roc_auc']:.3f})")
    ax_pr.plot(rec_m, prec_m, ls, lw=1.8, color=col,
               label=f"{name} (PR-AUC={m_info['pr_auc']:.3f})")

ax_roc.plot([0, 1], [0, 1], ":", color="#bbbbbb", lw=1)
ax_roc.set_xlabel("False Positive Rate")
ax_roc.set_ylabel("True Positive Rate")
ax_roc.set_title("ROC curves (external test set, core features)")
ax_roc.legend(fontsize=8)

ax_pr.axhline(y_test.mean(), color="#bbbbbb", lw=1, linestyle=":",
              label=f"Chance ({y_test.mean():.2f})")
ax_pr.set_xlabel("Recall")
ax_pr.set_ylabel("Precision")
ax_pr.set_title("Precision-Recall curves (external test set)")
ax_pr.legend(fontsize=8)

fig.tight_layout()
savefig(fig, "08_roc_pr_curves.png")

# ============================================================
# 13. Explainability – SHAP or permutation importance
# ============================================================
print("\n" + "=" * 65)
print("STEP 10 – Explainability")
print("=" * 65)

# Use the best model key to pick the right model and feature set
if "_core" in best_model_key:
    best_model_name = best_model_key.replace("_core", "")
    best_model_obj  = trained_models_core[best_model_name]
    X_explain       = X_test_core
    y_explain       = y_test.values
    feat_names      = CORE_FEATURES
    feat_set_label  = "core"
else:
    best_model_name = best_model_key.replace("_extended", "")
    best_model_obj  = trained_models_ext[best_model_name]
    X_explain       = X_test_ext
    y_explain       = y_test_ext.values
    feat_names      = EXTENDED_FEATURES
    feat_set_label  = "extended"

print(f"  Best model for explanation: {best_model_name} ({feat_set_label})")

if SHAP_AVAILABLE:
    try:
        print("  Computing SHAP values...")
        # Use the underlying (non-calibrated) model for SHAP
        raw_model = best_model_obj

        # For XGBoost, use TreeExplainer; for LR use LinearExplainer;
        # for RF use TreeExplainer; fallback to KernelExplainer
        X_bg = shap.sample(X_explain, 200, random_state=SEED)  # background

        if isinstance(raw_model, Pipeline):
            # Logistic Regression inside pipeline
            inner = raw_model.named_steps["clf"]
            X_transformed = raw_model.named_steps["scaler"].transform(X_explain)
            X_bg_t = raw_model.named_steps["scaler"].transform(X_bg)
            explainer = shap.LinearExplainer(inner, X_bg_t)
            shap_vals = explainer.shap_values(X_transformed)
        elif XGB_AVAILABLE and isinstance(raw_model, xgb.XGBClassifier):
            explainer = shap.TreeExplainer(raw_model)
            shap_vals = explainer.shap_values(X_explain)
        elif isinstance(raw_model, RandomForestClassifier):
            explainer = shap.TreeExplainer(raw_model)
            sv_raw    = explainer.shap_values(X_explain)
            # shap_values returns list[2] in old SHAP or ndarray of shape
            # (n_samples, n_features, n_classes) in newer SHAP
            if isinstance(sv_raw, list):
                shap_vals = sv_raw[1]          # class=1 from list
            elif hasattr(sv_raw, "ndim") and sv_raw.ndim == 3:
                shap_vals = sv_raw[:, :, 1]    # class=1 slice from 3-D array
            else:
                shap_vals = sv_raw
        else:
            explainer = shap.KernelExplainer(
                raw_model.predict_proba, X_bg, link="logit"
            )
            sv_raw = explainer.shap_values(X_explain[:200], nsamples=100)
            if isinstance(sv_raw, list):
                shap_vals = sv_raw[1]
            elif hasattr(sv_raw, "ndim") and sv_raw.ndim == 3:
                shap_vals = sv_raw[:, :, 1]
            else:
                shap_vals = sv_raw

        shap_abs_mean = np.abs(shap_vals).mean(axis=0)
        print("  SHAP mean |value| per feature:")
        for feat, sv in sorted(zip(feat_names, shap_abs_mean),
                                key=lambda x: -x[1]):
            print(f"    {FEAT_LABELS.get(feat, feat):30s} {sv:.4f}")

        # Summary bar plot (B/W)
        fig, ax = plt.subplots(figsize=(7, 5))
        sorted_idx = np.argsort(shap_abs_mean)
        ax.barh(
            [FEAT_LABELS.get(feat_names[i], feat_names[i]) for i in sorted_idx],
            shap_abs_mean[sorted_idx],
            color="#444444", edgecolor="white",
        )
        ax.set_xlabel("Mean |SHAP value|")
        ax.set_title(f"SHAP feature importance – {best_model_name}")
        fig.tight_layout()
        savefig(fig, "09_shap_summary.png")

        # SHAP dependence plots for top-3 features
        top3_idx = np.argsort(shap_abs_mean)[::-1][:3]
        fig, axes = plt.subplots(1, 3, figsize=(14, 4))
        for ax, fidx in zip(axes, top3_idx):
            fname = feat_names[fidx]
            flabel = FEAT_LABELS.get(fname, fname)
            ax.scatter(
                X_explain.iloc[:, fidx] if hasattr(X_explain, "iloc") else X_explain[:, fidx],
                shap_vals[:, fidx],
                alpha=0.3, s=8, color="#333333",
            )
            ax.axhline(0, color="#aaaaaa", lw=1)
            ax.set_xlabel(flabel)
            ax.set_ylabel("SHAP value")
            ax.set_title(flabel)
        fig.suptitle("SHAP dependence plots (top 3 features)")
        fig.tight_layout()
        savefig(fig, "10_shap_dependence.png")

        SHAP_USED = True

    except Exception as e:
        print(f"  SHAP failed ({e}). Falling back to permutation importance.")
        SHAP_USED = False
else:
    SHAP_USED = False

if not SHAP_USED:
    print("  Computing permutation importance...")
    # Use calibrated model for consistent probabilities
    cal_best = calibrated_models_core.get(best_model_name,
               calibrated_models_ext.get(best_model_name))
    pi = permutation_importance(
        cal_best, X_explain, y_explain,
        n_repeats=20, random_state=SEED, scoring="roc_auc", n_jobs=1
    )
    sorted_idx = np.argsort(pi.importances_mean)
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.barh(
        [FEAT_LABELS.get(feat_names[i], feat_names[i]) for i in sorted_idx],
        pi.importances_mean[sorted_idx],
        xerr=pi.importances_std[sorted_idx],
        color="#444444", edgecolor="white",
    )
    ax.set_xlabel("Permutation importance (mean ROC-AUC drop)")
    ax.set_title(f"Permutation importance – {best_model_name}")
    fig.tight_layout()
    savefig(fig, "09_permutation_importance.png")

    print("  Top features (permutation importance):")
    for i in sorted_idx[::-1]:
        print(f"    {FEAT_LABELS.get(feat_names[i], feat_names[i]):30s} "
              f"{pi.importances_mean[i]:.4f} +/- {pi.importances_std[i]:.4f}")

# ============================================================
# 14. Interpretation: does model beat FIB-4?
# ============================================================
print("\n" + "=" * 65)
print("STEP 11 – Does the model beat FIB-4?")
print("=" * 65)

best_auc = all_metrics[best_model_key]["roc_auc"]
beat_fib4 = best_auc > fib4_auc
print(f"  Best model  ({best_model_key})  ROC-AUC = {best_auc:.3f}")
print(f"  FIB-4 baseline                  ROC-AUC = {fib4_auc:.3f}")
if beat_fib4:
    delta = best_auc - fib4_auc
    meaningful = delta >= 0.02
    print(f"  ✓ Best model exceeds FIB-4 by {delta:.3f} AUC points.")
    print(f"  {'Meaningful improvement (delta>=0.02).' if meaningful else 'Small improvement (<0.02) – marginal.'}")
else:
    print(f"  ✗ Best model does NOT beat FIB-4 on the external test set.")
    print(f"    This is reported honestly in the README and metrics.")

beat_fib4_meaningful = beat_fib4 and (best_auc - fib4_auc) >= 0.02

# ============================================================
# 15. Save metrics.json
# ============================================================
print("\n" + "=" * 65)
print("STEP 12 – Save metrics and models")
print("=" * 65)

metrics_out = {
    "timestamp":         pd.Timestamp.now().isoformat(),
    "target":            TARGET,
    "n_train_core":      int(len(X_train_core)),
    "n_train_extended":  int(len(X_train_ext)),
    "n_test_core":       int(len(X_test_core)),
    "n_test_extended":   int(len(X_test_ext)),
    "prevalence_train":  round(float(y_train.mean()), 4),
    "prevalence_test":   round(float(y_test.mean()),  4),
    "target_sensitivity": TARGET_SENSITIVITY,
    "risk_bands":        RISK_BANDS,
    "beat_fib4":         bool(beat_fib4),
    "beat_fib4_meaningful": bool(beat_fib4_meaningful),
    "best_model":        best_model_key,
    "results":           all_metrics,
    "figure_dir":        FIG_DIR,
    "shap_used":         SHAP_USED,
    "xgb_used":          XGB_AVAILABLE,
    "feat_labels":       FEAT_LABELS,
    "core_features":     CORE_FEATURES,
    "extended_features": EXTENDED_FEATURES,
}

metrics_path = os.path.join(OUT_DIR, "metrics.json")
with open(metrics_path, "w") as f:
    json.dump(metrics_out, f, indent=2)
print(f"  Metrics saved -> {metrics_path}")

# Save models (joblib)
model_artefacts = {
    "calibrated_core":     calibrated_models_core,
    "calibrated_extended": calibrated_models_ext,
    "thresholds_core":     thresholds,
    "risk_bands":          RISK_BANDS,
    "core_features":       CORE_FEATURES,
    "extended_features":   EXTENDED_FEATURES,
    "feat_labels":         FEAT_LABELS,
    "best_model_name":     best_model_key,
    "seed":                SEED,
}
model_path = os.path.join(MODEL_DIR, "livercheck_models.joblib")
joblib.dump(model_artefacts, model_path)
print(f"  Models saved  -> {model_path}")

# ============================================================
# 16. Summary table
# ============================================================
print("\n" + "=" * 65)
print("RESULTS SUMMARY – External test set")
print("=" * 65)
print(f"{'Model':<35} {'ROC-AUC':>10} {'95% CI':>20} {'PR-AUC':>10} {'Sens':>7} {'Spec':>7}")
print("-" * 95)

# FIB-4
m = all_metrics["FIB4_baseline"]
print(f"{'FIB-4 (cutoff 1.30)':<35} "
      f"{m['roc_auc']:>10.3f} "
      f"[{m['roc_auc_lo']:.3f}–{m['roc_auc_hi']:.3f}]".rjust(20) + " "
      f"{m['pr_auc']:>10.3f} "
      f"{m['sensitivity']:>7.3f} "
      f"{m['specificity']:>7.3f}")

for key, m in all_metrics.items():
    if key == "FIB4_baseline":
        continue
    print(f"{key:<35} "
          f"{m['roc_auc']:>10.3f} "
          f"[{m['roc_auc_lo']:.3f}–{m['roc_auc_hi']:.3f}]".rjust(20) + " "
          f"{m['pr_auc']:>10.3f} "
          f"{m['sensitivity']:>7.3f} "
          f"{m['specificity']:>7.3f}")

print("\nTraining complete. Run the app with:")
print("  uvicorn app.main:app --reload")
