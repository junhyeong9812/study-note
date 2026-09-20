# java/syntax/29 — 람다: 문법·변수 캡처·`this` 의 의미 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·에러·역어셈블은 **Temurin JDK 21.0.5 에서 실제로 돌려 얻은 것**이다.\
> 프로그램 17개(+ 보조 2개)를 17.0.13 · 21.0.5 · 25.0.1 에서 각각 돌렸다. **달랐던 것은 11번 답에 모아 두었다.**\
> javadoc 인용은 `21.0.5-tem/lib/src.zip` 의 원문이다.\
> 역어셈블 출력에 보이는 `\u0001` 은 `javap -v` 가 문자열 이어붙이기 틀을 표시하는 방식이며, **화면에 나온 그대로**다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 컴파일하면 클래스 파일이 몇 개 나오나

**출력** (`Ex.java (29-c)` · `javac Ex.java` 뒤 `ls *.class`)

```text
Ex$1.class
Ex.class
```

**왜 그런가**

- **두 개**다. 람다를 둘이나 썼는데 `Ex$2.class`·`Ex$3.class` 가 없다.
- 있는 `Ex$1.class` 는 **익명 클래스 하나** 몫이다.
- 즉 **람다는 컴파일 시점에 타입을 만들지 않는다.**

**람다 둘은 각각 어떤 클래스 파일이 되는가**

- **아무 클래스 파일도 되지 않는다.**
- 대신 바깥 클래스(`Ex.class`) 안에 **합성 메서드**로 남는다(2번).
- 객체는 **실행 시점에** 만들어진다 — 런타임 클래스 이름이 `Ex$$Lambda/0x...` 다(8번).

**람다 자리에 무엇이 컴파일되는가**

```text
       3: invokedynamic #7,  0              // InvokeDynamic #0:get:()Ljava/util/function/Supplier;
       8: astore_2
       9: iload_1
      10: invokedynamic #11,  0             // InvokeDynamic #1:get:(I)Ljava/util/function/Supplier;
      15: astore_3
      16: new           #14                 // class Ex$1
      19: dup
      20: iload_1
      21: invokespecial #16                 // Method Ex$1."<init>":(I)V
```

- 람다 자리에 **`invokedynamic`** 이 하나씩 있다. `new` 가 없다.
- 익명 클래스 자리에만 `new Ex$1` + `invokespecial <init>` 가 있다 — **평범한 객체 생성**이다.

**그 명령이 첫 실행에서 부르는 메서드**

```text
BootstrapMethods:
  0: #72 REF_invokeStatic java/lang/invoke/LambdaMetafactory.metafactory:(Ljava/lang/invoke/MethodHandles$Lookup;Ljava/lang/String;Ljava/lang/invoke/MethodType;Ljava/lang/invoke/MethodType;Ljava/lang/invoke/MethodHandle;Ljava/lang/invoke/MethodType;)Ljava/lang/invoke/CallSite;
    Method arguments:
      #60 ()Ljava/lang/Object;
      #61 REF_invokeStatic Ex.lambda$main$0:()Ljava/lang/String;
      #64 ()Ljava/lang/String;
```

- **`java.lang.invoke.LambdaMetafactory.metafactory`** 다.
- 두 번째 인자가 **실제 본문**을 가리킨다 — `Ex.lambda$main$0`.
- 첫 실행에 한 번 연결되고 그 뒤로는 그 결과를 재사용한다.

> **`invokedynamic`** — 무엇을 부를지 첫 실행에서 정하는 바이트코드 명령.\
> 예: 람다 자리. 위 출력에 같이 보이는 문자열 이어붙이기(`makeConcatWithConstants`)도 이것이다.

### 2. 캡처 유무에 따라 합성 메서드가 어떻게 달라지나

**출력** (`Ex.java (29-c)` · `javap -c -p Ex.class` 의 끝부분)

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

**몇 개이며 이름은**

