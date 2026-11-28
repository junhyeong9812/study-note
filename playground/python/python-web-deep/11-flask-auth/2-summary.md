# python/python-web-deep/11 — Flask 인증: Login, 세션, JWT — 정리 (힌트)

> 출처 — study-site 항목 `python/flask-auth`(항목 데이터 `data/python/django-flask-deep.json`) · 정답 코드 study-practice `python/python-web-deep/reference/flask-auth.py`\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).\
> 실행 — 실행하지 않음 — 돌릴 때마다 출력이 달라지는 예제다 — 출력을 싣지 않았다.

## 한눈에 — 쉽게 말하면

**세션 인증은 「물품 보관소 번호표」, JWT 는 「위조 방지 도장이 찍힌 손목 밴드」다.**
보관소 번호표에는 번호만 적혀 있다.
직원은 번호표를 받을 때마다 뒤편 장부를 펼쳐 누구의 짐인지 찾는다.
손목 밴드에는 이름과 등급, 유효 시각이 직접 적혀 있고, 위조를 막는 도장이 찍혀 있다.
직원은 장부 없이 도장이 진짜인지만 확인하고 들여보낸다.
Flask 인증도 똑같은 구조다.
Flask-Login 은 번호표(세션 쿠키) 방식으로, 서버가 장부(사용자 조회)를 들고 있어야 한다.
JWT 는 밴드 방식으로, 서버는 서명만 다시 계산해 맞춰 본다.

| 비유 | 실체 |
|---|---|
| 번호표 | 세션 쿠키 (사용자 id 를 담는다) |
| 뒤편 장부 | 서버 쪽 상태 · `user_loader` 가 id 로 사용자를 찾는 일 |
| 손목 밴드에 적힌 내용 | JWT 의 payload (`user_id` · `role` · `exp`) |
| 위조 방지 도장 | HMAC-SHA256 서명 |
| 밴드의 유효 시각 | `exp` 클레임 |
| 「VIP 구역은 VIP 밴드만」 | `require_role('admin')` |

```text
세션 방식                               JWT 방식
브라우저 ──쿠키(세션)──▶ 서버             클라이언트 ──Bearer 토큰──▶ 서버
                        │                                          │
                        ▼                                          ▼
                user_loader(id)                       서명 재계산 → 같으면 통과
                  → 사용자 조회                         (장부 조회 없음)
```

## 이 주제가 답하려는 질문

1. 서버는 요청을 보낸 사람이 이미 로그인했다는 것을 어떻게 기억하나 — 서버가 상태를 들고 있나, 토큰이 들고 있나?
2. 받은 토큰이 위조되지 않았고 만료되지 않았음을 어떻게 확인하나?
3. 여러 함수에 「로그인 필요」 「관리자만」 검사를 반복하지 않고 어떻게 붙이나?
4. 비밀번호를 어떤 꼴로 저장하고, 로그인할 때 어떻게 맞춰 보나?

## 동작 방식

### (1) Flask-Login — 세션 인증

**언제 쓰나** — 브라우저로 쓰는 일반 웹 페이지에서, 서버가 로그인 상태를 기억해 주면 될 때 쓴다.

세션 기반 인증은 로그인 상태를 서버 쪽에 두고, 브라우저는 쿠키로 자신을 알린다.
> **세션** — 서버가 요청과 요청 사이에 사용자에 관한 상태를 기억해 두는 방식.\
> 예: 로그인 후 쿠키만 보내면 서버가 「아까 그 사람」으로 알아본다.

```text
POST /login (username, password)
   │  User.query.filter_by(username=...).first()
   │  user.check_password(...) 가 참이면
   ▼
login_user(user, remember=True) ──▶ 세션 쿠키에 사용자 id 기록
   ...
GET /dashboard (쿠키 동봉)
   │  @login_required
   ▼
user_loader(user_id) ──▶ User.query.get(int(user_id)) ──▶ current_user
   │                                     (인증 안 됐으면 login_view 로 리다이렉트)
   ▼
'Hello, {current_user.username}!'
```

