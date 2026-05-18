"""
G1 mode switch helper.

Examples:
  python example/g1/mode_switch.py interactive
  python example/g1/mode_switch.py walk_run
  python example/g1/mode_switch.py damp
  python example/g1/mode_switch.py zero_torque --yes
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

SDK_ROOT = Path(__file__).resolve().parents[2]
if str(SDK_ROOT) not in sys.path:
    sys.path.insert(0, str(SDK_ROOT))

from unitree_sdk2py.core.channel import ChannelFactoryInitialize
from unitree_sdk2py.g1.loco.g1_loco_client import LocoClient


CONFIG_PATH = Path(__file__).with_name("config.json")

MODE_CALLS = {
    "zero_torque": ("零力矩模式", lambda client: client.SetFsmId(0)),
    "damp": ("阻尼/保护模式", lambda client: client.SetFsmId(1)),
    "walk_run": ("走跑模式", lambda client: client.SetFsmId(500)),
    "sit": ("坐下模式", lambda client: client.SetFsmId(3)),
    "stand": ("站立/蹲站切换", lambda client: client.SetFsmId(706)),
    "lie_to_stand": ("躺姿起身", lambda client: client.SetFsmId(702)),
    "high_stand": ("高站姿", lambda client: client.SetStandHeight((1 << 32) - 1)),
    "low_stand": ("低站姿", lambda client: client.SetStandHeight(0)),
    "stop": ("停止移动", lambda client: client.SetVelocity(0.0, 0.0, 0.0)),
    "wave": ("挥手", lambda client: client.SetTaskId(0)),
    "turn_wave": ("转身挥手", lambda client: client.SetTaskId(1)),
    "shake_hand_1": ("握手阶段1", lambda client: client.SetTaskId(2)),
    "shake_hand_2": ("握手阶段2", lambda client: client.SetTaskId(3)),
}

DANGEROUS_MODES = {"zero_torque", "lie_to_stand"}

RPC_ERROR_NAMES = {
    0: "OK",
    3001: "RPC_ERR_UNKNOWN",
    3102: "RPC_ERR_CLIENT_SEND",
    3103: "RPC_ERR_CLIENT_API_NOT_REG",
    3104: "RPC_ERR_CLIENT_API_TIMEOUT",
    3105: "RPC_ERR_CLIENT_API_NOT_MATCH",
    3106: "RPC_ERR_CLIENT_API_DATA",
    3107: "RPC_ERR_CLIENT_LEASE_INVALID",
}


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        return {}
    with CONFIG_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def create_client(interface: str, timeout: float) -> LocoClient:
    ChannelFactoryInitialize(0, interface)
    print(f"✓ DDS通道初始化成功: {interface}")

    client = LocoClient()
    client.SetTimeout(timeout)
    client.Init()
    print("✓ Loco/Sport客户端初始化成功")
    return client


def diagnose_network(interface: str) -> int:
    print(f"诊断网卡: {interface}")
    subprocess.run(["ip", "addr", "show", interface], check=False)
    subprocess.run(["ip", "route"], check=False)

    candidates = ["192.168.123.161", "192.168.123.1"]
    ok = False
    for host in candidates:
        print(f"\nPing {host}:")
        result = subprocess.run(
            ["ping", "-I", interface, "-c", "1", "-W", "1", host],
            check=False,
        )
        ok = ok or result.returncode == 0

    if not ok:
        print("\n✗ 常见机器人地址 ping 不通。请确认机器人 IP、网线、机器人已开机。")
        return 1

    print("\n✓ 至少有一个常见地址可以 ping 通。若 DDS 仍失败，请检查机器人端 sport 服务/模式。")
    return 0


def switch_mode(client: LocoClient, mode: str) -> int:
    _, handler = MODE_CALLS[mode]
    return handler(client)


def print_commands() -> None:
    print("可用命令:")
    for name, (description, _) in MODE_CALLS.items():
        danger = " 需要 --yes" if name in DANGEROUS_MODES else ""
        print(f"  {name:<14} {description}{danger}")
    print("  help           显示命令")
    print("  quit           退出交互模式")


def run_one_command(client: LocoClient, mode: str, assume_yes: bool = False) -> int:
    description, _ = MODE_CALLS[mode]
    if mode in DANGEROUS_MODES and not assume_yes:
        print(f"✗ {description}有风险。如确认安全，请加 --yes，或交互模式中输入 yes {mode}。")
        return 2

    print(f"准备执行: {mode} ({description})")
    code = switch_mode(client, mode)
    if code != 0:
        print(f"✗ 指令发送失败: {mode} (code={code}, {RPC_ERROR_NAMES.get(code, 'UNKNOWN')})")
        if code == 3102:
            print("  3102 表示本机 DDS 请求发送失败，通常是没有匹配到机器人端 sport 服务。")
        return 1

    print(f"✓ 指令已发送: {mode}")
    return 0


def interactive_loop(client: LocoClient) -> int:
    print_commands()
    while True:
        try:
            raw = input("\nmode> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n退出交互模式。")
            return 0

        if not raw:
            continue
        if raw in {"quit", "exit", "q"}:
            return 0
        if raw == "help":
            print_commands()
            continue

        parts = raw.split()
        assume_yes = len(parts) == 2 and parts[0] == "yes"
        mode = parts[1] if assume_yes else parts[0]
        if mode not in MODE_CALLS:
            print(f"✗ 未知命令: {raw}")
            print_commands()
            continue
        run_one_command(client, mode, assume_yes=assume_yes)

    return 0


def main() -> int:
    config = load_config()
    parser = argparse.ArgumentParser(description="G1 机器人模式切换工具")
    parser.add_argument(
        "mode",
        choices=["diagnose", "interactive", *MODE_CALLS.keys()],
        help="要执行的模式命令",
    )
    parser.add_argument(
        "--iface",
        default=config.get("network_interface", "eno1"),
        help="连接机器人的网卡名，默认读取 config.json",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=float(config.get("robot_timeout", 2.0)),
        help="SDK RPC 超时时间",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="跳过危险模式确认",
    )
    args = parser.parse_args()

    if args.mode == "diagnose":
        return diagnose_network(args.iface)

    client = create_client(args.iface, args.timeout)
    if args.mode == "interactive":
        return interactive_loop(client)
    return run_one_command(client, args.mode, assume_yes=args.yes)


if __name__ == "__main__":
    raise SystemExit(main())
