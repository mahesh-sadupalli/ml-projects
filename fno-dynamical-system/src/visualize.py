"""Visualization script for all tasks — generates publication-quality figures."""
import os
import numpy as np
import torch
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

from model import FNO1d
from dataset import load_test_data, load_test_data_all_times
from evaluate import evaluate_all2all, relative_l2_error

plt.rcParams.update({
    'font.size': 12,
    'axes.titlesize': 14,
    'axes.labelsize': 12,
    'figure.dpi': 150,
    'savefig.dpi': 200,
    'savefig.bbox': 'tight',
})

DATA_DIR = "../data"
CKPT_DIR = "../checkpoints"
FIG_DIR = "../figures"
DEVICE = "cpu"
MODES, WIDTH, N_LAYERS = 16, 64, 4
TIMES = [0.0, 0.25, 0.50, 0.75, 1.0]


def make_model(in_ch):
    return FNO1d(modes=MODES, width=WIDTH, in_channels=in_ch, out_channels=1, n_layers=N_LAYERS)


def load_model(path, in_ch):
    model = make_model(in_ch)
    model.load_state_dict(torch.load(path, weights_only=True))
    model.eval()
    return model


# ── Figure 1: Dataset Visualization ──────────────────────────────────────────

def fig_dataset():
    """Visualize sample trajectories from the training data."""
    data = np.load(f"{DATA_DIR}/data_train_128.npy")
    x = np.linspace(0, 1, 128)

    fig, axes = plt.subplots(2, 3, figsize=(14, 8))
    fig.suptitle("Training Dataset — Sample Trajectories", fontsize=16, fontweight='bold')

    colors = plt.cm.viridis(np.linspace(0.1, 0.9, 5))

    for idx, ax in enumerate(axes.flat):
        for t_idx in range(5):
            ax.plot(x, data[idx, t_idx, :], color=colors[t_idx],
                    label=f"t={TIMES[t_idx]:.2f}", linewidth=1.5)
        ax.set_title(f"Trajectory {idx + 1}", fontsize=11)
        ax.set_xlabel("x")
        ax.set_ylabel("u(x, t)")
        ax.grid(True, alpha=0.3)

    axes[0, 0].legend(fontsize=8, loc='upper left')
    plt.tight_layout()
    plt.savefig(f"{FIG_DIR}/01_dataset_samples.png")
    plt.close()
    print("  Saved 01_dataset_samples.png")


# ── Figure 2: Task 1 — One2One Predictions ───────────────────────────────────

