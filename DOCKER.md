# Docker部署指南

## 🐳 快速开始

### 方式1：使用Docker Hub镜像（推荐）

```bash
# 拉取最新镜像
docker pull your-dockerhub-username/nginx-firewall:latest

# 运行容器
docker run -d \
  --name nginx-firewall \
  -p 8080:8080 \
  -v $(pwd)/config.yaml:/app/config.yaml:ro \
  -v /var/log/nginx:/var/log/nginx:ro \
  -v firewall-data:/data \
  your-dockerhub-username/nginx-firewall:latest
```

### 方式2：使用Docker Compose（推荐）

```bash
# 克隆仓库
git clone https://github.com/your-username/Firewall.git
cd Firewall

# 编辑配置
cp config.yaml config.yaml.local
nano config.yaml.local

# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

### 方式3：本地构建

```bash
# 构建镜像
docker build -t nginx-firewall:local .

# 运行
docker run -d \
  --name nginx-firewall \
  -p 8080:8080 \
  -v $(pwd)/config.yaml:/app/config.yaml:ro \
  nginx-firewall:local
```

---

## 📋 前置要求

### 1. 安装Docker

**Ubuntu/Debian:**
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
```

**CentOS/RHEL:**
```bash
sudo yum install -y docker
sudo systemctl start docker
sudo systemctl enable docker
```

