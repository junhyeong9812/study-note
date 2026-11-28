# python/python-security/07 — RSA (비대칭 암호화) — 정리 (힌트)

> 출처 — study-site 항목 `python/rsa-encryption`(항목 데이터 `data/python/security.json`) · 정답 코드 study-practice `python/python-security/reference/rsa-encryption.py`\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).\
> 실행 — 실행하지 않음 — 외부 라이브러리 `cryptography` 가 있어야 도는 예제다 — 그것 없이 만들어 실행하지 않았다.

## 한눈에 — 쉽게 말하면

**RSA 는 「누구나 넣을 수 있고 주인만 여는 우체통」과 「주인만 찍을 수 있는 도장」을 한 쌍의 열쇠로 만든 것이다.**
우체통 투입구는 길가에 열려 있어서 아무나 편지를 넣는다.
꺼내는 열쇠는 주인 혼자 가진다.
도장은 주인만 찍을 수 있고, 도장 모양 대조표는 동네에 붙어 있어서 누구나 「이게 그 사람 도장이 맞나」를 확인한다.
RSA 의 키 쌍도 똑같은 구조다.
공개키는 투입구이자 대조표이고, 개인키는 우체통 열쇠이자 도장이다.

> **키 쌍(key pair)** — 수학적으로 묶여 만들어지는 공개키와 개인키 한 벌이다.\
> 예: `private_key.public_key()` 로 개인키에서 짝이 되는 공개키를 꺼낸다.

| 비유 | 실체 |
|---|---|
| 우체통 투입구 (누구나 넣음) | 공개키로 암호화 — `public_key.encrypt(...)` |
| 우체통 열쇠 (주인만 꺼냄) | 개인키로 복호화 — `private_key.decrypt(...)` |
| 주인의 도장 | 개인키로 서명 — `private_key.sign(...)` |
| 동네에 붙은 도장 대조표 | 공개키로 검증 — `public_key.verify(...)` |
| 편지를 넣는 봉투의 규격 | 패딩 — 암호화는 `OAEP`, 서명은 `PSS` |
| 열쇠를 넣어 두는 금고 | 비밀번호로 암호화한 개인키 PEM |

```text
          ┌───────────── 공개키 (누구에게나 나눠 줌) ─────────────┐
          │                                                     │
 보내는 사람 ── encrypt ──▶ 암호문 ──▶ 주인 ── decrypt (개인키) ──▶ 평문
                                                     기밀성

 주인 ── sign (개인키) ──▶ 서명 ──▶ 받는 사람 ── verify (공개키) ──▶ 맞다 / 아니다
                                                     인증 + 무결성
```

## 이 주제가 답하려는 질문

1. 키 쌍을 어떻게 만들고, 파일(PEM)로 저장했다가 다시 불러오나?
2. 공개키로 잠근 메시지를 어떻게 개인키로만 여나 — 그리고 왜 같은 평문이 매번 다른 암호문이 되나?
3. 서명으로 어떻게 「누가 썼나」와 「내용이 바뀌지 않았나」를 함께 확인하나?
4. RSA 만으로 큰 데이터를 다루지 않는 까닭은 무엇이고, 대신 무엇을 하나?

## 동작 방식

### (1) 키 쌍 만들기

**언제 쓰나** — 암호화든 서명이든 맨 먼저 한 번 한다.
개인키를 만들면 공개키는 그 안에서 꺼낼 수 있다.

```text
rsa.generate_private_key(public_exponent=65537, key_size=2048)
        │
        ▼
 private_key  (개인키 — 비밀)
        │ .public_key()
        ▼
 public_key   (공개키 — 나눠 줌)       ✗ 공개키 → 개인키 방향은 불가능
        │
        ▼
 private_key.key_size  →  2048
```

- `generate_private_key` 는 개인키 객체 하나를 돌려준다.
- `public_exponent=65537` 은 공개 지수로, 원본은 이것을 「표준 값」이라 부른다.
- `key_size=2048` 은 키의 비트 수이고, 원본 팁은 최소 2048비트, 장기 보안에는 4096비트를 권한다.
- 공개키는 개인키에서 도출되지만, 공개키에서 개인키를 되돌려 얻을 수는 없다.
- 이 한 방향성 덕분에 공개키를 아무에게나 줘도 된다.

> **공개 지수(public exponent)** — 공개키를 이루는 수 가운데 하나로, 암호화 · 검증 계산에 쓰인다.\
> 예: `public_exponent=65537`.

