# java/syntax/06 — 클래스 멤버와 초기화 순서: static/인스턴스 초기화 블록 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력은 **Temurin JDK 21.0.5 에서 실제로 돌려 얻은 것**이다.\
> 바이트코드는 `javap -c -p` 출력을 그대로 옮겼다.\
> 17.0.13 · 25.0.1 에서도 같은 프로그램을 돌려 **출력이 한 글자도 다르지 않음**을 확인했다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 이 프로그램의 출력 순서를 예측하라

**실행 결과** (`InitOrder.java`, JDK 21.0.5 — 17·25 동일)

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

**첫 번째 `new Child()` — 열 줄**

```text
  [클래스 초기화 — 부모 먼저, 자식 나중]
   1  Parent static field      \  Parent 의 <clinit>
   2  Parent static block      /  소스 순서대로
   3  Child  static field      \  Child 의 <clinit>
   3  Child  static block      /
       |
  [인스턴스 초기화 — 부모 전체를 끝내고 자식으로]
   4  Parent instance field    \
   5  Parent instance block     |  Parent 의 <init>
   6  Parent constructor body  /
       |
   7  Child  instance field    \
   8  Child  instance block     |  Child 의 <init> 의 나머지
   9  Child  constructor body  /
```

- 두 층(클래스/인스턴스) 다 **부모 → 자식** 순이다.
- 층 사이에는 섞임이 없다 — 클래스 초기화가 **전부** 끝난 뒤 인스턴스 초기화가 시작된다.
- 각 층 안에서 필드식과 블록은 **소스에 적힌 순서**대로 섞인다.

**두 번째 `new Child()` — 여섯 줄, 1~3번이 빠진다**

**왜 빠졌는가**

- `static` 초기화는 **클래스당 딱 한 번**이다. 이미 끝났으므로 다시 안 돈다.
- JLS §12.4.1 이 "will be initialized immediately before the **first** occurrence of ..." 라고 쓴 그 `first` 다.
- 실무 함의: `static` 블록의 부작용(등록·로깅·커넥션)은 **"딱 한 번"이 보장된다.**\
  반대로 그 한 번이 **언제인지는 보장되지 않는다**(6번 참조).

> **`<clinit>`** — 컴파일러가 `static` 필드 초기화식과 `static` 블록을 모아 만드는 메서드. 클래스당 하나이고 JVM 이 직접 부른다.\
> 예: 소스에 `static` 블록이 셋 있어도 클래스 파일의 `<clinit>` 은 하나이고, 그 안에 셋이 순서대로 들어 있다.

### 2. 필드와 블록의 상대 순서

**실행 결과** (`Textual.java`)

```text
X (블록이 위):
블록
필드
Y (필드가 위):
필드
블록
```

**무엇이 먼저 출력되는가**

- 주어진 `X` 에서는 **"블록"이 먼저**다. 블록이 소스에서 위에 있기 때문이다.

**"필드 초기화식이 먼저, 초기화 블록이 나중"이라는 기억은 맞는가**

- **틀렸다.** 같은 코드를 순서만 바꾼 `Y` 에서는 "필드"가 먼저 나온다.

```text
class X { 블록; 필드; }            class Y { 필드; 블록; }
+----------------------+          +----------------------+
| 블록                  |          | 필드                  |
| 필드                  |          | 블록                  |
+----------------------+          +----------------------+
   소스 순서 그대로              소스 순서 그대로
```

**이 순서를 정하는 것**

- **소스에 적힌 텍스트 순서**다. JLS §12.5 4단계가 "assigning values in **left-to-right textual order**" 라고 못박는다.
- 그래서 "필드 선언을 위로 모으는" 리팩토링이 **동작을 바꿀 수 있다.**
- 방어: 초기화 블록은 그 블록이 쓰는 필드들 **아래**에 둔다.

### 3. 초기화 블록은 클래스 파일의 어디로 가는가

**실행 결과** (`ThisChain.java`)

```text
new Point()
   인스턴스 초기화 블록
   Point(int,int) 본문
   Point() 본문
```

**세 줄의 출력 순서**

1. `인스턴스 초기화 블록`
2. `Point(int,int) 본문`
3. `Point() 본문`

**"블록"은 몇 번 출력되는가**

- **한 번.** 생성자 둘을 거쳤는데도 한 번이다.

**`javap -c` 로 열면 어느 쪽에 들어 있는가**

