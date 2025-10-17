# 使用指南

## 快速开始

### 1. 启动系统

```bash
# Windows
run.bat

# Linux/macOS
./run.sh

# 或直接运行
python main.py
```

### 2. 批量处理历史日志

```bash
# 处理完整日志文件
python main.py --batch /var/log/nginx/access.log

# 只处理最近1000行
python main.py --batch /var/log/nginx/access.log --max-lines 1000
```

### 3. 访问Web管理后台

启动系统后，访问：http://localhost:8080

## 命令行管理工具

系统提供了强大的CLI管理工具：

### 查看统计信息
```bash
python tools/cli_manager.py stats
```

### 封禁管理

```bash
# 查看所有封禁
python tools/cli_manager.py list-bans

# 手动封禁IP
python tools/cli_manager.py ban 192.168.1.100 -r "手动测试" -d 3600

# 解封IP
python tools/cli_manager.py unban 192.168.1.100
```

### 搜索IP信息
```bash
python tools/cli_manager.py search 192.168.1.100
```

### 查看威胁事件
```bash
# 最近24小时的威胁
python tools/cli_manager.py threats

# 最近7天的威胁
python tools/cli_manager.py threats --hours 168
```

### 查看身份链
```bash
# 列出所有身份链
python tools/cli_manager.py chains

# 限制显示数量
python tools/cli_manager.py chains --limit 20
```

## 测试工具

### 生成测试日志

```bash
# 生成1000条测试日志
python tools/test_log_generator.py

# 生成10000条
python tools/test_log_generator.py -n 10000 -o test_large.log

# 然后处理测试日志
python main.py --batch test_access.log
```

## 核心功能说明

### 1. 指纹系统

系统会为每个访问生成两种指纹：

- **基础指纹** (base_hash): 基于 IP + User-Agent
  - 用于识别相同的"设备/客户端"
  - 例如：`sha256(192.168.1.100|Mozilla/5.0...)`

- **行为指纹** (behavior_hash): 基于请求特征
  - 用于识别访问行为模式
  - 包含：请求方法、路径、状态码等

查看某个IP的指纹：
```bash
python tools/cli_manager.py search 192.168.1.100
```

### 2. 身份链系统

当系统检测到相同的基础指纹出现多次，但行为模式发生变化时，会自动创建"身份链"。

**触发条件**（在config.yaml中配置）：
- 相同基础指纹出现次数 >= 10次
- 行为变化率 >= 30%

**示例场景**：
1. 某IP用正常浏览器访问了10次（生成基础指纹A）
2. 之后该IP行为突变，开始扫描敏感路径
3. 系统检测到行为变化，创建身份链
4. 将原有指纹A和新的行为模式关联起来
5. 后续所有相关活动都归档到这个身份链下

查看身份链：
```bash
python tools/cli_manager.py chains
```

### 3. 威胁检测

系统自动检测以下威胁类型：

| 威胁类型 | 严重程度 | 自动封禁 | 说明 |
|---------|---------|---------|------|
| SQL注入 | Critical | ✓ | 检测SQL注入特征 |
| XSS攻击 | High | ✓ | 检测XSS攻击特征 |
| 路径扫描 | High | ✓ | 大量404错误 |
| 频率限制 | High | ✓ | 请求过于频繁 |
| 敏感路径访问 | Medium | 可选 | 访问/.env等敏感文件 |
| 恶意工具 | Medium | 可选 | sqlmap、nikto等工具特征 |

配置检测规则：编辑 `config.yaml` 中的 `threat_detection` 部分

### 4. 自动封禁

**封禁规则**：
- Critical威胁：立即封禁24小时
- High威胁：立即封禁1小时
- Medium威胁：根据类型决定

**累计封禁**：
- 同一IP被封禁5次后，自动升级为永久封禁

**自动解封**：
- 系统每5分钟检查一次过期的封禁
- 自动解封已到期的临时封禁

**白名单保护**：
- 在 `config.yaml` 中配置白名单
- 白名单IP永不封禁

```yaml
firewall:
  whitelist:
    - "127.0.0.1"
    - "192.168.1.0/24"  # 支持CIDR
```

## 实际使用场景

### 场景1：防御DDoS/CC攻击

**问题**：某IP在短时间内发起大量请求

**系统响应**：
1. 检测到频率超限（60秒内>100次请求）
2. 触发 `rate_limit_exceeded` 威胁
3. 自动封禁该IP 1小时
4. 记录到威胁事件表

**配置调整**：
```yaml
threat_detection:
  rate_limit:
    window_seconds: 60
    max_requests: 100  # 根据实际情况调整
```

