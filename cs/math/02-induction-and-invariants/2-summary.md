# math/02-induction-and-invariants — 수학적 귀납과 루프 불변식: 정확성과 종료를 따로 논증하기 — 정리 (힌트)

## 해결하는 문제

루프와 재귀가 맞는지 "몇 개 돌려 보니 맞다"로는 알 수 없다. 테스트는 입력 몇 개만 본다. 루프는 반복 횟수만큼 다른 상태를 지나간다.

```text
  for (i = 0; i < n - 1; i++) s += a[i];      ← 마지막 원소 누락 (off-by-one)
  while (lo < hi) { ... lo = mid; ... }        ← 구간이 줄지 않아 무한 루프 (CPU 100%)

  둘 다 컴파일되고, 둘 다 어떤 입력에서는 맞는 답을 낸다
```

쉬운 예: 도미노. "첫 도미노가 넘어진다"와 "k번째가 넘어지면 k+1번째도 넘어진다" 두 가지를 확인하면, 몇 개를 세웠든 끝까지 넘어간다. 하나씩 넘어뜨려 볼 필요가 없다.

똑같은 구조다.\
루프도 "처음에 성립하는 성질"과 "한 번 돌아도 유지되는 성질"을 확인하면, 몇 번 돌든 그 성질이 남는다. 이것이 *루프 불변식*이다. 여기에 "매번 줄어드는 양"을 하나 더 확인하면 끝난다는 것까지 보인다.

실무 예:
- 이진 탐색을 고치다 `hi = mid - 1` 한 글자를 바꿔 특정 키에서만 못 찾는다.
- 페이지네이션 루프가 마지막 페이지에서 같은 커서를 돌려받아 영원히 돈다(예시).
- 배치 합계에서 마지막 행이 빠져 원장과 1건씩 어긋난다.

## 동작·원리

### 1. 수학적 귀납 — 두 단계로 무한을 덮는다

```text
  보통 귀납                                   강한 귀납
  ───────────────────────────                ─────────────────────────────────
  기저:  P(0)                                 기저:  P(0)
  단계:  P(n) ⇒ P(n+1)   (n ≥ 0)              단계:  P(0) ∧ ... ∧ P(n) ⇒ P(n+1)
  결론:  n ≥ 0인 정수 n 각각에서 P(n)           결론:  같음

  P(0) ─⇒ P(1) ─⇒ P(2) ─⇒ P(3) ─⇒ ...        (도미노)
```

- *수학적 귀납(induction)*: 음이 아닌 정수 n에 대한 명제 P(n)을 기저와 단계 두 개로 증명하는 방법(MCS 5.1).
- *기저(base case)*: 가장 작은 n에서 P가 참임을 보이는 부분.
- *귀납 단계(inductive step)*: P(n)을 가정하고 P(n+1)을 보이는 부분. 가정하는 P(n)을 *귀납 가정*이라 한다.
- *강한 귀납(strong induction)*: 단계에서 P(0)부터 P(n)까지 전부를 가정할 수 있는 판(MCS 5.2). 분할 정복처럼 "n/2짜리 부분 문제"에 기대는 재귀를 논증할 때 쓴다.
- 재귀 함수와 귀납의 대응(기저 사례 ↔ 기저, 재귀 호출 ↔ 귀납 가정)은 [algorithm/03-recursion](../../algorithm/03-recursion/2-summary.md) §1에 그림이 있다. 여기서는 루프 쪽을 다룬다.

### 2. 불변식 원리 — 루프는 상태 기계다

```text
  상태 = 루프 변수들의 값 (lo, hi) 등

  시작 상태 q0 ──한 바퀴──> q1 ──한 바퀴──> q2 ──> ... ──> 종료 상태
     I(q0) 참     I 유지        I 유지                    I 참 + 루프 조건 거짓
     (초기화)     (유지)        (유지)                    ⇒ 원하는 결과 (종료)
```

