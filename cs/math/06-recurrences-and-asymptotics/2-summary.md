# math/06-recurrences-and-asymptotics — 점화식·급수·로그, 재귀 트리와 마스터 정리 — 정리 (힌트)

## 해결하는 문제

재귀 코드의 비용은 코드에 바로 보이지 않는다. "자기 자신을 몇 번, 얼마나 작게 부르나"로 적은 식, 곧 **점화식**을 풀어야 보인다.

```text
  모양이 비슷한 두 재귀                                결과는 전혀 다르다 (MCS 22.5 표)
  하노이 탑   T(n) = 2T(n−1) + 1   크기 n−1짜리 둘       T(n) = 2^n − 1      n=64 → 10^19 단계 넘음
  병합 정렬   T(n) = 2T(n/2) + n−1 크기 n/2짜리 둘       T(n) ≈ n log n      n=64 → 수백 번 비교
```

- 점화식을 못 풀면 "테스트(n=1000)에서는 빨랐다"를 운영 입력으로 외삽할 수 없다.
- 재귀의 깊이도 점화식에서 나온다. 깊이가 n에 비례하면 스택이 먼저 터진다.

쉬운 예: 사전에서 단어 찾기.
- 반으로 펼쳐 앞뒤를 고르는 일을 반복하면 1,000쪽도 10번 남짓이면 끝난다. T(n) = T(n/2) + 1.
- 한 장씩 넘기면 1,000번이다. T(n) = T(n−1) + 1.

똑같은 구조다.\
"얼마나 작게 줄이나(÷2 vs −1)"가 로그와 선형을 가른다. 이진 탐색과 선형 탐색의 차이다.

실무 예:
- 연결 리스트·트리를 재귀로 도는 코드가 운영 데이터(긴 사슬)에서 `StackOverflowError`를 낸다(깊이 = n).
- 매 단계 나머지 배열을 복사하는 재귀·루프가 입력 20만~30만에서 초 단위로 느려진다(T(n) = T(n−1) + n = Θ(n²)).
- 메모 없는 중복 재귀가 n이 2 늘 때마다 약 2.6배씩 느려진다(T(n) = T(n−1) + T(n−2), [algorithm/03-recursion](../../algorithm/03-recursion/2-summary.md) 실험).

## 동작·원리

### 1. 급수 — 점화식을 풀면 나오는 합들

```text
  등차    1 + 2 + … + n        = n(n+1)/2               ~ n²/2
  등비    1 + x + … + x^n      = (1 − x^(n+1))/(1 − x)  (x ≠ 1, MCS 식 14.2)
          |x| < 1이면 끝없이 더해도 1/(1 − x)            (MCS Theorem 14.1.1)
  조화    H_n = 1 + 1/2 + … + 1/n,  ln n + 1/n ≤ H_n ≤ ln n + 1   (MCS 식 14.21)
```

- 기호
  - *~*: 비가 1로 가는 근사. n(n+1)/2 ~ n²/2.
  - *ln*: 자연로그. 밑만 다른 로그는 상수배다(log_b n = ln n / ln b). 그래서 Θ 안에서는 밑을 생략한다.
- 실무 감각
  - 등비 비 0 < x < 1(줄어드는 합) → 첫 항이 전체를 정한다. x > 1(늘어나는 합) → 마지막 항이 정한다. (음수 비는 부호가 번갈아 이 감각이 맞지 않는다 — 수렴 조건은 |x| < 1.)
  - 동적 배열을 2배씩 키울 때 복사 총량이 n 근처인 이유가 등비급수다([algorithm/02-asymptotic-analysis](../../algorithm/02-asymptotic-analysis/2-summary.md) 분할상환).
  - 조화수는 "1/i씩 줄어드는 일"의 합이다. 쿠폰 수집 기댓값 n·H_n ≈ n ln n이 여기서 나온다(매번 n종 중 하나가 균일·독립으로 나올 때, [08-expectation-variance-tails](../08-expectation-variance-tails/2-summary.md)).
