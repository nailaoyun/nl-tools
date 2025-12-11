"""
UI动画效果模块
- 渐入渐出
- 滑动效果
- 缩放效果
"""
from PySide6.QtWidgets import QWidget, QGraphicsOpacityEffect
from PySide6.QtCore import (
    QPropertyAnimation, QEasingCurve, QParallelAnimationGroup,
    QSequentialAnimationGroup, Property, QPoint, QSize
)
from PySide6.QtGui import QColor

from core.config import config


class AnimationMixin:
    """动画混入类，为QWidget添加动画功能"""
    
    def setup_animation(self):
        """初始化动画效果"""
        if not hasattr(self, '_opacity_effect'):
            self._opacity_effect = QGraphicsOpacityEffect(self)
            self._opacity_effect.setOpacity(1.0)
            self.setGraphicsEffect(self._opacity_effect)
    
    def fade_in(self, duration: int = None, callback=None):
        """渐入动画"""
        if not config.get("animation_enabled", True):
            if callback:
                callback()
            return
        
        self.setup_animation()
        duration = duration or config.get("animation_duration", 300)
        
        self._opacity_effect.setOpacity(0)
        self.show()
        
        self._fade_anim = QPropertyAnimation(self._opacity_effect, b"opacity")
        self._fade_anim.setDuration(duration)
        self._fade_anim.setStartValue(0.0)
        self._fade_anim.setEndValue(1.0)
        self._fade_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        if callback:
            self._fade_anim.finished.connect(callback)
        
        self._fade_anim.start()
    
    def fade_out(self, duration: int = None, callback=None):
        """渐出动画"""
        if not config.get("animation_enabled", True):
            self.hide()
            if callback:
                callback()
            return
        
        self.setup_animation()
        duration = duration or config.get("animation_duration", 300)
        
        self._fade_anim = QPropertyAnimation(self._opacity_effect, b"opacity")
        self._fade_anim.setDuration(duration)
        self._fade_anim.setStartValue(1.0)
        self._fade_anim.setEndValue(0.0)
        self._fade_anim.setEasingCurve(QEasingCurve.Type.InCubic)
        
        def on_finished():
            self.hide()
            self._opacity_effect.setOpacity(1.0)
            if callback:
                callback()
        
        self._fade_anim.finished.connect(on_finished)
        self._fade_anim.start()


def create_fade_animation(widget: QWidget, fade_in: bool = True, duration: int = None) -> QPropertyAnimation:
    """创建渐变动画"""
    if not config.get("animation_enabled", True):
        return None
    
    duration = duration or config.get("animation_duration", 300)
    
    # 确保有透明度效果
    effect = widget.graphicsEffect()
    if not isinstance(effect, QGraphicsOpacityEffect):
        effect = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(effect)
    
    anim = QPropertyAnimation(effect, b"opacity")
    anim.setDuration(duration)
    
    if fade_in:
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
    else:
        anim.setStartValue(1.0)
        anim.setEndValue(0.0)
        anim.setEasingCurve(QEasingCurve.Type.InCubic)
    
    return anim


def create_slide_animation(widget: QWidget, start_pos: QPoint, end_pos: QPoint, 
                          duration: int = None) -> QPropertyAnimation:
    """创建滑动动画"""
    if not config.get("animation_enabled", True):
        widget.move(end_pos)
        return None
    
    duration = duration or config.get("animation_duration", 300)
    
    anim = QPropertyAnimation(widget, b"pos")
    anim.setDuration(duration)
    anim.setStartValue(start_pos)
    anim.setEndValue(end_pos)
    anim.setEasingCurve(QEasingCurve.Type.OutCubic)
    
    return anim


def animate_widget_show(widget: QWidget, direction: str = "fade"):
    """显示控件动画"""
    if not config.get("animation_enabled", True):
        widget.show()
        return
    
    duration = config.get("animation_duration", 300)
    
    if direction == "fade":
        effect = QGraphicsOpacityEffect(widget)
        effect.setOpacity(0)
        widget.setGraphicsEffect(effect)
        widget.show()
        
        anim = QPropertyAnimation(effect, b"opacity")
        anim.setDuration(duration)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim.start()
        
        # 保持引用
        widget._show_anim = anim
    else:
        widget.show()


def animate_widget_hide(widget: QWidget, callback=None):
    """隐藏控件动画"""
    if not config.get("animation_enabled", True):
        widget.hide()
        if callback:
            callback()
        return
    
    duration = config.get("animation_duration", 300)
    
    effect = widget.graphicsEffect()
    if not isinstance(effect, QGraphicsOpacityEffect):
        effect = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(effect)
    
    anim = QPropertyAnimation(effect, b"opacity")
    anim.setDuration(duration)
    anim.setStartValue(1.0)
    anim.setEndValue(0.0)
    anim.setEasingCurve(QEasingCurve.Type.InCubic)
    
    def on_finished():
        widget.hide()
        effect.setOpacity(1.0)
        if callback:
            callback()
    
    anim.finished.connect(on_finished)
    anim.start()
    
    # 保持引用
    widget._hide_anim = anim

