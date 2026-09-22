# java/syntax/13 — `enum` 클래스: 상수별 본문·`EnumSet`/`EnumMap` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·에러·역어셈블은 **Temurin JDK 21.0.5 에서 실제로 돌려 얻은 것**이다.\
> `case` 라벨의 한정 이름만 `--release 17 · 20 · 21` 과 Temurin **JDK 25.0.1** 넷에서 비교했다.\
> 긴 역어셈블 출력은 [2-summary.md](2-summary.md) 「동작 방식」에 전문이 있고, 여기서는 **판정에 쓰이는 줄**만 다시 옮긴다.\
> JLS 인용은 [SE 21 §8.9](https://docs.oracle.com/javase/specs/jls/se21/html/jls-8.html) · [§14.11.1](https://docs.oracle.com/javase/specs/jls/se21/html/jls-14.html) 에서, 구현 코드 인용은 **JDK 21.0.5 의 `lib/src.zip`** 에서 복사했다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. enum 상수 셋을 쓰면 클래스 파일에 무엇이 생기는가

**출력** (`javap -p Ex$Planet`, `Ex.java (13-a)`)

```text
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

**왜 그런가**

내가 쓰지 않은 것이 여섯 개 보인다.

| 멤버 | 무엇인가 | 언어 보장인가 |
|---|---|---|
| `public static final` 상수 필드 셋 | 상수 하나 = 필드 하나 | **보장**(JLS §8.9.3) |
| `values()` | 선언 순서의 배열 | **보장**(§8.9.3) |
| `valueOf(String)` | 이름으로 상수 찾기 | **보장**(§8.9.3) |
| `$VALUES` | 상수 배열을 보관하는 숨은 필드 | 구현 세부 |
| `$values()` | 그 배열을 만드는 합성 메서드 | 구현 세부 |
| `static {}` = `<clinit>` | 상수 객체를 만드는 코드 | 있다는 것은 필연, 이름은 JVM 규약 |

- 상위 클래스는 **`java.lang.Enum<Ex$Planet>`** — 자기 자신을 타입 인자로 받는다.\
  JLS §8.9: "The direct superclass type of an enum class `E` is `Enum<E>`. An enum declaration does not have an `extends` clause, so it is not possible to explicitly declare a direct superclass type, even `Enum<E>`."
- 클래스 선언은 **`final`** 이다. 상수 본문이 하나도 없기 때문이다.\
  JLS §8.9: "An enum class is implicitly `final` if its declaration contains no enum constants that have a class body."
- `<clinit>` 은 상수 하나당 **`new` → `invokespecial <init>` → `putstatic`** 을 정확히 한 번씩 한다.

```text
javap -c -p Ex$Planet 의 static {} — MERCURY 한 상수분과 끝부분 (전문은 2-summary.md 동작 방식 (1))

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

- 그리고 마지막에 `$values()` 의 결과를 `$VALUES` 에 넣는다.
- **이 코드가 도는 곳이 `<clinit>` 이라는 것이 이 주제의 핵심**이다.\
  클래스 초기화는 프로세스당 **딱 한 번**이고 **JVM 이 락으로 보호**한다([**06번 주제**](../06-initialization-order/)).\
  그래서 상수 객체는 한 번만 만들어지고, 두 스레드가 동시에 들어와도 중복이 없다 — **싱글턴이 공짜인 1차 근거**다.

**descriptor 의 차이**

```text
javap -v -p Ex$Planet — 해당 부분 그대로

  private Ex$Planet(double, double);
    descriptor: (Ljava/lang/String;IDD)V
    flags: (0x0002) ACC_PRIVATE
    Code:
```

- 소스는 `(double, double)` 인데 클래스 파일은 **`(String, int, double, double)`** 이다.
- 앞의 둘이 `Enum` 의 `name` 과 `ordinal` 이고, `<clinit>` 의 `ldc "MERCURY"` · `iconst_0` 이 그 인자다.
- **이것은 보장이 아니다.** JLS §8.9.2 가 직접 못박는다 —\
  "In practice, a compiler is likely to mirror the `Enum` class by declaring `String` and `int` parameters ... However, these parameters are **not specified as "implicitly declared"** because different compilers do not need to agree on the form of the default constructor."
- 실무 함의: **리플렉션으로 enum 생성자를 다루는 코드는 컴파일러에 의존한다.** 어차피 7번에서 보듯 막혀 있다.

### 2. `values()` 로 받은 배열을 망가뜨리면

**출력** (`Ex.java (13-a)`, JDK 21.0.5)

```text
--- values() 가 같은 배열인가 ---
values() == values() ? false
망가뜨린 뒤 values()[0] = MERCURY
내가 들고 있던 배열[0] = null
```

**왜 그런가**

```text
javap -c -p Ex$Planet — values() 전체

  public static Ex$Planet[] values();
    Code:
       0: getstatic     #13                 // Field $VALUES:[LEx$Planet;
       3: invokevirtual #17                 // Method "[LEx$Planet;".clone:()Ljava/lang/Object;
       6: checkcast     #18                 // class "[LEx$Planet;"
       9: areturn
```

- 명령은 **넷**이고, 결정적인 것은 가운데의 **`invokevirtual clone()`** 이다.
- 진짜 배열 `$VALUES` 를 꺼내 **복사한 뒤** 돌려준다 — 그래서 두 번 부르면 서로 다른 배열이고(`false`), 내 배열을 망가뜨려도 원본은 멀쩡하다.
- 배열은 Java 에서 불변으로 만들 수 없다. **복사본을 주는 것 말고는 내부를 지킬 방법이 없다.**

**대가**

- **호출마다 배열 하나가 할당된다.** 상수 n 개면 n 칸짜리 참조 배열이다.
- `for (int i = 0; i < Day.values().length; i++) { ... Day.values()[i] ... }` 는 상수 7개일 때 배열을 **15개** 만든다.
- 에러도 경고도 없고, 프로파일러 없이는 안 보인다.

**방어책 둘** (`Ex.java (13-h)` 로 확인)

```text
values() == values()   ? false
VALUES  == VALUES      ? true
VALUES  == Day.values()? false
EnumSet.allOf(Day.class) = [MON, TUE, WED, THU, FRI, SAT, SUN]
```

1. `private static final Day[] VALUES = values();` — **한 번만** 받아 둔다. 단 **밖으로 내주면 안 된다**(내주는 순간 방어가 무너진다).
2. 순회라면 `EnumSet.allOf(Day.class)` — `EnumSet` 은 내부 상수 배열을 `getUniverse` → `SharedSecrets.getJavaLangAccess().getEnumConstantsShared(...)` 로 **공유해서** 받으므로 복사가 없다(`EnumSet.java` 인용).

### 3. 상수별 본문을 쓰면 `getClass()` 가 무엇을 돌려주는가

**출력** (`Ex.java (13-b)`, JDK 21.0.5)

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

**왜 그런가**

- `getClass()` 는 **`Ex$Op$1`·`Ex$Op$2`·`Ex$Op$3`** — 상수마다 다르다.\
  JLS §8.9.1: "The optional class body of an enum constant **implicitly declares an anonymous class** (§15.9.5) that (i) is a direct subclass of the immediately enclosing enum class, and (ii) is `final`."
- `getDeclaringClass()` 는 셋 다 **`Ex$Op`** 다 — "내가 어느 enum 소속인가"를 묻는 메서드가 따로 있는 이유가 이것이다.\
  **enum 타입을 비교할 때 `getClass()` 를 쓰면 틀린다.**
- `Op.class` 는 **`abstract`**(추상 메서드가 있으므로), `Plain.class` 는 **`final`**(상수 본문이 없으므로)이다.
- 클래스 파일은 **여섯 개** 생긴다 — `Ex`, `Ex$Op`, `Ex$Op$1~3`, `Ex$Plain`.\
  상수가 30개면 클래스 파일이 31개다. 이것이 상수별 본문의 **비용**이다.

**`javap -v` 에만 나타나는 속성**

```text
javap -v -p Ex$Op — 헤더와 PermittedSubclasses 부분 그대로

abstract class Ex$Op extends java.lang.Enum<Ex$Op>
  flags: (0x4420) ACC_SUPER, ACC_ABSTRACT, ACC_ENUM
...
PermittedSubclasses:
  Ex$Op$1
  Ex$Op$2
  Ex$Op$3
```

```text
javap -v -p Ex$Plain — flags 줄 그대로

  flags: (0x4030) ACC_FINAL, ACC_SUPER, ACC_ENUM
```

- **`PermittedSubclasses`** — 즉 상수 본문이 있는 enum 은 **`sealed`** 다.\
  JLS §8.9: "An enum class `E` is implicitly **sealed** if its declaration contains at least one enum constant that has a class body. The permitted direct subclasses of `E` are the anonymous classes implicitly declared by the enum constants that have a class body."
- `sealed`/`permits` 자체는 [`../15-sealed-classes/`](../15-sealed-classes/) 가 정본이다.\
  여기서 외울 것은 **"enum 은 늘 `final` 아니면 `sealed` 다 — 둘 다 바깥에서 못 늘린다"** 이다.
- 상수별 본문의 진짜 이득은 다형성이 아니라 **컴파일 에러**다.\
  JLS §8.9.2: 추상 메서드가 있으면 "all of `E` 's enum constants have class bodies that provide concrete implementations of `m`" 여야 한다 — 상수를 하나 추가하면 **그 자리가 컴파일 에러**가 된다. `switch` 는 그것을 못 잡는다.

### 4. `EnumSet`·`EnumMap` 과 `HashSet`·`HashMap` 의 출력이 갈린다

**출력** (`Ex.java (13-c)`, JDK 21.0.5)

```text
--- EnumSet 은 선언 순서로 순회한다 ---
EnumSet.of(SUN, SAT) = [SAT, SUN]
HashSet 같은 내용     = [SUN, SAT]
--- EnumMap 도 선언 순서 ---
EnumMap  = {MON=2, FRI=3, SUN=1}
HashMap  = {SUN=1, FRI=3, MON=2}
--- null 키 ---
EnumMap.put(null,..) -> java.lang.NullPointerException: Cannot invoke "Object.getClass()" because "key" is null
HashMap.put(null,..) -> ok, 9
```

**왜 그런가**

- `of(SUN, SAT)` 라고 **거꾸로** 넣었는데 `[SAT, SUN]` 으로 나왔고, `SUN → MON → FRI` 순으로 넣은 `EnumMap` 이 `{MON, FRI, SUN}` 으로 나왔다 — **선언 순서로 되돌아온다.**
- 마지막 줄은 **NPE** 다. `EnumMap.put` 의 첫 줄 `typeCheck(key)` 안의 `key.getClass()` 에서 터지므로 메시지가 저렇게 나온다.\
  `HashMap` 이었다면 **통과**한다(`ok, 9`).

**보장인가 우연인가 — 보장이다**

> **`EnumSet` javadoc** — "The iterator returned by the `iterator` method traverses the elements in their *natural order* (**the order in which the enum constants are declared**)."

> **`EnumMap` javadoc** — "Enum maps are maintained in the *natural order* of their keys (**the order in which the enum constants are declared**). This is reflected in the iterators returned by the collections views."

- 반대로 `HashSet`/`HashMap` 의 순서는 **계약이 아니다.** 같은 JDK 에서 같은 순서가 나왔다고 보장이 되지 않는다.
- `null` 금지도 javadoc 이 명시한다 — `EnumMap` 쪽 원문이 "Null keys are not permitted. ... **Null values are permitted.**" 다.\
  **키만 막고 값은 허용**한다는 비대칭까지 계약이다.

**구조적 이유 — 그리고 말하면 안 되는 것**

```text
java/util/EnumMap.java — put/get 의 핵심 줄 (JDK 21.0.5 src.zip · 전문은 2-summary.md 동작 방식 (7))

        int index = key.ordinal();            // put
        return (isValidKey(key) ? unmaskNull(vals[((Enum<?>)key).ordinal()]) : null);   // get
```

- `ordinal()` 을 **배열 인덱스로 직접** 쓴다 — 해시 계산도, 버킷 탐색도, `equals` 호출도 없다.\
  **`EnumMap` 은 해시를 아예 쓰지 않는다.** 해시 자료구조 원리는 [`../../../../../data-structure/05-hashmap/`](../../../../../data-structure/05-hashmap/) 가 정본이다.
- ★ **말하면 안 되는 것: "몇 배 빠르다" 같은 수치.** 이 문서는 측정하지 않았다.\
  javadoc 자신이 이렇게만 쓴다 —\
    "All basic operations execute in constant time. They are **likely (though not guaranteed)** to be faster than their `HashMap` counterparts."
- 한계도 구조에서 나온다 — `vals` 는 **상수 개수만큼** 잡힌다. 상수 1,000개에 항목 3개면 997칸이 `null` 이다.

### 5. `ordinal()` 로 저장한 값이 조용히 바뀐다

**출력** (`Ex.java (13-f)`, JDK 21.0.5)

어제 (`enum Status { NEW, PAID, SHIPPED }`):

```text
어제 저장한 값 = 2 (SHIPPED)
오늘 그 값을 되읽으면 = SHIPPED
이름으로 저장했다면  = SHIPPED
```

오늘 (`enum Status { NEW, CANCELLED, PAID, SHIPPED }` — 가운데에 하나를 끼웠다):

```text
오늘 그 값을 되읽으면 = PAID
이름으로 저장했다면  = SHIPPED
```

**왜 그런가**

`NEW·PAID·SHIPPED` 였던 `0·1·2` 가 `NEW·CANCELLED·PAID` 로 밀렸다 — 저장해 둔 `2` 가 가리키는 칸이 바뀐 것이다.

- `values()[2]` 는 **여전히 유효한 상수**를 돌려준다 — 다른 상수일 뿐이다.
- **예외도 경고도 로그도 없다.** 배송 완료 주문이 결제 완료로 읽히고, 그것이 어디서 시작됐는지 추적할 단서가 없다.
- 이름으로 저장했으면 그대로 `SHIPPED` 다.\
  이름을 **지우거나 바꾸면** 그때는 `IllegalArgumentException: No enum constant ...` 로 **터진다** — 조용히 틀리는 것보다 낫다.

**javadoc 이 직접 경고한다**

> **`Enum.ordinal()` javadoc** (JDK 21.0.5 src.zip) — "Returns the ordinal of this enumeration constant (its position in its enum declaration, where the initial constant is assigned an ordinal of zero). **Most programmers will have no use for this method.** It is designed for use by sophisticated enum-based data structures, such as `EnumSet` and `EnumMap`."

**그런데 `EnumSet`/`EnumMap` 은 왜 안전한가**

- 그것들이 쓰는 `ordinal` 은 **같은 JVM, 같은 클래스 파일 안에서만** 산다.\
  객체가 살아 있는 동안 ordinal 은 안 바뀐다.
- 위험한 것은 **ordinal 을 프로세스 밖으로 내보내는 것**이다 — DB·파일·JSON·캐시·다른 서비스.\
  그 숫자는 **다음 배포의 클래스 파일**과 만나게 된다.
- 그래서 규칙은 "`ordinal()` 을 쓰지 마라"가 아니라 **"`ordinal()` 을 내보내지 마라"** 다.\
  숫자 코드가 꼭 필요하면 `SHIPPED(30)` 처럼 **내가 정한 필드**를 둔다.

### 6. 같은 파일이냐 다른 파일이냐로 `switch` 의 컴파일 결과가 갈린다

**출력** — `javap -c -p Ex` 의 `kind()` 첫머리 (전문은 2-summary.md 동작 방식 (5))

```text
(A) 같은 파일 (13-d)                        (B) 다른 파일 (13-e)
       0: aload_0                              0: getstatic  Ex$1.$SwitchMap$Day:[I
       1: invokevirtual Ex$Day.ordinal:()I     3: aload_0
       4: lookupswitch { 2: 32                 4: invokevirtual Day.ordinal:()I
                         3: 32                 7: iaload
                   default: 35 }               8: lookupswitch { 1: 36
                                                                 2: 36
                                                           default: 39 }
```

**왜 그런가**

- (A) 는 `ordinal()` 결과로 **바로** `lookupswitch` 한다. `case SAT:`·`case SUN:` 이 숫자 **`2`·`3`** 이 되어 **호출부에 박혔다.**
- (B) 는 그 사이에 **`Ex$1.$SwitchMap$Day` 라는 `int[]`** 를 한 번 거친다(`iaload`). 박힌 숫자는 `1`·`2` 로, **ordinal 이 아니라 스위치 내부 번호**다.

**(B) 에서 더 생기는 클래스**

```text
javap -c -p Ex$1 — SAT 매핑 한 개분과 예외 테이블 (전문은 2-summary.md 동작 방식 (5))

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
      ...                                   // SUN 도 같은 형태로 2 를 넣는다
    Exception table:
       from    to  target type
           9    20    23   Class java/lang/NoSuchFieldError
          24    35    38   Class java/lang/NoSuchFieldError
}
```

- 이 클래스의 `<clinit>` 은 **런타임에** `Day.SAT.ordinal()` 을 물어보고 그 칸에 `1` 을 넣는다.\
  "`SAT` 의 현재 순번이 몇이든 내 스위치 번호 1로 매핑한다"는 표다.
- **예외 테이블이 있는 이유**: 각 매핑이 `NoSuchFieldError` 로 감싸여 있다.\
  `Day` 에서 상수가 **사라져도** 그 한 칸만 건너뛰고 나머지 매핑은 살아남는다 — `<clinit>` 전체가 `ExceptionInInitializerError` 로 죽지 않게 하는 장치다.
- 즉 `$SwitchMap` 은 **바이너리 호환성**을 위한 것이다.

**`Day` 의 순서만 바꿔 `Day` 만 다시 컴파일하면**

(B) 실행 결과 — `Day` 를 `{SAT, SUN, MON, TUE}` 로 바꾸고 **`Day` 만** 다시 컴파일한 뒤 `Ex` 는 그대로:

```text
SAT(ordinal=0) -> 쉬는 날
SUN(ordinal=1) -> 쉬는 날
MON(ordinal=2) -> 일하는 날
TUE(ordinal=3) -> 일하는 날
```

- `SAT` 의 ordinal 이 `2` 에서 `0` 으로 바뀌었는데 **결과가 옳다.** `$SwitchMap` 이 런타임에 다시 채워졌기 때문이다.
- (A) 는 애초에 **한 파일이라 따로 컴파일할 수가 없다** — 고치면 같이 컴파일되고, 박힌 숫자도 같이 갱신된다.\
  위험한 조합은 "**별도 파일인데 옛날 컴파일 전략처럼 ordinal 이 박혔다고 믿는 것**"이 아니라, 반대로 **ordinal 이 프로세스 밖에 저장된 경우**다(5번).
- ★ **여기까지가 관측이다.** `$SwitchMap$Day` 라는 이름도, 합성 클래스를 쓴다는 선택도 **javac 의 전략**이지 언어 보장이 아니다. 다른 컴파일러는 다르게 해도 된다.

### 7. enum 이 싱글턴인 것을 무엇이 보장하는가

**길은 넷이고 전부 막혀 있다.**

JLS §8.9 가 **컴파일 에러 하나 + "three further mechanisms" 셋**을 직접 나열한다 — 원문 전문은 2-summary.md 동작 방식 (3)에 있다.

네 문을 그린 도식은 2-summary.md 동작 방식 (3)에 있다 — 남는 길은 `<clinit>` 하나뿐이고, 그것은 딱 한 번 돈다.

**컴파일러가 막는 것 / 런타임이 막는 것**

- **(1)만 컴파일러**다. 소스에 `new` 를 쓰는 순간 에러다.\
  생성자도 `private` 이다(§8.9.2: "a constructor declaration with no access modifiers is `private`").
- **(2)(3)(4)는 런타임**이다. 소스를 우회해 들어오는 길이므로 컴파일러가 볼 수 없다.
- (3)(4)는 엄밀히는 **`Enum` 의 `final` 선언**이 막는 것이라 검사 비용이 없다.

**리플렉션 메시지** (`Ex.java (13-b)`)

```text
--- 싱글턴이 공짜인 이유 ---
리플렉션 생성 -> java.lang.IllegalArgumentException: Cannot reflectively create enum objects
Enum.clone() 선언 = protected final + throws CloneNotSupportedException
```

`src.zip` 에 (3)(4)가 그대로 있다.

```text
java/lang/Enum.java — 두 선언 (JDK 21.0.5 src.zip · javadoc 전문은 2-summary.md 동작 방식 (3))

    protected final Object clone() throws CloneNotSupportedException {
    private void readObject(...) { throw new InvalidObjectException("can't deserialize enum"); }
```

**06번 주제의 어느 규칙에 기대는가**

- **`<clinit>` 은 클래스당 딱 한 번 돌고, JVM 이 락으로 보호한다.**
- 1번에서 본 대로 상수 객체를 만드는 `new`/`putstatic` 이 전부 그 안에 있다.\
  따라서 **락도, 이중 검사도, `volatile` 도 내가 쓸 필요가 없다.**
- 06번의 `static` 홀더 관용구가 "락 없는 지연 싱글턴"이었다면, enum 은 **그 관용구를 언어 기능으로 굳힌 것**이다.
- 덤으로 `==` 비교가 안전해진다 — JLS §8.9.1:\
  "Because there is only one instance of each enum constant, it is permitted to use the `==` operator in place of the `equals` method ...". `Enum.equals` 는 `final` 이라 **계약을 깰 수도 없다**([`../27-equals-hashcode-contract/`](../27-equals-hashcode-contract/)).

### 8. enum 생성자에서 그 enum 의 `static` 필드를 건드리면

**컴파일되지 않는다** (`Ex.java (13-err3)`)

```text
err3/Ex.java:6: error: illegal reference to static field from initializer
        Code(String tag) { BY_TAG.put(tag, this); }
                           ^
1 error
```

**왜 그런가**

- 컴파일이 됐다면 **`NullPointerException`** 이 났을 것이다.
- 1번에서 본 `<clinit>` 의 순서 때문이다 — **상수 객체를 만드는 코드가 맨 앞**이고, 그 뒤에 내가 선언한 `static` 필드 초기화가 온다(`<clinit>` 은 소스 순서대로 — [**06번 주제**](../06-initialization-order/)).
- 즉 `Code("a")` 가 도는 시점에 `BY_TAG` 는 아직 **`null`** 이다.

```text
<clinit> 안의 시간 축

  1  new Code("a") -> 생성자 본문에서 BY_TAG.put(...)   <- BY_TAG 는 아직 null
  2  new Code("b")
  3  BY_TAG = new HashMap<>()                          <- 이제서야 만들어진다
```

- JLS 도 같은 설명을 붙인다(§8.9.2 Example 8.9.2-2):\
  "Static initialization of this enum would throw a `NullPointerException` because the static variable `colorMap` is uninitialized when the constructors for the enum constants run. The restriction above ensures that such code cannot be compiled."

**예외 — 허용되는 경우**

- JLS §8.9.2: "... **unless the field is a constant variable** (§4.12.4)."
- 즉 `static final int MAX = 10;` 처럼 **상수 변수**(기본형·`String` + 상수 식)는 생성자에서 읽어도 된다.\
  컴파일 타임에 값이 박히므로 초기화 순서와 무관하기 때문이다 — 이 개념의 정본도 [**06번 주제**](../06-initialization-order/)다.

**올바른 형태** — 생성자에서 넣지 말고 **`static` 블록에서 `values()` 를 돌며** 채운다(코드는 2-summary.md 「어디서 틀리나」 3번).

- `static` 블록은 **상수 생성 뒤**에 돈다. JLS 가 제시하는 고침도 이 형태다.
- 여기서 `values()` 를 한 번만 부르는 것도 맞다(2번).

### 9. `case Day.SAT:` 는 되는가

**출력** (`Ex.java (13-err4)` — 넷을 실제로 돌렸다)

```text
--- release 17
err4/Ex.java:5: error: an enum switch case label must be the unqualified name of an enumeration constant
        switch (d) { case Day.SAT: System.out.println("주말"); break; default: break; }
                             ^
1 error
--- release 20
err4/Ex.java:5: error: an enum switch case label must be the unqualified name of an enumeration constant
        switch (d) { case Day.SAT: System.out.println("주말"); break; default: break; }
                             ^
1 error
--- release 21
주말
--- JDK 25.0.1 기본
주말
```

**왜 그런가**

- `--release 17`·`--release 20` 은 **컴파일 에러**, `--release 21` 과 JDK 25 는 **통과**한다.
- 에러 메시지가 규칙을 그대로 말한다 — "an enum switch case label must be the **unqualified** name of an enumeration constant".
- 바뀐 계기는 **21 의 JEP 441**(switch 패턴 매칭 정식화)이다.\
  연혁은 [`../../../../../../history/java/java-21.md`](../../../../../../history/java/java-21.md) 가 정본이다.
- JLS SE 21 §14.11.1 의 문장에는 **`unqualified` 라는 한정이 없다**:

> Every case constant must be either a constant expression (§15.29), or **the name of an enum constant** (§8.9.1), otherwise a compile-time error occurs.

**21 → 17 로 되돌리면**

- **그 자리가 컴파일 에러로 깨진다.** 반대 방향(17 코드를 21 에서 컴파일)은 안전하다.
- 실무 규칙: 라이브러리처럼 **낮은 버전도 지원해야 하는 코드에서는 한정 이름을 쓰지 않는다.**\
  IDE 가 자동으로 한정 이름을 붙여 주는 경우가 있으니 주의한다.
- 참고 — 21 부터는 모든 상수를 `case` 로 덮으면 `default` 를 안 써도 된다(§14.11.1.1:\
  "A `default` label is permitted, but not required, in the case where the names of all the enum constants appear as case constants"). 그쪽 정본은 [**21번 주제**](../21-switch-statement-and-expression/)·**23번 주제**다.

### 10. `switch` 문에 `null` 을 넣으면

**출력** (`Ex.java (13-err5)`, JDK 21.0.5 — `default:` 가 있는 옛 `switch` 문)

```text
Exception in thread "main" java.lang.NullPointerException: Cannot invoke "Ex$Day.ordinal()" because "<local1>" is null
	at Ex.main(Ex.java:5)
```

**왜 그런가**

- **`default:` 가 있어도 안 잡힌다.**
- 예외 메시지가 **`ordinal()`** 을 지목한다 — 6번에서 본 그 `invokevirtual ordinal()` 이다.\
  즉 **분기를 고르기도 전에** selector 를 읽다가 터진 것이다.\
  `default` 는 "분기를 고른 뒤 아무 `case` 도 안 맞을 때"의 자리이지, selector 자체가 `null` 일 때의 자리가 아니다.
**21 부터**

- `case null` 을 쓸 수 있다. JLS SE 21 §14.11.1 의 `SwitchLabel` 문법에 `case null [, default]` 가 들어 있다.
- 정본은 [**23번 주제**](../23-switch-pattern-matching/)(`switch` 패턴 매칭)다.
- 21 미만이면 방어는 하나뿐 — **`switch` 앞에서 `null` 을 걸러 낸다.**

### 11. `toString()` 을 바꿔 놓고 `valueOf()` 로 되읽으면

**출력** (`Ex.java (13-h)`, JDK 21.0.5)

```text
--- name() 과 toString() 은 다른 것이다 ---
Op.PLUS.toString() = +
Op.PLUS.name()     = PLUS
valueOf("+") -> java.lang.IllegalArgumentException: No enum constant Ex.Op.+
valueOf(name())    = PLUS
```

**왜 그런가**

- `name()` 은 **선언한 식별자** `PLUS`, `toString()` 은 내가 오버라이드한 `+` 다.
- `valueOf` 는 **이름으로만** 찾는다. `src.zip` 의 본문이 이렇다.

```text
java/lang/Enum.java — valueOf (JDK 21.0.5 src.zip)

    public static <T extends Enum<T>> T valueOf(Class<T> enumClass,
                                                String name) {
        T result = enumClass.enumConstantDirectory().get(name);
        if (result != null)
            return result;
        if (name == null)
            throw new NullPointerException("Name is null");
        throw new IllegalArgumentException(
            "No enum constant " + enumClass.getCanonicalName() + "." + name);
    }
```

**오버라이드할 수 있는 것**

`src.zip` 의 선언은 `public final String name()` 과 `public String toString()` 이다 — 앞은 `final`, 뒤는 아니다.

- **`toString()` 만 바꿀 수 있다.** 그리고 화면 표시용으로 자주 바꾼다.
- 그래서 규칙 하나가 나온다 — **직렬화·저장·전송의 왕복에는 언제나 `name()`** 을 쓴다.\
  `toString()` 으로 쓰고 `valueOf()` 로 읽으면 왕복이 깨진다.
- 표시 문자열에서 되돌려야 하면 **역인덱스 `Map` 을 `static` 블록에서** 만든다(8번의 고친 코드와 같은 형태).
- 이것은 5번의 `ordinal` 함정과 **같은 가족**이다 — 바깥으로 내보내는 식별자는 **내가 통제하는 것**이어야 한다.

### 12. 어디까지가 언어 보장인가

**JLS 에 나오는 것 / 안 나오는 것**

| 이름 | JLS 에 있나 | 무엇인가 |
|---|---|---|
| `$VALUES` | 없다 | javac 가 상수 배열을 보관하는 숨은 필드 |
| `$values()` | 없다 | 그 배열을 만드는 합성 메서드 |
| `$SwitchMap$Day` | 없다 | 별도 컴파일 단위의 enum switch 용 합성 `int[]` |
| `Ex$Op$1` | 없다 | 상수 본문의 **익명 클래스**는 JLS §8.9.1 에 있지만 **이 이름**은 javac 의 것 |

- 넷 다 **구현 세부**다. `javap` 로 보이는 것을 규칙으로 외우면 안 된다.
- 보장 쪽은 이것들이다 — 상수가 `public static final` 필드라는 것, `values()`/`valueOf` 가 암묵 선언된다는 것, `values()` 가 **선언 순서**라는 것, `ordinal()` 이 선언에서의 위치라는 것, 상수 인스턴스가 하나뿐이라는 것, 상수 본문이 익명 하위 클래스라는 것.

**`values()` 가 "매번 새 배열"이라는 것**

- JLS §8.9.3 의 문장은 여기까지다:

> An implicitly declared method `public static E[] values()`, which returns an array containing the enum constants of `E`, **in the same order as they appear in the body of the declaration of `E`**.

- **"매번 새 배열"이라는 말은 그 절에 없다.**
- 다만 그 조항이 **호출 때마다** 성립하려면 호출자가 망가뜨릴 수 없어야 하고, javac 는 `$VALUES.clone()` 으로 그렇게 구현한다(2번).
- 그러니 외울 것은 `clone()` 이라는 **수단**이 아니라 **성질** 둘이다 —\
  ① 내가 받은 배열을 고쳐도 **다음 호출은 멀쩡하다**, ② 그래서 **부를 때마다 할당이 있다.**

**생성자 descriptor 에 대해 JLS 가 직접 쓴 말**

> In practice, a compiler is likely to mirror the `Enum` class by declaring `String` and `int` parameters in the default constructor of an enum class. However, these parameters are **not specified as "implicitly declared"** because different compilers do not need to agree on the form of the default constructor. (JLS §8.9.2)

- 즉 `(Ljava/lang/String;IDD)V` 는 **javac 가 그렇게 하더라**는 관측이다.

**"더 빠르다"는 보장인가 — 아니다**

> **`EnumSet` javadoc** — "All basic operations execute in constant time. They are **likely (though not guaranteed)** to be much faster than their `HashSet` counterparts."\
> **`EnumMap` javadoc** — 같은 문장을 `HashMap` 에 대고 쓴다("likely (though not guaranteed) to be faster").

- 근거로 쓸 수 있는 것은 **구조**(비트 하나 / 배열 인덱싱 하나, 해시·버킷·`equals` 없음)와 **메모리**(상수 64개까지 `long` 하나)까지다.
- **속도 배수를 적으려면 측정해야 한다.** 이 주제는 측정하지 않았다.
- 덧붙여 `RegularEnumSet`/`JumboEnumSet` 과 **64 경계**도 javadoc 에 없다 — `java.util` 패키지 전용 구현이다.

**enum 을 늘려야 할 때는 어디로 가나**

- enum 은 **항상 `final` 아니면 `sealed`** 라 바깥에서 못 늘린다(3번, 그리고 `Ex.java (13-err1)` 의 `enum classes are not extensible`).
- **가짓수가 고정이 아니면 enum 이 아니다.** 선택지는 둘이다 —\
  타입 계층이 필요하면 [`../15-sealed-classes/`](../15-sealed-classes/), 값 묶음이면 [`../14-records/`](../14-records/).
- 공통 동작만 묶고 싶으면 **여러 enum 이 같은 인터페이스를 구현**한다([**11번 주제**](../11-interfaces-default-methods/)(인터페이스 — `default`/`static`/`private` 메서드)).

---

## 이 주제를 확인한 실행 목록

| 프로그램 | 무엇을 확인했나 | 도구 | 돌린 JDK |
|---|---|---|---|
| `Ex (13-a)` | `values()` 가 매번 새 배열 · 망가뜨려도 원본 무사 · `valueOf` 의 IAE | 실행 | 21.0.5 |
| `Ex (13-a)` | enum 이 `final class ... extends Enum` 으로, 상수가 `public static final` 필드로 컴파일됨 · `values()` = `getstatic $VALUES` + `clone()` + `checkcast` · `<clinit>` 이 상수마다 `new`+`putstatic` · 생성자 descriptor 가 `(Ljava/lang/String;IDD)V` | `javap -p` · `-c -p` · `-v -p` | 21.0.5 |
| `Ex (13-b)` | 상수별 본문 = `Ex$Op$1~3` 익명 하위 클래스 · `Op` 는 abstract, `Plain` 은 final · 리플렉션·`clone` 차단 | 실행 | 21.0.5 |
| `Ex (13-b)` | `Ex$Op` 에 `PermittedSubclasses: Ex$Op$1~3` (= 암묵 sealed) · `Ex$Plain` 은 `ACC_FINAL` | `javap -v -p` | 21.0.5 |
| `Ex (13-c)` | 상수 64 → `RegularEnumSet`, 65 → `JumboEnumSet` · 순회 순서 · `EnumMap` null 키 NPE | 실행 | 21.0.5 |
| `Ex (13-d)` | 같은 컴파일 단위의 enum switch = `ordinal()` + `lookupswitch`(숫자가 박힘) | 실행 + `javap -c -p` | 21.0.5 |
| `Ex (13-e)` | 다른 컴파일 단위 = 합성 `Ex$1.$SwitchMap$Day` + `NoSuchFieldError` 예외 테이블 · `Day` 순서만 바꿔 재컴파일해도 결과가 옳다 | 실행 + `javap -c -p` | 21.0.5 |
| `Ex (13-f)` | 가운데에 상수를 끼우면 `values()[2]` 가 **조용히** 다른 상수가 된다 | 실행 | 21.0.5 |
| `Ex (13-g)` | `RegularEnumSet.elements` 의 비트 벡터를 눈으로 (`--add-opens java.base/java.util=ALL-UNNAMED` 필요) | 실행 + 리플렉션 | 21.0.5 |
| `Ex (13-h)` | `name()` vs 오버라이드한 `toString()` · `VALUES` 캐시 · `EnumSet.allOf` · `compareTo` = ordinal 차 | 실행 | 21.0.5 |
| `Ex (13-err1)` | `cannot inherit from final Base` + `enum classes are not extensible` | `javac` | 21.0.5 |
| `Ex (13-err2)` | 상수 본문의 새 메서드는 바깥에서 `cannot find symbol` | `javac` | 21.0.5 |
| `Ex (13-err3)` | enum 생성자에서 static 필드 → `illegal reference to static field from initializer` | `javac` | 21.0.5 |
| `Ex (13-err4)` | `case Day.SAT:` — 17·20 에러 / 21·25 통과 | `javac --release` | 21.0.5 · 25.0.1 |
| `Ex (13-err5)` | 옛 switch 문 + `null` → NPE(`ordinal()` 을 지목) | 실행 | 21.0.5 |
| `lib/src.zip` | `EnumSet`·`EnumMap` `@since 1.5` · `noneOf` 의 64 분기 · `RegularEnumSet.elements` · `EnumMap.put/get` · `Enum` 의 `clone`/`readObject`/`valueOf`/`name`/`ordinal`/`compareTo` | 소스 직접 읽기 | 21.0.5 |

**구현 의존 항목** — 버전이 오르면 다시 돌려야 하는 것.

- `$VALUES`·`$values()`·`$SwitchMap$Day`·`Ex$Op$1` 이라는 **이름**과 합성 클래스 전략(13-a·13-b·13-e).
- `RegularEnumSet`/`JumboEnumSet` 의 **이름과 64 경계**(13-c), `RegularEnumSet.elements` 필드(13-g).
- `case Day.SAT:` 의 `--release` 별 결과(13-err4) — 새 버전이 나오면 그 버전을 추가한다.
- `javap` 출력 형식 자체(명령 번호·상수 풀 인덱스 `#nn` 은 컴파일마다 달라질 수 있다).
