# python/python-networking/08 — DNS 조회와 리졸버 — 정리 (힌트)

> 출처 — study-site 항목 `python/dns-lookup`(항목 데이터 `data/python/networking.json`) · 정답 코드 study-practice `python/python-networking/reference/dns-lookup.py`\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).\
> 실행 — 실행하지 않음 — 실행 환경 · 바깥 네트워크에 따라 달라지는 예제다.

## 한눈에 — 쉽게 말하면

**DNS 조회는 「114 전화번호 안내」다.**
가게 이름을 말하면 안내원이 번호를 알려 준다.
거꾸로 번호를 대고 「이 번호가 어디냐」고 묻는 서비스도 있다.
자주 거는 번호는 수첩에 적어 두고 안내에 다시 묻지 않는다.
다만 번호는 바뀔 수 있으니 수첩 메모에는 「언제까지 믿을지」를 함께 적는다.
파이썬의 `socket` 모듈로 하는 DNS 조회도 똑같은 구조다.

> **DNS** — 도메인 이름(`www.google.com`)을 IP 주소로 바꿔 주는 인터넷의 이름 체계.\
> 예: `www.google.com` 을 물으면 IP 주소 목록이 돌아온다.

> **리졸버** — 이름 → 주소 변환을 대신 해 주는 쪽(운영체제의 조회 기능 · 그것을 감싼 함수 · 직접 만든 캐시 클래스).\
> 예: `socket.getaddrinfo()` 는 운영체제 리졸버에게 일을 맡긴다.

| 비유 | 실체 |
|---|---|
| 가게 이름 | 호스트명 · 도메인 (`www.google.com`) |
| 전화번호 | IP 주소 |
| 114 안내원 | 리졸버 (`gethostbyname` · `getaddrinfo`) |
| 번호로 가게 찾기 | 역방향 DNS (`gethostbyaddr`) |
| 수첩 메모 | DNS 캐시 (`DNSCache.cache` 딕셔너리) |
| 「언제까지 믿을지」 | TTL · 만료 시각 |
| 가게에 전화해 보기 | 포트 확인 (`connect_ex`) |

```text
 'www.google.com'                       '8.8.8.8'
        │  정방향                           │  역방향
        ▼                                   ▼
  ┌──────────────┐                   ┌──────────────┐
  │  리졸버(OS)   │ ──▶ DNS 서버       │  리졸버(OS)   │ ──▶ PTR 레코드
  └──────────────┘                   └──────────────┘
        │                                   │
        ▼                                   ▼
  [<IP>, <IP>, ...]                   ('<호스트명>', [별칭], [IP])
```

## 이 주제가 답하려는 질문

1. 이름에서 IP 를 얻는 함수가 여럿인데, 무엇이 어떻게 다르고 무엇을 써야 하나?
2. 거꾸로 IP 에서 이름을 얻으려면 어떻게 하나?
3. 내 컴퓨터의 이름 · IP, 그리고 어떤 포트가 열려 있는지는 어떻게 알아보나?
4. 같은 이름을 여러 번 물을 때 매번 DNS 에 묻지 않으려면 어떻게 하나?

## 동작 방식

### (1) 간단한 정방향 조회 — `gethostbyname` · `gethostbyname_ex`

**언제 쓰나** — IPv4 주소 하나만 빨리 얻으면 될 때.
별칭과 IPv4 목록까지 보고 싶으면 `_ex` 판을 쓴다.

```text
socket.gethostbyname('www.google.com')
   → 리졸버에 묻는다
   → IPv4 주소 문자열 하나   '<IPv4>'

socket.gethostbyname_ex('www.google.com')
   → 리졸버에 묻는다
   → 튜플 (호스트명, [별칭들], [IPv4 목록])
          [0]        [1]          [2]

이름을 못 찾으면 → socket.gaierror 예외
```

- `gethostbyname` 은 이름 하나를 받아 IPv4 주소 **하나**를 문자열로 돌려준다.
- IPv6 주소는 돌려주지 않는다 — 원본 팁의 말대로 「IPv4 만 반환한다」.
- 정답 코드 주석은 이 함수를 「구식 API, IPv6 미지원」이라 부른다.
- `gethostbyname_ex` 는 세 칸짜리 튜플을 돌려준다 — 대표 호스트명, 별칭 목록, IP 목록 차례다.
- 조회에 실패하면 `socket.gaierror` 가 난다. 정답 코드는 이것을 잡아 「조회 실패」를 찍는다.

