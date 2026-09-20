# java/syntax/47 — `Collectors`: 기본 수집기와 `toMap` 의 함정 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·에러는 **Temurin JDK 21.0.5 에서 실제로 돌려 얻은 것**이다.\
> 소스·javadoc 인용은 `lib/src.zip` 의 `java.base/java/util/stream/Collectors.java` 원문이다.\
> 17.0.13 · 25.0.1 에서도 같은 프로그램을 돌렸다 — **메시지는 같고 스택트레이스만 달랐다**(11번).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 세 가지 `toList` 의 차이

**출력** (`Ex.java` — 47-a, 17·21·25 동일)

```text
== null 원소 ==
Stream.toList() + null   : [x, null]
collect(toList()) + null : [x, null]
toUnmodifiableList + null : java.lang.NullPointerException
== 수정할 수 있나 ==
Stream.toList() 에 add : java.lang.UnsupportedOperationException
collect(toList()) 에 add : 성공 [a, b]
toUnmodifiableList 에 add : java.lang.UnsupportedOperationException
== 구체 타입 ==
Stream.toList()          : java.util.ImmutableCollections$ListN
collect(toList())        : java.util.ArrayList
collect(toUnmodifiableList()) : java.util.ImmutableCollections$List12
```

**왜 그런가**

```text
                        add 가능?   null 원소?   실측 구체 타입
  Stream.toList() (16+)     X          O        ImmutableCollections$ListN
  Collectors.toList()       O          O        java.util.ArrayList
  toUnmodifiableList()(10+) X          X        ImmutableCollections$List12
```

- **`Stream.toList()` 는 수정 불가인데 `null` 을 받는다.** 이 조합이 핵심이다.
- `Collectors.toUnmodifiableList()` 는 **`List.of(...)` 와 같은 계약**이라 `null` 에서 NPE 다.
- `Collectors.toList()` 만 고칠 수 있다.

**구체 타입은 보장인가**

- **아니다.** javadoc 이 명시적으로 부정한다.

> There are no guarantees on the type, mutability, serializability, or thread-safety of the `List` returned.

- 그래서 `((ArrayList<?>) result)` 같은 캐스팅을 쓰면 안 된다.

**"불변" 한 단어로 묶으면 놓치는 것**

- **`null` 허용 여부**와 **원본과 이어져 있는지** 둘을 놓친다.

```text
                            add     null     원본과 이어짐
  Stream.toList()            X       O            X
  toUnmodifiableList()       X       X            X
  Collections                X       O            O  <- 뷰다
  .unmodifiableList(al)                              al 을 고치면 따라 바뀐다
```

- `collectingAndThen(toList(), Collections::unmodifiableList)` 가 만드는 것이 셋째 줄이다.\
  실측 타입 `java.util.Collections$UnmodifiableRandomAccessList`.

**무엇을 기본으로 쓰나**

- **`toList()`(16+)를 기본으로.** 짧고, 중간 리스트를 덜 만들고, 실수로 고칠 수 없다.
- 고쳐야 하면 `collect(Collectors.toCollection(ArrayList::new))` — 의도가 드러난다.
- API 로 내보낼 진짜 불변 리스트면 `toUnmodifiableList()`. 단 `null` 원소가 없어야 한다.

### 2. `toMap` 의 첫 함정

**출력** (`Ex.java` — 47-b)

```text
== HashMap.put 은 덮어쓴다 ==
결과 {lee=20, kim=30}
== 같은 일을 toMap 으로 ==
예외 : java.lang.IllegalStateException: Duplicate key kim (attempted merging values 10 and 30)
```

**(A)의 결과**

- **`{lee=20, kim=30}`** — `kim=10` 이 조용히 덮어써졌다.

**(B)는 무엇을 던지는가**

- **`IllegalStateException`**.

**메시지 전문**

```text
Duplicate key kim (attempted merging values 10 and 30)
```

- 값 두 개가 다 들어 있다 — **먼저 있던 값(10)과 새로 온 값(30)**.

**어느 쪽이 더 안전한가**

```text
for + HashMap.put                          collect(toMap(...)) 2인자

  결과가 나온다                              멈춘다
  {lee=20, kim=30}                          IllegalStateException
        |                                          |
        v                                          v
  한 건이 사라진 것을 아무도 모른다              어느 키가 겹쳤는지까지 알려 준다
  = 무음 실패                                  = 시끄러운 실패
```

