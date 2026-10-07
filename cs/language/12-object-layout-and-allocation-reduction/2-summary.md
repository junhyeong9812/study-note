# language/12-object-layout-and-allocation-reduction — 객체 레이아웃과 할당 줄이기: 헤더·압축 참조·박싱·탈출 분석·풀링 — 정리 (힌트)

## 해결하는 문제

JVM에서 `long` 하나는 8바이트지만, `Long` 하나를 리스트에 넣으면 그보다 훨씬 많이 든다. 그리고 객체를 많이 만들수록 GC가 자주 돈다.

```text
  long[] 1천만 개          →  약 80MB
  List<Long> 1천만 개      →  약 281MB   (아래 실험 2, 3.5배)
  요청마다 작은 객체 수십 개 →  초당 GB 단위 할당 → Young GC가 잦아지고 p99가 튄다
```

- 이 노트는 두 질문을 다룬다.
  - 객체 하나가 메모리에서 실제로 몇 바이트인가(헤더·참조·패딩).
  - 할당 자체를 어떻게 줄이나(원시 배열, 탈출 분석, 그리고 하지 말아야 할 객체 풀링).

쉬운 예: 택배 상자다.
- 작은 반지 하나(`long` 8바이트)를 보내는데 상자(헤더), 송장(참조), 완충재(패딩)가 붙으면 부피가 몇 배가 된다.
- 반지 1천 개를 상자 1천 개로 보내지 말고, 칸막이 상자 하나(원시 배열)에 넣으면 된다.
- 상자를 아끼겠다고 헌 상자를 창고에 쌓아 두면(객체 풀링), 창고(Old 영역)가 꽉 차서 대청소(Full GC)를 부른다.

똑같은 구조다.\
실무 예:
- ID 1천만 개를 `Set<Long>`에 올리는 배치가 힙 1GB로 시작했는데 OOM이 난다.
- 요청마다 DTO·`Optional`·람다 캡처 객체를 만드는 서비스의 할당률이 초당 수 GB다.
- "GC를 줄이려고" 도입한 객체 풀 뒤에 Young GC가 20배 길어졌다(아래 실험 4).

## 동작·원리

### 1. 객체 하나의 모양 (HotSpot, 64비트)

```text
  오프셋  0        8        12       16       24  25  26  28       32
         [ mark word 8B ][klass 4B][ int  ][  long 8B ][b ][b][pad][ref 4B ]
          ↑ 해시·락·GC 나이  ↑ 압축 클래스 포인터                          → 객체 크기 32B (8의 배수)

  Long 객체:     [mark 8][klass 4][빈칸 4][value 8]          = 24B
  Integer 객체:  [mark 8][klass 4][value 4]                  = 16B
```

- *객체 헤더*: 모든 객체 앞에 붙는 관리 정보. *mark word*(해시코드·락 상태·GC 나이 등)와 *클래스 포인터*(이 객체의 타입)로 이뤄진다. JOL README의 예시 출력: `0 8 (object header: mark)`, `8 4 (object header: class)`.
- *정렬(alignment)*: 객체 크기를 8바이트 배수로 맞춘다(`ObjectAlignmentInBytes` 기본 8, JDK 21 `PrintFlagsFinal`). 남는 칸이 패딩이다. 정렬·패딩의 일반 원리는 [architecture/06](../../architecture/06-byte-order-and-alignment/2-summary.md).
- `long` 필드는 8바이트 경계에 놓인다. 그래서 `Long`은 헤더(12) 뒤에 4바이트를 비우고 16에서 값이 시작한다(실험 1).
- 필드 배치는 **선언 순서가 아니다.** JVM이 크기·정렬에 맞게 재배치한다(실험 1의 `Order`: 선언은 `paid, amount, qty, status, customer`, 배치는 `qty@12, amount@16, paid@24, status@25, customer@28`). JLS는 필드 배치를 정하지 않으므로 이것은 HotSpot 구현 동작이다.

