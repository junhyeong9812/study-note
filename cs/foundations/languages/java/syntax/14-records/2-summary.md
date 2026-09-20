# java/syntax/14 — `record` (16+): 컴팩트 생성자·불변 계약·못 하는 것 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — JDK 21.0.5 표준 라이브러리 소스 `java.base/java/lang/Record.java` 의 **javadoc 원문**(`lib/src.zip` 에서 직접 인용 — 클래스 javadoc의 복사 불변식, `equals`·`hashCode`·`toString` 의 `@implSpec`) · [JLS SE 21 §8.10 Record Classes](https://docs.oracle.com/javase/specs/jls/se21/html/jls-8.html) · [JEP 395: Records](https://openjdk.org/jeps/395)
> **실행 검증** — 이 문서의 모든 출력·에러 메시지는 Temurin **JDK 21.0.5** 에서 실제로 돌려 얻은 것이다.\
> 같은 프로그램을 **17.0.13 · 25.0.1** 에서도 돌려 **출력이 한 글자도 다르지 않음**을 확인했다\
> (단 배열의 `toString` 에 박히는 `[I@77459877` 같은 **identity 해시는 실행마다 다르다** — 그 줄만 예외다).\
> 바이트코드는 `javap -c -p` · `javap -v -p` 출력을 그대로 옮겼다.
> **버전** — `record` 는 **Java 16** 정식이다(`src.zip` 의 `java/lang/Record.java` 가 `@since 16`, `java/lang/reflect/RecordComponent.java` 도 `@since 16`).\
> `javac --release 15` 로 컴파일하면 `records are not supported in -source 15` 로 막힌다 — 아래 「문법」 절에 출력 그대로 있다.\
> 14·15 에서는 preview 였다(그 연혁은 [`../../../../../../history/java/java-16.md`](../../../../../../history/java/java-16.md)).
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 javadoc·JLS 로, 동작은 실행·역어셈블로 접지했다.

## 한눈에 — 쉽게 말하면

**`record` 는 「보관함 번호가 적힌 영수증」이다.**

비유 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 영수증 **양식** — 칸 이름이 미리 정해진 것 | `record` 선언 — 컴포넌트 목록 |
| 인쇄된 칸 하나 | 컴포넌트 하나 = `private final` 필드 + 같은 이름의 `public` 접근자 |
| 발급기가 자동으로 찍는 것 — 대조번호·인쇄 형식 | 컴파일러가 만드는 `equals`·`hashCode`·`toString` |
| 발급 직전에 금액을 검산하고 통화를 대문자로 고치는 단계 | 컴팩트 생성자 |
| 칸에 적힌 **「보관함 3번」이라는 글자** | 참조 타입 컴포넌트가 들고 있는 **참조** |
| 보관함 **안에 든 물건** | 그 참조가 가리키는 객체의 **내용** |
| 두 영수증이 같은가 = 칸마다 글자를 대조 | `equals` = **컴포넌트 단위** 비교 |

- 영수증은 발급되면 **글자를 못 고친다.**\
  `record` 의 필드가 전부 `private final` 인 것이 이것이다.
- 그런데 영수증에 적힌 건 「보관함 3번」이라는 **번호**뿐이다.\
  **3번 보관함 안의 물건은 아무나 바꿔 넣을 수 있다** — 영수증은 그걸 막지 못한다.
- 두 영수증을 대조할 때도 **글자만 본다.**\
  「3번」과 「7번」은 안에 똑같은 물건이 들었어도 **다른 영수증**이다.

```text
record Order(String id, List<String> items) 를 만들었다

   영수증 (record 객체)              보관함 (그 참조가 가리키는 ArrayList)
   +-----------------------+        +---------------------------+
   | id    = "#1"          |        |  [ "a", "b" ]             |
   | items = 보관함 3번     | -----> |                           |
   +-----------------------+        +---------------------------+
     글자는 final — 못 고친다          여기는 아무도 안 잠갔다
                                       밖에 남은 원본 참조로 add() 가 된다
```

**똑같은 구조로** Java 가 이렇게 동작한다: 영수증 글자 = `final` 필드, 보관함 번호 = 참조 값, 보관함 속 물건 = 가리켜진 객체의 상태.\
그래서 `record` 가 주는 불변은 **얕은 불변(shallow immutability)** 이다 — `Record.java` 의 클래스 javadoc 이 쓴 표현 그대로다.

> A record class is a **shallowly immutable**, transparent carrier for a fixed set of values, called the *record components*.

실무에서 이게 터지는 자리는 **DTO 를 `record` 로 바꾸고 "이제 불변이니 안심"이라고 적는 순간**이다.\
`List` 필드 하나만 들어 있어도 밖에서 원본을 붙들고 있던 코드가 내용을 바꿔 버린다.\
그리고 그 record 를 `HashMap` 키로 쓰고 있었다면 **키가 사라진다**(계약 위반의 증상은 [`../27-equals-hashcode-contract/`](../27-equals-hashcode-contract/) 「어디서 틀리나」 2번이 정본이다).

> **컴포넌트(record component)** — `record` 이름 뒤 괄호 안에 적는 항목 하나.\
> 예: `record Point(int x, int y)` 의 `int x` 와 `int y` 가 컴포넌트 둘이고, 각각 `private final int x` 필드와 `public int x()` 접근자가 된다.

> **얕은 불변(shallow immutability)** — 필드에 **담긴 값**은 못 바꾸지만, 그 값이 참조일 때 **가리켜진 객체의 내부**는 막지 못하는 것.\
> 예: `final List<String> items` 는 다른 리스트로 갈아끼울 수 없을 뿐, `items.add("c")` 는 그대로 된다.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. `record Point(int x, int y)` 한 줄을 쓰면 컴파일러가 **정확히 무엇을 만들어 주고 무엇은 안 만들어 주는가.**
2. 검증·정규화·방어 복사는 **어디에 쓰는가** — 컴팩트 생성자는 무엇을 할 수 있고 무엇을 못 하는가.
3. 「`record` 는 불변이고 `equals` 는 알아서 맞는다」가 **어디까지 참인가.**

## 동작 방식

### (1) 한 줄이 무엇으로 펼쳐지나 — 리플렉션으로 전수 출력

**언제 쓰나** — "이거 내가 안 썼는데 어디서 나온 메서드지"를 확인할 때.

```java
record Point(int x, int y) { }        // 내가 쓴 것은 이 한 줄이 전부다
```

**실행 결과** (`Ex.java (14-a)`, JDK 21.0.5 — 17·25 동일)

```text
toString()   = Point[x=1, y=2]
x()          = 1, y() = 2
equals       = true
== 는        = false
hashCode     = 33 / 33
상위 클래스   = java.lang.Record
final 인가    = true
isRecord()   = true
--- 무엇이 만들어졌나 ---
  method public final boolean Ex$Point.equals(java.lang.Object)
  method public final java.lang.String Ex$Point.toString()
  method public final int Ex$Point.hashCode()
  method public int Ex$Point.x()
  method public int Ex$Point.y()
  field  private final int Ex$Point.x
  field  private final int Ex$Point.y
  ctor   Ex$Point(int,int)
  component int x accessor=x
  component int y accessor=y
```

