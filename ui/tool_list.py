"""
中间二级菜单组件
- 分类标题
- 搜索框(带图标)
- 工具列表(图标+名称+描述)
- 用户信息
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QButtonGroup, QScrollArea, QFrame, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QFont, QColor, QPainter, QLinearGradient
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtCore import QByteArray


# 工具图标 SVG
TOOL_ICONS = {
    "ph-arrows-in-line-horizontal": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256"><path fill="currentColor" d="M136 40v176a8 8 0 0 1-16 0V40a8 8 0 0 1 16 0M96 120H35.31l18.35-18.34a8 8 0 0 0-11.32-11.32l-32 32a8 8 0 0 0 0 11.32l32 32a8 8 0 0 0 11.32-11.32L35.31 136H96a8 8 0 0 0 0-16m149.66 2.34l-32-32a8 8 0 0 0-11.32 11.32L220.69 120H160a8 8 0 0 0 0 16h60.69l-18.35 18.34a8 8 0 0 0 11.32 11.32l32-32a8 8 0 0 0 0-11.32"/></svg>""",
    "ph-arrows-left-right": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256"><path fill="currentColor" d="m213.66 181.66l-32 32a8 8 0 0 1-11.32-11.32L188.69 184H48a8 8 0 0 1 0-16h140.69l-18.35-18.34a8 8 0 0 1 11.32-11.32l32 32a8 8 0 0 1 0 11.32m-139.32-96a8 8 0 0 0 11.32-11.32L67.31 56H208a8 8 0 0 0 0-16H67.31l18.35-18.34a8 8 0 0 0-11.32-11.32l-32 32a8 8 0 0 0 0 11.32Z"/></svg>""",
    "ph-stamp": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256"><path fill="currentColor" d="M224 224a8 8 0 0 1-8 8H40a8 8 0 0 1 0-16h176a8 8 0 0 1 8 8m0-80v40a16 16 0 0 1-16 16H48a16 16 0 0 1-16-16v-40a16 16 0 0 1 16-16h60.43l-15.52-46.55A40 40 0 0 1 128 32a40 40 0 0 1 35.09 49.45L147.57 128H208a16 16 0 0 1 16 16m-16 0H48v40h160Z"/></svg>""",
    "ph-scissors": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256"><path fill="currentColor" d="M157.73 113.13A8 8 0 0 1 159.82 102L227.48 55.7a8 8 0 0 1 9 13.21l-67.67 46.3a7.92 7.92 0 0 1-4.51 1.4a8 8 0 0 1-6.57-3.48m80.87 85.09a8 8 0 0 1-11.12 2.08L136 137.7l-31.11 21.29a36 36 0 1 1-8.87-12.94l27.46-18.79l-27.46-18.79a36 36 0 1 1 8.87-12.94l123.6 84.59a8 8 0 0 1 2.11 11.1M80 180a20 20 0 1 0-20 20a20 20 0 0 0 20-20m0-104a20 20 0 1 0-20 20a20 20 0 0 0 20-20"/></svg>""",
    "ph-files": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256"><path fill="currentColor" d="M213.66 66.34l-40-40A8 8 0 0 0 168 24H88a16 16 0 0 0-16 16v16H56a16 16 0 0 0-16 16v144a16 16 0 0 0 16 16h112a16 16 0 0 0 16-16v-16h16a16 16 0 0 0 16-16V72a8 8 0 0 0-2.34-5.66M168 216H56V72h76.69L168 107.31Zm32-32h-16v-80a8 8 0 0 0-2.34-5.66l-40-40A8 8 0 0 0 136 56H88V40h76.69L200 75.31Zm-56-32a8 8 0 0 1-8 8H88a8 8 0 0 1 0-16h48a8 8 0 0 1 8 8m0 32a8 8 0 0 1-8 8H88a8 8 0 0 1 0-16h48a8 8 0 0 1 8 8"/></svg>""",
    "ph-microsoft-word-logo": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256"><path fill="currentColor" d="M200 24H72a16 16 0 0 0-16 16v24H40a16 16 0 0 0-16 16v96a16 16 0 0 0 16 16h16v24a16 16 0 0 0 16 16h128a16 16 0 0 0 16-16V40a16 16 0 0 0-16-16m-40 176H72v-24h88a16 16 0 0 0 16-16v-23h24v63Zm0-79h-32V80h32Zm0-57h-32V40h32ZM40 80h88v96H40Zm160 136h-24v-24a16 16 0 0 0-16-16h-32v-55h72Zm0-111h-32V80a16 16 0 0 0-16-16h-12V40h60Zm-104.5 47.8l-9.36 34.14a6 6 0 0 1-11.56.12L68 162.18l-6.58 24.88a6 6 0 1 1-11.58-3.12l12-45a6 6 0 0 1 11.48-.16l7.18 27.14l9.86-36a6 6 0 0 1 11.56 0l9.86 36l7.18-27.14a6 6 0 0 1 11.48.16l12 45a6 6 0 1 1-11.58 3.12L124 162.18l-6.54 24.88a6 6 0 0 1-11.56-.12l-9.36-34.14Z"/></svg>""",
    "ph-eye": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256"><path fill="currentColor" d="M247.31 124.76c-.35-.79-8.82-19.58-27.65-38.41C194.57 61.26 162.88 48 128 48S61.43 61.26 36.34 86.35C17.51 105.18 9 124 8.69 124.76a8 8 0 0 0 0 6.5c.35.79 8.82 19.57 27.65 38.4C61.43 194.74 93.12 208 128 208s66.57-13.26 91.66-38.34c18.83-18.83 27.3-37.61 27.65-38.4a8 8 0 0 0 0-6.5M128 192c-30.78 0-57.67-11.19-79.93-33.25A133.47 133.47 0 0 1 25 128a133.33 133.33 0 0 1 23.07-30.75C70.33 75.19 97.22 64 128 64s57.67 11.19 79.93 33.25A133.46 133.46 0 0 1 231.05 128c-7.21 13.46-38.62 64-103.05 64m0-112a48 48 0 1 0 48 48a48.05 48.05 0 0 0-48-48m0 80a32 32 0 1 1 32-32a32 32 0 0 1-32 32"/></svg>""",
    "ph-chart-bar": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256"><path fill="currentColor" d="M224 200h-8V40a8 8 0 0 0-8-8h-56a8 8 0 0 0-8 8v40H96a8 8 0 0 0-8 8v40H48a8 8 0 0 0-8 8v64h-8a8 8 0 0 0 0 16h192a8 8 0 0 0 0-16M160 48h40v152h-40Zm-56 48h40v104h-40Zm-48 48h32v56H56Z"/></svg>""",
    "ph-magnifying-glass": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256"><path fill="currentColor" d="m229.66 218.34l-50.07-50.06a88.11 88.11 0 1 0-11.31 11.31l50.06 50.07a8 8 0 0 0 11.32-11.32M40 112a72 72 0 1 1 72 72a72.08 72.08 0 0 1-72-72"/></svg>""",
}