### 2. 압축 참조 (compressed oops)

```text
  압축 참조 켬(기본):   참조 = 32비트 오프셋 × 8 (정렬)   → 4B, 최대 힙 약 32GB까지
  끔(-XX:-UseCompressedOops):  참조 = 64비트 주소        → 8B
```

- `java` 문서: 압축 참조는 기본으로 켜져 있고, 참조를 64비트 포인터 대신 32비트 오프셋으로 표현한다. 기본으로 덮는 범위는 32GB다.
- 효과는 참조가 많은 구조에서 크다. `Object[]` 한 칸이 4B ↔ 8B, `Order`가 32B ↔ 40B(실험 1·2).
- 힙을 32GB 넘게 잡으면 기본 정렬(8B)로는 압축 참조가 덮지 못한다. `java` 문서: `MaxRAMPercentage` 등으로 정한 최대 힙이 압축 참조 범위를 넘으면 압축 참조 자동 사용이 꺼지고, `-XX:ObjectAlignmentInBytes`를 키우면 범위가 "4GB * ObjectAlignmentInBytes"로 넓어지는 대신 객체 사이 빈칸(패딩)이 늘어난다. 이 노트는 32GB 이상 힙을 실험하지 않았다.

### 실험 1: 필드 오프셋과 인스턴스 크기 (Java 21)

```java
static class Order { boolean paid; long amount; int qty; byte status; Object customer; }
// sun.misc.Unsafe.objectFieldOffset으로 필드별 오프셋, jcmd GC.class_histogram으로 인스턴스 바이트
```

`eclipse-temurin:21-jdk`(21.0.12), `--cpus=2`:

```text
  -XX:+UseCompressedOops (기본)          -XX:-UseCompressedOops
  Layout$Order                          Layout$Order
     12 int      qty                       12 int      qty
     16 long     amount                    16 long     amount
     24 boolean  paid                      24 boolean  paid
     25 byte     status                    25 byte     status
     28 Object   customer                  32 Object   customer
  java.lang.Long:  16 long value         (같음)
  java.lang.Integer: 12 int value        (같음)
  ARRAY_OBJECT_INDEX_SCALE=4             ARRAY_OBJECT_INDEX_SCALE=8
  히스토그램: Order 1000개 32000 바이트    Order 1000개 40000 바이트
```

- 압축 참조를 꺼도 헤더는 12바이트였다(클래스 포인터 압축 `UseCompressedClassPointers`는 별도 옵션이라 켜진 채). 참조 필드만 8바이트가 됐다.
- `-XX:+PrintFieldLayout`은 이 JDK에서 쓸 수 없었다(`notproduct` — 디버그 빌드 전용, OpenJDK `globals.hpp`). JOL도 없는 환경이라 `Unsafe`와 히스토그램으로 대신 확인했다.

### 3. 박싱 — 값 하나에 객체 하나

```text
  long[] (원시 배열)                         List<Long> → ArrayList → Object[] → Long 객체들
  [hdr 16][ 8 ][ 8 ][ 8 ] ...                [hdr][ref4][ref4][ref4] ...
                                                     │     │     │
                                                     ▼     ▼     ▼
                                                   [Long 24B] [Long 24B] [Long 24B]   (힙 곳곳)
  원소당 8B, 연속                             원소당 4B + 24B = 28B, 간접 참조 한 번 더
```

- *박싱(boxing)*: 원시 값(`long`)을 객체(`Long`)로 감싸는 것. 제네릭 컬렉션은 객체만 담으므로 `List<Long>`에 넣을 때 자동으로 일어난다(오토박싱).
- `Long.valueOf`는 -128~127을 항상 캐시한다(Java API 문서 "will always cache values in the range -128 to 127"). 그 밖의 값은 대개 새 객체다. 실험 2는 캐시 밖 값(`i * 1000`)을 썼다.
- 메모리뿐 아니라 접근도 느려진다. 원소마다 포인터를 한 번 더 따라가고, 객체가 흩어져 있으면 캐시 미스가 난다. 그 측정은 [architecture/11 실험 3](../../architecture/11-memory-hierarchy-and-locality/2-summary.md)에 있다.