```text
        내가 쓴 한 줄                     컴파일러가 만든 것
   record Point(int x, int y) { }
             |
             +--> final class Point extends java.lang.Record
             |         (상속 불가 · 다른 클래스를 상속할 수도 없다)
             |
             +--> private final int x
             |    private final int y            <- 칸(필드)
             |
             +--> public int x()
             |    public int y()                 <- 접근자 (get 접두어가 없다)
             |
             +--> Point(int x, int y)            <- 표준 생성자(canonical constructor)
             |
             +--> public final boolean equals(Object)
             |    public final int hashCode()    <- 자동 생성분은 final 이다
             |    public final String toString()
             |
             +--> 클래스 파일의 Record 속성 (컴포넌트 목록)
                  -> Class.isRecord() · Class.getRecordComponents()
```

그림 해설 (한 단계씩):

- **상위 클래스가 `java.lang.Record` 로 고정**된다.\
  그래서 `record` 는 다른 클래스를 상속할 수 없다 — 자리가 이미 찼다.
- **클래스가 `final`** 이다(`Modifier.isFinal` = true). 아무도 상속할 수 없다.
- 접근자 이름은 **`getX()` 가 아니라 `x()`** — 컴포넌트 이름 그대로다.
- 자동 생성된 `equals`·`hashCode`·`toString` 은 **`public final`** 이다.\
  내가 직접 쓰면 그 `final` 이 사라진다(아래 (2)의 끝).
- 표준 생성자 `Ex$Point(int,int)` 에는 접근 제어자가 안 붙어 있다.\
  이 `record` 를 `class Ex` 안에 **아무 제어자 없이** 선언했기 때문이다 — javadoc 이 "must provide at least as much access as the record class" 라고 적은 규칙이다.
- **`Record` 속성**은 클래스 파일에 실제로 박혀 있다. `javap -v` 로 보면 이렇다.

```text
javap -v -p Ex$Point  — 출력 그대로

Record:
  int x;
    descriptor: I

  int y;
    descriptor: I
```

- 이 속성이 있어서 리플렉션의 `getRecordComponents()` 가 **컴포넌트 이름 `x`·`y` 를 런타임에 되찾는다.**\
  일반 클래스는 파라미터 이름이 지워지지만 `record` 는 안 지워진다 — Jackson 같은 라이브러리가 이걸로 매핑한다.

비용 — 선언 한 줄에 메서드 다섯 + 필드 둘 + 생성자 하나가 생긴다.\
손으로 쓰던 boilerplate 가 클래스 파일로 이동한 것이지 사라진 것이 아니다.

> **표준 생성자(canonical constructor)** — 컴포넌트와 **같은 순서·같은 타입**의 파라미터를 받는 생성자.\
> 예: `record Point(int x, int y)` 의 표준 생성자는 `Point(int x, int y)` 하나뿐이고, `record` 마다 반드시 하나 존재한다.

### (2) `equals`·`hashCode`·`toString` 은 메서드 본문이 아니다 — `invokedynamic` 한 줄이다

**언제 쓰나** — "컴파일러가 진짜 뭘 넣었나"를 확인할 때. 답이 바이트코드에 그대로 있다.

```text
javap -c -p Ex$Point  — 출력 그대로 (14-a)

  public final java.lang.String toString();
    Code:
       0: aload_0
       1: invokedynamic #16,  0             // InvokeDynamic #0:toString:(LEx$Point;)Ljava/lang/String;
       6: areturn

  public final int hashCode();
    Code:
       0: aload_0
       1: invokedynamic #20,  0             // InvokeDynamic #0:hashCode:(LEx$Point;)I
       6: ireturn

  public final boolean equals(java.lang.Object);
    Code:
       0: aload_0
       1: aload_1
       2: invokedynamic #24,  0             // InvokeDynamic #0:equals:(LEx$Point;Ljava/lang/Object;)Z
       7: ireturn

  public int x();
    Code:
       0: aload_0
       1: getfield      #7                  // Field x:I
       4: ireturn
```

```text
javap -v -p Ex$Point 의 BootstrapMethods — 출력 그대로

BootstrapMethods:
  0: #46 REF_invokeStatic java/lang/runtime/ObjectMethods.bootstrap:(Ljava/lang/invoke/MethodHandles$Lookup;Ljava/lang/String;Ljava/lang/invoke/TypeDescriptor;Ljava/lang/Class;Ljava/lang/String;[Ljava/lang/invoke/MethodHandle;)Ljava/lang/Object;
    Method arguments:
      #8 Ex$Point
      #42 x;y
      #44 REF_getField Ex$Point.x:I
      #45 REF_getField Ex$Point.y:I
```

그림 해설 (한 단계씩):

- 세 메서드의 본문이 **전부 `invokedynamic` 한 줄**이다. 비교 로직이 클래스 파일에 없다.
- 실제 구현은 **첫 호출 때** `java.lang.runtime.ObjectMethods.bootstrap` 이 만들어 붙인다.
- `Method arguments` 가 그 부트스트랩에 넘기는 재료다 — **어느 클래스**(`Ex$Point`), **컴포넌트 이름 목록**(`x;y`), **각 필드를 읽는 핸들 둘**(`REF_getField`).
- 대비로 **접근자 `x()` 는 평범한 `getfield`** 세 줄이다. 여기엔 지연도 부트스트랩도 없다.
- 그래서 컴포넌트를 하나 추가하면 `Method arguments` 의 목록이 `x;y;z` 로 늘고 **세 메서드가 동시에 갱신**된다.\
  손으로 쓸 때 가장 흔한 사고(`equals` 만 고치고 `hashCode` 를 잊는 것)가 구조적으로 불가능해진다.

**내가 직접 쓰면 이 자리가 통째로 바뀐다.**

```text
javap -c -p Ex$C  — equals 를 직접 쓴 record (14x-g)

  public boolean equals(java.lang.Object);
    Code:
       0: aload_1
       1: instanceof    #8                  // class Ex$C
       4: ifeq          27
       7: aload_1
       8: checkcast     #8                  // class Ex$C
      11: astore_2
      12: aload_2
      13: getfield      #7                  // Field x:I
      ...
```

- `invokedynamic` 이 사라지고 **내가 쓴 코드**가 들어간다.
- 그리고 `final` 도 사라진다 — 실행으로 확인한 것이다.

**실행 결과** (`Ex.java (14x-g)`, JDK 21.0.5 — 17·25 동일)

```text
  A.equals final? true  -> public final boolean Ex$A.equals(java.lang.Object)
  B.equals final? true  -> public final boolean Ex$B.equals(java.lang.Object)
  C.equals final? false  -> public boolean Ex$C.equals(java.lang.Object)
```

- `A`(전부 자동)와 `B`(표준 생성자만 직접 씀)의 `equals` 는 `final`.
- `C`(`equals` 를 직접 씀)의 `equals` 는 `final` 이 아니다.
- 즉 **`final` 은 "컴파일러가 만든 것"의 표시**이지 `record` 라서 붙는 도장이 아니다.

비용 — 첫 호출에 부트스트랩 한 번(그 뒤로는 일반 호출과 같다).\
그 대가로 클래스 파일이 작아지고 컴포넌트 추가가 자동 반영된다.

> **`invokedynamic`** — 무엇을 부를지 **첫 실행 때 정하는** JVM 명령. 부트스트랩 메서드가 호출 대상을 만들어 그 자리에 붙인다.\
> 예: 람다도 이 명령으로 컴파일된다 — 클래스 파일에는 "누구를 부를지 이 부트스트랩에 물어봐라"만 적혀 있다.

