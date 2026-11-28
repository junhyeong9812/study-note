# python/python-web-deep/11 — Flask 인증: Login, 세션, JWT — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 고친 토큰과 다른 키 (예측)

```python
# 질문용 발췌 — token 은 jwt.encode({'user_id': 42, 'role': 'admin'}) 로 만든 정상 토큰
print(jwt.decode(token + "tampered"))
print(JWTAuth(secret='other-key').decode(token))
```

- 두 줄은 각각 무엇을 찍는가?

### 2. 데코레이터 차례를 뒤집으면 (예측)

```python
# 질문용 발췌 — 쌓는 차례만 원본과 반대
@require_role('admin')
@require_auth
def admin_dashboard2(request):
    return {'message': '관리자 대시보드', 'user': request['user']}

req2 = {'headers': {'Authorization': f'Bearer {token}'}}   # 정상 admin 토큰, 새 딕셔너리
print(admin_dashboard2(req2))
```

- 무엇이 찍히는가?

### 3. 같은 비밀번호를 두 번 해싱하면 (예측)

```python
# 질문용 발췌
a = hash_password('mypassword')
b = hash_password('mypassword')
print(a == b)
print(verify_password('mypassword', a), verify_password('mypassword', b))
```

- 두 줄은 각각 무엇을 찍는가?

### 4. `decode` 가 서명 비교에 `compare_digest` 를 쓰는 까닭 (왜)
- `expected == actual` 로 비교하면 어떤 정보가 새어 나갈 수 있는가?

### 5. 세션은 서버 상태가 필요하고 JWT 는 무상태라 불리는 까닭 (왜)
- 요청이 올 때 서버가 하는 일이 두 방식에서 어떻게 다른가?

### 6. JWT payload 에 담아도 되는 것의 한계 (경계)
- 비밀 키가 없는 사람은 payload 를 읽을 수 있는가, 고칠 수 있는가?

### 7. 401 과 403 의 갈림 (경계)
- 데코레이터 예제에서 어떤 경우는 401, 어떤 경우는 403 을 돌려주는가?

### 8. 원본 코드는 자신의 팁을 어디서 어기나 (경계)
- 「평문 비교 대신 `compare_digest`」라는 팁을 지키지 않는 함수는 어느 것인가?

### 9. access 와 refresh 를 나누는 까닭 (연결)
- Flask-JWT-Extended 의 `/refresh` 라우트는 두 토큰의 TTL 차이와 어떻게 이어지는가?

### 10. 데코레이터에 `@wraps(f)` 를 붙이는 까닭 (연결)
- `@wraps` 를 빼면 `get_profile.__name__` 은 무엇이 되는가?

## 실습

### 실습 1. 세션 패턴 · JWT · 인증 데코레이터 · 비밀번호 해싱을 한 파일로

**만들 것** — 표준 라이브러리만으로 JWT 발급 · 검증, 인증 · 역할 데코레이터, 비밀번호 해싱을 구현하고, Flask-Login 과 Flask-JWT-Extended 의 쓰임새는 코드 문자열로 출력하는 학습 파일.

**준비물** — 파이썬 표준 라이브러리만 있으면 된다. Flask · Flask-Login · Flask-JWT-Extended 부분은 실행하지 않고 문자열로 출력만 하며, HTTP 요청은 `{'headers': {...}}` 딕셔너리로 흉내 낸다.

**요구 조건**

1. 1단계 — `=== 1. Flask-Login 패턴 ===` 제목을 찍고, 세션 인증 패턴 코드를 여러 줄 문자열로 출력한다: `LoginManager` 를 앱에 붙이고 `login_view` 를 정하기, `UserMixin` 을 상속한 `User` 모델, `@login_manager.user_loader` 로 id 에서 사용자 찾기, `/login` 에서 비밀번호 확인 뒤 `login_user(user, remember=True)` 하고 실패 시 401, `@login_required` 가 붙은 `/dashboard` 에서 `current_user` 쓰기.
2. 2단계 — `JWTAuth` 클래스: 생성자는 비밀 키와 알고리즘(기본 `'HS256'`)을 저장한다.
3. `_base64url_encode` 는 url-safe base64 로 인코딩하고 끝의 `=` 를 떼며, `_base64url_decode` 는 패딩을 복원해 디코딩한다.
4. `encode(payload, expires_in=3600)` 는 헤더(`alg` · `typ`)와, `exp` · `iat` 를 덧붙인 payload 를 각각 base64url 로 만들고, `header.payload` 에 HMAC-SHA256 서명을 붙여 점 세 부분 토큰을 돌려준다.
5. `decode(token)` 는 세 조각인지 확인 → 서명을 다시 계산해 `hmac.compare_digest` 로 비교 → payload 를 JSON 으로 풀기 → `exp` 가 지났으면 `None` → 통과하면 payload 를 돌려주고, 어떤 예외든 `None` 을 돌려준다.
6. 비밀 키 `'my-secret-key-123'` 로 인스턴스를 만들고, `{'user_id': 42, 'role': 'admin'}` 로 1시간짜리 토큰을 만들어 앞 50글자와 길이를 찍고, 디코딩 결과와 끝에 `"tampered"` 를 붙인 위조 토큰의 디코딩 결과를 찍는다.
7. 3단계 — `require_auth`: `Authorization` 헤더가 `Bearer ` 로 시작하지 않으면 `({'error': '토큰 필요'}, 401)`, 토큰이 무효면 `({'error': '유효하지 않은 토큰'}, 401)`, 통과하면 `request['user']` 에 payload 를 넣고 본 함수를 부른다.
8. `require_role(*roles)`: `request['user']` 의 역할이 허용 목록에 없으면 `({'error': '권한 없음'}, 403)` 을 돌려주는 데코레이터 팩토리. 두 데코레이터 모두 `@wraps` 를 쓴다.
9. 인증만 필요한 `get_profile`(`user_id` · `role` 반환)과, 인증 + `'admin'` 역할이 필요한 `admin_dashboard`(메시지와 사용자 반환)를 만들고, 정상 토큰 요청으로 둘을 부르고, 헤더가 빈 요청으로 `get_profile` 을 불러 각각 찍는다.
10. 4단계 — `hash_password(password, salt=None)` 는 솔트가 없으면 무작위 16바이트 16진 솔트를 만들고 pbkdf2-sha256 100,000회로 해싱해 `솔트$해시` 를 돌려주며, `verify_password` 는 저장값에서 솔트를 꺼내 다시 해싱해 비교한다. 해시 앞 40글자와 맞는 · 틀린 비밀번호의 검증 결과를 찍는다.
11. 5단계 — `=== 5. Flask-JWT-Extended ===` 제목과 함께 `JWTManager` 설정(`JWT_SECRET_KEY`, 1시간 access 만료), `/login` 의 access · refresh 발급, `@jwt_required()` 의 `/protected`, `@jwt_required(refresh=True)` 의 `/refresh` 를 담은 패턴 코드 문자열을 출력하고, 핵심 정리 다섯 줄을 찍는다.

