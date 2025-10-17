# ⚡ 快速部署指南（5分钟）

## 🎯 目标

将项目推送到GitHub并自动构建Docker镜像发布到Docker Hub

---

## 📝 准备工作（3个账户）

1. ✅ GitHub账户
2. ✅ Docker Hub账户  
3. ✅ 本地已安装Git

---

## 🚀 步骤1：修改配置（1分钟）

### 必须修改的文件

**文件1: `.github/workflows/docker-build.yml`**

找到第17行，修改：
```yaml
DOCKER_IMAGE: your-dockerhub-username/nginx-firewall
```
改为：
```yaml
DOCKER_IMAGE: zhangsan/nginx-firewall  # 你的Docker Hub用户名
```

**文件2: `README.md`**

用文本编辑器打开，全局替换：
- `your-username` → 你的GitHub用户名
- 保存文件

---

## 🚀 步骤2：推送到GitHub（1分钟）

### Windows系统

双击运行：
```
push_to_github.bat
```

然后按提示输入你的GitHub用户名

### Linux/macOS系统

在终端执行：
```bash
chmod +x push_to_github.sh
./push_to_github.sh
```

### 或者手动推送

```bash
git init
git add .
git commit -m "Initial commit: v1.0.0"
git branch -M main
git remote add origin https://github.com/<你的用户名>/Firewall.git
git push -u origin main
```

---

## 🚀 步骤3：配置Docker Hub Secrets（2分钟）

### 3.1 获取Docker Hub访问令牌

1. 登录 https://hub.docker.com
2. 点击右上角头像 → **Account Settings**
3. 左侧选择 **Security**
4. 点击 **New Access Token**
5. 填写：
   - Description: `github-actions`
   - Permissions: `Read, Write, Delete`
6. 点击 **Generate**
7. **复制令牌**（只显示一次！记得保存）

### 3.2 在GitHub添加Secrets

1. 访问你的GitHub仓库
2. 点击 `Settings`（设置）
3. 左侧菜单：`Secrets and variables` → `Actions`
4. 点击 `New repository secret`

**添加Secret 1:**
```
Name: DOCKERHUB_USERNAME
Secret: <你的Docker Hub用户名>
```
点击 `Add secret`

**添加Secret 2:**
```
Name: DOCKERHUB_PASSWORD  
Secret: <粘贴刚才复制的访问令牌>
```
点击 `Add secret`

**验证**：你应该看到两个secrets：
```
DOCKERHUB_USERNAME ✓
DOCKERHUB_PASSWORD ✓
```

---

## 🚀 步骤4：触发构建（1分钟）

### 方式1：创建版本标签（推荐）⭐

```bash
# 创建v1.0.0版本标签
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0
```

**结果**：
- 自动构建并推送 `v1.0.0` 标签
- 自动更新 `latest` 标签

### 方式2：手动触发

1. 访问仓库的 `Actions` 标签
2. 选择 `Build and Push Docker Image`
3. 点击 `Run workflow`
4. 选择 `main` 分支
5. 点击绿色的 `Run workflow` 按钮

---

## 📊 步骤5：监控构建（5-10分钟）

### 查看构建进度

1. 访问：`Actions` 标签
2. 点击最新的workflow运行
3. 查看实时日志

**构建过程**：
```
✓ Checkout代码
✓ 设置Docker Buildx
✓ 登录Docker Hub
✓ 提取元数据
⏳ 构建镜像（3-5分钟）
⏳ 推送到Docker Hub（2-3分钟）
✓ 生成摘要
```

**总耗时**: 约5-10分钟

### 成功标志

- ✅ GitHub Actions页面显示绿色✓
- ✅ 收到GitHub邮件通知（如果启用）
- ✅ Docker Hub出现新镜像

---

## ✅ 步骤6：验证部署（1分钟）

### 6.1 检查Docker Hub

访问：`https://hub.docker.com/r/<你的用户名>/nginx-firewall/tags`

应该看到：
- ✅ `latest` 标签
- ✅ `v1.0.0` 标签（如果创建了版本标签）
- ✅ 镜像大小：约500MB
- ✅ 更新时间：刚刚

### 6.2 拉取并测试镜像

```bash
# 拉取镜像
docker pull <你的用户名>/nginx-firewall:latest

# 运行测试
docker run --rm \
  -p 8080:8080 \
  <你的用户名>/nginx-firewall:latest \
  python -c "print('Container works!')"

# 完整运行
docker-compose up -d

# 查看日志
docker-compose logs -f

# 访问Web界面
# http://localhost:8080
# 登录: admin / admin
```

---

## 🎊 完成！

现在你的项目已经：

✅ 托管在GitHub  
✅ 自动CI/CD构建  
✅ 自动发布到Docker Hub  
✅ 任何人都可以使用：

```bash
docker pull <你的用户名>/nginx-firewall:latest
docker-compose up -d
```

---

## 📋 完整时间估算

| 步骤 | 耗时 | 说明 |
|-----|------|------|
| 修改配置 | 1分钟 | 改镜像名称 |
| 推送GitHub | 1分钟 | 运行脚本 |
| 配置Secrets | 2分钟 | Docker Hub令牌 |
| 触发构建 | 1分钟 | 创建标签 |
| 等待构建 | 5-10分钟 | 自动进行 |
| 验证测试 | 1分钟 | 拉取测试 |
| **总计** | **10-15分钟** | **全自动化** |

---

## 🔄 后续更新流程

### 日常更新（只需1分钟）

```bash
# 1. 修改代码
# 2. 提交推送
git add .
git commit -m "Add new feature"
git push

# 3. 等待自动构建（5-10分钟）
# 4. latest标签自动更新
```

### 版本发布（只需2分钟）

```bash
# 1. 更新CHANGELOG.md
# 2. 创建版本标签
git tag -a v1.1.0 -m "Release v1.1.0"
git push origin v1.1.0

# 3. 自动构建 v1.1.0 和 latest
# 4. 创建GitHub Release（可选）
```

---

## 🆘 需要帮助？

- 📖 详细配置：[docs/GITHUB_SECRETS_SETUP.md](docs/GITHUB_SECRETS_SETUP.md)
- 📖 完整指南：[DEPLOY_TO_GITHUB.md](DEPLOY_TO_GITHUB.md)
- 🐛 遇到问题：提交GitHub Issue

---

## 🎯 快速链接

- GitHub仓库：`https://github.com/<你的用户名>/Firewall`
- Docker Hub：`https://hub.docker.com/r/<你的用户名>/nginx-firewall`
- Actions页面：`https://github.com/<你的用户名>/Firewall/actions`

---

**现在就开始吧！只需10分钟！** ⚡

