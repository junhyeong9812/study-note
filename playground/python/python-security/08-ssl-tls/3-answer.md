# python/python-security/08 — SSL/TLS (보안 통신) — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 검증 모드는 `CERT_REQUIRED`, 호스트명 검증은 `True`

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
첫 줄에는 `CERT_REQUIRED` 를 뜻하는 값이, 둘째 줄에는 `True` 가 담긴다.
`CERT_REQUIRED` 가 `VerifyMode.CERT_REQUIRED` 로 찍힐지 숫자로 찍힐지는 파이썬 버전의 열거형 출력 방식에 따라 다르다(확인 필요).

**왜 그런가**
`create_default_context()` 는 안전한 기본값 묶음으로, 인증서를 꼭 받아 검증하고 이름 대조도 켠 채로 시작한다.
근거: 2-summary 「동작 방식 (1)」 · 「어디서 틀리나 7」.

### 2. 예외 클래스 이름이 든 한 줄이 찍히고 다음 절로 넘어간다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
`  HTTPS 요청 예시 (네트워크 필요): ` 뒤에 실패한 예외의 클래스 이름이 붙은 한 줄이 찍힌다.
`상태:` 줄은 찍히지 않는다.
그다음 `=== 다음 절 ===` 이 찍히며 프로그램이 이어진다.
어떤 클래스 이름이 붙는지는 실패 원인에 달렸다(원본에 근거 없음 — 추론).

**왜 그런가**
`urlopen` 이 예외를 내면 `with` 안의 줄은 건너뛰고 `except Exception` 으로 간다.
넓은 `except` 라서 네트워크 실패든 검증 실패든 같은 꼴로 지나간다.
근거: 2-summary 「동작 방식 (2)」 · 「어디서 틀리나 5」.

### 3. 화면 글은 똑같다 — 고정 문자열이기 때문이다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
`  암호: ECDHE+AESGCM` 이 원래와 똑같이 찍힌다.

**왜 그런가**
이 `print` 는 `strict_ctx` 에서 값을 읽지 않고 문자열을 그대로 찍는다.
그래서 설정이 실제로 걸렸는지와 상관없이 같은 글이 나온다.
설정을 확인하려면 컨텍스트 객체에서 값을 읽어야 한다.
근거: 2-summary 「동작 방식 (4)」 · 「어디서 틀리나 4」.

### 4. 진짜 인증서라도 「남의 것」일 수 있기 때문이다

CA 서명 검증은 「믿을 만한 기관이 발급했나」만 확인한다.
이름 대조를 끄면 CA 가 정당하게 발급한 **다른 도메인**의 인증서로 위장한 상대도 통과한다.
그러면 공격자가 중간에 끼어도 막지 못한다(MITM).
근거: 2-summary 「동작 방식 (1)」 · 「동작 방식 (5)」 · 「어디서 틀리나 2」.

### 5. SNI 와 호스트명 검증

첫째, 핸드셰이크 첫머리에 서버에게 접속하려는 이름을 알려(SNI) 알맞은 인증서를 받게 한다.
둘째, 받은 인증서의 이름과 이 이름을 대조하는 호스트명 검증에 쓰인다.
근거: 2-summary 「동작 방식 (3)」.

### 6. 자체 서명 · 만료 인증서까지 전부 — 개발 환경에서만, 그것도 자체 서명까지만

`verify_mode = CERT_NONE` 은 인증서 검증 자체를 꺼서 자체 서명 인증서도 만료된 인증서도 받아들인다.
`check_hostname = False` 까지 겹치면 다른 도메인 인증서로도 위장할 수 있다.
원본 권장사항은 `CERT_NONE` 을 프로덕션에서 절대 쓰지 말고, 자체 서명 인증서는 개발 환경에서만 쓰라고 한다.
근거: 2-summary 「동작 방식 (5)」 · 「어디서 틀리나 1」 · 「언제 쓰고 언제 안 쓰나」.

### 7. TLS 1.0 · 1.1 이 막힌다 — 취약점이 많아서다

