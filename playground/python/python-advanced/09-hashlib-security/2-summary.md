# python/python-advanced/09 — hashlib (해시와 보안) — 정리 (힌트)

> 출처 — study-site 항목 `python/hashlib-security`(항목 데이터 `data/python/advanced-techniques.json`) · 정답 코드 study-practice `python/python-advanced/reference/hashlib-security.py`\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).\
> 실행 — 실행하지 않음 — 예제 코드를 읽지 못했다(문법 오류) — 실행하지 않았다.

## 한눈에 — 쉽게 말하면

**해시는 「문서를 넣으면 지문 한 장이 나오는 기계」다.**
같은 문서를 넣으면 언제나 같은 지문이 나오고, 글자 하나만 바꿔도 전혀 다른 지문이 나온다.
지문만 보고 원래 문서를 되살릴 수는 없다.
비밀번호 보관도 똑같은 구조다.
서버는 비밀번호 대신 지문을 보관하고, 로그인 때 입력값의 지문을 다시 떠서 맞춰 본다.
여기에 두 가지를 더한다.
사람마다 다른 **소금(솔트)** 을 섞어 같은 비밀번호도 다른 지문이 되게 하고, 지문 뜨는 일을 **수십만 번 반복**해 위조범이 한 번 시도하는 데 드는 비용을 키운다.

| 비유 | 실체 |
|---|---|
| 지문 기계 | 해시 함수(`hashlib.sha256` 등) |
| 지문 한 장 | 다이제스트(`hexdigest()` 결과) |
| 사람마다 다른 소금 | 솔트(`os.urandom(32)`) |
| 지문을 수십만 번 다시 뜨기 | 키 스트레칭(`pbkdf2_hmac` 의 `iterations`) |
| 도장 찍힌 봉투 | HMAC(비밀키로 만든 서명) |
| 지문 대조를 늘 같은 속도로 하기 | `hmac.compare_digest` |

```text
 "Hello, Python!"            비밀번호 + 솔트
        │                          │
   encode('utf-8')           pbkdf2_hmac × 600000
        │                          │
     bytes ──► sha256 ──► 64글자 16진 지문     "600000$솔트hex$해시hex" 로 보관
```

> **해시 함수** — 임의 길이의 바이트를 받아 정해진 길이의 값을 내는 함수.\
> 예: `hashlib.sha256(b"abc").hexdigest()` 는 늘 64글자 16진 문자열이다.

## 이 주제가 답하려는 질문

1. 바이트 덩어리(문자열 · 큰 파일)의 지문을 `hashlib` 으로 어떻게 뜨고, 알고리즘마다 무엇이 다른가?
2. 비밀번호는 왜 해시 한 번으로 저장하면 안 되고, 솔트와 반복(PBKDF2 · bcrypt)을 어떻게 붙이나?
3. 「이 메시지는 키를 가진 사람이 보냈고 고쳐지지 않았다」를 HMAC 으로 어떻게 확인하나?
4. 비교 · 토큰 생성처럼 보안 코드의 작은 부분은 무엇으로 해야 안전한가?

## 동작 방식

### (1) 기본 해시 — 바이트를 넣고 다이제스트를 꺼낸다

**언제 쓰나** — 데이터의 고정 길이 지문이 필요할 때 쓴다.
알고리즘 이름이 곧 생성자 함수다.

```text
"Hello, Python!"
   │ .encode('utf-8')          ← 해시는 bytes 만 받는다
   ▼
b'Hello, Python!'
   │ hashlib.sha256(...)       ← 해시 객체
   ▼
.hexdigest()                    ← 16진 문자열
   ▼
64글자 문자열 (256비트 ÷ 4비트/글자)
```

- 해시 입력은 `bytes` 여야 하므로 `str` 은 `encode('utf-8')` 로 바꾼다.
- 생성자에 넣으면 해시 객체가 나오고, `hexdigest()` 가 그 결과를 16진 문자열로 준다.
- 16진 한 글자는 4비트이므로 글자 수는 비트 수의 4분의 1이다.

원본이 다룬 알고리즘은 다음과 같다.

