# python/python-web/13 — CORS & CSRF (보안 설정) — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 붙이지 않는다 — 이 훅의 화이트리스트에 `localhost:3000` 이 없다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
`origin` 은 `'http://localhost:3000'` 이 되고, `origin in allowed_origins` 는 `False` 라서 이 훅은 아무 헤더도 붙이지 않는다.

**왜 그런가**
훅의 `allowed_origins` 는 `'https://frontend.example.com'` 하나뿐이다.
`localhost:3000` 은 flask-cors 의 `resources` 정책 쪽 목록에만 있다.
그래서 `/api/*` 경로라면 flask-cors 가 따로 허용할 수 있다 — 두 방식의 목록이 어긋나는 것이 2-summary 「어디서 틀리나 3」이다.

### 2. `None` 이 들어가고 `if` 를 건너뛴다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
`request.headers.get('Origin')` 은 `None` 을 돌려준다.
`None in ['https://frontend.example.com']` 은 `False` 라서 CORS 헤더 없이 `response` 를 그대로 돌려준다.

**왜 그런가**
딕셔너리식 `get` 은 키가 없으면 `None` 이고, 문자열 목록에 `None` 은 없다.
근거 — 2-summary 「동작 방식 (1)」 그림 해설과 「구현 세부사항 대 언어 보장」 표.

### 3. CORS 를 지키는 쪽이 브라우저이기 때문이다

서버는 허락 헤더를 쓸 뿐이고, 그 헤더를 보고 응답을 JS 에 넘길지 정하는 쪽은 브라우저다.
브라우저를 거치지 않는 다른 서버의 호출에는 그 판단을 해 줄 주체가 없으므로 CORS 가 걸리지 않는다.
API 자체는 인증 · 권한 검사로 지켜야 한다.
근거 — 원본 팁, 2-summary 「동작 방식 (1)」 · 「어디서 틀리나 1」.

### 4. AJAX 의 JS 가 CSRF 토큰을 읽어 헤더에 실어야 하기 때문이다

HttpOnly 쿠키는 JS 가 읽지 못한다.
CSRF 토큰은 JS 가 읽어 `X-CSRFToken` 헤더로 다시 보내야 쓸모가 있으므로 `False` 로 둔다.
세션 쿠키는 JS 가 읽을 일이 없어서 `True` 로 막아 둔다.
근거 — 2-summary 「동작 방식 (3)」 · 「동작 방식 (4)」 Django 표 아래 불릿 · 「어디서 틀리나 10」.

### 5. JWT 를 쿠키에 담아 보낼 때 무너진다

면제의 근거는 「`Authorization` 헤더의 JWT 는 브라우저가 자동으로 싣지 않는다」는 데 있다.
JWT 를 쿠키에 담으면 브라우저가 공격 페이지의 요청에도 자동으로 실으므로 CSRF 의 전제(자동 전송)가 되살아나고 토큰 방어가 다시 필요하다.
근거 — 2-summary 「동작 방식 (3)」 · 「어디서 틀리나 5」 (원본 팁을 좁힌 것 — 원본에 근거 없음 — 추론).

### 6. 개발 환경과 공개 라우트 하나에는 되고, 프로덕션 전체에는 안 된다

`CORS_ALLOW_ALL_ORIGINS = True` 는 개발용이며 프로덕션에서 금지다.
프로덕션에서는 `allowed_origins` 를 명시적으로 지정한다.
누구나 읽어도 되는 `/api/public` 같은 라우트 하나만 `@cross_origin(origins='*')` 로 따로 연다.
근거 — 원본 팁, 2-summary 「어디서 틀리나 2」 · 「언제 쓰고 언제 안 쓰나」.

### 7. 바깥 스크립트도 인라인 스크립트도 실행되지 않는다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
`https://other.example.net/x.js` 는 `script-src` 목록(`'self'` · CDN)에 없으므로 브라우저가 불러와 실행하지 않는다.
`script-src` 에 `'unsafe-inline'` 이 없으므로 인라인 `<script>` 도 실행되지 않는다.

**왜 그런가**
CSP 는 지시어마다 허용 출처만 적고, 목록에 없는 출처와 `'unsafe-inline'` 없는 인라인 코드는 막는다.
`'unsafe-inline'` 은 `style-src` 에만 있어 인라인 스타일만 허용된다.
근거 — 2-summary 「동작 방식 (4)」.

### 8. 끼워 넣은 스크립트가 「실행되는」 단계를 끊는다

XSS 는 공격자의 스크립트가 남의 페이지에서 실행되어야 해를 끼친다.
CSP 는 허용한 출처 밖의 스크립트와 인라인 스크립트의 실행을 브라우저가 거부하게 하므로, 스크립트가 페이지에 끼어들어도 실행까지 가기 어렵다.
그래서 「막는다」가 아니라 「공격 표면을 줄인다」고 말한다 — 이스케이프 같은 다른 방어와 함께 쓴다.
근거 — 원본 팁, 2-summary 「동작 방식 (4)」 · 「어디서 틀리나 7」.

