# java/syntax/41 — `Map` API: `merge`/`compute*`/`getOrDefault`/`putIfAbsent` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **선행** — [`../39-collections-framework-map/`](../39-collections-framework-map/). `Map` 이 `Collection` 이 아니라는 것과 뷰 셋이 전제다.
> **기준 소스** — JDK 21.0.5 의 `lib/src.zip` 을 **직접 풀어 읽은** javadoc 과 구현이다.\
> `java.base/java/util/Map.java` — `get`·`getOrDefault`·`computeIfAbsent`·`merge` 의 javadoc 과 `@implSpec` 기본 구현.\
> `java.base/java/util/HashMap.java` — `computeIfAbsent` 구현(`modCount` 대조 두 줄·`oldValue != null` 검사).\
> 인용은 **그 파일에서 복사한 것만** 옮겼다.
> **실행 검증** — 이 문서의 모든 출력·에러는 Temurin JDK 에서 **실제로 돌려** 얻은 것이다.\
> 프로그램 4개를 **17.0.13 · 21.0.5 · 25.0.1** 셋 다에서 돌려 `diff` 했다 — 본문 출력은 전부 같고 스택트레이스 줄 번호만 달랐다.
> **버전** — `getOrDefault`·`putIfAbsent`·`compute*`·`merge`·`replaceAll`·`forEach` 는 전부 **Java 8**.\
> `Map.of`·`Map.entry`·`Map.ofEntries` 는 **Java 9**, `Map.copyOf` 는 **Java 10**.\
> `@since` 는 전부 `src.zip` 에서 직접 읽었다.
> **범위** — 해시 테이블이 어떻게 동작하나(버킷·충돌·리사이즈·트리화)는
> [`../../../../../data-structure/05-hashmap/`](../../../../../data-structure/05-hashmap/)·[`../../../../../data-structure/29-open-addressing/`](../../../../../data-structure/29-open-addressing/) 가 정본이다.\
> 그쪽은 **해시가 어떻게 자리를 찾나**까지, 여기는 **`java.util.Map` 이 그 위에 얹은 메서드들의 계약**부터다.\
> `Collectors.toMap`·`groupingBy` 는 [`../47-collectors-basics/`](../47-collectors-basics/)·[`../48-collectors-grouping/`](../48-collectors-grouping/) 가 정본이다.
> 이 본문은 Claude 작성이다(원고 없음).

## 한눈에 — 쉽게 말하면

**`Map` 의 갱신 메서드 다섯은 「사물함에 짐을 넣는 다섯 가지 규칙」이다.**

| 비유 | 실체 | 칸이 비었으면 | 칸에 짐이 있으면 |
|---|---|---|---|
| 무조건 넣고 있던 건 꺼내 준다 | **`put(k, v)`** | 넣는다 | **덮어쓴다** |
| 비었을 때만 넣는다 | **`putIfAbsent(k, v)`** | 넣는다 | 그대로 둔다 |
| 비었을 때만 **만들어서** 넣는다 | **`computeIfAbsent(k, f)`** | `f` 를 불러 넣는다 | **`f` 를 안 부른다** |
| 있을 때만 바꾼다 | **`computeIfPresent(k, f)`** | 아무것도 안 한다 | `f(k, 옛값)` 으로 바꾼다 |
| 항상 부르고 결과로 바꾼다 | **`compute(k, f)`** | `f(k, null)` | `f(k, 옛값)` |
| 없으면 넣고 있으면 합친다 | **`merge(k, v, f)`** | **`v` 를 그냥 넣는다** | `f(옛값, v)` |

**똑같은 구조로** 자바가 동작한다: 사물함 칸 = 키, 짐 = 값.

그런데 사물함에 **셋째 상태**가 있다.

```text
   칸의 상태는 셋이다

   (1) 칸 자체가 없다            containsKey = false   get = null
   (2) 칸에 짐이 있다            containsKey = true    get = 짐
   (3) 칸은 있는데 짐이 null     containsKey = true    get = null   <- 여기
                                      ^
                          get() 만 보면 (1) 과 구분이 안 된다
```

- **`HashMap` 은 값으로 `null` 을 받는다.** 그래서 (3)이 생긴다.
- **다섯 메서드 중 넷이 (3)을 (1)로 취급한다.** 그것이 이 주제의 핵심이다.
- 그리고 **람다가 `null` 을 돌려주면 칸 자체가 사라진다.** 예외도 경고도 없다.

실무에서 이게 터지는 자리는 **"캐시에 없으면 계산해서 넣자"** 한 줄이다.

```java
cache.computeIfAbsent(key, k -> loadFromDb(k));   // loadFromDb 가 null 을 주면?
```

`null` 은 저장되지 않는다. **다음에도 또 DB 를 친다.** 아무 에러도 없다.

> **`null` 값(null value)** — 키는 있는데 값이 `null` 인 상태. `HashMap` 만의 이야기다(`ConcurrentHashMap` 은 금지).\
> 예: `m.put("a", null)` 뒤 `m.containsKey("a")` 는 `true`, `m.get("a")` 는 `null`.

> **재매핑 함수(remapping function)** — `compute`·`merge` 에 넘기는 "옛값으로 새 값을 만드는" 함수.\
> 예: `merge(k, 1, Integer::sum)` 의 `Integer::sum` 이 그것이다.

## 이 주제가 답하려는 질문

원고가 없는 API 주제라 「문제」 대신 이 세 질문을 둔다.

1. `merge` · `compute` · `computeIfAbsent` 는 **언제 람다를 부르고 언제 안 부르나** — 그 차이가 왜 중요한가.
2. **"키가 없다"와 "값이 `null` 이다"를 어느 메서드가 구분하고 어느 메서드가 못 하나.**
3. `entrySet`·`keySet`·`values` 가 **뷰**라는 것이 무엇을 바꾸나 —
   그리고 `computeIfAbsent` 안에서 같은 맵을 고치면 무슨 일이 나나.

## 예시 데이터 — 이 묶음이 공유하는 것

39~43번은 같은 데이터를 쓴다.

```text
과일 다섯 개 (중복 하나)
  "pear"  "apple"  "fig"  "apple"  "date"

메서드 격자용 축소판 — 키 하나짜리 맵의 세 상태
  {}          키가 없다
  {k=1}       값이 있다
  {k=null}    키는 있는데 값이 null      <- 이 주제의 주인공
```

