# distributed/06-replication-strategies — 복제 전략: 단일 리더·다중 리더·리더리스 — 정리 (힌트)

## 해결하는 문제

데이터가 한 곳에만 있으면 세 가지가 막힌다(DDIA 5장 서두의 복제 이유).
- 그 노드가 죽으면 데이터를 못 쓴다(가용성).
- 멀리 있는 사용자는 왕복 지연을 그대로 낸다(지연).
- 읽기가 한 노드의 처리량을 넘으면 늘릴 곳이 없다(읽기 확장).

같은 데이터를 여러 노드에 두면 된다. 복사 자체는 쉽다.\
어려운 것은 **바뀌는 데이터**다. 쓰기를 누가 받고, 그 변경을 다른 사본에 어떻게 퍼뜨리나. 답이 세 갈래다.

쉬운 예: 지점이 셋인 가게의 공동 장부.
- 본점 한 사람만 장부에 적고, 지점은 본점 장부를 베낀다 → **단일 리더**.
- 지점마다 적는 사람이 따로 있고, 밤에 서로 장부를 맞춘다 → **다중 리더**.
- 손님이 장부 세 권 중 아무 두 권에 직접 적고, 볼 때도 두 권을 펼쳐 최신 줄을 고른다 → **리더리스**.

똑같은 구조다. 누가 쓰기를 받느냐가 충돌·지연·장애 대응을 모두 정한다.

실무 예
- PostgreSQL·MySQL·Redis 기본 복제: 리더 하나가 쓰기를 받고 팔로워가 따라간다.
- 지역별 데이터센터가 각자 쓰기를 받는 구성, 오프라인에서도 고칠 수 있는 캘린더·메모 앱(기기마다 로컬 DB가 리더): 다중 리더.
- Amazon Dynamo 논문과 그 계열(Cassandra·Riak): 리더 없이 여러 복제본에 직접 쓴다.

## 동작·원리

### 1. 세 전략 한눈에

```text
 단일 리더                    다중 리더                         리더리스
 client ─write─▶ [L]          client ─▶ [L1]   [L2] ◀─ client    client ─write─▶ [A] [B] [C]
                  │ 복제 로그            ▲ └─비동기─┘ ▲                    (N개에 보내고 W개 확인)
            ┌─────┴─────┐               └─ 충돌 가능 ─┘          client ─read──▶ [A] [B] [C]
           [F1]        [F2]                                              (R개 응답 중 최신 버전)
 쓰기 순서 = 리더가 정한 하나     쓰기 순서 = 리더마다 따로          쓰기 순서 = 정해 주는 곳 없음
```

- *리더(leader)*: 쓰기를 받아 순서를 정하는 노드. primary·master라고도 부른다.
- *팔로워(follower)*: 리더의 변경을 받아 같은 순서로 적용하는 노드. replica·standby·secondary라고도 부른다.
- *복제 지연(replication lag)*: 리더에 반영된 쓰기가 팔로워에 반영되기까지의 시간 차.

### 2. 단일 리더 — 복제 로그를 같은 순서로 재생

```text
  리더:   w1  w2  w3  w4  w5      ← 리더가 정한 순서 = 복제 로그
           │   │   │   │   │
  팔로워:  w1  w2  w3  ·   ·      ← 같은 순서로 따라오는 중(지연 2개)
```

- 팔로워는 리더 로그를 **같은 순서로** 적용한다. 그래서 언젠가는 같은 상태가 된다.
- 복제 로그의 형태는 네 가지다(DDIA 5장 "Implementation of Replication Logs").
  - 문장 기반: SQL 문장을 그대로 보낸다. `RAND()`·`UUID()` 같은 비결정 함수가 복제본마다 다른 값을 낸다. (DDIA는 `NOW()`도 예로 들지만, MySQL 8.4는 `NOW()`를 문장 기반으로도 올바르게 복제한다고 적는다 — database/32.)
  - WAL 전송: 저장 엔진의 바이트 수준 로그를 보낸다. 엔진·버전에 묶인다.
  - 논리(행 기반) 로그: "어느 행이 어떻게 바뀌었나"를 보낸다. MySQL ROW binlog가 이쪽이다.
  - 트리거 기반: 앱 코드(트리거)가 변경을 다른 테이블에 남긴다.