- **두 개.** `lambda$main$0` 과 `lambda$main$1`.
- 이름 규칙은 `lambda$` + **둘러싼 메서드 이름** + `$` + **그 클래스 안에서 몇 번째 람다인지**.
- `javap -v` 로 보면 플래그에 `ACC_SYNTHETIC` 이 붙어 있다 — 소스에 없는 메서드라는 표시다.

**캡처 없는 람다의 시그니처**

- `private static java.lang.String lambda$main$0()` — **인자 0개.**
- 호출 자리도 `InvokeDynamic #0:get:()Ljava/util/function/Supplier;` — **넘기는 값이 없다.**

**캡처 있는 람다의 시그니처**

- `private static java.lang.String lambda$main$1(int)` — **인자 1개.**
- 호출 자리는 `InvokeDynamic #1:get:(I)Ljava/util/function/Supplier;` — `(I)` 가 붙었다.
- 그 앞줄의 `iload_1` 이 캡처할 `int` 를 스택에 올린다.

```text
캡처 없음                                   캡처 있음

  lambda$main$0()                            lambda$main$1(int)
  indy: get:()  -> Supplier                  indy: get:(I) -> Supplier
       |                                          |
  넘길 것이 없다                              iload_1 로 42 를 올려 넘긴다
```

**그 차이가 말해 주는 것**

- 캡처한 것이 **인자로 한 번 넘어갔을 뿐**이라는 것.
- 변수 자체가 아니라 **그 순간의 값**이 갔다 — 그러니 나중에 바깥 변수를 바꿔도 이미 넘어간 값은 안 바뀐다.
- **그래서 effectively final 이 필요하다.** 바꿀 수 있으면 두 값이 갈라져 어느 쪽이 맞는지 말할 수 없게 된다.

**익명 클래스는 어디에 담는가**

```text
class Ex$1 implements java.util.function.Supplier<java.lang.String> {
  final int val$captured;

  Ex$1();
    Code:
       0: aload_0
       1: iload_1
       2: putfield      #1                  // Field val$captured:I
```

- **`final` 필드**에 담는다. 생성자 인자로 받아서 넣는다.
- 이름이 `val$captured` 다 — `val$` 접두어가 「캡처한 지역 변수」 표시다.
- **둘 다 값 복사**다. 방식만 인자냐 필드냐로 다르다.

### 3. `this` 는 각각 무엇인가

**출력** (`Ex.java (29-a)` · 17 · 21 · 25 에서 한 글자도 다르지 않았다)

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

**왜 그런가**

- 람다는 **새 스코프를 열지 않는다.** 바깥 메서드 안에 그대로 있는 것과 같다.
- 익명 클래스는 **새 클래스 본문**이다. 그래서 `this` 가 자기 자신이 된다.
- 바깥에서 찍은 `this` 와 람다 안에서 찍은 `this` 가 **같다** — 그것이 이 절의 증거다.

**익명 클래스 안에서 바깥 `name` 에 닿으려면**

- **`Ex.this.name`.** 출력의 마지막 줄이 그것이다.
- 「바깥클래스이름 `.this`」가 바깥 인스턴스를 가리키는 문법이다.

**람다 안에서 바깥 `name` 을 가리는 방법**

- **없다.** 같은 이름을 다시 선언하면 컴파일 에러다(5번 (D)).
- 람다는 새 스코프가 아니므로 가릴 대상 자체가 없다.

**람다 객체의 클래스와 `this.getClass()` 는 같은가**

- **다르다.** 람다 안의 `this.getClass()` 는 `Ex` 이고, 람다 객체 자신의 클래스는 `Ex$$Lambda/0x...` 다.
- 이 둘이 헷갈리는 것이 이 주제의 대표적 오개념이다.\
  **람다 객체가 있다는 것과 람다 안의 `this` 가 그 객체라는 것은 다른 이야기**다.

