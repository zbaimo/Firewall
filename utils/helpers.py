"""
辅助函数
"""
import yaml
import ipaddress
from typing import Dict, Any
from datetime import datetime, timedelta


def load_config(config_file: str = 'config.yaml') -> Dict[str, Any]:
    """加载配置文件"""
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        return config
    except FileNotFoundError:
        print(f"错误: 配置文件不存在: {config_file}")
        raise
    except yaml.YAMLError as e:
        print(f"错误: 配置文件格式错误: {e}")
        raise


def is_valid_ip(ip: str) -> bool:
    """验证IP地址是否有效"""
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False


def is_private_ip(ip: str) -> bool:
    """检查是否为私有IP"""
    try:
        ip_obj = ipaddress.ip_address(ip)
        return ip_obj.is_private
    except ValueError:
        return False


def format_duration(seconds: int) -> str:
    """格式化时间长度"""
    if seconds < 60:
        return f"{seconds}秒"
    elif seconds < 3600:
        return f"{seconds // 60}分钟"
    elif seconds < 86400:
        return f"{seconds // 3600}小时"
    else:
        return f"{seconds // 86400}天"


def format_size(bytes_size: int) -> str:
    """格式化文件大小"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.2f} PB"


def parse_time_range(time_str: str) -> timedelta:
    """
    解析时间范围字符串
    例如: '1h', '30m', '7d'
    """
    time_str = time_str.strip().lower()
    
    if time_str.endswith('s'):
        return timedelta(seconds=int(time_str[:-1]))
    elif time_str.endswith('m'):
        return timedelta(minutes=int(time_str[:-1]))
    elif time_str.endswith('h'):
        return timedelta(hours=int(time_str[:-1]))
    elif time_str.endswith('d'):
        return timedelta(days=int(time_str[:-1]))
    else:
        raise ValueError(f"无效的时间格式: {time_str}")


def get_severity_emoji(severity: str) -> str:
    """根据严重程度返回emoji"""
    severity_map = {
        'low': '🟢',
        'medium': '🟡',
        'high': '🟠',
        'critical': '🔴'
    }
    return severity_map.get(severity.lower(), '⚪')


def truncate_string(s: str, max_length: int = 50) -> str:
    """截断字符串"""
    if len(s) <= max_length:
        return s
    return s[:max_length-3] + '...'


def merge_dicts(dict1: Dict, dict2: Dict) -> Dict:
    """递归合并字典"""
    result = dict1.copy()
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_dicts(result[key], value)
        else:
            result[key] = value
    return result