### (2) PEM 으로 직렬화하고 다시 불러오기

**언제 쓰나** — 키를 파일로 저장하거나 다른 프로그램에 넘길 때 쓴다.
메모리 속 키 객체를 텍스트 덩어리로 바꾸고(직렬화), 그 텍스트를 다시 키 객체로 되돌린다(로드).

```text
 private_key ── private_bytes(PEM, PKCS8, NoEncryption())            ──▶ private_pem   (평문 개인키 — 위험)
 private_key ── private_bytes(PEM, PKCS8, BestAvailableEncryption(pw)) ──▶ encrypted_pem (비밀번호로 잠긴 개인키)
 public_key  ── public_bytes(PEM, SubjectPublicKeyInfo)               ──▶ public_pem    (공개키)

 private_pem   ── load_pem_private_key(…, password=None)          ──▶ 개인키 객체
 encrypted_pem ── load_pem_private_key(…, password=b"my-password") ──▶ 개인키 객체
 public_pem    ── load_pem_public_key(…)                          ──▶ 공개키 객체
```

- `Encoding.PEM` 은 Base64 텍스트 꼴이라 저장 · 전송이 쉽다.
- 개인키 형식 `PrivateFormat.PKCS8` 은 표준 개인키 컨테이너다.
- 공개키 형식 `PublicFormat.SubjectPublicKeyInfo` 는 X.509 표준 공개키 형식이다.
- `NoEncryption()` 은 개인키를 잠그지 않고 그대로 적는다 — 원본은 「학습용, 실무에선 평문 저장 금지」라고 못 박는다.
- `BestAvailableEncryption(b"my-password")` 는 비밀번호로 개인키를 잠그며, 어떤 암호 방식으로 잠글지는 라이브러리가 고른다.
- 잠긴 PEM 은 같은 비밀번호를 줘야 열린다; 원본 주석대로 잘못된 비밀번호는 예외가 난다.
- 잠기지 않은 PEM 은 `password=None` 으로 연다.
- 불러온 키도 `key_size` 를 그대로 가진다 — 개인키 · 공개키 모두 2048 이다.
- PKCS8 평문 개인키 PEM 은 `-----BEGIN PRIVATE KEY-----` 로, 잠긴 것은 `-----BEGIN ENCRYPTED PRIVATE KEY-----` 로, 공개키는 `-----BEGIN PUBLIC KEY-----` 로 시작한다.

> **직렬화(serialization)** — 메모리 속 객체를 바이트나 텍스트로 바꿔 저장 · 전송할 수 있게 하는 일이다.\
> 예: `private_key.private_bytes(...)` 가 PEM 바이트를 돌려준다.

> **PEM** — 바이너리 키를 Base64 텍스트로 감싸고 `-----BEGIN …-----` · `-----END …-----` 줄을 붙인 꼴이다.\
> 예: `-----BEGIN PUBLIC KEY-----` 로 시작하는 텍스트.

### (3) 공개키 암호화 / 개인키 복호화 — OAEP

**언제 쓰나** — 「주인만 읽을 수 있는」 작은 비밀(대개 다른 암호의 키)을 보낼 때 쓴다.
목적은 기밀성이다.

```text
 "비밀 메시지입니다."  ── .encode('utf-8') ──▶ bytes
        │
        ▼  public_key.encrypt(bytes, OAEP(MGF1(SHA256), SHA256, label=None))
 ciphertext  (길이 = 키 크기의 바이트 수 = 2048 / 8 = 256 bytes)
        │      ※ 같은 평문을 다시 넣어도 OAEP 의 무작위성 때문에 다른 암호문
        ▼  private_key.decrypt(ciphertext, 같은 OAEP 설정)
 bytes ── .decode('utf-8') ──▶ "비밀 메시지입니다."
```