> **익명 클래스(anonymous class)** — `new 타입() { ... }` 로 그 자리에서 만드는 이름 없는 클래스.\
> 예: 위 출력의 `Ex$1` 이 그것이고, 실제로 `Ex$1.class` 파일이 생긴다.

### 4. 캡처 뒤에 바꿀 수 있는 것은 무엇인가

**출력** (`Ex.java (29-b)` · 17 · 21 · 25 동일)

```text
만들 때   : 지역 10 / 필드 1 / static 100 / 배열칸 1000
바꾼 뒤   : 지역 10 / 필드 2 / static 200 / 배열칸 2000
-- 지역 변수 10 만 그대로다 --

== 참조 캡처는 객체를 얼리지 않는다 ==
만들 때   : sb = 처음
바꾼 뒤   : sb = 처음+덧붙임
```

**무엇이 바뀌고 무엇이 안 바뀌는가**

| 대상 | 바뀌나 |
|---|---|
| 지역 변수 `local` | **안 바뀐다** (애초에 바꾸면 컴파일 에러) |
| 인스턴스 필드 `field` | 바뀐다 |
| `static` 필드 `staticField` | 바뀐다 |
| 배열 원소 `box[0]` | 바뀐다 |

**필드가 바뀌는 이유**

- **람다가 캡처한 것은 필드가 아니라 `this` 다.**
- `this` 를 통해 **그때그때 필드를 읽는다** — 10번의 바이트코드가 그것을 보여 준다(`aload_0` 다음 `getfield`).
- `static` 필드는 아무것도 캡처하지 않고 `getstatic` 으로 바로 읽는다.
- 그래서 **필드에는 effectively final 제약이 없다.**

**`StringBuilder` 를 캡처한 뒤 `append` 하면**

- **보이는 값이 바뀐다** — `처음` 에서 `처음+덧붙임` 이 됐다.
- 캡처한 것은 **참조 값**이고, 그 참조가 가리키는 객체 내부는 자유롭게 바뀐다.
- 「캡처는 값 복사」는 **참조도 값이라는 뜻**이지 객체가 얼어붙는다는 뜻이 아니다.\
  자바의 모든 전달이 값 전달인 것과 같은 이야기다 — [`../03-variables-and-assignment/`](../03-variables-and-assignment/).

### 5. 어느 줄이 컴파일 에러인가

**어느 것이 컴파일되나** (아래 다섯 조각을 각각 따로 `javac` 에 넣어 본 결과다)

| | 결과 |
|---|---|
| (A) | 컴파일 에러 |
| (B) | 컴파일 에러 (에러 **2개**) |
| (C) | 컴파일 에러 |
| (D) | 컴파일 에러 |
| (E) | **컴파일된다** — 출력 `익명 클래스 안 / 바깥` |

**컴파일되는 것**

- **(E)뿐**이다. 익명 클래스로 바꾼 것만 된다.

**(A)의 에러 메시지와 가리키는 줄** (`Ex.java (29-e1)`)

```text
Ex.java:6: error: local variables referenced from a lambda expression must be final or effectively final
        Supplier<Integer> s = () -> count;
                                    ^
1 error
```

- 에러는 **대입한 7번째 줄이 아니라 캡처한 6번째 줄**을 가리킨다.
- 대입이 람다보다 **뒤에 있어도** 걸린다 — 컴파일러는 메서드 전체를 보고 effectively final 여부를 판정한다.

**(B)의 에러 개수** (`Ex.java (29-e2)`)

```text
Ex.java:6: error: local variables referenced from a lambda expression must be final or effectively final
        Supplier<Integer> s = () -> { count++; return count; };   // 람다 안에서 대입
                                      ^
Ex.java:6: error: local variables referenced from a lambda expression must be final or effectively final
        Supplier<Integer> s = () -> { count++; return count; };   // 람다 안에서 대입
                                                      ^
2 errors
```

- **둘.** 대입한 자리(`count++`)와 읽은 자리(`return count`)가 각각 걸린다.

**(C)** (`Ex.java (29-e3)`)

