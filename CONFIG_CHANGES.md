# 📝 配置文件变更说明 v1.2.0

## 变更概述

重写了 `config.yaml` 和 `docker-compose.deploy.yml`，优化配置结构，适配重构后的系统。

---

## config.yaml 变更

### 主要变更

#### 1. 简化规则配置 ✨

**之前**：
```yaml
threat_detection:
  sql_injection:
    enabled: true
    patterns:
      - "union.*select"
      - "select.*from"
      # ... 大量规则配置
  
custom_rules:
  - name: "深夜异常访问"
    description: "..."
    conditions: {...}
    # ... 详细规则
```

**现在**：
```yaml
threat_detection:
  sql_injection:
    enabled: true
  # 详细规则通过Web界面配置

# 访问 http://your-server:8800/rules 管理规则
```

**原因**：规则现在存储在数据库中，通过Web界面动态管理。

#### 2. 优化注释和结构

- 添加清晰的章节分隔
- 每个配置项都有说明
- 添加生产环境提示
- 添加Web界面访问说明

#### 3. 突出必须修改的配置

```yaml
web_dashboard:
  secret_key: "CHANGE_ME_TO_RANDOM_SECRET_KEY"  # ⚠️ 必须修改

authentication:
  password_salt: "CHANGE_ME_TO_RANDOM_SALT"     # ⚠️ 必须修改
```

#### 4. 保留核心配置

- 防火墙基础配置
- 威胁检测开关
- 评分系统配置
- Redis连接
- 日志配置

### 配置项对比

| 配置项 | v1.1.0 | v1.2.0 | 说明 |
|--------|--------|--------|------|
| 总行数 | 306 | 200 | 精简35% |
| 详细规则 | config中 | Web管理 | 更灵活 |
| 注释 | 基础 | 详细 | 更清晰 |
| 章节划分 | 简单 | 清晰 | 易维护 |

---

## docker-compose.deploy.yml 变更

### 主要变更

#### 1. 优化健康检查

**之前**：
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8080/api/system/health"]
```

**现在**：
```yaml
healthcheck:
  test: ["CMD", "python", "-c", "import requests; requests.get('http://localhost:8080/api/system/health', timeout=5)"]
```

**优势**：
- 不依赖curl命令
- 更可靠的健康检查
- 自定义超时时间

#### 2. 增强Redis配置

```yaml
redis:
  command: >
    redis-server
    --appendonly yes
    --appendfsync everysec
    --maxmemory 512mb
    --maxmemory-policy allkeys-lru
    --save 60 1000
    --save 300 100
    --save 900 1
    --bind 127.0.0.1
    --protected-mode yes
    --tcp-backlog 511
    --timeout 300
    --tcp-keepalive 300
```

**优化**：
- 多级保存策略
- TCP优化
- 保护模式
- 更安全的绑定

#### 3. 数据卷优化

```yaml
volumes:
  firewall-data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: ./data
```

**优势**：
- 数据存储在当前目录
- 便于备份
- 便于迁移

#### 4. 添加iptables备份目录

```yaml
volumes:
  - ./iptables-backup:/etc/iptables
```

**用途**：
- 保存iptables规则备份
- 系统重启后快速恢复

#### 5. 完善使用说明

添加了详细的命令示例：
- 启动/停止服务
- 查看日志
- 更新镜像
- 进入容器
- 使用CLI工具
- 查看iptables规则
- 数据备份

---

## 配置最佳实践

### 生产环境部署前

#### 1. 修改安全配置

```yaml
# config.yaml
web_dashboard:
  secret_key: "生成随机密钥"  # python -c "import secrets; print(secrets.token_hex(32))"

authentication:
  password_salt: "生成随机盐值"  # python -c "import secrets; print(secrets.token_hex(16))"
```

#### 2. 配置Nginx日志路径

```yaml
# config.yaml
nginx:
  access_log: "/var/log/nginx/access.log"  # 修改为实际路径

# docker-compose.deploy.yml
volumes:
  - /var/log/nginx:/var/log/nginx:ro  # 修改为实际路径
```

#### 3. 启用告警（可选）

```yaml
alerts:
  enabled: true
  email:
    enabled: true
    smtp_host: "smtp.gmail.com"
    # ... 配置邮件
