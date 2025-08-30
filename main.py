from fastapi import FastAPI
from database import Base, engine
import models
from routes import items, users

app = FastAPI()

# create both tables in one go
Base.metadata.create_all(bind=engine)

# include routers
app.include_router(users.router)
app.include_router(items.router)
