# Prismata 使用指南

## 安装

### 前提条件

- Python 3.10 或更高版本
- Node.js 14 或更高版本（用于 VSCode 扩展）
- Java 11 或更高版本（用于 JetBrains 插件）

### 安装核心 Agent

1. 克隆仓库：

```bash
git clone https://github.com/yourusername/prismata.git
cd prismata
```

2. 使用 uv 创建虚拟环境并安装依赖：

```bash
# 安装 uv (如果还没有安装)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 创建虚拟环境
uv venv
source .venv/bin/activate  # 在 Windows 上使用 .venv\Scripts\activate

# 安装依赖
uv pip install -r requirements.txt

# 安装开发依赖
uv pip install -r requirements-dev.txt
```

或者使用传统方式：

```bash
python -m venv venv
source venv/bin/activate  # 在 Windows 上使用 venv\Scripts\activate
pip install -e .
pip install -e ".[dev]"  # 安装开发依赖
```

### 安装 VSCode 扩展

1. 进入 VSCode 扩展目录：

```bash
cd vscode_extension
```

2. 安装依赖并构建扩展：

```bash
npm install
npm run compile
```

3. 将扩展链接到 VSCode：

```bash
# 在 VSCode 中按 F5 运行扩展
# 或者创建一个符号链接到 VSCode 扩展目录
```

## 运行

### 启动 Agent 服务

```bash
python main.py --host localhost --port 8765
```

### 在 VSCode 中使用

1. 打开 VSCode
2. 按 `Ctrl+Shift+P`（Windows/Linux）或 `Cmd+Shift+P`（macOS）打开命令面板
3. 输入 "Prismata" 查看可用命令：
   - `Prismata: Start Agent` - 启动 Agent 服务
   - `Prismata: Generate Code` - 生成代码
   - `Prismata: Analyze Code` - 分析代码

## 开发

### 使用 Makefile

我们提供了 Makefile 来简化常见的开发任务：

```bash
# 安装依赖
make setup

# 安装开发依赖
make setup-dev

# 运行 Agent 服务
make run

# 运行测试
make test

# 格式化代码
make format

# 代码检查
make lint

# 清理生成的文件
make clean
```

### 手动运行开发任务

#### 运行测试

```bash
# 使用 uv
uv pip run pytest

# 或者使用传统方式
pytest
```

#### 代码格式化

```bash
# 使用 uv
uv pip run black .
uv pip run isort .

# 或者使用传统方式
black .
isort .
```

#### 类型检查

```bash
# 使用 uv
uv pip run mypy .

# 或者使用传统方式
mypy .
```

## 项目结构

- `core_agent/` - 核心 AI agent 功能
- `communication/` - 通信层
- `shared/` - 共享模型和工具
- `vscode_extension/` - VSCode 插件
- `jetbrains_plugin/` - JetBrains 插件
- `tests/` - 测试套件
- `docs/` - 文档

## 配置

### VSCode 扩展配置

在 VSCode 设置中，可以配置以下选项：

- `prismata.agentPath` - Agent 可执行文件的路径
- `prismata.serverHost` - Agent 服务器主机
- `prismata.serverPort` - Agent 服务器端口
- `prismata.autoStart` - 是否在扩展激活时自动启动 Agent
