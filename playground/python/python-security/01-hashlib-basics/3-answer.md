# python/python-security/01 — hashlib (해시 함수) — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. `True` — 나눠 넣어도 이어 붙인 입력이 같으면 해시가 같다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
`True` 를 찍는다.

**왜 그런가**
`update()` 는 부를 때마다 입력을 이어 붙이고, `hexdigest()` 는 누적된 입력 전체의 다이제스트를 낸다.
`b"Hello, "` 와 `b"World!"` 를 이어 붙이면 `b"Hello, World!"` 이므로 일괄 방식과 같은 입력을 해시한 셈이다.
근거: 2-summary 「동작 방식 (2)」.

### 2. 64 · 128 · 64

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
첫 줄 `64`, 둘째 줄 `128`, 셋째 줄 `64` 를 찍는다.

**왜 그런가**
16진수 한 글자는 4비트다.
SHA-256 은 256비트이므로 256 ÷ 4 = 64글자다.
SHA-512 는 512비트이므로 128글자다.
PBKDF2 는 `dklen=32` 로 32바이트 키를 만들고, `.hex()` 는 바이트 하나를 두 글자로 바꾸므로 64글자다.
입력 `b"x"` 의 길이는 결과 길이와 상관없다.
근거: 2-summary 「동작 방식 (1)」 · 「동작 방식 (5)」 · 「문법 — 형태와 규칙」의 표.

### 3. `False` 다음 `True` — 솔트가 달라 해시가 다르고, 검증은 저장된 솔트로 맞는다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
첫 줄은 `False`, 둘째 줄은 `True` 를 찍는다.

**왜 그런가**
`salt` 를 넘기지 않았으므로 두 호출은 각각 `os.urandom(32)` 로 새 솔트를 만든다.
솔트가 다르면 해시하는 바이트(`salt + password`)가 달라지므로 해시도 달라진다.
32바이트 난수 두 개가 같게 나올 가능성은 무시할 만큼 작다 (원본에 근거 없음 — 추론).
`verify_password_simple("pw", s1, h1)` 은 저장된 솔트 `s1` 로 같은 계산을 다시 하므로 `h1` 과 같은 값이 나와 `True` 다.
근거: 2-summary 「동작 방식 (4)」.

### 4. 해시 함수는 바이트를 받고, 바이트가 같아야 해시가 같기 때문이다

해시 함수는 바이트 입력을 받으므로 문자열은 `encode('utf-8')` 로 바이트로 바꿔야 한다.
같은 글자라도 인코딩이 다르면 바이트가 달라지고, 바이트가 달라지면 해시도 달라진다.
파일을 `'rb'` 로 여는 것도 같은 까닭이다 — 텍스트 모드의 인코딩 처리가 바이트를 바꾸지 못하게, 파일에 적힌 바이트를 그대로 해시한다.
근거: 2-summary 「동작 방식 (1)」 · 「동작 방식 (3)」 · 「어디서 틀리나 5」.

### 5. 메모리를 청크 하나 크기로 묶어 두기 위해서이고, `update` 가 누적되므로 결과가 같다

통째로 읽으면 파일 크기만큼 메모리를 쓰지만, 청크로 읽으면 한 번에 청크 하나만 메모리에 올라가 사용량이 일정하다.
`update()` 는 입력을 이어 붙이므로 청크를 차례로 넣으면 결국 파일 전체 바이트를 넣은 것과 같다.
그래서 나눠 읽어도 일괄 해시와 같은 다이제스트를 얻는다.
근거: 2-summary 「동작 방식 (2)」 · 「동작 방식 (3)」 · 「어디서 틀리나 3」.

### 6. 보안이 걸리면 금지, 보안과 무관한 단순 비교면 허용

MD5 · SHA-1 은 충돌이 발견되었다.
그래서 디지털 서명 · 비밀번호처럼 보안이 걸린 용도에는 쓰지 않는다.
보안과 상관없이 파일이 같은지 빠르게 확인하는 체크섬에는 원본도 MD5 · SHA-1 을 허용한다.
언어는 `hashlib.md5()` 호출을 막지 않으므로 이 경계는 쓰는 사람이 지켜야 한다.
근거: 2-summary 「동작 방식 (6)」 · 「어디서 틀리나 1」 · 「구현 세부사항 대 언어 보장」.

### 7. 솔트는 미리 계산한 표를 막지만, 빠른 해시의 무차별 대입은 막지 못한다

