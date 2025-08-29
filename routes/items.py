from fastapi import APIRouter

router = APIRouter(
    prefix="/items",
    tags=["items"]
)

@router.get("/")
async def get_items():
    return {"message": "List of items"}

@router.get("/{item_id}")
async def get_item(item_id: int):
    return {"message": f"Item with id {item_id}"}