| 생성자 | 출력 크기 | 원본의 평가 |
|---|---|---|
| `hashlib.md5` | 128비트 | 충돌이 발견됨 → 보안 부적합, 체크섬에만 |
| `hashlib.sha1` | 160비트 | 2017년 SHAttered 로 충돌 공격 입증 → 보안 부적합 |
| `hashlib.sha256` | 256비트 | SHA-2 계열, 일반 보안 용도에 권장 |
| `hashlib.sha512` | 512비트 | SHA-2 계열, 64비트 시스템에서 더 빠를 수 있음 |
| `hashlib.sha3_256` | 256비트 | Keccak 기반, SHA-2 와 다른 구조(스폰지 함수) |
| `hashlib.blake2b(..., digest_size=32)` | `digest_size` 로 조정(여기선 32바이트) | 빠르면서 보안성 높음 |

예제는 SHA-512 결과가 길어서 `sha512_hash[:64]` 로 앞 64글자만 찍고 `...` 을 붙인다.

> **다이제스트** — 해시 함수가 내놓은 결과값.\
> 예: `digest()` 는 `bytes` 로, `hexdigest()` 는 16진 `str` 로 준다.

> **충돌** — 서로 다른 두 입력이 같은 해시를 내는 일.\
> 예: MD5 · SHA-1 은 일부러 충돌을 만드는 방법이 알려져 보안 용도에서 빠졌다.

### (2) 점진적 `update` — 큰 파일을 조각내 해싱

**언제 쓰나** — 파일이 커서 한꺼번에 메모리에 올리기 싫을 때 쓴다.

```text
h = hashlib.sha256()          빈 해시 객체
h.update(b"Hello, ")          ┐
h.update(b"Python!")          ┘ 이어 붙인 것과 같다
h.hexdigest()  ==  hashlib.sha256(b"Hello, Python!").hexdigest()
```

- `update()` 는 지금까지 넣은 바이트 뒤에 새 바이트를 잇는 누적 해싱이다.
- 그래서 메시지를 몇 조각으로 나눠 넣든 순서만 같으면 결과는 한 번에 넣은 것과 같다.
- 예제의 `file_hash` 는 이것을 이용해 파일을 `'rb'`(바이트 읽기)로 열고 `chunk_size`(기본 8192바이트)씩 읽어 `update` 한다.
- `while chunk := f.read(chunk_size):` 는 워러스 연산자로 읽은 값을 담고, 빈 바이트(EOF)가 나오면 거짓이 되어 멈춘다.
- `hashlib.new(algorithm)` 은 `'sha256'` 같은 이름 문자열로 해시 객체를 만든다 — 알고리즘을 인자로 고를 수 있다.

> **체크섬** — 데이터가 전송 · 보관 중 깨지지 않았는지 확인하려고 뜨는 값.\
> 예: 내려받은 `big_file.zip` 의 SHA-256 을 배포처가 알린 값과 비교한다.

### (3) 솔트 해싱 — 같은 비밀번호도 다른 해시로

**언제 쓰나** — 비밀번호 해시가 사용자끼리 겹치지 않게 하고, 미리 계산한 표를 쓸모없게 만들 때다.

```text
salt = os.urandom(32)                     32바이트 무작위
salted = salt + password.encode('utf-8')  솔트를 앞에 붙임
hashed = sha256(salted).hexdigest()
보관: (salt.hex(), hashed)

검증: bytes.fromhex(저장된 솔트) → 같은 절차로 재계산 → 저장된 해시와 같은가?
```

- `salt` 를 넘기지 않으면 `os.urandom(32)` 로 운영체제의 안전한 난수 32바이트를 만든다.
- 솔트를 비밀번호 앞에 이어 SHA-256 을 뜨고, 솔트는 `hex()` 로 문자열로 바꿔 해시와 함께 돌려준다.
- 솔트는 호출마다 새로 뽑히므로, 같은 비밀번호를 두 번 저장해도 해시가 다르다.
- 검증 때는 저장된 솔트를 `bytes.fromhex` 로 되돌려 넘긴다 — 같은 솔트 · 같은 비밀번호면 같은 해시가 나온다.
- 솔트는 비밀이 아니다. 해시 옆에 그대로 보관한다.

> **레인보우 테이블** — 흔한 비밀번호들의 해시를 미리 계산해 둔 거대한 조회표.\
> 예: 솔트 없는 SHA-256 해시가 새면 표에서 찾아 원래 비밀번호를 곧바로 알아낸다.