# 工具数据定义
TOOLS_DATA = {
    "image": {
        "title": "图片工具",
        "items": [
            {"id": "img-compress", "name": "图片压缩", "icon": "ph-arrows-in-line-horizontal", "desc": "智能无损压缩"},
            {"id": "img-convert", "name": "格式转换", "icon": "ph-arrows-left-right", "desc": "JPG/PNG/WEBP"},
            {"id": "img-watermark", "name": "图片加水印", "icon": "ph-stamp", "desc": "批量添加水印"},
        ]
    },
    "pdf": {
        "title": "PDF 工具箱",
        "items": [
            {"id": "pdf-split", "name": "PDF 拆分", "icon": "ph-scissors", "desc": "提取指定页面"},
            {"id": "pdf-merge", "name": "PDF 合并", "icon": "ph-files", "desc": "多文件合并"},
            {"id": "pdf-word", "name": "PDF 转 Word", "icon": "ph-microsoft-word-logo", "desc": "保持排版转换"},
        ]
    },
    "excel": {
        "title": "Excel 表格",
        "items": [
            {"id": "xls-view", "name": "Excel 预览", "icon": "ph-eye", "desc": "在线查看表格"},
            {"id": "xls-chart", "name": "图表生成", "icon": "ph-chart-bar", "desc": "数据可视化"},
        ]
    }
}


def render_svg_icon(svg_data: str, size: int = 18, color: str = "#94a3b8") -> 'QPixmap':
    """渲染SVG图标"""
    from PySide6.QtGui import QPixmap
    svg_data = svg_data.replace('currentColor', color)
    renderer = QSvgRenderer(QByteArray(svg_data.encode()))
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    return pixmap


