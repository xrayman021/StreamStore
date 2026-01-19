from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from fastapi.responses import HTMLResponse
import uuid
import os
from producer import send_order

app = FastAPI(title="Order API")

class Order(BaseModel):
    order_id: str | None = Field(default=None)
    user: str
    item: str
    price: int
    quantity: int

@app.post("/orders", status_code=202)
def post_order(order: Order):
    data = order.dict()
    if not data.get("order_id"):
        data["order_id"] = uuid.uuid4().hex
    try:
        send_order(data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"status": "accepted", "order_id": data["order_id"]}

@app.get("/", response_class=HTMLResponse)
def index():
    with open(os.path.join("ui", "index.html"), "r", encoding="utf-8") as f:
        return f.read()