# java/syntax/23 — `switch` 패턴 매칭 (21): 완결성 · `null` · `when` 가드 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·에러 메시지는 Temurin JDK 에서 **실제로 돌려 얻은 것**이다.\
> 기본은 **21.0.5**이고, 도는 프로그램은 **25.0.1** 에서도 돌렸다.\
> ★ **17.0.13 에서는 컴파일되지 않는다** — 그 에러도 11번에 실었다.\
> 두 판에서 같았던 것은 "같았다"라고 **관찰로** 적었다 — 보장이 아니다.\
> 버전 갈림(`--release 17` / `20` / `21`)은 JDK 21 의 `javac --release` 로 찍었다.\
> 역어셈블은 `javap -c -p` · `javap -v -p` 출력을 그대로 옮겼다.\
> javadoc 인용은 JDK 21.0.5 의 `lib/src.zip` 에서 복사한 것이다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★ 패턴 `switch` 는 무엇으로 컴파일되나

**출력** — `javap -c -p Ex.class` (JDK 21.0.5)

```text
  static java.lang.String name(Ex$Shape);
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
                     1: 64
                     2: 75
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
      58: astore_3
      59: ldc           #24                 // String 원
      61: goto          83
      64: aload_1
      65: checkcast     #26                 // class Ex$Square
      68: astore        4
      70: ldc           #28                 // String 정사각형
      72: goto          83
      75: aload_1
      76: checkcast     #30                 // class Ex$Rect
      79: astore        5
      81: ldc           #32                 // String 직사각형
      83: areturn
```

**출력** — 같은 판의 javac 로 찍은 `enum` `switch` 식([**21번 주제**](../21-switch-statement-and-expression/))

```text
  static java.lang.String kindExpr(Ex$Day);
    Code:
       0: aload_0
       1: invokevirtual #7                  // Method Ex$Day.ordinal:()I
       4: tableswitch   { // 0 to 3
                     0: 46
                     1: 46
                     2: 51
                     3: 51
               default: 36
          }
      36: new           #13                 // class java/lang/MatchException
      ...
```

**출력** — `javap -v -p Ex.class` 의 `BootstrapMethods`

```text
BootstrapMethods:
  0: #154 REF_invokeStatic java/lang/runtime/SwitchBootstraps.typeSwitch:(Ljava/lang/invoke/MethodHandles$Lookup;Ljava/lang/String;Ljava/lang/invoke/MethodType;[Ljava/lang/Object;)Ljava/lang/invoke/CallSite;
    Method arguments:
      #22 Ex$Circle
      #26 Ex$Square
      #30 Ex$Rect
  1: #154 REF_invokeStatic java/lang/runtime/SwitchBootstraps.typeSwitch:(Ljava/lang/invoke/MethodHandles$Lookup;Ljava/lang/String;Ljava/lang/invoke/MethodType;[Ljava/lang/Object;)Ljava/lang/invoke/CallSite;
    Method arguments:
      #37 java/lang/Integer
      #43 java/lang/String
      #52 "[I"
      #55 Ex$Shape
```

**왜 그런가**

- ★ **`if-else` 사슬이 아니다.** 타입 판별이 **`invokedynamic typeSwitch` 한 번**으로 끝난다.\
  그것이 돌려준 `int` 로 평범한 `tableswitch` 를 탄다.
- **명령 이름**은 `invokedynamic`, 부트스트랩 이름은 `typeSwitch`,\
  부트스트랩을 제공하는 클래스는 `java.lang.runtime.SwitchBootstraps` 다.
- **`enum` `switch` 식과 갈리는 자리**는 "번호를 어떻게 얻느냐"다.

| | 옛 `switch`(`enum`) | 패턴 `switch` |
|---|---|---|
| `null` 처리 | 없다 (번호 뽑다 NPE) | `Objects.requireNonNull` 을 앞에 둔다 |
| 번호 얻기 | `ordinal()` — 값에서 계산 | `invokedynamic typeSwitch` — 런타임 호출 |
| 분기 | `tableswitch` | `tableswitch` (같다) |
| 가지 시작 | 바로 본문 | `checkcast` 로 패턴 변수를 만든다 |
| 완결 뒷문 | `MatchException` | `MatchException` (같다) |

