# java/syntax/55 — 원자 변수와 동시 컬렉션: `Atomic*`·`ConcurrentHashMap` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **선행** — [`../33-synchronized-and-volatile/`](../33-synchronized-and-volatile/) (락의 문법과 `volatile` 의 경계 — **이 주제는 그 다음 칸이다**) · [`../41-map-api-merge-compute/`](../41-map-api-merge-compute/) (`Map` API 의 `merge`/`compute*`/`getOrDefault`).
> **기준 소스** — [`java.util.concurrent.atomic` 패키지 javadoc (Java SE 21)](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/concurrent/atomic/package-summary.html) · [`ConcurrentHashMap`](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/concurrent/ConcurrentHashMap.html) · [`LongAdder`](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/concurrent/atomic/LongAdder.html) · [`CopyOnWriteArrayList`](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/concurrent/CopyOnWriteArrayList.html) · 이 머신의 `lib/src.zip` 에서 **직접 읽은** `java.base/java/util/concurrent/ConcurrentHashMap.java`·`CopyOnWriteArrayList.java`·`atomic/LongAdder.java`.
> **실행 검증** — 이 문서의 모든 출력·에러·수치는 Temurin **JDK 21.0.5** 에서 실제로 돌려 얻은 것이다.\
> 정확성 실험 `(55-a)` `(55-c)` `(55-d)` 는 **17.0.13 · 21.0.5 · 25.0.1** 에서 각각 돌렸다 —\
> **정답/오답 패턴은 세 버전이 같았고**(`(55-d)` 는 출력이 한 글자도 안 달랐다), **수치는 전부 달랐다**(아래 「구현 세부사항」).\
> 성능 실험 `(55-b)` `(55-e)` `(55-f)` 는 **21 에서만** 돌렸다.
> ⚠️ **측정 조건 — 이 주제의 수치는 두 종류다. 섞어 읽으면 안 된다.**\
> ① **정확성 실험**(정답 횟수) — 스레드를 직접 띄워 **각 10회 반복**하고 「정답 횟수 / 10」과 「관측 합의 최소~최대」로 적는다.\
> ② **성능 실험**(ms) — **JMH 가 아니다.** 워밍업 3회 뒤 **측정 7회의 중앙값**이고, 최소·최대를 함께 적었다.\
> 머신: **CPU 24코어**(`availableProcessors` = 24), Linux x86-64.\
> 흔들림: 성능 실험의 최소~최대가 **`AtomicLong` 8스레드에서 377~997 ms** 로 2.6배까지 벌어졌다. **자릿수만 읽는다.**\
> ★ **「안 터졌다」는 「안전하다」가 아니다.** 아래 「어디서 틀리나」의 실패는 전부 **터지지 않고 조용히 값이 줄어드는** 형태다.
> **버전** — `java.util.concurrent.atomic` 의 `AtomicInteger`·`AtomicLong`·`AtomicReference` 는 **`@since 1.5`**,\
> **`LongAdder` 와 `ConcurrentHashMap.mappingCount` 는 `@since 1.8`** 이다(`src.zip` 직접 확인).\
> `putIfAbsent`·`computeIfAbsent`·`merge` 는 `ConcurrentHashMap` 소스에 `@since` 가 없다 — **`java.util.Map` 의 디폴트 메서드 쪽이 `@since 1.8`** 이고 여기서는 그것을 재정의한다(`Map.java` 의 835·1058·1319 줄에서 직접 읽었다).\
> `ConcurrentHashMap` 자체는 `@since 1.5`, `CopyOnWriteArrayList` 는 `@since 1.5` 다.
> **범위** — **메모리 모델·happens-before 는 [`../../언어-특성/README.md`](../../언어-특성/README.md) §9 가 정본이다.**\
> 그쪽은 **CAS·`volatile` 쓰기가 무엇을 보장하나**까지, 여기는 **그 도구로 코드를 어떻게 쓰나**부터다.\
> 해시맵의 내부 구조(버킷·충돌·트리화)는 [`../../../../../data-structure/05-hashmap/`](../../../../../data-structure/05-hashmap/) 이 정본이다.\
> 그쪽은 **해시 테이블이 어떻게 생겼나**까지, 여기는 **그 위에 얹힌 동시성 계약**부터.\
> 병렬 스트림에서 공유 컬렉션이 깨지는 모습과 공용 ForkJoinPool 경합은 [`../49-parallel-streams/`](../49-parallel-streams/) 가 정본이다 — **여기서 다시 재지 않는다.**
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 javadoc·`src.zip` 으로, 출력은 실행으로 접지했다.

## 한눈에 — 쉽게 말하면

**CAS 는 "값이 아직 그대로면 바꿔라"를 한 번에 하는 것이고, 동시 컬렉션은 그 위에 지은 집이다.**

비유 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 방 열쇠를 받아 들어갔다 나오기 | `synchronized` — [33번 주제](../33-synchronized-and-volatile/) |
| **"내가 본 값이 아직 그대로면 바꿔 주세요"** | **CAS(`compareAndSet`)** |
| 실패하면 다시 보고 다시 시도 | CAS 루프 — `incrementAndGet` 안에 들어 있다 |
| 장부 한 권에 모두가 줄 서서 적기 | `AtomicLong` — 경합이 세면 줄이 길어진다 |
| **장부를 여러 권으로 쪼개 적고 나중에 합치기** | **`LongAdder`** — 읽을 때 합친다 |
| 서랍이 여러 칸인 캐비닛, 칸마다 열쇠 | `ConcurrentHashMap` — 버킷 단위 잠금 |
| **꺼내 보고 다시 넣기** | **`get` + `put` — 그 사이가 비어 있다** |
| 서랍째 맡기고 "이렇게 고쳐 주세요" | `compute` / `merge` — 한 번에 끝난다 |
| 통째로 복사해 새 장부를 만들기 | `CopyOnWriteArrayList` — 쓰기가 비싸다 |

- CAS 는 **열쇠를 안 받는다.** 그냥 시도하고, 남이 먼저 바꿨으면 다시 시도한다.
- 그래서 **경합이 없으면 아주 싸고, 경합이 세면 재시도가 늘어난다.**\
  실측에서 16스레드일 때 **증가 1회당 재시도가 1.77회**였다.
- **`LongAdder` 는 그 재시도를 없애려고 칸을 늘린다.**\
  실측에서 24스레드 × 200만 회가 `AtomicLong` **2,758 ms** 대 `LongAdder` **50 ms** 였다.
