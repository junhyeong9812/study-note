# python/python-web/13 — CORS & CSRF (보안 설정) — 정리 (힌트)

> 출처 — study-site 항목 `python/cors-csrf`(항목 데이터 `data/python/web-frameworks.json`) · 정답 코드 study-practice `python/python-web/reference/cors-csrf.py`\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).\
> 실행 — 실행하지 않음 — 외부 라이브러리 `flask` 가 있어야 도는 예제다 — 그것 없이 만들어 실행하지 않았다.

## 한눈에 — 쉽게 말하면

**CORS 는 「건물 경비원의 방문자 명단」이고, CSRF 토큰은 「본인만 아는 암호」다.**
아파트 경비원(브라우저)은 손님(다른 사이트의 스크립트)이 주민(서버)의 물건을 들고 나가려 할 때 주민이 써 둔 명단(응답 헤더)을 본다.
명단에 손님의 이름(오리진)이 있으면 내보내고, 없으면 막는다.
경비원이 없는 뒷문(서버 간 통신)에는 명단이 소용없다.
CSRF 는 반대 방향의 문제다.
누군가 주민의 이름으로 택배 반품 요청서를 위조해 보내면, 관리실(서버)은 요청서에 「주민만 아는 암호(토큰)」가 적혀 있는지로 진짜를 가른다.
웹 보안 설정도 똑같은 구조다.

| 비유 | 실체 |
|---|---|
| 경비원 | 브라우저 |
| 방문자 명단 | `Access-Control-Allow-Origin` 같은 CORS 응답 헤더 |
| 손님의 이름 | 요청의 `Origin` 헤더 |
| 뒷문 | 서버 간 통신(브라우저를 거치지 않는 호출) |
| 위조 요청서 | CSRF 공격 요청 |
| 주민만 아는 암호 | CSRF 토큰 |
| 건물 출입 규칙 게시판 | 보안 헤더(CSP · HSTS · X-Frame-Options …) |

```text
 다른 오리진의 JS ──요청(Origin: A)──▶ 서버
                                         │ A 가 화이트리스트에 있나?
 브라우저 ◀──응답 + Allow-Origin: A ─────┘
   └─ 헤더가 맞으면 JS 에 응답을 넘기고, 아니면 막는다
```

## 이 주제가 답하려는 질문

1. 다른 오리진에서 온 브라우저 요청을 서버는 어떻게 허용하고, 누가 실제로 막나?
2. 사용자의 쿠키를 등에 업은 위조 요청을 서버는 어떻게 가려내나?
3. 응답 헤더 몇 줄로 XSS · 클릭재킹 · HTTP 다운그레이드의 공격 표면을 어떻게 줄이나?
4. Flask 와 Django 는 같은 설정을 각각 어디에, 어떤 꼴로 쓰나?

## 동작 방식

### (1) CORS — 서버가 명단을 쓰고 브라우저가 지킨다

**언제 쓰나** — 프런트엔드(`frontend.example.com`, 개발 중 `localhost:3000`)와 API 서버의 오리진이 다를 때 쓴다.
브라우저 안의 JS 가 다른 오리진의 응답을 읽게 하려면 서버가 허락 헤더를 내줘야 한다.

> **오리진(origin)** — 스킴 · 호스트 · 포트의 묶음이다.\
> 예: `https://frontend.example.com` 과 `http://localhost:3000` 은 서로 다른 오리진이다.

> **CORS(Cross-Origin Resource Sharing)** — 다른 오리진에서 온 요청을 허용 · 차단하는 브라우저 강제 정책이다.\
> 예: 서버가 `Access-Control-Allow-Origin` 을 돌려주지 않으면 브라우저가 JS 에 응답을 넘기지 않는다.

