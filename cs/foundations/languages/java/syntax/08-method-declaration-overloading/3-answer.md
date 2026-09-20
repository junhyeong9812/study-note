# java/syntax/08 — 메서드 선언: 오버로딩 해소·가변 인자 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·경고·에러 메시지는 **Temurin JDK 21.0.5 에서 실제로 돌려 얻은 것**이다.\
> 정상 실행되는 프로그램은 **17.0.13 · 21.0.5 · 25.0.1** 셋에서 다 돌려 출력이 같음을 확인했다.\
> 바이트코드는 `javap -c` 출력을 그대로 옮겼다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 후보가 넷일 때 무엇이 뽑히나

**출력** (`Ex.java`, JDK 21.0.5 — 17·25 동일)

```text
f(1)          -> f(long)
```

**왜 그런가**

```text
javap -c Ex 의 main — 출력 그대로

       0: iconst_1
       1: istore_1
       2: getstatic     #7                  // Field java/lang/System.out:Ljava/io/PrintStream;
       5: ldc           #27                 // String f(1)          ->
       7: invokevirtual #29                 // Method java/io/PrintStream.print:(Ljava/lang/String;)V
      10: iload_1
      11: i2l                                                       <- 넓히기 명령 하나
      12: invokestatic  #32                 // Method f:(J)V
      15: return
```

- 1단계(박싱·가변 인자 **없이** 되는 것)에 `f(long)` 만 통과한다.\
  `int` → `long` 은 **넓히기 변환**이라 1단계에서 허용된다.
- `f(Integer)` 는 박싱이 필요해 **2단계**, `f(Object)` 도 박싱이 필요해 2단계, `f(int...)` 는 **3단계**다.
- **1단계에 통과자가 있으면 2·3단계는 열리지 않는다.** "더 가까워 보이는" 것은 기준이 아니다.
- 호출 직전에 붙은 명령은 **`i2l`** 하나다 — 객체를 만들지 않는다.

### 2. 3단계를 하나씩 벗겨 보라

**출력** (`Ex.java`, JDK 21.0.5 — 17·25 동일)

```text
p1(long)      <- 1단계: 넓히기
p2(Integer)   <- 2단계: 박싱
p3(int...)    <- 3단계: 가변 인자
q(Object)     <- 박싱 후 참조 넓히기
```

**왜 그런가**

```text
javap -c Ex 의 main — 출력 그대로. 네 단계의 흔적이 전부 여기 있다

       0: iconst_1
       1: istore_1
       2: iload_1
       3: i2l                                                      <- 1단계
       4: invokestatic  #33                 // Method p1:(J)V
       7: iload_1
       8: invokestatic  #39                 // Method java/lang/Integer.valueOf:(I)Ljava/lang/Integer;   <- 2단계
      11: invokestatic  #45                 // Method p2:(Ljava/lang/Integer;)V
      14: iconst_1
      15: newarray       int                                       <- 3단계
      17: dup
      18: iconst_0
      19: iload_1
      20: iastore
      21: invokestatic  #49                 // Method p3:([I)V
      24: iload_1
      25: invokestatic  #39                 // Method java/lang/Integer.valueOf:(I)Ljava/lang/Integer;
      28: invokestatic  #53                 // Method q:(Ljava/lang/Object;)V
      31: return
```

| 단계 | 바이트코드의 흔적 | 비용 |
|---|---|---|
| 1 — 넓히기 | `i2l` 같은 변환 명령 하나 | 없음 |
| 2 — 박싱 | `Integer.valueOf(I)` 호출 | 객체 하나(캐시 범위면 재사용) |
| 3 — 가변 인자 | `newarray` / `dup` / `iastore` | **배열 하나** |

- `q(Object)` 는 **2단계**다. 그 안에서 변환이 두 번 일어난다 — **박싱**(`int`→`Integer`) 다음 **참조 넓히기**(`Integer`→`Object`).
- JLS 가 2단계를 "method invocation conversion" 으로 정의하는데, 거기에 박싱 + 참조 넓히기 조합이 들어 있다.
- 반대는 안 된다 — `int` 를 `Long` 으로는 못 간다(박싱 후 **기본형** 넓히기는 없다).

### 3. 가변 인자와 배열의 관계

**출력** (`Ex.java`, JDK 21.0.5 — 17·25 동일)

```text
v(null)        -> v(String...) len=null 배열
v()            -> v(String...) len=0
v("a","b")     -> v(String...) len=2
v(new String[]{"a"}) -> v(String...) len=1
```

**경고는 `v(null)` 에서 난다.**

```text
Ex.java:13: warning: non-varargs call of varargs method with inexact argument type for last parameter;
        System.out.print("v(null)        -> "); v(null);
                                                  ^
  cast to String for a varargs call
  cast to String[] for a non-varargs call and to suppress this warning
1 warning
```

