# math/04-graph-theory-basics — 그래프·트리·DAG·연결성·사이클의 정의와 성질 — 정리 (힌트)

## 해결하는 문제

"A가 B를 쓴다", "B가 끝나야 C를 돌린다" 같은 관계는 코드 곳곳에 숨어 있다. 빈 의존성 주입 컨테이너, 빌드 도구, DB 마이그레이션, 락 대기가 다 그렇다.

```text
  관계를 글로 적으면                       그림으로 그리면
  "orders 테이블은 users를 참조한다"        users ──> orders ──> order_items ──> report_view
  "report_view는 order_items를 읽는다"                 ^                               │
  "orders 마이그레이션이 report_view를 쓴다"            └───────────────────────────────┘
                                                      한 바퀴 도는 길 = 순서를 정할 수 없다
```

- 글로는 "꼬였다"는 느낌만 든다. 그래프로 그리면 **사이클**이라는 이름이 붙고, 찾는 알고리즘과 고치는 방법이 따라온다.
- 많은 코드가 "이 관계에는 사이클이 없다(DAG)"를 말없이 가정한다. 재귀로 의존을 풀어 가는 코드가 대표적이다. 가정이 깨지면 `StackOverflowError`나 무한 대기로 나타난다.

쉬운 예: 대학 선수과목이다.
- "자료구조를 들으려면 프로그래밍 입문을 먼저 들어야 한다"를 화살표로 그린다.
- 화살표를 따라 한 바퀴 돌아오는 과목 묶음이 있으면, 그 묶음은 아무도 졸업 계획에 넣을 수 없다.

똑같은 구조다.\
과목 = 정점, "먼저 들어야 한다" = 방향 간선, 졸업 계획 = 위상 순서다.

실무 예:
- Spring Boot 2.6부터 빈 사이의 순환 참조가 기본 금지라, 순환이 있으면 기동 시 `BeanCurrentlyInCreationException`으로 실패한다(Spring Boot 2.6 Release Notes "Circular References Prohibited by Default").
- 마이그레이션·빌드 태스크 의존에 사이클이 생기면 순서를 정하는 도구가 멈추거나 오류를 낸다.
- DB 락 대기 관계에 사이클이 생기면 교착(deadlock)이다([os/19-deadlock](../../os/19-deadlock/2-summary.md), [database/15](../../database/15-two-phase-locking-and-deadlock/2-summary.md)).

## 동작·원리

### 1. 용어 — 정점, 간선, 차수, 길

```text
  무방향 그래프                       방향 그래프(digraph)
     a ─── b                            a ──> b
     │   ╱ │                            │     │
     │  ╱  │                            v     v
     c ─── d                            c ──> d
  deg(b) = 3 (a, c, d)               outdeg(a) = 2, indeg(d) = 2
```

- *그래프 G = (V, E)*: 정점 집합 V와 간선 집합 E. 간선은 정점 두 개를 잇는다.
  - *무방향 그래프(simple graph)*: 간선에 방향이 없다. MCS 12장은 자기 자신으로 가는 간선과 겹친 간선이 없는 단순 그래프를 다룬다.
  - *방향 그래프(digraph)*: 간선 u → v에 방향이 있다. u를 꼬리(tail), v를 머리(head)라 한다(MCS 10.1).
- *차수 deg(v)*: v에 붙은 간선 수. 방향 그래프는 들어오는 수(*indeg*)와 나가는 수(*outdeg*)를 따로 센다.
- *걷기(walk)*: 간선을 따라 정점을 이어 간 열. 정점이 겹쳐도 된다(MCS 10.2).
  - *경로(path)*: 정점이 겹치지 않는 걷기.
  - *사이클(cycle)*: 출발 정점으로 돌아오는 걷기(시작=끝 말고는 정점이 겹치지 않음).
    - 흔한 오해: "이미 방문한 정점을 또 만나면 사이클이다." 방향 그래프의 다이아몬드(a→b, a→c, b→d, c→d)는 d를 두 번 만나지만 사이클이 없다. 자세히는 [algorithm/12-dfs](../../algorithm/12-dfs/2-summary.md) 사이클 탐지 절.

