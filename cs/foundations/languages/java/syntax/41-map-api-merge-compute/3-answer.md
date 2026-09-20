# java/syntax/41 — `Map` API: `merge`/`compute*`/`getOrDefault`/`putIfAbsent` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·에러는 **Temurin JDK 에서 실제로 돌려 얻은 것**이다.\
> javadoc·소스 인용은 JDK 21.0.5 의 `lib/src.zip` 을 풀어 읽은 원문이다.\
> 프로그램 4개를 17.0.13 · 21.0.5 · 25.0.1 셋 다에서 돌렸다 — **본문 출력은 같고 스택트레이스만 달랐다**(11번).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 세 상태에서 읽기 세 가지

**출력** (`Ex.java` — 41-a, 17·21·25 동일)

```text
메서드 (반환값 / 호출 뒤 맵)                    {}  (키 없음)                {k=1} (값 있음)              {k=null} (값이 null)        
get("k")                              null / {}                 1 / {k=1}                 null / {k=null}           
getOrDefault("k", 9)                  9 / {}                    1 / {k=1}                 null / {k=null}           
containsKey("k")                      false / {}                true / {k=1}              true / {k=null}           
```

**아홉 칸**

| | `{}` | `{k=1}` | `{k=null}` |
|---|---|---|---|
| `get("k")` | `null` | `1` | `null` |
| `getOrDefault("k", 9)` | **`9`** | `1` | **`null`** |
| `containsKey("k")` | `false` | `true` | **`true`** |

**기본값을 안 주는 칸**

- **`{k=null}` 칸**이다. `getOrDefault` 는 **"값이 없으면"이 아니라 "키가 없으면"** 기본값을 준다.

**세 상태를 전부 구분할 수 있는 것**

- **`containsKey` 하나뿐**이다. 나머지 둘은 `{}` 와 `{k=null}` 에서 같은 `null` 을 준다.
- javadoc 이 `get` 쪽에서 미리 경고한다.

> If this map permits null values, then a return value of `null` does not *necessarily* indicate that the map contains no mapping for the key; it's also possible that the map explicitly maps the key to `null`. The `containsKey` operation may be used to distinguish these two cases.

**`getOrDefault` 의 기본 구현**

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

**`int` 에 담으면**

**출력** (`Ex.java` — 41-d, 17·21·25 동일)

```text
--- 1) getOrDefault 의 결과를 int 에 담으면
{}       -> int n = m.getOrDefault("k", 0) : 0
{k=null} -> int n = m.getOrDefault("k", 0) : NullPointerException: Cannot invoke "java.lang.Integer.intValue()" because the return value of "java.util.Map.getOrDefault(Object, Object)" is null
```

- **`{k=null}` 칸에서 언박싱 NPE** 다.
- ★ 메시지가 `getOrDefault` 를 지목해 준다 — helpful NullPointerException(JDK 14+) 덕이다.

### 2. 넣기 다섯 가지

**출력** (`Ex.java` — 41-a, 17·21·25 동일)

```text
put("k", 5)                           null / {k=5}              1 / {k=5}                 null / {k=5}              
putIfAbsent("k", 5)                   null / {k=5}              1 / {k=1}                 null / {k=5}              
computeIfAbsent("k", x -> 5)          5 / {k=5}                 1 / {k=1}                 5 / {k=5}                 
computeIfPresent("k",(x,v)->5)        null / {}                 5 / {k=5}                 null / {k=null}           
compute("k", (x,v) -> 5)              5 / {k=5}                 5 / {k=5}                 5 / {k=5}                 
merge("k", 5, (o,n) -> o+n)           5 / {k=5}                 6 / {k=6}                 5 / {k=5}                 
merge("k", null, (o,n) -> o+n)        NullPointerException / {} NullPointerException / {k=1}NullPointerException / {k=null}
```

**호출 뒤 맵 — 열여덟 칸**

| | `{}` | `{k=1}` | `{k=null}` |
|---|---|---|---|
| `put(k,5)` | `{k=5}` | `{k=5}` | `{k=5}` |
| `putIfAbsent(k,5)` | `{k=5}` | `{k=1}` | **`{k=5}`** |
| `computeIfAbsent(k, x->5)` | `{k=5}` | `{k=1}` | **`{k=5}`** |
| `computeIfPresent(k,(x,v)->5)` | `{}` | `{k=5}` | **`{k=null}`** |
| `compute(k,(x,v)->5)` | `{k=5}` | `{k=5}` | `{k=5}` |
| `merge(k,5,합)` | `{k=5}` | `{k=6}` | **`{k=5}`** |

