"""3D surface visualizations of FNO predictions vs ground truth."""
import os
import numpy as np
import torch
import matplotlib.pyplot as plt
from matplotlib import cm
from mpl_toolkits.mplot3d import Axes3D

from model import FNO1d
from dataset import load_test_data_all_times
from evaluate import evaluate_all2all

plt.rcParams.update({
    'font.size': 12,
    'figure.dpi': 150,
    'savefig.dpi': 200,
    'savefig.bbox': 'tight',
})

DATA_DIR = "../data"
CKPT_DIR = "../checkpoints"
FIG_DIR = "../figures"
DEVICE = "cpu"
MODES, WIDTH, N_LAYERS = 16, 64, 4
TIMES = np.array([0.0, 0.25, 0.50, 0.75, 1.0])


def load_model(path, in_ch=3):
    model = FNO1d(modes=MODES, width=WIDTH, in_channels=in_ch, out_channels=1, n_layers=N_LAYERS)
    model.load_state_dict(torch.load(path, weights_only=True))
    model.eval()
    return model


def interpolate_trajectory(trajectory, n_time_fine=50):
    """Interpolate a (5, S) trajectory to (n_time_fine, S) for smooth surface."""
    from scipy.interpolate import interp1d
    n_space = trajectory.shape[1]
    t_coarse = TIMES
    t_fine = np.linspace(0, 1, n_time_fine)
    interp_func = interp1d(t_coarse, trajectory, axis=0, kind='cubic')
    return interp_func(t_fine), t_fine


def predict_all_times(model, u0, t_fine):
    """Get FNO predictions at fine time grid (predicting from t=0 to each t)."""
    S = u0.shape[0]
    preds = np.zeros((len(t_fine), S))
    preds[0] = u0

    u0_tensor = torch.tensor(u0, dtype=torch.float32)
    for i, t in enumerate(t_fine[1:], 1):
        t_i_ch = torch.zeros(S)
        t_j_ch = torch.full((S,), t)
        inp = torch.stack([u0_tensor, t_i_ch, t_j_ch], dim=0).unsqueeze(0)
        with torch.no_grad():
            preds[i] = model(inp).squeeze().numpy()
    return preds


def plot_3d_surface(X, T, U, title, filename, elev=25, azim=-60, cmap='viridis'):
    """Create a publication-quality 3D surface plot."""
    fig = plt.figure(figsize=(12, 8))
    ax = fig.add_subplot(111, projection='3d')

    surf = ax.plot_surface(
        X, T, U,
        cmap=cmap,
        edgecolor='none',
        alpha=0.95,
        antialiased=True,
        rstride=1, cstride=1,
        shade=True
    )

    ax.set_xlabel('x (spatial)', fontsize=13, labelpad=10)
    ax.set_ylabel('t (time)', fontsize=13, labelpad=10)
    ax.set_zlabel('u(x, t)', fontsize=13, labelpad=10)
    ax.set_title(title, fontsize=16, fontweight='bold', pad=20)

    ax.view_init(elev=elev, azim=azim)
    ax.xaxis.pane.fill = False
    ax.yaxis.pane.fill = False
    ax.zaxis.pane.fill = False
    ax.xaxis.pane.set_edgecolor('lightgray')
    ax.yaxis.pane.set_edgecolor('lightgray')
    ax.zaxis.pane.set_edgecolor('lightgray')
    ax.grid(True, alpha=0.3)

    fig.colorbar(surf, ax=ax, shrink=0.5, aspect=15, pad=0.1, label='u(x, t)')

    plt.savefig(f"{FIG_DIR}/{filename}")
    plt.close()
    print(f"  Saved {filename}")


