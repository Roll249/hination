"""
Hination Disaster Prediction Model
Based on Spatio-Temporal Point Process methodology (Mateu et al., 2025)
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Tuple, Optional
import math


class SpatialEncoder(nn.Module):
    """
    CNN-based encoder for spatial features (weather grids, elevation, etc.)
    Architecture based on Mateu et al. CNN for point patterns
    """
    
    def __init__(
        self,
        in_channels: int = 4,
        grid_size: int = 64,
        dropout_rate: float = 0.2
    ):
        super().__init__()
        
        self.grid_size = grid_size
        
        # Convolutional Block 1
        self.conv1 = nn.Conv2d(in_channels, 32, kernel_size=3, padding=1)
        self.bn1 = nn.BatchNorm2d(32)
        self.pool1 = nn.MaxPool2d(2, 2)
        self.dropout1 = nn.Dropout2d(dropout_rate)
        
        # Convolutional Block 2
        self.conv2 = nn.Conv2d(32, 64, kernel_size=3, padding=1)
        self.bn2 = nn.BatchNorm2d(64)
        self.pool2 = nn.MaxPool2d(2, 2)
        self.dropout2 = nn.Dropout2d(dropout_rate + 0.1)
        
        # Convolutional Block 3
        self.conv3 = nn.Conv2d(64, 128, kernel_size=3, padding=1)
        self.bn3 = nn.BatchNorm2d(128)
        self.pool3 = nn.MaxPool2d(2, 2)
        self.dropout3 = nn.Dropout2d(dropout_rate + 0.1)
        
        # Calculate output size
        self.out_size = (grid_size // 8) ** 2 * 128  # 64 -> 32 -> 16 -> 8
        
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: (batch, channels, height, width)
        
        x = F.relu(self.bn1(self.conv1(x)))
        x = self.pool1(x)
        x = self.dropout1(x)
        
        x = F.relu(self.bn2(self.conv2(x)))
        x = self.pool2(x)
        x = self.dropout2(x)
        
        x = F.relu(self.bn3(self.conv3(x)))
        x = self.pool3(x)
        x = self.dropout3(x)
        
        return x


class TemporalEncoder(nn.Module):
    """
    LSTM-based encoder for temporal weather sequences
    Processes 24-hour weather history
    """
    
    def __init__(
        self,
        input_dim: int = 8,
        hidden_dim: int = 128,
        num_layers: int = 2,
        dropout: float = 0.3
    ):
        super().__init__()
        
        self.lstm = nn.LSTM(
            input_size=input_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0,
            bidirectional=True
        )
        
        self.output_dim = hidden_dim * 2  # Bidirectional
        
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: (batch, seq_len, input_dim)
        
        lstm_out, (hidden, cell) = self.lstm(x)
        
        # Concatenate forward and backward hidden states
        # hidden: (num_layers * 2, batch, hidden_dim)
        forward_hidden = hidden[-2, :, :]  # Last forward layer
        backward_hidden = hidden[-1, :, :]  # Last backward layer
        
        return torch.cat([forward_hidden, backward_hidden], dim=1)


class HawkesAttention(nn.Module):
    """
    Self-Attention mechanism based on Hawkes Process
    Models temporal clustering of disaster events
    """
    
    def __init__(self, feature_dim: int, num_heads: int = 4):
        super().__init__()
        
        self.attention = nn.MultiheadAttention(
            embed_dim=feature_dim,
            num_heads=num_heads,
            batch_first=True
        )
        
        self.norm = nn.LayerNorm(feature_dim)
        
    def forward(
        self, 
        temporal_features: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        # temporal_features: (batch, seq_len, feature_dim)
        
        attn_out, attn_weights = self.attention(
            temporal_features,
            temporal_features,
            temporal_features,
            key_padding_mask=attention_mask
        )
        
        return self.norm(temporal_features + attn_out)


class DisasterPredictionModel(nn.Module):
    """
    Multi-task model for disaster prediction and zonation
    
    Tasks:
    1. Flood Risk Classification
    2. Landslide Risk Classification
    3. Cold Wave Risk Classification
    4. Risk Zonation Map Generation
    """
    
    def __init__(
        self,
        spatial_channels: int = 4,
        temporal_input_dim: int = 8,
        temporal_seq_len: int = 24,
        grid_size: int = 64,
        num_classes: int = 3,
        dropout: float = 0.3
    ):
        super().__init__()
        
        # Spatial encoder (CNN)
        self.spatial_encoder = SpatialEncoder(
            in_channels=spatial_channels,
            grid_size=grid_size,
            dropout_rate=dropout
        )
        
        # Temporal encoder (LSTM)
        self.temporal_encoder = TemporalEncoder(
            input_dim=temporal_input_dim,
            hidden_dim=128,
            num_layers=2,
            dropout=dropout
        )
        
        # Hawkes-style attention
        self.hawkes_attention = HawkesAttention(
            feature_dim=128 * 2,  # Bidirectional output
            num_heads=4
        )
        
        # Calculate fusion input size
        spatial_feat_size = self.spatial_encoder.out_size
        temporal_feat_size = self.temporal_encoder.output_dim
        fusion_input_size = spatial_feat_size + temporal_feat_size
        
        # Fusion layer
        self.fusion = nn.Sequential(
            nn.Linear(fusion_input_size, 512),
            nn.BatchNorm1d(512),
            nn.ReLU(),
            nn.Dropout(dropout + 0.1),
            nn.Linear(512, 256),
            nn.BatchNorm1d(256),
            nn.ReLU(),
            nn.Dropout(dropout)
        )
        
        # Classification heads (one per disaster type)
        self.flood_head = nn.Linear(256, 1)
        self.landslide_head = nn.Linear(256, 1)
        self.cold_wave_head = nn.Linear(256, 1)
        
        # Zonation map decoder (transpose conv for upsampling)
        self.zonation_decoder = nn.Sequential(
            nn.ConvTranspose2d(256, 128, kernel_size=4, stride=2, padding=1),  # 8 -> 16
            nn.BatchNorm2d(128),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.ConvTranspose2d(128, 64, kernel_size=4, stride=2, padding=1),   # 16 -> 32
            nn.BatchNorm2d(64),
            nn.ReLU(),
            nn.ConvTranspose2d(64, 32, kernel_size=4, stride=2, padding=1),   # 32 -> 64
            nn.BatchNorm2d(32),
            nn.ReLU(),
            nn.Conv2d(32, num_classes, kernel_size=1)  # 64 -> 64, channels -> num_classes
        )
        
    def forward(
        self,
        spatial_input: torch.Tensor,
        temporal_input: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        Args:
            spatial_input: (batch, channels, height, width) - e.g., (32, 4, 64, 64)
            temporal_input: (batch, seq_len, features) - e.g., (32, 24, 8)
            attention_mask: Optional mask for attention
            
        Returns:
            flood_risk: (batch, 1) - probability of flood
            landslide_risk: (batch, 1) - probability of landslide
            cold_wave_risk: (batch, 1) - probability of cold wave
            zonation_map: (batch, classes, 64, 64) - risk probability per grid cell
        """
        
        # Spatial encoding
        spatial_features = self.spatial_encoder(spatial_input)
        batch_size = spatial_features.size(0)
        spatial_flat = spatial_features.view(batch_size, -1)
        
        # Temporal encoding
        temporal_features = self.temporal_encoder(temporal_input)
        
        # Hawkes attention on temporal features
        temporal_seq = temporal_input  # (batch, seq_len, features)
        temporal_attended = self.hawkes_attention(temporal_seq, attention_mask)
        
        # Use last time step after attention
        temporal_final = temporal_attended[:, -1, :]  # (batch, 256)
        
        # Fusion
        fused = torch.cat([spatial_flat, temporal_final], dim=1)
        fused_features = self.fusion(fused)
        
        # Classification outputs (sigmoid for probability)
        flood_risk = torch.sigmoid(self.flood_head(fused_features))
        landslide_risk = torch.sigmoid(self.landslide_head(fused_features))
        cold_wave_risk = torch.sigmoid(self.cold_wave_head(fused_features))
        
        # Zonation map
        zonation_input = fused_features.view(batch_size, 256, 1, 1)
        zonation_input = zonation_input.repeat(1, 1, 8, 8)  # Upsample to 8x8
        zonation_map = torch.sigmoid(self.zonation_decoder(zonation_input))
        
        return flood_risk, landslide_risk, cold_wave_risk, zonation_map


