# python/python-security/06 — Fernet (대칭 암호화) — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 토큰은 다르고, 풀면 같다 — `False` 와 `True`

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
False
True
```

**왜 그런가**

- `encrypt` 는 호출할 때마다 IV 를 새로 만들어 쓰고, 토큰에 발급 타임스탬프도 넣는다.
- 그래서 같은 평문이라도 토큰 `a` 와 `b` 는 다르다.
- 두 토큰 모두 같은 키로 만들었으므로 풀면 둘 다 `b"hello"` 다.
- 근거: 2-summary 「동작 방식 (2)」.

### 2. `InvalidToken` 이 찍힌다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
InvalidToken
```

**왜 그런가**

- `decrypt` 는 먼저 자기 키로 HMAC 을 다시 계산해 토큰 속 HMAC 과 비교한다.
- 키가 다르니 HMAC 이 맞지 않고, `InvalidToken` 예외가 난다.
- `type(e).__name__` 은 그 클래스 이름을 돌려준다.
- 근거: 2-summary 「동작 방식 (3)」.

### 3. 실패한다 — 거꾸로 된 순서는 옛 키로 다시 잠근다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

마지막 줄에서 `InvalidToken` 예외가 난다.

**왜 그런가**

- `rotate` 는 토큰을 푼 뒤 **첫 번째** 키로 다시 암호화한다.
- 이 코드는 첫 번째 자리에 `old_key` 를 두었으므로 `rotated` 는 여전히 `old_key` 토큰이다.
- `new_key` 만 가진 `Fernet` 으로는 HMAC 이 맞지 않아 풀 수 없다.
- 새 키를 맨 앞에 두어야 로테이션이 된다.
- 근거: 2-summary 「동작 방식 (5)」 · 「어디서 틀리나 6」.

### 4. 둘 다 HMAC 검사에서 걸리기 때문이다

`decrypt` 는 내용을 풀기 전에 HMAC 부터 검사한다.
잘못된 키로 계산한 HMAC 도, 바뀐 토큰에 대해 계산한 HMAC 도 토큰 속 값과 맞지 않는다.
검사 결과는 「맞다 / 안 맞다」뿐이므로, 예외도 `InvalidToken` 하나로 나온다.
그래서 예외만 보고 원인을 가를 수 없다.
근거: 2-summary 「동작 방식 (3)」 · 「어디서 틀리나 5」.

### 5. 소스를 보는 누구나 데이터를 풀 수 있게 된다

대칭 암호화는 잠그는 키와 여는 키가 같다.
키가 소스에 있으면, 소스를 읽을 수 있는 사람(저장소 접근자 · 유출된 코드를 얻은 사람)이 곧 모든 암호문을 풀 수 있는 사람이 된다.
그래서 키는 환경 변수나 KMS 같은 코드 밖에 둔다.
근거: 2-summary 「한눈에」 · 「어디서 틀리나 1」.

### 6. `decrypt` 에서 지정하고, 토큰 속 발급 시각을 기준으로 잰다

`encrypt` 에는 TTL 인자가 없다 — 토큰에 발급 타임스탬프만 박는다.
`decrypt(token, ttl=10)` 처럼 복호화할 때 유효 시간을 정한다.
발급 시각에 `ttl` 을 더한 시각이 이미 지났으면 `InvalidToken` 으로 거부한다.
근거: 2-summary 「동작 방식 (4)」.

### 7. 풀 수 없다

실행할 때마다 `generate_key()` 가 새 무작위 키를 만든다.
지난 실행의 토큰은 지난 키로 잠겼으므로 새 키로는 HMAC 이 맞지 않아 `InvalidToken` 이 난다.
설정을 저장해 두고 다시 쓰려면 키를 한 번 만들어 보관하고, 그 키를 읽어 와야 한다.
근거: 2-summary 「어디서 틀리나 2」.

### 8. Fernet 은 `bytes` 만 암호화하기 때문이다

