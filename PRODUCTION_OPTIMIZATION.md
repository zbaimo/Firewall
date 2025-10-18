# 🚀 生产环境优化指南

## 当前状态

✅ 系统已成功启动
⚠️ 正在使用Flask开发服务器（不适合生产环境）

---

## 🔧 优化1：使用Gunicorn (推荐)

### 为什么需要Gunicorn？

Flask内置服务器的问题：
- ❌ 单线程，性能差
- ❌ 不支持并发
- ❌ 不稳定，容易崩溃
- ❌ 没有负载均衡

Gunicorn的优势：
- ✅ 多进程/多线程
- ✅ 高并发处理
- ✅ 生产级稳定性
- ✅ 自动重启
- ✅ 资源管理

### 实施步骤

#### 1. 修改 requirements.txt

添加 Gunicorn：

\`\`\`txt
gunicorn>=21.2.0
\`\`\`

#### 2. 创建 gunicorn_config.py

\`\`\`python
# Gunicorn配置文件
import multiprocessing

# 监听地址
bind = "0.0.0.0:8080"

# 工作进程数（推荐：CPU核心数 * 2 + 1）
workers = multiprocessing.cpu_count() * 2 + 1

# 工作模式（sync, gevent, eventlet）
worker_class = "sync"

# 每个进程的线程数
threads = 2

# 超时时间（秒）
timeout = 120

# 保持连接时间（秒）
keepalive = 5

# 日志
accesslog = "logs/gunicorn_access.log"
errorlog = "logs/gunicorn_error.log"
loglevel = "info"

# 进程名称
proc_name = "nginx-firewall"

# 优雅重启超时
graceful_timeout = 30

# 最大请求数（防止内存泄漏）
max_requests = 1000
max_requests_jitter = 100

# Daemon模式
daemon = False

# PID文件
pidfile = "logs/gunicorn.pid"
\`\`\`

#### 3. 修改 Dockerfile

\`\`\`dockerfile
# 使用Gunicorn启动
CMD ["gunicorn", "--config", "gunicorn_config.py", "main:app"]
\`\`\`

或者修改 main.py 启动方式：

\`\`\`python
if __name__ == '__main__':
    # 检查是否在容器中
    import os
    if os.environ.get('DOCKER_CONTAINER'):
        # Docker环境，使用Gunicorn
        os.system('gunicorn --config gunicorn_config.py main:app')
    else:
        # 本地开发环境
        app = create_app()
        app.run(host='0.0.0.0', port=8080)
\`\`\`

---

## 🔧 优化2：使用Nginx反向代理

### 架构

\`\`\`
[用户] → [Nginx] → [Gunicorn] → [Flask应用]
\`\`\`

### Nginx配置

\`\`\`nginx
server {
    listen 80;
    server_name your-domain.com;

    # 限流
    limit_req_zone $binary_remote_addr zone=firewall:10m rate=10r/s;
    limit_req zone=firewall burst=20 nodelay;

    # 日志
    access_log /var/log/nginx/firewall_access.log;
    error_log /var/log/nginx/firewall_error.log;

    # 静态文件
    location /static/ {
        alias /app/web/static/;
        expires 7d;
        add_header Cache-Control "public, immutable";
    }

    # API和Web界面
    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 超时设置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        
        # WebSocket支持（如果需要）
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}

# HTTPS配置（推荐）
server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # 其他配置同上...
}
\`\`\`

---

## 🔧 优化3：Docker Compose优化

### docker-compose.prod.yml

\`\`\`yaml
services:
  firewall:
    image: zbaimo/nginx-firewall:latest
    container_name: nginx-firewall
    restart: always
    network_mode: "host"
    
    environment:
      - TZ=Asia/Shanghai
      - REDIS_HOST=localhost
      - REDIS_PORT=6379
      - DOCKER_CONTAINER=true  # 启用Gunicorn
      - WORKERS=4  # Gunicorn工作进程数
    
    volumes:
      - ./config.yaml:/app/config.yaml:ro
      - /root/data/Nginx:/var/log/nginx:ro
      - firewall-data:/data
      - ./logs:/app/logs
      - ./exports:/app/exports
    
    privileged: true
    cap_add:
      - NET_ADMIN
      - NET_RAW
    
    deploy:
      resources:
        limits:
          cpus: '4.0'
          memory: 2G
        reservations:
          cpus: '1.0'
          memory: 512M

  redis:
    image: redis:7-alpine
    container_name: firewall-redis
    restart: always
    network_mode: "host"
    
    command: >
      redis-server
      --appendonly yes
      --maxmemory 1gb
      --maxmemory-policy allkeys-lru
      --save 60 1000
      --bind 127.0.0.1
      --tcp-backlog 511
      --timeout 300
    
    volumes:
      - redis-data:/data
    
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 1G

volumes:
  firewall-data:
  redis-data:
\`\`\`

---

## 📊 性能监控

### 监控命令

\`\`\`bash
# CPU和内存使用
docker stats nginx-firewall firewall-redis

# 进程数
ps aux | grep gunicorn | wc -l

# 连接数
netstat -an | grep 8080 | wc -l

# 日志监控
tail -f logs/gunicorn_access.log
tail -f logs/gunicorn_error.log
\`\`\`

### 性能指标

| 指标 | 开发服务器 | Gunicorn | Nginx+Gunicorn |
|------|-----------|----------|----------------|
| 并发请求 | 1 | 50-100 | 500-1000 |
| 响应时间 | 100ms | 50ms | 30ms |
| 稳定性 | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| CPU使用 | 单核 | 多核 | 多核+缓存 |

---

## 🔒 安全加固

### 1. 启用HTTPS

\`\`\`bash
# 使用Let's Encrypt
certbot --nginx -d your-domain.com
\`\`\`

### 2. 防火墙规则

\`\`\`bash
# 只允许必要端口
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw deny 8080/tcp   # 禁止直接访问后端（通过Nginx代理）
ufw enable
\`\`\`

### 3. 限流配置

在 config.yaml 中：

\`\`\`yaml
rate_limiting:
  enabled: true
  requests_per_minute: 60
  burst: 10
\`\`\`

---

## 📈 扩展方案

### 单机优化（当前）

\`\`\`
[Nginx] → [Gunicorn (4 workers)] → [Redis]
\`\`\`

### 高可用架构（未来）

\`\`\`
          [Load Balancer]
                 ↓
    ┌────────────┼────────────┐
    ↓            ↓            ↓
[Server 1]  [Server 2]  [Server 3]
    ↓            ↓            ↓
 [Redis Cluster] [MySQL Cluster]
\`\`\`

---

## 🚀 快速部署Gunicorn版本

如果现在不想改动太多，可以这样快速优化：

### 方法1：临时使用Gunicorn

\`\`\`bash
# 进入容器
docker exec -it nginx-firewall bash

# 安装Gunicorn
pip install gunicorn

# 停止当前进程
pkill -f main.py

# 启动Gunicorn
gunicorn --bind 0.0.0.0:8080 --workers 4 --threads 2 main:app
\`\`\`

### 方法2：等待新版本镜像

我们会在下一个版本中集成Gunicorn。

---

## 📝 当前建议

**对于您当前的系统**：

1. ✅ 目前可以继续使用（功能正常）
2. ⚠️ 如果访问量不大（<100 并发），暂时无需改动
3. 📈 如果访问量增加，建议升级到Gunicorn
4. 🔒 建议尽快设置HTTPS和防火墙规则

---

## 🎯 下一步

1. **现在**：测试所有功能，确保正常工作
2. **短期**：配置告警系统（邮件/Telegram）
3. **中期**：升级到Gunicorn
4. **长期**：添加Nginx反向代理和HTTPS

---

**系统已经可以正常使用了！** 🎉

访问 http://您的服务器IP:8800 开始使用吧！


