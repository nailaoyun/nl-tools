"""
PDF拆分工具
- 渲染PDF页面缩略图网格
- 多选页面(复选框)
- 导出选中页面为新PDF
"""
import os
import logging
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QFileDialog, QMessageBox, QProgressBar,
    QScrollArea, QGridLayout, QCheckBox
)
from PySide6.QtCore import Qt, QThread, Signal, QSize
from PySide6.QtGui import QFont, QPixmap, QImage

from ui.workspace import BaseWorkspace, UploadArea

# PDF处理
try:
    import fitz  # PyMuPDF
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False
    logging.warning("PyMuPDF未安装, PDF功能不可用")


class PDFRenderWorker(QThread):
    """PDF页面渲染线程"""
    page_rendered = Signal(int, QPixmap)  # page_num, pixmap
    finished = Signal(int)  # total_pages
    error = Signal(str)
    
    def __init__(self, pdf_path: str, dpi: int = 72):
        super().__init__()
        self.pdf_path = pdf_path
        self.dpi = dpi
    
    def run(self):
        if not HAS_PYMUPDF:
            self.error.emit("PyMuPDF未安装")
            return
        
        try:
            doc = fitz.open(self.pdf_path)
            total_pages = len(doc)
            
            for page_num in range(total_pages):
                page = doc[page_num]
                # 渲染页面
                mat = fitz.Matrix(self.dpi / 72, self.dpi / 72)
                pix = page.get_pixmap(matrix=mat)
                
                # 转换为 QPixmap
                img = QImage(
                    pix.samples,
                    pix.width,
                    pix.height,
                    pix.stride,
                    QImage.Format.Format_RGB888 if pix.n == 3 else QImage.Format.Format_RGBA8888
                )
                pixmap = QPixmap.fromImage(img)
                
                self.page_rendered.emit(page_num, pixmap)
            
            doc.close()
            self.finished.emit(total_pages)
            
        except Exception as e:
            logging.error(f"渲染PDF失败: {e}")
            self.error.emit(str(e))


