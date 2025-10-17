"""
测试日志生成器
用于生成模拟的nginx日志，测试系统功能
"""
import random
from datetime import datetime, timedelta


# 测试数据
TEST_IPS = [
    "192.168.1.100",
    "192.168.1.101", 
    "10.0.0.50",
    "203.0.113.45",  # 正常访问
    "198.51.100.66",  # 扫描攻击
    "203.0.113.89",   # SQL注入
    "198.51.100.123", # XSS攻击
]

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)",
    "Python-requests/2.28.0",
    "sqlmap/1.6",  # 恶意工具
    "nikto/2.1.5",  # 扫描工具
]

PATHS = [
    "/",
    "/api/users",
    "/api/posts",
    "/admin/login",
    "/static/css/style.css",
    "/images/logo.png",
]

ATTACK_PATHS = [
    "/admin",
    "/.env",
    "/.git/config",
    "/phpmyadmin",
    "/wp-admin",
    "/backup.sql",
    "/config.php",
    "/../../etc/passwd",
]

SQL_INJECTION_PARAMS = [
    "?id=1' OR '1'='1",
    "?user=admin' --",
    "?search='; DROP TABLE users--",
    "?id=1 UNION SELECT * FROM users",
]

XSS_PARAMS = [
    "?q=<script>alert(1)</script>",
    "?name=<img src=x onerror=alert(1)>",
    "?comment=javascript:alert(1)",
]

STATUS_CODES = [200, 200, 200, 200, 301, 302, 404, 500]


def generate_normal_request():
    """生成正常请求"""
    ip = random.choice(TEST_IPS[:4])
    ua = random.choice(USER_AGENTS[:3])
    path = random.choice(PATHS)
    status = random.choice([200, 200, 200, 301, 302, 404])
    size = random.randint(1000, 50000)
    time = datetime.now().strftime("%d/%b/%Y:%H:%M:%S +0800")
    
    return f'{ip} - - [{time}] "GET {path} HTTP/1.1" {status} {size} "-" "{ua}"\n'


def generate_scan_attack():
    """生成扫描攻击"""
    ip = "198.51.100.66"
    ua = random.choice(USER_AGENTS[3:6])
    path = random.choice(ATTACK_PATHS)
    status = 404
    size = random.randint(100, 500)
    time = datetime.now().strftime("%d/%b/%Y:%H:%M:%S +0800")
    
    return f'{ip} - - [{time}] "GET {path} HTTP/1.1" {status} {size} "-" "{ua}"\n'


def generate_sql_injection():
    """生成SQL注入攻击"""
    ip = "203.0.113.89"
    ua = "sqlmap/1.6"
    path = "/api/users" + random.choice(SQL_INJECTION_PARAMS)
    status = random.choice([200, 500])
    size = random.randint(500, 2000)
    time = datetime.now().strftime("%d/%b/%Y:%H:%M:%S +0800")
    
    return f'{ip} - - [{time}] "GET {path} HTTP/1.1" {status} {size} "-" "{ua}"\n'


def generate_xss_attack():
    """生成XSS攻击"""
    ip = "198.51.100.123"
    ua = random.choice(USER_AGENTS[:3])
    path = "/search" + random.choice(XSS_PARAMS)
    status = 200
    size = random.randint(1000, 3000)
    time = datetime.now().strftime("%d/%b/%Y:%H:%M:%S +0800")
    
    return f'{ip} - - [{time}] "GET {path} HTTP/1.1" {status} {size} "-" "{ua}"\n'


def generate_rate_limit_attack():
    """生成频率限制攻击（快速大量请求）"""
    ip = "198.51.100.88"
    ua = "Python-requests/2.28.0"
    path = random.choice(PATHS)
    status = 200
    size = random.randint(500, 2000)
    time = datetime.now().strftime("%d/%b/%Y:%H:%M:%S +0800")
    
    return f'{ip} - - [{time}] "GET {path} HTTP/1.1" {status} {size} "-" "{ua}"\n'


def generate_test_logs(filename="test_access.log", count=1000):
    """
    生成测试日志文件
    
    Args:
        filename: 输出文件名
        count: 生成的日志条数
    """
    print(f"正在生成 {count} 条测试日志...")
    
    with open(filename, 'w', encoding='utf-8') as f:
        for i in range(count):
            # 生成不同类型的请求
            rand = random.random()
            
            if rand < 0.70:  # 70% 正常请求
                log = generate_normal_request()
            elif rand < 0.80:  # 10% 扫描攻击
                log = generate_scan_attack()
            elif rand < 0.85:  # 5% SQL注入
                log = generate_sql_injection()
            elif rand < 0.90:  # 5% XSS攻击
                log = generate_xss_attack()
            else:  # 10% 频率限制攻击
                log = generate_rate_limit_attack()
            
            f.write(log)
            
            if (i + 1) % 100 == 0:
                print(f"已生成 {i + 1}/{count} 条")
    
    print(f"✓ 完成！日志已保存到: {filename}")
    print("\n日志类型分布:")
    print("  - 70% 正常请求")
    print("  - 10% 路径扫描攻击")
    print("  - 5%  SQL注入攻击")
    print("  - 5%  XSS攻击")
    print("  - 10% 频率限制攻击")
    print("\n使用方法:")
    print(f"  python main.py --batch {filename}")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='生成测试nginx日志')
    parser.add_argument('-o', '--output', default='test_access.log', help='输出文件名')
    parser.add_argument('-n', '--count', type=int, default=1000, help='生成的日志条数')
    
    args = parser.parse_args()
    
    generate_test_logs(args.output, args.count)

