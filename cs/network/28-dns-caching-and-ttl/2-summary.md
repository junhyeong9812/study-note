# network/28-dns-caching-and-ttl — DNS 캐시와 TTL: 캐시 계층·부정 캐시·검색 도메인 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> ⚠️ 이 서머리는 Claude 초안(2026-09-30) — 근거는 아래 「관련 주제·근거」. 본인 검수 후 이 줄을 `✅ 검수 완료(날짜)`로 바꾼다.

## 해결하는 문제

DNS 이름 하나를 풀려면 루트 → TLD → 권한 서버로 여러 번 묻는다(27번).\
요청마다 이 길을 다 걸으면 느리고, 권한 서버는 전 세계 질의에 묻힌다.\
그래서 답을 **잠시 기억해 두고 재사용**한다.\
얼마나 오래 기억해도 되는지는 레코드 주인이 정한다. 그 값이 **TTL**이다.

  - *TTL(Time To Live)*: 이 답을 캐시에 둬도 되는 시간(초)이다. 레코드마다 붙어 온다(RFC 1035 §3.2.1). 값은 0 ~ 2^31−1이다(RFC 2181 §8).

쉬운 예: 친구 전화번호를 매번 114에 묻지 않고 수첩에 적어 둔다.\
수첩에 "이 번호는 한 달 뒤 다시 확인" 하고 적어 두는 것이 TTL이다.\
친구가 번호를 바꿨는데 수첩이 아직 유효하면, 한 달 동안 옛 번호로 건다.

똑같은 구조다.\
캐시는 속도를 주고, 대가로 **바뀐 사실이 늦게 퍼진다**.

실무 예:
- DB 페일오버로 엔드포인트 IP가 바뀌었는데, 애플리케이션이 몇 분째 죽은 IP로 접속한다.
- 새 서브도메인 레코드를 만들었는데 "아직 없는 이름"이라는 답이 한참 남는다.
- 쿠버네티스 파드에서 외부 도메인 하나를 부를 때 DNS 질의가 여러 번 나간다.

## 동작·원리

### 1. 캐시는 여러 층에 있다

```text
  앱 프로세스                          (1) 언어 런타임 캐시  예: JVM InetAddress 캐시
     |  getaddrinfo() / InetAddress
     v
  OS 스텁 리졸버                       (2) OS 캐시  예: systemd-resolved, nscd (구성에 따라 없음)
     |  /etc/resolv.conf 의 nameserver
     v
  노드·클러스터 DNS                    (3) 예: CoreDNS cache 플러그인
     |
     v
  재귀 리졸버 (ISP, 8.8.8.8 등)         (4) 공용 캐시 — 여러 사용자가 공유
     |  캐시에 없을 때만
     v
  권한 서버  -- 원본. 레코드와 TTL을 정한다
```

- 아래층(권한 서버에 가까운 쪽)이 답을 주면서 **남은 TTL**을 적어 준다.
  - 재귀 리졸버가 300초짜리 레코드를 200초 전에 받아 두었다면, 지금 질의한 클라이언트는 TTL 100을 받는다.
  - 그래서 TTL을 따르는 캐시끼리는 층이 몇 개든 낡음의 상한이 대략 원래 TTL로 유지된다.
- 문제는 **TTL을 따르지 않는 층**이다.
  - JVM의 `InetAddress` 캐시는 DNS 응답의 TTL이 아니라 자체 정책 값(`networkaddress.cache.ttl`)으로 캐시한다(아래 §4).
  - 이런 층은 원래 TTL 위에 자기 시간을 **더한다**.

  - *스텁 리졸버(stub resolver)*: 스스로 재귀 탐색을 하지 않고, 설정된 재귀 리졸버에게 "대신 풀어 달라"고만 묻는 OS 쪽 해석기다.
  - *재귀 리졸버(recursive resolver)*: 루트부터 따라 내려가 답을 찾아 주는 서버다. 결과를 캐시한다.

### 2. TTL의 수명 — 카운트다운

