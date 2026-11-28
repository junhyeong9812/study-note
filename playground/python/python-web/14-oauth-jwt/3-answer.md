# python/python-web/14 — OAuth2 & JWT (인증/인가) — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 검증 결과는 원래 클레임 그대로, `user_data` 는 바뀌지 않는다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
검증 결과: user=user123, role=admin
{'sub': 'user123', 'name': 'Alice', 'role': 'admin'}
```

**왜 그런가**
액세스 토큰은 `iss='myapp.com'` · `type='access'` · 1시간 뒤 `exp` 를 갖고 있어 `verify_token` 의 서명 · 만료 · 발급자 · 타입 검사를 모두 통과한다.
돌아온 payload 에는 넣었던 `sub` · `role` 이 그대로 있다.
`create_access_token` 은 `data.copy()` 에 클레임을 더하므로 `user_data` 에는 `exp` 등이 붙지 않는다.
근거: 2-summary 「동작 방식 (2)」 · 「동작 방식 (3)」.

### 2. 둘 다 예외 — 타입 검사에 닿기 전에 발급자 검사에서 걸릴 것으로 읽힌다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
(가) · (나) 모두 `ValueError('유효하지 않은 토큰: …')` 를 던진다.
`…` 자리는 발급자(`iss`)가 맞지 않는다는 python-jose 의 메시지일 것이다(정확한 문구는 확인 필요).

**왜 그런가**
`create_refresh_token` 은 `iss` 를 넣지 않는다.
`verify_token` 은 `issuer='myapp.com'` 으로 디코딩하므로, `iss` 가 없는 토큰은 `jwt.decode` 단계에서 실패한다.
`type` 검사는 디코딩이 통과한 뒤에야 하므로, (가) 에서 「잘못된 토큰 타입: refresh」 메시지는 나오지 않는다.
(나) 처럼 `'refresh'` 를 넘겨도 같은 이유로 막힌다.
근거: 2-summary 「동작 방식 (3)」 · 「어디서 틀리나 6」. (python-jose 의 `iss` 누락 처리는 원본에 근거 없음 — 추론)

### 3. 「유효하지 않은 토큰: …」 쪽이 난다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
`ValueError('유효하지 않은 토큰: …')` 가 나고, `…` 에는 만료를 알리는 python-jose 메시지가 들어간다(문구는 확인 필요).

**왜 그런가**
`expires_delta=timedelta(seconds=-1)` 이라 `exp` 가 이미 지났으므로 `jwt.decode` 는 `ExpiredSignatureError` 를 던진다.
`ExpiredSignatureError` 는 `JWTError` 의 하위 클래스다.
`except` 는 위에서부터 맞춰 보므로 `except JWTError` 가 먼저 잡고, 아래의 만료 전용 `except` 에는 닿지 않는다.
근거: 2-summary 「동작 방식 (3)」 · 「어디서 틀리나 5」.

### 4. HS256 은 검증 키가 곧 서명 키라서

HS256 은 같은 키로 서명과 검증을 한다.
여러 서비스가 검증하려면 모두 그 비밀 키를 가져야 하고, 키를 가진 서비스는 아무 사용자의 토큰이나 위조해 찍어 낼 수 있다.
키가 새는 곳도 서비스 수만큼 늘어난다.
RS256 은 발급 서버만 private key 로 서명하고, 다른 서비스는 public key 로 검증만 한다 — public key 로는 서명할 수 없다.
근거: 2-summary 「동작 방식 (4)」 · 「어디서 틀리나 1」.

### 5. 내가 시작하지 않은 로그인 응답을 걸러 CSRF 를 막으려고

`state` 비교가 없으면, 공격자가 자기 계정으로 받은 `code` 가 든 콜백 주소를 피해자 브라우저로 열게 할 수 있다.
그러면 내 서버는 그 `code` 를 교환해 피해자를 공격자 계정으로 로그인시킨다 — CSRF 다.
로그인을 시작할 때 무작위 `state` 를 세션에 넣고 콜백에서 같은지 보면, 그 세션이 시작한 흐름만 받아들이게 된다.
`session.pop` 으로 꺼내므로 같은 `state` 는 한 번만 쓰인다.
근거: 2-summary 「동작 방식 (5)」 · 「어디서 틀리나 2」.

### 6. 없다 — 액세스 토큰에는 `jti` 가 없다

`TokenBlacklist` 는 `jti` 로 폐기 여부를 가린다.
예제의 `create_access_token` 은 `jti` 를 넣지 않으므로, 폐기할 이름표가 없다.
리프레시 토큰은 끊을 수 있지만, 이미 나간 액세스 토큰은 만료(기본 1시간)까지 통과한다.
액세스 토큰도 끊으려면 `jti` 를 넣거나 만료를 짧게 둔다.
근거: 2-summary 「동작 방식 (2)」 · 「어디서 틀리나 7」.

### 7. 서명은 고치기를 막을 뿐 읽기는 막지 않는다

header 와 payload 는 인코딩만 된 것이라 토큰을 손에 넣은 누구나 풀어 읽는다.
서명은 payload 를 바꾸면 검증에서 어긋나게 할 뿐이다.
그래서 비밀번호를 넣으면 로그 · 브라우저 저장소 · 중간 경로 어디서든 토큰이 보이는 순간 비밀번호도 드러난다.
근거: 2-summary 「동작 방식 (1)」 · 「어디서 틀리나 4」.

### 8. 서버가 발급 목록을 안 갖고 있으니 「아직 유효한 토큰」을 지울 곳도 없어서

JWT 는 서명과 만료만 보고 믿으므로 서버는 세션 저장소가 필요 없다.
대신 로그아웃해도 이미 나간 토큰은 서명이 맞고 만료 전이면 계속 통과한다.
그래서 폐기된 `jti` 목록(블랙리스트)과 리프레시 토큰 DB 라는 상태를 다시 두고, 모든 요청마다 확인한다.
Redis TTL 을 토큰 만료까지로 두면 목록이 만료와 함께 저절로 줄어든다.
근거: 2-summary 「동작 방식 (6)」 · 「어디서 틀리나 3」.

### 9. 토큰으로 바꾸는 데 `client_secret` 이 필요하고, 그 비밀은 서버에만 있어서

인가 코드는 브라우저 주소를 거쳐 오므로 노출될 수 있지만, 그것만으로는 API 를 부를 수 없다.
`exchange_code` 는 서버가 `client_id` · `client_secret` · `code` · `redirect_uri` 를 붙여 토큰 엔드포인트에 POST 하는 단계다.
그래서 액세스 · 리프레시 토큰과 `client_secret` 은 브라우저를 지나지 않고 서버와 구글 사이에서만 오간다.
근거: 2-summary 「동작 방식 (5)」.

## 실습 정답

### 실습 1. JWT 발급 · 검증, RS256, OAuth2 클라이언트, 토큰 블랙리스트를 한 파일에

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. 액세스 토큰 발급 | `create_access_token` — `data.copy()`, `expires_delta or timedelta(hours=1)`, `to_encode.update({...})`, `jwt.encode` |
| 2. 리프레시 토큰 발급 | `create_refresh_token` — `timedelta(days=30)`, `'jti': secrets.token_hex(16)` |
| 3. 디코딩 옵션과 타입 검사 | `verify_token` 의 `jwt.decode(..., algorithms=[ALGORITHM], options={...}, issuer='myapp.com')`, `payload.get('type') != token_type` |
| 4. 예외를 `ValueError` 로 | `except jwt.ExpiredSignatureError` → `except JWTError as e` |
| 5. 발급 · 출력 · 검증 | `user_data`, `access_token[:50]`, `verify_token(access_token)` 뒤 `print` |
| 6. RSA 키쌍 · PEM | `rsa.generate_private_key`, `private_bytes(PKCS8)`, `public_bytes(SubjectPublicKeyInfo)` |
| 7. RS256 서명 · 검증 | `rs_token = jwt.encode(..., algorithm='RS256')`, `rs_payload = jwt.decode(..., algorithms=['RS256'])` |
| 8. 자격 증명 보관 | `OAuth2Client.__init__` |
| 9. 인가 URL 과 `state` | `get_authorization_url` — `secrets.token_urlsafe(32)`, `params`, `urlencode(params)` |
| 10. 코드 교환 · 갱신 | `exchange_code`, `refresh_access_token` — `requests.post`, `raise_for_status()`, `response.json()` |
| 11. 사용자 정보 | `get_user_info` — `headers={'Authorization': f'Bearer {access_token}'}` |
| 12. 콜백 의사 코드 | `google_callback` 주석 — `state != session.pop('oauth_state', None)` 이면 `abort(403)` |
| 13. 블랙리스트 | `TokenBlacklist` — `_blacklist = set()`, `revoke`, `is_revoked` |
| 14. 핵심 정리 출력 | 파일 끝 `print` 일곱 줄 |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`python/python-web/reference/oauth-jwt.py`

```python
# [웹 프레임워크] OAuth2 & JWT (인증/인가)
# 설명: OAuth2 흐름, JWT 생성/검증, python-jose, 토큰 관리
# 팁: HS256은 간단하지만 서버만 서명/검증 가능. RS256은 다른 서비스가 public key로 검증 가능하여 마이크로서비스에 적합. OAuth2의 state 파라미터로 CSRF를 방지한다. 리프레시 토큰은 DB에 저장하고 로그아웃 시 폐기한다. 토큰에 민감한 정보(비밀번호 등)를 넣지 않는다.

