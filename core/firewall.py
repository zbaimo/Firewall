"""
防火墙执行器 - 基于iptables的增强实现
自动执行IP封禁和解封操作，支持高级功能
"""
import subprocess
import ipaddress
import platform
import json
import re
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class FirewallRule:
    """防火墙规则数据类"""
    chain: str  # INPUT, OUTPUT, FORWARD
    action: str  # ACCEPT, DROP, REJECT
    source: Optional[str] = None
    destination: Optional[str] = None
    protocol: Optional[str] = None
    port: Optional[int] = None
    comment: Optional[str] = None


class FirewallExecutor:
    """防火墙执行器 - 基于iptables的增强实现"""
    
    # 自定义链名称
    FIREWALL_CHAIN = "FIREWALL_BANS"
    RATE_LIMIT_CHAIN = "FIREWALL_RATE_LIMIT"
    PORT_RULES_CHAIN = "FIREWALL_PORT_RULES"
    
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
        
        # 如果是Linux，初始化iptables自定义链
        if self.enabled and self.os_type == 'linux':
            self._initialize_chains()
        
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
    
    # ==================== 白名单/黑名单检查 ====================
    
    def is_whitelisted(self, ip: str) -> bool:
        """检查IP是否在白名单中"""
        # 检查配置文件白名单
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
    
    # ==================== 初始化 ====================
    
    def _initialize_chains(self):
        """初始化自定义iptables链"""
        try:
            # 创建自定义链
            self._create_chain(self.FIREWALL_CHAIN)
            self._create_chain(self.RATE_LIMIT_CHAIN)
            self._create_chain(self.PORT_RULES_CHAIN)
            
            # 将自定义链挂载到INPUT链
            self._ensure_chain_jump('INPUT', self.FIREWALL_CHAIN)
            self._ensure_chain_jump('INPUT', self.RATE_LIMIT_CHAIN)
            self._ensure_chain_jump('INPUT', self.PORT_RULES_CHAIN)
            
            logger.info(f"✓ 自定义iptables链初始化完成")
        except Exception as e:
            logger.error(f"初始化iptables链失败: {e}")
    
    def _create_chain(self, chain_name: str):
        """创建自定义链（如果不存在）"""
        try:
            # 检查链是否存在
            result = subprocess.run(
                ['iptables', '-L', chain_name, '-n'],
                capture_output=True,
                timeout=5
            )
            
            if result.returncode != 0:
                # 链不存在，创建它
                subprocess.run(
                    ['iptables', '-N', chain_name],
                    check=True,
                    timeout=5
                )
                logger.info(f"创建iptables链: {chain_name}")
        except subprocess.TimeoutExpired:
            logger.error(f"创建链超时: {chain_name}")
        except Exception as e:
            logger.warning(f"创建链失败 {chain_name}: {e}")
    
    def _ensure_chain_jump(self, from_chain: str, to_chain: str):
        """确保链跳转规则存在"""
        try:
            # 检查跳转规则是否存在
            result = subprocess.run(
                ['iptables', '-C', from_chain, '-j', to_chain],
                capture_output=True,
                timeout=5
            )
            
            if result.returncode != 0:
                # 跳转规则不存在，添加它
                subprocess.run(
                    ['iptables', '-I', from_chain, '1', '-j', to_chain],
                    check=True,
                    timeout=5
                )
                logger.info(f"添加链跳转: {from_chain} -> {to_chain}")
        except Exception as e:
            logger.warning(f"添加链跳转失败: {e}")
    
    # ==================== IP封禁 ====================
    
    def ban_ip(self, ip: str, reason: str = "Manual ban", 
               duration_seconds: Optional[int] = None,
               threat_event_id: Optional[int] = None) -> bool:
        """
        封禁IP地址（兼容新旧接口）
        
        Args:
            ip: 要封禁的IP地址
            reason: 封禁原因
            duration_seconds: 封禁时长（秒），None表示永久
            threat_event_id: 威胁事件ID（可选）
            
        Returns:
            是否成功
        """
        # 检查白名单
        if self.is_whitelisted(ip):
            logger.warning(f"IP在白名单中，不能封禁: {ip}")
            return False
        
        if not self.enabled:
            logger.info(f"防火墙未启用，仅记录数据库: {ip}")
            self._save_ban_record(ip, reason, duration_seconds, threat_event_id)
            return True
        
        try:
            # 验证IP地址
            ipaddress.ip_address(ip)
            
            # 检查是否已经封禁
            if self._is_ip_banned(ip):
                logger.warning(f"IP已经被封禁: {ip}")
                return True
            
            # 根据操作系统执行不同的封禁方法
            if self.os_type == 'linux':
                success = self._ban_linux_iptables(ip, reason, duration_seconds)
            elif self.os_type == 'windows':
                success = self._ban_windows(ip, reason)
            else:
                logger.error(f"不支持的操作系统: {self.os_type}")
                return False
            
            if success:
                # 保存到数据库
                self._save_ban_record(ip, reason, duration_seconds, threat_event_id)
                print(f"✓ 成功封禁 IP: {ip} (原因: {reason})")
                return True
            else:
                return False
                
        except ValueError:
            logger.error(f"无效的IP地址: {ip}")
            return False
        except subprocess.TimeoutExpired:
            logger.error(f"封禁IP超时: {ip}")
            return False
        except Exception as e:
            logger.error(f"封禁IP异常: {ip}, {e}")
            return False
    
    def _ban_linux_iptables(self, ip: str, reason: str, duration: Optional[int]) -> bool:
        """Linux iptables封禁"""
        try:
            # 添加iptables规则
            comment = self._format_comment(reason, duration)
            cmd = [
                'iptables', '-A', self.FIREWALL_CHAIN,
                '-s', ip,
                '-j', 'DROP',
                '-m', 'comment', '--comment', comment
            ]
            
            result = subprocess.run(cmd, capture_output=True, timeout=10)
            
            if result.returncode == 0:
                logger.info(f"✓ iptables封禁成功: {ip}")
                return True
            else:
                logger.error(f"iptables封禁失败: {result.stderr.decode()}")
                return False
        except Exception as e:
            logger.error(f"iptables封禁异常: {e}")
            return False
    
    def _ban_windows(self, ip: str, reason: str) -> bool:
        """Windows防火墙封禁"""
        rule_name = f"FirewallBlock_{ip.replace('.', '_')}"
        
        cmd = [
            'netsh', 'advfirewall', 'firewall', 'add', 'rule',
            f'name={rule_name}',
            'dir=in',
            'action=block',
            f'remoteip={ip}'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode == 0
    
    def unban_ip(self, ip: str) -> bool:
        """
        解封IP地址
        
        Args:
            ip: 要解封的IP地址
            
        Returns:
            是否成功
        """
        if not self.enabled:
            logger.info(f"防火墙未启用，模拟解封: {ip}")
            return True
        
        try:
            # 查找并删除规则
            # 首先获取规则行号
            result = subprocess.run(
                ['iptables', '-L', self.FIREWALL_CHAIN, '-n', '--line-numbers'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                logger.error(f"获取规则列表失败")
                return False
            
            # 解析输出，查找包含该IP的规则
            lines = result.stdout.split('\n')
            rules_to_delete = []
            
            for line in lines:
                if ip in line and 'DROP' in line:
                    # 提取规则行号
                    parts = line.split()
                    if parts and parts[0].isdigit():
                        rules_to_delete.append(int(parts[0]))
            
            # 从后往前删除（避免行号变化）
            for rule_num in sorted(rules_to_delete, reverse=True):
                subprocess.run(
                    ['iptables', '-D', self.FIREWALL_CHAIN, str(rule_num)],
                    capture_output=True,
                    timeout=10
                )
            
            if rules_to_delete:
                logger.info(f"✓ 解封IP成功: {ip}")
                
                # 更新数据库
                self._update_ban_record(ip, unbanned=True)
                
                return True
            else:
                logger.warning(f"未找到IP封禁规则: {ip}")
                return False
                
        except Exception as e:
            logger.error(f"解封IP异常: {ip}, {e}")
            return False
    
    def _is_ip_banned(self, ip: str) -> bool:
        """检查IP是否已被封禁"""
        try:
            result = subprocess.run(
                ['iptables', '-L', self.FIREWALL_CHAIN, '-n'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            return ip in result.stdout and 'DROP' in result.stdout
        except Exception as e:
            logger.error(f"检查IP封禁状态失败: {e}")
            return False
    
    # ==================== 批量操作 ====================
    
    def ban_ips_batch(self, ips: List[str], reason: str = "Batch ban") -> Dict[str, bool]:
        """
        批量封禁IP
        
        Args:
            ips: IP列表
            reason: 封禁原因
            
        Returns:
            {ip: success} 字典
        """
        results = {}
        
        for ip in ips:
            results[ip] = self.ban_ip(ip, reason)
        
        success_count = sum(1 for v in results.values() if v)
        logger.info(f"批量封禁完成: 成功 {success_count}/{len(ips)}")
        
        return results
    
    def unban_ips_batch(self, ips: List[str]) -> Dict[str, bool]:
        """批量解封IP"""
        results = {}
        
        for ip in ips:
            results[ip] = self.unban_ip(ip)
        
        success_count = sum(1 for v in results.values() if v)
        logger.info(f"批量解封完成: 成功 {success_count}/{len(ips)}")
        
        return results
    
    # ==================== 端口管理 ====================
    
    def open_port(self, port: int, protocol: str = 'tcp', 
                  source_ip: Optional[str] = None) -> bool:
        """
        开放端口
        
        Args:
            port: 端口号
            protocol: 协议（tcp/udp）
            source_ip: 来源IP（None表示所有IP）
            
        Returns:
            是否成功
        """
        try:
            cmd = [
                'iptables', '-A', self.PORT_RULES_CHAIN,
                '-p', protocol,
                '--dport', str(port),
                '-j', 'ACCEPT',
                '-m', 'comment', '--comment', f'Allow port {port}/{protocol}'
            ]
            
            if source_ip:
                cmd.insert(3, '-s')
                cmd.insert(4, source_ip)
            
            result = subprocess.run(cmd, capture_output=True, timeout=10)
            
            if result.returncode == 0:
                logger.info(f"✓ 端口已开放: {port}/{protocol}")
                return True
            else:
                logger.error(f"开放端口失败: {result.stderr.decode()}")
                return False
                
        except Exception as e:
            logger.error(f"开放端口异常: {e}")
            return False
    
    def close_port(self, port: int, protocol: str = 'tcp') -> bool:
        """关闭端口"""
        try:
            # 查找并删除允许规则
            result = subprocess.run(
                ['iptables', '-L', self.PORT_RULES_CHAIN, '-n', '--line-numbers'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            lines = result.stdout.split('\n')
            rules_to_delete = []
            
            for line in lines:
                if f'{protocol}' in line and f'dpt:{port}' in line and 'ACCEPT' in line:
                    parts = line.split()
                    if parts and parts[0].isdigit():
                        rules_to_delete.append(int(parts[0]))
            
            for rule_num in sorted(rules_to_delete, reverse=True):
                subprocess.run(
                    ['iptables', '-D', self.PORT_RULES_CHAIN, str(rule_num)],
                    capture_output=True,
                    timeout=10
                )
            
            if rules_to_delete:
                logger.info(f"✓ 端口已关闭: {port}/{protocol}")
                return True
            else:
                logger.warning(f"未找到端口规则: {port}/{protocol}")
                return False
                
        except Exception as e:
            logger.error(f"关闭端口异常: {e}")
            return False
    
    def block_port(self, port: int, protocol: str = 'tcp') -> bool:
        """阻止端口（主动拒绝）"""
        try:
            cmd = [
                'iptables', '-A', self.PORT_RULES_CHAIN,
                '-p', protocol,
                '--dport', str(port),
                '-j', 'REJECT',
                '-m', 'comment', '--comment', f'Block port {port}/{protocol}'
            ]
            
            result = subprocess.run(cmd, capture_output=True, timeout=10)
            
            if result.returncode == 0:
                logger.info(f"✓ 端口已阻止: {port}/{protocol}")
                return True
            else:
                return False
                
        except Exception as e:
            logger.error(f"阻止端口异常: {e}")
            return False
    
    # ==================== 频率限制 ====================
    
    def add_rate_limit(self, limit: int = 10, period: int = 60, 
                       port: Optional[int] = None) -> bool:
        """
        添加频率限制规则
        
        Args:
            limit: 限制次数
            period: 时间周期（秒）
            port: 端口（None表示所有端口）
            
        Returns:
            是否成功
        """
        try:
            # 使用iptables的hashlimit模块
            cmd = [
                'iptables', '-A', self.RATE_LIMIT_CHAIN,
                '-m', 'hashlimit',
                '--hashlimit-name', f'ratelimit_{port or "all"}',
                '--hashlimit-mode', 'srcip',
                '--hashlimit-above', f'{limit}/{period}',
                '-j', 'DROP',
                '-m', 'comment', '--comment', f'Rate limit {limit}/{period}s'
            ]
            
            if port:
                cmd.insert(3, '-p')
                cmd.insert(4, 'tcp')
                cmd.insert(5, '--dport')
                cmd.insert(6, str(port))
            
            result = subprocess.run(cmd, capture_output=True, timeout=10)
            
            if result.returncode == 0:
                logger.info(f"✓ 频率限制已添加: {limit}/{period}s")
                return True
            else:
                return False
                
        except Exception as e:
            logger.error(f"添加频率限制异常: {e}")
            return False
    
    # ==================== 规则管理 ====================
    
    def list_banned_ips(self) -> List[Dict]:
        """列出所有被封禁的IP"""
        try:
            result = subprocess.run(
                ['iptables', '-L', self.FIREWALL_CHAIN, '-n', '-v'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            banned_ips = []
            lines = result.stdout.split('\n')[2:]  # 跳过头部
            
            for line in lines:
                if 'DROP' in line:
                    parts = line.split()
                    if len(parts) >= 8:
                        ip = parts[7]  # 源IP地址
                        packets = parts[0]
                        bytes_count = parts[1]
                        
                        banned_ips.append({
                            'ip': ip,
                            'packets_blocked': int(packets),
                            'bytes_blocked': int(bytes_count),
                            'chain': self.FIREWALL_CHAIN
                        })
            
            return banned_ips
            
        except Exception as e:
            logger.error(f"列出封禁IP失败: {e}")
            return []
    
    def get_firewall_stats(self) -> Dict:
        """获取防火墙统计信息"""
        try:
            banned_ips = self.list_banned_ips()
            
            stats = {
                'total_bans': len(banned_ips),
                'total_packets_blocked': sum(ip['packets_blocked'] for ip in banned_ips),
                'total_bytes_blocked': sum(ip['bytes_blocked'] for ip in banned_ips),
                'chains': {
                    'bans': self._count_rules(self.FIREWALL_CHAIN),
                    'rate_limits': self._count_rules(self.RATE_LIMIT_CHAIN),
                    'port_rules': self._count_rules(self.PORT_RULES_CHAIN)
                },
                'timestamp': datetime.now().isoformat()
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"获取防火墙统计失败: {e}")
            return {}
    
    def _count_rules(self, chain: str) -> int:
        """统计链中的规则数量"""
        try:
            result = subprocess.run(
                ['iptables', '-L', chain, '-n'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            # 计算规则数量（跳过头部2行）
            lines = result.stdout.split('\n')[2:]
            return len([line for line in lines if line.strip()])
            
        except Exception as e:
            return 0
    
    # ==================== 规则持久化 ====================
    
    def save_rules(self, filepath: str = '/etc/iptables/rules.v4') -> bool:
        """
        保存iptables规则到文件（持久化）
        
        Args:
            filepath: 保存路径
            
        Returns:
            是否成功
        """
        try:
            # 使用iptables-save导出规则
            result = subprocess.run(
                ['iptables-save'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                # 写入文件
                with open(filepath, 'w') as f:
                    f.write(result.stdout)
                
                logger.info(f"✓ iptables规则已保存到: {filepath}")
                return True
            else:
                return False
                
        except Exception as e:
            logger.error(f"保存iptables规则失败: {e}")
            return False
    
    def restore_rules(self, filepath: str = '/etc/iptables/rules.v4') -> bool:
        """
        从文件恢复iptables规则
        
        Args:
            filepath: 规则文件路径
            
        Returns:
            是否成功
        """
        try:
            # 使用iptables-restore导入规则
            with open(filepath, 'r') as f:
                result = subprocess.run(
                    ['iptables-restore'],
                    stdin=f,
                    capture_output=True,
                    timeout=10
                )
            
            if result.returncode == 0:
                logger.info(f"✓ iptables规则已从文件恢复: {filepath}")
                return True
            else:
                logger.error(f"恢复规则失败: {result.stderr.decode()}")
                return False
                
        except FileNotFoundError:
            logger.error(f"规则文件不存在: {filepath}")
            return False
        except Exception as e:
            logger.error(f"恢复iptables规则失败: {e}")
            return False
    
    # ==================== 规则验证 ====================
    
    def verify_ban(self, ip: str) -> Tuple[bool, Dict]:
        """
        验证IP是否真的被封禁
        
        Returns:
            (is_banned, details)
        """
        try:
            result = subprocess.run(
                ['iptables', '-L', self.FIREWALL_CHAIN, '-n', '-v'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            is_banned = ip in result.stdout and 'DROP' in result.stdout
            
            details = {
                'ip': ip,
                'is_banned': is_banned,
                'chain': self.FIREWALL_CHAIN,
                'verified_at': datetime.now().isoformat()
            }
            
            return is_banned, details
            
        except Exception as e:
            logger.error(f"验证封禁失败: {e}")
            return False, {}
    
    def health_check(self) -> Tuple[bool, Dict]:
        """
        防火墙健康检查
        
        Returns:
            (is_healthy, details)
        """
        checks = {}
        
        # 检查iptables命令是否可用
        try:
            result = subprocess.run(
                ['which', 'iptables'],
                capture_output=True,
                timeout=5
            )
            checks['iptables_available'] = result.returncode == 0
        except:
            checks['iptables_available'] = False
        
        # 检查自定义链是否存在
        for chain in [self.FIREWALL_CHAIN, self.RATE_LIMIT_CHAIN, self.PORT_RULES_CHAIN]:
            try:
                result = subprocess.run(
                    ['iptables', '-L', chain, '-n'],
                    capture_output=True,
                    timeout=5
                )
                checks[f'chain_{chain}'] = result.returncode == 0
            except:
                checks[f'chain_{chain}'] = False
        
        # 检查规则数量
        try:
            stats = self.get_firewall_stats()
            checks['total_rules'] = sum(stats.get('chains', {}).values())
        except:
            checks['total_rules'] = 0
        
        is_healthy = all([
            checks.get('iptables_available', False),
            checks.get(f'chain_{self.FIREWALL_CHAIN}', False)
        ])
        
        return is_healthy, checks
    
    # ==================== 辅助方法 ====================
    
    def _format_comment(self, reason: str, duration: Optional[int]) -> str:
        """格式化iptables注释"""
        comment = f"Firewall: {reason[:40]}"
        if duration:
            expires_at = datetime.now() + timedelta(seconds=duration)
            comment += f" | Expires: {expires_at.strftime('%Y-%m-%d %H:%M')}"
        return comment
    
    def _save_ban_record(self, ip: str, reason: str, duration: Optional[int], threat_event_id: Optional[int] = None):
        """保存封禁记录到数据库"""
        from models.database import BanRecord
        
        session = self.db.get_session()
        try:
            ban_until = None
            if duration:
                ban_until = datetime.now() + timedelta(seconds=duration)
            
            # 检查是否已有活跃的封禁记录
            existing_ban = session.query(BanRecord).filter(
                BanRecord.ip == ip,
                BanRecord.is_active == True
            ).first()
            
            if existing_ban:
                # 更新现有记录
                existing_ban.ban_count += 1
                existing_ban.reason = reason
                existing_ban.banned_at = datetime.now()
                existing_ban.ban_until = ban_until
                if threat_event_id:
                    existing_ban.threat_event_id = threat_event_id
            else:
                # 创建新记录
                ban_record = BanRecord(
                    ip=ip,
                    reason=reason,
                    banned_at=datetime.now(),
                    ban_until=ban_until,
                    is_permanent=(duration is None),
                    is_active=True,
                    ban_count=1,
                    threat_event_id=threat_event_id
                )
                session.add(ban_record)
            
            session.commit()
        except Exception as e:
            logger.error(f"保存封禁记录失败: {e}")
            session.rollback()
        finally:
            session.close()
    
    def _update_ban_record(self, ip: str, unbanned: bool = False):
        """更新封禁记录"""
        from models.database import BanRecord
        
        session = self.db.get_session()
        try:
            ban_record = session.query(BanRecord).filter(
                BanRecord.ip == ip,
                BanRecord.is_active == True
            ).first()
            
            if ban_record:
                if unbanned:
                    ban_record.is_active = False
                    ban_record.unbanned_at = datetime.now()
                
                session.commit()
        except Exception as e:
            logger.error(f"更新封禁记录失败: {e}")
            session.rollback()
        finally:
            session.close()
    
    # ==================== 清理和维护 ====================
    
    def flush_chain(self, chain: str) -> bool:
        """清空指定链的所有规则"""
        try:
            result = subprocess.run(
                ['iptables', '-F', chain],
                capture_output=True,
                timeout=10
            )
            
            if result.returncode == 0:
                logger.info(f"✓ 链已清空: {chain}")
                return True
            else:
                return False
                
        except Exception as e:
            logger.error(f"清空链失败: {e}")
            return False
    
    def reset_firewall(self) -> bool:
        """重置防火墙（清空所有自定义规则）"""
        try:
            # 清空自定义链
            self.flush_chain(self.FIREWALL_CHAIN)
            self.flush_chain(self.RATE_LIMIT_CHAIN)
            self.flush_chain(self.PORT_RULES_CHAIN)
            
            logger.info(f"✓ 防火墙已重置")
            return True
            
        except Exception as e:
            logger.error(f"重置防火墙失败: {e}")
            return False
    
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
                
            if expired_bans:
                print(f"✓ 已解封 {len(expired_bans)} 个过期IP")
                
        except Exception as e:
            logger.error(f"检查过期封禁失败: {e}")
        finally:
            session.close()
    
    def list_banned_ips(self) -> List[Dict]:
        """列出所有被封禁的IP（兼容方法）"""
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

