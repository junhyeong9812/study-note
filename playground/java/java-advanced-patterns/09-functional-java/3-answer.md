# java/java-advanced-patterns/09 — Functional Java (함수형 Java) — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. `Right(성인)` · `Left(숫자가 아님: abc)` · `Left(나이 범위 초과: -5)` — 실패 둘에서는 `classifyAge` 가 불리지 않는다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
Right(성인)
Left(숫자가 아님: abc)
Left(나이 범위 초과: -5)
```

`r2` · `r3` 를 만들 때 `classifyAge` 는 한 번도 불리지 않는다.

**왜 그런가**
`"25"` 는 숫자로 바뀌고 0~150 안이라 `Right(25)` 가 된다.
`flatMap` 이 `classifyAge(25)` 를 부르고, 25 는 65 미만이라 `Right("성인")` 이다.
`"abc"` 는 `NumberFormatException` 이 나서 `Left("숫자가 아님: abc")` 가 된다.
`"-5"` 는 숫자로는 바뀌지만 0 미만이라 `Left("나이 범위 초과: -5")` 다.
`Left` 의 `flatMap` 은 함수를 부르지 않고 왼쪽 값을 그대로 전파한다.
근거: 2-summary 「동작 방식 (1)」 · 「동작 방식 (2)」.

### 2. `10/0 -> Success(Infinity)` — 0 나눗셈이 실패가 아니다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
10/0 -> Success(Infinity)
```

**왜 그런가**
`n` 은 `Double` 이라 `n / 0` 은 부동소수점 나눗셈이고, 예외 없이 `Infinity` 가 된다.
`Try.map` 은 예외가 날 때만 `Failure` 를 만들므로 `Success(Infinity)` 가 이어진다.
`Infinity + 1` 도 `Infinity` 다.
근거: 2-summary 「동작 방식 (3)」 · 「어디서 틀리나 3」.

