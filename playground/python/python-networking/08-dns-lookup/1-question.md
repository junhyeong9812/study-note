# python/python-networking/08 — DNS 조회와 리졸버 — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 같은 캐시에 세 번 물으면 (예측)

```python
# 질문용 발췌
dns = DNSCache(ttl=60)
dns.resolve('www.google.com')
dns.resolve('www.google.com')
dns.resolve('www.python.org')
print(f"\n캐시 항목: {len(dns.cache)}개")
```

- 화면에 찍히는 줄의 차례와 각 줄의 꼬리표(`[...]`)는 무엇인가?
- 마지막 줄의 항목 수는 몇인가?

### 2. 없는 이름을 캐시에 넘기면 (예측)

```python
# 질문용 발췌
dns = DNSCache(ttl=60)
r = dns.resolve('no-such-host.invalid')
print(r, len(dns.cache))
```

- 이름 조회가 실패한다고 할 때, `resolve` 안에서 찍히는 줄과 마지막 `print` 의 두 값은 무엇인가?

### 3. 61초 뒤에 같은 이름을 다시 물으면 (예측)

- `DNSCache(ttl=60)` 으로 `www.google.com` 을 한 번 조회하고 61초 뒤 다시 `resolve` 를 부르면, 어떤 꼬리표가 어떤 차례로 찍히고 캐시 항목 수는 어떻게 되나?

### 4. `getaddrinfo` 가 권장되는 까닭 (왜)

- 이름 → 주소 변환에 왜 `gethostbyname` 보다 `getaddrinfo` 가 권장되나?

### 5. 패킷을 보내지 않는 UDP `connect` 로 내 IP 를 아는 까닭 (왜)

- `get_local_ip` 는 실제 패킷을 보내지 않는데 어떻게 내 컴퓨터의 바깥쪽 IP 를 알아내나?

### 6. 포트 확인에 `connect_ex` 를 쓰는 까닭 (왜)

- `check_port` 는 왜 `connect` 가 아니라 `connect_ex` 를 쓰나?

### 7. `check_port` 의 「닫힘」이 뜻하는 범위 (경계)

- `check_port` 가 「닫힘」을 찍었을 때, 그것만으로 「그 포트에 서비스가 없다」고 말할 수 있나?

### 8. 「TTL 기반」 캐시가 실제 DNS 와 어긋나는 지점 (경계)

- `DNSCache` 의 TTL 은 실제 DNS 레코드의 TTL 과 어떤 관계이고, 그 때문에 어떤 일이 생길 수 있나?

### 9. 정방향 조회와 역방향 조회의 짝 (연결)

- `gethostbyname_ex` 와 `gethostbyaddr` 는 입력 · 결과 모양 · 실패 예외에서 무엇이 같고 무엇이 다른가?

## 실습

### 실습 1. DNS 조회 · 로컬 정보 · 포트 확인 · TTL 캐시를 한 스크립트로

**만들 것** — `socket` 모듈로 정방향 · 역방향 · `getaddrinfo` 조회를 해 보고, 내 컴퓨터 정보와 로컬 포트 상태를 확인한 뒤, TTL 캐시 클래스로 반복 조회를 줄이는 스크립트를 만든다.

**준비물** — 표준 라이브러리만 쓴다. 이름 조회 부분은 인터넷(DNS)에 닿을 수 있어야 결과가 나온다.

**요구 조건**

1단계 — 기본 조회
1. `www.google.com` 을 `gethostbyname` 으로 조회해 `gethostbyname('<이름>') = <IP>` 꼴로 찍는다.
2. 같은 이름을 `gethostbyname_ex` 로 조회해 호스트 · 별칭 · IP 를 한 줄씩 찍는다.
3. 두 정방향 조회는 `socket.gaierror` 를 잡아 「조회 실패」 메시지를 찍는다.
4. `8.8.8.8` 을 `gethostbyaddr` 로 역방향 조회해 호스트 · 별칭 · IP 를 한 줄씩 찍고, `socket.herror` 를 잡아 「역방향 실패」를 찍는다.

2단계 — `getaddrinfo`
5. `resolve_host(hostname, port=80)` 함수는 `getaddrinfo` 를 TCP 로 좁혀 부르고, 결과마다 `family`(`'IPv4'` · `'IPv6'`) · `ip` · `port` 딕셔너리를 리스트에 담아 돌려준다.
6. 조회 실패(`gaierror`) 때는 메시지를 찍고 빈 리스트를 돌려준다.
7. `www.google.com` · `www.python.org` 에 대해 호스트 이름을 찍고, 결과를 최대 4개까지 `<family>: <ip>:<port>` 꼴로 찍는다.

3단계 — 로컬 정보
8. `gethostname()` 으로 호스트명을, `getfqdn()` 으로 FQDN 을 찍는다(FQDN 에서 예외가 나면 그냥 넘어간다).
9. `get_local_ip()` 는 UDP 소켓을 `8.8.8.8:80` 에 `connect` 하고 `getsockname()` 의 IP 를 돌려준다. 예외가 나면 `'127.0.0.1'` 을 돌려준다.

4단계 — 포트 확인
10. `check_port(host, port, timeout=1.0)` 은 IPv4 TCP 소켓에 타임아웃을 걸고 `connect_ex` 결과가 `0` 이면 `True`, 아니면 `False`, 예외가 나면 `False` 를 돌려준다.
11. HTTP 80 · HTTPS 443 · SSH 22 를 `127.0.0.1` 에서 타임아웃 0.5초로 확인해 `열림` · `닫힘` 을 찍는다.