> **`socket.gaierror`** — 이름 조회(주소 정보 얻기) 계열 함수가 실패했을 때 나는 예외.\
> 예: 존재하지 않는 도메인을 `gethostbyname` 에 넘기면 난다.

### (2) 역방향 조회 — `gethostbyaddr`

**언제 쓰나** — IP 를 알고 있고 그 IP 에 붙은 이름을 알고 싶을 때(로그에 찍힌 IP 가 누구인지 볼 때 등).

```text
socket.gethostbyaddr('8.8.8.8')
   → 리졸버가 PTR 레코드를 묻는다
   → 튜플 (호스트명, [별칭들], [IP 목록])   ← gethostbyname_ex 와 같은 꼴

PTR 레코드가 없거나 조회가 안 되면 → socket.herror 예외
```

- 입력이 이름이 아니라 IP 라는 점만 다르고, 돌아오는 튜플의 모양은 `gethostbyname_ex` 와 같다.
- 정답 코드 주석대로 이 조회는 PTR 레코드를 묻는다.
- 정답 코드는 실패를 `socket.herror` 로 잡는다 — 주석은 이것을 「호스트 조회 전용 에러」라 부른다.

> **PTR 레코드** — IP 주소 → 이름을 적어 둔 DNS 레코드. 역방향 조회가 읽는 대상이다.\
> 예: `8.8.8.8` 의 PTR 레코드를 물으면 그 주소에 붙은 호스트명이 나온다.

> **`socket.herror`** — 호스트 주소 관련 조회가 실패했을 때 나는 예외.\
> 예: PTR 레코드가 없는 IP 로 `gethostbyaddr` 를 부르면 날 수 있다.

### (3) 권장 방식 — `getaddrinfo`

**언제 쓰나** — 실제로 접속할 주소를 구할 때.
원본 팁이 「가장 권장되는 DNS 조회 방식」이라 부르는 함수다.

```text
socket.getaddrinfo('www.google.com', 80, proto=socket.IPPROTO_TCP)
   → 리졸버에 이름 + 포트 + 조건(TCP)을 함께 묻는다
   → 튜플의 리스트
       [ (family, socktype, proto, canonname, sockaddr),
         (family, socktype, proto, canonname, sockaddr), ... ]
                                               │
                                     sockaddr[0] = IP 문자열
                                     sockaddr[1] = 포트

family == socket.AF_INET   → IPv4
family == socket.AF_INET6  → IPv6
```

- `getaddrinfo` 는 IPv4 와 IPv6 결과를 **한 번에** 돌려준다.
- 결과 하나하나가 다섯 칸 튜플이고, 다섯째 칸 `sockaddr` 에 IP 와 포트가 들어 있다.
- 포트를 함께 넘기므로 결과가 「이 주소의 이 포트로 접속하라」는 꼴로 바로 쓸 수 있다.
- `proto=socket.IPPROTO_TCP` 를 주면 TCP 용 결과만 받는다 — 주석 말대로 「중복 결과를 줄인다」.
  프로토콜을 지정하지 않으면 같은 IP 가 소켓 종류별로 여러 번 나올 수 있다는 뜻이다.
- 정답 코드의 `resolve_host` 는 결과를 `{'family', 'ip', 'port'}` 딕셔너리 리스트로 바꾸고, 실패하면 메시지를 찍고 빈 리스트를 돌려준다.
- 출력 쪽은 `results[:4]` 로 최대 4개만 보여 준다.
- 가족 이름은 `'IPv4' if family == socket.AF_INET else 'IPv6'` 로 정한다 — `AF_INET` 이 아니면 전부 `IPv6` 로 적힌다.

> **`AF_INET` · `AF_INET6`** — 소켓 주소 체계(family) 상수. 앞은 IPv4, 뒤는 IPv6.\
> 예: `getaddrinfo` 결과의 첫 칸이 `AF_INET6` 이면 그 줄은 IPv6 주소다.

### (4) 로컬 정보 — `gethostname` · `getfqdn` · UDP 트릭

**언제 쓰나** — 로그 · 설정에 내 컴퓨터의 이름과 바깥으로 나가는 IP 를 적어야 할 때.

