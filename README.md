# AI Tool Server & Token-Analysis Agent

> ✅ OpenAI-compatible `/v1/chat/completions` (stream & non-stream)  
> ✅ UnifAI Tools loop + Claude token-efficient header  
> ✅ Redis prompt-cache for Claude (opt-in, 1800 s)  
> ✅ Crypto-Token Multi-dimensional report (HTML + charts)

---

## 0. 目录结构（核心）

```

server/
├─ main.py              # FastAPI entry
├─ routers/chat.py      # OpenAI-compatible route + SSE stream
├─ model\_client.py      # OpenAI / Anthropic wrapper (+ Redis cache)
├─ cache.py             # tiny redis helper
├─ requirements.txt
agent/ …                 # Token analysis workflow

````

---

## 1. Quick Start (Local Linux / macOS)

```bash
git clone https://github.com/<you>/ai_tool_server.git
cd ai_tool_server/server

python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt                 # installs redis, orjson, litellm, …
cp .env.example .env                            # add your Keys here
# optional Redis (Claude cache)
docker run -d --name redis -p 6379:6379 redis:7
uvicorn main:app --host 0.0.0.0 --port 8080 --reload
````

打开 [http://localhost:8080/docs](http://localhost:8080/docs) 即可调接口。
流式 curl 示例（Server-Sent Events）：

```bash
curl -N http://localhost:8080/v1/chat/completions \
 -H "Content-Type: application/json" \
 -d '{
       "model":"gpt-4o-mini",
       "messages":[{"role":"user","content":"Tell me a joke"}],
       "stream": true
     }'
```

输出会是：

```
data: {"choices":[{"delta":{"role":"assistant"}}]}

data: {"choices":[{"delta":{"content":"Why did..."}}]}

data: {"choices":[{"finish_reason":"stop"}]}

data: [DONE]
```

---

## 2. 云服务器部署示例（Ubuntu 22.04）

| 步骤        | 命令                                                                                        |
| --------- | ----------------------------------------------------------------------------------------- |
| ① 系统依赖    | `sudo apt update && sudo apt install python3.10 python3-venv git redis-server -y`         |
| ② 克隆 + 安装 | 同 *Quick Start*                                                                           |
| ③ systemd | `sudo cp deploy/ai-api.service /etc/systemd/system && sudo systemctl enable --now ai-api` |
| ④ 端口映射    | 云控制台放通 **TCP 8080**<br>或使用**自带映射**下表                                                      |

| 内部端口 | 公网端口(示例) | 访问 URL                   |
| ---- | -------- | ------------------------ |
| 8080 | 34773    | `http://<ip>:34773/docs` |
| 8081 | 34788    | `http://<ip>:34788/…`    |

---

## 3. Redis Prompt Cache (Claude only)

* **为什么？** Anthropic Claude 支持 server-side prompt-caching；本地再加 LRU 可省 \$\$。
* **启用**：默认 `.env` 留空即使用 `localhost:6379`; 亦可：

```ini
REDIS_HOST=your.redis.host
REDIS_PORT=6379
```

* **策略**：对最后 6 条消息做 `md5`，缓存 30 min。
  命中后直接返回，不再占用 Claude token。

---

## 4. Token 分析 Agent

```bash
cd ../agent && source ../server/.venv/bin/activate  # 可共用 venv
pip install -r requirements.txt
python runner.py usd-coin 0xa0b8...                 # 生成 ./usd-coin_report.html
```

报告内嵌价格/交易量 PNG + GPT-4o 洞察。

---

## 5. 常见错误 & 排查

| 症状                                                   | 可能原因                                      | 解决                       |
| ---------------------------------------------------- | ----------------------------------------- | ------------------------ |
| `openai.BadRequestError: messages with role 'tool'…` | 流式忘记把带 `tool_calls` 的 assistant 消息 append | 已在 `routers/chat.py` 修复  |
| Browser SSE “JSON parse error”                       | `data:` 前缀缺失                              | 现已加 `data: …\n\n`        |
| Redis 连接 refused                                     | 未运行 redis-server 或端口不对                    | `docker ps` 检查，或改 `.env` |
| Claude 缓存未命中                                         | prompt 不完全一致                              | 确认 messages 最后 6 条相同     |


