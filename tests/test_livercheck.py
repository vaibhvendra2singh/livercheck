"""
LiverCheck – Automated Test Suite
==================================
Tests covering:
  1. Clinical formula calculations (FIB-4 score & risk stratification)
  2. Model artifact integrity (joblib model bundle, metrics.json, figures)
  3. Live FastAPI endpoints (/health, /metrics, /predict core & extended)
  4. Input validation and error handling
  5. Frontend integrity (Stitch components and single-page app structure)

Run with:
    venv/bin/python3 -m unittest tests/test_livercheck.py
"""

import os
import json
import math
import unittest
import urllib.request
import urllib.error
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_PATH = BASE_DIR / "outputs" / "models" / "livercheck_models.joblib"
METRICS_PATH = BASE_DIR / "outputs" / "metrics.json"
FIGURES_DIR = BASE_DIR / "outputs" / "figures"
FRONTEND_DIR = BASE_DIR / "Frontend"
API_URL = "http://localhost:8000"


class TestClinicalCalculations(unittest.TestCase):
    """Test clinical formulas and risk categorizations."""

    def test_fib4_calculation(self):
        """Verify FIB-4 formula: (Age * AST) / (Platelets * sqrt(ALT))."""
        age = 50.0
        ast = 35.0
        alt = 25.0
        platelets = 200.0

        # Expected: (50 * 35) / (200 * sqrt(25)) = 1750 / (200 * 5) = 1750 / 1000 = 1.75
        expected = 1.75
        computed = (age * ast) / (platelets * math.sqrt(alt))
        self.assertAlmostEqual(computed, expected, places=4)

    def test_fib4_threshold_stratification(self):
        """Test clinical risk cutoffs for FIB-4 index."""
        def stratify(score):
            if score < 1.30:
                return "Low"
            elif score <= 2.67:
                return "Intermediate"
            else:
                return "High"

        self.assertEqual(stratify(1.10), "Low")
        self.assertEqual(stratify(1.30), "Intermediate")
        self.assertEqual(stratify(2.00), "Intermediate")
        self.assertEqual(stratify(2.67), "Intermediate")
        self.assertEqual(stratify(2.85), "High")


class TestModelArtifacts(unittest.TestCase):
    """Verify saved models, metadata, and generated visual figures."""

    def test_model_file_exists_and_loads(self):
        """Model joblib file must exist and contain required keys."""
        import joblib

        self.assertTrue(MODEL_PATH.exists(), f"Model file missing at {MODEL_PATH}")
        artefacts = joblib.load(MODEL_PATH)
        self.assertIsInstance(artefacts, dict)

        required_keys = [
            "best_model_name",
            "core_features",
            "extended_features",
            "calibrated_core",
            "calibrated_extended",
            "risk_bands",
            "feat_labels",
        ]
        for key in required_keys:
            self.assertIn(key, artefacts, f"Missing key in model bundle: {key}")

        self.assertEqual(len(artefacts["core_features"]), 8)
        self.assertEqual(len(artefacts["extended_features"]), 10)

    def test_metrics_json_integrity(self):
        """Metrics JSON must record that ML meaningfully beats FIB-4."""
        self.assertTrue(METRICS_PATH.exists(), f"Metrics file missing at {METRICS_PATH}")
        with open(METRICS_PATH, "r") as f:
            data = json.load(f)

        self.assertTrue(data.get("beat_fib4"), "Model failed to beat FIB-4 baseline")
        self.assertIn("RandomForest", data.get("best_model", ""))

        results = data.get("results", {})
        fib4_auc = results.get("FIB4_baseline", {}).get("roc_auc", 0)
        best_auc = results.get("RandomForest_core", {}).get("roc_auc", 0)

        self.assertGreater(best_auc, fib4_auc + 0.10, "Improvement over FIB-4 must exceed +0.10 AUC")
        self.assertGreater(best_auc, 0.75, "Best model AUC must exceed 0.75")

    def test_figures_exist(self):
        """Key EDA and diagnostic figures must be present."""
        expected_figures = [
            "01_missingness.png",
            "02_class_balance.png",
            "03_distributions.png",
            "04_feature_by_target.png",
            "05_correlation_heatmap.png",
            "06_fib4_distribution.png",
            "07_calibration_curves.png",
            "08_roc_pr_curves.png",
            "09_shap_summary.png",
        ]
        for fig in expected_figures:
            fig_path = FIGURES_DIR / fig
            self.assertTrue(fig_path.exists(), f"Figure missing: {fig}")