```text
  권한 서버: api.example.com  300  IN A 203.0.113.10

  t=0     리졸버 캐시에 저장 (TTL 300)
  t=120   클라이언트 질의 -> 캐시 적중, TTL 180 으로 응답
  t=300   만료 -> 다음 질의에서 권한 서버에 다시 묻는다
```

- 같은 이름·타입·클래스의 레코드 묶음(RRset)은 TTL이 같아야 한다(RFC 2181 §5.2).
- TTL 0은 "캐시하지 말라"는 뜻이다. 조회 부하가 그만큼 권한 서버로 간다.
- RFC 8767 §4는 TTL 값을 며칠~몇 주 수준에서 자르라고 하고(SHOULD), 권장 상한으로 7일(604,800초)을 든다.

### 3. 부정 캐시 — "없다"는 답도 캐시된다

```text
  질의: new.example.com A
  응답: NXDOMAIN
        AUTHORITY 절: example.com  SOA  ... MINIMUM=3600 (예시), SOA 레코드 TTL=3600 (예시)

  리졸버: "new.example.com 은 없다"를 min(SOA.MINIMUM, SOA TTL) 동안 캐시
```

- 부정 응답은 두 종류다(RFC 2308 §1).
  - *NXDOMAIN*: 그 이름 자체가 없다.
  - *NODATA*: 이름은 있는데 그 타입(예: AAAA) 레코드가 없다.
- 부정 캐시 TTL = SOA 레코드의 MINIMUM 필드와 SOA 자신의 TTL 중 **작은 값**이다(RFC 2308 §3, §5).
  - SOA의 MINIMUM 필드는 원래 뜻이 여럿이었다. RFC 2308 §4가 "부정 응답 TTL"로 뜻을 고정했다.
- RFC 2308 §5는 리졸버가 부정 응답을 캐시하는 시간에 **자기 상한**을 두라고 한다. 그 상한은 1~3시간이 적당한 기본값이고, 하루를 넘으면 문제가 됐다고 적는다.
- 그래서 **레코드를 만들기 전에 그 이름을 먼저 조회하면** "없음"이 캐시된다. 레코드를 만든 뒤에도 그 시간 동안 안 보인다.

### 4. 애플리케이션 런타임 캐시 — JVM

```text
  java.security (OpenJDK)
    networkaddress.cache.ttl           주석: 기본 동작은 30초 캐시
    networkaddress.cache.negative.ttl  10
    networkaddress.cache.stale.ttl     기본 0 (낡은 값 사용 안 함)

  값의 뜻:  음수 = 영원히,  0 = 캐시 안 함,  양수 = 그 초만큼
```

- Oracle 문서: `networkaddress.cache.ttl`의 기본은 **보안 관리자가 설치돼 있으면 −1(영원히)**, 없으면 구현 의존이다.
  - OpenJDK 소스(`InetAddressCachePolicy.DEFAULT_POSITIVE = 30`)와 `java.security` 주석은 30초다.
- 이 값들은 **보안 속성**이다. `-D` 시스템 속성으로는 못 바꾼다(Oracle 문서 "not set by the -D option", AWS SDK 문서).
  - 바꾸는 법: `java.security` 파일 수정, 또는 시작 직후 `Security.setProperty(...)`.
  - 대체 경로: `-Dsun.net.inetaddr.ttl`, `-Dsun.net.inetaddr.negative.ttl`(보안 속성이 없을 때만 쓰이는 JDK 내부 속성).
- JVM 캐시는 **DNS 응답의 TTL을 보지 않는다.** 권한 서버가 TTL 5초를 줘도 JVM은 자기 정책대로 들고 있다.

Node.js는 구조가 다르다.
- `dns.lookup()`은 호출마다 OS의 `getaddrinfo(3)`를 libuv 스레드 풀에서 부른다(Node 문서). 캐시 여부는 OS 층 구성에 달린다.
- `dns.resolve4()` 등은 `getaddrinfo`를 거치지 않고 항상 네트워크로 질의한다. `{ ttl: true }`로 TTL을 받을 수 있다.