- **원자 연산 둘을 이어 붙이면 원자가 아니다.**\
  `map.get()` 하고 `map.put()` 하면 각각은 안전한데 **합쳐서는 안전하지 않다** — 실측 0/10회 정답.

```text
get + put (원자 연산 둘)                    merge (원자 연산 하나)

  m.get("k")  -> 5                          m.merge("k", 1, Integer::sum)
       |                                          |
   (여기서 남이 6 을 씀)                      (버킷을 잡은 채 읽고 더하고 쓴다)
       |                                          |
  m.put("k", 6)  <- 남의 6 을 덮는다               v
       |                                    10회 전부 160,000 (정답)
       v
  10회 전부 틀림 (104,465 ~ 124,739)
```

**똑같은 구조로** 자바가 이렇게 동작한다: 캐비닛 = `ConcurrentHashMap`, 서랍 칸 = 버킷,\
`compute`/`merge` 는 **그 칸을 잡은 채** 람다를 돌린다.

실무에서 이게 사고를 내는 자리는 **"`ConcurrentHashMap` 을 썼는데 카운트가 모자란다"** 이다.\
맵은 안전한데 **내가 그 위에 비원자 조합을 얹은 것**이다.

> **CAS(compare-and-swap)** — "메모리의 이 자리가 아직 기대값이면 새 값으로 바꿔라"를 **CPU 명령 하나로** 하는 것.\
> 예: `ai.compareAndSet(10, 20)` 은 지금 값이 10일 때만 20으로 바꾸고 `true` 를, 아니면 아무것도 안 하고 `false` 를 준다.

> **경합(contention)** — 여러 스레드가 **같은 자리**를 동시에 건드리려 몰리는 상태.\
> 예: 카운터 하나를 24개 스레드가 두들기면 경합이 세고, 스레드가 하나면 경합이 없다.

> **약하게 일관된 반복자(weakly consistent iterator)** — 순회 중에 맵이 바뀌어도 예외를 안 던지고,\
> 바뀐 것이 보일 수도 안 보일 수도 있는 반복자.\
> 예: `ConcurrentHashMap` 의 반복자는 `ConcurrentModificationException` 을 던지지 않는다.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 네 질문을 둔다.

1. CAS 는 **락의 무엇을 대체하고 무엇은 대체하지 못하나.**
2. `AtomicLong` 과 `LongAdder` 는 **어느 지점에서 갈리나.**
3. `ConcurrentHashMap` 이 **보장하는 단위**는 무엇인가 — 어디까지가 원자적인가.
4. 동시 컬렉션이 **값을 내는 조건**은 무엇인가 — 특히 `CopyOnWriteArrayList`.

## 동작 방식

### (1) CAS 가 대체하는 것 — 읽고-고치고-쓰기

**언제 쓰나** — 카운터·플래그·참조 하나를 여러 스레드가 고칠 때.

**실행 결과** (`Ex.java` — 55-a, 8스레드 × 10만 회, 각 10회 반복, JDK 21.0.5)

```text
--- 8스레드 x 100000회 증가 (기대 800000) / 각 10회 반복
  int++                    정답  3/10회  관측 119673 ~ 800000
  AtomicInteger.incrementAndGet  정답 10/10회
  ai.set(ai.get() + 1)     정답  0/10회  관측 236912 ~ 351488   <- 원자 연산 둘을 이어 붙이면 원자가 아니다
  LongAdder.increment      정답 10/10회
```

```text
ai.incrementAndGet()                       ai.set(ai.get() + 1)

  한 번의 CAS 루프                           원자 연산 두 개
  +---------------------------+              +---------------------------+
  | do {                      |              |  v = ai.get()   (원자적)   |
  |   cur = 읽는다            |              |     ... 남이 끼어든다 ...  |
  |   if CAS(cur, cur+1) 성공 |              |  ai.set(v + 1)  (원자적)   |
  | } while (실패)            |              +---------------------------+
  +---------------------------+                       |
             |                                        v
             v                                 10회 전부 틀림
       10회 전부 정답
```

그림 해설 (한 단계씩):

- **`incrementAndGet` 은 10/10회 정답**이다. 읽고-고치고-쓰기가 **한 덩어리**다.
- **`ai.set(ai.get() + 1)` 은 0/10회 정답**이다. 두 호출 **각각은** 원자적인데 **사이가 비어 있다.**
- ★ **이것이 이 주제 전체의 핵심 규칙이다** — **원자 연산을 이어 붙이면 원자가 아니다.**
- 참고로 일반 `int++` 은 **3/10회 정답**이었다. **틀린 것이 다수파지만 전부는 아니다** —\
  「안 터졌다」가 안전의 증거가 아닌 이유는 [`../33-synchronized-and-volatile/`](../33-synchronized-and-volatile/) 가 정본이다.

비용 — CAS 는 락을 안 잡으므로 **교착이 없고 대기도 없다.** 대신 **실패하면 다시 한다.**

### (2) CAS 는 몇 번 다시 시도하나

**언제 쓰나** — 경합이 셀 때 비용이 어디서 오는지 볼 때.

**실행 결과** (`Ex.java` — 55-a, 직접 CAS 루프를 돌려 재시도를 센다, 각 스레드 5만 회, JDK 21.0.5)

```text
--- CAS 는 몇 번 다시 시도하나 (직접 루프를 돌려 센다)
  스레드  1 : 최종값 50000(기대 50000)  재시도 0회  증가 1회당 0.00회
  스레드  2 : 최종값 100000(기대 100000)  재시도 46,862회  증가 1회당 0.47회
  스레드  4 : 최종값 200000(기대 200000)  재시도 99,592회  증가 1회당 0.50회
  스레드  8 : 최종값 400000(기대 400000)  재시도 159,880회  증가 1회당 0.40회
  스레드 16 : 최종값 800000(기대 800000)  재시도 1,418,995회  증가 1회당 1.77회
```

```text
스레드 1 (경합 없음)                        스레드 16 (경합 셈)

  읽는다 -> CAS -> 성공                      읽는다 -> CAS -> 실패
       |                                          -> 다시 읽는다 -> CAS -> 실패
       v                                          -> ... 평균 1.77회 더
  재시도 0회, 값은 항상 정답                       |
                                                  v
                                            값은 여전히 정답, 시간만 든다
```

그림 해설 (한 단계씩):

