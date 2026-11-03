"""推荐报告渲染。"""

from __future__ import annotations

from diskadvisor.recommender.models import Priority, Recommendation


def priority_icon(p: Priority) -> str:
    return {
        Priority.CRITICAL: "🔴",
        Priority.HIGH: "🟠",
        Priority.MEDIUM: "🟡",
        Priority.LOW: "⚪",
    }.get(p, "⚪")


def render_recommendations(recs: list[Recommendation]) -> str:
    """渲染推荐列表为 Markdown。"""
    lines: list[str] = []
    lines.append("# DiskAdvisor 推荐操作")
    lines.append("")

    if not recs:
        lines.append("未发现需要处理的问题。")
        return "\n".join(lines)

    lines.append(f"共 {len(recs)} 条推荐，按性价比排序：")
    lines.append("")

    for i, rec in enumerate(recs, start=1):
        lines.append(f"## {i}. {priority_icon(rec.priority)} {rec.title}")
        lines.append("")
        lines.append(f"- **优先级**：{rec.priority.value}")
        lines.append(f"- **类别**：{rec.category.value}")
        lines.append(f"- **难度**：{rec.difficulty.value}")
        lines.append(f"- **风险**：{rec.risk.value}")
        lines.append(f"- **预计耗时**：{rec.estimated_minutes} 分钟")
        if rec.impact_gb > 0:
            lines.append(f"- **预计释放**：{rec.impact_gb:.1f} GB")
        if rec.reason:
            lines.append(f"- **原因**：{rec.reason}")
        if rec.conflict:
            lines.append(f"- **⚠️ 冲突**：{rec.conflict}")
        lines.append("")
        lines.append("**步骤**：")
        lines.append("")
        for step in rec.steps:
            marker = "（手动）" if step.manual else ""
            lines.append(f"{step.order}. {step.description}{marker}")
            if step.command:
                lines.append(f"   ```powershell")
                lines.append(f"   {step.command}")
                lines.append(f"   ```")
            if step.warning:
                lines.append(f"   > ⚠️ {step.warning}")
        lines.append("")

    return "\n".join(lines)