### 9. 둘 다 모든 요청 · 응답이 지나가는 처리 자리이고, CORS 는 맨 앞이어야 빠지는 응답이 없다

`@app.after_request` 는 모든 응답을 가로채는 훅이고, Django `MIDDLEWARE` 는 요청 · 응답 처리 체인이다 — 둘 다 응답마다 헤더를 일괄로 붙이는 자리다.
Django 체인은 순서가 중요하다.
앞쪽 미들웨어가 응답을 먼저 만들어 돌려보내면 그보다 뒤에 있는 `CorsMiddleware` 는 그 응답에 CORS 헤더를 붙이지 못할 수 있으므로 최상단에 둔다(확인 필요).
근거 — 2-summary 「동작 방식 (2)」 · 「어디서 틀리나 9」.

## 실습 정답

### 실습 1. Flask · Django 웹 보안 설정 모음 만들기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. `/api/*` CORS 정책 | `CORS(app, resources={r'/api/*': {...}})` 의 `origins` · `methods` · `allow_headers` · `expose_headers` · `supports_credentials` · `max_age` |
| 2. 공개 라우트 | `@cross_origin(origins='*')` + `public_api()` 의 `jsonify({'data': 'public'})` |
| 3. 수동 화이트리스트 훅 | `add_cors_headers` 의 `request.headers.get('Origin')` · `if origin in allowed_origins:` |
| 4. Django 앱 등록 · 미들웨어 순서 | `INSTALLED_APPS = ['corsheaders', ...]` · `MIDDLEWARE` 첫 줄 `CorsMiddleware` |
| 5. Django CORS 설정 | `CORS_ALLOWED_ORIGINS` · `CORS_ALLOW_METHODS` · `CORS_ALLOW_HEADERS` · `CORS_ALLOW_CREDENTIALS` · `CORS_PREFLIGHT_MAX_AGE` · 주석 처리한 `CORS_ALLOW_ALL_ORIGINS` |
| 6. Django CSRF 쿠키 | `CSRF_COOKIE_SECURE` · `CSRF_COOKIE_HTTPONLY` · `CSRF_COOKIE_SAMESITE` · `CSRF_TRUSTED_ORIGINS` |
| 7. 면제 뷰 · 토큰 뷰 | `@csrf_exempt` `api_endpoint` · `@ensure_csrf_cookie` `get_csrf` |
| 8. Flask CSRF 보호 | `csrf = CSRFProtect(app)` · `app.config['WTF_CSRF_TIME_LIMIT']` |
| 9. webhook 면제 · 토큰 엔드포인트 | `@csrf.exempt` `webhook()` · `csrf_token()` 의 `generate_csrf()` |
| 10. 일곱 보안 헤더 | `set_security_headers` 의 `X-Content-Type-Options` … `Permissions-Policy` |
| 11. Django 보안 설정 | `SECURE_BROWSER_XSS_FILTER` … `SESSION_COOKIE_HTTPONLY` 여덟 줄 |
| 12. 정리 문장 | 파일 끝 `print(...)` 들 |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`python/python-web/reference/cors-csrf.py`