- DB 제품에서의 구체적 모습(PostgreSQL WAL·MySQL binlog, 동기 수준, 페일오버)은 [database/32](../../database/32-replication-leader-follower/2-summary.md)에 있다. 이 노트는 그것을 전략 비교의 한 칸으로 본다.

**언제 성공이라고 답하나**가 동기/비동기를 가른다.

```text
  비동기: client ─SET─▶ L ─OK─▶ client        L ─(나중에)─▶ F
  동기:   client ─SET─▶ L ──▶ F ─ack─▶ L ─OK─▶ client
```

- 비동기면 리더가 OK한 쓰기가 팔로워에 아직 없을 수 있다. 리더가 그때 죽으면 그 쓰기는 사라진다.
- Redis는 기본이 비동기다. `WAIT numreplicas timeout`을 부르면 그 시점까지의 쓰기를 복제본 몇 개가 받았는지 확인할 수 있다. 문서는 `WAIT`가 Redis를 강한 일관성(CP) 시스템으로 바꾸지는 않으며, 페일오버 때 확인된 쓰기도 잃을 수 있다고 적는다(Redis replication 문서).

#### 실험: 리더에 쓰고 바로 팔로워에서 읽기 (Redis 7.4.9)

- 환경: 일회용 컨테이너 `redis:7-alpine`(7.4.9) 리더 1 + 복제본 1, 클라이언트는 `eclipse-temurin:21-jdk`의 Java 21. 같은 호스트의 Docker 네트워크.
- 같은 호스트라 복제가 너무 빨라 지연이 안 보였다. 그래서 복제 링크 사이에 **50ms 지연 프록시**(리더→복제본 방향 바이트를 50ms 늦게 전달하는 Java 프로그램)를 끼운 경우도 돌렸다. 원거리 데이터센터나 바쁜 팔로워를 흉내 낸 것이다.

```java
// RedisRepl.java 핵심 (최소 RESP 클라이언트 p=리더, f=팔로워)
for (int i = 0; i < n; i++) {
    p.cmd("SET", "w06:k", String.valueOf(i));          // 리더 OK
    Object v = f.cmd("GET", "w06:k");                  // 곧바로 팔로워에서 읽기
    if (!String.valueOf(i).equals(v)) stale++;
}
// [2]는 SET 뒤에 p.cmd("WAIT", "1", "100")를 넣고 같은 일을 한다
```

(실험, Redis 7.4.9 리더 1 + 복제본 1, 2026-10-01)

```text
== 직결(지연 프록시 없음) ==
[1] SET(리더) 직후 GET(팔로워): 300회 중 옛 값 0회 (0.0%)
[2] SET + WAIT 1 100 뒤 GET(팔로워): 300회 중 옛 값 0회, WAIT가 0을 돌려준 횟수 0
[3] SET 직후 GET(리더): 300회 중 옛 값 0회
== 복제 링크 50ms 지연 프록시 ==
[1] SET(리더) 직후 GET(팔로워): 300회 중 옛 값 300회 (100.0%)
[2] SET + WAIT 1 100 뒤 GET(팔로워): 300회 중 옛 값 0회, WAIT가 0을 돌려준 횟수 0
[3] SET 직후 GET(리더): 300회 중 옛 값 0회
```

- 관찰: 지연이 거의 없으면 문제가 안 보인다. 링크가 50ms 늦어지자 "쓰고 바로 팔로워에서 읽기"는 300번 모두 옛 값이었다.
- `WAIT 1 100`으로 복제본 1개의 수신을 확인한 뒤에는 0번이었다. 대가는 쓰기마다 그 확인을 기다리는 시간이다.
- 해석: 로컬 테스트에서 안 보이는 복제 지연 버그가 운영(원거리·부하)에서 나타나는 이유다.

#### 실험: 비동기 페일오버 — OK 받은 쓰기 1000건이 사라진다

- 같은 구성에서 프록시 지연을 3000ms로 늘렸다. 리더에 `SET` 1000건을 하나씩 보내 모두 OK를 받은 직후, 복제본을 `REPLICAOF NO ONE`으로 승격했다.

(실험, Redis 7.4.9, 복제 링크 3000ms 지연 프록시, 2026-10-01)

