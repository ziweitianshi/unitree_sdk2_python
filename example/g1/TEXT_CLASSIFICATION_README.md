# G1机器人 - 文本/语音动作分类与执行系统

## 🎯 功能概述

这个系统提供了一个完整的解决方案，用于：
1. **文本分类**：根据中文语音文本分类出具体的机器人动作
2. **动作执行**：通过G1 SDK执行分类出的动作
3. **语音识别**（可选）：支持语音输入到文本的转换
4. **交互模式**：实时对话与机器人交互

## 📁 系统结构

```
G1文本分类与执行系统
├── text_classifier.py      # 文本分类器核心
├── action_executor.py      # 动作执行器
├── main_system.py         # 主程序和CLI接口
├── config.json            # 配置文件
├── commands_example.txt   # 示例命令列表
└── README.md              # 本文件
```

## 🚀 快速开始

### 1. 环境准备

```bash
# 进入项目目录
cd unitree_sdk2_python/example/g1

# 安装依赖（如需要语音识别功能）
pip install openai-whisper
```

### 2. 基本使用

#### 交互模式（推荐）
```bash
python main_system.py --interactive
```
在交互界面中输入自然语言命令：
```
>> 输入命令: 站起来
>> 输入命令: 向前走
>> 输入命令: 拥抱
>> 输入命令: 挥手
```

#### 单个命令
```bash
python main_system.py --command "站起来"
python main_system.py --command "向前走"
python main_system.py --command "手臂拥抱"
```

#### 根据机器人回答文本选择动作（Qwen/LLM分类）

当“人类问题 -> 机器人回答”的模块已经完成时，把机器人即将说出的回答文本传给
`--reply`。系统会让大模型根据回答的情绪、意图和安全性选择动作，或者输出
`no_action`。

```bash
export DASHSCOPE_API_KEY="你的DashScope API Key"

python main_system.py \
  --config config.json \
  --classifier llm \
  --reply "太棒了！我为你鼓掌。"
```

真实G1执行时再加：

```bash
python main_system.py \
  --config config.json \
  --classifier llm \
  --reply "你好，我很高兴见到你。" \
  --real-robot \
  --iface eth0
```

`eth0` 请替换成连接G1的实际网卡名。未设置 `DASHSCOPE_API_KEY` 时，系统会自动退回本地规则分类。

#### 批量处理
```bash
python main_system.py --batch commands_example.txt
```

#### 查看所有可用动作
```bash
python main_system.py --list-actions
```

## 📚 支持的动作

### Loco (腿部/移动) 动作 - 17种

| 动作 | 关键词示例 | 说明 |
|------|---------|------|
| `stand_up` | 站起来, 站立, 起来 | 从蹲姿或躺姿站立 |
| `squat` | 蹲下, 蹲 | 从站立蹲下 |
| `move_forward` | 前进, 向前, 走 | 向前行走 |
| `move_backward` | 后退, 向后 | 向后行走 |
| `move_left` | 左移, 向左 | 向左移动 |
| `move_right` | 右移, 向右 | 向右移动 |
| `rotate_left` | 左转, 逆时针 | 左转身 |
| `rotate_right` | 右转, 顺时针 | 右转身 |
| `high_stand` | 高站, 站起来 | 高站立姿态 |
| `low_stand` | 低站, 蹲 | 低站立姿态 |
| `zero_torque` | 零力矩, 软 | 零力矩模式 |
| `wave_hand_simple` | 挥手, wave | 简单挥手 |
| `wave_hand_rotate` | 转身挥手, 转身 | 转身并挥手 |
| `shake_hand` | 握手, shake | 握手动作 |
| `lie_to_stand` | 躺, 躺下 | 从躺姿站起 |
| `damp` | 放松, 松弛, 阻尼 | 进入阻尼状态 |

### Arm (手臂) 动作 - 8种

| 动作 | 关键词示例 | 说明 |
|------|---------|------|
| `arm_shake_hand` | 手臂握手, 握手 | 手臂握手 |
| `arm_high_five` | 击掌, high five, 拍手 | 击掌动作 |
| `arm_hug` | 拥抱, hug, 熊抱 | 拥抱动作 |
| `arm_wave` | 手臂挥手, 挥手, hi | 手臂挥手 |
| `arm_clap` | 拍手, 鼓掌, clap | 鼓掌动作 |
| `arm_face_wave` | 脸部挥手, face wave | 脸部挥手 |
| `arm_hands_up` | 举手, hands up, 加油 | 举手动作 |
| `arm_reject` | 摇头, reject, 不 | 拒绝动作 |

## 💻 Python API 使用

### 基础使用

```python
from text_classifier import ActionType, TextClassifier
from action_executor import G1ActionExecutor

# 创建分类器和执行器
classifier = TextClassifier()
executor = G1ActionExecutor(use_real_robot=False, verbose=True)

# 分类文本
action, confidence = classifier.classify_text("站起来")
print(f"分类结果: {action.value}, 置信度: {confidence:.2%}")

# 执行动作
executor.process_text_command("向前走")
```

### 批量处理

```python
commands = ["站起来", "向前走", "左转", "挥手"]
for cmd in commands:
    executor.process_text_command(cmd)
    time.sleep(0.5)
```

### 动作建议

