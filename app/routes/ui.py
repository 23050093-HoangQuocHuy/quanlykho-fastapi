from datetime import timedelta
from fastapi import APIRouter, Request, Form, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import jwt

from app import models, schemas, crud
from app.database import get_db
from app.models import User, Category
from app.routes.auth import (
    create_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    SECRET_KEY,
    ALGORITHM,
)

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# =====================================
# Auth + Profile + Logout
# =====================================

@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/login", response_class=HTMLResponse)
async def login_user(
    request: Request,
    username: str = Form(..., max_length=50),
    password: str = Form(..., max_length=100),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.username == username).first()
    if not user or not crud.pwd_context.verify(password, user.password):
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Invalid Credentials"},
        )

    token = create_access_token(
        data={"sub": user.username},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    response = RedirectResponse(url="/profile", status_code=status.HTTP_302_FOUND)
    response.set_cookie(key="access_token", value=token, httponly=True)
    return response


@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


@router.post("/register", response_class=HTMLResponse)
async def register_user(
    request: Request,
    username: str = Form(..., max_length=50),
    password: str = Form(..., max_length=100),
    role: str = Form(..., max_length=20),
    db: Session = Depends(get_db),
):
    existing_user = db.query(User).filter(User.username == username).first()
    if existing_user:
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "User already registered"},
        )

    user_in = schemas.UserCreate(username=username, password=password, role=role)
    crud.create_user(db, user_in)

    return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)


def get_current_user_from_cookie(
    request: Request, db: Session = Depends(get_db)
) -> User:
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user


@router.get("/profile", response_class=HTMLResponse)
async def profile_page(
    request: Request,
    current_user: User = Depends(get_current_user_from_cookie),
):
    return templates.TemplateResponse(
        "profile.html", {"request": request, "current_user": current_user}
    )


@router.get("/logout")
async def logout():
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie("access_token")
    return response


# =====================================
# Inventory: Manage
# =====================================

@router.get("/inventory/manage", response_class=HTMLResponse)
async def manage_inventory(
    request: Request,
    sku: str | None = None,
    page: int = 1,
    current_user: User = Depends(get_current_user_from_cookie),
    db: Session = Depends(get_db),
):
    limit = 10
    skip = (page - 1) * limit

    items = crud.get_items(
        db,
        skip=skip,
        limit=limit,
        created_by=current_user.user_id,
        sku=sku,
    )

    prev_page = page - 1 if page > 1 else None
    next_page = page + 1 if len(items) == limit else None

    categories = crud.get_categories(db)
    categories_data = [
        {"category_id": c.category_id, "name": c.name} for c in categories
    ]

    return templates.TemplateResponse(
        "manage_inventory.html",
        {
            "request": request,
            "current_user": current_user,
            "items": items,
            "sku": sku,
            "prev_page": prev_page,
            "next_page": next_page,
            "categories": categories_data,
        },
    )


# =====================================
# Inventory: View
# =====================================

@router.get("/inventory/view", response_class=HTMLResponse)
async def view_inventory(
    request: Request,
    sku: str | None = None,        # ✅ SKU
    category_id: str | None = None,
    page: int = 1,
    current_user: User = Depends(get_current_user_from_cookie),
    db: Session = Depends(get_db),
):
    limit = 10
    skip = (page - 1) * limit
    

    items = crud.get_items(
        db,
        skip=skip,
        limit=limit,
        sku=sku,
        created_by=current_user.user_id,
    )

    prev_page = page - 1 if page > 1 else None
    next_page = page + 1 if len(items) == limit else None

    return templates.TemplateResponse(
        "view_inventory.html",
        {
            "request": request,
            "current_user": current_user,
            "items": items,
            "sku": sku,
            "page": page,
            "prev_page": prev_page,
            "next_page": next_page,
            "currency": "VND",
        },
    )


# =====================================
# Inventory: Add / Edit / Delete
# =====================================