### (3) 컴팩트 생성자 — 파라미터를 고치면, 대입은 컴파일러가 마지막에 해 준다

**언제 쓰나** — 검증(거부)·정규화(다듬기)·방어 복사를 넣을 때. `record` 에서 이 셋의 자리는 여기 하나다.

```java
record Range(int lo, int hi) {
    Range {                                  // 컴팩트 생성자 — 파라미터 목록이 없다
        if (lo > hi) throw new IllegalArgumentException("lo > hi: " + lo + " > " + hi);
        lo = Math.max(lo, 0);                // 정규화 — 파라미터에 대입한다
    }
}
record Money(String currency, long amount) {
    Money {
        currency = currency.toUpperCase();   // 정규화
    }
}
```

**실행 결과** (`Ex.java (14-b)`)

```text
Range[lo=0, hi=10]
Money[currency=USD, amount=100]
검증 -> java.lang.IllegalArgumentException: lo > hi: 9 > 2
```

- `new Range(-5, 10)` 이 `Range[lo=0, hi=10]` 이 됐다 — `lo = Math.max(lo, 0)` 이 **필드에 반영**됐다.
- `new Money("usd", 100)` 이 `USD` 로 저장됐다.
- `new Range(9, 2)` 는 **객체가 아예 안 만들어진다** — 잘못된 상태의 `record` 가 존재할 수 없다.

```text
컴팩트 생성자가 실제로 도는 순서

  new Range(-5, 10)
        |
        v
  [파라미터 lo=-5, hi=10 이 준비된다]
        |
        v
  +-- 내가 쓴 본문 --------------------+
  |  if (lo > hi) throw ...            |   <- 검증: 던지면 여기서 끝, 필드는 안 만들어짐
  |  lo = Math.max(lo, 0);   // lo=0   |   <- 정규화: 파라미터 변수를 고친다
  +------------------------------------+
        |
        v
  [컴파일러가 넣은 마지막 두 줄]
     this.lo = lo;   // 0
     this.hi = hi;   // 10
        |
        v
  Range[lo=0, hi=10]
```

**그 마지막 두 줄이 바이트코드에 그대로 있다.**

```text
javap -c -p Ex$Range  — 출력 그대로 (14-b)

  Ex$Range(int, int);
    Code:
       0: aload_0
       1: invokespecial #1                  // Method java/lang/Record."<init>":()V
       4: iload_1
       5: iload_2
       6: if_icmple     24
       9: new           #7                  // class java/lang/IllegalArgumentException
      12: dup
      13: iload_1
      14: iload_2
      20: invokespecial #13                 // Method java/lang/IllegalArgumentException."<init>":(Ljava/lang/String;)V
      23: athrow
      24: iload_1
      25: iconst_0
      26: invokestatic  #16                 // Method java/lang/Math.max:(II)I
      29: istore_1
      30: aload_0
      31: iload_1
      32: putfield      #22                 // Field lo:I
      35: aload_0
      36: iload_2
      37: putfield      #28                 // Field hi:I
      40: return
```

*(offset 15 의 문자열 결합 한 줄은 `javap -v` 에서 제어문자가 섞여 나오므로 뺐다 — 그 자리는 `"lo > hi: " + lo + " > " + hi` 를 만드는 줄이다.)*

그림 해설 (한 단계씩):

- offset 4~23 이 **내가 쓴 검증**이다. `athrow` 로 끝나는 길에는 `putfield` 가 없다.
- offset 24~29 가 **내가 쓴 정규화** — `Math.max` 의 결과를 `istore_1`, 즉 **파라미터 슬롯**에 다시 넣는다.
- offset 30~37 이 **내가 안 쓴 두 줄** — `putfield lo`, `putfield hi`.\
  컴팩트 생성자가 "대입으로 끝난다"는 말의 실물이 이것이다.
- 그래서 **파라미터를 고치면 필드에 반영되고**, 반대로 `this.lo = ...` 은 쓸 수 없다(「어디서 틀리나」 5번).

비용 — 없음. 일반 생성자와 같은 바이트코드다.

> **컴팩트 생성자(compact constructor)** — `record` 이름 뒤에 **괄호 없이** 바로 `{` 를 여는 생성자 형태.\
> 예: `Range { ... }` 는 `Range(int lo, int hi)` 의 본문 앞부분만 쓰는 것이고, 마지막 대입은 컴파일러가 채운다.

### (4) 얕은 불변 — `record` 가 잠그는 것은 칸이지 보관함이 아니다

**언제 쓰나** — `record` 의 컴포넌트에 `List`·`Map`·배열·가변 객체가 있을 때. 즉 거의 항상.

```java
record Order(String id, List<String> items) { }     // 방어 복사 없음
```

**실행 결과** (`Ex.java (14-c)`, JDK 21.0.5 — 17·25 동일)

```text
=== 얕은 불변 — 컬렉션 컴포넌트 ===
만든 직후  : Order[id=#1, items=[a, b]]
밖에서 추가: Order[id=#1, items=[a, b, c]]
접근자로 추가: Order[id=#1, items=[a, b, c, d]]
```

```text
구멍 1 — 밖에 남은 원본 참조             구멍 2 — 접근자가 준 참조

  List src = new ArrayList(["a","b"])      Order o
        |                                     |
        +--> new Order("#1", src)             +--> o.items()  (같은 리스트를 그대로 준다)
        |                                     |
  src.add("c")  <- 밖에서 바꾼다          o.items().add("d")  <- 받아서 바꾼다
        |                                     |
        v                                     v
  Order[id=#1, items=[a, b, c]]         Order[id=#1, items=[a, b, c, d]]
```

그림 해설 (한 단계씩):

- 구멍이 **둘**이다 — 들어올 때(생성자로 받은 참조)와 나갈 때(접근자가 주는 참조).
- 한쪽만 막으면 다른 쪽으로 샌다. **컴팩트 생성자와 접근자 양쪽**을 고쳐야 한다.
- 에러도 경고도 없다. `record` 라서 `final` 인데도 내용이 바뀐다.

**고친 판** (`Ex.java (14-d)`)

```java
record Order(String id, List<String> items) {
    Order {
        items = List.copyOf(items);              // 들어올 때 복사 + 불변 리스트로
    }
}
record Buf(String name, int[] data) {
    Buf { data = data.clone(); }                 // 배열도 복사한다
    @Override public boolean equals(Object o) {
        return o instanceof Buf b && name.equals(b.name) && Arrays.equals(data, b.data);
    }
    @Override public int hashCode() { return Objects.hash(name, Arrays.hashCode(data)); }
    @Override public String toString() { return "Buf[name=" + name + ", data=" + Arrays.toString(data) + "]"; }
    public int[] data() { return data.clone(); } // 나갈 때도 복사해서 준다
}
```

```text
밖에서 추가해도 : Order[id=#1, items=[a, b]]
접근자로 추가  : java.lang.UnsupportedOperationException
배열 record equals = true / Buf[name=x, data=[1, 2]]
HashSet 크기 = 1
```

- `List.copyOf` 하나로 **두 구멍이 동시에 막혔다** — 복사본이면서 수정 불가 뷰이기 때문이다.\
  그래서 `Order` 는 접근자를 안 고쳐도 됐다.
