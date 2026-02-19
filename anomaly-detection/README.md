# Data Exploration and Anomaly Detection in Wholesale Customer Data

Two independent approaches to anomaly detection on the same dataset, developed at two different universities using distinct methodologies.

## Overview

This project applies exploratory data analysis and unsupervised anomaly detection to the [UCI Wholesale Customers dataset](https://archive.ics.uci.edu/ml/datasets/Wholesale+customers). The goal is to identify customers with abnormal spending patterns across six product categories and provide interpretable insights into what drives those anomalies.

## Dataset

**Source:** UCI Machine Learning Repository — Wholesale Customers Data Set

The dataset contains annual spending data for 440 wholesale customers across 8 attributes:

| Feature | Description |
|---------|-------------|
| `Channel` | Customer type (1 = Hotel/Restaurant/Cafe, 2 = Retail) |
| `Region` | Geographic region (1 = Lisbon, 2 = Oporto, 3 = Other) |
| `Fresh` | Annual spending on fresh products |
| `Milk` | Annual spending on milk and dairy products |
| `Grocery` | Annual spending on grocery items |
| `Frozen` | Annual spending on frozen products |
| `Detergents_Paper` | Annual spending on detergents and paper products |
| `Delicassen` | Annual spending on delicatessen items |

---

## Approach 1: Softmin Scoring with LRP Explainability (FU Berlin)

> Notebook: `Anomaly_Detection_P1.ipynb`

### Preprocessing
- Log transformation with offset 10 to normalize heavily skewed distributions (e.g., Delicassen skewness: 11.11 → −0.74)
- StandardScaler for zero mean and unit variance

### Anomaly Detection — Softmin Scoring

Instead of simple nearest-neighbor distance, this approach uses a weighted sum of distances to all instances:

```
A(i) = -(1/γ) × log( (1/(n-1)) × Σ exp(-γ × ||xᵢ - xⱼ||²) )
```

This provides a smoother, more robust anomaly score than hard nearest-neighbor methods. A naive Euclidean distance baseline was computed first for comparison.

### Gamma Selection via Bootstrapping

Evaluated γ ∈ {0.05, 0.1, 0.5, 1.0, 10.0} using 50 bootstrap samples of size 440:
- Designed a **profit function**: `std(mean_scores) - mean(spread_scores)` — maximizing separation while minimizing variance
- Also tested an alternative metric: `(mean - median) / mean(spread)` to verify consistency
- **γ = 0.1** selected as optimal (profit score: 5.68 vs. 0.01 for γ = 10)

### Metadata-Driven Analysis

Investigated how anomalies shift when subsetting by Channel and Region:

**By Channel:**
- Indirect customers (n=298) dominate full-dataset anomalies; Direct customers (n=142) reveal different top anomalies when isolated
- Anomaly scores drop significantly for Direct customers in isolation, suggesting channel-specific spending norms

**By Region:**
- Full-dataset anomalies are mostly from "Other regions" (n=316)
- Lisbon (n=77) and Oporto (n=47) reveal unique anomalous customers when analyzed separately
- Subsetting by region can skew results due to sample size imbalance

### Feature-Level Explainability (LRP)

Applied Layer-wise Relevance Propagation to decompose each anomaly score into per-feature contributions:

```
R_feature(i, f) = Σⱼ [(xⱼf - xᵢf)² / ||xⱼ - xᵢ||²] × R(i, j)
```

Key findings:
- **Customer 338** (score: 56.41): Driven by extremely low Fresh spending (R_Fresh = 29.5)
- **Customer 154** (score: 52.17): Uniformly anomalous across all features
- **Customer 75** (score: 43.10): Almost entirely driven by low Grocery spending (R_Grocery = 29.0)
- **Customer 183** (score: 36.05): Dominated by exceptionally high Delicassen spending (R_Delicassen = 13.5)

---

## Approach 2: PCA + One-Class SVM (BTU Cottbus-Senftenberg)

> Notebooks: `Anomaly Detection.ipynb`, `Anomalies_PCA_OCSVM.ipynb`
>
> Course: Data Exploration and System Management Using AI/ML (WiSe 24/25)

### Preprocessing
- Log transformation with offset 10 (same as Approach 1)
- StandardScaler normalization
- Correlation analysis: Detergents_Paper and Grocery exhibited strong positive correlation (r > 0.9), motivating dimensionality reduction

### Dimensionality Reduction with PCA

Reduced 6 spending features to 2 principal components:
- PC1 explained **44.1%** of variance, PC2 explained **28.4%** (total: 72.5%)
- Addressed multicollinearity flagged in the correlation matrix
- Enabled 2D visualization of the data distribution

### Anomaly Detection — One-Class SVM

Trained a One-Class SVM on PCA-transformed data:
- RBF kernel with `gamma='auto'` and `nu=0.05` (targeting ~5% anomaly rate)
- Anomalies visualized on the PCA scatter plot with distinct colors
- Identified 30 anomalous instances (< 5% of data) representing unusual spending patterns

### Benchmark — Linear Regression

Tested the predictive quality of PCA features using a Linear Regression model to predict the Fresh feature:

| Metric | Training | Testing |
|--------|----------|---------|
| RMSE | 0.86 | 1.02 |
| R² | 0.66 | 0.60 |
| MAE | 0.66 | 0.76 |

Results suggest PCA preserved reasonable predictive power but left room for improvement in generalization.

---

## Comparison of Both Approaches

| Aspect | Approach 1 (FU Berlin) | Approach 2 (BTU) |
|--------|----------------------|------------------|
| **Detection Method** | Softmin scoring (distance-based) | One-Class SVM (kernel-based) |
| **Feature Space** | Full 6D feature space | Reduced 2D (PCA) |
| **Hyperparameter Tuning** | Bootstrapped gamma selection with profit function | Fixed `nu=0.05`, `gamma='auto'` |
| **Robustness Validation** | 50 bootstrap samples, spread analysis | Single-run detection |
| **Explainability** | LRP decomposition per feature | PCA scatter plot visualization |
| **Metadata Analysis** | Subset analysis by Channel and Region | Not explored |
| **Anomaly Count** | Continuous scores (top-k ranking) | Binary classification (~30 anomalies) |
| **Key Strength** | Deep interpretability — identifies *why* each customer is anomalous | Simplicity — quick visual separation in 2D |
| **Key Limitation** | O(n²) computational cost | PCA loses 27.5% variance; no per-feature explanation |

### Overlap in Findings

Both approaches consistently flag certain customers as anomalous — most notably Customer 338, which emerges as the top anomaly in Approach 1 (score: 56.41) and is also detected by One-Class SVM. The softmin approach provides deeper insight into *why* — for Customer 338, it's driven primarily by extremely low Fresh spending — while the PCA+SVM approach offers a quick geometric view of how anomalies sit relative to the main data cluster.

---

## Project Structure

```
anomaly-detection/
├── README.md
├── Anomaly_Detection_P1.ipynb           # Approach 1: Softmin scoring + LRP (FU Berlin)
├── Anomaly Detection.ipynb              # Approach 2: PCA + One-Class SVM (BTU)
├── Anomalies_PCA_OCSVM.ipynb            # Approach 2: Extended PCA + OCSVM analysis
└── Wholesale customers data.csv         # UCI Wholesale Customers dataset
```

## Tech Stack

- **Python** — NumPy, pandas, scikit-learn, SciPy, Matplotlib, Seaborn
- **Anomaly Detection** — Softmin scoring, One-Class SVM
- **Explainability** — Layer-wise Relevance Propagation (LRP)
- **Dimensionality Reduction** — PCA
- **Validation** — Bootstrapping, Linear Regression benchmark

## References

- Dua, D. and Graff, C. (2019). UCI Machine Learning Repository
- Montavon, G. et al. (2019). Layer-wise Relevance Propagation
- Pedregosa, F. et al. Scikit-learn: Machine Learning in Python. JMLR, 12, 2825–2830
- Jolliffe, I.T. and Cadima, J. (2016). Principal component analysis: a review and recent developments
