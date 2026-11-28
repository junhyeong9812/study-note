# java/java-coding-patterns/14 — 재귀 패턴 — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. `(4,1) → (3,4) → (2,12) → (1,24)`, 반환값 24

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
factorialTail(4, 1)
factorialTail(3, 4)    ← 4 * 1
factorialTail(2, 12)   ← 3 * 4
factorialTail(1, 24)   ← 2 * 12, n <= 1 이라 acc = 24 를 돌려준다
```

**왜 그런가**
곱셈은 다음 호출의 인자를 만들 때, 곧 내려가는 길에 이미 끝난다.
맨 아래 호출이 24 를 돌려주면 위의 호출들은 그 값에 아무것도 하지 않고 그대로 넘긴다.
근거: 2-summary 「동작 방식 (2)」.

### 2. 6번 호출, 지수는 10 → 5 → 4 → 2 → 1 → 0

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
power(2, 10)  짝수 → half = power(2, 5)
power(2, 5)   홀수 → 2 * power(2, 4)
power(2, 4)   짝수 → half = power(2, 2)
power(2, 2)   짝수 → half = power(2, 1)
power(2, 1)   홀수 → 2 * power(2, 0)
power(2, 0)   → 1
돌아오며: 1 → 2 → 4 → 16 → 32 → 1024
```

**왜 그런가**
짝수면 지수가 절반이 되고, 홀수면 1 을 빼서 다음이 짝수가 된다.
그래서 지수를 하나씩 줄였다면 11번 불렸을 것이 6번으로 줄고, 호출 수는 `log₂ exp` 에 비례한다.
근거: 2-summary 「동작 방식 (3)」.

### 3. `A -> B`, `A -> C`, `B -> C` 세 줄

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
  A -> B
  A -> C
  B -> C
