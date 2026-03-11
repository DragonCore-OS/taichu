#!/usr/bin/env python3
import json

# 加载基线
with open('data/shadow/retune_baseline_report.json') as f:
    baseline = json.load(f)['metrics']

# 加载实验1
with open('data/shadow/retune_deliberation_70_report.json') as f:
    exp = json.load(f)['metrics']

print('='*70)
print('🧪 实验结果对比: deliberation_70 vs baseline')
print('='*70)

fb_improvement = baseline['false_block_rate'] - exp['false_block_rate']
alignment_improvement = exp['decision_alignment_rate'] - baseline['decision_alignment_rate']
risk_change = exp['accepted_risk_count'] - baseline['accepted_risk_count']

print(f'\n📊 指标对比:')
print(f'  False-Block Rate: {baseline["false_block_rate"]:.1%} → {exp["false_block_rate"]:.1%} ({fb_improvement:+.1%})')
print(f'  Decision Alignment: {baseline["decision_alignment_rate"]:.1%} → {exp["decision_alignment_rate"]:.1%} ({alignment_improvement:+.1%})')
print(f'  Accepted-Risk: {baseline["accepted_risk_count"]} → {exp["accepted_risk_count"]} ({risk_change:+d})')

print(f'\n✅ 通过条件检查:')
fb_pass = fb_improvement >= 0.05
alignment_pass = alignment_improvement >= 0.10
risk_pass = risk_change <= 3

print(f'  FB Rate 下降 ≥ 5%: {fb_improvement:.1%} {"✅ PASS" if fb_pass else "❌ FAIL"}')
print(f'  Alignment 上升 ≥ 10%: {alignment_improvement:.1%} {"✅ PASS" if alignment_pass else "❌ FAIL"}')
print(f'  Accepted-Risk 不恶化 > 3: {risk_change:+d} {"✅ PASS" if risk_pass else "❌ FAIL"}')

passed = fb_pass and alignment_pass and risk_pass
print(f'\n🎯 实验结果: {"🟢 PASS - 进入下一轮" if passed else "🔴 FAIL - 需继续调参"}')

print('\n' + '='*70)
