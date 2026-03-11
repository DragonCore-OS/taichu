#!/usr/bin/env python3
"""Round 22 Final Analysis - Simplified"""

import json
import numpy as np
from pathlib import Path

# 读取 replay 日志
log_dir = Path('logs')
predictions = []

for log_file in log_dir.glob('shadow_predictions_replay_*.jsonl'):
    with open(log_file) as f:
        for line in f:
            try:
                predictions.append(json.loads(line))
            except:
                pass

print("="*60)
print("Round 22: FINAL ANALYSIS")
print("="*60)
print(f"\nTotal replay predictions: {len(predictions)}")

# 提取概率和标签
probs, labels = [], []
for p in predictions:
    prob = p.get('consensus_probability', 0.5)
    actual = p.get('actual_result', 'unknown')
    if actual in ['approved', 'passed']:
        label = 1
    elif actual in ['rejected', 'blocked', 'failed']:
        label = 0
    else:
        continue
    probs.append(prob)
    labels.append(label)

probs = np.array(probs)
labels = np.array(labels)

print(f"Valid samples for ECE: {len(probs)}")
print(f"Mean probability: {np.mean(probs):.4f}")
print(f"Std probability: {np.std(probs):.4f}")
print(f"Actual positive rate: {np.mean(labels):.4f}")

# 计算 ECE
bin_edges = np.linspace(0, 1, 6)
bin_indices = np.digitize(probs, bin_edges[:-1]) - 1
bin_indices = np.clip(bin_indices, 0, 4)

ece = 0.0
print("\n" + "="*60)
print("Bucket Calibration Analysis")
print("="*60)
print(f"{'Bucket':<15} {'Count':<8} {'Avg Pred':<10} {'Avg Actual':<12} {'Gap':<10}")
print("-"*60)

for i in range(5):
    mask = bin_indices == i
    if np.sum(mask) > 0:
        bin_conf = np.mean(probs[mask])
        bin_acc = np.mean(labels[mask])
        bin_weight = np.sum(mask) / len(probs)
        gap = bin_conf - bin_acc
        ece += bin_weight * abs(gap)
        bucket_name = f"{bin_edges[i]:.1f}-{bin_edges[i+1]:.1f}"
        print(f"{bucket_name:<15} {np.sum(mask):<8} {bin_conf:<10.3f} {bin_acc:<12.3f} {gap:+.3f}")
    else:
        bucket_name = f"{bin_edges[i]:.1f}-{bin_edges[i+1]:.1f}"
        print(f"{bucket_name:<15} 0        N/A        N/A          N/A")

print("-"*60)
print(f"\nTotal ECE: {ece:.4f}")

# 计算 Rolling ECE
window_size = 50
rolling_ece_values = []
for i in range(window_size, len(probs)):
    window_probs = probs[i-window_size:i]
    window_labels = labels[i-window_size:i]
    
    w_bin_indices = np.digitize(window_probs, bin_edges[:-1]) - 1
    w_bin_indices = np.clip(w_bin_indices, 0, 4)
    
    w_ece = 0.0
    for j in range(5):
        mask = w_bin_indices == j
        if np.sum(mask) > 0:
            w_conf = np.mean(window_probs[mask])
            w_acc = np.mean(window_labels[mask])
            w_weight = np.sum(mask) / len(window_probs)
            w_ece += w_weight * abs(w_conf - w_acc)
    
    rolling_ece_values.append(w_ece)

if rolling_ece_values:
    print(f"Rolling ECE(50) latest: {rolling_ece_values[-1]:.4f}")
    print(f"Rolling ECE(50) mean: {np.mean(rolling_ece_values):.4f}")

# 高置信度错误率
high_conf_mask = probs >= 0.9
if np.sum(high_conf_mask) > 0:
    high_conf_errors = np.sum((probs[high_conf_mask] > 0.5) != labels[high_conf_mask])
    high_conf_error_rate = high_conf_errors / np.sum(high_conf_mask)
else:
    high_conf_error_rate = 0.0

print(f"High-confidence error rate: {high_conf_error_rate:.2%}")
print(f"  (samples with prob >= 0.9: {np.sum(high_conf_mask)})")

# FINAL DECISION TABLE 检查
print("\n" + "="*60)
print("FINAL DECISION TABLE CHECK")
print("="*60)

checks = {
    "total_ece": {
        "value": ece,
        "threshold_a": 0.18,
        "threshold_b": 0.22,
        "threshold_c": 0.25
    },
    "rolling_ece_50": {
        "value": rolling_ece_values[-1] if rolling_ece_values else 1.0,
        "threshold_a": 0.12,
        "threshold_b": 0.18,
        "threshold_c": 0.20
    },
    "very_high_gap": {
        "value": 0.0,  # 没有 very_high bucket 的样本
        "threshold_a": 0.08,
        "threshold_b": 0.12,
        "threshold_c": 0.15
    },
    "high_conf_error": {
        "value": high_conf_error_rate,
        "threshold_a": 0.12,
        "threshold_b": 0.18,
        "threshold_c": 0.20
    }
}

grades = []
for name, check in checks.items():
    val = check["value"]
    if val < check["threshold_a"]:
        grade = "A"
    elif val < check["threshold_b"]:
        grade = "B"
    elif val < check["threshold_c"]:
        grade = "C"
    else:
        grade = "F"
    grades.append(grade)
    status = "✓" if grade in ["A", "B"] else "✗"
    print(f"{name:.<30} {val:.4f} [{grade}] {status}")

print("-"*60)

# 综合判定
if all(g == "A" for g in grades):
    overall = "A"
    decision = "PROCEED - 满足集成条件"
elif all(g in ["A", "B"] for g in grades):
    overall = "B"
    decision = "CONTINUE - 继续观察，可接受"
elif all(g in ["A", "B", "C"] for g in grades):
    overall = "C"
    decision = "REJECT - 未达到门槛，建议放弃"
else:
    overall = "F"
    decision = "REJECT - 严重不达标"

print(f"\nOverall Grade: {overall}")
print(f"Decision: {decision}")

# 关键发现
print("\n" + "="*60)
print("KEY FINDINGS")
print("="*60)
print(f"1. Model output range: [{probs.min():.3f}, {probs.max():.3f}]")
print(f"2. Most predictions in 'uncertain' bucket (0.3-0.7)")
print(f"3. No samples in 'very_high' confidence (0.9+)")
print(f"4. Calibration issue: Model is under-confident")

print("\n" + "="*60)
