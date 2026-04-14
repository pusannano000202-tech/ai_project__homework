import logging
import os
import secrets
from pathlib import Path

import uvicorn
from authlib.integrations.starlette_client import OAuth, OAuthError
from dotenv import load_dotenv
from fastapi import FastAPI, File, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from contact_angle import ContactAngleError, analyze_contact_angle


BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

logger = logging.getLogger(__name__)
MAX_UPLOAD_BYTES = 6 * 1024 * 1024


def read_env(name: str) -> str | None:
    value = os.getenv(name)
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


BASE_URL_ENV = read_env("BASE_URL")
BASE_URL = BASE_URL_ENV or "http://localhost:8000"
GOOGLE_CLIENT_ID = read_env("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = read_env("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = read_env("GOOGLE_REDIRECT_URI")
SESSION_SECRET_KEY = read_env("SESSION_SECRET_KEY")
GOOGLE_CALLBACK_PATH = "/api/auth/google/callback"

SESSION_KEY_FALLBACK_USED = SESSION_SECRET_KEY is None
SESSION_SECRET = SESSION_SECRET_KEY or secrets.token_urlsafe(32)

app = FastAPI(
    title="김충현 소개 페이지",
    description="초발수표면 연구와 부산대학교 4학년 김충현을 소개하는 웹페이지 초안",
)
app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET,
    same_site="lax",
    https_only=False,
    session_cookie="portfolio_session",
)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

oauth = OAuth()
google_oauth = None
if GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET:
    google_oauth = oauth.register(
        name="google",
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={"scope": "openid email profile"},
    )

PROFILE = {
    "name": "김충현",
    "headline": "초발수표면을 연구하는 부산대학교 4학년",
    "summary": (
        "표면의 미세구조와 젖음성 제어에 관심을 두고, "
        "물방울이 머무르지 않는 초발수표면의 물리와 응용 가능성을 탐구하고 있습니다."
    ),
    "university": "부산대학교",
    "major": "물리학과",
    "year": "4학년",
    "research_theme": "Superhydrophobic Surface",
    "draft_note": (
        "현재 버전은 자기소개용 랜딩 페이지 초안이며, "
        "세부 연구 데이터와 성과는 추후 보강 예정입니다."
    ),
}

RESEARCH_POINTS = [
    {
        "title": "핵심 관심사",
        "body": "미세 패턴 구조, 표면 에너지 제어, 접촉각 분석을 중심으로 초발수 현상을 이해합니다.",
    },
    {
        "title": "연구 방향",
        "body": "자연계의 연잎 효과에서 영감을 받아 self-cleaning과 anti-wetting 응용 가능성을 살핍니다.",
    },
    {
        "title": "작업 방식",
        "body": "실험 설계, 결과 정리, 시각화까지 한 흐름으로 묶어 물리적 해석이 가능한 형태로 다룹니다.",
    },
]

TIMELINE = [
    {
        "title": "학부 과정",
        "body": "부산대학교 물리학과에서 기초 물리, 수치 계산, 데이터 해석 역량을 쌓고 있습니다.",
    },
    {
        "title": "현재 연구",
        "body": "초발수표면의 구조와 성능 사이의 관계를 관찰하며 실험 중심의 관점을 키우고 있습니다.",
    },
    {
        "title": "다음 목표",
        "body": "연구 내용을 더 체계적으로 정리해 포트폴리오와 프로젝트 기록으로 확장할 계획입니다.",
    },
]

KEYWORDS = [
    "Superhydrophobicity",
    "Surface Physics",
    "Contact Angle",
    "Microstructure",
    "Self-Cleaning",
]

SNAPSHOTS = [
    {"label": "Research Core", "value": "초발수표면"},
    {"label": "Current Stage", "value": "학부 4학년"},
    {"label": "Base", "value": "부산대학교"},
]


def build_auth_config_issues() -> list[str]:
    issues: list[str] = []

    if not BASE_URL_ENV:
        issues.append("BASE_URL이 설정되지 않아 기본값 http://localhost:8000 을 사용 중입니다.")
    if not GOOGLE_CLIENT_ID:
        issues.append("GOOGLE_CLIENT_ID가 설정되지 않았습니다.")
    if not GOOGLE_CLIENT_SECRET:
        issues.append("GOOGLE_CLIENT_SECRET이 설정되지 않았습니다.")
    if not GOOGLE_REDIRECT_URI:
        issues.append("GOOGLE_REDIRECT_URI가 설정되지 않았습니다.")
    if not SESSION_SECRET_KEY:
        issues.append(
            "SESSION_SECRET_KEY가 설정되지 않아 임시 세션 키를 사용 중입니다. 서버를 재시작하면 로그인 세션이 초기화됩니다."
        )

    if GOOGLE_REDIRECT_URI and not GOOGLE_REDIRECT_URI.startswith(BASE_URL):
        issues.append(
            "GOOGLE_REDIRECT_URI와 BASE_URL의 호스트가 다릅니다. localhost와 127.0.0.1을 혼용하지 마세요."
        )

    if GOOGLE_REDIRECT_URI and not GOOGLE_REDIRECT_URI.endswith(GOOGLE_CALLBACK_PATH):
        issues.append(
            f"GOOGLE_REDIRECT_URI는 {GOOGLE_CALLBACK_PATH} 로 끝나도록 맞추는 것을 권장합니다."
        )

    return issues


