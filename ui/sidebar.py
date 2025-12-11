"""
左侧一级菜单组件
- Logo (使用图片，点击弹出个人信息卡片)
- 图片工具、PDF工具箱、Excel表格 三个分类
- 设置按钮
- 选中状态有左侧高亮条
- 水波纹点击效果
"""
import os
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QButtonGroup, 
    QSpacerItem, QSizePolicy, QLabel, QFrame, QGraphicsOpacityEffect
)
from PySide6.QtCore import (
    Signal, Qt, QSize, QPropertyAnimation, QEasingCurve, 
    QPoint, QTimer, QParallelAnimationGroup, QSequentialAnimationGroup,
    Property
)
from PySide6.QtGui import (
    QFont, QPainter, QColor, QLinearGradient, QPen, QBrush, QPixmap,
    QRadialGradient, QPainterPath
)
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtCore import QByteArray


# 获取资源目录
def get_resource_path(relative_path: str) -> str:
    """获取资源文件的绝对路径"""
    base_path = Path(__file__).parent.parent
    return str(base_path / relative_path)


# Logo图片路径
LOGO_IMAGE_PATH = get_resource_path("image/生成奶酪商城官方店介绍.png")


# SVG 图标定义 (Phosphor Icons 风格)
ICONS = {
    "cheese": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256"><path fill="currentColor" d="M184 32a8 8 0 0 0-8 8v16h-16a8 8 0 0 0 0 16h16v16a8 8 0 0 0 16 0V72h16a8 8 0 0 0 0-16h-16V40a8 8 0 0 0-8-8m48 88h-64a8 8 0 0 0-8 8v64a8 8 0 0 0 8 8h64a8 8 0 0 0 8-8v-64a8 8 0 0 0-8-8m-8 64h-48v-48h48ZM80 40a8 8 0 0 0-8 8v16H56a8 8 0 0 0 0 16h16v16a8 8 0 0 0 16 0V80h16a8 8 0 0 0 0-16H88V48a8 8 0 0 0-8-8m48 88H64a8 8 0 0 0-8 8v64a8 8 0 0 0 8 8h64a8 8 0 0 0 8-8v-64a8 8 0 0 0-8-8m-8 64H72v-48h48Z"/></svg>""",
    "image": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256"><path fill="currentColor" d="M216 40H40a16 16 0 0 0-16 16v144a16 16 0 0 0 16 16h176a16 16 0 0 0 16-16V56a16 16 0 0 0-16-16m0 16v102.75l-26.07-26.06a16 16 0 0 0-22.63 0l-20 20l-44-44a16 16 0 0 0-22.62 0L40 149.37V56ZM40 172l52-52l80 80H40Zm176 28h-21.37l-36-36l20-20L216 181.38V200m-72-100a12 12 0 1 1 12 12a12 12 0 0 1-12-12"/></svg>""",
    "file-pdf": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256"><path fill="currentColor" d="M224 152a8 8 0 0 1-8 8h-24v16h16a8 8 0 0 1 0 16h-16v16a8 8 0 0 1-16 0v-56a8 8 0 0 1 8-8h32a8 8 0 0 1 8 8M92 172a28 28 0 0 1-28 28h-8v8a8 8 0 0 1-16 0v-56a8 8 0 0 1 8-8h16a28 28 0 0 1 28 28m-16 0a12 12 0 0 0-12-12h-8v24h8a12 12 0 0 0 12-12m88 0c0 21.78-14.36 36-36 36h-16a8 8 0 0 1-8-8v-56a8 8 0 0 1 8-8h16c21.64 0 36 14.22 36 36m-16 0c0-13.56-8-20-20-20h-8v40h8c12 0 20-6.44 20-20M40 112V40a16 16 0 0 1 16-16h96a8 8 0 0 1 5.66 2.34l56 56A8 8 0 0 1 216 88v24a8 8 0 0 1-16 0V96h-48a8 8 0 0 1-8-8V40H56v72a8 8 0 0 1-16 0m120-32h28.69L160 51.31Z"/></svg>""",
    "file-xls": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256"><path fill="currentColor" d="M156 208a8 8 0 0 1-8 8h-24a8 8 0 0 1-8-8v-56a8 8 0 0 1 16 0v48h16a8 8 0 0 1 8 8m-62.37-55.58a8 8 0 0 0-11.26 1.21L68 172.32l-14.37-18.69a8 8 0 0 0-12.47 10.05L58.59 184l-17.43 20.32a8 8 0 0 0 12.47 10.05L68 195.68l14.37 18.69A8 8 0 0 0 88 216a8 8 0 0 0 5.05-1.79a8 8 0 0 0 1.21-11.26L77.41 184l16.85-19.63a8 8 0 0 0-1.63-11.95m72 5.58c-14.06 0-24.63 8.88-24.63 20.67S151.57 200 166.63 200a22.76 22.76 0 0 0 7.47-1.27a8 8 0 0 0-5.2-15.13a6.89 6.89 0 0 1-2.27.4c-4.39 0-8.63-2.72-8.63-4.67s4.24-4.66 8.63-4.66c3.36 0 5.15 1 5.79 1.55a8 8 0 0 0 10.63-12a22.6 22.6 0 0 0-16.42-5.89M40 112V40a16 16 0 0 1 16-16h96a8 8 0 0 1 5.66 2.34l56 56A8 8 0 0 1 216 88v24a8 8 0 0 1-16 0V96h-48a8 8 0 0 1-8-8V40H56v72a8 8 0 0 1-16 0m120-32h28.69L160 51.31Z"/></svg>""",
    "gear": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256"><path fill="currentColor" d="M128 80a48 48 0 1 0 48 48a48.05 48.05 0 0 0-48-48m0 80a32 32 0 1 1 32-32a32 32 0 0 1-32 32m88-29.84q.06-2.16 0-4.32l14.92-18.64a8 8 0 0 0 1.48-7.06a107.6 107.6 0 0 0-10.88-26.25a8 8 0 0 0-6-3.93l-23.72-2.64q-1.48-1.56-3-3L186 40.54a8 8 0 0 0-3.94-6a107.29 107.29 0 0 0-26.25-10.86a8 8 0 0 0-7.06 1.48L130.16 40h-4.32L107.2 25.11a8 8 0 0 0-7.06-1.48a107.6 107.6 0 0 0-26.25 10.88a8 8 0 0 0-3.93 6l-2.64 23.76q-1.56 1.49-3 3L40.54 70a8 8 0 0 0-6 3.94a107.71 107.71 0 0 0-10.87 26.25a8 8 0 0 0 1.49 7.06L40 125.84v4.32L25.11 148.8a8 8 0 0 0-1.48 7.06a107.6 107.6 0 0 0 10.88 26.25a8 8 0 0 0 6 3.93l23.72 2.64q1.49 1.56 3 3L70 215.46a8 8 0 0 0 3.94 6a107.71 107.71 0 0 0 26.25 10.87a8 8 0 0 0 7.06-1.49L125.84 216q2.16.06 4.32 0l18.64 14.92a8 8 0 0 0 7.06 1.48a107.21 107.21 0 0 0 26.25-10.88a8 8 0 0 0 3.93-6l2.64-23.72q1.56-1.48 3-3l23.78-2.8a8 8 0 0 0 6-3.94a107.71 107.71 0 0 0 10.87-26.25a8 8 0 0 0-1.49-7.06Zm-16.1-6.5a73.93 73.93 0 0 1 0 8.68a8 8 0 0 0 1.74 5.48l14.19 17.73a91.57 91.57 0 0 1-6.23 15l-22.6 2.56a8 8 0 0 0-5.1 2.64a74.11 74.11 0 0 1-6.14 6.14a8 8 0 0 0-2.64 5.1l-2.51 22.58a91.32 91.32 0 0 1-15 6.23l-17.74-14.19a8 8 0 0 0-5-1.75h-.48a73.93 73.93 0 0 1-8.68 0a8 8 0 0 0-5.48 1.74l-17.78 14.2a91.57 91.57 0 0 1-15-6.23L82.89 168a8 8 0 0 0-2.64-5.1a74.11 74.11 0 0 1-6.14-6.14a8 8 0 0 0-5.1-2.64l-22.58-2.52a91.32 91.32 0 0 1-6.23-15l14.19-17.74a8 8 0 0 0 1.74-5.48a73.93 73.93 0 0 1 0-8.68a8 8 0 0 0-1.74-5.48L40.2 81.76a91.57 91.57 0 0 1 6.23-15L69 64.2a8 8 0 0 0 5.1-2.64a74.11 74.11 0 0 1 6.14-6.14A8 8 0 0 0 82.89 50l2.51-22.57a91.32 91.32 0 0 1 15-6.23l17.74 14.19a8 8 0 0 0 5.48 1.74a73.93 73.93 0 0 1 8.68 0a8 8 0 0 0 5.48-1.74l17.77-14.19a91.57 91.57 0 0 1 15 6.23L168 50a8 8 0 0 0 2.64 5.1a74.11 74.11 0 0 1 6.14 6.14a8 8 0 0 0 5.1 2.64l22.58 2.51a91.32 91.32 0 0 1 6.23 15l-14.19 17.74a8 8 0 0 0-1.6 5.53Z"/></svg>""",
}