### 3. 다섯 개 — 이름 · 이메일 · 비밀번호 규칙 셋의 차례

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
검증 결과: Invalid([이름은 필수입니다, 이메일 형식이 잘못되었습니다, 비밀번호는 8자 이상이어야 합니다, 대문자가 포함되어야 합니다, 숫자가 포함되어야 합니다])
```

**왜 그런가**
`""` 는 `isBlank()` 라 「이름은 필수입니다」 하나다.
`"invalid"` 는 비어 있지 않지만 `@` 가 없어 「이메일 형식이 잘못되었습니다」 하나다.
`"short"` 는 5자라 8자 미만이고, 대문자도 숫자도 없어 에러 셋이 쌓인다.
`combine` 은 넘겨받은 차례(이름 → 이메일 → 비밀번호)로 에러를 이어 붙인다.
근거: 2-summary 「동작 방식 (4)」.

### 4. `map` 은 결과를 한 번 더 `Right` 로 감싸 상자가 겹친다

`classifyAge` 는 이미 `Either<String, String>` 을 돌려준다.
`map` 은 그 결과를 다시 `Either.right(...)` 로 감싸므로 타입이 `Either<String, Either<String, String>>` 이 된다.
`flatMap` 은 `fn` 의 결과를 감싸지 않고 그대로 돌려줘 한 겹으로 편다.
근거: 2-summary 「동작 방식 (2)」 · 「어디서 틀리나 1」.

### 5. 함수 안에서 난 예외도 `Failure` 로 흡수하려고

`Try.of` 는 넘겨받은 람다를 `try` 안에서 실행하고 `Exception` 을 잡아 실패로 바꾼다.
`map` 이 `fn.apply(value)` 를 `Try.of` 로 감싸면, 변환 함수가 던진 예외도 같은 길로 `Failure` 가 된다.
그래서 체인 어디서 예외가 나도 바깥으로 튀지 않는다.
근거: 2-summary 「동작 방식 (3)」.

### 6. `Left` 가 되지 않고 예외가 그대로 터진다

`Either.map` 은 `Either.right(fn.apply(right))` 만 하고 `try/catch` 가 없다.
`fn` 이 던진 예외는 `map` 을 부른 쪽으로 그대로 전파된다.
예외를 값으로 바꾸는 것은 `Try` 의 `map` · `flatMap` 뿐이다.
근거: 2-summary 「동작 방식 (2)」 · 「어디서 틀리나 2」.

### 7. 컴파일 단계에서 막힌다 — `Supplier.get()` 이 검사 예외를 선언하지 않아서

`Try.of` 는 `Supplier<T>` 를 받는다.
`Supplier.get()` 에는 `throws` 가 없으므로, 람다 안에서 `IOException` 을 던질 수 있는 호출을 하면 컴파일러가 거부한다.
`Try.of` 안의 `catch (Exception e)` 까지 가지 못한다.
그래서 「Try 는 checked exception 을 우아하게 처리한다」는 원본 팁은 이 구현에는 그대로 들어맞지 않는다.
근거: 2-summary 「어디서 틀리나 4」 · 「구현 세부사항 대 언어 보장」.

### 8. `true` — 판정이 에러 목록이 비었는지만 보기 때문이다

`isValid()` 는 `errors.isEmpty()` 만 돌려준다.
`invalid` 로 만들었어도 목록이 비었으면 `Valid` 로 판정되고, 값 칸은 `null` 이다.
`toString` 도 `Valid(null)` 꼴이 된다.
근거: 2-summary 「동작 방식 (4)」 · 「어디서 틀리나 5」.

### 9. 첫 에러 하나만 본다 — `flatMap` 은 첫 실패에서 멈춘다

`Either` 의 `flatMap` 은 앞이 `Left` 면 뒤 함수를 부르지 않는다.
그래서 이름이 틀리면 이메일 · 비밀번호는 검사되지도 않고, 사용자는 에러 하나를 고칠 때마다 다음 에러를 하나씩 보게 된다.
`Validation.combine` 은 모든 검증을 다 돌고 에러를 모아 한 번에 보여 준다.
근거: 2-summary 「동작 방식 (4)」 · 「동작 방식 (5)」.

### 10. `Either<Exception, T>` — 실패 쪽이 `Exception` 으로 정해져 있다

`Try` 의 성공은 값 `T`, 실패는 `Exception` 하나다.
`Either` 의 왼쪽을 `Exception` 으로 고정하면 같은 꼴이 된다.
둘 다 실패면 `map` · `flatMap` 이 함수를 건너뛰고 실패를 전파한다.
다른 점은 `Try` 의 `map` · `flatMap` 이 함수 안 예외까지 실패로 바꾼다는 것이다.
근거: 2-summary 「동작 방식 (5)」.

## 실습 정답

### 실습 1. `Either` · `Try` · `Validation` 을 직접 만들고 데모로 이어 보기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. `private` 생성자와 `left` · `right` 팩토리 | `private Either(...)` · `Either.left` · `Either.right` |
| 2. 판정 · 꺼내기 메서드 | `isRight` · `isLeft` · `getLeft` · `getRight` |
| 3. `Right` 일 때만 적용하는 `map` | `Either.map` 의 `if (isRight) return Either.right(fn.apply(right));` |
| 4. 평탄화하는 `flatMap` | `Either.flatMap` 의 `if (isRight) return fn.apply(right);` |
| 5. `Right(..)` · `Left(..)` 문자열 | `Either.toString` |
| 6. 예외를 잡아 실패로 담는 `of` | `Try.of` 의 `try { … supplier.get() … } catch (Exception e)` |
| 7. 팩토리와 「에러가 `null` 인가」 판정 | `Try.success` · `Try.failure` · `isSuccess` · `isFailure` |
| 8. `Try.of` 로 다시 감싸는 `map` | `Try.map` 의 `return Try.of(() -> fn.apply(value));` |
| 9. `try/catch` 로 감싼 `flatMap` | `Try.flatMap` |
| 10. 대체값 메서드 | `getOrElse` · `getOrElseGet` |
| 11. `Success(..)` · `Failure(메시지)` 문자열 | `Try.toString` 의 `error.getMessage()` |
| 12. 값 · 에러 목록과 팩토리 셋 | `Validation.valid` · `invalid(String)` · `invalid(List<String>)` |
| 13. 빈 목록이면 유효 | `Validation.isValid` 의 `errors.isEmpty()` |
| 14. 에러를 모으는 `combine` | `Validation.combine` 의 `allErrors.addAll(v.getErrors())` |
| 15. `Valid(..)` · `Invalid([..])` 문자열 | `Validation.toString` |
| 16. 나이 해석 | `parseAge` 의 `catch (NumberFormatException e)` 와 `age < 0 \|\| age > 150` |
| 17. 나이 분류 | `classifyAge` 의 `14` · `20` · `65` 비교 |
| 18. 이름 검증 | `validateName` |
| 19. 이메일 검증 | `validateEmail` 의 `email.contains("@")` |
| 20. 비밀번호 규칙 셋 누적 | `validatePassword` 의 `errors.add(...)` 세 줄 |
| 21. `Either` 데모 | `main` 의 `result1` · `result2` · `result3` |
| 22. `Try` 데모 | `main` 의 `t1` · `t2` · `t2.getOrElse(0)` · `t3` |
| 23. `Validation` 데모 | `main` 의 `signupResult` · `v2` |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`java/java-advanced-patterns/reference/functional-java.java`

```java
// [고급 패턴 & 기법] Functional Java (함수형 Java)
// 설명: Java에서 함수형 프로그래밍 기법 적용. Either, Try, Validation 패턴으로 안전한 에러 처리
// 팁: Either는 예외 대신 값으로 에러를 표현하여 컴파일러의 도움을 받을 수 있다. Try는 checked exception을 우아하게 처리하는데 유용하다. Validation은 모든 에러를 한 번에 수집할 수 있어 폼 검증에 적합하다. Vavr 라이브러리를 사용하면 이런 타입들을 바로 쓸 수 있다.

