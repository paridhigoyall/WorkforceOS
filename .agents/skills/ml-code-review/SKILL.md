---
name: ml-code-review
description: >-
  Review Machine Learning (ML), Deep Learning (DL), and Data Science code for data leakage,
  train/test contamination, incorrect preprocessing, feature leakage, bad validation strategies,
  metric mismatch, reproducibility, random seeds, model serialization, train-serve skew, and data imbalance.
  Use when reviewing ML training scripts, data preprocessing pipelines, model architectures, or inference endpoints.
---

# ML Code Review Skill

This skill provides an automated, structured methodology for auditing Machine Learning (ML), Deep Learning (DL), and Data Science code.

## 🎯 11-Point Review Workflow

When evaluating ML code, systematically audit against these 11 dimensions:

1. **Data Leakage**: Ensure train/test split happens strictly *before* any transformer/imputer/encoder fitting.
2. **Train/Test Contamination**: Prevent cross-fold information bleeding by embedding transformers inside `Pipeline` objects.
3. **Incorrect Preprocessing**: Handle unseen categories with `handle_unknown='ignore'`; avoid silent NaN introductions.
4. **Feature Leakage**: Prohibit features containing post-event proxies or future information; shift rolling windows (`.shift(1)`).
5. **Validation Strategy**: Use `TimeSeriesSplit` for temporal data and `GroupKFold` when multiple records share an entity ID.
6. **Metric Mismatch**: Ban raw accuracy on imbalanced classes; require PR-AUC, F1-Score (macro/weighted), Average Precision, or Brier score.
7. **Reproducibility**: Pin library versions and enforce deterministic algorithms.
8. **Random Seeds**: Provide a global `seed_everything()` setting seeds across `random`, `numpy`, `torch`, and estimator arguments.
9. **Model Serialization**: Require atomic packaging of preprocessor + model (avoid bare estimator dumps); use `safetensors`/`ONNX`/verified `joblib`.
10. **Inference/Training Mismatch**: Eliminate train-serve skew by reusing the exact training pipeline at inference time; validate schemas strictly with Pydantic.
11. **Data Imbalance**: Adjust loss weighting (`class_weight='balanced'`, `scale_pos_weight`) and calibrate probability thresholds.

## 🏢 WorkforceOS Compliance
- **Protected Attributes**: Verify no protected demographic proxies are used in scoring.
- **Explainability**: Output risk breakdown factors (SHAP / feature contributions).
- **Auditing**: Log all automated scoring events via `AuditLogService`.