- **모든 경우에 값은 정답**이다. 재시도는 **정확성이 아니라 비용**의 문제다.
- 스레드 1개면 **재시도 0회**. 경합이 없으면 CAS 는 사실상 공짜다.
- 16스레드에서 **증가 1회당 1.77회** 재시도했다 — 같은 일을 **2.77배** 한 셈이다.
- ★ **CAS 루프 안의 람다는 여러 번 불린다.** 그래서 **부수효과를 넣으면 안 된다**(아래 「어디서 틀리나」 3번).

비용 — 경합이 세지면 **CAS 가 락보다 나을 이유가 사라진다.** 그때 쓰는 것이 (3) 이다.

### (3) `AtomicLong` 과 `LongAdder` 의 갈림

**언제 쓰나** — 카운터를 고를 때. **경합 정도가 기준이다.**

**실행 결과** (`Ex.java` — 55-b, 스레드당 200만 회, **워밍업 3회 + 측정 7회의 중앙값**, JMH 아님, 24코어)

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

```text
스레드 1 (경합 없음)                        스레드 24 (경합 셈)

  AtomicLong    12 ms  <- 가장 빠르다        AtomicLong    2,758 ms
  LongAdder     19 ms                       LongAdder        50 ms  <- 가장 빠르다
  synchronized  43 ms                       synchronized 14,548 ms
        |                                          |
        v                                          v
  칸이 하나뿐인 게 이득                        칸을 쪼갠 게 55배 이득
```

그림 해설 (한 단계씩):

- **스레드 1개일 때는 `AtomicLong` 이 가장 빠르다**(12 대 19 ms). `LongAdder` 는 칸 관리 비용이 있다.
- **스레드가 2개만 돼도 뒤집힌다**(172 대 26 ms).
- **24스레드에서 `LongAdder` 가 `AtomicLong` 의 55배, `synchronized` 의 291배** 빠르다.
- **`synchronized` 는 경합이 세지면 자릿수가 바뀐다** — 43 → 14,548 ms.
- ★ **흔들림이 크다.** `AtomicLong` 8스레드가 **377~997 ms**(2.6배)였다. **자릿수만 읽는다.**
- javadoc 이 이 갈림을 그대로 적는다.

  > This class is usually preferable to `AtomicLong` when multiple threads update a common sum that is used
  > for purposes such as collecting statistics, not for fine-grained synchronization control.
  > Under low update contention, the two classes have similar characteristics. But under high contention,
  > expected throughput of this class is significantly higher, at the expense of higher space consumption.

**읽기 비용은 반대로 간다**

**실행 결과** (`Ex.java` — 55-f, 1000만 회 읽기, 워밍업 3회 뒤 1회, JDK 21.0.5)

```text
--- 1. 경합을 겪은 LongAdder 의 sum() 비용
  (24스레드가 두들긴 뒤 sum = 48000000)
  AtomicLong.get()            : 3 ms
  LongAdder.sum() 경합 없던 것 : 3 ms
  LongAdder.sum() 경합 겪은 것 : 169 ms   <- 칸이 늘어난 만큼 읽기가 비싸진다
```

- **경합을 겪은 `LongAdder` 는 읽기가 56배 비싸다.** 칸을 전부 더해야 하기 때문이다.
- **쓰기가 압도적으로 많고 읽기는 가끔**일 때 `LongAdder` 가 맞는다. 통계·지표가 정확히 그 모양이다.
- 매번 읽어서 분기하는 값(예: 재고 수량)에는 **`AtomicLong` 이 낫다.**

비용 — **`LongAdder` 는 값 하나를 여러 칸에 나눠 갖는다.** 메모리를 더 쓰고, `sum()` 이 **딱 그 순간의 근사**다.

### (4) `ConcurrentHashMap` — 무엇이 원자적인가

**언제 쓰나** — 맵에 카운트를 쌓거나, 키마다 값을 고칠 때. **이 주제의 대표 사고다.**

**실행 결과** (`Ex.java` — 55-c, 8스레드 × 2만 회, 키 4개, 각 10회 반복, JDK 21.0.5)

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

```text
get + put (0/10회)                         merge (10/10회)

  스레드 A: get("k") -> 5                   스레드 A: merge("k", 1, sum)
  스레드 B: get("k") -> 5                     |-- 버킷을 잡는다
  스레드 A: put("k", 6)                       |-- 읽고 더하고 쓴다
  스레드 B: put("k", 6)   <- A 의 결과가 사라졌다  |-- 버킷을 놓는다
       |                                    스레드 B: 그 다음에 들어온다
       v                                          |
  16만이 10만으로 줄었다                             v
                                            16만 그대로
```

그림 해설 (한 단계씩):

- **세 가지 "읽고 나서 쓰기" 조합이 전부 0/10회**다. 개수가 **16만에서 9~12만으로 줄었다.**
- **`merge`·`compute` 는 10/10회**다. javadoc 이 그 이유를 적는다 — "The entire method invocation is performed atomically."
- **`computeIfAbsent` 로 `AtomicInteger` 를 넣고 그것을 올리는 것**도 10/10회다.\
  맵 연산은 한 번(값 객체 생성)이고 증가는 `AtomicInteger` 가 맡는다.
- ★ **`ConcurrentHashMap` 이 보장하는 단위는 "메서드 호출 하나"다.** 그 밖은 내 책임이다.

**`putIfAbsent` 와 `computeIfAbsent` 의 차이**

```text
--- putIfAbsent 는 객체를 미리 만든다, computeIfAbsent 는 필요할 때만 만든다
  putIfAbsent    : 값 객체를 1000번 만들었다
  computeIfAbsent: 값 객체를 1번 만들었다
```

- **`putIfAbsent(k, new X())` 는 값을 **항상** 만든다.** 인자를 평가해야 호출이 되니까.
- **`computeIfAbsent(k, k -> new X())` 는 없을 때만 만든다.** 1000회 중 **1회**.
- 값이 비싼 객체(커넥션·버퍼·`AtomicInteger`)면 이 차이가 크다.

비용 — `compute`/`merge` 는 **버킷을 잡은 채 람다를 돌린다.** 그래서 람다는 **짧고 단순해야** 한다.\
javadoc 원문: "Some attempted update operations on this map by other threads may be blocked while computation is in progress, so the computation should be short and simple."

### (5) `compute` 안에서 같은 맵을 건드리면

**언제 쓰나** — `computeIfAbsent` 람다에 로직을 넣을 때.

**실행 결과** (`Ex.java` — 55-d, JDK 21.0.5)

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

```text
ConcurrentHashMap                          HashMap

  같은 버킷 -> IllegalStateException        어느 키든 -> ConcurrentModificationException
  다른 버킷 -> 조용히 성공                    (modCount 하나로 전체를 본다)
       |                                          |
       v                                          v
  "터졌다/안 터졌다"가 키에 좌우된다            항상 터진다 (그래서 더 낫다, 진단 면에서는)
```

