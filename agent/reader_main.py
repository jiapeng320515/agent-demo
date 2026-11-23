"""读书 agent 命令行入口（阶段一：关键词检索 RAG）。

用法：
    # 交互式问答（需要 .env 里的 API key）
    python -m agent.reader_main --book books/sample.txt

    # 单次提问
    python -m agent.reader_main --book books/sample.txt -q "费曼学习法是什么"

    # 只看切块结果（理解「切块」这一步）
    python -m agent.reader_main --book books/sample.txt --inspect

    # 只演示检索，不调用 LLM（无 key 也能跑）
    python -m agent.reader_main --book books/sample.txt --demo -q "番茄工作法"
"""

__author__ = "Lucy"

import argparse

# 兼容「直接以脚本运行」：IDEA 的 Run 按钮、或 `python agent/reader_main.py`
# 会以脚本方式启动本文件，此时 Python 把它当作顶层脚本（__package__ 为 None），
# 下面的相对导入（from . import reader）会报 ImportError。
# 这里手动把项目根目录加入 sys.path，并声明本文件属于 agent 包，让相对导入也能工作；
# 用 `python -m agent.reader_main`（模块方式）运行时本块不会生效，两者互不影响。
if __package__ in (None, ""):
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    __package__ = "agent"

from . import reader
from .llm import build_client


def _answer_or_demo(client, index, question, top_k, demo_mode):
    """根据「是否有 key」和「是否 demo 模式」，决定调 LLM 还是只演示检索。"""
    if demo_mode or client is None:
        reader.demo_retrieve(index, question, top_k)
    else:
        print(f"\n[答案] {reader.ask(client, index, question, top_k)}")


def main() -> None:
    parser = argparse.ArgumentParser(description="读书 agent（阶段一：关键词检索 RAG）")
    parser.add_argument("--book", default="books/sample.txt", help="书文件路径（txt）")
    parser.add_argument("-q", "--question", help="单次提问")
    parser.add_argument("--top-k", type=int, default=3, help="检索返回的段落数（默认 3）")
    parser.add_argument("--inspect", action="store_true", help="只展示切块结果，不问答")
    parser.add_argument("--demo", action="store_true", help="只演示检索，不调用 LLM")
    args = parser.parse_args()

    # ① 建索引（一次性）
    print(f"正在加载：{args.book}")
    text = reader.load_book(args.book)
    index = reader.build_index(text)
    print(f"切块完成：共 {len(index['chunks'])} 块\n")

    if args.inspect:
        reader.inspect_index(index)
        return

    client = build_client()
    if client is None:
        print("未检测到 OPENAI_API_KEY，本次只演示「检索」环节（不调用 LLM）。")
        print("要完整回答，请复制 .env.example 为 .env 并填入密钥。\n")

    demo_mode = args.demo or client is None

    if args.question:
        _answer_or_demo(client, index, args.question, args.top_k, demo_mode)
        return

    print("=" * 52)
    print("读书 agent（阶段一：关键词检索 RAG）")
    print("输入问题开始，输入 exit / quit 退出。")
    print("=" * 52)
    while True:
        try:
            question = input("\n你 > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n再见！")
            break
        if question.lower() in ("exit", "quit", "q"):
            print("再见！")
            break
        if not question:
            continue
        _answer_or_demo(client, index, question, args.top_k, demo_mode)


if __name__ == "__main__":
    main()