### 2. 핸드셰이크 보조정리 — 차수의 합은 간선 수의 두 배

```text
  간선 하나 = 양 끝에 차수 1씩, 합 2
     a ─── b      deg(a) += 1, deg(b) += 1

  Σ deg(v) = 2·|E|            (무방향, MCS Lemma 12.2.1)
  Σ indeg(v) = Σ outdeg(v) = |E|   (방향, MCS Lemma 10.1.2)
```

- 기호
  - *Σ deg(v)*: 모든 정점의 차수를 더한 값.
  - *|E|*: 간선 개수.
- 따름 성질: 차수가 홀수인 정점의 개수는 짝수다. 합이 짝수(2|E|)이기 때문이다.
- 실무 쓰임: 인접 리스트의 메모리 어림. 무방향 그래프를 인접 리스트로 두면 이웃 항목이 정확히 2|E|개다. 방향 그래프면 |E|개다.

### 3. 연결성 — 무방향의 연결 요소, 방향의 강연결 요소

```text
  무방향: 연결 요소 2개                 방향: 강연결 요소(SCC)를 점 하나로 줄이면 DAG
   a─b   d─e                             ┌────────┐       ┌───┐
   │ │                                   │ a ⇄ b  │ ────> │ c │
   c─┘                                   └────────┘       └───┘
                                          SCC 1            SCC 2   (줄인 그래프에는 사이클이 없다)
```

- *연결(connected)*: 두 정점 사이에 경로가 있다. 연결 관계로 나뉜 덩어리가 *연결 요소*다(MCS 12.8).
  - 연결 관계는 반사·대칭·추이를 만족하는 동치관계다. 그래서 정점이 겹치지 않는 덩어리로 나뉜다([03-sets-relations-orders](../03-sets-relations-orders/2-summary.md)의 동치류).
- *강연결(strongly connected)*: 방향 그래프에서 u → v와 v → u 경로가 둘 다 있다. 이 관계의 동치류가 *강연결 요소(SCC)*다.
- 각 SCC를 점 하나로 줄인 그래프(응축 그래프)에는 사이클이 없다(CLRS 3판 22.5 — 보조정리 번호는 확인 못 함 `[?]`). 그래서 "사이클이 있는 의존 그래프"도 SCC로 묶으면 그 위에서 순서를 정할 수 있다. 알고리즘은 [algorithm/18-scc](../../algorithm/18-scc/2-summary.md).

### 4. 트리 — 사이클 없이 연결된 그래프

```text
  정점 5, 간선 4                 간선 하나를 더하면           간선 하나를 빼면
       a                             a                           a
      / \                           / \                         / \
     b   c                         b───c   ← 사이클             b   c
    / \                           / \                          /
   d   e                         d   e                        d    e  ← 떨어짐(연결 끊김)
```

- *트리(tree)*: 연결되어 있고 사이클이 없는 무방향 그래프. *숲(forest)*: 사이클이 없는 그래프(연결 요소마다 트리).
- 같은 것을 가리키는 네 가지 조건(MCS Theorem 12.11.4, 단순 그래프)
  1. 연결 + 사이클 없음.
  2. 연결 + 어느 간선을 빼도 연결이 끊김(간선이 최소).
  3. 사이클 없음 + 이웃이 아닌 두 정점 사이에 간선을 더하면 사이클이 생김(간선이 최대).
  4. 두 정점 사이의 경로가 정확히 하나.
- 유한 그래프에서는 간선 수로도 판정한다(MCS Theorem 12.11.6): 유한 트리 ⇔ 연결 + |V| = |E| + 1.
  - 증명 아이디어: 정점이 둘 이상인 유한 트리에는 차수 1인 잎이 둘 이상 있다(MCS Lemma 12.11.3). 잎과 그 간선을 하나씩 떼어 내며 귀납한다.
- 실무 쓰임: "n개 노드를 연결하는 데 간선이 n − 1개면 충분하고, 그보다 많으면 사이클이 생긴다". 무방향 그래프에서 간선을 하나씩 넣으며 union-find로 "이미 같은 덩어리인가"를 보면 사이클을 만드는 간선을 바로 찾는다([data-structure/14-union-find](../../data-structure/14-union-find/2-summary.md)).

