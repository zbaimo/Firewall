# 🛠️ 防火墙CLI管理工具使用指南

## 安装

确保已安装依赖：
```bash
pip install click tabulate
```

或使用requirements.txt：
```bash
pip install -r requirements.txt
```

## 基础用法

```bash
# 显示帮助
python tools/firewall_cli.py --help

# 查看子命令帮助
python tools/firewall_cli.py ban --help
```

---

## IP封禁管理

### 封禁IP

```bash
# 永久封禁
python tools/firewall_cli.py ban 1.2.3.4

# 指定原因
python tools/firewall_cli.py ban 1.2.3.4 --reason="DDoS攻击"

# 临时封禁（1小时）
python tools/firewall_cli.py ban 1.2.3.4 -r "暴力破解" -d 3600

# 临时封禁（24小时）
python tools/firewall_cli.py ban 1.2.3.5 -d 86400
```

### 解封IP

```bash
# 解封单个IP
python tools/firewall_cli.py unban 1.2.3.4

# 验证解封
python tools/firewall_cli.py verify 1.2.3.4
```

### 批量操作

```bash
# 批量封禁
python tools/firewall_cli.py ban-batch 1.2.3.4 1.2.3.5 1.2.3.6 --reason="批量封禁"

# 批量解封
python tools/firewall_cli.py unban-batch 1.2.3.4 1.2.3.5 1.2.3.6
```

### 列出封禁

```bash
# 列出所有封禁的IP
python tools/firewall_cli.py list

# 输出示例：
# ╔════════════════╦═══════════╦═══════════════╦══════════════════════╗
# ║ IP地址         ║ 阻止包数  ║ 阻止字节数    ║ iptables链           ║
# ╠════════════════╬═══════════╬═══════════════╬══════════════════════╣
# ║ 1.2.3.4        ║ 1,234     ║ 567,890       ║ FIREWALL_BANS        ║
# ║ 1.2.3.5        ║ 456       ║ 123,456       ║ FIREWALL_BANS        ║
# ╚════════════════╩═══════════╩═══════════════╩══════════════════════╝
```

### 验证封禁

```bash
# 验证IP是否被封禁
python tools/firewall_cli.py verify 1.2.3.4

# 输出示例：
# ✓ IP已被封禁: 1.2.3.4
#
# 详情:
#   ip: 1.2.3.4
#   is_banned: True
#   chain: FIREWALL_BANS
#   verified_at: 2025-10-18T12:30:45
```

---

## 端口管理

### 开放端口

```bash
# 开放HTTP端口
python tools/firewall_cli.py open-port 80

# 开放MySQL端口（TCP）
python tools/firewall_cli.py open-port 3306 --protocol tcp

# 开放DNS端口（UDP）
python tools/firewall_cli.py open-port 53 -p udp

# 开放端口（仅允许特定IP）
python tools/firewall_cli.py open-port 22 --source 192.168.1.100
```

### 关闭端口

```bash
# 关闭端口
python tools/firewall_cli.py close-port 3306

# 关闭UDP端口
python tools/firewall_cli.py close-port 53 -p udp
```

### 阻止端口

```bash
# 阻止Telnet端口
python tools/firewall_cli.py block-port 23

# 阻止危险服务
python tools/firewall_cli.py block-port 3389  # RDP
```

---

## 频率限制

```bash
# 添加全局频率限制（10次/分钟）
python tools/firewall_cli.py ratelimit --limit 10 --period 60

# 针对HTTP端口的频率限制（30次/分钟）
python tools/firewall_cli.py ratelimit -l 30 -p 60 --port 80

# 严格限制（5次/分钟）
python tools/firewall_cli.py ratelimit -l 5 -p 60
```

---

## 统计和监控

### 查看统计

```bash
python tools/firewall_cli.py stats

# 输出示例：
# ==================================================
#   防火墙统计信息
# ==================================================
#
# 总封禁数:     42
# 阻止数据包:   12,345
# 阻止字节数:   5,678,901 bytes
#
# iptables链规则数:
#   - 封禁链:     42
#   - 频率限制:   3
#   - 端口规则:   8
#
# 更新时间: 2025-10-18T12:30:45
# ==================================================
```

### 健康检查

```bash
python tools/firewall_cli.py health

# 输出示例：
# ==================================================
#   ✓ 防火墙运行正常
# ==================================================
#
# 检查项:
#   ✓ iptables_available: 通过
#   ✓ chain_FIREWALL_BANS: 通过
#   ✓ chain_FIREWALL_RATE_LIMIT: 通过
#   ✓ chain_FIREWALL_PORT_RULES: 通过
#   ✓ total_rules: 53
```

