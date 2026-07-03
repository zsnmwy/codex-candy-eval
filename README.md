# Codex 降智测试 & 尝试修复

## How fix - 替换系统提示词

将 [gpt-5.5-base-instructions.md](./gpt-5.5-base-instructions.md) 放到 `~/.codex`中。

配置 `config.toml` ，加入下面的配置

```
model_instructions_file = '/${ABS FILE PATH}/gpt-5.5-base-instructions.md'
```

配置写**绝对路径**指向该系统提示词

建议先走下面的方式去测试一下智商，等替换系统提示词后，再次测试，看看智商是否有改善。

## 智商测试

用本地 Codex CLI 批量测试一道糖果数学题，并统计 reasoning tokens 与正确率。

![example](./example.png)

## 用法

该脚本无任何第三方依赖，只需要您已安装并登录 [Codex CLI](https://github.com/openai/codex)

```bash
python codex_candy_eval.py -m gpt-5.5 -r high -n 5
```
### 一键运行
以下任选其一
```bash
wget -qO- "https://raw.githubusercontent.com/haowang02/codex-candy-eval/main/codex_candy_eval.py" | python3 - -m gpt-5.5 -r high -n 5
```
```bash
curl -fsSL "https://raw.githubusercontent.com/haowang02/codex-candy-eval/main/codex_candy_eval.py" | python3 - -m gpt-5.5 -r high -n 5
```

参数：

- `-m, --model`：codex 模型名，省略则用本地默认
- `-r, --reasoning-effort`：`low/medium/high/xhigh`（默认 `medium`）
- `-n, --tests`：测试次数（默认 1）

正确答案为 **21**，脚本直接判断回答中是否出现独立的 `21`。

## 致谢

- [LINUX DO](https://linux.do/) - 新的理想型社区
- [有关 Codex 516 降智问题的局部探索](https://linux.do/t/topic/2489646)

