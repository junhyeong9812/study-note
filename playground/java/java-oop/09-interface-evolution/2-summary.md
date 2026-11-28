# java/java-oop/09 — 인터페이스 진화 (Java 8~17+) — 정리 (힌트)

> 출처 — study-site 항목 `java/interface-evolution`(항목 데이터 `data/java/oop.json`) · 정답 코드 study-practice `java/java-oop/reference/interface-evolution.java`\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).\
> 실행 — 실행하지 않음 — Java 예제는 이 문서를 만들 때 컴파일 · 실행하지 않았다(JDK 로 돌려 확인한다).

## 한눈에 — 쉽게 말하면

**인터페이스는 「가맹점 계약서」다.**
처음 계약서에는 「가맹점이 반드시 할 일(의무 조항)」만 적혀 있었다.
나중에 본사가 조항을 하나 더 넣고 싶어졌다.
의무 조항으로 넣으면 이미 계약한 가맹점이 모두 계약 위반이 된다.
그래서 「따로 정하지 않으면 본사 방식대로 한다」는 **기본 조항**을 붙인다.
기본 조항끼리 겹치는 절차는 **본사 내부 메모**로 빼 둔다. 가맹점은 이 메모를 볼 수 없다.
마지막으로 본사는 **가맹점 명단을 닫을** 수 있다. 명단에 없는 가게는 이 계약서로 계약할 수 없다.
Java 인터페이스도 똑같은 구조다.

| 비유 | 실체 |
|---|---|
| 계약서 | `interface` |
| 의무 조항 | 추상 메서드 (`void log(String message);`) |
| 기본 조항 | `default` 메서드 (Java 8) |
| 본사 대표 창구 | `static` 메서드 (Java 8) |
| 본사 내부 메모 | `private` · `private static` 메서드 (Java 9) |
| 닫힌 가맹점 명단 | `sealed interface … permits …` (Java 17) |
| 두 계약서의 기본 조항이 겹칠 때 | `default` 충돌 → 구현 클래스가 직접 오버라이드 |

```text
            interface
  ┌─────────────────────────────────┐
  │ 추상 메서드       ← 구현체가 채움 │  (원래부터)
  │ default 메서드    ← 기본 구현     │  Java 8
  │ static 메서드     ← 이름으로 호출 │  Java 8
  │ private 메서드    ← 안에서만      │  Java 9
  └─────────────────────────────────┘
  sealed ... permits A, B, C          ← 구현체 명단 닫기 (Java 17)
```

## 이 주제가 답하려는 질문

1. 이미 구현체가 많은 인터페이스에 메서드를 더하면서 그 구현체들을 깨지 않으려면 어떻게 하나?
2. 인터페이스 안의 기본 구현끼리 겹치는 코드를 바깥에 드러내지 않고 나누려면 어떻게 하나?
3. 「이 인터페이스의 구현체는 딱 이것들뿐이다」를 컴파일러가 알게 하면 무엇이 좋아지나?
4. 두 인터페이스가 같은 기본 구현을 줄 때 어느 쪽을 쓰나?

## 동작 방식

### (1) `default` 메서드 — 구현체를 깨지 않고 인터페이스를 넓힌다

**언제 쓰나** — 이미 여러 클래스가 구현한 인터페이스에 메서드를 더해야 할 때 쓴다.
추상 메서드로 더하면 모든 구현체가 새 메서드를 구현해야 하므로 컴파일이 깨진다.

```text
interface Logger {
    void log(String message);              ← 추상: 구현체가 채운다
    default void info(String msg) {        ← 기본 구현이 들어 있다
        log("[INFO] " + msg);
    }
}

logger.info("시작")
   │
   ▼  info 는 default 이므로 인터페이스의 본문이 돈다
log("[INFO] 시작")
   │
   ▼  log 는 추상 메서드이므로 구현체의 log 가 돈다
구현체가 "[INFO] 시작" 을 받아 처리한다
```

- `info` 를 따로 구현하지 않은 클래스도 `info` 를 가진다.
- `info` 의 본문은 추상 메서드 `log` 를 부른다.
- 실제로 무엇을 하는지는 구현체의 `log` 가 정한다.
- 원본의 `Logger` 는 `info` · `error` · `debug` 셋을 모두 이 꼴로 둔다. 머리말(`[INFO]` · `[ERROR]` · `[DEBUG]`)만 다르다.

