# java/syntax/13 — `enum` 클래스: 상수별 본문·`EnumSet`/`EnumMap` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [JLS SE 21 §8.9 Enum Classes](https://docs.oracle.com/javase/specs/jls/se21/html/jls-8.html) (§8.9.1 상수 본문 · §8.9.2 생성자 제약 · §8.9.3 암묵 멤버) · [§14.11.1 Switch Blocks](https://docs.oracle.com/javase/specs/jls/se21/html/jls-14.html) (case 라벨·완결성). **둘 다 열어서 해당 절을 읽고 인용했다.**\
> 그리고 **JDK 21.0.5 의 `lib/src.zip`** 을 직접 풀어 읽은 `java/lang/Enum.java` · `java/util/EnumSet.java` · `java/util/RegularEnumSet.java` · `java/util/EnumMap.java` — 인용한 구현 코드와 javadoc 은 전부 그 파일에서 복사했다.
> **실행 검증** — 이 문서의 모든 출력·에러·역어셈블은 Temurin **JDK 21.0.5** 에서 실제로 돌려 얻은 것이다.\
> `case` 라벨의 한정 이름만 `--release 17 · 20 · 21` 과 Temurin **JDK 25.0.1** 넷에서 돌려 비교했다.\
> 바이트코드는 `javap -c -p` · `javap -v -p` 출력을 그대로 옮겼다.
> **버전** — `enum` 은 **Java 5**(JSR 201)에서 들어왔다. `EnumSet` · `EnumMap` 은 `@since 1.5`(src.zip 에서 직접 확인).\
> `case` 라벨에 **한정 이름**(`case Day.SAT:`)을 쓸 수 있게 된 것은 **21**(JEP 441)이다 — 아래 「어디서 틀리나」 6번.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 JLS 와 `src.zip` 으로, 동작은 실행 트레이스와 바이트코드로 접지했다.

## 한눈에 — 쉽게 말하면

**`enum` 은 학교 복도에 붙박이로 시공해 둔 사물함 줄이다.**

비유 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 복도에 붙박이로 시공된 사물함 한 칸 | enum 상수 하나 — 인스턴스가 딱 하나뿐이다 |
| 사물함에 페인트로 찍힌 순번 0,1,2… | `ordinal()` — 선언 순서에서의 자리 |
| 사물함에 붙은 이름표 | `name()` — 선언한 식별자 |
| 개교 때 복도 공사를 딱 한 번 한 것 | `<clinit>` 1회 — [**06번 주제**](../06-initialization-order/) |
| 관리실이 요청할 때마다 새로 **복사해 주는** 사물함 명단 | `values()` 가 돌려주는 배열 |
| 사물함마다 다른 여는 방식(번호키·열쇠) | 상수별 본문 — 상수마다 다른 구현 |
| 입구 벽의 전구 한 줄(칸마다 켜짐/꺼짐) | `EnumSet` — 비트 벡터 |
| 사물함 번호와 1:1로 짝지은 선반 한 줄 | `EnumMap` — ordinal 로 인덱싱하는 배열 |
| 중간에 사물함을 하나 끼워 넣기 | 상수 목록 **가운데**에 상수를 추가하는 것 |

- 복도 공사는 **개교 때 딱 한 번**이다.\
  학생이 천 명 와도 사물함이 새로 생기지 않는다 — 이것이 enum 의 싱글턴이다.
- 사물함에는 **순번**과 **이름표**가 둘 다 붙어 있다 — **순번은 옆 칸이 늘면 밀리고 이름표는 안 밀린다.**
- 관리실에 명단을 달라고 하면 **매번 새로 복사해서** 준다.\
  내가 받은 종이에 낙서를 해도 원본 명단은 멀쩡하다 — 대신 **부를 때마다 복사 비용**이 든다.
- 출석 표시는 이름을 적는 게 아니라 **칸마다 전구를 켜는 것**이다 — 일곱 칸이면 전부 `long` 하나에 들어간다.

```text
사물함 복도 (enum Day 의 상수 일곱)

  ordinal  0     1     2     3     4     5     6
         +-----+-----+-----+-----+-----+-----+-----+
 이름표  | MON | TUE | WED | THU | FRI | SAT | SUN |
         +-----+-----+-----+-----+-----+-----+-----+
            ^                                   ^
            |                                   |
         Day.MON 이라는 이름은               Day.SUN
         언제 불러도 이 칸 하나를 가리킨다     (== 로 비교해도 된다)

  관리실에 명단을 청구 = Day.values()
     1회차 [MON..SUN]   2회차 [MON..SUN]   <- 내용은 같고 종이는 다르다
                                             (values() == values() 가 false)
```

**똑같은 구조로** Java 가 이렇게 동작한다: 복도 = `enum` 클래스, 사물함 = `public static final` 상수 필드, 개교 공사 = `<clinit>`, 명단 복사 = `$VALUES.clone()`, 전구 판 = `RegularEnumSet` 의 `long elements`.

실무에서 이게 터지는 자리는 **상태 코드를 `ordinal()` 로 DB·JSON 에 저장한 코드**다.\
누가 상수 목록 **가운데**에 값을 하나 끼워 넣는 순간, 어제 저장한 `2` 가 오늘 다른 상태로 읽힌다 — **에러 없이** 그렇게 된다.

> **enum 상수(enum constant)** — `enum` 선언의 본문에 이름으로 적은 그 타입의 인스턴스 하나.\
> 예: `enum Day { MON, TUE }` 는 `Day` 타입의 인스턴스 **둘**을 만들고, `Day.MON` 이라는 `public static final` 필드에 각각 담는다.

> **ordinal** — 상수가 **선언에서 몇 번째**인지(0부터). `Enum.ordinal()` 의 javadoc 원문이 "its position in its enum declaration, where the initial constant is assigned an ordinal of zero" 다.\
> 예: `enum Day { MON, TUE }` 에서 `MON.ordinal()` 은 `0`, `TUE.ordinal()` 은 `1`.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. `enum` 은 **왜 싱글턴이 공짜인가** — 인스턴스를 더 만드는 길을 무엇이 몇 겹으로 막고 있나.
2. 상수마다 **다르게 동작**하게 하려면 — `switch` 대신 상수별 본문을 쓰면 무엇이 생기고 무엇을 잃나.
3. `EnumSet`/`EnumMap` 은 `HashSet`/`HashMap` 과 **무엇이 다른가** — 그리고 `ordinal()` 에 기대면 왜 안 되나.

## 동작 방식

### (1) `enum` 은 문법 설탕이 아니라 클래스다 — javac 가 만드는 멤버

**언제 쓰나** — "`enum` 이 실제로 무엇으로 컴파일되나"를 확인할 때. 답이 `javap` 에 그대로 있다.

```java
// Ex.java (13-a)
enum Planet {
    MERCURY(3.303e+23, 2.4397e6),
    VENUS  (4.869e+24, 6.0518e6),
    EARTH  (5.976e+24, 6.37814e6);
    private final double mass, radius;
    Planet(double mass, double radius) { this.mass = mass; this.radius = radius; }
    double surfaceGravity() { return 6.67300E-11 * mass / (radius * radius); }
}
```

```text
javap -p Ex$Planet  — 출력 그대로

Compiled from "Ex.java"
final class Ex$Planet extends java.lang.Enum<Ex$Planet> {
  public static final Ex$Planet MERCURY;
  public static final Ex$Planet VENUS;
  public static final Ex$Planet EARTH;
  private final double mass;
  private final double radius;
  private static final Ex$Planet[] $VALUES;
  public static Ex$Planet[] values();
  public static Ex$Planet valueOf(java.lang.String);
  private Ex$Planet(double, double);
  double surfaceGravity();
  private static Ex$Planet[] $values();
  static {};
}
```

```text
내가 쓴 것                      javac 가 더 얹은 것
+------------------------+     +-------------------------------------+
| 상수 이름 셋            |     | final class ... extends Enum<자기>   |
| 필드 mass · radius      | --> | public static final 필드 셋          |
| 생성자                  |     | public static values() / valueOf()   |
| surfaceGravity()        |     | private static final $VALUES 배열    |
+------------------------+     | private static $values()             |
                               | static {} = <clinit>                 |
                               +-------------------------------------+
```

그림 해설 (한 단계씩):

- `enum` 은 **`java.lang.Enum<자기 타입>` 을 상속한 진짜 클래스**로 컴파일된다.\
  JLS §8.9 원문이 "The direct superclass type of an enum class E is `Enum<E>`" 이고, 바로 다음 문장이 "An enum declaration does not have an `extends` clause, so it is not possible to explicitly declare a direct superclass type, even `Enum<E>`" 다.