```text
요청 헤더 Origin: https://frontend.example.com
        │
        ▼
add_cors_headers(response)                ← @app.after_request 훅
  origin = request.headers.get('Origin')  → 'https://frontend.example.com'
  origin in allowed_origins ?             → True
        │
        ▼
응답에 붙는 헤더
  Access-Control-Allow-Origin: https://frontend.example.com
  Access-Control-Allow-Methods: GET, POST, PUT, DELETE
  Access-Control-Allow-Headers: Content-Type, Authorization
  Access-Control-Allow-Credentials: true
```

- 훅은 요청의 `Origin` 헤더를 읽는다.
- 헤더가 없으면 `request.headers.get('Origin')` 은 `None` 을 돌려준다.
- `origin in allowed_origins` 는 화이트리스트 검사다 — `None` 이나 목록에 없는 문자열이면 `False` 라서 CORS 헤더를 하나도 붙이지 않는다.
- 목록에 있으면 `*` 이 아니라 그 오리진 문자열을 그대로 되돌려 준다(동적 설정).
- `Access-Control-Allow-Credentials: true` 는 쿠키 · 인증 정보가 실린 요청의 응답도 읽게 해 준다.
- 서버는 헤더를 쓸 뿐이고, 응답을 JS 에 넘길지 정하는 쪽은 브라우저다.
- 그래서 브라우저를 거치지 않는 서버 간 통신에는 CORS 가 적용되지 않는다.

**preflight** — 원본 설정의 `max_age: 3600` 은 「preflight 캐시 1시간」이다.

> **preflight** — 본 요청 전에 브라우저가 「이 메서드 · 헤더로 보내도 되나」를 먼저 묻는 사전 요청이다(Django 설정의 `OPTIONS` 메서드가 이것이다).\
> 예: `Authorization` 헤더를 단 `PUT` 요청 앞에 `OPTIONS` 요청이 먼저 간다.

```text
브라우저 ──OPTIONS (사전 확인)──▶ 서버
브라우저 ◀── 허용 메서드·헤더, max-age 3600 ──┘
   (3600초 동안 같은 확인을 다시 하지 않는다)
브라우저 ──PUT (본 요청)──▶ 서버
```

- `allow_headers` 에 `Authorization` 처럼 커스텀 헤더를 적어야 그 헤더를 단 요청이 허락된다.
- `expose_headers` 의 `X-Total-Count` 는 반대 방향이다 — JS 가 **응답**에서 읽을 수 있게 노출할 헤더다.

### (2) Flask 와 Django 에서 CORS 를 거는 세 자리

**언제 쓰나** — 앱 전체 정책, 라우트 하나의 예외, 손으로 짠 규칙 중 무엇이 필요한지에 따라 고른다.

```text
Flask
  CORS(app, resources={r'/api/*': {...}})   → 경로 패턴별 정책 (flask-cors)
  @cross_origin(origins='*')                → 라우트 하나만 (모든 오리진)
  @app.after_request + 헤더 직접 대입         → 수동

Django (settings.py)
  INSTALLED_APPS 에 'corsheaders'
  MIDDLEWARE 맨 위에 'corsheaders.middleware.CorsMiddleware'
  CORS_ALLOWED_ORIGINS / CORS_ALLOW_METHODS / CORS_ALLOW_HEADERS
  CORS_ALLOW_CREDENTIALS / CORS_PREFLIGHT_MAX_AGE
```

- `resources` 는 경로 패턴(정규식 `r'/api/*'`)을 정책 딕셔너리에 매핑한다.
- `@cross_origin(origins='*')` 은 `/api/public` 처럼 공개해도 되는 라우트만 넓게 연다.
- `@app.after_request` 는 모든 응답을 가로채는 훅이다 — 미들웨어처럼 쓴다.
- Django 의 `MIDDLEWARE` 는 요청 · 응답 처리 체인이고 순서가 중요하다.
- 원본은 `CorsMiddleware` 를 최상단에 두라고 한다.
- 체인 앞쪽의 미들웨어가 응답을 먼저 만들어 돌려보내면, 그보다 뒤에 있는 미들웨어는 그 응답에 손대지 못할 수 있기 때문이다(확인 필요).
- Django 의 허용 헤더 목록에는 `x-csrftoken` 이 들어 있다 — 다른 오리진의 JS 가 CSRF 토큰 헤더를 실어 보내야 하기 때문이다.
- `CORS_ALLOW_ALL_ORIGINS = True` 는 개발용이고 프로덕션에서는 금지다.

