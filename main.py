from fastapi import FastAPI,status,Depends,HTTPException
from typing import Annotated
from sqlalchemy.orm import Session


app = FastAPI()
app.include_router(auth.router)


models.Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]

@app.get("/", status_code=status.HTTP_200_OK)
async def verify_user_exists(user: user_dependency, db: db_dependency):
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication failed")
    return {"User":user}

@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    return {"status":"ok"}