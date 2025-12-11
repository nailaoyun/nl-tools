"""
Excel图表生成工具
- 选择数据列
- 图表类型选择(柱状图/折线图/饼图)
- matplotlib图表嵌入Qt窗口
"""
import logging
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QFileDialog, QMessageBox, QComboBox, QListWidget,
    QListWidgetItem, QAbstractItemView, QSplitter, QGroupBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from ui.workspace import BaseWorkspace, UploadArea

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

try:
    import matplotlib
    matplotlib.use('QtAgg')
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
    
    # 设置中文字体
    plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False
except ImportError:
    HAS_MATPLOTLIB = False
    logging.warning("matplotlib未安装, 图表生成功能不可用")


class ChartCanvas(FigureCanvas if HAS_MATPLOTLIB else QWidget):
    """图表画布"""
    
    def __init__(self, parent=None):
        if HAS_MATPLOTLIB:
            self.figure = Figure(figsize=(8, 6), facecolor='#1e293b')
            super().__init__(self.figure)
            self.axes = self.figure.add_subplot(111)
            self.configure_axes()
        else:
            super().__init__(parent)
    
    def configure_axes(self):
        """配置坐标轴样式"""
        self.axes.set_facecolor('#0f172a')
        self.axes.tick_params(colors='#94a3b8')
        self.axes.xaxis.label.set_color('#e2e8f0')
        self.axes.yaxis.label.set_color('#e2e8f0')
        self.axes.title.set_color('white')
        
        for spine in self.axes.spines.values():
            spine.set_color('#334155')
    
    def clear_chart(self):
        """清空图表"""
        if HAS_MATPLOTLIB:
            self.axes.clear()
            self.configure_axes()
            self.draw()
    
    def draw_bar_chart(self, x_data, y_data, x_label: str, y_label: str, title: str):
        """绘制柱状图"""
        self.clear_chart()
        
        colors = ['#fbbf24', '#3b82f6', '#22c55e', '#ef4444', '#8b5cf6', '#ec4899']
        bars = self.axes.bar(x_data, y_data, color=colors[:len(x_data)])
        
        self.axes.set_xlabel(x_label)
        self.axes.set_ylabel(y_label)
        self.axes.set_title(title, fontsize=14, fontweight='bold')
        
        # 旋转x轴标签
        self.axes.tick_params(axis='x', rotation=45)
        self.figure.tight_layout()
        self.draw()
    
    def draw_line_chart(self, x_data, y_data, x_label: str, y_label: str, title: str):
        """绘制折线图"""
        self.clear_chart()
        
        self.axes.plot(x_data, y_data, color='#fbbf24', linewidth=2, marker='o', markersize=6)
        self.axes.fill_between(x_data, y_data, alpha=0.2, color='#fbbf24')
        
        self.axes.set_xlabel(x_label)
        self.axes.set_ylabel(y_label)
        self.axes.set_title(title, fontsize=14, fontweight='bold')
        self.axes.grid(True, alpha=0.3, color='#334155')
        
        self.axes.tick_params(axis='x', rotation=45)
        self.figure.tight_layout()
        self.draw()
    
    def draw_pie_chart(self, labels, values, title: str):
        """绘制饼图"""
        self.clear_chart()
        
        colors = ['#fbbf24', '#3b82f6', '#22c55e', '#ef4444', '#8b5cf6', 
                  '#ec4899', '#14b8a6', '#f97316', '#6366f1', '#84cc16']
        
        wedges, texts, autotexts = self.axes.pie(
            values, 
            labels=labels, 
            autopct='%1.1f%%',
            colors=colors[:len(values)],
            textprops={'color': '#e2e8f0'}
        )
        
        for autotext in autotexts:
            autotext.set_color('#0f172a')
            autotext.set_fontweight('bold')
        
        self.axes.set_title(title, fontsize=14, fontweight='bold')
        self.figure.tight_layout()
        self.draw()
    
    def save_chart(self, file_path: str):
        """保存图表"""
        if HAS_MATPLOTLIB:
            self.figure.savefig(file_path, dpi=150, facecolor='#1e293b', edgecolor='none')


