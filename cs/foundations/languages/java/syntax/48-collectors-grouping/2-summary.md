# java/syntax/48 — `Collectors` 그룹핑·분할·다운스트림 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **선행** — [`../47-collectors-basics/`](../47-collectors-basics/). 기본 수집기와 `toMap` 을 먼저 본다.
> **기준 소스** — [`Collectors` javadoc (Java SE 21)](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/stream/Collectors.html) · JDK 21.0.5 표준 라이브러리 소스 `java.base/java/util/stream/Collectors.java`(`lib/src.zip`)
> **실행 검증** — 이 문서의 모든 출력·에러는 Temurin **JDK 21.0.5** 에서 실제로 돌려 얻은 것이다.\
> 같은 프로그램 3개를 **17.0.13 · 25.0.1** 에서도 돌려 **출력이 한 글자도 다르지 않음**을 확인했다(`HashMap` 의 키 순서까지 같았다).
> **버전** — `groupingBy`·`partitioningBy`·`mapping` 은 **Java 8**. `filtering`·`flatMapping` 은 **Java 9**. `teeing` 은 **Java 12**.\
> 17·21·25 동작 동일.
> **범위** — 병렬에서 달라지는 것(`groupingByConcurrent`·결합 비용)은 [`../49-parallel-streams/`](../49-parallel-streams/) 이 정본이다.\
> 그쪽은 **스레드와 결합 비용**까지, 여기는 **조합의 문법과 결과 모양**까지다.\
> `HashMap` 이 키를 왜 그 순서로 도는지는 [`../../../../../data-structure/05-hashmap/`](../../../../../data-structure/05-hashmap/) 이 정본이다.\
> 그쪽은 **버킷 배치**까지, 여기는 **"그래서 순서를 믿으면 안 된다"**부터다.
> 이 본문은 Claude 작성이다(원고 없음).

## 한눈에 — 쉽게 말하면

**그룹핑은 그릇을 칸칸이 나누는 것이고, 다운스트림은 칸마다 또 그릇을 놓는 것이다.**

47번의 비유를 그대로 잇는다.

| 비유 | 실체 |
|---|---|
| 벨트 끝에 놓는 그릇 | 수집기 — 47번 |
| **이름표를 보고 칸을 골라 담는 선반** | **`groupingBy(분류함수)`** |
| 칸마다 **또 다른 그릇**을 놓는 것 | 다운스트림 수집기 |
| **칸이 딱 둘인 선반** | `partitioningBy(술어)` |
| 담기 전에 물건을 바꿔치기 | `mapping(변환, 그릇)` |
| 칸은 만들되 조건에 맞는 것만 담기 | `filtering(술어, 그릇)` (9+) |
| 그릇 둘에 동시에 담고 끝에 합치기 | `teeing(그릇1, 그릇2, 합치기)` (12+) |

- 선반의 칸은 **물건을 보고 나서** 만들어진다.\
  `red` 가 하나도 없으면 `red` 칸은 **아예 생기지 않는다.**
- 그런데 **칸이 둘뿐인 선반(`partitioningBy`)만은 다르다.**\
  거기는 물건이 없어도 `false` 칸과 `true` 칸이 **언제나 둘 다** 있다.
- 칸을 고르는 순서는 **보장이 없다.** 선반이 `HashMap` 이기 때문이다.

```text
groupingBy — 칸이 필요할 때 생긴다        partitioningBy — 칸이 언제나 둘

  점수 > 1000 인 사람으로 나누면             점수 > 1000 으로 나누면
        |                                          |
        v                                          v
  {false=[다섯 명]}                          {false=[다섯 명], true=[]}
  크기 1                                      크기 2
  get(true) -> null                           get(true) -> []  (빈 리스트)
```

**똑같은 구조로** Java 가 이렇게 동작한다: 선반 = 결과 `Map`, 칸 = 키, 칸 안의 그릇 = 다운스트림.

실무에서 이게 터지는 자리는 **`groupingBy` 결과에 `.get(키)` 하고 바로 `.size()` 를 부르는 것**이다.\
그 키의 원소가 하나도 없으면 `null` 이고, `NullPointerException` 이 난다.

> **분류 함수(classifier)** — 원소를 보고 어느 칸에 넣을지 정하는 함수. `groupingBy` 의 첫 인자.\
> 예: `P::team` 은 팀 이름을 키로 삼는다.

> **다운스트림(downstream)** — 한 칸 안에 모인 원소들을 다시 모으는 수집기.\
> 예: `groupingBy(P::team, counting())` 의 `counting()` 이 다운스트림이다. 칸마다 따로 센다.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. `groupingBy` 의 결과는 **어떤 맵·어떤 리스트**이고 그 순서를 믿어도 되나.
2. 다운스트림을 **어떻게 조합**해서 2단 그룹핑·집계를 만드나.
3. `partitioningBy` 는 `groupingBy` 로 대체할 수 있나 — 무엇이 다른가.

