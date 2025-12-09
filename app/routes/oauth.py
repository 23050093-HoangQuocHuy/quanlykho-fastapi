from fastapi import APIRouter, Request, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import os
import requests
from app.database import get_db
from app import crud, models, schemas
from app.routes.auth import create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES

router = APIRouter()

# Google OAuth2 SSO

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
REDIRECT_URI = "http://localhost:8500/auth/google/callback"


if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
    raise RuntimeError("Missing google OAuth credentials in environment variables")

# redirects the user to Google’s OAuth2 consent screen, passing key parameters 
@router.get("/auth/google/login")
def google_login():
    google_auth_url = (
        "https://accounts.google.com/o/oauth2/v2/auth"
        f"?client_id={GOOGLE_CLIENT_ID}"
        f"&response_type=code"
        f"&redirect_uri={REDIRECT_URI}"
        f"&scope=openid%20email%20profile"
    )
    return RedirectResponse(google_auth_url)


@router.get("/auth/google/callback")
def google_callback(request: Request, code: str, db: Session = Depends(get_db)):
    # exchange code for token
    token_response = requests.post(
        "https://oauth2.googleapis.com/token",
        data={
            "code" : code,
            "client_id" : GOOGLE_CLIENT_ID,
            "client_secret" : GOOGLE_CLIENT_SECRET,
            "redirect_uri" : REDIRECT_URI,
            "grant_type" : "authorization_code",
        },
        headers={"Content-Type" : "application/x-www-form-urlencoded"},
    )

    if token_response.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to exchange code for token")


    tokens = token_response.json() # convert to json
    access_token = tokens.get("access_token")

    userinfo_response = requests.get(
        "https://www.googleapis.com/oauth2/v1/userinfo",
        params={"access_token" : access_token}
    )

    if userinfo_response.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to retrieve user info")

    user_info = userinfo_response.json()
    username = user_info["email"]

    # check if the user exists in our db else create them
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user:
        user = crud.create_user(
            db,
            schemas.UserCreate(
                username=username,
                password="oauth2_user", # dummy password since google is handling that and we dont store users password in this case
                role="Regular", # default google OAuth user to regular not Admin 
            )
        )

    # Issue JWT and set in cookie
    jwt_token = create_access_token(
        data={"sub" : user.username},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    response = RedirectResponse(url="/profile")
    response.set_cookie(key="access_token", value=jwt_token, httponly=True)
    return response


