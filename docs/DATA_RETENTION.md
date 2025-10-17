# 智能数据保留策略

## 概述

系统采用**智能清理策略**，而不是简单的"删除X天前的所有数据"。

## 核心原则

### ✅ 持续活跃 = 持续保存

如果用户/指纹持续有访问活动，**无论多久都会保留数据**。

```
示例：某个用户每天都访问
Day 1: 访问 → last_seen = Day 1
Day 2: 访问 → last_seen = Day 2  
Day 3: 访问 → last_seen = Day 3
Day 4: 访问 → last_seen = Day 4
...
Day 100: 仍在访问 → 数据依然保留
```

### ⏰ 连续无访问 = 自动清理

如果用户/指纹超过配置的天数（默认3天）没有新访问，第4天自动清理该用户的**所有历史数据**。

```
示例：某个用户停止访问
Day 1: 访问 → last_seen = Day 1
Day 2: 访问 → last_seen = Day 2
Day 3: 访问 → last_seen = Day 3
Day 4: 无访问
Day 5: 无访问
Day 6: 无访问
Day 7: 清理触发 → 删除该用户的所有数据（Day 1-3的所有记录）
```

## 技术实现

### 1. 关键字段：last_seen

每个指纹记录都有 `last_seen` 字段：

```python
class Fingerprint:
    base_hash = ...
    first_seen = ...      # 首次访问时间
    last_seen = ...       # 最后访问时间（持续更新）
    visit_count = ...
```

**每次访问时**：
```python
# 更新last_seen为当前时间
fingerprint.last_seen = datetime.now()
```

### 2. 清理逻辑

系统每天运行清理任务（默认凌晨3点）：

```python
def cleanup_old_data(retention_days=3):
    cutoff_date = now() - timedelta(days=3)
    
    # 1. 找出所有过期的指纹
    expired_fingerprints = 查询(last_seen < cutoff_date)
    
    # 2. 删除这些指纹的所有相关数据
    for fp in expired_fingerprints:
        删除(fp的所有访问日志)
        删除(fp的所有威胁事件)
        删除(fp本身)
    
    # 3. 清理空的身份链
    删除(没有活跃指纹的身份链)
```

### 3. 级联删除

当删除一个指纹时，会级联删除：

- ✓ 该指纹的所有访问日志（access_logs）
- ✓ 该指纹的所有威胁事件（threat_events）
- ✓ 指纹记录本身（fingerprints）
- ✓ 如果指纹所属的身份链没有其他活跃指纹，也会删除身份链

**不会删除**：
- ✗ 封禁记录（ban_records）- 保留作为审计日志
- ✗ 统计数据（statistics）- 保留作为历史统计

## 配置

在 `config.yaml` 中配置保留天数：

```yaml
fingerprint:
  retention_days: 3  # 默认3天
```

**建议值**：
- 小型网站：3天
- 中型网站：7天
- 大型网站：3天（配合Redis缓存）
- 安全审计需求：30天或更长

## 使用场景

### 场景1：正常用户

```
用户A：每天都访问
├─ Day 1-30: 持续访问
├─ last_seen: 持续更新
└─ 结果: 数据保留30天（甚至更长）
```

### 场景2：一次性访问者

```
用户B：只访问1次
├─ Day 1: 访问
├─ Day 2-3: 无访问
├─ Day 4: 清理触发
└─ 结果: Day 1的数据被删除
```

### 场景3：周期性访问

```
用户C：每周访问一次
├─ Day 1: 访问 (last_seen = Day 1)
├─ Day 8: 访问 (last_seen = Day 8) ← 超过7天，但仍保留
├─ Day 15: 访问 (last_seen = Day 15)
└─ 结果: 数据持续保留
```

### 场景4：攻击者

```
攻击者：尝试攻击后停止
├─ Day 1: 大量攻击请求
├─ Day 2: 被封禁后停止
├─ Day 3-4: 无访问
├─ Day 5: 清理触发
├─ 结果: 攻击日志被删除
└─ 但是: 封禁记录保留（作为审计）
```

## 手动控制

### 查看某个IP的保留状态

```bash
python tools/cli_manager.py search 192.168.1.100
```

输出包括：
- first_seen: 首次访问时间
- last_seen: 最后访问时间
- 距离过期还有多少天

### 手动清理数据

```python
# 在Python中
from models.database import Database
from utils.helpers import load_config

config = load_config()
db = Database(config)

# 立即执行清理
deleted_logs, deleted_fps, deleted_chains = db.cleanup_old_data(3)
print(f"删除: {deleted_logs}条日志, {deleted_fps}个指纹, {deleted_chains}个身份链")
```

### 调整单个指纹的保留期

如果想永久保留某个指纹的数据，可以手动更新 `last_seen`：

```python
session = db.get_session()
fp = session.query(Fingerprint).filter_by(base_hash='xxx').first()
if fp:
    fp.last_seen = datetime.now()  # 刷新保留期
    session.commit()
```

## 数据库空间管理

### 预估空间占用

```
单条访问日志: ~500 bytes
每天10万请求: 50 MB/天
保留3天: ~150 MB
保留30天: ~1.5 GB
```

### 查看当前数据量

```bash
python tools/cli_manager.py stats
```

### SQLite数据库优化

定期执行VACUUM来释放空间：

```python
from sqlalchemy import text

session = db.get_session()
session.execute(text("VACUUM"))
session.close()
```

## 与传统方案对比

| 特性 | 传统固定保留 | 智能保留策略 |
|-----|------------|------------|
| 活跃用户数据 | 3天后删除 | ✓ 持续保留 |
| 一次性访问者 | 占用空间 | ✓ 自动清理 |
| 攻击者数据 | 保留3天 | ✓ 停止攻击后清理 |
| 数据库大小 | 固定增长 | ✓ 动态平衡 |
| 长期用户追踪 | ✗ 数据丢失 | ✓ 完整历史 |

## 最佳实践

1. **初期设置较短保留期**（3天），观察效果
2. **监控数据库大小**，根据需要调整
3. **定期查看统计**，了解数据清理情况
4. **重要用户加入白名单**，防止误清理
5. **封禁记录单独管理**，不受清理影响

## 注意事项

### ⚠️ 清理是不可逆的

数据删除后无法恢复，建议：
- 定期备份数据库
- 先在测试环境验证
- 重要数据导出归档

### ⚠️ 身份链的特殊处理

如果身份链中的所有指纹都过期，整个身份链会被删除。如果想保留某个身份链：

```python
# 保持身份链活跃的方法
# 方法1：确保至少一个指纹持续有访问
# 方法2：手动刷新所有指纹的last_seen
```

### ⚠️ 封禁记录不受影响

封禁记录（BanRecord）独立管理，不会因为数据清理而删除。这是为了保留安全审计日志。

如需清理封禁记录，请手动操作：

```bash
python tools/cli_manager.py unban <IP>
```

## 总结

智能数据保留策略的优势：

1. **自动化管理**：无需手动清理过期数据
2. **空间优化**：自动删除不活跃用户数据
3. **历史保留**：活跃用户数据持久保存
4. **灵活配置**：根据需求调整保留期
5. **安全审计**：封禁记录独立保留

这种策略特别适合：
- 访问量大但活跃用户相对集中的网站
- 需要长期追踪特定用户行为的场景
- 存储空间有限但需要完整历史的情况