- 로그 항등식 하나: a^(log_b n) = n^(log_b a). 재귀 트리의 잎 개수를 n의 거듭제곱으로 바꿀 때 쓴다.

### 2. 두 종류의 점화식 — 빼기형과 나누기형

| 형태 | 예 | 해 | 깊이 |
|---|---|---|---|
| 나누기형, 부분 문제 1개 | T(n) = T(n/2) + 1 (이진 탐색) | Θ(log n) | log n |
| 나누기형, 2개 | T(n) = 2T(n/2) + n (병합 정렬) | Θ(n log n) | log n |
| 빼기형, 1개 | T(n) = T(n−1) + 1 (리스트 재귀) | Θ(n) | **n** |
| 빼기형, 1개 + 선형 일 | T(n) = T(n−1) + n (퀵정렬 최악, 꼬리 복사) | Θ(n²) | **n** |
| 빼기형, 2개 | T(n) = T(n−1) + T(n−2) + 1 (메모 없는 피보나치) | Θ(φ^n), φ ≈ 1.618 | n |
| 빼기형, 2개 | T(n) = 2T(n−1) + 1 (하노이) | 2^n − 1 | n |

- MCS 22.5의 경험칙: 부분 문제가 원래보다 **상수만큼** 작으면(n−1, n−2) 해는 대개 지수다(부분 문제가 하나뿐인 T(n−1) + n 같은 식은 다항식이다). **비율만큼** 작으면(n/2) 대개 다항식으로 묶인다.
- 성능은 "호출당 일의 양"보다 "부분 문제의 크기와 개수"가 대개 정한다(MCS 22.5 경험칙 "usually"). 다만 나누기형에서는 g(n)도 함께 본다 — 같은 2T(n/2)라도 +n이면 Θ(n log n), +n²이면 Θ(n²)다(아래 4). 하노이의 +1을 +n으로 바꿔도 해는 두 배쯤만 커지지만, n−1을 n/2로 바꾸면 지수가 다항식이 된다.
- 깊이: 빼기형은 깊이가 n이다. 재귀로 구현하면 n만큼 스택 프레임을 쌓는다. 나누기형은 log n이다.

### 3. 재귀 트리 — 층별 일의 합

```text
  T(n) = 2T(n/2) + n                                     층의 일
  층 0                 [n]                                 n
  층 1           [n/2]      [n/2]                          n
  층 2       [n/4] [n/4] [n/4] [n/4]                       n
   ...                 ...                                ...
  층 log₂n   [1][1][1] ... [1]   (잎 n개)                  n
  ─────────────────────────────────────────────────
  합 = n × (log₂n + 1)  = Θ(n log n)    층마다 같다 → 층 수를 곱한다

  T(n) = 4T(n/2) + n                                     층 i의 일 = 4^i · (n/2^i) = 2^i · n
  층의 일이 2배씩 는다 → 등비급수, 마지막 층(잎 4^(log₂n) = n²개)이 지배 → Θ(n²)

  T(n) = 2T(n/2) + n²                                    층 i의 일 = 2^i · (n/2^i)² = n²/2^i
  층의 일이 절반씩 준다 → 등비급수, 첫 층(뿌리 n²)이 지배 → Θ(n²)
```

- 세 그림이 마스터 정리의 세 경우다.
  - 층의 일이 **등비로(층마다 일정 배율로) 늘면** 잎이 지배(경우 1).
  - **같으면** 층 수(log n)를 곱한다(경우 2).
  - **줄면** 뿌리가 지배(경우 3).
- 근거: CLRS 3판 4.4(재귀 트리 방법), MCS 22.2·22.4.

### 4. 마스터 정리 — 나누기형의 공식