### 실험 2: `long[]` vs `List<Long>` 1천만 개 (Java 21)

```java
long[] prim = new long[n]; for (...) prim[i] = i * 1_000L;
List<Long> boxed = new ArrayList<>(n); for (...) boxed.add(i * 1_000L);
// System.gc() 3회 뒤 (totalMemory - freeMemory) 차이로 측정, 그리고 jcmd GC.class_histogram
```

`-Xmx1g`, G1, `--cpus=2 --memory=2g`, 2회(같은 값):

```text
                       압축 참조 켬                  압축 참조 끔
  long[]       1천만 개: 80,698,872 B (8.1 B/개)      80,698,912 B (8.1 B/개)
  List<Long>   1천만 개: 281,084,096 B (28.1 B/개)    320,843,336 B (32.1 B/개)
  히스토그램   java.lang.Long 10,000,255개 240,006,120 B (24 B/개)  — 두 경우 같음
               [Ljava.lang.Object;  40,146,216 B                    80,270,160 B
```

- 원소당 28B = `Long` 24B + 참조 4B. 압축 참조를 끄면 참조가 8B라 32B.
- `long[]` 대비 3.5배(켬)·4배(끔). 커리큘럼 ⚠의 "몇 배"는 이 환경에서 3.5~4배였다.
- `Long` 개수가 1천만보다 255개 많은 것은 JDK 안의 다른 `Long`(캐시 등)이 섞인 것이라는 해석이다.

### 4. TLAB — 할당은 원래 싸다

```text
  Eden
  [ 스레드 A의 TLAB ......▲ top        ][ 스레드 B의 TLAB ...▲ top   ][ ... ]
                          └ new = top을 객체 크기만큼 민다 (락 없음)
  TLAB이 차면 새 TLAB을 Eden에서 받는다. Eden이 차면 Young GC.
```

- *TLAB(thread-local allocation buffer)*: Eden을 스레드별 구간으로 나눠 주고, 그 안에서는 포인터만 미는(bump) 할당. 다른 스레드와 경쟁하지 않는다(`UseTLAB` 기본 true). bump 할당 구조는 [data-structure/35-allocator](../../data-structure/35-allocator/2-summary.md), 자바 할당과 `malloc`의 관계는 [os/11 §2 자바](../../os/11-heap-allocation/2-summary.md).
- 그래서 객체 하나 만드는 비용 자체는 작다. 비싼 것은 **할당이 쌓여 Young GC를 부르는 빈도**와, 오래 살아 Old로 승격되는 객체다.
  - 흔한 오해: "new는 비싸니 객체를 재사용해야 한다." 할당은 bump라 싸고, 비용은 수명에서 나온다. 재사용(풀링)은 수명을 늘려 오히려 비싸질 수 있다(5절, 실험 4).

### 5. 탈출 분석과 스칼라 치환

```text
  long noEscape(long i) { Point p = new Point(i, i+1); return p.dist2(); }
                          └ p가 메서드 밖으로 안 나간다 (반환·필드 저장·다른 스레드 전달 없음)
  C2가 하는 일 (스칼라 치환)
     new Point 없앰 →  long px = i, py = i+1;  return px*px + py*py;    ← 객체가 사라지고 지역 변수만 남는다

  long escapes(long i) { Point p = new Point(i, i+1); leaked = p; ... }   ← static 필드로 탈출 → 할당 유지
```