def fig_one2one_predictions():
    """Compare one2one model predictions vs ground truth."""
    model = load_model(f"{CKPT_DIR}/one2one_best.pt", in_ch=1)
    test_data = np.load(f"{DATA_DIR}/data_test_128.npy")
    x = np.linspace(0, 1, 128)

    inputs = torch.tensor(test_data[:, 0, :], dtype=torch.float32).unsqueeze(1)
    targets = test_data[:, -1, :]

    with torch.no_grad():
        preds = model(inputs).squeeze(1).numpy()

    fig, axes = plt.subplots(2, 4, figsize=(16, 8))
    fig.suptitle("Task 1: One-to-One Predictions — u₀ → u(t=1.0)", fontsize=16, fontweight='bold')

    for i in range(8):
        ax = axes[i // 4, i % 4]
        ax.plot(x, test_data[i, 0, :], '--', color='gray', alpha=0.5, label='u₀', linewidth=1)
        ax.plot(x, targets[i], 'b-', label='Ground Truth', linewidth=1.5)
        ax.plot(x, preds[i], 'r--', label='FNO Prediction', linewidth=1.5)

        err = np.linalg.norm(preds[i] - targets[i]) / np.linalg.norm(targets[i])
        ax.set_title(f"Sample {i+1}  (err={err:.4f})", fontsize=10)
        ax.set_xlabel("x")
        ax.grid(True, alpha=0.3)

    axes[0, 0].legend(fontsize=8)
    plt.tight_layout()
    plt.savefig(f"{FIG_DIR}/02_one2one_predictions.png")
    plt.close()
    print("  Saved 02_one2one_predictions.png")


# ── Figure 3: Task 2 — Multi-Resolution ──────────────────────────────────────

def fig_multi_resolution():
    """Bar chart + example predictions at different resolutions."""
    model = load_model(f"{CKPT_DIR}/one2one_best.pt", in_ch=1)
    resolutions = [32, 64, 96, 128]
    errors = []

    fig = plt.figure(figsize=(16, 10))
    gs = gridspec.GridSpec(2, 4, figure=fig, hspace=0.35)

    # Top row: predictions at each resolution
    for idx, res in enumerate(resolutions):
        test_path = f"{DATA_DIR}/data_test_{res}.npy"
        if not os.path.exists(test_path):
            errors.append(0)
            continue

        test_data = np.load(test_path)
        x_res = np.linspace(0, 1, res)
        inputs = torch.tensor(test_data[:, 0, :], dtype=torch.float32).unsqueeze(1)
        targets = torch.tensor(test_data[:, -1, :], dtype=torch.float32).unsqueeze(1)

        if res != 128:
            inputs_128 = torch.nn.functional.interpolate(inputs, size=128, mode='linear', align_corners=True)
        else:
            inputs_128 = inputs

        with torch.no_grad():
            preds_128 = model(inputs_128)

        if res != 128:
            preds = torch.nn.functional.interpolate(preds_128, size=res, mode='linear', align_corners=True)
        else:
            preds = preds_128

        err = relative_l2_error(preds, targets)
        errors.append(err)

        ax = fig.add_subplot(gs[0, idx])
        sample_idx = 0
        ax.plot(x_res, test_data[sample_idx, -1, :], 'b-', label='Truth', linewidth=1.5)
        ax.plot(x_res, preds[sample_idx].squeeze().numpy(), 'r--', label='Pred', linewidth=1.5)
        ax.set_title(f"Resolution {res}", fontsize=11)
        ax.set_xlabel("x")
        ax.grid(True, alpha=0.3)
        if idx == 0:
            ax.legend(fontsize=8)

    # Bottom row: bar chart
    ax_bar = fig.add_subplot(gs[1, :])
    colors = ['#3498db', '#2ecc71', '#e67e22', '#e74c3c']
    bars = ax_bar.bar([str(r) for r in resolutions], errors, color=colors, width=0.5, edgecolor='white')

    for bar, err in zip(bars, errors):
        ax_bar.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.002,
                    f'{err:.4f}', ha='center', va='bottom', fontweight='bold', fontsize=11)

    ax_bar.set_xlabel("Spatial Resolution")
    ax_bar.set_ylabel("Relative L² Error")
    ax_bar.set_title("Task 2: Resolution Invariance — Same Weights, Different Grids", fontsize=14, fontweight='bold')
    ax_bar.set_ylim(0, max(errors) * 1.3)
    ax_bar.grid(True, alpha=0.3, axis='y')

    plt.savefig(f"{FIG_DIR}/03_multi_resolution.png")
    plt.close()
    print("  Saved 03_multi_resolution.png")


# ── Figure 4: Task 3 — All2All Time-Dependent ────────────────────────────────

def fig_all2all_predictions():
    """All2All predictions at multiple time steps."""
    model = load_model(f"{CKPT_DIR}/all2all_best.pt", in_ch=3)
    test_data = np.load(f"{DATA_DIR}/data_test_128.npy")
    x = np.linspace(0, 1, 128)

    test_tensor = torch.tensor(test_data, dtype=torch.float32)

    # Plot 3 samples, each with predictions at all future times
    fig, axes = plt.subplots(3, 4, figsize=(16, 10))
    fig.suptitle("Task 3: All2All Predictions at Multiple Time Steps", fontsize=16, fontweight='bold')

    time_colors = ['#27ae60', '#e67e22', '#e74c3c', '#8e44ad']
    target_times = [1, 2, 3, 4]

    for row in range(3):
        sample = test_tensor[row]
        u0 = sample[0]

        for col, t_j in enumerate(target_times):
            ax = axes[row, col]

            # Build input
            t_i_ch = torch.full((128,), TIMES[0])
            t_j_ch = torch.full((128,), TIMES[t_j])
            inp = torch.stack([u0, t_i_ch, t_j_ch], dim=0).unsqueeze(0)

            with torch.no_grad():
                pred = model(inp).squeeze().numpy()

            truth = sample[t_j].numpy()
            err = np.linalg.norm(pred - truth) / np.linalg.norm(truth)

            ax.plot(x, truth, 'b-', label='Truth', linewidth=1.5)
            ax.plot(x, pred, 'r--', label='Prediction', linewidth=1.5)
            ax.set_title(f"t={TIMES[t_j]:.2f}  (err={err:.4f})", fontsize=10, color=time_colors[col])
            ax.grid(True, alpha=0.3)

            if col == 0:
                ax.set_ylabel(f"Sample {row + 1}")
            if row == 0 and col == 0:
                ax.legend(fontsize=8)

    plt.tight_layout()
    plt.savefig(f"{FIG_DIR}/04_all2all_predictions.png")
    plt.close()
    print("  Saved 04_all2all_predictions.png")


