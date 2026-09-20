# java/syntax/06 — 클래스 멤버와 초기화 순서: static/인스턴스 초기화 블록 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [JLS SE 21 §12.4.1 When Initialization Occurs](https://docs.oracle.com/javase/specs/jls/se21/html/jls-12.html) · [§12.5 Creation of New Class Instances](https://docs.oracle.com/javase/specs/jls/se21/html/jls-12.html) · [§4.12.4 final Variables (constant variable)](https://docs.oracle.com/javase/specs/jls/se21/html/jls-4.html)
> **실행 검증** — 이 문서의 모든 출력은 Temurin **JDK 21.0.5** 에서 실제로 돌려 얻은 것이다.\
> 같은 프로그램을 **17.0.13 · 25.0.1** 에서도 돌려 **출력이 한 글자도 다르지 않음**을 확인했다.\
> 바이트코드는 `javap -c -p` 출력을 그대로 옮겼다.
> **버전** — 초기화 순서 규칙 자체는 Java 1.0 이래 바뀌지 않았다. 17·21·25 동작 동일.\
> 단 **25의 유연한 생성자 본문**(JEP 513)은 `super()` **앞**에 쓸 수 있는 문장을 넓혔다 — 목록의 07번 주제.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 JLS 로, 순서는 실행 트레이스로 접지했다.

## 한눈에 — 쉽게 말하면

**객체 하나가 만들어지는 것은 공장에서 차 한 대가 조립되는 것과 같다.**

비유 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 설계도 | 클래스 |
| 라인을 처음 돌릴 때 하는 준비 (딱 한 번) | 클래스 초기화 — `static` 필드 초기화식 + `static` 블록 |
| 차 한 대 조립 (주문마다) | 인스턴스 생성 — `new` |
| 섀시 = 아래쪽 골격 | 상위 클래스 부분 |
| 차체 = 그 위에 얹는 것 | 하위 클래스 부분 |
| 조립 도중 "이 차 색깔이 뭐죠?" 라고 묻기 | 생성자에서 오버라이드된 메서드 호출 |

- 공장은 **이 설계도를 처음 쓸 때 딱 한 번** 라인 준비를 한다.\
  천 대를 만들어도 준비는 한 번이다 — 이것이 `static` 초기화다.
- 차는 **주문마다 처음부터** 조립한다.\
  섀시부터 올리고 그 위에 차체를 얹는다 — 순서를 바꿀 수 없다.
- 상속이 있으면 **부모가 완전히 끝난 뒤에야** 자식 부분을 만든다.\
  섀시 없이 차체를 얹을 수 없기 때문이다.
- 문제는 **섀시를 올리는 단계에서 "이 차 색깔이 뭐죠?"라고 물어보는 코드**다.\
  차체는 아직 없으니 대답은 "없음"이다. 그런데 **에러가 아니라 "없음"이 그냥 흘러간다.**

```text
new Child() 한 번의 전체 순서 (실제 실행 출력)

  라인 준비 (딱 한 번)          차 한 대 조립 (new 마다)
  +-----------------------+     +-----------------------+
  | 1 Parent static 필드   |     | 4 Parent 인스턴스 필드 |
  | 2 Parent static 블록   |     | 5 Parent 인스턴스 블록 |
  | 3 Child  static 필드   |     | 6 Parent 생성자 본문   |
  |   Child  static 블록   |     | 7 Child  인스턴스 필드 |
  +-----------------------+     | 8 Child  인스턴스 블록 |
    두 번째 new 부터는 건너뜀     | 9 Child  생성자 본문   |
                                +-----------------------+
```

**똑같은 구조로** Java 가 이렇게 동작한다: 라인 준비 = `<clinit>`, 차 한 대 = `<init>`, 섀시 = 상위 클래스의 몫, 차체 = 하위 클래스의 몫.

실무에서 이게 터지는 자리는 **추상 클래스의 생성자가 `init()` 같은 템플릿 메서드를 부르는 설계**다.\
하위 클래스의 필드가 아직 `null` 인 채로 그 메서드가 돌고, **NPE 가 아니라 "빈 목록"으로 조용히 넘어간다.**

> **클래스 초기화(class initialization)** — 클래스가 처음 쓰일 때 JVM 이 `static` 필드 초기화식과 `static` 블록을 한 번 실행하는 것.\
> 예: `static Map<String,String> CACHE = new HashMap<>();` 가 실행되는 순간이 여기다.

