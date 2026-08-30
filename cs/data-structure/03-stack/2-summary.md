# data-structure/03-stack — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> 작성 방식: 내가 먼저 기억으로 흐름을 서술하고, Claude는 빠지거나 틀린 곳을 짚는다. 대신 써주지 않는다.
> 이미 따라 치며 만든 정리본이 따로 있으면(organize류) 이 파일은 핵심 문장 압축 + 링크만 담는다.

## 전체 흐름

<!-- 이 자료구조가 동작하는 원리를 자기 말로 -->

## 계약 — Stack (`src/main/java/com/datastructure/stack/Stack.java`)

- `void push(E element)`
- `E pop()`
- `E peek()`
- `int size()`
- `boolean isEmpty()`
- `void clear()`

## 구현 — ArrayStack (`src/main/java/com/datastructure/stack/ArrayStack.java`)

<!-- 메서드마다 내 언어로. 복잡도는 "왜 그런지"까지. -->

### `필드`

- `private static final int DEFAULT_CAPACITY = 4` — 역할:
- `Object[] elements` — 역할:
- `int top` — 역할:

### `ArrayStack()`

- 하는 일:
- 논리:
- 비용(왜):

### `ArrayStack(int initialCapacity)`

- 하는 일:
- 논리:
- 비용(왜):

### `int size()`

- 하는 일:
- 논리:
- 비용(왜):

### `boolean isEmpty()`

- 하는 일:
- 논리:
- 비용(왜):

### `int capacity()`

- 하는 일:
- 논리:
- 비용(왜):

### `String toString()`

- 하는 일:
- 논리:
- 비용(왜):

### `private void ensureCapacity(int minCapacity)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `void push(E element)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `E pop()` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `E peek()` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `void clear()` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

## 구현 — LinkedStack (`src/main/java/com/datastructure/stack/LinkedStack.java`)

### `필드`

- `static class Node<E> { E item; Node<E> next; }` — 역할:
- `Node<E> top` — 역할:
- `private int size` — 역할:

### `int size()`

- 하는 일:
- 논리:
- 비용(왜):

### `boolean isEmpty()`

- 하는 일:
- 논리:
- 비용(왜):

### `String toString()`

- 하는 일:
- 논리:
- 비용(왜):

### `void push(E element)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `E pop()` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `E peek()` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `void clear()` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

## 구현 전략 비교

| 전략 | 장점 | 단점 | 적합한 경우 |
|------|------|------|-------------|
| ArrayStack | | | |
| LinkedStack | | | |

## 문제 — StackProblems (`src/main/java/com/datastructure/stack/StackProblems.java`)

### 문제 1. 괄호 짝 맞추기

> 문제 설명: `()`, `[]`, `{}` 세 종류가 올바르게 짝지어졌는지 본다. 괄호 외의 문자는 무시한다.
> `"a(b[c]d)e"` -> true
> `"([)]"` -> false — 짝은 맞지만 순서가 어긋난다
> `"(("` -> false — 안 닫혔다
> `")("` -> false — 닫는 게 먼저 왔다
> 생각할 것 — 왜 스택인가? 가장 최근에 열린 괄호가 가장 먼저 닫혀야 하기 때문이다. /
> 다 훑고 나서 스택에 뭔가 남아 있으면 그건 무슨 뜻인가?
> 시그니처: `static boolean isBalanced(String input, Stack<Character> buffer)` — `buffer` 는 비어 있는 상태로 들어온다.

- 내 접근:
- 논리:
- 비용(왜):

### 문제 2. 후위 표기식 계산

> 문제 설명: 공백으로 구분된 후위 표기식을 계산한다. 정수와 `+ - * /` 만 나온다.
> `"3 4 +"` -> 7 / `"3 4 + 2 *"` -> 14 / `"5 1 2 + 4 * + 3 -"` -> 14
> 나눗셈은 정수 나눗셈이다. 0 으로 나누면 ArithmeticException 이 그대로 나가면 된다.
> 식이 올바르지 않으면 IllegalArgumentException.
> 생각할 것 — 연산자를 만났을 때 꺼내는 순서가 중요하다. `"3 4 -"` 는 3-4 인가 4-3 인가? /
> 다 계산하고 스택에 값이 정확히 하나 남아야 올바른 식이다.
> 시그니처: `static int evaluatePostfix(String expression, Stack<Integer> buffer)`

- 내 접근:
- 논리:
- 비용(왜):