솔트를 붙이면 같은 비밀번호라도 사용자마다 해시가 달라진다.
그래서 흔한 비밀번호의 해시를 미리 계산해 둔 레인보우 테이블이나 사전 공격이 그대로 통하지 않는다.
그러나 솔트는 해시와 함께 저장되므로, 공격자는 솔트를 알고 후보 비밀번호를 하나씩 넣어 볼 수 있다.
SHA-256 한 번은 빠르므로 이 무차별 대입도 빠르다.
PBKDF2 는 HMAC 해시를 수십만 번 반복해 후보 하나를 시험하는 비용을 키운다.
근거: 2-summary 「동작 방식 (4)」 · 「동작 방식 (5)」 · 「어디서 틀리나 2」.

### 8. 안전성은 오르고 속도는 떨어지며, 반복 횟수가 다르면 검증이 실패한다

반복 횟수를 올리면 한 번 계산하는 비용이 커져 무차별 대입이 비싸진다 — 원본의 말로 「높을수록 안전, 느림」이다.
대가는 정당한 로그인 검증도 그만큼 느려진다는 것이다.
반복 횟수가 다르면 만들어지는 키가 달라지므로, 맞는 비밀번호를 넣어도 비교가 `False` 가 된다.
그래서 원본의 `hash_password_pbkdf2` 는 반복 횟수까지 돌려주고, 검증은 저장된 반복 횟수를 넘겨 다시 계산한다.
근거: 2-summary 「동작 방식 (5)」 · 「어디서 틀리나 6」.

### 9. `new` 는 이름으로 고르는 문이고, `algorithms_guaranteed` 는 어디서나 통하는 이름의 목록이다

`hashlib.new(algorithm)` 은 알고리즘 이름 문자열을 받아 해시 객체를 만든다 — 그래서 `file_hash(path, 'md5')` 처럼 인자로 알고리즘을 바꿀 수 있다.
`hashlib.algorithms_guaranteed` 는 모든 플랫폼에서 쓸 수 있다고 보장된 이름의 집합이다.
이 집합 안의 이름을 `new` 에 넘기면 어느 환경에서 돌려도 알고리즘이 있다고 기대할 수 있다.
집합이라 순서가 없으므로 원본은 `sorted()` 로 정렬해 보여 준다.
근거: 2-summary 「동작 방식 (3)」 · 「동작 방식 (6)」 · 「구현 세부사항 대 언어 보장」.

## 실습 정답

### 실습 1. 해시 함수 종합 데모 만들기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. 세 알고리즘의 hex 다이제스트 | `hashlib.sha256(message.encode('utf-8')).hexdigest()` · `hashlib.sha512(...)` · `hashlib.md5(...)` |
| 2. SHA-256 전체와 글자 수 | `print(f"SHA-256: {sha256}")` · `len(sha256)` |
| 3. SHA-512 앞 40글자와 글자 수 | `sha512[:40]` · `len(sha512)` |
| 4. MD5 와 경고 표시 | `print(f"MD5:     {md5} (보안 용도 사용 금지)")` |
| 5. 빈 객체에 두 번 `update` | `h = hashlib.sha256()` · `h.update(b"Hello, ")` · `h.update(b"World!")` |
| 6. 결과와 일괄 방식 비교 | `result = h.hexdigest()` · `result == sha256` |
| 7. `file_hash` | `hashlib.new(algorithm)` · `open(filepath, 'rb')` · `f.read(chunk_size)` · `if not chunk: break` · `h.update(chunk)` |
| 8. 임시 파일 해시 후 삭제 | `tempfile.NamedTemporaryFile(..., delete=False)` · `file_hash(temp_path)` · `file_hash(temp_path, 'md5')` · `os.unlink(temp_path)` |
| 9. `hash_password_simple` | `salt = os.urandom(32)` · `hashlib.sha256(salt + password.encode('utf-8'))` · `return salt, h.hexdigest()` |
| 10. `verify_password_simple` | `hash_password_simple(password, salt)` · `computed_hash == expected_hash` |
| 11. 솔트 · 해시 · 검증 두 번 출력 | `salt.hex()` · `verify_password_simple(password, ...)` · `verify_password_simple('wrong', ...)` |
| 12. `hash_password_pbkdf2` | `hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, iterations, dklen=32)` · `return salt, key.hex(), iterations` |
| 13. `verify_pbkdf2` | `hash_password_pbkdf2(password, salt, iterations)` · `computed_hex == expected_hex` |
| 14. PBKDF2 결과 출력 | `salt.hex()[:32]` · `{iters:,}` · `verify_pbkdf2('my_password', salt, key_hex, iters)` |
| 15. 보장된 알고리즘 목록 | `sorted(hashlib.algorithms_guaranteed)` |
| 16. 선택 가이드 네 줄 | `print("비밀번호: …")` 부터 `print("절대 사용 금지: …")` 까지 |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`python/python-security/reference/hashlib-basics.py`

