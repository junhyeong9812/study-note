# java/java-testing/04 — JUnit 5 @Nested 테스트 — 정리 (힌트)

> 출처 — study-site 항목 `java/junit5-nested`(항목 데이터 `data/java/testing.json`) · 정답 코드 study-practice `java/java-testing/reference/junit5-nested.java`\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).\
> 실행 — 실행하지 않음 — Java 예제는 이 문서를 만들 때 컴파일 · 실행하지 않았다(JDK 로 돌려 확인한다).

## 한눈에 — 쉽게 말하면

**`@Nested` 테스트는 「서랍 안의 칸막이 상자」다.**
큰 서랍(바깥 테스트 클래스)에 공통 준비물이 깔려 있다.
그 안에 「빈 상태」 상자와 「요소가 있는 상태」 상자가 따로 놓인다.
「요소가 있는 상태」 상자 안에는 「가득 찬 상태」라는 더 작은 상자가 또 들어 있다.
작은 상자를 열려면 바깥 서랍부터 차례로 열어야 하듯, 안쪽 테스트가 돌기 전에는 바깥 준비가 먼저 끝난다.
JUnit 5 의 `@Nested` 도 똑같은 구조다.

| 비유 | 실체 |
|---|---|
| 큰 서랍 | 바깥 테스트 클래스 `CustomStackTest` |
| 서랍 바닥에 깔린 공통 준비물 | 바깥 `@BeforeEach` 인 `setUp()` (새 스택 생성) |
| 칸막이 상자 | `@Nested` 내부 클래스 (`WhenEmpty` · `WhenNotEmpty`) |
| 상자 안의 더 작은 상자 | 한 번 더 중첩된 `WhenFull` |
| 상자를 열 때마다 하는 준비 | 각 내부 클래스의 `@BeforeEach` |
| 상자 속 물건 하나 | `@Test` 메서드 하나 |

```text
CustomStackTest            setUp(): 크기 3 스택 생성
├── WhenEmpty              (추가 준비 없음)
│     └── @Test × 4
└── WhenNotEmpty           pushElement(): "first","second" push
      ├── @Test × 4
      └── WhenFull         fillStack(): "third" push
            └── @Test × 1
```

## 이 주제가 답하려는 질문

1. 관련 있는 테스트를 「상황(컨텍스트)」별로 어떻게 묶어 계층으로 보이게 하나?
2. 중첩된 클래스마다 있는 `@BeforeEach` 는 어떤 순서로 실행되나?
3. 왜 `@Nested` 클래스는 `static` 이 아닌 내부 클래스여야 하나?
4. 이 구조가 Given-When-Then 스타일과 어떻게 맞물리나?

## 동작 방식

### (1) `@Nested` 로 상황별 테스트를 클래스로 묶는다

**언제 쓰나** — 같은 대상을 「빈 상태」 「요소가 있는 상태」 「가득 찬 상태」처럼 여러 상황에서 검사할 때 쓴다.
테스트 이름에 상황을 일일이 붙이는 대신, 상황을 클래스 이름과 `@DisplayName` 으로 한 번만 적는다.

```text
입력 코드                                 무엇이 일어나나                     결과
@DisplayName("CustomStack 테스트")
class CustomStackTest {           →  바깥 클래스가 뿌리가 된다        →  CustomStack 테스트
  @Nested @DisplayName("빈 스택일 때")                                     ├ 빈 스택일 때
  class WhenEmpty { @Test ... }   →  내부 클래스가 가지가 된다          │   └ isEmpty()는 true를 반환한다 …
  @Nested @DisplayName("요소가 있을 때")                                   └ 요소가 있을 때
  class WhenNotEmpty {                                                       ├ size()는 요소 수를 반환한다 …
    @Nested class WhenFull {...}  →  더 깊은 가지도 만들 수 있다            └ 스택이 가득 찼을 때 …
  }
}
```

- 바깥 클래스 하나가 테스트 묶음의 뿌리가 된다.
- `@Nested` 가 붙은 내부 클래스 하나가 상황 하나를 나타내는 가지가 된다.
- `@Nested` 클래스 안에 또 `@Nested` 클래스를 두면 「요소가 있을 때 + 가득 찼을 때」처럼 상황을 좁혀 갈 수 있다.
- `@DisplayName` 은 클래스와 메서드에 사람이 읽는 이름을 붙여, 계층이 문장처럼 읽히게 한다.

> **`@Nested`** — 테스트 클래스 안의 내부 클래스를 「중첩 테스트 묶음」으로 표시하는 JUnit 5 어노테이션.\
> 예: `@Nested class WhenEmpty { ... }` 는 「빈 스택일 때」 묶음이다.