> **default 메서드** — 인터페이스 안에 본문을 가진 메서드. 구현체가 오버라이드하지 않으면 이 본문이 쓰인다.\
> 예: `default void info(String msg) { log("[INFO] " + msg); }`

> **하위 호환성** — 새 판이 나와도 옛 판에 맞춰 만든 코드가 그대로 동작하는 성질.\
> 예: `Logger` 에 `debug` 를 더해도 `log` 만 구현한 옛 클래스가 깨지지 않는다.

### (2) `static` 메서드 — 인터페이스 이름으로 부르는 도구

**언제 쓰나** — 그 인터페이스와 짝을 이루는 도구 메서드, 특히 구현체를 만들어 주는 팩토리를 인터페이스 안에 두고 싶을 때 쓴다.

```text
interface Logger {
    static Logger consoleLogger() {
        return msg -> System.out.println("  CONSOLE: " + msg);
    }
}

Logger logger = Logger.consoleLogger();
   │
   ▼  인터페이스 이름으로 부른다
람다 하나가 Logger 구현체가 되어 돌아온다 (log 를 람다 본문으로 채움)
   │
   ▼
logger.info("x") → log("[INFO] x") → "  CONSOLE: [INFO] x" 를 찍는다
```

- `consoleLogger` 는 `Logger.consoleLogger()` 처럼 인터페이스 이름으로 부른다.
- 인터페이스의 `static` 메서드는 구현 클래스에 물려지지 않는다. 그래서 `logger.consoleLogger()` 처럼 구현체 쪽으로는 부를 수 없다.
- 반환하는 람다가 `Logger` 가 될 수 있는 까닭은 `Logger` 에 추상 메서드가 `log` 하나뿐이기 때문이다. `default` · `static` 메서드는 이 셈에 들지 않는다.

> **팩토리 메서드** — 객체를 만들어 돌려주는 일을 맡은 메서드.\
> 예: `Logger.consoleLogger()` 가 콘솔에 찍는 `Logger` 를 만든다.

> **함수형 인터페이스** — 추상 메서드가 딱 하나인 인터페이스. 람다로 구현체를 만들 수 있다.\
> 예: `Logger`(추상 메서드 `log` 하나), `Validator`(추상 메서드 `validate` 하나).

### (3) `private` · `private static` 메서드 — `default` 끼리 나눠 쓰는 숨은 도우미

**언제 쓰나** — 여러 `default` 메서드가 같은 검사나 계산을 되풀이할 때 쓴다.
그 공통 부분을 `default` 로 빼면 구현체와 호출자에게 공개된다. 공개하지 않고 나누려고 `private` 을 쓴다.

```text
interface Validator {
    default boolean validateNotEmpty(String s) { return checkNotNull(s) && !s.isBlank(); }
    default boolean validateLength(String s, int min, int max) {
        return checkNotNull(s) && s.length() >= min && s.length() <= max;
    }
    private boolean checkNotNull(String s) { return s != null; }
}

validateNotEmpty("hello") ──┐
                            ├──► checkNotNull (인터페이스 안에서만 보임)
validateLength("hello",3,10)┘

바깥: validator.checkNotNull(..)  → 컴파일 오류 (보이지 않는다)
```

- 두 `default` 메서드가 같은 `null` 검사를 `checkNotNull` 하나로 나눠 쓴다.
- `checkNotNull` 은 `private` 이라 인터페이스 바깥(구현 클래스 · 호출자)에서 부를 수 없다.
- `private static` 메서드(원본의 `sanitize`)는 객체 없이 쓰는 도우미다. 원본에서는 선언만 있고 어디서도 부르지 않는다.
- `private` 메서드는 본문이 반드시 있어야 하며 추상 메서드 셈에 들지 않는다. 그래서 `Validator` 는 여전히 람다로 만들 수 있다.

원본 `main` 은 `Validator` 를 람다로 만든다.

```java
// 원본 main 에서 발췌
Validator validator = input -> input != null && input.matches("[a-zA-Z]+");
```

