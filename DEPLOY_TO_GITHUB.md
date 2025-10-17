# 🚀 部署到GitHub和Docker Hub指南

## 📝 前提条件

- [x] 本地Git已安装
- [x] GitHub账号
- [x] Docker Hub账号

---

## 第一步：准备GitHub仓库

### 1. 创建GitHub仓库

访问：https://github.com/new

```
仓库名称: Firewall（或 nginx-firewall）
描述: Nginx日志智能防火墙系统
公开性: Public（推荐）或 Private
不要勾选: Initialize with README
```

点击 **Create repository**

### 2. 记录仓库地址

```
https://github.com/your-username/Firewall.git
```

---

## 第二步：修改配置文件

### 1. 修改Docker镜像名称

编辑文件：`.github/workflows/docker-build.yml`

**找到第9行**，将：
```yaml
DOCKER_IMAGE: your-dockerhub-username/nginx-firewall
```

改为：
```yaml
DOCKER_IMAGE: <你的Docker Hub用户名>/nginx-firewall
```

例如：`zhangsan/nginx-firewall`

### 2. 修改README徽章

编辑 `README.md` 顶部，将所有 `your-username` 替换为你的用户名

```markdown
[![Docker Build](https://github.com/<你的用户名>/Firewall/actions/workflows/docker-build.yml/badge.svg)]
[![Docker Pulls](https://img.shields.io/docker/pulls/<你的用户名>/nginx-firewall)]
```

---

## 第三步：推送到GitHub

### 在项目目录执行：

```bash
# 1. 初始化Git（如果还没有）
git init

# 2. 添加所有文件
git add .

# 3. 第一次提交
git commit -m "Initial commit: 完整的Nginx智能防火墙系统"

# 4. 设置主分支名称为main
git branch -M main

# 5. 添加远程仓库（替换为你的仓库地址）
git remote add origin https://github.com/your-username/Firewall.git

# 6. 推送到GitHub
git push -u origin main
```

### 如果推送需要认证：

```bash
# 使用个人访问令牌（推荐）
# 1. 访问 GitHub Settings → Developer settings → Personal access tokens
# 2. Generate new token (classic)
# 3. 勾选 repo 权限
# 4. 生成并复制token
# 5. 在推送时输入用户名和token（作为密码）
```

---

## 第四步：配置Docker Hub密钥

### 1. 创建Docker Hub访问令牌

1. 登录 https://hub.docker.com
2. 点击右上角头像 → **Account Settings**
3. 选择 **Security** → **New Access Token**
4. 名称：`github-actions`
5. 权限：`Read, Write, Delete`
6. 生成并**复制令牌**（只显示一次！）

### 2. 在GitHub添加Secrets

访问：`https://github.com/your-username/Firewall/settings/secrets/actions`

添加两个secrets：

**Secret 1: DOCKERHUB_USERNAME**
```
Name: DOCKERHUB_USERNAME
Value: 你的Docker Hub用户名
```

**Secret 2: DOCKERHUB_PASSWORD**
```
Name: DOCKERHUB_PASSWORD
Value: 刚才复制的Docker Hub访问令牌
```

---

## 第五步：触发自动构建

### 方法1：手动触发（推荐首次使用）

1. 访问：`https://github.com/your-username/Firewall/actions`
2. 选择 **Build and Push Docker Image**
3. 点击 **Run workflow**
4. 选择分支：`main`
5. 点击 **Run workflow** 按钮

### 方法2：推送代码自动触发

```bash
# 修改任何文件后
git add .
git commit -m "Update something"
git push
```

### 方法3：发布版本（推荐）⭐

```bash
# 创建版本标签 v1.0.0
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0
```

**会自动生成的镜像标签：**
- `v1.0.0` - 特定版本号（不变）
- `latest` - 最新稳定版本（自动更新）

**标签说明：**
- 推送代码到main分支 → 更新 `latest` 标签
- 创建v1.0.0标签 → 创建 `v1.0.0` 和更新 `latest`
- 推送到其他分支 → 创建分支名标签（如 `main`）

---

## 第六步：监控构建进度

### 查看构建状态

访问：`https://github.com/your-username/Firewall/actions`

**构建过程**（约5-10分钟）：
```
✓ Checkout代码
✓ 设置Docker Buildx
✓ 登录Docker Hub
✓ 提取元数据
⏳ 构建多架构镜像 (3-5分钟)
⏳ 推送到Docker Hub (2-3分钟)
✓ 生成摘要
```

### 构建成功标志

- Actions页面显示 ✅ 绿色对勾
- 收到GitHub邮件通知
- Docker Hub出现新镜像

---

## 第七步：验证部署

### 1. 访问Docker Hub

打开：`https://hub.docker.com/r/your-username/nginx-firewall`

