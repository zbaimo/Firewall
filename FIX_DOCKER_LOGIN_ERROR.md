# 🔧 修复 Docker Login 错误

## ❌ 错误信息

```
Error: Username and password required
```

这个错误表示GitHub Actions无法找到Docker Hub的登录凭据。

---

## ✅ 解决方案（2分钟）

### 原因

GitHub Secrets `DOCKERHUB_USERNAME` 和 `DOCKERHUB_PASSWORD` 未配置或名称错误。

### 立即修复

#### Step 1: 访问Secrets页面

**将`<你的GitHub用户名>`替换后访问**：

```
https://github.com/<你的GitHub用户名>/Firewall/settings/secrets/actions
```

或手动导航：
1. 打开你的GitHub仓库
2. 点击 `Settings`（设置）
3. 左侧菜单：`Secrets and variables` → `Actions`

---

#### Step 2: 检查现有Secrets

在 "Repository secrets" 部分，检查是否有：

- `DOCKERHUB_USERNAME` ✓
- `DOCKERHUB_PASSWORD` ✓

**如果没有或名称不对**（如显示 DOCKER_USERNAME），需要删除并重新添加。

---

#### Step 3: 添加正确的Secrets

### 添加 DOCKERHUB_USERNAME

1. 点击 **`New repository secret`** 按钮
2. 填写：
   ```
   Name: DOCKERHUB_USERNAME
   ```
   **⚠️ 名称必须完全一致，区分大小写**

3. 填写：
   ```
   Secret: <你的Docker Hub用户名>
   ```
   **示例**：如果你的Docker Hub用户名是 `zhangsan`，就填 `zhangsan`

4. 点击 **`Add secret`**

---

### 添加 DOCKERHUB_PASSWORD

#### 3.1 获取Docker Hub访问令牌

1. 打开新标签页，访问：https://hub.docker.com
2. 登录你的Docker Hub账户
3. 点击右上角头像 → **Account Settings**
4. 左侧菜单选择 **Security**
5. 点击 **New Access Token** 按钮
6. 填写：
   ```
   Access Token Description: github-actions
   Access permissions: Read, Write, Delete
   ```
7. 点击 **Generate**
8. **立即复制显示的令牌**（只显示一次！）
   - 格式类似：`dckr_pat_abc123xyz...`

#### 3.2 添加到GitHub

回到GitHub的Secrets页面：

1. 点击 **`New repository secret`**
2. 填写：
   ```
   Name: DOCKERHUB_PASSWORD
   ```
   **⚠️ 名称必须完全一致**

3. 填写：
   ```
   Secret: <粘贴刚才复制的访问令牌>
   ```

4. 点击 **`Add secret`**

---

#### Step 4: 验证Secrets已添加

在Secrets页面，你应该看到：

```
Repository secrets

🔒 DOCKERHUB_USERNAME       Updated now
🔒 DOCKERHUB_PASSWORD       Updated now
```

**注意**：Secret的值不会显示（正常的安全机制）

---

#### Step 5: 重新运行workflow（30秒）

1. 访问：`https://github.com/<你的用户名>/Firewall/actions`

2. 找到失败的workflow（红色❌）

3. 点击进入

4. 点击右上角的 **`Re-run all jobs`** 按钮

或者手动触发新的运行：

1. 左侧点击：`Build and Push Docker Image`
2. 右侧点击：`Run workflow`
3. 选择：`main`
4. 点击：`Run workflow`

---

## 🎯 成功标志

workflow重新运行后，你应该看到：

```
✓ Checkout代码
✓ 设置Docker Buildx  
✓ 登录Docker Hub        ← 这一步应该成功（之前失败的）
⏳ 提取Docker元数据
⏳ 构建并推送Docker镜像
```

大约5-10分钟后，全部变成绿色✓

---

## 🔍 常见错误

### 错误1：Secret名称错误

❌ 错误的名称：
- `DOCKER_USERNAME`
- `DockerHub_Username`
- `dockerhub_username`

✅ 正确的名称（必须完全一致）：
- `DOCKERHUB_USERNAME`
- `DOCKERHUB_PASSWORD`

### 错误2：使用了密码而不是访问令牌