```python
# 获取前3个最相似的动作
suggestions = classifier.suggest_action("走")
for action, score in suggestions:
    print(f"{action.value}: {score:.2%}")
```

## 🔧 高级配置

编辑 `config.json` 来配置系统参数：

```json
{
  "default_duration": 2.0,        # 默认动作持续时间（秒）
  "confidence_threshold": 0.6,    # 分类置信度阈值
  "classifier_mode": "llm",       # "rule" 或 "llm"
  "enable_suggestions": true,     # 是否启用动作建议
  "max_suggestions": 3,           # 最多建议数量
  "robot_mode": "simulation",     # "simulation" 或 "real"
  "network_interface": "eth0",    # 真实G1网络接口
  "robot_timeout": 10.0,          # SDK RPC超时时间
  "llm": {
    "provider": "qwen_openai_compatible",
    "model": "qwen-plus",
    "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "api_key_env": "DASHSCOPE_API_KEY",
    "temperature": 0.0,
    "timeout": 15.0,
    "min_confidence": 0.6,
    "fallback_to_rules": true
  },
  "verbose": true                 # 是否输出详细信息
}
```

## 🎤 语音识别集成

### 使用Whisper进行语音识别

```bash
# 安装Whisper
pip install openai-whisper

# 使用语音输入
python main_system.py --audio audio_input.wav
```

### Python API

```python
system = G1SmartActionSystem(use_real_robot=False)
text = system.process_voice_input("audio.wav")
system.process_command(text)
```

## 📊 分类原理

系统使用多层次的文本匹配策略：

1. **精确匹配**：检查关键词是否完全包含在输入文本中
2. **相似度匹配**：使用编辑距离（Levenshtein distance）计算相似度
3. **置信度排序**：选择置信度最高的分类结果
4. **动作建议**：当分类失败时提供最相似的动作建议

### 示例

```python
classifier = TextClassifier()

# 精确匹配
action, score = classifier.classify_text("请站起来")
# 结果: (ActionType.STAND_UP, 1.0)

# 相似度匹配
action, score = classifier.classify_text("站")
# 结果: (ActionType.STAND_UP, 0.85)

# 无法识别
action, score = classifier.classify_text("随机文本")
# 结果: (None, 0.15)
# 建议: [(ActionType.MOVE_FORWARD, 0.3), ...]
```

## 🤖 真实机器人模式

### 连接到真实G1机器人

```python
# 启用真实机器人模式
executor = G1ActionExecutor(use_real_robot=True, verbose=True)

# 或使用CLI
python main_system.py --real-robot --interactive
```

### 确保事项

1. 确保G1 SDK正确安装
2. 机器人网络连接正常
3. 机器人处于安全状态（地面上，周围没有障碍物）
4. 首次运行时请做好机器人的安全防护

## ⚠️ 注意事项

1. **安全第一**：测试动作时，请在安全的环境中运行
2. **模拟模式**：默认以模拟模式运行，不会实际控制机器人
3. **网络连接**：真实模式需要与机器人的网络连接
4. **库依赖**：确保G1 SDK库正确安装
5. **中文支持**：分类器完全支持中文输入

## 🐛 故障排除

### 问题1：G1 SDK未找到
```
⚠️ 警告: G1 SDK未找到，将使用模拟模式
```
**解决方案**：
```bash
cd ../..
pip install -e .
```

### 问题2：分类结果不准确
- 检查输入文本中是否包含关键词
- 查看是否启用了动作建议
- 可以添加自定义关键词到 `text_classifier.py` 中的 `action_keywords`

### 问题3：语音识别慢或失败
- 确保已安装Whisper：`pip install openai-whisper`
- 使用更小的模型：修改 `system.py` 中的 `"base"` 为 `"tiny"`
- 检查音频文件格式（推荐 .wav 或 .mp3）

## 📝 自定义扩展

### 添加新动作

编辑 `text_classifier.py`：

```python
class ActionType(Enum):
    # 添加新动作
    MY_CUSTOM_ACTION = "my_custom_action"

# 在 TextClassifier.__init__ 中添加
self.action_keywords[ActionType.MY_CUSTOM_ACTION] = ["我的关键词1", "关键词2"]
```

### 添加新的关键词

```python
self.action_keywords[ActionType.STAND_UP].extend(["起来吧", "站起来"])
```

### 自定义执行逻辑

在 `action_executor.py` 的 `_execute_loco_action` 中添加：

```python
elif action == ActionType.MY_CUSTOM_ACTION:
    # 自定义逻辑
    print("执行自定义动作")
```

## 📈 性能指标

| 指标 | 值 |
|------|-----|
| 文本分类延迟 | < 50ms |
| 内存占用（模拟模式） | ~ 50MB |
| 支持的动作总数 | 25+ |
| 语言支持 | 中文、英文 |

## 🔄 更新日志

### v1.0 (2024年)
- ✓ 基础文本分类器
- ✓ G1 Loco和Arm动作执行
- ✓ 交互式命令行接口
- ✓ 批量处理支持
- ✓ 动作建议功能

## 📞 技术支持

如遇到问题，请检查：
1. 依赖库是否正确安装
2. 配置文件是否正确
3. 机器人网络连接（真实模式）
4. 输入文本格式是否正确

## 📄 许可证

遵循Unitree SDK的许可证

---

**祝你使用愉快！🚀**