**시작 코드**

```python
"""Flask 인증: Flask-Login, JWT, 데코레이터 보호"""
import hashlib
import hmac
import json
import time
import base64
from functools import wraps
from typing import Optional

# === 1. Flask-Login 세션 인증 패턴 ===
print("=== 1. Flask-Login 패턴 ===")
print("""
# TODO: LoginManager · UserMixin · user_loader · login_user · login_required 를 쓰는 패턴 코드
""")

# === 2. JWT 인증 구현 ===
print("=== 2. JWT 인증 구현 ===")

class JWTAuth:
    """간단한 JWT 인증 구현 (학습용)"""

    def __init__(self, secret: str, algorithm: str = 'HS256'):
        pass  # TODO: 키와 알고리즘 저장

    def _base64url_encode(self, data: bytes) -> str:
        pass  # TODO: url-safe 인코딩 후 '=' 제거

    def _base64url_decode(self, data: str) -> bytes:
        pass  # TODO: 패딩 복원 후 디코딩

    def encode(self, payload: dict, expires_in: int = 3600) -> str:
        """JWT 토큰 생성"""
        # TODO: header / payload(+exp, iat) / HMAC-SHA256 서명 → "a.b.c"
        pass

    def decode(self, token: str) -> Optional[dict]:
        """JWT 토큰 검증 및 디코딩"""
        # TODO: 3조각 확인 → 서명 compare_digest → payload → exp 확인, 예외는 None
        pass

jwt = JWTAuth(secret='my-secret-key-123')
# TODO: 토큰 생성 · 앞 50글자와 길이 출력 · 디코딩 출력 · 위조 토큰 디코딩 출력

# === 3. 인증 데코레이터 ===
print("\n=== 3. 인증 데코레이터 ===")

def require_auth(f):
    """JWT 인증 필수 데코레이터"""
    # TODO: Bearer 확인(401) · 토큰 검증(401) · request['user'] 첨부
    pass

def require_role(*roles):
    """역할 기반 접근 제어 데코레이터"""
    # TODO: 역할이 roles 에 없으면 403
    pass

# TODO: get_profile, admin_dashboard 정의 (쌓는 차례에 주의)

print("\n인증된 요청:")
# TODO: 정상 토큰으로 get_profile, admin_dashboard 호출 후 출력
print("\n인증 안 된 요청:")
# TODO: 헤더 없는 요청으로 get_profile 호출 후 출력

# === 4. 비밀번호 해싱 ===
print("\n=== 4. 비밀번호 해싱 ===")

def hash_password(password: str, salt: str = None) -> str:
    pass  # TODO: 무작위 솔트 + pbkdf2_hmac('sha256', ..., 100000) → "salt$hash"

def verify_password(password: str, stored: str) -> bool:
    pass  # TODO: 솔트 꺼내 다시 해싱 후 비교

# TODO: 해시 앞 40글자, 맞는/틀린 비밀번호 검증 결과 출력

# === 5. Flask-JWT-Extended 패턴 ===
print("\n=== 5. Flask-JWT-Extended ===")
print("""
# TODO: JWTManager 설정 · /login(access+refresh) · /protected · /refresh 패턴 코드
""")

print("=== 핵심 정리 ===")
# TODO: 핵심 정리 다섯 줄
```

**확인 방법** — `python flask-auth.py` 로 돌려, 디코딩이 `user_id` 42 · `role` admin 을 담은 딕셔너리인지, 위조 토큰이 `None` 인지, 인증된 요청의 프로필 · 관리자 결과가 딕셔너리이고 인증 안 된 요청이 `({'error': '토큰 필요'}, 401)` 인지, 비밀번호 검증이 `True` / `False` 인지 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