### 5. DAG와 위상 순서 — "순서를 정할 수 있다"의 수학

```text
  DAG                                    위상 순서(가능한 것 중 하나)
  V1 ──> V2 ──> V4 ──> V5                 V1, V2, V3, V4, V5
   └──> V3 ──┘                            (모든 화살표가 왼쪽 → 오른쪽)

  사이클이 있으면                          V2 ──> V4 ──> V5 ──> V2
  "V2는 V5보다 앞, V5는 V2보다 앞"         → 한 줄에 놓을 방법이 없다
```

- *DAG(directed acyclic graph)*: 사이클이 없는 방향 그래프(MCS Definition 10.5.1).
- *위상 순서(topological sort)*: 모든 간선 u → v에 대해 u가 v보다 앞에 오는 정점의 나열(MCS Definition 10.5.2).
- 정리: **유한 DAG에는 위상 순서가 있다**(MCS Theorem 10.5.4). 역으로 사이클이 있으면 위상 순서가 없다. 사이클 위의 정점들은 서로가 서로보다 앞이어야 하기 때문이다.
  - 증명 아이디어: 유한 DAG에는 들어오는 간선이 없는 정점(MCS의 *minimal*)이 있다. 그것을 맨 앞에 놓고 지운다. 남은 그래프도 DAG이므로 반복한다. 이것이 그대로 Kahn 알고리즘(Kahn 1962)이다.
- 병렬 실행: 모든 태스크의 실행 시간이 같고(MCS 10.5.2의 가정) 프로세서가 무제한이면 전체 완료 단계 수 = 가장 긴 사슬(critical path)의 정점 수다(MCS Corollary 10.5.9). 실행 시간이 다르면 실행 시간 합이 가장 큰 경로가 완료 시간을 정한다. 깊이가 같은 정점끼리 같은 단계에 돌린다(Theorem 10.5.8). 빌드 서버에 코어를 아무리 붙여도 가장 긴 의존 사슬보다 빨라지지 않는 이유다.

### 6. 사이클 탐지 — 두 가지 판정

```text
  Kahn(진입 차수 0부터 꺼내기)               DFS 3색
  꺼낸 수 = |V|  → DAG                        WHITE(안 봄) → GRAY(경로 위) → BLACK(끝남)
  꺼낸 수 < |V|  → 사이클이 있다               GRAY를 다시 만나면(역방향 간선) 사이클
  (남은 정점 = 사이클 + 사이클 뒤에 매달린 정점)  경로를 되짚어 사이클 자체를 보고할 수 있다
```

- DFS에서 *역방향 간선(back edge)*: 아직 끝나지 않은 조상(GRAY)으로 가는 간선. 방향 그래프는 DFS에 역방향 간선이 없을 때만 DAG다(CLRS 22.3, Lemma 22.11 — 2판 본문 발췌와 3판 기반 강의 페이지로 확인).
- Kahn은 "사이클이 있다"는 알지만 어느 것인지는 바로 말하지 않는다. 남은 정점에는 사이클에 매달린 정점도 섞인다. 사이클 경로까지 보고하려면 3색 DFS를 쓴다([data-structure/34-dependency-resolver](../../data-structure/34-dependency-resolver/2-summary.md) 장애 4).

### 실험: 차수 합, 트리 간선 수, 위상정렬·사이클, 방문 표시 없는 재귀

`Graph04.java` 핵심(전체는 scratchpad `math/04/Graph04.java`):

```java
// 방문 표시 없는 재귀 해석: "내 단계 = 1 + 선행들의 최대 단계" — DAG라고 믿는 코드
static int naiveLevel(String v) {
    calls++;
    int best = 0;
    for (String p : rev.getOrDefault(v, List.of())) best = Math.max(best, naiveLevel(p) + 1);
    return best;
}
// Kahn: 진입 차수 0부터 꺼낸다. order.size() < 정점 수면 사이클
while (!ready.isEmpty()) {
    String u = ready.poll(); order.add(u);
    for (String v : g.get(u)) if (indeg.merge(v, -1, Integer::sum) == 0) ready.add(v);
}
```

