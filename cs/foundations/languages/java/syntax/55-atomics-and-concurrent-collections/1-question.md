# java/syntax/55 — 원자 변수와 동시 컬렉션: `Atomic*`·`ConcurrentHashMap` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> **선행** — [`../33-synchronized-and-volatile/`](../33-synchronized-and-volatile/) 의 질문을 먼저 푼다. `int++` 이 왜 세 동작인지가 전제다.
> [`../41-map-api-merge-compute/`](../41-map-api-merge-compute/) 의 `merge`/`compute*` 를 알면 더 쉽다.
> ⚠️ 이 주제의 수치는 두 종류다. **정답 횟수**(10회 중 몇 회)는 **0 인가 아닌가**만,
> **ms 수치**는 **자릿수**만 맞히면 된다. 둘 다 24코어 머신의 한 측정이고 다른 머신에서 재현되지 않는다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 네 가지 카운터의 정답률 (예측)

8스레드가 각 10만 회 올린다(기대 80만). 각각 10회 반복했을 때 정답 횟수를 예측하라.

```java
(A) plain++
(B) ai.incrementAndGet()
(C) ai.set(ai.get() + 1)
(D) longAdder.increment()
```

- 넷의 정답 횟수는 각각 몇인가?
- (C)가 틀리는 이유를 한 줄로 설명하라 — `ai.get()` 도 `ai.set()` 도 원자적인데?
- 이 문항에서 끌어낼 수 있는 일반 규칙 한 문장은 무엇인가?

### 2. CAS 는 몇 번 다시 시도하나 (예측)

```java
do { cur = v.get(); } while (!v.compareAndSet(cur, cur + 1));
```

- 스레드 1개일 때 증가 1회당 재시도 횟수는?
- 스레드 16개일 때는?
- 재시도가 늘면 **결과값**이 틀리는가?
- 이 사실에서 `updateAndGet(x -> ...)` 의 람다에 대한 규칙이 무엇이 나오나?

### 3. ★ `AtomicLong` 과 `LongAdder` 는 어디서 갈리나 (예측)

스레드당 200만 회 증가, 워밍업 3 + 측정 7의 중앙값.

- 스레드 1개일 때 둘 중 어느 쪽이 빠른가?
- 스레드 24개일 때는 어느 쪽이 몇 배 빠른가(자릿수)?
- 같은 조건에서 `synchronized` 카운터는 어디쯤인가?
- 이 세 수치의 **최소~최대 폭**은 얼마나 벌어졌는가 — 그래서 수치를 어떻게 읽어야 하는가?

### 4. `LongAdder.sum()` 의 비용 (예측)

- 경합을 한 번도 안 겪은 `LongAdder` 의 `sum()` 과 `AtomicLong.get()` 중 어느 쪽이 빠른가?
- 24스레드가 두들긴 뒤의 `sum()` 은 몇 배 느려지는가?
- 왜 그런가 — `LongAdder` 가 값을 어떻게 갖고 있길래?
- 그래서 `LongAdder` 를 **쓰면 안 되는** 용도는 무엇인가?

### 5. ★ `ConcurrentHashMap` 에 카운트를 쌓는 다섯 가지 (예측)

8스레드 × 2만 회, 키 4개(기대 합 16만). 각 10회 중 정답 횟수를 예측하라.

```java
(A) Integer v = m.get(k); m.put(k, v == null ? 1 : v + 1);
(B) m.put(k, m.getOrDefault(k, 0) + 1);
(C) if (!m.containsKey(k)) m.put(k, 1); else m.put(k, m.get(k) + 1);
(D) m.merge(k, 1, Integer::sum);
(E) m.compute(k, (kk, v) -> v == null ? 1 : v + 1);
```

- 다섯의 정답 횟수는 각각 몇인가?
- 틀리는 것들의 관측 합은 기대값보다 큰가 작은가?
- `ConcurrentHashMap` 이 **보장하는 단위**를 한 문장으로 말하라.
- `ConcurrentHashMap<K, AtomicInteger>` + `computeIfAbsent` 조합은 안전한가?

### 6. `putIfAbsent` 와 `computeIfAbsent` (예측)

```java
for (int i = 0; i < 1000; i++) m1.putIfAbsent("k", makeExpensive());
for (int i = 0; i < 1000; i++) m2.computeIfAbsent("k", k -> makeExpensive());
```

- `makeExpensive()` 는 각각 몇 번 불리는가?
- 왜 그런가?
- 값이 커넥션이나 버퍼일 때 이 차이가 왜 중요한가?

### 7. `compute` 람다 안에서 같은 맵을 건드리면 (예측)

```java
(1) m.computeIfAbsent("A", k -> m.computeIfAbsent("A", k2 -> 1));
(2) m.computeIfAbsent(k0, k -> m.computeIfAbsent(k70, k2 -> 1));   // k0, k70 은 같은 버킷
(3) m.computeIfAbsent("A", k -> { m.put("B", 2); return 1; });     // 다른 버킷
(5) HashMap 에서 (1) 과 (3) 을 똑같이 하면
```

- (1)·(2)·(3) 은 각각 무엇을 던지는가, 아니면 성공하는가?
- (3)이 성공하는 것이 왜 (1)보다 위험한가?
- `HashMap` 에서는 무엇이 나오는가?
- javadoc 은 이 상황을 무엇이라 적는가?