> **인스턴스 초기화(instance initialization)** — `new` 할 때마다 인스턴스 필드 초기화식과 인스턴스 초기화 블록이 실행되는 것.\
> 예: `private List<String> items = new ArrayList<>();` 가 실행되는 순간이 여기다.

> **`<clinit>` / `<init>`** — 컴파일러가 만들어 주는 두 메서드의 이름. 앞은 클래스 초기화용(클래스당 하나), 뒤는 생성자(생성자마다 하나).\
> 예: `javap` 로 클래스 파일을 열면 내가 쓰지 않은 `<clinit>` 이 보인다.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. 필드 초기화식·초기화 블록·생성자 본문은 **어느 순서로 도는가** — 상속이 끼면 어떻게 되는가.
2. `static` 초기화는 **언제** 도는가 — "클래스를 썼다"의 기준이 무엇인가.
3. 내가 쓴 초기화 블록은 클래스 파일의 **어디로 가는가**.

## 동작 방식

### (1) 초기화는 두 종류다 — 횟수가 다르다

**언제 쓰나** — "이 코드가 몇 번 도는가"를 판단할 때.

```text
클래스 초기화 <clinit>                     인스턴스 초기화 <init>
+--------------------------------+        +--------------------------------+
| 대상 : 클래스 하나              |        | 대상 : 객체 하나                |
| 횟수 : 프로세스당 딱 한 번       |        | 횟수 : new 할 때마다            |
| 내용 : static 필드식 + static 블록|       | 내용 : 인스턴스 필드식 + 초기화 블록|
| 시점 : "처음 쓸 때" (§12.4.1)   |        | 시점 : new 직후, 생성자 본문 앞  |
+--------------------------------+        +--------------------------------+
```

**실행 결과** (`InitOrder.java` — `new Child()` 를 연달아 두 번)

```text
--- new Child() #1 ---
1. Parent static field
2. Parent static block
3-1. Child static field
3-2. Child static block
4. Parent instance field
5. Parent instance block
6. Parent constructor body
7. Child instance field
8. Child instance block
9. Child constructor body
--- new Child() #2 ---
4. Parent instance field
5. Parent instance block
6. Parent constructor body
7. Child instance field
8. Child instance block
9. Child constructor body
```

그림 해설 (한 단계씩):

- 두 번째 `new` 에서 **1~3번이 통째로 사라졌다.**\
  클래스 초기화는 이미 끝났기 때문이다.
- 4~9번은 그대로 반복된다 — 객체마다 새로 하는 일이다.
- 그래서 `static` 블록에 부작용을 넣으면 **"딱 한 번"이 보장되고**, 인스턴스 블록에 넣으면 **객체 수만큼** 일어난다.

비용 — `<clinit>` 은 클래스당 1회(JVM 이 락으로 보호한다).\
`<init>` 은 객체당 1회.

### (2) 아홉 단계 — 상속이 끼었을 때의 전체 순서

**언제 쓰나** — 부모·자식에 초기화 코드가 흩어져 있을 때.

```text
new Child() 가 실제로 하는 일 (위에서 아래로)

  [클래스 초기화 — 처음 한 번만]
       |
   1   +-- Parent 의 static 필드 초기화식        \
   2   +-- Parent 의 static 블록                 |  부모 먼저 (JLS 12.4.1)
       |                                         |
   3-1 +-- Child 의 static 필드 초기화식         |  그 다음 자식
   3-2 +-- Child 의 static 블록                 /
       |
  [인스턴스 초기화 — new 마다]
       |
       +-- (모든 인스턴스 필드를 기본값으로: int=0, 참조=null)
       |
   4   +-- Parent 의 인스턴스 필드 초기화식      \
   5   +-- Parent 의 인스턴스 초기화 블록         |  부모 부분을 완성하고
   6   +-- Parent 의 생성자 본문                 /
       |
   7   +-- Child 의 인스턴스 필드 초기화식       \
   8   +-- Child 의 인스턴스 초기화 블록          |  그 위에 자식 부분
   9   +-- Child 의 생성자 본문                  /
       |
       v
     객체 완성
```

그림 해설 (한 단계씩):

- 클래스 초기화가 **인스턴스 초기화보다 전부 먼저** 온다.\
  라인 준비가 안 끝났는데 차를 만들 수는 없다.
