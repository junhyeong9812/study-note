# algorithm/01-algorithm-basics — 알고리즘 기초: 입력 규모로 고르는 탐색과 정렬 — 정리 (힌트)

## 해결하는 문제

테스트 데이터는 작다. 운영 데이터는 크다. 작은 데이터에서는 어떤 알고리즘이든 빨라 보인다.

```text
  같은 정렬 요청, 원본 코드 그대로 (CPython 3.12, 아래 실험)

  n = 1,000      거품 정렬  ~0.1초     퀵 정렬  ~0.002초     → 둘 다 "빠르다"
  n = 4,000      거품 정렬  ~1.8초     퀵 정렬  ~0.01초
  n = 100,000    거품 정렬  ~20분(추정) 퀵 정렬  ~0.4초      → 한쪽은 타임아웃
```

- 차이는 "몇 초 걸렸나"가 아니라 **n이 두 배가 될 때 일이 몇 배가 되나**에서 나온다.
  - *알고리즘(algorithm)*: 입력을 받아 정해진 단계를 거쳐 답을 내는 절차.
  - *입력 규모(n)*: 알고리즘이 다루는 원소 수. 비용을 n의 함수로 본다.

쉬운 예: 출석부에서 이름 찾기다.
- 순서 없는 출석부는 처음부터 한 명씩 본다. 30명이면 금방이지만 3만 명이면 오래 걸린다.
- 가나다순 출석부는 가운데를 펴서 앞인지 뒤인지 보고 절반을 버린다. 3만 명도 15번 남짓 펴면 된다.

똑같은 구조다.\
앞은 *선형 탐색*, 뒤는 *이진 탐색*이다. 이진 탐색은 "가나다순"(정렬)이라는 전제를 대가로 낸다.

실무 예:
- 관리자 화면이 개발 DB(100건)에서는 즉시 뜨는데 운영(100만 건)에서는 게이트웨이 타임아웃이 난다. 서버 코드가 목록 두 개를 이중 루프로 대조하고 있었다.
- 조회 API마다 "정렬 후 이진 탐색" 함수를 불렀는데, 그 함수가 호출될 때마다 리스트를 다시 정렬한다(원본 §4 코드 모양). 이진 탐색인데 선형 탐색 급으로 느리다.

이 노트는 원본 [foundations/algorithm-basics](../../foundations/algorithm-basics/README.md)(부트캠프 ch14 따라 친 원고)를 이어받는다. 원본이 이미 설명한 정의·코드는 링크와 한두 줄 요약만 두고, **두 배 실험·원본 오류·장애·적용**을 채운다.

## 동작·원리

### 1. 빅오 — "n이 커질 때 일의 양이 어떻게 늘어나나"

```text
  n이 2배가 될 때 일의 양          대표 예(원본 §1·§3~§5)
  O(1)        그대로              배열 i번째 읽기
  O(log n)    +1 단계             이진 탐색
  O(n)        2배                 선형 탐색
  O(n log n)  2배보다 조금 더       퀵 정렬(평균), 병합 정렬
  O(n²)       4배                 거품 정렬, 모든 쌍 비교
```

- 원본 §1이 정의와 곡선 그림을 준다. 요지는 "절대 시간이 아니라 n에 따른 연산 횟수의 경향"이다.
  - *빅오(Big-O)*: 비용이 n에 대해 어떤 함수보다 **크게 자라지 않는다**는 상한 표기. 정확한 정의(상수 c·문턱 n₀)와 Θ·Ω는 다음 편 [02-asymptotic-analysis](../02-asymptotic-analysis/2-summary.md).
- 원본 §2의 분할 상환(동적 배열 확장 복사를 나눠 내기)도 다음 편에서 복사 횟수 실측으로 다룬다.

### 2. 선형 탐색 vs 이진 탐색 — 비교 횟수

```text
  이진 탐색, data = [1..10], target = 1           (start, end, mid는 0부터 센 인덱스)
  ① start=0 end=9 mid=4 → data[4]=5 > 1  → end=3
  ② start=0 end=3 mid=1 → data[1]=2 > 1  → end=0
  ③ start=0 end=0 mid=0 → data[0]=1 = 1  → 찾음 (3번)

  남은 후보:  10 → 4 → 1   (매번 절반 이하)
```

