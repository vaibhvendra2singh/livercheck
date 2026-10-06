"""
LiverCheck – FastAPI Backend
============================
Endpoints:
  POST /predict  – run the ML model and return risk score
  GET  /metrics  – return saved metrics.json
  GET  /health   – liveness check

Run:
    uvicorn app.main:app --reload
"""

import os
import json
import math
import time
import warnings
import numpy as np
import pandas as pd
import joblib
from pathlib import Path
from typing import Optional, List

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel, Field, field_validator, model_validator

# Suppress feature names UserWarning from scikit-learn CalibratedClassifierCV wrapper
warnings.filterwarnings("ignore", category=UserWarning, module="sklearn")

# ============================================================
# Paths
# ============================================================
BASE_DIR    = Path(__file__).resolve().parent.parent
MODEL_PATH  = BASE_DIR / "outputs" / "models" / "livercheck_models.joblib"
METRICS_PATH= BASE_DIR / "outputs" / "metrics.json"
FIGURES_DIR = BASE_DIR / "outputs" / "figures"
FRONTEND_DIR= BASE_DIR / "frontend"

# ============================================================
# Load model artefacts at startup
# ============================================================
artefacts: dict = {}

def load_artefacts():
    global artefacts
    if not MODEL_PATH.exists():
        print(f"[WARNING] Model file not found at {MODEL_PATH}. "
              "Run python3 src/train.py first.")
        return
    artefacts = joblib.load(MODEL_PATH)
    print(f"[INFO] Models loaded. Best model: {artefacts.get('best_model_name')}")

load_artefacts()

# ============================================================
# App setup
# ============================================================
app = FastAPI(
    title="LiverCheck API",
    description=(
        "Non-invasive liver fibrosis risk estimation from routine blood tests. "
        "FOR EDUCATIONAL / RESEARCH USE ONLY – not a medical diagnostic tool."
    ),
    version="1.0.0",
)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    print(f"[422 Validation Notice] Path: {request.url.path} | Errors: {errors}")
    return JSONResponse(status_code=422, content={"detail": errors})

# CORS – allow all origins for local dev / student use
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# Pydantic schemas
# ============================================================
class PredictRequest(BaseModel):
    """Input schema with validated clinical ranges."""
    age:          float = Field(..., ge=18, le=120,  description="Age in years (18–120)")
    sex:          int   = Field(..., ge=1,  le=2,    description="Sex: 1=Male, 2=Female")
    bmi:          float = Field(..., ge=5,  le=150,  description="Body Mass Index (5–150)")
    waist:        float = Field(..., ge=30, le=300,  description="Waist circumference in cm (30–300)")
    alt:          float = Field(..., ge=0.1,le=2000, description="ALT (U/L, 0.1–2000)")
    ast:          float = Field(..., ge=0.1,le=2000, description="AST (U/L, 0.1–2000)")
    ggt:          float = Field(..., ge=0.1,le=3000, description="GGT (U/L, 0.1–3000)")
    platelets:    float = Field(..., ge=0.1,le=3000, description="Platelets (10^9/L, 0.1–3000)")
    triglycerides:Optional[float] = Field(None, ge=0.01, le=100, description="Triglycerides (mmol/L, optional)")
    glucose:      Optional[float] = Field(None, ge=1,    le=1200,description="Glucose (mg/dL, optional)")

    @field_validator("age", "bmi", "waist", "alt", "ast", "ggt", "platelets")
    @classmethod
    def must_be_positive(cls, v):
        if v <= 0:
            raise ValueError("Value must be positive")
        return v


class FactorItem(BaseModel):
    name:         str
    direction:    str   # "increases" or "decreases"
    contribution: float  # normalised 0-1


class PredictResponse(BaseModel):
    probability:   float
    risk_level:    str        # Low / Moderate / High
    fib4:          float
    fib4_category: str        # Low / Intermediate / High
    top_factors:   List[FactorItem]
    model_used:    str
    disclaimer:    str


# ============================================================
# Helper functions
# ============================================================
def compute_fib4(age, ast, alt, platelets) -> float:
    """FIB-4 = (age × AST) / (platelets × √ALT)"""
    if alt <= 0 or platelets <= 0:
        return float("nan")
    return (age * ast) / (platelets * math.sqrt(alt))


def fib4_category(score: float) -> str:
    """Standard FIB-4 risk categories (EASL 2021)."""
    if score < 1.30:
        return "Low"
    if score < 2.67:
        return "Intermediate"
    return "High"


def classify_risk(prob: float, bands: dict) -> str:
    low_cut  = bands.get("low_cutoff",  0.10)
    high_cut = bands.get("high_cutoff", 0.30)
    if prob < low_cut:
        return "Low"
    if prob < high_cut:
        return "Moderate"
    return "High"


