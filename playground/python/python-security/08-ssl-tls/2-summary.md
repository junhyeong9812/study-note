# python/python-security/08 — SSL/TLS (보안 통신) — 정리 (힌트)

> 출처 — study-site 항목 `python/ssl-tls`(항목 데이터 `data/python/security.json`) · 정답 코드 study-practice `python/python-security/reference/ssl-tls.py`\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).\
> 실행 — 실행하지 않음 — 실행 환경 · 바깥 네트워크에 따라 달라지는 예제다.

## 한눈에 — 쉽게 말하면

**TLS 연결은 「신분증을 확인하고 나서야 봉투를 여는 등기 우편」이다.**
우체부(서버)가 문 앞에 오면 먼저 신분증(인증서)을 본다.
신분증이 믿을 만한 기관(CA)에서 나왔는지, 이름이 내가 부른 사람(호스트명)과 맞는지 확인한다.
확인이 끝나면 둘만 아는 자물쇠(암호 스위트)로 잠근 봉투를 주고받는다.
파이썬의 `ssl` 모듈도 똑같은 구조다.
`SSLContext` 는 「무엇을 어디까지 확인할지」를 적어 둔 확인 규칙서이고, 소켓을 이 규칙서로 감싸면 TLS 연결이 된다.

| 비유 | 실체 |
|---|---|
| 확인 규칙서 | `SSLContext` (`ssl.create_default_context()` 로 만든 것) |
| 신분증 | 서버 인증서 (X.509) |
| 신분증을 발급한 기관 | CA (인증 기관) |
| 믿을 만한 기관 명단 | 시스템 CA 인증서 묶음 (`load_default_certs()`) |
| 신분증 이름과 부른 이름 대조 | 호스트명 검증 (`check_hostname`) |
| 자물쇠의 종류 | 암호 스위트 (`set_ciphers`) |
| 신분증을 안 보고 문을 열어 줌 | `verify_mode = ssl.CERT_NONE` |

```text
  내 프로그램                                   서버
  ──────────                                   ────
  SSLContext (규칙서)
      │
  TCP 소켓 ──── wrap_socket ────▶  TLS 핸드셰이크
                                    ├─ 서버가 인증서를 보낸다
                                    ├─ CA 서명 확인  (verify_mode)
                                    ├─ 이름 대조     (check_hostname)
                                    └─ 암호 스위트·TLS 버전 합의
      ◀──────────── 암호화된 데이터 ────────────▶
```

## 이 주제가 답하려는 질문

1. 파이썬에서 「안전한 기본값」으로 TLS 연결을 만들려면 무엇을 부르나, 그 기본값은 무엇을 켜 두나?
2. HTTPS 요청과 날것의 TLS 소켓은 어떻게 만들고, 서버 인증서에서 무엇을 읽어 낼 수 있나?
3. 더 엄격한 정책(TLS 버전 하한 · 암호 스위트 제한)은 어떻게 걸고, 반대로 검증을 끄면 무엇이 뚫리나?

## 동작 방식

### (1) 기본 컨텍스트 — `create_default_context()` 가 켜 두는 것

**언제 �르나** — TLS 연결을 만들 때 언제나 출발점으로 쓴다.
따로 고칠 이유가 없으면 이것만 쓴다.

```text
ctx = ssl.create_default_context()
        │
        ▼
  ┌─────────────────────────────────────┐
  │ protocol        : PROTOCOL_TLS_CLIENT │  클라이언트용
  │ verify_mode     : CERT_REQUIRED       │  인증서 필수 + 검증
  │ check_hostname  : True                │  이름 대조 켬
  │ minimum_version : (보통 TLS 1.2 이상) │
  │ CA 묶음         : 시스템 것을 읽음     │
  └─────────────────────────────────────┘
        │
        ▼
  이 규칙서를 urlopen · wrap_socket 에 넘긴다
```

