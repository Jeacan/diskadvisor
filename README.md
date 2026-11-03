# DiskAdvisor

> Windows 磁盘空间规划顾问：扫描系统现状，结合软件知识库，告诉你「装哪里、数据放哪里、怎么配环境变量」，并生成可审阅的 PowerShell 脚本。

[![Tests](https://img.shields.io/badge/tests-45%20passed-brightgreen)]()
[![Coverage](https://img.shields.io/badge/coverage-69%25-yellowgreen)]()
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)]()
[![License](https://img.shields.io/badge/license-MIT-blue)]()

---

## 📖 目录

- [它解决什么问题](#-它解决什么问题)
- [它不是什么](#-它不是什么)
- [核心特性](#-核心特性)
- [快速开始](#-快速开始)
- [命令一览](#-命令一览)
- [典型工作流](#-典型工作流)
- [目录规划](#-目录规划)
- [安全原则](#-安全原则)
- [知识库](#-知识库)
- [开发](#-开发)
- [打包](#-打包)
- [项目结构](#-项目结构)
- [支持范围](#-支持范围)
- [后续规划](#-后续规划)
- [License](#-license)

---

## 🎯 它解决什么问题

- **C 盘越用越满**：Windows 默认把所有软件、数据、缓存都往 C 盘塞，新机几个月就满
- **决策成本高**：每装一个软件都要思考装哪、数据放哪、环境变量怎么配
- **迁移风险未知**：想迁移但不知道能不能迁、怎么迁、有什么坑
- **知识分散**：微信数据要改内置设置、Steam 库要加新位置、开发工具最好用 Scoop……这些知识散落在各处
- **重复劳动**：换新电脑时，所有规划都要重新来一遍

DiskAdvisor 把这些决策自动化：**扫描 → 分析 → 推荐 → 生成脚本**。

---

## 🚫 它不是什么

- ❌ 不是清理工具（不删缓存、不删临时文件）
- ❌ 不是空间分析工具（不是 WizTree / TreeSize）
- ❌ 不是搬家工具（不直接剪切数据）
- ❌ 不做病毒扫描
- ❌ 不做系统优化（不调注册表性能项）
- ❌ 不替代包管理器（而是集成 Scoop / winget）

**它是决策建议层**：诊断 + 推荐 + 可执行方案。

---

## ✨ 核心特性

| 特性           | 说明                                                                  |
| -------------- | --------------------------------------------------------------------- |
| **系统扫描**   | 磁盘、已装软件（注册表 + Scoop + winget）、环境变量、目录占用、大文件 |
| **智能分析**   | 磁盘压力分级、空间归因（哪个软件占了 C 盘）、错位软件识别             |
| **推荐引擎**   | 基于知识库 + 评分模型 + 冲突检测，按性价比排序                        |
| **脚本生成**   | 生成可审阅的 PowerShell 脚本，区分手动/自动步骤                       |
| **安全执行**   | 默认 dry-run，支持 interactive / auto 模式                            |
| **可回滚**     | 所有操作记录日志，支持按会话回滚                                      |
| **知识库驱动** | 20 个软件条目，覆盖社交、游戏、开发、办公、娱乐、系统                 |
| **Scoop 集成** | 优先推荐 Scoop，开发工具支持版本管理（scoop reset）                   |
| **配置管理**   | 导出/导入规划方案，换机器一键还原                                     |
| **新机初始化** | 一键生成 D 盘目录结构 + Scoop 配置脚本                                |
| **单文件分发** | PyInstaller 打包，零外部依赖，38 MB 一个 exe                          |

---

## 🚀 快速开始

### 方式一：下载 exe（推荐）

从 [Releases](../../releases) 下载 `diskadvisor.exe`，放到任意目录，直接运行：

```powershell
.\diskadvisor.exe --help
```

无需安装 Python。

### 方式二：源码安装

```powershell
git clone <repo>
cd diskadvisor
pip install -e ".[dev]"
```

需要 **Python 3.11+**、**Windows 10 1809+ / Windows 11**。

### 第一次运行

```powershell
# 诊断：扫描系统，生成报告
diskadvisor scan -o report/diagnosis.md

# 推荐：生成推荐列表和可执行脚本
diskadvisor recommend -o report/recommendations.md -s report/apply.ps1

# 咨询：单个软件该装哪
diskadvisor advise wechat
```

---

## 📋 命令一览

| 命令                 | 说明                   | 示例                                            |
| -------------------- | ---------------------- | ----------------------------------------------- |
| `scan`               | 扫描系统，生成诊断报告 | `diskadvisor scan -o report/diagnosis.md`       |
| `recommend`          | 生成推荐列表和脚本     | `diskadvisor recommend -s report/apply.ps1`     |
| `advise <软件>`      | 查询单个软件的安装建议 | `diskadvisor advise nodejs`                     |
| `apply <rec-id>`     | 执行推荐               | `diskadvisor apply config-scoop --mode dry-run` |
| `rollback <exec-id>` | 回滚执行会话           | `diskadvisor rollback 20261103-161852-1b5e4d`   |
| `journal`            | 查看执行日志           | `diskadvisor journal -n 10`                     |
| `kb-list`            | 列出知识库支持的软件   | `diskadvisor kb-list`                           |
| `kb-validate`        | 校验知识库             | `diskadvisor kb-validate`                       |
| `export`             | 导出规划方案           | `diskadvisor export -o plan.json`               |
| `import`             | 导入规划方案           | `diskadvisor import plan.json --show`           |
| `init`               | 新机初始化向导         | `diskadvisor init -o init-setup.ps1`            |

### 常用参数

| 参数                                | 说明                                           |
| ----------------------------------- | ---------------------------------------------- |
| `--no-deep`                         | 跳过目录占用和大文件扫描（速度快，推荐日常用） |
| `--top N`                           | 只显示前 N 条推荐                              |
| `--include-manual`                  | 脚本中包含手动步骤（以注释形式）               |
| `--mode dry-run\|interactive\|auto` | 执行模式                                       |
| `-v / --verbose`                    | 输出调试日志                                   |

---

## 🎬 典型工作流

### 场景 1：新机初始化

拿到新电脑，想一开始就把 D 盘规划好：

```powershell
# 1. 生成初始化脚本
diskadvisor init -o init-setup.ps1

# 2. 审阅脚本（重要！）
notepad init-setup.ps1

# 3. 执行
.\init-setup.ps1
```

脚本会：

- 创建 D 盘目录结构（Developer、SocialApps、Games 等）
- 配置 `SCOOP` / `SCOOP_GLOBAL` 环境变量到 D 盘
- 安装 Scoop
- 设置 Scoop 缓存目录到 D 盘

### 场景 2：C 盘告急

```powershell
# 1. 诊断
diskadvisor scan -o report/diagnosis.md

# 2. 生成推荐
diskadvisor recommend -o report/recommendations.md -s report/apply.ps1

# 3. 审阅推荐和脚本
notepad report/recommendations.md
notepad report/apply.ps1

# 4. 逐条执行（先 dry-run）
diskadvisor apply migrate-wechat --mode dry-run
diskadvisor apply migrate-wechat --mode auto
```

### 场景 3：装新软件前咨询

```powershell
diskadvisor advise docker
diskadvisor advise nodejs
diskadvisor advise steam
```

### 场景 4：出问题回滚

```powershell
# 查看执行记录
diskadvisor journal

# 回滚指定会话
diskadvisor rollback 20261103-161852-1b5e4d
```

### 场景 5：换机器还原规划

```powershell
# 旧机器导出
diskadvisor export -o my-plan.json

# 新机器导入
diskadvisor import my-plan.json
diskadvisor init -o init-setup.ps1
```

---

## 📁 目录规划

DiskAdvisor 默认推荐以下 D 盘规划（可通过 `export` / `import` 自定义）：

```text
D:\
├── Developer
│   ├── Scoop              # Scoop 用户级主目录
│   ├── ScoopGlobal        # Scoop 全局目录
│   ├── Env                # 开发环境（JDK、Node、MySQL 等）
│   ├── DevTools           # IDE、大型工具（IDEA、Docker 等）
│   └── Projects           # 代码项目
├── SocialApps             # 社交软件及数据（微信、QQ、钉钉）
├── Games                  # 游戏（SteamLibrary、EpicLibrary）
├── Entertainment          # 影音娱乐（浏览器数据、Spotify）
├── Office                 # 办公软件及文档
├── GreenSoft              # 免安装绿色软件
└── SystemTools            # 系统工具（7-Zip、Everything、PowerToys）
```

**设计原则**：

- 按**用途**分类，不按字母或数字
- 目录名用英文，兼容性更好
- 程序与数据分离（如 `SocialApps\WeChat` 和 `SocialApps\WeChatData`）
- 开发工具统一由 Scoop 管理

---

## 🔒 安全原则

DiskAdvisor 的设计核心是 **「不伤害用户」**：

1. **只读优先**：默认 `dry-run`，不修改系统
2. **可逆**：所有修改记录日志，支持一键回滚
3. **透明**：每一步操作、原因、风险都展示给用户
4. **不碰数据**：只调用软件官方迁移功能，绝不直接剪切文件夹
5. **知识库驱动**：所有推荐基于可验证的知识库，不是硬编码
6. **默认不自动**：`--mode auto` 需要显式开启，交互式确认

**绝对不能自动做的事**：

- 删除任何用户数据
- 直接剪切已安装软件的目录
- 修改注册表里软件的安装路径

**可以自动做的事**：

- 创建目录结构
- 设置用户环境变量
- 安装 Scoop
- 调用 `scoop install`
- 生成迁移脚本供用户审阅

---

## 📚 知识库

知识库位于 `src/diskadvisor/kb/entries/`，当前覆盖 **20 个软件**：

| 类别              | 软件                                                     |
| ----------------- | -------------------------------------------------------- |
| **dev**           | Docker Desktop、Git、JDK、MySQL、Node.js、Python、VSCode |
| **social**        | 钉钉、QQ、微信                                           |
| **game**          | Epic Games、Steam                                        |
| **office**        | Microsoft Office、WPS Office                             |
| **entertainment** | Chrome、Edge、Spotify                                    |
| **system**        | 7-Zip、Everything、PowerToys                             |

### 条目结构

```json
{
  "id": "wechat",
  "name": "微信",
  "aliases": ["WeChat", "Weixin"],
  "category": "social",
  "defaultInstallPaths": ["C:\\Program Files\\Tencent\\WeChat"],
  "defaultDataPaths": ["%USERPROFILE%\\Documents\\WeChat Files"],
  "recommendedInstallPath": "D:\\SocialApps\\WeChat",
  "recommendedDataPath": "D:\\SocialApps\\WeChatData",
  "installMethods": [{ "method": "manual", "command": null, "priority": 1 }],
  "migration": {
    "install": "reinstall",
    "data": "in-app-setting",
    "steps": [
      "打开微信 → 左下角三横线 → 设置",
      "文件管理 → 更改 → 选择 D:\\SocialApps\\WeChatData",
      "微信提示重启并迁移，确认"
    ],
    "risk": "low",
    "auto_migratable": false
  },
  "notes": "数据迁移必须通过微信内置功能，直接剪切文件夹会导致聊天记录丢失",
  "verifiedVersion": "3.9.x",
  "verifiedDate": "2024-01-15"
}
```

### 贡献新条目

1. 在 `src/diskadvisor/kb/entries/<category>/` 下新建 `<software-id>.json`
2. 参照已有条目填写，注意：
   - `id` 全局唯一
   - `recommendedInstallPath` 建议在 D 盘（系统软件除外）
   - `migration.steps` 必须是可验证的真实步骤
   - `verifiedVersion` / `verifiedDate` 标注验证环境
3. 运行 `diskadvisor kb-validate` 校验
4. 提交 PR，说明验证环境（Windows 版本、软件版本）

---

## 🛠️ 开发

### 环境准备

```powershell
git clone <repo>
cd diskadvisor
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

### 常用命令

```powershell
# 测试
pytest

# 测试 + 覆盖率
pytest --cov=diskadvisor --cov-report=html:report/coverage

# 代码检查
ruff check .
ruff format .

# 类型检查
mypy src/

# 校验知识库
diskadvisor kb-validate
```

### 添加新功能

项目结构按职责分层，新增功能通常需要：

1. **数据模型**：`core/models/` 或对应模块的 `models.py`
2. **核心逻辑**：`scanner/` / `analyzer/` / `recommender/` / `executor/`
3. **CLI 命令**：`cli/app.py`
4. **测试**：`tests/unit/` 或 `tests/integration/`

---

## 📦 打包

```powershell
.\scripts\build.ps1
```

打包脚本会：

1. 清理旧构建
2. 安装依赖 + PyInstaller
3. 运行全部测试（失败则中止）
4. 打包成 `dist/diskadvisor.exe`
5. 验证 exe 能运行

输出：`dist\diskadvisor.exe`（约 38 MB）

### 分发

- 直接分享 exe 文件
- 上传到 GitHub Releases
- 通过 Scoop bucket 分发（未来支持）

---

## 📂 项目结构

```text
diskadvisor/
├── src/diskadvisor/
│   ├── cli/                # 命令行入口
│   │   ├── app.py          # Typer 命令定义
│   │   └── init_wizard.py  # 新机初始化向导
│   ├── core/               # 核心模型和工具
│   │   ├── config/         # 配置 + 规划导入导出
│   │   ├── models/         # SystemSnapshot 等数据模型
│   │   └── utils/          # PowerShell、路径、日志
│   ├── scanner/            # 扫描器
│   │   ├── disk.py         # 磁盘
│   │   ├── software.py     # 已装软件
│   │   ├── env.py          # 环境变量
│   │   ├── dir_size.py     # 目录占用
│   │   └── big_file.py     # 大文件
│   ├── analyzer/           # 分析器
│   │   └── analyzer.py     # 压力、归因、错位识别
│   ├── kb/                 # 知识库
│   │   ├── entries/        # 软件条目（JSON）
│   │   ├── loader.py       # 加载器
│   │   └── validator.py    # 校验器
│   ├── recommender/        # 推荐引擎
│   │   ├── engine.py       # 主流程
│   │   ├── scorer.py       # 评分
│   │   └── conflict.py     # 冲突检测
│   ├── executor/           # 执行器
│   │   ├── executor.py     # 执行 + 回滚
│   │   ├── journal.py      # 执行日志
│   │   └── script_gen.py   # 脚本生成
│   └── reporter/           # 报告渲染
├── tests/
│   ├── unit/               # 单元测试
│   └── integration/        # 端到端测试
├── scripts/
│   └── build.ps1           # 打包脚本
├── pyproject.toml
├── README.md
└── LICENSE
```

---

## 💻 支持范围

| 项         | 要求                                              |
| ---------- | ------------------------------------------------- |
| 操作系统   | Windows 10 1809+ / Windows 11                     |
| Python     | 3.11+（源码运行）                                 |
| PowerShell | 5.1+（系统自带）                                  |
| 权限       | 大部分命令无需管理员；`SCOOP_GLOBAL` 配置需管理员 |

---

## 🗺️ 后续规划

### v0.2（计划中）

- [ ] 知识库扩充到 **50+ 软件**
- [ ] 扫描提速：`dir_size` 并行 + 缓存（当前约 2 分钟）
- [ ] 增强软件路径识别：用 `UninstallString`、`DisplayIcon` 推断未记录 `InstallLocation` 的软件

### v0.3（规划中）

- [ ] 定期体检模式（Windows 计划任务 + 通知）
- [ ] 远程知识库（从 GitHub 拉取最新条目，不用更新 exe）
- [ ] 与 Scoop / winget 深度集成（自动迁移可 Scoop 化的软件）

### v1.0（远期）

- [ ] GUI（Tauri 或 Web）
- [ ] 多语言（当前中文为主，抽 i18n）
- [ ] 跨机器配置同步

---

## 🤝 贡献

欢迎贡献知识库条目、代码、文档。

1. Fork 项目
2. 创建分支（`feature/xxx` 或 `fix/xxx`）
3. 编写代码 + 测试
4. 运行 `ruff check .`、`mypy src/`、`pytest`
5. 提交 PR

提交规范：

```
feat: 添加 Telegram 知识库条目
fix: 修复 Windows 10 下磁盘扫描的兼容性
docs: 更新 README 快速开始
test: 补充 Recommender 单元测试
```

---

## 📄 License

[MIT](LICENSE)

---

## 🙏 致谢

- [Scoop](https://scoop.sh/) — Windows 包管理器
- [Typer](https://typer.tiangolo.com/) — CLI 框架
- [Rich](https://rich.readthedocs.io/) — 终端渲染
- [Pydantic](https://docs.pydantic.dev/) — 数据校验
- [PyInstaller](https://pyinstaller.org/) — 打包工具
- [c-drive-cleaner-skill](https://github.com/dww911/c-drive-cleaner-skill) — 早期灵感

---

**DiskAdvisor** — 让你的 C 盘不再焦虑。
