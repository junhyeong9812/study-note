# java/java-advanced-patterns/09 — Functional Java (함수형 Java) — 정리 (힌트)

> 출처 — study-site 항목 `java/functional-java`(항목 데이터 `data/java/advanced-patterns.json`) · 정답 코드 study-practice `java/java-advanced-patterns/reference/functional-java.java`\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).\
> 실행 — 실행하지 않음 — Java 예제는 이 문서를 만들 때 컴파일 · 실행하지 않았다(JDK 로 돌려 확인한다).

## 한눈에 — 쉽게 말하면

**`Either` · `Try` · `Validation` 은 「택배 상자에 붙이는 송장」이다.**
상자(값)에 문제가 생겨도 상자를 내던지지 않는다.
「정상」인지 「파손」인지를 송장에 적어 다음 창구로 넘긴다.
「파손」 송장이 붙은 상자는 다음 창구가 열어 보지 않고 그대로 통과시킨다.
검수대(`Validation`)만 다르게 일한다.
검수대는 상자를 끝까지 다 살피고, 흠을 전부 목록에 적는다.
함수형 Java 의 에러 처리도 똑같은 구조다.
예외를 던져 흐름을 끊지 않고, 「성공 또는 실패」를 담은 **값**을 돌려준다.

| 비유 | 실체 |
|---|---|
| 상자 | 계산 결과를 담은 객체(`Either` · `Try` · `Validation`) |
| 「정상」 송장 | `Right(값)` · `Success(값)` · `Valid(값)` |
| 「파손」 송장 | `Left(에러)` · `Failure(예외)` · `Invalid(에러 목록)` |
| 다음 창구 | `map` · `flatMap` 에 넘긴 함수 |
| 파손 상자는 열지 않고 통과 | 실패면 함수를 부르지 않고 실패를 그대로 전파 |
| 흠을 전부 적는 검수대 | `Validation.combine` — 에러를 모두 모은다 |

```text
 입력 ──▶ [단계 1] ──▶ [단계 2] ──▶ [단계 3] ──▶ 결과 값
            │ 실패        (건너뜀)      (건너뜀)
            └──────────── Left/Failure 가 그대로 끝까지 흘러간다
```

## 이 주제가 답하려는 질문

1. 예외를 던지지 않고 「실패」를 어떻게 돌려주나?
2. 실패할 수 있는 단계를 여럿 이을 때, 앞 단계의 실패를 어떻게 뒤로 넘기나?
3. 예외를 던질 수 있는 코드를 어떻게 값으로 감싸나?
4. 첫 에러에서 멈추지 않고 모든 에러를 한 번에 모으려면 어떻게 하나?

## 동작 방식

### (1) `Either<L, R>` — 두 갈래 중 하나만 유효하다

**언제 쓰나** — 실패 이유를 값(보통 메시지)으로 돌려주고 싶을 때 쓴다.
메서드 시그니처에 「실패할 수 있다」가 드러나서 호출하는 쪽이 실패를 잊기 어렵다.

```text
parseAge("25")   ── parseInt 성공, 범위 안 ──▶ Either.right(25)            → Right(25)
parseAge("abc")  ── NumberFormatException  ──▶ Either.left("숫자가 아님: abc") → Left(숫자가 아님: abc)
parseAge("-5")   ── 0 미만                  ──▶ Either.left("나이 범위 초과: -5") → Left(나이 범위 초과: -5)
```

- 객체 하나는 `left` · `right` 두 칸과 `isRight` 표시 하나를 가진다.
- `right(v)` 는 오른쪽 칸에 값을 넣고 `isRight = true` 로 만든다.
- `left(v)` 는 왼쪽 칸에 값을 넣고 `isRight = false` 로 만든다.
- 생성자는 `private` 이다 — 밖에서는 `left` · `right` 정적 팩토리로만 만든다.
- 「Right 가 성공, Left 가 실패」는 관례다(「right = 올바른」).

> **합집합 타입(sum type)** — 여러 갈래 중 정확히 하나의 꼴만 갖는 타입.\
> 예: `Either` 는 `Left` 아니면 `Right` 다.

> **정적 팩토리** — 생성자 대신 객체를 만들어 돌려주는 `static` 메서드.\
> 예: `Either.right(25)`.

### (2) `map` 과 `flatMap` — 실패를 자동으로 넘긴다

**언제 쓰나** — 성공 값에 다음 계산을 이어 붙일 때 쓴다.
다음 계산이 평범한 값을 돌려주면 `map`, 다시 `Either` 를 돌려주면 `flatMap` 이다.