- 선형 탐색: 최선 1번(첫 원소), 최악 n번(마지막이거나 없음) → O(n). 원본 §3.
- 이진 탐색: 비교 한 번마다 후보가 절반 이하로 준다 → 최악 ⌊log₂n⌋ + 1번 → O(log n). 원본 §4의 유도 n·(1/2)^k = 1 → k = log₂n은 이 식의 근삿값이다.

### 실험: 이진 탐색 비교 횟수와 원본 코드의 숨은 정렬

원본 §4 루프를 그대로 두고 "mid를 확인한 횟수"만 셌다. 이어서 원본 `binary_search`(호출마다 `data.sort()`)를 질의 1,000번에 그대로 쓴 경우를 비교했다.

(실험, CPython 3.12.14 `python:3.12-slim` 컨테이너 --cpus=2, 2026-10-05 — 시간은 실행마다 다르다. 2회 실행 중 1회째 출력)

```text
[1] 이진 탐색 비교 횟수 (data = 1..n)
  n=       10  target=1 → 3회, 최악 4회, floor(log2 n)+1 = 4
  n=      100  target=1 → 6회, 최악 7회, floor(log2 n)+1 = 7
  n=    1,000  target=1 → 9회, 최악 10회, floor(log2 n)+1 = 10
  n=1,000,000  target=1 → 19회, 최악 20회, floor(log2 n)+1 = 20
[3] 질의 1,000번 — 원본 binary_search(매번 sort) vs 한 번 정렬 + bisect vs 선형 탐색
  원본 binary_search     4009.7 ms
  sort 1번 + bisect         1.9 ms
  linear_search          8825.3 ms
```

- 비교 횟수(결정적, 매번 같다): 최악이 ⌊log₂n⌋ + 1과 정확히 맞는다. n=1,000,000도 20번이다. 최악 값은 n ≤ 1,000이면 target 1..n+1 전부, n = 100만이면 무작위 2,000개와 n, n+1을 넣어 찾은 최댓값이다.
- 원본 `binary_search`(n = 100,000, 질의 1,000번): 집필 2회 + 점검 1회 범위 4010~4190 ms. 한 번만 정렬하고 `bisect`를 쓰면 1.4~1.9 ms다.
  - 해석: 원본은 호출마다 `data.sort()`를 한다. 첫 호출 뒤에는 이미 정렬돼 있어 CPython의 정렬이 n−1번 비교로 끝나지만(호스트 CPython 3.12.3에서 정렬된 10만 개 정렬 비교 99,999회 확인), 그래도 호출마다 O(n)이다. 그래서 이진 탐색인데 선형 탐색(8.8초)과 같은 급이 됐다.

### 3. 거품 정렬 vs 퀵 정렬 — 두 배 실험

```text
  거품 정렬: 이웃끼리 비교·교환을 끝까지 → 한 바퀴에 최댓값 하나가 끝으로
   [5 1 4 2] → [1 4 2 5] → [1 2 4 5] → ...    비교 (n-1)+(n-2)+…+1 = n(n-1)/2

  퀵 정렬: 피벗 기준으로 작은 쪽 / 큰 쪽으로 가르고 각각 재귀
                [5 1 4 2 8 3]   pivot=4(가운데)
               /              \
          [3 1 2]            [4 8 5]       분할 깊이가 log n이면 각 층 O(n) → O(n log n)
```

- 코드는 원본 §5(파이썬). 원본 퀵 정렬은 가운데 원소를 피벗으로 쓰는 호어 방식 분할이다.

(실험, CPython 3.12.14 `python:3.12-slim` --cpus=2, 2026-10-05 — 무작위 정수, 3번 중 최소. 2회 실행 중 1회째 출력)

```text
[2] 정렬 시간 — 크기 두 배씩 (무작위 정수, 3번 중 최소)
  bubble n= 1000    120.9 ms 
  bubble n= 2000    518.6 ms (x4.3)
  bubble n= 4000   1845.6 ms (x3.6)
  quick  n= 1000      2.2 ms 
  quick  n= 2000      5.1 ms (x2.3)
  quick  n= 4000     10.8 ms (x2.1)
  quick  n=100000    399.0 ms
  quick  n=200000    771.1 ms
```

