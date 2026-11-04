"""DiskAdvisor CLI。"""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel

from diskadvisor import __version__
from diskadvisor.analyzer import Analyzer
from diskadvisor.core.config import Settings
from diskadvisor.core.models import SystemSnapshot
from diskadvisor.core.utils import setup_logging
from diskadvisor.executor import ScriptGenerator
from diskadvisor.recommender import Recommender
from diskadvisor.reporter import render_diagnosis, render_recommendations
from diskadvisor.scanner import (
    BigFileScanner,
    DirSizeScanner,
    DiskScanner,
    EnvScanner,
    SoftwareScanner,
)

app = typer.Typer(
    name="diskadvisor",
    help="Windows 磁盘空间规划顾问",
    no_args_is_help=True,
)

console = Console()


def _version_callback(value: bool) -> None:
    if value:
        console.print(f"DiskAdvisor v{__version__}")
        raise typer.Exit()


@app.callback()
def main_callback(
    version: bool = typer.Option(
        False,
        "--version",
        "-V",
        callback=_version_callback,
        is_eager=True,
        help="显示版本号",
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="输出调试日志"),
) -> None:
    """DiskAdvisor 命令行入口。"""
    setup_logging(verbose=verbose)


def _collect_snapshot(settings: Settings, no_deep: bool = False) -> SystemSnapshot:
    """采集系统快照。"""
    import os
    import platform

    snapshot = SystemSnapshot(
        os_version=platform.platform(),
        os_build=platform.version(),
        user_profile=os.environ.get("USERPROFILE", ""),
        computer_name=platform.node(),
        is_admin=_is_admin(),
    )

    scanners: list = [
        DiskScanner(),
        EnvScanner(),
        SoftwareScanner(),
    ]

    if not no_deep:
        scanners.append(DirSizeScanner(top_n=settings.top_dir_count))
        scanners.append(BigFileScanner(threshold_gb=settings.big_file_threshold_gb))

    for scanner in scanners:
        scanner.run(snapshot)

    return snapshot


def _is_admin() -> bool:
    """判断是否以管理员身份运行。"""
    import ctypes

    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())  # type: ignore[attr-defined]
    except Exception:
        return False


@app.command()
def scan(
    output: Path = typer.Option(None, "--output", "-o", help="输出报告文件路径（Markdown）"),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="不打印报告到终端"),
    no_deep: bool = typer.Option(False, "--no-deep", help="跳过目录占用和大文件扫描"),
) -> None:
    """扫描系统并生成诊断报告。"""
    console.print(Panel.fit("[bold cyan]DiskAdvisor 诊断[/bold cyan]", border_style="cyan"))

    settings = Settings()
    snapshot = _collect_snapshot(settings, no_deep=no_deep)

    console.print("[dim]分析中...[/dim]")
    analyzer = Analyzer()
    analysis = analyzer.analyze(snapshot)

    report = render_diagnosis(snapshot, analysis)

    if not quiet:
        console.print(report)

    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(report, encoding="utf-8-sig")
        console.print(f"\n[green]报告已保存：{output}[/green]")


@app.command()
def recommend(
    output: Path = typer.Option(None, "--output", "-o", help="输出推荐报告（Markdown）"),
    script: Path = typer.Option(None, "--script", "-s", help="输出 PowerShell 脚本"),
    top: int = typer.Option(10, "--top", "-t", help="只显示前 N 条推荐"),
    include_manual: bool = typer.Option(False, "--include-manual", help="脚本中包含手动步骤（注释）"),
    no_deep: bool = typer.Option(False, "--no-deep", help="跳过深度扫描"),
) -> None:
    """生成推荐操作列表。"""
    console.print(Panel.fit("[bold cyan]DiskAdvisor 推荐[/bold cyan]", border_style="cyan"))

    settings = Settings()
    snapshot = _collect_snapshot(settings, no_deep=no_deep)

    console.print("[dim]分析中...[/dim]")
    analyzer = Analyzer()
    analysis = analyzer.analyze(snapshot)

    console.print("[dim]生成推荐中...[/dim]")
    recommender = Recommender()
    recs = recommender.recommend(snapshot, analysis)

    if top > 0:
        recs = recs[:top]

    report = render_recommendations(recs)
    console.print(report)

    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(report, encoding="utf-8-sig")
        console.print(f"\n[green]推荐报告已保存：{output}[/green]")

    if script:
        gen = ScriptGenerator()
        script_text = gen.generate(recs, include_manual=include_manual)
        script.parent.mkdir(parents=True, exist_ok=True)
        script.write_text(script_text, encoding="utf-8-sig")
        console.print("[dim]提示：脚本默认不包含手动步骤，加 --include-manual 可包含（以注释形式）[/dim]")
        console.print(f"[green]脚本已保存：{script}[/green]")


