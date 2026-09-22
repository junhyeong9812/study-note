# java/syntax/15 — `sealed` (17+): `permits` 와 허용 계층의 조건 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·에러 메시지는 Temurin **JDK 21.0.5** 에서 **실제로 돌려 얻은 것**이다.\
> 역어셈블은 `javap -v -p` · `javap -c -p` 출력을 그대로 옮겼다.\
> `15-a` 프로그램은 **25.0.1** 에서도 돌려 출력이 같았다 — 그것은 관찰이지 보장이 아니다.
> 버전 갈림(`--release 16` / `17`)은 JDK 21 의 `javac --release` 로 찍었다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 조건 셋 중 ① — 하위 타입에 수식어를 안 붙이면

**출력**

```text
e2/Ex.java:3: error: sealed, non-sealed or final modifiers expected
    static class Circle implements Shape { }
           ^
1 error
```

**왜 그런가**

- `sealed` 로 계층을 닫는 순간, **하위 타입마다 "너는 여기서 끝인가, 더 뻗을 것인가"를 답해야 한다.**\
  그 답을 안 적으면 컴파일러가 계층의 끝을 판정할 수 없다.
- 그래서 하위 타입에는 셋 중 하나가 **의무**다.

| 붙이는 것 | 뜻 | 완결성 |
|---|---|---|
| `final` | 여기서 끝 | 끝난다 |
| `sealed` (+ 자기 `permits`) | 내 밑도 명단으로 닫는다 | 한 단계 더 이어진다 |
| `non-sealed` | 내 밑은 자유다 | **거기서 끊긴다** |

- **`record` 로 바꾸면 통과한다.** `record` 는 암묵적으로 `final` 이기 때문이다.\
  15-a 의 실행 출력이 이것을 직접 보여 준다.

```text
Circle 은 final 인가       = true
```

- `enum` 도 같은 이유로 수식어 없이 통과한다(12번 참고).

### 2. 조건 셋 중 ② — 명단과 상속이 어긋나면

**출력** — (a) 명단 밖에서 상속

```text
e1/Ex.java:4: error: class is not allowed to extend sealed class: Shape (as it is not listed in its 'permits' clause)
    record Triangle(double b, double h) implements Shape { }
    ^
1 error
```

**출력** — (b) 명단에 적었는데 상속을 안 함

```text
e3/Ex.java:2: error: invalid permits clause
    sealed interface Shape permits Circle, Ghost { }
                                           ^
  (subclass Ghost must extend sealed class)
1 error
```

**왜 그런가**

- **두 에러는 방향이 반대다.**\
  (a)는 **하위 타입 쪽**을 가리킨다 — "명단에 없는데 들어오려 한다".\
  (b)는 **명단 쪽**을 가리킨다 — "명단에 올려 놓고 실제로는 상속을 안 했다".
- `permits` 는 **양방향 계약**이다. 한쪽만 맞으면 둘 다 에러다.
- (a)에서 `Triangle` 이 같은 파일에 있는데도 막히는 이유:\
  **암묵적 명단은 `permits` 를 생략했을 때만 생긴다.** `permits` 를 한 번 적으면 그것이 전부다.
- (a)의 메시지가 `interface` 인데도 `extend sealed class` 라고 말하는 것은 javac 의 표현이다.

**손자 타입은 `permits` 에 적을 수 없다** — 돌려 확인했다.

```java
sealed interface Shape permits Mid, Grand { }      // Grand 는 손자다
static non-sealed class Mid implements Shape { }
static class Grand extends Mid { }
```

```text
g1/Ex.java:2: error: invalid permits clause
    sealed interface Shape permits Mid, Grand { }      // Grand 는 손자다
                                        ^
  (subclass Grand must extend sealed class)
1 error
```

- (b)와 **같은 에러**가 난다. 조건은 "하위 타입"이 아니라 "**직접 하위 타입**"이다.

### 3. 조건 셋 중 ③ — 다른 패키지를 `permits` 하면