- `app.secret_key` 를 정하고 `LoginManager()` 를 만들어 `init_app(app)` 으로 앱에 붙인다.
- `login_manager.login_view = 'auth.login'` 은 로그인하지 않은 사용자가 보호된 주소에 오면 보낼 곳이다.
- `User` 는 `UserMixin` 을 함께 상속해 `is_authenticated` · `get_id` 같은 기본 구현을 얻는다.
- `@login_manager.user_loader` 가 붙은 `load_user` 는 쿠키에서 꺼낸 id 로 사용자 객체를 다시 찾는다.
- 로그인 라우트는 사용자를 찾고 비밀번호를 확인한 뒤 `login_user(user, remember=True)` 를 부르고, 실패하면 `'Invalid credentials', 401` 을 돌려준다.
- `@login_required` 가 붙은 라우트 안에서는 `current_user` 로 지금 사용자를 쓴다.
- 요청마다 id 로 사용자를 찾아야 하므로 서버 쪽 상태(사용자 저장소)가 필요하다.

이 부분은 예제에서 문자열로 출력만 하는 「패턴」이다.
`db` 같은 이름이 정의되어 있지 않으므로 그대로 실행되는 코드가 아니다.

### (2) JWT 만들기 — `encode`

**언제 쓰나** — API 서버처럼 서버가 로그인 상태를 기억하지 않고, 요청마다 토큰 하나로 사용자를 확인하고 싶을 때 쓴다.

JWT 는 `header.payload.signature` 세 부분을 점으로 이은 문자열이다.
> **JWT(JSON Web Token)** — JSON 두 덩어리와 서명을 base64url 로 인코딩해 점으로 이은 토큰.\
> 예: `xxxxx.yyyyy.zzzzz` 꼴.

```text
header  = {'alg': 'HS256', 'typ': 'JWT'}
payload = {'user_id': 42, 'role': 'admin', 'exp': 지금+3600, 'iat': 지금}
   │ json.dumps → .encode() → base64url (끝의 '=' 제거)
   ▼
header_b64 , payload_b64
   │ signature_input = "header_b64.payload_b64"
   ▼
hmac.new(secret, signature_input, sha256).digest() → base64url
   ▼
"header_b64.payload_b64.signature_b64"
```

- 헤더는 알고리즘(`HS256`, HMAC-SHA256 대칭 서명)과 토큰 종류를 적는다.
- 페이로드에 원래 내용을 펼쳐 넣고 `exp`(만료 시각)와 `iat`(발급 시각)를 덧붙인다.
- 두 덩어리를 JSON 으로 바꾼 뒤 base64url 로 인코딩한다.
- 서명은 「이미 인코딩된」 `header_b64.payload_b64` 문자열에 비밀 키로 HMAC 을 건 값이다.
- 세 부분을 점으로 이어 돌려준다.

> **클레임** — JWT 페이로드에 담긴 이름-값 한 쌍.\
> 예: `'exp'` 는 만료 시각 클레임, `'role'` 은 직접 넣은 클레임.

> **base64url** — 표준 base64 에서 URL 에 문제가 되는 `+` · `/` 를 다른 글자로 바꾼 인코딩. 이 구현은 끝의 패딩 `=` 도 떼어 낸다.\
> 예: `rstrip(b'=')` 로 패딩을 지운다.

인코딩은 암호화가 아니다.
payload 는 비밀 키 없이 base64url 을 풀기만 하면 누구나 읽을 수 있다.
비밀 키가 지키는 것은 「읽기」가 아니라 「고치기」다.

### (3) JWT 검증 — `decode`

**언제 쓰나** — 요청에 실려 온 토큰을 믿어도 되는지 판단하고 사용자 정보를 꺼낼 때 쓴다.

