# 프로필만들기

부산대학교 물리학과 4학년 김충현을 소개하는 FastAPI + Jinja2 템플릿 기반 웹사이트입니다.  
현재 구조를 유지한 채 서버사이드 Google OAuth 로그인을 붙인 버전입니다.

## 사용 기술

- FastAPI
- Jinja2 템플릿
- Authlib 기반 Google OAuth
- Numpy + Pillow 기반 접촉각 추정
- SessionMiddleware
- python-dotenv
- Tailwind CSS CDN
- Custom CSS

## 수정한 파일

- `main.py`
- `templates/index.html`
- `contact_angle.py`
- `requirements.txt`
- `run_portfolio.bat`
- `.env.example`

루트 `.gitignore`도 `.env` 파일이 커밋되지 않도록 함께 수정했습니다.

## 왜 수정했나

- `main.py`
  FastAPI 앱 엔트리 파일입니다. Google OAuth 시작, 콜백, 로그아웃 라우트와 세션 처리, `.env` 로딩을 추가했습니다.
- `templates/index.html`
  로그인 상태 카드와 함께 이미지 업로드 기반 접촉각 분석 섹션을 추가했습니다.
- `contact_angle.py`
  업로드한 사진에서 물방울 실루엣을 추정하고 접촉각을 계산하는 분석 로직을 분리했습니다.
- `requirements.txt`
  OAuth, 업로드 처리, 이미지 분석에 필요한 패키지를 추가했습니다.
- `run_portfolio.bat`
  실행 주소 안내를 `localhost:8000` 기준으로 맞췄습니다.
- `.env.example`
  필요한 환경변수 이름과 placeholder 값을 추가했습니다.

## 설치 명령

```bash
python -m pip install -r requirements.txt
```

## .env 파일 만들기

같은 폴더에 `.env` 파일을 만들고 아래 값을 채워 주세요.

```env
BASE_URL=http://localhost:8000
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-google-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8000/api/auth/google/callback
SESSION_SECRET_KEY=replace-this-with-a-long-random-string
```

`SESSION_SECRET_KEY` 는 충분히 길고 예측하기 어려운 값으로 넣어 주세요.

## 실행 방법

1. 프로젝트 폴더로 이동합니다.

```bash
cd week1/프로필만들기
```

2. 의존성을 설치합니다.

```bash
python -m pip install -r requirements.txt
```

3. `.env.example` 을 참고해서 `.env` 파일을 만듭니다.

4. 서버를 실행합니다.

```bash
python -m uvicorn main:app --host localhost --port 8000
```

또는 Windows에서는 `run_portfolio.bat` 를 실행해도 됩니다.

5. 브라우저에서 아래 주소를 엽니다.

```text
http://localhost:8000
```

## Google Cloud Console 설정

이 프로젝트는 React/Vite 프론트엔드가 없는 서버 렌더링 FastAPI 앱입니다.  
따라서 Google Cloud Console 값도 `localhost:8000` 기준으로 맞춰야 합니다.

### Authorized JavaScript origins

```text
http://localhost:8000
```

### Authorized redirect URIs

```text
http://localhost:8000/api/auth/google/callback
```

## 중요한 주의사항

- `localhost` 와 `127.0.0.1` 을 혼용하면 안 됩니다.
- 예를 들어 `.env` 는 `http://localhost:8000/...` 인데 Google Cloud Console 은 `http://127.0.0.1:8000/...` 로 등록하면 OAuth 콜백이 실패할 수 있습니다.
- 이 README 기준으로는 모든 값을 `localhost:8000` 으로 통일해 주세요.
- 예전의 `localhost:5173` 설정은 이 프로젝트 구조에서는 사용하지 않습니다.

## 라우트 정리

- 메인 페이지: `/`
- 접촉각 분석 업로드: `/analysis/contact-angle`
- Google 로그인 시작: `/auth/google/login`
- Google 로그인 콜백: `/api/auth/google/callback`
- 로그아웃: `/auth/logout`
- 상태 확인: `/health`

## 접촉각 분석 기능

- 메인 페이지의 `Contact Angle Lab` 섹션에서 이미지를 바로 업로드할 수 있습니다.
- 서버는 물방울 윤곽을 추정한 뒤 원호 기반 근사로 접촉각을 계산합니다.
- 결과 화면에는 원본 이미지, 오버레이 이미지, 추정 접촉각이 함께 표시됩니다.
- 이 기능은 실험실 측정 장비를 완전히 대체하는 용도가 아니라, 빠른 1차 확인용 도구입니다.
- 측면 사진, 단순한 배경, 수평한 시료면에서 가장 잘 동작합니다.

## 동작 방식

1. 메인 페이지에서 `Google로 로그인` 버튼을 누릅니다.
2. FastAPI 서버가 Google OAuth 로그인 화면으로 리다이렉트합니다.
3. 로그인 후 Google 이 `/api/auth/google/callback` 으로 되돌려 보냅니다.
4. 서버가 사용자 정보를 읽고 세션에 저장합니다.
5. 다시 메인 페이지로 돌아오면 이름 또는 이메일과 로그아웃 버튼이 표시됩니다.

## 테스트 방법

1. `.env` 파일의 다섯 값을 모두 채웁니다.
2. Google Cloud Console 에 아래 두 값을 정확히 등록합니다.
   - Origin: `http://localhost:8000`
   - Redirect URI: `http://localhost:8000/api/auth/google/callback`
3. 서버를 실행하고 `http://localhost:8000` 에 접속합니다.
4. 메인 화면에서 `Contact Angle Lab` 섹션과 `Google로 로그인` 버튼이 보이는지 확인합니다.
5. 물방울 측면 사진을 업로드하고 접촉각 값과 오버레이 이미지가 표시되는지 확인합니다.
6. 버튼을 눌러 Google 로그인 후 다시 메인 화면으로 돌아오는지 확인합니다.
7. 로그인 후 사용자 이름 또는 이메일이 표시되는지 확인합니다.
8. `로그아웃` 버튼을 눌렀을 때 로그인 전 상태로 돌아가는지 확인합니다.
9. 설정이 잘못된 경우 화면의 경고 메시지와 상태 메시지가 표시되는지 확인합니다.