class HawkesProcessLoss(nn.Module):
    """
    Custom loss combining BCE for classification and
    Hawkes-inspired temporal clustering loss
    """
    
    def __init__(self, alpha: float = 0.3, beta: float = 0.1):
        super().__init__()
        self.alpha = alpha  # Weight for temporal loss
        self.beta = beta    # Decay factor
        
        self.bce = nn.BCELoss(reduction='mean')
        self.focal = FocalLoss(alpha=0.25, gamma=2)
        
    def forward(
        self,
        predictions: Tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor],
        targets: Tuple[torch.Tensor, torch.Tensor, torch.Tensor],
        zonation_targets: torch.Tensor
    ) -> dict:
        flood_pred, landslide_pred, cold_wave_pred, zonation_map = predictions
        flood_target, landslide_target, cold_wave_target = targets
        
        # BCE loss for each disaster type
        loss_flood = self.bce(flood_pred, flood_target)
        loss_landslide = self.bce(landslide_pred, landslide_target)
        loss_cold_wave = self.bce(cold_wave_pred, cold_wave_target)
        
        # Focal loss for hard examples
        loss_flood += 0.1 * self.focal(flood_pred, flood_target)
        loss_landslide += 0.1 * self.focal(landslide_pred, landslide_target)
        loss_cold_wave += 0.1 * self.focal(cold_wave_pred, cold_wave_target)
        
        # Zonation map loss (Dice-like)
        loss_zonation = self._dice_loss(zonation_map, zonation_targets)
        
        # Total loss
        total_loss = (
            loss_flood + loss_landslide + loss_cold_wave + 
            0.5 * loss_zonation
        )
        
        return {
            'total': total_loss,
            'flood': loss_flood,
            'landslide': loss_landslide,
            'cold_wave': loss_cold_wave,
            'zonation': loss_zonation
        }
    
    def _dice_loss(self, pred: torch.Tensor, target: torch.Tensor) -> torch.Tensor:
        smooth = 1e-6
        pred_flat = pred.view(pred.size(0), pred.size(1), -1)
        target_flat = target.view(target.size(0), target.size(1), -1)
        
        intersection = (pred_flat * target_flat).sum(dim=2)
        union = pred_flat.sum(dim=2) + target_flat.sum(dim=2)
        
        dice = (2 * intersection + smooth) / (union + smooth)
        return 1 - dice.mean()


