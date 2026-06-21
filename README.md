# codex-candy-eval

用本地 codex CLI 批量测试一道糖果数学题，并统计 reasoning tokens 与正确率。

## 依赖

- 已安装并登录 [codex CLI](https://github.com/openai/codex)（需支持 `codex exec --json`）
- Python 3，纯标准库，无需额外依赖

## 用法

```bash
python codex_candy_eval.py -m gpt-5.5 -r high -n 5
```

参数：

- `-m, --model`：codex 模型名，省略则用本地默认
- `-r, --reasoning-effort`：`low` / `medium` / `high` / `xhigh`（默认 `medium`）
- `-n, --tests`：测试次数（默认 1）

正确答案为 **21**，脚本直接判断回答中是否出现独立的 `21`。