```python
# [웹 프레임워크] CORS & CSRF (보안 설정)
# 설명: CORS 설정, CSRF 보호, 보안 헤더 적용
# 팁: CORS는 브라우저의 보안 메커니즘이므로 서버 간 통신에는 적용되지 않는다. CSRF 토큰은 상태가 있는 세션 인증에 필수이며, JWT 같은 토큰 인증에는 불필요하다. CSP 헤더로 XSS 공격 표면을 줄인다. 프로덕션에서는 allowed_origins를 명시적으로 지정한다.

# CORS & CSRF - 웹 보안 설정

# === 1. CORS (Cross-Origin Resource Sharing) ===
# 다른 도메인에서의 요청을 허용/차단하는 메커니즘 (브라우저 강제 정책)

# --- Flask CORS ---
# pip install flask-cors
# Flask 핵심 객체와 응답 헬퍼 import
from flask import Flask, jsonify, request, make_response
# flask-cors: CORS 헤더 자동 처리 확장
from flask_cors import CORS

# WSGI 기반 Flask 앱 생성
app = Flask(__name__)

# 전체 앱에 CORS 적용
# resources: 경로 패턴별 CORS 정책 매핑
CORS(app, resources={
    r'/api/*': {
        # 허용할 출처(origin) 목록 - 프로덕션에서는 명시 필수
        'origins': ['https://frontend.example.com', 'http://localhost:3000'],
        # 허용 HTTP 메서드
        'methods': ['GET', 'POST', 'PUT', 'DELETE'],
        # 허용 요청 헤더 (Authorization 등 커스텀 헤더 명시)
        'allow_headers': ['Content-Type', 'Authorization'],
        # 클라이언트 JS가 읽을 수 있는 응답 헤더 노출
        'expose_headers': ['X-Total-Count'],
        'supports_credentials': True,   # 쿠키 포함 허용
        'max_age': 3600,                # preflight 캐시 1시간
    }
})

# 특정 라우트만 CORS - 데코레이터 방식으로 라우트별 적용
from flask_cors import cross_origin

# @app.route: 데코레이터로 URL을 함수에 매핑 (Flask 라우팅 등록 방식)
@app.route('/api/public')
@cross_origin(origins='*')   # 모든 오리진 허용
def public_api():
    # jsonify: dict를 JSON 응답으로 직렬화
    return jsonify({'data': 'public'})

# 수동 CORS 헤더 설정
# @app.after_request: 모든 응답을 가로채는 미들웨어 훅
@app.after_request
def add_cors_headers(response):
    # 요청의 Origin 헤더 확인
    origin = request.headers.get('Origin')
    allowed_origins = ['https://frontend.example.com']
    # 화이트리스트 검증 후 동적으로 헤더 설정
    if origin in allowed_origins:
        response.headers['Access-Control-Allow-Origin'] = origin
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        # 쿠키/인증정보 포함 허용
        response.headers['Access-Control-Allow-Credentials'] = 'true'
    return response


# --- Django CORS ---
# pip install django-cors-headers
# settings.py 설정 예시
# INSTALLED_APPS: Django 앱 등록 리스트
INSTALLED_APPS = ['corsheaders', ...]
# MIDDLEWARE: 요청/응답 처리 체인 (순서 중요)
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',  # 최상단에 위치
    'django.middleware.common.CommonMiddleware',
    ...
]

# CORS_ALLOWED_ORIGINS: 허용 출처 화이트리스트
CORS_ALLOWED_ORIGINS = [
    'https://frontend.example.com',
    'http://localhost:3000',
]
CORS_ALLOW_METHODS = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS']
CORS_ALLOW_HEADERS = ['content-type', 'authorization', 'x-csrftoken']
# 쿠키 기반 인증 시 True 필요
CORS_ALLOW_CREDENTIALS = True
# preflight 결과 캐시 시간
CORS_PREFLIGHT_MAX_AGE = 3600
# CORS_ALLOW_ALL_ORIGINS = True  # 개발용: 모든 오리진 허용 (프로덕션 금지!)


# === 2. CSRF (Cross-Site Request Forgery) ===

# --- Django CSRF ---
# Django는 기본으로 CSRF 보호 활성화 (CsrfViewMiddleware)
# settings.py
# HTTPS에서만 쿠키 전송 (보안 강화)
CSRF_COOKIE_SECURE = True       # HTTPS에서만 CSRF 쿠키 전송
# JavaScript에서 토큰을 읽어야 하므로 False
CSRF_COOKIE_HTTPONLY = False     # JavaScript에서 접근 필요 (AJAX)
# Lax: 다른 사이트에서의 GET만 허용 (기본 권장값)
CSRF_COOKIE_SAMESITE = 'Lax'    # SameSite 속성
# 신뢰할 출처 (서브도메인 분리 시 필수)
CSRF_TRUSTED_ORIGINS = ['https://frontend.example.com']

# 템플릿에서 사용 - {% csrf_token %} 태그가 hidden input 자동 삽입
# <form method="post">
#     {% csrf_token %}
#     ...
# </form>

# AJAX 요청 시 (JavaScript) - 헤더 X-CSRFToken에 토큰 실어 전송
# const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;
# fetch('/api/data', {
#     method: 'POST',
#     headers: {'X-CSRFToken': csrftoken},
#     body: JSON.stringify(data)
# });

# 특정 뷰에서 CSRF 면제 (API용)
# csrf_exempt: CSRF 검사 비활성화 데코레이터
# ensure_csrf_cookie: 응답에 CSRF 쿠키 강제 설정
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie

@csrf_exempt    # CSRF 검사 비활성화 (JWT 인증 API에서 사용)
def api_endpoint(request):
    pass

@ensure_csrf_cookie   # CSRF 쿠키가 항상 설정되도록
def get_csrf(request):
    # SPA에서 초기 토큰을 받아오기 위한 엔드포인트 패턴
    return JsonResponse({'csrfToken': request.META.get('CSRF_COOKIE')})


# --- Flask CSRF ---
# pip install flask-wtf
# CSRFProtect: 앱 전역 CSRF 보호, generate_csrf: 토큰 생성 헬퍼
from flask_wtf.csrf import CSRFProtect, generate_csrf

# 앱에 CSRF 보호 적용 (모든 POST/PUT/DELETE 검증)
csrf = CSRFProtect(app)
# 토큰 유효 시간 설정 (초 단위)
app.config['WTF_CSRF_TIME_LIMIT'] = 3600  # 토큰 유효 시간

# 특정 뷰 CSRF 면제 - 외부 webhook 같은 경우
@csrf.exempt
@app.route('/webhook', methods=['POST'])
def webhook():
    return 'OK'

# AJAX용 CSRF 토큰 제공 엔드포인트
@app.route('/api/csrf-token')
def csrf_token():
    # generate_csrf(): 새 토큰 생성하여 반환
    return jsonify({'csrf_token': generate_csrf()})


# === 3. 보안 헤더 ===

# Flask 보안 헤더 미들웨어
# after_request로 모든 응답에 보안 헤더 일괄 추가
@app.after_request
def set_security_headers(response):
    # XSS 방지
    # MIME 타입 스니핑 방지
    response.headers['X-Content-Type-Options'] = 'nosniff'
    # iframe 임베드 방지 (클릭재킹)
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'       # 클릭재킹 방지
    # 구형 브라우저 XSS 필터 활성화
    response.headers['X-XSS-Protection'] = '1; mode=block'

    # Content Security Policy - 리소스 출처 제한 정책
    response.headers['Content-Security-Policy'] = (
        # default-src: 기본 출처 (자기 도메인만 허용)
        "default-src 'self'; "
        # script-src: 스크립트 허용 출처 (CDN 명시)
        "script-src 'self' https://cdn.example.com; "
        # 인라인 스타일 허용 (보안상 권장하지 않음)
        "style-src 'self' 'unsafe-inline'; "
        # img-src: data URI, https 허용
        "img-src 'self' data: https:; "
        "font-src 'self' https://fonts.googleapis.com; "
    )

    # HTTPS 강제 (HSTS) - 1년 동안 HTTPS만 사용하도록 브라우저에 지시
    response.headers['Strict-Transport-Security'] = (
        'max-age=31536000; includeSubDomains'
    )

    # Referrer 정책 - 다른 출처 이동 시 Referer 노출 제어
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'

    # 권한 정책 - 브라우저 API(카메라/마이크 등) 접근 제어
    response.headers['Permissions-Policy'] = (
        'camera=(), microphone=(), geolocation=()'
    )
    return response


# Django 보안 설정 (settings.py)
# X-XSS-Protection 헤더 자동 설정
SECURE_BROWSER_XSS_FILTER = True
# X-Content-Type-Options: nosniff
SECURE_CONTENT_TYPE_NOSNIFF = True
# X-Frame-Options 값
X_FRAME_OPTIONS = 'SAMEORIGIN'
# HSTS max-age
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
# HTTP를 HTTPS로 자동 리다이렉트
SECURE_SSL_REDIRECT = True
# 세션 쿠키 보안 설정
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True


print("CORS & CSRF 보안 핵심 정리")
print("="*50)
print("CORS: 다른 도메인 요청 허용/차단 (서버 측 헤더)")
print("CSRF: 위조 요청 방지 (토큰 기반 검증)")
print("CSP: 허용된 리소스 출처 제한")
print("HSTS: HTTPS 강제")
print("X-Frame-Options: 클릭재킹 방지")
print("프로덕션에서 CORS_ALLOW_ALL_ORIGINS는 절대 True 금지!")
```

