# java/syntax/49 — 병렬 스트림: 값이 나오는 조건 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **선행** — [`../46-terminal-operations/`](../46-terminal-operations/). 최종 연산·단락 평가·`forEachOrdered` 를 먼저 본다.
> **기준 소스** — [`java.util.stream` 패키지 javadoc (Java SE 21)](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/stream/package-summary.html) · [`Collectors` javadoc](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/stream/Collectors.html) · JDK 21.0.5 표준 라이브러리 소스 `java.base/java/util/stream/package-info.java`·`Collectors.java`(`lib/src.zip`)
> **실행 검증** — 이 문서의 모든 출력·에러·수치는 Temurin **JDK 21.0.5** 에서 실제로 돌려 얻은 것이다.\
> 측정 머신: **CPU 24코어**(`availableProcessors` = 24, 공용 풀 병렬도 23).\
> 분할 특성과 수집기 특성은 **17.0.13 · 25.0.1** 에서도 돌렸다 — **한 곳에서 갈렸다**(아래 「구현 세부사항 대 언어 보장」).
> ⚠️ **측정 방법** — JMH 가 아니다. 워밍업 5회 뒤 9회 측정의 **중앙값**이다.\
> 같은 프로그램을 두 번 돌리면 배수가 3.9~5.1 배처럼 흔들린다. **배수의 자릿수만 읽는다.**
> **버전** — `parallel()`·`parallelStream()` 은 **Java 8**. 17·21·25 동작 동일.
> **범위** — 스레드·JIT·GC 의 **런타임 내부**는 [`../../언어-특성/README.md`](../../언어-특성/README.md) 와 [`../../../../process-thread/`](../../../../process-thread/) 가 정본이다.\
> 그쪽은 **OS 스레드와 JVM 이 무엇을 하나**까지, 여기는 **이 API 를 언제 쓰면 이득인가**부터다.\
> 자료구조의 원리는 [`../../../../../data-structure/`](../../../../../data-structure/) 가 정본이다.\
> 그쪽은 **`ArrayList`·`LinkedList` 가 어떻게 생겼나**까지, 여기는 **그 모양이 분할에 유리한가**까지만 본다.
> 이 본문은 Claude 작성이다(원고 없음).

## 한눈에 — 쉽게 말하면

**병렬 스트림은 벨트를 여러 갈래로 쪼개 동시에 돌리는 것이다.**

44~48번의 비유를 그대로 잇는다.

| 비유 | 실체 |
|---|---|
| 벨트 하나 | 순차 스트림 |
| **벨트를 여러 갈래로 쪼갠 것** | **병렬 스트림 — 이 주제** |
| 물건 더미를 반으로 가르는 사람 | `Spliterator` — 분할 담당 |
| 갈래마다 붙는 작업자 | ForkJoinPool 의 워커 스레드 |
| **공장에 작업자 풀이 하나뿐** | **공용 ForkJoinPool 을 모두가 공유한다** |
| 갈래별 결과를 다시 합치는 사람 | 결합자(combiner) |
| 갈래를 나눌 수 없는 더미 | `Stream.iterate`·`BufferedReader.lines` |

- 쪼개려면 **더미를 반으로 가를 수 있어야** 한다.\
  배열은 "여기서 자르자" 한 번이면 되고, 연결 리스트는 **처음부터 세어 가야** 한다.
- 작업자를 붙이는 데도 비용이 든다.\
  **물건이 100개면 나누고 합치는 값이 일하는 값보다 크다.**
- 그리고 **작업자 풀은 공장에 하나뿐**이다.\
  옆 라인이 풀을 다 쓰고 있으면 내 라인은 그냥 기다린다.

```text
쪼갤 수 있는 더미 (int[] 1000만)           쪼갤 수 없는 더미 (Stream.iterate)

  [==================================]      1 -> 2 -> 3 -> 4 -> ...
   |        |        |        |             앞을 만들어야 뒤를 안다
   v        v        v        v                    |
  [====][====][====][====]  24갈래                  v
   작업자 24명이 동시에                        갈래를 못 만든다
        |                                     (억지로 나누면 미리 만들어 둬야 한다)
        v                                            |
  실측 5.1배 빨라졌다                                  v
                                             실측 0.28배 — 3.5배 느려졌다
```

**똑같은 구조로** Java 가 이렇게 동작한다: 더미 가르기 = `Spliterator.trySplit`, 작업자 = 공용 ForkJoinPool.

실무에서 이게 손해를 보는 자리는 **"느려서 `.parallel()` 을 붙여 봤다"** 이다.\
분할이 안 되는 소스거나, 데이터가 작거나, 순서를 지켜야 하는 연산이면 **더 느려진다.**

> **`Spliterator`** — "쪼갤 수 있는 반복자". 원소를 하나씩 주는 것과 **자신을 둘로 가르는 것** 둘 다 한다.\
> 예: `ArrayList` 의 것은 인덱스 중간을 잡아 한 번에 반으로 가른다.

> **공용 ForkJoinPool(common pool)** — JVM 에 하나뿐인 기본 작업자 풀.\
> 예: 별도 지정이 없으면 **모든 병렬 스트림이 이 하나를 나눠 쓴다.**

> **결합 법칙(associativity)** — `(a op b) op c` 와 `a op (b op c)` 가 같다는 성질.\
> 예: 덧셈은 성립하고 뺄셈은 성립하지 않는다. 병렬 `reduce` 는 이 성질에 기댄다.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. 어떤 조건에서 병렬이 **값을 내나** — 소스·데이터 크기·원소당 일의 양.
2. 어떤 코드가 병렬에서 **틀린 답을 내나** — 공유 상태·결합 법칙·항등원.
3. 병렬이 **순서를 지키느라 치르는 비용**은 얼마인가.

## 동작 방식

### (1) 분할 가능성 — 소스가 정한다

**언제 쓰나** — `.parallel()` 을 붙일지 말지 정할 때. 가장 먼저 보는 것.

**실행 결과** (`Ex.java` — 49-a, 원소 1024개, JDK 21.0.5)