**`{k=null}` 을 `{}` 처럼 다루는 메서드 — 넷**

```text
   putIfAbsent       {k=null} -> {k=5}     "없으니 넣자"
   computeIfAbsent   {k=null} -> {k=5}     "없으니 만들자"
   computeIfPresent  {k=null} -> {k=null}  "없으니 아무것도 안 한다"
   merge             {k=null} -> {k=5}     "없으니 합치지 말고 그냥 넣자"
```

**`merge` 의 기본 구현 한 줄**

```java
V newValue = (oldValue == null) ? value : remappingFunction.apply(oldValue, value);
```

- **`oldValue == null` 하나**가 "키 없음"과 "값이 `null`" 을 묶는다. 나머지 셋도 같은 판정이다.

**`merge("k", null, f)`**

- **세 상태 모두 `NullPointerException`** 이다. 맵은 그대로 남는다.
- `merge` 의 첫 두 줄이 `Objects.requireNonNull(remappingFunction)` 과 `Objects.requireNonNull(value)` 다.
- javadoc 도 `@throws NullPointerException if ... the value or remappingFunction is null` 로 적는다.

### 3. 람다는 언제 불리나

**출력** (`Ex.java` — 41-a, 17·21·25 동일)

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

**불리는 칸**

```text
                      {}        {k=1}      {k=null}
  computeIfAbsent     부른다     안 부른다    부른다
  merge               안 부른다   부른다      안 부른다
  compute             부른다     부른다      부른다
```

**`computeIfAbsent` 와 `merge` 의 관계**

- **정확히 반대다.** 한쪽이 부르는 칸에서 다른 쪽은 안 부른다.
- 같은 `oldValue == null` 판정을 **반대 방향으로** 쓰기 때문이다.

**`compute` 의 옛값**

- `{}` 에서도 `{k=null}` 에서도 **`old=null`** 이다.
- 즉 **람다 안에서는 두 상태를 구분할 수 없다.** `compute` 는 부르기는 하지만 정보를 주지는 않는다.

**람다에 DB 조회가 있으면**

- **`computeIfAbsent`** 다. 값이 있으면 아예 안 부른다.
- 단 **DB 가 `null` 을 주면 저장이 안 된다**(5번). 그것까지 고려해야 한다.

### 4. ★ 람다가 `null` 을 돌려주면

**출력** (`Ex.java` — 41-a · 41-d, 17·21·25 동일)

```text
computeIfAbsent -> null               null / {}                 1 / {k=1}                 null / {k=null}
compute -> null                       null / {}                 null / {}                 null / {}
merge("k",5,(o,n) -> null)            5 / {k=5}                 null / {}                 5 / {k=5}
compute("k", (x,v) -> v)              null / {}                 1 / {k=1}                 null / {}
```

```text
--- 3) computeIfPresent 가 null 을 돌려주면          (Ex.java — 41-d)
{k=1}    computeIfPresent -> null : null / {}
{k=null} computeIfPresent -> null : null / {k=null}
```

**넷이 맵에 남기는 것**

| 메서드 | `null` 결과일 때 |
|---|---|
| `compute` | **키를 지운다** |
| `computeIfPresent` | **키를 지운다**(값이 있었을 때) |
| `merge` | **키를 지운다**(합치는 함수가 불렸을 때) |
| `computeIfAbsent` | **아무것도 안 한다** — 넣지도 지우지도 않는다 |

**하나만 다른 것**

- **`computeIfAbsent`** 다. "없으니 만들어 넣겠다"였는데 만들 값이 `null` 이면 **그냥 포기한다.**
- 나머지 셋은 "이 키의 새 값은 `null` 이다" 를 **"이 키를 지운다"** 로 해석한다.

**`nullValue.compute("k", (x, v) -> v)`**

- **`{}`** 가 된다. **항등 함수를 걸었는데 데이터가 사라진다.**

**어느 계약 때문인가**