- `create_default_context()` 는 안전한 기본값 묶음을 담은 `SSLContext` 를 돌려준다.
- `verify_mode` 가 `CERT_REQUIRED` 라서 서버가 인증서를 내지 않거나 검증에 실패하면 연결이 끊긴다.
- `check_hostname` 이 켜져 있어서 인증서에 적힌 이름(SAN/CN)과 내가 접속한 호스트명이 다르면 연결이 끊긴다.
- 최소 TLS 버전은 원본 주석이 「보통 TLS 1.2 이상」이라고만 적는다 — 정확한 값은 파이썬 · OpenSSL 버전에 따라 다르다(확인 필요).

> **SSLContext** — TLS 연결에 쓸 설정(검증 방식 · 신뢰할 CA · 허용 버전 · 암호 스위트)을 한데 담은 객체.\
> 예: `ctx = ssl.create_default_context()` 로 만든 뒤 여러 연결에 같이 쓴다.

> **호스트명 검증** — 인증서에 적힌 도메인 이름이 실제로 접속한 이름과 같은지 대조하는 일.\
> 예: `www.google.com` 에 붙었는데 인증서가 `evil.example` 용이면 거부한다.

### (2) HTTPS 요청 — `urlopen(…, context=ctx)`

**언제 쓰나** — 표준 라이브러리만으로 HTTPS 주소에서 응답을 받아 올 때 쓴다.

```text
Request(url, headers={'User-Agent': 'Python/3'})
        │
        ▼
urlopen(req, timeout=5, context=ctx)
        │   ├─ TCP 연결
        │   ├─ ctx 규칙대로 TLS 핸드셰이크 + 인증서 검증
        │   └─ HTTP 요청을 암호화해 보냄
        ▼
response.status · response.headers · response.read()
        │
        ▼
json.loads(... .decode())  →  파이썬 dict
```

- `Request` 에 `User-Agent` 를 적는 것은 일부 서버가 이 헤더가 없는 요청을 막기 때문이다.
- `context=ctx` 로 규칙서를 직접 넘긴다 — 원본 주석대로 이는 기본 동작(검증 켬)을 명시적으로 강제하는 것이다.
- `timeout=5` 는 5초 안에 응답이 없으면 예외를 내게 한다.
- 응답 몸통은 바이트라서 `.decode()` 로 문자열을 만든 뒤 `json.loads` 로 푼다.
- 이 블록 전체가 `try/except Exception` 안에 있어서, 네트워크가 없거나 검증이 실패해도 프로그램이 멈추지 않고 예외 클래스 이름만 찍고 다음 절로 넘어간다.

### (3) 소켓을 직접 TLS 로 감싸 인증서 읽기

**언제 쓰나** — HTTP 가 아니라 TLS 연결 자체를 다루거나, 서버 인증서의 만료일 · 발급자 같은 메타정보를 보고 싶을 때(만료 모니터링 · 디버깅) 쓴다.

```text
socket.create_connection((hostname, 443), timeout=5)   ← 평범한 TCP
        │
        ▼
ctx.wrap_socket(sock, server_hostname=hostname)        ← TCP → TLS 업그레이드
        │       (server_hostname: SNI + 이름 대조에 쓰임)
        ▼
ssock.getpeercert()  →  dict
   ├─ 'subject'      주체 (CN, O …)
   ├─ 'issuer'       발급자 (CA)
   ├─ 'version'      X.509 버전
   ├─ 'serialNumber' CA 가 매긴 고유 번호
   ├─ 'notBefore'    유효 시작
   └─ 'notAfter'     유효 끝
ssock.version()      →  협상된 TLS 버전 문자열
ssock.cipher()       →  협상된 암호 스위트
```

- `create_connection` 은 아직 암호화가 없는 TCP 연결이다.
- `wrap_socket` 이 그 위에서 TLS 핸드셰이크를 하고, 암호화된 소켓 `ssock` 을 돌려준다.
- `server_hostname` 은 두 군데에 쓰인다 — 서버에게 「이 이름의 인증서를 달라」고 알리는 SNI, 그리고 받은 인증서와 이름을 대조하는 호스트명 검증이다.
- `getpeercert()` 는 **검증을 통과한** 상대 인증서의 정보를 돌려준다.
- `subject` 와 `issuer` 는 겹겹의 튜플이라서 원본은 `dict(x[0] for x in cert['subject'])` 로 각 묶음의 첫 (키, 값) 쌍만 뽑아 dict 로 만든다(원본에 근거 없음 — 코드에서 추론).
- `version()` 과 `cipher()` 는 인증서가 아니라 **이번 연결에서 합의된** 값이다.
- `with` 두 겹이 끝나면 TLS 소켓과 TCP 소켓이 차례로 닫힌다.

