# ⚠️ 修复Docker数据卷冲突

## 问题
```
Volume "firewall_firewall-data" exists but doesn't match configuration.
Recreate (data will be lost)? (y/N)
```

## 原因
docker-compose.deploy.yml修改了数据卷配置，导致与现有卷冲突。

## 安全解决方案（保留数据）

### 方法1：使用现有卷（推荐，最简单）

```bash
# 按 N (不重建)
N

# 修改docker-compose.deploy.yml，使用简单的卷配置
# 见下文
```

### 方法2：迁移数据到新卷

```bash
# 1. 按 N 退出
N

# 2. 备份现有数据
docker run --rm -v firewall_firewall-data:/source -v $(pwd)/backup:/backup alpine tar czf /backup/firewall-data-backup.tar.gz -C /source .

# 3. 创建新目录
mkdir -p data redis-data

# 4. 恢复数据到新目录
docker run --rm -v $(pwd)/data:/target -v $(pwd)/backup:/backup alpine tar xzf /backup/firewall-data-backup.tar.gz -C /target

# 5. 删除旧卷
docker volume rm firewall_firewall-data firewall_redis-data

# 6. 重新启动
docker compose -f docker-compose.deploy.yml up -d
```

---

## 快速修复（推荐）⭐

修改docker-compose.deploy.yml，使用简单的卷配置：

### 在服务器上执行：

```bash
cd /root/data/firewall

# 创建临时修复文件
cat > docker-compose.deploy.yml << 'EOF'
services:
  firewall:
    image: zbaimo/nginx-firewall:latest
    container_name: nginx-firewall
    restart: always
    network_mode: "host"
    
    volumes:
      - ./config.yaml:/app/config.yaml:ro
      - /root/data/Nginx:/var/log/nginx:ro
      - firewall-data:/data
      - ./logs:/app/logs
      - ./exports:/app/exports
    
    environment:
      - TZ=Asia/Shanghai
      - REDIS_HOST=localhost
      - REDIS_PORT=6379
    
    privileged: true
    
    cap_add:
      - NET_ADMIN
      - NET_RAW
    
    depends_on:
      redis:
        condition: service_healthy

  redis:
    image: redis:7-alpine
    container_name: firewall-redis
    restart: always
    network_mode: "host"
    
    command: >
      redis-server
      --appendonly yes
      --maxmemory 512mb
      --maxmemory-policy allkeys-lru
      --bind 127.0.0.1
    
    volumes:
      - redis-data:/data
    
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 3

volumes:
  firewall-data:
  redis-data:
EOF

# 现在启动
docker compose -f docker-compose.deploy.yml up -d
```

---

## 或者简单跳过冲突

如果不需要之前的数据：

```bash
# 1. 选择 y (会丢失旧数据，但创建新的)
y

# 2. 等待启动完成

# 3. 查看日志
docker logs nginx-firewall
```

---

## 验证成功

```bash
# 查看容器状态
docker ps

# 查看数据卷
docker volume ls | grep firewall

# 查看日志
docker logs nginx-firewall | grep "初始化"
```

---

## 推荐方案

**如果您刚开始部署，旧数据不重要**：
- 选择 `y`，重新创建卷
- 系统会自动初始化默认规则

**如果您有重要数据**：
- 选择 `N`
- 使用上面的"快速修复"简化配置
- 或使用"方法2"迁移数据

---

**现在在服务器执行**：

```bash
# 如果数据不重要（推荐）
y

# 如果需要保留数据
N
# 然后使用上面的快速修复方案
```

