# python/python-web-deep/11 — Flask 인증: Login, 세션, JWT — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 두 줄 모두 `None` 이다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
None
None
```

**왜 그런가**
첫 줄은 세 번째 조각(서명)의 끝에 `tampered` 가 붙어, 디코딩한 서명 바이트가 다시 계산한 32바이트 서명과 달라진다.
`compare_digest` 가 거짓이 되어 `None` 이고, 혹시 디코딩에서 예외가 나더라도 `except` 가 `None` 을 돌려준다.
둘째 줄은 토큰은 멀쩡하지만 다른 키로 서명을 다시 계산하므로 값이 맞지 않아 `None` 이다.
근거: 2-summary 「동작 방식 (3)」.

### 2. 정상 관리자도 403 을 받는다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
({'error': '권한 없음'}, 403)
```

**왜 그런가**
위에 둔 `require_role` 이 바깥 껍질이라 호출 때 먼저 돈다.
`req2` 는 새 딕셔너리라 `'user'` 가 없으므로 `request.get('user', {})` 는 빈 딕셔너리이고, 역할은 `None` 이다.
`None` 은 `('admin',)` 에 없으므로 토큰 검사까지 가지도 못하고 403 이 된다.
원본 데모의 `req` 처럼 앞 호출이 이미 `'user'` 를 넣어 둔 딕셔너리를 재사용하면 우연히 통과할 수 있어, 잘못이 가려진다.
근거: 2-summary 「동작 방식 (4)」 · 「어디서 틀리나 3 · 4」.

