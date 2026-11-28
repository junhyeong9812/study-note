# python/python-advanced/09 — hashlib (해시와 보안) — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. `True` 와 `64` — 조각내 넣어도 같은 해시, 256비트는 16진 64글자

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
True
64
```

**왜 그런가**
`update()` 는 지금까지 넣은 바이트 뒤에 이어 붙이는 누적 해싱이라, `b"Hello, "` 과 `b"Python!"` 을 차례로 넣은 것은 `b"Hello, Python!"` 을 한 번에 넣은 것과 같다.
SHA-256 의 결과는 256비트이고 16진 한 글자가 4비트이므로 `hexdigest()` 는 64글자다.
근거: 2-summary 「동작 방식 (1)」「동작 방식 (2)」.

### 2. `False True` — 솔트가 다르면 다르고, 솔트가 같으면 같다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
False True
```

**왜 그런가**
솔트를 넘기지 않으면 호출마다 `os.urandom(32)` 로 새 솔트를 뽑으므로 `a_hash` 와 `b_hash` 는 다르다(32바이트 무작위 값이 우연히 같을 일은 사실상 없다).
`c_hash` 는 `a` 의 솔트를 `bytes.fromhex` 로 되돌려 넣었으므로 같은 입력이 되어 `a_hash` 와 같다 — 이것이 곧 검증 절차다.
근거: 2-summary 「동작 방식 (3)」.

