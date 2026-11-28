# python/python-security/04 — secrets (안전한 토큰 생성) — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 32 · 64 · 32 — hex 앞 32자는 16바이트어치다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

`32 64 32` 가 찍힐 것이다.
`raw_token.hex()[:32]` 는 토큰의 앞 16바이트를 보여 준다.

**왜 그런가**

`token_bytes(32)` 는 32바이트 `bytes` 라 길이가 32다.
`token_hex(32)` 는 한 바이트를 두 글자로 적으므로 64자다.
`raw_token.hex()` 도 64자이고, `[:32]` 로 앞 32자만 자르면 2글자 = 1바이트이므로 16바이트어치다.
근거: 2-summary 「동작 방식 (1)」.

### 2. 43 · 64 — `+` `/` `=` 는 나오지 않는다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

`43 64` 가 찍힐 것이다.
`url_token` 에는 `+` · `/` · `=` 가 나오지 않는다.

**왜 그런가**

Base64 한 글자는 6비트를 나른다.
32바이트 = 256비트 → 256 ÷ 6 ≈ 42.7 → 43글자다.
48바이트 = 384비트 → 384 ÷ 6 = 64글자다.
URL 안전 Base64 는 `+` `/` 대신 `-` `_` 를 쓰고, 끝을 채우는 `=` 를 붙이지 않는다.
근거: 2-summary 「동작 방식 (1)」 · 「문법 — 형태와 규칙」.

### 3. `000042` 6자리 — `:06d` 가 앞을 0 으로 채운다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

`000042 6` 이 찍힐 것이다.

**왜 그런가**

`:06d` 는 정수를 너비 6 으로 쓰고 모자란 앞자리를 0 으로 채운다.
그래서 `randbelow(1_000_000)` 이 어떤 값을 내도 OTP 는 늘 6자리다.
`str(n)` 으로만 바꾸면 `"42"` 두 글자가 된다.
근거: 2-summary 「동작 방식 (2)」 · 「어디서 틀리나 5」.

### 4. Mersenne Twister 는 출력을 모으면 상태를 되살릴 수 있다

`random` 은 Mersenne Twister 알고리즘을 쓴다.
원본 주석대로 출력 624개를 모으면 내부 상태를 복원할 수 있고, 상태를 알면 이후 값을 모두 계산한다.
그래서 공격자는 이미 받은 토큰들을 근거로 다음 토큰을 맞힌다.
`secrets` 는 OS 의 CSPRNG 를 써서 출력을 모아도 다음 값을 계산할 수 없다.
근거: 2-summary 「동작 방식 (5)」.

### 5. 비교에 걸리는 시간이 정답을 흘리지 않게 하려고

`==` 는 다른 글자를 만나면 곧바로 멈출 수 있어, 앞부분이 많이 맞을수록 조금 늦게 끝난다.
공격자는 응답 시간을 재며 한 글자씩 맞혀 갈 수 있다(타이밍 공격).
`compare_digest` 는 어디서 달라지든 같은 방식으로 끝까지 보아, 걸린 시간으로 몇 글자가 맞았는지 알 수 없다.
다만 두 값의 길이가 다를 때도 시간이 같은지는 단정하지 않는다 (확인 필요).
근거: 2-summary 「동작 방식 (4)」 · 「구현 세부사항 대 언어 보장」.

### 6. 고치면 무늬가 생기고, 다시 뽑으면 고르게 남는다

통째로 다시 뽑으면 정책을 지키는 비밀번호들이 서로 같은 확률로 남는다(rejection sampling, 원본 주석의 「편향 없음」).
빠진 종류를 정해진 자리에 끼워 넣어 고치면 「그 자리에는 숫자가 오기 쉽다」 같은 무늬가 생겨 추측이 쉬워진다 (원본에 근거 없음 — 추론).
근거: 2-summary 「동작 방식 (3)」 · 「어디서 틀리나 6」.