```text
javap -c -p Point  — 출력 그대로 (요약 없이)

  Point();                                    Point(int, int);
    0: aload_0                                  0: aload_0
    1: iconst_0                                 1: invokespecial Object."<init>":()V
    2: iconst_0                                 4: getstatic  System.out
    3: invokespecial "<init>":(II)V             7: ldc "   인스턴스 초기화 블록"
    6: getstatic  System.out                    9: invokevirtual println
    9: ldc "   Point() 본문"                   12: aload_0 / iload_1 / putfield x
   11: invokevirtual println                   17: aload_0 / iload_2 / putfield y
   14: return                                  22: getstatic  System.out
                                               25: ldc "   Point(int,int) 본문"
   초기화 블록의 코드가 없다                    27: invokevirtual println
                                               30: return
```

- **`Point(int,int)` 쪽에만** 들어 있다. `super()` 인 `Object.<init>` 바로 뒤다.
- `Point()` 는 `this(0,0)` 으로 위임만 하고 블록 코드가 아예 없다.

**규칙 한 문장**

> 필드 초기화식과 인스턴스 초기화 블록은 **`super(...)` 를 (명시적으로든 암묵적으로든) 부르는 생성자에만** 복사된다.

- 따라서 `this(...)` 로 위임하는 생성자에는 안 들어가고, 그 덕에 **중복 실행이 안 일어난다.**
- 생성자가 셋인데 셋 다 `super()` 를 부른다면, 블록의 코드는 **클래스 파일에 세 벌** 들어간다.
- 출력 순서가 헷갈리는 이유도 여기 있다 — 블록은 **위임받은 쪽**에서 돌았으므로 `Point()` 본문보다 앞선다.

### 4. 부모 생성자가 자식 메서드를 부르면

**실행 결과** (`CtorTrap2.java`)

```text
Base ctor    : name=null
Derived ctor : name=derived
```

**두 줄의 출력**

- `Base ctor    : name=null`
- `Derived ctor : name=derived`

```text
new Derived() 의 시간 축

  t0  메모리 할당 — name 에 기본값 null 이 들어간다
  t1  Derived() 진입 -> 암묵적 super()
  t2    Base() 본문: describe() 호출
  t3      -> Derived.describe() 가 불린다 (동적 디스패치)
  t4      -> name 을 읽는다 ... 아직 null
  t5      -> "name=null" 출력            <-- 여기
  t6  Base() 반환
  t7  Derived 의 필드 초기화식: name = "derived"   <-- 이제서야
  t8  Derived() 본문: describe() -> "name=derived"
```

**어느 클래스의 `describe()` 가 불렸는가**

- **`Derived` 의 것**이다.
- 객체의 런타임 타입은 `t0` 부터 이미 `Derived` 다.\
  "아직 부모 생성자 중이니 부모 메서드가 불린다"는 것은 오개념이다.

**왜 NPE 가 아닌가**

- `"name=" + name` 에서 `name` 이 `null` 이어도 **문자열 연결은 `"null"` 로 처리**된다.
- 즉 **예외가 아니라 그럴듯한 값**이 나온다 — 조용한 실패다.
- 필드가 `List` 였다면 `null.size()` 에서 NPE 가 났을 수도 있고, `Objects.requireNonNullElse` 같은 방어가 있었다면 **빈 목록으로 조용히 흘러갔을** 것이다.\
  어느 쪽이든 **원인 지점과 증상 지점이 멀어진다.**

> **조용한 실패(silent failure)** — 에러 없이 정상처럼 끝나는데 결과만 틀린 것.\
> 예: 생성자에서 읽은 설정이 `null` 이라 기본값으로 떨어졌는데, 로그에는 아무것도 안 남는 것.

**안전하게 만들려면**

- **생성자에서는 오버라이드 가능한 메서드를 부르지 않는다.**\
  `private`·`final`·`static` 만 부른다 — 이 셋은 재정의될 수 없다.
- 하위 클래스의 값이 필요하면 **생성자 인자로 받는다**(`Base(String name)`).
- 초기화가 꼭 두 단계로 나뉘어야 하면 **생성자 밖의 `init()` 을 팩토리 메서드에서 명시적으로 부른다.**

```text
나쁜 계약                                   좋은 계약
+---------------------------+              +---------------------------+
| Base() { describe(); }    |              | Base(String name) {       |
|   -> 하위 필드 미초기화     |              |   this.name = name;       |
|   -> null 이 흘러간다      |              | }                         |
+---------------------------+              +---------------------------+
  하위 클래스가 조심해야 한다                 언어가 순서를 보장한다
```

