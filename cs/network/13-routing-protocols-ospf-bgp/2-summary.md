# network/13-routing-protocols-ospf-bgp — 라우터는 길을 어떻게 "배우나": 링크 상태·거리 벡터·경로 벡터 — 정리 (힌트)

## 해결하는 문제

라우터는 라우팅 테이블을 보고 패킷을 보낸다(8번 노트).\
그런데 그 테이블은 누가 채우나?

```text
  손으로 채우기 (정적 라우팅)            자동으로 배우기 (라우팅 프로토콜)
  ip route add 10.2.0.0/16 via R2      R1 <-- "나 10.2.0.0/16 알아, 비용 3" -- R2
  - 링크가 끊겨도 모른다                 - 링크가 끊기면 이웃이 알려 준다
  - 라우터 1000대면 불가능               - 새 경로를 스스로 다시 계산한다
```

라우팅 프로토콜은 라우터끼리 "내가 아는 길"을 주고받게 한다.\
그래서 링크가 끊기면 우회로로 바꾸고, 새 망이 생기면 퍼뜨린다.

쉬운 예: 동네 길 찾기다.
- **링크 상태**: 모든 사람이 동네 **지도 전체**를 나눠 갖는다. 각자 지도를 보고 최단 경로를 계산한다.
- **거리 벡터**: 지도 없이 이웃에게 "시청까지 나를 거치면 3블록"만 듣는다. 들은 값에 1을 더해 또 이웃에게 말한다.
- **경로 벡터**: 거리 대신 "시청까지 A동 → B동 → C동을 거친다"는 **경로 목록**을 전한다. 목록에 내 동네가 있으면 받지 않는다.

똑같은 구조다.\
OSPF가 링크 상태, RIP이 거리 벡터, BGP가 경로 벡터다.

실무 예:
- 데이터센터·사내망 안에서는 OSPF 같은 **내부 라우팅(IGP)** 이 돈다.
- 회사와 ISP, ISP와 ISP 사이는 **BGP**로 "우리 망에 이 주소 대역이 있다"를 알린다.
- BGP 설정 실수 하나가 전 세계에서 서비스를 사라지게 한다(Facebook 2021, 아래).

  - *AS(Autonomous System, 자율 시스템)*: 한 조직이 한 가지 라우팅 정책으로 운영하는 망의 묶음이다. 번호(ASN)로 구분한다. 예: YouTube AS36561.
  - *IGP(Interior Gateway Protocol)*: AS 안에서 쓰는 라우팅 프로토콜이다. OSPF·RIP 등.
  - *EGP(Exterior Gateway Protocol)*: AS 사이에서 쓰는 라우팅 프로토콜이다. 오늘날 사실상 BGP-4 하나다.

## 동작·원리

### 세 방식 한눈에

```text
               링크 상태 (OSPF)          거리 벡터 (RIP)             경로 벡터 (BGP)
  이웃에게 보내는 것  내 링크 정보(LSA)를        내 거리표 전체를             목적지별 "경로 전체"와 속성을
                   전체에 flooding          이웃에게만                   이웃에게만
  각자 가진 것      망 전체 지도(LSDB)         이웃이 말한 거리만           이웃이 말한 경로들
  계산             다익스트라                 벨만-포드 (분산)             정책 + 결정 과정
  루프 방지         모두 같은 지도             split horizon 등, 느림       AS_PATH에 내 AS 있으면 버림
  쓰는 곳           AS 내부                   AS 내부 (작은 망)            AS 사이 (인터넷)
```

### 링크 상태 — OSPF

```text
  (1) 이웃 찾기             (2) 지도 조각 뿌리기            (3) 각자 최단 경로 계산
  R1 --Hello--> R2         R1: "나-R2 비용1, 나-R3 비용4"   LSDB(전체 지도)
  R1 <--Hello-- R2          --> 모든 라우터에 flooding       |
  (10초마다, 예시값)                                          v
                                                          다익스트라: 나를 뿌리로 하는
                                                          최단 경로 트리 -> 라우팅 테이블
```