class ToolButton(QFrame):
    """工具按钮 - 还原HTML设计样式"""
    
    clicked = Signal()
    
    def __init__(self, tool_data: dict, parent=None):
        super().__init__(parent)
        self.tool_data = tool_data
        self._checked = False
        self._hovered = False
        self.setFixedHeight(56)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(12)
        
        # 图标容器
        self.icon_frame = QFrame()
        self.icon_frame.setFixedSize(32, 32)
        self.icon_frame.setStyleSheet("""
            background: #0f172a;
            border: 1px solid #334155;
            border-radius: 6px;
        """)
        icon_layout = QVBoxLayout(self.icon_frame)
        icon_layout.setContentsMargins(0, 0, 0, 0)
        icon_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 图标
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(18, 18)
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        svg_data = TOOL_ICONS.get(self.tool_data.get('icon', ''), '')
        if svg_data:
            self.icon_label.setPixmap(render_svg_icon(svg_data, 18, "#94a3b8"))
        icon_layout.addWidget(self.icon_label)
        
        layout.addWidget(self.icon_frame)
        
        # 文字区域
        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        
        self.name_label = QLabel(self.tool_data.get('name', ''))
        self.name_label.setStyleSheet("color: #e2e8f0; font-size: 13px; font-weight: 500;")
        text_layout.addWidget(self.name_label)
        
        self.desc_label = QLabel(self.tool_data.get('desc', ''))
        self.desc_label.setStyleSheet("color: #64748b; font-size: 10px;")
        text_layout.addWidget(self.desc_label)
        
        layout.addLayout(text_layout, 1)
        
        self.update_style()
    
    def setChecked(self, checked: bool):
        self._checked = checked
        self.update_style()
    
    def isChecked(self) -> bool:
        return self._checked
    
    def update_style(self):
        if self._checked:
            self.setStyleSheet("""
                ToolButton {
                    background: #334155;
                    border-radius: 8px;
                    border-left: 2px solid #fbbf24;
                }
            """)
            self.icon_frame.setStyleSheet("""
                background: #0f172a;
                border: 1px solid rgba(251, 191, 36, 0.3);
                border-radius: 6px;
            """)
            svg_data = TOOL_ICONS.get(self.tool_data.get('icon', ''), '')
            if svg_data:
                self.icon_label.setPixmap(render_svg_icon(svg_data, 18, "#fbbf24"))
            self.name_label.setStyleSheet("color: white; font-size: 13px; font-weight: 500;")
        elif self._hovered:
            self.setStyleSheet("""
                ToolButton {
                    background: rgba(51, 65, 85, 0.5);
                    border-radius: 8px;
                }
            """)
            self.icon_frame.setStyleSheet("""
                background: #0f172a;
                border: 1px solid rgba(251, 191, 36, 0.3);
                border-radius: 6px;
            """)
            svg_data = TOOL_ICONS.get(self.tool_data.get('icon', ''), '')
            if svg_data:
                self.icon_label.setPixmap(render_svg_icon(svg_data, 18, "#fbbf24"))
            self.name_label.setStyleSheet("color: white; font-size: 13px; font-weight: 500;")
        else:
            self.setStyleSheet("""
                ToolButton {
                    background: transparent;
                    border-radius: 8px;
                }
            """)
            self.icon_frame.setStyleSheet("""
                background: #0f172a;
                border: 1px solid #334155;
                border-radius: 6px;
            """)
            svg_data = TOOL_ICONS.get(self.tool_data.get('icon', ''), '')
            if svg_data:
                self.icon_label.setPixmap(render_svg_icon(svg_data, 18, "#94a3b8"))
            self.name_label.setStyleSheet("color: #e2e8f0; font-size: 13px; font-weight: 500;")
    
    def enterEvent(self, event):
        self._hovered = True
        self.update_style()
    
    def leaveEvent(self, event):
        self._hovered = False
        self.update_style()
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()


class SearchInput(QWidget):
    """搜索框 - 带前置图标"""
    
    textChanged = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 容器
        container = QFrame()
        container.setStyleSheet("""
            QFrame {
                background: #0f172a;
                border: 1px solid #334155;
                border-radius: 8px;
            }
            QFrame:focus-within {
                border-color: rgba(251, 191, 36, 0.5);
            }
        """)
        container_layout = QHBoxLayout(container)
        container_layout.setContentsMargins(12, 8, 12, 8)
        container_layout.setSpacing(8)
        
        # 搜索图标
        icon_label = QLabel()
        icon_label.setFixedSize(16, 16)
        svg_data = TOOL_ICONS.get("ph-magnifying-glass", "")
        if svg_data:
            icon_label.setPixmap(render_svg_icon(svg_data, 16, "#64748b"))
        container_layout.addWidget(icon_label)
        
        # 输入框
        self.input = QLineEdit()
        self.input.setPlaceholderText("搜索功能...")
        self.input.setStyleSheet("""
            QLineEdit {
                background: transparent;
                border: none;
                color: #e2e8f0;
                font-size: 13px;
            }
            QLineEdit::placeholder {
                color: #475569;
            }
        """)
        self.input.textChanged.connect(self.textChanged.emit)
        container_layout.addWidget(self.input, 1)
        
        layout.addWidget(container)
    
    def text(self) -> str:
        return self.input.text()


