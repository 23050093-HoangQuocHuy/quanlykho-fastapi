from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional

from app import crud, schemas
from app.database import get_db

router = APIRouter()

# =========================
# GET ALL ITEMS (SKU FILTER)
# =========================
@router.get("/", response_model=list[schemas.InventoryItem])
def list_items(
    skip: int = 0,
    limit: int = 10,
    sku: Optional[str] = None,
    name: Optional[str] = None,
    category_id: Optional[int] = None,
    created_by: Optional[int] = None,
    db: Session = Depends(get_db)
):
    return crud.get_items(
        db=db,
        skip=skip,
        limit=limit,
        sku=sku,
        name=name,
        category_id=category_id,
        created_by=created_by
    )


# =========================
# GET SINGLE ITEM
# =========================
@router.get("/{item_id}", response_model=schemas.InventoryItem)
def read_item(item_id: int, db: Session = Depends(get_db)):
    db_item = crud.get_item(db, item_id)
    if not db_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )
    return db_item


# =========================
# CREATE ITEM
# =========================
@router.post("/", response_model=schemas.InventoryItem, status_code=status.HTTP_201_CREATED)
def create_item(item: schemas.InventoryItemCreate, db: Session = Depends(get_db)):
    return crud.create_item(db, item)


# =========================
# UPDATE ITEM
# =========================
@router.post("/{item_id}", response_model=schemas.InventoryItem)
def update_item(
    item_id: int,
    updates: schemas.InventoryItemUpdate,
    db: Session = Depends(get_db)
):
    db_item = crud.get_item(db, item_id)
    if not db_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )
    return crud.update_item(db, db_item, updates)


# =========================
# DELETE ITEM
# =========================
@router.delete("/{item_id}", response_model=schemas.InventoryItem)
def delete_item(item_id: int, db: Session = Depends(get_db)):
    db_item = crud.get_item(db, item_id)
    if not db_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )
    return crud.delete_item(db, item_id)