```text
role:slave
master_link_status:up
리더 OK 응답 수: 1000
OK
승격 직후 새 리더(옛 팔로워)의 w06:o:* 키 수: 0
옛 리더의 w06:o:* 키 수: 1000
새 리더에 있는 가장 큰 번호:
```

- 클라이언트는 1000건 모두 성공으로 알았다. 새 리더에는 한 건도 없다.
- 같은 실험을 지연 50ms로 먼저 돌렸을 때는 1000건이 모두 남았다. 마지막 `SET`과 승격 명령 사이(셸에서 `docker exec`를 다시 띄우는 시간)에 복제가 따라잡았다.
- 해석: 잃는 양은 "승격 순간의 복제 지연"에 달렸다. 평소 지연이 작다는 것은 잃지 않는다는 보장이 아니다.
- 실사례: GitHub 2018-10-21 사고(분석 글 2018-10-30). 미국 동부 허브와 동부 데이터센터 사이 연결이 43초 끊긴 동안 Orchestrator가 서부 데이터센터 쪽으로 MySQL 리더를 옮겼다. 동부에서 받았지만 서부로 복제되지 못한 쓰기가 남았다. 가장 바쁜 클러스터 하나에서 그런 쓰기가 954건이었다(원문 수치). GitHub은 binlog를 꺼내 자동으로 맞출 수 있는 쓰기와 사용자에게 연락해야 하는 쓰기를 가려내는 중이라고 적었다.

### 3. 다중 리더 — 각자 받고 나중에 맞춘다

```text
  t=0   L1(서울): cart = {a}         L2(도쿄): cart = {a}
  t=1   사용자X → L1: cart += b  → {a,b}   OK
  t=1   사용자Y → L2: cart += c  → {a,c}   OK
  t=31  복제 도착: L1 ← {a,c}, L2 ← {a,b}      ← 충돌! 둘 다 같은 키를 다르게 바꿨다
        LWW(타임스탬프 큰 쪽 승리)로 해소하면 → 둘 다 {a,c}  … b는 OK를 받았는데 사라졌다
```

- 쓰는 곳이 여럿이면 **같은 데이터를 동시에 다르게 바꾸는 충돌**이 생긴다. 단일 리더에는 없는 문제다.
- 쓰는 시점에는 충돌을 모른다. 각 리더는 로컬에서 OK를 준다. 충돌은 복제가 도착할 때 알게 된다.
- 쓰는 이유(DDIA 5장 "Use Cases for Multi-Leader Replication")
  - 여러 데이터센터: 쓰기도 가까운 데이터센터에서 받아 지연을 줄이고, 데이터센터 하나가 끊겨도 각자 계속 쓴다.
  - 오프라인 클라이언트: 기기마다 로컬 DB가 리더다. 다시 연결되면 맞춘다.
  - 실시간 공동 편집: 각자의 로컬 사본이 리더다(33번).
- 충돌을 다루는 방법
  - *충돌 회피*: 키마다 "홈 리더"를 하나 정해 그 키의 쓰기는 그 리더로만 보낸다. 그 키에 한해서는 단일 리더와 같다.
  - *수렴*: 모든 리더가 같은 규칙으로 같은 최종값에 도달하게 한다. 쓰기마다 ID·타임스탬프를 붙여 큰 쪽을 남기는 것이 *LWW(last write wins)*다. 간단하지만 진 쓰기는 **에러 없이 버려진다.**
  - *병합*: 값을 합친다(합집합, CRDT). 24번 주제.
  - *앱에 맡기기*: 충돌한 판을 모두 보관했다가 읽을 때 앱이 고르거나 합친다. Dynamo 논문의 장바구니 앱은 판들을 **합친다**(§4.4·§6).
- 복제 경로(토폴로지): 원형·별형·전체 연결. 원형·별형은 노드 하나가 죽으면 경로가 끊긴다. 전체 연결은 경로가 여러 개라 메시지가 **순서를 바꿔** 도착할 수 있다(DDIA 5장 "Multi-Leader Replication Topologies").

#### 실험(시뮬레이션): 다중 리더 LWW에서 조용히 사라지는 쓰기

- 환경: Java 21 단일 프로세스 이산 시뮬레이션. 리더 A·B, 복제 지연 30ms(예시), 10초 동안 평균 50ms마다 장바구니에 항목 하나 추가(읽고-추가-쓰기). 시드 고정이라 실행마다 같다.

