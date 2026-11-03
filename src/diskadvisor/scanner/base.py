"""扫描器基类。"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from loguru import logger

from diskadvisor.core.models import SystemSnapshot

T = TypeVar("T")


class BaseScanner(ABC, Generic[T]):
    """扫描器基类。

    每个扫描器负责采集一类信息，并将结果写入 SystemSnapshot。
    """

    name: str = "base"
    requires_admin: bool = False

    @abstractmethod
    def scan(self) -> T:
        """执行扫描，返回采集结果。"""

    def apply(self, snapshot: SystemSnapshot, result: T) -> None:
        """将扫描结果写入快照。

        Args:
            snapshot: 系统快照。
            result: 扫描结果。
        """
        raise NotImplementedError

    def run(self, snapshot: SystemSnapshot) -> None:
        """执行扫描并写入快照。

        Args:
            snapshot: 系统快照。
        """
        logger.info("开始扫描：{}", self.name)
        try:
            result = self.scan()
            self.apply(snapshot, result)
            logger.info("扫描完成：{}", self.name)
        except Exception as e:
            logger.warning("扫描失败：{} - {}", self.name, e)