# java/syntax/47 — `Collectors`: 기본 수집기와 `toMap` 의 함정 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **선행** — [`../46-terminal-operations/`](../46-terminal-operations/). `collect` 가 최종 연산이라는 것을 먼저 본다.
> **기준 소스** — [`Collectors` javadoc (Java SE 21)](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/stream/Collectors.html) · JDK 21.0.5 표준 라이브러리 소스 `java.base/java/util/stream/Collectors.java`(`lib/src.zip`)
> **실행 검증** — 이 문서의 모든 출력·에러는 Temurin **JDK 21.0.5** 에서 실제로 돌려 얻은 것이다.\
> 같은 프로그램 5개를 **17.0.13 · 25.0.1** 에서도 돌렸다. **예외 메시지는 같고 스택트레이스 줄 번호만 달랐다.**
> **버전** — `Collectors` 는 **Java 8**. `toUnmodifiableList`/`Set`/`Map` 은 **Java 10**. `Stream.toList()` 는 **Java 16**.\
> 17·21·25 동작 동일.
> **범위** — 그룹핑·분할·다운스트림 조합은 [`../48-collectors-grouping/`](../48-collectors-grouping/) 이 정본이다.\
> 그쪽은 **키로 나누는 것**부터, 여기는 **나누지 않고 하나로 모으는 것**까지다.\
> `HashMap` 의 내부(버킷·충돌)는 [`../../../../../data-structure/05-hashmap/`](../../../../../data-structure/05-hashmap/) 이 정본이다.\
> 그쪽은 **해시가 어떻게 자리를 찾나**까지, 여기는 **`Collectors` 가 그 위에 무엇을 얹었나**부터다.
> 이 본문은 Claude 작성이다(원고 없음).

## 한눈에 — 쉽게 말하면

**수집기는 벨트 끝에 놓는 그릇이다.**

44~46번의 비유를 그대로 잇는다.

| 비유 | 실체 |
|---|---|
| 벨트 끝의 시동 스위치 | 최종 연산 `collect` — 46번 |
| **스위치 아래 놓는 그릇** | **수집기 `Collector` — 이 주제** |
| 상자에 차곡차곡 담는 그릇 | `toList()`·`toSet()` |
| **이름표를 붙여 칸칸이 담는 그릇** | **`toMap()`** |
| 담기 전에 개수만 세는 그릇 | `counting()` |
| 담기 전에 무게만 더하는 그릇 | `summingInt()`·`averagingDouble()` |
| 전부 한 줄로 이어 붙이는 그릇 | `joining()` |
| 다 담은 뒤 뚜껑을 덮는 그릇 | `collectingAndThen()` |

- 그릇은 대부분 얌전하다. 담으면 담긴다.
- **딱 하나 까다로운 그릇이 `toMap`** 이다.\
  이름표가 **겹치면 던지고**, 내용물이 **비어 있어도 던진다.**
- 같은 일을 `HashMap.put` 으로 하면 **둘 다 조용히 통과한다.**\
  그래서 "맵으로 바꾸기만 했는데 예외가 난다"가 이 주제의 대표 사고다.

```text
같은 데이터, 같은 의도, 다른 결과

  [kim 10] [lee 20] [kim 30]

  for + HashMap.put                        collect(toMap(이름, 점수))
        |                                        |
        v                                        v
  {lee=20, kim=30}                         IllegalStateException:
  (kim 이 덮어써졌다 — 조용히)               Duplicate key kim
                                           (attempted merging values 10 and 30)
```

**똑같은 구조로** Java 가 이렇게 동작한다: 그릇 = `Collector`, 이름표 겹침 = 중복 키.

실무에서 이게 터지는 자리는 **"리스트를 id 로 맵으로 바꾸자"** 한 줄이다.\
테스트 데이터에는 중복이 없고 운영 데이터에는 있다.

> **수집기(`Collector`)** — `collect` 최종 연산에 넘기는 "어떻게 모을지"의 명세.\
> 예: `Collectors.toList()` 는 "리스트에 순서대로 담아라"라는 명세다.

> **`Collectors`** — 표준 수집기들을 만들어 주는 정적 팩토리 클래스. 이름이 복수형이다.\
> 예: `Collectors.joining(", ")` 은 `Collector` 객체 하나를 만들어 돌려준다.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. `Stream.toList()` 와 `Collectors.toList()` 는 **무엇이 다른가** — 이름이 비슷한데 왜 둘 다 있나.
2. `toMap` 이 던지는 **두 예외의 조건**은 각각 무엇인가 — 그리고 `HashMap.put` 과 왜 다른가.
3. 집계 수집기들은 **무슨 타입을 돌려주고 빈 스트림에서 무엇을 주나.**

## 예시 데이터 — 이 묶음이 공유하는 것

