"""
图片压缩工具 - 极致优化版
专注于：在保证视觉效果不降低的情况下，极致压缩文件大小
- 保持原有格式（不转换格式）
- 多种压缩模式
- 智能参数优化
"""
import os
import io
import logging
from pathlib import Path
from PIL import Image
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSlider, QFrame, QFileDialog, QMessageBox,
    QProgressBar, QListWidget, QListWidgetItem, QCheckBox,
    QGroupBox, QRadioButton, QButtonGroup, QComboBox
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont

from ui.workspace import BaseWorkspace, UploadArea
from ui.image_preview import DualPreviewWidget
from core.config import config


class SmartCompressor:
    """智能图片压缩器 - 保持原格式，极致压缩"""
    
    # 压缩模式
    MODE_VISUALLY_LOSSLESS = "visually"  # 视觉无损（推荐）
    MODE_BALANCED = "balanced"           # 均衡模式
    MODE_MAXIMUM = "maximum"             # 极致压缩
    MODE_LOSSLESS = "lossless"           # 完全无损
    
    @classmethod
    def compress(cls, img: Image.Image, original_format: str, mode: str,
                 quality_override: int = None) -> tuple:
        """
        压缩图片（保持原格式）
        
        Args:
            img: PIL Image对象
            original_format: 原始格式 (jpeg/png/webp)
            mode: 压缩模式
            quality_override: 手动覆盖质量值
            
        Returns:
            (compressed_data, output_extension)
        """
        # 标准化格式名
        fmt = original_format.lower()
        if fmt in ['jpg', 'jpeg']:
            return cls._compress_jpeg(img, mode, quality_override)
        elif fmt == 'png':
            return cls._compress_png(img, mode)
        elif fmt == 'webp':
            return cls._compress_webp(img, mode, quality_override)
        elif fmt == 'gif':
            return cls._compress_gif(img)
        else:
            # 未知格式，转为JPEG压缩
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                if img.mode in ('RGBA', 'LA'):
                    background.paste(img, mask=img.split()[-1])
                else:
                    background.paste(img)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            return cls._compress_jpeg(img, mode, quality_override)
    
    @classmethod
    def _compress_jpeg(cls, img: Image.Image, mode: str, quality_override: int = None) -> tuple:
        """JPEG极致压缩"""
        # 确保是RGB模式
        if img.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            if img.mode in ('RGBA', 'LA'):
                background.paste(img, mask=img.split()[-1])
            else:
                background.paste(img)
            img = background
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        
        buffer = io.BytesIO()
        
        # 根据模式选择参数
        if quality_override is not None:
            quality = quality_override
        else:
            quality = {
                cls.MODE_LOSSLESS: 100,
                cls.MODE_VISUALLY_LOSSLESS: 88,  # 视觉无损的最佳质量
                cls.MODE_BALANCED: 80,
                cls.MODE_MAXIMUM: 70,
            }.get(mode, 85)
        
        # 子采样设置：quality高时用4:4:4保持质量
        if quality >= 90:
            subsampling = 0  # 4:4:4
        elif quality >= 80:
            subsampling = 1  # 4:2:2
        else:
            subsampling = 2  # 4:2:0
        
        img.save(
            buffer, 
            "JPEG",
            quality=quality,
            optimize=True,
            subsampling=subsampling,
            progressive=True
        )
        
        return buffer.getvalue(), ".jpg"
    
    @classmethod
    def _compress_png(cls, img: Image.Image, mode: str) -> tuple:
        """PNG压缩（无损，但优化）"""
        buffer = io.BytesIO()
        
        # PNG是无损格式，只能通过优化来减小
        # 对于极致压缩模式，尝试减少颜色
        if mode == cls.MODE_MAXIMUM:
            # 检查是否可以用调色板模式
            if img.mode == 'RGBA':
                colors = img.getcolors(maxcolors=256)
                if colors:
                    img = img.convert('P', palette=Image.Palette.ADAPTIVE, colors=len(colors))
            elif img.mode == 'RGB':
                colors = img.getcolors(maxcolors=256)
                if colors:
                    img = img.convert('P', palette=Image.Palette.ADAPTIVE, colors=len(colors))
        
        img.save(
            buffer,
            "PNG",
            optimize=True,
            compress_level=9  # 最大压缩级别
        )
        
        return buffer.getvalue(), ".png"
    
    @classmethod
    def _compress_webp(cls, img: Image.Image, mode: str, quality_override: int = None) -> tuple:
        """WebP压缩"""
        buffer = io.BytesIO()
        
        if mode == cls.MODE_LOSSLESS:
            img.save(buffer, "WEBP", lossless=True, quality=100)
        else:
            if quality_override is not None:
                quality = quality_override
            else:
                quality = {
                    cls.MODE_VISUALLY_LOSSLESS: 88,
                    cls.MODE_BALANCED: 80,
                    cls.MODE_MAXIMUM: 70,
                }.get(mode, 85)
            
            img.save(
                buffer,
                "WEBP",
                quality=quality,
                method=6  # 最慢但压缩率最高
            )
        
        return buffer.getvalue(), ".webp"
    
    @classmethod
    def _compress_gif(cls, img: Image.Image) -> tuple:
        """GIF保持原样（GIF压缩会丢失动画）"""
        buffer = io.BytesIO()
        img.save(buffer, "GIF", optimize=True)
        return buffer.getvalue(), ".gif"