### Top阻止IP

```bash
# 显示阻止数据包最多的前10个IP
python tools/firewall_cli.py top-blocked

# 显示前20个
python tools/firewall_cli.py top-blocked --count 20
```

---

## 规则管理

### 查看规则

```bash
# 显示所有自定义链的规则
python tools/firewall_cli.py show

# 显示特定链
python tools/firewall_cli.py show --chain FIREWALL_BANS

# 详细模式（显示包统计）
python tools/firewall_cli.py show -v
```

### 保存规则

```bash
# 保存到默认位置
python tools/firewall_cli.py save

# 保存到指定文件
python tools/firewall_cli.py save --filepath /backup/iptables.rules
```

### 恢复规则

```bash
# 从默认位置恢复
python tools/firewall_cli.py restore

# 从指定文件恢复
python tools/firewall_cli.py restore -f /backup/iptables.rules
```

### 清空规则

```bash
# 清空所有自定义链
python tools/firewall_cli.py flush

# 清空特定链
python tools/firewall_cli.py flush --chain FIREWALL_BANS
```

### 清理过期封禁

```bash
# 清理所有过期的封禁
python tools/firewall_cli.py cleanup
```

---

## 导出功能

```bash
# 导出防火墙配置和统计
python tools/firewall_cli.py export

# 导出到指定文件
python tools/firewall_cli.py export --output firewall_backup.json

# 导出的JSON包含：
# - 统计信息
# - 封禁列表
# - 健康检查结果
# - 导出时间戳
```

---

## 交互式模式

```bash
# 启动交互式管理界面
python tools/firewall_cli.py interactive

# 交互式菜单：
# 1. 封禁IP
# 2. 解封IP
# 3. 列出封禁
# 4. 查看统计
# 5. 健康检查
# 0. 退出
```

---

## 测试功能

```bash
# 运行完整的功能测试
python tools/firewall_cli.py test

# 输出示例：
# ==================================================
#   防火墙功能测试
# ==================================================
#
# 测试1: 健康检查...
#   ✓ 通过
#
# 测试2: 封禁IP...
#   ✓ 通过
#
# 测试3: 验证封禁...
#   ✓ 通过
#
# 测试4: 解封IP...
#   ✓ 通过
#
# 测试5: 验证解封...
#   ✓ 通过
#
# ==================================================
#   ✓ 所有测试通过！
# ==================================================
```

---

## 实际应用场景

### 场景1：紧急封禁攻击IP

```bash
# 发现攻击，立即封禁
python tools/firewall_cli.py ban 1.2.3.4 -r "DDoS攻击" -d 3600

# 验证
python tools/firewall_cli.py verify 1.2.3.4

# 查看统计
python tools/firewall_cli.py stats
```

### 场景2：批量封禁恶意IP

```bash
# 从文件读取IP列表并封禁
cat malicious_ips.txt | xargs python tools/firewall_cli.py ban-batch --reason="恶意IP"
```

### 场景3：配置服务器端口

```bash
# 开放必要的端口
python tools/firewall_cli.py open-port 22 --source 192.168.1.100  # SSH（仅内网）
python tools/firewall_cli.py open-port 80                         # HTTP
python tools/firewall_cli.py open-port 443                        # HTTPS

# 阻止危险端口
python tools/firewall_cli.py block-port 23    # Telnet
python tools/firewall_cli.py block-port 3389  # RDP（如果不需要）
```

### 场景4：定期维护

```bash
# 每天凌晨清理过期封禁
0 2 * * * /usr/bin/python /app/tools/firewall_cli.py cleanup

# 每天备份规则
0 3 * * * /usr/bin/python /app/tools/firewall_cli.py save -f /backup/iptables-$(date +\%Y\%m\%d).rules

# 每小时检查健康状态
0 * * * * /usr/bin/python /app/tools/firewall_cli.py health | mail -s "Firewall Health" admin@example.com
```

### 场景5：灾难恢复

```bash
# 系统崩溃后恢复防火墙规则
python tools/firewall_cli.py restore -f /backup/iptables-20251018.rules

# 验证恢复
python tools/firewall_cli.py stats
python tools/firewall_cli.py health
```

---

## 集成到系统服务

### systemd服务

```ini
# /etc/systemd/system/firewall-manager.service

[Unit]
Description=Nginx Firewall Manager
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/app
ExecStart=/usr/bin/python /app/main.py
ExecStartPost=/usr/bin/python /app/tools/firewall_cli.py health
ExecReload=/bin/kill -HUP $MAINPID
Restart=always

[Install]
WantedBy=multi-user.target
```