### 7. 10 은 나오지 않는다 — 0~9 를 치우침 없이 고른다

`randbelow(n)` 의 범위는 0 이상 n 미만이라 `randbelow(10)` 은 0~9 만 낸다.
무작위 바이트(0~255)를 `% 10` 하면 256 이 10 으로 나누어떨어지지 않아 0~5 가 조금 더 자주 나온다(모듈로 편향).
`randbelow` 는 그런 치우침 없이 0~9 를 고르게 고른다.
근거: 2-summary 「동작 방식 (2)」.

### 8. 만족하지 않는다 — 128비트로 가이드의 절반이다

`token_hex(16)` 은 16바이트 = 128비트다.
원본 가이드는 「세션 토큰: 32바이트(256비트) 이상」이라 적는다.
가이드를 따르려면 `token_hex(32)` 처럼 32바이트 이상을 써야 한다.
근거: 2-summary 「문법 — 형태와 규칙」 표 · 「어디서 틀리나 3」.

### 9. 아니다 — 둘 다 256비트로 추측 난이도가 같다

두 함수 모두 32바이트의 무작위 값을 만든다.
엔트로피는 바이트 수가 정하고, 글자 수는 인코딩(16진수는 글자당 4비트, Base64 는 6비트)이 정한다.
그래서 64자짜리 hex 와 43자짜리 URL 안전 토큰은 같은 2²⁵⁶ 가지 중 하나다.
근거: 2-summary 「동작 방식 (1)」 · 「어디서 틀리나 2」.

## 실습 정답

### 실습 1. `secrets` 로 토큰 · 비밀번호 · PIN · 비교 데모 만들기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. 32바이트 `token_bytes`, hex 앞 32자와 길이 | `raw_token = secrets.token_bytes(32)` · `raw_token.hex()[:32]` · `len(raw_token)` |
| 2. 32바이트 `token_hex`, 앞 32자와 글자 수 | `hex_token = secrets.token_hex(32)` · `hex_token[:32]` · `len(hex_token)` |
| 3. 32바이트 `token_urlsafe`, 값과 글자 수 | `url_token = secrets.token_urlsafe(32)` |
| 4. 알파벳에서 `length` 글자 뽑기 | `generate_password` 의 `alphabet = string.ascii_letters + string.digits + string.punctuation` · `''.join(secrets.choice(alphabet) for _ in range(length))` |
| 5. 네 종류 확인 후 돌려주거나 다시 | `while True:` + `any(c.isupper() …)` 네 개 + `return password` |
| 6. 비밀번호 세 개 | `for i in range(3): pw = generate_password(16)` |
| 7. 6자리 PIN | `pin = ''.join(str(secrets.randbelow(10)) for _ in range(6))` |
| 8. 0 채운 6자리 OTP | `otp = f"{secrets.randbelow(1_000_000):06d}"` |
| 9. 재설정 URL · API 키 · 세션 ID | `reset_token = secrets.token_urlsafe(32)` · `api_key = secrets.token_urlsafe(48)` · `session_id = secrets.token_hex(16)` |
| 10. 같은 · 다른 문자열 비교 | `secrets.compare_digest(token_a, token_b)` · `secrets.compare_digest(token_a, token_c)` |
| 11. 색 고르기 · 20자 문자열 | `secrets.choice(colors)` · `''.join(secrets.choice(alphabet) for _ in range(20))` |
| 12. 0~99 · 0~255 정수 | `secrets.randbelow(100)` · `secrets.randbelow(256)` |
| 13. `random` 대 `secrets` · 길이 가이드 안내 | `=== secrets vs random ===` 아래 `print` 줄들 · `--- 토큰 길이 가이드 ---` 아래 `print` 줄들 |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`python/python-security/reference/secrets-module.py`