- RSA 는 문자열이 아니라 바이트를 다루므로 먼저 `encode('utf-8')` 한다.
- `padding.OAEP` 는 평문에 무작위 값을 섞어 감싼다 — 그래서 같은 평문도 매번 다른 암호문이 나오고, 원본은 이것을 CCA(선택 암호문 공격) 방어로 설명한다.
- `MGF1` 은 OAEP 안에서 쓰는 마스크 생성 함수이고, 여기에 넣는 해시와 OAEP 의 `algorithm` 해시를 모두 `SHA256` 으로 맞춘다.
- 복호화할 때는 암호화와 **똑같은 패딩 설정**을 넘겨야 한다; 다르면 복호화가 실패한다.
- 암호문의 길이는 평문 길이와 상관없이 키 크기의 바이트 수(2048비트면 256 바이트)다.
- 패딩이 자리를 차지하므로 한 번에 넣을 수 있는 평문은 키 크기보다 작다 — 긴 데이터는 RSA 로 직접 암호화하지 못한다.
- 암호문은 사람이 못 읽는 바이트라 화면에 보일 때는 `base64.b64encode` 로 텍스트로 바꾼다.

> **패딩(padding)** — RSA 계산에 넣기 전에 데이터를 정해진 규격으로 감싸는 방식이다.\
> 예: 암호화용 `padding.OAEP(...)`, 서명용 `padding.PSS(...)`.

### (4) 개인키 서명 / 공개키 검증 — PSS

**언제 쓰나** — 「이 문서는 내가 썼고, 그 뒤로 바뀌지 않았다」를 증명할 때 쓴다.
목적은 인증과 무결성이다.

```text
 data (bytes)
    │ private_key.sign(data, PSS(MGF1(SHA256), salt_length=MAX_LENGTH), SHA256)
    ▼     └ 안에서: data 를 SHA256 으로 해시 → 해시값을 개인키로 서명
 signature (256 bytes)
    │
    ├─ public_key.verify(signature, data, 같은 PSS, SHA256)            → 아무 일 없음 = 유효
    │
    └─ public_key.verify(signature, b"tampered data", 같은 PSS, SHA256) → InvalidSignature 예외 = 변조 감지
```

- `sign` 의 마지막 인자 `hashes.SHA256()` 은 데이터를 먼저 해시할 알고리즘이다 — 서명은 데이터 전체가 아니라 그 해시값 위에 만들어진다.
- `padding.PSS` 는 무작위 솔트를 섞는 서명 패딩이고, `salt_length=padding.PSS.MAX_LENGTH` 는 솔트를 허용되는 최대 길이로 잡는다.
- 솔트가 무작위이므로 같은 데이터에 두 번 서명하면 서명 바이트가 달라지지만, 둘 다 검증을 통과한다.
- `verify` 는 성공하면 아무것도 돌려주지 않고 조용히 끝나며, 실패하면 `InvalidSignature` 예외를 던진다 — 그래서 `try` / `except` 로 감싼다.
- 데이터가 한 글자만 달라도 해시가 달라지므로 검증이 실패한다.
- 서명할 때와 똑같은 패딩 · 해시 설정을 검증에도 넘겨야 한다.

> **솔트(salt)** — 같은 입력이 같은 결과를 내지 않도록 섞어 넣는 무작위 바이트다.\
> 예: `salt_length=padding.PSS.MAX_LENGTH`.

### (5) 역할 맞바꿈과 하이브리드 암호화

**언제 쓰나** — 어느 키를 어디에 쓸지 헷갈릴 때, 그리고 큰 데이터를 보낼 때 이 그림을 떠올린다.

```text
           누가 할 수 있나          누가 할 수 있나
 암호화:   공개키 → 누구나     복호화: 개인키 → 주인만     ⇒ 기밀성
 서명:     개인키 → 주인만     검증:   공개키 → 누구나     ⇒ 인증 + 무결성

 큰 데이터 (하이브리드):
   AES 키 하나를 무작위로 만든다
   데이터    ── AES ──────────▶ 암호화된 데이터 (빠름, 크기 제한 없음)
   AES 키    ── RSA-OAEP 공개키 ▶ 감싼 키 (작으니 RSA 로 충분)
   받는 쪽: 개인키로 AES 키를 풀고 → 그 키로 데이터를 푼다
```

- 「주인만 해야 하는 일」에는 언제나 개인키가, 「누구나 해도 되는 일」에는 언제나 공개키가 간다.
- 암호화는 누구나 할 수 있어야 비밀을 받을 수 있고, 서명은 주인만 할 수 있어야 증명이 된다 — 그래서 두 쓰임에서 키의 순서가 뒤집힌다.
- RSA 는 큰 데이터에 느리고 한 번에 넣을 수 있는 크기도 작다.
- 그래서 실제 데이터는 대칭 암호 AES 로 암호화하고, RSA 는 그 AES 키만 감싼다 — 원본 주석은 실 데이터를 AES-GCM 으로 암호화한다고 적는다.

