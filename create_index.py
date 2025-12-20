from app.database import engine
from sqlalchemy import text

sql = text("""
CREATE UNIQUE INDEX IF NOT EXISTS ux_inventory_items_sku
ON inventory_items (sku);
""")

with engine.connect() as conn:
    conn.execute(sql)
    conn.commit()

print("✅ UNIQUE INDEX sku created")