## 동작 방식

### (1) 다섯 메서드의 전수 격자 — 한 표로 끝난다

**언제 쓰나** — 어느 메서드를 쓸지 고를 때. 이 표가 이 주제의 결론이다.

**실행 결과** (`Ex.java` — 41-a, 17·21·25 동일 — `LinkedHashMap` 으로 순서를 고정했다)

```text
메서드 (반환값 / 호출 뒤 맵)                    {}  (키 없음)                {k=1} (값 있음)              {k=null} (값이 null)        
--------------------------------------------------------------------------------------------------------------------
get("k")                              null / {}                 1 / {k=1}                 null / {k=null}           
getOrDefault("k", 9)                  9 / {}                    1 / {k=1}                 null / {k=null}           
containsKey("k")                      false / {}                true / {k=1}              true / {k=null}           
put("k", 5)                           null / {k=5}              1 / {k=5}                 null / {k=5}              
putIfAbsent("k", 5)                   null / {k=5}              1 / {k=1}                 null / {k=5}              
computeIfAbsent("k", x -> 5)          5 / {k=5}                 1 / {k=1}                 5 / {k=5}                 
computeIfPresent("k",(x,v)->5)        null / {}                 5 / {k=5}                 null / {k=null}           
compute("k", (x,v) -> 5)              5 / {k=5}                 5 / {k=5}                 5 / {k=5}                 
compute("k", (x,v) -> v)              null / {}                 1 / {k=1}                 null / {}                 
merge("k", 5, (o,n) -> o+n)           5 / {k=5}                 6 / {k=6}                 5 / {k=5}                 
replace("k", 5)                       null / {}                 1 / {k=5}                 null / {k=5}              
remove("k")                           null / {}                 1 / {}                    null / {}                 
computeIfAbsent -> null               null / {}                 1 / {k=1}                 null / {k=null}           
compute -> null                       null / {}                 null / {}                 null / {}                 
merge("k",5,(o,n) -> null)            5 / {k=5}                 null / {}                 5 / {k=5}                 
merge("k", null, (o,n) -> o+n)        NullPointerException / {} NullPointerException / {k=1}NullPointerException / {k=null}
```

```text
   셋째 칸(값이 null)을 첫째 칸(키 없음)처럼 다루는 메서드

     putIfAbsent       -> 넣는다        (있는 키를 덮어썼다)
     computeIfAbsent   -> 만들어 넣는다  (람다를 부른다)
     computeIfPresent  -> 아무것도 안 함 (있는데 없다고 본다)
     merge             -> 그냥 넣는다    (합치는 함수를 안 부른다)

   구분하는 메서드
     containsKey       -> true          <- 유일하게 정직하다
     compute           -> 람다를 부른다  (옛값이 null 로 온다 — 키 없음과 같은 모양)
     replace           -> 바꾼다        (키 없음일 때는 안 바꾼다)
```

그림 해설 (한 단계씩):

- **`containsKey` 만이 셋째 상태를 확실히 구분한다.**
- `compute` 는 **람다를 부르기는 하는데** 옛값이 `null` 로 오므로 람다 안에서는 구분이 안 된다.
- `replace` 는 구분하지만 **반환값이 둘 다 `null`** 이라 호출자는 결과로 구분할 수 없다.
- 나머지 넷은 아예 "키가 없다"로 취급한다.

비용 — 이 표를 외우지 말고 **"값에 `null` 을 안 넣는다"를 규칙으로 삼으면** 표가 필요 없어진다.\
셋째 칸이 없으면 나머지는 직관대로 동작한다.

### (2) 람다가 언제 불리나 — `computeIfAbsent`·`merge`·`compute`

**언제 쓰나** — 람다 안에 비싼 작업(DB 조회·객체 생성)이 있을 때. 불리는지 아닌지가 성능과 정합성을 가른다.

**실행 결과** (`Ex.java` — 41-a, 17·21·25 동일)

```text
--- 람다가 실제로 불렸나
absent       computeIfAbsent 람다 호출 : true
present      computeIfAbsent 람다 호출 : false
null-value   computeIfAbsent 람다 호출 : true
absent       merge 람다 호출          : 안 불림
present      merge 람다 호출          : [old=1 new=5]
null-value   merge 람다 호출          : 안 불림
absent       compute 람다 호출        : [old=null]
present      compute 람다 호출        : [old=1]
null-value   compute 람다 호출        : [old=null]
```

```text
                      키 없음      값 있음      값이 null

  computeIfAbsent      부른다       안 부른다     부른다
  merge                안 부른다     부른다       안 부른다
  compute              부른다       부른다       부른다
                         ^
                    세 상태 전부에서 부른다 = 가장 비싸고 가장 예측 가능
```

그림 해설 (한 단계씩):

- **`computeIfAbsent` 와 `merge` 는 정반대다.** 하나는 없을 때, 하나는 있을 때 부른다.
- `merge` 가 키 없음에서 람다를 안 부르는 이유는 **기본 구현이 그렇게 생겼기** 때문이다.

```java
// JDK 21.0.5  java.base/java/util/Map.java  1317~1330행 — 실제 소스 그대로
    default V merge(K key, V value,
            BiFunction<? super V, ? super V, ? extends V> remappingFunction) {
        Objects.requireNonNull(remappingFunction);
        Objects.requireNonNull(value);
        V oldValue = get(key);
        V newValue = (oldValue == null) ? value :
                   remappingFunction.apply(oldValue, value);
        if (newValue == null) {
            remove(key);
        } else {
            put(key, newValue);
        }
        return newValue;
    }
```

- **`oldValue == null` 하나로 "키 없음"과 "값이 `null`" 을 묶어 버린다.** 두 줄에 전부 들어 있다.
- `Objects.requireNonNull(value)` 도 보인다 — **`merge` 의 둘째 인자에 `null` 을 못 준다.**

비용 — `merge` 가 가장 짧다. 카운팅은 한 줄이다.

```java
counts.merge(word, 1, Integer::sum);        // 없으면 1, 있으면 옛값+1
```

`computeIfAbsent` 로 같은 일을 하면 두 줄이 되고, `get`+`put` 으로 하면 세 줄에 경쟁 조건이 생긴다.

### (3) ★ `null` 값의 의미가 갈리는 자리 — `getOrDefault`

**언제 쓰나** — "없으면 기본값" 을 쓸 때. 즉 거의 언제나.