```text
socket.gethostname()   → 시스템 호스트명         'my-pc'
socket.getfqdn()       → 호스트명 + 도메인        'my-pc.example.local'

get_local_ip():
  UDP 소켓 생성 (SOCK_DGRAM)
     → s.connect(('8.8.8.8', 80))     ← 패킷을 보내지 않는다
     → 커널이 「이 목적지로 가려면 어느 인터페이스?」를 정한다
     → s.getsockname()[0]             ← 그때 고른 내 쪽 IP
  예외가 나면 → '127.0.0.1'
```

- `gethostname()` 은 운영체제에 설정된 컴퓨터 이름을 돌려준다.
- `getfqdn()` 은 정규화된 전체 도메인명을 돌려준다. 정답 코드는 예외가 나면 조용히 넘어간다.
- UDP 는 연결이라는 단계가 없어서, UDP 소켓의 `connect` 는 「앞으로 보낼 목적지를 정해 둔다」는 뜻일 뿐이다.
- 목적지가 정해지면 커널은 라우팅으로 「어느 내 주소에서 나갈지」를 결정한다.
- `getsockname()` 은 그렇게 정해진 내 쪽 주소를 읽는다 — 그래서 패킷 없이 실제 인터페이스 IP 를 알 수 있다.
- 주석은 `8.8.8.8` 을 「도달 가능 가정」의 목적지로 쓴다고 적는다. 경로를 못 정해 예외가 나면 루프백 `127.0.0.1` 을 돌려준다.

> **FQDN** — 호스트명에 도메인까지 붙인 전체 이름.\
> 예: 호스트명 `web1` 의 FQDN 은 `web1.example.com` 꼴이다.

> **루프백** — 자기 자신을 가리키는 주소 `127.0.0.1`. 밖으로 나가지 않는다.\
> 예: `127.0.0.1:80` 에 접속하면 내 컴퓨터의 80 번 포트로 간다.

### (5) 포트 확인 — `connect_ex`

**언제 쓰나** — 어떤 호스트의 TCP 포트에 서비스가 떠 있는지 가볍게 확인할 때.

```text
check_port('127.0.0.1', 80, timeout=0.5)
   → TCP 소켓 생성 (AF_INET, SOCK_STREAM)
   → s.settimeout(0.5)
   → s.connect_ex(('127.0.0.1', 80))
          │
          ├─ 0          → True   ('열림')
          ├─ 0 이 아닌 수 → False  ('닫힘')   ← 거절 · 실패의 오류 번호
   예외가 나면 ───────────→ False  ('닫힘')
```

- `connect` 는 실패하면 예외를 던지지만, `connect_ex` 는 오류 번호(errno)를 **값으로** 돌려준다. 성공이면 `0` 이다.
- 그래서 포트 여러 개를 훑을 때 `try/except` 를 일일이 감싸지 않고 `== 0` 비교로 끝낼 수 있다.
- `settimeout` 은 응답이 없는 포트에서 오래 멈추지 않게 기다리는 시간을 정한다.
- 정답 코드는 HTTP 80 · HTTPS 443 · SSH 22 를 `127.0.0.1` 에서 확인하고 `열림` · `닫힘` 을 찍는다.
- 이 함수가 돌려주는 값은 참/거짓 둘뿐이다 — 「닫힘」은 거절, 시간 초과, 그 밖의 예외를 모두 한데 묶은 말이다.
- 소켓을 `AF_INET` 으로 만들므로 IPv4 주소만 확인할 수 있다.

> **errno** — 운영체제가 실패 원인을 알리는 정수 오류 번호.\
> 예: `connect_ex` 가 `0` 이 아닌 수를 돌려주면 그 수가 errno 다.

### (6) TTL 캐시 — `DNSCache`

**언제 쓰나** — 같은 이름을 짧은 시간에 여러 번 조회하는 프로그램에서, 조회 비용을 줄이고 싶을 때.

```text
cache = { 'www.google.com': ('<IP>', 만료시각) , ... }

resolve(name):
  now = time.time()
  name 이 cache 에 있나?
    ├─ 있고 now < 만료시각  → "[캐시 히트]" 찍고 캐시 IP 반환   (DNS 안 물음)
    └─ 있지만 만료됨        → "[캐시 만료]" 찍고 아래로 내려감
  gethostbyname(name)
    ├─ 성공 → cache[name] = (ip, now + ttl) 로 덮어씀 → "[DNS 조회]" 찍고 반환
    └─ gaierror → 아무것도 찍지 않고 None 반환 (cache 는 그대로)
```

