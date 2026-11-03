"""日志配置。"""

from __future__ import annotations

import sys

from loguru import logger


def setup_logging(verbose: bool = False) -> None:
    """配置日志。

    Args:
        verbose: 是否输出 DEBUG 级别日志。
    """
    logger.remove()

    level = "DEBUG" if verbose else "INFO"
    logger.add(
        sys.stderr,
        level=level,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
    )