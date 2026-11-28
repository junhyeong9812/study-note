# python/python-web/14 — OAuth2 & JWT (인증/인가) — 정리 (힌트)

> 출처 — study-site 항목 `python/oauth-jwt`(항목 데이터 `data/python/web-frameworks.json`) · 정답 코드 study-practice `python/python-web/reference/oauth-jwt.py`\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).\
> 실행 — 실행하지 않음 — 실행 환경 · 바깥 네트워크에 따라 달라지는 예제다.

## 한눈에 — 쉽게 말하면

**JWT 는 「도장 찍힌 놀이공원 손목밴드」다.**
매표소(서버)는 손목밴드에 이름 · 등급 · 마감 시각을 적고 위조할 수 없는 도장을 찍어 준다.
놀이기구 앞 직원은 매표소에 전화하지 않는다.
도장이 진짜인지와 마감 시각이 지났는지만 보고 들여보낸다.
**OAuth2** 는 「신분 확인을 큰 매표소(구글)에 맡기고, 확인 결과를 받아 오는 절차」다.
인증 · 인가 코드도 똑같은 구조다.

| 비유 | 실체 |
|---|---|
| 손목밴드 | JWT 문자열 |
| 밴드에 적힌 이름 · 등급 · 마감 시각 | payload 의 클레임(`sub` · `role` · `exp`) |
| 매표소 도장 | 서명(Signature) |
| 도장을 찍는 인주와 확인용 견본 | 서명 키와 검증 키(HS256 은 같은 키, RS256 은 다른 키) |
| 하루권 · 시즌권 교환권 | 액세스 토큰(1시간) · 리프레시 토큰(30일) |
| 분실 신고된 밴드 번호 목록 | `jti` 블랙리스트 |
| 큰 매표소에서 받아 오는 교환 쪽지 | OAuth2 인가 코드(`code`) |

```text
  [로그인] ──> 서버: 클레임 + 서명 ──> JWT 발급
                                         │
  [요청마다] Authorization: Bearer <JWT> ─┘
                                         ▼
               서버: 서명 맞나? 만료 안 됐나? 발급자 맞나? ──> 통과 / 거절
```

> **인증(authentication)** — 「너는 누구인가」를 확인하는 일이다.\
> 예: 로그인해서 `sub='user123'` 임을 증명한다.

> **인가(authorization)** — 「너는 무엇을 해도 되나」를 정하는 일이다.\
> 예: `role='admin'` 이면 관리 페이지를 연다.

## 이 주제가 답하려는 질문

1. 서버가 세션 저장소를 뒤지지 않고 「이 요청은 누구의 것인가」를 어떻게 믿나?
2. 서명 키를 누가 갖나 — HS256 과 RS256 은 무엇이 다른가?
3. 구글 로그인 같은 남의 인증을 내 앱에 어떻게 붙이고, 그 사이의 CSRF 는 어떻게 막나?
4. 저장소 없이 믿는 토큰을 로그아웃 때 어떻게 끊나?

## 동작 방식

### (1) JWT 의 생김새 — Header.Payload.Signature

**언제 쓰나** — 서버가 「누가 · 언제까지」를 토큰 안에 담아 건네고, 다음 요청에서 그 토큰만 보고 판단할 때 쓴다.

```text
 header (알고리즘)   payload (클레임)                 signature
 {"alg":"HS256"}  .  {"sub":"user123","exp":...}  .  서명(header+payload, 키)
       │                     │                            │
   base64url             base64url                 키 없이는 못 만든다
```

- 세 조각을 점(`.`)으로 이어 붙인 문자열이 JWT 다.
- header 와 payload 는 인코딩만 된 것이라 누구나 풀어 읽을 수 있다.
- signature 는 키로 만든 값이라, payload 를 한 글자라도 바꾸면 검증에서 어긋난다.
- 그래서 서명은 **위조를 막을 뿐 읽기는 막지 않는다** — 토큰에 비밀번호 같은 민감한 정보를 넣지 않는 까닭이다.