- 범위(집필 2회 + 점검 1회): 거품 비율 ×3.6~×4.8, 퀵 비율 ×2.1~×2.4. 퀵 n=200,000은 771~873 ms.
- 관찰: 거품 정렬은 두 배 → 약 4배(O(n²)), 퀵 정렬은 두 배 → 2배 남짓(O(n log n)).
- 추정: 거품 정렬 n=100,000은 n=1,000(97~121 ms)의 (100)² = 10,000배 → 약 970~1,210초(약 16~20분). 실행하지 않은 **추정**이다.

### 4. Java·C로 옮길 때 — `mid = (start + end) // 2`

- 파이썬 정수는 크기 제한이 없어 원본 식이 안전하다.
- Java `int`는 32비트라 `start + end`가 2³¹−1을 넘으면 음수로 감긴다(JLS §4.2). C의 `int` 폭은 구현마다 다르고(흔한 플랫폼은 32비트, 표준 최소 16비트), 부호 있는 정수 오버플로는 감기는 것이 아니라 정의되지 않은 동작이다(C11 N1570 §5.2.4.2.1·§6.5). Bloch(2006)는 이 버그가 JDK `Arrays.binarySearch`에 약 9년 있었다고 보고했다. 원소가 2³⁰개 이상인 배열에서 드러난다.

(실험, OpenJDK 21.0.12 Temurin, 2026-10-05)

```java
int lo = 1_500_000_000, hi = 2_000_000_000;
System.out.println("(lo + hi) / 2      = " + (lo + hi) / 2);
System.out.println("lo + (hi - lo) / 2 = " + (lo + (hi - lo) / 2));
System.out.println("(lo + hi) >>> 1    = " + ((lo + hi) >>> 1));
```

```text
(lo + hi) / 2      = -397483648
lo + (hi - lo) / 2 = 1750000000
(lo + hi) >>> 1    = 1750000000
```

- 음수 인덱스로 배열을 읽으면 Java는 `ArrayIndexOutOfBoundsException`, C는 정의되지 않은 동작이다. 자세한 불변식은 [06-binary-search](../06-binary-search/2-summary.md).

### 원본 오류와 바로잡기

- 참고: 원본 §1은 `O(1)` 예로 "map", `O(log n)` 예로 "이진 탐색 트리", `O(n log n)` 예로 "퀵 정렬"을 든다. 각각 조건이 붙는다. 해시 맵의 O(1)은 해시가 고르게 퍼진다는 가정 아래 기대 비용이다(Java 21 `HashMap` Javadoc). BST의 O(log n)은 균형이 맞을 때이고, 정렬된 입력에서는 O(n)이다([data-structure/01-data-structures-basics](../../data-structure/01-data-structures-basics/2-summary.md) 실험). 퀵 정렬의 O(n log n)은 평균이고 최악은 O(n²)이다(CLRS 3판 7.2).
- 참고: 원본 §4 `binary_search`는 함수 안에서 `data.sort()`를 한다. 그래서 (1) 호출자의 리스트를 바꾸고, (2) 반환한 인덱스가 원래 리스트의 위치가 아니며, (3) 호출마다 정렬 비용이 든다(위 실험: 질의 1,000번에 약 4초). 정렬은 호출 밖에서 한 번 하고, 탐색 함수는 "정렬돼 있다"를 전제 조건으로 문서화한다.
- 참고: 원본 §4의 "10까지의 데이터라면 3번 비교"는 target = 1일 때 맞다. 최악은 4번(⌊log₂10⌋ + 1)이다(위 실험).
- 참고: 원본 §5의 거품 정렬에는 "한 바퀴 동안 교환이 없으면 멈춘다" 조기 종료가 없다. 그래서 이미 정렬된 입력도 n(n−1)/2번 비교한다. 조기 종료를 넣으면 정렬된 입력에서 n−1번으로 끝난다(최선 O(n)).

## 쓰이는 자료구조·알고리즘