def get_top_factors(model, feature_names, feat_values,
                    feat_labels: dict, n=5) -> List[FactorItem]:
    """
    Derive top contributing features.
    Uses SHAP if available, else a perturbation-based approximation.
    """
    sv = None
    if hasattr(model, "named_steps"):
        try:
            import shap as _shap
            X = np.array(feat_values).reshape(1, -1)
            inner  = model.named_steps["clf"]
            scaler = model.named_steps["scaler"]
            X_t    = scaler.transform(X)
            bg     = scaler.transform(np.zeros((1, len(feature_names))))
            exp    = _shap.LinearExplainer(inner, bg)
            sv     = exp.shap_values(X_t)[0]
        except Exception:
            sv = None
    elif "XGB" in type(model).__name__:
        try:
            import shap as _shap
            X_df = pd.DataFrame(np.array(feat_values).reshape(1, -1), columns=feature_names)
            exp = _shap.TreeExplainer(model)
            sv  = exp.shap_values(X_df)[0]
        except Exception:
            sv = None

    if sv is None:
        # Batched perturbation: evaluate base + all feature perturbations in a single model call (10x faster)
        n_feats = len(feat_values)
        batch = np.tile(feat_values, (n_feats + 1, 1)).astype(float)
        for i, val in enumerate(feat_values):
            delta = max(abs(val) * 0.1, 0.01)
            batch[i + 1, i] += delta
        X_batch = pd.DataFrame(batch, columns=feature_names)
        probs = model.predict_proba(X_batch)[:, 1]
        base_prob = probs[0]
        sv = probs[1:] - base_prob

    # Build output
    abs_sv = np.abs(sv)
    total  = abs_sv.sum() if abs_sv.sum() > 0 else 1.0
    order  = np.argsort(abs_sv)[::-1][:n]
    return [
        FactorItem(
            name        = feat_labels.get(feature_names[i], feature_names[i]),
            direction   = "increases" if sv[i] > 0 else "decreases",
            contribution= round(float(abs_sv[i] / total), 4),
        )
        for i in order
    ]


# ============================================================
# Endpoints
# ============================================================
@app.get("/health")
async def health():
    """Liveness check."""
    return {
        "status":       "ok",
        "model_loaded": bool(artefacts),
        "timestamp":    time.time(),
    }


@app.get("/metrics")
async def get_metrics():
    """Return saved metrics.json and a list of available figure paths."""
    if not METRICS_PATH.exists():
        raise HTTPException(
            status_code=503,
            detail="Metrics not found. Run python3 src/train.py first."
        )
    with open(METRICS_PATH) as f:
        metrics = json.load(f)

    # List figures
    figures = []
    if FIGURES_DIR.exists():
        figures = [
            f"/figures/{p.name}"
            for p in sorted(FIGURES_DIR.glob("*.png"))
        ]
    metrics["figure_urls"] = figures
    return JSONResponse(content=metrics)


@app.post("/predict", response_model=PredictResponse)
async def predict(req: PredictRequest):
    """
    Predict liver fibrosis risk from blood test values.
    Uses extended model (+ TG + glucose) if both optional fields provided;
    otherwise uses core model.
    """
    if not artefacts:
        raise HTTPException(
            status_code=503,
            detail="Model not loaded. Run python3 src/train.py first."
        )

    use_extended = (req.triglycerides is not None and req.glucose is not None)

    if use_extended:
        features    = artefacts["extended_features"]
        feat_values = [
            req.age, req.sex, req.bmi, req.waist,
            req.alt, req.ast, req.ggt, req.platelets,
            req.triglycerides, req.glucose,
        ]
        # Pick best available extended model
        best_key   = artefacts.get("best_model_name", "")
        model_name = best_key.replace("_extended", "").replace("_core", "")
        models     = artefacts["calibrated_extended"]
        # Prefer best model, fallback to any available
        if model_name in models:
            model_obj = models[model_name]
        else:
            model_obj  = next(iter(models.values()))
            model_name = next(iter(models.keys()))
        model_used = f"{model_name} (extended)"
    else:
        features    = artefacts["core_features"]
        feat_values = [
            req.age, req.sex, req.bmi, req.waist,
            req.alt, req.ast, req.ggt, req.platelets,
        ]
        best_key   = artefacts.get("best_model_name", "")
        model_name = best_key.replace("_extended", "").replace("_core", "")
        models     = artefacts["calibrated_core"]
        if model_name in models:
            model_obj = models[model_name]
        else:
            model_obj  = next(iter(models.values()))
            model_name = next(iter(models.keys()))
        model_used = f"{model_name} (core)"

    # Predict
    X = pd.DataFrame([feat_values], columns=features)
    probability = float(model_obj.predict_proba(X)[0, 1])

    # FIB-4
    fib4_score = compute_fib4(req.age, req.ast, req.alt, req.platelets)
    fib4_cat   = fib4_category(fib4_score)

    # Risk level
    bands      = artefacts.get("risk_bands", {})
    risk_level = classify_risk(probability, bands)

    # Top factors (use underlying non-calibrated model from best fit)
    # We access calibrated estimator's base estimator for SHAP
    try:
        base_model = model_obj.calibrated_classifiers_[0].estimator
    except Exception:
        base_model = model_obj

    feat_labels = artefacts.get("feat_labels", {})
    top_factors = get_top_factors(base_model, features, feat_values, feat_labels)

    return PredictResponse(
        probability   = round(probability, 4),
        risk_level    = risk_level,
        fib4          = round(fib4_score, 3) if not math.isnan(fib4_score) else -1,
        fib4_category = fib4_cat,
        top_factors   = top_factors,
        model_used    = model_used,
        disclaimer    = (
            "This tool is for educational and research purposes only. "
            "It is NOT a medical diagnosis. Always consult a qualified clinician."
        ),
    )


# ============================================================
# Static file serving
# ============================================================
# Serve output figures
if FIGURES_DIR.exists():
    app.mount("/figures", StaticFiles(directory=str(FIGURES_DIR)), name="figures")

# Serve frontend (must be last – catch-all)
if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