def fig_ground_truth_3d():
    """3D surface of ground truth trajectory."""
    data = np.load(f"{DATA_DIR}/data_test_128.npy")
    x = np.linspace(0, 1, 128)

    for sample_idx in [0, 2]:
        traj = data[sample_idx]  # (5, 128)
        traj_fine, t_fine = interpolate_trajectory(traj, n_time_fine=80)

        X, T = np.meshgrid(x, t_fine)

        plot_3d_surface(
            X, T, traj_fine,
            f"Ground Truth — Trajectory {sample_idx + 1}",
            f"08_ground_truth_3d_sample{sample_idx + 1}.png",
            elev=28, azim=-55, cmap='viridis'
        )


def fig_prediction_3d():
    """3D surface of FNO all2all prediction."""
    model = load_model(f"{CKPT_DIR}/all2all_best.pt", in_ch=3)
    data = np.load(f"{DATA_DIR}/data_test_128.npy")
    x = np.linspace(0, 1, 128)
    t_fine = np.linspace(0, 1, 80)
    X, T = np.meshgrid(x, t_fine)

    for sample_idx in [0, 2]:
        u0 = data[sample_idx, 0]
        preds = predict_all_times(model, u0, t_fine)

        plot_3d_surface(
            X, T, preds,
            f"FNO Prediction — Trajectory {sample_idx + 1}",
            f"09_fno_prediction_3d_sample{sample_idx + 1}.png",
            elev=28, azim=-55, cmap='plasma'
        )


def fig_comparison_3d():
    """Side-by-side 3D: ground truth vs prediction vs error."""
    model = load_model(f"{CKPT_DIR}/all2all_best.pt", in_ch=3)
    data = np.load(f"{DATA_DIR}/data_test_128.npy")
    x = np.linspace(0, 1, 128)
    t_fine = np.linspace(0, 1, 80)
    X, T = np.meshgrid(x, t_fine)

    sample_idx = 0
    traj = data[sample_idx]
    traj_fine, _ = interpolate_trajectory(traj, n_time_fine=80)
    u0 = data[sample_idx, 0]
    preds = predict_all_times(model, u0, t_fine)
    error = np.abs(traj_fine - preds)

    fig = plt.figure(figsize=(20, 6))
    fig.suptitle("Spatiotemporal Evolution — Ground Truth vs FNO Prediction",
                 fontsize=18, fontweight='bold', y=1.02)

    configs = [
        (traj_fine, 'Ground Truth', 'viridis'),
        (preds, 'FNO All2All Prediction', 'plasma'),
        (error, '|Error|', 'hot'),
    ]

    for i, (Z, title, cmap) in enumerate(configs):
        ax = fig.add_subplot(1, 3, i + 1, projection='3d')
        surf = ax.plot_surface(
            X, T, Z, cmap=cmap, edgecolor='none', alpha=0.95,
            antialiased=True, rstride=1, cstride=1, shade=True
        )
        ax.set_xlabel('x', fontsize=11, labelpad=8)
        ax.set_ylabel('t', fontsize=11, labelpad=8)
        ax.set_zlabel('u', fontsize=11, labelpad=8)
        ax.set_title(title, fontsize=14, fontweight='bold', pad=10)
        ax.view_init(elev=25, azim=-55)
        ax.xaxis.pane.fill = False
        ax.yaxis.pane.fill = False
        ax.zaxis.pane.fill = False
        ax.xaxis.pane.set_edgecolor('lightgray')
        ax.yaxis.pane.set_edgecolor('lightgray')
        ax.zaxis.pane.set_edgecolor('lightgray')
        ax.grid(True, alpha=0.3)
        fig.colorbar(surf, ax=ax, shrink=0.5, aspect=12, pad=0.12)

    plt.tight_layout()
    plt.savefig(f"{FIG_DIR}/10_comparison_3d.png")
    plt.close()
    print("  Saved 10_comparison_3d.png")


