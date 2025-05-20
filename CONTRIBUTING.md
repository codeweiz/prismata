# 贡献指南

感谢您对 Prismata 项目的关注！我们欢迎各种形式的贡献，包括但不限于代码贡献、文档改进、问题报告和功能建议。

## 开发环境设置

1. 克隆仓库：

```bash
git clone https://github.com/yourusername/prismata.git
cd prismata
```

2. 使用 uv 设置开发环境：

```bash
# 安装依赖和开发工具
make setup-dev
```

## 开发工作流

我们使用基于功能分支的工作流：

1. 为您的工作创建一个新分支：

```bash
git checkout -b feature/your-feature-name
```

2. 进行更改并遵循代码风格指南

3. 运行测试和代码检查：

```bash
make test
make lint
```

4. 提交您的更改：

```bash
git commit -m "描述性的提交消息"
```

5. 推送到您的分支：

```bash
git push origin feature/your-feature-name
```

6. 创建一个 Pull Request

## 代码风格指南

我们使用以下工具来保持代码质量和一致性：

- **Black**: 用于 Python 代码格式化
- **isort**: 用于导入排序
- **mypy**: 用于类型检查
- **ruff**: 用于代码质量检查

在提交代码之前，请运行：

```bash
make format  # 格式化代码
make lint    # 检查代码质量
```

## 提交消息指南

请使用清晰、描述性的提交消息，遵循以下格式：

```
类型(范围): 简短描述

详细描述（如果需要）
```

类型可以是：
- **feat**: 新功能
- **fix**: 错误修复
- **docs**: 文档更改
- **style**: 不影响代码含义的更改（空格、格式等）
- **refactor**: 既不修复错误也不添加功能的代码更改
- **test**: 添加或修改测试
- **chore**: 对构建过程或辅助工具的更改

## 项目里程碑

请查看 [里程碑文档](docs/milestones.md) 了解项目的开发计划和当前状态。我们鼓励贡献者关注当前活跃里程碑中的任务。

## 问题和功能请求

如果您发现了问题或有功能建议，请创建一个 issue，并尽可能提供详细信息。

## 行为准则

请尊重所有项目参与者，保持专业和友好的交流环境。

## 许可证

通过贡献到本项目，您同意您的贡献将在项目的许可证下发布。
