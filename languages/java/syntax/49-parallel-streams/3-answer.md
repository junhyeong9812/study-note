# java/syntax/49 — 병렬 스트림: 값이 나오는 조건 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·에러·수치는 **Temurin JDK 21.0.5 에서 실제로 돌려 얻은 것**이다.\
> 측정 머신: **CPU 24코어**(`availableProcessors` = 24, 공용 풀 병렬도 23).\
> ⚠️ **JMH 가 아니다.** 워밍업 5회 뒤 9회 측정의 중앙값이고, 두 번 돌리면 배수가 흔들린다.\
> 수치는 **자릿수만** 읽는다. 다른 머신에서 그대로 재현되지 않는다.\
> javadoc 인용은 `lib/src.zip` 의 `java.base/java/util/stream/package-info.java`·`Collectors.java` 원문이다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 어떤 소스가 잘 갈리는가

**출력** (`Ex.java` — 49-a, 원소 1024개, JDK 21.0.5)

```text
ArrayList              est=1024         분할=가능     왼쪽=512          특성=ORDERED SIZED SUBSIZED
LinkedList             est=1024         분할=가능     왼쪽=1024         특성=ORDERED SIZED SUBSIZED
HashSet                est=1024         분할=가능     왼쪽=512          특성=DISTINCT
int[] (Arrays.stream)  est=1024         분할=가능     왼쪽=512          특성=ORDERED SIZED SUBSIZED IMMUTABLE
Stream.iterate 2인자     est=MAX(모름)      분할=가능     왼쪽=4611686018427387903 특성=ORDERED IMMUTABLE
```

**`estimateSize()`**

- 앞의 넷은 **1024**, `Stream.iterate` 는 **`Long.MAX_VALUE`**(= 9223372036854775807, 표에는 `MAX(모름)` 으로 표시했다).

**잘라 낸 쪽의 크기**

| 소스 | 왼쪽 | 읽는 법 |
|---|---|---|
| `ArrayList` | **512** | 정확히 반 |
| `int[]` | **512** | 정확히 반 |
| `HashSet` | **512** | 해시 테이블을 반으로 — 실제 원소 수는 고르지 않다 |
| `LinkedList` | **1024** | 잘랐는데 크기를 제대로 모른다 |
| `Stream.iterate` | **4611686018427387903** | `Long.MAX_VALUE / 2` — 모른다는 뜻 |

**어떤 플래그가 있어야 하나**

- **`SIZED` + `SUBSIZED`** 다.

```text
SIZED 만 있음                              SIZED + SUBSIZED

  전체 개수는 안다                            전체도 알고 조각도 안다
  자른 뒤의 크기는 모른다                      자른 뒤도 정확히 안다
        |                                          |
        v                                          v
  조각마다 작업을 어떻게 나눌지                 미리 배열을 잡고 자리를 정할 수 있다
  미리 계획할 수 없다
```

**`LinkedList` 가 잘 안 갈리는 이유**

```text
배열                                       연결 리스트

  [0][1][2] ... [1023]                      0 -> 1 -> 2 -> ... -> 1023
        ^                                    링크를 512번 따라가야
   인덱스 512 를 계산으로 찾는다                중간을 찾는다
        |                                          |
   O(1) 로 자른다                            기본 구현은 아예 다르게 한다:
                                             앞에서 원소를 배치로 퍼 담아
                                             그 배열을 잘라 낸 조각으로 쓴다
                                                   |
                                             즉 "자르기" 자체가 순차 순회다
```

- `왼쪽=1024` 라는 값이 그 증거다 — 퍼 담은 조각의 크기를 제대로 못 센다.
- 재귀 분할 실측에서 `LinkedList` 는 **1025조각**이 나왔다(`ArrayList` 는 1024조각).\
  결국 원소 단위까지 잘게 갈렸고, 그 과정 전체가 순차 순회였다.

**무한 스트림의 `estimateSize()`**

- **`Long.MAX_VALUE`** 다. javadoc 이 "크기를 모름"을 이 값으로 표현한다.
- 그래서 `count()` 같은 최적화가 안 걸리고(46번 4번), 병렬 분할 계획도 못 세운다.

### 2. 병렬이 이득인 경우와 손해인 경우

**출력** (`Ex.java` — 49-e, 24코어, 마이크로초 중앙값)

```text
== 1) int[] 합계 — 1000만 개 ==
  Arrays.stream(int[]).sum()         중앙값     4248 us   (최소 4141, 최대 5012)
  Arrays.stream(int[]).parallel().sum() 중앙값      833 us   (최소 546, 최대 971)
  -> 병렬 / 순차 = 5.10 배
== 2) 같은 합계인데 박싱을 거치면 — 1000만 개 ==
  List<Integer> 순차 mapToInt.sum()    중앙값    14014 us
  List<Integer> 병렬 mapToInt.sum()    중앙값     7676 us
  -> 병렬 / 순차 = 1.83 배
== 3) LinkedList — 100만 개 ==
  LinkedList 순차                      중앙값     5477 us
  LinkedList 병렬                      중앙값     8512 us
  -> 병렬 / 순차 = 0.64 배
== 4) 작은 데이터 — 100개 ==
  int[100] 순차                        중앙값        1 us
  int[100] 병렬                        중앙값      137 us
  -> 병렬 / 순차 = 0.01 배
== 5) 원소당 일이 무거우면 — 2000개 ==
  무거운 일 순차                           중앙값     4616 us
  무거운 일 병렬                           중앙값      702 us
  -> 병렬 / 순차 = 6.58 배
== 6) Stream.iterate (분할 불가 소스) — 100만 개 ==
  iterate 순차                         중앙값     6205 us
  iterate 병렬                         중앙값    22008 us
  -> 병렬 / 순차 = 0.28 배
== 7) IntStream.range 대 boxed() ==
  IntStream.range 병렬 sum             중앙값      801 us
  range.boxed() 병렬 sum               중앙값    12426 us
  -> boxed 쪽이 15.51 배 걸린다
```

