# python/python-networking/08 — DNS 조회와 리졸버 — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 조회 → 히트 → 조회, 항목은 2개

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
  [DNS 조회] www.google.com -> <IP>
  [캐시 히트] www.google.com -> <같은 IP>
  [DNS 조회] www.python.org -> <IP>

캐시 항목: 2개
```

`<IP>` 자리의 값은 조회하는 환경마다 다르다.
조회가 모두 성공한다는 가정이다.

**왜 그런가**

- 첫 호출 때 캐시가 비어 있으니 `gethostbyname` 으로 조회하고 `(ip, now + 60)` 을 저장한다.
- 두 번째 호출은 곧바로 이어지므로 `now < expire` 가 참이라 DNS 에 묻지 않고 캐시 값을 준다.
- `www.python.org` 는 캐시에 없는 새 키라 조회하고 저장한다.
- 키가 둘이므로 `len(dns.cache)` 는 2다.
- 근거: 2-summary 「동작 방식 (6)」.

### 2. 아무것도 찍히지 않고 `None 0`

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
None 0
```

**왜 그런가**

- 캐시가 비어 있어 캐시 확인 단계는 건너뛴다 — `[캐시 히트]` · `[캐시 만료]` 모두 찍히지 않는다.
- `gethostbyname` 이 `gaierror` 를 내면 `except` 가 받아 `None` 을 돌려준다. 이 `except` 에는 `print` 가 없다.
- 저장은 조회 성공 뒤에만 하므로 캐시는 그대로 비어 있다.
- 근거: 2-summary 「동작 방식 (6)」 · 「어디서 틀리나 6」.

### 3. `[캐시 만료]` 다음 `[DNS 조회]`, 항목 수는 그대로

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
  [DNS 조회] www.google.com -> <IP>
  [캐시 만료] www.google.com
  [DNS 조회] www.google.com -> <IP>