### 문제 3. 오른쪽의 첫 번째 더 큰 값 (이 문제집의 함정)

> 문제 설명: 각 원소에 대해, 그 오른쪽에서 처음으로 나타나는 더 큰 값을 찾는다. 없으면 -1.
> `[2, 1, 3]` -> `[3, 3, -1]` / `[5, 4, 3]` -> `[-1, -1, -1]` / `[1, 3, 2, 4]` -> `[3, 4, 4, -1]`
> 함정 — 각 원소마다 오른쪽을 훑으면 O(n^2) 이다. 테스트에 20만 개짜리 케이스와 시간 제한이 있다.
> 생각할 것 — 스택에 "아직 답을 못 찾은 원소"를 쌓아두면 어떻게 되는가? /
> 새 값이 들어왔을 때, 그 값보다 작은 것들은 답이 한꺼번에 정해진다. /
> 각 원소가 스택에 몇 번 들어가고 몇 번 나오는가? 그게 복잡도다.
> 시그니처: `static int[] nextGreater(int[] values, Stack<Integer> buffer)` — O(n) 이어야 한다. `buffer` 에는 인덱스를 담으면 편하다.

- 내 접근:
- 논리:
- 비용(왜):

### 문제 4. 스택 정렬

> 문제 설명: 스택을 오름차순으로 만든다. 큰 값이 top 에 오게 한다.
> 배열이나 리스트로 옮기지 말고, 주어진 보조 스택 하나만 써서 해결하라.
> `[3, 1, 2] (top=2)` -> `[1, 2, 3] (top=3)`
> 생각할 것 — 보조 스택을 항상 정렬된 상태로 유지하면 어떻게 되는가? /
> 넣으려는 값보다 큰 것들이 보조 스택 위에 있으면 어떻게 하는가? /
> 마지막에 다시 옮겨 담으면 순서가 어떻게 되는가?
> 시그니처: `static void sortAscending(Stack<Integer> stack, Stack<Integer> helper)`

- 내 접근:
- 논리:
- 비용(왜):

### 문제 5. 중위 표기식을 후위 표기식으로

> 문제 설명: 우리가 쓰는 표기(중위)를 문제 2가 계산할 수 있는 표기(후위)로 바꾼다.
> 토큰은 공백으로 구분되고 정수, `+ - * /`, 괄호만 나온다.
> `"3 + 4 * 2"` -> `"3 4 2 * +"` / `"( 3 + 4 ) * 2"` -> `"3 4 + 2 *"` /
> `"3 - 4 - 5"` -> `"3 4 - 5 -"` — 왼쪽부터 묶인다
> 이 변환을 shunting yard 알고리즘이라고 부른다. 결과를 문제 2에 그대로 넣으면 계산이 된다. 두 문제가 이어진다.
> 규칙 — 숫자: 바로 출력한다 / 여는 괄호: 쌓는다 / 닫는 괄호: 여는 괄호를 만날 때까지 꺼내 출력하고, 여는 괄호는 버린다 /
> 연산자: 스택 위에 "우선순위가 같거나 높은 연산자"가 있으면 먼저 꺼내 출력한 뒤 쌓는다 / 끝나면: 남은 것을 전부 꺼내 출력한다
> 생각할 것 — 왜 "같거나 높은"인가? "높은"만 보면 `3 - 4 - 5` 가 어떻게 되는가?
> 사칙연산은 왼쪽부터 묶이는데, 그 성질이 이 조건 하나에 들어 있다. /
> 괄호가 안 맞으면 언제 알 수 있는가? 두 가지 경우가 있다.
> 괄호가 맞지 않으면 IllegalArgumentException.
> 시그니처: `static String infixToPostfix(String expression, Stack<Character> buffer)`

- 내 접근:
- 논리:
- 비용(왜):

## 핵심 문장

<!-- 지도 수준의 문장들 — 세부가 아니라 "왜 이 구조인가"를 담은 문장 -->

-
-
-

## 관련 자료

<!-- 원본 문서·코드 경로. 기준 소스는 문서가 아니라 코드/원전이다. -->

- 원본 README: `/home/jun/project/myway/data-structure/03-stack/README.md`
- 구현: `/home/jun/project/myway/data-structure/03-stack/src/main/java/com/datastructure/stack/`
- 테스트: `/home/jun/project/myway/data-structure/03-stack/src/test/java/com/datastructure/stack/`
- 참고 구현: `/home/jun/project/myway/data-structure/03-stack/impl/`
