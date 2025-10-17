# 快速开始指南

## 5分钟快速部署

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置系统

编辑 `config.yaml`：

```yaml
nginx:
  access_log: "/var/log/nginx/access.log"  # 修改为你的nginx日志路径
```

### 3. 启动系统

```bash
# Windows
run.bat

# Linux/macOS
./run.sh
```

### 4. 访问管理后台

打开浏览器访问：http://localhost:8080

## 常用命令

### 查看统计

```bash
python tools/cli_manager.py stats
```

### 查看封禁列表

```bash
python tools/cli_manager.py list-bans
```

### 搜索IP信息

```bash
python tools/cli_manager.py search 192.168.1.100
```

### 手动封禁IP

```bash
python tools/cli_manager.py ban 192.168.1.100 -r "测试封禁" -d 3600
```

### 解封IP

```bash
python tools/cli_manager.py unban 192.168.1.100
```

### 导出记录

```bash
# 导出封禁记录
python tools/cli_manager.py export bans -f csv

# 导出威胁事件
python tools/cli_manager.py export threats -f txt

# 导出完整报告
python tools/cli_manager.py export all
```

## 配置调优

### 调整评分阈值

编辑 `config.yaml`：

```yaml
scoring_system:
  ban_thresholds:
    temporary_ban: 60      # 临时封禁分数（调低=更严格）
    extended_ban: 100      # 延长封禁分数
    permanent_ban: 150     # 永久封禁分数
```

### 调整威胁分数

```yaml
scoring_system:
  threat_scores:
    sql_injection: 50      # SQL注入分数（调高=更严厉）
    xss_attack: 40         # XSS攻击分数
    path_scan: 30          # 路径扫描分数
```

### 调整数据保留期

```yaml
fingerprint:
  retention_days: 3        # 无访问3天后清理（调大=保留更久）
```

### 启用自动导出

```yaml
export:
  auto_export_enabled: true        # 启用自动导出
  auto_export_interval_hours: 24   # 每24小时导出
```

## 测试系统

### 生成测试日志

```bash
# 生成1000条测试日志
python tools/test_log_generator.py -n 1000

# 处理测试日志
python main.py --batch test_access.log
```

### 查看结果

```bash
# 查看威胁事件
python tools/cli_manager.py threats

# 查看评分记录
python tools/cli_manager.py export scores -f txt
```

## 下一步

- 📖 阅读 [完整使用指南](USAGE.md)
- 📖 了解 [核心概念](CONCEPT.md)
- 📖 查看 [导出功能](docs/EXPORT_GUIDE.md)
- ⚙️ 根据实际需求调整 `config.yaml`
- 🔍 监控系统日志 `firewall.log`

## 常见问题

### Q: 日志文件权限错误？
A: 确保有读取nginx日志的权限
```bash
sudo chmod +r /var/log/nginx/access.log
```

### Q: 防火墙规则不生效？
A: 需要管理员权限运行
```bash
sudo python main.py  # Linux
# 或以管理员身份运行 PowerShell  # Windows
```

### Q: 数据库被锁定？
A: 确保只有一个进程在运行
```bash
ps aux | grep main.py
```

### Q: 想要更严格的防护？
A: 降低封禁阈值和提高威胁分数
```yaml
scoring_system:
  ban_thresholds:
    temporary_ban: 40     # 从60降到40
  threat_scores:
    sql_injection: 70     # 从50提到70
```

### Q: 想要更宽松的防护？
A: 提高封禁阈值和降低威胁分数
```yaml
scoring_system:
  ban_thresholds:
    temporary_ban: 80     # 从60提到80
  threat_scores:
    sql_injection: 30     # 从50降到30
```

## 获取帮助

- 查看文档：`docs/` 目录
- 查看示例：`tools/` 目录
- 检查日志：`firewall.log`
- GitHub Issues: 提交问题反馈

