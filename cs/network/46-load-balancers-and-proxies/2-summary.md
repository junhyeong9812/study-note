# network/46-load-balancers-and-proxies — 로드밸런서와 리버스 프록시: L4/L7·분배·헬스체크·드레이닝·XFF 신뢰 경계 — 정리 (힌트)

## 해결하는 문제

서버 한 대로는 두 가지가 안 된다.\
트래픽이 한 대의 처리량을 넘으면 받을 수 없다.\
그 한 대가 죽거나 배포로 내려가면 서비스가 멈춘다.

서버를 여러 대 두면 새 문제가 생긴다.\
클라이언트가 서버 목록을 다 알아야 한다.\
어느 서버가 죽었는지도 클라이언트가 알아야 한다.

쉬운 예: 은행 창구가 여러 개다.\
입구의 안내원이 번호표를 보고 빈 창구로 보낸다.\
쉬는 창구에는 보내지 않는다.\
마감하는 창구는 새 손님을 받지 않고, 상담 중인 손님만 끝낸다.

똑같은 구조다.\
안내원 = 로드밸런서, 창구 = 백엔드 서버.\
빈 창구 고르기 = 분배 알고리즘.\
쉬는 창구 거르기 = 헬스체크.\
마감 창구 처리 = 연결 드레이닝.

실무 예:
- nginx·HAProxy·Envoy·AWS ALB/NLB가 서버 여러 대 앞에서 주소 하나(VIP·도메인)를 대신 받는다.
- 배포 때 서버를 하나씩 빼고 넣어도 사용자는 끊김을 보지 않아야 한다.
- L7 프록시(연결을 새로 여는 프록시) 뒤 서버는 클라이언트 IP 대신 프록시 IP를 본다. 그래서 `X-Forwarded-For` 같은 헤더로 원래 주소를 전한다. 이 헤더를 잘못 믿으면 IP 기반 차단·레이트 리밋이 뚫린다.

기초 설명(L4/L7 표, 분배 알고리즘 표, 헬스체크 3종, 깊은 헬스체크 연쇄)은 원고 [systems/server-design/02-request-path §3](../../systems/server-design/02-request-path.md)에 있다.\
스티키 세션 표는 같은 원고 §5에 있다.\
이 노트는 그 위에 원리 그림, 제품별 기본값, 실험, 장애 진단을 더한다.

## 동작·원리

### 1. 요청 경로에서 LB가 서는 자리

```text
  클라이언트
     │  DNS로 VIP(가상 IP)·도메인을 얻는다 (27번)
     v
  [CDN·엣지] ───────── 캐시로 끝낼 수 있으면 여기서 끝 (47번)
     │
     v
  [L4 LB]  연결·흐름(TCP/UDP) 단위로 백엔드를 고른다. 보통 HTTP는 보지 않고 넘긴다
     │
     v
  [L7 LB · 리버스 프록시 · API 게이트웨이]  HTTP 요청 단위로 고른다. 보통 TLS를 여기서 푼다
     │
     v
  [앱 서버 1] [앱 서버 2] [앱 서버 3]   ← 헬스체크로 살아 있는 것만 후보
```

- *로드밸런서(LB)*: 들어온 요청·연결을 여러 백엔드 중 하나로 보내는 장치·프로그램이다.
- *리버스 프록시*: 서버 쪽에 서서 클라이언트 요청을 대신 받아 뒤의 서버에 다시 보내는 프록시다. 클라이언트는 뒤의 서버를 모른다.
  - 흔한 오해: "리버스 프록시 = 로드밸런서"는 아니다. 리버스 프록시는 백엔드가 하나여도 쓴다(TLS 종료·캐시·압축). 백엔드가 여럿이면 LB 역할을 겸한다.
- *VIP(virtual IP)*: 특정 서버 한 대가 아니라 서비스를 가리키는 주소다. LB가 이 주소로 오는 것을 받아 나눈다.
- API 게이트웨이(인증·레이트 리밋·라우팅을 모은 L7 프록시)는 [api-design/19](../../api-design/19-api-gateway-and-bff/2-summary.md)에서 다룬다.

### 2. L4와 L7 — 무엇을 단위로 고르나

```text
  L4 (연결 단위)                               L7 (요청 단위)
  ─────────────────────────────                ──────────────────────────────────
  첫 패킷(TCP면 SYN) → 흐름 해시 → 백엔드 B 선택   TCP·TLS를 LB가 끝까지 받는다
  이후 이 연결의 패킷은 전부 B로                    HTTP 요청을 하나 읽을 때마다 백엔드를 고른다
  (연결 추적 표에 기록)                           요청1 → A, 요청2 → C, 요청3 → B
                                               경로·헤더·쿠키를 보고 고를 수 있다
  HTTP 내용은 보지 않는다                        TLS 종료·재시도·헤더 추가가 가능하다
```

- *5-tuple*: (출발지 IP, 출발지 포트, 목적지 IP, 목적지 포트, 프로토콜). 연결 하나를 가리키는 키다.
- *TLS 종료*: 클라이언트와의 TLS를 LB가 풀어 평문 HTTP로 본다. 핸드셰이크는 [29번](../29-tls-handshake/2-summary.md).
  - L4라서 TLS를 못 푸는 것은 아니다. AWS NLB는 TLS 리스너면 TLS를 종료하고, TCP 리스너면 암호문을 그대로 대상에 넘긴다(NLB 리스너 문서). TLS 종료 여부는 리스너 설정에 달렸다.
- 흐름 해시에 무엇을 넣는지는 제품마다 다르다. 그림의 5-tuple은 한 예다. AWS NLB는 프로토콜, 출발지·목적지 IP와 포트, TCP 시퀀스 번호로 대상을 고르고, TCP 연결 하나를 수명 내내 같은 대상으로 보낸다(ELB "How Elastic Load Balancing works" 문서). UDP는 SYN이 없으므로 흐름(같은 5-tuple의 패킷 묶음) 단위로 다룬다.
- L4는 연결이 정해지면 그 연결의 패킷을 같은 백엔드로 보내야 한다. 중간에 바뀌면 TCP가 깨진다.
  - Google Maglev(L4 소프트웨어 LB)는 백엔드를 일관 해싱으로 고르고, 그 결과를 로컬 연결 추적 표(5-tuple 해시 → 백엔드)에 적는다(Eisenbud 외 NSDI 2016 §3.3 Backend Selection). 연결 추적은 NAT의 conntrack과 같은 발상이다([11번](../11-nat-and-conntrack/2-summary.md)).
- L7은 요청마다 고른다. 그래서 클라이언트↔LB 연결이 오래 살아도 요청은 퍼진다. AWS ALB가 그렇게 동작한다는 근거는 [35번](../35-http-connection-management/2-summary.md)의 장애 시나리오 4에 있다.
  - 연결 단위로 고르는 구간(L4, 클라이언트 측 분산)에서는 오래 사는 연결이 옛 서버에 묶인다. 35번 장애 시나리오 4와 [36번](../36-http2-multiplexing/2-summary.md)(한 연결에 요청 여럿)이 이 문제를 다룬다.

### 3. 프록시에는 연결이 둘이다

```text
   클라이언트 172.28.0.2:38266 ──연결①──> nginx :8081
                                         nginx 172.28.0.3:59488 ──연결②──> 백엔드 :9002

   백엔드가 보는 상대 주소 = 172.28.0.3 (nginx)   ← 클라이언트 주소가 아니다
```

- L7 프록시는 연결 ①을 끝내고 연결 ②를 새로 연다. 두 연결의 타임아웃·keep-alive는 따로다([35번 §6](../35-http-connection-management/2-summary.md)).
- 그래서 백엔드는 클라이언트 IP를 직접 볼 수 없다. 프록시가 헤더(`X-Forwarded-For`, `Forwarded`)로 전한다(§8).
- 502·504는 연결 ②에서 생긴 문제를 프록시가 연결 ①로 알리는 응답이다. 누가 만든 5xx인지 가르는 법은 [52번 §7](../52-network-symptom-index/2-summary.md).

실험에서 nginx 컨테이너 안의 연결을 본 결과(긴 요청 하나가 처리 중일 때, 아래 실험 환경과 같다):

```text
$ docker exec sn-net46-w-ngx netstat -tn | grep ESTAB
tcp   0   0 172.28.0.3:59488    172.28.0.2:9002     ESTABLISHED    ← 연결② nginx → 백엔드
tcp   0   0 172.28.0.3:8081     172.28.0.2:38266    ESTABLISHED    ← 연결① 클라이언트 → nginx
```

- 이 실험은 클라이언트와 백엔드가 같은 컨테이너(172.28.0.2)에 있다. 그래서 두 줄의 상대 주소가 같다. 포트(38266은 클라이언트, 9002는 백엔드)로 구분한다.

### 4. 분배 알고리즘

```text
  요청 순서:  r1 r2 r3 r4 r5 r6 ...      백엔드 A B C (A가 느려져 처리 중 요청이 쌓인다)

  라운드로빈        r1→A r2→B r3→C r4→A ...      처리 중 개수는 안 본다. A에도 1/3이 간다
  least_conn       처리 중 연결이 가장 적은 곳     A에 요청이 쌓이면 B·C로 간다
  P2C(두 개 중 하나) 무작위로 둘을 뽑아 덜 바쁜 쪽     전체를 훑지 않고도 least에 가깝다
  해시(키 기반)     hash(키) → 고정 백엔드          같은 키는 같은 곳 (캐시·세션 지역성)
```

- *라운드로빈(round-robin)*: 차례대로 돌아가며 보낸다. 가중치가 있으면 가중치 비율로 돈다.
- *least_conn(최소 연결)*: 지금 처리 중인 연결(요청)이 가장 적은 백엔드로 보낸다.
- *P2C(power of two choices)*: 백엔드 둘을 무작위로 뽑아 덜 바쁜 쪽에 보낸다.

제품별 기본값과 이름(문서로 확인한 것):