> **하이브리드 암호화** — 데이터는 대칭 암호(AES)로, 그 대칭 키는 비대칭 암호(RSA)로 보호하는 방식이다.\
> 예: RSA-OAEP 로 AES 키를 감싸고, 데이터는 AES-GCM 으로 암호화한다.

## 문법 — 형태와 규칙

```python
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes

key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
pub = key.public_key()

oaep = padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(), label=None)
ct = pub.encrypt(b"hi", oaep)
pt = key.decrypt(ct, oaep)          # b"hi"

pss = padding.PSS(mgf=padding.MGF1(hashes.SHA256()),
                  salt_length=padding.PSS.MAX_LENGTH)
sig = key.sign(b"doc", pss, hashes.SHA256())
pub.verify(sig, b"doc", pss, hashes.SHA256())   # 실패하면 예외
```

- 키 생성: `rsa.generate_private_key(public_exponent=65537, key_size=2048 이상)`.
- 공개키 꺼내기: `private_key.public_key()`.
- 암호화: `public_key.encrypt(평문바이트, padding.OAEP(...))` — 패딩 객체는 반드시 넘긴다.
- 복호화: `private_key.decrypt(암호문, 암호화와_같은_OAEP)`.
- 서명: `private_key.sign(데이터, padding.PSS(...), hashes.SHA256())` — 인자 순서는 데이터 · 패딩 · 해시.
- 검증: `public_key.verify(서명, 데이터, 같은_PSS, 같은_해시)` — 반환값이 아니라 예외로 결과를 알린다.
- 개인키 직렬화: `private_key.private_bytes(encoding=Encoding.PEM, format=PrivateFormat.PKCS8, encryption_algorithm=...)`.
- 공개키 직렬화: `public_key.public_bytes(encoding=Encoding.PEM, format=PublicFormat.SubjectPublicKeyInfo)`.
- 로드: `serialization.load_pem_private_key(pem, password=비밀번호바이트_또는_None)` · `serialization.load_pem_public_key(pem)`.
- 모든 입력 · 출력은 `bytes` 다 — 문자열은 `encode` 로 넣고 `decode` 로 꺼낸다.

| 고를 것 | 선택지 | 쓰임 |
|---|---|---|
| `encoding` | `Encoding.PEM` | Base64 텍스트, 저장 · 전송용 |
| 개인키 `format` | `PrivateFormat.PKCS8` | 표준 개인키 컨테이너 |
| 공개키 `format` | `PublicFormat.SubjectPublicKeyInfo` | X.509 표준 공개키 형식 |
| `encryption_algorithm` | `NoEncryption()` | 평문 저장 — 학습용으로만 |
| `encryption_algorithm` | `BestAvailableEncryption(pw)` | 비밀번호 보호 — 실무 권장 |
| 암호화 패딩 | `OAEP` | PKCS1v15 보다 안전 |
| 서명 패딩 | `PSS` | PKCS1v15 보다 안전 |

## 어디서 틀리나

### 1. 개인키를 평문으로 저장하거나 코드에 넣는다

원본 팁은 「개인키는 반드시 암호화하여 저장하고, 코드에 포함하지 않는다」고 한다.
`NoEncryption()` 으로 만든 PEM 은 파일만 손에 넣으면 누구나 개인키를 쓴다.
저장할 때는 `BestAvailableEncryption` 으로 잠그고, 비밀번호 자체도 코드에 박지 않는다.
예제의 `b"my-password"` 는 학습용이다.

### 2. 키를 너무 작게 만든다

원본 팁은 최소 2048비트, 장기 보안에는 4096비트를 권한다.
그보다 작은 키는 쓰지 않는다.

### 3. PKCS1v15 패딩을 고른다

원본 팁은 OAEP(암호화)와 PSS(서명)가 PKCS1v15 보다 안전하다고 한다.
새로 쓰는 코드는 암호화에 `OAEP`, 서명에 `PSS` 를 쓴다.

### 4. 암호화 · 복호화(또는 서명 · 검증)의 패딩 설정이 다르다

복호화에는 암호화와 같은 OAEP 설정을, 검증에는 서명과 같은 PSS · 해시 설정을 넘겨야 한다.
하나라도 다르면 올바른 키로도 복호화 · 검증이 실패한다.
설정을 한 번 만들어 변수에 담아 두면 어긋나지 않는다.

### 5. 큰 데이터를 RSA 로 직접 암호화한다

