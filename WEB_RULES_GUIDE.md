# 📋 Web界面规则管理完全指南

## 概述

**所有规则现在完全通过Web界面管理，不再需要编辑config.yaml！**

---

## 🌐 访问地址

```
规则管理: http://your-server:8080/rules
端口管理: http://your-server:8080/ports
防火墙管理: http://your-server:8080/firewall
```

---

## 🎯 规则管理页面

### 威胁检测规则

**访问**: http://your-server:8080/rules → 威胁检测规则

**功能**：
- 查看所有威胁检测规则
- 添加新的检测规则
- 编辑现有规则
- 启用/禁用规则
- 删除规则

#### 默认规则（系统自动创建）

系统首次启动时会自动创建以下规则：

1. **SQL注入检测**
   - 分类: sql_injection
   - 分数: 50
   - 模式: `union.*select`, `'; --`, `' or '1'='1`

2. **XSS攻击检测**
   - 分类: xss_attack
   - 分数: 40
   - 模式: `<script`, `javascript:`, `onerror=`

3. **频率限制**
   - 分类: rate_limit
   - 分数: 25
   - 参数: 60秒内最多100次请求

4. **路径扫描检测**
   - 分类: scan_detection
   - 分数: 30
   - 参数: 5分钟内最多20个404

5. **敏感路径访问**
   - 分类: sensitive_path
   - 分数: 15
   - 模式: `/.env`, `/.git`, `/admin`

6. **恶意User-Agent**
   - 分类: bad_user_agent
   - 分数: 20
   - 模式: `masscan`, `nmap`, `nikto`, `sqlmap`

#### 添加新规则

点击 "+ 添加规则"，填写：

```
规则分类: [选择类型]
规则名称: 例如：高级SQL注入检测
描述: 检测更多SQL注入模式
检测模式: ["union all select", "information_schema"]
威胁分数: 60
启用: ✓
```

---

### 自定义规则

**访问**: http://your-server:8080/rules → 自定义规则

**功能**：
- 创建自定义评分规则
- 支持时间、行为、地理位置等规则类型
- 设置评分和动作

#### 默认规则

1. **深夜管理员访问**
   - 类型: time
   - 条件: `{"time_range": "02:00-05:00", "path_contains": "/admin"}`
   - 评分: 30
   - 动作: score

#### 规则类型

- **pattern**: 模式匹配
- **rate**: 频率限制
- **behavior**: 行为分析
- **time**: 时间规则
- **geo**: 地理位置

#### 添加示例

**时间规则**：
```json
{
  "name": "工作时间外访问",
  "rule_type": "time",
  "conditions": {
    "time_range": "18:00-08:00",
    "path_contains": "/api"
  },
  "score": 15,
  "action": "score"
}
```

**行为规则**：
```json
{
  "name": "工具切换检测",
  "rule_type": "behavior",
  "conditions": {
    "user_agent_changes": 5,
    "time_window": 300
  },
  "score": 35,
  "action": "score"
}
```

---

## 🔌 端口管理页面

**访问**: http://your-server:8080/ports

### 功能

1. **常用端口**
   - 22个预定义常用端口
   - 一键开放/关闭/阻止
   - 实时状态显示

2. **自定义规则**
   - 添加自定义端口规则
   - 指定来源IP（可选）
   - 支持TCP/UDP/Both

3. **端口扫描检测**
   - 查看端口扫描行为
   - 自动封禁扫描者

4. **操作日志**
   - 所有端口操作记录
   - 审计追踪

### 常用端口列表

```
Web: 80 (HTTP), 443 (HTTPS), 8080, 8443
SSH: 22
FTP: 20, 21
Email: 25 (SMTP), 110 (POP3), 143 (IMAP), 465, 587, 993, 995
Database: 3306 (MySQL), 5432 (PostgreSQL), 6379 (Redis), 27017 (MongoDB)
Remote: 3389 (RDP), 23 (Telnet)
DNS: 53
Other: 9000 (PHP-FPM)
```

### 添加自定义端口

点击 "+ 添加规则"，填写：

