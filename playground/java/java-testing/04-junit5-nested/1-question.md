# java/java-testing/04 — JUnit 5 @Nested 테스트 — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. `WhenFull` 의 테스트 하나를 돌릴 때 호출 차례 (예측)

```java
// 질문용 발췌
class CustomStackTest {
    @BeforeEach void setUp() { stack = new CustomStack<>(3); }
    @Nested class WhenNotEmpty {
        @BeforeEach void pushElement() { stack.push("first"); stack.push("second"); }
        @Nested class WhenFull {
            @BeforeEach void fillStack() { stack.push("third"); }
            @Test void push_throws_when_full() { /* ... */ }
        }
    }
}
```

- `push_throws_when_full()` 하나를 실행하면 메서드 네 개가 어떤 차례로 불리나?
- 테스트 본문이 시작되는 순간 스택에는 무엇이 들어 있나?

### 2. 스택을 비운 테스트 다음에 도는 테스트 (예측)

- `WhenNotEmpty` 안에서 `pop_returns_in_lifo_order()` 가 먼저 돌고 그다음 `size_returns_element_count()` 가 돈다면, 뒤 테스트에서 `stack.size()` 는 얼마인가?

### 3. 가득 찬 스택에서 세 번 꺼내기 (예측)

```java
// 질문용 발췌 — WhenFull 안에 새로 넣은 테스트
@Test
void pop_three_times() {
    String a = stack.pop();
    String b = stack.pop();
    String c = stack.pop();
    // a, b, c 는?
}
```

- 이 테스트에서 `a` · `b` · `c` 에는 각각 어떤 문자열이 들어가나?

### 4. `WhenFull` 을 `WhenNotEmpty` 안에 넣은 까닭 (왜)

- `WhenFull` 을 바깥 클래스 바로 아래가 아니라 `WhenNotEmpty` 안에 중첩하면 무엇이 좋은가?

### 5. `peek` 테스트가 `size()` 까지 검사하는 까닭 (왜)

- `peek_returns_top_without_removing()` 은 왜 `peek()` 의 값만이 아니라 `size()` 가 2인지도 확인하나?

### 6. `@Nested` 클래스에 `static` 을 붙이면 (경계)

- `class WhenNotEmpty` 를 `static class WhenNotEmpty` 로 바꾸면 이 예제에서 어디가 문제가 되나?

### 7. 바깥 최대 크기를 4로 바꾸면 (경계)

- `setUp()` 을 `new CustomStack<>(4)` 로 바꾸고 나머지는 그대로 두면, `push_throws_when_full()` 의 두 검사 중 어느 것이 깨지나?

### 8. 이 구조와 Given-When-Then (연결)

- `CustomStackTest` 의 바깥 `setUp()` · `@Nested` 클래스 · `@Test` 메서드는 Given-When-Then 의 어느 부분에 각각 대응하나?

### 9. `CustomStack` 이 `Stack` 을 필드로 드는 방식 (연결)

- `CustomStack` 이 `java.util.Stack` 을 필드 `internal` 로 들고 일을 맡기는 방식을 무엇이라 부르고, 그 덕분에 `push` 앞에서 무엇을 할 수 있나?

## 실습

### 실습 1. 크기 제한 스택을 상황별 중첩 테스트로 검사하기

**만들 것** — 최대 크기가 있는 `CustomStack` 을 「빈 스택일 때 · 요소가 있을 때 · 가득 찼을 때」 세 상황으로 나눈 `@Nested` 테스트를 만든다.

**준비물** — JUnit 5(JUnit Jupiter) 가 클래스패스에 있어야 한다(Maven 이나 Gradle 의 테스트 의존성 또는 IDE 의 JUnit 5 지원).

**요구 조건**

1단계 — 테스트 대상
1. `CustomStack<T>` 는 `java.util.Stack` 을 필드로 들고 일을 맡긴다(시작 코드에 있다).
2. `push` 는 크기가 최대 크기 이상이면 `IllegalStateException` 을 던지고, `pop` · `peek` 은 비어 있으면 `EmptyStackException` 을 던진다(시작 코드에 있다).

2단계 — 바깥 테스트 클래스
3. `CustomStackTest` 에 `@DisplayName("CustomStack 테스트")` 를 붙인다.
4. 필드 `stack` 을 두고, `@BeforeEach` 메서드 `setUp()` 이 테스트마다 최대 크기 3의 새 `CustomStack<String>` 을 만든다.