**실행 결과** — 실행하지 않음 — 외부 라이브러리 `flask` 가 있어야 도는 예제다 — 그것 없이 만들어 실행하지 않았다.

**풀이 요점**
- CORS 는 세 자리(경로 정책 · 라우트 데코레이터 · 수동 훅)로 걸 수 있지만, 실제 앱에서는 한 방식만 고른다 — 정답 코드는 방식을 나란히 보인 모음이다.
- 수동 훅은 `*` 이 아니라 검사를 통과한 오리진 문자열을 그대로 되돌려 준다.
- CSRF 쿠키는 JS 가 읽어야 하므로 `HTTPONLY = False`, 세션 쿠키는 `True` 다.
- 면제(`csrf_exempt` · `csrf.exempt`)는 쿠키 자동 전송이 없는 JWT 헤더 API 와 외부 webhook 에만 쓴다.
- `get_csrf` 를 실제로 쓰려면 `from django.http import JsonResponse` 가 더 필요하다(정답 코드에 빠져 있다).
- 보안 헤더는 `after_request` 와 Django settings 로 응답마다 일괄 적용하고, 그중 `X-XSS-Protection` 은 구형 브라우저용이라 CSP 가 중심이다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — 외부 라이브러리 `flask` 가 있어야 도는 예제다 — 그것 없이 만들어 실행하지 않았다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
