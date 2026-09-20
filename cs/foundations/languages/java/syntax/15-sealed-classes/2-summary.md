# java/syntax/15 — `sealed` (17+): `permits` 와 허용 계층의 조건 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — JDK 21.0.5 의 `lib/src.zip` 을 **직접 풀어 읽은** javadoc 둘이다.\
> `java.base/java/lang/Class.java` — `isSealed()` · `getPermittedSubclasses()` (`@since 17`, `@jls 8.1` `@jls 9.1`).\
> `java.base/java/lang/MatchException.java` — `@since 21`, `@jls 14.11.3` `@jls 14.30.2` `@jls 15.28.2`.\
> JLS 절 번호는 **그 javadoc 의 `@jls` 태그에 적힌 것만** 옮겼다. JLS 본문은 열지 않았다.
> **실행 검증** — 이 문서의 모든 출력·에러 메시지는 Temurin **JDK 21.0.5** 에서 실제로 돌려 얻은 것이다.\
> `javac` 12회 · `java` 6회 · `javap` 6회. 프로그램 `15-a` 는 **25.0.1** 에서도 돌려 출력이 같았다.\
> 버전 갈림(`--release 16` / `--release 17`)은 JDK 21 의 `javac --release` 로 찍은 것이다.\
> 역어셈블은 `javap -v -p` · `javap -c -p` 출력을 **그대로** 옮겼다.
> **버전** — `sealed` · `non-sealed` · `permits` 는 **Java 17** 정식(15·16 프리뷰).\
> `Class.isSealed()` · `Class.getPermittedSubclasses()` 도 **17**.\
> 다만 이 주제가 쓰는 **패턴 `switch` 는 21** 이다 — `MatchException` 도 21 이다. **둘은 같은 버전이 아니다.**
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 javac 의 실제 에러 메시지와 클래스 파일 속성으로 접지했다.

## 한눈에 — 쉽게 말하면

**`sealed` 는 「문 앞에 가입 명단을 붙여 둔 회원제 클럽」이다.**

명단에 없는 사람은 못 들어온다. 그리고 명단이 확정돼 있으니 **전원 점호가 가능하다.**\
이 두 번째 성질이 `sealed` 의 값어치다 — 닫아서 막는 것보다, 닫혀 있으니 **셀 수 있다**는 쪽이 크다.

비유 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 클럽 | `sealed` 로 선언한 타입 (`Shape`) |
| 문 앞에 붙은 가입 명단 | `permits Circle, Square, Rect` |
| 명단에 없는 사람이 들어오려 함 | 허용 목록 밖 타입이 상속 -> 컴파일 에러 |
| 회원마다 "나는 더 이상 안 들인다"고 서약 | 하위 타입의 `final` |
| 회원이 "내 밑으로는 자유롭게 받는다" | 하위 타입의 `non-sealed` |
| 회원이 자기 앞에도 작은 명단을 붙임 | 하위 타입의 `sealed` |
| **전원 점호 — 명단대로 부르면 빠짐이 없다** | **`switch` 완결성 (`default` 가 필요 없다)** |
| 명단은 같은 건물 사람만 (건물이 없으면 같은 층만) | 같은 **모듈**, 이름 없는 모듈이면 같은 **패키지** |
| 점호표를 인쇄한 뒤 명단에 사람이 늘었다 | 분리 컴파일 -> 런타임 `MatchException` |

```text
열린 계층 (그냥 interface)                닫힌 계층 (sealed interface)
+-----------------------------+          +-----------------------------+
|  Shape                      |          |  Shape  permits C, S, R     |
|   +-- Circle                |          |   +-- Circle  (final)       |
|   +-- Square                |          |   +-- Square  (final)       |
|   +-- Rect                  |          |   +-- Rect    (final)       |
|   +-- ??? (누가 더 있는지    |          |                             |
|        컴파일러가 모른다)    |          |   명단이 클래스 파일에 박힌다 |
+-----------------------------+          +-----------------------------+
  switch 에 default 가 필요하다            switch 에 default 가 필요 없다
  새 타입이 생기면 default 로 샌다          새 타입이 생기면 빌드가 멈춘다
```

**똑같은 구조로** Java 가 이렇게 동작한다: 명단 = `permits` 절, 문 앞 = 클래스 파일의 `PermittedSubclasses` 속성,\
전원 점호 = `switch` 완결성 검사, 인쇄된 점호표 = 이미 컴파일된 `switch` 의 바이트코드.

실무에서 이게 값을 내는 자리는 **"결과는 성공·실패·재시도 셋 중 하나"** 같은 **닫힌 선택지**다.\
선택지가 넷이 되는 날, `default` 를 쓴 코드는 조용히 넘어가고 `sealed` 를 쓴 코드는 **빌드가 멈춘다.**

> **합타입(sum type)** — "이것 아니면 저것"인 값을 타입으로 표현한 것. 선택지의 **개수가 닫혀 있다.**\
> 예: `Shape` 는 `Circle` 이거나 `Square` 이거나 `Rect` 이고, 그 밖은 없다.

> **완결성(exhaustiveness)** — `switch` 의 `case` 들이 입력 타입의 **모든 경우를 덮는다**는 컴파일러의 판정.\
> 예: `Shape` 의 세 하위 타입을 전부 `case` 로 적으면 `default` 없이도 컴파일이 통과한다.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 셋을 과녁으로 둔다.

1. `permits` 에 이름을 올릴 수 있는 타입의 **조건은 무엇인가** — 어기면 javac 가 **무엇을 출력하는가.**
2. 계층이 닫히면 컴파일러가 **무엇을 새로 할 수 있게 되는가** — `default` 없는 `switch` 가 왜 통과하는가.
3. 그 "닫힘"은 **어디까지 보장되는가** — 컴파일한 뒤 계층이 바뀌면 무슨 일이 일어나는가.

## 동작 방식

### (1) 닫힌 계층 — 컴파일러가 하위 타입 전부를 안다

**언제 쓰나** — "이 타입의 구현체가 몇 개인지 컴파일러가 아는가"를 따질 때.

`Ex.java (15-a)` — sealed 인터페이스 + `record` 셋 + `default` 없는 `switch`.