| 제품 | 기본 | 다른 선택지 | 근거 |
|---|---|---|---|
| nginx 오픈소스 `upstream` | 가중 라운드로빈 | `least_conn`, `hash 키 [consistent]`, `ip_hash`, `random [two]` | nginx upstream 모듈 문서 |
| AWS ALB 대상 그룹 | 라운드로빈 | least outstanding requests, weighted random | ALB 대상 그룹 속성 문서 |
| HAProxy 3.0 `balance` | `roundrobin`(다른 알고리즘·모드·옵션을 정하지 않았을 때) | `leastconn`, `random(<draws>)`(기본 draws 2), `hash`·`source`·`uri` 등 | HAProxy 3.0.29 설정 문서 |
| Envoy 클러스터 `lb_policy` | `ROUND_ROBIN` | least request(가중치가 같으면 P2C, 기본 2개 추출), ring hash, Maglev, random | Envoy 1.40-dev 문서 "Supported load balancers"·`cluster.proto`(`ROUND_ROBIN (DEFAULT)`) |

- HAProxy 문서는 `leastconn`을 LDAP·SQL처럼 **아주 긴 세션**에 권하고, HTTP처럼 짧은 세션에는 잘 맞지 않는다고 적는다.
- Envoy 문서는 P2C가 전체를 훑는 O(N) 방식과 거의 같다는 결과를 Mitzenmacher 외의 연구로 든다. 원 논문 서지는 `[?]`.
- 참고: 원고 §3 분배 표의 Least Connections '함정' 칸에 있는 "일반적으로 가장 무난한 기본값"은 함정이 아니라 평가이고, 근거도 없다. nginx·ALB의 기본은 라운드로빈이다. HAProxy 문서는 짧은 HTTP 세션에 `leastconn`이 잘 맞지 않는다고 적는다. least_conn의 실제 함정은 원고가 다음 줄에 쓴 "새로 뜬 서버로 쏠림"과 아래 실험의 조건(동시 처리 수가 차이를 드러낼 만큼 있어야 함)이다.

#### 슬로우 스타트 — 새 서버로 한꺼번에 몰리지 않게

- least_conn은 방금 뜬 서버(처리 중 0개)를 가장 한가하다고 본다. 캐시·JIT가 차지 않은 서버에 요청이 몰릴 수 있다(원고 §3).
- *슬로우 스타트*: 새로 들어온 서버의 가중치를 0에서 정상값까지 시간에 걸쳐 올린다.
- 제품마다 다르다.
  - nginx `server ... slow_start=시간`은 **상용판(nginx Plus) 전용** 파라미터다. `hash`·`ip_hash`·`random`과는 같이 못 쓴다(upstream 문서).
  - HAProxy `slowstart`는 0%에서 100%까지 선형으로 올린다(설정 문서).
  - AWS ALB slow start mode는 least outstanding requests·weighted random과 같이 쓸 수 없다(대상 그룹 속성 문서).
  - 콜드 스타트 자체는 [reliability/42](../../reliability/42-cold-start-and-scale-from-zero/2-summary.md).

### 실험 1: 느린 백엔드 하나 — 라운드로빈 vs least_conn

- 구성: nginx 1.27.5(`nginx:1.27-alpine`, `worker_processes 1`) 뒤에 JDK 21 `HttpServer` 백엔드 3개(be1~be3). 클라이언트는 JDK `HttpClient`로 동시 12개 작업자가 600건을 보낸다. 요청 하나는 20ms 걸린다.
- be1에만 300ms를 더해 "느려진 인스턴스"를 만든다.
- 환경: 리눅스 7.0.0-34 호스트, Docker 29.1.3, 컨테이너마다 `--cpus=2`, 외부와 끊긴 `--internal` 도커 네트워크, eclipse-temurin:21-jdk(21.0.12), 2026-10-07.

```nginx
upstream rr { server be:9001; server be:9002; server be:9003; }               # 기본 = 가중 라운드로빈
upstream lc { least_conn; server be:9001; server be:9002; server be:9003; }
```

```text
== be1 +300ms #1
:8081(rr) total=600 conc=12 wall=6942ms p50=24ms p95=324ms p99=565ms
  200 be1  200건 (33.3%) p50=323ms
  200 be2  200건 (33.3%) p50=24ms
  200 be3  200건 (33.3%) p50=24ms
:8082(lc) total=600 conc=12 wall=3518ms p50=26ms p95=325ms p99=588ms
  200 be1   36건 (6.0%) p50=326ms
  200 be2  282건 (47.0%) p50=26ms
  200 be3  282건 (47.0%) p50=25ms
== be1 +300ms #2
:8081(rr) wall=6941ms  be1 200건(33.3%) be2 200건 be3 200건
:8082(lc) wall=3091ms  be1  32건(5.3%)  be2 284건 be3 284건
```

- 관찰: 라운드로빈은 느린 be1에도 정확히 1/3(200건)을 보냈다. 전체 시간은 6.9~7.1초였다(점검 재실행 포함 3회: 6942·6941·7092ms).
- least_conn은 be1에 5~6%(32~36건)만 보냈다. 전체 시간은 3.1~3.5초로 절반쯤이었다(점검 재실행: be1 32건, 3137ms).
- 지연이 없을 때는 두 방식 모두 약 1/3씩 갔다(rr 200/200/200, lc 199/199/202, 점검 재실행 lc 197/198/205).
- p99가 지연 없는 실행에서도 500~630ms였다. 실행 초반의 연결 수립·JIT 준비 때문으로 보이며, 원인을 따로 확인하지는 않았다.
- 해석: least_conn이 이긴 이유는 "처리 중 개수"가 느림을 드러냈기 때문이다. 동시 요청이 거의 없으면(처리 중이 늘 0~1) 이 신호가 생기지 않는다(이 실험에서 따로 재지는 않았다).
- 수동 헬스체크(§6)는 느림을 잡지 못한다. 실패가 아니라 늦을 뿐이기 때문이다.

### 5. 해시로 고정하기 — mod-N, 해시 링, Maglev

```text
  mod-N:   백엔드 = hash(키) mod N
           N이 100 → 99가 되면 키 대부분의 나머지가 바뀐다

  해시 링: 백엔드마다 가상 노드 여러 개를 원 위에 뿌린다
           키는 시계 방향으로 처음 만나는 노드로 간다
           ...─(A)───(C)──●키──(B)───(A)─...      ●키 → B
           B를 빼면 B 몫만 다음 노드로 옮겨 간다

  Maglev:  크기 M(소수)의 조회 테이블을 미리 채운다
           칸:   0   1   2   3   4   5   6
           주인: B2  B1  B2  B1  B3  B3  B1      키 → 테이블[hash(키) mod M]
           백엔드마다 칸 수가 거의 같다(차이 최대 1칸)
```

- *일관 해싱(consistent hashing)*: 백엔드가 늘거나 줄 때 일부 키만 자리를 옮기게 하는 해싱이다. 해시 링의 구현은 [data-structure/31](../../data-structure/31-consistent-hashing/2-summary.md).
- *가상 노드*: 한 백엔드를 링 위 여러 자리에 둔 것. 몫을 고르게 하려고 쓴다.
- nginx `hash 키 consistent`는 ketama 방식의 일관 해싱이다. `consistent`를 빼면 서버 추가·제거 때 대부분의 키가 다른 서버로 갈 수 있다(upstream 문서).

Maglev 테이블 채우기(Eisenbud 외 NSDI 2016 §3.4 Pseudocode 1):

```java
// 백엔드 i의 선호 순열: permutation[i][j] = (offset_i + j * skip_i) mod M
//   offset = h1(이름) mod M,  skip = h2(이름) mod (M-1) + 1,  M은 소수
static int[] populate(long[][] offSkip, int M) {
    int N = offSkip.length;
    int[] next = new int[N], entry = new int[M];
    Arrays.fill(entry, -1);
    int n = 0;
    while (true) {
        for (int i = 0; i < N; i++) {                       // 백엔드가 돌아가며
            long c = (offSkip[i][0] + next[i] * offSkip[i][1]) % M;
            while (entry[(int) c] >= 0) {                   // 자기 선호 순서에서 아직 빈 칸을 찾아
                next[i]++;
                c = (offSkip[i][0] + next[i] * offSkip[i][1]) % M;
            }
            entry[(int) c] = i;                             // 차지한다
            next[i]++;
            if (++n == M) return entry;                     // 칸이 다 차면 끝
        }
    }
}
```

- M이 소수여야 skip(1~M-1)이 M과 서로소가 된다. 그래야 순열이 0~M-1을 다 돈다(논문 §3.4). 서로소는 [algorithm/28](../../algorithm/28-number-theory/2-summary.md).
- 백엔드가 차례로 한 칸씩 가져가므로 칸 수는 ⌊M/N⌋ 또는 ⌈M/N⌉이다. 논문은 M을 100×N보다 크게 잡아 몫 차이를 1% 안으로 둔다고 적는다.
- 논문의 선택: 고른 부하를 재배치 최소화보다 앞에 둔다. 평상시에는 연결이 같은 Maglev 장비로 계속 오고 그 장비의 연결 추적 표가 기존 배정을 지키므로, 테이블이 조금 바뀌어도 기존 연결이 리셋되지 않는다(§3.4).
  - 단 연결이 다른 Maglev 장비로 옮겨 가면(장비 추가·제거·교체) 새 장비에는 그 연결의 기록이 없다. 이때 리셋은 테이블이 바뀐 칸 수에 비례하고, 백엔드 변경이 같이 일어나면 연결이 깨진다(§3.3·§3.4). 연결 추적 표가 가득 찬 경우도 기댈 수 없다(§3.3).
- 논문 기본 테이블 크기는 65537이다(§5.3). Envoy Maglev도 기본 65537이다. Envoy 개요 문서는 "fixed table size of 65537"이라 적지만, API의 `table_size`(소수, 5000011 이하)로 바꿀 수 있고 키우면 재배치가 준다고 적는다(`cluster.proto` `MaglevLbConfig`).