- 클래스 초기화도 인스턴스 초기화도 **부모 → 자식** 순이다.
- **4~6(부모 전체)이 끝난 뒤에야 7(자식 첫 필드)이 시작된다.**\
  이 경계가 이 주제의 모든 함정이 사는 자리다.
- 4·5(필드식과 블록)는 **소스에 적힌 순서**대로 섞인다.\
  블록이 필드보다 위에 있으면 블록이 먼저 돈다 — "필드 먼저, 블록 나중"이 아니다.
- 필드가 기본값(`0`·`null`)으로 채워지는 단계는 출력에 안 나타나지만, **4보다도 앞**이다.

JLS §12.5 가 정한 절차와 같다 — 인용하면 4단계가 이것이다.

> **Execute instance initializers and instance variable initializers** for the class, assigning values in left-to-right textual order. ... Instance initializers and instance variable initializers are executed **after** the superclass constructor completes but **before** the remainder of the current constructor body executes.

비용 — 단계 수는 클래스 계층 깊이에 비례한다.\
깊은 상속은 `new` 한 번에 그만큼의 생성자 프레임을 쌓는다.

### (3) 컴파일러가 하는 일 — 초기화 블록은 생성자 안으로 복사된다

**언제 쓰나** — "초기화 블록은 언제 도나"를 확인할 때. 답이 바이트코드에 그대로 있다.

```java
class Point {
    int x, y;
    { System.out.println("   인스턴스 초기화 블록"); }

    Point() {
        this(0, 0);                 // 여기서는 super() 가 안 불린다
        System.out.println("   Point() 본문");
    }
    Point(int x, int y) {
        // 암묵적 super() 가 여기 있다
        this.x = x; this.y = y;
        System.out.println("   Point(int,int) 본문");
    }
}
```

```text
javap -c -p Point  — 출력 그대로

  Point();                                Point(int, int);
    0: aload_0                              0: aload_0
    1: iconst_0                             1: invokespecial Object."<init>"   <- super()
    2: iconst_0                             4: getstatic System.out
    3: invokespecial "<init>":(II)V  <-이쪽 7: ldc "   인스턴스 초기화 블록"   <- 블록이
    6: getstatic System.out                 9: invokevirtual println              여기 복사됨
    9: ldc "   Point() 본문"                12: aload_0 / iload_1 / putfield x
   11: invokevirtual println                17: aload_0 / iload_2 / putfield y
   14: return                              22: getstatic System.out
                                           25: ldc "   Point(int,int) 본문"
     초기화 블록이 없다!                    27: invokevirtual println
                                           30: return
```

그림 해설 (한 단계씩):

- 왼쪽 `Point()` 에는 **초기화 블록의 흔적이 아예 없다.**\
  `this(0,0)` 으로 넘기기만 한다.
- 오른쪽 `Point(int,int)` 에는 `super()` 바로 뒤에 **블록의 내용이 그대로 복사**되어 있다.
- 규칙: **`super()` 를 부르는 생성자에만** 필드 초기화식과 초기화 블록이 복사된다.\
  `this(...)` 로 위임하는 생성자에는 안 들어간다.
- 그래서 생성자가 셋이면 초기화 블록은 **클래스 파일에 세 벌**이 될 수도 있다(각자 `super()` 를 부른다면).

**실행 결과** (`ThisChain.java`)

```text
new Point()
   인스턴스 초기화 블록
   Point(int,int) 본문
   Point() 본문
new Point(1,2)
   인스턴스 초기화 블록
   Point(int,int) 본문
```

- `new Point()` 를 해도 블록은 **한 번만** 돈다 — 두 생성자를 거쳤는데도.
- 그리고 블록이 **`Point()` 본문보다 먼저** 돈다 — 위임받은 생성자 안에서 돌았기 때문이다.

비용 — 초기화 블록의 코드가 생성자 수만큼 복제되어 클래스 파일이 커진다.\
실행 비용은 그대로(생성자 하나당 한 번).

> **`invokespecial`** — 생성자·`private` 메서드·`super.` 호출에 쓰는 JVM 명령.\
> 예: `super()` 와 `this(...)` 가 둘 다 이 명령으로 컴파일되므로, `javap` 에서 어느 쪽인지는 대상 클래스 이름으로 구분한다.