**이득인 것**

- **(A) 5.10배, (E) 6.58배** — 이 둘이다.
- (B)는 1.83배로 **이득이긴 하지만 절반 이하로 깎였다**(박싱 때문).
- (C) 0.64배, (D) 0.01배, (F) 0.28배는 **전부 손해**다.

**(D)의 배수**

- **약 0.01배 — 100배 느려졌다.** 1us 짜리 일이 137us 가 됐다.
- 손해가 이득보다 훨씬 극적이라는 점이 중요하다.\
  최대 이득은 코어 수(24)로 막혀 있지만 **손해에는 상한이 없다.**

**(E)는 이득인데 (D)는 손해인 이유**

> **나누고 합치는 고정 비용보다 실제 일이 커야 이득이 난다.** (E)는 2000개뿐이지만 원소당 일이 크고, (D)는 100개에 원소당 일이 거의 없다.

**판단 기준**

- **원소 수 × 원소당 비용**이다.
- "1만 건 이상이면 병렬" 같은 규칙은 틀린다 — (E)는 2000건에 이득, (C)는 100만 건에 손해였다.

**다른 머신에서 믿어도 되나**

- **안 된다.**
- 이 머신은 24코어다. 4코어에서는 최대 배수가 4 근처로 떨어진다.
- 같은 머신에서 두 번 돌린 결과도 이만큼 흔들렸다.

```text
              1회차      2회차
  (A)         5.10       3.92
  (B)         1.83       2.28
  (C)         0.64       0.50
  (D)         0.01       0.01
  (E)         6.58       8.11
  (F)         0.28       0.24
  (7) boxed  15.51      34.07
```

- **부호(1보다 큰가 작은가)는 안정적이고 소수점은 아니다.** 읽을 것은 부호와 자릿수다.

### 3. 누가 실행하는가

**출력** (`Ex.java` — 49-d, 24코어)

```text
availableProcessors    : 24
commonPool parallelism : 23
== 누가 실행하나 ==
순차 : [main]
병렬 : 스레드 17개
       [ForkJoinPool.commonPool-worker-1, ForkJoinPool.commonPool-worker-10, ForkJoinPool.commonPool-worker-11, ForkJoinPool.commonPool-worker-15, ForkJoinPool.commonPool-worker-16, ForkJoinPool.commonPool-worker-17, ForkJoinPool.commonPool-worker-18, ForkJoinPool.commonPool-worker-19, ForkJoinPool.commonPool-worker-2, ForkJoinPool.commonPool-worker-21, ForkJoinPool.commonPool-worker-3, ForkJoinPool.commonPool-worker-4, ForkJoinPool.commonPool-worker-5, ForkJoinPool.commonPool-worker-6, ForkJoinPool.commonPool-worker-7, ForkJoinPool.commonPool-worker-8, main]
```

**스레드 이름**

- (A) 순차 → **`[main]`** 하나뿐이다.
- (B) 병렬 → **`ForkJoinPool.commonPool-worker-N`** 들과 **`main`**.

**개수**

- 실측 **17개**(실행마다 다르다 — 8\~11개로 나올 때도 있었다).
- 병렬도가 23이어도 **항상 23개를 다 쓰지는 않는다.** 작업 훔치기라 필요한 만큼만 깨어난다.

**병렬도는 코어 수와 같은가**

- **아니다.** 24코어에서 **23**이다.

```text
availableProcessors = 24
        |
        v
공용 풀 병렬도 = 23   (워커 스레드)
        +
호출한 스레드 1개      (main — 결과를 기다리는 대신 같이 일한다)
        =
동시에 일하는 것 24개
```

**`main` 도 일을 하는가**

- **한다.** 워커 목록에 `main` 이 들어 있는 것이 그 증거다.
- 병렬 스트림은 호출 스레드를 놀리지 않는다 — `invoke` 로 작업을 던지고 그 스레드도 참여한다.
- 그래서 병렬도가 코어 수 **- 1** 인 것이다.

### 4. 공용 풀을 공유한다는 것

**출력** (`Ex.java` — 49-d, 5회 반복)

```text
풀이 붐빌 때 24칸 작업: 402 ms   (404 / 404 / 402 / 405 / 404)
풀이 한가할 때 같은 작업: 154 ms   (153 / 156 / 154 / 160 / 153)
```

**둘이 동시에 돌면**

- **같은 풀의 작업자를 나눠 쓴다.** 내 작업이 순서를 기다린다.