> **SNI** — TLS 핸드셰이크 첫머리에 클라이언트가 접속하려는 호스트 이름을 알리는 것.\
> 예: 한 IP 에 사이트가 여럿이면 서버는 SNI 를 보고 알맞은 인증서를 고른다.

> **암호 스위트** — 키 교환 · 암호화 · 무결성 검사에 쓸 알고리즘의 조합.\
> 예: `ECDHE` 로 키를 나누고 `AES-GCM` 으로 암호화한다.

### (4) 엄격한 컨텍스트를 직접 짜기

**언제 쓰나** — 운영 환경에서 허용 범위를 명시적으로 좁히고 싶을 때 쓴다.

```text
ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)        ← 빈 클라이언트용 규칙서
   │
   ├─ .minimum_version = TLSVersion.TLSv1_2   ← TLS 1.0/1.1 차단
   ├─ .set_ciphers('ECDHE+AESGCM')            ← 강한 조합만
   └─ .load_default_certs()                   ← 시스템 CA 를 신뢰 목록에
   │
   ▼
strict_ctx  (기본 컨텍스트보다 좁은 정책)
```

- `minimum_version` 을 `TLSv1_2` 로 두면 그보다 낮은 TLS 1.0 · 1.1 은 협상되지 않는다 — 원본 주석대로 둘 다 취약점이 많다.
- `ECDHE` 는 전방향 비밀성(Forward Secrecy)을, `AESGCM` 은 인증 암호화를 준다.
- `load_default_certs()` 를 부르지 않으면 신뢰할 CA 가 없는 규칙서가 된다.
- 원본에서 이 절의 `print` 두 줄(「최소 TLS: TLSv1.2」 · 「암호: ECDHE+AESGCM」)은 **고정 문자열**이다 — `strict_ctx` 에서 값을 읽어 오지 않는다.

> **전방향 비밀성** — 서버의 장기 비밀키가 나중에 새어도 과거 대화를 풀 수 없게 하는 성질.\
> 예: 세션마다 ECDHE 로 새 키를 만들면 지난 세션 키를 되살릴 수 없다.

### (5) 검증을 끄면 무엇이 뚫리나 — MITM

**언제 쓰나** — 쓰지 않는다.
원본은 위험을 보여 주려고 학습용으로만 시연한다.

```text
unsafe_ctx = create_default_context()
   ├─ check_hostname = False   → 다른 도메인 인증서여도 통과
   └─ verify_mode = CERT_NONE  → 자체 서명 · 만료 인증서도 통과

  나 ───▶ [공격자: 가짜 인증서 제시] ───▶ 진짜 서버
            ▲
            └─ 검증이 꺼져 있으니 그대로 연결됨
               → 암호화는 되지만 '누구와' 암호화했는지 모름
```

- `check_hostname = False` 는 이름 대조를 끈다 — 남의 도메인 인증서로 위장할 수 있다.
- `verify_mode = CERT_NONE` 은 인증서 검증 자체를 끈다 — 자체 서명 · 만료 인증서까지 모두 받아들인다.
- 둘이 꺼지면 공격자가 중간에 끼어 가짜 인증서를 내밀고 트래픽을 가로챌 수 있다(MITM).
- 원본 코드는 먼저 `check_hostname` 을 끄고 나서 `verify_mode` 를 바꾼다.

> **MITM (중간자 공격)** — 공격자가 통신하는 두 쪽 사이에 끼어 양쪽에 상대인 척하며 내용을 엿보거나 바꾸는 공격.\
> 예: 공용 와이파이에서 가짜 인증서를 내밀어 HTTPS 를 가로챈다.

