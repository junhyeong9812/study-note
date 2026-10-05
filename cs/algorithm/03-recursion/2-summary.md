# algorithm/03-recursion — 재귀: 귀납의 코드, 기저·축소·꼬리 재귀 — 정리 (힌트)

## 해결하는 문제

어떤 문제는 "같은 모양의 더 작은 문제"로 자연스럽게 쪼개진다.

```text
  폴더 크기 = 이 폴더의 파일 크기 합 + (하위 폴더 각각의 크기)
                                      └─ 같은 질문, 더 작은 폴더
```

- 반복문으로 쓰려면 "아직 안 본 하위 폴더 목록"을 직접 들고 다녀야 한다.
- 재귀로 쓰면 그 목록을 언어의 **호출 스택**이 대신 들고 다닌다. 코드가 문제 정의와 같은 모양이 된다.
  - *재귀(recursion)*: 함수가 자기 자신을 (더 작은 입력으로) 호출하는 것.
  - *호출 스택(call stack)*: 함수를 호출할 때마다 지역 변수·돌아갈 위치를 담은 *프레임*을 하나씩 쌓는 메모리 영역. 함수가 끝나면 그 프레임을 걷어낸다.

쉬운 예: 러시아 인형(마트료시카)을 열어 가장 작은 인형을 찾는다.
- 인형을 연다 → 안에 인형이 있으면 같은 일을 반복한다 → 더 열 게 없으면 그것이 답이다.
- "더 열 게 없으면 멈춘다"가 *기저 사례*, "한 겹 작은 인형에 같은 일"이 *축소 단계*다.