3단계 — 빈 스택일 때
5. `@Nested` 내부 클래스 `WhenEmpty` 에 `@DisplayName("빈 스택일 때")` 를 붙인다.
6. `isEmpty()` 가 `true`, `size()` 가 0 인지 검사하는 테스트를 하나씩 만든다.
7. `pop()` 과 `peek()` 이 각각 `EmptyStackException` 을 던지는지 `assertThrows` 로 검사하는 테스트를 하나씩 만든다.

4단계 — 요소가 있을 때
8. `@Nested` 내부 클래스 `WhenNotEmpty` 에 `@DisplayName("요소가 있을 때")` 를 붙인다.
9. 그 클래스의 `@BeforeEach` 메서드 `pushElement()` 가 `"first"`, `"second"` 를 차례로 넣는다.
10. `isEmpty()` 가 `false` 인지, `size()` 가 2 인지 검사하는 테스트를 하나씩 만든다.
11. `peek()` 이 `"second"` 를 돌려주고 그 뒤에도 `size()` 가 2 인지 검사하는 테스트를 만든다.
12. `pop()` 이 `"second"`, `"first"` 순으로 돌려주고 그 뒤 스택이 비는지 검사하는 테스트를 만든다.

5단계 — 가득 찼을 때
13. `WhenNotEmpty` 안에 `@Nested` 내부 클래스 `WhenFull` 을 두고 `@DisplayName("스택이 가득 찼을 때")` 를 붙인다.
14. 그 클래스의 `@BeforeEach` 메서드 `fillStack()` 이 `"third"` 를 하나 더 넣는다.
15. `size()` 가 3 인지 확인한 뒤 `push("overflow")` 가 `IllegalStateException` 을 던지는지 검사하는 테스트를 만든다.
16. 모든 테스트 메서드에 그 기대를 문장으로 적은 `@DisplayName` 을 붙인다.

**시작 코드**

```java
import org.junit.jupiter.api.*;
import static org.junit.jupiter.api.Assertions.*;
import java.util.EmptyStackException;
import java.util.Stack;

// === 테스트 대상 클래스 (완성되어 있다) ===
class CustomStack<T> {
    private final Stack<T> internal = new Stack<>();
    private final int maxSize;

    public CustomStack(int maxSize) {
        this.maxSize = maxSize;
    }

    public void push(T item) {
        if (internal.size() >= maxSize) {
            throw new IllegalStateException("스택이 가득 찼습니다");
        }
        internal.push(item);
    }

    public T pop() {
        if (internal.isEmpty()) {
            throw new EmptyStackException();
        }
        return internal.pop();
    }

    public T peek() {
        if (internal.isEmpty()) {
            throw new EmptyStackException();
        }
        return internal.peek();
    }

    public boolean isEmpty() {
        return internal.isEmpty();
    }

    public int size() {
        return internal.size();
    }
}

// === 테스트 클래스 ===
// TODO: 표시 이름 붙이기
class CustomStackTest {

    private CustomStack<String> stack;

    // TODO: 테스트마다 최대 크기 3의 새 스택을 만드는 준비 메서드

    // TODO: "빈 스택일 때" 중첩 묶음
    //   - isEmpty() 는 true / size() 는 0
    //   - pop() · peek() 은 EmptyStackException

    // TODO: "요소가 있을 때" 중첩 묶음
    //   - 준비: "first", "second" push
    //   - isEmpty() 는 false / size() 는 2
    //   - peek() 은 "second" 이고 크기는 그대로
    //   - pop() 은 "second", "first" 순, 그 뒤 비어 있음

    //   TODO: 그 안에 "스택이 가득 찼을 때" 중첩 묶음
    //     - 준비: "third" push
    //     - size() 는 3, push("overflow") 는 IllegalStateException
}
```

**확인 방법** — IDE 의 테스트 실행이나 `mvn test` · `gradle test` 로 돌려, 테스트 9개가 모두 통과하는지와 결과 트리가 「CustomStack 테스트 → 빈 스택일 때 / 요소가 있을 때 → 스택이 가득 찼을 때」 꼴로 묶여 보이는지 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
