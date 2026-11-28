# python/python-security/01 — hashlib (해시 함수) — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 한 번에 넣은 해시와 두 번 나눠 넣은 해시 (예측)

```python
# 질문용 발췌
import hashlib
a = hashlib.sha256(b"Hello, World!").hexdigest()
h = hashlib.sha256()
h.update(b"Hello, ")
h.update(b"World!")
print(h.hexdigest() == a)
```

- 마지막 줄은 무엇을 찍는가?

### 2. 세 가지 결과의 글자 수 (예측)

```python
# 질문용 발췌
import hashlib, os
print(len(hashlib.sha256(b"x").hexdigest()))
print(len(hashlib.sha512(b"x").hexdigest()))
key = hashlib.pbkdf2_hmac("sha256", b"pw", os.urandom(32), 1000, dklen=32)
print(len(key.hex()))
```

- 세 줄은 각각 어떤 수를 찍는가?

### 3. 같은 비밀번호로 두 번 가입하면 (예측)

```python
# 질문용 발췌 — hash_password_simple · verify_password_simple 은 원본 그대로
s1, h1 = hash_password_simple("pw")
s2, h2 = hash_password_simple("pw")
print(h1 == h2)
print(verify_password_simple("pw", s1, h1))
```

- 두 줄은 각각 무엇을 찍는가?

### 4. 해시에 문자열 대신 바이트를 넣는 이유 (왜)

- `message.encode('utf-8')` 를 거쳐 넣고, 파일은 `'rb'` 로 여는 까닭은 무엇인가?

### 5. 파일을 청크 단위로 읽는 이유 (왜)

- `file_hash` 가 `f.read(chunk_size)` 를 반복하고도 통째로 읽은 것과 같은 해시를 얻을 수 있는 까닭은 무엇인가?

### 6. MD5 를 써도 되는 자리와 안 되는 자리 (경계)

- MD5 · SHA-1 을 허용하는 용도와 금지하는 용도의 경계는 어디인가?

### 7. 솔트를 붙인 SHA-256 은 왜 아직 부족한가 (왜)

- 솔트가 막아 주는 공격은 무엇이고, 솔트만으로 막지 못해 PBKDF2 가 필요한 까닭은 무엇인가?

### 8. 반복 횟수를 바꾸면 생기는 일 (경계)

- PBKDF2 의 반복 횟수를 올리면 무엇을 얻고 무엇을 잃으며, 검증 때 가입과 다른 반복 횟수를 넘기면 어떻게 되는가?

### 9. `hashlib.new` 와 `algorithms_guaranteed` 의 관계 (연결)

- `hashlib.new(algorithm)` 으로 알고리즘을 고르게 할 때 `algorithms_guaranteed` 는 어떤 구실을 하는가?

## 실습

### 실습 1. 해시 함수 종합 데모 만들기

**만들 것** — `hashlib` 으로 문자열 해시, 나눠 넣는 해시, 파일 해시, 솔트 비밀번호 해시, PBKDF2 해시를 차례로 만들고 결과를 출력하는 스크립트를 만든다.

**요구 조건**

1단계 — 기본 해시
1. `"Hello, World!"` 를 UTF-8 바이트로 바꿔 SHA-256 · SHA-512 · MD5 의 16진수 다이제스트를 만든다.
2. SHA-256 다이제스트 전체와 그 글자 수를 출력한다.
3. SHA-512 는 앞 40글자와 전체 글자 수를 출력한다.
4. MD5 는 보안 용도로 쓰지 말라는 표시와 함께 출력한다.

2단계 — 나눠 넣는 해시
5. 빈 SHA-256 객체에 `b"Hello, "` 와 `b"World!"` 를 차례로 `update` 한다.
6. 그 결과와, 그것이 1단계의 SHA-256 결과와 같은지(`True`/`False`)를 출력한다.

3단계 — 파일 해시
7. `file_hash(filepath, algorithm='sha256', chunk_size=8192)` 를 만든다 — 알고리즘 이름 문자열로 해시 객체를 만들고, 파일을 바이너리 모드로 열어 청크 단위로 읽어 넣은 뒤 16진수 다이제스트를 돌려준다.
8. 임시 텍스트 파일에 같은 줄을 100번 써 두고, 그 파일의 SHA-256 과 MD5 해시를 출력한 뒤 파일을 지운다.

4단계 — 솔트 해싱
9. `hash_password_simple(password, salt=None)` 을 만든다 — 솔트가 없으면 32바이트 안전 난수로 만들고, 솔트와 비밀번호 바이트를 이어 붙여 SHA-256 으로 해시해 `(salt, 해시)` 를 돌려준다.
10. `verify_password_simple(password, salt, expected_hash)` 를 만든다 — 같은 솔트로 다시 계산해 비교한 결과를 돌려준다.
11. 솔트(16진수) · 해시 · 맞는 비밀번호의 검증 결과 · 틀린 비밀번호(`'wrong'`)의 검증 결과를 출력한다.

5단계 — PBKDF2
12. `hash_password_pbkdf2(password, salt=None, iterations=600_000)` 을 만든다 — 솔트가 없으면 32바이트 난수로 만들고, `pbkdf2_hmac` 을 SHA-256 · 키 길이 32바이트로 불러 `(salt, 키의 16진수, iterations)` 를 돌려준다.
13. `verify_pbkdf2(password, salt, expected_hex, iterations)` 를 만든다 — 같은 솔트 · 같은 반복 횟수로 다시 계산해 비교한다.
14. 솔트 앞 32글자 · 키 · 천 단위 쉼표가 붙은 반복 횟수 · 검증 결과를 출력한다.