```text
== 소스별 분할 가능성 ==
ArrayList              est=1024         분할=가능     왼쪽=512          특성=ORDERED SIZED SUBSIZED
List.of (불변)           est=4            분할=가능     왼쪽=2            특성=ORDERED SIZED SUBSIZED
LinkedList             est=1024         분할=가능     왼쪽=1024         특성=ORDERED SIZED SUBSIZED
HashSet                est=1024         분할=가능     왼쪽=512          특성=DISTINCT
TreeSet                est=1024         분할=가능     왼쪽=512          특성=ORDERED DISTINCT SORTED
int[] (Arrays.stream)  est=1024         분할=가능     왼쪽=512          특성=ORDERED SIZED SUBSIZED IMMUTABLE
IntStream.range        est=1024         분할=가능     왼쪽=512          특성=ORDERED DISTINCT SORTED SIZED SUBSIZED NONNULL IMMUTABLE
Stream.iterate 2인자     est=MAX(모름)      분할=가능     왼쪽=4611686018427387903 특성=ORDERED IMMUTABLE
Stream.iterate 3인자     est=MAX(모름)      분할=가능     왼쪽=4611686018427387903 특성=ORDERED IMMUTABLE
Stream.generate        est=MAX(모름)      분할=가능     왼쪽=4611686018427387903 특성=IMMUTABLE
BufferedReader.lines   est=MAX(모름)      분할=가능     왼쪽=4611686018427387903 특성=ORDERED NONNULL
```

```text
좋은 소스                                  나쁜 소스

  int[] / ArrayList / IntStream.range       LinkedList / Stream.iterate
  +----------------------------+            1 -> 2 -> 3 -> 4 -> ...
  | SIZED : 개수를 안다         |            SIZED 가 있어도(LinkedList)
  | SUBSIZED : 조각 크기도 안다  |            자르려면 링크를 따라가야 한다
  +----------------------------+            iterate 는 개수조차 모른다
   인덱스 하나로 반을 가른다                      |
        |                                        v
        v                                  "앞부분을 버퍼에 담아 두고"
  비용 O(1), 크기가 정확히 반                 자르는 수밖에 없다
```

그림 해설 (한 단계씩):

- **`SIZED`·`SUBSIZED` 가 붙은 소스가 좋은 소스**다 — 배열·`ArrayList`·`IntStream.range`.\
  `est=1024`, `왼쪽=512` 로 **정확히 반**을 갈랐다.
- `LinkedList` 는 `SIZED` 가 붙어 있는데도 **`왼쪽=1024`** 다 — 자른 쪽 크기를 제대로 모른다.\
  기본 구현이 **원소를 배치로 퍼 담아** 자르기 때문이다.
- 무한·크기 미상 소스(`iterate`·`generate`·`BufferedReader.lines`)는 `est` 가 `Long.MAX_VALUE` 다.
- `HashSet` 은 `SIZED` 도 `ORDERED` 도 없고 **`DISTINCT`** 만 있다 — 원소가 이미 유일하다는 뜻이다.\
  개수를 모르니 조각 크기가 고르지 않다(재귀 분할에서 1024개가 2048조각이 됐다).

비용 — 이 한 줄이 병렬 성능의 대부분을 정한다.\
**소스를 바꿀 수 있으면 소스를 바꾼다** — `LinkedList` 를 `ArrayList` 로, `iterate` 를 `IntStream.range` 로.

### (2) 측정 — 어디서 값이 나오나

**언제 쓰나** — `.parallel()` 의 이득을 짐작할 때. 짐작하지 말고 이 표를 본다.

**실행 결과** (`Ex.java` — 49-e, JDK 21.0.5, 24코어, 마이크로초 중앙값)

```text
== 1) int[] 합계 — 1000만 개 ==
  Arrays.stream(int[]).sum()         중앙값     4248 us   (최소 4141, 최대 5012)
  Arrays.stream(int[]).parallel().sum() 중앙값      833 us   (최소 546, 최대 971)
  -> 병렬 / 순차 = 5.10 배
== 2) 같은 합계인데 박싱을 거치면 — 1000만 개 ==
  List<Integer> 순차 mapToInt.sum()    중앙값    14014 us   (최소 12775, 최대 15989)
  List<Integer> 병렬 mapToInt.sum()    중앙값     7676 us   (최소 7163, 최대 9291)
  -> 병렬 / 순차 = 1.83 배
== 3) LinkedList — 100만 개 ==
  LinkedList 순차                      중앙값     5477 us   (최소 4620, 최대 5977)
  LinkedList 병렬                      중앙값     8512 us   (최소 6467, 최대 107736)
  -> 병렬 / 순차 = 0.64 배
== 4) 작은 데이터 — 100개 ==
  int[100] 순차                        중앙값        1 us   (최소 1, 최대 3)
  int[100] 병렬                        중앙값      137 us   (최소 131, 최대 331)
  -> 병렬 / 순차 = 0.01 배
== 5) 원소당 일이 무거우면 — 2000개 ==
  무거운 일 순차                           중앙값     4616 us   (최소 4334, 최대 5599)
  무거운 일 병렬                           중앙값      702 us   (최소 524, 최대 853)
  -> 병렬 / 순차 = 6.58 배
== 6) Stream.iterate (분할 불가 소스) — 100만 개 ==
  iterate 순차                         중앙값     6205 us   (최소 5556, 최대 23989)
  iterate 병렬                         중앙값    22008 us   (최소 20001, 최대 23361)
  -> 병렬 / 순차 = 0.28 배
== 7) IntStream.range 대 boxed() ==
  IntStream.range 병렬 sum             중앙값      801 us   (최소 522, 최대 1860)
  range.boxed() 병렬 sum               중앙값    12426 us   (최소 11039, 최대 38064)
  -> boxed 쪽이 15.51 배 걸린다
```

```text
이득이 나는 쪽                              손해가 나는 쪽

  int[] 1000만        5.10 배 빠름           작은 데이터 100개    0.01 배 (100배 느림)
  원소당 일이 무거움   6.58 배 빠름           Stream.iterate      0.28 배
                                            LinkedList          0.64 배
  박싱 리스트 1000만  1.83 배 (이득이 줄었다)
```

그림 해설 (한 단계씩):

