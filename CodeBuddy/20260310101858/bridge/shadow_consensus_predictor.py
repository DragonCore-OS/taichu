#!/usr/bin/env python3
"""
Round 22: Shadow ConsensusPredictor with Audit Trail

旁路集成模块 - 只观察、记录，不影响主决策
关键特性：所有记录标记来源 (live/replay/synthetic/batch_shadow)

设计原则：
1. 只读输入 - 不修改任何状态
2. 只记录输出 - 不参与最终决策
3. 来源可审计 - 明确区分真实流量和评估流量
4. 可开关 - 零成本禁用
"""

import json
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime
import pickle
import os


@dataclass
class ShadowPrediction:
    """单次预测记录（带审计来源标记）"""
    timestamp: str
    input_stance_distribution: Dict[str, int]
    input_features: List[float]
    consensus_probability: float
    confidence_bucket: str
    predicted_consensus: bool
    source: str  # live | replay | synthetic | batch_shadow
    actual_result: Optional[str] = None
    calibration_error: Optional[float] = None
    metadata: Dict = field(default_factory=dict)


class ShadowConsensusPredictor:
    """
    影子共识预测器（带完整审计链）
    
    接入 reduce_votes 管道作为旁路观察模块：
    - 接收 stance distribution
    - 输出 consensus probability
    - 记录但不影响决策
    - 明确标记数据来源
    """
    
    VALID_SOURCES = ["live", "replay", "synthetic", "batch_shadow"]
    
    def __init__(self, model_path: str = '/home/admin/CodeBuddy/20260310101858/data/consensus_predictor_model.pkl',
                 log_dir: str = '/home/admin/CodeBuddy/20260310101858/logs'):
        """
        初始化影子预测器
        
        Args:
            model_path: 训练好的模型权重路径
            log_dir: 预测日志保存目录
        """
        self.model_path = model_path
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # 加载模型参数
        self.model_params = self._load_model()
        
        # 统计信息
        self.prediction_count = 0
        self.enabled = self.model_params is not None
        
        # 按来源分离的计数器
        self.source_counts = {src: 0 for src in self.VALID_SOURCES}
        
        if self.enabled:
            print(f"🔍 ShadowConsensusPredictor enabled")
            print(f"   Model: {model_path}")
            print(f"   Log dir: {log_dir}")
        else:
            print(f"⚠️ ShadowConsensusPredictor disabled (model not found)")
            # 自动创建默认模型用于测试
            self._create_default_model()
    
    def _create_default_model(self):
        """创建默认模型（用于无模型时的测试）"""
        print("   Creating default model for testing...")
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        
        # 默认模型参数：4→16→1 MLP
        default_params = {
            'W1': np.random.randn(4, 16) * 0.01,
            'b1': np.zeros(16),
            'W2': np.random.randn(16, 1) * 0.01,
            'b2': np.zeros(1)
        }
        
        with open(self.model_path, 'wb') as f:
            pickle.dump(default_params, f)
        
        self.model_params = default_params
        self.enabled = True
        print(f"   ✓ Default model created")
    
    def _load_model(self) -> Optional[Dict]:
        """加载模型参数"""
        try:
            with open(self.model_path, 'rb') as f:
                return pickle.load(f)
        except Exception as e:
            print(f"Failed to load model: {e}")
            return None
    
    def _forward(self, X: np.ndarray) -> np.ndarray:
        """
        前向传播（内联实现，避免依赖 training 模块）
        
        Architecture: 4 → 16 → 1
        """
        if self.model_params is None:
            return np.array([[0.5]])  # 默认无信息先验
        
        W1 = self.model_params['W1']
        b1 = self.model_params['b1']
        W2 = self.model_params['W2']
        b2 = self.model_params['b2']
        
        # Layer 1: Linear + ReLU
        z1 = X @ W1 + b1
        a1 = np.maximum(0, z1)
        
        # Layer 2: Linear + Sigmoid
        z2 = a1 @ W2 + b2
        output = 1 / (1 + np.exp(-np.clip(z2, -500, 500)))
        
        return output
    
    def predict(self, stance_distribution: Dict[str, int], 
                source: str = "live") -> Dict[str, Any]:
        """
        预测共识概率
        
        Args:
            stance_distribution: {
                "support": int,
                "conditional": int,
                "oppose": int,
                "veto": int
            }
            source: 数据来源标记 (live/replay/synthetic/batch_shadow)
        
        Returns:
            {
                "consensus_probability": float,
                "confidence_bucket": str,
                "predicted_consensus": bool,
                "source": str
            }
        """
        if source not in self.VALID_SOURCES:
            raise ValueError(f"Invalid source: {source}. Must be one of {self.VALID_SOURCES}")
        
        if not self.enabled:
            return {
                "consensus_probability": 0.5,
                "confidence_bucket": "unknown",
                "predicted_consensus": False,
                "source": source
            }
        
        # 提取特征
        support = stance_distribution.get("support", 0)
        conditional = stance_distribution.get("conditional", 0)
        oppose = stance_distribution.get("oppose", 0)
        veto = stance_distribution.get("veto", 0)
        
        total = support + conditional + oppose + veto
        if total == 0:
            # 无投票情况
            return {
                "consensus_probability": 0.0,
                "confidence_bucket": "no_votes",
                "predicted_consensus": False,
                "source": source
            }
        
        # 转换为比例特征
        features = np.array([
            support / total,
            conditional / total,
            oppose / total,
            veto / total
        ]).reshape(1, -1)
        
        # 预测
        prob = float(self._forward(features)[0, 0])
        
        # 置信度分桶
        if prob > 0.9:
            bucket = "very_high"
        elif prob > 0.7:
            bucket = "high"
        elif prob > 0.3:
            bucket = "uncertain"
        elif prob > 0.1:
            bucket = "low"
        else:
            bucket = "very_low"
        
        return {
            "consensus_probability": prob,
            "confidence_bucket": bucket,
            "predicted_consensus": prob > 0.5,
            "source": source
        }
    
    def record_prediction(self, 
                         stance_distribution: Dict[str, int],
                         prediction_result: Dict[str, Any],
                         actual_result: Optional[str] = None,
                         source: str = "live",
                         metadata: Dict = None) -> ShadowPrediction:
        """
        记录一次预测（核心方法，所有来源统一走这里）
        
        Args:
            stance_distribution: 立场分布
            prediction_result: predict() 的输出
            actual_result: 实际结果（如果已知）
            source: 数据来源
            metadata: 额外元数据
        
        Returns:
            ShadowPrediction record
        """
        if not self.enabled:
            return None
        
        if source not in self.VALID_SOURCES:
            raise ValueError(f"Invalid source: {source}")
        
        total = sum(stance_distribution.values())
        features = [
            stance_distribution["support"] / total if total > 0 else 0,
            stance_distribution["conditional"] / total if total > 0 else 0,
            stance_distribution["oppose"] / total if total > 0 else 0,
            stance_distribution["veto"] / total if total > 0 else 0
        ]
        
        record = ShadowPrediction(
            timestamp=datetime.now().isoformat(),
            input_stance_distribution=stance_distribution,
            input_features=features,
            consensus_probability=prediction_result["consensus_probability"],
            confidence_bucket=prediction_result["confidence_bucket"],
            predicted_consensus=prediction_result["predicted_consensus"],
            source=source,
            actual_result=actual_result,
            metadata=metadata or {}
        )
        
        # 保存记录（按来源分离存储）
        self._save_record(record, source)
        self.prediction_count += 1
        self.source_counts[source] += 1
        
        return record
    
    def observe_reduce_votes(self, state: Dict[str, Any], 
                            decision_result: Dict[str, Any],
                            source: str = "live") -> Optional[ShadowPrediction]:
        """
        观察 reduce_votes 调用并记录
        
        Args:
            state: reduce_votes 输入状态
            decision_result: reduce_votes 输出结果
            source: 数据来源（live 为真实流量，replay 为历史回放）
        
        Returns:
            ShadowPrediction record (or None if disabled)
        """
        if not self.enabled:
            return None
        
        # 提取 stance distribution
        speeches = state.get("speeches", [])
        valid_seats = state.get("valid_seat_ids", [])
        
        # 统计最终立场
        last_stance_per_seat = {}
        for speech in speeches:
            seat_id = speech.get("seat_id")
            if seat_id and seat_id in valid_seats:
                stance = speech.get("stance", "support").lower()
                last_stance_per_seat[seat_id] = stance
        
        stance_distribution = {
            "support": 0,
            "conditional": 0,
            "oppose": 0,
            "veto": 0
        }
        for stance in last_stance_per_seat.values():
            if stance in stance_distribution:
                stance_distribution[stance] += 1
        
        # 预测
        prediction_result = self.predict(stance_distribution, source=source)
        
        # 提取实际结果
        actual_status = decision_result.get("status", "unknown")
        
        # 使用统一记录方法
        metadata = {
            "valid_seats_count": len(valid_seats),
            "speeches_count": len(speeches)
        }
        
        return self.record_prediction(
            stance_distribution=stance_distribution,
            prediction_result=prediction_result,
            actual_result=actual_status,
            source=source,
            metadata=metadata
        )
    
    def _save_record(self, record: ShadowPrediction, source: str):
        """保存预测记录到日志（按来源分离）"""
        date_str = datetime.now().strftime("%Y%m%d")
        
        # 主日志：所有来源
        main_log = self.log_dir / f"shadow_predictions_{date_str}.jsonl"
        with open(main_log, 'a') as f:
            f.write(json.dumps(asdict(record)) + '\n')
        
        # 按来源分离的日志
        source_log = self.log_dir / f"shadow_predictions_{source}_{date_str}.jsonl"
        with open(source_log, 'a') as f:
            f.write(json.dumps(asdict(record)) + '\n')
    
    def get_observation_stats(self, source_filter: Optional[str] = None) -> Dict[str, Any]:
        """
        获取观察统计信息
        
        Args:
            source_filter: 如果指定，只统计该来源的数据 (live/replay/synthetic/batch_shadow)
        
        Returns:
            统计信息字典
        """
        if not self.enabled:
            return {"enabled": False}
        
        # 读取日志文件
        all_predictions = []
        
        if source_filter:
            # 只读取指定来源的日志
            log_files = list(self.log_dir.glob(f"shadow_predictions_{source_filter}_*.jsonl"))
        else:
            # 读取所有主日志（包含所有来源）
            log_files = list(self.log_dir.glob("shadow_predictions_20*.jsonl"))
            # 排除来源分离的日志（避免重复计数）
            log_files = [f for f in log_files if not any(
                f"_{src}_" in f.name for src in self.VALID_SOURCES
            )]
        
        for log_file in log_files:
            with open(log_file, 'r') as f:
                for line in f:
                    try:
                        all_predictions.append(json.loads(line))
                    except:
                        pass
        
        if not all_predictions:
            return {
                "enabled": True, 
                "predictions_count": 0,
                "source_filter": source_filter
            }
        
        # 统计
        probs = [p["consensus_probability"] for p in all_predictions]
        buckets = {}
        sources = {}
        
        for p in all_predictions:
            b = p["confidence_bucket"]
            buckets[b] = buckets.get(b, 0) + 1
            
            s = p.get("source", "unknown")
            sources[s] = sources.get(s, 0) + 1
        
        return {
            "enabled": True,
            "predictions_count": len(all_predictions),
            "probability_mean": float(np.mean(probs)),
            "probability_std": float(np.std(probs)),
            "confidence_buckets": buckets,
            "source_distribution": sources,
            "source_filter": source_filter
        }
    
    def get_real_data_count(self) -> int:
        """获取真实数据样本数（live + replay，不含 synthetic/batch_shadow）"""
        stats = self.get_observation_stats()
        sources = stats.get("source_distribution", {})
        return sources.get("live", 0) + sources.get("replay", 0)
    
    def check_threshold(self, threshold: int = 200) -> Dict[str, Any]:
        """
        检查是否达到决策阈值
        
        Returns:
            {
                "threshold_reached": bool,
                "real_samples": int,
                "threshold": int,
                "can_decide": bool
            }
        """
        real_count = self.get_real_data_count()
        total_count = self.get_observation_stats()["predictions_count"]
        
        return {
            "threshold_reached": real_count >= threshold,
            "real_samples": real_count,
            "total_samples": total_count,
            "threshold": threshold,
            "can_decide": real_count >= threshold
        }


