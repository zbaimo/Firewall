# 🔧 GitHub Actions 故障排查指南

## 常见问题和解决方案

### ❓ 问题1：Actions标签页看不到任何workflow

**可能原因**：
- 代码还没有推送到GitHub
- 推送时`.github`目录没有包含进去
- GitHub仓库还没有创建

**解决方法**：

#### 步骤1：确认已推送到GitHub
```bash
# 检查远程仓库
git remote -v

# 如果没有，添加远程仓库
git remote add origin https://github.com/<你的用户名>/Firewall.git

# 推送所有内容（包括.github目录）
git add .
git add .github/  # 确保.github目录被包含
git commit -m "Add GitHub Actions workflows"
git push -u origin main
```

#### 步骤2：检查.github目录是否在Git中
```bash
# 查看Git跟踪的文件
git ls-files | findstr ".github"

# 应该看到：
# .github/workflows/docker-build.yml
# .github/workflows/ci.yml
# .github/ISSUE_TEMPLATE/bug_report.md
# .github/ISSUE_TEMPLATE/feature_request.md
# .github/PULL_REQUEST_TEMPLATE.md
```

#### 步骤3：强制添加.github目录
```bash
git add -f .github/
git commit -m "Add GitHub Actions configuration"
git push
```

---

### ❓ 问题2：Actions存在但没有运行

**可能原因**：
- Actions功能未启用
- 工作流权限未配置
- 触发条件不满足

**解决方法**：

#### 启用GitHub Actions

1. 访问GitHub仓库
2. 点击 `Settings`（设置）
3. 左侧菜单选择 `Actions` → `General`
4. 在 "Actions permissions" 部分，选择：
   ```
   ✓ Allow all actions and reusable workflows
   ```
5. 在 "Workflow permissions" 部分，选择：
   ```
   ✓ Read and write permissions
   ✓ Allow GitHub Actions to create and approve pull requests
   ```
6. 点击 `Save`

#### 手动触发workflow

1. 访问仓库的 `Actions` 标签
2. 选择 `Build and Push Docker Image`
3. 点击右侧的 `Run workflow` 按钮
4. 选择分支：`main`
5. 点击绿色的 `Run workflow` 按钮

---

### ❓ 问题3：workflow运行失败

**检查失败原因**：

1. 访问 `Actions` 标签
2. 点击失败的workflow（红色X）
3. 查看错误日志

**常见错误和解决：**

#### 错误A：Docker登录失败
```
Error: login failed
```

**原因**：Secrets未配置或配置错误

**解决**：
1. 访问 `Settings` → `Secrets and variables` → `Actions`
2. 确认有以下两个secrets：
   - `DOCKERHUB_USERNAME`
   - `DOCKERHUB_PASSWORD`
3. 如果没有，按照 [docs/GITHUB_SECRETS_SETUP.md](docs/GITHUB_SECRETS_SETUP.md) 配置
4. 如果有但失败，删除重新添加

#### 错误B：权限被拒绝
```
Error: denied: requested access to the resource is denied
```

**原因**：
- Docker Hub仓库不存在
- 镜像名称错误
- 访问令牌权限不足

**解决**：
1. 确认 `.github/workflows/docker-build.yml` 第17行的镜像名称正确
2. 访问 https://hub.docker.com 确认仓库存在
3. 重新生成访问令牌，确保权限包含 `Read, Write, Delete`

#### 错误C：YAML语法错误
```
Error: workflow syntax error
```

**解决**：
```bash
# 验证YAML语法
python -c "import yaml; yaml.safe_load(open('.github/workflows/docker-build.yml'))"
```

---

### ❓ 问题4：workflow不自动触发

**触发条件检查**：

我们的workflow会在以下情况自动触发：

1. **推送到main或master分支**
   ```bash
   git push origin main
   ```

2. **创建v开头的标签**
   ```bash
   git tag -a v1.0.0 -m "Release v1.0.0"
   git push origin v1.0.0
   ```

3. **创建Pull Request**

如果推送后没有触发：

1. 检查分支名称是否为 `main` 或 `master`
   ```bash
   git branch
   ```

2. 如果是其他分支，修改workflow文件或切换分支
   ```bash
   git checkout -b main
   git push -u origin main
   ```

---

## 🛠️ 完整修复步骤

如果Actions完全不工作，按以下步骤操作：

### 1. 确保.github目录已提交

```bash
# 查看Git状态
git status

# 添加.github目录（强制）
git add -f .github/workflows/
git add -f .github/ISSUE_TEMPLATE/
git add -f .github/PULL_REQUEST_TEMPLATE.md

# 提交
git commit -m "Add GitHub Actions workflows"

# 推送
git push origin main
```

### 2. 启用Actions权限

访问：`https://github.com/<你的用户名>/Firewall/settings/actions`

配置：
- ✅ Allow all actions and reusable workflows
- ✅ Read and write permissions
- ✅ Allow GitHub Actions to create and approve pull requests

### 3. 配置Secrets

访问：`https://github.com/<你的用户名>/Firewall/settings/secrets/actions`