```java
public class Ex {
    sealed interface Shape permits Circle, Square, Rect { }
    record Circle(double r)            implements Shape { }
    record Square(double side)         implements Shape { }
    record Rect  (double w, double h)  implements Shape { }

    static double area(Shape s) {          // default 가 없다 — 완결성으로 통과한다
        return switch (s) {
            case Circle c -> Math.PI * c.r() * c.r();
            case Square q -> q.side() * q.side();
            case Rect   r -> r.w() * r.h();
        };
    }
    public static void main(String[] args) {
        for (Shape s : new Shape[]{ new Circle(1), new Square(2), new Rect(2, 3) })
            System.out.printf("%-20s area=%.4f%n", s, area(s));
        System.out.println("Shape.isSealed()          = " + Shape.class.isSealed());
        System.out.print  ("getPermittedSubclasses()  = ");
        for (Class<?> c : Shape.class.getPermittedSubclasses()) System.out.print(c.getSimpleName() + " ");
        System.out.println();
        System.out.println("Circle 은 final 인가       = "
            + java.lang.reflect.Modifier.isFinal(Circle.class.getModifiers()));
    }
}
```

**실행 결과** (JDK 21.0.5 — 25.0.1 에서도 같았다)

```text
Circle[r=1.0]        area=3.1416
Square[side=2.0]     area=4.0000
Rect[w=2.0, h=3.0]   area=6.0000
Shape.isSealed()          = true
getPermittedSubclasses()  = Circle Square Rect 
Circle 은 final 인가       = true
```

```text
  Shape (sealed)
    |
    +-- Circle (record => 암묵적으로 final)
    +-- Square (record => 암묵적으로 final)
    +-- Rect   (record => 암묵적으로 final)

  이 세 갈래 말고는 Shape 가 될 수 있는 것이 없다
      |
      v
  switch (s) 의 case 셋이 "전부"다  ->  default 없이 통과
```

- `record` 는 **암묵적으로 `final`** 이다 — 그래서 `sealed` 의 하위 타입으로 쓸 때\
  `final` 을 따로 적지 않아도 된다(실행 출력의 마지막 줄이 이것이다).
- 세 하위 타입이 전부 더 뻗지 않으므로 **`Shape` 의 구체 타입은 정확히 셋**이다.
- `area` 에 `default` 가 없는데 컴파일이 통과한다 — 이것이 완결성이다.

**비용** — 대가는 **확장 불가**다.\
라이브러리 사용자가 `Shape` 를 새로 구현할 방법이 없다. 그것이 목적이기도 하다.

### (2) 허용 목록은 소스가 아니라 클래스 파일에 박힌다

**언제 쓰나** — "명단이 정말 남아 있나, 아니면 컴파일러가 확인만 하고 버리나"를 확인할 때.

`permits` 는 주석이 아니다. **클래스 파일의 `PermittedSubclasses` 속성**으로 남는다.

```text
$ javap -v -p -classpath a 'Ex$Shape'
PermittedSubclasses:
  Ex$Circle
  Ex$Square
  Ex$Rect
InnerClasses:
```

★ **`javap -p` 로는 안 보인다.** 속성(attribute)이라서 `-v` 를 붙여야 덤프된다.

```text
$ javap -p -classpath a 'Ex$Shape'
Compiled from "Ex.java"
interface Ex$Shape {
}
```

- 이 속성이 있기 때문에 **다른 컴파일 단위**(다른 `.java`, 다른 jar)에서도 `Shape` 를 상속하려는 시도를 막을 수 있다.\
  소스가 없어도 클래스 파일만 보면 명단이 읽힌다.
- 같은 이유로 `Class.getPermittedSubclasses()` 가 런타임에 목록을 돌려줄 수 있다.

**`sealed` 에는 접근 플래그가 없다** — 명단 속성의 유무가 곧 `sealed` 다. `javap -v` 의 `flags:` 줄을 보면 안다.

```text
--- Ex$Shape (sealed interface) flags
  flags: (0x0600) ACC_INTERFACE, ACC_ABSTRACT
--- Ex$Animal (sealed abstract class) flags
  flags: (0x0420) ACC_SUPER, ACC_ABSTRACT
--- Ex$Cat (non-sealed) flags
  flags: (0x0020) ACC_SUPER
--- Ex$Dog (final) flags
  flags: (0x0030) ACC_FINAL, ACC_SUPER
```

- `sealed` 는 `flags:` 에 나타나지 않는다. `PermittedSubclasses` 속성이 있느냐 없느냐뿐이다.
- ★ **`non-sealed` 는 클래스 파일에 흔적이 아예 없다** — `Ex$Cat` 의 플래그는 평범한 클래스와 구별되지 않는다.\
  `non-sealed` 는 "상위가 닫혀 있으니 너도 무언가를 골라라"는 **소스 단계의 요구**를 만족시키는 표시일 뿐이다.

> **접근 플래그(access flags)** — 클래스 파일 맨 앞의 비트 묶음. `public`·`final`·`abstract` 같은 수식어가 여기 들어간다.\
> 예: `Ex$Dog` 의 `(0x0030)` 에서 `0x0010` 이 `ACC_FINAL` 이다.

> **속성(attribute)** — 클래스 파일에 이름표를 달고 붙는 가변 길이 데이터.\
> 예: `PermittedSubclasses` · `Record` · `InnerClasses` 가 전부 속성이다. `javap -v` 로만 보인다.

**비용** — 클래스 파일이 이름 목록만큼 커진다(하위 타입 하나당 상수 풀 항목 둘). 실무에서 셀 만한 크기가 아니다.

### (3) 완결성 — `default` 없는 `switch` 가 통과하는 이유, 그리고 그 대가

**언제 쓰나** — "왜 `default` 를 안 쓰는 편이 나은가"를 설명할 때.

```text
  default 를 쓴 코드                       완결성에 기댄 코드
  +---------------------------+           +---------------------------+
  | case Circle -> ...        |           | case Circle -> ...        |
  | case Square -> ...        |           | case Square -> ...        |
  | default     -> 0          |           | case Rect   -> ...        |
  +---------------------------+           +---------------------------+
    Rect 가 추가되면                         Rect 가 추가되면
      -> 조용히 0 이 나온다                    -> 컴파일 에러로 멈춘다
```

`Ex.java (15-e4)` — 하위 타입은 셋인데 `case` 를 둘만 적었다.

```java
sealed interface Shape permits Circle, Square, Triangle { }
record Circle(double r) implements Shape { }
record Square(double s) implements Shape { }
record Triangle(double b, double h) implements Shape { }
static double area(Shape s) {
    return switch (s) {
        case Circle c -> Math.PI * c.r() * c.r();
        case Square q -> q.s() * q.s();
    };
}
```

```text
e4/Ex.java:7: error: the switch expression does not cover all possible input values
        return switch (s) {
               ^
1 error
```

