"""
G1机器人 - 智能动作系统
集成了文本分类、语音识别（可选）和机器人控制
"""

import sys
import json
from pathlib import Path
from typing import Optional, List
import argparse

from text_classifier import ActionType, TextClassifier, LLMActionClassifier
from action_executor import G1ActionExecutor, TextCommandInterface


class G1SmartActionSystem:
    """G1智能动作系统"""
    
    def __init__(
        self,
        config_file: Optional[str] = None,
        use_real_robot: bool = False,
        network_interface: Optional[str] = None,
        classifier_mode: Optional[str] = None,
    ):
        """
        初始化系统
        
        Args:
            config_file: 配置文件路径
            use_real_robot: 是否使用真实机器人
        """
        self.config = self._load_config(config_file)
        self.classifier_mode = classifier_mode or self.config.get("classifier_mode", "rule")
        self.executor = G1ActionExecutor(
            use_real_robot=use_real_robot,
            verbose=self.config.get("verbose", True),
            network_interface=network_interface or self.config.get("network_interface"),
            timeout=self.config.get("robot_timeout", 10.0),
            control_mode=self.config.get("control_mode", "arm_action"),
        )
        self.rule_classifier = TextClassifier()
        self.llm_classifier = LLMActionClassifier(
            self.config.get("llm", {}),
            fallback=self.rule_classifier,
        )
        self.command_history: List[str] = []
        
        print("✓ G1智能动作系统初始化完成")
    
    def _load_config(self, config_file: Optional[str]) -> dict:
        """加载配置文件"""
        default_config = {
            "default_duration": 2.0,
            "confidence_threshold": 0.6,
            "enable_suggestions": True,
            "max_suggestions": 3,
            "classifier_mode": "rule",
            "llm": {},
        }
        
        if config_file and Path(config_file).exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    default_config.update(config)
                print(f"✓ 加载配置文件: {config_file}")
            except Exception as e:
                print(f"⚠️ 加载配置失败: {e}，使用默认配置")
        
        return default_config
    
    def process_command(self, text: str) -> bool:
        """
        处理单个命令
        
        Args:
            text: 输入文本
        
        Returns:
            是否成功
        """
        self.command_history.append(text)
        duration = self.config.get("default_duration", 2.0)
        return self.executor.process_text_command(text, duration)

    def process_reply_text(self, reply_text: str) -> bool:
        """
        处理机器人已经生成好的回答文本：LLM/规则分类 -> 执行动作。

        Args:
            reply_text: 机器人即将通过扬声器说出的回答文本

        Returns:
            是否成功处理
        """
        self.command_history.append(reply_text)
        duration = self.config.get("default_duration", 2.0)

        print(f"\n📝 回答文本: '{reply_text}'")
        if self.classifier_mode == "llm":
            result = self.llm_classifier.classify_reply(reply_text)
        else:
            result = self.rule_classifier.classify_reply(
                reply_text,
                threshold=self.config.get("confidence_threshold", 0.6),
            )
        return self.executor.execute_classification(result, duration)
    
    def process_batch_commands(self, commands: List[str], delay: float = 0.5):
        """
        批量处理命令序列
        
        Args:
            commands: 命令列表
            delay: 命令间延迟（秒）
        """
        import time
        print(f"\n🔄 批量处理 {len(commands)} 条命令...")
        
        for i, cmd in enumerate(commands, 1):
            print(f"\n[{i}/{len(commands)}] ", end="")
            success = self.process_command(cmd)
            if i < len(commands):
                time.sleep(delay)
    
    def process_voice_input(self, audio_file: str) -> Optional[str]:
        """
        处理语音输入（需要语音识别模型）
        
        Args:
            audio_file: 音频文件路径
        
        Returns:
            识别出的文本
        """
        try:
            # 尝试导入whisper
            import whisper
            print(f"🎤 识别音频: {audio_file}")
            model = whisper.load_model("base")
            result = model.transcribe(audio_file, language="zh")
            text = result["text"]
            print(f"✓ 识别结果: '{text}'")
            return text
        except ImportError:
            print("⚠️ Whisper未安装，请运行: pip install openai-whisper")
            return None
        except Exception as e:
            print(f"✗ 语音识别失败: {e}")
            return None
    
    def get_action_list(self) -> List[dict]:
        """获取所有可用动作列表"""
        classifier = TextClassifier()
        actions = []
        
        for action in ActionType:
            if action == ActionType.NO_ACTION:
                continue
            info = classifier.get_action_info(action)
            actions.append({
                "action_id": action.value,
                "type": info["type"],
                "keywords": info["keywords"][:3],  # 只显示前3个关键词
            })
        
        return actions
    
    def print_stats(self):
        """打印统计信息"""
        print("\n" + "=" * 60)
        print("📊 系统统计")
        print("=" * 60)
        print(f"处理的命令数: {len(self.command_history)}")
        if self.command_history:
            print(f"最后的命令: '{self.command_history[-1]}'")
        print(f"可用动作数: {len([action for action in ActionType if action != ActionType.NO_ACTION])}")
        print("=" * 60)
    
    def cleanup(self):
        """清理资源"""
        self.executor.cleanup()


