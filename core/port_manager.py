"""
端口管理器
通过Web界面管理防火墙端口规则
"""
import subprocess
import platform
from typing import List, Dict, Optional
from datetime import datetime


class PortManager:
    """端口管理器"""
    
    def __init__(self, db, config: Dict, audit_logger=None):
        self.db = db
        self.config = config
        self.audit_logger = audit_logger
        
        # 检测操作系统
        firewall_config = config.get('firewall', {})
        os_type = firewall_config.get('os', 'auto')
        if os_type == 'auto':
            self.os_type = self._detect_os()
        else:
            self.os_type = os_type
        
        self.enabled = firewall_config.get('enabled', True)
        
        print(f"✓ 端口管理器已初始化: OS={self.os_type}")
    
    def _detect_os(self) -> str:
        """检测操作系统"""
        system = platform.system().lower()
        if 'windows' in system:
            return 'windows'
        elif 'linux' in system:
            return 'linux'
        else:
            return 'unknown'
    
    # ==================== 端口开放 ====================
    
    def open_port(self, port: int, protocol: str = 'tcp', description: str = '', 
                  operator: str = 'admin') -> bool:
        """
        开放端口
        
        Args:
            port: 端口号
            protocol: 协议（tcp/udp）
            description: 描述
            operator: 操作者
            
        Returns:
            是否成功
        """
        if not self.enabled:
            print(f"防火墙未启用，模拟开放端口: {port}/{protocol}")
            return True
        
        try:
            if self.os_type == 'linux':
                success = self._open_port_linux(port, protocol)
            elif self.os_type == 'windows':
                success = self._open_port_windows(port, protocol, description)
            else:
                print(f"不支持的操作系统: {self.os_type}")
                return False
            
            if success:
                # 保存到数据库
                self._save_port_rule(port, protocol, 'allow', description, operator)
                
                # 记录审计日志
                if self.audit_logger:
                    self.audit_logger.log(
                        action='port_open',
                        operator=operator,
                        target=f"{port}/{protocol}",
                        details={'description': description}
                    )
                
                print(f"✓ 端口已开放: {port}/{protocol}")
                return True
            else:
                return False
                
        except Exception as e:
            print(f"开放端口失败: {e}")
            return False
    
    def close_port(self, port: int, protocol: str = 'tcp', operator: str = 'admin') -> bool:
        """
        关闭端口
        
        Args:
            port: 端口号
            protocol: 协议（tcp/udp）
            operator: 操作者
            
        Returns:
            是否成功
        """
        if not self.enabled:
            print(f"防火墙未启用，模拟关闭端口: {port}/{protocol}")
            return True
        
        try:
            if self.os_type == 'linux':
                success = self._close_port_linux(port, protocol)
            elif self.os_type == 'windows':
                success = self._close_port_windows(port, protocol)
            else:
                return False
            
            if success:
                # 从数据库删除
                self._delete_port_rule(port, protocol)
                
                # 记录审计日志
                if self.audit_logger:
                    self.audit_logger.log(
                        action='port_close',
                        operator=operator,
                        target=f"{port}/{protocol}"
                    )
                
                print(f"✓ 端口已关闭: {port}/{protocol}")
                return True
            else:
                return False
                
        except Exception as e:
            print(f"关闭端口失败: {e}")
            return False
    
    def block_port(self, port: int, protocol: str = 'tcp', description: str = '',
                   operator: str = 'admin') -> bool:
        """
        阻止端口（DROP）
        
        Args:
            port: 端口号
            protocol: 协议
            description: 描述
            operator: 操作者
        """
        if not self.enabled:
            return True
        
        try:
            if self.os_type == 'linux':
                success = self._block_port_linux(port, protocol)
            elif self.os_type == 'windows':
                success = self._block_port_windows(port, protocol, description)
            else:
                return False
            
            if success:
                self._save_port_rule(port, protocol, 'deny', description, operator)
                
                if self.audit_logger:
                    self.audit_logger.log(
                        action='port_block',
                        operator=operator,
                        target=f"{port}/{protocol}",
                        details={'description': description}
                    )
                
                print(f"✓ 端口已阻止: {port}/{protocol}")
                return True
            else:
                return False
                
        except Exception as e:
            print(f"阻止端口失败: {e}")
            return False
    
    # ==================== Linux实现 ====================
    
    def _open_port_linux(self, port: int, protocol: str) -> bool:
        """Linux开放端口"""
        try:
            # 检查是否使用firewalld
            result = subprocess.run(['which', 'firewall-cmd'], capture_output=True)
            if result.returncode == 0:
                return self._open_port_firewalld(port, protocol)
            else:
                return self._open_port_iptables(port, protocol)
        except:
            return self._open_port_iptables(port, protocol)
    
    def _open_port_iptables(self, port: int, protocol: str) -> bool:
        """使用iptables开放端口"""
        # 允许入站连接
        cmd = ['iptables', '-A', 'INPUT', '-p', protocol, '--dport', str(port), '-j', 'ACCEPT']
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            # 保存规则（使其永久生效）
            subprocess.run(['iptables-save'], capture_output=True)
            return True
        
        return False
    
    def _open_port_firewalld(self, port: int, protocol: str) -> bool:
        """使用firewalld开放端口"""
        cmd = ['firewall-cmd', '--permanent', '--add-port', f'{port}/{protocol}']
        result = subprocess.run(cmd, capture_output=True)
        
        if result.returncode == 0:
            # 重新加载
            subprocess.run(['firewall-cmd', '--reload'], capture_output=True)
            return True
        
        return False
    
    def _close_port_linux(self, port: int, protocol: str) -> bool:
        """Linux关闭端口"""
        try:
            result = subprocess.run(['which', 'firewall-cmd'], capture_output=True)
            if result.returncode == 0:
                return self._close_port_firewalld(port, protocol)
            else:
                return self._close_port_iptables(port, protocol)
        except:
            return self._close_port_iptables(port, protocol)
    
    def _close_port_iptables(self, port: int, protocol: str) -> bool:
        """使用iptables关闭端口"""
        cmd = ['iptables', '-D', 'INPUT', '-p', protocol, '--dport', str(port), '-j', 'ACCEPT']
        result = subprocess.run(cmd, capture_output=True)
        
        if result.returncode == 0:
            subprocess.run(['iptables-save'], capture_output=True)
            return True
        
        return False
    
    def _close_port_firewalld(self, port: int, protocol: str) -> bool:
        """使用firewalld关闭端口"""
        cmd = ['firewall-cmd', '--permanent', '--remove-port', f'{port}/{protocol}']
        result = subprocess.run(cmd, capture_output=True)
        
        if result.returncode == 0:
            subprocess.run(['firewall-cmd', '--reload'], capture_output=True)
            return True
        
        return False
    
    def _block_port_linux(self, port: int, protocol: str) -> bool:
        """Linux阻止端口"""
        cmd = ['iptables', '-A', 'INPUT', '-p', protocol, '--dport', str(port), '-j', 'DROP']
        result = subprocess.run(cmd, capture_output=True)
        
        if result.returncode == 0:
            subprocess.run(['iptables-save'], capture_output=True)
            return True
        
        return False
    
    # ==================== Windows实现 ====================
    
    def _open_port_windows(self, port: int, protocol: str, description: str) -> bool:
        """Windows开放端口"""
        rule_name = f"FirewallPort_{protocol.upper()}_{port}"
        if description:
            rule_name = f"{rule_name}_{description}"
        
        cmd = [
            'netsh', 'advfirewall', 'firewall', 'add', 'rule',
            f'name={rule_name}',
            'dir=in',
            'action=allow',
            f'protocol={protocol}',
            f'localport={port}'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode == 0
    
    def _close_port_windows(self, port: int, protocol: str) -> bool:
        """Windows关闭端口"""
        rule_name = f"FirewallPort_{protocol.upper()}_{port}"
        
        cmd = [
            'netsh', 'advfirewall', 'firewall', 'delete', 'rule',
            f'name={rule_name}'
        ]
        
        result = subprocess.run(cmd, capture_output=True)
        return result.returncode == 0
    
    def _block_port_windows(self, port: int, protocol: str, description: str) -> bool:
        """Windows阻止端口"""
        rule_name = f"FirewallBlockPort_{protocol.upper()}_{port}"
        
        cmd = [
            'netsh', 'advfirewall', 'firewall', 'add', 'rule',
            f'name={rule_name}',
            'dir=in',
            'action=block',
            f'protocol={protocol}',
            f'localport={port}'
        ]
        
        result = subprocess.run(cmd, capture_output=True)
        return result.returncode == 0
    
    # ==================== 规则管理 ====================
    
    def list_port_rules(self) -> List[Dict]:
        """列出所有端口规则"""
        from models.database import PortRule
        
        session = self.db.get_session()
        try:
            rules = session.query(PortRule).filter(
                PortRule.is_active == True
            ).order_by(PortRule.port).all()
            
            return [{
                'id': rule.id,
                'port': rule.port,
                'protocol': rule.protocol,
                'action': rule.action,
                'description': rule.description,
                'created_at': rule.created_at.isoformat(),
                'created_by': rule.created_by
            } for rule in rules]
        finally:
            session.close()
    
    def get_system_port_rules(self) -> List[Dict]:
        """获取系统实际的端口规则（从iptables/netsh读取）"""
        if self.os_type == 'linux':
            return self._get_linux_port_rules()
        elif self.os_type == 'windows':
            return self._get_windows_port_rules()
        else:
            return []
    
    def _get_linux_port_rules(self) -> List[Dict]:
        """获取Linux端口规则"""
        rules = []
        
        try:
            # 读取iptables规则
            result = subprocess.run(['iptables', '-L', 'INPUT', '-n', '--line-numbers'],
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                for line in lines:
                    # 解析规则行
                    if 'dpt:' in line:
                        parts = line.split()
                        for i, part in enumerate(parts):
                            if part.startswith('dpt:'):
                                port = part.split(':')[1]
                                protocol = 'tcp'  # 简化处理
                                action = 'ACCEPT' if 'ACCEPT' in line else 'DROP'
                                
                                rules.append({
                                    'port': int(port),
                                    'protocol': protocol,
                                    'action': action.lower(),
                                    'source': 'iptables'
                                })
                                break
        except Exception as e:
            print(f"读取iptables规则失败: {e}")
        
        return rules
    
    def _get_windows_port_rules(self) -> List[Dict]:
        """获取Windows端口规则"""
        rules = []
        
        try:
            cmd = ['netsh', 'advfirewall', 'firewall', 'show', 'rule', 'name=all']
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            # 简化解析（实际使用可能需要更复杂的解析）
            if result.returncode == 0:
                # Windows规则解析较复杂，这里返回数据库记录
                return self.list_port_rules()
        except Exception as e:
            print(f"读取Windows规则失败: {e}")
        
        return rules
    
    def _save_port_rule(self, port: int, protocol: str, action: str, 
                       description: str, operator: str):
        """保存端口规则到数据库"""
        from models.database import PortRule
        
        session = self.db.get_session()
        try:
            # 检查是否已存在
            existing = session.query(PortRule).filter(
                PortRule.port == port,
                PortRule.protocol == protocol,
                PortRule.action == action
            ).first()
            
            if existing:
                existing.is_active = True
                existing.description = description
            else:
                rule = PortRule(
                    port=port,
                    protocol=protocol,
                    action=action,
                    description=description,
                    created_by=operator,
                    is_active=True
                )
                session.add(rule)
            
            session.commit()
        except Exception as e:
            session.rollback()
            print(f"保存端口规则失败: {e}")
        finally:
            session.close()
    
    def _delete_port_rule(self, port: int, protocol: str):
        """从数据库删除端口规则"""
        from models.database import PortRule
        
        session = self.db.get_session()
        try:
            session.query(PortRule).filter(
                PortRule.port == port,
                PortRule.protocol == protocol
            ).update({'is_active': False})
            
            session.commit()
        except Exception as e:
            session.rollback()
            print(f"删除端口规则失败: {e}")
        finally:
            session.close()
    
    def open_port_range(self, start_port: int, end_port: int, protocol: str = 'tcp',
                       description: str = '', operator: str = 'admin') -> bool:
        """
        开放端口范围
        
        Args:
            start_port: 起始端口
            end_port: 结束端口
            protocol: 协议
            description: 描述
            operator: 操作者
        """
        if not self.enabled:
            return True
        
        try:
            if self.os_type == 'linux':
                cmd = ['iptables', '-A', 'INPUT', '-p', protocol, 
                      '--dport', f'{start_port}:{end_port}', '-j', 'ACCEPT']
                result = subprocess.run(cmd, capture_output=True)
                
                if result.returncode == 0:
                    subprocess.run(['iptables-save'], capture_output=True)
                    
                    # 记录审计
                    if self.audit_logger:
                        self.audit_logger.log(
                            action='port_range_open',
                            operator=operator,
                            target=f"{start_port}-{end_port}/{protocol}",
                            details={'description': description}
                        )
                    
                    print(f"✓ 端口范围已开放: {start_port}-{end_port}/{protocol}")
                    return True
            
            elif self.os_type == 'windows':
                rule_name = f"FirewallPortRange_{protocol}_{start_port}_{end_port}"
                
                cmd = [
                    'netsh', 'advfirewall', 'firewall', 'add', 'rule',
                    f'name={rule_name}',
                    'dir=in',
                    'action=allow',
                    f'protocol={protocol}',
                    f'localport={start_port}-{end_port}'
                ]
                
                result = subprocess.run(cmd, capture_output=True)
                
                if result.returncode == 0:
                    if self.audit_logger:
                        self.audit_logger.log(
                            action='port_range_open',
                            operator=operator,
                            target=f"{start_port}-{end_port}/{protocol}",
                            details={'description': description}
                        )
                    
                    print(f"✓ 端口范围已开放: {start_port}-{end_port}/{protocol}")
                    return True
            
            return False
            
        except Exception as e:
            print(f"开放端口范围失败: {e}")
            return False
    
    def get_common_ports(self) -> List[Dict]:
        """获取常用端口列表"""
        return [
            {'port': 80, 'protocol': 'tcp', 'name': 'HTTP', 'description': 'Web服务'},
            {'port': 443, 'protocol': 'tcp', 'name': 'HTTPS', 'description': 'SSL Web服务'},
            {'port': 22, 'protocol': 'tcp', 'name': 'SSH', 'description': 'SSH远程登录'},
            {'port': 21, 'protocol': 'tcp', 'name': 'FTP', 'description': 'FTP文件传输'},
            {'port': 3306, 'protocol': 'tcp', 'name': 'MySQL', 'description': 'MySQL数据库'},
            {'port': 5432, 'protocol': 'tcp', 'name': 'PostgreSQL', 'description': 'PostgreSQL数据库'},
            {'port': 6379, 'protocol': 'tcp', 'name': 'Redis', 'description': 'Redis缓存'},
            {'port': 27017, 'protocol': 'tcp', 'name': 'MongoDB', 'description': 'MongoDB数据库'},
            {'port': 3000, 'protocol': 'tcp', 'name': 'Node.js', 'description': 'Node.js应用'},
            {'port': 8080, 'protocol': 'tcp', 'name': 'Alt HTTP', 'description': '备用HTTP端口'},
            {'port': 53, 'protocol': 'udp', 'name': 'DNS', 'description': 'DNS服务'},
            {'port': 123, 'protocol': 'udp', 'name': 'NTP', 'description': '时间同步'},
        ]

