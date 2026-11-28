# java/java-advanced-patterns/09 — Functional Java (함수형 Java) — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. `parseAge` 에 세 입력을 넣고 `flatMap` 으로 이으면 (예측)

```java
// 질문용 발췌
Either<String, String> r1 = parseAge("25").flatMap(age -> classifyAge(age));
Either<String, String> r2 = parseAge("abc").flatMap(age -> classifyAge(age));
Either<String, String> r3 = parseAge("-5").flatMap(age -> classifyAge(age));
System.out.println(r1); System.out.println(r2); System.out.println(r3);
```

- 세 줄에는 각각 무엇이 찍히나?
- `r2` 와 `r3` 를 만들 때 `classifyAge` 는 불리나?

### 2. `Try` 체인에서 `10.0` 을 0 으로 나누면 (예측)

```java
// 질문용 발췌
Try<Double> t3 = Try.of(() -> 10.0)
    .map(n -> n / 0)
    .map(n -> n + 1);
System.out.println("10/0 -> " + t3);
```

- 이 줄에는 무엇이 찍히나?

### 3. 가입 폼 세 칸이 모두 틀렸을 때 `combine` 하면 (예측)

```java
// 질문용 발췌
Validation<String> r = Validation.combine("signup",
    validateName(""), validateEmail("invalid"), validatePassword("short"));
System.out.println("검증 결과: " + r);
```

- 에러는 몇 개가 어떤 차례로 모이나?

### 4. `classifyAge` 를 잇는 데 `map` 이 아니라 `flatMap` 을 쓰는 까닭 (왜)

- `parseAge("25").map(age -> classifyAge(age))` 로 쓰면 결과 타입이 왜 문제가 되나?

### 5. `Try.map` 이 `Try.of` 를 다시 부르는 까닭 (왜)

- `Try.map` 이 `fn.apply(value)` 를 그냥 부르지 않고 `Try.of` 로 감싸는 것은 무엇을 위해서인가?

### 6. `Either.map` 에 넘긴 함수가 예외를 던지면 (경계)

- `Right` 에 `map` 을 걸었는데 그 함수가 예외를 던지면 결과는 `Left` 가 되나, 아니면 어떻게 되나?

### 7. 검사 예외를 던지는 메서드를 `Try.of` 로 감싸면 (경계)

- `throws IOException` 이 선언된 메서드를 부르는 람다를 이 구현의 `Try.of` 에 넘기면 어디서 막히나?

### 8. `Validation.invalid` 에 빈 목록을 넘기면 (경계)

- `Validation.invalid(new ArrayList<>())` 로 만든 객체의 `isValid()` 는 무엇을 돌려주나?

### 9. 폼 검증에 `Either` 대신 `Validation` 을 쓰는 까닭 (연결)

- 같은 세 칸 검증을 `Either` 의 `flatMap` 으로 이으면 사용자는 에러를 몇 개 보게 되나?

### 10. `Try<T>` 를 `Either` 로 옮겨 적으면 (연결)

- `Try<T>` 는 어떤 꼴의 `Either` 와 대응하고, 실패 쪽 타입이 무엇으로 정해져 있나?

## 실습

### 실습 1. `Either` · `Try` · `Validation` 을 직접 만들고 데모로 이어 보기

**만들 것** — 세 상자 타입을 직접 구현하고, 나이 분류 · 숫자 변환 · 회원가입 검증 데모를 `main` 에서 돌린다.

**요구 조건**

1단계 — `Either<L, R>`

1. 생성자는 `private` 이고 `left(값)` · `right(값)` 정적 팩토리로만 만든다.
2. `isRight` · `isLeft` · `getLeft` · `getRight` 를 둔다.
3. `map(fn)` 은 `Right` 일 때만 `fn` 을 적용해 `Right` 로 감싸고, `Left` 면 같은 왼쪽 값의 `Left` 를 돌려준다.
4. `flatMap(fn)` 은 `Right` 일 때 `fn` 이 돌려준 `Either` 를 그대로 돌려주고, `Left` 면 왼쪽 값을 전파한다.
5. `toString` 은 `Right(값)` 또는 `Left(값)` 꼴이다.

