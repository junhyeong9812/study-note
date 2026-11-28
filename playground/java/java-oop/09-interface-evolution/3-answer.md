# java/java-oop/09 — 인터페이스 진화 (Java 8~17+) — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. `  CONSOLE: [INFO] 애플리케이션 시작` 과 `  CONSOLE: [ERROR] 오류 발생`

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
  CONSOLE: [INFO] 애플리케이션 시작
  CONSOLE: [ERROR] 오류 발생
```

**왜 그런가**
`info` 는 `default` 메서드라 인터페이스의 본문이 돌아 `log("[INFO] 애플리케이션 시작")` 을 부른다.
`log` 는 추상 메서드이고, 그 구현은 `consoleLogger` 가 돌려준 람다다.
람다는 받은 문자열 앞에 `  CONSOLE: `(앞 공백 둘)을 붙여 찍는다.
`error` 도 머리말만 `[ERROR] ` 로 다를 뿐 같은 길을 간다.
근거: 2-summary 「동작 방식 (1)」 · 「동작 방식 (2)」.

### 2. `true` · `false` · `true` — 람다의 규칙은 끼어들지 않는다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
true
false
true
```

**왜 그런가**
`validateNotEmpty("hello")` 는 `checkNotNull` 이 `true`, `isBlank()` 가 `false` 라서 `true` 다.
`validateNotEmpty("")` 는 빈 문자열이 공백뿐인 것으로 보아 `isBlank()` 가 `true` 이므로 `false` 다.
`validateLength("hello", 3, 10)` 은 길이 5 가 3 이상 10 이하이므로 `true` 다.
람다는 추상 메서드 `validate` 의 본문인데, 두 `default` 메서드는 `validate` 를 부르지 않는다.
그래서 「알파벳만 통과」 규칙은 세 결과에 아무 영향도 주지 않는다.
근거: 2-summary 「동작 방식 (3)」 · 「어디서 틀리나 7」.