RSA 는 큰 데이터에 느리고, 패딩 때문에 한 번에 넣을 수 있는 평문은 키 크기보다 작다.
긴 데이터는 하이브리드 암호화로 처리한다.

### 6. `verify` 의 반환값을 검사한다

`verify` 는 성공해도 `True` 를 돌려주지 않는다 — 예외가 없으면 성공이다.
`if public_key.verify(...):` 처럼 쓰면 성공해도 조건이 거짓이 된다.

### 7. `except Exception` 으로 너무 넓게 잡는다

원본은 `except Exception` 으로 모든 예외를 「서명 무효」로 처리한다.
그러면 인자를 잘못 넘긴 프로그래밍 실수도 「변조 감지」로 보인다.
원본 주석이 말하는 실패 예외는 `InvalidSignature` 이니, 그것만 잡는 편이 정확하다.

### 8. 원본 주석에서 의심스러운 곳

- 원본 주석 「2048비트: NIST 최소 권장 (~2030년까지)」 → 정확한 기한은 권고 문서의 판에 따라 다르므로 이 문서에서 확인하지 않았다 (확인 필요).
- 원본 주석 「4096: 장기 보안 (성능 저하 ~5배)」 → 몇 배 느려지는지는 연산(서명 · 복호화 · 검증)과 기계에 따라 다르고, 한 숫자로 단정할 근거가 원본에 없다 (확인 필요).
- 원본은 `Prehashed` 를 「사전 해시된 데이터 처리 보조」로 들여오지만, 코드 어디에서도 쓰지 않는다 — 지워도 동작이 같다.
- 원본 끝의 결과 주석은 일부 줄만 적었고, `서명 검증: 유효함` 줄에는 코드가 실제로 찍는 `✓` 가 빠져 있다 — 그 주석을 결과 전체로 믿으면 안 된다.

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| `verify` 가 실패하면 `InvalidSignature` 예외를 던지고 성공하면 아무것도 돌려주지 않는다 | `cryptography` 라이브러리의 API — Python 언어가 아니다 |
| `BestAvailableEncryption` 이 고르는 실제 암호 방식 | `cryptography` 라이브러리 — 판에 따라 바뀔 수 있다 (확인 필요) |
| OAEP 암호문이 매번 달라진다 | OAEP 패딩 규격 — 무작위 값을 섞도록 정의되어 있다 |
| PSS 서명이 매번 달라진다 | PSS 규격 — 무작위 솔트를 쓴다 |
| 2048비트 키의 암호문 · 서명이 256 바이트다 | RSA 의 수학 — 결과가 모듈러스 크기와 같다 |
| `65537` 이 「표준 값」이다 | 널리 쓰는 관례 — 수학이 다른 값을 막지는 않는다 |
| 2048비트가 2030년까지 안전하다 | 원본 주석이 든 권고 — 이 문서에서 확인하지 않았다 (확인 필요) |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 상대만 읽게 짧은 비밀(키 등)을 보낸다 | 상대 공개키 + `OAEP` 로 `encrypt` | 내 개인키로 「암호화」하기 |
| 내가 쓴 문서임을 증명한다 | 내 개인키 + `PSS` 로 `sign` | 공개키로 서명 흉내 |
| 큰 파일을 상대만 읽게 보낸다 | 하이브리드 — AES 로 데이터, RSA-OAEP 로 AES 키 | 파일 전체를 RSA 로 직접 |
| 개인키를 디스크에 둔다 | `BestAvailableEncryption` 으로 잠근 PKCS8 PEM | `NoEncryption()` · 코드 속 하드코딩 |
| 공개키를 나눠 준다 | `SubjectPublicKeyInfo` PEM | 개인키 PEM 을 대신 보내기 |
| 패딩을 고른다 | 암호화 `OAEP`, 서명 `PSS` | `PKCS1v15` |

## 핵심 문장

1. **주인만 해야 하는 일(복호화 · 서명)은 개인키, 누구나 해도 되는 일(암호화 · 검증)은 공개키다.**
2. **암호화는 기밀성을, 서명은 인증과 무결성을 준다** — 같은 키 쌍이지만 목적이 다르다.
3. **패딩은 암호화에 OAEP, 서명에 PSS 를 쓰고, 양쪽 끝에서 똑같이 맞춘다.**
4. **개인키는 잠가서 저장하고 코드에 넣지 않는다; 키는 2048비트 이상이다.**
5. **RSA 는 작은 것(대칭 키)만 감싸고, 큰 데이터는 AES 에 맡긴다.**

