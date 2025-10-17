"""
日志工具
"""
import logging
import logging.handlers
import os
from datetime import datetime


def setup_logger(config: dict) -> logging.Logger:
    """
    设置日志系统
    
    Args:
        config: 配置字典
        
    Returns:
        配置好的logger对象
    """
    log_config = config.get('logging', {})
    
    # 创建logger
    logger = logging.getLogger('firewall')
    logger.setLevel(getattr(logging, log_config.get('level', 'INFO')))
    
    # 防止重复添加handler
    if logger.handlers:
        return logger
    
    # 创建格式化器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 文件处理器（带日志轮转）
    log_file = log_config.get('file', 'firewall.log')
    max_bytes = log_config.get('max_size_mb', 100) * 1024 * 1024
    backup_count = log_config.get('backup_count', 5)
    
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger


def log_threat(logger: logging.Logger, ip: str, threat_type: str, description: str):
    """记录威胁日志"""
    logger.warning(f"[威胁检测] IP: {ip} | 类型: {threat_type} | {description}")


def log_ban(logger: logging.Logger, ip: str, reason: str):
    """记录封禁日志"""
    logger.info(f"[封禁] IP: {ip} | 原因: {reason}")


def log_unban(logger: logging.Logger, ip: str):
    """记录解封日志"""
    logger.info(f"[解封] IP: {ip}")