- 상수 셋은 **`public static final` 필드 셋**이 되었다.\
  JLS §8.9.3 이 "For each enum constant `c` ... `E` has an implicitly declared `public static final` field of type `E` that has the same name as `c`" 라고 쓴 그대로다.
- 상수 본문이 하나도 없는 이 `Planet` 은 **`final class`** 로 찍혔다.\
  JLS §8.9: "An enum class is implicitly `final` if its declaration contains no enum constants that have a class body."
- `$VALUES` 와 `$values()` 는 **내가 쓰지 않은 것**이고 JLS 에도 없다 — javac 의 구현 수단이다(아래 「구현 세부사항 대 언어 보장」).

`<clinit>` 을 열면 싱글턴의 근거가 그대로 보인다.

```text
javap -c -p Ex$Planet  — static {} 에서 MERCURY 한 상수분과 끝부분 그대로
(VENUS·EARTH 블록은 상수 이름·ordinal·인자만 다른 같은 형태다 — 전문은 3-answer.md 1번)

  static {};
    Code:
       0: new           #1                  // class Ex$Planet
       3: dup
       4: ldc           #41                 // String MERCURY
       6: iconst_0
       7: ldc2_w        #42                 // double 3.303E23d
      10: ldc2_w        #44                 // double 2439700.0d
      13: invokespecial #46                 // Method "<init>":(Ljava/lang/String;IDD)V
      16: putstatic     #3                  // Field MERCURY:LEx$Planet;
      ...
      57: invokestatic  #59                 // Method $values:()[LEx$Planet;
      60: putstatic     #13                 // Field $VALUES:[LEx$Planet;
      63: return
```

- `new` + `invokespecial <init>` + `putstatic` 이 **상수마다 정확히 한 번씩** 있고, 마지막에 `$values()` 의 결과를 `$VALUES` 에 넣는다.
- 이 코드가 도는 곳이 **`<clinit>`** 이다 — [**06번 주제**](../06-initialization-order/)에서 본 그 메서드다.\
  클래스 초기화는 **프로세스당 딱 한 번**이고 **JVM 이 락으로 보호**하므로, 상수 객체는 한 번만 만들어지고 두 스레드가 동시에 들어와도 중복 생성이 없다.
- **그래서 싱글턴이 공짜다.** 내가 `synchronized` 도, 이중 검사 락도 쓰지 않았다.
- `ldc "MERCURY"` 와 `iconst_0` 을 보라 — **이름과 ordinal 이 생성자 인자로 앞에 붙어 있다.**\
  `javap -v` 로 실제 descriptor 를 찍으면 이렇다.

```text
javap -v -p Ex$Planet | grep -B1 -A2 'descriptor:' — 해당 부분 그대로

  private Ex$Planet(double, double);
    descriptor: (Ljava/lang/String;IDD)V
    flags: (0x0002) ACC_PRIVATE
    Code:
```

- 소스에는 `Planet(double, double)` 라고 썼는데 클래스 파일의 descriptor 는 **`(String, int, double, double)`** 다.
- 앞의 둘이 `Enum` 의 `name` 과 `ordinal` 이다. JLS §8.9.2 가 이 점을 **명시적으로 "보장이 아니다"** 라고 못박는다.

> **JLS §8.9.2 원문** — "In practice, a compiler is likely to mirror the `Enum` class by declaring `String` and `int` parameters in the default constructor of an enum class. However, these parameters are **not specified as "implicitly declared"** because different compilers do not need to agree on the form of the default constructor."

비용 — 상수 하나당 객체 하나가 클래스 초기화 때 만들어진다.\
상수가 많아도 **한 번**이고, 그 뒤로는 필드 읽기뿐이다.

> **`<clinit>`** — 컴파일러가 `static` 필드 초기화식과 `static` 블록을 모아 만드는 클래스 초기화 메서드. 클래스당 하나이고 JVM 이 직접 부른다.\
> 예: `enum` 에서는 상수 객체를 `new` 하는 코드 전부가 여기 들어간다 — 그래서 상수 생성이 "딱 한 번"이 된다. 정본은 [**06번 주제**](../06-initialization-order/).

### (2) `values()` 는 매번 복사본이다

**언제 쓰나** — `values()` 를 루프 안에서 부르고 있을 때. 또는 "이 배열 고쳐도 되나"가 궁금할 때.

```text
values() 를 부를 때 실제로 일어나는 일

   $VALUES  (클래스가 들고 있는 진짜 배열, private static final)
   +-----+-----+-----+
   |MER  |VEN  |EARTH|
   +-----+-----+-----+
        |
        |  clone()          <- 여기서 새 배열이 만들어진다
        v
   +-----+-----+-----+
   |MER  |VEN  |EARTH|   <- 호출자에게 이 복사본을 준다
   +-----+-----+-----+
        칸 안의 "객체"는 같은 객체다 (얕은 복사)
        칸을 담는 "배열"만 새것이다
```

바이트코드에 그 세 줄이 그대로 있다.

```text
javap -c -p Ex$Planet  — values() 전체

  public static Ex$Planet[] values();
    Code:
       0: getstatic     #13                 // Field $VALUES:[LEx$Planet;
       3: invokevirtual #17                 // Method "[LEx$Planet;".clone:()Ljava/lang/Object;
       6: checkcast     #18                 // class "[LEx$Planet;"
       9: areturn
```

**실행 결과** (`Ex.java (13-a)`, JDK 21.0.5)

```text
--- values() 가 같은 배열인가 ---
values() == values() ? false
망가뜨린 뒤 values()[0] = MERCURY
내가 들고 있던 배열[0] = null
```

그림 해설 (한 단계씩):

- `getstatic $VALUES` 로 진짜 배열을 꺼내고, **`invokevirtual clone()`** 으로 복사한 뒤, `checkcast` 로 타입을 되돌려 돌려준다.
- 그래서 `values() == values()` 가 **`false`** 다 — 두 번 부르면 서로 다른 배열이다.
- 받아온 배열의 0번에 `null` 을 넣어 망가뜨려도 **다음 `values()[0]` 은 `MERCURY`** 로 멀쩡하다.\
  내가 들고 있던 배열만 `null` 이 되었다.
- 이것이 **방어 복사**다. 배열은 Java 에서 불변으로 만들 수 없으므로, 복사본을 주는 것 말고는 내부 상태를 지킬 방법이 없다.

> **방어 복사(defensive copy)** — 내부 상태를 바깥에 그대로 내주지 않고 복사본을 내주어, 바깥에서 고쳐도 내부가 안 망가지게 하는 것.\
> 예: `values()` 가 `$VALUES` 를 그대로 돌려줬다면, 누군가 한 칸을 `null` 로 바꾸는 순간 그 프로세스의 모든 `values()` 호출이 오염된다.

비용 — **호출마다 배열 하나가 새로 할당된다.**\
상수 n 개면 n 칸짜리 참조 배열이다. 루프 조건에 `i < Day.values().length` 를 쓰면 **반복마다** 할당이 일어난다.\
방어책은 둘 — `private static final Day[] VALUES = values();` 로 한 번만 받아 두거나, 순회라면 `EnumSet.allOf(Day.class)` 를 쓴다.

**실행 결과** (`Ex.java (13-h)` — 방어책 확인)

```text
values() == values()   ? false
VALUES  == VALUES      ? true
VALUES  == Day.values()? false
EnumSet.allOf(Day.class) = [MON, TUE, WED, THU, FRI, SAT, SUN]
```

- `EnumSet` 이 내부에서 쓰는 상수 배열은 `getUniverse` → `SharedSecrets.getJavaLangAccess().getEnumConstantsShared(elementType)` 로 얻는 **공유 배열**이다(`EnumSet.java` 인용).\
  `values()` 와 달리 **복사하지 않는다** — 그래서 `EnumSet` 을 쓰면 순회 때 배열 할당이 없다.
- 단 `VALUES` 를 `static final` 로 캐시해 두면 **그 배열은 방어가 안 된 배열**이다. 절대 밖으로 내주지 말고 클래스 안에서만 읽는다.

### (3) 싱글턴이 공짜인 네 겹의 잠금

**언제 쓰나** — "enum 싱글턴이 왜 안전한가"를 설명해야 할 때. 잠금이 **넷**이라는 것이 요점이다.

JLS §8.9 가 셋을 직접 나열한다.

> An enum class has no instances other than those defined by its enum constants.\
> It is a compile-time error to attempt to explicitly instantiate an enum class (§15.9.1).\
> In addition to the compile-time error, **three further mechanisms** ensure that no instances of an enum class exist beyond those defined by its enum constants:
> - The final `clone` method in `Enum` ensures that enum constants can never be cloned.
> - Reflective instantiation of enum classes is prohibited.
> - Special treatment by the serialization mechanism ensures that duplicate instances are never created as a result of deserialization.