### (4) 클래스 초기화는 "처음 쓸 때" — 그 기준이 좁다

**언제 쓰나** — `static` 블록이 안 돌아서 의아할 때. 또는 돌 줄 알았는데 돌았을 때.

JLS §12.4.1 은 초기화를 일으키는 경우를 **네 가지로 못박는다**(원문 요약 인용).

> A class or interface T will be initialized immediately before the first occurrence of any one of the following:\
> 1. T is a class and an instance of T is created.\
> 2. A `static` method declared by T is invoked.\
> 3. A `static` field declared by T is assigned.\
> 4. A `static` field declared by T is used and the field is **not a constant variable** (§4.12.4).

**실행 결과** (`WhenClinit.java`)

```text
a) Holder.CONST 읽기
   값 = 42
b) Holder 타입 이름만 쓰기
   배열 길이 = 3
c) Holder.BOXED 읽기
   >> Holder <clinit> 실행됨
   값 = 42
```

```text
class Holder {
    static final int     CONST = 42;   // 컴파일 타임 상수 -> 4번 조건에서 제외
    static final Integer BOXED = 42;   // 상수 아님 (Integer 는 상수 변수가 못 된다)
    static { System.out.println("   >> Holder <clinit> 실행됨"); }
}

  a) Holder.CONST     ->  javac 가 42 를 호출부에 박아 넣었다 -> Holder 를 아예 안 건드림
  b) new Holder[3]    ->  배열 타입을 쓴 것뿐, 인스턴스를 만든 게 아님 -> 초기화 안 됨
  c) Holder.BOXED     ->  진짜 static 필드 읽기 -> 여기서 비로소 <clinit> 실행
```

그림 해설 (한 단계씩):

- (a) `CONST` 는 **상수 변수**라 컴파일 타임에 `42` 로 치환된다.\
  클래스 파일에 `Holder` 를 가리키는 참조가 남지 않으므로 초기화가 안 일어난다.
- (b) 배열을 만드는 것은 **`Holder` 의 인스턴스를 만드는 것이 아니다.**\
  칸 세 개가 전부 `null` 일 뿐이다.
- (c) `BOXED` 는 `Integer` 라서 상수 변수가 될 수 없다 — 진짜 필드 읽기가 되어 그때 `<clinit>` 이 돈다.
- 함의: `static` 블록에 로깅·등록 같은 부작용을 넣고 "상수 하나 읽으면 돌겠지"라고 기대하면 **안 돈다.**

비용 — 초기화는 **지연**된다. 기동 시점이 아니라 첫 사용 시점에 비용이 난다.

> **상수 변수(constant variable)** — `final` 이면서 초기화식이 상수 식인 **기본형 또는 `String`** 변수(JLS §4.12.4).\
> 예: `static final int X = 42;` 와 `static final String S = "a";` 는 상수 변수고, `static final Integer B = 42;` 와 `static final int[] A = {1};` 는 아니다.

## 문법 — 형태와 규칙

직접 쓴 최소 예제다.

### 네 가지 초기화 수단

```java
class Example {
    static int a = 1;                 // (1) static 필드 초기화식
    static { a += 1; }                // (2) static 초기화 블록

    int b = 1;                        // (3) 인스턴스 필드 초기화식
    { b += 1; }                       // (4) 인스턴스 초기화 블록

    Example() { b += 1; }             // (5) 생성자 본문
}
```

| 수단 | 실행 시점 | 횟수 | 쓰는 이유 |
|---|---|---|---|
| (1) static 필드식 | 클래스 초기화 | 1 | 한 줄로 끝나는 상수·싱글턴 |
| (2) static 블록 | 클래스 초기화 | 1 | 여러 줄이 필요하거나 예외를 잡아야 할 때 |
| (3) 인스턴스 필드식 | `super()` 직후 | new 마다 | 기본값 지정 |
| (4) 인스턴스 블록 | `super()` 직후 | new 마다 | 생성자 여러 개가 **공통으로** 할 일 |
| (5) 생성자 본문 | (3)(4) 다음 | new 마다 | 인자에 따라 달라지는 일 |

- (1)(2)는 소스에 적힌 **순서대로** 섞여 실행된다. (3)(4)도 마찬가지다.
- (4)는 익명 클래스처럼 **생성자를 못 쓰는 자리**에서 특히 쓸모가 있다.

### `this()` 와 `super()` 의 규칙