## 예시 데이터 — 이 묶음이 공유하는 것

47번과 같은 데이터다. 주제를 건너다니며 읽을 때 비교가 공짜로 따라온다.

```text
record P(String team, String name, int score)

  [red   kim   10]
  [blue  lee   20]
  [red   park  30]
  [green choi  40]
  [blue  jung  50]

  team 별:  red   -> kim(10), park(30)     합 40  평균 20.0
            blue  -> lee(20), jung(50)     합 70  평균 35.0
            green -> choi(40)              합 40  평균 40.0
```

- 47번은 이 다섯을 **하나로** 모았다(합 150·평균 30.0).
- 48번은 **`team` 으로 나눠서** 모은다. 그것이 두 주제의 경계다.

## 동작 방식

### (1) `groupingBy` 의 기본값 — 무엇이 나오나

**언제 쓰나** — 목록을 어떤 속성으로 묶을 때.

**실행 결과** (`Ex.java` — 48-a, 17·21·25 동일)

```text
== groupingBy 기본 ==
맵 타입   : java.util.HashMap
값 타입   : java.util.ArrayList
키 순서   : [red, green, blue]
red       : [kim, park]
```

```text
groupingBy(P::team)   =   groupingBy(P::team, HashMap::new, toList())

  [red kim 10]   -> 키 "red"   -> red 칸의 ArrayList 에 추가
  [blue lee 20]  -> 키 "blue"  -> blue 칸을 만들고 추가
  [red park 30]  -> 키 "red"   -> 이미 있는 red 칸에 추가
  [green choi]   -> 키 "green" -> green 칸을 만들고 추가
  [blue jung 50] -> 키 "blue"  -> 이미 있는 blue 칸에 추가
        |
        v
  HashMap{red=ArrayList[kim,park], green=ArrayList[choi], blue=ArrayList[lee,jung]}
   ^                ^
   순서 보장 없음    칸 안은 입력 순서 그대로
```

그림 해설 (한 단계씩):

- 1인자 `groupingBy` 는 **`groupingBy(classifier, toList())` 와 같다.** javadoc 의 `@implSpec` 이 그렇게 적는다.
- 맵은 **`HashMap`**, 값은 **`ArrayList`** 다 — 둘 다 **실측이지 보장이 아니다.**

> There are no guarantees on the type, mutability, serializability, or thread-safety of the `Map` or `List` objects returned.

- **칸 안의 순서는 입력 순서**다(순차 스트림 기준). `red` 칸이 `[kim, park]` 인 것이 그 증거다.
- **칸의 순서(키 순서)는 보장이 아니다** — 입력이 `red, blue, red, green, blue` 인데 결과는 `[red, green, blue]` 다.

비용 — 원소마다 해시 한 번 + 리스트 추가 한 번. 순회는 한 번이다.

### (2) 키 순서를 믿으면 안 된다

**언제 쓰나** — 그룹핑 결과를 그대로 화면·API 로 내보낼 때.

**실행 결과** (`Ex.java` — 48-a, 세 JDK 모두 동일)

```text
== 키 순서는 보장이 아니다 ==
입력 순서 : [apple, banana, cherry, date, elderberry, fig, grape, honeydew]
맵 순서   : [date, banana, honeydew, cherry, apple, fig, grape, elderberry]
```

```text
입력 순서                                   HashMap 순회 순서

  apple                                      date
  banana                                     banana
  cherry                                     honeydew
  date            ==== groupingBy ====>      cherry
  elderberry                                 apple
  fig                                        fig
  grape                                      grape
  honeydew                                   elderberry

  아무 관계도 없다 — 해시값이 자리를 정한다
```

그림 해설 (한 단계씩):

- 입력 순서와 **아무 관계가 없다.** 정렬 순서도 아니다.
- 그런데 **실행할 때마다 바뀌지는 않는다** — 세 JDK · 여러 실행에서 같은 순서였다.\
  `String.hashCode` 가 결정적이기 때문이다. **이 안정성이 함정이다.**\
  "돌려 보니 항상 같더라"는 관찰이 「보장」으로 오해된다.
- 키를 하나만 바꿔도, JDK 를 바꿔도, 맵 크기가 달라져도 순서가 바뀔 수 있다.

**고치는 법**

```java
// 정렬 순서가 필요하면
groupingBy(P::team, TreeMap::new, mapping(P::name, toList()))       // {blue=…, green=…, red=…}
// 입력에서 처음 나온 순서가 필요하면
groupingBy(P::team, LinkedHashMap::new, mapping(P::name, toList())) // {red=…, blue=…, green=…}
```

**실행 결과** (`Ex.java` — 48-a)

```text
TreeMap       : {blue=[lee, jung], green=[choi], red=[kim, park]}
LinkedHashMap : {red=[kim, park], blue=[lee, jung], green=[choi]}
```

