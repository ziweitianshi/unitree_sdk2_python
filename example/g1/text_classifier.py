"""
G1机器人 - 文本动作分类器
将语音/文本输入分类为具体的机器人动作
"""

import json
import os
import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Tuple, Optional, Any
import difflib


class ActionType(Enum):
    """动作类型枚举，动作值与 g1_arm_action_client.action_map 保持一致。"""
    NO_ACTION = "no_action"
    RELEASE_ARM = "release arm"
    TWO_HAND_KISS = "two-hand kiss"
    LEFT_KISS = "left kiss"
    RIGHT_KISS = "right kiss"
    HANDS_UP = "hands up"
    CLAP = "clap"
    HIGH_FIVE = "high five"
    HUG = "hug"
    HEART = "heart"
    RIGHT_HEART = "right heart"
    REJECT = "reject"
    RIGHT_HAND_UP = "right hand up"
    X_RAY = "x-ray"
    FACE_WAVE = "face wave"
    HIGH_WAVE = "high wave"
    SHAKE_HAND = "shake hand"


ACTION_DESCRIPTIONS: Dict[ActionType, str] = {
    ActionType.NO_ACTION: "不执行任何动作，用于普通问答、解释、没有明显情绪或动作意图的回答",
    ActionType.RELEASE_ARM: "释放手臂动作/回到释放状态",
    ActionType.TWO_HAND_KISS: "双手飞吻",
    ActionType.LEFT_KISS: "左手飞吻",
    ActionType.RIGHT_KISS: "右手飞吻",
    ActionType.HANDS_UP: "双手举起/庆祝",
    ActionType.CLAP: "鼓掌",
    ActionType.HIGH_FIVE: "击掌",
    ActionType.HUG: "拥抱",
    ActionType.HEART: "双手比心",
    ActionType.RIGHT_HEART: "右手比心",
    ActionType.REJECT: "拒绝/摆手",
    ActionType.RIGHT_HAND_UP: "右手举起",
    ActionType.X_RAY: "X-Ray动作",
    ActionType.FACE_WAVE: "脸部附近挥手",
    ActionType.HIGH_WAVE: "高位挥手",
    ActionType.SHAKE_HAND: "握手",
}


@dataclass
class ClassificationResult:
    """动作分类结果"""
    action: ActionType
    confidence: float
    reason: str = ""
    source: str = "rule"


