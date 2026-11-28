# java/java-testing/04 — JUnit 5 @Nested 테스트 — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. `setUp` → `pushElement` → `fillStack` → 테스트, 스택은 `[first, second, third]`

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

차례는 `setUp()` → `pushElement()` → `fillStack()` → `push_throws_when_full()` 이다.
테스트 본문이 시작될 때 스택에는 아래에서부터 `"first"`, `"second"`, `"third"` 셋이 들어 있고 크기는 3(가득 참)이다.

**왜 그런가**

`@BeforeEach` 는 바깥 클래스의 것이 먼저, 안쪽으로 갈수록 나중에 돈다.
`setUp()` 이 빈 스택을 만들고, `pushElement()` 가 둘을 넣고, `fillStack()` 이 하나를 더 넣는다.
근거: 2-summary 「동작 방식 (2)」.

### 2. 2 — 앞 테스트가 비운 스택을 이어받지 않는다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

`stack.size()` 는 2 다.

**왜 그런가**

`@BeforeEach` 는 테스트마다 다시 돈다.
뒤 테스트 직전에도 `setUp()` 이 새 스택을 만들고 `pushElement()` 가 다시 둘을 넣는다.
그래서 앞 테스트가 `pop` 으로 비운 상태는 남지 않는다.
근거: 2-summary 「동작 방식 (3)」 · 「어디서 틀리나 3」.

### 3. `"third"` · `"second"` · `"first"` — 넣은 반대 순서

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

`a` 는 `"third"`, `b` 는 `"second"`, `c` 는 `"first"` 다.
세 번 꺼낸 뒤 스택은 비고, 예외는 나지 않는다.

**왜 그런가**

`WhenFull` 의 테스트 직전에 준비가 `first` → `second` → `third` 순으로 넣는다.
`pop` 은 LIFO 라 마지막에 넣은 것부터 꺼낸다.
세 번째 `pop` 까지는 스택이 비어 있지 않으므로 `EmptyStackException` 이 나지 않는다.
근거: 2-summary 「동작 방식 (2)」 · 「동작 방식 (5)」.

### 4. 「요소가 있을 때」 준비를 물려받아 하나만 더 넣으면 된다

「가득 찼을 때」는 「요소가 있을 때」를 한 걸음 더 진행한 상황이다.
`WhenNotEmpty` 안에 두면 `pushElement()` 의 두 개가 이미 들어간 상태에서 시작하므로 `fillStack()` 은 `"third"` 하나만 넣으면 된다.
준비 코드가 중복되지 않고, 계층이 「요소가 있고 + 가득 찼을 때」라는 상황을 그대로 읽히게 한다.
근거: 2-summary 「어디서 틀리나 5」 · 「동작 방식 (6)」.

### 5. 값만 보면 `pop` 과 구별되지 않기 때문이다

`peek()` 과 `pop()` 은 둘 다 맨 위 요소 `"second"` 를 돌려준다.
`peek` 의 고유한 성질은 「제거하지 않는다」이므로, 호출 뒤에도 크기가 2 그대로인지 확인해야 그 성질이 검사된다.
근거: 2-summary 「어디서 틀리나 4」 · 「동작 방식 (5)」.

### 6. 바깥 필드 `stack` 을 못 써서 컴파일이 안 되고, `@Nested` 규칙에도 어긋난다

`static` 중첩 클래스는 바깥 객체에 묶이지 않으므로, 바깥의 인스턴스 필드 `stack` 을 이름만으로 쓸 수 없다.
`pushElement()` 와 테스트들이 모두 `stack` 을 쓰므로 컴파일 오류가 난다.
또 `@Nested` 클래스는 non-static 내부 클래스여야 한다는 JUnit 규칙에도 어긋난다.
근거: 2-summary 「동작 방식 (4)」 · 「어디서 틀리나 1」.

### 7. `assertThrows` 쪽이 깨진다

`fillStack()` 까지 넣어도 요소는 셋이므로 `assertEquals(3, stack.size())` 는 그대로 통과한다.
그러나 최대 크기가 4 이면 `size() >= maxSize` 가 거짓이라 `push("overflow")` 가 예외 없이 들어가므로, `IllegalStateException` 을 기대한 `assertThrows` 가 실패한다.
안쪽 준비가 바깥 설정 값(최대 크기 3)을 전제로 짜여 있기 때문이다.
근거: 2-summary 「어디서 틀리나 6」 · 「동작 방식 (5)」.

### 8. 바깥 `setUp` = Given, `@Nested` 클래스 = When, `@Test` = Then