```java
// JDK 21.0.5  java.base/java/util/Map.java  merge 의 @implSpec — 실제 소스 그대로
     * V oldValue = map.get(key);
     * V newValue = (oldValue == null) ? value :
     *              remappingFunction.apply(oldValue, value);
     * if (newValue == null)
     *     map.remove(key);
     * else
     *     map.put(key, newValue);
```

- `if (newValue == null) map.remove(key);` — **`compute`·`computeIfPresent` 도 같은 모양**이다.

**왜 위험한가**

```text
   예외가 나는 실패                        이 실패

   스택트레이스가 남는다                    아무 흔적이 없다
   어느 줄인지 안다                        맵의 크기만 하나 줄어 있다
        |                                        |
   고칠 수 있다                            며칠 뒤 "데이터가 없어졌다" 로 발견된다
```

- **무음 실패**다. 재매핑 함수는 **항상 `null` 이 아닌 값을 돌려준다**를 규칙으로 삼는다.
- 버려야 하면 `remove` 를 명시적으로 부른다. 그래야 의도가 코드에 남는다.

### 5. 캐시에 `null` 을 넣으려 하면

**출력** (`Ex.java` — 41-d, 17·21·25 동일)

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

- **맵에는 아무것도 저장되지 않는다** — 세 번 불러도 `{}` 다.
- **반환값은 `null`** 이다.
- **`loadFromDb` 가 매번 다시 불린다** — 누적 호출이 1, 2, 3 으로 는다.
- **예외도 경고도 없다.** 캐시가 전혀 안 먹는데 아무도 모른다.

**"없다는 사실"을 캐시하려면**

```java
// 1) Optional 을 값으로 — 위 출력에서 람다가 한 번만 불렸다
Map<K, Optional<V>> cache = new HashMap<>();
cache.computeIfAbsent(k, key -> Optional.ofNullable(load(key)));

// 2) 센티널 객체
private static final V NONE = new V();
cache.computeIfAbsent(k, key -> { V v = load(key); return v == null ? NONE : v; });

// 3) containsKey 로 분기 — 조회가 두 번이다
if (!cache.containsKey(k)) cache.put(k, load(k));
```

- `Optional` 을 **필드·맵의 값**으로 쓰는 것은 보통 안티패턴이지만([`../38-optional/`](../38-optional/)),
  **negative caching 은 그 예외로 쓸 만한 자리**다 — "없음"을 값으로 표현해야 하기 때문이다.

### 6. ★ 람다 안에서 같은 맵을 고치면

**출력** (`Ex.java` — 41-b, JDK 21.0.5)

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

**(A)~(D)**

- **(A)** 새 키 `other` 를 넣는다 → **`ConcurrentModificationException`**.
- **(B)** 다른 키로 재귀 → **`ConcurrentModificationException`**.
- **(C)** 같은 키로 재귀 → **`ConcurrentModificationException`**.
- **(D)** 이미 있는 키 `p0` 의 값만 바꾼다 → **예외 없음.** 맵은 `{p0=99, p1=1, p2=2, p3=3, k=5}`.

**(D)가 다른 이유**

```text
   modCount 는 "구조적 수정" 만 센다

   big.put("새키", v)    -> 크기가 는다 -> modCount++ -> 감지된다
   big.put("p0", 99)     -> 크기 그대로 -> modCount 그대로 -> 감지 못 한다
                                                |
                                     람다가 맵을 고쳤는데도 통과한다
```

**감지하는 소스 — 세 줄**

```java
// JDK 21.0.5  java.base/java/util/HashMap.java  1226~1228행 — 실제 소스 그대로
        int mc = modCount;
        V v = mappingFunction.apply(key);
        if (mc != modCount) { throw new ConcurrentModificationException(); }
```

**보장인가 — 근거 낱말**

> The default implementation makes no guarantees about detecting if the mapping function modifies this map during computation and, if appropriate, reporting an error. Non-concurrent implementations should override this method and, **on a best-effort basis**, throw a `ConcurrentModificationException` if it is detected that the mapping function modifies this map during computation.

- 근거 낱말은 **`on a best-effort basis`** 다. "detected" 되면 던진다는 것이지 **항상 감지한다는 약속이 아니다.**
- (D)가 그 한계의 실물이다.
- javadoc 은 그 앞에 규칙도 적어 둔다 — **"The mapping function should not modify this map during computation."**

**다른 구현·다른 메서드**