- 배열은 `List.copyOf` 같은 게 없으므로 **`clone()` 을 양쪽에** 넣어야 한다.
- 그리고 배열은 `equals`·`hashCode`·`toString` **셋을 전부 직접 써야** 한다(다음 절).

비용 — 생성마다 복사 1회. 접근자 호출마다 복사 1회(배열 쪽).\
뜨거운 경로에서 접근자를 반복 호출하면 그 복사가 누적된다.

> **방어 복사(defensive copy)** — 밖에서 받은 가변 객체를 그대로 붙잡지 않고 복사본을 갖는 것. 줄 때도 복사본을 주는 것.\
> 예: `items = List.copyOf(items)` 는 받은 리스트의 복사본을 만들고, 그 복사본은 `add` 가 막혀 있다.\
> 이 관용구 자체는 [**59번 주제**](../59-immutable-objects/)(불변 객체 만들기)가 정본이다.

### (5) `equals` 는 컴포넌트 단위다 — 그 규칙이 그대로 드러나는 두 자리

**언제 쓰나** — `record` 의 `equals` 가 기대와 다를 때. 원인은 항상 **컴포넌트 하나의 `equals`** 다.

`Record.equals` 의 `@implSpec` 원문이 규칙을 못박는다(JDK 21.0.5 `src.zip`).

> `<li>` If the component is of a **reference type**, the component is considered equal if and only if `Objects.equals(this.c, r.c)` would return `true`.
> `<li>` If the component is of a **primitive type**, using the corresponding primitive wrapper class `PW` ..., the component is considered equal if and only if `PW.compare(this.c, r.c)` would return `0`.

```text
  Point[x=1, y=2].equals(other)
        |
        +-- other 가 같은 record 클래스인가?  아니면 false
        |
        +-- 컴포넌트마다 한 칸씩
              int x    (원시)   -> Integer.compare(this.x, r.x) == 0
              int y    (원시)   -> Integer.compare(this.y, r.y) == 0
              List l   (참조)   -> Objects.equals(this.l, r.l)
              int[] d  (참조!)  -> Objects.equals(this.d, r.d)   <- 배열의 equals = 참조 비교
              double c (원시)   -> Double.compare(this.c, r.c) == 0
```

**(5-a) 배열 컴포넌트 — 내용이 같아도 다르다**

```text
=== 배열 컴포넌트와 equals ===        (14-c)
b1 = Buf[name=x, data=[I@77459877]
내용이 같은 두 record 가 equals? false
hashCode 같나? false
HashSet 크기 = 2
```

- 배열은 **참조 타입**이므로 `Objects.equals` 로 간다.\
  `int[]` 는 `equals` 를 재정의하지 않으므로 그건 곧 **`==`(참조 비교)** 다.
- `toString` 도 `[I@77459877` 이 그대로 박힌다.
- 결과: `HashSet` 에 같은 내용이 **둘** 들어간다. 조회도 실패한다.
- 이것은 `equals` **계약 위반이 아니다** — 참조가 다르면 다른 객체라는 판정은 반사·대칭·추이를 다 지킨다.\
  다섯 조항과 위반의 증상은 [`../27-equals-hashcode-contract/`](../27-equals-hashcode-contract/) 가 정본이다.\
  여기서 깨지는 건 계약이 아니라 **"내용이 같으면 같겠지"라는 내 기대**다.

**(5-b) 부동소수 컴포넌트 — 원시 비교와 뒤집힌다**

```text
=== 부동소수 컴포넌트 ===             (14-c, 17·21·25 동일)
NaN  == NaN  (원시 비교)   : false
Temp(NaN).equals(Temp(NaN)): true
0.0  == -0.0 (원시 비교)   : true
Temp(0.0).equals(Temp(-0.0)): false
```

```text
   그냥 double 로 비교할 때            record 컴포넌트로 비교할 때
   +---------------------------+      +---------------------------------+
   | NaN == NaN      -> false  |      | Double.compare(NaN, NaN) == 0   |
   |                           |      |                 -> true         |
   | 0.0 == -0.0     -> true   |      | Double.compare(0.0, -0.0) == 0  |
   |                           |      |                 -> false        |
   +---------------------------+      +---------------------------------+
     IEEE 754 의 == 규칙                 @implSpec 이 정한 PW.compare 규칙
```

- **둘 다 뒤집힌다.** 우연이 아니라 `@implSpec` 이 `Double.compare` 를 쓰라고 정한 결과다.
- `Double.compare` 는 `NaN` 을 자기 자신과 같게, `-0.0` 을 `0.0` 보다 작게 정렬한다.
- 그래서 `record` 의 `equals` 가 **오히려 반사성을 지킨다** — `NaN` 필드를 가진 손수 쓴 `equals` 가 `==` 를 쓰면 `x.equals(x)` 가 `false` 가 되어 계약을 깬다.
- 대신 **금액·좌표에서 `0.0` 과 `-0.0` 이 다른 키**가 된다. 계산 결과로 `-0.0` 이 나오는 경로가 있으면 조회가 빈다.

비용 — 없음. 판정 규칙이다.

> **`PW.compare`** — 원시 타입에 대응하는 래퍼 클래스(`int` → `Integer`, `double` → `Double`)의 `compare` 정적 메서드.\
> 예: `Double.compare(a, b) == 0` 이 `record` 가 `double` 컴포넌트를 같다고 보는 기준이다 — `a == b` 가 아니다.

## 문법 — 형태와 규칙

직접 쓴 최소 예제다.

### 선언 형태 셋

```java
record Point(int x, int y) { }                    // 본문이 비어도 된다

record Range(int lo, int hi) {                    // 1) 컴팩트 생성자
    Range { if (lo > hi) throw new IllegalArgumentException(); }
}

record B(int x, int y) {                          // 2) 표준 생성자를 통째로 쓴다
    B(int x, int y) { this.x = x; this.y = Math.max(y, 0); }
}

record User(String name, int age) {               // 3) 보조 생성자 — this(...) 로 위임
    User(String name) { this(name, 0); }
}
```

| 형태 | 파라미터 목록 | 필드 대입 | 언제 |
|---|---|---|---|
| 컴팩트 생성자 `Range { }` | **안 쓴다** | 컴파일러가 마지막에 | 검증·정규화·방어 복사 — **기본값** |
| 표준 생성자 `B(int x, int y) { }` | 컴포넌트와 동일 | **내가 전부** `this.x = x` | 대입 자체를 다르게 해야 할 때 |
| 보조 생성자 `User(String name)` | 다르게 | `this(...)` 로 위임 | 기본값 있는 팩토리 대용 |

- 1과 2는 **둘 다 표준 생성자**다. **동시에 쓰면 컴파일 에러**다(「어디서 틀리나」 5번).
- 2를 쓰면 **모든 컴포넌트를 내가 대입**해야 한다. 하나라도 빠지면 `variable y might not have been initialized`.
- 3은 **첫 문장이 `this(...)`** 여야 한다. `super(...)` 는 쓸 수 없다(상위는 `Record` 로 고정).

### `record` 로 되는 것

**실행 결과** (`Ex.java (14-e)`)

```text
안녕 준
보조 생성자   : 무명(0)
static 상수   : anonymous(0)
제네릭 record : Box[value=[1, 2]]
지역 record   : Local[a=3, b=4] sum=7
Local 은 static 인가 = true
정렬도 된다   : [a(2), b(1)]
```

