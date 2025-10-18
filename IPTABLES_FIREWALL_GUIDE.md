# 🔥 基于iptables的增强防火墙系统

## 概述

本系统实现了一个功能完整、高性能的基于iptables的防火墙管理系统。

## 架构设计

### 自定义链结构

```
INPUT链
  ├── FIREWALL_BANS (IP封禁)
  ├── FIREWALL_RATE_LIMIT (频率限制)
  └── FIREWALL_PORT_RULES (端口规则)
```

**优势**：
- 规则组织清晰
- 便于管理和调试
- 不影响现有iptables规则
- 可以独立开关

## 核心功能

### 1. IP封禁管理

#### 基础封禁
```python
from core.firewall_enhanced import IptablesManager

firewall = IptablesManager(db, config)

# 封禁IP
firewall.ban_ip("1.2.3.4", "DDoS攻击")

# 临时封禁（1小时）
firewall.ban_ip("1.2.3.5", "暴力破解", duration_seconds=3600)

# 解封IP
firewall.unban_ip("1.2.3.4")
```

#### 批量操作
```python
# 批量封禁
ips = ["1.2.3.4", "1.2.3.5", "1.2.3.6"]
results = firewall.ban_ips_batch(ips, "批量封禁")

# 批量解封
results = firewall.unban_ips_batch(ips)
```

#### 封禁验证
```python
# 验证IP是否被封禁
is_banned, details = firewall.verify_ban("1.2.3.4")
print(f"封禁状态: {is_banned}")
print(f"详情: {details}")
```

### 2. 端口管理

#### 开放端口
```python
# 开放HTTP端口（所有来源）
firewall.open_port(80, 'tcp')

# 开放MySQL端口（仅特定IP）
firewall.open_port(3306, 'tcp', source_ip="192.168.1.100")
```

#### 关闭端口
```python
# 关闭端口
firewall.close_port(3306, 'tcp')
```

#### 阻止端口
```python
# 主动拒绝端口访问
firewall.block_port(23, 'tcp')  # 阻止Telnet
```

### 3. 频率限制

```python
# 添加频率限制：10次/分钟
firewall.add_rate_limit(limit=10, period=60)

# 针对特定端口的频率限制
firewall.add_rate_limit(limit=30, period=60, port=80)
```

### 4. 规则持久化

```python
# 保存规则（重启后保留）
firewall.save_rules('/etc/iptables/rules.v4')

# 恢复规则
firewall.restore_rules('/etc/iptables/rules.v4')
```

### 5. 统计和监控

```python
# 获取防火墙统计
stats = firewall.get_firewall_stats()
print(f"总封禁数: {stats['total_bans']}")
print(f"阻止数据包: {stats['total_packets_blocked']}")
print(f"阻止字节数: {stats['total_bytes_blocked']}")

# 列出所有被封禁的IP
banned_ips = firewall.list_banned_ips()
for ban in banned_ips:
    print(f"IP: {ban['ip']}, 阻止包数: {ban['packets_blocked']}")
```

### 6. 健康检查

```python
# 防火墙健康检查
is_healthy, checks = firewall.health_check()

if is_healthy:
    print("✓ 防火墙运行正常")
else:
    print("✗ 防火墙存在问题:")
    for check, status in checks.items():
        print(f"  {check}: {'✓' if status else '✗'}")
```

## 实际iptables命令

### 系统生成的规则示例

```bash
# 查看自定义链
iptables -L FIREWALL_BANS -n -v

# 输出示例：
Chain FIREWALL_BANS (1 references)
pkts bytes target  prot opt in out source      destination
  42 2520 DROP    all  --  *  *   1.2.3.4     0.0.0.0/0    /* Firewall: DDoS攻击 */
   0    0 DROP    all  --  *  *   1.2.3.5     0.0.0.0/0    /* Firewall: 暴力破解 | Expires: 2025-10-18 15:30 */
```

### 手动管理（如果需要）

```bash
# 查看所有规则
iptables -L -n -v

# 查看特定链
iptables -L FIREWALL_BANS -n --line-numbers

# 手动删除规则
iptables -D FIREWALL_BANS 1

# 清空链
iptables -F FIREWALL_BANS

# 保存规则
iptables-save > /etc/iptables/rules.v4

# 恢复规则
iptables-restore < /etc/iptables/rules.v4
```

