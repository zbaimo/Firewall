@echo off
echo ============================================================
echo   修复 GitHub Actions
echo ============================================================
echo.

echo 正在重新推送.github目录...
echo.

git add .github/ -f
git add .
git commit -m "Enable GitHub Actions workflows"
git push origin main

echo.
echo ============================================================
echo   第1步完成: 代码已推送
echo ============================================================
echo.

echo 接下来请在浏览器中完成以下步骤:
echo.
echo 第2步: 启用Actions权限
echo ----------------------------------------
echo 1. 访问: https://github.com/你的用户名/Firewall/settings/actions
echo 2. 选择: Allow all actions and reusable workflows
echo 3. 选择: Read and write permissions
echo 4. 勾选: Allow GitHub Actions to create...
echo 5. 点击 Save
echo.

echo 第3步: 配置Secrets
echo ----------------------------------------
echo 1. 访问: https://github.com/你的用户名/Firewall/settings/secrets/actions
echo 2. 添加 DOCKERHUB_USERNAME (你的Docker Hub用户名)
echo 3. 添加 DOCKERHUB_PASSWORD (Docker Hub访问令牌)
echo.
echo    获取令牌: https://hub.docker.com
echo    头像 - Account Settings - Security - New Access Token
echo.

echo 第4步: 手动触发workflow
echo ----------------------------------------
echo 1. 访问: https://github.com/你的用户名/Firewall/actions
echo 2. 点击: Build and Push Docker Image
echo 3. 点击: Run workflow
echo 4. 选择: main 分支
echo 5. 点击: Run workflow (绿色按钮)
echo.

echo ============================================================
echo   详细步骤请查看: FIX_STEPS.txt
echo ============================================================
echo.

pause