```

캐시 항목 수는 1개로 그대로다.

**왜 그런가**

- 61초 뒤에는 `now < expire` 가 거짓이라 `[캐시 만료]` 를 찍고 `if` 블록을 빠져나온다.
- 만료된 경우 `return` 이 없으므로 아래의 실제 조회로 내려간다.
- 조회에 성공하면 같은 키 `www.google.com` 에 새 `(ip, now + 60)` 을 덮어쓴다 — 키가 늘지 않는다.
- 근거: 2-summary 「동작 방식 (6)」.

### 4. IPv4 · IPv6 를 모두 다루고 접속 정보를 함께 주기 때문

- `gethostbyname` 은 IPv4 주소 하나만 돌려준다 — IPv6 만 쓰는 상대나 여러 주소 중 고를 상황을 다룰 수 없다.
- `getaddrinfo` 는 IPv4 와 IPv6 결과를 한 번에 주고, 결과마다 주소 체계 · 소켓 종류 · 프로토콜 · `(IP, 포트)` 를 함께 담는다.
- 포트와 프로토콜(`proto=IPPROTO_TCP`)을 같이 넘기므로 결과를 접속에 바로 쓸 수 있다.
- 근거: 2-summary 「동작 방식 (1)」 · 「동작 방식 (3)」, 원본 팁.

### 5. UDP `connect` 가 커널에게 출발 주소를 고르게 하기 때문

- UDP 에는 연결 맺기 절차가 없어서, `connect` 는 패킷을 보내지 않고 「보낼 목적지」만 정해 둔다.
- 목적지가 정해지면 커널이 라우팅으로 어느 인터페이스 · 어느 내 주소에서 나갈지를 결정한다.
- `getsockname()` 은 그 결정된 내 쪽 주소를 읽는다 — 그래서 실제로 바깥으로 나가는 IP 가 나온다.
- 경로를 못 정해 예외가 나면 `'127.0.0.1'` 로 물러선다.
- 근거: 2-summary 「동작 방식 (4)」.

### 6. 실패를 예외가 아니라 값으로 받기 위해

- `connect` 는 접속이 안 되면 예외를 던진다 — 포트를 여럿 훑을 때마다 예외를 잡아야 한다.
- `connect_ex` 는 오류 번호를 값으로 돌려주고 성공이면 `0` 이다.
- 그래서 `result == 0` 한 번으로 열림 여부를 참/거짓으로 바꿀 수 있다.
- 근거: 2-summary 「동작 방식 (5)」, 원본 팁.

### 7. 말할 수 없다 — 「접속하지 못했다」까지만 뜻한다

- `check_port` 는 0 이 아닌 오류 번호, 시간 초과, 그 밖의 예외를 모두 `False` 로 묶는다.
- 따라서 서비스가 없는 경우 말고도 방화벽이 막은 경우 · 0.5초 안에 응답이 없는 경우 · `AF_INET` 소켓이라 IPv6 주소에 붙지 못한 경우도 「닫힘」이 된다.
- 원인을 가르려면 `connect_ex` 의 반환값(errno)을 그대로 보아야 한다.
- 근거: 2-summary 「동작 방식 (5)」 · 「어디서 틀리나 4」 (원본에 근거 없음 — 추론).

### 8. 관계가 없다 — 고정값이라 바뀐 IP 를 늦게 알아챈다

- `DNSCache` 의 TTL 은 생성자에 넘긴 고정 초(`ttl=60`, 기본 300)다.
- `gethostbyname` 은 레코드의 TTL 을 돌려주지 않으므로 캐시는 실제 레코드 TTL 을 알 수 없다.
- 그래서 레코드의 IP 가 바뀌어도 고정 TTL 이 끝나기 전까지는 옛 IP 를 계속 돌려줄 수 있다.
- 반대로 레코드가 오래 유효해도 고정 TTL 이 짧으면 필요 없이 다시 조회한다.
- 근거: 2-summary 「어디서 틀리나 5」 (원본에 근거 없음 — 추론).

### 9. 결과 꼴은 같고, 입력 방향과 실패 예외가 다르다

- 같은 점 — 둘 다 `(호스트명, 별칭 목록, IP 목록)` 세 칸 튜플을 돌려준다.
- 다른 점 1 — `gethostbyname_ex` 는 이름을 넣는 정방향, `gethostbyaddr` 는 IP 를 넣는 역방향이고 PTR 레코드를 읽는다.
- 다른 점 2 — 정답 코드는 정방향 실패를 `gaierror`, 역방향 실패를 `herror` 로 잡는다.
- 근거: 2-summary 「동작 방식 (1)」 · 「동작 방식 (2)」 · 「문법 — 형태와 규칙」 표.

## 실습 정답

### 실습 1. DNS 조회 · 로컬 정보 · 포트 확인 · TTL 캐시를 한 스크립트로

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. `gethostbyname` 결과 찍기 | `ip = socket.gethostbyname(hostname)` + `print(f"gethostbyname(...")` |
| 2. 호스트 · 별칭 · IP 한 줄씩 | `host_info = socket.gethostbyname_ex(hostname)` → `host_info[0]` · `[1]` · `[2]` |
| 3. 정방향 실패 처리 | `except socket.gaierror as e:` → `조회 실패` |
| 4. 역방향 조회와 실패 처리 | `socket.gethostbyaddr('8.8.8.8')` · `except socket.herror` |
| 5. `resolve_host` 의 딕셔너리 리스트 | `socket.getaddrinfo(hostname, port, proto=socket.IPPROTO_TCP)` · `'IPv4' if family == socket.AF_INET else 'IPv6'` |
| 6. 실패 때 빈 리스트 | `except socket.gaierror` 후 `return results` |
| 7. 두 호스트, 최대 4개 | `for host in [...]` · `results[:4]` |
| 8. 호스트명 · FQDN | `socket.gethostname()` · `socket.getfqdn()` + `except Exception: pass` |
| 9. `get_local_ip` | `socket.SOCK_DGRAM` · `s.connect(('8.8.8.8', 80))` · `s.getsockname()[0]` · `return '127.0.0.1'` |
| 10. `check_port` | `socket.SOCK_STREAM` · `s.settimeout(timeout)` · `s.connect_ex((host, port))` · `result == 0` |
| 11. 세 포트 확인 | `common_ports` · `check_port('127.0.0.1', port, timeout=0.5)` |
| 12. 캐시 구조 | `DNSCache.__init__` 의 `self.cache = {}` · `self.ttl` |
| 13. 히트 · 만료 | `if now < expire:` → `[캐시 히트]` / `else:` → `[캐시 만료]` |
| 14. 실제 조회와 저장 | `socket.gethostbyname(hostname)` · `self.cache[hostname] = (ip, now + self.ttl)` · `except socket.gaierror: return None` |
| 15. 비우기 | `def clear(self): self.cache.clear()` |
| 16. 테스트와 항목 수 | `dns = DNSCache(ttl=60)` · `dns.resolve(...)` 세 번 · `len(dns.cache)` |
| 17. 요약 다섯 줄 | `=== 핵심 정리 ===` 아래 `print` 다섯 개 |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`python/python-networking/reference/dns-lookup.py`

```python
# [네트워크 & 시스템] DNS 조회와 리졸버
# 설명: socket.getaddrinfo로 DNS 조회, 커스텀 리졸버 패턴
# 팁: socket.getaddrinfo()가 가장 권장되는 DNS 조회 방식으로 IPv4/IPv6를 모두 처리한다. gethostbyname은 IPv4만 반환한다. connect_ex()로 포트 상태를 확인할 수 있으며, DNS 캐시를 구현하면 반복 조회를 줄일 수 있다.