> **미들웨어(middleware)** — 모든 요청 · 응답이 지나가는 처리 단계다.\
> 예: Django 의 `CsrfViewMiddleware` 가 POST 요청마다 토큰을 검사한다.

### (3) CSRF — 쿠키는 저절로 실리고, 토큰은 저절로 실리지 않는다

**언제 쓰나** — 세션 쿠키로 로그인 상태를 유지하는(상태가 있는) 인증에서 필수다.

> **CSRF(Cross-Site Request Forgery)** — 로그인한 사용자의 브라우저가 공격 사이트에서 의도하지 않은 요청을 보내게 만드는 공격이다.\
> 예: 악성 페이지의 숨은 폼이 은행 사이트로 송금 POST 를 보낸다.

```text
공격 페이지 ──POST /transfer──▶ 서버
   브라우저가 세션 쿠키를 자동으로 붙인다   → 쿠키만으로는 진짜와 구별이 안 된다
   CSRF 토큰은 붙일 수 없다                → 토큰이 없거나 틀림 → 서버가 거부

진짜 페이지 ──POST + 토큰──▶ 서버
   폼 hidden input 또는 X-CSRFToken 헤더   → 토큰이 맞음 → 통과
```

- 공격이 성립하는 까닭은 브라우저가 쿠키를 요청에 자동으로 싣기 때문이다.
- 토큰은 진짜 페이지만 알고 있어서 공격 페이지가 요청에 넣을 수 없다.
- Django 는 기본으로 CSRF 보호가 켜져 있다(`CsrfViewMiddleware`).
- 폼은 템플릿의 `{% csrf_token %}` 태그가 hidden input(`csrfmiddlewaretoken`)을 자동으로 넣는다.
- AJAX 는 그 값을 읽어 `X-CSRFToken` 헤더에 실어 보낸다.
- JS 가 CSRF 쿠키를 읽어야 할 때가 있어서 `CSRF_COOKIE_HTTPONLY = False` 로 둔다.
- `CSRF_COOKIE_SECURE = True` 는 HTTPS 에서만 쿠키를 보내게 한다.
- `CSRF_COOKIE_SAMESITE = 'Lax'` 는 쿠키의 SameSite 속성이다.
- `CSRF_TRUSTED_ORIGINS` 는 신뢰할 출처 목록이다 — 서브도메인을 나눴을 때 필수라고 원본은 말한다.
- `@ensure_csrf_cookie` 는 응답에 CSRF 쿠키를 강제로 설정한다 — SPA 가 처음 토큰을 받아 가는 엔드포인트 패턴이다.
- `@csrf_exempt` 는 그 뷰의 CSRF 검사를 끈다 — JWT 인증 API 에서 쓴다.
- JWT 를 `Authorization` 헤더로 보내면 브라우저가 자동으로 싣지 않으므로 CSRF 의 전제(자동 전송)가 사라진다.
- 반대로 JWT 를 쿠키에 담으면 다시 자동으로 실리므로 CSRF 방어가 다시 필요하다.

> **CSRF 토큰** — 서버가 발급하고 요청마다 되돌려 받아 대조하는 비밀 값이다.\
> 예: Flask 의 `generate_csrf()` 가 새 토큰을 만든다.

Flask 쪽은 `flask-wtf` 다.

```text
csrf = CSRFProtect(app)                  → 모든 POST/PUT/DELETE 에 토큰 검증
app.config['WTF_CSRF_TIME_LIMIT'] = 3600 → 토큰 유효 시간(초)
@csrf.exempt  /webhook                   → 외부 webhook 은 토큰을 못 가져오므로 면제
/api/csrf-token → generate_csrf()        → AJAX 가 토큰을 받아 가는 자리
```

