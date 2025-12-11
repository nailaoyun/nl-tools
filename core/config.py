"""
全局配置管理模块
- 保存/读取用户配置
- 配置全局文件保存位置
"""
import os
import json
import logging
from pathlib import Path
from typing import Any, Optional


class Config:
    """全局配置管理器"""
    
    _instance = None
    _config_file = None
    _config_data = {}
    
    # 默认配置
    DEFAULT_CONFIG = {
        "output_directory": "",  # 空字符串表示每次询问
        "auto_save_to_default": False,  # 是否自动保存到默认目录
        "image_quality": 85,  # 默认图片质量
        "enable_lossless_compression": True,  # 启用无损压缩
        "show_preview": True,  # 显示预览
        "animation_enabled": True,  # 启用动画
        "animation_duration": 300,  # 动画时长(ms)
    }
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        # 配置文件路径
        app_root = Path(__file__).parent.parent
        config_dir = app_root / "config"
        config_dir.mkdir(exist_ok=True)
        self._config_file = config_dir / "settings.json"
        
        # 加载配置
        self._load_config()
        self._initialized = True
    
    def _load_config(self):
        """加载配置文件"""
        if self._config_file.exists():
            try:
                with open(self._config_file, "r", encoding="utf-8") as f:
                    self._config_data = json.load(f)
                logging.info(f"已加载配置文件: {self._config_file}")
            except Exception as e:
                logging.error(f"加载配置文件失败: {e}")
                self._config_data = {}
        else:
            self._config_data = {}
        
        # 合并默认配置
        for key, value in self.DEFAULT_CONFIG.items():
            if key not in self._config_data:
                self._config_data[key] = value
    
    def _save_config(self):
        """保存配置文件"""
        try:
            with open(self._config_file, "w", encoding="utf-8") as f:
                json.dump(self._config_data, f, ensure_ascii=False, indent=2)
            logging.info("配置已保存")
        except Exception as e:
            logging.error(f"保存配置失败: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        return self._config_data.get(key, default)
    
    def set(self, key: str, value: Any):
        """设置配置值"""
        self._config_data[key] = value
        self._save_config()
    
    def get_output_directory(self) -> str:
        """获取输出目录"""
        path = self.get("output_directory", "")
        if path and os.path.isdir(path):
            return path
        return ""
    
    def set_output_directory(self, path: str):
        """设置输出目录"""
        self.set("output_directory", path)


# 全局配置实例
config = Config()

