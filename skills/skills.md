# Machine Learning (ML) Code Review Guide & Specifications

This guide establishes the comprehensive review framework, code patterns, diagnostic questions, and anti-pattern checklists across all 11 critical ML dimensions.

---

## 📑 Core Review Dimensions

1. [Data Leakage & Train/Test Contamination](#1-data-leakage--traintest-contamination)
2. [Incorrect Preprocessing & Pipelines](#2-incorrect-preprocessing--pipelines)
3. [Feature Leakage & Future Information](#3-feature-leakage--future-information)
4. [Bad Validation Strategy](#4-bad-validation-strategy)
5. [Metric Mismatch & Thresholding](#5-metric-mismatch--thresholding)
6. [Reproducibility & Determinism](#6-reproducibility--determinism)
7. [Random Seed Management](#7-random-seed-management)
8. [Model Serialization & Security](#8-model-serialization--security)
9. [Inference / Training Mismatch (Train-Serve Skew)](#9-inference--training-mismatch-train-serve-skew)
10. [Data Imbalance & Class Disparity](#10-data-imbalance--class-disparity)
11. [WorkforceOS Domain & Compliance Rules](#11-workforceos-domain--compliance-rules)

---

## 🔍 1. Data Leakage & Train/Test Contamination

Data leakage occurs when information from outside the training dataset (test set, validation set, or future data) influences the creation or training of the model.

### Diagnostic Checklist:
- [ ] Is `train_test_split()` performed **before** any feature transformations, scaling, or imputation?
- [ ] Are global statistics (mean, variance, min/max, category frequencies, target encodings) computed strictly on the training subset?
- [ ] In cross-validation, is preprocessing embedded inside each fold (e.g., via `sklearn.pipeline.Pipeline`)?

### ❌ Anti-Pattern (Leakage) vs. ✅ Best Practice:
```python
# ❌ BAD: Fit scaler on full dataset prior to splitting (Leakage!)
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)
X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2)

# ✅ GOOD: Fit strictly on training split, transform both
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)
```

---

## ⚙️ 2. Incorrect Preprocessing & Pipelines

Preprocessing steps must be deterministic, preserve sample alignments, handle missing values appropriately, and prevent silent index errors.

### Diagnostic Checklist:
- [ ] Are transformations encapsulated in reusable estimators or pipelines?
- [ ] Does categorical encoding handle unseen categories at test/inference time (`handle_unknown='ignore'`)?
- [ ] Are missing values imputed using training distributions rather than arbitrary constants that bias distributions?
- [ ] Is dataframe index alignment preserved after filtering or concatenation?

### ❌ Anti-Pattern vs. ✅ Best Practice:
```python
# ❌ BAD: Ad-hoc manual transforms without fallback for new categories
df['dept_code'] = df['department'].map({'Engineering': 0, 'HR': 1, 'Sales': 2}) # Produces NaN for new depts

# ✅ GOOD: Scikit-learn OneHotEncoder / TargetEncoder with unknown category handling
from sklearn.preprocessing import OneHotEncoder
encoder = OneHotEncoder(handle_unknown='ignore', sparse_output=False)
X_train_encoded = encoder.fit_transform(X_train[['department']])
X_test_encoded = encoder.transform(X_test[['department']])
```

---

## 🔮 3. Feature Leakage & Future Information

Feature leakage occurs when features contain information that would not be available at the exact moment the model makes an inference prediction in production.

### Diagnostic Checklist:
- [ ] Are features strictly computed using data recorded prior to the prediction timestamp?
- [ ] Are target proxies excluded (e.g., `exit_interview_notes` or `badge_deactivation_timestamp` when predicting employee turnover)?
- [ ] Are window/lag aggregations strictly backward-looking (`closed='left'` or strictly shifted by 1 period)?

### ❌ Anti-Pattern vs. ✅ Best Practice:
```python
# ❌ BAD: Rolling 30-day average includes the current/future day's data
df['avg_overtime_30d'] = df.groupby('emp_id')['overtime_hours'].transform(lambda x: x.rolling(30).mean())

# ✅ GOOD: Shift by 1 so only strictly historical days are aggregated
df['avg_overtime_30d'] = df.groupby('emp_id')['overtime_hours'].transform(lambda x: x.shift(1).rolling(30).mean())
```

---

## 📐 4. Bad Validation Strategy

A validation strategy that does not mirror the real-world deployment scenario produces misleadingly optimistic performance estimates.

### Diagnostic Checklist:
- [ ] **Temporal Data**: Uses `TimeSeriesSplit` or out-of-time validation instead of random k-fold shuffling.
- [ ] **Grouped Data**: If samples share an entity (e.g., multiple records per employee), use `GroupKFold` or `LeaveOneGroupOut` to prevent cross-split subject leakage.
- [ ] **Stratification**: Imbalanced classification uses `StratifiedKFold` or `stratify=y` in splits.

### ❌ Anti-Pattern vs. ✅ Best Practice:
```python
# ❌ BAD: Random K-Fold on sequential employee records leaks historical patterns
from sklearn.model_selection import KFold
cv = KFold(n_splits=5, shuffle=True)

# ✅ GOOD: GroupKFold ensuring all records of any single employee remain in one split
from sklearn.model_selection import GroupKFold
cv = GroupKFold(n_splits=5)
for train_idx, val_idx in cv.split(X, y, groups=X['employee_id']):
    ...
```

---

## 🎯 5. Metric Mismatch & Thresholding

Using the wrong metric optimizes for the wrong business objective and masks severe performance flaws.

### Diagnostic Checklist:
- [ ] **Imbalanced Classes**: Never rely on raw `Accuracy`. Use `PR-AUC`, `F1-score (macro/weighted)`, `Brier Score`, or `Average Precision`.
- [ ] **Cost Asymmetry**: Are false negatives and false positives weighted based on business impact?
- [ ] **Threshold Optimization**: Is the decision threshold tuned on a validation set (not the test set) rather than defaulting to `0.5`?
- [ ] **Probability Calibration**: If probabilities represent risk scores (e.g. employee attrition risk), are they calibrated using reliability curves?

### ❌ Anti-Pattern vs. ✅ Best Practice:
```python
# ❌ BAD: 98% accuracy on 2% positive class (a dummy model predicting all 0s gets 98%)
print(f"Accuracy: {accuracy_score(y_test, y_pred)}")

# ✅ GOOD: Inspect Precision-Recall curve, Average Precision, and tuned threshold
from sklearn.metrics import classification_report, average_precision_score, precision_recall_curve
ap = average_precision_score(y_test, y_prob)
precision, recall, thresholds = precision_recall_curve(y_test, y_prob)
# Select optimal threshold maximizing F1 or custom cost matrix on validation set
```

---

## 🔄 6. Reproducibility & Determinism

ML experiments must be repeatable across different runs, machines, and environments.

### Diagnostic Checklist:
- [ ] Are environment configurations and library versions pinned (`requirements.txt`, `poetry.lock`)?
- [ ] Are non-deterministic multithreaded operations (e.g., OpenMP, MKL, PyTorch non-deterministic ops) configured?
- [ ] Are data loaders configured with deterministic worker seeding?

---

## 🎲 7. Random Seed Management

A single unseeded generator will cause model weights, splits, and augmentation to vary unpredictably.

### Diagnostic Checklist:
- [ ] Is a global `seed_everything` function called at the start of scripts and pipelines?
- [ ] Are seeds passed to third-party algorithms (`RandomForest(random_state=42)`, `XGBClassifier(random_state=42)`)?

### ✅ Standard Seeding Helper:
```python
import os
import random
import numpy as np

def seed_everything(seed: int = 42) -> None:
    random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)
    np.random.seed(seed)
    try:
        import torch
        torch.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False
    except ImportError:
        pass
```

---

## 💾 8. Model Serialization & Security

Improper serialization causes arbitrary code execution vulnerabilities, version incompatibility, or missing preprocessing artifacts.

### Diagnostic Checklist:
- [ ] **Security**: Avoid unverified `pickle` / `cPickle` for model loading from untrusted sources.
- [ ] **Modern Formats**: Use `safetensors`, `ONNX`, or `joblib` with checksum validation.
- [ ] **Atomic Bundling**: Does the saved artifact bundle both the fitted feature pipeline AND the model estimator?
- [ ] **Metadata**: Are model version, training timestamp, git commit hash, and input schema stored alongside the model weights?

### ❌ Anti-Pattern vs. ✅ Best Practice:
```python
# ❌ BAD: Saving raw model estimator without its preprocessing pipeline
joblib.dump(raw_model, "model.pkl") # Incoming data at inference won't know how to transform

# ✅ GOOD: Save end-to-end Pipeline with metadata
pipeline = Pipeline([
    ('preprocessor', preprocessor),
    ('classifier', model)
])
pipeline.fit(X_train, y_train)
joblib.dump({
    'version': '1.2.0',
    'pipeline': pipeline,
    'input_schema': ['tenure_months', 'overtime_hours', 'performance_rating'],
    'sha256': '...'
}, "attrition_model_v1.2.joblib")
```

---

## ⚡ 9. Inference / Training Mismatch (Train-Serve Skew)

Train-serve skew is the discrepancy between performance during training and performance in production, caused by differences in data processing or environment.

### Diagnostic Checklist:
- [ ] Does the inference endpoint reuse the exact same preprocessing pipeline object as training (rather than re-implementing logic in SQL or backend code)?
- [ ] Are missing values and type coercions in incoming HTTP payloads handled identically to training data?
- [ ] Are default fallback values for nulls consistent between training and inference?
- [ ] Is input schema validated strictly via Pydantic or TypedDict?

---

## ⚖️ 10. Data Imbalance & Class Disparity

Severe class imbalance leads to biased predictors that ignore the minority class.

### Diagnostic Checklist:
- [ ] **Loss Weighting**: Are loss functions adjusted for class weights (`class_weight='balanced'`, `scale_pos_weight` in XGBoost, `pos_weight` in BCEWithLogitsLoss)?
- [ ] **Resampling**: If using SMOTE or random oversampling, verify oversampling occurs **only on the training split inside cross-validation loops**.
- [ ] **Calibration & Decision Cutoffs**: Is the positive classification threshold adjusted based on the operational cost of false positives vs. false negatives?

---

## 🏢 11. WorkforceOS Domain & Compliance Rules

When reviewing ML models and insights services in **WorkforceOS** (such as turnover risk, attendance anomaly detection, payroll forecasting):

1. **Fairness & Non-Discrimination**:
   - Ensure protected attributes (gender, age, marital status, religion, nationality, disability) are **strictly excluded** from feature inputs and cannot be reconstructed via high-correlation proxies.
2. **Explainability & Transparency**:
   - Every risk score (e.g., `attrition_risk: 0.82`) must output interpretable contributing factors (e.g., `['high_overtime', 'tenure_milestone', 'stagnant_compensation']`) using SHAP or permutation importances.
3. **Audit Trail**:
   - Automated triggers and predictions must log execution events to `AuditLogService` with model version and operator context.
