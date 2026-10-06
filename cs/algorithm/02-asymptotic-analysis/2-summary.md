# algorithm/02-asymptotic-analysis — 점근 분석: 빅오·최악/평균·분할상환 — 정리 (힌트)

## 해결하는 문제

"이 코드 빠른가?"에 답하려면 **어떤 n에서, 어떤 입력에서, 한 번인가 여러 번의 합인가**를 정해야 한다. 그 언어가 점근 분석이다.

```text
  모든 쌍 비교(이중 루프) — 아래 실험의 실측과 추정 (OpenJDK 21, --cpus=2)

  n = 100          비교 약 5천 번          → 1 ms도 안 걸림   (테스트 데이터)
  n = 40,000       비교 약 8억 번          → 약 0.8초         (실측)
  n = 1,000,000    비교 약 5천억 번        → 약 8분           (추정: 40,000의 25² = 625배)
```

- 테스트 100건에서 빠른 것은 아무것도 증명하지 않는다. 점근 분석은 "n을 키우면 어떻게 되나"를 코드만 보고 예측하게 해 준다.
  - *점근(asymptotic)*: n이 충분히 커질 때의 경향. 작은 n에서의 상수·잡음을 무시하고 증가 모양만 본다.

쉬운 예: 반 학생끼리 서로 한 번씩 악수하기다.
- 10명이면 45번, 100명이면 4,950번, 1,000명이면 약 50만 번이다.
- 인원이 10배가 되면 악수는 약 100배가 된다. 학생 수가 아니라 **짝의 수**가 일이다.

똑같은 구조다.\
두 목록을 이중 루프로 대조하는 코드가 이 악수다. n이 두 배면 일은 네 배다.

실무 예:
- 중복 검사·조인을 애플리케이션 이중 루프로 짰다. 개발 데이터 100건에선 즉시, 운영 100만 건에서 배치 창을 넘긴다.
- `ArrayList.add`는 "분할상환 O(1)"인데, 2천만 번째 근처의 한 번이 수백 ms 걸려 요청 지연 최대치가 튄다(아래 실험). 평균과 최대가 다른 보장이다.

## 동작·원리

### 1. 세 가지 표기 — 상한·하한·꽉 낀 한계

```text
  비용 f(n)
    │        c₂·g(n)  ← O: 이 위로는 안 간다 (상한)
    │      ╱
    │    ╱   f(n)
    │  ╱  ╱‾‾‾‾╲___╱‾‾      Θ: 위아래 둘 다 g(n)의 상수배 사이 (꽉 낀 한계)
    │╱  ╱
    │ ╱   c₁·g(n)  ← Ω: 이 아래로는 안 간다 (하한)
    └──┼───────────────── n
       n₀  (여기서부터 성립하면 된다 — 작은 n은 무시)
```

- CLRS 3판 3.1의 정의(양의 상수 c, c₁, c₂, n₀가 있어 모든 n ≥ n₀에서):
  - *O(g(n))*: 0 ≤ f(n) ≤ c·g(n). 상한.
  - *Ω(g(n))*: 0 ≤ c·g(n) ≤ f(n). 하한.
  - *Θ(g(n))*: c₁·g(n) ≤ f(n) ≤ c₂·g(n). 꽉 낀 한계. f = Θ(g) ⇔ f = O(g)이고 f = Ω(g).
- 쓰임이 갈린다(출처별로 나눠 읽는다).
  - 이론 교재: O는 **상한일 뿐**이다. "삽입 정렬은 O(n³)"도 정의상 참이다. Princeton COS226(Sedgewick·Wayne) 1.4 강의 슬라이드는 Θ = 알고리즘 분류, O = 상한 증명, Ω = 하한 증명으로 용도를 나눈다.
  - 실무·면접: "O(n²)"를 "딱 n²로 자란다"(= Θ)는 뜻으로 쓰는 관행이 흔하다.
    - 흔한 오해: "O(n log n) 알고리즘은 O(n²) 알고리즘보다 항상 빠르다." 점근 표기는 상수와 작은 n을 버린다. OpenJDK 21의 `DualPivotQuicksort`는 가장 왼쪽 구간이 길이 44 미만이면 삽입 정렬(O(n²))로 처리한다(`MAX_INSERTION_SORT_SIZE = 44`, `size < 44` 검사). 그 밖의 작은 구간은 길이 65(+재귀 깊이 보정) 미만에서 혼합 삽입 정렬을 쓴다(`MAX_MIXED_INSERTION_SORT_SIZE = 65`). 작은 n에서는 상수가 작은 쪽이 이긴다.