def main():
    """主程序"""
    parser = argparse.ArgumentParser(
        description="G1机器人 - 文本/语音动作分类与执行系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 交互模式
  python main_system.py --interactive
  
  # 处理单个命令（规则分类，适合直接控制命令）
  python main_system.py --command "站起来"

  # 处理机器人回答文本（LLM分类，适合对话回答 -> 动作）
  python main_system.py --classifier llm --reply "太棒了！我为你鼓掌。"
  
  # 批量处理命令
  python main_system.py --batch commands.txt
  
  # 语音输入
  python main_system.py --audio input.wav
  
  # 列出所有动作
  python main_system.py --list-actions
        """
    )
    
    parser.add_argument(
        "-i", "--interactive",
        action="store_true",
        help="进入交互模式"
    )
    parser.add_argument(
        "-c", "--command",
        type=str,
        help="处理单个命令文本"
    )
    parser.add_argument(
        "--reply",
        type=str,
        help="处理机器人生成的回答文本，并根据回答情感/意图映射动作"
    )
    parser.add_argument(
        "--classifier",
        choices=["rule", "llm"],
        help="分类器类型：rule为本地规则，llm为Qwen/OpenAI-compatible大模型"
    )
    parser.add_argument(
        "-b", "--batch",
        type=str,
        help="批量处理命令文件（每行一个命令）"
    )
    parser.add_argument(
        "-a", "--audio",
        type=str,
        help="处理语音文件（需要whisper）"
    )
    parser.add_argument(
        "-l", "--list-actions",
        action="store_true",
        help="列出所有可用动作"
    )
    parser.add_argument(
        "-r", "--real-robot",
        action="store_true",
        help="使用真实机器人（默认使用模拟模式）"
    )
    parser.add_argument(
        "--iface",
        type=str,
        help="真实G1机器人网络接口，例如 eth0"
    )
    parser.add_argument(
        "--config",
        type=str,
        help="配置文件路径"
    )
    
    args = parser.parse_args()
    
    # 创建系统
    system = G1SmartActionSystem(
        config_file=args.config,
        use_real_robot=args.real_robot,
        network_interface=args.iface,
        classifier_mode=args.classifier,
    )
    
    try:
        # 处理不同的输入模式
        if args.list_actions:
            # 列出所有动作
            print("\n" + "=" * 60)
            print("🎯 可用动作列表")
            print("=" * 60)
            actions = system.get_action_list()
            for action in actions:
                keywords_str = ", ".join(action["keywords"])
                print(f"  [{action['type']}] {action['action_id']}")
                print(f"           关键词: {keywords_str}")
        
        elif args.reply:
            # 处理机器人回答文本
            system.process_reply_text(args.reply)
            system.print_stats()
        
        elif args.command:
            # 处理单个命令
            system.process_command(args.command)
            system.print_stats()
        
        elif args.batch:
            # 批量处理
            if Path(args.batch).exists():
                with open(args.batch, 'r', encoding='utf-8') as f:
                    commands = [line.strip() for line in f if line.strip()]
                system.process_batch_commands(commands)
            else:
                print(f"✗ 文件不存在: {args.batch}")
        
        elif args.audio:
            # 语音识别
            text = system.process_voice_input(args.audio)
            if text:
                system.process_command(text)
        
        else:
            # 默认交互模式
            interface = TextCommandInterface(system.executor)
            interface.interactive_mode()
    
    finally:
        system.cleanup()


if __name__ == "__main__":
    main()