- 무작위 그래프(V=1000, E=5000, `new Random(42)`)로 차수 합을 세고, 무작위 트리(정점 i를 0..i−1 중 하나에 붙임)에 간선 하나를 더해 union-find로 사이클을 확인했다.
- 마이그레이션 5개 DAG에서 위상정렬 → `V5 → V2` 간선 추가 → Kahn·3색 DFS·재귀 해석을 다시 돌렸다.

(실험, OpenJDK 21.0.12 Temurin, `eclipse-temurin:21-jdk` 컨테이너 `--network none --cpus=2`, 2026-10-07, 두 번 실행)

```text
handshake: V=1000 E=5000 sum(deg)=10000 2E=10000 oddDegreeVertices=502 (even? true)
tree: V=1000 E=999 (V-1=999) extra edge 64-486 closes a cycle? true
DAG kahn order: [V1__users, V2__orders, V3__payments, V4__order_items, V5__report_view] (5/5)
DAG cycle: null
cyclic kahn order: [V1__users, V3__payments] (2/5) stuck=[V2__orders, V4__order_items, V5__report_view]
cyclic 3-color cycle: [V2__orders, V4__order_items, V5__report_view, V2__orders]
naive recursive resolve: java.lang.StackOverflowError after calls=10990
```

- 관찰
  - 차수 합 = 2|E| = 10000, 홀수 차수 정점 502개(짝수)로 보조정리 그대로다.
  - 트리는 간선 999 = V − 1이고, 간선 하나를 더하자 사이클이 생겼다.
  - 사이클이 생기자 Kahn은 5개 중 2개만 꺼내고 멈췄다. 3색 DFS는 사이클 `V2 → V4 → V5 → V2`를 짚었다.
  - 방문 표시 없는 재귀는 `StackOverflowError`로 끝났다. 터지기까지의 호출 수는 세 번 실행(사실 점검 재실행 포함)에서 10,990·11,037·11,045로 달랐다. JIT 컴파일 시점에 따라 프레임 크기가 달라지기 때문이다(해석, 근거는 [algorithm/03-recursion](../../algorithm/03-recursion/2-summary.md)의 깊이 실험).

## 쓰이는 자료구조·알고리즘

- **인접 리스트·인접 행렬** — 그래프를 메모리에 두는 두 방식. 인접 리스트는 2|E|(무방향) 항목, 행렬은 |V|² 칸. [data-structure/08-graph](../../data-structure/08-graph/2-summary.md)
- **위상정렬(Kahn·DFS 후위 역순)과 3색 사이클 탐지** — [data-structure/34-dependency-resolver](../../data-structure/34-dependency-resolver/2-summary.md), [algorithm/12-dfs](../../algorithm/12-dfs/2-summary.md), [algorithm/11-bfs](../../algorithm/11-bfs/2-summary.md)(Kahn은 큐 기반)
- **union-find** — 무방향 그래프에서 사이클을 만드는 간선 찾기, 연결 요소 관리. [data-structure/14-union-find](../../data-structure/14-union-find/2-summary.md)
- **SCC(Tarjan·Kosaraju)** — 사이클 덩어리를 점 하나로 줄여 DAG로 만든다. [algorithm/18-scc](../../algorithm/18-scc/2-summary.md)
- **대기 그래프(wait-for graph)** — 교착 탐지 = 사이클 탐지. [os/19-deadlock](../../os/19-deadlock/2-summary.md)
- **최소 신장 트리** — 연결 그래프에서 간선 n − 1개짜리 트리를 고른다. [algorithm/17-mst](../../algorithm/17-mst/2-summary.md)

## 적용 — 풀어나가는 법

### 1. 증상 → 그래프로 옮긴다

- 증상: 기동 실패, `StackOverflowError`, 순서 정하는 도구가 멈춤, 교착.
- 먼저 정점과 간선 방향을 정한다. 이 노트는 "u → v = u가 먼저"로 쓴다. 방향을 거꾸로 넣으면 순서가 정확히 뒤집히는데 사이클 검사는 통과한다(뒤집어도 사이클은 사이클). 자세히는 [data-structure/34](../../data-structure/34-dependency-resolver/2-summary.md) 장애 1.

