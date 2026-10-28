from typing import Dict, List, Optional, Set
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Query as SAQuery
from sqlalchemy.orm import Session
from mysite import get_current_user, get_db, require_roles
from mysite import City, Order, OrderStatus, Product, User, UserStatus
from mysite import OrderInputSchema, OrderOutSchema, OrderStatusUpdateSchema

order_router = APIRouter(prefix="/order", tags=["order"])

S = OrderStatus


TRANSITIONS: Dict[OrderStatus, Set[OrderStatus]] = {
    S.created: {S.paid, S.cancelled},
    S.paid: {S.processing, S.cancelled},
    S.processing: {S.shipped, S.cancelled},
    S.shipped: {S.delivered},
    S.delivered: set(),
    S.cancelled: set()}


ROLE_TARGETS: Dict[UserStatus, Set[OrderStatus]] = {
    UserStatus.manager: {S.paid, S.processing, S.shipped, S.delivered, S.cancelled},
    UserStatus.courier: {S.shipped, S.delivered},
    UserStatus.buyer: {S.cancelled},
    UserStatus.seller: set()}

BUYER_CANCELLABLE = {S.created, S.paid}
COURIER_VISIBLE = {S.processing, S.shipped, S.delivered}


def _visible(query: SAQuery, user: User):
    if user.status == UserStatus.manager:
        return query
    if user.status == UserStatus.courier:
        return query.filter(Order.status.in_(COURIER_VISIBLE))
    return query.filter(Order.user_id == user.id)


@order_router.post("/", response_model=OrderOutSchema, status_code=201)
def create_order(
    data: OrderInputSchema,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserStatus.buyer))):
    if db.get(City, data.city_id) is None:
        raise HTTPException(status_code=404, detail="City not found")


    product = (
        db.query(Product).filter(Product.id == data.product_id).with_for_update().first())
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    if product.stock < data.quantity:
        raise HTTPException(status_code=409, detail=f"Not enough stock (available: {product.stock})")

    product.stock -= data.quantity
    order = Order(
        product_id=product.id,
        user_id=user.id,
        city_id=data.city_id,
        quantity=data.quantity,
        unit_price=product.price,
        total_price=round(product.price * data.quantity, 2),
        status=OrderStatus.created,
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


@order_router.get("/", response_model=List[OrderOutSchema])
def list_order(
    status: Optional[OrderStatus] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = _visible(db.query(Order), user)
    if status is not None:
        query = query.filter(Order.status == status)
    return query.order_by(Order.id.desc()).limit(limit).offset(offset).all()


@order_router.get("/{order_id}", response_model=OrderOutSchema)
def detail_order(
    order_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    order = _visible(db.query(Order), user).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@order_router.patch("/{order_id}/status", response_model=OrderOutSchema)
def update_order_status(
    order_id: int,
    data: OrderStatusUpdateSchema,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    order = (
        _visible(db.query(Order), user)
        .filter(Order.id == order_id)
        .with_for_update()
        .first()
    )
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    target = data.status
    if target not in ROLE_TARGETS.get(user.status, set()):
        raise HTTPException(status_code=403, detail="Your role cannot set this status")
    if user.status == UserStatus.buyer and order.status not in BUYER_CANCELLABLE:
        raise HTTPException(status_code=403, detail="Order can no longer be cancelled by buyer")
    if target not in TRANSITIONS[order.status]:
        raise HTTPException(
            status_code=409, detail=f"Cannot move order from {order.status.value} to {target.value}"
        )

    if target == OrderStatus.cancelled:
        product = (
            db.query(Product).filter(Product.id == order.product_id).with_for_update().first()
        )
        product.stock += order.quantity

    order.status = target
    db.commit()
    db.refresh(order)
    return order