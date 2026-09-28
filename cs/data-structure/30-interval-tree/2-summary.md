# data-structure/30-interval-tree — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> 작성 방식: 내가 먼저 기억으로 흐름을 서술하고, Claude는 빠지거나 틀린 곳을 짚는다. 대신 써주지 않는다.
> 이미 따라 치며 만든 정리본이 따로 있으면(organize류) 이 파일은 핵심 문장 압축 + 링크만 담는다.
> 2026-09-14: 쉽게 풀어쓴 확장(Claude 작성) — 한눈에 절·동작 그림·용어 풀이 추가.
> 2026-09-28: 통일 골격 양식으로 재배치 + 새 절 추가(Claude 작성 — 기존 본문은 이동만).

## 해결하는 문제

"이 키가 있나"는 해시맵과 BST가 답한다. 그런데 자료가 점이 아니라 **구간**이고, 묻는 것이 "이 범위와 겹치는 것"이면 그 둘로는 안 된다.\
겹침은 키 하나의 일치가 아니라 두 끝점의 크기 비교이고, 겹치는 구간은 여러 개일 수 있다.

```text
예약 [9,11) [10,12) [14,15) ...  10만 개
질문: [10:30, 11:30) 과 겹치는 예약 전부?

전수 검사                        인터벌 트리 (BST + maxEnd)
[9,11) v  [10,12) v  [14,15) v          [15,20) maxEnd=40
 ... 10만 개 전부 overlaps 를 묻는다      /            \
매 질의 O(n)                    (왼쪽 묶음 maxEnd=30)  [30,40)
                                 (질의가 [32,35) 라면 30 <= 32 -> 왼쪽을 통째로 건너뜀)
```

인터벌 트리는 시작점 정렬 BST에 "이 부분트리에서 제일 늦게 끝나는 시각"(`maxEnd`) 한 필드를 얹어, 겹칠 가능성이 없는 가지를 통째로 건너뛴다.\
쉬운 예: 회의실 예약 장부 — 묶음마다 "제일 늦게 끝나는 시각" 포스트잇을 붙여 두면 "이 묶음은 전부 3시 전에 끝남"을 한 번에 안다.\
똑같은 구조다: 이 노트의 `IntervalTree`는 06번 BST에 `maxEnd`를 더한 것이고, 가지치기 두 줄이 새로 생긴 전부다.\
실무 예: 달력 앱의 겹치는 일정 표시, 회의실·자원 배정의 충돌 검사, 게놈 분석의 유전자 구간 겹침 조회 — 구간 수십만 개에서 질의가 반복될 때.
  - *증강(augmentation)*: 기존 자료구조의 노드에 보조 정보 한 칸을 얹어 새 능력을 얻는 기법. 여기서 얹은 한 칸이 `maxEnd`다.

### 한눈에 — 쉽게 말하면

**비유: 회의실 예약 장부.** "3시~4시에 걸치는 회의 전부 알려줘"라는 질문에,
장부를 처음부터 끝까지 다 읽는 게 나이브(전수 검사)다.
대신 예약들을 시작 시각 순서의 트리로 정리하고, 가지(묶음)마다 **"이 묶음에서 제일 늦게 끝나는 시각"** 포스트잇을 붙여 두면,
"이 묶음은 전부 3시 전에 끝나네" → 그 가지를 통째로 안 읽고 건너뛸 수 있다.

- 구간(interval) = 시작~끝의 범위 하나(회의 하나).
- 인터벌 트리 = 보통의 이진 탐색 트리에 포스트잇(maxEnd) 하나를 더한 것.
- 그 포스트잇 덕에 "겹칠 가능성이 없는 묶음"을 통째로 건너뛴다(가지치기).

```text
  질문: [32,35) 와 겹치는 회의는?

              [15,20) 늦끝=40
             /              \
   +----------------+      [17,19) 늦끝=40
   | 왼쪽 묶음 3개   |           \
   | 늦끝 = 30      |           [30,40)  <- 겹친다!
   +----------------+
   30 <= 32 : 전부 일찍 끝남 -> 통째로 건너뛴다
```

달력 앱의 "겹치는 일정 표시", 회의실 배정, 게놈 분석(유전자 구간 겹침 조회)이 **똑같은 구조다** — 구간 수십만 개에서 "이 범위와 겹치는 것만" 빨리 골라내야 할 때 인터벌 트리를 쓴다.

## 동작·원리

### 전체 흐름

```text
[1] 반개구간 [start, end) 을 정한다        [2] 겹침 = 한 줄
    [9,11) 과 [11,13) 은 안 겹친다              a.start < b.end && b.start < a.end
    (붙여 잡은 회의가 예약되어야 한다)           (통째로 왼쪽/오른쪽인 두 경우의 부정)
              |                                          |
              v                                          v
[3] 시작점 정렬 BST + maxEnd 한 필드
                  [15,20) maxEnd = 40         maxEnd = max(자기 end, left.maxEnd, right.maxEnd)
                 /                \           빈 부분트리 = Long.MIN_VALUE (max 의 항등원)
     [10,30) maxEnd=30      [17,40) maxEnd=40
              |
              v
[4] 질의 [qs, qe) — 가지치기 두 줄
    left.maxEnd <= qs        -> 왼쪽은 전부 qs 전에 끝난다. 통째로 건너뛴다
    node.start  >= qe        -> 오른쪽은 start 가 더 크다. 통째로 건너뛴다
    findAny : 한 갈래로 O(높이)     findAll : O(높이 + k)
              |
              v
[5] 갱신은 돌아오는 길에         [6] 질의가 한 번이면 트리 없이
    insert/remove 뒤 조상마다        정렬 + 스위핑 (merge · maxConcurrent)
    recomputeMaxEnd — 빼먹으면       좌표 범위가 크면 좌표 압축 후 13번 세그먼트 트리
    예외 없이 답이 조용히 빠진다
```

