from fastapi import APIRouter, HTTPException, Depends
from mysite import require_roles
from mysite import Deliver, UserStatus
from mysite import DeliverInputSchema, DeliverOutSchema
from mysite import SessionLocal
from sqlalchemy.orm import Session
from typing import List

deliver_router = APIRouter(prefix="/deliver", tags=["deliver"])

ManagerOnly = Depends(require_roles(UserStatus.manager))
StaffOnly = Depends(require_roles(UserStatus.manager, UserStatus.courier))


async def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@deliver_router.post('/', response_model=DeliverOutSchema, dependencies=[ManagerOnly])
async def create_deliver(deliver: DeliverInputSchema, db: Session = Depends(get_db)):
    db_deliver = Deliver(**deliver.model_dump())
    db.add(db_deliver)
    db.commit()
    db.refresh(db_deliver)
    return db_deliver


@deliver_router.get("/", response_model=List[DeliverOutSchema], dependencies=[StaffOnly])
async def list_deliver(db: Session = Depends(get_db)):
    return db.query(Deliver).all()


@deliver_router.get("/{deliver_id}", response_model=DeliverOutSchema, dependencies=[StaffOnly])
async def detail_deliver(deliver_id: int, db: Session = Depends(get_db)):
    deliver = db.query(Deliver).filter(Deliver.id == deliver_id).first()
    if not deliver:
        raise HTTPException(status_code=404, detail="Deliver not found")
    return deliver


@deliver_router.put("/{deliver_id}", response_model=dict, dependencies=[ManagerOnly])
async def update_deliver(
    deliver_id: int,
    deliver: DeliverInputSchema,
    db: Session = Depends(get_db)
):
    db_deliver = db.query(Deliver).filter(Deliver.id == deliver_id).first()
    if not db_deliver:
        raise HTTPException(status_code=404, detail="Deliver not found")

    for deliver_key, deliver_value in deliver.model_dump().items():
        setattr(db_deliver, deliver_key, deliver_value)

    db.commit()
    db.refresh(db_deliver)
    return {'message': 'Deliver updated successfully'}


@deliver_router.delete("/{deliver_id}", response_model=dict, dependencies=[ManagerOnly])
async def delete_deliver(deliver_id: int, db: Session = Depends(get_db)):
    db_deliver = db.query(Deliver).filter(Deliver.id == deliver_id).first()
    if not db_deliver:
        raise HTTPException(status_code=404, detail="Deliver not found")

    db.delete(db_deliver)
    db.commit()

    return {'message': 'Deliver deleted successfully'}