> **클레임(claim)** — payload 에 담긴 이름-값 한 쌍이다.\
> 예: `'sub': 'user123'` 은 「주체가 user123 이다」라는 클레임이다.

### (2) 발급 — `create_access_token` 과 `create_refresh_token`

**언제 쓰나** — 로그인에 성공한 사용자에게 짧은 액세스 토큰과 긴 리프레시 토큰을 함께 줄 때 쓴다.

```text
 user_data ──copy()──> to_encode ──update(exp, iat, iss, type)──> jwt.encode(…, SECRET_KEY, 'HS256')
     │                                                                    │
  원본 그대로                                                         JWT 문자열
```

- `data.copy()` 로 복사본에 클레임을 더한다. 넘겨받은 원본 dict 는 바뀌지 않는다.
- 액세스 토큰은 `exp` 를 지금(`datetime.utcnow()`) + `expires_delta` 로 둔다. 인자를 주지 않으면 1시간이다.
- 액세스 토큰에는 `iat`(발급 시각) · `iss='myapp.com'`(발급자) · `type='access'` 가 붙는다.
- 리프레시 토큰은 `exp` 가 30일 뒤이고 `type='refresh'` 와 `jti=secrets.token_hex(16)` 이 붙는다.
- 예제의 리프레시 토큰에는 **`iss` 가 없고**, 액세스 토큰에는 **`jti` 가 없다** — 뒤의 (3) · (6) 에서 문제가 된다.

> **`jti`** — 토큰마다 붙이는 고유 ID 클레임이다.\
> 예: `secrets.token_hex(16)` 은 16바이트 난수를 32글자 16진 문자열로 만든다.

### (3) 검증 — `verify_token`

**언제 쓰나** — 보호된 요청이 들어올 때마다 토큰을 믿어도 되는지 판정한다.

```text
 token ──> jwt.decode(token, SECRET_KEY, algorithms=['HS256'], options=…, issuer='myapp.com')
              │ 서명 확인 → exp 확인 → iss 확인
              ├─ 만료         → jwt.ExpiredSignatureError ──> ValueError('토큰이 만료되었습니다.')
              ├─ 그 밖의 실패 → JWTError                   ──> ValueError('유효하지 않은 토큰: …')
              └─ 통과 → payload['type'] == token_type ?
                         ├─ 아니다 → raise JWTError(…) ──(같은 try 안)──> ValueError('유효하지 않은 토큰: 잘못된 토큰 타입: …')
                         └─ 맞다   → payload 반환
```

- `jwt.decode` 는 서명이 맞는지 보고, 맞으면 payload dict 를 돌려준다.
- `algorithms=[ALGORITHM]` 은 받아들일 알고리즘을 서버가 못 박는 목록이다.
- `options` 의 `verify_exp` · `verify_iss` · `require_exp` 는 만료 검증 · 발급자 검증 · `exp` 필수를 켠다.
- `issuer='myapp.com'` 을 넘기면 payload 의 `iss` 가 이 값과 같아야 통과한다. `iss` 가 아예 없어도 실패로 본다(python-jose 동작 — 확인 필요).
- 서명 · 만료 · 발급자 검사를 다 통과해야 그다음 `type` 검사에 닿는다.
- `type` 검사에서 직접 던진 `JWTError` 도 같은 `try` 안이라 아래 `except JWTError` 가 받아 `ValueError` 로 바꾼다.
- `ExpiredSignatureError` 는 `JWTError` 의 하위 클래스다. 그래서 만료를 먼저 잡는 `except` 가 위에 와야 「만료」 메시지가 따로 나간다.

### (4) HS256 과 RS256 — 키를 누가 갖나

**언제 쓰나** — 토큰을 검증할 곳이 발급 서버 하나뿐이면 HS256, 여러 서비스가 각자 검증하면 RS256 을 고른다.