```python
# [보안 & 암호화] hashlib (해시 함수)
# 설명: hashlib로 SHA-256, SHA-512, MD5 해시를 생성하고 파일 해시 검증, 솔트 해싱을 수행
# 팁: MD5와 SHA-1은 충돌이 발견되어 보안 용도로 사용하면 안 된다. 비밀번호는 반드시 솔트와 함께 해시하고, PBKDF2/bcrypt/scrypt 같은 느린 해시를 사용한다. 파일 해시는 청크 단위로 읽어 메모리 효율을 유지한다. hashlib.new(algorithm)으로 동적으로 알고리즘을 선택할 수 있다.

# hashlib: 표준 해시 함수 모음 (SHA-2/3, MD5, PBKDF2 등)
import hashlib
# os: 솔트용 안전 난수 생성(os.urandom) 제공
import os
# tempfile: 파일 해싱 예제용 임시 파일
import tempfile

# === 기본 해시 생성 ===
print("=== 기본 해시 ===")
message = "Hello, World!"

# SHA-256
# encode: 문자열 → 바이트 (해시는 바이트 입력 필요)
# hexdigest: 16진수 문자열로 결과 반환
sha256 = hashlib.sha256(message.encode('utf-8')).hexdigest()
print(f"SHA-256: {sha256}")
print(f"  길이:  {len(sha256)}자 (256비트 = 64 hex)")

# SHA-512
# 512비트 출력 → 더 긴 다이제스트, 더 높은 충돌 저항
sha512 = hashlib.sha512(message.encode('utf-8')).hexdigest()
print(f"SHA-512: {sha512[:40]}... ({len(sha512)}자)")

# MD5 (보안 용도로 사용 금지! 파일 체크섬 용도로만)
# 충돌 공격 발견 → 디지털 서명/비밀번호 등 보안 목적 사용 금지
md5 = hashlib.md5(message.encode('utf-8')).hexdigest()
print(f"MD5:     {md5} (보안 용도 사용 금지)")
print()

# === 단계별 해시 (update) ===
print("=== 단계별 해시 (스트리밍) ===")
# 빈 해시 객체 생성
h = hashlib.sha256()
# 데이터 일부 추가
h.update(b"Hello, ")
h.update(b"World!")  # 여러 번 update 가능
# 누적된 입력 전체에 대한 해시 산출
result = h.hexdigest()
print(f"update 방식: {result}")
# 일괄 입력과 동일한 결과 → 대용량 스트림 해싱에 유리
print(f"일괄 방식과 동일: {result == sha256}")
print()

# === 파일 해시 (대용량 파일 지원) ===
print("=== 파일 해시 ===")

# 대용량 파일도 OOM 없이 해싱하는 표준 패턴
def file_hash(filepath, algorithm='sha256', chunk_size=8192):
    """파일의 해시 값을 계산 (대용량 파일도 메모리 효율적)"""
    # hashlib.new: 알고리즘명 문자열로 동적 선택
    h = hashlib.new(algorithm)
    # 바이너리 읽기 모드 (텍스트 인코딩 영향 제거)
    with open(filepath, 'rb') as f:
        while True:
            # 청크 단위로 읽어 메모리 사용량 일정 유지
            chunk = f.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()

# 테스트 파일 생성
with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
    # 일정 패턴 데이터 작성
    f.write("테스트 파일 내용입니다.\n" * 100)
    temp_path = f.name

# 무결성 검증용 해시 산출
hash_value = file_hash(temp_path)
print(f"파일 해시 (SHA-256): {hash_value}")
# MD5는 빠른 비교 용도로만 (보안 X)
print(f"파일 해시 (MD5):     {file_hash(temp_path, 'md5')}")
# 임시 파일 정리
os.unlink(temp_path)
print()

# === 솔트 해싱 (비밀번호) ===
print("=== 솔트 해싱 ===")

# 단순 SHA-256 + 솔트 (학습용; 실무는 bcrypt/argon2 권장)
def hash_password_simple(password, salt=None):
    """솔트 + SHA-256 (기본 예시, 실무에서는 bcrypt/scrypt 사용)"""
    if salt is None:
        # urandom: OS의 CSPRNG → 예측 불가능한 솔트
        salt = os.urandom(32)  # 32바이트 랜덤 솔트
    # 솔트 + 비밀번호를 결합하여 해시
    # 솔트는 레인보우 테이블/사전 공격 무력화에 필수
    h = hashlib.sha256(salt + password.encode('utf-8'))
    return salt, h.hexdigest()

# 검증: 동일 솔트로 재계산 후 비교
def verify_password_simple(password, salt, expected_hash):
    _, computed_hash = hash_password_simple(password, salt)
    return computed_hash == expected_hash

password = "my_secure_password"
# 가입 시: 솔트와 해시를 모두 저장
salt, hashed = hash_password_simple(password)
print(f"솔트:   {salt.hex()}")
print(f"해시:   {hashed}")
# 정상 검증
print(f"검증:   {verify_password_simple(password, salt, hashed)}")
# 잘못된 비밀번호
print(f"오답:   {verify_password_simple('wrong', salt, hashed)}")
print()

# === pbkdf2_hmac (권장 해시) ===
print("=== PBKDF2 (강력한 비밀번호 해시) ===")

# PBKDF2: 반복 횟수만큼 HMAC 해시를 적용 → 무차별 대입 비용 증가
def hash_password_pbkdf2(password, salt=None, iterations=600_000):
    """PBKDF2-HMAC-SHA256 (NIST 권장)"""
    if salt is None:
        salt = os.urandom(32)
    # pbkdf2_hmac: 표준 키 유도 함수 (NIST SP 800-132)
    key = hashlib.pbkdf2_hmac(
        'sha256',                          # 해시 알고리즘
        password.encode('utf-8'),          # 비밀번호
        salt,                              # 솔트
        iterations,                        # 반복 횟수 (높을수록 안전, 느림)
        dklen=32                           # 키 길이
    )
    return salt, key.hex(), iterations

# 검증: 동일 파라미터로 재계산
def verify_pbkdf2(password, salt, expected_hex, iterations):
    _, computed_hex, _ = hash_password_pbkdf2(password, salt, iterations)
    return computed_hex == expected_hex

# 60만 회 반복 (2024 NIST 가이드)
salt, key_hex, iters = hash_password_pbkdf2("my_password")
print(f"솔트:      {salt.hex()[:32]}...")
print(f"PBKDF2:    {key_hex}")
print(f"반복 횟수:  {iters:,}")
print(f"검증:      {verify_pbkdf2('my_password', salt, key_hex, iters)}")
print()

# === 사용 가능한 알고리즘 ===
print("=== 사용 가능한 알고리즘 ===")
# 모든 플랫폼에서 보장되는 알고리즘 목록
print(f"보장됨:  {sorted(hashlib.algorithms_guaranteed)}")
print()

# 용도별 알고리즘 선택 가이드
print("--- 해시 알고리즘 선택 가이드 ---")
# 비밀번호: 느린 해시 함수 사용 (GPU 공격 방어)
print("비밀번호: bcrypt, scrypt, argon2 (또는 PBKDF2)")
# 데이터 무결성: SHA-256 표준
print("데이터 무결성: SHA-256, SHA-3")
# 파일 체크섬: 보안 X 단순 비교는 MD5/SHA-1도 허용
print("파일 체크섬: SHA-256 (빠른 확인: MD5, SHA-1)")
# 보안 컨텍스트에서는 절대 금지
print("절대 사용 금지: MD5, SHA-1 (보안 목적)")

# 출력:
# === 기본 해시 ===
# SHA-256: dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f
# SHA-512: 374d794a95cdcfd8b35993185fef9ba368f160d8daf432d08ba9f1ed1e5abe6c...
# MD5: 65a8e27d8879283831b664bd8b7f0ad4
# === PBKDF2 ===
# 반복 횟수: 600,000
```

**실행 결과** — 실행하지 않음 — 돌릴 때마다 출력이 달라지는 예제다 — 출력을 싣지 않았다.

**풀이 요점**

- 해시에 넣는 것은 언제나 바이트다 — 문자열은 `encode('utf-8')`, 파일은 `'rb'`.
- `update` 는 누적되므로 2단계의 결과는 1단계의 SHA-256 과 같아야 하고, 3단계의 청크 읽기도 이 성질에 기댄다.
- `hashlib.new(algorithm)` 덕분에 `file_hash` 하나로 SHA-256 과 MD5 를 모두 계산한다.
- 솔트를 새로 만들 때마다 솔트 해시 · PBKDF2 키는 실행마다 달라지고, 기본 해시 · 파일 해시는 입력이 같으므로 그대로다.
- 검증 함수는 「저장된 솔트(와 반복 횟수)로 다시 계산해 비교」라는 같은 꼴이다.
- 원본 끝의 `# 출력:` 주석은 실제 `print` 모양과 다르고 일부만 적혀 있으니 정답 출력으로 믿지 않는다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — 돌릴 때마다 출력이 달라지는 예제다 — 출력을 싣지 않았다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
