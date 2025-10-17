"""
命令行管理工具
提供手动管理功能
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.helpers import load_config
from models.database import Database
from core.firewall import FirewallExecutor
from core.threat_detector import ThreatDetector
from core.identity_chain import IdentityChainManager
from core.fingerprint import FingerprintGenerator
import argparse


def list_bans(db, firewall):
    """列出所有封禁"""
    bans = firewall.list_banned_ips()
    
    if not bans:
        print("没有活跃的封禁记录")
        return
    
    print(f"\n共 {len(bans)} 个活跃封禁:\n")
    print(f"{'IP地址':<20} {'封禁时间':<20} {'解封时间':<20} {'原因':<30} {'次数'}")
    print("-" * 120)
    
    for ban in bans:
        print(f"{ban['ip']:<20} {ban['banned_at']:<20} {ban['ban_until']:<20} "
              f"{ban['reason']:<30} {ban['ban_count']}")


def ban_ip(db, firewall, ip, reason, duration):
    """手动封禁IP"""
    print(f"正在封禁 IP: {ip}")
    print(f"原因: {reason}")
    print(f"时长: {duration}秒")
    
    success = firewall.ban_ip(ip, reason, duration)
    
    if success:
        print("✓ 封禁成功")
    else:
        print("✗ 封禁失败")


def unban_ip(db, firewall, ip):
    """手动解封IP"""
    print(f"正在解封 IP: {ip}")
    
    success = firewall.unban_ip(ip)
    
    if success:
        print("✓ 解封成功")
    else:
        print("✗ 解封失败")


def search_ip(db, threat_detector, ip):
    """搜索IP信息"""
    from models.database import AccessLog, Fingerprint, ThreatEvent, BanRecord
    from sqlalchemy import func
    
    print(f"\n正在搜索 IP: {ip}\n")
    
    session = db.get_session()
    try:
        # 访问记录
        log_count = session.query(func.count(AccessLog.id)).filter(
            AccessLog.ip == ip
        ).scalar()
        
        print(f"访问记录数: {log_count}")
        
        # 指纹
        fingerprints = session.query(Fingerprint).filter(
            Fingerprint.ip == ip
        ).all()
        
        print(f"指纹数量: {len(fingerprints)}")
        
        for fp in fingerprints:
            print(f"  - 哈希: {fp.base_hash[:16]}...")
            print(f"    访问次数: {fp.visit_count}")
            print(f"    威胁评分: {fp.threat_score}")
            print(f"    首次: {fp.first_seen}")
            print(f"    最后: {fp.last_seen}")
        
        # 威胁事件
        threats = threat_detector.get_ip_threat_history(ip, 720)  # 30天
        
        print(f"\n威胁事件数: {len(threats)}")
        
        for t in threats[:10]:  # 显示最近10个
            print(f"  - [{t['severity']}] {t['threat_type']}")
            print(f"    {t['description']}")
            print(f"    时间: {t['timestamp']}")
        
        # 封禁状态
        ban = session.query(BanRecord).filter(
            BanRecord.ip == ip,
            BanRecord.is_active == True
        ).first()
        
        if ban:
            print(f"\n封禁状态: 已封禁")
            print(f"  封禁时间: {ban.banned_at}")
            print(f"  解封时间: {ban.ban_until if ban.ban_until else '永久'}")
            print(f"  原因: {ban.reason}")
            print(f"  封禁次数: {ban.ban_count}")
        else:
            print(f"\n封禁状态: 未封禁")
    finally:
        session.close()


def list_threats(db, threat_detector, hours):
    """列出最近的威胁"""
    from models.database import ThreatEvent
    from datetime import datetime, timedelta
    
    session = db.get_session()
    try:
        cutoff = datetime.now() - timedelta(hours=hours)
        
        threats = session.query(ThreatEvent).filter(
            ThreatEvent.timestamp >= cutoff
        ).order_by(ThreatEvent.timestamp.desc()).limit(50).all()
        
        print(f"\n最近 {hours} 小时内的威胁事件 (显示最多50个):\n")
        
        if not threats:
            print("没有威胁事件")
            return
        
        print(f"{'时间':<20} {'IP':<20} {'类型':<20} {'严重程度':<10} {'描述'}")
        print("-" * 100)
        
        for t in threats:
            time_str = t.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            print(f"{time_str:<20} {t.ip:<20} {t.threat_type:<20} "
                  f"{t.severity:<10} {t.description[:40]}")
    finally:
        session.close()


def list_chains(db, identity_chain_mgr, limit):
    """列出身份链"""
    chains = identity_chain_mgr.list_all_chains(limit)
    
    if not chains:
        print("没有身份链记录")
        return
    
    print(f"\n共 {len(chains)} 个身份链:\n")
    print(f"{'ID':<10} {'根哈希':<20} {'指纹数':<10} {'访问数':<10} {'威胁分':<10} {'描述'}")
    print("-" * 100)
    
    for chain in chains:
        print(f"{chain['id']:<10} {chain['root_hash'][:16]+'...':<20} "
              f"{chain['fingerprint_count']:<10} {chain['total_visits']:<10} "
              f"{chain['threat_score']:<10} {chain['description'][:30]}")


def show_stats(db):
    """显示统计信息"""
    from models.database import AccessLog, Fingerprint, IdentityChain, ThreatEvent, BanRecord
    from sqlalchemy import func
    from datetime import datetime, timedelta
    
    session = db.get_session()
    try:
        cutoff_24h = datetime.now() - timedelta(hours=24)
        
        print("\n=== 系统统计 ===\n")
        
        # 总体统计
        total_logs = session.query(func.count(AccessLog.id)).scalar()
        total_fps = session.query(func.count(Fingerprint.id)).scalar()
        total_chains = session.query(func.count(IdentityChain.id)).scalar()
        
        print(f"总访问记录: {total_logs:,}")
        print(f"总指纹数: {total_fps:,}")
        print(f"总身份链: {total_chains:,}")
        
        # 24小时统计
        print(f"\n24小时内:")
        
        requests_24h = session.query(func.count(AccessLog.id)).filter(
            AccessLog.timestamp >= cutoff_24h
        ).scalar()
        
        unique_ips_24h = session.query(func.count(func.distinct(AccessLog.ip))).filter(
            AccessLog.timestamp >= cutoff_24h
        ).scalar()
        
        threats_24h = session.query(func.count(ThreatEvent.id)).filter(
            ThreatEvent.timestamp >= cutoff_24h
        ).scalar()
        
        print(f"  请求数: {requests_24h:,}")
        print(f"  唯一IP: {unique_ips_24h:,}")
        print(f"  威胁事件: {threats_24h:,}")
        
        # 封禁统计
        active_bans = session.query(func.count(BanRecord.id)).filter(
            BanRecord.is_active == True
        ).scalar()
        
        permanent_bans = session.query(func.count(BanRecord.id)).filter(
            BanRecord.is_active == True,
            BanRecord.is_permanent == True
        ).scalar()
        
        print(f"\n封禁:")
        print(f"  活跃封禁: {active_bans}")
        print(f"  永久封禁: {permanent_bans}")
        
    finally:
        session.close()


def export_records(export_mgr, args):
    """导出记录"""
    export_type = args.type
    
    if export_type == 'bans':
        export_mgr.export_ban_records(
            output_file=args.output,
            format=args.format,
            active_only=args.active_only,
            days=args.days
        )
    elif export_type == 'threats':
        export_mgr.export_threat_events(
            output_file=args.output,
            format=args.format,
            days=args.days or 7
        )
    elif export_type == 'scores':
        export_mgr.export_score_records(
            output_file=args.output,
            format=args.format
        )
    elif export_type == 'logs':
        export_mgr.export_access_logs(
            output_file=args.output,
            format=args.format,
            hours=args.days * 24 if args.days else 24
        )
    elif export_type == 'all':
        export_mgr.export_all_records(format=args.format)


def main():
    parser = argparse.ArgumentParser(description='防火墙命令行管理工具')
    parser.add_argument('-c', '--config', default='config.yaml', help='配置文件路径')
    
    subparsers = parser.add_subparsers(dest='command', help='命令')
    
    # 封禁相关
    ban_parser = subparsers.add_parser('ban', help='封禁IP')
    ban_parser.add_argument('ip', help='要封禁的IP地址')
    ban_parser.add_argument('-r', '--reason', default='手动封禁', help='封禁原因')
    ban_parser.add_argument('-d', '--duration', type=int, default=3600, help='封禁时长(秒)')
    
    unban_parser = subparsers.add_parser('unban', help='解封IP')
    unban_parser.add_argument('ip', help='要解封的IP地址')
    
    list_bans_parser = subparsers.add_parser('list-bans', help='列出所有封禁')
    
    # 搜索
    search_parser = subparsers.add_parser('search', help='搜索IP信息')
    search_parser.add_argument('ip', help='要搜索的IP地址')
    
    # 威胁
    threats_parser = subparsers.add_parser('threats', help='列出威胁事件')
    threats_parser.add_argument('--hours', type=int, default=24, help='时间范围(小时)')
    
    # 身份链
    chains_parser = subparsers.add_parser('chains', help='列出身份链')
    chains_parser.add_argument('--limit', type=int, default=50, help='显示数量')
    
    # 统计
    stats_parser = subparsers.add_parser('stats', help='显示统计信息')
    
    # 导出记录
    export_parser = subparsers.add_parser('export', help='导出记录')
    export_parser.add_argument('type', choices=['bans', 'threats', 'scores', 'logs', 'all'],
                               help='导出类型')
    export_parser.add_argument('-f', '--format', choices=['json', 'csv', 'txt'], 
                               default='json', help='导出格式')
    export_parser.add_argument('-o', '--output', help='输出文件路径')
    export_parser.add_argument('--days', type=int, help='最近N天的记录')
    export_parser.add_argument('--active-only', action='store_true', 
                               help='只导出活跃的封禁')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # 加载配置和初始化
    config = load_config(args.config)
    db = Database(config)
    firewall = FirewallExecutor(db, config)
    threat_detector = ThreatDetector(db, config)
    fingerprint_gen = FingerprintGenerator(config)
    identity_chain_mgr = IdentityChainManager(db, config, fingerprint_gen)
    
    # 导入导出管理器
    from core.export_manager import ExportManager
    export_mgr = ExportManager(db, config)
    
    # 执行命令
    if args.command == 'ban':
        ban_ip(db, firewall, args.ip, args.reason, args.duration)
    elif args.command == 'unban':
        unban_ip(db, firewall, args.ip)
    elif args.command == 'list-bans':
        list_bans(db, firewall)
    elif args.command == 'search':
        search_ip(db, threat_detector, args.ip)
    elif args.command == 'threats':
        list_threats(db, threat_detector, args.hours)
    elif args.command == 'chains':
        list_chains(db, identity_chain_mgr, args.limit)
    elif args.command == 'stats':
        show_stats(db)
    elif args.command == 'export':
        export_records(export_mgr, args)


if __name__ == '__main__':
    main()