# OAuth2 & JWT - 인증/인가 구현
# pip install python-jose[cryptography] requests authlib

import json
import time
from datetime import datetime, timedelta
# python-jose: JWT 인코딩/디코딩 (jwt 모듈)
from jose import jwt, JWTError
import hashlib
# secrets: 암호학적으로 안전한 난수 생성
import secrets


# === 1. JWT 기본 - 생성과 검증 ===
# 대칭 비밀 키 (256비트 권장)
SECRET_KEY = 'your-256-bit-secret-key-here-make-it-long'
# HS256: HMAC-SHA256 알고리즘
ALGORITHM = 'HS256'   # HMAC-SHA256 (대칭 키)


# 액세스 토큰 발급 함수
def create_access_token(data: dict, expires_delta: timedelta = None):
    """액세스 토큰 생성"""
    # 원본 dict를 보호하기 위해 복사
    to_encode = data.copy()
    # exp 클레임: 만료 시각 (UTC)
    expire = datetime.utcnow() + (expires_delta or timedelta(hours=1))
    # 표준 클레임 추가
    to_encode.update({
        'exp': expire,                    # 만료 시간
        'iat': datetime.utcnow(),         # 발급 시간
        'iss': 'myapp.com',              # 발급자
        'type': 'access'
    })
    # encode: payload + 서명
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# 리프레시 토큰 발급 (장기 유효)
def create_refresh_token(data: dict):
    """리프레시 토큰 생성 (긴 유효기간)"""
    to_encode = data.copy()
    to_encode.update({
        'exp': datetime.utcnow() + timedelta(days=30),
        'iat': datetime.utcnow(),
        'type': 'refresh',
        # jti: 토큰 고유 ID (블랙리스트 관리용)
        'jti': secrets.token_hex(16),     # 고유 토큰 ID (블랙리스트용)
    })
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# 토큰 검증 함수
def verify_token(token: str, token_type: str = 'access'):
    """토큰 검증"""
    try:
        # decode: 서명 검증 + payload 반환
        payload = jwt.decode(
            token, SECRET_KEY,
            algorithms=[ALGORITHM],
            # 검증 옵션 명시
            options={
                'verify_exp': True,       # 만료 검증
                'verify_iss': True,       # 발급자 검증
                'require_exp': True,
            },
            issuer='myapp.com'
        )
        # 토큰 종류 추가 검증 (액세스/리프레시 구분)
        if payload.get('type') != token_type:
            raise JWTError(f'잘못된 토큰 타입: {payload.get("type")}')
        return payload
    except jwt.ExpiredSignatureError:
        # 만료 시 명확한 에러
        raise ValueError('토큰이 만료되었습니다.')
    except JWTError as e:
        # 서명 불일치 등
        raise ValueError(f'유효하지 않은 토큰: {e}')


