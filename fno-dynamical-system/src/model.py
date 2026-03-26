import torch
import torch.nn as nn
import torch.nn.functional as F


class SpectralConv1d(nn.Module):
    """Spectral convolution layer — learns weights in Fourier space."""

    def __init__(self, in_channels, out_channels, modes):
        super().__init__()
        self.in_channels = in_channels
        self.out_channels = out_channels
        self.modes = modes

        scale = 1 / (in_channels * out_channels)
        self.weights = nn.Parameter(
            scale * torch.rand(in_channels, out_channels, modes, dtype=torch.cfloat)
        )

    def forward(self, x):
        # x: (batch, channels, spatial)
        batchsize = x.shape[0]
        x_ft = torch.fft.rfft(x)

        out_ft = torch.zeros(
            batchsize, self.out_channels, x.size(-1) // 2 + 1,
            dtype=torch.cfloat, device=x.device
        )
        out_ft[:, :, :self.modes] = torch.einsum(
            "bix,iox->box", x_ft[:, :, :self.modes], self.weights
        )

        return torch.fft.irfft(out_ft, n=x.size(-1))


class FourierLayer(nn.Module):
    """Single Fourier layer: spectral conv (global) + linear (local) + activation."""

    def __init__(self, width, modes):
        super().__init__()
        self.spectral_conv = SpectralConv1d(width, width, modes)
        self.linear = nn.Conv1d(width, width, 1)

    def forward(self, x):
        return F.gelu(self.spectral_conv(x) + self.linear(x))


class FNO1d(nn.Module):
    """Fourier Neural Operator for 1D problems.

    Args:
        modes: Number of Fourier modes to keep.
        width: Hidden channel dimension.
        in_channels: Number of input channels.
        out_channels: Number of output channels.
        n_layers: Number of Fourier layers.
    """

    def __init__(self, modes=16, width=64, in_channels=1, out_channels=1, n_layers=4):
        super().__init__()
        self.modes = modes
        self.width = width
        self.n_layers = n_layers

        # Lifting: input channels -> width
        self.lift = nn.Conv1d(in_channels, width, 1)

        # Fourier layers
        self.fourier_layers = nn.ModuleList([
            FourierLayer(width, modes) for _ in range(n_layers)
        ])

        # Projection: width -> out_channels
        self.project = nn.Sequential(
            nn.Conv1d(width, 128, 1),
            nn.GELU(),
            nn.Conv1d(128, out_channels, 1),
        )

    def forward(self, x):
        # x: (batch, in_channels, spatial)
        x = self.lift(x)

        for layer in self.fourier_layers:
            x = layer(x)

        x = self.project(x)
        return x
