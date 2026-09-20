# java/syntax/03 — 변수와 대입: 전부 값 전달·`final`·effectively final — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·컴파일 에러·바이트코드는 **Temurin JDK 21.0.5 에서 실제로 돌려 얻은 것**이다.\
> 값 전달·`final` 실행 결과와 캡처 관련 컴파일 에러 문구는 **17.0.13 · 25.0.1** 에서도 같았다(관찰이다 — 보장은 JLS 인용으로만 적었다).\
> 바이트코드는 `javap -c -p` 출력을 그대로 옮겼다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 이 세 호출이 끝난 뒤 값은 무엇인가

**출력** (`Ex.java (03-a)`, JDK 21.0.5 — 17·25 에서도 동일)

```text
(C) int          n = 1
(A) 필드 변경     p1 = Point(99)
(B) 참조 재대입   p2 = Point(1)
```

**`n`, `p1`, `p2` 는 각각 무엇인가**

- `n` -> **1** (안 바뀌었다)
- `p1` -> **`Point(99)`** (바뀌었다)
- `p2` -> **`Point(1)`** (안 바뀌었다)

**왜 결과가 갈리는가**

```text
mutateField(p1) — 창고를 고쳤다                 reassign(p2) — 쪽지를 고쳤다
+----------------------------------+           +----------------------------------+
| 호출 중                          |           | 호출 중                          |
|   p1 [#7] ---+                   |           |   p2 [#7] ---> [창고#7 x=1]      |
|              +--> [창고#7 x=99]  |           |   p  [#9] ---> [창고#9 x=99]     |
|   p  [#7] ---+                   |           |                                  |
| 쪽지 둘이 같은 창고를 본다        |           | 쪽지 둘이 다른 창고를 본다        |
| 호출 후 p1.x == 99               |           | 호출 후 p2.x == 1                |
+----------------------------------+           +----------------------------------+
```

- `mutateField` 는 복사된 쪽지의 **주소를 따라가 창고 안을 고쳤다.** 창고는 하나라 밖에서도 보인다.
- `reassign` 은 복사된 쪽지에 **다른 주소를 적었다.** 원본 쪽지는 손대지 않았으므로 밖에서는 아무 일도 없었다.
- 두 메서드가 받은 것은 **똑같이 "참조의 복사본"** 이다. 다른 것은 그 복사본으로 무엇을 했느냐뿐이다.

**복사된 것은 각각 무엇인가**

