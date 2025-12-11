"""
全局错误处理模块
- 重写 sys.excepthook 捕获主线程未处理异常
- 使用 threading.excepthook 捕获子线程异常
- 所有异常统一进入 ErrorHandler 处理
- 弹框提示用户，不闪退
"""
import sys
import logging
import threading
import traceback
from PySide6.QtWidgets import QMessageBox, QTextEdit, QPushButton, QVBoxLayout, QDialog
from PySide6.QtCore import QObject, Signal


class ErrorSignal(QObject):
    """用于跨线程传递错误信号"""
    error_occurred = Signal(str, str)  # (error_message, error_detail)


class ErrorDialog(QDialog):
    """自定义错误对话框，支持显示详细堆栈"""
    
    def __init__(self, title: str, message: str, detail: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumSize(500, 200)
        self.setup_ui(message, detail)
    
    def setup_ui(self, message: str, detail: str):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        
        # 错误消息
        from PySide6.QtWidgets import QLabel
        msg_label = QLabel(message)
        msg_label.setWordWrap(True)
        msg_label.setStyleSheet("font-size: 14px; color: #f87171;")
        layout.addWidget(msg_label)
        
        # 详细信息(可展开)
        self.detail_edit = QTextEdit()
        self.detail_edit.setPlainText(detail)
        self.detail_edit.setReadOnly(True)
        self.detail_edit.setVisible(False)
        self.detail_edit.setMinimumHeight(200)
        layout.addWidget(self.detail_edit)
        
        # 按钮区域
        from PySide6.QtWidgets import QHBoxLayout
        btn_layout = QHBoxLayout()
        
        self.detail_btn = QPushButton("显示详情")
        self.detail_btn.setObjectName("secondary_btn")
        self.detail_btn.clicked.connect(self.toggle_detail)
        btn_layout.addWidget(self.detail_btn)
        
        btn_layout.addStretch()
        
        ok_btn = QPushButton("确定")
        ok_btn.setObjectName("primary_btn")
        ok_btn.clicked.connect(self.accept)
        btn_layout.addWidget(ok_btn)
        
        layout.addLayout(btn_layout)
    
    def toggle_detail(self):
        """切换详情显示"""
        visible = not self.detail_edit.isVisible()
        self.detail_edit.setVisible(visible)
        self.detail_btn.setText("隐藏详情" if visible else "显示详情")
        
        # 调整窗口大小
        if visible:
            self.resize(600, 450)
        else:
            self.resize(500, 200)


class ErrorHandler:
    """全局错误处理器"""
    
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, app=None):
        if hasattr(self, '_initialized') and self._initialized:
            return
        
        self.app = app
        self.error_signal = ErrorSignal()
        self.error_signal.error_occurred.connect(self._show_error_dialog)
        
        # 设置全局异常处理
        sys.excepthook = self.handle_exception
        threading.excepthook = self.handle_thread_exception
        
        self._initialized = True
        logging.info("全局错误处理器已初始化")
    
    def handle_exception(self, exc_type, exc_value, exc_tb):
        """处理主线程未捕获的异常"""
        # 忽略键盘中断
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_tb)
            return
        
        # 格式化错误信息
        error_msg = str(exc_value)
        error_detail = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
        
        # 记录日志
        logging.error(f"未捕获的异常:\n{error_detail}")
        
        # 显示错误对话框
        self._show_error_dialog(error_msg, error_detail)
    
    def handle_thread_exception(self, args):
        """处理子线程未捕获的异常"""
        exc_type = args.exc_type
        exc_value = args.exc_value
        exc_tb = args.exc_traceback
        
        # 格式化错误信息
        error_msg = str(exc_value) if exc_value else str(exc_type)
        error_detail = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
        
        # 记录日志
        logging.error(f"线程异常 ({args.thread.name}):\n{error_detail}")
        
        # 通过信号在主线程显示对话框
        self.error_signal.error_occurred.emit(error_msg, error_detail)
    
    def _show_error_dialog(self, error_msg: str, error_detail: str):
        """显示错误对话框"""
        try:
            dialog = ErrorDialog(
                title="发生错误",
                message=f"程序遇到了一个问题:\n\n{error_msg}\n\n详情已记录到日志文件。",
                detail=error_detail
            )
            dialog.exec()
        except Exception as e:
            # 如果对话框也出错，至少打印到控制台
            print(f"显示错误对话框失败: {e}")
            print(f"原始错误: {error_msg}")
            print(error_detail)
    
    @staticmethod
    def safe_execute(func, *args, error_msg: str = "操作失败", **kwargs):
        """安全执行函数，捕获异常并显示友好提示"""
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logging.error(f"{error_msg}: {e}\n{traceback.format_exc()}")
            QMessageBox.warning(None, "警告", f"{error_msg}\n\n{str(e)}")
            return None

