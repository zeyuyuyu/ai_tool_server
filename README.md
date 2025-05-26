# AI Tool Server & Token Analysis Agent

## Quick Start (local)
```bash
cd server
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # 填 API KEY
python migrate.py
uvicorn main:app --reload
```
## Agent
```bash
cd ../agent
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python runner.py
```