class FocalLoss(nn.Module):
    """Focal loss for handling class imbalance"""
    
    def __init__(self, alpha: float = 0.25, gamma: float = 2):
        super().__init__()
        self.alpha = alpha
        self.gamma = gamma
        
    def forward(self, pred: torch.Tensor, target: torch.Tensor) -> torch.Tensor:
        bce = F.binary_cross_entropy(pred, target, reduction='none')
        pt = torch.exp(-bce)
        focal_loss = self.alpha * (1 - pt) ** self.gamma * bce
        return focal_loss.mean()


def get_model(config: dict) -> DisasterPredictionModel:
    """Factory function to create model with config"""
    model = DisasterPredictionModel(
        spatial_channels=config.get('spatial_channels', 4),
        temporal_input_dim=config.get('temporal_input_dim', 8),
        temporal_seq_len=config.get('temporal_seq_len', 24),
        grid_size=config.get('grid_size', 64),
        num_classes=config.get('num_classes', 3),
        dropout=config.get('dropout', 0.3)
    )
    return model


# Model configurations
MODEL_CONFIGS = {
    'small': {
        'spatial_channels': 4,
        'temporal_input_dim': 8,
        'temporal_seq_len': 24,
        'grid_size': 64,
        'num_classes': 3,
        'dropout': 0.3
    },
    'medium': {
        'spatial_channels': 6,
        'temporal_input_dim': 12,
        'temporal_seq_len': 48,
        'grid_size': 128,
        'num_classes': 4,
        'dropout': 0.4
    },
    'large': {
        'spatial_channels': 8,
        'temporal_input_dim': 16,
        'temporal_seq_len': 72,
        'grid_size': 256,
        'num_classes': 5,
        'dropout': 0.5
    }
}