- *상태 기계(state machine)*: 상태 집합과 "한 단계에 어디로 갈 수 있나"(전이)로 정의한 과정(MCS 6.1). 루프 한 바퀴가 전이 한 번이다.
- *보존되는 불변식(preserved invariant)*: 상태에 대한 술어 I로, I(q)가 참이고 q → r이면 I(r)도 참인 것(MCS 정의 6.2.5).
- *불변식 원리(Invariant Principle)*: 보존되는 불변식이 시작 상태에서 참이면, 도달 가능한 상태 각각에서 참이다(MCS 6.2.2). 시작 상태 확인이 기저, 보존 확인이 귀납 단계다 — 귀납을 상태 기계용으로 바꿔 쓴 것이다.
- CLRS 3판 2.1은 같은 것을 루프 불변식의 세 성질로 적는다.
  - *초기화(initialization)*: 첫 반복 전에 참이다.
  - *유지(maintenance)*: 한 반복 전에 참이면 다음 반복 전에도 참이다.
  - *종료(termination)*: 루프가 끝났을 때, 불변식과 종료 조건을 합치면 정확성을 보여 주는 유용한 성질이 된다.

### 3. 부분 정확성 + 종료 = 정확성

```text
  정확성 = 부분 정확성 (끝나면 답이 맞다)     ← 불변식으로
         + 종료         (입력마다 끝난다)     ← 감소하는 척도로

  척도 f(상태) ∈ {0, 1, 2, ...}   매 바퀴 f가 엄격히 줄어든다
      f: 7 → 3 → 1 → 0  (멈춤)       최대 바퀴 수 ≤ f(시작 상태)
```

- *부분 정확성(partial correctness)*: 결과가 나온다면 그 결과가 맞다는 성질. 끝나지 않을 가능성은 다루지 않는다(MCS 6.3, Floyd의 구분).
- *종료(termination)*: 과정이 끝나 결과를 낸다는 성질.
- *척도(derived variable, 감소 변수)*: 상태마다 값을 매기는 함수. 음이 아닌 정수값이고 전이마다 **엄격히** 줄면, 실행 길이는 그 시작값 이하다(MCS 정리 6.3.2). 근거는 *정렬 원리(well ordering)*: 음이 아닌 정수는 무한히 줄어들 수 없다.
  - 흔한 오해: "줄어들거나 그대로인 양이 있으면 끝난다." — **약하게** 감소하는(같을 수 있는) 척도는 종료를 보장하지 않는다(MCS 6.3.3). 같은 값에 머문 채 영원히 돌 수 있다.
- 이진 탐색의 척도는 `hi - lo`(구간 길이)다. 매 바퀴 엄격히 줄어야 한다.

### 4. 이진 탐색 lowerBound의 불변식

```text
  전제: a는 오름차순 정렬 (정렬이 아니면 a[mid] 하나로 앞뒤 구역을 확정할 수 없다)
  불변식 I(lo, hi):   a[0..lo)  는 전부 < key
                      a[hi..n)  는 전부 ≥ key
                      0 ≤ lo ≤ hi ≤ n

   idx   0      lo            hi       n
         [ < key ][  미확인  ][ ≥ key ]

  초기화: lo=0, hi=n → 왼쪽·오른쪽 구역이 비어 I는 공허하게 참
  유지:   a[mid] < key 이면 lo = mid+1  (a[mid]까지 < key 로 확정)
          아니면           hi = mid    (a[mid]부터 ≥ key 로 확정)
  종료:   lo == hi  →  미확인 구역이 비었다 → lo 는 "key 이상인 첫 자리"
  척도:   hi - lo 가 매 바퀴 엄격히 준다 (mid ∈ [lo, hi) 이므로)
```

- 두 버그가 각각 다른 성질을 깬다.
  - `hi = mid - 1`: a[mid]가 key 이상이라는 것만 알았는데, 확인하지 않은 a[mid-1]까지 "≥ key" 구역(a[hi..n))에 넣었다. 그러면 a[mid-1]이 key보다 작을 때 **불변식(부분 정확성)** 이 깨진다. 답이 될 수 있던 자리 mid도 반환 후보에서 빠진다.
  - `lo = mid`: `hi - lo = 1`이면 `mid = lo`라 구간이 그대로다. **척도(종료)** 가 깨진다.
- 반열린 판·닫힌 판의 차이와 `upperBound`·`firstTrue`는 [algorithm/06-binary-search](../../algorithm/06-binary-search/2-summary.md). `(lo + hi) / 2` 오버플로는 [algorithm/01-algorithm-basics](../../algorithm/01-algorithm-basics/2-summary.md) §4.

### 실험: 불변식을 `assert`로 매 반복 검사

코드 핵심(`Inv.java`):