### 2. 수식으로 어림한다

- DAG인가? → Kahn으로 꺼낸 수가 |V|인지 본다.
- 몇 단계로 병렬화되나? → 가장 긴 사슬의 길이(MCS Corollary 10.5.9).
- 메모리는? → 인접 리스트 항목 수 = |E|(방향) 또는 2|E|(무방향).
- 무방향 연결 그래프인데 간선이 |V| − 1보다 많은가? → 사이클이 하나 이상 있다(MCS Theorem 12.11.6의 대우).

### 3. 코드로 확인한다 — 재귀 해석에 사이클 방어선

```java
// Java 21: DAG를 가정한 재귀 해석에 GRAY 표시를 붙여, 사이클이면 경로와 함께 실패한다
enum Mark { GRAY, BLACK }
static int level(String v, Map<String, List<String>> deps, Map<String, Mark> mark,
                 Map<String, Integer> memo, Deque<String> path) {
    if (mark.get(v) == Mark.BLACK) return memo.get(v);
    if (mark.get(v) == Mark.GRAY) {
        throw new IllegalStateException("dependency cycle: " + path + " -> " + v);
    }
    mark.put(v, Mark.GRAY); path.addLast(v);
    int best = 0;
    for (String d : deps.getOrDefault(v, List.of())) best = Math.max(best, level(d, deps, mark, memo, path) + 1);
    path.removeLast(); mark.put(v, Mark.BLACK); memo.put(v, best);
    return best;
}
```

- GRAY 표시 하나로 `StackOverflowError`(원인 불명)가 `dependency cycle: [...]`(원인 명시)로 바뀐다.
- BLACK 메모는 다이아몬드에서 같은 정점을 다시 파지 않게 한다. 깊이가 입력에 비례하면 재귀 대신 Kahn(큐)으로 바꾼다([algorithm/03-recursion](../../algorithm/03-recursion/2-summary.md) 깊이 한계).

## 장애 시나리오와 대처

### 1. 순환 의존 → 재귀 해석이 `StackOverflowError` (⚠ 커리큘럼)

- **현상**: 설정·권한·모듈 의존을 재귀로 푸는 코드가 특정 데이터에서만 죽는다.
- **보이는 형태**: `java.lang.StackOverflowError`, 스택 트레이스에 같은 메서드 프레임이 수천 겹(위 실험: 약 1.1만 호출 뒤).
- **원인**: 코드가 의존 그래프를 DAG로 가정했다. 데이터에 사이클(A → B → C → A)이 들어오자 재귀가 끝나지 않는다.
- **대처**: GRAY 표시로 사이클을 감지해 경로와 함께 실패시킨다(적용 3). 데이터 입력 시점에도 간선을 추가할 때 사이클 검사를 해 저장을 거부한다.

### 2. 빈 순환 참조 → 애플리케이션 기동 실패

- **현상**: Spring Boot 2.6 이상으로 올린 뒤 애플리케이션이 뜨지 않는다.
- **보이는 형태**: `BeanCurrentlyInCreationException`, 메시지에 `Is there an unresolvable circular reference or an asynchronous initialization dependency?`(Spring Framework 6.2.11 재현 출력, [software-design/25](../../software-design/25-dependency-injection-and-composition-root/2-summary.md) 실험 A).
- **원인**: 빈 의존 그래프에 사이클이 있다. 2.6부터 순환 참조가 기본 금지다(Spring Boot 2.6 Release Notes).
- **대처**: 사이클을 끊는다(책임 분리, 이벤트로 역방향 호출 대체). 릴리스 노트는 사이클을 끊기를 강하게 권하고, 그럴 수 없을 때 `spring.main.allow-circular-references=true`로 2.5 동작을 되돌릴 수 있다고 적는다. 이 설정은 임시 조치로 보는 것이 맞다(해석).

### 3. 빌드·마이그레이션 순서가 정해지지 않는다 (⚠ 커리큘럼)

