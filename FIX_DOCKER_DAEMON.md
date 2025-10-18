# 🔧 修复Docker Daemon错误

## 错误信息
```
Cannot connect to the Docker daemon at unix:///var/run/docker.sock. 
Is the docker daemon running?
```

## 解决方案

### 在服务器上执行以下命令

#### 1. 检查Docker服务状态

```bash
# 检查Docker服务状态
systemctl status docker

# 或使用
service docker status
```

#### 2. 启动Docker服务

```bash
# 方法1：使用systemctl
sudo systemctl start docker

# 方法2：使用service
sudo service docker start

# 设置开机自启
sudo systemctl enable docker
```

#### 3. 验证Docker运行

```bash
# 检查Docker版本
docker --version

# 检查Docker info
docker info

# 测试运行
docker ps
```

#### 4. 重新启动防火墙系统

```bash
cd /root/data/firewall

# 启动服务
docker compose -f docker-compose.deploy.yml up -d

# 或使用旧版命令
docker-compose -f docker-compose.deploy.yml up -d
```

---

## 常见问题

### 问题1: Permission denied

```bash
# 解决方案：添加用户到docker组
sudo usermod -aG docker $USER

# 重新登录或执行
newgrp docker

# 验证
docker ps
```

### 问题2: Docker未安装

```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com | bash

# 或手动安装
sudo apt-get update
sudo apt-get install docker.io docker-compose -y

# 启动服务
sudo systemctl start docker
sudo systemctl enable docker
```

### 问题3: Docker Compose版本

```bash
# 检查版本
docker compose version

# 如果不支持，使用旧版
docker-compose version

# 更新Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

---

## 完整部署流程

### 步骤1: 确保Docker运行

```bash
# 启动Docker
sudo systemctl start docker

# 检查状态
sudo systemctl status docker

# 应该看到: Active: active (running)
```

### 步骤2: 检查Docker Compose

```bash
# 尝试新版命令
docker compose version

# 如果失败，使用旧版
docker-compose version
```

### 步骤3: 启动防火墙系统

```bash
cd /root/data/firewall

# 新版Docker Compose
docker compose -f docker-compose.deploy.yml up -d

# 或旧版
docker-compose -f docker-compose.deploy.yml up -d
```

### 步骤4: 验证启动

```bash
# 查看容器状态
docker ps

# 应该看到:
# nginx-firewall
# firewall-redis

# 查看日志
docker logs nginx-firewall | head -50

# 应该看到:
# ✓ 已初始化 6 条默认威胁检测规则
# ✓ 已初始化 1 条默认自定义规则
# 🚀 系统已启动
```

---

## 快速命令参考

```bash
# 启动Docker
sudo systemctl start docker

# 查看Docker状态
sudo systemctl status docker

# 重启Docker
sudo systemctl restart docker

# 查看Docker日志
sudo journalctl -u docker.service -n 50

# 启动防火墙
cd /root/data/firewall
docker compose -f docker-compose.deploy.yml up -d

# 查看防火墙日志
docker logs -f nginx-firewall

# 查看所有容器
docker ps -a
```

---

## 故障排查

### 如果Docker无法启动

```bash
# 查看详细错误
sudo journalctl -xe -u docker.service

# 检查Docker配置
sudo cat /etc/docker/daemon.json

# 重置Docker
sudo systemctl stop docker
sudo rm -rf /var/lib/docker
sudo systemctl start docker
```

### 如果端口被占用

```bash
# 检查8080端口
netstat -tunlp | grep 8080

# 检查6379端口
netstat -tunlp | grep 6379

# 如果被占用，修改config.yaml中的端口
```

---

## 成功标志

启动成功后应该看到：

```bash
$ docker ps
CONTAINER ID   IMAGE                   STATUS          PORTS     NAMES
xxx            zbaimo/nginx-firewall   Up 30 seconds             nginx-firewall
xxx            redis:7-alpine          Up 30 seconds             firewall-redis
```

```bash
$ docker logs nginx-firewall | grep "初始化"
✓ 已初始化 6 条默认威胁检测规则
✓ 已初始化 1 条默认自定义规则
```

```bash
$ docker logs nginx-firewall | grep "系统已启动"
🚀 系统已启动
```

---

**立即在服务器上执行**：

```bash
sudo systemctl start docker
sudo systemctl status docker
cd /root/data/firewall
docker compose -f docker-compose.deploy.yml up -d
```