`encrypt` 는 바이트를 받는다.
딕셔너리는 바이트가 아니므로 먼저 `json.dumps` 로 글자열로 펼치고, `encode('utf-8')` 로 바이트로 바꾼다.
복호화 뒤에는 거꾸로 `decode` → `json.loads` 를 거쳐 딕셔너리를 되살린다.
근거: 2-summary 「동작 방식 (6)」 · 「어디서 틀리나 3」.

### 9. 모든 옛 토큰을 `rotate` 한 뒤에 버린다 — 그 전까지는 옛 키로도 풀어 주기 때문이다

`MultiFernet([새 키, 옛 키])` 는 새로 잠그는 것은 새 키로 하고, 풀 때는 두 키를 차례로 시도한다.
그래서 교체 도중에도 옛 데이터와 새 데이터를 모두 읽을 수 있어 서비스가 멈추지 않는다.
저장된 옛 토큰을 모두 `rotate` 해서 새 키 토큰으로 바꾸고 나면, 옛 키가 필요한 데이터가 남지 않으므로 그때 옛 키를 폐기한다.
근거: 2-summary 「동작 방식 (5)」.

## 실습 정답

### 실습 1. Fernet 으로 암호화 · TTL · 키 로테이션 · 설정 암호화를 한 파일에 구현하기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. 키 생성 · 길이 출력 | `key = Fernet.generate_key()` · `len(key)` |
| 2. 인스턴스 만들고 암호화 | `f = Fernet(key)` · `f.encrypt(plaintext.encode('utf-8'))` |
| 3. 복호화 · 일치 확인 | `f.decrypt(encrypted)` · `decrypted.decode('utf-8') == plaintext` |
| 4. 잘못된 키로 시도 | `wrong_f = Fernet(wrong_key)` · `wrong_f.decrypt(encrypted)` · `type(e).__name__` |
| 5. TTL 안 복호화 | `f2 = Fernet(key)` · `f2.decrypt(token, ttl=10)` |
| 6. TTL 만료 | `time.sleep(1)` · `f2.decrypt(token, ttl=0)` |
| 7. MultiFernet 복호화 | `MultiFernet([Fernet(new_key), Fernet(old_key)])` · `multi.decrypt(old_encrypted)` |
| 8. 로테이션 후 새 키로 복호화 | `multi.rotate(old_encrypted)` · `new_only.decrypt(rotated)` |
| 9. `SecureConfig` 클래스 | `__init__` 의 `self.fernet` · `encrypt_config` · `decrypt_config` |
| 10. 설정 암호화 · 복원 출력 | `sc.encrypt_config(sensitive_config)` · `sc.decrypt_config(encrypted_config)` |
| 11. 내부 구조 네 줄 | `print("--- Fernet 내부 구조 ---")` 아래 네 `print` |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`python/python-security/reference/fernet-encryption.py`

