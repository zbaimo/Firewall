# 🔧 修复镜像名称错误

## ❌ 错误信息

```
ERROR: failed to push your-dockerhub-username/nginx-firewall:main: 
push access denied, repository does not exist or may require authorization
```

## 🎯 问题原因

`.github/workflows/docker-build.yml` 文件中的镜像名称还是默认值 `your-dockerhub-username`，需要改成你的实际Docker Hub用户名。

---

## ✅ 快速修复（1分钟）

### 方法1：使用修复脚本（最快）

我已经为您准备好了修复脚本，请告诉我：

**您的Docker Hub用户名是什么？**

然后我会为您生成修复命令。

### 方法2：手动修改

#### Step 1: 修改镜像名称

编辑文件：`.github/workflows/docker-build.yml`

找到第17行：
```yaml
DOCKER_IMAGE: your-dockerhub-username/nginx-firewall
```

修改为（替换为你的Docker Hub用户名）：
```yaml
DOCKER_IMAGE: <你的Docker Hub用户名>/nginx-firewall
```

**示例**：
- 如果你的Docker Hub用户名是 `zhangsan`
- 改为：`DOCKER_IMAGE: zhangsan/nginx-firewall`

#### Step 2: 提交并推送

```bash
git add .github/workflows/docker-build.yml
git commit -m "Fix Docker image name"
git push origin main
```

#### Step 3: 重新运行workflow

访问：https://github.com/zbaimo/Firewall/actions

1. 点击失败的workflow
2. 点击：`Re-run all jobs`

---

## 📝 完整步骤

### 如果您的Docker Hub用户名是：zhangsan

```bash
# 1. 修改文件（在文本编辑器中打开）
# .github/workflows/docker-build.yml 第17行
# 改为: DOCKER_IMAGE: zhangsan/nginx-firewall

# 2. 提交
git add .github/workflows/docker-build.yml
git commit -m "Fix: Update Docker image name to zhangsan/nginx-firewall"
git push origin main

# 3. 重新运行
# 访问 https://github.com/zbaimo/Firewall/actions
# 点击 Re-run all jobs
```

---

## 🔍 验证修改正确

修改后，文件应该类似：

```yaml
env:
  DOCKER_IMAGE: zhangsan/nginx-firewall  # 你的用户名
  DOCKER_PLATFORMS: linux/amd64,linux/arm64
  VERSION: v1.0.0
```

**确认**：
- ✅ 没有 `your-dockerhub-username`
- ✅ 是你的实际Docker Hub用户名
- ✅ 格式：`用户名/nginx-firewall`

---

## 💡 Docker Hub仓库说明

### 仓库会自动创建

**好消息**：当你第一次推送镜像时，Docker Hub会自动创建仓库！

**前提条件**：
- ✅ DOCKERHUB_USERNAME 和 DOCKERHUB_PASSWORD 配置正确
- ✅ 镜像名称格式正确
- ✅ 访问令牌有 Write 权限

### 或手动创建仓库（可选）

1. 访问：https://hub.docker.com/repositories
2. 点击：`Create Repository`
3. 填写：
   ```
   Repository Name: nginx-firewall
   Description: Nginx智能防火墙系统
   Visibility: Public
   ```
4. 点击：`Create`

---

## 🎯 修复后的效果

正确配置后，workflow会：

```
✓ Checkout代码
✓ 设置Docker Buildx
✓ 登录Docker Hub
✓ 提取Docker元数据
✓ 构建并推送Docker镜像到 <你的用户名>/nginx-firewall:latest
✓ 生成镜像摘要
```

---

## 📋 完整检查清单

在重新运行前，确认：

- [ ] `.github/workflows/docker-build.yml` 第17行已修改
- [ ] 镜像名称不包含 `your-dockerhub-username`
- [ ] 镜像名称格式：`<你的用户名>/nginx-firewall`
- [ ] DOCKERHUB_USERNAME Secret 已配置
- [ ] DOCKERHUB_PASSWORD Secret 已配置
- [ ] 访问令牌权限包含 Write

---

## 🚀 立即修复

**告诉我你的Docker Hub用户名，我帮你生成修复命令！**

或者按照以上步骤手动修改 `.github/workflows/docker-build.yml` 文件。

---

**修复完成后，重新运行workflow即可成功！** ✅