- 이것이 **`default` 를 쓰지 않는 이유 전부**다.\
  `default` 를 적었다면 `Triangle` 은 조용히 `default` 로 흘러가고, 잘못된 넓이가 계산된다.\
  적지 않았기 때문에 **새 하위 타입을 추가한 사람이 빌드에서 바로 걸린다.**
- 바꿔 말하면 완결성은 **"빠뜨릴 수 없게 만드는 장치"**다. 실행 시 방어가 아니라 **빌드 시 방어**다.

**컴파일러가 실제로 무엇을 하나** — `javap -c -p` 로 `area` 를 열면 보인다.

```text
  static double area(Ex$Shape);
    Code:
       0: aload_0
       1: dup
       2: invokestatic  #7                  // Method java/util/Objects.requireNonNull:(Ljava/lang/Object;)Ljava/lang/Object;
       5: pop
       6: astore_1
       7: iconst_0
       8: istore_2
       9: aload_1
      10: iload_2
      11: invokedynamic #13,  0             // InvokeDynamic #0:typeSwitch:(Ljava/lang/Object;I)I
      16: tableswitch   { // 0 to 2
                     0: 54
                     1: 75
                     2: 95
               default: 44
          }
      44: new           #17                 // class java/lang/MatchException
      47: dup
      48: aconst_null
      49: aconst_null
      50: invokespecial #19                 // Method java/lang/MatchException."<init>":(Ljava/lang/String;Ljava/lang/Throwable;)V
      53: athrow
      54: aload_1
      55: checkcast     #22                 // class Ex$Circle
```

- 소스에는 `default` 가 없는데 **바이트코드에는 `default:` 분기가 있다.**\
  그 분기가 하는 일은 `MatchException` 을 만들어 던지는 것뿐이다.
- 타입 판별은 `if-else` 사슬이 아니라 `invokedynamic typeSwitch` 로 **인덱스 하나를 받아** `tableswitch` 로 간다.
- 즉 **"완결하다"는 판정은 컴파일 시점의 판정**이고, 런타임에는 그 판정이 깨질 때 던질 문이 하나 열려 있다.

> **`invokedynamic`** — 호출 대상을 런타임에 한 번 정해 놓고 이후 그 자리를 고정하는 JVM 호출 명령.\
> 예: 여기서는 `typeSwitch` 부트스트랩이 "이 값이 몇 번째 `case` 인가"를 돌려준다.

> **`MatchException`** — 완결하다고 판정된 패턴 매칭이 런타임에 **아무 패턴에도 안 맞는 값**을 만났을 때 던지는 예외.\
> 예: 컴파일 뒤에 `permits` 에 타입이 하나 늘었는데 `switch` 를 다시 컴파일하지 않은 경우.

**비용** — `default` 가 없으므로 **하위 타입이 늘 때마다 모든 `switch` 를 고쳐야 한다.**\
그 비용을 치르는 대신 빠뜨림이 불가능해진다. 하위 타입이 자주 늘어나는 설계라면 이 거래가 손해다.

### (4) `non-sealed` — 계층을 다시 여는 자리

**언제 쓰나** — 닫힌 계층의 한 갈래만 확장 가능하게 열어 주고 싶을 때.

`Ex.java (15-b)` 의 뒷부분.

```java
sealed static abstract class Animal permits Dog, Cat { }
static final class Dog extends Animal { }
static non-sealed class Cat extends Animal { }  // 여기서 계층이 다시 열린다
static class Kitten extends Cat { }             // Cat 의 하위는 제한이 없다
```

```text
  Animal (sealed)          isSealed() = true
    |
    +-- Dog    (final)      여기서 끝
    +-- Cat    (non-sealed) isSealed() = false
          |
          +-- Kitten        수식어가 필요 없다
          +-- (누구든)       컴파일러가 더 이상 세지 못한다
```

**실행 결과** (JDK 21.0.5)

```text
Animal.isSealed = true / Cat.isSealed = false
Cat 의 하위 Kitten 도 Animal 인가 = true
```

- `Kitten` 은 아무 수식어도 안 붙였는데 통과한다 — **`Cat` 이 이미 열렸기 때문**이다.
- `Animal.isSealed()` 는 여전히 `true` 다. 닫힘은 **한 단계씩** 판정된다.
- ★ **완결성은 `non-sealed` 에서 멈춘다.** `Animal` 을 `switch` 할 때 `case Cat c` 는 써야 하고,\
  `case Kitten k` 만 쓰고 `Cat` 을 빼면 덮이지 않는다(「어디서 틀리나」 9번).

**비용** — `non-sealed` 를 하나 두는 순간 **그 갈래 아래는 아무것도 셀 수 없다.**\
`sealed` 를 쓴 목적의 절반(완결성)을 그 갈래에서 포기하는 것이다.

### (5) `permits` 생략 — 같은 **파일**이 암묵적 목록이다

**언제 쓰나** — 하위 타입이 전부 같은 파일에 있을 때. 명단을 두 번 적지 않아도 된다.

`Ex.java (15-b)` 의 앞부분.

```java
sealed interface Node { }                      // permits 를 안 썼다 — 같은 파일이 암묵적 목록
record Leaf(int v)                 implements Node { }
record Pair(Node left, Node right) implements Node { }
```

**실행 결과** (JDK 21.0.5)

```text
Node 의 암묵적 permits = Leaf Pair 
sum = 6
```

- 명단을 안 적었는데 `getPermittedSubclasses()` 가 `Leaf Pair` 를 돌려준다.\
  **컴파일러가 같은 파일을 훑어 명단을 만들어 넣은 것**이다.
- ★ 범위는 **파일**이지 패키지가 아니다. 하위 타입이 다른 `.java` 에 있으면 실패한다(「어디서 틀리나」 5번).
- 재귀 자료구조(`Pair` 가 `Node` 를 담는다)가 이 형태와 잘 맞는다 — 한 파일에 전부 들어간다.

**비용** — 파일이 커진다. 하위 타입이 다섯을 넘으면 파일을 나누고 `permits` 를 명시하는 편이 낫다.

### (6) 경계 — 같은 **모듈**, 모듈이 없으면 같은 **패키지**

**언제 쓰나** — 하위 타입을 다른 패키지에 두고 싶을 때. 여기서 대부분 막힌다.

먼저 **이름 없는 모듈**(그냥 클래스패스 컴파일)에서 다른 패키지를 `permits` 해 본다.

```text
pkg/src/
  shapes/Shape.java     public sealed interface Shape permits Circle, other.Triangle { }
  shapes/Circle.java    public record Circle(double r) implements Shape { }
  other/Triangle.java   public record Triangle(double b, double h) implements shapes.Shape { }
```