```text
Ex.java:5: error: non-static variable this cannot be referenced from a static context
        Supplier<String> s = () -> this.toString();   // static 문맥의 this
                                   ^
1 error
```

- 람다의 `this` 는 **바깥 문맥의 `this`** 다. 바깥이 `static` 이면 `this` 자체가 없다.
- 3번의 결론과 같은 사실을 반대쪽에서 보여 주는 에러다.

**(D)의 에러 메시지와 그 함의** (`Ex.java (29-e4)`)

```text
Ex.java:7: error: variable msg is already defined in method main(String[])
            String msg = "람다 안";        // 바깥 지역 변수와 같은 이름
                   ^
1 error
```

- 메시지가 **`already defined in method main`** 이다.
- 컴파일러가 「람다 본문은 `main` 안이다」라고 말하고 있다 — **람다는 새 스코프를 열지 않는다.**

**(E)가 되는 이유** (`Ex.java (29-e5)`)

```text
익명 클래스 안 / 바깥
```

- 익명 클래스는 **새 클래스 본문**이라 새 스코프가 열린다. 바깥 이름을 가릴 수 있다.
- 가려진 바깥 것은 여전히 살아 있다 — 출력의 `/ 바깥` 이 그 증거다.

### 6. 루프 변수를 캡처하면

**출력** (`Ex.java (29-i)` · (B)만 따로 `Ex.java (29-j)`)

```text
향상된 for : 가나다
기본 for + 사본 : 012
```

```text
Ex.java:8: error: local variables referenced from a lambda expression must be final or effectively final
            subs.add(() -> "" + i);      // i 는 회전마다 바뀐다
                                ^
1 error
```

**컴파일되는 것**

- **(A)와 (C).** (B)는 컴파일 에러다.

**(A)가 되는 이유**

- **향상된 `for` 의 변수는 회전마다 새로 만들어진다.**
- 한 회전 안에서는 한 번도 대입되지 않으므로 effectively final 이다.

**(C)가 되는 이유**

- 루프 **본문 안에서 새 지역 변수**를 만들었다. 그 변수도 회전마다 새로 생긴다.
- 값을 읽어 복사한 뒤 그 사본을 캡처하므로 제약을 피한다.

**(B)가 안 되는 이유**

- 기본 `for` 의 인덱스는 **변수 하나를 계속 바꾼다.** 회전마다 새로 생기지 않는다.
- 캡처는 값 하나를 넘기는 것인데, 그 값이 계속 변한다면 어느 값을 넘길지 정할 수 없다.

**(A)·(C) 의 출력** (위 실행 결과의 두 줄이다)

- (A) `가나다` — 세 람다가 각각 다른 문자열을 붙잡았다.
- (C) `012` — 사본 셋이 각각 0·1·2 를 붙잡았다.

### 7. 스택트레이스에 무엇이 뜨나

**출력** (`Ex.java (29-d)` · `Ex.` 로 시작하는 프레임은 17 · 21 · 25 에서 같았다)

```text
== 1. 람다에서 터졌을 때 ==
  at java.base/java.lang.NumberFormatException.forInputString(NumberFormatException.java:67)
  at java.base/java.lang.Integer.parseInt(Integer.java:662)
  at java.base/java.lang.Integer.parseInt(Integer.java:778)
  at Ex.lambda$main$0(Ex.java:9)
  at java.base/java.lang.Iterable.forEach(Iterable.java:75)
  at Ex.main(Ex.java:9)
== 2. 익명 클래스에서 터졌을 때 ==
  at java.base/java.lang.NumberFormatException.forInputString(NumberFormatException.java:67)
  at java.base/java.lang.Integer.parseInt(Integer.java:662)
  at java.base/java.lang.Integer.parseInt(Integer.java:778)
  at Ex$1.accept(Ex.java:17)
  at Ex$1.accept(Ex.java:16)
  at java.base/java.lang.Iterable.forEach(Iterable.java:75)
  at Ex.main(Ex.java:16)
== 3. 메서드 참조에서 터졌을 때 ==
  at java.base/java.lang.NumberFormatException.forInputString(NumberFormatException.java:67)
  at java.base/java.lang.Integer.parseInt(Integer.java:662)
  at java.base/java.lang.Integer.parseInt(Integer.java:778)
  at Ex.boom(Ex.java:4)
  at java.base/java.lang.Iterable.forEach(Iterable.java:75)
  at Ex.main(Ex.java:25)
```