1. **Hello**로 이웃을 찾고 살아 있는지 확인한다.
   - RFC 2328은 LAN의 HelloInterval 예시값으로 10초를 든다(부록 C.3).
   - RouterDeadInterval 동안 Hello가 없으면 이웃이 죽었다고 본다. 값은 HelloInterval의 배수(예: 4배)로 둔다(부록 C.3).
2. 각 라우터는 자기 링크 정보를 **LSA**로 만들어 area 전체에 **flooding**한다(§13).
3. 같은 area의 모든 라우터가 같은 **LSDB**를 갖는다. 각자 자기를 뿌리로 **다익스트라**를 돌려 최단 경로 트리를 만든다(§16.1).

  - *LSA(Link State Advertisement)*: "나는 누구와 어떤 비용으로 연결돼 있다"를 담은 광고다.
  - *LSDB(Link State Database)*: 받은 LSA를 모두 모은 망 지도다.
  - *flooding*: 받은 LSA를 받은 곳을 뺀 모든 이웃에게 다시 보내 전체에 퍼뜨리는 방식이다.
  - *area*: OSPF 망을 나눈 구역이다. area 0(0.0.0.0)이 **backbone**이고, 다른 area끼리의 통신은 backbone을 거친다(§3.1). 지도를 area별로 쪼개 계산량을 줄인다.

링크 하나가 끊기면 그 끝의 라우터가 새 LSA를 뿌린다.\
모두가 다시 다익스트라를 돌린다.\
지도 전체를 알기 때문에 수렴이 빠르다.

### 거리 벡터 — RIP과 "무한까지 세기"

```text
  각 라우터: D(나 -> 목적지) = min over 이웃 v { cost(나, v) + D(v -> 목적지) }   (벨만-포드)

  정상        A --1-- B --1-- C --(망 N, 직접 연결)
              C: N까지 1 (직접)   B: N까지 2 (C 경유)   A: N까지 3 (B 경유)

  B-C 링크 끊김
              B: "C 경유 경로 잃음". 그런데 A가 "N까지 3"이라고 말한다
              B: N까지 4 (A 경유)   <- A의 3이 사실 B를 거친 값인 줄 모름
              A: N까지 5 (B 경유)
              B: N까지 6 ...        -> 서로 1씩 올리며 16(무한)까지 간다
```

- RIP에서 직접 붙은 망의 거리는 보통 1이다(RFC 2453 §3.4.2 예). 그래서 그림에서 C는 1, B는 2, A는 3이다.
- RIP은 거리 16을 "무한(도달 불가)"으로 쓴다(RFC 2453 §3.4.1). 그래서 RIP 망의 지름은 15홉까지다.
- 위처럼 서로 잘못된 값을 주고받으며 16까지 올라가는 문제를 **counting to infinity**라 한다(RFC 2453 §3.4.2).
- 완화책이 **split horizon**이다. 어떤 이웃에게서 배운 경로는 그 이웃에게 다시 알리지 않는다(RFC 2453 §3.4.3). poisoned reverse는 한 걸음 더 나가 그 이웃에게 "무한"으로 알린다.
- RIP은 업데이트를 30초마다 보낸다(RFC 2453 §3.1). 그래서 수렴이 느리다.

### 경로 벡터 — BGP

```text
  AS 65001 (우리)          AS 3491 (ISP)              AS 174 (다른 ISP)
  "203.0.113.0/24 여기 있음"
   --UPDATE: 203.0.113.0/24, AS_PATH=[65001]-->
                           --UPDATE: AS_PATH=[3491 65001]-->
                                                     받는 쪽: AS_PATH에 내 AS(174)가 있나?
                                                     없음 -> 후보로 저장, 정책으로 고름
```

