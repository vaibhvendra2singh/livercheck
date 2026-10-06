# LiverCheck

LiverCheck is a student machine learning project. It checks whether basic blood tests and body measurements can help spot early liver scarring (fibrosis) before symptoms appear.

---

## What this project does

Your liver can develop scarring when it stays inflamed over a long period. In the early stages, people usually feel completely normal. Doctors traditionally use an equation called FIB-4 to look for risk, but it misses many early cases. 

We wanted to see if a simple machine learning model could do better by combining blood tests with waist and weight measurements.

This project is for educational use only. It is not a medical device and cannot diagnose any condition.

---

## The data we used

We used public data from the US National Health and Nutrition Examination Survey (NHANES), collected by the Centers for Disease Control and Prevention (CDC).

| Dataset | Source | Purpose |
|---|---|---|
| `train.csv` | NHANES 2017 to 2018 survey cycle | Model training and cross-validation |
| `test.csv` | NHANES 2021 to 2023 survey cycle | Independent testing only |

The test file was kept separate. We never trained the model on it, tuned settings with it, or picked cutoffs from it.

### Where to download the raw NHANES data
Because raw health survey files are large and public, `train.csv` and `test.csv` are kept locally and excluded from git via `.gitignore`. You can download the original files directly from the CDC NHANES portal:
- NHANES 2017–2018: https://wwwn.cdc.gov/nchs/nhanes/continuousnhanes/default.aspx?BeginYear=2017
- NHANES 2021–2023: https://wwwn.cdc.gov/nchs/nhanes/continuousnhanes/default.aspx?BeginYear=2021
- Modules required: Demographics (DEMO), Body Measures (BMX), Liver Ultrasound Transient Elastography (LUX), Standard Biochemistry Profile (BIOPRO), Complete Blood Count (CBC).

### Measurements used as features
1. **Age**: Your current age in years.
2. **Biological sex**: Used to set baseline enzyme ranges.
3. **Body Mass Index (BMI)**: Weight in kilograms divided by height in meters squared.
4. **Waist circumference**: Distance around the belly in centimeters. Extra belly fat is closely tied to fat in the liver.
5. **ALT (Alanine Aminotransferase)**: An enzyme released into the blood when liver cells are irritated.
6. **AST (Aspartate Aminotransferase)**: An enzyme found in liver and muscle cells.
7. **GGT (Gamma-glutamyl Transferase)**: An enzyme that rises when bile ducts or liver tissue are under stress.
8. **Platelet count**: Blood cells that help clotting. A stiff liver slows blood flow, which can drop platelet counts.
9. **Triglycerides (optional)**: Blood fats linked to metabolic health.
10. **Fasting glucose (optional)**: Blood sugar level.

**Target label:** Liver stiffness of 8.0 kPa or higher on a FibroScan exam (transient elastography). A score of 8.0 kPa indicates significant scarring.

---

## How we built and trained the models

We trained three machine learning algorithms on the 2017 to 2018 data:
1. **Logistic Regression**: A standard linear baseline with balanced class weights.
2. **Random Forest**: An ensemble of decision trees that handles non-linear interactions.
3. **XGBoost**: Gradient boosted decision trees.

### Steps taken:
- We trained using 5-fold cross-validation on the training set only.
- We set our decision cutoff to catch at least 90 percent of people with significant scarring (90 percent sensitivity).
- We calibrated predicted probabilities with isotonic regression so percentages reflect real observed frequencies.
- We tested every model against standard clinical baselines: FIB-4 and the Fatty Liver Index (FLI).

---

## Test results on the independent 2021 to 2023 group

Here are the results on 5,526 people from the 2021 to 2023 survey. The model had never seen these records before.

| Model | Features | ROC-AUC (95% CI) | PR-AUC | Sensitivity | Specificity | PPV | NPV |
|---|---|---|---|---|---|---|---|
| **FIB-4 baseline** | Clinical (4) | 0.601 [0.577 to 0.628] | 0.193 | 0.434 | 0.702 | 0.163 | 0.902 |
| Logistic Regression | Core (8) | 0.776 [0.756 to 0.799] | 0.398 | 0.944 | 0.232 | 0.142 | 0.968 |
| **Random Forest** | **Core (8)** | **0.782 [0.760 to 0.801]** | **0.399** | **0.963** | 0.156 | 0.133 | 0.969 |
| XGBoost | Core (8) | 0.761 [0.740 to 0.783] | 0.377 | 0.998 | 0.005 | 0.119 | 0.955 |

The Random Forest model with 8 core routine features performed best. It reached an ROC-AUC of 0.782, beating the standard FIB-4 score (0.601) by 0.181 points.

The most influential measurements were waist size, GGT, BMI, and age. Adding fasting glucose and triglycerides cut the available training rows in half, which lowered overall performance. The core 8-measurement model generalized best.

---

## Limitations

Please keep these points in mind:
1. **US survey data only**: The model was trained on people living in the United States. It may not behave the same way in other countries.
2. **FibroScan stiffness is an estimate, not a biopsy**: Transient elastography is safe and painless, but temporary inflammation, heavy meals, or alcohol can also increase stiffness.
3. **Student project**: This software was written as part of an AI and machine learning class project. It has not been reviewed by health authorities.
4. **No preloaded sample data**: The web app starts with blank inputs and only shows numbers after you run a calculation. We do not store or track any data you enter.

---

## Project structure

```
.
├── start.sh                  # One-step startup script
├── train.csv                 # NHANES 2017-2018 training data (ignored by git)
├── test.csv                  # NHANES 2021-2023 test data (ignored by git)
├── requirements.txt          # Python dependencies
├── README.md                 # Project documentation
├── src/
│   ├── eda.py                # Exploratory data analysis scripts
│   └── train.py              # Model training and calibration pipeline
├── app/
│   ├── __init__.py
│   └── main.py               # FastAPI backend server
├── Frontend/                 # Web application interface
│   ├── index.html            # Main interface markup
│   ├── strings.js            # Centralized user-facing plain language strings
│   ├── app.js                # Form handling and API communication
│   └── index.css             # Base styles and animations
├── tests/
│   └── test_livercheck.py    # Automated test suite
└── outputs/
    ├── metrics.json          # Benchmark metrics from training
    ├── models/
    │   └── livercheck_models.joblib
    └── figures/              # Plots generated during training
```

---

## How to run the project

### Quick start
Open a terminal in this folder and run:
```bash
./start.sh
```
This script checks the Python environment, verifies model files, and starts the local server at `http://localhost:8000`.

### Manual steps
1. Activate the virtual environment:
   ```bash
   source venv/bin/activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the automated test suite:
   ```bash
   python3 -m unittest tests/test_livercheck.py -v
   ```
4. Start the app:
   ```bash
   uvicorn app.main:app --reload
   ```
5. Open `http://localhost:8000` in your web browser.

---

## API endpoints

- `POST /predict`: Takes JSON blood test values and returns the calculated probability, risk level, FIB-4 score, and contributing factors.
- `GET /metrics`: Returns evaluation metrics from the saved `metrics.json`.
- `GET /health`: Checks if the server and models are loaded.
- `GET /`: Serves the web interface.