### 3. `A의 hello + B의 hello`

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
A의 hello + B의 hello
```

**왜 그런가**
`A.super.hello()` 는 인터페이스 `A` 의 `default` 본문을 불러 `A의 hello` 를 돌려준다.
`B.super.hello()` 는 같은 식으로 `B의 hello` 를 돌려준다.
`AB` 의 `hello` 는 둘 사이에 ` + ` 를 끼워 잇는다.
근거: 2-summary 「동작 방식 (6)」.

### 4. 추상 메서드는 모든 구현체에게 새 의무를 지우고, `default` 는 본문을 함께 주기 때문이다

추상 메서드로 더하면 그 인터페이스를 구현한 모든 클래스가 새 메서드를 구현하지 않은 상태가 되어 컴파일이 깨진다.
`default` 메서드는 본문을 인터페이스 안에 가지고 있다.
구현체가 오버라이드하지 않으면 이 본문이 쓰이므로, 옛 구현체는 손대지 않아도 새 메서드를 가진다.
근거: 2-summary 「동작 방식 (1)」 · 「어디서 틀리나 1」.

### 5. 공통 도우미를 계약 바깥에 숨기기 위해서다

`default` 로 두면 그 검사도 구현체와 호출자에게 공개되어 인터페이스 계약의 일부가 된다.
`private` 으로 두면 두 `default` 메서드는 중복 없이 같은 검사를 나눠 쓰고, 바깥에서는 보이지 않는다.
원본 팁도 private 메서드가 default 메서드 간 코드 중복을 제거한다고 말한다.
근거: 2-summary 「동작 방식 (3)」 · 「어디서 틀리나 3」.

### 6. 컴파일 오류가 난다

`A` 와 `B` 가 시그니처가 같은 `default hello()` 를 하나씩 주므로, `AB` 는 어느 본문을 물려받을지 정할 수 없다.
컴파일러는 둘 가운데 하나를 마음대로 고르지 않는다.
그래서 `AB` 가 `hello` 를 직접 오버라이드해야 하며, 필요하면 `X.super.hello()` 로 부모를 고른다.
근거: 2-summary 「동작 방식 (6)」 · 「어디서 틀리나 2」.

### 7. 둘 다 컴파일 오류다

`Square` 는 `permits` 명단에 없으므로 `Shape` 를 구현할 수 없어 컴파일 오류가 난다.
`case Triangle t` 를 지우면 `switch` 가 `Shape` 의 명단 셋 가운데 하나를 덮지 못한다.
`default` 도 없으니 exhaustive 가 아니어서 역시 컴파일 오류다.
이것이 sealed 의 쓸모다 — 빠뜨린 경우를 실행 전에 컴파일러가 잡는다.
근거: 2-summary 「동작 방식 (4)」 · 「동작 방식 (5)」 · 「어디서 틀리나 5」.

### 8. 만들 수 있고, `case Triangle t` 로 간다

`Triangle` 은 `non-sealed` 라서 그 아래로는 상속 제한이 풀려 있다.
따라서 `RightTriangle extends Triangle` 은 허용된다.
`RightTriangle` 객체도 `Triangle` 이므로 `switch` 에서는 `case Triangle t` 에 걸린다.
명단의 세 갈래(`Circle` · `Rectangle` · `Triangle`)는 그대로이므로 `switch` 의 exhaustive 판단도 바뀌지 않는다.
근거: 2-summary 「동작 방식 (4)」 · 「동작 방식 (5)」.

### 9. 추상 메서드가 `log` 하나뿐이라서다

함수형 인터페이스의 조건은 「추상 메서드가 딱 하나」다.
`default` · `static` · `private` 메서드는 본문을 가지므로 이 셈에 들지 않는다.
`Logger` 에는 `default` 가 셋 있지만 추상 메서드는 `log` 하나이므로, 람다 하나가 `log` 의 본문이 되어 `Logger` 를 이룬다.
`Validator` 가 람다로 만들어지는 것도 같은 까닭이다.
근거: 2-summary 「동작 방식 (2)」 · 「동작 방식 (3)」 · 「문법 — 형태와 규칙」.

## 실습 정답

### 실습 1. 인터페이스 진화를 한 파일에 모으기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. 추상 메서드 `log` | `interface Logger` 의 `void log(String message);` |
| 2. 머리말을 붙여 `log` 를 부르는 `default` 셋 | `default void info` · `error` · `debug` |
| 3. 람다를 돌려주는 `static` 팩토리 | `static Logger consoleLogger()` 의 `msg -> System.out.println("  CONSOLE: " + msg)` |
| 4. 추상 메서드 `validate` | `boolean validate(String input);` |
| 5. 비었는지 검사하는 `default` | `default boolean validateNotEmpty` (`!input.isBlank()`) |
| 6. 길이 범위 검사하는 `default` | `default boolean validateLength(String input, int min, int max)` |
| 7. 나눠 쓰는 `null` 검사 | `private boolean checkNotNull` |
| 8. `private static` 도우미 | `private static String sanitize` (`input.strip()`) |
| 9. 세 구현체만 허용하는 sealed | `sealed interface Shape permits Circle, Rectangle, Triangle` |
| 10. record 둘 · `non-sealed` 클래스 하나 | `record Circle` · `record Rectangle` · `static non-sealed class Triangle` |
| 11. 넓이 · 설명 | 각 타입의 `area()` · `describe()` |
| 12. 같은 `default hello` 를 가진 두 인터페이스 | `interface A` · `interface B` |
| 13. 충돌 해결 | `static class AB` 의 `A.super.hello() + " + " + B.super.hello()` |
| 14. `default` 없는 패턴 매칭 `switch` | `case Circle c` · `case Rectangle r` · `case Triangle t` |
| 15. 나머지 `main` | `public static void main` 의 머리말 · 호출 · 타임라인 줄 |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`java/java-oop/reference/interface-evolution.java`

```java
// [객체지향 프로그래밍] 인터페이스 진화 (Java 8~17+)
// 설명: Java 8 default/static, Java 9 private, sealed interface (Java 17+)
// 팁: default 메서드는 기존 인터페이스에 메서드를 추가할 때 하위 호환성을 유지한다. sealed interface는 허용된 구현체만 가능하므로 패턴 매칭에서 default 없이 exhaustive 검사가 된다. private 메서드는 default 메서드 간 코드 중복을 제거한다.