- **현상**: 순서를 정하는 도구가 일부만 처리하고 멈추거나 "cycle" 오류를 낸다.
- **보이는 형태**: Kahn식 도구면 처리한 개수 < 전체(위 실험 `2/5`), 남은 목록에 사이클과 무관한 정점이 섞일 수 있다.
- **원인**: 의존에 사이클이 생겼다(예: 뷰 마이그레이션이 뒤 단계 테이블을 참조하고, 그 테이블 마이그레이션이 뷰를 참조).
- **대처**: 3색 DFS로 사이클 경로를 뽑아 사람이 끊을 간선을 고른다. 끊을 수 없는 묶음이면 SCC로 묶어 묶음 사이의 순서를 정하고 한 단위로 배포한다. 묶음 안의 선행 조건 사이클은 SCC가 풀어 주지 않는다 — 단계별 적용(먼저 만들고 나중에 참조 추가) 등으로 따로 해소한다. 마이그레이션 쪽 운영 절차는 [database/26-schema-migration](../../database/26-schema-migration/2-summary.md).

### 4. 대기 그래프의 사이클 → 교착

- **현상**: 두 트랜잭션·스레드가 서로를 기다리며 멈춘다.
- **보이는 형태**: DB는 교착 탐지 후 한쪽을 중단시킨다(PostgreSQL `ERROR: deadlock detected`, [database/15](../../database/15-two-phase-locking-and-deadlock/2-summary.md)). JVM 스레드는 `jstack`에 대기 그래프의 사이클이 그대로 찍힌다.

(실험, OpenJDK 21.0.12 Temurin 컨테이너, 2026-10-07 — 스레드 t1이 A→B, t2가 B→A 순서로 `synchronized`, `jstack` 출력 발췌)

```text
   java.lang.Thread.State: BLOCKED (on object monitor)
Found one Java-level deadlock:
"t1":
  waiting to lock monitor 0x0000792dc8001920 (object 0x00000005d5367b00, a java.lang.Object),
  which is held by "t2"
```

- **원인**: "T1이 T2를 기다린다" 간선으로 만든 대기 그래프에 사이클이 생겼다.
- **대처**: 락 획득 순서를 하나로 정해 대기 그래프에 사이클이 생길 수 없게 한다(전순서를 따르면 간선이 한 방향뿐). 자세히는 [os/19-deadlock](../../os/19-deadlock/2-summary.md), [database/15](../../database/15-two-phase-locking-and-deadlock/2-summary.md).

### 5. 무방향 판정법을 방향 그래프에 썼다 → 사이클 오탐

- **현상**: 정상 의존(다이아몬드)인데 "순환 의존" 오류가 난다.
- **보이는 형태**: a → b, a → c, b → d, c → d 그래프에서 오류. 사이클 경로를 출력하면 화살표 방향이 맞지 않는다.
- **원인**: union-find나 "이미 방문 = 사이클" 같은 무방향용 판정을 방향 그래프에 썼다. 무방향으로 보면 a-b-d-c-a가 사이클이지만, 방향으로는 사이클이 아니다.
- **대처**: 방향 그래프는 3색 DFS(역방향 간선) 또는 Kahn으로 판정한다.

## 핵심 문장

- 의존·대기·참조 관계는 방향 그래프이고, "순서를 정할 수 있다"는 "사이클이 없다(DAG)"와 같은 말이다(MCS Theorem 10.5.4).
- 차수의 합은 간선 수의 두 배다. 인접 리스트의 크기와 홀수 차수 정점 개수가 여기서 나온다.
- 유한 무방향 그래프가 트리일 조건은 "연결 + 간선 = 정점 − 1"이다. 간선이 더 있으면 사이클이 있다.
- 사이클 판정은 방향 그래프와 무방향 그래프에서 다르다. 방향 그래프는 경로 위(GRAY) 정점을 다시 만날 때만 사이클이다.
- DAG를 가정한 재귀 코드는 사이클 데이터에서 `StackOverflowError`를 낸다. GRAY 표시로 원인을 드러내는 실패로 바꾼다.
- 병렬 실행 시간의 하한은 가장 긴 의존 사슬이다.

