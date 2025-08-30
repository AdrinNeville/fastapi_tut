from fastapi import FastAPI
from routes import user, items

app = FastAPI()

app.include_router(user.router)
app.include_router(items.router)

@app.get("/")
def root():
    return {"message": "Welcome!"}