public class Main {

    // Java 8+: default, static 메서드 - 인터페이스에 구현 코드 포함 가능
    interface Logger {
        // 핵심 추상 메서드 - 구현체가 반드시 정의
        void log(String message);

        // default 메서드: 기존 구현체 깨지지 않고 인터페이스 확장
        default void info(String msg) {
            // 추상 메서드 호출 - 구현체의 log를 사용
            log("[INFO] " + msg);
        }

        // 에러 레벨 로그
        default void error(String msg) {
            log("[ERROR] " + msg);
        }

        // 디버그 레벨 로그
        default void debug(String msg) {
            log("[DEBUG] " + msg);
        }

        // static 메서드 - 팩토리 패턴 자주 사용
        static Logger consoleLogger() {
            // 람다로 Logger 구현체 반환 (함수형 인터페이스)
            return msg -> System.out.println("  CONSOLE: " + msg);
        }
    }

    // Java 9+: private 메서드 (default 메서드 내 코드 재사용)
    interface Validator {
        // 추상 메서드
        boolean validate(String input);

        // default 메서드 - private 메서드 활용
        default boolean validateNotEmpty(String input) {
            return checkNotNull(input) && !input.isBlank();
        }

        // 길이 검증 default 메서드
        default boolean validateLength(String input, int min, int max) {
            return checkNotNull(input) && input.length() >= min && input.length() <= max;
        }

        // Java 9+: private 메서드 (외부 노출 안 됨) - default끼리 공유하는 헬퍼
        private boolean checkNotNull(String input) {
            return input != null;
        }

        // Java 9+: private static 메서드 - static 헬퍼
        private static String sanitize(String input) {
            return input == null ? "" : input.strip();
        }
    }

    // Java 17+: sealed interface - 허용된 구현체만 가능
    // permits로 명시한 클래스만 이 인터페이스를 구현 가능
    sealed interface Shape permits Circle, Rectangle, Triangle {
        double area();
        String describe();
    }

    // record는 암묵적 final - sealed 자식으로 적합
    record Circle(double radius) implements Shape {
        @Override
        public double area() { return Math.PI * radius * radius; }

        @Override
        public String describe() { return "원(반지름=" + radius + ")"; }
    }

    // 사각형 record
    record Rectangle(double width, double height) implements Shape {
        @Override
        public double area() { return width * height; }

        @Override
        public String describe() { return "사각형(" + width + "x" + height + ")"; }
    }

    // non-sealed: 이 클래스는 자유롭게 상속 가능 - sealed 봉인 해제
    static non-sealed class Triangle implements Shape {
        double base, height;

        Triangle(double base, double height) {
            this.base = base;
            this.height = height;
        }

        @Override
        public double area() { return 0.5 * base * height; }

        @Override
        public String describe() { return "삼각형(" + base + "x" + height + ")"; }
    }

    // default 메서드 충돌 해결 - 다중 구현 시 시그니처 같으면 충돌
    interface A {
        default String hello() { return "A의 hello"; }
    }

    // 같은 시그니처의 default 메서드를 가진 두 번째 인터페이스
    interface B {
        default String hello() { return "B의 hello"; }
    }

    // 두 인터페이스 동시 구현 - 충돌 해결을 위해 hello 반드시 오버라이드
    static class AB implements A, B {
        @Override
        public String hello() {
            // 충돌 시 반드시 오버라이딩 - 어떤 부모를 호출할지 명시
            // InterfaceName.super.method(): 특정 부모 인터페이스의 default 호출
            return A.super.hello() + " + " + B.super.hello();
        }
    }

