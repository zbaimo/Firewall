# GitHub Secrets 配置指南

## 📋 需要配置的Secrets

为了让GitHub Actions自动构建并推送Docker镜像到Docker Hub，你需要配置以下两个secrets：

---

## 🔑 Secret 1: DOCKERHUB_USERNAME

### 获取方式
这就是你的Docker Hub用户名

### 配置步骤
1. 访问你的GitHub仓库
2. 点击 `Settings`（设置）
3. 左侧菜单选择 `Secrets and variables` → `Actions`
4. 点击 `New repository secret`
5. 填写：
   ```
   Name: DOCKERHUB_USERNAME
   Secret: <你的Docker Hub用户名>
   ```
6. 点击 `Add secret`

**示例**：
```
Name: DOCKERHUB_USERNAME
Secret: zhangsan
```

---

## 🔐 Secret 2: DOCKERHUB_PASSWORD

### 获取Docker Hub访问令牌（推荐）

**⚠️ 重要：使用访问令牌而不是密码更安全！**

#### 步骤1：创建访问令牌

1. 登录 https://hub.docker.com
2. 点击右上角头像 → `Account Settings`
3. 选择左侧菜单 `Security`
4. 点击 `New Access Token`
5. 填写：
   ```
   Access Token Description: github-actions
   Access Permissions: Read, Write, Delete
   ```
6. 点击 `Generate`
7. **立即复制令牌**（只显示一次！）

#### 步骤2：添加到GitHub Secrets

1. 回到GitHub仓库
2. `Settings` → `Secrets and variables` → `Actions`
3. 点击 `New repository secret`
4. 填写：
   ```
   Name: DOCKERHUB_PASSWORD
   Secret: <粘贴刚才复制的访问令牌>
   ```
5. 点击 `Add secret`

**示例**：
```
Name: DOCKERHUB_PASSWORD
Secret: dckr_pat_abc123xyz...（你的访问令牌）
```

---

## ✅ 验证配置

配置完成后，你应该在 Secrets 页面看到：

```
Repository secrets

DOCKERHUB_USERNAME       Updated X minutes ago
DOCKERHUB_PASSWORD       Updated X minutes ago
```

**注意**：
- ✅ Secret值不会显示（出于安全考虑）
- ✅ 只有仓库所有者可以查看
- ✅ 可以随时更新

---

## 🚀 触发构建

配置完Secrets后，可以触发构建：

### 方法1：手动触发

1. 访问：`Actions` 标签
2. 选择：`Build and Push Docker Image`
3. 点击：`Run workflow`
4. 选择分支：`main`
5. 点击：绿色的 `Run workflow` 按钮

### 方法2：推送代码

```bash
git add .
git commit -m "Update configuration"
git push
```

### 方法3：创建版本标签（推荐）

```bash
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0
```

---

## 📊 构建结果

构建成功后，你将看到：

### GitHub Actions
- ✅ 绿色对勾标志
- ✅ 构建日志显示成功

### Docker Hub
访问：https://hub.docker.com/r/<你的用户名>/nginx-firewall

你会看到：
- ✅ `latest` 标签
- ✅ `v1.0.0` 标签（如果创建了版本标签）
- ✅ 镜像大小（约500MB）
- ✅ 更新时间

---

## 🔍 故障排查

### 问题1：登录失败

**错误信息**：
```
Error: login failed
```

**可能原因**：
- ❌ DOCKERHUB_USERNAME 错误
- ❌ DOCKERHUB_PASSWORD 错误或过期
- ❌ 访问令牌权限不足

**解决方法**：
1. 重新检查用户名是否正确
2. 重新生成访问令牌
3. 确保令牌权限包含 `Read, Write, Delete`
4. 更新GitHub Secrets

### 问题2：推送失败

**错误信息**：
```
Error: denied: requested access to the resource is denied
```

**可能原因**：
- ❌ 仓库名称不匹配
- ❌ 仓库不存在
- ❌ 访问权限不足

**解决方法**：
1. 确认 `.github/workflows/docker-build.yml` 中的镜像名称正确
2. 确认Docker Hub仓库存在或设为public
3. 重新生成访问令牌并确保权限正确

### 问题3：构建超时

**错误信息**：
```
Error: build timeout
```

**解决方法**：
1. 重新运行workflow（通常是网络问题）
2. 检查Dockerfile是否有问题
3. 使用缓存加速（已配置）

---

## 📝 完整配置清单

在推送到GitHub前，确保已完成：

- [ ] 修改 `.github/workflows/docker-build.yml` 第17行的镜像名称
- [ ] 在GitHub添加 `DOCKERHUB_USERNAME` secret
- [ ] 在GitHub添加 `DOCKERHUB_PASSWORD` secret
- [ ] 推送代码到GitHub
- [ ] 触发GitHub Actions构建
- [ ] 验证Docker Hub有镜像

---

## 🎉 完成！

配置完成后，每次推送代码或创建标签，都会：

1. ✅ 自动运行CI测试
2. ✅ 自动构建Docker镜像
3. ✅ 自动推送到Docker Hub
4. ✅ 自动更新latest标签

**享受自动化的力量！** 🚀

---

## 💡 最佳实践

### 安全性
- ✅ 使用访问令牌而不是密码
- ✅ 定期轮换访问令牌
- ✅ 限制令牌权限

### 版本管理
- ✅ 使用语义化版本（v1.0.0）
- ✅ 创建GitHub Release
- ✅ 更新CHANGELOG.md

### 镜像标签
- ✅ `latest` 用于快速部署
- ✅ `v1.0.0` 用于生产环境
- ✅ `main` 用于开发测试

---

需要帮助？查看 [DEPLOY_TO_GITHUB.md](../DEPLOY_TO_GITHUB.md)