바깥 `setUp()` 은 「크기 3 스택이 있다」라는 공통 전제(Given)다.
`@Nested` 클래스의 이름과 그 `@BeforeEach` 는 「요소가 있을 때」 같은 상황(When)을 만든다.
`@Test` 메서드와 그 `@DisplayName` 은 「size()는 요소 수를 반환한다」 같은 기대 결과(Then)를 적는다.
근거: 2-summary 「동작 방식 (6)」.

### 9. 위임(Composition) — `push` 앞에서 크기 검사를 끼워 넣을 수 있다

필드로 들고 일을 맡기는 방식을 위임(Composition)이라 한다.
`CustomStack` 의 `push` 는 `internal.push(item)` 을 부르기 전에 `internal.size() >= maxSize` 를 검사해 가득 찼으면 `IllegalStateException` 을 던진다.
`pop` · `peek` 도 같은 식으로 비었는지 먼저 확인한다.
근거: 2-summary 「동작 방식 (5)」.

## 실습 정답

### 실습 1. 크기 제한 스택을 상황별 중첩 테스트로 검사하기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. `Stack` 을 필드로 들고 위임 | `CustomStack` 의 `private final Stack<T> internal` |
| 2. 가득 참 · 빈 상태 예외 | `push` 의 `IllegalStateException`, `pop` · `peek` 의 `EmptyStackException` |
| 3. 바깥 표시 이름 | `@DisplayName("CustomStack 테스트") class CustomStackTest` |
| 4. 테스트마다 크기 3 새 스택 | `@BeforeEach void setUp()` 의 `new CustomStack<>(3)` |
| 5. 빈 스택 묶음 | `@Nested @DisplayName("빈 스택일 때") class WhenEmpty` |
| 6. `isEmpty` true · `size` 0 | `isEmpty_returns_true()` · `size_returns_zero()` |
| 7. `pop` · `peek` 예외 | `pop_throws_exception()` · `peek_throws_exception()` 의 `assertThrows` |
| 8. 요소 있음 묶음 | `@Nested @DisplayName("요소가 있을 때") class WhenNotEmpty` |
| 9. 두 요소 넣기 | `@BeforeEach void pushElement()` |
| 10. `isEmpty` false · `size` 2 | `isEmpty_returns_false()` · `size_returns_element_count()` |
| 11. `peek` 은 제거하지 않음 | `peek_returns_top_without_removing()` |
| 12. LIFO 로 꺼냄 | `pop_returns_in_lifo_order()` |
| 13. 가득 참 묶음(이중 중첩) | `WhenNotEmpty` 안의 `@Nested @DisplayName("스택이 가득 찼을 때") class WhenFull` |
| 14. 하나 더 넣기 | `@BeforeEach void fillStack()` |
| 15. 크기 3 확인 뒤 넘침 예외 | `push_throws_when_full()` |
| 16. 테스트마다 표시 이름 | 각 `@Test` 위의 `@DisplayName(...)` |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`java/java-testing/reference/junit5-nested.java`