| 호출 | 복사된 것 | 공유된 것 |
|---|---|---|
| `changePrimitive(n)` | `int` 값 `1` | 없음 |
| `mutateField(p1)` | 참조(주소 #7) | 창고 #7 자체 |
| `reassign(p2)` | 참조(주소 #7) | 창고 #7 자체 — 다만 메서드가 안 건드렸다 |

> **값 전달(pass by value)** — 호출할 때 인자의 값을 복사해 파라미터에 대입하는 것. 자바의 유일한 전달 방식이다.\
> 예: `f(p)` 에서 복사되는 것은 `p` 가 든 참조 한 칸이고, 객체는 복사되지 않는다.

### 2. 한 메서드가 둘을 다 하면

**출력** (`Ex.java (03-a)`)

```text
(D) 둘 다        p3 = Point(50)
```

**호출이 끝난 뒤 `p3` 는 무엇인가**

- **`Point(50)`** 이다.

**어느 것이 보이고 어느 것이 안 보이는가**

```text
p3 [#7] ---> [창고#7 x=1]
   (1) p.x = 50          -> 원래 창고. 보인다
p3 [#7] ---> [창고#7 x=50]        p [#7]
   (2) p = new Point(77) -> 쪽지를 돌렸다. 여기서 연결이 끊긴다
p3 [#7] ---> [창고#7 x=50]        p [#9] ---> [창고#9 x=77]
   (3) p.x = 88          -> 새 창고. 안 보인다
p3 [#7] ---> [창고#7 x=50]        p [#9] ---> [창고#9 x=88]
```

- **50 만 보인다.** 77 과 88 은 안 보인다.
- 규칙 한 줄: **재대입한 줄 이후의 변경은 호출자에게 전달되지 않는다.**

**88 을 적은 객체는 어떻게 되는가**

- 메서드가 끝나면 파라미터 `p` 가 사라지고, **창고 #9 를 가리키는 쪽지가 하나도 남지 않는다.**
- 아무도 도달할 수 없으므로 GC 대상이 된다. 88 이라는 값은 어디에도 기록되지 않는다.

### 3. `swap` 은 왜 불가능한가

**출력** (`Ex.java (03-a)`)

```text
(E) swap 후      a = Point(1)  b = Point(2)
```

**호출 후 호출자의 `a`, `b`**

- **아무것도 안 바뀐다.** `a` 는 `Point(1)`, `b` 는 `Point(2)` 그대로다.

```text
  호출자    a [#7]   b [#8]
  파라미터  a [#7]   b [#8]      <- 쪽지 두 장을 복사
  t = a           t [#7]
  a = b     a [#8]               <- 복사본만 바뀐다
  b = t              b [#7]
  메서드 끝 -> 복사본 셋 다 소멸
  호출자    a [#7]   b [#8]      <- 손댄 흔적이 없다
```

**왜 이것이 증명이 되는가**

- 참조 전달이 있는 언어(C# 의 `ref`, C++ 의 `&`)에서는 **이 코드가 그대로 동작한다.**
- 자바에서 동작하지 않는다는 것은 **호출자의 변수 자체에 접근할 수단이 언어에 없다**는 뜻이다.
- 1번의 `reassign` 과 같은 현상이지만, `swap` 은 **참조 전달이라면 반드시 되어야 할 일**이라 반증으로 더 강하다.

**두 값을 실제로 바꾸려면**

1. **바뀐 값을 담은 객체를 돌려준다** — `return new int[]{b, a};` 또는 `record Pair(T a, T b)`.
2. **가변 컨테이너의 내용을 바꾼다** — `list.set(0, ...)`, `arr[0] = ...`, 객체 필드 대입.\
   이것은 "쪽지를 바꾸는 것"이 아니라 "창고 안을 바꾸는 것"이다.
3. `Collections.swap(list, i, j)` 가 실제로 하는 일이 2번이다.

### 4. `final` 이 막는 것과 안 막는 것

**출력** (`Ex.java (03-b)`)

```text
final int[]        NUMS[0] = 99
final List         NAMES   = [추가됨]
final StringBuilder SB     = ab
```

**컴파일되는 것과 안 되는 것**

| 줄 | 결과 |
|---|---|
| `NUMS[0] = 99;` | **컴파일된다.** 창고 안을 고쳤다 |
| `NAMES.add("추가됨");` | **컴파일된다.** 창고 안을 고쳤다 |
| `NUMS = new int[]{9};` | **컴파일 에러.** 쪽지를 고치려 했다 |

`final` 재대입을 실제로 시도하면 이렇게 나온다(`Ex.java (03-c1)`).

```text
Ex.java:4: error: cannot assign a value to final variable x
        x = 2;
        ^
1 error
```

**`final` 이 거는 제약을 한 문장으로**

- **"이 변수에는 값을 정확히 한 번만 대입할 수 있다."**
- 그 값이 가리키는 대상의 내부에 대해서는 **아무 말도 하지 않는다.**

**`public static final int[] PRIMES` 가 위험한 이유**

```text
겉보기 — 상수처럼 읽힌다                     실제 — 누구나 고칠 수 있다
+-------------------------------+          +-------------------------------+
| public static final           |          | Other.PRIMES[0] = 999;        |
|   int[] PRIMES = {2, 3, 5};   |          |   -> 컴파일도 되고 실행도 된다 |
| 대문자 이름 + final           |          | 그 뒤 모든 사용처가 오염된다   |
+-------------------------------+          +-------------------------------+
```

- 배열에는 `Collections.unmodifiableList` 같은 **"수정 불가 뷰"가 없다.**
- 방어는 **복사본을 돌려주는 메서드**뿐이다.

```java
private static final int[] PRIMES = {2, 3, 5};
public static int[] primes() { return PRIMES.clone(); }
```

- 다차원 배열이면 `clone()` 도 얕아서 부족하다 — 자세한 것은 [`../05-arrays/`](../05-arrays/).

### 5. 이 코드가 컴파일되지 않는 이유와 에러가 가리키는 줄

**컴파일 에러** (`Ex.java (03-c2)`, JDK 21.0.5 — 17·25 에서도 문구가 같았다)

```text
Ex.java:4: error: local variables referenced from a lambda expression must be final or effectively final
        Runnable r = () -> System.out.println(counter);
                                              ^
1 error
```

**에러 문구**

- `local variables referenced from a lambda expression must be final or effectively final`

**에러 줄과 실제 원인 줄이 같은가**

- **다르다.** 에러는 4번 줄(람다)을 가리키는데, **원인은 5번 줄 `counter = 1;`** 이다.

```text
  3:  int counter = 0;
  4:  Runnable r = () -> ... counter ...;    <- 에러가 여기 찍힌다
  5:  counter = 1;                           <- 진짜 원인은 여기다
```

- 컴파일러 입장에서는 **"캡처하는 자리"에서 위반이 발견**되므로 그 줄을 가리킨다.
- 처음 이 에러를 볼 때 가장 헷갈리는 자리다 — **아래쪽에서 재대입한 줄을 찾아야 한다.**

**`counter = 1;` 을 지우면**

- `counter` 가 **effectively final** 이 되어 컴파일된다.
- 실행하면 캡처한 값이 찍힌다(`Ex.java (03-b)` 의 출력).

```text
람다가 캡처한 counter = 7
```

- 즉 `final` 이라고 **쓰지 않아도** 조건만 만족하면 캡처된다. 이것이 Java 8 이 완화한 부분이다.

### 6. 어느 반복문의 변수가 캡처되는가

**컴파일 결과**

- (A) 기본 `for` — **컴파일 에러** (`Ex.java (03-c3)`)
- (B) 향상된 `for` — **컴파일된다**

```text
Ex.java:7: error: local variables referenced from a lambda expression must be final or effectively final
            rs.add(() -> System.out.print(i));
                                          ^
1 error
```

(B)의 실행 결과는 이렇다(`Ex.java (03-b)`).

```text
for-each 캡처 = abc
```

**둘의 차이를 만드는 것**

```text
기본 for                                     향상된 for
+--------------------------------+          +--------------------------------+
| int i = 0;                     |          | 반복마다 새 변수 s 를 만든다    |
| i < 3 을 검사                   |          |   s = "a"  (첫 번째 s)         |
| i++  <- 같은 변수에 재대입       |          |   s = "b"  (두 번째 s, 다른 변수)|
|                                |          |   s = "c"  (세 번째 s)          |
| 변수 하나가 0,1,2 를 거친다      |          | 변수 셋이 각각 한 번 대입된다    |
| -> effectively final 아님       |          | -> 각각 effectively final       |
+--------------------------------+          +--------------------------------+
```

- 기본 `for` 의 `i` 는 **한 변수가 여러 값을 거친다.** 캡처 시점의 값이 무엇이어야 하는지 정할 수 없다.
- 향상된 `for` 의 변수는 **반복마다 새로 선언된 것**으로 취급된다. 각각 한 번만 대입되므로 캡처된다.
- 그래서 리스트를 돌며 람다를 모으는 코드는 **향상된 `for` 로 쓰면 그냥 된다.**

기본 `for` 로도 하고 싶으면 **반복 안에서 지역 변수로 한 번 받으면** 된다.

```java
for (int i = 0; i < 3; i++) {
    int captured = i;                       // 반복마다 새 변수 — effectively final
    rs.add(() -> System.out.print(captured));
}
```

### 7. effectively final 은 왜 생겼는가

**익명 클래스가 캡처하면 클래스 파일에 무엇이 생기는가**

**`javap -c -p 'Ex$1.class'` 출력 그대로** (`Ex.java (03-d)`, JDK 21.0.5)

```text
class Ex$1 implements java.lang.Runnable {
  final int val$n;

  Ex$1();
    Code:
       0: aload_0
       1: iload_1
       2: putfield      #1                  // Field val$n:I
       5: aload_0
       6: invokespecial #7                  // Method java/lang/Object."<init>":()V
       9: return

  public void run();
    Code:
       0: getstatic     #13                 // Field java/lang/System.out:Ljava/io/PrintStream;
       3: aload_0
       4: getfield      #1                  // Field val$n:I
       7: invokevirtual #19                 // Method java/io/PrintStream.println:(I)V
      10: return
}
```

- **`val$n` 이라는 필드가 생긴다.** 소스에는 없는 필드다.
- 생성자가 `putfield` 로 **캡처한 값을 복사해 넣는다.**
- `run()` 은 바깥 변수가 아니라 **이 복사본을 `getfield` 로 읽는다.**

**그 필드의 제어자**

- **`final`** 이다 — `final int val$n;`
- 복사한 뒤에는 바꿀 길이 자체가 없다.

**재대입을 허용하면 생기는 모순**

```text
허용했다고 가정하면

  바깥 n [ 7 ] ---- 캡처(값 복사) ----> val$n [ 7 ]
  바깥에서 n = 1
  바깥 n [ 1 ]                          val$n [ 7 ]   <- 어긋난다

  람다를 실행하면 7 이 찍힌다. 바깥은 1 이다.
  "같은 변수"라고 배운 것이 두 값을 갖는다.
```

- 둘 중 무엇이 맞는지 **언어가 답할 수 없다.** 동기화하려면 변수 하나마다 힙 상자를 만들어야 한다(다른 언어들이 그렇게 한다).
- 자바는 그 비용과 모호함 대신 **"안 바뀌는 변수만 캡처하게" 막는 길**을 택했다.
- 그래서 effectively final 은 **제약이 아니라 값 복사 구현의 결과**다.

**람다는 캡처한 값을 어디로 넣는가**

**`javap -c -p Ex.class` 출력 그대로**

```text
  static java.lang.Runnable capture(int);
    Code:
       0: iload_0
       1: invokedynamic #16,  0             // InvokeDynamic #0:run:(I)Ljava/lang/Runnable;
       6: areturn
```

- **`invokedynamic` 의 인자로 들어간다.** 시그니처 `run:(I)Ljava/lang/Runnable;` 의 `(I)` 가 캡처한 `int` 하나다.
- 람다 본문은 별도의 `private static` 메서드로 뽑힌다.

```text
  private static void lambda$capture$0(int);
    Code:
       0: getstatic     #23                 // Field java/lang/System.out:Ljava/io/PrintStream;
       3: iload_0
       4: invokevirtual #29                 // Method java/io/PrintStream.println:(I)V
       7: return
```

- 익명 클래스는 **클래스 파일 하나 + 필드**, 람다는 **메서드 하나 + `invokedynamic` 인자**다.
- 형태는 다르지만 **"캡처는 값 복사"** 라는 성질은 같다 — 그래서 제약도 같다.\
  (여기서 본 `val$n` 이라는 이름과 `invokedynamic` 이라는 명령은 **javac 의 구현 세부**다. 외울 것은 성질이다.)

### 8. 이 두 메서드의 바이트코드는 몇 줄인가

**출력** (`javap -c -p Ex.class`, `Ex.java (03-e)`, JDK 21.0.5 — 출력 그대로)

```text
  static int withFinal();
    Code:
       0: iconst_2
       1: ireturn

  static int withoutFinal();
    Code:
       0: iconst_1
       1: istore_0
       2: iload_0
       3: iconst_1
       4: iadd
       5: ireturn
```

**명령 수는 같은가 다른가**

- **다르다.** `withFinal` 은 2개, `withoutFinal` 은 6개다.

**어느 쪽이 짧고 왜인가**

- **`final` 쪽이 짧다.**
- `final int x = 1;` 은 **상수 변수**다(JLS §4.12.4) — `final` 이면서 컴파일 타임 상수로 초기화됐다.
- 그러면 컴파일러가 `x + 1` 을 **컴파일 타임에 `2` 로 접는다.** 변수 저장·읽기·덧셈이 통째로 사라진다.
- `final` 이 없으면 `x` 는 상수 변수가 아니므로 접을 수 없고, 슬롯에 저장했다가 읽어서 더한다.

```text
final 있음                                   final 없음
+---------------------------+               +---------------------------+
| 컴파일러: x 는 상수 1 이다  |               | 컴파일러: x 는 변수다      |
| x + 1 을 2 로 접는다       |               | 실행 시점에 더해야 한다    |
| -> iconst_2               |               | -> istore/iload/iadd      |
+---------------------------+               +---------------------------+
```

**`final` 의 런타임 비용에 대해 말할 수 있는 것**

- **지역 변수의 `final` 은 런타임 비용이 0이다.** 바이트코드에 흔적이 없다.
- 상수 초기화면 **오히려 코드가 줄어든다.**
- 그러므로 "`final` 을 붙이면 느려질까"라는 걱정은 근거가 없다.\
  다만 **접는 것(constant folding)은 javac 의 재량**이다 — JLS 가 요구하는 것은 "상수 변수다"라는 분류까지다.

`final` **필드**는 다르다 — 클래스 파일에 플래그로 남는다. `javap -p` 가 보여 준다.

```text
public class Ex {
  final int f;
  int g;
  ...
}
```

### 9. 지역 변수와 필드의 초기화 규칙 차이

**`int x;` 를 선언만 하고 읽으면**

**컴파일 에러** (`Ex.java (03-c5)`)

```text
Ex.java:4: error: variable x might not have been initialized
        System.out.println(x);
                           ^
1 error
```

- **컴파일이 안 된다.** 지역 변수는 확정 대입 규칙(JLS §16)의 대상이다.

**같은 선언을 필드로 하면**

- **그냥 된다.** 필드는 선언만 해도 **기본값으로 초기화**된다.

| 타입 | 필드 기본값 |
|---|---|
| `int`/`long`/`short`/`byte` | `0` |
| `double`/`float` | `0.0` |
| `char` | 코드 포인트 0 (널 문자) |
| `boolean` | `false` |
| 참조 타입 | `null` |

- 이유는 **객체 할당 시 메모리가 0으로 밀리기** 때문이다 — 지역 변수 슬롯은 그렇지 않다.
- 필드 초기화가 언제 어떤 순서로 도는지는 [`../06-initialization-order/`](../06-initialization-order/) 가 정본이다.

**`final int y;` 를 두 갈래에서 각각 한 번씩 대입하는 것**

- **허용된다.** blank final 이라 부른다.

```java
final int y;
if (args.length == 0) { y = 10; } else { y = 20; }
```

**출력** (`Ex.java (03-b)`)

```text
blank final        y       = 10
```

```text
        final int y;            y: 미대입
            |
      +-----+-----+
   y = 10      y = 20          경로마다 정확히 한 번
      +-----+-----+
            |
        println(y)              확정 대입됨 -> 읽어도 된다
```

**한쪽 갈래에서만 대입하면**

- `else` 경로에서는 대입되지 않으므로 **읽는 순간 `variable y might not have been initialized`** 가 난다.
- `final` 이 아니어도 같은 에러다 — 확정 대입은 `final` 과 별개의 규칙이다.\
  `final` 이 얹는 것은 **"두 번은 안 된다"** 쪽이다.

### 10. 자바에서 참조 전달이 없다는 것을 어떻게 한 문장으로 말하나

**"자바는 객체를 참조로 넘긴다"는 어디까지 맞고 어디서부터 틀리는가**

```text
이 문장으로 설명되는 것                      이 문장으로 설명 안 되는 것
+---------------------------------+        +---------------------------------+
| void f(Point p) { p.x = 99; }   |        | void f(Point p) { p = new ...; }|
|   -> 호출자에게 보인다            |        |   -> 호출자에게 안 보인다        |
|                                 |        | swap(a, b) 가 안 먹힌다          |
| 절반은 맞다                      |        | 참조 전달이면 둘 다 되어야 한다   |
+---------------------------------+        +---------------------------------+
```

- **절반만 맞아서 더 위험하다.** 매일 쓰는 코드의 대부분이 왼쪽 칸이라 틀린 줄 모르고 지나간다.
- 틀리는 순간은 **재대입이 끼는 자리**뿐이고, 그때는 에러 없이 조용히 아무 일도 안 일어난다.

**정확한 한 문장**

> **자바는 언제나 값을 전달한다. 참조 타입의 값은 객체가 아니라 참조다.**

**그 문장으로 1번이 전부 설명되는가**

| 호출 | 전달된 값 | 메서드가 한 일 | 밖에서 보이나 |
|---|---|---|---|
| `changePrimitive(n)` | `int` 1 | 복사본에 99 대입 | 안 보인다 |
| `mutateField(p1)` | 참조 #7 | 참조를 따라가 창고 수정 | **보인다** |
| `reassign(p2)` | 참조 #7 | 복사본에 다른 참조 대입 | 안 보인다 |

- 세 줄 모두 **"복사본에 대입한 것은 안 보이고, 공유된 창고를 고친 것은 보인다"** 로 설명된다.
- 예외가 없다 — 그래서 이 문장을 쓴다.

### 11. 다른 주제와 잇기

**`Integer` 는 참조 타입인데 왜 "내용을 고치는" 일이 불가능한가**

- `Integer` 가 **불변**이기 때문이다. 값을 담은 필드가 `private final int value` 하나이고, 이를 바꾸는 메서드가 없다.
- 즉 창고는 있는데 **문이 없다.** `mutateField` 에 해당하는 수단이 존재하지 않는다.
- 그래서 래퍼는 참조 타입인데도 **값처럼만 쓸 수 있다.**\
  이 성질과 `Integer` 캐시의 관계는 [`../01-primitives-and-wrappers/`](../01-primitives-and-wrappers/) 가 정본이다.

**다중 `catch` 변수와 자원 변수는 이 주제와 어떻게 이어지나**

- 둘 다 **암묵적으로 `final`** 이다. 재대입하면 컴파일 에러다.
- 다중 `catch` 의 변수에 대입하면 이렇게 나온다(`Ex.java (25-a4)`).

```text
Ex.java:7: error: multi-catch parameter e may not be assigned
            e = new RuntimeException("재대입");
            ^
1 error
```

- 자원 변수도 마찬가지다(`Ex.java (26-d1)`).

```text
Ex.java:5: error: auto-closeable resource r may not be assigned
            r = new R();
            ^
1 error
```

- 그리고 Java 9 부터는 **effectively final 인 바깥 변수를 자원 자리에 직접 쓸 수 있다** — 이 주제의 개념이 문법으로 들어온 자리다.\
  자세한 것은 [`../25-exceptions/`](../25-exceptions/)·[`../26-try-with-resources/`](../26-try-with-resources/).

**팀 상수로 `List` 를 공개할 때**

- `final` 만으로는 **아무것도 못 막는다.** `add`/`remove`/`set` 이 전부 열려 있다.
- 대안 세 가지.
  1. `List.of(...)` — 진짜 불변 리스트. 수정 시도는 `UnsupportedOperationException`.
  2. `Collections.unmodifiableList(inner)` — **뷰**다. 원본 `inner` 를 고치면 뷰에도 보인다.
  3. 접근자에서 방어적 복사본을 돌려준다.
- 1과 2의 차이("불변" 대 "수정 불가 뷰")는 [**40번 주제**](../40-list-set-and-immutable-factories/), 방어적 복사는 [**59번 주제**](../59-immutable-objects/)가 정본이다.

---

## 이 주제를 확인한 실행 목록

| 프로그램 | 무엇을 확인했나 | 돌린 JDK |
|---|---|---|
| `Ex.java (03-a)` | 값 전달 — `int`·필드 변경·재대입·`both`·`swap`·배열·`String`·`StringBuilder` | 17 · 21 · 25 (동일) |
| `Ex.java (03-b)` | `final` 배열/`List`/`StringBuilder` 내용 변경, blank final, 람다 캡처, for-each 캡처 | 17 · 21 · 25 (동일) |
| `Ex.java (03-c1)` `javac` | `final` 지역 변수 재대입 -> `cannot assign a value to final variable x` | 21 |
| `Ex.java (03-c2)` `javac` | 캡처 후 재대입 -> `must be final or effectively final` | 17 · 21 · 25 (문구 동일) |
| `Ex.java (03-c3)` `javac` | 기본 `for` 의 인덱스 캡처 -> 같은 에러 | 17 · 21 · 25 (문구 동일) |
| `Ex.java (03-c4)` `javac` | `final` 필드를 다른 메서드에서 대입 -> 에러 | 21 |
| `Ex.java (03-c5)` `javac` | 미초기화 지역 변수 읽기 -> `might not have been initialized` | 21 |
| `Ex.java (03-d)` `javap -c -p` | 익명 클래스의 `final int val$n`, 람다의 `invokedynamic (I)` 인자 | 21 |
| `Ex.java (03-e)` `javap -c -p` | 상수 변수 접기(`iconst_2`), `final` 필드의 클래스 파일 표시 | 21 |
| `Ex.java (25-a4)` `javac` | 다중 `catch` 변수 재대입 -> `multi-catch parameter e may not be assigned` | 21 |
| `Ex.java (26-d1)` `javac` | 자원 변수 재대입 -> `auto-closeable resource r may not be assigned` | 21 |

**구현 의존 항목** — `val$n` 이라는 캡처 필드 이름, 람다가 `invokedynamic` 으로 컴파일되는 것, 상수 접기(`iconst_2`)는 **javac 의 구현 세부**다.\
버전이 올라 이 표의 `javap` 항목이 달라질 수 있다 — 그때 다시 찍어 본다. 반면 값 전달 규칙·`final`·effectively final 제약은 JLS 가 보장한다.
