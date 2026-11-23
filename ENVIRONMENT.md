# 环境说明

本文档说明如何准备运行环境、安装依赖、配置密钥。**核心原则：阶段一（当前）零第三方依赖，`python` 直接能跑；只有进入阶段二 / 三才需要安装可选依赖。**

---

## 一、Python 版本要求

| 项目 | 要求 |
|------|------|
| 最低版本 | Python 3.12（代码用了 `Path \| None` 等新语法，需 3.10+，但统一按 3.12 收口） |
| 推荐版本 | **3.12.x**（与作者本地稳定版一致，见 `pyproject.toml` 的 `requires-python`） |

验证：

```bash
python --version        # 期望输出 Python 3.12.x
```

> 若本机没有 3.12，用 uv 一键装：`uv python install 3.12`。

---

## 二、依赖策略

| 文件 | 用途 | 何时安装 |
|------|------|---------|
| （核心） | 仅标准库，无任何第三方依赖 | 无需安装 |
| `requirements.txt` | 声明「核心零依赖」的说明文件 | 不需要装（`pip install` 为空是预期） |
| `requirements-optional.txt` | 阶段二 / 三的可选依赖 | 进入阶段二 / 三再装 |

阶段一直接运行即可，**不需要** `pip install` 或 `uv sync`：

```bash
python -m agent.reader_main --book books/sample.txt --inspect          # 看切块
python -m agent.reader_main --book books/sample.txt --demo -q "费曼学习法"  # 演示检索
```

---

## 三、安装方式（进入阶段二 / 三时才需要）

### 方式 A：uv（推荐，作者日常工具）

```bash
# 1. 确认 uv 已装（作者本机在 C:\Users\FF7Cloud\.local\bin）
uv --version

# 2. 锁定 Python 3.12
uv python pin 3.12

# 3. 安装可选依赖（等价于 pip install -r requirements-optional.txt）
uv sync --extra rag

# 4. 在 uv 管理的环境里运行
uv run python -m agent.reader_main --book books/sample.txt --inspect
```

### 方式 B：pip + venv（通用，任何机器可用）

```bash
# 1. 创建虚拟环境
python -m venv .venv

# 2. 激活（Windows Git Bash / 终端）
source .venv/Scripts/activate        # Windows
# source .venv/bin/activate          # macOS / Linux

# 3. 安装可选依赖（阶段二 / 三才需要）
pip install -r requirements-optional.txt
```

---

## 四、配置 LLM 密钥（`.env`）

阶段一演示（`--demo` / `--inspect`）**不需要密钥**，走检索演示或只看切块。要真实调用大模型时才需要：

```bash
# 1. 复制模板
cp .env.example .env

# 2. 编辑 .env，填入密钥（.env 不要提交到 git）
OPENAI_BASE_URL=https://api.deepseek.com
OPENAI_API_KEY=sk-你的密钥
LLM_MODEL=deepseek-chat
```

> `.env` 由 `config.py` 里的极简解析器加载，不依赖 python-dotenv。shell 里 `export` 的变量优先级更高。

---

## 五、换模型

任何 OpenAI 兼容接口都能用，改 `.env` 三个值即可：

| 服务 | OPENAI_BASE_URL | LLM_MODEL |
|------|-----------------|-----------|
| DeepSeek（默认） | https://api.deepseek.com | deepseek-chat |
| 通义千问 | https://dashscope.aliyuncs.com/compatible-mode/v1 | qwen-plus |
| 智谱 | https://open.bigmodel.cn/api/paas/v4 | glm-4-flash |
| MiniMax | https://api.minimax.chat/v1 | abab6.5s-chat |

---

## 六、验证环境正常

依次执行，全部不报错即环境就绪：

```bash
python --version                                              # 1. Python 版本
python -m agent.reader_main --book books/sample.txt --inspect  # 2. 读书切块
python -m agent.reader_main --book books/sample.txt --demo -q "费曼学习法"  # 3. 读书检索
```

---

## 七、依赖变更约定

- **新增运行时依赖**：必须同时更新 `pyproject.toml`（`dependencies` 或 `[project.optional-dependencies]`）与对应的 `requirements*.txt`，保持两份一致。
- **阶段二 / 三依赖**：统一归入 `rag` extra 与 `requirements-optional.txt`，不要塞进核心 `dependencies`，以免破坏「零依赖」的定位。
