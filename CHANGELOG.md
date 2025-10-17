# 更新日志

## 2025-10-17 - 威胁评分系统与记录导出功能

### 新增功能

#### 🎯 威胁评分系统
- ✅ **自动威胁评分**（0-200分）
  - 每个用户独立评分
  - 基于威胁类型和严重程度
  - 支持行为模式识别
  - 良好行为可降低分数（奖励机制）

- ✅ **策略性封禁**
  - 60分：临时封禁（1小时）
  - 100分：延长封禁（24小时）
  - 150分：永久封禁
  - 阈值和时长完全可自定义

- ✅ **分数衰减机制**
  - 分数随时间自然降低
  - 默认24小时衰减50%
  - 减少误判风险

- ✅ **完全可配置**
  - 用户可在 `config.yaml` 中自定义所有评分规则
  - 支持自定义威胁类型分数
  - 支持自定义严重程度乘数
  - 支持自定义行为模式分数
  - 支持自定义封禁阈值和时长

#### 📤 记录导出功能
- ✅ **多类型导出**
  - 封禁记录导出
  - 威胁事件导出
  - 评分记录导出
  - 访问日志导出
  - 完整报告导出

- ✅ **多格式支持**
  - JSON格式（程序处理）
  - CSV格式（Excel分析）
  - TXT格式（易于阅读）

- ✅ **灵活筛选**
  - 按时间范围筛选
  - 按状态筛选（活跃/全部）
  - 按严重程度筛选
  - 自定义输出路径

- ✅ **自动导出**
  - 支持定时自动导出
  - 自动生成时间戳文件名
  - 自动清理过期文件
  - 完整报告一键生成

### 技术实现

**新增文件**：
1. `core/scoring_system.py` - 威胁评分系统
2. `core/export_manager.py` - 记录导出管理器
3. `models/database.py` - 新增数据表：
   - `ScoreHistory` - 评分历史表
   - `ScoringRule` - 自定义评分规则表
4. `docs/EXPORT_GUIDE.md` - 导出功能使用指南

**更新文件**：
1. `config.yaml` - 新增评分和导出配置
2. `tools/cli_manager.py` - 新增导出命令
3. `models/database.py` - Fingerprint表新增评分字段

### 配置示例

在 `config.yaml` 中配置：

```yaml
# 威胁评分系统
scoring_system:
  enabled: true
  
  # 分数衰减
  score_decay_hours: 24
  score_decay_rate: 0.5
  
  # 封禁阈值（完全自定义）
  ban_thresholds:
    temporary_ban: 60
    extended_ban: 100
    permanent_ban: 150
  
  # 威胁类型分数（完全自定义）
  threat_scores:
    sql_injection: 50
    xss_attack: 40
    path_scan: 30
  
  # 分数奖励（负分）
  score_rewards:
    normal_access: -1
    successful_login: -5

# 导出配置
export:
  directory: "exports"
  auto_export_enabled: false
  auto_export_interval_hours: 24
```

### 使用示例

```bash
# 导出封禁记录
python tools/cli_manager.py export bans -f csv

# 导出威胁事件
python tools/cli_manager.py export threats --days 7 -f txt

# 导出评分记录
python tools/cli_manager.py export scores -f json

# 导出完整报告
python tools/cli_manager.py export all
```

### 文档

- [导出功能使用指南](docs/EXPORT_GUIDE.md) ⭐新增

---

## 2025-10-17 - 智能数据保留策略

### 新增功能

#### 智能清理策略
- ✅ **持续访问的用户数据永久保留**
  - 只要用户持续访问，数据就会一直保存（无论多长时间）
  - 每次访问时，系统会更新该用户的 `last_seen` 时间戳

- 🗑️ **停止访问的用户数据自动清理**
  - 如果用户连续3天（可配置）没有新访问
  - 第4天系统会自动删除该用户的所有历史记录
  - 包括：访问日志、指纹记录、威胁事件

### 技术实现

**修改的文件**：
1. `models/database.py`
   - 重写 `cleanup_old_data()` 方法
   - 基于 `last_seen` 字段判断是否过期
   - 级联删除过期指纹的所有相关数据
   - 自动清理空的身份链

2. `config.yaml`
   - 添加智能清理策略说明
   - 配置项：`fingerprint.retention_days`

3. `README.md`
   - 更新系统特点描述

4. `USAGE.md`
   - 添加数据保留策略使用说明

5. `docs/DATA_RETENTION.md` (新文件)
   - 详细的智能数据保留策略文档
   - 使用场景、配置说明、最佳实践

### 工作原理

```
每次访问 → 更新 last_seen
              ↓
        定时检查（每天凌晨3点）
              ↓
    last_seen < (今天 - 3天) ?
       ↓              ↓
      是            否
       ↓              ↓
   删除数据      保留数据
```

### 使用示例

**场景1：活跃用户**
```
用户A每天都访问
→ Day 1-100 持续有数据
→ 数据保留100天（或更长）
```

**场景2：一次性访问者**
```
用户B只访问1次
→ Day 1 访问
→ Day 2-6 无访问
→ Day 7 自动清理
```

### 配置

在 `config.yaml` 中调整保留天数：

```yaml
fingerprint:
  retention_days: 3  # 3天无访问后清理
```

### 优势

1. **自动化**：无需手动管理数据生命周期
2. **空间优化**：自动清理不活跃用户，节省存储
3. **历史完整**：活跃用户的数据完整保留
4. **灵活配置**：可根据需求调整保留期
5. **精准清理**：基于用户级别，不是简单的时间切分

### 注意事项

- ⚠️ 封禁记录（BanRecord）不受清理影响，作为审计日志保留
- ⚠️ 数据清理不可逆，建议定期备份数据库
- ⚠️ 身份链中所有指纹都过期时，身份链也会被删除

### 文档

详细说明请查看：
- [docs/DATA_RETENTION.md](docs/DATA_RETENTION.md) - 数据保留策略详解
- [USAGE.md](USAGE.md) - 使用指南（数据保留部分）

---

## 初始版本 - 核心功能

### 实现的功能

1. **指纹系统**
   - 基础指纹（IP + User-Agent）
   - 行为指纹（请求特征）
   - 身份链（关联演变的指纹）

2. **威胁检测**
   - SQL注入检测
   - XSS攻击检测
   - 路径扫描检测
   - 频率限制检测
   - 恶意工具识别

3. **自动防火墙**
   - Windows (netsh)
   - Linux (iptables/firewalld)
   - 自动封禁/解封
   - 白名单保护

4. **Web管理后台**
   - 实时统计面板
   - 威胁事件列表
   - 封禁管理
   - IP搜索

5. **命令行工具**
   - 封禁/解封管理
   - 统计查看
   - IP信息搜索
   - 身份链查看

