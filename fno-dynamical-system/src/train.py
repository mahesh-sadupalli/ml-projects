import argparse
import os
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from tqdm import tqdm

from model import FNO1d
from dataset import (
    One2OneDataset, All2AllDataset,
    load_test_data, load_test_data_all_times
)
from evaluate import relative_l2_error, evaluate_one2one, evaluate_all2all


def train_epoch(model, loader, optimizer, criterion, device):
    model.train()
    total_loss = 0.0
    for x, y in loader:
        x, y = x.to(device), y.to(device)
        pred = model(x)
        loss = criterion(pred, y)
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        total_loss += loss.item() * x.shape[0]
    return total_loss / len(loader.dataset)


@torch.no_grad()
def val_epoch(model, loader, criterion, device):
    model.eval()
    total_loss = 0.0
    for x, y in loader:
        x, y = x.to(device), y.to(device)
        pred = model(x)
        loss = criterion(pred, y)
        total_loss += loss.item() * x.shape[0]
    return total_loss / len(loader.dataset)


def train(
    model, train_loader, val_loader, device,
    epochs=500, lr=1e-3, checkpoint_path=None, patience=50
):
    """Full training loop with Adam + ReduceLROnPlateau + early stopping."""
    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode='min', factor=0.5, patience=20
    )

    best_val_loss = float('inf')
    no_improve = 0

    for epoch in range(1, epochs + 1):
        train_loss = train_epoch(model, train_loader, optimizer, criterion, device)
        val_loss = val_epoch(model, val_loader, criterion, device)
        scheduler.step(val_loss)

        if epoch % 10 == 0 or epoch == 1:
            lr_now = optimizer.param_groups[0]['lr']
            print(f"Epoch {epoch:4d} | Train Loss: {train_loss:.6e} | "
                  f"Val Loss: {val_loss:.6e} | LR: {lr_now:.2e}")

        if val_loss < best_val_loss:
            best_val_loss = val_loss
            no_improve = 0
            if checkpoint_path:
                torch.save(model.state_dict(), checkpoint_path)
        else:
            no_improve += 1
            if no_improve >= patience:
                print(f"Early stopping at epoch {epoch}")
                break

    # Load best model
    if checkpoint_path and os.path.exists(checkpoint_path):
        model.load_state_dict(torch.load(checkpoint_path, weights_only=True))

    return model


def run_one2one(args):
    """Task 1: One-to-one training u0 -> u(t=1.0)."""
    device = torch.device(args.device)
    print("=" * 60)
    print("Task 1: One-to-One Training")
    print("=" * 60)

    train_ds = One2OneDataset(os.path.join(args.data_dir, "data_train_128.npy"))
    val_ds = One2OneDataset(os.path.join(args.data_dir, "data_val_128.npy"))

    train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=args.batch_size)

    model = FNO1d(
        modes=args.modes, width=args.width,
        in_channels=1, out_channels=1, n_layers=args.n_layers
    ).to(device)

    print(f"Model parameters: {sum(p.numel() for p in model.parameters()):,}")

    ckpt_path = os.path.join(args.checkpoint_dir, "one2one_best.pt")
    model = train(
        model, train_loader, val_loader, device,
        epochs=args.epochs, lr=args.lr, checkpoint_path=ckpt_path,
        patience=args.patience
    )

    # Evaluate on test sets at different resolutions (Task 2)
    print("\n" + "=" * 60)
    print("Task 2: Testing on Different Resolutions")
    print("=" * 60)

    for res in [32, 64, 96, 128]:
        test_path = os.path.join(args.data_dir, f"data_test_{res}.npy")
        if not os.path.exists(test_path):
            print(f"  Resolution {res:3d}: data not found, skipping")
            continue

        inputs, targets = load_test_data(test_path)

        # Interpolate inputs to training resolution (128) for prediction
        if res != 128:
            inputs_128 = torch.nn.functional.interpolate(
                inputs, size=128, mode='linear', align_corners=True
            )
        else:
            inputs_128 = inputs

        # Predict at training resolution
        model.eval()
        with torch.no_grad():
            preds_128 = model(inputs_128.to(device)).cpu()

        # Interpolate predictions back to test resolution for error computation
        if res != 128:
            preds = torch.nn.functional.interpolate(
                preds_128, size=res, mode='linear', align_corners=True
            )
        else:
            preds = preds_128

        err = relative_l2_error(preds, targets)
        print(f"  Resolution {res:3d}: Relative L2 Error = {err:.6f}")


