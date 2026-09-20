# java/syntax/55 — 원자 변수와 동시 컬렉션: `Atomic*`·`ConcurrentHashMap` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·에러·수치는 **Temurin JDK 21.0.5 에서 실제로 돌려 얻은 것**이다.\
> ⚠️ **측정 조건 — 수치가 두 종류다.**\
> ① **정확성**(정답 횟수) — 스레드를 직접 띄워 **각 10회 반복**, 「정답 횟수 / 10」과 「관측 합의 최소~최대」.\
> ② **성능**(ms) — **JMH 가 아니다.** 워밍업 3회 + **측정 7회의 중앙값**(리스트 실험만 워밍업 2 + 3회의 중앙값).\
> 머신 **24코어**(Linux x86-64). 흔들림 폭이 커서(`AtomicLong` 8스레드 377~997 ms) **자릿수만** 읽는다.\
> javadoc 인용은 `lib/src.zip` 의 `java.base/java/util/concurrent/*.java` 원문이다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 네 가지 카운터의 정답률

**출력** (`Ex.java` — 55-a, 8스레드 × 10만 회, 각 10회 반복, JDK 21.0.5)

```text
--- 8스레드 x 100000회 증가 (기대 800000) / 각 10회 반복
  int++                    정답  3/10회  관측 119673 ~ 800000
  AtomicInteger.incrementAndGet  정답 10/10회
  ai.set(ai.get() + 1)     정답  0/10회  관측 236912 ~ 351488   <- 원자 연산 둘을 이어 붙이면 원자가 아니다
  LongAdder.increment      정답 10/10회
```

**왜 그런가**

| | 정답 횟수 | 왜 |
|---|---|---|
| (A) `plain++` | **3/10** | 읽고-고치고-쓰기 세 단계. **그런데 3회는 맞았다** |
| (B) `incrementAndGet` | **10/10** | CAS 루프가 한 덩어리로 처리한다 |
| (C) `ai.set(ai.get() + 1)` | **0/10** | 원자 연산 둘 **사이**가 비어 있다 |
| (D) `LongAdder.increment` | **10/10** | 칸마다 CAS 로 더하고 `sum()` 에서 합친다 |

- **(C)가 틀리는 이유** — `ai.get()` 도 `ai.set()` 도 각각은 원자적이다.\
  그러나 **둘 사이에 다른 스레드가 통째로 끼어든다.** 둘이 같은 값을 읽고 같은 값을 쓴다.
- **일반 규칙 한 문장** — ★ **원자 연산을 이어 붙이면 원자가 아니다.**\
  이 규칙이 5번(맵의 `get`+`put`)과 12번(두 변수)에서 그대로 반복된다.
- (A) 가 **3회나 맞은 것**도 기억할 것 — 「안 터졌다」는 안전의 증거가 아니다\
  ([`../33-synchronized-and-volatile/`](../33-synchronized-and-volatile/) 가 그 정본이다).

```text
ai.incrementAndGet()                       ai.set(ai.get() + 1)

  do {                                       v = ai.get()      (원자적)
    cur = 읽는다                                  ... 남이 끼어든다 ...
    성공 = CAS(cur, cur+1)                   ai.set(v + 1)     (원자적)
  } while (!성공)                                  |
        |                                          v
        v                                    10회 전부 틀림
  10회 전부 정답
```

### 2. CAS 는 몇 번 다시 시도하나

**출력** (`Ex.java` — 55-a, 스레드당 5만 회, JDK 21.0.5)

```text
--- CAS 는 몇 번 다시 시도하나 (직접 루프를 돌려 센다)
  스레드  1 : 최종값 50000(기대 50000)  재시도 0회  증가 1회당 0.00회
  스레드  2 : 최종값 100000(기대 100000)  재시도 46,862회  증가 1회당 0.47회
  스레드  4 : 최종값 200000(기대 200000)  재시도 99,592회  증가 1회당 0.50회
  스레드  8 : 최종값 400000(기대 400000)  재시도 159,880회  증가 1회당 0.40회
  스레드 16 : 최종값 800000(기대 800000)  재시도 1,418,995회  증가 1회당 1.77회
```

**왜 그런가**

- **스레드 1개: 0회.** 경합이 없으면 CAS 는 항상 첫 시도에 성공한다.
- **스레드 16개: 증가 1회당 1.77회.** 같은 일을 2.77배 한 셈이다.
- **결과값은 모든 경우에 정답**이다. 재시도는 **정확성이 아니라 비용**의 문제다.
- 그래서 나오는 규칙 — ★ **`updateAndGet`·`accumulateAndGet`·`compute`·`merge` 의 람다는 여러 번 불린다.**\
  **부수효과를 넣으면 그만큼 더 실행된다.** javadoc 도 이렇게 적는다.

  > The function should be side-effect-free, since it may be re-applied when attempted updates fail
  > due to contention among threads.