```java
// MultiLeaderLww.java 핵심: 복제 메시지가 도착하면 충돌 해소
Ver merged = switch (policy) {
    case "LWW", "HOME" -> (in.ts() > mine.ts() || (in.ts() == mine.ts()
                           && in.leader().compareTo(mine.leader()) > 0)) ? in : mine;   // 큰 타임스탬프가 이김
    case "UNION" -> { Set<String> u = new TreeSet<>(mine.items()); u.addAll(in.items());
                      yield new Ver(u, Math.max(mine.ts(), in.ts()), mine.leader()); }   // 합집합
    default -> throw new IllegalStateException();
};
```

(실험, Java 21 시뮬레이션, 2026-10-01)

```text
LWW    B 시계    +0ms | OK 받은 추가 182 | 최종 A 154개, B 154개, A==B true | 조용히 사라짐 28
LWW    B 시계  -500ms | OK 받은 추가 182 | 최종 A 100개, B 100개, A==B true | 조용히 사라짐 82
UNION  B 시계    +0ms | OK 받은 추가 182 | 최종 A 182개, B 182개, A==B true | 조용히 사라짐 0
HOME   B 시계    +0ms | OK 받은 추가 178 | 최종 A 178개, B 178개, A==B true | 조용히 사라짐 0
```

- 관찰: LWW는 두 리더를 **같은 값으로 수렴**시켰다(`A==B true`). 그런데 OK를 받은 182건 중 28건이 사라졌다. 에러는 한 번도 없었다.
- B의 시계가 500ms 늦으면 82건이 사라졌다. B에서 나중에 쓴 값이 작은 타임스탬프 때문에 진다(시계 문제는 04·24번).
- 합집합 병합과 홈 리더(충돌 회피)는 0건이었다. HOME의 추가 수가 178로 다른 것은 리더 선택에 난수를 쓰지 않아 난수 흐름이 달라졌기 때문이다.
- "수렴했다"와 "아무것도 잃지 않았다"는 다른 말이다.

### 4. 리더리스 — 여러 곳에 쓰고 여러 곳에서 읽는다

```text
  쓰기 v2 (N=3, W=2)                         읽기 (R=2)
  client ─▶ A ✔ v2                           client ◀─ A: v2 ┐ 버전이 큰 v2를 고른다
         ─▶ B ✔ v2   → 2개 확인 = 성공           ◀─ C: v1 ┘
         ─▶ C ✘ (그 순간 장애) → v1 남음       읽은 김에 C에 v2를 써 준다 = 읽기 복구
```

- 쓰기를 순서 짓는 리더가 없다. 클라이언트(또는 대신 일하는 코디네이터 노드)가 N개 복제본에 보내고 W개 확인을 받으면 성공이다.
- 읽을 때도 R개에서 받아, 다른 판의 조상인(인과적으로 옛) 판은 버린다. 남은 판이 하나면 그것이 최신이다. 서로 동시인 판이 여럿 남으면 모두 돌려주고 병합에 맡긴다(Dynamo §4.4·§4.5).
- 노드 하나가 죽어도 R개·W개 응답을 채울 수 있으면 **페일오버 없이** 계속 쓰고 읽는다. 채울 수 없으면(예: N=3에서 W=3) 그 요청은 실패한다.
  - *버전*: 값마다 붙는 번호나 버전 벡터. "어느 쪽이 최신인가"를 판정하는 근거다(05·24번).
- 장애 중 쓰기를 놓친 복제본은 옛 값을 계속 들고 있다. 이것을 맞추는 길이 둘이다(DeCandia 외 2007 §5 읽기 복구·§4.7 anti-entropy, DDIA 5장).
  - *읽기 복구(read repair)*: 읽다가 옛 값을 돌려준 복제본을 발견하면 최신 값을 써 준다. **읽힌 키만** 고쳐진다.
  - *anti-entropy*: 백그라운드에서 복제본끼리 데이터를 비교해 맞춘다. Dynamo는 Merkle 트리로 비교량을 줄인다.
- R·W·N의 관계, sloppy quorum, hinted handoff는 [09-quorums](../09-quorums/2-summary.md)에서 판다.
- 아래 출력은 09번의 시뮬레이션 [B]다. 키 3000개를 W=1로 한 번씩 쓰고, 쓰기 메시지가 복제본마다 10% 확률로 유실되게 했다.

