# DiskAdvisor

> Windows 磁盘空间规划顾问：扫描系统现状，结合软件知识库，告诉你「装哪里、数据放哪里、怎么配环境变量」，并生成可审阅的 PowerShell 脚本。提供 CLI 和 Web UI 两种界面。

[![Tests](https://img.shields.io/badge/tests-60%2B%20passed-brightgreen)]()
[![Coverage](https://img.shields.io/badge/coverage-75%25-yellowgreen)]()
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)]()
[![License](https://img.shields.io/badge/license-MIT-blue)]()

---

## 📖 目录

- [它解决什么问题](#-它解决什么问题)
- [它不是什么](#-它不是什么)
- [核心特性](#-核心特性)
- [界面预览](#-界面预览)
- [快速开始](#-快速开始)
- [Web UI](#-web-ui)
- [CLI 命令](#-cli-命令)
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

DiskAdvisor 把这些决策自动化：**扫描 → 分析 → 推荐 → 生成脚本 → 安全执行**。

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

### 双界面

| 界面       | 适合                 | 启动方式              |
| ---------- | -------------------- | --------------------- |
| **Web UI** | 普通用户、可视化操作 | `diskadvisor ui`      |
| **CLI**    | 开发者、脚本自动化   | `diskadvisor scan` 等 |

### 功能矩阵

| 特性         | CLI | Web UI |
| ------------ | --- | ------ |
| 系统扫描     | ✅  | ✅     |
| 智能分析     | ✅  | ✅     |
| 推荐列表     | ✅  | ✅     |
| 脚本生成     | ✅  | ✅     |
| 安全执行     | ✅  | ✅     |
| 回滚         | ✅  | ✅     |
| 知识库管理   | ✅  | ✅     |
| 配置导入导出 | ✅  | ⬜     |
| 新机初始化   | ✅  | ⬜     |

### 性能

| 场景                    | 耗时      |
| ----------------------- | --------- |
| 首次扫描（快速模式）    | 约 15 秒  |
| 首次扫描（完整模式）    | 约 20 秒  |
| 第二次扫描（命中缓存）  | 约 0.0 秒 |
| 诊断 → 推荐（复用缓存） | 约 15 秒  |

### 安全

- 默认 `dry-run`，不修改系统
- 所有操作记录日志，支持一键回滚
- 不删除数据、不剪切目录、不改注册表路径
- 知识库驱动，无硬编码推荐

---

## 🖥️ 界面预览

### Web UI

```text
┌─────────────────────────────────────────────────────┐
│  💾 DiskAdvisor                          v1.1.0      │
│  Windows 磁盘空间规划顾问                             │
├─────────────────────────────────────────────────────┤
│  [诊断]  [推荐]  [咨询]  [执行日志]  [知识库]          │
├─────────────────────────────────────────────────────┤
│                                                      │
│  [开始扫描]  ☐ 快速模式  ☐ 强制刷新                   │
│                                                      │
│  ┌────────────────────────────────────────────────┐ │
│  │ 磁盘现状                                        │ │
│  │ 盘符  总容量  可用   使用率        状态          │ │
│  │ C:    150GB   65GB   ████████░░ 56%  🟢 充足    │ │
│  │ D:    326GB   264GB  ██░░░░░░░░ 19%  🟢 充足    │ │
│  └────────────────────────────────────────────────┘ │
│                                                      │
│  ┌────────────────────────────────────────────────┐ │
│  │ 环境变量问题                                    │ │
│  │ ⚠️ SCOOP 未设置，建议安装 Scoop 并配置到 D 盘   │ │
│  └────────────────────────────────────────────────┘ │
│                                                      │
│  ┌────────────────────────────────────────────────┐ │
│  │ 装在 C 盘的软件                                 │ │
│  │ 软件    当前位置              推荐位置          │ │
│  │ Git     C:\Program Files\Git  D:\Developer\...  │ │
│  └────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────┘
```

### 推荐页

```text
┌─────────────────────────────────────────────────────┐
│  共 7 条推荐                                         │
│                                                      │
│  ┃ 🔴 迁移 Docker Desktop 数据目录（36.3 GB）        │
│  ┃ 类别：migrate · 难度：medium · 风险：medium      │
│  ┃ 释放：36.3 GB · 10 分钟                          │
│  ┃ 原因：C:\Users\...\AppData 占用 36.3 GB          │
│  ┃ 1. Docker Desktop → Settings → Resources         │
│  ┃ 2. 修改 Disk image location 到 D:\...            │
│  ┃ [试运行] [执行]                                   │
│                                                      │
│  ┃ 🟠 迁移 Git 到 D 盘                               │
│  ┃ 类别：migrate · 难度：easy · 风险：low           │
│  ┃ 1. scoop install git                            │
│  ┃ [试运行] [执行]                                   │
└─────────────────────────────────────────────────────┘
```

---

## 🚀 快速开始

### 方式一：下载 exe（推荐）

从 [Releases](../../releases) 下载 `diskadvisor.exe`，放到任意目录：

```powershell
# 启动 Web UI
.\diskadvisor.exe ui

# 或使用 CLI
.\diskadvisor.exe scan --no-deep
```

无需安装 Python。

### 方式二：源码安装

```powershell
git clone <repo>
cd diskadvisor
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

需要 **Python 3.11+**、**Windows 10 1809+ / Windows 11**。

---

## 🖥️ Web UI

### 启动

```powershell
diskadvisor ui
```

浏览器自动打开 `http://127.0.0.1:8765`。

### 参数

```powershell
diskadvisor ui --port 9000        # 自定义端口
diskadvisor ui --host 0.0.0.0     # 监听所有网卡
diskadvisor ui --no-open          # 不自动打开浏览器
```

### 5 个标签页

| 标签         | 功能                                                        |
| ------------ | ----------------------------------------------------------- |
| **诊断**     | 一键扫描，磁盘使用率可视化，环境问题、错位软件、目录 Top N  |
| **推荐**     | 按优先级分色卡片，展示原因/影响/步骤/风险，支持试运行和执行 |
| **咨询**     | 输入软件名，查看安装路径、环境变量、版本管理、迁移步骤      |
| **执行日志** | 历史列表，一键回滚                                          |
| **知识库**   | 按类别分组、关键词搜索、校验结果                            |

### 使用技巧

- **快速模式**：勾选「快速模式」跳过目录和大文件扫描，约 15 秒
- **强制刷新**：忽略缓存重新扫描
- **缓存复用**：先诊断再推荐，推荐直接命中缓存，秒出
- **试运行**：执行前先 `dry-run`，确认操作无误再正式执行

---

## 📋 CLI 命令

| 命令                 | 说明                   | 示例                                            |
| -------------------- | ---------------------- | ----------------------------------------------- |
| `ui`                 | 启动 Web UI            | `diskadvisor ui --port 9000`                    |
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
| `--force-refresh`                   | 忽略缓存重新扫描                               |
| `--top N`                           | 只显示前 N 条推荐                              |
| `--include-manual`                  | 脚本中包含手动步骤（以注释形式）               |
| `--mode dry-run\|interactive\|auto` | 执行模式                                       |
| `-v / --verbose`                    | 输出调试日志                                   |

---

## 🎬 典型工作流

### 场景 1：新机初始化

```powershell
# 1. 生成初始化脚本
diskadvisor init -o init-setup.ps1

# 2. 审阅脚本（重要！）
notepad init-setup.ps1

# 3. 执行
.\init-setup.ps1
```

脚本会创建 D 盘目录结构、配置 `SCOOP` / `SCOOP_GLOBAL` 环境变量、安装 Scoop、设置缓存目录。

### 场景 2：C 盘告急（Web UI）

```powershell
diskadvisor ui
```

1. 点击「诊断」→「开始扫描」→ 查看磁盘使用率和目录占用
2. 切换到「推荐」→ 查看推荐列表
3. 对推荐项先点「试运行」，确认无误后点「执行」
4. 出问题在「执行日志」里一键回滚

### 场景 3：C 盘告急（CLI）

```powershell
# 1. 诊断
diskadvisor scan -o report/diagnosis.md

# 2. 生成推荐
diskadvisor recommend -o report/recommendations.md -s report/apply.ps1

# 3. 审阅
notepad report/recommendations.md
notepad report/apply.ps1

# 4. 逐条执行
diskadvisor apply migrate-wechat --mode dry-run
diskadvisor apply migrate-wechat --mode auto
```

### 场景 4：装新软件前咨询

```powershell
diskadvisor advise docker
diskadvisor advise nodejs
diskadvisor advise steam
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

# 启动开发服务器（热重载）
uvicorn diskadvisor.server.app:create_app --factory --reload --port 8765
```

### 添加新功能

项目结构按职责分层，新增功能通常需要：

1. **数据模型**：`core/models/` 或对应模块的 `models.py`
2. **核心逻辑**：`scanner/` / `analyzer/` / `recommender/` / `executor/`
3. **API**（如果 Web 需要）：`server/routes/`
4. **CLI 命令**：`cli/app.py`
5. **前端**（如果 Web 需要）：`server/static/`
6. **测试**：`tests/unit/` 或 `tests/integration/`

---

## 📦 打包

```powershell
.\scripts\build.ps1
```

打包脚本会：

1. 清理旧构建
2. 安装依赖 + PyInstaller
3. 运行全部测试（失败则中止）
4. 打包成 `dist/diskadvisor.exe`（含 Web UI 静态文件）
5. 验证 exe 能运行

输出：`dist\diskadvisor.exe`（约 40 MB）

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
│   ├── server/             # Web 服务器
│   │   ├── app.py          # FastAPI 应用
│   │   ├── cache.py        # 扫描结果缓存
│   │   ├── deps.py         # 共享依赖
│   │   ├── tasks.py        # 异步任务
│   │   ├── routes/         # API 路由
│   │   │   ├── scan.py
│   │   │   ├── recommend.py
│   │   │   ├── advise.py
│   │   │   ├── execute.py
│   │   │   ├── journal.py
│   │   │   └── kb.py
│   │   └── static/         # 前端资源
│   │       ├── index.html
│   │       ├── app.js
│   │       └── style.css
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
| 浏览器     | Chrome / Edge / Firefox 最新版（Web UI）          |
| 权限       | 大部分命令无需管理员；`SCOOP_GLOBAL` 配置需管理员 |

---

## 🗺️ 后续规划

### v1.2（计划中）

- [ ] 知识库扩充到 **50+ 软件**
- [ ] 远程知识库更新（从 GitHub 拉取，不用更新 exe）
- [ ] 增强软件路径识别（用 `UninstallString`、`DisplayIcon` 推断）

### v1.3（规划中）

- [ ] 定期体检模式（Windows 计划任务 + 通知）
- [ ] 与 Scoop / winget 深度集成（自动迁移可 Scoop 化的软件）
- [ ] Web UI 支持配置导入导出

### v2.0（远期）

- [ ] Tauri 桌面应用（原生体验，体积更小）
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
perf: 优化目录扫描速度
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
- [FastAPI](https://fastapi.tiangolo.com/) — Web 框架
- [Uvicorn](https://www.uvicorn.org/) — ASGI 服务器
- [PyInstaller](https://pyinstaller.org/) — 打包工具
- [c-drive-cleaner-skill](https://github.com/dww911/c-drive-cleaner-skill) — 早期灵感

---

**DiskAdvisor** — 让你的 C 盘不再焦虑。