> **`@DisplayName`** — 테스트 클래스나 메서드에 표시용 이름을 붙이는 어노테이션.\
> 예: `@DisplayName("빈 스택일 때")`.

### (2) `@BeforeEach` 는 바깥에서 안으로 차례로 쌓인다

**언제 쓰나** — 안쪽 상황이 바깥 상황을 「조금 더 진행한 것」일 때 쓴다.
안쪽 `@BeforeEach` 는 바깥 준비가 끝난 상태에 준비를 덧붙이기만 하면 된다.

```text
WhenFull 의 push_throws_when_full() 하나를 실행하면

  setUp()          (CustomStackTest)   stack = new CustomStack<>(3)   → []
     ↓
  pushElement()    (WhenNotEmpty)      push "first", push "second"    → [first, second]
     ↓
  fillStack()      (WhenFull)          push "third"                   → [first, second, third]
     ↓
  @Test            push_throws_when_full()
                   size()==3 확인 → push("overflow") 가 IllegalStateException 을 던지는지 확인
```

- 먼저 가장 바깥 클래스의 `setUp()` 이 돌아 크기 3짜리 새 스택을 만든다.
- 다음으로 한 칸 안쪽 `WhenNotEmpty` 의 `pushElement()` 가 요소 둘을 넣는다.
- 그다음 가장 안쪽 `WhenFull` 의 `fillStack()` 이 하나를 더 넣어 스택을 채운다.
- 마지막으로 테스트 메서드가 돈다.
- `WhenEmpty` 의 테스트라면 `setUp()` 다음에 바로 테스트가 돈다 — `WhenEmpty` 에는 자기 `@BeforeEach` 가 없기 때문이다.

> **`@BeforeEach`** — 그 클래스의 테스트 메서드 하나하나가 실행되기 직전에 매번 도는 준비 메서드를 표시하는 어노테이션.\
> 예: `@BeforeEach void setUp() { stack = new CustomStack<>(3); }`.

### (3) 테스트마다 준비를 처음부터 다시 한다

**언제 쓰나** — 한 테스트가 상태를 바꿔도 다른 테스트에 번지지 않게 할 때 기대는 성질이다.

```text
pop_returns_in_lifo_order()      setUp → pushElement → [first, second] → pop, pop → []
                                                                         (끝)
size_returns_element_count()     setUp → pushElement → [first, second] → size()==2 ✔
                                 ↑ 앞 테스트가 비운 스택을 이어받지 않는다
```

- `@BeforeEach` 는 「테스트마다」 돈다.
- 그래서 `setUp()` 이 매번 `new CustomStack<>(3)` 으로 새 스택을 만들고, 안쪽 준비가 그 위에 다시 쌓인다.
- `pop_returns_in_lifo_order()` 가 스택을 비워도, 다음 테스트는 다시 `[first, second]` 에서 시작한다.
- 그래서 각 테스트는 다른 테스트가 언제 돌았는지 신경 쓰지 않아도 된다.

### (4) 내부 클래스라서 바깥 필드를 그대로 본다

**언제 쓰나** — 안쪽 테스트가 바깥에서 만든 대상(`stack`)과 바깥 준비 결과를 함께 써야 할 때다.

```text
class CustomStackTest {
    private CustomStack<String> stack;        ← 바깥 인스턴스의 필드
    @Nested class WhenNotEmpty {               ← static 없음 = 내부 클래스
        void pushElement() { stack.push(..) }  ← 바깥 인스턴스의 stack 을 그대로 씀
    }
}
```

- `@Nested` 클래스는 내부 클래스(non-static inner class)여야 한다.
- Java 에서 내부 클래스의 객체는 바깥 클래스의 객체에 묶여 있어서, 바깥 인스턴스의 필드 `stack` 을 이름만으로 쓸 수 있다.
- `static` 이 붙은 중첩 클래스는 바깥 객체에 묶이지 않으므로 인스턴스 필드 `stack` 을 그냥 쓸 수 없다 — 이 예제처럼 `stack` 을 쓰는 코드라면 컴파일부터 되지 않는다.
- 바깥 `setUp()` 이 채운 그 `stack` 을 안쪽이 이어 쓰기 때문에 (2)의 「쌓이는 준비」가 성립한다.

> **내부 클래스(inner class)** — 다른 클래스 안에 `static` 없이 선언되어, 바깥 클래스의 객체에 묶여 있는 클래스.\
> 예: `class WhenEmpty { ... }` 는 `CustomStackTest` 객체의 필드를 볼 수 있다.