### 실험 2: Maglev 모형 — 논문 표 재현, 링·mod-N과 비교

- **모형**이다. 위 `populate`를 JDK 21로 그대로 짰다. h1·h2·키 해시는 SHA-256 다이제스트의 서로 다른 8바이트 조각을 쓴다. 실제 Maglev·Envoy의 해시 함수와 다르다.
- 환경: eclipse-temurin:21-jdk 컨테이너 `--network none --cpus=2`.

① 논문 Table 1 재현(M=7, (offset, skip) = B1 (3,4), B2 (0,2), B3 (3,1), B2 제거 전후):

```text
[Table 1 재현] 칸  before  after
  0  B2  B1
  1  B1  B1
  2  B2  B1
  3  B1  B1
  4  B3  B3
  5  B3  B3
  6  B1  B3   <- B2 몫이 아닌데 바뀐 칸
```

- 논문 Table 1의 before(B2 B1 B2 B1 B3 B3 B1)·after(B1 B1 B1 B1 B3 B3 B3)와 같다. 논문도 "B2 칸 말고는 7번째 칸 하나만 바뀐다"고 적는다.

② 백엔드 100개, 키 100만 개(`user_0000000`~), 백엔드 1대 제거(서로 다른 3대로 3회):

```text
[N=100, 키 1,000,000개, 제거=be-037]  (이상적 이동 = 1/N = 1.00%)
  Maglev M=65537 (칸 655~656) 부하 max/평균=1.026 min/평균=0.981 | 1대 제거 시 이동 키 1.60% (제거된 백엔드 몫 아닌 키의 이동 0.60%)
  Maglev M=655373 (칸 6553~6554) 부하 max/평균=1.024 min/평균=0.976 | 1대 제거 시 이동 키 1.15% (제거된 백엔드 몫 아닌 키의 이동 0.15%)
  해시 링 가상노드 100          부하 max/평균=1.221 min/평균=0.763 | 1대 제거 시 이동 키 0.89% (제거된 백엔드 몫 아닌 키의 이동 0.00%)
  해시 링 가상노드 160          부하 max/평균=1.208 min/평균=0.834 | 1대 제거 시 이동 키 0.91% (제거된 백엔드 몫 아닌 키의 이동 0.00%)
  mod-N                  부하 max/평균=1.029 min/평균=0.982 | 1대 제거 시 이동 키 99.00% (제거된 백엔드 몫 아닌 키의 이동 97.99%)
(첫 회차만 실었다. 나머지 두 회차(be-071·be-005 제거)는 아래 표의 범위에 들어 있다.)
```

| 방식 | 키 부하 max/평균 | 1대 제거 시 이동 키 (3회 범위) | 제거된 백엔드 몫이 아닌 키의 이동 |
|---|---|---|---|
| Maglev M=65537 | 1.026 (테이블 칸은 655~656) | 1.58~1.60% | 0.58~0.60% |
| Maglev M=655373 | 1.024 (칸 6553~6554) | 1.14~1.15% | 0.13~0.15% |
| 해시 링 가상 노드 100 | 1.221 | 0.89~1.12% | 0.00% |
| 해시 링 가상 노드 160 | 1.208 | 0.91~1.04% | 0.00% |
| mod-N | 1.029 | 98.99~99.00% | 97.97~98.01% |

- 관찰 1: Maglev 테이블 칸 수는 백엔드마다 655~656으로 1칸 차이였다. 키 부하의 max/평균 1.026은 키 100만 개를 표본으로 쓴 데서 오는 흔들림이 섞인 값이다.
- 관찰 2: 해시 링(가상 노드 100)은 가장 많이 받는 백엔드가 평균의 1.22배였다. 같은 키 수에서 Maglev보다 덜 고르다.
- 관찰 3: 링은 제거된 백엔드의 키만 옮겼다(그 밖 0.00%). Maglev는 그 밖의 키도 0.6%쯤 옮겼다. 그래서 전체 이동이 링의 약 1.4~1.8배였다(3회 범위). Envoy 문서도 Maglev는 호스트가 빠질 때 링보다 약 두 배의 키가 움직이며, 테이블을 키우면 줄어든다고 적는다. 이 모형에서도 M을 10배로 키우자 0.6% → 0.15%로 줄었다.
- 관찰 4: mod-N은 부하는 고르지만 1대만 빠져도 키의 99%가 자리를 옮겼다. 캐시 서버 앞이라면 히트율이 거의 0이 된다.
- 테이블 생성 시간은 이 컨테이너에서 N=100, M=65537일 때 평균 9.5~9.7ms, M=655373일 때 126~130ms였다(5회 평균을 2번 실행, SHA-256 포함). 논문은 자기 환경에서 1.8ms → 22.9ms로 늘어 테이블을 무한정 키울 수 없다고 적는다. 수치 자체는 구현·환경이 달라 비교하지 않는다.

### 6. 헬스체크 — 누구를 후보에 넣나

```text
  능동(active) 헬스체크                      수동(passive) 헬스체크
  LB가 주기적으로 /health 를 따로 묻는다       실제 요청의 실패를 센다
  요청이 없어도 죽은 서버를 안다               실제 요청 일부가 실패해야 안다
  예: ALB·HAProxy check·k8s probe·          예: nginx 오픈소스 max_fails/fail_timeout,
      nginx Plus health_check                  Envoy outlier detection

  상태 전이 (연속 횟수로 판정 — 한 번의 흔들림으로 넣고 빼지 않게)
     healthy ──(연속 실패 U회)──> unhealthy ──(연속 성공 H회)──> healthy
```

- *능동 헬스체크*: LB가 백엔드에 검사용 요청을 주기적으로 보낸다.
- *수동 헬스체크*: 실제 트래픽의 오류·타임아웃을 보고 판정한다. Envoy는 이것을 *outlier detection*(이상치 감지·축출)이라 부른다.
- 연속 횟수 판정은 넣고 빼기가 흔들리는 것(플래핑)을 막는 히스테리시스다([reliability/33](../../reliability/33-hysteresis-and-flapping/2-summary.md)).

제품별 기본값(문서로 확인한 것만):

| 제품 | 간격 | 타임아웃 | 비정상 판정 | 정상 복귀 | 근거 |
|---|---|---|---|---|---|
| AWS ALB (대상 유형 instance·ip) | 30초 | 5초 | 연속 2회 실패 | 연속 5회 성공 | 대상 그룹 헬스체크 문서 |
| Kubernetes probe | 10초 | 1초 | 연속 3회 실패 | 1회 성공 | probe 문서 |
| HAProxy `check` | 2초(`inter`) | `inter`와 같음(`timeout check` 없을 때) | 연속 3회(`fall`) | 연속 2회(`rise`) | 설정 문서 |
| nginx 오픈소스 | 능동 검사 없음 | — | `fail_timeout`(10초) 안에 `max_fails`(1)회 실패 | `fail_timeout` 뒤 실제 요청으로 다시 시도 | upstream 문서 |

- nginx 오픈소스에서 무엇을 "실패"로 세는지는 `proxy_next_upstream`이 정한다. `error`·`timeout`·`invalid_header`는 지시어에 없어도 실패로 센다. `http_500` 등은 적었을 때만 센다. `http_403`·`http_404`는 실패로 세지 않는다(proxy 모듈 문서).
- 서버가 한 대뿐인 그룹에서는 `max_fails`·`fail_timeout`이 무시되고 그 서버는 unavailable로 표시되지 않는다(upstream 문서).

#### 헬스체크 3종과 무엇을 검사하나

- liveness·readiness·startup의 뜻은 원고 §3 표를 본다.
- Kubernetes에서 readiness가 실패하면 EndpointSlice 컨트롤러가 그 Pod IP를 서비스 엔드포인트에서 뺀다(probe 문서). 재시작은 liveness 실패 때 일어난다.
- 무엇을 검사할지에 대해 두 1차 문서가 강조점이 다르다.
  - Kubernetes 문서: 앱이 뒤쪽 서비스에 엄격히 의존하면 readiness가 필요한 뒤쪽 서비스까지 확인하게 할 수 있다고 적는다. 오류만 낼 Pod에 트래픽을 보내지 않으려는 목적이다.
  - Spring Boot Actuator 문서: liveness는 외부 시스템 검사에 의존하면 안 된다고 적는다. 외부 시스템이 실패하면 쿠버네티스가 전 인스턴스를 재시작해 연쇄 장애를 만들 수 있어서다. readiness에 외부 시스템을 넣을지는 개발자가 신중히 정하라고 적는다. 그래서 Spring Boot는 readiness 그룹에 외부 검사를 기본으로 넣지 않는다.
  - 같은 문서는 필수가 아닌 외부 시스템(서킷 브레이커·폴백이 있는 것)은 넣지 말라고 한다. **전 인스턴스가 공유하는** 시스템은 판단의 문제라고 적는다. 넣으면 그 시스템이 죽을 때 앱이 서비스에서 빠지는 것을 감수하고, 빼면 호출 쪽 서킷 브레이커 등 위쪽에서 다룬다.
- 두 문서를 합치면: 인스턴스마다 따로인 의존성은 readiness에 넣을 수 있다. 전 인스턴스가 공유하는 의존성(DB 하나)을 넣으면 그 의존성의 장애가 전 인스턴스 제외로 번진다. 다음 실험이 그 경우다.

### 실험 3: 깊은 헬스체크 연쇄 — 공유 DB가 6초 느려질 때

- **모형**이다. 실제 LB 대신 JDK 21로 짠 능동 헬스체크 LB(`HealthLb.java`)가 백엔드 3개 앞에 선다.
  - 검사: 0.5초마다, 타임아웃 1초, 연속 2회 실패면 제외, 연속 2회 성공이면 복귀(예시 값).
  - 트래픽: 초당 20건, 14초. 요청 `/work`는 DB를 쓰지 않는다.
  - `/health/shallow`는 프로세스만 확인한다. `/health/deep`은 공유 가짜 DB에 ping을 보내 300ms 안에 답이 없으면 503을 준다.
  - 3초에 DB 응답을 1000ms로 늦추고 9초에 되돌린다.
  - 건강한 대상이 없을 때 정책: `reject`(503 반환) 또는 `failopen`(전부에게 보냄).
