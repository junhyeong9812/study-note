# python/python-web/13 — CORS & CSRF (보안 설정) — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 개발 서버 오리진에서 온 요청과 수동 훅 (예측)

```python
# 질문용 발췌
@app.after_request
def add_cors_headers(response):
    origin = request.headers.get('Origin')
    allowed_origins = ['https://frontend.example.com']
    if origin in allowed_origins:
        response.headers['Access-Control-Allow-Origin'] = origin
    return response
```

- 요청 헤더가 `Origin: http://localhost:3000` 일 때 이 훅은 응답에 `Access-Control-Allow-Origin` 을 붙이나?

### 2. `Origin` 헤더가 아예 없는 요청 (예측)

- 문항 1 의 훅에 `Origin` 헤더가 없는 요청이 오면 `origin` 에는 무엇이 들어가고 `if` 는 어느 쪽으로 가나?

### 3. CORS 가 서버 간 통신에 적용되지 않는 까닭 (왜)

- CORS 헤더를 아무리 좁혀도 다른 서버가 이 API 를 직접 부르는 것을 막지 못하는 이유는 무엇인가?

### 4. CSRF 쿠키는 HttpOnly 가 꺼져 있다 (왜)

- 세션 쿠키는 `SESSION_COOKIE_HTTPONLY = True` 인데 CSRF 쿠키는 `CSRF_COOKIE_HTTPONLY = False` 로 둔 이유는 무엇인가?

### 5. JWT API 의 `csrf_exempt` 가 안전한 범위 (경계)

- JWT 인증 API 에 `@csrf_exempt` 를 다는 근거는 JWT 를 어디에 실어 보낼 때 무너지나?

### 6. 모든 오리진 허용의 자리 (경계)

- `CORS_ALLOW_ALL_ORIGINS = True` 나 `origins='*'` 를 써도 되는 곳과 쓰면 안 되는 곳은 어디인가?

### 7. 이 CSP 아래에서 불러온 스크립트 (예측)

```python
# 질문용 발췌
response.headers['Content-Security-Policy'] = (
    "default-src 'self'; "
    "script-src 'self' https://cdn.example.com; "
    "style-src 'self' 'unsafe-inline'; "
)
```

- 페이지가 `https://other.example.net/x.js` 를 `<script src>` 로 불러오고, 본문에 인라인 `<script>` 도 하나 있으면 각각 어떻게 되나?

### 8. CSP 와 XSS (연결)

- CSP 헤더는 XSS 공격의 어느 단계를 끊어서 공격 표면을 줄이나?

### 9. Flask `after_request` 와 Django `MIDDLEWARE` (연결)

- 두 장치가 맡는 공통 역할은 무엇이고, Django 쪽에서 `CorsMiddleware` 를 최상단에 두라는 이유는 무엇인가?

## 실습

### 실습 1. Flask · Django 웹 보안 설정 모음 만들기

**만들 것** — CORS · CSRF · 보안 헤더를 Flask 와 Django 양쪽 방식으로 나란히 적은 설정 모음 파일 하나를 만든다.
Django 부분은 `settings.py` 와 뷰에 들어갈 내용을 같은 파일에 예시로 적는다.

**준비물** — `flask` · `flask-cors` · `flask-wtf` · `django` · `django-cors-headers` 가 필요하다.
Django 부분은 실제 프로젝트가 아니라 settings 와 뷰의 꼴을 흉내 낸 예시다.

**요구 조건**

1단계 — Flask CORS
1. Flask 앱을 만들고 flask-cors 로 `/api/*` 경로 패턴에 정책을 건다 — 허용 오리진 둘(프런트엔드 운영 · 로컬 개발), 메서드 GET · POST · PUT · DELETE, 요청 헤더 `Content-Type` · `Authorization`, 노출 헤더 `X-Total-Count`, 쿠키 포함 허용, preflight 캐시 1시간.
2. `/api/public` 라우트는 데코레이터로 모든 오리진을 허용하고 `{'data': 'public'}` 을 JSON 으로 돌려준다.
3. `after_request` 훅 `add_cors_headers` 가 요청의 `Origin` 이 화이트리스트(프런트엔드 운영 오리진 하나)에 있을 때만 그 오리진을 되돌려 주는 `Allow-Origin` 과 `Allow-Methods` · `Allow-Headers` · `Allow-Credentials` 헤더를 붙인다.

2단계 — Django CORS 설정
4. `INSTALLED_APPS` 에 `corsheaders` 를 넣고, `MIDDLEWARE` 맨 위에 `CorsMiddleware` 를 둔다.
5. 허용 오리진 둘, 메서드 여섯(PATCH · OPTIONS 포함), 소문자 헤더 셋(`x-csrftoken` 포함), 자격 증명 허용, preflight 캐시 3600초를 설정하고, 모든 오리진 허용 줄은 주석으로만 남긴다.