비용 — `TreeMap` 은 삽입마다 비교가 들어간다(O(log n)). `LinkedHashMap` 은 링크 하나 값이다.\
어느 쪽이든 **순서가 필요하면 반드시 명시한다.**

### (3) 다운스트림 — 칸마다 다른 그릇

**언제 쓰나** — 그룹별 개수·합·평균·이름 목록이 필요할 때.

**실행 결과** (`Ex.java` — 48-b, 출력을 `TreeMap` 으로 받아 순서를 고정했다)

```text
counting        : {blue=2, green=1, red=2}
mapping         : {blue=[lee, jung], green=[choi], red=[kim, park]}
summingInt      : {blue=70, green=40, red=40}
averagingInt    : {blue=35.0, green=40.0, red=20.0}
joining         : {blue=lee+jung, green=choi, red=kim+park}
maxBy           : {blue=Optional[P[team=blue, name=jung, score=50]], green=Optional[P[team=green, name=choi, score=40]], red=Optional[P[team=red, name=park, score=30]]}
collectingAndThen : {blue=jung, green=choi, red=park}
toCollection    : {blue=[jung, lee], green=[choi], red=[kim, park]}
```

```text
groupingBy(P::team, TreeMap::new, 다운스트림)

  선반을 만든다 (TreeMap)
        |
   +----+----+----+
   |         |    |
  blue     green red        <- 칸
   |         |    |
  [lee]    [choi][kim]      <- 각 칸에 들어온 원소들이
  [jung]         [park]        다운스트림 수집기로 다시 들어간다
   |         |    |
  toList()  -> [lee, jung]
  counting()-> 2
  joining("+") -> "lee+jung"
  maxBy()   -> Optional[jung]
```

그림 해설 (한 단계씩):

- 다운스트림은 **칸 안에서 다시 `collect` 를 돌리는 것**이다. 47번의 수집기가 전부 여기 들어간다.
- `maxBy` 를 다운스트림으로 쓰면 **값 자리에 `Optional` 이 박힌다.** 대개 원하는 모양이 아니다.
- 그때 `collectingAndThen` 으로 벗긴다.

```java
groupingBy(P::team, TreeMap::new,
        collectingAndThen(maxBy(comparingInt(P::score)), o -> o.map(P::name).orElse("-")))
// {blue=jung, green=choi, red=park}
```

- `mapping` 은 **담기 전에 변환**한다. `mapping(P::name, toList())` 가 가장 자주 쓰인다.
- `toCollection(TreeSet::new)` 을 쓰면 칸 안이 정렬된다 — `blue=[jung, lee]` 가 그 증거다(입력은 `lee, jung`).

비용 — 순회는 여전히 **한 번**이다. 다운스트림이 늘어도 소스를 다시 읽지 않는다.

### (4) `filtering`(9+)과 `filter` 를 앞에 두는 것은 다르다

**언제 쓰나** — 그룹별 집계인데 일부만 세야 할 때. **빈 그룹을 남기고 싶을 때.**

**실행 결과** (`Ex.java` — 48-b, 조건은 `score >= 40`)

```text
filtering 다운스트림 : {blue=[jung], green=[choi], red=[]}
filter 를 앞에      : {blue=[jung], green=[choi]}
```

```text
filtering 다운스트림                       filter 를 앞에

  원소 5개가 전부 분류된다                   원소 2개만 살아남는다
  red 칸도 만들어진다                        red 원소가 없으니
        |                                    red 칸이 안 만들어진다
        v                                          |
  {blue=[jung], green=[choi], red=[]}              v
   ^                                        {blue=[jung], green=[choi]}
   빈 리스트로 남는다                          red 는 아예 없다
```

그림 해설 (한 단계씩):

- **결과가 다르다.** 키 `red` 가 있느냐 없느냐.
- `filtering` 은 **분류는 하고 담기만 거른다** — 그래서 빈 칸이 남는다.
- `filter` 를 앞에 두면 **분류 자체를 안 하므로** 칸이 안 생긴다.
- 어느 쪽이 맞는지는 요구사항이 정한다.\
  "모든 팀에 대해 고득점자 수를 보여 달라"면 `filtering`(0명도 보여야 한다),\
  "고득점자가 있는 팀만 보여 달라"면 `filter`.
- 이 차이 때문에 `filtering` 이 Java 9 에 추가됐다. **`filter` 로는 표현할 수 없는 결과**가 있다.

비용 — `filtering` 은 걸러진 원소도 분류 함수를 거친다. `filter` 를 앞에 두는 쪽이 조금 싸다.

### (5) `partitioningBy` 는 **항상 두 칸**이다

**언제 쓰나** — 조건으로 둘로 가를 때. 그리고 **양쪽 다 보여 줘야** 할 때.

**실행 결과** (`Ex.java` — 48-c)

