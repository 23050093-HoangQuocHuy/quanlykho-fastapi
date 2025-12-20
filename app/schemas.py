from pydantic import BaseModel, condecimal, Field
from datetime import datetime
from decimal import Decimal
from typing import List, Annotated, ForwardRef, Optional

SupplierRef = ForwardRef("Supplier")

# =========================
# CATEGORY
# =========================

class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class Category(CategoryBase):
    category_id: int
    created_at: datetime

    class Config:
        orm_mode = True


# =========================
# INVENTORY ITEM (SKU)
# =========================

class InventoryItemBase(BaseModel):
    sku: str = Field(..., min_length=1, description="Stock Keeping Unit")
    name: str
    description: Optional[str] = None
    quantity: int = Field(..., ge=0)
    price: Annotated[
        Decimal,
        condecimal(max_digits=10, decimal_places=2)
    ]


class InventoryItemCreate(InventoryItemBase):
    category_id: int
    created_by: int
    supplier: Optional[str] = None


class InventoryItemUpdate(BaseModel):
    sku: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    quantity: Optional[int] = Field(None, ge=0)
    price: Optional[
        Annotated[
            Decimal,
            condecimal(max_digits=10, decimal_places=2)
        ]
    ] = None
    category_id: Optional[int] = None


class InventoryItem(InventoryItemBase):
    item_id: int
    created_by: int
    created_at: datetime
    updated_at: datetime
    category: Optional[Category] = None   
    suppliers: List["Supplier"] = []

    class Config:
        from_attributes = True



# =========================
# SUPPLIER
# =========================

class SupplierBase(BaseModel):
    name: str
    contact_details: Optional[str] = None


class SupplierCreate(SupplierBase):
    pass


class SupplierUpdate(BaseModel):
    name: Optional[str] = None
    contact_details: Optional[str] = None


class Supplier(SupplierBase):
    supplier_id: int
    created_at: datetime

    class Config:
        orm_mode = True


# =========================
# USER
# =========================

class UserBase(BaseModel):
    username: str
    role: str


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = None


class User(UserBase):
    user_id: int
    created_at: datetime

    class Config:
        orm_mode = True


class UserPasswordUpdate(BaseModel):
    old_password: str = Field(..., min_length=8)
    new_password: str = Field(..., min_length=8)

    class Config:
        orm_mode = True


# =========================
# ORDER
# =========================

InventoryItem.model_rebuild()


class OrderItemBase(BaseModel):
    item_id: int
    quantity: int = Field(..., gt=0)
    price: float


class OrderItemCreate(OrderItemBase):
    pass


class OrderItem(OrderItemBase):
    id: int

    class Config:
        from_attributes = True


class OrderBase(BaseModel):
    status: Optional[str] = "pending"


class OrderCreate(BaseModel):
    items: List[OrderItemCreate]


class Order(OrderBase):
    order_id: int
    created_at: datetime
    created_by: int
    items: List[OrderItem]

    class Config:
        from_attributes = True