**시간 차이**

- **402ms 대 154ms — 약 2.6배.**
- 5회 반복에서 **402\~405 / 153\~160** 으로 매우 안정적이었다.\
  (이 측정은 바쁜 대기 루프라 GC·JIT 영향이 적다.)

```text
공용 풀이 한가할 때                         다른 스레드가 공용 풀을 쓰는 중일 때

  내 작업 24칸                               남의 작업 40칸이 먼저 큐에 있다
  +---+---+ ... +---+                        +---+---+ ... +---+
  | 24명이 한 번에    |                       | 내 24칸이 기다린다 |
  +---+---+ ... +---+                        +---+---+ ... +---+
        154 ms                                      402 ms
              같은 코드, 내 코드는 한 글자도 안 바뀌었다
```

**웹 서버에서 왜 위험한가**

- **요청 A 의 `.parallel()` 이 요청 B 를 느리게 만든다.**
- 부하가 오를수록 더 나빠진다 — 요청이 늘면 공용 풀 경합도 는다.
- 그리고 **장애 원인이 내 코드에 안 보인다.** 프로파일러도 "풀에서 기다림"만 보여 준다.
- 라이브러리가 내부에서 `.parallel()` 을 쓰고 있으면 더 찾기 어렵다.

**블로킹 I/O 를 하면**

- **풀 전체가 막힌다.** 워커 23개가 전부 소켓을 기다리면 다른 병렬 스트림은 아무것도 못 한다.
- ForkJoinPool 은 CPU 바운드 작업을 전제로 설계됐다 — 블로킹이 들어가면 전제가 깨진다.

**전용 풀**

```java
ForkJoinPool mine = new ForkJoinPool(3);
Set<String> r = mine.submit(() -> stream.parallel().collect(...)).get();
mine.shutdown();
```

**출력** (`Ex.java` — 49-d)

```text
전용 풀(3) : [ForkJoinPool-1-worker-1, ForkJoinPool-1-worker-2]
```

- 워커 이름이 **`ForkJoinPool-1-worker-N`** 이다 — 공용 풀을 안 썼다.

**그 동작은 계약인가**

- **아니다.** javadoc 어디에도 "`ForkJoinPool.submit` 안에서 돌린 병렬 스트림은 그 풀을 쓴다"는 계약이 없다.
- 구현에 기댄 관용구다. 널리 쓰이지만 **보장에 기대지 않는 편이 낫다.**
- 서버라면 애초에 `ExecutorService` 로 작업을 나누는 쪽을 고른다([**54번 주제**](../54-executorservice-and-future/)).

### 5. `ArrayList` 에 `forEach` 로 `add` 하면

**출력** (`Ex.java` — 49-b, 10만 개, 10회)

```text
  0: 크기 17692 <- 원소가 사라졌다 / null 포함 true
  1: 크기 6762 <- 원소가 사라졌다 / null 포함 true
  2: 예외 java.lang.ArrayIndexOutOfBoundsException
  3: 크기 8939 <- 원소가 사라졌다 / null 포함 true
  4: 예외 java.lang.ArrayIndexOutOfBoundsException
  5: 크기 8562 <- 원소가 사라졌다 / null 포함 true
  6: 크기 11997 <- 원소가 사라졌다 / null 포함 false
  7: 예외 java.lang.ArrayIndexOutOfBoundsException
  8: 크기 9195 <- 원소가 사라졌다 / null 포함 false
  9: 예외 java.lang.ArrayIndexOutOfBoundsException
== 순차 스트림이면 멀쩡하다 ==
  크기 100000
```

**`out.size()`**

- **10만이 아니다.** 실측 6,762 \~ 17,692.

**매번 같은가**

- **아니다.** 10회가 전부 달랐다.

**예외가 나는가**

- **날 때도 있고 안 날 때도 있다** — 10회 중 4회.
- **나쁜 쪽은 안 날 때다.** 결과가 나오는데 틀렸다.

**`null` 이 들어갈 수 있는가**

- **있다.** 10회 중 6회에서 `null` 이 섞였다.

```text
ArrayList.add(x) 가 실제로 하는 일 (원자적이 아니다)

  1. size 를 읽는다
  2. elementData[size] = x
  3. size = size + 1

  스레드 A 와 B 가 동시에 add 하면:

  A: size 읽음 = 100          B: size 읽음 = 100        <- 같은 값을 읽었다
  A: elementData[100] = x     B: elementData[100] = y   <- x 가 덮어써져 사라진다
  A: size = 101               B: size = 101             <- +1 이 한 번만 반영
        또는
  A: size = 101               B: size = 102             <- 둘 다 반영
        -> elementData[101] 에 아무도 안 썼다 -> null 이 남는다
```

- 그리고 배열이 꽉 차면 `grow()` 가 새 배열을 만드는데, 그 사이 다른 스레드가 옛 크기 기준 인덱스로 쓰면 **`ArrayIndexOutOfBoundsException`** 이다.

**스택트레이스** (`Ex.java` — 49-c, JDK 21.0.5)