- 실제로 세어 봤다.

```text
--- 3. 람다가 여러 번 불릴 수 있다 (updateAndGet 은 CAS 루프다)
  스레드 1 : 최종값 100,000  람다 호출 100,000회 (증가 1회당 1.00회)
  스레드 8 : 최종값 800,000  람다 호출 1,977,224회 (증가 1회당 2.47회)
```

- 8스레드에서 **2.47회**다. 람다 안에 로그를 넣었다면 로그가 2.47배 찍힌다.

### 3. ★ `AtomicLong` 과 `LongAdder` 는 어디서 갈리나

**출력** (`Ex.java` — 55-b, 스레드당 200만 회, 워밍업 3 + 측정 7의 중앙값, JMH 아님, 24코어)

```text
--- 스레드당 2,000,000회 증가 / 워밍업 3회 + 측정 7회의 중앙값 (JMH 아님)
  AtomicLong     스레드  1 : 중앙값    12 ms  (최소 11, 최대 13)
  LongAdder      스레드  1 : 중앙값    19 ms  (최소 17, 최대 21)
  synchronized   스레드  1 : 중앙값    43 ms  (최소 40, 최대 45)

  AtomicLong     스레드  2 : 중앙값   172 ms  (최소 140, 최대 195)
  LongAdder      스레드  2 : 중앙값    26 ms  (최소 24, 최대 27)
  synchronized   스레드  2 : 중앙값   135 ms  (최소 115, 최대 162)

  AtomicLong     스레드  8 : 중앙값   828 ms  (최소 377, 최대 997)
  LongAdder      스레드  8 : 중앙값    27 ms  (최소 25, 최대 32)
  synchronized   스레드  8 : 중앙값  4684 ms  (최소 3278, 최대 4876)

  AtomicLong     스레드 24 : 중앙값  2758 ms  (최소 1320, 최대 2944)
  LongAdder      스레드 24 : 중앙값    50 ms  (최소 42, 최대 53)
  synchronized   스레드 24 : 중앙값 14548 ms  (최소 10581, 최대 16033)
```

**왜 그런가**

- **스레드 1개면 `AtomicLong` 이 빠르다**(12 대 19 ms). `LongAdder` 의 칸 관리 비용이 손해다.
- **스레드 24개면 `LongAdder` 가 55배 빠르다**(2,758 대 50 ms).\
  갈리는 지점은 이미 **스레드 2개**다(172 대 26 ms).
- **`synchronized` 는 24스레드에서 14,548 ms** — `LongAdder` 의 **291배**다.\
  단일 스레드에서도 가장 느렸다(43 ms).
- **흔들림 폭** — `AtomicLong` 8스레드가 **377~997 ms** 로 2.6배 벌어졌다.\
  ★ 그래서 이 표는 **"어느 쪽이 이기나"와 "자릿수"**만 읽는다. **"55배"를 외우지 마라.**
- javadoc 이 방향만 보장한다 — "Under low update contention, the two classes have similar characteristics.\
  But under high contention, expected throughput of this class is significantly higher, at the expense of higher space consumption."

```text
스레드 1 (경합 없음)                        스레드 24 (경합 셈)

  AtomicLong      12 ms  <- 이긴다          AtomicLong    2,758 ms
  LongAdder       19 ms                     LongAdder        50 ms  <- 이긴다
  synchronized    43 ms                     synchronized 14,548 ms
```

### 4. `LongAdder.sum()` 의 비용

**출력** (`Ex.java` — 55-f, 1000만 회 읽기, 워밍업 3회 뒤 1회, JDK 21.0.5)

```text
--- 1. 경합을 겪은 LongAdder 의 sum() 비용
  (24스레드가 두들긴 뒤 sum = 48000000)
  AtomicLong.get()            : 3 ms
  LongAdder.sum() 경합 없던 것 : 3 ms
  LongAdder.sum() 경합 겪은 것 : 169 ms   <- 칸이 늘어난 만큼 읽기가 비싸진다
```

**왜 그런가**

- **경합을 안 겪은 `LongAdder.sum()` 은 `AtomicLong.get()` 과 같다**(둘 다 3 ms).\
  칸이 안 늘어나 base 하나만 읽으면 되기 때문이다.
- **경합을 겪은 뒤에는 56배 느리다**(169 ms). **칸을 전부 더해야** 한다.
- javadoc 의 설명대로 `LongAdder` 는 "one or more variables that together maintain an initially zero long sum" 이다.\
  경합이 세면 변수 집합이 **동적으로 늘어난다.**