- 이 주제가 쓰는 구조: 배열(임의 접근 O(1)이 이진 탐색의 전제) — [data-structure/01-dynamic-array](../../data-structure/01-dynamic-array/2-summary.md), 비용 계약 — [data-structure/02-adt-and-cost-contracts](../../data-structure/02-adt-and-cost-contracts/2-summary.md)
- 각 알고리즘의 심화 노트
  - 이진 탐색 → [06-binary-search](../06-binary-search/2-summary.md), 응용 → [07-parametric-search](../07-parametric-search/2-summary.md)
  - 기본 정렬(선택·삽입·거품) → [01-elementary-sort](../01-elementary-sort/2-summary.md)
  - 퀵 정렬 → [03-quick-sort](../03-quick-sort/2-summary.md), 병합 정렬 → [02-merge-sort](../02-merge-sort/2-summary.md)
  - 분할정복 일반 → [24-divide-conquer](../24-divide-conquer/2-summary.md)
- 이 주제를 쓰는 곳(🔧): 선형·이진 탐색, 기본 정렬 — 모든 조회·정렬 코드의 출발점. 실무 정렬(안정성·비교자·TimSort)은 [09-sorting-in-practice](../09-sorting-in-practice/2-summary.md), 재귀는 [03-recursion](../03-recursion/2-summary.md).

## 적용 — 풀어나가는 법

### 1. 고르는 순서 — "운영 n을 먼저 적는다"

```text
  ① 운영 최대 n은?             (테스트 데이터 말고)
  ② 몇 번 하나?                질의 1번이면 선형 탐색 O(n)로 충분할 수 있다
                               질의 m번이면 정렬 1번 O(n log n) + 이진 탐색 m × O(log n)
  ③ 허용 시간은?               API 타임아웃·배치 창
  ④ 표준 라이브러리부터          직접 짠 정렬·탐색은 마지막
```

- 예: n = 100만, 질의 1만 번. 선형 탐색이면 비교 약 10¹⁰번 급(최악 기준). 정렬 1번 + 이진 탐색이면 정렬 약 2×10⁷ + 탐색 약 2×10⁵ 비교 급.
- 탐색이 주 업무면 해시 맵(기대 O(1))이 더 맞을 수 있다. 정렬 순서·범위 질의가 필요하면 정렬 배열 + 이진 탐색이나 `TreeMap`.

### 2. Java 21로 — 표준 라이브러리 쓰기

```java
import java.util.*;

int[] ids = loadIds();                 // 운영 n
Arrays.sort(ids);                      // 한 번만 정렬 (원시형: Dual-Pivot Quicksort)

int pos = Arrays.binarySearch(ids, target);
if (pos >= 0) {
    // 찾음: ids[pos] == target
} else {
    int insertionPoint = -pos - 1;     // 없으면 (-(삽입 위치) - 1)을 돌려준다
}

List<Order> orders = loadOrders();
orders.sort(Comparator.comparing(Order::createdAt));   // 객체: 안정 정렬(TimSort 계열)
```

- `Arrays.sort(int[])` Javadoc(OpenJDK 21u `Arrays.java` 92~95행): Dual-Pivot Quicksort이고 "offers O(n log(n)) performance on all data sets". 구현은 분할 깊이가 커지면 힙 정렬로 바꾼다(`DualPivotQuicksort.java` "Switch to heap sort if execution time is becoming quadratic").
- `Arrays.binarySearch`는 정렬이 안 된 배열이면 결과가 정의되지 않는다(Javadoc). 정렬은 호출자가 책임진다.

### 3. 코딩 테스트에서 — n으로 시간 복잡도 역산

- 흔한 어림(언어·채점기마다 다르다, 예시): 1초에 단순 연산 10⁸번 안팎.
  - n ≤ 수천 → O(n²) 가능 / n ≤ 수십만~백만 → O(n log n) / n이 그보다 크면 O(n) 또는 O(log n).