- 외부 서비스가 부르는 webhook 은 브라우저 세션이 아니어서 토큰을 낼 수 없다 — 그래서 면제한다.

### (4) 보안 헤더 — 응답마다 붙이는 브라우저 규칙

**언제 쓰나** — 모든 응답에 일괄로 붙인다(Flask 는 `after_request`, Django 는 settings).

```text
set_security_headers(response)
  X-Content-Type-Options: nosniff          → MIME 타입 스니핑 금지
  X-Frame-Options: SAMEORIGIN              → 남의 iframe 에 안 실림 (클릭재킹)
  X-XSS-Protection: 1; mode=block          → 구형 브라우저 XSS 필터
  Content-Security-Policy: ...             → 리소스 출처 제한
  Strict-Transport-Security: max-age=31536000; includeSubDomains → 1년간 HTTPS 만
  Referrer-Policy: strict-origin-when-cross-origin → 다른 출처로 갈 때 Referer 노출 제어
  Permissions-Policy: camera=(), microphone=(), geolocation=() → 브라우저 API 차단
```

- CSP 는 「이 페이지가 어디서 온 리소스만 써도 되나」를 적는다.
- `default-src 'self'` 는 기본값으로 자기 도메인만 허용한다.
- `script-src 'self' https://cdn.example.com` 은 스크립트를 자기 도메인과 그 CDN 에서만 받는다.
- 목록에 없는 출처의 스크립트와 `'unsafe-inline'` 이 없는 지시어의 인라인 코드는 브라우저가 실행하지 않는다.
- `style-src` 에는 `'unsafe-inline'` 이 있어 인라인 스타일이 허용된다 — 원본도 보안상 권장하지 않는다고 적었다.
- `img-src 'self' data: https:` 는 data URI 와 모든 https 이미지를 허용한다.
- 공격자가 페이지에 스크립트를 끼워 넣어도 CSP 가 실행을 막으므로 XSS 의 공격 표면이 줄어든다.

> **XSS(Cross-Site Scripting)** — 공격자의 스크립트가 남의 페이지 안에서 실행되게 하는 공격이다.\
> 예: 댓글에 `<script>` 를 넣어 다른 사용자의 브라우저에서 돌게 한다.

> **클릭재킹** — 투명한 iframe 으로 진짜 사이트를 덮어 사용자가 모르게 버튼을 누르게 하는 공격이다.\
> 예: 「경품 받기」 버튼 아래에 숨은 「계정 삭제」 버튼.

Django 는 같은 것을 설정 값으로 켠다.

| Django 설정 | 하는 일 |
|---|---|
| `SECURE_BROWSER_XSS_FILTER = True` | `X-XSS-Protection` 헤더 |
| `SECURE_CONTENT_TYPE_NOSNIFF = True` | `X-Content-Type-Options: nosniff` |
| `X_FRAME_OPTIONS = 'SAMEORIGIN'` | `X-Frame-Options` 값 |
| `SECURE_HSTS_SECONDS = 31536000` | HSTS `max-age` |
| `SECURE_HSTS_INCLUDE_SUBDOMAINS = True` | HSTS 를 서브도메인까지 |
| `SECURE_SSL_REDIRECT = True` | HTTP 를 HTTPS 로 리다이렉트 |
| `SESSION_COOKIE_SECURE = True` | 세션 쿠키를 HTTPS 에서만 |
| `SESSION_COOKIE_HTTPONLY = True` | 세션 쿠키를 JS 가 못 읽게 |

- 세션 쿠키는 `HTTPONLY = True`, CSRF 쿠키는 `HTTPONLY = False` 다 — JS 가 읽을 필요가 있는지가 다르다.

## 문법 — 형태와 규칙

```python
# 최소 예: Flask 에서 CORS 화이트리스트 + 보안 헤더 하나
from flask import Flask, request

app = Flask(__name__)
ALLOWED = ['https://frontend.example.com']

@app.after_request
def cors_and_headers(response):
    origin = request.headers.get('Origin')        # 없으면 None
    if origin in ALLOWED:                         # 화이트리스트
        response.headers['Access-Control-Allow-Origin'] = origin
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    return response                               # 반드시 돌려준다
```