```text
partitioningBy       : {false=[kim, lee], true=[park, choi, jung]}
맵 타입              : java.util.stream.Collectors$Partition
키 순서              : [false, true]
== 항상 두 칸이다 ==
아무도 통과 못 함     : {false=[P[team=red, name=kim, score=10], P[team=blue, name=lee, score=20], P[team=red, name=park, score=30], P[team=green, name=choi, score=40], P[team=blue, name=jung, score=50]], true=[]} / 크기 2
전부 통과            : [] <- false 칸이 비어 있다 / 크기 2
빈 스트림            : {false=[], true=[]} / 크기 2
== groupingBy 로 같은 일을 하면 ==
groupingBy 아무도 통과 못 함 : {false=[P[team=red, name=kim, score=10], P[team=blue, name=lee, score=20], P[team=red, name=park, score=30], P[team=green, name=choi, score=40], P[team=blue, name=jung, score=50]]} / 크기 1
g.get(true)          : null
part.get(true)       : []
== 이 맵은 수정할 수 있나 ==
put(true) : java.lang.UnsupportedOperationException
put(null) : java.lang.UnsupportedOperationException
```

```text
partitioningBy(p)                          groupingBy(원소 -> p.test(원소))

  {false=[...], true=[...]}                  {false=[...]}  또는 {true=[...]}
  언제나 크기 2                                통과한 쪽만 생긴다
  get(true) -> 빈 리스트                       get(true) -> null   <- NPE 의 씨앗
  키 순서 [false, true] 고정                   키 순서 보장 없음
  전용 맵 타입 (Collectors$Partition)          HashMap
  수정 불가 (put 하면 던진다)                   수정 가능
```

그림 해설 (한 단계씩):

- **이것이 두 메서드의 진짜 차이다.** "키가 `Boolean` 인 `groupingBy`"가 아니다.
- javadoc 이 명시한다.

> The returned `Map` **always contains mappings for both `false` and `true` keys.**\
> (`@apiNote`) If a partition has no elements, its value in the result Map will be an empty List.

- 그래서 `part.get(true).size()` 는 **언제나 안전**하고, `g.get(true).size()` 는 `NullPointerException` 이 날 수 있다.
- 반환 맵은 **전용 타입**(`Collectors$Partition`)이고 **수정할 수 없다.**\
  `put(true, ...)` 도 `put(null, ...)` 도 `UnsupportedOperationException` 이다.\
  단 이 타입 자체는 javadoc 이 보장하지 않는다 — 보장되는 것은 **"두 키가 항상 있다"** 까지다.

비용 — `HashMap` 보다 가볍다(칸이 둘로 고정이라 배열 둘이면 된다).\
**조건이 둘로 갈리는 일이면 `groupingBy` 보다 `partitioningBy` 가 맞다.**

### (6) 조합 — 2단 그룹핑과 `teeing`(12+)

**언제 쓰나** — "팀별·등급별 인원", "팀별 최저~최고" 같은 2차원 집계.

**실행 결과** (`Ex.java` — 48-b·48-c)

```text
2단 그룹핑       : {blue={false=[lee], true=[jung]}, green={true=[choi]}, red={false=[kim], true=[park]}}
분할 안 그룹핑        : {false={blue=1, red=1}, true={blue=1, green=1, red=1}}
teeing          : 5명 합계 150
teeing 다운스트림 : {blue=20~50, green=40~40, red=10~30}
flatMapping     : {blue=[l, e, e, j, u, n, g], green=[c, h, o, i], red=[k, i, m, p, a, r, k]}
```

```text
groupingBy(팀, groupingBy(고득점여부, mapping(이름, toList())))

  선반                칸 안의 선반          칸 안의 칸 안의 그릇
  +-------+          +---------+          +----------+
  | blue  | -------> | false   | -------> | [lee]    |
  |       |          | true    | -------> | [jung]   |
  +-------+          +---------+          +----------+
  | green | -------> | true    | -------> | [choi]   |   <- false 칸이 없다
  +-------+          +---------+              (groupingBy 라서)
  | red   | -------> | false   | -------> | [kim]    |
  |       |          | true    | -------> | [park]   |
  +-------+          +---------+          +----------+
```

그림 해설 (한 단계씩):

- 다운스트림 자리에 `groupingBy` 를 또 넣으면 **2단**이 된다. 깊이 제한은 없다.
- `green` 에 `false` 칸이 없는 것을 보라 — **안쪽도 `groupingBy` 라서** 빈 칸이 안 생긴다.\
  안쪽을 `partitioningBy` 로 바꾸면 `green` 도 `{false=[], true=[choi]}` 가 된다.
- **`teeing`(12+)은 한 번의 순회로 수집기 둘을 동시에 돌리고 끝에 합친다.**

```java
teeing(counting(), summingInt(P::score), (c, s) -> c + "명 합계 " + s)   // "5명 합계 150"
```