- **`toMap` 쪽이 안전하다.** 조용한 데이터 유실을 예외로 승격시킨 것이다.
- 다만 **운영에서 처음 터진다**는 대가가 있다 — 그래서 3인자를 기본으로 쓴다(12번).

**JDK 소스**

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

```java
// JDK 21.0.5  java.base/java/util/stream/Collectors.java  133~139행 — 실제 소스 그대로
private static IllegalStateException duplicateKeyException(
        Object k, Object u, Object v) {
    return new IllegalStateException(String.format(
        "Duplicate key %s (attempted merging values %s and %s)",
        k, u, v));
}
```

- `putIfAbsent` 가 `null` 아닌 값을 돌려주면 **그 키가 이미 있었다**는 뜻이고, 거기서 던진다.
- 같은 줄에 **`Objects.requireNonNull` 도 있다** — 3번의 `null` 값 함정이 여기서 난다.

**스택트레이스 전문** (JDK 21.0.5)

```text
Exception in thread "main" java.lang.IllegalStateException: Duplicate key kim (attempted merging values 10 and 30)
	at java.base/java.util.stream.Collectors.duplicateKeyException(Collectors.java:135)
	at java.base/java.util.stream.Collectors.lambda$uniqKeysMapAccumulator$1(Collectors.java:182)
	at java.base/java.util.stream.ReduceOps$3ReducingSink.accept(ReduceOps.java:169)
	at java.base/java.util.AbstractList$RandomAccessSpliterator.forEachRemaining(AbstractList.java:722)
	at java.base/java.util.stream.AbstractPipeline.copyInto(AbstractPipeline.java:509)
	at java.base/java.util.stream.AbstractPipeline.wrapAndCopyInto(AbstractPipeline.java:499)
	at java.base/java.util.stream.ReduceOps$ReduceOp.evaluateSequential(ReduceOps.java:921)
	at java.base/java.util.stream.AbstractPipeline.evaluate(AbstractPipeline.java:234)
	at java.base/java.util.stream.ReferencePipeline.collect(ReferencePipeline.java:682)
	at Ex.main(Ex.java:33)
```

### 3. `toMap` 의 둘째 함정

**출력** (`Ex.java` — 47-c)

```text
== HashMap.put 은 null 값을 받는다 ==
결과 {lee=null, kim=10} / containsKey(lee)=true / get(lee)=null
== toMap 은 null 값에 던진다 (merge 함수 없음) ==
toMap 2인자 : java.lang.NullPointerException
== merge 함수를 줘도 던진다 ==
toMap 3인자 : java.lang.NullPointerException
```

**(A)는 어떻게 되는가**

- **들어간다.** `containsKey("lee")` 는 `true`, `get("lee")` 는 `null`.
- `HashMap` 은 "키는 있는데 값이 없다"를 표현할 수 있다.

**(B)와 (C)**

- **둘 다 `NullPointerException`**.

**같은 자리에서 나는가**

- **아니다.** 스택트레이스가 다르다.

```text
(B) 2인자 — Collectors 자신이 막는다        (C) 3인자 — HashMap.merge 가 막는다

  at java.util.Objects.requireNonNull          at java.util.HashMap.merge
       (Objects.java:233)                           (HashMap.java:1363)
  at Collectors                                at Collectors
       .lambda$uniqKeysMapAccumulator$1             .lambda$toMap$68
       (Collectors.java:180)                        (Collectors.java:1636)
```

- **2인자와 3인자는 구현이 다른 함수다.** 같은 계약의 두 오버로드가 아니다.
- 2인자는 2번에서 본 `uniqKeysMapAccumulator`, 3인자는 `map.merge(...)` 를 그대로 부른다.

```text
Exception in thread "main" java.lang.NullPointerException
	at java.base/java.util.Objects.requireNonNull(Objects.java:233)
	at java.base/java.util.stream.Collectors.lambda$uniqKeysMapAccumulator$1(Collectors.java:180)
	at java.base/java.util.stream.ReduceOps$3ReducingSink.accept(ReduceOps.java:169)
	... (이하 생략)
	at Ex.main(Ex.java:39)
```

**메시지가 있는가**