@app.command()
def advise(
    software: str = typer.Argument(..., help="软件名或 ID，例如 wechat、nodejs"),
) -> None:
    """查询单个软件的安装建议。"""
    recommender = Recommender()
    advice = recommender.advise_software(software)

    if not advice:
        console.print(f"[red]知识库中未找到：{software}[/red]")
        console.print("[dim]可用 diskadvisor kb list 查看支持的软件[/dim]")
        raise typer.Exit(code=1)

    lines: list[str] = []
    lines.append(f"# {advice.software_name} 安装建议")
    lines.append("")
    lines.append(f"- **推荐安装路径**：`{advice.recommended_install_path}`")
    if advice.recommended_data_path:
        lines.append(f"- **推荐数据路径**：`{advice.recommended_data_path}`")
    if advice.install_method:
        lines.append(f"- **安装方式**：{advice.install_method}")
    if advice.install_command:
        lines.append(f"- **安装命令**：`{advice.install_command}`")
    lines.append("")

    if advice.env_vars:
        lines.append("**环境变量**：")
        lines.append("")
        for ev in advice.env_vars:
            lines.append(f"- `{ev['name']}` = `{ev['value']}`（{ev['scope']}）")
        lines.append("")

    if advice.version_management:
        vm = advice.version_management
        lines.append("**版本管理**：")
        lines.append("")
        lines.append(f"- 工具：{vm['tool']}")
        lines.append(f"- 方法：{vm['method']}")
        if vm.get("commands"):
            lines.append("- 命令：")
            for cmd in vm["commands"]:
                lines.append(f"  - `{cmd}`")
        lines.append("")

    if advice.migration_steps:
        lines.append("**迁移步骤**：")
        lines.append("")
        for i, s in enumerate(advice.migration_steps, start=1):
            lines.append(f"{i}. {s}")
        lines.append("")

    if advice.notes:
        lines.append(f"> {advice.notes}")
        lines.append("")

    console.print("\n".join(lines))


@app.command("kb-list")
def kb_list() -> None:
    """列出知识库中所有软件。"""
    from diskadvisor.kb import KnowledgeBase

    kb = KnowledgeBase()
    entries = kb.all()

    lines: list[str] = []
    lines.append(f"知识库共 {len(entries)} 个软件：")
    lines.append("")
    by_cat: dict[str, list] = {}
    for e in entries:
        by_cat.setdefault(e.category.value, []).append(e)

    for cat, items in sorted(by_cat.items()):
        lines.append(f"## {cat}")
        lines.append("")
        for e in sorted(items, key=lambda x: x.id):
            lines.append(f"- `{e.id}` — {e.name}")
        lines.append("")

    console.print("\n".join(lines))
    
@app.command()
def apply(
    rec_id: str = typer.Argument(..., help="推荐 ID，例如 migrate-wechat"),
    mode: str = typer.Option("dry-run", "--mode", "-m", help="dry-run | interactive | auto"),
    yes: bool = typer.Option(False, "--yes", "-y", help="跳过确认（auto 模式）"),
) -> None:
    """执行指定推荐。"""
    from diskadvisor.analyzer import Analyzer
    from diskadvisor.executor import ExecMode, Executor

    settings = Settings()
    snapshot = _collect_snapshot(settings, no_deep=False)
    analysis = Analyzer().analyze(snapshot)
    recs = Recommender().recommend(snapshot, analysis)

    target = next((r for r in recs if r.id == rec_id), None)
    if not target:
        console.print(f"[red]未找到推荐：{rec_id}[/red]")
        console.print("[dim]可用 diskadvisor recommend 查看推荐 ID[/dim]")
        raise typer.Exit(code=1)

    console.print(f"[bold]准备执行：{target.title}[/bold]")
    for step in target.steps:
        console.print(f"  {step.order}. {step.description}")
        if step.command:
            console.print(f"     [dim]{step.command}[/dim]")
    console.print("")

    try:
        exec_mode = ExecMode(mode)
    except ValueError:
        console.print(f"[red]无效模式：{mode}[/red]")
        raise typer.Exit(code=1)

    if exec_mode == ExecMode.AUTO and not yes:
        confirm = typer.confirm("确认自动执行？")
        if not confirm:
            console.print("[yellow]已取消[/yellow]")
            raise typer.Exit()

    executor = Executor()
    result = executor.execute(target, mode=exec_mode)

    console.print("")
    if result.success:
        console.print(f"[green]执行完成：{result.entry.exec_id}[/green]")
    else:
        console.print(f"[red]部分失败：{result.entry.exec_id}[/red]")
        for op in result.failed_ops:
            console.print(f"  [red]✗[/red] {op.description}: {op.error}")

    console.print(f"[dim]回滚命令：diskadvisor rollback {result.entry.exec_id}[/dim]")


@app.command()
def rollback(
    exec_id: str = typer.Argument(..., help="执行 ID"),
) -> None:
    """回滚指定执行会话。"""
    from diskadvisor.executor import Executor

    executor = Executor()
    try:
        result = executor.rollback(exec_id)
    except ValueError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(code=1)

    console.print(f"[green]回滚完成：{exec_id}[/green]")
    for op in result.entry.operations:
        if op.rollback != "none":
            console.print(f"  [dim]{op.description}[/dim]")


