# java/syntax/48 — `Collectors` 그룹핑·분할·다운스트림 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·에러는 **Temurin JDK 21.0.5 에서 실제로 돌려 얻은 것**이다.\
> 소스·javadoc 인용은 `lib/src.zip` 의 `java.base/java/util/stream/Collectors.java` 원문이다.\
> 프로그램 4개를 17.0.13 · 25.0.1 에서도 돌렸다 — **출력이 한 글자도 다르지 않았다**(2번).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. `groupingBy` 의 기본값

**출력** (`Ex.java` — 48-a, 17·21·25 동일)

```text
== groupingBy 기본 ==
맵 타입   : java.util.HashMap
값 타입   : java.util.ArrayList
키 순서   : [red, green, blue]
red       : [kim, park]
```

**구체 타입**

- 맵 → **`java.util.HashMap`**, 값 → **`java.util.ArrayList`**.

**보장인가**

- **아니다.** javadoc 이 명시적으로 부정한다.

> There are no guarantees on the type, mutability, serializability, or thread-safety of the `Map` or `List` objects returned.

- 그래서 `((HashMap<?,?>) g)` 캐스팅도, "값이 `ArrayList` 니까 `sort` 해도 된다"도 쓰면 안 된다.

**`g.get("red")` 의 순서**

- **`[kim, park]`** — 입력에 나온 순서다.
- 칸 **안**의 순서는 입력 순서(encounter order)를 따른다.\
  칸 **자체**의 순서는 보장이 없다(2번). 이 둘을 헷갈리지 않는다.

**1인자는 무엇과 같은가**

```java
groupingBy(classifier)  ==  groupingBy(classifier, toList())
```

- javadoc 의 `@implSpec` 이 그렇게 적는다.

> This produces a result similar to: `groupingBy(classifier, toList());`

### 2. 키 순서를 예측하라

**출력** (`Ex.java` — 48-a, 17·21·25 동일)

```text
== 키 순서는 보장이 아니다 ==
입력 순서 : [apple, banana, cherry, date, elderberry, fig, grape, honeydew]
맵 순서   : [date, banana, honeydew, cherry, apple, fig, grape, elderberry]
```

**입력 순서인가 정렬 순서인가**

- **둘 다 아니다.**

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

  해시값이 버킷 자리를 정하고, 그 자리 순서로 순회한다
```

**다시 돌리면 바뀌는가**

- **안 바뀐다.** `String.hashCode` 가 결정적이기 때문이다.

**17·21·25 에서는**

- **셋 다 같았다.** `diff` 로 확인했다.

**그 안정성이 왜 위험한가**

- "돌려 보니 항상 같더라"가 **「보장」으로 오해**되기 때문이다.
- 그런데 이 순서는 **키 하나만 추가해도, 맵 크기(버킷 수)가 바뀌어도** 달라진다.
- 즉 **테스트는 통과하는데 데이터가 늘면 화면 순서가 바뀐다.**\
  실행마다 바뀌었다면 오히려 개발 중에 잡혔을 것이다.
- `HashMap` 이 왜 그 순서인지는 [`../../../../../data-structure/05-hashmap/`](../../../../../data-structure/05-hashmap/) 이 정본이다.

**순서가 필요하면**

```java
// 정렬 순서
groupingBy(P::team, TreeMap::new, mapping(P::name, toList()))
// 입력에서 처음 나온 순서
groupingBy(P::team, LinkedHashMap::new, mapping(P::name, toList()))
```

**출력** (`Ex.java` — 48-a)

```text
TreeMap       : {blue=[lee, jung], green=[choi], red=[kim, park]}
LinkedHashMap : {red=[kim, park], blue=[lee, jung], green=[choi]}
```

### 3. `partitioningBy` 가 `groupingBy` 와 다른 점

**출력** (`Ex.java` — 48-c)

```text
== 항상 두 칸이다 ==
아무도 통과 못 함     : {false=[P[team=red, name=kim, score=10], P[team=blue, name=lee, score=20], P[team=red, name=park, score=30], P[team=green, name=choi, score=40], P[team=blue, name=jung, score=50]], true=[]} / 크기 2
빈 스트림            : {false=[], true=[]} / 크기 2
== groupingBy 로 같은 일을 하면 ==
groupingBy 아무도 통과 못 함 : {false=[P[team=red, name=kim, score=10], P[team=blue, name=lee, score=20], P[team=red, name=park, score=30], P[team=green, name=choi, score=40], P[team=blue, name=jung, score=50]]} / 크기 1
g.get(true)          : null
part.get(true)       : []
== 이 맵은 수정할 수 있나 ==
put(true) : java.lang.UnsupportedOperationException
put(null) : java.lang.UnsupportedOperationException
```

**크기**

- (A) `partitioningBy` → **2**
- (B) `groupingBy` → **1**

**`.get(true)`**

- (A) → **`[]`** (빈 리스트)
- (B) → **`null`**

```text
partitioningBy(p)                          groupingBy(t -> p.test(t))

  {false=[...], true=[]}                     {false=[...]}
  크기 언제나 2                                통과한 쪽만 생긴다
  get(true) -> []                            get(true) -> null
        |                                          |
        v                                          v
  .size() 가 안전하다                          .size() 가 NPE 를 낸다