- **분할 잘 되는 소스 + 충분한 데이터**에서만 배수가 난다 — 5.1배.
- **원소당 일이 무거우면** 데이터가 2000개뿐이어도 6.58배가 난다.\
  즉 판단 기준은 "원소 수"가 아니라 **"원소 수 × 원소당 비용"** 이다.
- **작은 데이터는 재앙이다** — 1us 짜리 일이 137us 가 됐다. 나누고 합치는 값이 전부다.
- **박싱이 이득을 깎는다** — 같은 합계인데 `IntStream` 은 801us, `boxed()` 는 12,426us.\
  15배 차이 중 상당 부분은 병렬 여부와 **무관하게 박싱 자체의 값**이다.
- 두 번째 실행에서는 배수가 3.92 / 2.28 / 0.50 / 0.01 / 8.11 / 0.24 / 34.07 로 나왔다.\
  **배수의 자릿수는 안정적이고 소수점은 아니다.**

비용 — 측정 없이는 아무것도 말할 수 없다. 이 표의 값어치는 **"짐작이 자주 틀린다"**는 것이다.

### (3) 공용 ForkJoinPool 을 모두가 공유한다

**언제 쓰나** — 서버 코드에 `.parallel()` 을 넣을 때. **이것이 가장 자주 사고가 나는 자리다.**

**실행 결과** (`Ex.java` — 49-d, 24코어)

```text
availableProcessors    : 24
commonPool parallelism : 23
공용 풀 객체           : java.util.concurrent.ForkJoinPool@5cad8086[Running, parallelism = 23, size = 0, active = 0, running = 0, steals = 0, tasks = 0, submissions = 0]
== 누가 실행하나 ==
순차 : [main]
병렬 : 스레드 17개
       [ForkJoinPool.commonPool-worker-1, ForkJoinPool.commonPool-worker-10, ForkJoinPool.commonPool-worker-11, ForkJoinPool.commonPool-worker-15, ForkJoinPool.commonPool-worker-16, ForkJoinPool.commonPool-worker-17, ForkJoinPool.commonPool-worker-18, ForkJoinPool.commonPool-worker-19, ForkJoinPool.commonPool-worker-2, ForkJoinPool.commonPool-worker-21, ForkJoinPool.commonPool-worker-3, ForkJoinPool.commonPool-worker-4, ForkJoinPool.commonPool-worker-5, ForkJoinPool.commonPool-worker-6, ForkJoinPool.commonPool-worker-7, ForkJoinPool.commonPool-worker-8, main]
== 두 병렬 스트림이 같은 풀을 쓴다 ==
풀이 붐빌 때 24칸 작업: 402 ms
풀이 한가할 때 같은 작업: 154 ms
== 내 풀에서 돌리면 그 풀의 스레드가 쓰인다 ==
전용 풀(3) : [ForkJoinPool-1-worker-1, ForkJoinPool-1-worker-2]
```

```text
공용 풀이 한가할 때                         다른 스레드가 공용 풀을 쓰는 중일 때

  내 작업 24칸                               남의 작업 40칸이 풀을 차지
  +---+---+---+ ... +---+                    +---+---+ ... +---+
  |24명의 작업자가 한 번에|                    | 내 24칸이 순서를 기다린다 |
  +---+---+---+ ... +---+                    +---+---+ ... +---+
        |                                            |
        v                                            v
      154 ms                                       402 ms
                                             같은 코드, 2.6배
```

그림 해설 (한 단계씩):

- **병렬도는 `availableProcessors - 1`** 이다(24코어 → 23). 나머지 한 자리는 **호출한 스레드**가 채운다.\
  실측에서 `main` 이 워커 목록에 들어 있는 것이 그 증거다.
- 같은 코드가 **풀 상태에 따라 2.6배 느려졌다.** 내 코드는 그대로인데.
- **이것이 서버에서 위험한 이유**다 — 요청 A 의 `.parallel()` 이 요청 B 의 `.parallel()` 을 느리게 만든다.\
  그리고 장애가 나도 **내 코드에는 범인이 없다.**
- 전용 풀을 쓰면 그 풀의 스레드가 쓰인다(`ForkJoinPool-1-worker-N`).\
  `new ForkJoinPool(3).submit(() -> stream.parallel()...).get()` 형태다.\
  다만 이것은 **공식 API 로 보장된 동작이 아니다**(「구현 세부사항」 절).
- `forEachOrdered` 의 액션도 워커 스레드에서 돌 수 있다 — 실측에서 1~2개 스레드, `main` 일 때도 있었다.\
  javadoc 도 "the action may be performed in whatever thread the library chooses" 라고 적는다.

비용 — 공유 자원이다. **블로킹 I/O 를 병렬 스트림 안에서 하지 않는다** — 풀 전체가 막힌다.

### (4) `ArrayList` 에 `forEach` 로 `add` 하면 깨진다

**언제 쓰나** — 병렬 스트림에서 결과를 모을 때. **이 주제의 대표 사고다.**

**실행 결과** (`Ex.java` — 49-b, 원소 10만 개, 10회 반복)

```text
== ArrayList 에 forEach 로 add (10회) ==
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

```text
ArrayList.add 는 원자적이지 않다

  add(x) 가 실제로 하는 일:
     1. size 를 읽는다            <- 여기서 스레드 A 와 B 가 같은 값을 읽으면
     2. elementData[size] = x        둘이 같은 칸에 쓴다 (하나가 사라진다)
     3. size = size + 1              둘 다 +1 하면 size 가 실제보다 크다
                                      -> 안 채운 칸이 null 로 남는다
     그리고 배열이 꽉 차면 grow() 로 새 배열을 만드는데
     그 와중에 다른 스레드가 옛 배열 인덱스로 쓰면
       -> ArrayIndexOutOfBoundsException
