"""
G1机器人 - 文本分类系统完整演示
展示系统的各种使用方式
"""

import sys
import time
from pathlib import Path

# 确保可以导入模块
sys.path.insert(0, str(Path(__file__).parent))

from text_classifier import ActionType, TextClassifier
from action_executor import G1ActionExecutor
from main_system import G1SmartActionSystem


def print_header(title: str):
    """打印标题"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def demo_text_classification():
    """演示1：文本分类"""
    print_header("演示1：文本分类功能")
    
    classifier = TextClassifier()
    
    test_cases = [
        "挥挥手打个招呼",
        "给我一个拥抱",
        "我们来击掌",
        "做个鼓掌的动作",
        "举起你的手",
        "比个心",
        "握手",
        
        # 边界情况
        "站",
        "随机文本",
        "xyz",
    ]
    
    print("\n测试文本分类:")
    for text in test_cases:
        action, score = classifier.classify_text(text)
        if action:
            print(f"  ✓ '{text}' → {action.value} ({score:.1%})")
        else:
            print(f"  ✗ '{text}' → 无法识别 ({score:.1%})")
            # 显示建议
            suggestions = classifier.suggest_action(text, top_k=2)
            if suggestions:
                print(f"     💡 建议: {suggestions[0][0].value} ({suggestions[0][1]:.1%})")


def demo_action_execution():
    """演示2：动作执行（模拟模式）"""
    print_header("演示2：动作执行 (模拟模式)")
    
    executor = G1ActionExecutor(use_real_robot=False, verbose=True)
    
    actions = [
        ActionType.HIGH_WAVE,
        ActionType.HUG,
        ActionType.CLAP,
        ActionType.HIGH_FIVE,
        ActionType.HANDS_UP,
        ActionType.SHAKE_HAND,
    ]
    
    print("\n顺序执行动作:")
    for i, action in enumerate(actions, 1):
        print(f"\n[{i}/{len(actions)}]")
        executor.execute_action(action, duration=1.0)
        time.sleep(0.3)
    
    executor.cleanup()


def demo_text_to_action():
    """演示3：文本到动作的完整流程"""
    print_header("演示3：文本到动作的完整流程")
    
    executor = G1ActionExecutor(use_real_robot=False, verbose=True)
    
    commands = [
        "给我挥挥手",
        "做个拥抱的动作",
        "鼓掌",
        "击掌",
        "握手",
    ]
    
    print("\n处理文本命令序列:")
    for i, cmd in enumerate(commands, 1):
        print(f"\n[{i}/{len(commands)}]", end="")
        executor.process_text_command(cmd)
        time.sleep(0.5)
    
    executor.cleanup()


def demo_batch_processing():
    """演示4：批量处理"""
    print_header("演示4：批量处理命令")
    
    system = G1SmartActionSystem(use_real_robot=False)
    
    commands = [
        "挥手打招呼",
        "拥抱",
        "鼓掌",
        "击掌",
        "举手",
    ]
    
    print(f"\n批量处理 {len(commands)} 条命令:")
    system.process_batch_commands(commands, delay=0.3)
    system.print_stats()
    system.cleanup()


def demo_action_suggestions():
    """演示5：动作建议功能"""
    print_header("演示5：动作建议功能")
    
    classifier = TextClassifier()
    
    ambiguous_inputs = [
        "走",
        "手",
        "转",
        "动作",
        "我需要帮助",
    ]
    
    print("\n为模糊输入提供建议:")
    for text in ambiguous_inputs:
        print(f"\n输入: '{text}'")
        action, score = classifier.classify_text(text)
        
        if action:
            print(f"  最可能的动作: {action.value} ({score:.1%})")
        else:
            print(f"  无法确定动作 (最高匹配: {score:.1%})")
        
        suggestions = classifier.suggest_action(text, top_k=3)
        print("  💡 其他可能的动作:")
        for suggested_action, suggested_score in suggestions:
            print(f"     - {suggested_action.value} ({suggested_score:.1%})")


def demo_action_info():
    """演示6：查看所有可用动作"""
    print_header("演示6：所有可用动作信息")
    
    system = G1SmartActionSystem(use_real_robot=False)
    actions = system.get_action_list()
    
    # 按类型分组
    arm_actions = [a for a in actions if a['type'] == 'arm']

    print(f"\n🤖 Arm (手臂) 动作 - {len(arm_actions)}种:")
    for action in arm_actions:
        keywords = ", ".join(action['keywords'])
        print(f"  • {action['action_id']}")
        print(f"    关键词: {keywords}")
    
    print(f"\n📊 总计: {len(actions)} 种动作")


def demo_classifier_api():
    """演示7：分类器API的详细使用"""
    print_header("演示7：分类器API详细使用")
    
    classifier = TextClassifier()
    
    # 示例1：基本分类
    print("\n1️⃣  基本分类:")
    text = "我想和你握手"
    action, score = classifier.classify_text(text)
    print(f"  输入: '{text}'")
    print(f"  结果: {action.value if action else '无法识别'}")
    print(f"  置信度: {score:.2%}")
    
    # 示例2：获取动作信息
    print("\n2️⃣  获取动作详细信息:")
    if action:
        info = classifier.get_action_info(action)
        print(f"  动作ID: {info['action']}")
        print(f"  类型: {info['type']}")
        print(f"  关键词: {', '.join(info['keywords'][:5])}")
        if info['params']:
            print(f"  参数: {info['params']}")
    
    # 示例3：动作建议
    print("\n3️⃣  动作建议:")
    ambiguous_text = "动"
    suggestions = classifier.suggest_action(ambiguous_text, top_k=3)
    print(f"  输入: '{ambiguous_text}'")
    print(f"  建议动作:")
    for suggested_action, suggested_score in suggestions:
        print(f"    - {suggested_action.value} ({suggested_score:.1%})")
    
    # 示例4：阈值控制
    print("\n4️⃣  阈值控制:")
    test_text = "有点像挥手"
    for threshold in [0.3, 0.5, 0.7]:
        action, score = classifier.classify_text(test_text, threshold=threshold)
        result = f"{action.value} ({score:.1%})" if action else "无法识别"
        print(f"  阈值{threshold:.1f}: {result}")


def demo_custom_scenario():
    """演示8：自定义场景示例"""
    print_header("演示8：自定义场景 - 机器人欢迎动作序列")
    
    executor = G1ActionExecutor(use_real_robot=False, verbose=True)
    
    print("\n场景：机器人欢迎访客")
    print("-" * 70)
    
    scenario = [
        ("请站起来", "首先站起来"),
        ("挥挥手", "向访客挥手"),
        ("拥抱", "热烈欢迎"),
        ("鼓掌", "表示高兴"),
    ]
    
    for command, description in scenario:
        print(f"\n📍 {description}")
        executor.process_text_command(command)
        time.sleep(0.5)
    
    executor.cleanup()


def main():
    """主演示函数"""
    print("\n" + "🤖 " * 20)
    print("G1机器人 - 文本分类与动作执行系统 - 完整演示")
    print("🤖 " * 20)
    
    demos = [
        ("文本分类", demo_text_classification),
        ("动作执行", demo_action_execution),
        ("文本到动作", demo_text_to_action),
        ("批量处理", demo_batch_processing),
        ("动作建议", demo_action_suggestions),
        ("动作信息", demo_action_info),
        ("分类器API", demo_classifier_api),
        ("自定义场景", demo_custom_scenario),
    ]
    
    print("\n可用的演示:")
    for i, (name, _) in enumerate(demos, 1):
        print(f"  {i}. {name}")
    print(f"  0. 运行所有演示")
    print(f"  q. 退出")
    
    try:
        while True:
            print()
            choice = input("请选择演示 (0-8, q退出): ").strip().lower()
            
            if choice == 'q':
                print("\n👋 再见！")
                break
            
            if choice == '0':
                # 运行所有演示
                for name, demo_func in demos:
                    try:
                        demo_func()
                        time.sleep(0.5)
                    except Exception as e:
                        print(f"❌ 演示错误: {e}")
            else:
                try:
                    idx = int(choice) - 1
                    if 0 <= idx < len(demos):
                        name, demo_func = demos[idx]
                        demo_func()
                    else:
                        print("❌ 无效的选择")
                except (ValueError, IndexError):
                    print("❌ 无效的选择")
    
    except KeyboardInterrupt:
        print("\n\n👋 中断退出")


if __name__ == "__main__":
    main()