### 3. 저장값은 서로 다르지만 둘 다 검증을 통과한다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
False
True True
```

**왜 그런가**
`hash_password` 는 부를 때마다 `os.urandom(16)` 으로 새 솔트를 만들므로 `솔트$해시` 문자열이 달라진다(무작위 16바이트가 겹칠 일은 사실상 없다).
`verify_password` 는 각 저장값에서 자기 솔트를 꺼내 같은 솔트로 다시 해싱하므로 두 경우 모두 일치한다.
근거: 2-summary 「동작 방식 (5)」.

### 4. 비교에 걸린 시간으로 서명이 어디까지 맞았는지 새어 나갈 수 있다

`==` 는 앞에서부터 비교하다 다른 바이트를 만나면 바로 멈춘다.
공격자는 걸린 시간 차이를 재서 맞는 서명을 한 바이트씩 알아낼 수 있다(타이밍 공격).
`hmac.compare_digest` 는 이런 시간 차이를 줄이도록 만든 비교라, 서명 같은 비밀 값 비교에 쓴다.
근거: 2-summary 「동작 방식 (3)」.

### 5. 세션은 요청마다 서버가 사용자를 다시 찾고, JWT 는 서명만 다시 계산한다

세션 방식은 쿠키에 담긴 id 로 `user_loader` 가 사용자 저장소를 조회해야 하므로, 서버 쪽에 상태가 있어야 한다.
JWT 는 사용자 정보와 만료 시각이 토큰 안에 들어 있고, 서버는 비밀 키로 서명만 맞춰 보면 되므로 요청 사이에 기억할 것이 없다.
근거: 2-summary 「한눈에」 · 「동작 방식 (1) · (2)」 · 「어디서 틀리나 9」.

### 6. 읽을 수는 있지만, 고치면 검증을 통과하지 못한다

payload 는 base64url 인코딩일 뿐이라 비밀 키 없이도 풀어 읽는다.
그러나 고친 payload 에 맞는 서명은 비밀 키가 있어야 만들 수 있으므로, 고친 토큰은 `decode` 에서 `None` 이 된다.
그래서 비밀 값은 payload 에 넣지 않는다.
근거: 2-summary 「동작 방식 (2) · (3)」 · 「어디서 틀리나 1」.

### 7. 누구인지 모르면 401, 누구인지는 아는데 역할이 안 맞으면 403

`require_auth` 에서 `Bearer ` 헤더가 없거나(「토큰 필요」) 토큰이 무효면(「유효하지 않은 토큰」) 401 이다.
토큰은 통과했지만 `require_role` 에서 역할이 허용 목록에 없으면 403 「권한 없음」이다.
근거: 2-summary 「동작 방식 (4)」.

### 8. `verify_password` 가 `==` 로 비교한다

`decode` 는 서명을 `compare_digest` 로 비교하지만, `verify_password` 는 `hash_password(password, salt) == stored` 로 비교한다.
코드 주석도 실무에서는 `hmac.compare_digest` 로 바꾸라고 밝혀 둔다.
근거: 2-summary 「어디서 틀리나 2」.

### 9. 짧은 access 가 만료되면 긴 refresh 로 새 access 를 받는 창구다

access 토큰은 TTL 을 짧게(예: 1시간) 두어 도난당해도 피해 기간이 짧다.
refresh 토큰은 길게 살아 있어서, `@jwt_required(refresh=True)` 가 붙은 `/refresh` 에 내면 `create_access_token` 으로 새 access 를 받는다.
그래서 사용자는 자주 다시 로그인하지 않아도 되고, 매 요청에 쓰는 토큰은 짧게 유지된다.
근거: 2-summary 「동작 방식 (6)」 · 「어디서 틀리나 9」.

### 10. `@wraps` 를 빼면 `__name__` 이 `'decorated'` 가 된다

데코레이터는 원래 함수 대신 안쪽 함수 `decorated` 를 돌려준다.
`@wraps(f)` 는 그 감싼 함수에 원래 함수의 이름 · 독스트링 같은 메타 정보를 옮겨 준다.
빼면 `get_profile` · `admin_dashboard` 모두 이름이 `decorated` 로 보여 구분이 어려워진다.
근거: 2-summary 「동작 방식 (4)」 · 「문법 — 형태와 규칙」.

## 실습 정답

### 실습 1. 세션 패턴 · JWT · 인증 데코레이터 · 비밀번호 해싱을 한 파일로

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. Flask-Login 패턴 출력 | 첫 `print("""...""")` 의 `LoginManager` · `UserMixin` · `load_user` · `login` · `dashboard` |
| 2. 키 · 알고리즘 저장 | `JWTAuth.__init__` |
| 3. base64url 인코딩 · 디코딩 | `_base64url_encode` 의 `rstrip(b'=')`, `_base64url_decode` 의 `padding` |
| 4. 토큰 생성 | `encode` 의 `header` · `payload = {**payload, 'exp': ..., 'iat': ...}` · `hmac.new(...).digest()` |
| 5. 토큰 검증 | `decode` 의 `len(parts) != 3` · `hmac.compare_digest` · `payload.get('exp', 0) < time.time()` · `except Exception` |
| 6. JWT 데모 | `jwt = JWTAuth(...)` · `token[:50]` · `len(token)` · `jwt.decode(token + "tampered")` |
| 7. 인증 데코레이터 | `require_auth` 의 `startswith('Bearer ')` · `split(' ', 1)[1]` · `request['user'] = payload` |
| 8. 역할 데코레이터 | `require_role` → `decorator` → `decorated`, `@wraps(f)` |
| 9. 보호된 함수와 테스트 | `get_profile` · `@require_auth` 아래 `@require_role('admin')` 의 `admin_dashboard` · `get_profile({'headers': {}})` |
| 10. 비밀번호 해싱 · 검증 | `hash_password` 의 `os.urandom(16).hex()` · `pbkdf2_hmac('sha256', ..., 100000)`, `verify_password` 의 `split('$', 1)` |
| 11. Flask-JWT-Extended 패턴과 정리 | 둘째 `print("""...""")` 의 `create_access_token` · `create_refresh_token` · `jwt_required(refresh=True)`, `=== 핵심 정리 ===` 아래 다섯 줄 |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`python/python-web-deep/reference/flask-auth.py`

```python
# [웹 프레임워크 심화] Flask 인증: Login, 세션, JWT
# 설명: Flask-Login 세션 인증, JWT 토큰 인증, 데코레이터 보호
# 팁: 세션 인증(Flask-Login)은 서버 상태가 필요하고, JWT는 무상태(stateless)다. JWT는 access token(짧은 TTL)과 refresh token(긴 TTL)을 분리하는 것이 보안상 좋다. 비밀번호는 반드시 pbkdf2나 bcrypt로 해싱하고, 평문 비교 대신 hmac.compare_digest를 사용한다.

