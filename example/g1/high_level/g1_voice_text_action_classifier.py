#!/usr/bin/env python3
"""
Classify recognized Chinese/English voice text into a safe G1 high-level action.

Default mode is dry-run. Add --execute and --iface <networkInterface> to send the
classified action to a Unitree G1 robot through unitree_sdk2_python.
"""

from __future__ import annotations

import argparse
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable


SDK_ROOT = Path(__file__).resolve().parents[3]
if str(SDK_ROOT) not in sys.path:
    sys.path.insert(0, str(SDK_ROOT))


@dataclass(frozen=True)
class RobotAction:
    name: str
    kind: str
    method: str
    args: tuple = ()
    release_after: float = 0.0
    description: str = ""


ACTIONS = {
    "stop": RobotAction("stop", "loco", "StopMove", description="停止移动"),
    "damp": RobotAction("damp", "loco", "Damp", description="阻尼保护"),
    "stand_up": RobotAction("stand_up", "loco", "Squat2StandUp", description="站起来"),
    "squat": RobotAction("squat", "loco", "StandUp2Squat", description="蹲下"),
    "high_stand": RobotAction("high_stand", "loco", "HighStand", description="高站姿"),
    "low_stand": RobotAction("low_stand", "loco", "LowStand", description="低站姿"),
    "move_forward": RobotAction("move_forward", "loco", "Move", (0.3, 0.0, 0.0), description="向前走"),
    "move_back": RobotAction("move_back", "loco", "Move", (-0.3, 0.0, 0.0), description="后退"),
    "move_left": RobotAction("move_left", "loco", "Move", (0.0, 0.25, 0.0), description="左移"),
    "move_right": RobotAction("move_right", "loco", "Move", (0.0, -0.25, 0.0), description="右移"),
    "turn_left": RobotAction("turn_left", "loco", "Move", (0.0, 0.0, 0.35), description="左转"),
    "turn_right": RobotAction("turn_right", "loco", "Move", (0.0, 0.0, -0.35), description="右转"),
    "loco_wave": RobotAction("loco_wave", "loco", "WaveHand", description="挥手"),
    "loco_shake": RobotAction("loco_shake", "loco", "ShakeHand", description="握手"),
    "release_arm": RobotAction("release_arm", "arm", "release arm", description="释放手臂"),
    "arm_shake": RobotAction("arm_shake", "arm", "shake hand", release_after=2.0, description="上肢握手"),
    "high_five": RobotAction("high_five", "arm", "high five", release_after=2.0, description="击掌"),
    "hug": RobotAction("hug", "arm", "hug", release_after=2.0, description="拥抱"),
    "clap": RobotAction("clap", "arm", "clap", description="鼓掌"),
    "heart": RobotAction("heart", "arm", "heart", release_after=2.0, description="比心"),
    "hands_up": RobotAction("hands_up", "arm", "hands up", release_after=2.0, description="举手"),
    "reject": RobotAction("reject", "arm", "reject", release_after=2.0, description="拒绝/摆手"),
}


RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("stop", ("停", "停止", "别动", "刹车", "stop", "halt")),
    ("damp", ("阻尼", "保护模式", "damp")),
    ("stand_up", ("站起来", "起立", "站立", "stand up")),
    ("squat", ("蹲下", "下蹲", "squat")),
    ("high_stand", ("站高", "高一点", "高站姿", "high stand")),
    ("low_stand", ("站低", "低一点", "低站姿", "low stand")),
    ("turn_left", ("左转", "向左转", "turn left")),
    ("turn_right", ("右转", "向右转", "turn right")),
    ("move_left", ("左移", "向左走", "往左走", "move left")),
    ("move_right", ("右移", "向右走", "往右走", "move right")),
    ("move_back", ("后退", "往后", "退后", "back", "backward")),
    ("move_forward", ("前进", "向前", "往前", "forward")),
    ("high_five", ("击掌", "give me five", "high five")),
    ("hug", ("拥抱", "抱一下", "hug")),
    ("heart", ("比心", "爱心", "heart")),
    ("clap", ("鼓掌", "拍手", "clap")),
    ("hands_up", ("举手", "抬手", "hands up")),
    ("reject", ("拒绝", "不要", "摆手", "reject")),
    ("arm_shake", ("握手", "shake hand")),
    ("loco_wave", ("挥手", "招手", "wave")),
    ("release_arm", ("放下手", "释放手臂", "手臂复位", "release arm")),
)


def normalize_text(text: str) -> str:
    text = text.lower().strip()
    return re.sub(r"\s+", " ", text)


def classify_voice_text(text: str) -> RobotAction | None:
    normalized = normalize_text(text)
    if not normalized:
        return None

    for action_name, keywords in RULES:
        if any(keyword in normalized for keyword in keywords):
            return ACTIONS[action_name]

    return None


class G1ActionExecutor:
    def __init__(self, network_interface: str, timeout: float = 10.0):
        from unitree_sdk2py.core.channel import ChannelFactoryInitialize
        from unitree_sdk2py.g1.arm.g1_arm_action_client import G1ArmActionClient
        from unitree_sdk2py.g1.arm.g1_arm_action_client import action_map
        from unitree_sdk2py.g1.loco.g1_loco_client import LocoClient

        ChannelFactoryInitialize(0, network_interface)
        self._action_map = action_map

        self._loco = LocoClient()
        self._loco.SetTimeout(timeout)
        self._loco.Init()

        self._arm = G1ArmActionClient()
        self._arm.SetTimeout(timeout)
        self._arm.Init()

    def execute(self, action: RobotAction) -> int | None:
        if action.kind == "loco":
            method: Callable = getattr(self._loco, action.method)
            return method(*action.args)

        if action.kind == "arm":
            action_id = self._action_map.get(action.method)
            if action_id is None:
                raise ValueError(f"Unknown G1 arm action: {action.method}")
            code = self._arm.ExecuteAction(action_id)
            if action.release_after > 0:
                time.sleep(action.release_after)
                self._arm.ExecuteAction(self._action_map["release arm"])
            return code

        raise ValueError(f"Unsupported action kind: {action.kind}")


def iter_input_text(args: argparse.Namespace) -> Iterable[str]:
    if args.text:
        yield args.text
        return

    print("请输入语音识别文本，输入 q/quit/exit 退出。")
    while True:
        try:
            text = input("> ")
        except EOFError:
            return
        if normalize_text(text) in {"q", "quit", "exit"}:
            return
        yield text


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Classify voice text and optionally execute a Unitree G1 action."
    )
    parser.add_argument("text", nargs="?", help="recognized voice text, for one-shot mode")
    parser.add_argument("--iface", help="robot network interface, for example eth0")
    parser.add_argument("--execute", action="store_true", help="send action to the robot")
    parser.add_argument("--timeout", type=float, default=10.0, help="RPC timeout in seconds")
    return parser


def main() -> int:
    args = build_parser().parse_args()

    executor = None
    if args.execute:
        if not args.iface:
            print("--execute 需要同时提供 --iface <networkInterface>", file=sys.stderr)
            return 2
        print("WARNING: Please ensure there are no obstacles around the robot.")
        input("Press Enter to initialize G1 clients and continue...")
        executor = G1ActionExecutor(args.iface, args.timeout)

    for text in iter_input_text(args):
        action = classify_voice_text(text)
        if action is None:
            print(f"[UNKNOWN] {text!r} -> 未匹配到安全动作")
            continue

        print(f"[ACTION] {text!r} -> {action.name} ({action.description})")
        if executor is not None:
            code = executor.execute(action)
            print(f"[EXECUTED] {action.name}, return code: {code}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