**람다에서 터지면**

- **`Ex.lambda$main$0`** 이 뜬다. 합성 메서드 이름 그대로다.
- 줄 번호(`Ex.java:9`)는 정확하다 — **어느 줄인지는 알 수 있고, 무슨 일을 하는 람다인지는 모른다.**
- 람다 순서가 바뀌면 번호도 바뀌므로 **로그를 그 이름으로 검색하지 못한다.**

**익명 클래스면**

- **`Ex$1.accept`** 가 뜨고, **두 줄** 나온다.
- 둘째 줄(`Ex.java:16`)이 **다리 메서드**다 — 제네릭 소거 때문에 `accept(Object)` 가 만들어져 `accept(String)` 을 부른다.

> **다리 메서드(bridge method)** — 제네릭이 소거된 시그니처와 실제 시그니처를 잇기 위해 컴파일러가 넣는 중계 메서드.\
> 예: `Consumer<String>` 을 구현하면 `accept(Object)` 가 하나 더 생겨 `accept(String)` 으로 넘긴다.

**메서드 참조면**

- **`Ex.boom`** — **실제 메서드 이름**이 그대로 뜬다.
- 리팩토링해도 이름이 따라가고, 로그에서 검색된다.

**람다 객체의 클래스는 나오는가**

- **안 나온다.** `Ex$$Lambda/0x...` 프레임이 세 JDK 어디에서도 출력되지 않았다.
- JVM 이 그 프레임을 감춘다 — 위 출력 그대로가 근거다.

**디버깅에 가장 유리한 것**

- **메서드 참조.** 이름이 의미를 담고 있고 안 바뀐다.
- 그 다음이 익명 클래스(적어도 클래스 단위로 구분된다), 람다가 가장 불리하다.
- 본문이 길어지면 메서드로 뽑아 **메서드 참조로 넘기는 것**이 이 문제를 그대로 해결한다 — [`../30-method-references/`](../30-method-references/).

### 8. 람다를 `==` 로 비교하면

**출력** (`Ex.java (29-f)` · JDK 21.0.5)

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

**캡처 없는 람다 두 개는**

- 이 실행에서는 **`==` 가 참**이었다. 같은 객체를 돌려줬다.
- 담을 상태가 없으니 하나로 충분하기 때문이다.

**캡처 있는 람다를 같은 값으로 두 번 만들면**

- **`==` 도 `equals` 도 거짓**이다.
- 람다는 `equals` 를 재정의하지 않는다 — `Object` 의 것, 즉 참조 비교다.

**보장인가**

- **보장이 아니다.** `LambdaMetafactory` javadoc 원문(`src.zip`)이 직접 부정한다.

  > Capture may involve allocation of a new function object, or may return
  > a suitable existing function object. The identity of a function object
  > produced by capture is unpredictable, and therefore identity-sensitive
  > operations (such as reference equality, object locking, and `System.identityHashCode()`)
  > may produce different results in different implementations, or even upon
  > different invocations in the same implementation.

- 「참조 동일성은 예측할 수 없다」·「같은 구현에서 호출할 때마다 달라질 수도 있다」고 못박고 있다.
- 그러므로 위 `a == b ? true` 는 **관찰이지 보장이 아니다.**

**리스너 해제**

- **아무것도 안 빠진다.** 예외도 경고도 없다 — 조용히 실패한다.
- 해결: 만든 람다를 변수에 담아 두고 **그 변수로** 해제한다.