def run_all2all(args):
    """Task 3: All-to-all time-dependent training."""
    device = torch.device(args.device)
    print("=" * 60)
    print("Task 3: All2All Training")
    print("=" * 60)

    train_ds = All2AllDataset(os.path.join(args.data_dir, "data_train_128.npy"))
    val_ds = All2AllDataset(os.path.join(args.data_dir, "data_val_128.npy"))

    train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=args.batch_size)

    # 3 input channels: u(t_i), t_i, t_j
    model = FNO1d(
        modes=args.modes, width=args.width,
        in_channels=3, out_channels=1, n_layers=args.n_layers
    ).to(device)

    print(f"Model parameters: {sum(p.numel() for p in model.parameters()):,}")

    ckpt_path = os.path.join(args.checkpoint_dir, "all2all_best.pt")
    model = train(
        model, train_loader, val_loader, device,
        epochs=args.epochs, lr=args.lr, checkpoint_path=ckpt_path,
        patience=args.patience
    )

    # Evaluate at t=1.0 on test set
    test_path = os.path.join(args.data_dir, "data_test_128.npy")
    if os.path.exists(test_path):
        test_data = load_test_data_all_times(test_path)

        print("\nEvaluation at t=1.0:")
        results = evaluate_all2all(model, test_data, device, target_times=[4])
        for t, err in results.items():
            print(f"  t={t:.2f}: Relative L2 Error = {err:.6f}")

        print("\nEvaluation at all time steps:")
        results = evaluate_all2all(model, test_data, device, target_times=[1, 2, 3, 4])
        for t, err in results.items():
            print(f"  t={t:.2f}: Relative L2 Error = {err:.6f}")


def run_finetune(args):
    """Task 4: Fine-tune all2all model on unknown distribution."""
    device = torch.device(args.device)
    print("=" * 60)
    print("Task 4: Fine-tuning on Unknown Distribution")
    print("=" * 60)

    # Load pretrained all2all model
    model = FNO1d(
        modes=args.modes, width=args.width,
        in_channels=3, out_channels=1, n_layers=args.n_layers
    ).to(device)

    pretrained_path = os.path.join(args.checkpoint_dir, "all2all_best.pt")
    if not os.path.exists(pretrained_path):
        print(f"Error: Pretrained model not found at {pretrained_path}")
        print("Run --mode all2all first.")
        return

    # Zero-shot evaluation
    model.load_state_dict(torch.load(pretrained_path, weights_only=True))
    test_path = os.path.join(args.data_dir, "data_test_unknown_128.npy")

    if os.path.exists(test_path):
        test_data = load_test_data_all_times(test_path)
        results = evaluate_all2all(model, test_data, device, target_times=[4])
        print(f"\nZero-shot (before fine-tuning):")
        for t, err in results.items():
            print(f"  t={t:.2f}: Relative L2 Error = {err:.6f}")

    # Fine-tune
    ft_train_path = os.path.join(args.data_dir, "data_finetune_train_unknown_128.npy")
    ft_val_path = os.path.join(args.data_dir, "data_finetune_val_unknown_128.npy")

    if not os.path.exists(ft_train_path):
        print(f"Fine-tuning data not found at {ft_train_path}")
        return

    train_ds = All2AllDataset(ft_train_path)
    val_ds = All2AllDataset(ft_val_path)

    train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=args.batch_size)

    # Fine-tune with lower learning rate
    ckpt_path = os.path.join(args.checkpoint_dir, "finetune_best.pt")
    model = train(
        model, train_loader, val_loader, device,
        epochs=args.ft_epochs, lr=args.lr * 0.1, checkpoint_path=ckpt_path,
        patience=args.patience
    )

    if os.path.exists(test_path):
        test_data = load_test_data_all_times(test_path)
        results = evaluate_all2all(model, test_data, device, target_times=[4])
        print(f"\nAfter fine-tuning:")
        for t, err in results.items():
            print(f"  t={t:.2f}: Relative L2 Error = {err:.6f}")