```

그림 해설 (한 단계씩):

- **세 가지 실패 모드가 섞여 나온다.**
  1. **원소 유실** — 10만 개가 6,762~17,692개로 줄었다.
  2. **`null` 구멍** — 크기 칸에 아무도 안 쓴 자리가 남는다.
  3. **`ArrayIndexOutOfBoundsException`** — 10회 중 4회.
- **가장 나쁜 것이 1·2번**이다. **예외 없이 결과가 나온다.**\
  10만 건을 넣었는데 8,939건이 나왔고 아무도 안 죽었다.
- 순차로 돌리면 **완벽히 정상**이다(10만). 그래서 개발·테스트에서 안 잡힌다.
- 예외가 날 때의 스택트레이스가 원인을 정확히 가리킨다(`Ex.java` — 49-c).

```text
Caused by: java.lang.ArrayIndexOutOfBoundsException: Index 9686 out of bounds for length 9369
	at java.base/java.util.ArrayList.add(ArrayList.java:484)
	at java.base/java.util.ArrayList.add(ArrayList.java:496)
	at java.base/java.util.stream.ForEachOps$ForEachOp$OfRef.accept(ForEachOps.java:184)
```

**고치는 법**

**실행 결과** (`Ex.java` — 49-b)

```text
  collect(toList())            : 크기 100000
  toList()                     : 크기 100000
  synchronizedList + forEach   : 크기 100000 (순서는 깨진다: 앞 5개 [66406, 66407, 66408, 66409, 66410])
  CopyOnWriteArrayList(2000개) : 크기 2000
```

- **`collect` 를 쓴다.** 스트림이 조각마다 리스트를 만들고 안전하게 합친다.
- `synchronizedList` 는 개수는 맞지만 **순서가 깨진다**(앞 5개가 66406부터다). 그리고 락 경합으로 느리다.
- `CopyOnWriteArrayList` 는 안전하지만 add 마다 배열을 복사한다 — 10만 개는 사실상 불가능해 2000개로 줄여 확인했다.

javadoc 이 이 규칙을 못박는다.

> If the behavioral parameters do have side-effects, unless explicitly stated, there are no guarantees as to: the *visibility* of those side-effects to other threads; that different operations on the "same" element within the same stream pipeline are executed in the same thread; and **that behavioral parameters are always invoked**, ...

비용 — `collect` 쪽이 더 빠르고 더 안전하다. **`forEach` + 공유 컬렉션은 아무 장점이 없다.**

### (5) 결합 법칙과 항등원 — 순차에서는 안 보인다

**언제 쓰나** — `reduce` 를 쓸 때. 특히 나중에 `.parallel()` 을 붙일 가능성이 있을 때.

**실행 결과** (`Ex.java` — 49-f, 입력 1~10)

```text
== 결합 법칙이 없는 reduce ==
뺄셈 순차 : -55
뺄셈 병렬 : -5
뺄셈 병렬 : -5
뺄셈 병렬 : -5
== 항등원이 아닌 씨앗 ==
합 순차(씨앗 100) : 155
합 병렬(씨앗 100) : 1055
```

```text
reduce(0, (a,b) -> a - b)   에서  [1..10]

순차                                       병렬 (조각 셋으로 나뉘었다 치면)

  ((((0-1)-2)-3)...-10)                    조각1: 0-1-2-3      = -6
        = -55                              조각2: 0-4-5-6      = -15
                                           조각3: 0-7-8-9-10   = -34
                                              합치기: -6-(-15)-(-34) = ...
                                                = -5   <- 조각 수에 따라 달라진다
```

```text
reduce(100, Integer::sum)   에서  [1..10]

순차                                       병렬
  100 + 1 + 2 + ... + 10 = 155              조각마다 100 을 씨앗으로 쓴다
                                            조각이 10개면 100 이 10번 더해진다
                                              = 1000 + 55 = 1055
```

그림 해설 (한 단계씩):

- **순차에서는 둘 다 "맞는 답"처럼 보인다.** `-55` 도 `155` 도 의도한 값이다.
- 병렬로 바꾸는 순간 답이 바뀐다. **컴파일 에러도 런타임 예외도 없다.**
- javadoc 이 두 요구를 명시한다.

> More formally, the `identity` value must be an *identity* for the combiner function. This means that for all `u`, `combiner.apply(identity, u)` is equal to `u`. Additionally, the `combiner` function must be **associative** ...

- `combiner.apply(100, u)` 는 `u` 가 아니다 → 항등원이 아니다.\
  `(a-b)-c` 는 `a-(b-c)` 가 아니다 → 결합 법칙이 없다.
- 뺄셈 병렬 결과가 **5회 모두 `-5`** 로 같았다는 점도 함정이다 — "재현되니 맞는 값"으로 읽힌다.\
  조각 수가 달라지면 값도 달라진다.

비용 — 없다. **그래서 위험하다.** 씨앗은 항등원이어야 하고 연산은 결합 법칙을 만족해야 한다.

### (6) 순서를 지키는 데 드는 값

**언제 쓰나** — `limit`·`skip`·`distinct`·`sorted`·`findFirst`·`forEachOrdered` 를 병렬에 섞을 때.

**실행 결과** (`Ex.java` — 49-h, 1000만 개 `int[]`, 마이크로초 중앙값)

```text
== 순서를 지키는 값이 얼마인가 ==
  병렬 filter.count (순서 무관)                     1532
  병렬 filter.limit(1000).sum                   8317
  병렬 unordered.filter.limit(1000).sum         1109
  병렬 skip(9_000_000).sum                       421
  순차 skip(9_000_000).sum                     23193
== distinct — 순서를 지키느라 병렬이 손해다 (1000만 개) ==
  순차 distinct.count                         420446
  병렬 distinct.count                        1461811
  병렬 unordered.distinct.count               805927
== forEach 대 forEachOrdered (LongAdder 로 경쟁 제거, 1000만 개) ==
  병렬 forEach                                  8472
  병렬 forEachOrdered                         125047
  순차 forEach                                 116889
```

```text
순서를 지킬 때                              순서를 버릴 때 (.unordered())

  limit(1000)                                limit(1000)
  "앞에서부터 정확히 1000개"                   "아무 1000개"
  조각마다 몇 번째인지 세야 한다                 먼저 채운 조각이 이기면 된다
        |                                            |
        v                                            v
      8317 us                                     1109 us
                                                  7.5배 싸다
