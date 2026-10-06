/**
 * LiverCheck – Centralized User-Facing Strings
 * ==============================================
 * Every piece of text shown to the user is kept here in plain human language.
 * No marketing hype, no stacked adjectives, no exclamation marks, no emoji.
 */

const UI_STRINGS = {
  // Brand and Header
  brandName: "LiverCheck",
  headerTagline: "Educational screening tool. Not a medical diagnosis.",
  navCalculator: "Calculator",
  navResults: "Results",
  navHowItWorks: "How it works",

  // Calculator Page
  calcBadge: "Student Machine Learning Project · NHANES Data",
  calcTitle: "Liver Scarring Risk Check",
  calcSubtitle: "Enter common blood test numbers and body measurements to estimate the chance of liver scarring (fibrosis). It takes about two minutes. No data is stored.",

  // Form Section 1: About You
  sectionAboutTitle: "About you",
  sectionAboutSubtitle: "Basic information",
  ageLabel: "Age",
  ageHint: "Years (18 to 85)",
  ageUnit: "years",
  ageExplanation: "Liver risk formulas need your current age.",
  sexLabel: "Biological sex",
  sexHint: "Used to set baseline enzyme ranges.",
  sexMale: "Male",
  sexFemale: "Female",

  // Form Section 2: Body Measurements
  sectionBodyTitle: "Body measurements",
  sectionBodySubtitle: "Weight and waist measurements",
  heightLabel: "Height",
  heightUnit: "cm",
  weightLabel: "Weight",
  weightUnit: "kg",
  waistLabel: "Waist circumference",
  waistUnit: "cm",
  waistTip: "Measure around your waist level with your belly button while breathing out gently.",
  bmiTitle: "Calculated Body Mass Index (BMI)",
  bmiEmpty: "Enter height and weight",
  bmiUnderweight: "Underweight",
  bmiNormal: "Normal range",
  bmiOverweight: "Overweight",
  bmiObesity: "Higher weight range",

  // Form Section 3: Blood Test Results
  sectionBloodTitle: "Blood test results",
  sectionBloodSubtitle: "From your routine metabolic panel or hepatic function panel.",
  labGuideButton: "Where to find these numbers on your lab report",
  altLabel: "ALT (Alanine Aminotransferase)",
  altUnit: "U/L",
  altNormal: "Standard range: 7 to 56 U/L",
  altExplanation: "An enzyme your liver releases when liver cells are irritated or injured.",
  astLabel: "AST (Aspartate Aminotransferase)",
  astUnit: "U/L",
  astNormal: "Standard range: 10 to 40 U/L",
  astExplanation: "An enzyme found in liver and muscle cells. The ratio of AST to ALT helps check for scarring.",
  ggtLabel: "GGT (Gamma-glutamyl Transferase)",
  ggtUnit: "U/L",
  ggtNormal: "Standard range: 9 to 48 U/L",
  ggtExplanation: "An enzyme that rises when bile ducts or liver tissue are under stress.",
  plateletsLabel: "Platelet count",
  plateletsUnit: "x1000/µL",
  plateletsNormal: "Standard range: 150 to 400",
  plateletsExplanation: "Blood cells that help clotting. A lower count can happen when a stiff liver slows blood flow.",

  // Optional Fasting Tests
  fastingAccordionTitle: "Optional fasting tests",
  fastingAccordionSubtitle: "Adds triglycerides and glucose if you have them.",
  fastingDescription: "If your lab test included a fasting lipid or metabolic panel, you can add these two numbers.",
  triglyceridesLabel: "Triglycerides",
  triglyceridesUnit: "mmol/L",
  glucoseLabel: "Fasting glucose",
  glucoseUnit: "mg/dL",

  // Buttons & Privacy
  calculateButton: "Calculate risk estimate",
  calculatingButton: "Calculating...",
  clearButton: "Start over",
  privacyNotice: "Zero data storage. Your numbers stay in your browser session only.",

  // Validation & Error Messages
  errMissingFields: "Please fill in all required fields: ",
  errAgeRange: "Age must be between 18 and 85 years.",
  errHeightRange: "Height must be between 100 and 240 cm.",
  errWeightRange: "Weight must be between 30 and 300 kg.",
  errWaistRange: "Waist must be between 40 and 200 cm.",
  errPositiveEnzymes: "Enzyme and platelet numbers must be positive numbers.",
  errSelectSex: "Please select biological sex.",
  altWarningHigh: "This number looks unusually high. Please double check the unit on your lab report.",

  // Sidebar Helper Cards
  sidebarUseTitle: "How to use this tool",
  sidebarStep1: "Find your most recent blood test from the past 12 months.",
  sidebarStep2: "Check that the units match: U/L for liver enzymes, x1000/µL for platelets.",
  sidebarStep3: "Bring the final result to discuss with your doctor.",
  sidebarWhyTitle: "Why screen for liver scarring",
  sidebarWhyBody1: "Liver scarring develops slowly and rarely causes symptoms in early stages.",
  sidebarWhyBody2: "Routine blood tests combined with waist size can flag early changes years before serious trouble appears.",

  // Lab Guide Modal
  modalTitle: "How to read your lab report",
  modalSubtitle: "Where to locate ALT, AST, GGT, and Platelets.",
  modalBody: "ALT and AST appear on a standard metabolic panel (CMP) or liver function panel. In some labs, ALT is called SGPT, and AST is called SGOT. Platelets appear on a complete blood count (CBC).",
  modalCloseButton: "Close guide",

  // Results Page - Empty State
  resultsEmptyTitle: "No calculation yet",
  resultsEmptyBody: "Enter your test numbers in the Calculator and press calculate to view your estimate here.",
  resultsEmptyButton: "Go to Calculator",

  // Results Page - Populated State
  resultsTitle: "Screening Summary",
  resultsNotice: "Calculated from your inputs",
  probLabel: "Estimated probability of significant liver scarring (stiffness 8 kPa or higher on transient elastography).",

  // Risk Interpretations (Calm, Honest, No Hype)
  riskLowBadge: "Low Risk",
  riskLowStage: "Stage F0 to F1 range",
  riskLowHeadline: "Low chance of significant liver scarring",
  riskLowNarrative: "Your numbers suggest a low chance of liver scarring. Only a doctor can confirm this. Continue routine checkups and healthy daily habits.",
  riskLowAction: "Routine checkup recommended.",

  riskModBadge: "Moderate Risk",
  riskModStage: "Stage F2 range",
  riskModHeadline: "Moderate chance of liver scarring",
  riskModNarrative: "Your numbers suggest a moderate chance of liver scarring. A doctor should review these findings and decide if an ultrasound or FibroScan test is needed.",
  riskModAction: "Schedule a non-urgent visit with your doctor.",

  riskHighBadge: "Higher Concern",
  riskHighStage: "Stage F3 to F4 range",
  riskHighHeadline: "Higher chance of liver scarring",
  riskHighNarrative: "Your numbers suggest an increased chance of liver scarring or ongoing liver inflammation. You should discuss these results promptly with a doctor or liver specialist.",
  riskHighAction: "Prompt medical consultation recommended.",

  // Comparison Card
  compareTitle: "Comparison to standard FIB-4",
  compareSubtitle: "How this machine learning model compares to the traditional formula.",
  compareMLTitle: "LiverCheck Model (Random Forest)",
  compareMLDesc: "Combines blood tests with waist circumference and BMI.",
  compareFib4Title: "Standard FIB-4 Score",
  compareFib4Desc: "A standard clinical equation based only on Age, AST, ALT, and Platelets.",
  compareNote: "FIB-4 is widely used by doctors. LiverCheck adds body measurements to reduce missed early cases.",

  // Factor Breakdown Card
  factorsTitle: "What influenced your result",
  factorsSubtitle: "The measurements that had the biggest impact on this calculation.",
  increasesRisk: "Increases risk",
  lowersRisk: "Lowers risk",
  neutralRisk: "Neutral impact",

  // Action Steps Card
  actionTitle: "Sensible next steps",
  actionSubtitle: "General health advice based on liver screening guidelines.",
  stepDoctorTitle: "Talk with your primary doctor",
  stepDoctorDesc: "Show your doctor this summary. They can order follow-up blood tests or an ultrasound if appropriate.",
  stepFoodTitle: "Focus on wholesome foods",
  stepFoodDesc: "Eat more vegetables, beans, nuts, whole grains, and fish. Cut back on ultra-processed snacks and added sugars.",
  stepDrinksTitle: "Limit alcohol and sugary drinks",
  stepDrinksDesc: "Alcohol and high-fructose corn syrup put extra stress on liver cells.",
  stepMoveTitle: "Stay physically active",
  stepMoveDesc: "Aim for about 30 minutes of brisk walking or other moderate exercise most days of the week.",

  // Warning Alert
  warningUrgentTitle: "When to see a doctor right away",
  warningUrgentBody: "Seek medical care promptly if you notice yellow skin or eyes (jaundice), swelling in your legs or belly, dark urine, or unusual mental confusion.",

  // Results Buttons
  printButton: "Print or save PDF",
  editButton: "Edit my numbers",
  resetButton: "Start over",
  resultsDisclaimer: "Educational use only. This tool is not a medical device. It cannot diagnose or rule out liver disease. Always consult a qualified healthcare professional.",

  // How It Works Page
  howTitle: "How LiverCheck works",
  howSubtitle: "A student machine learning project using public survey data to explore non-invasive liver screening.",
  howSection1Title: "1. What it measures",
  howSection1Body: "The model looks at three main aspects of your health:",
  howItem1Title: "Liver cell stress",
  howItem1Body: "ALT, AST, and GGT. These enzymes leak into the blood when liver cells or bile ducts are under strain.",
  howItem2Title: "Platelets and age",
  howItem2Body: "Platelets drop when a stiff liver causes blood to back up into the spleen.",
  howItem3Title: "Metabolic factors",
  howItem3Body: "BMI and waist size. Extra fat around the belly is closely linked to fat deposits in the liver.",

  howSection2Title: "2. How the model was trained",
  howSection2Body: "We used data from the US National Health and Nutrition Examination Survey (NHANES). The training set comes from the 2017 to 2018 survey cycle (4,746 adults). Each person had routine blood work and a FibroScan exam, which measures liver stiffness in kilopascals (kPa). We set the target to 8.0 kPa or higher, which indicates significant scarring.",

  howSection3Title: "3. Results on an independent test group",
  howSection3Body: "We tested the model on a completely separate group from the 2021 to 2023 NHANES survey (5,526 adults). The model was never trained or adjusted on these people.",

  howSection4Title: "4. Limitations to keep in mind",
  limitation1Title: "US data only",
  limitation1Body: "The model was trained on US adults and may not perform the same way in other countries.",
  limitation2Title: "FibroScan estimates, not biopsy",
  limitation2Body: "FibroScan is a safe, painless scan, but only a tissue biopsy can prove scarring definitively.",
  limitation3Title: "Acute illness can distort numbers",
  limitation3Body: "Recent heavy drinking, a viral infection, or new medications can spike liver enzymes temporarily.",
  limitation4Title: "Student research only",
  limitation4Body: "This tool was built to learn and test machine learning concepts. It has not been reviewed by health authorities.",

  howCtaTitle: "Ready to test your own numbers?",
  howCtaBody: "Enter values from your last routine blood test. All calculations run in your browser.",
  howCtaButton: "Open Calculator",

  footerCopyright: "LiverCheck Student AI/ML Project.",
  footerNotice: "Built for education and learning. Not for medical treatment decisions."
};

// Expose globally
window.UI_STRINGS = UI_STRINGS;