2단계 — `Try<T>`

6. `of(supplier)` 는 `supplier.get()` 을 실행해 값이면 성공, `Exception` 이면 실패를 담는다.
7. `success` · `failure` 정적 팩토리를 두고, 성공 판정은 「에러가 `null` 인가」로 한다.
8. `map` 은 성공일 때 `Try.of` 로 함수를 다시 감싸 함수 안 예외도 실패로 바꾸고, 실패면 같은 예외를 전파한다.
9. `flatMap` 은 성공일 때 함수를 `try/catch` 로 감싸 실행하고, 실패면 같은 예외를 전파한다.
10. `getOrElse(기본값)` 과 `getOrElseGet(예외 → 대체값 함수)` 를 둔다.
11. `toString` 은 `Success(값)` 또는 `Failure(예외 메시지)` 꼴이다.

3단계 — `Validation<T>`

12. 값과 에러 목록을 갖고, `valid(값)` · `invalid(에러 하나)` · `invalid(에러 목록)` 으로 만든다.
13. `isValid` 는 에러 목록이 비었는지로 정한다.
14. 정적 메서드 `combine(값, 검증들...)` 는 모든 검증의 에러를 차례대로 모아, 비었으면 `valid(값)`, 아니면 `invalid(모은 에러)` 를 돌려준다.
15. `toString` 은 `Valid(값)` 또는 `Invalid([에러, …])` 꼴이다.

4단계 — 도메인 함수(`FunctionalJavaDemo` 안)

16. `parseAge(문자열)` 는 숫자가 아니면 `Left("숫자가 아님: 입력")`, 0 미만이나 150 초과면 `Left("나이 범위 초과: 나이")`, 아니면 `Right(나이)` 를 돌려준다.
17. `classifyAge(나이)` 는 14 미만 「어린이」, 20 미만 「청소년」, 65 미만 「성인」, 그 밖은 「시니어」를 `Right` 로 돌려준다.
18. `validateName` 은 비었으면 「이름은 필수입니다」, 2자 미만이면 「이름은 2자 이상이어야 합니다」를 에러로 낸다.
19. `validateEmail` 은 비었으면 「이메일은 필수입니다」, `@` 가 없으면 「이메일 형식이 잘못되었습니다」를 에러로 낸다.
20. `validatePassword` 는 8자 미만 · 대문자 없음 · 숫자 없음 세 규칙을 모두 검사해 해당하는 에러를 전부 쌓는다.

5단계 — `main`

21. `=== Either ===` 아래에서 `"25"` · `"abc"` · `"-5"` 를 `parseAge` 에 넣고 `flatMap` 으로 `classifyAge` 를 이어 찍는다.
22. `=== Try ===` 아래에서 `"42"` 를 변환해 `* 2` · `+ 10` 을 `map` 으로 잇고, `"not_a_number"` 를 변환해 `* 2` 를 잇고 `getOrElse(0)` 도 찍고, `10.0` 에 `/ 0` · `+ 1` 을 잇는다.
23. `=== Validation ===` 아래에서 빈 이름 · `"invalid"` 이메일 · `"short"` 비밀번호를 `combine` 해 찍고, `"홍길동"` · `"hong@test.com"` · `"MyPass123"` 도 `combine` 해 찍는다.

**시작 코드**

