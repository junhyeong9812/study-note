# python/python-security/04 — secrets (안전한 토큰 생성) — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 32바이트 토큰을 16진수로 적으면 (예측)

```python
# 질문용 발췌
raw_token = secrets.token_bytes(32)
hex_token = secrets.token_hex(32)
print(len(raw_token), len(hex_token), len(raw_token.hex()[:32]))
```

- 세 숫자는 각각 무엇인가?
- `raw_token.hex()[:32]` 는 토큰의 몇 바이트어치를 보여 주나?

### 2. URL 안전 토큰의 길이와 글자 (예측)

```python
# 질문용 발췌
url_token = secrets.token_urlsafe(32)
api_key = secrets.token_urlsafe(48)
print(len(url_token), len(api_key))
```

- 두 길이는 각각 몇인가?
- `url_token` 안에 `+` · `/` · `=` 가 나올 수 있나?

### 3. 뽑힌 수가 작을 때의 OTP (예측)

```python
# 질문용 발췌
n = 42   # secrets.randbelow(1_000_000) 이 42 를 돌려줬다고 하자
otp = f"{n:06d}"
print(otp, len(otp))
```

- 어떤 문자열과 길이가 찍히나?

### 4. 보안 값에 `random` 을 쓰면 안 되는 까닭 (왜)

- `random.choice` 로 만든 토큰도 겉으로는 무작위처럼 보이는데, 공격자는 무엇을 근거로 다음 토큰을 맞힐 수 있나?

### 5. 결과가 같은데도 `compare_digest` 를 쓰는 까닭 (왜)

- `==` 와 `compare_digest` 는 돌려주는 값이 같은데, 토큰 비교에서 `compare_digest` 를 고르는 이유는 무엇인가?

### 6. 정책 미달 비밀번호를 통째로 다시 뽑는 까닭 (왜)

- `generate_password` 가 숫자가 빠진 비밀번호를 고쳐 쓰지 않고 버린 뒤 처음부터 다시 뽑는 이유는 무엇인가?

### 7. `randbelow` 의 범위 끝 (경계)

- `secrets.randbelow(10)` 이 10 을 돌려줄 수 있나, 그리고 PIN 한 자리를 `무작위 바이트 % 10` 대신 이것으로 뽑는 까닭은 무엇인가?

### 8. 원본의 세션 ID 와 원본의 가이드 (경계)

- 원본이 세션 ID 로 쓴 `secrets.token_hex(16)` 은 원본 자신의 「세션 토큰 길이 가이드」를 만족하나?

### 9. 글자 수와 추측 난이도 (연결)

- `token_hex(32)` 는 64자이고 `token_urlsafe(32)` 는 43자인데, 더 긴 쪽이 더 맞히기 어려운가?

## 실습

### 실습 1. `secrets` 로 토큰 · 비밀번호 · PIN · 비교 데모 만들기

**만들 것** — `secrets` 모듈의 토큰 생성, 비밀번호 · PIN · OTP 생성, 안전한 비교, 선택 · 정수 뽑기, `random` 과의 비교 안내를 차례로 찍는 스크립트 하나.

**요구 조건**

1단계 — 토큰 생성
1. 32바이트 `token_bytes` 를 만들고, hex 로 바꾼 앞 32자와 바이트 길이를 찍는다.
2. 32바이트 `token_hex` 를 만들고, 앞 32자와 전체 글자 수를 찍는다.
3. 32바이트 `token_urlsafe` 를 만들고, 전체 값과 글자 수를 찍는다.

2단계 — 비밀번호
4. `generate_password(length=16)` 함수: 대소문자 · 숫자 · 기호로 된 알파벳에서 `secrets.choice` 로 `length` 글자를 뽑는다.
5. 대문자 · 소문자 · 숫자 · 기호가 하나 이상씩 있으면 돌려주고, 아니면 처음부터 다시 뽑는다.
6. 이 함수로 비밀번호 세 개를 만들어 번호와 함께 찍는다.

3단계 — PIN · OTP
7. `randbelow(10)` 을 여섯 번 불러 6자리 PIN 을 만든다.
8. `randbelow(1_000_000)` 을 한 번 불러 0 으로 채운 6자리 OTP 를 만든다.

4단계 — 용도별 토큰
9. 32바이트 URL 안전 토큰을 넣은 비밀번호 재설정 URL, 48바이트 URL 안전 API 키, 16바이트 hex 세션 ID 를 찍는다.

