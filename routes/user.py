from fastapi import APIRouter

router = APIRouter(
    prefix="/user",   # every route here will start with /users
    tags=["user"]     # shows up in Swagger docs as "users"
)

@router.get("/")
async def get_users():
    return {"message": "List of users"}

@router.get("/{user_id}")
async def get_user(user_id: int):
    return {"message": f"User with id {user_id}"}