# 사용 예시
# sub: subject (사용자 식별자)
user_data = {'sub': 'user123', 'name': 'Alice', 'role': 'admin'}
access_token = create_access_token(user_data)
refresh_token = create_refresh_token(user_data)

print("=== JWT 토큰 ===")
print(f"Access Token: {access_token[:50]}...")
print(f"Refresh Token: {refresh_token[:50]}...")

# 검증
payload = verify_token(access_token)
print(f"검증 결과: user={payload['sub']}, role={payload['role']}")


# === 2. RSA 비대칭 키 JWT ===
# 비대칭 키: 서버는 private로 서명, 클라이언트/타 서비스는 public으로 검증
from jose import jwk
# cryptography: 키 생성 라이브러리
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

# RSA 키 생성
# 2048비트 RSA 키쌍 생성
private_key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048
)
public_key = private_key.public_key()

# PEM 형식으로 변환
# PEM: 텍스트 형태의 키 표준 포맷
private_pem = private_key.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption()
)
public_pem = public_key.public_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.SubjectPublicKeyInfo
)

# RS256으로 서명 (서버만 private key 보유)
# RS256: RSA-SHA256, 서명/검증 키가 분리되어 마이크로서비스에 적합
rs_token = jwt.encode(
    {'sub': 'user123', 'exp': datetime.utcnow() + timedelta(hours=1)},
    private_pem.decode(),
    algorithm='RS256'
)