```text
인스턴스를 더 만들려는 네 개의 문 — 전부 잠겨 있다

  (1) new Planet(...)            -> 컴파일 에러 (JLS §15.9.1)
                                    생성자는 private 이기도 하다 (§8.9.2)
  (2) 리플렉션으로 newInstance   -> IllegalArgumentException
  (3) clone()                    -> protected final + CloneNotSupportedException
  (4) 역직렬화                   -> readObject 가 InvalidObjectException
       |
       v
  남은 길은 <clinit> 하나뿐 — 그리고 그것은 딱 한 번 돈다 (06번 주제)
```

**실행 결과** (`Ex.java (13-b)`, JDK 21.0.5)

```text
--- 싱글턴이 공짜인 이유 ---
리플렉션 생성 -> java.lang.IllegalArgumentException: Cannot reflectively create enum objects
Enum.clone() 선언 = protected final + throws CloneNotSupportedException
```

`src.zip` 의 `java/lang/Enum.java` 에 (3)(4)가 그대로 있다.

```text
java/lang/Enum.java — clone 의 javadoc (JDK 21.0.5 src.zip)

     * Throws CloneNotSupportedException.  This guarantees that enums
     * are never cloned, which is necessary to preserve their "singleton"
     * status.
     *
     * @return (never returns)
     */
    protected final Object clone() throws CloneNotSupportedException {
```

```text
java/lang/Enum.java — 역직렬화 (JDK 21.0.5 src.zip)

    private void readObject(ObjectInputStream in) throws IOException,
        ClassNotFoundException {
        throw new InvalidObjectException("can't deserialize enum");
    }
```

그림 해설 (한 단계씩):

- (1)은 **컴파일러가** 막는다. 생성자에 접근 제어자를 안 붙여도 JLS §8.9.2 가 "a constructor declaration with no access modifiers is `private`" 라고 정한다.
- (2)는 **JVM/리플렉션 구현이** 막는다 — `Cannot reflectively create enum objects` 라는 문장이 그 증거다.
- (3)(4)는 **`Enum` 의 `final` 메서드가** 막는다. `clone` 은 `protected final` 이라 하위 클래스가 열어 줄 수도 없다.
- 직접 만든 싱글턴 클래스가 (2)(3)(4)를 전부 막으려면 코드를 꽤 써야 한다. enum 은 **언어가 해 준다.**
- 그래서 `==` 로 비교해도 된다. JLS §8.9.1: "Because there is only one instance of each enum constant, it is permitted to use the `==` operator in place of the `equals` method ...".\
  덧붙여 `Enum.equals` 는 `final` 이고 `super.equals` 를 부르는 **동일성 비교**다 — 계약 쪽은 [`../27-equals-hashcode-contract/`](../27-equals-hashcode-contract/) 가 정본이다.

비용 — 없다. 잠금 넷 중 셋은 런타임 검사가 아니라 **선언(`final`)과 컴파일 규칙**이다.

### (4) 상수별 본문 = 익명 하위 클래스 (그리고 enum 이 `sealed` 가 된다)

**언제 쓰나** — `switch (op) { case PLUS: ... }` 를 상수마다 다른 구현으로 바꿀 때.

```java
// Ex.java (13-b)
enum Op {
    PLUS("+")  { int apply(int a, int b) { return a + b; } },
    MINUS("-") { int apply(int a, int b) { return a - b; } },
    TIMES("*") { int apply(int a, int b) { return a * b; } };
    private final String symbol;
    Op(String symbol) { this.symbol = symbol; }
    abstract int apply(int a, int b);        // 모든 상수가 구현해야 한다
}
enum Plain { A, B }                          // 상수 본문 없음 — 비교용
```

```text
상수별 본문이 있는 enum 의 실제 타입 계층

            java.lang.Enum<Ex$Op>
                    ^
                    |
              Ex$Op  (abstract, ACC_ENUM)
              PermittedSubclasses: Ex$Op$1, Ex$Op$2, Ex$Op$3
              ^        ^        ^
              |        |        |
          Ex$Op$1  Ex$Op$2  Ex$Op$3      <- 상수마다 익명 하위 클래스 하나
            PLUS     MINUS    TIMES         (각각 final)

   본문이 없는 enum:   Ex$Plain (final, ACC_ENUM)  — 하위 클래스가 없다
```

**실행 결과** (`Ex.java (13-b)`, JDK 21.0.5)

```text
3 + 4 = 7    getClass()=Ex$Op$1  getDeclaringClass()=Ex$Op
3 - 4 = -1   getClass()=Ex$Op$2  getDeclaringClass()=Ex$Op
3 * 4 = 12   getClass()=Ex$Op$3  getDeclaringClass()=Ex$Op
Plain.A getClass() = Ex$Plain
Op.class 가 abstract 인가?    true
Plain.class 가 final 인가?    true
PLUS 의 클래스 == Op.class ?  false
PLUS 의 상위 클래스 =         Ex$Op
--- 생성된 클래스 파일
Ex$Op$1.class
Ex$Op$2.class
Ex$Op$3.class
Ex$Op.class
Ex$Plain.class
Ex.class
```

클래스 파일의 속성까지 보면 `sealed` 가 실제로 찍혀 있다.

```text
javap -v -p Ex$Op  — 헤더와 PermittedSubclasses 부분 그대로

abstract class Ex$Op extends java.lang.Enum<Ex$Op>
  minor version: 0
  major version: 65
  flags: (0x4420) ACC_SUPER, ACC_ABSTRACT, ACC_ENUM
...
PermittedSubclasses:
  Ex$Op$1
  Ex$Op$2
  Ex$Op$3
```

```text
javap -v -p Ex$Plain  — flags 줄 그대로

  flags: (0x4030) ACC_FINAL, ACC_SUPER, ACC_ENUM
```

그림 해설 (한 단계씩):

- 상수 셋의 `getClass()` 가 **서로 다르다.** `Ex$Op$1`·`Ex$Op$2`·`Ex$Op$3` — 실제로 그 이름의 클래스 파일이 디스크에 생긴다.
- `getDeclaringClass()` 는 셋 다 `Ex$Op` 다.\
  **"내가 어느 enum 소속인가"를 묻는 메서드가 따로 있다** — `getClass()` 로 enum 타입을 비교하면 틀린다.
- 상수별 본문이 있고 추상 메서드가 있으면 enum 클래스 자체가 **`abstract`** 로 찍힌다(`ACC_ABSTRACT`). 본문이 없는 `Plain` 은 **`final`**(`ACC_FINAL`)이다.
- 그리고 `Ex$Op` 에 **`PermittedSubclasses`** 속성이 붙는다 — JLS §8.9 의 "An enum class `E` is implicitly **sealed** if its declaration contains at least one enum constant that has a class body. The permitted direct subclasses of `E` are the anonymous classes implicitly declared by the enum constants that have a class body" 가 그대로 클래스 파일에 나타난 것이다.\
  `sealed` 자체는 [`../15-sealed-classes/`](../15-sealed-classes/) 가 정본이다.
- JLS §8.9.1 은 그 본문이 **익명 클래스**임을 못박는다: "The optional class body of an enum constant implicitly declares an anonymous class (§15.9.5) that (i) is a direct subclass of the immediately enclosing enum class, and (ii) is `final`."\
  익명 클래스 일반은 [`../12-nested-classes/`](../12-nested-classes/) 가 정본이다.
- 추상 메서드를 두려면 **모든 상수가 구현을 줘야 한다.** JLS §8.9.2: "It is a compile-time error if an enum declaration `E` has an abstract method `m` as a member, unless `E` has at least one enum constant and all of `E` 's enum constants have class bodies that provide concrete implementations of `m`."\
  **이것이 `switch` 대비 가장 큰 이득**이다 — 상수를 하나 추가하면 구현을 안 준 그 자리가 컴파일 에러가 된다.

비용 — **클래스 파일이 상수 수만큼 늘어난다.** 상수가 30개면 클래스 파일이 31개다.\
클래스 로딩 비용과 이름 오염이 그만큼 붙는다. 분기가 한두 줄이면 `switch` 나 필드로 들고 있는 편이 낫다.

> **다형성(polymorphism)** — 같은 이름의 호출이 **받는 쪽의 실제 타입**에 따라 다른 구현으로 가는 것.\
> 예: `op.apply(3,4)` 한 줄이 `op` 가 `PLUS` 면 덧셈, `TIMES` 면 곱셈으로 간다 — 부르는 쪽 코드는 그대로다.\
> 개념 자체는 [`../../../../oop-basics/`](../../../../oop-basics/) 가 정본이고, **여기는 enum 이 그것을 어떻게 강제하나**만 다룬다.

