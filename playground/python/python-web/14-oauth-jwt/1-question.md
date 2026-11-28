# python/python-web/14 — OAuth2 & JWT (인증/인가) — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 액세스 토큰을 발급해 검증한 뒤 원본 dict 를 찍으면 (예측)

```python
# 질문용 발췌
user_data = {'sub': 'user123', 'name': 'Alice', 'role': 'admin'}
access_token = create_access_token(user_data)
payload = verify_token(access_token)
print(f"검증 결과: user={payload['sub']}, role={payload['role']}")
print(user_data)
```

- 두 `print` 는 각각 무엇을 찍는가?

### 2. 리프레시 토큰을 `verify_token` 에 넣으면 (예측)

```python
# 질문용 발췌
refresh_token = create_refresh_token(user_data)
verify_token(refresh_token)              # (가)
verify_token(refresh_token, 'refresh')   # (나)
```

- (가) 와 (나) 는 payload 를 돌려주는가, 예외를 던지는가?
- 예외라면 어느 검사에서 걸리는가?

### 3. `except` 두 줄의 차례를 바꾸고 만료된 토큰을 넣으면 (예측)

```python
# 질문용 발췌
expired = create_access_token(user_data, expires_delta=timedelta(seconds=-1))
try:
    jwt.decode(expired, SECRET_KEY, algorithms=['HS256'], issuer='myapp.com')
except JWTError as e:
    raise ValueError(f'유효하지 않은 토큰: {e}')
except jwt.ExpiredSignatureError:
    raise ValueError('토큰이 만료되었습니다.')
```

- 어느 메시지의 `ValueError` 가 나는가?

### 4. 마이크로서비스에서 RS256 이 HS256 보다 맞는 까닭 (왜)

- 여러 서비스가 토큰을 검증해야 할 때 HS256 의 키 하나가 왜 문제가 되는가?

### 5. `state` 를 세션에 넣고 콜백에서 비교하는 까닭 (왜)

- 콜백에서 `state` 비교를 빼면 어떤 공격이 열리는가?

### 6. `TokenBlacklist` 로 끊을 수 있는 토큰의 범위 (경계)

- 이 예제의 발급 함수 그대로라면, 블랙리스트로 액세스 토큰을 폐기할 수 있는가?

### 7. 서명이 막아 주는 것과 못 막는 것 (경계)

- 서명된 JWT 의 payload 에 비밀번호를 넣으면 무엇이 위험한가?

### 8. 세션 저장소를 없앤 JWT 가 로그아웃에서 다시 저장소를 부르는 까닭 (연결)

- stateless 라는 장점이 로그아웃에서는 왜 약점이 되는가?

### 9. 인가 코드를 토큰으로 바꾸는 일을 서버가 맡는 까닭 (연결)

- 브라우저 주소로 온 `code` 를 곧바로 쓰지 않고 `exchange_code` 를 거치는 것은 `client_secret` 과 어떻게 이어지는가?

## 실습

### 실습 1. JWT 발급 · 검증, RS256, OAuth2 클라이언트, 토큰 블랙리스트를 한 파일에

**만들 것** — HS256 액세스 · 리프레시 토큰을 만들고 검증하는 함수, RS256 서명 · 검증, 구글 OAuth2 Code Flow 클라이언트 클래스, `jti` 블랙리스트 클래스를 한 파이썬 파일에 모은다.

**준비물** — `pip install python-jose[cryptography] requests authlib`. OAuth2 부분은 클래스 정의만 하고 호출하지 않으므로 구글 자격 증명 없이도 파일이 끝까지 돈다. Redis 는 `set` 으로 흉내 낸다.

**요구 조건**

1단계 — HS256 JWT
1. `create_access_token(data, expires_delta=None)` 은 `data` 를 복사한 뒤 `exp`(지금 + `expires_delta`, 없으면 1시간) · `iat` · `iss='myapp.com'` · `type='access'` 를 더해 `SECRET_KEY` · `ALGORITHM` 으로 인코딩한다.
2. `create_refresh_token(data)` 은 복사본에 `exp`(30일 뒤) · `iat` · `type='refresh'` · `jti`(`secrets.token_hex(16)`) 를 더해 인코딩한다.
3. `verify_token(token, token_type='access')` 는 `algorithms` 목록 · 만료 검증 · 발급자 검증 · `exp` 필수 옵션 · `issuer='myapp.com'` 으로 디코딩하고, `type` 이 `token_type` 과 다르면 `JWTError` 를 던진다.
4. 만료는 「토큰이 만료되었습니다.」, 그 밖의 `JWTError` 는 「유효하지 않은 토큰: …」 메시지의 `ValueError` 로 바꾼다.
5. `user_data` 로 두 토큰을 만들어 앞 50글자씩 찍고, 액세스 토큰을 검증해 `sub` 와 `role` 을 찍는다.