```java
static int lowerBound(int[] a, int key, int variant) {
    int lo = 0, hi = a.length, steps = 0;
    assert inv(a, key, lo, hi) : "초기화에서 깨짐";
    while (lo < hi) {
        int before = hi - lo;                              // 척도
        int mid = lo + (hi - lo) / 2;
        if (a[mid] < key) lo = (variant == 2) ? mid : mid + 1;
        else              hi = (variant == 1) ? mid - 1 : mid;
        steps++;
        assert inv(a, key, lo, hi) : "유지 단계에서 깨짐: ...";
        assert hi - lo < before    : "척도가 줄지 않음: ...";
        if (steps > 1000) throw new IllegalStateException("1000회 넘게 반복 — 무한 루프로 판단");
    }
    return lo;
}
// inv: a[0..lo) 전부 < key, a[hi..n) 전부 >= key, 0 <= lo <= hi <= n 을 직접 훑어 검사 (O(n))
// 입력: 길이 0~7, 값 0~9 정렬 배열, key 0~10, 판마다 10,000회. 답은 선형 탐색과 비교
// 세 판이 Random(42) 하나를 이어 쓰므로 판끼리는 입력이 다르다. 같은 판의 -ea 유무는 같은 입력이다
```

(실험, OpenJDK 21.0.12 Temurin, docker `--cpus=2 --network none`, 2026-10-07 — 같은 시드라 반복 실행해도 같은 수)

`java Inv.java`(assert 꺼짐 — 기본값):

```text
assert 활성(-ea) = false
올바름(lo=mid+1, hi=mid): 0/10000 실패
버그1(hi=mid-1): 2230/10000 실패
버그2(lo=mid): 6478/10000 실패
   첫 오류: IllegalStateException: 1000회 넘게 반복 — 무한 루프로 판단
sum(offByOne=false) = 14
sum(offByOne=true) = 9
```

`java -ea Inv.java`(assert 켬):

```text
assert 활성(-ea) = true
올바름(lo=mid+1, hi=mid): 0/10000 실패
버그1(hi=mid-1): 3973/10000 실패
   첫 오류: AssertionError: 유지 단계에서 깨짐: step=1 lo=0 hi=-1 a=[6] key=6
버그2(lo=mid): 6478/10000 실패
   첫 오류: AssertionError: 척도가 줄지 않음: step=3 lo=0 hi=1 (hi-lo=1)
sum(offByOne=false) = 14
sum(offByOne=true) AssertionError: 종료 시 i=4 != n=5 → 불변식이 a[0..n) 전체를 말하지 않음
```

- 버그1은 assert가 꺼져 있으면 **예외 없이** 2,230회 틀린 답을 냈다. assert를 켜면 3,973회 실패로 잡혔다. 차이 1,743회는 "답은 우연히 맞았지만 불변식은 깨진" 실행이다. 불변식 검사는 답 비교보다 먼저, 원인 가까이에서 터진다.
- 버그1의 첫 오류 `a=[6] key=6`: 한 번에 `hi = 0 - 1 = -1`이 되어 `lo ≤ hi`가 깨졌다.
- 버그2는 `hi - lo = 1`에서 멈췄다. 1000회 상한이 없으면 그 스레드는 끝나지 않는다.
- 합계 루프의 불변식 `s == a[0] + ... + a[i-1]`은 off-by-one 판에서도 매 반복 참이었다. 깨진 것은 **종료 단계**다. 끝났을 때 `i = n - 1`(= 4)이라 불변식이 "앞 n−1개의 합"만 말한다. 원소 하나(값 5)가 빠져 14 대신 9가 나왔다.
- Java `assert`는 기본으로 꺼져 있다(위 첫 줄, JLS 21 §14.10: 꺼진 assert는 "아무 효과가 없다"). 운영에서 불변식을 지키려면 `-ea`에 기대지 말고 명시적 검사(`if (...) throw`)를 쓴다.

### 실험: 척도가 "줄지 않는" 정수 루프

Java 정수 타입과 C `unsigned`는 범위가 유한해서, 감소·증가가 경계에서 반대편으로 넘어간다. 그러면 루프 조건이 거짓이 될 수 없다. C의 부호 있는 정수 오버플로는 넘어간다는 보장도 없는 미정의 동작이다(C11 초안 N1570 §6.5p5, `unsigned`의 나머지 연산은 §6.2.5p9).

(실험, `Wrap.java` 같은 Java 환경 / `unsigned.c` 호스트 gcc 13.3.0 `-Wall -Wextra`, 2026-10-07)