### (5) `switch` 의 특별 대우 — 컴파일 전략이 파일 경계에서 갈린다

**언제 쓰나** — `switch (day) { case SAT: ... }` 에서 상수 이름을 **한정 없이** 쓸 수 있는 이유가 궁금할 때. 그리고 상수 순서를 바꿔도 괜찮은지 판단할 때.

JLS §14.11.1 이 case 상수를 이렇게 정한다.

> Every case constant must be either a constant expression (§15.29), or **the name of an enum constant** (§8.9.1), otherwise a compile-time error occurs.

`enum` 은 여기서 **이름을 그대로 쓸 수 있는 유일한 참조 타입**이다.\
컴파일러가 selector 의 타입을 알고 있으므로 `Day.` 를 붙일 필요가 없다.

그런데 **그 한 줄이 어떤 바이트코드가 되는지는 컴파일 단위에 따라 갈린다.**

```text
같은 .java 파일 (13-d)                 다른 .java 파일 (13-e)
+---------------------------+         +----------------------------------+
| ordinal() -> lookupswitch |         | 합성 클래스 Ex$1 을 하나 만들고    |
| ordinal 값이 호출부에 박힌다 |         | $SwitchMap$Day 를 런타임에 채운다 |
+---------------------------+         +----------------------------------+
  Day 를 고치면 Ex 도 같이 컴파일된다    Day 만 다시 컴파일해도 결과가 옳다
```

**같은 파일일 때** (`Ex.java (13-d)` — `enum Day { MON, TUE, SAT, SUN }` 가 `Ex` 안에 있다)

```text
javap -c -p Ex  — kind() 전체

  static java.lang.String kind(Ex$Day);
    Code:
       0: aload_0
       1: invokevirtual #7                  // Method Ex$Day.ordinal:()I
       4: lookupswitch  { // 2
                     2: 32
                     3: 32
               default: 35
          }
      32: ldc           #13                 // String 쉬는 날
      34: areturn
      35: ldc           #15                 // String 일하는 날
      37: areturn
```

- `case SAT:` 와 `case SUN:` 이 **숫자 `2`·`3`** 이 되어 코드에 박혔다.
- 이 숫자는 `Day` 의 선언 순서다. **`Day` 를 고치면 `Ex` 도 같이 다시 컴파일해야 한다.**

**다른 파일일 때** (`Ex.java` + `Day.java` (13-e) — 별도 컴파일 단위)

```text
javap -c -p Ex  — kind() 전체

  static java.lang.String kind(Day);
    Code:
       0: getstatic     #7                  // Field Ex$1.$SwitchMap$Day:[I
       3: aload_0
       4: invokevirtual #13                 // Method Day.ordinal:()I
       7: iaload
       8: lookupswitch  { // 2
                     1: 36
                     2: 36
               default: 39
          }
      36: ldc           #19                 // String 쉬는 날
      38: areturn
      39: ldc           #21                 // String 일하는 날
      41: areturn
```

```text
javap -c -p Ex$1  — 합성 스위치 맵 클래스 전체

Compiled from "Ex.java"
class Ex$1 {
  static final int[] $SwitchMap$Day;

  static {};
    Code:
       0: invokestatic  #1                  // Method Day.values:()[LDay;
       3: arraylength
       4: newarray       int
       6: putstatic     #7                  // Field $SwitchMap$Day:[I
       9: getstatic     #7                  // Field $SwitchMap$Day:[I
      12: getstatic     #13                 // Field Day.SAT:LDay;
      15: invokevirtual #17                 // Method Day.ordinal:()I
      18: iconst_1
      19: iastore
      20: goto          24
      23: astore_0
      24: getstatic     #7                  // Field $SwitchMap$Day:[I
      27: getstatic     #23                 // Field Day.SUN:LDay;
      30: invokevirtual #17                 // Method Day.ordinal:()I
      33: iconst_2
      34: iastore
      35: goto          39
      38: astore_0
      39: return
    Exception table:
       from    to  target type
           9    20    23   Class java/lang/NoSuchFieldError
          24    35    38   Class java/lang/NoSuchFieldError
}
```

그림 해설 (한 단계씩):

- 합성 클래스 `Ex$1` 의 `<clinit>` 이 **런타임에** `Day.SAT.ordinal()` 을 물어보고, 그 자리에 `1` 을 넣는다.\
  즉 "`SAT` 의 현재 순번이 몇이든, 그 칸을 내 스위치 번호 1로 매핑한다"는 표를 만든다.
- **예외 테이블**을 보라 — 각 매핑이 `NoSuchFieldError` 로 보호돼 있다.\
  `Day` 에서 상수가 **사라져도** 그 칸만 건너뛰고 나머지 매핑은 살아남는다.
- 그래서 `Day` 의 상수 **순서만 바꿔서 `Day` 만 다시 컴파일해도** `Ex` 의 switch 가 옳게 돈다.

**실행 결과** (`Ex.java (13-e)` — `Day` 를 `{SAT, SUN, MON, TUE}` 로 바꿔 **`Day` 만** 다시 컴파일한 뒤 `Ex` 는 그대로 실행)

```text
SAT(ordinal=0) -> 쉬는 날
SUN(ordinal=1) -> 쉬는 날
MON(ordinal=2) -> 일하는 날
TUE(ordinal=3) -> 일하는 날
```

- `SAT` 의 ordinal 이 `2` 에서 `0` 으로 바뀌었는데 **결과가 옳다.**
- `$SwitchMap` 은 **이 문제를 풀려고** 존재한다 — 바이너리 호환성을 위한 장치다.
- 단 이것은 **javac 의 전략**이지 언어 보장이 아니다(아래 「구현 세부사항 대 언어 보장」).

비용 — 다른 파일일 때 **클래스 하나와 `int[]` 하나**가 더 생기고, 분기마다 배열 접근이 한 번 더 붙는다.\
같은 파일일 때는 그 비용이 없는 대신 **ordinal 이 호출부에 박힌다.**

### (6) `EnumSet` = `long` 하나

**언제 쓰나** — enum 상수들의 집합을 다룰 때. `Set<Day>` 를 만들려는 모든 자리.

`EnumSet` 의 javadoc 첫 문단이 구조를 직접 밝힌다.

> Enum sets are represented internally as **bit vectors**. This representation is extremely compact and efficient.

```text
EnumSet<Day> 의 내부 (상수 일곱: MON TUE WED THU FRI SAT SUN)

   long elements 한 개의 비트 자리
   비트 번호     6    5    4    3    2    1    0
                SUN  SAT  FRI  THU  WED  TUE  MON      <- ordinal 이 곧 비트 번호
                +----+----+----+----+----+----+----+
   EnumSet.of(SAT, SUN)     |  1 |  1 |  0 |  0 |  0 |  0 |  0 |
                +----+----+----+----+----+----+----+
   add / remove / contains  =  비트 하나 켜기 / 끄기 / 읽기
   union / intersection     =  | 과 &  한 번
```

**실행 결과** (`Ex.java (13-g)` — 리플렉션으로 `RegularEnumSet.elements` 를 직접 읽었다)

```text
상수 순서   = [MON, TUE, WED, THU, FRI, SAT, SUN]
            SUN SAT FRI THU WED TUE MON   <- 비트는 ordinal 의 역순으로 읽는다
00000000 []
00000001 [MON]
01100000 [SAT, SUN]
00011110 [TUE, WED, THU, FRI]
01111111 [MON, TUE, WED, THU, FRI, SAT, SUN]
```

- 여덟 자리로 찍은 것은 `String.format("%8s", ...)` 의 자릿수 맞춤 때문이고, 상수는 일곱이다 — **맨 왼쪽 `0` 은 패딩**이다.
- 이 프로그램은 `java.util` 내부 필드를 리플렉션으로 읽으므로 실행에 **`--add-opens java.base/java.util=ALL-UNNAMED`** 가 필요하다.\
  붙이지 않으면 모듈 접근이 막힌다 — 즉 **보통 코드에서는 이 필드를 볼 수 없다.** 여기서는 그림을 눈으로 보여 주려고만 열었다.

구현 선택은 상수 개수로 갈린다.

```text
java/util/EnumSet.java — noneOf 의 분기 (JDK 21.0.5 src.zip)

        Enum<?>[] universe = getUniverse(elementType);
        ...
        if (universe.length <= 64)
            return new RegularEnumSet<>(elementType, universe);
        else
            return new JumboEnumSet<>(elementType, universe);
```

```text
java/util/RegularEnumSet.java — 필드와 addAll (JDK 21.0.5 src.zip)

    private long elements = 0L;
...
    void addAll() { if (universe.length != 0) elements = -1L >>> -universe.length; }
```

