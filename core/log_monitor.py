"""
Nginx日志监控模块
实时监控并解析nginx日志
"""
import re
import os
import time
from datetime import datetime
from typing import Dict, Optional, Callable
from urllib.parse import urlparse, parse_qs
import json


class NginxLogParser:
    """Nginx日志解析器"""
    
    # Nginx combined格式正则表达式
    COMBINED_PATTERN = re.compile(
        r'(?P<ip>[\d\.]+) - (?P<remote_user>.*?) \[(?P<time>.*?)\] '
        r'"(?P<request>.*?)" (?P<status>\d+) (?P<size>\d+|-) '
        r'"(?P<referer>.*?)" "(?P<user_agent>.*?)"'
    )
    
    # 自定义格式（包含响应时间）
    CUSTOM_PATTERN = re.compile(
        r'(?P<ip>[\d\.]+) - (?P<remote_user>.*?) \[(?P<time>.*?)\] '
        r'"(?P<request>.*?)" (?P<status>\d+) (?P<size>\d+|-) '
        r'"(?P<referer>.*?)" "(?P<user_agent>.*?)" '
        r'(?P<request_time>[\d\.]+)'
    )
    
    def __init__(self, log_format: str = 'combined'):
        self.log_format = log_format
        if log_format == 'custom':
            self.pattern = self.CUSTOM_PATTERN
        else:
            self.pattern = self.COMBINED_PATTERN
    
    def parse_line(self, line: str) -> Optional[Dict]:
        """
        解析单行日志
        
        Returns:
            解析后的字典，包含：
            - ip: 客户端IP
            - user_agent: User-Agent
            - request_method: 请求方法
            - request_path: 请求路径
            - query_params: 查询参数（JSON字符串）
            - status_code: HTTP状态码
            - referer: Referer
            - response_size: 响应大小
            - request_time: 请求时间（如果有）
            - timestamp: 时间戳
            - raw_log: 原始日志行
        """
        match = self.pattern.match(line.strip())
        if not match:
            return None
        
        data = match.groupdict()
        
        # 解析请求行
        request = data.get('request', '')
        request_parts = request.split(' ', 2)
        
        if len(request_parts) >= 2:
            method = request_parts[0]
            full_path = request_parts[1]
        else:
            method = 'UNKNOWN'
            full_path = request
        
        # 分离路径和查询参数
        parsed_url = urlparse(full_path)
        path = parsed_url.path
        query_params = dict(parse_qs(parsed_url.query))
        
        # 解析时间
        time_str = data.get('time', '')
        try:
            # Nginx时间格式: 17/Oct/2025:18:30:00 +0800
            timestamp = datetime.strptime(time_str.split(' ')[0], '%d/%b/%Y:%H:%M:%S')
        except:
            timestamp = datetime.now()
        
        # 处理响应大小
        size = data.get('size', '0')
        if size == '-':
            size = 0
        else:
            size = int(size)
        
        return {
            'ip': data.get('ip'),
            'user_agent': data.get('user_agent', ''),
            'request_method': method,
            'request_path': path,
            'query_params': json.dumps(query_params) if query_params else '',
            'status_code': int(data.get('status', 0)),
            'referer': data.get('referer', ''),
            'response_size': size,
            'request_time': float(data.get('request_time', 0)) if 'request_time' in data else 0,
            'timestamp': timestamp,
            'raw_log': line.strip()
        }


