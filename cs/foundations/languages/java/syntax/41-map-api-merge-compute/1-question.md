# java/syntax/41 — `Map` API: `merge`/`compute*`/`getOrDefault`/`putIfAbsent` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> **선행** — [`../39-collections-framework-map/`](../39-collections-framework-map/) 의 질문을 먼저 푼다.
> 해시 테이블의 **내부**(버킷·충돌·리사이즈)는 여기서 묻지 않는다 — [`../../../../../data-structure/05-hashmap/`](../../../../../data-structure/05-hashmap/) 의 질문이다.
> `Collectors.toMap` 은 [`../47-collectors-basics/`](../47-collectors-basics/) 의 질문이다.

## 예시 데이터

여러 문항이 **키 하나짜리 맵의 세 상태**를 쓴다.

```java
Map<String,Integer> absent    = new LinkedHashMap<>();                 // {}
Map<String,Integer> present   = new LinkedHashMap<>(); present.put("k", 1);    // {k=1}
Map<String,Integer> nullValue = new LinkedHashMap<>(); nullValue.put("k", null); // {k=null}
```

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 세 상태에서 읽기 세 가지 (예측)

```java
m.get("k")
m.getOrDefault("k", 9)
m.containsKey("k")
```

- 세 메서드 × 세 상태 = 아홉 칸의 결과는 각각 무엇인가?
- **`getOrDefault` 가 기본값을 안 주는 칸**은 어디이며 왜인가?
- 셋 중 세 상태를 전부 구분할 수 있는 것은 무엇인가?
- `getOrDefault` 의 기본 구현(`@implSpec`)을 코드로 쓰면 무엇인가?
- `m.getOrDefault("k", 0)` 의 결과를 `int` 에 담으면 어느 칸에서 무엇이 터지는가?

### 2. 넣기 다섯 가지 (예측)

```java
m.put("k", 5)
m.putIfAbsent("k", 5)
m.computeIfAbsent("k", x -> 5)
m.computeIfPresent("k", (x, v) -> 5)
m.compute("k", (x, v) -> 5)
m.merge("k", 5, (o, n) -> o + n)
```

- 여섯 메서드 × 세 상태 = 열여덟 칸에서 **호출 뒤 맵**은 각각 무엇인가?
- `{k=null}` 칸을 `{}` 칸처럼 다루는 메서드는 몇 개이며 무엇인가?
- 그렇게 되는 이유를 `merge` 의 기본 구현 **한 줄**로 말하면?
- `merge("k", null, f)` 는 세 상태에서 각각 무엇을 하는가?

### 3. 람다는 언제 불리나 (예측)

```java
m.computeIfAbsent("k", x -> { 호출을 기록; return 5; });
m.merge("k", 5, (o, n) -> { 호출을 기록; return o + n; });
m.compute("k", (x, v) -> { 호출을 기록; return 5; });
```

- 세 메서드 × 세 상태 중 **람다가 불리는 칸**은 어디인가?
- `computeIfAbsent` 와 `merge` 의 호출 패턴은 어떤 관계인가?
- `compute` 의 람다에 넘어오는 옛값은 `{}` 와 `{k=null}` 에서 각각 무엇인가 — 구분이 되는가?
- 람다 안에 DB 조회가 있다면 셋 중 무엇을 고르는가?

### 4. ★ 람다가 `null` 을 돌려주면 (예측)

```java
m.compute("k", (x, v) -> null)
m.computeIfPresent("k", (x, v) -> null)
m.merge("k", 5, (o, n) -> null)
m.computeIfAbsent("k", x -> null)

// 그리고 이것 — 항등 함수처럼 보인다
nullValue.compute("k", (x, v) -> v)
```

- 앞 넷은 각각 맵에 무엇을 남기는가?
- 넷 중 **하나만** 다르게 동작한다 — 무엇이고 어떻게 다른가?
- 마지막 줄은 `{k=null}` 에 걸면 무엇이 되는가?
- 왜 그렇게 되는가 — 어느 메서드의 계약 때문인가?
- 이것이 왜 위험한 실패 모드인가?

### 5. 캐시에 `null` 을 넣으려 하면 (경계)

```java
cache.computeIfAbsent(key, k -> loadFromDb(k));   // loadFromDb 가 null 을 돌려준다
```

- 맵에는 무엇이 저장되는가?
- 반환값은 무엇인가?
- 다음 호출에서 `loadFromDb` 는 다시 불리는가?
- 예외나 경고가 나는가?
- "없다는 사실"을 캐시하려면 어떻게 하는가?