添加：
```
DOCKERHUB_USERNAME = <你的Docker Hub用户名>
DOCKERHUB_PASSWORD = <你的Docker Hub访问令牌>
```

### 4. 手动触发第一次运行

访问：`https://github.com/<你的用户名>/Firewall/actions`

1. 点击 `Build and Push Docker Image`
2. 点击 `Run workflow`
3. 选择 `main` 分支
4. 点击绿色的 `Run workflow` 按钮

---

## 📋 验证Actions是否工作

### 检查清单

1. **仓库中存在.github目录**
   ```bash
   # 在GitHub网页查看
   https://github.com/<你的用户名>/Firewall/tree/main/.github/workflows
   ```
   应该能看到：
   - docker-build.yml
   - ci.yml

2. **Actions标签可见**
   - 访问仓库的 `Actions` 标签
   - 应该能看到两个workflow：
     - Build and Push Docker Image
     - CI Tests

3. **可以手动触发**
   - 点击workflow
   - 右侧有 `Run workflow` 按钮

4. **运行历史**
   - 推送代码后，Actions会自动运行
   - 在Actions标签下可以看到运行历史

---

## 🔍 调试技巧

### 查看workflow文件是否被识别

访问：
```
https://github.com/<你的用户名>/Firewall/blob/main/.github/workflows/docker-build.yml
```

如果404错误 → 文件未推送

### 查看Actions权限

访问：
```
https://github.com/<你的用户名>/Firewall/settings/actions
```

确保启用了所有权限

### 查看workflow运行日志

1. 访问 `Actions` 标签
2. 点击任意workflow运行
3. 点击 `build-and-push` job
4. 查看详细日志

### 测试触发条件

```bash
# 测试推送触发
echo "test" >> README.md
git add README.md
git commit -m "Test Actions trigger"
git push

# 几秒钟后，访问Actions标签，应该看到新的运行
```

---

## 💡 快速解决方案

### 方案1：重新推送（最简单）

```bash
# 删除远程仓库（如果已创建）
# 然后重新推送所有内容

git add .
git add .github/ -f
git commit -m "Complete project with GitHub Actions"
git push -f origin main
```

### 方案2：创建新的workflow文件

如果问题仍然存在，可以在GitHub网页创建：

1. 访问仓库
2. 点击 `Actions` 标签
3. 点击 `New workflow`
4. 选择 `set up a workflow yourself`
5. 复制 `.github/workflows/docker-build.yml` 的内容
6. 粘贴并提交

### 方案3：检查仓库设置

确保仓库不是private且没有限制Actions：

1. `Settings` → `General`
2. 滚动到 "Danger Zone"
3. 确认仓库为Public或Actions已启用

---

## ✅ 成功标志

当一切正常时，你应该看到：

1. **Actions标签页**
   - 有两个workflow列表
   - 可以点击查看

2. **自动运行**
   - 推送代码后自动触发
   - 几秒钟内出现在运行历史中

3. **运行成功**
   - 绿色✓标志
   - 构建日志正常
   - Docker Hub出现镜像

---

## 🆘 仍然不工作？

### 创建测试workflow

创建一个简单的测试workflow来验证Actions是否可用：

**文件**: `.github/workflows/test.yml`
```yaml
name: Test Workflow

on:
  push:
  workflow_dispatch:

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - name: Echo test
        run: echo "GitHub Actions is working!"
```

推送后，如果这个都不运行，说明Actions未启用或权限问题。

### 联系支持

如果所有方法都试过还是不行：

1. 检查GitHub状态：https://www.githubstatus.com/
2. 查看GitHub文档：https://docs.github.com/actions
3. 提交GitHub Support ticket

---

## 📝 推荐流程

### 首次部署最稳妥的方法：

1. **确保代码在本地能运行**
   ```bash
   python validate.py
   ```

2. **推送到GitHub**
   ```bash
   git add .
   git add .github/ -f
   git commit -m "Initial commit with Actions"
   git push -u origin main
   ```

3. **立即访问Actions标签**
   ```
   https://github.com/<你的用户名>/Firewall/actions
   ```

4. **启用Actions权限**（如果需要）
   ```
   Settings → Actions → General
   允许所有Actions
   ```

5. **配置Secrets**
   ```
   Settings → Secrets → Actions
   添加 DOCKERHUB_USERNAME
   添加 DOCKERHUB_PASSWORD
   ```

6. **手动触发第一次运行**
   ```
   Actions → Build and Push → Run workflow
   ```

7. **查看运行日志**
   - 点击运行中的workflow
   - 查看详细步骤
   - 等待完成（5-10分钟）

---

## 🎯 快速诊断命令

```bash
# 检查.github目录
ls -la .github/workflows/

# 检查Git状态
git status

# 检查远程仓库
git remote -v

# 验证YAML语法
python -c "import yaml; yaml.safe_load(open('.github/workflows/docker-build.yml'))"

# 查看Git跟踪的.github文件
git ls-files .github/
```

---

**遇到问题？查看详细日志，90%的问题都是配置或权限问题！** 🔍

