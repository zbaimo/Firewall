"""
端口扫描器
扫描服务器开启的端口（内部和外部）
"""
import socket
import subprocess
from typing import List, Dict, Tuple
import logging

logger = logging.getLogger(__name__)


class PortScanner:
    """端口扫描器"""
    
    # 常用端口列表
    COMMON_PORTS = {
        20: 'FTP-Data', 21: 'FTP', 22: 'SSH', 23: 'Telnet', 25: 'SMTP',
        53: 'DNS', 80: 'HTTP', 110: 'POP3', 143: 'IMAP', 443: 'HTTPS',
        465: 'SMTPS', 587: 'SMTP-Submit', 993: 'IMAPS', 995: 'POP3S',
        3306: 'MySQL', 3389: 'RDP', 5432: 'PostgreSQL', 6379: 'Redis',
        8080: 'HTTP-Proxy', 8443: 'HTTPS-Alt', 9000: 'PHP-FPM', 27017: 'MongoDB'
    }
    
    def __init__(self, db, config: Dict):
        self.db = db
        self.config = config
    
    def scan_localhost_ports(self, port_range: Tuple[int, int] = (1, 65535)) -> List[Dict]:
        """
        扫描本地开放的端口（内部端口）
        
        Args:
            port_range: 端口范围 (start, end)
            
        Returns:
            开放端口列表
        """
        open_ports = []
        
        try:
            # 使用netstat或ss命令获取监听端口
            result = subprocess.run(
                ['ss', '-tuln'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                # 尝试netstat
                result = subprocess.run(
                    ['netstat', '-tuln'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
            
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                for line in lines:
                    if 'LISTEN' in line or 'UNCONN' in line:
                        parts = line.split()
                        if len(parts) >= 5:
                            addr = parts[4] if 'LISTEN' in line else parts[3]
                            # 提取端口
                            if ':' in addr:
                                port_str = addr.split(':')[-1]
                                try:
                                    port = int(port_str)
                                    if port_range[0] <= port <= port_range[1]:
                                        service = self.COMMON_PORTS.get(port, 'Unknown')
                                        protocol = 'tcp' if 'tcp' in line.lower() else 'udp'
                                        
                                        open_ports.append({
                                            'port': port,
                                            'protocol': protocol,
                                            'service': service,
                                            'type': 'internal',
                                            'listen_address': addr
                                        })
                                except ValueError:
                                    continue
            
            logger.info(f"扫描到 {len(open_ports)} 个内部开放端口")
            return open_ports
            
        except Exception as e:
            logger.error(f"扫描本地端口失败: {e}")
            return []
    
    def scan_external_ports(self, host: str = '127.0.0.1', 
                          ports: List[int] = None) -> List[Dict]:
        """
        扫描外部可访问的端口
        
        Args:
            host: 目标主机
            ports: 要扫描的端口列表（默认扫描常用端口）
            
        Returns:
            开放端口列表
        """
        if ports is None:
            ports = list(self.COMMON_PORTS.keys())
        
        open_ports = []
        
        for port in ports:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex((host, port))
                
                if result == 0:
                    service = self.COMMON_PORTS.get(port, 'Unknown')
                    open_ports.append({
                        'port': port,
                        'protocol': 'tcp',
                        'service': service,
                        'type': 'external',
                        'accessible': True
                    })
                
                sock.close()
                
            except Exception as e:
                logger.debug(f"扫描端口 {port} 失败: {e}")
                continue
        
        logger.info(f"扫描到 {len(open_ports)} 个外部可访问端口")
        return open_ports
    
    def get_listening_ports(self) -> List[Dict]:
        """
        获取所有监听端口（使用系统命令）
        
        Returns:
            监听端口详细信息
        """
        ports = []
        
        try:
            # 使用ss命令
            result = subprocess.run(
                ['ss', '-tulnp'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                lines = result.stdout.split('\n')[1:]  # 跳过标题行
                
                for line in lines:
                    if not line.strip():
                        continue
                    
                    parts = line.split()
                    if len(parts) >= 5:
                        protocol = parts[0].lower()
                        local_addr = parts[4]
                        process_info = parts[-1] if len(parts) > 5 else ''
                        
                        # 提取端口和地址
                        if ':' in local_addr:
                            addr_parts = local_addr.rsplit(':', 1)
                            listen_addr = addr_parts[0]
                            port_str = addr_parts[1]
                            
                            try:
                                port = int(port_str)
                                service = self.COMMON_PORTS.get(port, 'Unknown')
                                
                                # 判断是内部还是外部
                                is_external = listen_addr in ['0.0.0.0', '*', '::', '[::]']
                                
                                ports.append({
                                    'port': port,
                                    'protocol': protocol.replace('6', ''),  # tcp6 -> tcp
                                    'service': service,
                                    'listen_address': listen_addr,
                                    'type': 'external' if is_external else 'internal',
                                    'process': process_info,
                                    'is_public': is_external
                                })
                            except ValueError:
                                continue
            
            # 去重
            seen = set()
            unique_ports = []
            for p in ports:
                key = (p['port'], p['protocol'])
                if key not in seen:
                    seen.add(key)
                    unique_ports.append(p)
            
            logger.info(f"检测到 {len(unique_ports)} 个监听端口")
            return unique_ports
            
        except Exception as e:
            logger.error(f"获取监听端口失败: {e}")
            return []
    
    def categorize_ports(self, ports: List[Dict]) -> Dict:
        """
        将端口分类
        
        Returns:
            分类结果
        """
        categorized = {
            'web': [],
            'database': [],
            'remote': [],
            'email': [],
            'dns': [],
            'other': [],
            'external': [],
            'internal': []
        }
        
        port_categories = {
            'web': [80, 443, 8080, 8443, 8888, 9000, 3000],
            'database': [3306, 5432, 6379, 27017, 1433, 5984],
            'remote': [22, 23, 3389],
            'email': [25, 110, 143, 465, 587, 993, 995],
            'dns': [53]
        }
        
        for port_info in ports:
            port = port_info['port']
            
            # 按类型分类
            if port_info.get('is_public') or port_info.get('type') == 'external':
                categorized['external'].append(port_info)
            else:
                categorized['internal'].append(port_info)
            
            # 按服务分类
            found = False
            for category, port_list in port_categories.items():
                if port in port_list:
                    categorized[category].append(port_info)
                    found = True
                    break
            
            if not found:
                categorized['other'].append(port_info)
        
        return categorized