**`synchronized`**

- **안 된다.** 위 인용이 object locking 을 같이 든다.
- 같은 객체가 재사용되면 서로 무관한 두 코드가 같은 락을 잡게 된다.

### 9. 람다를 직렬화하면

**출력** (`Ex.java (29-g)`)

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

**무슨 예외인가**

- **`java.io.NotSerializableException`**, 메시지는 람다의 런타임 클래스 이름이다.

**직렬화하려면**

- 타깃 타입이 `Serializable` 을 **같이** 구현해야 한다.
- 두 길이 있다 — 인터페이스를 따로 선언(`interface SerSupplier<T> extends Supplier<T>, Serializable {}`)하거나,\
  교차 캐스트(`(Supplier<String> & Serializable) () -> ...`)를 쓴다. 둘 다 실제로 성공했다.

**직렬화된 바이트에 무엇이 들어가나** (`Ex3.java (29-g)` — 직렬화 바이트에서 길이 4 이상의 인쇄 가능 문자열만 뽑은 것)

```text
  java.lang.invoke.SerializedLambda
  implMethodKind
  capturedArgs
  capturingClass
  functionalInterfaceClass
  functionalInterfaceMethodName
  implClass
  implMethodName
  implMethodSignature
  instantiatedMethodType
  SerSup
  get
  ()Ljava/lang/Object;
  Ex3
  lambda$main$ef07458b$1
  ()Ljava/lang/String;
```

- 저장되는 클래스는 **`java.lang.invoke.SerializedLambda`** 다.
- 필드는 `implMethodKind`·`capturedArgs`·`capturingClass`·`functionalInterfaceClass`·\
  `functionalInterfaceMethodName`·`implClass`·`implMethodName`·`implMethodSignature`·`instantiatedMethodType`.
- 즉 **「어느 클래스의 어느 합성 메서드인가」를 문자열로 저장**한다. 코드가 아니라 좌표를 저장한다.
- (위 목록은 직렬화 스트림의 구분 바이트를 걷어낸 것이다. 원시 바이트에는 각 이름 뒤에 `t`·`q` 같은 스트림 태그 문자가 붙어 나온다.)

**합성 메서드 이름이 어떻게 다른가**

```text
  private static java.lang.Object $deserializeLambda$(java.lang.invoke.SerializedLambda);
  private static java.lang.String lambda$main$ef07458b$1();
```

- 보통 람다는 `lambda$main$0`, 직렬화 가능 람다는 **`lambda$main$ef07458b$1`** 이다.
- 가운데에 **해시가 박힌다.** 같은 클래스 안에 둘 다 있으면 나란히 확인할 수 있다.
- 부트스트랩도 다르다 — `metafactory` 가 아니라 `altMetafactory` 를 쓰고 플래그 `5` 가 붙는다.
- 클래스에 `$deserializeLambda$` 라는 합성 메서드가 하나 더 생긴다.

**그래서 무엇이 깨지는가**

- **소스를 고치면 역직렬화가 깨진다.** 람다를 한 줄 옮기거나 위쪽에 람다를 하나 추가하면 번호가 바뀐다.
- 시그니처가 바뀌면 해시도 바뀐다.
- 규칙: **람다를 저장하지 않는다.** 저장할 것은 데이터이지 코드가 아니다.

### 10. `this` 를 캡처한 람다의 합성 메서드

**출력** (`Ex.java (29-h)` · `javap -c -p Ex.class`)

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

**`static` 이 붙는가**

- **안 붙는다.** `private java.lang.String lambda$run$0()` — 인스턴스 메서드다.
- 캡처가 없는 쪽(`lambda$run$1`)에만 `static` 이 있다.

**`aload_0` 은 무엇인가**

- **`this`** 다. 인스턴스 메서드의 0번 지역 변수가 `this` 이기 때문이다.
- 그 다음 `getfield field` 로 바깥 인스턴스의 필드를 읽는다.
- **이것이 「람다 안의 `this` 는 바깥 인스턴스」의 바이트코드 근거**다. 수사가 아니다.