이 패턴은 레인보우 테이블은 무력화하지만 SHA-256 한 번은 계산이 빠르다.
솔트를 아는 공격자가 한 계정을 노려 후보 비밀번호를 하나씩 넣어 보는 것(무차별 대입)은 여전히 빠르다.
원본도 이것을 「기본 수준」이라 부르고 실무엔 PBKDF2 · bcrypt 를 권한다.

### (4) PBKDF2 — 반복으로 일부러 느리게

**언제 쓰나** — 표준 라이브러리만으로 비밀번호를 저장할 때 쓴다.

```text
pbkdf2_hmac('sha256', 비밀번호bytes, salt, iterations=600000, dklen=32)
   │  HMAC-SHA256 을 600000번 반복
   ▼
dk (32바이트 키)
   ▼
보관 문자열: f"{iterations}${salt.hex()}${dk.hex()}"
            "600000$<솔트 64글자>$<해시 64글자>"

검증: stored.split('$') → 세 조각 → 같은 iterations·솔트로 재계산
      → hmac.compare_digest(dk.hex(), hash_hex)
```

- `pbkdf2_hmac` 은 HMAC-SHA256 을 `iterations` 번 반복해 `dklen` 바이트 길이의 키를 뽑는다.
- 반복이 많을수록 한 번 시도의 비용이 커져 무차별 대입이 느려진다(키 스트레칭).
- 반복 횟수 · 솔트를 결과와 함께 보관해야 나중에 같은 계산을 재현할 수 있다 — 그래서 `$` 로 이어 붙인다.
- 검증 함수는 `split('$')` 으로 세 조각을 나누고, 반복 횟수는 `int()` 로 되돌린다.
- 마지막 비교는 `==` 가 아니라 `hmac.compare_digest` 로 한다.
- 예제는 `stored[:50]` 만 찍는다 — 앞부분은 `600000$` 과 솔트 16진 문자열이다.

> **키 스트레칭** — 해시를 많이 반복해 계산을 일부러 느리게 만드는 기법.\
> 예: 600000번 반복하면 공격자도 후보 하나마다 600000번을 계산해야 한다.

### (5) bcrypt — 비밀번호 전용 해시

**언제 쓰나** — 외부 패키지를 써도 될 때, 솔트 관리까지 맡기고 싶을 때다.

```text
salt   = bcrypt.gensalt(rounds=12)      cost factor → 2^12 번 반복
hashed = bcrypt.hashpw(password, salt)  솔트가 해시 문자열 안에 들어감
ok     = bcrypt.checkpw(password, hashed)  해시에서 솔트를 꺼내 재계산·비교
```

- `pip install bcrypt` 로 설치하는 외부 패키지다 — 예제는 코드를 주석으로만 두고 함수 설명을 출력한다.
- Blowfish 기반이며 `rounds`(cost factor)로 시간 비용을 조절한다. 원본은 2^rounds 번 반복이라 적는다.
- 해시 결과 자체에 솔트가 들어 있어 따로 보관할 필요가 없다(자동 솔트).
- 원본은 `rounds=12` 가 약 0.25초 걸린다고 적는다 — 기계마다 다른 값이다.

> **cost factor** — 반복 횟수를 정하는 조절값.\
> 예: `rounds` 를 1 올리면 반복이 두 배가 된다(2^rounds 이므로).

### (6) HMAC 과 `compare_digest` — 열쇠 있는 지문, 일정한 속도의 대조

**언제 쓰나** — 메시지가 고쳐지지 않았고(무결성) 키를 아는 쪽이 보냈다(진위)는 것을 함께 확인할 때다.

```text
보내는 쪽: mac = hmac.new(secret_key, message, hashlib.sha256).hexdigest()
받는 쪽:   같은 키로 재계산 → hmac.compare_digest(받은 mac, 재계산 mac)

webhook:   expected = HMAC-SHA256(secret, payload)
           compare_digest(f"sha256={expected}", 받은 signature)
```