47·48번은 같은 데이터를 쓴다. 주제를 건너다니며 읽을 때 비교가 공짜로 따라온다.

```text
record P(String team, String name, int score)

  [red   kim   10]
  [blue  lee   20]
  [red   park  30]
  [green choi  40]
  [blue  jung  50]
```

- 47번은 **`team` 을 무시하고 전체를 하나로** 모은다.
- 48번은 **`team` 으로 나눠서** 모은다. 그것이 두 주제의 경계다.
- `toMap` 의 함정을 보일 때만 `name` 이 겹치는 축소판(`kim 10`·`lee 20`·`kim 30`)을 쓴다.

## 동작 방식

### (1) `toList()` 셋 — 이름이 비슷하고 계약이 다르다

**언제 쓰나** — 결과 리스트를 나중에 고쳐야 할 때. `null` 이 섞일 수 있을 때.

**실행 결과** (`Ex.java` — 47-a, 17·21·25 동일)

```text
== 구체 타입 ==
Stream.toList()          : java.util.ImmutableCollections$ListN
collect(toList())        : java.util.ArrayList
collect(toUnmodifiableList()) : java.util.ImmutableCollections$List12
collect(toSet())         : java.util.HashSet
collect(toUnmodifiableSet()) : java.util.ImmutableCollections$Set12
collect(toCollection(TreeSet::new)) : java.util.TreeSet
== 수정할 수 있나 ==
Stream.toList() 에 add : java.lang.UnsupportedOperationException
collect(toList()) 에 add : 성공 [a, b]
toUnmodifiableList 에 add : java.lang.UnsupportedOperationException
collect(toSet()) 에 add : 성공 [a, b]
== null 원소 ==
Stream.toList() + null   : [x, null]
collect(toList()) + null : [x, null]
toUnmodifiableList + null : java.lang.NullPointerException
collect(toSet()) + null  : [null, x]
toUnmodifiableSet + null : java.lang.NullPointerException: Cannot invoke "Object.equals(Object)" because "e0" is null
```

```text
              수정 가능?        null 원소?
  toList()      X              O            <- 16+, 기본 선택
  (16+)                                        "불변"이지만 null 은 받는다

  Collectors      O              O            <- 고쳐야 할 때
  .toList()                                     실측 타입 ArrayList (보장 아님)

  Collectors      X              X            <- 진짜 불변 컬렉션
  .toUnmodifiable                               null 에서 NPE
  List() (10+)
```

그림 해설 (한 단계씩):

- 셋 다 "리스트를 만든다"인데 **세 칸이 전부 다르다.**
- `Stream.toList()` 는 **수정 불가 + `null` 허용**이라는 조합이다.\
  "불변"이라는 한 단어로 뭉뚱그리면 틀린다.
- `Collectors.toUnmodifiableList()` 는 `List.of(...)` 와 같은 계약이라 **`null` 에서 NPE** 다.
- 반환 **타입**(`ArrayList`·`ImmutableCollections$ListN`)은 **javadoc 이 보장하지 않는다** — 실측일 뿐이다.

비용 — `Stream.toList()` 는 중간 리스트를 만들지 않아 한 번 덜 복사한다.\
`collect(toList())` 는 `ArrayList` 를 그대로 돌려주므로 추가 복사가 없지만 **캡슐화가 새는** 쪽이다.

### (2) `toMap` 의 첫 함정 — 중복 키에 **던진다**

**언제 쓰나** — 리스트를 id 로 맵으로 바꿀 때. 즉 거의 언제나.

**실행 결과** (`Ex.java` — 47-b)

```text
== HashMap.put 은 덮어쓴다 ==
결과 {lee=20, kim=30}
== 같은 일을 toMap 으로 ==
예외 : java.lang.IllegalStateException: Duplicate key kim (attempted merging values 10 and 30)
== merge 함수를 주면 ==
뒤쪽 이김 : {lee=20, kim=30}
앞쪽 이김 : {lee=20, kim=10}
합치기   : {lee=20, kim=40}
```

```text
for + HashMap.put                          collect(toMap(...))  2인자

  kim -> 없다 -> 넣는다 {kim=10}             kim -> putIfAbsent 성공
  lee -> 없다 -> 넣는다 {kim=10,lee=20}      lee -> putIfAbsent 성공
  kim -> 있다 -> 덮어쓴다 {kim=30}           kim -> putIfAbsent 가 기존 값 10 을 돌려준다
        |                                          |
        v                                          v
  조용히 하나가 사라진다                        IllegalStateException 을 던진다
  결과는 나오는데 틀렸다                        멈춘다 — 그래서 알게 된다
```

그림 해설 (한 단계씩):

- **`toMap` 이 더 엄격한 쪽이다.** `HashMap.put` 의 조용한 덮어쓰기를 예외로 승격시킨다.
- JDK 21.0.5 소스가 그대로 보여 준다.

