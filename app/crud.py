from sqlalchemy.orm import Session
from fastapi import HTTPException
from passlib.context import CryptContext

from app.models import (
    InventoryItem, Category, Supplier, User, ItemSupplier,
    Order, OrderItem
)
from app import schemas

# ===== Thêm import email =====
from app.email_utils import send_email_alert
import asyncio

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

LOW_STOCK_THRESHOLD = 10   # Ngưỡng cảnh báo


# -----------------------------------------
# Helper
# -----------------------------------------
def get_item_by_user(db: Session, item_id: int, user_id: int):
    return db.query(InventoryItem).filter(
        InventoryItem.item_id == item_id,
        InventoryItem.created_by == user_id
    ).first()


# -----------------------------------------
# Inventory CRUD
# -----------------------------------------
def create_item(db: Session, item: schemas.InventoryItemCreate):
    db_item = InventoryItem(
        name=item.name,
        description=item.description,
        quantity=item.quantity,
        price=item.price,
        category_id=item.category_id,
        created_by=item.created_by
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)

    # xử lý supplier
    if item.supplier and item.supplier.strip():
        existing_supplier = db.query(Supplier).filter(Supplier.name == item.supplier).first()

        if not existing_supplier:
            new_supplier = Supplier(name=item.supplier, contact_details="")
            db.add(new_supplier)
            db.commit()
            db.refresh(new_supplier)
            supplier_id = new_supplier.supplier_id
        else:
            supplier_id = existing_supplier.supplier_id

        item_supplier_link = ItemSupplier(item_id=db_item.item_id, supplier_id=supplier_id)
        db.add(item_supplier_link)
        db.commit()

    return db_item


def get_item(db: Session, item_id: int):
    return db.query(InventoryItem).filter(InventoryItem.item_id == item_id).first()


def get_items(db: Session, skip: int = 0, limit: int = 10, search: str | None = None,
              category_id: int | None = None, created_by: int | None = None):
    query = db.query(InventoryItem)

    if search:
        query = query.filter(InventoryItem.name.ilike(f"%{search}%"))
    if category_id:
        query = query.filter(InventoryItem.category_id == category_id)
    if created_by:
        query = query.filter(InventoryItem.created_by == created_by)

    return query.offset(skip).limit(limit).all()


def update_item(db: Session, db_item: InventoryItem, updates: schemas.InventoryItemUpdate):
    update_data = updates.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_item, key, value)
    db.commit()
    db.refresh(db_item)
    return db_item


def delete_item(db: Session, item_id: int):
    db_item = get_item(db, item_id)
    if db_item:
        db.delete(db_item)
        db.commit()
    return db_item


# -----------------------------------------
# Category CRUD
# -----------------------------------------
def create_category(db: Session, category: schemas.CategoryCreate):
    db_category = Category(**category.model_dump())
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category


def get_category(db: Session, category_id: int):
    return db.query(Category).filter(Category.category_id == category_id).first()


def get_categories(db: Session, skip: int = 0, limit: int = 10, search: str | None = None):
    query = db.query(Category)
    if search:
        query = query.filter(Category.name.ilike(f"%{search}%"))
    return query.offset(skip).limit(limit).all()


def update_category(db: Session, db_category: Category, updates: schemas.CategoryUpdate):
    update_data = updates.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_category, key, value)
    db.commit()
    db.refresh(db_category)
    return db_category


def delete_category(db: Session, category_id: int):
    db_category = get_category(db, category_id)
    if db_category:
        db.delete(db_category)
        db.commit()
    return db_category


# -----------------------------------------
# Supplier CRUD
# -----------------------------------------
def create_supplier(db: Session, supplier: schemas.SupplierCreate):
    db_supplier = Supplier(**supplier.model_dump())
    db.add(db_supplier)
    db.commit()
    db.refresh(db_supplier)
    return db_supplier


def get_supplier(db: Session, supplier_id: int):
    return db.query(Supplier).filter(Supplier.supplier_id == supplier_id).first()


def get_suppliers(db: Session, skip: int = 0, limit: int = 10, search: str | None = None):
    query = db.query(Supplier)
    if search:
        query = query.filter(Supplier.name.ilike(f"%{search}%"))
    return query.offset(skip).limit(limit).all()


def update_supplier(db: Session, db_supplier: Supplier, updates: schemas.SupplierUpdate):
    update_data = updates.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_supplier, key, value)
    db.commit()
    db.refresh(db_supplier)
    return db_supplier


def delete_supplier(db: Session, supplier_id: int):
    db_supplier = get_supplier(db, supplier_id)
    if db_supplier:
        db.delete(db_supplier)
        db.commit()
    return db_supplier


# -----------------------------------------
# User CRUD
# -----------------------------------------
def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = pwd_context.hash(user.password)
    user_data = user.model_dump()
    user_data["password"] = hashed_password
    db_user = User(**user_data)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_user(db: Session, user_id: int):
    return db.query(User).filter(User.user_id == user_id).first()


def update_user(db: Session, db_user: User, updates: schemas.UserUpdate):
    update_data = updates.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_user, key, value)
    db.commit()
    db.refresh(db_user)
    return db_user


def update_user_password(db: Session, db_user: User, updates: schemas.UserPasswordUpdate):
    if not pwd_context.verify(updates.old_password, db_user.password):
        raise ValueError("Incorrect old password")

    new_hashed = pwd_context.hash(updates.new_password)
    db_user.password = new_hashed
    db.commit()
    db.refresh(db_user)
    return db_user


def delete_user(db: Session, user_id: int):
    db_user = get_user(db, user_id)
    if db_user:
        db.delete(db_user)
        db.commit()
    return db_user


# -----------------------------------------
# ORDER CRUD (ĐÃ THÊM EMAIL ALERT)
# -----------------------------------------
def create_order(db: Session, user_id: int, order_data: schemas.OrderCreate):
    # Tạo đơn hàng
    order = Order(
        created_by=user_id,
        status="pending"
    )
    db.add(order)
    db.commit()
    db.refresh(order)

    # Duyệt qua từng item trong đơn hàng
    for item in order_data.items:
        db_item = db.query(InventoryItem).filter(
            InventoryItem.item_id == item.item_id,
            InventoryItem.created_by == user_id
        ).first()

        if not db_item:
            raise HTTPException(status_code=404, detail=f"Sản phẩm ID {item.item_id} không tồn tại.")

        # Kiểm tra tồn kho
        if db_item.quantity < item.quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Sản phẩm '{db_item.name}' không đủ tồn kho."
            )

        # Trừ tồn kho
        db_item.quantity -= item.quantity
        db.add(db_item)

        # ===============================
        # ⚠️ KIỂM TRA LOW-STOCK & GỬI EMAIL
        # ===============================
        if db_item.quantity <= LOW_STOCK_THRESHOLD:
            subject = f"Cảnh báo tồn kho thấp: {db_item.name}"
            body = (
                f"Sản phẩm '{db_item.name}' hiện còn {db_item.quantity} trong kho.\n"
                f"Bạn nên nhập thêm hàng!"
            )

            # gửi email nền
            asyncio.create_task(
                send_email_alert(
                    to_email="huy1995303@gmail.com",   
                    subject=subject,
                    message=body
                )
            )

        # Lưu chi tiết đơn hàng
        order_item = OrderItem(
            order_id=order.order_id,
            item_id=item.item_id,
            quantity=item.quantity,
            price=item.price
        )
        db.add(order_item)

    db.commit()
    db.refresh(order)
    return order


def get_orders(db: Session):
    return db.query(Order).all()


def get_order(db: Session, order_id: int):
    order = db.query(Order).filter(Order.order_id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order