5단계 — TTL 캐시
12. `DNSCache(ttl=300)` 은 `호스트명 → (IP, 만료 시각)` 딕셔너리를 가진다.
13. `resolve(hostname)` 은 만료 전 캐시면 `[캐시 히트]` 를 찍고 캐시 IP 를 돌려주고, 만료되었으면 `[캐시 만료]` 를 찍고 다시 조회한다.
14. 실제 조회는 `gethostbyname` 으로 하고, 성공하면 `(ip, 지금 + ttl)` 로 저장한 뒤 `[DNS 조회]` 를 찍고 IP 를 돌려준다. 실패하면 `None` 을 돌려준다.
15. `clear()` 는 캐시를 비운다.
16. `ttl=60` 캐시로 `www.google.com` 두 번, `www.python.org` 한 번 조회한 뒤 캐시 항목 수를 찍는다.

6단계 — 마무리
17. 다섯 가지 도구(`gethostbyname` · `getaddrinfo` · `gethostbyaddr` · `connect_ex` · DNS 캐시)를 한 줄씩 요약해 찍는다.

**시작 코드**

```python
"""DNS 조회와 리졸버: socket, 호스트 조회"""
import socket
import time
from typing import List, Dict

# === 1. 기본 DNS 조회 ===
print("=== 1. 기본 DNS 조회 ===")
hostname = 'www.google.com'
try:
    ip = ...  # TODO: 이름 → IPv4 하나
    print(f"gethostbyname('{hostname}') = {ip}")
except ...:  # TODO: 이름 조회 실패 예외
    print("조회 실패")

try:
    host_info = ...  # TODO: 이름 → (호스트, 별칭, IP 목록)
    print(f"\ngethostbyname_ex('{hostname}'):")
    # TODO: 호스트 · 별칭 · IP 를 한 줄씩
except socket.gaierror as e:
    print(f"조회 실패: {e}")

try:
    reverse = ...  # TODO: '8.8.8.8' 역방향 조회
    print(f"\n역방향 DNS('8.8.8.8'):")
    # TODO: 호스트 · 별칭 · IP 를 한 줄씩
except ...:  # TODO: 역방향 실패 예외
    print("역방향 실패")

# === 2. getaddrinfo (권장) ===
print("\n=== 2. getaddrinfo (권장) ===")

def resolve_host(hostname: str, port: int = 80) -> List[Dict]:
    results = []
    # TODO: getaddrinfo 를 TCP 로 좁혀 부르고
    #       (family, socktype, proto, canonname, sockaddr) 를 풀어
    #       {'family', 'ip', 'port'} 딕셔너리로 담는다. 실패하면 메시지만 찍는다.
    return results

for host in ['www.google.com', 'www.python.org']:
    results = resolve_host(host)
    print(f"\n{host}:")
    # TODO: 최대 4개를 "  <family>: <ip>:<port>" 꼴로

# === 3. 로컬 네트워크 정보 ===
print("\n=== 3. 로컬 네트워크 정보 ===")
# TODO: 호스트명과 FQDN 을 찍는다 (FQDN 예외는 무시)

def get_local_ip() -> str:
    # TODO: UDP 소켓을 8.8.8.8:80 에 connect → 내 쪽 IP 반환, 실패 시 루프백
    ...

print(f"로컬 IP: {get_local_ip()}")

# === 4. 간단한 포트 확인 ===
print("\n=== 4. 간단한 포트 확인 ===")

def check_port(host: str, port: int, timeout: float = 1.0) -> bool:
    # TODO: TCP 소켓 + 타임아웃 + connect_ex 결과로 판정
    ...

common_ports = {'HTTP': 80, 'HTTPS': 443, 'SSH': 22}
for name, port in common_ports.items():
    status = ...  # TODO: 127.0.0.1, 타임아웃 0.5
    print(f"  127.0.0.1:{port} ({name}): {'열림' if status else '닫힘'}")

# === 5. DNS 캐시 패턴 ===
print("\n=== 5. DNS 캐시 패턴 ===")

class DNSCache:
    def __init__(self, ttl: int = 300):
        self.cache = {}  # hostname -> (ip, expire_time)
        self.ttl = ttl

    def resolve(self, hostname: str) -> str:
        now = time.time()
        # TODO: 캐시 확인 → 히트면 "[캐시 히트]" 후 반환, 만료면 "[캐시 만료]"
        # TODO: 실제 조회 → 저장 → "[DNS 조회]" 후 반환, 실패 시 None
        ...

    def clear(self):
        ...  # TODO

dns = DNSCache(ttl=60)
# TODO: www.google.com 두 번, www.python.org 한 번

print(f"\n캐시 항목: {len(dns.cache)}개")

print("\n=== 핵심 정리 ===")
# TODO: 다섯 도구를 한 줄씩 요약
```

**확인 방법** — `python dns-lookup.py` 로 돌려, 다섯 구역 제목이 차례로 나오는지, 5번 구역에서 `[DNS 조회]` → `[캐시 히트]` → `[DNS 조회]` 차례로 찍히고 캐시 항목이 2개인지 본다. IP 값 자체는 환경마다 다르다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
