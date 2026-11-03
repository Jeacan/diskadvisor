"""PowerShell 调用封装。"""

from __future__ import annotations

import json
import subprocess
from typing import Any

from loguru import logger


class PowerShellError(RuntimeError):
    """PowerShell 执行错误。"""


def run_powershell(
    script: str,
    *,
    timeout: int = 60,
    as_json: bool = False,
) -> Any:
    """执行 PowerShell 脚本。

    Args:
        script: PowerShell 脚本内容。
        timeout: 超时秒数。
        as_json: 是否将输出解析为 JSON。

    Returns:
        脚本输出；若 as_json 为 True，返回解析后的对象。

    Raises:
        PowerShellError: 执行失败或 JSON 解析失败。
    """
    cmd = [
        "powershell.exe",
        "-NoProfile",
        "-NonInteractive",
        "-ExecutionPolicy",
        "Bypass",
        "-Command",
        script,
    ]

    logger.debug("执行 PowerShell: {}", script[:200])

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding="utf-8",
            errors="replace",
        )
    except subprocess.TimeoutExpired as e:
        raise PowerShellError(f"PowerShell 执行超时（{timeout}s）") from e

    if result.returncode != 0:
        stderr = result.stderr.strip()
        raise PowerShellError(f"PowerShell 执行失败：{stderr}")

    output = result.stdout.strip()

    if as_json:
        if not output:
            return None
        try:
            return json.loads(output)
        except json.JSONDecodeError as e:
            raise PowerShellError(f"JSON 解析失败：{e}\n原始输出：{output[:500]}") from e

    return output


def run_powershell_json(script: str, *, timeout: int = 60) -> Any:
    """执行 PowerShell 并解析 JSON 输出。"""
    return run_powershell(script, timeout=timeout, as_json=True)