- [1] 끝점을 포함할지부터 정한다. 반개구간이면 11시에 끝나는 회의와 11시에 시작하는 회의가 안 겹친다. 이 결정 하나가 `overlaps`·스위핑 이벤트 순서·`merge` 조건의 부등호를 전부 정한다.
  - *반개구간 [start, end)*: 시작점은 포함하고 끝점은 포함하지 않는 구간.
- [2] 겹침 판정은 "안 겹치는 두 경우(통째로 왼쪽·통째로 오른쪽)"를 부정한 한 줄이다.
- [3] 트리는 06번 BST 그대로이고(`compareTo` = start 오름차순), 노드마다 부분트리 끝점의 최댓값 `maxEnd`를 둔다. 빈 부분트리는 0이 아니라 `Long.MIN_VALUE` — 0을 쓰면 음수 좌표에서 조용히 틀린다.
  - *항등원(identity)*: 연산에 넣어도 결과를 안 바꾸는 값. max의 항등원은 가장 작은 수.
- [4] `left.maxEnd <= qs`면 왼쪽 묶음의 모든 구간이 질의 시작 전에 끝나므로 건너뛴다. `node.start >= qe`면 오른쪽은 start가 더 커서 전부 안 겹친다. 두 줄 중 하나만 지워도 답은 같고 방문만 n으로 뛴다 — 그래서 시간이 아니라 걸음 수(`visitedNodes`)를 센다.
  - *가지치기(pruning)*: 답이 있을 수 없는 가지를 조건 하나로 판정해 통째로 안 내려가는 것.
- [5] 삽입·삭제는 내려갈 때 BST와 같고, 올라올 때 지나온 조상의 `maxEnd`를 전부 다시 계산한다. 낡은 값은 "여기 아래엔 볼 게 없다"는 거짓말이 되어 답이 빠진다 — 나이브 대조만이 그것을 잡는다.
- [6] 자료가 아니라 **질의 횟수**가 자료구조를 정한다. 한 번 물을 거면 정렬 한 번 + 스위핑이 이기고, 반복해서 물을 때 트리가 이긴다.

### 계약 — IntervalStore (`src/main/java/com/datastructure/interval/IntervalStore.java`)

- `boolean insert(Interval iv)`
- `boolean remove(Interval iv)`
- `int size()`
- `void clear()`
- `default boolean isEmpty()`
- `Interval findAny(Interval query)`
- `List<Interval> findAll(Interval query)`
- `boolean anyOverlaps(Interval query)`
- `List<Interval> toList()`

### 계약 — VisitCounting (`src/main/java/com/datastructure/interval/VisitCounting.java`)

- `long visitedNodes()`

### 구현 — Interval (`src/main/java/com/datastructure/interval/Interval.java`)

#### 필드
- `start` — 역할:
- `end` — 역할:

#### `Interval(long start, long end)`
- 하는 일:
- 논리:
- 비용(왜):

#### `static Interval of(long start, long end)`
- 하는 일:
- 논리:
- 비용(왜):

#### `long length()`
- 하는 일:
- 논리:
- 비용(왜):

#### `boolean overlaps(Interval other)` (TODO)
- 하는 일:
- 논리:
- 비용(왜):

#### `boolean contains(long point)` (TODO)
- 하는 일:
- 논리:
- 비용(왜):

#### `int compareTo(Interval other)`
- 하는 일:
- 논리:
- 비용(왜):

#### `boolean equals(Object o)` / `int hashCode()` / `String toString()`
- 하는 일:
- 논리:
- 비용(왜):

### 구현 — NaiveIntervalStore (`src/main/java/com/datastructure/interval/NaiveIntervalStore.java`)

#### 구조

  - *나이브(naive)*: 머리 안 쓰고 전부 확인하는 가장 단순한 방법. 느리지만 틀리기 어려워서 "정답 기준선"으로 쓴다.

```
NaiveIntervalStore - ArrayList 하나가 전부다. 정렬도 색인도 없다(들어온 순서로 뒤에 붙는다)

  intervals   0        1        2        3        4        5
           +--------+--------+--------+--------+--------+--------+
           |[15,20) |[10,30) | [5,20) |[12,15) |[17,19) |[30,40) |
           +--------+--------+--------+--------+--------+--------+

  visitedNodes : 이번 질의에서 들여다본 개수. 트리와 대조할 때 쓰는 계기판이다
  이 클래스가 쉽다는 것이 요점이다. IntervalTree 의 답은 이것과 같아야 한다 - 대조 검증의 기준선
```

#### 동작 — 전수 검사

**언제 쓰나**: 겹치는 구간을 찾을 때 — 이 구현은 언제나 처음부터 끝까지 전부 물어본다. 그림 먼저 — 6개 전부에 v(확인)가 찍히고 마지막 하나만 O(겹침)다.

```
findAll([32,35)) : 처음부터 끝까지 전부 overlaps 를 물어본다. 건너뛰는 곳이 없다

              0        1        2        3        4        5
           +--------+--------+--------+--------+--------+--------+
           |[15,20) |[10,30) | [5,20) |[12,15) |[17,19) |[30,40) |
           +--------+--------+--------+--------+--------+--------+
               v        v        v        v        v        v
               x        x        x        x        x        O   <- 겹치는 것
           visitedNodes = 6 = n  (언제나 정확히 n. 같은 질의에 IntervalTree 는 3)

 findAny 는 첫 겹침에서 멈춘다. 운이 좋으면 1, 나빠도 n
 insert 는 contains 로 중복을 확인하므로 O(n), toList 는 매번 정렬하므로 O(n log n)

 왜 이 느린 것이 필요한가
   가지치기는 "볼 필요 없는 곳을 안 본다"인데, 조건을 하나만 틀리게 쓰면
   "봐야 하는 곳을 안 본다"가 된다. 그러면 예외도 안 나고 답이 조용히 몇 개 빠진다.
   그 조용한 누락을 잡는 유일한 방법이 이 구현과의 대조다.
```

