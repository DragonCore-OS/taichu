#!/usr/bin/env python3
import numpy as np
import pickle
from pathlib import Path

np.random.seed(42)

# 生成训练数据
n_samples = 2000
X, y = [], []

for _ in range(n_samples):
    counts = np.random.randint(0, 30, size=4)
    total = counts.sum()
    if total == 0:
        counts = np.array([10, 5, 5, 0])
        total = 20
    props = counts / total
    
    support = props[0] + 0.5 * props[1]
    oppose = props[2] + props[3]
    label = 1.0 if (support > 0.6 or oppose > 0.6) else 0.0
    
    X.append(props)
    y.append(label)

X = np.array(X)
y = np.array(y)

split = int(0.8 * n_samples)
X_train, y_train = X[:split], y[:split]
X_test, y_test = X[split:], y[split:]

print(f"Train: {len(X_train)}, Test: {len(X_test)}")

# 初始化模型
W1 = np.random.randn(4, 16) * np.sqrt(2.0 / 4)
b1 = np.zeros(16)
W2 = np.random.randn(16, 1) * np.sqrt(2.0 / 16)
b2 = np.zeros(1)

def sigmoid(x):
    return 1 / (1 + np.exp(-np.clip(x, -500, 500)))

# 初始精度
z1 = X_test @ W1 + b1
a1 = np.maximum(0, z1)
z2 = a1 @ W2 + b2
initial_pred = sigmoid(z2)
initial_acc = np.mean((initial_pred > 0.5).flatten() == y_test)
print(f"Initial accuracy: {initial_acc:.4f}")

# 训练
lr = 0.1
for epoch in range(200):
    z1 = X_train @ W1 + b1
    a1 = np.maximum(0, z1)
    z2 = a1 @ W2 + b2
    output = sigmoid(z2)
    
    dz2 = output - y_train.reshape(-1, 1)
    dW2 = (a1.T @ dz2) / len(X_train)
    db2 = np.mean(dz2, axis=0)
    
    da1 = dz2 @ W2.T
    dz1 = da1 * (z1 > 0)
    dW1 = (X_train.T @ dz1) / len(X_train)
    db1 = np.mean(dz1, axis=0)
    
    W1 -= lr * dW1
    b1 -= lr * db1
    W2 -= lr * dW2
    b2 -= lr * db2
    
    if (epoch + 1) % 50 == 0:
        z1 = X_test @ W1 + b1
        a1 = np.maximum(0, z1)
        z2 = a1 @ W2 + b2
        test_pred = sigmoid(z2)
        test_acc = np.mean((test_pred > 0.5).flatten() == y_test)
        print(f"Epoch {epoch+1}: test_acc={test_acc:.4f}")

# 最终精度
z1 = X_test @ W1 + b1
a1 = np.maximum(0, z1)
z2 = a1 @ W2 + b2
final_pred = sigmoid(z2)
final_acc = np.mean((final_pred > 0.5).flatten() == y_test)
print(f"Final accuracy: {final_acc:.4f}")
print(f"Improvement: {final_acc - initial_acc:+.4f}")

# 保存
params = {'W1': W1, 'b1': b1, 'W2': W2, 'b2': b2}
with open('data/consensus_predictor_model.pkl', 'wb') as f:
    pickle.dump(params, f)

print(f"\n✓ Model saved (improvement: {final_acc - initial_acc:+.1%})")
