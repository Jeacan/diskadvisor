"""脚本生成器测试。"""

from diskadvisor.executor import ScriptGenerator
from diskadvisor.recommender import RecCategory, Recommendation, Step


def test_generate_script() -> None:
    rec = Recommendation(
        id="r1",
        category=RecCategory.ENV,
        title="配置 Scoop",
        steps=[
            Step(
                order=1,
                description="设置环境变量",
                command='[Environment]::SetEnvironmentVariable("SCOOP", "D:\\Scoop", "User")',
            )
        ],
    )
    gen = ScriptGenerator()
    script = gen.generate([rec])
    assert "# 配置 Scoop" in script
    assert "SetEnvironmentVariable" in script
    assert "$ErrorActionPreference" in script


def test_generate_skips_conflicted() -> None:
    rec = Recommendation(
        id="r1",
        category=RecCategory.ENV,
        title="冲突推荐",
        conflict="路径冲突",
        steps=[Step(order=1, description="步骤", command="echo hi")],
    )
    gen = ScriptGenerator()
    script = gen.generate([rec])
    assert "跳过此推荐" in script
    assert "echo hi" not in script