```

그림 해설 (한 단계씩):

- **`limit` 은 병렬에서 비싸다.** `.unordered()` 를 앞에 두면 7.5배 싸진다.
- **`distinct()` 는 병렬이 순차보다 3.5배 느렸다**(1.46s 대 0.42s).\
  입력 순서를 지키면서 중복을 없애려면 조정 비용이 크기 때문이다.\
  `.unordered()` 를 주면 0.81s 로 줄지만 **여전히 순차보다 느리다.**
- **`forEachOrdered` 는 병렬의 이득을 전부 반납한다** — 125ms 로 순차(117ms)와 거의 같다.
- 반대로 **`skip` 은 병렬이 압도적이다**(421us 대 23,193us). `SIZED` 소스라 건너뛸 자리를 계산으로 찾기 때문이다.
- `findFirst` 와 `findAny` 도 갈린다.

**실행 결과** (`Ex.java` — 49-g, 0~999 중 `i % 7 == 3`, 5회)

```text
  findFirst 3  /  findAny 668
  findFirst 3  /  findAny 668
  findFirst 3  /  findAny 668
```

- `findFirst` 는 병렬에서도 **반드시 3** 이다(가장 앞). 그래서 조정 비용을 낸다.
- `findAny` 는 **먼저 찾은 조각의 답**을 준다 — 실측에서 668이었다.\
  순차에서는 `findAny` 도 언제나 3이다. **차이가 병렬에서만 드러난다.**

비용 — 정리하면 이렇다.

| 연산 | 병렬에서 |
|---|---|
| `filter`·`map`·`sum`·`count` | **이득** — 순서와 무관하다 |
| `skip` (SIZED 소스) | **큰 이득** |
| `sorted` | 이득 (실측: 역순 100만 개에서 17,715 → 9,934us) |
| `limit` | **손해** — `.unordered()` 로 줄일 수 있다 |
| `distinct` | **큰 손해** — 순차보다 느렸다 |
| `findFirst` | `findAny` 보다 비싸다 |
| `forEachOrdered` | **이득이 사라진다** — 순차와 같아진다 |

### (7) 수집기가 병렬에서 어떻게 도나

**언제 쓰나** — 병렬 스트림에 `collect` 를 붙일 때.

**실행 결과** (`Ex.java` — 49-f)

```text
== 수집기의 특성 ==
toList()            : [IDENTITY_FINISH]
toSet()             : [UNORDERED, IDENTITY_FINISH]
toMap()             : [IDENTITY_FINISH]
groupingBy()        : [IDENTITY_FINISH]
groupingByConcurrent: [CONCURRENT, UNORDERED, IDENTITY_FINISH]
joining()           : []
counting()          : []
== toMap 은 병렬에서도 결과가 같다 ==
순차 크기 200000 / 병렬 크기 200000 / 같은가 true
병렬 결과 맵 타입 : java.util.HashMap
== groupingBy vs groupingByConcurrent ==
groupingBy 병렬       : {blue=[lee, jung], green=[choi], red=[kim, park]}
groupingByConcurrent  : {blue=[jung, lee], green=[choi], red=[park, kim]} / 타입 ConcurrentHashMap
```

```text
CONCURRENT 가 아닌 수집기 (toMap·groupingBy)   CONCURRENT 수집기 (groupingByConcurrent)

  조각1 -> HashMap A                           조각1 ---+
  조각2 -> HashMap B                           조각2 ---+--> ConcurrentHashMap 하나
  조각3 -> HashMap C                           조각3 ---+     (동시에 쓴다)
        |                                            |
   A + B + C 를 합친다                          합칠 것이 없다
   (키마다 merge — javadoc 이                        |
    "can be an expensive operation")                v
        |                                     그룹 안의 순서를 잃는다
        v
  그룹 안의 입력 순서가 유지된다
```

그림 해설 (한 단계씩):

- **`toMap`·`groupingBy` 는 `CONCURRENT` 가 아니다.** 조각마다 맵을 만들어 나중에 합친다.
- 그래서 **결과는 순차와 같다** — 20만 개로 확인했다(`같은가 true`).
- 대신 **합치는 값이 든다.** javadoc 이 명시한다.

> The returned `Collector` is **not concurrent**. For parallel stream pipelines, the `combiner` function operates by merging the keys from one map into another, which **can be an expensive operation**.

- `groupingByConcurrent` 는 맵 하나를 여러 스레드가 동시에 쓴다. 합칠 게 없다.\
  대신 **그룹 안의 순서를 잃는다** — 위 실측에서 `[lee, jung]` 이 `[jung, lee]` 가 됐다.\
  이 순서는 **실행마다 다르다**(40개짜리로 5회 반복해 확인했다 — 3-answer 10번).

**병렬에서 `toMap` 의 중복 키 예외는 실행마다 다르다**

**실행 결과** (`Ex.java` — 49-f, 같은 코드 5회, JDK 21.0.5)

```text
예외 : java.lang.IllegalStateException: java.lang.IllegalStateException: Duplicate key 5 (attempted merging values 165625 and 165635)
예외 : java.lang.IllegalStateException: java.lang.IllegalStateException: Duplicate key 5 (attempted merging values 65625 and 65635)
예외 : java.lang.IllegalStateException: java.lang.IllegalStateException: Duplicate key 2 (attempted merging values 182812 and 182822)
예외 : java.lang.IllegalStateException: java.lang.IllegalStateException: Duplicate key 2 (attempted merging values 57812 and 57822)
예외 : java.lang.IllegalStateException: java.lang.IllegalStateException: Duplicate key 5 (attempted merging values 65625 and 65635)
```

- **어느 키가 겹쳤다고 나오는지가 실행마다 다르다.** 값도 다르다.
- 그리고 예외가 **한 번 더 감싸져 있다**(`IllegalStateException: java.lang.IllegalStateException: ...`).\
  조각 안에서 난 예외(accumulator)인지 합치다 난 예외(merger)인지에 따라 갈린다.\
  17·25 에서도 **같은 코드가 실행마다 감싸지기도 하고 안 감싸지기도 했다.**
- 즉 **순차에서 나던 진단 가능한 메시지가 병렬에서는 진단이 안 된다.**

비용 — 병렬에서 `collect` 를 쓸 거면 **`CONCURRENT` 수집기를 고려**하되, 순서를 잃는 것을 받아들일 수 있을 때만.

## 문법 — 형태와 규칙

직접 쓴 최소 예제다. 출력은 전부 실행 결과다.

### 병렬로 만드는 두 가지

```java
list.parallelStream()                  // 컬렉션에서 바로
IntStream.range(0, n).parallel()       // 이미 만든 스트림을 병렬로
stream.sequential()                    // 되돌리기
stream.isParallel()                    // 확인
```

### 병렬 플래그는 파이프라인 **전체**에 걸린다

**실행 결과** (`Ex.java` — 49-g)

```text
  중간에 parallel() : true
  parallel 뒤 sequential() : false
  parallel() 을 맨 뒤에 붙여도 앞 연산의 스레드 수 : 24