# Singleton instance for easy import
_shadow_predictor = None

def get_shadow_predictor() -> ShadowConsensusPredictor:
    """获取影子预测器单例"""
    global _shadow_predictor
    if _shadow_predictor is None:
        _shadow_predictor = ShadowConsensusPredictor()
    return _shadow_predictor


def reset_shadow_predictor():
    """重置影子预测器（用于测试）"""
    global _shadow_predictor
    _shadow_predictor = None


if __name__ == "__main__":
    print("Shadow ConsensusPredictor with Audit Trail")
    print("=" * 50)
    
    # Test
    predictor = ShadowConsensusPredictor()
    
    if predictor.enabled:
        # 测试不同来源的预测
        test_distribution = {
            "support": 10,
            "conditional": 2,
            "oppose": 1,
            "veto": 0
        }
        
        for source in ["live", "replay", "synthetic", "batch_shadow"]:
            result = predictor.predict(test_distribution, source=source)
            print(f"\nSource: {source}")
            print(f"  Probability: {result['consensus_probability']:.4f}")
            print(f"  Bucket: {result['confidence_bucket']}")
        
        # 显示统计
        stats = predictor.get_observation_stats()
        print(f"\n统计信息:")
        print(f"  总预测数: {stats['predictions_count']}")
        print(f"  来源分布: {stats.get('source_distribution', {})}")
    else:
        print("Predictor not enabled")
