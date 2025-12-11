"""
图片加水印工具
- 支持文字水印和图片水印
- 可调整位置、透明度、大小
- 预览功能
- 批量处理
"""
import os
import io
import logging
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSlider, QFrame, QFileDialog, QMessageBox, QProgressBar,
    QListWidget, QListWidgetItem, QLineEdit, QComboBox,
    QTabWidget, QSpinBox, QColorDialog
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont, QColor

from ui.workspace import BaseWorkspace, UploadArea
from ui.image_preview import DualPreviewWidget
from core.config import config


class WatermarkWorker(QThread):
    """水印工作线程"""
    progress = Signal(int, int)
    file_processed = Signal(str, bytes, dict, str)  # file_path, data, info, output_name
    finished = Signal(list)
    
    def __init__(self, files: list, watermark_config: dict, output_dir: str = None):
        super().__init__()
        self.files = files
        self.config = watermark_config
        self.output_dir = output_dir
        self.save_files = output_dir is not None
    
    def run(self):
        results = []
        total = len(self.files)
        
        for i, file_path in enumerate(self.files):
            try:
                result = self.add_watermark(file_path)
                results.append(result)
                
                if result.get("success") and result.get("data"):
                    self.file_processed.emit(
                        file_path,
                        result["data"],
                        {"size": len(result["data"]), "name": result["output_name"]},
                        result["output_name"]
                    )
            except Exception as e:
                logging.error(f"添加水印失败 {file_path}: {e}")
                results.append({
                    "file": file_path,
                    "success": False,
                    "error": str(e)
                })
            
            self.progress.emit(i + 1, total)
        
        self.finished.emit(results)
    
    def add_watermark(self, file_path: str) -> dict:
        """添加水印"""
        ext = Path(file_path).suffix.lower()
        output_name = Path(file_path).stem + "_watermarked" + ext
        output_buffer = io.BytesIO()
        
        with Image.open(file_path) as img:
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            
            watermark_layer = Image.new('RGBA', img.size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(watermark_layer)
            
            if self.config['type'] == 'text':
                self.add_text_watermark(draw, img.size)
            else:
                self.add_image_watermark(watermark_layer, img.size)
            
            result = Image.alpha_composite(img, watermark_layer)
            
            # 保存
            if ext in ['.jpg', '.jpeg']:
                result = result.convert('RGB')
                result.save(output_buffer, 'JPEG', quality=95)
            elif ext == '.png':
                result.save(output_buffer, 'PNG')
            else:
                result = result.convert('RGB')
                result.save(output_buffer, 'JPEG', quality=95)
                output_name = Path(file_path).stem + "_watermarked.jpg"
        
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
    
    def add_text_watermark(self, draw: ImageDraw, img_size: tuple):
        """添加文字水印"""
        text = self.config.get('text', 'Watermark')
        opacity = int(self.config.get('opacity', 50) * 2.55)
        font_size = self.config.get('font_size', 48)  # 默认更大的字体
        color = self.config.get('color', (255, 255, 255))
        position = self.config.get('position', 'center')
        
        # 尝试使用支持中文的字体
        font = None
        # Windows 中文字体列表
        chinese_fonts = [
            "C:/Windows/Fonts/msyh.ttc",      # 微软雅黑
            "C:/Windows/Fonts/simhei.ttf",    # 黑体
            "C:/Windows/Fonts/simsun.ttc",    # 宋体
            "C:/Windows/Fonts/simkai.ttf",    # 楷体
            "msyh.ttc",
            "simhei.ttf",
            "arial.ttf",
        ]
        
        for font_path in chinese_fonts:
            try:
                font = ImageFont.truetype(font_path, font_size)
                break
            except:
                continue
        
        if font is None:
            font = ImageFont.load_default()
        
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        positions = {
            'top-left': (20, 20),
            'top-right': (img_size[0] - text_width - 20, 20),
            'bottom-left': (20, img_size[1] - text_height - 20),
            'bottom-right': (img_size[0] - text_width - 20, img_size[1] - text_height - 20),
            'center': ((img_size[0] - text_width) // 2, (img_size[1] - text_height) // 2)
        }
        
        x, y = positions.get(position, positions['center'])
        draw.text((x, y), text, font=font, fill=(*color, opacity))
    
    def add_image_watermark(self, layer: Image, img_size: tuple):
        """添加图片水印"""
        watermark_path = self.config.get('image_path')
        if not watermark_path or not os.path.exists(watermark_path):
            return
        
        opacity = self.config.get('opacity', 50) / 100
        scale = self.config.get('scale', 20) / 100
        position = self.config.get('position', 'center')
        
        with Image.open(watermark_path) as watermark:
            if watermark.mode != 'RGBA':
                watermark = watermark.convert('RGBA')
            
            new_width = int(img_size[0] * scale)
            ratio = new_width / watermark.width
            new_height = int(watermark.height * ratio)
            watermark = watermark.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            alpha = watermark.split()[3]
            alpha = alpha.point(lambda p: int(p * opacity))
            watermark.putalpha(alpha)
            
            positions = {
                'top-left': (20, 20),
                'top-right': (img_size[0] - new_width - 20, 20),
                'bottom-left': (20, img_size[1] - new_height - 20),
                'bottom-right': (img_size[0] - new_width - 20, img_size[1] - new_height - 20),
                'center': ((img_size[0] - new_width) // 2, (img_size[1] - new_height) // 2)
            }
            
            x, y = positions.get(position, positions['center'])
            layer.paste(watermark, (x, y), watermark)


class ImageWatermarkPage(BaseWorkspace):
    """图片加水印页面"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.files = []
        self.current_file_index = 0
        self.processed_results = {}
        self.watermark_color = (255, 255, 255)
        self.watermark_image_path = None
        self.setup_watermark_ui()
    
    def setup_watermark_ui(self):
        """设置水印UI"""
        self.history_btn.hide()
        self.export_btn.setText("💾 批量保存")
        self.export_btn.clicked.connect(self.batch_save)
        
        # 上传区域
        self.upload_area = UploadArea("图片文件 (*.jpg *.jpeg *.png *.webp)")
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
        
        # 标签页
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane { border: none; background: transparent; }
            QTabBar::tab {
                background: transparent;
                color: #94a3b8;
                padding: 8px 16px;
                border-bottom: 2px solid transparent;
            }
            QTabBar::tab:selected { color: #fbbf24; border-bottom: 2px solid #fbbf24; }
        """)
        
        # 文字水印
        text_tab = QWidget()
        text_layout = QVBoxLayout(text_tab)
        text_layout.setSpacing(12)
        
        text_input_layout = QHBoxLayout()
        text_input_layout.addWidget(QLabel("水印文字:"))
        self.text_input = QLineEdit("© 奶酪云工具箱")
        text_input_layout.addWidget(self.text_input, 1)
        text_layout.addLayout(text_input_layout)
        
        font_layout = QHBoxLayout()
        font_layout.addWidget(QLabel("字体大小:"))
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(24, 300)
        self.font_size_spin.setValue(72)  # 默认更大的字体
        font_layout.addWidget(self.font_size_spin)
        font_layout.addStretch()
        
        font_layout.addWidget(QLabel("颜色:"))
        self.color_btn = QPushButton()
        self.color_btn.setFixedSize(40, 30)
        self.color_btn.setStyleSheet("background: white; border-radius: 4px;")
        self.color_btn.clicked.connect(self.choose_color)
        font_layout.addWidget(self.color_btn)
        text_layout.addLayout(font_layout)
        
        self.tab_widget.addTab(text_tab, "📝 文字水印")
        
        # 图片水印
        image_tab = QWidget()
        image_layout = QVBoxLayout(image_tab)
        image_layout.setSpacing(12)
        
        img_select_layout = QHBoxLayout()
        img_select_layout.addWidget(QLabel("水印图片:"))
        self.watermark_path_label = QLabel("未选择")
        self.watermark_path_label.setStyleSheet("color: #64748b;")
        img_select_layout.addWidget(self.watermark_path_label, 1)
        
        select_img_btn = QPushButton("选择")
        select_img_btn.setObjectName("secondary_btn")
        select_img_btn.clicked.connect(self.select_watermark_image)
        img_select_layout.addWidget(select_img_btn)
        image_layout.addLayout(img_select_layout)
        
        scale_layout = QHBoxLayout()
        scale_layout.addWidget(QLabel("缩放:"))
        self.scale_slider = QSlider(Qt.Orientation.Horizontal)
        self.scale_slider.setRange(5, 50)
        self.scale_slider.setValue(20)
        scale_layout.addWidget(self.scale_slider, 1)
        self.scale_value = QLabel("20%")
        self.scale_slider.valueChanged.connect(lambda v: self.scale_value.setText(f"{v}%"))
        scale_layout.addWidget(self.scale_value)
        image_layout.addLayout(scale_layout)
        
        self.tab_widget.addTab(image_tab, "🖼️ 图片水印")
        
        settings_layout.addWidget(self.tab_widget)
        
        # 通用设置
        common_frame = QFrame()
        common_frame.setStyleSheet("background: rgba(15, 23, 42, 0.5); border-radius: 8px; padding: 8px;")
        common_layout = QVBoxLayout(common_frame)
        common_layout.setSpacing(8)
        
        opacity_layout = QHBoxLayout()
        opacity_layout.addWidget(QLabel("透明度:"))
        self.opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.opacity_slider.setRange(10, 100)
        self.opacity_slider.setValue(50)
        opacity_layout.addWidget(self.opacity_slider, 1)
        self.opacity_value = QLabel("50%")
        self.opacity_slider.valueChanged.connect(lambda v: self.opacity_value.setText(f"{v}%"))
        opacity_layout.addWidget(self.opacity_value)
        common_layout.addLayout(opacity_layout)
        
        pos_layout = QHBoxLayout()
        pos_layout.addWidget(QLabel("位置:"))
        self.position_combo = QComboBox()
        positions = [("左上角", "top-left"), ("右上角", "top-right"), 
                    ("左下角", "bottom-left"), ("右下角", "bottom-right"), ("居中", "center")]
        for text, value in positions:
            self.position_combo.addItem(text, value)
        self.position_combo.setCurrentIndex(4)
        pos_layout.addWidget(self.position_combo)
        pos_layout.addStretch()
        common_layout.addLayout(pos_layout)
        
        settings_layout.addWidget(common_frame)
        
        # 文件列表
        files_header = QHBoxLayout()
        files_label = QLabel("📁 待处理:")
        files_header.addWidget(files_label)
        self.count_label = QLabel("0")
        self.count_label.setStyleSheet("color: #fbbf24;")
        files_header.addWidget(self.count_label)
        files_header.addStretch()
        
        clear_btn = QPushButton("清空")
        clear_btn.setObjectName("secondary_btn")
        clear_btn.clicked.connect(self.clear_files)
        files_header.addWidget(clear_btn)
        settings_layout.addLayout(files_header)
        
        self.files_list = QListWidget()
        self.files_list.setMaximumHeight(80)
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
        
        # 开始按钮
        self.start_btn = QPushButton("💧 添加水印")
        self.start_btn.setObjectName("primary_btn")
        self.start_btn.setMinimumSize(150, 45)
        self.start_btn.setFont(QFont("Microsoft YaHei", 12, QFont.Weight.Bold))
        self.start_btn.clicked.connect(self.start_watermark_all)
        settings_layout.addWidget(self.start_btn)
        
        content_layout.addWidget(settings_frame)
        
        self.content_layout.addWidget(content_widget, 1)
    
    def on_files_added(self, files: list):
        """文件添加"""
        for file_path in files:
            if file_path.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                if file_path not in self.files:
                    self.files.append(file_path)
                    self.files_list.addItem(f"📷 {Path(file_path).name}")
        
        self.count_label.setText(str(len(self.files)))
        
        if self.files:
            self.files_list.setCurrentRow(0)
            self.preview_widget.set_original(self.files[0])
            self.current_file_index = 0
    
    def on_file_clicked(self, item):
        """文件点击"""
        row = self.files_list.currentRow()
        if row >= 0 and row < len(self.files):
            self.current_file_index = row
            file_path = self.files[row]
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
        self.count_label.setText("0")
        self.processed_results.clear()
        self.preview_widget.clear()
    
    def choose_color(self):
        """选择颜色"""
        color = QColorDialog.getColor(QColor(*self.watermark_color), self)
        if color.isValid():
            self.watermark_color = (color.red(), color.green(), color.blue())
            self.color_btn.setStyleSheet(f"background: {color.name()}; border-radius: 4px;")
    
    def select_watermark_image(self):
        """选择水印图片"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择水印图片", "", "图片文件 (*.png *.jpg *.jpeg)"
        )
        if file_path:
            self.watermark_image_path = file_path
            self.watermark_path_label.setText(Path(file_path).name)
    
    def get_watermark_config(self) -> dict:
        """获取水印配置"""
        is_text = self.tab_widget.currentIndex() == 0
        config = {
            'type': 'text' if is_text else 'image',
            'opacity': self.opacity_slider.value(),
            'position': self.position_combo.currentData()
        }
        
        if is_text:
            config['text'] = self.text_input.text() or 'Watermark'
            config['font_size'] = self.font_size_spin.value()
            config['color'] = self.watermark_color
        else:
            config['image_path'] = self.watermark_image_path
            config['scale'] = self.scale_slider.value()
        
        return config
    
    def preview_current(self):
        """预览当前文件"""
        if not self.files:
            QMessageBox.warning(self, "提示", "请先添加要处理的图片文件")
            return
        
        watermark_config = self.get_watermark_config()
        if watermark_config['type'] == 'image' and not self.watermark_image_path:
            QMessageBox.warning(self, "提示", "请先选择水印图片")
            return
        
        file_path = self.files[self.current_file_index]
        
        self.preview_btn.setEnabled(False)
        self.preview_btn.setText("处理中...")
        
        self.worker = WatermarkWorker([file_path], watermark_config, None)
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
    
    def start_watermark_all(self):
        """处理所有文件"""
        if not self.files:
            QMessageBox.warning(self, "提示", "请先添加要处理的图片文件")
            return
        
        watermark_config = self.get_watermark_config()
        if watermark_config['type'] == 'image' and not self.watermark_image_path:
            QMessageBox.warning(self, "提示", "请先选择水印图片")
            return
        
        self.start_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        self.worker = WatermarkWorker(self.files, watermark_config, None)
        self.worker.progress.connect(self.on_progress)
        self.worker.file_processed.connect(self.on_file_processed)
        self.worker.finished.connect(self.on_finished)
        self.worker.start()
        
        logging.info(f"开始添加水印, 文件数: {len(self.files)}")
    
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
    
    def on_finished(self, results: list):
        """处理完成"""
        self.start_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        success_count = sum(1 for r in results if r.get("success"))
        QMessageBox.information(
            self, "完成", 
            f"水印添加完成!\n\n✅ 成功: {success_count}/{len(results)}\n\n请点击「批量保存」或在预览中单独保存"
        )
        logging.info(f"水印添加完成: 成功 {success_count}/{len(results)}")
    
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
