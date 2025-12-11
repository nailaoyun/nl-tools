"""
个人信息卡片模态框
- 头像、微信二维码、邮箱
- 高级UI设计，带装饰元素和动画
"""
import os
from pathlib import Path
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QWidget, QGraphicsOpacityEffect, QApplication
)
from PySide6.QtCore import (
    Qt, QPropertyAnimation, QEasingCurve, QTimer, 
    QPoint, QRect, QParallelAnimationGroup, Signal
)
from PySide6.QtGui import (
    QPixmap, QPainter, QColor, QLinearGradient, QRadialGradient,
    QFont, QPen, QBrush, QPainterPath, QCursor
)
import math


def get_resource_path(relative_path: str) -> str:
    """获取资源文件的绝对路径"""
    base_path = Path(__file__).parent.parent
    return str(base_path / relative_path)


# 资源路径
AVATAR_PATH = get_resource_path("image/头像.jpg")
QRCODE_PATH = get_resource_path("image/二维码.jpg")


class FloatingOrb(QWidget):
    """浮动装饰球"""
    
    def __init__(self, size: int, color: QColor, parent=None):
        super().__init__(parent)
        self.orb_size = size
        self.orb_color = color
        self.setFixedSize(size, size)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        
        # 设置透明效果
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.opacity_effect.setOpacity(0.6)
        self.setGraphicsEffect(self.opacity_effect)
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 径向渐变
        gradient = QRadialGradient(
            self.orb_size / 2, self.orb_size / 2, self.orb_size / 2
        )
        gradient.setColorAt(0, QColor(self.orb_color.red(), self.orb_color.green(), self.orb_color.blue(), 120))
        gradient.setColorAt(0.5, QColor(self.orb_color.red(), self.orb_color.green(), self.orb_color.blue(), 60))
        gradient.setColorAt(1, QColor(self.orb_color.red(), self.orb_color.green(), self.orb_color.blue(), 0))
        
        painter.setBrush(gradient)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(0, 0, self.orb_size, self.orb_size)


class GlowButton(QPushButton):
    """发光按钮"""
    
    def __init__(self, text: str, primary: bool = True, parent=None):
        super().__init__(text, parent)
        self.primary = primary
        self._hovered = False
        self.setFixedHeight(44)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFont(QFont("Microsoft YaHei UI", 10, QFont.Weight.Medium))
        
        self.setStyleSheet("""
            QPushButton {
                border: none;
                border-radius: 10px;
                padding: 10px 24px;
                color: white;
            }
        """)
    
    def enterEvent(self, event):
        self._hovered = True
        self.update()
    
    def leaveEvent(self, event):
        self._hovered = False
        self.update()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        rect = self.rect()
        
        if self.primary:
            # 主按钮 - 奶酪色渐变
            gradient = QLinearGradient(0, 0, rect.width(), 0)
            if self._hovered:
                gradient.setColorAt(0, QColor("#fcd34d"))
                gradient.setColorAt(1, QColor("#f59e0b"))
            else:
                gradient.setColorAt(0, QColor("#fbbf24"))
                gradient.setColorAt(1, QColor("#d97706"))
            
            painter.setBrush(gradient)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(rect, 10, 10)
            
            # 发光效果
            if self._hovered:
                glow = QRadialGradient(rect.center().x(), rect.center().y(), rect.width() / 2)
                glow.setColorAt(0, QColor(251, 191, 36, 60))
                glow.setColorAt(1, QColor(251, 191, 36, 0))
                painter.setBrush(glow)
                painter.drawRoundedRect(rect.adjusted(-5, -5, 5, 5), 15, 15)
        else:
            # 次按钮 - 透明边框
            if self._hovered:
                painter.setBrush(QColor(71, 85, 105, 80))
            else:
                painter.setBrush(QColor(71, 85, 105, 40))
            
            painter.setPen(QPen(QColor("#475569"), 1))
            painter.drawRoundedRect(rect.adjusted(1, 1, -1, -1), 10, 10)
        
        # 绘制文字
        painter.setPen(QColor("white") if self.primary else QColor("#94a3b8"))
        painter.setFont(self.font())
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, self.text())