"""Flask 인증: Flask-Login, JWT, 데코레이터 보호"""
# hashlib: pbkdf2/sha256 해시
import hashlib
# hmac: 타이밍 안전 비교 (compare_digest), JWT 서명
import hmac
# json: JWT 페이로드 직렬화
import json
# time: 만료 시각 계산
import time
# base64: JWT 인코딩 (url-safe)
import base64
# wraps: 데코레이터 메타 보존
from functools import wraps
# 타입 힌트
from typing import Optional

# === 1. Flask-Login 세션 인증 패턴 ===
print("=== 1. Flask-Login 패턴 ===")
# 세션 기반: 서버에 로그인 상태 저장 (쿠키-세션ID로 식별)
# UserMixin: is_authenticated/get_id 등 기본 구현 제공
print("""
from flask import Flask, redirect, url_for, request
from flask_login import (
    LoginManager, UserMixin, login_user, logout_user,
    login_required, current_user
)

app = Flask(__name__)
app.secret_key = 'your-secret-key'

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'  # 미인증 시 리다이렉트

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True)
    password_hash = db.Column(db.String(256))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/login', methods=['POST'])
def login():
    user = User.query.filter_by(username=request.form['username']).first()
    if user and user.check_password(request.form['password']):
        login_user(user, remember=True)
        return redirect(url_for('dashboard'))
    return 'Invalid credentials', 401

@app.route('/dashboard')
@login_required
def dashboard():
    return f'Hello, {current_user.username}!'
""")

# === 2. JWT 인증 구현 ===
print("=== 2. JWT 인증 구현 ===")

# JWT(JSON Web Token): header.payload.signature 3개 부분으로 구성
# 학습용 직접 구현 (실무에서는 PyJWT 라이브러리 사용 권장)
class JWTAuth:
    """간단한 JWT 인증 구현 (학습용)"""

    # 시크릿 키와 알고리즘 (HS256: HMAC-SHA256 대칭 서명)
    def __init__(self, secret: str, algorithm: str = 'HS256'):
        self.secret = secret
        self.algorithm = algorithm

    # base64url: 표준 b64에서 +,/ 제거하고 패딩(=) 제거
    def _base64url_encode(self, data: bytes) -> str:
        return base64.urlsafe_b64encode(data).rstrip(b'=').decode()

    # 디코딩 시 패딩 복원 필요
    def _base64url_decode(self, data: str) -> bytes:
        padding = 4 - len(data) % 4
        data += '=' * padding
        return base64.urlsafe_b64decode(data)

    # 토큰 생성: header + payload + HMAC 서명
    def encode(self, payload: dict, expires_in: int = 3600) -> str:
        """JWT 토큰 생성"""
        # 헤더: 알고리즘과 토큰 타입
        header = {'alg': self.algorithm, 'typ': 'JWT'}
        # 페이로드에 표준 클레임 추가 (exp: 만료, iat: 발급 시각)
        payload = {**payload, 'exp': int(time.time()) + expires_in, 'iat': int(time.time())}

        # 각 부분을 base64url 인코딩
        header_b64 = self._base64url_encode(json.dumps(header).encode())
        payload_b64 = self._base64url_encode(json.dumps(payload).encode())

        # 서명 입력: header.payload (이미 인코딩된 상태)
        signature_input = f"{header_b64}.{payload_b64}".encode()
        # HMAC-SHA256으로 서명 생성
        signature = hmac.new(self.secret.encode(), signature_input, hashlib.sha256).digest()
        signature_b64 = self._base64url_encode(signature)

        # 최종 토큰: 점(.)으로 연결
        return f"{header_b64}.{payload_b64}.{signature_b64}"

    # 토큰 검증 + 페이로드 추출
    def decode(self, token: str) -> Optional[dict]:
        """JWT 토큰 검증 및 디코딩"""
        try:
            parts = token.split('.')
            # 정확히 3개 부분이어야 유효
            if len(parts) != 3:
                return None

            header_b64, payload_b64, signature_b64 = parts

            # 서명 재계산 → 토큰의 서명과 비교
            signature_input = f"{header_b64}.{payload_b64}".encode()
            expected = hmac.new(self.secret.encode(), signature_input, hashlib.sha256).digest()
            actual = self._base64url_decode(signature_b64)

            # compare_digest: 타이밍 공격 방지 (==보다 안전)
            if not hmac.compare_digest(expected, actual):
                return None

            # 페이로드 디코딩
            payload = json.loads(self._base64url_decode(payload_b64))

            # 만료 시각 검증
            if payload.get('exp', 0) < time.time():
                return None  # 만료됨

            return payload
        except Exception:
            # 어떤 예외든 안전하게 None 반환 (오류 메시지 노출 방지)
            return None