| 되는 것 | 형태 |
|---|---|
| 인터페이스 구현 | `record User(String name, int age) implements Named { }` |
| `static` 필드·메서드 | `static final User ANONYMOUS = new User("anonymous", 0);` |
| 인스턴스 메서드 추가 | `public String greet() { return "안녕 " + name; }` |
| `toString`·`equals`·`hashCode` 재정의 | `@Override public String toString() { ... }` |
| 접근자 재정의 | `public int[] data() { return data.clone(); }` |
| 제네릭 | `record Box<T>(T value) { }` |
| **지역 `record`** (메서드 안) | `record Local(int a, int b) { }` — 암묵적으로 `static` 이다 |

- 지역 `record` 의 `Modifier.isStatic` 이 **true** 로 나왔다.\
  지역 클래스와 달리 **바깥 지역 변수를 캡처하지 않는다** — 중첩·지역 클래스의 캡처 규칙은 [`../12-nested-classes/`](../12-nested-classes/) 가 정본이다.
- 메서드 본문에서 스트림 중간 결과를 담는 **한 번 쓰고 버리는 타입**이 지역 `record` 의 자리다.

### `record` 로 안 되는 것 — 전부 실제 `javac` 출력이다

```text
(1) 인스턴스 필드 추가                    (14-err e1)
e1/Ex.java:3: error: field declaration must be static
        private int cached;
                    ^
  (consider replacing field with record component)

(2) 다른 클래스 상속                      (14-err e2)
e2/Ex.java:3: error: '{' expected
    record Point(int x) extends Base { }
                       ^

(3) record 를 상속                        (14-err e3)
e3/Ex.java:3: error: cannot inherit from final Point
    static class Sub extends Point { Sub(int x) { super(x); } }
                             ^

(4) 컴팩트 생성자에서 this.x 에 대입       (14-err e4)
e4/Ex.java:3: error: cannot assign a value to final variable x
        Point { this.x = Math.abs(x); }
                    ^

(5) 컴팩트 + 표준 생성자 둘 다             (14-err e5)
e5/Ex.java:4: error: constructor Point(int) is already defined in record Point
        Point(int x) { this.x = x; }
        ^

(6) 컴포넌트 이름을 hashCode 로            (14-err e6)
e6/Ex.java:2: error: illegal record component name hashCode
    record Bad(int hashCode) { }
                   ^
```

- (2)만 **문법 에러**(`'{' expected`)다 — `extends` 를 쓰는 **자리 자체가 없다.**\
  "상속 금지"가 의미 검사가 아니라 **문법에 없는 것**으로 처리된다.
- (6)의 금지어는 `Object` 의 메서드 이름들이다(`hashCode`·`toString`·`equals`·`getClass`·`wait`·`notify`·`clone`·`finalize`).\
  접근자 이름이 그 메서드와 충돌하기 때문이다.
- `implements` 는 된다. 막힌 건 **`extends` 뿐**이다.

### 버전 경계

```text
$ javac --release 15 d/Ex.java
d/Ex.java:3: error: records are not supported in -source 15
    record Order(String id, List<String> items) {
    ^
  (use -source 16 or higher to enable records)
d/Ex.java:3: warning: 'record' may become a restricted type name in a future release and may be unusable for type declarations or as the element type of an array

$ javac --release 16 d/Ex.java
(컴파일 성공)
```

- 16 부터다. `src.zip` 의 `java/lang/Record.java` 와 `java/lang/reflect/RecordComponent.java` 가 둘 다 `@since 16`.
- 경고가 말하듯 `record` 는 **제한 식별자**다 — 15 까지는 변수 이름으로 쓸 수 있었다.

## 어디서 틀리나

이 주제의 값어치는 전부 여기 있다.\
**여섯 중 다섯이 컴파일 에러 없이 조용히 틀린다.**

### 1. "`record` 니까 불변이다" — 컬렉션·배열 컴포넌트에서 무너진다

동작 방식 (4)가 그대로 함정이다. 다시 한 번, **증상만**.

```text
             기대                                실제 (14-c)
  +---------------------------+      +---------------------------------+
  | record 로 바꿨으니        |      | src.add("c")     -> 내용이 바뀐다 |
  | 아무도 못 바꾼다          |      | o.items().add("d") -> 또 바뀐다  |
  | HashMap 키로 안전하다     |      | 키의 해시가 바뀌어 조회가 실패한다 |
  +---------------------------+      +---------------------------------+
```

- `record` 가 보장하는 것은 **"`o.items` 가 다른 리스트를 가리키게 만들 수 없다"** 뿐이다.
- `HashMap` 키로 쓰던 중에 내용이 바뀌면 **넣은 키를 못 찾는다.** 그 증상의 정본은 [`../27-equals-hashcode-contract/`](../27-equals-hashcode-contract/) 「어디서 틀리나」 2번이다.
- 방어: 컴팩트 생성자에서 `List.copyOf` / `Map.copyOf` / `.clone()`.\
  `List.copyOf` 는 복사와 수정 불가를 동시에 주므로 **접근자를 안 고쳐도 된다.**\
  배열은 그런 게 없으므로 **접근자도 고쳐야 한다.**
- 판별 질문: **"이 컴포넌트의 타입이 `String`·기본형·다른 `record`·`List.of` 류가 아닌가?"**\
  아니면 방어 복사를 생각한다.

### 2. 배열 컴포넌트 — `equals` 셋을 전부 직접 써야 한다

```text
Buf(String name, int[] data) 를 자동 그대로 두면   (14-c)

  b1.equals(b2)        -> false      내용이 같은데도
  hashCode 같나        -> false
  HashSet 크기         -> 2          중복이 그대로 쌓인다
  toString             -> Buf[name=x, data=[I@77459877]
```

- 원인은 하나다 — **배열은 참조 타입**이고 `Objects.equals` 는 배열의 `equals`(= `==`)를 부른다.
- **고칠 때 셋을 다 고쳐야 한다.** `equals` 만 `Arrays.equals` 로 바꾸면 `hashCode` 가 어긋나 계약을 깬다.

```java
@Override public boolean equals(Object o) {
    return o instanceof Buf b && name.equals(b.name) && Arrays.equals(data, b.data);
}
@Override public int hashCode() { return Objects.hash(name, Arrays.hashCode(data)); }
@Override public String toString() { return "Buf[name=" + name + ", data=" + Arrays.toString(data) + "]"; }
```

- `toString` 까지 고치는 이유는 javadoc 의 또 다른 불변식 때문이다 — **"any two records which are equal must produce equal strings"**.\
  `equals` 만 고치고 `toString` 을 두면 같다고 판정된 둘이 다른 문자열을 뱉는다.
- **더 나은 답**: 애초에 컴포넌트를 `List<Integer>`·`String` 으로 잡는다.\
  배열을 `record` 컴포넌트로 두는 순간 자동 생성의 이득이 전부 사라진다.

### 3. ★ 접근자만 방어 복사하면 **javadoc 이 "반드시 성립한다"고 못박은 불변식이 깨진다**

가장 조용하고, 가장 그럴듯하게 틀리는 자리다.

```java
record Safe(String name, int[] data) {
    public int[] data() { return data.clone(); }   // 좋은 일을 한 것 같다
}
```

**실행 결과** (`Ex.java (14x-h)`, JDK 21.0.5 — 17·25 동일)