def fig_all2all_error_vs_time():
    """Error as a function of prediction time horizon."""
    model = load_model(f"{CKPT_DIR}/all2all_best.pt", in_ch=3)
    test_data = load_test_data_all_times(f"{DATA_DIR}/data_test_128.npy")

    results = evaluate_all2all(model, test_data, DEVICE, target_times=[1, 2, 3, 4])
    times_plot = list(results.keys())
    errors_plot = list(results.values())

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(times_plot, errors_plot, 'o-', color='#e74c3c', linewidth=2.5, markersize=10, markerfacecolor='white', markeredgewidth=2)

    for t, e in zip(times_plot, errors_plot):
        ax.annotate(f'{e:.4f}', (t, e), textcoords="offset points", xytext=(0, 15),
                    ha='center', fontsize=11, fontweight='bold')

    ax.set_xlabel("Prediction Time t")
    ax.set_ylabel("Relative L² Error")
    ax.set_title("Task 3: Error Growth Over Prediction Horizon", fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.set_xlim(0.15, 1.1)
    ax.set_ylim(0, max(errors_plot) * 1.4)

    plt.tight_layout()
    plt.savefig(f"{FIG_DIR}/05_error_vs_time.png")
    plt.close()
    print("  Saved 05_error_vs_time.png")


# ── Figure 6: Task 4 — Fine-tuning Comparison ────────────────────────────────

def fig_finetune_comparison():
    """Compare zero-shot, fine-tuned, and from-scratch on unknown distribution."""
    test_data = load_test_data_all_times(f"{DATA_DIR}/data_test_unknown_128.npy")
    x = np.linspace(0, 1, 128)

    models = {}
    labels = {}
    colors_map = {}

    # Load all available models
    if os.path.exists(f"{CKPT_DIR}/all2all_best.pt"):
        models['zero_shot'] = load_model(f"{CKPT_DIR}/all2all_best.pt", in_ch=3)
        labels['zero_shot'] = 'Zero-Shot'
        colors_map['zero_shot'] = '#e67e22'

    if os.path.exists(f"{CKPT_DIR}/finetune_best.pt"):
        models['finetuned'] = load_model(f"{CKPT_DIR}/finetune_best.pt", in_ch=3)
        labels['finetuned'] = 'Fine-Tuned'
        colors_map['finetuned'] = '#27ae60'

    if os.path.exists(f"{CKPT_DIR}/from_scratch_best.pt"):
        models['scratch'] = load_model(f"{CKPT_DIR}/from_scratch_best.pt", in_ch=3)
        labels['scratch'] = 'From Scratch'
        colors_map['scratch'] = '#8e44ad'

    # ── Bar chart of errors ──
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    fig.suptitle("Task 4: Transfer Learning on Unknown Distribution", fontsize=16, fontweight='bold')

    errs = {}
    for key, model in models.items():
        results = evaluate_all2all(model, test_data, DEVICE, target_times=[4])
        errs[key] = results[1.0]

    ax = axes[0]
    bar_labels = [labels[k] for k in errs]
    bar_vals = list(errs.values())
    bar_colors = [colors_map[k] for k in errs]
    bars = ax.bar(bar_labels, bar_vals, color=bar_colors, width=0.5, edgecolor='white', linewidth=1.5)

    for bar, val in zip(bars, bar_vals):
        ax.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.005,
                f'{val:.4f}', ha='center', va='bottom', fontweight='bold', fontsize=12)

    ax.set_ylabel("Relative L² Error at t=1.0")
    ax.set_title("Error Comparison")
    ax.set_ylim(0, max(bar_vals) * 1.3)
    ax.grid(True, alpha=0.3, axis='y')

    # ── Prediction comparison on a sample ──
    ax2 = axes[1]
    sample_idx = 0
    u0 = torch.tensor(test_data[sample_idx, 0, :], dtype=torch.float32)
    truth = test_data[sample_idx, -1, :].numpy()

    ax2.plot(x, truth, 'b-', label='Ground Truth', linewidth=2)

    for key, model in models.items():
        t_i_ch = torch.full((128,), 0.0)
        t_j_ch = torch.full((128,), 1.0)
        inp = torch.stack([u0, t_i_ch, t_j_ch], dim=0).unsqueeze(0)
        with torch.no_grad():
            pred = model(inp).squeeze().numpy()
        ax2.plot(x, pred, '--', color=colors_map[key], label=labels[key], linewidth=1.5)

    ax2.set_xlabel("x")
    ax2.set_ylabel("u(x, t=1.0)")
    ax2.set_title("Prediction Comparison (Sample 1)")
    ax2.legend(fontsize=10)
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(f"{FIG_DIR}/06_finetune_comparison.png")
    plt.close()
    print("  Saved 06_finetune_comparison.png")


