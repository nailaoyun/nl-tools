"""
右侧工作区基类
- 装饰性背景光晕
- 毛玻璃效果头部
- 面包屑导航 + 版本标签
- 上传区域(虚线边框+图标)
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QFrame, QScrollArea, QFileDialog, QGraphicsDropShadowEffect,
    QGraphicsBlurEffect
)
from PySide6.QtCore import Signal, Qt, QSize
from PySide6.QtGui import (
    QFont, QDragEnterEvent, QDropEvent, QPainter, 
    QColor, QRadialGradient, QLinearGradient, QPen, QBrush
)


class BackgroundDecoration(QWidget):
    """装饰性背景 - 渐变光晕"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 右上角奶酪色光晕
        gradient1 = QRadialGradient(
            self.width() + 50, -50,  # 圆心
            500  # 半径
        )
        gradient1.setColorAt(0, QColor(251, 191, 36, 25))  # cheese-500/10
        gradient1.setColorAt(1, QColor(251, 191, 36, 0))
        painter.setBrush(gradient1)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(
            int(self.width() * 0.5), int(-self.height() * 0.2),
            int(self.width() * 0.7), int(self.height() * 0.7)
        )
        
        # 左侧紫色光晕
        gradient2 = QRadialGradient(
            self.width() * 0.1, self.height() * 0.3,
            350
        )
        gradient2.setColorAt(0, QColor(139, 92, 246, 12))  # purple-500/5
        gradient2.setColorAt(1, QColor(139, 92, 246, 0))
        painter.setBrush(gradient2)
        painter.drawEllipse(
            int(-self.width() * 0.1), int(self.height() * 0.1),
            int(self.width() * 0.5), int(self.height() * 0.5)
        )


class UploadArea(QFrame):
    """上传区域 - 还原HTML设计样式"""
    
    files_dropped = Signal(list)
    
    def __init__(self, accept_types: str = "所有文件", parent=None):
        super().__init__(parent)
        self.accept_types = accept_types
        self.setAcceptDrops(True)
        self.setMinimumHeight(208)  # h-52 = 13rem = 208px
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._hovered = False
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(12)
        
        # 图标容器 (圆形背景)
        self.icon_container = QFrame()
        self.icon_container.setFixedSize(56, 56)
        self.icon_container.setStyleSheet("""
            background: #334155;
            border-radius: 28px;
        """)
        icon_layout = QVBoxLayout(self.icon_container)
        icon_layout.setContentsMargins(0, 0, 0, 0)
        icon_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 云上传图标
        icon_label = QLabel("☁️")
        icon_label.setFont(QFont("Segoe UI Emoji", 24))
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet("background: transparent;")
        icon_layout.addWidget(icon_label)
        
        layout.addWidget(self.icon_container, 0, Qt.AlignmentFlag.AlignCenter)
        
        # 主文字
        self.title_label = QLabel("点击或拖拽文件到此处")
        self.title_label.setStyleSheet("color: white; font-size: 16px; font-weight: 500; background: transparent;")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.title_label)
        
        # 副文字
        self.desc_label = QLabel(f"支持批量上传 ({self.accept_types})")
        self.desc_label.setStyleSheet("color: #64748b; font-size: 13px; background: transparent;")
        self.desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.desc_label)
        
        self.update_style()
    
    def update_style(self):
        if self._hovered:
            self.setStyleSheet("""
                UploadArea {
                    background: rgba(30, 41, 59, 0.5);
                    border: 2px dashed rgba(251, 191, 36, 0.5);
                    border-radius: 16px;
                }
            """)
        else:
            self.setStyleSheet("""
                UploadArea {
                    background: rgba(30, 41, 59, 0.3);
                    border: 2px dashed #334155;
                    border-radius: 16px;
                }
            """)
    
    def enterEvent(self, event):
        self._hovered = True
        self.update_style()
    
    def leaveEvent(self, event):
        self._hovered = False
        self.update_style()
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.open_file_dialog()
    
    def open_file_dialog(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "选择文件", "", f"{self.accept_types}"
        )
        if files:
            self.files_dropped.emit(files)
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self._hovered = True
            self.update_style()
    
    def dragLeaveEvent(self, event):
        self._hovered = False
        self.update_style()
    
    def dropEvent(self, event: QDropEvent):
        self._hovered = False
        self.update_style()
        files = []
        for url in event.mimeData().urls():
            if url.isLocalFile():
                files.append(url.toLocalFile())
        if files:
            self.files_dropped.emit(files)