### Docker容器

```bash
# 在容器内执行CLI
docker exec nginx-firewall python tools/firewall_cli.py stats

# 封禁IP
docker exec nginx-firewall python tools/firewall_cli.py ban 1.2.3.4

# 查看规则
docker exec nginx-firewall python tools/firewall_cli.py show
```

---

## 别名配置

为常用命令创建别名：

```bash
# 添加到 ~/.bashrc 或 ~/.zshrc

alias fw='python /app/tools/firewall_cli.py'
alias fw-ban='python /app/tools/firewall_cli.py ban'
alias fw-unban='python /app/tools/firewall_cli.py unban'
alias fw-list='python /app/tools/firewall_cli.py list'
alias fw-stats='python /app/tools/firewall_cli.py stats'
alias fw-health='python /app/tools/firewall_cli.py health'
```

使用示例：
```bash
fw-ban 1.2.3.4 -r "DDoS"
fw-stats
fw-health
```

---

## 脚本自动化

### 自动封禁脚本

```bash
#!/bin/bash
# auto_ban.sh - 自动分析日志并封禁

# 分析日志，找出异常IP
tail -n 1000 /var/log/nginx/access.log | \
  awk '{print $1}' | \
  sort | uniq -c | sort -rn | \
  awk '$1 > 100 {print $2}' | \
  while read ip; do
    python tools/firewall_cli.py ban $ip --reason="请求频率异常" -d 3600
  done
```

### 监控脚本

```bash
#!/bin/bash
# monitor_firewall.sh - 持续监控防火墙

while true; do
  clear
  echo "================================"
  echo "  防火墙实时监控"
  echo "================================"
  echo ""
  python tools/firewall_cli.py stats
  echo ""
  echo "按Ctrl+C退出"
  sleep 30
done
```

---

## 高级用法

### 组合使用

```bash
# 封禁并立即验证
python tools/firewall_cli.py ban 1.2.3.4 && \
python tools/firewall_cli.py verify 1.2.3.4

# 批量封禁后查看统计
python tools/firewall_cli.py ban-batch 1.2.3.{4..10} && \
python tools/firewall_cli.py stats

# 保存规则并导出配置
python tools/firewall_cli.py save && \
python tools/firewall_cli.py export
```

### 定时任务

```bash
# 编辑crontab
crontab -e

# 添加定时任务：

# 每5分钟清理过期封禁
*/5 * * * * /usr/bin/python /app/tools/firewall_cli.py cleanup

# 每小时保存规则
0 * * * * /usr/bin/python /app/tools/firewall_cli.py save

# 每天凌晨2点导出配置
0 2 * * * /usr/bin/python /app/tools/firewall_cli.py export -o /backup/firewall_$(date +\%Y\%m\%d).json

# 每30分钟检查健康状态
*/30 * * * * /usr/bin/python /app/tools/firewall_cli.py health >> /var/log/firewall_health.log
```

---

## 故障排查

### 检查权限

```bash
# 检查是否有iptables权限
sudo python tools/firewall_cli.py health

# 如果失败，检查：
which iptables
iptables -L
```

### 查看详细日志

```bash
# 启用Python日志
export PYTHONPATH=/app
python -u tools/firewall_cli.py stats 2>&1 | tee firewall.log
```

### 调试模式

```python
# 修改firewall_cli.py，添加调试信息
import logging
logging.basicConfig(level=logging.DEBUG)
```

---

## 最佳实践

### 1. 使用别名

创建快捷命令，提高效率

### 2. 定期备份

每天自动备份防火墙规则

### 3. 监控告警

设置健康检查和异常告警

### 4. 测试后部署

在测试环境验证后再在生产环境使用

### 5. 文档记录

记录所有手动操作的防火墙规则

---

## 快速参考

```bash
# 封禁
fw ban IP [-r REASON] [-d DURATION]

# 解封
fw unban IP

# 列表
fw list

# 统计
fw stats

# 健康
fw health

# 端口
fw open-port PORT [-p PROTOCOL] [-s SOURCE]
fw close-port PORT [-p PROTOCOL]
fw block-port PORT [-p PROTOCOL]

# 规则
fw show [-c CHAIN] [-v]
fw save [-f FILE]
fw restore [-f FILE]
fw flush [--chain CHAIN]

# 其他
fw cleanup          # 清理过期
fw top-blocked      # Top IP
fw export           # 导出
fw test             # 测试
fw interactive      # 交互式
```

---

**现在您可以通过CLI快速管理防火墙了！** 🚀

```bash
python tools/firewall_cli.py --help
```