```text
  T(n) = a·T(n/b) + g(n)        a ≥ 1개 부분 문제, 크기 n/b (b > 1), 나누고 합치는 일 g(n)
                                a·b는 n과 무관한 상수
  비교 기준: n^(log_b a)  = 잎의 개수 (a^(log_b n) = n^(log_b a))

  경우 1  g(n) = O(n^(log_b a − ε))  어떤 ε > 0             → T(n) = Θ(n^(log_b a))
  경우 2  g(n) = Θ(n^(log_b a) · log^k n)  어떤 k ≥ 0       → T(n) = Θ(n^(log_b a) · log^(k+1) n)
  경우 3  g(n) = Ω(n^(log_b a + ε))  어떤 ε > 0
          그리고 a·g(n/b) ≤ c·g(n)  (어떤 c < 1, 충분히 큰 n)   → T(n) = Θ(g(n))
```

- 출처: MCS Theorem 22.4.2(위 형태, 경우 2에 log^k 포함). CLRS 3판 4.5의 마스터 정리는 경우 2를 k = 0(g(n) = Θ(n^(log_b a)))으로만 적고, log^k 일반화는 연습문제 4.6-2로 둔다(연습문제 원문은 walkccc.me CLRS 풀이 사이트로 확인, 정리 번호 4.1은 확인 못 함 `[?]`).
- 기호
  - *ε*: 아주 작아도 되는 양수. "다항식 차이(n^ε배)만큼" 작거나 커야 한다는 뜻.
  - *a·g(n/b) ≤ c·g(n)*: 경우 3의 정칙 조건. 아래 층으로 갈수록 일이 실제로 줄어야 한다.
- 세 경우 사이에 틈이 있다. 예: T(n) = 2T(n/2) + n / log n. g(n)이 n^(log_b a) = n보다 작지만 n^ε배만큼 작지는 않다. 경우 1이 안 맞고, k ≥ 0인 경우 2도 안 맞는다. 이런 식은 MCS 22.4.1의 Akra–Bazzi 공식으로 푼다.
- 경계 조건(T(1)이 얼마인지)과 n/b의 올림·내림은 나누기형의 점근 해를 대개 바꾸지 않는다(MCS 22.4.2 "Two Technical Issues"). MCS가 드는 예외: T(n) = 2T(n/2)는 T(1) = 0이면 해가 0이고, 아니면 Θ(n)이다.
- 빼기형(T(n−1))에는 마스터 정리를 쓸 수 없다. 전개(치환)하거나 특성방정식(MCS 22.3)으로 푼다.

### 5. 선형 점화식 — 지수가 나오는 곳

- T(n) = T(n−1) + T(n−2): 특성방정식 x² = x + 1의 큰 근 φ = (1 + √5)/2 ≈ 1.618이 밑이 된다(MCS 22.3). 피보나치 수는 φ^n/√5에 가장 가까운 정수다.
- 호출 수(메모 없음)는 정확히 2·F(n+1) − 1이다(T(n) = T(n−1) + T(n−2) + 1, T(0)=T(1)=1을 풀면). n이 4 늘면 φ⁴ ≈ 6.854배다.
- T(n) = T(n−1) + n을 전개하면 T(0) + n + (n−1) + … + 1 = T(0) + n(n+1)/2. 등차급수다(T(0) = 0이면 정확히 n(n+1)/2).

### 실험: 점화식의 일을 직접 세기

`Rec06.java` 핵심 — 호출마다 g(n) 만큼 "일"을 더한다.

```java
// T(n) = a T(n/b) + n^d, T(1) = 1
static void dc(long n, int a, int b, int d) {
    work += (d == 0) ? 1 : (d == 1 ? n : n * n);
    if (n <= 1) return;
    for (int i = 0; i < a; i++) dc(n / b, a, b, d);
}
static long fib(int n) { fibCalls++; return n < 2 ? n : fib(n - 1) + fib(n - 2); }
static long sumRec(int[] x, int i) { return i == x.length ? 0 : x[i] + sumRec(x, i + 1); }   // 깊이 n
```