```text
pkg/src/shapes/Shape.java:2: error: class Shape in unnamed module cannot extend a sealed class in a different package
public sealed interface Shape permits Circle, other.Triangle { }
                                                   ^
1 error
```

`Triangle` 을 `shapes` 패키지로 옮기면 그대로 통과한다.

```text
pkg2/src/
  shapes/Shape.java     public sealed interface Shape permits Circle, Triangle { }
  shapes/Circle.java
  shapes/Triangle.java
```

```text
(컴파일 성공)
```

이제 **`module-info.java` 를 하나 두어 같은 모듈로 묶으면**, 패키지가 달라도 통과한다.

```text
mod/src/
  module-info.java      module demo { exports shapes; exports other; }
  shapes/Shape.java     public sealed interface Shape permits Circle, other.Triangle { }
  shapes/Circle.java
  other/Triangle.java   public record Triangle(double b, double h) implements shapes.Shape { }
```

```text
(컴파일 성공)
PermittedSubclasses:
  shapes/Circle
  other/Triangle
```

```text
  이름 없는 모듈 (클래스패스)            이름 있는 모듈 (module-info.java 있음)
  +-----------------------------+      +-----------------------------+
  | 경계 = 패키지                |      | 경계 = 모듈                  |
  |   shapes.Shape              |      |   demo 모듈                  |
  |     permits shapes.Circle O |      |     shapes.Shape            |
  |     permits other.Triangle X|      |       permits shapes.Circle O|
  +-----------------------------+      |       permits other.Triangle O|
    "cannot extend a sealed class      +-----------------------------+
     in a different package"
```

- 에러 메시지가 **`in unnamed module`** 로 시작한다는 점이 이 규칙의 정확한 모양을 알려 준다.\
  "다른 패키지는 안 된다"가 아니라 **"이름 없는 모듈이면 다른 패키지는 안 된다"**이다.
- 같은 모듈이면 `PermittedSubclasses` 에 `other/Triangle` 이 그대로 들어간다 — 패키지를 넘어 기록된다.

> **이름 없는 모듈(unnamed module)** — `module-info.java` 없이 클래스패스에 올린 코드가 들어가는 기본 모듈.\
> 예: `javac -d out src/**/*.java` 로 그냥 컴파일하면 전부 여기 들어간다.

**비용** — 다른 패키지에 하위 타입을 두려면 **모듈 시스템을 도입해야 한다.**\
대부분의 프로젝트에서 이것은 "하위 타입을 같은 패키지에 모아라"와 같은 말이 된다.

## 문법 — 형태와 규칙

### 선언 형태

```java
// 명단을 적는다
public sealed interface Shape permits Circle, Square, Rect { }

// 명단을 생략한다 — 같은 "파일" 의 하위 타입이 암묵적 목록
sealed interface Node { }

// 클래스에도 쓴다
public sealed abstract class Animal permits Dog, Cat { }
```

### `permits` 의 조건 셋 — 이 주제의 뼈대

| # | 조건 | 어기면 javac 가 출력하는 것 |
|---|---|---|
| 1 | 같은 **모듈**, 이름 없는 모듈이면 같은 **패키지** | `class Shape in unnamed module cannot extend a sealed class in a different package` |
| 2 | 명단에 적힌 타입이 **실제로 직접 상속**할 것 | `invalid permits clause` + `(subclass Ghost must extend sealed class)` |
| 3 | 하위 타입에 `final` · `sealed` · `non-sealed` 중 **하나** | `sealed, non-sealed or final modifiers expected` |

그리고 역방향 조건이 하나 더 있다 — **명단 밖의 타입은 상속할 수 없다.**

```text
error: class is not allowed to extend sealed class: Shape (as it is not listed in its 'permits' clause)
```

- 조건 2의 "직접"이 중요하다. 손자 타입을 `permits` 에 적을 수 없다.
- 조건 3에서 `record` 와 `enum` 은 이미 `final` 이라 **아무것도 안 적어도 된다.**\
  반대로 `non-sealed record` 는 아예 문법 에러다(「어디서 틀리나」 11번).

### 하위 타입에 붙일 수 있는 것

| 하위 타입에 붙인 것 | 그 아래로 더 뻗을 수 있나 | 완결성이 거기서 끝나나 |
|---|---|---|
| `final` | 못 뻗는다 | 끝난다 (좋은 의미) |
| `sealed` (+ 자기 `permits`) | 명단 안에서만 | 한 단계 더 이어진다 |
| `non-sealed` | 제한 없다 | **거기서 끊긴다** |
| `record` | 못 뻗는다 (암묵적 `final`) | 끝난다 |
| `enum` | 못 뻗는다 | 끝난다 |

### `sealed` + `record` = 합타입

이 조합이 이 주제의 실제 용도다. 자세한 `record` 문법은 [`../14-records/`](../14-records/) 가 정본이다.

```java
sealed interface Result permits Ok, Fail { }
record Ok(String body)  implements Result { }
record Fail(int code)   implements Result { }
```

- `sealed` 가 **선택지를 닫고**, `record` 가 **각 선택지의 필드를 고정**한다.
- 그래서 `switch (r) { case Ok o -> ...; case Fail f -> ...; }` 가 `default` 없이 성립한다.
- 여기서 한 걸음 더 나간 `case Ok(String body)` 형태(record 패턴)는 목록의 **24번 주제**가 정본이다.

## 어디서 틀리나

★ 이 주제의 값은 대부분 여기 있다. **아래 에러 메시지는 전부 JDK 21.0.5 의 javac 실출력이다.**

### 1. 하위 클래스에 수식어를 안 붙였다

`Ex.java (15-e2)`

```java
public class Ex {
    sealed interface Shape permits Circle { }
    static class Circle implements Shape { }
    public static void main(String[] args) { }
}
```

```text
e2/Ex.java:3: error: sealed, non-sealed or final modifiers expected
    static class Circle implements Shape { }
           ^
1 error
```

- 가장 자주 만나는 에러다. `sealed` 를 쓰기 시작하면 **하위 타입마다 선택을 강요받는다.**
- 메시지가 선택지 셋을 그대로 나열해 준다 — `sealed, non-sealed or final`.
- `record` 로 바꾸면 수식어 없이 통과한다(암묵적 `final`). 위 15-a 가 그 형태다.

### 2. 명단 밖에서 상속했다

`Ex.java (15-e1)`

