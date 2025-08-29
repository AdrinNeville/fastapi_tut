from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

class Item(BaseModel):
    text: str
    is_done: bool=False

items = []

@app.get("/")
def root():
    return {"status": "ok", "message": "FastAPI is running"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.post("/items")
def create_item(item: Item):
    items.append(item)
    return items

@app.get("/items", response_model=list[Item])
def list_items(limit: int = 10):
    return items[0:limit]

@app.get("/items/{item_id}", response_model=Item)
def get_item(item_id: int) -> Item:
    if item_id < 0 or item_id >= len(items):
        raise HTTPException(status_code=404, detail=f"Item {item_id} not found")
    return items[item_id]

@app.put("/items/{item_id}", response_model=Item)
def update_item(item_id: int, item: Item) -> Item:  
    if item_id < 0 or item_id >= len(items):
        raise HTTPException(status_code=404, detail=f"Item {item_id} not found")
    items[item_id] = item
    return item

@app.delete("/items/{item_id}", response_model=Item)
def delete_item(item_id: int) -> Item:
    if item_id < 0 or item_id >= len(items):
        raise HTTPException(status_code=404, detail=f"Item {item_id} not found")
    return items.pop(item_id)