- **없다.** 그냥 `java.lang.NullPointerException` 이다.
- 그래서 **스택트레이스를 봐야 원인을 안다** — 로그에 메시지만 찍으면 아무것도 모른다.
- 대조적으로 `toUnmodifiableSet` 의 NPE 는 메시지가 있었다(도움말 NPE, 14+):\
  `Cannot invoke "Object.equals(Object)" because "e0" is null`.

**키가 `null` 이면**

**출력** (`Ex.java` — 47-d)

```text
== null 키는 통과한다 ==
2인자 HashMap : {null=1, a=2}
3인자 HashMap : {null=1, a=2}
4인자 TreeMap : java.lang.NullPointerException: Cannot invoke "java.lang.Comparable.compareTo(Object)" because "k1" is null
```

- **키가 `null` 인 것은 통과한다.** `HashMap` 이 `null` 키를 허용하기 때문이다.
- **값만 막는다** — 비대칭이다.
- `TreeMap::new` 를 주면 그때는 **`TreeMap` 자신의 계약** 때문에 던진다(정렬하려면 비교해야 한다).

### 4. merge 함수가 `null` 을 돌려주면

**출력** (`Ex.java` — 47-e)

```text
== merge 함수가 null 을 돌려주면 ==
결과 {} / 크기 0
```

**결과**

- **`{}`** — 빈 맵이다. 크기 0.

**예외가 나는가**

- **안 난다.** 아무 경고도 없다.

**왜 그렇게 되는가**

```text
toMap(name, score, (a,b) -> null)   에서  [kim 10] [kim 30]

  kim=10 을 넣는다                    {kim=10}
  kim=30 이 온다 -> merge(10, 30) 호출 -> null 을 돌려받는다
        |
        v
  Map.merge 의 계약 — 결과가 null 이면 그 키를 제거한다
        |
        v
  {}    키 자체가 사라졌다
```

- 3인자 `toMap` 의 accumulator 가 **`map.merge(...)` 를 그대로 부르기** 때문이다.
- javadoc 도 merge 함수를 이렇게 설명한다.

> a merge function, used to resolve collisions between values associated with the same key, **as supplied to `Map.merge(Object, Object, BiFunction)`**

**왜 위험한가**

- **무음 실패**다. 예외도 로그도 없이 데이터가 사라진다.
- 더 나쁜 것은 **중복이 있을 때만** 사라진다는 점이다 — 테스트 데이터에는 중복이 없다.
- 방어: merge 함수는 **항상 값을 돌려준다.** "버리고 싶다"는 `toMap` 앞에서 `filter` 로 표현한다.

### 5. 집계 수집기의 반환 타입

**출력** (`Ex.java` — 47-e)

```text
counting()        : 5 (Long)
summingInt()      : 150 (Integer)
summingDouble()   : 150.0 (Double)
averagingInt()    : 30.0 (Double)
averagingDouble() : 30.0 (Double)
summarizingInt()  : IntSummaryStatistics{count=5, sum=150, min=10, average=30.000000, max=50}
maxBy : Optional[P[team=blue, name=jung, score=50]]
minBy : Optional[P[team=red, name=kim, score=10]]
```

**네 줄의 값과 타입**

| 수집기 | 값 | 타입 |
|---|---|---|
| `counting()` | 5 | **`Long`** |
| `summingInt(...)` | 150 | `Integer` |
| `averagingInt(...)` | 30.0 | **`Double`** |
| `maxBy(...)` | 점수 50인 `jung` | **`Optional<P>`** |

**`averagingInt` 가 `Integer` 가 아닌 이유**

- 평균은 **나눗셈**이다. 정수 나눗셈으로 버리면 답이 틀린다.
- 실측: `Stream.of(1, 2).collect(averagingInt(i -> i))` → **`1.5`**.\
  `int` 였다면 `1` 이 됐을 것이다.
- `averagingInt`·`averagingLong`·`averagingDouble` **셋 다 `Double`** 을 돌려준다.

**빈 스트림에서**

```text
== 빈 스트림에서 ==
counting()   : 0
summingInt() : 0
averagingInt(): 0.0
maxBy()      : Optional.empty
```

- **`averagingInt` 만 조심한다** — `NaN` 도 `Optional` 도 아니고 `0.0` 이다(8번).

**어느 것만 `Optional` 인가**

- **`minBy`/`maxBy` 뿐**이다.