(실험, Java 21 시뮬레이션 N=3, 2026-10-01 — 09번과 같은 실행)

```text
[B] 복구 없음          1바퀴 옛 값  274/3000  2바퀴(R=1) 옛 값  283/3000
[B] 읽기 복구(R=2)     1바퀴 옛 값   34/3000  2바퀴(R=1) 옛 값  108/3000
[B] anti-entropy   1바퀴 옛 값  274/3000  2바퀴(R=1) 옛 값    0/3000
```

- 복구 장치가 없으면 두 번째 바퀴에도 옛 값 비율이 그대로다(274 → 283, 무작위 복제본 선택 차이). 시간이 지나도 저절로 낫지 않는다.
- 읽기 복구는 읽힌 복제본 두 곳만 고친다. 세 번째 복제본이 옛 값이면 다음 R=1 읽기에서 다시 걸린다(108).

### 5. 세 전략 비교

| | 단일 리더 | 다중 리더 | 리더리스 |
|---|---|---|---|
| 쓰기를 받는 곳 | 리더 하나 | 리더 여럿 | 아무 복제본(N개에 보내 W개 확인) |
| 쓰기 충돌 | 없음(리더가 순서를 정함) | 있음 — 해소 규칙 필요 | 있음 — 버전 비교·해소 필요 |
| 리더 장애 | 페일오버 필요, 비동기면 유실 가능 | 다른 리더가 계속 받음 | 페일오버 개념 없음 |
| 놓친 쓰기 메우기 | 로그를 순서대로 따라잡음 | 리더 간 복제 로그 | 읽기 복구·anti-entropy·hinted handoff |
| 예 | PostgreSQL·MySQL·Redis 복제 | 다중 데이터센터 구성, 오프라인 앱 | Dynamo 논문, Cassandra |

## 쓰이는 자료구조·알고리즘

- **복제 로그** — 추가 전용 로그 + "어디까지 적용했나" 위치(오프셋). 단일 리더 복제는 로그를 같은 순서로 재생하는 것이다. 지연 = 위치의 차이(Redis `master_repl_offset` vs 복제본 `slave_repl_offset`). [database/19-wal-and-logging](../../database/19-wal-and-logging/2-summary.md), [database/32](../../database/32-replication-leader-follower/2-summary.md)
- **상태 기계 복제** — 같은 초기 상태 + 같은 순서의 결정적 연산 = 같은 결과. 문장 기반 로그에서 비결정 함수가 위험한 이유다.
- **버전 번호·버전 벡터** — 리더리스·다중 리더에서 "최신"과 "동시"를 가린다. [05-logical-clocks](../05-logical-clocks/2-summary.md), [24-conflict-resolution-and-crdt](../24-conflict-resolution-and-crdt/2-summary.md)
- **Merkle 트리** — anti-entropy에서 다른 구간만 찾아낸다. [data-structure/27-merkle-tree](../../data-structure/27-merkle-tree/2-summary.md)
- **일관 해싱** — 리더리스에서 키를 어느 N개 노드에 둘지 정한다(Dynamo의 링, preference list). [data-structure/31-consistent-hashing](../../data-structure/31-consistent-hashing/2-summary.md)

## 적용 — 풀어나가는 법

### 1. 고르는 순서

1. 기본은 **단일 리더**다. 충돌이 없어 앱 코드가 가장 단순하다. 읽기 확장은 팔로워로, 쓰기 확장은 샤딩([database/33](../../database/33-partitioning-and-sharding/2-summary.md))으로 푼다.
2. 지역마다 쓰기 지연을 줄여야 하거나 오프라인 쓰기가 필요하면 **다중 리더**를 검토한다. 이때 먼저 "충돌을 어떻게 해소할지"를 데이터 종류마다 적는다. 적을 수 없으면 홈 리더로 충돌을 피한다.
3. 노드 장애에도 쓰기를 계속 받아야 하고, 값이 갈라져도 합칠 규칙(LWW로 충분한 데이터, 합집합, CRDT)이 있으면 **리더리스**를 검토한다.

### 2. 단일 리더 — 지연을 재고 read-your-writes를 지킨다

