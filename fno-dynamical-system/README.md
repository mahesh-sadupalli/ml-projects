# FNO for Approximating a Dynamical System

Training a Fourier Neural Operator (FNO) to approximate an unknown 1D dynamical system governed by:

$$\frac{\partial u}{\partial t} = \mathcal{D}(u(x,t)), \quad t \in (0,1], \; x \in [0,1]$$

with homogeneous Dirichlet boundary conditions and unknown initial condition distribution.

## Project Structure

```
fno-dynamical-system/
├── data/                   # Training, validation, and test datasets
├── src/
│   ├── model.py            # FNO architecture
│   ├── dataset.py          # Data loading and preprocessing
│   ├── train.py            # Training loop
│   └── evaluate.py         # Evaluation and metrics
├── notebooks/              # Experiments and visualization
├── configs/                # Training configurations
├── checkpoints/            # Saved model weights
├── requirements.txt
└── README.md
```

## Tasks

| Task | Description | Points |
|------|-------------|--------|
| 1 | **One-to-One Training** — Learn mapping u₀ → u(t=1.0) | 10 |
| 2 | **Multi-Resolution Testing** — Evaluate on resolutions {32, 64, 96, 128} | 10 |
| 3 | **All2All Training** — Time-dependent FNO with all time snapshots | 15 |
| 4 | **Fine-tuning** — Adapt to unknown distribution + train from scratch (bonus) | 15 + 10 |

## Datasets

| File | Shape | Description |
|------|-------|-------------|
| `data_train_128.npy` | (1024, 5, 128) | 1024 trajectories, 5 time steps, 128 spatial points |
| `data_val_128.npy` | (32, 5, 128) | Validation set |
| `data_test_{s}.npy` | (128, 5, s) | Test sets at resolution s ∈ {32, 64, 96, 128} |
| `data_finetune_train_unknown_128.npy` | (32, 5, 128) | Fine-tuning data (unknown distribution) |
| `data_finetune_val_unknown_128.npy` | (8, 5, 128) | Fine-tuning validation |
| `data_test_unknown_128.npy` | (128, 5, 128) | Test set (unknown distribution) |

Time snapshots: t ∈ {0.0, 0.25, 0.50, 0.75, 1.0}

## Evaluation Metric

Average relative L² error:

$$\text{err} = \frac{1}{N}\sum_{n=1}^{N} \frac{\|u_{\text{pred}}^{(n)} - u_{\text{true}}^{(n)}\|_2}{\|u_{\text{true}}^{(n)}\|_2}$$

## Setup

```bash
pip install -r requirements.txt
```

## Usage

```bash
# Task 1: One-to-one training
python src/train.py --mode one2one

# Task 3: All2All training
python src/train.py --mode all2all

# Task 4: Fine-tuning
python src/train.py --mode finetune --checkpoint checkpoints/all2all_best.pt
```