### 8. `size()` 는 믿을 수 있나 (경계)

- 8스레드가 넣는 **도중에** `size()` 와 `mappingCount()` 를 같은 순간에 읽으면 얼마나 어긋나는가?
- 모든 스레드가 끝난 **뒤에는** 정확한가?
- `mappingCount()` 가 `size()` 와 다른 점 둘은 무엇인가?
- javadoc 이 이 메서드들의 용도를 어떻게 한정하는가?

### 9. 순회 중에 고치면 (예측)

```java
for (var e : chm.entrySet()) chm.put(newKey, 0);   // (A)
for (var e : hm.entrySet())  hm.put(100, 0);       // (B)
Iterator<Integer> it = cow.iterator(); cow.add(4); // (C)
```

- (A)와 (B)는 각각 어떻게 되는가?
- (C)에서 반복자가 보는 것은 무엇인가?
- `CopyOnWriteArrayList` 반복자의 `remove()` 는?
- "약하게 일관된 반복자"와 "스냅샷 반복자"의 차이를 한 줄로 말하라.

### 10. `CopyOnWriteArrayList` 는 언제 값을 내나 (예측)

- 원소 5만 개를 하나씩 `add` 하면 `ArrayList` 대비 몇 배 느린가(자릿수)?
- 왜 그런가?
- 단일 스레드로 1만 개를 1000번 순회할 때 셋(`ArrayList`/`synchronizedList`/`CopyOnWriteArrayList`)의 차이는 컸는가?
- 그 결과로 "읽기가 빠르다"를 주장할 수 있는가 — 왜 없는가?

### 11. 8스레드가 동시에 `add` 하면 (예측)

각 1만 건씩 8스레드(기대 8만), 10회 반복.

- `ArrayList` / `synchronizedList` / `CopyOnWriteArrayList` 의 크기 정답 횟수는?
- `ArrayList` 에서 **예외가 난 실행**은 10회 중 몇 회인가?
- 그 숫자가 왜 무서운가?

### 12. "각각 원자적"과 "함께 원자적" (예측)

```java
// 쓰는 쪽: x.incrementAndGet(); y.incrementAndGet();
// 읽는 쪽: if (x.get() != y.get()) 불일치++;
```

- 50만 회 관찰 중 불일치는 몇 번 보이는가(자릿수)?
- 이것을 0으로 만들려면 무엇으로 바꾸는가?
- 그 방법으로 바꾸면 관측된 불일치는 몇 번인가?

### 13. `null` 은 왜 금지인가 (왜)

- `chm.put(null, "v")` 와 `chm.put("k", null)` 은 각각 어떻게 되는가?
- `HashMap` 은 어떤가?
- 이 금지가 **불편**이 아니라 **설계**인 이유를 `get(k) == null` 의 의미로 설명하라.
- `merge` 의 remapping 함수가 `null` 을 반환하면 무슨 일이 나나?

### 14. 이 코드를 어떻게 고칠 것인가 (연결)

각각 무엇으로 바꿀지 한 줄로 답하라.

```text
(A) Integer c = counts.get(userId); counts.put(userId, c == null ? 1 : c + 1);
(B) private final AtomicLong requestCount = new AtomicLong();   // 초당 수만 요청, 값은 1분에 한 번 조회
(C) private final AtomicLong stockQuantity = new AtomicLong();  // 요청마다 읽어서 분기
(D) cache.computeIfAbsent(k, key -> { log.info("생성"); return load(key); });
(E) if (list.size() > 100) trim();                              // list 는 ConcurrentHashMap.keySet()
(F) private final List<Listener> listeners = new CopyOnWriteArrayList<>();  // 초당 1000건 add
(G) synchronized (chm) { if (!chm.containsKey(k)) chm.put(k, v); }
```

### 15. 경합이 있으면 `CopyOnWriteArrayList` 가 이기나 (예측)

원소 5,000개를 각 스레드가 200번 순회한다. 스레드 1·8·24 에서 셋을 비교하라.

```text
(A) synchronizedList 를 그냥 for-each
(B) synchronizedList 를 synchronized (list) { ... } 로 감싸 순회
(C) CopyOnWriteArrayList 를 그냥 for-each
```

- 스레드 1개에서 셋의 차이는 큰가?
- 스레드 24개에서 (B)와 (C)의 배수는 얼마인가(자릿수)?
- (A)가 (B)보다 빠른데 왜 그것을 장점이라 할 수 없는가 — javadoc 은 무엇을 요구하는가?
- `CopyOnWriteArrayList` 가 값을 내는 조건 **둘**을 말하라.

### 16. `Collections.synchronizedMap` 을 써도 되나 (예측)

8스레드가 각 20만 회 `merge`(키 1000개), 그리고 같은 실험을 읽기 99% 로 바꿨다.

- 쓰기 위주에서 `ConcurrentHashMap` 은 `synchronizedMap` 의 몇 배인가(자릿수)?
- 읽기 위주에서는 몇 배인가 — 차이가 더 커지는가 작아지는가? 왜?
- `Collections.synchronizedMap(new HashMap<>())` 과 직접 `synchronized` 로 감싸는 것은 성능이 다른가?
- 셋 중 **결과값이 틀리는 것**이 있는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
