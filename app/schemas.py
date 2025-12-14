from pydantic import BaseModel, condecimal, Field
from datetime import datetime
from decimal import Decimal
from typing import List, Annotated, ForwardRef

SupplierRef = ForwardRef("Supplier")


# Category

class CategoryBase(BaseModel):
    name: str
    description: str | None = None

# # keeping this separate will allow for future modifications should I decide to add more. For now it extends from CategoryBase
class CategoryCreate(CategoryBase):
    pass

class CategoryUpdate(BaseModel):
    name: str | None = None
    description: str | None = None

class Category(CategoryBase):
    category_id: int
    created_at: datetime

    # used so that SQLAlchemy models can be converted to Pydantic objects easily
    class Config:
        orm_mode = True
    

# Inventory Item

class InventoryItemBase(BaseModel):
    name: str
    description: str | None = None
    quantity: int
    price: Annotated[Decimal, condecimal(max_digits=10, decimal_places=2)]


class InventoryItemCreate(InventoryItemBase):
    category_id: int
    created_by: int 
    supplier: str | None = None

class InventoryItemUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    quantity: int | None = None
    price: Annotated[Decimal, condecimal(max_digits=10, decimal_places=2)]  | None = None
    category_id: int | None = None


class InventoryItem(InventoryItemBase):
    item_id: int
    created_by: int
    created_at: datetime
    updated_at: datetime
    category: Category
    suppliers: List["Supplier"] = [] 

    class Config:
        orm_mode = True


# Supplier

class SupplierBase(BaseModel):
    name: str
    contact_details: str | None = None

# keeping this separate will allow for future modifications should I decide to add more. For now it extends from SupplierBase
class SupplierCreate(SupplierBase):
    pass

class SupplierUpdate(BaseModel):
    name: str | None = None
    contact_details: str | None = None

class Supplier(SupplierBase):
    supplier_id: int
    created_at: datetime

    class Config:
        orm_mode = True


# User

class UserBase(BaseModel):
    username: str
    role: str

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    username: str | None = None
    role: str | None = None
    
class User(UserBase):
    user_id: int
    created_at: datetime

    class Config:
        orm_mode = True


class UserPasswordUpdate(BaseModel):
    old_password: str = Field(..., min_length=8, description="Current password")
    new_password: str = Field(..., min_length=8, description="New password to be set")

    class Config:
        orm_mode = True

InventoryItem.model_rebuild()
class OrderItemBase(BaseModel):
    item_id: int
    quantity: int
    price: float


class OrderItemCreate(OrderItemBase):
    pass


class OrderItem(OrderItemBase):
    id: int

    class Config:
        from_attributes = True
class OrderBase(BaseModel):
    status: str | None = "pending"


class OrderCreate(BaseModel):
    items: list[OrderItemCreate]


class Order(OrderBase):
    order_id: int
    created_at: datetime
    created_by: int
    items: list[OrderItem]

    class Config:
        from_attributes = True