// === 함수형 Java: Either, Try, Validation 패턴 ===

// 컬렉션
import java.util.*;
// 함수형 인터페이스 — map/flatMap에 사용
import java.util.function.Function;
// 지연 평가 (Try.of)
import java.util.function.Supplier;
// 스트림 수집
import java.util.stream.Collectors;

// === Either<L, R>: 성공(Right) 또는 실패(Left) ===
// 관례: Right는 성공(올바른), Left는 실패. 두 갈래 중 하나만 유효한 합집합 타입.
class Either<L, R> {
    private final L left;
    private final R right;
    // 어느 쪽이 유효한지 플래그
    private final boolean isRight;

    // 외부에서 직접 생성 금지 — 정적 팩토리로만 생성 (의도 명확화)
    private Either(L left, R right, boolean isRight) {
        this.left = left;
        this.right = right;
        this.isRight = isRight;
    }

    // 실패 값 생성 (Left)
    public static <L, R> Either<L, R> left(L value) {
        return new Either<>(value, null, false);
    }

    // 성공 값 생성 (Right)
    public static <L, R> Either<L, R> right(R value) {
        return new Either<>(null, value, true);
    }

    public boolean isRight() { return isRight; }
    public boolean isLeft() { return !isRight; }
    public L getLeft() { return left; }
    public R getRight() { return right; }

    // map: Right 값 변환
    // 성공이면 함수 적용, 실패면 그대로 전파 (단락 평가)
    public <T> Either<L, T> map(Function<R, T> fn) {
        if (isRight) return Either.right(fn.apply(right));
        return Either.left(left);
    }

    // flatMap: 체이닝
    // fn이 Either를 반환 → 중첩 없이 평탄화 (모나드의 핵심)
    public <T> Either<L, T> flatMap(Function<R, Either<L, T>> fn) {
        if (isRight) return fn.apply(right);
        return Either.left(left);
    }

    @Override
    public String toString() {
        return isRight ? "Right(" + right + ")" : "Left(" + left + ")";
    }
}

// === Try<T>: 예외를 값으로 처리 ===
// 검사 예외/비검사 예외를 모두 값으로 흡수 — try/catch 분산 제거
class Try<T> {
    private final T value;
    private final Exception error;

    private Try(T value, Exception error) {
        this.value = value;
        this.error = error;
    }

    // 람다 실행을 감싸 예외를 Failure로 변환
    public static <T> Try<T> of(Supplier<T> supplier) {
        try {
            return new Try<>(supplier.get(), null);
        } catch (Exception e) {
            return new Try<>(null, e);
        }
    }

    public static <T> Try<T> success(T value) {
        return new Try<>(value, null);
    }

    public static <T> Try<T> failure(Exception error) {
        return new Try<>(null, error);
    }

    public boolean isSuccess() { return error == null; }
    public boolean isFailure() { return error != null; }
    public T getValue() { return value; }
    public Exception getError() { return error; }

