from datetime import timedelta
from fastapi import APIRouter, Request, Form, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import jwt

from app import models, schemas, crud
from app.database import get_db
from app.models import User, Category
from app.routes.auth import create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES, SECRET_KEY, ALGORITHM
from app.currency_utils import get_exchange_rate

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
    exisiting_user = db.query(User).filter(User.username == username).first()
    if exisiting_user:
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "User already registered"},
        )

    user_in = schemas.UserCreate(username=username, password=password, role=role)
    try:
        crud.create_user(db, user_in)
    except Exception as e:
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": f"Registration failed: {str(e)}"},
        )

    response = RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    return response


def get_current_user_from_cookie(
    request: Request, db: Session = Depends(get_db)
) -> User:
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
        )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str | None = payload.get("sub")
        if not username:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
            )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
        )
    return user


@router.get("/profile", response_class=HTMLResponse)
async def profile_page(
    request: Request, current_user: schemas.User = Depends(get_current_user_from_cookie)
):
    return templates.TemplateResponse(
        "profile.html", {"request": request, "current_user": current_user}
    )


@router.get("/logout")
async def logout(_request: Request):
    response = RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    response.delete_cookie("access_token")
    return response

# =====================================
# Inventory: Manage
# =====================================

@router.get("/inventory/manage", response_class=HTMLResponse)
async def manage_inventory(
    request: Request,
    search: str | None = None,
    page: int = 1,
    category_id: str | None = None,
    current_user: User = Depends(get_current_user_from_cookie),
    db: Session = Depends(get_db),
):
    limit = 10
    skip = (page - 1) * limit
    cat_id = int(category_id) if category_id and category_id.strip() else None

    items = crud.get_items(
        db, skip=skip, limit=limit, created_by=current_user.user_id
    )

    prev_page = page - 1 if page > 1 else None
    next_page = page + 1 if len(items) == limit else None

    categories = crud.get_categories(db)
    categories_data = [
        {"category_id": cat.category_id, "name": cat.name} for cat in categories
    ]
    return templates.TemplateResponse(
        "manage_inventory.html",
        {
            "request": request,
            "current_user": current_user,
            "limit": limit,
            "prev_page": prev_page,
            "next_page": next_page,
            "search": search,
            "items": items,
            "categories": categories_data,
        },
    )

# =====================================
# Inventory: View (Huy muốn bỏ tiền khác → tiền CAD mặc định)
# =====================================

@router.get("/inventory/view", response_class=HTMLResponse)
async def view_inventory(
    request: Request,
    search: str | None = None,
    category_id: str | None = None,
    page: int = 1,
    current_user: User = Depends(get_current_user_from_cookie),
    db: Session = Depends(get_db),
):
    limit = 10
    skip = (page - 1) * limit
    search = search.strip() if search else None
    cat_id = int(category_id) if category_id and category_id.strip() else None

    items = crud.get_items(
        db, skip=skip, limit=limit, search=search, created_by=current_user.user_id
    )

    prev_page = page - 1 if page > 1 else None
    next_page = page + 1 if len(items) == limit else None

    categories = crud.get_categories(db)

    return templates.TemplateResponse(
        "view_inventory.html",
        {
            "request": request,
            "current_user": current_user,
            "items": items,
            "prev_page": prev_page,
            "next_page": next_page,
            "page": page,
            "search": search,
            "selected_category": cat_id,
            "currency": "VND",
            "categories": categories,
        },
    )

# =====================================
# Inventory: Add / Edit / Delete
# =====================================

@router.post("/inventory/add", response_class=RedirectResponse)
async def add_inventory_item(
    request: Request,
    name: str = Form(..., max_length=100),
    description: str = Form("", max_length=255),
    quantity: int = Form(...),
    price: float = Form(...),
    category: str = Form(...),
    category_id: str = Form(""),
    supplier: str = Form("", max_length=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie),
):
    if category_id:
        cat_id = int(category_id)
    else:
        existing_cat = db.query(Category).filter(Category.name == category).first()
        if existing_cat:
            cat_id = existing_cat.category_id
        else:
            new_cat = crud.create_category(
                db, schemas.CategoryCreate(name=category, description="")
            )
            cat_id = new_cat.category_id

    item_data = schemas.InventoryItemCreate(
        name=name,
        description=description,
        quantity=quantity,
        price=price,
        supplier=supplier,
        category_id=cat_id,
        created_by=current_user.user_id,
    )
    crud.create_item(db, item_data)
    return RedirectResponse(
        url="/inventory/manage", status_code=status.HTTP_302_FOUND
    )


@router.post("/inventory/edit/{item_id}", response_class=RedirectResponse)
async def edit_inventory_item(
    item_id: int,
    request: Request,
    name: str = Form(..., max_length=100),
    description: str = Form("", max_length=255),
    quantity: int = Form(...),
    price: float = Form(...),
    category: str = Form(""),
    category_id: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie),
):
    item = crud.get_item_by_user(db, item_id, current_user.user_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Item not found"
        )

    if category.strip():
        existing_cat = db.query(Category).filter(Category.name == category).first()
        if existing_cat:
            cat_id = existing_cat.category_id
        else:
            new_cat = crud.create_category(
                db, schemas.CategoryCreate(name=category, description="")
            )
            cat_id = new_cat.category_id
    else:
        cat_id = int(category_id)

    updates = schemas.InventoryItemUpdate(
        name=name,
        description=description,
        quantity=quantity,
        price=price,
        category_id=cat_id,
    )
    crud.update_item(db, item, updates)
    return RedirectResponse(
        url="/inventory/manage", status_code=status.HTTP_302_FOUND
    )


@router.get("/inventory/delete/{item_id}", response_class=RedirectResponse)
async def delete_inventory_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie),
):
    item = crud.get_item_by_user(db, item_id, current_user.user_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Item not found"
        )
    crud.delete_item(db, item_id)
    return RedirectResponse(
        url="/inventory/manage", status_code=status.HTTP_302_FOUND
    )

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

    category_data: dict[str, int] = {}
    for item in items:
        cat_name = item.category.name if item.category else "uncategorized"
        category_data[cat_name] = 1 + category_data.get(cat_name, 0)

    category_labels = list(category_data.keys())
    category_counts = list(category_data.values())

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

    low_stock_items = [item for item in items if item.quantity < 10]

    supplier_names: list[str] = []
    for item in items:
        if item.suppliers:
            first_supplier = item.suppliers[0]
            supplier = first_supplier.supplier
            supplier_names.append(supplier.name)

    unique_suppliers = len(set(supplier_names))
    supplier_counts: dict[str, int] = {}
    for s in supplier_names:
        supplier_counts[s] = 1 + supplier_counts.get(s, 0)

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
                "unique_suppliers": unique_suppliers,
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
            "current_user": current_user,   # FIX QUAN TRỌNG
        },
    )


@router.post("/orders/create")
async def create_order_ui(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie),
    item_id: list[int] = Form(...),
    quantity: list[int] = Form(...),
    price: list[float] = Form(...),
):
    items_data: list[schemas.OrderItemCreate] = []
    for i in range(len(item_id)):
        items_data.append(
            schemas.OrderItemCreate(
                item_id=item_id[i],
                quantity=quantity[i],
                price=price[i],
            )
        )

    order_data = schemas.OrderCreate(items=items_data)
    crud.create_order(db, current_user.user_id, order_data)

    return RedirectResponse(url="/orders", status_code=303)