### 3. `3 600000 64 64` — 반복 횟수 · 솔트 · 키의 세 조각

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
3 600000 64 64
```

**왜 그런가**
저장 문자열은 `f"{iterations}${salt.hex()}${dk.hex()}"` 이므로 `$` 로 나누면 세 조각이다.
첫 조각은 기본값 `600000` 이고, 문자열이므로 `600000` 으로 찍힌다.
솔트는 32바이트, 키는 `dklen=32` 로 32바이트이므로 각각 16진 64글자다.
16진 문자열에는 `$` 가 들어갈 수 없어 나누기가 어긋나지 않는다.
근거: 2-summary 「동작 방식 (4)」.

### 4. 표 조회와 빠른 대입 — 솔트는 앞의 것만 막는다

솔트 없는 SHA-256 해시가 새면, 흔한 비밀번호의 해시를 미리 계산해 둔 레인보우 테이블에서 찾아 원래 비밀번호를 곧바로 알아낼 수 있다.
같은 비밀번호를 쓴 사용자끼리 해시도 같아 한 번에 드러난다.
솔트를 붙이면 미리 만든 표는 쓸모가 없어지지만, SHA-256 한 번은 계산이 빨라 솔트를 아는 공격자가 후보 비밀번호를 대량으로 넣어 보는 무차별 대입은 여전히 빠르다.
그래서 PBKDF2 · bcrypt · scrypt 처럼 반복으로 느리게 만든 방식을 쓴다.
근거: 2-summary 「동작 방식 (3)」「어디서 틀리나 1 · 2」.

### 5. 비교에 걸린 시간이 「앞에서 몇 글자가 맞았나」를 흘린다

`==` 는 첫 번째로 다른 글자에서 바로 멈출 수 있어, 앞쪽이 많이 맞을수록 비교가 미세하게 오래 걸린다.
공격자는 응답 시간을 재 가며 값을 한 글자씩 맞혀 갈 수 있다(타이밍 공격).
`hmac.compare_digest` 는 어디가 다르든 걸리는 시간이 달라지지 않게 비교하도록 만들어져 이 정보를 흘리지 않는다.
근거: 2-summary 「동작 방식 (6)」「어디서 틀리나 3」.

### 6. 같은 계산을 다시 해야 맞춰 볼 수 있기 때문이다

해시는 되돌릴 수 없으므로 검증은 「입력한 비밀번호로 저장 때와 똑같은 계산을 다시 해서 결과를 비교」하는 방식뿐이다.
솔트가 다르거나 반복 횟수가 다르면 맞는 비밀번호라도 다른 키가 나온다.
그래서 `verify_password_pbkdf2` 는 `split('$')` 으로 반복 횟수와 솔트를 꺼내 같은 매개변수로 재계산한다.
반복 횟수를 함께 두면 나중에 기본값을 바꿔도 옛 저장값을 검증할 수 있다.
근거: 2-summary 「동작 방식 (4)」「어디서 틀리나 6」.

### 7. 「우연한 손상 확인」은 되고 「일부러 한 위조 방지」는 안 된다

MD5 는 충돌이 발견된 알고리즘이라, 공격자가 같은 해시를 내는 다른 데이터를 일부러 만들 수 있다.
그래서 비밀번호 저장 · 서명 · 위조 방지 같은 보안 용도에는 쓰지 않는다.
전송 중 깨졌는지 보는 체크섬처럼 상대가 공격자가 아닌 자리에서만 쓴다.
SHA-1 도 2017년 SHAttered 로 충돌 공격이 입증되어 같은 줄에 선다.
근거: 2-summary 「동작 방식 (1)」「어디서 틀리나 4」.

### 8. 통과하지 못한다 — 형식이 달라 언제나 거짓이 된다

받는 서명은 `sha256=` 머리를 단 꼴로 오므로, 머리 없는 `expected` 와 비교하면 내용이 맞아도 두 문자열이 다르다.
그래서 `verify_webhook_signature` 는 `f"sha256={expected}"` 로 형식을 똑같이 맞춘 뒤 `compare_digest` 로 비교한다.
근거: 2-summary 「동작 방식 (6)」「어디서 틀리나 7」.

### 9. 키가 없으면 고친 메시지의 맞는 서명을 만들 수 없다

그냥 해시는 누구나 계산할 수 있으므로, 중간에서 메시지를 고친 사람이 해시도 새로 계산해 바꿔 붙이면 받는 쪽은 알아채지 못한다.
HMAC 은 비밀키와 해시 함수를 엮어 계산하므로, 키를 모르는 사람은 고친 메시지에 맞는 값을 만들 수 없다.
그래서 HMAC 은 무결성(고쳐지지 않음)과 진위(키를 가진 쪽이 보냄)를 함께 확인한다.
근거: 2-summary 「동작 방식 (6)」.

### 10. 둘 다 예측할 수 없는 난수를 낸다

`os.urandom` 은 운영체제의 엔트로피 소스에서 안전한 무작위 바이트를 얻고, `secrets` 는 암호학적으로 안전한 난수 생성기(CSPRNG)를 쓴다(PEP 506).
솔트와 토큰은 공격자가 미리 알거나 예측하면 안 되는 값이므로 이런 생성기가 필요하다.
원본은 `secrets` 가 `random` 보다 안전하다고 적는다 — `random` 은 이런 보안 목적으로 쓰지 않는다.
근거: 2-summary 「동작 방식 (3)」「동작 방식 (7)」.

## 실습 정답

### 실습 1. 해시 · 비밀번호 · HMAC · 토큰을 한 파일로 정리하기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. 메시지를 UTF-8 bytes 로 | `message = "Hello, Python!".encode('utf-8')` |
| 2. 여섯 알고리즘 다이제스트 | `hashlib.md5` · `sha1` · `sha256` · `sha512`(`[:64]`) · `sha3_256` · `blake2b(..., digest_size=32)` 의 `.hexdigest()` |
| 3. 청크 단위 파일 해시 | `file_hash` — `hashlib.new(algorithm)`, `open(filepath, 'rb')`, `while chunk := f.read(chunk_size)`, `h.update(chunk)` |
| 4. 점진적 해시와 비교 | `h = hashlib.sha256()` + `h.update` 두 번, `h.hexdigest() == sha256_hash` |
| 5. 솔트 + SHA-256 | `hash_password_simple` — `os.urandom(32)`, `salt + password.encode('utf-8')`, `return salt.hex(), hashed` |
| 6. 솔트 되돌려 검증 | `bytes.fromhex(salt)`, `verify_hash == hashed` |
| 7. PBKDF2 저장 | `hash_password_pbkdf2` — `hashlib.pbkdf2_hmac('sha256', ..., iterations=iterations, dklen=32)`, `f"{iterations}${salt.hex()}${dk.hex()}"` |
| 8. PBKDF2 검증 | `verify_password_pbkdf2` — `stored.split('$')`, `int(iterations)`, `hmac.compare_digest(dk.hex(), hash_hex)` |
| 9. 저장값 · 두 검증 출력 | `stored[:50]`, `'secure_password'` · `'wrong_password'` 호출 |
| 10. bcrypt 안내 | 주석 처리된 `bcrypt.gensalt(rounds=12)` · `hashpw` · `checkpw` + `print` 네 줄 |
| 11. HMAC 계산 · 검증 | `hmac.new(secret_key, message, hashlib.sha256)`, `hmac.compare_digest(expected_mac, received_mac)` |
| 12. webhook 서명 검증 | `verify_webhook_signature` — `secret.encode()`, `payload.encode()`, `compare_digest(f"sha256={expected}", signature)` |
| 13. 보안 토큰 | `secrets.token_hex(32)` · `token_urlsafe(32)` · `token_bytes(16).hex()` · `randbelow(100)` |
| 14. 핵심 정리 | 마지막 `print` 여섯 줄 |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`python/python-advanced/reference/hashlib-security.py`

```python
# [고급 기법] hashlib (해시와 보안)
# 설명: hashlib, SHA-256, 솔트 해싱, PBKDF2, bcrypt 비밀번호 해싱
# 팁: 비밀번호는 반드시 솔트+반복 해싱(PBKDF2, bcrypt, scrypt) 사용. 단순 SHA-256은 비밀번호 저장에 부적합하다 (레인보우 테이블 공격). hmac.compare_digest()로 타이밍 공격을 방지한다. MD5는 보안 용도로 사용하지 않고 체크섬에만 사용한다.