- 평균을 직접 계산하거나, 최소·최대를 한 번에 얻을 때 쓴다.\
  `teeing(minBy(...), maxBy(...), (lo, hi) -> lo.get().score() + "~" + hi.get().score())` → `20~50`.
- `flatMapping`(9+)은 원소 하나에서 **여러 개를 칸에 쏟는다** — 다운스트림판 `flatMap` 이다.

비용 — 전부 **소스 순회 한 번**이다.\
`teeing` 이 없으면 같은 스트림을 두 번 만들어야 한다(스트림은 재사용 불가 — 46번 6번).

## 문법 — 형태와 규칙

직접 쓴 최소 예제다. 출력은 전부 실행 결과다.

### `groupingBy` 세 형태

```java
groupingBy(분류함수)                          // Map<K, List<T>>,  HashMap + ArrayList
groupingBy(분류함수, 다운스트림)               // Map<K, D>,        HashMap
groupingBy(분류함수, 맵팩토리, 다운스트림)      // M extends Map<K,D>
```

- **2인자와 3인자의 두 번째 인자가 서로 다르다.** 2인자는 다운스트림, 3인자는 맵 팩토리다.
- 3인자를 쓸 때는 **변수에 먼저 담는다**(47번 9번 — 오버로드된 메서드에 인라인하면 추론이 실패한다).

### `partitioningBy` 두 형태

```java
partitioningBy(술어)                 // Map<Boolean, List<T>>
partitioningBy(술어, 다운스트림)      // Map<Boolean, D>
```

- 맵 팩토리를 주는 형태가 **없다.** 칸이 둘로 고정이라 필요가 없다.

### 다운스트림 수집기 지도

| 하고 싶은 일 | 다운스트림 | 버전 |
|---|---|---|
| 원소 목록 | `toList()` (기본값) | 8 |
| 중복 없이 | `toSet()` / `toCollection(TreeSet::new)` | 8 |
| 개수 | `counting()` → `Long` | 8 |
| 합·평균 | `summingInt` / `averagingInt` 등 | 8 |
| 통계 한 번에 | `summarizingInt` 등 | 8 |
| 변환해서 담기 | `mapping(함수, 다운스트림)` | 8 |
| 최소·최대 | `minBy` / `maxBy` → `Optional` | 8 |
| `Optional` 벗기기·후처리 | `collectingAndThen(수집기, 함수)` | 8 |
| 문자열 잇기 | `mapping(P::name, joining("+"))` | 8 |
| 조건에 맞는 것만 (빈 칸 유지) | **`filtering(술어, 다운스트림)`** | **9** |
| 하나에서 여러 개 쏟기 | **`flatMapping(함수, 다운스트림)`** | **9** |
| 또 나누기 | `groupingBy(...)` / `partitioningBy(...)` | 8 |
| 둘을 동시에 돌리고 합치기 | **`teeing(수집기1, 수집기2, 합치기)`** | **12** |

### 분류 함수가 `null` 을 돌려주면

**실행 결과** (`Ex.java` — 48-a)

```text
== 분류 함수가 null 을 돌려주면 ==
예외 : java.lang.NullPointerException: element cannot be mapped to a null key
```

- **메시지가 있다.** 47번의 `toMap` NPE(메시지 없음)와 대조적이다.
- `groupingBy` 는 내부에서 `Objects.requireNonNull(key, "element cannot be mapped to a null key")` 를 부른다.
- 방어: 분류 함수가 `null` 을 낼 수 있으면 **기본 키로 바꾼다**(`"(없음)"` 등). `Optional` 키는 쓰지 않는다.

### `partitioningBy` 의 술어가 `null` 원소를 만나면

**실행 결과** (`Ex.java` — 48-c)

```text
partitioningBy null 원소 : java.lang.NullPointerException: Cannot invoke "String.length()" because "<parameter1>" is null
술어가 null 을 견디면    : {false=[a, null], true=[bb]}
```

- **`partitioningBy` 자신은 `null` 원소를 막지 않는다.** 술어가 터질 뿐이다.
- 술어를 `s != null && s.length() > 1` 로 쓰면 **`null` 원소가 `false` 칸에 담긴다.**
- 즉 `groupingBy`(키 `null` 금지)와 `partitioningBy`(원소 `null` 허용)의 계약이 다르다.

## 어디서 틀리나

### 1. `groupingBy` 결과에 `.get(키).size()` 를 부른다

```java
Map<String, List<P>> g = src.stream().collect(groupingBy(P::team));
int n = g.get("yellow").size();        // NullPointerException
```

- **그 키의 원소가 하나도 없으면 칸 자체가 없다.** `null` 이 나온다.
- 방어 셋 중 하나.

