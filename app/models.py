from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Numeric,
    ForeignKey,
    DateTime,
    Table,
)
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime, timezone


# =========================
# ASSOCIATION TABLE
# =========================

item_suppliers = Table(
    "item_suppliers",
    Base.metadata,
    Column("id", Integer, primary_key=True, index=True),
    Column("item_id", Integer, ForeignKey("inventory_items.item_id"), nullable=False),
    Column("supplier_id", Integer, ForeignKey("suppliers.supplier_id"), nullable=False),
    Column("created_at", DateTime, default=lambda: datetime.now(timezone.utc)),
)


# =========================
# CATEGORY
# =========================

class Category(Base):
    __tablename__ = "categories"

    category_id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    items = relationship("InventoryItem", back_populates="category")


# =========================
# INVENTORY ITEM
# =========================

class InventoryItem(Base):
    __tablename__ = "inventory_items"

    item_id = Column(Integer, primary_key=True, index=True)
    sku = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text)
    quantity = Column(Integer, nullable=False)
    price = Column(Numeric(10, 2), nullable=False)

    category_id = Column(Integer, ForeignKey("categories.category_id"), nullable=False)
    created_by = Column(Integer, ForeignKey("users.user_id"), nullable=False)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    category = relationship("Category", back_populates="items")

    # ✅ MANY-TO-MANY ĐÚNG
    suppliers = relationship(
        "Supplier",
        secondary=item_suppliers,
        back_populates="items",
    )


# =========================
# SUPPLIER
# =========================

class Supplier(Base):
    __tablename__ = "suppliers"

    supplier_id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    contact_details = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    items = relationship(
        "InventoryItem",
        secondary=item_suppliers,
        back_populates="suppliers",
    )


# =========================
# USER
# =========================

class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    role = Column(String, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    items_created = relationship("InventoryItem", backref="creator")
    orders = relationship("Order", back_populates="user")


# =========================
# ORDER
# =========================

class Order(Base):
    __tablename__ = "orders"

    order_id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    status = Column(String, default="pending")
    created_by = Column(Integer, ForeignKey("users.user_id"), nullable=False)

    user = relationship("User", back_populates="orders")
    items = relationship("OrderItem", back_populates="order")


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.order_id"), nullable=False)
    item_id = Column(Integer, ForeignKey("inventory_items.item_id"), nullable=False)

    quantity = Column(Integer, nullable=False)
    price = Column(Numeric(10, 2), nullable=False)

    order = relationship("Order", back_populates="items")
    item = relationship("InventoryItem")
