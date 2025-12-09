from datetime import timedelta
from fastapi import APIRouter, Request, Form, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import jwt

from app import models, schemas, crud
from app.database import get_db
from app import crud, schemas
from app.models import User, Category, InventoryItem, Supplier
from app.routes.auth import create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES, SECRET_KEY, ALGORITHM
from app.currency_utils import get_exchange_rate
from app.crud import get_item_by_user 

import os

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")  # fallback if not set

if not SECRET_KEY:
    raise RuntimeError("Missing SECRET_KEY in environment")

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request" : request}) # loads index.html aka home page

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request" : request}) # loads login.html page


@router.post("/login", response_class=HTMLResponse)
async def login_user(
    request: Request,
    username: str = Form(..., max_length=50), # extracts username from submitted form
    password: str = Form(..., max_length=100), # extracts password from submitted form
    db: Session = Depends(get_db)
):  
    # check user credentials from db
    user = db.query(User).filter(User.username == username).first()
    # if username or password not correct, load login.html page with error message
    if not user or not crud.pwd_context.verify(password, user.password):
        return templates.TemplateResponse("login.html", {"request" : request, "error" : "Invalid Credentials"})
    
    # create a JWT token 
    token = create_access_token(
        data={'sub': user.username},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    # create a response and set token in a cookie
    response = RedirectResponse(url="/profile", status_code=status.HTTP_302_FOUND)
    response.set_cookie(key="access_token", value=token, httponly=True)
    return response


@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request" : request}) # loads registration page


@router.post("/register", response_class=HTMLResponse)
async def register_user(
    request: Request,
    username: str = Form(..., max_length=50),
    password: str = Form(..., max_length=100),
    role:  str = Form(..., max_length=20),
    db: Session = Depends(get_db)
):
    # we first check if the user exists
    exisiting_user = db.query(User).filter(User.username == username).first()
    if exisiting_user:
        return templates.TemplateResponse("register.html", {"request" : request, "error" : "User already registered"})
    
    # now we can create the user 
    user_in = schemas.UserCreate(username=username, password=password, role=role)
    try:
        crud.create_user(db, user_in)
    except Exception as e:
        return templates.TemplateResponse("register.html", {"request" : request, "error" : f"Registration failed: {str(e)}"})
    
    # redirect to login page once user reigsters their account
    response = RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    return response

#cookie based dependancy. Retrieves token from the requests cookies (instead of expecting authorization header)
def get_current_user_from_cookie(request: Request, db: Session = Depends(get_db)) -> User:
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if not username:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


# route to user profile page
@router.get("/profile", response_class=HTMLResponse)
async def profile_page(request: Request, current_user: schemas.User = Depends(get_current_user_from_cookie)):
    return templates.TemplateResponse("profile.html", {"request" : request, "current_user" : current_user})

# logout route to redirect user to login page after they logout
@router.get("/logout")
async def logout(_request: Request):
    response = RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    response.delete_cookie("access_token")
    return response


@router.get("/inventory/manage", response_class=HTMLResponse)
async def manage_inventory(
    request: Request,
    search: str | None = None,
    page: int = 1,
    category_id: str | None = None, 
    current_user: User = Depends(get_current_user_from_cookie), 
    db: Session = Depends(get_db)
    ):
        limit = 10
        skip = (page - 1) * limit
        cat_id = int(category_id) if category_id and category_id.strip() else None 

        items = crud.get_items(db, skip=skip, limit=limit, created_by=current_user.user_id)

        prev_page = page - 1 if page > 1 else None
        next_page = page + 1 if len(items) == limit else None

        categories = crud.get_categories(db)
        categories_data = [{"category_id": cat.category_id, "name": cat.name} for cat in categories]
        return templates.TemplateResponse("manage_inventory.html", {
            "request": request, 
            "current_user": current_user, 
            "limit" : limit,
            "prev_page" : prev_page,
            "next_page" : next_page,
            "search": search,
            "items": items,
            "categories": categories_data
        })


@router.get("/inventory/view", response_class=HTMLResponse)
async def view_inventory(
    request: Request, 
    search: str | None = None, 
    category_id: str | None = None,
    currency: str = "CAD", 
    page: int = 1, 
    current_user: User = Depends(get_current_user_from_cookie), 
    db: Session = Depends(get_db)
):
    limit = 10
    skip = (page - 1) * limit
    search = search.strip() if search else None
    cat_id = int(category_id) if category_id and category_id.strip() else None # convert category_id to int if provided and is non-empty; otherwise we can set to None

    items = crud.get_items(db, skip=skip, limit=limit, search=search, created_by=current_user.user_id)

    exchange_rate = 1.0
    if currency != "CAD":
        exchange_rate = await get_exchange_rate("CAD", currency) # get exchange rate
    
    # apply the exchange rate to item prices dynamically
    for item in items:
        item.price = float(item.price) * exchange_rate

    prev_page = page - 1 if page > 1 else None
    next_page = page + 1 if len(items) == limit else None

    categories = crud.get_categories(db)

    return templates.TemplateResponse("view_inventory.html", {
        "request" : request,
        "current_user" : current_user,
        "items" : items,
        "prev_page" : prev_page,
        "next_page" : next_page,
        "page" : page,
        "search" : search,
        "selected_category" : cat_id,
        "currency" : currency,
        "exchange_rate" : exchange_rate,
        "categories" : categories   
    })

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
    current_user: User = Depends(get_current_user_from_cookie)
):
    
    if category_id:
        cat_id = int(category_id)
    else:
        
        existing_cat = db.query(Category).filter(Category.name == category).first()
        if existing_cat:
            cat_id = existing_cat.category_id
        else:
           
            new_cat = crud.create_category(db, schemas.CategoryCreate(name=category, description=""))
            cat_id = new_cat.category_id

    item_data = schemas.InventoryItemCreate(
        name=name,
        description=description,
        quantity=quantity,
        price=price,
        supplier=supplier,
        category_id=cat_id,
        created_by=current_user.user_id
    )
    crud.create_item(db, item_data)
    return RedirectResponse(url="/inventory/manage", status_code=status.HTTP_302_FOUND)


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
    current_user: User = Depends(get_current_user_from_cookie)
):
    item = crud.get_item_by_user(db, item_id, current_user.user_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    
    
    if category.strip():  
        
        existing_cat = db.query(Category).filter(Category.name == category).first()
        if existing_cat:
            cat_id = existing_cat.category_id
        else:
            
            new_cat = crud.create_category(db, schemas.CategoryCreate(name=category, description=""))
            cat_id = new_cat.category_id
    else:
        
        cat_id = int(category_id)
    
    updates = schemas.InventoryItemUpdate(
        name=name,
        description=description,
        quantity=quantity,
        price=price,
        category_id=cat_id
    )
    crud.update_item(db, item, updates)
    return RedirectResponse(url="/inventory/manage", status_code=status.HTTP_302_FOUND)


@router.get("/inventory/delete/{item_id}", response_class=RedirectResponse)
async def delete_inventory_item(
    item_id: int, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user_from_cookie)
):
    item = crud.get_item_by_user(db, item_id, current_user.user_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    crud.delete_item(db, item_id)
    return RedirectResponse(url="/inventory/manage", status_code=status.HTTP_302_FOUND)


# dashboard route

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user_from_cookie)):
    items = db.query(models.InventoryItem).filter(models.InventoryItem.created_by == current_user.user_id).all()

    # total inventory value
    total_inventory_value = sum(item.quantity * float(item.price) for item in items)

    # top categories
    category_data = {} # {'category name': 'count'}
    for item in items:
        cat_name = item.category.name if item.category else "uncategorized"
        category_data[cat_name] = 1 + category_data.get(cat_name, 0)

    category_labels = list(category_data.keys()) # keys aka cat names
    category_counts = list(category_data.values()) # count

    # price distribution buckets
    price_ranges = ["0–50", "51–100", "101–200", "201–500", "500+"]
    price_counts = [0,0,0,0,0]
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

    # low stock items
    low_stock_items = [item for item in items if item.quantity < 10] # if item quantity less than 10, the item stock is low

    # supplier overview
    supplier_names = []
    for item in items:
        if item.suppliers: # check if item has suppliers
            first_supplier = item.suppliers[0] # get first ItemSupplier object in db in that first row
            supplier = first_supplier.supplier # access the supplier object
            supplier_name = supplier.name # get the name of the supplier
            supplier_names.append(supplier_name)
    
    unique_suppliers = len(set(supplier_names)) 
    supplier_counts = {} # {'supplier names' : '# of items each supplier provides'}
    for s in supplier_names:
        supplier_counts[s] = 1 + supplier_counts.get(s, 0)
    
    top_suppliers = sorted(supplier_counts.items(), key=lambda x: x[1], reverse=True)[:5] # x = ("Supplier Name", item count). Sorts based on the count in the tuple, return top 5 supplier pairs by item count
    
    # recently added items
    recent_items = sorted(items, key=lambda x: x.created_at, reverse=True)[:5]

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "current_user": current_user,
        "total_inventory_value": total_inventory_value,
        "category_labels" : category_labels,
        "category_counts" : category_counts,
        "price_ranges": price_ranges,
        "price_counts" : price_counts,
        "low_stock_items": low_stock_items,
        "recent_items": recent_items,
        "supplier_overview": {
            "unique_suppliers": unique_suppliers,
            "top_suppliers" : top_suppliers
        }
    })