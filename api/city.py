from fastapi import APIRouter, HTTPException, Depends
from mysite import get_current_user
from mysite import City, User, UserStatus
from mysite import CityInputSchema, CityOutSchema
from mysite import SessionLocal
from sqlalchemy.orm import Session
from typing import List

city_router = APIRouter(prefix="/city", tags=["city"])


async def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@city_router.post('/', response_model=CityOutSchema)
async def create_city(
    city: CityInputSchema,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    if user.status != UserStatus.manager:
        raise HTTPException(
            status_code=403,
            detail=f"Only manager can create a city. Your role: {user.status.value}")

    db_city = City(**city.model_dump())
    db.add(db_city)
    db.commit()
    db.refresh(db_city)
    return db_city


@city_router.get("/", response_model=List[CityOutSchema])
async def list_city(db: Session = Depends(get_db)):
    return db.query(City).all()


@city_router.get("/{city_id}", response_model=CityOutSchema)
async def detail_city(city_id: int, db: Session = Depends(get_db)):
    city = db.query(City).filter(City.id == city_id).first()
    if not city:
        raise HTTPException(status_code=404, detail="City not found")
    return city


@city_router.put("/{city_id}", response_model=dict)
async def update_city(
    city_id: int,
    city: CityInputSchema,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    if user.status != UserStatus.manager:
        raise HTTPException(
            status_code=403,
            detail=f"Only manager can update a city. Your role: {user.status.value}")

    db_city = db.query(City).filter(City.id == city_id).first()
    if not db_city:
        raise HTTPException(status_code=404, detail="City not found")

    for city_key, city_value in city.model_dump().items():
        setattr(db_city, city_key, city_value)

    db.commit()
    db.refresh(db_city)
    return {'message': 'City updated successfully'}


@city_router.delete("/{city_id}", response_model=dict)
async def delete_city(
    city_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    if user.status != UserStatus.manager:
        raise HTTPException(
            status_code=403,
            detail=f"Only manager can delete a city. Your role: {user.status.value}")

    db_city = db.query(City).filter(City.id == city_id).first()
    if not db_city:
        raise HTTPException(status_code=404, detail="City not found")

    db.delete(db_city)
    db.commit()

    return {'message': 'City deleted successfully'}