- BGP는 **TCP 179번** 포트로 이웃(peer)과 세션을 맺는다(RFC 4271 §3, §8.2.1). 신뢰성 있는 전달은 TCP에 맡긴다.
- 메시지는 넷이다: OPEN, UPDATE, NOTIFICATION, KEEPALIVE(§4).
- UPDATE가 경로를 알리거나 거둔다(withdraw). 경로에는 **속성**이 붙는다.
  - *AS_PATH*: 이 경로가 지나온 AS 번호 목록이다. 한 AS를 지날 때마다 그 AS 번호를 앞에 붙인다(§5.1.2).
  - *NEXT_HOP*: 이 목적지로 가려면 보낼 다음 라우터 주소다.
  - *LOCAL_PREF*: 우리 AS 안에서 어느 출구를 선호할지 정하는 값이다. 클수록 선호한다.
- **루프 방지**: 받은 경로의 AS_PATH에 내 AS 번호가 있으면 그 경로를 결정 과정에서 뺀다(should, §9.1.2).
- **경로 선택**(§9.1)
  1. Phase 1: 정책으로 선호도를 매긴다. 내부 peer에게서 온 경로는 LOCAL_PREF를 쓴다(§9.1.1).
  2. Phase 2: 선호도가 같으면 동점 깨기 규칙을 **정해진 순서로** 적용한다. 첫 기준은 "AS_PATH의 AS 개수가 가장 적은 것"이다(§9.1.2.2).
  - 즉 BGP는 "가장 짧은 경로"보다 **정책(비즈니스 관계)** 이 먼저다.
- **세션 생존 확인**: BGP는 TCP keepalive가 아니라 자체 KEEPALIVE 메시지를 쓴다(§4.4).
  - Hold Time 동안 아무 메시지도 안 오면 세션을 끊는다. 권장 기본값은 Hold Time 90초, KEEPALIVE 간격은 그 1/3이다(§10).
  - 세션이 끊기면 기본적으로 그 peer에게서 배운 경로를 모두 거둔다.
  - 예외: Graceful Restart를 협상했고 TCP 세션 종료가 감지되면, peer가 재시작하는 동안 그 경로를 "stale"로 표시해 계속 쓴다. Restart Time 안에 다시 맺지 못하면 지운다(RFC 4724 §4.2). NOTIFICATION·Hold Timer 만료까지 이 규칙을 넓히는 확장이 RFC 8538이다.

BGP 세션의 상태 기계(§8.2.2):

```text
  Idle -> Connect -> (Active) -> OpenSent -> OpenConfirm -> Established
          TCP 연결 시도   재시도     OPEN 보냄    OPEN 받음,       UPDATE 교환
                                               KEEPALIVE 대기
```

### 최장 접두사 매칭이 하이재킹을 만든다

라우터는 목적지에 맞는 경로 중 **가장 긴 접두사**를 고른다(RFC 1812 §5.2.4.3 "Longest Match", 8번 노트).\
BGP로 배운 경로도 포워딩 테이블에 들어가면 같은 규칙을 탄다. 그래서 더 구체적인 접두사가 이긴다.

```text
  2008-02-24 (RIPE NCC RIS 사례 연구)
  YouTube(AS36561)가 알린 경로:        208.65.152.0/22
  Pakistan Telecom(AS17557)이 알린 경로: 208.65.153.0/24   <- 더 구체적 (/24 > /22)
  상위 ISP PCCW(AS3491)가 걸러내지 않고 전파

  전 세계 라우터: 208.65.153.x 목적지 -> /24가 더 길다 -> 파키스탄으로
```

