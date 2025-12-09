from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app import crud, schemas
from app.database import get_db


router = APIRouter()

# get all items
@router.get("/", response_model=list[schemas.InventoryItem])
def list_items(skip: int = 0, limit: int = 10, search: str | None = None, category_id: int | None = None, db: Session = Depends(get_db)):
    return crud.get_items(db, skip=skip, limit=limit, search=search, category_id=category_id )

# get a single item
@router.get("/{item_id}", response_model=schemas.InventoryItem)
def read_item(item_id: int, db: Session = Depends(get_db)):
    db_item = crud.get_item(db, item_id)
    if not db_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail = "Item not found")
    return db_item

# create an item
@router.post("/", response_model=schemas.InventoryItem, status_code=status.HTTP_201_CREATED)
def create_item(item: schemas.InventoryItemCreate, db: Session = Depends(get_db)):
    return crud.create_item(db, item)

# update an item
@router.post("/{item_id}", response_model=schemas.InventoryItem)
def update_item(item_id: int, updates: schemas.InventoryItemUpdate, db: Session = Depends(get_db)):
    db_item = crud.get_item(db, item_id)
    if not db_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail = "Item not found")
    return crud.update_item(db, db_item, updates)

# delete an item
@router.delete("/{item_id}", response_model=schemas.InventoryItem)
def delete_item(item_id: int, db: Session = Depends(get_db)):
    db_item = crud.get_item(db, item_id)
    if not db_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    deleted_item = crud.delete_item(db,item_id)
    if not deleted_item:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unable to delete item")
    return deleted_item