**출력** — 클래스패스(이름 없는 모듈)로 컴파일할 때

```text
pkg/src/shapes/Shape.java:2: error: class Shape in unnamed module cannot extend a sealed class in a different package
public sealed interface Shape permits Circle, other.Triangle { }
                                                   ^
1 error
```

**출력** — `module-info.java` 를 추가하면

```text
(컴파일 성공)
PermittedSubclasses:
  shapes/Circle
  other/Triangle
```

**왜 그런가**

- 메시지의 첫 구절이 **`class Shape in unnamed module`** 이다.\
  ★ 이 구절이 규칙의 정확한 모양을 알려 준다 — 금지된 것은 "다른 패키지"가 아니라\
  "**이름 없는 모듈에서의 다른 패키지**"다.
- 규칙은 이렇게 읽는다.

```text
  이름 없는 모듈 (클래스패스)            이름 있는 모듈 (module-info.java 있음)
  +-----------------------------+      +-----------------------------+
  | 경계 = 패키지                |      | 경계 = 모듈                  |
  |   permits 같은 패키지   O    |      |   permits 같은 모듈 안이면   |
  |   permits 다른 패키지   X    |      |   패키지가 달라도       O    |
  +-----------------------------+      +-----------------------------+
```

- `module demo { exports shapes; exports other; }` 한 줄이면 통과한다.\
  `PermittedSubclasses` 에는 **패키지를 포함한 내부 이름**(`other/Triangle`)이 찍힌다.
- **실무 함의**: 모듈을 쓰지 않는 보통의 프로젝트에서 이 규칙은\
  "하위 타입을 전부 같은 패키지에 모아라"와 같은 말이 된다.
- `Triangle` 을 `shapes` 패키지로 옮기기만 해도 통과한다 — 그것도 돌려 확인했다(`(컴파일 성공)`).

### 4. `default` 없는 `switch` 와 하위 타입 추가

**출력**

```text
e4/Ex.java:7: error: the switch expression does not cover all possible input values
        return switch (s) {
               ^
1 error
```

**왜 그런가**

- `Shape` 의 하위 타입은 `permits` 가 말해 주듯 **정확히 셋**인데 `case` 가 둘뿐이다.\
  컴파일러는 명단을 읽어 "덮이지 않은 경우가 있다"고 판정한다.
- **`default -> 0` 을 추가하면 통과한다.** 그리고 바로 그것이 문제다 — 돌려 확인했다.

```java
static double area(Shape s) {
    return switch (s) {
        case Circle c -> Math.PI * c.r() * c.r();
        case Square q -> q.s() * q.s();
        default       -> 0;
    };
}
// area(new Triangle(3, 4))
```

```text
Triangle 의 넓이 = 0.0
```

- **삼각형의 넓이가 0 으로 나왔는데 아무도 모른다.** 에러도 경고도 없다.
- 한 문장으로: **`default` 는 빠뜨림을 런타임의 잘못된 값으로 바꾸고, 완결성은 빌드 실패로 바꾼다.**

```text
  default 를 쓴 코드                       완결성에 기댄 코드
  +---------------------------+           +---------------------------+
  | Triangle 이 추가된다      |           | Triangle 이 추가된다      |
  |   -> 빌드 통과            |           |   -> 빌드 실패            |
  |   -> 넓이 0.0 이 흘러간다  |           |   -> 고칠 때까지 못 나간다 |
  +---------------------------+           +---------------------------+
```

- **이 에러는 1~3번과 성격이 반대다.**\
  1~3번은 `sealed` 를 **잘못 쓴** 것을 막는 에러이고,\
  4번은 `sealed` 를 **제대로 쓴 덕분에 받는** 에러다. 원해서 받는 에러다.

### 5. 분리 컴파일 — 이미 컴파일된 `switch` 는

**출력**

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

**왜 그런가**

