"""
防火墙执行器
自动执行IP封禁和解封操作
"""
import platform
import subprocess
import ipaddress
from datetime import datetime, timedelta
from typing import List, Optional, Dict
import re


class FirewallExecutor:
    """防火墙执行器"""
    
    def __init__(self, db, config: Dict):
        self.db = db
        self.config = config
        self.firewall_config = config.get('firewall', {})
        
        # 检测操作系统
        os_type = self.firewall_config.get('os', 'auto')
        if os_type == 'auto':
            self.os_type = self._detect_os()
        else:
            self.os_type = os_type
        
        self.enabled = self.firewall_config.get('enabled', True)
        self.whitelist = set(self.firewall_config.get('whitelist', []))
        self.blacklist = set(self.firewall_config.get('blacklist', []))
        
        print(f"防火墙执行器初始化: OS={self.os_type}, 启用={self.enabled}")
    
    def _detect_os(self) -> str:
        """检测操作系统类型"""
        system = platform.system().lower()
        if 'windows' in system:
            return 'windows'
        elif 'linux' in system:
            return 'linux'
        elif 'darwin' in system:
            return 'macos'
        else:
            return 'unknown'
    
    def is_whitelisted(self, ip: str) -> bool:
        """检查IP是否在白名单中"""
        # 检查精确匹配
        if ip in self.whitelist:
            return True
        
        # 检查CIDR范围
        try:
            ip_obj = ipaddress.ip_address(ip)
            for cidr in self.whitelist:
                if '/' in cidr:
                    network = ipaddress.ip_network(cidr, strict=False)
                    if ip_obj in network:
                        return True
        except:
            pass
        
        # 检查数据库白名单
        from models.database import Whitelist
        session = self.db.get_session()
        try:
            exists = session.query(Whitelist).filter(
                Whitelist.ip == ip
            ).first()
            return exists is not None
        finally:
            session.close()
    
    def is_blacklisted(self, ip: str) -> bool:
        """检查IP是否在黑名单中"""
        if ip in self.blacklist:
            return True
        
        from models.database import Blacklist
        session = self.db.get_session()
        try:
            exists = session.query(Blacklist).filter(
                Blacklist.ip == ip,
                Blacklist.is_active == True
            ).first()
            return exists is not None
        finally:
            session.close()
    
    def ban_ip(self, ip: str, reason: str, duration_seconds: Optional[int] = None,
               threat_event_id: Optional[int] = None) -> bool:
        """
        封禁IP
        
        Args:
            ip: 要封禁的IP地址
            reason: 封禁原因
            duration_seconds: 封禁时长（秒），None表示使用默认值
            threat_event_id: 关联的威胁事件ID
            
        Returns:
            是否成功
        """
        # 检查白名单
        if self.is_whitelisted(ip):
            print(f"IP {ip} 在白名单中，跳过封禁")
            return False
        
        # 检查是否已经被封禁
        if self._is_currently_banned(ip):
            print(f"IP {ip} 已经被封禁")
            return False
        
        # 使用默认时长
        if duration_seconds is None:
            duration_seconds = self.firewall_config.get('ban', {}).get('default_duration', 3600)
        
        # 执行防火墙规则
        if self.enabled:
            success = self._execute_ban(ip)
            if not success:
                print(f"执行防火墙封禁失败: {ip}")
                return False
        else:
            print(f"防火墙未启用，模拟封禁: {ip}")
        
        # 记录到数据库
        from models.database import BanRecord
        session = self.db.get_session()
        try:
            # 检查是否有历史封禁记录
            existing = session.query(BanRecord).filter(
                BanRecord.ip == ip
            ).first()
            
            if existing:
                # 更新现有记录
                existing.is_active = True
                existing.banned_at = datetime.now()
                existing.ban_until = datetime.now() + timedelta(seconds=duration_seconds)
                existing.reason = reason
                existing.threat_event_id = threat_event_id
                existing.ban_count += 1
                existing.unbanned_at = None
                
                # 检查是否需要永久封禁
                permanent_threshold = self.firewall_config.get('ban', {}).get('permanent_threshold', 5)
                if existing.ban_count >= permanent_threshold:
                    existing.is_permanent = True
                    existing.ban_until = None
                    print(f"IP {ip} 达到封禁阈值，设为永久封禁")
            else:
                # 创建新记录
                ban_until = datetime.now() + timedelta(seconds=duration_seconds)
                new_ban = BanRecord(
                    ip=ip,
                    banned_at=datetime.now(),
                    ban_until=ban_until,
                    reason=reason,
                    threat_event_id=threat_event_id,
                    is_permanent=False,
                    is_active=True,
                    ban_count=1
                )
                session.add(new_ban)
            
            session.commit()
            print(f"✓ 成功封禁 IP: {ip}, 原因: {reason}, 时长: {duration_seconds}秒")
            return True
        except Exception as e:
            session.rollback()
            print(f"记录封禁失败: {e}")
            return False
        finally:
            session.close()
    
    def unban_ip(self, ip: str) -> bool:
        """解封IP"""
        # 执行防火墙规则
        if self.enabled:
            success = self._execute_unban(ip)
            if not success:
                print(f"执行防火墙解封失败: {ip}")
                return False
        
        # 更新数据库
        from models.database import BanRecord
        session = self.db.get_session()
        try:
            ban_record = session.query(BanRecord).filter(
                BanRecord.ip == ip,
                BanRecord.is_active == True
            ).first()
            
            if ban_record:
                ban_record.is_active = False
                ban_record.unbanned_at = datetime.now()
                session.commit()
                print(f"✓ 成功解封 IP: {ip}")
                return True
            else:
                print(f"未找到活跃的封禁记录: {ip}")
                return False
        finally:
            session.close()
    
    def _is_currently_banned(self, ip: str) -> bool:
        """检查IP是否当前被封禁"""
        from models.database import BanRecord
        session = self.db.get_session()
        try:
            ban = session.query(BanRecord).filter(
                BanRecord.ip == ip,
                BanRecord.is_active == True
            ).first()
            return ban is not None
        finally:
            session.close()
    
    def _execute_ban(self, ip: str) -> bool:
        """执行实际的防火墙封禁命令"""
        try:
            if self.os_type == 'windows':
                return self._ban_windows(ip)
            elif self.os_type == 'linux':
                return self._ban_linux(ip)
            else:
                print(f"不支持的操作系统: {self.os_type}")
                return False
        except Exception as e:
            print(f"执行防火墙命令失败: {e}")
            return False
    
    def _execute_unban(self, ip: str) -> bool:
        """执行实际的防火墙解封命令"""
        try:
            if self.os_type == 'windows':
                return self._unban_windows(ip)
            elif self.os_type == 'linux':
                return self._unban_linux(ip)
            else:
                return False
        except Exception as e:
            print(f"执行防火墙解封命令失败: {e}")
            return False
    
    def _ban_windows(self, ip: str) -> bool:
        """Windows防火墙封禁"""
        rule_name = f"FirewallBlock_{ip.replace('.', '_')}"
        
        # 添加防火墙规则
        cmd = [
            'netsh', 'advfirewall', 'firewall', 'add', 'rule',
            f'name={rule_name}',
            'dir=in',
            'action=block',
            f'remoteip={ip}'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode == 0
    
    def _unban_windows(self, ip: str) -> bool:
        """Windows防火墙解封"""
        rule_name = f"FirewallBlock_{ip.replace('.', '_')}"
        
        cmd = [
            'netsh', 'advfirewall', 'firewall', 'delete', 'rule',
            f'name={rule_name}'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode == 0
    
    def _ban_linux(self, ip: str) -> bool:
        """Linux防火墙封禁（iptables）"""
        # 检查是否使用firewalld
        try:
            result = subprocess.run(['which', 'firewall-cmd'], capture_output=True)
            if result.returncode == 0:
                return self._ban_linux_firewalld(ip)
        except:
            pass
        
        # 使用iptables
        cmd = ['iptables', '-A', 'INPUT', '-s', ip, '-j', 'DROP']
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode == 0
    
    def _unban_linux(self, ip: str) -> bool:
        """Linux防火墙解封"""
        try:
            result = subprocess.run(['which', 'firewall-cmd'], capture_output=True)
            if result.returncode == 0:
                return self._unban_linux_firewalld(ip)
        except:
            pass
        
        cmd = ['iptables', '-D', 'INPUT', '-s', ip, '-j', 'DROP']
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode == 0
    
    def _ban_linux_firewalld(self, ip: str) -> bool:
        """使用firewalld封禁"""
        cmd = ['firewall-cmd', '--permanent', '--add-rich-rule=',
               f"rule family='ipv4' source address='{ip}' reject"]
        subprocess.run(cmd, capture_output=True)
        
        # 重新加载
        subprocess.run(['firewall-cmd', '--reload'], capture_output=True)
        return True
    
    def _unban_linux_firewalld(self, ip: str) -> bool:
        """使用firewalld解封"""
        cmd = ['firewall-cmd', '--permanent', '--remove-rich-rule=',
               f"rule family='ipv4' source address='{ip}' reject"]
        subprocess.run(cmd, capture_output=True)
        
        subprocess.run(['firewall-cmd', '--reload'], capture_output=True)
        return True
    
    def check_expired_bans(self):
        """检查并自动解封过期的IP"""
        from models.database import BanRecord
        
        session = self.db.get_session()
        try:
            # 查找所有过期的封禁
            expired_bans = session.query(BanRecord).filter(
                BanRecord.is_active == True,
                BanRecord.is_permanent == False,
                BanRecord.ban_until < datetime.now()
            ).all()
            
            for ban in expired_bans:
                print(f"自动解封过期IP: {ban.ip}")
                self.unban_ip(ban.ip)
        finally:
            session.close()
    
    def list_banned_ips(self) -> List[Dict]:
        """列出所有被封禁的IP"""
        from models.database import BanRecord
        
        session = self.db.get_session()
        try:
            bans = session.query(BanRecord).filter(
                BanRecord.is_active == True
            ).order_by(BanRecord.banned_at.desc()).all()
            
            return [{
                'ip': ban.ip,
                'banned_at': ban.banned_at.isoformat(),
                'ban_until': ban.ban_until.isoformat() if ban.ban_until else '永久',
                'reason': ban.reason,
                'is_permanent': ban.is_permanent,
                'ban_count': ban.ban_count
            } for ban in bans]
        finally:
            session.close()