**Windows/macOS:**
- 下载并安装 [Docker Desktop](https://www.docker.com/products/docker-desktop/)

### 2. 安装Docker Compose（可选）

```bash
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

---

## ⚙️ 配置说明

### 环境变量

可以通过环境变量覆盖配置：

```bash
docker run -d \
  -e REDIS_HOST=redis \
  -e REDIS_PORT=6379 \
  -e ALERT_ENABLED=true \
  nginx-firewall:latest
```

### 数据卷挂载

**必需挂载：**
```bash
# 配置文件（只读）
-v $(pwd)/config.yaml:/app/config.yaml:ro

# Nginx日志目录（只读）
-v /var/log/nginx:/var/log/nginx:ro
```

**可选挂载：**
```bash
# 数据持久化
-v firewall-data:/data

# 导出文件
-v $(pwd)/exports:/app/exports

# 日志文件
-v $(pwd)/logs:/app/logs

# GeoIP数据库
-v $(pwd)/GeoLite2-City.mmdb:/app/GeoLite2-City.mmdb:ro
```

### 网络配置

**桥接模式（默认）：**
```yaml
networks:
  - firewall-network
```

**主机模式（可以操作iptables）：**
```yaml
network_mode: "host"
```

---

## 🚀 GitHub Actions自动构建

### 1. 配置Docker Hub密钥

在GitHub仓库设置中添加Secrets：

1. 访问: `Settings` → `Secrets and variables` → `Actions`
2. 添加以下secrets：
   - `DOCKERHUB_USERNAME`: 你的Docker Hub用户名
   - `DOCKERHUB_PASSWORD`: 你的Docker Hub访问令牌

### 2. 修改镜像名称

编辑 `.github/workflows/docker-build.yml`：

```yaml
env:
  DOCKER_IMAGE: your-dockerhub-username/nginx-firewall
```

改为你的Docker Hub用户名。

### 3. 触发构建

**自动触发：**
- 推送到 `main` 或 `master` 分支
- 创建 `v*` 标签（如 `v1.0.0`）

**手动触发：**
- 访问 `Actions` → `Build and Push Docker Image` → `Run workflow`

### 4. 版本发布

```bash
# 创建版本标签
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0

# GitHub Actions会自动构建并推送
# 生成的镜像标签：
# - your-username/nginx-firewall:v1.0.0
# - your-username/nginx-firewall:v1.0
# - your-username/nginx-firewall:v1
# - your-username/nginx-firewall:latest
```

---

## 🛠️ 常用命令

### 容器管理

```bash
# 查看运行状态
docker ps

# 查看日志
docker logs nginx-firewall
docker logs -f nginx-firewall  # 实时查看

# 进入容器
docker exec -it nginx-firewall bash

# 重启容器
docker restart nginx-firewall

# 停止容器
docker stop nginx-firewall

# 删除容器
docker rm nginx-firewall
```

### 镜像管理

```bash
# 查看镜像
docker images

# 拉取最新镜像
docker pull your-username/nginx-firewall:latest

# 删除镜像
docker rmi nginx-firewall:local

# 清理未使用的镜像
docker image prune -a
```

### Docker Compose

```bash
# 启动服务（后台）
docker-compose up -d

# 查看日志
docker-compose logs -f

# 重启服务
docker-compose restart

# 停止服务
docker-compose stop

# 停止并删除容器
docker-compose down

# 停止并删除容器+数据卷
docker-compose down -v
```

---

## 🔧 高级配置

### 1. 操作主机防火墙

**Linux (iptables):**

```yaml
# docker-compose.yml
services:
  firewall:
    network_mode: "host"
    privileged: true
    cap_add:
      - NET_ADMIN
      - NET_RAW
```

或Docker命令：
```bash
docker run -d \
  --network host \
  --privileged \
  --cap-add=NET_ADMIN \
  --cap-add=NET_RAW \
  nginx-firewall:latest
```

### 2. 资源限制

```yaml
# docker-compose.yml
services:
  firewall:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 256M
```

或Docker命令：
```bash
docker run -d \
  --cpus=2 \
  --memory=1g \
  nginx-firewall:latest
```

### 3. 健康检查

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8080/"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

### 4. 自动重启

```yaml
restart: unless-stopped
```

---

## 📊 监控和日志

### 查看实时日志

```bash
# Docker
docker logs -f --tail=100 nginx-firewall

# Docker Compose
docker-compose logs -f --tail=100
```

### 导出日志

```bash
docker logs nginx-firewall > firewall.log
```

### 访问Web管理后台

```bash
# 浏览器访问
http://localhost:8080

# 或服务器IP
http://your-server-ip:8080
```

### 查看容器状态

```bash
docker stats nginx-firewall
```

---

## 🔍 故障排查

### 容器无法启动

```bash
# 查看详细错误
docker logs nginx-firewall

# 检查配置文件
docker run --rm \
  -v $(pwd)/config.yaml:/app/config.yaml:ro \
  nginx-firewall:latest \
  python -c "from utils.helpers import load_config; load_config()"
```

### 无法访问Web界面

```bash
# 检查端口映射
docker port nginx-firewall

# 检查防火墙
sudo ufw allow 8080  # Ubuntu
sudo firewall-cmd --add-port=8080/tcp --permanent  # CentOS
```

### Redis连接失败

```bash
# 检查Redis容器
docker-compose logs redis

# 测试连接
docker exec nginx-firewall redis-cli -h redis ping
```

### 权限问题

```bash
# 给予容器适当权限
docker run -d \
  --privileged \
  --cap-add=NET_ADMIN \
  nginx-firewall:latest
```

---

## 🔒 安全建议

1. **不要暴露管理端口到公网**
   ```bash
   # 只绑定到本地
   -p 127.0.0.1:8080:8080
   ```

2. **使用只读挂载**
   ```bash
   -v $(pwd)/config.yaml:/app/config.yaml:ro
   ```

3. **定期更新镜像**
   ```bash
   docker pull your-username/nginx-firewall:latest
   docker-compose pull
   docker-compose up -d
   ```

4. **使用secrets管理敏感信息**
   ```yaml
   secrets:
     - db_password
   ```

---

## 📦 生产环境部署

### 完整示例

```yaml
version: '3.8'

services:
  firewall:
    image: your-username/nginx-firewall:latest
    container_name: nginx-firewall
    restart: always
    
    network_mode: "host"
    
    volumes:
      - ./config.yaml:/app/config.yaml:ro
      - /var/log/nginx:/var/log/nginx:ro
      - firewall-data:/data
      - ./exports:/app/exports
      - ./GeoLite2-City.mmdb:/app/GeoLite2-City.mmdb:ro
    
    environment:
      - TZ=Asia/Shanghai
      - REDIS_HOST=localhost
    
    privileged: true
    cap_add:
      - NET_ADMIN
    
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 1G
    
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

volumes:
  firewall-data:
```

### 使用Nginx反向代理

```nginx
server {
    listen 80;
    server_name firewall.yourdomain.com;
    
    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

---

## 🆘 获取帮助

- 查看日志: `docker logs nginx-firewall`
- 进入容器: `docker exec -it nginx-firewall bash`
- 检查配置: `docker exec nginx-firewall cat /app/config.yaml`
- GitHub Issues: 提交问题反馈

---

## 📝 更新日志

查看最新版本: [GitHub Releases](https://github.com/your-username/Firewall/releases)

更新容器:
```bash
docker-compose pull
docker-compose up -d
```

