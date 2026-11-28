# python/python-security/08 — SSL/TLS (보안 통신) — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 기본 컨텍스트를 만든 직후의 두 속성 (예측)

```python
# 질문용 발췌
import ssl
ctx = ssl.create_default_context()
print(f"검증 모드: {ctx.verify_mode}")
print(f"호스트명 검증: {ctx.check_hostname}")
```

- 두 줄에는 각각 어떤 설정 값이 담겨 나오나?

### 2. 네트워크가 끊긴 상태에서 HTTPS 요청 절 (예측)

```python
# 질문용 발췌
try:
    with urllib.request.urlopen(req, timeout=5, context=ctx) as response:
        print(f"  상태: {response.status}")
except Exception as e:
    print(f"  HTTPS 요청 예시 (네트워크 필요): {type(e).__name__}")
print("=== 다음 절 ===")
```

- 연결이 실패하면 어떤 꼴의 줄이 찍히고, 그 뒤 프로그램은 어떻게 되나?

### 3. `set_ciphers` 줄을 지운 엄격 설정 (예측)

```python
# 질문용 발췌
strict_ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
strict_ctx.minimum_version = ssl.TLSVersion.TLSv1_2
# strict_ctx.set_ciphers('ECDHE+AESGCM')   ← 주석 처리함
strict_ctx.load_default_certs()
print(f"  암호: ECDHE+AESGCM")
```

- 이 줄이 화면에 찍히는 글은 원래 코드와 비교해 어떻게 되나?

### 4. 인증서가 유효한데도 `check_hostname` 이 필요한 까닭 (왜)

- CA 서명이 멀쩡한 인증서라도 이름 대조를 끄면 왜 위험한가?

### 5. `wrap_socket` 에 `server_hostname` 을 넘기는 까닭 (왜)

- 이 인자는 TLS 연결에서 어떤 두 가지 일에 쓰이나?

### 6. `CERT_NONE` 이 받아들여 버리는 범위 (경계)

- 검증을 끈 컨텍스트는 어떤 인증서까지 통과시키고, 개발 환경에서는 어디까지 허용되나?

### 7. `minimum_version = TLSv1_2` 가 긋는 선 (경계)

- 이 설정으로 막히는 TLS 버전은 무엇이고, 그 버전들을 막는 까닭은 무엇인가?

### 8. `getpeercert()` 와 `version()` · `cipher()` 의 차이 (연결)

- 셋 중 인증서에서 오는 정보와 이번 연결의 합의에서 오는 정보는 각각 무엇인가?

### 9. `ssl` 컨텍스트와 `requests` · HSTS (연결)

- `requests` 의 기본 동작과 HSTS 는 이 문서의 인증서 검증과 각각 어떤 관계인가?

## 실습

### 실습 1. TLS 점검 스크립트 만들기

**만들 것** — 기본 컨텍스트 확인, HTTPS 요청, 서버 인증서 조회, 엄격한 컨텍스트, 검증을 끈 위험 컨텍스트 시연, 환경 정보와 권장사항을 차례로 찍는 파이썬 스크립트 하나.

**준비물** — 표준 라이브러리(`ssl` · `socket` · `urllib.request` · `json`)만 쓴다. HTTPS 요청과 인증서 조회는 인터넷 연결이 있어야 실제 응답을 받는다.

**요구 조건**

1단계 — 기본 컨텍스트
1. `ssl.create_default_context()` 로 컨텍스트를 만들고 `protocol` · `verify_mode` · `check_hostname` · `minimum_version` 네 값을 찍는다.

2단계 — HTTPS 요청
2. `User-Agent` 헤더를 단 `Request` 를 만들고, 1단계 컨텍스트를 `context=` 로, 타임아웃 5초로 `urlopen` 한다.
3. 응답 몸통을 디코드해 JSON 으로 풀고, URL · 상태 코드 · 헤더 앞 세 개를 찍는다.
4. 어떤 예외가 나도 멈추지 않고 예외 클래스 이름을 찍는다.

3단계 — 인증서 정보
5. `get_cert_info(hostname, port=443)` 함수를 만든다: TCP 로 연결하고, `server_hostname` 을 넘겨 TLS 로 감싼 뒤 dict 를 돌려준다.
6. dict 에는 주체 · 발급자(각각 dict 로 변환) · X.509 버전 · 시리얼 번호 · 유효 시작 · 유효 끝 · 협상된 TLS 버전 · 협상된 암호 스위트를 담는다.
7. `www.google.com` 으로 불러 주체 · 발급자 · 유효기간 · 프로토콜 · 암호스위트를 찍고, 예외가 나면 클래스 이름을 찍는다.

