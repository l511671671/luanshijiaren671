"""
WorkBuddy 主程序接入：根据任务复杂度自动选择模型并启动 CLI

用法：
  python workbuddy_router.py "帮我设计一个A股量化交易系统"

说明：
  1. 使用 router/model_router.py 对 prompt 分级
  2. 根据 model-routing.json 的 tier_to_model 选择 WorkBuddy model id
  3. 调用 codebuddy CLI 的 --model 和 --fallback-model 启动会话
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

# 让 Python 能找到 router 模块
WORKBUDDY_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(WORKBUDDY_DIR))

from router.model_router import ModelRouter, TaskTier, ModelConfig, DEFAULT_MODELS  # noqa: E402

ROUTING_CONFIG_PATH = WORKBUDDY_DIR / "model-routing.json"


def load_routing_config() -> dict:
    with open(ROUTING_CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def select_workbuddy_model(prompt: str, config: dict) -> tuple:
    """
    返回 (主模型 id, fallback 模型 id 列表)
    """
    # 使用 router 分级
    router_models = [
        ModelConfig(
            id="deepseek-v4-flash",
            name="DeepSeek-V4 Flash",
            vendor="DeepSeek",
            tier="standard",
            fallback_order=1,
        ),
        ModelConfig(
            id="deepseek-v4",
            name="DeepSeek-V4",
            vendor="DeepSeek",
            tier="complex",
            fallback_order=2,
        ),
        ModelConfig(
            id="deepseek-r1",
            name="DeepSeek-R1",
            vendor="DeepSeek",
            tier="verify",
            fallback_order=3,
        ),
    ]
    router = ModelRouter(models=router_models)
    result = router.route(prompt)

    tier = result.tier.value
    tier_to_model = config.get("tier_to_model", {})
    fallback_chain = config.get("fallback_chain", {}).get(tier, [])

    model_id = tier_to_model.get(tier)
    if not model_id:
        model_id = result.selected.id

    # 过滤掉主模型，确保 fallback 不同
    fallbacks = [m for m in fallback_chain if m != model_id]

    return model_id, fallbacks, tier


def run_workbuddy(prompt: str, model_id: str, fallbacks: list, cli_path: str):
    cli_path = str(cli_path)
    if cli_path.lower().endswith("codebuddy") and not cli_path.lower().endswith((".exe", ".cmd", ".bat")):
        cmd = ["node", cli_path, "--model", model_id]
    else:
        cmd = [cli_path, "--model", model_id]
    if fallbacks:
        cmd.extend(["--fallback-model", fallbacks[0]])
    cmd.extend(["-p", "--", prompt])

    print(f"[WorkBuddy Router] tier -> model={model_id} fallback={fallbacks[:1]}")
    print(f"[WorkBuddy Router] command: {' '.join(cmd)}")

    try:
        subprocess.run(cmd, check=True)
    except FileNotFoundError as exc:
        raise RuntimeError(f"CLI not found at {cli_path}. Check model-routing.json.") from exc
    except subprocess.CalledProcessError as exc:
        print(f"[WorkBuddy Router] CLI exited with code {exc.returncode}")
        raise


def main():
    dry_run = "--dry-run" in sys.argv
    if dry_run:
        sys.argv.remove("--dry-run")

    if len(sys.argv) < 2:
        print("Usage: python workbuddy_router.py [--dry-run] <prompt>")
        sys.exit(1)

    prompt = sys.argv[1]
    config = load_routing_config()
    cli_path = config.get("cli_path", "codebuddy")

    model_id, fallbacks, tier = select_workbuddy_model(prompt, config)
    print(f"[WorkBuddy Router] prompt classified as {tier}")

    if dry_run:
        print(f"[DRY RUN] selected model={model_id} fallback={fallbacks[:1]}")
        print(f"[DRY RUN] would run: {cli_path} --model {model_id} --fallback-model {fallbacks[0]} -p -- {prompt}")
        return

    run_workbuddy(prompt, model_id, fallbacks, cli_path)


if __name__ == "__main__":
    main()