```c
for (unsigned i = n; i >= 0; i--) { ... }      /* n = 3 */
```

```text
unsigned.c:4:28: warning: comparison of unsigned expression in '>= 0' is always true [-Wtype-limits]
unsigned 루프: 6회 넘음, 지금 i=4294967293
byte 루프: 1000회 넘음, 지금 b=-24              (for (byte b = 0; b < 128; b++))
int 루프: 5회 넘음, 지금 i=-2147483645          (while (i <= Integer.MAX_VALUE) i++)
```

- `unsigned`는 0 다음이 4294967295다. `i >= 0`은 거짓이 될 수 없다. gcc는 `-Wextra`(`-Wtype-limits`)에서 경고했다.
- Java `byte`는 −128~127이라 `b < 128`이 거짓이 될 수 없다. 127 다음은 −128이다.
- 척도 논증으로 보면: "i가 매번 1씩 줄어든다"는 수학 정수에서만 맞다. 고정폭 정수에서는 0(또는 MIN) 다음에 큰 값으로 돌아가므로 척도가 아니다.

## 쓰이는 자료구조·알고리즘

- **이진 탐색** — 불변식 "왼쪽 < key ≤ 오른쪽", 척도 `hi - lo` → [algorithm/06-binary-search](../../algorithm/06-binary-search/2-summary.md)
- **투 포인터** — 불변식 "버린 쌍 중에는 답이 없다", 척도 `j - i` → [algorithm/08-two-pointers](../../algorithm/08-two-pointers/2-summary.md)
- **재귀 정당성** — 강한 귀납 = 재귀, 척도 = 입력 크기 → [algorithm/03-recursion](../../algorithm/03-recursion/2-summary.md)
- **정렬** — 삽입 정렬의 "앞 j−1개는 정렬됨"(CLRS 2.1), 병합 정렬의 재귀 정당성 → [algorithm/02-merge-sort](../../algorithm/02-merge-sort/2-summary.md)
- **자료구조 불변식** — 힙 속성, BST 순서, 레드-블랙 균형 규칙은 "연산 전후로 보존되는 불변식"이다 → [data-structure/07-heap](../../data-structure/07-heap/2-summary.md), [data-structure/16-red-black-tree](../../data-structure/16-red-black-tree/2-summary.md)
- **속성 기반 테스트** — 불변식을 무작위 입력으로 검사 → [testing/14-property-based-testing](../../testing/14-property-based-testing/2-summary.md)

## 적용 — 풀어나가는 법

### 1. 루프를 쓰기 전에 세 줄을 적는다

```java
// 불변식: a[0..lo) < key, a[hi..n) >= key
// 척도:   hi - lo  (매 바퀴 엄격히 감소, 0 이상)
// 종료 시: lo == hi → lo 가 답
int lo = 0, hi = a.length;
while (lo < hi) { ... }
```

- 불변식이 한 문장으로 안 써지면 루프 설계가 아직 덜 된 것이다.
- 갱신 줄마다 "이 대입 뒤에도 불변식이 참인가"를 확인한다. `hi = mid`와 `hi = mid - 1`의 차이는 여기서 보인다.

### 2. 증상 → 어느 성질이 깨졌나

| 증상 | 깨진 성질 | 확인할 것 |
|---|---|---|
| 특정 입력에서 틀린 답, 예외 없음 | 유지(부분 정확성) | 각 대입 뒤 불변식 |
| 마지막·첫 원소만 빠짐 | 종료 단계(종료 조건 + 불변식이 결과를 말하지 않음) | 끝났을 때 인덱스 값 |
| 스레드가 안 끝남, CPU 100% | 척도(종료) | 매 바퀴 엄격히 주는 양이 있나, 정수 경계 |
| 첫 반복부터 틀림 | 초기화 | 빈 입력·길이 1 |

### 3. 코드로 확인

- 개발·테스트에서는 불변식을 `assert`로 두고 `-ea`로 돌린다(Maven Surefire `enableAssertions` 기본 `true`, Gradle `Test.enableAssertions` `java` 플러그인 기본 `true` — 각 문서. 그래서 테스트에서는 켜지고 운영 JVM에서는 꺼진 채로 돈다).
- 운영 경로에서 지켜야 하는 것(종료 상한, 입력 범위)은 명시적 검사로 쓴다.