- **소스에 `default` 가 없는데 바이트코드에는 있다**(오프셋 44). 하는 일은 **`MatchException` 을 던지는 것뿐**이다.
- `BootstrapMethods` 에는 **`case` 에 적은 타입이 순서대로** 들어간다.\
  0번이 `name()`(`Circle`·`Square`·`Rect`), 1번이 `describe(Object)`(`Integer`·`String`·`"[I"`·`Shape`)다.
- ★ **배열 타입(`"[I"`)도 패턴으로 쓸 수 있다**는 사실이 여기 드러난다.
- ★ 이 목록이 **컴파일 시점에 박힌다**는 것이 9번의 `MatchException` 으로 이어진다.

### 2. 완결성을 만드는 네 가지

**왜 그런가**

| 방법 | 예 | 새 타입이 생기면 |
|---|---|---|
| `default` | `default -> ...` | 조용히 흡수한다 |
| 무조건 패턴 | `case Object o -> ...` | 조용히 흡수한다 |
| **`sealed` 전부 나열** | `case Circle`·`case Square`·`case Rect` | **컴파일 에러** |
| **`enum` 상수 전부 나열** | `case MON`·`case TUE`·... | **컴파일 에러** |

- **빌드를 멈춰 주는 것은 아래 둘**이다. 위 둘은 옛 `switch` 와 같은 안전성밖에 안 준다.
- **`default` 와 `case Object o` 를 같이 쓰면 에러**다 — 둘 다 "나머지 전부"라서 역할이 겹친다.

```text
Ex.java:6: error: switch has both an unconditional pattern and a default label
            default        -> "그 밖";
            ^
```

- ★ **패턴 `switch` 문도 완결해야 한다** — 돌려 확인했다(`Ex.java (23-e10)`).

```text
Ex.java:4: error: the switch statement does not cover all possible input values
        switch (o) {                       // 문(statement) 인데 패턴을 쓴다
        ^
1 error
```

- **옛 `enum` `switch` 문과 다르다.** [**21번 주제**](../21-switch-statement-and-expression/)에서 확인했듯,\
  `enum` 상수를 둘만 적은 `switch` **문**은 아무 말 없이 통과하고 조용히 지나갔다.\
  경계는 「문이냐 식이냐」만이 아니라 **「옛 selector 냐 패턴이냐」**에도 걸려 있다.

### 3. ★ `null` 을 넣으면

**출력** (JDK 21.0.5 — 25.0.1 에서도 같았다)

```text
oldEnumSwitch(null)   -> 던짐: java.lang.NullPointerException: Cannot invoke "Ex$Day.ordinal()" because "<parameter1>" is null
withCaseNull(null)    -> 널이다
withCaseNull("a")     -> 문자열 a
nullWithDefault(null) -> 널이거나 그 밖
noCaseNull(null)      -> 던짐: java.lang.NullPointerException
sealedNoNull(null)    -> 던짐: java.lang.NullPointerException
sealedNoNull(Circle)  -> 원
```

| | `null` 을 넣으면 |
|---|---|
| (a) 옛 `switch` | **NPE** — 메시지에 `ordinal()` 이 박힌다 |
| (b) `case null` 있음 | `"널이다"` |
| (c) `case null, default` | `"널이거나 그 밖"` |
| (d) `default` 만 | **NPE** — 메시지가 없다 |
| (e) `sealed` 완결, `case null` 없음 | **NPE** |

**왜 그런가**

- ★ (d)에 **`default` 가 있는데도 NPE** 인 이유: **`default` 는 `null` 을 받지 않는다.**\
  `case null` 이 없으면 `switch` **입구에서** `Objects.requireNonNull` 이 먼저 튕긴다.\
  검문소(`typeSwitch`)까지 가지도 못한다.

**스택 트레이스 맨 윗줄** (`Ex.java (23-b2)`)

```text
문자열 a
Exception in thread "main" java.lang.NullPointerException
	at java.base/java.util.Objects.requireNonNull(Objects.java:233)
	at Ex.noCaseNull(Ex.java:3)
	at Ex.main(Ex.java:11)
```

- 맨 위가 **`java.util.Objects.requireNonNull`** 이다.
- 옛 `switch` 의 NPE 와 달리 **메시지가 비어 있다.** 로그만 보고 원인을 찾기가 더 어렵다.

