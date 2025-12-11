"""
日志查看器界面
- 日志文件列表
- 日志内容显示
- 搜索过滤
- 导出功能
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QListWidget, QListWidgetItem, QTextEdit,
    QSplitter, QFrame, QFileDialog, QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from pathlib import Path
import logging

from core.logger import get_all_log_files, read_log_file


class LogViewer(QWidget):
    """日志查看器 - 可嵌入设置页面"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_log_content = ""
        self.setup_ui()
        self.load_log_files()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # 主内容区 - 分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setStyleSheet("QSplitter::handle { background: #334155; }")
        
        # 左侧 - 日志文件列表
        left_panel = QFrame()
        left_panel.setStyleSheet("background: rgba(30, 41, 59, 0.5); border-radius: 12px;")
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(12, 12, 12, 12)
        left_layout.setSpacing(8)
        
        list_title = QLabel("日志文件")
        list_title.setStyleSheet("color: #94a3b8; font-size: 12px; font-weight: 600;")
        left_layout.addWidget(list_title)
        
        self.file_list = QListWidget()
        self.file_list.setMinimumWidth(180)
        self.file_list.currentItemChanged.connect(self.on_file_selected)
        left_layout.addWidget(self.file_list)
        
        # 刷新按钮
        refresh_btn = QPushButton("🔄 刷新")
        refresh_btn.setObjectName("secondary_btn")
        refresh_btn.clicked.connect(self.load_log_files)
        left_layout.addWidget(refresh_btn)
        
        splitter.addWidget(left_panel)
        
        # 右侧 - 日志内容
        right_panel = QFrame()
        right_panel.setStyleSheet("background: rgba(30, 41, 59, 0.5); border-radius: 12px;")
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(12, 12, 12, 12)
        right_layout.setSpacing(8)
        
        # 搜索和操作栏
        toolbar = QHBoxLayout()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 搜索日志内容...")
        self.search_input.textChanged.connect(self.filter_log)
        toolbar.addWidget(self.search_input, 1)
        
        # 级别过滤
        self.level_buttons = {}
        for level, color in [("ERROR", "#ef4444"), ("WARNING", "#f59e0b"), ("INFO", "#22c55e"), ("DEBUG", "#64748b")]:
            btn = QPushButton(level)
            btn.setCheckable(True)
            btn.setChecked(True)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: rgba({self.hex_to_rgb(color)}, 0.2);
                    border: 1px solid {color};
                    color: {color};
                    padding: 4px 8px;
                    border-radius: 4px;
                    font-size: 11px;
                }}
                QPushButton:checked {{
                    background: {color};
                    color: white;
                }}
            """)
            btn.clicked.connect(self.filter_log)
            toolbar.addWidget(btn)
            self.level_buttons[level] = btn
        
        right_layout.addLayout(toolbar)
        
        # 日志内容显示
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 11))
        self.log_text.setStyleSheet("""
            QTextEdit {
                background: #0f172a;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 8px;
                color: #e2e8f0;
            }
        """)
        right_layout.addWidget(self.log_text, 1)
        
        # 底部操作
        bottom_bar = QHBoxLayout()
        
        self.status_label = QLabel("选择左侧日志文件查看")
        self.status_label.setStyleSheet("color: #64748b; font-size: 12px;")
        bottom_bar.addWidget(self.status_label)
        
        bottom_bar.addStretch()
        
        export_btn = QPushButton("📤 导出日志")
        export_btn.setObjectName("primary_btn")
        export_btn.clicked.connect(self.export_log)
        bottom_bar.addWidget(export_btn)
        
        right_layout.addLayout(bottom_bar)
        
        splitter.addWidget(right_panel)
        splitter.setSizes([200, 600])
        
        layout.addWidget(splitter, 1)
    
    def load_log_files(self):
        """加载日志文件列表"""
        self.file_list.clear()
        log_files = get_all_log_files()
        
        for log_file in log_files:
            item = QListWidgetItem(log_file.name)
            item.setData(Qt.ItemDataRole.UserRole, log_file)
            self.file_list.addItem(item)
        
        # 自动选择第一个(最新)
        if self.file_list.count() > 0:
            self.file_list.setCurrentRow(0)
        
        logging.info(f"加载了 {len(log_files)} 个日志文件")
    
    def on_file_selected(self, current: QListWidgetItem, previous: QListWidgetItem):
        """日志文件选择变化"""
        if current:
            file_path = current.data(Qt.ItemDataRole.UserRole)
            self.current_log_content = read_log_file(file_path)
            self.filter_log()
            self.status_label.setText(f"文件: {file_path.name}")
    
    def filter_log(self):
        """过滤日志内容"""
        if not self.current_log_content:
            return
        
        search_text = self.search_input.text().lower()
        active_levels = [level for level, btn in self.level_buttons.items() if btn.isChecked()]
        
        lines = self.current_log_content.split('\n')
        filtered_lines = []
        
        for line in lines:
            # 检查级别过滤
            level_match = any(f"[{level}]" in line for level in active_levels)
            if not level_match and line.strip():
                # 如果不是日志行(没有级别标记),检查是否是错误堆栈的一部分
                if filtered_lines and not line.startswith('['):
                    level_match = True
                else:
                    continue
            
            # 检查搜索过滤
            if search_text and search_text not in line.lower():
                continue
            
            filtered_lines.append(line)
        
        # 语法高亮
        highlighted = self.highlight_log('\n'.join(filtered_lines))
        self.log_text.setHtml(highlighted)
    
    def highlight_log(self, text: str) -> str:
        """日志语法高亮"""
        import html
        text = html.escape(text)
        
        # 替换颜色
        text = text.replace('[ERROR]', '<span style="color: #ef4444; font-weight: bold;">[ERROR]</span>')
        text = text.replace('[WARNING]', '<span style="color: #f59e0b; font-weight: bold;">[WARNING]</span>')
        text = text.replace('[INFO]', '<span style="color: #22c55e;">[INFO]</span>')
        text = text.replace('[DEBUG]', '<span style="color: #64748b;">[DEBUG]</span>')
        
        # 时间戳颜色
        import re
        text = re.sub(
            r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\]',
            r'<span style="color: #94a3b8;">[\1]</span>',
            text
        )
        
        return f'<pre style="margin: 0; font-family: Consolas, monospace;">{text}</pre>'
    
    def export_log(self):
        """导出日志文件"""
        if not self.current_log_content:
            QMessageBox.warning(self, "提示", "请先选择一个日志文件")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出日志", "log_export.txt", "文本文件 (*.txt)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.log_text.toPlainText())
                QMessageBox.information(self, "成功", f"日志已导出到:\n{file_path}")
                logging.info(f"日志已导出到: {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导出失败: {e}")
                logging.error(f"导出日志失败: {e}")
    
    @staticmethod
    def hex_to_rgb(hex_color: str) -> str:
        """十六进制颜色转RGB"""
        hex_color = hex_color.lstrip('#')
        r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        return f"{r}, {g}, {b}"