```text
Caused by: java.lang.ArrayIndexOutOfBoundsException: Index 9686 out of bounds for length 9369
	at java.base/java.util.ArrayList.add(ArrayList.java:484)
	at java.base/java.util.ArrayList.add(ArrayList.java:496)
	at java.base/java.util.stream.ForEachOps$ForEachOp$OfRef.accept(ForEachOps.java:184)
	at java.base/java.util.stream.IntPipeline$1$1.accept(IntPipeline.java:180)
	at java.base/java.util.stream.Streams$RangeIntSpliterator.forEachRemaining(Streams.java:104)
```

- `Index 9686 out of bounds for length 9369` — **`size` 가 배열 길이를 앞질렀다**는 증거다.

**순차로 바꾸면**

- **정확히 10만.** 완벽히 정상이다.
- 그래서 **개발·테스트에서 절대 안 잡힌다.** 병렬로 바꾼 뒤 운영에서 조용히 데이터가 샌다.

### 6. 그 사고를 고치는 방법

**출력** (`Ex.java` — 49-b)

```text
  collect(toList())            : 크기 100000
  toList()                     : 크기 100000
  synchronizedList + forEach   : 크기 100000 (순서는 깨진다: 앞 5개 [66406, 66407, 66408, 66409, 66410])
  CopyOnWriteArrayList(2000개) : 크기 2000
```

**`collect(toList())`**

- **맞는다.** 10만.
- 스트림이 **조각마다 리스트를 만들고 결합자로 순서대로 합친다.** 공유 상태가 없다.
- `Stream.toList()`(16+)도 같다.

**`synchronizedList`**

- **개수는 맞고 순서는 깨진다.** 앞 5개가 `[66406, ...]` 였다.
- 해결된 것: 경쟁 조건(유실·`null`·예외).
- 안 된 것: **입력 순서.** 그리고 락 경합으로 느려진다 — 모든 `add` 가 한 줄로 서기 때문이다.

**`CopyOnWriteArrayList` 가 부적절한 이유**

- **`add` 마다 배열 전체를 복사**한다. n 번 add 면 O(n²) 복사다.
- 10만 개로는 실질적으로 끝나지 않아 **2000개로 줄여서** 확인했다.
- 이 클래스는 "읽기가 압도적으로 많고 쓰기가 드문" 경우를 위한 것이다.

**javadoc 근거**

> If the behavioral parameters do have side-effects, unless explicitly stated, there are no guarantees as to: the *visibility* of those side-effects to other threads; that different operations on the "same" element within the same stream pipeline are executed in the same thread; and that behavioral parameters are always invoked, ...

> (Non-interference) ... preventing interference means ensuring that the data source is **not modified at all** during the execution of the stream pipeline.

- 두 번째 문장은 **소스**에 대한 것이지만, 첫 번째가 **부작용의 가시성**을 명시적으로 부정한다.
- 정리: **바깥 컬렉션을 고치지 말고 `collect` 로 받는다.**

### 7. `reduce` 가 병렬에서 다른 답을 내는 두 경우

**출력** (`Ex.java` — 49-f, 입력 1\~10)

```text
== 결합 법칙이 없는 reduce ==
뺄셈 순차 : -55
뺄셈 병렬 : -5
뺄셈 병렬 : -5
뺄셈 병렬 : -5
뺄셈 병렬 : -5
뺄셈 병렬 : -5
== 항등원이 아닌 씨앗 ==
합 순차(씨앗 100) : 155
합 병렬(씨앗 100) : 1055
```

**네 줄**

| | 결과 |
|---|---|
| (A) 뺄셈 순차 | **-55** |
| (B) 뺄셈 병렬 | **-5** |
| (C) 합 순차(씨앗 100) | **155** |
| (D) 합 병렬(씨앗 100) | **1055** |

**(B)가 (A)와 다른 이유**

> 뺄셈에는 **결합 법칙이 없다.** 조각으로 나눠 계산한 뒤 합치면 괄호 위치가 달라지고, 괄호 위치가 답을 바꾼다.

```text
순차                                       병렬 (조각 셋이라 치면)

  ((((0-1)-2)-3)-...-10)                   조각1: 0-1-2-3     = -6
        = -55                              조각2: 0-4-5-6     = -15
                                           조각3: 0-7-8-9-10  = -34
                                             합치기: (-6)-(-15)-(-34)
                                               = -6 +15 +34 ... 조각 수에 따라 달라진다
```

**(D)가 (C)와 다른 이유**

> 씨앗 `100` 이 **항등원이 아니기 때문**이다. 조각마다 씨앗을 한 번씩 쓰므로 조각이 10개면 100이 10번 더해진다.

```text
1055 = 1000 + 55
        ^      ^
        |      원소의 합 (1+2+...+10)
        100 이 10번 들어갔다 — 조각이 10개였다는 뜻
```

- javadoc 의 요구가 이것이다.

> More formally, the `identity` value must be an *identity* for the combiner function. This means that for all `u`, `combiner.apply(identity, u)` is equal to `u`.

- `Integer.sum(100, u)` 는 `u` 가 아니다 → 항등원이 아니다.

**예외나 경고**

- **없다.** 컴파일도 실행도 정상이다. **답만 바뀐다.**
- 이것이 이 주제에서 가장 조용한 실패 모드다.

**여러 번 돌리면 같은 값인가**

