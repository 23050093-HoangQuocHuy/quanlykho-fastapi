# Hệ thống Quản Lý Kho – FastAPI
## 1. Giới thiệu
Hệ thống quản lý kho được xây dựng bằng FastAPI, quản lý kho hàng, nhà cung cấp và tạo đơn hàng.

## 2. Công nghệ sử dụng
- Python 3.10+
- FastAPI
- SQLAlchemy
- SQLite
- Jinja2
- Bootstrap

## 3. Chức năng chính
- Quản lý danh mục sản phẩm
- Quản lý nhà cung cấp
- Tạo và quản lý đơn hàng
- Thống kê tổng quan (dashboard)

## 4. Thiết lập và cài đặt

### Sao chép

``` bash
git clone https://github.com/23050093-HoangQuocHuy/quanlykho-fastapi
cd quanlykho-fastapi
```

### 5. Cài đặt các gói

``` bash
python -m venv .venv
.\.venv\Scripts\Activate
pip install -r requirements.txt

```

### 6. Chạy ứng dụng

``` bash
python -m uvicorn app.main:app --reload --port 8500
```

Visit:

    http://127.0.0.1:8500

------------------------------------------------------------------------

## 7. Biến môi trường (.env)

``` env
SECRET_KEY=your_secret_key_here

```

------------------------------------------------------------------------

## 8. Đặc trưng

-   CRUD Inventory (Products, Categories, Suppliers)
-   Orders system (auto stock deduction)
-   Dashboard with charts
-   Authentication (JWT Cookies)
-   Google OAuth Login
-   VND currency only
-   TailwindCSS UI
-   Dark Mode
-   Pagination, search, filtering

------------------------------------------------------------------------

## 9. Giao diện người dùng

  Route               Description
  ------------------- --------------
  /                   Home
  /login              Login
  /register           Register
  /profile            User profile
  /dashboard          Dashboard
  /inventory/manage   Manage stock
  /inventory/view     View stock
  /orders             Orders UI

------------------------------------------------------------------------

## 10. Tài liệu API

Swagger:

    http://127.0.0.1:8500/docs

------------------------------------------------------------------------

## 11. Bảng ERD

ERD-Image.png

------------------------------------------------------------------------

## 12. Những cải tiến trong tương lai

-  Multi-warehouse
-  Export reports
-  Activity logs
-  Supplier analytics
-  AI reorder suggestions
-  Multi-warehouse
-  stock transfers
-  SKU management