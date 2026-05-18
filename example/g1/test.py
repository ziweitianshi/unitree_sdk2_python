import json
from pathlib import Path

from action_executor import G1ActionExecutor
from text_classifier import LLMActionClassifier, TextClassifier


def load_config() -> dict:
    config_path = Path(__file__).with_name("config.json")
    with config_path.open("r", encoding="utf-8") as f:
        return json.load(f)


config = load_config()

# 这里传入的是“机器人准备说出口的回答文本”，不是用户原始问题。
reply_text = "你好，我向你挥挥手"

rule_classifier = TextClassifier()
classifier = LLMActionClassifier(
    config=config.get("llm", {}),
    fallback=rule_classifier,
)
executor = G1ActionExecutor(
    use_real_robot=config.get("robot_mode") == "real",
    network_interface=config.get("network_interface"),
    timeout=config.get("robot_timeout", 10.0),
    control_mode=config.get("control_mode", "arm_action"),
)

# 大语言模型分类：输出 action / confidence / reason。
# 如果没有设置 DASHSCOPE_API_KEY，会自动退回本地规则分类，并可能返回 no_action。
result = classifier.classify_reply(reply_text)
print(f"分类结果：{result.action.value}")
print(f"置信度：{result.confidence:.1%}")
print(f"来源：{result.source}")
print(f"理由：{result.reason}")

try:
    # 执行动作。若结果是 no_action，执行器会安全地不做动作。
    executor.execute_classification(result)
except KeyboardInterrupt:
    print("\n已手动中断，程序退出。")