그림 해설 (한 단계씩):

- **같은 키나 같은 버킷이면 `IllegalStateException: Recursive update`** 다. 메시지가 정확하다.
- **다른 버킷이면 조용히 성공한다**(`{A=1, B=2}`). ★ **터지는지가 키의 해시에 좌우된다** — 테스트에서 안 걸린다.
- `merge` 중첩은 **예외 없이 `{A=6}`** 이 나왔다. 기대와 다른 값이지만 **아무 신호가 없다.**\
  (이 문서는 그 값이 6 이 된 내부 경로는 **추적하지 않았다.** 관측만 적는다.)
- **`HashMap` 은 어느 경우든 `ConcurrentModificationException`** 이다 — 진단 면에서는 오히려 낫다.
- javadoc 이 못박는다 — "The mapping function must not modify this map during computation."\
  `merge` 쪽은 "must not attempt to update any other mappings of this Map."

비용 — **`compute` 계열의 람다 안에서는 그 맵을 절대 건드리지 않는다.** 예외가 안 나도 규칙 위반이다.

### (6) `size()` 는 근사다

**언제 쓰나** — 맵 크기로 분기·검증할 때.

**실행 결과** (`Ex.java` — 55-e, 8스레드가 각 5만 건, 10회 반복, JDK 21.0.5)

```text
--- 1. 넣는 도중에 size() 를 읽으면 (8스레드가 각 5만 건, 10회 반복)
  모두 끝난 뒤 size() 가 틀린 실행 : 0/10
  넣는 도중 size() 와 mappingCount() 가 어긋난 최대 폭 : 3783
  (javadoc: "the results of aggregate status methods including size, isEmpty, and containsValue are typically useful only when a map is not undergoing concurrent updates")
```

```text
갱신이 멈춘 뒤 (정지 상태)                  갱신이 도는 중

  size() = 400,000  (10/10회 정확)          size() 와 mappingCount() 가
       |                                     같은 순간에 최대 3,783 만큼 달랐다
       v                                          |
  검증에 써도 된다                                  v
                                            분기·검증에 쓰면 안 된다
```

그림 해설 (한 단계씩):

- **갱신이 끝난 뒤에는 10/10회 정확했다.** "항상 틀린다"가 아니다.
- **갱신이 도는 동안에는 어긋난다.** 같은 순간에 읽은 `size()` 와 `mappingCount()` 가 **최대 3,783** 달랐다.
- javadoc 원문이 그 경계를 정확히 말한다 — 결과가 *"adequate for monitoring or estimation purposes, but not for program control"*.
- **`mappingCount()`**(`@since 1.8`) 는 `long` 을 준다. javadoc 이 **"The value returned is an estimate"** 라고 명시한다.\
  `size()` 는 `int` 라 20억을 넘는 맵을 표현하지 못한다.

비용 — **크기로 프로그램 흐름을 정하지 않는다.** 모니터링 지표로만 쓴다.

### (7) 순회 — 예외를 안 던지는 대신 무엇을 보나

**언제 쓰나** — 동시에 고쳐지는 컬렉션을 순회할 때.

**실행 결과** (`Ex.java` — 55-e, JDK 21.0.5)

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

```text
ConcurrentHashMap 반복자                    CopyOnWriteArrayList 반복자

  "약하게 일관됨"                             "스냅샷"
  순회 중 추가된 것이                          반복자를 만든 시점의 배열을 본다
  보일 수도, 안 보일 수도                      나중에 추가된 것은 절대 안 보인다
       |                                          |
       v                                          v
  예외 없음. 이번 실험에서는 100/100 보였다      예외 없음. [1,2,3] 만 봤다
  (그래도 보장이 아니다)                        remove() 는 UnsupportedOperationException
```

그림 해설 (한 단계씩):

- **`ConcurrentHashMap` 은 `ConcurrentModificationException` 을 안 던진다.** `HashMap` 은 던진다.
- 순회 중 넣은 것이 **이번 실험에서는 100/100회 보였다.**\
  ★ **그래도 "보인다"는 보장이 아니다.** javadoc 은 반복자가 *"at or since the creation of the iterator"* 시점의 상태를 반영한다고만 적는다.
- **`CopyOnWriteArrayList` 의 반복자는 스냅샷**이다. 만든 뒤 `add(4)` 한 것이 **안 보였다.**\
  그리고 **`Iterator.remove()` 가 `UnsupportedOperationException`** 이다 — 복사본을 고쳐 봐야 소용없으니까.
- javadoc 원문: "The iterator will not reflect additions, removals, or changes to the list since the iterator was created."

비용 — 예외가 안 나는 대신 **무엇을 봤는지 정확히 말할 수 없다.** 그 대가를 받아들일 때만 쓴다.

### (8) `CopyOnWriteArrayList` 가 값을 내는 조건

**언제 쓰나** — 리스너 목록·설정 목록처럼 **거의 안 바뀌는데 자주 읽는** 것.

**실행 결과** (`Ex.java` — 55-e, 워밍업 2회 뒤 3회의 중앙값, JMH 아님, JDK 21.0.5)

```text
--- 5. 쓰기 비용 (원소 N개를 하나씩 add, 3회 중앙값)
  N= 1,000  ArrayList(비동기)   0.1 ms   synchronizedList   0.1 ms   CopyOnWriteArrayList     0.4 ms
  N=10,000  ArrayList(비동기)   0.7 ms   synchronizedList   0.8 ms   CopyOnWriteArrayList    88.0 ms
  N=50,000  ArrayList(비동기)   0.9 ms   synchronizedList   2.1 ms   CopyOnWriteArrayList   584.5 ms
--- 6. 읽기 비용 (원소 1만 개를 1000번 순회, 3회 중앙값)
  ArrayList  14.4 ms   synchronizedList   9.5 ms   CopyOnWriteArrayList  19.7 ms
--- 7. 8스레드가 동시에 add 하면 (각 1만 건, 10회)
  ArrayList             크기 정답  0/10회  관측 2,405 ~ 47,033  예외 난 실행 1회
  synchronizedList      크기 정답 10/10회  관측 80,000 ~ 80,000  예외 난 실행 0회
  CopyOnWriteArrayList  크기 정답 10/10회  관측 80,000 ~ 80,000  예외 난 실행 0회
```