- **쓰면 안 되는 용도** — **매번 읽어서 분기하는 값.**\
  재고 수량·잔여 한도·세마포어 카운트 같은 것. 그때는 `AtomicLong` 이다.\
  `LongAdder` 가 맞는 것은 **쓰기가 압도적이고 읽기는 가끔인 통계·지표**다.

### 5. ★ `ConcurrentHashMap` 에 카운트를 쌓는 다섯 가지

**출력** (`Ex.java` — 55-c, 8스레드 × 2만 회, 키 4개, 각 10회 반복, JDK 21.0.5)

```text
--- ConcurrentHashMap 에 카운팅 (8스레드 x 20,000, 키 4개, 기대 합 160,000) / 각 10회
  get 한 뒤 put                            정답  0/10회  관측 합 104,465 ~ 124,739
  getOrDefault 한 뒤 put                   정답  0/10회  관측 합 98,971 ~ 137,903
  containsKey 로 보고 put                   정답  0/10회  관측 합 91,411 ~ 110,270
  merge                                  정답 10/10회  관측 합 160,000 ~ 160,000
  compute                                정답 10/10회  관측 합 160,000 ~ 160,000

--- AtomicInteger 를 값으로 두면
  computeIfAbsent + AtomicInteger        정답 10/10회
```

**왜 그런가**

- **(A)·(B)·(C) 는 0/10회**, **(D)·(E) 는 10/10회**다.
- **틀린 것들의 합은 항상 기대값보다 작다**(16만 → 9~12만).\
  남의 결과를 덮어쓰기 때문에 **잃기만 한다.**
- ★ **`ConcurrentHashMap` 이 보장하는 단위는 "메서드 호출 하나"다.**\
  맵은 안전한데 **내가 그 위에 얹은 조합**이 안전하지 않다.
- javadoc 이 `merge`·`compute` 에 대해 "The entire method invocation is performed atomically" 라고 적는다.
- **`ConcurrentHashMap<K, AtomicInteger>` + `computeIfAbsent` 도 10/10회 안전**하다.\
  맵 연산은 값 객체를 만들 때 한 번이고, 증가는 `AtomicInteger` 가 원자적으로 한다.\
  `LongAdder` 를 값으로 두는 조합은 **javadoc 자신이 예로 든다**\
  (`freqs.computeIfAbsent(key, k -> new LongAdder()).increment();`).

```text
get + put (0/10회)                         merge (10/10회)

  A: get("k") -> 5                          A: merge("k", 1, sum)
  B: get("k") -> 5                            |-- 버킷을 잡는다
  A: put("k", 6)                              |-- 읽고 더하고 쓴다
  B: put("k", 6)  <- A 의 결과가 사라졌다        |-- 버킷을 놓는다
       |                                    B: 그 다음에 들어온다
       v                                          |
  16만이 10만으로 줄었다                             v
                                            16만 그대로
```

### 6. `putIfAbsent` 와 `computeIfAbsent`

**출력** (`Ex.java` — 55-c, 각 1000회, JDK 21.0.5)

```text
--- putIfAbsent 는 객체를 미리 만든다, computeIfAbsent 는 필요할 때만 만든다
  putIfAbsent    : 값 객체를 1000번 만들었다
  computeIfAbsent: 값 객체를 1번 만들었다
```

**왜 그런가**

- **`putIfAbsent(k, makeExpensive())` 는 1000번 만든다.**\
  자바는 **인자를 먼저 평가**한다. 넣을지 말지는 그 다음 문제다.
- **`computeIfAbsent(k, k -> makeExpensive())` 는 1번 만든다.**\
  람다는 **키가 없을 때만** 불린다. javadoc 의 표현대로 "invoked exactly once per invocation of this method if the key is absent, else not at all".
- **값이 커넥션·버퍼·스레드풀 같은 비싼 객체**면 999개를 만들어 바로 버리는 셈이다.\
  게다가 그 객체가 **자원을 잡는 것**이면 누수가 된다.

### 7. `compute` 람다 안에서 같은 맵을 건드리면

**출력** (`Ex.java` — 55-d, JDK 21.0.5)

```text
--- compute 계열의 함수 안에서 같은 맵을 건드리면
  (1) 같은 키를 다시 computeIfAbsent
      java.lang.IllegalStateException: Recursive update
  (2) 같은 버킷에 떨어지는 다른 키를 computeIfAbsent
      같은 버킷 키 : [k0, k70, k81]  (hash&15 = 5)
      java.lang.IllegalStateException: Recursive update
  (3) 다른 버킷의 키를 put
      결과 {A=1, B=2}   <- 터지지 않았다. 그래서 더 위험하다
  (4) merge 안에서 같은 키를 merge
      결과 {A=6}
  (5) HashMap 에서 같은 일을 하면
      java.util.ConcurrentModificationException
      다른 키 put : java.util.ConcurrentModificationException
```