- `TreeMap`·`LinkedHashMap` 도 던진다((4)·(5)).
- `merge`·`compute` 도 던진다((7)·(8)).
- `ConcurrentHashMap` 은 다르다 — javadoc 이 "on a best-effort basis, throw an **`IllegalStateException`**" 라고 갈라 적는다([**55번 주제**](../55-atomics-and-concurrent-collections/)).

### 7. 뷰 셋을 고치면

**출력** (`Ex.java` — 41-c, 17·21·25 동일)

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

**(A)~(D)**

- **(A)** `keys` 가 `[a, b, c, d]`, `vals` 가 `[1, 2, 3, 4]` 로 **따라 바뀐다.**
- **(B)** 맵이 `{b=2, c=3, d=4}` — **키를 지우면 항목이 통째로 사라진다.**
- **(C)** 맵이 `{c=3, d=4}` — **값으로도 지울 수 있다.**
- **(D)** **`UnsupportedOperationException`**.

**(D)만 막힌 이유**

- **키만 받아서는 값을 무엇으로 할지 정할 수 없다.** 지우는 것은 정의되지만 넣는 것은 정의되지 않는다.
- `values().add(v)` 도 같은 이유로 막힌다.

**모든 값에 10을 곱하는 두 가지**

```java
// 1) Entry.setValue — 순회하며 고치는 유일하게 안전한 길
for (Map.Entry<String,Integer> e : m.entrySet()) e.setValue(e.getValue() * 10);

// 2) replaceAll (8+) — 한 줄
m.replaceAll((k, v) -> v * 10);
```

**뷰를 밖으로 넘길 때**

- 받는 쪽이 **원본을 고칠 수 있다.** `keySet().remove(k)` 한 줄로 맵이 바뀐다.
- 방어: `Set.copyOf(m.keySet())` 로 끊는다([`../40-list-set-and-immutable-factories/`](../40-list-set-and-immutable-factories/)).

### 8. `Entry` 를 들고 나가면

**출력** (`Ex.java` — 41-c, 17·21·25 동일)

```text
--- 4) 순회가 끝난 Entry 를 들고 있으면
보관한 Entry      : a=1  (java.util.HashMap$Node)
맵을 고친 뒤 held : a=7
키를 지운 뒤 held : a=7 / setValue : OK / 그 뒤 held : a=9 / 맵 : {}
--- 5) Map.entry 로 만든 것은 뷰가 아니다
Map.entry("a",1)  : a=1  (java.util.KeyValueHolder)
setValue          : java.lang.UnsupportedOperationException: not supported
```

**(A)~(C)**

- **(A)** `m.put("a", 7)` 뒤 `held` 는 **`a=7`** — 맵과 이어져 있다.
- **(B)** `m.remove("a")` 뒤에도 `held` 는 **`a=7`** 이고, `setValue(9)` 가 **성공한다**(`a=9`). 맵은 `{}` 다.
- **(C)** `Map.entry("a",1).setValue(2)` → **`UnsupportedOperationException: not supported`**.

**`held` 의 구체 타입**

- **`java.util.HashMap$Node`** — 맵의 내부 노드 그 자체다. 복사본이 아니다.

**(B)가 위험한 이유**

```text
   held.setValue(9) 가 성공한다
        |
   예외가 없으니 "고쳐졌다" 고 읽는다
        |
   그런데 맵에는 그 키가 없다 -> 아무 데도 반영되지 않았다
        |
   "분명히 값을 바꿨는데 왜 안 바뀌어 있지" 가 된다
```

- `Map.Entry.setValue` javadoc 이 이 상황을 그대로 적어 놓았다.

