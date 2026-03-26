import torch
import numpy as np


def relative_l2_error(pred, target):
    """Compute per-sample relative L2 error.

    Args:
        pred: (N, 1, S) or (N, S) predicted solutions
        target: (N, 1, S) or (N, S) true solutions

    Returns:
        Scalar average relative L2 error
    """
    pred = pred.reshape(pred.shape[0], -1)
    target = target.reshape(target.shape[0], -1)

    diff_norm = torch.norm(pred - target, dim=1)
    target_norm = torch.norm(target, dim=1)

    return (diff_norm / target_norm).mean().item()


@torch.no_grad()
def evaluate_one2one(model, inputs, targets, device, batch_size=64):
    """Evaluate one2one model on test data.

    Args:
        model: Trained FNO model
        inputs: (N, 1, S) initial conditions
        targets: (N, 1, S) true solutions at t=1.0
        device: torch device
        batch_size: Evaluation batch size

    Returns:
        Average relative L2 error
    """
    model.eval()
    all_preds = []

    for i in range(0, len(inputs), batch_size):
        batch_in = inputs[i:i + batch_size].to(device)
        pred = model(batch_in)
        all_preds.append(pred.cpu())

    preds = torch.cat(all_preds, dim=0)
    return relative_l2_error(preds, targets)


@torch.no_grad()
def evaluate_all2all(model, data, device, target_times=None, batch_size=64):
    """Evaluate all2all model on test data.

    Args:
        model: Trained FNO model (in_channels=3)
        data: (N, 5, S) full trajectory data
        device: torch device
        target_times: List of time indices to evaluate. Default: [4] (t=1.0 only)
        batch_size: Evaluation batch size

    Returns:
        Dict mapping time index -> relative L2 error
    """
    model.eval()
    times = [0.0, 0.25, 0.50, 0.75, 1.0]

    if target_times is None:
        target_times = [4]

    results = {}
    n_samples = data.shape[0]
    spatial_size = data.shape[2]

    for t_j in target_times:
        all_preds = []
        all_targets = []

        for i in range(0, n_samples, batch_size):
            batch_data = data[i:i + batch_size]
            bs = batch_data.shape[0]

            u_input = batch_data[:, 0, :]  # (bs, S)
            u_target = batch_data[:, t_j, :]  # (bs, S)

            t_i_ch = torch.full((bs, spatial_size), times[0])
            t_j_ch = torch.full((bs, spatial_size), times[t_j])
            x = torch.stack([u_input, t_i_ch, t_j_ch], dim=1).to(device)  # (bs, 3, S)

            pred = model(x)
            all_preds.append(pred.cpu())
            all_targets.append(u_target.unsqueeze(1))

        preds = torch.cat(all_preds, dim=0)
        targets = torch.cat(all_targets, dim=0)
        results[times[t_j]] = relative_l2_error(preds, targets)

    return results