**왜 그런가**

- **(1)·(2) 는 `IllegalStateException: Recursive update`** 다. 같은 버킷을 다시 잡으려다 걸린다.
- **(3) 은 조용히 성공한다** — `{A=1, B=2}`.
- ★ **(3)이 더 위험한 이유** — **터지는지가 키의 해시에 좌우된다.**\
  개발·테스트의 키로는 안 걸리다가, 운영의 어떤 키 조합에서 터진다.\
  그리고 예외가 안 났다고 안전한 것도 아니다 — **javadoc 이 금지한 동작**이다.
- **(4) merge 중첩은 예외 없이 `{A=6}`** 이 나왔다. 기대한 값이 아닌데 **아무 신호가 없다.**\
  (이 문서는 그 값이 6 이 된 내부 경로를 **추적하지 않았다.** 관측만 적는다.)
- **`HashMap` 은 어느 경우든 `ConcurrentModificationException`** 이다.\
  `modCount` 하나로 맵 전체를 보기 때문이다. **진단 면에서는 오히려 낫다.**
- javadoc 원문:\
  `computeIfAbsent` — "The mapping function must not modify this map during computation."\
  `merge` — "the computation should be short and simple, and must not attempt to update any other mappings of this Map."

### 8. `size()` 는 믿을 수 있나

**출력** (`Ex.java` — 55-e, 8스레드가 각 5만 건, 10회 반복, JDK 21.0.5)

```text
--- 1. 넣는 도중에 size() 를 읽으면 (8스레드가 각 5만 건, 10회 반복)
  모두 끝난 뒤 size() 가 틀린 실행 : 0/10
  넣는 도중 size() 와 mappingCount() 가 어긋난 최대 폭 : 3783
  (javadoc: "the results of aggregate status methods including size, isEmpty, and containsValue are typically useful only when a map is not undergoing concurrent updates")
```

**왜 그런가**

- **갱신 도중에는 같은 순간에 읽은 두 값이 최대 3,783 어긋났다.**
- **모든 스레드가 끝난 뒤에는 10/10회 정확**했다. "항상 틀린다"가 아니다.\
  ★ 그래도 **보장이 아니다** — javadoc 은 정지 상태의 정확성을 약속하지 않는다.
- **`mappingCount()` 가 `size()` 와 다른 점 둘**\
  ① 반환 타입이 **`long`** 이다 — `size()` 는 `int` 라 20억을 넘는 맵을 표현하지 못한다.\
  ② javadoc 이 **"The value returned is an estimate; the actual count may differ if there are concurrent insertions or removals"** 라고 **명시**한다.\
  `@since 1.8` 이다.
- javadoc 이 용도를 한정한다 — 결과가 "adequate for monitoring or estimation purposes, **but not for program control**".

### 9. 순회 중에 고치면

**출력** (`Ex.java` — 55-e, JDK 21.0.5)

```text
--- 2. 순회 중에 고치면
  ConcurrentHashMap : 예외 없음, 본 원소 16개 (최종 크기 21)
  HashMap           : java.util.ConcurrentModificationException
--- 3. 순회 중 넣은 것이 보이나 (100회 반복)
  순회 시작 뒤 넣은 키가 보인 횟수 : 100/100  (약하게 일관된 반복자 — 보일 수도 안 보일 수도 있다)
--- 4. CopyOnWriteArrayList 의 반복자는 스냅샷이다
  반복자를 만든 뒤 add(4) → 반복자가 본 것 [1, 2, 3], 실제 리스트 [1, 2, 3, 4]
  반복자 remove() : java.lang.UnsupportedOperationException
```

**왜 그런가**

- **(A) `ConcurrentHashMap` 은 예외 없이 끝난다.** 16개를 봤고 최종 크기는 21이었다.
- **(B) `HashMap` 은 `ConcurrentModificationException`** 이다.
- **(C) `CopyOnWriteArrayList` 반복자는 `[1, 2, 3]` 만 본다.** 나중에 넣은 `4` 는 안 보인다.\
  javadoc: "The iterator will not reflect additions, removals, or changes to the list since the iterator was created."
- **반복자의 `remove()` 는 `UnsupportedOperationException`** 이다. 복사본을 고쳐 봐야 소용없으니까.
- **차이 한 줄**\
  **약하게 일관됨** = 순회 중 변경이 **보일 수도 안 보일 수도** 있다(예외는 없다).\
  **스냅샷** = 순회 중 변경이 **절대 안 보인다**(예외도 없다).