- 이 람다는 `validate` 의 본문이 된다.
- 그런데 `main` 은 `validateNotEmpty` 와 `validateLength` 만 부르고 `validate` 는 한 번도 부르지 않는다.
- 두 `default` 메서드는 `validate` 를 쓰지 않으므로, 「알파벳만 통과」 규칙은 이 예제의 결과에 끼어들지 않는다.

> **private 인터페이스 메서드** — 인터페이스 안에서만 부를 수 있는, 본문을 가진 메서드 (Java 9).\
> 예: `private boolean checkNotNull(String input) { return input != null; }`

### (4) `sealed interface` — 구현체 명단을 닫는다

**언제 쓰나** — 「도형은 원 · 사각형 · 삼각형뿐이다」처럼 구현체의 종류가 정해져 있고, 아무나 새 구현체를 더하지 못하게 막고 싶을 때 쓴다.

```text
sealed interface Shape permits Circle, Rectangle, Triangle { ... }

  Shape
   ├── record Circle             (record → 암묵적 final: 더 상속 불가)
   ├── record Rectangle          (record → 암묵적 final)
   └── non-sealed class Triangle (봉인 해제: 누구나 Triangle 을 상속 가능)
            └── (예: class RightTriangle extends Triangle — 허용)

class Square implements Shape  → 컴파일 오류 (permits 명단에 없음)
```

- `permits` 뒤에 적은 타입만 `Shape` 를 구현할 수 있다.
- 명단에 오른 구현체는 자신이 더 상속될 수 있는지를 밝혀야 한다 — `final`(닫힘) · `sealed`(다시 명단을 둠) · `non-sealed`(활짝 엶) 가운데 하나다.
- `record` 는 암묵적으로 `final` 이라 따로 밝히지 않아도 sealed 의 자식으로 알맞다.
- `Triangle` 은 `non-sealed` 라서 그 밑으로는 다시 아무나 상속할 수 있다. 그래도 그 자손은 모두 「`Triangle` 의 한 종류」다.

> **sealed** — 자신을 상속 · 구현할 수 있는 타입을 `permits` 명단으로 제한하는 표시 (Java 17 정식).\
> 예: `sealed interface Shape permits Circle, Rectangle, Triangle`

> **non-sealed** — sealed 명단에 오른 타입이 「내 아래로는 제한을 풀겠다」고 밝히는 표시.\
> 예: `static non-sealed class Triangle implements Shape`

> **record** — 값을 담는 불변 클래스를 짧게 선언하는 문법. 암묵적으로 `final` 이다.\
> 예: `record Circle(double radius) implements Shape { ... }`

### (5) sealed + `switch` 패턴 매칭 — `default` 없이 빠짐없는 분기

**언제 쓰나** — 닫힌 구현체마다 다른 일을 하고, 하나라도 빠뜨리면 컴파일러가 알려 주기를 바랄 때 쓴다. 원본은 이 조합을 Java 21+ 로 표시한다.

```text
String info = switch (s) {
    case Circle c    -> "원의 반지름: " + c.radius();
    case Rectangle r -> "사각형: " + r.width() + "x" + r.height();
    case Triangle t  -> "삼각형 밑변: " + t.base;
};                                   ← default 가 없다

컴파일러: Shape 의 명단 = {Circle, Rectangle, Triangle}
          case 가 셋 다 덮는다 → exhaustive → 통과

명단에 Square 를 더하면 → 이 switch 가 Square 를 덮지 못함 → 컴파일 오류
```

- `case Circle c` 는 「`s` 가 `Circle` 이면 그것을 `c` 라는 이름으로 받는다」는 뜻이다.
- 컴파일러는 `permits` 명단을 알기 때문에 세 `case` 로 모든 경우가 덮였다고 판단한다.
- 그래서 `default` 가 없어도 `switch` 표현식이 성립한다.
- `default` 를 두지 않은 덕에, 나중에 명단에 새 구현체를 더하면 덮지 못한 `switch` 가 모두 컴파일 오류로 드러난다.
- `Triangle` 의 자손(`non-sealed` 로 열린 쪽)은 `case Triangle t` 에 걸린다.
- `Circle` · `Rectangle` 은 record 라서 `c.radius()` · `r.width()` 같은 접근자가 저절로 생긴다. `Triangle` 은 보통 클래스라 필드 `t.base` 를 직접 읽는다.

