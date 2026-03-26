import numpy as np
import torch
from torch.utils.data import Dataset


class One2OneDataset(Dataset):
    """Dataset for one-to-one training: u(t=0) -> u(t=1.0).

    Args:
        data_path: Path to .npy file of shape (N, 5, S).
        resolution: Target spatial resolution (for interpolation). None = use native.
    """

    def __init__(self, data_path, resolution=None):
        data = np.load(data_path)  # (N, 5, S)
        self.input = torch.tensor(data[:, 0, :], dtype=torch.float32)   # u(t=0)
        self.target = torch.tensor(data[:, -1, :], dtype=torch.float32)  # u(t=1)

        if resolution is not None and resolution != self.input.shape[-1]:
            self.input = self._interpolate(self.input, resolution)
            self.target = self._interpolate(self.target, resolution)

    def _interpolate(self, x, size):
        # x: (N, S) -> (N, 1, S) -> interpolate -> (N, size)
        return torch.nn.functional.interpolate(
            x.unsqueeze(1), size=size, mode='linear', align_corners=True
        ).squeeze(1)

    def __len__(self):
        return self.input.shape[0]

    def __getitem__(self, idx):
        # Returns (input, target) each of shape (1, S) for conv1d
        return self.input[idx].unsqueeze(0), self.target[idx].unsqueeze(0)


class All2AllDataset(Dataset):
    """Dataset for all-to-all training: (u(t_i), t_i, t_j) -> u(t_j).

    Creates all valid (i, j) pairs where j > i from the 5 time snapshots.

    Args:
        data_path: Path to .npy file of shape (N, 5, S).
    """

    TIMES = [0.0, 0.25, 0.50, 0.75, 1.0]

    def __init__(self, data_path):
        data = np.load(data_path)  # (N, 5, S)
        self.data = torch.tensor(data, dtype=torch.float32)
        self.n_traj = data.shape[0]
        self.spatial_size = data.shape[2]

        # All pairs (i, j) with j > i
        self.pairs = [(i, j) for i in range(5) for j in range(i + 1, 5)]

    def __len__(self):
        return self.n_traj * len(self.pairs)

    def __getitem__(self, idx):
        traj_idx = idx // len(self.pairs)
        pair_idx = idx % len(self.pairs)
        t_i, t_j = self.pairs[pair_idx]

        u_input = self.data[traj_idx, t_i, :]  # (S,)
        u_target = self.data[traj_idx, t_j, :]  # (S,)

        # Input: stack [u(t_i), t_i_channel, t_j_channel] -> (3, S)
        t_i_channel = torch.full((self.spatial_size,), self.TIMES[t_i])
        t_j_channel = torch.full((self.spatial_size,), self.TIMES[t_j])
        x = torch.stack([u_input, t_i_channel, t_j_channel], dim=0)  # (3, S)

        return x, u_target.unsqueeze(0)  # (3, S), (1, S)


def load_test_data(data_path):
    """Load test data and return (inputs, targets) for evaluation at t=1.0.

    Returns:
        inputs: (N, 1, S) tensor of initial conditions
        targets: (N, 1, S) tensor of solutions at t=1.0
    """
    data = np.load(data_path)  # (N, 5, S)
    inputs = torch.tensor(data[:, 0, :], dtype=torch.float32).unsqueeze(1)
    targets = torch.tensor(data[:, -1, :], dtype=torch.float32).unsqueeze(1)
    return inputs, targets


def load_test_data_all_times(data_path):
    """Load test data for all2all evaluation at all future time steps.

    Returns:
        data: (N, 5, S) full trajectory tensor
    """
    data = np.load(data_path)
    return torch.tensor(data, dtype=torch.float32)