```text
token.split('.') ── 3조각이 아니면 → None
   │
   ▼
expected = HMAC(secret, "header_b64.payload_b64")
actual   = base64url_decode(signature_b64)  (패딩 복원 후)
   │ hmac.compare_digest(expected, actual) 가 거짓 → None
   ▼
payload = json.loads(base64url_decode(payload_b64))
   │ payload['exp'] < 지금 → None (만료)
   ▼
payload 반환
(중간에 어떤 예외가 나도 → None)
```

- 점으로 나눠 정확히 세 조각인지 본다.
- 받은 header 와 payload 로 서명을 다시 계산한다.
- 토큰에 붙어 온 서명을 디코딩해, 다시 계산한 값과 `hmac.compare_digest` 로 비교한다.
- 서명이 맞아야 비로소 payload 를 JSON 으로 푼다.
- `exp` 가 지금보다 이전이면 만료로 보고 `None` 을 돌려준다.
- `try` 로 감싸 어떤 예외가 나도 `None` 을 돌려준다(오류 내용을 밖에 드러내지 않는다).

payload 를 한 글자라도 고치면 다시 계산한 서명이 달라진다.
비밀 키를 모르는 사람은 고친 payload 에 맞는 서명을 만들 수 없다.
그래서 위조 토큰 · 다른 키로 서명된 토큰 · 조각 수가 틀린 토큰은 모두 `None` 이 된다.

> **타이밍 공격** — 비교가 걸린 시간 차이로 비밀 값을 한 글자씩 알아내는 공격.\
> 예: `==` 는 첫 글자부터 비교하다 다르면 바로 멈추므로, 앞쪽이 많이 맞을수록 조금 더 오래 걸린다.

`hmac.compare_digest` 는 이런 시간 차이를 줄이도록 만든 비교 함수다.
그래서 서명 · 해시처럼 비밀에 기대는 값은 `==` 대신 이것으로 비교한다.

### (4) 인증 데코레이터 — `require_auth` · `require_role`

**언제 쓰나** — 여러 처리 함수 앞에 같은 인증 · 권한 검사를 붙일 때 쓴다.

예제의 요청은 진짜 Flask 요청이 아니라 `{'headers': {...}}` 꼴의 딕셔너리로 흉내 낸 것이다.
> **데코레이터** — 함수를 받아 감싼 새 함수를 돌려주는 함수. `@이름` 으로 붙인다.\
> 예: `@require_auth` 를 붙이면 본 함수 앞에서 토큰 검사가 먼저 돈다.

```text
요청 ──▶ require_auth.decorated
          │ Authorization 이 'Bearer ' 로 시작? 아니면 → ({'error':'토큰 필요'}, 401)
          │ jwt.decode(토큰) 이 None?            그러면 → ({'error':'유효하지 않은 토큰'}, 401)
          │ request['user'] = payload
          ▼
        require_role('admin').decorated
          │ request['user']['role'] 이 roles 안에? 아니면 → ({'error':'권한 없음'}, 403)
          ▼
        본 함수 (admin_dashboard)
```

- `require_auth` 는 헤더에서 `Bearer ` 뒤의 토큰만 떼어(`split(' ', 1)[1]`) 검증한다.
- 검증된 payload 를 `request['user']` 에 붙여, 뒤에 오는 함수가 쓰게 한다.
- `require_role(*roles)` 는 역할 목록을 받아 데코레이터를 돌려주는 「데코레이터 팩토리」다.
- 401 은 「누구인지 모른다(인증 실패)」, 403 은 「누구인지는 알지만 권한이 없다」를 뜻한다.
- 검사에 걸리지 않으면 본 함수의 반환값(딕셔너리)을 그대로 돌려주고, 걸리면 `(딕셔너리, 상태 코드)` 튜플을 돌려준다.

> **RBAC(역할 기반 접근 제어)** — 사용자에게 역할을 주고, 역할로 허용 여부를 정하는 방식.\
> 예: `role` 이 `'admin'` 인 사용자만 관리자 대시보드를 본다.