class LogMonitor:
    """日志监控器 - 实时监控日志文件"""
    
    def __init__(self, log_file: str, parser: NginxLogParser, callback: Callable):
        """
        Args:
            log_file: 日志文件路径
            parser: 日志解析器
            callback: 回调函数，处理解析后的日志行
        """
        self.log_file = log_file
        self.parser = parser
        self.callback = callback
        self.running = False
    
    def start(self):
        """开始监控日志文件"""
        self.running = True
        
        # 检查文件是否存在
        if not os.path.exists(self.log_file):
            print(f"警告: 日志文件不存在: {self.log_file}")
            print("等待文件创建...")
            while not os.path.exists(self.log_file) and self.running:
                time.sleep(1)
        
        # 打开文件并跳到末尾（只处理新的日志）
        with open(self.log_file, 'r', encoding='utf-8', errors='ignore') as f:
            # 跳到文件末尾
            f.seek(0, 2)
            
            print(f"开始监控日志文件: {self.log_file}")
            
            while self.running:
                line = f.readline()
                
                if line:
                    # 解析日志行
                    parsed = self.parser.parse_line(line)
                    if parsed:
                        try:
                            self.callback(parsed)
                        except Exception as e:
                            print(f"处理日志行时出错: {e}")
                else:
                    # 没有新数据，等待一下
                    time.sleep(0.1)
                    
                    # 检查文件是否被轮转
                    try:
                        current_inode = os.stat(self.log_file).st_ino
                        if hasattr(f, 'fileno'):
                            file_inode = os.fstat(f.fileno()).st_ino
                            if current_inode != file_inode:
                                # 文件已轮转，重新打开
                                print("检测到日志轮转，重新打开文件...")
                                break
                    except:
                        pass
    
    def stop(self):
        """停止监控"""
        self.running = False


class BatchLogProcessor:
    """批量日志处理器 - 用于处理历史日志"""
    
    def __init__(self, parser: NginxLogParser, callback: Callable):
        self.parser = parser
        self.callback = callback
    
    def process_file(self, log_file: str, max_lines: Optional[int] = None):
        """
        处理日志文件
        
        Args:
            log_file: 日志文件路径
            max_lines: 最多处理的行数（None表示全部）
        """
        if not os.path.exists(log_file):
            print(f"错误: 日志文件不存在: {log_file}")
            return
        
        print(f"开始处理日志文件: {log_file}")
        
        processed = 0
        errors = 0
        
        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                if max_lines and processed >= max_lines:
                    break
                
                parsed = self.parser.parse_line(line)
                if parsed:
                    try:
                        self.callback(parsed)
                        processed += 1
                        
                        if processed % 1000 == 0:
                            print(f"已处理 {processed} 行...")
                    except Exception as e:
                        errors += 1
                        if errors <= 10:  # 只打印前10个错误
                            print(f"处理日志行时出错: {e}")
                else:
                    errors += 1
        
        print(f"处理完成: 成功 {processed} 行, 错误 {errors} 行")


# 使用watchdog库的高级监控器（可选）
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    
    class LogFileHandler(FileSystemEventHandler):
        """使用watchdog的文件监控处理器"""
        
        def __init__(self, log_file: str, parser: NginxLogParser, callback: Callable):
            self.log_file = log_file
            self.parser = parser
            self.callback = callback
            self.last_position = 0
            
            # 初始化文件位置
            if os.path.exists(log_file):
                self.last_position = os.path.getsize(log_file)
        
        def on_modified(self, event):
            """文件修改时触发"""
            if event.src_path.endswith(os.path.basename(self.log_file)):
                self.process_new_lines()
        
        def process_new_lines(self):
            """处理新增的日志行"""
            try:
                with open(self.log_file, 'r', encoding='utf-8', errors='ignore') as f:
                    f.seek(self.last_position)
                    
                    for line in f:
                        parsed = self.parser.parse_line(line)
                        if parsed:
                            try:
                                self.callback(parsed)
                            except Exception as e:
                                print(f"处理日志行时出错: {e}")
                    
                    self.last_position = f.tell()
            except Exception as e:
                print(f"读取日志文件时出错: {e}")
    
    class WatchdogLogMonitor:
        """基于watchdog的日志监控器"""
        
        def __init__(self, log_file: str, parser: NginxLogParser, callback: Callable):
            self.log_file = log_file
            self.observer = Observer()
            self.handler = LogFileHandler(log_file, parser, callback)
            
            # 监控日志文件所在目录
            log_dir = os.path.dirname(os.path.abspath(log_file))
            self.observer.schedule(self.handler, log_dir, recursive=False)
        
        def start(self):
            """开始监控"""
            self.observer.start()
            print(f"开始监控日志文件(watchdog): {self.log_file}")
            
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                self.stop()
        
        def stop(self):
            """停止监控"""
            self.observer.stop()
            self.observer.join()

except ImportError:
    # watchdog未安装，使用基本的LogMonitor
    WatchdogLogMonitor = None

