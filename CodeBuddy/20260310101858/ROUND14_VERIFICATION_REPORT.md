# 第十四轮验证报告：FFI 真实加载与性能基线

**日期**: 2026-03-11  
**验证目标**: 确认 FFI 真实加载（非 fallback），产出性能基线  
**结论**: ⚠️ FFI 可用，但性能未达灰度切换门槛

---

## 1. 修复项完成情况

### 1.1 编译错误修复
| 文件 | 问题 | 修复方式 |
|------|------|----------|
| `lib.rs` | `DecisionStatus` 导入路径错误 | 改为 `council::types::DecisionStatus` |
| `lib.rs` | `RiskLevel` 未导入 | 添加 `use council::RiskLevel` |
| `lib.rs` | `as_sequence()` 不存在 | 改为 `as_array()` |
| `lib.rs` | `risk_level` 类型不匹配 | `risk_level.to_string()` → `RiskLevel::from_str(risk_level)` |
| `mod.rs` | `RiskLevel` 无 `Display` trait | 实现 `std::fmt::Display` |
| `artifacts.rs` | `MeetingStatus` 未导入 | 添加导入 |
| `activation.rs` | `RiskLevel` 类型不匹配 | 添加 `.to_string()` 转换 |
| `adapter.rs` | `RiskLevel` 类型不匹配 | 使用 `RiskLevel::from_str()` |
| `reducer.rs` | HashMap move 后借用 | 改为 `&last_stance_per_seat` 迭代 |
| `reducer.rs` | `speakers` move 后使用 | 先计算 `speaker_count` |
| `Cargo.toml` | 缺少 `dashmap` | 添加 `dashmap = "5.5"` |
| `types.rs` | `Stance` 反序列化失败 | 添加 `#[serde(rename_all = "lowercase")]` |
| `types.rs` | `SpeakerType` 反序列化失败 | 添加 `#[serde(rename_all = "lowercase")]` |
| `types.rs` | `SpeechTurn` 字段缺失 | 为可选字段添加 `#[serde(default)]` |

### 1.2 重复代码确认
- `ffi.rs` 与 `lib.rs` 存在重复实现
- 实际构建使用的是 `lib.rs`（`ffi.rs` 未被引用）
- **建议**: 后续手动删除 `ffi.rs`

---

## 2. FFI 真实加载验证 (A)

### 2.1 验证结果
```
✅ Rust core module loaded
✅ taichu_core 模块可导入: True
✅ wrapper.use_rust = True
✅ taichu_core.__version__ = 1.0.0
✅ 直接调用 taichu_core.reduce_votes: True
```

### 2.2 结论
**FFI 真实加载验证通过** - 确认使用的是 Rust 实现，非 Python fallback。

---

## 3. 语义一致性测试 (B)

### 3.1 测试结果
| 测试项 | 状态 | Python | Rust |
|--------|------|--------|------|
| reduce_votes/全支持场景 | ✅ PASS | 19 support | 19 support |
| reduce_votes/有conditional场景 | ✅ PASS | 14/5/0 | 14/5/0 |
| reduce_votes/有oppose场景 | ✅ PASS | 17/0/2 | 17/0/2 |
| stage_summary/第一轮总结 | ✅ PASS | 6 speakers | 6 speakers |
| activate_personas/鬼谷子激活 | ❌ FAIL | 1 | 0 |
| activate_personas/华佗激活 | ❌ FAIL | 1 | 0 |
| activate_personas/妈祖激活 | ❌ FAIL | 1 | 0 |
| activate_personas/低风险不触发 | ✅ PASS | 0 | 0 |

**统计**: 5/8 通过

### 3.2 问题分析
`activate_personas` 测试失败原因：
- Rust 返回 0 个激活人格，Python 返回 1 个
- 可能是激活逻辑的过滤条件不一致
- 需要检查 `ActivationEngine::activate` 实现

### 3.3 结论
核心路径（reduce_votes, stage_summary）语义一致，activate_personas 需修复。

---

## 4. 性能基线测试 (C)

### 4.1 Release 模式结果