#### 필드
- `intervals` — 역할:
- `visitedNodes` — 역할:

#### `boolean insert(Interval iv)`
- 하는 일:
- 논리:
- 비용(왜):

#### `boolean remove(Interval iv)`
- 하는 일:
- 논리:
- 비용(왜):

#### `int size()` / `void clear()`
- 하는 일:
- 논리:
- 비용(왜):

#### `Interval findAny(Interval query)`
- 하는 일:
- 논리:
- 비용(왜):

#### `List<Interval> findAll(Interval query)` (TODO)
- 하는 일:
- 논리:
- 비용(왜):

#### `boolean anyOverlaps(Interval query)`
- 하는 일:
- 논리:
- 비용(왜):

#### `List<Interval> toList()`
- 하는 일:
- 논리:
- 비용(왜):

#### `long visitedNodes()`
- 하는 일:
- 논리:
- 비용(왜):

### 구현 — IntervalTree (`src/main/java/com/datastructure/interval/IntervalTree.java`)

#### 구조

그림 두 장 — 같은 구간 6개를 수직선(위)과 트리(아래)로 본다. 그림 앞에 말 셋.
  - *이진 탐색 트리(BST)*: 왼쪽엔 작은 것, 오른쪽엔 큰 것을 두는 트리(여기서는 구간의 start 기준).
  - *증강(augmentation)*: 기존 자료구조의 노드에 보조 정보 한 칸을 얹어 새 능력을 얻는 기법. 여기서 얹은 한 칸이 maxEnd 다.
  - *반개구간 [start, end)*: 시작점은 포함하고 끝점은 포함하지 않는 구간. [9,11) 과 [11,13) 은 안 겹친다 — 11시에 끝나는 회의와 11시에 시작하는 회의는 같은 방을 쓸 수 있다.

```
같은 구간 6개를 두 가지로 본다. 수직선 위의 모습과, 그것을 담은 트리.

               0    5    10   15   20   25   30   35   40
               |....|....|....|....|....|....|....|....|
   [5,20)           +==============+
   [10,30)               +===================+
   [12,15)                 +==+
   [15,20)                    +====+
   [17,19)                      +=+
   [30,40)                                   +=========+

 트리 (넣은 순서 [15,20), [10,30), [5,20), [12,15), [17,19), [30,40))

                              +-----------------------+
                              | [15,20)   maxEnd = 40 |
                              +-----------------------+
                                    /             \
                +-----------------------+     +-----------------------+
                | [10,30)   maxEnd = 30 |     | [17,19)   maxEnd = 40 |
                +-----------------------+     +-----------------------+
                    /             \                             \
   +-----------------------+ +-----------------------+     +-----------------------+
   | [5,20)    maxEnd = 20 | | [12,15)   maxEnd = 15 |     | [30,40)   maxEnd = 40 |
   +-----------------------+ +-----------------------+     +-----------------------+

 노드 = 구간 하나. 좌우 순서는 Interval.compareTo = start 오름차순, 같으면 end 오름차순
        (거기까지는 06번 이진 탐색 트리와 똑같다. 더한 것은 maxEnd 한 필드뿐이다)

 증강 maxEnd = 이 부분트리에 있는 모든 구간의 end 중 최댓값
        maxEnd = max(자기 interval.end, left.maxEnd, right.maxEnd)   -> recomputeMaxEnd
        빈 부분트리의 maxEnd = Long.MIN_VALUE (최댓값의 항등원.
                               0 을 쓰면 끝점이 음수인 구간에서 조용히 틀린다)
        루트의 40 은 [30,40) 에서 올라온 값이다. 값이 어디서 왔는지가 아니라
        "이 아래 어딘가에 40 까지 가는 구간이 있다"만 말한다. 가지치기에는 그것으로 충분하다

 구간은 반개구간 [start, end). 겹침 판정은 Interval.overlaps 한 줄이다
        this.start < other.end && other.start < this.end
        안 겹치는 경우는 둘뿐이다(통째로 왼쪽이거나 통째로 오른쪽). 그 둘을 부정한 식이다.
        닫힌 구간으로 잡으면 [9,11] 과 [11,13] 이 11 한 점을 공유해 "겹친다"가 나와서
        붙여 잡은 회의를 예약할 수 없다. 반개구간을 고른 이유가 그것이다.

 균형은 잡지 않는다. 정렬된 순서로 넣으면 한쪽으로 늘어져 연결 리스트가 된다(height() 로 확인).
```

#### 동작 — 삽입(maxEnd 갱신)

**언제 쓰나**: 구간을 새로 넣을 때. 내려가는 길은 보통 BST 삽입과 같고, 요점은 **올라오는 길** — 지나온 조상들의 maxEnd(포스트잇)를 전부 새로 쓰는 것이다. 그림 먼저 — 왼쪽이 전 상태, 오른쪽이 후 상태.
  - *항등원(identity)*: 연산에 넣어도 결과를 안 바꾸는 값. max 의 항등원은 "가장 작은 수"라서, 빈 트리의 maxEnd 는 0이 아니라 Long.MIN_VALUE 여야 한다.

