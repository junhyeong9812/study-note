# python/python-security/06 — Fernet (대칭 암호화) — 정리 (힌트)

> 출처 — study-site 항목 `python/fernet-encryption`(항목 데이터 `data/python/security.json`) · 정답 코드 study-practice `python/python-security/reference/fernet-encryption.py`\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).\
> 실행 — 실행하지 않음 — 외부 라이브러리 `cryptography` 가 있어야 도는 예제다 — 그것 없이 만들어 실행하지 않았다.

## 한눈에 — 쉽게 말하면

**Fernet 은 「봉인 테이프가 붙은 자물쇠 상자」다.**
열쇠 하나로 상자를 잠그고, 같은 열쇠로만 연다.
상자에는 봉인 테이프가 붙어 있어서, 누가 상자를 몰래 뜯었다 붙이면 여는 순간 들킨다.
상자 겉면에는 잠근 시각이 찍혀 있어서 「10초 지난 상자는 받지 않는다」 같은 규칙도 걸 수 있다.
Fernet 도 똑같은 구조다.

| 비유 | 실체 |
|---|---|
| 열쇠 | `Fernet.generate_key()` 가 만든 키 |
| 상자에 넣고 잠그기 | `encrypt(바이트)` |
| 상자 열기 | `decrypt(토큰)` |
| 봉인 테이프 | HMAC-SHA256 (변조 검사) |
| 자물쇠 | AES-128-CBC (내용 숨기기) |
| 겉면에 찍힌 시각 | 토큰 안의 타임스탬프 |
| 열쇠 꾸러미 | `MultiFernet([새 키, 옛 키])` |

```text
  평문(bytes) ──encrypt(key)──▶ 토큰(bytes)
                                  │
  평문(bytes) ◀──decrypt(key)─────┘   같은 key 일 때만
                                      다른 key·변조된 토큰이면 InvalidToken
```

> **대칭 암호화** — 잠그는 키와 여는 키가 같은 암호화 방식이다.\
> 예: `Fernet(key).encrypt(...)` 로 잠근 것은 `Fernet(key).decrypt(...)` 로만 풀린다.

## 이 주제가 답하려는 질문

1. 데이터를 남이 읽지도, 몰래 고치지도 못하게 하려면 무엇을 해야 하나?
2. 「너무 오래된 암호문은 받지 않는다」는 규칙은 어떻게 거나?
3. 키를 바꿔야 할 때, 이미 옛 키로 잠근 데이터는 어떻게 하나?
4. 딕셔너리 같은 구조화된 설정을 통째로 암호화하려면 어떻게 하나?

## 동작 방식

### (1) 키 생성 — 256비트 키 하나에 두 역할

**언제 쓰나** — 암호화를 시작하기 전 단 한 번, 키를 만들 때 쓴다.
만든 키는 어딘가에 보관해야 나중에 복호화할 수 있다.

```text
Fernet.generate_key()
   │  256비트(32바이트) 무작위 값
   ▼  URL-safe Base64 로 인코딩
b'....=' (bytes)
   │
   └─ 안쪽에서 둘로 나뉘어 쓰인다:
        128비트 → AES 암호화 키
        128비트 → HMAC 서명 키
```

- `generate_key()` 는 256비트 키를 URL-safe Base64 로 인코딩한 `bytes` 를 돌려준다.
- Base64 로 바꿔 두면 파일 · 환경 변수 · 설정에 글자로 저장하고 옮기기 쉽다.
- 키 256비트는 안에서 128비트 암호화 키와 128비트 서명 키로 나뉘어 쓰인다.

> **Base64** — 바이트를 영문자 · 숫자 · 몇몇 기호만으로 적는 인코딩이다.\
> 예: 무작위 32바이트를 글자열로 바꿔 환경 변수에 넣을 수 있게 한다.

### (2) 암호화 — IV · AES · HMAC 을 한 번에