- 이 실험에서 순회 중 넣은 키가 **100/100회 보였다.** ★ **그래도 보장이 아니다** —\
  javadoc 은 반복자가 "at or since the creation of the iterator" 시점의 상태를 반영한다고만 적는다.

### 10. `CopyOnWriteArrayList` 는 언제 값을 내나

**출력** (`Ex.java` — 55-e, 워밍업 2회 + 3회의 중앙값, JMH 아님, JDK 21.0.5)

```text
--- 5. 쓰기 비용 (원소 N개를 하나씩 add, 3회 중앙값)
  N= 1,000  ArrayList(비동기)   0.1 ms   synchronizedList   0.1 ms   CopyOnWriteArrayList     0.4 ms
  N=10,000  ArrayList(비동기)   0.7 ms   synchronizedList   0.8 ms   CopyOnWriteArrayList    88.0 ms
  N=50,000  ArrayList(비동기)   0.9 ms   synchronizedList   2.1 ms   CopyOnWriteArrayList   584.5 ms
--- 6. 읽기 비용 (원소 1만 개를 1000번 순회, 3회 중앙값)
  ArrayList  14.4 ms   synchronizedList   9.5 ms   CopyOnWriteArrayList  19.7 ms
```

**왜 그런가**

- **5만 건 하나씩 `add` 에 584.5 ms — `ArrayList` 의 약 650배**다.
- 이유는 javadoc 그대로다 — 모든 변경 연산이 "implemented by making a fresh copy of the underlying array".\
  n 번째 `add` 가 n 개를 복사하므로 **총 복사량이 O(n²)** 이다.\
  1,000 → 10,000 → 50,000 에서 0.4 → 88 → 584 ms 로 뛴 것이 그 모양이다.
- **단일 스레드 순회에서는 셋의 차이가 거의 없다**(14.4 / 9.5 / 19.7 ms).\
  오히려 `synchronizedList` 가 가장 빨랐다.
- ★ **그래서 이 수치로 "읽기가 빠르다"를 주장할 수 없다.**\
  `CopyOnWriteArrayList` 의 읽기 이득은 **여러 스레드가 동시에 읽을 때** 나온다 — 조건을 바꿔 다시 쟀다(15번).

### 11. 8스레드가 동시에 `add` 하면

**출력** (`Ex.java` — 55-e, 각 1만 건 × 8스레드, 10회 반복, JDK 21.0.5)

```text
--- 7. 8스레드가 동시에 add 하면 (각 1만 건, 10회)
  ArrayList             크기 정답  0/10회  관측 2,405 ~ 47,033  예외 난 실행 1회
  synchronizedList      크기 정답 10/10회  관측 80,000 ~ 80,000  예외 난 실행 0회
  CopyOnWriteArrayList  크기 정답 10/10회  관측 80,000 ~ 80,000  예외 난 실행 0회
```

**왜 그런가**

- **`ArrayList` 0/10회**, 나머지 둘은 **10/10회**다.
- **`ArrayList` 에서 예외가 난 실행은 10회 중 1회**뿐이다.
- ★ **그 숫자가 무서운 이유** — **10회 중 9회는 예외 없이 끝났다.**\
  8만 건을 넣었는데 2,405건만 남은 실행에서도 **아무도 안 죽었다.**\
  로그에도, 에러율에도, 알람에도 안 나타난다. **조용히 데이터가 사라진다.**
- 병렬 스트림에서의 같은 실패(원소 유실·`null` 구멍·`ArrayIndexOutOfBoundsException`)는\
  [`../49-parallel-streams/`](../49-parallel-streams/) 가 이미 실측했다. **여기서 다시 재지 않는다.**

### 12. "각각 원자적"과 "함께 원자적"

**출력** (`Ex.java` — 55-f, 50만 회 관찰, JDK 21.0.5)

```text
--- 4. 두 변수를 함께 바꿔야 하면 CAS 로는 안 된다
  x 와 y 를 각각 원자적으로 올리는 동안 x != y 로 보인 횟수 : 68182 / 500,000회 관찰
  → "각각 원자적"은 "둘이 함께 원자적"이 아니다. 그때는 락이나 불변 객체 + AtomicReference 다
--- 5. AtomicReference 로 두 값을 한 번에
  a != b 로 보인 횟수 : 0 / 500,000회 관찰   (최종 Pair[a=500000, b=500000])
```

**왜 그런가**

- **50만 회 중 68,182회** 불일치가 보였다 — 약 **7분의 1**이다. 자릿수로는 **수만 회**.
- **불변 객체 하나를 `AtomicReference` 에 넣으면 0회**다.

