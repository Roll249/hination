# Hination - Disaster Prediction Model

## Requirements

```
torch>=2.0.0
numpy>=1.24.0
scipy>=1.10.0
matplotlib>=3.7.0
tensorboard>=2.13.0
```

## Quick Start

```bash
# Install dependencies
pip install torch numpy scipy matplotlib tensorboard

# Train model (1 hour)
python train.py --samples 10000 --epochs 50 --batch-size 32

# Train with GPU
python train.py --samples 50000 --epochs 100 --batch-size 64
```

## Model Architecture

The model combines:
- **CNN** for spatial feature extraction from weather grids
- **LSTM** for temporal sequence modeling
- **Hawkes Attention** for temporal clustering
- **Multi-task heads** for flood, landslide, and cold wave prediction

## Training

```bash
# Small model (fast training)
python train.py --model-size small

# Medium model (balanced)
python train.py --model-size medium --samples 50000

# Large model (best accuracy)
python train.py --model-size large --samples 100000
```

## Prediction

```python
from model import DisasterPredictionModel, get_model
import torch

# Load model
model = get_model({'model_size': 'small'})
model.load_state_dict(torch.load('checkpoints/latest.pt')['model_state_dict'])
model.eval()

# Predict
with torch.no_grad():
    spatial_input = torch.randn(1, 4, 64, 64)  # (batch, channels, H, W)
    temporal_input = torch.randn(1, 24, 8)  # (batch, seq_len, features)
    
    flood, landslide, cold_wave, zonation = model(spatial_input, temporal_input)
```

## API Integration

The model can be served via FastAPI:

```python
from fastapi import FastAPI
import torch

app = FastAPI()

@app.post("/predict")
async def predict(weather_data: WeatherData):
    # Prepare input tensors
    # Run inference
    return predictions
```