class CompressWorker(QThread):
    """压缩工作线程"""
    progress = Signal(int, int)
    file_processed = Signal(str, bytes, dict)
    finished = Signal(list)
    
    def __init__(self, files: list, compress_mode: str, quality: int = None,
                 resize_percent: int = 100):
        super().__init__()
        self.files = files
        self.compress_mode = compress_mode
        self.quality = quality
        self.resize_percent = resize_percent
    
    def run(self):
        results = []
        total = len(self.files)
        
        for i, file_path in enumerate(self.files):
            try:
                result = self.compress_image(file_path)
                results.append(result)
                
                if result.get("success") and result.get("data"):
                    self.file_processed.emit(
                        file_path, 
                        result["data"],
                        {
                            "size": result["compressed_size"],
                            "name": result.get("output_name", ""),
                            "original_size": result["original_size"]
                        }
                    )
            except Exception as e:
                logging.error(f"压缩失败 {file_path}: {e}")
                results.append({
                    "file": file_path,
                    "success": False,
                    "error": str(e)
                })
            
            self.progress.emit(i + 1, total)
        
        self.finished.emit(results)
    
    def compress_image(self, file_path: str) -> dict:
        """压缩单个图片"""
        original_size = os.path.getsize(file_path)
        original_ext = Path(file_path).suffix.lower()
        
        # 获取原始格式
        original_format = original_ext.lstrip('.')
        
        with Image.open(file_path) as img:
            original_width, original_height = img.size
            
            # 调整尺寸（如果需要）
            if self.resize_percent < 100:
                new_width = int(original_width * self.resize_percent / 100)
                new_height = int(original_height * self.resize_percent / 100)
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # 压缩（保持原格式）
            compressed_data, ext = SmartCompressor.compress(
                img,
                original_format,
                self.compress_mode,
                self.quality
            )
            
            compressed_size = len(compressed_data)
            
            # 如果压缩后反而变大，使用原文件
            if compressed_size >= original_size and self.resize_percent == 100:
                with open(file_path, 'rb') as f:
                    compressed_data = f.read()
                compressed_size = original_size
                ext = original_ext
            
            output_name = Path(file_path).stem + "_compressed" + ext
            
            return {
                "file": file_path,
                "output_name": output_name,
                "original_size": original_size,
                "compressed_size": compressed_size,
                "ratio": (1 - compressed_size / original_size) * 100 if original_size > 0 else 0,
                "success": True,
                "data": compressed_data
            }