class IconWidget(QLabel):
    """SVG图标组件"""
    
    def __init__(self, icon_name: str, size: int = 24, color: str = "#94a3b8", parent=None):
        super().__init__(parent)
        self.icon_name = icon_name
        self.icon_size = size
        self.icon_color = color
        self.setFixedSize(size, size)
        self.update_icon()
    
    def set_color(self, color: str):
        self.icon_color = color
        self.update_icon()
    
    def update_icon(self):
        svg_data = ICONS.get(self.icon_name, "")
        if svg_data:
            # 替换颜色
            svg_data = svg_data.replace('currentColor', self.icon_color)
            renderer = QSvgRenderer(QByteArray(svg_data.encode()))
            pixmap = QPixmap(self.icon_size, self.icon_size)
            pixmap.fill(Qt.GlobalColor.transparent)
            painter = QPainter(pixmap)
            renderer.render(painter)
            painter.end()
            self.setPixmap(pixmap)


class RippleEffect:
    """水波纹效果数据"""
    def __init__(self, center: QPoint, max_radius: float):
        self.center = center
        self.max_radius = max_radius
        self.current_radius = 0.0
        self.opacity = 0.4


class CategoryButton(QWidget):
    """分类按钮 - 带左侧高亮条和水波纹效果"""
    
    clicked = Signal()
    
    def __init__(self, icon_name: str, tooltip: str, parent=None):
        super().__init__(parent)
        self.icon_name = icon_name
        self._checked = False
        self._hovered = False
        self._pressed = False
        self.setFixedSize(80, 56)  # 放大按钮
        self.setToolTip(tooltip)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # 水波纹效果
        self._ripples = []
        self._ripple_timer = QTimer(self)
        self._ripple_timer.timeout.connect(self._update_ripples)
        
        # 图标 - 放大
        self.icon_widget = IconWidget(icon_name, 28, "#94a3b8", self)
        self.icon_widget.move(26, 14)
    
    def setChecked(self, checked: bool):
        self._checked = checked
        self.update_style()
        self.update()
    
    def isChecked(self) -> bool:
        return self._checked
    
    def update_style(self):
        if self._checked:
            self.icon_widget.set_color("#fbbf24")
        elif self._hovered:
            self.icon_widget.set_color("#fbbf24")
        else:
            self.icon_widget.set_color("#94a3b8")
    
    def enterEvent(self, event):
        self._hovered = True
        self.update_style()
        self.update()
    
    def leaveEvent(self, event):
        self._hovered = False
        self.update_style()
        self.update()
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._pressed = True
            # 创建水波纹
            self._create_ripple(event.pos())
            self.update()
    
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._pressed = False
            if self.rect().contains(event.pos()):
                self.clicked.emit()
            self.update()
    
    def _create_ripple(self, pos: QPoint):
        """创建水波纹效果"""
        # 计算最大半径
        distances = [
            (pos - QPoint(0, 0)).manhattanLength(),
            (pos - QPoint(self.width(), 0)).manhattanLength(),
            (pos - QPoint(0, self.height())).manhattanLength(),
            (pos - QPoint(self.width(), self.height())).manhattanLength()
        ]
        max_radius = max(distances) * 0.8
        
        ripple = RippleEffect(pos, max_radius)
        self._ripples.append(ripple)
        
        if not self._ripple_timer.isActive():
            self._ripple_timer.start(16)  # ~60fps
    
    def _update_ripples(self):
        """更新水波纹动画"""
        to_remove = []
        for ripple in self._ripples:
            ripple.current_radius += ripple.max_radius * 0.08
            ripple.opacity -= 0.025
            
            if ripple.opacity <= 0:
                to_remove.append(ripple)
        
        for ripple in to_remove:
            self._ripples.remove(ripple)
        
        if not self._ripples:
            self._ripple_timer.stop()
        
        self.update()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 绘制按钮背景
        btn_rect = self.rect().adjusted(12, 4, -12, -4)
        
        if self._checked:
            # 选中背景
            painter.setBrush(QColor(251, 191, 36, 30))  # cheese-400/20
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(btn_rect, 14, 14)
            
            # 左侧高亮条
            indicator_height = int(self.height() * 0.6)
            indicator_y = (self.height() - indicator_height) // 2
            
            # 发光效果
            glow_color = QColor(251, 191, 36, 80)
            painter.setBrush(glow_color)
            painter.drawRoundedRect(0, indicator_y - 2, 6, indicator_height + 4, 3, 3)
            
            # 实体条
            painter.setBrush(QColor("#fbbf24"))
            painter.drawRoundedRect(0, indicator_y, 4, indicator_height, 2, 2)
            
        elif self._hovered:
            painter.setBrush(QColor(51, 65, 85, 128))  # darkbg-700/50
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(btn_rect, 14, 14)
        
        # 绘制水波纹
        if self._ripples:
            painter.save()
            # 创建裁剪区域
            path = QPainterPath()
            path.addRoundedRect(btn_rect.x(), btn_rect.y(), btn_rect.width(), btn_rect.height(), 14, 14)
            painter.setClipPath(path)
            
            for ripple in self._ripples:
                color = QColor(251, 191, 36, int(ripple.opacity * 255))
                gradient = QRadialGradient(ripple.center.x(), ripple.center.y(), ripple.current_radius)
                gradient.setColorAt(0, QColor(251, 191, 36, 0))
                gradient.setColorAt(0.5, color)
                gradient.setColorAt(1, QColor(251, 191, 36, 0))
                
                painter.setBrush(gradient)
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawEllipse(
                    ripple.center, 
                    int(ripple.current_radius), 
                    int(ripple.current_radius)
                )
            painter.restore()


