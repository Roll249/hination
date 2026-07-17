# PDF Analysis: Spatial and Spatio-temporal Point Processes for Disaster Zonation

**Source:** Jorge Mateu, University Jaume I, Spain  
**Presented at:** 14th European Congress for Stereology and Image Analysis (ECSIA), September 2025  
**Date Analyzed:** July 2026

---

## Executive Summary

This presentation covers statistical learning methods for spatio-temporal point processes, with applications ranging from ecological modeling to crime prediction. The methodologies presented have direct applicability to **disaster zonation and early warning systems** for events such as floods, landslides, and extreme weather patterns in regions like Điện Biên, Vietnam.

---

## 1. Mathematical Foundations

### 1.1 Spatial Point Process Definition

A spatial point process is a stochastic process whose realizations are point patterns in a bounded region $W \subset \mathbb{R}^2$.

**Key formulations:**

1. **Density-based:** First choose $n \sim p_n$, then draw points $x_1, ..., x_n$ from a joint density $f_n(x_1, ..., x_n)$

2. **Binary grid approximation:** Model presence/absence in pixels via binary variables $I_j$

3. **Measure-theoretic:** Treat the process as a random integer-valued measure $N(B)$ over test sets $B$

### 1.2 Likelihood Functions

For spatial point processes, the likelihood has the form:

$$L(\theta | x) = \frac{f(x_1, ..., x_n)}{Z(\theta)}$$

Where:
- $f$: potential function (encodes interaction, aggregation)
- $Z(\theta)$: normalizing constant ensuring total probability integrates to 1

**Key Challenge:** The normalizing constant $Z(\theta)$ is intractable in most practical models.

### 1.3 Point Process Types

| Process Type | Description | Characteristics |
|-------------|-------------|-----------------|
| **Poisson Process** | Baseline homogeneous process | Complete spatial randomness |
| **Log-Gaussian Cox Process (LGCP)** | Doubly stochastic with log-Gaussian intensity | Captures overdispersion and spatial heterogeneity |
| **Thomas Process** | Cluster process with Poisson parents | Circular clusters with random centers |
| **Matérn Cluster Process** | Thomas variant with uniform disc distribution | Fixed cluster radius |
| **Strauss Process** | Gibbs process with pairwise interaction | Repulsion/inhibition between points |
| **Hawkes Process** | Self-exciting process | Time clustering, triggering effects |

---

## 2. Methodology 1: Siamese Neural Networks for Pattern Classification

### 2.1 Problem Statement

Given spatial point patterns, classify whether two patterns come from the same underlying process or different processes.

### 2.2 Dissimilarity Functions