```java
g.getOrDefault("yellow", List.of()).size()                       // 1) 기본값
src.stream().collect(groupingBy(P::team, counting()))            // 2) 애초에 개수로 모은다
                                                                 //    (없는 팀은 여전히 없다)
Map<String,Long> base = allTeams.stream()                        // 3) 전체 키를 미리 채운다
        .collect(toMap(t -> t, t -> 0L));
base.putAll(src.stream().collect(groupingBy(P::team, counting())));
```

- **둘로 갈리는 조건이면 `partitioningBy` 를 쓴다** — 그쪽은 이 문제가 없다((5)).

### 2. 키 순서를 믿는다

```java
groupingBy(P::team)   // 화면에 그대로 뿌린다
```

- (2)에서 본 대로 **입력 순서도 정렬 순서도 아니다.**
- 더 나쁜 것은 **실행마다 바뀌지는 않는다**는 점이다 — 세 JDK 에서 같은 순서였다.\
  그래서 "확인해 봤는데 잘 나오던데요"가 통과해 버린다.
- 방어: 순서가 의미를 가지면 **3인자 형태로 `TreeMap::new`/`LinkedHashMap::new` 를 명시**한다.\
  또는 받는 쪽에서 정렬한다.

### 3. 2인자 `groupingBy` 에 맵 팩토리를 주려 한다

```java
groupingBy(P::team, TreeMap::new)             // 컴파일 에러 — 두 번째 인자는 다운스트림이다
groupingBy(P::team, TreeMap::new, toList())   // 이렇게 쓴다
```

```text
$ javac Ex.java
Ex.java:8: error: no suitable method found for groupingBy(P::team,TreeMap::new)
    method Collectors.<T#1,K#1>groupingBy(Function<? super T#1,? extends K#1>) is not applicable
      (cannot infer type-variable(s) T#1,K#1
        (actual and formal argument lists differ in length))
    method Collectors.<T#2,K#2,A#1,D#1>groupingBy(Function<? super T#2,? extends K#2>,Collector<? super T#2,A#1,D#1>) is not applicable
      (cannot infer type-variable(s) T#2,K#2,A#1,D#1
```

- 에러가 **후보 오버로드를 하나씩 세어 준다** — 2인자 형태의 둘째 인자가 `Collector` 라는 것이 거기 보인다.
- 3인자에서는 **다운스트림을 생략할 수 없다.** `toList()` 를 명시해야 한다.

### 4. 3인자 `groupingBy` 를 오버로드된 메서드에 인라인한다

```java
System.out.println(src.stream().collect(groupingBy(P::team, TreeMap::new, counting())));
```

```text
$ javac Ex.java
Ex.java:8: error: incompatible types: inference variable R has incompatible bounds
        System.out.println(SRC.stream().collect(Collectors.groupingBy(P::team, TreeMap::new, Collectors.counting())));
                                               ^
    upper bounds: String,Map<K#1,D>,Object
    lower bounds: TreeMap<K#2,V>
```

- 47번 9번과 **똑같은 원인**이다 — `println` 의 오버로드 때문에 `M` 이 안 정해진다.
- 방어: **변수에 먼저 담는다.**

### 5. `maxBy` 를 다운스트림으로 쓰고 `Optional` 이 박힌 맵을 받는다

```java
Map<String, Optional<P>> best = src.stream()
        .collect(groupingBy(P::team, maxBy(comparingInt(P::score))));
```

- 값 타입이 `Optional<P>` 다. **쓸 때마다 `.get()` 을 해야 한다.**
- 그런데 `groupingBy` 의 칸은 **비어 있을 수 없으므로**(원소가 있어야 칸이 생긴다) 그 `Optional` 은 **언제나 값이 있다.**\
  즉 이 `Optional` 은 정보가 없는 껍데기다.
- 방어: `collectingAndThen(maxBy(...), Optional::get)` 또는 `o -> o.map(P::name).orElse("-")`.

### 6. `filtering` 과 `filter` 를 같은 것으로 안다

- (4)에서 본 대로 **결과 맵의 키 집합이 다르다.**
- 특히 "전 팀 현황판"처럼 **0을 보여 줘야 하는 화면**에서 `filter` 를 쓰면 팀이 통째로 사라진다.
- 방어: **빈 그룹이 필요한지**를 먼저 묻는다. 필요하면 `filtering`(9+).

### 7. 그룹핑 결과를 수정하려 한다

```text
put(true) : java.lang.UnsupportedOperationException
put(null) : java.lang.UnsupportedOperationException
```

- `partitioningBy` 의 결과는 **수정 불가**다.
- `groupingBy` 의 결과(`HashMap`)는 지금은 수정 가능하지만 **보장이 아니다.**
- 방어: 결과를 고쳐야 하면 3인자로 **맵 팩토리를 내가 준다.**

## 구현 세부사항 대 언어 보장

