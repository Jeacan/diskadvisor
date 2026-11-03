"""PowerShell 脚本生成器。"""

from __future__ import annotations

from diskadvisor.recommender.models import Recommendation


class ScriptGenerator:
    """把推荐项转成 PowerShell 脚本。"""

    def generate(
        self,
        recs: list[Recommendation],
        include_manual: bool = False,
    ) -> str:
        """生成脚本。

        Args:
            recs: 推荐列表。
            include_manual: 是否包含需要手动执行的步骤（以注释形式）。

        Returns:
            PowerShell 脚本字符串。
        """
        lines: list[str] = []
        lines.append("# DiskAdvisor 生成的 PowerShell 脚本")
        lines.append("# 请逐段审阅后执行")
        lines.append("")
        lines.append('$ErrorActionPreference = "Stop"')
        lines.append("")

        for rec in recs:
            lines.append(f"# {'=' * 60}")
            lines.append(f"# {rec.title}")
            lines.append(f"# 优先级：{rec.priority.value} | 难度：{rec.difficulty.value} | 风险：{rec.risk.value}")
            if rec.reason:
                lines.append(f"# 原因：{rec.reason}")
            if rec.conflict:
                lines.append(f"# ⚠️ 冲突：{rec.conflict}")
                lines.append(f"# 跳过此推荐，请手动处理")
                lines.append("")
                continue
            lines.append(f"# {'=' * 60}")
            lines.append("")
            
            # 全部为手动步骤，且不包含手动步骤时，加说明
            all_manual = all(step.manual for step in rec.steps)
            if all_manual and not include_manual:
                lines.append("# 此推荐全部为手动步骤，请参考 diskadvisor recommend 输出")
                lines.append("")
                continue

            for step in rec.steps:
                prefix = f"# [{step.order}] "
                if step.manual:
                    if include_manual:
                        lines.append(f"{prefix}{step.description}（需手动执行）")
                        if step.warning:
                            lines.append(f"# ⚠️ {step.warning}")
                else:
                    if step.command:
                        lines.append(f"{prefix}{step.description}")
                        if step.warning:
                            lines.append(f"# ⚠️ {step.warning}")
                        lines.append(step.command)
                lines.append("")

        return "\n".join(lines)

    def generate_single(self, rec: Recommendation, include_manual: bool = False) -> str:
        """生成单条推荐脚本。"""
        return self.generate([rec], include_manual=include_manual)