**언제 쓰나** — 비밀번호 · API 키처럼 남이 보면 안 되는 데이터를 저장하거나 보낼 때 쓴다.

```text
f = Fernet(key)
f.encrypt("민감한 데이터".encode('utf-8'))
   │ ① IV(초기화 벡터)를 새로 만든다
   │ ② AES-128-CBC 로 평문을 암호화한다      → 기밀성
   │ ③ 버전·타임스탬프·IV·암호데이터에 HMAC 을 붙인다 → 무결성
   ▼
토큰 = 버전 + 타임스탬프 + IV + 암호데이터 + HMAC  (bytes)
```

- `Fernet(key)` 는 키를 묶어 둔 인스턴스를 만든다.
- `encrypt` 는 `bytes` 를 받는다 — 문자열이면 먼저 `.encode('utf-8')` 로 바꾼다.
- 호출할 때마다 IV 를 새로 만들어 쓰므로, 같은 평문이라도 매번 다른 토큰이 나온다.
- 토큰에는 암호데이터만이 아니라 버전 · 타임스탬프 · IV · HMAC 이 함께 들어 있다.

> **IV(초기화 벡터)** — 같은 평문이 같은 암호문이 되지 않도록 암호화마다 새로 섞어 넣는 값이다.\
> 예: 같은 문장을 두 번 `encrypt` 해도 토큰이 달라지는 까닭이다.

> **HMAC** — 키를 넣어 계산한 데이터의 지문이다. 키 없이는 맞는 지문을 만들 수 없다.\
> 예: 토큰의 한 바이트만 바뀌어도 지문이 맞지 않아 거부된다.

### (3) 복호화 — HMAC 검사부터

**언제 쓰나** — 저장해 둔 토큰에서 원래 데이터를 꺼낼 때 쓴다.

```text
f.decrypt(token)
   │ ① HMAC 을 다시 계산해 토큰 속 HMAC 과 비교한다
   │      ├ 다르면 → InvalidToken 예외 (잘못된 키 · 변조 모두 여기서 걸린다)
   │      └ 같으면 ↓
   │ ② AES 로 암호데이터를 푼다
   ▼
평문 (bytes)  → .decode('utf-8') 로 문자열 복원
```

- `decrypt` 는 먼저 HMAC 을 검사한다.
- 다른 키로 열거나 토큰이 변조됐으면 HMAC 이 맞지 않아 `InvalidToken` 예외가 난다.
- 그래서 예외 하나만 보고는 「키가 틀렸나, 데이터가 변조됐나」를 가를 수 없다.
- 돌려주는 값은 `bytes` 다 — 그대로 출력하면 `b'...'` 꼴로 보이고, 문자열로 쓰려면 `.decode('utf-8')` 한다.

### (4) TTL — 복호화할 때 거는 유효 시간

**언제 쓰나** — 비밀번호 재설정 링크처럼 일정 시간만 유효해야 하는 토큰을 만들 때 쓴다.

```text
token = f.encrypt(b"time-limited data")   ← 토큰에 발급 시각이 박힌다
f.decrypt(token, ttl=10)                   ← 「발급 후 10초 안이면 통과」
   │ 발급 시각 + ttl 이 지금보다 이전이면 → InvalidToken
   ▼
(1초 기다린 뒤) f.decrypt(token, ttl=0)    ← 이미 0초가 지났으므로 만료
```

- 유효 시간은 암호화할 때가 아니라 **복호화할 때** `ttl=` 인자로 건다.
- 기준은 토큰 안에 들어 있는 발급 타임스탬프다.
- 같은 키로 만든 다른 인스턴스(`f2 = Fernet(key)`)도 같은 토큰을 풀 수 있다 — 키가 같으면 인스턴스는 상관없다.
- 만료된 토큰도 `InvalidToken` 으로 거부된다.

> **TTL(time to live)** — 발급 뒤 몇 초 동안 유효한지를 나타내는 값이다.\
> 예: `decrypt(token, ttl=10)` 은 10초가 지난 토큰을 거부한다.

