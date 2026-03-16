#!/bin/bash
# 测试GPT-OSS-120B - 原创题V2完整测试

API_URL="http://localhost:8000/v1/chat/completions"
MODEL="openai/gpt-oss-120b"
OUTPUT_DIR="gptoss120b_v2"
PROMPT_DIR="prompts"
mkdir -p $OUTPUT_DIR

echo "═══════════════════════════════════════════════════════════════"
echo "🧪 GPT-OSS-120B - 原创题V2 完整测试"
echo "═══════════════════════════════════════════════════════════════"
echo "开始时间: $(date)"
echo "模型: $MODEL"
echo "输出目录: $OUTPUT_DIR"
echo ""

# 题目列表
declare -a QUESTIONS=(
    "original_001:量子囚徒困境"
    "original_002:地月引力弹弓"
    "original_003:医疗资源分配"
    "original_004:后量子签名聚合"
    "original_005:异步BFT下界证明"
    "original_006:奖励黑客检测"
    "original_007:CRISPR脱靶预测"
    "original_008:社会契约涌现"
    "original_009:量子纠错阈值"
    "original_010:智能合约形式化验证"
)

total=${#QUESTIONS[@]}

for i in $(seq 1 $total); do
    idx=$((i-1))
    qfile=$(echo "${QUESTIONS[$idx]}" | cut -d':' -f1)
    qname=$(echo "${QUESTIONS[$idx]}" | cut -d':' -f2)
    input_file="$PROMPT_DIR/${qfile}.json"
    output_file="$OUTPUT_DIR/${qfile}.txt"
    
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "[$i/$total] 测试: $qname"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    if [ ! -f "$input_file" ]; then
        echo "❌ 错误: prompt文件不存在 $input_file"
        continue
    fi
    
    # 替换模型名并调用API
    sed "s/\"model\": \"PLACEHOLDER\"/\"model\": \"$MODEL\"/" "$input_file" > /tmp/prompt_current.json
    
    echo "⏳ 发送请求..."
    start_time=$(date +%s.%N)
    
    curl -s -X POST $API_URL \
        -H "Content-Type: application/json" \
        -d @/tmp/prompt_current.json > "$output_file" 2>&1
    
    end_time=$(date +%s.%N)
    duration=$(echo "$end_time - $start_time" | bc 2>/dev/null || echo "未知")
    
    # 检查结果
    if [ -s "$output_file" ] && grep -q '"choices"' "$output_file" 2>/dev/null; then
        # 提取token数（如果存在）
        tokens=$(grep -o '"total_tokens":[0-9]*' "$output_file" | head -1 | cut -d':' -f2 || echo "N/A")
        echo "✅ 完成 | 耗时: ${duration}s | tokens: $tokens"
        
        # 提取回答预览
        echo "📝 回答预览:"
        python3 -c "
import json
import sys
try:
    with open('$output_file', 'r') as f:
        data = json.load(f)
        content = data['choices'][0]['message']['content']
        preview = content[:300].replace('\n', ' ')
        print(f'  {preview}...')
except Exception as e:
    print(f'  [无法解析JSON: {e}]')
" 2>/dev/null || head -c 300 "$output_file"
        echo ""
    else
        echo "⚠️ 响应异常"
        head -5 "$output_file"
    fi
    
    echo ""
    sleep 1
done

echo "═══════════════════════════════════════════════════════════════"
echo "✅ 测试完成"
echo "═══════════════════════════════════════════════════════════════"
echo "结束时间: $(date)"
echo "输出文件:"
ls -lh $OUTPUT_DIR/