```text
Right(25).flatMap(age -> classifyAge(age))
   isRight? ── 예 ──▶ fn.apply(25) = Right("성인")  ──▶ Right(성인)

Left("숫자가 아님: abc").flatMap(age -> classifyAge(age))
   isRight? ── 아니오 ──▶ fn 을 부르지 않음 ──▶ Either.left(같은 에러) ──▶ Left(숫자가 아님: abc)
```

- `isRight` 이면 함수를 오른쪽 값에 적용한다.
- 아니면 함수를 아예 부르지 않고 왼쪽 값을 담은 새 `Either` 를 돌려준다.
- 이렇게 실패에서 뒤 계산을 건너뛰는 것을 단락 평가라 한다.
- `map(fn)` 은 `fn` 의 결과를 `Either.right(...)` 로 한 번 감싼다.
- `flatMap(fn)` 은 `fn` 이 이미 `Either` 를 돌려주므로 감싸지 않고 그대로 돌려준다.
- 그래서 `Either` 를 돌려주는 함수에 `map` 을 쓰면 `Either<String, Either<String, String>>` 처럼 상자 안에 상자가 생긴다.
- `flatMap` 은 이 중첩을 펴 준다(평탄화).
- 원본은 이것을 「모나드의 핵심」이라 부른다.
- `Either.map` 은 `fn` 이 던진 예외를 잡지 않는다 — 예외는 그대로 바깥으로 튀어 나간다.

> **단락 평가** — 앞에서 결론이 나면 뒤 계산을 하지 않는 것.\
> 예: `Left` 에 `flatMap` 을 아무리 이어도 함수는 한 번도 불리지 않는다.

> **모나드** — 값을 감싼 상자와, 상자를 이어 붙이는 `flatMap` 을 갖춘 꼴.\
> 예: `Either` · `Try` 는 `flatMap` 으로 단계를 잇는다.

### (3) `Try<T>` — 예외를 값으로 흡수한다

**언제 쓰나** — 예외를 던지는 코드(`Integer.parseInt` 등)를 `try/catch` 없이 이어 쓰고 싶을 때 쓴다.

```text
Try.of(() -> Integer.parseInt("42"))   ── 성공 ──▶ Success(42)
   .map(n -> n * 2)                    ── Try.of 로 다시 감싸 실행 ──▶ Success(84)
   .map(n -> n + 10)                   ──────────────────────────▶ Success(94)

Try.of(() -> Integer.parseInt("not_a_number"))  ── 예외를 catch ──▶ Failure(예외)
   .map(n -> n * 2)                             ── 함수 안 부름  ──▶ Failure(같은 예외)
```

- `Try.of(supplier)` 는 `supplier.get()` 을 `try` 안에서 부른다.
- 값이 나오면 `Try(value, null)`, `Exception` 이 나면 `Try(null, e)` 를 만든다.
- 성공 판정은 오직 `error == null` 이다.
- `map` 은 성공일 때 `Try.of(() -> fn.apply(value))` 로 다시 감싼다.
- 그래서 `fn` 안에서 난 예외도 `Failure` 로 바뀐다 — `Either.map` 과 다른 점이다.
- `flatMap` 은 `fn.apply(value)` 를 직접 `try/catch` 로 감싸 같은 일을 한다.
- `getOrElse(기본값)` 은 실패면 기본값을, `getOrElseGet(fn)` 은 실패면 예외를 넣어 계산한 값을 돌려준다.
- `toString` 은 실패일 때 `error.getMessage()` 를 찍는다.
- `double` 은 0 으로 나눠도 예외가 나지 않고 `Infinity` 가 된다.
- 예외가 없으니 `Try` 는 이것을 **성공**으로 본다 — 수학적으로 이상한 값도 `Try` 는 걸러 주지 않는다.

> **`Supplier<T>`** — 인자 없이 값 하나를 돌려주는 함수형 인터페이스(`get()`).\
> 예: `() -> Integer.parseInt("42")`.

### (4) `Validation<T>` — 에러를 끝까지 모은다

**언제 쓰나** — 회원가입 폼처럼 칸이 여럿이고, 틀린 곳을 **한 번에 전부** 알려 줘야 할 때 쓴다.

```text
validateName("")          ──▶ Invalid([이름은 필수입니다])
validateEmail("invalid")  ──▶ Invalid([이메일 형식이 잘못되었습니다])
validatePassword("short") ──▶ Invalid([8자 이상…, 대문자…, 숫자…])
                 │
                 ▼  Validation.combine("signup", nameV, emailV, passV)
       에러 목록을 차례대로 이어 붙임 → 5개
                 ▼
       Invalid([이름…, 이메일…, 8자…, 대문자…, 숫자…])
```