- **2차 컴파일은 성공한다.** `Shape` 와 `Triangle` 만 보면 아무 모순이 없다.\
  `Ex.java` 를 건드리지 않았으므로 완결성 검사가 **다시 돌지 않았다.**
- `new Circle(1)` 은 정상적으로 `"원"` 을 낸다 — 기존 경로는 그대로 돈다.
- `Triangle` 인스턴스를 넣으면 **`java.lang.MatchException`** 이다.
- 그 예외가 어디서 나오는지는 `javap -c -p` 로 보인다. 소스에 없던 `default:` 분기가 바이트코드에 있다.

```text
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
```

- **javac 가 막지 못하는 이유**: 검사 시점이 다르다.

```text
  Shape.java 컴파일   -> permits 조건 검사 + PermittedSubclasses 기록
  Ex.java 컴파일      -> 그 시점의 명단을 읽어 완결성 판정 (여기서 굳는다)
  Shape.java 만 재컴파일 -> 명단은 늘었지만 Ex.class 의 판정은 옛것 그대로
```

- `MatchException` 의 javadoc 이 이 상황을 첫 번째 사례로 들고 있다(JDK 21.0.5 `src.zip`).

```text
 *     <li>Separate compilation anomalies, where parts of the type hierarchy that
 *         the patterns reference have been changed, but the pattern matching
 *         construct has not been recompiled. For example, if a sealed interface
 *         has a different set of permitted subtypes at run time than it had at
 *         compile time, ...
```

- **실무 결론**: `sealed` 계층과 그것을 `switch` 하는 코드는 같이 빌드·배포한다.\
  공개 라이브러리의 `sealed` 타입에 하위 타입을 늘리는 것은 **바이너리 호환을 깨는 변경**이다.

### 6. `non-sealed` 갈래에서 완결성은 어디까지 가나

**출력**

```text
f2/Ex.java:7: error: the switch expression does not cover all possible input values
        return switch (s) {
               ^
1 error
```

**왜 그런가**

- `Shape` 의 직접 하위는 `Circle` 과 **`Poly`** 다. `Tri` 는 `Poly` 의 하위일 뿐이다.
- `case Tri t` 는 `Poly` 를 덮지 않는다 — `Poly` 자신도, `Poly` 의 다른 하위도 남는다.
- `case Poly p` 로 고치면 통과하고, `new Tri()` 도 **그 가지로 들어온다.** 돌려 확인했다.

```text
원
다각형 Tri
```

- `Tri` 에 수식어가 필요 없는 이유: **`Poly` 가 이미 `non-sealed` 라 계층이 거기서 열렸다.**\
  수식어 의무는 `sealed` 타입의 **직접** 하위 타입에만 걸린다.

```text
  Shape (sealed)
    +-- Circle (record, final)     여기는 셀 수 있다
    +-- Poly   (non-sealed)  <---- 여기서 벽이 끝난다
          +-- Tri                  컴파일러가 더 못 센다
          +-- (누구든)
```

- **대가 한 문장**: `non-sealed` 를 하나 두는 순간, 그 갈래에서는\
  `case Poly p` 라는 **손으로 쓴 포괄 가지**에 의존하게 된다 — `default` 를 쓰는 것과 사실상 같아진다.

### 7. `permits` 를 생략하면 명단의 범위는 어디까지인가

**출력** — 같은 파일이면 컴파일러가 명단을 만들어 준다

```text
Node 의 암묵적 permits = Leaf Pair 
sum = 6
```

**출력** — 하위 타입이 같은 패키지의 **다른 파일**에 있으면

```text
src/shapes/Circle.java:2: error: class is not allowed to extend sealed class: Shape (as it is not listed in its 'permits' clause)
public record Circle(double r) implements Shape { }
       ^
src/shapes/Shape.java:2: error: sealed class must have subclasses
public sealed interface Shape { }
              ^
2 errors
```

**왜 그런가**