**실행 결과** (`Ex.java (13-c)`)

```text
Small 상수 수 = 64 -> RegularEnumSet
Big   상수 수 = 65 -> JumboEnumSet
```

그림 해설 (한 단계씩):

- 상수가 **64개 이하면 `RegularEnumSet`** — `long` **하나**가 집합 전체다.
- **65개부터 `JumboEnumSet`** — `long[]` 로 바뀐다. 경계가 64인 것은 `long` 의 비트 수다.
- `EnumSet.allOf` 는 원소를 하나씩 넣지 않는다 — `elements = -1L >>> -universe.length` **한 줄**로 필요한 비트를 전부 켠다.
- `contains` 는 해시를 구하지도, 버킷을 찾지도, `equals` 를 부르지도 않는다 — **비트 검사 하나**다.

순회 순서는 **javadoc 이 보장한다**(관측이 아니라 계약이다).

> **`EnumSet` javadoc 원문** — "The iterator returned by the `iterator` method traverses the elements in their *natural order* (the order in which the enum constants are declared)."

**실행 결과** (`Ex.java (13-c)`)

```text
--- EnumSet 은 선언 순서로 순회한다 ---
EnumSet.of(SUN, SAT) = [SAT, SUN]
HashSet 같은 내용     = [SUN, SAT]
EnumSet.range(TUE,FRI) = [TUE, WED, THU, FRI]
complementOf(weekend)  = [MON, TUE, WED, THU, FRI]
```

- `of(SUN, SAT)` 라고 **거꾸로 넣었는데** 출력은 `[SAT, SUN]` 이다 — 선언 순서로 되돌아온다.
- 같은 내용의 `HashSet` 은 `[SUN, SAT]` 로 나왔다.\
  `HashSet` 의 순서는 **계약이 아니다** — 해시 자료구조 원리는 [`../../../../../data-structure/05-hashmap/`](../../../../../data-structure/05-hashmap/) 가 정본이다.
- `range(TUE, FRI)` 와 `complementOf` 는 **비트 연산 하나로 끝나는 연산**이라 `EnumSet` 에만 있다.

비용 — **속도를 수치로 적지 않는다.** 이 문서는 측정하지 않았다.\
javadoc 자신이 이렇게만 말한다 — "All basic operations execute in constant time. They are **likely (though not guaranteed)** to be much faster than their `HashSet` counterparts."\
근거로 쓸 수 있는 것은 **구조**(해시·버킷·`equals` 없이 비트 하나)와 **메모리**(상수 64개까지 `long` 하나)까지다.

> **비트 벡터(bit vector)** — 원소 하나를 비트 한 자리로 표현해 집합 전체를 정수 하나에 담는 것.\
> 예: 요일 일곱 개의 집합이 `0b1100000` 처럼 `long` 하나가 된다 — 합집합이 `|`, 교집합이 `&` 한 번이다.

### (7) `EnumMap` = ordinal 로 인덱싱하는 배열

**언제 쓰나** — 키가 enum 인 `Map` 을 만들 때.

`EnumMap` javadoc 도 구조를 직접 밝힌다.

> Enum maps are represented internally as **arrays**. This representation is extremely compact and efficient.

```text
EnumMap<Day,Integer> 의 내부

   keyUniverse  [MON][TUE][WED][THU][FRI][SAT][SUN]     <- 키는 ordinal 순서 고정
   vals         [ 2 ][null][null][null][ 3 ][null][ 1 ]  <- 값만 담는 배열
                  ^                      ^         ^
             put(MON,2)             put(FRI,3)  put(SUN,1)

   get(FRI)  =  vals[FRI.ordinal()]  =  vals[4]    <- 해시 없음, 버킷 없음, equals 없음
```

```text
java/util/EnumMap.java — 핵심 필드와 put/get (JDK 21.0.5 src.zip)

    private final Class<K> keyType;
    private transient K[] keyUniverse;
    private transient Object[] vals;

    public V put(K key, V value) {
        typeCheck(key);
        int index = key.ordinal();
        Object oldValue = vals[index];
        vals[index] = maskNull(value);
        ...
    }

    public V get(Object key) {
        return (isValidKey(key) ?
                unmaskNull(vals[((Enum<?>)key).ordinal()]) : null);
    }
```

**실행 결과** (`Ex.java (13-c)`)

```text
--- EnumMap 도 선언 순서 ---
EnumMap  = {MON=2, FRI=3, SUN=1}
HashMap  = {SUN=1, FRI=3, MON=2}
--- null 키 ---
EnumMap.put(null,..) -> java.lang.NullPointerException: Cannot invoke "Object.getClass()" because "key" is null
HashMap.put(null,..) -> ok, 9
```

그림 해설 (한 단계씩):

- `put`/`get` 이 `key.ordinal()` 을 **배열 인덱스로 직접** 쓴다. 해시 계산도, 버킷 탐색도, `equals` 호출도 없다.
- 그래서 키의 `hashCode`/`equals` 가 무엇이든 상관이 없다 — **`EnumMap` 은 해시를 쓰지 않는다.**
- 순회 순서는 javadoc 이 보장한다: "Enum maps are maintained in the *natural order* of their keys (the order in which the enum constants are declared)."\
  `SUN` → `MON` → `FRI` 순으로 넣었는데 `{MON=2, FRI=3, SUN=1}` 로 나온 것이 그것이다.
- **`null` 키는 NPE** 다. `typeCheck(key)` 의 첫 줄 `key.getClass()` 에서 터진다 — 그래서 예외 메시지가 `Cannot invoke "Object.getClass()" because "key" is null` 이다.\
  같은 자리에서 `HashMap` 은 통과한다. 두 자료구조의 **계약 자체가 다르다.**
- `vals` 는 **상수 개수만큼 미리 잡힌다.** 상수가 1,000개인데 항목이 3개면 997칸이 `null` 로 남는다 — 이 경우는 `EnumMap` 이 불리하다.

비용 — 여기서도 **속도 수치는 쓰지 않는다.** javadoc 이 "They are likely (though **not guaranteed**) to be faster than their `HashMap` counterparts" 라고만 쓴다.\
확실한 것은 구조뿐이다: 배열 인덱싱 한 번, 해시 충돌 없음, 크기는 **항목 수가 아니라 상수 수**에 비례.

## 문법 — 형태와 규칙

직접 쓴 최소 예제다.

### 네 가지 형태

```java
// (1) 상수만
enum Day { MON, TUE, WED }

// (2) 필드 + 생성자 (상수 뒤에 세미콜론이 필요하다)
enum Planet {
    MERCURY(3.303e+23), EARTH(5.976e+24);      // <- 이 세미콜론
    private final double mass;
    Planet(double mass) { this.mass = mass; }  // 접근 제어자를 안 쓰면 private
}

// (3) 상수별 본문 + 추상 메서드
enum Op {
    PLUS { int apply(int a, int b) { return a + b; } },
    TIMES{ int apply(int a, int b) { return a * b; } };
    abstract int apply(int a, int b);          // 모든 상수가 구현해야 한다
}

// (4) 인터페이스 구현 (상속은 불가, 구현은 가능)
interface Described { String describe(); }
enum Level implements Described {
    LOW, HIGH;
    public String describe() { return name().toLowerCase(); }
}
```

### 규칙 불릿

- **상속은 안 된다.** JLS §8.9: 직접 상위 클래스는 항상 `Enum<E>` 이고 `extends` 절 자체를 쓸 수 없다.\
  반대로 **인터페이스 구현은 된다**(`EnumBody` 앞의 `ClassImplements`). 인터페이스 쪽은 [**11번 주제**](../11-interfaces-default-methods/)(인터페이스 — `default`/`static`/`private` 메서드) 가 정본이다.
- **생성자는 `private`** 이다. 안 써도 `private` 이고, `public`/`protected` 를 쓰면 컴파일 에러다(§8.9.2).\
  생성자에 `super(...)` 도 쓸 수 없다(§8.9.2).