```java
// JDK 21.0.5  java.base/java/util/stream/Collectors.java  175~185행 — 실제 소스 그대로
private static <T, K, V>
BiConsumer<Map<K, V>, T> uniqKeysMapAccumulator(Function<? super T, ? extends K> keyMapper,
                                                Function<? super T, ? extends V> valueMapper) {
    return (map, element) -> {
        K k = keyMapper.apply(element);
        V v = Objects.requireNonNull(valueMapper.apply(element));
        V u = map.putIfAbsent(k, v);
        if (u != null) throw duplicateKeyException(k, u, v);
    };
}
```

- `putIfAbsent` 가 `null` 이 아닌 값을 돌려주면 **이미 그 키가 있었다**는 뜻이다. 거기서 던진다.
- 메시지도 소스에 그대로 있다.

```java
// JDK 21.0.5  java.base/java/util/stream/Collectors.java  133~139행 — 실제 소스 그대로
private static IllegalStateException duplicateKeyException(
        Object k, Object u, Object v) {
    return new IllegalStateException(String.format(
        "Duplicate key %s (attempted merging values %s and %s)",
        k, u, v));
}
```

- javadoc 도 명시한다.

> If the mapped keys contain duplicates (according to `Object.equals(Object)`), **an `IllegalStateException` is thrown when the collection operation is performed.** If the mapped keys might have duplicates, use `toMap(Function, Function, BinaryOperator)` instead.

비용 — 3인자 `toMap`(merge 함수)을 주면 예외가 사라진다.\
대신 **어느 값이 살아남는지를 내가 정해야 한다** — `(a, b) -> b` 가 `HashMap.put` 과 같은 동작이다.

### (3) `toMap` 의 둘째 함정 — 값이 `null` 이면 **던진다**

**언제 쓰나** — nullable 필드를 값으로 쓸 때. `Optional` 을 안 쓰는 레거시 DTO 를 다룰 때.

**실행 결과** (`Ex.java` — 47-c)

```text
== HashMap.put 은 null 값을 받는다 ==
결과 {lee=null, kim=10} / containsKey(lee)=true / get(lee)=null
== toMap 은 null 값에 던진다 (merge 함수 없음) ==
toMap 2인자 : java.lang.NullPointerException
== merge 함수를 줘도 던진다 ==
toMap 3인자 : java.lang.NullPointerException
```

```text
HashMap.put(k, null)                       toMap(..., v -> null)

  넣힌다                                    2인자 -> Objects.requireNonNull 에서 NPE
  containsKey(k) = true                     3인자 -> HashMap.merge 안에서 NPE
  get(k) = null
        |                                          |
        v                                          v
  "키는 있는데 값이 없다"를 표현할 수 있다      표현할 수 없다 — 아예 못 넣는다
```

그림 해설 (한 단계씩):

- **`HashMap` 은 `null` 값을 받는다.** `containsKey` 와 `get` 이 다른 답을 주는 것이 그 증거다.
- **`toMap` 은 못 넣게 막는다.** 2인자와 3인자가 **서로 다른 자리에서** 던진다.
- 스택트레이스가 그 차이를 보여 준다.

```text
2인자 — Collectors 자신이 막는다            3인자 — HashMap.merge 가 막는다
  at java.util.Objects.requireNonNull         at java.util.HashMap.merge
  at Collectors.lambda$uniqKeysMapAccumulator at Collectors.lambda$toMap$68
```

- **메시지가 없다.** 그냥 `java.lang.NullPointerException` 이다 — 원인을 스택트레이스로 찾아야 한다.
- 반대로 **키가 `null` 인 것은 통과한다**(`{null=1, a=2}`). 값만 막는다.\
  단 `TreeMap::new` 를 주면 그때는 `Comparable.compareTo` 에서 NPE 가 난다.

비용 — 방어가 필요하다. 셋 중 하나를 고른다.

```java
// 1) 걸러 낸다
src.stream().filter(p -> p.score() != null).collect(Collectors.toMap(P::name, P::score));
// 2) 기본값으로 바꾼다
src.stream().collect(Collectors.toMap(P::name, p -> p.score() == null ? 0 : p.score()));
// 3) toMap 을 안 쓴다 — 3인자 collect 로 직접 모은다
src.stream().collect(HashMap::new, (m, p) -> m.put(p.name(), p.score()), HashMap::putAll);
```

**실행 결과** (`Ex.java` — 47-c)

```text
filter : {kim=10}
기본값 : {lee=0, kim=10}
HashMap 으로 모으기 : {lee=null, kim=10}
```

### (4) merge 함수가 `null` 을 돌려주면 항목이 **사라진다**

**언제 쓰나** — merge 함수 안에서 조건부로 "이건 버리자"를 표현하려 할 때.