```
端口号: 8888
协议: TCP
动作: 允许（开放）
描述: 自定义Web服务
来源IP: 留空（所有IP）或指定IP
```

---

## 🔥 防火墙管理页面

**访问**: http://your-server:8080/firewall

### 功能

1. **IP封禁管理**
   - 查看所有封禁的IP
   - 手动封禁/解封
   - 批量解封
   - 查看封禁统计

2. **iptables链查看**
   - FIREWALL_BANS - IP封禁链
   - FIREWALL_RATE_LIMIT - 频率限制链
   - FIREWALL_PORT_RULES - 端口规则链
   - 实时查看规则

3. **白名单管理**
   - 添加信任的IP
   - 永不封禁

4. **黑名单管理**
   - 添加恶意IP
   - 立即封禁

### 手动封禁IP

点击 "+ 手动封禁"，填写：

```
IP地址: 1.2.3.4
封禁原因: 恶意攻击
封禁时长: 3600 (1小时) 或 0 (永久)
```

### 批量解封

1. 勾选要解封的IP
2. 点击"批量解封"
3. 确认操作

---

## 🔄 规则管理工作流

### 新系统部署

**步骤1**: 部署系统
```bash
docker-compose -f docker-compose.deploy.yml up -d
```

**步骤2**: 访问Web界面
```
http://your-server:8080
```

**步骤3**: 登录系统
```
用户名: admin
密码: admin (首次登录强制修改)
```

**步骤4**: 检查默认规则
```
访问: /rules
查看: 系统已自动创建6条威胁检测规则和1条自定义规则
```

**步骤5**: 根据需要调整
- 启用/禁用规则
- 修改分数
- 添加新规则

### 日常管理

**查看规则**:
```
http://your-server:8080/rules
```

**添加规则**:
1. 点击 "+ 添加规则" 或 "+ 添加自定义规则"
2. 填写表单
3. 保存（立即生效）

**修改规则**:
1. 点击规则的"编辑"按钮
2. 修改配置
3. 保存（立即生效）

**启用/禁用**:
- 点击"启用"或"禁用"按钮
- 立即生效，无需重启

---

## 🎨 规则示例库

### SQL注入检测规则

```json
{
  "category": "sql_injection",
  "name": "高级SQL注入",
  "patterns": [
    "union all select",
    "information_schema",
    "concat.*char",
    "group_concat",
    "load_file",
    "into outfile"
  ],
  "threat_score": 60,
  "enabled": true
}
```

### XSS攻击检测

```json
{
  "category": "xss_attack",
  "name": "高级XSS检测",
  "patterns": [
    "document.write",
    "window.location",
    "innerHTML",
    "outerHTML",
    "insertAdjacentHTML"
  ],
  "threat_score": 45,
  "enabled": true
}
```

### 暴力破解检测

```json
{
  "category": "rate_limit",
  "name": "登录暴力破解",
  "parameters": {
    "path_contains": "/login",
    "window_seconds": 300,
    "max_requests": 10
  },
  "threat_score": 40,
  "enabled": true
}
```

### 爬虫检测

```json
{
  "name": "爬虫检测",
  "rule_type": "pattern",
  "conditions": {
    "user_agent_contains": "bot",
    "request_rate": 50
  },
  "score": 10,
  "action": "monitor"
}
```

---

## 🛠️ CLI工具（备用方式）

如果Web界面暂时无法访问，也可以使用CLI工具：

```bash
# 进入容器
docker exec -it nginx-firewall bash

# 使用初始化脚本
python tools/init_default_rules.py

# 或使用CLI工具
python tools/firewall_cli.py interactive
```

---

## 📊 规则生效机制

### 实时生效

```
Web界面添加/修改规则
         ↓
     保存到数据库
         ↓
    立即生效（无需重启）
         ↓
   下一个日志条目立即使用新规则
```

### 规则优先级

1. 白名单检查（最高优先级）
2. 黑名单检查
3. 威胁检测规则（按category）
4. 自定义规则（按priority排序）
5. 评分系统判断

---

## 🔍 故障排查

### 规则不生效？