```text
 HS256 (대칭)                         RS256 (비대칭)
 SECRET_KEY ──서명──> token           private_pem ──서명──> token        (발급 서버만 보유)
 SECRET_KEY ──검증──> payload          public_pem  ──검증──> payload      (누구에게 줘도 됨)
 검증하는 쪽도 서명할 수 있다          검증하는 쪽은 서명할 수 없다
```

- HS256 은 HMAC-SHA256 이고, 같은 키로 서명도 검증도 한다.
- 그래서 검증을 남에게 맡기려면 비밀 키를 넘겨야 하고, 키를 받은 쪽은 토큰을 찍어 낼 수도 있다.
- RS256 은 RSA-SHA256 이다. `rsa.generate_private_key(public_exponent=65537, key_size=2048)` 로 키쌍을 만든다.
- 키는 `private_bytes`(PKCS8) · `public_bytes`(SubjectPublicKeyInfo) 로 PEM 텍스트로 바꿔 `jwt.encode` · `jwt.decode` 에 넘긴다.
- 서명은 private key 로, 검증은 public key 로 한다 — 다른 서비스가 public key 만으로 검증할 수 있어 마이크로서비스에 맞다.

> **PEM** — 키를 `-----BEGIN …-----` 로 감싼 텍스트로 적는 표준 형식이다.\
> 예: `private_pem.decode()` 는 bytes 인 PEM 을 문자열로 바꾼다.

### (5) OAuth2 Authorization Code Flow — 구글 로그인 붙이기

**언제 쓰나** — 사용자의 비밀번호를 내 서버가 받지 않고, 구글이 확인한 신원을 받아 올 때 쓴다.

```text
 [1] get_authorization_url ──> (URL, state)   state 는 세션에 저장
      브라우저가 구글 인가 화면으로 이동 → 사용자 동의
 [콜백] 구글 → 브라우저 → 내 서버  ?code=…&state=…
      state == session.pop('oauth_state') ?  아니면 403
 [2] exchange_code(code)   서버 → 구글 토큰 엔드포인트 (client_secret 동봉)
      → access_token, refresh_token, id_token
 [3] get_user_info(access_token)  Authorization: Bearer … → id, email, name, picture
 [갱신] refresh_access_token(refresh_token)  grant_type='refresh_token'
```

- `OAuth2Client` 는 `client_id` · `client_secret` · `redirect_uri` 를 보관한다.
- 1단계는 `urlencode` 로 `client_id` · `redirect_uri` · `response_type='code'` · `scope` · `state` · `access_type='offline'` · `prompt='consent'` 를 쿼리 문자열로 만들어 인가 URL 을 돌려준다.
- `state` 는 주지 않으면 `secrets.token_urlsafe(32)` 로 만든 무작위 값이다. URL 과 함께 돌려주어 세션에 넣게 한다.
- 콜백에서는 돌아온 `state` 를 세션에 넣어 둔 값과 비교해, 다르면 403 으로 끊는다. 내가 시작하지 않은 로그인 응답을 받아들이지 않는 것이다 — 이것이 OAuth2 의 CSRF 방지다.
- 인가 코드는 브라우저 주소를 거쳐 오지만 그 자체로는 API 를 부를 수 없다.
- 2단계에서 **서버가** `client_secret` 을 붙여 토큰 엔드포인트에 POST 해야 토큰으로 바뀐다. 그래서 토큰과 비밀은 브라우저를 지나지 않는다.
- 응답이 실패면 `raise_for_status()` 가 예외를 던지고, 성공이면 `response.json()` 을 돌려준다.
- 3단계는 액세스 토큰을 `Bearer` 스키마의 `Authorization` 헤더에 실어 사용자 정보를 받는다.
- `access_type='offline'` 은 refresh_token 을 받기 위한 값이다(코드 주석 기준).