### (5) MultiFernet — 키 로테이션

**언제 쓰나** — 키를 새것으로 바꿔야 하지만, 옛 키로 잠근 데이터가 DB 에 남아 있을 때 쓴다.

```text
multi = MultiFernet([Fernet(new_key), Fernet(old_key)])
                      └ 첫 번째 = 암호화에 쓰는 키

multi.encrypt(...)        → 항상 첫 번째 키(new_key)로 암호화
multi.decrypt(옛 토큰)     → new_key 로 시도 → 실패 → old_key 로 시도 → 성공
multi.rotate(옛 토큰)      → 복호화한 뒤 첫 번째 키로 다시 암호화
                             ▼
Fernet(new_key).decrypt(rotated)  → 성공 — 이제 old_key 를 폐기할 수 있다
```

- `MultiFernet` 은 키 목록을 받는다.
- 암호화는 늘 첫 번째 키로 한다 — 그래서 새 키를 맨 앞에 둔다.
- 복호화는 목록 순서대로 키를 하나씩 시도한다 — 옛 데이터도 읽을 수 있다.
- `rotate` 는 토큰을 풀고 첫 번째 키로 다시 잠근다.
- 모든 토큰을 `rotate` 한 뒤에는 옛 키를 버려도 된다 — 서비스를 멈추지 않고 키를 바꿀 수 있다.

> **키 로테이션** — 쓰던 키를 새 키로 바꾸고, 옛 키로 잠근 데이터를 새 키로 다시 잠그는 일이다.\
> 예: `multi.rotate(old_encrypted)` 가 옛 토큰을 새 키 토큰으로 바꾼다.

### (6) 실무 패턴 — 설정 딕셔너리 통째로 암호화

**언제 쓰나** — DB URL · API 시크릿 · Redis 비밀번호처럼 민감한 값이 든 설정을 저장할 때 쓴다.

```text
config_dict ──json.dumps──▶ str ──encode──▶ bytes ──encrypt──▶ 토큰
토큰 ──decrypt──▶ bytes ──decode──▶ str ──json.loads──▶ config_dict
```

- Fernet 은 `bytes` 만 다루므로, 딕셔너리는 JSON 으로 직렬화해 바이트로 바꾼 뒤 암호화한다.
- 복호화는 그 반대 순서로 거슬러 간다.
- `SecureConfig` 클래스는 키를 묶어 두고 `encrypt_config` · `decrypt_config` 두 메서드로 이 왕복을 감싼다.

> **직렬화** — 딕셔너리 같은 구조를 글자열이나 바이트로 펼쳐 적는 일이다.\
> 예: `json.dumps({"a": 1})` → `'{"a": 1}'`.

## 문법 — 형태와 규칙

```python
from cryptography.fernet import Fernet, MultiFernet, InvalidToken

key = Fernet.generate_key()          # bytes, Base64 인코딩된 256비트
f = Fernet(key)

token = f.encrypt("비밀".encode("utf-8"))
print(f.decrypt(token).decode("utf-8"))   # 비밀

try:
    f.decrypt(token, ttl=60)          # 발급 60초 안에만 유효
except InvalidToken:
    print("거부됨")

multi = MultiFernet([Fernet(Fernet.generate_key()), f])
new_token = multi.rotate(token)       # 첫 번째 키로 다시 암호화
```

- `Fernet.generate_key()` — 새 키(`bytes`)를 돌려주는 클래스 메서드다.
- `Fernet(key)` — 키를 묶은 인스턴스를 만든다.
- `encrypt(data: bytes) -> bytes` — 토큰을 돌려준다. 문자열은 미리 `encode` 한다.
- `decrypt(token, ttl=None) -> bytes` — HMAC 검사 → 복호화. 실패하면 `InvalidToken`.
- `ttl=초` — 발급 시각 기준으로 그 초가 지난 토큰을 거부한다.
- `MultiFernet([키0, 키1, …])` — 암호화는 키0, 복호화는 순서대로 시도한다.
- `MultiFernet.rotate(token)` — 풀고 키0으로 다시 잠근 토큰을 돌려준다.

