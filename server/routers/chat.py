# server/routers/chat.py
import json, time
from typing import Any, Dict, List

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.orm import Session

from db import SessionLocal, RequestLog, UsageLog
from schemas import ChatCompletionRequest
from model_client import chat_completion
from toolkit import get_tool_funcs, call_tool_calls

router = APIRouter(prefix="/v1")


# ---------- helpers ---------------------------------------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _extract_tool_name(call: Any) -> str | None:
    """兼容 dict 结构与 openai ToolCall 对象"""
    if isinstance(call, dict):
        return call.get("name") or call.get("function", {}).get("name")
    return getattr(call, "name", None) or getattr(getattr(call, "function", None), "name", None)


# ---------- route -----------------------------------------------------------
@router.post("/chat/completions")
async def completions(req: ChatCompletionRequest, db: Session = Depends(get_db)):
    t0 = time.time()
    log = RequestLog(
        model=req.model,
        prompt=[m.model_dump() for m in req.messages],
        stream=int(req.stream),
    )
    db.add(log)
    db.commit()
    db.refresh(log)

    tool_funcs = await get_tool_funcs()

    async def run(history: List[Dict]):
        return await chat_completion(
            req.model, history, tool_funcs, stream=False, max_tokens=req.max_tokens
        )

    # --------------------------- stream -------------------------------------
    if req.stream:

        async def generate():
            history = [m.model_dump() for m in req.messages]
            tools_used: List[str] = []

            while True:
                resp = await run(history)
                msg = resp.choices[0].message

                # 1️⃣ 推 assistant delta
                yield f"data: {json.dumps({'choices':[{'delta': msg.model_dump(mode='python')} ]})}\n\n"

                # 2️⃣ 把带 tool_calls 的 assistant 消息加入 history
                history.append(msg.model_dump(mode="python"))

                tool_calls = msg.tool_calls or []
                if tool_calls:
                    for call in tool_calls:
                        tool_name = _extract_tool_name(call)
                        tools_used.append(tool_name)
                        yield f"data: {json.dumps({'choices':[{'delta': {'tool': tool_name}}]})}\n\n"

                    # 调用工具并把结果追加进历史
                    history.extend(await call_tool_calls(tool_calls))
                    continue

                # 结束：写 usage 日志
                db.add(
                    UsageLog(
                        request_id=log.id,
                        tokens_prompt=resp.usage.prompt_tokens,
                        tokens_completion=resp.usage.completion_tokens,
                        tools_used=tools_used,
                        latency_ms=int((time.time() - t0) * 1000),
                    )
                )
                db.commit()

                yield f"data: {json.dumps({'choices':[{'finish_reason':'stop'}]})}\n\n"
                yield "data: [DONE]\n\n"
                break

        return StreamingResponse(generate(), media_type="text/event-stream")

    # ------------------------- non-stream -----------------------------------
    history = [m.model_dump() for m in req.messages]
    tools_used: List[str] = []

    while True:
        resp = await run(history)
        msg = resp.choices[0].message
        history.append(msg.model_dump(mode="python"))

        tool_calls = msg.tool_calls or []
        if tool_calls:
            tools_used += [_extract_tool_name(c) for c in tool_calls]
            history.extend(await call_tool_calls(tool_calls))
            continue

        db.add(
            UsageLog(
                request_id=log.id,
                tokens_prompt=resp.usage.prompt_tokens,
                tokens_completion=resp.usage.completion_tokens,
                tools_used=tools_used,
                latency_ms=int((time.time() - t0) * 1000),
            )
        )
        db.commit()
        return JSONResponse(content=resp.model_dump(mode="python"))