데코레이터를 쌓을 때는 「붙이는 차례」와 「도는 차례」를 나눠 봐야 한다.

```text
@require_auth            ← 나중에 감싼다 = 바깥 껍질 = 호출 때 먼저 돈다
@require_role('admin')   ← 먼저 감싼다   = 안쪽 껍질 = 호출 때 나중에 돈다
def admin_dashboard(...)
```

- 파이썬은 함수에 가까운 아래쪽 데코레이터부터 적용한다.
- 그래서 위쪽 데코레이터가 바깥 껍질이 되고, 호출하면 바깥부터 돈다.
- `require_role` 은 `request['user']` 가 이미 있어야 일할 수 있으므로, 그것을 넣는 `require_auth` 가 바깥(위)에 있어야 한다.

`@wraps(f)` 는 감싼 함수가 원래 함수의 이름 · 독스트링 같은 메타 정보를 이어받게 한다.
이것이 없으면 감싼 함수들이 모두 `decorated` 라는 이름을 갖게 된다.

### (5) 비밀번호 해싱 — pbkdf2 + 솔트

**언제 쓰나** — 비밀번호를 저장하고, 로그인 때 맞는지 확인할 때 쓴다.

```text
hash_password('mypassword')
   │ salt = os.urandom(16).hex()      (무작위 16바이트 → 32글자 16진)
   │ hashlib.pbkdf2_hmac('sha256', 비밀번호, salt, 100000)
   ▼
"salt$해시16진"  ← 저장

verify_password(입력, 저장값)
   │ 저장값을 '$' 로 나눠 salt 를 꺼냄
   │ 같은 salt 로 입력을 다시 해싱
   ▼
다시 만든 문자열 == 저장값 ?  → True / False
```

- 솔트를 매번 무작위로 만들므로, 같은 비밀번호라도 저장값이 달라진다.
- 솔트는 미리 계산해 둔 해시 표(레인보 테이블)를 쓸모없게 만든다.
- 100,000번 반복은 해시 한 번을 일부러 느리게 만들어(키 스트레칭) 무차별 대입을 어렵게 한다.
- 반복 횟수가 많을수록 안전하지만 느려진다.
- 솔트를 해시 앞에 `$` 로 붙여 저장하므로, 검증 때 솔트를 다시 꺼낼 수 있다.
- 비밀번호는 반드시 pbkdf2 나 bcrypt 같은 방법으로 해싱한다. 원본은 직접 구현보다 `werkzeug.security` 를 권한다.

> **솔트** — 해싱 전에 비밀번호에 섞는 무작위 값.\
> 예: 같은 `'mypassword'` 도 솔트가 다르면 해시가 다르다.

### (6) access token 과 refresh token — Flask-JWT-Extended

**언제 쓰나** — 실무에서 JWT 를 쓸 때, 직접 구현 대신 라이브러리로 발급 · 검증 · 재발급을 맡길 때 쓴다.

```text
POST /login ──▶ create_access_token(identity, additional_claims={'role':..})  (짧은 TTL, 예: 1시간)
              ──▶ create_refresh_token(identity)                                (긴 TTL)
GET /protected   @jwt_required()            → get_jwt_identity(), get_jwt()
   ... access 만료 ...
POST /refresh    @jwt_required(refresh=True) → 새 access 토큰 발급
```

- `JWT_SECRET_KEY` 로 서명 키를, `JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)` 로 access 토큰 수명을 정한다.
- `@jwt_required()` 는 access 토큰을, `@jwt_required(refresh=True)` 는 refresh 토큰을 요구한다.
- `get_jwt_identity()` 는 발급 때 넣은 `identity` 를, `get_jwt()` 는 클레임 전체를 꺼낸다.
- access 토큰은 짧게 살려 도난 피해를 줄이고, 만료되면 긴 수명의 refresh 토큰으로 새 access 토큰을 받는다.
- 그래서 보안(짧은 access 수명)과 사용 편의(자주 다시 로그인하지 않음)를 함께 얻는다.