### 5. 검색 도메인과 ndots — 이름 하나가 질의 여러 개가 된다

```text
  /etc/resolv.conf (쿠버네티스 파드 예시, k8s 문서)
    nameserver 10.32.0.10
    search <ns>.svc.cluster.local svc.cluster.local cluster.local
    options ndots:5

  앱이 "api.example.com" (점 2개 < 5) 을 조회하면
    1) api.example.com.<ns>.svc.cluster.local   -> NXDOMAIN
    2) api.example.com.svc.cluster.local        -> NXDOMAIN
    3) api.example.com.cluster.local            -> NXDOMAIN
    4) api.example.com.                         -> 답
  A 와 AAAA 를 따로 물으면 위 과정이 타입마다 반복된다
```

- `search`: 짧은 이름 뒤에 차례로 붙여 볼 도메인 목록이다(resolv.conf(5)).
- `ndots:n`: 이름에 든 점이 n개보다 **적으면** 검색 목록을 먼저 붙여 본다. 기본값 1, 상한 15다(resolv.conf(5)).
- 쿠버네티스는 파드의 resolv.conf에 `ndots:5`를 넣는다. 서비스 이름 `data`처럼 짧은 이름을 풀기 위해서다.
- 대가는 외부 도메인 조회의 증폭이다. 위 예시에서 이름 하나가 4번 질의가 되고, A·AAAA를 각각 물으면 그 두 배가 된다.
- 끝에 점을 찍은 이름(`api.example.com.`)은 완전한 이름(FQDN)으로 취급해 검색 목록을 건너뛴다.

  - *FQDN(Fully Qualified Domain Name)*: 루트까지 다 적은 절대 이름이다. 끝의 `.`이 루트를 뜻한다.

### 6. 만료된 값을 계속 쓸 수 있나 — serve-stale

```text
  캐시 만료 -> 권한 서버에 재질의 -> 권한 서버 무응답
    옛 방식: SERVFAIL -> 서비스 전체가 "이름 해석 실패"
    serve-stale(RFC 8767): 만료된 답을 TTL 30초(권장)로 붙여 돌려준다
```

- RFC 8767은 리졸버가 권한 서버에서 갱신하지 못할 때 만료된 데이터를 쓸 수 있게 한다(MAY, §4).
  - 만료 레코드에 붙이는 TTL은 0보다 커야 하고(MUST), 30초를 권한다(§4).
  - 만료 뒤 얼마나 더 보관할지(최대 stale 타이머)는 §5의 예시 방법에서 1~3일을 제안한다.
- CoreDNS `cache` 플러그인에도 `serve_stale` 옵션이 있다. 기본 최대 TTL은 성공 응답 3600초, 부정 응답 1800초다(CoreDNS 문서).

## 쓰이는 자료구조·알고리즘

- **TTL 캐시 = 해시 맵 + 만료 시각** — 키는 (이름, 타입, 클래스), 값은 (레코드들, 만료 시각)이다.
  - 조회할 때 만료 시각을 지났으면 버리고 다시 묻는다(지연 만료).
  - [해시 맵](../../data-structure/05-hashmap/2-summary.md) 참고.
- **용량 제한과 교체** — 캐시 크기가 차면 오래 안 쓴 항목부터 버린다. 흔한 선택은 LRU다. [LRU 캐시](../../data-structure/10-lru-cache/2-summary.md) 참고.
- **프리페치** — 인기 항목을 만료 직전에 미리 갱신한다. 만료 순간의 지연 스파이크를 없앤다(CoreDNS `prefetch`).
- **검색 목록 전개** — 이름 하나를 후보 이름 목록으로 바꿔 순서대로 시도한다. 첫 성공에서 멈추는 선형 탐색이다.
- **캐시 계층의 낡음 합산** — TTL을 존중하는 층은 남은 TTL을 넘겨받아 상한이 유지된다. 자체 타이머를 쓰는 층은 그 시간이 더해진다.