```java
import java.util.*;
import java.util.function.Function;
import java.util.function.Supplier;

class Either<L, R> {
    private final L left;
    private final R right;
    private final boolean isRight;

    private Either(L left, R right, boolean isRight) {
        this.left = left;
        this.right = right;
        this.isRight = isRight;
    }

    public static <L, R> Either<L, R> left(L value) { /* TODO */ return null; }
    public static <L, R> Either<L, R> right(R value) { /* TODO */ return null; }

    public boolean isRight() { return isRight; }
    public boolean isLeft() { return !isRight; }
    public L getLeft() { return left; }
    public R getRight() { return right; }

    public <T> Either<L, T> map(Function<R, T> fn) {
        // TODO: Right 면 fn 적용 후 Right 로 감싸기, Left 면 전파
        return null;
    }

    public <T> Either<L, T> flatMap(Function<R, Either<L, T>> fn) {
        // TODO: Right 면 fn 결과를 그대로, Left 면 전파
        return null;
    }

    @Override
    public String toString() { /* TODO: Right(..) / Left(..) */ return ""; }
}

class Try<T> {
    private final T value;
    private final Exception error;

    private Try(T value, Exception error) {
        this.value = value;
        this.error = error;
    }

    public static <T> Try<T> of(Supplier<T> supplier) {
        // TODO: 실행해서 값이면 성공, Exception 이면 실패
        return null;
    }

    public static <T> Try<T> success(T value) { return new Try<>(value, null); }
    public static <T> Try<T> failure(Exception error) { return new Try<>(null, error); }

    public boolean isSuccess() { /* TODO */ return false; }
    public boolean isFailure() { /* TODO */ return false; }
    public T getValue() { return value; }
    public Exception getError() { return error; }

    public <R> Try<R> map(Function<T, R> fn) {
        // TODO: 성공이면 Try.of 로 감싸 실행, 실패면 전파
        return null;
    }

    public <R> Try<R> flatMap(Function<T, Try<R>> fn) {
        // TODO: 성공이면 try/catch 로 감싸 실행, 실패면 전파
        return null;
    }

    public T getOrElse(T defaultValue) { /* TODO */ return null; }
    public T getOrElseGet(Function<Exception, T> fn) { /* TODO */ return null; }

    @Override
    public String toString() { /* TODO: Success(..) / Failure(메시지) */ return ""; }
}

class Validation<T> {
    private final T value;
    private final List<String> errors;

    private Validation(T value, List<String> errors) {
        this.value = value;
        this.errors = errors;
    }

    public static <T> Validation<T> valid(T value) { /* TODO */ return null; }
    public static <T> Validation<T> invalid(String error) { /* TODO */ return null; }
    public static <T> Validation<T> invalid(List<String> errors) { /* TODO */ return null; }

    public boolean isValid() { /* TODO */ return false; }
    public T getValue() { return value; }
    public List<String> getErrors() { return errors; }

    public static <T> Validation<T> combine(T value, Validation<?>... validations) {
        // TODO: 모든 에러를 차례대로 모아 valid / invalid 결정
        return null;
    }

    @Override
    public String toString() { /* TODO: Valid(..) / Invalid([..]) */ return ""; }
}

public class FunctionalJavaDemo {
    static Either<String, Integer> parseAge(String input) {
        // TODO: 숫자 아님 / 범위 초과 / 성공
        return null;
    }

    static Either<String, String> classifyAge(int age) {
        // TODO: 14 · 20 · 65 를 경계로 분류
        return null;
    }

    static Validation<String> validateName(String name) { /* TODO */ return null; }
    static Validation<String> validateEmail(String email) { /* TODO */ return null; }

    static Validation<String> validatePassword(String password) {
        List<String> errors = new ArrayList<>();
        // TODO: 8자 이상 · 대문자 포함 · 숫자 포함 — 셋 다 검사해 쌓기
        return null;
    }

    public static void main(String[] args) {
        System.out.println("=== Either ===");
        // TODO: "25" · "abc" · "-5" 를 parseAge → flatMap(classifyAge)

        System.out.println("\n=== Try ===");
        // TODO: "42" 체인 · "not_a_number" 체인과 getOrElse(0) · 10.0 / 0 체인

        System.out.println("\n=== Validation ===");
        // TODO: 실패 케이스 combine · 성공 케이스 combine
    }
}
```

**확인 방법** — 파일을 `FunctionalJavaDemo.java` 로 저장하고 `javac FunctionalJavaDemo.java && java FunctionalJavaDemo` 로 돌린다.
`Either` 세 줄 · `Try` 네 줄 · `Validation` 두 줄이 찍히는지, 퀴즈 1~3 의 답과 맞는지 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
