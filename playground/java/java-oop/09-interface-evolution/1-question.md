# java/java-oop/09 — 인터페이스 진화 (Java 8~17+) — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 콘솔 로거로 `info` 를 부르면 (예측)

```java
// 질문용 발췌
Logger logger = Logger.consoleLogger();
logger.info("애플리케이션 시작");
logger.error("오류 발생");
```

- 이 두 호출이 찍는 두 줄은 각각 무엇인가?

### 2. 알파벳 검사 람다를 가진 `Validator` 의 세 결과 (예측)

```java
// 질문용 발췌
Validator validator = input -> input != null && input.matches("[a-zA-Z]+");
System.out.println(validator.validateNotEmpty("hello"));
System.out.println(validator.validateNotEmpty(""));
System.out.println(validator.validateLength("hello", 3, 10));
```

- 세 줄에 찍히는 `true` / `false` 는 각각 무엇인가?
- 람다에 적은 「알파벳만 통과」 규칙은 이 세 결과에 영향을 주는가?

### 3. `A` 와 `B` 를 함께 구현한 `AB` 의 `hello` (예측)

```java
// 질문용 발췌
return A.super.hello() + " + " + B.super.hello();
```

- `new AB().hello()` 는 어떤 문자열을 돌려주는가?

### 4. `default` 메서드가 하위 호환을 지키는 까닭 (왜)
- 이미 구현체가 많은 인터페이스에 메서드를 추상 메서드로 더하면 무엇이 깨지고, `default` 로 더하면 왜 깨지지 않는가?

### 5. `checkNotNull` 을 `private` 으로 둔 까닭 (왜)
- 두 `default` 메서드가 함께 쓰는 `null` 검사를 `default` 가 아니라 `private` 메서드로 둔 이유는 무엇인가?

### 6. `AB` 에서 `hello` 오버라이드를 지우면 (경계)
- `class AB implements A, B { }` 처럼 비워 두면 어떻게 되는가?

### 7. `Shape` 명단 밖의 구현체와 `case` 하나가 빠진 `switch` (경계)
- `permits` 명단에 없는 `class Square implements Shape` 를 만들면 어떻게 되는가?
- `switch (s)` 에서 `case Triangle t` 가지를 지우면 어떻게 되는가?

### 8. `non-sealed` 인 `Triangle` 의 자손과 `switch` (연결)
- 누군가 `class RightTriangle extends Triangle` 을 만들 수 있는가, 그리고 그 객체는 원본의 `switch` 에서 어느 `case` 로 가는가?

### 9. `default` 메서드가 셋이나 있는 `Logger` 가 람다로 만들어지는 까닭 (연결)
- `consoleLogger` 가 람다 하나로 `Logger` 를 만들 수 있는 것은 함수형 인터페이스의 어떤 조건 덕분인가?

## 실습

### 실습 1. 인터페이스 진화를 한 파일에 모으기

**만들 것** — Java 8 · 9 · 17 에서 인터페이스에 생긴 기능(`default` · `static` · `private` · `sealed`)과 `default` 충돌 해결을 한 `Main` 클래스 안에 모두 써 보고, `main` 에서 차례로 불러 본다.

**준비물** — JDK 21 이상(패턴 매칭 `switch` 를 쓰므로).

**요구 조건**

1단계 — `Logger` (Java 8)
1. 추상 메서드 `log(String message)` 를 둔다.
2. `default` 메서드 `info` · `error` · `debug` 가 각각 `[INFO] ` · `[ERROR] ` · `[DEBUG] ` 를 앞에 붙여 `log` 를 부른다.
3. `static` 메서드 `consoleLogger()` 가 받은 메시지 앞에 `  CONSOLE: ` 를 붙여 찍는 `Logger` 를 람다로 만들어 돌려준다.

2단계 — `Validator` (Java 9)
4. 추상 메서드 `validate(String input)` 를 둔다.
5. `default` 메서드 `validateNotEmpty` 는 `null` 이 아니고 공백뿐이 아니면 `true` 를 돌려준다.
6. `default` 메서드 `validateLength(input, min, max)` 는 `null` 이 아니고 길이가 `min` 이상 `max` 이하이면 `true` 를 돌려준다.
7. 두 `default` 메서드는 `null` 검사를 `private` 메서드 `checkNotNull` 하나로 나눠 쓴다.
8. `null` 이면 빈 문자열, 아니면 앞뒤 공백을 뗀 문자열을 돌려주는 `private static` 메서드 `sanitize` 를 둔다.