| 관측한 것 | 보장인가 | 근거 |
|---|---|---|
| `partitioningBy` 결과에 `false`·`true` 둘 다 있다 | **보장** | javadoc: "always contains mappings for both" |
| 빈 파티션의 값이 **빈 리스트** | **보장** | javadoc `@apiNote` |
| `groupingBy` 결과가 `HashMap`, 값이 `ArrayList` | **보장 아님** | javadoc: "no guarantees on the type, mutability, …" |
| `groupingBy` 의 키 순서 | **보장 없음** | 위와 같다. 실측에서 입력·정렬 어느 쪽도 아니었다 |
| 칸 **안**의 원소 순서가 입력 순서 | **순차 스트림에서는 사실상 보장** | 패키지 javadoc 의 encounter order. 병렬은 49번 |
| 분류 함수가 `null` 이면 NPE + 그 메시지 | 예외는 사실상 보장, **메시지는 보장 아님** | 구현의 `requireNonNull` 메시지 |
| `partitioningBy` 결과 타입이 `Collectors$Partition` | **보장 아님** | javadoc 이 타입을 규정하지 않는다 |
| `partitioningBy` 결과가 수정 불가 | **보장 아님** | 위와 같다(다만 현재 구현은 던진다) |
| `groupingBy(f)` = `groupingBy(f, toList())` | **보장** | javadoc `@implSpec` |

**세 JDK 실측** — 프로그램 3개(48-a·b·c)를 17.0.13 · 21.0.5 · 25.0.1 에서 돌려 `diff` 했다.\
**한 글자도 다르지 않았다** — `HashMap` 의 키 순서(`[date, banana, honeydew, …]`)까지 같았다.

- 그래서 더 위험하다. **"세 버전에서 같았으니 보장"이 아니다.**\
  `String.hashCode` 는 명세에 박혀 있지만 `HashMap` 의 **순회 순서**는 그렇지 않다.

## 언제 쓰고 언제 안 쓰나

| 하고 싶은 일 | 고를 것 |
|---|---|
| 속성으로 묶기 | `groupingBy(f)` |
| 조건으로 둘로 가르기 | **`partitioningBy(p)`** — 빈 쪽도 남는다 |
| 그룹별 개수 | `groupingBy(f, counting())` |
| 그룹별 이름 목록 | `groupingBy(f, mapping(P::name, toList()))` |
| 그룹별 대표 하나 | `groupingBy(f, collectingAndThen(maxBy(cmp), Optional::get))` |
| 키 순서가 필요 | 3인자 + `TreeMap::new` 또는 `LinkedHashMap::new` |
| 빈 그룹을 남겨야 함 | `filtering(p, 다운스트림)` (9+) |
| 그룹이 아예 없어도 됨 | `filter(p)` 를 앞에 |
| 2차원 집계 | 다운스트림에 `groupingBy` 를 또 |
| 한 번에 두 집계 | `teeing(c1, c2, 합치기)` (12+) |
| 키가 `null` 일 수 있음 | **분류 함수에서 기본 키로 바꾼다** — 안 그러면 NPE |
| 그룹이 아주 많고 병렬 | `groupingByConcurrent` — 단 순서를 잃는다([`../49-parallel-streams/`](../49-parallel-streams/)) |
| 그룹이 하나뿐 | 그룹핑을 안 한다. 47번의 기본 수집기로 |

판단 규칙 세 줄.

- **둘로 갈리면 `partitioningBy`.** `groupingBy` 로 `Boolean` 키를 쓰면 빈 쪽이 사라진다.
- **키 순서가 화면에 보이면 맵 팩토리를 명시한다.** 기본값은 순서가 없다.
- **빈 그룹이 필요한지 먼저 묻는다.** 그 답이 `filtering` 과 `filter` 를 가른다.

## 핵심 문장

- `groupingBy` 의 기본값은 **`HashMap` + `ArrayList`** 이고 **둘 다 보장이 아니다.** 순서가 필요하면 3인자로 명시한다.
- **`groupingBy` 는 원소가 있는 칸만 만들고, `partitioningBy` 는 언제나 두 칸을 만든다.** 이것이 두 메서드의 진짜 차이다.
- **다운스트림은 칸 안에서 다시 `collect` 를 돌리는 것**이다 — 47번의 수집기가 전부 그 자리에 들어간다.
- **`filtering`(9+)과 `filter` 는 결과의 키 집합이 다르다.** 빈 그룹을 남기느냐가 갈린다.
- 분류 함수가 `null` 을 돌려주면 **`element cannot be mapped to a null key`** 로 터진다 — 메시지가 있는 NPE 다.

## 관련 자료

