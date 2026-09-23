# java/syntax/29 — 람다: 문법·변수 캡처·`this` 의 의미 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **선행** — [**11번 주제**](../11-interfaces-default-methods/)(인터페이스 `default`/`static` 메서드). 람다가 들어갈 자리가 어떤 타입인지 먼저 본다.
> **기준 소스** — 이 머신의 `21.0.5-tem/lib/src.zip` 에서 **직접 읽은** `java/lang/invoke/LambdaMetafactory.java` · `java/lang/FunctionalInterface.java`,
> 그리고 `javac` 가 실제로 낸 에러 메시지.
> [JLS SE 21 §15.27](https://docs.oracle.com/javase/specs/jls/se21/html/jls-15.html#jls-15.27) 은 이 작업에서 **본문을 열지 못했다** — 그래서 본문의 「보장」 판정은 **javadoc 원문과 컴파일러 에러**만 근거로 삼았다.
> **실행 검증** — 이 문서의 모든 출력·에러·역어셈블은 Temurin **JDK 21.0.5** 에서 실제로 돌려 얻은 것이다.\
> 프로그램 17개(+ 직렬화 바이트를 들여다보는 보조 2개)를 **17.0.13 · 21.0.5 · 25.0.1** 세 JDK 에서 각각 돌렸다.\
> **세 버전에서 달랐던 것이 있다** — 「구현 세부사항 대 언어 보장」 절에 모아 두었다.
> **버전** — 람다는 **Java 8**. 이 주제에 21·25 에서 새로 생긴 문법은 없다.
> **범위** — 람다·`invokedynamic` 이 **왜 그때 들어왔나**는 [`../../../../../../history/java/java-8.md`](../../../../../../history/java/java-8.md) 가 정본이다.\
> JIT·클래스로딩 같은 **JVM 내부**는 [`../../언어-특성/README.md`](../../언어-특성/README.md) 가 정본이다.\
> 여기는 **소스에서 어떻게 쓰고, 컴파일러가 무엇을 만들고, 무엇을 못 하나** — 바이트코드 표면까지다.
> 이 본문은 Claude 작성이다(원고 없음).

## 한눈에 — 쉽게 말하면

**익명 클래스는 사람을 새로 뽑는 것이고, 람다는 내가 하던 일에 쪽지를 붙이는 것이다.**

| 비유 | 실체 |
|---|---|
| 새 직원을 뽑아 책상과 이름표를 준다 | 익명 클래스 — `Ex$1.class` 파일이 생긴다 |
| 그 직원이 "나"라고 하면 그 직원 자신이다 | 익명 클래스의 `this` — 자기 자신 |
| 내가 하던 일에 쪽지 한 장을 붙인다 | 람다 — 클래스 파일이 **안 생긴다** |
| 쪽지에 "이건 내가 한다"라고 적혀 있다 | 람다의 `this` — **바깥 인스턴스** |
| 쪽지에 값을 **적어 준다** | 캡처 — 값 복사 |
| 적어 준 뒤 내 수첩을 고쳐도 쪽지는 그대로다 | 그래서 지역 변수는 effectively final 이어야 한다 |
| 회사 안에서만 통하는 내부 번호 | 합성 메서드 `lambda$main$0` |

```text
        익명 클래스                                람다

  new Runnable() { ... }                     () -> { ... }
        |                                          |
        v                                          v
  Ex$1.class 파일이 생긴다                  클래스 파일이 안 생긴다
  새 객체가 하나 만들어진다                  실행할 때 JVM 이 만든다
        |                                          |
  그 안의 this = Ex$1 인스턴스                그 안의 this = 바깥 Ex 인스턴스
```

**똑같은 구조로** Java 가 이렇게 동작한다 — 익명 클래스는 **새 타입**을 만들고, 람다는 **바깥 메서드 안의 코드 조각**으로 남는다.

실무에서 이게 값을 내는 자리는 **`this` 로 바깥 객체를 쓸 때**다.\
익명 클래스 안에서는 `Ex.this.field` 라고 길게 써야 하지만, 람다 안에서는 그냥 `field` 다.\
반대로 **자기 자신을 가리켜야 하는 코드**(재귀 리스너 해제 등)는 람다로 못 쓴다.

> **람다식(lambda expression)** — 함수형 인터페이스의 인스턴스를 만드는 식. `(인자) -> 본문` 꼴이다.\
> 예: `Runnable r = () -> System.out.println("안녕");` 는 `Runnable` 을 구현한 객체 하나를 만든다.

> **캡처(capture)** — 람다가 바깥 문맥의 값을 자기 안으로 가져오는 것.\
> 예: `int n = 3; Supplier<Integer> s = () -> n;` 에서 `n` 의 값 3이 람다로 들어간다.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. 람다는 **무엇으로 컴파일되나** — 익명 클래스와 같은 것인가 다른 것인가.
2. 캡처는 **무엇을 가져오나** — 값인가 변수인가. 왜 effectively final 이 필요한가.
3. 람다 안의 **`this`·`super`·이름**은 무엇을 가리키나 — 익명 클래스와 어디가 갈리나.

## 동작 방식

### (1) 람다는 클래스 파일을 만들지 않는다

**언제 쓰나** — "람다는 익명 클래스의 짧은 문법"이라고 알고 있을 때. 빌드 산출물 수를 따질 때.

**입력 코드** (`Ex.java (29-c)`)

```java
int captured = 42;

Supplier<String> noCapture  = () -> "상수";                  // 캡처 없음
Supplier<String> yesCapture = () -> "값 " + captured;        // 지역 변수 캡처
Supplier<String> anon = new Supplier<String>() {             // 익명 클래스
    public String get() { return "값 " + captured; }
};
```

람다가 둘, 익명 클래스가 하나다. 컴파일하면 클래스 파일이 몇 개 나오나.

**실행 결과** — `javac Ex.java` 뒤의 `ls *.class`

```text
Ex$1.class
Ex.class
```

```text
익명 클래스 3개를 썼다면                   람다 3개를 썼다면

  Ex.class                                  Ex.class
  Ex$1.class                                (끝)
  Ex$2.class
  Ex$3.class
     |                                         |
  클래스 파일 4개                            클래스 파일 1개
  로딩할 클래스 4개                          로딩할 클래스 1개
```

그림 해설 (한 단계씩):

- 람다 **둘**을 썼는데 `Ex$2.class`·`Ex$3.class` 가 없다.
- 있는 `Ex$1.class` 는 **익명 클래스 하나** 몫이다.
- 즉 **람다는 컴파일 시점에 타입을 만들지 않는다.**
- 그러면 실행할 때 그 객체는 어디서 오나 — (2)가 그 답이다.

비용 — 클래스 파일 수·클래스로딩 수가 줄어든다.\
대신 **첫 실행에서 런타임이 클래스를 만드는 비용**이 생긴다(부트스트랩, (2) 참조).

### (2) `invokedynamic` + `LambdaMetafactory` — 객체를 실행 시점에 만든다

**언제 쓰나** — 람다가 "무엇으로" 컴파일되는지 확인할 때. 스택트레이스가 이상할 때.

**역어셈블** (`Ex.java (29-c)` · `javap -c -p Ex.class`)

```text
  public static void main(java.lang.String[]);
    Code:
       0: bipush        42
       2: istore_1
       3: invokedynamic #7,  0              // InvokeDynamic #0:get:()Ljava/util/function/Supplier;
       8: astore_2
       9: iload_1
      10: invokedynamic #11,  0             // InvokeDynamic #1:get:(I)Ljava/util/function/Supplier;
      15: astore_3
      16: new           #14                 // class Ex$1
      19: dup
      20: iload_1
      21: invokespecial #16                 // Method Ex$1."<init>":(I)V
      24: astore        4
```

그림 해설 (한 단계씩):

- 람다 자리에 **`invokedynamic`** 하나가 있다. `new` 가 없다.
- 익명 클래스 자리에는 `new Ex$1` + `invokespecial <init>` 가 그대로 있다 — **평범한 객체 생성**이다.
- `invokedynamic` 이 무엇을 부르는지는 클래스 파일 끝의 `BootstrapMethods` 표에 있다.

**역어셈블** (`javap -v -p Ex.class` 의 끝부분)

```text
BootstrapMethods:
  0: #72 REF_invokeStatic java/lang/invoke/LambdaMetafactory.metafactory:(Ljava/lang/invoke/MethodHandles$Lookup;Ljava/lang/String;Ljava/lang/invoke/MethodType;Ljava/lang/invoke/MethodType;Ljava/lang/invoke/MethodHandle;Ljava/lang/invoke/MethodType;)Ljava/lang/invoke/CallSite;
    Method arguments:
      #60 ()Ljava/lang/Object;
      #61 REF_invokeStatic Ex.lambda$main$0:()Ljava/lang/String;
      #64 ()Ljava/lang/String;
  1: #72 REF_invokeStatic java/lang/invoke/LambdaMetafactory.metafactory:(Ljava/lang/invoke/MethodHandles$Lookup;Ljava/lang/String;Ljava/lang/invoke/MethodType;Ljava/lang/invoke/MethodType;Ljava/lang/invoke/MethodHandle;Ljava/lang/invoke/MethodType;)Ljava/lang/invoke/CallSite;
    Method arguments:
      #60 ()Ljava/lang/Object;
      #65 REF_invokeStatic Ex.lambda$main$1:(I)Ljava/lang/String;
      #64 ()Ljava/lang/String;
```

```text
컴파일 시점                     첫 실행                        그 뒤

  invokedynamic  ──부트스트랩──>  LambdaMetafactory       ──>  만들어 둔 객체를
  (호출 자리만 있다)              .metafactory(...)             그냥 돌려준다
                                      |
                                      v
                             Supplier 를 구현한 클래스를
                             그 자리에서 만들어 낸다
```

그림 해설 (한 단계씩):

- 부트스트랩 메서드가 **`LambdaMetafactory.metafactory`** 다. 이것이 람다 객체의 공장이다.
- 두 번째 인자(`REF_invokeStatic Ex.lambda$main$0`)가 **실제 본문**이다 — 컴파일러가 만든 합성 메서드를 가리킨다.
- 첫 실행에서 호출 자리가 한 번 「연결(linkage)」되고, 그 뒤로는 만들어진 공장을 재사용한다.
- 그래서 **클래스 파일에는 타입이 없고 실행 중에 생긴다.**

비용 — 첫 호출에 부트스트랩 비용이 든다. 그 뒤는 일반 인터페이스 호출과 같다.

> **`invokedynamic`** — "무엇을 부를지 첫 실행에서 정한다"는 바이트코드 명령. 연결된 뒤에는 그 결정을 재사용한다.\
> 예: 람다 자리, 그리고 이 출력에 같이 보이는 문자열 이어붙이기(`makeConcatWithConstants`)가 이것을 쓴다.

> **합성 메서드(synthetic method)** — 소스에 없는데 컴파일러가 만들어 넣은 메서드. `ACC_SYNTHETIC` 플래그가 붙는다.\
> 예: `lambda$main$0` 은 내가 쓴 적 없지만 클래스 파일에 있다.

### (3) ★ 캡처하는 람다와 안 하는 람다는 합성 메서드 시그니처가 다르다

**언제 쓰나** — 캡처가 "값 복사"라는 말의 근거를 볼 때. 캡처 비용을 따질 때.

**역어셈블** (`Ex.java (29-c)` · `javap -c -p Ex.class` 의 뒷부분)

```text
  private static java.lang.String lambda$main$1(int);
    Code:
       0: iload_0
       1: invokedynamic #42,  0             // InvokeDynamic #3:makeConcatWithConstants:(I)Ljava/lang/String;
       6: areturn

  private static java.lang.String lambda$main$0();
    Code:
       0: ldc           #45                 // String 상수
       2: areturn
```

```text
캡처 없는 람다                              캡처 있는 람다

  () -> "상수"                               () -> "값 " + captured
       |                                          |
       v                                          v
  lambda$main$0()                            lambda$main$1(int)
  인자 0개                                    인자 1개  <- 캡처한 값이 인자다
       |                                          |
  indy: get:()Ljava/.../Supplier;            indy: get:(I)Ljava/.../Supplier;
  호출 자리에 넘기는 값 없음                   호출 자리에 int 를 넘긴다
       |                                          |
  객체를 만들 것이 없다                        int 를 담은 객체를 새로 만든다
```

그림 해설 (한 단계씩):

- 두 합성 메서드의 **인자 개수가 다르다** — `()` 대 `(int)`.
- 캡처한 값은 합성 메서드의 **인자로 들어간다.** 본문에서 `iload_0` 으로 읽는다.
- 호출 자리의 `invokedynamic` 서술자도 다르다 — `()→Supplier` 대 `(I)→Supplier`.\
  `(I)` 는 "이 호출 자리에 `int` 하나를 넘겨야 한다"는 뜻이고, 앞줄의 `iload_1` 이 그것을 올린다.
- **캡처한 것은 변수가 아니라 값이다** — 스택에서 읽어 인자로 밀어 넣었을 뿐이다.\
  그래서 나중에 바깥 변수를 바꿔도 이미 넘어간 값은 안 바뀐다.
- 이것이 effectively final 규칙의 이유다 — 값 하나만 넘기므로 **바꿀 수 있으면 둘이 갈라진다.**

**비교 — 익명 클래스는 필드에 담는다** (`javap -c -p 'Ex$1.class'`)

```text
class Ex$1 implements java.util.function.Supplier<java.lang.String> {
  final int val$captured;

  Ex$1();
    Code:
       0: aload_0
       1: iload_1
       2: putfield      #1                  // Field val$captured:I
```

- 익명 클래스도 **같은 일을 한다** — 생성자 인자로 받아 `final` 필드에 넣는다.
- 이름이 `val$captured` 다. `val$` 접두어가 "캡처한 지역 변수"라는 표시다.
- **둘 다 값 복사**다. 방식만 인자냐 필드냐로 다르다.

비용 — 캡처 없는 람다는 만들 것이 없어 **재사용될 수 있다**((6) 참조).\
캡처 있는 람다는 **캡처할 때마다 객체 하나**가 후보가 된다.

### (4) ★ `this` 를 캡처하면 합성 메서드가 static 이 아니게 된다

**언제 쓰나** — "람다 안의 `this` 는 바깥 인스턴스"라는 말의 근거를 볼 때.

**입력 코드** (`Ex.java (29-h)`)

```java
private int field = 7;

void run() {
    Supplier<String> usesThis = () -> "필드 " + field;    // this 를 캡처한다
    Supplier<String> pure     = () -> "상수";             // 아무것도 캡처 안 한다
    System.out.println(usesThis.get() + " / " + pure.get());
}
```

**역어셈블** (`javap -c -p Ex.class`)

```text
  void run();
    Code:
       0: aload_0
       1: invokedynamic #13,  0             // InvokeDynamic #0:get:(LEx;)Ljava/util/function/Supplier;
       6: astore_1
       7: invokedynamic #17,  0             // InvokeDynamic #1:get:()Ljava/util/function/Supplier;
      12: astore_2

  private static java.lang.String lambda$run$1();
    Code:
       0: ldc           #47                 // String 상수
       2: areturn

  private java.lang.String lambda$run$0();
    Code:
       0: aload_0
       1: getfield      #7                  // Field field:I
       4: invokedynamic #49,  0             // InvokeDynamic #3:makeConcatWithConstants:(I)Ljava/lang/String;
       9: areturn
```

```text
필드를 쓴 람다                              아무것도 안 쓴 람다

  private String lambda$run$0()             private static String lambda$run$1()
       static 가 없다!                            static 이 있다
       |                                          |
  인스턴스 메서드 = 수신 객체가 있다          static = 수신 객체가 없다
       |                                          |
  aload_0 = this                             ldc "상수"
  getfield field                             (this 를 안 쓴다)
       |                                          |
  호출 자리: get:(LEx;)                       호출 자리: get:()
  Ex 인스턴스를 넘긴다                        아무것도 안 넘긴다
```

그림 해설 (한 단계씩):

- `lambda$run$0` 에는 **`static` 이 없다.** 인스턴스 메서드다.
- 그 본문의 `aload_0` 은 **`this`** 다 — 바깥 `Ex` 인스턴스.
- 호출 자리에서 `aload_0` 으로 `this` 를 올린 뒤 `invokedynamic ... (LEx;)` 로 넘긴다.\
  **바깥 `this` 가 캡처된 값**인 것이다.
- 그래서 「람다 안의 `this` 는 바깥 인스턴스」는 수사가 아니라 **바이트코드 그대로**다.
- 캡처가 없는 쪽은 `static` 이라 수신 객체 자체가 없다.

비용 — `this` 를 캡처하는 람다는 **바깥 인스턴스를 붙잡는다.**\
그 람다를 오래 사는 자료구조(캐시·리스너 목록)에 넣으면 바깥 객체가 같이 산다.

### (5) ★ 람다의 `this` 와 익명 클래스의 `this` — 같은 프로그램에서

**언제 쓰나** — 익명 클래스를 람다로 바꿀 때. 리스너·콜백을 옮길 때.

**입력 코드** (`Ex.java (29-a)`)

```java
public class Ex {
    private String name = "바깥 Ex 인스턴스";
    public String toString() { return name; }

    void run() {
        Runnable lam = () -> {
            System.out.println("람다   this          = " + this);
            System.out.println("람다   this.getClass = " + this.getClass().getName());
            System.out.println("람다   name          = " + name);
        };

        Runnable anon = new Runnable() {
            private String name = "익명 클래스 자기 자신";
            public String toString() { return name; }
            public void run() {
                System.out.println("익명   this          = " + this);
                System.out.println("익명   this.getClass = " + this.getClass().getName());
                System.out.println("익명   name          = " + name);
                System.out.println("익명   Ex.this.name  = " + Ex.this.name);
            }
        };
        ...
    }
}
```

**실행 결과** (17 · 21 · 25 에서 한 글자도 다르지 않았다)

```text
== 람다 안의 this ==
람다   this          = 바깥 Ex 인스턴스
람다   this.getClass = Ex
람다   name          = 바깥 Ex 인스턴스
== 익명 클래스 안의 this ==
익명   this          = 익명 클래스 자기 자신
익명   this.getClass = Ex$1
익명   name          = 익명 클래스 자기 자신
익명   Ex.this.name  = 바깥 Ex 인스턴스
== 바깥에서 본 this ==
바깥   this          = 바깥 Ex 인스턴스
바깥   this.getClass = Ex
```

```text
람다 안                                    익명 클래스 안

  this        -> 바깥 Ex 인스턴스            this        -> Ex$1 인스턴스
  this.getClass -> Ex                       this.getClass -> Ex$1
  name        -> 바깥 Ex 의 name             name        -> 익명 클래스가 새로 선언한 name
  (바깥 것을 가릴 수단이 없다)               Ex.this.name -> 바깥 Ex 의 name
       |                                          |
  새 스코프가 열리지 않는다                   새 클래스 스코프가 열린다
```

그림 해설 (한 단계씩):

- **`this` 가 갈린다.** 람다 안은 바깥 `Ex`, 익명 클래스 안은 `Ex$1`.
- **`this.getClass()` 도 갈린다.** 람다 쪽이 `Ex` 라는 것이 (1)의 「클래스 파일이 안 생긴다」와 같은 사실이다.\
  (람다 객체 자신의 클래스는 `Ex$$Lambda/0x...` 인데, **`this` 는 그것이 아니다** — (6) 참조.)
- **이름 해석도 갈린다.** 익명 클래스는 `name` 을 새로 선언해 바깥 것을 가렸고, 바깥 것은 `Ex.this.name` 으로만 닿는다.
- 람다에는 **가릴 방법이 아예 없다** — 같은 이름을 다시 선언하면 컴파일 에러다(「어디서 틀리나」 3번).
- 바깥에서 본 `this` 와 람다 안의 `this` 가 같다 — **람다는 새 스코프를 열지 않는다.**

비용 — 익명 클래스를 람다로 바꿀 때 `this` 가 든 코드는 **조용히 뜻이 바뀐다.**\
컴파일이 되어 버리는 경우가 있으므로(둘 다 어떤 메서드를 갖고 있으면) 기계적 치환이 위험하다.

### (6) 람다 객체는 실행 시점에 생기고, 같은 것이 재사용될 수 있다

**언제 쓰나** — 람다를 `==` 로 비교하거나 `Set` 에 넣을 때. 리스너를 해제하려 할 때.

**실행 결과** (`Ex.java (29-f)` · JDK 21.0.5)

```text
캡처 없는 람다의 런타임 클래스 = Ex$$Lambda/0x000073da900009f8
캡처 있는 람다의 런타임 클래스 = Ex$$Lambda/0x000073da90000c08

캡처 없음  a == b ? true
캡처 있음  c == d ? false
캡처 있음  c.equals(d) ? false

같은 람다식인데 클래스도 같나 ? true
다른 람다식이면 ? false

a.toString() = Ex$$Lambda/0x000073da900009f8@511d50c0
isSynthetic  = true
isHidden     = true
인터페이스   = [interface java.util.function.Supplier]
```

```text
캡처 없는 람다                              캡처 있는 람다

  makeNoCapture() 를 두 번 불렀다            makeCapture(1) 을 두 번 불렀다
       |                                          |
  a == b  ->  true                           c == d  ->  false
  같은 객체를 돌려줬다                        새 객체를 두 개 만들었다
       |                                          |
  담을 상태가 없으니 하나면 된다               담은 값이 있으니 각각 필요하다
       |                                          |
  ★ 그래도 보장은 아니다 — 아래 「구현 세부사항 대 언어 보장」
```

그림 해설 (한 단계씩):

- 런타임 클래스 이름이 `Ex$$Lambda/0x...` 다 — 소스에도 클래스 파일에도 없던 이름이다.
- `isHidden()` 이 `true` 다. **숨은 클래스**라 이름으로 찾을 수도, 클래스로더에서 조회할 수도 없다.
- 캡처 없는 쪽은 두 번 불러도 **같은 객체**가 나왔다.
- 캡처 있는 쪽은 **값이 같아도** 다른 객체이고 `equals` 도 `false` 다.\
  람다는 `equals` 를 재정의하지 않는다 — `Object` 의 것, 즉 참조 비교다.
- 그래서 **람다를 기억해 두지 않으면 나중에 같은 것을 다시 못 만든다.**\
  `removeListener(x -> ...)` 가 안 먹는 이유가 이것이다.

비용 — 캡처 없는 람다는 객체 재사용이 가능해 싸다.\
하지만 **그 재사용을 코드가 의존해서는 안 된다**(바로 아래 절).

## 문법 — 형태와 규칙

직접 쓴 최소 예제다. 출력은 전부 실행 결과다.

### 네 가지 본문 형태

```java
// 1. 인자 0개 + 식 본문
Supplier<String> a = () -> "값";

// 2. 인자 1개 + 괄호 생략
Function<String, Integer> b = s -> s.length();

// 3. 인자 여럿 + 타입 생략 (타깃 타입에서 추론)
BiFunction<Integer, Integer, Integer> c = (x, y) -> x + y;

// 4. 블록 본문 — return 이 필요하다
Function<String, Integer> d = s -> { int n = s.length(); return n * 2; };
```

| 쓰는 곳 | 규칙 |
|---|---|
| 인자 타입 | 전부 쓰거나 전부 생략한다. 섞을 수 없다 |
| `var` 인자 | `(var x, var y) -> ...` 로 **전부 `var`** 는 된다 (11+). 생략과 섞으면 에러 |
| 인자 하나 | 괄호를 생략할 수 있다. 단 **타입을 쓰면 괄호가 필요하다** |
| 식 본문 | `return` 을 쓰지 않는다. 그 값이 반환값이다 |
| 블록 본문 | `{ }` 안에 문장. 값을 돌려주려면 `return` |
| `void` 자리 | 값을 돌려주는 식도 넣을 수 있다 — [`../31-functional-interfaces/`](../31-functional-interfaces/) 「어디서 틀리나」 |

**되는 것** (`Ex.java (29-k)` · 17 · 21 · 25 동일)

```java
BiFunction<Integer,Integer,Integer> a = (var x, var y) -> x + y;   // 전부 var (11+)
Function<String,Integer> b = (String s) -> s.length();             // 타입 + 괄호
Function<String,Integer> c = s -> s.length();                      // 생략 + 괄호 생략
```

```text
3 3 5
```

**`var` 와 생략을 섞으면** (`Ex.java (29-l)`)

```text
Ex.java:5: error: invalid lambda parameter declaration
        BiFunction<Integer,Integer,Integer> a = (var x, y) -> x + y;   // 섞으면?
                                                ^
  (cannot mix 'var' and implicitly-typed parameters)
1 error
```

**타입을 쓰고 괄호를 빼면** (`Ex.java (29-m)`)

```text
Ex.java:5: error: ';' expected
        Function<String,Integer> c = String s -> s.length();   // 타입을 쓰고 괄호를 뺀다
                                           ^
Ex.java:5: error: not a statement
        Function<String,Integer> c = String s -> s.length();   // 타입을 쓰고 괄호를 뺀다
                                            ^
2 errors
```

- 둘째 에러는 **파서 단계**에서 난다 — 메시지가 람다를 아예 언급하지 않는다.  `';' expected` 가 나오면 람다 인자 괄호부터 의심한다.

### 캡처할 수 있는 것과 없는 것

**실행 결과** (`Ex.java (29-b)`)

```text
만들 때   : 지역 10 / 필드 1 / static 100 / 배열칸 1000
바꾼 뒤   : 지역 10 / 필드 2 / static 200 / 배열칸 2000
-- 지역 변수 10 만 그대로다 --

== 참조 캡처는 객체를 얼리지 않는다 ==
만들 때   : sb = 처음
바꾼 뒤   : sb = 처음+덧붙임
```

| 대상 | 캡처 뒤에 바꿀 수 있나 | 람다가 보는 값 |
|---|---|---|
| 지역 변수 | **못 바꾼다** (컴파일 에러) | 캡처할 때의 값 |
| 인스턴스 필드 | 바꿀 수 있다 | **바꾼 뒤의 값** |
| `static` 필드 | 바꿀 수 있다 | **바꾼 뒤의 값** |
| 배열 원소·객체 내부 | 바꿀 수 있다 | **바꾼 뒤의 값** |
| 메서드 인자 | 못 바꾼다 (지역 변수와 같다) | 캡처할 때의 값 |

- **필드는 `this` 를 캡처하는 것**이므로 값이 아니라 **객체를 붙잡는다.**\
  그래서 필드 값의 변경이 람다에 보인다.
- 배열 한 칸을 우회로 쓰는 관용구(`int[] box = {0}`)가 여기서 나온다.\
  다만 그 우회가 필요해졌다면 **설계를 먼저 의심한다** — [`../03-variables-and-assignment/`](../03-variables-and-assignment/) 와 이어진다.

### 루프 변수는 어느 for 인가에 따라 갈린다

**실행 결과** (`Ex.java (29-i)`)

```text
향상된 for : 가나다
기본 for + 사본 : 012
```

```java
for (String s : List.of("가","나","다")) subs.add(() -> s);   // 된다
for (int i = 0; i < 3; i++)              subs.add(() -> "" + i);  // 컴파일 에러
for (int i = 0; i < 3; i++) { int copy = i; subs.add(() -> "" + copy); }  // 된다
```

- **향상된 `for` 의 변수는 회전마다 새로 만들어진다** — 그래서 effectively final 이다.
- 기본 `for` 의 인덱스는 **하나를 계속 바꾼다** — 캡처할 수 없다.
- 회전 안에서 새 지역 변수를 만들면 된다. 사본이 회전마다 따로 생기기 때문이다.

### `this`·`super`·이름의 규칙 한 표

| 쓰는 것 | 람다 안 | 익명 클래스 안 |
|---|---|---|
| `this` | **바깥 인스턴스** | **자기 자신** |
| 바깥 인스턴스에 닿기 | `this` (그냥) | `Ex.this` |
| `super.m()` | **바깥 클래스의 부모** | 익명 클래스가 구현한 타입의 부모 |
| 바깥 지역 변수 이름 다시 선언 | **컴파일 에러** | 된다 (가린다) |
| 바깥 필드 이름 다시 선언 | (필드는 선언할 수 없다) | 된다 (가린다) |
| `static` 문맥에서 `this` | **컴파일 에러** | 컴파일 에러 |

## 어디서 틀리나

### 1. 캡처 뒤에 지역 변수를 바꾼다

**컴파일 에러** (`Ex.java (29-e1)`)

```text
Ex.java:6: error: local variables referenced from a lambda expression must be final or effectively final
        Supplier<Integer> s = () -> count;
                                    ^
1 error
```

- 에러는 **대입한 줄이 아니라 캡처한 줄**을 가리킨다. 원인을 찾을 때 헷갈리는 자리다.
- 대입이 **람다보다 뒤에 있어도** 걸린다 — 컴파일러는 메서드 전체를 보고 판정한다.
- 해결: 대입을 지우거나, 값을 새 지역 변수에 복사해 그것을 캡처한다.

> **effectively final** — `final` 이라고 안 썼지만 **초기화 뒤 한 번도 대입되지 않은** 지역 변수.\
> 예: `int n = 3;` 뒤에 `n` 에 아무것도 대입하지 않으면 `n` 은 effectively final 이다.

### 2. 람다 안에서 캡처 변수를 증가시킨다

**컴파일 에러** (`Ex.java (29-e2)`)

```text
Ex.java:6: error: local variables referenced from a lambda expression must be final or effectively final
        Supplier<Integer> s = () -> { count++; return count; };   // 람다 안에서 대입
                                      ^
Ex.java:6: error: local variables referenced from a lambda expression must be final or effectively final
        Supplier<Integer> s = () -> { count++; return count; };   // 람다 안에서 대입
                                                      ^
2 errors
```

- **에러가 둘**이다. 대입한 자리와 읽은 자리가 각각 걸린다.
- 세고 싶으면 배열 한 칸이나 `AtomicInteger` 를 쓴다.\
  단 람다가 병렬로 불리면 배열 우회는 **경쟁 조건**이 된다 — [**49번 주제**](../49-parallel-streams/).

### 3. 람다 안에서 바깥 지역 변수와 같은 이름을 선언한다

**컴파일 에러** (`Ex.java (29-e4)`)

```text
Ex.java:7: error: variable msg is already defined in method main(String[])
            String msg = "람다 안";        // 바깥 지역 변수와 같은 이름
                   ^
1 error
```

**대조 — 익명 클래스는 된다** (`Ex.java (29-e5)`)

```text
익명 클래스 안 / 바깥
```

- 람다는 **새 스코프를 열지 않는다.** 바깥 메서드의 지역 변수 이름을 그대로 물려받는다.
- 익명 클래스는 **새 클래스 본문**이라 가릴 수 있다.
- 에러 메시지가 `already defined in method main` 이다 — 「람다는 `main` 안이다」를 컴파일러가 말해 주고 있다.

### 4. `static` 문맥의 람다에서 `this` 를 쓴다

**컴파일 에러** (`Ex.java (29-e3)`)

```text
Ex.java:5: error: non-static variable this cannot be referenced from a static context
        Supplier<String> s = () -> this.toString();   // static 문맥의 this
                                   ^
1 error
```

- 람다의 `this` 는 바깥 문맥의 `this` 다. **바깥이 `static` 이면 `this` 가 없다.**
- 여기서도 「람다가 새 스코프를 만들지 않는다」가 그대로 나온다.
- 익명 클래스로 바꾸면 컴파일된다 — 그쪽은 자기 자신이 있기 때문이다.

### 5. 스택트레이스에 `lambda$main$0` 이 뜬다

**실행 결과** (`Ex.java (29-d)` · `Ex.` 로 시작하는 프레임은 17 · 21 · 25 에서 같았다)

```text
== 1. 람다에서 터졌을 때 ==
  at java.base/java.lang.NumberFormatException.forInputString(NumberFormatException.java:67)
  at java.base/java.lang.Integer.parseInt(Integer.java:662)
  at java.base/java.lang.Integer.parseInt(Integer.java:778)
  at Ex.lambda$main$0(Ex.java:9)
  at java.base/java.lang.Iterable.forEach(Iterable.java:75)
  at Ex.main(Ex.java:9)
== 2. 익명 클래스에서 터졌을 때 ==
  ...
  at Ex$1.accept(Ex.java:17)
  at Ex$1.accept(Ex.java:16)
  at java.base/java.lang.Iterable.forEach(Iterable.java:75)
  at Ex.main(Ex.java:16)
== 3. 메서드 참조에서 터졌을 때 ==
  ...
  at Ex.boom(Ex.java:4)
  at java.base/java.lang.Iterable.forEach(Iterable.java:75)
  at Ex.main(Ex.java:25)
```

```text
람다                        익명 클래스                  메서드 참조

Ex.lambda$main$0            Ex$1.accept                 Ex.boom
     |                           |                           |
숫자가 이름이다              클래스 번호가 이름이다        진짜 메서드 이름이다
람다 순서가 바뀌면 이름도    익명 클래스 순서가 바뀌면     이름이 안 바뀐다
바뀐다                       번호도 바뀐다
```

그림 해설 (한 단계씩):

- 세 경우 다 **줄 번호는 정확하다.** 어느 줄인지는 알 수 있다.
- 이름은 셋 다 다르다 — `lambda$main$0` 은 **몇 번째 람다인지**만 말한다.
- 익명 클래스는 같은 이름이 **두 줄** 나온다(`accept` 가 둘) — 제네릭 다리(bridge) 메서드 때문이다.
- **메서드 참조가 가장 읽기 좋다** — 실제 메서드 이름이 그대로 나온다.\
  이것이 [목록의 **30번 주제**](../30-method-references/)(이번 묶음)가 람다보다 나은 자리 중 하나다.
- 람다 객체 자신의 클래스(`Ex$$Lambda/0x...`)는 **스택트레이스에 안 나온다.**\
  JVM 이 그 프레임을 감춘다 — 「돌려 본 위 출력 그대로」가 근거다.

### 6. 람다를 그대로 직렬화하려 한다

**실행 결과** (`Ex.java (29-g)`)

```text
== 1. 보통 람다를 직렬화하면 ==
  java.io.NotSerializableException: Ex$$Lambda/0x00007c14440009f8
== 2. Serializable 을 섞은 함수형 인터페이스면 ==
  직렬화 성공, 바이트 수 = 532
  역직렬화 결과 = 안녕
  역직렬화된 것의 클래스 = Ex$$Lambda/0x00007c144400c000
== 3. 캐스트로 즉석에서 섞을 수도 있다 ==
  직렬화 성공, 바이트 수 = 548
```

- 람다는 **기본적으로 직렬화되지 않는다.** 타깃 타입이 `Serializable` 을 섞어야 한다.
- 되긴 하는데, **되고 나서가 문제**다 — 무엇이 저장되는지 보면 안다.

**실행 결과** — 직렬화된 바이트에서 뽑은 문자열 (`Ex2.java (29-g)` · `Ex3.java (29-g)`)

```text
  !java.lang.invoke.SerializedLambdaoa
  implMethodKind[
  capturedArgst
  capturingClasst
  functionalInterfaceClasst
  functionalInterfaceMethodNameq
  implClassq
  implMethodNameq
  implMethodSignatureq
  instantiatedMethodTypeq
  SerSupt
  gett
  ()Ljava/lang/Object;t
  Ex3t
  lambda$main$ef07458b$1t
  ()Ljava/lang/String;q
```

- 저장되는 것은 `SerializedLambda` 이고, 그 안에 **합성 메서드 이름이 문자열로 들어 있다.**
- 이름이 `lambda$main$ef07458b$1` 이다 — **해시가 박힌 이름**이다.\
  같은 클래스의 직렬화 불가 람다는 `lambda$main$0` 인데, 직렬화 가능 람다만 이 꼴이 된다.
- 그래서 **소스를 고치면 역직렬화가 깨진다.** 람다를 한 줄 위로 옮겨도 이름이 바뀐다.
- 직렬화 가능 람다는 부트스트랩도 다르다 — `altMetafactory` 를 쓰고, 클래스에 `$deserializeLambda$` 메서드가 생긴다.

```text
  private static java.lang.Object $deserializeLambda$(java.lang.invoke.SerializedLambda);
  private static java.lang.String lambda$main$ef07458b$1();
```

- 규칙: **람다를 저장하지 않는다.** 저장할 것은 데이터이지 코드가 아니다.

### 7. 람다를 `==` 로 비교하거나 해제하려 한다

- (6)절의 실행 결과 — 캡처 있는 람다는 같은 값으로 두 번 만들어도 `==` 도 `equals` 도 `false` 다.
- 리스너를 `remove(x -> ...)` 로 빼려 하면 **아무것도 안 빠진다.** 예외도 안 난다.
- 해결: 만든 람다를 **변수에 담아 두고 그 변수로 해제**한다.

## 구현 세부사항 대 언어 보장

이 주제는 관찰한 것과 보장된 것이 특히 크게 갈린다.

| 관찰한 것 | 보장인가 | 근거 |
|---|---|---|
| 람다 안의 `this` 가 바깥 인스턴스 | **언어 규칙** | 세 JDK 에서 같은 출력. 그리고 `static` 문맥에서 `this` 를 쓰면 **컴파일 에러**다 — 바깥 문맥의 `this` 라는 뜻이다 |
| effectively final 이 아니면 컴파일 에러 | **언어 규칙** | `javac` 가 거부한다(「어디서 틀리나」 1·2번). 세 JDK 에서 같은 메시지 |
| `@FunctionalInterface` 위반이 컴파일 에러 | **보장** | `FunctionalInterface` javadoc — "compilers are required to generate an error message" |
| 람다가 클래스 파일을 안 만든다 | 구현 세부 | 명세는 "함수형 인터페이스의 인스턴스를 만든다"까지다 |
| `invokedynamic` + `LambdaMetafactory` 를 쓴다 | 구현 세부 | javac 가 고른 방식이다 |
| 합성 메서드 이름이 `lambda$메서드$번호` | 구현 세부 | 아래 실측 참조 |
| 캡처 없는 람다가 `==` 로 같다 | **명시적으로 보장 아님** | 아래 javadoc 인용 |

**근거 — `LambdaMetafactory` javadoc (`21.0.5-tem/lib/src.zip`)**

> Capture may involve allocation of a new function object, or may return
> a suitable existing function object. The identity of a function object
> produced by capture is unpredictable, and therefore identity-sensitive
> operations (such as reference equality, object locking, and
> `System.identityHashCode()`) may produce different results in different
> implementations, or even upon different invocations in the same
> implementation.

- 「참조 동일성은 예측할 수 없다」고 **명세가 직접 말한다.**
- 그러므로 (6)절의 `a == b ? true` 는 **관찰이지 보장이 아니다.**
- 람다 객체로 `synchronized` 를 걸어서도 안 된다 — 같은 문장이 object locking 을 같이 든다.

**실측 — 세 JDK 에서 달랐던 것**

| 무엇 | 17.0.13 | 21.0.5 | 25.0.1 |
|---|---|---|---|
| 람다 런타임 클래스 이름 | `Ex$$Lambda$1/0x...` | `Ex$$Lambda/0x...` | `Ex$$Lambda/0x...` |
| 그 16진수 부분 | 실행할 때마다 다르다 | 〃 | 〃 |
| JDK 내부 `Predicate` 의 합성 메서드 번호 | `lambda$and$0`·`lambda$negate$1`·`lambda$or$2`·`lambda$isEqual$3` | 같음 | **전부 `$0`** (`lambda$and$0`·`lambda$negate$0`·`lambda$or$0`·`lambda$isEqual$0`) |
| `javap` 출력의 들여쓰기 | 기존 | 기존 | 바이트코드 오프셋이 두 칸 더 들어간다 |

- 17 에서 있던 **일련번호(`$1`)가 21 에서 사라졌다.** 클래스 이름에 기대는 코드는 이때 깨졌다.
- 16진수 부분은 **같은 JDK 에서 실행할 때마다 다르다** — 두 번 돌려 확인했다.
- 25 에서는 **JDK 자신의 합성 메서드 번호 매김이 달라졌다.** 클래스 단위가 아니라 메서드 단위로 센다.
- `javap` 출력 자체의 형식도 25 에서 달라졌다(내용은 `diff -w` 로 동일).
- 결론: **이름·번호·동일성 중 어느 것에도 기대지 않는다.** 외울 것은 「컴파일러가 합성 메서드를 만들고 `invokedynamic` 으로 잇는다」는 성질이다.
- `javac --release 8` 로 다시 찍어도 (3)·(4)의 합성 메서드 시그니처는 같았다.

## 언제 쓰고 언제 안 쓰나

| 하고 싶은 일 | 쓰는 것 |
|---|---|
| 짧은 동작 하나를 넘긴다 | **람다** |
| 이미 있는 메서드를 그대로 넘긴다 | **메서드 참조** ([`../30-method-references/`](../30-method-references/)) — 스택트레이스가 읽힌다 |
| 자기 자신을 가리켜야 한다(재귀·리스너 해제) | **익명 클래스** 또는 이름 있는 클래스 |
| 상태(필드)를 여러 개 갖는다 | **익명 클래스** 또는 이름 있는 클래스 |
| 메서드를 여러 개 구현한다 | **익명 클래스** (함수형 인터페이스가 아니다) |
| 저장·전송한다 | **람다를 쓰지 않는다.** 데이터를 저장한다 |
| 바깥 지역 변수를 바꿔야 한다 | 람다가 아니라 일반 루프 |
| 본문이 서너 줄을 넘는다 | 메서드로 뽑고 **메서드 참조** |

판단 규칙 세 줄.

- **`this` 가 본문에 있으면 기계적으로 바꾸지 않는다.** 뜻이 조용히 바뀐다.
- **본문이 길어지면 메서드로 뽑는다.** 스택트레이스가 읽히고 테스트도 붙는다.
- **람다를 신원(identity)으로 쓰지 않는다.** 비교·해제·락 전부 안 된다.

## 핵심 문장

- 람다는 **클래스 파일을 만들지 않는다.** `invokedynamic` 이 `LambdaMetafactory` 를 불러 **실행 시점에** 객체를 만든다.
- 본문은 `private ... lambda$메서드$번호` 라는 **합성 메서드**로 남고, **캡처한 값은 그 메서드의 인자**가 된다 — 캡처 없는 쪽은 인자가 0개다.
- **`this` 를 캡처하면 그 합성 메서드가 `static` 이 아니게 된다** — 그것이 「람다의 `this` 는 바깥 인스턴스」의 바이트코드 근거다.
- 익명 클래스는 **새 타입·새 스코프**를 연다. `this` 는 자기 자신이고, 바깥 이름을 가릴 수 있다. 람다는 둘 다 못 한다.
- 캡처는 **값 복사**다. 그래서 지역 변수는 effectively final 이어야 하고, 필드·배열은 캡처 뒤에도 바뀐다.
- 람다의 **이름·클래스·동일성은 보장이 아니다.** 세 JDK 에서 실제로 달랐다.

## 관련 자료

- [`../30-method-references/`](../30-method-references/) — **이 묶음의 다음 주제.** 람다를 메서드 참조로 바꾸는 자리와 못 바꾸는 자리
- [`../31-functional-interfaces/`](../31-functional-interfaces/) — **이 묶음의 다음 주제.** 람다가 들어갈 타입을 고르는 지도
- [`../44-stream-creation/`](../44-stream-creation/) · [`../45-intermediate-operations/`](../45-intermediate-operations/) — 람다가 실제로 가장 많이 쓰이는 자리
- [`../README.md`](../README.md) — Java 문법·API 주제 목록(이 주제는 29번)
- [`../../../../../../history/java/java-8.md`](../../../../../../history/java/java-8.md) — 람다·`invokedynamic` 이 **왜 그때 들어왔나**. 설계 논쟁과 JEP 는 **거기까지**, 여기는 **컴파일 결과와 사용 규칙부터**
- [`../../언어-특성/README.md`](../../언어-특성/README.md) — JIT·클래스로딩·메모리 모델 같은 **JVM 내부는 거기**. 여기는 `javap` 로 보이는 **바이트코드 표면까지**
- [`../03-variables-and-assignment/`](../03-variables-and-assignment/) — 변수와 대입(전부 값 전달·`final`·effectively final). 「캡처는 값 복사」의 상위 개념이 정본으로 다뤄지는 곳
- [**09번 주제**](../09-inheritance-overriding/)(상속과 오버라이딩) — `super::m` 이 디스패치를 건너뛰는 것의 배경
- [**11번 주제**](../11-interfaces-default-methods/)(인터페이스 `default`/`static` 메서드) — 이 주제의 선행
- [`../12-nested-classes/`](../12-nested-classes/) — 중첩 클래스(익명 클래스 포함). 익명 클래스가 바깥 인스턴스를 붙잡는 비용의 정본
- [**49번 주제**](../49-parallel-streams/)(병렬 스트림) — 캡처 우회(배열 한 칸)가 경쟁 조건이 되는 곳

## 용어 풀이

- **람다식(lambda expression)** — 함수형 인터페이스의 인스턴스를 만드는 `(인자) -> 본문` 꼴의 식.
- **함수형 인터페이스(functional interface)** — 추상 메서드가 정확히 하나인 인터페이스. 람다가 들어갈 수 있는 타입.
- **캡처(capture)** — 람다가 바깥 문맥의 값을 자기 안으로 가져오는 것. 값 복사다.
- **effectively final** — `final` 이라고 안 썼지만 초기화 뒤 한 번도 대입되지 않은 지역 변수.
- **합성 메서드(synthetic method)** — 소스에 없는데 컴파일러가 만든 메서드. 람다 본문이 여기로 간다.
- **`invokedynamic`** — 무엇을 부를지 첫 실행에서 정하는 바이트코드 명령. 람다 객체의 호출 자리다.
- **부트스트랩 메서드(bootstrap method)** — `invokedynamic` 이 첫 실행에서 부르는 메서드. 람다는 `LambdaMetafactory.metafactory`.
- **숨은 클래스(hidden class)** — 이름으로 조회할 수 없는 클래스. 람다 객체의 클래스가 이것이다.
- **익명 클래스(anonymous class)** — `new 타입() { ... }` 로 그 자리에서 만드는 이름 없는 클래스. `Ex$1.class` 가 생긴다.
- **다리 메서드(bridge method)** — 제네릭 소거 때문에 컴파일러가 넣는 중계 메서드. 익명 클래스 스택트레이스에 같은 이름이 두 번 나오는 이유.

## 더 들어가면

- **`super::m` 은 디스패치를 건너뛴다.** `Ex.java (30-a)` 에서 `this::toString` 은 재정의한 것을,\
  `super::toString` 은 `Object` 의 것을 불렀다(`[내가 재정의한 toString]` 대 `[Ex@...]`).\
  `super.m()` 과 같은 규칙이다 — [**09번 주제**](../09-inheritance-overriding/).
- **JDK 자신의 `default` 메서드도 람다로 쓰여 있다.** 리플렉션으로 선언 메서드를 찍어 보면 보인다.

  ```text
  Consumer 의 선언 메서드: [accept, andThen, lambda$andThen$0]
  Function 의 선언 메서드: [andThen, apply, compose, identity, lambda$andThen$1, lambda$compose$0, lambda$identity$2]
  ```

  `Function.andThen` 의 본문이 람다라서 `lambda$andThen$1` 이 남았다.\
  「합성 메서드가 생긴다」는 내 코드만의 이야기가 아니다.
- **직렬화 가능 람다는 부트스트랩 메서드부터 다르다.** `metafactory` 가 아니라 `altMetafactory` 이고,\
  인자 뒤에 플래그(`5`)와 개수(`0`)가 더 붙는다. 그 플래그가 「직렬화 가능하게 만들라」는 지시다.
- **`(Supplier<String> & Serializable) () -> "..."` 처럼 교차 캐스트**로 그 자리에서 `Serializable` 을 섞을 수 있다.\
  실제로 직렬화됐다(548바이트). 다만 위에서 본 깨짐 문제는 그대로다.
- **람다 본문의 부작용은 스트림에서 실행 보장이 없다** — [`../45-intermediate-operations/`](../45-intermediate-operations/) 「어디서 틀리나」 3번.\
  람다가 "순수해야 한다"는 말의 실질적 근거가 거기 있다.