# hashlib - 해시 함수와 비밀번호 보안

# hashlib: SHA, BLAKE 등 표준 해시 알고리즘과 PBKDF2 제공
import hashlib
# hmac: HMAC 메시지 인증 + compare_digest로 상수 시간 비교
import hmac
# os: urandom으로 암호학적 난수(엔트로피 풀에서) 생성
import os
# secrets: 토큰/난수 생성에 권장되는 안전한 모듈 (PEP 506)
import secrets
# binascii: hex/base 변환 (이 파일에서는 직접 사용 안 함)
import binascii


# === 1. 기본 해시 ===
print("=== 해시 함수 ===")
# 해시 입력은 bytes여야 함. encode('utf-8')로 str -> bytes 변환
message = "Hello, Python!".encode('utf-8')

# MD5: 128비트, 충돌 발견됨 -> 보안 부적합. 빠른 체크섬에만 사용
md5_hash = hashlib.md5(message).hexdigest()
print(f"MD5:     {md5_hash}")

# SHA-1: 160비트. 2017년 SHAttered로 충돌 공격 입증 -> 보안 부적합
sha1_hash = hashlib.sha1(message).hexdigest()
print(f"SHA-1:   {sha1_hash}")

# SHA-256: SHA-2 계열, 256비트. 일반 보안용도에 권장
sha256_hash = hashlib.sha256(message).hexdigest()
print(f"SHA-256: {sha256_hash}")

# SHA-512: SHA-2 계열, 512비트. 64비트 시스템에서 더 빠를 수 있음
sha512_hash = hashlib.sha512(message).hexdigest()
print(f"SHA-512: {sha512_hash[:64]}...")

# SHA-3: Keccak 기반, SHA-2와 다른 구조 (스폰지 함수)
sha3_hash = hashlib.sha3_256(message).hexdigest()
print(f"SHA3-256: {sha3_hash}")

# BLAKE2: 빠르면서 보안성 높음. digest_size로 출력 길이 조정
blake2_hash = hashlib.blake2b(message, digest_size=32).hexdigest()
print(f"BLAKE2b: {blake2_hash}")


# === 2. 파일 해시 (무결성 검증) ===
print("\n=== 파일 해시 ===")