- `cache` 는 `호스트명 → (IP, 만료 시각)` 딕셔너리다.
- 만료 시각은 「저장한 순간 + `ttl` 초」다. `ttl` 기본값은 300(5분)이고, 정답 코드의 테스트는 `ttl=60` 으로 만든다.
- 만료 전이면 DNS 에 묻지 않고 저장된 값을 돌려준다 — 이것이 원본 팁의 「반복 조회를 줄인다」다.
- 만료되었으면 「캐시 만료」를 알리고 다시 조회해 같은 키를 **덮어쓴다** — 항목 수는 늘지 않는다.
- 조회가 실패하면 `None` 을 돌려주고 캐시는 건드리지 않는다. 만료된 옛 항목도 지워지지 않고 남는다.
- 실제 조회는 `gethostbyname` 이라 IPv4 하나만 캐시에 들어간다.
- `clear()` 는 캐시를 통째로 비운다.

> **TTL (Time To Live)** — 값을 믿고 써도 되는 시간(초).\
> 예: `ttl=60` 이면 저장 후 60초까지는 캐시 값을 쓴다.

> **캐시 히트 · 만료** — 저장된 값을 그대로 쓰는 경우 · 저장된 값의 시간이 지나 다시 구해야 하는 경우.\
> 예: 같은 이름을 곧바로 두 번 물으면 두 번째는 캐시 히트다.

## 문법 — 형태와 규칙

```python
import socket

ip = socket.gethostbyname('example.com')              # '<IPv4>'
name, aliases, ips = socket.gethostbyname_ex('example.com')

for family, socktype, proto, canon, addr in socket.getaddrinfo(
        'example.com', 443, proto=socket.IPPROTO_TCP):
    print(family == socket.AF_INET6, addr[0], addr[1])

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.settimeout(1.0)
    is_open = s.connect_ex(('127.0.0.1', 22)) == 0
```

| 함수 | 넣는 것 | 돌려받는 것 | 실패 예외(정답 코드가 잡는 것) |
|---|---|---|---|
| `gethostbyname(name)` | 이름 | IPv4 문자열 하나 | `gaierror` |
| `gethostbyname_ex(name)` | 이름 | `(호스트명, 별칭 목록, IPv4 목록)` | `gaierror` |
| `gethostbyaddr(ip)` | IP | `(호스트명, 별칭 목록, IP 목록)` | `herror` |
| `getaddrinfo(name, port, proto=…)` | 이름 · 포트 · 조건 | `(family, socktype, proto, canonname, sockaddr)` 리스트 | `gaierror` |
| `gethostname()` | 없음 | 시스템 호스트명 | — |
| `getfqdn()` | 없음 | FQDN | — |
| `sock.connect_ex(addr)` | `(host, port)` | errno 정수 (`0` = 성공) | 예외 대신 값 |
| `sock.getsockname()` | 없음 | 내 쪽 `(IP, 포트)` | — |

- 소켓 함수는 `with socket.socket(...) as s:` 로 감싸 블록이 끝나면 닫히게 한다.
- `SOCK_STREAM` 은 TCP, `SOCK_DGRAM` 은 UDP 다.
- 주소는 언제나 `(host, port)` 튜플 하나로 넘긴다 — 괄호가 두 겹이 된다.
- `getaddrinfo` 결과는 다섯 칸으로 풀어 받고, 주소는 다섯째 칸에서 꺼낸다.

## 어디서 틀리나

### 1. `gethostbyname` 으로 IPv6 를 기대한다

이 함수는 IPv4 하나만 돌려준다(원본 팁).
IPv6 주소가 필요하거나, 여러 주소 중 골라 써야 하면 `getaddrinfo` 를 쓴다.
`gethostbyname_ex` 도 IP 목록이 IPv4 목록이라는 점은 같다(확인 필요).

### 2. 예외 종류를 엉뚱하게 잡는다

정방향은 `gaierror`, 역방향은 `herror` 로 잡는 것이 정답 코드의 짝이다.
역방향 블록은 `herror` 만 잡으므로, 거기서 다른 종류의 예외가 나면 잡히지 않고 프로그램이 멈춘다.
`gethostbyaddr` 가 상황에 따라 `gaierror` 를 낼 수도 있는지는 원본에 없다(확인 필요).

### 3. `AF_INET` 이 아니면 모두 `IPv6` 로 적힌다

