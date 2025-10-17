# 🚀 启用GitHub Actions - 详细步骤

## 问题：GitHub Actions没有工作

如果你发现Actions标签页是空的，或者workflow没有运行，按照以下步骤操作：

---

## ✅ 解决方案（5分钟）

### 第1步：确保.github目录已推送

```bash
# 检查.github目录是否在Git中
git ls-files | findstr ".github"

# 如果没有输出，执行：
git add .github/ -f
git add .
git commit -m "Add GitHub Actions workflows"
git push origin main
```

**Windows PowerShell版本**：
```powershell
# 检查
git ls-files | Select-String ".github"

# 添加
git add .github/ -f
git add .
git commit -m "Add GitHub Actions workflows"
git push origin main
```

---

### 第2步：在GitHub启用Actions

#### 2.1 访问仓库设置

```
https://github.com/<你的用户名>/Firewall/settings/actions
```

#### 2.2 配置Actions权限

在 **"Actions permissions"** 部分：

**选择**：
```
⚪ Disable Actions
⚪ Allow <你的用户名>, and select non-<你的用户名>, actions and reusable workflows
🔘 Allow all actions and reusable workflows  ← 选择这个
```

在 **"Workflow permissions"** 部分：

**选择**：
```
🔘 Read and write permissions  ← 选择这个
☑️ Allow GitHub Actions to create and approve pull requests  ← 勾选这个
```

#### 2.3 保存设置

点击页面底部的 **`Save`** 按钮

---

### 第3步：验证Actions已启用

#### 3.1 访问Actions标签

```
https://github.com/<你的用户名>/Firewall/actions
```

你应该看到：

```
All workflows

🔨 Build and Push Docker Image
🧪 CI Tests
```

#### 3.2 如果看不到workflow

**可能的问题**：
- `.github/workflows/` 目录不在main分支
- 文件名或路径错误
- YAML语法错误

**解决**：

在GitHub网页查看文件是否存在：
```
https://github.com/<你的用户名>/Firewall/tree/main/.github/workflows
```

应该看到：
- `docker-build.yml` ✓
- `ci.yml` ✓

如果没有，重新推送：
```bash
git add .github/workflows/*.yml -f
git commit -m "Re-add workflows"
git push
```

---

### 第4步：配置Docker Hub Secrets

#### 4.1 访问Secrets页面

```
https://github.com/<你的用户名>/Firewall/settings/secrets/actions
```

#### 4.2 添加第一个Secret

点击 **`New repository secret`**

```
Name: DOCKERHUB_USERNAME
Secret: <你的Docker Hub用户名>
```

点击 **`Add secret`**

#### 4.3 添加第二个Secret

再次点击 **`New repository secret`**

```
Name: DOCKERHUB_PASSWORD
Secret: <你的Docker Hub访问令牌>
```

**如何获取访问令牌**：
1. 登录 https://hub.docker.com
2. 头像 → Account Settings → Security
3. New Access Token
4. Description: `github-actions`
5. Permissions: `Read, Write, Delete`
6. Generate → 复制令牌

点击 **`Add secret`**

#### 4.4 验证Secrets

你应该看到两个secrets：
```
Repository secrets

📦 DOCKERHUB_USERNAME       Updated now
📦 DOCKERHUB_PASSWORD       Updated now
```

---

### 第5步：手动触发workflow

#### 5.1 访问Actions

```
https://github.com/<你的用户名>/Firewall/actions
```

#### 5.2 选择workflow

点击左侧的 **`Build and Push Docker Image`**

#### 5.3 运行workflow

1. 右侧会出现 **`Run workflow`** 按钮（灰色下拉按钮）
2. 点击它
3. 在弹出的对话框中：
   - Use workflow from: `Branch: main`
4. 点击绿色的 **`Run workflow`** 按钮

#### 5.4 查看运行状态

- 几秒钟后，页面会刷新
- 你会看到一个黄色圆点 🟡（运行中）
- 点击它查看详细日志
- 等待5-10分钟
- 成功后变成绿色✓

---

### 第6步：验证构建成功

#### 6.1 检查Actions状态

在Actions页面应该看到绿色✓：
```
✓ Build and Push Docker Image
  #1: <你的提交信息>
  main
  Completed in 8m 32s
```

#### 6.2 检查Docker Hub

访问：`https://hub.docker.com/r/<你的用户名>/nginx-firewall/tags`

应该看到：
- ✅ `latest` 标签
- ✅ `main` 标签
- ✅ 镜像大小：约500MB
- ✅ 更新时间：几分钟前

#### 6.3 测试拉取镜像

```bash
docker pull <你的用户名>/nginx-firewall:latest
```

应该成功下载镜像

---

## 🎯 成功标准

全部完成后，你应该：

- ✅ Actions标签页有workflow列表
- ✅ 可以手动运行workflow
- ✅ 推送代码自动触发构建
- ✅ 构建成功（绿色✓）
- ✅ Docker Hub有镜像
- ✅ 可以拉取镜像

---

## 📸 截图参考

### Actions标签页应该看起来像：

```
┌─────────────────────────────────────────┐
│ Actions                                  │
├─────────────────────────────────────────┤
│                                          │
│ All workflows                            │
│                                          │
│ 🔨 Build and Push Docker Image          │
│ 🧪 CI Tests                             │
│                                          │
│ ┌─────────────────────────────────────┐│
│ │ ✓ Build and Push Docker Image       ││
│ │   #1: Initial commit                ││
│ │   main                              ││
│ │   Completed in 8m 32s               ││
│ └─────────────────────────────────────┘│
└─────────────────────────────────────────┘
```

### Settings → Actions应该看起来像：

```
Actions permissions
⚪ Disable Actions
⚪ Allow <user>, and select non-<user>...
🔘 Allow all actions and reusable workflows  ← 选中

Workflow permissions
🔘 Read and write permissions  ← 选中
☑️ Allow GitHub Actions to create...  ← 勾选
```

---

## 🆘 快速帮助

### 如果看不到Actions标签

1. 确认仓库是public或Actions已启用（private仓库）
2. 检查Settings → Actions是否被禁用

### 如果workflow不运行

1. 检查分支名称（必须是main或master）
2. 检查.github/workflows/目录是否存在
3. 手动触发一次

### 如果构建失败

1. 查看详细日志
2. 检查Secrets是否正确
3. 检查镜像名称是否正确

---

## 📞 需要帮助？

- 📖 详细文档：[DEPLOY_TO_GITHUB.md](DEPLOY_TO_GITHUB.md)
- 🔑 Secrets配置：[docs/GITHUB_SECRETS_SETUP.md](docs/GITHUB_SECRETS_SETUP.md)
- 📋 配置模板：[SECRETS_TEMPLATE.txt](SECRETS_TEMPLATE.txt)
- 🐛 提交Issue：GitHub Issues

---

**记住**：90%的Actions问题都是以下原因：
1. `.github`目录未推送
2. Actions权限未启用
3. Secrets未配置或配置错误

**按照本指南逐步检查，一定能解决！** ✅