## Docker环境配置

### docker-compose.yml

```yaml
services:
  firewall:
    image: zbaimo/nginx-firewall:latest
    
    # 需要特权模式来操作iptables
    privileged: true
    
    # 或使用能力授权（推荐）
    cap_add:
      - NET_ADMIN
      - NET_RAW
    
    # 主机网络模式（可选，性能最佳）
    network_mode: "host"
    
    volumes:
      # 持久化iptables规则
      - ./iptables-rules:/etc/iptables
```

### Dockerfile

```dockerfile
FROM python:3.11-slim

# 安装iptables
RUN apt-get update && apt-get install -y \
    iptables \
    ipset \
    iptables-persistent \
    && rm -rf /var/lib/apt/lists/*

# ... 其他配置
```

## 系统集成

### 与现有系统集成

```python
# main.py
from core.firewall_enhanced import IptablesManager

# 初始化
firewall = IptablesManager(db, config)

# 威胁检测后自动封禁
def handle_threat(ip, threat_type):
    if threat_type in ['ddos', 'bruteforce']:
        # 封禁1小时
        firewall.ban_ip(ip, f"检测到{threat_type}", duration_seconds=3600)
    elif threat_type == 'sql_injection':
        # 永久封禁
        firewall.ban_ip(ip, "SQL注入攻击")

# 定期检查过期封禁
import schedule
schedule.every(5).minutes.do(firewall.check_expired_bans)
```

## 性能优化

### 1. 使用ipset管理大量IP

```python
# 对于大量IP，使用ipset更高效
import subprocess

# 创建ipset集合
subprocess.run(['ipset', 'create', 'blacklist', 'hash:ip'])

# 添加IP到集合
subprocess.run(['ipset', 'add', 'blacklist', '1.2.3.4'])

# 创建iptables规则匹配集合
subprocess.run([
    'iptables', '-A', 'INPUT',
    '-m', 'set', '--match-set', 'blacklist', 'src',
    '-j', 'DROP'
])
```

### 2. 规则优化

- 高频规则放在前面
- 使用自定义链分类管理
- 定期清理过期规则
- 使用conntrack限制连接数

### 3. 批量操作

```python
# 使用iptables-restore批量导入
rules = """
*filter
:FIREWALL_BANS - [0:0]
-A FIREWALL_BANS -s 1.2.3.4 -j DROP
-A FIREWALL_BANS -s 1.2.3.5 -j DROP
-A FIREWALL_BANS -s 1.2.3.6 -j DROP
COMMIT
"""

subprocess.run(['iptables-restore', '-n'], input=rules, text=True)
```

## 监控和告警

### 实时监控

```python
import time

def monitor_firewall():
    while True:
        stats = firewall.get_firewall_stats()
        
        # 检查异常
        if stats['total_bans'] > 1000:
            send_alert("防火墙封禁数量异常")
        
        if stats['total_packets_blocked'] > 1000000:
            send_alert("阻止的数据包异常多")
        
        time.sleep(60)
```

### 日志集成

```python
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/firewall.log'),
        logging.StreamHandler()
    ]
)
```

## Web界面集成

### API端点

```python
# web/app.py

@app.route('/api/firewall/ban', methods=['POST'])
def api_ban_ip():
    data = request.json
    ip = data.get('ip')
    reason = data.get('reason', 'Manual ban')
    duration = data.get('duration')  # 秒
    
    success = firewall.ban_ip(ip, reason, duration)
    return jsonify({'success': success})

@app.route('/api/firewall/stats')
def api_firewall_stats():
    stats = firewall.get_firewall_stats()
    return jsonify(stats)

@app.route('/api/firewall/health')
def api_firewall_health():
    is_healthy, checks = firewall.health_check()
    return jsonify({
        'healthy': is_healthy,
        'checks': checks
    })
```

## 故障排查

### 常见问题

#### 1. 权限不足

```bash
# 检查是否有iptables权限
iptables -L

# 如果报错，需要root权限或使用sudo
sudo iptables -L

# Docker容器中需要privileged或cap_add
```

#### 2. 规则不生效

```bash
# 检查自定义链是否正确挂载
iptables -L INPUT -n | grep FIREWALL

# 如果没有，手动添加跳转
iptables -I INPUT 1 -j FIREWALL_BANS
```

#### 3. 规则丢失（重启后）