(실험, OpenJDK 21.0.12 Temurin, `eclipse-temurin:21-jdk` 컨테이너 `--network none --cpus=2`, 기본 스택, 2026-10-07. 일·호출 수는 결정적, 시간은 네 번 실행한 범위를 글에)

```text
-- divide & conquer: work / predicted (n = 2^k)
4T(n/2)+n   case1 Θ(n^2) :  n=2^8 work=130,816 ratio=1.996  n=2^10 work=2,096,128 ratio=1.999  n=2^12 work=33,550,336 ratio=2.000
2T(n/2)+n   case2 Θ(n log n) :  n=2^10 work=11,264 ratio=1.100  n=2^15 work=524,288 ratio=1.067  n=2^20 work=22,020,096 ratio=1.050
2T(n/2)+n^2 case3 Θ(n^2) :  n=2^10 work=2,096,128 ratio=1.999  n=2^15 work=2,147,450,880 ratio=2.000  n=2^20 work=2,199,022,206,976 ratio=2.000
T(n/2)+1    case2 Θ(log n) :  n=2^10 work=11 ratio=1.100  n=2^15 work=16 ratio=1.067  n=2^20 work=21 ratio=1.050
-- linear: T(n)=T(n-1)+T(n-2)+1 (fib calls), ratio per +4
  n=20 calls=21,891
  n=24 calls=150,049  x6.854 per +4 (phi^4=6.854)
  n=28 calls=1,028,457  x6.854 per +4 (phi^4=6.854)
  n=32 calls=7,049,155  x6.854 per +4 (phi^4=6.854)
-- linear: T(n)=T(n-1)+n as a loop (ArrayList.remove(0) until empty)
  n=25,000  82 ms  (element moves = n(n-1)/2 = 312,487,500)
  n=50,000  300 ms  (element moves = n(n-1)/2 = 1,249,975,000)
  n=100,000  1370 ms  (element moves = n(n-1)/2 = 4,999,950,000)
  n=200,000  4797 ms  (element moves = n(n-1)/2 = 19,999,900,000)
-- linear recursion depth: T(n)=T(n-1)+1 with depth n
  n=1,000 sum=0
  n=10,000 sum=0
  n=100,000 java.lang.StackOverflowError
  n=1,000,000 java.lang.StackOverflowError
```

- 관찰
  - 마스터 정리의 세 경우 모두 "일 / 예측"이 상수로 수렴했다. 경우 1·3은 정확히 2n² − n(비 → 2), 경우 2는 n(log₂n + 1)(비 = 1 + 1/k)이다. 상수 2는 Θ가 버리는 부분이다.
  - 피보나치 호출 수는 n이 4 늘 때마다 6.8544 → 6.8541 → 6.8541배로 φ⁴ ≈ 6.8541에 수렴했다(같지는 않고 점점 가까워진다). n=32의 7,049,155 = 2·F(33) − 1.
  - `remove(0)` 반복(T(n) = T(n−1) + n)은 n이 2배일 때 시간이 3.4~5.3배였다(집필 네 번: n=200,000에서 4,797~5,343ms. 사실 점검 재실행: 다른 컨테이너와 동시에 돌아 호스트 부하가 높을 때 7,094ms). 이차 함수의 4배 근처다. 30만이면 그 2.25배, 약 11~16초로 어림된다(외삽, 실측 아님). 시간 수치는 이 제한 환경·부하에서의 값이다.
  - 깊이 n 재귀는 n=10,000은 통과, n=100,000에서 `StackOverflowError`였다(기본 스레드 스택). 정확한 한계 깊이는 JIT·프레임 크기에 따라 실행마다 다르다([algorithm/03-recursion](../../algorithm/03-recursion/2-summary.md) 깊이 실험).

## 쓰이는 자료구조·알고리즘