```text
쓰기가 잦다 (N=50,000 을 하나씩 add)        읽기만 한다 (1만 개를 1000번 순회)

  ArrayList              0.9 ms            ArrayList             14.4 ms
  synchronizedList       2.1 ms            synchronizedList       9.5 ms
  CopyOnWriteArrayList 584.5 ms            CopyOnWriteArrayList  19.7 ms
        |                                          |
        v                                          v
  650배 느리다 — 쓸 수 없다                   세 배가 다 비슷하다 (차이가 안 난다)
```

그림 해설 (한 단계씩):

- **쓰기가 잦으면 못 쓴다.** 5만 건을 하나씩 넣는 데 **584 ms** — `ArrayList` 의 **650배**다.\
  `add` 마다 배열 전체를 복사하기 때문이다(javadoc: "making a fresh copy of the underlying array").
- **이 실험에서는 읽기 이득이 안 나왔다** — 단일 스레드 순회라 락 경합이 없어서\
  `synchronizedList` 가 오히려 가장 빨랐다(9.5 ms). **읽기 이득은 경합이 있을 때 나온다.**\
  ★ 이 문서는 **경합 있는 읽기를 측정하지 않았다.** 여기 수치로 "읽기가 빠르다"를 주장하지 않는다.
- **8스레드 동시 `add` 에서 `ArrayList` 는 0/10회**다. 개수가 **2,405~47,033** 로 제각각이고 **예외가 난 실행은 10회 중 1회**뿐이다.\
  ★ **대부분은 예외 없이 조용히 원소가 사라졌다.** 병렬 스트림에서의 같은 실패는 [`../49-parallel-streams/`](../49-parallel-streams/) 가 정본이다.

비용 — **쓰기 O(n)** 이다. **원소가 수백 개 이하이고 쓰기가 드물 때**만 쓴다.

### (9) 경합이 있을 때 비로소 갈린다 — 읽기 쪽 실측

**언제 쓰나** — (8) 의 단일 스레드 읽기 실험이 **차이를 못 낸 이유**를 보고 싶을 때.

(8) 은 **한 스레드가 순회**했다. 그때는 셋이 거의 같았다.동시 컬렉션의 값은 **여러 스레드가 동시에 읽을 때** 나오므로 조건을 바꿔 다시 쟀다.

**실행 결과** (`Ex.java` — 55-h, 원소 5,000개 × 200회 순회, 워밍업 2 + 측정 5의 중앙값, JMH 아님, 24코어)

```text
--- 여러 스레드가 동시에 순회 (원소 5,000개 x 200회) / 워밍업 2 + 측정 5의 중앙값
    (A) synchronizedList 를 그냥 for-each      <- javadoc 이 금지하는 형태(락 없이 순회)
    (B) synchronizedList 를 synchronized 로 감싸 순회  <- javadoc 이 요구하는 형태
    (C) CopyOnWriteArrayList 를 그냥 for-each   <- 락이 필요 없다
  스레드  1 : (A)     3 ms   (B)      2 ms   (C)     3 ms
  스레드  8 : (A)     4 ms   (B)     12 ms   (C)     4 ms
  스레드 24 : (A)     6 ms   (B)     44 ms   (C)    10 ms
```

```text
스레드 1 (경합 없음)                        스레드 24 (경합 셈)

  (A) 3 ms  (B) 2 ms  (C) 3 ms              (A) 6 ms  (B) 44 ms  (C) 10 ms
        |                                          |
        v                                          v
  셋이 구별되지 않는다                          올바르게 잠근 (B) 가 (C) 의 4.4배
  -> (8) 이 차이를 못 낸 이유가 이것            -> 여기가 CopyOnWriteArrayList 의 자리다
```

그림 해설 (한 단계씩):

- **(B) 가 javadoc 이 요구하는 형태**다. `Collections.synchronizedList` 의 javadoc 원문:

  > It is imperative that the user manually synchronize on the returned
  > list when traversing it via `Iterator`, `Spliterator` or `Stream`

- **(A) 는 빠르지만 규칙 위반**이다. 순회 중 남이 고치면 `ConcurrentModificationException` 이 난다.  ★ 이 실험에서 (A) 가 (B) 보다 빨랐던 것은 **안전을 안 지켰기 때문**이지 장점이 아니다.
- **24스레드에서 (B) 44 ms 대 (C) 10 ms — 4.4배**다.  순회하는 내내 락을 쥐므로 **읽기끼리도 줄선다.**
- ★ **그래서 `CopyOnWriteArrayList` 의 조건은 "쓰기가 드물다"만이 아니다.**  **"여러 스레드가 동시에 순회한다"**가 함께 성립해야 값이 나온다.  단일 스레드 읽기(8)에서는 **오히려 손해**였다.

비용 — (8) 과 (9) 를 함께 읽는다. **쓰기 650배 손해를 읽기 4.4배 이득으로 갚을 수 있을 때만** 쓴다.

### (10) 맵 구현 셋 — 같은 일을 시키면

**언제 쓰나** — `ConcurrentHashMap` 대신 `Collections.synchronizedMap` 을 써도 되나 물을 때.

**실행 결과** (`Ex.java` — 55-g, 8스레드가 각 20만 회 `merge`, 키 1000개, 워밍업 2 + 측정 5의 중앙값, JMH 아님)

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

```text
쓰기 위주 (merge 100%)                      읽기 위주 (읽기 99% / 쓰기 1%)

  ConcurrentHashMap     40 ms              ConcurrentHashMap      3 ms
  synchronizedMap      216 ms              synchronizedMap      184 ms
  HashMap+synchronized 258 ms                    |
        |                                        v
        v                                  61배 — 읽기에서 차이가 더 벌어진다
  5.4배
```

그림 해설 (한 단계씩):

- **쓰기 위주에서 `ConcurrentHashMap` 이 5.4배** 빠르다(40 대 216 ms).
- **읽기 위주에서는 61배**다(3 대 184 ms). ★ **읽기에서 차이가 더 크다.**  `synchronizedMap` 은 **읽기에도 맵 전체 락**을 잡기 때문이다.
- `Collections.synchronizedMap(new HashMap<>())` 과 **직접 `synchronized` 로 감싸는 것**은 거의 같다(216 대 258 ms).  **같은 일을 하는 두 형태**일 뿐이다.
- 세 경우 모두 **최종 합은 정확했다**(프로그램이 `AssertionError` 로 검증한다). **성능 차이지 정확성 차이가 아니다.**