**왜 그런가**

```text
javap -c Ex — 네 호출의 대상이 전부 같다

  v(null)              32: aconst_null
                       33: invokestatic  #61   // Method v:([Ljava/lang/String;)V

  v()                  44: iconst_0
                       45: anewarray     #36   // class java/lang/String
                       48: invokestatic  #61   // Method v:([Ljava/lang/String;)V

  v("a","b")           59: iconst_2
                       60: anewarray     #36   // class java/lang/String
                       63: dup / iconst_0 / ldc "a" / aastore
                       68: dup / iconst_1 / ldc "b" / aastore
                       73: invokestatic  #61   // Method v:([Ljava/lang/String;)V
```

- **대상 시그니처는 넷 다 같다**: `v:([Ljava/lang/String;)V`. `...` 라는 것은 클래스 파일에 없다 — **그냥 배열**이다.
- 배열을 만드는 것은 **호출하는 쪽**이다. 메서드는 받기만 한다.
- `v()` = **길이 0 배열**(`anewarray` 로 만든다). `v(null)` = **`aconst_null`**, 배열 자체가 없다.
- 그래서 `v()` 는 안전하고 `v(null)` 은 `s.length` 에서 `NullPointerException` 이다.
- 경고가 정확히 그 얘기다 — "가변 인자 호출로 안 봤다. 배열로 넘겼다."

### 4. 런타임 타입은 보지 않는다

**출력** (`Ex.java`, JDK 21.0.5 — 17·25 동일)

```text
t(o) where Object o = "..." -> t(Object)
```

**왜 그런가**

```text
javap -c Ex (해당 줄)

      12: invokestatic  #30                 // Method t:(Ljava/lang/Object;)V
```

- 클래스 파일에 박히는 것은 **`t:(Ljava/lang/Object;)V`** 다.
- `o` 의 **선언 타입**이 `Object` 이므로 컴파일러는 `t(Object)` 를 고른다.\
  그 안에 무엇이 들었는지는 **컴파일 타임에 알 수 없고, 알려고 하지도 않는다.**
- "오버로딩은 다형성이 아니다"라고 말하는 이유:\
  다형성은 **런타임 타입**으로 구현을 고르는 것인데, 오버로딩은 **컴파일 타임 선언 타입**으로 **메서드 자체**를 고른다.\
  이름만 같은 별개의 메서드들이다.
- 09 편의 오버라이딩과 정확히 반대다 — 거기서는 같은 시그니처가 박히고 **대상만 런타임에 갈린다.**

### 5. `null` 을 넘기면

**출력** (`Ex.java`, JDK 21.0.5 — 17·25 동일)

```text
g(null)        -> g(String)
g((Object)null)-> g(Object)
```

`h(null)` 은 컴파일이 멈춘다.

```text
Ex.java:4: error: reference to h is ambiguous
    public static void main(String[] a) { h(null); }
                                          ^
  both method h(String) in Ex and method h(StringBuilder) in Ex match
1 error
```

**왜 그런가**

- `null` 은 **모든 참조 타입에 대입 가능**하므로 후보가 전부 적용 가능해진다.
- 그러면 「더 구체적인 것」 규칙이 작동한다 — `String` 은 `Object` 의 하위 타입이므로 **`String` 이 이긴다.**
- `String` 과 `StringBuilder` 는 **서로 상속 관계가 아니다.** 어느 쪽도 상대에 대입 못 하므로 우열이 없다 → 모호.

한 문장 규칙: **후보들이 하나의 상속 사슬 위에 있으면 가장 아래가 이기고, 형제면 멈춘다.**

- 고치는 법은 **호출부 캐스트**다: `h((String) null)`.
- `g((Object) null)` 이 `g(Object)` 로 간 것이 같은 원리다 — 캐스트가 선언 타입을 바꾼다.

### 6. `List<Integer>.remove`

**출력** (`Ex.java`, JDK 21.0.5 — 17·25 동일)

```text
list.remove(1)            -> [10, 30]
list2.remove(Integer(10)) -> [20, 30]
```

**왜 그런가**

```text
javap -c Ex (해당 줄들)

      43: invokeinterface #53,  2           // InterfaceMethod java/util/List.remove:(I)Ljava/lang/Object;
      96: invokeinterface #66,  2           // InterfaceMethod java/util/List.remove:(Ljava/lang/Object;)Z
```

- `remove(1)` 은 `remove(int index)` 로 간다 — **1단계**(변환 없음)에서 통과하기 때문이다.\
  `remove(Object)` 는 박싱이 필요해 2단계이고, 1단계에 통과자가 있으면 열리지 않는다.