class GlassHeader(QFrame):
    """毛玻璃效果头部"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(80)
        self.setStyleSheet("""
            GlassHeader {
                background: rgba(30, 41, 59, 0.7);
                border-bottom: 1px solid rgba(51, 65, 85, 0.3);
            }
        """)


class BaseWorkspace(QWidget):
    """工作区基类"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("workspace")
        self.setup_base_ui()
    
    def setup_base_ui(self):
        # 主布局
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # 背景装饰层
        self.bg_decoration = BackgroundDecoration(self)
        
        # 头部区域
        self.header = GlassHeader()
        header_layout = QVBoxLayout(self.header)
        header_layout.setContentsMargins(32, 16, 32, 16)
        header_layout.setSpacing(4)
        
        # 面包屑
        breadcrumb_layout = QHBoxLayout()
        breadcrumb_layout.setSpacing(8)
        
        self.breadcrumb_category = QLabel("首页")
        self.breadcrumb_category.setStyleSheet("color: #64748b; font-size: 12px;")
        breadcrumb_layout.addWidget(self.breadcrumb_category)
        
        arrow = QLabel("›")
        arrow.setStyleSheet("color: #64748b; font-size: 12px;")
        breadcrumb_layout.addWidget(arrow)
        
        self.breadcrumb_tool = QLabel("控制台")
        self.breadcrumb_tool.setStyleSheet("color: #fbbf24; font-size: 12px;")
        breadcrumb_layout.addWidget(self.breadcrumb_tool)
        
        breadcrumb_layout.addStretch()
        header_layout.addLayout(breadcrumb_layout)
        
        # 标题行
        title_layout = QHBoxLayout()
        
        # 标题 + 版本标签
        title_container = QHBoxLayout()
        title_container.setSpacing(8)
        
        self.title_label = QLabel("欢迎回来")
        self.title_label.setStyleSheet("color: white; font-size: 22px; font-weight: 700;")
        title_container.addWidget(self.title_label)
        
        self.version_label = QLabel("v2.1")
        self.version_label.setStyleSheet("""
            color: #64748b;
            font-size: 12px;
            background: #1e293b;
            border: 1px solid #334155;
            border-radius: 4px;
            padding: 2px 8px;
        """)
        self.version_label.setVisible(False)
        title_container.addWidget(self.version_label)
        title_container.addStretch()
        
        title_layout.addLayout(title_container, 1)
        
        # 按钮区域
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        
        self.history_btn = QPushButton("🕐 历史")
        self.history_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: 1px solid #334155;
                border-radius: 8px;
                color: #cbd5e1;
                padding: 8px 16px;
                font-size: 13px;
            }
            QPushButton:hover {
                background: #334155;
            }
        """)
        btn_layout.addWidget(self.history_btn)
        
        self.export_btn = QPushButton("📤 导出")
        self.export_btn.setStyleSheet("""
            QPushButton {
                background: #f59e0b;
                border: none;
                border-radius: 8px;
                color: white;
                padding: 8px 16px;
                font-size: 13px;
                font-weight: 500;
            }
            QPushButton:hover {
                background: #fbbf24;
            }
        """)
        btn_layout.addWidget(self.export_btn)
        
        title_layout.addLayout(btn_layout)
        header_layout.addLayout(title_layout)
        
        self.main_layout.addWidget(self.header)
        
        # 内容区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setStyleSheet("background: transparent;")
        
        self.content_widget = QWidget()
        self.content_widget.setStyleSheet("background: transparent;")
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(32, 24, 32, 24)
        self.content_layout.setSpacing(24)
        
        scroll_area.setWidget(self.content_widget)
        self.main_layout.addWidget(scroll_area, 1)
    
    def resizeEvent(self, event):
        super().resizeEvent(event)
        # 调整背景装饰大小
        self.bg_decoration.setGeometry(0, 0, self.width(), self.height())
        self.bg_decoration.lower()
    
    def set_breadcrumb(self, category: str, tool: str):
        self.breadcrumb_category.setText(category)
        self.breadcrumb_tool.setText(tool)
    
    def set_title(self, title: str):
        self.title_label.setText(title)
        self.version_label.setVisible(bool(title and title != "欢迎回来"))
    
    def clear_content(self):
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()


class ShortcutCard(QFrame):
    """快捷入口卡片"""
    
    clicked = Signal()
    
    def __init__(self, data: dict, parent=None):
        super().__init__(parent)
        self.data = data
        self.setFixedSize(200, 140)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._hovered = False
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)
        
        # 图标
        color = self.data.get("color", "#64748b")
        self.icon_frame = QFrame()
        self.icon_frame.setFixedSize(40, 40)
        r, g, b = self.hex_to_rgb(color)
        self.icon_frame.setStyleSheet(f"""
            background: rgba({r}, {g}, {b}, 0.1);
            border-radius: 8px;
        """)
        icon_layout = QVBoxLayout(self.icon_frame)
        icon_layout.setContentsMargins(0, 0, 0, 0)
        icon_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        icon = QLabel(self.data.get("icon", ""))
        icon.setFont(QFont("Segoe UI Emoji", 16))
        icon.setStyleSheet(f"color: {color}; background: transparent;")
        icon_layout.addWidget(icon)
        
        layout.addWidget(self.icon_frame)
        
        # 名称
        name = QLabel(self.data.get("name", ""))
        name.setStyleSheet("color: white; font-size: 14px; font-weight: 500;")
        layout.addWidget(name)
        
        # 描述
        desc = QLabel(self.data.get("desc", ""))
        desc.setStyleSheet("color: #64748b; font-size: 11px;")
        layout.addWidget(desc)
        
        layout.addStretch()
        self.update_style()
    
    def update_style(self):
        if self._hovered:
            self.setStyleSheet("""
                ShortcutCard {
                    background: rgba(30, 41, 59, 0.8);
                    border: 1px solid rgba(251, 191, 36, 0.5);
                    border-radius: 16px;
                }
            """)
        else:
            self.setStyleSheet("""
                ShortcutCard {
                    background: rgba(30, 41, 59, 0.5);
                    border: 1px solid #334155;
                    border-radius: 16px;
                }
            """)
    
    def enterEvent(self, event):
        self._hovered = True
        self.update_style()
    
    def leaveEvent(self, event):
        self._hovered = False
        self.update_style()
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
    
    @staticmethod
    def hex_to_rgb(hex_color: str) -> tuple:
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


class WelcomeWorkspace(BaseWorkspace):
    """欢迎页面工作区"""
    
    tool_clicked = Signal(str, str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_welcome_ui()
    
    def setup_welcome_ui(self):
        self.set_breadcrumb("首页", "控制台")
        self.set_title("欢迎回来")
        self.version_label.setVisible(False)
        
        self.history_btn.hide()
        self.export_btn.hide()
        
        # 中心内容
        center_widget = QWidget()
        center_layout = QVBoxLayout(center_widget)
        center_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        center_layout.setSpacing(24)
        
        # Logo区域
        logo_container = QFrame()
        logo_container.setFixedSize(128, 128)
        logo_container.setStyleSheet("""
            background: #1e293b;
            border: 1px solid #334155;
            border-radius: 64px;
        """)
        logo_layout = QVBoxLayout(logo_container)
        logo_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        logo = QLabel("🧀")
        logo.setFont(QFont("Segoe UI Emoji", 48))
        logo.setStyleSheet("color: #fbbf24; background: transparent;")
        logo_layout.addWidget(logo)
        
        center_layout.addWidget(logo_container, 0, Qt.AlignmentFlag.AlignCenter)
        
        # 标题
        title = QLabel("开始你的创作")
        title.setFont(QFont("Microsoft YaHei", 28, QFont.Weight.Bold))
        title.setStyleSheet("color: white;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        center_layout.addWidget(title)
        
        # 描述
        desc = QLabel("从左侧选择一个工具。无论是压缩图片、拆分PDF还是处理数据，我们都能搞定。")
        desc.setStyleSheet("color: #94a3b8; font-size: 14px;")
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setWordWrap(True)
        desc.setMaximumWidth(500)
        center_layout.addWidget(desc)
        
        center_layout.addSpacing(20)
        
        # 快捷入口
        shortcuts_layout = QHBoxLayout()
        shortcuts_layout.setSpacing(16)
        shortcuts_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        shortcuts = [
            {"id": "img-compress", "category": "image", "name": "图片压缩", "desc": "智能无损压缩", "icon": "🖼", "color": "#3b82f6"},
            {"id": "pdf-split", "category": "pdf", "name": "PDF 拆分", "desc": "提取特定页面", "icon": "✂️", "color": "#ef4444"},
            {"id": "img-convert", "category": "image", "name": "格式转换", "desc": "格式互转工具", "icon": "🔄", "color": "#22c55e"},
        ]
        
        for item in shortcuts:
            card = ShortcutCard(item)
            card.clicked.connect(lambda i=item: self.tool_clicked.emit(i["id"], i["category"]))
            shortcuts_layout.addWidget(card)
        
        center_layout.addLayout(shortcuts_layout)
        
        self.content_layout.addStretch()
        self.content_layout.addWidget(center_widget)
        self.content_layout.addStretch()