```text
Buf  (자동 그대로)   : r.equals(copy) = true
   같은 내용의 새 배열로 만들면 = false
Safe (접근자만 복사) : r.equals(copy) = false
```

`Record.java` 의 클래스 javadoc 이 요구하는 것은 이것 하나다.

> For all record classes, the following **invariant must hold**: if a record R's components are `c1, c2, ... cn`, then if a record instance is copied as follows:
> ```
>     R copy = new R(r.c1(), r.c2(), ..., r.cn());
> ```
> then it must be the case that `r.equals(copy)`.

```text
  자동 그대로 (Buf)                        접근자만 복사 (Safe)
  +-------------------------------+       +-------------------------------+
  | data() 가 원본 배열을 준다      |       | data() 가 clone 을 준다        |
  |   -> copy 의 배열 == 원본 배열  |       |   -> copy 의 배열 != 원본 배열  |
  |   -> Objects.equals -> true    |       |   -> Objects.equals -> false   |
  | 불변식 **성립**                 |       | 불변식 **위반**                |
  +-------------------------------+       +-------------------------------+
     단, 내용이 같은 다른 배열과는            "좋은 일"을 한 쪽이 계약을 깼다
     false — 그건 계약 위반이 아니다
```

- 자동 그대로인 `Buf` 는 **불변식을 지킨다.** 접근자가 같은 참조를 돌려주기 때문이다.
- 접근자만 `clone()` 으로 바꾼 `Safe` 는 **불변식을 깬다.** 복사본이 자기 자신과 같지 않다.
- 즉 **방어 복사는 `equals` 재정의와 한 묶음**이다. 접근자만 고치는 중간 상태가 가장 나쁘다.
- 14-d 처럼 `equals` 를 `Arrays.equals` 로 함께 고치면 다시 성립한다.
- 이 불변식은 직렬화·역직렬화와 `record` 패턴 분해가 기대는 토대다 — `record` 패턴은 [**24번 주제**](../24-record-patterns/).

### 4. 부동소수 컴포넌트 — `0.0` 과 `-0.0` 이 다른 키가 된다

동작 방식 (5-b)가 그대로 함정이다.

```text
Temp(0.0).equals(Temp(-0.0)) : false      (14-c)
```

- `0.0 == -0.0` 은 `true` 인데 `record` 의 `equals` 는 `false` 다.
- `-0.0` 은 **일부러 쓰지 않아도 나온다** — `-1.0 * 0.0`, `0.0 / -1.0`, 반올림 결과.
- 증상: `Map<Temp, ...>` 에 넣어 둔 값을 **같은 계산을 다시 해도 못 찾는다.**
- 방어: 컴팩트 생성자에서 정규화한다 — `celsius = celsius == 0.0 ? 0.0 : celsius;`\
  (`==` 는 `-0.0` 도 `0.0` 과 같다고 보므로 이 한 줄로 `-0.0` 이 `0.0` 이 된다.)
- 돈은 `double` 이 아니라 `BigDecimal`·`long`(최소 단위) 로 — [**53번 주제**](../53-bigdecimal/).

### 5. 생성자 세 형태를 섞는다 — 여기만 컴파일 에러로 막힌다

```text
(a) 컴팩트 생성자에서 this.x 에 대입                       (14-err e4)
    error: cannot assign a value to final variable x

(b) 컴팩트 + 표준 생성자를 둘 다 선언                      (14-err e5)
    error: constructor Point(int) is already defined in record Point

(c) 표준 생성자를 직접 쓰면서 컴포넌트 하나를 안 채움        (14x-g2)
    error: variable y might not have been initialized
```

- (a)가 헷갈리는 이유: 컴팩트 생성자 안의 `x` 는 **필드가 아니라 파라미터**다.\
  `x = ...` 는 되고 `this.x = ...` 는 안 된다. 보통 자바와 정반대의 감각이다.
- (b) 컴팩트와 표준은 **같은 생성자의 두 표기**다. 둘 다 쓰면 중복 선언이다.
- (c) 표준 생성자를 직접 쓰기로 했으면 **전부 내 책임**이다. 컴파일러가 대입을 안 넣어 준다.
- 셋 다 **컴파일이 막아 준다** — 이 주제에서 유일하게 안전한 자리다.

### 6. 안 만들어 주는 것을 만들어 준다고 기대한다

```text
=== record 가 구현하지 않는 것 ===        (14x-f, 17·21·25 동일)
Comparable 인가   = false
Serializable 인가 = false
구현한 인터페이스 = []
TreeSet -> java.lang.ClassCastException
   메시지: class Ex$Point cannot be cast to class java.lang.Comparable (Ex$Point is in unnamed module of loader 'app'; java.lang.Comparable is in module java.base of loader 'bootstrap')
HashMap 조회      = a
```

```text
   만들어 준다                          안 만들어 준다
  +-----------------------------+     +------------------------------------+
  | 표준 생성자                  |     | 세터 (그럴 리가)                    |
  | 컴포넌트 접근자 x()          |     | 빌더                               |
  | equals / hashCode / toString |     | with 류 복사 메서드                 |
  | java.lang.Record 상속        |     | Comparable  -> TreeSet 이 던진다    |
  | final (상속 불가)            |     | Serializable                       |
  | Record 속성 (컴포넌트 이름)   |     | **깊은 불변**                      |
  +-----------------------------+     +------------------------------------+
     -> HashMap 은 그냥 된다              -> TreeSet 은 ClassCastException
```

- `getInterfaces()` 가 **빈 배열**이다. `record` 는 어떤 인터페이스도 자동으로 붙이지 않는다.
- `HashMap` 은 `equals`/`hashCode` 만 쓰므로 **그냥 된다.**\
  `TreeSet`/`TreeMap` 은 `compareTo` 를 쓰므로 **런타임에 터진다.**\
  두 컬렉션이 "같음"을 다르게 판정한다는 것 자체는 [`../27-equals-hashcode-contract/`](../27-equals-hashcode-contract/) 「더 알면 좋은 것」이 정본이다.
- 필드 하나만 바꾼 복사본이 필요하면 **직접 써야 한다** — `Point withX(int x) { return new Point(x, y); }`.
- 직렬화는 안 붙지만, `implements Serializable` 을 붙이면 javadoc 이 적은 대로 **역직렬화가 표준 생성자를 거친다**(「더 들어가면」).

## 구현 세부사항 대 언어 보장

`record` 는 **자동 생성**이라서, 관찰한 값을 보장으로 착각하기 가장 쉬운 문법이다.\
아래 표의 왼쪽은 **전부 17·21·25 세 버전에서 똑같이 나왔다.** 그래도 오른쪽이 판정이다.

