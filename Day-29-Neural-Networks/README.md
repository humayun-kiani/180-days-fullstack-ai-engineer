# Day 29 — Neural Networks & Deep Learning with PyTorch

> **Phase 3 — AI & Machine Learning** | Week 5 | Day 29 of 180

---

## 📌 What I Learned Today

- What an artificial neuron is: weighted sum + activation function
- Why activation functions are essential: linear stacking = one layer
- ReLU: max(0, x) — most common for hidden layers, fast to compute
- Sigmoid: (0,1) range — good for binary output
- Softmax: converts logits to probability distribution summing to 1
- Why softmax for multi-class output (not sigmoid)
- PyTorch tensors: like NumPy arrays + GPU support + autograd
- requires_grad=True: tells PyTorch to track gradients on this tensor
- loss.backward(): computes all gradients via automatic differentiation
- optimizer.zero_grad(): must clear gradients before each backward pass
- optimizer.step(): applies computed gradients to update weights
- nn.Module: base class for all PyTorch models
- nn.Sequential: stack layers in order
- nn.Linear(in, out): fully connected layer with weights + bias
- nn.BatchNorm1d: normalize activations → stable training
- nn.Dropout(p): randomly zero neurons → prevents overfitting
- model.train() vs model.eval(): controls dropout + batchnorm behavior
- with torch.no_grad(): skip gradient computation during inference
- DataLoader: batches + shuffling + parallel loading
- TensorDataset: wrap numpy arrays into a dataset
- StandardScaler: CRITICAL for neural networks (sensitive to scale)
- Xavier initialization: better weight init for deep networks
- AdamW optimizer: Adam + proper weight decay
- ReduceLROnPlateau: halve learning rate when val loss plateaus
- gradient clipping: clip*grad_norm* prevents exploding gradients
- Early stopping: stop when val loss stops improving
- EarlyStopping class: save best weights, restore on stop
- torch.save(state_dict()) + torch.load() for persistence
- NN vs Random Forest on tabular data: RF often wins
- NNs truly shine on: images, text, audio, large datasets

## 🔨 Project Built

**Deep Learning Task Priority Predictor:**

- 2,000 synthetic tasks across 4 priority levels
- 35 engineered features (same as Day 27)
- TaskPriorityNet: 3 hidden layers [128, 64, 32]
  - BatchNorm + Dropout(0.3) per layer
  - Xavier weight initialization
  - 15,108 total trainable parameters
- TaskPriorityResNet: residual connections variant
- Complete training loop: AdamW + ReduceLROnPlateau + early stopping
- Gradient clipping for training stability
- ASCII training curve visualization
- Comparison: Neural Net vs Random Forest on same test set
  (Result: similar — RF competitive on small tabular data)
- Model saved: state_dict .pth + scaler .joblib + meta .json
- FastAPI endpoint: POST /predict, POST /predict/batch, GET /model/info

## 🚀 How to Run

```bash
cd Day-29-Neural-Networks
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

python src/main.py    # train + compare + demo

uvicorn src.api:app --reload
# Open: http://localhost:8000/docs
```

## 🧠 Key PyTorch Patterns

| Pattern      | Code                                       |
| ------------ | ------------------------------------------ |
| Create model | `model = MyNet().to(device)`               |
| Forward pass | `logits = model(X_batch)`                  |
| Compute loss | `loss = loss_fn(logits, y_batch)`          |
| Zero grads   | `optimizer.zero_grad()`                    |
| Backprop     | `loss.backward()`                          |
| Clip grads   | `clip_grad_norm_(model.parameters(), 1.0)` |
| Update       | `optimizer.step()`                         |
| Inference    | `model.eval(); torch.no_grad()`            |
| Save         | `torch.save(model.state_dict(), path)`     |
| Load         | `model.load_state_dict(torch.load(path))`  |

## 🔗 Back to Main Roadmap

[← Back to 180-Day Roadmap](../README.md)