- Sedgewick 4판 1.4는 O 대신 *물결 표기(tilde)* f(N) ~ g(N)(비가 1로 수렴)과 "증가 차수(order of growth)"를 쓴다. 상수까지 남겨 실측과 비교하기 위해서다.

### 2. 최악·최선·평균 — "어떤 입력에서?"

```text
  같은 알고리즘(삽입 정렬), 입력 모양만 다르다

  정렬됨   [1 2 3 4 5]  → 원소마다 비교 1번      → n-1번          최선
  무작위   [3 5 1 4 2]  → 원소마다 평균 절반쯤    → 약 n²/4번      평균
  역순     [5 4 3 2 1]  → 원소마다 앞 전부와     → n(n-1)/2번     최악
```

### 실험: 삽입 정렬 비교 횟수 — 같은 코드, 입력 모양별

(실험, OpenJDK 21.0.12 Temurin, 2026-10-05 — 비교 횟수라 결정적. 무작위는 `Random(42)`)

```text
    n |  정렬됨(최선) |  무작위(평균) |  역순(최악) | n^2/4
 1000 |          999 |       253737 |     499500 | 250000
 2000 |         1999 |       999815 |    1999000 | 1000000
 4000 |         3999 |      3965190 |    7998000 | 4000000
```

- 최선 n−1, 최악 n(n−1)/2, 무작위는 n²/4 근처다. CLRS 3판 2.2의 분석(평균은 최악의 약 절반, 차수는 같은 n²)과 맞는다.
- "평균"은 두 가지 뜻이 있다. 섞지 않는다.
  - *평균 경우(average case)*: **입력 분포**를 가정한 기대 비용. 위 표의 "무작위" 열은 그 분포(서로 다른 키의 모든 순열이 같은 확률)에서 뽑은 **표본 1개**의 값이고, 평균 경우 기대값 약 n²/4에 가깝게 나왔다. 실제 입력이 그 분포가 아니면(이미 거의 정렬됨, 공격자가 고른 입력) 성립하지 않는다.
  - *기대 실행 시간(expected running time)*: 알고리즘 **스스로** 난수를 쓸 때(무작위 피벗 퀵 정렬), 어떤 입력에 대해서든 난수에 대한 기대값. CLRS 3판 5장이 이 둘을 구분한다. 무작위화 알고리즘은 [39-randomized-algorithms](../39-randomized-algorithms/2-summary.md).
- 실무에서 기본은 **최악**이다. 최악은 어떤 입력에도 성립하는 상한이라 SLA 계산에 쓸 수 있다(CLRS 2.2의 이유).

### 3. 분할상환 — "한 번이 아니라 n번의 합"

```text
  ArrayList.add (OpenJDK 21: 용량 10에서 시작, 꽉 차면 old + old/2로 확장 후 전부 복사)

  용량   10 → 15 → 22 → 33 → 49 → 73 → ...     (실측 순서)
  add    ■■■■■■■■■■ [복사10] ■■■■■ [복사15] ■■■■■■■ [복사22] ...
         대부분 1칸 쓰기, 가끔 전체 복사 — 복사량은 등비급수 → 합이 O(n)
```

- *분할상환 분석(amortized analysis)*: 연산 **n번 전체의 최악 합**을 n으로 나눈 값. 확률을 쓰지 않는다(CLRS 3판 17장 서론).
  - CLRS 17장의 세 방법: 집계(aggregate, 17.1 — 합을 직접 센다), 회계(accounting, 17.2 — 싼 연산에 미리 적립), 퍼텐셜(potential, 17.3 — 자료구조 상태에 저장된 에너지). 동적 배열은 17.4 동적 테이블이다.
    - 흔한 오해: 분할상환 = 평균 경우. 평균 경우는 입력 분포를 가정하고, 분할상환은 **어떤 연산 순서에도** 합을 보장한다. 대신 한 번의 연산은 길 수 있다.
