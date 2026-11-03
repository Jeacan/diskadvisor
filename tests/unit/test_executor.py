"""执行器测试。"""

from pathlib import Path

from diskadvisor.executor import ExecMode, Executor, Journal
from diskadvisor.recommender import RecCategory, Recommendation, Step


def test_dry_run_does_not_create_dir(tmp_path: Path) -> None:
    target = tmp_path / "should_not_exist"
    rec = Recommendation(
        id="test",
        category=RecCategory.CONFIG,
        title="测试",
        steps=[
            Step(
                order=1,
                description="创建目录",
                command=f'New-Item -ItemType Directory -Path "{target}" -Force',
            )
        ],
    )
    journal = Journal(journal_dir=tmp_path / "journal")
    executor = Executor(journal=journal)
    result = executor.execute(rec, mode=ExecMode.DRY_RUN)

    assert result.success
    assert not target.exists()


def test_apply_creates_dir(tmp_path: Path) -> None:
    target = tmp_path / "created"
    rec = Recommendation(
        id="test",
        category=RecCategory.CONFIG,
        title="测试",
        steps=[
            Step(
                order=1,
                description="创建目录",
                command=f'New-Item -ItemType Directory -Path "{target}" -Force',
            )
        ],
    )
    journal = Journal(journal_dir=tmp_path / "journal")
    executor = Executor(journal=journal)
    result = executor.execute(rec, mode=ExecMode.AUTO)

    assert result.success
    assert target.exists()


def test_rollback_removes_empty_dir(tmp_path: Path) -> None:
    target = tmp_path / "to_remove"
    rec = Recommendation(
        id="test",
        category=RecCategory.CONFIG,
        title="测试",
        steps=[
            Step(
                order=1,
                description="创建目录",
                command=f'New-Item -ItemType Directory -Path "{target}" -Force',
            )
        ],
    )
    journal = Journal(journal_dir=tmp_path / "journal")
    executor = Executor(journal=journal)
    result = executor.execute(rec, mode=ExecMode.AUTO)
    assert target.exists()

    executor.rollback(result.entry.exec_id)
    assert not target.exists()


def test_conflicted_rec_skipped(tmp_path: Path) -> None:
    rec = Recommendation(
        id="test",
        category=RecCategory.CONFIG,
        title="测试",
        conflict="路径冲突",
        steps=[Step(order=1, description="步骤", command="echo hi")],
    )
    journal = Journal(journal_dir=tmp_path / "journal")
    executor = Executor(journal=journal)
    result = executor.execute(rec, mode=ExecMode.AUTO)

    assert len(result.entry.operations) == 0