# distributed/05-logical-clocks — 램포트 시계·벡터 시계·happens-before — 정리 (힌트)

## 해결하는 문제

서버마다 벽시계가 조금씩 어긋난다. 그 시각으로 사건을 정렬하면 원인과 결과가 뒤집힐 수 있다.

```text
  P0(시계 정확)  100 주문 생성 ── 110 전송 ──┐
                                            │ 메시지
  P1(시계 80ms 느림)                          └─> 50 수신 → 배송 생성
  벽시계로 정렬:  배송(50) → 주문(100)      ← 결과가 원인보다 먼저
```

- 값은 멀쩡히 찍혀 있다. 그래서 에러 없이 틀린 순서가 로그·이벤트 저장소에 남는다.
- 해법: 시각을 재지 않고 **누가 무엇을 들었나**를 센다.
  - *논리 시계(logical clock)*: 물리 시각 없이 사건의 인과 순서를 숫자로 기록하는 장치. 램포트 시계와 벡터 시계가 대표다.

쉬운 예: 편지로만 소식을 주고받는 두 마을.
- 두 마을의 벽시계는 안 맞는다.
- 그래도 "네 편지를 받고 나서 이 일을 했다"는 순서는 확실하다.

똑같은 구조다.\
한 마을 안의 일은 일어난 차례대로 순서가 있다. 서로 다른 마을의 두 일은 편지(메시지)가 이어 주지 않으면 순서를 말할 근거가 없다.

실무 예:
- 이벤트 소싱·감사 로그에서 서버마다 찍은 시각으로 정렬했더니 "환불"이 "결제"보다 앞에 온다.
- 복제본 두 곳에서 같은 키를 고쳤다. 어느 쪽이 나중인지, 아니면 서로 모른 채 동시에 고쳤는지 가려야 한다(24번).
- 분산 추적에서 호출 순서를 서버 시각으로만 복원하면 자식 span이 부모보다 먼저 시작한 것처럼 보인다.

## 동작·원리

### 1. happens-before (→) — 순서의 정의

```text
  P0:  a ──── b(send m1) ──────────────────────────── g
                 \
  P1:             └──> d(recv m1) ── e(send m2)
                                          \
  P2:  c ───────────────────────────────── └──> f(recv m2)

  a → b → d → e → f        (같은 프로세스 안의 순서 + 보내기→받기, 이어 붙이기)
  c → f                    (같은 P2 안)
  c ∥ d, g ∥ d, g ∥ f       (어느 쪽으로도 화살표 경로가 없다 = 동시)
```

- Lamport 1978의 정의: 다음 셋으로만 `a → b`가 생긴다.
  1. 같은 프로세스에서 a가 b보다 먼저 일어났다.
  2. a가 메시지를 보냈고 b가 그 메시지를 받았다.
  3. a → x이고 x → b이다(이행성).
  - *happens-before(→)*: "a가 b에 영향을 줄 수 있었다"는 관계. 물리 시각이 아니라 정보가 흐를 수 있었는지로 정한다.
- 어느 쪽도 성립하지 않으면 두 사건은 *동시(concurrent, ∥)*다.
  - 동시는 "같은 시각"이 아니다. 서로 소식이 닿지 않았다는 뜻이다.
- 그래서 →는 **부분 순서**다. 모든 쌍을 비교할 수 있지는 않다.
  - *부분 순서(partial order)*: 일부 쌍만 비교 가능한 순서. 비교 불가능한 쌍이 동시다.
- 모델: Lamport의 정의는 메시지 지연 상한도, 시계 동기도 가정하지 않는다(비동기 모델). 프로세스 고장도 다루지 않는다.

### 2. 램포트 시계 — 숫자 하나

```text
  IR1  사건마다:            C := C + 1
  IR2  보낼 때:             메시지에 C를 싣는다
       받을 때(값 Tm):      C := max(C, Tm) + 1

  P0: a=1  b=2 ─────────────────────────────── g=3
               \ (Tm=2)
  P1:           └> d=max(0,2)+1=3   e=4
                                      \ (Tm=4)
  P2: c=1 ─────────────────────────────└> f=max(1,4)+1=5
```

