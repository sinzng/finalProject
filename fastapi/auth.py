import os
import requests
from fastapi import APIRouter, Request, Depends
from fastapi.responses import RedirectResponse
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

router = APIRouter()

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")

# 구글 로그인 URL 생성
def get_google_login_url():
    return (
        f"https://accounts.google.com/o/oauth2/v2/auth?"
        f"client_id={GOOGLE_CLIENT_ID}&response_type=code&redirect_uri={REDIRECT_URI}&"
        f"scope=openid%20email%20profile"
    )

@router.get("/login/google")
async def login_google():
    google_login_url = get_google_login_url()
    print(f"Google Login URL: {google_login_url}")  # URL을 로그로 출력
    return RedirectResponse(url=google_login_url)

@router.get("/auth/callback")
async def auth(request: Request):
    code = request.query_params.get("code")
    if code:
        print(f"Authorization code received: {code}")  # Authorization code 로그 출력
        token_url = "https://oauth2.googleapis.com/token"
        token_data = {
            "code": code,
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "redirect_uri": REDIRECT_URI,
            "grant_type": "authorization_code",
        }
        token_response = requests.post(token_url, data=token_data)
        token_json = token_response.json()
        access_token = token_json.get("access_token")
        print(f"Access token received: {access_token}")  # Access token 로그 출력

        # 구글 프로필 정보 요청
        user_info_url = "https://www.googleapis.com/oauth2/v2/userinfo"
        headers = {"Authorization": f"Bearer {access_token}"}
        user_info_response = requests.get(user_info_url, headers=headers)
        user_info = user_info_response.json()
        print(f"User info: {user_info}")  # 사용자 정보 로그 출력

        return user_info
    return {"error": "No code provided"}