```python
# [보안 & 암호화] Fernet (대칭 암호화)
# 설명: cryptography.Fernet으로 데이터를 대칭 암호화하고 키 관리, 키 로테이션을 구현
# 팁: Fernet은 AES-128-CBC + HMAC-SHA256을 사용하여 기밀성과 무결성을 모두 보장한다. 키는 환경 변수나 키 관리 서비스(KMS)에 저장하고, 코드에 하드코딩하지 않는다. MultiFernet으로 키 로테이션을 구현하면 서비스 중단 없이 키를 교체할 수 있다. TTL을 사용하면 시간 제한 토큰을 만들 수 있다.

# Fernet: 대칭 암호화 (AES-128-CBC + HMAC), MultiFernet: 다중 키로 로테이션 지원
from cryptography.fernet import Fernet, MultiFernet
# base64: 키/암호문 인코딩 보조
import base64
# os: 환경 변수 키 로딩에 사용
import os
# json: 구조화된 데이터를 암호화 가능하게 직렬화
import json
# time: TTL 만료 시뮬레이션
import time

# === 키 생성 ===
print("=== Fernet 키 생성 ===")
# 256비트 키를 URL-safe Base64로 인코딩하여 반환 (저장/전송 용이)
key = Fernet.generate_key()
print(f"키: {key}")
# 키 크기 = 32바이트(256비트) → AES 128 + HMAC 128로 분할 사용
print(f"키 길이: {len(key)} bytes (Base64 인코딩된 256비트)")
print()

# === 기본 암호화/복호화 ===
print("=== 암호화/복호화 ===")
# Fernet 인스턴스 생성 (키 바인딩)
f = Fernet(key)

# 암호화
plaintext = "민감한 데이터: 비밀번호, API 키 등"
# encrypt: IV 자동 생성 + AES 암호화 + HMAC 부착 → 변조 감지 가능
encrypted = f.encrypt(plaintext.encode('utf-8'))
print(f"평문:     {plaintext}")
print(f"암호문:   {encrypted[:50]}...")
print(f"암호문 길이: {len(encrypted)} bytes")

# 복호화
# decrypt: HMAC 검증 → 실패 시 InvalidToken (변조/잘못된 키 모두 거부)
decrypted = f.decrypt(encrypted)
print(f"복호화:   {decrypted.decode('utf-8')}")
print(f"일치:     {decrypted.decode('utf-8') == plaintext}")
print()

# === 잘못된 키로 복호화 시도 ===
print("=== 잘못된 키 ===")
# 다른 키 생성 (공격자 시나리오 시뮬레이션)
wrong_key = Fernet.generate_key()
wrong_f = Fernet(wrong_key)
try:
    # HMAC 검증이 실패하여 예외 발생 → 키 없이 복호화 불가
    wrong_f.decrypt(encrypted)
except Exception as e:
    print(f"복호화 실패: {type(e).__name__}")
    print("  → 잘못된 키 또는 변조된 데이터")
print()

# === TTL (시간 제한 암호화) ===
print("=== TTL (시간 제한) ===")
# 같은 키로 또 다른 인스턴스 생성
f2 = Fernet(key)
# 암호문 내부에 발급 타임스탬프 포함 → 만료 검사에 활용
token = f2.encrypt(b"time-limited data")

# 즉시 복호화 (TTL 내)
# ttl=10: 발급 후 10초까지 유효
result = f2.decrypt(token, ttl=10)  # 10초 이내만 유효
print(f"TTL 내 복호화: {result}")

# TTL 초과 시뮬레이션
print("TTL=0으로 테스트:")
# 1초 대기 후 ttl=0으로 검증 → 즉시 만료 처리
time.sleep(1)
try:
    f2.decrypt(token, ttl=0)  # 이미 0초 지남
except Exception as e:
    print(f"  TTL 만료: {type(e).__name__}")
print()

# === 키 로테이션 (MultiFernet) ===
print("=== 키 로테이션 ===")

# 기존 키
old_key = Fernet.generate_key()
# 새 키
new_key = Fernet.generate_key()

# 기존 키로 암호화된 데이터
old_fernet = Fernet(old_key)
# 과거 암호문 (DB에 저장되어 있다고 가정)
old_encrypted = old_fernet.encrypt(b"old data encrypted")

# MultiFernet: 새 키로 암호화, 모든 키로 복호화 시도
# 첫 번째 키가 새 키 → 새로 암호화는 항상 새 키로 수행
multi = MultiFernet([Fernet(new_key), Fernet(old_key)])

# 기존 데이터 복호화 (old_key 사용)
# 순차 시도 → 첫 키 실패 시 다음 키로 (구버전 데이터 호환)
decrypted = multi.decrypt(old_encrypted)
print(f"기존 데이터 복호화: {decrypted}")

# 키 로테이션: 기존 데이터를 새 키로 재암호화
# rotate: 복호화 후 첫 키로 재암호화 → 무중단 마이그레이션
rotated = multi.rotate(old_encrypted)
print(f"로테이션 후: 새 키로 재암호화됨")

# 새 키만으로 복호화 가능
new_only = Fernet(new_key)
# 로테이션 후에는 구 키 폐기 가능
result = new_only.decrypt(rotated)
print(f"새 키로 복호화: {result}")
print()

# === 실무 패턴: 설정 파일 암호화 ===
print("=== 설정 파일 암호화 ===")

# 설정 딕셔너리를 통째로 암호화하는 헬퍼
class SecureConfig:
    def __init__(self, key):
        # 키 바인딩
        self.fernet = Fernet(key)

    def encrypt_config(self, config_dict):
        """딕셔너리를 암호화된 문자열로"""
        # JSON 직렬화 → 바이트 변환 → 암호화
        json_bytes = json.dumps(config_dict).encode('utf-8')
        return self.fernet.encrypt(json_bytes)

    def decrypt_config(self, encrypted_data):
        """암호화된 데이터를 딕셔너리로"""
        # 복호화 → JSON 역직렬화로 원본 구조 복원
        json_bytes = self.fernet.decrypt(encrypted_data)
        return json.loads(json_bytes.decode('utf-8'))

# 설정 전용 키 (실무에선 KMS/Vault에서 로드)
config_key = Fernet.generate_key()
sc = SecureConfig(config_key)

# 민감 정보가 포함된 설정 (DB URL, API 시크릿 등)
sensitive_config = {
    "database_url": "postgresql://user:pass@host/db",
    "api_secret": "sk-1234567890abcdef",
    "redis_password": "r3d!s_p@ss"
}

# 암호화된 형태로 저장 가능
encrypted_config = sc.encrypt_config(sensitive_config)
print(f"암호화된 설정: {encrypted_config[:40]}...")

# 런타임에 복호화하여 사용
restored = sc.decrypt_config(encrypted_config)
print(f"복원된 설정: {restored}")
print()

# Fernet 토큰 내부 구성 요소 설명
print("--- Fernet 내부 구조 ---")
# AES-128-CBC: 기밀성 (블록 암호)
print("알고리즘: AES-128-CBC + HMAC-SHA256")
# 256비트 키 = 128비트 암호화 키 + 128비트 서명 키로 분리
print("키 256비트: 128비트 암호화 + 128비트 서명")
# 토큰 = 0x80(버전) + 8바이트 타임스탬프 + 16바이트 IV + 암호문 + 32바이트 HMAC
print("암호문에 포함: 버전 + 타임스탬프 + IV + 암호데이터 + HMAC")
print("→ 기밀성(AES) + 무결성(HMAC) + 인증 모두 제공")

# 출력:
# === Fernet 키 생성 ===
# 키: b'ABcDeFgH...='
# === 암호화/복호화 ===
# 평문: 민감한 데이터: 비밀번호, API 키 등
# 복호화: 민감한 데이터: 비밀번호, API 키 등
# === 키 로테이션 ===
# 기존 데이터 복호화: b'old data encrypted'
# 새 키로 복호화: b'old data encrypted'
```

**실행 결과** — 실행하지 않음 — 외부 라이브러리 `cryptography` 가 있어야 도는 예제다 — 그것 없이 만들어 실행하지 않았다.

**풀이 요점**

- 문자열은 `encode` 로 바이트가 된 뒤에야 `encrypt` 에 들어가고, `decrypt` 결과는 `decode` 로 되돌린다.
- 잘못된 키 · TTL 만료는 모두 `InvalidToken` 으로 잡힌다 — 원본은 `except Exception` 으로 넓게 잡는다.
- TTL 은 `decrypt` 의 인자이고, `time.sleep(1)` 은 발급 뒤 시간이 흘렀음을 확실히 하려고 넣었다.
- `MultiFernet` 의 첫 자리에 새 키를 두어야 `rotate` 결과를 새 키만으로 풀 수 있다.
- `SecureConfig` 는 `json.dumps` → `encode` → `encrypt` 와 그 반대 순서를 메서드 둘로 감싼다.
- 예제는 키를 매번 새로 만들므로, 실제로 저장 · 재사용하려면 키를 환경 변수나 KMS 에서 읽어 오게 바꿔야 한다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — 외부 라이브러리 `cryptography` 가 있어야 도는 예제다 — 그것 없이 만들어 실행하지 않았다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