### 6. ★ 람다 안에서 같은 맵을 고치면 (예측)

```java
Map<String,Integer> m = new HashMap<>();
m.put("seed", 0);
m.computeIfAbsent("k", x -> { m.put("other", 1); return 5; });      // (A)
m.computeIfAbsent("a", x -> m.computeIfAbsent("b", y -> 2) + 1);     // (B)
m.computeIfAbsent("a", x -> m.computeIfAbsent("a", y -> 2) + 1);     // (C)

Map<String,Integer> big = new HashMap<>(64);
for (int i = 0; i < 4; i++) big.put("p" + i, i);
big.computeIfAbsent("k", x -> { big.put("p0", 99); return 5; });     // (D)
```

- (A)~(D)는 각각 무엇이 되는가?
- (D)가 나머지와 다른 이유는 무엇인가?
- 이 감지를 하는 JDK 소스는 **세 줄**이다 — 무엇인가?
- 이 동작은 **보장인가**? javadoc 의 어느 낱말이 근거인가?
- `TreeMap`·`LinkedHashMap`·`merge`·`compute` 에서도 같은가?

### 7. 뷰 셋을 고치면 (예측)

```java
Map<String,Integer> m = new LinkedHashMap<>(); // {a=1, b=2, c=3}
Set<String> keys = m.keySet();
Collection<Integer> vals = m.values();

m.put("d", 4);          // (A) keys 와 vals 는?
keys.remove("a");       // (B) m 은?
vals.remove(2);         // (C) m 은?
keys.add("z");          // (D) ?
```

- (A)~(D)는 각각 어떻게 되는가?
- (D)만 막혀 있는 이유는 무엇인가?
- 순회하며 모든 값에 10을 곱하는 두 가지 방법은 무엇인가?
- 뷰를 메서드 밖으로 넘길 때 무엇을 조심하는가?

### 8. `Entry` 를 들고 나가면 (예측)

```java
Map<String,Integer> m = new HashMap<>(); m.put("a", 1);
Map.Entry<String,Integer> held = m.entrySet().iterator().next();
m.put("a", 7);          // (A) held 는?
m.remove("a");          // (B) held 는? held.setValue(9) 는?

Map.Entry<String,Integer> free = Map.entry("a", 1);
free.setValue(2);       // (C) ?
```

- (A)~(C)는 각각 무엇이 되는가?
- `held` 의 **구체 타입**은 무엇인가?
- (B)에서 `setValue` 가 성공하는 것이 왜 위험한가?
- `Entry` 를 안전하게 보관하려면 어떻게 하는가?

### 9. 순회 중 삭제 (예측)

```java
for (String k : m.keySet()) if (k.equals("k1")) m.remove(k);   // (A)
m.keySet().removeIf(k -> k.equals("k1"));                       // (B)
for (var it = m.entrySet().iterator(); it.hasNext(); )
    if (it.next().getValue() == 1) it.remove();                 // (C)
```

- 셋은 각각 어떻게 되는가?
- (A)가 터지고 (B)·(C)가 안 터지는 이유는 무엇인가?
- 값 기준으로 지우려면 어느 뷰를 쓰는가?

### 10. 카운팅을 한 줄로 (연결)

```java
// 옛 관용구
Integer old = counts.get(w);
counts.put(w, old == null ? 1 : old + 1);
```

- `getOrDefault` 로 쓰면 어떻게 되는가, 조회는 몇 번인가?
- `merge` 로 쓰면 어떻게 되는가, 조회는 몇 번인가?
- 멀티맵(`Map<K, List<V>>`)은 어느 메서드로 만드는가?
- 거기서 `putIfAbsent` 를 쓰면 무엇이 낭비되는가?

### 11. 무엇이 보장인가 (경계)

- `merge` 가 `null` 값에서 람다를 안 부른다는 것은?
- `compute` 가 `null` 결과에 키를 지운다는 것은?
- 람다 안에서 맵을 고치면 CME 가 난다는 것은?
- `entrySet` 의 원소가 `HashMap$Node` 라는 것은?
- 근거가 되는 javadoc 표현을 각각 한 조각씩 대면?

### 12. 이 주제의 경계 (연결)

- 「해시 충돌이 나면 버킷이 어떻게 되나」는 어느 문서인가?
- 「`Collectors.toMap` 이 중복 키에 던지는 예외」는 어디인가?
- 「`LinkedHashMap.firstEntry`·`putFirst`」는 어디인가?
- 「`modCount` 가 무엇이고 fail-fast 가 왜 best-effort 인가」는 어디인가?
- 「키가 `equals` 계약을 어기면」은 어디인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