**실행 결과** (`Ex.java` — 47-e)

```text
== merge 함수가 null 을 돌려주면 ==
결과 {} / 크기 0
```

```text
toMap(name, score, (a, b) -> null)   에서  [kim 10] [kim 30]

  kim=10 을 넣는다            {kim=10}
  kim=30 이 온다 -> merge 호출 -> null 을 돌려받는다
        |
        v
  HashMap.merge 의 계약: 결과가 null 이면 그 키를 제거한다
        |
        v
  {}   <- 예외 없음. 키 자체가 사라졌다
```

그림 해설 (한 단계씩):

- 3인자 `toMap` 은 내부에서 **`Map.merge` 를 그대로 부른다.**\
  javadoc 도 merge 함수를 "as supplied to `Map.merge(Object, Object, BiFunction)`" 라고 설명한다.
- `Map.merge` 는 **결과가 `null` 이면 그 항목을 지운다.**
- 그래서 merge 함수에서 `null` 을 돌려주면 **예외도 경고도 없이 데이터가 사라진다.**
- 전형적인 무음 실패다. "버리고 싶다"를 `null` 로 표현하지 않는다.

비용 — 없음(그것이 문제다). 방어는 **merge 함수가 `null` 을 절대 안 돌려주게 쓰는 것**뿐이다.

### (5) 집계 수집기 — 무엇을 돌려주나

**언제 쓰나** — 합·평균·개수·문자열 이어 붙이기.

**실행 결과** (`Ex.java` — 47-e, 예시 데이터 5명)

```text
== 세기·합·평균의 반환 타입 ==
counting()        : 5 (Long)
summingInt()      : 150 (Integer)
summingDouble()   : 150.0 (Double)
averagingInt()    : 30.0 (Double)
averagingDouble() : 30.0 (Double)
summarizingInt()  : IntSummaryStatistics{count=5, sum=150, min=10, average=30.000000, max=50}
== 빈 스트림에서 ==
counting()   : 0
summingInt() : 0
averagingInt(): 0.0
maxBy()      : Optional.empty
== minBy / maxBy 는 Optional ==
maxBy : Optional[P[team=blue, name=jung, score=50]]
minBy : Optional[P[team=red, name=kim, score=10]]
```

```text
값이 항상 있는 것 (항등원이 있다)         값이 없을 수 있는 것 (항등원이 없다)

  counting()      -> Long                   minBy() -> Optional<T>
  summingInt()    -> Integer                maxBy() -> Optional<T>
  averagingInt()  -> Double
        |                                          |
   빈 스트림에서 0 / 0.0                      빈 스트림에서 Optional.empty
```

그림 해설 (한 단계씩):

- **`counting()` 만 `Long`** 이다. `summingInt` 는 `Integer`, `averagingInt` 는 `Double`.\
  `averaging*` 은 입력이 `int` 여도 **항상 `Double`** 을 돌려준다 — `Stream.of(1,2)` 의 평균이 `1.5` 로 나온다.
- **빈 스트림의 `averagingInt` 는 `0.0`** 이다. `NaN` 도 `Optional` 도 아니다.\
  "평균 0" 과 "원소 없음"을 구별할 수 없다 — 구별하려면 `summarizingInt` 의 `count` 를 본다.
- `minBy`/`maxBy` 만 `Optional` 이다.

비용 — `summarizingInt` 하나로 count·sum·min·average·max 다섯을 한 번에 얻는다.\
따로 다섯 번 돌리는 것보다 싸다.

### (6) `joining` 과 `collectingAndThen`

**언제 쓰나** — 문자열로 이어 붙일 때. 결과에 마지막 손질을 할 때.

**실행 결과** (`Ex.java` — 47-e)

```text
== joining 세 형태 ==
joining()        : kimleeparkchoijung
joining(", ")    : kim, lee, park, choi, jung
joining(구분,앞,뒤) : [kim, lee, park, choi, jung]
빈 스트림 + 앞뒤   : []
== reducing / collectingAndThen ==
reducing(0,f,op) : 150
collectingAndThen 타입 : java.util.Collections$UnmodifiableRandomAccessList
```

```text
joining(", ", "[", "]")   에서  [kim] [lee] [park] [choi] [jung]

  "["  +  kim  + ", " + lee + ", " + ... + jung  +  "]"
   앞     원소   구분자          원소                 뒤

  빈 스트림이면:  "[" + "]" = "[]"     <- 앞뒤는 원소가 없어도 붙는다
```

그림 해설 (한 단계씩):