- 실측에서 **5회 모두 `-5`** 였다.
- **그것이 함정이다.** "돌려 보니 재현되네"로 읽혀 버린다.
- 조각 수는 데이터 크기·코어 수·풀 상태에 따라 달라지고, 그러면 값도 달라진다.\
  즉 **개발 머신에서 맞았는데 서버에서 틀린다.**

### 8. 순서를 지키는 연산의 값

**출력** (`Ex.java` — 49-h, 1000만 개 `int[]`, 마이크로초 중앙값)

```text
== 순서를 지키는 값이 얼마인가 ==
  병렬 filter.count (순서 무관)                     1532
  병렬 filter.limit(1000).sum                   8317
  병렬 unordered.filter.limit(1000).sum         1109
  병렬 skip(9_000_000).sum                       421
  순차 skip(9_000_000).sum                     23193
== distinct ==
  순차 distinct.count                         420446
  병렬 distinct.count                        1461811
  병렬 unordered.distinct.count               805927
== forEach 대 forEachOrdered ==
  병렬 forEach                                  8472
  병렬 forEachOrdered                         125047
  순차 forEach                                 116889
```

**(B)와 (C)의 차이**

- **약 7.5배**(8,317 대 1,109).

```text
limit(1000) — 순서를 지킬 때               .unordered().limit(1000)

  "앞에서부터 정확히 1000개"                 "아무 1000개"
  조각마다 자기 앞에 몇 개가 있는지           먼저 채우는 조각이 이기면 된다
  알아야 하므로 조정이 필요하다                    |
        |                                        v
        v                                     1109 us
     8317 us
```

**(D) — `distinct` 는 병렬이 빠른가**

- **아니다. 3.5배 느리다**(1,461,811 대 420,446).
- `.unordered()` 를 줘도 805,927us 로 **여전히 순차보다 느렸다.**
- 입력 순서를 지키면서 중복을 없애려면 조각 간 조정이 크기 때문이다.

**(E) 빠른 순서**

```text
  1등  병렬 forEach          8,472 us
  2등  순차 forEach        116,889 us    (14배 느림)
  3등  병렬 forEachOrdered 125,047 us    (순차보다도 조금 느리다)
```

- **`forEachOrdered` 는 병렬의 이득을 전부 반납한다.** 순차보다 약간 더 느리기까지 하다.
- 순서가 필요하면 `forEachOrdered` 보다 **`collect` 로 모아서 나중에 순회**하는 쪽이 낫다.

**이득인 순서 의존 연산도 있는가**

- **있다.**

| 연산 | 결과 |
|---|---|
| `skip(9_000_000)` | 병렬 **421us**, 순차 23,193us — **55배** |
| `sorted` | 역순 100만 개에서 순차 17,715us → 병렬 9,934us |

- `skip` 은 `SIZED` 소스라 **건너뛸 자리를 계산으로 찾는다.** 순차는 실제로 900만 개를 지나가야 한다.
- `sorted` 는 병합 정렬이라 **분할·정복이 자연스럽다.**
- 정리: **"순서 의존 = 병렬 손해"가 아니다.** 조각 간 조정이 필요한 것(`limit`·`distinct`·`forEachOrdered`)이 손해다.

### 9. `findFirst` 와 `findAny`

**출력** (`Ex.java` — 49-g, 0\~999 중 `i % 7 == 3`, 5회)

```text
  findFirst 3  /  findAny 668
  findFirst 3  /  findAny 668
  findFirst 3  /  findAny 668
  findFirst 3  /  findAny 668
  findFirst 3  /  findAny 668
== 순차에서는 findAny 도 첫 원소다 (5회) ==
3 3 3 3 3
```

**(A)와 (B)**

- (A) `findFirst` → **3** (5회 모두)
- (B) `findAny` → **668** (5회 모두)

**순차로 바꾸면**

- `findAny` 도 **3** 이다.

```text
순차                                       병렬

  앞에서부터 하나씩 본다                      조각 24개가 동시에 찾는다
  3 을 만나면 끝                              각 조각이 자기 첫 답을 낸다
        |                                          |
   findFirst = findAny = 3                   findFirst: 조각 순서를 따져
                                                        가장 앞인 3 을 고른다
                                             findAny:   먼저 신고한 조각의 답
                                                        (실측 668)
```

**어느 쪽이 싼가**

- **`findAny` 가 싸다.** 조각 간 순서를 따질 필요가 없다.
- `findFirst` 는 "더 앞 조각이 답을 낼지도 모른다"를 기다려야 한다.

**순차 개발에서 안 드러나는 이유**

- **순차에서는 두 메서드가 완전히 같은 값을 낸다.** 구별할 방법이 없다.
- 그래서 `findAny` 로 써 놓고 "첫 원소"를 가정한 코드가 쌓인다.
- 나중에 `.parallel()` 을 붙이는 순간 **조용히 다른 원소가 나온다.**
- 46번의 `forEach`/`forEachOrdered` 와 **완전히 같은 구조의 함정**이다.

### 10. 병렬에서의 `Collectors`

**출력** (`Ex.java` — 49-f, 17·21·25 동일)

