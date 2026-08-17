from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import User

def get_current_user(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")

    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated"
        )

    user = db.query(User).filter(User.id == user_id).first()
    
    if not user: 
        request.session.clear()
        raise HTTPException(
            status_code=401,
            detail="User no longer exists"
        )

    return user

    