    // map: 값 변환 — fn 안에서 던진 예외도 Failure로 흡수 (Try.of 재사용)
    public <R> Try<R> map(Function<T, R> fn) {
        if (isSuccess()) {
            return Try.of(() -> fn.apply(value));
        }
        return Try.failure(error);
    }

    // flatMap: 체이닝 — fn 자체가 던진 예외도 안전하게 캡처
    public <R> Try<R> flatMap(Function<T, Try<R>> fn) {
        if (isSuccess()) {
            try { return fn.apply(value); }
            catch (Exception e) { return Try.failure(e); }
        }
        return Try.failure(error);
    }

    // 실패 시 기본값 반환
    public T getOrElse(T defaultValue) {
        return isSuccess() ? value : defaultValue;
    }

    // 실패 시 예외 정보로 대체값 계산
    public T getOrElseGet(Function<Exception, T> fn) {
        return isSuccess() ? value : fn.apply(error);
    }

    @Override
    public String toString() {
        return isSuccess() ? "Success(" + value + ")" : "Failure(" + error.getMessage() + ")";
    }
}

// === Validation: 에러를 누적하는 검증 ===
// Either와 달리 첫 실패에서 멈추지 않고 모든 에러 수집 — 폼 검증에 적합
class Validation<T> {
    private final T value;
    // 빈 리스트면 valid, 아니면 invalid
    private final List<String> errors;

    private Validation(T value, List<String> errors) {
        this.value = value;
        this.errors = errors;
    }

    public static <T> Validation<T> valid(T value) {
        return new Validation<>(value, List.of());
    }

    public static <T> Validation<T> invalid(String error) {
        return new Validation<>(null, List.of(error));
    }

    public static <T> Validation<T> invalid(List<String> errors) {
        return new Validation<>(null, errors);
    }

    public boolean isValid() { return errors.isEmpty(); }
    public T getValue() { return value; }
    public List<String> getErrors() { return errors; }

    // 여러 Validation을 합침 (에러 누적)
    // 모두 성공이면 valid(value), 하나라도 실패면 모든 에러 합쳐서 invalid
    public static <T> Validation<T> combine(T value, Validation<?>... validations) {
        List<String> allErrors = new ArrayList<>();
        for (Validation<?> v : validations) {
            allErrors.addAll(v.getErrors());
        }
        return allErrors.isEmpty() ? valid(value) : invalid(allErrors);
    }

    @Override
    public String toString() {
        return isValid() ? "Valid(" + value + ")" : "Invalid(" + errors + ")";
    }
}

public class FunctionalJavaDemo {
    // Either를 사용한 사용자 검증
    // 예외 던지지 않고 Left/Right로 결과 표현
    static Either<String, Integer> parseAge(String input) {
        try {
            int age = Integer.parseInt(input);
            if (age < 0 || age > 150) return Either.left("나이 범위 초과: " + age);
            return Either.right(age);
        } catch (NumberFormatException e) {
            return Either.left("숫자가 아님: " + input);
        }
    }

    // 모두 성공으로 분류 — 실패 가능성 없음을 시그니처로 표현 어려움 (Either의 한계)
    static Either<String, String> classifyAge(int age) {
        if (age < 14) return Either.right("어린이");
        if (age < 20) return Either.right("청소년");
        if (age < 65) return Either.right("성인");
        return Either.right("시니어");
    }

    // Validation을 사용한 회원가입 검증
    // 이름 검증 — 단일 에러 반환
    static Validation<String> validateName(String name) {
        if (name == null || name.isBlank()) return Validation.invalid("이름은 필수입니다");
        if (name.length() < 2) return Validation.invalid("이름은 2자 이상이어야 합니다");
        return Validation.valid(name);
    }

    // 이메일 검증
    static Validation<String> validateEmail(String email) {
        if (email == null || email.isBlank()) return Validation.invalid("이메일은 필수입니다");
        if (!email.contains("@")) return Validation.invalid("이메일 형식이 잘못되었습니다");
        return Validation.valid(email);
    }

    // 비밀번호 검증 — 다중 규칙을 한 번에 평가하여 에러 누적
    static Validation<String> validatePassword(String password) {
        List<String> errors = new ArrayList<>();
        if (password == null || password.length() < 8) errors.add("비밀번호는 8자 이상이어야 합니다");
        if (password != null && !password.matches(".*[A-Z].*")) errors.add("대문자가 포함되어야 합니다");
        if (password != null && !password.matches(".*[0-9].*")) errors.add("숫자가 포함되어야 합니다");
        return errors.isEmpty() ? Validation.valid(password) : Validation.invalid(errors);
    }