### 场景2：防御路径扫描

**问题**：攻击者使用工具扫描敏感路径

**系统响应**：
1. 检测到5分钟内20个404错误
2. 触发 `path_scan` 威胁
3. 检测到User-Agent包含"nikto"
4. 触发 `bad_user_agent` 威胁
5. 双重威胁，立即封禁

### 场景3：SQL注入防护

**问题**：攻击者尝试SQL注入

**系统响应**：
1. 检测到URL包含 `' OR '1'='1`
2. 触发 `sql_injection` 威胁（Critical）
3. 立即封禁24小时
4. 记录详细攻击特征

### 场景4：追踪攻击者行为演变

**问题**：攻击者更换工具或策略

**系统响应**：
1. 初期：正常浏览器访问（收集数据）
2. 中期：切换到自动化工具扫描
3. 系统检测到行为突变
4. 创建身份链，关联所有活动
5. 提高该"身份"的威胁评分
6. 未来该IP的任何活动都被重点监控

## 监控和告警

### 实时监控

Web管理后台提供实时监控：
- 访问统计
- 威胁趋势
- 封禁列表
- 最近事件

### 日志查看

系统日志：`firewall.log`
```bash
# 实时查看日志
tail -f firewall.log

# Windows
Get-Content firewall.log -Wait
```

### 邮件告警（可选）

配置 `config.yaml` 中的告警部分：
```yaml
alerts:
  enabled: true
  email:
    enabled: true
    smtp_host: "smtp.gmail.com"
    smtp_port: 587
    username: "your-email@gmail.com"
    password: "your-app-password"
    to_addrs:
      - "admin@yourdomain.com"
```

## 性能优化

### 使用Redis缓存

对于高流量网站，启用Redis：
```yaml
redis:
  enabled: true
  host: "localhost"
  port: 6379
```

### 数据库优化

1. **定期清理**：系统自动清理3天前的数据
2. **使用MySQL/PostgreSQL**：对于大规模部署
3. **索引优化**：数据库表已预先建立索引

### 日志轮转

配置nginx日志轮转：
```nginx
# /etc/logrotate.d/nginx
/var/log/nginx/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 www-data adm
    sharedscripts
    postrotate
        [ -f /var/run/nginx.pid ] && kill -USR1 `cat /var/run/nginx.pid`
    endscript
}
```

## 故障排查

### 系统不封禁IP

1. 检查防火墙是否启用：
```yaml
firewall:
  enabled: true
```

2. 检查是否在白名单：
```bash
python tools/cli_manager.py search <IP>
```

3. 查看日志：
```bash
grep "封禁" firewall.log
```

### 性能问题

1. 启用Redis
2. 使用更强大的数据库
3. 减少数据保留天数
4. 调整检测阈值

### 误封禁

1. 立即解封：
```bash
python tools/cli_manager.py unban <IP>
```

2. 添加到白名单：
```yaml
firewall:
  whitelist:
    - "<IP>"
```

3. 调整检测阈值

## 数据保留策略

系统采用**智能清理策略**：

- ✅ **持续访问的用户**：数据持续保留（无论多久）
- 🗑️ **停止访问的用户**：3天无访问后，第4天自动删除所有记录

### 工作原理

每个指纹记录都有 `last_seen`（最后访问时间）字段：
- 每次访问时，`last_seen` 更新为当前时间
- 系统每天检查：如果 `last_seen` 超过3天，删除该用户的所有数据
- 如果用户持续访问，`last_seen` 不断更新，数据永久保留

### 示例

**活跃用户**：
```
Day 1: 访问 → last_seen = Day 1
Day 2: 访问 → last_seen = Day 2
Day 100: 仍在访问 → 数据保留100天
```

**一次性访问者**：
```
Day 1: 访问 → last_seen = Day 1
Day 2-6: 无访问
Day 7: 自动清理 → 删除Day 1的所有记录
```

详细说明请查看：[docs/DATA_RETENTION.md](docs/DATA_RETENTION.md)

## 最佳实践

1. **初期测试**：先禁用实际封禁，观察威胁检测
```yaml
firewall:
  enabled: false
```

2. **逐步启用**：先启用高危威胁的封禁，观察效果

3. **定期审查**：查看封禁列表和威胁统计，调整规则

4. **备份数据库**：定期备份 `firewall.db`

5. **监控日志**：定期查看 `firewall.log`

6. **白名单管理**：及时添加可信IP到白名单

7. **阈值调整**：根据实际流量调整检测阈值

## 问题反馈

如有问题或建议，请创建Issue或联系管理员。