"""DNS 조회와 리졸버: socket, 호스트 조회"""
# socket: BSD 소켓 API + DNS 리졸버 함수 제공
import socket
# 타입 힌트
from typing import List, Dict

# === 1. 기본 DNS 조회 ===
print("=== 1. 기본 DNS 조회 ===")

# hostname -> IP
# 도메인 → IPv4 (구식 API, IPv6 미지원)
hostname = 'www.google.com'
try:
    # gethostbyname: 첫 번째 IPv4만 반환
    ip = socket.gethostbyname(hostname)
    print(f"gethostbyname('{hostname}') = {ip}")
except socket.gaierror as e:
    # gaierror: getaddrinfo 계열 실패 (DNS 조회 불가)
    print(f"조회 실패: {e}")

# hostname -> (hostname, aliases, addresses)
try:
    # gethostbyname_ex: 별칭과 모든 IP 반환
    host_info = socket.gethostbyname_ex(hostname)
    print(f"\ngethostbyname_ex('{hostname}'):")
    print(f"  호스트: {host_info[0]}")
    print(f"  별칭:   {host_info[1]}")
    print(f"  IP:     {host_info[2]}")
except socket.gaierror as e:
    print(f"조회 실패: {e}")

# IP -> hostname (역방향 DNS)
try:
    # gethostbyaddr: PTR 레코드 조회
    reverse = socket.gethostbyaddr('8.8.8.8')
    print(f"\n역방향 DNS('8.8.8.8'):")
    print(f"  호스트: {reverse[0]}")
    print(f"  별칭:   {reverse[1]}")
    print(f"  IP:     {reverse[2]}")
except socket.herror as e:
    # herror: 호스트 조회 전용 에러
    print(f"역방향 실패: {e}")

# === 2. getaddrinfo (권장) ===
print("\n=== 2. getaddrinfo (권장) ===")

# 권장 API: IPv4/IPv6 동시 처리, 프로토콜별 결과
def resolve_host(hostname: str, port: int = 80) -> List[Dict]:
    """getaddrinfo로 상세 DNS 조회"""
    results = []
    try:
        # proto 지정으로 TCP만 (중복 결과 줄임)
        infos = socket.getaddrinfo(hostname, port, proto=socket.IPPROTO_TCP)
        # 각 결과: (family, socktype, proto, canonname, sockaddr)
        for family, socktype, proto, canonname, sockaddr in infos:
            results.append({
                # AF_INET=IPv4, AF_INET6=IPv6
                'family': 'IPv4' if family == socket.AF_INET else 'IPv6',
                'ip': sockaddr[0],
                'port': sockaddr[1],
            })
    except socket.gaierror as e:
        print(f"조회 실패: {e}")
    return results

for host in ['www.google.com', 'www.python.org']:
    results = resolve_host(host)
    print(f"\n{host}:")
    for r in results[:4]:  # 최대 4개
        print(f"  {r['family']}: {r['ip']}:{r['port']}")

# === 3. 로컬 네트워크 정보 ===
print("\n=== 3. 로컬 네트워크 정보 ===")

# 자기 호스트명
# 시스템 hostname
my_hostname = socket.gethostname()
print(f"호스트명: {my_hostname}")

# FQDN
try:
    # FQDN: 정규화된 전체 도메인명 (host + 도메인)
    fqdn = socket.getfqdn()
    print(f"FQDN: {fqdn}")
except Exception:
    pass

# 자기 IP (외부 연결 시뮬레이션)
# UDP는 연결을 실제로 만들지 않고도 라우팅 결정이 됨 → 로컬 IP 알아내는 트릭
def get_local_ip() -> str:
    """로컬 IP 주소 확인 (실제 네트워크 인터페이스)"""
    try:
        # SOCK_DGRAM = UDP (실제 패킷 송신 없음)
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            # 8.8.8.8: 구글 DNS (도달 가능 가정)
            s.connect(('8.8.8.8', 80))  # 실제 연결하지 않음
            # 커널이 선택한 발신 IP
            return s.getsockname()[0]
    except Exception:
        # 실패 시 루프백
        return '127.0.0.1'