- 명단을 안 적으면 컴파일러가 **같은 컴파일 단위**(= 같은 `.java` 파일)를 훑어 목록을 만든다.\
  `getPermittedSubclasses()` 가 `Leaf Pair` 를 돌려주는 것이 그 증거다 —\
  소스에 안 쓴 명단이 **클래스 파일에는 들어 있다.**
- ★ 범위는 **파일**이다. 패키지가 아니다.
- 파일을 나누면 **에러가 둘 난다.**\
  하위 타입 쪽에서 "명단에 없다", `Shape` 쪽에서 "하위 타입이 하나도 없다".
- **하위 타입이 없는 `sealed` 는 선언 자체가 에러**다 — 그것만 따로 컴파일해도 같다.

```text
src/shapes/Shape.java:2: error: sealed class must have subclasses
public sealed interface Shape { }
              ^
1 error
```

- 재귀 자료구조(`Pair` 가 `Node` 를 담는 형태)는 한 파일에 다 들어가므로 이 생략형과 잘 맞는다.

### 8. 명단은 어디에 남는가

**출력** — `javap -v -p` 로 열면 속성이 있다

```text
PermittedSubclasses:
  Ex$Circle
  Ex$Square
  Ex$Rect
InnerClasses:
```

**출력** — `javap -p` 로는 안 보인다

```text
Compiled from "Ex.java"
interface Ex$Shape {
}
```

**왜 그런가**

- `permits` 는 컴파일러가 확인하고 버리는 것이 **아니다.**\
  **클래스 파일의 `PermittedSubclasses` 속성**으로 남는다.
- 남아야 하는 이유: 다른 jar 의 소스 없는 클래스를 상속하려는 시도도 막아야 하고,\
  `Class.getPermittedSubclasses()` 가 런타임에 목록을 돌려줄 수 있어야 한다.
- ★ **`-v` 가 필요하다.** `PermittedSubclasses` 는 속성이고, `javap -p` 는 멤버 선언만 찍는다.\
  `-p` 는 "private 까지 보여라"는 뜻이지 "속성을 덤프하라"는 뜻이 아니다.

**`sealed` 를 나타내는 접근 플래그는 없다.**

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

- `sealed` 는 **속성의 유무**로 표현된다. 플래그가 아니다.
- ★ **`non-sealed` 는 클래스 파일에 흔적이 전혀 없다.**\
  `Ex$Cat` 의 플래그는 평범한 클래스와 한 글자도 다르지 않다.\
  `non-sealed` 는 **소스 단계에서 "선택했다"는 것을 표시하는 것**일 뿐이다.\
  런타임에 `Cat` 이 열려 있다는 사실은 `Cat` 에 `PermittedSubclasses` 가 **없다**는 것으로 드러난다.

### 9. 리플렉션으로 물으면 무엇이 돌아오나

**출력**

```text
Circle.isSealed()               = false
Circle.getPermittedSubclasses() = null
String.getPermittedSubclasses() = null
```

**왜 그런가**

- `Circle` 은 `record` 라 `final` 이지 `sealed` 가 아니다 — `isSealed()` 는 `false`.
- ★ **`sealed` 가 아니면 `null` 이다. 빈 배열이 아니다.**\
  그냥 `for (Class<?> c : X.class.getPermittedSubclasses())` 로 돌리면 **NPE** 로 간다.\
  순서는 **`isSealed()` 로 먼저 확인하고 목록을 꺼내는 것**이다.
- 근거는 JDK 21.0.5 `lib/src.zip` 의 `Class.java` javadoc 이다 — 직접 읽었다.

```text
 * @return an array of Class objects of the permitted subclasses of this class or interface,
 *         or null if this class or interface is not sealed.
 * @jls 8.1 Class Declarations
 * @jls 9.1 Interface Declarations
 * @since 17
```

- **두 메서드 모두 `@since 17`** 이다. `isSealed()` 의 javadoc 에도 같은 태그가 있다.\
  기억이 아니라 `src.zip` 을 읽어 확인한 값이다.
