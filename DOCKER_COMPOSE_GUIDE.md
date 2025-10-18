# 🐳 Docker Compose 部署指南

## 📦 提供的Docker Compose文件

我们提供了4个不同的docker-compose配置文件，适用于不同场景：

### 1. docker-compose.simple.yml ⭐ 推荐新手

**特点**：
- 最简化配置
- 开箱即用
- 适合快速测试

**使用场景**：
- 首次试用
- 本地开发
- 快速测试

**启动命令**：
```bash
docker-compose -f docker-compose.simple.yml up -d
```

---

### 2. docker-compose.yml - 默认配置

**特点**：
- 标准配置
- 包含详细注释
- 平衡功能和易用性

**使用场景**：
- 日常开发
- 中小型部署
- 学习参考

**启动命令**：
```bash
docker-compose up -d
```

---

### 3. docker-compose.deploy.yml - 部署配置 ⭐ 推荐生产

**特点**：
- 生产环境优化
- 完整的配置注释
- 包含健康检查
- 资源限制
- 日志管理

**使用场景**：
- 生产环境部署
- 企业级应用
- 长期运行

**启动命令**：
```bash
docker-compose -f docker-compose.deploy.yml up -d
```

---

### 4. docker-compose.prod.yml - 高性能配置

**特点**：
- 主机网络模式
- 可以操作主机iptables
- 固定版本镜像
- 最高性能

**使用场景**：
- 高性能需求
- 需要操作防火墙
- 严格版本控制

**启动命令**：
```bash
docker-compose -f docker-compose.prod.yml up -d
```

---

## 🚀 快速开始

### 最简单的方式（2步）

```bash
# 1. 启动服务
docker-compose -f docker-compose.simple.yml up -d

# 2. 访问Web界面
http://localhost:8080

# 登录
用户名: admin
密码: admin
```

---

## ⚙️ 配置修改

### 必须修改的配置

编辑 `config.yaml`，修改以下内容：

```yaml
nginx:
  access_log: "/var/log/nginx/access.log"  # 改为你的nginx日志路径
```

**Windows示例**：
```yaml
nginx:
  access_log: "C:/nginx/logs/access.log"
```

**Linux示例**：
```yaml
nginx:
  access_log: "/var/log/nginx/access.log"
```

### 修改docker-compose中的日志路径

编辑你选择的docker-compose文件：

```yaml
volumes:
  # Windows
  - C:/nginx/logs:/var/log/nginx:ro
  
  # Linux
  - /var/log/nginx:/var/log/nginx:ro
```

---

## 📋 各配置文件对比

| 特性 | simple | 默认 | deploy | prod |
|------|--------|------|--------|------|
| 易用性 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ |
| 功能完整 | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 性能优化 | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 生产就绪 | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 资源限制 | ❌ | ❌ | ✅ | ✅ |
| 健康检查 | ❌ | ✅ | ✅ | ✅ |
| 操作防火墙 | ❌ | ⚠️ | ⚠️ | ✅ |
| 版本固定 | ❌ | ❌ | ❌ | ✅ |

---

## 🎯 使用建议

### 个人用户/测试
```bash
docker-compose -f docker-compose.simple.yml up -d
```

### 中小型网站
```bash
docker-compose up -d
```

### 企业生产环境
```bash
docker-compose -f docker-compose.deploy.yml up -d
```

### 高性能需求
```bash
docker-compose -f docker-compose.prod.yml up -d
```

---

## 📝 常用命令

### 启动服务

```bash
# 使用简化版
docker-compose -f docker-compose.simple.yml up -d

# 使用部署版
docker-compose -f docker-compose.deploy.yml up -d

# 使用默认版
docker-compose up -d
```

### 查看日志

```bash
# 查看所有服务日志
docker-compose -f docker-compose.deploy.yml logs -f

# 只看防火墙服务
docker-compose -f docker-compose.deploy.yml logs -f firewall

# 只看Redis
docker-compose -f docker-compose.deploy.yml logs -f redis
```

### 停止服务

```bash
# 停止但保留数据
docker-compose -f docker-compose.deploy.yml down

# 停止并删除数据卷
docker-compose -f docker-compose.deploy.yml down -v
```

