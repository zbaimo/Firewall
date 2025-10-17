# 记录导出使用指南

## 概述

系统提供完整的记录导出功能，可以将封禁、威胁、评分、访问日志等记录导出到文件，方便查看、分析和归档。

## 支持的导出格式

- **JSON** - 结构化数据，适合程序处理
- **CSV** - 表格格式，可用Excel打开
- **TXT** - 文本格式，易于阅读

## 导出目录

默认导出到 `exports/` 目录，可在 `config.yaml` 中配置：

```yaml
export:
  directory: "exports"  # 导出目录
```

## 命令行导出

### 1. 导出封禁记录

```bash
# 导出所有封禁记录（JSON格式）
python tools/cli_manager.py export bans

# 导出为CSV格式
python tools/cli_manager.py export bans -f csv

# 只导出活跃的封禁
python tools/cli_manager.py export bans --active-only

# 导出最近7天的封禁
python tools/cli_manager.py export bans --days 7

# 指定输出文件
python tools/cli_manager.py export bans -o my_bans.json
```

**导出内容**：
- IP地址
- 封禁时间
- 解封时间
- 是否活跃
- 封禁原因
- 封禁次数
- 备注信息

### 2. 导出威胁事件

```bash
# 导出最近7天的威胁事件
python tools/cli_manager.py export threats

# 导出最近30天
python tools/cli_manager.py export threats --days 30

# 导出为TXT格式（易于阅读）
python tools/cli_manager.py export threats -f txt
```

**导出内容**：
- 时间戳
- IP地址
- 威胁类型
- 严重程度
- 描述信息
- 处理状态

### 3. 导出评分记录

```bash
# 导出威胁评分最高的100个用户
python tools/cli_manager.py export scores

# 导出为CSV（可用Excel分析）
python tools/cli_manager.py export scores -f csv
```

**导出内容**：
- IP地址
- 威胁评分
- 访问次数
- 首次访问时间
- 最后访问时间
- 所属身份链

### 4. 导出访问日志

```bash
# 导出最近24小时的访问日志
python tools/cli_manager.py export logs

# 导出最近3天
python tools/cli_manager.py export logs --days 3

# 导出为CSV格式
python tools/cli_manager.py export logs -f csv
```

**导出内容**：
- 时间戳
- IP地址
- 请求方法
- 请求路径
- 状态码
- 响应大小
- User-Agent

### 5. 导出完整报告

```bash
# 导出所有类型的记录（生成完整报告）
python tools/cli_manager.py export all

# 指定格式
python tools/cli_manager.py export all -f csv
```

**包含内容**：
- 封禁记录
- 威胁事件（30天）
- 评分记录（前500）
- 访问日志（24小时）
- 统计摘要

输出目录结构：
```
exports/full_report_20251017_183000/
├── ban_records.json
├── threat_events.json
├── score_records.json
├── access_logs.json
└── summary.txt
```

## 自动定时导出

### 启用自动导出

在 `config.yaml` 中配置：

```yaml
export:
  auto_export_enabled: true        # 启用自动导出
  auto_export_interval_hours: 24   # 每24小时导出一次
  auto_export_format: "json"       # 导出格式
  retention_days: 30               # 导出文件保留30天
```

### 自动导出行为

- 系统启动后自动执行一次导出
- 之后每隔配置的时间间隔自动导出
- 自动生成时间戳文件名
- 自动清理过期的导出文件

## 导出文件命名规则

### 自动命名

```
ban_records_active_20251017_183000.json
             ↑       ↑
          筛选条件  时间戳

threat_events_critical_20251017_183000.csv
              ↑
           严重程度

scores_min60_20251017_183000.txt
       ↑
     最低分数

access_logs_192_168_1_100_20251017_183000.json
            ↑
          特定IP
```

### 手动命名

```bash
# 使用 -o 参数指定文件名
python tools/cli_manager.py export bans -o /path/to/my_report.json
```

## 导出格式详解

### JSON格式

**优点**：
- 结构化数据
- 易于程序处理
- 支持嵌套数据

**示例**：
```json
[
  {
    "ip": "192.168.1.100",
    "banned_at": "2025-10-17 18:30:00",
    "ban_until": "2025-10-17 19:30:00",
    "reason": "频率限制超限",
    "ban_count": 1
  }
]
```

**适用场景**：
- 程序自动处理
- 数据分析
- API集成

### CSV格式

**优点**：
- 可用Excel/Numbers打开
- 易于制作图表
- 便于筛选排序

**示例**：
```csv
ip,banned_at,reason,ban_count
192.168.1.100,2025-10-17 18:30:00,频率限制超限,1
```

**适用场景**：
- 数据分析
- 制作报表
- 与第三方工具集成

### TXT格式

**优点**：
- 易于阅读
- 包含格式化
- 适合打印