class ProfileCard(QDialog):
    """个人信息卡片模态框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.Dialog
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setModal(True)
        self.setFixedSize(480, 780)
        
        self._drag_pos = None
        self.setup_ui()
        self.setup_animations()
        self.add_decorations()
    
    def setup_ui(self):
        """设置UI"""
        # 主容器
        self.container = QWidget(self)
        self.container.setGeometry(0, 0, 480, 780)
        
        main_layout = QVBoxLayout(self.container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 内容卡片
        self.card = QWidget()
        self.card.setObjectName("profile_card")
        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(32, 24, 32, 24)
        card_layout.setSpacing(12)
        
        # 关闭按钮
        close_btn = QPushButton("×")
        close_btn.setFixedSize(36, 36)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet("""
            QPushButton {
                background: rgba(71, 85, 105, 0.4);
                border: none;
                border-radius: 18px;
                color: #94a3b8;
                font-size: 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: rgba(239, 68, 68, 0.6);
                color: white;
            }
        """)
        close_btn.clicked.connect(self.close_with_animation)
        
        close_layout = QHBoxLayout()
        close_layout.addStretch()
        close_layout.addWidget(close_btn)
        card_layout.addLayout(close_layout)
        
        # 头像区域
        avatar_container = QWidget()
        avatar_container.setFixedHeight(100)
        avatar_layout = QHBoxLayout(avatar_container)
        avatar_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.avatar_label = QLabel()
        self.avatar_label.setFixedSize(100, 100)
        self.avatar_label.setStyleSheet("""
            QLabel {
                border-radius: 50px;
                border: 3px solid #fbbf24;
            }
        """)
        self._load_avatar()
        avatar_layout.addWidget(self.avatar_label)
        card_layout.addWidget(avatar_container)
        
        # 名称
        name_label = QLabel("奶酪云工具箱")
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_label.setStyleSheet("""
            QLabel {
                color: #f8fafc;
                font-size: 22px;
                font-weight: bold;
                font-family: "Microsoft YaHei UI";
            }
        """)
        card_layout.addWidget(name_label)
        
        # 副标题
        subtitle_label = QLabel("高效办公 · 精致生活")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_label.setStyleSheet("""
            QLabel {
                color: #64748b;
                font-size: 13px;
                font-family: "Microsoft YaHei UI";
            }
        """)
        card_layout.addWidget(subtitle_label)
        
        card_layout.addSpacing(8)
        
        # 分割线
        divider = QWidget()
        divider.setFixedHeight(1)
        divider.setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 transparent, stop:0.5 #334155, stop:1 transparent);")
        card_layout.addWidget(divider)
        
        card_layout.addSpacing(8)
        
        # 二维码区域
        qr_container = QWidget()
        qr_layout = QVBoxLayout(qr_container)
        qr_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        qr_layout.setSpacing(8)
        
        qr_title = QLabel("📱 微信扫码添加好友")
        qr_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        qr_title.setStyleSheet("""
            QLabel {
                color: #94a3b8;
                font-size: 12px;
                font-family: "Microsoft YaHei UI";
            }
        """)
        qr_layout.addWidget(qr_title)
        
        self.qr_label = QLabel()
        self.qr_label.setFixedSize(220, 220)
        self.qr_label.setStyleSheet("""
            QLabel {
                background: white;
                border-radius: 12px;
            }
        """)
        self._load_qrcode()
        qr_layout.addWidget(self.qr_label, 0, Qt.AlignmentFlag.AlignCenter)
        
        card_layout.addWidget(qr_container)
        
        card_layout.addSpacing(10)
        
        # 邮箱区域
        email_container = QWidget()
        email_container.setStyleSheet("""
            QWidget {
                background: rgba(30, 41, 59, 0.6);
                border-radius: 12px;
            }
        """)
        email_layout = QVBoxLayout(email_container)
        email_layout.setContentsMargins(20, 16, 20, 16)
        email_layout.setSpacing(8)
        
        email_title = QLabel("📧 合作联系邮箱")
        email_title.setStyleSheet("""
            QLabel {
                color: #94a3b8;
                font-size: 12px;
                background: transparent;
            }
        """)
        email_layout.addWidget(email_title)
        
        email_row = QHBoxLayout()
        
        self.email_label = QLabel("workerqi@163.com")
        self.email_label.setStyleSheet("""
            QLabel {
                color: #fbbf24;
                font-size: 16px;
                font-weight: bold;
                background: transparent;
            }
        """)
        email_row.addWidget(self.email_label)
        
        email_row.addStretch()
        
        copy_btn = GlowButton("复制", False)
        copy_btn.setFixedSize(70, 34)
        copy_btn.clicked.connect(self.copy_email)
        email_row.addWidget(copy_btn)
        
        send_btn = GlowButton("发送邮件", True)
        send_btn.setFixedSize(90, 34)
        send_btn.clicked.connect(self.send_email)
        email_row.addWidget(send_btn)
        
        email_layout.addLayout(email_row)
        card_layout.addWidget(email_container)
        
        card_layout.addStretch()
        
        # 底部提示
        tip_label = QLabel("点击空白处关闭")
        tip_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tip_label.setStyleSheet("""
            QLabel {
                color: #475569;
                font-size: 11px;
            }
        """)
        card_layout.addWidget(tip_label)
        
        main_layout.addWidget(self.card)
    
    def _load_avatar(self):
        """加载头像"""
        if os.path.exists(AVATAR_PATH):
            pixmap = QPixmap(AVATAR_PATH)
            if not pixmap.isNull():
                # 创建圆形头像
                scaled = pixmap.scaled(94, 94, Qt.AspectRatioMode.KeepAspectRatioByExpanding, 
                                       Qt.TransformationMode.SmoothTransformation)
                
                # 裁剪为圆形
                rounded = QPixmap(94, 94)
                rounded.fill(Qt.GlobalColor.transparent)
                
                painter = QPainter(rounded)
                painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                
                path = QPainterPath()
                path.addEllipse(0, 0, 94, 94)
                painter.setClipPath(path)
                
                # 居中裁剪
                x = (scaled.width() - 94) // 2
                y = (scaled.height() - 94) // 2
                painter.drawPixmap(0, 0, scaled, x, y, 94, 94)
                painter.end()
                
                self.avatar_label.setPixmap(rounded)
                return
        
        # 默认头像
        self.avatar_label.setText("🧀")
        self.avatar_label.setStyleSheet(self.avatar_label.styleSheet() + """
            font-size: 48px;
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #fbbf24, stop:1 #d97706);
        """)
    
    def _load_qrcode(self):
        """加载二维码"""
        if os.path.exists(QRCODE_PATH):
            pixmap = QPixmap(QRCODE_PATH)
            if not pixmap.isNull():
                # 缩放到完整显示，保持宽高比
                scaled = pixmap.scaled(210, 210, Qt.AspectRatioMode.KeepAspectRatio,
                                       Qt.TransformationMode.SmoothTransformation)
                self.qr_label.setPixmap(scaled)
                self.qr_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                return
        
        self.qr_label.setText("二维码")
        self.qr_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    
    def add_decorations(self):
        """添加装饰元素"""
        # 添加浮动装饰球
        orb1 = FloatingOrb(120, QColor("#fbbf24"), self.container)
        orb1.move(-30, -30)
        
        orb2 = FloatingOrb(80, QColor("#3b82f6"), self.container)
        orb2.move(420, 50)
        
        orb3 = FloatingOrb(60, QColor("#8b5cf6"), self.container)
        orb3.move(400, 500)
        
        orb4 = FloatingOrb(100, QColor("#ec4899"), self.container)
        orb4.move(-20, 480)
        
        # 确保装饰在底层
        orb1.lower()
        orb2.lower()
        orb3.lower()
        orb4.lower()
    
    def setup_animations(self):
        """设置动画"""
        # 卡片淡入效果
        self.card_opacity = QGraphicsOpacityEffect(self.card)
        self.card_opacity.setOpacity(0)
        self.card.setGraphicsEffect(self.card_opacity)
        
        self.fade_anim = QPropertyAnimation(self.card_opacity, b"opacity")
        self.fade_anim.setDuration(300)
        self.fade_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
    
    def showEvent(self, event):
        super().showEvent(event)
        # 居中显示
        if self.parent():
            parent_rect = self.parent().rect()
            x = (parent_rect.width() - self.width()) // 2
            y = (parent_rect.height() - self.height()) // 2
            self.move(self.parent().mapToGlobal(QPoint(x, y)))
        
        # 播放淡入动画
        self.fade_anim.setStartValue(0)
        self.fade_anim.setEndValue(1)
        self.fade_anim.start()
    
    def close_with_animation(self):
        """带动画关闭"""
        self.fade_anim.setStartValue(1)
        self.fade_anim.setEndValue(0)
        self.fade_anim.finished.connect(self.accept)
        self.fade_anim.start()
    
    def copy_email(self):
        """复制邮箱"""
        clipboard = QApplication.clipboard()
        clipboard.setText("workerqi@163.com")
        
        # 临时显示"已复制"
        original_text = self.email_label.text()
        self.email_label.setText("✓ 已复制到剪贴板")
        self.email_label.setStyleSheet("""
            QLabel {
                color: #22c55e;
                font-size: 16px;
                font-weight: bold;
                background: transparent;
            }
        """)
        QTimer.singleShot(1500, lambda: self._reset_email_label(original_text))
    
    def _reset_email_label(self, text):
        """重置邮箱标签"""
        self.email_label.setText(text)
        self.email_label.setStyleSheet("""
            QLabel {
                color: #fbbf24;
                font-size: 16px;
                font-weight: bold;
                background: transparent;
            }
        """)
    
    def send_email(self):
        """发送邮件"""
        import webbrowser
        webbrowser.open("mailto:workerqi@163.com?subject=奶酪云工具箱-合作咨询")
    
    def paintEvent(self, event):
        """绘制背景"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 半透明遮罩背景
        painter.fillRect(self.rect(), QColor(0, 0, 0, 120))
        
        # 卡片背景
        card_rect = self.card.geometry().adjusted(20, 20, -20, -20)
        
        # 卡片阴影
        shadow_color = QColor(0, 0, 0, 80)
        for i in range(10):
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(0, 0, 0, int(80 - i * 8)))
            painter.drawRoundedRect(card_rect.adjusted(-i*2, -i*2, i*2, i*2), 24 + i, 24 + i)
        
        # 卡片主体 - 玻璃质感
        gradient = QLinearGradient(card_rect.topLeft(), card_rect.bottomRight())
        gradient.setColorAt(0, QColor(30, 41, 59, 240))
        gradient.setColorAt(0.5, QColor(15, 23, 42, 250))
        gradient.setColorAt(1, QColor(30, 41, 59, 240))
        
        painter.setBrush(gradient)
        painter.setPen(QPen(QColor(71, 85, 105, 100), 1))
        painter.drawRoundedRect(card_rect, 24, 24)
        
        # 顶部高光
        highlight_rect = QRect(card_rect.x() + 40, card_rect.y(), card_rect.width() - 80, 2)
        highlight_gradient = QLinearGradient(highlight_rect.topLeft(), highlight_rect.topRight())
        highlight_gradient.setColorAt(0, QColor(251, 191, 36, 0))
        highlight_gradient.setColorAt(0.5, QColor(251, 191, 36, 150))
        highlight_gradient.setColorAt(1, QColor(251, 191, 36, 0))
        painter.setBrush(highlight_gradient)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(highlight_rect, 1, 1)
    
    def mousePressEvent(self, event):
        """点击空白处关闭"""
        card_rect = self.card.geometry().adjusted(20, 20, -20, -20)
        if not card_rect.contains(event.pos()):
            self.close_with_animation()
        else:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
    
    def mouseMoveEvent(self, event):
        """拖动窗口"""
        if self._drag_pos:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
    
    def mouseReleaseEvent(self, event):
        self._drag_pos = None

