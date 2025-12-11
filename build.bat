@echo off
chcp 65001 >nul
echo.
echo ╔══════════════════════════════════════════════╗
echo ║         奶酪云工具箱 - Windows 打包          ║
echo ╚══════════════════════════════════════════════╝
echo.

:: 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 未找到 Python，请先安装 Python 3.8+
    pause
    exit /b 1
)

:: 安装依赖
echo 📦 安装/更新依赖...
pip install -r requirements.txt
pip install pyinstaller

:: 执行打包
echo.
echo 🔨 开始打包...
python build_app.py --platform current

echo.
echo ✅ 打包完成！
echo 📁 输出目录: dist\
pause

