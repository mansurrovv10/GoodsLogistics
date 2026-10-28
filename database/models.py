from .db import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import (
    Integer, String, Enum, Date, ForeignKey, Text, Boolean, DateTime, Float,
    CheckConstraint, UniqueConstraint,
)
from typing import Optional, List
from datetime import date, datetime
from enum import Enum as PyEnum


class UserStatus(str, PyEnum):
    buyer = "buyer"
    seller = "seller"
    manager = "manager"
    courier = "courier"


class OrderStatus(str, PyEnum):
    created = "created"
    paid = "paid"
    processing = "processing"
    shipped = "shipped"
    delivered = "delivered"
    cancelled = "cancelled"


class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String, unique=True)
    email: Mapped[str] = mapped_column(String, unique=True)
    password: Mapped[str] = mapped_column(String)
    status: Mapped[UserStatus] = mapped_column(Enum(UserStatus), default=UserStatus.buyer)
    created_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    reviews: Mapped[List["Review"]] = relationship("Review", back_populates="user",
                                                   cascade="all, delete-orphan")
    orders: Mapped[List["Order"]] = relationship("Order", back_populates="user")
    delivers: Mapped[List["Deliver"]] = relationship("Deliver", back_populates="user",
                                                     cascade="all, delete-orphan")
    refresh_tokens: Mapped[List["RefreshToken"]] = relationship("RefreshToken", back_populates="user",
                                                                cascade="all, delete-orphan")


class RefreshToken(Base):
    __tablename__ = 'refresh_token'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    token: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship("User", back_populates="refresh_tokens")


class Category(Base):
    __tablename__ = 'categories'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    category_name: Mapped[str] = mapped_column(String, unique=True)

    stores: Mapped[List["Store"]] = relationship("Store", back_populates="category",
                                                 cascade="all, delete-orphan")


class Store(Base):
    __tablename__ = 'stores'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    store_name: Mapped[str] = mapped_column(String, unique=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"))
    store_image: Mapped[str] = mapped_column(String)

    category: Mapped["Category"] = relationship("Category", back_populates="stores")
    products: Mapped[List["Product"]] = relationship("Product", back_populates="store",
                                                     cascade="all, delete-orphan")
    reviews: Mapped[List["Review"]] = relationship("Review", back_populates="store",
                                                   cascade="all, delete-orphan")


class Product(Base):
    __tablename__ = 'products'
    __table_args__ = (
        UniqueConstraint("store_id", "product_name", name="uq_product_store_name"),
        CheckConstraint("stock >= 0", name="check_stock_non_negative"),
        CheckConstraint("price > 0", name="check_price_positive"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    store_id: Mapped[int] = mapped_column(ForeignKey("stores.id"))
    product_name: Mapped[str] = mapped_column(String)  # unique алынды: дүкөн ичинде гана уникалдуу
    price: Mapped[float] = mapped_column(Float)
    stock: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    description: Mapped[str] = mapped_column(Text, default="")
    is_original: Mapped[bool] = mapped_column(Boolean, default=False)
    create_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    store: Mapped["Store"] = relationship("Store", back_populates="products")
    orders: Mapped[List["Order"]] = relationship("Order", back_populates="product")


class Review(Base):
    __tablename__ = 'reviews'
    __table_args__ = (
        CheckConstraint("stars BETWEEN 1 AND 5", name="check_stars_range"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    store_id: Mapped[int] = mapped_column(ForeignKey("stores.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    text: Mapped[str] = mapped_column(Text)
    stars: Mapped[int] = mapped_column(Integer)
    created_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    store: Mapped["Store"] = relationship("Store", back_populates="reviews")
    user: Mapped["User"] = relationship("User", back_populates="reviews")


class City(Base):
    __tablename__ = 'cities'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    city_name: Mapped[str] = mapped_column(String, unique=True)

    orders: Mapped[List["Order"]] = relationship("Order", back_populates="city")
    warehouses: Mapped[List["Warehouse"]] = relationship("Warehouse", back_populates="city",
                                                          cascade="all, delete-orphan")


class Order(Base):
    __tablename__ = 'orders'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    city_id: Mapped[int] = mapped_column(ForeignKey("cities.id"))
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    unit_price: Mapped[float] = mapped_column(Float, default=0, server_default="0")
    total_price: Mapped[float] = mapped_column(Float)
    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus), default=OrderStatus.created, server_default=OrderStatus.created.value
    )
    created_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    product: Mapped["Product"] = relationship("Product", back_populates="orders")
    user: Mapped["User"] = relationship("User", back_populates="orders")
    city: Mapped["City"] = relationship("City", back_populates="orders")


class Warehouse(Base):
    __tablename__ = 'warehouses'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    city_id: Mapped[int] = mapped_column(ForeignKey("cities.id"))
    warehouse_code: Mapped[str] = mapped_column(String, unique=True)
    street: Mapped[str] = mapped_column(String)

    city: Mapped["City"] = relationship("City", back_populates="warehouses")
    delivers: Mapped[List["Deliver"]] = relationship("Deliver", back_populates="warehouse",
                                                     cascade="all, delete-orphan")


class Deliver(Base):
    __tablename__ = 'delivers'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    warehouse_id: Mapped[int] = mapped_column(ForeignKey("warehouses.id"))

    user: Mapped["User"] = relationship("User", back_populates="delivers")
    warehouse: Mapped["Warehouse"] = relationship("Warehouse", back_populates="delivers")