- **분할정복의 비용 분석** — 병합 정렬 2T(n/2) + n, 카라추바 3T(n/2) + n, 빠른 거듭제곱 T(n/2) + 1. [algorithm/24-divide-conquer](../../algorithm/24-divide-conquer/2-summary.md), [algorithm/02-merge-sort](../../algorithm/02-merge-sort/2-summary.md)
- **퀵정렬 최악** — 피벗이 한쪽 끝이면 T(n) = T(n−1) + n = Θ(n²)과 깊이 n. [algorithm/03-quick-sort](../../algorithm/03-quick-sort/2-summary.md), [algorithm/39-randomized-algorithms](../../algorithm/39-randomized-algorithms/2-summary.md)
- **이진 탐색** — T(n) = T(n/2) + 1. [algorithm/06-binary-search](../../algorithm/06-binary-search/2-summary.md)
- **메모이제이션·DP** — 지수 점화를 다항식으로 바꾼다(중복 부분 문제 제거). [algorithm/21-dp-basics](../../algorithm/21-dp-basics/2-summary.md)
- **점근 표기·분할상환** — O·Θ·Ω 정의와 두 배 실험. [algorithm/02-asymptotic-analysis](../../algorithm/02-asymptotic-analysis/2-summary.md)
- **호출 스택** — 재귀 깊이 = 재귀 트리 높이. [algorithm/03-recursion](../../algorithm/03-recursion/2-summary.md)

## 적용 — 풀어나가는 법

### 1. 코드 → 점화식

- 순서
  1. 자기 호출이 몇 번인가 → a(또는 빼기형의 항 개수).
  2. 각 호출의 크기는 → n/b인가 n − c인가.
  3. 호출 밖에서 하는 일은 → g(n). **숨은 일을 센다**: `substring`, `Arrays.copyOfRange`, `List.subList(...)`를 새 리스트로 복사, `remove(0)`는 O(n)이다.
- 나누기형이면 마스터 정리, 빼기형이면 전개(급수)로 푼다.

### 2. 수식으로 어림 → 운영 n에 대입

- T(n) = T(n−1) + n이면 n²/2 단위 일. n=30만 → 4.5×10¹⁰. 위 실험의 원소 이동 속도(약 3~4×10⁹/초, n=200,000 기준 2×10¹⁰회/4.8~7.1초)로 나누면 약 11~16초다(어림).
- 깊이가 n이면 스택 한계(기본 설정에서 수천~수만, [algorithm/03](../../algorithm/03-recursion/2-summary.md))와 비교한다.

### 3. 코드로 확인 — 숨은 복사 없애기

```java
// ✗ 매 단계 꼬리를 복사: T(n) = T(n−1) + n → Θ(n²), 깊이 n
static long sumBad(List<Integer> xs) {
    if (xs.isEmpty()) return 0;
    return xs.get(0) + sumBad(new ArrayList<>(xs.subList(1, xs.size())));
}
// ✓ 인덱스로 넘기고 루프로: T(n) = T(n−1) + 1 → Θ(n), 깊이 1
static long sumGood(List<Integer> xs) {
    long s = 0;
    for (int x : xs) s += x;
    return s;
}
```

- 확인은 두 배 실험으로 한다: n을 2배씩 늘려 시간이 2배(선형), 4배(이차), 제곱(지수 계열)인지 본다([algorithm/02](../../algorithm/02-asymptotic-analysis/2-summary.md) 두 배 실험).

## 장애 시나리오와 대처

### 1. 선형 재귀 깊이 → `StackOverflowError` (⚠ 커리큘럼)

- **현상**: 리스트·트리·연결 체인을 재귀로 도는 코드가 큰 입력에서 죽는다.
- **보이는 형태**: `java.lang.StackOverflowError`, 같은 메서드 프레임 반복(위 실험: 1만 통과, 10만 실패).
- **원인**: 빼기형 점화식 T(n) = T(n−1) + …의 재귀 트리 높이가 n이다. 스택 프레임이 n개 쌓인다.
- **대처**: 루프나 명시적 스택으로 바꾼다. 나누기형으로 바꿀 수 있으면(반씩 나누기) 깊이가 log n이 된다. `-Xss`는 한계를 미룰 뿐이다.

