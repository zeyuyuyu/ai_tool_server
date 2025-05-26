FROM python:3.10-slim
WORKDIR /app
COPY server/requirements.txt ./requirements.txt
RUN pip install -r requirements.txt
COPY server ./server
WORKDIR /app/server
CMD ["uvicorn","main:app","--host","0.0.0.0","--port","8000","--workers","2"]