class UserInfoWidget(QFrame):
    """用户信息区 - 渐变头像"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(70)
        self.setStyleSheet("""
            UserInfoWidget {
                background: rgba(30, 41, 59, 0.3);
                border-top: 1px solid rgba(51, 65, 85, 0.5);
            }
        """)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)
        
        # 头像 - 渐变背景
        avatar = QFrame()
        avatar.setFixedSize(36, 36)
        avatar.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #8b5cf6, stop:1 #6366f1);
            border-radius: 18px;
        """)
        avatar_layout = QVBoxLayout(avatar)
        avatar_layout.setContentsMargins(0, 0, 0, 0)
        avatar_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        avatar_text = QLabel("SV")
        avatar_text.setStyleSheet("color: white; font-size: 12px; font-weight: bold; background: transparent;")
        avatar_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar_layout.addWidget(avatar_text)
        
        layout.addWidget(avatar)
        
        # 信息
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)
        
        name_label = QLabel("超级会员")
        name_label.setStyleSheet("color: white; font-size: 12px; font-weight: 500;")
        info_layout.addWidget(name_label)
        
        expire_label = QLabel("有效期至 2026-10")
        expire_label.setStyleSheet("color: #64748b; font-size: 10px;")
        info_layout.addWidget(expire_label)
        
        layout.addLayout(info_layout, 1)


class SecondarySidebar(QWidget):
    """中间二级菜单"""
    
    tool_selected = Signal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("secondary_sidebar")
        self.setFixedWidth(256)
        self.current_category = "image"
        self.tool_buttons = []
        self._stretch_item = None  # 保存stretch引用
        self.setup_ui()
        self.load_tools("image")
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 标题区域
        title_widget = QWidget()
        title_widget.setFixedHeight(80)
        title_widget.setStyleSheet("border-bottom: 1px solid rgba(51, 65, 85, 0.5);")
        title_layout = QVBoxLayout(title_widget)
        title_layout.setContentsMargins(24, 0, 24, 0)
        title_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        
        self.category_title = QLabel("图片工具")
        self.category_title.setStyleSheet("color: white; font-size: 18px; font-weight: 600; letter-spacing: 1px;")
        title_layout.addWidget(self.category_title)
        
        layout.addWidget(title_widget)
        
        # 搜索区域
        search_widget = QWidget()
        search_layout = QVBoxLayout(search_widget)
        search_layout.setContentsMargins(16, 16, 16, 8)
        
        self.search_input = SearchInput()
        self.search_input.textChanged.connect(self.filter_tools)
        search_layout.addWidget(self.search_input)
        
        layout.addWidget(search_widget)
        
        # 工具列表区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setStyleSheet("background: transparent;")
        
        self.tools_container = QWidget()
        self.tools_layout = QVBoxLayout(self.tools_container)
        self.tools_layout.setContentsMargins(12, 4, 12, 16)
        self.tools_layout.setSpacing(4)
        self.tools_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        scroll_area.setWidget(self.tools_container)
        layout.addWidget(scroll_area, 1)
        
        # 用户信息
        layout.addWidget(UserInfoWidget())
    
    def load_tools(self, category: str):
        self.current_category = category
        data = TOOLS_DATA.get(category, {})
        
        self.category_title.setText(data.get("title", ""))
        
        # 清空所有内容（包括stretch）
        for btn in self.tool_buttons:
            self.tools_layout.removeWidget(btn)
            btn.deleteLater()
        self.tool_buttons.clear()
        
        # 移除旧的stretch
        while self.tools_layout.count() > 0:
            item = self.tools_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # 添加工具按钮
        for tool in data.get("items", []):
            btn = ToolButton(tool)
            btn.clicked.connect(lambda t=tool: self.on_tool_clicked(t))
            self.tools_layout.addWidget(btn)
            self.tool_buttons.append(btn)
        
        # 添加新的stretch
        self.tools_layout.addStretch()
    
    def on_tool_clicked(self, tool_data: dict):
        # 更新选中状态
        for btn in self.tool_buttons:
            btn.setChecked(btn.tool_data.get('id') == tool_data.get('id'))
        self.tool_selected.emit(tool_data)
    
    def filter_tools(self, text: str):
        text = text.lower()
        for btn in self.tool_buttons:
            name = btn.tool_data.get("name", "").lower()
            desc = btn.tool_data.get("desc", "").lower()
            btn.setVisible(text in name or text in desc or not text)
    
    def select_tool(self, tool_id: str):
        for btn in self.tool_buttons:
            if btn.tool_data.get("id") == tool_id:
                btn.setChecked(True)
                self.tool_selected.emit(btn.tool_data)
                break
