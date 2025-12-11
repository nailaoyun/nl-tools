"""
UI 模块
- 主窗口
- 侧边栏
- 工作区
- 动画效果
"""
from .main_window import MainWindow
from .sidebar import PrimarySidebar
from .tool_list import SecondarySidebar
from .workspace import BaseWorkspace, WelcomeWorkspace, UploadArea
from .settings import SettingsPage
from .log_viewer import LogViewer
from .image_preview import ImagePreviewWidget, DualPreviewWidget
from .animations import AnimationMixin, animate_widget_show, animate_widget_hide

__all__ = [
    'MainWindow',
    'PrimarySidebar',
    'SecondarySidebar',
    'BaseWorkspace',
    'WelcomeWorkspace',
    'UploadArea',
    'SettingsPage',
    'LogViewer',
    'ImagePreviewWidget',
    'DualPreviewWidget',
    'AnimationMixin',
    'animate_widget_show',
    'animate_widget_hide'
]
