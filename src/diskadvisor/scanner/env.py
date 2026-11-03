"""环境变量扫描器。"""

from __future__ import annotations

from diskadvisor.core.models import EnvScope, EnvVar, SystemSnapshot
from diskadvisor.scanner.base import BaseScanner


class EnvScanner(BaseScanner[list[EnvVar]]):
    """扫描环境变量。"""

    name = "env"

    def scan(self) -> list[EnvVar]:
        """扫描进程、用户、系统三级环境变量。"""
        import os

        env_vars: list[EnvVar] = []
        seen: set[tuple[str, str]] = set()

        # 进程级
        for name, value in os.environ.items():
            key = (name, EnvScope.PROCESS.value)
            if key in seen:
                continue
            seen.add(key)
            env_vars.append(EnvVar(name=name, value=value, scope=EnvScope.PROCESS))

        return env_vars

    def apply(self, snapshot: SystemSnapshot, result: list[EnvVar]) -> None:
        snapshot.env_vars = result