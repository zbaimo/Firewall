"""
Nginx日志防火墙系统 - 主程序
"""
import sys
import signal
import threading
import time
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler

from utils.helpers import load_config
from utils.logger import setup_logger, log_threat, log_ban
from models.database import Database, AccessLog, Fingerprint
from core.log_monitor import NginxLogParser, LogMonitor, BatchLogProcessor
from core.fingerprint import FingerprintGenerator, BehaviorAnalyzer
from core.identity_chain import IdentityChainManager
from core.threat_detector import ThreatDetector
from core.firewall import FirewallExecutor
from core.cache_manager import CacheManager
from core.geo_analyzer import GeoAnalyzer
from core.alert_manager import AlertManager
from core.audit_logger import AuditLogger
from core.scoring_system import ThreatScoringSystem
from core.rule_engine import RuleEngine
from core.port_manager import PortManager
from core.auth_manager import AuthManager


class FirewallSystem:
    """防火墙系统主类"""
    
    def __init__(self, config_file: str = 'config.yaml'):
        print("=" * 60)
        print("🛡️  Nginx日志智能防火墙系统")
        print("=" * 60)
        
        # 加载配置
        print("正在加载配置...")
        self.config = load_config(config_file)
        
        # 设置日志
        self.logger = setup_logger(self.config)
        self.logger.info("系统启动中...")
        
        # 初始化数据库
        print("正在初始化数据库...")
        self.db = Database(self.config)
        
        # 初始化性能优化模块
        print("正在初始化性能优化模块...")
        self.cache_manager = CacheManager(self.config)
        
        # 初始化核心模块
        print("正在初始化核心模块...")
        self.fingerprint_gen = FingerprintGenerator(self.config)
        self.behavior_analyzer = BehaviorAnalyzer(self.config)
        self.identity_chain_mgr = IdentityChainManager(self.db, self.config, self.fingerprint_gen)
        self.threat_detector = ThreatDetector(self.db, self.config)
        self.firewall = FirewallExecutor(self.db, self.config)
        
        # 初始化高级功能
        print("正在初始化高级功能...")
        self.geo_analyzer = GeoAnalyzer(self.db, self.cache_manager, self.config)
        self.alert_manager = AlertManager(self.config)
        self.audit_logger = AuditLogger(self.config)
        self.scoring_system = ThreatScoringSystem(self.db, self.config)
        self.rule_engine = RuleEngine(self.db, self.config)
        self.port_manager = PortManager(self.db, self.config, self.audit_logger)
        self.auth_manager = AuthManager(self.db, self.config)
        
        # 日志监控器
        nginx_config = self.config.get('nginx', {})
        log_format = nginx_config.get('log_format', 'combined')
        self.log_parser = NginxLogParser(log_format)
        
        access_log = nginx_config.get('access_log')
        self.log_monitor = LogMonitor(access_log, self.log_parser, self.process_log_entry)
        
        # 定时任务调度器
        self.scheduler = BackgroundScheduler()
        self.running = False
        
        print("✓ 初始化完成")
        print()
    
    def process_log_entry(self, log_data: dict):
        """
        处理单条日志记录
        这是核心处理流程
        """
        try:
            ip = log_data.get('ip')
            
            # 检查白名单
            if self.firewall.is_whitelisted(ip):
                return
            
            # 1. 生成指纹
            base_hash = self.fingerprint_gen.generate_base_hash(log_data)
            behavior_hash = self.fingerprint_gen.generate_behavior_hash(log_data)
            
            log_data['base_hash'] = base_hash
            log_data['behavior_hash'] = behavior_hash
            
            # 2. 保存到数据库
            self.save_access_log(log_data)
            
            # 3. 更新或创建指纹记录
            self.update_fingerprint(log_data)
            
            # 4. 地理位置分析
            if self.geo_analyzer.enabled:
                location = self.geo_analyzer.get_location(ip)
                if location:
                    self.geo_analyzer.update_location_metadata(base_hash, location)
                    
                    # 检测地理位置异常
                    is_anomaly, reason, geo_score = self.geo_analyzer.check_geo_anomaly(ip, base_hash)
                    if is_anomaly and self.scoring_system.enabled:
                        self.scoring_system.add_score_to_fingerprint(base_hash, geo_score, reason)
                        if self.alert_manager.enabled:
                            self.alert_manager.send_threat_alert(
                                ip, 'geo_anomaly', 'medium', reason, 
                                {'location': location, 'score': geo_score}
                            )
            
            # 5. 行为分析 - 检查是否需要创建身份链
            behavior_analysis = self.behavior_analyzer.analyze_behavior_change(base_hash, self.db.get_session())
            if behavior_analysis.get('should_create_chain'):
                chain_id = self.identity_chain_mgr.check_and_create_chain(base_hash, behavior_analysis)
                if chain_id:
                    self.logger.info(f"创建身份链 #{chain_id} for {ip} (hash: {base_hash[:8]}...)")
                    if self.audit_logger:
                        self.audit_logger.log_system_event('identity_chain_created', {
                            'chain_id': chain_id,
                            'ip': ip,
                            'base_hash': base_hash[:16]
                        })
            
            # 6. 自定义规则检测
            if self.rule_engine:
                rule_matches = self.rule_engine.evaluate(log_data)
                for match in rule_matches:
                    if match['action'] == 'score' and self.scoring_system.enabled:
                        self.scoring_system.add_score_to_fingerprint(
                            base_hash, 
                            match['score'], 
                            f"自定义规则: {match['rule_name']}"
                        )
            
            # 7. 威胁检测
            threats = self.threat_detector.detect(log_data)
            
            if threats:
                self.handle_threats(ip, base_hash, threats, log_data)
            
        except Exception as e:
            self.logger.error(f"处理日志条目时出错: {e}", exc_info=True)
    
    def save_access_log(self, log_data: dict):
        """保存访问日志到数据库"""
        session = self.db.get_session()
        try:
            log_entry = AccessLog(
                timestamp=log_data['timestamp'],
                ip=log_data['ip'],
                user_agent=log_data['user_agent'],
                request_method=log_data['request_method'],
                request_path=log_data['request_path'],
                query_params=log_data['query_params'],
                status_code=log_data['status_code'],
                referer=log_data['referer'],
                response_size=log_data['response_size'],
                request_time=log_data.get('request_time', 0),
                base_hash=log_data['base_hash'],
                behavior_hash=log_data['behavior_hash'],
                raw_log=log_data['raw_log']
            )
            session.add(log_entry)
            session.commit()
        except Exception as e:
            session.rollback()
            self.logger.error(f"保存访问日志失败: {e}")
        finally:
            session.close()
    
    def update_fingerprint(self, log_data: dict):
        """更新或创建指纹记录"""
        session = self.db.get_session()
        try:
            base_hash = log_data['base_hash']
            
            fingerprint = session.query(Fingerprint).filter(
                Fingerprint.base_hash == base_hash
            ).first()
            
            if fingerprint:
                # 更新现有指纹
                fingerprint.last_seen = log_data['timestamp']
                fingerprint.visit_count += 1
            else:
                # 创建新指纹
                fingerprint = Fingerprint(
                    base_hash=base_hash,
                    ip=log_data['ip'],
                    user_agent=log_data['user_agent'],
                    first_seen=log_data['timestamp'],
                    last_seen=log_data['timestamp'],
                    visit_count=1
                )
                session.add(fingerprint)
            
            session.commit()
        except Exception as e:
            session.rollback()
            self.logger.error(f"更新指纹失败: {e}")
        finally:
            session.close()
    
    def handle_threats(self, ip: str, base_hash: str, threats: list, log_data: dict):
        """处理检测到的威胁"""
        for threat in threats:
            threat_type = threat['threat_type']
            severity = threat['severity']
            description = threat['description']
            
            # 记录威胁日志
            log_threat(self.logger, ip, threat_type, description)
            
            # 保存威胁事件
            event_id = self.threat_detector.save_threat_event(ip, base_hash, threat)
            
            # 使用评分系统（如果启用）
            if self.scoring_system and self.scoring_system.enabled:
                # 计算威胁分数
                threat_score = self.scoring_system.calculate_threat_score(threat)
                self.scoring_system.add_score_to_fingerprint(
                    base_hash, 
                    threat_score, 
                    f"威胁检测: {threat_type}",
                    event_id
                )
                
                # 检查是否应该封禁
                should_ban, ban_type, ban_duration = self.scoring_system.should_ban(base_hash)
                
                if should_ban:
                    success = self.firewall.ban_ip(ip, f"评分超限: {description}", ban_duration, event_id)
                    if success:
                        log_ban(self.logger, ip, description)
                        if self.audit_logger:
                            self.audit_logger.log_ban(ip, description, ban_duration)
                        if self.alert_manager:
                            self.alert_manager.send_ban_alert(ip, description, ban_duration)
            else:
                # 使用传统封禁逻辑
                should_ban = self.should_ban_for_threat(threat)
                
                if should_ban:
                    ban_duration = self.get_ban_duration(threat)
                    success = self.firewall.ban_ip(ip, description, ban_duration, event_id)
                    
                    if success:
                        log_ban(self.logger, ip, description)
                        if self.audit_logger:
                            self.audit_logger.log_ban(ip, description, ban_duration)
            
            # 发送告警
            if self.alert_manager and self.alert_manager.enabled:
                if severity in ['critical', 'high']:
                    self.alert_manager.send_threat_alert(
                        ip, threat_type, severity, description,
                        threat.get('details')
                    )
    
    def should_ban_for_threat(self, threat: dict) -> bool:
        """判断是否应该为该威胁封禁IP"""
        severity = threat['severity']
        threat_type = threat['threat_type']
        
        # 关键威胁立即封禁
        if severity == 'critical':
            return True
        
        # 高危威胁封禁
        if severity == 'high':
            return True
        
        # 中等威胁根据类型判断
        if severity == 'medium':
            # 路径扫描和频率限制封禁
            if threat_type in ['path_scan', 'rate_limit_exceeded']:
                return True
        
        return False
    
    def get_ban_duration(self, threat: dict) -> int:
        """根据威胁类型获取封禁时长（秒）"""
        severity_duration = {
            'critical': 86400,  # 1天
            'high': 3600,       # 1小时
            'medium': 1800,     # 30分钟
            'low': 600          # 10分钟
        }
        
        return severity_duration.get(threat['severity'], 3600)
    
    def setup_scheduled_tasks(self):
        """设置定时任务"""
        # 每5分钟检查过期的封禁
        auto_unban_config = self.config.get('auto_unban', {})
        if auto_unban_config.get('enabled', True):
            interval = auto_unban_config.get('check_interval', 300)
            self.scheduler.add_job(
                self.firewall.check_expired_bans,
                'interval',
                seconds=interval,
                id='check_expired_bans'
            )
            self.logger.info(f"定时任务: 每{interval}秒检查过期封禁")
        
        # 每天清理过期数据
        retention_days = self.config.get('fingerprint', {}).get('retention_days', 3)
        self.scheduler.add_job(
            lambda: self.db.cleanup_old_data(retention_days),
            'cron',
            hour=3,
            minute=0,
            id='cleanup_old_data'
        )
        self.logger.info(f"定时任务: 每天3:00清理{retention_days}天前的数据")
        
        # 每小时生成统计数据
        self.scheduler.add_job(
            self.generate_statistics,
            'cron',
            minute=0,
            id='generate_statistics'
        )
        self.logger.info("定时任务: 每小时生成统计数据")
    
    def generate_statistics(self):
        """生成统计数据"""
        from models.database import Statistics
        import json
        from sqlalchemy import func
        from datetime import datetime, timedelta
        
        session = self.db.get_session()
        try:
            # 统计上一小时的数据
            hour_start = datetime.now().replace(minute=0, second=0, microsecond=0) - timedelta(hours=1)
            hour_end = hour_start + timedelta(hours=1)
            
            # 总请求数
            total_requests = session.query(func.count(AccessLog.id)).filter(
                AccessLog.timestamp >= hour_start,
                AccessLog.timestamp < hour_end
            ).scalar()
            
            # 唯一IP数
            unique_ips = session.query(func.count(func.distinct(AccessLog.ip))).filter(
                AccessLog.timestamp >= hour_start,
                AccessLog.timestamp < hour_end
            ).scalar()
            
            # 状态码统计
            status_stats = session.query(
                AccessLog.status_code,
                func.count(AccessLog.id)
            ).filter(
                AccessLog.timestamp >= hour_start,
                AccessLog.timestamp < hour_end
            ).group_by(AccessLog.status_code).all()
            
            status_codes = {str(code): count for code, count in status_stats}
            
            # 保存统计
            stats = Statistics(
                timestamp=hour_start,
                total_requests=total_requests,
                unique_ips=unique_ips,
                status_codes=json.dumps(status_codes)
            )
            session.add(stats)
            session.commit()
            
            self.logger.info(f"统计: {hour_start.strftime('%Y-%m-%d %H:00')} - "
                           f"请求: {total_requests}, IP: {unique_ips}")
        except Exception as e:
            session.rollback()
            self.logger.error(f"生成统计失败: {e}")
        finally:
            session.close()
    
    def start(self):
        """启动系统"""
        self.running = True
        
        # 设置信号处理
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        # 启动定时任务
        self.setup_scheduled_tasks()
        self.scheduler.start()
        
        # 启动Web管理后台（如果启用）
        web_config = self.config.get('web_dashboard', {})
        if web_config.get('enabled', False):
            self.start_web_dashboard()
        
        print()
        print("=" * 60)
        print("🚀 系统已启动")
        print("=" * 60)
        print(f"📝 日志文件: {self.config['nginx']['access_log']}")
        print(f"💾 数据库: {self.config['database']['path']}")
        print(f"🔥 防火墙: {'启用' if self.firewall.enabled else '禁用'}")
        print(f"⚡ Redis缓存: {'启用' if self.cache_manager.is_enabled() else '禁用'}")
        print(f"🌍 地理位置: {'启用' if self.geo_analyzer.enabled else '禁用'}")
        print(f"📋 审计日志: {'启用' if self.audit_logger.enabled else '禁用'}")
        print(f"🔔 实时告警: {'启用' if self.alert_manager.enabled else '禁用'}")
        print(f"📊 评分系统: {'启用' if self.scoring_system.enabled else '禁用'}")
        print(f"⚙️  自定义规则: {len(self.rule_engine.rules)} 条")
        
        if web_config.get('enabled'):
            print(f"🌐 管理后台: http://{web_config['host']}:{web_config['port']}")
        
        print()
        print("按 Ctrl+C 停止系统")
        print("=" * 60)
        print()
        
        # 记录系统启动
        if self.audit_logger:
            self.audit_logger.log_system_event('system_start', {
                'redis_enabled': self.cache_manager.is_enabled(),
                'geo_enabled': self.geo_analyzer.enabled,
                'alert_enabled': self.alert_manager.enabled
            })
        
        # 启动日志监控
        try:
            self.log_monitor.start()
        except KeyboardInterrupt:
            self.stop()
    
    def start_web_dashboard(self):
        """启动Web管理后台"""
        try:
            from web.app import create_app
            
            web_config = self.config.get('web_dashboard', {})
            app = create_app(
                self.config, self.db, self.firewall, 
                self.threat_detector, self.identity_chain_mgr,
                self.cache_manager, self.geo_analyzer, 
                self.audit_logger, self.scoring_system,
                self.port_manager, self.auth_manager
            )
            
            def run_flask():
                app.run(
                    host=web_config.get('host', '127.0.0.1'),
                    port=web_config.get('port', 8080),
                    debug=False,
                    use_reloader=False
                )
            
            # 在单独的线程中运行Flask
            flask_thread = threading.Thread(target=run_flask, daemon=True)
            flask_thread.start()
            
            self.logger.info("Web管理后台已启动")
        except ImportError as e:
            self.logger.warning(f"无法启动Web管理后台: {e}")
        except Exception as e:
            self.logger.error(f"启动Web管理后台失败: {e}")
    
    def stop(self):
        """停止系统"""
        print("\n正在关闭系统...")
        self.running = False
        
        # 记录系统停止
        if self.audit_logger:
            self.audit_logger.log_system_event('system_stop')
        
        # 停止日志监控
        self.log_monitor.stop()
        
        # 停止定时任务
        self.scheduler.shutdown()
        
        # 关闭GeoIP数据库
        if self.geo_analyzer:
            self.geo_analyzer.close()
        
        self.logger.info("系统已停止")
        print("✓ 系统已关闭")
        sys.exit(0)
    
    def _signal_handler(self, signum, frame):
        """信号处理器"""
        self.stop()


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Nginx日志智能防火墙系统')
    parser.add_argument('-c', '--config', default='config.yaml', help='配置文件路径')
    parser.add_argument('--batch', help='批量处理历史日志文件')
    parser.add_argument('--max-lines', type=int, help='批量处理最大行数')
    
    args = parser.parse_args()
    
    # 加载配置
    config = load_config(args.config)
    
    if args.batch:
        # 批量处理模式
        print(f"批量处理日志文件: {args.batch}")
        
        db = Database(config)
        fingerprint_gen = FingerprintGenerator(config)
        behavior_analyzer = BehaviorAnalyzer(config)
        threat_detector = ThreatDetector(db, config)
        firewall = FirewallExecutor(db, config)
        
        system = FirewallSystem(args.config)
        
        log_format = config.get('nginx', {}).get('log_format', 'combined')
        parser = NginxLogParser(log_format)
        processor = BatchLogProcessor(parser, system.process_log_entry)
        
        processor.process_file(args.batch, args.max_lines)
        print("处理完成")
    else:
        # 实时监控模式
        system = FirewallSystem(args.config)
        system.start()


if __name__ == '__main__':
    main()