- 18:47 UTC에 잘못된 /24 광고가 시작됐다.
- YouTube는 20:07에 같은 /24를, 20:18에 더 긴 /25 두 개를 알려 트래픽을 되찾았다.
- 21:01에 PCCW가 Pakistan Telecom 경로를 거뒀다(RIPE NCC).
- 교훈: BGP는 "이 AS가 이 대역을 가질 권한이 있나"를 기본으로 검사하지 않는다.

  - *경로 하이재킹(route hijack)*: 권한 없는 AS가 남의 주소 대역을 자기 것처럼 광고해 트래픽을 끌어가는 것이다.
  - *경로 누출(route leak)*: 받은 경로를 전파하면 안 되는 이웃에게 전파해, 트래픽이 의도하지 않은 길로 몰리는 것이다.

## 쓰이는 자료구조·알고리즘

- **다익스트라** — OSPF의 최단 경로 트리 계산(RFC 2328 §16.1). 우선순위 큐로 가장 가까운 노드부터 확정한다. [algorithm/14-dijkstra](../../algorithm/14-dijkstra/2-summary.md)
- **벨만-포드** — 거리 벡터의 식 `D(x,y) = min_v { c(x,v) + D(v,y) }`를 라우터마다 분산으로 반복한다(RFC 2453 §3.1). [algorithm/15-bellman-floyd](../../algorithm/15-bellman-floyd/2-summary.md)
- **그래프** — LSDB는 가중 그래프다. 링크 비용이 간선 가중치다. [data-structure/08-graph](../../data-structure/08-graph/2-summary.md)
- **트라이(LPM)** — 계산 결과는 포워딩 테이블에 들어가 최장 접두사 매칭으로 조회된다. [data-structure/20-radix-trie](../../data-structure/20-radix-trie/2-summary.md)
- **상태 기계** — OSPF 이웃 상태(Down → Init → 2-Way → ExStart → Exchange → Loading → Full), BGP 세션 FSM.
- **RIB 단계** — BGP는 Adj-RIB-In(이웃별로 받은 것) → Loc-RIB(고른 것) → Adj-RIB-Out(이웃별로 보낼 것)으로 나눠 둔다(RFC 4271 §1.1·§3.1).

링크 상태와 거리 벡터의 차이를 코드로 보면 이렇다(TypeScript, 개념 예시).

```ts
// 링크 상태: 지도 전체(graph)를 알고, 나를 시작점으로 다익스트라
function linkState(graph: Map<string, [string, number][]>, me: string) {
  const dist = new Map([[me, 0]]);
  const done = new Set<string>();
  while (true) {
    let u: string | undefined, best = Infinity;
    for (const [n, d] of dist) if (!done.has(n) && d < best) { u = n; best = d; }
    if (u === undefined) return dist;          // 모든 노드 확정
    done.add(u);
    for (const [v, w] of graph.get(u) ?? []) {
      if (best + w < (dist.get(v) ?? Infinity)) dist.set(v, best + w);
    }
  }
}

// 거리 벡터: 이웃이 말해 준 거리표만 보고 한 번 갱신 (이걸 계속 반복)
const INFINITY = 16;                            // RIP의 "도달 불가"
function distanceVectorStep(
  linkCost: Map<string, number>,                // 이웃 -> 그 이웃까지 비용
  neighborTables: Map<string, Map<string, number>>, // 이웃 -> (목적지 -> 거리)
) {
  const mine = new Map<string, number>();
  for (const [nb, table] of neighborTables) {
    for (const [dst, d] of table) {
      const via = Math.min(INFINITY, linkCost.get(nb)! + d);
      if (via < (mine.get(dst) ?? INFINITY)) mine.set(dst, via);
    }
  }
  return mine;                                  // 이 표를 다시 이웃에게 알린다
}
```

- `linkState`는 지도 전체가 입력이다. 모두 같은 지도를 가지면 모두 일관된 답을 낸다.
- `distanceVectorStep`은 이웃의 말만 믿는다. 이웃의 값이 나를 거친 값이어도 알 수 없다. 그래서 counting to infinity가 생긴다.

## 적용 — 풀어나가는 법

### 1. 내 서비스와 BGP의 관계를 안다