3단계 — Django CSRF
6. CSRF 쿠키를 HTTPS 전용 · JS 접근 가능 · SameSite `Lax` 로 두고, 신뢰 오리진에 프런트엔드를 넣는다.
7. `api_endpoint` 뷰는 CSRF 검사를 끄고, `get_csrf` 뷰는 CSRF 쿠키를 강제로 설정한 뒤 `request.META` 의 `CSRF_COOKIE` 를 `csrfToken` 키로 JSON 응답한다.

4단계 — Flask CSRF
8. `CSRFProtect` 로 앱 전체 CSRF 보호를 켜고 토큰 유효 시간을 3600초로 둔다.
9. POST 전용 `/webhook` 은 CSRF 면제로 `'OK'` 를 돌려주고, `/api/csrf-token` 은 새 토큰을 `csrf_token` 키로 JSON 응답한다.

5단계 — 보안 헤더
10. `after_request` 훅 `set_security_headers` 가 모든 응답에 일곱 헤더를 붙인다 — 스니핑 금지, 같은 오리진만 iframe 허용, 구형 XSS 필터 차단 모드, CSP(기본 자기 도메인 · 스크립트는 자기와 CDN · 스타일은 인라인 허용 · 이미지는 data 와 https · 폰트는 자기와 구글 폰트), HSTS 1년 + 서브도메인, Referrer 정책, 카메라 · 마이크 · 위치 권한 차단.
11. Django 보안 설정 여덟 줄로 같은 헤더와 HTTPS 리다이렉트 · 세션 쿠키 보안을 켠다.

6단계 — 정리
12. 마지막에 핵심 정리 문장들을 찍는다(시작 코드에 채워 둠).

**시작 코드**

```python
# CORS & CSRF - 웹 보안 설정

# === 1. CORS ===
from flask import Flask, jsonify, request, make_response
from flask_cors import CORS

app = Flask(__name__)

# TODO: CORS(app, resources={r'/api/*': {...}}) — 오리진 2 · 메서드 4 · 요청 헤더 2 · 노출 헤더 · 쿠키 · max_age

from flask_cors import cross_origin

@app.route('/api/public')
# TODO: 모든 오리진 허용 데코레이터
def public_api():
    pass  # TODO: {'data': 'public'} 을 JSON 으로

@app.after_request
def add_cors_headers(response):
    # TODO: Origin 헤더 읽기
    allowed_origins = ['https://frontend.example.com']
    # TODO: 화이트리스트 검사 후 Allow-Origin / Methods / Headers / Credentials
    return response


# --- Django CORS (settings.py 예시) ---
INSTALLED_APPS = [...]   # TODO: corsheaders 등록
MIDDLEWARE = [
    # TODO: CorsMiddleware 를 맨 위에
    'django.middleware.common.CommonMiddleware',
    ...
]
# TODO: CORS_ALLOWED_ORIGINS / CORS_ALLOW_METHODS / CORS_ALLOW_HEADERS
# TODO: CORS_ALLOW_CREDENTIALS / CORS_PREFLIGHT_MAX_AGE
# CORS_ALLOW_ALL_ORIGINS = True  # 개발용: 모든 오리진 허용 (프로덕션 금지!)


# === 2. CSRF ===
# --- Django CSRF ---
# TODO: CSRF_COOKIE_SECURE / CSRF_COOKIE_HTTPONLY / CSRF_COOKIE_SAMESITE / CSRF_TRUSTED_ORIGINS

from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie

# TODO: CSRF 검사 끄기
def api_endpoint(request):
    pass

# TODO: CSRF 쿠키 강제
def get_csrf(request):
    pass  # TODO: {'csrfToken': ...} JSON 응답

# --- Flask CSRF ---
from flask_wtf.csrf import CSRFProtect, generate_csrf

# TODO: CSRFProtect 적용, WTF_CSRF_TIME_LIMIT

# TODO: 면제 데코레이터
@app.route('/webhook', methods=['POST'])
def webhook():
    return 'OK'

@app.route('/api/csrf-token')
def csrf_token():
    pass  # TODO: 새 토큰을 csrf_token 키로


# === 3. 보안 헤더 ===
@app.after_request
def set_security_headers(response):
    # TODO: 일곱 보안 헤더
    return response

# Django 보안 설정 (settings.py)
# TODO: SECURE_* / X_FRAME_OPTIONS / SESSION_COOKIE_* 여덟 줄


print("CORS & CSRF 보안 핵심 정리")
print("="*50)
print("CORS: 다른 도메인 요청 허용/차단 (서버 측 헤더)")
print("CSRF: 위조 요청 방지 (토큰 기반 검증)")
print("CSP: 허용된 리소스 출처 제한")
print("HSTS: HTTPS 강제")
print("X-Frame-Options: 클릭재킹 방지")
print("프로덕션에서 CORS_ALLOW_ALL_ORIGINS는 절대 True 금지!")
```

**확인 방법** — 요구 조건 12줄을 하나씩 짚으며 빈 TODO 가 남지 않았는지 본다.
Flask 부분만 떼어 앱으로 띄운 뒤 `curl -i -H "Origin: https://frontend.example.com" http://127.0.0.1:5000/api/public` 처럼 `Origin` 을 바꿔 가며 응답 헤더에 CORS 헤더와 보안 헤더가 붙는지 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
