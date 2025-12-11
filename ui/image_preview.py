"""
图片预览组件
- 原图/处理后对比预览
- 缩放/平移
- 信息显示
"""
import os
from pathlib import Path
from PIL import Image
import io

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QSplitter, QFileDialog, QMessageBox
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QPixmap, QImage, QFont

from core.config import config


class ImagePreviewWidget(QFrame):
    """单个图片预览组件"""
    
    def __init__(self, title: str = "预览", parent=None):
        super().__init__(parent)
        self.title = title
        self._pixmap = None
        self._image_info = {}
        self.setup_ui()
    
    def setup_ui(self):
        self.setStyleSheet("""
            ImagePreviewWidget {
                background: rgba(15, 23, 42, 0.5);
                border: 1px solid #334155;
                border-radius: 12px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        
        # 标题栏
        header = QHBoxLayout()
        
        self.title_label = QLabel(self.title)
        self.title_label.setStyleSheet("""
            background: rgba(0, 0, 0, 0.5);
            color: white;
            font-size: 11px;
            padding: 4px 10px;
            border-radius: 4px;
        """)
        header.addWidget(self.title_label)
        header.addStretch()
        
        # 尺寸信息
        self.size_label = QLabel("")
        self.size_label.setStyleSheet("color: #64748b; font-size: 10px;")
        header.addWidget(self.size_label)
        
        layout.addLayout(header)
        
        # 图片显示区域
        self.image_container = QFrame()
        self.image_container.setStyleSheet("""
            background: #0f172a;
            border-radius: 8px;
        """)
        self.image_container.setMinimumHeight(250)
        
        container_layout = QVBoxLayout(self.image_container)
        container_layout.setContentsMargins(8, 8, 8, 8)
        container_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 占位图标
        self.placeholder_icon = QLabel("🖼️")
        self.placeholder_icon.setFont(QFont("Segoe UI Emoji", 40))
        self.placeholder_icon.setStyleSheet("color: #334155;")
        self.placeholder_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        container_layout.addWidget(self.placeholder_icon)
        
        # 占位文字
        self.placeholder_text = QLabel("暂无图片")
        self.placeholder_text.setStyleSheet("color: #64748b; font-size: 12px;")
        self.placeholder_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        container_layout.addWidget(self.placeholder_text)
        
        # 图片标签
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setVisible(False)
        container_layout.addWidget(self.image_label)
        
        layout.addWidget(self.image_container, 1)
        
        # 文件信息
        self.info_label = QLabel("")
        self.info_label.setStyleSheet("color: #94a3b8; font-size: 11px;")
        self.info_label.setWordWrap(True)
        layout.addWidget(self.info_label)
    
    def set_image(self, pixmap: QPixmap = None, file_path: str = None, 
                  pil_image: Image.Image = None, image_bytes: bytes = None):
        """设置预览图片"""
        if pixmap:
            self._pixmap = pixmap
        elif file_path and os.path.exists(file_path):
            self._pixmap = QPixmap(file_path)
            self._image_info = self._get_file_info(file_path)
        elif pil_image:
            self._pixmap = self._pil_to_pixmap(pil_image)
        elif image_bytes:
            self._pixmap = QPixmap()
            self._pixmap.loadFromData(image_bytes)
        else:
            self._pixmap = None
        
        self._update_display()
    
    def set_image_from_bytes(self, data: bytes, info: dict = None):
        """从字节数据设置图片"""
        self._pixmap = QPixmap()
        self._pixmap.loadFromData(data)
        if info:
            self._image_info = info
        self._update_display()
    
    def _pil_to_pixmap(self, pil_image: Image.Image) -> QPixmap:
        """PIL Image转QPixmap"""
        if pil_image.mode == "RGB":
            data = pil_image.tobytes("raw", "RGB")
            qimage = QImage(data, pil_image.width, pil_image.height, 
                           pil_image.width * 3, QImage.Format.Format_RGB888)
        elif pil_image.mode == "RGBA":
            data = pil_image.tobytes("raw", "RGBA")
            qimage = QImage(data, pil_image.width, pil_image.height,
                           pil_image.width * 4, QImage.Format.Format_RGBA8888)
        else:
            pil_image = pil_image.convert("RGB")
            data = pil_image.tobytes("raw", "RGB")
            qimage = QImage(data, pil_image.width, pil_image.height,
                           pil_image.width * 3, QImage.Format.Format_RGB888)
        return QPixmap.fromImage(qimage)
    
    def _get_file_info(self, file_path: str) -> dict:
        """获取文件信息"""
        try:
            size = os.path.getsize(file_path)
            with Image.open(file_path) as img:
                return {
                    "path": file_path,
                    "name": Path(file_path).name,
                    "width": img.width,
                    "height": img.height,
                    "size": size,
                    "format": img.format
                }
        except:
            return {}
    
    def _update_display(self):
        """更新显示"""
        if self._pixmap and not self._pixmap.isNull():
            # 隐藏占位符
            self.placeholder_icon.setVisible(False)
            self.placeholder_text.setVisible(False)
            self.image_label.setVisible(True)
            
            # 缩放图片适应容器
            container_size = self.image_container.size()
            max_width = container_size.width() - 20
            max_height = container_size.height() - 20
            
            scaled = self._pixmap.scaled(
                QSize(max_width, max_height),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.image_label.setPixmap(scaled)
            
            # 更新尺寸信息
            self.size_label.setText(f"{self._pixmap.width()}×{self._pixmap.height()}")
            
            # 更新文件信息
            if self._image_info:
                size_str = self._format_size(self._image_info.get("size", 0))
                self.info_label.setText(
                    f"📁 {self._image_info.get('name', '')}  |  💾 {size_str}"
                )
        else:
            # 显示占位符
            self.placeholder_icon.setVisible(True)
            self.placeholder_text.setVisible(True)
            self.image_label.setVisible(False)
            self.size_label.setText("")
            self.info_label.setText("")
    
    def set_info(self, info: dict):
        """设置图片信息"""
        self._image_info = info
        if info:
            size_str = self._format_size(info.get("size", 0))
            self.info_label.setText(
                f"📁 {info.get('name', '')}  |  💾 {size_str}"
            )
    
    def clear(self):
        """清空预览"""
        self._pixmap = None
        self._image_info = {}
        self._update_display()
    
    def resizeEvent(self, event):
        """窗口大小变化时重新缩放图片"""
        super().resizeEvent(event)
        if self._pixmap and not self._pixmap.isNull():
            self._update_display()
    
    @staticmethod
    def _format_size(size: int) -> str:
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"


class DualPreviewWidget(QWidget):
    """双栏预览组件 - 原图/处理后对比"""
    
    save_requested = Signal(object)  # 发出保存请求信号，携带处理后的数据
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._processed_data = None  # 保存处理后的数据
        self._output_filename = ""
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        
        # 预览区 - 左右分栏
        preview_layout = QHBoxLayout()
        preview_layout.setSpacing(16)
        
        # 原图预览
        self.original_preview = ImagePreviewWidget("📷 原图")
        preview_layout.addWidget(self.original_preview, 1)
        
        # 处理后预览
        self.result_preview = ImagePreviewWidget("✨ 处理结果")
        preview_layout.addWidget(self.result_preview, 1)
        
        layout.addLayout(preview_layout, 1)
        
        # 对比信息
        self.compare_label = QLabel("")
        self.compare_label.setStyleSheet("""
            color: #22c55e;
            font-size: 13px;
            padding: 8px;
            background: rgba(34, 197, 94, 0.1);
            border-radius: 8px;
        """)
        self.compare_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.compare_label.setVisible(False)
        layout.addWidget(self.compare_label)
        
        # 操作按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.save_btn = QPushButton("💾 保存结果")
        self.save_btn.setObjectName("primary_btn")
        self.save_btn.setMinimumSize(150, 40)
        self.save_btn.clicked.connect(self._on_save_clicked)
        self.save_btn.setEnabled(False)
        btn_layout.addWidget(self.save_btn)
        
        layout.addLayout(btn_layout)
    
    def set_original(self, file_path: str):
        """设置原图"""
        self.original_preview.set_image(file_path=file_path)
    
    def set_result(self, data: bytes, info: dict = None, filename: str = "", 
                   show_size_compare: bool = True):
        """设置处理结果"""
        self._processed_data = data
        self._output_filename = filename
        self.result_preview.set_image_from_bytes(data, info)
        self.save_btn.setEnabled(True)
        
        # 显示对比信息（仅在压缩场景下显示大小对比）
        if info and show_size_compare:
            original_size = self.original_preview._image_info.get("size", 0)
            result_size = info.get("size", len(data))
            if original_size > 0:
                saved = original_size - result_size
                percent = (saved / original_size) * 100
                if saved > 0:
                    self.compare_label.setText(
                        f"✅ 处理完成! 节省 {self._format_size(saved)} ({percent:.1f}%)"
                    )
                    self.compare_label.setStyleSheet("""
                        color: #22c55e;
                        font-size: 13px;
                        padding: 8px;
                        background: rgba(34, 197, 94, 0.1);
                        border-radius: 8px;
                    """)
                    self.compare_label.setVisible(True)
                else:
                    # 文件变大或相同，不显示对比（可能是添加水印等操作）
                    self.compare_label.setVisible(False)
        elif not show_size_compare:
            # 不需要显示大小对比（如水印、格式转换）
            self.compare_label.setText("✅ 处理完成!")
            self.compare_label.setStyleSheet("""
                color: #22c55e;
                font-size: 13px;
                padding: 8px;
                background: rgba(34, 197, 94, 0.1);
                border-radius: 8px;
            """)
            self.compare_label.setVisible(True)
    
    def _on_save_clicked(self):
        """保存按钮点击"""
        if not self._processed_data:
            return
        
        # 检查是否有默认保存路径
        default_dir = config.get_output_directory()
        auto_save = config.get("auto_save_to_default", False)
        
        if default_dir and auto_save:
            # 自动保存
            save_path = os.path.join(default_dir, self._output_filename)
        else:
            # 询问保存位置
            save_path, _ = QFileDialog.getSaveFileName(
                self, "保存文件",
                os.path.join(default_dir, self._output_filename) if default_dir else self._output_filename,
                "图片文件 (*.jpg *.png *.webp)"
            )
        
        if save_path:
            try:
                with open(save_path, 'wb') as f:
                    f.write(self._processed_data)
                QMessageBox.information(self, "成功", f"文件已保存到:\n{save_path}")
                self.save_requested.emit(save_path)
            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存失败:\n{e}")
    
    def clear(self):
        """清空预览"""
        self.original_preview.clear()
        self.result_preview.clear()
        self._processed_data = None
        self._output_filename = ""
        self.save_btn.setEnabled(False)
        self.compare_label.setVisible(False)
    
    @staticmethod
    def _format_size(size: int) -> str:
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"