- *탈출 분석(escape analysis)*: 새 객체의 참조가 메서드·스레드 밖으로 나가는지 컴파일러가 따지는 데이터 흐름 분석. 분석 일반은 [22-ir-and-optimization](../22-ir-and-optimization/2-summary.md).
- *스칼라 치환(scalar replacement)*: 탈출하지 않는 객체의 필드를 지역 변수(레지스터)로 바꿔 할당 자체를 없애는 최적화.
  - 흔한 오해: "HotSpot은 객체를 스택에 할당한다." Shipilëv "JVM Anatomy Quark #18": "Hotspot does not do stack allocations per se, but it does approximate that with Scalar Replacement."
- C2(최상위 JIT)가 하는 최적화다. JDK 21 플래그 `DoEscapeAnalysis`·`EliminateAllocations`는 `{C2 product}`로 표시되고 기본 true다. C1만 쓰면(`-XX:TieredStopAtLevel=1`) 일어나지 않았다(실험 3). JIT 단계는 [23-jit-tiered-compilation-and-warmup](../23-jit-tiered-compilation-and-warmup/2-summary.md).
- 깨지기 쉽다. 같은 글: 제어 흐름이 합쳐진 뒤 접근하거나, 인라인되지 않은 메서드를 부르면 탈출로 간주된다. 리팩터링 하나로 할당이 되살아날 수 있다.

### 실험 3: 탈출 분석 on/off — 호출당 할당 바이트 (Java 21)

```java
record Point(long x, long y) { long dist2() { return x * x + y * y; } }
// 1천만 회 호출 × 5라운드, com.sun.management.ThreadMXBean.getThreadAllocatedBytes 차이 / 호출 수
```

`-Xmx256m`, `--cpus=2`, 2회 + 사실 점검 재실행 1회(시간은 3회 범위):

```text
  -XX:+DoEscapeAnalysis (기본)
  round 1  noEscape:   0.04~0.20 B/call  30~36ms | escapes:  32.00 B/call  192~206ms   (워밍업 중)
  round 3  noEscape:   0.00 B/call   20~21ms | escapes:  32.00 B/call   92~98ms
  round 5  noEscape:   0.00 B/call   20~22ms | escapes:  32.00 B/call   82~103ms
  -XX:-DoEscapeAnalysis
  round 3~5 noEscape:  32.00 B/call   68~93ms | escapes:  32.00 B/call   85~304ms
  -XX:TieredStopAtLevel=1 (C1만)
  round 1~5 noEscape:  32.00 B/call   90~265ms
  G1 -Xms256m -Xmx256m, 같은 프로그램 전체의 Young GC 횟수:  탈출 분석 켬 11회(2회 동일) / 끔 21회(2회 동일)
```

- `Point`는 헤더 12 + `long` 2개 → 정렬 포함 32B. 탈출 분석이 켜지면 `noEscape`의 할당이 0이 됐다.
- 할당이 사라진 쪽이 약 3~4.5배 빨랐다(20~22ms vs 68~93ms). 할당이 반으로 줄자 Young GC도 21회 → 11회로 줄었다.
- 원인을 컴파일 로그로 직접 보지는 못했다(`-XX:+PrintEliminateAllocations`는 OpenJDK jdk21u `opto/c2_globals.hpp`에서 `notproduct` — 디버그 빌드 전용). 플래그 on/off 비교와 C1 비교가 근거다. 시간은 이 호스트·`--cpus=2` 한정, 첫 라운드는 워밍업 구간이라 제외하고 읽는다. 첫 라운드 `noEscape`가 이미 0.04~0.20 B/call(32B의 1% 미만)이라, 그 라운드 안에서 대부분의 호출은 벌써 스칼라 치환된 코드로 돌았다는 뜻이다 — 컴파일 시점은 로그 없이 특정하지 못했다.

### 6. 객체 풀링은 왜 GC 언어에서 반패턴이 되나