- `hmac.new(key, msg, digestmod)` 는 비밀키와 해시 함수로 HMAC 을 계산한다.
- 키가 없는 사람은 메시지를 고친 뒤 맞는 HMAC 을 새로 만들 수 없다 — 그냥 해시라면 누구나 다시 계산할 수 있다.
- `verify_webhook_signature` 는 GitHub 같은 webhook 의 서명(`X-Hub-Signature-256`)을 검증하는 패턴이다. 받은 서명이 `sha256=` 머리를 달고 오므로, 비교할 값도 같은 머리를 붙여 형식을 똑같이 맞춘다.
- 비교는 `==` 를 쓰지 말고 `hmac.compare_digest` 를 쓴다.

> **타이밍 공격** — 비교에 걸린 시간 차이로 비밀값을 한 글자씩 알아내는 공격.\
> 예: `==` 가 첫 다른 글자에서 바로 멈추면, 앞쪽이 많이 맞을수록 응답이 미세하게 늦어진다.

`compare_digest` 는 어디가 다르든 걸리는 시간이 달라지지 않게 비교하도록 만든 함수다.
`secrets.compare_digest(a, b)` 로도 같은 비교를 부를 수 있다.

> **HMAC** — 비밀키와 해시 함수를 엮어 만드는 메시지 인증 코드.\
> 예: `hmac.new(b'key', b'msg', hashlib.sha256).hexdigest()`.

### (7) `secrets` — 토큰과 난수

**언제 쓰나** — 세션 토큰 · 비밀번호 재설정 링크 · 인증 코드처럼 추측되면 안 되는 값을 만들 때다.

```text
secrets.token_hex(32)       32바이트 → 64글자 16진
secrets.token_urlsafe(32)   32바이트 → URL-safe base64 (쿠키·링크용)
secrets.token_bytes(16)     원시 16바이트
secrets.randbelow(100)      0 이상 100 미만 균등 정수
```

- `secrets` 는 암호학적으로 안전한 난수 생성기(CSPRNG)를 쓴다 — `random` 모듈보다 안전하다(PEP 506).
- 이 값들은 실행할 때마다 달라진다.

> **CSPRNG** — 앞선 출력을 보고도 다음 값을 예측할 수 없게 설계된 난수 생성기.\
> 예: `secrets.token_hex(32)` · `os.urandom(32)`.

## 문법 — 형태와 규칙

```python
import hashlib, hmac, os, secrets

digest = hashlib.sha256("abc".encode("utf-8")).hexdigest()

h = hashlib.new("sha256")
h.update(b"ab"); h.update(b"c")          # digest 와 같은 값

salt = os.urandom(16)
dk = hashlib.pbkdf2_hmac("sha256", b"pw", salt, iterations=600000, dklen=32)
record = f"600000${salt.hex()}${dk.hex()}"

mac = hmac.new(b"key", b"msg", hashlib.sha256).hexdigest()
same = hmac.compare_digest(mac, mac)

token = secrets.token_urlsafe(32)
```

- 해시 생성자 · `update` · `pbkdf2_hmac` · `hmac.new` 의 데이터 인자는 모두 `bytes` 다.
- `hashlib.<이름>(data)` 와 `hashlib.new('<이름>')` 은 같은 일을 하는 두 가지 꼴이다.
- `hexdigest()` 는 16진 `str`, `hex()` 는 `bytes` 를 16진 `str` 로, `bytes.fromhex()` 는 그 반대다.
- `hashlib.blake2b` 는 `digest_size` 로 출력 바이트 수를 정한다.
- `pbkdf2_hmac(해시이름, 비밀번호, 솔트, iterations=, dklen=)` 의 결과는 `bytes` 다.
- 비밀번호 저장 문자열에는 검증에 필요한 매개변수(반복 횟수 · 솔트)를 함께 담는다.
- 원본은 `binascii` 를 가져오지만 실제로 쓰지 않는다 — 16진 변환은 `bytes.hex()` · `bytes.fromhex()` 로 한다.

## 어디서 틀리나

### 1. 비밀번호를 SHA-256 한 번으로 저장한다
비밀번호는 반드시 솔트 + 반복 해싱(PBKDF2 · bcrypt · scrypt)으로 저장한다.
단순 SHA-256 은 비밀번호 저장에 부적합하다 — 솔트가 없으면 레인보우 테이블에 그대로 걸리고, 계산이 빨라 후보를 대량으로 시험할 수 있다.