```java
public class Ex {
    sealed interface Shape permits Circle { }
    record Circle(double r) implements Shape { }
    record Triangle(double b, double h) implements Shape { }
    public static void main(String[] args) { }
}
```

```text
e1/Ex.java:4: error: class is not allowed to extend sealed class: Shape (as it is not listed in its 'permits' clause)
    record Triangle(double b, double h) implements Shape { }
    ^
1 error
```

- **`permits` 를 적은 순간 같은 파일이라도 예외가 없다.** 암묵적 목록은 `permits` 를 **생략했을 때만** 생긴다.
- 메시지가 `interface` 인데도 "extend sealed class" 라고 말한다 — javac 의 표현이 이렇다. 놀라지 않으면 된다.

### 3. 명단에 적었는데 실제로 상속하지 않았다

`Ex.java (15-e3)`

```java
public class Ex {
    sealed interface Shape permits Circle, Ghost { }
    record Circle(double r) implements Shape { }
    record Ghost() { }
    public static void main(String[] args) { }
}
```

```text
e3/Ex.java:2: error: invalid permits clause
    sealed interface Shape permits Circle, Ghost { }
                                           ^
  (subclass Ghost must extend sealed class)
1 error
```

- `permits` 는 **양방향 계약**이다. 명단에 올린 쪽도 실제로 `implements` / `extends` 를 해야 한다.
- 이름을 바꾸거나 상속을 지우고 `permits` 를 안 고치면 여기서 걸린다.

### 4. 다른 패키지를 `permits` 했는데 모듈이 없다

```text
pkg/src/shapes/Shape.java:2: error: class Shape in unnamed module cannot extend a sealed class in a different package
public sealed interface Shape permits Circle, other.Triangle { }
                                                   ^
1 error
```

- **가장 오해가 많은 조건**이다. "같은 패키지여야 한다"가 아니라 **"같은 모듈, 모듈이 없으면 같은 패키지"**다.
- 모듈을 쓰지 않는 일반 프로젝트에서는 결과적으로 **하위 타입을 같은 패키지에 모아야 한다.**
- `module-info.java` 를 두면 패키지를 갈라도 통과한다(「동작 방식」 (6)).

### 5. `permits` 를 생략했는데 하위 타입이 다른 파일에 있다

```text
src/shapes/Shape.java     public sealed interface Shape { }
src/shapes/Circle.java    public record Circle(double r) implements Shape { }
```

```text
src/shapes/Circle.java:2: error: class is not allowed to extend sealed class: Shape (as it is not listed in its 'permits' clause)
public record Circle(double r) implements Shape { }
       ^
src/shapes/Shape.java:2: error: sealed class must have subclasses
public sealed interface Shape { }
              ^
2 errors
```

- 에러가 **둘 동시에** 난다. 하나는 하위 타입 쪽, 하나는 `Shape` 쪽이다.
- ★ 암묵적 목록의 범위는 **파일**이지 패키지가 아니다. 같은 패키지에 둬도 파일이 다르면 실패한다.
- 두 번째 에러는 그 자체로도 나온다 — **하위 타입이 하나도 없는 `sealed` 는 선언 자체가 에러다.**

```text
src/shapes/Shape.java:2: error: sealed class must have subclasses
public sealed interface Shape { }
              ^
1 error
```

### 6. 익명 클래스로 구현하려 했다

`Ex.java (15-e5)`

```java
public class Ex {
    sealed interface Shape permits Circle { }
    record Circle(double r) implements Shape { }
    public static void main(String[] args) {
        Shape s = new Shape() { };
    }
}
```

```text
e5/Ex.java:5: error: anonymous classes must not extend sealed classes
        Shape s = new Shape() { };
                              ^
1 error
```

- 익명 클래스는 `permits` 에 이름을 올릴 수 없다(이름이 없다). 그래서 통째로 금지된다.
- 테스트에서 가짜 구현체를 익명 클래스로 만들던 습관이 여기서 막힌다.\
  `sealed` 를 쓰기로 했으면 **테스트용 하위 타입도 명단에 올려야 한다.**

### 7. 람다로 구현하려 했다 — 에러 메시지가 다르다

```java
sealed interface Op permits Add { int apply(int x); }
record Add(int n) implements Op { public int apply(int x) { return x + n; } }
Op o = x -> x + 1;
```

```text
f5/Ex.java:5: error: incompatible types: Op is not a functional interface
        Op o = x -> x + 1;
               ^
1 error
```

- 추상 메서드가 **정확히 하나**인데도 함수형 인터페이스가 아니다.\
  `sealed` 인터페이스는 **람다의 대상이 될 수 없기 때문**이다.
- 메시지가 `sealed` 를 언급하지 않아 헤매기 쉽다. **"하나뿐인데 왜?"의 답이 `sealed`** 다.
- 함수형 인터페이스의 조건은 [**31번 주제**](../31-functional-interfaces/)가 정본이다.

### 8. 하위 타입을 늘리고 `switch` 를 안 고쳤다 — 이건 **좋은** 에러다

```text
e4/Ex.java:7: error: the switch expression does not cover all possible input values
        return switch (s) {
               ^
1 error
```

- 앞의 일곱과 달리 이것은 **원하던 동작**이다. 이 에러를 받기 위해 `sealed` 를 쓴다.
- `default` 를 넣어 이 에러를 끄는 순간 `sealed` 의 값어치가 대부분 사라진다.
- 값이 아니라 타입을 `switch` 할 때만 그렇다 — 패턴 `switch` 문법 자체는 목록의 **23번 주제**가 정본이다.

### 9. `non-sealed` 갈래에서 완결성이 끊긴다

```java
sealed interface Shape permits Circle, Poly { }
record Circle(double r) implements Shape { }
static non-sealed class Poly implements Shape { }
static class Tri extends Poly { }

static String name(Shape s) {
    return switch (s) {
        case Circle c -> "원";
        case Tri t    -> "삼각형";      // Poly 를 안 받았다
    };
}
```

```text
f2/Ex.java:7: error: the switch expression does not cover all possible input values
        return switch (s) {
               ^
1 error
```

- `Tri` 는 `Poly` 의 하위일 뿐이다. **`Poly` 자신**(또는 `Poly` 의 다른 하위)이 안 덮였다.
- `case Poly p` 로 고치면 통과하고, `Tri` 도 그 가지로 들어온다.

```text
원
다각형 Tri
```

- ★ 그래서 `non-sealed` 갈래는 **항상 그 갈래의 최상위 타입으로 받아야** 한다.\
  거기서부터는 컴파일러가 세어 주지 않고, `default` 를 손으로 쓰는 것과 사실상 같다.