- 환경: 실험 1과 같은 백엔드 컨테이너 안에서 실행.

```text
mode=deep policy=reject  (DB 지연 1000ms: 3s~9s)
  t= 3s healthy=[0, 1, 2] 200=20 503(대상없음)= 0
  t= 4s healthy=[0, 1, 2] 200=17 503(대상없음)= 3
  t= 5s healthy=[]        200= 0 503(대상없음)=20
  t= 6s healthy=[]        200= 0 503(대상없음)=20
  t= 7s healthy=[]        200= 0 503(대상없음)=20
  t= 8s healthy=[]        200= 0 503(대상없음)=20
  t= 9s healthy=[]        200=14 503(대상없음)= 6
  t=10s healthy=[0, 1, 2] 200=20 503(대상없음)= 0
mode=shallow policy=reject   t=0s~13s 전 구간 healthy=[0, 1, 2], 200=20/초, 503=0
mode=deep policy=failopen    t=5s~9s healthy=[] 이지만 200=20/초, 503=0
```

- 관찰: deep 모드에서는 DB가 느려지고 약 1~2초 뒤 세 인스턴스가 **동시에** 제외됐다. 그 뒤 4초 넘게 요청이 하나도 성공하지 못했다. 280건 중 89건이 503이었다(합계를 확인한 4회 모두 89건).
- 실패한 요청은 DB를 쓰지 않는 `/work`였다. 의존성 하나의 문제가 그 의존성과 무관한 요청까지 막았다.
- shallow 모드는 같은 DB 장애에서 503이 0건이었다. DB를 쓰는 요청의 실패는 앱의 타임아웃·서킷 브레이커가 다룰 몫이다([reliability/10](../../reliability/10-circuit-breaker/2-summary.md)).
- failopen 모드는 deep 검사가 전부 실패했지만 전부에게 보내서 503이 0건이었다.

실제 제품의 "전부 비정상" 처리(1차 문서):

- AWS ALB: 대상 그룹에 비정상 대상만 있으면 상태와 무관하게 전부에게 보낸다(**fail open**, 대상 그룹 헬스체크 문서).
- Envoy: 사용 가능한 호스트 비율이 *panic threshold*(기본 50%) 아래로 떨어지면 헬스 상태를 무시하고 전 호스트에 보내거나, 설정에 따라 아무 데도 보내지 않는다(Envoy 문서 "Panic threshold"). 장애가 부하를 타고 클러스터 전체로 번지는 것을 막으려는 장치라고 적는다.
- nginx 오픈소스: 그룹의 서버가 전부 unavailable이면 `no live upstreams` 오류와 함께 502로 끝난다([52번 §7](../52-network-symptom-index/2-summary.md)의 nginx 소스 근거).
- Kubernetes Service(ClusterIP·NodePort): 전 인스턴스가 unready면 연결 자체를 받지 않는다. 503 같은 HTTP 응답도 없다(Spring Boot Actuator 문서의 쿠버네티스 설명).

### 실험 4: nginx 수동 헬스체크와 재시도 — 죽은 백엔드가 502가 되나

- 실험 1의 구성에서 be2(9002)를 끈다(리스닝 소켓을 닫아 연결 거부). 세 가지 설정으로 순차 요청을 보낸다.

```nginx
upstream rr  { server be:9001; server be:9002; server be:9003; }      # max_fails=1 fail_timeout=10s (기본)
upstream rr0 { server be:9001 max_fails=0; server be:9002 max_fails=0; server be:9003 max_fails=0; }
server { listen 8081; location / { proxy_pass http://rr; } }                              # 재시도 기본(error timeout)
server { listen 8083; location / { proxy_pass http://rr;  proxy_next_upstream off; } }
server { listen 8084; location / { proxy_pass http://rr0; proxy_next_upstream off; } }
```

```text
== 8084 실패 집계 끔 + 재시도 끔 (0.2초 간격 9건)
#00 200 be1 / #01 502 / #02 200 be3 / #03 200 be1 / #04 502 / #05 200 be3 / #06 200 be1 / #07 502 / #08 200 be3
== 8081 기본 (1초 간격 14건): 14건 전부 200 (be1·be3만 응답)
== 8083 재시도 끔 (1초 간격 14건): #01 하나만 502, 나머지 13건 200

액세스 로그 (log_format: $remote_addr ... $status up=$upstream_addr up_status=$upstream_status rt=$request_time)
8081: "GET /work" 200 up=172.28.0.2:9002, 172.28.0.2:9003 up_status=502, 200 rt=0.022
8083: "GET /work" 502 up=172.28.0.2:9002 up_status=502 rt=0.000
에러 로그
[error] connect() failed (111: Connection refused) while connecting to upstream ... upstream: "http://172.28.0.2:9002/work"
[warn]  upstream server temporarily disabled while connecting to upstream ...
```

- 관찰 1 — 8084: 죽은 서버를 실패로 세지 않고(`max_fails=0`) 재시도도 끄면, 차례가 올 때마다 502다(9건 중 3건).
- 관찰 2 — 8081(기본): 사용자는 502를 보지 않았다. 첫 요청은 be2에서 연결 거부를 받고 be3로 재시도했다. 로그의 `up=…9002, …9003`과 `up_status=502, 200`이 한 요청 안의 두 시도다. 그 뒤 be2는 `temporarily disabled`로 빠졌다.
- 관찰 3 — 8083: 재시도를 꺼도 502는 한 건뿐이었다. 연결 거부는 `proxy_next_upstream`에 적지 않아도 실패로 세므로(`error`), be2가 그 한 번으로 제외됐기 때문이다.
- 관찰 4 — 복귀: `fail_timeout` 10초가 지나도 be2는 곧바로 다시 시도되지 않았다. 14초 실행 동안 두 번째 시도가 로그에 없었다.
  - nginx 1.27.5 소스(`src/http/ngx_http_upstream_round_robin.c`)는 실패한 서버의 `effective_weight`를 `weight / max_fails`만큼 깎고(최소 0), 고를 때마다 1씩 올린다. 제외가 풀린 뒤에도 차례가 늦게 오는 이유로 보인다(해석).
  - be2를 다시 켠 뒤에는 다음 차례부터 be1·be3·be2가 번갈아 응답했다.

### 7. 연결 드레이닝 — 빼는 서버의 진행 중 요청 끝내기

```text
  t0  "be1을 뺀다" (설정 변경·등록 해제·Pod 삭제)
      ├─ LB: be1에 새 요청을 보내지 않는다
      └─ LB: be1에서 처리 중인 요청·연결은 끝날 때까지 기다린다 (드레이닝)
  t1  처리 중 0  → 바로 완료      또는     드레이닝 한도 도달 → 남은 연결을 끊는다
  t2  be1 프로세스 종료 (이 순서가 뒤집히면 502)
```

- *연결 드레이닝(connection draining)*: 빠질 대상에 새 요청은 보내지 않고, 진행 중인 것만 마치게 하는 것이다. AWS는 *deregistration delay*라 부른다.
- 제품별:
  - AWS ALB: 등록 해제된 대상은 `draining` 상태가 되고, 기본 300초 기다린다. 진행 중 요청·연결이 없으면 바로 끝낸다. 대상이 그 전에 연결을 끊으면 클라이언트는 500대 오류를 받는다(대상 그룹 속성 문서).
  - nginx: `nginx -s reload` 때 새 설정으로 새 worker를 띄우고, 옛 worker는 처리 중인 요청을 마친 뒤 끝난다(아래 실험으로 확인).
  - Kubernetes: Pod을 지우면 EndpointSlice에서 그 엔드포인트의 ready 조건이 false가 되고, LB는 일반 트래픽에 그것을 쓰지 않는다(probe 문서). 앱 쪽의 SIGTERM·전파 대기·드레이닝 순서는 [reliability/14](../../reliability/14-graceful-shutdown/2-summary.md)에서 다룬다.

### 실험 5: nginx reload 드레이닝 vs 백엔드 즉시 종료

① 6초짜리 요청 2건이 be1·be2에서 처리 중일 때 설정에서 be1을 빼고 `nginx -s reload`:

```text
-- reload 직후 프로세스
    1 nginx: master process nginx -g daemon off;
   30 nginx: worker process is shutting down        ← 옛 worker: 처리 중 요청을 마저 처리
   61 nginx: worker process                         ← 새 worker: 새 설정
-- reload 직후 짧은 요청 6건
be2 be2 be2 be2 be2 be2
be1 long 6000ms done  -> HTTP 200 6.01s
be2 long 6000ms done  -> HTTP 200 6.01s
[notice] 30#30: gracefully shutting down       (14:08:01)
[notice] 30#30: exiting                         (14:08:06)
```

- 관찰: 새 요청은 be2로만 갔다. 빠진 be1에서 처리 중이던 6초 요청도 200으로 끝났다. 옛 worker는 그 요청이 끝난 뒤 사라졌다.

② 대신 백엔드가 처리 중 연결을 즉시 닫는 경우(JDK `HttpServer.stop(0)`, 4~6초 요청 처리 중 1.5초에 종료):

```text
단일 서버로 프록시(8090), GET  -> HTTP 502 1.49s
  [error] upstream prematurely closed connection while reading response header from upstream
라운드로빈 그룹(8081), GET      -> HTTP 200 5.64s
  up=172.28.0.2:9001, 172.28.0.2:9002 up_status=502, 200 rt=5.635
라운드로빈 그룹(8081), POST     -> HTTP 502 1.67s
  up=172.28.0.2:9003 up_status=502
```