### 2. 숨은 선형 일 → 입력 20만~30만에서 초 단위 지연 (⚠ 커리큘럼)

- **현상**: 테스트(수천 건)에서는 빠르던 처리가 운영(수십만 건)에서 타임아웃.
- **보이는 형태**: 처리 시간이 입력 2배에 약 4배로 는다(위 실험 `remove(0)`: 20만에 약 5~7초). 프로파일러에 `System.arraycopy`·`Arrays.copyOf`가 위에 뜬다.
- **원인**: 매 단계 남은 부분을 복사·이동한다. T(n) = T(n−1) + n = Θ(n²)(T(0) = 0이면 n(n+1)/2).
- **대처**: 인덱스·커서로 넘긴다. 앞에서 빼는 큐는 `ArrayDeque`로 바꾼다(앞 제거 O(1)).
- 참고: 커리큘럼 ⚠의 "지수 점화 → 입력 30만"은 규모로 보면 이 이차형에 해당한다. 지수 점화(아래 3)는 n이 수십일 때 이미 초 단위다(해석).

### 3. 지수 점화 → 작은 n에서 갑자기 타임아웃

- **현상**: n=30에서 수십 ms이던 계산이 n=40에서 초 단위가 된다.
- **보이는 형태**: n이 1 늘 때마다 시간이 약 1.6배(φ). 호출 수가 2·F(n+1) − 1.
- **원인**: T(n) = T(n−1) + T(n−2) — 같은 부분 문제를 거듭 푼다.
- **대처**: 메모이제이션이나 상향식 DP로 Θ(n)([algorithm/21-dp-basics](../../algorithm/21-dp-basics/2-summary.md)). 실측은 [algorithm/03](../../algorithm/03-recursion/2-summary.md)의 n=40 약 2초.

### 4. 퀵정렬 최악 → O(n²)와 깊은 재귀가 동시에

- **현상**: 이미 정렬된 데이터를 직접 구현한 퀵정렬에 넣으면 느리고, 크면 스택 오버플로까지 난다.
- **보이는 형태**: 정렬된(끝 원소 피벗이면 역순 정렬도) 입력에서 느림. `StackOverflowError` 스택에 `quickSort` 반복.
- **원인**: 피벗이 끝 원소면 분할이 n−1과 0으로 갈린다. T(n) = T(n−1) + n — 장애 1과 2가 겹친 꼴이다.
- **대처**: 무작위 피벗(기대 Θ(n log n)), 작은 쪽만 재귀하고 큰 쪽은 루프(깊이 O(log n), CLRS 3판 문제 7-4). 실무는 라이브러리 정렬을 쓴다([algorithm/39](../../algorithm/39-randomized-algorithms/2-summary.md), [algorithm/09-sorting-in-practice](../../algorithm/09-sorting-in-practice/2-summary.md)).

### 5. 마스터 정리를 잘못 적용 → 용량 추정이 차수째 틀림

- **현상**: "n log n이니 10배 데이터면 약 11배"라고 잡았는데 실제로는 약 100배가 걸린다.
- **보이는 형태**: 두 배 실험에서 시간이 2.1배가 아니라 4배로 는다.
- **원인**: 부분 문제 개수 a를 빠뜨렸다. 예: 한 단계에서 반 크기 재귀를 네 번 부르면 4T(n/2) + n = Θ(n²)이다(경우 1). 또는 빼기형에 마스터 정리를 썼다.
- **대처**: 재귀 트리를 두세 층 그려 층별 일이 느는지·같은지·주는지 본다. 두 배 실험으로 확인한다.

## 핵심 문장