```text
  새로 만들기                              풀에서 꺼내 재사용
  [Req]→[payload]  요청 끝 → 둘 다 쓰레기     [Req(Old에 산다)]──→[payload(새로 만든 것)]
  Young GC: 산 것이 거의 없다 → 짧다          Young GC: Old의 풀 객체 50만 개가 payload를 붙잡는다
                                              → 50만 개 payload가 "살아 있다" → 복사 → 승격 → Old가 찬다
```

- 풀 객체는 오래 살아 Old에 있다. 요청 데이터는 어차피 새로 만드는데, 그 참조를 Old 객체가 들고 있으면 Young GC 입장에서 **산 객체**다(카드 테이블·기억 집합 경유 — [10 §3](../10-garbage-collection/2-summary.md)).
- 그래서 짧게 살 데이터가 복사되고 승격돼 Old를 오염시킨다. G1 가이드 8장도 Full GC 대책으로 "decreasing the allocation rate in the old generation"을 든다.

### 실험 4: 객체 풀 vs 새로 만들기 (Java 21)

```java
Req r = pooled ? pool[(int) (i % 500_000)] : new Req();   // 풀 50만 개 (미리 만들고 System.gc()로 Old로)
r.payload = new byte[256]; r.meta = new Object(); r.id = i; sink = r;   // 요청 4천만 건
```

G1 `-Xms1g -Xmx1g -Xlog:gc*`, `--cpus=2 --memory=2g`, 2회:

```text
            총 시간         Young GC 횟수  평균        최대        Young 합계    G1 Full GC
  fresh    3,531 / 3,584ms   20 / 20      2.43ms      3.0~3.2ms   49ms          0 / 0
  pooled   8,789 / 9,462ms   68 / 94      44.8~51.4ms 72.9~79.8ms 3,494~4,207ms 1 / 0
  (두 모드 모두 시작 때 System.gc()에 의한 Pause Full 1회는 제외)

  fresh  GC(10) Pause Young (Normal)  631M->18M(1024M)  2.463ms   Old regions: 17->17
  pooled GC(20) Pause Young (Mixed)   803M->785M(1024M) 69.673ms  Old regions: 687->769
```

- 풀을 쓰자 Young GC 평균이 2.4ms → 45~51ms(약 20배), 총 시간이 2.5~2.6배가 됐다. 한 번은 `Pause Full (G1 Compaction Pause) 1023M->155M 112ms`까지 갔다.
- fresh는 Young GC 뒤 힙이 18M로 돌아왔고 Old가 늘지 않았다. pooled는 GC 한 번에 Old가 82개 영역 늘었다. "짧게 살 데이터가 Old로 승격된다"는 위 그림과 맞는다는 해석이다(로그는 영역 수만 보여 주고, Mixed 수집이라 Old 영역 이동도 섞여 있다 — 무엇이 승격됐는지는 힙 덤프·클래스 히스토그램 같은 별도 증거가 필요하다).
- 이 부하 한 가지의 결과다. 풀 객체가 젊은 객체를 가리키지 않는 경우(예: 큰 원시 버퍼를 통째로 재사용)는 다르게 나올 수 있다.

## 쓰이는 자료구조·알고리즘

- **AoS vs SoA** — 객체 배열(Array of Structures: `Order[]`, 원소마다 헤더·참조)과 필드별 원시 배열(Structure of Arrays: `long[] amounts; int[] qtys`). SoA는 원소별 객체 헤더·참조가 없고 연속이다(배열마다 헤더 하나는 남는다). 지역성 측정은 [architecture/11](../../architecture/11-memory-hierarchy-and-locality/2-summary.md).
- **원시형 특화 컬렉션** — `long` 키를 박싱 없이 담는 해시맵·리스트(내부가 `long[]`). 직접 만들면 개방 주소법 해시가 흔하다 — [data-structure/29-open-addressing](../../data-structure/29-open-addressing/2-summary.md), [data-structure/01-dynamic-array](../../data-structure/01-dynamic-array/2-summary.md).
- **탈출 분석 = 데이터 흐름 분석** — 할당 지점에서 참조가 어디로 흘러가는지(반환·필드 저장·호출 인자) 따라가는 정적 분석. 일반론은 [22-ir-and-optimization](../22-ir-and-optimization/2-summary.md).
- **bump pointer 할당(TLAB)** — [data-structure/35-allocator](../../data-structure/35-allocator/2-summary.md).