- `Validation` 은 값 하나와 에러 목록(`List<String>`) 하나를 가진다.
- `valid(v)` 는 빈 목록(`List.of()`), `invalid(...)` 는 에러 하나 또는 목록을 담는다.
- 유효 판정은 오직 `errors.isEmpty()` 다.
- `combine(value, v1, v2, …)` 는 넘겨받은 검증을 **모두** 돌며 에러를 넘겨받은 차례대로 한 목록에 붙인다.
- 목록이 비면 `valid(value)`, 아니면 `invalid(모든 에러)` 를 돌려준다.
- 성공일 때 담기는 값은 각 검증의 값이 아니라 `combine` 의 첫 인자(`"signup"`)다.
- `validatePassword` 는 한 칸 안에서도 규칙 셋(8자 이상 · 대문자 · 숫자)을 모두 검사해 에러를 쌓는다.
- `Either` 의 `flatMap` 은 첫 실패에서 멈추지만, `Validation.combine` 은 멈추지 않는다.

### (5) 셋을 견주면

| | `Either<L, R>` | `Try<T>` | `Validation<T>` |
|---|---|---|---|
| 실패에 담기는 것 | 아무 타입 `L`(보통 메시지) | `Exception` | `List<String>` |
| 실패 뒤 계산 | 멈추고 전파 | 멈추고 전파 | 다 돌고 모음 |
| 함수 안 예외 | `map` 은 잡지 않음 | `map` · `flatMap` 이 잡음 | 해당 없음 |
| 쓰임 | 이유가 있는 실패 | 예외를 던지는 코드 감싸기 | 폼 검증 |

- `Try<T>` 는 실패 쪽이 `Exception` 으로 정해진 `Either<Exception, T>` 와 같은 꼴이다.
- 세 클래스 모두 필드가 `final` 이다 — 만든 뒤 바뀌지 않고, `map` 은 새 객체를 돌려준다.
- `parseAge` · `classifyAge` · `validate…` 는 바깥 상태를 바꾸지 않고 입력만으로 결과를 정한다.

> **불변성** — 객체를 만든 뒤 상태가 바뀌지 않는 성질.\
> 예: `map` 은 원래 `Either` 를 고치지 않고 새 `Either` 를 만든다.

> **순수 함수** — 같은 입력에 늘 같은 결과를 내고 바깥 상태를 바꾸지 않는 함수.\
> 예: `classifyAge(25)` 는 언제 불러도 `Right("성인")` 이다.

## 문법 — 형태와 규칙

```java
static Either<String, Integer> half(int n) {
    if (n % 2 != 0) return Either.left("홀수: " + n);
    return Either.right(n / 2);
}

Either<String, Integer> a = half(8).flatMap(x -> half(x));   // 8 → 4 → 2
Either<String, Integer> b = half(6).flatMap(x -> half(x));   // 6 → 3 → 홀수에서 멈춤
Try<Integer> t = Try.of(() -> Integer.parseInt("7")).map(x -> x + 1);
Validation<String> v = Validation.combine("form",
    Validation.valid("a"), Validation.invalid("b 틀림"));
```

- 실패를 돌려주는 메서드는 반환 타입을 `Either<에러타입, 성공타입>` 으로 쓴다.
- 다음 단계가 평범한 값을 돌려주면 `map`, 같은 상자 타입을 돌려주면 `flatMap` 으로 잇는다.
- 예외를 던지는 식은 `Try.of(() -> 식)` 처럼 람다로 감싸야 한다 — 감싸지 않으면 `of` 에 들어가기 전에 이미 예외가 난다.
- 값을 꺼낼 때는 `getOrElse` · `getOrElseGet` 로 실패의 대체값을 정한다.
- 여러 검증을 모을 때는 `Validation.combine(결과값, 검증들...)` 를 쓴다(가변 인자 `Validation<?>...`).
- 생성자는 `private`, 만들기는 정적 팩토리(`left` · `right` · `of` · `success` · `failure` · `valid` · `invalid`)로만 한다.

## 어디서 틀리나

### 1. `Either` 를 돌려주는 함수에 `map` 을 쓴다
`parseAge("25").map(age -> classifyAge(age))` 의 타입은 `Either<String, Either<String, String>>` 이다.
상자가 겹친다.
`flatMap` 을 써야 한 겹으로 펴진다.

