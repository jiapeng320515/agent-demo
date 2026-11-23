"""读书 agent —— 阶段一：RAG 最小闭环（关键词检索，暂不向量化）。

本阶段目标：把「读书问答」这条链路先跑通，理解 RAG（检索增强生成）的骨架。
刻意不引入 embedding / 向量库，用最简单的「关键词重叠打分」来做检索。

对照 README 中的 RAG 流水线，本文件对应两段：

    ① 建索引（一次性）：
        书文件(txt) -> 读成文本(load_book) -> 切块(chunk_text/build_index)
        -> 预计算每个块的词元(_tokenize)

    ② 问答（每次）：
        问题 -> 关键词检索(retrieve) -> 拼提示词(build_prompt) -> 大模型回答(ask)

为什么阶段一先用「关键词检索」，而不是直接上向量化？
    1. 先验证「切块 + 检索 + 生成」整条链路能跑通，再谈优化；
    2. 关键词检索零依赖、结果可解释，你能清楚看到「它到底找对了没有」；
    3. 阶段二只需把 retrieve() 里的打分函数换成「向量相似度」，接口不变，其余代码基本不动。

已知局限（对应阶段二的改进方向）：
    - 只按字面重叠匹配，不理解同义词（"学习法" 匹配不到 "学习方法"）；
    - 对「这本书讲了什么」这类全局问题效果差，因为答案散落在全书各处。
"""

from __future__ import annotations

__author__ = "Lucy"

import re
from pathlib import Path

from . import config


# ==================== ① 建索引（一次性） ====================

def load_book(path: str | Path) -> str:
    """读取一本 txt 书，返回整本书的纯文本。

    为什么从 txt 起步：txt 没有排版干扰（双栏、表格、脚注、换页），
    解析零成本，能让你把精力集中在「检索」这个核心上。
    PDF / EPUB 的解析属于「脏活」，留到阶段二。

    相对路径统一基于项目根目录（PROJECT_ROOT）解析，而不是依赖当前工作目录（cwd）：
    否则从 IDEA 直接 Run（working directory 未必是项目根）时会找不到 books/ 下的书。
    """
    p = Path(path)
    if not p.is_absolute():
        p = config.PROJECT_ROOT / p
    return p.read_text(encoding="utf-8", errors="replace")


def chunk_text(text: str, chunk_size: int = 400, overlap: int = 80) -> list[str]:
    """把一整本书切成若干「块」（chunk）。

    切块是 RAG 里最影响效果的一步，两个参数的含义：
    - chunk_size：每块最多多少字。太大 -> 检索到的块很杂、命中不准；
      太小 -> 一句话被切碎、上下文丢失。400 字是常见的起步值。
    - overlap：相邻两块重叠多少字。目的是避免一句话正好被切在两块之间，
      导致「前半句在块 A、后半句在块 B」，检索时都找不全。

    阶段一先按「固定字数 + 重叠」切（简单、可控）；
    阶段二会改成「按章节标题切」，语义更完整。
    """
    chunks: list[str] = []
    start = 0
    total = len(text)
    while start < total:
        end = min(start + chunk_size, total)
        piece = text[start:end].strip()
        if piece:
            chunks.append(piece)
        if end >= total:
            break
        # 下一块从「end - overlap」开始，制造重叠（chunk_size > overlap 保证向前推进）
        start = end - overlap
    return chunks


def _tokenize(text: str) -> list[str]:
    """把一段文本切成「检索用的最小单位」（词元）。

    中文没有天然空格分词，这里用一个零依赖技巧：字符 bigram（二字词）。
    例："费曼学习法" -> ["费曼", "曼学", "学习", "习法"]
    好处是：即使用户只输入"费曼"，也能和"费曼学习法"匹配上。

    英文和数字则按单词切（用正则按非字母数字分隔）。
    分词是阶段二换向量化时也会用到的关键预处理。
    """
    tokens: list[str] = []
    # 把文本拆成「连续中文」和「英文/数字」两类片段
    for part in re.findall(r"[\u4e00-\u9fff]+|[A-Za-z0-9]+", text.lower()):
        if re.match(r"[\u4e00-\u9fff]", part):
            # 中文片段：切成相邻二字组合（bigram）
            tokens += [part[i:i + 2] for i in range(len(part) - 1)]
        else:
            tokens.append(part)
    return tokens