- `@app.after_request` 함수는 `response` 를 받아 **돌려줘야** 한다.
- 허용 오리진은 목록으로 명시한다 — 프로덕션에서 `*` 이나 `CORS_ALLOW_ALL_ORIGINS = True` 를 쓰지 않는다.
- 자격 증명(쿠키)을 허용하려면 Flask 는 `supports_credentials: True`, Django 는 `CORS_ALLOW_CREDENTIALS = True` 다.
- Django CORS 는 `INSTALLED_APPS` 등록 + `MIDDLEWARE` 맨 위 + `CORS_*` 설정의 세 곳을 함께 채운다.
- Django CSRF 면제는 `@csrf_exempt`, 쿠키 강제는 `@ensure_csrf_cookie` 다.
- Flask CSRF 는 `CSRFProtect(app)` 로 켜고 `@csrf.exempt` 로 뺀다.
- CSP 는 `지시어 출처 출처; 지시어 출처;` 꼴의 한 문자열이다.

| 키(flask-cors `resources`) | Django 대응 | 뜻 |
|---|---|---|
| `origins` | `CORS_ALLOWED_ORIGINS` | 허용 오리진 |
| `methods` | `CORS_ALLOW_METHODS` | 허용 메서드 |
| `allow_headers` | `CORS_ALLOW_HEADERS` | 요청에 실어도 되는 헤더 |
| `expose_headers` | (원본에 없음) | JS 가 읽을 수 있는 응답 헤더 |
| `supports_credentials` | `CORS_ALLOW_CREDENTIALS` | 쿠키 포함 허용 |
| `max_age` | `CORS_PREFLIGHT_MAX_AGE` | preflight 캐시 초 |

## 어디서 틀리나

### 1. CORS 를 서버 보안이라고 믿는다

CORS 는 브라우저의 보안 메커니즘이라 서버 간 통신에는 적용되지 않는다.
CORS 헤더를 아무리 좁혀도 브라우저 밖의 클라이언트는 서버를 그대로 부를 수 있다.
API 를 지키는 것은 인증 · 권한 검사다.

### 2. 프로덕션에서 모든 오리진을 연다

`CORS_ALLOW_ALL_ORIGINS = True` 는 개발용이다.
프로덕션에서는 `allowed_origins` 를 명시적으로 지정한다.
공개 데이터만 내는 라우트(`/api/public`)만 `origins='*'` 로 따로 연다.

### 3. 같은 일을 두 방식으로 한다

원본은 flask-cors 의 `CORS(app, ...)` 와 수동 `add_cors_headers` 훅을 한 앱에 모두 건다.
두 방식은 허용 목록이 다르다 — `localhost:3000` 은 flask-cors 목록에만 있다.
실제 앱에서는 한 방식만 고른다 — 원본은 방식을 나란히 보이는 모음이다.

### 4. 한 파일에 Flask 와 Django 가 섞여 있다

Django 부분은 `settings.py` 와 뷰 파일에 나눠 들어갈 예시다.
`INSTALLED_APPS = ['corsheaders', ...]` 의 `...` 은 「나머지 앱」을 줄인 표시다(파이썬에서는 `Ellipsis` 객체가 되므로 실제 설정에 그대로 두면 안 된다).
`get_csrf` 는 `JsonResponse` 를 import 하지 않아 실제로 불리면 `NameError` 가 난다(원본에 `from django.http import JsonResponse` 가 빠졌다).

### 5. 「JWT 면 CSRF 가 필요 없다」를 무조건으로 읽는다

원본의 주장 — CSRF 토큰은 세션 인증에 필수이고 JWT 같은 토큰 인증에는 불필요하다.
왜 의심스러운가 — JWT 를 `Authorization` 헤더로 보낼 때만 맞다.
JWT 를 쿠키에 담으면 브라우저가 자동으로 실으므로 CSRF 의 전제가 되살아난다.