- 클라우드·호스팅을 쓰면 BGP는 보통 제공자가 운영한다. 그래도 "우리 대역이 어떻게 광고되는가"는 가용성의 일부다.
- 자체 AS를 운영하면 다음을 지킨다.
  - 이웃에게서 받을 경로 수에 상한(max-prefix)을 둔다(RFC 7454 §8 RECOMMENDED).
  - 고객에게서는 그 고객의 대역·AS만 받는다(prefix·AS_PATH 필터, RFC 7454 §6·§9).
  - RPKI ROA를 발행하고, 받은 경로의 출발 AS를 검증한다(RFC 6811).

  - *RPKI ROA(Route Origin Authorization)*: "이 대역은 이 AS만 광고할 수 있다"는 서명된 문서다.
  - *출발지 검증(Origin Validation)*: 받은 경로를 ROA와 대조해 Valid·Invalid·NotFound로 판정한다(RFC 6811 §2).

### 2. 진단 명령과 도구

```bash
# 내 호스트의 라우팅 테이블 — 어떤 경로가 어떤 프로토콜로 들어왔나
ip route show
ip route get 8.8.8.8            # 이 목적지에 실제로 쓰일 경로

# 경로 따라가기 — 어디서 끊기나
traceroute -n example.com
mtr -n example.com

# 라우터(FRRouting)에서
vtysh -c 'show ip ospf neighbor'     # OSPF 이웃이 Full인가
vtysh -c 'show bgp summary'          # BGP 세션이 Established인가, 받은 경로 수
```

- 인터넷 쪽 시야는 공개 도구로 본다. RIPEstat·BGP looking glass에서 "내 대역을 지금 어느 AS가 광고하나"를 확인한다.

## 장애 시나리오와 대처

### 1. BGP 경로 하이재킹·누출 — 특정 대역만 전 세계에서 도달 불가

- **현상**: 우리 서비스의 일부 IP 대역만 사용자 다수가 접속하지 못한다. 서버는 멀쩡하다.
- **보이는 형태**
  - 외부 traceroute가 엉뚱한 나라·ISP로 빠진다.
  - RIPEstat·looking glass에서 우리 대역보다 **더 구체적인** 접두사를 다른 AS가 광고한다.
- **원인**: 다른 AS가 우리 대역을 광고했다(실수 또는 공격). 더 긴 접두사가 이긴다. 상위 ISP가 걸러내지 않았다(Pakistan Telecom–YouTube 2008).
- **대처**
  - 같은 길이 또는 더 구체적인 접두사를 광고해 트래픽을 되찾는다(YouTube가 /24·/25로 대응).
  - 상위 ISP에 연락해 잘못된 경로를 막게 한다.
  - 평소에 ROA를 발행해 둔다. RPKI 검증을 하는 망은 Invalid 경로를 거를 수 있다.

### 2. 자기 경로 철회 — 서버는 살아 있는데 인터넷에서 사라진다 (Facebook 2021)

- **현상**: 모든 서비스가 한꺼번에 사라진다. DNS 조회부터 실패한다.
- **보이는 형태**
  - 외부에서 권한 DNS 서버 주소로 가는 경로가 없다. 공용 리졸버는 SERVFAIL을 준다.
  - 사용자 앱이 재시도하며 공용 리졸버의 질의량이 평소의 30배로 뛰었다(Cloudflare 관측).
- **원인** (Meta 엔지니어링 블로그)
  - 정기 작업 중 백본 용량을 점검하려던 명령이 백본 연결 전체를 끊었다. 이를 막아야 할 감사 도구에 버그가 있었다.
  - DNS 서버는 데이터센터와 통신이 안 되면 자기 BGP 광고를 거두도록 설계돼 있었다. 그래서 DNS 서버 대역이 인터넷에서 사라졌다.
  - Cloudflare 관측: 15:40 UTC께 경로 변화가 몰렸고, 21:00께 광고가 돌아왔다.