> **패턴 매칭(switch)** — `case 타입 이름` 꼴로 값의 타입을 검사하고 동시에 그 타입의 변수로 꺼내는 문법.\
> 예: `case Circle c -> c.radius()`

> **exhaustive** — 분기가 가능한 모든 경우를 빠짐없이 덮은 상태.\
> 예: `Shape` 의 명단 셋을 모두 `case` 로 덮은 `switch`.

### (6) `default` 충돌 — 직접 오버라이드하고 `X.super.m()` 으로 고른다

**언제 쓰나** — 한 클래스가 두 인터페이스를 구현했는데, 둘 다 같은 시그니처의 `default` 메서드를 줄 때다.

```text
interface A { default String hello() { return "A의 hello"; } }
interface B { default String hello() { return "B의 hello"; } }

class AB implements A, B { }              → 컴파일 오류: 어느 hello 인지 모른다

class AB implements A, B {
    public String hello() {
        return A.super.hello() + " + " + B.super.hello();
    }                                     → 통과: 직접 정했다
}

new AB().hello()
   ├── A.super.hello() → "A의 hello"
   ├── B.super.hello() → "B의 hello"
   └── 이어 붙여 "A의 hello + B의 hello"
```

- 두 기본 구현이 겹치면 컴파일러는 어느 하나를 고르지 않는다.
- 그래서 구현 클래스가 `hello` 를 반드시 오버라이드해야 한다.
- 오버라이드 안에서 `인터페이스이름.super.메서드()` 로 특정 부모 인터페이스의 `default` 를 부를 수 있다.
- 하나만 골라도 되고, 원본처럼 둘을 합쳐도 된다.

> **시그니처** — 메서드 이름과 매개변수 타입의 묶음.\
> 예: `A.hello()` 와 `B.hello()` 는 이름 · 매개변수가 같아 시그니처가 같다.

## 문법 — 형태와 규칙

```java
interface Greeter {
    String name();                                  // 추상 메서드

    default String greet() {                        // Java 8
        return wrap("안녕, " + name());
    }

    static Greeter of(String n) {                   // Java 8
        return () -> n;
    }

    private String wrap(String s) {                 // Java 9
        return "[" + s + "]";
    }
}

sealed interface Animal permits Dog, Cat { }        // Java 17
record Dog() implements Animal { }                  // 암묵적 final
final class Cat implements Animal { }
```

- `default` 메서드: `default` 키워드 + 본문. 구현체가 오버라이드할 수 있다.
- `static` 메서드: 본문 필수. `인터페이스이름.메서드()` 로만 부른다.
- `private` 메서드: 본문 필수. 인터페이스 안의 `default` · `private` 메서드에서 부른다.
- `private static` 메서드: 본문 필수. 객체 없이 쓰는 내부 도우미다. 인터페이스의 `static` 메서드에서도 부를 수 있다.
- 추상 메서드가 하나뿐이면 함수형 인터페이스다. `default` · `static` · `private` 메서드가 몇 개든 이 성질은 바뀌지 않는다.
- `sealed interface 이름 permits 타입, 타입, …` — 명단 밖의 구현은 컴파일 오류다.
- 명단의 타입은 `final`(또는 `record`) · `sealed` · `non-sealed` 가운데 하나여야 한다.
- 충돌 해결: `인터페이스이름.super.메서드(…)`.

버전 흐름(원본의 타임라인을 옮기되, 의심스러운 줄은 「어디서 틀리나 6」에서 다룬다):

| 판 | 인터페이스에 생긴 것 |
|---|---|
| Java 8 | `default` · `static` 메서드 |
| Java 9 | `private` · `private static` 메서드 |
| (프리뷰 단계) | `sealed` — 원본은 Java 14 로 적었다 |
| Java 17 | `sealed interface` 정식 도입 |
| Java 21+ | (원본 주석) sealed 와 `switch` 패턴 매칭의 조합 |

## 어디서 틀리나

### 1. `default` 메서드는 「하위 호환」을 위한 것이다 — 아무 메서드나 넣는 곳이 아니다

원본 팁: default 메서드는 기존 인터페이스에 메서드를 추가할 때 하위 호환성을 유지한다.
기존 구현체가 새 메서드를 구현하지 않아도 기본 본문이 쓰이므로 깨지지 않는다.
하지만 인터페이스는 상태(인스턴스 필드)를 가질 수 없다.
그래서 `default` 본문은 추상 메서드 같은 다른 메서드를 불러 일을 이루는 꼴이 된다 (`info` → `log`).