class ImageCompressPage(BaseWorkspace):
    """图片压缩页面"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.files = []
        self.current_file_index = 0
        self.processed_results = {}
        self.setup_compress_ui()
    
    def setup_compress_ui(self):
        """设置压缩UI"""
        self.history_btn.hide()
        self.export_btn.setText("💾 批量保存")
        self.export_btn.clicked.connect(self.batch_save)
        
        # 上传区域
        self.upload_area = UploadArea("图片文件 (*.jpg *.jpeg *.png *.webp *.gif *.bmp)")
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
        settings_frame.setFixedWidth(300)
        settings_frame.setStyleSheet("""
            #card {
                background: #1e293b;
                border: 1px solid #334155;
                border-radius: 16px;
            }
        """)
        settings_layout = QVBoxLayout(settings_frame)
        settings_layout.setContentsMargins(20, 20, 20, 20)
        settings_layout.setSpacing(16)
        
        # ====== 压缩模式 ======
        mode_group = QGroupBox("🎯 压缩模式")
        mode_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                color: #e2e8f0;
                border: 1px solid #334155;
                border-radius: 8px;
                margin-top: 8px;
                padding-top: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px;
            }
        """)
        mode_layout = QVBoxLayout(mode_group)
        mode_layout.setSpacing(6)
        
        self.mode_group = QButtonGroup(self)
        
        modes = [
            ("visually", "🔒 视觉无损（推荐）", "肉眼几乎看不出差异", True),
            ("balanced", "⚖️ 均衡模式", "平衡质量与压缩率"),
            ("maximum", "🚀 极致压缩", "最大压缩，可能有轻微损失"),
            ("lossless", "💎 完全无损", "100%保留原质量"),
        ]
        
        for i, mode_data in enumerate(modes):
            mode_id, text, desc = mode_data[:3]
            is_default = len(mode_data) > 3 and mode_data[3]
            
            radio = QRadioButton(text)
            radio.setProperty("mode_id", mode_id)
            radio.setStyleSheet("color: #e2e8f0; font-size: 12px;")
            if is_default:
                radio.setChecked(True)
            self.mode_group.addButton(radio, i)
            mode_layout.addWidget(radio)
            
            desc_label = QLabel(f"   {desc}")
            desc_label.setStyleSheet("color: #64748b; font-size: 10px;")
            mode_layout.addWidget(desc_label)
        
        settings_layout.addWidget(mode_group)
        
        # ====== 高级设置 ======
        advanced_group = QGroupBox("⚙️ 高级选项")
        advanced_group.setStyleSheet(mode_group.styleSheet())
        advanced_layout = QVBoxLayout(advanced_group)
        advanced_layout.setSpacing(10)
        
        # 手动质量
        self.manual_quality_check = QCheckBox("手动指定质量")
        self.manual_quality_check.setStyleSheet("color: #cbd5e1; font-size: 12px;")
        self.manual_quality_check.stateChanged.connect(self.on_manual_quality_changed)
        advanced_layout.addWidget(self.manual_quality_check)
        
        quality_row = QHBoxLayout()
        self.quality_slider = QSlider(Qt.Orientation.Horizontal)
        self.quality_slider.setRange(50, 100)
        self.quality_slider.setValue(85)
        self.quality_slider.setEnabled(False)
        self.quality_slider.valueChanged.connect(self.on_quality_changed)
        quality_row.addWidget(self.quality_slider, 1)
        
        self.quality_label = QLabel("85%")
        self.quality_label.setStyleSheet("color: #fbbf24; font-weight: bold; min-width: 35px;")
        quality_row.addWidget(self.quality_label)
        advanced_layout.addLayout(quality_row)
        
        # 缩放
        resize_row = QHBoxLayout()
        resize_row.addWidget(QLabel("尺寸:"))
        self.resize_combo = QComboBox()
        self.resize_combo.addItem("100% 原尺寸", 100)
        self.resize_combo.addItem("75%", 75)
        self.resize_combo.addItem("50%", 50)
        resize_row.addWidget(self.resize_combo, 1)
        advanced_layout.addLayout(resize_row)
        
        settings_layout.addWidget(advanced_group)
        
        # ====== 文件列表 ======
        files_header = QHBoxLayout()
        files_label = QLabel("📁 待压缩文件")
        files_label.setStyleSheet("color: #e2e8f0; font-weight: bold; font-size: 12px;")
        files_header.addWidget(files_label)
        
        self.files_count = QLabel("0")
        self.files_count.setStyleSheet("color: #fbbf24;")
        files_header.addWidget(self.files_count)
        files_header.addStretch()
        
        clear_btn = QPushButton("清空")
        clear_btn.setObjectName("secondary_btn")
        clear_btn.setFixedWidth(50)
        clear_btn.clicked.connect(self.clear_files)
        files_header.addWidget(clear_btn)
        
        settings_layout.addLayout(files_header)
        
        self.files_list = QListWidget()
        self.files_list.setMaximumHeight(100)
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
        self.preview_btn.setMinimumHeight(38)
        self.preview_btn.clicked.connect(self.preview_current)
        settings_layout.addWidget(self.preview_btn)
        
        # 开始压缩按钮
        self.compress_btn = QPushButton("⚡ 开始压缩")
        self.compress_btn.setObjectName("primary_btn")
        self.compress_btn.setMinimumHeight(45)
        self.compress_btn.setFont(QFont("Microsoft YaHei", 12, QFont.Weight.Bold))
        self.compress_btn.clicked.connect(self.start_compress_all)
        settings_layout.addWidget(self.compress_btn)
        
        content_layout.addWidget(settings_frame)
        
        self.content_layout.addWidget(content_widget, 1)
    
    def get_compress_settings(self) -> dict:
        """获取压缩设置"""
        selected_btn = self.mode_group.checkedButton()
        mode = selected_btn.property("mode_id") if selected_btn else "visually"
        
        quality = None
        if self.manual_quality_check.isChecked():
            quality = self.quality_slider.value()
        
        resize_percent = self.resize_combo.currentData()
        
        return {"mode": mode, "quality": quality, "resize": resize_percent}
    
    def on_manual_quality_changed(self, state):
        self.quality_slider.setEnabled(state == Qt.CheckState.Checked.value)
    
    def on_quality_changed(self, value: int):
        self.quality_label.setText(f"{value}%")
    
    def on_files_added(self, files: list):
        valid_exts = ('.jpg', '.jpeg', '.png', '.webp', '.gif', '.bmp')
        for file_path in files:
            if file_path.lower().endswith(valid_exts):
                if file_path not in self.files:
                    self.files.append(file_path)
                    size = os.path.getsize(file_path)
                    size_str = self.format_size(size)
                    item = QListWidgetItem(f"📷 {Path(file_path).name} ({size_str})")
                    item.setData(Qt.ItemDataRole.UserRole, file_path)
                    self.files_list.addItem(item)
        
        self.files_count.setText(str(len(self.files)))
        
        if self.files:
            self.files_list.setCurrentRow(0)
            self.preview_widget.set_original(self.files[0])
            self.current_file_index = 0
    
    def on_file_clicked(self, item: QListWidgetItem):
        file_path = item.data(Qt.ItemDataRole.UserRole)
        self.current_file_index = self.files.index(file_path)
        self.preview_widget.set_original(file_path)
        
        if file_path in self.processed_results:
            result = self.processed_results[file_path]
            self.preview_widget.set_result(
                result["data"],
                {"size": result["compressed_size"], "name": result["output_name"]},
                result["output_name"]
            )
    
    def clear_files(self):
        self.files.clear()
        self.files_list.clear()
        self.files_count.setText("0")
        self.processed_results.clear()
        self.preview_widget.clear()
    
    def preview_current(self):
        if not self.files:
            QMessageBox.warning(self, "提示", "请先添加要压缩的图片")
            return
        
        settings = self.get_compress_settings()
        file_path = self.files[self.current_file_index]
        
        self.preview_btn.setEnabled(False)
        self.preview_btn.setText("处理中...")
        
        self.worker = CompressWorker(
            [file_path], settings["mode"], settings["quality"], settings["resize"]
        )
        self.worker.file_processed.connect(self.on_preview_ready)
        self.worker.finished.connect(lambda: self.preview_btn.setEnabled(True))
        self.worker.finished.connect(lambda: self.preview_btn.setText("👁️ 预览效果"))
        self.worker.start()
    
    def on_preview_ready(self, file_path: str, data: bytes, info: dict):
        output_name = info.get("name", Path(file_path).stem + "_compressed.jpg")
        self.preview_widget.set_result(data, info, output_name)
        self.processed_results[file_path] = {
            "data": data,
            "compressed_size": info.get("size", len(data)),
            "output_name": output_name
        }
    
    def start_compress_all(self):
        if not self.files:
            QMessageBox.warning(self, "提示", "请先添加要压缩的图片")
            return
        
        settings = self.get_compress_settings()
        
        self.compress_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        self.worker = CompressWorker(
            self.files, settings["mode"], settings["quality"], settings["resize"]
        )
        self.worker.progress.connect(self.on_progress)
        self.worker.file_processed.connect(self.on_file_processed)
        self.worker.finished.connect(self.on_compress_finished)
        self.worker.start()
    
    def on_progress(self, current: int, total: int):
        self.progress_bar.setValue(int(current / total * 100))
    
    def on_file_processed(self, file_path: str, data: bytes, info: dict):
        output_name = info.get("name", Path(file_path).stem + "_compressed.jpg")
        self.processed_results[file_path] = {
            "data": data,
            "compressed_size": info.get("size", len(data)),
            "output_name": output_name,
            "original_size": info.get("original_size", 0)
        }
        
        if self.files.index(file_path) == self.current_file_index:
            self.preview_widget.set_result(data, info, output_name)
    
    def on_compress_finished(self, results: list):
        self.compress_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        success = sum(1 for r in results if r.get("success"))
        total_orig = sum(r.get("original_size", 0) for r in results if r.get("success"))
        total_comp = sum(r.get("compressed_size", 0) for r in results if r.get("success"))
        saved = total_orig - total_comp
        
        if total_orig > 0:
            pct = (saved / total_orig) * 100
            msg = (f"压缩完成!\n\n"
                   f"✅ 成功: {success}/{len(results)}\n"
                   f"📊 原始: {self.format_size(total_orig)}\n"
                   f"📦 压缩后: {self.format_size(total_comp)}\n"
                   f"💾 节省: {self.format_size(saved)} ({pct:.1f}%)")
        else:
            msg = f"压缩完成!\n✅ 成功: {success}/{len(results)}"
        
        QMessageBox.information(self, "完成", msg)
    
    def on_file_saved(self, path):
        logging.info(f"已保存: {path}")
    
    def batch_save(self):
        if not self.processed_results:
            QMessageBox.warning(self, "提示", "没有可保存的结果，请先压缩")
            return
        
        output_dir = QFileDialog.getExistingDirectory(
            self, "选择保存目录", config.get_output_directory()
        )
        if not output_dir:
            return
        
        saved = 0
        for fp, result in self.processed_results.items():
            try:
                with open(os.path.join(output_dir, result["output_name"]), 'wb') as f:
                    f.write(result["data"])
                saved += 1
            except Exception as e:
                logging.error(f"保存失败: {e}")
        
        QMessageBox.information(self, "完成", f"已保存 {saved} 个文件到:\n{output_dir}")
    
    @staticmethod
    def format_size(size: int) -> str:
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"