```

**왜 그런가**
`hanoi(2, A, C, B)` 는 먼저 `hanoi(1, A, B, C)` 로 작은 원판을 보조 기둥 B 로 옮겨 `A -> B` 를 찍는다.
이어서 가장 큰 원판을 목표로 옮기며 `A -> C` 를 찍는다.
마지막으로 `hanoi(1, B, C, A)` 가 작은 원판을 B 에서 C 로 옮겨 `B -> C` 를 찍는다.
줄마다 앞에 공백 두 칸이 붙고, 이동 수는 `2^2 − 1 = 3` 과 맞는다.
근거: 2-summary 「동작 방식 (6)」.

### 4. Java 가 꼬리 호출을 최적화하지 않아 프레임이 그대로 쌓이기 때문이다

꼬리 재귀는 돌아온 값에 할 일이 없으므로, 원리상 지금 프레임을 버리고 다음 호출로 갈아탈 수 있다.
그러나 Java 는 그 최적화를 하지 않아, `factorialTail` 도 호출마다 새 프레임을 쌓아 깊이가 `n` 이 된다.
그래서 꼬리 재귀의 이점은 「반복문으로 직접 옮기기 쉬운 꼴」이라는 데 있고, 깊이를 줄이려면 반복문으로 바꾸거나 `-Xss` 로 스택을 키워야 한다.
근거: 2-summary 「동작 방식 (2)」 · 「어디서 틀리나 3」.

### 5. 두 번 부르면 호출이 단계마다 두 배로 갈라져 O(log n) 이 O(n) 으로 돌아간다

`half` 에 담으면 각 단계에서 재귀 호출이 하나뿐이라 호출 수가 지수의 로그에 비례한다.
`power(base, exp / 2) * power(base, exp / 2)` 로 쓰면 같은 부분 문제를 두 번 풀고, 그 둘이 또 각각 둘로 갈라진다.
깊이 `log n` 의 이진 나무가 되어 노드 수가 `n` 수준이 되므로, 지수를 절반으로 줄인 이득이 사라진다.
근거: 2-summary 「동작 방식 (3)」 · 「어디서 틀리나 4」.

### 6. 스택 넘침(깊이 한계)과 `long` 오버플로(값 범위 한계)

첫째, `factorial` 의 깊이는 `n` 이므로 `n` 이 크면 호출 스택이 정해진 크기를 넘어 `StackOverflowError` 가 난다 — 스택 크기 쪽 한계다.
둘째, 그보다 훨씬 작은 `n` 에서 값이 먼저 망가진다 — `long` 은 약 9.22 × 10^18 까지라 `21!` 부터 넘쳐서 예외 없이 틀린 값이 나온다.
근거: 2-summary 「동작 방식 (8)」 · 「어디서 틀리나 2」 · 「어디서 틀리나 6」 (오버플로 부분은 원본에 근거 없음 — 추론).

### 7. 0 이 아니라 원소 중 가장 큰 값 −1 이다

기저 조건이 `nums[left]` 를 그대로 돌려주고, `maxCrossing` 의 두 최대는 `Integer.MIN_VALUE` 에서 시작해 양쪽에서 원소를 하나 이상 넣는다.
그래서 빈 구간(합 0)은 후보가 될 수 없고, 답은 실제로 존재하는 구간의 합이다.
손으로 따라가면: 왼쪽 `[-3, -1]` 은 max(−3, −1, 걸침 −4) = −1, 오른쪽 `[-2]` 는 −2, 가운데를 걸치는 최대는 −1 + −2 = −3, 그중 최대가 −1 이다.
근거: 2-summary 「동작 방식 (4)」.

### 8. 겹치는 부분 문제의 답을 저장해 다시 쓰는 생각 — 시간은 O(2^n) 에서 O(n), 깊이는 여전히 `n`

메모가 없으면 `fib(n)` 이 `fib(n−1)` 과 `fib(n−2)` 로 갈라지며 같은 값을 거듭 계산해 O(2^n) 이 된다.
`memo` 는 각 `n` 의 답을 한 번만 계산해 저장하므로 O(n) 이 되고, 이것이 위에서 아래로 내려가는 동적 계획법이다.
하지만 처음 `fibMemo(n)` 을 부르면 `n−1`, `n−2`, … 로 기저 조건까지 한 줄로 내려가야 하므로 스택 깊이는 `n` 그대로다.
근거: 2-summary 「동작 방식 (5)」 · 「어디서 틀리나 5」.

### 9. 호출 스택의 층수를 대신하며, 재귀 호출과 스택 쌓임을 피한다

괄호 하나에 들어가는 것은 재귀 호출 하나로 한 층 내려가는 것과 같고, 닫는 괄호는 그 호출에서 돌아오는 것과 같다.
`depth` 는 「지금 몇 층에 있나」만 숫자로 기억해, 프레임을 쌓지 않고 문자열을 한 번 훑어 O(n) 에 끝낸다.
원본 주석은 이것을 「반복으로 표현된 재귀적 사고」라 부른다.
근거: 2-summary 「동작 방식 (7)」.

## 실습 정답

### 실습 1. 재귀 패턴 일곱 가지를 한 클래스에 모으기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. 기본 재귀 팩토리얼 | `factorial` — `if (n <= 1) return 1;` · `return n * factorial(n - 1);` |
| 2. 꼬리 재귀 팩토리얼 | `factorialTail` — `if (n <= 1) return acc;` · `return factorialTail(n - 1, n * acc);` |
| 3. 분할 정복 거듭제곱 | `power` — `exp == 0` · `long half = power(base, exp / 2); return half * half;` · `base * power(base, exp - 1)` |
| 4. 분할 정복 최대 부분 배열 | `maxSubarrayDC` — `left == right` · `mid` · `leftMax` · `rightMax` · `crossMax` · `Math.max(Math.max(…), …)` |
| 5. 가운데를 걸치는 최대 | `maxCrossing` — `leftSum = Integer.MIN_VALUE` 와 `i = mid` 부터 내려가는 `for` · `rightSum` 과 `i = mid + 1` 부터 올라가는 `for` · `leftSum + rightSum` |
| 6. 메모이제이션 피보나치 | `static Map<Integer, Long> memo` · `fibMemo` 의 `memo.containsKey` · `memo.get` · `memo.put` |
| 7. 하노이 탑 | `hanoi` — `n == 1` 분기의 `println` · `hanoi(n - 1, from, aux, to)` · 가운데 `println` · `hanoi(n - 1, aux, to, from)` |
| 8. 괄호 제거 깊이 카운터 | `removeParentheses` — `depth++` · `depth--` · `else if (depth == 0) sb.append(c)` |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`java/java-coding-patterns/reference/recursion-patterns.java`

```java
// [코딩 테스트 패턴] 재귀 패턴
// 설명: 재귀의 기본 구조, 꼬리 재귀, 분할 정복, 메모이제이션 패턴
// 팁: 재귀의 시간복잡도: 분할 정복 거듭제곱 O(log n), 하노이 탑 O(2^n). Java의 기본 스택 크기는 약 512KB~1MB로, 재귀 깊이 약 5000~10000 정도. 깊이가 깊으면 -Xss 옵션으로 스택 크기 증가 또는 반복문 변환. 꼬리 재귀는 Java에서 최적화되지 않으므로 직접 반복문으로 변환해야 한다.

