from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional
from datetime import datetime
from mysite import UserStatus, OrderStatus

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    status: UserStatus = UserStatus.buyer

class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    status: UserStatus
    created_date: datetime

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserUpdateSchema(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    status: Optional[UserStatus] = None


class CategoryInputSchema(BaseModel):
    category_name: str


class CategoryOutSchema(BaseModel):
    id: int
    category_name: str

    model_config = ConfigDict(from_attributes=True)


class ProductInputSchema(BaseModel):
    store_id: int
    product_name: str = Field(min_length=1)
    price: float = Field(gt=0)
    stock: int = Field(0, ge=0)
    description: str = ""
    is_original: bool = False


class ProductOutSchema(BaseModel):
    id: int
    store_id: int
    product_name: str
    price: float
    stock: int
    description: str
    is_original: bool
    create_date: datetime

    model_config = ConfigDict(from_attributes=True)


class OrderInputSchema(BaseModel):
    product_id: int
    city_id: int
    quantity: int = Field(1, ge=1, le=1000)


class OrderStatusUpdateSchema(BaseModel):
    status: OrderStatus


class OrderOutSchema(BaseModel):
    id: int
    product_id: int
    user_id: int
    city_id: int
    quantity: int
    unit_price: float
    total_price: float
    status: OrderStatus
    created_date: datetime

    model_config = ConfigDict(from_attributes=True)


class CityInputSchema(BaseModel):
    city_name: str


class CityOutSchema(BaseModel):
    id: int
    city_name: str

    model_config = ConfigDict(from_attributes=True)


class StoreInputSchema(BaseModel):
    store_name: str
    category_id: int
    store_image: str


class StoreOutSchema(BaseModel):
    id: int
    store_name: str
    category_id: int
    store_image: str

    category: Optional[CategoryOutSchema] = None

    model_config = ConfigDict(from_attributes=True)


class WarehouseInputSchema(BaseModel):
    city_id: int
    warehouse_code: str
    street: str


class WarehouseOutSchema(BaseModel):
    id: int
    city_id: int
    warehouse_code: str
    street: str

    city: Optional[CityOutSchema] = None

    model_config = ConfigDict(from_attributes=True)


class DeliverInputSchema(BaseModel):
    user_id: int
    warehouse_id: int


class DeliverOutSchema(BaseModel):
    id: int
    user_id: int
    warehouse_id: int

    model_config = ConfigDict(from_attributes=True)


class ReviewInputSchema(BaseModel):
    store_id: int
    text: str
    stars: int = Field(ge=1, le=5)


class ReviewOutSchema(BaseModel):
    id: int
    store_id: int
    user_id: int
    text: str
    stars: int
    created_date: datetime

    model_config = ConfigDict(from_attributes=True)