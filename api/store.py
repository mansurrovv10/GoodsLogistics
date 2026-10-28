from fastapi import APIRouter, HTTPException, Depends
from mysite import get_current_user
from mysite import Store, User, UserStatus
from mysite import StoreInputSchema, StoreOutSchema
from mysite import SessionLocal
from sqlalchemy.orm import Session
from typing import List

store_router = APIRouter(prefix="/store", tags=["store"])


async def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@store_router.post('/', response_model=StoreOutSchema)
async def create_store(
    store: StoreInputSchema,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    if user.status not in (UserStatus.seller, UserStatus.manager):
        raise HTTPException(
            status_code=403,
            detail=f"Only seller or manager can create a store. Your role: {user.status.value}")

    db_store = Store(**store.model_dump())
    db.add(db_store)
    db.commit()
    db.refresh(db_store)
    return db_store


@store_router.get("/", response_model=List[StoreOutSchema])
async def list_store(db: Session = Depends(get_db)):
    return db.query(Store).all()


@store_router.get("/{store_id}", response_model=StoreOutSchema)
async def detail_store(store_id: int, db: Session = Depends(get_db)):
    store = db.query(Store).filter(Store.id == store_id).first()
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")
    return store


@store_router.put("/{store_id}", response_model=dict)
async def update_store(
    store_id: int,
    store: StoreInputSchema,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    if user.status not in (UserStatus.seller, UserStatus.manager):
        raise HTTPException(
            status_code=403,
            detail=f"Only seller or manager can update a store. Your role: {user.status.value}")

    db_store = db.query(Store).filter(Store.id == store_id).first()
    if not db_store:
        raise HTTPException(status_code=404, detail="Store not found")

    for store_key, store_value in store.model_dump().items():
        setattr(db_store, store_key, store_value)

    db.commit()
    db.refresh(db_store)
    return {'message': 'Store updated successfully'}


@store_router.delete("/{store_id}", response_model=dict)
async def delete_store(
    store_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    if user.status not in (UserStatus.seller, UserStatus.manager):
        raise HTTPException(
            status_code=403,
            detail=f"Only seller or manager can delete a store. Your role: {user.status.value}")

    db_store = db.query(Store).filter(Store.id == store_id).first()
    if not db_store:
        raise HTTPException(status_code=404, detail="Store not found")

    db.delete(db_store)
    db.commit()

    return {'message': 'Store deleted successfully'}