**示例**：
```
================================================================================
封禁记录报告
生成时间: 2025-10-17 18:30:00
总记录数: 10
================================================================================

[1] IP: 192.168.1.100
    封禁时间: 2025-10-17 18:30:00
    解封时间: 2025-10-17 19:30:00
    状态: 活跃
    原因: 频率限制超限
    封禁次数: 1
--------------------------------------------------------------------------------
```

**适用场景**：
- 快速查看
- 打印输出
- 报告文档

## 使用场景

### 场景1：日常审计

```bash
# 每天导出活跃封禁记录
python tools/cli_manager.py export bans --active-only -f csv

# 查看并分析封禁趋势
```

### 场景2：安全事件调查

```bash
# 导出特定时间段的威胁事件
python tools/cli_manager.py export threats --days 7 -f txt

# 查看攻击模式和来源
```

### 场景3：性能分析

```bash
# 导出访问日志
python tools/cli_manager.py export logs --days 1 -f csv

# 用Excel分析访问模式
```

### 场景4：合规审计

```bash
# 导出完整报告（用于审计）
python tools/cli_manager.py export all -f json

# 归档到审计目录
mv exports/full_report_* /audit/2025/Q4/
```

### 场景5：威胁评分分析

```bash
# 导出高分用户
python tools/cli_manager.py export scores -f csv

# 分析哪些行为导致高分
```

## 高级用法

### Python脚本调用

```python
from models.database import Database
from core.export_manager import ExportManager
from utils.helpers import load_config

# 初始化
config = load_config('config.yaml')
db = Database(config)
export_mgr = ExportManager(db, config)

# 导出封禁记录
export_mgr.export_ban_records(
    output_file='custom_report.json',
    format='json',
    active_only=True,
    days=7
)

# 导出完整报告
export_mgr.export_all_records(format='csv')
```

### 定制导出内容

修改 `core/export_manager.py` 中的导出方法：

```python
def export_ban_records(self, ...):
    data = [{
        'ip': r.ip,
        'banned_at': r.banned_at,
        # 添加自定义字段
        'custom_field': calculate_custom_value(r)
    } for r in records]
```

### 集成到监控系统

```bash
#!/bin/bash
# 每小时导出威胁事件并发送告警

python tools/cli_manager.py export threats --days 1 -f json -o /tmp/threats.json

# 检查是否有新威胁
if [ $(jq length /tmp/threats.json) -gt 0 ]; then
    # 发送告警邮件
    mail -s "威胁告警" admin@example.com < /tmp/threats.json
fi
```

## 导出文件管理

### 查看导出文件

```bash
# 列出所有导出文件
ls -lh exports/

# 查看最新的导出
ls -lt exports/ | head
```

### 清理旧文件

```bash
# 手动清理30天前的导出文件
find exports/ -type f -mtime +30 -delete

# 或使用系统自动清理（配置retention_days）
```

### 备份导出文件

```bash
# 压缩导出目录
tar -czf exports_backup_$(date +%Y%m%d).tar.gz exports/

# 移动到备份位置
mv exports_backup_*.tar.gz /backup/firewall/
```

## 最佳实践

1. **定期导出**：配置自动导出，无需手动操作
2. **选择合适格式**：
   - 快速查看 → TXT
   - 数据分析 → CSV
   - 程序处理 → JSON
3. **合理设置保留期**：根据存储空间和审计需求
4. **导出前压缩**：大文件导出后压缩节省空间
5. **敏感数据保护**：导出文件包含IP等信息，注意权限控制

## 故障排查

### 导出失败

```bash
# 检查导出目录权限
ls -ld exports/

# 检查磁盘空间
df -h

# 查看错误日志
tail -f firewall.log
```

### 文件为空

```bash
# 检查数据库是否有记录
python tools/cli_manager.py stats

# 检查查询条件是否过于严格
python tools/cli_manager.py export bans --days 365
```

### 格式错误

```bash
# 检查文件编码
file exports/ban_records.json

# 验证JSON格式
python -m json.tool exports/ban_records.json
```

## 常见问题

**Q: 导出文件太大怎么办？**
A: 使用 `--days` 参数限制时间范围，或导出后压缩文件

**Q: 可以导出为Excel格式吗？**
A: 导出为CSV格式后，可以直接用Excel打开

**Q: 如何导出特定IP的所有记录？**
A: 暂不支持，建议导出JSON后用jq过滤：
```bash
jq '.[] | select(.ip=="192.168.1.100")' exports/threats.json
```

**Q: 导出会影响系统性能吗？**
A: 大数据量导出会占用数据库资源，建议在低峰期进行

**Q: 可以导出到远程服务器吗？**
A: 先导出到本地，再使用scp/rsync上传：
```bash
python tools/cli_manager.py export all
scp -r exports/full_report_* user@remote:/path/
```

## 总结

导出功能为系统提供了完整的数据可视化和审计支持：

- ✅ 多种格式支持（JSON、CSV、TXT）
- ✅ 灵活的筛选条件
- ✅ 自动定时导出
- ✅ 完整报告生成
- ✅ 命令行和程序API

合理使用导出功能，可以大大提升安全运维效率！