```

**빈 스트림에 (A)**

- **`{false=[], true=[]}`** — 크기 2. 원소가 하나도 없어도 두 칸이 다 있다.

**javadoc 근거**

> The returned `Map` **always contains mappings for both `false` and `true` keys.**

> (`@apiNote`) If a partition has no elements, its value in the result Map will be an empty List.

**`put` 을 하면**

- **`UnsupportedOperationException`** 이다. `put(true, ...)` 도 `put(null, ...)` 도.
- 반환 타입은 실측 `java.util.stream.Collectors$Partition` — **타입도 수정 불가도 javadoc 이 보장하지 않는다.**\
  보장되는 것은 "두 키가 항상 있다"까지다.

### 4. 다운스트림으로 무엇이 나오는가

**출력** (`Ex.java` — 48-b)

```text
counting        : {blue=2, green=1, red=2}
summingInt      : {blue=70, green=40, red=40}
averagingInt    : {blue=35.0, green=40.0, red=20.0}
joining         : {blue=lee+jung, green=choi, red=kim+park}
```

**네 줄**

| 다운스트림 | 결과 |
|---|---|
| `counting()` | `{blue=2, green=1, red=2}` |
| `summingInt(P::score)` | `{blue=70, green=40, red=40}` |
| `averagingInt(P::score)` | `{blue=35.0, green=40.0, red=20.0}` |
| `mapping(P::name, joining("+"))` | `{blue=lee+jung, green=choi, red=kim+park}` |

```text
groupingBy(P::team, TreeMap::new, 다운스트림)

  선반 (TreeMap — 키가 정렬된다)
   +--------+--------+--------+
   | blue   | green  | red    |
   +--------+--------+--------+
   | lee    | choi   | kim    |     <- 칸에 들어온 원소들이
   | jung   |        | park   |        다운스트림 수집기로 다시 들어간다
   +--------+--------+--------+
      |         |        |
  counting()   1        2            <- 칸마다 따로 센다
      2
```

**`counting()` 의 값 타입**

- **`Long`** 이다. `Integer` 가 아니다 — `{blue=2, …}` 의 `2` 는 `Long` 이다.
- `Map<String, Integer>` 로 받으면 컴파일 에러가 난다.

**왜 `TreeMap::new` 를 넣었는가**

- 기본 `HashMap` 은 **키 순서가 없어서** 문서에 출력을 그대로 실을 수 없기 때문이다(2번).
- 출력을 재현 가능하게 만들려는 목적이지, `TreeMap` 이 필요해서가 아니다.

**소스를 몇 번 읽는가**

- **한 번.** 다운스트림이 몇 겹이든, `teeing` 으로 둘을 돌리든 순회는 한 번이다.
- 이것이 그룹핑을 스트림으로 하는 가장 큰 이유다.

### 5. `maxBy` 를 다운스트림으로

**출력** (`Ex.java` — 48-b)

```text
maxBy           : {blue=Optional[P[team=blue, name=jung, score=50]], green=Optional[P[team=green, name=choi, score=40]], red=Optional[P[team=red, name=park, score=30]]}
collectingAndThen : {blue=jung, green=choi, red=park}
```

**값 타입**

- **`Optional<P>`** 다.

**비어 있을 수 있는가**

- **없다.**

```text
groupingBy 는 원소가 있어야 칸을 만든다
        |
        v
  칸이 존재한다  ->  그 칸에 원소가 최소 하나 있다
        |
        v
  maxBy 는 반드시 값을 찾는다  ->  Optional 이 절대 비지 않는다