### (6) 환경 정보 확인

**언제 쓰나** — 내 파이썬이 어떤 TLS 라이브러리 위에서 도는지, 어떤 CA 묶음을 읽는지 점검할 때 쓴다.

```text
ssl.OPENSSL_VERSION            → 링크된 OpenSSL 버전 문자열 (취약점 점검용)
ssl.get_default_verify_paths() → 시스템 CA 번들 파일·디렉터리 경로
```

- 파이썬의 `ssl` 모듈은 OpenSSL 위에서 동작하므로, OpenSSL 버전이 낡으면 취약점도 따라온다.
- CA 경로는 `load_default_certs()` 가 무엇을 읽는지 알려 준다.

## 문법 — 형태와 규칙

```python
import ssl, socket

ctx = ssl.create_default_context()           # 안전한 기본값
host = "example.com"

with socket.create_connection((host, 443), timeout=5) as sock:
    with ctx.wrap_socket(sock, server_hostname=host) as ssock:
        print(ssock.version())               # 합의된 TLS 버전
        cert = ssock.getpeercert()
        print(cert["notAfter"])              # 만료 시각

strict = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
strict.minimum_version = ssl.TLSVersion.TLSv1_2
strict.set_ciphers("ECDHE+AESGCM")
strict.load_default_certs()
```

- 클라이언트 컨텍스트는 `ssl.create_default_context()` 로 시작한다.
- 직접 만들 때는 `ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)` 로 만든 뒤 `load_default_certs()` 로 신뢰 목록을 채운다.
- `wrap_socket` 에는 `server_hostname=` 을 꼭 넘긴다 — SNI 와 이름 대조에 쓰인다.
- HTTPS 는 `urllib.request.urlopen(req, timeout=…, context=ctx)` 로 규칙서를 넘긴다.
- 인증서 정보는 `getpeercert()` · 연결 정보는 `version()` · `cipher()` 로 읽는다.

| 설정 | 값 | 뜻 |
|---|---|---|
| `verify_mode` | `CERT_REQUIRED` | 인증서 필수 + 검증 (기본 컨텍스트) |
| `verify_mode` | `CERT_NONE` | 검증 안 함 — 운영 금지 |
| `check_hostname` | `True` / `False` | 인증서 이름 대조 켬 / 끔 |
| `minimum_version` | `TLSVersion.TLSv1_2` | TLS 1.2 미만 차단 |
| `set_ciphers(…)` | `'ECDHE+AESGCM'` | 전방향 비밀성 + 인증 암호화 조합만 |

## 어디서 틀리나

### 1. 「일단 되게」 하려고 `CERT_NONE` 을 넣는다

인증서 오류를 없애려고 `verify_mode = ssl.CERT_NONE` 을 넣으면 연결은 되지만 MITM 에 그대로 열린다.
원본 팁대로 프로덕션에서는 절대 쓰지 않는다.
자체 서명 인증서는 개발 환경에서만 쓴다.

### 2. 검증은 켰는데 이름 대조를 끈다

`check_hostname = False` 만 해도 「믿을 만한 CA 가 발급한, 하지만 남의 도메인」 인증서를 받아들이게 된다.
인증서가 진짜라는 것과 **내가 부른 상대의** 인증서라는 것은 다른 확인이다.

### 3. 낡은 TLS 버전과 약한 암호를 열어 둔다

TLS 1.0 · 1.1 은 취약점이 많다.
`minimum_version` 을 `TLSv1_2` 이상으로 두고, 암호 스위트는 `ECDHE` · `AES-GCM` 처럼 강한 것으로 좁힌다.

### 4. 설정을 확인한다면서 고정 문자열을 찍는다

원본의 「엄격 설정」 절은 설정 값을 읽지 않고 문자열을 그대로 찍는다.
`set_ciphers` 줄을 지워도 화면 글은 똑같다.
설정이 실제로 걸렸는지 보려면 `strict_ctx.minimum_version` 처럼 객체에서 값을 읽어야 한다.

