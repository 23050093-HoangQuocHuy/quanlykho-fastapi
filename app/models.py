from sqlalchemy import Column, Integer, String, Text, Numeric, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime, timezone


class Category(Base):
    __tablename__ = "categories"

    category_id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc)) # lambda ensures dynamic time sets

    # One category can have many inventory items. We can use this setup to access all inventory items that belong to a certain category
    items = relationship("InventoryItem", back_populates="category")

class InventoryItem(Base):
    __tablename__ = "inventory_items"
    
    item_id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String, index=True)
    quantity = Column(Integer)
    price = Column(Numeric)
    category_id = Column(Integer, ForeignKey("categories.category_id"), nullable=False)
    created_by = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # each inventory item belongs to exactly one category
    category = relationship("Category", back_populates="items")
    # many inventory items can have many suppliers (many-to-many relationship)
    suppliers = relationship("ItemSupplier", back_populates="item")


class Supplier(Base):
    __tablename__ = "suppliers"

    supplier_id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    contact_details = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # many suppliers can supply many inventory items (a lit of items the supplier can supply)
    items = relationship("ItemSupplier", back_populates="supplier")


class ItemSupplier(Base):
    __tablename__ = "item_suppliers"

    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(Integer, ForeignKey("inventory_items.item_id"), nullable=False)
    supplier_id = Column(Integer, ForeignKey("suppliers.supplier_id"), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    item = relationship("InventoryItem", back_populates="suppliers")
    supplier = relationship("Supplier", back_populates="items")


class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)
    role = Column(String)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # user could have created many inventory items
    items_created = relationship("InventoryItem", backref="creator")