```text
항등원이 있는 것                          항등원이 없는 것

  개수의 항등원 = 0                         최댓값의 항등원 = 없다
  합의 항등원   = 0                              |
  평균?          = 규약상 0.0                     v
        |                                    "없음"을 표현해야 한다
        v                                    -> Optional
  값을 그냥 돌려준다
```

- 평균은 **엄밀히는 항등원이 없는데도 `0.0`** 을 돌려준다. 이것이 8번의 함정이다.

### 6. `joining` 의 앞뒤 문자열

**출력** (`Ex.java` — 47-e)

```text
joining()        : kimleeparkchoijung
joining(", ")    : kim, lee, park, choi, jung
joining(구분,앞,뒤) : [kim, lee, park, choi, jung]
빈 스트림 + 앞뒤   : []
```

**두 줄**

- `[kim, lee, park, choi, jung]`
- 빈 스트림 → **`[]`**

**빈 스트림에서도 앞뒤가 붙는가**

- **붙는다.** 빈 문자열이 아니라 `[]` 다.

```text
joining(", ", "[", "]")

  원소 있음:  "["  +  kim  + ", " + ... + jung  +  "]"   ->  [kim, ..., jung]
  원소 없음:  "["                              +  "]"   ->  []
              앞뒤는 원소와 무관하게 언제나 붙는다
```

- JSON 배열·SQL `IN` 절을 만들 때 이 성질이 정확히 필요한 것이다.

**숫자 스트림에 바로 걸 수 있는가**

- **없다.** `joining` 은 `Collector<CharSequence, ?, String>` 이다.
- `map(String::valueOf)` 또는 `mapToObj(String::valueOf)` 를 먼저 건다.

**내부에서 무엇을 쓰는가**

- **`StringJoiner`**(내부적으로 `StringBuilder`)다.
- 루프 안 `+=` 보다 싸다 — 그 이유는 [**36번 주제**](../36-stringbuilder-and-concat/)가 정본이다.

### 7. 합계가 조용히 틀리는 자리

**출력** (`Ex.java` — 47-e)

```text
summingInt 오버플로 : -2147483648
summingLong 으로   : 2147483648
```

**두 줄의 결과**

- `summingInt` → **`-2147483648`** (`Integer.MIN_VALUE`)
- `summingLong` → **`2147483648`** (맞는 값)

**예외나 경고가 나는가**

- **안 난다.** `int` 덧셈의 오버플로는 Java 에서 조용히 감싸 돈다.

```text
Integer.MAX_VALUE + 1  =  2147483647 + 1

  0111...1111  (2147483647)
+ 0000...0001
= 1000...0000  ->  부호 비트가 켜진다  ->  -2147483648
```

- 이것은 `Collectors` 의 문제가 아니라 **`int` 산술의 성질**이다 — [**02번 주제**](../02-numeric-operations/)가 정본이다.

**무엇을 기본으로 쓰나**

- **금액·카운트 합계는 `summingLong`.**
- 정확한 돈 계산이면 `BigDecimal` 로 `reducing` 하거나 아예 스트림 밖에서 다룬다([**53번 주제**](../53-bigdecimal/)).

### 8. 빈 목록의 평균

**결과**

- **`0.0`** 이다.

**왜 위험한가**

```text
주문이 0건                                주문이 3건인데 전부 0원

  averagingInt -> 0.0                      averagingInt -> 0.0
        |                                        |
        +----------------+-----------------------+
                         v
              화면에는 "평균 0원" 으로 똑같이 보인다
```

- **"데이터 없음"과 "값이 0"을 구별할 수 없다.**
- 대시보드·리포트에서 조용히 틀리는 전형적인 자리다.

**구별하려면**

```java
IntSummaryStatistics st = orders.stream().collect(Collectors.summarizingInt(Order::amount));
if (st.getCount() == 0) { /* 데이터 없음 */ } else { st.getAverage(); }
```

- `summarizingInt` 하나로 count·sum·min·average·max 를 다 얻는다. 따로 다섯 번 돌리는 것보다 싸다.
- 또는 `mapToInt(...).average()` 를 쓰면 **`OptionalDouble`** 이 나와서 구별된다.

### 9. 이 코드는 왜 컴파일이 안 되는가

**출력** (`javac`, JDK 21.0.5)

