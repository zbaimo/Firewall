# 🚀 部署指南

## 快速开始

### 方式1：使用部署脚本（推荐）⭐

#### Windows

```bash
deploy.bat
```

#### Linux/Mac

```bash
chmod +x deploy.sh
./deploy.sh
```

脚本会自动：
- ✅ 检查依赖（Docker、Docker Compose）
- ✅ 选择部署模式
- ✅ 检查配置文件
- ✅ 创建必要目录
- ✅ 拉取镜像
- ✅ 启动服务
- ✅ 显示访问地址

---

### 方式2：手动部署

```bash
# 1. 拉取镜像
docker pull zbaimo/nginx-firewall:latest

# 2. 准备配置文件（如果还没有）
cp .env.example .env
# 编辑 .env 修改配置

# 3. 创建必要目录
mkdir -p exports logs data

# 4. 启动服务
docker-compose -f docker-compose.deploy.yml up -d

# 5. 查看日志
docker-compose -f docker-compose.deploy.yml logs -f
```

---

## 部署前准备

### 1. 安装Docker

#### Windows
下载并安装 [Docker Desktop](https://www.docker.com/products/docker-desktop)

#### Linux (Ubuntu/Debian)
```bash
curl -fsSL https://get.docker.com | bash -
sudo usermod -aG docker $USER
```

#### Mac
下载并安装 [Docker Desktop for Mac](https://www.docker.com/products/docker-desktop)

### 2. 验证安装

```bash
docker --version
docker-compose --version
```

---

## 配置说明

### 必须修改的配置

#### 1. Nginx日志路径

编辑 `docker-compose.deploy.yml`：

```yaml
volumes:
  # Windows
  - C:/nginx/logs:/var/log/nginx:ro
  
  # Linux
  - /var/log/nginx:/var/log/nginx:ro
```

#### 2. 环境变量

复制并编辑环境变量文件：

```bash
cp .env.example .env
```

编辑 `.env`：
```bash
# 修改Nginx日志路径
NGINX_LOG_PATH=/var/log/nginx

# 修改时区
TZ=Asia/Shanghai

# 修改端口（可选）
WEB_PORT=8080
```

---

## 部署模式选择

### 简单模式（快速测试）

**特点**：
- 最简配置
- 开箱即用
- 适合测试

**使用**：
```bash
docker-compose -f docker-compose.simple.yml up -d
```

---

### 标准模式（日常使用）

**特点**：
- 平衡配置
- 功能完整
- 适合中小型网站

**使用**：
```bash
docker-compose up -d
```

---

### 生产模式（推荐）⭐

**特点**：
- 生产优化
- 健康检查
- 资源限制
- 日志管理

**使用**：
```bash
docker-compose -f docker-compose.deploy.yml up -d
```

**配置亮点**：
```yaml
# 健康检查
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8080/api/system/health"]
  interval: 30s

# 资源限制
deploy:
  resources:
    limits:
      cpus: '2.0'
      memory: 1G

# 日志管理
logging:
  options:
    max-size: "10m"
    max-file: "3"
```

---

### 高性能模式

**特点**：
- 主机网络
- 可操作防火墙
- 固定版本
- 最高性能

**使用**：
```bash
docker-compose -f docker-compose.prod.yml up -d
```

**注意**：
- 需要 `privileged: true` 或 `cap_add: NET_ADMIN`
- 使用 `network_mode: "host"` 性能最佳

---

## 访问Web界面

### 1. 打开浏览器

```
http://localhost:8080
```

或者使用服务器IP：
```
http://your-server-ip:8080
```

### 2. 首次登录

```
用户名: admin
密码: admin
```

### 3. 强制修改密码

首次登录会自动跳转到修改密码页面。

### 4. 启用2FA（可选，推荐）

设置 → 启用两步验证

---

## 常用命令

### 查看服务状态

```bash
docker-compose -f docker-compose.deploy.yml ps
```

### 查看日志

```bash
# 所有服务
docker-compose -f docker-compose.deploy.yml logs -f

# 只看防火墙
docker-compose -f docker-compose.deploy.yml logs -f firewall

# 只看Redis
docker-compose -f docker-compose.deploy.yml logs -f redis

# 最近100行
docker-compose -f docker-compose.deploy.yml logs --tail=100
```

### 停止服务

```bash
# 停止但保留数据
docker-compose -f docker-compose.deploy.yml down

# 停止并删除数据
docker-compose -f docker-compose.deploy.yml down -v
```

### 重启服务

```bash
# 重启所有服务
docker-compose -f docker-compose.deploy.yml restart

# 只重启防火墙
docker-compose -f docker-compose.deploy.yml restart firewall
```

### 更新镜像

```bash
# 拉取最新版本
docker-compose -f docker-compose.deploy.yml pull

# 重新启动
docker-compose -f docker-compose.deploy.yml up -d
```

### 进入容器调试

```bash
# 进入防火墙容器
docker-compose -f docker-compose.deploy.yml exec firewall bash

# 进入Redis容器
docker-compose -f docker-compose.deploy.yml exec redis sh
```

---

## 数据管理

### 数据持久化

Docker卷保存在：
```bash
# 查看卷
docker volume ls | grep firewall

# 查看卷详情
docker volume inspect firewall_firewall-data
```

### 备份数据

```bash
# 备份数据卷
docker run --rm -v firewall_firewall-data:/data -v $(pwd):/backup alpine tar czf /backup/firewall-backup.tar.gz /data

# 备份配置文件
tar czf config-backup.tar.gz config.yaml .env
```

### 恢复数据

```bash
# 恢复数据卷
docker run --rm -v firewall_firewall-data:/data -v $(pwd):/backup alpine tar xzf /backup/firewall-backup.tar.gz -C /
```

---

## 性能优化

### 1. 启用Redis缓存

`.env`:
```bash
CACHE_ENABLED=true
```

性能提升：**60%**

### 2. 使用主机网络

```yaml
network_mode: "host"
```

性能提升：**30%**

### 3. 调整资源限制

根据实际负载：

```yaml
deploy:
  resources:
    limits:
      cpus: '4.0'      # 大型网站
      memory: 2G
```

### 4. 优化Redis配置

```yaml
command: >
  redis-server
  --maxmemory 1gb
  --maxmemory-policy allkeys-lru
  --save 60 1000
```

---

## 安全加固

### 1. 修改默认密钥

`.env`:
```bash
# 生成随机密钥
WEB_SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")
PASSWORD_SALT=$(python -c "import secrets; print(secrets.token_hex(16))")
```

### 2. 启用2FA

Web界面 → 设置 → 启用两步验证

### 3. 限制访问IP

使用Nginx反向代理：

```nginx
server {
    listen 80;
    server_name firewall.example.com;
    
    # 只允许特定IP访问
    allow 192.168.1.0/24;
    deny all;
    
    location / {
        proxy_pass http://localhost:8080;
    }
}
```

### 4. 启用HTTPS

```yaml
services:
  nginx:
    image: nginx:alpine
    ports:
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
```

---

## 监控和告警

### 1. 启用邮件告警

`.env`:
```bash
ALERT_EMAIL_ENABLED=true
ALERT_EMAIL_SMTP_HOST=smtp.gmail.com
ALERT_EMAIL_SMTP_PORT=587
ALERT_EMAIL_FROM=alert@example.com
ALERT_EMAIL_TO=admin@example.com
ALERT_EMAIL_USERNAME=your_email@gmail.com
ALERT_EMAIL_PASSWORD=your_app_password
```

### 2. 启用Webhook告警

```bash
ALERT_WEBHOOK_ENABLED=true
ALERT_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

### 3. 启用Telegram告警

```bash
ALERT_TELEGRAM_ENABLED=true
ALERT_TELEGRAM_BOT_TOKEN=your_bot_token
ALERT_TELEGRAM_CHAT_ID=your_chat_id
```

---

## 故障排查

### 容器无法启动

```bash
# 查看详细日志
docker-compose -f docker-compose.deploy.yml logs

# 检查配置
docker-compose -f docker-compose.deploy.yml config

# 验证配置文件
docker-compose -f docker-compose.deploy.yml config --quiet
```

### Redis连接失败

```bash
# 检查Redis状态
docker-compose -f docker-compose.deploy.yml ps redis

# 测试连接
docker-compose -f docker-compose.deploy.yml exec firewall redis-cli -h redis ping
```

### 无法访问Web界面

```bash
# 检查端口
docker-compose -f docker-compose.deploy.yml port firewall 8080

# 检查防火墙（Linux）
sudo ufw allow 8080

# 检查容器网络
docker network inspect firewall_firewall-network
```

### Nginx日志读取失败

1. 检查日志路径是否正确
2. 检查卷挂载权限
3. 检查日志文件是否存在

```bash
# 进入容器检查
docker-compose -f docker-compose.deploy.yml exec firewall bash
ls -la /var/log/nginx/
```

---

## 升级指南

### 1. 备份数据

```bash
# 备份数据库
docker-compose -f docker-compose.deploy.yml exec firewall python -c "from tools.cli_manager import export_all; export_all()"

# 备份配置
cp config.yaml config.yaml.backup
cp .env .env.backup
```

### 2. 拉取新版本

```bash
docker-compose -f docker-compose.deploy.yml pull
```

### 3. 停止旧版本

```bash
docker-compose -f docker-compose.deploy.yml down
```

### 4. 启动新版本

```bash
docker-compose -f docker-compose.deploy.yml up -d
```

### 5. 验证

```bash
# 检查版本
docker-compose -f docker-compose.deploy.yml exec firewall python -c "print(open('VERSION').read())"

# 检查健康状态
curl http://localhost:8080/api/system/health
```

---

## 生产环境清单

部署到生产环境前，确认：

- [ ] 已安装Docker和Docker Compose
- [ ] 已修改 `.env` 中的所有配置
- [ ] 已修改 `config.yaml` 中的密钥和盐值
- [ ] 已配置正确的Nginx日志路径
- [ ] 已创建必要的目录（exports, logs）
- [ ] 已下载GeoIP数据库（如果启用）
- [ ] 已配置告警（邮件/Webhook）
- [ ] 已测试Web界面访问
- [ ] 已修改默认密码
- [ ] 已启用2FA
- [ ] 已配置HTTPS（如果需要）
- [ ] 已设置自动备份

---

## 推荐架构

### 小型网站

```
[Nginx] → [防火墙+Redis] → [SQLite]
```

### 中型网站

```
[Nginx] → [防火墙] → [Redis] → [MySQL]
                    ↓
                 [Alerts]
```

### 大型网站

```
             [Load Balancer]
                    ↓
         [Nginx Cluster (多台)]
                    ↓
          [防火墙 Cluster (多台)]
                    ↓
         [Redis Cluster] [MySQL Master-Slave]
                    ↓
            [监控&告警系统]
```

---

## 获取帮助

- 📖 完整文档：`DOCKER_COMPOSE_GUIDE.md`
- 🐛 问题追踪：GitHub Issues
- 💬 讨论区：GitHub Discussions
- 📧 邮件支持：support@example.com

---

**现在就开始部署**：

```bash
# Windows
deploy.bat

# Linux/Mac
./deploy.sh
```

**访问**: http://localhost:8080