## 어디서 틀리나

### 1. 키를 코드에 적어 두기

키를 소스에 하드코딩하면 소스를 보는 사람 누구나 데이터를 풀 수 있다.
키는 환경 변수나 키 관리 서비스(KMS) · Vault 같은 곳에 두고, 실행할 때 읽어 온다.

### 2. 키를 매번 새로 만들기

예제는 실행할 때마다 `generate_key()` 로 새 키를 만든다.
이대로 암호화한 설정을 파일에 저장하면, 다음 실행에서는 키가 달라 풀 수 없다.
키는 한 번 만들어 보관하고, 그 보관한 키를 다시 읽어 써야 한다.
원본의 `import os` 는 「환경 변수 키 로딩」용이라고 주석이 달려 있지만, 예제 안에서 실제로 쓰이지는 않는다.

### 3. 문자열을 그대로 `encrypt` 에 넘기기

`encrypt` 는 `bytes` 를 받는다.
`"..."` 문자열은 `.encode('utf-8')` 로 바꿔 넘기고, `decrypt` 결과는 `.decode('utf-8')` 로 되돌린다.

### 4. 예외를 너무 넓게 잡기

원본은 `except Exception as e:` 로 잡는다.
그러면 Fernet 과 상관없는 버그(오타로 난 `NameError` 등)도 「잘못된 키」로 잘못 보고된다.
`InvalidToken` 을 직접 잡는 편이 뜻이 분명하다 (원본에 근거 없음 — 추론).

### 5. 같은 예외, 다른 원인

잘못된 키 · 변조된 토큰 · TTL 만료가 모두 `InvalidToken` 하나로 나온다.
예외만 보고 원인을 단정하지 않는다.

### 6. MultiFernet 의 키 순서

암호화와 `rotate` 는 **첫 번째** 키를 쓴다.
옛 키를 앞에 두면 새 데이터가 계속 옛 키로 잠기고, 로테이션이 거꾸로 일어난다.

### 7. 키 길이 주석

원본 주석의 주장: 「키 크기 = 32바이트(256비트)」를 `len(key)` 출력 줄 바로 위에 달았다.
왜 의심스러운가: `key` 는 Base64 로 인코딩된 `bytes` 라서 `len(key)` 는 원래 바이트 수 32가 아니라 인코딩된 글자 수다.
32바이트를 Base64(패딩 포함)로 적으면 4 × ⌈32 ÷ 3⌉ = 44 글자가 된다 (원본에 근거 없음 — 추론).
「256비트 키」라는 말은 맞지만, 출력되는 숫자는 32가 아닐 것이다.

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| AES-128-CBC + HMAC-SHA256, 키 256비트를 128+128 로 나눔 | Fernet 명세 — 파이썬 언어와 무관 |
| 토큰 = 버전 + 타임스탬프 + IV + 암호데이터 + HMAC | Fernet 명세 |
| 실패하면 `InvalidToken` 이 난다 | `cryptography` 라이브러리의 API |
| `MultiFernet` 은 첫 키로 암호화하고 순서대로 복호화를 시도한다 | `cryptography` 라이브러리의 API |
| `bytes` 를 출력하면 `b'...'` 꼴로 보인다 | 파이썬 언어(`bytes` 의 표현) |
| `json.dumps` / `json.loads` 왕복으로 딕셔너리가 복원된다 | 파이썬 표준 라이브러리(값이 JSON 으로 표현 가능할 때) |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 내 서비스가 저장했다가 다시 읽을 비밀 값 | `Fernet` | 평문 저장 |
| 일정 시간만 유효한 토큰 | `decrypt(..., ttl=)` | 만료를 따로 안 거는 토큰 |
| 키 교체 중 옛 데이터도 읽어야 함 | `MultiFernet` + `rotate` | 옛 키를 바로 버리기 |
| 딕셔너리 설정 암호화 | JSON 직렬화 → `encrypt` | `str(dict)` 를 암호화했다가 손으로 파싱 |
| 키 보관 | 환경 변수 · KMS · Vault | 소스 코드 하드코딩 |

