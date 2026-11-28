# java/java-coding-patterns/14 — 재귀 패턴 — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 누산기를 들고 내려가는 팩토리얼 (예측)

```java
// 질문용 발췌
static long factorialTail(int n, long acc) {
    if (n <= 1) return acc;
    return factorialTail(n - 1, n * acc);
}
// factorialTail(4, 1) 을 부른다
```

- 호출마다 `(n, acc)` 는 어떤 차례로 바뀌고, 최종 반환값은 무엇인가?

### 2. `power(2, 10)` 이 거치는 지수 (예측)

```java
// 질문용 발췌
static long power(long base, int exp) {
    if (exp == 0) return 1;
    if (exp % 2 == 0) {
        long half = power(base, exp / 2);
        return half * half;
    }
    return base * power(base, exp - 1);
}
```

- `power(2, 10)` 을 부르면 `power` 는 모두 몇 번 호출되고, 각 호출의 `exp` 는 차례로 무엇인가?

### 3. 원판 두 개의 하노이 탑 (예측)

```java
// 질문용 발췌
static void hanoi(int n, char from, char to, char aux) {
    if (n == 1) {
        System.out.println("  " + from + " -> " + to);
        return;
    }
    hanoi(n - 1, from, aux, to);
    System.out.println("  " + from + " -> " + to);
    hanoi(n - 1, aux, to, from);
}
// hanoi(2, 'A', 'C', 'B') 를 부른다
```

- 어떤 줄들이 어떤 차례로 찍히는가?

### 4. 꼬리 재귀로 바꿔도 깊이 문제가 남는 까닭 (왜)

- `factorialTail` 은 꼬리 재귀인데 왜 Java 에서는 큰 `n` 에서 `factorial` 과 똑같이 스택이 넘치나?

### 5. 짝수 분기가 `half` 변수에 담는 까닭 (왜)

- `power` 의 짝수 분기에서 `power(base, exp / 2)` 를 두 번 곱하지 않고 `half` 에 한 번 담아 쓰는 것이 왜 복잡도를 바꾸나?

### 6. 아주 큰 `n` 을 넣은 팩토리얼 (경계)

- `factorial` 에 큰 `n` 을 넣을 때 결과가 망가지는 두 갈래는 무엇이고, 각각 어느 쪽 한계에 걸리나?

### 7. 모든 원소가 음수인 배열 (경계)

- `maxSubarrayDC` 에 `{-3, -1, -2}` 를 넣으면 답은 0 인가, 원소 중 하나인가?

### 8. `fibMemo` 의 `memo` 와 DP (연결)

- `fibMemo` 의 `memo` 는 동적 계획법의 어떤 생각을 구현한 것이며, 그 덕에 시간은 어떻게 바뀌고 깊이는 왜 그대로인가?

### 9. 괄호 깊이 카운터와 호출 스택 (연결)

- `removeParentheses` 의 `depth` 변수는 재귀의 무엇을 대신하며, 그 덕에 무엇을 피하나?

## 실습

### 실습 1. 재귀 패턴 일곱 가지를 한 클래스에 모으기

**만들 것** — 기본 재귀 · 꼬리 재귀 · 분할 정복 두 가지 · 메모이제이션 · 하노이 탑 · 깊이 카운터를 메서드로 구현하고, 이미 채워진 `main` 이 결과를 찍게 한다.

**요구 조건**

1단계 — 선형 재귀
1. `factorial(int n)` 은 `n` 이 1 이하면 1 을 돌려주고, 아니면 `n` 과 `factorial(n - 1)` 의 곱을 돌려준다.
2. `factorialTail(int n, long acc)` 는 `n` 이 1 이하면 `acc` 를 돌려주고, 아니면 `n * acc` 를 누산기로 넘기며 `n - 1` 로 자신을 부른다 — 재귀 호출이 마지막 연산이어야 한다.

2단계 — 분할 정복
3. `power(long base, int exp)` 는 `exp` 가 0 이면 1, 짝수면 절반 지수의 결과를 한 번만 계산해 제곱, 홀수면 `base * power(base, exp - 1)` 을 돌려준다.
4. `maxSubarrayDC(int[] nums, int left, int right)` 는 원소가 하나면 그 값을 돌려주고, 아니면 가운데로 나눠 왼쪽 최대 · 오른쪽 최대 · 가운데를 걸치는 최대 중 가장 큰 값을 돌려준다.
5. `maxCrossing(int[] nums, int left, int mid, int right)` 는 `mid` 에서 왼쪽으로, `mid + 1` 에서 오른쪽으로 누적하며 각 방향의 최대 누적합을 구해 더한다 — 각 최대는 `Integer.MIN_VALUE` 에서 시작한다.

