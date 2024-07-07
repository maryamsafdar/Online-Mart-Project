# crud.py
from fastapi import HTTPException
from sqlmodel import Session, select
from app.models.user_model import User

def create_user(user_data: User, session: Session):
    session.add(user_data)
    session.commit()
    session.refresh(user_data)
    return user_data

def get_user_by_id(user_id: int, session: Session):
    user = session.exec(select(User).where(User.id == user_id)).one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user

def delete_user_by_id(user_id: int, session: Session):
    user = session.exec(select(User).where(User.id == user_id)).one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    session.delete(user)
    session.commit()
    return {"message": "User Deleted Successfully"}

def update_user_by_id(user_id: int, to_update_user_data: User, session: Session):
    user = session.exec(select(User).where(User.id == user_id)).one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    updated_data = to_update_user_data.dict(exclude_unset=True)
    for field, value in updated_data.items():
        setattr(user, field, value)
    session.add(user)
    session.commit()
    return user
