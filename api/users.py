from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from mysite import get_current_user, get_db, require_roles
from mysite import User, UserStatus
from mysite import UserResponse, UserUpdateSchema

user_router = APIRouter(prefix="/users", tags=["users"])

ManagerOnly = Depends(require_roles(UserStatus.manager))


@user_router.get("/", response_model=List[UserResponse], dependencies=[ManagerOnly])
def get_users(limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),db: Session = Depends(get_db)):
    return db.query(User).order_by(User.id).limit(limit).offset(offset).all()


@user_router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db), me: User = Depends(get_current_user)):
    if me.status != UserStatus.manager and me.id != user_id:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@user_router.put("/{user_id}", response_model=UserResponse)
def update_user(user_id: int,data: UserUpdateSchema,
    db: Session = Depends(get_db),me: User = Depends(get_current_user)):
    is_manager = me.status == UserStatus.manager
    if not is_manager and me.id != user_id:
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    changes = data.model_dump(exclude_unset=True)
    if "status" in changes and not is_manager:
        raise HTTPException(status_code=403, detail="Only manager can change status")

    for field in ("username", "email"):
        if field in changes and changes[field] != getattr(user, field):
            taken = db.query(User).filter(
                getattr(User, field) == changes[field], User.id != user_id).first()
            if taken:
                raise HTTPException(status_code=409, detail=f"{field} already taken")

    for key, value in changes.items():
        setattr(user, key, value)
    db.commit()
    db.refresh(user)
    return user


@user_router.delete("/{user_id}", dependencies=[ManagerOnly])
def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    try:
        db.delete(user)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="User has related orders")
    return {"message": "User deleted successfully"}