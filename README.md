# Hệ thống quản lý kho (FastAPI + Jinja2 + TailwindCSS)

## Thiết lập và cài đặt

### Sao chép kho lưu trữ

``` bash
git clone <url_repo_cua_huy>
cd <folder>
```

### Cài đặt các gói

``` bash
pip install -r requirements.txt
```

### Chạy ứng dụng

``` bash
uvicorn app.main:app --reload
```

Visit:

    http://127.0.0.1:8000

------------------------------------------------------------------------

## Biến môi trường (.env)

``` env
SECRET_KEY=your_secret_key_here
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
REDIRECT_URI=http://localhost:8500/auth/google/callback
```

------------------------------------------------------------------------

## Đặc trưng

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

## Giao diện người dùng

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

## Tài liệu API

Swagger:

    http://127.0.0.1:8500/docs

------------------------------------------------------------------------

## Bảng ERD

ERD-Image.png

------------------------------------------------------------------------

## Những cải tiến trong tương lai

-   Export reports
-   Activity logs
-   Supplier analytics
-   AI reorder suggestions