```

```java
IntStream.range(0, 2000)
         .map(i -> { 스레드이름기록(); return i; })   // 이 map 도 병렬로 돈다
         .parallel()                                  // 뒤에 붙였는데도
         .sum();
```

- **어디에 붙이든 파이프라인 전체가 병렬**이 된다. "여기부터 병렬"이 아니다.
- 마지막으로 부른 것이 이긴다 — `parallel()` 뒤에 `sequential()` 을 부르면 순차다.
- 그래서 **`.parallel()` 을 중간에 숨겨 두면 앞쪽 연산까지 스레드 안전성을 요구받는다.**

### 공용 풀 크기 바꾸기

```text
-Djava.util.concurrent.ForkJoinPool.common.parallelism=4
```

- **JVM 전역**이다. 라이브러리와 내 코드가 같이 영향을 받는다.
- 실측: 기본값은 `availableProcessors - 1`(24코어 → 23).

### 전용 풀에서 돌리기

```java
ForkJoinPool mine = new ForkJoinPool(3);
Set<String> r = mine.submit(() -> stream.parallel().collect(...)).get();
mine.shutdown();
```

**실행 결과** (`Ex.java` — 49-d)

```text
전용 풀(3) : [ForkJoinPool-1-worker-1, ForkJoinPool-1-worker-2]
```

- **워커 이름이 `ForkJoinPool-1-worker-N` 으로 바뀌었다** — 공용 풀을 안 썼다는 증거다.
- 다만 이 동작은 **javadoc 에 계약으로 적혀 있지 않다.** 구현에 기댄 관용구다.

## 어디서 틀리나

### 1. "느리니까 `.parallel()` 을 붙여 본다"

- (2)에서 본 대로 **더 느려지는 경우가 더 흔하다.**
- 100개 데이터에서 **137배 느려졌다.** 손해가 이득보다 극적이다.
- 방어: **붙이기 전에 재고 붙인 뒤에 잰다.** 재지 않았으면 붙이지 않는다.

### 2. 서버 코드에 `.parallel()` 을 넣는다

- (3)에서 본 대로 **공용 풀을 전 애플리케이션이 공유**한다.
- 요청 하나의 `.parallel()` 이 다른 요청을 느리게 만들고, 장애 원인이 내 코드에서 안 보인다.
- **블로킹 I/O(DB·HTTP)를 병렬 스트림 안에서 하면 풀이 통째로 막힌다.**
- 방어: 서버에서는 **`ExecutorService` 를 명시적으로 쓴다**([**54번 주제**](../54-executorservice-and-future/)).\
  병렬 스트림은 **배치·CLI·계산 작업**에 맞는 도구다.

### 3. `forEach` 로 공유 컬렉션에 담는다

- (4)에서 본 대로 **예외 없이 데이터가 사라진다.**
- 순차에서는 완벽히 동작한다. **테스트가 못 잡는다.**
- 방어: **`collect` 를 쓴다.** `forEach` 안에서 바깥 상태를 바꾸지 않는다.

### 4. `reduce` 의 씨앗을 초기값처럼 쓴다

```java
list.stream().reduce(100, Integer::sum);     // 순차 155, 병렬 1055
```

- (5)에서 본 대로 **조각마다 씨앗이 들어간다.**
- 방어: 씨앗은 **항등원만.** 초기값이 필요하면 `reduce` 결과에 나중에 더한다.

### 5. 결합 법칙 없는 연산을 `reduce` 에 넣는다

```java
list.stream().reduce(0, (a, b) -> a - b);            // 병렬에서 답이 바뀐다
list.stream().reduce("", (a, b) -> a + b.charAt(0)); // 타입이 달라 컴파일은 되지만 위험하다
```

- 뺄셈·나눗셈·문자열 누적(순서 의존) 전부 해당한다.
- 방어: **덧셈·최대·최소·집합 합집합처럼 결합 법칙이 있는 연산만** 쓴다.\
  나머지는 `collect` 로 모아서 나중에 처리한다.

### 6. `findAny` 가 항상 첫 원소라고 안다

- 순차에서는 **항상 첫 원소**다. 그래서 그렇게 배운다.
- 병렬에서는 다르다 — 실측에서 `findFirst` 가 3, `findAny` 가 668이었다.
- 방어: **첫 원소가 필요하면 `findFirst`.** 아무거나 되면 `findAny` 가 싸다.

### 7. `Stream.iterate` 를 병렬로 돌린다

- (1)·(2)에서 본 대로 **분할이 안 되는 소스**다. 실측 0.28배(3.5배 느림).
- 방어: **소스를 바꾼다.** 수열이 필요하면 `IntStream.range(...).map(...)`.

### 8. `LinkedList`·`BufferedReader.lines` 를 병렬로 돌린다

- `LinkedList` 는 실측 0.64배였다. `Spliterator` 가 배치로 퍼 담아야 자를 수 있다.
- 방어: **`ArrayList` 로 바꾼 뒤** 병렬로 돌린다. 복사 비용이 분할 비용보다 싸다.

### 9. 병렬에서 난 예외 메시지로 진단하려 한다

- (7)에서 본 대로 **실행마다 다른 키·값이 나오고 감싸지기도 한다.**
- 방어: 병렬에서 터지면 **순차로 재현**해서 진단한다.

### 10. 측정값을 단언한다

- 이 문서의 수치도 **JMH 가 아니고, 이 머신(24코어) 것이고, 실행마다 흔들린다.**
- 두 번 돌렸더니 `5.10 → 3.92`, `15.51 → 34.07` 로 바뀌었다.
- 방어: **"몇 배"를 말할 때는 어느 머신·어느 방법인지 같이 적는다.** 안 적을 거면 말하지 않는다.

## 구현 세부사항 대 언어 보장

| 관측한 것 | 보장인가 | 근거 |
|---|---|---|
| 병렬 `forEach` 의 순서 | **보장 없음(명시적 비결정)** | `forEach` javadoc |
| `forEachOrdered` 가 입력 순서 | **보장** | `forEachOrdered` javadoc |
| `findFirst` 가 병렬에서도 첫 원소 | **보장** | `findFirst` javadoc |
| `findAny` 가 어느 원소 | **보장 없음** | `findAny` javadoc |
| `reduce` 가 결합 법칙·항등원을 요구 | **보장(요구사항)** | 패키지 javadoc |
| 그것을 어겼을 때 **어떤 답**이 나오나 | **보장 없음** | 조각 수에 달려 있다 |
| `toMap`·`groupingBy` 가 `CONCURRENT` 가 아님 | **`@implNote`** — 구현 노트지 계약은 아니다 | `Collectors` javadoc |
| 병렬 `toMap` 의 결과가 순차와 같음 | **사실상 보장** — 수집기의 결합자 계약 | 실측 20만 건 일치 |
| 병렬 `toMap` 중복 키 예외의 메시지·감싸짐 | **보장 없음** | 실행마다 달랐다 |
| 공용 풀 병렬도 = `availableProcessors - 1` | **보장 아님** | `ForkJoinPool.commonPool()` 의 구현 |
| 전용 `ForkJoinPool.submit` 안에서 그 풀이 쓰임 | **보장 아님** | javadoc 에 그런 계약이 없다 |
| `Spliterator` 의 `estimateSize`·분할 결과 | **보장 아님** | `Spliterator` javadoc 이 추정치라고 적는다 |

**세 JDK 실측 — 한 곳에서 갈렸다**

크기를 모르는 소스(`Stream.iterate`·`BufferedReader.lines`)를 `trySplit` 했을 때\
**잘라 낸 쪽의 `estimateSize` 가 버전마다 달랐다.**

```text
                        JDK 17.0.13        JDK 21.0.5 / 25.0.1
  Stream.iterate 2인자    왼쪽 = 1024        왼쪽 = 4611686018427387903
  Stream.iterate 3인자    왼쪽 = 1023        왼쪽 = 4611686018427387903
  BufferedReader.lines   왼쪽 = 3           왼쪽 = 4611686018427387903