```text
$ javac Ex.java
Ex.java:8: error: incompatible types: inference variable R has incompatible bounds
        System.out.println(k.stream().collect(Collectors.toMap(P::name, P::score, (a, b) -> b, TreeMap::new)));
                                             ^
    upper bounds: String,Map<K#1,U>,Object
    lower bounds: TreeMap<K#2,V>
```

**원인은 어느 쪽인가**

- **`println` 쪽이다.**

```text
4인자 toMap 의 시그니처:  <T,K,U,M extends Map<K,U>> Collector<T,?,M>

  M 을 정하려면 "무엇으로 받을 것인가"(대상 타입)가 필요하다
        |
        v
  println 은 오버로드가 많다 — String? Object? char[]?
        |
        v
  대상 타입이 하나로 안 정해진다 -> M 추론 실패
```

- `upper bounds: String, Map<K,U>, Object` 가 그 증거다 — 컴파일러가 세 후보를 동시에 요구받고 있다.

**어떻게 고치나**

```java
TreeMap<String, Integer> tm = src.stream()
        .collect(Collectors.toMap(P::name, P::score, (a,b)->b, TreeMap::new));
System.out.println(tm);
```

- **변수에 먼저 담는다.** 변수 선언이 대상 타입을 준다.
- 48번의 3인자 `groupingBy(classifier, TreeMap::new, downstream)` 에서도 같은 일이 난다.

### 10. 반환 타입은 어디까지 믿어도 되나

**`ArrayList` 를 가정해도 되는가**

- **안 된다.**

**`HashMap` 은**

- **안 된다.**

**javadoc 근거**

> (`toList`) There are no guarantees on the type, mutability, serializability, or thread-safety of the `List` returned.

> (`toMap`) There are no guarantees on the type, mutability, serializability, or thread-safety of the `Map` returned.

**그러면 무엇이 계약인가**

```text
계약인 것                                 계약이 아닌 것

  인터페이스 타입 (List / Set / Map)        구체 클래스 (ArrayList / HashMap)
  원소의 순서 (List 는 입력 순서)            Set·Map 의 순회 순서
  Stream.toList() 가 수정 불가              Collectors.toList() 가 수정 가능한 것
  toUnmodifiable* 가 null 에서 NPE          예외 메시지 문구
```

- **필요한 성질은 내가 명시한다** — 정렬이 필요하면 `toCollection(TreeSet::new)`, 순서가 필요하면 `LinkedHashMap::new`.
- "지금 `ArrayList` 니까 고칠 수 있다"에 기대지 않는다.\
  `Collectors.toList()` 가 수정 가능한 것조차 **javadoc 상 보장이 아니다.**

### 11. 17·21·25 에서 무엇이 달랐나

**메시지**

- **세 버전이 한 글자도 같았다.**

```text
IllegalStateException: Duplicate key kim (attempted merging values 10 and 30)
NullPointerException   (메시지 없음)
NullPointerException: Cannot invoke "Object.equals(Object)" because "e0" is null
```

**스택트레이스**

- **줄 번호가 전부 다르다.**

```text
                                      17           21           25
  Objects.requireNonNull            :209         :233         :220
  ArrayList$ArrayListSpliterator    :1625        :1708        :1716
  AbstractList$RandomAccess…        :720         :722         :722
  AbstractPipeline.copyInto         :509         :509         :570
  ReferencePipeline.collect         :682         :682         :723
  HashMap.merge                     :1355        :1363        :1364
  Collectors.lambda$toMap$…         :1673        :1636        :1642
```

**람다 이름**

- **바뀐다.**

```text
  21: Collectors.lambda$uniqKeysMapAccumulator$1(Collectors.java:182)
  25: Collectors.lambda$uniqKeysMapAccumulator$0(Collectors.java:182)
  21: Collectors.lambda$toMap$68(Collectors.java:1636)
  25: Collectors.lambda$toMap$0(Collectors.java:1642)
```

- 같은 파일 같은 줄인데 **합성 람다의 일련번호가 달라졌다.**

**테스트로 고정할 때**

```java
// 안 된다 — 메시지·스택트레이스 문자열
assertTrue(e.getMessage().startsWith("Duplicate key"));
assertTrue(trace.contains("lambda$uniqKeysMapAccumulator$1"));

// 된다 — 예외 타입과 결과 값
assertThrows(IllegalStateException.class, () -> ...);
assertEquals(Map.of("kim", 40, "lee", 20), result);
```