```

- 즉 **정보가 없는 껍데기 `Optional`** 이다. 쓰는 쪽만 번거로워진다.
- (`partitioningBy` 의 다운스트림이면 이야기가 다르다 — 빈 칸이 있으므로 `Optional.empty` 가 나온다.)

**이름만 얻으려면**

```java
groupingBy(P::team, TreeMap::new,
        collectingAndThen(maxBy(comparingInt(P::score)), o -> o.map(P::name).orElse("-")))
// {blue=jung, green=choi, red=park}
```

- `Optional::get` 만 써도 되지만, `partitioningBy` 로 바꿨을 때 터진다.\
  `o -> o.map(...).orElse(...)` 쪽이 안전하다.

### 6. `filtering` 과 `filter`

**출력** (`Ex.java` — 48-b, 조건 `score >= 40`)

```text
filtering 다운스트림 : {blue=[jung], green=[choi], red=[]}
filter 를 앞에      : {blue=[jung], green=[choi]}
```

**두 결과**

- (A) `filtering` → `{blue=[jung], green=[choi], red=[]}`
- (B) `filter` → `{blue=[jung], green=[choi]}`

**어느 키가 한쪽에만 있는가**

- **`red`** 다. `red` 의 두 명(10·30)이 전부 조건에 안 맞는다.

```text
filtering 다운스트림                       filter 를 앞에

  원소 5개가 전부 분류된다                   조건에 맞는 2개만 남는다
        |                                          |
  red 칸이 만들어지고                         red 원소가 없으니
  담을 게 없어 빈 리스트로 남는다               red 칸이 아예 안 만들어진다
        |                                          |
        v                                          v
  {blue=[jung], green=[choi], red=[]}       {blue=[jung], green=[choi]}
```

**어느 쪽을 언제**

- **빈 그룹이 필요하면 `filtering`** — "전 팀 현황판"처럼 0명도 보여야 하는 화면.
- **그룹이 아예 없어도 되면 `filter`** — 조금 싸다(걸러진 원소가 분류 함수를 안 거친다).
- 이 차이 때문에 `filtering` 이 추가됐다. **`filter` 로는 만들 수 없는 결과**가 있다.

**버전**

- **Java 9**. `flatMapping` 도 같은 9다.

### 7. 2단 그룹핑

**출력** (`Ex.java` — 48-b)

```text
2단 그룹핑       : {blue={false=[lee], true=[jung]}, green={true=[choi]}, red={false=[kim], true=[park]}}
```

**결과**

```text
{blue={false=[lee], true=[jung]},
 green={true=[choi]},
 red={false=[kim], true=[park]}}
```

**`green` 의 칸 수**

- **한 개**다. `{true=[choi]}` 뿐이다.
- `green` 에는 `choi`(40점) 하나뿐이고 그가 조건(30 이상)을 통과하므로 **`false` 칸이 안 생긴다.**
- **안쪽도 `groupingBy` 이기 때문**이다.

**안쪽을 `partitioningBy` 로 바꾸면**

**출력** (`Ex.java` — 48-f, 17·21·25 동일)

```text
{blue={false=[lee], true=[jung]}, green={false=[], true=[choi]}, red={false=[kim], true=[park]}}
```

- `green` 에 **`false=[]` 가 생겼다.** 모든 팀이 두 칸을 갖는다.

```text
안쪽이 groupingBy                          안쪽이 partitioningBy

  blue  | false true                        blue  | false true
  green |       true    <- 구멍             green | false true
  red   | false true                        red   | false true

  표를 그리면 칸이 빈다                      직사각형 표가 된다
