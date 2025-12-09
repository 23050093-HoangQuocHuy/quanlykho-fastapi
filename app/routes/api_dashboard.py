from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import InventoryItem, User
from app.routes.ui import get_current_user_from_cookie

router = APIRouter(prefix="/api/dashboard")

@router.get("/summary")
async def dashboard_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie)
):
    items = db.query(InventoryItem).filter(InventoryItem.created_by == current_user.user_id).all()
    total_value = sum(item.quantity * float(item.price) for item in items)
    total_items = len(items)

    return {
        "total_inventory_value" : total_value,
        "total_items" : total_items
    }
@router.get("/low-stock")
async def low_stock_items(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie)
):
    items = db.query(InventoryItem).filter(
        InventoryItem.created_by == current_user.user_id,
        InventoryItem.quantity < 10
    ).all()

    return [
        {"name" : item.name, "quantity" : item.quantity}
        for item in items
    ]