## 적용 — 풀어나가는 법

### 1. 순서

```text
  1. 무엇이 메모리를 차지하나     jcmd <pid> GC.class_histogram | head   → 인스턴스 수·바이트, [Ljava.lang.Object;·java.lang.Long이 위에 있나
  2. 누가 할당하나               JFR 할당 프로파일(jcmd <pid> JFR.start ...) 또는 async-profiler alloc 모드 (reliability/36)
  3. 할당률이 얼마인가            GC 로그의 GC 사이 증가량 / 시간 (11번 §4)
  4. 고칠 곳을 고른다            상위 몇 개 할당 지점만 (나머지는 bump 할당이라 싸다)
```

### 2. 고치는 순서 — 효과 큰 것부터

| 증상 | 처방 |
|---|---|
| `java.lang.Long`·`Integer`가 히스토그램 상위 | 원시 배열·원시형 특화 컬렉션 |
| `[Ljava.lang.Object;` + 작은 객체 다수 | SoA로 펼치기, 필드 수 줄이기 |
| 요청당 임시 객체 다수(DTO·`Optional`·박싱) | 핫 경로만 원시형으로, 객체를 메서드 밖으로 내보내지 않게(탈출 분석이 지울 수 있게) |
| 큰 버퍼를 요청마다 생성 | humongous면 [11](../11-gc-tuning-and-gc-logs/2-summary.md) 실험 3, 재사용·스트리밍 |
| "GC 줄이려고" 객체 풀 | 측정 후 대개 제거(실험 4). 진짜 비싼 자원(커넥션·스레드)만 풀링 |

### 3. 바꾼 뒤 확인

```java
// 핫 경로 한 구간의 할당 바이트를 직접 잰다 (JMH 없이)
var mx = (com.sun.management.ThreadMXBean) ManagementFactory.getThreadMXBean();
long b0 = mx.getThreadAllocatedBytes(Thread.currentThread().getId());
for (int i = 0; i < N; i++) handle(req);
long perCall = (mx.getThreadAllocatedBytes(Thread.currentThread().getId()) - b0) / N;
```

- 워밍업 라운드를 버리고 여러 라운드를 본다(실험 3의 1라운드는 워밍업 중 — C2 컴파일 전후가 섞인다). 마이크로벤치마크 함정은 [reliability/38-microbenchmarking](../../reliability/38-microbenchmarking/2-summary.md).

## 장애 시나리오와 대처

### 1. ⚠ `List<Long>` 1천만 개 → `long[]`의 몇 배 메모리

- **현상**: ID 목록을 메모리에 올리는 배치가 힙 1GB에서 OOM.
- **보이는 형태**: 히스토그램 상위가 `java.lang.Long`(개당 24B)과 `[Ljava.lang.Object;`. 원소당 28B(실험 2) — `long[]`은 8B.
- **원인**: 원소마다 헤더 12B + 패딩 4B + 값 8B의 `Long`, 그리고 그것을 가리키는 4B 참조.
- **대처**: `long[]`·원시형 특화 컬렉션. 정렬이 필요하면 `long[]` + `Arrays.sort`. 집합 연산이면 비트셋([data-structure/18-bitset](../../data-structure/18-bitset/2-summary.md)).

### 2. ⚠ 초당 GB 단위 할당 → 잦은 Young GC, p99 상승

