# python/python-advanced/09 — hashlib (해시와 보안) — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 두 번 나눠 `update` 한 해시와 한 번에 뜬 해시 (예측)

```python
# 질문용 발췌
import hashlib
whole = hashlib.sha256(b"Hello, Python!").hexdigest()
h = hashlib.sha256()
h.update(b"Hello, ")
h.update(b"Python!")
print(h.hexdigest() == whole)
print(len(whole))
```

- 두 `print` 는 각각 무엇을 찍는가?

### 2. 같은 비밀번호를 솔트 없이 두 번 저장하면 (예측)

```python
# 질문용 발췌
a_salt, a_hash = hash_password_simple('mypassword123')
b_salt, b_hash = hash_password_simple('mypassword123')
_, c_hash = hash_password_simple('mypassword123', bytes.fromhex(a_salt))
print(a_hash == b_hash, a_hash == c_hash)
```

- 출력되는 두 불리언은 각각 무엇인가?

### 3. PBKDF2 저장 문자열의 모양 (예측)

```python
# 질문용 발췌
stored = hash_password_pbkdf2('secure_password')
parts = stored.split('$')
print(len(parts), parts[0], len(parts[1]), len(parts[2]))
```

- 네 값은 각각 무엇인가?

### 4. 단순 SHA-256 이 비밀번호 저장에 부적합한 까닭 (왜)
- 솔트도 반복도 없는 SHA-256 해시가 유출되면 무엇이 문제인가?
- 솔트만 붙였을 때 여전히 남는 약점은 무엇인가?

### 5. 해시 비교에 `==` 대신 `compare_digest` 를 쓰는 까닭 (왜)
- `==` 비교가 공격자에게 흘리는 정보는 무엇인가?

### 6. PBKDF2 결과에 반복 횟수와 솔트를 함께 붙여 두는 까닭 (왜)
- 검증 함수가 이 두 값 없이 일할 수 없는 이유는 무엇인가?

### 7. MD5 를 써도 되는 자리와 안 되는 자리 (경계)
- MD5 로 해도 되는 일과 해서는 안 되는 일을 가르는 기준은 무엇인가?

### 8. webhook 서명 비교에서 머리 글자를 빼면 (경계)
- `verify_webhook_signature` 에서 `f"sha256={expected}"` 대신 `expected` 만 비교하면 맞는 서명은 통과하는가?

### 9. HMAC 과 그냥 해시의 차이 (연결)
- 메시지 옆에 SHA-256 해시만 붙여 보내면 막지 못하는 공격을 HMAC 은 어떻게 막는가?

### 10. `secrets` 와 `os.urandom` 이 맡은 자리 (연결)
- 솔트 생성의 `os.urandom` 과 토큰 생성의 `secrets` 는 `random` 모듈과 무엇이 다르기에 보안 코드에 쓰이는가?

## 실습

### 실습 1. 해시 · 비밀번호 · HMAC · 토큰을 한 파일로 정리하기

**만들 것** — `hashlib` · `hmac` · `os` · `secrets` 로 기본 해시, 파일 해시, 솔트 해싱, PBKDF2, bcrypt 안내, HMAC, 보안 토큰을 차례로 보여 주는 스크립트를 만든다.

**준비물** — 표준 라이브러리만 쓴다. bcrypt 는 외부 패키지(`pip install bcrypt`)지만 이 과제에서는 코드를 주석으로만 두고 실행하지 않는다.

**요구 조건**

1단계 — 기본 해시
1. `"Hello, Python!"` 을 UTF-8 `bytes` 로 바꿔 `message` 에 담는다.
2. MD5 · SHA-1 · SHA-256 · SHA-512 · SHA3-256 · BLAKE2b(출력 32바이트)의 16진 다이제스트를 구해 출력한다. SHA-512 는 앞 64글자만 찍고 `...` 을 붙인다.

2단계 — 파일 해시와 점진적 해시
3. `file_hash(filepath, algorithm='sha256', chunk_size=8192)` 는 알고리즘 이름으로 해시 객체를 만들고, 파일을 바이트 모드로 열어 청크 단위로 끝까지 읽으며 누적 해싱한 뒤 16진 다이제스트를 돌려준다(워러스 연산자 사용).
4. 빈 SHA-256 객체에 `b"Hello, "` 과 `b"Python!"` 을 차례로 넣어 얻은 해시와 1단계의 SHA-256 을 출력하고, 둘이 같은지를 출력한다.