```

- 17 은 **실제로 퍼 담은 개수**를 돌려줬고, 21·25 는 **`Long.MAX_VALUE / 2`** 를 돌려줬다.
- 나머지(`ArrayList`·`HashSet`·배열·`IntStream.range`)와 재귀 분할 조각 수는 **세 버전이 같았다.**
- 수집기 특성(`characteristics()`)도 세 버전이 같았다.
- 교훈: **`estimateSize` 는 추정치다.** 그 값으로 분기하는 코드를 쓰지 않는다.

## 언제 쓰고 언제 안 쓰나

| 상황 | 병렬을 쓰나 |
|---|---|
| `int[]`·`ArrayList`·`IntStream.range` + 원소 수만 이상 | **쓴다** — 실측 5배 |
| 원소당 계산이 무거움 (암복호화·이미지·파싱) | **쓴다** — 2000개에서도 6.5배 |
| 원소 수천 개 이하이고 원소당 일이 가벼움 | **안 쓴다** — 100개에서 137배 손해 |
| `LinkedList`·`Stream.iterate`·`BufferedReader.lines` | **안 쓴다** — 분할이 안 된다 |
| 파이프라인에 `limit`·`distinct`·`forEachOrdered` | **안 쓴다** — 순서 비용이 이득을 먹는다 |
| `sorted`·`skip` 이 있음 | 써도 된다 — 실측에서 이득이었다 |
| 블로킹 I/O (DB·HTTP) | **절대 안 쓴다** — 공용 풀이 막힌다 |
| 웹 서버의 요청 처리 경로 | **안 쓴다** — `ExecutorService` 를 쓴다(목록의 54번 주제) |
| 배치·CLI·일회성 계산 | 후보다. 단 재고 결정한다 |
| `reduce` 의 연산에 결합 법칙이 없음 | **안 쓴다** — 답이 바뀐다 |
| 람다가 바깥 상태를 고침 | **안 쓴다** — 고쳐서 `collect` 로 |
| 재지 않았음 | **안 쓴다** |

판단 규칙 세 줄.

- **소스가 반으로 갈리는가**를 먼저 본다. 안 갈리면 나머지는 볼 필요도 없다.
- **원소 수 × 원소당 비용**이 판단 기준이다. 원소 수만 보지 않는다.
- **측정하지 않았으면 `.parallel()` 을 붙이지 않는다.** 이 문서의 수치도 이 머신 것이다.

## 핵심 문장

- 병렬의 이득은 **소스의 분할 가능성**이 정한다 — `SIZED`·`SUBSIZED` 가 붙은 배열·`ArrayList` 는 반으로 갈리고, `Stream.iterate`·`LinkedList` 는 안 갈린다(실측 0.28·0.64배).
- **판단 기준은 원소 수가 아니라 원소 수 × 원소당 비용**이다 — 2000개여도 원소당 일이 무거우면 6.58배가 났고, 10만 개여도 가벼우면 손해였다.
- **공용 ForkJoinPool 은 JVM 에 하나뿐**이다 — 풀이 붐빌 때 같은 작업이 154ms 에서 402ms 가 됐다.
- **`forEach` 로 `ArrayList` 에 담으면 깨진다** — 10만 건이 6,762건이 되고 `null` 이 섞이고 10회 중 4회는 예외가 났다. 순차에서는 완벽히 동작한다.
- **순서를 지키는 연산이 이득을 먹는다** — `limit` 7.5배, `distinct` 는 순차보다 3.5배 느렸고, `forEachOrdered` 는 순차와 같아졌다.

## 관련 자료

- [`../46-terminal-operations/`](../46-terminal-operations/) — **이 주제의 선행.** `forEach`/`forEachOrdered`, 단락 평가, `reduce` 의 항등원
- [`../44-stream-creation/`](../44-stream-creation/) — 소스 팩토리. 분할 가능성은 **소스를 고르는 순간** 정해진다
- [`../47-collectors-basics/`](../47-collectors-basics/) — `toMap` 의 예외가 순차에서 어떻게 나오나(여기서는 그 메시지가 진단이 안 된다)
- [`../48-collectors-grouping/`](../48-collectors-grouping/) — `groupingBy` 대 `groupingByConcurrent` 의 결과 모양
- [`../../언어-특성/README.md`](../../언어-특성/README.md) — JIT·GC·메모리 모델. 그쪽은 **런타임이 무엇을 하나**까지, 여기는 **API 를 언제 쓰나**부터
- [`../../../../process-thread/`](../../../../process-thread/) — 스레드·경쟁 조건의 개념은 거기가 정본. 그쪽은 **왜 경쟁이 나나**까지, 여기는 **스트림에서 어떻게 드러나나**부터
- [`../../../../../data-structure/01-dynamic-array/`](../../../../../data-structure/01-dynamic-array/) — `ArrayList` 가 배열이라 반으로 갈리는 이유
- [`../../../../../data-structure/02-linked-list/`](../../../../../data-structure/02-linked-list/) — `LinkedList` 가 안 갈리는 이유
- [`../README.md`](../README.md) — Java 문법·API 주제 목록(이 주제는 49번)
- [**54번 주제**](../54-executorservice-and-future/)(`ExecutorService`) — 서버에서 병렬 스트림 대신 쓸 것
- [**55번 주제**](../55-atomics-and-concurrent-collections/)(원자 변수·동시 컬렉션) — `LongAdder`·`ConcurrentHashMap`
- [**33번 주제**](../33-synchronized-and-volatile/)(`synchronized`·`volatile`) — 공유 상태의 가시성
- [**01번 주제**](../01-primitives-and-wrappers/)(기본형과 래퍼) — 박싱이 병렬 이득을 깎는 이유

## 용어 풀이

- **`Spliterator`** — 쪼갤 수 있는 반복자. 원소를 하나씩 주는 것과 자신을 둘로 가르는 것(`trySplit`)을 둘 다 한다.
- **`SIZED` / `SUBSIZED`** — 개수를 안다 / 잘라 낸 조각의 개수도 안다. 둘 다 있어야 분할이 싸다.
- **`ORDERED`** — 입력 순서가 정의돼 있다. `List`·배열에는 있고 `HashSet` 에는 없다.
- **공용 ForkJoinPool(common pool)** — JVM 에 하나뿐인 기본 작업자 풀. 병렬 스트림이 기본으로 쓴다.
- **병렬도(parallelism)** — 풀이 동시에 돌리는 작업자 수. 실측 기본값은 `availableProcessors - 1`.
- **작업 훔치기(work stealing)** — 일이 없는 작업자가 다른 작업자의 큐에서 일을 가져오는 것. ForkJoinPool 의 방식.
- **결합 법칙(associativity)** — `(a op b) op c == a op (b op c)`. 병렬 `reduce` 가 요구한다.
- **항등원(identity)** — `combiner.apply(identity, u) == u` 인 값. `reduce` 의 씨앗이 이것이어야 한다.
- **경쟁 조건(race condition)** — 두 스레드의 실행 순서에 따라 결과가 달라지는 것. `ArrayList.add` 가 그것이다.
- **결합자(combiner)** — 조각별 결과를 합치는 함수. 병렬에서만 불린다.
- **`CONCURRENT` 수집기** — 여러 스레드가 결과 컨테이너 하나에 동시에 쓸 수 있는 수집기. `groupingByConcurrent` 등.
- **`unordered()`** — 입력 순서를 안 지켜도 된다고 알려 주는 중간 연산. `limit`·`distinct` 의 병렬 비용을 줄인다.

## 더 들어가면

- **`.parallel()` 은 요청이지 명령이 아니다.**\
  구현이 조각 수를 정하고, 코어가 하나면 사실상 순차로 돈다.\
  그래서 "몇 개로 쪼개졌나"에 기대는 코드를 쓸 수 없다 — (5)의 `reduce` 가 실행마다 다른 답을 낼 수 있는 이유다.
- **재귀 분할이 몇 조각까지 가는지 실측했다**(원소 1024개, 세 JDK 동일).

  ```text
  ArrayList  : 1024 조각
  LinkedList : 1025 조각
  HashSet    : 2048 조각
  ```

  조각 수 자체는 실제 병렬 실행에서 쓰는 숫자가 아니다(실행은 병렬도를 보고 멈춘다).\
  다만 **`HashSet` 이 균등하게 안 갈린다**는 것과 **`LinkedList` 가 결국 원소 단위까지 간다**는 것을 보여 준다.
- **`Collectors.toConcurrentMap`** 이 `toMap` 의 `CONCURRENT` 판이다.\
  javadoc 이 `toMap` 의 `@implNote` 에서 직접 가리킨다 — "If it is not required that results are inserted into the `Map` in encounter order, using `toConcurrentMap` may offer better parallel performance."
- **`LongAdder`(55번 주제)는 병렬 누적의 정석이다.**\
  (6)의 측정에서 `int[]` 한 칸에 `+=` 를 했을 때는 병렬 `forEach` 가 156ms 였는데,\
  `LongAdder` 로 바꾸자 8.5ms 가 됐다 — **18배**. 같은 병렬 코드인데 경쟁만 없앤 것이다.\
  (그 `+=` 는 **답도 틀린다** — 원자적이지 않다.)
- **가상 스레드(21+)는 이 문제를 풀지 않는다.**\
  병렬 스트림은 CPU 바운드 작업을 코어 수만큼 나누는 도구이고, 가상 스레드는 블로킹 I/O 를 싸게 기다리는 도구다.\
  목적이 다르다 — [**56번 주제**](../56-virtual-threads/).