- 논문 IR2(b)는 "받은 뒤 C를 현재 값 이상이면서 Tm보다 크게"만 요구한다. `max(C, Tm) + 1`은 그 조건을 채우는 흔한 구현이다.
- 보장하는 것은 **한 방향**이다(Clock Condition): `a → b`이면 `C(a) < C(b)`.
- 역은 성립하지 않는다. `C(c)=1 < C(d)=3`이지만 c와 d는 동시다.
  - Lamport 1978도 "역 조건은 기대할 수 없다. 그러면 동시인 두 사건이 같은 시각에 일어나야 한다"고 적는다.
- **전순서 만들기**: 값이 같으면 프로세스 번호로 끊는다. `(C, 프로세스 번호)` 사전순.
  - 이 순서는 →를 어기지 않는 여러 전순서 중 **하나**일 뿐이다. 동시인 쌍의 앞뒤는 임의로 정해진다.
  - 그래도 모두가 같은 규칙을 쓰면 모두 같은 순서에 동의한다. 논문은 이것으로 분산 상호 배제(요청 큐)를 푼다.

### 3. 벡터 시계 — 프로세스마다 한 칸

```text
  V[i] = "프로세스 i의 사건을 몇 번째까지 (직간접으로) 들었나"

  사건마다:      V[me] += 1
  보낼 때:       V를 싣는다
  받을 때(Vm):   V[k] := max(V[k], Vm[k])  모든 k   →  그다음 V[me] += 1

  P0: a=[1,0,0] b=[2,0,0] ──────────────────────── g=[3,0,0]
                    \
  P1:                └> d=[2,1,0]  e=[2,2,0]
                                       \
  P2: c=[0,0,1] ─────────────────────── └> f=[2,2,2]
```

- 비교 규칙
  - `V(a) ≤ V(b)`(칸마다 작거나 같다)이고 하나라도 작으면 `a → b`.
  - 서로 상대보다 큰 칸이 있으면 동시. 예: `c=[0,0,1]`과 `d=[2,1,0]`.
- 벡터 시계는 **양방향**이 성립한다: `a → b` ⇔ `V(a) < V(b)`(Mattern 1989가 "isomorphism"이라 부른 성질). 그래서 "동시다"를 믿을 수 있다.
- 대가: 프로세스 수 n만큼의 칸을 **메시지마다** 싣는다. 참여자가 계속 바뀌면 칸 관리가 문제다(장애 3).

### 실험: 어긋난 벽시계 vs 램포트 vs 벡터

- 코드: `Clocks.java`(아래 핵심). 세 프로세스, P1 벽시계 −80ms, P2 +30ms(예시 값). 위 그림의 사건 a~g를 실제 시각 100~160ms에 일으킨다.

```java
Event receive(String name, long real, Event msg) {
    lamport = Math.max(lamport, msg.lamport) + 1;                  // max + 1
    for (int i = 0; i < N; i++) vc[i] = Math.max(vc[i], msg.vc[i]); // 칸마다 max
    vc[id]++;                                                       // 그다음 내 칸 +1
    return new Event(name, id, wall(real), lamport, vc);
}
```

(실험, eclipse-temurin 21 JDK 컨테이너에서 `java Clocks.java`, 2026-10-01)