def run_from_scratch(args):
    """Task 4 Bonus: Train from scratch on unknown distribution."""
    device = torch.device(args.device)
    print("=" * 60)
    print("Task 4 Bonus: Training from Scratch on Unknown Distribution")
    print("=" * 60)

    ft_train_path = os.path.join(args.data_dir, "data_finetune_train_unknown_128.npy")
    ft_val_path = os.path.join(args.data_dir, "data_finetune_val_unknown_128.npy")

    train_ds = All2AllDataset(ft_train_path)
    val_ds = All2AllDataset(ft_val_path)

    train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=args.batch_size)

    model = FNO1d(
        modes=args.modes, width=args.width,
        in_channels=3, out_channels=1, n_layers=args.n_layers
    ).to(device)

    print(f"Model parameters: {sum(p.numel() for p in model.parameters()):,}")

    ckpt_path = os.path.join(args.checkpoint_dir, "from_scratch_best.pt")
    model = train(
        model, train_loader, val_loader, device,
        epochs=args.epochs, lr=args.lr, checkpoint_path=ckpt_path,
        patience=args.patience
    )

    test_path = os.path.join(args.data_dir, "data_test_unknown_128.npy")
    if os.path.exists(test_path):
        test_data = load_test_data_all_times(test_path)
        results = evaluate_all2all(model, test_data, device, target_times=[4])
        print(f"\nTrained from scratch:")
        for t, err in results.items():
            print(f"  t={t:.2f}: Relative L2 Error = {err:.6f}")


def main():
    parser = argparse.ArgumentParser(description="FNO for Dynamical Systems")
    parser.add_argument("--mode", type=str, required=True,
                        choices=["one2one", "all2all", "finetune", "from_scratch"],
                        help="Training mode")
    parser.add_argument("--data_dir", type=str, default="data/",
                        help="Path to data directory")
    parser.add_argument("--checkpoint_dir", type=str, default="checkpoints/",
                        help="Path to save checkpoints")
    # FFT ops require CPU on Mac (MPS doesn't support complex tensors)
    parser.add_argument("--device", type=str, default="cuda" if torch.cuda.is_available() else "cpu")

    # Model hyperparameters
    parser.add_argument("--modes", type=int, default=16, help="Number of Fourier modes")
    parser.add_argument("--width", type=int, default=64, help="Hidden channel width")
    parser.add_argument("--n_layers", type=int, default=4, help="Number of Fourier layers")

    # Training hyperparameters
    parser.add_argument("--epochs", type=int, default=500)
    parser.add_argument("--ft_epochs", type=int, default=200, help="Fine-tuning epochs")
    parser.add_argument("--batch_size", type=int, default=32)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--patience", type=int, default=50, help="Early stopping patience")

    args = parser.parse_args()
    os.makedirs(args.checkpoint_dir, exist_ok=True)

    print(f"Device: {args.device}")
    print(f"Modes: {args.modes}, Width: {args.width}, Layers: {args.n_layers}")
    print()

    if args.mode == "one2one":
        run_one2one(args)
    elif args.mode == "all2all":
        run_all2all(args)
    elif args.mode == "finetune":
        run_finetune(args)
    elif args.mode == "from_scratch":
        run_from_scratch(args)


if __name__ == "__main__":
    main()