### 5. `final` 필드 둘의 결과가 갈린다

**실행 결과** (`ConstFold.java`)

```text
B2 ctor: constant=10 computed=0
```

**두 값**

- `constant` = **10**
- `computed` = **0**

**왜 갈리는가**

- `constant` 는 **상수 변수**다 — `final` + 기본형 + 초기화식이 상수 식(JLS §4.12.4).\
  `javac` 가 값을 **쓰는 자리에 박아 넣는다.** 필드를 읽는 코드 자체가 사라진다.
- `computed` 는 초기화식이 메서드 호출이라 상수 식이 아니다.\
  진짜 필드 읽기가 남고, 아직 초기화 전이라 **기본값 `0`** 이 나온다.

**`javap` 로 `show()` 를 열면**

```text
javap -c -p D2  — show() 의 전체 바이트코드

  java.lang.String show();
    Code:
       0: aload_0
       1: getfield      #17   // Field computed:I
       4: invokedynamic #20   // makeConcatWithConstants:(I)Ljava/lang/String;
       9: areturn
```

- **`getfield` 는 한 개뿐**이다. `computed` 를 읽는 것.
- `constant` 를 읽는 명령이 없다 — `10` 은 `invokedynamic` 이 쓰는 **상수 문자열 안에** 접혀 들어갔다.
- 소스에는 필드 둘을 읽는 것처럼 보이는데 **클래스 파일에는 하나뿐**이다.

**`= 10` 을 `= compute()` 로 바꾸면**

- `constant` 가 **상수 변수가 아니게 된다.**
- 출력이 `constant=10` 에서 `constant=0` 으로 **조용히 바뀐다.**
- 값도 같고(`compute()` 가 10을 돌려준다) 타입도 같고 `final` 도 그대로인데 **결과만 달라진다.**
- 같은 이유로 **다른 클래스가 이 상수를 쓰고 있었다면 재컴파일이 필요하다** — 상수는 그 클래스 파일에 복사돼 있기 때문이다.

> **상수 접기(constant folding)** — 컴파일러가 상수 식을 미리 계산해 결과 값으로 치환하는 것.\
> 예: `static final int X = 42;` 를 쓰는 다른 클래스의 클래스 파일에는 `42` 가 박히고, `X` 를 읽는 명령은 남지 않는다.

### 6. `static` 블록은 언제 도는가

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

**어디에서 출력되는가**

- **(c) 에서만.**

```text
  (a) Holder.CONST         (b) new Holder[3]        (c) Holder.BOXED
       |                        |                        |
  상수 변수 -> 42 가          배열 타입을 쓴 것 ->      진짜 static 필드 읽기
  호출부에 박혔다              인스턴스를 안 만든다      -> 조건 4 성립
       |                        |                        |
  Holder 를 안 건드림        Holder 를 안 건드림        <clinit> 실행
```

**`CONST` 와 `BOXED` 가 갈리는 이유**

- `CONST` 는 `static final int` + 상수 식 -> **상수 변수**라 JLS §12.4.1 의 4번 조건에서 **명시적으로 제외**된다.\
  원문: "A `static` field declared by T is used and the field is **not a constant variable**".
- `BOXED` 는 `static final Integer` 다.\
  `Integer` 는 기본형도 `String` 도 아니므로 **상수 변수가 될 수 없다**(§4.12.4).
- 값이 둘 다 `42` 이고 둘 다 `static final` 인데 **타입 하나로 갈린다.**\
  01번 주제의 오토박싱이 여기서 다시 걸린다 — `Integer BOXED = 42` 는 초기화식이 박싱 변환이라 상수 식이 아니다.

**배열이 왜 초기화를 안 일으키는가**

- `new Holder[3]` 은 **`Holder` 타입의 배열 객체**를 만든 것이다.
- `Holder` 의 인스턴스는 **하나도 안 만들어졌다** — 칸 셋이 전부 `null` 이다.
- 조건 1은 "an instance of T is created" 이므로 성립하지 않는다.

**클래스 초기화를 일으키는 네 가지** (JLS §12.4.1)

1. T 가 클래스이고 **T 의 인스턴스가 생성될 때**
2. T 가 선언한 **`static` 메서드가 호출될 때**
3. T 가 선언한 **`static` 필드에 값이 대입될 때**
4. T 가 선언한 **`static` 필드가 사용되고, 그 필드가 상수 변수가 아닐 때**