4단계 — 엄격한 컨텍스트
8. `PROTOCOL_TLS_CLIENT` 로 빈 컨텍스트를 만들고, 최소 버전 TLS 1.2 · 암호 `ECDHE+AESGCM` · 시스템 CA 를 건다.

5단계 — 위험 시연
9. 기본 컨텍스트를 하나 더 만들어 호스트명 검증을 끄고 검증 모드를 `CERT_NONE` 으로 바꾼 뒤, 경고 문구를 찍는다.

6단계 — 환경과 권장사항
10. OpenSSL 버전과 기본 CA 경로를 찍는다.
11. 보안 권장사항 일곱 줄을 찍는다.

**시작 코드**

```python
import ssl
import socket
import urllib.request
import json

print("=== SSL 컨텍스트 ===")
ctx = None  # TODO: 안전한 기본값 컨텍스트
# TODO: protocol · verify_mode · check_hostname · minimum_version 찍기
print()

print("=== HTTPS 요청 ===")
try:
    url = "https://httpbin.org/get"
    req = None  # TODO: User-Agent 'Python/3' 를 단 Request
    # TODO: urlopen(…, timeout=5, context=…) 로 열고 JSON 파싱
    #       URL · 상태 · 헤더 앞 세 개 찍기
except Exception as e:
    print(f"  HTTPS 요청 예시 (네트워크 필요): {type(e).__name__}")
print()

print("=== 인증서 정보 확인 ===")

def get_cert_info(hostname, port=443):
    """서버의 SSL 인증서 정보 조회"""
    # TODO: 컨텍스트 → TCP 연결(timeout=5) → TLS 로 감싸기(server_hostname)
    # TODO: getpeercert() 로 읽어 dict 반환
    #       subject · issuer · version · serial · notBefore · notAfter · protocol · cipher
    pass

try:
    info = get_cert_info('www.google.com')
    print(f"  주체:     {info['subject']}")
    print(f"  발급자:   {info['issuer']}")
    print(f"  유효기간: {info['notBefore']} ~ {info['notAfter']}")
    print(f"  프로토콜: {info['protocol']}")
    print(f"  암호스위트: {info['cipher']}")
except Exception as e:
    print(f"  인증서 조회 예시 (네트워크 필요): {type(e).__name__}")
print()

print("=== SSL 컨텍스트 설정 ===")
strict_ctx = None  # TODO: 클라이언트용 빈 컨텍스트
# TODO: 최소 TLS 1.2 · 암호 'ECDHE+AESGCM' · 시스템 CA
print("엄격 설정:")
print(f"  최소 TLS: TLSv1.2")
print(f"  암호: ECDHE+AESGCM")
print()

print("=== 검증 비활성화 (주의!) ===")
unsafe_ctx = None  # TODO: 기본 컨텍스트
# TODO: 호스트명 검증 끄기 → 검증 모드 CERT_NONE
print("  check_hostname = False")
print("  verify_mode = CERT_NONE")
print("  ⚠ 절대 프로덕션에서 사용 금지! (MITM 공격에 취약)")
print()

print("=== SSL 프로토콜 정보 ===")
# TODO: OpenSSL 버전 · 기본 CA 경로 찍기
print()

print("--- SSL/TLS 보안 권장사항 ---")
print("1. 항상 인증서 검증 활성화 (create_default_context)")
print("2. TLS 1.2 이상만 허용 (TLS 1.0/1.1 비활성화)")
print("3. 강력한 암호 스위트 사용 (ECDHE, AES-GCM)")
print("4. 인증서 만료 모니터링")
print("5. HSTS(HTTP Strict Transport Security) 적용")
print("6. verify_mode = CERT_NONE은 절대 프로덕션 사용 금지")
print("7. 자체 서명 인증서는 개발 환경에서만 사용")
```

**확인 방법** — `python ssl-tls.py` 로 돌려 여섯 절의 제목이 차례로 찍히는지 본다. 인터넷이 연결돼 있으면 HTTPS 상태 코드와 인증서 주체가, 끊겨 있으면 예외 클래스 이름이 찍히고 끝까지 진행되는지 확인한다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