`resolve_host` 는 `family == socket.AF_INET` 이 아니면 무조건 `'IPv6'` 라 적는다.
`getaddrinfo` 가 IPv4 · IPv6 만 돌려주는 보통 경우에는 맞지만, 판정이 「IPv6 인지 확인」이 아니라 「IPv4 가 아님」이라는 점을 알아 둔다.

### 4. 「닫힘」을 「서비스가 없다」로만 읽는다

`check_port` 는 `connect_ex` 가 `0` 이 아니어도, 시간 초과여도, 예외가 나도 모두 `False` 다.
그래서 「닫힘」은 「접속에 성공하지 못했다」까지만 뜻한다.
방화벽이 막은 경우 · 응답이 늦은 경우 · 주소가 IPv6 라 `AF_INET` 소켓으로 못 붙은 경우도 같은 「닫힘」이 된다(원본에 근거 없음 — 추론).
시간 초과일 때 `connect_ex` 가 값을 돌려주는지 예외를 내는지는 원본에 없다 — 어느 쪽이든 이 함수에서는 `False` 다(확인 필요).

### 5. 「TTL 기반 DNS 캐시」라는 말을 문자 그대로 믿는다

**원본의 주장** — `DNSCache` 를 「TTL 기반 DNS 캐시」라 부른다.
**왜 의심스러운가** — 여기서 쓰는 TTL 은 생성자에 넘긴 **고정값**(`ttl=60` · 기본 300)이다.
실제 DNS 레코드에는 레코드마다 자기 TTL 이 붙는데, `gethostbyname` 은 그 값을 돌려주지 않으므로 이 캐시는 레코드의 TTL 을 모른다.
그래서 레코드가 실제로 바뀐 뒤에도 고정 TTL 이 끝날 때까지 옛 IP 를 줄 수 있다(원본에 근거 없음 — 추론).

### 6. `resolve` 의 반환 표기와 실제 반환이 다르다

시그니처는 `-> str` 인데 실패하면 `None` 을 돌려준다.
부르는 쪽이 문자열만 온다고 믿고 쓰면 실패 때 깨진다.
반환 표기를 `Optional[str]` 로 고치거나, 부르는 쪽에서 `None` 을 따로 다뤄야 한다(원본에 근거 없음 — 추론).

### 7. 조회 결과를 고정값으로 여긴다

IP 주소 · 별칭 · 결과 개수 · 차례는 네트워크 · 지역 · 시각 · 운영체제 설정에 따라 다르다.
조회 결과를 코드에 박아 두거나 테스트의 기대값으로 쓰면 깨진다.

### 8. 원본 팁 정리

원본 팁 네 문장은 위에 모두 들어 있다 — `getaddrinfo` 권장(동작 방식 (3)), `gethostbyname` 은 IPv4 만(1번), `connect_ex` 로 포트 상태 확인(동작 방식 (5)), DNS 캐시로 반복 조회 줄이기(동작 방식 (6)).

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| `socket` 모듈 함수들이 위 표의 꼴로 값을 돌려준다 | 파이썬 표준 라이브러리 문서 |
| 실제 이름 조회(어느 DNS 서버, hosts 파일을 먼저 보는지 등) | 운영체제의 리졸버 설정 — 파이썬이 아니다 |
| `getaddrinfo` 결과의 차례 · 개수 | 운영체제 리졸버와 네트워크 환경 — 고정되지 않는다 |
| UDP 소켓의 `connect` 가 패킷을 보내지 않고 출발 주소만 정한다 | 운영체제 커널의 소켓 동작(확인 필요) |
| `connect_ex` 가 돌려주는 0 이 아닌 오류 번호의 구체적인 값 | 운영체제마다 다르다(확인 필요) |
| `gethostname` · `getfqdn` 의 값 | 그 컴퓨터의 시스템 설정 |
| `DNSCache` 의 만료 판단 | 이 코드 자신 — 실제 DNS TTL 과 무관 |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 접속할 주소 구하기(IPv4 · IPv6 모두) | `getaddrinfo` | `gethostbyname` (IPv4 만) |
| IPv4 하나만 빨리 보기 | `gethostbyname` | 결과를 IPv6 환경에 그대로 쓰기 |
| 별칭 · IPv4 목록 보기 | `gethostbyname_ex` | — |
| IP 로 이름 찾기 | `gethostbyaddr` (+ `herror` 처리) | 정방향 함수에 IP 넣기 |
| 바깥으로 나가는 내 IP | UDP `connect` + `getsockname` | `gethostbyname(gethostname())` 류 추측(원본에 근거 없음 — 추론) |
| 포트 열림 확인 | `connect_ex` + `settimeout` | 타임아웃 없는 `connect` 를 여러 포트에 |
| 같은 이름을 짧은 시간에 반복 조회 | TTL 캐시 | 레코드가 자주 바뀌는 이름에 긴 고정 TTL |