`minimum_version = TLSVersion.TLSv1_2` 는 1.2 미만, 곧 TLS 1.0 과 1.1 을 협상하지 않게 한다.
두 버전은 취약점이 많아서 원본 권장사항이 비활성화를 요구한다.
TLS 1.2 와 그 이상은 그대로 허용된다.
근거: 2-summary 「동작 방식 (4)」 · 「어디서 틀리나 3」.

### 8. `getpeercert()` 는 인증서, `version()` · `cipher()` 는 연결 합의

`getpeercert()` 는 검증을 통과한 상대 인증서의 정보(주체 · 발급자 · X.509 버전 · 시리얼 · 유효 기간)를 준다.
`version()` 과 `cipher()` 는 인증서가 아니라 이번 연결에서 클라이언트와 서버가 합의한 TLS 버전과 암호 스위트를 준다.
그래서 같은 서버라도 클라이언트 설정이 다르면 뒤의 둘은 달라질 수 있다.
근거: 2-summary 「동작 방식 (3)」 · 「구현 세부사항 대 언어 보장」.

### 9. `requests` 는 같은 검증을 기본으로 켜 두고, HSTS 는 HTTPS 자체를 강제한다

`requests` 라이브러리는 기본적으로 인증서 검증이 켜져 있어 `create_default_context()` 를 쓴 것과 같은 방향이다 — 그 기본값을 끄면 `CERT_NONE` 과 같은 구멍이 생긴다.
HSTS 는 인증서를 확인하는 일이 아니라, 브라우저가 처음부터 HTTPS 만 쓰게 강제해 TLS 연결이 일어나도록 만드는 정책이다.
근거: 2-summary 「어디서 틀리나 8」 · 「구현 세부사항 대 언어 보장」.

## 실습 정답

### 실습 1. TLS 점검 스크립트 만들기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. 기본 컨텍스트와 네 값 | `ctx = ssl.create_default_context()` · `ctx.protocol` · `ctx.verify_mode` · `ctx.check_hostname` · `ctx.minimum_version` |
| 2. `User-Agent` · `context=` · 타임아웃 5초 | `urllib.request.Request(url, headers={'User-Agent': 'Python/3'})` · `urlopen(req, timeout=5, context=ctx)` |
| 3. JSON 파싱 · URL · 상태 · 헤더 셋 | `json.loads(response.read().decode())` · `response.status` · `dict(list(response.headers.items())[:3])` |
| 4. 예외 클래스 이름 | `except Exception as e:` · `type(e).__name__` |
| 5. TCP → TLS 로 감싸는 함수 | `get_cert_info` · `socket.create_connection((hostname, port), timeout=5)` · `ctx.wrap_socket(sock, server_hostname=hostname)` |
| 6. 인증서 · 연결 정보 dict | `ssock.getpeercert()` · `dict(x[0] for x in cert['subject'])` · `cert['serialNumber']` · `ssock.version()` · `ssock.cipher()` |
| 7. 구글 인증서 조회와 예외 처리 | `get_cert_info('www.google.com')` · 두 번째 `try/except` |
| 8. 엄격한 컨텍스트 | `ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)` · `minimum_version = ssl.TLSVersion.TLSv1_2` · `set_ciphers('ECDHE+AESGCM')` · `load_default_certs()` |
| 9. 위험 시연 | `unsafe_ctx.check_hostname = False` · `unsafe_ctx.verify_mode = ssl.CERT_NONE` |
| 10. 환경 정보 | `ssl.OPENSSL_VERSION` · `ssl.get_default_verify_paths()` |
| 11. 권장사항 일곱 줄 | `--- SSL/TLS 보안 권장사항 ---` 아래 `print` 일곱 개 |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`python/python-security/reference/ssl-tls.py`