### (5) 테스트 대상: 세 가지 상태가 있는 `CustomStack`

**언제 쓰나** — `@Nested` 를 연습하기 좋은 대상은 상태에 따라 행동이 달라지는 클래스다.
`CustomStack` 은 「비어 있음 · 요소 있음 · 가득 참」 세 상태가 뚜렷하다.

```text
상태          isEmpty   size   push(x)                      pop() / peek()
비어 있음      true      0      들어간다                       EmptyStackException
요소 있음      false     1~2    들어간다                       맨 위 요소 (pop 은 제거, peek 은 그대로)
가득 참(3)     false     3      IllegalStateException          맨 위 요소
```

- `CustomStack` 은 `java.util.Stack` 을 필드 `internal` 로 들고 일을 맡긴다(위임, Composition).
- `push` 는 `internal.size() >= maxSize` 이면 `IllegalStateException("스택이 가득 찼습니다")` 를 던진다.
- `pop` 과 `peek` 은 비어 있으면 `EmptyStackException` 을 던진다.
- `pop` 은 맨 위 요소를 꺼내 없애고, `peek` 은 맨 위 요소를 보여 주기만 하고 남겨 둔다.
- 나중에 넣은 것이 먼저 나온다(LIFO) — `"first"`, `"second"` 순으로 넣으면 `pop` 은 `"second"` 부터 돌려준다.

> **SUT(System Under Test)** — 테스트가 검사하는 대상.\
> 예: 여기서는 `CustomStack`.

> **LIFO(Last-In-First-Out)** — 마지막에 넣은 것이 먼저 나오는 순서.\
> 예: `first`, `second` 를 넣으면 `second` 가 먼저 나온다.

> **위임(Composition)** — 상속하지 않고 다른 객체를 필드로 들고 일을 맡기는 방식.\
> 예: `CustomStack` 의 `push` 는 검사 뒤 `internal.push(item)` 을 부른다.

### (6) Given-When-Then 과의 대응

**언제 쓰나** — 테스트를 「주어진 상황 → 일어난 일 → 기대 결과」로 읽히게 만들고 싶을 때다.

```text
Given  바깥 setUp()             크기 3 스택이 있다
When   @Nested 클래스 + 그 @BeforeEach   "요소가 있을 때" → 두 개 push 된 상태
Then   @Test + @DisplayName       "size()는 요소 수를 반환한다"
```

- 공통 전제는 바깥 `@BeforeEach` 에 둔다.
- 상황은 `@Nested` 클래스의 이름과 그 `@BeforeEach` 로 만든다.
- 기대 결과는 `@Test` 하나와 그 `@DisplayName` 으로 적는다.
- 상황 안에 상황을 더 넣으면(`WhenFull`) 「~이고 ~일 때」를 클래스 계층으로 표현할 수 있다.

> **Given-When-Then** — 테스트를 「전제 → 상황 · 행동 → 기대 결과」 세 부분으로 나눠 쓰는 방식.\
> 예: 「크기 3 스택에(Given) 요소가 둘 있을 때(When) size()는 2다(Then)」.

## 문법 — 형태와 규칙

```java
class OuterTest {
    private Thing thing;                    // 안쪽 묶음들이 함께 쓰는 대상

    @BeforeEach void setUp() { thing = new Thing(); }   // 1번째로 돈다

    @Nested @DisplayName("어떤 상황일 때")
    class WhenSomething {                    // static 을 붙이지 않는다
        @BeforeEach void more() { thing.change(); }     // 2번째로 돈다

        @Test @DisplayName("이렇게 된다")
        void result() { assertTrue(thing.ok()); }       // 3번째로 돈다
    }
}
```

- `@Nested` 는 테스트 클래스 **안에 있는 클래스**에 붙인다.
- `@Nested` 클래스는 `static` 이 없는 내부 클래스여야 한다.
- `@Nested` 클래스 안에 또 `@Nested` 클래스를 둘 수 있다(여러 단계 중첩).
- 바깥 `@BeforeEach` 가 먼저, 안쪽 `@BeforeEach` 가 나중에 돈다.
- 안쪽 클래스는 바깥 클래스의 필드를 이름으로 바로 쓴다.
- `@DisplayName` 은 바깥 클래스 · `@Nested` 클래스 · `@Test` 메서드 어디에나 붙일 수 있다.
- 예외를 검사할 때는 `assertThrows(예외클래스.class, () -> 호출)` 꼴을 쓴다.
- `import org.junit.jupiter.api.*;` 로 `@Test` · `@Nested` · `@BeforeEach` · `@DisplayName` 을 한 번에 가져오고, `import static org.junit.jupiter.api.Assertions.*;` 로 `assertTrue` · `assertEquals` · `assertThrows` 같은 검사 메서드를 가져온다.