### 2. 솔트만 붙이면 끝났다고 여긴다
솔트는 미리 만든 표와 「같은 비밀번호끼리 같은 해시」를 막는다.
한 계정을 노린 무차별 대입의 속도는 줄이지 못한다 — 그 일은 반복(키 스트레칭)이 한다.

### 3. 해시 · HMAC 을 `==` 로 비교한다
`==` 로 비교하면 타이밍 공격의 빌미가 된다.
`hmac.compare_digest()` 로 비교한다.

### 4. MD5 · SHA-1 을 보안에 쓴다
MD5 는 보안 용도로 쓰지 않고 체크섬에만 쓴다.
SHA-1 도 충돌 공격이 입증되어 보안 용도에 부적합하다.
「우연히 깨졌나」를 보는 데는 괜찮지만, 「누가 일부러 바꿨나」를 막는 데는 못 쓴다.

### 5. `str` 을 그대로 넣는다
해시 함수는 `bytes` 만 받는다.
`encode('utf-8')` 를 빠뜨리면 오류가 난다.

### 6. 반복 횟수 · 솔트를 버린다
검증하려면 저장할 때와 같은 반복 횟수 · 솔트로 다시 계산해야 한다.
반복 횟수를 나중에 바꿀 수도 있으니 저장 문자열에 함께 둔다.

### 7. webhook 서명 형식을 안 맞춘다
받은 서명이 `sha256=` 머리를 달고 오면, 계산한 값에도 같은 머리를 붙여 비교해야 한다.

### 8. 토큰을 `random` 으로 만든다
추측되면 안 되는 값은 `secrets` 로 만든다.

### 9. 원본 주석 중 의심스러운 것
- 원본 주장: 「compare_digest: 길이/바이트 차이를 상수 시간으로 비교」 → 의심스러운 까닭: 바이트 내용의 비교 시간이 일정하도록 만든 함수지만, 두 값의 길이가 다를 때까지 시간이 같다고 보장하는지는 따로 확인해야 한다 (확인 필요).
- 원본 주장: PBKDF2 기본값 `iterations=600000` 옆에 「NIST 권장」 → 의심스러운 까닭: PBKDF2 가 권장 방식이라는 것과 600000이라는 구체 숫자의 출처가 같은지 원본은 밝히지 않는다 (확인 필요).
- 원본 주장: 「rounds=12는 약 0.25초 소요」 → 의심스러운 까닭: 계산 시간은 기계 성능에 달려 있어 고정값이 아니다.

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| `update` 로 나눠 넣어도 한 번에 넣은 것과 결과가 같다 | 해시 알고리즘의 정의 + `hashlib` API 의 약속 |
| `compare_digest` 는 비교 시간이 값의 차이에 따라 달라지지 않게 만들어졌다 | 표준 라이브러리 문서의 설명(상수 시간의 범위는 확인 필요) |
| `os.urandom` · `secrets` 의 값은 예측할 수 없다 | 운영체제의 난수 소스 · 표준 라이브러리(PEP 506) |
| SHA-512 가 64비트 시스템에서 더 빠를 수 있다 | 하드웨어 · 구현에 따라 다름 — 언어 보장 아님 |
| bcrypt `rounds=12` 는 약 0.25초 | 기계 성능 — 보장 아님 |
| bcrypt 해시 안에 솔트가 들어 있다 | 외부 패키지 `bcrypt` 와 bcrypt 형식 — 파이썬 언어 보장 아님 |
| PBKDF2 는 NIST 권장 · 600000회 | 표준 기관의 권고 — 파이썬과 무관, 숫자는 (확인 필요) |
| MD5 · SHA-1 은 보안 부적합 | 암호학계의 분석 결과 — 언어가 막지 않는다 |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 내려받은 파일이 깨졌는지 확인 | `file_hash`(SHA-256), 체크섬이면 MD5 도 가능 | 파일 전체를 한 번에 `read()` |
| 비밀번호 저장 | PBKDF2(`pbkdf2_hmac`) · bcrypt · scrypt | SHA-256 한 번, 솔트만 붙인 SHA-256 |
| 메시지 · webhook 진위 확인 | `hmac.new` + `compare_digest` | 키 없는 단순 해시, `==` 비교 |
| 해시 · 토큰 비교 | `hmac.compare_digest` · `secrets.compare_digest` | `==` |
| 세션 토큰 · 재설정 링크 | `secrets.token_urlsafe` · `token_hex` | `random` 모듈 |
| 일반 데이터 지문 | SHA-256 · SHA-3 · BLAKE2 | 보안 목적의 MD5 · SHA-1 |