비용 — **`Collections.synchronizedMap` 을 새로 쓸 이유가 없다.** 레거시에서 만나면 `ConcurrentHashMap` 으로 바꾼다(단 **`null` 키·값을 쓰고 있었다면** 그것부터 걷어내야 한다 — 「문법」 절).

## 문법 — 형태와 규칙

### `Atomic*` 의 연산 네 갈래

```java
AtomicInteger a = new AtomicInteger(10);

a.get(); a.set(20);                      // volatile 읽기/쓰기와 같은 효과
a.incrementAndGet(); a.getAndIncrement(); // CAS 루프가 안에 들어 있다
a.compareAndSet(20, 30);                  // CAS 한 번 — 실패하면 false 를 주고 끝
a.updateAndGet(x -> x * 2);               // CAS 루프 + 람다
a.accumulateAndGet(5, Integer::sum);      // CAS 루프 + 두 인자 람다
```

**실행 결과** (`Ex.java` — 55-f, JDK 21.0.5)

```text
--- 2. CAS 한 번으로 되는 것과 안 되는 것
  compareAndSet(10, 20)      : true  값 20
  compareAndSet(10, 30)      : false  값 20   <- 기대값이 다르면 실패하고 아무것도 안 바꾼다
  getAndUpdate(x -> x * 2)   : 반환 20  값 40
  updateAndGet(x -> x + 1)   : 반환 41  값 41
  accumulateAndGet(5, sum)   : 반환 46  값 46
```

- **`getAnd*` 는 바꾸기 전 값**, **`*AndGet` 은 바꾼 뒤 값**을 반환한다.
- `compareAndSet` 은 **실패해도 예외가 아니다.** `false` 를 주고 아무것도 안 바꾼다.

### `ConcurrentHashMap` 의 원자 연산

```java
m.putIfAbsent(k, v);                      // 없을 때만 넣는다
m.computeIfAbsent(k, key -> 비싼객체());    // 없을 때만 만들고 넣는다
m.computeIfPresent(k, (key, v) -> v + 1);
m.compute(k, (key, v) -> v == null ? 1 : v + 1);
m.merge(k, 1, Integer::sum);              // 카운팅의 표준형
m.replace(k, oldV, newV);                 // 맵 버전의 CAS
m.remove(k, v);                           // 값이 v 일 때만 지운다
```

- 위 전부 **"메서드 호출 하나"가 원자적**이다. 둘을 이어 붙이면 아니다.
- `merge`/`compute` 의 람다가 **`null` 을 반환하면 그 키가 지워진다.**

```text
  merge 의 remapping 이 null 을 반환하면 :
    키가 지워진다 → {}
```

### `null` 이 금지다

**실행 결과** (`Ex.java` — 55-c, JDK 21.0.5)

```text
--- null 키·null 값
  put(null, "v") : java.lang.NullPointerException
  put("k", null) : java.lang.NullPointerException
  HashMap 은 둘 다 된다 : {null=null}
  그래서 CHM 은 get()==null 이 "없다"를 확정한다 (HashMap 은 못 한다)
```

- **키도 값도 `null` 이면 `NullPointerException`** 이다.
- 이것은 불편이 아니라 **설계**다 — `get(k) == null` 이 **"없다"를 확정**한다.\
  `HashMap` 에서는 "없다"와 "값이 `null` 이다"를 `containsKey` 없이 구분할 수 없고,\
  동시 환경에서는 `containsKey` 와 `get` 사이가 또 비어 있다.

## 어디서 틀리나

### 1. `get` 하고 `put` 한다

- (4) 의 실측 — **0/10회 정답**, 16만이 9~12만으로 줄었다.
- **`merge` 나 `compute` 로 바꾼다.**

### 2. 원자 연산 둘을 이어 붙인다

- `ai.set(ai.get() + 1)` 은 **0/10회 정답**이다((1)).
- `if (!m.containsKey(k)) m.put(k, v)` 도 같은 모양이다 — `putIfAbsent` 로 바꾼다.

### 3. CAS 루프의 람다에 부수효과를 넣는다

**실행 결과** (`Ex.java` — 55-f, JDK 21.0.5)

```text
--- 3. 람다가 여러 번 불릴 수 있다 (updateAndGet 은 CAS 루프다)
  스레드 1 : 최종값 100,000  람다 호출 100,000회 (증가 1회당 1.00회)
  스레드 8 : 최종값 800,000  람다 호출 1,977,224회 (증가 1회당 2.47회)
  → 이 람다에 부수효과(로그·카운터·DB 쓰기)를 넣으면 그만큼 더 실행된다
```

- 8스레드에서 람다가 **증가 1회당 2.47회** 불렸다.
- **로그·카운터·DB 쓰기를 넣으면 2.47배 실행된다.** 람다는 **순수 함수**여야 한다.
- `compute`/`merge` 의 람다도 같다 — 게다가 그쪽은 **버킷을 잡은 채** 돈다.

### 4. "각각 원자적"을 "함께 원자적"으로 읽는다

**실행 결과** (`Ex.java` — 55-f, 50만 회 관찰, JDK 21.0.5)

```text
--- 4. 두 변수를 함께 바꿔야 하면 CAS 로는 안 된다
  x 와 y 를 각각 원자적으로 올리는 동안 x != y 로 보인 횟수 : 68182 / 500,000회 관찰
  → "각각 원자적"은 "둘이 함께 원자적"이 아니다. 그때는 락이나 불변 객체 + AtomicReference 다
--- 5. AtomicReference 로 두 값을 한 번에
  a != b 로 보인 횟수 : 0 / 500,000회 관찰   (최종 Pair[a=500000, b=500000])
```

- `AtomicInteger` 둘을 각각 올리면 **50만 회 중 68,182회** 불일치가 보였다.
- **불변 객체 하나를 `AtomicReference` 에 넣으면 0회**다. 두 값이 **한 번에** 바뀐다.

### 5. `compute` 람다 안에서 같은 맵을 건드린다

- (5) 의 실측 — **같은 버킷이면 `IllegalStateException: Recursive update`, 다른 버킷이면 조용히 성공.**
- 키의 해시에 좌우되므로 **테스트에서 안 걸린다.**

### 6. `size()` 로 분기한다

- (6) 의 실측 — 갱신 중에 **최대 3,783** 어긋났다.
- javadoc 이 "not for program control" 이라고 적는다.

### 7. `ConcurrentHashMap` 을 넣고 나서 전체를 락으로 감싼다

```java
synchronized (map) { if (!map.containsKey(k)) map.put(k, v); }   // 의미 없다
```