- 관찰 1: 서버가 하나면 갈 곳이 없어 바로 502다.
- 관찰 2: 그룹이고 GET이면 nginx가 다른 서버로 재시도해 200이 됐다. 대신 걸린 시간이 5.6초다. 앞 서버에서 1.5초 일한 것을 버리고 처음부터 다시 했다.
- 관찰 3: POST는 재시도하지 않고 502였다. nginx는 요청을 이미 상류로 보낸 뒤에는 POST·LOCK·PATCH 같은 비멱등 요청을 다음 서버로 넘기지 않는다(`non_idempotent`를 켜야 넘김, proxy 모듈 문서, 1.9.13부터). 멱등은 [reliability/13](../../reliability/13-idempotency/2-summary.md).
- 재시도는 클라이언트에 아무것도 보내기 전에만 가능하다. 응답을 보내는 도중 끊기면 고칠 수 없다(proxy 모듈 문서).

### 8. X-Forwarded-For와 신뢰 경계

```text
  클라이언트 C ──> 프록시 P1 ──> 프록시 P2 ──> 서버
  (C가 아무 값이나 넣을 수 있다)

  C가 보냄:     X-Forwarded-For: 203.0.113.9              ← 위조. C가 마음대로 쓴 값
  P1이 덧붙임:   X-Forwarded-For: 203.0.113.9, C
  P2가 덧붙임:   X-Forwarded-For: 203.0.113.9, C, P1
  서버의 소켓 상대 = P2

  오른쪽 끝부터 읽는다:  P1(우리 프록시, 신뢰) → C(신뢰 아님) ← 여기서 멈춘다 = 클라이언트
  왼쪽 끝(203.0.113.9)은 누구도 검증하지 않은 값이다
```

- *X-Forwarded-For(XFF)*: 프록시가 자기가 본 상대 주소를 덧붙여 가는 요청 헤더다. 가장 왼쪽이 원래 클라이언트, 가장 오른쪽이 가장 최근 프록시다. 단 클라이언트·프록시가 정직할 때만 그렇다(MDN).
- *Forwarded*: 같은 목적을 표준화한 헤더(RFC 7239). `Forwarded: for=192.0.2.43, for=198.51.100.17;by=203.0.113.60;proto=http;host=example.com`처럼 쓴다(§7.5).
- *신뢰 경계*: 이 선 안쪽에서 들어온 값만 믿는다는 경계다. 위협 모델링의 개념은 [security/02](../../security/02-threat-modeling/2-summary.md).
- RFC 7239 §8.1: 이 헤더는 요청을 보낸 클라이언트를 포함해 경로의 어느 노드든 고칠 수 있어 정확하다고 믿을 수 없다. 신뢰하는 프록시 목록을 두는 방법도 그 프록시 앞에서 들어온 주소들은 믿을 수 없다고 적는다.
- MDN: 보안 용도(레이트 리밋, IP 접근 제어)에는 **신뢰하는 프록시가 덧붙인 주소만** 쓰라고 적는다. 서버에 인터넷에서 직접 닿을 수 있으면 XFF 목록의 어느 값도 믿을 수 없다. 헤더가 여러 개 오면 하나의 목록으로 합쳐 읽으라고도 적는다.
- 제품별 처리:
  - nginx `realip` 모듈: `set_real_ip_from`(신뢰 주소)에서 온 연결만 헤더로 클라이언트 주소를 바꾼다. `real_ip_recursive off`(기본)면 헤더의 마지막 주소로, `on`이면 신뢰 주소가 아닌 마지막 주소로 바꾼다(realip 문서).
  - nginx `$proxy_add_x_forwarded_for`: 받은 XFF 뒤에 `$remote_addr`를 붙인 값이다(proxy 모듈 문서). 가장 바깥 프록시에서 이것을 쓰면 클라이언트가 보낸 값이 그대로 앞에 남는다.
  - Envoy: `use_remote_address`가 false(기본)면 XFF를 고치지 않는 투명 모드다. 신뢰할 클라이언트 주소는 `xff_num_trusted_hops`로 오른쪽에서 몇 번째를 믿을지 정한다(Envoy 문서 "HTTP header manipulation").
  - AWS ALB: `routing.http.xff_header_processing.mode` 기본값이 `append`(클라이언트 IP를 덧붙임)다. `preserve`·`remove`도 있다(ALB X-Forwarded 헤더 문서).

### 실험 6: XFF — 신뢰 경계를 둔 구성과 안 둔 구성

- 모두 로컬 도커 내부 네트워크 안의 자기 nginx·백엔드다. 위조 값은 문서 예시용 주소 203.0.113.9다. 클라이언트 실제 주소는 172.28.0.2다.
- 백엔드 `/whoami`는 XFF 맨 왼쪽을 그대로 믿는 "순진한" 코드다(`naive_leftmost`).

```nginx
server { listen 8090; location / { proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for; proxy_pass http://be:9001; } }  # 덧붙이기
server { listen 8091; location / { proxy_set_header X-Forwarded-For $remote_addr;              proxy_pass http://be:9001; } }  # 덮어쓰기
# 안쪽 프록시(I): 127.0.0.1에서 온 연결만 신뢰
server { listen 8095; set_real_ip_from 127.0.0.1; real_ip_header X-Forwarded-For; real_ip_recursive on;  ... }   # I_on
server { listen 8097; set_real_ip_from 127.0.0.1; real_ip_header X-Forwarded-For; real_ip_recursive off; ... }   # I_off
server { listen 8099; set_real_ip_from 0.0.0.0/0; real_ip_header X-Forwarded-For; real_ip_recursive on;  ... }   # I_all (전부 신뢰)
# 8092 -> 8093 -> 8095(I_on), 8094 -> 8096 -> 8097(I_off): 프록시 2단, 8098 -> 8099(I_all): 1단
```

```text
== 8090 위조 XFF   be1 socket_peer=172.28.0.3 xff=[203.0.113.9, 172.28.0.2] naive_leftmost=203.0.113.9
== 8091 위조 XFF   be1 socket_peer=172.28.0.3 xff=[172.28.0.2]              naive_leftmost=172.28.0.2
== 8092 위조       I_on  remote_addr=172.28.0.2 realip_remote_addr=127.0.0.1 xff=203.0.113.9, 172.28.0.2, 127.0.0.1
== 8094 위조       I_off remote_addr=127.0.0.1  realip_remote_addr=127.0.0.1 xff=203.0.113.9, 172.28.0.2, 127.0.0.1
== 8098 위조       I_all remote_addr=203.0.113.9 realip_remote_addr=127.0.0.1 xff=203.0.113.9, 172.28.0.2
(위조 헤더 없이 보내면 8090·8091 모두 naive_leftmost=172.28.0.2, I_on·I_all은 172.28.0.2, I_off는 127.0.0.1)
```

- 관찰 1 — 8090: 가장 바깥 프록시가 덧붙이기만 하면, 왼쪽을 믿는 백엔드는 위조 주소 203.0.113.9를 클라이언트로 기록한다.
- 관찰 2 — 8091: 가장 바깥 프록시가 XFF를 자기가 본 주소로 덮어쓰면 위조 값이 사라진다.
- 관찰 3 — I_on: 신뢰 주소(127.0.0.1)만 오른쪽에서 건너뛰고 처음 만난 비신뢰 주소 172.28.0.2를 골랐다. 정답이다.
- 관찰 4 — I_off: 프록시가 2단이라 헤더 마지막 값이 중간 프록시(127.0.0.1)였다. recursive를 끄면 그 값을 클라이언트로 쓴다.
- 관찰 5 — I_all: 0.0.0.0/0을 신뢰하면 nginx는 맨 왼쪽 위조 값까지 걸어가 203.0.113.9를 클라이언트로 삼았다. 신뢰 범위를 넓게 잡는 것은 헤더를 그냥 믿는 것과 같다.
- `$realip_remote_addr`에는 바꾸기 전의 원래 소켓 주소가 남는다(realip 문서). 진단 로그에 같이 찍어 두면 무엇이 바뀌었는지 보인다.

### 9. 스티키 세션 — 같은 사용자를 같은 서버로

```text
  쿠키 방식:   첫 응답에 "srv=be2" 쿠키 → 이후 요청은 쿠키를 보고 be2로
  IP 해시:     hash(클라이언트 IP) → 고정 서버
               nginx ip_hash는 IPv4의 앞 세 옥텟(/24)만 키로 쓴다

  회사 NAT 뒤 사용자 300명 → 공인 IP 하나 → 전부 같은 서버
```

- *스티키 세션(session affinity)*: 한 클라이언트의 요청을 같은 백엔드로 계속 보내는 것이다. 쓰는 이유와 문제(서버가 죽으면 세션 유실, 오토스케일과 상성 나쁨)는 원고 §5 표.
- *NAT*: 여러 내부 주소를 공인 주소 하나로 바꿔 내보내는 것([11번](../11-nat-and-conntrack/2-summary.md)). LB에는 NAT 뒤 많은 사용자가 IP 하나로 보인다.
- 제품별:
  - nginx `ip_hash`: IPv4 주소의 앞 세 옥텟 또는 IPv6 주소 전체를 키로 쓴다. 서버를 잠시 빼야 하면 해시를 유지하도록 `down`으로 표시하라고 적는다(upstream 문서).
  - nginx `sticky cookie`: 1.29.6 전에는 상용판 전용이었다(upstream 문서). 이 실험의 1.27.5 오픈소스에는 없다.
  - AWS ALB: 기간 기반(LB가 만드는 `AWSALB` 쿠키)과 애플리케이션 기반 쿠키를 지원한다. 처음 대상은 라우팅 알고리즘으로 고르고, 그 뒤 같은 클라이언트는 알고리즘을 건너뛰고 같은 대상으로 간다. 대상이 비정상이 되면 새 대상을 고르고 쿠키를 갱신한다(대상 그룹 속성 문서).
- 쿠키 보안 속성은 [security/11](../../security/11-sessions-and-cookie-security/2-summary.md).

