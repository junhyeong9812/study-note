# data-structure/30-interval-tree — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> 작성 방식: 내가 먼저 기억으로 흐름을 서술하고, Claude는 빠지거나 틀린 곳을 짚는다. 대신 써주지 않는다.
> 이미 따라 치며 만든 정리본이 따로 있으면(organize류) 이 파일은 핵심 문장 압축 + 링크만 담는다.
> 2026-09-14: 쉽게 풀어쓴 확장(Claude 작성) — 한눈에 절·동작 그림·용어 풀이 추가.

## 한눈에 — 쉽게 말하면

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

## 전체 흐름

<!-- 이 자료구조가 동작하는 원리를 자기 말로 -->

## 계약 — IntervalStore (`src/main/java/com/datastructure/interval/IntervalStore.java`)

- `boolean insert(Interval iv)`
- `boolean remove(Interval iv)`
- `int size()`
- `void clear()`
- `default boolean isEmpty()`
- `Interval findAny(Interval query)`
- `List<Interval> findAll(Interval query)`
- `boolean anyOverlaps(Interval query)`
- `List<Interval> toList()`

## 계약 — VisitCounting (`src/main/java/com/datastructure/interval/VisitCounting.java`)

- `long visitedNodes()`

## 구현 — Interval (`src/main/java/com/datastructure/interval/Interval.java`)

### 필드
- `start` — 역할:
- `end` — 역할:

### `Interval(long start, long end)`
- 하는 일:
- 논리:
- 비용(왜):

### `static Interval of(long start, long end)`
- 하는 일:
- 논리:
- 비용(왜):

### `long length()`
- 하는 일:
- 논리:
- 비용(왜):

### `boolean overlaps(Interval other)` (TODO)
- 하는 일:
- 논리:
- 비용(왜):

### `boolean contains(long point)` (TODO)
- 하는 일:
- 논리:
- 비용(왜):

### `int compareTo(Interval other)`
- 하는 일:
- 논리:
- 비용(왜):

### `boolean equals(Object o)` / `int hashCode()` / `String toString()`
- 하는 일:
- 논리:
- 비용(왜):

## 구현 — NaiveIntervalStore (`src/main/java/com/datastructure/interval/NaiveIntervalStore.java`)

### 구조

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

### 동작 — 전수 검사

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

### 필드
- `intervals` — 역할:
- `visitedNodes` — 역할:

### `boolean insert(Interval iv)`
- 하는 일:
- 논리:
- 비용(왜):

### `boolean remove(Interval iv)`
- 하는 일:
- 논리:
- 비용(왜):

### `int size()` / `void clear()`
- 하는 일:
- 논리:
- 비용(왜):

### `Interval findAny(Interval query)`
- 하는 일:
- 논리:
- 비용(왜):

### `List<Interval> findAll(Interval query)` (TODO)
- 하는 일:
- 논리:
- 비용(왜):

### `boolean anyOverlaps(Interval query)`
- 하는 일:
- 논리:
- 비용(왜):

### `List<Interval> toList()`
- 하는 일:
- 논리:
- 비용(왜):

### `long visitedNodes()`
- 하는 일:
- 논리:
- 비용(왜):

## 구현 — IntervalTree (`src/main/java/com/datastructure/interval/IntervalTree.java`)

### 구조

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

### 동작 — 삽입(maxEnd 갱신)

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

### 동작 — 겹침 검색(가지치기)

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

### 필드
- `root` — 역할:
- `size` — 역할:
- `visitedNodes` — 역할:
- `Node.interval` — 역할:
- `Node.maxEnd` — 역할:
- `Node.left` / `Node.right` — 역할:

### `static long maxEndOf(Node node)`
- 하는 일:
- 논리:
- 비용(왜):

### `static void recomputeMaxEnd(Node node)`
- 하는 일:
- 논리:
- 비용(왜):

### `int size()` / `void clear()`
- 하는 일:
- 논리:
- 비용(왜):

### `boolean insert(Interval iv)`
- 하는 일:
- 논리:
- 비용(왜):

### `Node insertInto(Node node, Interval iv)` (TODO, private)
- 하는 일:
- 논리:
- 비용(왜):

### `Interval findAny(Interval query)` (TODO)
- 하는 일:
- 논리:
- 비용(왜):

### `List<Interval> findAll(Interval query)`
- 하는 일:
- 논리:
- 비용(왜):

### `void collectFrom(Node node, Interval query, List<Interval> out)` (TODO, private)
- 하는 일:
- 논리:
- 비용(왜):

### `boolean anyOverlaps(Interval query)`
- 하는 일:
- 논리:
- 비용(왜):

### `boolean remove(Interval iv)`
- 하는 일:
- 논리:
- 비용(왜):

### `Node removeFrom(Node node, Interval iv)` (TODO, private)
- 하는 일:
- 논리:
- 비용(왜):

### `int height()`
- 하는 일:
- 논리:
- 비용(왜):

### `List<Interval> toList()` / `String toString()`
- 하는 일:
- 논리:
- 비용(왜):

### `long visitedNodes()`
- 하는 일:
- 논리:
- 비용(왜):

## 구현 — CoordinateCompressor (`src/main/java/com/datastructure/interval/CoordinateCompressor.java`)

### 구조

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

### 동작 — 압축

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

### 필드
- `coordinates` — 역할:

### `CoordinateCompressor(List<Interval> intervals)` (TODO)
- 하는 일:
- 논리:
- 비용(왜):

### `int size()`
- 하는 일:
- 논리:
- 비용(왜):

### `int compressPoint(long value)`
- 하는 일:
- 논리:
- 비용(왜):

### `long decompressPoint(int index)`
- 하는 일:
- 논리:
- 비용(왜):

### `Interval compress(Interval iv)`
- 하는 일:
- 논리:
- 비용(왜):

### `Interval decompress(Interval compressed)`
- 하는 일:
- 논리:
- 비용(왜):

## 구현 전략 비교

| 전략 | 장점 | 단점 | 적합한 경우 |
|------|------|------|-------------|
| NaiveIntervalStore | | | |
| IntervalTree | | | |
| 정렬 + 스위핑 (IntervalProblems) | | | |

## 문제 — IntervalProblems (`src/main/java/com/datastructure/interval/IntervalProblems.java`)

### 문제 1. merge — 겹치거나 맞닿은 구간을 합친다
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

### 문제 2. maxConcurrent — 동시에 겹치는 구간의 최대 개수
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

## 핵심 문장

<!-- 지도 수준의 문장들 — 세부가 아니라 "왜 이 구조인가"를 담은 문장 -->

-
-
-

## 관련 자료

- 원본 README: `/home/jun/project/myway/data-structure/30-interval-tree/README.md`
- 구현 대상: `/home/jun/project/myway/data-structure/30-interval-tree/src/main/java/com/datastructure/interval/`
- 테스트: `/home/jun/project/myway/data-structure/30-interval-tree/src/test/java/com/datastructure/interval/`
- 정답 구현: `/home/jun/project/myway/data-structure/30-interval-tree/impl/`

## 용어 풀이

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