**바이트코드가 갈리는 자리** — `case null` 이 **없을 때**

```text
  static java.lang.String noCaseNull(java.lang.Object);
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
      16: lookupswitch  { // 2
                     0: 44
                     1: 58
               default: 74
          }
```

**있을 때**

```text
  static java.lang.String withCaseNull(java.lang.Object);
    Code:
       0: aload_0
       1: astore_1                          <- requireNonNull 이 없다
       2: iconst_0
       3: istore_2
       4: aload_1
       5: iload_2
       6: invokedynamic #19,  0             // InvokeDynamic #0:typeSwitch:(Ljava/lang/Object;I)I
      11: tableswitch   { // -1 to 1        <- 범위가 -1 부터 시작한다
                    -1: 36
                     0: 41
                     1: 55
               default: 71
          }
      36: ldc           #23                 // String 널이다
      38: goto          73
```

- ★ 두 군데가 다르다 — **`requireNonNull` 이 사라지고**, **`tableswitch` 범위가 `-1` 부터** 시작한다.
- `typeSwitch` 는 **`null` 에 `-1`** 을 돌려준다. 그 `-1` 이 `case null` 가지(오프셋 36)로 간다.
- **`case null, String s ->` 처럼 다른 패턴과는 못 묶는다** — 돌려 확인했다(`Ex.java (23-e11)`).

```text
Ex.java:4: error: invalid case label combination
            case null, String s -> "널이거나 문자열";
                       ^
1 error
```

- `default` 와만 묶인다. `default` 는 패턴 변수를 안 만들기 때문이다.

### 4. ★ `case` 의 순서

**출력** — (a) `Object` 를 먼저

```text
Ex.java:6: error: switch has both an unconditional pattern and a default label
            default        -> "그 밖";
            ^
Ex.java:5: error: this case label is dominated by a preceding case label
            case String s  -> "문자열";      // 앞의 Object 가 이미 다 먹었다
                 ^
2 errors
```

**출력** — (b) `sealed` 의 상위를 먼저

```text
Ex.java:8: error: this case label is dominated by a preceding case label
            case Circle c -> "원";
                 ^
1 error
```

**출력** — (c) `default` 뒤에 `case`

```text
Ex.java:6: error: this case label is dominated by a preceding case label
            case Integer i -> "정수";        // default 뒤에 case 를 두면?
                 ^
1 error
```

**왜 그런가**

- (a)는 에러가 **2개** 다. `case Object x` 가 `Object` selector 에 대해 **무조건 패턴**이라\
  `default` 와 역할이 겹치는 것이 하나, `String` 이 도달 불가인 것이 하나.
- (c)에서 **`default` 는 마지막이 아니면 안 된다.**\
  옛 `switch` 에서는 `default` 를 가운데 둬도 됐다 — 폴스루로 흘러 들어갈 수 있었기 때문이다.\
  패턴 `switch` 는 폴스루가 없으므로 그 자유가 사라졌다.
- ★ 한 문장: **"앞의 `case` 가 뒤의 `case` 가 맞을 값을 전부 먼저 가져가면 컴파일 에러다."**

```text
  잘못된 순서                              올바른 순서
  +-----------------------------+         +-----------------------------+
  | case Object x -> ...        |         | case String s -> ...        |
  | case String s -> ...  X     |         | case Object x -> ...        |
  +-----------------------------+         +-----------------------------+
    좁은 것 -> 넓은 것 -> default 순서로 적는다. 예외 없다.
```

### 5. ★ 가드가 붙으면 지배는 어떻게 되나

**출력** — (a) 같은 가드 둘

```text
(컴파일 성공)
짧은 문자열
```

**출력** — (b) 무가드가 먼저

```text
Ex.java:5: error: this case label is dominated by a preceding case label
            case String s when s.length() > 3 -> "긴 문자열";   // 가드가 있어도 앞이 먹었다
                 ^
1 error
```

**왜 그런가**

- ★ (a)는 **컴파일된다.** `f("a")` 는 `"짧은 문자열"` 이다 — 두 가드가 다 거짓이라 셋째 가지로 갔다.
- **둘째 가지는 영원히 도달할 수 없는 죽은 코드인데 경고도 없다.**
- 차이를 만드는 규칙: **지배 검사는 앞의 `case` 가 무가드일 때만 돈다.**

