"""执行日志测试。"""

from pathlib import Path

from diskadvisor.executor.journal import Journal, JournalEntry, Operation, OperationType


def test_save_and_load(tmp_path: Path) -> None:
    journal = Journal(journal_dir=tmp_path)
    entry = JournalEntry(
        rec_id="test",
        rec_title="测试",
        operations=[
            Operation(
                type=OperationType.CREATE_DIR,
                description="创建目录",
                path="D:\\Test",
                success=True,
            )
        ],
    )
    journal.save(entry)

    loaded = journal.load(entry.exec_id)
    assert loaded is not None
    assert loaded.rec_id == "test"
    assert len(loaded.operations) == 1


def test_list_entries(tmp_path: Path) -> None:
    journal = Journal(journal_dir=tmp_path)
    for i in range(3):
        journal.save(JournalEntry(rec_id=f"r{i}", rec_title=f"测试{i}"))

    entries = journal.list_entries()
    assert len(entries) == 3


def test_mark_rolled_back(tmp_path: Path) -> None:
    journal = Journal(journal_dir=tmp_path)
    entry = JournalEntry(rec_id="test", rec_title="测试")
    journal.save(entry)

    journal.mark_rolled_back(entry.exec_id)
    loaded = journal.load(entry.exec_id)
    assert loaded.rolled_back is True