```java
int guard = 0;
while (cursor != null) {
    Page p = client.fetch(cursor);
    if (Objects.equals(p.nextCursor(), cursor))      // 척도가 줄지 않음 = 진행 없음
        throw new IllegalStateException("cursor did not advance: " + cursor);
    if (++guard > MAX_PAGES) throw new IllegalStateException("page limit exceeded");
    cursor = p.nextCursor();
}
```

- 외부 시스템이 척도를 정할 때(커서·재시도 횟수)는 "진행했나"와 "상한"을 둘 다 둔다. 외부 응답이 척도를 줄여 준다는 보장은 내 코드 밖에 있다.

## 장애 시나리오와 대처

### 1. off-by-one — 마지막 원소 누락 (⚠ 커리큘럼)

- **현상**: 일별 정산 합계가 원장보다 매번 마지막 한 건만큼 적다. 또는 페이지 마지막 항목이 화면에 안 나온다.
- **보이는 형태**: 예외 없음. 대사(reconciliation) 차이 = 마지막 원소 값. 테스트 데이터가 1건이면 0이 나와 잡히지 않을 수 있다.
- **원인**: 루프 경계 `i < n - 1`. 불변식 "s = 앞 i개의 합"은 매 반복 참이지만, n ≥ 1이면 끝났을 때 i = n − 1이라 결과가 n개 전체를 말하지 않는다(실험 `sum(offByOne=true)` = 9 vs 14).
- **대처**: 반열린 구간 `[0, n)` 관례로 통일하고 `i < n`을 쓴다. 가능하면 인덱스 루프 대신 `for-each`·`stream().mapToLong(...).sum()`을 쓴다. 테스트에 길이 0·1·2 입력을 넣는다.

### 2. 종료 척도 부재 → 무한 루프·CPU 100% (⚠ 커리큘럼)

- **현상**: 특정 요청 뒤 서버 CPU 한 코어가 100%에 붙고, 해당 요청은 타임아웃된다. 스레드 풀이 하나씩 잠식된다.
- **보이는 형태**: `jstack`에서 같은 메서드의 같은 줄에 `RUNNABLE`로 머무는 스레드. 요청 로그에는 완료 기록이 없다.
- **원인**: 구간이 줄지 않는 갱신(`lo = mid`), 커서가 진행하지 않는 페이지네이션, 정수 경계를 넘어 돌아가는 카운터(실험 `Wrap.java`·`unsigned.c`).
- **대처**: 척도를 코드 주석으로 적고, 갱신 줄이 척도를 엄격히 줄이는지 확인한다. 외부 입력에 기대는 루프에는 반복 상한과 "진행 없음" 검사를 둔다(적용 §3). C에서는 `-Wextra` 경고를 오류로 다룬다.

### 3. 이진 탐색이 특정 키에서만 못 찾는다

- **현상**: 존재하는 키 조회가 가끔 "없음"을 낸다.
- **보이는 형태**: 예외 없음. 실험에서 `hi = mid - 1` 판은 10,000회 중 2,230회 틀린 답을 냈다.
- **원인**: 확인하지 않은 a[mid-1]을 "≥ key" 구역에 넣고, 답 후보 mid를 반환 후보에서 뺐다. 불변식의 유지 단계가 깨졌다.
- **대처**: 반열린 판(`hi = mid`)과 닫힌 판(`hi = mid - 1`, 루프 `lo <= hi`) 중 하나로 통일한다. 불변식 assert를 넣은 테스트를 무작위 입력으로 돌린다. 직접 짜지 말고 `Arrays.binarySearch`·`Collections.binarySearch`를 쓰는 것도 방법이다(단, 중복 키에서 어느 자리를 돌려줄지는 보장하지 않는다 — Javadoc).

### 4. 테스트는 통과했는데 운영에서 불변식이 깨진다 — `assert` 꺼짐

- **현상**: 테스트에서 잡히던 불변식 위반이 운영에서는 조용히 지나가 데이터가 틀어진다.
- **보이는 형태**: 운영 로그에 `AssertionError`가 없다. JVM 인자에 `-ea`가 없다.
- **원인**: Java `assert`는 기본으로 꺼져 있다(실험 첫 줄 `assert 활성(-ea) = false`). 꺼진 assert는 아무 효과가 없다(JLS §14.10).
- **대처**: 운영에서 지켜야 하는 불변식은 `if (!inv) throw new IllegalStateException(...)`으로 쓴다. 비싼 검사(O(n) 훑기)는 테스트에만 둔다.