**Dissimilarity function properties:**
- $D(x, x') \rightarrow 0$ when $s_i = s_i'$ (similar patterns)
- $D(x, x') \rightarrow \infty$ when $s_i \neq s_i'$ (different patterns)

**Pattern matching vs. process matching:**
- Pattern matching: compares similarities of observed point patterns
- Process matching: compares the generative point processes

### 2.3 Summary Statistics

**First-order statistics (Intensity):**
$$\hat{\rho}(u;x) = \sum_{v \in x} k(u - v')$$

**Second-order statistics (K-function):**
$$\hat{K}(r;x) = \frac{1}{\hat{\rho}(u;x)\hat{\rho}(v;x)|W \cap u - v|} \sum_{u \neq v} \mathbb{1}_{[||u-v|| \leq r]}$$

**Pair correlation function:**
$$g(r;x) = \frac{1}{2\pi r \hat{\rho}(u;x)\hat{\rho}(v;x)|W \cap u - v|} \sum_{u \neq v} \mathbb{1}_{[||u-v|| \leq r]}$$

### 2.4 CNN Feature Extraction Architecture

**Discretization:** Partition observation window $W$ into $d_1 \times d_2$ grid cells

**Convolutional layers:**
1. Input: discretized point pattern $\tilde{x} = [x_{ij}]$
2. Convolution with $d_1^{(1)} \times d_2^{(1)}$ kernels/filters
3. Apply activation functions (ReLU)
4. Pooling (mean, sum, or max)

**Network architecture:**
- Multiple convolutional + pooling layers
- Final perceptron layer produces feature vector $G = [g_1, ..., g_{\ell_L}]$

**Vector of parameters:**
$$\vartheta = \{b_0^{(l,k)}, F_{i,j}^{(l,k,k')}, w_{ij}^{(k,k')} \}$$

### 2.5 Discriminant Model

**Response variable:**
$$y(x(s_1,t_1), x(s_2,t_2)) = \begin{cases} 1 & s_1 = s_2 \\ 0 & s_1 \neq s_2 \end{cases}$$

**Siamese network architecture:**
```
x → CNN → G_ϑ(x)
x' → CNN → G_ϑ(x')
         ↓
    |G_ϑ(x) - G_ϑ(x')|
         ↓
    p_θ(x, x') = f_{L+1}(\beta_0 + \sum_k \beta_k ||G_ϑ(x) - G_ϑ(x')||_k)
```

### 2.6 Training Procedure

**Parameter estimation:** Maximize Bernoulli composite log-likelihood:
$$l(\theta; D_{train}) = \sum_{\{x,x'\} \subset D_{train}} \left[ y(x,x')\log p_\theta(x,x') + \log(1 - p_\theta(x,x')) \right]$$

**Hyperparameters:**
- Discretization grid dimensions $(d_1, d_2)$
- Number of layers $L$
- Nodes at each layer $\ell_1, ..., \ell_L$
- Pooling dimensions and functions

---

## 3. Methodology 2: Second Order Preserving (SOP) Permutations

### 3.1 Problem

When testing interactions between spatial-temporal point processes, random permutations may not preserve second-order statistics of the original data.

### 3.2 L-Function

The L-function captures spatial clustering:
$$L(r) = [K(r)]^{1/2}$$

Where $K(r)$ is the second-order statistic:
$$K(r) = \frac{1}{N^2} \sum_{i,j} \mathbb{1}_{[||z_i - z_j|| < r]}$$

### 3.3 SOP Algorithm

**Stage 1:** Generate M random permutations and compute mean L-function:
$$\mu(r) = \frac{1}{M} \sum_{k=1}^{M} L_k(r)$$

**Stage 2:** Iteratively swap times to minimize error:
$$\text{error} = \left( \int [L_{prop}(r) - L_{data}(r) - \epsilon_k(r)]^2 dr \right)^{1/2}$$

### 3.4 Application to Data Augmentation

**Use case:** CNN-LSTM for 1-day ahead point process forecasting

**Process:**
1. Discretize space into $25 \times 25$ grid cells
2. Time into 1-day intervals
3. Create $14 \times 25 \times 25$ binary feature tensors
4. Apply SOP augmentation (10x data increase)
5. Train CNN-LSTM to predict next-day events

**Results:** SOP-augmented training showed improved AUC on held-out data.

---

## 4. Methodology 3: Spatio-Temporal Network Point Processes (STNPP)

### 4.1 Application Context

Crime incident modeling in Valencia, Spain, with landmark-based urban zoning:
- 47,125 crime events (2015-2019)
- 1,975 city landmarks (7 categories)
- 3 crime types: Assault, Subtraction, Others

### 4.2 Hawkes Process Model

**Conditional intensity function:**
$$\lambda_{cl}(t, s) = \mu_{cl} + \sum_{(t',s',c' \times l') \in H_t} \alpha_{cl,c'l'} \beta e^{-\beta(t-t')} \frac{1}{2\pi\sigma^2} e^{-\frac{d_{net}(s,s')^2}{2\sigma^2}}$$

**Components:**
- $\mu_{cl}$: baseline intensity
- Temporal kernel: $\beta e^{-\beta(t-t')}$
- Spatial kernel: Gaussian on street network
- Mark interaction: $\alpha_{cl,c'l'}$

### 4.3 Urban Functional Zoning

**Zone assignment:**
1. For each location $s$, find k nearest landmarks
2. Assign zone $\ell(s)$ as most common landmark category
3. Partition city into $\{S_\ell\}_{\ell \in L}$

**Event marks:** Concatenation of crime category $c$ and landmark category $\ell(s)$
- Mark space size: $|C \times L| = 3 \times 7 = 21$

### 4.4 Graph Attention Networks for Influence Learning

**Decomposition of coefficients:**
$$\alpha_{cl,c'l'} = a_{cl,c'l'} \cdot p_{cl,c'l'}$$

Where:
- $p_{cl,c'l'}$: chance of interaction (graph topology)
- $a_{cl,c'l'}$: strength of interaction (learned weight)

**Attention mechanism:**
$$e_{cl,c'l'}^r = \gamma(W^r X_{cl}, W^r X_{c'l'})$$

**Normalized attention:**
$$p_{cl,c'l'}^r = \text{softmax}\left( \frac{\exp(\text{LeakyReLU}(b^r [W^r X_{cl} - W^r X_{c'l'}]))}{\sum \exp(\text{LeakyReLU}(b^r [W^r X_{cl} - W^r X_{c'l'}]))} \right)$$

### 4.5 Model Results

| Model | MAE(rare) | MAE(frequent) | MAE(total) | Log-likelihood |
|-------|-----------|----------------|-------------|----------------|
| Persistent | 0.998 | 5.736 | 31.538 | - |
| VAR | 0.906 | 3.680 | 21.940 | - |
| ETAS | 0.785 | 4.266 | 30.925 | -2.476 |
| STNPP-GAT | 0.728 | 3.875 | 21.561 | -2.427 |
| **STNPP** | **0.716** | **3.708** | **20.080** | **-2.413** |

---

## 5. Methodology 4: Non-Stationary Deep Spatial-Temporal Modeling

### 5.1 Application

COVID-19 case modeling in Cali, Colombia:
- 38,611 cases (March-September 2020)
- Daily temporal resolution
- Longitude/latitude spatial coordinates

### 5.2 Non-Stationary Kernel

**Challenge:** Heterogeneous spread patterns in different areas

**Kernel decomposition:**
$$k(t, t', s, s') = \nu(t, t') \cdot v(s, s')$$

**Spatial kernel (non-stationary):**
$$v(s, s') = \langle \phi(s), \phi(s') \rangle = \sum_{r=1}^{R} w_r \kappa_r(\cdot), \sum_{r=1}^{R} w_r \kappa_r(\cdot)$$

Where $\kappa_r$ are Gaussian components centered at location $s$ with covariance $\Sigma_s$.

### 5.3 Neural Network Mapping

Covariance matrices smoothly vary over space via neural networks:
$$\Sigma_s = f_{NN}(s)$$

### 5.4 Efficient Computation

**Log-likelihood:**
$$\ell(\theta) = -\sum_{i=1}^{n} \log \lambda(t_i, s_i) + \int_0^T \int_S \lambda(\tau, u) du d\tau$$

**Challenge:** $O(N^3)$ complexity for direct computation

**Solution:** Approximated to $O(N)$ complexity (5 seconds/epoch vs 5 minutes/epoch)

---

## 6. Methodology 5: Neural Likelihood Inference

### 6.1 Likelihood-Free Inference via CNN

**Problem:** Intractable normalizing constants in most point process models

**Solution:** Binary classifier as likelihood proxy

**Training process:**
1. Sample parameters $\theta_1, ..., \theta_m$ (Latin Hypercube Sampling)
2. Simulate realizations $y_{i,1}, ..., y_{i,n_i} \sim p(y | \theta_i)$
3. Create null class by permuting: $C_2 = \{(y_i, \theta_{\pi_j(i)})\}$
4. Train classifier $h(y, \theta)$ to distinguish:
   - Class 1: $(y, \theta) \sim p(y | \theta)p(\theta)$
   - Class 2: $(y, \theta) \sim p(y)p(\theta)$

### 6.2 Likelihood Approximation

From the classifier:
$$L(\theta | y) \propto \frac{h(y, \theta)}{1 - h(y, \theta)}$$

For multiple observations:
$$\prod_{i=1}^{n} \frac{h(y_i, \theta)}{1 - h(y_i, \theta)}$$

### 6.3 CNN Architecture

| Layer | Output Shape | Filters | Kernel Size | Weights |
|-------|--------------|---------|-------------|---------|
| Input | (48, 48, 1) | - | - | - |
| Conv2D + ReLU | (48, 48, 128) | 128 | (3, 3) | 1,280 |
| MaxPooling2D | (24, 24, 128) | - | (2, 2) | 0 |
| Conv2D + ReLU | (22, 22, 128) | 128 | (3, 3) | 147,584 |
| ... | ... | ... | ... | ... |
| Dense (Softmax) | (2,) | - | - | 18 |

### 6.4 GNN Alternative

Graph Neural Networks for raw coordinates:
- Avoids discretization
- Preserves geometric properties
- Better generalization

**Architecture:**
1. GraphConvolutionLayer (d → 32)
2. GraphConvolutionLayer (32 → 32)
3. GraphConvolutionLayer (32 → 32)
4. GlobalMeanPooling
5. FullyConnected (32 → 2)

### 6.5 Computational Efficiency

| Model | Points | CNN (sec) | Traditional (sec) | Speedup |
|-------|--------|-----------|-------------------|---------|
| Matérn | 9,000 | 1.81 | 17.72 | 9.8x |
| LGCP | 3,000 | 1.69 | 2.21 | 1.3x |
| Strauss (GNN) | 100 | 0.0012 | 0.009 | 7.6x |
| Matérn (GNN) | 1,000 | 0.003 | 0.92 | 291x |

---

## 7. Applications to Disaster Zonation

### 7.1 Flood and Landslide Prediction

**Similarity to crime modeling:**
- Spatial clustering of events
- Temporal triggering effects (aftershocks)
- Influence of landmarks (rivers, slopes)
- Network-based spatial relationships

**Recommended approach:**
1. Collect historical flood/landslide data with spatial coordinates
2. Define landmark features (rivers, elevation changes, deforestation areas)
3. Apply STNPP model with Hawkes process kernel
4. Use GAT for influence learning between zones

### 7.2 Extreme Weather Pattern Detection

**Methodology:**
1. Discretize region into grid cells
2. Create binary event indicators (rainfall > threshold, temperature extremes)
3. Apply CNN-LSTM with SOP augmentation
4. Predict next-day risk zones

### 7.3 Zoning Framework

**Functional zones for disaster management:**
1. **High-risk zones:** Areas with historical clustering of events
2. **Medium-risk zones:** Adjacent to high-risk areas with triggered events
3. **Low-risk zones:** Areas with low event density

**Zone assignment using k-NN to landmarks:**
```python
def assign_zone(location, landmarks, k=5):
    distances = [distance(location, lm) for lm in landmarks]
    nearest_k = sorted(range(len(distances)), key=lambda i: distances[i])[:k]
    zone_labels = [landmarks[i].category for i in nearest_k]
    return majority_vote(zone_labels)
```

---

## 8. Implementation Recommendations for Điện Biên

### 8.1 Data Requirements

| Data Type | Source | Purpose |
|-----------|--------|---------|
| Historical disasters | Ban Chỉ huy Phòng chống thiên tai | Event locations, times |
| Weather data | Open-Meteo, OpenWeatherMap | Environmental covariates |
| Elevation/DEM | Remote sensing | Spatial covariates |
| River network | Topographic data | Network-based distances |
| Settlement locations | Census/Administrative | Landmark features |

### 8.2 Model Pipeline

```
┌─────────────────┐
│ Data Collection │
└────────┬────────┘
         ↓
┌─────────────────┐
│ Discretization  │  (Grid cells: elevation, proximity to rivers)
└────────┬────────┘
         ↓
┌─────────────────┐
│ Feature Maps    │  (CNN layers extract spatial patterns)
└────────┬────────┘
         ↓
┌─────────────────┐
│ Hawkes Kernel   │  (Temporal triggering effects)
└────────┬────────┘
         ↓
┌─────────────────┐
│ Network Distances│  (Streets/rivers as networks)
└────────┬────────┘
         ↓
┌─────────────────┐
│ GAT Learning    │  (Influence between zones)
└────────┬────────┘
         ↓
┌─────────────────┐
│ Risk Zoning     │  (Classify areas by risk level)
└─────────────────┘
```

### 8.3 Key Parameters

**For disaster event prediction:**
- Grid resolution: 100m × 100m (for commune-level)
- Temporal kernel: Exponential with $\beta$ estimated from historical data
- Spatial kernel: Gaussian on network distances
- Attention heads: R = 4-8 (tuned via cross-validation)

### 8.4 Early Warning Thresholds

Based on conditional intensity $\lambda(t, s)$:
- **Low alert:** $\lambda < \lambda_{0.5}$ (50th percentile)
- **Medium alert:** $\lambda_{0.5} \leq \lambda < \lambda_{0.9}$
- **High alert:** $\lambda \geq \lambda_{0.9}$ (90th percentile)

---

## 9. Key Algorithms Summary

### 9.1 Siamese Network for Pattern Classification

```python
class SiamesePointProcessCNN(nn.Module):
    def __init__(self, grid_dims=(128, 128)):
        super().__init__()
        self.cnn = nn.Sequential(
            nn.Conv2d(1, 8, kernel_size=9),
            nn.ReLU(),
            nn.MaxPool2d(3),
            nn.Conv2d(8, 16, kernel_size=5),
            nn.ReLU(),
            nn.MaxPool2d(3),
            nn.Conv2d(16, 32, kernel_size=3),
            nn.ReLU(),
            nn.MaxPool2d(2),
        )
        self.fc = nn.Linear(32 * some_size, 256)
    
    def forward_one(self, x):
        x = self.cnn(x)
        x = x.view(x.size(0), -1)
        return self.fc(x)
    
    def forward(self, x1, x2):
        f1 = self.forward_one(x1)
        f2 = self.forward_one(x2)
        return torch.abs(f1 - f2)
```

### 9.2 SOP Permutation Algorithm

```python
def second_order_preserving_permutation(data, M=100, iterations=1000):
    # Stage 1: Random permutations
    L_data = compute_L_function(data)
    mu = np.mean([compute_L(random_permutation(data)) for _ in range(M)])
    
    # Stage 2: Iterative swapping
    perm = random_permutation(data)
    for _ in range(iterations):
        proposal = swap_two_times(perm)
        L_prop = compute_L(proposal)
        error_prop = integrate((L_prop - L_data - (L_prop - mu))**2)
        error_curr = integrate((L_perm - L_data - epsilon)**2)
        if error_prop < error_curr:
            perm = proposal
    return perm
```

### 9.3 GAT for Influence Learning

```python
class GraphAttentionLayer(nn.Module):
    def __init__(self, in_features, out_features, n_heads=4):
        super().__init__()
        self.n_heads = n_heads
        self.W = nn.Linear(in_features, out_features * n_heads)
        self.a = nn.Linear(2 * out_features, 1)
    
    def forward(self, x, adj):
        h = self.W(x).view(-1, self.n_heads, out_features)
        a_input = torch.cat([h.unsqueeze(1).expand(-1, n, -1, -1),
                            h.unsqueeze(2).expand(-1, -1, n, -1)], dim=-1)
        e = self.a(a_input).squeeze(-1)
        attention = F.softmax(F.leaky_relu(e), dim=-1)
        return (attention.unsqueeze(-1) * h).mean(dim=1)
```

---

## 10. References

1. Jalilian, A. and Mateu, J. (2023). Assessing similarities between spatial point patterns with a Siamese Neural Network discriminant model. Advances in Data Analysis and Classification.

2. Dong, Z., Zhu, S., Xie, Y., Mateu, J. and Rodriguez-Cortes, F. (2023). Non-stationary spatio-temporal point process modeling for high-resolution COVID-19 data. Journal of the Royal Statistical Society C.

3. Mohler, G. and Mateu, J. (2024). Second order preserving point process permutations. Stat.

4. Dong, Z., Mateu, J. and Xie, Y. (2025). Spatio-temporal-network point processes for modeling crime incidents with landmarks. Submitted.

5. Platero, J., Walchessen, J., Kuusela, M. and Mateu, J. (2025). Neural likelihood inference for complex spatial points processes. Submitted.

---

## 11. Applicability Assessment

| Methodology | Flood Prediction | Landslide Prediction | Weather Warnings |
|-------------|-----------------|---------------------|------------------|
| Siamese CNN | ✓ (pattern comparison) | ✓ (pattern comparison) | ✓ (event clustering) |
| SOP Augmentation | ✓ (data scarcity) | ✓ (data scarcity) | ✓ (data scarcity) |
| STNPP + GAT | ✓ (rivers as landmarks) | ✓ (terrain features) | Limited |
| Non-stationary Kernel | ✓ (heterogeneous terrain) | ✓ (slope variations) | ✓ (microclimates) |
| Neural Likelihood | ✓ (intractable models) | ✓ (complex dependencies) | ✓ (rare events) |

**Overall Assessment:** The methodologies in this PDF are **highly applicable** to disaster zonation in Điện Biên province, particularly for:
1. Predicting flood events based on spatial-temporal clustering
2. Landslide risk assessment using terrain and rainfall triggers
3. Real-time warning systems using CNN-LSTM with SOP augmentation
4. Zone-based risk classification using Siamese networks