- **대처**
  - 자동 광고 철회 로직에 "전부 철회"를 막는 안전장치를 둔다.
  - 복구 경로(원격 접속·현장 접근)가 장애 대상 망에 의존하지 않게 한다.
  - 권한 DNS를 서로 다른 망·제공자에 분산한다.

### 3. BGP 세션 flapping — 경로가 붙었다 떨어졌다 한다

- **현상**: 특정 ISP 경유 트래픽이 수 분 간격으로 끊겼다 붙는다.
- **보이는 형태**: 라우터 로그에 NOTIFICATION "Hold Timer Expired"(RFC 4271 §6.5)와 세션 재수립이 반복된다. `show bgp summary`의 Up/Down 시간이 계속 초기화된다.
- **원인**: Hold Time(권장 90초) 동안 KEEPALIVE가 도착하지 않았다. 링크 혼잡·CPU 과부하·MTU 문제로 BGP 메시지가 늦거나 사라진다[?].
- **대처**
  - 세션이 지나는 링크의 손실·혼잡을 먼저 본다.
  - 라우터 CPU를 확인한다. BGP 트래픽을 우선 처리하게 한다.
  - 경로가 불안정하면 전 세계에 UPDATE가 퍼진다. 원인을 고치기 전까지 불안정한 peer를 내린다.

### 4. OSPF 이웃이 Full까지 안 올라간다

- **현상**: 새로 연결한 라우터가 경로를 배우지 못한다.
- **보이는 형태**: `show ip ospf neighbor`에서 이웃 상태가 ExStart·Exchange에 머문다.
- **원인**: 양쪽 인터페이스 MTU가 다르다. OSPF는 Database Description 패킷의 Interface MTU가 자기가 받을 수 있는 크기보다 크면 그 패킷을 거부한다(RFC 2328 §10.6). 그래서 DB 교환이 진행되지 않는다.\
  Hello의 마스크·HelloInterval·RouterDeadInterval이 다르면 그 Hello를 버린다(§10.5). area ID·인증 설정이 다르면 패킷 자체를 버린다(§8.2). 둘 다 이웃이 아예 맺어지지 않는다.
- **대처**: 양쪽 MTU·타이머·area·인증 설정을 맞춘다.

### 5. 라우팅 루프 — `Time to live exceeded`

- **현상**: 특정 목적지로 가는 패킷이 사라진다.
- **보이는 형태**: traceroute에서 같은 두 라우터 주소가 번갈아 나온다. ICMP "Time to live exceeded"가 돌아온다.
- **원인**
  - 수렴 중에 라우터들의 테이블이 서로 어긋났다(거리 벡터의 counting to infinity가 대표적이다).
  - 또는 정적 경로와 동적 경로가 서로를 가리킨다.
- **대처**
  - 일시적이면 수렴을 기다린다.
  - 지속되면 두 라우터의 해당 접두사 경로를 비교해 서로를 가리키는 쪽을 고친다(8·9번 노트).

## 핵심 문장

- 라우팅 프로토콜은 라우터끼리 길을 알려 줘서 라우팅 테이블을 자동으로 채우고, 링크가 끊기면 다시 계산하게 한다.
- 링크 상태(OSPF)는 **지도 전체를 flooding**하고 각자 다익스트라를 돌린다. 거리 벡터(RIP)는 **이웃의 거리만** 믿고 벨만-포드를 반복해 counting to infinity가 생긴다.
- BGP는 목적지마다 **AS 경로 전체**를 전해 내 AS가 보이면 버리는 방식으로 루프를 막고, 최단 경로보다 **정책**으로 고른다.
- BGP는 기본적으로 "그 대역을 광고할 권한"을 검사하지 않는다. 그래서 더 구체적인 잘못된 광고 하나가 최장 접두사 매칭을 타고 트래픽을 빼앗는다.
- 방어선은 필터(prefix·max-prefix)와 RPKI 출발지 검증이다. 자동 철회 로직에는 "전부 사라지기"를 막는 안전장치가 필요하다.