# ── Figure 7: Summary Dashboard ──────────────────────────────────────────────

def fig_summary():
    """Single summary figure with all key results."""
    fig = plt.figure(figsize=(18, 10))
    fig.suptitle("FNO for Dynamical Systems — Results Summary", fontsize=18, fontweight='bold', y=0.98)
    gs = gridspec.GridSpec(2, 3, figure=fig, hspace=0.35, wspace=0.3)

    # Panel 1: One2One sample prediction
    ax1 = fig.add_subplot(gs[0, 0])
    model_o2o = load_model(f"{CKPT_DIR}/one2one_best.pt", in_ch=1)
    test = np.load(f"{DATA_DIR}/data_test_128.npy")
    x = np.linspace(0, 1, 128)
    inp = torch.tensor(test[0:1, 0, :], dtype=torch.float32).unsqueeze(1)
    with torch.no_grad():
        pred = model_o2o(inp).squeeze().numpy()
    ax1.plot(x, test[0, -1, :], 'b-', label='Truth', lw=1.5)
    ax1.plot(x, pred, 'r--', label='FNO', lw=1.5)
    ax1.legend(fontsize=8)
    ax1.set_title("Task 1: One-to-One", fontweight='bold')
    ax1.grid(True, alpha=0.3)

    # Panel 2: Multi-resolution bar
    ax2 = fig.add_subplot(gs[0, 1])
    resolutions = [32, 64, 96, 128]
    res_errors = []
    for res in resolutions:
        tp = f"{DATA_DIR}/data_test_{res}.npy"
        if not os.path.exists(tp):
            res_errors.append(0)
            continue
        td = np.load(tp)
        inp_r = torch.tensor(td[:, 0, :], dtype=torch.float32).unsqueeze(1)
        tgt_r = torch.tensor(td[:, -1, :], dtype=torch.float32).unsqueeze(1)
        if res != 128:
            inp_r = torch.nn.functional.interpolate(inp_r, size=128, mode='linear', align_corners=True)
        with torch.no_grad():
            pr = model_o2o(inp_r)
        if res != 128:
            pr = torch.nn.functional.interpolate(pr, size=res, mode='linear', align_corners=True)
        res_errors.append(relative_l2_error(pr, tgt_r))

    ax2.bar([str(r) for r in resolutions], res_errors, color=['#3498db', '#2ecc71', '#e67e22', '#e74c3c'], width=0.5)
    ax2.set_title("Task 2: Resolution Invariance", fontweight='bold')
    ax2.set_ylabel("Rel. L² Error")
    ax2.grid(True, alpha=0.3, axis='y')

    # Panel 3: Error vs time
    ax3 = fig.add_subplot(gs[0, 2])
    model_a2a = load_model(f"{CKPT_DIR}/all2all_best.pt", in_ch=3)
    test_tensor = load_test_data_all_times(f"{DATA_DIR}/data_test_128.npy")
    results = evaluate_all2all(model_a2a, test_tensor, DEVICE, target_times=[1, 2, 3, 4])
    ax3.plot(list(results.keys()), list(results.values()), 'o-', color='#e74c3c', lw=2, markersize=8, markerfacecolor='white', markeredgewidth=2)
    ax3.set_title("Task 3: Error vs Time", fontweight='bold')
    ax3.set_xlabel("t")
    ax3.set_ylabel("Rel. L² Error")
    ax3.grid(True, alpha=0.3)

    # Panel 4: All2All sample
    ax4 = fig.add_subplot(gs[1, 0])
    u0 = test_tensor[0, 0]
    for t_j, col in zip([1, 2, 3, 4], ['#27ae60', '#e67e22', '#e74c3c', '#8e44ad']):
        t_i_ch = torch.full((128,), 0.0)
        t_j_ch = torch.full((128,), TIMES[t_j])
        inp_a = torch.stack([u0, t_i_ch, t_j_ch], dim=0).unsqueeze(0)
        with torch.no_grad():
            pr = model_a2a(inp_a).squeeze().numpy()
        ax4.plot(x, pr, '--', color=col, lw=1.2, label=f'pred t={TIMES[t_j]}')
        ax4.plot(x, test_tensor[0, t_j].numpy(), '-', color=col, lw=1, alpha=0.5)
    ax4.set_title("Task 3: Multi-Step Prediction", fontweight='bold')
    ax4.legend(fontsize=7, ncol=2)
    ax4.grid(True, alpha=0.3)

    # Panel 5: Finetune comparison
    ax5 = fig.add_subplot(gs[1, 1])
    test_unk = load_test_data_all_times(f"{DATA_DIR}/data_test_unknown_128.npy")
    ft_errors = {}
    for name, path in [('Zero-Shot', 'all2all_best.pt'), ('Fine-Tuned', 'finetune_best.pt'), ('From Scratch', 'from_scratch_best.pt')]:
        p = f"{CKPT_DIR}/{path}"
        if os.path.exists(p):
            m = load_model(p, in_ch=3)
            r = evaluate_all2all(m, test_unk, DEVICE, target_times=[4])
            ft_errors[name] = r[1.0]
    if ft_errors:
        ft_colors = ['#e67e22', '#27ae60', '#8e44ad'][:len(ft_errors)]
        ax5.bar(list(ft_errors.keys()), list(ft_errors.values()), color=ft_colors, width=0.5)
        ax5.set_title("Task 4: Transfer Learning", fontweight='bold')
        ax5.set_ylabel("Rel. L² Error")
        ax5.grid(True, alpha=0.3, axis='y')

    # Panel 6: Unknown dist prediction
    ax6 = fig.add_subplot(gs[1, 2])
    if os.path.exists(f"{CKPT_DIR}/finetune_best.pt"):
        model_ft = load_model(f"{CKPT_DIR}/finetune_best.pt", in_ch=3)
        u0_unk = torch.tensor(test_unk[0, 0, :], dtype=torch.float32)
        truth_unk = test_unk[0, -1, :].numpy()
        t_i_ch = torch.full((128,), 0.0)
        t_j_ch = torch.full((128,), 1.0)

        ax6.plot(x, truth_unk, 'b-', label='Truth', lw=1.5)
        for name, path, col in [('Zero-Shot', 'all2all_best.pt', '#e67e22'), ('Fine-Tuned', 'finetune_best.pt', '#27ae60')]:
            m = load_model(f"{CKPT_DIR}/{path}", in_ch=3)
            inp_u = torch.stack([u0_unk, t_i_ch, t_j_ch], dim=0).unsqueeze(0)
            with torch.no_grad():
                pr = m(inp_u).squeeze().numpy()
            ax6.plot(x, pr, '--', color=col, label=name, lw=1.5)

        ax6.set_title("Task 4: Unknown Dist. Prediction", fontweight='bold')
        ax6.legend(fontsize=8)
        ax6.grid(True, alpha=0.3)

    plt.savefig(f"{FIG_DIR}/07_summary_dashboard.png")
    plt.close()
    print("  Saved 07_summary_dashboard.png")


if __name__ == "__main__":
    os.makedirs(FIG_DIR, exist_ok=True)

    print("Generating figures...")
    fig_dataset()
    fig_one2one_predictions()
    fig_multi_resolution()
    fig_all2all_predictions()
    fig_all2all_error_vs_time()
    fig_finetune_comparison()
    fig_summary()
    print("\nAll figures saved to", FIG_DIR)
