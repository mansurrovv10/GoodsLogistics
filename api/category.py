from fastapi import APIRouter, HTTPException, Depends
from mysite import get_current_user
from mysite import Category, User, UserStatus
from mysite import CategoryInputSchema, CategoryOutSchema
from mysite import SessionLocal
from sqlalchemy.orm import Session
from typing import List

category_router = APIRouter(prefix="/category", tags=["category"])


async def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@category_router.post('/', response_model=CategoryOutSchema)
async def create_category(
    category: CategoryInputSchema,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    if user.status != UserStatus.manager:
        raise HTTPException(
            status_code=403,
            detail=f"Only manager can create a category. Your role: {user.status.value}")

    db_category = Category(**category.model_dump())
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category


@category_router.get("/", response_model=List[CategoryOutSchema])
async def list_category(db: Session = Depends(get_db)):
    return db.query(Category).all()


@category_router.get("/{category_id}", response_model=CategoryOutSchema)
async def detail_category(category_id: int, db: Session = Depends(get_db)):
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category


@category_router.put("/{category_id}", response_model=dict)
async def update_category(
    category_id: int,
    category: CategoryInputSchema,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    if user.status != UserStatus.manager:
        raise HTTPException(
            status_code=403,
            detail=f"Only manager can update a category. Your role: {user.status.value}")

    db_category = db.query(Category).filter(Category.id == category_id).first()
    if not db_category:
        raise HTTPException(status_code=404, detail="Category not found")

    for category_key, category_value in category.model_dump().items():
        setattr(db_category, category_key, category_value)

    db.commit()
    db.refresh(db_category)
    return {'message': 'Category updated successfully'}


@category_router.delete("/{category_id}", response_model=dict)
async def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    if user.status != UserStatus.manager:
        raise HTTPException(
            status_code=403,
            detail=f"Only manager can delete a category. Your role: {user.status.value}")

    db_category = db.query(Category).filter(Category.id == category_id).first()
    if not db_category:
        raise HTTPException(status_code=404, detail="Category not found")
    db.delete(db_category)
    db.commit()

    return {'message': 'Category deleted successfully'}