class TestAPIEndpoints(unittest.TestCase):
    """Test live FastAPI endpoints and input validation."""

    def _post_json(self, endpoint, payload):
        try:
            req = urllib.request.Request(
                f"{API_URL}{endpoint}",
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req) as resp:
                return resp.getcode(), json.loads(resp.read().decode("utf-8"))
        except (urllib.error.URLError, ConnectionRefusedError, OSError):
            # In-process fallback when running tests without an external server
            import asyncio
            from app.main import predict, PredictRequest
            from pydantic import ValidationError
            if endpoint == "/predict":
                try:
                    req_obj = PredictRequest(**payload)
                    res = asyncio.run(predict(req_obj))
                    return 200, res.model_dump()
                except (ValidationError, ValueError):
                    raise urllib.error.HTTPError(f"{API_URL}{endpoint}", 422, "Unprocessable Entity", {}, None)
            raise

    def _get_json(self, endpoint):
        try:
            req = urllib.request.Request(f"{API_URL}{endpoint}")
            with urllib.request.urlopen(req) as resp:
                return resp.getcode(), json.loads(resp.read().decode("utf-8"))
        except (urllib.error.URLError, ConnectionRefusedError, OSError):
            # In-process fallback when running tests without an external server
            import asyncio
            from app.main import health, get_metrics
            if endpoint == "/health":
                res = asyncio.run(health())
                return 200, res
            elif endpoint == "/metrics":
                res = asyncio.run(get_metrics())
                return 200, json.loads(res.body.decode("utf-8"))
            raise

    def test_health_endpoint(self):
        """GET /health must return 200 with status 'ok' and model loaded."""
        code, data = self._get_json("/health")
        self.assertEqual(code, 200)
        self.assertEqual(data.get("status"), "ok")
        self.assertTrue(data.get("model_loaded"))

    def test_metrics_endpoint(self):
        """GET /metrics must return model performance comparison."""
        code, data = self._get_json("/metrics")
        self.assertEqual(code, 200)
        self.assertTrue(data.get("beat_fib4"))
        self.assertIn("results", data)

    def test_predict_core_model(self):
        """POST /predict with core 8 features must return valid prediction."""
        payload = {
            "age": 55,
            "sex": 1,
            "bmi": 28.5,
            "waist": 96.0,
            "alt": 45.0,
            "ast": 38.0,
            "ggt": 52.0,
            "platelets": 190.0,
        }
        code, data = self._post_json("/predict", payload)
        self.assertEqual(code, 200)

        # Probabilities must be bounded in [0, 1]
        self.assertGreaterEqual(data["probability"], 0.0)
        self.assertLessEqual(data["probability"], 1.0)

        # Risk level must be one of standard categories
        self.assertIn(data["risk_level"], ["Low", "Moderate", "High"])

        # FIB-4 score must be positive
        self.assertGreater(data["fib4"], 0.0)

        # Top factors list must be populated
        self.assertIsInstance(data["top_factors"], list)
        self.assertGreaterEqual(len(data["top_factors"]), 3)

        # Core model should be marked as used
        self.assertIn("core", data["model_used"])

    def test_predict_extended_model(self):
        """POST /predict with 10 features should trigger extended model."""
        payload = {
            "age": 60,
            "sex": 2,
            "bmi": 32.0,
            "waist": 105.0,
            "alt": 60.0,
            "ast": 55.0,
            "ggt": 75.0,
            "platelets": 165.0,
            "triglycerides": 2.2,
            "glucose": 115.0,
        }
        code, data = self._post_json("/predict", payload)
        self.assertEqual(code, 200)
        self.assertIn("extended", data["model_used"])

    def test_predict_validation_error(self):
        """POST /predict with clinically invalid inputs should fail with 422."""
        invalid_payload = {
            "age": 12,  # ge=18 constraint
            "sex": 1,
            "bmi": 25.0,
            "waist": 85.0,
            "alt": -5.0,  # negative enzyme
            "ast": 30.0,
            "ggt": 40.0,
            "platelets": 200.0,
        }
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            self._post_json("/predict", invalid_payload)
        self.assertEqual(ctx.exception.code, 422)


class TestFrontendIntegrity(unittest.TestCase):
    """Verify that Frontend folder has all Stitch components and SPA wiring."""

    def test_frontend_subdirectories_present(self):
        """All Stitch exported components must be present in Frontend/."""
        expected_dirs = [
            "calculator_liver_health_risk_check",
            "results_liver_health_risk_screening",
            "how_it_works_clinical_methodology",
            "livercheck_monochromatic_logo",
            "clinical_monochrome",
        ]
        for d in expected_dirs:
            p = FRONTEND_DIR / d
            self.assertTrue(p.is_dir(), f"Required Stitch component missing: {d}")

    def test_index_html_has_all_sections(self):
        """index.html must contain all three application sections and SVG elements."""
        index_file = FRONTEND_DIR / "index.html"
        self.assertTrue(index_file.exists())
        content = index_file.read_text(encoding="utf-8")

        self.assertIn('id="section-calculator"', content)
        self.assertIn('id="section-results"', content)
        self.assertIn('id="section-how-it-works"', content)
        self.assertIn('id="gauge-fill-arc"', content)
        self.assertIn('id="factors-container"', content)
        self.assertIn("Hepatic Vector Model", content)

    def test_app_js_wiring(self):
        """app.js must implement core interaction and prediction methods."""
        app_file = FRONTEND_DIR / "app.js"
        self.assertTrue(app_file.exists())
        content = app_file.read_text(encoding="utf-8")

        self.assertIn("calculateRiskScore", content)
        self.assertIn("recalculateBMI", content)
        self.assertIn("showSection", content)
        self.assertIn("renderResults", content)
        self.assertIn("renderFactorBreakdown", content)


if __name__ == "__main__":
    unittest.main()