    public static void main(String[] args) {
        System.out.println("=== Java 8: default & static 메서드 ===");
        // static 팩토리로 Logger 생성
        Logger logger = Logger.consoleLogger();  // static 팩토리
        // default 메서드들 호출 (info/error/debug)
        logger.info("애플리케이션 시작");
        logger.error("오류 발생");
        logger.debug("디버그 메시지");

        System.out.println();
        System.out.println("=== Java 9: private 메서드 ===");
        // 람다로 validate 구현 - 알파벳만 통과
        Validator validator = input -> input != null && input.matches("[a-zA-Z]+");
        // default 메서드들 호출 (private 헬퍼 활용)
        System.out.println("validateNotEmpty(\"hello\"): " + validator.validateNotEmpty("hello"));
        System.out.println("validateNotEmpty(\"\"): " + validator.validateNotEmpty(""));
        System.out.println("validateLength(\"hello\", 3, 10): " + validator.validateLength("hello", 3, 10));

        System.out.println();
        System.out.println("=== Java 17: sealed interface ===");
        // sealed interface의 모든 허용된 구현체
        Shape[] shapes = {
            new Circle(5),
            new Rectangle(4, 6),
            new Triangle(3, 8)
        };
        // 다형성으로 면적 계산
        for (Shape s : shapes) {
            System.out.printf("  %s -> 면적: %.2f%n", s.describe(), s.area());
        }

        // 패턴 매칭과의 조합 (Java 21+) - sealed 덕에 default 불필요
        for (Shape s : shapes) {
            // switch 표현식 + 패턴 매칭
            String info = switch (s) {
                case Circle c -> "원의 반지름: " + c.radius();
                case Rectangle r -> "사각형: " + r.width() + "x" + r.height();
                case Triangle t -> "삼각형 밑변: " + t.base;
                // sealed라 default 없어도 exhaustive
            };
            System.out.println("  패턴 매칭: " + info);
        }

        System.out.println();
        System.out.println("=== default 메서드 충돌 해결 ===");
        AB ab = new AB();
        // 두 부모의 hello가 결합된 결과
        System.out.println(ab.hello());
        System.out.println("(InterfaceName.super.method()로 특정 인터페이스 지정)");

        System.out.println();
        System.out.println("=== 인터페이스 진화 타임라인 ===");
        System.out.println("Java 8:  default/static 메서드");
        System.out.println("Java 9:  private/private static 메서드");
        System.out.println("Java 14: @Preview sealed interface");
        System.out.println("Java 17: sealed interface 정식 도입");
    }
}
```

**실행 결과** — 실행하지 않음 — Java 예제는 이 문서를 만들 때 컴파일 · 실행하지 않았다(JDK 로 돌려 확인한다).

**풀이 요점**
- `Logger` 의 `default` 셋은 모두 추상 메서드 `log` 에 일을 넘긴다 — 무엇을 할지는 구현체가 정한다.
- `default` · `static` · `private` 메서드를 아무리 더해도 추상 메서드가 하나면 람다로 구현체를 만들 수 있다.
- `checkNotNull` 은 `private` 이라 `Validator` 안에서만 쓰인다. `sanitize` 는 선언만 있고 쓰이지 않는다.
- `record` 는 암묵적 `final` 이라 sealed 의 자식으로 곧바로 알맞고, `Triangle` 은 `non-sealed` 로 아래를 연다.
- `switch` 에 `default` 를 두지 않았기에, 명단에 구현체를 더하면 이 `switch` 가 컴파일 오류로 알려 준다.
- 타임라인의 「Java 14: @Preview」 줄은 원본을 그대로 옮긴 것이며, 사실 여부는 따로 확인할 거리다 (2-summary 「어디서 틀리나 6」).

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — Java 예제는 이 문서를 만들 때 컴파일 · 실행하지 않았다(JDK 로 돌려 확인한다) |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