- `joining` 은 **`CharSequence` 스트림에만** 쓸 수 있다. 숫자면 `map(String::valueOf)` 를 먼저.
- **빈 스트림에서도 앞뒤 문자열은 붙는다** — `[]` 가 나온다. 빈 문자열이 아니다.
- `collectingAndThen(수집기, 마무리함수)` 는 **다 모은 뒤 한 번 더 변환**한다.\
  결과를 수정 불가로 감싸거나, `Optional` 을 벗길 때 쓴다(48번에서 자주 나온다).

비용 — `joining` 은 내부에서 `StringBuilder` 를 쓴다. 루프 안 `+=` 보다 싸다([**36번 주제**](../36-stringbuilder-and-concat/)).

## 문법 — 형태와 규칙

직접 쓴 최소 예제다. 출력은 전부 실행 결과다.

### 기본 수집기 지도

| 하고 싶은 일 | 수집기 | 돌려주는 것 | 버전 |
|---|---|---|---|
| 리스트로 (고칠 것) | `toList()` | `ArrayList` (실측) | 8 |
| 리스트로 (안 고칠 것) | **`Stream.toList()`** — 수집기가 아니다 | 수정 불가 `List` | 16 |
| 리스트로 (진짜 불변) | `toUnmodifiableList()` | `List.of` 계열 | 10 |
| 집합으로 | `toSet()` | `HashSet` (실측) | 8 |
| 집합으로 (불변) | `toUnmodifiableSet()` | `Set.of` 계열 | 10 |
| 원하는 컬렉션으로 | `toCollection(TreeSet::new)` | 그 타입 그대로 | 8 |
| 맵으로 | `toMap(키, 값)` | `HashMap` (실측) | 8 |
| 맵으로 (중복 키 허용) | `toMap(키, 값, merge)` | `HashMap` (실측) | 8 |
| 맵으로 (타입 지정) | `toMap(키, 값, merge, TreeMap::new)` | 그 타입 그대로 | 8 |
| 문자열 잇기 | `joining()` / `joining(",")` / `joining(",", "[", "]")` | `String` | 8 |
| 개수 | `counting()` | `Long` | 8 |
| 합 | `summingInt`/`summingLong`/`summingDouble` | `Integer`/`Long`/`Double` | 8 |
| 평균 | `averagingInt`/`averagingLong`/`averagingDouble` | **항상 `Double`** | 8 |
| 통계 한 번에 | `summarizingInt` 등 | `IntSummaryStatistics` 등 | 8 |
| 최소·최대 | `minBy(cmp)` / `maxBy(cmp)` | `Optional<T>` | 8 |
| 접기 | `reducing(...)` | 형태 나름 | 8 |
| 마무리 변환 | `collectingAndThen(수집기, 함수)` | 함수 나름 | 8 |

- **`Stream.toList()` 는 `Collectors` 가 아니다.** 스트림의 메서드다. 표에는 대비를 위해 넣었다.

### `toMap` 네 형태

```java
// 2인자 — 중복 키면 던진다
collect(Collectors.toMap(P::name, P::score))

// 3인자 — 중복 키를 merge 함수로 푼다
collect(Collectors.toMap(P::name, P::score, (a, b) -> b))     // HashMap.put 과 같은 동작
collect(Collectors.toMap(P::name, P::score, (a, b) -> a))     // 먼저 온 것이 이김
collect(Collectors.toMap(P::name, P::score, Integer::sum))    // 합산

// 4인자 — 맵 타입까지 고른다
collect(Collectors.toMap(P::name, P::score, Integer::sum, TreeMap::new))
```

**실행 결과** (`Ex.java` — 47-b)

```text
뒤쪽 이김 : {lee=20, kim=30}
앞쪽 이김 : {lee=20, kim=10}
합치기   : {lee=20, kim=40}
TreeMap       : java.util.TreeMap
LinkedHashMap : {kim=40, lee=20}
기본 맵 타입   : java.util.HashMap
```

- **2인자를 기본으로 쓰지 않는다.** 키가 유일하다고 **증명할 수 있을 때만** 쓴다.
- 키 순서가 필요하면 `LinkedHashMap::new`(입력 순서) 또는 `TreeMap::new`(정렬 순서)를 4인자로 준다.

### 오버로드된 메서드에 4인자 `toMap` 을 인라인하면 컴파일이 안 된다

```java
System.out.println(k.stream().collect(Collectors.toMap(P::name, P::score, (a,b)->b, TreeMap::new)));
```

```text
$ javac Ex.java
Ex.java:8: error: incompatible types: inference variable R has incompatible bounds
        System.out.println(k.stream().collect(Collectors.toMap(P::name, P::score, (a, b) -> b, TreeMap::new)));
                                             ^
    upper bounds: String,Map<K#1,U>,Object
    lower bounds: TreeMap<K#2,V>
```

- `println` 이 오버로드돼 있어 **대상 타입이 정해지지 않아** 추론이 실패한다.
- 고치는 법: **변수에 먼저 담는다.**

