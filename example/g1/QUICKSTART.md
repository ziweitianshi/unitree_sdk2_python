# G1机器人文本分类系统 - 快速入门指南

## ⚡ 5分钟快速开始

### 步骤1：进入项目目录
```bash
cd unitree_sdk2_python/example/g1
```

### 步骤2：运行演示程序
```bash
python demo_system.py
```

### 步骤3：选择演示（直接按0运行所有）
```
请选择演示 (0-8, q退出): 0
```

## 🎮 实际使用

### 方式1️⃣ ：交互模式（最简单）
```bash
python main_system.py --interactive
```

在提示符下输入任意自然语言命令：
```
>> 输入命令: 站起来
>> 输入命令: 向前走
>> 输入命令: 拥抱我
```

### 方式2️⃣ ：单个命令
```bash
python main_system.py --command "让G1机器人转身"
python main_system.py --command "做个握手的动作"
```

### 方式3️⃣ ：查看所有支持的动作
```bash
python main_system.py --list-actions
```

### 方式4️⃣ ：批量处理命令
```bash
python main_system.py --batch commands_example.txt
```

## 💻 Python代码集成

### 最简单的使用方式

```python
from action_executor import G1ActionExecutor

# 创建执行器
executor = G1ActionExecutor(use_real_robot=False)

# 输入自然语言，执行动作
executor.process_text_command("请站起来")
executor.process_text_command("向前走三步")
executor.process_text_command("给我一个拥抱")
```

### 更详细的使用

```python
from text_classifier import TextClassifier
from action_executor import G1ActionExecutor

classifier = TextClassifier()
executor = G1ActionExecutor(use_real_robot=False)

# 分类文本
action, confidence = classifier.classify_text("站起来")
print(f"分类结果：{action.value}，置信度：{confidence:.1%}")

# 执行动作
executor.execute_action(action)
```

## 🎯 常用命令示例

| 输入文本 | 结果 | 说明 |
|---------|------|------|
| 站起来 | ✓ | 从蹲姿站立 |
| 向前走 | ✓ | 向前行走 |
| 左转 | ✓ | 左转身 |
| 右转 | ✓ | 右转身 |
| 蹲下 | ✓ | 蹲姿 |
| 挥手 | ✓ | 简单挥手 |
| 转身挥手 | ✓ | 转身并挥手 |
| 拥抱 | ✓ | 拥抱动作 |
| 握手 | ✓ | 握手或手臂握手 |
| 击掌 | ✓ | 击掌/拍手 |
| 鼓掌 | ✓ | 鼓掌 |
| 举手 | ✓ | 举手动作 |
| 放松 | ✓ | 阻尼状态 |

## 🔧 系统架构

```
文本输入
   ↓
[文本分类器] → 分类 + 置信度
   ↓
[动作执行器] → 调用G1 SDK
   ↓
机器人执行动作
```

## 📊 系统特点

✅ **多层分类** - 精确匹配 + 相似度匹配  
✅ **中文支持** - 完全支持中文输入  
✅ **25+动作** - Loco和Arm动作的完整支持  
✅ **智能建议** - 无法识别时提供动作建议  
✅ **模拟模式** - 安全测试，无需真实机器人  
✅ **CLI + API** - 命令行和Python API双支持  
✅ **批处理** - 支持命令序列批量处理  
✅ **可扩展** - 易于添加新动作和关键词  

## ⚠️ 注意事项

1. **默认模拟模式** - 不会实际控制机器人
2. **真实模式** - 加上 `--real-robot` 参数（需确认机器人安全）
3. **G1 SDK** - 需在项目根目录安装：`pip install -e .`
4. **中文输入** - 自然支持，无需特殊配置

## 🚀 下一步

- 查看 [TEXT_CLASSIFICATION_README.md](TEXT_CLASSIFICATION_README.md) 了解详细功能
- 运行 `python demo_system.py` 查看完整演示
- 编辑 `text_classifier.py` 添加自定义关键词
- 在真实G1机器人上测试 (使用 `--real-robot` 参数)

## 🎓 学习资源

1. **文本分类器** - `text_classifier.py` (基于关键词匹配)
2. **动作执行器** - `action_executor.py` (调用G1 SDK)
3. **主程序** - `main_system.py` (CLI接口)
4. **演示程序** - `demo_system.py` (交互式演示)

## 📞 故障排除

### 提示：G1 SDK未找到
```bash
cd ../..
pip install -e .
```

### 分类结果不准确
→ 查看 `text_classifier.py` 中的关键词定义  
→ 手动运行 `demo_system.py` 中的"动作建议"演示

### 命令不响应
→ 检查是否使用了 `--real-robot` 参数  
→ 验证文本输入格式是否正确

---

**现在就开始试试吧！🚀**

```bash
python main_system.py --interactive
```

输入任何自然语言命令，让G1机器人执行！✨