## 적용 — 풀어나가는 법

### 1. 지금 각 층이 무엇을 들고 있는지 본다

```bash
# 재귀 리졸버가 준 남은 TTL (두 번 연달아 치면 줄어드는 게 보인다)
dig +noall +answer api.example.com

# 권한 서버에 직접 -> 원래 TTL
dig +noall +answer api.example.com @ns1.example.com

# 부정 캐시 시간 = min(SOA MINIMUM, SOA TTL)
dig +noall +answer example.com SOA

# 앱과 같은 경로(NSS)로 풀기 — /etc/hosts, search, ndots 가 반영된다
getent hosts api.example.com

# systemd-resolved 캐시 확인·비우기
resolvectl query api.example.com
resolvectl flush-caches

# 실제로 몇 번 질의가 나가는지 (ndots 증폭 확인)
sudo tcpdump -ni any port 53
```

### 2. JVM 설정

```java
// 애플리케이션 시작 직후, 어떤 조회보다 먼저
java.security.Security.setProperty("networkaddress.cache.ttl", "30");
java.security.Security.setProperty("networkaddress.cache.negative.ttl", "5");
```

- AWS SDK for Java 문서는 JVM TTL을 5초로 두기를 권한다. IP가 바뀌는 관리형 엔드포인트를 쓰기 때문이다.
- 값을 너무 낮추면 조회가 늘어 DNS 서버·지연 부담이 커진다. 페일오버 목표 시간과 조회 비용 사이에서 정한다.

### 3. Node.js에서 TTL 보기

```js
const dns = require('node:dns').promises;
const recs = await dns.resolve4('api.example.com', { ttl: true });
console.log(recs); // [{ address: '203.0.113.10', ttl: 60 }, ...]
```

### 4. 레코드 변경(이전·페일오버) 절차

1. 바꾸기 **전에** TTL을 낮춘다(예시: 3600 → 60).
2. **옛 TTL만큼 기다린다.** 이미 캐시된 사본은 옛 TTL로 살아 있기 때문이다.
3. 레코드를 바꾼다. 이제 낡음의 상한은 새 TTL(60초)이다.
4. 안정되면 TTL을 다시 올린다.
5. TTL을 따르지 않는 층(JVM 캐시, 커넥션 풀)은 따로 점검한다.

### 5. 쿠버네티스 조회 증폭 줄이기

- 외부 도메인은 코드·설정에서 끝에 점을 찍어 FQDN으로 쓴다(`api.example.com.`).
  - HTTP `Host` 헤더·TLS SNI에 점이 붙은 이름이 그대로 들어가는지는 클라이언트마다 확인한다 [?].
- 또는 파드 `dnsConfig.options`로 `ndots` 값을 낮춘다(k8s 문서의 Pod DNS Config).
- 노드 로컬 DNS 캐시를 두어 증폭된 질의가 클러스터 DNS까지 가지 않게 한다.

## 장애 시나리오와 대처

### 1. 페일오버 후 JVM이 죽은 IP로 계속 접속한다

- **현상**: DB·캐시 엔드포인트가 페일오버됐다. `dig`는 새 IP를 보여 주는데, 자바 서비스만 수 분째 연결 실패다.
- **보이는 형태**
  - `java.net.ConnectException: Connection refused` 또는 connect timeout이 옛 IP로 찍힌다.
  - 재시작한 인스턴스만 정상이 된다.
- **원인**
  - JVM `InetAddress` 캐시가 DNS TTL과 무관하게 자기 정책으로 옛 IP를 들고 있다.
  - 보안 관리자가 설치된 환경이면 기본값이 "영원히"(−1)다(Oracle 문서).
  - 또는 커넥션 풀이 옛 IP로 맺은 연결을 계속 쓴다. DNS 캐시와 별개로, 이미 맺은 TCP 연결은 DNS 변경을 모른다.
- **대처**
  - `networkaddress.cache.ttl`을 명시적으로 짧게 둔다(보안 속성).
  - 커넥션 풀에 최대 수명(max lifetime)을 둔다. 연결 오류가 나면 풀을 비우고 다시 해석한다.

