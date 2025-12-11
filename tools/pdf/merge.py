"""
PDF合并工具
- 文件列表 + 拖拽排序
- 添加/删除/上下移动
- 一键合并
"""
import os
import logging
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QFileDialog, QMessageBox, QProgressBar,
    QListWidget, QListWidgetItem, QAbstractItemView
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont, QIcon

from ui.workspace import BaseWorkspace, UploadArea

try:
    import fitz
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False


class MergeWorker(QThread):
    """合并工作线程"""
    progress = Signal(int, int)
    finished = Signal(str)
    error = Signal(str)
    
    def __init__(self, files: list, output_path: str):
        super().__init__()
        self.files = files
        self.output_path = output_path
    
    def run(self):
        try:
            merged = fitz.open()
            total = len(self.files)
            
            for i, file_path in enumerate(self.files):
                doc = fitz.open(file_path)
                merged.insert_pdf(doc)
                doc.close()
                self.progress.emit(i + 1, total)
            
            merged.save(self.output_path)
            merged.close()
            
            self.finished.emit(self.output_path)
            
        except Exception as e:
            logging.error(f"合并PDF失败: {e}")
            self.error.emit(str(e))


class PDFFileItem(QWidget):
    """PDF文件列表项"""
    
    remove_clicked = Signal(str)  # file_path
    
    def __init__(self, file_path: str, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.setup_ui()
    
    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(12)
        
        # 拖拽手柄
        handle = QLabel("⋮⋮")
        handle.setStyleSheet("color: #64748b; font-size: 16px;")
        handle.setCursor(Qt.CursorShape.OpenHandCursor)
        layout.addWidget(handle)
        
        # PDF图标
        icon = QLabel("📄")
        icon.setFont(QFont("Segoe UI Emoji", 16))
        layout.addWidget(icon)
        
        # 文件信息
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)
        
        name = QLabel(Path(self.file_path).name)
        name.setStyleSheet("color: #e2e8f0; font-size: 13px; font-weight: 500;")
        info_layout.addWidget(name)
        
        # 文件大小
        size = os.path.getsize(self.file_path)
        size_str = self.format_size(size)
        size_label = QLabel(size_str)
        size_label.setStyleSheet("color: #64748b; font-size: 11px;")
        info_layout.addWidget(size_label)
        
        layout.addLayout(info_layout, 1)
        
        # 删除按钮
        remove_btn = QPushButton("🗑")
        remove_btn.setFixedSize(32, 32)
        remove_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background: rgba(239, 68, 68, 0.2);
            }
        """)
        remove_btn.clicked.connect(lambda: self.remove_clicked.emit(self.file_path))
        layout.addWidget(remove_btn)
    
    @staticmethod
    def format_size(size: int) -> str:
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"


class PDFMergePage(BaseWorkspace):
    """PDF合并页面"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.files = []
        self.setup_merge_ui()
    
    def setup_merge_ui(self):
        """设置合并UI"""
        self.history_btn.hide()
        
        # 上传区域
        self.upload_area = UploadArea("PDF文件 (*.pdf)")
        self.upload_area.files_dropped.connect(self.on_files_added)
        self.content_layout.addWidget(self.upload_area)
        
        # 文件列表区域
        list_frame = QFrame()
        list_frame.setObjectName("card")
        list_layout = QVBoxLayout(list_frame)
        list_layout.setContentsMargins(20, 20, 20, 20)
        list_layout.setSpacing(16)
        
        # 标题
        header = QHBoxLayout()
        
        title = QLabel("📑 待合并文件列表")
        title.setStyleSheet("color: white; font-weight: 600; font-size: 16px;")
        header.addWidget(title)
        
        header.addStretch()
        
        hint = QLabel("(可拖拽排序)")
        hint.setStyleSheet("color: #64748b; font-size: 12px;")
        header.addWidget(hint)
        
        list_layout.addLayout(header)
        
        # 文件列表
        self.file_list = QListWidget()
        self.file_list.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.file_list.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.file_list.setMinimumHeight(250)
        self.file_list.setStyleSheet("""
            QListWidget {
                background: rgba(15, 23, 42, 0.5);
                border: 1px solid #334155;
                border-radius: 8px;
            }
            QListWidget::item {
                background: #1e293b;
                border: 1px solid #334155;
                border-radius: 8px;
                margin: 4px;
                padding: 4px;
            }
            QListWidget::item:hover {
                border-color: #fbbf24;
            }
            QListWidget::item:selected {
                background: rgba(251, 191, 36, 0.1);
                border-color: #fbbf24;
            }
        """)
        self.file_list.model().rowsMoved.connect(self.on_rows_moved)
        list_layout.addWidget(self.file_list)
        
        # 操作按钮
        btn_layout = QHBoxLayout()
        
        add_btn = QPushButton("➕ 添加文件")
        add_btn.setObjectName("secondary_btn")
        add_btn.clicked.connect(self.add_files)
        btn_layout.addWidget(add_btn)
        
        move_up_btn = QPushButton("⬆️ 上移")
        move_up_btn.setObjectName("secondary_btn")
        move_up_btn.clicked.connect(self.move_up)
        btn_layout.addWidget(move_up_btn)
        
        move_down_btn = QPushButton("⬇️ 下移")
        move_down_btn.setObjectName("secondary_btn")
        move_down_btn.clicked.connect(self.move_down)
        btn_layout.addWidget(move_down_btn)
        
        btn_layout.addStretch()
        
        clear_btn = QPushButton("🗑️ 清空列表")
        clear_btn.setObjectName("secondary_btn")
        clear_btn.clicked.connect(self.clear_files)
        btn_layout.addWidget(clear_btn)
        
        list_layout.addLayout(btn_layout)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        list_layout.addWidget(self.progress_bar)
        
        # 合并按钮
        self.merge_btn = QPushButton("📑 合并为单个 PDF")
        self.merge_btn.setObjectName("primary_btn")
        self.merge_btn.setMinimumHeight(50)
        self.merge_btn.setFont(QFont("Microsoft YaHei", 13, QFont.Weight.Bold))
        self.merge_btn.clicked.connect(self.do_merge)
        list_layout.addWidget(self.merge_btn)
        
        self.content_layout.addWidget(list_frame, 1)
    
    def on_files_added(self, files: list):
        """文件添加"""
        for file_path in files:
            if file_path.lower().endswith('.pdf') and file_path not in self.files:
                self.files.append(file_path)
                self.add_file_item(file_path)
        
        logging.info(f"添加了 {len(files)} 个PDF文件")
    
    def add_file_item(self, file_path: str):
        """添加文件列表项"""
        item = QListWidgetItem()
        item.setData(Qt.ItemDataRole.UserRole, file_path)
        item.setSizeHint(QListWidgetItem().sizeHint())
        item.setSizeHint(item.sizeHint().expandedTo(QListWidgetItem().sizeHint()))
        
        widget = PDFFileItem(file_path)
        widget.remove_clicked.connect(self.remove_file)
        
        item.setSizeHint(widget.sizeHint())
        self.file_list.addItem(item)
        self.file_list.setItemWidget(item, widget)
    
    def remove_file(self, file_path: str):
        """移除文件"""
        if file_path in self.files:
            self.files.remove(file_path)
        
        for i in range(self.file_list.count()):
            item = self.file_list.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == file_path:
                self.file_list.takeItem(i)
                break
    
    def add_files(self):
        """添加文件对话框"""
        files, _ = QFileDialog.getOpenFileNames(
            self, "选择PDF文件", "", "PDF文件 (*.pdf)"
        )
        if files:
            self.on_files_added(files)
    
    def move_up(self):
        """上移"""
        row = self.file_list.currentRow()
        if row > 0:
            item = self.file_list.takeItem(row)
            self.file_list.insertItem(row - 1, item)
            self.file_list.setCurrentRow(row - 1)
            
            # 重新创建widget
            file_path = item.data(Qt.ItemDataRole.UserRole)
            widget = PDFFileItem(file_path)
            widget.remove_clicked.connect(self.remove_file)
            item.setSizeHint(widget.sizeHint())
            self.file_list.setItemWidget(item, widget)
            
            self.sync_files_order()
    
    def move_down(self):
        """下移"""
        row = self.file_list.currentRow()
        if row < self.file_list.count() - 1:
            item = self.file_list.takeItem(row)
            self.file_list.insertItem(row + 1, item)
            self.file_list.setCurrentRow(row + 1)
            
            # 重新创建widget
            file_path = item.data(Qt.ItemDataRole.UserRole)
            widget = PDFFileItem(file_path)
            widget.remove_clicked.connect(self.remove_file)
            item.setSizeHint(widget.sizeHint())
            self.file_list.setItemWidget(item, widget)
            
            self.sync_files_order()
    
    def on_rows_moved(self):
        """行移动后同步文件顺序"""
        self.sync_files_order()
    
    def sync_files_order(self):
        """同步文件顺序"""
        self.files = []
        for i in range(self.file_list.count()):
            item = self.file_list.item(i)
            file_path = item.data(Qt.ItemDataRole.UserRole)
            if file_path:
                self.files.append(file_path)
    
    def clear_files(self):
        """清空文件"""
        self.files.clear()
        self.file_list.clear()
    
    def do_merge(self):
        """执行合并"""
        if not HAS_PYMUPDF:
            QMessageBox.critical(self, "错误", "PyMuPDF未安装,无法合并PDF")
            return
        
        if len(self.files) < 2:
            QMessageBox.warning(self, "提示", "请至少添加2个PDF文件")
            return
        
        # 同步顺序
        self.sync_files_order()
        
        # 选择保存路径
        save_path, _ = QFileDialog.getSaveFileName(
            self, "保存合并后的PDF", "merged.pdf", "PDF文件 (*.pdf)"
        )
        
        if not save_path:
            return
        
        # 开始合并
        self.merge_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        self.worker = MergeWorker(self.files, save_path)
        self.worker.progress.connect(self.on_progress)
        self.worker.finished.connect(self.on_merge_finished)
        self.worker.error.connect(self.on_merge_error)
        self.worker.start()
        
        logging.info(f"开始合并 {len(self.files)} 个PDF文件")
    
    def on_progress(self, current: int, total: int):
        """进度更新"""
        self.progress_bar.setValue(int(current / total * 100))
    
    def on_merge_finished(self, output_path: str):
        """合并完成"""
        self.merge_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        QMessageBox.information(
            self, "成功", 
            f"PDF合并完成!\n\n共合并 {len(self.files)} 个文件\n保存到: {output_path}"
        )
        logging.info(f"PDF合并完成: {output_path}")
    
    def on_merge_error(self, error: str):
        """合并错误"""
        self.merge_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        QMessageBox.critical(self, "错误", f"合并失败:\n{error}")
        logging.error(f"PDF合并失败: {error}")

