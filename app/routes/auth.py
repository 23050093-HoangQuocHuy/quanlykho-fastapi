from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timezone
import jwt
from jwt.exceptions import InvalidTokenError
import os
from dotenv import load_dotenv


from app import crud, schemas
from app.database import get_db
from app.models import User


load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")

# Google OAuth2 sign in 
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

# validation of critical variables
missing_vars = []
if not SECRET_KEY:
    missing_vars.append("SECRET_KEY")
if not GOOGLE_CLIENT_ID:
    missing_vars.append("GOOGLE_CLIENT_ID")
if not GOOGLE_CLIENT_SECRET:
    missing_vars.append("GOOGLE_CLIENT_SECRET")

if missing_vars:
    raise RuntimeError(f"Missing environment variables: {', '.join(missing_vars)}")


ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


router = APIRouter()


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login") #oauth2 scheme for token extraction from requests

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    # we use this to create JWT access token
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    
    to_encode.update({"exp" : expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# extract and return the current user based on the JWT token
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate" : "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str | None = payload.get("sub")
        if username is None:
            raise credentials_exception
    except InvalidTokenError:
        raise credentials_exception
    
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    return user

# ensures user has admin role
def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role.lower() != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operation not permitted. Admins only",
        )
    return current_user

# register a new user
@router.post("/register", response_model=schemas.User, status_code=status.HTTP_201_CREATED)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.username == user.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered.")
    return crud.create_user(db, user)

# login a user
@router.post("/login")
def login(form_date: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_date.username).first()
    if not user or not crud.pwd_context.verify(form_date.password, user.password):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub" : user.username},
        expires_delta=access_token_expires,
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/profile", response_model=schemas.User)
def read_profile(current_user: schemas.User = Depends(get_current_user)):
    return current_user

@router.get("/admin", response_model=schemas.User)
def admin_endpoint(current_user: User = Depends(require_admin)):
    return {"message" : f"Welcome, admin {current_user.username}"}





