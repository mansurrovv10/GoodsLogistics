from fastapi import APIRouter, HTTPException, Depends
from mysite import get_current_user
from mysite import Warehouse, User, UserStatus
from mysite import WarehouseInputSchema, WarehouseOutSchema
from mysite import SessionLocal
from sqlalchemy.orm import Session
from typing import List

warehouse_router = APIRouter(prefix="/warehouse", tags=["warehouse"])


async def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@warehouse_router.post('/', response_model=WarehouseOutSchema)
async def create_warehouse(
    warehouse: WarehouseInputSchema,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    if user.status != UserStatus.manager:
        raise HTTPException(
            status_code=403,
            detail=f"Only manager can create a warehouse. Your role: {user.status.value}")

    db_warehouse = Warehouse(**warehouse.model_dump())
    db.add(db_warehouse)
    db.commit()
    db.refresh(db_warehouse)
    return db_warehouse


@warehouse_router.get("/", response_model=List[WarehouseOutSchema])
async def list_warehouse(db: Session = Depends(get_db)):
    return db.query(Warehouse).all()


@warehouse_router.get("/{warehouse_id}", response_model=WarehouseOutSchema)
async def detail_warehouse(warehouse_id: int, db: Session = Depends(get_db)):
    warehouse = db.query(Warehouse).filter(Warehouse.id == warehouse_id).first()
    if not warehouse:
        raise HTTPException(status_code=404, detail="Warehouse not found")
    return warehouse


@warehouse_router.put("/{warehouse_id}", response_model=dict)
async def update_warehouse(
    warehouse_id: int,
    warehouse: WarehouseInputSchema,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    if user.status != UserStatus.manager:
        raise HTTPException(
            status_code=403,
            detail=f"Only manager can update a warehouse. Your role: {user.status.value}")

    db_warehouse = db.query(Warehouse).filter(Warehouse.id == warehouse_id).first()
    if not db_warehouse:
        raise HTTPException(status_code=404, detail="Warehouse not found")

    for warehouse_key, warehouse_value in warehouse.model_dump().items():
        setattr(db_warehouse, warehouse_key, warehouse_value)

    db.commit()
    db.refresh(db_warehouse)
    return {'message': 'Warehouse updated successfully'}


@warehouse_router.delete("/{warehouse_id}", response_model=dict)
async def delete_warehouse(
    warehouse_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    if user.status != UserStatus.manager:
        raise HTTPException(
            status_code=403,
            detail=f"Only manager can delete a warehouse. Your role: {user.status.value}")

    db_warehouse = db.query(Warehouse).filter(Warehouse.id == warehouse_id).first()
    if not db_warehouse:
        raise HTTPException(status_code=404, detail="Warehouse not found")

    db.delete(db_warehouse)
    db.commit()

    return {'message': 'Warehouse deleted successfully'}