## 핵심 문장

- 귀납은 "기저 + 한 단계"로 무한히 많은 경우를 덮는다. 루프 불변식은 그 귀납을 루프 상태에 적용한 것이다.
- 루프의 정확성 = 부분 정확성(불변식: 초기화·유지·종료) + 종료(엄격히 줄어드는 음이 아닌 척도).
- `hi = mid - 1`은 불변식을, `lo = mid`는 척도를 깬다. 증상(틀린 답 vs 무한 루프)으로 어느 쪽인지 가른다.
- off-by-one은 대개 유지가 아니라 종료 단계의 문제다. 끝났을 때 불변식이 전체를 말하는지 본다.
- 고정폭 정수의 감소는 경계에서 반대편으로 넘어가므로 척도가 되지 못할 수 있다.
- Java `assert`는 기본으로 꺼져 있다. 운영에서 지킬 불변식은 명시적 검사로 쓴다.

## 관련 주제·근거

- 선행: [01-propositional-logic](../01-propositional-logic/2-summary.md) — 불변식은 술어다
- 후속: [03-sets-relations-orders](../03-sets-relations-orders/2-summary.md) · 점화식·마스터 정리 등 → [06-recurrences-and-asymptotics](../06-recurrences-and-asymptotics/2-summary.md)
- 연결
  - [algorithm/03-recursion](../../algorithm/03-recursion/2-summary.md) — 재귀 = 귀납의 코드
  - [algorithm/06-binary-search](../../algorithm/06-binary-search/2-summary.md) · [algorithm/08-two-pointers](../../algorithm/08-two-pointers/2-summary.md) · [algorithm/01-algorithm-basics](../../algorithm/01-algorithm-basics/2-summary.md)(중간값 오버플로)
  - [algorithm/02-merge-sort](../../algorithm/02-merge-sort/2-summary.md) · [data-structure/07-heap](../../data-structure/07-heap/2-summary.md) · [data-structure/16-red-black-tree](../../data-structure/16-red-black-tree/2-summary.md)
  - [testing/14-property-based-testing](../../testing/14-property-based-testing/2-summary.md)
- 교재
  - MCS(2018-06-06 개정판 PDF <https://courses.csail.mit.edu/6.042/spring18/mcs.pdf>) — 5.1 보통 귀납, 5.2 강한 귀납, 6.1 상태 기계, 6.2 불변식 원리(정의 6.2.4·6.2.5, 6.2.2 원리 서술 — Floyd), 6.3 부분 정확성과 종료(정리 6.3.2 감소 변수, 6.3.3 약한 감소는 종료를 보장하지 않음). 장 번호는 이 PDF의 목차 기준.
  - CLRS 3판 2.1 Insertion sort — 루프 불변식의 초기화·유지·종료(본문 미열람, 세 성질의 서술은 강의 자료 교차 확인: <https://web.stanford.edu/class/archive/cs/cs161/cs161.1168/lecture1.pdf>, <https://walkccc.me/CLRS/Chap02/2.1/>)
- 명세·문서
  - JLS SE 21 §14.10 The `assert` Statement <https://docs.oracle.com/javase/specs/jls/se21/html/jls-14.html>
  - Maven Surefire `test` mojo — `enableAssertions` Default `true` <https://maven.apache.org/surefire/maven-surefire-plugin/test-mojo.html> · Gradle DSL `Test.enableAssertions` — Default with `java` plugin `true` <https://docs.gradle.org/current/dsl/org.gradle.api.tasks.testing.Test.html>
  - `Arrays.binarySearch` Javadoc — 같은 값이 여러 개면 어느 것을 찾을지 보장하지 않음
- 실험 목록(이 노트)
  - `Inv.java` — lowerBound 올바름·`hi=mid-1`·`lo=mid` 세 판을 무작위 10,000회(Random(42)), 불변식·척도 assert, `-ea` 유무 비교, 합계 루프 off-by-one. OpenJDK 21.0.12 Temurin, docker(`--cpus=2 --network none`), 2026-10-07.
  - `Wrap.java` — `byte`·`int` 경계 넘김 루프(반복 상한으로 중단). 같은 환경.
  - `unsigned.c` — `unsigned i >= 0` 루프, gcc 13.3.0 `-Wall -Wextra` 경고. 호스트.