```
insert([25,45)) : 내려가는 길은 06번 BST 와 같다. 다른 것은 돌아오는 길뿐이다

  내려갈 때 : compareTo 로 왼/오른쪽만 고른다
              25 > 15 -> 오른쪽,  25 > 17 -> 오른쪽,  25 < 30 -> 왼쪽,  null -> 새 노드(size++)
              같은 구간이면 그냥 반환한다. 두 번 담지 않고 maxEnd 도 안 바뀐다

 before                                    after
   [15,20) maxEnd = 40                       [15,20) maxEnd = 45   <- 갱신
      |        \                                |        \
     ...        [17,19) maxEnd = 40            ...        [17,19) maxEnd = 45   <- 갱신
                     \                                         \
                      [30,40) maxEnd = 40                        [30,40) maxEnd = 45  <- 갱신
                                                                 /
                                                          [25,45) maxEnd = 45  <- 새 노드

  올라올 때 : 지나온 조상마다 recomputeMaxEnd(node) 를 부른다.
              새 구간이 아래에 붙으면 그 길에 있던 조상들의 maxEnd 가 전부 낡기 때문이다.
              이걸 빼면 예외도 안 나고 답만 조용히 빠진다.
              낡은(작은) maxEnd 를 보고 가지치기가 "여기엔 없다"며 잘라버리기 때문이다.
              삭제 쪽이 더 위험하다. 지운 구간이 그 부분트리에서 제일 늦게 끝나던 것이면
              조상 maxEnd 가 실제보다 커진 채로 남아 방문 수만 늘고(답은 맞고),
              반대로 커진 값을 못 올리면 답이 빠진다.

 비용 = O(트리 높이). 갱신은 내려온 경로에서만 일어나므로 하강과 같은 값이다.
        균형을 안 잡으므로 최악 O(n)
```

#### 동작 — 겹침 검색(가지치기)

**언제 쓰나**: "이 범위와 겹치는 것 전부(findAll) / 하나만(findAny)"을 물을 때. 그림 먼저 — 방문한 노드는 3개뿐이고, 왼쪽 묶음 3개는 상자째 건너뛴다.
  - *가지치기(pruning)*: 답이 있을 수 없는 가지를 조건 하나로 판정해 통째로 안 내려가는 것. 조건이 틀리면 예외 없이 답만 조용히 빠지므로, 나이브와의 대조로 검증한다.

```
findAll([32,35)) : qs = 32, qe = 35.  안 볼 곳을 통째로 건너뛴다

  가지치기 1 (왼쪽)   node.left.maxEnd > qs  일 때만 왼쪽으로 내려간다
      왜 안전한가 : left.maxEnd <= qs 이면 그 부분트리의 모든 구간이 qs 보다 앞에서 끝난다.
                    end <= qs 인 구간은 [qs, qe) 와 겹칠 수 없다(반개구간이라 끝점도 안 겹친다).
                    그래서 몇 개가 있든 통째로 건너뛰어도 답이 안 빠진다.

  가지치기 2 (오른쪽) node.interval.start < qe  일 때만 오른쪽으로 내려간다
      왜 안전한가 : 시작점으로 정렬했으므로 오른쪽 부분트리의 start 는
                    전부 이 노드의 start 이상이다.
                    이 노드의 start 가 이미 qe 이상이면 오른쪽도 전부 그렇고, 전부 안 겹친다.

                              [15,20) maxEnd = 40    (1) 방문. 안 겹침
                                    /             \
   left.maxEnd = 30 <= qs = 32     /               \
   +-------------------------------------+          [17,19) maxEnd = 40   (2) 방문. 안 겹침
   |  [10,30)                            |              \    (start 17 < qe 35 이므로 오른쪽으로)
   |     [5,20)      [12,15)             |               \
   |                                     |                [30,40) maxEnd = 40  (3) 방문
   |   -- 3개를 통째로 건너뛴다 --       |                     30 < 35 && 32 < 40 -> 겹침!
   +-------------------------------------+                     오른쪽은 null

  visitedNodes :  IntervalTree 3   vs   NaiveIntervalStore 6 (= n, 언제나)
  답이 k 개일 때 O(트리 높이 + k) 를 지향한다.
  가지치기가 없으면 답은 똑같이 맞고 방문 수만 n 이 된다.
  그게 더 위험해서 걸음 수를 따로 센다.

 findAny 는 한 갈래로만 내려간다(되돌아오지 않는다). O(트리 높이)
   node.left.maxEnd > qs 이면 왼쪽, 아니면 오른쪽. 왼쪽에서 못 찾았으면 오른쪽에도 없다.
   왼쪽으로 갔다는 건 왼쪽에 end 가 qs 보다 큰 구간 i 가 있다는 뜻인데,
   그 i 가 질의와 안 겹친다면 i.start >= qe 라는 뜻이고,
   오른쪽 구간들의 start 는 전부 i.start 이상이므로 그것들도 전부 안 겹친다.
```

#### 필드
- `root` — 역할:
- `size` — 역할:
- `visitedNodes` — 역할:
- `Node.interval` — 역할:
- `Node.maxEnd` — 역할:
- `Node.left` / `Node.right` — 역할:

#### `static long maxEndOf(Node node)`
- 하는 일:
- 논리:
- 비용(왜):

#### `static void recomputeMaxEnd(Node node)`
- 하는 일:
- 논리:
- 비용(왜):

#### `int size()` / `void clear()`
- 하는 일:
- 논리:
- 비용(왜):

#### `boolean insert(Interval iv)`
- 하는 일:
- 논리:
- 비용(왜):

#### `Node insertInto(Node node, Interval iv)` (TODO, private)
- 하는 일:
- 논리:
- 비용(왜):

#### `Interval findAny(Interval query)` (TODO)
- 하는 일:
- 논리:
- 비용(왜):

#### `List<Interval> findAll(Interval query)`
- 하는 일:
- 논리:
- 비용(왜):

#### `void collectFrom(Node node, Interval query, List<Interval> out)` (TODO, private)
- 하는 일:
- 논리:
- 비용(왜):

#### `boolean anyOverlaps(Interval query)`
- 하는 일:
- 논리:
- 비용(왜):

#### `boolean remove(Interval iv)`
- 하는 일:
- 논리:
- 비용(왜):

#### `Node removeFrom(Node node, Interval iv)` (TODO, private)
- 하는 일:
- 논리:
- 비용(왜):

#### `int height()`
- 하는 일:
- 논리:
- 비용(왜):

#### `List<Interval> toList()` / `String toString()`
- 하는 일:
- 논리:
- 비용(왜):