## 어디서 틀리나

### 1. `@Nested` 클래스에 `static` 을 붙인다

습관처럼 `static class WhenEmpty` 로 쓰기 쉽다.
`@Nested` 클래스는 내부 클래스(non-static)여야 한다는 것이 규칙이다.
게다가 `static` 중첩 클래스는 바깥 인스턴스 필드 `stack` 을 쓸 수 없으므로, 이 예제 꼴이라면 컴파일 오류가 난다.

### 2. 안쪽 `@BeforeEach` 가 먼저 돈다고 생각한다

순서는 바깥 → 안쪽이다.
`WhenFull` 의 테스트 하나는 `setUp()` → `pushElement()` → `fillStack()` → 테스트 순으로 돈다.
안쪽 준비가 먼저라고 착각하면, `fillStack()` 이 `null` 인 `stack` 에 `push` 하는 그림을 떠올리게 된다.

### 3. 테스트끼리 스택을 이어 쓴다고 생각한다

`pop_returns_in_lifo_order()` 가 스택을 비워도 다른 테스트는 영향을 받지 않는다.
`@BeforeEach` 가 테스트마다 다시 돌아 새 스택부터 쌓기 때문이다.
반대로 말하면, 상태를 앞 테스트에 기대는 테스트를 쓰면 안 된다.

### 4. `peek` 을 값만 보고 검사한다

`peek()` 이 `"second"` 를 돌려준다는 것만 보면 `pop()` 과 구별되지 않는다.
「제거하지 않는다」를 보이려면 `peek()` 뒤에 `size()` 가 그대로 2인지 함께 확인해야 한다.

### 5. 상황을 엉뚱한 가지에 둔다

「가득 찼을 때」는 「요소가 있을 때」를 한 걸음 더 진행한 상황이다.
그래서 `WhenFull` 을 `WhenNotEmpty` 안에 두면 `pushElement()` 의 두 개를 물려받고 `fillStack()` 은 하나만 더 넣으면 된다.
`WhenFull` 을 바깥 클래스 바로 아래에 두면 세 개를 모두 직접 넣어야 하고, 「요소 있음」 준비와 중복된다.

### 6. 바깥 설정 값을 바꾸고 안쪽 기대를 그대로 둔다

안쪽 준비는 바깥 준비를 전제로 짜여 있다.
`setUp()` 의 최대 크기 3을 다른 값으로 바꾸면 `fillStack()` 이 하나만 넣어도 「가득 참」이 된다는 전제가 깨진다.
중첩이 깊을수록 바깥 한 줄이 아래 전부에 번진다는 점을 기억해야 한다.

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| 바깥 `@BeforeEach` 가 먼저, 안쪽 `@BeforeEach` 가 나중에 돈다 | JUnit 5(Jupiter)의 동작 규칙 |
| `@Nested` 클래스는 non-static 내부 클래스여야 한다 | JUnit 5 의 규칙 |
| `@BeforeEach` 는 테스트마다 다시 돈다 | JUnit 5 의 `@BeforeEach` 정의 |
| 내부 클래스는 바깥 인스턴스 필드를 이름으로 쓸 수 있고, `static` 중첩 클래스는 못 쓴다 | Java 언어 |
| 비었을 때 `EmptyStackException`, 가득 찼을 때 `IllegalStateException` | `CustomStack` 코드 자신(직접 `throw` 한다) |
| `java.util.Stack` 의 `pop` · `peek` 이 맨 위 요소를 다룬다(LIFO) | Java 표준 라이브러리 |
| `@DisplayName` 이 화면에 어떤 모양의 트리로 보이나 | IDE · 빌드 도구의 보고 화면 (확인 필요) |
| 같은 클래스 안 `@Test` 들이 소스에 적힌 순서대로 돈다 | 아무도 보장하지 않는다 — 순서에 기대지 않아야 한다 (확인 필요) |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 한 대상을 여러 상태(빈 · 일부 · 가득)에서 검사 | 상태마다 `@Nested` 클래스 | 테스트 이름에 상태를 매번 붙인 평평한 목록 |
| 어떤 상황이 다른 상황을 한 걸음 더 진행한 것 | 안쪽에 중첩하고 `@BeforeEach` 로 덧붙이기 | 같은 준비를 여러 클래스에 복사 |
| 모든 테스트에 공통인 준비 | 바깥 `@BeforeEach` | 안쪽마다 같은 생성 코드 반복 |
| 안쪽에서 바깥 필드를 써야 함 | 내부 클래스(`static` 없음) | `static` 중첩 클래스 |
| 상태가 하나뿐인 단순한 대상 | 평평한 테스트 클래스 하나 | 의미 없는 깊은 중첩 |