def build_index(text: str, chunk_size: int = 400, overlap: int = 80) -> dict:
    """建索引：切块 + 预计算每块的词元。

    返回结构：
        {
            "chunks": ["第一块原文", "第二块原文", ...],
            "tokens": [["块1词元"], ["块2词元"], ...],
        }

    为什么要预计算 tokens？因为检索会反复进行，如果每次都重新切词会浪费算力。
    「建索引只做一次、检索复用」正是 RAG 的核心思想。
    """
    chunks = chunk_text(text, chunk_size, overlap)
    tokens = [_tokenize(c) for c in chunks]
    return {"chunks": chunks, "tokens": tokens}


# ==================== ② 问答（每次） ====================

def retrieve(index: dict, query: str, top_k: int = 3) -> list[str]:
    """从所有块里，挑出和问题最相关的 top_k 块（关键词打分）。

    打分方式：把问题的词元做成集合，看每个块「命中了问题里的多少个词元」，
    命中越多越相关。这是最简单、可解释的检索。

    阶段二会把这里换成「向量余弦相似度」，接口保持不变：
    输入 index + query + top_k，输出最相关的几段原文。
    """
    query_set = set(_tokenize(query))
    if not query_set:
        return []

    scored: list[tuple[int, int]] = []
    for i, chunk_tokens in enumerate(index["tokens"]):
        score = sum(1 for t in chunk_tokens if t in query_set)
        scored.append((score, i))

    scored.sort(key=lambda x: x[0], reverse=True)
    # 只保留「确有命中（分数 > 0）」的块，避免把毫不相关的段落喂给模型
    hits = [index["chunks"][i] for score, i in scored if score > 0][:top_k]
    return hits


def build_prompt(hits: list[str], query: str) -> str:
    """把检索到的段落 + 问题，拼成给大模型的提示词。

    这里有一条读书 agent 的关键纪律：明确要求模型「只能依据段落回答、
    不知道就直说」，否则模型会凭记忆脑补，检索就白做了。
    """
    context = "\n\n---\n\n".join(
        f"[段落{i + 1}]\n{hit}" for i, hit in enumerate(hits)
    )
    return (
        "你是一个严谨的读书助手，只能根据下面提供的书中段落回答问题，"
        "不要编造书中没有的内容；如果段落里没有相关信息，请明确说「书中未提及」。\n\n"
        f"=== 书中相关段落 ===\n{context}\n=== 段落结束 ===\n\n"
        f"问题：{query}"
    )


def ask(client, index: dict, query: str, top_k: int = 3, verbose: bool = True) -> str:
    """一次完整的读书问答：检索 -> 拼提示词 -> 调大模型 -> 返回答案。

    client 复用 agent/llm.py 里的 OpenAICompatClient，不做工具调用，
    只做一轮「带检索上下文的问答」。
    """
    hits = retrieve(index, query, top_k)
    if verbose:
        print(f"[检索] 「{query}」命中 {len(hits)} 段")
    if not hits:
        return "（没有检索到相关段落：问题可能太宽泛，或书中确实没有）"

    prompt = build_prompt(hits, query)
    message = client.chat(
        [
            {"role": "system", "content": "你是严谨的读书助手。"},
            {"role": "user", "content": prompt},
        ]
    )
    return (message.get("content") or "").strip()


# ==================== 辅助：观察与演示 ====================

def inspect_index(index: dict) -> None:
    """打印切块结果，帮助你直观理解「切块」这一步做得好不好。"""
    for i, (chunk, tokens) in enumerate(zip(index["chunks"], index["tokens"])):
        preview = chunk[:80].replace("\n", " ")
        ellipsis = "..." if len(chunk) > 80 else ""
        print(f"[块 {i + 1}] 字数 {len(chunk)} / 词元 {len(tokens)}")
        print(f"  {preview}{ellipsis}")
        print("-" * 60)


def demo_retrieve(index: dict, query: str, top_k: int = 3) -> None:
    """只演示「检索」环节，不调用大模型（适合没有 API key 时观察效果）。"""
    hits = retrieve(index, query, top_k)
    print(f"[检索] 「{query}」命中 {len(hits)} 段：\n")
    for i, hit in enumerate(hits):
        print(f"[命中 {i + 1}]\n{hit}\n" + "-" * 60)
    print("这是关键词检索的结果。观察它是否找对了段落；阶段二用向量化会找得更准。")
