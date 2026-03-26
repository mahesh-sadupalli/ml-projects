<div align="center">

# Fourier Neural Operator for Dynamical Systems

[![PyTorch](https://img.shields.io/badge/PyTorch-2.0+-ee4c2c?logo=pytorch&logoColor=white)](https://pytorch.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![ETH Zurich](https://img.shields.io/badge/ETH%20Z%C3%BCrich-AI4Science-1e3a5f?logo=data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAiIGhlaWdodD0iMjAiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PHJlY3Qgd2lkdGg9IjIwIiBoZWlnaHQ9IjIwIiBmaWxsPSIjMWUzYTVmIi8+PHRleHQgeD0iMyIgeT0iMTUiIGZvbnQtc2l6ZT0iMTIiIGZpbGw9IndoaXRlIiBmb250LWZhbWlseT0iQXJpYWwiIGZvbnQtd2VpZ2h0PSJib2xkIj5FPC90ZXh0Pjwvc3ZnPg==)](https://camlab-ethz.github.io/ai4s-course/)
[![Python](https://img.shields.io/badge/Python-3.10+-3776ab?logo=python&logoColor=white)](https://python.org)

**Learning PDE dynamics directly from data using neural operators that generalize across spatial resolutions.**

Part of the [AI in the Sciences and Engineering](https://camlab-ethz.github.io/ai4s-course/) course at ETH Zurich.

<img src="figures/08_ground_truth_3d_sample1.png" width="55%" alt="3D spatiotemporal surface of dynamical system"/>

</div>

---

## The Problem

We are given trajectories from an **unknown dynamical system**:

$$\frac{\partial u}{\partial t} = \mathcal{D}(u(x,t)), \quad t \in (0,1], \; x \in [0,1]$$

with boundary conditions $u(0,t) = u(1,t) = 0$ and initial condition $u(x,0) = u_0(x)$.

We don't know $\mathcal{D}$. We only have **snapshot data** — solutions sampled at $t \in \{0, 0.25, 0.50, 0.75, 1.0\}$ across 1024 trajectories. The goal: learn an operator that maps initial conditions to future states, **purely from data**.

> This is the central promise of neural operators — replacing expensive numerical solvers with learned surrogates that are orders of magnitude faster at inference.

<details>
<summary><b>Dataset Samples</b> — click to expand</summary>
<br/>
<div align="center">
<img src="figures/01_dataset_samples.png" width="90%" alt="Training dataset sample trajectories"/>
</div>

6 representative trajectories from the training set. Each curve shows the solution $u(x, t)$ at 5 time snapshots, revealing diverse wave propagation and diffusion patterns.
</details>

---

## Why Fourier Neural Operators?

### The Limitation of Standard Neural Networks

A standard neural network (e.g., an MLP or CNN) learns a **fixed-dimensional function**:

$$f_\theta : \mathbb{R}^n \to \mathbb{R}^m$$

If you train on a 128-point grid, the network is locked to that grid. Change the resolution and you need to retrain. This is fundamentally limiting for physical systems that exist in continuous space.

### From Functions to Operators

Physical systems are governed by **operators** — mappings between infinite-dimensional function spaces:

$$\mathcal{G}^\dagger : \mathcal{A} \to \mathcal{U}$$

where $\mathcal{A}$ is the space of input functions (e.g., initial conditions) and $\mathcal{U}$ is the space of solutions. Neural operators learn this mapping directly.

```mermaid
graph LR
    A["Input Function Space 𝒜<br/>(initial conditions)"] -->|"𝒢<sub>θ</sub> (learned operator)"| B["Output Function Space 𝒰<br/>(solution fields)"]

    style A fill:#4a90d9,stroke:#2c5f8a,color:#fff,rx:10
    style B fill:#d94a4a,stroke:#8a2c2c,color:#fff,rx:10
```

### The Fourier Layer — Core Innovation

The key insight behind FNO is that many PDE operators are **diagonal in Fourier space**. Instead of learning convolution kernels in physical space (which is local), FNO learns **global interactions in the frequency domain**.

Each Fourier layer performs:

$$v_{l+1}(x) = \sigma\Big(W_l \, v_l(x) + \mathcal{F}^{-1}\big(R_l \cdot \mathcal{F}(v_l)\big)(x)\Big)$$

where:
- $\mathcal{F}$ / $\mathcal{F}^{-1}$ — Fast Fourier Transform and its inverse
- $R_l$ — learnable weight tensor in Fourier space (truncated to $k_{\max}$ modes)
- $W_l$ — pointwise linear transform (local path)
- $\sigma$ — nonlinear activation (GELU)

```mermaid
graph LR
    subgraph "Fourier Layer"
        direction TB
        IN["v(x)"] --> SPLIT1["  "]
        SPLIT1 -->|"Global Path"| FFT["FFT  𝓕"]
        FFT --> FILTER["Spectral Filter  R<sub>l</sub>"]
        FILTER --> IFFT["Inverse FFT  𝓕⁻¹"]
        SPLIT1 -->|"Local Path"| W["Linear  W"]
        IFFT --> ADD["⊕"]
        W --> ADD
        ADD --> ACT["σ (GELU)"]
        ACT --> OUT["v'(x)"]
    end

    style FFT fill:#6c5ce7,stroke:#4a3db5,color:#fff
    style FILTER fill:#6c5ce7,stroke:#4a3db5,color:#fff
    style IFFT fill:#6c5ce7,stroke:#4a3db5,color:#fff
    style W fill:#00b894,stroke:#008c6e,color:#fff
    style ADD fill:#fdcb6e,stroke:#d4a94a,color:#333
    style ACT fill:#fd79a8,stroke:#c45a87,color:#fff
    style IN fill:#dfe6e9,stroke:#b2bec3,color:#333
    style OUT fill:#dfe6e9,stroke:#b2bec3,color:#333
    style SPLIT1 fill:none,stroke:none
```

### Resolution Invariance

Because the Fourier transform is defined on continuous functions and we only keep the lowest $k_{\max}$ modes, the learned operator **transfers across resolutions**. Train on 128 points, evaluate on 32 or 256 — the same weights work because the spectral representation is resolution-agnostic.

```mermaid
graph LR
    subgraph "Same Learned Weights"
        A32["32 points"] --> FNO["FNO  𝒢<sub>θ</sub>"]
        A64["64 points"] --> FNO
        A96["96 points"] --> FNO
        A128["128 points"] --> FNO
        FNO --> P32["Prediction @ 32"]
        FNO --> P64["Prediction @ 64"]
        FNO --> P96["Prediction @ 96"]
        FNO --> P128["Prediction @ 128"]
    end

    style FNO fill:#e17055,stroke:#b04a3a,color:#fff,rx:10
    style A32 fill:#74b9ff,stroke:#4a8fd4,color:#333
    style A64 fill:#74b9ff,stroke:#4a8fd4,color:#333
    style A96 fill:#74b9ff,stroke:#4a8fd4,color:#333
    style A128 fill:#74b9ff,stroke:#4a8fd4,color:#333
    style P32 fill:#55efc4,stroke:#38c99e,color:#333
    style P64 fill:#55efc4,stroke:#38c99e,color:#333
    style P96 fill:#55efc4,stroke:#38c99e,color:#333
    style P128 fill:#55efc4,stroke:#38c99e,color:#333
```

---

## Full Architecture

The complete FNO pipeline stacks multiple Fourier layers between a lifting layer (projection to higher dimension) and a projection layer (back to output dimension):

$$u_0(x) \;\xrightarrow{\text{Lift } P}\; v_0(x) \;\xrightarrow{\text{Fourier Layer } \times L}\; v_L(x) \;\xrightarrow{\text{Project } Q}\; u(x, t)$$

```mermaid
graph LR
    INPUT["u₀(x)<br/>Input Function<br/><i>dim: 1</i>"] --> LIFT["Lifting<br/>Layer P<br/><i>dim: d</i>"]
    LIFT --> F1["Fourier<br/>Layer 1"]
    F1 --> F2["Fourier<br/>Layer 2"]
    F2 --> F3["Fourier<br/>Layer 3"]
    F3 --> F4["Fourier<br/>Layer 4"]
    F4 --> PROJ["Projection<br/>Layer Q<br/><i>dim: 1</i>"]
    PROJ --> OUTPUT["û(x,t)<br/>Predicted<br/>Solution"]

    style INPUT fill:#a29bfe,stroke:#6c5ce7,color:#fff,rx:8
    style LIFT fill:#74b9ff,stroke:#0984e3,color:#fff,rx:8
    style F1 fill:#6c5ce7,stroke:#4a3db5,color:#fff,rx:8
    style F2 fill:#6c5ce7,stroke:#4a3db5,color:#fff,rx:8
    style F3 fill:#6c5ce7,stroke:#4a3db5,color:#fff,rx:8
    style F4 fill:#6c5ce7,stroke:#4a3db5,color:#fff,rx:8
    style PROJ fill:#74b9ff,stroke:#0984e3,color:#fff,rx:8
    style OUTPUT fill:#fd79a8,stroke:#e84393,color:#fff,rx:8
```

**Model Configuration:**

| Hyperparameter | Value |
|:---|:---|
| Fourier Modes | 16 |
| Hidden Width | 64 |
| Fourier Layers | 4 |
| Parameters | 287K |
| Optimizer | Adam + ReduceLROnPlateau |

---

## Results

### Task 1: One-to-One Training (10 pts)

Learn the direct mapping $u_0 \mapsto u(t=1.0)$ using 1024 training trajectories.

<div align="center">
<img src="figures/02_one2one_predictions.png" width="90%" alt="One-to-one predictions vs ground truth"/>
</div>

<div align="center">

| Metric | Value |
|:---|:---|
| Training Epochs | 253 (early stopped) |
| Final Train Loss | 1.52e-03 |
| **Test Relative L² Error** | **0.1203** |

</div>

---

### Task 2: Multi-Resolution Testing (10 pts)

Test the same trained model (no retraining) on grids of different spatial resolution. This demonstrates FNO's core property — **resolution invariance**.

<div align="center">
<img src="figures/03_multi_resolution.png" width="90%" alt="Resolution invariance results"/>
</div>

<div align="center">

| Resolution | Relative L² Error |
|:---:|:---:|
| 32 | 0.1332 |
| 64 | 0.1492 |
| 96 | 0.1277 |
| **128** (train) | **0.1203** |

</div>

> Errors remain within a ~3% band across a 4x resolution range, confirming that spectral features transfer across discretizations.

---

### Task 3: All-to-All Time-Dependent Training (15 pts)

Train a time-conditioned FNO using all 5 time snapshots. Input channels: $[u(t_i),\; t_i,\; t_j]$.

<div align="center">
<img src="figures/04_all2all_predictions.png" width="90%" alt="All2All predictions at multiple time steps"/>
</div>

<div align="center">
<img src="figures/05_error_vs_time.png" width="55%" alt="Error growth over prediction horizon"/>
</div>

<div align="center">

| Prediction Time | Relative L² Error |
|:---:|:---:|
| t = 0.25 | 0.0524 |
| t = 0.50 | 0.0892 |
| t = 0.75 | 0.1197 |
| t = 1.00 | 0.1595 |

</div>

> Error grows approximately linearly with the prediction horizon — shorter-range predictions are significantly more accurate.

---

### Task 4: Fine-Tuning & Transfer Learning (15 + 10 bonus pts)

Test the all2all model on a **shifted initial condition distribution** (zero-shot), then fine-tune with only 32 trajectories. Compare against training from scratch.

<div align="center">
<img src="figures/06_finetune_comparison.png" width="90%" alt="Fine-tuning comparison"/>
</div>

<div align="center">

| Method | L² Error at t=1.0 | Improvement |
|:---|:---:|:---:|
| Zero-Shot (no adaptation) | 0.4025 | — |
| **Fine-Tuned** (32 trajectories) | **0.2255** | **44% reduction** |
| From Scratch (32 trajectories) | 0.2709 | 33% reduction |

</div>

> Fine-tuning outperforms training from scratch by ~17%, confirming that **transfer learning is successful** — pretrained spectral features generalize across distributions.

---

### 3D Spatiotemporal Visualization

Full spatiotemporal evolution as 3D surfaces ($x$ vs $t$ vs $u$) — comparing ground truth, FNO prediction, and absolute error.

<div align="center">
<img src="figures/10_comparison_3d.png" width="95%" alt="3D comparison: truth vs prediction vs error"/>
</div>

<div align="center">
<img src="figures/11_finetune_3d.png" width="95%" alt="3D transfer learning comparison"/>
</div>

<details>
<summary><b>Spatiotemporal Heatmaps</b> — click to expand</summary>
<br/>
<div align="center">
<img src="figures/12_heatmaps.png" width="90%" alt="Heatmaps x vs t"/>
</div>

Top-down view of the same data — error concentrates at later time steps and near boundary regions.
</details>

<details>
<summary><b>Summary Dashboard</b> — click to expand</summary>
<br/>
<div align="center">
<img src="figures/07_summary_dashboard.png" width="95%" alt="Results summary dashboard"/>
</div>
</details>

---

## Training Strategies

### One-to-One (Task 1)

Learn a direct mapping from initial condition to final state:

$$\mathcal{G}_\theta : u_0 \mapsto u(t = 1.0)$$

Simple and fast — but the model sees only two snapshots per trajectory and cannot predict intermediate times.

### All-to-All (Task 3)

Use **all time snapshots** to train a time-conditioned model:

$$\mathcal{G}_\theta : (u(t_i),\; t_i,\; t_j) \mapsto u(t_j)$$

This requires **time-conditional normalization** — injecting the target time as an additional input channel so the model knows *when* to predict. The model learns the full temporal dynamics, not just a single-step map.

### Fine-Tuning & Transfer Learning (Task 4)

When the initial condition distribution shifts (unknown distribution), the pretrained model degrades. **Fine-tuning** adapts the learned operator to a new regime using minimal data (32 trajectories), demonstrating that the spectral features learned by FNO are transferable across distributions.

```mermaid
graph TD
    subgraph "Training Pipeline"
        D1["Task 1<br/>One-to-One<br/><i>u₀ → u(t=1)</i>"] --> EVAL1["Test @ Multiple<br/>Resolutions"]
        D2["Task 3<br/>All-to-All<br/><i>(u, tᵢ, tⱼ) → u(tⱼ)</i>"] --> EVAL2["Test @ All<br/>Time Steps"]
        D2 --> FT["Task 4<br/>Fine-Tune on<br/>Unknown Distribution"]
        FT --> EVAL3["Compare: Fine-Tuned<br/>vs. From Scratch"]
    end

    style D1 fill:#0984e3,stroke:#065a9e,color:#fff,rx:8
    style D2 fill:#6c5ce7,stroke:#4a3db5,color:#fff,rx:8
    style FT fill:#e17055,stroke:#b04a3a,color:#fff,rx:8
    style EVAL1 fill:#00b894,stroke:#008c6e,color:#fff,rx:8
    style EVAL2 fill:#00b894,stroke:#008c6e,color:#fff,rx:8
    style EVAL3 fill:#00b894,stroke:#008c6e,color:#fff,rx:8
```

---

## Key References

| Paper | Contribution |
|:---|:---|
| [Li et al., 2021 — *Fourier Neural Operator for Parametric PDEs*](https://arxiv.org/abs/2010.08895) | Introduced FNO with spectral convolutions for resolution-invariant operator learning |
| [Li et al., 2023 — *Fourier Neural Operator with Learned Deformations*](https://arxiv.org/abs/2207.05209) | Extended FNO with geometry-adaptive deformations |
| [Kovachki et al., 2023 — *Neural Operator: Learning Maps Between Function Spaces*](https://arxiv.org/abs/2108.08481) | Unified theoretical framework for neural operators |

---

<div align="center">
<sub>Built as part of <a href="https://camlab-ethz.github.io/ai4s-course/">AI in the Sciences and Engineering</a> at ETH Zurich</sub>
</div>