똑같은 구조다.\
실무 예:
- 중첩된 JSON·XML을 재귀로 읽는 코드(재귀 하강(recursive descent) 파서, 객체로 바꾸는 역직렬화)는 중첩 한 겹마다 재귀 한 단계를 쓴다. 그래서 깊이 중첩된 입력이 스택을 넘길 수 있다. Jackson은 스트리밍 파서(jackson-core)가 중첩을 문맥 객체에 따로 기록하고, `StackOverflowError`는 jackson-databind 쪽 재귀에서 난다(jackson-core PR #943 설명). 2.15부터 core에 중첩 깊이 상한(기본 1000)을 두어, 상한을 크게 올리지 않는 한 `StackOverflowError` 대신 `StreamConstraintsException`을 던진다(CVE-2025-52999).
- 트리·그래프 순회(DFS), 병합·퀵 정렬 같은 분할정복, 백트래킹은 재귀로 쓰는 것이 기본형이다.

이 주제가 답하는 질문은 셋이다.
1. 재귀가 **맞다**는 것을 어떻게 보이나 → 수학적 귀납과 같은 논증.
2. 재귀가 **얼마나 깊어지나**, 스택이 넘치면 무엇이 보이나 → `StackOverflowError`.
3. 재귀가 **얼마나 느려지나** → 점화식으로 센다. 피보나치처럼 중복 부분문제가 쌓이면 지수 시간이 될 수 있다.

기초(팩토리얼·피보나치 정의, 탈출 조건)는 원본 [foundations/data-structures-basics §7](../../foundations/data-structures-basics/README.md)에 있다. 이 노트는 그 위에 정확성 논증·깊이 한계·비용·변환을 채운다.

## 동작·원리

### 1. 재귀 = 귀납의 코드

```text
  수학적 귀납                          재귀 함수
  ─────────────────────────────       ─────────────────────────────────
  P(0)이 참이다            (기저)  ↔   if (n == 0) return 1;      기저 사례
  P(n-1) ⇒ P(n)            (단계)  ↔   return n * fact(n - 1);    축소 + 결합
  ∴ 모든 n ≥ 0에서 P(n)              ∴ 모든 n ≥ 0에서 fact(n) = n!
```

- 재귀 함수가 맞으려면 세 가지를 확인한다.
  - **기저 사례**가 있고, 거기서 답이 맞다.
  - 재귀 호출의 입력이 **기저 쪽으로 엄격히 작아진다**(n → n−1, 구간 → 반 구간). 이 크기는 허용한 입력 안에서 0 아래로 내려가지 않아야 한다(예: `fact`는 n ≥ 0만 받는다). 그래야 무한히 작아질 수 없어 종료가 보장된다.
  - 더 작은 호출이 맞다고 **가정하면**, 그 결과를 합친 값이 맞다.
    - 흔한 오해: "재귀 호출이 어떻게 도는지 끝까지 따라가 봐야 맞는지 안다." — 귀납 가정 덕분에 한 단계만 확인하면 된다. 끝까지 따라가는 것은 디버깅 도구지 증명 방법이 아니다.
  - *기저 사례(base case)*: 더 쪼개지 않고 바로 답하는 입력.
  - *축소 단계(reduction step)*: 문제를 더 작은 같은 문제로 바꾸는 단계.
- 귀납 자체(강한 귀납, 루프 불변식)는 math 영역 02-induction-and-invariants 주제다(아직 미작성 — [math 커리큘럼](../../math/README.md)).

### 2. 호출 스택 — 재귀가 실제로 쓰는 메모리

`fact(3)`을 부르면 스택이 이렇게 자란다.

```text
  호출할 때 (아래로 쌓임)              돌아올 때 (위에서부터 걷힘)
  ┌──────────────────────┐
  │ main                 │
  ├──────────────────────┤
  │ fact(3)  n=3  ⇣대기   │           fact(3) = 3 * 2 = 6  ← 마지막
  ├──────────────────────┤
  │ fact(2)  n=2  ⇣대기   │           fact(2) = 2 * 1 = 2
  ├──────────────────────┤
  │ fact(1)  n=1  ⇣대기   │           fact(1) = 1 * 1 = 1
  ├──────────────────────┤
  │ fact(0)  n=0  → 1     │           fact(0) = 1          ← 처음
  └──────────────────────┘
       fact 프레임 = 4개 (재귀 깊이 n+1), main까지 세면 5개
```

- 프레임 하나에는 인자, 지역 변수, 돌아갈 주소가 들어간다. 지역 변수가 많을수록 프레임이 크다.
- 스택 크기는 스레드마다 정해져 있다. HotSpot의 `-Xss`(문서: `-XX:ThreadStackSize`와 비슷한 옵션) 기본값은 Linux/x64·macOS/x64에서 1024KB, Linux/AArch64·macOS/AArch64에서 2048KB다(Oracle JDK 21 `java` 도구 문서).
  - 실험 컨테이너에서 `java -XX:+PrintFlagsFinal -version`으로 본 값: `ThreadStackSize = 1024`(KB), `MaxJavaStackTraceDepth = 1024`.
- 기저 사례가 없거나, 있어도 입력이 기저 쪽으로 줄지 않으면 프레임이 끝없이 쌓인다. 한도에 닿으면 JVM은 `java.lang.StackOverflowError`를 던진다.
  - `StackOverflowError`는 `Error`의 하위 클래스다. `catch (Exception e)`로는 잡히지 않는다.

### 실험: 재귀 깊이 한계는 스택 크기와 프레임 크기로 정해진다

```java
public class Depth {
    static int depth = 0;
    static void down() { depth++; down(); }                 // 기저 조건 없음
    static long fat(long a, long b, long c, long d) {        // 지역 변수가 많은 프레임
        depth++; long x = a + b, y = c + d;
        return fat(x, y, a, b) + x + y;
    }
    public static void main(String[] args) {
        String mode = args.length > 0 ? args[0] : "thin";
        for (int run = 0; run < 3; run++) {
            depth = 0;
            try { if (mode.equals("thin")) down(); else fat(1, 2, 3, 4); }
            catch (StackOverflowError e) { System.out.println(mode + " run" + run + " depth=" + depth); }
        }
    }
}
```

인터프리터만 쓴 경우(`-Xint`, JIT 끔) — 결과가 실행마다 같다.

(실험, OpenJDK 21.0.12 Temurin, docker `--cpus=2`, `java -Xint -Xss<크기> Depth.java`, 2026-10-05)

```text
-Xss256k | thin run0 depth=1782  | fat run0 depth=852
-Xss512k | thin run0 depth=4761  | fat run0 depth=2277
-Xss1m   | thin run0 depth=10718 | fat run0 depth=5126
-Xss2m   | thin run0 depth=22634 | fat run0 depth=10825
-Xss4m   | thin run0 depth=46465 | fat run0 depth=22222
```

- 스택을 두 배로 늘리면 깊이도 약 두 배(2.1~2.7배)다. 고정 오버헤드가 있어 정확히 두 배는 아니다.
- 프레임이 큰 `fat`은 같은 스택에서 `thin`의 약 절반 깊이에서 넘친다.

JIT를 켠 기본 모드에서는 값이 흔들린다.

(실험, 같은 환경, `java -Xss1m Depth.java thin`을 세 번 실행)

```text
thin run0 depth=20213 thin run1 depth=23582 thin run2 depth=23582
thin run0 depth=19415 thin run1 depth=23582 thin run2 depth=41224
thin run0 depth=22114 thin run1 depth=23582 thin run2 depth=23582
```

- 같은 코드·같은 `-Xss1m`인데 깊이가 19,415~41,224로 실행마다 다르다(사실 점검 재실행 세 번: 첫 회 20,549~22,393, 이후 23,582 — 같은 환경).
- 해석: JIT가 컴파일한 프레임은 인터프리터 프레임보다 작고, 컴파일 시점이 실행마다 다르다. 그래서 "몇 단계까지 된다"를 숫자로 믿고 설계하면 안 된다. 깊이가 입력 크기에 비례하면 그 자체가 위험 신호다.

### 3. 꼬리 재귀 — 이론상 스택이 필요 없지만 Java는 지우지 않는다

```text
  일반 재귀: 호출 뒤에 할 일이 남는다        꼬리 재귀: 호출이 마지막 일이다
  sum(n) = n + sum(n-1)                   sumTail(n, acc) = sumTail(n-1, acc+n)
           └ 돌아와서 더해야 함 → 프레임 유지            └ 돌아와서 할 일 없음 → 프레임 재사용 가능

  꼬리 호출 제거(TCO)를 하는 언어:  [sumTail n=3] → 같은 자리에서 [n=2] → [n=1] → 답  (스택 1칸)
  HotSpot(Java):                   [n=3][n=2][n=1][n=0] … 프레임이 그대로 쌓인다
```

- *꼬리 호출(tail call)*: 함수의 마지막 동작이 다른 함수 호출이고, 그 결과를 그대로 돌려주는 호출.
- *꼬리 호출 제거(tail call elimination, TCO)*: 꼬리 호출이면 현재 프레임을 재사용해 스택이 자라지 않게 하는 컴파일러·런타임 최적화.
  - 흔한 오해: "꼬리 재귀로 바꾸면 Java에서도 깊이 제한이 사라진다." — 아래 실험처럼 HotSpot(OpenJDK 21)은 꼬리 재귀도 프레임을 쌓는다.
- 언어마다 다르다.
  - Kotlin: `tailrec` 한정자를 붙이고 조건(마지막 동작이 자기 호출, `try/catch/finally` 안이 아님, `open`이 아님)을 지키면 컴파일러가 반복문으로 바꾼다(Kotlin 문서 "Tail recursive functions").
  - JavaScript: ES2015 명세는 strict 모드의 proper tail call을 정의한다. 그러나 V8(Node.js 22)에서는 아래 실험처럼 스택이 넘친다.

### 실험: 꼬리 재귀 vs 반복

```java
static long sumTail(long n, long acc) {          // 꼬리 위치 호출
    if (n == 0) return acc;
    return sumTail(n - 1, acc + n);
}
static long sumLoop(long n) {                    // 같은 계산을 반복문으로
    long acc = 0;
    while (n > 0) { acc += n; n--; }
    return acc;
}
```

(실험, OpenJDK 21.0.12 Temurin, docker `--cpus=2`, `java Tail.java <n>`, 기본 `-Xss`(1024KB), 2026-10-05)

```text
n=10000:    loop  50005000
            tail  50005000
n=1000000:  loop  500000500000
            Exception in thread "main" java.lang.StackOverflowError
            	at Tail.sumTail(Tail.java:5)
            	at Tail.sumTail(Tail.java:5)
            	...
```

- n=1,000,000에서 반복판은 답을 내고, 꼬리 재귀판은 넘친다. `-Xss64m`에서도 넘쳤고 `-Xss256m`에서야 `tail 500000500000`이 나왔다(같은 환경).
- 스택 트레이스의 `at` 줄은 1,019개였고 `main` 프레임이 보이지 않았다. 트레이스가 `MaxJavaStackTraceDepth`(기본 1024)에서 잘린 것이다. 1,024가 아니라 1,019인 것은 `java Tail.java` 소스 실행기가 실행기 몫 프레임 수만큼 트레이스 끝을 더 잘라 내기 때문이다(jdk21u `com/sun/tools/javac/launcher/Main.java`의 `invocationFrames`). `javac`로 컴파일해 `java Tail 1000000`으로 돌리면 1,024줄이었다(정합 점검 재실행, 같은 환경). 그래서 **어디서 재귀가 시작됐는지가 트레이스에 안 나올 수 있다.**

(실험, `node:22-alpine` Node v22.23.2, `"use strict"` 같은 꼬리 재귀 `sumTail`, 2026-10-05)

```text
10000 RangeError: Maximum call stack size exceeded
100000 RangeError: Maximum call stack size exceeded
1000000 RangeError: Maximum call stack size exceeded
```

- 인자 없는 무한 재귀는 같은 환경에서 깊이 12,555에서 `RangeError`가 났다(세 번 같음).

### 4. 중복 부분문제 — 재귀가 지수 시간이 되는 경우

```text
  fib(5)
  ├─ fib(4)
  │  ├─ fib(3)
  │  │  ├─ fib(2) ─ fib(1), fib(0)
  │  │  └─ fib(1)
  │  └─ fib(2) ─ fib(1), fib(0)        ← 이미 위에서 계산했다
  └─ fib(3)                            ← 통째로 다시 계산
     ├─ fib(2) ─ fib(1), fib(0)
     └─ fib(1)

  같은 fib(k)를 여러 번 부른다 → 호출 수가 fib(n)에 비례해 자란다 (≈ 1.618^n)
```

- *중복 부분문제(overlapping subproblems)*: 재귀 트리에서 같은 입력의 호출이 여러 번 나오는 것.
- 해법은 두 가지다.
  - *메모이제이션(memoization)*: 처음 계산한 값을 표에 적어 두고 다시 부르면 표에서 꺼낸다. 재귀 모양을 유지한다.
  - *상향식 DP(bottom-up)*: 작은 것부터 표를 채운다. 재귀도 스택도 없다. → [algorithm/21-dp-basics](../21-dp-basics/2-summary.md)
- 중복이 없는 재귀(병합 정렬처럼 서로 겹치지 않는 반으로 나누기)는 메모이제이션이 소용없다. 그쪽은 분할정복이다 → [algorithm/24-divide-conquer](../24-divide-conquer/2-summary.md).

### 실험: 호출 수와 시간이 n이 2 늘 때마다 약 2.6배

```java
static long calls;
static long fib(int n) { calls++; return n < 2 ? n : fib(n - 1) + fib(n - 2); }
static long[] memo;
static long fibMemo(int n) {
    calls++;
    if (n < 2) return n;
    if (memo[n] != 0) return memo[n];
    return memo[n] = fibMemo(n - 1) + fibMemo(n - 2);
}
```

(실험, OpenJDK 21.0.12 Temurin, docker `--cpus=2`, `java Fib.java`, 워밍업 `fib(25)` 1회, 2026-10-05 — 시간은 세 번 실행 중 첫 번째, 세 번의 범위는 아래 글에)

```text
n=30 fib=832040 naiveCalls=2,692,537 time=18ms memoCalls=59
n=32 fib=2178309 naiveCalls=7,049,155 time=43ms memoCalls=63
n=34 fib=5702887 naiveCalls=18,454,929 time=94ms memoCalls=67
n=36 fib=14930352 naiveCalls=48,315,633 time=251ms memoCalls=71
n=38 fib=39088169 naiveCalls=126,491,971 time=759ms memoCalls=75
n=40 fib=102334155 naiveCalls=331,160,281 time=1985ms memoCalls=79
```

- 호출 수는 결정적이다. n이 2 늘 때마다 2.618배(= 황금비 φ ≈ 1.618의 제곱)다. 7,049,155 / 2,692,537 ≈ 2.618.
- 시간은 실행마다 다르다(n=40: 1,723~1,985ms, 세 번 / 사실 점검 재실행 세 번 1,683~1,805ms). 비율은 대략 같은 방향이다.
- 메모이제이션판은 호출 수가 2n−1(n=40에서 79)로 선형이다.

### 5. 재귀 → 반복 변환

```text
  재귀 DFS (언어 호출 스택)                명시적 스택 (힙의 ArrayDeque)
  size(x):                               st.push(root)
    if x == null: return 0               while st not empty:
    return 1 + size(x.left)                x = st.pop(); n++
             + size(x.right)               push(x.right); push(x.left)  (null이 아닐 때만)
  깊이 한계 = -Xss                        깊이 한계 = 힙(-Xmx)
```

- 꼬리 재귀는 "인자 갱신 + `while`"로 그대로 바뀐다(위 `sumLoop`).
- 꼬리가 아닌 재귀(트리 순회)는 호출 스택이 하던 일을 **명시적 스택**으로 옮긴다. 스택이 힙에 있으니 깊이가 힙 크기까지 늘어난다.

### 실험: 한쪽으로 늘어선 BST

정렬된 키 0, 1, 2, …를 순서대로 BST에 넣으면 오른쪽으로만 이어진 사슬이 된다(→ [data-structure/06-binary-search-tree](../../data-structure/06-binary-search-tree/2-summary.md)).

(실험, OpenJDK 21.0.12 Temurin, docker `--cpus=2`, 기본 `-Xss`, `java Chain.java <n>`, 2026-10-05)

```text
n=1000:     iter size=1000
            rec  size=1000
n=1000000:  iter size=1000000
            rec  StackOverflowError
```

- 같은 트리, 같은 답인데 재귀판만 죽는다. 테스트(1,000개)에서는 차이가 안 보인다.

참고: CPython 3.12는 재귀 깊이 상한을 따로 둔다. `sys.getrecursionlimit()`이 1000이었고, 깊이 5000 재귀에서 `RecursionError: maximum recursion depth exceeded`가 났다(호스트 Python 3.12.3).

## 쓰이는 자료구조·알고리즘

- **이 주제가 쓰는 하위 구조**
  - 호출 스택 = LIFO 스택이다 → [data-structure/03-stack](../../data-structure/03-stack/2-summary.md). 재귀 → 반복 변환은 이 스택을 직접 들고 다니는 것이다.
  - 메모이제이션 표: 배열 또는 해시맵 → [data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md)
- **이 주제를 쓰는 곳(🔧)**
  - DFS·위상 정렬 → [algorithm/12-dfs](../12-dfs/2-summary.md) (직선 그래프에서 같은 `StackOverflowError`)
  - 분할정복(병합·퀵 정렬, 마스터 정리) → [algorithm/24-divide-conquer](../24-divide-conquer/2-summary.md), [02-merge-sort](../02-merge-sort/2-summary.md), [03-quick-sort](../03-quick-sort/2-summary.md)
    - 퀵 정렬은 작은 쪽만 재귀하고 큰 쪽은 반복으로 돌려 깊이를 O(log n)으로 묶는다(CLRS 7장 문제 7-4의 tail-recursive quicksort).
  - 백트래킹 → [algorithm/13-backtracking](../13-backtracking/2-summary.md), DP → [algorithm/21-dp-basics](../21-dp-basics/2-summary.md)
  - 파서(재귀 하강): JSON·식 계산기·SQL 파서. 중첩 깊이 = 재귀 깊이.
  - 트리 구조 순회: BST·파일 시스템 디렉터리·DOM.

## 적용 — 풀어나가는 법

### 1. 재귀를 설계하는 순서

```text
  ① 입력의 "크기"를 정한다         (n, 구간 길이, 트리 높이, 남은 문자열 길이)
  ② 가장 작은 크기의 답을 쓴다      → 기저 사례
  ③ 크기 n을 더 작은 크기로 줄인다   → 축소 단계 (엄격히 작아지는지 확인)
  ④ 작은 답이 맞다고 가정하고 합친다  → 결합
  ⑤ 깊이와 중복을 따진다           → 깊이 ∝ n이면 반복으로, 중복이 있으면 메모
```

쉬운 예(코테): 이진 탐색 재귀판.

```java
// 불변식: 답이 있다면 [lo, hi) 안에 있다
static int search(int[] a, int key, int lo, int hi) {
    if (lo >= hi) return -1;                   // 기저: 빈 구간
    int mid = lo + (hi - lo) / 2;              // (lo+hi)/2는 오버플로 가능(Bloch 2006)
    if (a[mid] == key) return mid;
    return a[mid] < key ? search(a, key, mid + 1, hi)   // 구간이 엄격히 줄어든다
                        : search(a, key, lo, mid);
}
```

- 깊이는 log₂ n이라 재귀로 둬도 된다. 반면 연결 리스트 길이 재기처럼 깊이가 n인 재귀는 반복으로 바꾼다.

실무 예: 카테고리 트리(부모 id로 이어진 행)를 펼친다.

```java
// 깊이가 데이터에 달려 있다 → 명시적 스택 + 방문 집합(순환 데이터 방어)
List<Category> flatten(Category root) {
    List<Category> out = new ArrayList<>();
    Deque<Category> st = new ArrayDeque<>();
    Set<Long> seen = new HashSet<>();
    st.push(root);
    while (!st.isEmpty()) {
        Category c = st.pop();
        if (!seen.add(c.id())) continue;       // 잘못된 데이터(A→B→A)로 무한 반복 방지
        out.add(c);
        for (Category ch : c.children()) st.push(ch);
    }
    return out;
}
```

- 재귀로 쓰면 데이터 오류(자기 자신을 부모로 가리키는 행)가 곧 무한 재귀 → `StackOverflowError`다.

### 2. 깊이 한계를 다루는 선택지

| 선택 | 언제 | 대가 |
|---|---|---|
| 반복·명시적 스택으로 변환 | 깊이가 입력 크기에 비례할 때 | 코드가 길어진다 |
| 깊이 상한을 두고 거부 | 외부 입력(JSON 중첩 등) | 정상 입력의 상한을 정해야 한다 |
| 큰 스택의 전용 스레드 `new Thread(null, r, "deep", 512L << 20)` | 알고리즘상 재귀가 자연스럽고 깊이 상한을 안다 | `Thread` 생성자 문서는 플랫폼이 `stackSize`를 무시할 수 있다고 적는다 |
| `-Xss`를 전역으로 올림 | 거의 권하지 않음 | 모든 스레드의 스택 예약이 커진다 |

### 3. 진단 — `StackOverflowError`를 읽는 법

```text
Exception in thread "main" java.lang.StackOverflowError
	at Tail.sumTail(Tail.java:5)      ← 같은 줄이 반복 = 자기 재귀
	at Tail.sumTail(Tail.java:5)
	...                               ← 1,024줄 근처에서 잘려 시작점이 안 보일 수 있다
```

- 같은 메서드가 반복되면 직접 재귀, `A → B → A → B`가 반복되면 상호 재귀다(예: `toString()`·`equals()`·`hashCode()`가 양방향 연관을 따라 서로를 부르는 경우).
- 시작점이 잘렸으면 재현해서 `-XX:MaxJavaStackTraceDepth`를 늘리거나, 의심 지점에 깊이 카운터 로그를 둔다.
- 살아 있는 프로세스면 `jstack <pid>`(또는 `jcmd <pid> Thread.print`)로 깊어지는 중인 스레드의 프레임을 본다.

## 장애 시나리오와 대처

### 1. 기저 누락·축소 실패 → `StackOverflowError` (⚠ 커리큘럼)

- **현상**: 특정 요청만 500 에러. 작은 테스트 데이터에서는 재현되지 않는다.
- **보이는 형태**: 로그에 `java.lang.StackOverflowError`, 트레이스에 같은 프레임 수백~천여 줄. `catch (Exception e)` 블록을 통과해 올라간다(`Error` 계열).
- **원인**
  - 기저 조건이 특정 입력을 놓친다(예: `n == 0`만 검사했는데 음수가 들어옴 → 영영 0이 안 된다).
  - 축소가 안 된다(이진 탐색에서 `search(lo, mid)`인데 `mid == hi`가 되는 경우).
  - 순환 데이터(부모 포인터가 자기 자신)를 트리로 가정했다.
- **대처**: 기저 조건을 "같음"이 아니라 범위로(`n <= 0`) 쓴다. 축소량이 1 이상인지 불변식으로 확인한다. 외부 데이터는 방문 집합으로 순환을 끊는다.

### 2. 입력 크기에 비례하는 깊이 → 운영 데이터에서만 터진다

- **현상**: 개발 환경에서는 되던 트리 펼치기·연결 리스트 처리가 큰 고객 데이터에서 죽는다.
- **보이는 형태**: `StackOverflowError`. 실험처럼 1,000개는 되고 1,000,000개는 안 된다. JIT 상태에 따라 경계 크기가 실행마다 다르다.
- **원인**: 재귀 깊이가 log n이 아니라 n이다(치우친 트리, 직선 그래프, 긴 리스트).
- **대처**: 명시적 스택으로 바꾼다. `-Xss`만 키우는 것은 경계를 미룰 뿐이다(실험: 1,000,000 깊이에 `-Xss64m`도 부족).

### 3. 외부 입력의 중첩 깊이 → 서비스 거부

- **현상**: 악의적인 요청(`[[[[[…]]]]]` 수만 겹) 하나로 요청 스레드가 죽는다.
- **보이는 형태**: 파서·역직렬화 스택 트레이스의 `StackOverflowError`. Jackson 2.15+에서 기본 상한(1000)을 그대로 두면 `StreamConstraintsException`이다(상한을 크게 올리면 databind에서 다시 `StackOverflowError`가 날 수 있다 — PR #943). 문구는 판마다 다르다 — 2.15.0은 `Depth (1001) exceeds the maximum allowed nesting depth (1000)`, 2.16.0부터는 `` Document nesting depth (1001) exceeds the maximum allowed (1000, from `StreamReadConstraints.getMaxNestingDepth()`) ``(jackson-core 각 태그의 `StreamReadConstraints.validateNestingDepth`).
- **원인**: 재귀로 읽는 처리(재귀 하강 파서, 역직렬화)의 깊이 = 입력의 중첩 깊이. 공격자가 깊이를 정한다.
- **대처**: 파서의 깊이 상한을 켜 둔다(Jackson `StreamReadConstraints.maxNestingDepth`). 라이브러리 버전을 올린다. 직접 쓴 재귀 처리기에는 깊이 인자를 넘겨 상한에서 거부한다.

### 4. 중복 부분문제 → 지수 시간 (⚠ 커리큘럼)

- **현상**: n이 조금 늘었을 뿐인데 응답이 수십 배 느려지고 CPU가 100%다.
- **보이는 형태**: 프로파일러(async-profiler 등)의 플레임 그래프에 같은 재귀 메서드가 탑처럼 쌓인다. 실험에서 n이 30 → 40으로 늘자 호출 수가 약 123배(2,692,537 → 331,160,281).
- **원인**: 같은 부분문제를 반복 계산한다(피보나치, 메모 없는 경로 수 세기, 가격 조합).
- **대처**: 메모이제이션 또는 상향식 DP. 메모 키가 입력 전체(객체 그래프)면 메모가 오히려 메모리를 먹으니 키를 작게 설계한다.

### 5. 꼬리 재귀를 믿고 깊게 짰다

- **현상**: 다른 언어(Scheme·Kotlin `tailrec`) 습관으로 Java·JavaScript에 꼬리 재귀 루프를 썼다가 큰 입력에서 넘친다.
- **보이는 형태**: Java `StackOverflowError`, Node.js `RangeError: Maximum call stack size exceeded`.
- **원인**: HotSpot(OpenJDK 21)과 V8(Node 22)은 꼬리 호출을 제거하지 않았다(실험).
- **대처**: 반복문으로 직접 바꾼다. Kotlin이면 `tailrec`를 붙여 컴파일러가 바꾸게 한다(조건이 안 맞으면 경고).

## 핵심 문장

- 재귀는 귀납의 코드다. 기저 사례가 맞고, 입력이 엄격히 작아지고, 작은 답이 맞다고 가정해 합친 답이 맞으면 재귀 전체가 맞다.
- 재귀 깊이는 호출 스택 크기(`-Xss`, Linux/x64 기본 1024KB)와 프레임 크기로 막힌다. JIT 상태에 따라 한계 깊이가 실행마다 다르다.
- 깊이가 입력 크기에 비례하면 반복·명시적 스택으로 바꾼다. 스택을 키우는 것은 경계를 미룰 뿐이다.
- HotSpot과 V8은 꼬리 재귀도 프레임을 쌓는다. 꼬리 재귀가 안전한 것은 언어·컴파일러가 제거를 약속할 때뿐이다(Kotlin `tailrec`).
- 재귀의 비용은 점화식으로 센다. 피보나치처럼 중복 부분문제가 쌓이면 지수 시간이 되고, 메모이제이션이나 상향식 DP로 "상태 수 × 상태당 계산"으로 줄인다(피보나치는 선형).

## 관련 주제·근거

- 선행
  - 원본 기초 [foundations/data-structures-basics §7 재귀 함수](../../foundations/data-structures-basics/README.md) — 팩토리얼·피보나치·탈출 조건
  - 커리큘럼 선행 — [data-structure/01-data-structures-basics](../../data-structure/01-data-structures-basics/2-summary.md) · [02-asymptotic-analysis](../02-asymptotic-analysis/2-summary.md)(점화식 비용)
  - math 02-induction-and-invariants(미작성) — [math 커리큘럼](../../math/README.md)
- 후속·연결
  - [algorithm/24-divide-conquer](../24-divide-conquer/2-summary.md) — 재귀 + 마스터 정리
  - [algorithm/12-dfs](../12-dfs/2-summary.md) — 재귀 DFS의 깊이 문제와 반복판
  - [algorithm/21-dp-basics](../21-dp-basics/2-summary.md) — 중복 부분문제 제거
  - [algorithm/13-backtracking](../13-backtracking/2-summary.md), [02-merge-sort](../02-merge-sort/2-summary.md), [03-quick-sort](../03-quick-sort/2-summary.md)
  - [data-structure/03-stack](../../data-structure/03-stack/2-summary.md) — 호출 스택 = 스택, 깊은 재귀 장애
  - [os/07-threads-and-context-switch](../../os/07-threads-and-context-switch/2-summary.md) — 스레드마다 따로 잡히는 스택
  - [reliability/36-profiling](../../reliability/36-profiling/2-summary.md) — 플레임 그래프로 재귀 폭증 찾기
- 교재·문서
  - CLRS 3판 2.3 Designing algorithms(분할정복과 재귀식), 4장 Divide-and-Conquer(치환법·재귀 트리·마스터 정리), 7장 문제 7-4(꼬리 재귀 퀵 정렬의 스택 깊이)
  - Oracle JDK 21 `java` 도구 문서 — `-Xss` 기본값(Linux/x64 1024KB, Linux/AArch64 2048KB) <https://docs.oracle.com/en/java/javase/21/docs/specs/man/java.html>
  - Kotlin 문서 Functions — Tail recursive functions(`tailrec` 조건) <https://kotlinlang.org/docs/functions.html>
  - jackson-core PR #943(2.15 브랜치) — `maxNestingDepth` 기본 1000, CVE-2025-52999(NVD 설명: 2.15.0 미만은 깊은 중첩에서 `StackoverflowError`, 2.15.0은 기본 1000 상한) <https://github.com/FasterXML/jackson-core/pull/943> · 예외 문구는 jackson-core 태그 2.15.0·2.16.0의 `StreamReadConstraints.java`
  - Joshua Bloch 2006, "Extra, Extra - Read All About It: Nearly All Binary Searches and Mergesorts are Broken"(Google Research 블로그)
- 실험 목록(모두 2026-10-05)
  - 재귀 깊이 vs `-Xss`·프레임 크기(`Depth.java`, `-Xint`와 JIT 모드) — OpenJDK 21.0.12 Temurin, docker `--cpus=2`
  - 꼬리 재귀 vs 반복(`Tail.java`, n=10⁴·10⁶, `-Xss64m`·`-Xss256m`) — 같은 환경, 트레이스 줄 수 1,019(소스 실행기) · 1,024(`javac` 컴파일 후)
  - Node.js 꼬리 재귀·무한 재귀 깊이(`tail.js`, `depth.js`) — `node:22-alpine` v22.23.2
  - 피보나치 호출 수·시간·메모이제이션(`Fib.java`) — OpenJDK 21, 세 번 실행
  - 치우친 BST의 재귀 vs 명시적 스택 순회(`Chain.java`) — OpenJDK 21
  - CPython 3.12.3 `sys.getrecursionlimit()`·`RecursionError` — 호스트