@router.post("/inventory/add")
async def add_inventory_item(
    sku: str = Form(...),
    name: str = Form(...),
    description: str = Form(""),
    quantity: int = Form(...),
    price: float = Form(...),
    category: str = Form(...),
    category_id: str = Form(""),
    supplier: str = Form(""),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie),
):
    if category_id:
        cat_id = int(category_id)
    else:
        cat = db.query(Category).filter(Category.name == category).first()
        if not cat:
            cat = crud.create_category(
                db, schemas.CategoryCreate(name=category, description="")
            )
        cat_id = cat.category_id

    item = schemas.InventoryItemCreate(
        sku=sku,
        name=name,
        description=description,
        quantity=quantity,
        price=price,
        supplier=supplier,
        category_id=cat_id,
        created_by=current_user.user_id,
    )

    crud.create_item(db, item)
    return RedirectResponse("/inventory/manage", status_code=302)


@router.post("/inventory/edit/{item_id}")
async def edit_inventory_item(
    item_id: int,
    sku: str = Form(...),
    name: str = Form(...),
    description: str = Form(""),
    quantity: int = Form(...),
    price: float = Form(...),
    category_id: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie),
):
    item = crud.get_item_by_user(db, item_id, current_user.user_id)
    if not item:
        raise HTTPException(404, "Item not found")

    updates = schemas.InventoryItemUpdate(
        sku=sku,
        name=name,
        description=description,
        quantity=quantity,
        price=price,
        category_id=int(category_id),
    )

    crud.update_item(db, item, updates)
    return RedirectResponse("/inventory/manage", status_code=302)


@router.get("/inventory/delete/{item_id}")
async def delete_inventory_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie),
):
    crud.delete_item(db, item_id)
    return RedirectResponse("/inventory/manage", status_code=302)

# =====================================
# Dashboard
# =====================================

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie),
):
    items = (
        db.query(models.InventoryItem)
        .filter(models.InventoryItem.created_by == current_user.user_id)
        .all()
    )

    total_inventory_value = sum(item.quantity * float(item.price) for item in items)

    # Thống kê theo danh mục
    category_data: dict[str, int] = {}
    for item in items:
        name = item.category.name if item.category else "Khác"
        category_data[name] = category_data.get(name, 0) + 1

    category_labels = list(category_data.keys())
    category_counts = list(category_data.values())

    # Thống kê theo giá
    price_ranges = ["0–50", "51–100", "101–200", "201–500", "500+"]
    price_counts = [0, 0, 0, 0, 0]

    for item in items:
        p = float(item.price)
        if p <= 50:
            price_counts[0] += 1
        elif p <= 100:
            price_counts[1] += 1
        elif p <= 200:
            price_counts[2] += 1
        elif p <= 500:
            price_counts[3] += 1
        else:
            price_counts[4] += 1

    # Sắp hết hàng
    low_stock_items = [i for i in items if i.quantity < 10]

    # ✅ Nhà cung cấp (ĐÃ FIX ĐÚNG)
    supplier_counts: dict[str, int] = {}
    for item in items:
        for supplier in item.suppliers:
            name = supplier.name
            supplier_counts[name] = supplier_counts.get(name, 0) + 1

    top_suppliers = sorted(
        supplier_counts.items(), key=lambda x: x[1], reverse=True
    )[:5]

    recent_items = sorted(items, key=lambda x: x.created_at, reverse=True)[:5]

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "current_user": current_user,
            "total_inventory_value": total_inventory_value,
            "category_labels": category_labels,
            "category_counts": category_counts,
            "price_ranges": price_ranges,
            "price_counts": price_counts,
            "low_stock_items": low_stock_items,
            "recent_items": recent_items,
            "supplier_overview": {
                "unique_suppliers": len(supplier_counts),
                "top_suppliers": top_suppliers,
            },
        },
    )


# =====================================
# Orders UI
# =====================================

@router.get("/orders", response_class=HTMLResponse)
async def orders_page(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie),
):
    items = crud.get_items(db, limit=100, created_by=current_user.user_id)
    orders = crud.get_orders(db)

    return templates.TemplateResponse(
        "orders.html",
        {
            "request": request,
            "items": items,
            "orders": orders,
            "current_user": current_user,
        },
    )


@router.post("/orders/create")
async def create_order_ui(
    item_id: list[int] = Form(...),
    quantity: list[int] = Form(...),
    price: list[float] = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie),
):
    items_data = [
        schemas.OrderItemCreate(
            item_id=item_id[i],
            quantity=quantity[i],
            price=price[i],
        )
        for i in range(len(item_id))
    ]

    crud.create_order(db, current_user.user_id, schemas.OrderCreate(items=items_data))
    return RedirectResponse("/orders", status_code=303)
