"""
图片格式转换工具
- 支持 JPG/PNG/WEBP/ICO/PDF 互转
- 预览转换效果
- 批量转换
- 进度显示
"""
import os
import io
import logging
from pathlib import Path
from PIL import Image
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QFileDialog, QMessageBox, QProgressBar,
    QListWidget, QListWidgetItem, QButtonGroup
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont

from ui.workspace import BaseWorkspace, UploadArea
from ui.image_preview import DualPreviewWidget
from core.config import config


class ConvertWorker(QThread):
    """转换工作线程"""
    progress = Signal(int, int)
    file_processed = Signal(str, bytes, dict, str)  # file_path, data, info, output_name
    finished = Signal(list)
    
    def __init__(self, files: list, target_format: str, output_dir: str = None):
        super().__init__()
        self.files = files
        self.target_format = target_format.lower()
        self.output_dir = output_dir
        self.save_files = output_dir is not None
    
    def run(self):
        results = []
        total = len(self.files)
        
        for i, file_path in enumerate(self.files):
            try:
                result = self.convert_image(file_path)
                results.append(result)
                
                if result.get("success") and result.get("data"):
                    self.file_processed.emit(
                        file_path,
                        result["data"],
                        {"size": len(result["data"]), "name": result["output_name"]},
                        result["output_name"]
                    )
            except Exception as e:
                logging.error(f"转换失败 {file_path}: {e}")
                results.append({
                    "file": file_path,
                    "success": False,
                    "error": str(e)
                })
            
            self.progress.emit(i + 1, total)
        
        self.finished.emit(results)
    
    def convert_image(self, file_path: str) -> dict:
        """转换单个图片"""
        output_name = Path(file_path).stem + f".{self.target_format}"
        output_buffer = io.BytesIO()
        
        with Image.open(file_path) as img:
            # 处理透明通道
            if self.target_format in ['jpg', 'jpeg', 'pdf']:
                if img.mode in ('RGBA', 'P', 'LA'):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                    img = background
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
            
            # 保存到缓冲区
            if self.target_format == 'ico':
                sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
                img.save(output_buffer, format='ICO', sizes=sizes)
            elif self.target_format == 'pdf':
                img.save(output_buffer, 'PDF', resolution=100.0)
            else:
                save_format = 'JPEG' if self.target_format in ['jpg', 'jpeg'] else self.target_format.upper()
                img.save(output_buffer, save_format, quality=95)
        
        data = output_buffer.getvalue()
        
        # 如果需要保存
        output_path = None
        if self.save_files and self.output_dir:
            output_path = os.path.join(self.output_dir, output_name)
            with open(output_path, 'wb') as f:
                f.write(data)
        
        return {
            "file": file_path,
            "output": output_path,
            "output_name": output_name,
            "success": True,
            "data": data
        }