| 앞 | 뒤 | 결과 |
|---|---|---|
| 무가드 `case String s` | 가드 `case String s when ...` | **에러** (지배) |
| 가드 `case String s when A` | 가드 `case String s when A` | 통과 |
| 가드 `case String s when A` | 무가드 `case String s` | 통과 |

- 컴파일러가 (a)를 안 잡는 이유는 **두 가드가 겹치는지 판정할 일반 방법이 없기 때문**이다.\
  `when` 안에는 아무 식이나 올 수 있다. 그래서 javac 는 **타입만 보고** 판정하고 가드가 있으면 손을 뗀다.\
  *(이 설명은 javac 문서를 인용한 것이 아니라 관찰에서 세운 추론이다 — 근거는 (a)가 통과한다는 사실뿐이다.)*

### 6. `when` 가드의 평가 순서

**출력** (JDK 21.0.5 — 25.0.1 에서도 같았다)

```text
order("abc") = C  평가된 가드 = ABC
order("a")   = D  평가된 가드 = ABC
```

**왜 그런가**

- `"abc"`(길이 3)는 A(>100 거짓)·B(>10 거짓)를 지나 **C 에서 걸렸다.** `log` 는 `ABC`.
- `"a"`(길이 1)는 셋 다 거짓이라 **무가드 가지 D** 로 갔다. `log` 는 역시 `ABC`.
- ★ **가드는 `case` 순서대로 전부 평가될 수 있다.**

```text
  case A when 조건1   -> 조건1 평가
       |  거짓
       v
  case B when 조건2   -> 조건2 평가
       |  거짓
       v
  case C when 조건3   -> 조건3 평가
       |  거짓
       v
  case D (무가드)     -> 여기로
```

- **실무 규칙**: 가드에 **비싼 연산이나 부수효과**를 넣지 않는다.\
  넣어야 하면 `switch` 밖에서 한 번 계산해 변수로 넘긴다.
- **`when` 은 예약어가 아니고 제한 식별자도 아니다** — 변수·메서드 이름으로 아무 제약 없이 쓸 수 있다.\
  돌려 확인했다(`Ex.java (23-f1)`).

```java
static int when = 7;
static int when(int x) { return x * 2; }
```

```text
큰 원 / 작은 원 / 정사각형
변수 when = 7 / 메서드 when(3) = 6
```

- `yield` 와 다르다 — `yield(3)` 은 한정해야 부를 수 있지만 `when(3)` 은 그냥 된다\
  ([**21번 주제**](../21-switch-statement-and-expression/) 9번).

### 7. 가드만으로 완결할 수 있나

**출력**

```text
Ex.java:3: error: the switch expression does not cover all possible input values
        return switch (o) {
               ^
1 error
```

**왜 그런가**

- `String` 이 아닌 값이 문제인 것이 **아니다** — `case Object x when ...` 로 바꿔도 같은 에러다.\
  돌려 확인했다(`Ex.java (23-e12)`).

```java
return switch (o) {
    case Object x when x.hashCode() > 0 -> "양수 해시";
};
```

```text
Ex.java:3: error: the switch expression does not cover all possible input values
        return switch (o) {
               ^
1 error
```

  `Object x` 는 `Object` selector 를 **전부** 덮는 무조건 패턴인데도 안 된다.\
  진짜 이유는 **가드가 거짓일 수 있다**는 것이다. 그러면 갈 곳이 없다.
- ★ **가드 붙은 `case` 는 완결성 계산에서 빠진다.** 타입이 전부를 덮어도 소용없다.
- 고치는 방법 둘: **무가드 가지를 하나 더 두거나**(`case String s -> ...`), **`default` 를 넣는다.**
- 5번의 (a)에서 `default` 가 있어서 컴파일된 것, 「동작 방식」 (5) 의 `size()` 가 무가드 가지 덕에 완결한 것이\
  같은 규칙의 두 얼굴이다.

### 8. selector 타입과 상수 레이블

**출력**

```text
Ex.java:5: error: constant label of type String is not compatible with switch selector type Object
            case "hello"  -> "인사";          // 타입 패턴 뒤의 상수
                 ^
1 error
```