**호출 자리의 서술자**

```text
캡처 있음: InvokeDynamic #0:get:(LEx;)Ljava/util/function/Supplier;
캡처 없음: InvokeDynamic #1:get:()Ljava/util/function/Supplier;
```

- `(LEx;)` — **`Ex` 인스턴스 하나를 넘긴다.** 그 앞줄의 `aload_0` 이 `this` 를 올린다.
- 즉 **바깥 `this` 가 캡처된 값**이다. 2번의 `(I)` 와 완전히 같은 구조다.
- `javac --release 8` 로 다시 찍어도 같았고, 17 · 21 · 25 에서도 같았다.

**오래 사는 자료구조에 넣으면**

- **바깥 인스턴스가 같이 산다.** 람다가 `this` 를 붙잡고 있기 때문이다.
- 필드 하나만 쓰는 람다라도 **객체 전체**가 붙잡힌다.
- 피하려면 필요한 값을 지역 변수에 복사한 뒤 그것을 캡처한다(그러면 합성 메서드가 `static` 이 된다).
- 익명·inner 클래스의 같은 문제는 [`../12-nested-classes/`](../12-nested-classes/) 가 정본이다.

### 11. 언제 익명 클래스로 돌아가야 하나

**람다로 쓸 수 없는 세 가지**

1. **자기 자신을 가리켜야 할 때** — 람다 안의 `this` 는 바깥 인스턴스다.\
   재귀 리스너, 「한 번 불리면 자기를 해제하는 콜백」이 여기 걸린다.
2. **상태(필드)를 가져야 할 때** — 람다는 필드를 선언할 수 없다.
3. **메서드를 둘 이상 구현해야 할 때** — 타깃이 함수형 인터페이스가 아니면 람다가 안 들어간다\
   ([`../31-functional-interfaces/`](../31-functional-interfaces/) 「어디서 틀리나」).

덧붙여 **바깥 이름을 가려야 할 때**도 익명 클래스여야 한다(5번 (D)·(E)).

**기계적으로 바꾸면 안 되는 이유**

- **`this` 의 뜻이 조용히 바뀐다.** 5번 (C)처럼 컴파일 에러가 나면 다행이고,\
  바깥 클래스에도 같은 이름의 메서드가 있으면 **컴파일이 되면서 다른 것을 부른다.**
- 이름 가림도 마찬가지다 — 익명 클래스에서 가려져 있던 바깥 이름이 람다에서는 그대로 보인다.

**본문이 길어질 때**

- **메서드로 뽑고 메서드 참조로 넘긴다.**
- 스택트레이스가 읽히고(7번), 그 메서드에 테스트를 따로 붙일 수 있다.

**세 JDK 에서 달랐던 것**

| 무엇 | 17.0.13 | 21.0.5 | 25.0.1 |
|---|---|---|---|
| 람다 런타임 클래스 이름 | `Ex$$Lambda$1/0x...` | `Ex$$Lambda/0x...` | `Ex$$Lambda/0x...` |
| 그 16진수 부분 | 실행할 때마다 다르다 | 같음 | 같음 |
| JDK 내부 `Predicate` 의 합성 메서드 번호 | `and$0`·`negate$1`·`or$2`·`isEqual$3` | 같음 | **전부 `$0`** |
| `javap` 출력의 들여쓰기 | 기존 | 기존 | 오프셋이 두 칸 더 들어간다 (`diff -w` 로는 동일) |
| 스택트레이스의 JDK 내부 프레임 | 줄 번호가 다르다 | 다르다 | `List.of(...).forEach` 가 `ImmutableCollections$List12.forEach` 로 바뀌었다 |