### 10. 분리 컴파일 — 명단이 늘었는데 `switch` 를 다시 안 컴파일했다

`Ex.java (15-runtime)` — 파일을 나눠 둔다.

```text
runtime/src/
  Shape.java     public sealed interface Shape permits Circle, Square { }
  Circle.java    public record Circle(double r) implements Shape { }
  Square.java    public record Square(double s) implements Shape { }
  Ex.java        switch (s) { case Circle c -> "원"; case Square q -> "정사각형"; }   // default 없음
```

1차 컴파일은 통과한다. 그 뒤 `Shape` 의 명단에 `Triangle` 을 넣고 **`Shape` 와 `Triangle` 만** 다시 컴파일한다.

```text
(1차 컴파일 성공 — permits 는 Circle, Square 둘)
(2차 컴파일 성공 — Ex 는 다시 컴파일하지 않았다)
PermittedSubclasses:
  Circle
  Square
  Triangle
--- 실행
원
Exception in thread "main" java.lang.MatchException
	at Ex.name(Ex.java:3)
	at Ex.main(Ex.java:12)
```

- `Circle` 을 넣으면 정상적으로 `"원"` 이 나온다. **기존 경로는 그대로 돈다.**
- 새로 생긴 `Triangle` 을 넣는 순간 **`MatchException`** 이다. 앞의 바이트코드에서 본 `default: 44` 분기다.
- ★ **javac 는 이것을 막아 주지 못한다.** 완결성 검사는 `Ex.java` 를 컴파일하는 시점에만 돈다.
- 실무 함의: **`sealed` 계층과 그것을 `switch` 하는 코드는 같이 빌드·배포해야 한다.**\
  라이브러리의 `sealed` 타입에 하위 타입이 늘면 그것은 **바이너리 호환이 깨지는 변경**이다.

`MatchException` 의 javadoc 이 이 상황을 첫 번째 사례로 적고 있다(JDK 21.0.5 `src.zip`).

```text
 * <p>{@code MatchException} may be thrown when an exhaustive pattern matching
 * language construct (such as a {@code switch} expression) encounters a value
 * that does not match any of the specified patterns at run time, even though
 * the construct has been deemed exhaustive. This is intentional and can arise
 * from a number of cases:
 *
 * <ul>
 *     <li>Separate compilation anomalies, where parts of the type hierarchy that
 *         the patterns reference have been changed, but the pattern matching
 *         construct has not been recompiled. ...
```

### 11. `non-sealed record` 를 쓰려 했다

```java
sealed interface Shape permits Circle { }
non-sealed record Circle(double r) implements Shape { }
```

```text
f3/Ex.java:3: error: <identifier> expected
    non-sealed record Circle(double r) implements Shape { }
       ^
f3/Ex.java:3: error: 'sealed' is not allowed here
    non-sealed record Circle(double r) implements Shape { }
        ^
f3/Ex.java:3: error: ';' expected
    non-sealed record Circle(double r) implements Shape { }
                     ^
f3/Ex.java:3: error: invalid method declaration; return type required
    non-sealed record Circle(double r) implements Shape { }
                      ^
f3/Ex.java:3: error: ';' expected
    non-sealed record Circle(double r) implements Shape { }
                                      ^
5 errors
```

- `record` 는 이미 `final` 이라 열 수가 없다. **에러가 다섯 개 쏟아지는데 전부 파싱 에러**다.
- `non-sealed` 가 하이픈이 들어간 유일한 키워드라서, 못 쓰는 자리에서는 메시지가 이렇게 깨진다.\
  `non` / `-` / `sealed` 로 쪼개져 읽힌 것이다.

### 12. `getPermittedSubclasses()` 가 빈 배열일 거라 생각했다

```java
System.out.println("Circle.isSealed()               = " + Circle.class.isSealed());
System.out.println("Circle.getPermittedSubclasses() = " + Arrays.toString(Circle.class.getPermittedSubclasses()));
System.out.println("String.getPermittedSubclasses() = " + Arrays.toString(String.class.getPermittedSubclasses()));
```

```text
Circle.isSealed()               = false
Circle.getPermittedSubclasses() = null
String.getPermittedSubclasses() = null
```

- ★ **`null` 이다.** 빈 배열이 아니다. `sealed` 가 아닌 타입에 그냥 부르면 NPE 로 간다.
- javadoc 이 명시한다 — `or {@code null} if this class or interface is not sealed.`
- 그래서 순서는 **`isSealed()` 로 먼저 확인**하고 목록을 꺼내는 것이다.

## 구현 세부사항 대 언어 보장

이 주제는 "컴파일러가 확인만 하는 것"과 "클래스 파일에 남는 것"이 갈리므로 경계가 중요하다.

| 무엇 | 어디에 속하나 | 근거 |
|---|---|---|
| `permits` 의 조건 셋 | **언어 보장** | javac 가 거부한다 (에러 메시지 실측) |
| 하위 타입에 `final`/`sealed`/`non-sealed` 강제 | **언어 보장** | `sealed, non-sealed or final modifiers expected` |
| `PermittedSubclasses` 라는 클래스 파일 속성 | **클래스 파일 형식 사실** | `javap -v` 에 그대로 있다 |
| `isSealed()` · `getPermittedSubclasses()` (17+) | **언어/API 보장** | `Class.java` javadoc `@since 17` |
| `getPermittedSubclasses()` 가 non-sealed 에 `null` | **API 보장** | javadoc 의 `@return ... or null if ... not sealed` |
| `MatchException` 이 던져진다는 것 (21+) | **언어 보장** | `MatchException` javadoc — 분리 컴파일 사례를 명시 |
| `invokedynamic typeSwitch` + `tableswitch` 형태 | **구현 세부** | javac 21 의 코드 생성 방식. 명세가 아니다 |
| `default:` 분기가 `MatchException` 을 `new` 하는 자리 | **구현 세부** | 어떤 바이트코드로 던지느냐는 컴파일러 자유 |
| `sealed` 에 접근 플래그가 없다는 것 | **클래스 파일 형식 사실** | `flags:` 에 안 나온다 |
| `non-sealed` 가 클래스 파일에 흔적을 안 남기는 것 | **클래스 파일 형식 사실** | `Ex$Cat` 의 `flags: (0x0020) ACC_SUPER` 뿐 |
| 에러 메시지의 **문구 자체** | **구현 세부** | javac 의 것이다. 다른 컴파일러는 다르게 쓴다 |

### javac 가 언제 무엇을 검사하나 — 이 경계가 10번 사고의 원인이다