```java
TreeMap<String, Integer> tm = k.stream().collect(Collectors.toMap(P::name, P::score, (a,b)->b, TreeMap::new));
System.out.println(tm);
```

## 어디서 틀리나

### 1. "리스트를 맵으로" 한 줄이 운영에서 터진다

```java
Map<String, User> byEmail = users.stream()
        .collect(Collectors.toMap(User::email, u -> u));   // 중복 이메일이 하나만 있어도 터진다
```

- 테스트 데이터에는 중복이 없다. **운영 데이터에는 있다.**
- 터지는 게 나쁜 건 아니다 — `HashMap.put` 으로 썼다면 **조용히 한 건이 사라졌을** 것이다.
- 방어: **3인자 `toMap` 을 기본으로 쓴다.** 어느 쪽이 이겨야 하는지 그 자리에서 결정한다.
- 중복이 정말 있으면 안 되는 값이면 2인자를 쓰되 **예외 메시지가 진단이 되도록** 키를 잘 고른다.

### 2. `null` 값에 `toMap` 을 쓴다

```java
Map<String, String> m = users.stream()
        .collect(Collectors.toMap(User::id, User::nickname));   // nickname 이 null 이면 NPE
```

- **메시지 없는 `NullPointerException`** 이라 원인이 안 보인다.
- `HashMap.put` 은 받아 주므로 **`for` 문을 스트림으로 바꾼 순간** 터진다.
- 방어: (3)의 세 가지 중 하나. **`filter` 로 걸러 내는 쪽이 의도가 가장 잘 드러난다.**

### 3. `Stream.toList()` 의 결과를 정렬하려 한다

```java
List<String> l = stream.toList();
Collections.sort(l);              // UnsupportedOperationException
```

- `toList()`(16+)는 **수정 불가**다. `sort`·`add`·`remove`·`set` 전부 막힌다.
- 방어: 고칠 거면 `collect(Collectors.toCollection(ArrayList::new))`.\
  아니면 **스트림 안에서 `sorted()` 로 정렬해 버린다.**

### 4. "불변"이라는 한 단어로 세 가지를 뭉뚱그린다

```text
                        add     null 원소
  Stream.toList()        X        O        <- 불변인데 null 을 받는다
  toUnmodifiableList()   X        X        <- List.of 와 같은 계약
  unmodifiableList(al)   X        O        <- 뷰다. 원본을 고치면 따라 바뀐다
```

- 셋 다 "불변"이라 불리지만 **계약이 다르다.**
- `Collections.unmodifiableList` 는 **뷰**라서 원본 리스트를 고치면 그 변화가 비친다.\
  `collectingAndThen(toList(), Collections::unmodifiableList)` 가 만드는 것이 이것이다.
- 방어: **"고칠 수 있나"와 "원본과 이어져 있나"를 따로 묻는다.**

### 5. `averaging*` 의 빈 스트림 결과를 "데이터 없음"으로 읽는다

```java
double avg = orders.stream().collect(Collectors.averagingInt(Order::amount));   // 빈 목록이면 0.0
```

- **`0.0` 이다.** `NaN` 도 아니고 `Optional` 도 아니다.
- "평균 주문액 0원"과 "주문이 없음"이 **같은 값으로 보인다.**
- 방어: `summarizingInt` 를 써서 `count` 를 같이 본다. 또는 `isEmpty()` 를 먼저 검사한다.

### 6. `summingInt` 의 오버플로

**실행 결과** (`Ex.java` — 47-e)

```text
summingInt 오버플로 : -2147483648
summingLong 으로   : 2147483648
```

- `summingInt` 는 `int` 로 더한다. **조용히 음수가 된다.**
- 예외도 경고도 없다 — [**02번 주제**](../02-numeric-operations/)(정수 오버플로)와 같은 실패 모드다.
- 방어: **금액·카운트 합계는 `summingLong`.**

### 7. merge 함수에서 `null` 을 돌려준다

- (4)에서 본 것이다. **항목이 조용히 사라진다.**
- 방어: merge 함수는 항상 둘 중 하나 또는 새 값을 돌려준다. **"버림"을 표현하고 싶으면 `toMap` 앞에서 `filter` 한다.**

## 구현 세부사항 대 언어 보장