```text
사건                     proc  벽시계  램포트  벡터
a:주문생성                  P0     100      1    [1, 0, 0]
b:P0→P1 전송              P0     110      2    [2, 0, 0]
c:P2 독립작업               P2     145      1    [0, 0, 1]
d:P1 수신(배송생성)           P1      50      3    [2, 1, 0]
e:P1→P2 전송              P1      60      4    [2, 2, 0]
f:P2 수신                 P2     180      5    [2, 2, 2]
g:P0 독립작업               P0     160      3    [3, 0, 0]

벽시계 정렬:   d e a b c g f
램포트 정렬:   a c b g d e f

쌍     벽시계 판단        램포트 판단       벡터 판단
a,d    y 먼저(100,50)    x 먼저(?)(1,3)    BEFORE
b,d    y 먼저(110,50)    x 먼저(?)(2,3)    BEFORE
d,f    x 먼저(50,180)    x 먼저(?)(3,5)    BEFORE
a,f    x 먼저(100,180)   x 먼저(?)(1,5)    BEFORE
c,d    y 먼저(145,50)    x 먼저(?)(1,3)    CONCURRENT
c,f    x 먼저(145,180)   x 먼저(?)(1,5)    BEFORE
g,d    y 먼저(160,50)    같음(3,3)         CONCURRENT
g,f    x 먼저(160,180)   x 먼저(?)(3,5)    CONCURRENT

무작위 200회×30사건: 사건 쌍 87000, 벡터상 동시 43678 (50.2%), 그중 램포트 값이 달라 순서처럼 보인 쌍 39089 (89.5%), 인과 쌍에서 램포트가 순서를 어긴 경우 0
```

- 관찰
  - 벽시계 정렬은 `d`(배송, 50)를 `a`(주문, 100)보다 앞에 둔다. 인과 역전이다.
  - 램포트 정렬은 인과 쌍(a·b·d·e·f 사슬)을 한 번도 어기지 않았다. 무작위 200회에서도 위반 0이다.
  - 그러나 c와 d는 동시인데 램포트 값은 1과 3이라 "c가 먼저"처럼 보인다. 무작위 실험(프로세스 3개·30사건, 시드 1 고정)에서 동시 쌍의 89.5%가 이렇게 값이 달랐다. 이 비율은 작업 부하에 따라 달라진다.
  - 벡터 판단만 동시 쌍을 CONCURRENT로 정확히 가렸다.
- 해석: "램포트 값이 다르다"를 "순서가 있다"로 읽으면 동시 쌍 대부분에 근거 없는 순서를 붙인다.

### 4. 숨은 채널 — 시스템 밖의 인과는 못 본다

```text
  사용자: 컴퓨터 A에 요청 A ──(전화로 친구에게 알림)──> 친구: 컴퓨터 B에 요청 B
  시스템 안의 메시지 경로 없음 → 시스템은 A ∥ B로 본다 → B가 더 작은 시계 값을 받을 수 있다
```

- Lamport 1978의 "anomalous behavior" 예다. 논리 시계는 **시스템이 나르는 메시지**만 본다.
- 막는 방법은 둘이다.
  - 앞 요청의 타임스탬프를 사용자에게 돌려주고, 다음 요청에 실어 보내게 한다(인과 토큰).
  - 물리 시계를 충분히 맞춰 "Strong Clock Condition"에 가깝게 한다. 이 방향이 HLC·TrueTime이다(26번).

## 쓰이는 자료구조·알고리즘

- **단조 카운터 + max** — 램포트 시계 전체. long 하나.
- **노드 → 카운터 맵** — 벡터 시계·버전 벡터의 그릇. 없는 칸은 0으로 본다. [data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md)
- **부분 순서 비교(칸마다 ≤)** — 두 벡터를 원소별로 비교해 BEFORE / AFTER / CONCURRENT / EQUAL을 낸다. 칸마다 max가 곧 두 벡터의 최소 상계(join)다. 이 성질이 CRDT 병합의 바탕이다(24번).
- **사전순 비교 (값, 노드 번호)** — 램포트 값으로 전순서를 만들 때 동률 깨기.
- **버전 벡터(version vector)** — 같은 모양을 "사건"이 아니라 "한 키의 복제본 버전"에 붙인 것. Amazon Dynamo 논문(DeCandia 외 2007, §4.4)과 Riak이 충돌 감지에 쓴다. Riak 2.0부터는 형제 수를 줄이는 dotted version vector를 권한다(Riak 문서 Causal Context).
- **HLC** — 물리 시각에 램포트식 카운터를 붙인 64비트 타임스탬프(26번).