3단계 — 메모이제이션과 하노이
6. `static Map<Integer, Long> memo` 를 두고, `fibMemo(int n)` 은 `n` 이 1 이하면 `n`, 저장된 값이 있으면 그 값, 없으면 `fibMemo(n - 1) + fibMemo(n - 2)` 를 계산해 저장한 뒤 돌려준다.
7. `hanoi(int n, char from, char to, char aux)` 는 원판이 하나면 `"  " + from + " -> " + to` 를 한 줄 찍고 끝내고, 아니면 n−1 개를 보조 기둥으로 · 가장 큰 원판을 목표로(한 줄 찍기) · n−1 개를 보조에서 목표로 옮긴다.

4단계 — 재귀 없는 재귀적 사고
8. `removeParentheses(String s)` 는 `(` 를 만나면 깊이를 늘리고 `)` 를 만나면 줄이며, 깊이가 0 일 때의 다른 글자만 `StringBuilder` 에 모아 돌려준다(`main` 은 이 메서드를 부르지 않는다).

**시작 코드**

```java
import java.util.Arrays;
import java.util.HashMap;
import java.util.Map;

public class RecursionPatterns {

    static long factorial(int n) {
        // TODO: 기저 조건, 그다음 n * (더 작은 문제)
        return 0;
    }

    static long factorialTail(int n, long acc) {
        // TODO: 기저 조건이면 acc, 아니면 누산기를 갱신해 자신을 부른다
        return 0;
    }

    static long power(long base, int exp) {
        // TODO: exp == 0 / 짝수(half 재사용) / 홀수
        return 0;
    }

    static int maxSubarrayDC(int[] nums, int left, int right) {
        // TODO: 원소 하나면 그 값, 아니면 mid 로 나눠 세 후보 중 최대
        return 0;
    }

    static int maxCrossing(int[] nums, int left, int mid, int right) {
        // TODO: mid 에서 왼쪽으로, mid+1 에서 오른쪽으로 누적 최대를 구해 더한다
        return 0;
    }

    // TODO: 메모 저장소를 선언한다
    static long fibMemo(int n) {
        // TODO: 기저 조건 → 저장된 값 확인 → 계산 → 저장 → 반환
        return 0;
    }

    static void hanoi(int n, char from, char to, char aux) {
        // TODO: 원판 하나면 한 줄 찍고 끝, 아니면 세 단계
    }

    static String removeParentheses(String s) {
        StringBuilder sb = new StringBuilder();
        // TODO: 깊이 카운터로 괄호 밖 글자만 모은다
        return sb.toString();
    }

    public static void main(String[] args) {
        System.out.println("=== 팩토리얼 ===");
        System.out.println("5! = " + factorial(5));
        System.out.println("5! (꼬리재귀) = " + factorialTail(5, 1));

        System.out.println("\n=== 분할 정복 거듭제곱 ===");
        System.out.println("2^10 = " + power(2, 10));
        System.out.println("3^5  = " + power(3, 5));

        System.out.println("\n=== 분할 정복 최대 부분 배열 ===");
        int[] nums = {-2, 1, -3, 4, -1, 2, 1, -5, 4};
        System.out.println("배열: " + Arrays.toString(nums));
        System.out.println("최대 합: " + maxSubarrayDC(nums, 0, nums.length - 1));

        System.out.println("\n=== 메모이제이션 피보나치 ===");
        System.out.println("fib(40) = " + fibMemo(40));

        System.out.println("\n=== 하노이 탑 (n=3) ===");
        hanoi(3, 'A', 'C', 'B');
        System.out.println("이동 횟수: " + ((int) Math.pow(2, 3) - 1));

        System.out.println("\n=== 재귀 설계 원칙 ===");
        System.out.println("1. 기저 조건(Base Case)을 먼저 정의");
        System.out.println("2. 문제를 작은 부분 문제로 분할");
        System.out.println("3. 부분 문제의 결과를 조합");
        System.out.println("4. 중복 계산이 있으면 메모이제이션");
        System.out.println("5. 깊이가 깊으면 반복문으로 변환 고려");
    }
}
```

**확인 방법** — `javac RecursionPatterns.java && java RecursionPatterns` 로 돌려, 찍힌 값이 손으로 셈한 값(`5! = 120`, `2^10 = 1024`, `3^5 = 243`, 최대 합 6, 하노이 이동 7 줄)과 맞는지 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