```python
# [보안 & 암호화] secrets (안전한 토큰 생성)
# 설명: secrets 모듈로 암호학적으로 안전한 토큰, URL 안전 문자열, 비교를 수행
# 팁: 보안 관련 랜덤 값은 반드시 secrets 모듈을 사용한다. random 모듈은 예측 가능하므로 절대 보안 목적으로 사용하면 안 된다. 토큰 길이는 최소 32바이트(256비트)를 권장한다. compare_digest()로 토큰을 비교하여 타이밍 공격을 방지한다.

# secrets: OS의 CSPRNG 기반 암호학적 난수 (random 모듈은 보안용 X)
import secrets
# string: 알파벳/숫자/특수문자 상수 모음
import string

# === 토큰 생성 ===
print("=== 토큰 생성 ===")

# token_bytes: 랜덤 바이트
# 256비트 → 무작위 추측에 사실상 충돌 불가능
raw_token = secrets.token_bytes(32)  # 32바이트
print(f"token_bytes: {raw_token.hex()[:32]}... ({len(raw_token)} bytes)")

# token_hex: 16진수 문자열
# 1바이트 = 2 hex 문자 → 32바이트 = 64자
hex_token = secrets.token_hex(32)  # 32바이트 = 64자 hex
print(f"token_hex:   {hex_token[:32]}... ({len(hex_token)}자)")

# token_urlsafe: URL 안전 Base64 문자열
# +/= 대신 -_ 사용 → URL 파라미터에 안전하게 사용 가능
url_token = secrets.token_urlsafe(32)  # 32바이트
print(f"token_urlsafe: {url_token} ({len(url_token)}자)")
print()

# === 안전한 비밀번호 생성 ===
print("=== 안전한 비밀번호 생성 ===")

# 정책 만족하는 비밀번호 자동 생성 (rejection sampling)
def generate_password(length=16):
    """강력한 비밀번호 생성 (최소 요구사항 보장)"""
    # 영문 대소문자 + 숫자 + 기호 모두 사용
    alphabet = string.ascii_letters + string.digits + string.punctuation

    while True:
        # secrets.choice: 균등 분포 안전 선택
        password = ''.join(secrets.choice(alphabet) for _ in range(length))
        # 최소 요구사항 확인
        # 정책 미달 시 재생성 (편향 없음)
        if (any(c.isupper() for c in password)
                and any(c.islower() for c in password)
                and any(c.isdigit() for c in password)
                and any(c in string.punctuation for c in password)):
            return password

# 3개 샘플 출력
for i in range(3):
    pw = generate_password(16)
    print(f"  비밀번호 {i+1}: {pw}")
print()

# === 안전한 PIN 코드 ===
print("=== PIN 코드 ===")
# randbelow(10): 0~9 중 균등 선택 → 모듈로 편향 없음
pin = ''.join(str(secrets.randbelow(10)) for _ in range(6))
print(f"6자리 PIN: {pin}")

# OTP 코드
# 1_000_000 미만 정수 → 0 패딩하여 6자리 보장
otp = f"{secrets.randbelow(1_000_000):06d}"  # 0~999999
print(f"OTP 코드:  {otp}")
print()

# === 안전한 URL 토큰 (비밀번호 재설정 등) ===
print("=== URL 토큰 ===")
# 비밀번호 재설정 링크: 시간 제한 + 일회성으로 운영
reset_token = secrets.token_urlsafe(32)
reset_url = f"https://example.com/reset?token={reset_token}"
print(f"비밀번호 재설정 URL: {reset_url}")

# API 키: 길수록 안전 (48바이트 = 384비트)
api_key = secrets.token_urlsafe(48)
print(f"API Key: {api_key}")

# 세션 ID: 쿠키에 저장
session_id = secrets.token_hex(16)
print(f"세션 ID: {session_id}")
print()

# === 안전한 비교 ===
print("=== 안전한 비교 (compare_digest) ===")
token_a = "abc123def456"
token_b = "abc123def456"
token_c = "abc123def789"

# 타이밍 공격 안전한 비교
# 항상 전체 길이만큼 비교 → 응답 시간으로 정답 추론 불가
print(f"같은 토큰: {secrets.compare_digest(token_a, token_b)}")  # True
print(f"다른 토큰: {secrets.compare_digest(token_a, token_c)}")  # False
print("compare_digest: 항상 일정한 시간에 비교 (타이밍 공격 방지)")
print()

# === secrets.choice: 안전한 랜덤 선택 ===
print("=== secrets.choice ===")
# 추첨/A-B 테스트 등 보안 관련 랜덤 선택
colors = ["red", "blue", "green", "yellow", "purple"]
print(f"랜덤 선택: {secrets.choice(colors)}")

# 안전한 랜덤 문자열
# 영숫자 조합 → URL/식별자에 안전
alphabet = string.ascii_letters + string.digits
random_str = ''.join(secrets.choice(alphabet) for _ in range(20))
print(f"랜덤 문자열: {random_str}")
print()

# === secrets.randbelow ===
print("=== secrets.randbelow ===")
# 0 이상 n 미만 안전 정수
print(f"0~99 범위: {secrets.randbelow(100)}")
print(f"0~255 범위: {secrets.randbelow(256)}")
print()

# === secrets vs random 비교 ===
print("=== secrets vs random ===")
# random 모듈의 한계
print("random 모듈:")
# Mersenne Twister: 624개 출력으로 내부 상태 복원 가능 → 예측 가능
print("  - Mersenne Twister 알고리즘 (예측 가능!)")
# 통계/시뮬레이션용
print("  - 시뮬레이션, 게임, 통계용")
# 보안 컨텍스트 절대 금지
print("  - 절대 보안 목적으로 사용 금지!")
# secrets 모듈의 강점
print("secrets 모듈:")
# /dev/urandom, BCryptGenRandom 등 OS 엔트로피 사용
print("  - OS의 암호학적 난수 생성기 (CSPRNG) 사용")
# 보안 토큰 전 영역
print("  - 토큰, 비밀번호, API 키, 세션 ID 등")
print("  - 항상 보안이 필요한 곳에 사용")
print()

# 토큰 길이 권장값 (256비트 이상 권장)
print("--- 토큰 길이 가이드 ---")
print("세션 토큰:       32바이트 (256비트) 이상")
print("API 키:          32~48바이트")
print("비밀번호 재설정:  32바이트")
print("CSRF 토큰:       32바이트")

# 출력:
# === 토큰 생성 ===
# token_hex: a1b2c3d4... (64자)
# token_urlsafe: Ab_Cd-Ef... (43자)
# === 안전한 비밀번호 생성 ===
# 비밀번호 1: kX9#mP2!qR5$nL...
# === 안전한 비교 ===
# 같은 토큰: True
```

**실행 결과** — 실행하지 않음 — 돌릴 때마다 출력이 달라지는 예제다 — 출력을 싣지 않았다.

**풀이 요점**

- `token_*` 의 인자는 바이트 수다 — 32 를 넣으면 hex 는 64자, URL 안전 문자열은 43자가 된다.
- 비밀번호는 `secrets.choice` 로 한 글자씩 뽑고, 정책을 못 지키면 `while True` 로 통째로 다시 뽑는다.
- PIN 은 `randbelow(10)` 여섯 번, OTP 는 `randbelow(1_000_000)` 한 번 + `:06d` 다.
- 토큰 비교는 `==` 가 아니라 `compare_digest` 로 한다.
- 원본의 세션 ID(`token_hex(16)`)는 같은 파일의 길이 가이드(32바이트 이상)보다 짧다는 점을 기억해 둔다.
- 무작위 값은 돌릴 때마다 바뀌므로, 확인할 것은 값이 아니라 길이 · 글자 종류 · `True`/`False` 순서다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — 돌릴 때마다 출력이 달라지는 예제다 — 출력을 싣지 않았다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