```bash
# Redis 7.4: 리더와 복제본의 복제 위치 차이
redis-cli -h <leader> INFO replication | grep -E 'master_repl_offset|slave0'
redis-cli -h <replica> INFO replication | grep -E 'master_link_status|slave_repl_offset'
```

```java
// 쓰기 직후의 내 읽기만 리더로 보내는 라우팅 (예시)
public String saveProfile(String userId, String json) {
    leader.set("profile:" + userId, json);
    int all = replicas.size();
    long acked = leader.waitReplicas(all, 100);       // Redis WAIT <복제본 수> 100
    if (acked < all) recentWriter.put(userId, System.currentTimeMillis() + 5_000);   // 5초 동안 리더에서 읽기(예시 값)
    return json;
}
public String loadProfile(String userId) {
    Long until = recentWriter.get(userId);
    var node = (until != null && until > System.currentTimeMillis()) ? leader : replicas.pick();
    return node.get("profile:" + userId);
}
```

- `WAIT`는 복제본 **몇 개**가 받았는지만 돌려준다. 그래서 위 코드는 모든 복제본이 받았을 때만 아무 복제본에서 읽는다. 일부만 받았는데 `replicas.pick()`으로 읽으면 못 받은 복제본에 갈 수 있다.
- 5초는 예시 값일 뿐 그 뒤 복제본이 따라잡았다는 보장은 없다. 더 정확하게 하려면 복제본의 복제 위치(`slave_repl_offset`)가 내 쓰기 위치를 넘었는지 확인하고 읽는다.
- `WAIT`가 1을 돌려줘도 그 복제본이 **나중에** 리더로 승격된다는 보장은 없다. 문서는 `WAIT`가 유실 확률을 크게 줄이지만, Sentinel·Cluster의 승격은 최선 노력이라 `WAIT`로 복제를 확인한 쓰기도 잃을 수 있다고 적는다(Redis `WAIT` 명령 문서, replication 문서). 유실을 없애는 장치로 믿지 않는다.
- 쓰기 거부로 유실 창을 줄이려면 Redis `min-replicas-to-write`·`min-replicas-max-lag`(08번 실험)를 쓴다. 이것은 "최근 M초 안에 응답한 복제본이 N개 이상일 때만 쓰기를 받는" 조건이다. 이번 쓰기가 복제본에 도착할 때까지 기다리지는 않는다(Redis replication 문서 "Allow writes only with N attached replicas").

### 3. 다중 리더 — 홈 리더로 충돌을 피한다

```java
// 사용자마다 홈 리전을 고정: 그 사용자 데이터의 쓰기는 홈 리전 리더로만
String homeRegion(String userId) {
    return regions.get(Math.floorMod(userId.hashCode(), regions.size()));   // 보통은 가입 리전을 저장해 둔다
}
void updateCart(String userId, CartChange c) {
    leaderOf(homeRegion(userId)).apply(userId, c);   // 다른 리전은 비동기로 받기만 한다
}
```

- 홈 리전이 통째로 죽으면 홈을 바꿔야 한다. 그 순간에는 두 리전이 같은 사용자 쓰기를 받을 수 있다. 바꾸는 절차에 펜싱이 필요하다(12번).

### 4. 리더리스 — 정족수와 복구를 운영한다

- Cassandra 5.0: 쓰기는 일관성 수준과 상관없이 **모든 복제본에 보내고**, 일관성 수준은 몇 개의 응답을 기다릴지만 정한다(Cassandra 5.0 문서 "Dynamo" 절).
- 놓친 쓰기는 hinted handoff·읽기 복구가 최선 노력으로 메우고, 보장은 `nodetool repair`(Merkle 트리 비교)가 맡는다. 문서는 기본 gc grace 10일이면 적어도 7일마다 모든 노드를 repair하라고 권한다. 이보다 늦으면 지운 데이터가 되살아날 수 있다(Cassandra 5.0 "Repair").

## 장애 시나리오와 대처

### 1. 다중 리더 쓰기 충돌 → 조용한 덮어쓰기

