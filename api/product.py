from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from mysite import get_db, require_roles
from mysite import Product, Store, UserStatus
from mysite import ProductInputSchema, ProductOutSchema
product_router = APIRouter(prefix="/product", tags=["product"])


SellerOrManager = Depends(require_roles(UserStatus.seller, UserStatus.manager))


@product_router.get("/", response_model=List[ProductOutSchema])
def list_product(
    store_id: Optional[int] = None,
    min_price: Optional[float] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0),
    q: Optional[str] = Query(None, min_length=1),
    in_stock: bool = False,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),db: Session = Depends(get_db)):
    query = db.query(Product)
    if store_id is not None:
        query = query.filter(Product.store_id == store_id)
    if min_price is not None:
        query = query.filter(Product.price >= min_price)
    if max_price is not None:
        query = query.filter(Product.price <= max_price)
    if q:
        query = query.filter(Product.product_name.ilike(f"%{q}%"))
    if in_stock:
        query = query.filter(Product.stock > 0)
    return query.order_by(Product.id).limit(limit).offset(offset).all()


@product_router.get("/{product_id}", response_model=ProductOutSchema)
def detail_product(product_id: int, db: Session = Depends(get_db)):
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@product_router.post("/", response_model=ProductOutSchema, status_code=201,
                     dependencies=[SellerOrManager])
def create_product(data: ProductInputSchema, db: Session = Depends(get_db)):
    if db.get(Store, data.store_id) is None:
        raise HTTPException(status_code=404, detail="Store not found")
    product = Product(**data.model_dump())
    db.add(product)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Product with this name already exists in the store")
    db.refresh(product)
    return product


@product_router.put("/{product_id}", response_model=ProductOutSchema,
                    dependencies=[SellerOrManager])
def update_product(product_id: int, data: ProductInputSchema, db: Session = Depends(get_db)):
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    if db.get(Store, data.store_id) is None:
        raise HTTPException(status_code=404, detail="Store not found")
    for key, value in data.model_dump().items():
        setattr(product, key, value)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Product with this name already exists in the store")
    db.refresh(product)
    return product


@product_router.delete("/{product_id}", dependencies=[SellerOrManager])
def delete_product(product_id: int, db: Session = Depends(get_db)):
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    try:
        db.delete(product)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Product has orders and cannot be deleted")
    return {"message": "Product deleted successfully"}