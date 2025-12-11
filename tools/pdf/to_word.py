"""
PDF转Word工具
- 单文件上传
- 进度条显示转换进度
- 保持原始排版
"""
import os
import logging
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QFileDialog, QMessageBox, QProgressBar
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont, QPixmap

from ui.workspace import BaseWorkspace, UploadArea

try:
    from pdf2docx import Converter
    HAS_PDF2DOCX = True
except ImportError:
    HAS_PDF2DOCX = False
    logging.warning("pdf2docx未安装, PDF转Word功能不可用")


class ConvertWorker(QThread):
    """转换工作线程"""
    progress = Signal(int)  # 百分比
    finished = Signal(str)  # 输出路径
    error = Signal(str)
    
    def __init__(self, pdf_path: str, output_path: str):
        super().__init__()
        self.pdf_path = pdf_path
        self.output_path = output_path
    
    def run(self):
        try:
            cv = Converter(self.pdf_path)
            
            # pdf2docx 没有直接的进度回调，我们模拟进度
            self.progress.emit(10)
            
            cv.convert(self.output_path)
            self.progress.emit(90)
            
            cv.close()
            self.progress.emit(100)
            
            self.finished.emit(self.output_path)
            
        except Exception as e:
            logging.error(f"PDF转Word失败: {e}")
            self.error.emit(str(e))


class PDFToWordPage(BaseWorkspace):
    """PDF转Word页面"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.pdf_path = None
        self.setup_convert_ui()
    
    def setup_convert_ui(self):
        """设置转换UI"""
        self.history_btn.hide()
        
        # 上传区域
        self.upload_area = UploadArea("PDF文件 (*.pdf)")
        self.upload_area.files_dropped.connect(self.on_file_added)
        self.content_layout.addWidget(self.upload_area)
        
        # 转换区域
        convert_frame = QFrame()
        convert_frame.setObjectName("card")
        convert_layout = QVBoxLayout(convert_frame)
        convert_layout.setContentsMargins(32, 32, 32, 32)
        convert_layout.setSpacing(24)
        convert_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 图标
        icon_layout = QHBoxLayout()
        icon_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_layout.setSpacing(24)
        
        pdf_icon = QLabel("📄")
        pdf_icon.setFont(QFont("Segoe UI Emoji", 48))
        pdf_icon.setStyleSheet("background: rgba(239, 68, 68, 0.1); border-radius: 16px; padding: 16px;")
        icon_layout.addWidget(pdf_icon)
        
        arrow = QLabel("➡️")
        arrow.setFont(QFont("Segoe UI Emoji", 32))
        icon_layout.addWidget(arrow)
        
        word_icon = QLabel("📝")
        word_icon.setFont(QFont("Segoe UI Emoji", 48))
        word_icon.setStyleSheet("background: rgba(59, 130, 246, 0.1); border-radius: 16px; padding: 16px;")
        icon_layout.addWidget(word_icon)
        
        convert_layout.addLayout(icon_layout)
        
        # 文件信息
        self.file_info = QLabel("选择PDF文件开始转换")
        self.file_info.setStyleSheet("color: #94a3b8; font-size: 14px;")
        self.file_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        convert_layout.addWidget(self.file_info)
        
        # 特性说明
        features_layout = QHBoxLayout()
        features_layout.setSpacing(32)
        features_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        features = [
            ("✅", "保持排版"),
            ("✅", "保留图片"),
            ("✅", "提取表格")
        ]
        
        for icon, text in features:
            feature = QLabel(f"{icon} {text}")
            feature.setStyleSheet("color: #22c55e; font-size: 13px;")
            features_layout.addWidget(feature)
        
        convert_layout.addLayout(features_layout)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMinimumWidth(400)
        convert_layout.addWidget(self.progress_bar, 0, Qt.AlignmentFlag.AlignCenter)
        
        # 状态标签
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #fbbf24; font-size: 13px;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setVisible(False)
        convert_layout.addWidget(self.status_label)
        
        # 转换按钮
        self.convert_btn = QPushButton("📝 开始转换")
        self.convert_btn.setObjectName("primary_btn")
        self.convert_btn.setMinimumSize(200, 50)
        self.convert_btn.setFont(QFont("Microsoft YaHei", 13, QFont.Weight.Bold))
        self.convert_btn.clicked.connect(self.do_convert)
        self.convert_btn.setEnabled(False)
        convert_layout.addWidget(self.convert_btn, 0, Qt.AlignmentFlag.AlignCenter)
        
        # 提示
        hint = QLabel("提示: 转换复杂PDF可能需要较长时间,请耐心等待")
        hint.setStyleSheet("color: #64748b; font-size: 11px;")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        convert_layout.addWidget(hint)
        
        self.content_layout.addWidget(convert_frame)
        self.content_layout.addStretch()
    
    def on_file_added(self, files: list):
        """文件添加"""
        if not files:
            return
        
        pdf_file = None
        for f in files:
            if f.lower().endswith('.pdf'):
                pdf_file = f
                break
        
        if not pdf_file:
            QMessageBox.warning(self, "提示", "请选择PDF文件")
            return
        
        self.pdf_path = pdf_file
        self.file_info.setText(f"📁 {Path(pdf_file).name}")
        self.file_info.setStyleSheet("color: white; font-size: 14px; font-weight: 500;")
        self.convert_btn.setEnabled(True)
        
        logging.info(f"已选择PDF文件: {pdf_file}")
    
    def do_convert(self):
        """执行转换"""
        if not HAS_PDF2DOCX:
            QMessageBox.critical(self, "错误", "pdf2docx未安装,无法转换PDF")
            return
        
        if not self.pdf_path:
            QMessageBox.warning(self, "提示", "请先选择PDF文件")
            return
        
        # 选择保存路径
        default_name = Path(self.pdf_path).stem + ".docx"
        save_path, _ = QFileDialog.getSaveFileName(
            self, "保存Word文档", default_name, "Word文档 (*.docx)"
        )
        
        if not save_path:
            return
        
        # 开始转换
        self.convert_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_label.setVisible(True)
        self.status_label.setText("正在转换中,请稍候...")
        
        self.worker = ConvertWorker(self.pdf_path, save_path)
        self.worker.progress.connect(self.on_progress)
        self.worker.finished.connect(self.on_convert_finished)
        self.worker.error.connect(self.on_convert_error)
        self.worker.start()
        
        logging.info(f"开始转换PDF: {self.pdf_path}")
    
    def on_progress(self, value: int):
        """进度更新"""
        self.progress_bar.setValue(value)
        
        if value < 30:
            self.status_label.setText("正在解析PDF结构...")
        elif value < 70:
            self.status_label.setText("正在转换内容...")
        else:
            self.status_label.setText("正在生成Word文档...")
    
    def on_convert_finished(self, output_path: str):
        """转换完成"""
        self.convert_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_label.setVisible(False)
        
        QMessageBox.information(
            self, "成功",
            f"PDF转Word完成!\n\n保存到: {output_path}"
        )
        logging.info(f"PDF转Word完成: {output_path}")
    
    def on_convert_error(self, error: str):
        """转换错误"""
        self.convert_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_label.setVisible(False)
        
        QMessageBox.critical(self, "错误", f"转换失败:\n{error}")
        logging.error(f"PDF转Word失败: {error}")