| 관측한 것 | 보장인가 | 근거 |
|---|---|---|
| 중복 키에서 `IllegalStateException` | **보장** | `toMap` javadoc 명시 |
| 그 메시지가 `Duplicate key ... (attempted merging values ...)` | **보장 아님** | 소스의 `String.format` 일 뿐 |
| `null` 값에서 `NullPointerException` | **사실상 보장** — 계약은 "맵의 계약을 따른다" | 2인자는 `Objects.requireNonNull`, 3인자는 `Map.merge` 의 계약 |
| `collect(toList())` 가 `ArrayList` | **보장 아님** | javadoc: "no guarantees on the type, mutability, serializability, or thread-safety of the `List` returned" |
| `toMap` 이 `HashMap` | **보장 아님** | javadoc 같은 문장 |
| `toSet()` 이 `HashSet` | **보장 아님** | 같은 문장 |
| `Stream.toList()` 가 수정 불가 | **보장** | `Stream.toList` javadoc — "unmodifiable List" |
| `toUnmodifiableList` 가 `null` 에서 NPE | **보장** | `List.of` 의 계약을 따른다 |

**세 JDK 실측** — 프로그램 5개를 17.0.13 · 21.0.5 · 25.0.1 에서 돌려 `diff` 했다.

```text
예외 메시지 — 세 버전이 한 글자도 같다
  IllegalStateException: Duplicate key kim (attempted merging values 10 and 30)
  NullPointerException  (메시지 없음)

스택트레이스 — 줄 번호와 람다 번호가 다르다
  21: Collectors.lambda$uniqKeysMapAccumulator$1(Collectors.java:182)
  25: Collectors.lambda$uniqKeysMapAccumulator$0(Collectors.java:182)
  17: Objects.requireNonNull(Objects.java:209)  /  21: (:233)  /  25: (:220)
```

- **람다 번호(`$1` 대 `$0`)까지 바뀐다.** 스택트레이스 문자열 비교로 테스트를 쓰면 버전이 오를 때 깨진다.
- 구체 맵·리스트 타입을 `getClass()` 로 단언하는 테스트도 같은 이유로 쓰지 않는다.

## 언제 쓰고 언제 안 쓰나

| 하고 싶은 일 | 고를 것 |
|---|---|
| 그냥 리스트로 받기 | **`toList()`(16+)** — 기본 선택 |
| 받아서 고칠 것 | `collect(Collectors.toCollection(ArrayList::new))` |
| API 로 내보낼 불변 리스트 | `collect(Collectors.toUnmodifiableList())` — 단 `null` 원소가 없어야 한다 |
| 중복 제거 | `collect(Collectors.toSet())` — 순서는 잃는다 |
| 중복 제거 + 입력 순서 유지 | `collect(Collectors.toCollection(LinkedHashSet::new))` |
| id → 객체 맵 | **3인자 `toMap`** — 중복 정책을 명시한다 |
| 키 순서가 필요한 맵 | 4인자 `toMap` + `LinkedHashMap::new` 또는 `TreeMap::new` |
| 값이 `null` 일 수 있다 | `toMap` 을 쓰지 않거나 앞에서 `filter`/기본값 |
| 문자열 CSV | `map(String::valueOf).collect(joining(","))` |
| 개수만 | **`count()` 최종 연산** — `counting()` 은 다운스트림용이다(48번) |
| 합계 | 숫자면 `mapToInt(...).sum()` 이 더 곧다. `summingInt` 는 다운스트림용 |
| 통계 여러 개 | `summarizingInt` 한 번 |
| 그룹별로 나눠서 | **여기가 아니라 [`../48-collectors-grouping/`](../48-collectors-grouping/)** |

판단 규칙 세 줄.

- **`toMap` 은 2인자를 기본으로 쓰지 않는다.** 중복 정책을 그 자리에서 적는다.
- **`toMap` 에 `null` 값을 넣지 않는다.** `HashMap.put` 과 다르다.
- **`counting`·`summingInt` 는 단독으로 쓸 일이 거의 없다.** 그것들의 자리는 다운스트림이다(48번).

## 핵심 문장

- `Stream.toList()`·`Collectors.toList()`·`toUnmodifiableList()` 는 **수정 가능성과 `null` 허용이 각각 다르다.** "불변"이라는 한 단어로 묶으면 틀린다.
- **`toMap` 은 중복 키에 `IllegalStateException` 을 던진다** — `HashMap.put` 의 조용한 덮어쓰기를 예외로 승격시킨 것이다.
- **`toMap` 은 값이 `null` 이면 메시지 없는 `NullPointerException` 을 던진다.** 2인자는 `Objects.requireNonNull` 에서, 3인자는 `HashMap.merge` 에서.
- **merge 함수가 `null` 을 돌려주면 항목이 조용히 사라진다** — `Map.merge` 의 계약이 그렇다.
- 반환 **타입**(`ArrayList`·`HashMap`)은 javadoc 이 보장하지 않는다. **계약은 인터페이스까지**다.

## 관련 자료

