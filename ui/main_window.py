"""
主窗口 - 三栏布局
- 左侧: 一级菜单(80px)
- 中间: 二级菜单(256px)
- 右侧: 工作区(弹性宽度)
"""
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QStackedWidget, QGraphicsOpacityEffect
)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont
import logging

from ui.sidebar import PrimarySidebar
from ui.tool_list import SecondarySidebar, TOOLS_DATA
from ui.workspace import WelcomeWorkspace
from ui.settings import SettingsPage
from ui.animations import animate_widget_show
from ui.profile_card import ProfileCard
from core.config import config


class MainWindow(QMainWindow):
    """主窗口"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("奶酪云工具箱 | Cheese Cloud Tools")
        self.setMinimumSize(1200, 700)
        self.resize(1400, 800)
        
        # 工具页面映射
        self.tool_pages = {}
        
        self.setup_ui()
        self.setup_connections()
        
        logging.info("主窗口初始化完成")
    
    def setup_ui(self):
        """设置UI"""
        # 中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 1. 左侧一级菜单
        self.primary_sidebar = PrimarySidebar()
        main_layout.addWidget(self.primary_sidebar)
        
        # 2. 中间二级菜单
        self.secondary_sidebar = SecondarySidebar()
        main_layout.addWidget(self.secondary_sidebar)
        
        # 3. 右侧工作区(使用堆叠窗口切换不同工具页面)
        self.workspace_stack = QStackedWidget()
        self.workspace_stack.setObjectName("workspace")
        main_layout.addWidget(self.workspace_stack, 1)
        
        # 添加欢迎页
        self.welcome_page = WelcomeWorkspace()
        self.workspace_stack.addWidget(self.welcome_page)
        
        # 添加设置页面
        self.settings_page = SettingsPage()
        self.workspace_stack.addWidget(self.settings_page)
        
        # 延迟导入并添加工具页面
        self.init_tool_pages()
    
    def init_tool_pages(self):
        """初始化所有工具页面"""
        # 图片工具
        from tools.image.compress import ImageCompressPage
        from tools.image.convert import ImageConvertPage
        from tools.image.watermark import ImageWatermarkPage
        
        self.tool_pages["img-compress"] = ImageCompressPage()
        self.tool_pages["img-convert"] = ImageConvertPage()
        self.tool_pages["img-watermark"] = ImageWatermarkPage()
        
        # PDF工具
        from tools.pdf.split import PDFSplitPage
        from tools.pdf.merge import PDFMergePage
        from tools.pdf.to_word import PDFToWordPage
        
        self.tool_pages["pdf-split"] = PDFSplitPage()
        self.tool_pages["pdf-merge"] = PDFMergePage()
        self.tool_pages["pdf-word"] = PDFToWordPage()
        
        # Excel工具
        from tools.excel.preview import ExcelPreviewPage
        from tools.excel.chart import ExcelChartPage
        
        self.tool_pages["xls-view"] = ExcelPreviewPage()
        self.tool_pages["xls-chart"] = ExcelChartPage()
        
        # 添加到堆叠窗口
        for page in self.tool_pages.values():
            self.workspace_stack.addWidget(page)
    
    def setup_connections(self):
        """设置信号连接"""
        # 一级菜单切换
        self.primary_sidebar.category_changed.connect(self.on_category_changed)
        self.primary_sidebar.settings_clicked.connect(self.show_settings)
        self.primary_sidebar.logo_clicked.connect(self.show_profile_card)
        
        # 二级菜单工具选择
        self.secondary_sidebar.tool_selected.connect(self.on_tool_selected)
        
        # 欢迎页快捷入口
        self.welcome_page.tool_clicked.connect(self.on_shortcut_clicked)
    
    def on_category_changed(self, category: str):
        """分类切换"""
        logging.debug(f"切换分类: {category}")
        self.secondary_sidebar.load_tools(category)
        # 显示欢迎页
        self._switch_page(self.welcome_page)
    
    def on_tool_selected(self, tool_data: dict):
        """工具选择"""
        tool_id = tool_data.get("id")
        logging.info(f"选择工具: {tool_data.get('name')} ({tool_id})")
        
        if tool_id in self.tool_pages:
            page = self.tool_pages[tool_id]
            # 设置面包屑
            category_title = TOOLS_DATA.get(self.secondary_sidebar.current_category, {}).get("title", "")
            page.set_breadcrumb(category_title, tool_data.get("name", ""))
            page.set_title(tool_data.get("name", ""))
            
            self._switch_page(page)
        else:
            logging.warning(f"未找到工具页面: {tool_id}")
    
    def on_shortcut_clicked(self, tool_id: str, category: str):
        """快捷入口点击"""
        logging.debug(f"快捷入口: {tool_id}, {category}")
        self.primary_sidebar.set_category(category)
        self.secondary_sidebar.load_tools(category)
        self.secondary_sidebar.select_tool(tool_id)
    
    def show_settings(self):
        """显示设置页面"""
        logging.debug("打开设置页面")
        self._switch_page(self.settings_page)
    
    def show_profile_card(self):
        """显示个人信息卡片"""
        logging.debug("打开个人信息卡片")
        dialog = ProfileCard(self)
        dialog.exec()
    
    def _switch_page(self, page: QWidget):
        """切换页面（带动画）"""
        if not config.get("animation_enabled", True):
            self.workspace_stack.setCurrentWidget(page)
            return
        
        # 获取当前页面
        current = self.workspace_stack.currentWidget()
        if current == page:
            return
        
        # 设置新页面透明度效果
        effect = QGraphicsOpacityEffect(page)
        effect.setOpacity(0)
        page.setGraphicsEffect(effect)
        
        # 切换页面
        self.workspace_stack.setCurrentWidget(page)
        
        # 渐入动画
        duration = config.get("animation_duration", 300)
        anim = QPropertyAnimation(effect, b"opacity")
        anim.setDuration(duration)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        # 保持引用防止被垃圾回收
        page._fade_anim = anim
        anim.start()