- 기초 설명은 원본 [foundations/algorithm-basics](../../foundations/algorithm-basics/README.md) §2, 구현 세부는 [data-structure/01-dynamic-array](../../data-structure/01-dynamic-array/2-summary.md).

### 실험: 복사 횟수 합 — 1.5배 확장 vs 10칸씩 확장

OpenJDK 21 `ArrayList.grow` 규칙(`ArraysSupport.newLength(old, min - old, old >> 1)`, 처음 용량 10)을 그대로 시뮬레이션하고, 비교용으로 "꽉 차면 10칸만 늘리기"를 셌다. 1.5배 규칙은 실제 `ArrayList`의 내부 배열 길이를 리플렉션으로 읽어 같은 값임을 확인했다.

(실험, OpenJDK 21.0.12 Temurin, 2026-10-05 — 결정적)

```text
      n | 1.5배: 복사 합 | 복사/n | +10칸: 복사 합      | 복사/n
    1,000 |         2,456 |   2.46 |              49,500 |       49.5
   10,000 |        28,096 |   2.81 |           4,995,000 |      499.5
  100,000 |       213,413 |   2.13 |         499,950,000 |    4,999.5
1,000,000 |     2,430,972 |   2.43 |      49,999,500,000 |   49,999.5
```

```text
(실제 ArrayList, --add-opens로 elementData.length 관찰)
n=1,000 실제 복사 합=2,456 용량=1,234
n=10,000 실제 복사 합=28,096 용량=14,053
n=100,000 실제 복사 합=213,413 용량=106,710
n=1,000,000 실제 복사 합=2,430,972 용량=1,215,487
처음 용량들: [10, 15, 22, 33, 49, 73, 109, 163, 244, 366, 549, 823]
```

- 1.5배 확장: 원소당 복사가 2~3번 사이에 머문다 → add 한 번당 분할상환 O(1). 복사 합은 마지막 확장 직전 용량 C의 약 r/(r−1) = 1.5/0.5 = 3배 이하이고 C < n이므로 3n을 넘지 않는다. n이 확장 지점 바로 뒤냐 앞이냐에 따라 2~3 사이에서 흔들린다.
- 고정 10칸 확장: 원소당 복사가 n/20으로 자란다 → add 한 번당 분할상환 O(n), n번 합 O(n²).
- 해석: 분할상환 O(1)은 "배수로 키운다"에서 나온다. 고정 크기 증가는 이 보장을 깨뜨린다(CLRS 17.4의 테이블 확장 논증과 같은 결론).

### 4. 두 배 실험 — 코드를 못 읽을 때 차수를 재는 법

```text
  T(2n) / T(n) ≈ 2^b   →  b = log₂(비율)
  비율 ≈ 2   → n¹      비율 ≈ 4 → n²      비율 ≈ 8 → n³
  비율 ≈ 2.1 → n log n 또는 n?   ← 두 배 실험으로는 log 인자를 가려내기 어렵다
```

- Princeton COS226 1.4 강의는 이것을 "doubling hypothesis"라 부르고, 단서로 "Cannot identify logarithmic factors with doubling hypothesis"를 단다. Sedgewick 4판 1.4의 `DoublingRatio` 프로그램이 같은 방식이다.

### 실험: O(n)·O(n log n)·O(n²) — 크기 두 배씩

```java
static long linear(int[] a) { long s = 0; for (int x : a) s += x; return s; }       // O(n)
static void nlogn(int[] a) { Arrays.sort(a); }                                      // O(n log n)
static long quadratic(int[] a) {                                                    // O(n²) 모든 쌍
    long c = 0;
    for (int i = 0; i < a.length; i++)
        for (int j = i + 1; j < a.length; j++) if (a[i] < a[j]) c++;
    return c;
}
```

(실험, OpenJDK 21.0.12 Temurin --cpus=2, 기본 GC, 2026-10-05 — 각 칸 5번 중 최소, 작은 크기로 30회 워밍업. 3회 실행 중 1회째 출력)

```text
O(n)  합계               n=4000000        1.66ms         n=8000000        3.33ms(x2.00) n=16000000       7.22ms(x2.17)
O(n log n) Arrays.sort n=1000000      222.03ms         n=2000000      493.69ms(x2.22) n=4000000     1061.92ms(x2.15)
O(n^2) 모든 쌍 비교         n=10000         45.09ms         n=20000        194.20ms(x4.31) n=40000        730.21ms(x3.76)
```