# 함수 위 주석: 청크 단위로 읽어 메모리를 적게 쓰면서 큰 파일의 해시를 계산
def file_hash(filepath, algorithm='sha256', chunk_size=8192):
    """대용량 파일의 해시 계산 (메모리 효율적)"""
    # hashlib.new(name): 알고리즘 이름 문자열로 해시 객체 생성
    h = hashlib.new(algorithm)
    with open(filepath, 'rb') as f:
        # 워러스 연산자로 EOF까지 청크 읽기
        while chunk := f.read(chunk_size):
            # update(): 누적 해싱. 메시지를 분할 입력해도 결과 동일
            h.update(chunk)
    return h.hexdigest()

# 사용: checksum = file_hash('big_file.zip')

# 점진적 update와 일괄 해싱이 동일한 결과를 내는지 확인
h = hashlib.sha256()
h.update(b"Hello, ")
h.update(b"Python!")
print(f"점진적 해시: {h.hexdigest()}")
print(f"일괄 해시:   {sha256_hash}")
print(f"결과 동일:   {h.hexdigest() == sha256_hash}")


# === 3. 솔트 해싱 (비밀번호) ===
print("\n=== 솔트 해싱 ===")

# 함수 위 주석: 솔트와 SHA-256만 사용하는 기본 패턴 (실무엔 PBKDF2/bcrypt 권장)
def hash_password_simple(password, salt=None):
    """솔트 + SHA-256 (기본 수준)"""
    if salt is None:
        # os.urandom: 운영체제 엔트로피 소스로부터 안전한 랜덤 바이트 획득
        salt = os.urandom(32)  # 32바이트 랜덤 솔트
    # 솔트 + 비밀번호를 이어 해싱하여 레인보우 테이블 공격 무력화
    salted = salt + password.encode('utf-8')
    hashed = hashlib.sha256(salted).hexdigest()
    return salt.hex(), hashed

salt, hashed = hash_password_simple('mypassword123')
print(f"솔트: {salt}")
print(f"해시: {hashed}")

# 검증 시에는 저장된 솔트를 다시 사용해 동일한 절차로 재계산
salt_bytes = bytes.fromhex(salt)
_, verify_hash = hash_password_simple('mypassword123', salt_bytes)
print(f"검증: {verify_hash == hashed}")


# === 4. PBKDF2 (권장 비밀번호 해싱) ===
print("\n=== PBKDF2 ===")

# 함수 위 주석: PBKDF2-HMAC-SHA256로 키 스트레칭 -> brute-force 비용 증가
def hash_password_pbkdf2(password, salt=None, iterations=600000):
    """PBKDF2-HMAC-SHA256 (NIST 권장)"""
    if salt is None:
        salt = os.urandom(32)
    # pbkdf2_hmac: PRF=HMAC-SHA256으로 iterations회 반복 -> dklen 바이트 키 도출
    dk = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt,
        iterations=iterations,
        dklen=32
    )
    # 저장 형식 표준화: 알고리즘 파라미터를 함께 보관해야 검증 가능
    return f"{iterations}${salt.hex()}${dk.hex()}"

# 함수 위 주석: 저장된 형식을 분해해 동일 파라미터로 재계산 후 비교
def verify_password_pbkdf2(password, stored):
    """PBKDF2 비밀번호 검증"""
    iterations, salt_hex, hash_hex = stored.split('$')
    salt = bytes.fromhex(salt_hex)
    dk = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt,
        iterations=int(iterations),
        dklen=32
    )
    # compare_digest: 길이/바이트 차이를 상수 시간으로 비교 -> 타이밍 공격 방지
    return hmac.compare_digest(dk.hex(), hash_hex)  # 타이밍 공격 방지

stored = hash_password_pbkdf2('secure_password')
print(f"저장값: {stored[:50]}...")
print(f"검증 (맞는 비밀번호): {verify_password_pbkdf2('secure_password', stored)}")
print(f"검증 (틀린 비밀번호): {verify_password_pbkdf2('wrong_password', stored)}")