```text
  Shape.java 를 컴파일할 때
      |
      +-- permits 대상이 실제로 상속하나            <- 여기서 검사
      +-- 대상이 같은 모듈/패키지인가              <- 여기서 검사
      +-- 하위 타입에 수식어가 붙었나              <- 하위 타입 파일 컴파일 시
      |
      v
  PermittedSubclasses 속성을 Shape.class 에 기록
      |
      v
  Ex.java (switch) 를 컴파일할 때
      |
      +-- 그 시점의 PermittedSubclasses 를 읽어 완결성 판정  <- 여기서 검사
      |
      v
  판정이 끝난 뒤 명단이 바뀌면 -> 런타임 MatchException
```

- **명단 검사는 선언 시점**, **완결성 검사는 `switch` 컴파일 시점**이다. 두 시점이 다르다.
- `Ex.java` 를 다시 컴파일하지 않으면 **완결성 판정은 옛 명단 기준으로 굳어 있다.**
- 그래서 `sealed` 의 닫힘은 **"소스 트리 전체를 같이 컴파일한다"는 전제 위에서만** 완전하다.\
  그 전제가 깨지는 지점에 `MatchException` 이 놓여 있는 것이다.

> **분리 컴파일(separate compilation)** — 프로그램의 일부만 따로 컴파일해 나머지와 합쳐 돌리는 것.\
> 예: 라이브러리 jar 만 새 버전으로 바꾸고 내 코드는 그대로 두는 경우.

## 언제 쓰고 언제 안 쓰나

**쓴다**

- **닫힌 선택지를 타입으로 표현할 때** — `Result` 는 `Ok` 아니면 `Fail`, `Json` 은 객체·배열·문자열·수·불리언·널.\
  `record` 와 묶으면 그대로 합타입이 된다.
- **도메인 상태 기계** — 주문이 `Placed` · `Paid` · `Shipped` · `Cancelled` 중 하나이고 **각 상태가 다른 필드를 가질 때.**\
  `enum` 은 상태마다 다른 필드를 갖기 어렵다([`../13-enum-classes/`](../13-enum-classes/)와 갈리는 지점이 여기다).
- **Visitor 패턴을 쓰려던 자리** — "타입마다 다른 연산을 추가하고 싶다"는 요구는\
  `sealed` + 완결 `switch` 로 훨씬 짧게 풀린다. 새 연산은 새 `switch` 하나다.\
  패턴 자체의 해설은 [`../../../../../engineering/design-patterns-gof/`](../../../../../engineering/design-patterns-gof/) 가 정본이다.
- **라이브러리의 확장 표면을 좁힐 때** — "이 인터페이스는 우리가 준 구현체만 쓰라"를 컴파일러로 강제한다.

**안 쓴다**

- **확장점으로 열어 둘 인터페이스** — 플러그인·전략·리스너처럼 사용자가 구현하라고 만든 타입.\
  `sealed` 를 붙이는 순간 그 목적이 사라진다.
- **하위 타입이 자주 늘어나는 곳** — 늘 때마다 모든 `switch` 를 고쳐야 한다. 그것이 장점이자 비용이다.
- **하위 타입을 여러 패키지에 흩어 두고 싶을 때** — 모듈을 도입하지 않으면 애초에 안 된다.
- **테스트에서 익명 구현체를 많이 만드는 코드** — 익명 클래스도 람다도 못 쓴다.
- **선택지가 하나뿐일 때** — 그냥 `final` 클래스가 맞다.

**중간 지대**

- 대부분을 닫고 한 갈래만 `non-sealed` 로 여는 형태는 유효하지만,\
  **그 갈래에서 완결성이 끝난다**는 것을 알고 써야 한다. 모르면 `default` 를 안 쓴 것만으로 안심하게 된다.

## 핵심 문장

1. `sealed` 의 값어치는 **닫는 것이 아니라 셀 수 있게 되는 것**이다 — `default` 없는 `switch` 가 그 증거다.
2. `permits` 에 이름을 올리려면 **같은 모듈(모듈이 없으면 같은 패키지)** · **직접 상속** · **`final`/`sealed`/`non-sealed` 중 하나**.
3. `permits` 를 생략하면 **같은 파일**이 암묵적 목록이 된다 — 범위는 패키지가 아니라 **파일**이다.
4. 명단은 소스에만 있는 게 아니라 **클래스 파일의 `PermittedSubclasses` 속성**으로 남는다(`javap -v` 로만 보인다).
5. 완결성은 **`switch` 를 컴파일한 시점의 판정**이다 — 뒤에 명단이 늘면 런타임에 `MatchException` 이 난다.
6. `non-sealed` 는 계층을 다시 열고, **그 갈래에서 완결성은 끝난다.**
7. `sealed` 는 **17**, 패턴 `switch` 와 `MatchException` 은 **21** — 이 주제는 두 버전에 걸쳐 있다.

## 관련 자료

- [`../README.md`](../README.md) — Java 문법·API 주제 목록(이 주제는 15번)
- [`../../../../../../history/java/java-17.md`](../../../../../../history/java/java-17.md) — **언제·왜 들어왔나**(JEP 409 확정, 설계 논쟁).\
  여기는 **어떻게 쓰고 무엇을 못 하나**만 다룬다
- [`../../../../../../history/java/java-15.md`](../../../../../../history/java/java-15.md) — 1차 프리뷰 시점의 맥락. **연혁은 거기**
- [`../../../../../../history/java/java-21.md`](../../../../../../history/java/java-21.md) — 패턴 `switch` 와 `MatchException` 이 정식이 된 판.\
  **왜 21에서야 합쳐졌나는 거기**, 여기는 그 결과로 생기는 컴파일 규칙만