- **현상**: 장바구니에 넣은 상품, 저장한 설정이 나중에 없다. 사용자는 분명 "저장됨"을 봤다.
- **보이는 형태**: 에러·예외가 없다. 리더들은 같은 값으로 수렴해 있어 대조 쿼리로도 불일치가 안 보인다. 감사 로그(쓰기 요청 기록)와 최종 상태를 비교해야 드러난다.
- **원인**: 두 리더가 같은 키를 동시에 고쳤고, LWW가 한쪽을 버렸다. 시계가 늦은 리더의 쓰기는 더 자주 진다(시뮬레이션에서 28건 → 82건).
- **대처**
  - 키마다 홈 리더를 정해 충돌 자체를 피한다.
  - 버려도 되는 데이터에만 LWW를 쓴다. 합칠 수 있는 데이터는 병합(합집합·CRDT)으로 바꾼다.
  - 충돌을 감지해 두 판을 다 남기고 앱이 고르거나 합치게 한다(버전 벡터).

### 2. 리더리스 읽기 복구 누락 → 오래된 값

- **현상**: 같은 키를 읽을 때마다 새 값과 옛 값이 번갈아 나온다. 잘 안 읽히는 키는 몇 주째 옛 값이다.
- **보이는 형태**: R+W≤N인 읽기에서 재현된다(예: N=3에서 R=1, 또는 W=1일 때 R=2 — 시뮬레이션 1바퀴 R=2에서도 34/3000). Cassandra라면 repair를 오래 안 돈 테이블, 노드 교체 뒤 데이터.
- **원인**: 장애 중 쓰기를 놓친 복제본을 아무도 고치지 않았다. 읽기 복구는 읽힌 키·읽힌 복제본만 고친다. 힌트는 보관 기간이 있다(Cassandra 5.0 `max_hint_window` 기본 3시간).
- **대처**: 정기 anti-entropy(Cassandra `nodetool repair`)를 돌린다. 중요한 읽기는 R+W>N이 되게 한다(09번). 시뮬레이션에서 anti-entropy 한 번 뒤 옛 값 0/3000.

### 3. 비동기 페일오버 → 확인된 쓰기 유실

- **현상**: 페일오버 뒤 "성공" 응답을 받은 주문·메시지가 없다.
- **보이는 형태**: 새 리더의 마지막 위치(오프셋·LSN·GTID)가 옛 리더보다 뒤다. 옛 리더가 돌아오면 새 리더에 없는 쓰기를 갖고 있다.
- **원인**: 비동기 복제에서 리더가 OK한 쓰기가 팔로워에 닿기 전에 승격했다. 실험에서 1000건이 모두 사라졌다.
- **대처**: 동기·준동기 복제, Kafka `acks=all`+`min.insync.replicas`, Redis `WAIT`(이번 쓰기의 복제 확인)나 `min-replicas-to-write`(최근 응답한 복제본이 모자라면 쓰기 거부)로 창을 줄인다. 승격 후보는 가장 앞선 팔로워로 고른다. 옛 리더에만 있던 쓰기는 GitHub 2018처럼 로그(binlog)를 꺼내 대조한다.

### 4. 복제 지연 → 방금 쓴 것이 안 보인다

- **현상**: 글을 저장하고 목록으로 왔는데 없다. 새로고침하면 생긴다.
- **보이는 형태**: 팔로워 읽기에서만 생긴다. 지연 지표(Redis 오프셋 차이, PostgreSQL `replay_lag`)가 오를 때 늘어난다.
- **원인**: 쓰기는 리더, 읽기는 아직 따라오지 못한 팔로워로 갔다. 실험에서 지연 50ms면 300번 중 300번.
- **대처**: 쓰기 직후의 내 읽기는 리더로 보낸다. 또는 `WAIT`·복제 위치를 확인한 뒤 팔로워에서 읽는다. 세션 보장의 종류는 07번.

## 핵심 문장

- 복제 전략은 "누가 쓰기를 받나"로 갈린다. 단일 리더는 순서를 하나로 정해 충돌이 없고, 다중 리더와 리더리스는 충돌 해소를 떠안는다.
- 비동기 복제에서 리더의 OK는 "리더에 있다"는 뜻이다. 승격 순간의 지연만큼 확인된 쓰기를 잃는다.
- LWW는 복제본을 같은 값으로 수렴시키지만, 진 쓰기를 에러 없이 버린다. 수렴과 무손실은 다른 말이다.
- 리더리스에서 놓친 쓰기는 저절로 낫지 않는다. 읽기 복구는 읽힌 것만, anti-entropy는 전체를 맞춘다.
- 로컬에서 안 보이는 복제 지연 문제는 지연을 인위로 넣어야 재현된다.

