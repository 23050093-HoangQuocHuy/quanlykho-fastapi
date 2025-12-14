from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import RedirectResponse, JSONResponse
from app.database import engine, Base
from fastapi.staticfiles import StaticFiles

# --- IMPORT ROUTERS ---
from app.routes import items, categories, suppliers, auth, ui, oauth, api_dashboard
from app.routes import orders   # 🔥 Thêm dòng này


# --- CREATE DATABASE TABLES ---
Base.metadata.create_all(bind=engine)


# --- INIT APP ---
app = FastAPI(title="Inventory Management System API")


# --- GLOBAL 401 EXCEPTION HANDLER ---
@app.exception_handler(HTTPException)
async def custom_http_exception_hanlder(request: Request, exc: HTTPException):
    if exc.status_code == status.HTTP_401_UNAUTHORIZED:
        return RedirectResponse(url="/login")
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


# --- STATIC FILES ---
app.mount("/static", StaticFiles(directory="app/static"), name="static")


# --- ROUTERS ---
app.include_router(items.router, prefix="/items", tags=["Items"])
app.include_router(categories.router, prefix="/categories", tags=["Categories"])
app.include_router(suppliers.router, prefix="/suppliers", tags=["Suppliers"])
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(ui.router, prefix="", tags=["UI"])
app.include_router(oauth.router, tags=["OAuth"])
app.include_router(api_dashboard.router, tags=["API"])

# --- ADD ORDERS ROUTER ---
app.include_router(orders.router, prefix="/orders", tags=["Orders"])   # ✅ ĐÃ THÊM HOÀN CHỈNH