# 검증 (public key로 누구나 검증 가능)
rs_payload = jwt.decode(rs_token, public_pem.decode(), algorithms=['RS256'])
print(f"\nRS256 검증: {rs_payload['sub']}")


# === 3. OAuth2 Authorization Code Flow ===
import requests
# urlencode: dict -> query string 변환
from urllib.parse import urlencode

# OAuth2 클라이언트 캡슐화 (Google 예시)
class OAuth2Client:
    """OAuth2 클라이언트 (Google 예시)"""

    # 클라이언트 자격증명 + 리다이렉트 URI 보관
    def __init__(self, client_id, client_secret, redirect_uri):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri

    # 1단계: 사용자를 인가 서버로 보낼 URL 생성
    def get_authorization_url(self, scope='openid email profile', state=None):
        """1단계: 인가 URL 생성"""
        if state is None:
            # state: CSRF 방지용 무작위 값 (세션에 저장 후 콜백에서 비교)
            state = secrets.token_urlsafe(32)  # CSRF 방지

        # 표준 OAuth2 파라미터들
        params = {
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'response_type': 'code',
            'scope': scope,
            'state': state,
            'access_type': 'offline',    # refresh_token 받기
            'prompt': 'consent',
        }
        return (
            f'https://accounts.google.com/o/oauth2/v2/auth?'
            f'{urlencode(params)}',
            state
        )

    # 2단계: 받은 인가 코드를 토큰으로 교환
    def exchange_code(self, code):
        """2단계: 인가 코드 -> 토큰 교환"""
        # token endpoint에 POST 요청
        response = requests.post(
            'https://oauth2.googleapis.com/token',
            data={
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'code': code,
                'grant_type': 'authorization_code',
                'redirect_uri': self.redirect_uri,
            }
        )
        response.raise_for_status()
        return response.json()  # access_token, refresh_token, id_token

    # 토큰 갱신 (refresh_token grant)
    def refresh_access_token(self, refresh_token):
        """토큰 갱신"""
        response = requests.post(
            'https://oauth2.googleapis.com/token',
            data={
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'refresh_token': refresh_token,
                'grant_type': 'refresh_token',
            }
        )
        response.raise_for_status()
        return response.json()

    # 3단계: 액세스 토큰으로 보호된 리소스 호출
    def get_user_info(self, access_token):
        """3단계: 사용자 정보 조회"""
        response = requests.get(
            'https://www.googleapis.com/oauth2/v2/userinfo',
            # Bearer 스키마로 토큰 전송
            headers={'Authorization': f'Bearer {access_token}'}
        )
        response.raise_for_status()
        return response.json()  # id, email, name, picture


