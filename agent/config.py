"""配置加载：环境变量 + 极简 .env 解析（避免引入 python-dotenv 依赖）。"""

__author__ = "Lucy"

import os
from pathlib import Path

# 项目根目录：本文件位于 agent-demo/agent/ 下，向上两级即项目根目录。
# 用 __file__ 而不是 cwd，保证从任意目录运行都能正确定位 .env 与项目根。
PROJECT_ROOT = Path(__file__).resolve().parent.parent


def load_dotenv(path: Path | None = None) -> None:
    """极简 .env 加载器。

    规则：跳过空行与 # 注释；只加载尚未在环境中存在的键，
    这样 shell 里显式 export 的值优先级更高。
    """
    path = path or (PROJECT_ROOT / ".env")
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def _get_int(name: str, default: int) -> int:
    """读取整数环境变量，非法值回退到默认值（避免 int() 抛异常）。"""
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


# 在读取任何配置前先加载 .env，保证下面的默认值能被 .env 覆盖
load_dotenv()

# OpenAI 兼容接口配置：默认指向 DeepSeek，换通义/智谱/MiniMax/OpenAI 只需改这几个值
BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.deepseek.com")
API_KEY = os.getenv("OPENAI_API_KEY", "")
MODEL = os.getenv("LLM_MODEL", "deepseek-chat")
MAX_STEPS = _get_int("MAX_STEPS", 10)