```python
# [보안 & 암호화] SSL/TLS (보안 통신)
# 설명: ssl 모듈로 인증서 검증, HTTPS 연결, 보안 소켓을 구성하고 인증서 정보를 확인
# 팁: 항상 ssl.create_default_context()를 사용하여 인증서 검증을 활성화한다. verify_mode=CERT_NONE은 MITM 공격에 취약하므로 프로덕션에서 절대 사용하지 않는다. TLS 1.2 이상만 허용하고, 강력한 암호 스위트(ECDHE+AES-GCM)를 사용한다. requests 라이브러리는 기본적으로 인증서 검증이 활성화되어 있다.

# ssl: 표준 TLS 컨텍스트/소켓 처리
import ssl
# socket: 저수준 TCP 연결 (인증서 조회용)
import socket
# urllib: HTTPS 클라이언트
import urllib.request
# json: 응답 파싱
import json

# === SSL 컨텍스트 기본 ===
print("=== SSL 컨텍스트 ===")

# 기본 컨텍스트 (인증서 검증 활성)
# create_default_context: 안전한 기본값 묶음 (최신 TLS, 검증 활성)
ctx = ssl.create_default_context()
print(f"프로토콜: {ctx.protocol}")
# CERT_REQUIRED: 인증서 필수 + 검증
print(f"검증 모드: {ctx.verify_mode}")
# 호스트명 검증: SAN/CN 일치 확인 (MITM 방어)
print(f"호스트명 검증: {ctx.check_hostname}")
# 최소 TLS 버전: 보통 TLS 1.2 이상
print(f"최소 TLS 버전: {ctx.minimum_version}")
print()

# === HTTPS 요청 (urllib) ===
print("=== HTTPS 요청 ===")
try:
    # 기본 SSL 컨텍스트 사용 (인증서 검증)
    url = "https://httpbin.org/get"
    # User-Agent 명시 (일부 서버는 미지정 시 차단)
    req = urllib.request.Request(url, headers={'User-Agent': 'Python/3'})
    # context=ctx로 인증서 검증 강제 (기본 동작)
    with urllib.request.urlopen(req, timeout=5, context=ctx) as response:
        data = json.loads(response.read().decode())
        print(f"  URL: {url}")
        print(f"  상태: {response.status}")
        print(f"  헤더 일부: {dict(list(response.headers.items())[:3])}")
except Exception as e:
    # 네트워크 미연결 환경 대비 (학습용)
    print(f"  HTTPS 요청 예시 (네트워크 필요): {type(e).__name__}")
print()

# === 인증서 정보 확인 ===
print("=== 인증서 정보 확인 ===")

# 서버 인증서 메타정보 조회 (만료 모니터링/디버깅용)
def get_cert_info(hostname, port=443):
    """서버의 SSL 인증서 정보 조회"""
    ctx = ssl.create_default_context()
    # TCP 연결
    with socket.create_connection((hostname, port), timeout=5) as sock:
        # wrap_socket: TCP → TLS 업그레이드, server_hostname은 SNI/검증용
        with ctx.wrap_socket(sock, server_hostname=hostname) as ssock:
            # getpeercert: 검증된 피어 인증서 정보
            cert = ssock.getpeercert()
            return {
                # 주체 (CN, O 등)
                'subject': dict(x[0] for x in cert['subject']),
                # 발급자 (CA)
                'issuer': dict(x[0] for x in cert['issuer']),
                # X.509 버전
                'version': cert['version'],
                # 시리얼 번호 (CA가 발급한 고유 식별자)
                'serial': cert['serialNumber'],
                # 유효 기간
                'notBefore': cert['notBefore'],
                'notAfter': cert['notAfter'],
                # 협상된 TLS 버전
                'protocol': ssock.version(),
                # 협상된 암호 스위트
                'cipher': ssock.cipher(),
            }

try:
    # 구글 인증서 정보 조회
    info = get_cert_info('www.google.com')
    print(f"  주체:     {info['subject']}")
    print(f"  발급자:   {info['issuer']}")
    print(f"  유효기간: {info['notBefore']} ~ {info['notAfter']}")
    print(f"  프로토콜: {info['protocol']}")
    print(f"  암호스위트: {info['cipher']}")
except Exception as e:
    print(f"  인증서 조회 예시 (네트워크 필요): {type(e).__name__}")
print()

# === SSL 컨텍스트 설정 ===
print("=== SSL 컨텍스트 설정 ===")

# 엄격한 컨텍스트
# 운영 환경에서 명시적으로 강한 정책 적용
strict_ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
# TLS 1.0/1.1 차단 (취약점 다수)
strict_ctx.minimum_version = ssl.TLSVersion.TLSv1_2  # TLS 1.2 이상만
# ECDHE: 전방향 비밀성 (Forward Secrecy), AESGCM: 인증 암호화
strict_ctx.set_ciphers('ECDHE+AESGCM')  # 강력한 암호만
# 시스템 신뢰 저장소 사용
strict_ctx.load_default_certs()  # 시스템 CA 인증서
print("엄격 설정:")
print(f"  최소 TLS: TLSv1.2")
print(f"  암호: ECDHE+AESGCM")
print()

# === 인증서 검증 비활성화 (테스트용, 실무 금지!) ===
print("=== 검증 비활성화 (주의!) ===")
# 학습/디버깅용 위험 설정 시연 - 실무 사용 금지
unsafe_ctx = ssl.create_default_context()
# 호스트명 검증 끄기 → 다른 도메인 인증서로 위장 가능
unsafe_ctx.check_hostname = False
# 인증서 검증 자체를 끄기 → 자체 서명/만료 인증서 모두 허용
unsafe_ctx.verify_mode = ssl.CERT_NONE
print("  check_hostname = False")
print("  verify_mode = CERT_NONE")
# MITM 공격: 공격자가 중간에서 가짜 인증서로 트래픽 가로채기 가능
print("  ⚠ 절대 프로덕션에서 사용 금지! (MITM 공격에 취약)")
print()

# === SSL 버전/암호 정보 ===
print("=== SSL 프로토콜 정보 ===")
# 시스템에 설치된 OpenSSL 버전 (취약점 점검 시 활용)
print(f"OpenSSL 버전: {ssl.OPENSSL_VERSION}")
# 시스템 CA 번들 경로
print(f"기본 CA 경로: {ssl.get_default_verify_paths()}")
print()

# === 보안 권장사항 ===
print("--- SSL/TLS 보안 권장사항 ---")
# 1. 기본 컨텍스트 사용
print("1. 항상 인증서 검증 활성화 (create_default_context)")
# 2. 구버전 TLS 차단
print("2. TLS 1.2 이상만 허용 (TLS 1.0/1.1 비활성화)")
# 3. 강한 암호 스위트
print("3. 강력한 암호 스위트 사용 (ECDHE, AES-GCM)")
# 4. 만료 알림 (보통 30일 전 알림)
print("4. 인증서 만료 모니터링")
# 5. HSTS: 브라우저 HTTPS 강제
print("5. HSTS(HTTP Strict Transport Security) 적용")
# 6. 검증 비활성화 절대 금지
print("6. verify_mode = CERT_NONE은 절대 프로덕션 사용 금지")
# 7. 자체 서명은 dev에서만
print("7. 자체 서명 인증서는 개발 환경에서만 사용")

# 출력:
# === SSL 컨텍스트 ===
# 프로토콜: <_SSLMethod.PROTOCOL_TLS_CLIENT: 16>
# 검증 모드: VerifyMode.CERT_REQUIRED
# === HTTPS 요청 ===
# 상태: 200
# === 인증서 정보 ===
# 주체: {'commonName': 'www.google.com'}
# 프로토콜: TLSv1.3
```

**실행 결과** — 실행하지 않음 — 실행 환경 · 바깥 네트워크에 따라 달라지는 예제다.

**풀이 요점**
- 모든 연결의 출발점은 `create_default_context()` 다 — 검증과 이름 대조가 켜진 채로 시작한다.
- 인증서 조회는 `create_connection` 으로 TCP 를 열고 `wrap_socket(…, server_hostname=…)` 으로 TLS 로 올리는 두 겹 `with` 다.
- `getpeercert()` 의 주체 · 발급자는 겹겹의 튜플이라 `dict(x[0] for x in …)` 로 펴서 읽는다.
- 엄격한 컨텍스트는 빈 `PROTOCOL_TLS_CLIENT` 에서 시작하므로 `load_default_certs()` 를 빠뜨리면 신뢰할 CA 가 없다.
- 위험 시연은 이름 대조를 먼저 끄고 나서 `CERT_NONE` 으로 바꾸는 차례다 — 실무에서는 쓰지 않는다.
- 네트워크 절은 넓은 `except` 로 감싸 끝까지 진행되지만, 그 대가로 실패 원인이 클래스 이름 하나로 뭉쳐진다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — 실행 환경 · 바깥 네트워크에 따라 달라지는 예제다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