### 실험 7: 해시 고정의 쏠림 — `ip_hash` vs `hash $remote_addr consistent`

- nginx 앞단이 넣었다고 가정한 합성 클라이언트 주소를 `X-Forwarded-For`로 보낸다. nginx는 `set_real_ip_from 172.28.0.0/16`(이 도커 네트워크를 앞단 LB로 신뢰)으로 그 주소를 `$remote_addr`로 복원한 뒤 해시한다. 액세스 로그의 `$remote_addr`가 합성 주소로 바뀐 것을 확인했다.
- 시나리오(각 300건):
  - `spread`: 서로 다른 /24 대역의 300개 주소.
  - `same24`: 한 /24(198.51.100.0/24) 안의 서로 다른 주소 250개(198.51.100.1~250)에서 300건(50개 주소는 두 번). 통신사·회사 주소 풀을 흉내.
  - `bignat`: 180건(60%)은 NAT 공인 주소 하나(192.0.2.10), 120건은 서로 다른 주소.

```text
:8085(ip_hash)                      spread  -> {be1=101, be2=99, be3=100}
:8086(hash $remote_addr consistent) spread  -> {be1=108, be2=96, be3=96}
:8085(ip_hash)                      same24  -> {be1=300}
:8086(hash $remote_addr consistent) same24  -> {be1=103, be2=98, be3=99}
:8085(ip_hash)                      bignat  -> {be1=220, be2=40, be3=40}
:8086(hash $remote_addr consistent) bignat  -> {be1=43, be2=48, be3=209}
```

- 같은 입력으로 다시 돌려도 같은 결과였다(해시라 결정적이다. 점검 재실행 2회도 여섯 줄 모두 같았다).
- 관찰 1 — `same24`: 주소가 모두 달라도 앞 세 옥텟이 같아 `ip_hash`는 300건 전부를 be1로 보냈다. 전체 주소를 해시한 `hash $remote_addr consistent`는 고르게 나눴다.
- 관찰 2 — `bignat`: 어느 방식이든 NAT 주소 하나의 180건은 한 서버로 갔다. 그 서버가 전체의 70%쯤(209~220건)을 받았다. 키 하나가 무거우면 해시 방식을 바꿔도 쏠림이 남는다.
- 대처는 장애 시나리오 3에 있다.

## 쓰이는 자료구조·알고리즘

- **가중 라운드로빈(smooth weighted round-robin)** — nginx 1.27.5 소스는 고를 때마다 각 서버의 `current_weight`에 `effective_weight`를 더하고, 가장 큰 서버를 고른 뒤 그 서버의 `current_weight`에서 이번에 더한 가중치의 합을 뺀다(`ngx_http_upstream_round_robin.c`). 가중치 5:1:1이면 7번 중 5·1·1번 고른다(upstream 문서의 예).
- **최소 연결(least connections)** — 백엔드별 처리 중 카운터. 같은 값이 여럿이면 nginx는 그 안에서 가중 라운드로빈으로 고른다(upstream 문서).
- **P2C(두 개 중 하나)** — 무작위 둘을 뽑아 덜 바쁜 쪽. O(1)로 최소 연결에 가깝다(Envoy·HAProxy 문서). 무작위 알고리즘 일반은 [algorithm/39](../../algorithm/39-randomized-algorithms/2-summary.md).
- **해시 함수** — 키를 백엔드로 보내는 첫 단계. [algorithm/12](../../algorithm/12-hash-functions/2-summary.md).
- **해시 링(일관 해싱)** — 정렬된 맵에서 "키 이상인 첫 노드"를 찾는다(`TreeMap.ceilingEntry`). [data-structure/31](../../data-structure/31-consistent-hashing/2-summary.md).
- **Maglev 조회 테이블** — 크기 M(소수) 배열 + 백엔드별 순열 (offset + j·skip) mod M. 조회는 배열 한 번 읽기다. 생성은 평균 O(M log M), 최악 O(M²)이다(논문 §3.4). 서로소 조건은 [algorithm/28](../../algorithm/28-number-theory/2-summary.md).
- **연결 추적 표** — 5-tuple 해시 → 백엔드. 해시맵이다. [data-structure/05](../../data-structure/05-hashmap/2-summary.md), conntrack은 [11번](../11-nat-and-conntrack/2-summary.md).
- **헬스 상태 기계 + 연속 횟수 카운터** — 히스테리시스. [reliability/33](../../reliability/33-hysteresis-and-flapping/2-summary.md).

## 적용 — 풀어나가는 법

### 1. 증상에서 LB·프록시 원인으로

| 증상 | 먼저 의심할 LB·프록시 원인 | 확인 |
|---|---|---|
| 502 + `connect() failed (111: Connection refused)` | 백엔드 다운·포트 틀림, 헬스체크 제외 전 | 에러 로그의 `upstream:` 주소, 그 서버의 `ss -ltn` |
| 502 + `upstream prematurely closed connection` | 백엔드가 처리 중 연결을 닫음(배포·크래시·idle 경합) | 같은 시각의 배포 기록, 35번 idle timeout 표 |
| 502 + `no live upstreams` | 그룹의 서버가 전부 unavailable | `max_fails`·`fail_timeout`, 직전 에러 로그 |
| 503이 전 인스턴스에서 동시에 | 깊은 헬스체크가 공유 의존성 때문에 전부 실패(실험 3) | 헬스 엔드포인트가 무엇을 검사하나, LB 대상 상태 이력 |
| 인스턴스별 요청 수·CPU 불균형 | 스티키·해시 키 쏠림(실험 7), 느린 인스턴스에 RR(실험 1), 연결 단위 분산(L4) | 액세스 로그 `$upstream_addr` 집계, 키별 요청 수 |
| 로그·차단 목록의 클라이언트 IP가 이상함 | XFF를 왼쪽부터 믿음, 신뢰 범위가 넓음(실험 6) | `$remote_addr`·`$realip_remote_addr`·`$http_x_forwarded_for`를 나란히 |
| 배포 때마다 502가 몇 초 | 드레이닝 없이 종료, LB 반영 전 종료 | 배포 시각과 502 시각, 대상 상태(draining) |

### 2. 프록시 로그에 무엇을 남기나

```nginx
log_format lb '$remote_addr realip_from=$realip_remote_addr xff="$http_x_forwarded_for" '
              '"$request" $status up=$upstream_addr up_status=$upstream_status rt=$request_time';
```

- `$upstream_addr`·`$upstream_status`에는 시도한 서버가 쉼표로 다 나온다. `up=…9002, …9003 up_status=502, 200`은 "9002에서 실패하고 9003으로 재시도해 성공"이다(실험 4).
- `$status`(클라이언트에 준 코드)와 `$upstream_status`(백엔드에게 받은 코드)를 같이 봐야 누가 만든 5xx인지 안다.
- `$realip_remote_addr`는 realip로 바꾸기 전 소켓 주소다. `$remote_addr`와 다르면 헤더로 바뀐 것이다.

### 3. 명령으로 확인

```bash
# 응답이 어느 백엔드에서 왔나, 프록시가 만든 응답인가 (502 본문의 nginx 서명 등)
curl -sv http://lb.example.internal/health 2>&1 | grep -E '^< (HTTP|Server|Via)'

# 프록시 안의 연결 둘: 클라이언트 쪽(리스닝 포트)과 백엔드 쪽(상류 포트)
ss -tan state established '( sport = :443 or dport = :8080 )'

# 액세스 로그에서 백엔드별 요청 수 (불균형 확인)
awk -F'up=' '{split($2,a," "); print a[1]}' access.log | sort | uniq -c | sort -rn
```

- 알파인 기반 nginx 이미지에는 `ss`가 없어 실험에서는 `netstat -tn`을 썼다(§3 출력).

### 4. 설정 — nginx 오픈소스 기준

```nginx
upstream app {
    least_conn;                                   # 요청 비용이 제각각이고 동시 요청이 많을 때
    server 10.0.0.11:8080 max_fails=3 fail_timeout=10s;
    server 10.0.0.12:8080 max_fails=3 fail_timeout=10s;
}
server {
    # 앞단이 신뢰하는 LB(예: 10.0.0.0/24)일 때만 그 헤더로 클라이언트 주소를 복원
    set_real_ip_from 10.0.0.0/24;
    real_ip_header   X-Forwarded-For;
    real_ip_recursive on;

    location / {
        proxy_pass http://app;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;   # 안쪽 프록시면 덧붙이기
        # 가장 바깥 프록시라면: proxy_set_header X-Forwarded-For $remote_addr;
        proxy_next_upstream error timeout;        # 기본값. POST는 상류에 보낸 뒤엔 재시도 안 함
        proxy_next_upstream_tries 2;              # 재시도 횟수 상한 (기본 0 = 무제한)
    }
}
```

- `max_fails=3`은 예시다. 기본은 1회 실패로 10초 제외다.
- 능동 헬스체크(`health_check`)와 `slow_start`는 nginx Plus 기능이다. 오픈소스에서 능동 검사가 필요하면 앞단 LB(ALB·HAProxy·Envoy)나 오케스트레이터(쿠버네티스 readiness)에 맡긴다.

### 5. 앱 — 헬스 엔드포인트와 클라이언트 IP (Java 21, JDK `HttpServer`)