- [`../46-terminal-operations/`](../46-terminal-operations/) — **이 주제의 선행.** `collect` 가 언제 실제로 도는가
- [`../48-collectors-grouping/`](../48-collectors-grouping/) — 같은 수집기들을 **키로 나눠서** 쓰는 법. 그쪽은 **그룹핑·분할·다운스트림 조합**까지, 여기는 **나누지 않는 수집**까지
- [`../49-parallel-streams/`](../49-parallel-streams/) — `toMap`·`groupingBy` 가 병렬에서 어떻게 도나
- [`../44-stream-creation/`](../44-stream-creation/) — `Stream.toList()` 와 `Collectors.toList()` 의 차이가 처음 언급된 곳
- [`../27-equals-hashcode-contract/`](../27-equals-hashcode-contract/) — `toMap` 의 키와 `toSet` 이 기대는 계약
- [`../../../../../data-structure/05-hashmap/`](../../../../../data-structure/05-hashmap/) — 해시맵 **내부**는 거기가 정본. 그쪽은 **버킷·충돌·리사이즈**까지, 여기는 **`Collectors` 가 그 위에 얹은 규칙**부터
- [`../README.md`](../README.md) — Java 문법·API 주제 목록(이 주제는 47번)
- [**41번 주제**](../41-map-api-merge-compute/)(`Map` API) — `merge`/`compute*` 의 계약. (4)의 "`null` 이면 제거"가 정본으로 다뤄지는 곳
- [**40번 주제**](../40-list-set-and-immutable-factories/)(불변 팩토리) — `List.of`·`copyOf`·`unmodifiable*` 의 차이
- [**02번 주제**](../02-numeric-operations/)(정수 오버플로) — `summingInt` 가 조용히 음수가 되는 것
- [**38번 주제**](../38-optional/)(`Optional`) — `minBy`/`maxBy` 가 돌려주는 그 타입
- [**36번 주제**](../36-stringbuilder-and-concat/)(`StringBuilder`) — `joining` 이 내부에서 쓰는 것

## 용어 풀이

- **수집기(`Collector`)** — `collect` 에 넘기는 "어떻게 모을지"의 명세. 공급자·누산기·결합자·마무리 넷으로 이루어진다.
- **`Collectors`** — 표준 수집기를 만드는 정적 팩토리 클래스(복수형 이름).
- **merge 함수(`BinaryOperator`)** — 같은 키에 값이 둘 올 때 하나로 합치는 함수. `Map.merge` 에 그대로 넘어간다.
- **`IllegalStateException`** — 그 호출을 받을 상태가 아닐 때의 예외. `toMap` 의 중복 키가 이것이다.
- **수정 불가(unmodifiable)** — 고치는 메서드가 `UnsupportedOperationException` 을 던지는 것. 원본과 이어져 있을 수도, 아닐 수도 있다.
- **뷰(view)** — 원본을 가리키기만 하는 래퍼. 원본이 바뀌면 같이 바뀐다. `Collections.unmodifiableList` 가 그것이다.
- **다운스트림(downstream)** — 그룹 안에서 다시 돌리는 수집기. 48번의 주제다.
- **마무리(finisher)** — 다 모은 뒤 한 번 더 변환하는 단계. `collectingAndThen` 이 이것을 붙인다.
- **`IntSummaryStatistics`** — count·sum·min·average·max 를 한 객체에 담은 것. `summarizingInt` 의 결과.

## 더 들어가면

- **`toMap` 의 2인자와 3인자는 구현이 다른 함수다.**\
  2인자는 `uniqKeysMapAccumulator`(`putIfAbsent` + 예외), 3인자는 `map.merge(...)` 를 그대로 부른다.\
  그래서 `null` 값에서 **던지는 자리도 다르고 스택트레이스도 다르다.** 같은 계약의 두 오버로드가 아니다.
- **`toUnmodifiableMap`(10+)은 3인자 `toMap` 을 감싼 것**이다.

  ```java
  // JDK 21.0.5  java.base/java/util/stream/Collectors.java  1585~1587행 — 실제 소스 그대로
  return collectingAndThen(
          toMap(keyMapper, valueMapper, mergeFunction, HashMap::new),
          map -> (Map<K,U>)Map.ofEntries(map.entrySet().toArray(new Map.Entry[0])));
  ```

  `HashMap` 을 만든 뒤 `Map.ofEntries` 로 다시 복사한다 — **한 번 더 복사한다**는 뜻이다.
- **`Collector` 를 직접 만들 수도 있다** — `Collector.of(공급자, 누산기, 결합자, 마무리, 특성...)`.\
  다만 필요한 경우는 드물다. `collectingAndThen` + 기존 수집기 조합으로 대개 풀린다.
- **수집기의 `characteristics()`** 는 병렬 동작을 정한다 — `CONCURRENT`·`UNORDERED`·`IDENTITY_FINISH`.\
  `toMap` 은 `[IDENTITY_FINISH]` 뿐이라 **병렬에서 맵을 조각마다 만들어 합친다.** 그 비용과 대안은 49번이 정본이다.