> **TTL** — 값이 유효하게 살아 있는 시간.\
> 예: access 토큰 TTL 1시간.

원본은 직접 만든 `JWTAuth` 를 학습용으로 두고, 실무에서는 PyJWT 같은 라이브러리를 쓰라고 권한다.

## 문법 — 형태와 규칙

```python
import hmac, hashlib
from functools import wraps

def sign(secret: str, msg: str) -> bytes:
    return hmac.new(secret.encode(), msg.encode(), hashlib.sha256).digest()

def require_role(*roles):          # 인자를 받는 데코레이터 = 팩토리
    def decorator(f):
        @wraps(f)                  # 이름·독스트링 보존
        def decorated(request, *args, **kwargs):
            if request.get('user', {}).get('role') not in roles:
                return {'error': '권한 없음'}, 403
            return f(request, *args, **kwargs)
        return decorated
    return decorator

ok = hmac.compare_digest(sign('k', 'a.b'), sign('k', 'a.b'))
```

- `hmac.new(키바이트, 메시지바이트, hashlib.sha256).digest()` 는 바이트 서명을 만든다. 문자열은 `.encode()` 로 바이트로 바꿔 넣는다.
- `hmac.compare_digest(a, b)` 는 비밀 값 비교에 `==` 대신 쓴다.
- `hashlib.pbkdf2_hmac('sha256', 비밀번호바이트, 솔트바이트, 반복횟수)` 는 반복 해시를 만든다.
- 인자 없는 데코레이터는 「함수 → 함수」 두 겹, 인자 있는 데코레이터는 「인자 → 데코레이터 → 함수」 세 겹이다.
- 쌓은 데코레이터는 아래부터 적용되고, 호출 때는 위부터 돈다.
- 토큰은 `Authorization: Bearer <토큰>` 헤더로 보낸다.
- Flask-Login: `LoginManager` · `UserMixin` · `@user_loader` · `login_user` · `logout_user` · `@login_required` · `current_user`.
- Flask-JWT-Extended: `JWTManager` · `create_access_token` · `create_refresh_token` · `@jwt_required()` · `@jwt_required(refresh=True)` · `get_jwt_identity` · `get_jwt`.

## 어디서 틀리나

### 1. JWT payload 를 비밀로 여긴다
payload 는 base64url 로 인코딩만 되어 있다.
비밀 키 없이도 누구나 풀어 읽는다.
비밀번호 같은 비밀 값은 payload 에 넣지 않는다.

### 2. 비밀 값 비교에 `==` 를 쓴다
원본 팁은 「평문 비교 대신 `hmac.compare_digest` 를 쓴다」고 한다.
`decode` 는 이를 지키지만, `verify_password` 는 `hash_password(password, salt) == stored` 로 비교한다.
코드 주석도 「실무에서는 `hmac.compare_digest` 로 타이밍 공격 방어」라고 적어, 학습용 단순화임을 밝힌다.

### 3. 데코레이터 쌓는 차례를 거꾸로 둔다
원본 주석은 「데코레이터 스택 순서 주의: 아래가 먼저」라고 적는다.
원본의 주장 → 「아래가 먼저」 → 왜 의심스러운가: 아래가 먼저인 것은 「감싸는 차례」이고, 호출 때 검사가 「도는 차례」는 위가 먼저다.
`require_role` 을 위에 두면 `request['user']` 가 아직 없는 채로 역할 검사가 돌아, 정상 관리자도 403 을 받는다.

### 4. 요청 딕셔너리가 고쳐진 채 남는다
`require_auth` 는 받은 `request` 에 직접 `'user'` 를 넣는다.
같은 딕셔너리를 다시 쓰면 앞 호출이 넣은 `'user'` 가 그대로 남아 있다.
예제의 `req` 도 `get_profile` 호출 뒤 `'user'` 를 가진 채 `admin_dashboard` 에 넘어간다.

