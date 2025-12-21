from sqlalchemy import create_engine, text
import pandas as pd

# SQLite
sqlite_engine = create_engine("sqlite:///InventoryManagement.db")

# PostgreSQL
postgres_engine = create_engine(
    "postgresql+psycopg2://inventory_thtu_user:CLfmMkaaetP97axBAjuXHvdfdxy93vyP@dpg-d53covm3jp1c738imcj0-a.singapore-postgres.render.com/inventory_thtu"
)

tables = [
    "users",
    "categories",
    "suppliers",
    "inventory_items",
    "orders",
    "order_items",
    "item_suppliers"
]

with postgres_engine.connect() as conn:
    for table in tables:
        print(f"🧹 Xóa bảng {table} nếu tồn tại...")
        conn.execute(text(f'DROP TABLE IF EXISTS "{table}" CASCADE'))
    conn.commit()

print("🚀 Bắt đầu migrate dữ liệu...\n")

for table in tables:
    print(f"➡️ Đang chuyển bảng {table}...")
    df = pd.read_sql(f"SELECT * FROM {table}", sqlite_engine)
    df.to_sql(table, postgres_engine, if_exists="append", index=False)
    print(f"✅ Xong bảng {table}")

print("\n🎉 MIGRATE SQLITE → POSTGRESQL HOÀN TẤT")
