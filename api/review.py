from fastapi import APIRouter, HTTPException, Depends
from mysite import get_current_user, require_roles
from mysite import Review, User, UserStatus
from mysite import ReviewInputSchema, ReviewOutSchema
from mysite import SessionLocal
from sqlalchemy.orm import Session
from typing import List

review_router = APIRouter(prefix="/review", tags=["review"])


async def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@review_router.post('/', response_model=ReviewOutSchema)
async def create_review(
    review: ReviewInputSchema,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserStatus.buyer))
):
    db_review = Review(**review.model_dump(), user_id=user.id)
    db.add(db_review)
    db.commit()
    db.refresh(db_review)
    return db_review


@review_router.get("/", response_model=List[ReviewOutSchema])
async def list_review(db: Session = Depends(get_db)):
    return db.query(Review).all()


@review_router.get("/{review_id}", response_model=ReviewOutSchema)
async def detail_review(review_id: int, db: Session = Depends(get_db)):
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    return review


@review_router.put("/{review_id}", response_model=dict)
async def update_review(
    review_id: int,
    review: ReviewInputSchema,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    db_review = db.query(Review).filter(Review.id == review_id).first()
    if not db_review:
        raise HTTPException(status_code=404, detail="Review not found")
    if db_review.user_id != user.id:
        raise HTTPException(status_code=403, detail="You can edit only your own review")

    for review_key, review_value in review.model_dump().items():
        setattr(db_review, review_key, review_value)

    db.commit()
    db.refresh(db_review)
    return {'message': 'Review updated successfully'}


@review_router.delete("/{review_id}", response_model=dict)
async def delete_review(
    review_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    db_review = db.query(Review).filter(Review.id == review_id).first()
    if not db_review:
        raise HTTPException(status_code=404, detail="Review not found")
    if db_review.user_id != user.id and user.status != UserStatus.manager:
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    db.delete(db_review)
    db.commit()

    return {'message': 'Review deleted successfully'}