- `Animal` 이 `sealed` 이고 `Cat` 이 `non-sealed` 일 때, `Animal.class.isSealed()` 는 **`true`** 다.

```text
Animal.isSealed = true / Cat.isSealed = false
Cat 의 하위 Kitten 도 Animal 인가 = true
```

- **닫힘은 한 단계씩 판정된다.** 아래쪽 갈래가 열려 있어도 `Animal` 자신의 명단은 여전히 닫혀 있다.

### 10. 버전 — 이 주제는 몇부터인가

**출력** — `javac --release 16`

```text
b/Ex.java:2: error: sealed classes are not supported in -source 16
    sealed interface Node { }                      // permits 를 안 썼다 — 같은 파일이 암묵적 목록
    ^
  (use -source 17 or higher to enable sealed classes)
b/Ex.java:6: error: '{' expected
    sealed static abstract class Animal permits Dog, Cat { }
```

**출력** — `javac --release 17`

```text
b/Ex.java:13: error: patterns in switch statements are not supported in -source 17
            case Leaf l -> l.v();
                 ^
  (use -source 21 or higher to enable patterns in switch statements)
1 error
```

**왜 그런가**

- **`sealed` · `permits` · `non-sealed` 는 Java 17 정식**이다(15·16 프리뷰).\
  `--release 16` 의 에러가 `(use -source 17 or higher to enable sealed classes)` 로 그것을 직접 말해 준다.
- ★ **`--release 17` 로 올리면 `sealed` 는 통과하지만 `switch` 가 막힌다.**\
  이번 메시지는 `(use -source 21 or higher to enable patterns in switch statements)` 다.
- **같이 외워야 할 숫자는 21** 이다.

```text
  17 ─── sealed / permits / non-sealed 정식
         Class.isSealed() · getPermittedSubclasses()
           |
           |  이 사이에는 "닫기"만 되고 "완결 switch" 는 안 된다
           v
  21 ─── switch 패턴 매칭 정식
         MatchException (@since 21)
```

- 즉 **17에서는 계층을 닫을 수 있을 뿐**이고,\
  이 주제의 값어치인 **`default` 없는 완결 `switch` 는 21부터** 쓸 수 있다.
- `MatchException` 의 `@since` 도 `src.zip` 에서 직접 확인했다 — **21**이다.
- 두 숫자를 하나로 외우면 "sealed 는 17인데 왜 switch 가 안 되지?"에서 막힌다.

### 11. 익명 클래스와 람다는 왜 막히나

**출력** — (a) 익명 클래스

```text
e5/Ex.java:5: error: anonymous classes must not extend sealed classes
        Shape s = new Shape() { };
                              ^
1 error
```

**출력** — (b) 람다

```text
f5/Ex.java:5: error: incompatible types: Op is not a functional interface
        Op o = x -> x + 1;
               ^
1 error
```

**왜 그런가**

- 익명 클래스도 람다도 **이름이 없다.** 이름이 없으면 `permits` 명단에 올릴 방법이 없다.\
  명단에 올릴 수 없는 것은 `sealed` 타입의 하위가 될 수 없다.
- (b)의 `Op` 는 추상 메서드가 정확히 하나인데도 javac 가 "**함수형 인터페이스가 아니다**"라고 말한다.\
  람다는 **이름 없는 구현체**를 만드는데, `sealed` 타입은 이름 없는 하위 타입을 가질 수 없다 —\
  그래서 `sealed` 인터페이스는 아예 함수형 인터페이스로 세어지지 않는다.\
  (JLS 9.8 의 조건 목록 자체는 이 문서에서 **열어 보지 않았다** — 근거는 위 에러 메시지다.)\
  함수형 인터페이스의 조건은 [**31번 주제**](../31-functional-interfaces/)가 정본이다.
- ★ **(b)의 메시지에는 `sealed` 라는 낱말이 없다.**\
  "추상 메서드가 하나뿐인데 왜 함수형이 아니지?"에서 한참 헤매게 되는 자리다.\
  **답은 `sealed`** 라는 것을 이 문서에서 외워 둔다.