#### `long visitedNodes()`
- 하는 일:
- 논리:
- 비용(왜):

### 구현 — CoordinateCompressor (`src/main/java/com/datastructure/interval/CoordinateCompressor.java`)

#### 구조

  - *좌표 압축(coordinate compression)*: 실제로 등장하는 좌표만 모아 정렬하고, 큰 숫자 대신 그 순번(0, 1, 2, …)을 쓰는 기법. 크기 순서만 보존되면 겹침 판정이 안 바뀐다는 점을 이용한다.
  - *이진 탐색(binary search)*: 정렬된 목록에서 가운데를 보고 절반씩 줄여 찾는 방법. O(log k).

```
CoordinateCompressor
+---------------------------------------------------------------------+
| coordinates : long[]  - 정렬된 유일 좌표. 인덱스가 곧 압축된 값이다 |
|                         필드는 이것 하나뿐이다.                     |
|                         역매핑 배열이 따로 없다 - 같은 배열을       |
|                         인덱스로 읽으면 그게 역매핑이다.            |
+---------------------------------------------------------------------+

  size()             = k = 등장한 유일 좌표 수. 구간이 n 개면 아무리 많아도 2n
  compressPoint(값)  = coordinates 에서 이진 탐색한 인덱스.  O(log k)
                       없는 좌표면 IllegalArgumentException 을 던진다.
                       "가장 가까운 번호"를 돌려주면 왕복(compress -> decompress)이 조용히 깨진다.
                       압축은 등장한 좌표에 대해서만 정의된다.
  decompressPoint(i) = coordinates[i].  O(1). 범위 밖이면 예외
  compress/decompress= 구간의 양 끝에 위 둘을 각각 적용해 새 Interval 을 만든다

 왜 필요한가 : 13번 세그먼트 트리로 겹침을 풀려면 배열 한 칸이 좌표 하나다.
               좌표가 0..10억이면 배열이 10억 칸(관행대로 4n 이면 40억 칸)인데,
               구간이 1000개면 실제로 등장하는 좌표는 아무리 많아도 2000개다.
               나머지 칸은 어느 구간의 경계도 아니라서 있어도 답이 안 바뀐다.
```

#### 동작 — 압축

**언제 쓰나**: 좌표 범위는 어마어마한데(0~10억) 실제 등장하는 좌표는 몇 개 안 될 때, 배열 기반 구조(13번 세그먼트 트리)에 넣기 전에 좌표를 작은 번호로 갈아끼운다. 단계 먼저 — [1] 끝점 모으기 → [2] 정렬 → [3] 중복 제거, 그다음이 전/후 대응표다.

```
구간 3개 = [1000000000, 2000000000), [1500000000, 2000000000), [5, 1000000000)

 [1] 양 끝점을 전부 모은다 (2n 개)
     raw = [1000000000, 2000000000, 1500000000, 2000000000, 5, 1000000000]
 [2] 정렬한다
     raw = [5, 1000000000, 1000000000, 1500000000, 2000000000, 2000000000]
 [3] 앞에서부터 훑으며 중복을 앞으로 밀어 담고, copyOf 로 unique 개만큼 잘라낸다

  coordinates   idx      0            1            2            3
                     +-------+------------+------------+------------+
                     |   5   | 1000000000 | 1500000000 | 2000000000 |
                     +-------+------------+------------+------------+
                         ^         ^            ^            ^
   압축값(= 인덱스)      0         1            2            3

 before (원래 좌표)                        after (압축 좌표)
   [1000000000, 2000000000)       ->         [1, 3)
   [1500000000, 2000000000)       ->         [2, 3)
   [5,          1000000000)       ->         [0, 1)

 역매핑 : decompress([1,3)) -> [1000000000, 2000000000).  같은 배열을 인덱스로 읽는 것뿐이다

 왜 답이 같은가
   겹침은 좌표의 크기 비교로만 정해진다(a.start < b.end && b.start < a.end).
   순서만 보존하면 판정이 안 바뀌므로, 등장한 좌표를 정렬해 0,1,2 ... 로 갈아끼워도 답이 같다.
   원래 start < end 였고 둘 다 목록에 있으므로 번호도 그 순서를 지킨다
   -> 압축된 구간도 start < end 인 반개구간으로 성립한다.

 비용 : 만들 때 O(n log n) (정렬),  compressPoint O(log k),  decompressPoint O(1)
        배열 칸 수가 10억 -> 2n 으로 준다. 그게 이 클래스가 사는 값이다
```

#### 필드
- `coordinates` — 역할:

#### `CoordinateCompressor(List<Interval> intervals)` (TODO)
- 하는 일:
- 논리:
- 비용(왜):

#### `int size()`
- 하는 일:
- 논리:
- 비용(왜):

#### `int compressPoint(long value)`
- 하는 일:
- 논리:
- 비용(왜):

#### `long decompressPoint(int index)`
- 하는 일:
- 논리:
- 비용(왜):

#### `Interval compress(Interval iv)`
- 하는 일:
- 논리:
- 비용(왜):

#### `Interval decompress(Interval compressed)`
- 하는 일:
- 논리:
- 비용(왜):

## 쓰이는 곳