```java
// 얕은 liveness: 프로세스가 요청을 처리할 수 있나만 본다
server.createContext("/health/live", ex -> reply(ex, 200, "up"));

// readiness: 이 인스턴스만의 상태(종료 중인가, 워밍업 끝났나)를 본다.
// 전 인스턴스가 공유하는 DB 상태는 넣지 않는다 — 공유 의존성 장애가 전 인스턴스 제외로 번진다(실험 3)
server.createContext("/health/ready", ex -> reply(ex, ready.get() && !shuttingDown.get() ? 200 : 503, ""));

// 클라이언트 IP: 소켓 상대가 신뢰 프록시일 때만 XFF를 오른쪽부터 읽는다 (nginx real_ip_recursive on과 같은 규칙)
static String clientIp(String socketPeer, List<String> xffHeaders, Predicate<String> trusted) {
    if (!trusted.test(socketPeer)) return socketPeer;           // 프록시를 거치지 않은 연결은 헤더를 무시
    List<String> chain = xffHeaders.stream()                    // 헤더가 여러 개면 하나의 목록으로 합친다 (MDN)
            .flatMap(h -> Arrays.stream(h.split(","))).map(String::trim).filter(s -> !s.isEmpty()).toList();
    for (int i = chain.size() - 1; i >= 0; i--) {
        if (!trusted.test(chain.get(i))) return chain.get(i);   // 처음 만나는 비신뢰 주소 = 클라이언트
    }
    return chain.isEmpty() ? socketPeer : chain.get(0);         // 전부 신뢰 주소면 맨 왼쪽(nginx와 같음)
}
// 요청에서: clientIp(ex.getRemoteAddress().getAddress().getHostAddress(),
//                   ex.getRequestHeaders().getOrDefault("X-Forwarded-For", List.of()), Net::isOurProxy)
```

- `trusted`(예: `Net::isOurProxy`, 주소가 우리 프록시 CIDR 안인지 검사하는 함수)에는 우리가 운영하는 프록시 대역만 넣는다. 실험 6의 I_all처럼 넓게 잡으면 위조 값이 통과한다.
- Spring Boot라면 Actuator의 liveness·readiness 그룹을 쓴다. 기본으로 외부 검사를 넣지 않는다. 넣으려면 `management.endpoint.health.group.readiness.include=readinessState,customCheck`처럼 명시한다(Actuator 문서).

## 장애 시나리오와 대처

### 1. 깊은 헬스체크 — 의존성 장애가 전 인스턴스 제외로 번진다 (⚠ 커리큘럼)

- **현상**: 공유 DB·캐시가 몇 초 느려졌을 뿐인데 서비스 전체가 응답하지 않는다. DB를 쓰지 않는 API까지 실패한다.
- **보이는 형태**
  - LB 대상 상태가 같은 시각에 전부 unhealthy로 바뀐다.
  - 503(LB가 대상 없음으로 응답), nginx면 `no live upstreams` 502, 쿠버네티스 ClusterIP면 연결 거부.
  - 앱 로그에는 오류가 거의 없다. 요청이 앱까지 오지 않기 때문이다.
  - 실험 3에서 DB 6초 지연 동안 280건 중 89건이 503이었다. 실패한 요청은 DB를 쓰지 않는 `/work`였다.
- **원인**: 헬스 엔드포인트가 공유 의존성까지 검사한다. 의존성 하나의 문제를 LB가 "인스턴스 전부가 고장"으로 읽는다.
- **대처**
  - liveness는 프로세스 자신만 본다. 외부 시스템을 넣지 않는다(Spring Boot Actuator 문서).
  - readiness에는 인스턴스별 상태만 넣는다(이 노트의 선택 — 공유 의존성을 넣을지는 Spring 문서도 판단의 문제로 둔다). 공유 의존성 장애는 서킷 브레이커·폴백으로 다룬다([reliability/10](../../reliability/10-circuit-breaker/2-summary.md)).
  - LB의 전부-비정상 동작을 안다. ALB는 fail open, Envoy는 panic threshold(기본 50%)로 전부에게 보낸다. nginx 오픈소스는 502다.

### 2. `X-Forwarded-For` 스푸핑 — IP 기반 제한이 뚫린다 (⚠ 커리큘럼)

- **현상**: IP별 레이트 리밋이 듣지 않는다. 관리자 경로의 IP 허용 목록이 외부 요청을 통과시킨다. 감사 로그의 클라이언트 IP가 엉뚱하다.
- **보이는 형태**
  - 액세스 로그의 `$http_x_forwarded_for` 맨 왼쪽 값이 요청마다 바뀌는데, 소켓 상대(`$realip_remote_addr`)는 같다.
  - 앱이 기록한 클라이언트 IP가 문서용·사설 대역이거나 허용 목록 값과 같다.
  - 실험 6의 8090: 백엔드가 위조 값 203.0.113.9를 클라이언트로 기록했다.
- **원인**
  - 앱이 XFF 맨 왼쪽을 믿는다.
  - 가장 바깥 프록시가 클라이언트가 보낸 XFF를 지우지 않고 덧붙인다.
  - `set_real_ip_from` 같은 신뢰 범위가 너무 넓다(실험 6의 I_all).
  - 백엔드에 프록시를 거치지 않고 직접 닿는 경로가 있다(MDN: 이 경우 XFF의 어느 값도 믿을 수 없다).
- **대처**
  - 가장 바깥 프록시에서 XFF를 자기가 본 주소로 덮어쓰거나, 안쪽에서 신뢰 프록시만 건너뛰고 오른쪽부터 읽는다(nginx `real_ip_recursive on`, Envoy `xff_num_trusted_hops`).
  - 신뢰 목록에는 우리가 운영하는 프록시 대역만 넣는다.
  - 백엔드는 프록시에서 오는 연결만 받게 네트워크로 막는다([48번](../48-firewalls-and-network-policy/2-summary.md)).
  - 레이트 리밋 설계는 [reliability/11](../../reliability/11-rate-limiter/2-summary.md), 남용 방어는 [security/28](../../security/28-dos-and-abuse/2-summary.md).

### 3. 스티키 세션 불균형 — 한 서버만 뜨겁다 (⚠ 커리큘럼)

- **현상**: 인스턴스를 늘려도 특정 인스턴스의 CPU·메모리만 높다. 그 인스턴스가 죽으면 많은 사용자가 한꺼번에 로그아웃된다.
- **보이는 형태**
  - `$upstream_addr` 집계에서 한 서버의 몫이 1/N보다 훨씬 크다. 실험 7 `bignat`에서 한 서버가 300건 중 209~220건을 받았다.
  - 그 서버로 가는 요청의 클라이언트 IP(또는 쿠키 값)가 소수에 몰려 있다.
- **원인**
  - IP 기반 고정에서 NAT·프록시 뒤 많은 사용자가 주소 하나로 보인다.
  - nginx `ip_hash`는 /24 단위라 같은 대역의 다른 주소도 한 서버로 간다(실험 7 `same24`: 300건 전부 be1).
  - 쿠키 고정은 세션이 길게 이어져, 새로 늘린 서버에 기존 사용자가 옮겨 가지 않는다.
- **대처**
  - 세션 상태를 서버 밖(공유 저장소)이나 토큰으로 옮겨 고정을 없앤다(원고 §5).
  - 고정이 꼭 필요하면 IP보다 사용자 단위 쿠키로 고정하고, 쿠키 수명을 짧게 둔다.
  - IP 해시를 써야 하면 /24 단위인 `ip_hash` 대신 전체 주소를 쓰는 `hash $remote_addr consistent`를 검토한다. 단 NAT 주소 하나의 무게는 남는다.

### 4. 배포·축소 때 502가 몇 초씩 튄다 — 드레이닝 누락

- **현상**: 배포나 스케일 인 때마다 짧게 오류율이 오른다.
- **보이는 형태**
  - nginx: `upstream prematurely closed connection` 또는 `connect() failed (111: Connection refused)`와 502. 실험 5에서 단일 서버 프록시는 1.49초 만에 502였다.
  - ALB: 등록 해제 지연이 끝나기 전에 대상이 연결을 끊으면 클라이언트는 500대 오류를 받는다(대상 그룹 속성 문서).
  - 재시도가 켜진 GET은 성공하지만 지연이 늘어난다(실험 5: 4초 요청이 5.6초). POST는 502다.
- **원인**: LB가 대상을 빼기 전에, 또는 진행 중 요청이 끝나기 전에 프로세스가 연결을 닫는다.
- **대처**
  - 순서를 지킨다: LB에서 빼기(등록 해제·readiness false) → 반영 대기 → 진행 중 요청 마치기 → 종료. 앱 쪽 구현은 [reliability/14](../../reliability/14-graceful-shutdown/2-summary.md).
  - LB의 드레이닝 시간(ALB deregistration delay 기본 300초)을 가장 긴 정상 요청보다 길게, 배포 속도와 맞게 정한다.
  - nginx 설정 변경은 `nginx -s reload`로 한다. 옛 worker가 진행 중 요청을 마친다(실험 5 ①).

### 5. 느려진 인스턴스 하나가 꼬리 지연을 끌어올린다

- **현상**: 오류는 없는데 p95·p99 지연만 오른다. 인스턴스 하나의 응답 시간만 높다.
- **보이는 형태**
  - 실험 1: be1만 300ms 느릴 때 라운드로빈은 be1에도 1/3을 보내 전체 시간이 6.9초였다. least_conn은 be1 몫을 5~6%로 줄여 3.1~3.5초였다.
  - 수동 헬스체크는 아무것도 잡지 않는다. 실패가 아니라 느림이기 때문이다.
- **원인**: 처리 중 개수·지연을 보지 않는 분배(라운드로빈)가 느린 인스턴스에도 같은 몫을 준다.
- **대처**
  - 동시 요청이 많은 서비스는 least_conn·P2C·지연 기반 분배를 쓴다(nginx `least_conn`·`random two least_conn`, ALB least outstanding requests, Envoy least request).
  - 느림을 이상치로 빼는 장치를 둔다(Envoy outlier detection 등). 꼬리 지연 일반은 [reliability/34](../../reliability/34-tail-latency-and-stragglers/2-summary.md).
  - 새 인스턴스 쏠림이 걱정되면 슬로우 스타트를 같이 둔다(제품마다 지원 조합이 다르다, §4).

## 핵심 문장