## 관련 주제·근거

- 선행
  - [database/32-replication-leader-follower](../../database/32-replication-leader-follower/2-summary.md) — 단일 리더 복제의 DB 구현(WAL·binlog, 동기 수준, 지연 측정, 페일오버)
- 후속·연결
  - [07-consistency-models](../07-consistency-models/2-summary.md) — 복제 지연이 깨는 보장의 이름(선형화, 세션 보장)
  - [08-cap-and-pacelc](../08-cap-and-pacelc/2-summary.md) — 분할 시 쓰기를 받을까 거부할까
  - [09-quorums](../09-quorums/2-summary.md) — 리더리스의 R·W·N, sloppy quorum, hinted handoff
  - [24-conflict-resolution-and-crdt](../24-conflict-resolution-and-crdt/2-summary.md) — LWW·버전 벡터·CRDT
  - [27-chain-replication-and-striping](../27-chain-replication-and-striping/2-summary.md) — 또 다른 강한 복제 방식
  - [10-leader-election](../10-leader-election/2-summary.md) · [11-consensus-raft](../11-consensus-raft/2-summary.md) · [12-coordination-and-fencing](../12-coordination-and-fencing/2-summary.md) — 승격과 펜싱 · [33-collaborative-editing-ot-and-sequence-crdt](../33-collaborative-editing-ot-and-sequence-crdt/2-summary.md) — 다중 리더로서의 공동 편집
  - [database/33-partitioning-and-sharding](../../database/33-partitioning-and-sharding/2-summary.md) · [database/55-distributed-databases](../../database/55-distributed-databases/2-summary.md)
- 교재·논문
  - DDIA 1판 5장 Replication — Leaders and Followers, Implementation of Replication Logs, Problems with Replication Lag, Multi-Leader Replication(Use Cases, Handling Write Conflicts, Topologies), Leaderless Replication(Read repair and anti-entropy)
  - DeCandia 외, "Dynamo: Amazon's Highly Available Key-value Store", SOSP 2007 — §4.4 벡터 시계(장바구니), §4.5 R·W, §4.6 hinted handoff, §4.7 Merkle 트리 anti-entropy, §5 읽기 복구, §6 장바구니 병합(비즈니스 로직 조정)·LWW를 쓰는 세션 서비스 <https://www.allthingsdistributed.com/files/amazon-dynamo-sosp2007.pdf>
- 제품 문서
  - Redis replication — 기본 비동기, `WAIT`는 CP로 바꾸지 않음, `min-replicas-to-write` <https://redis.io/docs/latest/operate/oss_and_stack/management/replication/> · `WAIT` 명령 — 승격은 최선 노력, 확인된 쓰기도 유실 가능 <https://redis.io/docs/latest/commands/wait/>
  - Apache Cassandra 5.0 — Dynamo(쓰기는 모든 복제본에, 일관성 수준, LWW), Hints(`max_hint_window` 3시간), Repair(Merkle 트리, gc grace 10일·7일 주기 권장) <https://cassandra.apache.org/doc/5.0/cassandra/architecture/dynamo.html>
- 사고 보고서
  - GitHub, "October 21 post-incident analysis"(2018-10-30) — 43초 연결 끊김, Orchestrator의 서부 승격, 복제 안 된 쓰기(바쁜 클러스터 하나에 954건) <https://github.blog/news-insights/company-news/oct21-post-incident-analysis/>
- 실험 목록
  - Redis 7.4.9 리더 1 + 복제본 1(일회용 컨테이너, Java 21 RESP 클라이언트): 직결 vs 복제 링크 50ms 지연 프록시에서 쓰고 바로 팔로워 읽기, `WAIT 1 100` 뒤 읽기
  - 같은 구성, 3000ms 지연 프록시: OK 받은 `SET` 1000건 직후 `REPLICAOF NO ONE` 승격 → 새 리더 0건
  - Java 21 시뮬레이션: 다중 리더 2개 LWW·시계 −500ms·합집합·홈 리더별 사라진 쓰기 수
  - Java 21 시뮬레이션(09번과 공유): 쓰기 유실 10%에서 복구 없음·읽기 복구·anti-entropy별 옛 값 수