- [`../47-collectors-basics/`](../47-collectors-basics/) — **이 주제의 선행.** 다운스트림 자리에 들어가는 수집기들이 전부 거기 있다
- [`../46-terminal-operations/`](../46-terminal-operations/) — `collect` 가 최종 연산이라는 것, 스트림이 일회용이라는 것(`teeing` 이 필요한 이유)
- [`../49-parallel-streams/`](../49-parallel-streams/) — `groupingBy` 대 `groupingByConcurrent`, 맵 결합 비용. 그쪽은 **스레드·측정**까지, 여기는 **조합의 문법**까지
- [`../45-intermediate-operations/`](../45-intermediate-operations/) — `flatMapping` 의 원본인 `flatMap`
- [`../../../../../data-structure/05-hashmap/`](../../../../../data-structure/05-hashmap/) — `HashMap` 의 키 순서가 **왜** 그런지는 거기가 정본. 그쪽은 **버킷·해시 배치**까지, 여기는 **그래서 믿으면 안 된다**부터
- [`../../../../../data-structure/06-binary-search-tree/`](../../../../../data-structure/06-binary-search-tree/) — `TreeMap` 이 정렬 순서를 유지하는 원리
- [`../27-equals-hashcode-contract/`](../27-equals-hashcode-contract/) — 분류 함수가 돌려주는 키가 지켜야 하는 계약
- [`../README.md`](../README.md) — Java 문법·API 주제 목록(이 주제는 48번)
- 목록의 **41번 주제**(`Map` API) — `getOrDefault`·`merge`. 「어디서 틀리나」 1번의 방어
- 목록의 **39번 주제**(컬렉션 지도) — `TreeMap`·`LinkedHashMap` 을 언제 고르나
- [**28번 주제**](../28-comparable-comparator/)(`Comparator`) — `maxBy`/`minBy`/`TreeMap` 에 넘기는 비교자

## 용어 풀이

- **분류 함수(classifier)** — 원소를 보고 키를 정하는 함수. `groupingBy` 의 첫 인자. `null` 을 돌려주면 NPE 다.
- **다운스트림(downstream)** — 한 그룹 안의 원소들을 다시 모으는 수집기. 47번의 수집기가 전부 여기 들어간다.
- **맵 팩토리(map factory)** — 결과 맵을 만드는 공급자. `TreeMap::new` 처럼 준다. 3인자 `groupingBy` 의 둘째 인자.
- **분할(partition)** — 조건으로 둘로 가르는 것. 결과는 `Map<Boolean, ?>` 이고 **두 키가 항상 있다**.
- **`mapping`** — 담기 전에 원소를 변환하는 다운스트림. 그룹 안에서 `map` 을 하는 것과 같다.
- **`filtering`(9+)** — 담기 전에 거르는 다운스트림. `filter` 와 달리 **빈 그룹이 남는다**.
- **`flatMapping`(9+)** — 원소 하나에서 여러 개를 그룹에 쏟는 다운스트림.
- **`teeing`(12+)** — 수집기 둘을 한 번의 순회로 돌리고 결과를 합치는 수집기. 이름은 배관의 T 자 이음쇠에서 왔다.
- **`collectingAndThen`** — 다 모은 뒤 한 번 더 변환하는 것. `Optional` 을 벗기거나 불변으로 감쌀 때 쓴다.
- **입력 순서(encounter order)** — 소스가 원소를 내놓는 순서. 그룹 **안**의 순서는 이것을 따른다(순차 기준).

## 더 들어가면

- **`groupingBy` 의 2인자·3인자는 결국 같은 코드로 간다.**\
  1인자는 `groupingBy(classifier, toList())`, 2인자는 `groupingBy(classifier, HashMap::new, downstream)` 이다.\
  javadoc 의 `@implSpec` 이 1인자에 대해 그것을 명시한다.
- **`groupingBy` 는 `CONCURRENT` 가 아니다.**\
  실측: `Collectors.groupingBy(P::team).characteristics()` → `[IDENTITY_FINISH]`,\
  `groupingByConcurrent(P::team).characteristics()` → `[CONCURRENT, UNORDERED, IDENTITY_FINISH]`.\
  그래서 병렬에서 `groupingBy` 는 **조각마다 맵을 만들어 합친다** — javadoc 이 "can be an expensive operation" 이라 적는다.\
  대신 `groupingByConcurrent` 는 **그룹 안의 순서를 잃는다.** 실측과 측정은 49번이 정본이다.
- **`partitioningBy` 의 다운스트림에 `partitioningBy` 를 넣으면 2×2 표**가 된다.\
  `{false={false=[...], true=[...]}, true={false=[...], true=[...]}}` — 네 칸이 언제나 다 있다.\
  `groupingBy` 로 만든 2차원 표에는 **없는 칸이 생긴다.** 표를 그릴 거면 `partitioningBy` 쪽이 안전하다.
- **`teeing` 은 Java 12 에서 들어왔다.**\
  그 전에는 같은 데이터에 수집기 둘을 돌리려면 **컬렉션으로 한 번 받아 두고 스트림을 두 번 만들어야** 했다.\
  스트림이 일회용이기 때문이다(46번 6번). `teeing` 은 그 왕복을 없앤다.