- 다른 스레드가 **락 없이** `map.put` 을 부르면 이 `synchronized` 는 아무것도 막지 못한다.
- **`ConcurrentHashMap` 에 외부 락을 거는 순간 잘못 가고 있는 것**이다. 원자 연산을 쓴다.

### 8. `CopyOnWriteArrayList` 에 대량으로 넣는다

- (8) 의 실측 — 5만 건에 **584 ms**, `ArrayList` 의 650배.
- 처음 만들 때는 **생성자에 컬렉션을 통째로 넘긴다**(`new CopyOnWriteArrayList<>(list)`).

### 9. `ArrayList` 를 여러 스레드가 함께 고친다

- (8) 의 실측 — **0/10회 정답**, 예외는 10회 중 1회뿐이다. **대부분 조용히 사라진다.**

### 10. `Collections.synchronizedList` 를 순회한다

- 개별 메서드만 동기화된다. **순회는 직접 `synchronized (list) { ... }` 로 감싸야** 한다.
- 이 문서는 그 실패를 **재현하지 않았다**(순회 중 수정 시 `ConcurrentModificationException` 이 난다는 것은 javadoc 의 기술이다).

### 11. `ConcurrentHashMap` 에 `null` 을 넣으려 한다

- `NullPointerException` 이다((문법 절)). `Optional` 이나 센티널 값으로 바꾼다.

### 12. 통계 카운터에 `AtomicLong` 을 쓴다

- (3) 의 실측 — 24스레드에서 **`LongAdder` 가 55배** 빠르다.
- 반대로 **매번 읽어서 분기하는 값**에는 `LongAdder` 가 나쁘다(읽기 56배).

## 구현 세부사항 대 언어 보장

| 관측한 것 | 누가 보장하나 | 버전에 갈리나 |
|---|---|---|
| `merge`/`compute` 호출 하나가 원자적인 것 | **javadoc 이 보장** — "The entire method invocation is performed atomically" | 확인 안 함(21에서만 측정) |
| `get`+`put` 조합이 깨지는 것 | **보장의 부재**가 근거다. javadoc 이 조합을 약속한 적 없다 | 21에서 10회 |
| `IllegalStateException("Recursive update")` 문구 | **구현 세부.** javadoc 은 "must not modify" 라고만 적는다 | 21에서만 확인 |
| 다른 버킷이면 안 터지는 것 | **보장 아님.** 키의 해시와 테이블 크기에 좌우된다 | 21에서만 확인 |
| `size()` 가 정지 상태에서 정확한 것 | **보장 아님.** javadoc 은 "estimation purposes" 라고 적는다 | 21에서 10회 |
| `mappingCount()` 가 추정치인 것 | **javadoc 이 명시** — "The value returned is an estimate" | `@since 1.8` |
| `LongAdder` 가 경합에서 빠른 것 | **javadoc 이 방향만 보장** — "significantly higher throughput ... under high contention". **배수는 보장 아님** | 21에서만 측정 |
| CAS 재시도 횟수(증가 1회당 1.77회) | **전적으로 구현·머신 의존** | ★ **갈린다** — 16스레드에서 17 **4.30회** / 21 **1.77회** / 25 **1.31회** |
| `updateAndGet` 람다가 2.47회 불리는 것 | javadoc 이 "The function should be side-effect-free, since it may be re-applied when attempted updates fail due to contention among threads" 라고 경고한다. **횟수는 보장 아님** | 21에서만 측정 |
| `CopyOnWriteArrayList` 의 반복자가 스냅샷인 것 | **javadoc 이 보장** — "The iterator will not reflect additions ... since the iterator was created" | `@since 1.5` |
| 순회 중 넣은 키가 100/100회 보인 것 | **보장 아님.** javadoc 은 "at or since the creation of the iterator" 만 약속한다 | 21에서 100회 |

**세 버전에서 갈린 것과 같았던 것** (실제로 돌려 확인했다)

```text
                          17.0.13      21.0.5       25.0.1
--------------------  -----------  -----------  -----------
int++ 정답 (10회 중)        7/10         3/10         8/10   <- 갈린다
merge / compute 정답      10/10        10/10        10/10   <- 같다
get+put 정답               0/10         0/10         0/10   <- 같다
CAS 재시도 (16스레드)      4.30회       1.77회       1.31회   <- 갈린다
Recursive update 출력      동일         동일         동일    <- 한 글자도 안 달랐다
```

★ **이 문서의 수치 중 보장인 것은 하나도 없다.** 보장은 전부 javadoc 문장으로만 적었다.\
★ **"세 곳에서 같았다"도 보장이 아니다.** `merge` 의 원자성은 세 버전이 같아서가 아니라 **javadoc 문장이 있어서** 보장이다.

## 언제 쓰고 언제 안 쓰나

| 상황 | 고르는 것 | 왜 |
|---|---|---|
| 스레드 하나가 대부분 올리는 카운터 | **`AtomicLong`** | 경합 없으면 12 ms 로 가장 빠르다 |
| 여러 스레드가 두들기는 통계 카운터 | **`LongAdder`** | 24스레드에서 55배 빠르다 |
| 자주 읽어서 분기하는 수량 | **`AtomicLong`** | `LongAdder.sum()` 이 56배 비싸다 |
| 두 값을 함께 바꿔야 한다 | **불변 객체 + `AtomicReference`** | "각각 원자적"으로는 안 된다(68,182회 불일치) |
| 맵에 카운트를 쌓는다 | **`ConcurrentHashMap.merge`** | 10/10회 정답 |
| 키마다 비싼 객체를 한 번만 만든다 | **`computeIfAbsent`** | `putIfAbsent` 는 1000회 중 1000회 만든다 |
| 맵의 값이 자주 바뀌는 카운터 | **`ConcurrentHashMap<K, LongAdder>`** | javadoc 자신이 이 조합을 예로 든다 |
| 리스너 목록 — 거의 안 바뀌고 **여러 스레드가 동시에 순회**한다 | **`CopyOnWriteArrayList`** | 24스레드 순회에서 올바르게 잠근 `synchronizedList` 의 4.4배 |
| 거의 안 바뀌는데 **한 스레드만 읽는다** | `List.copyOf` 등 불변 리스트 | 단일 스레드 읽기에서는 `CopyOnWriteArrayList` 가 오히려 손해였다 |
| 레거시의 `Collections.synchronizedMap` | **`ConcurrentHashMap`** | 쓰기 5.4배·읽기 61배. 새로 쓸 이유가 없다 |
| 큐로 스레드 사이를 잇는다 | `BlockingQueue` 계열 | [54번 주제](../54-executorservice-and-future/) |
| 필드 셋 이상을 한 덩어리로 바꾼다 | **`synchronized`·`ReentrantLock`** | CAS 로는 표현이 안 된다. [33번 주제](../33-synchronized-and-volatile/) |
| 읽기만 하는 설정 맵 | **`Map.of` / 불변 맵** | 공유를 안 하면 이 장 전체가 필요 없다 |

