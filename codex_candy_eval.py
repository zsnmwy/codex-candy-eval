#!/usr/bin/env python3
"""用本地 codex CLI 测试糖果问题，统计 reasoning tokens 并判分。
    uv run python codex_candy_eval.py -m gpt-5.5 -r high -n 5
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import time
import unicodedata

CODEX_PROMPT = """不使用任何外部工具回答以下问题：

在一个黑色的袋子里放有三种口味的糖果，每种糖果有两种不同的形状（圆形和五角星形，不同的形状靠手感可以分辨）。现已知不同口味的糖和不同形状的数量统计如下表。参赛者需要在活动前决定摸出的糖果数目，那么，最少取出多少个糖果才能保证手中同时拥有不同形状的苹果味和桃子味的糖？（同时手中有圆形苹果味匹配五角星桃子味糖果，或者有圆形桃子味匹配五角星苹果味糖果都满足要求）

        苹果味  桃子味  西瓜味
圆形       7      9      8
五角星形   7      6      4
"""

# 正确答案为 21：只要回答中出现独立的 "21"（前后非数字）即判为正确。
ANSWER_PATTERN = re.compile(r"(?<!\d)21(?!\d)")


def run_codex(model: str | None, effort: str):
    cmd = [
        "codex", "exec", "--json",
        "--skip-git-repo-check",
        "--ephemeral",
        "-s", "read-only",
        "-c", f"model_reasoning_effort={effort}",
    ]
    if model:
        cmd += ["-m", model]
    cmd.append(CODEX_PROMPT)

    proc = subprocess.run(
        cmd, capture_output=True, text=True, stdin=subprocess.DEVNULL
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip() or "codex exec failed")

    # codex --json emits one JSON event per line. The final answer is the last
    # `agent_message` item; token usage (incl. reasoning) is in `turn.completed`.
    final_text = ""
    usage: dict = {}
    for line in proc.stdout.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") == "item.completed":
            item = event.get("item", {})
            if item.get("type") == "agent_message":
                final_text = item.get("text", final_text)
        elif event.get("type") == "turn.completed":
            usage = event.get("usage") or {}

    return (
        final_text,
        usage.get("input_tokens"),
        usage.get("output_tokens"),
        usage.get("reasoning_output_tokens"),
    )


def char_width(char: str) -> int:
    """终端显示宽度：组合字符 0，东亚全角/宽字符 2，其余 1。"""
    if unicodedata.combining(char):
        return 0
    return 2 if unicodedata.east_asian_width(char) in {"W", "F"} else 1


def display_width(text: str) -> int:
    return sum(char_width(c) for c in text)


def pad(text: str, width: int, align: str) -> str:
    """按显示宽度补空格对齐（中文宽字符按 2 计）。"""
    gap = width - display_width(text)
    if gap <= 0:
        return text
    if align == "right":
        return " " * gap + text
    if align == "center":
        left = gap // 2
        return " " * left + text + " " * (gap - left)
    return text + " " * gap


def render_table(headers: list[str], rows: list[list], aligns: list[str]) -> str:
    """原生渲染对齐表格（tabulate "simple" 风格），列宽按显示宽度计算。"""
    str_rows = [[str(c) for c in row] for row in rows]
    widths = [
        max(display_width(headers[i]), *(display_width(r[i]) for r in str_rows)) if str_rows
        else display_width(headers[i])
        for i in range(len(headers))
    ]

    def fmt(cells: list[str]) -> str:
        return "  ".join(pad(cells[i], widths[i], aligns[i]) for i in range(len(headers)))

    lines = [fmt(headers), "  ".join("-" * w for w in widths)]
    lines += [fmt(r) for r in str_rows]
    return "\n".join(lines)


def preview(text: str, limit: int = 40) -> str:
    flat = text.replace("\r\n", "\n").replace("\r", "\n").replace("\n", r"\n")
    if display_width(flat) <= limit:
        return flat

    result = []
    width = 0
    for char in flat:
        next_width = char_width(char)
        if width + next_width > limit - 3:
            break
        result.append(char)
        width += next_width
    return "".join(result) + "..."


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-m", "--model", help="Codex model name; omit for the local default.")
    parser.add_argument(
        "-r", "--reasoning-effort", default="medium",
        choices=["low", "medium", "high", "xhigh"],
    )
    parser.add_argument("-n", "--tests", type=int, default=1)
    args = parser.parse_args()

    headers = ["Run", "Codex", "In Tok", "Out Tok", "Reason Tok", "Time(s)", "TPS", "OK"]
    aligns = ["right", "left", "right", "right", "right", "right", "right", "center"]

    def run_one(index: int) -> tuple[list, bool | None]:
        try:
            start = time.perf_counter()
            text, in_tok, out_tok, rea_tok = run_codex(args.model, args.reasoning_effort)
            elapsed = time.perf_counter() - start
            tps = out_tok / elapsed if out_tok and elapsed > 0 else None
            ok = bool(ANSWER_PATTERN.search(text))
            return [index, preview(text), in_tok, out_tok, rea_tok, f"{elapsed:.1f}",
                    f"{tps:.1f}" if tps else "-", "✓" if ok else "✗"], ok
        except Exception as exc:
            return [index, f"ERROR: {preview(str(exc))}", *["-"] * 6], None

    # 串行执行：逐个请求，完成一个立即打印该行结果。
    rows = []
    graded = []
    # 保存表格起始位置；后续直接回到这里重绘，不依赖终端换行数。
    print("\033[s", end="", flush=True)
    for index in range(1, args.tests + 1):
        row, ok = run_one(index)
        rows.append(row)
        if ok is not None:
            graded.append(ok)
        table = render_table(headers, rows, aligns)
        # 恢复到表格起始位置，清除旧表格，再绘制累计结果。
        print("\033[u\033[J", end="")
        print(table, flush=True)

    correct = sum(graded)
    print(f"\nGraded {len(graded)}/{args.tests}  correct={correct}  "
          f"accuracy={correct / len(graded) * 100:.1f}%"
          if graded else f"\nGraded 0/{args.tests}")


if __name__ == "__main__":
    main()
