# data-structure/30-interval-tree — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> 작성 방식: 내가 먼저 기억으로 흐름을 서술하고, Claude는 빠지거나 틀린 곳을 짚는다. 대신 써주지 않는다.
> 이미 따라 치며 만든 정리본이 따로 있으면(organize류) 이 파일은 핵심 문장 압축 + 링크만 담는다.

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