## 적용 — 풀어나가는 법

### 1. 순서가 필요한지, 동시를 알아야 하는지 먼저 정한다

| 필요한 것 | 도구 | 예 |
|---|---|---|
| 모두가 같은 순서에 동의만 하면 된다 | 램포트 (값, 노드) 전순서 | 분산 락 큐, 로그 병합 순서 |
| "이 둘은 서로 몰랐다"를 감지해야 한다 | 벡터 시계 / 버전 벡터 | 복제본 충돌 감지, 공동 편집 |
| 사람이 읽는 시각과 가까우면서 인과도 지켜야 한다 | HLC (26번) | 분산 DB 타임스탬프 |
| 한 자원에 대한 "더 최근"만 필요하다 | 단조 증가 토큰(epoch·term·revision) | fencing token(12번) |

### 2. 경계마다 시계를 실어 나른다 (Java)

```java
// 램포트 시계: 스레드 안전, 영속 저장 지점을 둔다
public final class LamportClock {
    private final AtomicLong c;
    public LamportClock(long restored) { this.c = new AtomicLong(restored); } // 재기동 시 저장값에서 시작
    public long tick() { return c.incrementAndGet(); }                       // 로컬 사건·보내기
    public long onReceive(long remote) {                                     // 받기: max + 1
        return c.updateAndGet(local -> Math.max(local, remote) + 1);
    }
}

// HTTP·메시지 헤더로 나른다 (헤더 이름은 예시)
long ts = clock.tick();
request.header("X-Lamport", Long.toString(ts));
// 받는 쪽: 처리 전에 반영
long now = clock.onReceive(Long.parseLong(req.getHeader("X-Lamport")));
```

- 순서
  1. 인과가 중요한 경계(HTTP 호출·큐 메시지·이벤트 저장)를 모두 찾는다.
  2. 보내는 쪽은 `tick()` 값을 싣는다.
  3. 받는 쪽은 처리 **전에** `onReceive()`를 부른다.
  4. 시계 값을 사건과 함께 저장하고, 재기동 시 저장된 최댓값부터 이어 간다(장애 1).
  5. 사용자를 거치는 숨은 채널이 있으면 응답에 시계 값을 돌려주고 다음 요청에 싣게 한다.

### 3. 진단

- 이벤트 저장소에서 "원인 id보다 결과의 시계 값이 작거나 같은" 행을 찾는다. 행이 나오면 Clock Condition이 깨진 것이다. 원인 후보는 경계에서 `onReceive`가 빠진 것, 재기동 때 시계 값을 복원하지 못한 것(장애 2) 등이다.

```sql
-- 예시 스키마: events(id, causation_id, lamport)
SELECT e.id, e.lamport, c.lamport AS cause_lamport
FROM events e JOIN events c ON e.causation_id = c.id
WHERE e.lamport <= c.lamport;
```

- 벽시계 어긋남 자체는 `chronyc tracking` 같은 도구로 본다([04-physical-clocks-and-ntp](../04-physical-clocks-and-ntp/2-summary.md)).

## 장애 시나리오와 대처

### 1. 벽시계 타임스탬프로 이벤트 순서를 정함 → 인과 역전 (커리큘럼 ⚠)

- **현상**: 이벤트 재생·감사 로그에서 결과가 원인보다 앞에 나온다. 상태 재구성이 틀린다.
- **보이는 형태**: `created_at` 정렬 결과에서 배송이 주문보다 먼저, 환불이 결제보다 먼저. 에러는 없다. 위 실험의 `벽시계 정렬: d e a b c g f`가 같은 모양이다.
- **원인**: 노드마다 벽시계가 어긋나 있다. 메시지 지연보다 어긋남이 크면 받은 쪽 시각이 보낸 쪽보다 작아진다.
- **대처**
  - 순서의 근거를 논리 시계(또는 HLC)로 바꾼다. `created_at`은 표시용으로만 둔다.
  - 한 파티션 안의 순서만 필요하면 단일 리더가 매기는 순번(로그 오프셋 등)을 쓴다([17-queues-logs-and-delivery-semantics](../17-queues-logs-and-delivery-semantics/2-summary.md)).