- 범위(집필 3회 + 사실 점검 재실행 2회): O(n) ×1.65~×2.56, O(n log n) ×2.05~×2.34, O(n²) ×3.48~×4.56. O(n) 칸은 수 ms라 비율이 크게 흔들린다. n=40,000 모든 쌍 비교는 730~832 ms였다.
- 관찰: 선형은 약 2, 제곱은 약 4다. `Arrays.sort`는 2.05~2.34로 2보다 조금 크다. 이론값 2·log(2n)/log(n)은 n=100만에서 약 2.10이다. 다만 위 단서대로 이 정도 차이는 잡음과 겹친다. 선형과 n log n을 가르려면 코드 분석이 필요하다.
- 측정 주의: JIT 워밍업 전 값은 버렸다. `--cpus=2` 제한, GC 시점에 따라 같은 크기도 실행마다 10% 안팎 다르다. 1 ms 근처 값은 비율이 흔들린다.

## 쓰이는 자료구조·알고리즘

- 이 주제가 쓰는 도구: 점화식·급수(분할정복 비용 T(n) = 2T(n/2) + n 등) — [CS 수학 06 recurrences-and-asymptotics](../../math/06-recurrences-and-asymptotics/2-summary.md), 마스터 정리 — [24-divide-conquer](../24-divide-conquer/2-summary.md)
- 분할상환이 쓰이는 자료구조: 동적 배열 [data-structure/01-dynamic-array](../../data-structure/01-dynamic-array/2-summary.md), 스택 [data-structure/03-stack](../../data-structure/03-stack/2-summary.md), 덱 [data-structure/04-queue-deque](../../data-structure/04-queue-deque/2-summary.md), 유니온 파인드 [data-structure/14-union-find](../../data-structure/14-union-find/2-summary.md), 스플레이 트리 [data-structure/23-splay-tree](../../data-structure/23-splay-tree/2-summary.md)
- 이 주제를 쓰는 곳(🔧 모든 선택의 기준): 컬렉션 비용 계약 읽기 [data-structure/02-adt-and-cost-contracts](../../data-structure/02-adt-and-cost-contracts/2-summary.md), 정렬 선택 [01-elementary-sort](../01-elementary-sort/2-summary.md)·[02-merge-sort](../02-merge-sort/2-summary.md)·[03-quick-sort](../03-quick-sort/2-summary.md), DB 조인 알고리즘 비용 [database/11-join-algorithms](../../database/11-join-algorithms/2-summary.md)

## 적용 — 풀어나가는 법

### 1. 코드에서 차수 읽기 — 순서

```text
  ① 루프 중첩: 바깥 n × 안쪽 n → n²   (안쪽이 i부터여도 n²/2 → 여전히 Θ(n²))
  ② 루프 안의 "숨은 루프": list.contains, list.get(i)(LinkedList), String +=, indexOf, sort
  ③ 절반씩 줄이기: while (lo <= hi) mid... → log n
  ④ 재귀: T(n) = a·T(n/b) + f(n) → 마스터 정리(24번)
  ⑤ 분할상환 연산은 "n번 합"으로 센다: ArrayList.add n번 = O(n)
```

- 예: `for (User u : users) if (blocked.contains(u.id()))` — `blocked`가 `List`면 O(n·m), `HashSet`이면 기대 O(n).
- 예: 루프 안 `String s += x` — 매번 새 문자열을 복사해 O(n²) 문자 복사. `StringBuilder`면 분할상환 O(n).

### 2. 운영 n으로 어림 — 시간 예산

```java
// 실측 한 점에서 외삽: T(n_big) ≈ T(n_small) × (n_big / n_small)^b
double tSmallMs = 730.0;          // n=40,000 모든 쌍 비교 (위 실험)
double ratio = 1_000_000 / 40_000.0;
double tBigMs = tSmallMs * ratio * ratio;     // b = 2
System.out.printf("추정 %.0f초%n", tBigMs / 1000);   // 약 456초 — 추정, 실행 안 함
```