```java
record Pair(int a, int b) { }
AtomicReference<Pair> ref = new AtomicReference<>(new Pair(0, 0));
ref.updateAndGet(p -> new Pair(p.a() + 1, p.b() + 1));   // 두 값이 한 번에 바뀐다
```

- 읽는 쪽은 **참조 하나를 읽으므로** 반쯤 바뀐 상태를 볼 수 없다.
- 대가는 — **갱신마다 객체를 새로 만든다**(그리고 2번의 재시도만큼 더 만든다).\
  필드가 셋 이상이거나 갱신이 잦으면 **락이 낫다**([`../33-synchronized-and-volatile/`](../33-synchronized-and-volatile/)).

### 13. `null` 은 왜 금지인가

**출력** (`Ex.java` — 55-c, JDK 21.0.5)

```text
--- null 키·null 값
  put(null, "v") : java.lang.NullPointerException
  put("k", null) : java.lang.NullPointerException
  HashMap 은 둘 다 된다 : {null=null}
  그래서 CHM 은 get()==null 이 "없다"를 확정한다 (HashMap 은 못 한다)
  merge 의 remapping 이 null 을 반환하면 :
    키가 지워진다 → {}
```

**왜 그런가**

- **둘 다 `NullPointerException`** 이다. `HashMap` 은 `{null=null}` 로 둘 다 받는다.
- **설계인 이유** — `ConcurrentHashMap` 에서 **`get(k) == null` 은 "그 키가 없다"를 확정**한다.\
  `HashMap` 에서는 "없다"와 "값이 `null` 이다"가 구분이 안 돼 `containsKey` 를 또 불러야 한다.\
  그런데 **동시 환경에서는 `containsKey` 와 `get` 사이가 또 비어 있다**(1번·5번의 규칙).\
  즉 **`null` 을 금지해야만 한 번의 호출로 판정이 끝난다.**
- **`merge` 의 remapping 이 `null` 을 반환하면 그 키가 지워진다.**\
  실측에서 `{a=1}` 에 `merge("a", 1, (x, y) -> null)` 을 했더니 **`{}`** 가 됐다.\
  "0이 되면 지운다" 같은 코드를 이 규칙으로 한 줄에 쓴다.

### 14. 이 코드를 어떻게 고칠 것인가

**(A) `Integer c = counts.get(userId); counts.put(userId, c == null ? 1 : c + 1);`**

- **`counts.merge(userId, 1, Integer::sum)`** 로 바꾼다.
- 근거: 5번 — `get`+`put` 은 **0/10회 정답**, 16만이 10만으로 줄었다.

**(B) `AtomicLong requestCount` — 초당 수만 요청, 1분에 한 번 조회**

- **`LongAdder`** 로 바꾼다.
- 근거: 3번 — 24스레드에서 `LongAdder` 가 55배 빠르다. 읽기가 드무니 `sum()` 비용은 문제가 안 된다.

**(C) `AtomicLong stockQuantity` — 요청마다 읽어서 분기**

- **그대로 둔다.** `LongAdder` 로 바꾸면 안 된다.
- 근거: 4번 — 경합을 겪은 `sum()` 이 **56배** 비싸다. 읽기가 잦으면 `AtomicLong` 이 맞다.

**(D) `cache.computeIfAbsent(k, key -> { log.info("생성"); return load(key); });`**

- **람다에서 로그를 뺀다**(또는 `computeIfAbsent` 반환 뒤에 찍는다).
- 근거: 2번 — CAS 루프의 람다는 8스레드에서 **2.47회** 불렸다.\
  게다가 `compute` 계열의 람다는 **버킷을 잡은 채** 돈다 — javadoc 이 "short and simple" 을 요구한다.

**(E) `if (list.size() > 100) trim();` — `list` 가 `ConcurrentHashMap.keySet()`**

- **크기로 분기하지 않는다.** 필요하면 별도의 `LongAdder` 로 세거나, 정지 상태에서만 읽는다.
- 근거: 8번 — 갱신 중 `size()` 가 **최대 3,783** 어긋났다. javadoc 이 "not for program control" 이라고 적는다.

**(F) `CopyOnWriteArrayList listeners` — 초당 1000건 `add`**

- **`ConcurrentLinkedQueue` 나 `ConcurrentHashMap.newKeySet()`** 으로 바꾼다.
- 근거: 10번 — `add` 가 O(n) 이라 5만 건에 584 ms 였다. `CopyOnWriteArrayList` 는 **거의 안 바뀌는 목록**용이다.

**(G) `synchronized (chm) { if (!chm.containsKey(k)) chm.put(k, v); }`**