## 핵심 문장

1. **Fernet 은 AES(기밀성)와 HMAC(무결성)을 한 번에 건다** — 읽지도, 몰래 고치지도 못한다.
2. **`decrypt` 는 HMAC 부터 본다** — 잘못된 키 · 변조 · 만료는 모두 `InvalidToken` 이다.
3. **TTL 은 복호화할 때 건다** — 토큰 속 발급 시각이 기준이다.
4. **`MultiFernet` 은 첫 키로 잠그고, 모든 키로 열어 본다** — `rotate` 로 무중단 키 교체를 한다.
5. **키는 코드 밖에 보관한다** — 키가 곧 데이터다.

## 관련 자료

- [rsa-encryption](../07-rsa-encryption/2-summary.md)
- [hashlib-basics](../01-hashlib-basics/2-summary.md)
- `secure-coding` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- 원본: study-site 항목 데이터 `data/python/security.json` 의 `fernet-encryption`

## 용어 풀이

- **대칭 암호화** — 잠그는 키와 여는 키가 같은 암호화.
- **Fernet** — `cryptography` 라이브러리가 제공하는, AES + HMAC 을 묶은 대칭 암호화 방식.
- **AES-128-CBC** — 128비트 키를 쓰는 블록 암호 AES 를 CBC 방식으로 돌리는 것. 내용을 숨긴다.
- **HMAC-SHA256** — SHA-256 해시에 키를 넣어 만든 지문. 변조를 잡는다.
- **기밀성** — 키 없는 사람이 내용을 읽을 수 없는 성질.
- **무결성** — 데이터가 중간에 바뀌지 않았음을 확인할 수 있는 성질.
- **IV(초기화 벡터)** — 암호화마다 새로 만드는 값. 같은 평문이 같은 암호문이 되는 것을 막는다.
- **토큰** — Fernet 이 `encrypt` 로 돌려주는 결과 바이트.
- **TTL** — 발급 뒤 유효한 시간(초).
- **InvalidToken** — Fernet 이 검증에 실패했을 때 내는 예외.
- **키 로테이션** — 옛 키를 새 키로 바꾸고 데이터를 다시 잠그는 일.
- **MultiFernet** — 여러 Fernet 키를 묶어 로테이션을 돕는 클래스.
- **KMS** — 키 관리 서비스. 키를 코드 밖에서 보관 · 발급한다.
- **Base64** — 바이트를 글자로 적는 인코딩.
- **직렬화** — 구조를 글자열 · 바이트로 펼치는 일.

## 더 들어가면

- Fernet 토큰의 타임스탬프는 암호화되지 않은 채 토큰 앞부분에 들어 있다 — 키가 없어도 발급 시각은 읽을 수 있다 (확인 필요).
- 타임스탬프는 초 단위 정수라서, `sleep` 없이 곧바로 `ttl=0` 으로 검사하면 같은 초 안이라 통과할 수도 있다 (확인 필요).
- `MultiFernet.rotate` 는 원래 토큰의 타임스탬프를 그대로 이어받는다고 알려져 있다 — 로테이션이 TTL 을 연장하지 않는다 (확인 필요).
- `generate_key` 는 운영체제의 암호학적 난수(`os.urandom`)로 키를 만든다 (확인 필요).
- Fernet 은 데이터를 통째로 메모리에 올려 다루므로 매우 큰 파일 암호화에는 맞지 않는다 (확인 필요).
- 키 안에서 앞 16바이트가 서명 키, 뒤 16바이트가 암호화 키로 쓰인다 (확인 필요).