- **테스트 코드에 주는 영향**: 가짜 구현체를 익명 클래스로 만들던 습관이 막힌다.\
  `sealed` 를 쓰기로 했으면 **테스트용 하위 타입도 이름을 갖고 명단에 올라가야 한다.**\
  이것이 불편하면 그 타입은 애초에 `sealed` 가 아니어야 한다는 신호다.

### 12. 무엇을 골라야 하나 — `enum` · `record` · Visitor

- **선택지마다 데이터의 모양이 다르면 `sealed`** 다.\
  `enum` 은 상수마다 다른 필드를 갖기 어렵다.\
  `Ok(String body)` 와 `Fail(int code)` 처럼 **필드 구성이 갈리면** `sealed` + `record` 가 맞는다.\
  선택지가 그냥 이름표뿐이면 `enum` 이 더 싸다 — [`../13-enum-classes/`](../13-enum-classes/)가 정본이다.
- **`sealed` + `record` 가 만드는 것은 합타입(sum type)** 이다.\
  `sealed` 가 **선택지의 개수를 닫고**, `record` 가 **각 선택지의 필드를 고정**한다.

```java
sealed interface Result permits Ok, Fail { }
record Ok(String body)  implements Result { }
record Fail(int code)   implements Result { }
```

- **Visitor 와의 거래**는 방향이 정확히 반대다.

```text
  Visitor 패턴                          sealed + 완결 switch
  +-----------------------------+      +-----------------------------+
  | 새 연산 추가 = Visitor 하나  |      | 새 연산 추가 = switch 하나   |
  |               (싸다)        |      |               (싸다)        |
  | 새 타입 추가 = 모든 Visitor  |      | 새 타입 추가 = 모든 switch   |
  |               수정 (비싸다)  |      |               수정 (비싸다)  |
  +-----------------------------+      +-----------------------------+
    빠뜨리면? 인터페이스가 막아준다       빠뜨리면? 완결성이 막아준다
```

- 둘 다 **연산 추가가 싸고 타입 추가가 비싸다.** 차이는 **코드량**이다 —\
  `sealed` 쪽은 `accept`/`visit` 보일러플레이트가 통째로 없어진다.\
  패턴 자체의 해설은 [`../../../../../engineering/design-patterns-gof/`](../../../../../engineering/design-patterns-gof/) 가 정본이다.
- **공개 인터페이스에 `sealed` 를 붙이면 안 되는 경우**는 **사용자가 구현하라고 만든 타입**이다.\
  플러그인·전략·리스너·콜백이 그렇다. `sealed` 는 그 목적을 정면으로 부정한다.\
  거기에 더해, 나중에 명단을 늘리면 **재컴파일하지 않은 소비자가 `MatchException` 으로 깨진다**(5번).
- **`enum` 이 `sealed` 인터페이스를 구현할 수 있다** — 돌려 확인했다.

```java
sealed interface Cmd permits Basic, Custom { }
enum Basic implements Cmd { UP, DOWN }
record Custom(String s) implements Cmd { }
```

```text
기본 UP / 사용자 q
Cmd.isSealed=true / Basic.isSealed=false
```

- `enum` 은 이미 `final` 이라 수식어가 필요 없고, `case Basic b` 하나로 모든 상수를 받는다.
- ★ **`Basic.isSealed()` 는 `false`** 다. 하위 타입이 닫혀 있다고 `sealed` 인 것이 아니다 —\
  `sealed` 는 **`PermittedSubclasses` 속성이 있느냐**의 문제다(8번).

---

## 이 주제를 확인한 실행 목록