- **생성자·인스턴스 초기화자에서 그 enum 의 `static` 필드를 못 읽는다** — 상수 변수만 예외다(§8.9.2). 「어디서 틀리나」 3번.
- **상수 뒤 세미콜론**은 상수 말고 다른 멤버가 하나라도 있으면 필수다.
- **추상 메서드를 두면 모든 상수가 본문으로 구현**해야 한다(§8.9.2). 상수 본문 안에서 **새 추상 메서드를 선언할 수는 없다**(§8.9.1).
- **상수 본문에서 선언한 메서드는 바깥에서 안 보인다** — enum 클래스의 메서드를 **오버라이드한 것만** 보인다(§8.9.1). 「어디서 틀리나」 4번.
- **중첩 enum 은 자동으로 `static`** 이다(§8.9). **`name()` 은 `final`, `toString()` 은 아니다** — `src.zip` 에서 두 선언을 직접 확인했다.
- **`values()` / `valueOf(String)` 은 내가 쓰지 않아도 생긴다**(§8.9.3). 같은 시그니처의 메서드를 직접 선언하면 충돌로 컴파일 에러다.
- **`switch` 의 `case` 에는 상수 이름을 그대로** 쓴다(§14.11.1). 21 이전에는 **한정 이름을 쓰면 에러**였다 — 「어디서 틀리나」 6번.
- **모든 상수를 `case` 로 덮으면 `default` 가 필요 없다**(§14.11.1.1 —\
  "A `default` label is permitted, but not required, in the case where the names of all the enum constants appear as case constants"). 단 이것은 **`switch` 식**에서 의미가 있다 — 목록의 **21번 주제**·**23번 주제**가 정본이다.

## 어디서 틀리나

아홉 개 중 **1·2·8번은 컴파일도 실행도 통과하고 조용히 틀린다.** 나머지는 에러가 난다.

### 1. `ordinal()` 을 저장소 키로 쓴다 — 이 주제 최대의 함정

```java
// Ex.java (13-f)
enum Status { NEW, PAID, SHIPPED }
int storedYesterday = Status.SHIPPED.ordinal();   // DB·JSON·캐시에 2 를 저장
```

**실행 결과** (`Ex.java (13-f)`, JDK 21.0.5)

```text
어제 저장한 값 = 2 (SHIPPED)
오늘 그 값을 되읽으면 = SHIPPED
이름으로 저장했다면  = SHIPPED
```

그 다음, 누군가 상수 목록 **가운데**에 하나를 끼워 넣는다 — `enum Status { NEW, CANCELLED, PAID, SHIPPED }`.

```text
오늘 그 값을 되읽으면 = PAID
이름으로 저장했다면  = SHIPPED
```

```text
어제                                   오늘 (가운데에 CANCELLED 를 끼워 넣었다)
+---+---------+                        +---+-----------+
| 0 | NEW     |                        | 0 | NEW       |
| 1 | PAID    |                        | 1 | CANCELLED |
| 2 | SHIPPED |  <- 2 를 저장했다       | 2 | PAID      |  <- 같은 2 인데 PAID 다
+---+---------+                        | 3 | SHIPPED   |
                                       +---+-----------+
  "배송 완료"가 "결제 완료"로 바뀌었다 — 예외도, 경고도, 로그도 없다
```

- **에러가 나지 않는다.** `values()[2]` 는 여전히 유효한 상수를 돌려준다 — 다른 상수일 뿐이다.
- 이름으로 저장했으면 `valueOf("SHIPPED")` 가 그대로 `SHIPPED` 다.\
  이름을 지우거나 바꾸면 그때는 **`IllegalArgumentException` 으로 터진다** — 조용히 틀리는 것보다 낫다.
- `Enum.ordinal()` 의 javadoc 자신이 이렇게 쓴다 —\
  "**Most programmers will have no use for this method.** It is designed for use by sophisticated enum-based data structures, such as `EnumSet` and `EnumMap`."
- 방어: **저장·전송·비교에는 `name()`** 을 쓴다. 숫자 코드가 꼭 필요하면 **`ordinal()` 과 무관한 고유 필드**를 직접 둔다(`SHIPPED(30)`).
- ★ 이 함정이 `ordinal()` 을 "쓰지 마라"가 아니라 **"바깥으로 내보내지 마라"** 인 이유다 — `EnumSet`/`EnumMap` 은 같은 JVM 안에서만 쓰므로 안전하다.

### 2. `values()` 를 루프 안에서 부른다

```java
for (int i = 0; i < Day.values().length; i++)     // 조건 평가마다 배열 할당
    if (Day.values()[i] == today) { ... }         // 반복마다 또 한 번
```

- 동작 방식 (2)에서 본 대로 `values()` 는 **호출마다 `clone()`** 이다.\
  위 루프는 상수 7개면 배열을 **15개** 만든다(조건 8 + 본문 7).
- 컴파일 에러도 경고도 없고, 프로파일러 없이는 안 보인다.
- 방어 둘 — 순회는 `for (Day d : EnumSet.allOf(Day.class))`, 인덱스가 필요하면 `private static final Day[] VALUES = values();` 를 한 번만 만들어 쓴다.
- 캐시한 `VALUES` 는 **밖으로 내주지 않는다.** 내주는 순간 방어 복사가 무너진다.

### 3. enum 생성자에서 그 enum 의 `static` 필드를 건드린다

```java
// Ex.java (13-err3)
enum Code {
    A("a"), B("b");
    static final Map<String, Code> BY_TAG = new HashMap<>();
    Code(String tag) { BY_TAG.put(tag, this); }   // 여기
}
```

```text
err3/Ex.java:6: error: illegal reference to static field from initializer
        Code(String tag) { BY_TAG.put(tag, this); }
                           ^
1 error
```

- **컴파일러가 막아 준다.** 막지 않았다면 `NullPointerException` 이 났을 것이다 —\
  상수 객체는 `<clinit>` 의 **맨 앞**에서 만들어지고, `BY_TAG` 초기화는 그 **뒤**에 오기 때문이다([**06번 주제**](../06-initialization-order/): `<clinit>` 은 소스 순서대로).
- JLS §8.9.2 가 규칙과 이유를 함께 적는다 —\
  "It is a compile-time error to refer to a `static` field of an enum class from a constructor, instance initializer, or instance variable initializer in the enum declaration of the class, **unless the field is a constant variable**."
- JLS 가 제시하는 고침도 그대로 쓰면 된다 — 생성자에서 넣지 말고 **`static` 블록에서 `values()` 를 돌며** 채운다.

```java
enum Code {
    A("a"), B("b");
    private final String tag;
    Code(String tag) { this.tag = tag; }
    static final Map<String, Code> BY_TAG = new HashMap<>();
    static { for (Code c : values()) BY_TAG.put(c.tag, c); }   // 상수가 다 만들어진 뒤
}
```

### 4. 상수 본문에 **새** 메서드를 선언하고 바깥에서 부른다

```java
// Ex.java (13-err2)
enum Op {
    PLUS { int apply(int a, int b) { return a + b; } int extra() { return 1; } };
    abstract int apply(int a, int b);
}
// Op.PLUS.extra()
```

```text
err2/Ex.java:6: error: cannot find symbol
    public static void main(String[] args) { System.out.println(Op.PLUS.extra()); }
                                                                       ^
  symbol:   method extra()
  location: variable PLUS of type Op
1 error
```

- `PLUS` 의 **정적 타입은 `Op`** 다. `Op` 에 `extra()` 가 없으므로 안 보인다.\
  런타임 타입은 `Ex$Op$1` 이지만 그건 **이름 없는 익명 클래스**라 타입으로 적을 수도 없다.
- JLS §8.9.1: "Instance methods declared in these class bodies may be invoked outside the enclosing enum class **only if they override accessible methods** in the enclosing enum class."
- 방어: 바깥에서 부를 메서드는 **enum 본체에 `abstract` 로 선언**하고 상수 본문이 구현한다.

### 5. 옛 `switch` **문**에 `null` 을 넣는다

```java
// Ex.java (13-err5)
Day d = null;
switch (d) { case MON: break; default: break; }
```

```text
Exception in thread "main" java.lang.NullPointerException: Cannot invoke "Ex$Day.ordinal()" because "<local1>" is null
	at Ex.main(Ex.java:5)
```

- **`default:` 가 있어도 안 잡힌다.** 예외 메시지를 보라 — `ordinal()` 을 부르다 터졌다.\
  동작 방식 (5)에서 본 그 `invokevirtual ordinal()` 이다. 분기를 고르기도 전에 NPE 다.
- 21 부터는 `case null` 을 쓸 수 있다(§14.11.1 의 `SwitchLabel: case null [, default]`). 정본은 목록의 **23번 주제**.
- 방어: 21 미만이면 `switch` 앞에서 `null` 을 걸러 낸다.

### 6. `case Day.SAT:` — 한정 이름은 버전에 따라 갈린다

```java
// Ex.java (13-err4)
switch (d) { case Day.SAT: System.out.println("주말"); break; default: break; }
```

```text
--- release 17
err4/Ex.java:5: error: an enum switch case label must be the unqualified name of an enumeration constant
        switch (d) { case Day.SAT: System.out.println("주말"); break; default: break; }
                             ^
1 error
--- release 20
(위와 한 글자도 같은 에러 — 전문은 3-answer.md 9번)
--- release 21
주말
--- JDK 25.0.1 기본
주말
```

