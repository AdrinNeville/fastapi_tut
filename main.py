from fastapi import FastAPI,status,Depends,HTTPException
from routes import user, items

app = FastAPI()
app.include_router(user.router)
app.include_router(items.router)

@app.get("/")
async def root():
    return {"message": "Hello World"}