### 2. 새 레코드가 한참 안 보인다 — 부정 캐시

- **현상**: `new.example.com` A 레코드를 방금 만들었는데, 일부 사용자·서버에서 계속 "없는 이름"이다.
- **보이는 형태**
  - `dig new.example.com`의 `status: NXDOMAIN`, AUTHORITY 절에 SOA가 보인다.
  - Java `java.net.UnknownHostException`, Node `getaddrinfo ENOTFOUND`.
  - 권한 서버에 직접 물으면(`@ns1`) 정상이다.
- **원인**
  - 레코드를 만들기 전에 누군가(헬스체크, 배포 스크립트) 그 이름을 조회했다.
  - 리졸버가 NXDOMAIN을 min(SOA MINIMUM, SOA TTL) 동안 캐시했다(RFC 2308).
- **대처**
  - 레코드를 먼저 만들고, 그다음에 트래픽·헬스체크를 켠다.
  - 급하면 운영하는 리졸버의 캐시를 비운다(`resolvectl flush-caches`, 리졸버별 명령). 공용 리졸버 캐시는 기다리는 수밖에 없다.
  - 존의 SOA MINIMUM을 과도하게 길게 두지 않는다.

### 3. 쿠버네티스에서 외부 호출이 느리고 DNS 서버가 바쁘다 — ndots:5

- **현상**: 외부 API 호출 지연의 앞부분이 들쭉날쭉하다. CoreDNS CPU·질의 수가 높다.
- **보이는 형태**
  - `tcpdump port 53`에 `api.example.com.<ns>.svc.cluster.local` 같은 NXDOMAIN 질의가 줄지어 보인다.
  - CoreDNS 지표에서 NXDOMAIN 비율이 높다.
- **원인**
  - `ndots:5` 때문에 점이 5개 미만인 외부 이름이 검색 목록을 먼저 거친다.
  - A·AAAA를 각각 물으면 질의가 더 늘어난다.
- **대처**
  - 외부 이름을 FQDN(끝 점)으로 쓰거나 파드의 `ndots`를 낮춘다.
  - 노드 로컬 DNS 캐시로 증폭된 질의를 흡수한다.

### 4. TTL을 늦게 낮춰서 이전이 오래 걸린다

- **현상**: IP를 바꾼 뒤 몇 시간 동안 일부 트래픽이 옛 서버로 간다.
- **보이는 형태**: 옛 서버의 접속 로그가 옛 TTL(예시: 86400초)에 걸쳐 천천히 줄어든다.
- **원인**
  - 레코드를 바꾸는 순간 TTL을 같이 낮췄다.
  - 이미 캐시된 사본은 **이전 TTL**로 저장돼 있어 그 시간이 지나야 사라진다.
- **대처**
  - TTL을 먼저 낮추고 옛 TTL만큼 기다린 뒤 바꾼다(적용 §4).
  - 옛 서버는 옛 TTL이 지날 때까지 살려 두거나 새 서버로 프록시한다.

### 5. 권한 서버 장애 — 캐시가 만료되는 순간 전부 실패

- **현상**: 권한 DNS 제공자 장애가 시작되고 TTL이 지나자 이름 해석이 일제히 실패한다.
- **보이는 형태**: `dig`의 `status: SERVFAIL`, 애플리케이션의 `UnknownHostException`·`EAI_AGAIN`.
- **원인**
  - 캐시가 살아 있는 동안은 버티다가 만료 시점에 재질의가 실패한다.
  - TTL이 짧을수록 더 빨리 무너진다.
- **대처**
  - 리졸버에서 serve-stale(RFC 8767, CoreDNS `serve_stale`)을 켠다.
  - 권한 DNS를 둘 이상의 제공자로 운영한다.
  - TTL은 "변경 민첩성"과 "권한 서버 장애 내성" 사이의 선택임을 기억한다.

## 핵심 문장

