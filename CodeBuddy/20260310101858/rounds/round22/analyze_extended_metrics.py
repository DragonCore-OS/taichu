#!/usr/bin/env python3
"""
Round 22: Extended Metrics Analysis

分析 shadow predictor 的扩展指标：
- Total ECE (Expected Calibration Error)
- Rolling ECE (50-sample window)
- High-confidence error rate
- Per-class metrics

输出：分析报告和是否符合门槛的判断
"""

import json
import sys
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Tuple
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent / "bridge"))
from shadow_consensus_predictor import ShadowConsensusPredictor, get_shadow_predictor


def compute_ece(predictions: List[Dict], n_bins: int = 5) -> float:
    """计算 Expected Calibration Error"""
    if not predictions:
        return 0.0
    
    # 提取概率和标签
    probs = []
    labels = []
    
    for p in predictions:
        prob = p.get("consensus_probability", 0.5)
        # 从 actual_result 推导标签
        actual = p.get("actual_result", "unknown")
        if actual in ["approved", "passed"]:
            label = 1
        elif actual in ["rejected", "blocked", "failed"]:
            label = 0
        else:
            continue  # 跳过未知标签
        
        probs.append(prob)
        labels.append(label)
    
    if not probs:
        return 0.0
    
    probs = np.array(probs)
    labels = np.array(labels)
    
    # 创建 bin
    bin_edges = np.linspace(0, 1, n_bins + 1)
    bin_indices = np.digitize(probs, bin_edges[:-1]) - 1
    bin_indices = np.clip(bin_indices, 0, n_bins - 1)
    
    ece = 0.0
    total_samples = len(probs)
    
    for i in range(n_bins):
        mask = bin_indices == i
        if np.sum(mask) > 0:
            bin_confidence = np.mean(probs[mask])
            bin_accuracy = np.mean(labels[mask])
            bin_weight = np.sum(mask) / total_samples
            ece += bin_weight * abs(bin_confidence - bin_accuracy)
    
    return float(ece)


def compute_rolling_ece(predictions: List[Dict], window_size: int = 50) -> List[float]:
    """计算 Rolling ECE"""
    rolling_ece = []
    
    for i in range(len(predictions)):
        if i < window_size:
            continue
        
        window = predictions[i-window_size:i]
        ece = compute_ece(window)
        rolling_ece.append(ece)
    
    return rolling_ece


def compute_high_confidence_error_rate(predictions: List[Dict], 
                                       threshold: float = 0.9) -> float:
    """计算高置信度错误率"""
    high_conf_wrong = 0
    high_conf_total = 0
    
    for p in predictions:
        prob = p.get("consensus_probability", 0.5)
        
        if prob >= threshold:
            high_conf_total += 1
            actual = p.get("actual_result", "unknown")
            predicted = p.get("predicted_consensus", False)
            
            # 转换为布尔
            actual_bool = actual in ["approved", "passed"]
            
            if predicted != actual_bool:
                high_conf_wrong += 1
    
    if high_conf_total == 0:
        return 0.0
    
    return high_conf_wrong / high_conf_total


def compute_bucket_calibration(predictions: List[Dict]) -> Dict[str, Dict[str, float]]:
    """计算每个 bucket 的校准情况"""
    buckets = defaultdict(lambda: {"predicted_probs": [], "actual_labels": []})
    
    for p in predictions:
        bucket = p.get("confidence_bucket", "unknown")
        prob = p.get("consensus_probability", 0.5)
        actual = p.get("actual_result", "unknown")
        
        if actual in ["approved", "passed"]:
            label = 1
        elif actual in ["rejected", "blocked", "failed"]:
            label = 0
        else:
            continue
        
        buckets[bucket]["predicted_probs"].append(prob)
        buckets[bucket]["actual_labels"].append(label)
    
    # 计算每个 bucket 的校准
    result = {}
    for bucket_name, data in buckets.items():
        if data["predicted_probs"]:
            avg_predicted = np.mean(data["predicted_probs"])
            avg_actual = np.mean(data["actual_labels"])
            gap = avg_predicted - avg_actual
            
            result[bucket_name] = {
                "count": len(data["predicted_probs"]),
                "avg_predicted_prob": float(avg_predicted),
                "avg_actual_rate": float(avg_actual),
                "gap": float(gap),  # 正值=过度自信，负值=信心不足
                "accuracy": float(avg_actual)
            }
    
    return result


def check_thresholds(metrics: Dict[str, Any]) -> Dict[str, Any]:
    """
    检查是否满足 FINAL_DECISION_TABLE 门槛
    
    门槛标准（锁定）：
    - Total ECE < 0.22 (B档)
    - Rolling ECE(50) < 0.18 (B档)
    - very_high gap < +0.12 (B档)
    - High-conf error < 18% (B档)
    """
    checks = {
        "total_ece": {
            "value": metrics.get("total_ece", 1.0),
            "threshold_a": 0.18,
            "threshold_b": 0.22,
            "threshold_c": 0.25
        },
        "rolling_ece_50": {
            "value": metrics.get("rolling_ece_50_latest", 1.0),
            "threshold_a": 0.12,
            "threshold_b": 0.18,
            "threshold_c": 0.20
        },
        "very_high_gap": {
            "value": abs(metrics.get("bucket_calibration", {}).get("very_high", {}).get("gap", 1.0)),
            "threshold_a": 0.08,
            "threshold_b": 0.12,
            "threshold_c": 0.15
        },
        "high_conf_error": {
            "value": metrics.get("high_confidence_error_rate", 1.0),
            "threshold_a": 0.12,
            "threshold_b": 0.18,
            "threshold_c": 0.20
        }
    }
    
    # 判定每个指标的档次
    for name, check in checks.items():
        val = check["value"]
        if val < check["threshold_a"]:
            check["grade"] = "A"
        elif val < check["threshold_b"]:
            check["grade"] = "B"
        elif val < check["threshold_c"]:
            check["grade"] = "C"
        else:
            check["grade"] = "F"
    
    # 综合判定
    grades = [c["grade"] for c in checks.values()]
    
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
    
    return {
        "checks": checks,
        "overall_grade": overall,
        "decision": decision,
        "raw_grades": grades
    }


