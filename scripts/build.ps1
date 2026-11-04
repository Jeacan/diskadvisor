# 构建 DiskAdvisor 单文件 exe
$ErrorActionPreference = "Stop"

Write-Host "=== DiskAdvisor 构建 ===" -ForegroundColor Cyan

# 1. 清理
Write-Host "清理旧构建..." -ForegroundColor Cyan
Remove-Item -Recurse -Force build, dist -ErrorAction SilentlyContinue
Get-ChildItem -Recurse -Filter "*.spec" | Remove-Item -Force -ErrorAction SilentlyContinue

# 2. 安装依赖
Write-Host "安装依赖..." -ForegroundColor Cyan
pip install -e ".[dev]"
pip install pyinstaller

# 3. 测试
Write-Host "运行测试..." -ForegroundColor Cyan
pytest
if ($LASTEXITCODE -ne 0) {
    Write-Host "测试失败，中止构建" -ForegroundColor Red
    exit 1
}

# 4. 打包
Write-Host "打包..." -ForegroundColor Cyan
python -m PyInstaller `
    --onefile `
    --name diskadvisor `
    --console `
    --collect-all typer `
    --collect-all rich `
    --collect-all pydantic `
    --collect-all pydantic_settings `
    --collect-all loguru `
    --collect-all fastapi `
    --collect-all uvicorn `
    --collect-all starlette `
    --hidden-import uvicorn.logging `
    --hidden-import uvicorn.loops.auto `
    --hidden-import uvicorn.loops.asyncio `
    --hidden-import uvicorn.protocols.http.auto `
    --hidden-import uvicorn.protocols.http.h11_impl `
    --hidden-import uvicorn.protocols.websockets.auto `
    --hidden-import uvicorn.lifespan.on `
    --add-data "src/diskadvisor/kb/entries;diskadvisor/kb/entries" `
    --add-data "src/diskadvisor/server/static;diskadvisor/server/static" `
    src/diskadvisor/__main__.py

if ($LASTEXITCODE -ne 0) {
    Write-Host "打包失败" -ForegroundColor Red
    exit 1
}

# 5. 验证
Write-Host "验证..." -ForegroundColor Cyan
& .\dist\diskadvisor.exe --version
if ($LASTEXITCODE -ne 0) {
    Write-Host "验证失败" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "=== 构建完成 ===" -ForegroundColor Green
Write-Host "输出：dist\diskadvisor.exe" -ForegroundColor Green
Write-Host "大小：$([math]::Round((Get-Item '.\dist\diskadvisor.exe').Length / 1MB, 2)) MB" -ForegroundColor Green