### 2. 재기동한 노드의 시계가 0부터 다시 시작

- **현상**: 재시작한 서버가 만든 새 이벤트가 옛 이벤트보다 작은 값을 받는다. "옛 값"으로 취급되어 무시되거나 덮인다.
- **보이는 형태**: 재기동 직후 그 노드의 램포트 값이 작은 수에서 다시 시작한다. 1번의 진단 SQL에 행이 잡힌다.
- **원인**: 시계 값이 메모리에만 있었다.
- **대처**: 사건과 함께 시계 값을 저장하고 재기동 시 최댓값부터 시작한다. 주기적으로만 저장하면 "저장값 + 그 주기에 낼 수 있는 최대 증가분"부터 시작한다.

### 3. 벡터 시계 칸이 끝없이 늘어남

- **현상**: 메시지·레코드마다 붙는 메타데이터가 본문보다 커진다.
- **보이는 형태**: 오토스케일링·컨테이너 재생성마다 새 노드 id가 생겨 벡터 칸 수가 계속 는다. 직렬화 크기·GC 압력 증가.
- **원인**: 벡터 시계는 참여자마다 한 칸이다. 사라진 노드의 칸도 그 값을 기억하는 한 지울 수 없다.
- **대처**
  - 칸의 주인을 "요청을 처리한 서버"가 아니라 "복제본(레플리카)"으로 잡아 개수를 고정한다(버전 벡터).
  - Dynamo 논문은 (노드, 카운터) 쌍이 임계값(예: 10)에 닿으면 가장 오래된 쌍을 잘라 냈다. 논문 스스로 "후손 관계를 정확히 못 구할 수 있다"고 적는다(§4.4). 자르면 동시 판정이 틀릴 수 있음을 받아들인 선택이다.

### 4. 램포트 값 차이를 "나중에 쓴 것"으로 해석 → 동시 쓰기 유실

- **현상**: 두 사용자가 같은 항목을 거의 동시에 고쳤는데 한쪽 수정이 흔적 없이 사라진다.
- **보이는 형태**: 저장소가 "램포트 값이 큰 쪽이 이긴다"로 충돌을 푼다. 진 쪽 값은 로그에도 없다.
- **원인**: 램포트는 →의 한 방향만 보장한다. 동시 쓰기에도 값 차이가 생긴다(위 무작위 실험에서는 동시 쌍의 89.5%).
- **대처**: 동시를 감지해야 하면 벡터(버전 벡터)로 감지하고, 동시인 값은 형제로 보존하거나 CRDT로 합친다(24번).

### 5. 시계가 전파되지 않는 경계 → 인과 사슬 끊김

- **현상**: 분명히 "주문 → 배송"인데 둘이 동시로 판정된다.
- **보이는 형태**: 특정 경로(배치 재처리, 외부 웹훅, 사용자 화면을 거치는 흐름)의 메시지에만 시계 헤더가 없다.
- **원인**: 논리 시계는 메시지에 실려야만 전파된다. 4절의 숨은 채널과 같은 문제다.
- **대처**: 미들웨어로 모든 송수신 경로에 자동으로 싣고 받는다. 사람이 끼는 흐름은 응답에 시계 값을 돌려주고 다음 요청에 받는다.

## 핵심 문장

- 벽시계는 노드마다 어긋난다. 그 시각으로 정렬하면 원인과 결과가 뒤집혀도 에러가 나지 않는다.
- happens-before는 "정보가 흐를 수 있었나"로 정하는 부분 순서이고, 경로가 없는 두 사건은 동시다.
- 램포트 시계는 `a → b`이면 `C(a) < C(b)` 한 방향만 보장한다. 값이 다르다고 순서가 있는 것은 아니다.
- 벡터 시계는 `a → b` ⇔ `V(a) < V(b)`가 성립해 동시를 가려내지만, 참여자 수만큼 칸을 싣는다.
- 논리 시계는 시스템이 나르는 메시지만 본다. 사용자·외부 채널을 거친 인과는 토큰을 실어 보내거나 물리 시계로 보완한다.

