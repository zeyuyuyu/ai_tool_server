import json, time
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.orm import Session
from db import SessionLocal, RequestLog, UsageLog
from schemas import ChatCompletionRequest
from model_client import chat_completion
from toolkit import get_tool_funcs, call_tool_calls

router = APIRouter(prefix="/v1")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/chat/completions")
async def completions(req: ChatCompletionRequest, db: Session = Depends(get_db)):
    t0 = time.time()
    log = RequestLog(model=req.model,
                     prompt=[m.model_dump() for m in req.messages],
                     stream=int(req.stream))
    db.add(log); db.commit(); db.refresh(log)

    tool_funcs = await get_tool_funcs()

    async def run_chat(history):
        resp = await chat_completion(req.model, history, tool_funcs,
                                     stream=False, max_tokens=req.max_tokens)
        return resp

    if req.stream:
        async def generate():
            history = [m.model_dump() for m in req.messages]
            tools_used = []
            while True:
                resp = await run_chat(history)
                msg = resp["choices"][0]["message"]
                yield json.dumps({"choices":[{"delta": msg}]}) + "\n"
                tool_calls = msg.get("tool_calls", [])
                if tool_calls:
                    for call in tool_calls:
                        tools_used.append(call["name"])
                        yield json.dumps({"choices":[{"delta": {"tool": call['name']}}]}) + "\n"
                    tool_msgs = await call_tool_calls(tool_calls)
                    history.extend(tool_msgs)
                    continue
                else:
                    db.add(UsageLog(request_id=log.id,
                                    tokens_prompt=resp["usage"]["prompt_tokens"],
                                    tokens_completion=resp["usage"]["completion_tokens"],
                                    tools_used=tools_used,
                                    latency_ms=int((time.time()-t0)*1000)))
                    db.commit()
                    yield json.dumps({"choices":[{"finish_reason":"stop"}]}) + "\n"
                    break
        return StreamingResponse(generate(), media_type="application/json")
    else:
        history = [m.model_dump() for m in req.messages]
        tools_used = []
        while True:
            resp = await run_chat(history)
            msg = resp["choices"][0]["message"]
            history.append(msg)
            tool_calls = msg.get("tool_calls", [])
            if tool_calls:
                tools_used += [c["name"] for c in tool_calls]
                history.extend(await call_tool_calls(tool_calls))
                continue
            else:
                db.add(UsageLog(request_id=log.id,
                                tokens_prompt=resp["usage"]["prompt_tokens"],
                                tokens_completion=resp["usage"]["completion_tokens"],
                                tools_used=tools_used,
                                latency_ms=int((time.time()-t0)*1000)))
                db.commit()
                return JSONResponse(content=resp)