3단계 — 솔트 해싱
5. `hash_password_simple(password, salt=None)` 은 솔트가 없으면 32바이트 무작위 솔트를 만들고, 솔트 뒤에 비밀번호 바이트를 이어 SHA-256 16진 다이제스트를 구해 `(솔트의 16진 문자열, 해시)` 를 돌려준다.
6. `'mypassword123'` 으로 솔트 · 해시를 만들어 출력하고, 저장된 16진 솔트를 바이트로 되돌려 같은 비밀번호로 재계산한 결과가 같은지 출력한다.

4단계 — PBKDF2
7. `hash_password_pbkdf2(password, salt=None, iterations=600000)` 은 솔트가 없으면 32바이트 솔트를 만들고, PBKDF2-HMAC-SHA256(키 길이 32바이트)으로 키를 뽑아 `"반복횟수$솔트hex$키hex"` 문자열을 돌려준다.
8. `verify_password_pbkdf2(password, stored)` 는 저장 문자열을 `$` 로 나눠 같은 매개변수로 재계산하고, `hmac.compare_digest` 로 비교한 결과를 돌려준다.
9. `'secure_password'` 로 저장값을 만들어 앞 50글자를 출력하고, 맞는 비밀번호와 `'wrong_password'` 의 검증 결과를 출력한다.

5단계 — bcrypt 안내
10. bcrypt 의 솔트 생성(`gensalt(rounds=12)`) · 해싱(`hashpw`) · 검증(`checkpw`) 코드를 주석으로 남기고, 세 함수의 역할과 `rounds=12` 설명을 네 줄로 출력한다.

6단계 — HMAC
11. 비밀키 `b'my-secret-key-for-hmac'` 과 메시지 `b'중요한 메시지'` 로 HMAC-SHA256 을 계산해 출력하고, 같은 키로 재계산한 값과 `hmac.compare_digest` 로 비교한 결과를 출력한다.
12. `verify_webhook_signature(payload, signature, secret)` 는 문자열 인자를 바이트로 바꿔 HMAC-SHA256 16진 값을 구하고, `sha256=` 머리를 붙인 값과 받은 서명을 `compare_digest` 로 비교해 돌려준다.

7단계 — 보안 토큰과 정리
13. `secrets` 로 32바이트 16진 토큰, 32바이트 URL-safe 토큰, 16바이트 원시 토큰(16진으로 표시), 0~99 난수를 만들어 출력한다.
14. 마지막에 핵심 정리 여섯 줄을 출력한다.

**시작 코드**