    public static void main(String[] args) {
        // 1. Either 체이닝
        // flatMap으로 다음 단계 체인 — 실패는 자동 전파
        System.out.println("=== Either ===");
        Either<String, String> result1 = parseAge("25").flatMap(age -> classifyAge(age));
        System.out.println("25 -> " + result1);

        Either<String, String> result2 = parseAge("abc").flatMap(age -> classifyAge(age));
        System.out.println("abc -> " + result2);

        Either<String, String> result3 = parseAge("-5").flatMap(age -> classifyAge(age));
        System.out.println("-5 -> " + result3);

        // 2. Try 체이닝
        // 예외를 던지지 않고 map으로 안전하게 변환 누적
        System.out.println("\n=== Try ===");
        Try<Integer> t1 = Try.of(() -> Integer.parseInt("42"))
            .map(n -> n * 2)
            .map(n -> n + 10);
        System.out.println("42 -> " + t1);

        Try<Integer> t2 = Try.of(() -> Integer.parseInt("not_a_number"))
            .map(n -> n * 2);
        System.out.println("not_a_number -> " + t2);
        System.out.println("기본값: " + t2.getOrElse(0));

        // 주의: double은 0으로 나눠도 ArithmeticException이 아닌 Infinity → 성공으로 처리됨
        Try<Double> t3 = Try.of(() -> 10.0)
            .map(n -> n / 0)
            .map(n -> n + 1);
        System.out.println("10/0 -> " + t3);

        // 3. Validation (에러 누적)
        // Either와 달리 모든 검증을 실행한 뒤 에러를 합침
        System.out.println("\n=== Validation ===");
        Validation<String> nameV = validateName("");
        Validation<String> emailV = validateEmail("invalid");
        Validation<String> passV = validatePassword("short");

        Validation<String> signupResult = Validation.combine("signup", nameV, emailV, passV);
        System.out.println("검증 결과: " + signupResult);

        // 성공 케이스
        Validation<String> v2 = Validation.combine("signup",
            validateName("홍길동"),
            validateEmail("hong@test.com"),
            validatePassword("MyPass123"));
        System.out.println("성공 검증: " + v2);

        // 출력:
        // === Either ===
        // 25 -> Right(성인)
        // abc -> Left(숫자가 아님: abc)
        // -5 -> Left(나이 범위 초과: -5)
        //
        // === Try ===
        // 42 -> Success(94)
        // not_a_number -> Failure(For input string: "not_a_number")
        // 기본값: 0
        // 10/0 -> Success(Infinity)
        //
        // === Validation ===
        // 검증 결과: Invalid([이름은 필수입니다, 이메일 형식이 잘못되었습니다, 비밀번호는 8자 이상이어야 합니다, 대문자가 포함되어야 합니다, 숫자가 포함되어야 합니다])
        // 성공 검증: Valid(signup)
    }
}
```

**실행 결과** — 실행하지 않음 — Java 예제는 이 문서를 만들 때 컴파일 · 실행하지 않았다(JDK 로 돌려 확인한다).

**풀이 요점**

- 세 타입 모두 `private` 생성자 + 정적 팩토리라, 만드는 쪽의 의도(성공인가 실패인가)가 이름에 드러난다.
- `map` · `flatMap` 의 뼈대는 같다 — 성공이면 함수를 부르고, 실패면 실패를 새 객체에 담아 전파한다.
- `Try` 만 `map` · `flatMap` 에서 함수 안 예외까지 잡는다 — `Either.map` 에는 `try/catch` 가 없다.
- `Validation.combine` 은 멈추지 않고 모든 검증의 에러를 넘겨받은 차례대로 모으며, 성공 값은 첫 인자다.
- `validatePassword` 는 한 칸 안에서도 `if` 셋을 모두 검사해 에러를 쌓는다 — `else` 로 잇지 않는 것이 핵심이다.
- `10.0 / 0` 은 예외가 아니라 `Infinity` 라서 `Try` 체인은 성공으로 끝난다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — Java 예제는 이 문서를 만들 때 컴파일 · 실행하지 않았다(JDK 로 돌려 확인한다) |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
