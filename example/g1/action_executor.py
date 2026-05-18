"""
G1机器人 - 动作执行器
根据分类结果执行具体的机器人动作
"""

from typing import Optional, Callable
import sys
import time
from pathlib import Path

SDK_ROOT = Path(__file__).resolve().parents[2]
if str(SDK_ROOT) not in sys.path:
    sys.path.insert(0, str(SDK_ROOT))

# 导入分类器
from text_classifier import ActionType, TextClassifier, ClassificationResult

# 导入G1 SDK
try:
    from unitree_sdk2py.core.channel import ChannelFactoryInitialize
    from unitree_sdk2py.g1.arm.g1_arm_action_client import G1ArmActionClient, action_map
    from unitree_sdk2py.g1.loco.g1_loco_client import LocoClient
    HAS_G1_SDK = True
    SDK_IMPORT_ERROR = None
except ImportError as e:
    HAS_G1_SDK = False
    SDK_IMPORT_ERROR = e


class G1ActionExecutor:
    """G1机器人动作执行器"""
    
    def __init__(
        self,
        use_real_robot: bool = True,
        verbose: bool = True,
        network_interface: Optional[str] = None,
        timeout: float = 10.0,
        control_mode: str = "auto",
    ):
        """
        初始化执行器
        
        Args:
            use_real_robot: 是否使用真实机器人（否则使用模拟模式）
            verbose: 是否打印详细信息
            network_interface: 连接G1的网卡名，例如 eth0
            timeout: SDK RPC超时时间
            control_mode: auto 先判断机器人模式，arm_action 使用 ArmAction 服务，walk_run 使用走跑模式 sport 服务
        """
        self.verbose = verbose
        self.use_real_robot = use_real_robot
        self.network_interface = network_interface
        self.timeout = timeout
        self.control_mode = control_mode
        self.arm_client = None
        self.loco_client = None
        self.classifier = TextClassifier()
        
        if use_real_robot and HAS_G1_SDK:
            try:
                self._init_clients()
            except Exception as e:
                self._print(f"⚠️ 机器人初始化失败: {e}")
                self.use_real_robot = False
        elif use_real_robot and not HAS_G1_SDK:
            self._print(f"⚠️ G1 SDK导入失败，将使用模拟模式: {SDK_IMPORT_ERROR}")
            self.use_real_robot = False
    
    def _init_clients(self):
        """初始化G1机器人客户端"""
        if self.network_interface:
            ChannelFactoryInitialize(0, self.network_interface)
            self._print(f"✓ DDS通道初始化成功: {self.network_interface}")
        else:
            self._print("⚠️ 未提供network_interface，将尝试使用SDK默认DDS配置")

        try:
            self.loco_client = LocoClient()
            self.loco_client.SetTimeout(self.timeout)
            self.loco_client.Init()
            self._print("✓ Loco/Sport客户端初始化成功")
        except Exception as e:
            self._print(f"✗ Loco/Sport客户端初始化失败: {e}")

        if self.control_mode == "walk_run":
            return

        try:
            self.arm_client = G1ArmActionClient()
            self.arm_client.SetTimeout(self.timeout)
            self.arm_client.Init()
            self._print("✓ Arm客户端初始化成功")
        except Exception as e:
            self._print(f"✗ Arm客户端初始化失败: {e}")

    def _read_robot_mode(self) -> dict:
        """读取 sport 服务状态，用于判断当前机器人模式。"""
        mode = {
            "fsm_id": None,
            "fsm_mode": None,
            "balance_mode": None,
            "category": "unknown",
        }
        if not self.use_real_robot:
            mode["category"] = self.control_mode
            return mode
        if not self.loco_client:
            self._print("✗ 无法判断机器人模式：Loco/Sport客户端未初始化")
            return mode

        code, fsm_id = self.loco_client.GetFsmId()
        if code != 0:
            self._print(f"✗ 读取 FSM ID 失败 (code={code})")
            return mode

        code, fsm_mode = self.loco_client.GetFsmMode()
        if code != 0:
            self._print(f"⚠️ 读取 FSM Mode 失败 (code={code})")

        code, balance_mode = self.loco_client.GetBalanceMode()
        if code != 0:
            self._print(f"⚠️ 读取 Balance Mode 失败 (code={code})")

        mode.update({
            "fsm_id": fsm_id,
            "fsm_mode": fsm_mode,
            "balance_mode": balance_mode,
            "category": self._categorize_fsm_id(fsm_id),
        })
        self._print(
            "✓ 当前机器人模式: "
            f"{mode['category']} (fsm_id={fsm_id}, fsm_mode={fsm_mode}, balance_mode={balance_mode})"
        )
        return mode

    @staticmethod
    def _categorize_fsm_id(fsm_id) -> str:
        if fsm_id == 500:
            return "walk_run"
        if fsm_id == 0:
            return "zero_torque"
        if fsm_id == 1:
            return "damp"
        if fsm_id in {3, 702, 706}:
            return "transition_or_posture"
        return "unknown"

    def _choose_execution_mode(self, action: ActionType) -> Optional[str]:
        if not self.use_real_robot:
            return self.control_mode

        robot_mode = self._read_robot_mode()
        if robot_mode["category"] == "walk_run":
            if action in self._walk_run_supported_actions():
                return "walk_run"
            self._print(
                f"✗ 当前是走跑模式，不支持动作 {action.value}。"
                "请换成 high wave / face wave / shake hand / release arm，或在机器人端切到支持 ArmAction 的模式。"
            )
            return None

        if self.control_mode == "walk_run":
            self._print(f"✗ 当前不是走跑模式，而是 {robot_mode['category']}，不执行走跑模式动作")
            return None

        if robot_mode["category"] in {"zero_torque", "damp", "transition_or_posture"}:
            self._print(f"✗ 当前模式为 {robot_mode['category']}，不执行动作 {action.value}")
            return None

        self._print("✗ 未能明确判断机器人模式，不执行动作")
        return None

    @staticmethod
    def _walk_run_supported_actions() -> set:
        return {
            ActionType.HIGH_WAVE,
            ActionType.FACE_WAVE,
            ActionType.SHAKE_HAND,
            ActionType.RELEASE_ARM,
        }
    
    def _print(self, msg: str):
        """打印消息"""
        if self.verbose:
            print(msg)
    
    def execute_action(self, action: ActionType, duration: float = 2.0) -> bool:
        """
        执行动作
        
        Args:
            action: ActionType 动作类型
            duration: 持续时间（秒），对某些动作有效
        
        Returns:
            是否执行成功
        """
        if action == ActionType.NO_ACTION:
            self._print("\n🤖 分类结果为 no_action，不执行机器人动作")
            return True

        self._print(f"\n🤖 执行动作: {action.value}")
        
        try:
            action_type = self.classifier.get_action_info(action)["type"]
            
            if action_type == "arm":
                execution_mode = self._choose_execution_mode(action)
                if execution_mode == "walk_run":
                    return self._execute_walk_run_action(action)
                if execution_mode == "arm_action":
                    return self._execute_arm_action(action)
                return False
            else:
                self._print(f"✗ 未知的动作类型: {action_type}")
                return False
        
        except Exception as e:
            self._print(f"✗ 执行动作失败: {e}")
            return False

    def _execute_walk_run_action(self, action: ActionType) -> bool:
        """在走跑模式下通过 Loco/Sport 服务执行支持的手臂任务。"""

        if not self.use_real_robot:
            self._print(f"[模拟] 走跑模式动作: {action.value}")
            return True

        if not self.loco_client:
            self._print("✗ Loco/Sport客户端未初始化")
            return False

        walk_run_actions = {
            ActionType.HIGH_WAVE: lambda: self.loco_client.WaveHand(False),
            ActionType.FACE_WAVE: lambda: self.loco_client.WaveHand(False),
            ActionType.SHAKE_HAND: lambda: self.loco_client.ShakeHand(),
            ActionType.RELEASE_ARM: lambda: self.loco_client.SetTaskId(0),
        }

        handler = walk_run_actions.get(action)
        if handler is None:
            self._print(
                f"✗ 走跑模式不支持 action_map 动作: {action.value}。"
                "请切换 control_mode=arm_action，或选择 high wave / face wave / shake hand。"
            )
            return False

        try:
            code = handler()
            if code != 0:
                self._print(f"✗ 走跑模式动作发送失败: {action.value} (code={code})")
                return False
            self._print(f"✓ 走跑模式动作执行: {action.value}")
            return True
        except Exception as e:
            self._print(f"✗ 走跑模式动作执行失败: {e}")
            return False

    def execute_classification(self, result: ClassificationResult, duration: float = 2.0) -> bool:
        """执行分类结果，包含日志中的置信度和理由。"""
        self._print(
            f"✓ 分类结果: {result.action.value} "
            f"(置信度: {result.confidence:.2%}, 来源: {result.source})"
        )
        if result.reason:
            self._print(f"  理由: {result.reason}")
        return self.execute_action(result.action, duration)
    
    def _execute_arm_action(self, action: ActionType) -> bool:
        """执行Arm（手臂）动作"""
        
        if not self.use_real_robot:
            self._print(f"[模拟] Arm动作: {action.value}")
            return True
        
        if not self.arm_client:
            self._print("✗ Arm客户端未初始化")
            return False
        
        try:
            action_name = action.value
            action_id = action_map.get(action_name)
            if action_id is None:
                self._print(f"⚠️ 动作'{action_name}'在action_map中未找到")
                return False
            
            code = self.arm_client.ExecuteAction(action_id)
            if code != 0:
                self._print(f"✗ 手臂动作发送失败: {action_name} (code={code})")
                return False
            self._print(f"✓ 手臂动作执行: {action_name}")

            if action in {
                ActionType.SHAKE_HAND,
                ActionType.HIGH_FIVE,
                ActionType.HUG,
                ActionType.HANDS_UP,
                ActionType.REJECT,
                ActionType.RIGHT_HAND_UP,
            }:
                time.sleep(2.0)
                release_id = action_map.get("release arm")
                if release_id is not None:
                    code = self.arm_client.ExecuteAction(release_id)
                    if code != 0:
                        self._print(f"✗ 手臂释放发送失败 (code={code})")
                        return False
                    self._print("✓ 手臂已释放")
            return True
        
        except Exception as e:
            self._print(f"✗ Arm动作执行失败: {e}")
            return False
    
    def process_text_command(self, text: str, duration: float = 2.0) -> bool:
        """
        处理文本命令：分类 -> 执行
        
        Args:
            text: 输入文本
            duration: 持续时间
        
        Returns:
            是否成功执行
        """
        self._print(f"\n📝 输入文本: '{text}'")
        
        # 分类文本
        result = self.classifier.classify_reply(text)
        
        if result.action == ActionType.NO_ACTION:
            self._print(f"⚠️ 不执行动作（置信度: {result.confidence:.2%}）")
            # 打印建议
            suggestions = self.classifier.suggest_action(text, top_k=3)
            if suggestions:
                self._print("💡 可能的动作:")
                for suggested_action, score in suggestions:
                    self._print(f"  - {suggested_action.value} ({score:.2%})")
            return False
        
        # 执行动作
        return self.execute_classification(result, duration)
    
    def cleanup(self):
        """清理资源"""
        if self.arm_client:
            try:
                release_id = action_map.get("release arm")
                if release_id is not None:
                    self.arm_client.ExecuteAction(release_id)
                    self._print("✓ 手臂已释放")
            except:
                pass