> Replaces the value corresponding to this entry with the specified value (optional operation). (Writes through to the map.) **The behavior of this call is undefined if the mapping has already been removed from the map** (by the iterator's `remove` operation).

> `@throws IllegalStateException` implementations may, but are not required to, throw this exception if the entry has been removed from the backing map.

- **"던져도 되고 안 던져도 된다"** 까지 적혀 있다. 실측에서는 안 던졌다.

**안전하게 보관하려면**

```java
Map.Entry<String,Integer> copy = Map.entry(e.getKey(), e.getValue());   // 9+
```

- 또는 키와 값을 **따로** 꺼내 둔다.

### 9. 순회 중 삭제

**출력** (`Ex.java` — 41-c, 17·21·25 동일)

```text
--- 7) 순회 중 맵을 고치면
k1 제거 : java.util.ConcurrentModificationException
removeIf : 예외 없음 {k0=0, k2=2, k3=3, k4=4}
Iterator.remove : 예외 없음 {k0=0, k2=2, k3=3, k4=4}
```

- **(A)** `ConcurrentModificationException`.
- **(B)** 통과. 결과 `{k0=0, k2=2, k3=3, k4=4}`.
- **(C)** 통과. 결과 같다.

**(A)만 터지는 이유**

```text
  (A) 맵을 직접 고친다                   (B)·(C) 뷰/이터레이터로 고친다

  m.remove(k)                            it.remove() / removeIf
  -> modCount 가 오른다                  -> modCount 를 올리면서
  -> 순회 중인 이터레이터는 모른다           expectedModCount 도 같이 갱신한다
  -> 다음 next() 에서 대조 실패            -> 대조가 통과한다
```

- 자세한 것과 **안 터지는 경우**는 [`../43-iterator-and-fail-fast/`](../43-iterator-and-fail-fast/) 가 정본이다.

**값 기준으로 지우려면**

- `m.values().removeIf(v -> ...)` 또는 `m.entrySet().removeIf(e -> ...)`.
- `entrySet` 쪽이 키와 값을 다 볼 수 있어서 더 넓다.

### 10. 카운팅을 한 줄로

**출력** (`Ex.java` — 41-d, 17·21·25 동일)

```text
--- 4) 카운팅 세 관용구
get+put       : {pear=1, apple=2, fig=1, date=1}
getOrDefault  : {pear=1, apple=2, fig=1, date=1}
merge         : {pear=1, apple=2, fig=1, date=1}
```

| 관용구 | 코드 | 조회 횟수 |
|---|---|---|
| `get` + `put` | `Integer old = m.get(w); m.put(w, old == null ? 1 : old + 1);` | **2번** |
| `getOrDefault` | `m.put(w, m.getOrDefault(w, 0) + 1);` | **2번** |
| **`merge`** | `m.merge(w, 1, Integer::sum);` | **1번** |

- 결과는 셋 다 같다. **`merge` 만 한 줄이고 한 번 조회다.**

**멀티맵**

```java
idx.computeIfAbsent(key, k -> new ArrayList<>()).add(value);
```

**`putIfAbsent` 를 쓰면 낭비되는 것**

**출력** (`Ex.java` — 41-d, 17·21·25 동일)

```text
--- 5) 멀티맵에서 putIfAbsent 와 computeIfAbsent
putIfAbsent     : {p=[pear], a=[apple, apple], f=[fig], d=[date]} / 만든 리스트 5개
computeIfAbsent : {p=[pear], a=[apple, apple], f=[fig], d=[date]} / 만든 리스트 4개
```

- 원소 5개에 키 4개 — **`putIfAbsent` 는 리스트를 5개 만들고 1개를 버린다.**
- `putIfAbsent(k, new ArrayList<>())` 는 인자를 **미리 평가**하므로 키가 있어도 객체가 생긴다.
- `computeIfAbsent` 는 람다라 **필요할 때만** 평가된다. 이것이 후자를 쓰는 이유다.

### 11. 무엇이 보장인가

| 관측 | 보장? | javadoc 조각 |
|---|---|---|
| `merge` 가 `null` 값에서 람다를 안 부름 | **보장** | `@implSpec` — `V newValue = (oldValue == null) ? value : remappingFunction.apply(oldValue, value);` |
| `compute` 가 `null` 결과에 키를 지움 | **보장** | `@implSpec` — `if (newValue == null) map.remove(key);` |
| 람다 안에서 맵을 고치면 CME | **아니다** | `makes no guarantees about detecting` · **`on a best-effort basis`** |
| `entrySet` 의 원소가 `HashMap$Node` | **아니다** | 문서화되지 않은 내부 클래스 |

- `@implSpec` 에 적힌 기본 구현은 **계약의 일부**다. 그래서 첫 둘은 보장이다.
- 셋째는 같은 문단이 스스로 "보장하지 않는다"고 적는다 — **문서가 직접 부정한 것**이다.

### 12. 이 주제의 경계

| 질문 | 정본 |
|---|---|
| 해시 충돌이 나면 버킷이 어떻게 되나 | [`../../../../../data-structure/05-hashmap/`](../../../../../data-structure/05-hashmap/) |
| `Collectors.toMap` 이 중복 키에 던지는 예외 | [`../47-collectors-basics/`](../47-collectors-basics/) |
| `LinkedHashMap.firstEntry`·`putFirst` | [`../42-sequenced-collections/`](../42-sequenced-collections/) |
| `modCount` 와 fail-fast 가 best-effort 인 이유 | [`../43-iterator-and-fail-fast/`](../43-iterator-and-fail-fast/) |
| 키가 `equals` 계약을 어기면 | [`../27-equals-hashcode-contract/`](../27-equals-hashcode-contract/) |

- 한 줄로 갈라 보면 이렇다.\
  **해시가 어떻게 동작하나 = `data-structure/`, `Map` 메서드의 계약 = 여기,
  순회의 계약 = 43번, 스트림에서 맵 만들기 = 47번.**

---

## 실행 검증

| 프로그램 | 무엇을 확인했나 | 돌린 JDK |
|---|---|---|
| `Ex.java` (41-a) | 16개 메서드 × 3상태 격자(반환값 + 호출 뒤 맵), 람다 호출 여부 9칸, `merge(k,null,f)` 의 NPE | 17 · 21 · 25 (**출력 동일**) |
| `Ex.java` (41-b) | `computeIfAbsent`·`merge`·`compute` 안에서 맵을 고쳤을 때의 CME, 재귀 두 형태, `TreeMap`/`LinkedHashMap`, **기존 키만 갱신하면 안 터지는 것**, 안전한 색인 만들기 | 17 · 21 · 25 (**본문 동일 · 스택트레이스 줄 번호만 다름**) |
| `Ex.java` (41-c) | `keySet`/`values`/`entrySet` 의 뷰 성질, `setValue`·`replaceAll`, 지워진 `Entry` 의 `setValue`, `Map.entry` 의 불변성, 불변 맵 뷰, 순회 중 삭제 3형태 | 17 · 21 · 25 (**출력 동일**) |
| `Ex.java` (41-d) | `getOrDefault` 결과의 언박싱 NPE, negative caching 3회 반복, `computeIfPresent -> null`, 카운팅 3관용구, 멀티맵의 버려지는 리스트, 정렬한 `Entry` 리스트의 `setValue` | 17 · 21 · 25 (**출력 동일**) |
| `src.zip` 열람 | `Map` 의 `get`·`getOrDefault`·`computeIfAbsent`·`merge` javadoc 과 `@implSpec`, `HashMap.computeIfAbsent`·`forEach` 구현, `Map.Entry.comparingByKey` 의 `@since 1.8` | 21 |

**javac 12회 · java 12회.**

**버전별로 갈린 것**

```text
41-a · 41-c · 41-d : 세 버전 출력이 한 글자도 같다

41-b               : 스택트레이스 줄 번호만 갈린다
  17: HashMap.computeIfAbsent(HashMap.java:1221)
  21: HashMap.computeIfAbsent(HashMap.java:1229)
  25: HashMap.computeIfAbsent(HashMap.java:1230)
  -> 본문(어느 경우에 터지고 어느 경우에 안 터지나)은 세 버전이 같다
```

- **17·21·25 에서 (D)가 세 번 다 안 터졌다.** 그래도 그것은 "안 터진다"는 보장이 아니다 —
  javadoc 이 best-effort 라고 적었으므로 **터져도 맞고 안 터져도 맞다.**
  기댈 수 없는 쪽이라는 것이 결론이다.

**구현 의존 항목** (버전이 오르면 다시 돌려야 하는 것)

- 스택트레이스 줄 번호 — 세 버전이 전부 달랐다.
- 구체 타입 `LinkedHashMap$LinkedKeySet`·`LinkedHashMap$LinkedValues`·`HashMap$Node`·`KeyValueHolder`.
- **기존 키만 갱신했을 때 CME 가 안 나는 것** — best-effort 라 언제든 바뀔 수 있다.
- 예외 **메시지 문구** — `not supported` · `remove` · helpful NullPointerException 의 문장.
- `HashMap` 의 키 순회 순서 — 이 문서는 `LinkedHashMap` 을 써서 순서를 고정했다.
- **Java 8 은 안 돌려 봄** — 이 머신에 8이 없다. `Map.of`·`Map.entry`(9+)는 애초에 8에 없다.