- 생성자의 **첫 문장**만 `this(...)` 또는 `super(...)` 가 될 수 있다.\
  (JDK 25의 유연한 생성자 본문은 이 앞에 일부 문장을 허용한다 — 목록의 **07번 주제**.)
- 둘 다 안 쓰면 **컴파일러가 `super()` 를 넣는다.**
- `this(...)` 로 위임한 생성자에는 필드 초기화식·초기화 블록이 **안 복사된다**(동작 방식 3).

## 어디서 틀리나

넷 다 **컴파일 에러 없이 조용히 틀리거나, 직관과 다른 값이 나온다.**

### 1. 생성자에서 오버라이드 가능한 메서드를 부른다

```java
class Base {
    Base() { System.out.println("Base ctor    : " + describe()); }
    String describe() { return "Base"; }
}
class Derived extends Base {
    private String name = "derived";
    Derived() { System.out.println("Derived ctor : " + describe()); }
    @Override String describe() { return "name=" + name; }
}
```

**실행 결과** (`CtorTrap2.java`)

```text
Base ctor    : name=null
Derived ctor : name=derived
```

```text
잘못된 기대                                실제 순서
+-------------------------+               +-------------------------+
| Base 생성자              |               | Base 생성자              |
|   describe()            |               |   describe()            |
|   -> "name=derived"     |               |   -> Derived.describe() |
|                         |               |      (동적 디스패치)      |
|                         |               |   -> name 은 아직 null   |
|                         |               |   -> "name=null"        |
+-------------------------+               +-------------------------+
                                            그 다음에야 name = "derived"
```

- `describe()` 는 **동적 디스패치**되어 `Derived` 것이 불린다.\
  객체의 런타임 타입은 처음부터 `Derived` 다.
- 그런데 7번 단계(자식 필드 초기화)가 아직 안 왔으므로 `name` 은 **기본값 `null`**.
- **NPE 도 안 난다.** `"name=" + null` 은 `"name=null"` 이라는 멀쩡한 문자열이다.
- 실무에서는 `List` 필드가 `null` 인 채로 순회를 돌아 "0건"이 되거나, 캐시가 `null` 이라 매번 미스가 나는 식으로 나타난다.
- 방어: **생성자에서는 `private`·`final`·`static` 메서드만 부른다.**

> **동적 디스패치(dynamic dispatch)** — 어느 메서드 구현을 부를지 **런타임 타입**으로 고르는 것.\
> 예: 변수의 선언 타입이 `Base` 여도 실제 객체가 `Derived` 면 `Derived` 의 재정의가 불린다.\
> 이 규칙 자체는 목록의 **09번 주제**(상속과 오버라이딩)가 정본이다.

### 2. 컴파일 타임 상수는 "필드 읽기"가 아니다

같은 함정인데 **결과가 뒤집혀서 더 헷갈린다.**

```java
class D2 extends B2 {
    private final int constant = 10;        // 컴파일 타임 상수
    private final int computed = compute();  // 상수 아님
    static int compute() { return 10; }
    @Override String show() { return "constant=" + constant + " computed=" + computed; }
}
```

**실행 결과** (`ConstFold.java`)

```text
B2 ctor: constant=10 computed=0
```

```text
javap -c -p D2  — show() 의 전체 바이트코드

  java.lang.String show();
       0: aload_0
       1: getfield      #17   // Field computed:I          <- 필드 읽기는 하나뿐
       4: invokedynamic #20   // makeConcatWithConstants:(I)
       9: areturn
```

- `constant` 를 읽는 `getfield` 가 **아예 없다.**\
  `javac` 가 `10` 을 문자열 상수에 **접어 넣었다**(constant folding).
- `computed` 만 진짜 필드 읽기라 아직 초기화 전인 `0` 이 나온다.
- 그래서 같은 `final int` 필드 둘인데 **하나는 맞고 하나는 틀린다.**\
  `= 10` 을 `= compute()` 로 바꾸는 리팩토링 한 번에 값이 10에서 0으로 조용히 바뀐다.
- 판단 기준: **초기화식이 상수 식이면 필드가 아니라 상수**다(JLS §4.12.4).

### 3. 전방 참조 — 쓰기는 되고 읽기는 컴파일 에러

```java
class Counter {
    static { count = 5;  }        // 아래에 선언된 필드에 쓰기 — 허용
    static int count = 10;        // 이 줄이 나중에 실행된다
}
```