class TextCommandInterface:
    """文本命令交互接口"""
    
    def __init__(self, executor: G1ActionExecutor):
        """初始化接口"""
        self.executor = executor
    
    def interactive_mode(self):
        """交互模式 - 持续接收用户输入"""
        print("\n" + "=" * 60)
        print("🤖 G1机器人 - 文本动作分类器")
        print("=" * 60)
        print("输入文本命令（输入'quit'或'exit'退出）:")
        print("-" * 60)
        
        try:
            while True:
                try:
                    text = input("\n>> 输入命令: ").strip()
                    
                    if not text:
                        continue
                    
                    if text.lower() in ['quit', 'exit', '退出']:
                        print("\n👋 再见！")
                        break
                    
                    if text.lower() == 'help':
                        self._print_help()
                        continue
                    
                    self.executor.process_text_command(text)
                
                except KeyboardInterrupt:
                    print("\n\n👋 中断退出")
                    break
        
        finally:
            self.executor.cleanup()
    
    @staticmethod
    def _print_help():
        """打印帮助信息"""
        print("\n" + "=" * 60)
        print("💡 使用帮助")
        print("=" * 60)
        print("动作示例:")
        print("  - Arm action_map: '拥抱', '击掌', '挥手', '举手', '鼓掌', '握手', '比心'")
        print("\n命令:")
        print("  - help  : 显示帮助")
        print("  - quit  : 退出程序")
        print("=" * 60)


if __name__ == "__main__":
    # 创建执行器（模拟模式）
    print("🚀 启动G1机器人动作执行器...")
    executor = G1ActionExecutor(use_real_robot=False, verbose=True)
    
    # 创建交互接口
    interface = TextCommandInterface(executor)
    
    # 进入交互模式
    interface.interactive_mode()