```

- **표를 만들 거면 `partitioningBy` 쪽이 안전하다.**
- 바깥까지 `partitioningBy` 면 네 칸이 언제나 다 있다.\
  실측: `{false={false=[kim, lee], true=[]}, true={false=[park, jung], true=[choi]}}`.

**깊이 제한**

- **없다.** 다운스트림 자리에 수집기를 계속 중첩할 수 있다.
- 다만 3단을 넘어가면 **결과 타입이 읽을 수 없게 된다** — 그때는 `record` 로 키를 만들어 1단으로 푸는 쪽이 낫다.

### 8. `teeing`

**출력** (`Ex.java` — 48-b)

```text
teeing          : 5명 합계 150
teeing 다운스트림 : {blue=20~50, green=40~40, red=10~30}
```

**결과**

- **`5명 합계 150`**.

**버전**

- **Java 12**.

**그 전에는**

```java
// 스트림을 두 번 만들어야 했다 — 소스를 두 번 읽는다
long c = src.stream().count();
int  s = src.stream().mapToInt(P::score).sum();
```

- 또는 한 번 `toList()` 로 받아 두고 그 리스트로 두 번 스트림을 만들었다.

**왜 스트림을 두 번 쓸 수 없는가**

- **스트림은 일회용**이기 때문이다(46번 6번).

```java
Stream<P> s = src.stream();
s.count();
s.mapToInt(P::score).sum();   // IllegalStateException: stream has already been operated upon or closed
```

- `teeing` 은 이 제약을 **한 번의 순회 안에서** 푼 것이다.\
  수집기 둘에 같은 원소를 동시에 먹이고, 끝에 두 결과를 합친다.

```text
teeing(counting(), summingInt(score), (c, s) -> ...)

  원소 하나가 들어온다
        |
   +----+----+
   |         |
 counting  summingInt      <- 둘 다에게 같은 원소를 준다
   |         |
   5        150
   +----+----+
        |
   합치기 함수 -> "5명 합계 150"
```

### 9. 분류 함수가 `null` 을 돌려주면

**출력** (`Ex.java` — 48-a)

```text
== 분류 함수가 null 을 돌려주면 ==
예외 : java.lang.NullPointerException: element cannot be mapped to a null key
```

**무엇이 던져지는가**

- **`NullPointerException`**.

**메시지가 있는가**

- **있다.** `element cannot be mapped to a null key`.

**`toMap` 의 `null` 값 예외와 비교하면**

```text
groupingBy 의 null 키                      toMap 의 null 값 (2인자)

  NullPointerException:                     NullPointerException
    element cannot be mapped                  (메시지 없음)
    to a null key
        |                                          |
        v                                          v
  메시지만 보고 원인을 안다                    스택트레이스를 봐야 안다
```

- 같은 `NullPointerException` 인데 **진단 가능성이 다르다.**
- `groupingBy` 는 **키**를 막고 `toMap` 은 **값**을 막는다는 점도 대칭이 아니다.\
  (`toMap` 은 키가 `null` 이어도 통과한다 — 47번 3번.)

**방어**

```java
// 기본 키로 바꾼다
groupingBy(p -> p.team() == null ? "(없음)" : p.team())
```

- `Optional` 을 키로 쓰지 않는다 — 맵 키가 `Optional` 이면 쓰는 쪽이 전부 번거로워진다.

### 10. `partitioningBy` 에 `null` 원소가 들어오면

**출력** (`Ex.java` — 48-c)

```text
partitioningBy null 원소 : java.lang.NullPointerException: Cannot invoke "String.length()" because "<parameter1>" is null
술어가 null 을 견디면    : {false=[a, null], true=[bb]}
```

**무엇이 던져지는가**

- **`NullPointerException`** — 단 메시지가 `String.length()` 를 가리킨다.

**던지는 것은 누구인가**

- **술어다.** `partitioningBy` 자신은 `null` 원소를 막지 않는다.
- 메시지의 `Cannot invoke "String.length()" because "<parameter1>" is null` 이 그 증거다 — 내 람다 안에서 났다.

**술어를 고치면**

- **`{false=[a, null], true=[bb]}`** — `null` 원소가 `false` 칸에 얌전히 담긴다.

**`groupingBy` 와 계약이 어떻게 다른가**

```text
groupingBy                                 partitioningBy

  키가 null 이면 -> 라이브러리가 던진다        원소가 null 이어도 -> 통과한다
  "element cannot be mapped                  (술어만 견디면 된다)
   to a null key"
        |                                          |
        v                                          v
  null 키를 표현할 수 없다                     null 원소를 담을 수 있다