| 프로그램 | 무엇을 확인했나 | 돌린 JDK |
|---|---|---|
| `Ex (15-a)` | sealed + record 합타입, `default` 없는 완결 `switch` 실행 | 21 · 25 (출력 동일) |
| `Ex (15-a)` + `javap -v -p` | `PermittedSubclasses` 속성에 세 타입이 박힘 · `-p` 로는 안 보임 | 21 |
| `Ex (15-a)` + `javap -c -p` | `invokedynamic typeSwitch` + `default:` 분기가 `MatchException` 을 던짐 | 21 |
| `Ex (15-b)` | `permits` 생략 시 같은 파일이 암묵적 목록 · `non-sealed` 로 재개방 | 21 |
| `Ex (15-b)` `--release 16` | `sealed classes are not supported in -source 16` | 21 의 javac |
| `Ex (15-b)` `--release 17` | `patterns in switch statements are not supported in -source 17` | 21 의 javac |
| `15-pkg` (3파일) | 이름 없는 모듈에서 다른 패키지 `permits` -> 컴파일 에러 | 21 |
| `15-pkg2` (3파일) | 같은 패키지로 옮기면 통과 | 21 |
| `15-mod` (4파일 + `module-info`) | 같은 모듈이면 다른 패키지도 통과 · `other/Triangle` 기록됨 | 21 |
| `15-runtime` (5파일, 2단계 컴파일) | 분리 컴파일 -> 런타임 `java.lang.MatchException` | 21 |
| `15-e1` | 명단 밖 상속 -> `not allowed to extend sealed class` | 21 |
| `15-e2` | 하위에 수식어 없음 -> `sealed, non-sealed or final modifiers expected` | 21 |
| `15-e3` | `permits` 대상이 상속 안 함 -> `invalid permits clause` | 21 |
| `15-e4` | 하위 타입 추가 후 `switch` 미수정 -> `does not cover all possible input values` | 21 |
| `15-e5` | 익명 클래스 -> `anonymous classes must not extend sealed classes` | 21 |
| `15-f1` / `15-f2` | `non-sealed` 갈래는 그 최상위 타입으로 받아야 완결 | 21 |
| `15-f3` | `non-sealed record` -> 파싱 에러 5개 | 21 |
| `15-f4` | `enum` 이 sealed 인터페이스 구현 · `Basic.isSealed()=false` | 21 |
| `15-f5` | 람다 -> `Op is not a functional interface` | 21 |
| `15-f6` / `15-f7` | `permits` 생략 + 다른 파일 -> 에러 2개 · 하위 0개 -> `must have subclasses` | 21 |
| `15-f8` | `getPermittedSubclasses()` 가 non-sealed 에 **`null`** 반환 | 21 |
| `15-f9` | 중첩 `sealed` — 중간 타입으로도 말단 타입으로도 완결 | 21 |
| `15-g1` | 손자 타입을 `permits` -> `invalid permits clause` | 21 |
| `15-g2` | `default -> 0` 을 넣으면 `Triangle` 넓이가 조용히 `0.0` | 21 |
| `javap -v -p` flags | `sealed` 에 접근 플래그 없음 · `non-sealed` 는 흔적 없음 | 21 |
| `src.zip` (`Class.java`) | `isSealed()` · `getPermittedSubclasses()` `@since 17` · `null` 반환 명시 | 21.0.5 |
| `src.zip` (`MatchException.java`) | `@since 21` · 분리 컴파일 사례를 javadoc 이 명시 | 21.0.5 |

**구현 의존 항목** — 버전이 오르면 다시 돌려야 하는 것

- `javap -c -p` 의 `invokedynamic typeSwitch` · `tableswitch` **형태**는 javac 의 코드 생성 방식이다.\
  `MatchException` 이 던져진다는 **사실**은 언어 보장이지만, **어떤 명령으로 던지는지**는 아니다.
- **에러 메시지 문구 자체**는 javac 의 것이다. 다른 컴파일러는 다르게 쓴다.
- `15-a` 가 21 과 25 에서 같은 출력을 낸 것은 **관찰**이다. 보장은 javadoc 과 에러 메시지 쪽에만 있다.