## 핵심 문장

1. **이름 → 주소는 `getaddrinfo` 가 기본이다** — IPv4 · IPv6 를 함께 주고, 결과의 다섯째 칸에 접속할 `(IP, 포트)` 가 있다.
2. **`gethostbyname` 은 IPv4 하나뿐이다** — 간단하지만 구식이고, 역방향은 `gethostbyaddr` 가 PTR 레코드로 한다.
3. **UDP `connect` 는 패킷 없이 출발 주소만 정한다** — 그래서 `getsockname` 으로 내 IP 를 읽을 수 있다.
4. **`connect_ex` 는 예외 대신 숫자를 준다** — `0` 이면 열림, 그 밖에는 모두 「접속 못 함」이다.
5. **TTL 캐시는 만료 시각과 함께 저장해 반복 조회를 줄인다** — 다만 이 예제의 TTL 은 실제 레코드 TTL 이 아닌 고정값이다.

## 관련 자료

- `socket-tcp` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- `socket-udp` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- `url-parsing` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- 원본: study-site 항목 데이터 `data/python/networking.json` 의 `dns-lookup`

## 용어 풀이

- **DNS** — 도메인 이름을 IP 주소로 바꿔 주는 인터넷 이름 체계.
- **리졸버** — 이름 → 주소 변환을 맡아 하는 쪽(운영체제 기능 · 함수 · 캐시 클래스).
- **정방향 조회** — 이름 → IP.
- **역방향 조회** — IP → 이름. PTR 레코드를 읽는다.
- **PTR 레코드** — IP → 이름을 적은 DNS 레코드.
- **별칭** — 같은 호스트를 가리키는 다른 이름.
- **FQDN** — 호스트명 + 도메인까지 붙인 전체 이름.
- **`AF_INET` · `AF_INET6`** — IPv4 · IPv6 주소 체계 상수.
- **`SOCK_STREAM` · `SOCK_DGRAM`** — TCP 소켓 · UDP 소켓.
- **`IPPROTO_TCP`** — TCP 프로토콜 번호 상수. `getaddrinfo` 결과를 TCP 용으로 좁힌다.
- **`sockaddr`** — 소켓 주소 튜플. 첫 칸이 IP, 둘째 칸이 포트.
- **`gaierror`** — 이름 조회 계열 실패 예외.
- **`herror`** — 호스트 주소 관련 조회 실패 예외.
- **errno** — 운영체제의 정수 오류 번호.
- **루프백** — 자기 자신을 가리키는 주소 `127.0.0.1`.
- **TTL** — 값을 믿고 써도 되는 시간(초).
- **캐시 히트 · 만료** — 저장값을 그대로 씀 · 시간이 지나 다시 구함.

## 더 들어가면

- IPv6 의 `sockaddr` 는 `(IP, 포트, flowinfo, scope_id)` 네 칸이라 길이가 IPv4 와 다르다 — 앞 두 칸만 쓰면 양쪽에 다 통한다(확인 필요).
- `getaddrinfo` 에 `family=socket.AF_INET6` 처럼 주소 체계를 지정하면 한쪽만 받을 수 있다(확인 필요).
- 파이썬 문서는 IPv4/IPv6 를 모두 다루려면 `gethostbyname` 계열 대신 `getaddrinfo` 를 쓰라고 권한다(확인 필요).
- 만료 판단에는 시스템 시계 조정의 영향을 받는 `time.time()` 보다 `time.monotonic()` 이 안전하다(확인 필요).
- 레코드의 실제 TTL 을 존중하려면 `dnspython` 같은 서드파티 라이브러리로 DNS 응답을 직접 받아야 한다(확인 필요).
- `socket.create_connection((host, port), timeout)` 은 `getaddrinfo` 결과를 차례로 시도해 접속하는 편의 함수다(확인 필요).
- 포트 확인은 자기가 관리하는 호스트에만 하는 것이 원칙이다 — 남의 시스템을 훑는 것은 문제가 될 수 있다(확인 필요).
- 여러 포트를 빠르게 확인하려면 스레드나 `asyncio` 로 동시에 시도한다(확인 필요).