- **타입과 결과만 고정한다.** 메시지·스택트레이스·구체 클래스는 전부 구현 세부다.

### 12. 무엇을 고르는가

**리스트를 id 로 맵으로**

```java
// 기본 — 3인자. 중복 정책을 그 자리에서 적는다
users.stream().collect(Collectors.toMap(User::id, u -> u, (a, b) -> b));

// 유일성이 증명될 때만 — 2인자
users.stream().collect(Collectors.toMap(User::id, u -> u));
```

- 2인자는 "겹치면 죽어도 좋다"는 선언이다. 그게 의도면 맞는 선택이다.
- `(a, b) -> b` 가 `HashMap.put` 과 같은 동작(뒤쪽이 이김), `(a, b) -> a` 가 먼저 온 것이 이김.

**키 순서가 입력 순서여야 한다**

- **4인자 + `LinkedHashMap::new`**.
- 정렬 순서면 `TreeMap::new`. 기본 `HashMap` 은 **순서를 보장하지 않는다**(48번 (2)에서 실행으로 확인).

**중복 제거 + 입력 순서**

- `collect(Collectors.toCollection(LinkedHashSet::new))`.
- 실측: `Stream.of(3,1,2)` → `toSet()` 은 `[1, 2, 3]`, `LinkedHashSet` 은 `[3, 1, 2]`.

**개수만 센다**

- **`count()` 최종 연산**을 쓴다. `collect(counting())` 이 아니다.
- 이유: `count()` 는 소스가 크기를 알면 **순회를 아예 건너뛴다**(46번 4번).\
  `counting()` 은 원소를 하나씩 세므로 그 최적화가 없다.

**`counting()`·`summingInt()` 의 진짜 자리**

- **다운스트림**이다 — `groupingBy(P::team, counting())` 처럼.
- 단독으로 `collect(counting())` 을 쓸 일은 거의 없다. 48번이 그 이야기다.

---

## 실행 검증

| 프로그램 | 무엇을 확인했나 | 돌린 JDK |
|---|---|---|
| `Ex.java` (47-a) | `toList` 세 형태의 수정 가능성·`null`·구체 타입, `toSet`/`toUnmodifiableSet`/`toCollection`, 순서 | 17 · 21 · 25 (동일) |
| `Ex.java` (47-b) | `HashMap.put` 대 `toMap` 의 중복 키, merge 함수 세 가지, 맵 타입 지정, 스택트레이스 | 17 · 21 · 25 (**메시지 동일 · 줄 번호 다름**) |
| `Ex.java` (47-c) | `null` 값에서 2인자·3인자가 각각 다른 자리에서 던짐, 방어 세 가지 | 17 · 21 · 25 (**메시지 동일 · 줄 번호 다름**) |
| `Ex.java` (47-d) | `null` 키는 통과, `TreeMap::new` 면 `compareTo` 에서 NPE, 3인자 NPE 의 스택트레이스 | 17 · 21 · 25 (**메시지 동일 · 줄 번호·람다 번호 다름**) |
| `Ex.java` (47-e) | `joining` 셋, 집계 수집기의 타입과 빈 스트림, merge 가 `null` 을 돌려주면 항목 소멸, `summingInt` 오버플로 | 17 · 21 · 25 (동일) |
| `javac` 단독 (47-f) | 4인자 `toMap` 을 `println` 에 인라인했을 때의 추론 실패 메시지 | 21 |
| `src.zip` 열람 | `uniqKeysMapAccumulator`·`duplicateKeyException`·`toUnmodifiableMap` 소스, `toMap`/`toList` javadoc | 21 |

**구현 의존 항목** (버전이 오르면 다시 돌려야 하는 것)

- 구체 타입 `ArrayList`·`HashMap`·`HashSet`·`ImmutableCollections$ListN` — javadoc 이 보장하지 않는다.
- 예외 **메시지 문구** — 세 버전이 같았지만 계약이 아니다.
- 스택트레이스의 줄 번호와 **합성 람다 일련번호**(`lambda$toMap$68` vs `$0`) — 세 버전이 전부 달랐다.
- `toSet()` 의 순회 순서 — `HashSet` 의 해시 배치에 달려 있다.
- **Java 8 의 동작은 안 돌려 봄** — 이 머신에 8이 없다. `toUnmodifiable*`(10+)·`Stream.toList()`(16+)는 애초에 8에 없다.
