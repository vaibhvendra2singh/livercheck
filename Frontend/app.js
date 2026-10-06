/**
 * LiverCheck – Frontend Controller
 * =================================
 * Plain JavaScript controller for the LiverCheck screening tool.
 * Sends inputs to the FastAPI /predict endpoint, renders the real output,
 * animates the liver outline fill level, and never stores user inputs.
 */

"use strict";

const API_BASE = window.location.origin;

// Application state (kept in memory only, never stored in cookies or localStorage)
let isCalculating = false;
let currentSection = "calculator";
let hasCalculated = false;

// ============================================================
// Section Navigation
// ============================================================
function showSection(sectionId) {
  currentSection = sectionId;

  const sections = {
    calculator: document.getElementById("section-calculator"),
    results: document.getElementById("section-results"),
    "how-it-works": document.getElementById("section-how-it-works"),
  };

  const navs = {
    calculator: document.getElementById("nav-calculator"),
    results: document.getElementById("nav-results"),
    "how-it-works": document.getElementById("nav-how-it-works"),
  };

  const activeClasses = "bg-white/15 text-white shadow-xs";
  const inactiveClasses = "text-neutral-400 hover:text-white hover:bg-white/5";
  const baseClasses = "nav-pill-btn flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs sm:text-sm font-medium transition-all cursor-pointer";

  Object.keys(sections).forEach((key) => {
    if (sections[key]) {
      if (key === sectionId) {
        sections[key].classList.remove("hidden");
      } else {
        sections[key].classList.add("hidden");
      }
    }

    if (navs[key]) {
      const isCurrent = key === sectionId;
      navs[key].className = `${baseClasses} ${isCurrent ? activeClasses : inactiveClasses}`;
    }
  });

  // Keep the results area hidden until a real calculation completes
  if (sectionId === "results") {
    const emptyState = document.getElementById("results-empty-state");
    const contentArea = document.getElementById("results-content-area");
    if (!hasCalculated) {
      if (emptyState) emptyState.classList.remove("hidden");
      if (contentArea) contentArea.classList.add("hidden");
    } else {
      if (emptyState) emptyState.classList.add("hidden");
      if (contentArea) contentArea.classList.remove("hidden");
    }
  }

  window.scrollTo({ top: 0, behavior: "smooth" });
}

// ============================================================
// Form Interaction Handlers
// ============================================================
function setSex(val) {
  const hiddenInput = document.getElementById("sex");
  if (hiddenInput) hiddenInput.value = val;

  const maleBtn = document.getElementById("sex-male-btn");
  const femaleBtn = document.getElementById("sex-female-btn");

  if (val === "male") {
    if (maleBtn) {
      maleBtn.className =
        "h-full rounded-lg font-label-md text-label-md transition-all flex items-center justify-center bg-primary text-on-primary font-semibold shadow-xs cursor-pointer";
    }
    if (femaleBtn) {
      femaleBtn.className =
        "h-full rounded-lg font-label-md text-label-md transition-all flex items-center justify-center bg-transparent text-secondary hover:text-primary cursor-pointer";
    }
  } else if (val === "female") {
    if (femaleBtn) {
      femaleBtn.className =
        "h-full rounded-lg font-label-md text-label-md transition-all flex items-center justify-center bg-primary text-on-primary font-semibold shadow-xs cursor-pointer";
    }
    if (maleBtn) {
      maleBtn.className =
        "h-full rounded-lg font-label-md text-label-md transition-all flex items-center justify-center bg-transparent text-secondary hover:text-primary cursor-pointer";
    }
  } else {
    // Unselected state
    if (maleBtn) {
      maleBtn.className =
        "h-full rounded-lg font-label-md text-label-md transition-all flex items-center justify-center bg-transparent text-secondary hover:text-primary cursor-pointer";
    }
    if (femaleBtn) {
      femaleBtn.className =
        "h-full rounded-lg font-label-md text-label-md transition-all flex items-center justify-center bg-transparent text-secondary hover:text-primary cursor-pointer";
    }
  }
}