def analyze(predictor: ShadowConsensusPredictor = None, 
           source_filter: str = None) -> Dict[str, Any]:
    """
    执行完整分析
    
    Args:
        predictor: ShadowConsensusPredictor 实例
        source_filter: 如果指定，只分析该来源的数据
    
    Returns:
        完整分析结果
    """
    if predictor is None:
        predictor = get_shadow_predictor()
    
    # 获取所有预测
    stats = predictor.get_observation_stats(source_filter=source_filter)
    
    # 读取详细预测数据
    log_dir = predictor.log_dir
    predictions = []
    
    if source_filter:
        log_files = list(log_dir.glob(f"shadow_predictions_{source_filter}_*.jsonl"))
    else:
        log_files = list(log_dir.glob("shadow_predictions_20*.jsonl"))
        log_files = [f for f in log_files if not any(
            f"_{src}_" in f.name for src in predictor.VALID_SOURCES
        )]
    
    for log_file in log_files:
        with open(log_file, 'r') as f:
            for line in f:
                try:
                    predictions.append(json.loads(line))
                except:
                    pass
    
    if not predictions:
        return {"error": "No predictions found"}
    
    # 计算指标
    print(f"\nAnalyzing {len(predictions)} predictions...")
    
    total_ece = compute_ece(predictions)
    print(f"  Total ECE: {total_ece:.4f}")
    
    rolling_ece = compute_rolling_ece(predictions, window_size=50)
    rolling_ece_latest = rolling_ece[-1] if rolling_ece else 0.0
    rolling_ece_mean = np.mean(rolling_ece) if rolling_ece else 0.0
    print(f"  Rolling ECE(50): latest={rolling_ece_latest:.4f}, mean={rolling_ece_mean:.4f}")
    
    high_conf_error = compute_high_confidence_error_rate(predictions)
    print(f"  High-confidence Error Rate: {high_conf_error:.2%}")
    
    bucket_cal = compute_bucket_calibration(predictions)
    print(f"  Bucket Calibration:")
    for bucket, data in bucket_cal.items():
        print(f"    {bucket}: n={data['count']}, gap={data['gap']:+.3f}")
    
    # 组装指标
    metrics = {
        "total_predictions": len(predictions),
        "total_ece": total_ece,
        "rolling_ece_50_latest": rolling_ece_latest,
        "rolling_ece_50_mean": rolling_ece_mean,
        "high_confidence_error_rate": high_conf_error,
        "bucket_calibration": bucket_cal,
        "source_filter": source_filter
    }
    
    # 检查门槛
    threshold_check = check_thresholds(metrics)
    
    return {
        "metrics": metrics,
        "threshold_check": threshold_check
    }


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Round 22 Extended Metrics Analysis")
    parser.add_argument("--source", "-s", type=str,
                       choices=["live", "replay", "synthetic", "batch_shadow"],
                       help="Filter by source (default: all real sources)")
    parser.add_argument("--output", "-o", type=str,
                       help="Output report file path")
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("Round 22: Extended Metrics Analysis")
    print("=" * 60)
    
    # 如果没有指定 source，默认分析真实数据 (live + replay)
    source_filter = args.source
    if source_filter is None:
        print("\nAnalyzing REAL data sources (live + replay)...")
    else:
        print(f"\nAnalyzing source: {source_filter}")
    
    # 执行分析
    predictor = get_shadow_predictor()
    
    # 先检查样本数
    status = predictor.check_threshold(200)
    print(f"\nReal samples: {status['real_samples']} / 200")
    
    if status['real_samples'] < 50:
        print("\n⚠️ WARNING: Insufficient samples for reliable analysis (< 50)")
        print("   Recommend: Run accelerate_round22.py to collect more samples")
        return 1
    
    result = analyze(predictor, source_filter=source_filter)
    
    if "error" in result:
        print(f"\nERROR: {result['error']}")
        return 1
    
    # 输出判定结果
    print("\n" + "=" * 60)
    print("THRESHOLD CHECK (FINAL_DECISION_TABLE)")
    print("=" * 60)
    
    checks = result["threshold_check"]["checks"]
    for name, check in checks.items():
        print(f"\n{name}:")
        print(f"  Value: {check['value']:.4f}")
        print(f"  Grade: {check['grade']}")
        print(f"  Thresholds: A<{check['threshold_a']}, B<{check['threshold_b']}, C<{check['threshold_c']}")
    
    print(f"\n{'='*60}")
    print("FINAL DECISION")
    print(f"{'='*60}")
    print(f"Overall Grade: {result['threshold_check']['overall_grade']}")
    print(f"Decision: {result['threshold_check']['decision']}")
    
    # 保存报告
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2)
        
        print(f"\n✓ Report saved to: {output_path}")
    
    # 返回码
    grade = result['threshold_check']['overall_grade']
    return 0 if grade in ["A", "B"] else 1


if __name__ == "__main__":
    sys.exit(main())
