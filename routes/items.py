from fastapi import APIRouter

router = APIRouter(
    prefix="/items",
    tags=["items"]
)

# Fake in-memory "database"
items_db = []
next_id = 1

@router.post("/")
async def create_item(name: str):
    global next_id
    item = {"id": next_id, "name": name}
    items_db.append(item)
    next_id += 1
    return {"message": f"Item '{name}' created", "item": item}

@router.get("/")
async def get_items():
    return {"items": items_db}

@router.get("/{item_id}")
async def get_item(item_id: int):
    for item in items_db:
        if item["id"] == item_id:
            return item
    return {"error": "Item not found"}