3단계 — `Shape` (Java 17)
9. `area()` 와 `describe()` 를 가진 `sealed interface Shape` 를 만들고 `Circle` · `Rectangle` · `Triangle` 만 허용한다.
10. `Circle(radius)` 와 `Rectangle(width, height)` 는 record 로, `Triangle` 은 `base` · `height` 필드를 가진 `non-sealed` 클래스로 만든다.
11. 넓이는 원 = π·r², 사각형 = 가로·세로, 삼각형 = 0.5·밑변·높이이고, `describe` 는 `원(반지름=…)` · `사각형(…x…)` · `삼각형(…x…)` 꼴이다.

4단계 — 충돌 해결
12. 같은 `default String hello()` 를 가진 인터페이스 `A` · `B` 를 만든다 (`A의 hello` · `B의 hello` 를 돌려준다).
13. 둘을 함께 구현한 `AB` 가 `hello` 를 오버라이드해 두 부모의 결과를 ` + ` 로 이어 돌려준다.

5단계 — `main`
14. `Shape` 배열을 `switch` 패턴 매칭으로 나눠 원은 반지름, 사각형은 가로x세로, 삼각형은 밑변을 문자열로 만든다 — `default` 가지 없이.
15. 그 밖의 `main` 내용(머리말 줄, 호출, 타임라인 줄)은 시작 코드에 채워 둔 대로 둔다.

**시작 코드**

```java
public class Main {

    interface Logger {
        // TODO: 추상 메서드 log
        // TODO: default 메서드 info / error / debug
        // TODO: static 팩토리 consoleLogger (람다를 돌려준다)
    }

    interface Validator {
        // TODO: 추상 메서드 validate
        // TODO: default 메서드 validateNotEmpty / validateLength (checkNotNull 사용)
        // TODO: private 메서드 checkNotNull
        // TODO: private static 메서드 sanitize
    }

    // TODO: sealed interface Shape (Circle, Rectangle, Triangle 만 허용) — area(), describe()

    // TODO: record Circle(double radius)

    // TODO: record Rectangle(double width, double height)

    // TODO: non-sealed class Triangle — 필드 base, height
    // Triangle(double base, double height) { this.base = base; this.height = height; }

    interface A {
        // TODO: default hello — "A의 hello"
    }

    interface B {
        // TODO: default hello — "B의 hello"
    }

    static class AB implements A, B {
        // TODO: hello 를 오버라이드해 두 부모의 hello 를 " + " 로 잇는다
    }

    public static void main(String[] args) {
        System.out.println("=== Java 8: default & static 메서드 ===");
        Logger logger = Logger.consoleLogger();
        logger.info("애플리케이션 시작");
        logger.error("오류 발생");
        logger.debug("디버그 메시지");

        System.out.println();
        System.out.println("=== Java 9: private 메서드 ===");
        Validator validator = input -> input != null && input.matches("[a-zA-Z]+");
        System.out.println("validateNotEmpty(\"hello\"): " + validator.validateNotEmpty("hello"));
        System.out.println("validateNotEmpty(\"\"): " + validator.validateNotEmpty(""));
        System.out.println("validateLength(\"hello\", 3, 10): " + validator.validateLength("hello", 3, 10));

        System.out.println();
        System.out.println("=== Java 17: sealed interface ===");
        Shape[] shapes = {
            new Circle(5),
            new Rectangle(4, 6),
            new Triangle(3, 8)
        };
        for (Shape s : shapes) {
            System.out.printf("  %s -> 면적: %.2f%n", s.describe(), s.area());
        }

        for (Shape s : shapes) {
            String info = switch (s) {
                // TODO: Circle / Rectangle / Triangle 패턴 세 가지 (default 없이)
            };
            System.out.println("  패턴 매칭: " + info);
        }

        System.out.println();
        System.out.println("=== default 메서드 충돌 해결 ===");
        AB ab = new AB();
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

**확인 방법** — `Main.java` 로 저장하고 아래 명령으로 돌린다.
`CONSOLE: [INFO] …` 꼴의 로그 세 줄, `true` / `false` / `true`, 도형 세 개의 넓이와 패턴 매칭 세 줄, `A의 hello + B의 hello` 가 찍히는지 본다.
덤으로 `switch` 의 `case` 하나를 지우거나 `AB` 의 오버라이드를 지워 컴파일 오류가 나는지도 본다.

```bash
java Main.java
```

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