> **CSRF** — 공격자가 피해자의 브라우저로 피해자가 의도하지 않은 요청을 보내게 하는 공격이다.\
> 예: 공격자가 자기 계정의 `code` 가 든 콜백 주소를 피해자에게 열게 해, 피해자를 공격자 계정으로 로그인시킨다.

### (6) 로그아웃 — `jti` 블랙리스트

**언제 쓰나** — 아직 만료되지 않은 토큰을 지금 당장 못 쓰게 해야 할 때(로그아웃 · 탈취 의심) 쓴다.

```text
 로그아웃 ──> revoke(jti, exp) ──> _blacklist 에 jti 추가
 요청마다 ──> is_revoked(jti) ? ──> True 면 거절
 (Redis 라면 setex 로 exp - time.time() 초 뒤 자동 삭제)
```

- JWT 는 stateless 다 — 서버는 발급한 토큰 목록을 갖고 있지 않으니, 서명이 맞고 만료 전이면 통과시킨다.
- 그래서 로그아웃하려면 「폐기된 토큰」 목록을 따로 두고 모든 인증 요청마다 확인해야 한다.
- 예제는 `set` 으로 흉내 내고, 실제로는 Redis 같은 외부 저장소를 쓴다고 주석에 적었다.
- Redis 의 TTL 을 토큰 만료까지로 두면, 어차피 만료된 토큰의 `jti` 는 저절로 지워진다.
- 리프레시 토큰은 DB 에 저장하고 로그아웃 때 폐기한다(원본 팁).

> **stateless** — 서버가 요청 사이에 사용자 상태를 저장하지 않는 성질이다.\
> 예: 세션 저장소 대신 요청에 실린 JWT 만 보고 사용자를 판단한다.

## 문법 — 형태와 규칙

```python
from datetime import datetime, timedelta
from jose import jwt, JWTError

KEY = 'long-random-secret-from-env'
claims = {'sub': 'u1', 'exp': datetime.utcnow() + timedelta(minutes=5)}
token = jwt.encode(claims, KEY, algorithm='HS256')

try:
    data = jwt.decode(token, KEY, algorithms=['HS256'])
except jwt.ExpiredSignatureError:
    print('만료')
except JWTError as e:
    print('무효', e)
```

- `jwt.encode(클레임 dict, 키, algorithm='…')` — `algorithm` 은 단수 문자열이다.
- `jwt.decode(토큰, 키, algorithms=[…])` — `algorithms` 는 복수 · 리스트다. 서버가 허용할 알고리즘을 정한다.
- `options={…}` 로 검증 항목을 켜고 끄며, `issuer=` 로 기대하는 발급자를 준다.
- 표준 클레임: `sub`(주체) · `exp`(만료) · `iat`(발급 시각) · `iss`(발급자) · `jti`(토큰 ID). `type` 은 이 앱이 정한 클레임이다.
- `except` 는 하위 클래스(`ExpiredSignatureError`)를 위에, 상위 클래스(`JWTError`)를 아래에 둔다.
- 난수는 `random` 이 아니라 `secrets`(`token_hex` · `token_urlsafe`)로 만든다.
- 설치는 `pip install python-jose[cryptography] requests authlib` 다(원본 주석).

## 어디서 틀리나

### 1. HS256 키를 다른 서비스와 나눈다
HS256 은 같은 키로 서명도 한다.
검증만 맡기려고 키를 넘기면, 그 서비스도 아무 토큰이나 찍어 낼 수 있다.
여러 서비스가 검증해야 하면 RS256 으로 public key 만 나눈다.

### 2. `state` 를 만들기만 하고 비교하지 않는다
`state` 는 세션에 넣었다가 콜백에서 돌아온 값과 비교해야 효과가 있다.
예제 콜백은 `session.pop` 으로 꺼내 비교하므로 같은 `state` 를 두 번 쓸 수도 없다.

### 3. 리프레시 토큰을 저장 · 폐기하지 않는다
리프레시 토큰은 30일짜리라 새면 피해가 길다.
DB 에 저장하고 로그아웃 때 폐기한다.

