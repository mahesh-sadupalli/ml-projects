"""Quick evaluation and remaining tasks using saved checkpoints."""
import os
import torch
from model import FNO1d
from dataset import All2AllDataset, load_test_data_all_times
from evaluate import evaluate_all2all
from train import train

from torch.utils.data import DataLoader

DATA_DIR = "../data"
CKPT_DIR = "../checkpoints"
DEVICE = "cpu"

MODES = 16
WIDTH = 64
N_LAYERS = 4


def make_model(in_ch=3):
    return FNO1d(modes=MODES, width=WIDTH, in_channels=in_ch, out_channels=1, n_layers=N_LAYERS)


def task3_eval():
    """Evaluate all2all model at all time steps."""
    print("=" * 60)
    print("Task 3: All2All Evaluation")
    print("=" * 60)

    model = make_model(in_ch=3).to(DEVICE)
    model.load_state_dict(torch.load(f"{CKPT_DIR}/all2all_best.pt", weights_only=True))

    test_data = load_test_data_all_times(f"{DATA_DIR}/data_test_128.npy")

    print("\nPredictions at t=1.0 (compare with Task 1):")
    results = evaluate_all2all(model, test_data, DEVICE, target_times=[4])
    for t, err in results.items():
        print(f"  t={t:.2f}: Relative L2 Error = {err:.6f}")

    print("\nPredictions at all time steps:")
    results = evaluate_all2all(model, test_data, DEVICE, target_times=[1, 2, 3, 4])
    for t, err in results.items():
        print(f"  t={t:.2f}: Relative L2 Error = {err:.6f}")


def task4_finetune():
    """Fine-tune all2all model on unknown distribution."""
    print("\n" + "=" * 60)
    print("Task 4: Fine-tuning on Unknown Distribution")
    print("=" * 60)

    # Zero-shot evaluation
    model = make_model(in_ch=3).to(DEVICE)
    model.load_state_dict(torch.load(f"{CKPT_DIR}/all2all_best.pt", weights_only=True))

    test_data = load_test_data_all_times(f"{DATA_DIR}/data_test_unknown_128.npy")
    results = evaluate_all2all(model, test_data, DEVICE, target_times=[4])
    print(f"\nZero-shot (no fine-tuning):")
    for t, err in results.items():
        print(f"  t={t:.2f}: Relative L2 Error = {err:.6f}")

    # Fine-tune
    train_ds = All2AllDataset(f"{DATA_DIR}/data_finetune_train_unknown_128.npy")
    val_ds = All2AllDataset(f"{DATA_DIR}/data_finetune_val_unknown_128.npy")
    train_loader = DataLoader(train_ds, batch_size=32, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=32)

    print(f"\nFine-tuning ({len(train_ds)} pairs from 32 trajectories)...")
    model = train(
        model, train_loader, val_loader, DEVICE,
        epochs=200, lr=1e-4, checkpoint_path=f"{CKPT_DIR}/finetune_best.pt",
        patience=30
    )

    results = evaluate_all2all(model, test_data, DEVICE, target_times=[4])
    print(f"\nAfter fine-tuning:")
    for t, err in results.items():
        print(f"  t={t:.2f}: Relative L2 Error = {err:.6f}")


def task4_from_scratch():
    """Train from scratch on unknown distribution (bonus)."""
    print("\n" + "=" * 60)
    print("Task 4 Bonus: Training from Scratch on Unknown Distribution")
    print("=" * 60)

    train_ds = All2AllDataset(f"{DATA_DIR}/data_finetune_train_unknown_128.npy")
    val_ds = All2AllDataset(f"{DATA_DIR}/data_finetune_val_unknown_128.npy")
    train_loader = DataLoader(train_ds, batch_size=32, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=32)

    model = make_model(in_ch=3).to(DEVICE)
    print(f"\nTraining from scratch ({len(train_ds)} pairs from 32 trajectories)...")
    model = train(
        model, train_loader, val_loader, DEVICE,
        epochs=300, lr=1e-3, checkpoint_path=f"{CKPT_DIR}/from_scratch_best.pt",
        patience=40
    )

    test_data = load_test_data_all_times(f"{DATA_DIR}/data_test_unknown_128.npy")
    results = evaluate_all2all(model, test_data, DEVICE, target_times=[4])
    print(f"\nTrained from scratch:")
    for t, err in results.items():
        print(f"  t={t:.2f}: Relative L2 Error = {err:.6f}")


if __name__ == "__main__":
    task3_eval()
    task4_finetune()
    task4_from_scratch()