- 17 에 있던 **일련번호 `$1` 이 21 에서 사라졌다.**
- 16진수 부분은 **같은 JDK 에서 두 번 돌려도 달랐다.**
- 25 에서는 **JDK 자신의 합성 메서드 번호 매김 규칙이 달라졌다.**
- **반대로, 내 코드의 `Ex.lambda$main$0`·`Ex$1.accept`·`Ex.boom` 프레임은 세 JDK 에서 한 글자도 같았다.**\
  그래도 그것은 관찰이다 — 이름은 컴파일러가 정하는 구현 세부다.
- 결론: **이름·번호·동일성 어디에도 기대지 않는다.**\
  외울 것은 「컴파일러가 합성 메서드를 만들고 `invokedynamic` 으로 잇는다」는 **성질**이다.

---

## 실행 검증

| 프로그램 | 무엇을 확인했나 | 돌린 JDK |
|---|---|---|
| `Ex.java (29-a)` | 람다·익명 클래스·바깥의 `this` 와 이름 해석을 나란히 출력 | 17 · 21 · 25 (동일) |
| `Ex.java (29-b)` | 캡처 뒤 지역 변수·필드·static·배열칸·참조 대상의 변화 | 17 · 21 · 25 (동일) |
| `Ex.java (29-c)` | `ls *.class`, `javap -c -p`, `javap -v -p`(BootstrapMethods), `Ex$1` 의 `val$` 필드 | 17 · 21 · 25 (바이트코드 동일, 25 는 `javap` 들여쓰기만 다름) |
| `Ex.java (29-d)` | 람다·익명 클래스·메서드 참조의 스택트레이스 비교 | 17 · 21 · 25 (`Ex.` 프레임 동일) |
| `Ex.java (29-e1)`~`(29-e5)` | effectively final 위반 · 람다 내 대입 · static 문맥 `this` · 이름 재선언 · 익명 클래스 대조 | 17 · 21 · 25 (동일) |
| `Ex.java (29-f)` | 람다 런타임 클래스 이름, 캡처 유무별 `==`/`equals`, `isHidden` | 17 · 21 · 25 (**17 에서 클래스 이름이 다름**) |
| `Ex.java (29-g)` · `Ex2` · `Ex3` | `NotSerializableException`, 직렬화 성공 바이트 수, `SerializedLambda` 필드, 해시 박힌 합성 메서드 이름, `altMetafactory`, `$deserializeLambda$` | 17 · 21 · 25 (**17 에서 클래스 이름이 다름**) |
| `Ex.java (29-h)` | `this` 캡처 시 합성 메서드가 `static` 이 아님, 호출 자리 서술자 `(LEx;)` | 17 · 21 · 25 + `javac --release 8` (전부 동일) |
| `Ex.java (29-i)` · `(29-j)` | 향상된 `for` 는 캡처 가능, 기본 `for` 인덱스는 불가, 사본 우회 | 17 · 21 · 25 (동일) |
| `Ex.java (29-k)` · `(29-l)` · `(29-m)` | `var` 인자·괄호 생략 규칙과 그 위반 에러 둘 | 17 · 21 · 25 (동일) |
| `Ex.java (31-b)` | JDK 내부 `Function`·`Predicate`·`Consumer` 의 합성 메서드 목록 | 17 · 21 · 25 (**25 에서 번호가 다름**) |
| `src.zip` 열람 | `LambdaMetafactory` 의 identity 관련 원문, `FunctionalInterface` javadoc | 21 |

**구현 의존 항목** — 버전이 오르면 다시 돌려야 하는 것

- 람다 런타임 클래스 이름(`Ex$$Lambda...`) — 17에서 21로 가며 이미 바뀌었다.
- 합성 메서드 번호 매김 — 21에서 25로 가며 JDK 내부 기준이 바뀌었다.
- 캡처 없는 람다의 `==` 결과 — javadoc 이 보장을 명시적으로 부정한다.
- 스택트레이스의 JDK 내부 프레임 — 21에서 25로 가며 `forEach` 구현이 바뀌었다.
- `javap` 출력 형식 자체 — 25 에서 들여쓰기가 달라졌다.
