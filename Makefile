.PHONY: setup setup-dev run test format lint clean

# 使用 uv 安装依赖
setup:
	uv venv
	uv pip install -r requirements.txt

# 安装开发依赖
setup-dev: setup
	uv pip install -r requirements-dev.txt

# 运行 Agent 服务
run:
	python main.py

# 运行测试
test:
	uv pip run pytest

# 格式化代码
format:
	uv pip run black .
	uv pip run isort .

# 代码检查
lint:
	uv pip run ruff check .
	uv pip run mypy .

# 清理生成的文件
clean:
	rm -rf .venv
	rm -rf __pycache__
	rm -rf *.egg-info
	rm -rf dist
	rm -rf build
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