1. **检查规则是否启用**
   - 访问 /rules
   - 确认规则状态为"已启用"

2. **检查规则语法**
   - JSON格式是否正确
   - 正则表达式是否有效

3. **查看日志**
   ```bash
   docker logs nginx-firewall | grep -i "rule"
   ```

4. **重启服务**（如果需要）
   ```bash
   docker-compose -f docker-compose.deploy.yml restart firewall
   ```

---

## 📖 最佳实践

### 1. 先测试后启用

- 新规则先设为"禁用"
- 观察日志，确认匹配正确
- 再启用规则

### 2. 合理设置分数

- 严重威胁: 50-100分
- 中等威胁: 20-50分
- 轻微异常: 10-20分

### 3. 定期审查

- 每周检查规则效果
- 调整分数和阈值
- 删除无效规则

### 4. 备份规则

定期导出规则配置：
```bash
docker exec nginx-firewall python tools/cli_manager.py export --type rules
```

---

## 🎉 优势总结

### 使用Web界面管理规则的优势

✅ **无需重启** - 规则立即生效  
✅ **可视化** - 直观的界面操作  
✅ **版本控制** - 自动记录创建/更新时间  
✅ **审计日志** - 记录所有规则变更  
✅ **团队协作** - 多人可以管理  
✅ **容易维护** - 不用编辑复杂的YAML  
✅ **错误防护** - 表单验证防止配置错误  
✅ **灵活性** - 随时添加/修改/删除  

### vs 配置文件方式

| 特性 | config.yaml | Web界面 |
|------|-------------|---------|
| 添加规则 | 编辑文件+重启 | 点击按钮 |
| 生效时间 | 需重启 | 立即 |
| 易用性 | 需要YAML知识 | 直观 |
| 错误检查 | 手动 | 自动 |
| 审计日志 | ❌ | ✅ |
| 团队协作 | 困难 | 容易 |
| 版本控制 | 需要Git | 自动 |

---

## 🚀 快速开始

### 3分钟配置防火墙规则

1. **访问规则页面** (30秒)
   ```
   http://your-server:8080/rules
   ```

2. **查看默认规则** (30秒)
   - 系统已自动创建6条威胁检测规则
   - 根据需要启用/禁用

3. **添加自定义规则** (2分钟)
   - 点击"+ 添加自定义规则"
   - 填写规则信息
   - 保存（立即生效）

**完成！** ✅

---

## 📝 规则配置示例

### 示例1：防止目录遍历

```json
{
  "category": "sensitive_path",
  "name": "目录遍历检测",
  "patterns": [
    "../",
    "..\\",
    "..\\/",
    "%2e%2e"
  ],
  "threat_score": 35,
  "enabled": true
}
```

### 示例2：API频率限制

```json
{
  "name": "API频率限制",
  "rule_type": "rate",
  "conditions": {
    "path_prefix": "/api",
    "max_requests": 60,
    "window_seconds": 60
  },
  "score": 20,
  "action": "score"
}
```

### 示例3：特定国家封禁

```json
{
  "name": "封禁特定国家",
  "rule_type": "geo",
  "conditions": {
    "countries": ["KP", "IR"],
    "action": "ban"
  },
  "score": 100,
  "action": "ban"
}
```

---

## 💡 高级技巧

### 1. 组合规则

创建多个规则配合使用：
- 基础检测规则（低分）
- 组合条件规则（高分）
- 达到阈值触发封禁

### 2. 动态调整

根据实际情况调整：
- 监控威胁统计
- 查看误报情况
- 调整分数和阈值

### 3. 规则测试

使用测试工具验证规则：
```bash
python tools/test_log_generator.py --attack sql_injection
# 查看是否正确检测
```

---

## 🔗 相关文档

- `RULES_MANAGEMENT_FEATURE.md` - 规则管理技术文档
- `IPTABLES_FIREWALL_GUIDE.md` - iptables开发指南
- `CONFIG_CHANGES.md` - 配置文件变更说明

---

**🎊 现在您可以完全通过Web界面管理所有规则了！** ✨

**不再需要编辑config.yaml！** 🎉