### 2. 같은 `default` 를 두 인터페이스에서 받으면 컴파일이 깨진다

`AB` 에서 `hello` 오버라이드를 지우면 컴파일 오류가 난다.
컴파일러는 A 쪽과 B 쪽 가운데 하나를 마음대로 고르지 않는다.
해결은 직접 오버라이드하고 필요하면 `A.super.hello()` 처럼 고르는 것이다.

### 3. `private` 메서드는 구현 클래스에서도 보이지 않는다

원본 팁: private 메서드는 default 메서드 간 코드 중복을 제거한다.
「인터페이스를 구현했으니 private 도 쓸 수 있겠지」는 틀린 생각이다.
`checkNotNull` 은 `Validator` 안의 메서드만 부를 수 있다.
공개하고 싶으면 `default` 로 둬야 하고, 그러면 계약의 일부가 된다.

### 4. 인터페이스의 `static` 메서드는 물려지지 않는다

`Logger.consoleLogger()` 는 되지만 `logger.consoleLogger()` 는 안 된다.
클래스의 `static` 메서드처럼 생각하면 헷갈린다.

### 5. sealed 의 「default 없는 exhaustive」는 sealed 일 때만 된다

원본 팁: sealed interface 는 허용된 구현체만 가능하므로 패턴 매칭에서 default 없이 exhaustive 검사가 된다.
`Shape` 에서 `sealed` 를 빼면 명단이 열려 있으므로, 같은 `switch` 는 모든 경우를 덮었다고 볼 수 없다.
또 세 `case` 가운데 하나라도 빠뜨리면 exhaustive 가 아니어서 컴파일 오류다.
거꾸로 `default` 를 습관처럼 붙이면, 새 구현체가 생겨도 컴파일러가 알려 주지 않는다.

### 6. 원본 타임라인의 「Java 14: @Preview sealed interface」

원본의 주장 → `main` 마지막 부분은 「Java 14: @Preview sealed interface」를 찍는다.
왜 의심스러운가 → sealed 는 Java 15 에서 처음 프리뷰로 나왔다고 알려져 있다 (확인 필요).
또 `@Preview` 는 코드에 붙이는 애너테이션처럼 보이지만, 프리뷰 기능은 보통 컴파일 · 실행 옵션으로 켠다 (확인 필요).
타임라인을 외울 때는 「Java 17 정식」만 확실히 잡고 프리뷰 판은 따로 확인한다.

### 7. 예제의 `validate` 는 한 번도 불리지 않는다

`Validator` 람다의 「알파벳만 통과」 규칙은 `validate` 의 본문이다.
`main` 은 `validateNotEmpty` · `validateLength` 만 부르므로 이 규칙은 결과에 끼어들지 않는다.
`private static sanitize` 도 선언만 있고 쓰이지 않는다.
「선언했으니 어딘가 쓰였겠지」라고 읽으면 결과를 잘못 짐작한다.

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| `default` · `static` 메서드 (Java 8), `private` 메서드 (Java 9) | 언어 명세 |
| `sealed` · `permits` · `non-sealed` 의 규칙, `record` 가 암묵적 `final` | 언어 명세 (Java 17) |
| sealed 타입에 대한 `switch` 가 `default` 없이 exhaustive 로 인정됨 | 언어 명세 (원본은 Java 21+ 로 표시) |
| `default` 충돌 시 오버라이드 필수, `X.super.m()` | 언어 명세 |
| sealed 의 프리뷰가 Java 14 에서 시작 | 원본의 주장 — 의심스럽다 (확인 필요) |
| `printf("%.2f")` 가 소수점을 `.` 으로 찍음 | 기본 로캘에 따라 다를 수 있다 (확인 필요) |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 이미 구현체가 많은 인터페이스에 기능을 더한다 | `default` 메서드 | 추상 메서드 추가 (모든 구현체가 깨진다) |
| 인터페이스와 짝을 이루는 생성 도구 | `static` 팩토리 메서드 | 따로 만든 유틸 클래스 (꼭 필요할 때만) |
| `default` 끼리 겹치는 검사 | `private` 메서드 | 공개 `default` 로 빼기 (계약이 불필요하게 넓어진다) |
| 종류가 정해진 타입 묶음 (도형 · 결과 · 명령) | `sealed interface` + record | 아무나 구현할 수 있는 열린 인터페이스 |
| 닫힌 타입마다 다른 처리 | 패턴 매칭 `switch`, `default` 없이 | 습관적인 `default` 가지 |
| 두 인터페이스의 같은 `default` | 직접 오버라이드 + `X.super.m()` | 오버라이드 없이 두기 (컴파일 오류) |