- TTL은 레코드 주인이 정한 "캐시해도 되는 시간"이고, 캐시는 속도를 주는 대신 변경을 늦게 퍼뜨린다.
- TTL을 존중하는 캐시는 남은 TTL을 넘겨받아 낡음 상한이 유지되지만, JVM `InetAddress` 캐시처럼 자체 타이머를 쓰는 층은 그 시간을 더한다.
- "없다"도 캐시된다. 부정 캐시 TTL은 min(SOA MINIMUM, SOA TTL)이라(RFC 2308), 레코드를 만들기 전에 조회하면 한동안 안 보인다.
- TTL은 바꾸기 전에 낮추고 옛 TTL만큼 기다려야 효과가 있다.
- `ndots:5`와 검색 목록은 짧은 서비스 이름을 풀어 주지만, 외부 도메인 조회를 여러 번의 NXDOMAIN 질의로 늘린다.

## 관련 주제·근거

- 선행
  - [27-dns-resolution](../27-dns-resolution/2-summary.md) — 재귀·반복 질의, 레코드 종류.
- 후속·연결
  - [51-email-delivery-and-authentication](../51-email-delivery-and-authentication/2-summary.md) — TXT 레코드 기반 인증(SPF·DKIM·DMARC)
  - [35-http-connection-management](../35-http-connection-management/2-summary.md) — 커넥션 풀이 옛 IP를 쥐는 문제.
  - `reliability/07-timeout-taxonomy-by-layer` — DNS 타임아웃이 호출 타임아웃에 포함되는 방식. 미작성([reliability 영역 표](../../reliability/README.md))
  - [data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md) · [data-structure/10-lru-cache](../../data-structure/10-lru-cache/2-summary.md)
- RFC 1035 §3.2.1 TTL 필드 <https://www.rfc-editor.org/rfc/rfc1035>
- RFC 2181 §5.2 RRset TTL 동일 · §8 TTL 범위 <https://www.rfc-editor.org/rfc/rfc2181>
- RFC 2308 §1 NXDOMAIN·NODATA 정의 · §3, §5 부정 캐시 TTL · §4 SOA MINIMUM의 뜻 <https://www.rfc-editor.org/rfc/rfc2308>
- RFC 8767 §4 TTL 상한 권고·stale 응답 TTL · §5 stale 타이머 <https://www.rfc-editor.org/rfc/rfc8767>
- nscd.conf(5) — DNS는 이름 서비스가 준 TTL을 쓴다 <https://man7.org/linux/man-pages/man5/nscd.conf.5.html>
- Unbound `unbound.conf` — `cache-min-ttl`(TTL 하한 강제) <https://unbound.docs.nlnetlabs.nl/en/latest/manpages/unbound.conf.html>
- nginx `ngx_http_upstream_module` — `server ... resolve`(재시작 없이 IP 변경 추적) <https://nginx.org/en/docs/http/ngx_http_upstream_module.html>
- resolv.conf(5) — `search`, `ndots`(기본 1, 상한 15) <https://man7.org/linux/man-pages/man5/resolv.conf.5.html>
- Kubernetes "DNS for Services and Pods" — 파드 resolv.conf, `ndots:5`, Pod DNS Config <https://kubernetes.io/docs/concepts/services-networking/dns-pod-service/>
- Oracle Java Networking 문서 — `networkaddress.cache.ttl`·`negative.ttl` <https://docs.oracle.com/en/java/javase/21/core/java-networking.html>
- OpenJDK `java.security`·`InetAddressCachePolicy.java`(기본 30초, stale.ttl) <https://github.com/openjdk/jdk/blob/master/src/java.base/share/conf/security/java.security>
- AWS SDK for Java "Set the JVM TTL for DNS name lookups" <https://docs.aws.amazon.com/sdk-for-java/latest/developer-guide/jvm-ttl-dns.html>
- Node.js `dns` 문서 "Implementation considerations" <https://nodejs.org/api/dns.html>
- CoreDNS `cache` 플러그인 <https://coredns.io/plugins/cache/>