- L4 LB는 연결 단위로, L7 LB는 요청 단위로 백엔드를 고른다. L7 프록시에는 클라이언트 쪽과 백엔드 쪽, 연결이 둘이다.
- 기본 분배는 nginx·ALB·HAProxy·Envoy 모두 라운드로빈이다. 느린 인스턴스가 섞이고 동시 요청이 많으면 least_conn·P2C가 그 인스턴스의 몫을 줄인다.
- 해시 링 같은 일관 해싱은 백엔드 1대가 빠질 때 키의 약 1/N만 옮긴다(모형 N=100에서 0.89~1.12%). Maglev는 링보다 조금 더(모형 1.58~1.60%) 옮기는 대신 백엔드별 몫을 거의 같게 만든다.
- 헬스체크가 전 인스턴스가 공유하는 의존성을 검사하면, 그 의존성의 장애가 전 인스턴스 제외로 번진다. 이 노트는 liveness는 프로세스만, readiness는 인스턴스별 상태만 보게 하는 쪽을 택한다(Kubernetes·Spring 문서는 필수 의존성을 readiness에 넣는 길도 열어 둔다).
- `X-Forwarded-For`의 왼쪽 값은 클라이언트가 마음대로 쓸 수 있다. 신뢰하는 프록시가 덧붙인 주소만, 오른쪽부터 읽는다.
- 대상을 뺄 때는 새 요청을 끊고 진행 중 요청을 마치게 한 뒤(드레이닝) 프로세스를 끈다. 순서가 뒤집히면 502다.

## 관련 주제·근거

- 선행
  - [35-http-connection-management](../35-http-connection-management/2-summary.md) — 구간별 idle timeout, 연결 단위 vs 요청 단위 분산
  - [11-nat-and-conntrack](../11-nat-and-conntrack/2-summary.md) — 연결 추적 표, NAT 뒤 주소 하나
- 함께 보기(network)
  - [15-tcp-handshake-and-backlog](../15-tcp-handshake-and-backlog/2-summary.md) · [19-tcp-termination-fin-rst-half-open](../19-tcp-termination-fin-rst-half-open/2-summary.md) · [21-tcp-keepalive-and-user-timeout](../21-tcp-keepalive-and-user-timeout/2-summary.md)
  - [29-tls-handshake](../29-tls-handshake/2-summary.md) · [32-mtls-and-cert-operations](../32-mtls-and-cert-operations/2-summary.md) — LB의 TLS 종료와 백엔드 구간 mTLS
  - [33-http-semantics](../33-http-semantics/2-summary.md) · [36-http2-multiplexing](../36-http2-multiplexing/2-summary.md) · [38-websocket-sse-long-lived](../38-websocket-sse-long-lived/2-summary.md) — 오래 사는 연결과 LB
  - [47-cdn-and-edge](../47-cdn-and-edge/2-summary.md) · [48-firewalls-and-network-policy](../48-firewalls-and-network-policy/2-summary.md) · [49-what-happens-when-url](../49-what-happens-when-url/2-summary.md) · [52-network-symptom-index](../52-network-symptom-index/2-summary.md)
- 다른 영역
  - 원고 [systems/server-design/02-request-path](../../systems/server-design/02-request-path.md) §3 로드밸런서, §5 세션 처리
  - [api-design/19-api-gateway-and-bff](../../api-design/19-api-gateway-and-bff/2-summary.md) — 게이트웨이(원고 §4)
  - [reliability/14-graceful-shutdown](../../reliability/14-graceful-shutdown/2-summary.md) — 앱 쪽 드레이닝 · [reliability/10-circuit-breaker](../../reliability/10-circuit-breaker/2-summary.md) · [reliability/13-idempotency](../../reliability/13-idempotency/2-summary.md) · [reliability/50-sidecar-ambassador-and-service-mesh](../../reliability/50-sidecar-ambassador-and-service-mesh/2-summary.md)
  - [data-structure/31-consistent-hashing](../../data-structure/31-consistent-hashing/2-summary.md) · [algorithm/12-hash-functions](../../algorithm/12-hash-functions/2-summary.md)
  - [security/02-threat-modeling](../../security/02-threat-modeling/2-summary.md) · [security/11-sessions-and-cookie-security](../../security/11-sessions-and-cookie-security/2-summary.md)
- 논문·명세
  - Eisenbud 외, "Maglev: A Fast and Reliable Software Network Load Balancer", NSDI 2016 — §3.4 Consistent Hashing(Pseudocode 1, Table 1, M 소수·M > 100×N), §5.3 평가(테이블 65537·655373, 생성 시간) <https://www.usenix.org/system/files/conference/nsdi16/nsdi16-paper-eisenbud.pdf>
  - RFC 7239 Forwarded HTTP Extension — §5.2 for, §7.4 X-Forwarded-For 변환, §7.5 예시, §8.1 헤더의 유효성과 무결성 <https://www.rfc-editor.org/rfc/rfc7239.txt>
  - Karger 외, "Consistent hashing and random trees", STOC 1997 — 서지는 Maglev 논문 참고문헌 [28]로 확인했고 원문은 열지 못했다. Mitzenmacher "power of two choices" `[?]` — HAProxy 문서가 <http://www.eecs.harvard.edu/~michaelm/postscripts/handbook2001.pdf>를 가리키지만 원문을 열지 못했다. Envoy·HAProxy 문서의 인용으로 대신한다.
- 제품 문서
  - nginx upstream 모듈(가중 라운드로빈 기본, `max_fails`·`fail_timeout`·`slow_start`(상용), `hash … consistent`(ketama), `ip_hash`(앞 세 옥텟), `least_conn`, `random two`, `sticky`(1.29.6 전 상용)) <https://nginx.org/en/docs/http/ngx_http_upstream_module.html>
  - nginx realip 모듈(`set_real_ip_from`·`real_ip_header`·`real_ip_recursive`·`$realip_remote_addr`) <https://nginx.org/en/docs/http/ngx_http_realip_module.html>
  - nginx proxy 모듈(`proxy_next_upstream`·`non_idempotent`·`_tries`, `$proxy_add_x_forwarded_for`) <https://nginx.org/en/docs/http/ngx_http_proxy_module.html>
  - nginx 1.27.5 소스 `src/http/ngx_http_upstream_round_robin.c`(`effective_weight`·`current_weight`) <https://github.com/nginx/nginx/blob/release-1.27.5/src/http/ngx_http_upstream_round_robin.c>
  - HAProxy 3.0.29 설정 문서(`balance`, `inter`·`fall`·`rise`, `slowstart`) <https://docs.haproxy.org/3.0/configuration.html>
  - Envoy 문서(1.40-dev): Supported load balancers(least request P2C, ring hash, Maglev 65537) <https://www.envoyproxy.io/docs/envoy/latest/intro/arch_overview/upstream/load_balancing/load_balancers> · Cluster API(`lb_policy` 기본 `ROUND_ROBIN`, Maglev `table_size`) <https://www.envoyproxy.io/docs/envoy/latest/api-v3/config/cluster/v3/cluster.proto> · Panic threshold <https://www.envoyproxy.io/docs/envoy/latest/intro/arch_overview/upstream/load_balancing/panic_threshold> · Outlier detection <https://www.envoyproxy.io/docs/envoy/latest/intro/arch_overview/upstream/outlier> · HTTP header manipulation(XFF, `use_remote_address`, `xff_num_trusted_hops`) <https://www.envoyproxy.io/docs/envoy/latest/configuration/http/http_conn_man/headers>
  - AWS ALB 대상 그룹 헬스체크(기본값, fail open) <https://docs.aws.amazon.com/elasticloadbalancing/latest/application/target-group-health-checks.html> · 대상 그룹 속성(deregistration delay 300초, 라우팅 알고리즘, slow start, sticky sessions) <https://docs.aws.amazon.com/elasticloadbalancing/latest/application/edit-target-group-attributes.html> · X-Forwarded 헤더(`xff_header_processing.mode`) <https://docs.aws.amazon.com/elasticloadbalancing/latest/application/x-forwarded-headers.html>
  - Kubernetes "Liveness, Readiness, and Startup Probes"(기본값, readiness 실패 시 EndpointSlice 제외, 뒤쪽 서비스 확인) <https://kubernetes.io/docs/concepts/configuration/liveness-readiness-startup-probes/>
  - Spring Boot Actuator "Endpoints"(헬스 그룹, 쿠버네티스 probe와 외부 상태) <https://docs.spring.io/spring-boot/reference/actuator/endpoints.html>
  - MDN X-Forwarded-For(보안·파싱·주소 고르기) <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/X-Forwarded-For>
- 실험 목록(모두 2026-10-07, 리눅스 7.0.0-34 호스트, Docker 29.1.3, 컨테이너마다 `--cpus=2`, 외부와 끊긴 `--internal` 도커 네트워크 또는 `--network none`, nginx 1.27.5 `nginx:1.27-alpine`, eclipse-temurin:21-jdk 21.0.12)
  - 실험 1: nginx 라운드로빈 vs `least_conn`, be1 +300ms, 동시 12 × 600건, 2회(+ 점검 재실행 1회)
  - 실험 2: Maglev 모형(JDK 21) — 논문 Table 1 재현, N=100·키 100만 개에서 Maglev(M=65537·655373)·해시 링(가상 노드 100·160)·mod-N 비교, 제거 3회
  - 실험 3: 능동 헬스체크 LB 모형(JDK 21) — deep/shallow × reject/failopen, 공유 DB 6초 지연, deep·reject 3회
  - 실험 4: nginx 수동 헬스체크·재시도 — `max_fails`·`fail_timeout`·`proxy_next_upstream`, 죽은 백엔드 1대
  - 실험 5: nginx `-s reload` 드레이닝, 백엔드 즉시 종료 시 502, GET 재시도 vs POST
  - 실험 6: XFF — 덧붙이기·덮어쓰기, realip `recursive on/off`, 신뢰 범위 전체
  - 실험 7: `ip_hash` vs `hash $remote_addr consistent` — 다른 /24, 같은 /24, 큰 NAT 주소, 2회(결정적)
  - §3의 `netstat` 출력: 실험 1 구성에서 긴 요청 처리 중