### 2. `Either.map` 이 예외도 잡아 줄 거라 믿는다
`Either.map` 은 `fn.apply(right)` 를 그냥 부른다.
`fn` 이 예외를 던지면 `Left` 가 되지 않고 예외가 그대로 터진다.
예외를 값으로 바꾸는 것은 `Try` 의 `map` · `flatMap` 뿐이다.

### 3. `double` 의 0 나눗셈을 실패로 기대한다
`10.0 / 0` 은 예외가 아니라 `Infinity` 다.
`Try` 는 예외만 실패로 보므로 결과는 `Success` 다.
원본 주석도 「double은 0으로 나눠도 ArithmeticException이 아닌 Infinity → 성공으로 처리됨」이라 경고한다.

### 4. 「Try 는 checked exception 을 우아하게 처리한다」는 팁을 이 구현에 그대로 기대한다
원본의 주장 → 팁은 `Try` 가 검사 예외 처리에 유용하다고 한다.
왜 의심스러운가 → 이 구현의 `Try.of` 는 `Supplier<T>` 를 받는데, `Supplier.get()` 은 검사 예외를 선언하지 않는다.
그래서 검사 예외를 던지는 메서드를 부르는 람다는 `Try.of` 에 넘기는 순간 컴파일 오류가 난다.
`catch (Exception e)` 가 검사 예외까지 잡을 수 있게 쓰여 있어도, 거기까지 가지 못한다.
검사 예외를 받으려면 `get()` 이 `throws Exception` 을 선언한 자체 함수형 인터페이스가 필요하다(원본에 근거 없음 — 추론).

### 5. 성공 · 실패 판정이 한 칸에만 기댄다
`Try` 는 `error == null` 만 본다 — `Try.failure(null)` 은 성공으로 판정된다.
`Validation` 은 `errors.isEmpty()` 만 본다 — `Validation.invalid(빈 목록)` 은 `Valid` 로 판정되고 값은 `null` 이다.
`Try` 의 실패 `toString` 은 `getMessage()` 를 찍으므로, 메시지 없는 예외면 `Failure(null)` 이 된다.

### 6. `combine` 이 각 검증의 값을 모아 줄 거라 기대한다
`combine` 은 에러만 모은다.
성공일 때 담기는 값은 첫 인자로 넘긴 값(`"signup"`)이다 — 이름 · 이메일 값은 버려진다.

### 7. `classifyAge` 의 주석을 그대로 믿는다
원본의 주장 → 「모두 성공으로 분류 — 실패 가능성 없음을 시그니처로 표현 어려움 (Either의 한계)」.
왜 의심스러운가 → 실패가 없다면 반환 타입을 `String` 으로 두고 `map` 으로 이으면 「실패 없음」이 시그니처에 드러난다.
`Either` 를 돌려주게 한 것은 `flatMap` 예시를 보이려는 선택이지 `Either` 의 한계라 보기 어렵다(원본에 근거 없음 — 추론).

### 8. 쓰지 않는 import
원본은 `java.util.stream.Collectors` 를 들여오지만 쓰지 않는다.
컴파일은 되며, 동작에는 영향이 없다.

### 9. 이 타입들을 꼭 직접 만들어야 한다고 생각한다
원본 팁대로 Vavr 라이브러리를 쓰면 이런 타입을 바로 쓸 수 있다.
이 문서의 세 클래스는 원리를 보이려고 직접 만든 것이다.

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| `double` 을 0 으로 나누면 예외 없이 `Infinity` | 언어 보장 — Java 의 부동소수점 규칙(IEEE 754 를 따른다) |
| `Double` 의 `Infinity` 가 문자열로 `Infinity` 로 찍힌다 | 표준 라이브러리 API 명세(`Double.toString`) |
| `Integer.parseInt("not_a_number")` 의 예외 메시지가 `For input string: "not_a_number"` 꼴이다 | JDK 구현 — 메시지 문구는 명세가 정하지 않는다(확인 필요) |
| `Right` 가 성공, `Left` 가 실패 | 관례 — 언어나 라이브러리가 강제하지 않는다 |
| 실패면 `map` · `flatMap` 이 함수를 부르지 않는다 | 이 예제 클래스의 구현 |
| `Try.map` 이 함수 안 예외를 `Failure` 로 바꾼다 | 이 예제 클래스의 구현(`Either.map` 은 그렇지 않다) |
| `List.of()` 로 만든 목록은 바꿀 수 없다 | 표준 라이브러리 API 명세 |
| `Supplier.get()` 은 검사 예외를 던질 수 없다 | 언어 보장 — 인터페이스가 `throws` 를 선언하지 않아 컴파일러가 막는다 |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 입력을 해석하고 실패 이유를 돌려줘야 한다 | `Either<String, T>` | 예외를 던지고 호출자가 잡기를 바라기 |
| 예외를 던지는 코드를 여러 단계 잇는다 | `Try.of(...).map(...)` | 단계마다 `try/catch` 를 흩뿌리기 |
| 폼 칸 여럿을 한 번에 검증한다 | `Validation.combine` | `Either.flatMap` (첫 실패에서 멈춘다) |
| 다음 단계가 실패하지 않는다 | `map` | 억지로 `Either` 를 돌려주게 하고 `flatMap` |
| 0 나눗셈 같은 값 이상을 잡아야 한다 | 값을 직접 검사해 `Left` · `invalid` 로 | `Try` 에만 맡기기(예외가 안 나면 성공이다) |