**왜 그런가**

- 메시지가 정확하다 — **상수 레이블의 타입이 selector 타입과 맞아야** 한다.
- `switch (s)` 에서 `s` 가 `String` 이면 `case "hello"` 는 **된다.** selector 가 `Object` 라서 막힌 것이다.
- **`case null` 을 두 번 쓰면** 상수 중복과 같은 규칙으로 막힌다(`Ex.java (23-e6)`).

```text
Ex.java:6: error: duplicate case label
            case null      -> "또 널";
                 ^
1 error
```

- **배열 타입은 패턴으로 쓸 수 있다.** `Ex.java (23-a)` 의 `describe` 가 `case int[] a` 를 쓰고 돌았다.

```text
describe -> int 배열 길이 3
```

- 부트스트랩 인자에도 `"[I"` 로 들어가 있다(1번).

### 9. ★ `sealed` 계층이 컴파일 후에 바뀌었다

**출력** (JDK 21.0.5)

```text
--- 1차 컴파일
(성공)
--- typeSwitch 부트스트랩 인자 (1차)
BootstrapMethods:
  0: #98 REF_invokeStatic java/lang/runtime/SwitchBootstraps.typeSwitch:(Ljava/lang/invoke/MethodHandles$Lookup;Ljava/lang/String;Ljava/lang/invoke/MethodType;[Ljava/lang/Object;)Ljava/lang/invoke/CallSite;
    Method arguments:
      #22 Circle
      #26 Square
Circle[r=1.0] -> 원
--- 2차 컴파일: Shape 와 Triangle 만 (Ex 는 그대로)
(성공)
--- 기존 타입
Circle[r=1.0] -> 원
--- 새 타입
Exception in thread "main" java.lang.MatchException
	at Ex.name(Ex.java:3)
	at Ex.main(Ex.java:10)
```

**2차 컴파일 뒤에 두 클래스 파일을 다시 찍으면 어긋남이 그대로 보인다.**

```text
--- Shape.class 의 PermittedSubclasses (2차 뒤)
PermittedSubclasses:
  Circle
  Square
  Triangle
--- Ex.class 의 Method arguments (2차 뒤)
    Method arguments:
      #22 Circle
      #26 Square
```

**왜 그런가**

- 2차 컴파일은 **성공한다.** `Shape` 만 보면 아무 문제가 없다.
- `Circle` 을 넣으면 `Circle[r=1.0] -> 원` — **기존 경로는 그대로 돈다.**
- `Triangle` 을 넣으면 **`java.lang.MatchException`** 이다.
- ★ **부트스트랩 인자가 `Circle`·`Square` 둘 그대로**다. `Shape.class` 는 셋으로 늘었는데 `Ex.class` 는 안 바뀌었다.\
  `Triangle` 은 어느 번호에도 안 맞으므로 `default:` 로 가고, 거기서 `MatchException` 이 난다.

```text
  컴파일 시점                              실행 시점
  +-----------------------------+         +-----------------------------+
  | Shape permits Circle, Square|         | Shape permits Circle,       |
  | 부트스트랩 인자 = {Circle,   |  ---->  |        Square, Triangle     |
  |                   Square}   |         | 부트스트랩 인자는 그대로      |
  | -> 완결하다고 판정           |         | Triangle -> 어느 번호도 아님  |
  +-----------------------------+         +-----------------------------+
                                            -> MatchException
```

- `MatchException` 의 javadoc 이 이 사례를 **`Separate compilation anomalies`** 라고 부른다 (JDK 21.0.5 `src.zip`).

```text
 * <ul>
 *     <li>Separate compilation anomalies, where parts of the type hierarchy that
 *         the patterns reference have been changed, but the pattern matching
 *         construct has not been recompiled. For example, if a sealed interface
 *         has a different set of permitted subtypes at run time than it had at
 *         compile time, or if an enum class has a different set of enum constants
 *         at runtime than it had at compile time, or if the type hierarchy has
 *         been changed in some incompatible way between compile time and run time.</li>
```

- 같은 javadoc 이 **`null` 과 중첩 패턴** 사례를 둘 더 적었다 — [**24번 주제**](../24-record-patterns/)가 정본이다.
- 실무 함의: **`sealed` 계층과 그것을 `switch` 하는 코드는 같이 빌드·배포한다.**\
  라이브러리 공개 `sealed` 타입에 하위 타입을 늘리는 것은 **바이너리 호환이 깨지는 변경**이다.