덧붙는 규칙 둘(원문):

- 클래스가 초기화되면 **상위 클래스들도** 초기화된다(default 메서드를 선언한 상위 인터페이스도).\
  인터페이스의 초기화는 상위 인터페이스를 초기화하지 **않는다.**
- `static` 필드 참조는 **그 필드를 실제로 선언한 클래스만** 초기화한다 — 하위 클래스 이름으로 접근해도 마찬가지다.

### 7. 전방 참조

**실행 결과** (`Forward.java`)

```text
   블록 안: 방금 5 를 넣었다
Counter.count = 10
```

**출력은 무엇인가**

- **`10`.** 블록이 넣은 `5` 가 덮였다.

```text
<clinit> 이 실제로 하는 일 (소스 순서대로)

  1  count = 5           <- static 블록 (소스 첫 줄)
  2  println(...)
  3  count = 10          <- 필드 초기화식 (소스 둘째 줄)
        |
        v
  결과 count = 10        5 는 흔적도 없이 사라졌다
```

**컴파일되는가**

- **된다.** 경고도 없다.

**읽기로 바꾸면**

```text
$ javac ForwardRead.java
ForwardRead.java:2: error: illegal forward reference
    static { System.out.println(count); }
                                ^
1 error
```

- **컴파일 에러**다. 선언 아래의 필드를 **단순 이름으로 읽는 것**은 막힌다.
- 우회는 가능하다 — `Counter3.count` 처럼 **한정 이름**으로 쓰면 컴파일된다.\
  실행 결과 (`Qualified.java`):

  ```text
  블록에서 읽은 값 = 0
  최종 = 10
  ```

  기본값 `0` 을 읽는다. **언어가 막는 것은 형태이지 의미가 아니다.**

**비대칭이 만드는 위험**

- **"컴파일이 됐으니 순서가 맞다"가 성립하지 않는다.**\
  읽기만 막히고 쓰기는 통과하는데, 실제로 사라지는 것은 **쓰기 쪽**이다.
- 그래서 초기화 블록에서 한 일이 **에러 없이 무효가 된다.**
- 방어: 초기화 블록은 그 블록이 건드리는 필드 **선언 아래**에 둔다.

### 8. 초기화가 순환하면

**실행 결과** (`Cycle.java` — `A.aVal` 을 먼저 읽음)

```text
A.aVal 를 먼저 읽는다
   B <clinit> 끝: bVal=1
   A <clinit> 끝: aVal=2
A.aVal = 2 / B.bVal = 1
```

**실행 결과** (`Cycle2.java` — `B.bVal` 을 먼저 읽음)

```text
B 를 먼저 읽는다
B.bVal = 2 / A.aVal = 1
```

**데드락인가, 예외인가, 값인가**

- **값이 나온다.** 데드락도 예외도 없다.

```text
A.aVal 를 먼저 읽었을 때

  A 의 <clinit> 시작 — "A 는 초기화 중" 표시
       |
       +-- aVal = B.bVal + 1  -> B 를 건드린다
                |
                +-- B 의 <clinit> 시작
                        |
                        +-- bVal = A.aVal + 1  -> A 를 건드린다
                                 |
                                 +-- A 는 "초기화 중" + 같은 스레드
                                     -> 그냥 통과. aVal 을 읽는다 = 0  <-- 미완성 값
                                 |
                        +-- bVal = 0 + 1 = 1
                +-- B <clinit> 끝
       |
       +-- aVal = 1 + 1 = 2
  A <clinit> 끝
```

**각 값**

- `A.aVal` 을 먼저 읽으면 -> `A.aVal = 2`, `B.bVal = 1`
- `B.bVal` 을 먼저 읽으면 -> `B.bVal = 2`, `A.aVal = 1`

**읽는 순서를 바꾸면 달라지는가**

- **달라진다.** 같은 소스, 같은 JVM 인데 **읽는 순서가 값을 정한다.**
- JVM 은 "이 스레드가 이미 이 클래스를 초기화하는 중"이면 재진입을 **그냥 통과**시킨다.\
  그래야 데드락이 안 나기 때문이다 — 안전성을 얻고 **정확성을 잃은 거래**다.
- 함의: `static` 필드끼리 서로를 참조하는 구조는 **테스트 실행 순서에 따라 값이 바뀐다.**\
  단위 테스트에서만 통과하고 전체 실행에서 깨지는 전형적 형태다.