- [`../../../../oop-basics/`](../../../../oop-basics/) — 상속·다형성의 **개념**. 여기는 **자바가 상속을 어떻게 닫나**만
- [**09번 주제**](../09-inheritance-overriding/)(상속과 오버라이딩) — 상속과 오버라이딩의 일반 규칙. `sealed` 는 그 위에 **제한**을 얹는다
- [**11번 주제**](../11-interfaces-default-methods/)(인터페이스 — `default`/`static`/`private` 메서드) — 인터페이스의 일반 규칙. `sealed interface` 는 거기에 `permits` 가 붙은 것
- [`../12-nested-classes/`](../12-nested-classes/) — 익명 클래스. **`sealed` 가 익명 클래스를 금지하는 이유**가 그 문서의 "이름이 없다"와 이어진다
- [`../13-enum-classes/`](../13-enum-classes/) — `enum` 도 완결 `switch` 를 준다. **선택지마다 필드가 다르면 `sealed`, 같으면 `enum`**
- [`../14-records/`](../14-records/) — `record` 가 정본. 여기서는 **`sealed` 와 묶여 합타입이 되는 대목**만 쓴다
- [`../06-initialization-order/`](../06-initialization-order/) — `sealed` 계층도 초기화 순서는 똑같다. **순서 규칙은 거기**
- [`../27-equals-hashcode-contract/`](../27-equals-hashcode-contract/) — 합타입의 `equals` 는 `record` 가 만들어 준다. **계약은 거기**
- [`../../언어-특성/README.md`](../../언어-특성/README.md) — GC·JIT·클래스로더·메모리 모델. **이 주제와 겹치지 않는다** — 재서술하지 않는다
- [`../../../../../engineering/design-patterns-gof/`](../../../../../engineering/design-patterns-gof/) — Visitor 등 패턴. 여기는 **`sealed` 가 Visitor 를 대체하는 자리**까지만
- 목록의 **21번 주제**(`switch` 식) — `->` 와 `yield`, 식과 문의 차이가 정본
- 목록의 **22번 주제**(`instanceof` 패턴) — 타입 패턴의 기본형이 정본
- 목록의 **23번 주제**(`switch` 패턴 매칭, 21) — **패턴 `switch` 문법 자체가 정본.** 여기는 완결성만 다룬다
- 목록의 **24번 주제**(record 패턴) — `case Ok(String body)` 형태의 분해가 정본
- [**31번 주제**](../31-functional-interfaces/)(함수형 인터페이스) — `sealed` 가 왜 함수형 인터페이스가 못 되는지의 반대편

## 용어 풀이

- **`sealed`** — 이 타입을 상속·구현할 수 있는 타입을 명단으로 제한하는 수식어. Java 17 정식.
- **`permits`** — 그 명단을 적는 절. 생략하면 **같은 파일**의 하위 타입이 암묵적 명단이 된다.
- **`non-sealed`** — 닫힌 계층의 한 갈래를 다시 여는 수식어. 하이픈이 들어간 유일한 Java 키워드.
- **허용 하위 타입(permitted subclass)** — `permits` 명단에 오른 타입. **직접** 하위 타입이어야 한다.
- **완결성(exhaustiveness)** — `case` 들이 입력의 모든 경우를 덮는다는 컴파일러의 판정. `default` 를 생략할 수 있게 한다.
- **합타입(sum type)** — "이것 아니면 저것"을 타입으로 표현한 것. `sealed` + `record` 가 자바의 형태다.
- **`PermittedSubclasses`** — 명단이 기록되는 클래스 파일 속성. `javap -v` 로만 보이고 `javap -p` 로는 안 보인다.
- **접근 플래그(access flags)** — `public`·`final`·`abstract` 가 들어가는 비트 묶음. **`sealed` 는 여기 없다.**
- **`MatchException`** — 완결하다고 판정된 패턴 매칭이 런타임에 안 맞는 값을 만났을 때 던지는 예외. Java 21.
- **분리 컴파일(separate compilation)** — 프로그램의 일부만 따로 컴파일해 합치는 것. 완결성 판정이 낡는 원인.
- **이름 없는 모듈(unnamed module)** — `module-info.java` 없이 클래스패스에 올린 코드가 들어가는 기본 모듈.
- **`invokedynamic typeSwitch`** — 패턴 `switch` 에서 "이 값이 몇 번째 `case` 인가"를 구하는 호출. javac 21 의 구현 방식.
- **`isSealed()`** — 그 타입이 `sealed` 인지 돌려주는 리플렉션 메서드. Java 17.
- **`getPermittedSubclasses()`** — 명단을 배열로 돌려주는 리플렉션 메서드. `sealed` 가 아니면 **`null`**. Java 17.

## 더 들어가면

- **`enum` 과 `sealed` 는 같은 문제를 다른 축에서 푼다.**\
  `enum` 은 **값의 개수**를 닫고, `sealed` 는 **타입의 개수**를 닫는다.\
  선택지마다 들고 다녀야 할 데이터의 **모양이 다르면** `sealed` 쪽이다.\
  실제로 `enum` 이 `sealed` 인터페이스를 구현할 수도 있다 — 돌려 확인했다(JDK 21.0.5).

  ```java
  sealed interface Cmd permits Basic, Custom { }
  enum Basic implements Cmd { UP, DOWN }
  record Custom(String s) implements Cmd { }
  ```

  ```text
  기본 UP / 사용자 q
  Cmd.isSealed=true / Basic.isSealed=false
  ```

  `enum` 은 이미 `final` 이라 수식어를 안 붙여도 되고, `case Basic b` 하나로 모든 상수를 받는다.\
  `Basic.isSealed()` 가 `false` 인 것에 주의한다 — **하위 타입이 닫혀 있다고 `sealed` 인 것은 아니다.**
- **"바이너리 호환"의 관점에서 보면** `sealed` 타입에 하위 타입을 추가하는 것은\
  `enum` 에 상수를 추가하는 것과 같은 급의 변경이다. 재컴파일하지 않은 소비자가 런타임에 깨진다.\
  라이브러리 공개 API 에 `sealed` 를 쓸 때는 **명단을 늘리지 않겠다는 약속까지 같이 하는 셈**이다.
- **`sealed` 계층을 `switch` 하지 않고도 쓸 수 있다.**\
  `sealed` 만으로도 "이 인터페이스를 아무나 구현하지 못한다"는 보장이 생긴다.\
  보안·불변식이 목적이면 완결성 없이 `sealed` 만 쓰는 것도 완전히 정당한 용법이다.
- **하위 타입이 또 `sealed` 인 중첩 계층**은 완결성이 한 단계 더 이어진다. 돌려 확인했다(JDK 21.0.5).

  ```java
  sealed interface Expr permits Lit, Op { }
  record Lit(int v) implements Expr { }
  sealed interface Op extends Expr permits Add, Mul { }
  record Add(Expr l, Expr r) implements Op { }
  record Mul(Expr l, Expr r) implements Op { }
  ```

  `switch (e)` 에서 **중간 타입 `Op` 하나로 받아도** 완결하고,\
  **`Op` 를 건너뛰고 `Lit`/`Add`/`Mul` 말단 셋으로 받아도** 완결하다. 둘 다 컴파일된다.

  ```text
  중간 타입으로 받기 = 14
  말단 타입으로 받기 = 14
  ```

  컴파일러가 명단을 **재귀적으로 펼쳐** 판정하기 때문이다.