class ImageConvertPage(BaseWorkspace):
    """图片格式转换页面"""
    
    FORMATS = ['JPG', 'PNG', 'WEBP', 'ICO', 'PDF']
    FORMAT_COLORS = {
        'JPG': '#3b82f6',
        'PNG': '#22c55e', 
        'WEBP': '#8b5cf6',
        'ICO': '#f59e0b',
        'PDF': '#ef4444'
    }
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.files = []
        self.current_file_index = 0
        self.processed_results = {}
        self.selected_format = 'WEBP'
        self.setup_convert_ui()
    
    def setup_convert_ui(self):
        """设置转换UI"""
        self.history_btn.hide()
        self.export_btn.setText("💾 批量保存")
        self.export_btn.clicked.connect(self.batch_save)
        
        # 上传区域
        self.upload_area = UploadArea("图片文件 (*.jpg *.jpeg *.png *.webp *.bmp *.gif)")
        self.upload_area.files_dropped.connect(self.on_files_added)
        self.content_layout.addWidget(self.upload_area)
        
        # 主内容区
        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(24)
        
        # 左侧 - 预览区
        self.preview_widget = DualPreviewWidget()
        self.preview_widget.save_requested.connect(self.on_file_saved)
        content_layout.addWidget(self.preview_widget, 2)
        
        # 右侧设置区
        settings_frame = QFrame()
        settings_frame.setObjectName("card")
        settings_frame.setFixedWidth(280)
        settings_frame.setStyleSheet("""
            #card {
                background: #1e293b;
                border: 1px solid #334155;
                border-radius: 16px;
            }
        """)
        settings_layout = QVBoxLayout(settings_frame)
        settings_layout.setContentsMargins(24, 24, 24, 24)
        settings_layout.setSpacing(16)
        
        # 标题
        title = QLabel("🔄 选择目标格式")
        title.setStyleSheet("color: white; font-weight: 600; font-size: 14px;")
        settings_layout.addWidget(title)
        
        # 格式按钮
        formats_widget = QWidget()
        formats_layout = QVBoxLayout(formats_widget)
        formats_layout.setSpacing(8)
        
        self.format_buttons = {}
        for fmt in self.FORMATS:
            btn = QPushButton(fmt)
            btn.setCheckable(True)
            btn.setMinimumHeight(40)
            color = self.FORMAT_COLORS.get(fmt, '#64748b')
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: rgba({self._hex_to_rgb(color)}, 0.1);
                    border: 2px solid {color};
                    border-radius: 8px;
                    color: {color};
                    font-weight: bold;
                    font-size: 13px;
                }}
                QPushButton:hover {{
                    background: rgba({self._hex_to_rgb(color)}, 0.2);
                }}
                QPushButton:checked {{
                    background: {color};
                    color: white;
                }}
            """)
            btn.clicked.connect(lambda checked, f=fmt: self.on_format_selected(f))
            formats_layout.addWidget(btn)
            self.format_buttons[fmt] = btn
        
        # 默认选中 WEBP
        self.format_buttons['WEBP'].setChecked(True)
        
        settings_layout.addWidget(formats_widget)
        
        # 文件列表
        files_header = QHBoxLayout()
        files_label = QLabel("待转换文件")
        files_label.setStyleSheet("color: #cbd5e1; font-size: 13px;")
        files_header.addWidget(files_label)
        
        self.files_count = QLabel("0")
        self.files_count.setStyleSheet("color: #fbbf24; font-size: 12px;")
        files_header.addWidget(self.files_count)
        files_header.addStretch()
        
        clear_btn = QPushButton("清空")
        clear_btn.setObjectName("secondary_btn")
        clear_btn.setFixedWidth(60)
        clear_btn.clicked.connect(self.clear_files)
        files_header.addWidget(clear_btn)
        
        settings_layout.addLayout(files_header)
        
        self.files_list = QListWidget()
        self.files_list.setMaximumHeight(120)
        self.files_list.itemClicked.connect(self.on_file_clicked)
        settings_layout.addWidget(self.files_list)
        
        settings_layout.addStretch()
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        settings_layout.addWidget(self.progress_bar)
        
        # 预览按钮
        self.preview_btn = QPushButton("👁️ 预览效果")
        self.preview_btn.setObjectName("secondary_btn")
        self.preview_btn.setMinimumHeight(40)
        self.preview_btn.clicked.connect(self.preview_current)
        settings_layout.addWidget(self.preview_btn)
        
        # 转换按钮
        self.convert_btn = QPushButton("⚡ 转换全部")
        self.convert_btn.setObjectName("primary_btn")
        self.convert_btn.setMinimumSize(150, 45)
        self.convert_btn.setFont(QFont("Microsoft YaHei", 12, QFont.Weight.Bold))
        self.convert_btn.clicked.connect(self.start_convert_all)
        settings_layout.addWidget(self.convert_btn)
        
        content_layout.addWidget(settings_frame)
        
        self.content_layout.addWidget(content_widget, 1)
    
    def on_format_selected(self, fmt: str):
        """格式选择"""
        self.selected_format = fmt
        for f, btn in self.format_buttons.items():
            btn.setChecked(f == fmt)
    
    def on_files_added(self, files: list):
        """文件添加"""
        valid_extensions = ('.jpg', '.jpeg', '.png', '.webp', '.bmp', '.gif')
        for file_path in files:
            if file_path.lower().endswith(valid_extensions):
                if file_path not in self.files:
                    self.files.append(file_path)
                    item = QListWidgetItem(f"📷 {Path(file_path).name}")
                    item.setData(Qt.ItemDataRole.UserRole, file_path)
                    self.files_list.addItem(item)
        
        self.files_count.setText(str(len(self.files)))
        
        if self.files:
            self.files_list.setCurrentRow(0)
            self.preview_widget.set_original(self.files[0])
            self.current_file_index = 0
        
        logging.info(f"添加了 {len(files)} 个文件用于转换")
    
    def on_file_clicked(self, item: QListWidgetItem):
        """文件点击"""
        file_path = item.data(Qt.ItemDataRole.UserRole)
        self.current_file_index = self.files.index(file_path)
        self.preview_widget.set_original(file_path)
        
        if file_path in self.processed_results:
            result = self.processed_results[file_path]
            self.preview_widget.set_result(
                result["data"],
                {"size": len(result["data"]), "name": result["output_name"]},
                result["output_name"]
            )
    
    def clear_files(self):
        """清空文件"""
        self.files.clear()
        self.files_list.clear()
        self.files_count.setText("0")
        self.processed_results.clear()
        self.preview_widget.clear()
    
    def preview_current(self):
        """预览当前文件"""
        if not self.files:
            QMessageBox.warning(self, "提示", "请先添加要转换的图片文件")
            return
        
        file_path = self.files[self.current_file_index]
        
        self.preview_btn.setEnabled(False)
        self.preview_btn.setText("处理中...")
        
        self.worker = ConvertWorker([file_path], self.selected_format, None)
        self.worker.file_processed.connect(self.on_preview_ready)
        self.worker.finished.connect(lambda: self.preview_btn.setEnabled(True))
        self.worker.finished.connect(lambda: self.preview_btn.setText("👁️ 预览效果"))
        self.worker.start()
    
    def on_preview_ready(self, file_path: str, data: bytes, info: dict, output_name: str):
        """预览完成"""
        self.preview_widget.set_result(data, info, output_name, show_size_compare=False)
        self.processed_results[file_path] = {
            "data": data,
            "output_name": output_name
        }
    
    def start_convert_all(self):
        """转换所有文件"""
        if not self.files:
            QMessageBox.warning(self, "提示", "请先添加要转换的图片文件")
            return
        
        self.convert_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        self.worker = ConvertWorker(self.files, self.selected_format, None)
        self.worker.progress.connect(self.on_progress)
        self.worker.file_processed.connect(self.on_file_processed)
        self.worker.finished.connect(self.on_convert_finished)
        self.worker.start()
        
        logging.info(f"开始转换 {len(self.files)} 个文件为 {self.selected_format}")
    
    def on_progress(self, current: int, total: int):
        """进度更新"""
        self.progress_bar.setValue(int(current / total * 100))
    
    def on_file_processed(self, file_path: str, data: bytes, info: dict, output_name: str):
        """文件处理完成"""
        self.processed_results[file_path] = {
            "data": data,
            "output_name": output_name
        }
        
        if self.files.index(file_path) == self.current_file_index:
            self.preview_widget.set_result(data, info, output_name, show_size_compare=False)
    
    def on_convert_finished(self, results: list):
        """转换完成"""
        self.convert_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        success_count = sum(1 for r in results if r.get("success"))
        
        msg = f"转换完成!\n\n✅ 成功: {success_count}/{len(results)}\n\n请点击「批量保存」或在预览中单独保存"
        QMessageBox.information(self, "转换结果", msg)
        logging.info(f"转换完成: 成功 {success_count}/{len(results)}")
    
    def on_file_saved(self, save_path):
        """文件保存"""
        logging.info(f"文件已保存: {save_path}")
    
    def batch_save(self):
        """批量保存"""
        if not self.processed_results:
            QMessageBox.warning(self, "提示", "没有可保存的处理结果")
            return
        
        default_dir = config.get_output_directory()
        output_dir = QFileDialog.getExistingDirectory(self, "选择保存目录", default_dir)
        
        if not output_dir:
            return
        
        saved_count = 0
        for file_path, result in self.processed_results.items():
            try:
                output_path = os.path.join(output_dir, result["output_name"])
                with open(output_path, 'wb') as f:
                    f.write(result["data"])
                saved_count += 1
            except Exception as e:
                logging.error(f"保存失败 {file_path}: {e}")
        
        QMessageBox.information(
            self, "保存完成",
            f"已保存 {saved_count}/{len(self.processed_results)} 个文件到:\n{output_dir}"
        )
    
    @staticmethod
    def _hex_to_rgb(hex_color: str) -> str:
        hex_color = hex_color.lstrip('#')
        r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        return f"{r}, {g}, {b}"
