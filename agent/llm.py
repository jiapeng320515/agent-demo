"""LLM 客户端。

只依赖标准库 urllib，任何 OpenAI 兼容接口（DeepSeek/通义/智谱/MiniMax/OpenAI）都能用。
提供工厂函数 build_client()，各入口统一从这里构建客户端。
"""

__author__ = "Lucy"

import json
import urllib.error
import urllib.request

from . import config


class LLMError(Exception):
    """LLM 调用失败时抛出。"""


class OpenAICompatClient:
    """基于 OpenAI /chat/completions 兼容协议的客户端。"""

    def __init__(self, base_url: str, api_key: str, model: str):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model

    def chat(self, messages: list[dict], tools: list[dict] | None = None) -> dict:
        """发送一轮对话，返回 assistant 的 message（dict）。

        返回结构形如：
            {"content": "... 或 None", "tool_calls": [...] 或不存在}

        tools 参数为 OpenAI 兼容的工具调用能力预留；读书 agent 目前不传 tools，
        只做一轮「带检索上下文的问答」。
        """
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {"model": self.model, "messages": messages, "temperature": 0}
        if tools:
            payload["tools"] = tools

        req = urllib.request.Request(
            url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                body = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", "replace")
            raise LLMError(f"LLM 请求失败 (HTTP {e.code}): {detail[:300]}") from e
        except urllib.error.URLError as e:
            raise LLMError(f"网络错误: {e.reason}") from e

        return body["choices"][0]["message"]


def build_client() -> OpenAICompatClient | None:
    """构建真实 LLM 客户端；缺少 API key 时返回 None（由调用方决定降级策略）。

    把「如何构建客户端」集中在一处，各入口只负责「无 key 时怎么办」，
    避免在多个入口重复写构建逻辑。
    """
    if not config.API_KEY:
        return None
    return OpenAICompatClient(config.BASE_URL, config.API_KEY, config.MODEL)