**실행 결과** (`Ex.java` — 41-a, 위 격자에서 뽑은 것)

```text
get("k")                              null / {}                 1 / {k=1}                 null / {k=null}
getOrDefault("k", 9)                  9 / {}                    1 / {k=1}                 null / {k=null}
containsKey("k")                      false / {}                true / {k=1}              true / {k=null}
```

```text
   "기본값을 준다" 는 약속이 지켜지지 않는 칸

     m = {}            m.getOrDefault("k", 9)  ->  9     약속대로
     m = {k=1}         m.getOrDefault("k", 9)  ->  1     약속대로
     m = {k=null}      m.getOrDefault("k", 9)  ->  null  <- 9 가 아니다
                                                    |
                        호출자가 결과를 null 검사만 한다면
                        {} 인지 {k=null} 인지 구분할 수 없다
```

그림 해설 (한 단계씩):

- **`getOrDefault` 는 "값이 없으면"이 아니라 "키가 없으면" 기본값을 준다.**
- 값이 `null` 이면 그 `null` 을 그대로 돌려준다. 기본값이 아니다.
- 기본 구현이 그 사정을 그대로 보여 준다.

```java
// JDK 21.0.5  java.base/java/util/Map.java  689~694행 — 실제 소스 그대로
    default V getOrDefault(Object key, V defaultValue) {
        V v;
        return (((v = get(key)) != null) || containsKey(key))
            ? v
            : defaultValue;
    }
```

- `get` 이 `null` 이어도 **`containsKey` 가 `true` 면 그 `null` 을 돌려준다.**
- 그래서 세 상태 중 **둘째·셋째가 같은 처리**를 받는다.
- javadoc 은 `get` 쪽에서 이 모호성을 미리 경고한다.

> If this map permits null values, then a return value of `null` does not *necessarily* indicate that the map contains no mapping for the key; it's also possible that the map explicitly maps the key to `null`. The `containsKey` operation may be used to distinguish these two cases.

비용 — 구분해야 하면 **`containsKey` 를 쓸 수밖에 없다.** 조회가 두 번이 된다.\
그래서 실무 답은 "구분하지 않아도 되게 만든다" — **값에 `null` 을 안 넣는다.**

### (4) 람다가 `null` 을 돌려주면 칸이 사라진다

**언제 쓰나** — 재매핑 함수 안에서 조건부로 "이건 버리자"를 표현하려 할 때.

**실행 결과** (`Ex.java` — 41-a, 위 격자에서 뽑은 것)

```text
compute("k", (x,v) -> v)              null / {}                 1 / {k=1}                 null / {}
compute -> null                       null / {}                 null / {}                 null / {}
merge("k",5,(o,n) -> null)            5 / {k=5}                 null / {}                 5 / {k=5}
computeIfAbsent -> null               null / {}                 1 / {k=1}                 null / {k=null}
```

```text
   {k=null} 에 compute(k, (x, v) -> v) 를 걸면

     옛값 null 을 그대로 돌려준다
            |
     Map.compute 의 계약: 결과가 null 이면 그 키를 제거한다
            |
            v
     {}     <- 예외도 경고도 없이 키가 사라졌다
             "아무것도 안 바꾸는 항등 함수"인데 데이터가 지워졌다
```

그림 해설 (한 단계씩):

- ★ **`compute(k, (x, v) -> v)` 는 항등 함수처럼 보이는데 `{k=null}` 을 지운다.**
- `merge` 도 마찬가지다 — 재매핑이 `null` 을 주면 `remove(key)` 를 부른다((2)의 소스 참조).
- **`computeIfAbsent` 만 다르다.** 람다가 `null` 을 주면 **넣지 않고 끝낸다** — 지우지도 않는다.

```text
  결과가 null 일 때의 처리

    compute          -> remove(key)        키를 지운다
    computeIfPresent -> remove(key)        키를 지운다
    merge            -> remove(key)        키를 지운다
    computeIfAbsent  -> 아무것도 안 한다    키가 없으면 없는 채로
```

- 전형적인 무음 실패다. **"버림"을 `null` 로 표현하지 않는다.**

비용 — 없다(그것이 문제다). 방어는 **재매핑 함수가 `null` 을 절대 안 돌려주게 쓰는 것**뿐이다.\
버려야 하면 `remove` 를 명시적으로 부른다.

### (5) `computeIfAbsent` 안에서 같은 맵을 고치면

**언제 쓰나** — 람다 안에서 다른 키도 같이 채우고 싶을 때. 재귀적으로 색인을 만들 때.

**실행 결과** (`Ex.java` — 41-b, JDK 21.0.5)

```text
--- 1) computeIfAbsent 안에서 같은 맵을 고치면 (HashMap)
java.util.ConcurrentModificationException
	at java.base/java.util.HashMap.computeIfAbsent(HashMap.java:1229)
	at Ex.main(Ex.java:9)
--- 2) 재귀 computeIfAbsent (같은 맵, 다른 키)
예외 : java.util.ConcurrentModificationException
--- 3) 같은 키로 재귀하면
예외 : java.util.ConcurrentModificationException
--- 4) TreeMap 은 어떤가
예외 : java.util.ConcurrentModificationException
--- 5) LinkedHashMap 은 어떤가
예외 : java.util.ConcurrentModificationException
--- 6) 맵을 안 늘리면 (충분히 큰 맵에 put) 
기존 키 갱신 : 예외 없음. {p0=99, p1=1, p2=2, p3=3, k=5}
--- 7) merge 안에서 고치면
예외 : java.util.ConcurrentModificationException
--- 8) compute 안에서 고치면
예외 : java.util.ConcurrentModificationException
```

```text
   HashMap.computeIfAbsent 의 실제 구현

     int mc = modCount;                  <- 람다를 부르기 전 기록
     V v = mappingFunction.apply(key);   <- 여기서 맵을 고치면 modCount 가 오른다
     if (mc != modCount) { throw new ConcurrentModificationException(); }
                                          ^
                         "구조적으로 바뀌었나" 만 본다
```

그림 해설 (한 단계씩):

- **`compute*`·`merge` 넷 다 막는다.** `HashMap`·`LinkedHashMap`·`TreeMap` 전부.
- 실제 소스가 그대로 보여 준다.