- **현상**: 트래픽에 비례해 Young GC 빈도가 오르고 p99가 따라 오른다.
- **보이는 형태**: GC 로그에서 할당률 계산(11번 §4: 이 노트의 부하는 약 1.95GB/s). 실험 3에서 탈출 분석을 꺼(`-XX:-DoEscapeAnalysis`) 할당이 약 두 배가 되자 Young GC도 11 → 21회.
- **원인**: 요청마다 임시 객체·박싱·큰 버퍼. 할당 자체는 bump라 싸지만, Eden이 빨리 차 GC가 자주 온다.
- **대처**: 상위 할당 지점만 고친다. 탈출 분석이 지울 수 있게 객체를 메서드 밖으로 안 내보낸다. Young 크기는 수집기에 맡긴다(11번 — `-Xmn` 고정 비권장).

### 3. ⚠ 객체 풀링 → Old 오염, Young GC 급증, Full GC

- **현상**: GC를 줄이려고 요청 객체 풀을 넣었더니 지연이 오히려 커졌다.
- **보이는 형태**: Young GC 평균이 몇 배~수십 배, Young GC마다 Old 영역 증가, `Pause Young (Mixed)`·`Pause Full (G1 Compaction Pause)` 등장(실험 4: 2.4ms → 45~51ms).
- **원인**: Old에 사는 풀 객체가 매 요청 새로 만든 데이터를 가리켜, 짧게 살 데이터를 살려 두고 승격시킨다.
- **대처**: 풀을 걷어 내고 측정으로 확인한다. 풀링은 생성 비용이 진짜 큰 자원(DB 커넥션·스레드)에만. 꼭 재사용해야 하면 다음 요청 전에 참조 필드를 `null`로 비운다(그래도 승격된 풀 자체의 비용은 남는다).

### 4. 탈출 분석이 리팩터링 뒤 깨짐 → 할당이 되살아남