```bash
# 安装iptables-persistent
apt-get install iptables-persistent

# 保存规则
netfilter-persistent save

# 或手动保存
iptables-save > /etc/iptables/rules.v4
```

#### 4. 性能问题

```bash
# 查看规则数量
iptables -L -n | wc -l

# 如果规则过多（>1000），考虑使用ipset

# 优化规则顺序
iptables -L INPUT -n --line-numbers
# 将高频规则移到前面
```

## 安全最佳实践

### 1. 白名单优先

```python
# 始终先检查白名单
if not firewall.is_whitelisted(ip):
    firewall.ban_ip(ip, reason)
```

### 2. 限制最大封禁数

```python
MAX_BANS = 10000

def safe_ban_ip(ip, reason):
    current_bans = len(firewall.list_banned_ips())
    if current_bans >= MAX_BANS:
        logger.error("封禁数量已达上限")
        return False
    return firewall.ban_ip(ip, reason)
```

### 3. 定期备份规则

```bash
# 设置cron任务每天备份
0 2 * * * /usr/sbin/iptables-save > /backup/iptables-$(date +\%Y\%m\%d).rules
```

### 4. 审计日志

```python
# 所有防火墙操作都记录审计日志
from core.audit_logger import AuditLogger

audit = AuditLogger()

def ban_with_audit(ip, reason, operator):
    success = firewall.ban_ip(ip, reason)
    audit.log(
        action='firewall_ban',
        operator=operator,
        target=ip,
        result='success' if success else 'failed',
        details={'reason': reason}
    )
    return success
```

## 测试

### 单元测试

```python
import unittest

class TestIptablesManager(unittest.TestCase):
    def setUp(self):
        self.firewall = IptablesManager(db, config)
    
    def test_ban_ip(self):
        ip = "192.0.2.1"  # TEST-NET-1
        result = self.firewall.ban_ip(ip, "测试")
        self.assertTrue(result)
        
        # 验证封禁
        is_banned, _ = self.firewall.verify_ban(ip)
        self.assertTrue(is_banned)
        
        # 清理
        self.firewall.unban_ip(ip)
    
    def test_health_check(self):
        is_healthy, checks = self.firewall.health_check()
        self.assertTrue(is_healthy)
        self.assertTrue(checks['iptables_available'])
```

## 命令行工具

### CLI管理

```python
# tools/firewall_cli.py

import click

@click.group()
def cli():
    """防火墙管理CLI"""
    pass

@cli.command()
@click.argument('ip')
@click.option('--reason', default='Manual ban')
def ban(ip, reason):
    """封禁IP"""
    success = firewall.ban_ip(ip, reason)
    if success:
        click.echo(f"✓ 已封禁: {ip}")
    else:
        click.echo(f"✗ 封禁失败: {ip}")

@cli.command()
@click.argument('ip')
def unban(ip):
    """解封IP"""
    success = firewall.unban_ip(ip)
    if success:
        click.echo(f"✓ 已解封: {ip}")

@cli.command()
def stats():
    """显示统计信息"""
    stats = firewall.get_firewall_stats()
    click.echo(f"总封禁数: {stats['total_bans']}")
    click.echo(f"阻止包数: {stats['total_packets_blocked']}")

@cli.command()
def health():
    """健康检查"""
    is_healthy, checks = firewall.health_check()
    if is_healthy:
        click.echo("✓ 防火墙运行正常")
    else:
        click.echo("✗ 防火墙存在问题")

if __name__ == '__main__':
    cli()
```

使用：
```bash
python tools/firewall_cli.py ban 1.2.3.4 --reason="测试封禁"
python tools/firewall_cli.py unban 1.2.3.4
python tools/firewall_cli.py stats
python tools/firewall_cli.py health
```

## 总结

### 系统特点

✅ **功能完整**
- IP封禁/解封
- 端口管理
- 频率限制
- 规则持久化

✅ **高性能**
- 自定义链优化
- 批量操作支持
- 规则缓存

✅ **易于管理**
- Web界面集成
- CLI工具
- 健康检查

✅ **生产就绪**
- 错误处理
- 日志记录
- 监控告警

### 下一步

1. 集成到main.py
2. 添加Web API
3. 配置Docker权限
4. 测试和优化

---

**增强型防火墙已就绪！** 🔥

访问: `core/firewall_enhanced.py`