### 更新镜像

```bash
# 拉取最新镜像
docker-compose -f docker-compose.deploy.yml pull

# 重新启动
docker-compose -f docker-compose.deploy.yml up -d
```

### 查看服务状态

```bash
docker-compose -f docker-compose.deploy.yml ps
```

### 进入容器

```bash
# 进入防火墙容器
docker-compose -f docker-compose.deploy.yml exec firewall bash

# 进入Redis容器
docker-compose -f docker-compose.deploy.yml exec redis sh
```

---

## 🔧 高级配置

### 使用外部Redis

如果你已经有Redis服务器：

```yaml
services:
  firewall:
    environment:
      - REDIS_HOST=192.168.1.100  # 外部Redis地址
      - REDIS_PORT=6379
    # 移除 depends_on: redis

# 注释掉整个redis服务
```

### 使用外部数据库

如果使用MySQL或PostgreSQL：

编辑 `config.yaml`：
```yaml
database:
  type: "mysql"
  host: "192.168.1.100"
  port: 3306
  user: "firewall"
  password: "password"
  database: "firewall_db"
```

### 启用HTTPS（通过Nginx反向代理）

```yaml
services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - firewall
```

---

## 🛠️ 部署前检查清单

在生产环境部署前，确认：

- [ ] 已修改 `config.yaml` 中的nginx日志路径
- [ ] 已修改 docker-compose 中的日志卷挂载路径
- [ ] 已创建必要的目录（exports/, logs/）
- [ ] 如果使用地理位置，已下载GeoLite2-City.mmdb
- [ ] 已配置告警（邮件/Webhook等）
- [ ] 已修改 config.yaml 中的 secret_key 和 password_salt
- [ ] 已测试Web界面可以访问
- [ ] 已修改默认密码

---

## 💡 性能优化建议

### 1. 启用Redis缓存

config.yaml:
```yaml
redis:
  enabled: true  # 性能提升60%
```

### 2. 使用固定版本镜像（生产环境）

docker-compose:
```yaml
image: zbaimo/nginx-firewall:v1.0.0  # 不用latest
```

### 3. 调整资源限制

根据实际负载调整：
```yaml
deploy:
  resources:
    limits:
      cpus: '4.0'      # 大型网站
      memory: 2G
```

### 4. 使用主机网络（最高性能）

docker-compose:
```yaml
network_mode: "host"
```

---

## 🔍 故障排查

### 容器无法启动

```bash
# 查看详细日志
docker-compose -f docker-compose.deploy.yml logs firewall

# 检查配置文件
docker-compose -f docker-compose.deploy.yml config

# 验证配置文件语法
python -c "from utils.helpers import load_config; load_config('config.yaml')"
```

### Redis连接失败

```bash
# 检查Redis状态
docker-compose -f docker-compose.deploy.yml ps redis

# 测试Redis连接
docker-compose -f docker-compose.deploy.yml exec firewall redis-cli -h redis ping
```

### 无法访问Web界面

```bash
# 检查端口映射
docker-compose -f docker-compose.deploy.yml port firewall 8080

# 检查健康状态
docker-compose -f docker-compose.deploy.yml ps
```

### 权限问题

```bash
# 确保使用privileged模式
# 或添加cap_add: NET_ADMIN
```

---

## 📊 资源使用建议

### 小型网站（<1000 req/天）
```yaml
limits:
  cpus: '1.0'
  memory: 512M
```

### 中型网站（1000-10000 req/天）
```yaml
limits:
  cpus: '2.0'
  memory: 1G
```

### 大型网站（>10000 req/天）
```yaml
limits:
  cpus: '4.0'
  memory: 2G
```

---

## 🎯 推荐配置

**新手/测试**: `docker-compose.simple.yml`  
**日常使用**: `docker-compose.yml`  
**生产部署**: `docker-compose.deploy.yml` ⭐  
**高性能**: `docker-compose.prod.yml`  

---

**现在就开始部署**：

```bash
docker-compose -f docker-compose.deploy.yml up -d
```

**访问**: http://localhost:8080