### 5. 비밀 키를 코드에 박아 둔다
`'my-secret-key-123'` · `'your-secret-key'` · `'super-secret'` 은 예시 값이다.
키가 새면 누구나 유효한 토큰을 만들 수 있다.

### 6. `except Exception` 이 모든 실패를 `None` 하나로 뭉갠다
오류 내용을 밖에 드러내지 않는 장점이 있다.
대신 서명 불일치 · 만료 · 형식 오류를 구분하지 못해 원인을 찾기 어렵다.

### 7. 헤더의 `alg` 를 확인하지 않는다
`decode` 는 헤더를 읽지 않고 늘 HMAC-SHA256 으로 검증한다.
학습용 구현이라 헤더 검사를 건너뛴 것이다 (원본에 근거 없음 — 추론).

### 8. 패딩 복원 식의 끝자리
`padding = 4 - len(data) % 4` 는 길이가 4의 배수일 때 `=` 를 4개 붙인다.
남는 패딩을 디코더가 받아 주는지는 구현에 달려 있다 (확인 필요).

### 9. 세션과 JWT 의 성격을 섞는다
원본 팁: 세션 인증(Flask-Login)은 서버 상태가 필요하고, JWT 는 무상태다.
JWT 는 access token(짧은 TTL)과 refresh token(긴 TTL)을 나누는 것이 보안상 좋다.
비밀번호는 반드시 pbkdf2 나 bcrypt 로 해싱한다.

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| 데코레이터는 아래부터 적용되고 위가 바깥 껍질이 된다 | 파이썬 언어 |
| `@wraps` 가 이름 · 독스트링을 옮긴다 | 표준 라이브러리 `functools` |
| `compare_digest` 가 비교 시간 차이를 줄인다 | 표준 라이브러리 `hmac` 문서 (얼마나 줄이는지의 정도는 확인 필요) |
| 남는 `=` 패딩을 디코더가 받아 준다 | `base64` / `binascii` 구현 (확인 필요) |
| `login_view` 로 리다이렉트, `user_loader` 로 사용자 복원 | Flask-Login 라이브러리 |
| `jwt_required(refresh=True)` 가 refresh 토큰을 요구한다 | Flask-JWT-Extended 라이브러리 |
| `HS256` = HMAC-SHA256, `exp` · `iat` 의 뜻 | JWT 표준 명세 (이 구현은 그 일부만 흉내 낸다) |
| 401 은 인증 실패, 403 은 권한 없음 | HTTP 상태 코드 규약 |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 서버가 그려 주는 웹 페이지, 브라우저 로그인 | Flask-Login 세션 | 직접 만든 JWT |
| 여러 서버 · 모바일 앱이 부르는 API | JWT (access + refresh) | 서버마다 따로 기억하는 세션 |
| 실무 JWT 발급 · 검증 | Flask-JWT-Extended · PyJWT | 학습용 `JWTAuth` |
| 비밀번호 저장 | pbkdf2 · bcrypt + 솔트 (`werkzeug.security`) | 평문 · 솔트 없는 한 번짜리 해시 |
| 서명 · 해시 비교 | `hmac.compare_digest` | `==` |
| 같은 검사를 여러 함수에 | 데코레이터 | 함수마다 복사한 검사 코드 |

## 핵심 문장

1. **세션은 서버가 상태를 들고, JWT 는 토큰이 상태를 들고 서버는 서명만 확인한다.**
2. **JWT 서명은 「고치기」를 막을 뿐 「읽기」는 막지 않는다** — payload 는 누구나 읽는다.
3. **검증은 서명 → payload → 만료 차례이고, 하나라도 어긋나면 `None` 이다.**
4. **쌓은 데코레이터는 위가 먼저 돈다** — 인증이 위, 역할 검사가 아래.
5. **비밀번호는 무작위 솔트 + 반복 해시로 저장하고, 비밀 값 비교는 `compare_digest` 로 한다.**

## 관련 자료