- 파이썬은 같은 연산의 상수가 Java보다 크다. 위 실험에서 파이썬(원본 퀵 정렬) n=100,000이 약 0.4초였다. Java `Arrays.sort(int[])`는 10배 큰 100만 개를 약 0.2초에 끝냈다([02-asymptotic-analysis](../02-asymptotic-analysis/2-summary.md) 실험, 같은 --cpus=2 제한). 언어·구현이 다른 비교라 배수는 참고만 한다.

### 4. 진단 — "운영에서만 느리다"

- 같은 요청을 n을 두 배씩 늘린 데이터로 재 본다. 두 배 → 4배면 O(n²) 경로가 있다.
- Java: 느린 요청 중 `jcmd <pid> Thread.print`를 몇 번 떠서 같은 루프 프레임을 찾는다. 파이썬: `cProfile`로 누적 시간 상위 함수를 본다. `sort`가 탐색 함수 안에서 반복 호출되면 원본 §4 모양이다.

## 장애 시나리오와 대처

### 1. ⚠ 입력 규모를 보지 않은 선택 — 테스트에선 빠르고 운영에선 타임아웃

- 현상: 개발·스테이징에서 수십 ms이던 배치·API가 운영 데이터에서 타임아웃 난다.
- 보이는 형태: 게이트웨이 504, 배치 실행 시간 지표가 데이터 증가 비율의 제곱으로 증가. 스레드 덤프에 같은 이중 루프 프레임.
- 원인: O(n²) 알고리즘(거품 정렬, 이중 루프 대조)을 작은 n에서만 검증했다. 위 실험에서 거품 정렬은 n=1,000에서 0.1초지만, n=100,000이면 추정 20분이다.
- 대처: 운영 최대 n으로 성능 테스트한다. 표준 정렬(`Arrays.sort`, `List.sort`)과 해시·정렬 기반 대조(O(n log n) 또는 O(n))로 바꾼다. 데이터가 크기 단위로 늘 때마다 다시 잰다.

### 2. 탐색 함수 안의 숨은 정렬 — 이진 탐색인데 질의마다 O(n)

- 현상: "이진 탐색이라 빠를 것"이라던 조회가 데이터 증가에 비례해 느려진다.
- 보이는 형태: 프로파일 상위에 `list.sort`/`Arrays.sort`가 탐색 함수 아래에 있다. 호출자 리스트 순서가 바뀌어 다른 버그도 난다.
- 원인: 원본 §4처럼 탐색 함수가 매 호출 정렬한다.
- 대처: 정렬은 데이터가 바뀔 때 한 번, 탐색 함수는 정렬된 입력을 전제로 한다. 데이터가 자주 바뀌면 정렬 배열 대신 `TreeMap`이나 해시 맵.

### 3. 이진 탐색 중간값 오버플로 — 큰 배열에서만 터짐

- 현상: 원소가 약 2³⁰개(약 10억 개) 이상인 배열(또는 큰 오프셋 계산)에서, 뒤쪽을 찾을 때만 이진 탐색이 예외를 던진다(Bloch 원문은 "2^30 or greater", 실제로 넘치는 첫 크기는 2³⁰ + 1 — [43-alg-incidents](../43-alg-incidents/2-summary.md) 실험 D). C에서는 예측할 수 없는 결과가 난다(Bloch 2006).
- 보이는 형태: Java `ArrayIndexOutOfBoundsException: Index -397483648 …` 같은 음수 인덱스.
- 원인: `(lo + hi) / 2`가 `int` 범위를 넘었다(위 실험).
- 대처: `lo + (hi - lo) / 2` 또는 `(lo + hi) >>> 1`. 표준 `Arrays.binarySearch`를 쓴다.

### 4. 정렬되지 않은 데이터에 이진 탐색 — 조용히 틀린 답

- 현상: 있는 값을 "없다"고 한다. 예외는 없다.
- 보이는 형태: `Arrays.binarySearch`가 음수(없음)를 돌려준다. 재현이 데이터 순서에 따라 들쭉날쭉하다.
- 원인: 이진 탐색의 전제(정렬)가 깨졌다. 데이터를 추가한 뒤 정렬을 잊었거나, 정렬 기준(비교자)과 탐색 기준이 다르다.
- 대처: 삽입 시 정렬 위치에 넣는다(`-pos - 1`). 테스트에서 "정렬돼 있다" 단언을 둔다. 비교자는 정렬과 탐색에 같은 것을 쓴다.