2단계 — RS256
6. 2048비트 RSA 키쌍을 만들고 private key 는 PKCS8, public key 는 SubjectPublicKeyInfo 형식의 PEM 으로 바꾼다.
7. private PEM 으로 `sub` · `exp`(1시간 뒤) 를 담은 RS256 토큰을 만들고, public PEM 으로 검증해 `sub` 를 찍는다.

3단계 — OAuth2 클라이언트
8. `OAuth2Client(client_id, client_secret, redirect_uri)` 가 세 값을 보관한다.
9. `get_authorization_url(scope, state=None)` 은 `state` 가 없으면 `secrets.token_urlsafe(32)` 로 만들고, `client_id` · `redirect_uri` · `response_type='code'` · `scope` · `state` · `access_type='offline'` · `prompt='consent'` 를 `urlencode` 로 붙인 인가 URL 과 `state` 를 튜플로 돌려준다.
10. `exchange_code(code)` 는 `grant_type='authorization_code'` 로, `refresh_access_token(refresh_token)` 은 `grant_type='refresh_token'` 으로 토큰 엔드포인트에 POST 하고, 실패면 예외 · 성공이면 JSON 을 돌려준다.
11. `get_user_info(access_token)` 은 `Bearer` 헤더로 사용자 정보 엔드포인트에 GET 하고 JSON 을 돌려준다.
12. 콜백에서 `state` 를 세션 값과 비교하는 처리를 주석(의사 코드)으로 적는다.

4단계 — 블랙리스트와 정리
13. `TokenBlacklist` 는 `set` 을 두고 `revoke(jti, exp)` 로 추가, `is_revoked(jti)` 로 확인한다.
14. 끝에 핵심 정리 일곱 줄을 찍는다(시작 코드에 채워 둠).

**시작 코드**

```python
# pip install python-jose[cryptography] requests authlib
import json
import time
from datetime import datetime, timedelta
from jose import jwt, JWTError
import hashlib
import secrets

# === 1. JWT 기본 ===
SECRET_KEY = 'your-256-bit-secret-key-here-make-it-long'
ALGORITHM = 'HS256'


def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    # TODO: expire 계산 (기본 1시간)
    # TODO: exp, iat, iss, type 클레임 추가
    # TODO: 인코딩해서 반환


def create_refresh_token(data: dict):
    to_encode = data.copy()
    # TODO: exp(30일), iat, type, jti 추가 후 인코딩


def verify_token(token: str, token_type: str = 'access'):
    try:
        # TODO: jwt.decode (algorithms, options, issuer)
        # TODO: type 검사
        pass
    # TODO: 만료 → ValueError('토큰이 만료되었습니다.')
    # TODO: JWTError → ValueError(f'유효하지 않은 토큰: {e}')
    except Exception:
        raise


user_data = {'sub': 'user123', 'name': 'Alice', 'role': 'admin'}
# TODO: 두 토큰 발급, 앞 50글자 출력, 액세스 토큰 검증 결과 출력

# === 2. RSA 비대칭 키 JWT ===
from jose import jwk
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

# TODO: 키쌍 생성 (public_exponent=65537, key_size=2048)
# TODO: PEM 변환
# TODO: RS256 서명 → public 으로 검증 → sub 출력

# === 3. OAuth2 Authorization Code Flow ===
import requests
from urllib.parse import urlencode


class OAuth2Client:
    def __init__(self, client_id, client_secret, redirect_uri):
        pass  # TODO

    def get_authorization_url(self, scope='openid email profile', state=None):
        pass  # TODO: state 생성, params, (구글 인가 엔드포인트 + 쿼리, state) 반환

    def exchange_code(self, code):
        pass  # TODO: 구글 토큰 엔드포인트로 POST

    def refresh_access_token(self, refresh_token):
        pass  # TODO

    def get_user_info(self, access_token):
        pass  # TODO: 구글 사용자 정보 엔드포인트로 GET, Bearer 헤더


# TODO: Flask 콜백 의사 코드(주석)

# === 4. 토큰 블랙리스트 ===
class TokenBlacklist:
    def __init__(self):
        pass  # TODO

    def revoke(self, jti: str, exp: int):
        pass  # TODO

    def is_revoked(self, jti: str) -> bool:
        pass  # TODO


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

**확인 방법** — `python oauth-jwt.py` 로 돌려 두 토큰 앞부분 · `검증 결과: user=user123, role=admin` · `RS256 검증: user123` · 핵심 정리 일곱 줄이 예외 없이 찍히는지 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