// 배열 출력
import java.util.Arrays;
// 메모이제이션용 맵
import java.util.HashMap;
// 인터페이스 타입
import java.util.Map;

// 재귀 패턴 모음
public class RecursionPatterns {

    // 1. 기본 재귀: 팩토리얼
    // 효과: 수학적 정의를 그대로 표현 → 가독성↑, 단 스택 깊이 주의
    static long factorial(int n) {
        // Guard Clause: 기저 조건으로 무한 재귀 방지
        if (n <= 1) return 1; // 기저 조건
        return n * factorial(n - 1); // 재귀 호출
    }

    // 2. 꼬리 재귀 (Java에서는 최적화되지 않지만 개념 이해)
    // 효과: 누산기(acc) 패턴 - 반복문 변환 시 자연스러움
    static long factorialTail(int n, long acc) {
        // 기저 조건: 누적값을 그대로 반환
        if (n <= 1) return acc;
        return factorialTail(n - 1, n * acc); // 마지막 연산이 재귀 호출
    }

    // 3. 분할 정복: 거듭제곱
    // 효과: O(n) → O(log n), 지수를 절반씩 줄임
    static long power(long base, int exp) {
        // 기저 조건: 0제곱은 1
        if (exp == 0) return 1;
        // 짝수: half * half (한 번 계산해서 재사용)
        if (exp % 2 == 0) {
            long half = power(base, exp / 2);
            return half * half;
        }
        // 홀수: base * power(base, exp-1)로 짝수화
        return base * power(base, exp - 1);
    }

    // 4. 분할 정복: 최대 부분 배열 합
    // 효과: O(n²) 완전탐색 → O(n log n), 단 Kadane O(n) 알고리즘이 더 빠름
    static int maxSubarrayDC(int[] nums, int left, int right) {
        // 기저: 단일 원소
        if (left == right) return nums[left];
        // 중간 분할점
        int mid = (left + right) / 2;
        // 왼쪽 부분 최대
        int leftMax = maxSubarrayDC(nums, left, mid);
        // 오른쪽 부분 최대
        int rightMax = maxSubarrayDC(nums, mid + 1, right);
        // 중간 걸치는 최대
        int crossMax = maxCrossing(nums, left, mid, right);
        // 셋 중 최대
        return Math.max(Math.max(leftMax, rightMax), crossMax);
    }

    // 중간을 가로지르는 최대 합 (분할 정복 보조)
    static int maxCrossing(int[] nums, int left, int mid, int right) {
        // 왼쪽: mid에서 왼쪽으로 누적하며 최대 추적
        int leftSum = Integer.MIN_VALUE, sum = 0;
        for (int i = mid; i >= left; i--) {
            sum += nums[i];
            leftSum = Math.max(leftSum, sum);
        }
        // 오른쪽: mid+1에서 오른쪽으로 누적하며 최대 추적
        int rightSum = Integer.MIN_VALUE;
        sum = 0;
        for (int i = mid + 1; i <= right; i++) {
            sum += nums[i];
            rightSum = Math.max(rightSum, sum);
        }
        // 두 부분 합산 → 중간을 걸치는 최대
        return leftSum + rightSum;
    }

    // 5. 메모이제이션: 피보나치
    // 효과: 순수 재귀 O(2^n) → O(n), 중복 계산 제거 (대표적 DP 패턴)
    static Map<Integer, Long> memo = new HashMap<>();
    static long fibMemo(int n) {
        // 기저 조건
        if (n <= 1) return n;
        // Memoization 패턴: 캐시된 값 즉시 반환 (Early Return)
        if (memo.containsKey(n)) return memo.get(n);
        // 재귀로 계산
        long result = fibMemo(n - 1) + fibMemo(n - 2);
        // 결과 캐싱
        memo.put(n, result);
        return result;
    }

    // 6. 재귀 -> 반복 변환 (하노이 탑)
    // 효과: 재귀 자연스럽지만 O(2^n) - 본질적 복잡도이므로 최적화 불가
    static void hanoi(int n, char from, char to, char aux) {
        // 기저 조건: 1개 원판은 직접 이동
        if (n == 1) {
            System.out.println("  " + from + " -> " + to);
            return;
        }
        // n-1개를 보조 기둥으로 이동
        hanoi(n - 1, from, aux, to);
        // 가장 큰 원판을 목표 기둥으로
        System.out.println("  " + from + " -> " + to);
        // n-1개를 보조 기둥에서 목표 기둥으로
        hanoi(n - 1, aux, to, from);
    }