**실행 결과** (`Forward.java`)

```text
   블록 안: 방금 5 를 넣었다
Counter.count = 10
```

- **`5` 가 `10` 에 덮인다.** 블록이 먼저 돌고 필드 초기화식이 나중에 돌기 때문이다.
- 에러도 경고도 없다 — 블록에서 한 일이 그냥 사라진다.

읽기를 시도하면 컴파일이 막힌다.

```text
$ javac ForwardRead.java
ForwardRead.java:2: error: illegal forward reference
    static { System.out.println(count); }
                                ^
1 error
```

- **쓰기는 통과하고 읽기는 막는** 비대칭이다.
- 그래서 "컴파일이 됐으니 순서가 맞다"는 보장이 되지 않는다.
- 방어: 초기화 블록은 **관련 필드 선언 아래**에 둔다.

### 4. `this()` 위임에서 초기화 블록이 "한 번만" 돈다

동작 방식 (3)에서 본 것이 그대로 함정이 된다.

```text
new Point()  -> Point() -> this(0,0) -> Point(int,int)
                  |                        |
                  |                        +-- super() -> 초기화 블록 -> 본문
                  +-- 본문                              (블록은 여기서 딱 한 번)
```

- 생성자 둘을 거쳤지만 블록은 **한 번**이다. 옳은 동작이다.
- 헷갈리는 것은 **출력 순서**다 — `Point()` 의 본문보다 블록이 **먼저** 나온다.
- 함정이 되는 경우: `Point()` 본문에서 필드를 세팅하고, 초기화 블록이 그 필드를 읽는 구조.\
  블록이 먼저 도니 **항상 세팅 전 값**을 본다.

## 언제 쓰고 언제 안 쓰나

| 쓸 것 | 안 쓸 것 |
|---|---|
| 생성자 여러 개가 **공통으로** 할 초기화 -> 인스턴스 초기화 블록 | 생성자 하나뿐인 클래스에 초기화 블록 (생성자에 쓰면 된다) |
| 여러 줄이 필요한 `static` 준비 -> `static` 블록 | `static` 블록에서 무거운 I/O (첫 사용이 언제인지 예측이 어렵다) |
| 익명 클래스에서의 초기화 -> 인스턴스 초기화 블록 | 초기화 블록으로 컬렉션 채우기(이중 중괄호 관용구) — 익명 클래스가 남아 바깥을 붙잡는다 |
| 값이 고정된 상수 -> `static final` 기본형/`String` | 그 상수를 "클래스가 초기화되는 신호"로 쓰기 — 안 일어난다 |

판단 규칙 세 줄.

- **생성자에서는 오버라이드 가능한 메서드를 부르지 않는다.** 부를 필요가 생기면 설계가 틀린 것이다.
- **`static` 블록은 순수하게** — 다른 클래스를 깨우거나 예외를 던지면 `ExceptionInInitializerError` 로 번진다.
- **초기화식은 선언 아래에.** 전방 참조는 쓰기만 되고, 그 쓰기는 덮인다.

## 핵심 문장

- 초기화는 **클래스 초기화(한 번)** 와 **인스턴스 초기화(new 마다)** 두 층이고, 두 층 다 **부모 → 자식** 순이다.
- 인스턴스 초기화식과 초기화 블록은 **`super()` 직후, 생성자 본문 직전**에 소스 순서대로 실행된다(JLS §12.5 4단계).
- 컴파일러는 그 코드를 **`super()` 를 부르는 생성자에만 복사**한다. `this(...)` 로 위임하는 생성자에는 안 넣는다.
- 부모 생성자가 도는 동안 **자식 필드는 전부 기본값**이다 — 그래서 생성자에서 오버라이드 메서드를 부르면 조용히 틀린다.
- **컴파일 타임 상수는 필드가 아니다.** 호출부에 값이 박히므로 초기화 순서와 무관하고, 클래스 초기화도 일으키지 않는다.

## 관련 자료