### 10. `if` 사슬과 무엇이 다른가

**출력** (JDK 21.0.5 — 25.0.1 에서도 같았다)

```text
Circle[r=1.0]        name=원      ifElse=원
Square[side=2.0]     name=정사각형   ifElse=정사각형
Rect[w=2.0, h=3.0]   name=직사각형   ifElse=빠뜨린 것이 여기로 온다
```

**왜 그런가**

- `Rect` 를 넣으면 `if` 사슬은 **`"빠뜨린 것이 여기로 온다"`** 를 돌려준다. `switch` 는 `"직사각형"` 이다.
- **경고가 없다.** 컴파일러는 `if` 사슬이 무엇을 덮는지 세지 않는다.
- `sealed` + `switch` 로 쓰면 **가지를 빠뜨렸을 때 컴파일이 멈춘다.**

```text
Ex.java:6: error: the switch expression does not cover all possible input values
        return switch (sh) {
               ^
1 error
```

- **옮기는 기준**: 분기 대상이 **`sealed` 계층이거나 `enum`** 이면 `switch` 로 옮긴다.\
  열린 타입(아무나 하위 타입을 만들 수 있는 것)이면 `switch` 로 옮겨도 `default` 가 필요해 이득이 적다.\
  그때는 오히려 다형성을 먼저 검토한다([`../09-inheritance-overriding/`](../09-inheritance-overriding/)).

### 11. ★ 17 에서 컴파일하면

**출력** — JDK 17.0.13 의 javac

```text
Ex.java:10: error: patterns in switch statements are a preview feature and are disabled by default.
            case Circle c -> "원";
                 ^
  (use --enable-preview to enable patterns in switch statements)
1 error
```

**출력** — JDK 21 의 `javac --release 17`

```text
Ex.java:10: error: patterns in switch statements are not supported in -source 17
            case Circle c -> "원";
                 ^
  (use -source 21 or higher to enable patterns in switch statements)
1 error
```

`--release 20` 은 숫자만 `20` 으로 바뀐 같은 메시지, `--release 21` 은 통과였다.

**출력** — 17 에서 `--enable-preview` 를 붙였을 때

```text
--- 17 + --enable-preview 로 컴파일
Note: Ex.java uses preview features of Java SE 17.
Note: Recompile with -Xlint:preview for details.
--- 그 클래스를 --enable-preview 없이 실행
java.lang.UnsupportedClassVersionError: Preview features are not enabled for Ex (class file version 61.65535). Try running with '--enable-preview'
--- 그 클래스를 --enable-preview 로 (같은 17) 실행
Circle[r=1.0]        name=원      ifElse=원
Square[side=2.0]     name=정사각형   ifElse=정사각형
Rect[w=2.0, h=3.0]   name=직사각형   ifElse=빠뜨린 것이 여기로 온다
describe -> 정수 42
--- 그 클래스를 JDK 21 로 실행
java.lang.UnsupportedClassVersionError: Ex (class file version 61.65535) was compiled with preview features that are unsupported. This version of the Java Runtime only recognizes preview features for class file version 65.65535
```

**왜 그런가**

- ★ **두 에러 메시지가 다르다.**\
  17 의 javac: "프리뷰 기능인데 꺼져 있다" — **그 판에는 기능이 있다.**\
  21 의 javac `--release 17`: "17 에서는 지원 안 된다" — **그 버전을 타깃하면 못 쓴다.**
- 17 에서 `--enable-preview` 를 붙이면 **컴파일되고 돈다.** 다만 **클래스 파일 버전이 `61.65535`** 다.
- `61` 은 Java 17 의 메이저 버전이고, 마이너 `65535`(= `0xFFFF`)가 **"프리뷰로 컴파일됨"** 을 뜻한다.
- 그래서 그 클래스 파일은 **딱 그 JDK 에서, `--enable-preview` 를 붙였을 때만** 돈다.\
  21 로 가져가면 실행조차 안 된다 — 21 은 `65.65535`(Java 21 의 프리뷰)만 인정한다.