6단계 — 알고리즘 목록과 가이드
15. 모든 플랫폼에서 보장되는 알고리즘 이름을 정렬해 출력한다.
16. 용도별 알고리즘 선택 가이드 네 줄을 출력한다.

**시작 코드**

```python
import hashlib
import os
import tempfile

# === 기본 해시 생성 ===
print("=== 기본 해시 ===")
message = "Hello, World!"

sha256 = None  # TODO: message 를 UTF-8 바이트로 바꿔 SHA-256 hex 다이제스트
print(f"SHA-256: {sha256}")
print(f"  길이:  {len(sha256)}자 (256비트 = 64 hex)")

sha512 = None  # TODO: SHA-512 hex 다이제스트
print(f"SHA-512: {sha512[:40]}... ({len(sha512)}자)")

md5 = None  # TODO: MD5 hex 다이제스트
print(f"MD5:     {md5} (보안 용도 사용 금지)")
print()

# === 단계별 해시 (update) ===
print("=== 단계별 해시 (스트리밍) ===")
h = None  # TODO: 빈 SHA-256 객체
# TODO: b"Hello, " 와 b"World!" 를 차례로 넣기
result = None  # TODO: 누적 입력의 hex 다이제스트
print(f"update 방식: {result}")
print(f"일괄 방식과 동일: {result == sha256}")
print()

# === 파일 해시 (대용량 파일 지원) ===
print("=== 파일 해시 ===")

def file_hash(filepath, algorithm='sha256', chunk_size=8192):
    """파일의 해시 값을 계산 (대용량 파일도 메모리 효율적)"""
    # TODO: 알고리즘 이름으로 해시 객체 만들기
    # TODO: 바이너리 모드로 열어 chunk_size 씩 읽어 update, 빈 청크면 멈추기
    # TODO: hex 다이제스트 돌려주기
    pass

with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
    f.write("테스트 파일 내용입니다.\n" * 100)
    temp_path = f.name

hash_value = file_hash(temp_path)
print(f"파일 해시 (SHA-256): {hash_value}")
print(f"파일 해시 (MD5):     {file_hash(temp_path, 'md5')}")
os.unlink(temp_path)
print()

# === 솔트 해싱 (비밀번호) ===
print("=== 솔트 해싱 ===")

def hash_password_simple(password, salt=None):
    """솔트 + SHA-256 (기본 예시, 실무에서는 bcrypt/scrypt 사용)"""
    # TODO: 솔트가 없으면 32바이트 안전 난수로 만들기
    # TODO: 솔트 + 비밀번호 바이트를 SHA-256 으로 해시
    # TODO: (salt, hex 다이제스트) 돌려주기
    pass

def verify_password_simple(password, salt, expected_hash):
    # TODO: 같은 솔트로 다시 계산해 비교
    pass

password = "my_secure_password"
salt, hashed = hash_password_simple(password)
print(f"솔트:   {salt.hex()}")
print(f"해시:   {hashed}")
print(f"검증:   {verify_password_simple(password, salt, hashed)}")
print(f"오답:   {verify_password_simple('wrong', salt, hashed)}")
print()

# === pbkdf2_hmac (권장 해시) ===
print("=== PBKDF2 (강력한 비밀번호 해시) ===")

def hash_password_pbkdf2(password, salt=None, iterations=600_000):
    """PBKDF2-HMAC-SHA256"""
    # TODO: 솔트가 없으면 32바이트 난수
    # TODO: pbkdf2_hmac 호출 (sha256, 비밀번호 바이트, 솔트, 반복 횟수, 키 길이 32)
    # TODO: (salt, 키의 hex, iterations) 돌려주기
    pass

def verify_pbkdf2(password, salt, expected_hex, iterations):
    # TODO: 같은 솔트 · 같은 반복 횟수로 다시 계산해 비교
    pass

salt, key_hex, iters = hash_password_pbkdf2("my_password")
print(f"솔트:      {salt.hex()[:32]}...")
print(f"PBKDF2:    {key_hex}")
print(f"반복 횟수:  {iters:,}")
print(f"검증:      {verify_pbkdf2('my_password', salt, key_hex, iters)}")
print()

# === 사용 가능한 알고리즘 ===
print("=== 사용 가능한 알고리즘 ===")
# TODO: 모든 플랫폼에서 보장되는 알고리즘 이름을 정렬해 출력
print()

print("--- 해시 알고리즘 선택 가이드 ---")
print("비밀번호: bcrypt, scrypt, argon2 (또는 PBKDF2)")
print("데이터 무결성: SHA-256, SHA-3")
print("파일 체크섬: SHA-256 (빠른 확인: MD5, SHA-1)")
print("절대 사용 금지: MD5, SHA-1 (보안 목적)")
```

**확인 방법** — `python hashlib-basics.py` 로 돌려, 「일괄 방식과 동일」 줄이 `True` 인지, 솔트 해싱의 「검증」이 `True` 이고 「오답」이 `False` 인지, PBKDF2 의 「검증」이 `True` 인지 본다.
두 번 돌려 솔트 · 솔트 해시 · PBKDF2 키는 바뀌고 기본 해시 · 파일 해시는 그대로인지도 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