- [`../README.md`](../README.md) — Java 문법·API 주제 목록(이 주제는 06번)
- [`../../../../oop-basics/`](../../../../oop-basics/) — 상속·다형성 개념. **개념은 거기**, 여기는 Java 의 실행 순서만
- [`../../언어-특성/README.md`](../../언어-특성/README.md) §3 — 클래스로더와 "언제 로드되는가". **로딩·링킹은 거기**, 여기는 **초기화 단계**만 다룬다
- [`../01-primitives-and-wrappers/`](../01-primitives-and-wrappers/) — 「어디서 틀리나」 2번의 상수 식 개념이 겹친다. `Integer` 는 상수 변수가 될 수 없다는 사실이 이 주제의 (4)에서 쓰인다
- 목록의 **07번 주제**(생성자 — `this()`/`super()`·25 유연한 생성자 본문) — `super()` 앞에 무엇을 쓸 수 있는지가 정본
- 목록의 **09번 주제**(상속과 오버라이딩 — 동적 디스패치) — 「어디서 틀리나」 1번의 디스패치 규칙이 정본
- 목록의 **12번 주제**(중첩 클래스) — 익명 클래스와 초기화 블록의 조합

## 용어 풀이

- **클래스 초기화** — 클래스를 처음 쓸 때 `static` 필드식과 `static` 블록을 한 번 실행하는 단계.
- **인스턴스 초기화** — `new` 마다 인스턴스 필드식과 초기화 블록을 실행하는 단계.
- **`<clinit>` / `<init>`** — 컴파일러가 만드는 클래스 초기화 메서드 / 생성자의 내부 이름.
- **상수 변수(constant variable)** — `final` + 상수 식 초기화 + 기본형이나 `String`. 값이 호출부에 박힌다.
- **상수 접기(constant folding)** — 컴파일러가 상수 식을 미리 계산해 결과 값으로 치환하는 것.
- **전방 참조(forward reference)** — 아직 선언되지 않은(아래에 있는) 멤버를 위에서 가리키는 것. 읽기는 컴파일 에러, 쓰기는 허용.
- **동적 디스패치** — 어느 구현을 부를지 런타임 타입으로 고르는 것. 생성자 안에서도 예외 없이 적용된다.
- **기본값(default value)** — 객체 메모리가 잡힐 때 모든 인스턴스 필드에 들어가는 값. `int` 계열 `0`, `boolean` `false`, 참조 `null`.
- **`ExceptionInInitializerError`** — `static` 초기화 도중 예외가 나면 JVM 이 감싸 던지는 에러. 그 클래스는 이후 사용할 수 없게 된다.
- **`invokespecial`** — 생성자·`super.`·`private` 호출용 JVM 명령.

---

## [Claude 추가] 더 알면 좋은 것

- **`<clinit>` 은 JVM 이 락으로 보호한다.**\
  여러 스레드가 동시에 같은 클래스를 처음 쓰면 한 스레드만 초기화하고 나머지는 기다린다.\
  그래서 `static` 홀더 관용구(`private static class Holder { static final X INSTANCE = new X(); }`)가 **락 없이 안전한 지연 싱글턴**이 된다.
- **초기화 순환은 데드락이 아니라 "미완성 값"을 준다.**\
  A 의 `<clinit>` 이 B 를 건드리고 B 의 `<clinit>` 이 다시 A 를 건드리면, 같은 스레드이므로 두 번째 진입은 그냥 통과되고 **아직 채워지지 않은 필드**를 읽게 된다.\
  실제로 돌려 확인했다 (`Cycle.java`, JDK 21.0.5) — `A.aVal = B.bVal + 1` 과 `B.bVal = A.aVal + 1` 을 두고 `A.aVal` 을 먼저 읽으면:

  ```text
  A.aVal 를 먼저 읽는다
     B <clinit> 끝: bVal=1      <- A.aVal 이 아직 0 이라 1 이 됐다
     A <clinit> 끝: aVal=2
  A.aVal = 2 / B.bVal = 1
  ```

  에러도 데드락도 없다. **읽는 순서를 바꾸면 값이 달라진다.**
- **인터페이스의 `static` 필드도 같은 규칙을 따르지만**, 인터페이스 초기화는 상위 인터페이스를 초기화하지 않는다(JLS §12.4.1).
- **이중 중괄호 초기화**(`new ArrayList<>() {{ add("a"); }}`)는 이 주제의 인스턴스 초기화 블록을 익명 클래스에 쓴 것이다.\
  편해 보이지만 익명 클래스가 **바깥 인스턴스를 붙잡아** 누수를 만들고, 직렬화·`equals` 도 깨진다. 쓰지 않는다.