## 관련 주제·근거

- 기초: [ops-patterns/14-logical-clock](../../ops-patterns/14-logical-clock/2-summary.md) — tick·receive·compare 구현과 테스트. 이 노트는 happens-before 정의, 숨은 채널, 장애·진단, 실험을 보탠다.
  - 참고: 원본 「한눈에」의 "실무 예: DynamoDB/Riak의 버전 벡터"는 같은 원본 앞부분의 설명(벡터를 쓰는 것은 Dynamo 논문·Riak이고 AWS DynamoDB 서비스는 아니다)과 어긋난다. 이 노트는 Dynamo 논문(DeCandia 외 2007)과 Riak 문서를 근거로 든다.
- 선행: [04-physical-clocks-and-ntp](../04-physical-clocks-and-ntp/2-summary.md) — 벽시계·단조 시계·NTP
- 후속
  - [13-distributed-id-generation](../13-distributed-id-generation/2-summary.md) — 시각을 앞에 둔 ID와 그 순서의 한계
  - [24-conflict-resolution-and-crdt](../24-conflict-resolution-and-crdt/2-summary.md) — 동시를 감지한 다음 합치는 법
  - [26-hybrid-clocks-and-truetime](../26-hybrid-clocks-and-truetime/2-summary.md) — HLC·TrueTime
  - [33-collaborative-editing-ot-and-sequence-crdt](../33-collaborative-editing-ot-and-sequence-crdt/2-summary.md) — 램포트 id로 글자를 정렬하는 시퀀스 CRDT
  - [12-coordination-and-fencing](../12-coordination-and-fencing/2-summary.md) — 단조 토큰(fencing token)
  - [database/17-occ-and-timestamp-ordering](../../database/17-occ-and-timestamp-ordering/2-summary.md) — 타임스탬프로 트랜잭션 순서를 정하는 동시성 제어
  - [database/55-distributed-databases](../../database/55-distributed-databases/2-summary.md) — 전역 타임스탬프(TSO·TrueTime·HLC)
- 논문
  - L. Lamport, "Time, Clocks, and the Ordering of Events in a Distributed System", CACM 21(7), 1978 — happens-before, Clock Condition, IR1·IR2, (값, 프로세스) 전순서, anomalous behavior·Strong Clock Condition <https://lamport.azurewebsites.net/pubs/time-clocks.pdf>
  - F. Mattern, "Virtual Time and Global States of Distributed Systems", 1989 — 길이 n 벡터 시계, 인과와 벡터 순서의 동형 <https://www.vs.inf.ethz.ch/publ/papers/VirtTimeGlobStates.pdf>
  - C. Fidge, "Timestamps in Message-Passing Systems That Preserve the Partial Ordering", 1988 — 같은 시기 독립 제안 (원문 미열람 [?])
  - G. DeCandia 외, "Dynamo: Amazon's Highly Available Key-value Store", SOSP 2007 §4.4 — 버전 벡터, 임계값 절단 <https://www.allthingsdistributed.com/files/amazon-dynamo-sosp2007.pdf>
- 문서: Riak KV "Causal Context" — vector clocks vs dotted version vectors, siblings <https://docs.riak.com/riak/kv/latest/learn/concepts/causal-context/index.html>
- 교재: DDIA 1판 5장 "Detecting Concurrent Writes"(happens-before, 버전 벡터), 9장 "Ordering Guarantees"(Lamport timestamps)
- 실험 목록
  - `Clocks.java` — 세 프로세스(P1 −80ms, P2 +30ms) 메시지 교환, 벽시계·램포트·벡터 정렬과 쌍 판단 + 무작위 200회×30사건 통계. eclipse-temurin 21 JDK 컨테이너, 2026-10-01.