def fig_finetune_3d():
    """3D comparison: zero-shot vs fine-tuned on unknown distribution."""
    data = np.load(f"{DATA_DIR}/data_test_unknown_128.npy")
    x = np.linspace(0, 1, 128)
    t_fine = np.linspace(0, 1, 80)
    X, T = np.meshgrid(x, t_fine)

    sample_idx = 0
    traj = data[sample_idx]
    traj_fine, _ = interpolate_trajectory(traj, n_time_fine=80)
    u0 = data[sample_idx, 0]

    fig = plt.figure(figsize=(20, 6))
    fig.suptitle("Transfer Learning — Unknown Distribution",
                 fontsize=18, fontweight='bold', y=1.02)

    panels = [
        ('Ground Truth', None, 'viridis'),
        ('Zero-Shot', 'all2all_best.pt', 'plasma'),
        ('Fine-Tuned', 'finetune_best.pt', 'cividis'),
    ]

    for i, (title, ckpt, cmap) in enumerate(panels):
        ax = fig.add_subplot(1, 3, i + 1, projection='3d')

        if ckpt is None:
            Z = traj_fine
        else:
            model = load_model(f"{CKPT_DIR}/{ckpt}", in_ch=3)
            Z = predict_all_times(model, u0, t_fine)

        surf = ax.plot_surface(
            X, T, Z, cmap=cmap, edgecolor='none', alpha=0.95,
            antialiased=True, rstride=1, cstride=1, shade=True
        )
        ax.set_xlabel('x', fontsize=11, labelpad=8)
        ax.set_ylabel('t', fontsize=11, labelpad=8)
        ax.set_zlabel('u', fontsize=11, labelpad=8)
        ax.set_title(title, fontsize=14, fontweight='bold', pad=10)
        ax.view_init(elev=25, azim=-55)
        ax.xaxis.pane.fill = False
        ax.yaxis.pane.fill = False
        ax.zaxis.pane.fill = False
        ax.xaxis.pane.set_edgecolor('lightgray')
        ax.yaxis.pane.set_edgecolor('lightgray')
        ax.zaxis.pane.set_edgecolor('lightgray')
        ax.grid(True, alpha=0.3)
        fig.colorbar(surf, ax=ax, shrink=0.5, aspect=12, pad=0.12)

    plt.tight_layout()
    plt.savefig(f"{FIG_DIR}/11_finetune_3d.png")
    plt.close()
    print("  Saved 11_finetune_3d.png")


def fig_bird_eye_heatmaps():
    """Top-down heatmap (x vs t) — cleaner view of the spatiotemporal field."""
    model = load_model(f"{CKPT_DIR}/all2all_best.pt", in_ch=3)
    data = np.load(f"{DATA_DIR}/data_test_128.npy")
    x = np.linspace(0, 1, 128)
    t_fine = np.linspace(0, 1, 80)

    sample_idx = 0
    traj = data[sample_idx]
    traj_fine, _ = interpolate_trajectory(traj, n_time_fine=80)
    u0 = data[sample_idx, 0]
    preds = predict_all_times(model, u0, t_fine)
    error = np.abs(traj_fine - preds)

    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    fig.suptitle("Spatiotemporal Heatmaps — x vs t", fontsize=16, fontweight='bold')

    for ax, Z, title, cmap in zip(
        axes,
        [traj_fine, preds, error],
        ['Ground Truth', 'FNO Prediction', '|Error|'],
        ['viridis', 'plasma', 'hot']
    ):
        im = ax.imshow(
            Z, aspect='auto', origin='lower', cmap=cmap,
            extent=[0, 1, 0, 1]
        )
        ax.set_xlabel('x (spatial)', fontsize=12)
        ax.set_ylabel('t (time)', fontsize=12)
        ax.set_title(title, fontsize=14, fontweight='bold')
        fig.colorbar(im, ax=ax, shrink=0.8)

    plt.tight_layout()
    plt.savefig(f"{FIG_DIR}/12_heatmaps.png")
    plt.close()
    print("  Saved 12_heatmaps.png")


if __name__ == "__main__":
    os.makedirs(FIG_DIR, exist_ok=True)
    print("Generating 3D visualizations...")
    fig_ground_truth_3d()
    fig_prediction_3d()
    fig_comparison_3d()
    fig_finetune_3d()
    fig_bird_eye_heatmaps()
    print("\nAll 3D figures saved to", FIG_DIR)
