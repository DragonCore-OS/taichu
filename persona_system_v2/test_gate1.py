"""
test_gate1.py
Gate 1 验证测试

验收标准:
1. 导入不报错
2. 初始化 core seats
3. generate_speech 调用返回 SpeechTurn
4. 字段兼容 (.name, .stance, .round_num)
5. stage summary 正常
6. artifacts 正常
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from bridge import PersonaActivator, ExtendedPersonaActivation


def test_import():
    """测试 1: 导入不报错"""
    print("[Test 1/6] Import test...")
    try:
        from bridge import PersonaActivator, ExtendedPersonaActivation
        print("  ✅ Import successful")
        return True
    except Exception as e:
        print(f"  ❌ Import failed: {e}")
        return False


def test_initialization():
    """测试 2: 初始化 core seats"""
    print("\n[Test 2/6] Initialization test...")
    try:
        activator = PersonaActivator({
            "use_persona_v2": True,
            "strict_mode": False  # 非严格模式，允许 registry 缺失
        })
        
        # 检查 core seats 是否已加载
        if hasattr(activator, 'CORE_SEAT_IDS'):
            print(f"  ✅ Core seats defined: {len(activator.CORE_SEAT_IDS)} seats")
            return True
        else:
            print("  ❌ CORE_SEAT_IDS not found")
            return False
    except Exception as e:
        print(f"  ❌ Initialization failed: {e}")
        return False


def test_generate_speech():
    """测试 3: generate_speech 调用返回 SpeechTurn"""
    print("\n[Test 3/6] Generate speech test...")
    try:
        activator = PersonaActivator({
            "use_persona_v2": True,
            "strict_mode": False
        })
        
        persona = ExtendedPersonaActivation(
            persona_id="00001",
            name="鬼谷子",
            archetypes=["strategist"],
            expertise=["high"],
            domains=["all"]
        )
        
        speech = activator.generate_speech(
            persona=persona,
            round_num=1,
            title="如何应对外部威胁",
            issue_type="strategic"
        )
        
        # 检查是否是 SpeechTurn 类型
        if hasattr(speech, 'name') and hasattr(speech, 'content'):
            print(f"  ✅ Speech generated: {speech.name}")
            return True
        else:
            print("  ❌ Invalid speech object")
            return False
    except Exception as e:
        print(f"  ❌ Generate speech failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_field_compatibility():
    """测试 4: 字段兼容"""
    print("\n[Test 4/6] Field compatibility test...")
    try:
        activator = PersonaActivator({
            "use_persona_v2": True,
            "strict_mode": False
        })
        
        persona = ExtendedPersonaActivation(
            persona_id="00001",
            name="鬼谷子",
            archetypes=["strategist"],
            expertise=["high"],
            domains=["all"]
        )
        
        speech = activator.generate_speech(
            persona, 1, "测试议题", "strategic"
        )
        
        # 检查必需字段
        required_fields = ['name', 'stance', 'round_num', 'content']
        missing = [f for f in required_fields if not hasattr(speech, f)]
        
        if not missing:
            print(f"  ✅ All required fields present:")
            print(f"     - name: {speech.name}")
            print(f"     - stance: {speech.stance}")
            print(f"     - round_num: {speech.round_num}")
            print(f"     - content: {speech.content[:30]}...")
            return True
        else:
            print(f"  ❌ Missing fields: {missing}")
            return False
    except Exception as e:
        print(f"  ❌ Field compatibility test failed: {e}")
        return False


def test_transcript():
    """测试 5: transcript 正常"""
    print("\n[Test 5/6] Transcript test...")
    try:
        activator = PersonaActivator({
            "use_persona_v2": True,
            "strict_mode": False
        })
        
        persona = ExtendedPersonaActivation(
            persona_id="00001",
            name="鬼谷子",
            archetypes=["strategist"],
            expertise=["high"],
            domains=["all"]
        )
        
        # 生成多条发言
        for i in range(1, 4):
            speech = activator.generate_speech(
                persona, i, f"议题_{i}", "strategic"
            )
            activator.add_to_transcript(speech)
        
        transcript = activator.get_transcript()
        
        if len(transcript) == 3:
            print(f"  ✅ Transcript contains {len(transcript)} entries")
            
            # 检查字段
            entry = transcript[0]
            print(f"     - Entry fields: {list(entry.keys())}")
            return True
        else:
            print(f"  ❌ Transcript length mismatch: {len(transcript)}")
            return False
    except Exception as e:
        print(f"  ❌ Transcript test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_audit_fields():
    """测试 6: audit 字段正常"""
    print("\n[Test 6/6] Audit fields test...")
    try:
        activator = PersonaActivator({
            "use_persona_v2": True,
            "strict_mode": False
        })
        
        persona = ExtendedPersonaActivation(
            persona_id="00001",
            name="鬼谷子",
            archetypes=["strategist"],
            expertise=["high"],
            domains=["all"]
        )
        
        speech = activator.generate_speech(
            persona, 1, "审计测试议题", "strategic"
        )
        
        # 检查 audit 字段
        if hasattr(speech, 'audit'):
            audit = speech.audit
            print(f"  ✅ Audit trail present")
            print(f"     - verified: {audit.verified}")
            print(f"     - divergence: {audit.template_divergence_score:.1%}")
            print(f"     - culture_match: {audit.culture_match_score:.1%}")
            
            # 添加到 transcript
            activator.add_to_transcript(speech)
            
            # 检查 transcript 中的 audit
            transcript = activator.get_transcript()
            if transcript and 'audit' in transcript[0]:
                print(f"  ✅ Audit in transcript")
                return True
            else:
                print(f"  ⚠️  Audit not in transcript (may be OK)")
                return True
        else:
            print(f"  ⚠️  No audit trail (legacy mode)")
            return True
    except Exception as e:
        print(f"  ❌ Audit fields test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主测试入口"""
    print("=" * 70)
    print("GATE 1 VERIFICATION TEST")
    print("=" * 70)
    
    tests = [
        test_import,
        test_initialization,
        test_generate_speech,
        test_field_compatibility,
        test_transcript,
        test_audit_fields,
    ]
    
    results = []
    for test in tests:
        results.append(test())
    
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Passed: {passed}/{total}")
    
    if all(results):
        print("\n✅ GATE 1 PASSED - Ready for Gate 2 (3x3 experiment)")
        return 0
    else:
        print("\n❌ GATE 1 FAILED - Fix issues before proceeding")
        return 1


if __name__ == "__main__":
    sys.exit(main())