### 4. 토큰에 민감한 정보를 넣는다
payload 는 인코딩일 뿐 암호화가 아니다.
비밀번호 같은 값은 넣지 않는다.
예제의 `name` · `role` 도 토큰을 가진 누구에게나 읽힌다.

### 5. `except` 차례를 뒤집는다
`ExpiredSignatureError` 가 `JWTError` 의 하위 클래스라, `except JWTError` 가 위에 오면 만료도 그쪽이 먼저 잡는다.
「만료되었습니다」 메시지는 영영 나가지 않는다.

### 6. 예제의 리프레시 토큰은 `verify_token` 을 통과하기 어렵다
`create_refresh_token` 은 `iss` 를 넣지 않는데, `verify_token` 은 `issuer='myapp.com'` 으로 발급자를 검사한다.
그래서 `verify_token(refresh_token, 'refresh')` 도 `type` 검사에 닿기 전에 발급자 검사에서 실패할 것으로 읽힌다(확인 필요).
리프레시 토큰에도 `iss` 를 넣어야 짝이 맞는다.

### 7. 액세스 토큰은 블랙리스트로 끊을 수 없다
`jti` 는 리프레시 토큰에만 붙는다.
액세스 토큰을 폐기하려면 액세스 토큰에도 `jti` 를 넣거나, 만료를 짧게 두고 리프레시 토큰을 끊는 쪽에 기댄다.

### 8. `revoke` 의 `exp` 인자는 `set` 버전에서 쓰이지 않는다
`exp` 는 Redis 의 TTL 을 계산할 때만 쓰인다(주석).
`set` 버전에서는 폐기한 `jti` 가 지워지지 않고 쌓이며, 프로세스가 끝나면 목록이 사라진다.

### 9. 비밀 키를 코드에 박는다
`SECRET_KEY = 'your-256-bit-…'` 는 예시용이다.
실제로는 길고 무작위인 키를 코드 밖(환경 변수 등)에 둔다.

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| `exp` · `iat` · `iss` · `sub` · `jti` 의 이름과 뜻 | JWT 표준 |
| `type` 클레임으로 액세스 · 리프레시를 가른다 | 이 예제가 정한 약속 — 표준 아님 |
| `jwt.encode` 가 `datetime` 인 `exp` · `iat` 를 숫자 타임스탬프로 바꿔 넣는다 | python-jose 구현 (확인 필요) |
| `ExpiredSignatureError` 가 `JWTError` 의 하위 클래스다 | python-jose 구현 |
| `issuer=` 를 주면 `iss` 가 없는 토큰도 실패한다 | python-jose 구현 (확인 필요) |
| `access_type='offline'` · `prompt='consent'` | 구글 인가 서버의 파라미터 — OAuth2 공통 아님 |
| `state` 를 콜백에서 비교한다 | OAuth2 가 권하는 장치, 비교는 클라이언트 코드의 책임 |
| `secrets` 는 암호학적으로 안전한 난수를 만든다 | Python 표준 라이브러리 문서의 약속 |
| 블랙리스트가 프로세스 메모리(`set`)에 있다 | 이 예제의 흉내 — 실서비스는 Redis 등 |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 서버 하나가 발급 · 검증 | HS256 + 긴 비밀 키 | 비밀 키를 다른 서비스에 복사 |
| 여러 서비스가 각자 검증 | RS256, public key 배포 | HS256 키 공유 |
| 구글 등 외부 계정 로그인 | Authorization Code Flow + `state` | 사용자 비밀번호를 직접 받기 |
| 로그아웃 · 강제 만료 | `jti` 블랙리스트, 리프레시 토큰 DB 폐기 | 만료만 기다리기 |
| 사용자 식별 | `sub` 같은 식별자 | 비밀번호 · 민감 정보를 payload 에 |
| 오래 로그인 유지 | 짧은 액세스 + 긴 리프레시 | 긴 액세스 토큰 하나 |