- 실무 함의: **프리뷰로 컴파일한 산출물은 배포할 수 없다.** 21 로 올리는 것 말고 답이 없다.
- *(위 실행 오류의 한국어 머리말 `오류: 기본 클래스 ...` 는 한국어 로캘 런처의 문구라 생략했다.)*

### 12. 정본 경계와 선행 버전

**왜 그런가**

| 주제 | 그쪽이 다루는 것 | 여기가 다루는 것 |
|---|---|---|
| [**15번**](../15-sealed-classes/) `sealed` | 허용 목록 조건 · `PermittedSubclasses` 속성 · `non-sealed` 에서 완결성이 끊기는 것 | **`switch` 쪽에서 본 완결성**과 `typeSwitch` 부트스트랩 |
| [**21번**](../21-switch-statement-and-expression/) `switch` 문법 | 화살표 · `yield` · 폴스루 · `tableswitch`/`lookupswitch` · 식의 완결성 | **`case` 에 패턴이 들어오며 달라진 것** — `null`·지배·가드·문의 완결성 |
| [**22번**](../22-instanceof-type-patterns/) 타입 패턴 | `String s` 라는 패턴 자체와 흐름 스코프 | 그것이 **`case` 에 들어갔을 때** |
| [**24번**](../24-record-patterns/) `record` 패턴 | `case Circle(double r)` 형태의 중첩 해체 · `null` 과 중첩의 상호작용 | 여기는 **타입 패턴까지** |

- **선행 넷이 전부 다른 버전**이다.

```text
  14  switch 식 · 화살표 · yield        (21번 주제)
  16  instanceof 타입 패턴              (22번 주제)
  17  sealed / permits                 (15번 주제)
  21  switch 패턴 매칭 · case null      (이 주제)
  21  record 패턴                       (24번 주제)
```

- "패턴 매칭은 21부터"라고 뭉뚱그리면 **16·17 짜리 코드까지 21 이라고 잘못 외운다.**
- **`invokedynamic typeSwitch` 라는 이름은 구현 세부**다.\
  `java.lang.runtime.SwitchBootstraps` 는 컴파일러가 쓰라고 만든 내부 API이고, 명세가 그 이름을 요구하지 않는다.\
  ★ 외울 것은 이름이 아니라 **"타입 판별이 런타임 호출 한 번으로 끝나고, 그 대상 목록이 클래스 파일에 박힌다"** 는 성질이다.
- **"`default` 가 `null` 을 안 받는다"는 바뀐 것이 아니라 그대로**다.\
  옛 `switch` 도 `default` 가 있어도 `null` 에서 NPE 였다. 바뀐 것은 **`case null` 이라는 선택지가 생긴 것**뿐이다.

```text
  바뀐 것                                  그대로인 것
  +-----------------------------+          +-----------------------------+
  | 무엇으로 분기하나            |          | default 는 null 을 안 받는다 |
  |   (번호 계산 -> 런타임 호출) |          | 완결 판정은 컴파일 시점이다   |
  | case null 이 생겼다          |          | 안 맞으면 예외를 던진다       |
  | 지배 검사가 생겼다           |          |                             |
  | 문에도 완결성을 요구한다      |          |                             |
  +-----------------------------+          +-----------------------------+
```

---

## 실행 검증

