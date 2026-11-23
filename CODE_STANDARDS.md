# 代码规范（CODE STANDARDS）

> 本文档定义本项目所有代码的写作规范，新增 / 修改代码必须遵循。
> 与 PEP 8 冲突时，以本文档为准。

## 1. 语言与依赖

- Python ≥ 3.12，使用现代语法（类型标注、`match`、海象运算符按需）。
- **零第三方依赖优先**。确需引入时，在 `pyproject.toml` 声明，并说明「为什么标准库做不到」。
- 核心运行时保持零依赖；阶段二 / 三的可选依赖统一归入 `[project.optional-dependencies].rag` 与 `requirements-optional.txt`，**两处必须保持一致**。
- 环境要求、安装方式、密钥配置见 `ENVIRONMENT.md`；变更依赖须同步更新该文档与 `requirements*.txt`。
- 编码 UTF-8；缩进 4 空格（禁用 Tab）；行尾 LF。
- 入口模块（`*_main.py`）须兼容两种启动方式：`python -m 包.模块` 与「直接脚本运行」（IDEA 的 Run 按钮 / `python 包/模块.py`）。脚本方式下 `__package__` 为 `None` 会导致相对导入失败，须在相对导入前加 `if __package__ in (None, ""):` 补 `sys.path` 并声明 `__package__`（参考 `reader_main.py`）。

## 2. 命名规范

| 对象 | 规则 | 示例 |
|------|------|------|
| 模块 | 小写 + 下划线 | `reader.py`、`reader_main.py` |
| 函数/方法 | 小写 + 下划线，动词开头 | `load_book`、`chunk_text`、`build_index` |
| 私有函数 | 下划线前缀 | `_tokenize`、`_resolve`、`_get_int` |
| 常量 | 全大写 + 下划线 | `PROJECT_ROOT`、`MAX_STEPS`、`TOOLS` |
| 类 | 大驼峰 | `OpenAICompatClient`、`LLMError` |
| 变量 | 小写 + 下划线 | `query_set`、`top_k` |

## 3. 类型标注

- 所有**公共函数**必须有参数和返回值类型标注。
- 用现代写法：`list[str]`、`dict`、`Path | None`，不用 `typing.List` 等旧式写法。

## 4. 注释规范

- 每个模块顶部有 docstring，说明「做什么、为什么、局限」。
- 每个公共函数有 docstring：参数含义、返回值、关键设计决策。
- 复杂或有安全含义的逻辑，注释要写「为什么这么做」，而非复述「做了什么」。
- 每个模块 docstring 之后标注作者：`__author__ = "Lucy"`。

## 5. 错误处理

- 对外调用（LLM、文件、网络）必须 try/except，并给出可读的中文错误信息。
- 禁止裸 `except:`；至少 `except Exception` 且说明原因。
- 工具函数用**返回字符串错误信息**而非抛异常，让模型能读到错误并自我纠正。

## 6. 安全规范

- 禁止裸 `eval`；确需使用必须置空 `__builtins__` 并注释安全依据。
- 涉及文件访问时必须做路径越界检查。
- 密钥只从环境变量 / `.env` 读取，**绝不硬编码、绝不打印**。

## 7. 配置管理

- 所有配置项统一从 `config.py` 读取，禁止在业务代码里直接 `os.getenv`。
- 新增配置项三步：① `config.py` 定义 → ② `.env.example` 加注释示例 → ③ README 说明。
- 项目内文件 / 资源路径（书文件、数据文件）用相对路径时，须基于 `config.PROJECT_ROOT` 解析，禁止依赖 cwd。

## 8. 输出规范

- 用户可见输出用中文。
- 过程性输出用 `[标签]` 前缀（如 `[思考]` / `[动作]` / `[观察]` / `[检索]` / `[答案]`）。
- 不用 emoji。

## 9. 测试

- 核心纯函数（`chunk_text`、`_tokenize`、`retrieve`、`execute`）必须有测试。
- 优先标准库 `unittest` 或最小 `assert` 脚本（放 `tests/` 目录），保持零依赖。
- 改动检索 / 切块逻辑后，必须回归验证检索效果。

## 10. 文档同步

- 新增模块 / 工具 / 入口 → 同步更新 `ARCHITECTURE.md` 和 `README.md`。
- 修改环境变量 → 同步更新 `.env.example`。