- 그래서 **`10` 이 아니라 인덱스 1의 `20` 이 지워져** `[10, 30]` 이 된다.
- `list2` 는 이미 `Integer` 라 1단계에 `remove(int)` 가 못 들어오고 `remove(Object)` 가 뽑힌다 → `[20, 30]`.
- 반환형도 다르다 — `remove(int)` 는 **지워진 원소**(`Object`), `remove(Object)` 는 **`boolean`**.\
  `boolean ok = list.remove(1);` 이라고 쓰면 그제서야 컴파일 에러로 티가 난다.
- 방어: **`remove(Integer.valueOf(x))`** 또는 `remove((Integer) x)` 로 못박는다.

### 7. 모호해지는 조건

**출력** (`javac Ex.java`, JDK 21.0.5)

```text
Ex.java:4: error: reference to f is ambiguous
    public static void main(String[] a) { f(1, 2); }
                                          ^
  both method f(int,long) in Ex and method f(long,int) in Ex match
1 error
```

**왜 그런가**

```text
f(int, long)  vs  f(long, int)     인자는 (int, int)

  1번 자리 : int -> int   (그대로)   |  int -> long  (넓히기)   -> 왼쪽이 낫다
  2번 자리 : int -> long  (넓히기)   |  int -> int   (그대로)   -> 오른쪽이 낫다

  둘 다 "모든 자리에서 낫다"가 성립하지 않는다 -> 승자 없음
```

- 「더 구체적」은 **모든 파라미터에 대해** 성립해야 한다. 한 자리씩 나눠 가지면 판정이 안 선다.
- 컴파일러는 임의로 고르지 않고 **멈춘다.** 이것이 옳은 설계다 — 조용히 하나를 고르면 아무도 모른다.
- 고치는 법: **호출부에서 못박는다.** `f(1, 2L)` 또는 `f(1L, 2)`.

### 8. 오버로딩이 아예 안 되는 조합

**`void f(int[] x)` 와 `void f(int... x)`**

```text
Ex.java:3: error: cannot declare both f(int...) and f(int[]) in Ex
    static void f(int... x) { }
                ^
1 error
```

- `...` 는 **문법 설탕**이라 클래스 파일에는 `[I` 하나로 남는다. 시그니처가 같다.

**`int f(int x)` 와 `String f(int x)`**

```text
Ex.java:3: error: method f(int) is already defined in class Ex
    static String f(int x) { return ""; }
                  ^
1 error
```

- **시그니처에 반환형이 포함되지 않는다.** 이름 + 파라미터 타입만이다.

**파라미터 이름만 다르거나 `throws` 절만 다르면** — 둘 다 같은 시그니처다.

```text
Ex.java:4: error: method f(int) is already defined in class Ex
    static void f(int size)  { }                       // 이름만 다르다
                ^
Ex.java:6: error: method g(int) is already defined in class Ex
    static void g(int x) { }                           // throws 절만 다르다
                ^
2 errors
```

- 규칙 한 줄: **시그니처 = 이름 + 파라미터 타입 목록.** 나머지는 전부 시그니처 밖이다.

### 9. 가변 인자의 비용

- **배열이 100만 개 생긴다.** 호출마다 하나씩이다.
- 근거는 3번의 바이트코드다 — 호출 직전에 `anewarray`(참조 타입) 또는 `newarray`(기본형)가 **호출부에** 있다.\
  메서드 안이 아니라 **부르는 쪽**에 있으므로, 부를 때마다 실행된다.
- `v()` 도 비용이 든다 — **길이 0 배열**을 만든다(`iconst_0; anewarray`).\
  다만 JIT 의 탈출 분석이 스택에 올리거나 없앨 수 있다. 그것은 [`../../언어-특성/README.md`](../../언어-특성/README.md) 의 영역이고 **여기서는 측정하지 않았다.**
- 실무 방어: 뜨거운 경로에서는 인자 개수별 고정 오버로드를 함께 둔다.\
  JDK 자신이 그렇게 한다 — `List.of()` 는 인자 0~10 개짜리 고정 오버로드와 `List.of(E...)` 를 함께 갖는다.

### 10. API 를 바꿀 때

**실제로 돌려 본 것** (`Lib.java` + `Ex.java`, JDK 21.0.5)

```text
1) 후보 하나일 때:
save(String)
2) Lib 만 다시 컴파일 (Ex.class 는 옛것):
save(String)
3) Ex 를 다시 컴파일하면:
Ex.java:1: error: reference to save is ambiguous
public class Ex { public static void main(String[] a) { Lib.save(null); } }
                                                           ^
  both method save(String) in Lib and method save(StringBuilder) in Lib match
1 error
```

**왜 그런가**

- **이미 컴파일된 코드는 안전하다.** `Ex.class` 에는 `save:(Ljava/lang/String;)V` 가 **박혀 있고**,\
  JVM 은 그 시그니처로 찾아갈 뿐 후보를 다시 고르지 않는다. 이것이 **이진 호환성**이다.