| 관찰한 것 | 무엇인가 | 근거 |
|---|---|---|
| `new Point(1,2).hashCode()` 가 **`33`** — 세 버전 동일 | **구현 세부** | `Record.hashCode` `@implSpec`: "The precise algorithm ... is **unspecified and is subject to change**" |
| 같은 값이면 실행이 달라도 같은 해시 | **보장 아님** | 같은 곳: "need not remain consistent from one execution of an application to another" |
| `int` 컴포넌트의 해시 = `Integer.hashCode` 라는 추정 | **보장 아님** | 같은 곳: "a component of primitive type **may contribute its bits ... differently** than the `hashCode` of its primitive wrapper class" |
| `toString` 이 `Point[x=1, y=2]` 형식 | **구현 세부** | `Record.toString` `@implSpec`: "The precise format ... is subject to change, so the present syntax **should not be parsed** by applications" |
| `equals`·`hashCode`·`toString` 이 `invokedynamic` 한 줄 | **구현 세부** — javac 의 전략 | `javap -c -p` |
| 부트스트랩이 `java.lang.runtime.ObjectMethods.bootstrap` | **구현 세부** | `javap -v -p` 의 `BootstrapMethods` |
| 컴팩트 생성자가 `putfield` 로 끝난다 | **언어 보장** (형태는 구현) | JLS §8.10.4 — 컴팩트 생성자 끝에 필드 대입이 암묵적으로 수행된다 |
| 참조 컴포넌트는 `Objects.equals`, 원시는 `PW.compare == 0` | **언어 보장** | `Record.equals` `@implSpec` |
| `r.equals(new R(r.c1(), ..., r.cn()))` | **언어 보장** — "invariant **must hold**" | `Record.java` 클래스 javadoc |
| `equals` 로 같은 두 record 는 같은 문자열을 낸다 | **언어 보장**(드문 완화 조건 있음) | `Record.toString` javadoc |
| `record` 는 `final`, 상위는 `java.lang.Record` | **언어 보장** | JLS §8.10, 실행 확인 |
| `Class.isRecord()` · `getRecordComponents()` | **언어 보장** (16+) | `src.zip` `@since 16` |

세 줄 요약.

- **값은 보장이 아니다.** `33` 도, `Point[x=1, y=2]` 라는 형식도 외우지 말고 **파싱하지도 마라.**
- **규칙은 보장이다.** "컴포넌트마다 `Objects.equals` / `PW.compare`" 는 `@implSpec` 이 문서화한 계약이고, 부동소수의 뒤집힘은 그 계약의 **직접적 귀결**이다.
- `@implSpec` 의 마지막 문장도 읽어 둘 것 — "The implementation **may or may not** use calls to the particular methods listed, and **may or may not** perform comparisons in the order of component declaration."\
  즉 **비교 순서도 보장이 아니다.** 컴포넌트의 `equals` 에 부작용을 넣으면 안 된다.

## 언제 쓰고 언제 안 쓰나

| 쓸 것 | 안 쓸 것 |
|---|---|
| API 응답·요청 DTO, 이벤트, 설정 값 묶음 — **값이 전부인 타입** | 정체성(ID)이 있는 도메인 엔티티 — 필드가 같다고 같은 주문이 아니다 |
| 메서드가 값 둘 이상을 돌려줘야 할 때 (`Map.Entry` 대용) | JPA 엔티티 — 기본 생성자·가변 필드·프록시 상속이 필요하다 |
| 메서드 안에서만 쓰는 임시 묶음 → **지역 `record`** | 필드를 **일부만** `equals` 에 넣고 싶을 때(캐시·타임스탬프 제외) |
| `sealed` 인터페이스의 대안들 → 패턴 매칭과 짝 ([`../15-sealed-classes/`](../15-sealed-classes/)) | 상속 계층이 필요한 타입 — `extends` 자체가 문법에 없다 |
| `Map` 의 복합 키 — `equals`/`hashCode` 가 공짜다 | **가변 컬렉션·배열을 그대로 담아야** 할 때 (방어 복사 비용을 감당 못 하면) |

판단 규칙 세 줄.

- **"이 타입의 정체성이 값 전부인가"** — 그렇다면 `record`. 아니면 클래스.
- **컴포넌트에 가변 참조가 하나라도 있으면 컴팩트 생성자를 반드시 연다.** 복사 없이 통과시키지 않는다.
- **배열 컴포넌트는 피한다.** 피할 수 없으면 `equals`·`hashCode`·`toString` **셋 다** 직접 쓴다.

## 핵심 문장

- `record` 한 줄은 **표준 생성자 + 접근자 + `equals`/`hashCode`/`toString` + `Record` 상속 + `final`** 로 펼쳐진다. 그 이상은 아무것도 안 만들어 준다.
- 자동 생성된 세 메서드는 클래스 파일에 **`invokedynamic` 한 줄**뿐이고, 실제 구현은 `ObjectMethods.bootstrap` 이 컴포넌트 목록을 받아 런타임에 만든다.
- **컴팩트 생성자가 검증·정규화·방어 복사의 유일한 자리**다. 파라미터에 대입하면 되고, `this.x =` 는 컴파일 에러다 — 대입은 컴파일러가 마지막에 `putfield` 로 넣는다.
- `record` 의 불변은 **얕다.** 컬렉션·배열 컴포넌트는 들어올 때와 나갈 때 **양쪽**을 막아야 하고, 접근자만 막으면 javadoc 의 복사 불변식이 깨진다.
- `equals` 는 **컴포넌트 단위**다 — 참조는 `Objects.equals`, 원시는 `PW.compare == 0`. 그래서 배열은 내용이 같아도 다르고, `NaN` 은 같고, `-0.0` 은 `0.0` 과 다르다.
- **`hashCode` 값도 `toString` 형식도 보장이 아니다.** 세 버전에서 같았다는 것은 관찰이지 계약이 아니다.

## 관련 자료

- [`../README.md`](../README.md) — Java 문법·API 주제 목록(이 주제는 14번)
- [`../../../../../../history/java/java-16.md`](../../../../../../history/java/java-16.md) — **`record` 가 언제·왜 들어왔나가 정본**(JEP 395, 14·15 preview 를 거친 정식화).\
  여기는 **어떻게 쓰고 무엇을 못 하나** — 연혁은 저기서, 컴팩트 생성자와 못 하는 것은 여기서 본다
- [`../../../../../../history/java/java-14.md`](../../../../../../history/java/java-14.md) — `record` 1차 preview 가 나온 편
- [`../../../../../../history/java/java-21.md`](../../../../../../history/java/java-21.md) — `record` 패턴 정식화(JEP 440)와 `switch` 패턴 매칭
- [`../27-equals-hashcode-contract/`](../27-equals-hashcode-contract/) — **`equals`/`hashCode` 계약 다섯 조항과 위반 증상이 정본이다.**\
  여기는 그 위에서 **`record` 가 그 계약을 대신 지켜 주는 범위**(컴포넌트 단위 비교·`final` 이라 대칭성 문제 없음)와 **배열에서 뚫리는 구멍**만 다룬다
- [`../../../../oop-basics/`](../../../../oop-basics/) — **캡슐화·불변 개념이 정본이다.**\
  여기는 **자바 문법이 그 개념을 어디까지 강제하나**(필드의 `final` 까지, 가리켜진 객체는 아님)를 본다