### 6. `CSRF_COOKIE_SAMESITE = 'Lax'` 주석

원본의 주장 — 「Lax: 다른 사이트에서의 GET 만 허용」.
왜 의심스러운가 — SameSite 는 요청 자체를 허용 · 차단하지 않고, 다른 사이트에서 시작된 요청에 쿠키를 실을지를 정한다(확인 필요).

### 7. `X-XSS-Protection` 에 기대다

원본의 주장 — `X-XSS-Protection: 1; mode=block` 으로 XSS 를 막는다.
왜 의심스러운가 — 정답 코드 주석 스스로 「구형 브라우저」 필터라고 적었다.
현대 브라우저에서 효과가 없고 최신 Django 에서 `SECURE_BROWSER_XSS_FILTER` 설정이 빠졌다는 말이 있다(확인 필요).
XSS 대책의 중심은 CSP 와 출력 이스케이프다.

### 8. CSP 에 `'unsafe-inline'` 을 넣는다

인라인 코드를 허용하면 끼워 넣은 코드도 함께 허용될 수 있다.
원본도 `style-src 'unsafe-inline'` 에 「보안상 권장하지 않음」을 달았다.

### 9. 미들웨어 순서를 아무렇게나 둔다

Django 의 `MIDDLEWARE` 는 순서가 중요한 체인이다.
`CorsMiddleware` 는 최상단에 둔다.

### 10. CSRF 쿠키를 HttpOnly 로 막는다

AJAX 가 토큰을 읽어야 하는 구성에서 `CSRF_COOKIE_HTTPONLY = True` 로 바꾸면 JS 가 토큰을 못 읽는다.
세션 쿠키(`SESSION_COOKIE_HTTPONLY = True`)와 헷갈리지 않는다.

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| `request.headers.get('Origin')` 이 헤더가 없으면 `None` | Flask/Werkzeug 의 헤더 객체(딕셔너리식 `get`) |
| `None in [문자열 목록]` 이 `False` | 파이썬 언어 |
| 서버가 보낸 CORS 헤더에 따라 응답을 JS 에 넘길지 결정 | 브라우저(웹 표준) — 서버도 파이썬도 아니다 |
| `resources` · `cross_origin` 의 옵션 이름 | flask-cors 라이브러리 |
| `CORS_*` 설정 이름, 미들웨어 순서 요구 | django-cors-headers 라이브러리 |
| CSRF 보호 기본 활성 · `csrf_exempt` · `ensure_csrf_cookie` | Django 프레임워크 |
| `CSRFProtect` · `WTF_CSRF_TIME_LIMIT` · `generate_csrf` | Flask-WTF 라이브러리 |
| `X-XSS-Protection` 의 실제 효과 | 브라우저마다 다름 — 구형만(확인 필요) |
| CSP · HSTS · X-Frame-Options 집행 | 브라우저 |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 프런트와 API 의 오리진이 다르다 | 명시한 오리진 목록 | 프로덕션의 `*` · `CORS_ALLOW_ALL_ORIGINS` |
| 누구나 읽어도 되는 공개 API 하나 | `@cross_origin(origins='*')` | 앱 전체 개방 |
| 세션 쿠키 로그인 | CSRF 토큰(`{% csrf_token %}` · `X-CSRFToken`) | `csrf_exempt` |
| `Authorization` 헤더의 JWT API | `csrf_exempt` | 쿠키에 담은 JWT 에 면제 |
| 외부 서비스의 webhook | `@csrf.exempt` | 토큰 요구 |
| SPA 가 처음 토큰이 필요하다 | `ensure_csrf_cookie` · `generate_csrf` 엔드포인트 | 토큰을 HTML 에 하드코딩 |
| 모든 응답의 보안 기본값 | `after_request` 훅 · Django `SECURE_*` 설정 | 뷰마다 헤더 복붙 |

## 핵심 문장