class TextClassifier:
    """文本到动作的分类器"""
    
    def __init__(self):
        """初始化分类器，建立关键词映射"""
        self.action_keywords: Dict[ActionType, List[str]] = {
            ActionType.NO_ACTION: [
                "不做动作",
                "不用动作",
                "不需要动作",
                "不需要任何动作",
                "无需动作",
                "无需任何动作",
                "没有动作",
                "no action",
                "none",
            ],

            ActionType.RELEASE_ARM: ["释放手臂", "放下手", "release arm", "release"],
            ActionType.TWO_HAND_KISS: ["双手飞吻", "飞吻", "two-hand kiss", "kiss"],
            ActionType.LEFT_KISS: ["左手飞吻", "left kiss"],
            ActionType.RIGHT_KISS: ["右手飞吻", "right kiss"],
            ActionType.HANDS_UP: ["举双手", "双手举起", "庆祝", "加油", "hands up"],
            ActionType.CLAP: ["拍手", "鼓掌", "clap", "掌声"],
            ActionType.HIGH_FIVE: ["击掌", "high five", "give me five", "拍一下手"],
            ActionType.HUG: ["拥抱", "抱抱", "hug", "熊抱"],
            ActionType.HEART: ["比心", "双手比心", "爱心", "heart"],
            ActionType.RIGHT_HEART: ["右手比心", "单手比心", "right heart"],
            ActionType.REJECT: ["摇头", "拒绝", "摆手拒绝", "不可以", "reject", "say no"],
            ActionType.RIGHT_HAND_UP: ["举右手", "右手举起", "right hand up"],
            ActionType.X_RAY: ["x-ray", "xray", "透视"],
            ActionType.FACE_WAVE: ["脸部挥手", "近脸挥手", "face wave"],
            ActionType.HIGH_WAVE: ["挥手", "高位挥手", "打招呼", "再见", "high wave", "wave"],
            ActionType.SHAKE_HAND: ["握手", "shake hand", "shake"],
        }
        self.action_params: Dict[ActionType, Dict] = {}
    
    def classify_text(self, text: str, threshold: float = 0.6) -> Tuple[Optional[ActionType], float]:
        """
        分类文本为动作
        
        Args:
            text: 输入的文本（可以来自语音识别）
            threshold: 匹配置信度阈值 (0-1)
        
        Returns:
            (ActionType, confidence_score) 元组
        """
        text = text.lower().strip()
        
        best_action = None
        best_score = 0.0
        
        # 遍历所有动作，计算匹配分数
        for action, keywords in self.action_keywords.items():
            for keyword in keywords:
                # 方法1: 完全匹配
                if keyword in text:
                    score = 1.0
                else:
                    # 方法2: 相似度匹配 (使用difflib)
                    score = difflib.SequenceMatcher(None, keyword, text).ratio()
                
                if score > best_score:
                    best_score = score
                    best_action = action
        
        # 只返回超过阈值的结果
        if best_score >= threshold:
            return best_action, best_score
        else:
            return None, best_score

    def classify_reply(self, reply_text: str, threshold: float = 0.6) -> ClassificationResult:
        """根据机器人将要说出的回答文本，使用规则 fallback 分类动作。"""
        action, confidence = self.classify_text(reply_text, threshold)
        if action is None:
            return ClassificationResult(
                action=ActionType.NO_ACTION,
                confidence=confidence,
                reason="规则分类未达到阈值",
                source="rule",
            )
        return ClassificationResult(
            action=action,
            confidence=confidence,
            reason="规则关键词匹配",
            source="rule",
        )
    
    def get_action_info(self, action: ActionType) -> Dict:
        """
        获取动作的详细信息
        
        Args:
            action: ActionType 枚举值
        
        Returns:
            包含动作信息的字典
        """
        return {
            "action": action.value,
            "type": self._get_action_type_category(action),
            "description": ACTION_DESCRIPTIONS.get(action, ""),
            "keywords": self.action_keywords.get(action, []),
            "params": self.action_params.get(action, {}),
        }
    
    def _get_action_type_category(self, action: ActionType) -> str:
        """获取动作的类别（Loco或Arm）"""
        if action == ActionType.NO_ACTION:
            return "none"
        return "arm"
    
    def suggest_action(self, text: str, top_k: int = 3) -> List[Tuple[ActionType, float]]:
        """
        建议最相似的K个动作
        
        Args:
            text: 输入文本
            top_k: 返回的建议数量
        
        Returns:
            [(ActionType, confidence_score), ...] 列表
        """
        text = text.lower().strip()
        scores = []
        
        for action, keywords in self.action_keywords.items():
            max_keyword_score = 0.0
            for keyword in keywords:
                if keyword in text:
                    score = 1.0
                else:
                    score = difflib.SequenceMatcher(None, keyword, text).ratio()
                max_keyword_score = max(max_keyword_score, score)
            
            if max_keyword_score > 0:
                scores.append((action, max_keyword_score))
        
        # 按分数排序，返回top K
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]


