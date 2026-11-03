"""冲突检测测试。"""

from diskadvisor.recommender import RecCategory, Recommendation, Step
from diskadvisor.recommender.conflict import ConflictDetector


def test_detect_duplicate_paths() -> None:
    r1 = Recommendation(
        id="r1",
        category=RecCategory.INSTALL,
        title="r1",
        steps=[
            Step(
                order=1,
                description="创建目录",
                command='New-Item -ItemType Directory -Path "D:\\Test"',
            )
        ],
    )
    r2 = Recommendation(
        id="r2",
        category=RecCategory.INSTALL,
        title="r2",
        steps=[
            Step(
                order=1,
                description="创建目录",
                command='New-Item -ItemType Directory -Path "D:\\Test"',
            )
        ],
    )
    detector = ConflictDetector()
    result = detector.detect([r1, r2])
    assert all(r.conflict for r in result)