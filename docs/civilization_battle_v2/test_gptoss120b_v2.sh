#!/bin/bash
# 测试GPT-OSS-120B - 原创题V2

API_URL="http://localhost:8000/v1/chat/completions"
MODEL="openai/gpt-oss-120b"
OUTPUT_DIR="gptoss120b_v2"
mkdir -p $OUTPUT_DIR

echo "🧪 开始测试 GPT-OSS-120B - 原创题V2"
echo "开始时间: $(date)"
echo ""

# 题目列表
declare -a QUESTIONS=(
    "original_001:动态博弈：量子囚徒困境"
    "original_002:混沌控制：地月系统引力弹弓" 
    "original_003:伦理算法：医疗资源分配稀缺性"
    "original_004:密码学前沿：后量子签名聚合"
    "original_005:分布式系统：异步BFT共识的下界证明"
    "original_006:AI对齐：奖励黑客的形式化检测"
    "original_007:计算生物学：CRISPR脱靶效应预测模型"
    "original_008:文明模拟：多智能体社会契约涌现"
    "original_009:数学物理：量子纠错码的阈值计算"
    "original_010:系统安全：形式化验证智能合约"
)

# 读取题目内容
get_question_content() {
    local num=$1
    case $num in
        1)
            echo "【原创-1】动态博弈：量子囚徒困境

100个量子计算实验室参与开源协议博弈。每轮随机两两配对，选择：
- 开源(Q)：双方各+4分（技术泄露风险+10%）
- 闭源(C)：自己+6分，对方+1分
- 背叛(D)：自己+8分，对方-3分（被发现概率20%，惩罚-10分）

特殊机制：
- 每轮历史行为公开
- 第500轮技术突破，开源收益变为+6分
- 技术泄露累积达阈值后，全行业收益下降50%

要求：
1. 设计最优策略（考虑技术突破前后）
2. 计算期望收益（考虑泄露风险和惩罚）
3. 证明ESS稳健性
4. Python模拟1000轮，绘制演化曲线"
            ;;
        2)
            echo "【原创-2】混沌控制：地月系统引力弹弓

设计地球→火星的引力弹弓轨道，利用地月L1/L2点。已知：
- 地月距离：384,400 km（偏心率0.0549）
- 月球周期：27.3天
- 飞船质量：1000kg，Δv ≤ 4 km/s
- 出发窗口：2026年7月-8月

约束：
- 至少1次月球引力弹弓
- 计算月球轨道摄动影响
- 考虑地球J2项扰动
- 总转移时间 ≤ 300天

要求：
1. 建立限制性三体模型
2. 设计L2出发的低能量转移轨道
3. 计算最优发射窗口
4. Python轨道积分（RK4），绘制轨道
5. 燃料-时间权衡分析"
            ;;
        3)
            echo "【原创-3】伦理算法：医疗资源分配稀缺性

灾难响应AI分配稀缺医疗资源：

灾区A：
- 200伤员，容量50人
- 红色30人(立即手术)、黄色100人(延迟)、绿色70人(轻伤)
- 红色含5未成年人，黄色含10关键工人

灾区B（与A互斥）：
- 化工厂泄漏，100人中毒
- 解毒剂限救60人
- 30%概率48小时内自我净化

伦理约束：
- 不能纯按年龄/社会价值排序
- 考虑边际效益
- 处理不确定性

要求：
1. 多目标优化框架（生存率、公平性、边际效益）
2. 具体分配算法和数学证明
3. 不同伦理权重的权衡曲线
4. Python模拟，展示结果分布"
            ;;
        *)
            echo "题目$num"
            ;;
    esac
}

# 测试前3题
total_questions=3
for i in $(seq 1 $total_questions); do
    qid=$(echo "${QUESTIONS[$((i-1))]}" | cut -d':' -f1)
    qname=$(echo "${QUESTIONS[$((i-1))]}" | cut -d':' -f2)
    output_file="$OUTPUT_DIR/${qid}.txt"
    
    echo "[$i/$total_questions] 测试: $qname"
    
    # 准备prompt
    question_content=$(get_question_content $i)
    
    cat > /tmp/prompt_v2_${i}.json << EOFPROMPT
{
  "model": "$MODEL",
  "messages": [
    {"role": "system", "content": "You are an expert in interdisciplinary problem solving. Provide rigorous mathematical analysis, concrete algorithms, and working Python code."},
    {"role": "user", "content": "$question_content\n\n请给出详细解答，包含数学推导、算法设计和Python实现。"}
  ],
  "max_tokens": 8192,
  "temperature": 0.3
}
EOFPROMPT
    
    # 调用API
    echo "  → 发送请求..."
    start_time=$(date +%s)
    
    curl -s -X POST $API_URL \
        -H "Content-Type: application/json" \
        -d @/tmp/prompt_v2_${i}.json > $output_file 2>&1
    
    end_time=$(date +%s)
    duration=$((end_time - start_time))
    
    # 检查响应
    if [ -s "$output_file" ] && grep -q '"choices"' "$output_file" 2>/dev/null; then
        echo "  ✅ 完成 (${duration}s)"
        # 提取内容预览
        head -c 200 "$output_file"
        echo "..."
    else
        echo "  ⚠️ 响应异常，保存原始输出"
        cat "$output_file" | head -5
    fi
    echo ""
    
    sleep 2
done

echo ""
echo "📝 测试完成"
echo "结束时间: $(date)"
echo "输出目录: $OUTPUT_DIR"
ls -la $OUTPUT_DIR