- **달력·예약 시스템의 충돌 검사** — "새 예약 [10,11)을 넣어도 되나"(`anyOverlaps`)와 "이 시간대에 걸치는 일정 전부"(`findAll`). 경계 포함 규칙이 어긋나면 예약 중복이 난다(아래 장애 1).
- **게놈 분석의 구간 겹침 질의** — 염색체 위치 범위(유전자·리드)를 구간으로 들고 "이 영역과 겹치는 유전자"를 묻는다. 도구마다 구조는 다르다 — bedtools는 UCSC 게놈 브라우저식 구간 bin 색인과 정렬 입력의 스위핑을 쓰고(bedtools 문서), 인터벌 트리를 쓰는 라이브러리도 있다.
- **Linux 커널의 `interval_tree`** — 메모리 매핑(VMA)의 역매핑 등에서 주소 구간 겹침을 찾는 데 레드블랙 트리에 증강한 인터벌 트리를 쓴다(`include/linux/interval_tree_generic.h` — 파일 매핑의 역매핑 `i_mmap` 등). "BST + maxEnd"가 커널 코드 그대로 있는 자리.
- **PostgreSQL range 타입 + GiST 인덱스** — `tsrange && tsrange`(겹침 연산자)와 EXCLUDE 제약으로 예약 중복을 DB가 막는다(PostgreSQL 문서 「Range Types」의 회의실 예약 예제). 반개구간 `[)`이 기본 표기인 것도 같은 결정이다.
- **스위핑 문제** — `merge`(겹치는 구간 합치기)·`maxConcurrent`(회의실 몇 개)는 트리 없이 정렬 + 훑기로 끝난다. [algorithm/30-sweeping](../../algorithm/30-sweeping/2-summary.md)의 이벤트 정렬이 그것이다.
- **좌표 압축 → 세그먼트 트리** — 좌표 범위가 10억이어도 등장하는 좌표는 2n개뿐이므로 순번으로 갈아끼운 뒤 [13-segment-tree](../13-segment-tree/2-summary.md)에 넣는다. `CoordinateCompressor`가 그 다리다.
- **다른 챕터의 재료** — [06-binary-search-tree](../06-binary-search-tree/2-summary.md)에 필드 하나를 더한 것이고, 점을 다루는 [25-spatial-index](../25-spatial-index/2-summary.md)와 같은 "가지치기 + 방문 수 세기" 계열이다.

## 적용 — 풀어나가는 법

구간 문제는 "몇 번 묻는가"와 "끝점을 포함하는가"를 먼저 정하는 데서 갈린다.\
순서: ① 구간 표기를 반개구간으로 못 박고 `overlaps` 한 줄을 먼저 쓴다 → ② 질의가 한 번이면 정렬 + 스위핑(문제 1·2), 반복이면 인터벌 트리 → ③ 트리를 쓰면 가지치기 두 줄과 `maxEnd` 갱신을 나이브 구현과 **대조**해 조용한 누락을 잡는다 → ④ 좌표 범위가 크고 집계가 필요하면 좌표 압축 뒤 세그먼트 트리로 넘긴다.\
아래 과제와 두 문제가 이 순서로 풀린다.

### 문제 — 이 챕터가 시키는 것

원본 README는 13번 세그먼트 트리가 **배열의 값**을, 25번이 **점**을 다뤘다면 여기서는 **구간 자체가 자료**이고 묻는 것이 **겹침**이라고 소개한다.\
06번 BST(시작점 정렬)에 `maxEnd`(그 부분트리 구간들의 끝점 최댓값) **한 필드**를 달면 가지치기 두 줄이 생긴다 — "왼쪽의 maxEnd 가 질의 시작 이하면 왼쪽은 안 본다", "지금 노드의 시작이 질의 끝 이상이면 오른쪽도 안 본다".\
구간 4000개·질의 200번에서 `findAll` 이 전수 800,000 대 트리 5,229, `findAny` 가 182,017 대 2,688 인데, **가지치기 한 줄만 지워도 답은 그대로이고 방문만 41만 번대로 뛴다** — 그래서 시간이 아니라 걸음 수를 센다.\
그리고 반개구간 `[start, end)` 결정 하나가 `overlaps`·스위핑 이벤트 순서·`merge` 의 합치기 조건을 전부 정하는데 **셋의 부등호가 서로 다르다**.

과제 목록 — `src/main/java/com/datastructure/interval/`의 TODO 10개:

- `Interval` — TODO 1(`overlaps` — 이 한 줄이 이 박스의 절반) · TODO 2(`contains` — 한쪽에만 등호)
- `NaiveIntervalStore`(기준선) — TODO 3(`findAll` — 하나 볼 때마다 `visitedNodes` 증가)
- `IntervalTree` — TODO 4(`insertInto` — 돌아오는 길에 `maxEnd` 갱신) · TODO 5(`findAny` — 한 갈래) · TODO 6(`collectFrom` — 가지치기 두 줄) · TODO 7(`removeFrom`)
- `CoordinateCompressor` — TODO 8(등장한 좌표만 정렬·중복 제거해 번호 매기기)
- `IntervalProblems` — TODO 9(`merge`) · TODO 10(`maxConcurrent` — 좌표가 같을 때 끝을 먼저)

순서: `Interval`(2) → `NaiveIntervalStore`(1) → `IntervalTree`(4, `insert` → `findAny` → `findAll` → `remove`) → `CoordinateCompressor`(1) → `IntervalProblems`(2).\
테스트가 `root`·`size` 와 노드의 `interval/maxEnd/left/right` 를 직접 읽는다 — **필드 이름이 계약이다.**\
실행: `cd ~/project/myway/data-structure && ./run.sh 30` — README 기준 **94개 중 78개가 실패**한다.

아래 서머리는 이 문제(README)를 분석·정리한 것이다.

### 구현 전략 비교

| 전략 | 장점 | 단점 | 적합한 경우 |
|------|------|------|-------------|
| NaiveIntervalStore | | | |
| IntervalTree | | | |
| 정렬 + 스위핑 (IntervalProblems) | | | |

### 문제 — IntervalProblems (`src/main/java/com/datastructure/interval/IntervalProblems.java`)