# Flask에서 OAuth2 콜백 처리 (의사 코드)
# @app.route('/auth/google/callback')
# def google_callback():
#     code = request.args.get('code')
#     state = request.args.get('state')
#     if state != session.pop('oauth_state', None):
#         abort(403)  # CSRF 방지
#     tokens = oauth_client.exchange_code(code)
#     user_info = oauth_client.get_user_info(tokens['access_token'])
#     # 사용자 생성 또는 로그인 처리
#     session['user'] = user_info
#     return redirect('/')


# === 4. 토큰 블랙리스트 (로그아웃) ===
# JWT는 stateless라 로그아웃 시 별도 블랙리스트 필요
class TokenBlacklist:
    """Redis 기반 토큰 블랙리스트"""

    def __init__(self):
        # 실제로는 Redis 같은 외부 저장소 사용
        self._blacklist = set()  # 실제로는 Redis 사용

    # 토큰 폐기 (jti 기준)
    def revoke(self, jti: str, exp: int):
        """토큰 폐기"""
        self._blacklist.add(jti)
        # Redis 사용 시 TTL을 토큰 만료까지로 설정해 자동 정리
        # Redis: redis.setex(f'blacklist:{jti}', exp - time.time(), '1')

    # 폐기 여부 확인 (모든 인증 요청마다 체크)
    def is_revoked(self, jti: str) -> bool:
        return jti in self._blacklist


print("\nOAuth2 & JWT 핵심 정리")
print("="*50)
print("JWT: Header.Payload.Signature 구조")
print("HS256: 대칭키 (같은 키로 서명/검증)")
print("RS256: 비대칭키 (private 서명, public 검증)")
print("OAuth2 Code Flow: 인가코드 -> 토큰 교환 -> API 호출")
print("Refresh Token: 액세스 토큰 갱신용 (긴 유효기간)")
print("state 파라미터: CSRF 공격 방지")
print("jti (JWT ID): 토큰 블랙리스트/로그아웃용")
```

**실행 결과** — 실행하지 않음 — 실행 환경 · 바깥 네트워크에 따라 달라지는 예제다.

**풀이 요점**
- 발급 함수는 원본 dict 를 복사해서 클레임을 더한다 — 호출한 쪽의 `user_data` 를 건드리지 않는다.
- `verify_token` 은 `except` 차례가 핵심이다 — 하위 클래스 `ExpiredSignatureError` 가 위에 있어야 만료 메시지가 따로 나간다.
- 예제의 리프레시 토큰에는 `iss` 가 없어 `verify_token` 의 발급자 검사와 어긋난다 — 고치려면 리프레시 토큰에도 `'iss': 'myapp.com'` 을 넣는다.
- RS256 은 private PEM 으로 서명하고 public PEM 으로 검증한다 — 검증하는 쪽에 비밀을 넘기지 않는다.
- OAuth2 클라이언트에서 `state` 는 만들어 돌려주기만 하고, 비교는 콜백(세션)에서 한다.
- `set` 블랙리스트는 흉내다 — `revoke` 의 `exp` 는 Redis TTL 계산 자리로만 남아 있다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — 실행 환경 · 바깥 네트워크에 따라 달라지는 예제다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