## 핵심 문장

- 알고리즘 비용은 초가 아니라 n이 두 배일 때 일이 몇 배가 되느냐로 본다.
- 선형 탐색은 O(n), 이진 탐색은 정렬을 전제로 최악 ⌊log₂n⌋ + 1번 비교한다.
- 거품 정렬은 두 배 → 약 4배, 퀵 정렬은 두 배 → 2배 남짓이다. 작은 테스트 데이터로는 둘이 구별되지 않는다.
- 이진 탐색 함수 안에서 매번 정렬하면 이진 탐색의 이점이 사라진다. 정렬은 한 번, 탐색은 여러 번이다.
- 파이썬에서 안전한 `(start + end) // 2`도 Java `int`(32비트)에서는 오버플로한다(C의 부호 있는 `int`라면 정의되지 않은 동작).

## 관련 주제·근거

- 원본: [foundations/algorithm-basics](../../foundations/algorithm-basics/README.md) — 부트캠프 ch14 이관본(§1 빅오, §2 분할 상환, §3 선형 탐색, §4 이진 탐색, §5 거품·퀵 정렬)
- 선행: [data-structure/01-data-structures-basics](../../data-structure/01-data-structures-basics/2-summary.md)
- 후속: [02-asymptotic-analysis](../02-asymptotic-analysis/2-summary.md) · [06-binary-search](../06-binary-search/2-summary.md) · [01-elementary-sort](../01-elementary-sort/2-summary.md) · [03-quick-sort](../03-quick-sort/2-summary.md) · [02-merge-sort](../02-merge-sort/2-summary.md) · [03-recursion](../03-recursion/2-summary.md) · [09-sorting-in-practice](../09-sorting-in-practice/2-summary.md)
- 다른 영역: [data-structure/02-adt-and-cost-contracts](../../data-structure/02-adt-and-cost-contracts/2-summary.md) · [reliability/22-capacity-and-load-testing](../../reliability/22-capacity-and-load-testing/2-summary.md) · [reliability/36-profiling](../../reliability/36-profiling/2-summary.md)
- 교재·문서
  - 컴퓨터사이언스 부트캠프 with 파이썬 ch14(원본 출처)
  - CLRS 3판 2장(2.1 삽입 정렬, 2.2 알고리즘 분석 — 최악·평균), 3장(점근 표기), 7장(퀵 정렬 — 7.2 최악 Θ(n²)), 12장(BST)
  - Sedgewick·Wayne 『Algorithms』 4판 1.4 Analysis of Algorithms(두 배 실험) <https://algs4.cs.princeton.edu/14analysis/>
  - Joshua Bloch, "Extra, Extra - Read All About It: Nearly All Binary Searches and Mergesorts are Broken", Google Research Blog, 2006-06-02 <https://research.google/blog/extra-extra-read-all-about-it-nearly-all-binary-searches-and-mergesorts-are-broken/>
  - Java SE 21 API `Arrays`(sort·binarySearch), `HashMap` 클래스 주석 · OpenJDK 21u `Arrays.java`, `DualPivotQuicksort.java`(힙 정렬 전환, `MAX_RECURSION_DEPTH`)
  - CPython 3.12 `Objects/listsort.txt`(정렬 알고리즘 설명, 이미 정렬된 입력 처리) <https://github.com/python/cpython/blob/3.12/Objects/listsort.txt>
- 실험 목록(2026-10-05, scratchpad `dsa/ds-01/`)
  - `alg_basics.py`: 원본 코드 그대로 — 이진 탐색 비교 횟수, 거품·퀵 정렬 두 배 실험, 원본 `binary_search` 질의 1,000번 vs `bisect` vs 선형 — CPython 3.12.14(`python:3.12-slim`, --cpus=2), 2회
  - 정렬된 10만 개 `list.sort` 비교 횟수 99,999 — 호스트 CPython 3.12.3 한 줄 스크립트
  - `MidOverflow.java`: `(lo+hi)/2` 오버플로 — OpenJDK 21.0.12 Temurin