## 관련 주제·근거

- 선행
  - [08-routing-and-longest-prefix-match](../08-routing-and-longest-prefix-match/2-summary.md) — 라우팅 테이블·최장 접두사 매칭.
  - [algorithm/14-dijkstra](../../algorithm/14-dijkstra/2-summary.md) — OSPF의 계산
- 연결
  - [algorithm/15-bellman-floyd](../../algorithm/15-bellman-floyd/2-summary.md) — 거리 벡터의 계산
  - [data-structure/20-radix-trie](../../data-structure/20-radix-trie/2-summary.md) — 포워딩 테이블 조회
  - [09-icmp-ping-traceroute](../09-icmp-ping-traceroute/2-summary.md) — 루프·경로 확인 도구.
  - [15-tcp-handshake-and-backlog](../15-tcp-handshake-and-backlog/2-summary.md) — BGP 세션은 TCP 179 위에서 돈다
  - [27-dns-resolution](../27-dns-resolution/2-summary.md) — 권한 DNS 대역이 사라지면 생기는 일.
- RFC
  - RFC 2328 OSPF Version 2 <https://www.rfc-editor.org/rfc/rfc2328>
    - §3.1 backbone(Area 0) · §8.2 패킷 수신 검사(area·인증) · §10.5 Hello 수신 조건 · §10.6 DD 패킷의 Interface MTU 검사
    - §13 flooding · §16.1 최단 경로 트리(다익스트라) · 부록 C.3 HelloInterval(LAN 예시 10초)·RouterDeadInterval(배수, 예: 4)
  - RFC 2453 RIP Version 2 — §3.1 벨만-포드·30초 업데이트, §3.4.1 무한 = 16, §3.4.2 counting to infinity(직접 연결 망 메트릭 1 예), §3.4.3 split horizon <https://www.rfc-editor.org/rfc/rfc2453>
  - RFC 1812 Requirements for IP Version 4 Routers — §5.2.4.3 Longest Match <https://www.rfc-editor.org/rfc/rfc1812>
  - RFC 4271 BGP-4 <https://www.rfc-editor.org/rfc/rfc4271>
    - §4 메시지 4종 · §4.4 KEEPALIVE(Hold Time의 1/3) · §5.1.2 AS_PATH
    - §6.5 Hold Timer Expired · §8.2.2 FSM
    - §9.1.1 Phase 1(LOCAL_PREF) · §9.1.2 AS 루프 제외 · §9.1.2.2 동점 깨기(AS_PATH 길이 먼저)
    - §10 타이머 권장값(HoldTime 90초, ConnectRetry 120초)
  - RFC 4724 Graceful Restart — §4.2 수신 측은 경로를 stale로 유지 <https://www.rfc-editor.org/rfc/rfc4724>
  - RFC 8538 Notification Message Support for BGP Graceful Restart <https://www.rfc-editor.org/rfc/rfc8538>
  - RFC 6811 BGP Prefix Origin Validation — Valid·Invalid·NotFound <https://www.rfc-editor.org/rfc/rfc6811>
  - RFC 7454 BGP Operations and Security — §8 max-prefix <https://www.rfc-editor.org/rfc/rfc7454>
- 사고 사례
  - RIPE NCC, "YouTube Hijacking: A RIPE NCC RIS case study"(2008) <https://www.ripe.net/publications/news/industry-developments/youtube-hijacking-a-ripe-ncc-ris-case-study>
  - Meta Engineering, "More details about the October 4 outage"(2021) <https://engineering.fb.com/2021/10/05/networking-traffic/outage-details/>
  - Cloudflare, "Understanding how Facebook disappeared from the Internet"(2021) <https://blog.cloudflare.com/october-2021-facebook-outage/>
- Kurose & Ross 8판 5.2(링크 상태·거리 벡터 알고리즘)·5.3(OSPF)·5.4(BGP)