```java
// JDK 21.0.5  java.base/java/util/HashMap.java  1226~1228행 — 실제 소스 그대로
        int mc = modCount;
        V v = mappingFunction.apply(key);
        if (mc != modCount) { throw new ConcurrentModificationException(); }
```

- ★ **그런데 (6)이 안 터진다.** 람다 안에서 **이미 있는 키의 값만 바꾸면** `modCount` 가 안 오른다.\
  `modCount` 는 **구조적 수정**(크기 변화)만 센다.
- javadoc 이 애초에 이것을 보장으로 약속하지 않는다.

> The mapping function should not modify this map during computation.

> The default implementation makes no guarantees about detecting if the mapping function modifies this map during computation and, if appropriate, reporting an error. Non-concurrent implementations should override this method and, **on a best-effort basis**, throw a `ConcurrentModificationException` if it is detected that the mapping function modifies this map during computation.

- **"best-effort"** 라고 적혀 있다. (6)이 그 한계의 실물이다.
- 같은 성질이 순회 쪽에도 있다 — [`../43-iterator-and-fail-fast/`](../43-iterator-and-fail-fast/) 가 정본이다.

비용 — 람다 안에서는 **맵을 읽지도 쓰지도 않는다**를 규칙으로 삼는다.\
안전한 형태는 값을 만들어 돌려주기만 하는 것이다.

```text
--- 9) 안전한 형태
computeIfAbsent 로 만든 색인 : {a=[apple, avocado], b=[banana, blueberry], c=[cherry]}
```

```java
for (String w : words)
    idx.computeIfAbsent(w.substring(0, 1), x -> new ArrayList<>()).add(w);
```

- 람다는 **빈 리스트를 만들 뿐** 맵을 건드리지 않는다. `.add(w)` 는 람다 밖에서 일어난다.

### (6) `entrySet`·`keySet`·`values` 는 뷰다

**언제 쓰나** — 맵의 일부만 넘기거나, 순회하며 값을 고칠 때.

**실행 결과** (`Ex.java` — 41-c, 17·21·25 동일)

```text
--- 1) entrySet·keySet·values 는 뷰다
맵      : {a=1, b=2, c=3}
keySet  : [a, b, c]  (java.util.LinkedHashMap$LinkedKeySet)
values  : [1, 2, 3]  (java.util.LinkedHashMap$LinkedValues)
맵에 d 추가 후 keySet : [a, b, c, d] / values : [1, 2, 3, 4] / entrySet 크기 : 4
--- 2) 뷰를 고치면 맵이 바뀐다
keySet.remove("a") 후 맵 : {b=2, c=3, d=4}
values.remove(2) 후 맵    : {c=3, d=4}
keySet.add("z") 는?      : UnsupportedOperationException
--- 3) Entry.setValue 는 맵에 쓴다
setValue 로 전부 x10 : {a=10, b=20}
같은 일을 replaceAll 로 : OK -> {a=11, b=21}
```

```text
      map {a=1, b=2, c=3}
        |
   +----+----+----------+
   |         |          |
 keySet   values    entrySet        <- 셋 다 저장하지 않는다. map 을 본다
   |         |          |
 remove    remove   Entry.setValue
   |         |          |
   +---------+----------+
             |
          map 이 바뀐다               add 만 막혀 있다 (키만으로는 값을 정할 수 없다)
```

그림 해설 (한 단계씩):

- **셋 다 복사본이 아니다.** 맵에 넣으면 뷰에 나타나고, 뷰에서 지우면 맵에서 지워진다.
- **`keySet().add` 만 막혀 있다.** 키만 받아서는 값을 무엇으로 할지 정할 수 없기 때문이다.
- `Entry.setValue` 는 **맵에 직접 쓴다.** 순회하며 값을 고치는 유일하게 안전한 길이다.
- `replaceAll` 이 같은 일을 한 줄로 한다 — **Java 8** 부터.

비용 — 뷰를 넘기면 복사 비용이 없다. 대신 **받는 쪽이 원본을 고칠 수 있다.**\
경계를 넘길 때는 `Set.copyOf(m.keySet())` 로 끊는다([`../40-list-set-and-immutable-factories/`](../40-list-set-and-immutable-factories/)).

### (7) 순회가 끝난 `Entry` 를 들고 있으면

**언제 쓰나** — `entrySet().iterator().next()` 로 첫 항목을 꺼내 보관할 때.

**실행 결과** (`Ex.java` — 41-c, 17·21·25 동일)

```text
--- 4) 순회가 끝난 Entry 를 들고 있으면
보관한 Entry      : a=1  (java.util.HashMap$Node)
맵을 고친 뒤 held : a=7
키를 지운 뒤 held : a=7 / setValue : OK / 그 뒤 held : a=9 / 맵 : {}
--- 5) Map.entry 로 만든 것은 뷰가 아니다
Map.entry("a",1)  : a=1  (java.util.KeyValueHolder)
setValue          : UnsupportedOperationException: not supported
```

```text
   HashMap$Node 를 들고 있다가 키를 지우면

     map {a=1}              held -> Node(a=1)
     map.put("a", 7)        held -> Node(a=7)    맵과 이어져 있다
     map.remove("a")        held -> Node(a=7)    노드는 살아 있다
     held.setValue(9)       held -> Node(a=9)    OK — 예외가 없다
     map                    {}                   <- 맵에는 반영되지 않는다
```

그림 해설 (한 단계씩):

- **`entrySet` 이 돌려주는 `Entry` 는 맵의 내부 노드 그 자체**다(`HashMap$Node`).
- 키가 지워져도 **노드 객체는 살아 있고 `setValue` 가 성공한다.** 맵과는 끊겼는데도.
- 그래서 **`Entry` 를 순회 밖으로 들고 나가면 안 된다.** javadoc 이 그대로 적어 놓았다.