### 9. 어디에 무엇을 쓰나

**생성자가 셋인데 공통 초기화가 있다면**

- **인스턴스 초기화 블록**에 쓴다. 세 생성자에 모두 복사된다.
- **대안이 더 낫다**: 생성자 둘이 `this(...)` 로 하나에 위임하고, 그 하나에만 공통 코드를 둔다.\
  이쪽이 읽는 사람에게 순서가 명시적이다.
- 초기화 블록이 정말 필요한 자리는 **생성자를 못 쓰는 곳** — 익명 클래스다.

**`static` 블록에 무거운 파일 읽기를 넣으면**

- **언제 도는지 예측이 어렵다**(6번). 상수 하나만 쓰면 아예 안 돌 수도 있다.
- 거기서 예외가 나면 `ExceptionInInitializerError` 가 되고, **그 클래스는 그 이후로 못 쓰게 된다.**\
  실행 결과 (`ClinitFail.java` — 같은 필드를 두 번 읽었다):

  ```text
  1번째: java.lang.ExceptionInInitializerError / cause=java.lang.ArithmeticException: / by zero
  2번째: java.lang.NoClassDefFoundError / cause=java.lang.ExceptionInInitializerError: Exception java.lang.ArithmeticException: / by zero [in thread "main"]
  ```

  두 번째부터는 예외 이름이 **`NoClassDefFoundError`** 로 바뀐다.\
  클래스가 없어서가 아니라 **초기화에 실패한 상태로 굳었기 때문**인데, 이름만 보면 클래스패스 문제로 오해하기 쉽다.
- 실패를 감당할 수 있는 자리(명시적 `init()`·DI 컨테이너)로 옮긴다.

**락 없는 지연 싱글턴이 기대는 규칙**

```java
class Config {
    private static class Holder { static final Config INSTANCE = new Config(); }
    static Config get() { return Holder.INSTANCE; }
}
```

- 기대는 규칙은 둘이다.
  1. **클래스 초기화는 첫 사용 시점까지 미뤄진다**(§12.4.1) -> `get()` 을 부를 때까지 객체가 안 생긴다.
  2. **`<clinit>` 은 JVM 이 락으로 보호해 딱 한 번만 돈다** -> 내가 `synchronized` 를 쓸 필요가 없다.
- `Holder` 를 따로 둔 이유는 `Config` 자체가 다른 이유로 초기화되어도 `INSTANCE` 는 안 만들어지게 하려는 것이다.
- 메모리 가시성 보장 자체는 [`../../언어-특성/README.md`](../../언어-특성/README.md) §9(happens-before)가 정본이다.

**이 주제가 다루지 않는 것**

- **클래스 로딩·링킹**(어느 클래스로더가 어디서 바이트코드를 읽어 오나, 검증·준비 단계)은 [`../../언어-특성/README.md`](../../언어-특성/README.md) §3 이 정본이다.
- 이 주제는 그 뒤의 **초기화 단계 하나**만 다룬다.
- **상속에서 메서드가 재정의되고 필드는 숨겨지는 비대칭**은 목록의 **09번 주제**가 정본이다.

---

## 이 주제를 확인한 실행 목록

| 프로그램 | 무엇을 확인했나 | 돌린 JDK |
|---|---|---|
| `InitOrder` | 9단계 순서, 두 번째 `new` 에서 static 이 빠짐 | 17 · 21 · 25 (동일) |
| `Textual` | 블록/필드의 상대 순서가 소스 텍스트 순서임 | 21 |
| `ThisChain` + `javap -c -p` | 초기화 블록이 `super()` 부르는 생성자에만 복사됨 | 21 |
| `CtorTrap2` | 부모 생성자에서 자식 메서드 호출 -> `null` | 21 |
| `ConstFold` + `javap -c -p` | 상수 접기로 `getfield` 가 하나만 남음 | 17 · 21 · 25 (동일) |
| `WhenClinit` | 상수 변수 읽기·배열 생성은 `<clinit>` 을 안 일으킴 | 17 · 21 · 25 (동일) |
| `Forward` | 전방 쓰기가 필드 초기화식에 덮임 | 21 |
| `ForwardRead` `javac` | 전방 읽기는 `illegal forward reference` 컴파일 에러 | 21 |
| `Cycle` / `Cycle2` | 순환 초기화 — 읽는 순서가 값을 정함 | 21 |