```text
toList()            : [IDENTITY_FINISH]
toSet()             : [UNORDERED, IDENTITY_FINISH]
toMap()             : [IDENTITY_FINISH]
groupingBy()        : [IDENTITY_FINISH]
groupingByConcurrent: [CONCURRENT, UNORDERED, IDENTITY_FINISH]
joining()           : []
counting()          : []
```

**다섯 줄**

| 수집기 | 특성 |
|---|---|
| `toList()` | `[IDENTITY_FINISH]` |
| `toSet()` | `[UNORDERED, IDENTITY_FINISH]` |
| `toMap(...)` | `[IDENTITY_FINISH]` |
| `groupingBy(...)` | `[IDENTITY_FINISH]` |
| `groupingByConcurrent(...)` | `[CONCURRENT, UNORDERED, IDENTITY_FINISH]` |

- **`CONCURRENT` 가 붙은 것은 `groupingByConcurrent` 뿐**이다.
- `toSet()` 에 `UNORDERED` 가 붙은 것을 보라 — 집합은 순서가 의미 없으므로 조정 비용을 낼 필요가 없다.

**`toMap` 이 `CONCURRENT` 가 아니면**

```text
CONCURRENT 가 아닌 수집기                  CONCURRENT 수집기

  조각1 -> HashMap A                        조각1 ---+
  조각2 -> HashMap B                        조각2 ---+--> ConcurrentHashMap 하나
  조각3 -> HashMap C                        조각3 ---+
        |                                          |
   결합자가 A + B + C 를 합친다               합칠 것이 없다
   (키마다 merge)                                   |
        |                                          v
        v                                    그룹 안의 순서를 잃는다
   입력 순서가 유지된다
```

**병렬 `toMap` 의 결과는 순차와 같은가**

**출력** (`Ex.java` — 49-f, 20만 건)

```text
순차 크기 200000 / 병렬 크기 200000 / 같은가 true
병렬 결과 맵 타입 : java.util.HashMap
```

- **같다.** 수집기의 결합자 계약이 그것을 요구한다.
- 대신 **합치는 값이 든다.** javadoc 이 명시한다.

> The returned `Collector` is **not concurrent**. For parallel stream pipelines, the `combiner` function operates by merging the keys from one map into another, which **can be an expensive operation**. If it is not required that results are inserted into the `Map` in encounter order, using `toConcurrentMap(Function, Function)` may offer better parallel performance.

**`groupingByConcurrent` 가 얻는 것과 잃는 것**

**출력** (`Ex.java` — 49-f)

```text
groupingBy 병렬       : {blue=[lee, jung], green=[choi], red=[kim, park]}
groupingByConcurrent  : {blue=[jung, lee], green=[choi], red=[park, kim]} / 타입 ConcurrentHashMap
== groupingByConcurrent 는 그룹 안 순서를 잃는다 (5회) ==
  groupingBy  0번 그룹 앞 8개 : [0, 2, 4, 6, 8, 10, 12, 14]
  Concurrent  0번 그룹 앞 8개 : [26, 12, 28, 14, 32, 22, 34, 36]
  groupingBy  0번 그룹 앞 8개 : [0, 2, 4, 6, 8, 10, 12, 14]
  Concurrent  0번 그룹 앞 8개 : [26, 12, 14, 6, 10, 36, 8, 34]
```

- **얻는 것**: 맵 합치기가 사라진다. 그룹이 많을수록 이득이 크다.
- **잃는 것**: **그룹 안의 순서.** `[lee, jung]` 이 `[jung, lee]` 가 됐고, 5회가 전부 다른 순서였다.
- `groupingBy` 쪽은 5회 모두 `[0, 2, 4, 6, ...]` 로 같았다 — **병렬이어도 입력 순서를 지킨다.**

### 11. 병렬에서 중복 키가 나면

**출력** (`Ex.java` — 49-f, 같은 코드 5회, JDK 21.0.5)

```text
예외 : java.lang.IllegalStateException: java.lang.IllegalStateException: Duplicate key 5 (attempted merging values 165625 and 165635)
예외 : java.lang.IllegalStateException: java.lang.IllegalStateException: Duplicate key 5 (attempted merging values 65625 and 65635)
예외 : java.lang.IllegalStateException: java.lang.IllegalStateException: Duplicate key 2 (attempted merging values 182812 and 182822)
예외 : java.lang.IllegalStateException: java.lang.IllegalStateException: Duplicate key 2 (attempted merging values 57812 and 57822)
예외 : java.lang.IllegalStateException: java.lang.IllegalStateException: Duplicate key 5 (attempted merging values 65625 and 65635)
```

**무엇이 던져지는가**

- **`IllegalStateException`** — 순차와 같은 타입이다(47번 2번).

**키와 값이 실행마다 같은가**

- **아니다.** 키가 `5` 일 때도 `2` 일 때도 있고, 값은 `165625`·`65625`·`182812`·`57812` 로 매번 달랐다.
- 조각 경계가 어디서 잡히느냐, 어느 조각이 먼저 끝나느냐에 달려 있다.

**감싸지는 경우가 있는가**

- **있다.** 위 다섯 줄은 전부 한 번 더 감싸져 있다(`IllegalStateException: java.lang.IllegalStateException: ...`).
- 그런데 **같은 코드가 감싸지지 않을 때도 있다.**

