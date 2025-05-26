from fastapi import FastAPI
from routers.chat import router as chat_router
from db import init_db

init_db()
app = FastAPI(title="AI Tool Server")
app.include_router(chat_router)