@app.command()
def journal(
    limit: int = typer.Option(10, "--limit", "-n", help="显示条数"),
) -> None:
    """查看执行日志。"""
    from diskadvisor.executor import Journal

    j = Journal()
    entries = j.list_entries()[:limit]

    if not entries:
        console.print("[dim]暂无执行记录[/dim]")
        return

    lines: list[str] = []
    lines.append(f"最近 {len(entries)} 条执行记录：")
    lines.append("")
    for e in entries:
        status = "已回滚" if e.rolled_back else ("成功" if all(op.success for op in e.operations) else "部分失败")
        lines.append(f"- `{e.exec_id}` {e.rec_title} [{status}] {e.timestamp.strftime('%Y-%m-%d %H:%M')}")

    console.print("\n".join(lines))

@app.command("kb-validate")
def kb_validate() -> None:
    """校验知识库。"""
    from diskadvisor.kb.validator import KBValidator

    validator = KBValidator()
    issues = validator.validate()

    if not issues:
        console.print("[green]知识库校验通过，无问题[/green]")
        return

    errors = [i for i in issues if i.level == "error"]
    warnings = [i for i in issues if i.level == "warning"]

    for issue in issues:
        color = "red" if issue.level == "error" else "yellow"
        console.print(f"[{color}]{issue}[/{color}]")

    console.print("")
    console.print(f"共 {len(errors)} 个错误，{len(warnings)} 个警告")

    if errors:
        raise typer.Exit(code=1)

@app.command("export")
def export_plan(
    output: Path = typer.Option(
        Path("diskadvisor-plan.json"),
        "--output",
        "-o",
        help="输出文件路径",
    ),
) -> None:
    """导出当前规划配置。"""
    from diskadvisor.core.config.plan import PlanManager

    settings = Settings()
    manager = PlanManager()
    manager.export(settings, output)
    console.print(f"[green]规划已导出：{output}[/green]")


@app.command("import")
def import_plan(
    input_path: Path = typer.Argument(..., help="规划文件路径"),
    show: bool = typer.Option(False, "--show", help="只显示不保存"),
) -> None:
    """导入规划配置。"""
    from diskadvisor.core.config.plan import PlanManager

    manager = PlanManager()
    try:
        settings = manager.import_plan(input_path)
    except FileNotFoundError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(code=1)

    lines: list[str] = ["导入的规划：", ""]
    for key, value in settings.model_dump().items():
        lines.append(f"- `{key}` = `{value}`")
    console.print("\n".join(lines))

    if not show:
        console.print("")
        console.print("[yellow]提示：当前版本仅展示，不会自动修改系统[/yellow]")

@app.command()
def init(
    output: Path = typer.Option(
        Path("init-setup.ps1"),
        "--output",
        "-o",
        help="输出初始化脚本路径",
    ),
    show: bool = typer.Option(False, "--show", help="只显示不保存"),
    execute: bool = typer.Option(False, "--execute", help="直接执行（需管理员）"),
) -> None:
    """新机初始化向导。"""
    from diskadvisor.cli.init_wizard import InitWizard

    wizard = InitWizard()
    script = wizard.generate_setup_script()

    console.print("[bold cyan]新机初始化脚本[/bold cyan]")
    console.print("")
    console.print(script)

    if show:
        return

    wizard.save_script(output)
    console.print("")
    console.print(f"[green]脚本已保存：{output}[/green]")
    console.print("[dim]请审阅后执行：.\\init-setup.ps1[/dim]")

    if execute:
        import subprocess

        console.print("")
        confirm = typer.confirm("确认执行初始化脚本？")
        if confirm:
            subprocess.run(
                ["powershell.exe", "-ExecutionPolicy", "Bypass", "-File", str(output)],
                check=False,
            )
    
@app.command()
def ui(
    host: str = typer.Option("127.0.0.1", "--host", help="监听地址"),
    port: int = typer.Option(8765, "--port", "-p", help="监听端口"),
    no_open: bool = typer.Option(False, "--no-open", help="不自动打开浏览器"),
) -> None:
    """启动 Web UI。"""
    import threading
    import time
    import webbrowser

    import uvicorn

    from diskadvisor.server import create_app

    app_instance = create_app()
    url = f"http://{host}:{port}"

    console.print(f"[bold cyan]DiskAdvisor UI[/bold cyan]")
    console.print(f"地址：{url}")
    console.print("[dim]按 Ctrl+C 停止[/dim]")
    console.print("")

    if not no_open:
        def _open_browser() -> None:
            time.sleep(1.5)
            webbrowser.open(url)

        threading.Thread(target=_open_browser, daemon=True).start()

    uvicorn.run(app_instance, host=host, port=port, log_level="warning")
    
def main() -> None:
    """CLI 入口（供 pyproject.toml 的 console_scripts 调用）。"""
    app()


if __name__ == "__main__":
    main()