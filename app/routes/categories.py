from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app import crud, schemas
from app.database import get_db


router = APIRouter()


@router.get("/", response_model=list[schemas.Category])
def list_categories(skip: int = 0, limit: int = 10, search: str | None = None, db: Session = Depends(get_db)):
    return crud.get_categories(db, skip=skip, limit=limit, search=search)


@router.get("/{category_id}", response_model=schemas.Category)
def read_category(category_id: int, db: Session = Depends(get_db)):
    db_category = crud.get_category(db, category_id)
    if not db_category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, details="Category not found")
    return db_category

@router.post("/", response_model=schemas.Category, status_code=status.HTTP_201_CREATED)
def create_category(category: crud.CategoryCreate, db: Session = Depends(get_db)):
    return crud.create_category(db, category)


@router.post("/{category_id}", response_model=schemas.Category)
def update_category(category_id: int, updates: schemas.CategoryUpdate, db: Session = Depends(get_db)):
    db_category = crud.get_category(db, category_id)
    if not db_category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, details="Category not found")
    return crud.update_category(db, db_category, updates)

@router.delete("/{category_id}", response_model=schemas.Category)
def delete_category(category_id: int, db: Session = Depends(get_db)):
    db_category = crud.get_category(db, category_id)
    if not db_category:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, details="Category not found")
    deleted_category = crud.delete_category(db, category_id)
    if not deleted_category:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unable to delete category")
    return deleted_category