- [`../../../../../data-structure/05-hashmap/`](../../../../../data-structure/05-hashmap/) — 해시 테이블의 원리. `record` 를 키로 쓸 때의 전제가 거기 있다
- [`../../../../../engineering/design-patterns-gof/`](../../../../../engineering/design-patterns-gof/) — Value Object·빌더 패턴. `record` 가 대체하는 것과 대체 못 하는 것(빌더)의 배경
- [`../../언어-특성/README.md`](../../언어-특성/README.md) — GC·JIT·클래스로더·메모리 모델. **이 문서는 그것을 다시 쓰지 않는다**
- [`../06-initialization-order/`](../06-initialization-order/) — `record` 의 `static` 필드 초기화도 같은 규칙을 따른다(`static final User ANONYMOUS = ...`)
- [`../12-nested-classes/`](../12-nested-classes/) — 지역 `record` 가 지역 클래스와 다른 점(암묵적 `static`, 캡처 없음)의 정본
- [`../13-enum-classes/`](../13-enum-classes/) — `enum` 도 컴파일러가 멤버를 자동 생성하고 상속이 막힌 타입이다. 「자동 생성 + 제한」의 짝
- [`../15-sealed-classes/`](../15-sealed-classes/) — `sealed` 인터페이스 + `record` 구현체가 패턴 매칭의 기본 조합
- [**09번 주제**](../09-inheritance-overriding/)(상속과 오버라이딩) — 동적 디스패치·`final` 의 의미
- [**11번 주제**](../11-interfaces-default-methods/)(인터페이스 — `default`/`static`/`private` 메서드) — `record` 가 유일하게 할 수 있는 상속 비슷한 것(`implements`)
- [**22번 주제**](../22-instanceof-type-patterns/)(`instanceof` 타입 패턴) · [**24번 주제**](../24-record-patterns/)(`record` 패턴 — 중첩 해체) — 해체 문법은 거기가 정본
- [**59번 주제**](../59-immutable-objects/)(불변 객체 만들기 — 방어적 복사·`record` 와의 조합) — **방어 복사 관용구 자체가 정본이다.**\
  여기는 **`record` 에서 그 관용구를 어디에 넣나**(컴팩트 생성자 + 접근자)만 다룬다
- [**53번 주제**](../53-bigdecimal/)(`BigDecimal`) — 「어디서 틀리나」 4번의 대안

## 용어 풀이

- **`record`** — 고정된 값 묶음을 나르는 타입. `final` 이고 `java.lang.Record` 를 상속하며 멤버 대부분이 자동 생성된다. Java 16 정식.
- **컴포넌트(record component)** — 헤더 괄호 안의 항목 하나. `private final` 필드 + 같은 이름의 `public` 접근자로 펼쳐진다.
- **레코드 디스크립터(record descriptor)** — 헤더에 적힌 컴포넌트 목록 전체. `equals`/`hashCode`/`toString` 이 이걸 기준으로 만들어진다.
- **표준 생성자(canonical constructor)** — 컴포넌트와 같은 순서·타입의 파라미터를 받는 생성자. `record` 마다 정확히 하나.
- **컴팩트 생성자(compact constructor)** — 괄호를 생략한 표준 생성자 표기. 본문 끝의 필드 대입을 컴파일러가 넣어 준다.
- **보조 생성자** — 파라미터가 다른 생성자. 첫 문장이 반드시 `this(...)` 여야 한다.
- **접근자(accessor)** — 컴포넌트 값을 주는 메서드. 이름은 `getX()` 가 아니라 `x()`.
- **얕은 불변(shallow immutability)** — 필드에 담긴 값은 고정되지만 그 값이 가리키는 객체의 내부는 막지 못하는 상태.
- **방어 복사(defensive copy)** — 받을 때·줄 때 가변 객체의 복사본을 쓰는 것. `record` 에서는 컴팩트 생성자와 접근자 양쪽이 자리다.
- **`invokedynamic`** — 호출 대상을 첫 실행 때 부트스트랩 메서드가 정하는 JVM 명령. `record` 의 세 메서드와 람다가 이걸 쓴다.
- **부트스트랩 메서드(bootstrap method)** — `invokedynamic` 이 처음 실행될 때 호출 대상을 만들어 주는 정적 메서드. `record` 는 `ObjectMethods.bootstrap`.
- **`Record` 속성** — 클래스 파일에 박히는 컴포넌트 목록. 이 덕분에 컴포넌트 이름이 런타임에 남는다.
- **`@implSpec`** — javadoc 태그 중 **구현이 지켜야 할 명세**를 적는 칸. "이 메서드가 무엇을 보장하나"의 정본.
- **복사 불변식** — `r.equals(new R(r.c1(), ..., r.cn()))` 가 반드시 참이어야 한다는 `Record` javadoc 의 요구.
- **제한 식별자(restricted identifier)** — 특정 자리에서만 키워드로 취급되는 이름. `record`·`sealed`·`permits`·`var` 가 그렇다.

---

## 더 들어가면

- **`record` 의 직렬화는 표준 생성자를 거친다.**\
  `Record.java` 의 `@apiNote` 가 적은 대로 "During deserialization the record's canonical constructor is invoked to construct the record object. Certain serialization-related methods, such as `readObject` and `writeObject`, **are ignored** for serializable records."\
  일반 클래스의 역직렬화는 생성자를 건너뛰어 **검증을 통째로 우회**하는데, `record` 는 그러지 않는다 — 컴팩트 생성자의 검증이 역직렬화에도 걸린다.\
  대신 `readObject` 로 하던 커스터마이즈는 못 한다.\
  **실행 결과** (`Ex.java (14-ser)`, JDK 21.0.5 — 같은 값을 직렬화했다 되읽었다):

  ```text
  --- 만들 때 ---
      [record 컴팩트 생성자 실행] x=5
      [일반 클래스 생성자 실행] x=5
  --- 역직렬화할 때 ---
      [record 컴팩트 생성자 실행] x=5
  record  -> RecPoint[x=5]
  일반 클래스 -> ClsPoint[x=5]
  ```

  되읽을 때 **record 쪽만 생성자 줄이 한 번 더 찍혔다.** 일반 클래스는 생성자를 건너뛰었다.
- **컴팩트 생성자의 파라미터는 `final` 이 아니다.**\
  그래서 `lo = Math.max(lo, 0)` 이 된다. 반면 같은 이름의 **필드**는 `final` 이라 `this.lo = ...` 가 막힌다.\
  "record 는 전부 final" 이라는 한 줄 요약이 이 자리에서 오해를 만든다.
- **`ObjectMethods.bootstrap` 은 `equals`·`hashCode`·`toString` 세 이름을 한 부트스트랩이 처리한다.**\
  `BootstrapMethods:` 항목이 `0:` 하나뿐이고 세 `invokedynamic` 이 전부 `#0` 을 가리킨다 — 무엇을 만들지는 호출 지점의 이름(`equals`/`hashCode`/`toString`)으로 갈린다.
- **`record` 컴포넌트에 애너테이션을 달면 어디로 가나**는 애너테이션의 `@Target` 이 정한다.\
  필드·파라미터·접근자·`Record` 속성 중 **적용 가능한 자리 전부**로 퍼진다(JLS §8.10.3).\
  **실행 결과** (`Ex.java (14-ann)`, JDK 21.0.5 — `@Wide` 는 `@Target` 이 넷, `@OnlyField` 는 `FIELD` 하나):

  ```text
  필드       : Wide OnlyField
  접근자     : Wide
  생성자 파라미터: Wide
  레코드 컴포넌트: Wide
  ```

  `@Target` 이 넓은 것은 네 자리에 전부 퍼지고, `FIELD` 하나뿐인 것은 **필드에만** 남았다.\
  그래서 접근자만 보는 검증 프레임워크는 `@OnlyField` 를 못 본다 — 애너테이션 자체는 [**16번 주제**](../16-annotations/)가 정본이다.
- **`record` 는 값 타입(Valhalla)의 예고가 아니다.**\
  `record` 는 여전히 힙에 놓이는 참조 객체다. `==` 는 `false` 였다(14-a). 식별자 없는 값 타입은 별개의 프로젝트다.