# JWT 데모
jwt = JWTAuth(secret='my-secret-key-123')

# 토큰 생성: user_id, role을 클레임에 포함
token = jwt.encode({'user_id': 42, 'role': 'admin'}, expires_in=3600)
print(f"생성된 JWT: {token[:50]}...")
print(f"토큰 길이: {len(token)}")

# 정상 토큰 검증
payload = jwt.decode(token)
print(f"디코딩: {payload}")

# 위조 토큰 (서명 깨짐) → None 반환
fake = jwt.decode(token + "tampered")
print(f"위조 토큰: {fake}")  # None

# === 3. 인증 데코레이터 ===
print("\n=== 3. 인증 데코레이터 ===")

# JWT 인증 필수: Authorization: Bearer <token> 헤더 검증
def require_auth(f):
    """JWT 인증 필수 데코레이터"""
    @wraps(f)
    def decorated(request, *args, **kwargs):
        auth_header = request.get('headers', {}).get('Authorization', '')
        # Bearer 스킴 확인
        if not auth_header.startswith('Bearer '):
            return {'error': '토큰 필요'}, 401

        # 토큰만 추출하여 검증
        token = auth_header.split(' ', 1)[1]
        payload = jwt.decode(token)
        if not payload:
            return {'error': '유효하지 않은 토큰'}, 401

        # 검증된 사용자 정보를 요청에 첨부
        request['user'] = payload
        return f(request, *args, **kwargs)
    return decorated

# RBAC: 역할 기반 접근 제어 데코레이터 팩토리
def require_role(*roles):
    """역할 기반 접근 제어 데코레이터"""
    def decorator(f):
        @wraps(f)
        def decorated(request, *args, **kwargs):
            user = request.get('user', {})
            # 허용된 역할인지 확인 (없으면 403 Forbidden)
            if user.get('role') not in roles:
                return {'error': '권한 없음'}, 403
            return f(request, *args, **kwargs)
        return decorated
    return decorator

# 사용 예: 인증만 필요한 엔드포인트
@require_auth
def get_profile(request):
    return {'user_id': request['user']['user_id'], 'role': request['user']['role']}

# 인증 + 관리자 역할 필요 (데코레이터 스택 순서 주의: 아래가 먼저)
@require_auth
@require_role('admin')
def admin_dashboard(request):
    return {'message': '관리자 대시보드', 'user': request['user']}

# 테스트
print("\n인증된 요청:")
req = {'headers': {'Authorization': f'Bearer {token}'}}
result = get_profile(req)
print(f"  프로필: {result}")

result2 = admin_dashboard(req)
print(f"  관리자: {result2}")