- **`chm.putIfAbsent(k, v)`** 로 바꾼다.
- 근거: 다른 스레드가 **락 없이** `chm.put` 을 부르면 이 `synchronized` 는 아무것도 막지 못한다.\
  동시 컬렉션에 외부 락을 거는 순간 **원자 연산을 안 쓰고 있다**는 신호다.

### 15. 경합이 있으면 `CopyOnWriteArrayList` 가 이기나

**출력** (`Ex.java` — 55-h, 원소 5,000개 × 200회 순회, 워밍업 2 + 측정 5의 중앙값, JMH 아님, JDK 21.0.5)

```text
--- 여러 스레드가 동시에 순회 (원소 5,000개 x 200회) / 워밍업 2 + 측정 5의 중앙값
    (A) synchronizedList 를 그냥 for-each      <- javadoc 이 금지하는 형태(락 없이 순회)
    (B) synchronizedList 를 synchronized 로 감싸 순회  <- javadoc 이 요구하는 형태
    (C) CopyOnWriteArrayList 를 그냥 for-each   <- 락이 필요 없다
  스레드  1 : (A)     3 ms   (B)      2 ms   (C)     3 ms
  스레드  8 : (A)     4 ms   (B)     12 ms   (C)     4 ms
  스레드 24 : (A)     6 ms   (B)     44 ms   (C)    10 ms
```

**왜 그런가**

- **스레드 1개에서는 셋이 구별되지 않는다**(3 / 2 / 3 ms). 10번이 차이를 못 낸 이유가 이것이다.
- **24스레드에서 (B) 44 ms 대 (C) 10 ms — 4.4배**다.\
  (B) 는 순회하는 내내 락을 쥐므로 **읽기끼리도 줄선다.**
- **(A) 는 빠르지만 규칙 위반**이다. `Collections.synchronizedList` 의 javadoc 원문:

  > It is imperative that the user manually synchronize on the returned
  > list when traversing it via `Iterator`, `Spliterator` or `Stream`

  ★ (A) 가 빠른 것은 **안전을 안 지켰기 때문**이지 장점이 아니다.
- ★ **`CopyOnWriteArrayList` 의 조건은 둘이 함께 성립할 때다** —\
  **① 쓰기가 드물다**(10번: 쓰기 650배 손해) **② 여러 스레드가 동시에 순회한다**(여기: 읽기 4.4배 이득).\
  한 스레드만 읽는다면 **불변 리스트**(`List.copyOf`)가 낫다.

### 16. `Collections.synchronizedMap` 을 써도 되나

**출력** (`Ex.java` — 55-g, 8스레드, 워밍업 2 + 측정 5의 중앙값, JMH 아님, JDK 21.0.5)

```text
--- 2. 맵 구현 셋의 처리 시간 (8스레드가 각 20만 회 merge, 키 1000개)
     워밍업 2 + 측정 5회의 중앙값 (JMH 아님)
  ConcurrentHashMap          중앙값    40 ms  (최소 36, 최대 51)
  synchronizedMap(HashMap)   중앙값   216 ms  (최소 192, 최대 265)
  HashMap + synchronized     중앙값   258 ms  (최소 241, 최대 296)
--- 3. 같은 실험을 '읽기 위주'로 바꾸면 (8스레드, 읽기 99% / 쓰기 1%)
  ConcurrentHashMap          중앙값     3 ms  (최소 2, 최대 10)
  synchronizedMap(HashMap)   중앙값   184 ms  (최소 139, 최대 285)
```

**왜 그런가**

- **쓰기 위주 5.4배**(40 대 216 ms), **읽기 위주 61배**(3 대 184 ms).
- ★ **읽기에서 차이가 더 크다.** `synchronizedMap` 은 **읽기에도 맵 전체 락**을 잡는다.\
  `ConcurrentHashMap` 의 읽기는 락을 안 잡는다.
- `Collections.synchronizedMap(new HashMap<>())` 과 **직접 `synchronized` 로 감싸는 것**은 거의 같다(216 대 258 ms).
- **세 경우 모두 최종 합은 정확했다**(프로그램이 `AssertionError` 로 검증한다).\
  **성능 차이지 정확성 차이가 아니다.**
- **결론** — 새로 쓸 이유가 없다. 레거시에서 만나면 바꾼다.\
  단 **`null` 키·값을 쓰고 있었다면 그것부터 걷어내야 한다**(13번).

---

## 실행 검증