```text
JDK 25.0.1 에서 같은 코드 5회
  IllegalStateException: Duplicate key 2 (attempted merging values 132812 and 132822)          <- 안 감싸짐
  IllegalStateException: java.lang.IllegalStateException: Duplicate key 5 (...)                <- 감싸짐
  IllegalStateException: java.lang.IllegalStateException: Duplicate key 5 (...)                <- 감싸짐
  IllegalStateException: Duplicate key 2 (attempted merging values 132812 and 132822)          <- 안 감싸짐
  IllegalStateException: Duplicate key 2 (attempted merging values 132812 and 132822)          <- 안 감싸짐
```

- 조각 **안에서**(accumulator) 났는지 조각을 **합치다**(merger) 났는지에 따라 갈린다.
- 17·21·25 셋 다 같은 비결정성을 보였다. **버전 차이가 아니라 병렬의 성질**이다.

**어떻게 진단하나**

- **순차로 재현해서 진단한다.**

```java
// 병렬에서 터졌다면
list.stream().collect(Collectors.toMap(...));   // 순차로 바꿔 다시 돌린다
```

- 순차에서는 **첫 중복이 결정적으로 잡힌다** — 같은 키, 같은 값이 나온다.
- 그리고 애초에 **3인자 `toMap` 을 쓰면** 이 예외가 안 난다(47번 12번).

### 12. `.parallel()` 을 어디에 붙이는가

**출력** (`Ex.java` — 49-g)

```text
  중간에 parallel() : true
  parallel 뒤 sequential() : false
  parallel() 을 맨 뒤에 붙여도 앞 연산의 스레드 수 : 24
```

**`map` 은 몇 개의 스레드에서 도는가**

- **24개**다. `.parallel()` 을 `map` **뒤에** 붙였는데도 그렇다.

**왜 그런가**

```text
파이프라인은 최종 연산 때 한 번에 조립된다

  range -> map -> parallel -> sum
                     |
              "이 파이프라인은 병렬" 이라는 플래그를
              파이프라인 객체 전체에 세운다
                     |
                     v
  실행 시점에는 map 도 병렬로 돈다 — "여기부터"가 없다
```

- `.parallel()` 은 **스테이지가 아니라 파이프라인 속성**이다.
- 46번에서 본 대로 최종 연산 전에는 아무것도 실행되지 않으므로, **순서와 무관하게 플래그만 남는다.**

**`sequential()` 을 부르면**

- **순차가 된다.** `parallel()` 뒤에 불러도 이긴다 — **마지막으로 부른 것이 이긴다.**

**왜 위험한가**

- **`.parallel()` 을 파이프라인 중간(혹은 헬퍼 메서드 안)에 숨겨 두면 앞쪽 람다까지 스레드 안전성을 요구받는다.**
- 코드를 읽는 사람은 `map` 위쪽만 보고 "여기는 순차"라고 오해한다.
- 방어: **`.parallel()` 은 소스 바로 뒤에 붙인다.** 또는 `parallelStream()` 을 쓴다.\
  스트림을 만들어 돌려주는 메서드에서는 **병렬 여부를 호출자가 정하게** 한다.

### 13. 17·21·25 에서 무엇이 갈렸나

**달라진 것이 있는가**

- **있다.** 46\~49번 네 주제 중 **출력 값 자체가 버전에 따라 갈린 유일한 자리**다.\
  (46·47번에서도 차이가 있었지만 그것은 스택트레이스의 줄 번호였다.)

**어느 소스에서 무엇이**

```text
                        JDK 17.0.13        JDK 21.0.5 / 25.0.1
  Stream.iterate 2인자    왼쪽 = 1024        왼쪽 = 4611686018427387903
  Stream.iterate 3인자    왼쪽 = 1023        왼쪽 = 4611686018427387903
  BufferedReader.lines   왼쪽 = 3           왼쪽 = 4611686018427387903
```

- **크기를 모르는 소스를 `trySplit()` 했을 때 잘라 낸 쪽의 `estimateSize()`** 가 달랐다.
- 17 은 **실제로 퍼 담은 개수**를, 21·25 는 **`Long.MAX_VALUE / 2`**(= 모른다)를 돌려줬다.
- 나머지는 전부 같았다 — `ArrayList`·`LinkedList`·`HashSet`·`TreeSet`·배열·`IntStream.range` 의 특성과 크기,\
  그리고 재귀 분할 조각 수(1024 / 1025 / 2048 / 1)까지.

**수집기 특성은**

- **세 버전이 완전히 같았다.**

**`estimateSize()` 를 코드에서 써도 되나**

- **안 된다.** javadoc 이 **추정치**라고 못박는다.
- 실측이 그것을 보여 줬다 — 같은 소스, 같은 원소 수인데 버전마다 다른 값이 나왔다.
- `SIZED` 가 붙어 있을 때만 정확하고, 그때도 **분기 조건으로 쓰지 않는다.**

### 14. 이 코드에 `.parallel()` 을 붙일 것인가

**(A) 웹 요청 핸들러에서 `List<Order>` 500건 검증**

- **안 붙인다.**
- 500건은 너무 작고(실측 100건에서 100배 손해), **공용 풀을 다른 요청과 공유**한다((3)·(4)).