## 핵심 문장

1. **실패를 던지지 말고 돌려준다** — `Either` · `Try` · `Validation` 은 성공과 실패를 담는 값이다.
2. **실패면 뒤 단계를 건너뛴다** — `map` · `flatMap` 은 성공일 때만 함수를 부르고 실패는 그대로 전파한다.
3. **상자를 돌려주는 함수는 `flatMap`** — `map` 을 쓰면 상자가 겹친다.
4. **`Try` 는 예외만 실패로 본다** — 예외가 안 나는 이상한 값(`Infinity`)은 성공이다.
5. **`Validation` 은 멈추지 않고 모은다** — 그래서 모든 에러를 한 번에 보여 주는 폼 검증에 맞다.

## 관련 자료

- `monad-pattern` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- `pipeline-pattern` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- `validation-patterns` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- 원본: study-site 항목 데이터 `data/java/advanced-patterns.json` 의 `functional-java`

## 용어 풀이

- **함수형 프로그래밍** — 값을 바꾸는 대신 함수를 이어 새 값을 만드는 방식.
- **`Either<L, R>`** — `Left`(실패) 아니면 `Right`(성공) 중 하나를 담는 타입.
- **`Try<T>`** — 계산 결과 또는 그때 난 예외를 담는 타입.
- **`Validation<T>`** — 값 또는 에러 목록을 담고, 여럿을 합치면 에러를 누적하는 타입.
- **`map`** — 성공 값에 함수를 적용하고 결과를 같은 상자에 다시 담는 연산.
- **`flatMap`** — 상자를 돌려주는 함수를 적용하되 상자를 겹치지 않게 펴는 연산.
- **모나드** — 값을 감싼 상자와 그것을 이어 붙이는 `flatMap` 을 갖춘 꼴.
- **단락 평가** — 앞에서 결론이 나면 뒤 계산을 하지 않는 것.
- **합집합 타입(sum type)** — 여러 갈래 중 하나의 꼴만 갖는 타입.
- **정적 팩토리** — 생성자 대신 객체를 만들어 돌려주는 `static` 메서드.
- **순수 함수** — 같은 입력에 같은 결과를 내고 바깥 상태를 바꾸지 않는 함수.
- **불변성** — 만든 뒤 상태가 바뀌지 않는 성질.
- **검사 예외(checked exception)** — 던지려면 `throws` 로 선언해야 하고 컴파일러가 처리를 강제하는 예외.
- **함수형 인터페이스** — 추상 메서드가 하나뿐이라 람다로 채울 수 있는 인터페이스(`Function` · `Supplier`).
- **`Infinity`** — 부동소수점에서 0 으로 나눌 때 등에 나오는 무한대 값.
- **Vavr** — `Either` · `Try` · `Validation` 같은 타입을 제공하는 Java 라이브러리.

## 더 들어가면

- 표준 라이브러리의 `Optional<T>` 도 `map` · `flatMap` 을 가진 상자다 — 다만 실패 이유를 담지 못한다(확인 필요).
- `Stream` 의 `flatMap` 도 같은 「펴기」 생각에서 나왔다(확인 필요).
- 모나드는 `flatMap` 이 지켜야 할 법칙(항등 · 결합)으로 정의된다 — 이 예제는 그 법칙을 검증하지 않는다(확인 필요).
- `Validation` 처럼 독립된 검증을 모으는 꼴은 흔히 「applicative」 라 부르며 모나드와 구별한다(확인 필요).
- 최신 Java 의 `sealed` 인터페이스와 `record` 를 쓰면 `Left` · `Right` 를 별도 타입으로 나눠 `switch` 패턴 매칭으로 다룰 수 있다(확인 필요).
- Vavr 의 `Validation` 은 결합 결과로 각 검증의 값을 묶어 객체를 만드는 쪽을 지원한다(확인 필요).