## 핵심 문장

1. **`@Nested` 는 상황별 테스트를 내부 클래스로 묶어 계층을 만든다** — 클래스 이름과 `@DisplayName` 이 상황을 말한다.
2. **`@BeforeEach` 는 바깥에서 안으로 쌓인다** — 안쪽 준비는 바깥 준비 위에 덧붙이기만 한다.
3. **`@Nested` 클래스는 `static` 이 아닌 내부 클래스여야 한다** — 그래야 바깥 인스턴스의 필드와 준비 결과를 그대로 쓴다.
4. **준비는 테스트마다 처음부터 다시 돈다** — 테스트끼리 상태가 번지지 않는다.
5. **바깥 = Given, 중첩 클래스 = When, `@Test` = Then** 으로 읽으면 Given-When-Then 이 클래스 계층이 된다.

## 관련 자료

- `junit5-basics` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- `junit5-lifecycle` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- `junit5-display` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- 원본: study-site 항목 데이터 `data/java/testing.json` 의 `junit5-nested`

## 용어 풀이

- **`@Nested`** — 테스트 클래스 안의 내부 클래스를 중첩 테스트 묶음으로 표시하는 JUnit 5 어노테이션.
- **`@Test`** — 메서드 하나를 테스트로 표시하는 어노테이션.
- **`@BeforeEach`** — 테스트마다 그 직전에 도는 준비 메서드를 표시하는 어노테이션.
- **`@DisplayName`** — 테스트 클래스 · 메서드에 표시용 이름을 붙이는 어노테이션.
- **내부 클래스(inner class)** — `static` 없이 다른 클래스 안에 선언되어 바깥 객체에 묶인 클래스.
- **`static` 중첩 클래스** — 바깥 클래스 안에 있지만 바깥 객체에 묶이지 않은 클래스.
- **SUT** — 테스트가 검사하는 대상(여기서는 `CustomStack`).
- **LIFO** — 마지막에 넣은 것이 먼저 나오는 순서.
- **위임(Composition)** — 상속 대신 다른 객체를 필드로 들고 일을 맡기는 방식.
- **`assertThrows`** — 주어진 람다를 실행했을 때 지정한 예외가 나는지 검사하는 메서드.
- **`assertEquals` · `assertTrue` · `assertFalse`** — 값이 같은지 · 참인지 · 거짓인지 검사하는 메서드.
- **`EmptyStackException`** — 빈 스택에서 꺼내거나 볼 때 쓰는 표준 예외.
- **`IllegalStateException`** — 객체가 그 호출을 받을 수 없는 상태일 때 쓰는 표준 예외.
- **Given-When-Then** — 전제 · 상황 · 기대 결과로 테스트를 나누는 방식.
- **BDD** — 행동(동작)을 문장처럼 기술하는 데 무게를 두는 테스트 작성 방식.

## 더 들어가면

- `@AfterEach` 는 `@BeforeEach` 와 반대로 안쪽이 먼저, 바깥이 나중에 도는 것으로 알려져 있다 (확인 필요).
- `@Nested` 클래스 안의 `@BeforeAll` · `@AfterAll` 은 `static` 메서드 제약 때문에 예전 JUnit 5 버전에서는 `@TestInstance(Lifecycle.PER_CLASS)` 없이 쓸 수 없었고, 최근 버전에서 완화되었다고 한다 (확인 필요).
- 기본 설정에서 JUnit 5 는 테스트 메서드마다 테스트 클래스 인스턴스를 새로 만들며, `@Nested` 테스트를 돌릴 때는 바깥 인스턴스를 먼저 만들고 그것에 묶인 안쪽 인스턴스를 만든다 (확인 필요).
- `static` 중첩 클래스에 `@Nested` 를 붙였을 때 JUnit 이 그것을 조용히 건너뛰는지, 오류로 알리는지는 버전에 따라 다르다 (확인 필요).
- JUnit 5 는 테스트 클래스 · 메서드가 `public` 이 아니어도(패키지 전용이어도) 찾아 실행한다 (확인 필요).
- 같은 클래스 안 테스트의 실행 순서를 정하고 싶으면 `@TestMethodOrder` 를 쓸 수 있다 (확인 필요).
- `java.util.Stack` 은 오래된 동기화 컬렉션이라, 새 코드에서는 `ArrayDeque` 를 스택으로 쓰라는 권고가 흔하다 (확인 필요).