| 프로그램 | 무엇을 확인했나 | 반복 | 돌린 JDK |
|---|---|---|---|
| `Ex.java` (55-a) | 카운터 4종의 정답률, CAS 재시도 횟수(스레드 1·2·4·8·16) | 정확성 각 10회 / 재시도 1회 | **17 · 21 · 25** (정답/오답 패턴 동일, 수치는 전부 다름) |
| `Ex.java` (55-b) | `AtomicLong`·`LongAdder`·`synchronized` 의 처리 시간(스레드 1·2·8·24) | **워밍업 3 + 측정 7의 중앙값** | 21 |
| `Ex.java` (55-c) | 맵 카운팅 5종의 정답률, `AtomicInteger` 값 조합, `putIfAbsent` 대 `computeIfAbsent`, `null` 금지, `merge` 의 `null` 반환 | 정확성 각 10회 | **17 · 21 · 25** (0/10 과 10/10 이 세 버전 모두 같음) |
| `Ex.java` (55-d) | `Recursive update` 4경로 + `HashMap` 대조, 같은 버킷 키 탐색 | 1회 | **17 · 21 · 25** (**출력이 한 글자도 다르지 않았다**) |
| `Ex.java` (55-e) | `size()` 대 `mappingCount()` 어긋남, 순회 중 수정, 스냅샷 반복자, 리스트 3종의 쓰기·읽기 비용, 8스레드 `add` | 크기 10회 / 반복자 100회 / 시간 3회의 중앙값 | 21 |
| `Ex.java` (55-f) | 경합 겪은 `sum()` 비용, CAS 연산 5종, `updateAndGet` 람다 호출 수, 두 변수 불일치, `AtomicReference` 해법 | 관찰 50만 회 | 21 |
| `Ex.java` (55-g) | 맵 구현 3종의 쓰기 위주·읽기 위주 처리 시간 | 워밍업 2 + 측정 5의 중앙값 | 21 |
| `Ex.java` (55-h) | 동시 순회 3형태(락 없음 / 락 걸고 / COW)의 처리 시간(스레드 1·8·24) | 워밍업 2 + 측정 5의 중앙값 | 21 |
| `src.zip` 열람 | `AtomicInteger`·`AtomicLong`·`AtomicReference`·`ConcurrentHashMap`·`CopyOnWriteArrayList` 의 `@since 1.5`, `LongAdder`·`mappingCount` 의 `@since 1.8`, `Map` 디폴트 메서드의 `@since 1.8`, `computeIfAbsent`/`merge`/`size`/`updateAndGet` javadoc 원문 | — | 21 |

**측정 방법의 한계 (반드시 같이 읽을 것)**

- **JMH 가 아니다.** 워밍업이 3회(리스트는 2회)뿐이고 DCE·JIT 편향을 완전히 막지 못한다.
- **머신 의존**이다 — 24코어. 코어가 적으면 `LongAdder` 의 이득 배수가 줄어든다.
- **흔들림이 크다** — `AtomicLong` 8스레드가 **377~997 ms**(2.6배). **자릿수만** 읽는다.
- **정확성 수치와 성능 수치를 섞어 읽지 마라.** 앞의 것은 10회 반복의 정답 횟수, 뒤의 것은 7회의 중앙값이다.
- **측정하지 않은 것** — ① ABA 문제의 재현, ② `ConcurrentHashMap` 의 병렬 대량 연산(`forEach`·`reduce`),\
  ③ 동시 큐(`ConcurrentLinkedQueue`·`LinkedBlockingQueue`).

**구현 의존 항목** (버전이 오르면 다시 돌려야 하는 것)

- CAS 재시도 횟수와 `updateAndGet` 람다 호출 횟수 — **머신·부하 의존.**
- `LongAdder` 대 `AtomicLong` 의 배수 — javadoc 은 **방향만** 보장한다.
- `IllegalStateException("Recursive update")` 의 문구 — **구현 세부.**
- **다른 버킷이면 안 터지는 것** — 키의 해시와 테이블 크기에 좌우된다.
- `size()` 가 정지 상태에서 정확한 것 — **보장 아님.**
- 순회 중 넣은 키가 100/100회 보인 것 — **보장 아님.**
- **CAS 재시도 횟수가 버전마다 크게 달랐다** — 16스레드 기준 17 에서 **4.30회**, 21 에서 **1.77회**, 25 에서 **1.31회**.\
  같은 프로그램·같은 머신이다. **이 수치를 절대 외우지 마라.**
- 일반 `int++` 의 정답 횟수도 갈렸다 — 17 **7/10**, 21 **3/10**, 25 **8/10**.\
  ★ **25 에서 가장 "안전해 보였다."** 「안 터졌다」가 안전의 증거가 아닌 이유다.
- **55-b(성능)·55-e·55-f 는 21 에서만 돌렸다** — 시간이 오래 걸리는 측정이라 교차 실행을 안 했다.
- `@since` 는 세 버전 `src.zip` 중 21 의 것을 읽었다.