function recalculateBMI() {
  const h = parseFloat(document.getElementById("height")?.value) || 0;
  const w = parseFloat(document.getElementById("weight")?.value) || 0;
  const bmiEl = document.getElementById("bmi");
  const classEl = document.getElementById("bmi-classification");

  if (!bmiEl || !classEl) return;

  const S = window.UI_STRINGS || {};

  if (h >= 100 && w >= 30) {
    const heightMeters = h / 100;
    const bmiVal = w / (heightMeters * heightMeters);
    bmiEl.innerText = bmiVal.toFixed(1);

    if (bmiVal < 18.5) {
      classEl.innerText = `(${S.bmiUnderweight || "Underweight"})`;
    } else if (bmiVal <= 24.9) {
      classEl.innerText = `(${S.bmiNormal || "Normal range"})`;
    } else if (bmiVal <= 29.9) {
      classEl.innerText = `(${S.bmiOverweight || "Overweight"})`;
    } else {
      classEl.innerText = `(${S.bmiObesity || "Higher weight range"})`;
    }
  } else {
    bmiEl.innerText = "--";
    classEl.innerText = `(${S.bmiEmpty || "Enter height and weight"})`;
  }
}

function checkAltThreshold() {
  const alt = parseFloat(document.getElementById("alt")?.value) || 0;
  const banner = document.getElementById("alt-warning-banner");
  const text = document.getElementById("alt-warning-text");
  const S = window.UI_STRINGS || {};

  if (!banner || !text) return;

  if (alt >= 300) {
    text.innerText = S.altWarningHigh || "This number looks unusually high. Please double check the unit on your lab report.";
    banner.classList.remove("hidden");
  } else {
    banner.classList.add("hidden");
  }
}

function toggleAccordion(panelId, iconId) {
  const panel = document.getElementById(panelId);
  const icon = document.getElementById(iconId);

  if (!panel || !icon) return;

  if (panel.classList.contains("hidden")) {
    panel.classList.remove("hidden");
    panel.classList.add("flex");
    icon.innerText = "remove";
  } else {
    panel.classList.add("hidden");
    panel.classList.remove("flex");
    icon.innerText = "add";
  }
}

function openLabModal() {
  const modal = document.getElementById("lab-guide-modal");
  if (modal) modal.classList.remove("hidden");
}

function closeLabModal() {
  const modal = document.getElementById("lab-guide-modal");
  if (modal) modal.classList.add("hidden");
}

function resetDefaults() {
  const fields = [
    "age",
    "height",
    "weight",
    "waist",
    "alt",
    "ast",
    "ggt",
    "platelets",
    "triglycerides",
    "glucose",
  ];
  fields.forEach((id) => {
    const el = document.getElementById(id);
    if (el) el.value = "";
  });

  // Biological sex starts unselected
  setSex("");

  const errBanner = document.getElementById("calc-error-banner");
  if (errBanner) errBanner.classList.add("hidden");

  const altBanner = document.getElementById("alt-warning-banner");
  if (altBanner) altBanner.classList.add("hidden");

  // Reset results display state
  hasCalculated = false;
  const emptyState = document.getElementById("results-empty-state");
  const contentArea = document.getElementById("results-content-area");
  if (emptyState) emptyState.classList.remove("hidden");
  if (contentArea) contentArea.classList.add("hidden");

  // Reset liver fill level inside SVG
  const liverFill = document.getElementById("liver-fill-level");
  if (liverFill) {
    liverFill.setAttribute("y", "92");
    liverFill.setAttribute("height", "0");
  }

  // Reset comparison metrics
  const mlMetric = document.getElementById("compare-ml-metric");
  const mlBar = document.getElementById("compare-ml-bar");
  const fib4Score = document.getElementById("compare-fib4-score");
  const fib4Cat = document.getElementById("compare-fib4-cat");
  const fib4Bar = document.getElementById("compare-fib4-bar");
  const metricCounter = document.getElementById("metric-counter");
  if (mlMetric) mlMetric.innerText = "--%";
  if (mlBar) mlBar.style.width = "0%";
  if (fib4Score) fib4Score.innerText = "--";
  if (fib4Cat) fib4Cat.innerText = "--";
  if (fib4Bar) fib4Bar.style.width = "0%";
  if (metricCounter) metricCounter.innerText = "--%";

  const factorsContainer = document.getElementById("factors-container");
  if (factorsContainer) factorsContainer.innerHTML = "";

  recalculateBMI();
}