def set_auth_message(request: Request, text: str, level: str = "info") -> None:
    request.session["auth_message"] = {"text": text, "level": level}


def get_current_user(request: Request) -> dict[str, str] | None:
    user = request.session.get("user")
    if isinstance(user, dict):
        return user
    return None


def auth_is_configured() -> bool:
    return (
        google_oauth is not None
        and GOOGLE_REDIRECT_URI is not None
        and not SESSION_KEY_FALLBACK_USED
    )


def render_home(
    request: Request,
    *,
    contact_result: dict[str, object] | None = None,
    contact_error: str | None = None,
) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "request": request,
            "profile": PROFILE,
            "research_points": RESEARCH_POINTS,
            "timeline": TIMELINE,
            "keywords": KEYWORDS,
            "snapshots": SNAPSHOTS,
            "user": get_current_user(request),
            "auth_message": request.session.pop("auth_message", None),
            "auth_config_issues": build_auth_config_issues(),
            "auth_ready": auth_is_configured(),
            "contact_result": contact_result,
            "contact_error": contact_error,
        },
    )


@app.get("/", response_class=HTMLResponse)
async def home(request: Request) -> HTMLResponse:
    return render_home(request)


@app.post("/analysis/contact-angle", response_class=HTMLResponse, name="contact_angle_analysis")
async def contact_angle_analysis(request: Request, image: UploadFile = File(...)) -> HTMLResponse:
    if not image.filename:
        return render_home(request, contact_error="업로드할 이미지를 선택해 주세요.")

    payload = await image.read()
    if not payload:
        return render_home(request, contact_error="빈 파일은 분석할 수 없습니다.")
    if len(payload) > MAX_UPLOAD_BYTES:
        return render_home(request, contact_error="파일 크기는 6MB 이하로 올려 주세요.")

    try:
        result = analyze_contact_angle(payload)
    except ContactAngleError as exc:
        return render_home(request, contact_error=str(exc))
    except Exception:
        logger.exception("Unexpected contact-angle analysis failure")
        return render_home(
            request,
            contact_error="이미지 분석 중 오류가 발생했습니다. 측면 사진인지와 배경 대비를 다시 확인해 주세요.",
        )

    return render_home(request, contact_result=result)


@app.get("/auth/google/login", name="google_login")
async def google_login(request: Request):
    if not auth_is_configured() or google_oauth is None or GOOGLE_REDIRECT_URI is None:
        set_auth_message(
            request,
            "Google 로그인 설정이 아직 완료되지 않았습니다. .env와 Google Cloud Console 값을 먼저 확인해 주세요.",
            "error",
        )
        return RedirectResponse(url=str(request.url_for("home")), status_code=303)

    return await google_oauth.authorize_redirect(request, GOOGLE_REDIRECT_URI)


@app.get(GOOGLE_CALLBACK_PATH, name="google_callback")
async def google_callback(request: Request) -> RedirectResponse:
    if google_oauth is None:
        set_auth_message(
            request,
            "Google OAuth 클라이언트가 초기화되지 않았습니다. 환경변수를 다시 확인해 주세요.",
            "error",
        )
        return RedirectResponse(url=str(request.url_for("home")), status_code=303)

    try:
        token = await google_oauth.authorize_access_token(request)
        user_info = token.get("userinfo")
        if not user_info:
            user_info = await google_oauth.userinfo(token=token)
    except OAuthError as exc:
        logger.warning("Google OAuth error: %s", exc)
        set_auth_message(
            request,
            "Google 로그인에 실패했습니다. Authorized redirect URI와 .env 값을 다시 확인해 주세요.",
            "error",
        )
        return RedirectResponse(url=str(request.url_for("home")), status_code=303)
    except Exception:
        logger.exception("Unexpected Google OAuth callback failure")
        set_auth_message(
            request,
            "Google 로그인 처리 중 예상치 못한 오류가 발생했습니다.",
            "error",
        )
        return RedirectResponse(url=str(request.url_for("home")), status_code=303)

    request.session["user"] = {
        "name": user_info.get("name") or user_info.get("given_name") or user_info.get("email", ""),
        "email": user_info.get("email", ""),
        "picture": user_info.get("picture", ""),
    }
    set_auth_message(request, "Google 계정으로 로그인되었습니다.", "success")
    return RedirectResponse(url=str(request.url_for("home")), status_code=303)


@app.get("/auth/logout", name="logout")
async def logout(request: Request) -> RedirectResponse:
    request.session.pop("user", None)
    set_auth_message(request, "로그아웃되었습니다.", "info")
    return RedirectResponse(url=str(request.url_for("home")), status_code=303)


@app.get("/health")
async def health() -> dict[str, object]:
    return {
        "status": "ok",
        "google_oauth_configured": google_oauth is not None,
        "session_secret_from_env": SESSION_SECRET_KEY is not None,
    }


if __name__ == "__main__":
    uvicorn.run("main:app", host="localhost", port=8000, reload=False)