- **재컴파일하면 깨진다.** `javac` 는 후보 집합을 새로 만들고, `null` 인자에서 우열이 없어 멈춘다.\
  이것이 **소스 호환성이 깨진 것**이다.
- 그래서 오버로딩 대신 고려할 것:\
  **이름을 다르게** 짓거나(`saveText` / `saveBuffer`), 파라미터 타입을 하나로 좁히거나, 빌더를 쓴다.

> **이진 호환성(binary compatibility)** — 라이브러리를 바꿔도 **이미 컴파일된** 호출부가 그대로 도는 것.\
> 예: 메서드를 하나 추가하는 것은 이진 호환이다 — 기존 클래스 파일의 시그니처가 여전히 유효하다.

> **소스 호환성(source compatibility)** — 라이브러리를 바꿔도 **다시 컴파일**이 되는 것.\
> 예: 오버로딩 추가는 이진 호환이지만 소스 호환이 아닐 수 있다 — 위 3번이 그 경우다.

### 11. 정본 경계

**박싱과 `Integer` 캐시**

- [`../01-primitives-and-wrappers/`](../01-primitives-and-wrappers/) 가 정본이다.\
  여기서는 박싱을 **"2단계에서 허용되는 변환"** 으로만 쓴다. 캐시 범위는 다루지 않는다.

**오버로딩과 오버라이딩의 대비**

- [**09번 주제**](../09-inheritance-overriding/)에서 완성된다.

| | 오버로딩 | 오버라이딩 |
|---|---|---|
| 언제 정해지나 | **컴파일 타임** | **런타임** |
| 무엇을 보나 | 인자의 **선언 타입** | 수신 객체의 **런타임 타입** |
| 시그니처 | 서로 **다르다** | 서로 **같다** |
| 클래스 파일에 남는 것 | 고른 **결과** | 선언 타입의 시그니처 + 런타임 디스패치 |

**`oop-basics` 의 "다형성"에 오버로딩이 포함되는가**

- [`../../../../oop-basics/`](../../../../oop-basics/) 는 **파이썬 예제로 다형성 개념**을 다루고,\
  그 문서의 다형성은 **메서드 오버라이딩**(§16)이다. 파이썬에는 오버로딩이 아예 없다.
- 그래서 **포함되지 않는다.** 오버로딩은 **Java 의 정적 타입 시스템이 만든 별개 기능**이고,\
  그 대비가 이 주제(08)와 09 가 존재하는 이유다.

---

## 실행 검증

| 프로그램 | 무엇을 확인했나 | 돌린 JDK |
|---|---|---|
| `08/a/Ex` + `javap -c` | 후보 넷 중 `f(long)` · `i2l` + `f:(J)V` | 17 · 21 · 25 (출력 동일) |
| `08/b/Ex` + `javap -c` | 3단계가 각각 남기는 명령 · 박싱 후 참조 넓히기 | 17 · 21 · 25 (출력 동일) |
| `08/c/Ex` + `javap -c` | `null` 해소 · 가변 인자 네 형태 · 경고 문구 | 17 · 21 · 25 (출력 동일) |
| `08/d/Ex` + `javap -c` | 선언 타입만 봄 · `List.remove(I)` 대 `remove(Object)` | 17 · 21 · 25 (출력 동일) |
| `08/e1/Ex` | `h(null)` — `reference to h is ambiguous` | 21 |
| `08/e2/Ex` | `f(int[])` 와 `f(int...)` 동시 선언 불가 | 21 |
| `08/e3/Ex` | 반환형만 다른 오버로딩 — `already defined` | 21 |
| `08/e4/Ex` | `f(int...)` 와 `f(long...)` 에 `f(1,2)` → `f(int...)` | 21 |
| `08/e5/Ex` | `f(int,long)`/`f(long,int)` 에 `f(1,2)` → 모호 | 21 |
| `08/e6/Ex` | `f(Object...)`/`f(String...)` — `f("a")`→String, `f(1)`→Object | 21 |
| `08/e7/Lib`+`Ex` | 이진 호환 / 소스 비호환 — 재컴파일에서만 깨짐 | 21 |
| `08/e8/Ex` | 파라미터 이름만·`throws` 만 다른 오버로딩 — `already defined` | 21 |

**안 돌려 본 것**

- 가변 인자 호출의 **실제 할당 비용 측정** — **안 돌려 봄**. 바이트코드에 `anewarray` 가 있다는 것만 확인했다.

**구현 의존 항목** — `javap` 의 오프셋·상수 풀 번호(`#n`)와 경고 문구는 컴파일러 버전에 따라 달라질 수 있다.\
**대상 시그니처**(`f:(J)V` 등)는 언어 규칙이 정하는 것이라 바뀌지 않는다.