# === 5. bcrypt (전용 비밀번호 해시) ===
print("\n=== bcrypt 패턴 ===")
# bcrypt: Blowfish 기반 + cost factor (rounds)로 시간 비용 조절
# pip install bcrypt
# import bcrypt
#
# # 해싱
# password = 'secure_password'.encode('utf-8')
# salt = bcrypt.gensalt(rounds=12)  # cost factor (2^rounds 반복)
# hashed = bcrypt.hashpw(password, salt)
# print(f"bcrypt: {hashed}")
#
# # 검증 (해시 자체에 솔트가 포함되어 있음)
# is_valid = bcrypt.checkpw(password, hashed)
# print(f"검증: {is_valid}")

print("bcrypt.gensalt(rounds=12): 솔트 생성")
print("bcrypt.hashpw(password, salt): 해싱")
print("bcrypt.checkpw(password, hashed): 검증")
print("rounds=12는 약 0.25초 소요 (brute-force 방지)")


# === 6. HMAC (메시지 인증 코드) ===
print("\n=== HMAC ===")

# 비밀키와 해시 함수로 메시지의 무결성+진위 동시 검증
secret_key = b'my-secret-key-for-hmac'
message = b'중요한 메시지'

# hmac.new(key, msg, digestmod): HMAC-SHA256 계산
mac = hmac.new(secret_key, message, hashlib.sha256)
print(f"HMAC: {mac.hexdigest()}")

# 검증 측에서 동일 키로 재계산 후 compare_digest로 비교 (== 사용 금지)
expected_mac = mac.hexdigest()
received_mac = hmac.new(secret_key, message, hashlib.sha256).hexdigest()
is_valid = hmac.compare_digest(expected_mac, received_mac)
print(f"HMAC 검증: {is_valid}")

# 함수 위 주석: GitHub 같은 webhook 서명(X-Hub-Signature-256) 검증 패턴
def verify_webhook_signature(payload, signature, secret):
    expected = hmac.new(
        secret.encode(), payload.encode(), hashlib.sha256
    ).hexdigest()
    # 비교 시 prefix까지 포함해 정확히 동일한 형식으로 비교
    return hmac.compare_digest(f"sha256={expected}", signature)


# === 7. 보안 토큰 생성 ===
print("\n=== 보안 토큰 ===")
# secrets 모듈은 random보다 안전 (CSPRNG 사용)
print(f"토큰(hex):     {secrets.token_hex(32)}")
# token_urlsafe: URL-safe base64. 쿠키/링크에 적합
print(f"토큰(urlsafe): {secrets.token_urlsafe(32)}")
# token_bytes: 원시 바이트 시퀀스
print(f"토큰(bytes):   {secrets.token_bytes(16).hex()}")
# randbelow: 0 <= n < N 범위의 균등 정수
print(f"랜덤 숫자(0-99): {secrets.randbelow(100)}")
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

**실행 결과** — 실행하지 않음 — 예제 코드를 읽지 못했다(문법 오류) — 실행하지 않았다.

**풀이 요점**
- 해시 · PBKDF2 · HMAC 의 데이터 인자는 모두 `bytes` 라서 문자열은 `encode` 를 거친다.
- 솔트 · PBKDF2 검증은 「저장 때와 같은 매개변수로 다시 계산해 비교」라는 같은 꼴이다.
- 반복 횟수 · 솔트를 `$` 로 이어 보관해야 `verify_password_pbkdf2` 가 재계산할 수 있다.
- 비밀값 비교는 PBKDF2 · HMAC · webhook 모두 `hmac.compare_digest` 로 한다.
- 솔트 · 토큰처럼 예측되면 안 되는 값은 `os.urandom` · `secrets` 로 만든다 — 그래서 솔트 · 토큰 줄은 돌릴 때마다 달라진다.
- `binascii` 는 가져오기만 하고 쓰지 않는다 — 16진 변환은 `hex()` · `fromhex()` 가 맡는다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — 예제 코드를 읽지 못했다(문법 오류) — 실행하지 않았다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