- 재귀 코드의 비용은 "몇 개로, 얼마나 작게, 밖에서 얼마나 일하나"로 적은 점화식의 해다.
- 부분 문제가 상수만큼 작아지면(n−1) 깊이가 n이고, 그런 부분 문제가 둘 이상이면 해는 대개 지수다. 비율만큼 작아지면(n/2) 깊이는 log n이다.
- 마스터 정리는 잎의 수 n^(log_b a)와 g(n)을 비교한다. g(n)이 다항식 차이(n^ε배)로 작으면 잎, 같으면 log를 곱하고, 다항식 차이로 크면(정칙 조건 포함) 뿌리가 지배한다. 그 사이 틈(예: n/log n — 층별 일은 늘지만 해는 Θ(n log log n))은 정리 밖이다.
- 마스터 정리는 나누기형에만 쓰고, 세 경우 사이 틈(예: n/log n)에는 Akra–Bazzi를 쓴다.
- `subList` 복사·`remove(0)` 같은 숨은 선형 일이 T(n−1) + 1을 T(n−1) + n으로 바꿔 선형을 이차로 만든다.
- 등비급수는 첫 항이나 마지막 항이 지배하고, 조화수는 ln n 근처다.

## 관련 주제·근거

- 선행
  - [02-induction-and-invariants](../02-induction-and-invariants/2-summary.md) — 점화식의 해를 귀납으로 검증(치환법)
- 후속·연결
  - [04-graph-theory-basics](../04-graph-theory-basics/2-summary.md) — 재귀 트리, 재귀 깊이와 사이클
  - [08-expectation-variance-tails](../08-expectation-variance-tails/2-summary.md) — 조화수와 기댓값(쿠폰 수집)
  - [algorithm/02-asymptotic-analysis](../../algorithm/02-asymptotic-analysis/2-summary.md) · [algorithm/03-recursion](../../algorithm/03-recursion/2-summary.md) · [algorithm/24-divide-conquer](../../algorithm/24-divide-conquer/2-summary.md) · [algorithm/21-dp-basics](../../algorithm/21-dp-basics/2-summary.md) · [algorithm/02-merge-sort](../../algorithm/02-merge-sort/2-summary.md) · [algorithm/03-quick-sort](../../algorithm/03-quick-sort/2-summary.md) · [algorithm/06-binary-search](../../algorithm/06-binary-search/2-summary.md) · [algorithm/39-randomized-algorithms](../../algorithm/39-randomized-algorithms/2-summary.md) · [algorithm/09-sorting-in-practice](../../algorithm/09-sorting-in-practice/2-summary.md)
- 교재
  - MIT 6.042 MCS(2018-06-06판 PDF <https://courses.csail.mit.edu/6.042/spring18/mcs.pdf>) — 14.1(Theorem 14.1.1, 식 14.2 등비급수), 14.4.2 Harmonic Numbers(식 14.21), 14.7 Asymptotic Notation, 22.1 Towers of Hanoi, 22.2 Merge Sort, 22.3 Linear Recurrences, 22.4 Divide-and-Conquer Recurrences(22.4.1 Akra-Bazzi, 22.4.2 Two Technical Issues, Theorem 22.4.2 Master Theorem), 22.5 A Feel for Recurrences(표와 경험칙)
  - CLRS 3판 3장(점근 표기), 4.3 치환법, 4.4 재귀 트리, 4.5 마스터 방법(정리 번호 `[?]`), 연습문제 4.6-2(경우 2의 log^k 일반화), 부록 A(급수), 문제 7-4(퀵정렬 스택 깊이)
- 실험 목록
  - `Rec06.java` — 마스터 정리 세 경우와 T(n/2)+1의 일 카운트(n = 2^8~2^20), 피보나치 호출 수(n = 20~32), `ArrayList.remove(0)` 반복 시간(n = 2.5만~20만), 깊이 n 재귀의 `StackOverflowError`(n = 10³~10⁶). OpenJDK 21.0.12 Temurin 컨테이너(`--network none --cpus=2`), 2026-10-07, 네 번 실행(카운트는 동일, 시간만 범위) + 사실 점검 재실행 1회(카운트 동일, 시간은 호스트 부하로 더 김).