虽然可以使用密码，但**强烈建议使用访问令牌**：

- ✅ 访问令牌：`dckr_pat_...`（推荐）
- ⚠️ 账户密码：不推荐，可能失败

### 错误3：访问令牌权限不足

访问令牌必须有以下权限：
- ✅ Read
- ✅ Write
- ✅ Delete

如果权限不足，重新生成令牌。

---

## 📝 快速检查清单

在重新运行前，确认：

- [ ] Secret名称是 `DOCKERHUB_USERNAME`（不是DOCKER_USERNAME）
- [ ] Secret名称是 `DOCKERHUB_PASSWORD`（不是DOCKER_PASSWORD）
- [ ] DOCKERHUB_USERNAME 的值是你的Docker Hub用户名（不是邮箱）
- [ ] DOCKERHUB_PASSWORD 的值是访问令牌（不是密码）
- [ ] 访问令牌权限包含 Read, Write, Delete
- [ ] 两个Secrets都已保存

---

## 💡 验证Secrets是否正确

### 方法1：查看workflow日志

运行workflow后，点击 "登录Docker Hub" 步骤：

**如果Secrets正确**：
```
✓ 登录Docker Hub
  Run docker/login-action@v3
  Login Succeeded
```

**如果Secrets错误**：
```
❌ 登录Docker Hub
   Error: Username and password required
```

### 方法2：测试Secrets

可以添加一个测试step到workflow（临时）：

```yaml
- name: 测试Secrets
  run: |
    echo "Username length: ${#DOCKERHUB_USERNAME}"
    echo "Password length: ${#DOCKERHUB_PASSWORD}"
  env:
    DOCKERHUB_USERNAME: ${{ secrets.DOCKERHUB_USERNAME }}
    DOCKERHUB_PASSWORD: ${{ secrets.DOCKERHUB_PASSWORD }}
```

如果输出 `0`，说明Secret未配置。

---

## 🚀 完整操作流程

```
1. 访问 Settings → Secrets → Actions
   ↓
2. 删除错误的secrets（如果有）
   ↓
3. 点击 New repository secret
   ↓
4. Name: DOCKERHUB_USERNAME
   Secret: <你的用户名>
   ↓
5. Add secret
   ↓
6. 再次点击 New repository secret
   ↓
7. Name: DOCKERHUB_PASSWORD
   Secret: <访问令牌>
   ↓
8. Add secret
   ↓
9. 访问 Actions → Re-run all jobs
   ↓
10. 等待5-10分钟
   ↓
11. 成功！✓
```

---

## 📸 正确配置的样子

### Secrets页面应该显示：

```
┌─────────────────────────────────────────┐
│ Repository secrets                       │
├─────────────────────────────────────────┤
│                                          │
│ 🔒 DOCKERHUB_USERNAME   Updated now     │
│ 🔒 DOCKERHUB_PASSWORD   Updated now     │
│                                          │
│ [New repository secret]                 │
└─────────────────────────────────────────┘
```

### workflow日志应该显示：

```
Run docker/login-action@v3
Logging in to Docker Hub...
Login Succeeded ✓
```

---

## ⚠️ 重要提示

### Secret值的格式

**DOCKERHUB_USERNAME**：
```
正确：zhangsan
错误：zhangsan@email.com（不是邮箱）
错误：Zhang San（不要有空格）
```

**DOCKERHUB_PASSWORD**：
```
正确：dckr_pat_abc123xyz...（访问令牌）
可用：your-password（账户密码，不推荐）
错误：<你的访问令牌>（不要有尖括号）
```

---

## 🎊 成功后

配置正确后，workflow会：

1. ✅ 成功登录Docker Hub
2. ✅ 构建Docker镜像
3. ✅ 推送镜像到Docker Hub
4. ✅ 生成latest和v1.0.0标签

你就可以：
```bash
docker pull <你的用户名>/nginx-firewall:latest
```

---

**立即修复**：运行 `fix_actions.bat` 然后访问 Settings → Secrets → Actions 🚀

**详细文档**：[docs/GITHUB_SECRETS_SETUP.md](docs/GITHUB_SECRETS_SETUP.md)