> Replaces the value corresponding to this entry with the specified value (optional operation). (Writes through to the map.) **The behavior of this call is undefined if the mapping has already been removed from the map** (by the iterator's `remove` operation).
- **`Map.entry(k, v)`(9+)는 다르다.** `KeyValueHolder` 라는 독립 객체이고 `setValue` 가 막혀 있다.

비용 — 보관해야 하면 **키와 값을 따로 꺼내거나 `Map.entry(e.getKey(), e.getValue())` 로 복사**한다.

### (8) 순회 중 맵을 고치면

**언제 쓰나** — 조건에 맞는 항목을 지울 때.

**실행 결과** (`Ex.java` — 41-c, 17·21·25 동일)

```text
--- 7) 순회 중 맵을 고치면
k1 제거 : java.util.ConcurrentModificationException
removeIf : 예외 없음 {k0=0, k2=2, k3=3, k4=4}
Iterator.remove : 예외 없음 {k0=0, k2=2, k3=3, k4=4}
```

```java
for (String k : m.keySet()) if (k.equals("k1")) m.remove(k);   // CME
m.keySet().removeIf(k -> k.equals("k1"));                       // OK
m.entrySet().removeIf(e -> e.getValue() == 1);                  // OK
m.values().removeIf(v -> v == 1);                               // OK
```

- 뷰에서 지우는 것은 **맵을 통하지 않으므로** 안전하다.
- 자세한 규칙과 **안 터지는 경우**는 [`../43-iterator-and-fail-fast/`](../43-iterator-and-fail-fast/) 가 정본이다.

비용 — `removeIf` 가 가장 짧고 가장 안전하다. **키·값·항목 어느 기준으로도 지울 수 있다.**

## 문법 — 형태와 규칙

직접 쓴 최소 예제다. 출력은 전부 실행 결과다.

### 언제 무엇을 쓰나 — 관용구 표

| 하고 싶은 일 | 쓰는 것 | 한 줄 |
|---|---|---|
| 단어 세기 | **`merge`** | `counts.merge(w, 1, Integer::sum)` |
| 금액 누적 | **`merge`** | `sum.merge(id, amt, BigDecimal::add)` |
| 없으면 만들어 담기(멀티맵) | **`computeIfAbsent`** | `idx.computeIfAbsent(k, x -> new ArrayList<>()).add(v)` |
| 캐시 — 없으면 계산 | `computeIfAbsent` | `cache.computeIfAbsent(k, this::load)` |
| 있을 때만 갱신 | `computeIfPresent` | `m.computeIfPresent(k, (x, v) -> v + 1)` |
| 없으면 기본값으로 읽기 | **`getOrDefault`** | `counts.getOrDefault(k, 0)` |
| 처음 한 번만 등록 | `putIfAbsent` | `registry.putIfAbsent(name, handler)` |
| 값 전부 변환 | **`replaceAll`** | `m.replaceAll((k, v) -> v.trim())` |
| 조건으로 삭제 | **`entrySet().removeIf`** | `m.entrySet().removeIf(e -> e.getValue() == 0)` |
| 전부 순회 | `forEach` | `m.forEach((k, v) -> ...)` |
| 상수 맵 | `Map.of` (9+) | `Map.of("a", 1, "b", 2)` |
| 11쌍 이상 상수 맵 | `Map.ofEntries` (9+) | `Map.ofEntries(Map.entry("a",1), ...)` |
| 받은 맵을 얼려 보관 | `Map.copyOf` (10+) | `this.conf = Map.copyOf(conf)` |

- **카운팅은 `merge` 가 정답이다.** `getOrDefault` + `put` 은 두 번 조회한다.

```java
// 세 줄짜리 옛 관용구
Integer old = counts.get(w);
counts.put(w, old == null ? 1 : old + 1);

// getOrDefault 관용구 — 여전히 두 번 조회
counts.put(w, counts.getOrDefault(w, 0) + 1);

// merge — 한 번 조회, 한 줄
counts.merge(w, 1, Integer::sum);
```

### `computeIfAbsent` 의 반환값은 "지금 그 키의 값" 이다

```java
List<String> bucket = idx.computeIfAbsent(key, k -> new ArrayList<>());
bucket.add(value);
```

- 새로 만들었든 이미 있었든 **그 키에 들어 있는 값**을 돌려준다. 그래서 곧바로 `.add` 할 수 있다.
- 단 람다가 `null` 을 돌려주면 **반환값도 `null`** 이다 — 거기서 `.add` 하면 NPE 다.

### 불변 맵의 뷰

**실행 결과** (`Ex.java` — 41-c, 17·21·25 동일)

```text
--- 6) 불변 맵의 뷰
Map.of.keySet().remove : java.lang.UnsupportedOperationException: remove
Map.of 의 Entry.setValue : java.lang.UnsupportedOperationException: not supported
```

- javadoc 이 "불변 컬렉션에서 파생된 뷰도 불변이어야 한다"고 못박아 놓았다.
- 메시지가 다르다 — `remove` 는 `Iterator.remove` 기본 구현, `not supported` 는 `KeyValueHolder` 다.

### `Map.of` 는 `null` 도 중복 키도 거부한다

```java
Map.of("a", 1, "a", 2)      // IllegalArgumentException: duplicate key: a
Map.of("a", null)           // NullPointerException
```

- 자세한 것은 [`../40-list-set-and-immutable-factories/`](../40-list-set-and-immutable-factories/) 가 정본이다.

## 어디서 틀리나

### 1. ★ 캐시에 `null` 이 저장될 거라고 믿는다

```java
cache.computeIfAbsent(key, k -> loadFromDb(k));   // loadFromDb 가 null 을 주면
```

**실행 결과** (`Ex.java` — 41-d, 17·21·25 동일)

```text
--- 2) negative caching — 람다가 null 을 주면 몇 번 불리나
  호출 1 : 반환 null / 맵 {} / 람다 누적 호출 1
  호출 2 : 반환 null / 맵 {} / 람다 누적 호출 2
  호출 3 : 반환 null / 맵 {} / 람다 누적 호출 3
  Optional 로 감싸면
  호출 1 : 반환 Optional.empty / 맵 {missing=Optional.empty} / 람다 누적 호출 1
  호출 2 : 반환 Optional.empty / 맵 {missing=Optional.empty} / 람다 누적 호출 1
  호출 3 : 반환 Optional.empty / 맵 {missing=Optional.empty} / 람다 누적 호출 1
```

- **아무것도 저장되지 않는다.** 반환값도 `null` 이고 맵은 그대로다.
- 세 번 부르면 **람다도 세 번 불린다.** 에러도 로그도 없다 — 조용히 캐시가 안 먹는다.
- 이것을 "negative caching 이 안 된다"고 부른다.
- 방어: **`Optional` 을 값으로 넣는다**([`../38-optional/`](../38-optional/)) — 위 출력에서 람다가 한 번만 불린다. 센티널 객체도 같은 역할을 한다.

### 2. `getOrDefault` 가 `null` 값을 기본값으로 바꿔 줄 거라고 믿는다

```java
int n = m.getOrDefault("k", 0);      // {k=null} 이면 NullPointerException (언박싱)
```

**실행 결과** (`Ex.java` — 41-d, 17·21·25 동일)

```text
--- 1) getOrDefault 의 결과를 int 에 담으면
{}       -> int n = m.getOrDefault("k", 0) : 0
{k=null} -> int n = m.getOrDefault("k", 0) : NullPointerException: Cannot invoke "java.lang.Integer.intValue()" because the return value of "java.util.Map.getOrDefault(Object, Object)" is null
```

- `null` 이 그대로 나오고, `int` 로 언박싱하다 **NPE** 가 난다.
- ★ 다행히 **메시지가 `getOrDefault` 를 지목한다**(JDK 14+ helpful NullPointerException). 그 전 버전에서는 원인이 안 보였다.
- 방어: 애초에 값에 `null` 을 넣지 않는다.

### 3. `compute` 의 람다에서 옛값을 그대로 돌려준다

```java
m.compute(k, (key, v) -> v);          // {k=null} 이면 키가 사라진다
```

- **아무것도 안 바꾸려고 쓴 코드인데 데이터가 지워진다.**
- `merge`·`computeIfPresent` 도 같다 — 결과가 `null` 이면 `remove` 다.
- 방어: 재매핑 함수는 **절대 `null` 을 돌려주지 않는다**를 규칙으로.

### 4. `computeIfAbsent` 안에서 같은 맵을 고친다

```java
m.computeIfAbsent("a", k -> { m.put("b", 1); return 2; });   // ConcurrentModificationException
```

- 재귀 `computeIfAbsent` 도 마찬가지다. **같은 키로 재귀해도 터진다.**
- 그런데 ★ **이미 있는 키의 값만 바꾸면 안 터진다.** 감지는 `modCount` 기반이라 best-effort 다.
- 방어: 람다 안에서 맵을 안 건드린다. 값만 만들어 돌려준다.

### 5. `Entry` 를 순회 밖으로 들고 나간다

```java
Map.Entry<String,Integer> first = m.entrySet().iterator().next();
cache.put(k, first);           // 맵의 내부 노드를 캐시에 넣었다
```

- `HashMap$Node` 그 자체다. 맵이 바뀌면 값이 따라 바뀌고, 키가 지워져도 객체는 산다.
- `setValue` 가 **성공하는데 맵에는 반영되지 않는** 상태가 된다.
- 방어: `Map.entry(e.getKey(), e.getValue())` 로 복사한다.

### 6. `keySet()` 으로 순회하며 `get` 한다

```java
for (String k : m.keySet()) { use(k, m.get(k)); }      // 조회가 두 번
```

- `entrySet()` 이면 한 번이다.
- 그리고 `keySet()` 으로 돌면서 `m.remove(k)` 를 하면 **`ConcurrentModificationException`** 이다.

### 7. `Map.Entry` 를 정렬에 쓰면서 뷰인 것을 잊는다

```java
List<Map.Entry<String,Integer>> es = new ArrayList<>(m.entrySet());
es.sort(Map.Entry.comparingByValue());
// es 의 원소는 여전히 맵의 내부 노드다 — setValue 가 맵에 쓴다
```

**실행 결과** (`Ex.java` — 41-d, 17·21·25 동일)

```text
--- 6) Entry 를 정렬해도 원소는 복사되지 않는다
정렬한 리스트 : [b=1, c=2, a=3]
es.get(0).setValue(99) 후 원본 맵 : {a=3, b=99, c=2}
Map.entry 로 복사한 것에 setValue : UnsupportedOperationException: not supported
```

- 리스트는 복사됐지만 **원소는 복사되지 않았다.** `setValue` 가 원본 맵에 그대로 쓴다.
- 방어: `m.entrySet().stream().map(e -> Map.entry(e.getKey(), e.getValue())).toList()` — 그러면 `setValue` 자체가 막힌다.

### 8. `merge` 의 둘째 인자에 `null` 을 준다

```java
m.merge(k, maybeNull, (a, b) -> b);     // NullPointerException
```

- `Objects.requireNonNull(value)` 가 첫 줄에 있다((2)의 소스).
- **맵의 상태와 무관하게** 던진다 — 격자의 마지막 줄이 그것이다.

### 9. `ConcurrentHashMap` 에 같은 습관을 쓴다

- `ConcurrentHashMap` 은 **키도 값도 `null` 을 금지**한다(39번 (4)).
- 그래서 이 주제의 "셋째 상태" 문제가 아예 없다 — 그것이 의도된 설계다.
- 대신 `computeIfAbsent` 의 람다 안에서 같은 맵을 고치면 **`IllegalStateException`** 이 나거나 교착할 수 있다.
  javadoc 이 그렇게 갈라 적는다. 자세한 계약은 [**55번 주제**](../55-atomics-and-concurrent-collections/)가 정본이다.

## 구현 세부사항 대 언어 보장

| 관측한 것 | 보장인가 | 근거 |
|---|---|---|
| `get` 이 `null` 일 때 `containsKey` 로 구분 | **보장** | `Map.get` javadoc — "The `containsKey` operation may be used to distinguish these two cases" |
| `getOrDefault` 가 `null` 값에 `null` 을 돌려줌 | **보장** | `@implSpec` 의 기본 구현이 명시돼 있다 |
| `merge` 가 `null` 값에서 람다를 안 부름 | **보장** | `@implSpec` — `(oldValue == null) ? value : remap(...)` |
| `compute`/`merge` 가 `null` 결과에 키를 제거 | **보장** | `@implSpec` — `if (newValue == null) map.remove(key)` |
| `computeIfAbsent` 가 `null` 결과를 안 넣음 | **보장** | `@implSpec` — `if (newValue != null) map.put(...)` |
| `merge(k, null, f)` 가 NPE | **보장** | javadoc `@throws NullPointerException if ... the value ... is null` |
| 람다 안에서 맵을 고치면 **CME** | **보장 아님 — best-effort** | "makes no guarantees about detecting ... on a best-effort basis, throw a `ConcurrentModificationException`" |
| 기존 키의 값만 바꾸면 **안 터짐** | 보장 아님 (위의 결과) | `modCount` 가 구조적 수정만 세기 때문 |
| `entrySet`/`keySet`/`values` 가 뷰 | **보장** | `Map` javadoc — "collection views" · `Collection` 의 「View Collections」 |
| `Entry.setValue` 가 맵에 쓰임 | **보장** | `Map.Entry.setValue` javadoc |
| `entrySet` 의 구체 타입이 `HashMap$Node` | **보장 아님** | 내부 클래스다 |
| 지워진 `Entry` 에 `setValue` 가 성공 | **보장 아님** | javadoc 은 순회 밖의 동작을 정의하지 않는다 |
| `Map.entry(k,v)` 의 `setValue` 가 UOE | **보장** | `Map.entry` javadoc — 불변 `Entry` |
| `HashMap` 의 키 순회 순서 | **보장 아님** | `HashMap` javadoc |

**세 JDK 실측** — 프로그램 3개를 17.0.13 · 21.0.5 · 25.0.1 에서 돌려 `diff` 했다.

```text
41-a (메서드 격자 16행 + 람다 호출 9행) : 세 버전 출력이 한 글자도 같다
41-c (뷰·Entry·순회)                    : 세 버전 출력이 한 글자도 같다
41-b (재진입 CME)                        : 본문은 같고 스택트레이스 줄 번호만 다르다
   17: HashMap.computeIfAbsent(HashMap.java:1221)
   21: HashMap.computeIfAbsent(HashMap.java:1229)
   25: HashMap.computeIfAbsent(HashMap.java:1230)
```

- 줄 번호는 **매 릴리스 바뀐다.** 스택트레이스 문자열로 테스트를 쓰지 않는다.

## 언제 쓰고 언제 안 쓰나

| 하고 싶은 일 | 고를 것 |
|---|---|
| 세기·누적 | **`merge(k, 시작값, 합치는함수)`** — 한 줄 |
| 멀티맵(키 하나에 여러 값) | **`computeIfAbsent(k, x -> new ArrayList<>()).add(v)`** |
| 캐시 | `computeIfAbsent`. **`null` 을 캐시하려면 `Optional` 이나 센티널** |
| 있을 때만 갱신 | `computeIfPresent` |
| 세 상태 전부 다루기 | `compute` — 람다가 항상 불린다 |
| 읽기만 + 기본값 | **`getOrDefault`** — 단 `null` 값이 없을 때만 믿는다 |
| 키 유무 확인 | **`containsKey`** — `get(k) != null` 은 틀릴 수 있다 |
| 값 일괄 변환 | `replaceAll` |
| 조건 삭제 | `entrySet().removeIf` / `values().removeIf` / `keySet().removeIf` |
| 상수 맵 | `Map.of` / `Map.ofEntries` |
| 스트림에서 맵으로 | **여기가 아니라 [`../47-collectors-basics/`](../47-collectors-basics/)** (`toMap`) |
| 맵을 필드에 보관 | `Map.copyOf(받은것)` |
| 여러 스레드 | `ConcurrentHashMap` — `null` 이 아예 없다 |

판단 규칙 세 줄.

- **값에 `null` 을 넣지 않는다.** 그러면 이 주제의 절반이 사라진다.
- **재매핑 함수는 `null` 을 돌려주지 않는다.** 돌려주면 키가 조용히 사라진다.
- **람다 안에서 그 맵을 건드리지 않는다.** 감지는 best-effort 라 안 터질 때도 있다.

## 핵심 문장

- `Map` 의 키 상태는 **셋**이다 — 키 없음 / 값 있음 / **값이 `null`**. `get` 만으로는 첫째와 셋째를 구분할 수 없고, **`containsKey` 만이 구분한다.**
- **`putIfAbsent`·`computeIfAbsent`·`computeIfPresent`·`merge` 는 "값이 `null`" 을 "키 없음" 으로 취급한다.** 넷 다 `oldValue == null` 하나로 판정한다.
- **`getOrDefault` 는 "값이 없으면"이 아니라 "키가 없으면" 기본값을 준다** — 값이 `null` 이면 그 `null` 을 그대로 돌려준다.
- **재매핑 함수가 `null` 을 돌려주면 `compute`·`computeIfPresent`·`merge` 는 그 키를 지운다.** `computeIfAbsent` 만 안 넣고 끝낸다. 예외도 경고도 없는 무음 실패다.
- **`entrySet`·`keySet`·`values` 는 뷰다.** 거기서 지우면 맵이 바뀌고, `Entry.setValue` 는 맵에 쓴다. 그리고 `computeIfAbsent` 안에서 맵을 고치면 `ConcurrentModificationException` 이 나지만 **그것은 보장이 아니라 best-effort 다.**

## 관련 자료

- [`../39-collections-framework-map/`](../39-collections-framework-map/) — **이 주제의 선행.** 그쪽은 **`Map` 이 `Collection` 이 아니고 뷰 셋으로 이어진다**까지, 여기는 **그 뷰와 메서드로 무엇을 하나**부터
- [`../40-list-set-and-immutable-factories/`](../40-list-set-and-immutable-factories/) — `Map.of`·`Map.copyOf` 와 **뷰 대 복사본**. 그쪽이 팩토리의 정본
- [`../42-sequenced-collections/`](../42-sequenced-collections/) — `LinkedHashMap` 의 `firstEntry`·`putFirst`·`reversed`. **순서 있는 맵은 그쪽이 정본**
- [`../43-iterator-and-fail-fast/`](../43-iterator-and-fail-fast/) — **`ConcurrentModificationException` 의 정본.**\
  그쪽은 **`modCount` 가 어떻게 동작하고 언제 안 터지나**까지, 여기는 **`compute*` 가 그것을 쓴다**까지
- [`../27-equals-hashcode-contract/`](../27-equals-hashcode-contract/) — **맵의 키가 지켜야 할 계약의 정본.** 어기면 `get` 이 못 찾는다
- [`../38-optional/`](../38-optional/) — `null` 값을 못 넣는 자리에서 "없음"을 표현하는 다른 길
- [`../60-null-handling/`](../60-null-handling/) — 애초에 `null` 을 안 만드는 방어의 정본
- [`../47-collectors-basics/`](../47-collectors-basics/) — `Collectors.toMap` 이 `merge` 함수를 그대로 쓴다. **스트림에서 맵을 만드는 것은 그쪽**
- [`../48-collectors-grouping/`](../48-collectors-grouping/) — `groupingBy` 가 내부에서 `computeIfAbsent` 를 쓴다
- [`../31-functional-interfaces/`](../31-functional-interfaces/) — `Function`·`BiFunction`·`BinaryOperator` 가 이 메서드들의 파라미터
- [`../../../../../data-structure/05-hashmap/`](../../../../../data-structure/05-hashmap/) — **해시 테이블 자료구조의 정본.**\
  그쪽은 **버킷·충돌·리사이즈·트리화**까지, 여기는 **`java.util.Map` 이 그 위에 얹은 메서드 계약**부터
- [`../../../../../data-structure/29-open-addressing/`](../../../../../data-structure/29-open-addressing/) — 다른 충돌 해결 전략. **자바가 고르지 않은 쪽**
- [`../../../../../data-structure/16-red-black-tree/`](../../../../../data-structure/16-red-black-tree/) — `TreeMap` 의 내부
- [`../../../../../data-structure/10-lru-cache/`](../../../../../data-structure/10-lru-cache/) — 접근 순서 `LinkedHashMap` 이 구현하는 그 자료구조
- [`../README.md`](../README.md) — Java 문법·API 주제 목록(이 주제는 41번)
- [`../55-atomics-and-concurrent-collections/`](../55-atomics-and-concurrent-collections/)(원자 변수와 동시 컬렉션) — `ConcurrentHashMap` 의 `compute*` 는 계약이 다르다

## 용어 풀이

- **`Map`** — 키와 값을 짝지어 담는 인터페이스. `Collection` 이 아니다.
- **`Map.Entry`** — 맵의 한 칸. `getKey`·`getValue`·`setValue` 셋을 가진다.
- **`null` 값(null value)** — 키는 있는데 값이 `null` 인 상태. `HashMap`·`TreeMap` 만 허용한다.
- **재매핑 함수(remapping function)** — `compute`·`merge` 에 넘기는 "옛값으로 새 값을 만드는" 함수.
- **매핑 함수(mapping function)** — `computeIfAbsent` 에 넘기는 "키로 값을 만드는" 함수.
- **뷰(view)** — 원소를 직접 저장하지 않고 원본에 위임하는 컬렉션. `entrySet`·`keySet`·`values`.
- **`modCount`** — 컬렉션이 **구조적으로** 몇 번 바뀌었나를 세는 필드. 값만 바꾸면 안 오른다.
- **구조적 수정(structural modification)** — 크기를 바꾸는 변경. 값 교체는 해당 없음.
- **best-effort** — "되는 만큼만 해 본다". 감지되면 던지지만 감지 못 할 수도 있다는 뜻.
- **`ConcurrentModificationException`** — 순회·계산 중 대상이 구조적으로 바뀐 것을 감지했을 때의 예외.
- **negative caching** — "없다"는 사실 자체를 캐시하는 것. `computeIfAbsent` 로는 안 된다.
- **멀티맵(multimap)** — 키 하나에 값 여럿. `Map<K, List<V>>` 로 흉내 낸다.

## 더 들어가면

- **`HashMap.computeIfAbsent` 는 `null` 값 판정을 소스에서 명시적으로 한다.**

  ```java
  // JDK 21.0.5  java.base/java/util/HashMap.java  1220~1223행 — 실제 소스 그대로
              V oldValue;
              if (old != null && (oldValue = old.value) != null) {
                  afterNodeAccess(old);
                  return oldValue;
              }
  ```

  `old != null`(노드가 있다)과 `old.value != null`(값이 있다)를 **따로 본다.**\
  둘째가 거짓이면 아래로 내려가 **매핑 함수를 부른다** — 격자의 셋째 칸이 그것이다.
- **`Map.forEach` 도 `modCount` 를 대조한다.**

  ```java
  // JDK 21.0.5  java.base/java/util/HashMap.java  1425~1433행 — 실제 소스 그대로
          if (size > 0 && (tab = table) != null) {
              int mc = modCount;
              for (Node<K,V> e : tab) {
                  for (; e != null; e = e.next)
                      action.accept(e.key, e.value);
              }
              if (modCount != mc)
                  throw new ConcurrentModificationException();
          }
  ```

  ★ **`size > 0` 가 조건에 있다.** 빈 맵에서는 대조 자체를 안 한다 — 여기서도 best-effort 다.
  `forEach` 가 fail-fast 라는 것과 그 한계는 [`../43-iterator-and-fail-fast/`](../43-iterator-and-fail-fast/) 가 정본이다.
- **`merge` 로 카운팅할 때 값이 `Integer` 면 박싱이 매번 일어난다.**\
  `Integer` 캐시 범위를 넘어가면 새 객체가 생긴다 — 그 범위와 규칙은 [`../01-primitives-and-wrappers/`](../01-primitives-and-wrappers/) 가 정본이다.\
  초당 수백만 번 세는 자리라면 `LongAdder` 나 `int[]` 값을 쓰는 쪽이 낫다.
- **`Map.Entry` 에는 비교자 팩토리가 있다.**\
  `Map.Entry.comparingByKey()`·`comparingByValue()` — **Java 8** 부터.\
  정렬해서 상위 N 개를 뽑는 관용구에 쓴다([`../28-comparable-comparator/`](../28-comparable-comparator/)).
- **`putIfAbsent` 와 `computeIfAbsent` 는 "값을 미리 만드나"가 다르다.**\
  `putIfAbsent(k, new ArrayList<>())` 는 **키가 있어도 리스트를 만든다**(버리게 된다).\
  `computeIfAbsent(k, x -> new ArrayList<>())` 는 필요할 때만 만든다.

  ```text
  --- 5) 멀티맵에서 putIfAbsent 와 computeIfAbsent   (Ex.java — 41-d)
  putIfAbsent     : {p=[pear], a=[apple, apple], f=[fig], d=[date]} / 만든 리스트 5개
  computeIfAbsent : {p=[pear], a=[apple, apple], f=[fig], d=[date]} / 만든 리스트 4개
  ```

  원소 5개에 키 4개 — **버려지는 리스트가 하나** 생겼다. 이것이 멀티맵에서 후자를 쓰는 이유다.
- **`compute` 계열은 원자적이지 않다.**\
  javadoc 이 명시한다 — "The default implementation makes no guarantees about synchronization or atomicity properties of this method."\
  `HashMap` 에서 이것들은 **한 스레드 안에서만** 안전하다. 원자성이 필요하면 `ConcurrentHashMap` 이고, 그때는 계약이 다르다.
