"""
日志配置模块
- 日志文件: logs/app_YYYYMMDD.log
- 日志格式: [时间] [级别] [模块] 消息
- 自动清理30天前的旧日志
"""
import os
import logging
import datetime
from pathlib import Path


def get_logs_dir() -> Path:
    """获取日志目录路径"""
    # 获取应用根目录
    app_root = Path(__file__).parent.parent
    logs_dir = app_root / "logs"
    logs_dir.mkdir(exist_ok=True)
    return logs_dir


def get_log_file_path() -> Path:
    """获取当天的日志文件路径"""
    today = datetime.date.today().strftime("%Y%m%d")
    return get_logs_dir() / f"app_{today}.log"


def setup_logging():
    """配置日志系统"""
    log_file = get_log_file_path()
    
    # 日志格式
    log_format = "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    
    # 配置根日志器
    logging.basicConfig(
        level=logging.DEBUG,
        format=log_format,
        datefmt=date_format,
        handlers=[
            # 文件处理器
            logging.FileHandler(log_file, encoding="utf-8"),
            # 控制台处理器
            logging.StreamHandler()
        ]
    )
    
    # 记录启动日志
    logging.info("=" * 50)
    logging.info("奶酪云工具箱 启动")
    logging.info("=" * 50)
    
    # 清理旧日志
    cleanup_old_logs()


def cleanup_old_logs(days: int = 30):
    """清理指定天数前的旧日志"""
    logs_dir = get_logs_dir()
    cutoff_date = datetime.date.today() - datetime.timedelta(days=days)
    
    for log_file in logs_dir.glob("app_*.log"):
        try:
            # 从文件名提取日期
            date_str = log_file.stem.replace("app_", "")
            file_date = datetime.datetime.strptime(date_str, "%Y%m%d").date()
            
            if file_date < cutoff_date:
                log_file.unlink()
                logging.info(f"已清理旧日志文件: {log_file.name}")
        except (ValueError, OSError) as e:
            logging.warning(f"清理日志文件失败 {log_file}: {e}")


def get_all_log_files() -> list:
    """获取所有日志文件列表(按时间倒序)"""
    logs_dir = get_logs_dir()
    log_files = list(logs_dir.glob("app_*.log"))
    log_files.sort(key=lambda x: x.name, reverse=True)
    return log_files


def read_log_file(file_path: Path) -> str:
    """读取日志文件内容"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"读取日志文件失败: {e}"