class ExcelChartPage(BaseWorkspace):
    """Excel图表生成页面"""
    
    CHART_TYPES = [
        ("📊 柱状图", "bar"),
        ("📈 折线图", "line"),
        ("🥧 饼图", "pie")
    ]
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.excel_path = None
        self.df = None
        self.setup_chart_ui()
    
    def setup_chart_ui(self):
        """设置图表UI"""
        self.history_btn.hide()
        self.export_btn.clicked.connect(self.export_chart)
        
        # 上传区域
        self.upload_area = UploadArea("Excel文件 (*.xlsx *.xls)")
        self.upload_area.files_dropped.connect(self.on_file_added)
        self.content_layout.addWidget(self.upload_area)
        
        # 主工作区
        self.work_area = QSplitter(Qt.Orientation.Horizontal)
        self.work_area.setVisible(False)
        
        # 左侧设置面板
        settings_frame = QFrame()
        settings_frame.setObjectName("card")
        settings_frame.setFixedWidth(280)
        settings_layout = QVBoxLayout(settings_frame)
        settings_layout.setContentsMargins(16, 16, 16, 16)
        settings_layout.setSpacing(16)
        
        # 文件信息
        self.file_label = QLabel("")
        self.file_label.setStyleSheet("color: #fbbf24; font-size: 12px;")
        self.file_label.setWordWrap(True)
        settings_layout.addWidget(self.file_label)
        
        # Sheet选择
        sheet_group = QGroupBox("📋 工作表")
        sheet_layout = QVBoxLayout(sheet_group)
        self.sheet_combo = QComboBox()
        self.sheet_combo.currentTextChanged.connect(self.on_sheet_changed)
        sheet_layout.addWidget(self.sheet_combo)
        settings_layout.addWidget(sheet_group)
        
        # 图表类型
        type_group = QGroupBox("📊 图表类型")
        type_layout = QVBoxLayout(type_group)
        self.type_combo = QComboBox()
        for text, value in self.CHART_TYPES:
            self.type_combo.addItem(text, value)
        self.type_combo.currentIndexChanged.connect(self.update_chart)
        type_layout.addWidget(self.type_combo)
        settings_layout.addWidget(type_group)
        
        # X轴数据(标签列)
        x_group = QGroupBox("📌 X轴 / 标签列")
        x_layout = QVBoxLayout(x_group)
        self.x_combo = QComboBox()
        self.x_combo.currentIndexChanged.connect(self.update_chart)
        x_layout.addWidget(self.x_combo)
        settings_layout.addWidget(x_group)
        
        # Y轴数据(数值列)
        y_group = QGroupBox("📈 Y轴 / 数值列")
        y_layout = QVBoxLayout(y_group)
        self.y_combo = QComboBox()
        self.y_combo.currentIndexChanged.connect(self.update_chart)
        y_layout.addWidget(self.y_combo)
        settings_layout.addWidget(y_group)
        
        settings_layout.addStretch()
        
        # 更换文件按钮
        change_btn = QPushButton("📂 更换文件")
        change_btn.setObjectName("secondary_btn")
        change_btn.clicked.connect(self.change_file)
        settings_layout.addWidget(change_btn)
        
        # 生成图表按钮
        self.generate_btn = QPushButton("⚡ 生成图表")
        self.generate_btn.setObjectName("primary_btn")
        self.generate_btn.setMinimumHeight(40)
        self.generate_btn.clicked.connect(self.update_chart)
        settings_layout.addWidget(self.generate_btn)
        
        self.work_area.addWidget(settings_frame)
        
        # 右侧图表区
        chart_frame = QFrame()
        chart_frame.setObjectName("card")
        chart_layout = QVBoxLayout(chart_frame)
        chart_layout.setContentsMargins(16, 16, 16, 16)
        
        if HAS_MATPLOTLIB:
            self.chart_canvas = ChartCanvas()
            chart_layout.addWidget(self.chart_canvas)
        else:
            no_chart_label = QLabel("matplotlib未安装,无法显示图表")
            no_chart_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            no_chart_label.setStyleSheet("color: #ef4444;")
            chart_layout.addWidget(no_chart_label)
        
        self.work_area.addWidget(chart_frame)
        self.work_area.setSizes([280, 700])
        
        self.content_layout.addWidget(self.work_area, 1)
    
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
        """加载Excel"""
        if not HAS_PANDAS:
            QMessageBox.critical(self, "错误", "pandas未安装,无法读取Excel")
            return
        
        try:
            self.excel_path = file_path
            self.excel_file = pd.ExcelFile(file_path)
            
            # 更新sheet下拉框
            self.sheet_combo.clear()
            self.sheet_combo.addItems(self.excel_file.sheet_names)
            
            self.file_label.setText(f"📁 {Path(file_path).name}")
            
            self.upload_area.setVisible(False)
            self.work_area.setVisible(True)
            
            logging.info(f"加载Excel: {file_path}")
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载Excel失败:\n{e}")
            logging.error(f"加载Excel失败: {e}")
    
    def on_sheet_changed(self, sheet_name: str):
        """Sheet变化"""
        if not sheet_name:
            return
        
        try:
            self.df = pd.read_excel(self.excel_file, sheet_name=sheet_name)
            
            # 更新列下拉框
            columns = list(self.df.columns)
            
            self.x_combo.clear()
            self.x_combo.addItems([str(c) for c in columns])
            
            self.y_combo.clear()
            # 尝试只添加数值列
            numeric_cols = self.df.select_dtypes(include=['number']).columns.tolist()
            if numeric_cols:
                self.y_combo.addItems([str(c) for c in numeric_cols])
            else:
                self.y_combo.addItems([str(c) for c in columns])
            
            self.update_chart()
            
        except Exception as e:
            logging.error(f"读取工作表失败: {e}")
    
    def update_chart(self):
        """更新图表"""
        if not HAS_MATPLOTLIB or self.df is None:
            return
        
        x_col = self.x_combo.currentText()
        y_col = self.y_combo.currentText()
        chart_type = self.type_combo.currentData()
        
        if not x_col or not y_col:
            return
        
        try:
            # 获取数据
            x_data = self.df[x_col].astype(str).tolist()
            y_data = pd.to_numeric(self.df[y_col], errors='coerce').fillna(0).tolist()
            
            # 限制数据量
            max_items = 20
            if len(x_data) > max_items:
                x_data = x_data[:max_items]
                y_data = y_data[:max_items]
            
            title = f"{y_col} by {x_col}"
            
            if chart_type == "bar":
                self.chart_canvas.draw_bar_chart(x_data, y_data, x_col, y_col, title)
            elif chart_type == "line":
                self.chart_canvas.draw_line_chart(x_data, y_data, x_col, y_col, title)
            elif chart_type == "pie":
                self.chart_canvas.draw_pie_chart(x_data, y_data, title)
            
            logging.debug(f"生成图表: {chart_type}, X={x_col}, Y={y_col}")
            
        except Exception as e:
            logging.error(f"生成图表失败: {e}")
            QMessageBox.warning(self, "警告", f"生成图表失败:\n{e}")
    
    def export_chart(self):
        """导出图表"""
        if not HAS_MATPLOTLIB:
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出图表", "chart.png", "PNG图片 (*.png);;JPEG图片 (*.jpg);;PDF文档 (*.pdf)"
        )
        
        if file_path:
            try:
                self.chart_canvas.save_chart(file_path)
                QMessageBox.information(self, "成功", f"图表已导出到:\n{file_path}")
                logging.info(f"图表导出: {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导出失败:\n{e}")
    
    def change_file(self):
        """更换文件"""
        self.work_area.setVisible(False)
        self.upload_area.setVisible(True)
        self.upload_area.open_file_dialog()

