from fastapi import Depends, HTTPException, APIRouter, status
from fastapi_jwt_auth import AuthJWT
from fastapi_jwt_auth.exceptions import JWTDecodeError, InvalidHeaderError, MissingTokenError
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from models import User
from database import get_db
from dependencies import get_password_hash, verify_password
from pydantic import BaseModel, EmailStr
from datetime import datetime

auth_router = APIRouter(prefix="/auth")

class Settings(BaseModel):
    authjwt_secret_key: str = "ragchatbot"
    authjwt_access_token_expires: int = 3600
    authjwt_refresh_token_expires: int = 3600

@AuthJWT.load_config
def get_config():
    return Settings()

class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    created_time: datetime
    updated_time: datetime

    class Config:
        orm_mode = True


class LoginRequest(BaseModel):
    username: str
    password: str

@auth_router.post("/register", response_model=UserResponse)
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    try:
        hashed_password = get_password_hash(request.password)
        user = User(username = request.username, email = request.email, password = hashed_password)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username or Email already exists.")
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during registration: {str(e)}"
        )

@auth_router.post("/login")
def login(request: LoginRequest, db: Session = Depends(get_db), Authorize: AuthJWT = Depends()):
    try:
        user = db.query(User).filter(User.username == request.username).first()
        if user == None or not verify_password(request.password, user.password):
            raise HTTPException(status_code=401, detail="Invalid username or password")
        else:
            access_token = Authorize.create_access_token(subject=user.username)
            refresh_token = Authorize.create_refresh_token(subject=user.username)
            return {"access_token": access_token, "refresh_token": refresh_token, "user": UserResponse.from_orm(user)}
    except SQLAlchemyError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Database error occurred: {str(e)}")
    except HTTPException as e:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {str(e)}")

@auth_router.post("/refresh")
def refresh_token(Authorize: AuthJWT = Depends(), db: Session = Depends(get_db)):
    try:
        Authorize.jwt_refresh_token_required()
        current_user_username = Authorize.get_jwt_subject()
        user = db.query(User).filter(User.username == current_user_username).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        new_access_token = Authorize.create_access_token(subject=user.username)
        new_refresh_token = Authorize.create_refresh_token(subject=user.username)

        return {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "user": UserResponse.from_orm(user)
        }
    except JWTDecodeError as e:
        raise HTTPException(status_code=401, detail=f"Invalid refresh token: {str(e)}")
    except InvalidHeaderError as e:
        raise HTTPException(status_code=400, detail=f"Authorization header is invalid or missing: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

def get_current_user(Authorize: AuthJWT = Depends(), db: Session = Depends(get_db)):
    try:
        Authorize.jwt_required()
        current_user = Authorize.get_jwt_subject()
        user = db.query(User).filter(User.username == current_user).first()
        if not user:
            raise HTTPException(status_code=401, detail="Invalid user")
        return user
    except MissingTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail = "Token is missing. Please provide a valid token."
        )
    except JWTDecodeError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token. Please provide a valid token."
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )