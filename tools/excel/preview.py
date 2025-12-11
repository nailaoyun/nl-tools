"""
Excel预览工具
- 读取.xlsx/.xls文件
- QTableWidget显示表格数据
- 多Sheet标签页切换
"""
import logging
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QFileDialog, QMessageBox, QTableWidget, QTableWidgetItem,
    QTabWidget, QHeaderView, QAbstractItemView
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont, QColor

from ui.workspace import BaseWorkspace, UploadArea

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False
    logging.warning("pandas未安装, Excel预览功能不可用")

try:
    import openpyxl
    HAS_OPENPYXL = True
except ImportError:
    HAS_OPENPYXL = False
    logging.warning("openpyxl未安装, Excel预览功能不可用")


class ExcelLoadWorker(QThread):
    """Excel加载线程"""
    finished = Signal(dict)  # {sheet_name: DataFrame}
    error = Signal(str)
    
    def __init__(self, file_path: str):
        super().__init__()
        self.file_path = file_path
    
    def run(self):
        try:
            # 使用pandas读取所有sheet
            excel_file = pd.ExcelFile(self.file_path)
            sheets_data = {}
            
            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(excel_file, sheet_name=sheet_name)
                sheets_data[sheet_name] = df
            
            self.finished.emit(sheets_data)
            
        except Exception as e:
            logging.error(f"加载Excel失败: {e}")
            self.error.emit(str(e))


class SheetTable(QTableWidget):
    """Sheet表格组件"""
    
    def __init__(self, df: 'pd.DataFrame', parent=None):
        super().__init__(parent)
        self.setup_table(df)
    
    def setup_table(self, df: 'pd.DataFrame'):
        """设置表格数据"""
        # 设置行列数
        self.setRowCount(len(df))
        self.setColumnCount(len(df.columns))
        
        # 设置表头
        headers = [str(col) for col in df.columns]
        self.setHorizontalHeaderLabels(headers)
        
        # 填充数据
        for row_idx, (_, row) in enumerate(df.iterrows()):
            for col_idx, value in enumerate(row):
                item = QTableWidgetItem(str(value) if pd.notna(value) else "")
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)  # 只读
                self.setItem(row_idx, col_idx, item)
        
        # 设置样式
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.horizontalHeader().setStretchLastSection(True)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.verticalHeader().setDefaultSectionSize(35)
        
        # 自动调整列宽
        self.resizeColumnsToContents()
        
        # 限制最大列宽
        for col in range(self.columnCount()):
            if self.columnWidth(col) > 300:
                self.setColumnWidth(col, 300)


class ExcelPreviewPage(BaseWorkspace):
    """Excel预览页面"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.excel_path = None
        self.sheets_data = {}
        self.setup_preview_ui()
    
    def setup_preview_ui(self):
        """设置预览UI"""
        self.history_btn.hide()
        
        # 上传区域
        self.upload_area = UploadArea("Excel文件 (*.xlsx *.xls)")
        self.upload_area.files_dropped.connect(self.on_file_added)
        self.content_layout.addWidget(self.upload_area)
        
        # 预览区域
        self.preview_frame = QFrame()
        self.preview_frame.setObjectName("card")
        self.preview_frame.setVisible(False)
        preview_layout = QVBoxLayout(self.preview_frame)
        preview_layout.setContentsMargins(0, 0, 0, 0)
        preview_layout.setSpacing(0)
        
        # 工具栏
        toolbar = QWidget()
        toolbar.setStyleSheet("background: rgba(15, 23, 42, 0.5); border-bottom: 1px solid #334155;")
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(16, 12, 16, 12)
        
        # 文件信息
        self.file_label = QLabel("")
        self.file_label.setStyleSheet("color: white; font-weight: 500;")
        toolbar_layout.addWidget(self.file_label)
        
        toolbar_layout.addStretch()
        
        # 统计信息
        self.stats_label = QLabel("")
        self.stats_label.setStyleSheet("color: #64748b; font-size: 12px;")
        toolbar_layout.addWidget(self.stats_label)
        
        # 重新选择按钮
        change_btn = QPushButton("📂 更换文件")
        change_btn.setObjectName("secondary_btn")
        change_btn.clicked.connect(self.change_file)
        toolbar_layout.addWidget(change_btn)
        
        preview_layout.addWidget(toolbar)
        
        # Sheet标签页
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: none;
                background: transparent;
            }
            QTabBar::tab {
                background: #1e293b;
                color: #94a3b8;
                padding: 10px 20px;
                border: none;
                border-bottom: 2px solid transparent;
            }
            QTabBar::tab:hover {
                color: #e2e8f0;
            }
            QTabBar::tab:selected {
                color: #fbbf24;
                border-bottom: 2px solid #fbbf24;
            }
        """)
        preview_layout.addWidget(self.tab_widget, 1)
        
        self.content_layout.addWidget(self.preview_frame, 1)
    
    def on_file_added(self, files: list):
        """文件添加"""
        if not files:
            return
        
        excel_file = None
        for f in files:
            if f.lower().endswith(('.xlsx', '.xls')):
                excel_file = f
                break
        
        if not excel_file:
            QMessageBox.warning(self, "提示", "请选择Excel文件")
            return
        
        self.load_excel(excel_file)
    
    def load_excel(self, file_path: str):
        """加载Excel文件"""
        if not HAS_PANDAS or not HAS_OPENPYXL:
            QMessageBox.critical(self, "错误", "pandas或openpyxl未安装,无法预览Excel文件")
            return
        
        self.excel_path = file_path
        self.file_label.setText(f"📊 {Path(file_path).name}")
        
        # 清空现有标签页
        self.tab_widget.clear()
        self.sheets_data.clear()
        
        # 启动加载线程
        self.worker = ExcelLoadWorker(file_path)
        self.worker.finished.connect(self.on_load_finished)
        self.worker.error.connect(self.on_load_error)
        self.worker.start()
        
        logging.info(f"开始加载Excel: {file_path}")
    
    def on_load_finished(self, sheets_data: dict):
        """加载完成"""
        self.sheets_data = sheets_data
        self.preview_frame.setVisible(True)
        self.upload_area.setVisible(False)
        
        total_rows = 0
        total_cols = 0
        
        # 创建标签页
        for sheet_name, df in sheets_data.items():
            table = SheetTable(df)
            self.tab_widget.addTab(table, f"📋 {sheet_name}")
            total_rows += len(df)
            total_cols = max(total_cols, len(df.columns))
        
        self.stats_label.setText(
            f"{len(sheets_data)} 个工作表 | 共 {total_rows} 行 | {total_cols} 列"
        )
        
        logging.info(f"Excel加载完成: {len(sheets_data)} 个工作表")
    
    def on_load_error(self, error: str):
        """加载错误"""
        QMessageBox.critical(self, "错误", f"加载Excel失败:\n{error}")
        logging.error(f"加载Excel失败: {error}")
    
    def change_file(self):
        """更换文件"""
        self.preview_frame.setVisible(False)
        self.upload_area.setVisible(True)
        self.upload_area.open_file_dialog()