- [flask-blueprint](../09-flask-blueprint/2-summary.md)
- [flask-testing](../12-flask-testing/2-summary.md)
- [api-rate-limit](../15-api-rate-limit/2-summary.md)
- 원본: study-site 항목 데이터 `data/python/django-flask-deep.json` 의 `flask-auth`

## 용어 풀이

- **인증** — 「누구인가」를 확인하는 일.
- **인가(권한)** — 「무엇을 해도 되나」를 정하는 일.
- **세션** — 서버가 요청 사이에 사용자 상태를 기억하는 방식.
- **쿠키** — 브라우저가 저장했다가 요청마다 서버로 보내는 작은 값.
- **무상태(stateless)** — 서버가 요청 사이에 사용자 상태를 기억하지 않는 성질.
- **`UserMixin`** — `is_authenticated` · `get_id` 등 기본 구현을 주는 Flask-Login 의 믹스인.
- **`user_loader`** — 세션의 id 로 사용자 객체를 다시 찾는 콜백.
- **`login_required`** — 로그인한 사용자만 들어오게 하는 Flask-Login 데코레이터.
- **`current_user`** — 지금 요청의 사용자.
- **JWT** — `header.payload.signature` 꼴의 서명된 토큰.
- **클레임** — payload 안의 이름-값 한 쌍.
- **`exp` / `iat`** — 만료 시각 / 발급 시각 클레임.
- **HMAC** — 비밀 키와 해시 함수로 만드는 메시지 인증 코드.
- **HS256** — HMAC-SHA256 대칭 서명 알고리즘 이름.
- **base64url** — URL 에 안전한 글자만 쓰는 base64 변형.
- **패딩** — base64 길이를 4의 배수로 맞추는 `=`.
- **타이밍 공격** — 걸린 시간 차이로 비밀을 알아내는 공격.
- **`compare_digest`** — 비교 시간 차이를 줄인 비교 함수.
- **Bearer** — `Authorization` 헤더에 토큰을 실어 보내는 방식 이름.
- **데코레이터** — 함수를 감싼 새 함수를 돌려주는 함수.
- **데코레이터 팩토리** — 인자를 받아 데코레이터를 돌려주는 함수.
- **`wraps`** — 감싼 함수에 원래 함수의 메타 정보를 옮기는 도우미.
- **RBAC** — 역할 기반 접근 제어.
- **401 / 403** — 인증 실패 / 권한 없음 상태 코드.
- **솔트** — 해싱 전에 섞는 무작위 값.
- **pbkdf2** — 해시를 여러 번 반복하는 비밀번호 해싱 방법.
- **키 스트레칭** — 반복으로 해시를 일부러 느리게 만드는 기법.
- **레인보 테이블** — 미리 계산해 둔 「비밀번호 → 해시」 표.
- **TTL** — 유효하게 살아 있는 시간.
- **access token / refresh token** — 짧게 쓰는 출입 토큰 / 새 access 를 받는 데 쓰는 긴 토큰.

## 더 들어가면

- JWT 를 만료 전에 무효로 만들려면(로그아웃 · 탈취 대응) 차단 목록 같은 서버 쪽 상태가 다시 필요하다 (확인 필요).
- refresh 토큰을 쓸 때마다 새것으로 바꿔 주는 「회전」 방식이 있다 (확인 필요).
- 헤더의 `alg` 를 믿고 검증 방식을 고르는 구현은 `alg: none` 같은 조작에 당할 수 있어, 허용 알고리즘을 고정하는 것이 보통이다 (확인 필요).
- 브라우저에 토큰을 둘 때 저장 위치(HttpOnly 쿠키 등)에 따라 노출 위험이 달라진다 (확인 필요).
- pbkdf2 반복 횟수의 권장값은 시간이 지나며 올라간다 (확인 필요).
- `werkzeug.security` 의 `generate_password_hash` · `check_password_hash` 가 솔트와 반복을 대신 처리한다 (확인 필요).
