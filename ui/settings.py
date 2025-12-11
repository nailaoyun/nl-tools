"""
设置页面
- 全局配置选项
- 文件保存位置设置
- 日志查看器
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QLineEdit, QFileDialog, QCheckBox, QSlider,
    QTabWidget, QSpinBox, QMessageBox, QScrollArea, QGroupBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
import logging

from core.config import config
from ui.log_viewer import LogViewer


class SettingsPage(QWidget):
    """设置页面"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.load_settings()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # 标题
        title = QLabel("⚙️ 设置")
        title.setFont(QFont("Microsoft YaHei", 20, QFont.Weight.Bold))
        title.setStyleSheet("color: white;")
        layout.addWidget(title)
        
        # 标签页
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: none;
                background: transparent;
            }
            QTabBar::tab {
                background: #1e293b;
                color: #94a3b8;
                padding: 12px 24px;
                border: none;
                border-bottom: 2px solid transparent;
                font-size: 13px;
            }
            QTabBar::tab:hover {
                color: #e2e8f0;
            }
            QTabBar::tab:selected {
                color: #fbbf24;
                border-bottom: 2px solid #fbbf24;
            }
        """)
        
        # 通用设置标签页
        self.tab_widget.addTab(self.create_general_tab(), "📁 通用设置")
        
        # 界面设置标签页
        self.tab_widget.addTab(self.create_ui_tab(), "🎨 界面设置")
        
        # 日志查看标签页
        self.log_viewer = LogViewer()
        self.tab_widget.addTab(self.log_viewer, "📋 日志查看")
        
        layout.addWidget(self.tab_widget, 1)
        
        # 底部按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        reset_btn = QPushButton("🔄 恢复默认")
        reset_btn.setObjectName("secondary_btn")
        reset_btn.clicked.connect(self.reset_settings)
        btn_layout.addWidget(reset_btn)
        
        save_btn = QPushButton("💾 保存设置")
        save_btn.setObjectName("primary_btn")
        save_btn.clicked.connect(self.save_settings)
        btn_layout.addWidget(save_btn)
        
        layout.addLayout(btn_layout)
    
    def create_general_tab(self) -> QWidget:
        """创建通用设置标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(20)
        
        # 输出目录设置
        output_group = QGroupBox("📂 默认保存位置")
        output_layout = QVBoxLayout(output_group)
        output_layout.setSpacing(12)
        
        # 路径选择
        path_layout = QHBoxLayout()
        
        self.output_path_edit = QLineEdit()
        self.output_path_edit.setPlaceholderText("未设置 - 每次操作时询问保存位置")
        self.output_path_edit.setReadOnly(True)
        self.output_path_edit.setStyleSheet("""
            QLineEdit {
                background: #0f172a;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 10px 12px;
                color: #e2e8f0;
                font-size: 13px;
            }
        """)
        path_layout.addWidget(self.output_path_edit, 1)
        
        browse_btn = QPushButton("📁 浏览")
        browse_btn.setObjectName("secondary_btn")
        browse_btn.clicked.connect(self.browse_output_dir)
        path_layout.addWidget(browse_btn)
        
        clear_btn = QPushButton("✖ 清除")
        clear_btn.setObjectName("secondary_btn")
        clear_btn.clicked.connect(self.clear_output_dir)
        path_layout.addWidget(clear_btn)
        
        output_layout.addLayout(path_layout)
        
        # 自动保存选项
        self.auto_save_check = QCheckBox("自动保存到默认目录（不再询问）")
        self.auto_save_check.setStyleSheet("color: #cbd5e1; font-size: 13px;")
        output_layout.addWidget(self.auto_save_check)
        
        hint = QLabel("提示: 设置默认保存位置后，处理完成的文件将自动保存到该目录")
        hint.setStyleSheet("color: #64748b; font-size: 11px;")
        hint.setWordWrap(True)
        output_layout.addWidget(hint)
        
        layout.addWidget(output_group)
        
        layout.addStretch()
        return widget
    
    def create_ui_tab(self) -> QWidget:
        """创建界面设置标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(20)
        
        # 动画设置
        anim_group = QGroupBox("✨ 动画效果")
        anim_layout = QVBoxLayout(anim_group)
        anim_layout.setSpacing(12)
        
        self.animation_check = QCheckBox("启用界面动画（渐入渐出效果）")
        self.animation_check.setStyleSheet("color: #cbd5e1; font-size: 13px;")
        self.animation_check.setChecked(True)
        self.animation_check.stateChanged.connect(self.on_animation_toggle)
        anim_layout.addWidget(self.animation_check)
        
        # 动画时长
        duration_row = QHBoxLayout()
        duration_row.addWidget(QLabel("动画时长:"))
        duration_row.addStretch()
        
        self.duration_spin = QSpinBox()
        self.duration_spin.setRange(100, 1000)
        self.duration_spin.setValue(300)
        self.duration_spin.setSuffix(" ms")
        self.duration_spin.setFixedWidth(100)
        duration_row.addWidget(self.duration_spin)
        
        anim_layout.addLayout(duration_row)
        
        layout.addWidget(anim_group)
        
        layout.addStretch()
        return widget
    
    def browse_output_dir(self):
        """浏览输出目录"""
        current = self.output_path_edit.text() or ""
        path = QFileDialog.getExistingDirectory(self, "选择默认保存目录", current)
        if path:
            self.output_path_edit.setText(path)
    
    def clear_output_dir(self):
        """清除输出目录"""
        self.output_path_edit.setText("")
        self.auto_save_check.setChecked(False)
    
    def on_animation_toggle(self, state):
        """动画开关切换"""
        self.duration_spin.setEnabled(state == Qt.CheckState.Checked.value)
    
    def load_settings(self):
        """加载设置"""
        self.output_path_edit.setText(config.get("output_directory", ""))
        self.auto_save_check.setChecked(config.get("auto_save_to_default", False))
        
        self.animation_check.setChecked(config.get("animation_enabled", True))
        self.duration_spin.setValue(config.get("animation_duration", 300))
        self.duration_spin.setEnabled(config.get("animation_enabled", True))
    
    def save_settings(self):
        """保存设置"""
        config.set("output_directory", self.output_path_edit.text())
        config.set("auto_save_to_default", self.auto_save_check.isChecked())
        
        config.set("animation_enabled", self.animation_check.isChecked())
        config.set("animation_duration", self.duration_spin.value())
        
        QMessageBox.information(self, "成功", "设置已保存!")
        logging.info("用户设置已保存")
    
    def reset_settings(self):
        """恢复默认设置"""
        reply = QMessageBox.question(
            self, "确认", "确定要恢复默认设置吗?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            for key, value in config.DEFAULT_CONFIG.items():
                config.set(key, value)
            self.load_settings()
            QMessageBox.information(self, "成功", "已恢复默认设置!")
            logging.info("用户设置已恢复默认")