## 관련 자료

- [fernet-encryption](../06-fernet-encryption/2-summary.md)
- [ssl-tls](../08-ssl-tls/2-summary.md)
- [hashlib-basics](../01-hashlib-basics/2-summary.md)
- 원본: study-site 항목 데이터 `data/python/security.json` 의 `rsa-encryption`

## 용어 풀이

- **RSA** — 공개키와 개인키를 쓰는 비대칭 암호 알고리즘이다.
- **비대칭 암호화** — 암호화하는 키와 푸는 키가 서로 다른 방식이다.
- **대칭 암호화** — 같은 키 하나로 암호화하고 푸는 방식이다(AES 등).
- **공개키** — 나눠 줘도 되는 키로, 암호화와 서명 검증에 쓴다.
- **개인키** — 주인만 가지는 키로, 복호화와 서명에 쓴다.
- **키 쌍** — 함께 만들어진 공개키 · 개인키 한 벌이다.
- **공개 지수** — 공개키를 이루는 수, 흔히 65537 이다.
- **키 크기** — 키의 비트 수, `key_size` 로 정한다.
- **직렬화** — 키 객체를 바이트 · 텍스트로 바꾸는 일이다.
- **PEM** — Base64 텍스트에 BEGIN/END 줄을 붙인 키 저장 꼴이다.
- **PKCS8** — 표준 개인키 컨테이너 형식이다.
- **SubjectPublicKeyInfo** — X.509 표준 공개키 형식이다.
- **패딩** — RSA 계산 전에 데이터를 규격대로 감싸는 방식이다.
- **OAEP** — 무작위성을 섞는 암호화용 패딩이다.
- **PSS** — 무작위 솔트를 섞는 서명용 패딩이다.
- **PKCS1v15** — OAEP · PSS 보다 오래되고 덜 안전한 패딩이다.
- **MGF1** — OAEP · PSS 안에서 쓰는 마스크 생성 함수다.
- **솔트** — 결과가 매번 달라지도록 섞는 무작위 바이트다.
- **해시** — 데이터를 고정 길이 값으로 줄이는 함수, 여기서는 SHA256 이다.
- **디지털 서명** — 개인키로 만든, 데이터에 묶인 증명값이다.
- **기밀성** — 허락된 사람만 내용을 읽을 수 있는 성질이다.
- **인증** — 누가 만들었는지 확인되는 성질이다.
- **무결성** — 내용이 바뀌지 않았음이 확인되는 성질이다.
- **CCA(선택 암호문 공격)** — 공격자가 고른 암호문의 복호 결과를 이용하는 공격이다.
- **`InvalidSignature`** — 검증이 실패할 때 `verify` 가 던지는 예외다.
- **Base64** — 바이너리를 텍스트 문자로 바꾸는 인코딩이다.
- **하이브리드 암호화** — 데이터는 AES 로, AES 키는 RSA 로 보호하는 방식이다.
- **AES-GCM** — 암호화와 변조 검사를 함께 하는 AES 사용 방식이다.

## 더 들어가면

- 2048비트 키와 SHA256 OAEP 에서 한 번에 넣을 수 있는 평문의 최대 길이는 `256 - 2×32 - 2 = 190` 바이트로 계산된다 (확인 필요).
- 한도를 넘는 평문을 `encrypt` 에 넣으면 예외가 난다 — 예외 종류는 라이브러리 판에 따라 확인이 필요하다 (확인 필요).
- 잠긴 PEM 을 `password=None` 으로 열려 하면 `TypeError`, 틀린 비밀번호를 주면 `ValueError` 가 나는 것으로 알려져 있다 (확인 필요).
- `PSS.MAX_LENGTH` 대신 해시 길이와 같은 솔트(`PSS.DIGEST_LENGTH`)를 권하는 표준 · 라이브러리도 있다 (확인 필요).
- 이미 해시한 값에 서명하려면 `Prehashed(hashes.SHA256())` 를 해시 인자 자리에 넘긴다 — 원본이 들여오기만 하고 쓰지 않은 것의 쓰임이다 (확인 필요).
- 서명 검증만으로는 「이 공개키가 정말 그 사람 것인가」를 알 수 없다 — 이를 위해 인증서(X.509)와 인증기관을 쓴다 (확인 필요).