- `--release 17` · `--release 20` 은 **컴파일 에러**, `--release 21` 과 JDK 25 는 **통과**다.\
  넷을 실제로 돌려 얻은 결과다.
- 21 에서 완화된 것이 **JEP 441**(switch 패턴 매칭 정식화)의 일부다 — 연혁은 [`../../../../../../history/java/java-21.md`](../../../../../../history/java/java-21.md).\
  JLS SE 21 §14.11.1 의 문장도 "the name of an enum constant" 로 **`unqualified` 라는 한정이 빠져 있다.**
- 실무 함의: **21 로 올린 코드를 17 로 되돌리면 이 자리가 깨진다.** 반대 방향은 안전하다.

### 7. enum 을 상속하려고 한다

```java
// Ex.java (13-err1)
enum Base { A, B }
static class Sub extends Base { }
```

```text
err1/Ex.java:3: error: cannot inherit from final Base
    static class Sub extends Base { }
                             ^
err1/Ex.java:3: error: enum classes are not extensible
    static class Sub extends Base { }
           ^
2 errors
```

- 에러가 **둘** 난다 — `final` 이라서, 그리고 enum 이라서. 상수 본문이 있어 `abstract`/`sealed` 인 enum 이라도 바깥에서는 못 늘린다(허용 하위 클래스가 **그 익명 클래스들로 고정**되기 때문이다).
- "공통 동작을 물려주고 싶다"면 **인터페이스를 구현**한다. 여러 enum 이 같은 인터페이스를 구현하면 하나의 타입으로 묶인다.

### 8. `toString()` 을 바꿔 놓고 `valueOf(toString())` 으로 되읽는다

**실행 결과** (`Ex.java (13-h)`)

```text
--- name() 과 toString() 은 다른 것이다 ---
Op.PLUS.toString() = +
Op.PLUS.name()     = PLUS
valueOf("+") -> java.lang.IllegalArgumentException: No enum constant Ex.Op.+
valueOf(name())    = PLUS
```

- `toString()` 은 오버라이드할 수 있고 **실제로 자주 한다**(화면 표시용 기호·한글 라벨).
- `valueOf` 는 **`name()` 으로만** 찾는다.\
  `src.zip` 의 `Enum.valueOf` 가 `enumClass.enumConstantDirectory().get(name)` 으로 조회하고, 없으면 `No enum constant <타입>.<이름>` 을 던진다.
- 즉 **쓸 때는 `toString()`, 읽을 때는 `valueOf()`** 를 쓰면 왕복이 깨진다.
- 방어: 직렬화 왕복에는 **항상 `name()`** 을 쓴다.\
  표시용 문자열로 역변환이 필요하면 **역인덱스 `Map` 을 `static` 블록에서** 직접 만든다(3번의 고친 코드와 같은 형태).

### 9. 그 밖의 경계 둘

- **`EnumMap` 에 `null` 키를 넣으면 NPE** 다 — `HashMap` 은 통과한다(동작 방식 7).\
  `HashMap` 에서 `EnumMap` 으로 바꾸는 리팩토링이 **런타임에만** 터지는 자리다.
- **상수 64개/65개 경계는 언어 보장이 아니다.** `RegularEnumSet`/`JumboEnumSet` 은 `java.util` 의 **패키지 전용 구현 클래스**이고 `EnumSet` 의 javadoc 에는 이름조차 없다.\
  실측(`13-c`)은 21.0.5 에서 그렇더라는 **관측**이다 — 코드가 이 경계에 기대면 안 된다.

## 구현 세부사항 대 언어 보장

이 주제는 `javap` 로 보이는 것이 많아서 **본 것을 그대로 규칙으로 외우기 쉽다.** 갈라 둔다.

| 항목 | 어느 쪽인가 | 근거 |
|---|---|---|
| `values()` 가 **선언 순서**대로 상수를 담은 배열을 준다 | **언어 보장** | JLS §8.9.3 "in the same order as they appear in the body of the declaration of E" |
| 내가 받은 배열을 고쳐도 **다음 호출은 멀쩡하다** | **관측 + 필연** (아래 주 참조) | 실행 결과 `values()==values()` 가 `false`, 0번을 망가뜨려도 다음 호출은 정상 |
| `$VALUES`·`$values()` 라는 **이름**, `clone()` 이라는 **수단** | 구현 세부 | JLS 에 없다. `javap` 로만 보인다 |
| `ordinal()` 이 **선언에서의 위치**(0부터) | **언어 보장** | `Enum.ordinal()` javadoc "its position in its enum declaration" |
| 생성자의 실제 descriptor 가 `(String, int, ...)` | 구현 세부 | **JLS §8.9.2 가 명시적으로 "not specified as implicitly declared"** 라고 못박는다 |
| enum 상수의 인스턴스가 **하나뿐**이고 `==` 로 비교해도 된다 | **언어 보장** | JLS §8.9 + §8.9.1 |
| 상수 본문이 **익명 하위 클래스**이고 enum 이 `sealed`/`final` 로 갈린다 | **언어 보장** | JLS §8.9 · §8.9.1 |
| `Ex$Op$1` 이라는 **클래스 이름**, `PermittedSubclasses` 에 적힌 **순서** | 구현 세부 | 이름 규칙은 컴파일러의 것이다 |
| `switch` 가 상수 이름을 **한정 없이** 받는다 (21+ 는 한정도 허용) | **언어 보장** | JLS §14.11.1 + `--release` 별 실행 결과 |
| `$SwitchMap$Day` 합성 클래스, `lookupswitch`, `NoSuchFieldError` 예외 테이블 | 구현 세부 | javac 의 컴파일 전략이다. **다른 컴파일러는 다르게 해도 된다** |
| `EnumSet` 이 **비트 벡터**, `EnumMap` 이 **배열** | **javadoc 이 명시** | 두 클래스의 javadoc 첫 문단 |
| `RegularEnumSet` / `JumboEnumSet` 이라는 **이름과 64 경계** | 구현 세부 | `java.util` 패키지 전용 클래스. javadoc 에 없다 |
| `EnumSet`/`EnumMap` 의 **순회가 선언 순서** | **javadoc 이 보장** | "traverses the elements in their natural order (the order in which the enum constants are declared)" |
| `EnumSet`/`EnumMap` 이 **더 빠르다** | **보장 아님** | javadoc 자신이 "likely (**though not guaranteed**)" 라고 쓴다 |

> **주 — `values()` 의 "매번 새 배열"** : JLS §8.9.3 의 문장은 "선언 순서대로 상수를 담은 배열을 돌려준다"까지이고, **"매번 새 배열"이라는 말은 그 절에 없다.**\
> 다만 그 조항이 **호출 때마다** 성립하려면 호출자가 망가뜨릴 수 없어야 하고, javac 는 `$VALUES.clone()` 으로 그렇게 구현한다.\
> 그러니 외울 것은 **"`clone()` 을 쓴다"가 아니라 "내가 받은 배열을 고쳐도 다음 호출은 멀쩡하다, 그래서 부를 때마다 할당이 있다"** 이다.

## 언제 쓰고 언제 안 쓰나

| 쓸 것 | 안 쓸 것 |
|---|---|
| 값의 **가짓수가 코드에 고정**된 것 → `enum` (상태·요일·통화·모드) | 값이 **런타임·설정·DB 에서 온다** → enum 이 아니라 데이터다 |
| 상수마다 **동작이 다르고 상수가 늘어날 예정** → 상수별 본문 | 분기가 한두 줄이고 늘 일이 없다 → `switch` 나 필드 하나 |
| 상수를 **키·플래그 집합**으로 다룬다 → `EnumSet`/`EnumMap` | 키가 enum 이 아니거나 **상수가 매우 많은데 항목은 몇 개** → `HashMap` |
| 저장·전송·로그에 남길 식별자 → `name()` 또는 **직접 둔 코드 필드** | 저장·전송에 `ordinal()` → 「어디서 틀리나」 1번 |
| 싱글턴이 필요하다 → 상수 하나짜리 `enum` | 상속으로 늘려야 한다 → `sealed` 인터페이스([`../15-sealed-classes/`](../15-sealed-classes/)) |
| 값 묶음이 **식별자 없는 데이터**다 → `record`([`../14-records/`](../14-records/)) | — |

판단 규칙 세 줄.

- **`ordinal()` 은 JVM 안에서만.** 밖으로 나가는 숫자는 내가 직접 정한 필드여야 한다.
- **`values()` 는 루프 밖에서.** 한 번 받아 두거나 `EnumSet` 을 쓴다.
- **상수가 늘 예정이면 `switch` 보다 상수별 본문.** 컴파일러가 빠뜨린 자리를 잡아 준다.

