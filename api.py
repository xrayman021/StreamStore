# python
# File: `api.py`
# - Adds /health to verify the server is up.
# - Adds /debug-order to accept raw JSON (helps confirm POST reaches the app and diagnose 404s).
# - Keeps the Pydantic /orders POST handler (uses model_dump()).

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.routing import APIRoute
import uuid
import os
from producer import send_order

app = FastAPI(title="Order API")

# Allow local dev cross-origin requests if UI served separately
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class Order(BaseModel):
    order_id: str | None = Field(default=None)
    user: str
    item: str
    price: int
    quantity: int

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/orders", status_code=202)
async def post_order(order: Order):
    data = order.model_dump()
    if not data.get("order_id"):
        data["order_id"] = uuid.uuid4().hex
    try:
        send_order(data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"status": "accepted", "order_id": data["order_id"]}

# Debug endpoint that accepts any JSON body (no Pydantic) to verify requests reach the app
# python
@app.post("/debug-order", status_code=202)
async def debug_order(request: Request):
    try:
        payload = await request.json()
    except (ValueError, UnicodeDecodeError):
        # JSON decoding failed — fall back to raw body, prefer decoded text
        body = await request.body()
        try:
            payload = body.decode("utf-8", errors="replace")
        except Exception:
            payload = body
    return {"received": payload}


@app.get("/", response_class=HTMLResponse)
def index():
    with open(os.path.join("ui", "index.html"), "r", encoding="utf-8") as f:
        return f.read()

@app.get("/routes")
async def list_routes():
    routes = []
    for r in app.routes:
        if isinstance(r, APIRoute):
            routes.append({"path": r.path, "methods": sorted(list(r.methods)), "name": r.name})
    return routes

# Usage after rebuild/restart:
# 1) Check logs: `docker compose logs api --follow`
# 2) Test health: `curl -v http://localhost:8000/health`
# 3) Test debug raw JSON: 
#    `curl -v -X POST http://localhost:8000/debug-order -H "Content-Type: application/json" -d '{"user":"u","item":"i","price":1,"quantity":1}'`
# 4) Test the real route:
#    `curl -v -X POST http://localhost:8000/orders -H "Content-Type: application/json" -d '{"user":"u","item":"i","price":1,"quantity":1}'`
