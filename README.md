# 读书 Agent（RAG）

一个**零第三方依赖**的读书问答 agent，用标准库从零理解「检索增强生成（RAG）」的核心机制。不引入 LangChain / LangGraph / 任何 HTTP 库或向量库，`python` 直接能跑。

核心思想一句话：**一本书几十万字塞不进大模型上下文，所以不把整本书给它，而是每次只检索出「和问题最相关的几段」再喂给模型。**

## 目录结构

```
agent-demo/
├── agent/
│   ├── reader.py      # 核心：RAG 最小闭环（切块 / 检索 / 生成）
│   ├── reader_main.py # 命令行入口（--inspect / --demo / -q / 交互）
│   ├── llm.py         # 公共：OpenAI 兼容客户端 + 工厂函数 build_client()
│   └── config.py      # 公共：环境变量 + 极简 .env 解析
├── books/
│   └── sample.txt     # 示例书（用于演示）
├── pyproject.toml
├── requirements.txt           # 核心零依赖说明
├── requirements-optional.txt  # 阶段二 / 三可选依赖
├── .env.example
└── README.md
```

## 环境要求与安装

- **Python**：>= 3.12（推荐 3.12.x）
- **依赖**：核心运行时**零第三方依赖**（仅标准库），直接 `python -m` 即可跑，无需安装任何包；阶段二 / 三的可选依赖见 `requirements-optional.txt`
- 完整说明（uv / pip 两种安装方式、`.env` 配置、换模型）：见 **[ENVIRONMENT.md](./ENVIRONMENT.md)**

```bash
# 阶段一验证环境：无需安装任何东西
python --version
python -m agent.reader_main --book books/sample.txt --inspect
```

## 快速开始

```bash
# 只看切块结果（理解「切块」这一步）
python -m agent.reader_main --book books/sample.txt --inspect

# 演示检索（无 key 也能跑，不调用 LLM）
python -m agent.reader_main --book books/sample.txt --demo -q "番茄工作法是什么"

# 完整问答（复制 .env.example 为 .env，填入 OPENAI_API_KEY）
python -m agent.reader_main --book books/sample.txt -q "费曼学习法是什么"
```

---

## 一、RAG 流水线（当前实现）

### 它解决什么问题

一本书 10–50 万字，塞不进 LLM 上下文；即使塞得下，又贵又慢、还容易「中间遗忘」。所以**不把整本书给模型，而是每次只检索出和问题最相关的几段给模型**——这就是 RAG（检索增强生成）。

### 流水线

```
① 建索引（一次性）：
    书文件(txt) → 解析成文本 → 切块 → 预计算词元

② 问答（每次）：
    问题 → 关键词检索 → 拼提示词 → 大模型回答
```

对应代码：

| 步骤 | 函数 | 说明 |
|------|------|------|
| 读文件 | `reader.load_book()` | 读 txt（无排版干扰，阶段二再啃 PDF/EPUB） |
| 切块 | `reader.chunk_text()` | 固定字数 + 重叠切，400 字起步 |
| 建索引 | `reader.build_index()` | 切块 + 预计算每个块的词元 |
| 检索 | `reader.retrieve()` | 关键词 bigram 重叠打分，取 top_k |
| 拼提示词 | `reader.build_prompt()` | 段落 + 问题，并约束「只依据段落回答」 |
| 回答 | `reader.ask()` | 调 LLM 一轮问答 |

---

## 二、阶段规划

| 阶段 | 做什么 | 目标 |
|------|--------|------|
| **阶段一（当前）** | txt + 简单切分 + 关键词检索 | 跑通「切块→检索→生成」链路 |
| 阶段二 | PDF/EPUB 解析 + 中文 embedding + 向量库 | 检索变准，细节题也能答对 |
| 阶段三 | 把「列目录→定位→摘要」固化成多步流水线 | 实现「读目录→定位→总结」多步助手 |

### 已知局限（对应阶段二的改进）

- 关键词检索只按字面重叠，不理解同义词（"学习法" 匹配不到 "学习方法"）；
- 对「这本书讲了什么」这类全局问题效果差，答案散落全书，需要分层摘要（map-reduce）。

---

## 换模型

任何 OpenAI 兼容接口都能用，改 `.env` 三个值即可：

| 服务 | OPENAI_BASE_URL | LLM_MODEL |
|------|-----------------|-----------|
| DeepSeek（默认） | https://api.deepseek.com | deepseek-chat |
| 通义千问 | https://dashscope.aliyuncs.com/compatible-mode/v1 | qwen-plus |
| 智谱 | https://open.bigmodel.cn/api/paas/v4 | glm-4-flash |
| MiniMax | https://api.minimax.chat/v1 | abab6.5s-chat |

## 如何扩展

- **换检索**：只改 `reader.retrieve()` 里的打分函数，其余不动——阶段二换成向量相似度即可。
- **加新能力**：能力层新建模块（如 `summarizer.py`），入口层新建 CLI，复用 `llm.build_client()` + `config`。
- **上框架**：理解本项目的 RAG 后，迁移到向量库 / 编排框架只是换实现，接口和思路完全复用。

## 规范与架构

- **[ENVIRONMENT.md](./ENVIRONMENT.md)**：环境要求、依赖安装（uv / pip）、密钥配置。
- **[ARCHITECTURE.md](./ARCHITECTURE.md)**：分层架构、模块职责、演进路线（阶段二 / 三）。
- **[CODE_STANDARDS.md](./CODE_STANDARDS.md)**：代码规范，新增 / 修改代码必须遵循。
