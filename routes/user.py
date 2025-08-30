from fastapi import APIRouter

router = APIRouter(
    prefix="/user",   # every route here will start with /users
    tags=["user"]     # shows up in Swagger docs as "users"
)

user_db = []
next_id = 1

@router.post("/")
async def create_user(name: str):
    global next_id
    user = {"id": next_id, "name": name}
    user_db.append(user)
    next_id += 1
    return {"message": f"User '{name}' created", "user": user}

@router.get("/")
async def get_users():
    return {"user": user_db}

@router.get("/{user_id}")
async def get_user(user_id: int):
    for user in user_db:
        if user["id"] == user_id:
            return user
    return {"error": "User not found"}