## 관련 주제·근거

- 선행
  - [03-sets-relations-orders](../03-sets-relations-orders/2-summary.md) — 관계·동치류·부분순서(DAG의 도달 관계는 부분순서)
- 후속·연결
  - [06-recurrences-and-asymptotics](../06-recurrences-and-asymptotics/2-summary.md) — 재귀 깊이와 호출 수
  - 자료구조·알고리즘: [data-structure/08-graph](../../data-structure/08-graph/2-summary.md) · [data-structure/34-dependency-resolver](../../data-structure/34-dependency-resolver/2-summary.md) · [data-structure/14-union-find](../../data-structure/14-union-find/2-summary.md) · [algorithm/11-bfs](../../algorithm/11-bfs/2-summary.md) · [algorithm/12-dfs](../../algorithm/12-dfs/2-summary.md) · [algorithm/18-scc](../../algorithm/18-scc/2-summary.md) · [algorithm/17-mst](../../algorithm/17-mst/2-summary.md) · [algorithm/03-recursion](../../algorithm/03-recursion/2-summary.md)
  - 운영: [os/19-deadlock](../../os/19-deadlock/2-summary.md) · [database/15-two-phase-locking-and-deadlock](../../database/15-two-phase-locking-and-deadlock/2-summary.md) · [database/26-schema-migration](../../database/26-schema-migration/2-summary.md) · [software-design/25-dependency-injection-and-composition-root](../../software-design/25-dependency-injection-and-composition-root/2-summary.md)
- 교재
  - MIT 6.042 MCS(Lehman·Leighton·Meyer, 2018-06-06판 PDF <https://courses.csail.mit.edu/6.042/spring18/mcs.pdf>) — 10.1 Vertex Degrees(Lemma 10.1.2), 10.2 Walks and Paths, 10.5 DAGs & Scheduling(Definition 10.5.1·10.5.2, Theorem 10.5.4, Theorem 10.5.8, Corollary 10.5.9), 12.2 Sexual Demographics in America(Lemma 12.2.1 Handshaking Lemma), 12.8 Connectivity, 12.11 Forests & Trees(Lemma 12.11.3, Theorem 12.11.4·12.11.6)
  - CLRS 3판 부록 B의 그래프·트리 절(절 번호 B.4·B.5는 목차로 확인 못 함 `[?]`), 22.3 Depth-first search(Lemma 22.11 "A directed graph G is acyclic if and only if a depth-first search of G yields no back edges"), 22.4 Topological sort, 22.5 Strongly connected components(응축 그래프는 DAG — 보조정리 번호 `[?]`). 절 제목은 walkccc.me CLRS 풀이 사이트, Lemma 22.11은 Grinnell CSC 301 강의 페이지(<https://walker.cs.grinnell.edu/courses/301.fa13/student-comments/student-comments-clrs-sec22.4.html>)로 확인
  - A. B. Kahn, "Topological sorting of large networks", Communications of the ACM 5(11), 1962
- 문서
  - Spring Boot 2.6 Release Notes — Circular References Prohibited by Default(`BeanCurrentlyInCreationException`, `spring.main.allow-circular-references`) <https://github.com/spring-projects/spring-boot/wiki/Spring-Boot-2.6-Release-Notes>
- 실험 목록
  - `Dead.java` + `jstack` — 두 스레드가 락 두 개를 반대 순서로 잡아 `Found one Java-level deadlock` 출력 확인. 같은 환경.
  - `Graph04.java` — 핸드셰이크(V=1000, E=5000, 시드 42), 무작위 트리 간선 수와 간선 추가 시 사이클(union-find), 마이그레이션 5개 DAG의 Kahn 순서, 사이클 추가 후 Kahn 2/5·3색 DFS 사이클 경로, 방문 표시 없는 재귀의 `StackOverflowError`. OpenJDK 21.0.12 Temurin 컨테이너(`--network none --cpus=2`), 2026-10-07, 두 번 실행 + 사실 점검 재실행 1회(결정적 줄 동일, 호출 수만 11,045).