应该看到：
- ✅ 镜像标签（latest, v1.0.0等）
- ✅ 最近更新时间
- ✅ 镜像大小（约500MB）
- ✅ 拉取次数

### 2. 测试拉取镜像

```bash
# 拉取镜像
docker pull your-username/nginx-firewall:latest

# 验证镜像
docker images | grep nginx-firewall

# 应该看到：
# your-username/nginx-firewall   latest   xxx   500MB
```

### 3. 运行容器

```bash
# 运行容器
docker run -d \
  --name test-firewall \
  -p 8080:8080 \
  your-username/nginx-firewall:latest

# 查看日志
docker logs -f test-firewall

# 访问Web界面
# 打开浏览器：http://localhost:8080
# 默认账户：admin/admin
```

### 4. 清理测试

```bash
docker stop test-firewall
docker rm test-firewall
```

---

## 🎉 完成！

现在你的项目已经：

✅ 托管在GitHub
✅ 自动CI/CD构建
✅ 自动发布到Docker Hub
✅ 任何人都可以使用：

```bash
docker pull your-username/nginx-firewall:latest
docker-compose up -d
```

---

## 📚 推荐的项目完善

### 1. 添加项目描述

编辑GitHub仓库页面：
- About → ⚙️ 编辑
- 添加描述和标签

建议描述：
```
智能Nginx日志防火墙系统 - 指纹识别、威胁评分、自动封禁、实时告警
```

建议标签：
```
nginx, firewall, security, python, docker, iptables, threat-detection
```

### 2. 创建Release

1. 访问：`https://github.com/your-username/Firewall/releases`
2. 点击 **Create a new release**
3. 选择标签：`v1.0.0`
4. 标题：`v1.0.0 - Initial Release`
5. 描述：复制 CHANGELOG.md 内容
6. 发布

### 3. 添加Star徽章

在README.md添加：
```markdown
⭐ 如果觉得有用，请给个Star！
```

---

## 🔄 日常维护

### 更新代码

```bash
# 1. 修改代码
vim core/something.py

# 2. 提交
git add .
git commit -m "Add: 新功能描述"
git push

# 3. 等待自动构建（5-10分钟）

# 4. 更新生产环境
docker-compose pull
docker-compose up -d
```

### 发布新版本

```bash
# 1. 更新CHANGELOG.md
# 2. 提交所有更改
git add .
git commit -m "Prepare v1.1.0 release"
git push

# 3. 创建标签
git tag -a v1.1.0 -m "Release v1.1.0"
git push origin v1.1.0

# 4. 创建GitHub Release（可选但推荐）
```

---

## ⚠️ 注意事项

### 1. 保护敏感信息

**不要提交到Git的文件：**
- ✗ `*.db` (数据库文件)
- ✗ `*.log` (日志文件)
- ✗ `config.yaml.local` (本地配置)
- ✗ `GeoLite2-City.mmdb` (大文件，用户自行下载)

已配置在 `.gitignore` 中

### 2. Secret管理

**GitHub Secrets 不会泄露：**
- ✓ 不会在日志中显示
- ✓ 只有仓库所有者可见
- ✓ 加密存储

### 3. 定期更新

```bash
# 更新依赖
pip install --upgrade -r requirements.txt

# 更新镜像
docker-compose pull
```

---

## 🆘 故障排查

### GitHub推送失败

```bash
# 问题：Permission denied
# 解决：使用HTTPS或配置SSH密钥

# 问题：rejected
# 解决：先pull再push
git pull origin main --rebase
git push
```

### Actions构建失败

**查看日志**：Actions → 点击失败的workflow → 查看详细日志

**常见问题**：
- Docker登录失败 → 检查Secrets
- 超时 → 重新运行
- 语法错误 → 本地测试后再推送

### Docker拉取失败

```bash
# 问题：镜像不存在
# 解决：检查Actions是否构建成功

# 问题：网络超时  
# 解决：配置镜像加速器
```

---

## 📊 成功指标

完成部署后应该达到：

- ✅ GitHub仓库有完整代码
- ✅ GitHub Actions构建成功（绿色✓）
- ✅ Docker Hub有最新镜像
- ✅ 可以成功拉取镜像
- ✅ 容器可以正常运行
- ✅ Web界面可以访问
- ✅ 登录功能正常（admin/admin → 强制修改密码）

---

## 🎊 恭喜！

你的项目现在是一个：
- ✅ 开源的
- ✅ 自动化的
- ✅ 容器化的
- ✅ 生产就绪的

**企业级安全防护系统！** 🛡️

---

需要帮助？查看详细指南：
- [GitHub + Docker 指南](docs/GITHUB_DOCKER_GUIDE.md)
- [Docker部署指南](DOCKER.md)
- [快速开始](QUICK_START.md)

