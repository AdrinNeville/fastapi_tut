from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import models
from database import SessionLocal

router = APIRouter(
    prefix="/items",
    tags=["items"]
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/")
def create_item(name: str, owner_id: int, db: Session = Depends(get_db)):
    # check if user exists
    owner = db.query(models.User).filter(models.User.id == owner_id).first()
    if not owner:
        raise HTTPException(status_code=400, detail="Owner does not exist")
    item = models.Item(name=name, owner_id=owner_id)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item

@router.get("/")
def get_items(db: Session = Depends(get_db)):
    return db.query(models.Item).all()

@router.get("/{item_id}")
def get_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item