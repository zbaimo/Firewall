# 🎯 规则管理功能 - Web界面

## 概述

将原本在`config.yaml`中的规则配置移到Web管理界面，实现动态配置和实时生效。

## 新增功能

### 1. 规则管理页面
- **访问路径**: `/rules`
- **功能**: 可视化管理所有安全规则

### 2. 三种规则类型

#### A. 威胁检测规则
- SQL注入检测
- XSS攻击检测
- 频率限制
- 扫描检测
- 敏感路径访问
- 恶意User-Agent

#### B. 自定义规则
- 模式匹配规则
- 频率限制规则
- 行为分析规则
- 时间规则

#### C. 评分配置
- 不同威胁类型的基础分数
- 封禁阈值配置

## 数据库表结构

### ThreatDetectionRule (威胁检测规则)
```sql
CREATE TABLE threat_detection_rules (
    id INTEGER PRIMARY KEY,
    category VARCHAR(50),  -- 规则分类
    name VARCHAR(100),     -- 规则名称
    description TEXT,      -- 描述
    enabled BOOLEAN,       -- 是否启用
    patterns TEXT,         -- 检测模式(JSON)
    parameters TEXT,       -- 规则参数(JSON)
    threat_score INTEGER,  -- 威胁分数
    created_at DATETIME,
    updated_at DATETIME
);
```

### ScoringRule (自定义规则)
```sql
CREATE TABLE scoring_rules (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100) UNIQUE,
    description TEXT,
    enabled BOOLEAN,
    rule_type VARCHAR(50),  -- pattern, rate, behavior, time
    conditions TEXT,         -- 匹配条件(JSON)
    score INTEGER,          -- 评分
    action VARCHAR(20),     -- 动作: score, ban, monitor
    priority INTEGER,       -- 优先级
    created_at DATETIME,
    updated_at DATETIME
);
```

## API端点

### 威胁检测规则
- `GET /api/rules/threat` - 获取所有威胁检测规则
- `GET /api/rules/threat/<id>` - 获取单个规则
- `POST /api/rules/threat` - 创建规则
- `PUT /api/rules/threat/<id>` - 更新规则
- `DELETE /api/rules/threat/<id>` - 删除规则
- `POST /api/rules/threat/<id>/toggle` - 切换启用/禁用

### 自定义规则
- `GET /api/rules/custom` - 获取所有自定义规则
- `GET /api/rules/custom/<id>` - 获取单个规则
- `POST /api/rules/custom` - 创建规则
- `PUT /api/rules/custom/<id>` - 更新规则
- `DELETE /api/rules/custom/<id>` - 删除规则
- `POST /api/rules/custom/<id>/toggle` - 切换启用/禁用

## 使用方法

### 1. 访问规则管理

```
http://your-server:8800/rules
```

或从仪表板点击"📋 规则管理"

### 2. 添加威胁检测规则

示例：添加SQL注入检测规则

```json
{
  "category": "sql_injection",
  "name": "高级SQL注入检测",
  "description": "检测常见SQL注入模式",
  "enabled": true,
  "patterns": "[\"union.*select\", \"select.*from\", \"'; drop\"]",
  "threat_score": 50
}
```

### 3. 添加自定义规则

示例：深夜异常访问检测

```json
{
  "name": "深夜异常访问",
  "description": "检测凌晨2-5点的/admin访问",
  "enabled": true,
  "rule_type": "time",
  "conditions": "{\"time_range\": \"02:00-05:00\", \"path_contains\": \"/admin\"}",
  "score": 30,
  "action": "score",
  "priority": 100
}
```

## config.yaml 简化

原本的规则配置可以从config.yaml中移除，改为通过Web界面管理：

### 之前（config.yaml）:
```yaml
threat_detection:
  sql_injection:
    enabled: true
    patterns:
      - "union.*select"
      - "select.*from"
      
custom_rules:
  - name: "深夜异常访问"
    enabled: true
    # ... 更多配置
```

### 现在（Web界面）:
- 所有规则配置存储在数据库
- 通过Web界面添加/编辑/删除
- 实时生效，无需重启

## 优势

✅ **动态配置**: 无需重启服务
✅ **可视化管理**: 直观的Web界面
✅ **版本控制**: 自动记录创建和更新时间
✅ **审计日志**: 记录所有规则变更
✅ **权限控制**: 需要登录才能访问
✅ **分类管理**: 威胁检测和自定义规则分开
✅ **优先级控制**: 可设置规则优先级
✅ **批量操作**: 快速启用/禁用规则

## 配置项保留

config.yaml中保留基础配置：

```yaml
# 保留这些基础配置
scoring_system:
  enabled: true
  score_decay_hours: 24
  score_decay_rate: 0.5
  ban_thresholds:
    temporary_ban: 60
    extended_ban: 100
    permanent_ban: 150

# 移除详细的规则配置
# custom_rules: []  # 不再需要
# threat_detection:  # 详细规则移到Web界面
```

## 迁移说明

如果您之前在config.yaml中配置了规则：

1. **启动系统后首次访问规则管理页面**
2. **手动添加之前的规则** (或使用迁移脚本)
3. **从config.yaml中删除规则配置**
4. **重启服务**

## 规则示例

### SQL注入检测
```
分类: sql_injection
名称: SQL注入检测
模式: ["union.*select", "'; drop", "' or '1'='1"]
分数: 50
```

### 扫描检测
```
分类: scan_detection
名称: 404扫描检测
参数: {"window_seconds": 300, "max_404_count": 20}
分数: 30
```

### 时间规则
```
类型: time
名称: 深夜管理员访问
条件: {"time_range": "02:00-05:00", "path_contains": "/admin"}
分数: 30
动作: score
```

## 注意事项

⚠️ **规则立即生效**: 添加或修改规则后立即生效，无需重启

⚠️ **性能影响**: 过多的复杂规则可能影响性能，建议控制在50条以内

⚠️ **备份**: 定期备份数据库以防止规则丢失

⚠️ **测试**: 新规则建议先在测试环境验证

## 后续优化

- [ ] 规则导入/导出功能
- [ ] 规则模板库
- [ ] 规则测试工具
- [ ] 规则生效统计
- [ ] 规则推荐系统

---

**现在就可以通过Web界面管理所有规则了！** 🎉

访问: http://your-server:8800/rules