```java
// [테스팅] JUnit 5 @Nested 테스트
// 설명: @Nested 어노테이션으로 계층적 테스트 구조를 만들어 관련 테스트를 논리적으로 그룹화
// 팁: @Nested 클래스는 내부 클래스(non-static inner class)여야 하며, 외부 테스트의 @BeforeEach가 먼저 실행된 후 내부의 @BeforeEach가 실행된다. 이를 활용하면 Given-When-Then 스타일의 계층적 테스트 구조를 자연스럽게 표현할 수 있다.

// @Test, @Nested, @BeforeEach, @DisplayName 등을 한 번에 임포트
import org.junit.jupiter.api.*;
import static org.junit.jupiter.api.Assertions.*;
// 빈 스택 pop/peek 시 던져지는 표준 예외
import java.util.EmptyStackException;
// SUT가 위임할 표준 라이브러리 스택
import java.util.Stack;

// === 테스트 대상 클래스 ===
// 최대 크기 제한이 있는 스택 - 빈 상태/요소 있음/가득 찬 상태의 3가지 컨텍스트가 자연스러운 SUT
class CustomStack<T> {
    // 표준 Stack에 위임 (Composition)
    private final Stack<T> internal = new Stack<>();
    // 최대 크기 - 생성자에서 한 번만 설정
    private final int maxSize;

    public CustomStack(int maxSize) {
        this.maxSize = maxSize;
    }

    // 가득 찬 경우 IllegalStateException 발생
    public void push(T item) {
        if (internal.size() >= maxSize) {
            throw new IllegalStateException("스택이 가득 찼습니다");
        }
        internal.push(item);
    }

    // 비어 있으면 EmptyStackException
    public T pop() {
        if (internal.isEmpty()) {
            throw new EmptyStackException();
        }
        return internal.pop();
    }

    // peek - 제거하지 않고 최상위 요소만 반환
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
@DisplayName("CustomStack 테스트")
class CustomStackTest {

    // 모든 @Nested 클래스가 공유하는 SUT
    private CustomStack<String> stack;

    // 외부 클래스의 @BeforeEach - 모든 중첩 테스트 전에 먼저 실행됨
    @BeforeEach
    void setUp() {
        // 최대 크기 3의 스택으로 매번 새로 초기화
        stack = new CustomStack<>(3);
    }

    // @Nested: 내부(non-static) 클래스로 컨텍스트별 테스트 그룹화
    // BDD의 "When ... then ..." 흐름을 클래스 계층으로 표현
    @Nested
    @DisplayName("빈 스택일 때")
    class WhenEmpty {

        @Test
        @DisplayName("isEmpty()는 true를 반환한다")
        void isEmpty_returns_true() {
            // 외부 setUp만 실행된 상태 - 스택이 비어 있음
            assertTrue(stack.isEmpty());
        }

        @Test
        @DisplayName("size()는 0을 반환한다")
        void size_returns_zero() {
            assertEquals(0, stack.size());
        }

        @Test
        @DisplayName("pop()은 EmptyStackException을 던진다")
        void pop_throws_exception() {
            assertThrows(EmptyStackException.class, () -> stack.pop());
        }

        @Test
        @DisplayName("peek()은 EmptyStackException을 던진다")
        void peek_throws_exception() {
            assertThrows(EmptyStackException.class, () -> stack.peek());
        }
    }

    @Nested
    @DisplayName("요소가 있을 때")
    class WhenNotEmpty {

        // 내부 클래스의 @BeforeEach - 외부 @BeforeEach 이후 실행되어 컨텍스트를 추가 구성
        // 결과: 외부 setUp(스택 생성) -> 내부 pushElement(요소 2개 push) -> @Test
        @BeforeEach
        void pushElement() {
            stack.push("first");
            stack.push("second");
        }

        @Test
        @DisplayName("isEmpty()는 false를 반환한다")
        void isEmpty_returns_false() {
            assertFalse(stack.isEmpty());
        }

        @Test
        @DisplayName("size()는 요소 수를 반환한다")
        void size_returns_element_count() {
            assertEquals(2, stack.size());
        }

        @Test
        @DisplayName("peek()은 마지막 요소를 제거하지 않고 반환한다")
        void peek_returns_top_without_removing() {
            assertEquals("second", stack.peek());
            // 크기가 그대로(2) 유지되는지 검증
            assertEquals(2, stack.size());
        }

        @Test
        @DisplayName("pop()은 LIFO 순서로 요소를 반환한다")
        void pop_returns_in_lifo_order() {
            // 마지막에 push된 "second"가 먼저 나옴 (Last-In-First-Out)
            assertEquals("second", stack.pop());
            assertEquals("first", stack.pop());
            assertTrue(stack.isEmpty());
        }

        // @Nested 클래스는 더 깊게 중첩 가능 - "요소가 있을 때 + 가득 찼을 때"의 컨텍스트
        @Nested
        @DisplayName("스택이 가득 찼을 때")
        class WhenFull {

            // 실행 순서: setUp(외부) -> pushElement(상위 nested) -> fillStack(현재) -> @Test
            @BeforeEach
            void fillStack() {
                stack.push("third"); // 3개 모두 채움
            }

            @Test
            @DisplayName("push()는 IllegalStateException을 던진다")
            void push_throws_when_full() {
                assertEquals(3, stack.size());
                assertThrows(IllegalStateException.class,
                    () -> stack.push("overflow"));
            }
        }
    }
}
```

**실행 결과** — 실행하지 않음 — Java 예제는 이 문서를 만들 때 컴파일 · 실행하지 않았다(JDK 로 돌려 확인한다).

**풀이 요점**

- 상황 하나 = `@Nested` 내부 클래스 하나이고, 모두 `static` 없이 선언한다.
- 공통 준비(새 스택)는 바깥 `setUp()` 한 곳에만 두고, 안쪽은 `pushElement()` · `fillStack()` 으로 덧붙이기만 한다.
- `WhenFull` 을 `WhenNotEmpty` 안에 두어 `setUp` → `pushElement` → `fillStack` 순으로 쌓인 상태를 물려받는다.
- `peek` 테스트는 값과 크기를 함께 검사해 `pop` 과 구별한다.
- 예외는 `assertThrows(예외.class, () -> 호출)` 꼴로 검사한다.
- 준비가 테스트마다 다시 돌므로, 스택을 비우는 테스트가 있어도 다른 테스트는 영향을 받지 않는다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — Java 예제는 이 문서를 만들 때 컴파일 · 실행하지 않았다(JDK 로 돌려 확인한다) |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