## 핵심 문장

- **원자 연산을 이어 붙이면 원자가 아니다.** `get`+`put` 은 10회 중 0회 정답이었다.
- **`ConcurrentHashMap` 이 보장하는 단위는 메서드 호출 하나다.**
- **`LongAdder` 는 쓰기가 몰릴 때 이기고, 읽기가 잦으면 진다.** 24스레드 55배 대 읽기 56배.
- **CAS 루프의 람다는 여러 번 불린다.** 부수효과를 넣지 않는다.
- **`size()` 는 갱신 중에 근사다.** 모니터링용이지 분기용이 아니다.
- **`CopyOnWriteArrayList` 는 쓰기가 O(n) 이다.** 그 대가를 받아들일 때만 쓴다.

## 관련 자료

- [`../33-synchronized-and-volatile/`](../33-synchronized-and-volatile/) — 락의 문법과 `volatile` 의 경계.\
  그쪽은 **락으로 막는 법**까지, 여기는 **락 없이 막는 법**부터. `int++` 이 왜 안 되는지의 바이트코드 근거도 그쪽이다.
- [`../41-map-api-merge-compute/`](../41-map-api-merge-compute/) — `Map` API 의 `merge`/`compute*`/`getOrDefault`.\
  그쪽은 **단일 스레드에서 그 메서드들을 어떻게 쓰나**까지, 여기는 **그 메서드들이 동시성에서 무엇을 보장하나**부터.
- [`../../../../../data-structure/05-hashmap/`](../../../../../data-structure/05-hashmap/) — 해시 테이블의 내부.\
  그쪽은 **버킷·충돌·트리화**까지, 여기는 **버킷 단위 잠금이 사용자에게 무엇으로 보이나**부터.
- [`../49-parallel-streams/`](../49-parallel-streams/) — **공유 컬렉션이 병렬에서 깨지는 모습의 정본.**\
  `ArrayList` 에 병렬 `forEach` 로 `add` 했을 때의 세 가지 실패 모드를 그쪽이 이미 실측했다. **여기서 다시 재지 않는다.**
- [`../54-executorservice-and-future/`](../54-executorservice-and-future/) — 이 자료구조들을 쓰는 실행 환경.
- [`../56-virtual-threads/`](../56-virtual-threads/) — 스레드가 수만 개가 될 때 이 선택들이 어떻게 바뀌나.
- [`../../언어-특성/README.md`](../../언어-특성/README.md) §9 — **happens-before 와 CAS 의 메모리 효과가 정본이다.**\
  그쪽은 **"동시성이 맞다"를 무엇으로 정의하나**까지, 여기는 **그 정의를 만족하는 API 를 어떻게 고르나**부터.
- [`../27-equals-hashcode-contract/`](../27-equals-hashcode-contract/) — 맵 키의 계약. 동시 맵에서도 그대로다.

## 용어 풀이

- **CAS(compare-and-swap)** — "이 자리가 아직 기대값이면 새 값으로 바꿔라"를 CPU 명령 하나로 하는 것.
- **경합(contention)** — 여러 스레드가 같은 자리를 동시에 건드리려 몰리는 상태.
- **재시도(retry)** — CAS 가 실패해 다시 읽고 다시 시도하는 것. 정확성이 아니라 비용의 문제다.
- **락 프리(lock-free)** — 락을 안 잡고도 **전체가 진전한다**는 성질. 한 스레드가 멈춰도 다른 스레드가 막히지 않는다.
- **`LongAdder`** — 합을 여러 칸에 나눠 갖고 `sum()` 에서 합치는 카운터. `@since 1.8`.
- **버킷(bin)** — 해시 테이블의 한 칸. `ConcurrentHashMap` 은 이 단위로 잠근다.
- **원자 연산(atomic operation)** — 중간 상태가 남에게 안 보이는 연산. **호출 하나가 단위다.**
- **약하게 일관된 반복자** — 순회 중 변경에 예외를 안 던지고, 변경이 보일 수도 안 보일 수도 있는 반복자.
- **`ConcurrentModificationException`** — `HashMap`·`ArrayList` 가 순회 중 수정을 감지해 던지는 것. 동시 컬렉션은 안 던진다.
- **`IllegalStateException("Recursive update")`** — `compute` 람다 안에서 같은 버킷을 다시 건드렸을 때 나오는 메시지.
- **스냅샷 반복자** — 만들어진 시점의 배열을 끝까지 보는 반복자. `CopyOnWriteArrayList` 의 것.
- **센티널(sentinel)** — `null` 대신 쓰는 "없음"을 뜻하는 특별한 값.

## 더 들어가면

- **ABA 문제** — CAS 는 "값이 같은가"만 본다. `A → B → A` 로 돌아온 것을 구분하지 못한다.\
  `AtomicStampedReference`(버전 번호를 같이 둔다) 가 그 답이다. **이 문서는 ABA 를 재현하지 않았다.**
- **`VarHandle`**(9+) — 필드에 CAS·acquire/release 접근을 직접 건다. `Atomic*` 객체를 안 만들고도 같은 일을 한다.
- **`ConcurrentSkipListMap`** — 정렬된 동시 맵. `TreeMap` 의 자리.
- **`ConcurrentHashMap` 의 대량 연산**(`forEach`·`search`·`reduce`, `@since 1.8`) — 병렬 임계값을 받는다.\
  이 문서는 **측정하지 않았다.**
- **`Striped64`** — `LongAdder`·`DoubleAdder` 의 공통 부모. 칸을 CPU 캐시 라인에 맞춰 떼어 놓는다.\
  **왜 그것이 빠른가는 [`../../언어-특성/README.md`](../../언어-특성/README.md) 와 하드웨어 영역이다.**
- **`ConcurrentSkipListSet`·`ConcurrentLinkedQueue`·`LinkedBlockingQueue`** — 리스트·큐 쪽 동시 자료구조.\
  큐는 **54번 주제**([`../54-executorservice-and-future/`](../54-executorservice-and-future/))의 작업 큐와 같은 물건이다.\
  이 문서는 **큐를 측정하지 않았다.**