5단계 — 비교 · 선택 · 정수
10. 같은 두 문자열과 다른 두 문자열을 `compare_digest` 로 비교한 결과를 찍는다.
11. 색 목록에서 `secrets.choice` 로 하나를 고르고, 영숫자 20자 랜덤 문자열을 만든다.
12. `randbelow(100)` 과 `randbelow(256)` 의 값을 찍는다.

6단계 — 안내
13. `random` 과 `secrets` 의 차이, 토큰 길이 가이드를 안내 문구로 찍는다.

**시작 코드**

```python
import secrets
import string

# === 토큰 생성 ===
print("=== 토큰 생성 ===")
raw_token = None   # TODO: 32바이트 랜덤 바이트
print(f"token_bytes: {raw_token.hex()[:32]}... ({len(raw_token)} bytes)")
hex_token = None   # TODO: 32바이트를 16진수 문자열로
print(f"token_hex:   {hex_token[:32]}... ({len(hex_token)}자)")
url_token = None   # TODO: 32바이트를 URL 안전 문자열로
print(f"token_urlsafe: {url_token} ({len(url_token)}자)")
print()

# === 안전한 비밀번호 생성 ===
print("=== 안전한 비밀번호 생성 ===")

def generate_password(length=16):
    """강력한 비밀번호 생성 (최소 요구사항 보장)"""
    alphabet = None  # TODO: 대소문자 + 숫자 + 기호
    while True:
        password = None  # TODO: alphabet 에서 length 글자를 안전하게 뽑아 이어 붙이기
        # TODO: 대문자·소문자·숫자·기호가 모두 있으면 return, 아니면 다시
        pass

for i in range(3):
    pw = generate_password(16)
    print(f"  비밀번호 {i+1}: {pw}")
print()

# === PIN 코드 ===
print("=== PIN 코드 ===")
pin = None   # TODO: 0~9 를 여섯 번 뽑아 이어 붙이기
print(f"6자리 PIN: {pin}")
otp = None   # TODO: 0~999999 하나를 뽑아 6자리로 0 채움
print(f"OTP 코드:  {otp}")
print()

# === URL 토큰 ===
print("=== URL 토큰 ===")
reset_token = None   # TODO: 32바이트 URL 안전 토큰
reset_url = f"https://example.com/reset?token={reset_token}"
print(f"비밀번호 재설정 URL: {reset_url}")
api_key = None       # TODO: 48바이트 URL 안전 토큰
print(f"API Key: {api_key}")
session_id = None    # TODO: 16바이트 hex 토큰
print(f"세션 ID: {session_id}")
print()

# === 안전한 비교 ===
print("=== 안전한 비교 (compare_digest) ===")
token_a = "abc123def456"
token_b = "abc123def456"
token_c = "abc123def789"
# TODO: token_a 와 token_b, token_a 와 token_c 를 타이밍 안전하게 비교해 찍기
print("compare_digest: 항상 일정한 시간에 비교 (타이밍 공격 방지)")
print()

# === secrets.choice ===
print("=== secrets.choice ===")
colors = ["red", "blue", "green", "yellow", "purple"]
# TODO: colors 에서 하나 골라 찍기
alphabet = string.ascii_letters + string.digits
random_str = None   # TODO: alphabet 에서 20글자
print(f"랜덤 문자열: {random_str}")
print()

# === secrets.randbelow ===
print("=== secrets.randbelow ===")
# TODO: 0~99, 0~255 범위 정수를 찍기
print()

# === secrets vs random ===
print("=== secrets vs random ===")
# TODO: random 모듈(Mersenne Twister, 예측 가능, 시뮬레이션·게임·통계용, 보안 금지)과
#       secrets 모듈(OS CSPRNG, 토큰·비밀번호·API 키·세션 ID)의 차이를 찍기
print()

print("--- 토큰 길이 가이드 ---")
# TODO: 세션 토큰 · API 키 · 비밀번호 재설정 · CSRF 토큰의 권장 길이를 찍기
```

**확인 방법** — `python secrets-module.py` 로 돌려, token_hex 줄의 글자 수가 64, token_urlsafe 줄이 43 인지, 비밀번호 세 개에 네 종류 글자가 모두 들어 있는지, PIN · OTP 가 6자리인지, 비교 줄이 `True` · `False` 순인지 본다. 무작위 값은 돌릴 때마다 달라진다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