### 5. 넓은 `except Exception` 이 원인을 가린다

원본은 네트워크가 없는 환경을 대비해 HTTPS 요청과 인증서 조회를 `except Exception` 으로 감싸고 클래스 이름만 찍는다.
그 탓에 「네트워크 없음」과 「인증서 검증 실패」가 같은 꼴로 지나간다.
학습용으로는 편하지만 실무에서는 검증 실패를 따로 다뤄야 한다.

### 6. 인증서 만료를 보지 않는다

인증서에는 `notBefore` · `notAfter` 유효 기간이 있다.
원본 권장사항대로 만료를 모니터링한다(원본 주석: 보통 30일 전 알림).

### 7. 원본 끝의 결과 주석은 실제 `print` 와 어긋난다

원본의 주장 → 코드 맨 끝 주석 블록이 이 코드가 찍는 줄이라고 적는다.
왜 의심스러운가 → 코드는 「=== 인증서 정보 확인 ===」을 찍는데 주석은 「=== 인증서 정보 ===」이고, 「주체:」 뒤 공백 수도 다르다.
또 `ctx.protocol` 을 f-string 에 넣으면 보통 `str()` 꼴이 쓰이는데 주석의 `<_SSLMethod.PROTOCOL_TLS_CLIENT: 16>` 은 `repr()` 꼴이다.
열거형이 f-string 에서 어떤 글자로 찍히는지는 파이썬 버전에 따라 다르다(확인 필요).
주석은 대략의 모습으로만 읽는다.

### 8. 다른 라이브러리는 각자의 기본값을 갖는다

원본 팁대로 `requests` 라이브러리는 기본적으로 인증서 검증이 켜져 있다.
그 기본값을 끄는 옵션을 쓰면 1번과 같은 구멍이 생긴다.
HTTPS 를 쓰는 사이트라면 HSTS 를 적용해 브라우저가 HTTPS 만 쓰게 한다.

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| `create_default_context()` 는 `CERT_REQUIRED` · `check_hostname=True` 로 시작한다 | 파이썬 표준 라이브러리 `ssl` 모듈의 문서화된 동작 (언어 문법이 아니라 라이브러리) |
| 기본 컨텍스트의 최소 TLS 버전은 「보통 1.2 이상」 | 파이썬 버전 · OpenSSL 빌드 설정에 따라 다름(확인 필요) |
| `ctx.protocol` · `verify_mode` 가 찍히는 글자 꼴 | 파이썬 버전의 열거형 출력 방식에 따라 다름(확인 필요) |
| `ssl.OPENSSL_VERSION` · `get_default_verify_paths()` 의 값 | 설치된 OpenSSL 과 운영체제 |
| `version()` · `cipher()` 의 값 | 클라이언트와 서버가 그때그때 협상한 결과 |
| `requests` 는 기본적으로 인증서를 검증한다 | `requests` 라이브러리 (표준 라이브러리 아님) |
| HSTS 로 브라우저가 HTTPS 를 강제한다 | 서버가 보내는 헤더와 브라우저 구현 |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 평범한 HTTPS 요청 | `create_default_context()` + `urlopen(context=ctx)` 또는 `requests` 기본값 | `CERT_NONE` |
| 서버 인증서 만료일 점검 | `create_connection` → `wrap_socket(server_hostname=…)` → `getpeercert()` | 검증을 끈 컨텍스트로 조회 |
| 운영 환경 정책 강화 | `minimum_version = TLSv1_2` · `set_ciphers('ECDHE+AESGCM')` · `load_default_certs()` | TLS 1.0 · 1.1 허용 |
| 개발용 자체 서명 인증서 | 개발 환경에서만 | 프로덕션에 그대로 배포 |
| 설정이 걸렸는지 확인 | 컨텍스트 속성을 직접 읽기 | 고정 문자열 `print` |

## 핵심 문장