- 외삽은 같은 차수가 유지된다는 가정 위에 있다. 캐시를 넘어서는 크기에서는 상수가 바뀐다. 결정 전에 운영 규모로 한 번 잰다([reliability/22-capacity-and-load-testing](../../reliability/22-capacity-and-load-testing/2-summary.md)).

### 3. 지연 최대치가 중요하면 — 분할상환을 의심한다

- 분할상환 O(1)은 처리량(합)에는 좋지만, 한 번의 최악은 O(n)이다. 저지연 경로에서는 미리 용량을 잡는다.

```java
List<Event> buf = new ArrayList<>(expectedMax);    // 확장 복사를 없앤다
Map<String, V> m = HashMap.newHashMap(expectedMax);   // 리해시를 없앤다(Java 19+)
// Java 18 이하: new HashMap<>((int) (expectedMax / 0.75f) + 1)
//   — expectedMax가 약 16억(1_610_612_736) 이상이면 +1에서 int가 넘쳐 음수 → IllegalArgumentException
```

- `HashMap.newHashMap(int)`은 Java 19에서 추가됐다(Java SE 21 API `HashMap` "Since: 19").

### 실험: 분할상환의 꼬리 — `ArrayList.add` 한 번의 최대 시간

(실험, OpenJDK 21.0.12 Temurin --cpus=2, `-Xms1g -Xmx1g` G1, 2026-10-05 — `add` 3천만 번을 하나씩 `nanoTime`으로 재서 가장 느린 6개. 2회 실행 중 1회째 출력)

```text
add 30,000,000번: 평균 119.1 ns/회 (nanoTime 오버헤드 포함)
  느린 add:    688.745 ms  (그때 size=20,767,725)
  느린 add:    115.775 ms  (그때 size=13,845,150)
  느린 add:     81.460 ms  (그때 size=9,230,100)
  느린 add:     48.721 ms  (그때 size=6,153,400)
  느린 add:     34.987 ms  (그때 size=4,102,267)
  느린 add:     18.210 ms  (그때 size=2,734,845)
```

- 느린 add가 일어난 size(2,734,845 → … → 20,767,725)는 1.5배 용량 수열과 정확히 같다. 확장 복사가 일어난 순간들이다.
- 가장 느린 한 번(`-Xlog:gc` 실행 포함 집필 3회 688~749 ms, 사실 점검 2회 731~826 ms)은 복사만이 아니다. `-Xlog:gc`로 다시 돌리자 같은 시점에 `Pause Young (Concurrent Start) (G1 Humongous Allocation) 378M->349M(1024M) 431.376ms`가 찍혔다(점검 재실행에서는 같은 줄이 536.017ms — 실행마다 다르다). 큰 새 배열 할당이 GC를 부른 것이다.
- 해석: 평균은 약 120 ns(측정 오버헤드 포함)인데 최대는 수백 ms다. 분할상환 보장은 평균(합)에 대한 약속이지 최대에 대한 약속이 아니다.

### 4. 코딩 테스트 — n에서 허용 차수 역산(예시 어림)

| n 상한 | 허용 차수(대략) |
|---|---|
| ~20 | O(2ⁿ), O(n!)은 ~10 |
| ~500 | O(n³) |
| ~5,000 | O(n²) |
| ~10⁶ | O(n log n) |
| 그 이상 | O(n), O(log n) |

- 1초에 단순 연산 10⁸번 안팎이라는 어림에서 나온 표다. 언어(파이썬은 더 느리다)·채점기마다 다르므로 예시로만 쓴다.

## 장애 시나리오와 대처

### 1. ⚠ 테스트(100건)에선 빠른 O(n²)가 운영(100만 건)에서 타임아웃

- 현상: 배포 직후는 괜찮다가 데이터가 쌓이면서 배치·API 시간이 데이터 증가 비율의 제곱으로 늘어난다.
- 보이는 형태: 배치 소요 시간 지표가 데이터량 두 배에 네 배. 게이트웨이 504. 스레드 덤프에 같은 이중 루프 프레임. CPU 한 코어 포화.
- 원인: 이중 루프 대조·루프 안 `List.contains` 같은 O(n²) 경로. 100건에서는 비교 5천 번이라 보이지 않았다. 위 실험 기준 100만 건이면 약 8분(추정).
- 대처: 해시·정렬 기반으로 O(n) 또는 O(n log n)으로 바꾼다. 성능 테스트를 운영 최대 n과 그 두 배로 돌려 비율을 본다. 코드 리뷰에서 ①~⑤(위 적용 1) 체크.