    // 7. 재귀적 문자열 처리: 괄호 제거
    // 효과: 깊이 카운터로 재귀 없이 O(n) 처리 (반복으로 표현된 재귀적 사고)
    static String removeParentheses(String s) {
        // 결과 누적용 가변 버퍼
        StringBuilder sb = new StringBuilder();
        // 괄호 깊이 추적
        int depth = 0;
        for (char c : s.toCharArray()) {
            // 여는 괄호: 깊이 증가
            if (c == '(') depth++;
            // 닫는 괄호: 깊이 감소
            else if (c == ')') depth--;
            // 깊이 0(괄호 밖)일 때만 결과에 포함
            else if (depth == 0) sb.append(c);
        }
        return sb.toString();
    }

    public static void main(String[] args) {
        // 1. 팩토리얼
        System.out.println("=== 팩토리얼 ===");
        System.out.println("5! = " + factorial(5));
        System.out.println("5! (꼬리재귀) = " + factorialTail(5, 1));

        // 2. 거듭제곱
        System.out.println("\n=== 분할 정복 거듭제곱 ===");
        System.out.println("2^10 = " + power(2, 10)); // 1024
        System.out.println("3^5  = " + power(3, 5));  // 243

        // 3. 최대 부분 배열 (분할 정복)
        System.out.println("\n=== 분할 정복 최대 부분 배열 ===");
        int[] nums = {-2, 1, -3, 4, -1, 2, 1, -5, 4};
        System.out.println("배열: " + Arrays.toString(nums));
        System.out.println("최대 합: " + maxSubarrayDC(nums, 0, nums.length - 1));

        // 4. 메모이제이션 피보나치
        System.out.println("\n=== 메모이제이션 피보나치 ===");
        System.out.println("fib(40) = " + fibMemo(40));

        // 5. 하노이 탑
        System.out.println("\n=== 하노이 탑 (n=3) ===");
        hanoi(3, 'A', 'C', 'B');
        System.out.println("이동 횟수: " + ((int) Math.pow(2, 3) - 1));

        // 재귀 설계 원칙
        System.out.println("\n=== 재귀 설계 원칙 ===");
        System.out.println("1. 기저 조건(Base Case)을 먼저 정의");
        System.out.println("2. 문제를 작은 부분 문제로 분할");
        System.out.println("3. 부분 문제의 결과를 조합");
        System.out.println("4. 중복 계산이 있으면 메모이제이션");
        System.out.println("5. 깊이가 깊으면 반복문으로 변환 고려");
    }
}
// 출력:
// === 팩토리얼 ===
// 5! = 120
// 5! (꼬리재귀) = 120
// === 분할 정복 거듭제곱 ===
// 2^10 = 1024
// 3^5  = 243
// === 분할 정복 최대 부분 배열 ===
// 배열: [-2, 1, -3, 4, -1, 2, 1, -5, 4]
// 최대 합: 6
// === 메모이제이션 피보나치 ===
// fib(40) = 102334155
// === 하노이 탑 (n=3) ===
//   A -> C
//   A -> B
//   C -> B
//   A -> C
//   B -> A
//   B -> C
//   A -> C
// 이동 횟수: 7
```

**실행 결과** — 실행하지 않음 — Java 예제는 이 문서를 만들 때 컴파일 · 실행하지 않았다(JDK 로 돌려 확인한다).

**풀이 요점**
- 모든 재귀 메서드가 첫 줄에 기저 조건을 두고, 인자는 매 호출마다 기저 쪽으로 줄어든다(`n - 1`, `exp / 2`, 구간 절반).
- `factorialTail` 은 누산기를 넘기는 꼬리 재귀 꼴이지만 Java 에서는 깊이가 줄지 않는다 — 반복문으로 옮기기 좋은 꼴일 뿐이다.
- `power` 의 `half` 와 `fibMemo` 의 `memo` 는 둘 다 「같은 부분 문제를 두 번 풀지 않는다」는 같은 생각이다.
- `maxCrossing` 의 `Integer.MIN_VALUE` 시작값 덕에 모든 원소가 음수여도 빈 구간(0)이 답이 되지 않는다.
- `hanoi` 는 이동 횟수가 `2^n − 1` 이라 본질적으로 지수이고, `removeParentheses` 는 재귀 없이 깊이 카운터로 같은 사고를 O(n) 에 해낸다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — Java 예제는 이 문서를 만들 때 컴파일 · 실행하지 않았다(JDK 로 돌려 확인한다) |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