1. **`ssl.create_default_context()` 가 출발점이다** — 인증서 검증(`CERT_REQUIRED`)과 호스트명 검증을 켠 채로 시작한다.
2. **인증서 검증은 두 겹이다** — CA 가 서명했나(`verify_mode`), 내가 부른 이름의 것이냐(`check_hostname`).
3. **TLS 소켓은 TCP 소켓을 감싸서 만든다** — `wrap_socket(sock, server_hostname=…)` 뒤에 `getpeercert()` · `version()` · `cipher()` 로 상대와 연결을 들여다본다.
4. **강하게 하려면 범위를 좁힌다** — TLS 1.2 이상, `ECDHE+AESGCM`, 시스템 CA.
5. **검증을 끄면 암호화는 남아도 상대를 모른다** — 그것이 MITM 이고, 그래서 `CERT_NONE` 은 프로덕션 금지다.

## 관련 자료

- [rsa-encryption](../07-rsa-encryption/2-summary.md)
- [fernet-encryption](../06-fernet-encryption/2-summary.md)
- `secure-coding` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- 원본: study-site 항목 데이터 `data/python/security.json` 의 `ssl-tls`

## 용어 풀이

- **TLS** — 네트워크 연결을 암호화하고 상대를 인증하는 규약. SSL 은 그 옛 이름이다.
- **HTTPS** — TLS 위에서 주고받는 HTTP.
- **인증서 (X.509)** — 서버의 이름 · 공개키 · 유효 기간을 CA 가 서명해 묶은 문서.
- **CA** — 인증서를 발급하고 서명하는 인증 기관.
- **SSLContext** — TLS 연결 설정을 담은 객체.
- **`CERT_REQUIRED` / `CERT_NONE`** — 인증서를 꼭 받아 검증함 / 검증하지 않음.
- **호스트명 검증** — 인증서의 SAN/CN 과 접속한 이름을 대조하는 일.
- **SAN / CN** — 인증서에 도메인 이름이 적히는 자리(주체 대체 이름 / 일반 이름).
- **SNI** — 핸드셰이크 때 접속할 호스트 이름을 서버에 알리는 것.
- **핸드셰이크** — 암호화된 대화를 시작하기 전에 버전 · 암호 스위트 · 키를 합의하는 과정.
- **암호 스위트** — 키 교환 · 암호화 · 무결성에 쓸 알고리즘 조합.
- **ECDHE** — 세션마다 새 키를 만드는 키 교환 방식. 전방향 비밀성을 준다.
- **AES-GCM** — 암호화와 위조 검사를 함께 하는 인증 암호화 방식.
- **전방향 비밀성** — 장기 비밀키가 새어도 지난 대화를 못 푸는 성질.
- **MITM** — 통신 중간에 끼어 엿보거나 바꾸는 공격.
- **자체 서명 인증서** — CA 없이 스스로 서명한 인증서.
- **HSTS** — 브라우저에 HTTPS 만 쓰라고 강제하는 정책 헤더.
- **OpenSSL** — 파이썬 `ssl` 모듈이 기대는 TLS 라이브러리.

## 더 들어가면

- `check_hostname` 이 켜진 채로 `verify_mode = CERT_NONE` 을 주면 `ValueError` 가 난다 — 그래서 원본처럼 이름 대조를 먼저 끈다(확인 필요).
- `set_ciphers()` 는 TLS 1.2 이하의 암호 스위트를 고른다. TLS 1.3 의 스위트는 따로 정해져 이 호출로는 바뀌지 않는다(확인 필요).
- 파이썬 3.10 무렵부터 `PROTOCOL_TLS_CLIENT` 의 기본 최소 버전이 TLS 1.2 로 올라갔다고 알려져 있다(확인 필요).
- 기본 소켓 타임아웃이 없는 상태에서 `timeout` 을 빠뜨리면 응답 없는 서버 앞에서 오래 멈출 수 있다(확인 필요).
- `getpeercert()` 는 검증 모드가 `CERT_NONE` 이면 빈 dict 를 돌려준다(확인 필요).
- 운영체제마다 CA 저장소가 달라서, 일부 환경에서는 `certifi` 같은 별도 CA 묶음을 쓰기도 한다(확인 필요).