### 2. 분할상환 연산의 꼬리 지연 — 평균은 좋은데 최대가 튄다

- 현상: 처리량은 정상인데 가끔 한 요청이 수백 ms 멈춘다. p99.9·최대 지연만 나쁘다.
- 보이는 형태: 지연 히스토그램의 긴 꼬리. GC 로그에 `G1 Humongous Allocation` 원인 일시 정지. 프로파일에 `Arrays.copyOf`·`HashMap.resize`.
- 원인: 동적 배열 확장·해시 리해시가 그 순간 O(n) 작업을 한다(위 실험: size 약 2천만에서 한 번 688~826 ms, GC 포함).
- 대처: 예상 크기로 용량을 미리 잡는다. 거대 단일 컬렉션 대신 청크로 나눈다. G1 humongous 할당은 영역 크기 절반 이상 객체에서 생기므로 큰 배열을 피하거나 영역 크기를 검토한다([reliability/34-tail-latency-and-stragglers](../../reliability/34-tail-latency-and-stragglers/2-summary.md)).

### 3. "평균 O(1)"을 최악 보장으로 착각 — 입력이 가정을 깨뜨림

- 현상: 평소 빠르던 해시 조회·퀵 정렬이 특정 입력에서 급격히 느려진다.
- 보이는 형태: 특정 요청(많은 키를 가진 JSON, 이미 정렬된 대량 데이터)에서만 CPU 급증.
- 원인: 평균 경우 분석은 입력 분포를 가정한다. 해시 충돌을 노린 키(HashDoS, 28C3 Klink–Wälde 2011)나 고정 피벗 퀵 정렬의 정렬된 입력은 그 가정 밖이다.
- 대처: 최악이 보장된 구조(`TreeMap`; 트리화된 `HashMap` 버킷 — JEP 180, 단 OpenJDK 21 소스 주석대로 키의 해시가 서로 다르거나 `Comparable`일 때만 O(log n)이고, 해시가 같고 비교도 못 하면(`compareTo`가 0인 경우 포함) 여전히 선형 탐색), 무작위화(무작위 피벗, 키 해시 시드)를 쓴다. 상세는 [12-hash-functions](../12-hash-functions/2-summary.md) · [39-randomized-algorithms](../39-randomized-algorithms/2-summary.md) · [03-quick-sort](../03-quick-sort/2-summary.md).

### 4. 측정을 잘못 읽음 — 워밍업 없는 비교, 작은 n 외삽

- 현상: 벤치마크로 "A가 B보다 10배 빠르다"고 결론 내 바꿨는데 운영에서 차이가 없거나 반대다.
- 보이는 형태: 첫 측정값이 이후보다 훨씬 크다(JIT 컴파일 전). 1 ms 근처 값의 비율이 실행마다 크게 바뀐다.
- 원인: JIT 워밍업·GC·CPU 제한이 섞였다. 작은 n에서는 상수가 점근 차이를 덮는다(`DualPivotQuicksort`가 작은 구간에 삽입 정렬을 쓰는 이유).
- 대처: 워밍업 후 여러 번 재서 범위를 적는다. 크기를 두 배씩 키워 비율을 본다. 정밀 측정은 JMH([reliability/38-microbenchmarking](../../reliability/38-microbenchmarking/2-summary.md)).

## 핵심 문장

- O는 상한, Ω는 하한, Θ는 꽉 낀 한계다. 실무에서 O를 Θ 뜻으로 쓰는 관행이 있으니 문맥을 확인한다.
- 최악은 모든 입력의 상한, 평균 경우는 입력 분포를 가정한 기대값, 기대 실행 시간은 알고리즘 자신의 난수에 대한 기대값이다.
- 분할상환은 연산 n번 합의 보장이다. 평균 경우와 다르고, 한 번의 연산은 O(n)일 수 있다.
- 동적 배열의 분할상환 O(1)은 배수 확장에서 나온다. 고정 크기 확장은 n번 합을 O(n²)로 만든다.
- 크기를 두 배로 해서 시간이 2배면 선형, 4배면 제곱이다. log 인자는 두 배 실험으로 가리기 어렵다.
- 점근 표기는 상수와 작은 n을 버린다. 작은 n에서는 상수가 작은 O(n²)가 이길 수 있다.