## 핵심 문장

1. **해시는 `bytes` 를 받아 고정 길이 지문을 낸다** — 같은 입력은 같은 지문, 조각내 `update` 해도 같다.
2. **비밀번호는 솔트 + 반복으로 저장한다** — 솔트는 표를 막고, 반복은 대입을 느리게 한다.
3. **검증에 필요한 매개변수는 해시 옆에 보관한다** — 반복 횟수 · 솔트 없이는 재계산이 안 된다.
4. **HMAC 은 키가 있는 해시다** — 무결성과 진위를 함께 본다.
5. **비밀값 비교는 `compare_digest`, 비밀값 생성은 `secrets`** 로 한다.

## 관련 자료

- `cryptography` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- `jwt-python` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- [oauth-jwt](../../python-web/14-oauth-jwt/2-summary.md)
- 원본: study-site 항목 데이터 `data/python/advanced-techniques.json` 의 `hashlib-security`

## 용어 풀이

- **해시 함수** — 임의 길이 바이트를 고정 길이 값으로 바꾸는 함수.
- **다이제스트** — 해시 함수의 결과값.
- **충돌** — 다른 두 입력이 같은 해시를 내는 일.
- **체크섬** — 데이터 손상 여부를 확인하려고 뜨는 값.
- **솔트** — 비밀번호에 섞는 사용자별 무작위 바이트.
- **레인보우 테이블** — 흔한 비밀번호의 해시를 미리 계산해 둔 조회표.
- **무차별 대입(brute-force)** — 후보를 하나씩 모두 넣어 보는 공격.
- **키 스트레칭** — 해시를 많이 반복해 계산을 느리게 만드는 기법.
- **PBKDF2** — HMAC 을 정해진 횟수만큼 반복해 키를 뽑는 방식.
- **bcrypt** — Blowfish 기반의 비밀번호 전용 해시, 솔트를 해시 안에 담는다.
- **cost factor** — bcrypt 의 반복 정도를 정하는 값(`rounds`).
- **HMAC** — 비밀키와 해시 함수로 만드는 메시지 인증 코드.
- **타이밍 공격** — 처리 시간 차이로 비밀을 알아내는 공격.
- **CSPRNG** — 암호학적으로 안전한 난수 생성기.
- **워러스 연산자(`:=`)** — 식 안에서 값을 변수에 담고 그 값을 그대로 쓰는 연산자.
- **`hexdigest` / `hex` / `fromhex`** — 결과를 16진 문자열로 / `bytes` 를 16진 문자열로 / 16진 문자열을 `bytes` 로.

## 더 들어가면

- `hashlib.scrypt` 도 표준 라이브러리에 있다고 알려져 있다 — 메모리까지 많이 쓰게 해 전용 하드웨어 공격을 어렵게 하는 방식이다 (확인 필요).
- `hashlib.md5(data, usedforsecurity=False)` 처럼 보안 용도가 아님을 밝히는 인자가 3.9 무렵 생겼다고 알려져 있다 — FIPS 모드 빌드에서 MD5 를 막는 환경과 관련된다 (확인 필요).
- `hashlib.new` 로 쓸 수 있는 알고리즘은 빌드에 링크된 OpenSSL 에 따라 달라질 수 있고, 어디서나 있는 것은 `hashlib.algorithms_guaranteed` 에 있다고 알려져 있다 (확인 필요).
- `compare_digest` 는 길이가 다르면 길이 정보 정도는 새어 나갈 수 있다고 문서가 적고 있다고 알려져 있다 (확인 필요).
- Argon2 는 비밀번호 해싱 대회(PHC)에서 뽑힌 알고리즘으로 `argon2-cffi` 같은 외부 패키지로 쓴다 (확인 필요).
- bcrypt 는 입력 비밀번호의 앞 72바이트까지만 쓴다고 알려져 있다 (확인 필요).
