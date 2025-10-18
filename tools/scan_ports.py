#!/usr/bin/env python3
"""
端口扫描工具
扫描并显示服务器开启的端口
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.helpers import load_config
from models.database import Database
from core.port_scanner import PortScanner
from tabulate import tabulate


def main():
    print("="*60)
    print("  🔍 服务器端口扫描")
    print("="*60)
    
    # 初始化
    config = load_config('config.yaml')
    db = Database(config)
    scanner = PortScanner(db, config)
    
    # 扫描监听端口
    print("\n正在扫描服务器监听端口...")
    listening_ports = scanner.get_listening_ports()
    
    if not listening_ports:
        print("未检测到开放端口")
        return
    
    # 分类显示
    categorized = scanner.categorize_ports(listening_ports)
    
    print(f"\n扫描完成！共检测到 {len(listening_ports)} 个端口\n")
    
    # 外部端口（公开）
    if categorized['external']:
        print("="*60)
        print("  🌐 外部可访问端口（公网）")
        print("="*60)
        
        table_data = []
        for p in categorized['external']:
            table_data.append([
                p['port'],
                p['protocol'].upper(),
                p['service'],
                p['listen_address'],
                p.get('process', '-')
            ])
        
        headers = ['端口', '协议', '服务', '监听地址', '进程']
        print(tabulate(table_data, headers=headers, tablefmt='grid'))
        print()
    
    # 内部端口
    if categorized['internal']:
        print("="*60)
        print("  🔒 内部端口（仅本地）")
        print("="*60)
        
        table_data = []
        for p in categorized['internal']:
            table_data.append([
                p['port'],
                p['protocol'].upper(),
                p['service'],
                p['listen_address']
            ])
        
        headers = ['端口', '协议', '服务', '监听地址']
        print(tabulate(table_data, headers=headers, tablefmt='grid'))
        print()
    
    # 按类别分组
    print("="*60)
    print("  📊 按服务分类")
    print("="*60)
    
    categories = {
        'web': 'Web服务',
        'database': '数据库',
        'remote': '远程管理',
        'email': '邮件服务',
        'dns': 'DNS服务',
        'other': '其他服务'
    }
    
    for key, name in categories.items():
        if categorized[key]:
            ports_str = ', '.join(str(p['port']) for p in categorized[key])
            print(f"{name:12s}: {ports_str}")
    
    print("\n" + "="*60)
    print("  ✓ 扫描完成")
    print("="*60)
    print(f"\n总计: {len(listening_ports)} 个端口")
    print(f"外部: {len(categorized['external'])} 个（需要注意安全）")
    print(f"内部: {len(categorized['internal'])} 个")
    print()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n扫描已取消")
        sys.exit(0)
    except Exception as e:
        print(f"\n错误: {e}")
        sys.exit(1)

