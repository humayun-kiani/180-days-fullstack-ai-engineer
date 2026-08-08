# ============================================================
# src/model.py
# Neural network architecture definitions
# ============================================================

import torch
import torch.nn as nn
import torch.nn.functional as F


class TaskPriorityNet(nn.Module):
    """
    Feed-forward neural network for task priority classification.

    Architecture:
        Input (35) → FC(128) → BN → ReLU → Dropout
                   → FC(64)  → BN → ReLU → Dropout
                   → FC(32)  → BN → ReLU → Dropout
                   → FC(4)   → LogSoftmax

    Components:
        - Linear: learnable weights + bias (core computation)
        - BatchNorm1d: normalize activations → stable training
        - ReLU: non-linearity → model can learn complex patterns
        - Dropout: randomly zero neurons → prevents overfitting
        - LogSoftmax: convert logits to log-probabilities
    """

    def __init__(
        self,
        input_size: int = 35,
        hidden_sizes: list[int] = None,
        num_classes: int = 4,
        dropout_rate: float = 0.3
    ):
        super().__init__()

        if hidden_sizes is None:
            hidden_sizes = [128, 64, 32]

        self.input_size = input_size
        self.hidden_sizes = hidden_sizes
        self.num_classes = num_classes
        self.dropout_rate = dropout_rate

        # Build network layers dynamically
        layers = []
        prev_size = input_size

        for i, hidden_size in enumerate(hidden_sizes):
            layers.extend([
                nn.Linear(prev_size, hidden_size),
                nn.BatchNorm1d(hidden_size),
                nn.ReLU(inplace=True),
                nn.Dropout(p=dropout_rate)
            ])
            prev_size = hidden_size

        # Output layer — no activation here
        # CrossEntropyLoss expects raw logits
        layers.append(nn.Linear(prev_size, num_classes))

        self.network = nn.Sequential(*layers)

        # Initialize weights with Xavier uniform
        # Better than random for deep networks
        self._init_weights()

    def _init_weights(self):
        """Initialize weights using Xavier uniform initialization."""
        for module in self.modules():
            if isinstance(module, nn.Linear):
                nn.init.xavier_uniform_(module.weight)
                nn.init.zeros_(module.bias)
            elif isinstance(module, nn.BatchNorm1d):
                nn.init.ones_(module.weight)
                nn.init.zeros_(module.bias)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass through the network.

        Args:
            x: Input tensor of shape (batch_size, input_size)

        Returns:
            torch.Tensor: Raw logits of shape (batch_size, num_classes)
        """
        return self.network(x)

    def predict_proba(self, x: torch.Tensor) -> torch.Tensor:
        """Get class probabilities (for inference)."""
        self.eval()
        with torch.no_grad():
            logits = self.forward(x)
            return F.softmax(logits, dim=1)

    def count_parameters(self) -> int:
        """Count total trainable parameters."""
        return sum(p.numel() for p in self.parameters() if p.requires_grad)

    def architecture_summary(self) -> str:
        """Return human-readable architecture description."""
        lines = [
            "TaskPriorityNet Architecture",
            "=" * 40,
            f"Input:  {self.input_size} features",
        ]
        prev = self.input_size
        for h in self.hidden_sizes:
            params = prev * h + h
            lines.append(f"  FC({prev} → {h}) + BN + ReLU + Dropout({self.dropout_rate})")
            lines.append(f"    Parameters: {params:,}")
            prev = h
        out_params = prev * self.num_classes + self.num_classes
        lines.append(f"Output: FC({prev} → {self.num_classes})")
        lines.append(f"    Parameters: {out_params:,}")
        lines.append("=" * 40)
        lines.append(f"Total: {self.count_parameters():,} parameters")
        return "\n".join(lines)


class ResidualBlock(nn.Module):
    """
    Residual block for deeper networks.

    Adds a skip connection: output = F(x) + x
    This helps gradient flow in very deep networks.
    """

    def __init__(self, size: int, dropout_rate: float = 0.3):
        super().__init__()
        self.block = nn.Sequential(
            nn.Linear(size, size),
            nn.BatchNorm1d(size),
            nn.ReLU(inplace=True),
            nn.Dropout(p=dropout_rate),
            nn.Linear(size, size),
            nn.BatchNorm1d(size)
        )
        self.relu = nn.ReLU(inplace=True)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.relu(self.block(x) + x)    # skip connection


class TaskPriorityResNet(nn.Module):
    """
    Deeper network with residual connections.

    Good for learning subtle patterns that require depth.
    """

    def __init__(
        self,
        input_size: int = 35,
        base_size: int = 128,
        num_blocks: int = 3,
        num_classes: int = 4,
        dropout_rate: float = 0.3
    ):
        super().__init__()

        # Project to base_size
        self.input_projection = nn.Sequential(
            nn.Linear(input_size, base_size),
            nn.BatchNorm1d(base_size),
            nn.ReLU(inplace=True)
        )

        # Residual blocks
        self.residual_blocks = nn.ModuleList([
            ResidualBlock(base_size, dropout_rate)
            for _ in range(num_blocks)
        ])

        # Output
        self.output_layer = nn.Sequential(
            nn.Linear(base_size, base_size // 2),
            nn.ReLU(inplace=True),
            nn.Linear(base_size // 2, num_classes)
        )

        self._init_weights()

    def _init_weights(self):
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.xavier_uniform_(m.weight)
                nn.init.zeros_(m.bias)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.input_projection(x)
        for block in self.residual_blocks:
            x = block(x)
        return self.output_layer(x)

    def count_parameters(self) -> int:
        return sum(p.numel() for p in self.parameters() if p.requires_grad)