| 프로그램 | 무엇을 확인했나 | 돌린 JDK |
|---|---|---|
| `Ex (23-a)` | `sealed` 완결 `switch` · `Object` selector + `default` · **`if` 사슬은 빠뜨려도 조용하다** | 21 · 25 (출력 동일) |
| `Ex (23-a)` + `javap -c -p` | `requireNonNull` + `invokedynamic typeSwitch` + `tableswitch` + 가지마다 `checkcast` + `MatchException` 가지 | 21 |
| `Ex (23-a)` + `javap -v -p` | `BootstrapMethods` 에 `case` 타입 목록(`"[I"` 포함)이 순서대로 박힌다 | 21 |
| `Ex (23-a)` JDK 17 javac | `patterns in switch statements are a preview feature and are disabled by default.` | 17 |
| `Ex (23-a)` `--release 17` / `20` / `21` | `not supported in -source 17` / `20` / (통과) | 21 의 javac |
| `Ex (23-a)` 17 `--enable-preview` | 컴파일됨 · 클래스 파일 `61.65535` · 21 에서 실행 불가 | 17 · 21 |
| `Ex (23-b)` | 옛 `switch` NPE · `case null` · `case null, default` · **`default` 만 있으면 NPE** | 21 · 25 (출력 동일) |
| `Ex (23-b)` + `javap -c -p` | `case null` 이 있으면 `requireNonNull` 이 사라지고 범위가 `-1` 부터 | 21 |
| `Ex (23-b2)` | `default` 만 있는 패턴 `switch` 의 NPE 스택 -> `Objects.requireNonNull` | 21 |
| `Ex (23-d)` | `when` 가드로 타입 안을 쪼갬 · 가드가 **순서대로 전부** 평가됨 | 21 · 25 (출력 동일) |
| `Ex (23-f1)` | `when` 을 변수·메서드 이름으로 쓸 수 있다 | 21 · 25 (출력 동일) |
| `Ex (23-f2)` | `enum` 이 구현한 `sealed` 를 타입 패턴으로 받아 완결 | 21 · 25 (출력 동일) |
| `23-rt` (4파일, 2단계 컴파일) | 부트스트랩 인자가 낡아 **`MatchException`** · `Shape.class` 는 셋, `Ex.class` 는 둘 | 21 |
| `Ex (23-e1)` | 무조건 패턴 먼저 -> `dominated` + `both an unconditional pattern and a default label` | 21 |
| `Ex (23-e2)` | `sealed` 가지 누락 -> `does not cover all possible input values` | 21 |
| `Ex (23-e3)` | `default` 뒤의 `case` -> `dominated` | 21 |
| `Ex (23-e4)` | ★ **같은 가드 둘이 컴파일된다** (경고도 없음) | 21 |
| `Ex (23-e5)` | selector `Object` 에 `case "hello"` -> `constant label of type String is not compatible` | 21 |
| `Ex (23-e6)` | `case null` 중복 -> `duplicate case label` | 21 |
| `Ex (23-e7)` | 무가드 -> 가드 순서 -> `dominated` | 21 |
| `Ex (23-e8)` | `sealed` 상위를 먼저 -> `dominated` | 21 |
| `Ex (23-e9)` | 가드만으로는 완결 안 됨 -> `does not cover all possible input values` | 21 |
| `Ex (23-e10)` | 패턴 `switch` **문**도 완결 요구 -> `the switch statement does not cover ...` | 21 |
| `Ex (23-e11)` | `case null, String s` -> `invalid case label combination` | 21 |
| `Ex (23-e12)` | 가드 붙은 **무조건** 패턴도 완결이 아니다 -> 같은 `does not cover ...` | 21 |
| `src.zip` (`MatchException.java`) | `@since 21` · 세 사례 중 **분리 컴파일** 사례 인용 | 21.0.5 |

**합계** — 프로그램 19개 + 분리 컴파일 1벌 · `javac` 41회 · `java` 16회 · `javap` 5회.

**구현 의존 항목** — 버전이 오르면 다시 돌려야 하는 것

- **`invokedynamic typeSwitch` · `SwitchBootstraps` 라는 이름**은 javac 21 의 코드 생성 방식이다.\
  외울 것은 이름이 아니라 **"판별이 런타임 호출 한 번이고 대상 목록이 클래스 파일에 박힌다"** 는 성질이다.
- **`typeSwitch` 가 `null` 에 `-1` 을 준다**는 것은 바이트코드에서 **관찰**한 것이다. 명세 인용이 아니다.
- **`Objects.requireNonNull` 로 `null` 을 막는 것**도 구현 선택이다. NPE 가 난다는 **사실**만 보장이다.
- **에러 메시지의 문구 자체**는 javac 의 것이다. 특히 11번의 두 메시지는 **javac 판에 따라 다르다.**
- **클래스 파일 버전 `61.65535`** 는 17 의 프리뷰 표시다. 판마다 숫자가 다르다(21 은 `65.65535`).
- 두 판(21·25)에서 출력이 같았던 것은 **관찰**이다.\
  [**21번 주제**](../21-switch-statement-and-expression/)에서 **출력이 같은데 바이트코드가 달랐던 실례**를 봤으므로,\
  이 주제에서도 "같았다"를 보장으로 읽지 않는다.