class PageThumbnail(QFrame):
    """页面缩略图组件"""
    
    selection_changed = Signal(int, bool)  # page_num, selected
    
    def __init__(self, page_num: int, parent=None):
        super().__init__(parent)
        self.page_num = page_num
        self.setObjectName("page_thumbnail")
        self.setFixedSize(140, 200)
        self.setup_ui()
    
    def setup_ui(self):
        self.setStyleSheet("""
            #page_thumbnail {
                background: white;
                border: 2px solid transparent;
                border-radius: 8px;
            }
            #page_thumbnail:hover {
                border-color: #fbbf24;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)
        
        # 预览图
        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setStyleSheet("background: #f1f5f9; border-radius: 4px;")
        self.preview_label.setMinimumHeight(150)
        layout.addWidget(self.preview_label, 1)
        
        # 底部信息
        bottom = QHBoxLayout()
        
        self.checkbox = QCheckBox()
        self.checkbox.stateChanged.connect(self.on_checkbox_changed)
        bottom.addWidget(self.checkbox)
        
        page_label = QLabel(f"第 {self.page_num + 1} 页")
        page_label.setStyleSheet("color: #1e293b; font-size: 11px;")
        bottom.addWidget(page_label)
        bottom.addStretch()
        
        layout.addLayout(bottom)
    
    def set_pixmap(self, pixmap: QPixmap):
        """设置预览图"""
        scaled = pixmap.scaled(
            QSize(130, 140),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self.preview_label.setPixmap(scaled)
    
    def on_checkbox_changed(self, state):
        """复选框状态变化"""
        selected = state == Qt.CheckState.Checked.value
        self.selection_changed.emit(self.page_num, selected)
        
        # 更新样式
        if selected:
            self.setStyleSheet("""
                #page_thumbnail {
                    background: white;
                    border: 2px solid #fbbf24;
                    border-radius: 8px;
                    box-shadow: 0 0 0 2px rgba(251, 191, 36, 0.3);
                }
            """)
        else:
            self.setStyleSheet("""
                #page_thumbnail {
                    background: white;
                    border: 2px solid transparent;
                    border-radius: 8px;
                }
                #page_thumbnail:hover {
                    border-color: #fbbf24;
                }
            """)
    
    def set_selected(self, selected: bool):
        """设置选中状态"""
        self.checkbox.setChecked(selected)
    
    def is_selected(self) -> bool:
        """是否选中"""
        return self.checkbox.isChecked()


class PDFSplitPage(BaseWorkspace):
    """PDF拆分页面"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.pdf_path = None
        self.total_pages = 0
        self.page_thumbnails = []
        self.selected_pages = set()
        self.setup_split_ui()
    
    def setup_split_ui(self):
        """设置拆分UI"""
        self.history_btn.hide()
        
        # 上传区域
        self.upload_area = UploadArea("PDF文件 (*.pdf)")
        self.upload_area.files_dropped.connect(self.on_file_added)
        self.content_layout.addWidget(self.upload_area)
        
        # 页面选择区域
        self.pages_frame = QFrame()
        self.pages_frame.setObjectName("card")
        self.pages_frame.setVisible(False)
        pages_layout = QVBoxLayout(self.pages_frame)
        pages_layout.setContentsMargins(20, 20, 20, 20)
        pages_layout.setSpacing(16)
        
        # 标题栏
        header = QHBoxLayout()
        
        title = QLabel("📄 选择页面")
        title.setStyleSheet("color: white; font-weight: 600; font-size: 16px;")
        header.addWidget(title)
        
        header.addStretch()
        
        # 全选/清空
        select_all_btn = QPushButton("全选")
        select_all_btn.setObjectName("secondary_btn")
        select_all_btn.clicked.connect(self.select_all)
        header.addWidget(select_all_btn)
        
        clear_btn = QPushButton("清空")
        clear_btn.setObjectName("secondary_btn")
        clear_btn.clicked.connect(self.clear_selection)
        header.addWidget(clear_btn)
        
        pages_layout.addLayout(header)
        
        # 文件信息
        self.file_info = QLabel("")
        self.file_info.setStyleSheet("color: #94a3b8; font-size: 12px;")
        pages_layout.addWidget(self.file_info)
        
        # 页面网格(滚动区域)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: rgba(15, 23, 42, 0.3); border-radius: 8px;")
        scroll.setMinimumHeight(350)
        
        self.grid_container = QWidget()
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setSpacing(16)
        self.grid_layout.setContentsMargins(16, 16, 16, 16)
        
        scroll.setWidget(self.grid_container)
        pages_layout.addWidget(scroll, 1)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        pages_layout.addWidget(self.progress_bar)
        
        # 底部操作
        bottom = QHBoxLayout()
        
        self.selection_label = QLabel("已选择: 0 页")
        self.selection_label.setStyleSheet("color: #fbbf24; font-size: 13px;")
        bottom.addWidget(self.selection_label)
        
        bottom.addStretch()
        
        self.split_btn = QPushButton("✂️ 拆分选定页面")
        self.split_btn.setObjectName("primary_btn")
        self.split_btn.setMinimumSize(150, 40)
        self.split_btn.setFont(QFont("Microsoft YaHei", 11, QFont.Weight.Bold))
        self.split_btn.clicked.connect(self.do_split)
        bottom.addWidget(self.split_btn)
        
        pages_layout.addLayout(bottom)
        
        self.content_layout.addWidget(self.pages_frame, 1)
    
    def on_file_added(self, files: list):
        """PDF文件添加"""
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
        self.load_pdf()
    
    def load_pdf(self):
        """加载PDF"""
        if not HAS_PYMUPDF:
            QMessageBox.critical(self, "错误", "PyMuPDF未安装,无法处理PDF文件")
            return
        
        # 清空现有内容
        self.clear_pages()
        
        # 显示页面区域
        self.pages_frame.setVisible(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        self.file_info.setText(f"📁 {Path(self.pdf_path).name}")
        
        # 启动渲染线程
        self.render_worker = PDFRenderWorker(self.pdf_path)
        self.render_worker.page_rendered.connect(self.on_page_rendered)
        self.render_worker.finished.connect(self.on_render_finished)
        self.render_worker.error.connect(self.on_render_error)
        self.render_worker.start()
        
        logging.info(f"开始加载PDF: {self.pdf_path}")
    
    def on_page_rendered(self, page_num: int, pixmap: QPixmap):
        """页面渲染完成"""
        thumbnail = PageThumbnail(page_num)
        thumbnail.set_pixmap(pixmap)
        thumbnail.selection_changed.connect(self.on_page_selection_changed)
        
        # 添加到网格
        row = page_num // 5
        col = page_num % 5
        self.grid_layout.addWidget(thumbnail, row, col)
        self.page_thumbnails.append(thumbnail)
        
        # 更新进度
        if self.total_pages > 0:
            self.progress_bar.setValue(int((page_num + 1) / self.total_pages * 100))
    
    def on_render_finished(self, total_pages: int):
        """渲染完成"""
        self.total_pages = total_pages
        self.progress_bar.setVisible(False)
        self.file_info.setText(f"📁 {Path(self.pdf_path).name}  |  共 {total_pages} 页")
        logging.info(f"PDF加载完成: {total_pages} 页")
    
    def on_render_error(self, error: str):
        """渲染错误"""
        self.progress_bar.setVisible(False)
        QMessageBox.critical(self, "错误", f"加载PDF失败:\n{error}")
        logging.error(f"加载PDF失败: {error}")
    
    def on_page_selection_changed(self, page_num: int, selected: bool):
        """页面选择变化"""
        if selected:
            self.selected_pages.add(page_num)
        else:
            self.selected_pages.discard(page_num)
        
        self.selection_label.setText(f"已选择: {len(self.selected_pages)} 页")
    
    def select_all(self):
        """全选"""
        for thumb in self.page_thumbnails:
            thumb.set_selected(True)
    
    def clear_selection(self):
        """清空选择"""
        for thumb in self.page_thumbnails:
            thumb.set_selected(False)
    
    def clear_pages(self):
        """清空页面"""
        for thumb in self.page_thumbnails:
            thumb.deleteLater()
        self.page_thumbnails.clear()
        self.selected_pages.clear()
        self.selection_label.setText("已选择: 0 页")
    
    def do_split(self):
        """执行拆分"""
        if not self.selected_pages:
            QMessageBox.warning(self, "提示", "请先选择要提取的页面")
            return
        
        # 选择保存路径
        save_path, _ = QFileDialog.getSaveFileName(
            self, "保存拆分后的PDF", 
            f"{Path(self.pdf_path).stem}_split.pdf",
            "PDF文件 (*.pdf)"
        )
        
        if not save_path:
            return
        
        try:
            doc = fitz.open(self.pdf_path)
            new_doc = fitz.open()
            
            # 按页码顺序添加
            for page_num in sorted(self.selected_pages):
                new_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)
            
            new_doc.save(save_path)
            new_doc.close()
            doc.close()
            
            QMessageBox.information(
                self, "成功", 
                f"已成功提取 {len(self.selected_pages)} 页!\n\n保存到: {save_path}"
            )
            logging.info(f"PDF拆分完成: {len(self.selected_pages)} 页 -> {save_path}")
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"拆分失败:\n{e}")
            logging.error(f"PDF拆分失败: {e}")