- **현상**: 기능 변경 없는 리팩터링 뒤 할당률과 GC 횟수가 늘었다.
- **원인**: 객체가 새로 만든 헬퍼 메서드로 넘어가는데 그 메서드가 인라인되지 않거나, 분기 뒤 합쳐진 값으로 쓰여 탈출로 판정됐다(Shipilëv Quark #18이 든 깨지는 경우).
- **대처**: 핫 경로는 호출당 할당 바이트(적용 §3)를 회귀 테스트로 둔다. 탈출 여부를 단정하지 말고 `-XX:-DoEscapeAnalysis` 비교로 확인한다.

### 5. 힙 32GB 경계를 넘김 → 같은 데이터가 더 큰 메모리

- **현상**: 힙을 30GB에서 40GB로 늘렸는데 쓸 수 있는 공간이 기대만큼 안 는다.
- **원인(문서 근거 + 미실험)**: 압축 참조의 기본 범위가 32GB라(`java` 문서), 넘기면 참조가 8B가 된다. 참조가 많은 데이터는 실험 1·2처럼 커진다(`Order` 32B → 40B, `Object[]` 칸 4B → 8B).
- **대처**: 32GB 아래로 두고 여러 JVM으로 나누거나, `ObjectAlignmentInBytes`를 16으로 키워 압축 범위를 64GB(4GB × 16)로 넓힌다(`java` 문서). 정렬이 커지면 객체 사이 빈칸도 커지므로 바꾼 뒤 히스토그램으로 다시 잰다.

## 핵심 문장

- HotSpot 객체에는 헤더(압축 클래스 포인터면 12B)가 붙고 8B 단위로 정렬된다. 그래서 `Long`은 24B, `Integer`는 16B다.
- `List<Long>`은 원소당 참조 4B + `Long` 24B = 28B로 `long[]`(8B)의 3.5배였다. 압축 참조를 끄면 4배.
- 할당 자체는 TLAB bump라 싸다. 비용은 할당이 쌓여 부르는 Young GC 빈도와, 오래 살아 승격되는 객체에서 나온다.
- 탈출 분석은 메서드 밖으로 나가지 않는 객체를 스칼라 치환으로 없앤다(스택 할당이 아니다). C2에서만, 그리고 깨지기 쉽게 동작한다.
- 객체 풀링은 짧게 살 데이터를 Old 객체에 매달아 살려 두므로, GC 언어에서는 Young GC를 오히려 길게 만들 수 있다.

## 관련 주제·근거

- 선행
  - [09-memory-management-models](../09-memory-management-models/2-summary.md) · [10-garbage-collection](../10-garbage-collection/2-summary.md)
  - [architecture/11-memory-hierarchy-and-locality](../../architecture/11-memory-hierarchy-and-locality/2-summary.md) · [architecture/06-byte-order-and-alignment](../../architecture/06-byte-order-and-alignment/2-summary.md)
- 후속·연결
  - [11-gc-tuning-and-gc-logs](../11-gc-tuning-and-gc-logs/2-summary.md) — 할당률·승격률 읽기, humongous
  - [22-ir-and-optimization](../22-ir-and-optimization/2-summary.md)(데이터 흐름 분석), [23-jit-tiered-compilation-and-warmup](../23-jit-tiered-compilation-and-warmup/2-summary.md)(C1/C2)
  - [reliability/36-profiling](../../reliability/36-profiling/2-summary.md) · [reliability/38-microbenchmarking](../../reliability/38-microbenchmarking/2-summary.md)
  - [data-structure/01-data-structures-basics](../../data-structure/01-data-structures-basics/2-summary.md) — 고정 배열 + 객체 풀 예와 그 주의
- 문서
  - OpenJDK JOL README — 헤더(mark 8B + class 4B), 필드·배열 크기, 정렬 손실 예시 출력 <https://github.com/openjdk/jol>
  - Shipilëv, "JVM Anatomy Quark #18: Scalar Replacement" — 스택 할당이 아닌 스칼라 치환, EA가 깨지는 경우 <https://shipilev.net/jvm/anatomy-quarks/18-scalar-replacement/>
  - `java` 도구 문서(JDK 21) — `-XX:-UseCompressedOops`(32비트 오프셋, 기본 범위 32GB), `-XX:ObjectAlignmentInBytes` <https://docs.oracle.com/en/java/javase/21/docs/specs/man/java.html>
  - Java API `Long.valueOf(long)` — -128~127 캐시 <https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/Long.html>
  - Oracle GC 튜닝 가이드(JDK 21) 8장 — Full GC 대책 "decreasing the allocation rate in the old generation" <https://docs.oracle.com/en/java/javase/21/gctuning/garbage-first-garbage-collector-tuning.html>
  - OpenJDK jdk21u `src/hotspot/share/runtime/globals.hpp` — `PrintFieldLayout`는 `notproduct`, `src/hotspot/share/opto/c2_globals.hpp` — `DoEscapeAnalysis`·`EliminateAllocations` product 기본 true, `PrintEliminateAllocations` `notproduct`
- 실험(호스트 i7-13700HX, `eclipse-temurin:21-jdk` 21.0.12, `--cpus=2 --network none`)
  - 실험 1: `Unsafe.objectFieldOffset` + `jcmd GC.class_histogram` — `Order`·`Long`·`Integer`, 압축 참조 켬/끔(사실 점검 재실행 동일, `-XX:+PrintFieldLayout`은 "notproduct and is available only in debug version of VM" 오류)
  - 실험 2: `long[]` vs `List<Long>` 1천만 개 — `-Xmx1g` G1, `Runtime` 사용량 차이 + 히스토그램, 압축 참조 켬/끔, 2회
  - 실험 3: 탈출 분석 — `ThreadMXBean.getThreadAllocatedBytes`, `±DoEscapeAnalysis`·`TieredStopAtLevel=1`, 5라운드 × 2회, Young GC 횟수(`-Xms256m -Xmx256m`)
  - 실험 4: 객체 풀(50만) vs 새로 만들기 — 요청 4천만 건, G1 `-Xms1g -Xmx1g -Xlog:gc*`, `--memory=2g`, 2회