```

#### 4. 配置GeoIP（可选）

下载GeoLite2-City.mmdb后：
```yaml
# config.yaml
geo_location:
  enabled: true

# docker-compose.deploy.yml
volumes:
  - ./GeoLite2-City.mmdb:/app/GeoLite2-City.mmdb:ro
```

---

## 迁移指南

### 从v1.1.0升级到v1.2.0

#### 步骤1：备份现有配置

```bash
cp config.yaml config.yaml.v1.1.0.backup
cp docker-compose.deploy.yml docker-compose.deploy.yml.backup
```

#### 步骤2：使用新配置

```bash
# 新配置已自动更新，检查差异
git diff config.yaml
git diff docker-compose.deploy.yml
```

#### 步骤3：迁移自定义配置

如果你修改过：
- Nginx日志路径
- 告警配置
- 数据库配置

请手动复制到新的config.yaml中。

#### 步骤4：迁移规则（重要）

旧的 `custom_rules` 配置需要手动迁移到Web界面：

1. 访问 `http://your-server:8800/rules`
2. 点击"自定义规则" → "+ 添加自定义规则"
3. 逐个添加之前config.yaml中的规则

**示例迁移**：

旧配置：
```yaml
custom_rules:
  - name: "深夜异常访问"
    description: "检测凌晨2-5点的/admin访问"
    enabled: true
    conditions:
      time_range: "02:00-05:00"
      path_contains: "/admin"
    score: 30
    action: "score"
```

新方式（Web界面）：
- 名称：深夜异常访问
- 描述：检测凌晨2-5点的/admin访问
- 规则类型：time
- 条件：`{"time_range": "02:00-05:00", "path_contains": "/admin"}`
- 评分：30
- 动作：score

---

## 配置验证

### 验证config.yaml

```bash
# Python验证
python -c "from utils.helpers import load_config; config = load_config('config.yaml'); print('✓ 配置文件有效')"

# YAML语法检查
python -c "import yaml; yaml.safe_load(open('config.yaml')); print('✓ YAML语法正确')"
```

### 验证docker-compose.yml

```bash
# 验证语法
docker-compose -f docker-compose.deploy.yml config --quiet
echo $?  # 应该输出 0

# 查看解析后的配置
docker-compose -f docker-compose.deploy.yml config
```

---

## 新配置特性

### 1. 更简洁
- 减少35%的配置行数
- 移除重复配置
- 保留核心选项

### 2. 更清晰
- 明确的章节划分
- 详细的注释说明
- 配置项分组

### 3. 更灵活
- 规则动态配置（Web界面）
- 环境变量覆盖
- 多种部署模式

### 4. 更安全
- 突出安全配置项
- 生产环境提示
- 最小权限原则

### 5. 更易用
- 详细的使用说明
- 常用命令列表
- 故障排查提示

---

## 常见问题

### Q: 我之前配置的规则去哪了？

A: 规则现在通过Web界面管理，存储在数据库中。访问 `/rules` 页面重新添加。

### Q: 为什么删除了详细的威胁检测配置？

A: 基础开关保留在config.yaml，详细规则通过Web界面动态配置，更灵活。

### Q: 需要手动迁移规则吗？

A: 是的，首次升级需要手动在Web界面添加规则。之后规则存储在数据库中。

### Q: config.yaml变小了，功能会减少吗？

A: 不会！功能更强了。只是将规则配置移到了更灵活的Web界面。

---

## 生产环境检查清单

部署前确认：

- [ ] 已修改 `secret_key` 为随机值
- [ ] 已修改 `password_salt` 为随机值
- [ ] 已配置正确的Nginx日志路径
- [ ] 已配置数据卷挂载路径
- [ ] 已决定是否启用告警
- [ ] 已决定是否启用地理位置
- [ ] 已准备好迁移规则到Web界面

---

## 快速生成安全配置

```bash
# 生成secret_key
python -c "import secrets; print('secret_key:', secrets.token_hex(32))"

# 生成password_salt  
python -c "import secrets; print('password_salt:', secrets.token_hex(16))"
```

复制输出到 `config.yaml` 中。

---

**配置文件已优化完成！** ✅

查看：
- `config.yaml` - 简化的主配置
- `docker-compose.deploy.yml` - 优化的部署配置
- `CONFIG_CHANGES.md` - 本变更说明