```

- 대칭이 아니다. **`groupingBy` 는 키를 검사하고 `partitioningBy` 는 아무것도 검사하지 않는다.**
- 이유: `partitioningBy` 의 키는 술어가 만든 `boolean` 이라 `null` 이 될 수 없다.

### 11. 이 두 줄은 왜 컴파일이 안 되는가

**(A)의 에러** (`javac`, JDK 21.0.5)

```text
$ javac Ex.java
Ex.java:8: error: no suitable method found for groupingBy(P::team,TreeMap::new)
        Map<String, List<P>> m = SRC.stream().collect(Collectors.groupingBy(P::team, TreeMap::new));
                                                                ^
    method Collectors.<T#1,K#1>groupingBy(Function<? super T#1,? extends K#1>) is not applicable
      (cannot infer type-variable(s) T#1,K#1
        (actual and formal argument lists differ in length))
    method Collectors.<T#2,K#2,A#1,D#1>groupingBy(Function<? super T#2,? extends K#2>,Collector<? super T#2,A#1,D#1>) is not applicable
      (cannot infer type-variable(s) T#2,K#2,A#1,D#1
```

- 원인: **2인자 `groupingBy` 의 둘째 인자는 맵 팩토리가 아니라 다운스트림(`Collector`)** 이다.
- 에러가 후보 오버로드를 세어 준다 — 1인자는 인자 수가 안 맞고, 2인자는 `Collector` 를 요구한다.

**(B)의 에러**

```text
$ javac Ex.java
Ex.java:8: error: incompatible types: inference variable R has incompatible bounds
        System.out.println(SRC.stream().collect(Collectors.groupingBy(P::team, TreeMap::new, Collectors.counting())));
                                               ^
    upper bounds: String,Map<K#1,D>,Object
    lower bounds: TreeMap<K#2,V>
```

- 원인: **`println` 의 오버로드** 때문에 대상 타입이 하나로 안 정해져 `M` 이 추론되지 않는다.
- `upper bounds: String, Map<K,D>, Object` 가 그 증거다 — 세 후보를 동시에 요구받고 있다.

**같은 원인인가**

- **아니다.**

```text
(A) 인자 개수·타입이 안 맞는다              (B) 인자는 맞는데 반환 타입이 안 정해진다
    -> 오버로드 선택 실패                       -> 타입 추론 실패
    "no suitable method found"                 "inference variable R has
                                                incompatible bounds"
```

**고치는 법**

```java
// (A) 다운스트림을 명시한다
Map<String, List<P>> m = SRC.stream()
        .collect(Collectors.groupingBy(P::team, TreeMap::new, Collectors.toList()));

// (B) 변수에 먼저 담는다
TreeMap<String, Long> c = SRC.stream()
        .collect(Collectors.groupingBy(P::team, TreeMap::new, Collectors.counting()));
System.out.println(c);
```

- (B)는 47번 9번(4인자 `toMap`)과 **똑같은 실패 모드**다. 맵 팩토리를 받는 수집기에서 반복된다.

### 12. 이 코드의 버그를 찾아라

**출력** (`Ex.java` — 48-f, 17·21·25 동일)

```text
red : 2
blue : 2
green : 1
Exception in thread "main" java.lang.NullPointerException: Cannot invoke "java.util.List.size()" because the return value of "java.util.Map.get(Object)" is null
	at Ex.main(Ex.java:26)
```

**무엇이 터지는가**

- `yellow` 차례에서 **`NullPointerException`**.

**왜**

- **`yellow` 팀 원소가 하나도 없어서 그 칸이 아예 안 만들어졌다.**
- `groupingBy` 는 **원소를 본 뒤에** 칸을 만든다. 없는 키는 없는 키다.
- 도움말 NPE(14+) 덕에 메시지가 원인을 정확히 가리킨다 — `the return value of "java.util.Map.get(Object)" is null`.

```text
앞의 세 줄은 잘 나온다                      네 번째에서 터진다

  red   : 2                                  yellow -> byTeam.get("yellow") = null
  blue  : 2                                            null.size()  ->  NPE
  green : 1
        |
   부분적으로 성공한 뒤 터진다 — 반쯤 출력된 화면이 남는다
```

**고치는 방법 셋**

```java
// 1) 기본값을 준다
byTeam.getOrDefault(team, List.of()).size()

// 2) 개수로 모으고 같은 방어를 쓴다
Map<String, Long> cnt = SRC.stream().collect(groupingBy(P::team, counting()));
cnt.getOrDefault(team, 0L)

// 3) 전체 키를 미리 채워 둔다
Map<String, Long> base = new LinkedHashMap<>();
for (String t : ALL_TEAMS) base.put(t, 0L);
base.putAll(SRC.stream().collect(groupingBy(P::team, counting())));
```

- 세 번째가 "전 팀 현황판" 요구사항에 맞는 답이다 — **없는 팀도 0으로 보여야** 하기 때문이다.

**조건이 둘로 갈렸다면**

- **`partitioningBy`** 를 썼어야 한다.
- 그쪽은 빈 칸도 **빈 리스트**로 남으므로 이 버그가 구조적으로 불가능하다(3번).

---

## 실행 검증

| 프로그램 | 무엇을 확인했나 | 돌린 JDK |
|---|---|---|
| `Ex.java` (48-a) | `groupingBy` 기본 타입·값 타입·키 순서, 8개 키의 `HashMap` 순회 순서, `TreeMap`/`LinkedHashMap` 지정, 빈 그룹이 안 생김, 분류 함수 `null` 의 NPE 메시지 | 17 · 21 · 25 (**한 글자도 동일**) |
| `Ex.java` (48-b) | 다운스트림 11가지(`counting`·`mapping`·`summingInt`·`averagingInt`·`summarizingInt`·`joining`·`maxBy`·`collectingAndThen`·`toCollection`·`filtering`·`flatMapping`), 2단 그룹핑, `teeing` 둘 | 17 · 21 · 25 (**동일**) |
| `Ex.java` (48-c) | `partitioningBy` 의 두 칸 보장(세 경우), 맵 타입·수정 불가, `groupingBy` 와의 `get(true)` 대비, 2단 분할, 술어의 `null` 원소 | 17 · 21 · 25 (**동일**) |
| `Ex.java` (48-f) | 안쪽을 `partitioningBy` 로 바꾼 2단, 분할 안 분할(네 칸), 없는 키에 `get().size()` 의 NPE | 17 · 21 · 25 (**동일**) |
| `javac` 단독 (48-d) | 3인자 `groupingBy` 를 `println` 에 인라인했을 때의 추론 실패 | 21 |
| `javac` 단독 (48-e) | 2인자 `groupingBy` 에 맵 팩토리를 줬을 때의 오버로드 선택 실패 | 21 |
| `src.zip` 열람 | `groupingBy` 의 `@implSpec`·`@implNote`, `partitioningBy` 의 "always contains mappings for both" | 21 |

**구현 의존 항목** (버전이 오르면 다시 돌려야 하는 것)

- `HashMap` 의 키 순회 순서 — 세 JDK 에서 같았지만 **보장이 아니다.** 키 집합이 바뀌면 순서도 바뀐다.
- 구체 타입 `HashMap`·`ArrayList`·`Collectors$Partition` — javadoc 이 보장하지 않는다.
- `partitioningBy` 결과가 수정 불가인 것 — 현재 구현의 성질이다.
- 분류 함수 `null` 의 **메시지 문구**(`element cannot be mapped to a null key`).
- `javac` 에러 메시지의 문구와 줄 번호 — 컴파일러 버전에 달려 있다.
- **Java 8 의 동작은 안 돌려 봄** — 이 머신에 8이 없다. `filtering`·`flatMapping`(9+)·`teeing`(12+)은 애초에 8에 없다.
