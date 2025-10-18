#!/usr/bin/env python3
"""
初始化默认规则
首次启动时自动创建默认的威胁检测规则和自定义规则
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from utils.helpers import load_config
from models.database import Database, ThreatDetectionRule, ScoringRule


def init_default_threat_rules(db):
    """初始化默认威胁检测规则"""
    
    default_rules = [
        {
            'category': 'sql_injection',
            'name': 'SQL注入检测',
            'description': '检测常见的SQL注入攻击模式',
            'enabled': True,
            'patterns': json.dumps([
                "union.*select",
                "select.*from",
                "insert.*into",
                "delete.*from",
                "drop.*table",
                "exec.*xp_",
                "'; --",
                "' or '1'='1",
                "admin'--",
                "' or 1=1--"
            ]),
            'threat_score': 50
        },
        {
            'category': 'xss_attack',
            'name': 'XSS攻击检测',
            'description': '检测跨站脚本攻击',
            'enabled': True,
            'patterns': json.dumps([
                "<script",
                "javascript:",
                "onerror=",
                "onload=",
                "eval\\(",
                "alert\\(",
                "document.cookie",
                "<iframe"
            ]),
            'threat_score': 40
        },
        {
            'category': 'rate_limit',
            'name': '频率限制',
            'description': '检测异常高频访问',
            'enabled': True,
            'parameters': json.dumps({
                'window_seconds': 60,
                'max_requests': 100
            }),
            'threat_score': 25
        },
        {
            'category': 'scan_detection',
            'name': '路径扫描检测',
            'description': '检测404路径扫描行为',
            'enabled': True,
            'parameters': json.dumps({
                'window_seconds': 300,
                'max_404_count': 20
            }),
            'threat_score': 30
        },
        {
            'category': 'sensitive_path',
            'name': '敏感路径访问',
            'description': '检测敏感文件和目录访问',
            'enabled': True,
            'patterns': json.dumps([
                "/.env",
                "/.git",
                "/admin",
                "/phpmyadmin",
                "/wp-admin",
                "/.aws",
                "/.ssh",
                "/config",
                "/backup"
            ]),
            'threat_score': 15
        },
        {
            'category': 'bad_user_agent',
            'name': '恶意User-Agent检测',
            'description': '检测扫描工具和恶意爬虫',
            'enabled': True,
            'patterns': json.dumps([
                "masscan",
                "nmap",
                "nikto",
                "sqlmap",
                "acunetix",
                "burpsuite",
                "metasploit",
                "nessus"
            ]),
            'threat_score': 20
        }
    ]
    
    session = db.get_session()
    try:
        # 检查是否已经初始化
        existing_count = session.query(ThreatDetectionRule).count()
        if existing_count > 0:
            print(f"✓ 威胁检测规则已存在（{existing_count}条），跳过初始化")
            return
        
        # 添加默认规则
        for rule_data in default_rules:
            rule = ThreatDetectionRule(**rule_data)
            session.add(rule)
        
        session.commit()
        print(f"✓ 已初始化 {len(default_rules)} 条默认威胁检测规则")
        
    except Exception as e:
        print(f"✗ 初始化威胁检测规则失败: {e}")
        session.rollback()
    finally:
        session.close()


def init_default_custom_rules(db):
    """初始化默认自定义规则"""
    
    default_rules = [
        {
            'name': '深夜管理员访问',
            'description': '检测凌晨2-5点的管理后台访问',
            'enabled': True,
            'rule_type': 'time',
            'conditions': json.dumps({
                'time_range': '02:00-05:00',
                'path_contains': '/admin'
            }),
            'score': 30,
            'action': 'score',
            'priority': 100
        },
        {
            'name': '快速行为变化',
            'description': '检测短时间内行为模式急剧变化',
            'enabled': True,
            'rule_type': 'behavior',
            'conditions': json.dumps({
                'behavior_change_rate': 0.8,
                'time_window': 300
            }),
            'score': 25,
            'action': 'score',
            'priority': 90
        },
        {
            'name': '地理位置异常',
            'description': '检测短时间内地理位置大幅变化',
            'enabled': True,
            'rule_type': 'geo',
            'conditions': json.dumps({
                'distance_threshold': 1000,
                'time_window': 3600
            }),
            'score': 20,
            'action': 'score',
            'priority': 80
        }
    ]
    
    session = db.get_session()
    try:
        # 检查是否已经初始化
        existing_count = session.query(ScoringRule).count()
        if existing_count > 0:
            print(f"✓ 自定义规则已存在（{existing_count}条），跳过初始化")
            return
        
        # 添加默认规则
        for rule_data in default_rules:
            rule = ScoringRule(**rule_data)
            session.add(rule)
        
        session.commit()
        print(f"✓ 已初始化 {len(default_rules)} 条默认自定义规则")
        
    except Exception as e:
        print(f"✗ 初始化自定义规则失败: {e}")
        session.rollback()
    finally:
        session.close()


def main():
    """主函数"""
    print("="*60)
    print("  初始化默认规则")
    print("="*60)
    
    # 加载配置
    config = load_config('config.yaml')
    
    # 初始化数据库
    db = Database(config)
    
    # 初始化规则
    init_default_threat_rules(db)
    init_default_custom_rules(db)
    
    print("\n" + "="*60)
    print("  ✓ 默认规则初始化完成")
    print("="*60)
    print("\n访问 Web 界面管理规则：")
    print("  - 威胁检测规则: http://your-server:8080/rules")
    print("  - 自定义规则: http://your-server:8080/rules")
    print("="*60)


if __name__ == '__main__':
    main()