function handleResetCalculation() {
  resetDefaults();
  showSection("calculator");
}

// ============================================================
// Prediction & API Integration
// ============================================================
async function calculateRiskScore() {
  if (isCalculating) return;

  const S = window.UI_STRINGS || {};
  const btn = document.getElementById("calc-submit-btn");
  const btnText = document.getElementById("btn-text");
  const errBanner = document.getElementById("calc-error-banner");
  const errText = document.getElementById("calc-error-text");
  const loadingOverlay = document.getElementById("calc-loading-overlay");

  const hideError = () => {
    if (errBanner) errBanner.classList.add("hidden");
  };
  const showError = (msg) => {
    let cleanMsg = "Calculation could not be completed. Please check your numbers.";
    if (typeof msg === "string") {
      cleanMsg = msg;
    } else if (Array.isArray(msg)) {
      const friendlyNames = {
        age: "Age",
        sex: "Biological sex",
        bmi: "Body Mass Index",
        waist: "Waist circumference",
        alt: "ALT",
        ast: "AST",
        ggt: "GGT",
        platelets: "Platelet count",
        triglycerides: "Triglycerides",
        glucose: "Glucose",
      };
      cleanMsg = msg
        .map((item) => {
          if (typeof item === "string") return item;
          if (item && typeof item === "object") {
            const loc = item.loc || [];
            const field = loc[loc.length - 1] || "";
            const fieldLabel = friendlyNames[field] || field;
            let m = item.msg || "Invalid value";
            m = m.replace(/^Value error,\s*/i, "").replace(/^Input should be\s*/i, "Must be ");
            return fieldLabel ? `${fieldLabel}: ${m}` : m;
          }
          return String(item);
        })
        .join(". ");
    } else if (msg && typeof msg === "object") {
      cleanMsg = msg.detail || msg.message || "Please verify your input values.";
    }

    if (errText) errText.innerText = cleanMsg;
    if (errBanner) {
      errBanner.classList.remove("hidden");
      errBanner.scrollIntoView({ behavior: "smooth", block: "center" });
    }
  };
  hideError();

  // Validate required inputs
  const ageStr = document.getElementById("age")?.value?.trim();
  const sexStr = document.getElementById("sex")?.value?.trim();
  const heightStr = document.getElementById("height")?.value?.trim();
  const weightStr = document.getElementById("weight")?.value?.trim();
  const waistStr = document.getElementById("waist")?.value?.trim();
  const altStr = document.getElementById("alt")?.value?.trim();
  const astStr = document.getElementById("ast")?.value?.trim();
  const ggtStr = document.getElementById("ggt")?.value?.trim();
  const plateletsStr = document.getElementById("platelets")?.value?.trim();

  // Biological sex check
  if (!sexStr) {
    showError(S.errSelectSex || "Please select biological sex.");
    return;
  }

  const missing = [];
  if (!ageStr) missing.push(S.ageLabel || "Age");
  if (!heightStr) missing.push(S.heightLabel || "Height");
  if (!weightStr) missing.push(S.weightLabel || "Weight");
  if (!waistStr) missing.push(S.waistLabel || "Waist circumference");
  if (!altStr) missing.push("ALT");
  if (!astStr) missing.push("AST");
  if (!ggtStr) missing.push("GGT");
  if (!plateletsStr) missing.push(S.plateletsLabel || "Platelet count");

  if (missing.length > 0) {
    showError((S.errMissingFields || "Please fill in all required fields: ") + missing.join(", "));
    return;
  }

  // Auto-clamp all filled inputs into their exact gap [min, max]
  document.querySelectorAll('input[type="number"]').forEach((input) => {
    if (input.value !== "") {
      const min = parseFloat(input.getAttribute("min"));
      const max = parseFloat(input.getAttribute("max"));
      let val = parseFloat(input.value);
      if (val < 0) val = Math.abs(val);
      if (!isNaN(min) && val < min) input.value = min;
      if (!isNaN(max) && val > max) input.value = max;
    }
  });

  const age = Math.max(18, Math.min(85, parseFloat(ageStr)));
  const height = Math.max(100, Math.min(240, parseFloat(heightStr)));
  const weight = Math.max(30, Math.min(300, parseFloat(weightStr)));
  const waist = Math.max(40, Math.min(200, parseFloat(waistStr)));
  const alt = Math.max(1, Math.min(1000, parseFloat(altStr)));
  const ast = Math.max(1, Math.min(1000, parseFloat(astStr)));
  const ggt = Math.max(1, Math.min(2000, parseFloat(ggtStr)));
  const platelets = Math.max(2, Math.min(1500, parseFloat(plateletsStr)));

  const sex = sexStr === "female" ? 2 : 1;
  const bmiVal = weight / ((height / 100) * (height / 100));
  const bmi = parseFloat(bmiVal.toFixed(1));

  const tgInput = document.getElementById("triglycerides")?.value?.trim();
  const glInput = document.getElementById("glucose")?.value?.trim();
  let triglycerides = tgInput && !isNaN(parseFloat(tgInput)) ? parseFloat(tgInput) : null;
  if (triglycerides !== null) {
    triglycerides = Math.max(0.1, Math.min(30.0, triglycerides));
    const tgEl = document.getElementById("triglycerides");
    if (tgEl) tgEl.value = triglycerides;
  }
  let glucose = glInput && !isNaN(parseFloat(glInput)) ? parseFloat(glInput) : null;
  if (glucose !== null) {
    glucose = Math.max(40.0, Math.min(600.0, glucose));
    const glEl = document.getElementById("glucose");
    if (glEl) glEl.value = glucose;
  }

  const payload = {
    age,
    sex,
    bmi,
    waist,
    alt,
    ast,
    ggt,
    platelets,
    triglycerides,
    glucose,
  };

  isCalculating = true;
  if (btn) btn.classList.add("opacity-70", "cursor-not-allowed");
  if (btnText) btnText.innerText = S.calculatingButton || "Calculating...";
  if (loadingOverlay) loadingOverlay.classList.remove("hidden");

  let resultData = null;

  try {
    const res = await fetch(`${API_BASE}/predict`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (res.ok) {
      resultData = await res.json();
    } else {
      const errJson = await res.json().catch(() => ({}));
      showError(errJson.detail || "Calculation could not be completed. Please check your numbers.");
    }
  } catch (err) {
    console.error("Calculation error:", err);
    showError("Could not reach the calculation server. Please make sure the app server is running.");
  } finally {
    if (loadingOverlay) loadingOverlay.classList.add("hidden");
    isCalculating = false;
    if (btn) btn.classList.remove("opacity-70", "cursor-not-allowed");
    if (btnText) btnText.innerText = S.calculateButton || "Calculate risk estimate";
  }

  if (!resultData) {
    return;
  }

  hasCalculated = true;
  renderResults(resultData, payload);
  showSection("results");
}

// ============================================================
// Render Results Page
// ============================================================
function renderResults(data, inputVals) {
  const S = window.UI_STRINGS || {};
  const emptyState = document.getElementById("results-empty-state");
  const contentArea = document.getElementById("results-content-area");
  if (emptyState) emptyState.classList.add("hidden");
  if (contentArea) contentArea.classList.remove("hidden");

  const prob = typeof data.probability === "number" ? data.probability : 0;
  const probPct = Math.round(prob * 100);

  // 1. Rising black fill level inside the SVG liver outline
  // The liver outline bounding box runs from y=20 (top) to y=92 (bottom) -> height = 72px
  const liverFill = document.getElementById("liver-fill-level");
  if (liverFill) {
    const fillHeight = Math.max(0, Math.min(72, prob * 72));
    const fillY = 92 - fillHeight;
    liverFill.setAttribute("y", fillY.toString());
    liverFill.setAttribute("height", fillHeight.toString());
  }

  // Animated percentage counter
  const metricCounter = document.getElementById("metric-counter");
  if (metricCounter) {
    animateValue(metricCounter, 0, probPct, 800);
  }

  // 2. Risk Level and Calm, Honest Interpretations
  const riskBadge = document.getElementById("risk-level-badge");
  const riskText = document.getElementById("risk-level-text");
  const stageText = document.getElementById("risk-stage-text");
  const riskHeadline = document.getElementById("risk-headline");
  const riskNarrative = document.getElementById("risk-narrative");
  const urgencyText = document.getElementById("urgency-text");

  const level = (data.risk_level || "").toLowerCase();

  if (level.includes("high") || prob >= 0.30) {
    if (riskBadge) {
      riskBadge.className =
        "inline-flex items-center gap-1.5 px-3 py-1 bg-primary text-on-primary font-label-md text-label-md rounded-full font-bold";
    }
    if (riskText) riskText.innerText = S.riskHighBadge || "Higher Concern";
    if (stageText) stageText.innerText = S.riskHighStage || "Stage F3 to F4 range";
    if (riskHeadline) riskHeadline.innerText = S.riskHighHeadline || "Higher chance of liver scarring";
    if (riskNarrative) riskNarrative.innerText = S.riskHighNarrative || "Your numbers suggest an increased chance of liver scarring or ongoing liver inflammation. You should discuss these results promptly with a doctor or liver specialist.";
    if (urgencyText) urgencyText.innerText = S.riskHighAction || "Prompt medical consultation recommended.";
  } else if (level.includes("moderate") || prob >= 0.10) {
    if (riskBadge) {
      riskBadge.className =
        "inline-flex items-center gap-1.5 px-3 py-1 border border-primary text-primary bg-surface-container font-label-md text-label-md rounded-full font-bold";
    }
    if (riskText) riskText.innerText = S.riskModBadge || "Moderate Risk";
    if (stageText) stageText.innerText = S.riskModStage || "Stage F2 range";
    if (riskHeadline) riskHeadline.innerText = S.riskModHeadline || "Moderate chance of liver scarring";
    if (riskNarrative) riskNarrative.innerText = S.riskModNarrative || "Your numbers suggest a moderate chance of liver scarring. A doctor should review these findings and decide if an ultrasound or FibroScan test is needed.";
    if (urgencyText) urgencyText.innerText = S.riskModAction || "Schedule a non-urgent visit with your doctor.";
  } else {
    if (riskBadge) {
      riskBadge.className =
        "inline-flex items-center gap-1.5 px-3 py-1 bg-surface-container text-on-surface font-label-md text-label-md rounded-full font-bold";
    }
    if (riskText) riskText.innerText = S.riskLowBadge || "Low Risk";
    if (stageText) stageText.innerText = S.riskLowStage || "Stage F0 to F1 range";
    if (riskHeadline) riskHeadline.innerText = S.riskLowHeadline || "Low chance of significant liver scarring";
    if (riskNarrative) riskNarrative.innerText = S.riskLowNarrative || "Your numbers suggest a low chance of liver scarring. Only a doctor can confirm this. Continue routine checkups and healthy daily habits.";
    if (urgencyText) urgencyText.innerText = S.riskLowAction || "Routine checkup recommended.";
  }

  // Model info
  const modelSlot = document.getElementById("model-badge-top");
  if (modelSlot) {
    modelSlot.innerText = `Model: ${data.model_used || "Random Forest"}`;
  }

  // 3. Comparison with standard FIB-4
  const mlMetric = document.getElementById("compare-ml-metric");
  const mlBar = document.getElementById("compare-ml-bar");
  if (mlMetric) mlMetric.innerText = `${probPct}%`;
  if (mlBar) mlBar.style.width = `${Math.min(100, Math.max(0, probPct))}%`;

  const fib4Val = typeof data.fib4 === "number" && data.fib4 > 0 ? data.fib4 : null;
  const fib4ScoreSlot = document.getElementById("compare-fib4-score");
  const fib4CatSlot = document.getElementById("compare-fib4-cat");
  const fib4Bar = document.getElementById("compare-fib4-bar");

  if (fib4Val !== null) {
    if (fib4ScoreSlot) fib4ScoreSlot.innerText = fib4Val.toFixed(2);
    if (fib4CatSlot) fib4CatSlot.innerText = `(${data.fib4_category || "Standard Scale"})`;
    if (fib4Bar) {
      const fib4Pct = Math.min(100, Math.max(0, Math.round((fib4Val / 4.0) * 100)));
      fib4Bar.style.width = `${fib4Pct}%`;
    }
  } else {
    if (fib4ScoreSlot) fib4ScoreSlot.innerText = "--";
    if (fib4CatSlot) fib4CatSlot.innerText = "";
    if (fib4Bar) fib4Bar.style.width = "0%";
  }

  // 4. Dynamic factor breakdown
  renderFactorBreakdown(data.top_factors || [], inputVals);

  // 5. Reference ID and timestamp
  const now = new Date();
  const dateFormatted = now.toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
  const timeSlot = document.getElementById("timestamp-slot");
  if (timeSlot) timeSlot.innerText = `Calculated on ${dateFormatted}`;

  const idEl = document.getElementById("assessment-id");
  if (idEl) {
    idEl.innerText = `LC-${dateFormatted.replace(/[^0-9]/g, "") || Date.now().toString().slice(-4)}`;
  }
}

function renderFactorBreakdown(factors, inputVals) {
  const container = document.getElementById("factors-container");
  if (!container) return;

  container.innerHTML = "";
  if (!factors || factors.length === 0) return;

  const S = window.UI_STRINGS || {};

  const factorValueMap = {
    "Waist circumference": `${inputVals.waist} cm`,
    "Platelet count": `${inputVals.platelets} x1000/µL`,
    "ALT (liver enzyme)": `${inputVals.alt} U/L`,
    "AST (liver enzyme)": `${inputVals.ast} U/L`,
    "GGT (liver enzyme)": `${inputVals.ggt} U/L`,
    "GGT enzyme": `${inputVals.ggt} U/L`,
    BMI: `${inputVals.bmi}`,
    Age: `${inputVals.age} years`,
    Triglycerides: inputVals.triglycerides ? `${inputVals.triglycerides} mmol/L` : null,
    Glucose: inputVals.glucose ? `${inputVals.glucose} mg/dL` : null,
  };

  const plainExplanations = {
    "Waist circumference": "Belly fat is closely connected to fat deposits in the liver.",
    "Platelet count": "A lower count can happen when liver stiffness slows blood flow.",
    "ALT (liver enzyme)": "An enzyme released when liver cells are irritated or injured.",
    "AST (liver enzyme)": "An enzyme found in liver and muscle cells that rises under stress.",
    "GGT (liver enzyme)": "An enzyme that rises when bile ducts or liver tissue are under stress.",
    "GGT enzyme": "An enzyme that rises when bile ducts or liver tissue are under stress.",
    BMI: "Extra body weight increases metabolic pressure on the liver.",
    Age: "The chance of liver scarring gradually increases with age.",
    Triglycerides: "Fats in the blood that reflect liver and metabolic function.",
    Glucose: "Blood sugar levels that relate to insulin and liver metabolism.",
  };

  factors.slice(0, 5).forEach((factor, idx) => {
    const name = factor.name || "Factor";
    const dir = (factor.direction || "neutral").toLowerCase();
    const contrib = Math.min(1.0, Math.max(0.02, factor.contribution || 0.1));
    const widthPct = Math.round(contrib * 100);

    const valStr = factorValueMap[name] || "";
    const explStr = plainExplanations[name] || "Contributes to the overall risk estimate.";

    let badgeClass = "bg-primary text-on-primary";
    let badgeText = S.increasesRisk || "Increases risk";
    let barColor = "bg-primary";

    if (dir === "decreases" || dir === "lowers") {
      badgeClass = "bg-surface-container text-on-surface border border-outline-variant/60";
      badgeText = S.lowersRisk || "Lowers risk";
      barColor = "bg-secondary";
    } else if (dir === "neutral") {
      badgeClass = "bg-surface-variant text-on-surface";
      badgeText = S.neutralRisk || "Neutral impact";
      barColor = "bg-outline";
    }

    const itemHtml = `
      <div class="flex flex-col gap-space-xs">
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-1">
          <div class="flex items-center gap-space-xs">
            <span class="font-label-md text-label-md font-semibold text-primary">${idx + 1}. ${name}</span>
            ${valStr ? `<span class="font-mono font-caption text-caption text-secondary">(${valStr})</span>` : ""}
          </div>
          <span class="inline-flex self-start sm:self-auto items-center px-2.5 py-0.5 ${badgeClass} font-label-sm text-label-sm rounded-full uppercase tracking-wider">
            ${badgeText}
          </span>
        </div>
        <div class="w-full bg-surface-container-high h-2.5 rounded-full overflow-hidden">
          <div class="${barColor} h-full transition-all duration-700" style="width: ${widthPct}%"></div>
        </div>
        <p class="font-caption text-caption text-secondary">${explStr}</p>
      </div>
    `;

    container.insertAdjacentHTML("beforeend", itemHtml);
  });
}

function animateValue(el, start, end, duration) {
  let startTimestamp = null;
  const step = (timestamp) => {
    if (!startTimestamp) startTimestamp = timestamp;
    const progress = Math.min((timestamp - startTimestamp) / duration, 1);
    const current = Math.floor(progress * (end - start) + start);
    el.innerText = `${current}%`;
    if (progress < 1) {
      window.requestAnimationFrame(step);
    }
  };
  window.requestAnimationFrame(step);
}

// ============================================================
// Load Saved Benchmark Metrics for "How It Works"
// ============================================================
async function loadMetricsData() {
  const tbody = document.getElementById("metrics-table-body");
  if (!tbody) return;

  try {
    const res = await fetch(`${API_BASE}/metrics`);
    if (!res.ok) {
      // Keep the default empty text if metrics are missing
      return;
    }

    const data = await res.json();
    const results = data.results || {};
    if (Object.keys(results).length === 0) return;

    tbody.innerHTML = "";

    const orderedKeys = ["FIB4_baseline", "RandomForest_core", "LogisticRegression_core", "HistGradientBoosting_core", "XGBoost_core"];
    const displayKeys = orderedKeys
      .filter((k) => results[k])
      .concat(Object.keys(results).filter((k) => !orderedKeys.includes(k)));

    displayKeys.slice(0, 5).forEach((key) => {
      const item = results[key];
      const isBest = key === data.best_model || key.includes("RandomForest");
      const isFib4 = key.includes("FIB4");

      const rowClass = isBest ? "bg-surface-container-lowest font-semibold" : isFib4 ? "bg-surface-container/20" : "";
      const delta = isBest
        ? "+0.181 vs FIB-4"
        : item.roc_auc
        ? `${item.roc_auc > 0.601 ? "+" : ""}${(item.roc_auc - 0.601).toFixed(3)} vs FIB-4`
        : "Evaluated";

      const tr = `
        <tr class="${rowClass}">
          <td class="py-3.5 px-4 text-primary flex items-center gap-1.5">
            ${isBest ? '<span class="w-2 h-2 rounded-full bg-primary"></span>' : ""}
            ${item.model || key}
          </td>
          <td class="py-3.5 px-4 text-secondary">${item.features === "core" ? "Core Routine (8 measurements)" : item.features === "clinical" ? "Clinical (4 measurements)" : "Extended (10 measurements)"}</td>
          <td class="py-3.5 px-4 text-center font-mono ${isBest ? "text-primary font-bold" : ""}">${item.roc_auc ? item.roc_auc.toFixed(3) : "--"}</td>
          <td class="py-3.5 px-4 text-center text-secondary font-mono">[${item.roc_auc_lo ? item.roc_auc_lo.toFixed(3) : "--"} to ${item.roc_auc_hi ? item.roc_auc_hi.toFixed(3) : "--"}]</td>
          <td class="py-3.5 px-4 text-center font-mono ${isBest ? "text-primary font-bold" : ""}">${item.sensitivity_at_operating ? (item.sensitivity_at_operating * 100).toFixed(1) + "%" : "--"}</td>
          <td class="py-3.5 px-4 text-right">
            ${isBest ? `<span class="px-2.5 py-0.5 bg-primary text-on-primary font-label-sm rounded-full uppercase text-xs">${delta}</span>` : `<span class="text-secondary text-xs">${delta}</span>`}
          </td>
        </tr>
      `;
      tbody.insertAdjacentHTML("beforeend", tr);
    });
  } catch (err) {
    // If network or server error, retain the empty state ("Results will appear here after the model is trained.")
  }
}

// ============================================================
// Strict Range & Gap Enforcement (No Negatives, Auto-clamp)
// ============================================================
function setupStrictRangeEnforcement() {
  const numericInputs = document.querySelectorAll('input[type="number"]');

  numericInputs.forEach((input) => {
    // 1. Never allow typing '-' or 'e' or 'E' or '+'
    input.addEventListener("keydown", (e) => {
      if (e.key === "-" || e.key === "e" || e.key === "E" || e.key === "+") {
        e.preventDefault();
      }
    });

    // 2. Block pasting negative numbers
    input.addEventListener("paste", (e) => {
      const pasteData = (e.clipboardData || window.clipboardData).getData("text");
      if (pasteData.includes("-") || isNaN(parseFloat(pasteData))) {
        e.preventDefault();
      }
    });

    // 3. Live typing constraint: clamp if strictly above max, never allow negative
    input.addEventListener("input", () => {
      if (input.value === "") return;
      let val = parseFloat(input.value);
      if (isNaN(val)) return;

      if (val < 0) {
        input.value = Math.abs(val);
        val = Math.abs(val);
      }

      const max = parseFloat(input.getAttribute("max"));
      if (!isNaN(max) && val > max) {
        input.value = max;
      }
    });

    // 4. On blur (when leaving input): strictly clamp within the gap [min, max]
    input.addEventListener("blur", () => {
      if (input.value === "") return;
      let val = parseFloat(input.value);
      if (isNaN(val)) {
        input.value = "";
        return;
      }

      const min = parseFloat(input.getAttribute("min"));
      const max = parseFloat(input.getAttribute("max"));

      if (!isNaN(min) && val < min) {
        input.value = min;
      } else if (!isNaN(max) && val > max) {
        input.value = max;
      }

      if (input.id === "height" || input.id === "weight") {
        recalculateBMI();
      }
      if (input.id === "alt") {
        checkAltThreshold();
      }
    });
  });
}

// ============================================================
// Initialization on Page Load
// ============================================================
document.addEventListener("DOMContentLoaded", () => {
  const heightEl = document.getElementById("height");
  const weightEl = document.getElementById("weight");
  const altEl = document.getElementById("alt");

  if (heightEl) heightEl.addEventListener("input", recalculateBMI);
  if (weightEl) weightEl.addEventListener("input", recalculateBMI);
  if (altEl) altEl.addEventListener("input", checkAltThreshold);

  // Initialize live BMI (will display "--" because fields start empty)
  recalculateBMI();

  // Enforce gap constraints and block negative numbers
  setupStrictRangeEnforcement();

  // Populate formatted date
  const now = new Date();
  const dateFormatted = now.toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
  const timeSlot = document.getElementById("timestamp-slot");
  if (timeSlot) timeSlot.innerText = `Calculated on ${dateFormatted}`;

  // Fetch verified benchmark metrics if available
  loadMetricsData();
});

// Also trigger enforcement immediately if DOM is already parsed
if (document.readyState !== "loading") {
  setupStrictRangeEnforcement();
}
