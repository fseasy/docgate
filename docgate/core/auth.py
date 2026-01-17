from docgate.utils.password import verify_password
from fastapi import HTTPException
from sqlalchemy.orm import Session

from docgate.models import User


def authenticate_user(db: Session, email: str, password: str):
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return user


def create_user(db: Session, email: str, password: str):
    hashed_password = hash_password(password)
    user = User(email=email, password_hash=hashed_password)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