**reduce_votes (100 次迭代)**
| 指标 | Python | Rust | 对比 |
|------|--------|------|------|
| p50 | 0.028ms | 0.048ms | 1.71x 慢 |
| p95 | 0.030ms | 0.056ms | 1.87x 慢 |
| mean | 0.029ms | 0.049ms | **0.59x** |
| CV | 11.6% | 9.3% | ✅ 更稳定 |

**pipeline 组合路径 (50 次迭代)**
| 指标 | Python | Rust | 对比 |
|------|--------|------|------|
| p50 | 0.044ms | 0.069ms | 1.57x 慢 |
| p95 | 0.049ms | 0.079ms | 1.61x 慢 |
| mean | 0.044ms | 0.070ms | **0.63x** |

### 4.2 通过标准检查
| 标准 | 要求 | 实际 | 结果 |
|------|------|------|------|
| FFI 加载 | True | True | ✅ 通过 |
| reduce_votes speedup | ≥ 1.8x | 0.59x | ❌ 未通过 |
| 稳定性 CV | < 15% | 9.3% | ✅ 通过 |
| pipeline p95 | ≤ 70% Python | 159.2% | ❌ 未通过 |

### 4.3 性能分析
**Rust 比 Python 慢的原因**:
1. **操作过于简单**: `reduce_votes` 只是简单的 dict 统计，Python 在此类操作上已高度优化
2. **FFI 调用开销**: Python → Rust → Python 的 JSON 序列化/反序列化开销占主导
3. **数据量小**: 测试只有 19 个席位，无法摊平 FFI 开销

**结论**: 对于简单操作，FFI 调用的固定开销超过了 Rust 的运行时性能优势。

---

## 5. 第十四轮执行摘要

### 5.1 已完成
- ✅ 修复所有编译错误，成功构建 `taichu_core` 模块
- ✅ 确认 FFI 真实加载（非 fallback）
- ✅ 修复 JSON 反序列化问题（字段默认值、枚举大小写）
- ✅ `reduce_votes` 和 `stage_summary` 语义一致性通过
- ✅ 产出性能基线数据

### 5.2 未完成
- ❌ `activate_personas` 语义一致性（Rust 返回 0，Python 返回 1）
- ❌ 性能达到灰度切换门槛（0.6x 未达到 1.8x）

### 5.3 风险确认
| 风险 | 状态 | 说明 |
|------|------|------|
| 假阳性通过 | ✅ 已排除 | FFI 验证日志确认 Rust 真实加载 |
| 双份实现漂移 | ⚠️ 存在 | ffi.rs 未删除，需手动清理 |
| 性能回退 | ⚠️ 确认 | Rust 比 Python 慢约 40% |

---

## 6. 第十五轮建议

### 6.1 方案 A：放弃 Rust FFI（推荐）
**理由**:
- 当前操作（投票统计、阶段总结）计算量太小
- FFI 调用开销无法摊平
- Python 实现已足够快（0.03ms 量级）

**行动**:
1. 删除 `core/` 目录下的 FFI 相关代码
2. 保留 `bridge/rust_core.py` 作为纯 Python 实现
3. 将精力投入其他高价值优化

### 6.2 方案 B：优化 Rust 实现
**可能的优化方向**:
1. **批量 API**: 改为 `reduce_votes_batch(states: Vec<State>)` 摊平 FFI 开销
2. **零拷贝**: 使用 PyO3 的 `PyDict` 直接访问，避免 JSON 序列化
3. **更复杂场景**: 只在计算密集型场景（如大规模矩阵运算）使用 Rust

### 6.3 方案 C：延迟切换
**条件**:
- 修复 `activate_personas` 语义差异
- 找到能体现 Rust 性能优势的场景
- 性能提升 ≥ 1.8x 方可灰度

---

## 7. 最终判断

**第十四轮目标达成情况**:
- ✅ 真实 FFI 验证完成
- ✅ 性能基线产出
- ⚠️ 性能未达预期（0.6x < 1.8x）
- ⚠️ 不建议进入灰度切换

**建议**:
对于当前的简单投票统计场景，**不建议切换至 Rust FFI**。Python 实现已足够高效，FFI 引入的复杂性和性能开销得不偿失。

---

**报告生成时间**: 2026-03-11  
**验证脚本**: `/data/taichu/tests/test_performance.py`  
**性能报告**: `/data/taichu/tests/performance_report.json`