class LLMActionClassifier:
    """使用 OpenAI-compatible Chat API 的动作分类器，可接 Qwen/DashScope。"""

    def __init__(self, config: Optional[Dict[str, Any]] = None, fallback: Optional[TextClassifier] = None):
        self.config = config or {}
        self.fallback = fallback or TextClassifier()
        self.model = self.config.get("model", "qwen-plus")
        self.base_url = self.config.get(
            "base_url",
            "https://dashscope.aliyuncs.com/compatible-mode/v1",
        ).rstrip("/")
        self.api_key_env = self.config.get("api_key_env", "DASHSCOPE_API_KEY")
        self.timeout = float(self.config.get("timeout", 15.0))
        self.temperature = float(self.config.get("temperature", 0.0))
        self.extra_body = self.config.get("extra_body")
        self.min_confidence = float(self.config.get("min_confidence", 0.6))
        self.use_fallback_on_error = bool(self.config.get("fallback_to_rules", True))

    def classify_reply(self, reply_text: str) -> ClassificationResult:
        """根据机器人回答文本分类为动作或 no_action。"""
        api_key = os.getenv(self.api_key_env)
        if not api_key:
            if self.use_fallback_on_error:
                result = self.fallback.classify_reply(reply_text, self.min_confidence)
                result.reason = f"未设置环境变量 {self.api_key_env}，已使用规则 fallback: {result.reason}"
                return result
            raise RuntimeError(f"未设置环境变量 {self.api_key_env}")

        try:
            payload = self._build_payload(reply_text)
            response = self._post_chat_completion(api_key, payload)
            content = response["choices"][0]["message"]["content"]
            result = self._parse_model_json(content)
            if result.confidence < self.min_confidence:
                return ClassificationResult(
                    action=ActionType.NO_ACTION,
                    confidence=result.confidence,
                    reason=f"LLM置信度低于阈值: {result.reason}",
                    source="llm",
                )
            return result
        except Exception as exc:
            if self.use_fallback_on_error:
                result = self.fallback.classify_reply(reply_text, self.min_confidence)
                result.reason = f"LLM分类失败，已使用规则 fallback: {exc}; {result.reason}"
                return result
            raise

    def _build_payload(self, reply_text: str) -> Dict[str, Any]:
        actions_text = "\n".join(
            f"- {action.value}: {ACTION_DESCRIPTIONS.get(action, '')}"
            for action in ActionType
        )
        system_prompt = f"""你是宇树 G1 机器人的动作分类器。
你的输入是“机器人即将通过扬声器说出的回答文本”，不是用户原始问题。
请根据回答文本的情绪、社交意图、语义和安全性，选择一个最合适的机器人动作。

可选动作白名单如下。除 no_action 代表不执行外，其余 action 必须是
unitree_sdk2py/g1/arm/g1_arm_action_client.py 的 action_map 中已有动作名：
{actions_text}

分类原则：
1. 普通解释、事实回答、闲聊、没有明显肢体表达需求时，选择 no_action。
2. 快乐、祝贺、鼓励、赞同时，可选择 clap、hands up、high five、heart 或 high wave。
3. 问候、告别、自我介绍时，可选择 high wave 或 face wave。
4. 安慰、亲近、表达温暖时，可选择 hug，但不确定时选择 no_action。
5. 拒绝、否定、不能做某事时，可选择 reject。
6. 不要输出 stand_up、move_forward、arm_hug、arm_clap 等不在 action_map 中的旧动作名。
7. 无法确定、多个动作都合理、或动作可能与回答冲突时，选择 no_action。

只输出 JSON，不要输出 Markdown。格式：
{{"action":"no_action","confidence":0.0,"reason":"简短中文理由"}}"""

        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": reply_text},
            ],
            "temperature": self.temperature,
        }
        if isinstance(self.extra_body, dict):
            payload["extra_body"] = self.extra_body
        return payload

    def _post_chat_completion(self, api_key: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        request = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"LLM HTTP {exc.code}: {body}") from exc

    def _parse_model_json(self, content: str) -> ClassificationResult:
        content = content.strip()
        match = re.search(r"\{.*\}", content, flags=re.DOTALL)
        if not match:
            raise ValueError(f"模型未返回JSON: {content}")

        data = json.loads(match.group(0))
        action_value = str(data.get("action", "no_action")).strip()
        confidence = float(data.get("confidence", 0.0))
        reason = str(data.get("reason", "")).strip()

        try:
            action = ActionType(action_value)
        except ValueError:
            action = ActionType.NO_ACTION
            reason = f"模型返回了非法动作 {action_value!r}，已改为 no_action。{reason}"

        return ClassificationResult(
            action=action,
            confidence=max(0.0, min(1.0, confidence)),
            reason=reason,
            source="llm",
        )


# 快速分类函数
def classify_action_text(text: str) -> Tuple[Optional[ActionType], float]:
    """
    快速分类文本
    
    Args:
        text: 输入文本
    
    Returns:
        (ActionType, confidence_score) 元组
    """
    classifier = TextClassifier()
    return classifier.classify_text(text)


if __name__ == "__main__":
    # 测试分类器
    classifier = TextClassifier()
    
    test_cases = [
        "我要站起来",
        "请向前走",
        "给我挥挥手",
        "拥抱我",
        "高五击掌",
        "转身走",
        "不知道",
    ]
    
    print("=" * 60)
    print("G1文本分类器 - 测试")
    print("=" * 60)
    
    for text in test_cases:
        action, score = classifier.classify_text(text)
        if action:
            print(f"\n输入: '{text}'")
            print(f"分类: {action.value} (置信度: {score:.2%})")
            print(f"动作类型: {classifier.get_action_info(action)['type']}")
        else:
            print(f"\n输入: '{text}' - 无匹配动作")
            suggestions = classifier.suggest_action(text, top_k=3)
            if suggestions:
                print("建议动作:")
                for suggested_action, suggested_score in suggestions:
                    print(f"  - {suggested_action.value} ({suggested_score:.2%})")
