#!/bin/bash

echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║       奶酪云工具箱 - macOS/Linux 打包        ║"
echo "╚══════════════════════════════════════════════╝"
echo ""

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 未找到 Python3，请先安装"
    exit 1
fi

# 安装依赖
echo "📦 安装/更新依赖..."
pip3 install -r requirements.txt
pip3 install pyinstaller

# 执行打包
echo ""
echo "🔨 开始打包..."
python3 build_app.py --platform current

echo ""
echo "✅ 打包完成！"
echo "📁 输出目录: dist/"