#### 문제 1. merge — 겹치거나 맞닿은 구간을 합친다
> 문제 설명: 겹치거나 맞닿은 구간을 합친다. 결과는 start 오름차순이고 서로 안 겹친다.
> `intervals` 가 null 이면 IllegalArgumentException, 비어 있으면 빈 목록.
>
> 생각할 것
> - 정렬하고 나면 지금 들고 있는 하나와 다음 하나만 보면 된다. 왜 그것으로 충분한가.
> - 합치는 조건이 `overlaps` 와 다르다. `[9,11)` 과 `[11,13)` 은 안 겹치는데, 둘을 합한 점의 집합은 `[9,13)` 과 정확히 같다. 반개구간이라 빈틈이 없기 때문이다.
> - 다음 구간이 앞 구간 안에 통째로 들어가 있으면 end 가 줄면 안 된다.
> - 마지막 하나는 반복문 안에서 안 나온다.

- 내 접근:
- 논리:
- 비용(왜):

#### 문제 2. maxConcurrent — 동시에 겹치는 구간의 최대 개수
> 문제 설명: 동시에 겹치는 구간의 최대 개수. 회의실이 몇 개 필요한가.
> 시작 이벤트와 끝 이벤트를 각각 정렬해놓고 이른 것부터 처리하는 스위핑이다.
> 빈 목록이면 0, null 이면 IllegalArgumentException.
>
> 생각할 것
> - 지금 열려 있는 개수를 세면서 그 최댓값을 기억한다.
> - 좌표가 같을 때 무엇을 먼저 처리해야 하는가. 반개구간이므로 `[9,11)` 이 끝나는 11 시에 `[11,13)` 이 시작해도 그 순간 방은 하나면 된다. 이 함정이 이 문제의 전부다.
> - 시작을 다 처리하면 끝난다. 남은 끝 이벤트는 최댓값을 못 바꾼다.

- 내 접근:
- 논리:
- 비용(왜):

## 장애 시나리오와 대처

**1. 11시에 끝나는 회의와 11시에 시작하는 회의를 "겹친다"고 거부한다 — 또는 그 반대로 둘 다 예약된다**

- 현상: 붙여 잡은 회의 둘 중 하나가 거부되거나, 반대로 같은 시각을 공유하는 예약이 중복으로 들어간다.
- 보이는 형태: `anyOverlaps([11,13))`이 `[9,11)`에 대해 `true`(닫힌 구간으로 판정) — 또는 DB에서는 끝점 포함(`[9,11]`)으로 저장했는데 트리는 반개구간으로 판정해 `[11,13)`을 허용한다. 예외는 없다.
- 원인: 경계 포함 규칙이 계층마다 다르다. `overlaps`의 부등호(`<`), 스위핑의 같은 좌표 처리 순서(끝 먼저), `merge`의 합치기 조건(`<=`)은 셋 다 반개구간이라는 하나의 결정에서 나오는데, 입력 쪽(UI·DB)이 다른 규칙이면 어느 한 줄이 어긋난다.
- 대처: 구간 표기를 시스템 경계에서 한 번만 정하고(`[start, end)`), 저장·전송 형식에 그 규칙을 명시한다. 끝점을 포함하는 입력이 오면 `end + 1`(정수 좌표)로 바꿔 넣는다. 경계 좌표가 정확히 같은 케이스는 무작위 대조로 안 걸리므로 경계 테스트를 따로 둔다(원본 README 한계 4).

**2. 압축기에 없는 좌표로 질의해서 예외가 난다**

- 현상: 구간 집합으로 `CoordinateCompressor`를 만든 뒤, 사용자 질의 구간을 압축하려는 순간 죽는다.
- 보이는 형태: `IllegalArgumentException: 등장하지 않은 좌표다: 1234`. 구축 때 넣은 구간의 끝점이 아닌 값은 전부 여기에 걸린다.
- 원인: 압축은 구축 시점에 등장한 좌표에 대해서만 정의된다. "가장 가까운 번호"를 돌려주면 `compress → decompress` 왕복이 조용히 깨지므로 일부러 예외로 막았다. 질의 좌표는 구축 집합에 없을 수 있다는 것을 잊은 것이다.
- 대처: 질의 좌표까지 미리 모아 함께 압축하거나(오프라인 문제의 관례), 질의 시점에는 이진 탐색으로 "그 값 이상인 첫 좌표"를 따로 구해 압축 구간을 만든다. 온라인으로 좌표가 계속 새로 들어오면 좌표 압축이 아니라 인터벌 트리가 맞는 구조다.

**3. 예약이 시간순으로 들어와 트리가 연결 리스트가 된다**

- 현상: 운영 초기에는 빠르던 `findAll`이 데이터가 쌓일수록 전수 검사와 다를 바 없어진다.
- 보이는 형태: `height()`가 `size()`에 가깝다. 같은 질의의 `visitedNodes()`가 흩어 넣은 트리의 수십 배(원본 README 실측: 1000개 정렬 삽입에 높이 1000, `findAll` 방문 506 대 17). 답은 맞다.
- 원인: 예약·로그는 대개 시작 시각 순으로 들어온다. 이 트리는 균형을 잡지 않으므로 정렬 입력에 한쪽으로 늘어진다 — 06번 BST와 똑같은 자리(정답 6번 참고).
- 대처: 삽입 순서를 섞을 수 없는 워크로드면 균형 트리(16번 레드블랙 트리)에 `maxEnd`를 증강한다 — 회전 때 `maxEnd`를 함께 다시 계산하면 된다. 일괄 적재라면 정렬 뒤 중앙값부터 넣어 처음부터 균형을 만든다.

## 핵심 문장

- 구간 자체가 자료이고 묻는 것이 겹침이면 키 일치 구조(해시·BST)로는 안 된다. 인터벌 트리는 시작점 정렬 BST에 `maxEnd` 한 필드를 얹어 겹칠 수 없는 가지를 통째로 건너뛴다.
- 가지치기는 두 줄이다 — 왼쪽 묶음의 `maxEnd`가 질의 시작 이하면 왼쪽을, 이 노드의 시작이 질의 끝 이상이면 오른쪽을 버린다. 한 줄만 지워도 답은 그대로이므로 시간이 아니라 걸음 수를 센다.
- 반개구간 `[start, end)` 결정 하나가 `overlaps`·스위핑 순서·`merge` 조건의 부등호를 전부 정한다 — 셋이 서로 다르되 한 결정에서 나온다.
- `maxEnd`는 돌아오는 길에 갱신한다. 빼먹으면 예외 없이 답이 빠지고, 빈 부분트리에 0을 쓰면 음수 좌표에서 무너진다 — 조용한 누락은 나이브 대조만이 잡는다.
- 자료가 아니라 질의 횟수가 자료구조를 정한다. 한 번 물으면 정렬 + 스위핑, 반복해서 물으면 트리, 좌표가 크고 집계가 필요하면 좌표 압축 뒤 세그먼트 트리.

