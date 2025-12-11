"""
奶酪云工具箱 - 主入口
Cheese Cloud Tools - Main Entry
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont

from core.logger import setup_logging
from core.error_handler import ErrorHandler
from ui.main_window import MainWindow


def load_stylesheet() -> str:
    """加载样式表"""
    style_path = PROJECT_ROOT / "resources" / "style.qss"
    if style_path.exists():
        with open(style_path, "r", encoding="utf-8") as f:
            return f.read()
    return ""


def main():
    """主函数"""
    # 初始化日志
    setup_logging()
    
    # 创建应用
    app = QApplication(sys.argv)
    app.setApplicationName("奶酪云工具箱")
    app.setApplicationVersion("1.0.0")
    
    # 设置默认字体
    font = QFont("Microsoft YaHei", 10)
    app.setFont(font)
    
    # 初始化全局错误处理
    error_handler = ErrorHandler(app)
    
    # 加载样式表
    stylesheet = load_stylesheet()
    if stylesheet:
        app.setStyleSheet(stylesheet)
    
    # 创建主窗口
    window = MainWindow()
    window.show()
    
    # 运行应用
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