## 핵심 문장

1. **JWT 는 서명된 클레임 묶음이다** — 서버는 저장소 없이 서명 · 만료 · 발급자만 보고 믿는다.
2. **서명은 위조를 막지만 읽기는 막지 않는다** — payload 에 민감한 정보를 넣지 않는다.
3. **HS256 은 키 하나, RS256 은 서명 키와 검증 키가 따로다** — 여러 서비스가 검증하면 RS256.
4. **OAuth2 Code Flow 는 인가 코드를 서버가 `client_secret` 과 함께 토큰으로 바꾼다** — `state` 로 내가 시작한 로그인인지 확인한다.
5. **stateless 토큰을 끊으려면 다시 상태가 필요하다** — `jti` 블랙리스트와 리프레시 토큰 저장.

## 관련 자료

- [cors-csrf](../13-cors-csrf/2-summary.md)
- [django-rest](../05-django-rest/2-summary.md)
- [flask-api](../07-flask-api/2-summary.md)
- 원본: study-site 항목 데이터 `data/python/web-frameworks.json` 의 `oauth-jwt`

## 용어 풀이

- **인증** — 누구인지 확인하는 일.
- **인가** — 무엇을 해도 되는지 정하는 일.
- **JWT** — Header.Payload.Signature 를 점으로 이은 서명된 토큰 문자열.
- **클레임** — payload 안의 이름-값 한 쌍.
- **액세스 토큰** — API 를 부를 때 내는 짧은 수명의 토큰.
- **리프레시 토큰** — 새 액세스 토큰을 받는 데 쓰는 긴 수명의 토큰.
- **HS256** — HMAC-SHA256, 같은 키로 서명 · 검증하는 대칭 방식.
- **RS256** — RSA-SHA256, private key 로 서명하고 public key 로 검증하는 비대칭 방식.
- **PEM** — 키를 텍스트로 적는 표준 형식.
- **OAuth2** — 다른 서비스에 사용자 대신 접근할 권한을 위임받는 규약.
- **인가 코드** — 사용자 동의 뒤 받는 일회용 교환권, 서버가 토큰으로 바꾼다.
- **`state`** — 로그인 시작 때 만들어 콜백에서 비교하는 무작위 값.
- **CSRF** — 사용자가 의도하지 않은 요청을 그 사용자 브라우저로 보내게 하는 공격.
- **Bearer** — 「이 토큰을 가진 사람」으로 인정하는 `Authorization` 헤더 스키마.
- **`jti`** — 토큰 고유 ID 클레임.
- **블랙리스트** — 폐기된 토큰 ID 목록.
- **stateless** — 요청 사이에 서버가 상태를 저장하지 않는 성질.
- **TTL** — 저장한 값이 저절로 지워질 때까지의 시간.

## 더 들어가면

- `datetime.utcnow()` 는 Python 3.12 에서 폐기 예정 경고가 붙었다고 알려져 있다. `datetime.now(timezone.utc)` 로 바꿔 쓴다 (확인 필요).
- python-jose 의 유지보수가 뜸하다는 평이 있어 PyJWT 를 대신 고르는 경우가 많다 (확인 필요).
- 공개 클라이언트(모바일 · SPA)에서는 `client_secret` 을 숨길 수 없어 PKCE 를 덧붙인다 (확인 필요).
- 리프레시 토큰을 쓸 때마다 새것으로 바꾸고 옛것을 폐기하는 「회전(rotation)」을 하면 탈취된 토큰을 알아채기 쉽다 (확인 필요).
- 구글이 주는 `id_token` 자체가 구글이 서명한 JWT 라서, 구글의 공개 키로 검증해 사용자 정보를 얻을 수도 있다 (확인 필요).
- 서버 사이 시계가 조금 어긋나면 막 발급된 토큰이 만료로 보일 수 있어 검증에 여유 시간(leeway)을 두기도 한다 (확인 필요).
