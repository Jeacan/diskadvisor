"""Markdown 报告生成器。"""

from __future__ import annotations

from diskadvisor.analyzer.models import AnalysisResult, PressureLevel
from diskadvisor.core.models import SystemSnapshot


def format_gb(value: float) -> str:
    """格式化 GB 数值。"""
    if value >= 1024:
        return f"{value / 1024:.2f} TB"
    return f"{value:.2f} GB"


def status_icon(used_percent: float) -> str:
    """根据使用率返回状态图标。"""
    if used_percent >= 90:
        return "🔴 紧张"
    if used_percent >= 75:
        return "🟡 注意"
    return "🟢 充足"


def pressure_icon(level: PressureLevel) -> str:
    """压力等级图标。"""
    if level == PressureLevel.CRITICAL:
        return "🔴"
    if level == PressureLevel.WARNING:
        return "🟡"
    return "🟢"


def render_diagnosis(snapshot: SystemSnapshot, analysis: AnalysisResult | None = None) -> str:
    """生成诊断报告。

    Args:
        snapshot: 系统快照。
        analysis: 分析结果（可选）。

    Returns:
        Markdown 格式报告。
    """
    lines: list[str] = []

    lines.append("# DiskAdvisor 诊断报告")
    lines.append("")
    lines.append(f"生成时间：{snapshot.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"计算机名：{snapshot.computer_name or '未知'}")
    lines.append(f"系统版本：{snapshot.os_version or '未知'}")
    lines.append(f"管理员权限：{'是' if snapshot.is_admin else '否'}")
    lines.append("")

    # 磁盘
    lines.append("## 磁盘现状")
    lines.append("")
    if snapshot.disks:
        lines.append("| 盘符 | 卷标 | 总容量 | 可用 | 使用率 | 类型 | 系统盘 | 状态 |")
        lines.append("|---|---|---|---|---|---|---|---|")
        for disk in snapshot.disks:
            lines.append(
                f"| {disk.letter} | {disk.label or '-'} | "
                f"{format_gb(disk.total_gb)} | {format_gb(disk.free_gb)} | "
                f"{disk.used_percent:.1f}% | {disk.disk_type.value} | "
                f"{'是' if disk.is_system else '否'} | {status_icon(disk.used_percent)} |"
            )
    else:
        lines.append("未采集到磁盘信息。")
    lines.append("")

    # 磁盘压力
    if analysis and analysis.disk_pressures:
        lines.append("## 磁盘压力")
        lines.append("")
        for p in analysis.disk_pressures:
            lines.append(f"- {pressure_icon(p.level)} **{p.letter} 盘**：{p.message}")
        lines.append("")

    # 目录占用
    if snapshot.top_dirs:
        lines.append("## 目录占用 Top N")
        lines.append("")
        lines.append("| 路径 | 大小 | 文件数 | 归属 | 类别 |")
        lines.append("|---|---|---|---|---|")
        attr_map = {a.path: a for a in (analysis.attributions if analysis else [])}
        for d in snapshot.top_dirs:
            attr = attr_map.get(d.path)
            owner = attr.software_name if attr and attr.software_name else "-"
            category = attr.category if attr and attr.category != "unknown" else "-"
            lines.append(
                f"| `{d.path}` | {format_gb(d.size_gb)} | {d.file_count} | {owner} | {category} |"
            )
        lines.append("")

    # 大文件
    if snapshot.big_files:
        lines.append("## 大文件")
        lines.append("")
        lines.append("| 路径 | 大小 |")
        lines.append("|---|---|")
        for f in snapshot.big_files:
            lines.append(f"| `{f.path}` | {format_gb(f.size_gb)} |")
        lines.append("")

    # 位置不正确的软件
    if analysis and analysis.misplaced:
        lines.append("## 装在 C 盘的软件")
        lines.append("")
        lines.append("| 软件 | 当前位置 | 推荐位置 |")
        lines.append("|---|---|---|")
        for m in analysis.misplaced:
            lines.append(
                f"| {m.software_name} | `{m.current_path}` | `{m.recommended_path}` |"
            )
        lines.append("")

    # 环境变量问题
    if analysis and analysis.env_issues:
        lines.append("## 环境变量问题")
        lines.append("")
        for issue in analysis.env_issues:
            lines.append(f"- ⚠️ {issue}")
        lines.append("")

    # 已装软件统计
    lines.append("## 已安装软件")
    lines.append("")
    if snapshot.installed:
        by_source: dict[str, int] = {}
        for sw in snapshot.installed:
            by_source[sw.source.value] = by_source.get(sw.source.value, 0) + 1
        lines.append(f"共检测到 {len(snapshot.installed)} 个软件：")
        lines.append("")
        for source, count in sorted(by_source.items()):
            lines.append(f"- {source}: {count}")
    else:
        lines.append("未采集到已安装软件。")
    lines.append("")

    # 环境变量关键项
    lines.append("## 关键环境变量")
    lines.append("")
    key_vars = ["SCOOP", "SCOOP_GLOBAL", "JAVA_HOME", "NODE_PATH", "PATH"]
    env_map = {ev.name: ev.value for ev in snapshot.env_vars}
    for name in key_vars:
        value = env_map.get(name)
        if value:
            display = value if len(value) <= 120 else value[:120] + "..."
            lines.append(f"- **{name}** = `{display}`")
        else:
            lines.append(f"- **{name}** = 未设置")
    lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("*由 DiskAdvisor v0.1 生成*")

    return "\n".join(lines)