1. **CORS 는 서버가 쓰고 브라우저가 지키는 명단이다** — 브라우저 밖의 서버 간 통신에는 적용되지 않는다.
2. **허용 오리진은 화이트리스트로 명시한다** — 모든 오리진 허용은 개발용이다.
3. **CSRF 는 쿠키가 자동으로 실리는 데서 생긴다** — 그래서 자동으로 실리지 않는 토큰으로 막고, 쿠키를 안 쓰는 토큰 인증에서는 면제한다.
4. **보안 헤더는 응답마다 일괄로 붙인다** — CSP 는 리소스 출처를 묶어 XSS 공격 표면을 줄인다.
5. **Flask 는 확장 · 데코레이터 · `after_request`, Django 는 미들웨어 · settings 로 같은 일을 한다.**

## 관련 자료

- [django-rest](../05-django-rest/2-summary.md)
- [flask-api](../07-flask-api/2-summary.md)
- [oauth-jwt](../14-oauth-jwt/2-summary.md)
- 원본: study-site 항목 데이터 `data/python/web-frameworks.json` 의 `cors-csrf`

## 용어 풀이

- **오리진** — 스킴 · 호스트 · 포트의 묶음.
- **CORS** — 다른 오리진의 요청을 허용 · 차단하는 브라우저 정책.
- **preflight** — 본 요청 전에 브라우저가 보내는 `OPTIONS` 사전 확인 요청.
- **화이트리스트** — 허용할 것만 적은 목록.
- **자격 증명(credentials)** — 쿠키 · 인증 정보.
- **CSRF** — 사용자의 브라우저가 공격 사이트에서 위조 요청을 보내게 만드는 공격.
- **CSRF 토큰** — 서버가 발급해 요청마다 대조하는 비밀 값.
- **JWT** — 서명된 토큰을 들고 다니는 상태 없는 인증 방식.
- **webhook** — 외부 서비스가 이벤트를 알리려고 우리 서버를 부르는 요청.
- **미들웨어** — 모든 요청 · 응답이 지나가는 처리 단계.
- **`after_request`** — Flask 에서 모든 응답을 돌려주기 직전에 부르는 훅.
- **XSS** — 공격자의 스크립트가 남의 페이지에서 실행되게 하는 공격.
- **CSP** — 페이지가 쓸 수 있는 리소스 출처를 제한하는 응답 헤더.
- **HSTS** — 일정 기간 HTTPS 만 쓰라고 브라우저에 지시하는 헤더.
- **클릭재킹** — 투명 iframe 으로 사용자의 클릭을 가로채는 공격.
- **MIME 스니핑** — 브라우저가 선언된 타입 대신 내용을 보고 타입을 짐작하는 동작.
- **SameSite** — 다른 사이트에서 시작된 요청에 쿠키를 실을지 정하는 쿠키 속성.
- **HttpOnly** — JS 가 쿠키를 읽지 못하게 하는 쿠키 속성.

## 더 들어가면

- 브라우저는 `Access-Control-Allow-Origin: *` 과 자격 증명 허용을 함께 받아들이지 않는다 — 쿠키를 쓰려면 오리진을 하나로 되돌려 줘야 한다(확인 필요).
- 단순 요청(simple request)은 preflight 없이 바로 서버에 닿는다 — CORS 는 요청을 막는 게 아니라 응답을 읽는 것을 막는 경우가 많다(확인 필요).
- Flask 는 `after_request` 함수를 등록의 역순으로 부른다(확인 필요).
- `Access-Control-Max-Age` 는 브라우저마다 상한이 있어 3600 초를 다 쓰지 않을 수 있다(확인 필요).
- Flask-WTF 문서는 `@csrf.exempt` 를 `@app.route` 위에 둔 꼴을 보인다(확인 필요).
- CSP 는 `Content-Security-Policy-Report-Only` 로 먼저 보고만 받아 보며 조일 수 있다(확인 필요).
- HSTS 의 `includeSubDomains` 는 HTTPS 가 준비되지 않은 서브도메인을 끊어 버릴 수 있다(확인 필요).