## 관련 주제·근거

- 선행: [01-algorithm-basics](../01-algorithm-basics/2-summary.md) · [CS 수학 06 recurrences-and-asymptotics](../../math/06-recurrences-and-asymptotics/2-summary.md) · 원본 [foundations/algorithm-basics](../../foundations/algorithm-basics/README.md) §1·§2
- 후속·연결: [03-recursion](../03-recursion/2-summary.md) · [39-randomized-algorithms](../39-randomized-algorithms/2-summary.md) · [24-divide-conquer](../24-divide-conquer/2-summary.md) · [03-quick-sort](../03-quick-sort/2-summary.md) · [data-structure/01-dynamic-array](../../data-structure/01-dynamic-array/2-summary.md) · [data-structure/02-adt-and-cost-contracts](../../data-structure/02-adt-and-cost-contracts/2-summary.md)
- 다른 영역: [reliability/22-capacity-and-load-testing](../../reliability/22-capacity-and-load-testing/2-summary.md) · [reliability/34-tail-latency-and-stragglers](../../reliability/34-tail-latency-and-stragglers/2-summary.md) · [reliability/38-microbenchmarking](../../reliability/38-microbenchmarking/2-summary.md) · [database/11-join-algorithms](../../database/11-join-algorithms/2-summary.md)
- 교재
  - CLRS 3판 2.2 Analyzing algorithms(최악·평균, 삽입 정렬 분석), 3장 Growth of Functions(3.1 Θ·O·Ω 정의), 5장 Probabilistic Analysis and Randomized Algorithms(평균 경우 vs 기대 실행 시간), 17장 Amortized Analysis(17.1 집계, 17.2 회계, 17.3 퍼텐셜, 17.4 동적 테이블)
  - Sedgewick·Wayne 『Algorithms』 4판 1.4 Analysis of Algorithms(물결 표기, 증가 차수, 두 배 실험) <https://algs4.cs.princeton.edu/14analysis/> · `DoublingRatio.java` <https://algs4.cs.princeton.edu/14analysis/DoublingRatio.java.html>
  - Princeton COS226 Fall 2015 강의 "1.4 Analysis of Algorithms" 슬라이드(doubling hypothesis와 log 인자 단서, Θ·O·Ω 용도 표) <https://www.cs.princeton.edu/courses/archive/fall15/cos226/lectures/14AnalysisOfAlgorithms.pdf>
- 소스·문서
  - OpenJDK 21u `java/util/ArrayList.java`(`grow`: `ArraysSupport.newLength(oldCapacity, minCapacity - oldCapacity, oldCapacity >> 1)`, `DEFAULT_CAPACITY = 10`), `java/util/DualPivotQuicksort.java`(`MAX_INSERTION_SORT_SIZE = 44`, `MAX_MIXED_INSERTION_SORT_SIZE = 65`, `MAX_RECURSION_DEPTH`, 힙 정렬 전환)
  - Java SE 21 API `ArrayList`(add 분할상환 상수 시간), `HashMap`(`newHashMap`, Since 19)
  - JEP 180 <https://openjdk.org/jeps/180> · 28C3 "Effective Denial of Service attacks against web application platforms"(Klink·Wälde, 2011) <https://media.ccc.de/v/28c3-4680-en-effective_dos_attacks_against_web_application_platforms>
- 실험 목록(2026-10-05, scratchpad `dsa/ds-01/`, OpenJDK 21.0.12 Temurin `eclipse-temurin:21-jdk`, --cpus=2)
  - `Cases.java`: 삽입 정렬 비교 횟수 — 정렬됨·무작위·역순(결정적)
  - `Amortized.java`: 1.5배 vs +10칸 확장 복사 합 시뮬레이션 / `RealGrowth.java`: 실제 `ArrayList` 용량·복사 합(`--add-opens java.base/java.util=ALL-UNNAMED`)
  - `Growth.java`: O(n)·`Arrays.sort`·모든 쌍 비교 두 배 실험, 3회
  - `AddSpike.java`: `add` 3천만 번 중 최대 지연 6개(`-Xms1g -Xmx1g`, 2회 + `-Xlog:gc` 1회)