## 핵심 문장

- `enum` 은 `java.lang.Enum<E>` 를 상속한 **진짜 클래스**이고, 상수는 `<clinit>` 이 딱 한 번 만드는 **`public static final` 필드**다 — 그래서 싱글턴이 공짜다.
- 싱글턴을 지키는 잠금은 **넷**이다 — 컴파일 에러(`new` 금지·`private` 생성자) · 리플렉션 차단 · `final clone` · 역직렬화 차단.
- `values()` 는 **호출마다 `$VALUES.clone()`** 이다. 내 배열을 망가뜨려도 원본은 멀쩡한 대신, **부를 때마다 배열 하나를 할당한다.**
- 상수별 본문은 **익명 하위 클래스**를 만들고, 추상 메서드를 두면 **상수를 늘렸을 때 컴파일 에러로 잡힌다** — `switch` 에는 없는 안전망이다.
- `EnumSet` 은 `long` 의 비트, `EnumMap` 은 `ordinal` 인덱스 배열이다 — **해시를 쓰지 않고**, 순회 순서가 **선언 순서로 보장**된다. 속도는 javadoc 도 보장하지 않는다.
- `ordinal()` 을 저장소·프로토콜에 내보내면, 상수 하나가 가운데 끼는 순간 **에러 없이 다른 값으로 읽힌다.**

## 관련 자료

- [`../README.md`](../README.md) — Java 문법·API 주제 목록(이 주제는 13번)
- [`../06-initialization-order/`](../06-initialization-order/) — **선행.** `<clinit>` 이 딱 한 번 돌고 JVM 이 락으로 보호한다는 규칙이 정본이다.\
  **여기는 그 규칙이 enum 싱글턴이 되는 부분만** 쓴다
- [`../12-nested-classes/`](../12-nested-classes/) — **익명 클래스 일반이 정본.** 여기는 **상수별 본문이 그 익명 클래스로 컴파일된다는 사실과 그 결과**(클래스 파일 증가·바깥에서 안 보이는 메서드)만
- [`../15-sealed-classes/`](../15-sealed-classes/) — **`sealed`/`permits` 가 정본.** 여기는 **상수 본문이 있는 enum 에 `PermittedSubclasses` 가 붙더라는 관측**까지
- [`../14-records/`](../14-records/) — 같은 "javac 가 멤버를 만들어 주는" 갈래. **고정된 인스턴스 집합은 enum, 값 묶음은 record** 로 갈린다
- [**11번 주제**](../11-interfaces-default-methods/)(인터페이스 — `default`/`static`/`private` 메서드) — **인터페이스 규칙이 정본.** 여기는 **enum 이 상속은 못 하고 구현은 된다**는 경계만. 동적 디스패치는 [**09번 주제**](../09-inheritance-overriding/)(상속과 오버라이딩) 가 정본이고, 상수별 본문의 호출이 그 규칙을 그대로 탄다
- [`../27-equals-hashcode-contract/`](../27-equals-hashcode-contract/) — `equals`/`hashCode` 계약이 정본. **enum 은 `Enum.equals` 가 `final` 이라 계약을 깰 수가 없다**는 것이 이 주제 쪽 결론
- [`../../../../../data-structure/05-hashmap/`](../../../../../data-structure/05-hashmap/) — **해시 자료구조의 원리가 정본**(버킷·충돌·리사이즈). 여기는 **`EnumMap` 이 해시를 아예 안 쓴다는 사실과 그 결과**(순회 순서 보장·`null` 키 금지·크기가 상수 수에 비례)만 다룬다.\
  집합·맵 일반은 [`../../../../../data-structure/`](../../../../../data-structure/)
- [`../../../../oop-basics/`](../../../../oop-basics/) — **다형성 개념이 정본.** 여기는 **enum 상수별 본문이 그것을 어떻게 강제하나**(추상 메서드 + 모든 상수 구현 의무)만
- [`../../../../../engineering/design-patterns-gof/`](../../../../../engineering/design-patterns-gof/) — 싱글턴·전략 패턴이 정본. **enum 이 그 둘을 언어 기능으로 흡수한 자리**가 이 주제다
- [`../../../../../../history/java/java-5.md`](../../../../../../history/java/java-5.md) — **언제·왜 들어왔나**(Java 5, JSR 201). **여기는 어떻게 쓰고 무엇을 못 하나**
- [`../../../../../../history/java/java-21.md`](../../../../../../history/java/java-21.md) — JEP 441 의 연혁. **여기는 그 변화가 `case` 라벨에서 실제로 무엇을 바꿨나**(한정 이름)만
- [`../../언어-특성/README.md`](../../언어-특성/README.md) — 클래스로더·GC·메모리 모델. **거기는 JVM 층**, 여기는 문법과 API 층이다 — 재서술하지 않는다
- 목록의 **21번 주제**(`switch` 문과 식 — 화살표·`yield`·완결성)와 **23번 주제**(`switch` 패턴 매칭 — `case null`·`when` 가드)가 `switch` 쪽 정본이다

## 용어 풀이

- **enum 상수(enum constant)** — `enum` 본문에 이름으로 적은 그 타입의 인스턴스. `public static final` 필드로 컴파일된다.
- **`ordinal`** — 상수가 선언에서 몇 번째인지(0부터). 선언 순서를 바꾸면 값이 바뀐다.
- **`name()`** — 선언한 식별자 문자열. `final` 이라 바꿀 수 없다. `toString()` 은 바꿀 수 있다.
- **상수별 본문(constant-specific class body)** — 상수 이름 뒤에 `{ ... }` 를 붙여 그 상수만의 구현을 주는 것. 익명 하위 클래스가 만들어진다.
- **`values()` / `valueOf(String)`** — javac 가 자동으로 넣어 주는 두 `static` 메서드. 전자는 선언 순서의 배열, 후자는 이름으로 상수 찾기.
- **방어 복사(defensive copy)** — 내부 배열·컬렉션을 그대로 주지 않고 복사본을 주는 것. `values()` 가 `clone()` 하는 이유다.
- **`$VALUES` / `$values()`** — javac 가 상수 배열을 보관·생성하려고 만든 숨은 멤버. **구현 세부다.**
- **`$SwitchMap`** — 다른 컴파일 단위의 enum 을 `switch` 할 때 javac 가 만드는 합성 `int[]`. ordinal 을 호출부에 박지 않으려는 장치다. **구현 세부다.**
- **비트 벡터(bit vector)** — 원소 하나를 비트 한 자리로 표현해 집합을 정수에 담는 것. `RegularEnumSet` 의 `long elements` 가 그것이다.
- **`RegularEnumSet` / `JumboEnumSet`** — 상수 64개 이하/초과일 때 `EnumSet` 이 고르는 두 구현. `java.util` 패키지 전용이다.
- **암묵 선언(implicitly declared)** —\
  JLS 가 "컴파일러가 반드시 만들어 넣는다"고 정한 멤버. `values()`·`valueOf` 와 상수 필드가 그것이고, **생성자의 `String`·`int` 파라미터는 아니다.**
- **`getDeclaringClass()`** — 이 상수가 **어느 enum 타입 소속**인지 돌려주는 메서드. 상수 본문이 있으면 `getClass()` 와 달라진다.
- **`<clinit>`** — 클래스 초기화 메서드. enum 상수 객체를 만드는 코드가 전부 여기 들어간다. 정본은 [**06번 주제**](../06-initialization-order/).

## 더 들어가면

- **`EnumSet` 은 `new` 로 만들 수 없다** — `noneOf`·`allOf`·`of`·`range`·`complementOf`·`copyOf` 같은 **정적 팩토리**만 공개한다.\
  그래야 상수 개수에 따라 `RegularEnumSet`/`JumboEnumSet` 을 바꿔 끼울 수 있다 — "생성자 대신 정적 팩토리"의 교과서적 사례다.
- **`Enum.compareTo` 는 ordinal 의 차이**다. `src.zip` 의 본문이 `return self.ordinal - other.ordinal;` 한 줄이고, 다른 enum 타입끼리면 `ClassCastException` 을 던진다.\
  실행으로도 확인했다 (`Ex.java (13-h)`) — `MON.compareTo(SUN)` 이 `-6`, `SUN.compareTo(MON)` 이 `6`.\
  즉 **`TreeSet<Day>` 의 정렬 순서도 선언 순서**다. 정렬 계약 쪽은 목록의 **28번 주제**가 정본이다.
- **`enum` 은 제네릭이 될 수 없다** — `EnumDeclaration` 문법에 `TypeParameters` 자리가 아예 없다(JLS §8.9). 상수마다 다른 타입을 다뤄야 하면 `sealed` 계층을 쓴다.