## 핵심 문장

1. **`default` 메서드는 기존 구현체를 깨지 않고 인터페이스를 넓히는 장치다.**
2. **`private` 메서드는 `default` 끼리 나눠 쓰는 도우미를 바깥에 숨긴다.**
3. **`sealed` 는 구현체 명단을 닫아, 컴파일러가 「모든 경우」를 알게 한다.**
4. **그래서 sealed 타입의 `switch` 는 `default` 없이 빠짐없음을 검사받고, 새 구현체가 생기면 컴파일 오류로 알려 준다.**
5. **같은 `default` 가 둘 들어오면 구현 클래스가 직접 정한다 — `X.super.m()` 으로 고른다.**

## 관련 자료

- `interface-basics` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- `sealed-classes` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- `abstract-class` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- 원본: study-site 항목 데이터 `data/java/oop.json` 의 `interface-evolution`

## 용어 풀이

- **인터페이스** — 구현체가 지켜야 할 메서드 목록(계약)을 정한 타입.
- **추상 메서드** — 본문 없이 선언만 있는 메서드. 구현체가 채운다.
- **default 메서드** — 인터페이스 안의, 본문을 가진 공개 메서드 (Java 8).
- **static 인터페이스 메서드** — 인터페이스 이름으로 부르는 메서드. 구현체에 물려지지 않는다 (Java 8).
- **private 인터페이스 메서드** — 인터페이스 안에서만 부를 수 있는 메서드 (Java 9).
- **하위 호환성** — 새 판에서도 옛 코드가 그대로 동작하는 성질.
- **팩토리 메서드** — 객체를 만들어 돌려주는 메서드.
- **함수형 인터페이스** — 추상 메서드가 하나뿐인 인터페이스. 람다로 구현할 수 있다.
- **람다** — 이름 없는 함수를 짧게 쓰는 식. 함수형 인터페이스의 구현체가 된다.
- **sealed** — 상속 · 구현할 수 있는 타입을 명단으로 제한하는 표시.
- **permits** — sealed 타입의 허용 명단을 적는 자리.
- **non-sealed** — 명단에 오른 타입이 자기 아래의 제한을 푸는 표시.
- **record** — 불변 값 클래스를 짧게 쓰는 문법. 암묵적 `final`, 접근자 자동 생성.
- **패턴 매칭(switch)** — `case 타입 이름` 으로 타입 검사와 변수 꺼내기를 한 번에 하는 문법.
- **exhaustive** — 모든 경우를 빠짐없이 덮은 상태.
- **시그니처** — 메서드 이름과 매개변수 타입의 묶음.
- **프리뷰 기능** — 정식 도입 전에 시험 삼아 켜서 쓰는 언어 기능.

## 더 들어가면

- `default` 충돌에는 더 자세한 규칙이 있다고 알려져 있다 — 클래스(부모 클래스)의 메서드가 인터페이스의 `default` 보다 앞서고, 한 인터페이스가 다른 인터페이스를 상속해 더 구체적이면 그쪽이 이긴다 (확인 필요).
- sealed 타입과 그 구현체가 같은 소스 파일에 있으면 `permits` 절을 생략할 수 있다고 알려져 있다 (확인 필요).
- sealed 의 허용 구현체는 같은 모듈(모듈이 없으면 같은 패키지)에 있어야 한다는 제약이 있다고 알려져 있다 (확인 필요).
- Java 21 에는 record 의 구성 요소를 바로 풀어 받는 record 패턴(`case Circle(double r) -> …`)도 있다고 알려져 있다 (확인 필요).
- 표준 라이브러리에서 `default` 메서드로 넓힌 대표 예로 `Collection.stream()`, `Iterable.forEach()` 가 꼽힌다 (확인 필요).