class LogoButton(QWidget):
    """Logo按钮 - 使用图片，无背景，带水波纹效果"""
    
    clicked = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(60, 60)  # 放大
        self.setToolTip("点击查看个人信息")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._hovered = False
        self._pressed = False
        self._logo_pixmap = None
        self._scale = 1.0
        
        # 水波纹效果
        self._ripples = []
        self._ripple_timer = QTimer(self)
        self._ripple_timer.timeout.connect(self._update_ripples)
        
        # 悬停缩放动画
        self._scale_anim = QPropertyAnimation(self, b"scale_factor")
        self._scale_anim.setDuration(150)
        self._scale_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        self._load_logo()
    
    def get_scale_factor(self):
        return self._scale
    
    def set_scale_factor(self, value):
        self._scale = value
        self.update()
    
    # 使用 PySide6 Property 以支持动画
    scale_factor = Property(float, get_scale_factor, set_scale_factor)
    
    def _load_logo(self):
        """加载Logo图片"""
        if os.path.exists(LOGO_IMAGE_PATH):
            self._logo_pixmap = QPixmap(LOGO_IMAGE_PATH)
            if not self._logo_pixmap.isNull():
                # 缩放到合适大小
                self._logo_pixmap = self._logo_pixmap.scaled(
                    56, 56,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
    
    def enterEvent(self, event):
        self._hovered = True
        self._scale_anim.stop()
        self._scale_anim.setStartValue(self._scale)
        self._scale_anim.setEndValue(1.1)
        self._scale_anim.start()
        self.update()
    
    def leaveEvent(self, event):
        self._hovered = False
        self._scale_anim.stop()
        self._scale_anim.setStartValue(self._scale)
        self._scale_anim.setEndValue(1.0)
        self._scale_anim.start()
        self.update()
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._pressed = True
            self._create_ripple(event.pos())
            self.update()
    
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._pressed = False
            if self.rect().contains(event.pos()):
                self.clicked.emit()
            self.update()
    
    def _create_ripple(self, pos: QPoint):
        """创建水波纹效果"""
        max_radius = max(self.width(), self.height())
        ripple = RippleEffect(pos, max_radius)
        self._ripples.append(ripple)
        
        if not self._ripple_timer.isActive():
            self._ripple_timer.start(16)
    
    def _update_ripples(self):
        """更新水波纹动画"""
        to_remove = []
        for ripple in self._ripples:
            ripple.current_radius += ripple.max_radius * 0.1
            ripple.opacity -= 0.03
            
            if ripple.opacity <= 0:
                to_remove.append(ripple)
        
        for ripple in to_remove:
            self._ripples.remove(ripple)
        
        if not self._ripples:
            self._ripple_timer.stop()
        
        self.update()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        
        center = self.rect().center()
        
        # 绘制Logo图片（无背景）
        if self._logo_pixmap and not self._logo_pixmap.isNull():
            # 应用缩放
            scaled_size = int(self._logo_pixmap.width() * self._scale)
            scaled_pixmap = self._logo_pixmap.scaled(
                scaled_size, scaled_size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            
            x = center.x() - scaled_pixmap.width() // 2
            y = center.y() - scaled_pixmap.height() // 2
            
            # 悬停时添加发光效果
            if self._hovered:
                glow_rect = self.rect().adjusted(-4, -4, 4, 4)
                glow = QRadialGradient(center.x(), center.y(), 40)
                glow.setColorAt(0, QColor(251, 191, 36, 60))
                glow.setColorAt(0.7, QColor(251, 191, 36, 30))
                glow.setColorAt(1, QColor(251, 191, 36, 0))
                painter.setBrush(glow)
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawEllipse(center, 36, 36)
            
            painter.drawPixmap(x, y, scaled_pixmap)
            
            # 绘制水波纹
            if self._ripples:
                painter.save()
                # 圆形裁剪
                path = QPainterPath()
                path.addEllipse(center.x() - 28, center.y() - 28, 56, 56)
                painter.setClipPath(path)
                
                for ripple in self._ripples:
                    color = QColor(251, 191, 36, int(ripple.opacity * 200))
                    gradient = QRadialGradient(ripple.center.x(), ripple.center.y(), ripple.current_radius)
                    gradient.setColorAt(0, QColor(251, 191, 36, 0))
                    gradient.setColorAt(0.6, color)
                    gradient.setColorAt(1, QColor(251, 191, 36, 0))
                    
                    painter.setBrush(gradient)
                    painter.setPen(Qt.PenStyle.NoPen)
                    painter.drawEllipse(
                        ripple.center, 
                        int(ripple.current_radius), 
                        int(ripple.current_radius)
                    )
                painter.restore()
        else:
            # 如果图片加载失败，使用emoji作为备选
            painter.setPen(QColor("#fbbf24"))
            font = QFont("Segoe UI Emoji", 28)
            painter.setFont(font)
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "🧀")


class PrimarySidebar(QWidget):
    """左侧一级菜单"""
    
    category_changed = Signal(str)
    settings_clicked = Signal()
    logo_clicked = Signal()  # 新增：Logo点击信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("primary_sidebar")
        self.setFixedWidth(80)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 20, 0, 24)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        
        # Logo - 点击弹出个人信息卡片
        self.logo_btn = LogoButton()
        self.logo_btn.clicked.connect(self.logo_clicked.emit)
        layout.addWidget(self.logo_btn, 0, Qt.AlignmentFlag.AlignHCenter)
        
        layout.addSpacing(28)
        
        # 分类按钮
        self.image_btn = CategoryButton("image", "图片工具")
        self.image_btn.setChecked(True)
        self.image_btn.clicked.connect(lambda: self._on_category_click("image"))
        layout.addWidget(self.image_btn)
        
        self.pdf_btn = CategoryButton("file-pdf", "PDF 工具箱")
        self.pdf_btn.clicked.connect(lambda: self._on_category_click("pdf"))
        layout.addWidget(self.pdf_btn)
        
        self.excel_btn = CategoryButton("file-xls", "Excel 表格")
        self.excel_btn.clicked.connect(lambda: self._on_category_click("excel"))
        layout.addWidget(self.excel_btn)
        
        self.buttons = {
            "image": self.image_btn,
            "pdf": self.pdf_btn,
            "excel": self.excel_btn
        }
        
        layout.addStretch()
        
        # 设置按钮
        self.settings_btn = CategoryButton("gear", "设置 / 日志查看")
        self.settings_btn.clicked.connect(self.settings_clicked.emit)
        layout.addWidget(self.settings_btn)
    
    def _on_category_click(self, category: str):
        for cat, btn in self.buttons.items():
            btn.setChecked(cat == category)
        self.category_changed.emit(category)
    
    def set_category(self, category: str):
        for cat, btn in self.buttons.items():
            btn.setChecked(cat == category)