**(B) 배치로 CSV 1000만 행을 파싱해 합계 (`BufferedReader.lines`)**

- **안 붙인다 — 그 소스로는.**
- `BufferedReader.lines` 는 **크기를 모르고 분할이 배치 버퍼링**이다((1)).
- 고치려면 **한 번 읽어 `ArrayList`/배열로 만든 뒤** 병렬로 돌린다. 메모리가 안 되면 순차로 간다.

**(C) 배치로 `int[]` 1000만 개의 평균**

- **붙인다.**
- 분할 최적 소스(`SIZED`+`SUBSIZED`), 충분한 크기, 박싱 없음, 순서 무관 — 실측 5.1배((2) 1번).
- 단 재고 붙인다.

**(D) 이미지 2000장 리사이즈**

- **붙인다(측정 후).**
- 원소는 2000개뿐이지만 **원소당 일이 압도적으로 무겁다** — (2) 5번의 6.58배가 이 모양이다.
- 주의: 리사이즈 결과를 **공유 컬렉션에 `forEach` 로 담지 않는다**((5)). `collect` 로 받는다.

**(E) `List<Long>` 100만 개를 조회해 각각 HTTP 호출**

- **절대 안 붙인다.**
- **블로킹 I/O 다.** 공용 풀 워커 전체가 소켓을 기다리며 막힌다((4)).
- 이 일에는 `ExecutorService`([**54번 주제**](../54-executorservice-and-future/))나 가상 스레드(**56번 주제**)를 쓴다.\
  병렬 스트림은 **CPU 바운드 작업을 코어 수만큼 나누는 도구**다.

---

## 실행 검증

| 프로그램 | 무엇을 확인했나 | 돌린 JDK |
|---|---|---|
| `Ex.java` (49-a) | 소스 11가지의 `Spliterator` 특성·`estimateSize`·`trySplit`, 재귀 분할 조각 수, 공용 풀 병렬도 | 17 · 21 · 25 (**크기 미상 소스의 분할 크기만 17 과 다름**) |
| `Ex.java` (49-b) | `ArrayList` + 병렬 `forEach` 의 세 실패 모드(10회), 고치는 법 넷, 순차는 정상 | 21 (비결정적이라 교차 비교 불가) |
| `Ex.java` (49-c) | `ArrayIndexOutOfBoundsException` 의 스택트레이스 원문 (50회 중 7회차에 발생) | 21 |
| `Ex.java` (49-d) | 워커 스레드 이름·개수, `main` 의 참여, 공용 풀 경합(5회 반복: 402\~405 대 153\~160ms), 전용 풀 | 21 |
| `Ex.java` (49-e) | 병렬/순차 배수 7가지 (워밍업 5 + 측정 9의 중앙값), 2회 반복해 흔들림 확인 | 21 |
| `Ex.java` (49-f) | 수집기 특성 7가지, 병렬 `toMap` 결과 일치(20만 건), 중복 키 예외의 비결정성(3버전 × 5회), `groupingByConcurrent` 의 순서 손실, 비결합 `reduce`·비항등원 씨앗 | 17 · 21 · 25 (**예외 감싸짐은 세 버전 모두 실행마다 다름**) |
| `Ex.java` (49-g) | `findFirst` 대 `findAny`(5회), `.parallel()` 의 위치가 무관함 | 21 |
| `Ex.java` (49-h) | 순서 의존 연산의 비용 11가지(`limit`·`unordered`·`skip`·`distinct`·`sorted`·`forEach`/`forEachOrdered`) | 21 |
| `src.zip` 열람 | `package-info` 의 Parallelism·Side-effects·Non-interference·Ordering·Associativity 절, `Collectors.toMap`/`groupingBy` 의 `@implNote` | 21 |

**측정 방법의 한계 (반드시 같이 읽을 것)**

- **JMH 가 아니다.** 워밍업 5회 뒤 9회 측정의 중앙값이다. DCE·JIT 편향을 완전히 막지 못한다.
- **머신 의존**이다 — 24코어. 코어가 적으면 이득 배수가 그만큼 줄고, 손해 배수는 그대로다.
- **실행마다 흔들린다** — 같은 프로그램 2회차에서 `5.10 → 3.92`, `15.51 → 34.07` 로 바뀌었다.
- 이 문서의 수치는 "**어느 방향인가**"의 근거이지 "**몇 배인가**"의 근거가 아니다.

**구현 의존 항목** (버전이 오르면 다시 돌려야 하는 것)

- 크기 미상 소스의 `trySplit` 결과 `estimateSize` — **17 과 21·25 가 실제로 달랐다.**
- 공용 풀 병렬도가 `availableProcessors - 1` 인 것.
- 전용 `ForkJoinPool.submit` 안에서 그 풀이 쓰이는 것 — javadoc 계약이 아니다.
- 병렬 중복 키 예외가 감싸지는지 여부와 그 키·값 — **같은 버전 안에서도 실행마다 다르다.**
- 재귀 분할 조각 수(1024 / 1025 / 2048).
- `ArrayList` 경쟁의 구체적 실패 형태(유실 개수·예외 발생률).
- **Java 8 의 동작은 안 돌려 봄** — 이 머신에 8이 없다.