## 관련 주제·근거

- 선행 — [06-binary-search-tree](../06-binary-search-tree/2-summary.md): 여기에 `maxEnd` 한 필드를 더한 것이 인터벌 트리다. 정렬 입력에 늘어지는 한계도 그대로 물려받는다.
- 선행 — [13-segment-tree](../13-segment-tree/2-summary.md): 배열 구간 집계. 좌표 압축을 거치면 겹침 문제를 여기로도 보낼 수 있다.
- 연결 — [25-spatial-index](../25-spatial-index/2-summary.md): 점을 다루는 가지치기. "볼 필요 없는 가지를 안 본다 + 방문 수를 센다"가 같은 계열이다.
- 연결 — [algorithm/30-sweeping](../../algorithm/30-sweeping/2-summary.md): `merge`·`maxConcurrent`의 이벤트 정렬 — 질의가 한 번일 때 트리를 대신한다.
- 후속 — [16-red-black-tree](../16-red-black-tree/2-summary.md) · [31-consistent-hashing](../31-consistent-hashing/2-summary.md): 균형이 필요해지는 자리, 그리고 정렬된 좌표를 원으로 잇는 다음 챕터.
- 영역 표 — [data-structure/curriculum.md](../curriculum.md) `42-interval-tree` (선행 `17`, 교재 CLRS 14.3).
- myway 원본 — `/home/jun/project/myway/data-structure/30-interval-tree/` (README.md · impl/IntervalTree.java · impl/Interval.java · impl/CoordinateCompressor.java · impl/IntervalProblems.java).

### 관련 자료

- 원본 README: `/home/jun/project/myway/data-structure/30-interval-tree/README.md`
- 구현 대상: `/home/jun/project/myway/data-structure/30-interval-tree/src/main/java/com/datastructure/interval/`
- 테스트: `/home/jun/project/myway/data-structure/30-interval-tree/src/test/java/com/datastructure/interval/`
- 정답 구현: `/home/jun/project/myway/data-structure/30-interval-tree/impl/`

### 용어 풀이

- **구간(interval)**: 시작~끝으로 표현되는 범위 하나. 회의 시간, 유전자 위치 범위 같은 것.
- **반개구간 [start, end)**: 시작점은 포함, 끝점은 미포함인 구간. 11에 끝나는 구간과 11에 시작하는 구간이 안 겹치게 해 준다.
- **겹침(overlap)**: 두 구간이 공통 부분을 갖는 것. 판정식은 `a.start < b.end && b.start < a.end`.
- **이진 탐색 트리(BST)**: 왼쪽엔 작은 키, 오른쪽엔 큰 키를 두는 트리. 비교하며 내려가면 자리가 나온다.
- **증강(augmentation)**: 기존 자료구조의 노드에 보조 정보를 한 칸 얹어 새 능력을 얻는 기법.
- **maxEnd**: 그 노드 아래(부분트리) 모든 구간의 end 중 최댓값. 가지치기의 근거가 되는 "포스트잇".
- **부분트리(subtree)**: 어떤 노드와 그 아래에 매달린 전체.
- **가지치기(pruning)**: 답이 있을 수 없는 가지를 조건 판정으로 통째로 건너뛰는 것.
- **나이브(naive) / 전수 검사**: 전부 다 확인하는 가장 단순한 방법. 느리지만 정답 기준선이 된다.
- **대조 검증(cross-check)**: 빠른 구현의 답을 느리고 확실한 구현의 답과 비교해 조용한 누락을 잡는 검증법.
- **항등원(identity)**: 연산에 넣어도 결과가 안 변하는 값. max 의 항등원은 가장 작은 수(Long.MIN_VALUE).
- **Long.MIN_VALUE**: 자바 long 타입이 표현할 수 있는 가장 작은 수.
- **균형 / 한쪽으로 늘어진 트리**: 좌우가 고르게 자라 높이가 log n 인 트리 / 정렬된 입력 때문에 연결 리스트처럼 늘어져 높이가 n 이 된 트리.
- **좌표 압축(coordinate compression)**: 등장하는 좌표만 정렬해 순번(0,1,2,…)으로 갈아끼우는 기법. 크기 순서만 지키면 겹침 판정이 안 바뀐다.
- **이진 탐색(binary search)**: 정렬된 목록에서 절반씩 줄여 찾는 방법.
- **세그먼트 트리(segment tree)**: 배열 구간 질의를 빠르게 하는 트리(13번). 배열 한 칸이 좌표 하나라서 좌표 압축이 필요해진다.
- **스위핑(sweeping)**: 이벤트(시작/끝)를 시각 순으로 정렬해 왼쪽부터 쓸고 지나가며 세는 기법.
- **O(n) / O(log n) / O(n log n) / O(트리 높이 + k)**: 전체 개수에 비례 / 절반씩 줄여 가는 걸음 수 / 정렬의 비용 / 내려가는 길 + 답의 개수(k)만큼만 일한다는 뜻.
- **재귀(recursion)**: 함수가 자기 자신을 불러 한 층 아래의 같은 문제를 푸는 방식.
- **IllegalArgumentException / IndexOutOfBoundsException**: "잘못된 값을 줬다 / 범위 밖 번호를 줬다"를 알리는 자바의 오류 신호.
