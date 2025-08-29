from fastapi import FastAPI
from routes import users, items

app = FastAPI()

app.include_router(users.router)
app.include_router(items.router)

@app.get("/")
def root():
    return {"message": "Welcome!"}