print(f"로컬 IP: {get_local_ip()}")

# === 4. 포트 스캔 (간단한 예시) ===
print("\n=== 4. 간단한 포트 확인 ===")

# TCP connect 시도로 포트 열림 여부 확인
def check_port(host: str, port: int, timeout: float = 1.0) -> bool:
    """특정 호스트의 포트가 열려있는지 확인"""
    try:
        # SOCK_STREAM = TCP
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            # 블로킹 소켓에 타임아웃 부과
            s.settimeout(timeout)
            # connect_ex: 예외 대신 errno 반환 (0=성공)
            result = s.connect_ex((host, port))  # 0이면 성공
            return result == 0
    except Exception:
        return False

# 잘 알려진 포트
common_ports = {'HTTP': 80, 'HTTPS': 443, 'SSH': 22}
for name, port in common_ports.items():
    status = check_port('127.0.0.1', port, timeout=0.5)
    print(f"  127.0.0.1:{port} ({name}): {'열림' if status else '닫힘'}")

# === 5. DNS 캐시 시뮬레이션 ===
print("\n=== 5. DNS 캐시 패턴 ===")

# 캐시 만료 시각 계산용
import time

# TTL 기반 인메모리 DNS 캐시 (반복 조회 비용 절감)
class DNSCache:
    """TTL 기반 DNS 캐시"""

    # 기본 TTL 5분
    def __init__(self, ttl: int = 300):
        # hostname -> (ip, expire_time)
        self.cache = {}  # hostname -> (ip, expire_time)
        self.ttl = ttl

    # 호스트명 → IP (캐시 우선)
    def resolve(self, hostname: str) -> str:
        # 현재 시각 (초)
        now = time.time()

        # 캐시 확인
        if hostname in self.cache:
            ip, expire = self.cache[hostname]
            # 만료 전이면 캐시 사용
            if now < expire:
                print(f"  [캐시 히트] {hostname} -> {ip}")
                return ip
            else:
                print(f"  [캐시 만료] {hostname}")

        # 실제 조회
        try:
            # 실제 DNS 조회
            ip = socket.gethostbyname(hostname)
            # 만료 시각 = 현재 + TTL
            self.cache[hostname] = (ip, now + self.ttl)
            print(f"  [DNS 조회] {hostname} -> {ip}")
            return ip
        except socket.gaierror:
            return None

    # 캐시 비우기
    def clear(self):
        self.cache.clear()

# 테스트
dns = DNSCache(ttl=60)
dns.resolve('www.google.com')  # DNS 조회
dns.resolve('www.google.com')  # 캐시 히트
dns.resolve('www.python.org')  # DNS 조회

print(f"\n캐시 항목: {len(dns.cache)}개")

print("\n=== 핵심 정리 ===")
print("gethostbyname():  간단한 IP 조회")
print("getaddrinfo():    상세 조회 (IPv4/IPv6, 포트, 프로토콜)")
print("gethostbyaddr():  역방향 DNS (IP -> 호스트명)")
print("connect_ex():     포트 열림 확인 (0=성공)")
print("DNS 캐시:         TTL 기반으로 반복 조회 방지")
```

**실행 결과** — 실행하지 않음 — 실행 환경 · 바깥 네트워크에 따라 달라지는 예제다.

**풀이 요점**

- 정방향 · 역방향은 결과 튜플의 꼴이 같아 출력 코드도 같은 모양이고, 잡는 예외만 `gaierror` · `herror` 로 다르다.
- `getaddrinfo` 결과는 다섯 칸으로 풀어 받고, 주소는 `sockaddr[0]` · 포트는 `sockaddr[1]` 에서 꺼낸다.
- `get_local_ip` 의 핵심은 UDP `connect` 가 패킷 없이 출발 주소만 정한다는 점이다.
- `check_port` 는 `connect_ex` 의 `0` 비교와 `except` 의 `False` 로 모든 실패를 「닫힘」으로 묶는다.
- `DNSCache.resolve` 는 만료된 경우 `return` 없이 아래로 흘러 다시 조회하고, 같은 키를 덮어쓴다.
- 이름 조회 결과(IP · 개수)는 환경마다 다르므로 확인할 때는 값이 아니라 꼬리표의 차례와 항목 수를 본다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — 실행 환경 · 바깥 네트워크에 따라 달라지는 예제다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