```python
# hashlib - 해시 함수와 비밀번호 보안
import hashlib
import hmac
import os
import secrets
import binascii


# === 1. 기본 해시 ===
print("=== 해시 함수 ===")
message = None  # TODO: "Hello, Python!" 을 UTF-8 bytes 로

md5_hash = None     # TODO
print(f"MD5:     {md5_hash}")
sha1_hash = None    # TODO
print(f"SHA-1:   {sha1_hash}")
sha256_hash = None  # TODO
print(f"SHA-256: {sha256_hash}")
sha512_hash = None  # TODO
print(f"SHA-512: {sha512_hash[:64]}...")
sha3_hash = None    # TODO
print(f"SHA3-256: {sha3_hash}")
blake2_hash = None  # TODO: 출력 32바이트
print(f"BLAKE2b: {blake2_hash}")


# === 2. 파일 해시 (무결성 검증) ===
print("\n=== 파일 해시 ===")

def file_hash(filepath, algorithm='sha256', chunk_size=8192):
    """대용량 파일의 해시 계산 (메모리 효율적)"""
    # TODO: 이름으로 해시 객체 생성 → 'rb' 로 열기 → 청크 루프로 update → hexdigest
    pass

# 사용: checksum = file_hash('big_file.zip')

h = None  # TODO: 빈 SHA-256 객체에 두 조각을 차례로 넣기
print(f"점진적 해시: {h.hexdigest()}")
print(f"일괄 해시:   {sha256_hash}")
print(f"결과 동일:   {h.hexdigest() == sha256_hash}")


# === 3. 솔트 해싱 (비밀번호) ===
print("\n=== 솔트 해싱 ===")

def hash_password_simple(password, salt=None):
    """솔트 + SHA-256 (기본 수준)"""
    # TODO: 솔트 준비 → 솔트 + 비밀번호 바이트 → SHA-256 → (salt.hex(), 해시)
    pass

salt, hashed = hash_password_simple('mypassword123')
print(f"솔트: {salt}")
print(f"해시: {hashed}")

salt_bytes = None  # TODO: 16진 솔트를 bytes 로
_, verify_hash = hash_password_simple('mypassword123', salt_bytes)
print(f"검증: {verify_hash == hashed}")


# === 4. PBKDF2 (권장 비밀번호 해싱) ===
print("\n=== PBKDF2 ===")

def hash_password_pbkdf2(password, salt=None, iterations=600000):
    """PBKDF2-HMAC-SHA256 (NIST 권장)"""
    # TODO: 솔트 준비 → pbkdf2_hmac → "반복$솔트hex$키hex"
    pass

def verify_password_pbkdf2(password, stored):
    """PBKDF2 비밀번호 검증"""
    # TODO: '$' 로 분해 → 같은 매개변수로 재계산 → compare_digest
    pass

stored = hash_password_pbkdf2('secure_password')
print(f"저장값: {stored[:50]}...")
print(f"검증 (맞는 비밀번호): {verify_password_pbkdf2('secure_password', stored)}")
print(f"검증 (틀린 비밀번호): {verify_password_pbkdf2('wrong_password', stored)}")


# === 5. bcrypt (전용 비밀번호 해시) ===
print("\n=== bcrypt 패턴 ===")
# TODO: gensalt / hashpw / checkpw 사용 코드를 주석으로 남기기

print("bcrypt.gensalt(rounds=12): 솔트 생성")
print("bcrypt.hashpw(password, salt): 해싱")
print("bcrypt.checkpw(password, hashed): 검증")
print("rounds=12는 약 0.25초 소요 (brute-force 방지)")


# === 6. HMAC (메시지 인증 코드) ===
print("\n=== HMAC ===")
secret_key = b'my-secret-key-for-hmac'
message = b'중요한 메시지'

mac = None  # TODO: HMAC-SHA256
print(f"HMAC: {mac.hexdigest()}")

expected_mac = mac.hexdigest()
received_mac = None  # TODO: 같은 키로 재계산한 16진 값
is_valid = None      # TODO: 안전한 비교
print(f"HMAC 검증: {is_valid}")

def verify_webhook_signature(payload, signature, secret):
    # TODO: HMAC-SHA256 16진 값 → "sha256=" 머리를 붙여 안전하게 비교
    pass


# === 7. 보안 토큰 생성 ===
print("\n=== 보안 토큰 ===")
print(f"토큰(hex):     {None}")  # TODO: 32바이트 16진 토큰
print(f"토큰(urlsafe): {None}")  # TODO: 32바이트 URL-safe 토큰
print(f"토큰(bytes):   {None}")  # TODO: 16바이트 원시 토큰을 16진으로
print(f"랜덤 숫자(0-99): {None}")  # TODO: 0 이상 100 미만
print(f"안전한 비교: secrets.compare_digest(a, b)")


print("\nhashlib 보안 핵심 정리")
print("="*50)
print("MD5/SHA-1: 보안 부적합, 체크섬에만 사용")
print("SHA-256: 일반 해싱에 권장")
print("PBKDF2: 비밀번호 해싱 표준 (NIST 권장)")
print("bcrypt: 비밀번호 전용 (자동 솔트, 시간 조절)")
print("HMAC: 메시지 무결성 + 인증")
print("hmac.compare_digest: 타이밍 공격 방지 비교")
```

**확인 방법** — `python hashlib-security.py` 로 돌린다. 「결과 동일」과 솔트 해싱 「검증」이 `True` 인지, PBKDF2 검증이 맞는 비밀번호에서 `True` · 틀린 비밀번호에서 `False` 인지, 「HMAC 검증」이 `True` 인지 본다. 토큰 줄은 돌릴 때마다 값이 바뀌어야 한다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
