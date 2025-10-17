# 贡献指南

感谢您考虑为本项目做出贡献！

## 📝 如何贡献

### 报告Bug

如果您发现Bug，请创建Issue并包含：

1. Bug描述
2. 重现步骤
3. 预期行为
4. 实际行为
5. 系统环境（OS、Python版本等）
6. 相关日志

### 建议新功能

创建Issue并说明：

1. 功能描述
2. 使用场景
3. 预期效果
4. 可选的实现方案

### 提交代码

1. Fork本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 编写代码并测试
4. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
5. 推送到分支 (`git push origin feature/AmazingFeature`)
6. 开启Pull Request

## 💻 开发规范

### 代码风格

- 遵循PEP 8规范
- 使用4空格缩进
- 函数和类添加文档字符串
- 变量命名清晰明了

### 提交信息

```bash
# 格式
<type>: <description>

# 类型
feat: 新功能
fix: Bug修复
docs: 文档更新
style: 代码格式
refactor: 代码重构
perf: 性能优化
test: 测试相关
chore: 构建/工具更改

# 示例
feat: 添加Redis缓存支持
fix: 修复评分计算错误
docs: 更新Docker部署文档
```

### 测试要求

- 新功能需要添加测试
- 确保所有测试通过
- 不降低测试覆盖率

## 🔍 Pull Request检查清单

提交PR前请确认：

- [ ] 代码遵循项目规范
- [ ] 添加了必要的文档
- [ ] 添加了相关测试
- [ ] 所有测试通过
- [ ] CI检查全部通过
- [ ] 更新了CHANGELOG.md
- [ ] 没有引入breaking changes

## 📄 许可证

提交代码即表示您同意将代码以MIT许可证开源。

## 🙏 感谢

感谢所有贡献者！