# 토큰 없는 요청 → 401
print("\n인증 안 된 요청:")
result3 = get_profile({'headers': {}})
print(f"  결과: {result3}")

# === 4. 비밀번호 해싱 ===
print("\n=== 4. 비밀번호 해싱 ===")

# pbkdf2: 키 스트레칭으로 무차별 대입 공격 방어 (반복 횟수 100,000)
def hash_password(password: str, salt: str = None) -> str:
    if salt is None:
        # 솔트: 무작위 16바이트 (rainbow table 방어)
        import os
        salt = os.urandom(16).hex()
    # 100,000회 반복 sha256 (반복 횟수가 많을수록 안전, 느림)
    hashed = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
    # 솔트$해시 형태로 저장 (검증 시 솔트 추출 가능)
    return f"{salt}${hashed.hex()}"

# 같은 솔트로 다시 해싱하여 비교
def verify_password(password: str, stored: str) -> bool:
    salt, _ = stored.split('$', 1)
    # 실무에서는 hmac.compare_digest로 타이밍 공격 방어
    return hash_password(password, salt) == stored

# 해싱 데모
stored = hash_password('mypassword')
print(f"해시: {stored[:40]}...")
print(f"검증 (맞는 비밀번호): {verify_password('mypassword', stored)}")
print(f"검증 (틀린 비밀번호): {verify_password('wrong', stored)}")

# === 5. Flask-JWT-Extended 패턴 ===
print("\n=== 5. Flask-JWT-Extended ===")
# 실무 라이브러리: access(짧은 TTL) + refresh(긴 TTL) 토큰 분리 패턴
# access 만료 시 refresh로 새 access 발급 → 보안과 UX 동시 확보
print("""
from flask_jwt_extended import (
    JWTManager, create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity, get_jwt
)

app.config['JWT_SECRET_KEY'] = 'super-secret'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
jwt_manager = JWTManager(app)

@app.route('/login', methods=['POST'])
def login():
    user = authenticate(request.json)
    access_token = create_access_token(identity=user.id, additional_claims={'role': user.role})
    refresh_token = create_refresh_token(identity=user.id)
    return {'access_token': access_token, 'refresh_token': refresh_token}

@app.route('/protected')
@jwt_required()
def protected():
    user_id = get_jwt_identity()
    claims = get_jwt()
    return {'user_id': user_id, 'role': claims.get('role')}

@app.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    identity = get_jwt_identity()
    new_token = create_access_token(identity=identity)
    return {'access_token': new_token}
""")

print("=== 핵심 정리 ===")
print("Flask-Login: 세션 기반, 서버 사이드 상태")
print("JWT: 토큰 기반, 무상태 (stateless)")
print("데코레이터: @login_required, @jwt_required")
print("비밀번호: pbkdf2 + salt (werkzeug.security 권장)")
print("Refresh Token: access 만료 시 새 토큰 발급")
```

**실행 결과** — 실행하지 않음 — 돌릴 때마다 출력이 달라지는 예제다 — 출력을 싣지 않았다.

**풀이 요점**
- 서명 입력은 「이미 인코딩된」 `header_b64.payload_b64` 이고, 검증도 같은 문자열로 다시 계산한다.
- `decode` 는 서명을 먼저 맞춰 본 뒤에야 payload 를 풀고 만료를 본다.
- `require_auth` 를 위, `require_role` 을 아래에 쌓아야 사용자 정보가 먼저 붙고 역할 검사가 뒤에 돈다.
- 실패는 `(딕셔너리, 상태 코드)` 튜플, 성공은 본 함수의 딕셔너리라 반환 꼴이 다르다.
- 비밀번호는 솔트를 저장값 앞에 붙여 두어 검증 때 같은 솔트로 다시 해싱한다. 비교는 실무라면 `compare_digest` 로 바꾼다.
- Flask 관련 두 부분은 문자열 출력이라 라이브러리 없이도 파일 전체가 돈다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — 돌릴 때마다 출력이 달라지는 예제다 — 출력을 싣지 않았다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
