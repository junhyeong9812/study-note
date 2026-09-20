# java/syntax/08 — 메서드 선언: 오버로딩 해소·가변 인자 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [JLS SE 21 §15.12.2 Compile-Time Step 2: Determine Method Signature](https://docs.oracle.com/javase/specs/jls/se21/html/jls-15.html) · [§8.4.1 Formal Parameters](https://docs.oracle.com/javase/specs/jls/se21/html/jls-8.html) · [§8.4.9 Overloading](https://docs.oracle.com/javase/specs/jls/se21/html/jls-8.html)
> **실행 검증** — 이 문서의 모든 출력·경고·에러 메시지는 Temurin **JDK 21.0.5** 에서 실제로 돌려 얻은 것이다.\
> 정상 실행되는 프로그램은 **17.0.13 · 21.0.5 · 25.0.1** 셋에서 다 돌려 **출력이 한 글자도 다르지 않음**을 확인했다.\
> 바이트코드는 `javap -c` 출력을 그대로 옮겼다.
> **버전** — 3단계 해소 규칙은 **Java 5**(오토박싱·가변 인자 도입)부터 지금까지 같다.
> **범위** — 기본형과 래퍼의 관계(`==`·`Integer` 캐시)는 [`../01-primitives-and-wrappers/`](../01-primitives-and-wrappers/) 가 정본이다.\
> 여기는 **그 변환이 오버로딩 후보를 고르는 데 어떻게 쓰이나**만 다룬다.
> 이 본문은 Claude 작성이다(원고 없음).

## 한눈에 — 쉽게 말하면

**오버로딩 해소는 서류 전형 3라운드다 — 그리고 전부 컴파일 타임에 끝난다.**

비유 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 지원자들 | 이름이 같은 메서드들(후보 집합) |
| 채용 공고의 자격 요건 | 파라미터 타입 |
| 1라운드 — 서류 그대로 통과하는 사람 | 박싱·가변 인자 **없이** 맞는 후보 |
| 2라운드 — 자격증 환산을 인정 | **박싱/언박싱**까지 허용 |
| 3라운드 — 정원 미달이라 기준을 더 낮춤 | **가변 인자**까지 허용 |
| 같은 라운드에 동점자 둘 | 컴파일 에러(`ambiguous`) |
| 면접(실제 사람을 보는 것) | 런타임 — 여기서는 **아무 일도 안 일어난다** |

- 라운드는 **앞에서 끝나면 뒤로 안 간다.**\
  1라운드에 통과자가 하나라도 있으면 2·3라운드는 열리지 않는다.
- 그래서 `f(long)` 과 `f(Integer)` 가 같이 있을 때 `f(1)` 은 **`f(long)`** 이 된다.\
  `Integer` 가 더 "딱 맞아 보여도" 그것은 2라운드 자격이기 때문이다.
- 같은 라운드에 동점자가 둘이면 **뽑지 않고 컴파일을 멈춘다.**
- ★ **심사는 서류로만 한다.** 변수의 **선언 타입**만 보고, 런타임에 그 안에 뭐가 들었는지는 보지 않는다.

```text
f(1) 을 썼을 때 컴파일러가 도는 3라운드

  후보: f(long) · f(Integer) · f(Object) · f(int...)

  1라운드  박싱 없이 되는가?   int -> long  (넓히기)        -> f(long)  통과
     |                        int -> Integer  X (박싱 필요)
     |                        int -> Object   X (박싱 필요)
     |                        f(int...)       X (가변 인자)
     v
   통과자 있음 -> 여기서 끝. 2·3라운드는 열리지 않는다
```

**똑같은 구조로** Java 가 이렇게 동작한다: 서류 전형 = `javac` 의 §15.12.2, 결과 = 클래스 파일에 박힌 **시그니처 한 줄**.

실무에서 이게 물리는 자리는 **`List<Integer>.remove(1)`** 이다.\
"10 을 지워 줘"라고 쓴 `remove(1)` 이 `remove(int index)` 로 뽑혀 **1번 자리**를 지운다.

> **오버로딩(overloading)** — 이름이 같고 **파라미터가 다른** 메서드를 여럿 두는 것.\
> 예: `println(int)` 와 `println(String)` 은 이름만 같고 서로 다른 메서드다.

> **해소(resolution)** — 후보 중 어느 것을 부를지 **컴파일러가** 정하는 것.\
> 예: `f(1)` 이라고 썼을 때 클래스 파일에는 `f:(J)V` 처럼 **고른 결과**가 박힌다.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. 후보가 여럿일 때 **어느 것이 뽑히는가** — 넓히기·박싱·가변 인자가 섞이면 순서가 무엇인가.
2. 가변 인자는 **무엇으로 컴파일되는가** — 배열과 어떤 관계인가.
3. `null` 을 넘기면 무엇이 뽑히고, **언제 컴파일이 멈추는가.**

## 동작 방식

### (1) 3단계 — 바이트코드에 세 라운드가 다 보인다

**언제 쓰나** — 이름이 같은 메서드가 여럿 있는 API 를 부를 때.

```java
// 1단계: 박싱·가변 인자 없이 되는 것
static void p1(long x)    { System.out.println("p1(long)      <- 1단계: 넓히기"); }
static void p1(Integer x) { System.out.println("p1(Integer)"); }
static void p1(int... x)  { System.out.println("p1(int...)"); }

// 2단계: 1단계 후보가 없을 때 — 박싱 허용
static void p2(Integer x) { System.out.println("p2(Integer)   <- 2단계: 박싱"); }
static void p2(int... x)  { System.out.println("p2(int...)"); }

// 3단계: 그것도 없을 때 — 가변 인자
static void p3(int... x)  { System.out.println("p3(int...)    <- 3단계: 가변 인자"); }

static void q(Object x)   { System.out.println("q(Object)     <- 박싱 후 참조 넓히기"); }

// main: int i = 1;  p1(i); p2(i); p3(i); q(i);
```

**실행 결과** (`Ex.java`, JDK 21.0.5 — 17·25 동일)

```text
p1(long)      <- 1단계: 넓히기
p2(Integer)   <- 2단계: 박싱
p3(int...)    <- 3단계: 가변 인자
q(Object)     <- 박싱 후 참조 넓히기
```

```text
javap -c Ex 의 main — 출력 그대로 (네 호출이 나란히 있다)

       0: iconst_1
       1: istore_1
       2: iload_1
       3: i2l                                                      <- 1단계: 넓히기 명령
       4: invokestatic  #33                 // Method p1:(J)V
       7: iload_1
       8: invokestatic  #39                 // Method java/lang/Integer.valueOf:(I)Ljava/lang/Integer;   <- 2단계: 박싱
      11: invokestatic  #45                 // Method p2:(Ljava/lang/Integer;)V
      14: iconst_1
      15: newarray       int                                       <- 3단계: 배열을 만든다
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

그림 해설 (한 단계씩):

- **1단계** — `i2l` 하나만 붙고 `p1:(J)V` 를 부른다. 객체가 안 생긴다.
- **2단계** — `Integer.valueOf(i)` 가 **호출부에** 끼어든다. 이것이 오토박싱의 정체다.
- **3단계** — `newarray int` / `dup` / `iastore` — **호출하는 쪽이 배열을 만든다.**\
  가변 인자 메서드는 배열을 받을 뿐이다.
- `q(Object)` 는 `Integer.valueOf` 후 그냥 넘긴다 — **박싱 다음 참조 넓히기**는 2단계 안에서 허용된다.
- 네 호출의 **대상 시그니처가 전부 클래스 파일에 박혀 있다.** 런타임에 고를 여지가 없다.

비용 — 1단계는 공짜, 2단계는 객체 하나(캐시 범위면 재사용), 3단계는 **호출마다 배열 하나**.

> **넓히기 변환(widening primitive conversion)** — 작은 기본형을 큰 기본형으로 손실 없이 올리는 것.\
> 예: `int` → `long`, `float` → `double`. 바이트코드에 `i2l` 같은 명령 하나로 나타난다.

> **오토박싱(autoboxing)** — 기본형을 대응 래퍼 객체로 자동 변환하는 것.\
> 예: `int` → `Integer` 는 `Integer.valueOf(int)` 호출로 컴파일된다.

### (2) 가변 인자는 배열이다 — 호출하는 쪽에서 만들어진다

**언제 쓰나** — `f(a, b, c)` 와 `f(arr)` 이 둘 다 되는 이유를 설명할 때.

```java
static void v(String... s) {
    System.out.println("v(String...) len=" + (s == null ? "null 배열" : s.length));
}
// main: v(null);  v();  v("a","b");  v(new String[]{"a"});
```

**실행 결과** (`Ex.java`, JDK 21.0.5 — 17·25 동일)

```text
v(null)        -> v(String...) len=null 배열
v()            -> v(String...) len=0
v("a","b")     -> v(String...) len=2
v(new String[]{"a"}) -> v(String...) len=1
```

`v(null)` 에는 컴파일 경고가 따라온다.

```text
Ex.java:13: warning: non-varargs call of varargs method with inexact argument type for last parameter;
        System.out.print("v(null)        -> "); v(null);
                                                  ^
  cast to String for a varargs call
  cast to String[] for a non-varargs call and to suppress this warning
1 warning
```

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

그림 해설 (한 단계씩):

- 네 호출 모두 **같은 대상** `v:([Ljava/lang/String;)V` 다. 시그니처에 `...` 같은 것은 없다 — **그냥 배열**이다.
- `v()` 는 **길이 0 배열**을 만들어 넘긴다. `null` 이 아니다.
- `v(null)` 은 `aconst_null` — 배열을 **안 만들고** `null` 을 그대로 넘긴다.\
  그래서 메서드 안에서 `s.length` 를 하면 `NullPointerException` 이 된다.
- 경고 문구가 정확히 그 얘기다: "정확하지 않은 타입이라 가변 인자 호출로 안 봤다."

비용 — 호출마다 배열 하나. 루프 안에서 가변 인자 메서드를 부르면 **쓰레기가 쌓인다.**

### (3) 심사는 **선언 타입**으로만 한다

**언제 쓰나** — "런타임 타입이 `String` 인데 왜 `Object` 버전이 불리지?" 에서 막혔을 때.

```java
static void t(Object o) { System.out.println("t(Object)"); }
static void t(String s) { System.out.println("t(String)"); }
// main:
Object o = "나는 런타임에는 String 이다";
t(o);
```

**실행 결과** (`Ex.java`, JDK 21.0.5 — 17·25 동일)

```text
t(o) where Object o = "..." -> t(Object)
```

```text
잘못된 기대                         실제
+---------------------------+      +---------------------------+
| 런타임 타입이 String 이니   |      | 선언 타입이 Object 다      |
| t(String) 이 불린다        |      | -> t(Object) 로 컴파일됨   |
+---------------------------+      +---------------------------+
                                     클래스 파일:
                                     invokestatic t:(Ljava/lang/Object;)V
```

그림 해설 (한 단계씩):

- 오버로딩은 **컴파일 타임에 끝난다.** 09 편의 오버라이딩(런타임)과 정반대다.
- 클래스 파일에 `t:(Ljava/lang/Object;)V` 가 박히면, 런타임에 그 객체가 무엇이든 그 메서드가 불린다.
- 그래서 **"오버로딩은 다형성이 아니다."** 이름만 같은 별개의 메서드들이다.

비용 — 런타임 비용 0. 대신 **읽는 사람의 비용**이 크다 — 어느 것이 불리는지 소스만 봐서는 헷갈린다.

## 문법 — 형태와 규칙

직접 쓴 최소 예제다.

### 메서드 선언의 구성

```java
public static <T> List<T> pick(List<T> src, int n, String... tags) throws Exception { ... }
//  ^접근   ^정적 ^타입파라미터 ^반환형  ^이름  ^파라미터들          ^가변 인자   ^검사 예외
```

### 오버로딩이 되는 조건과 안 되는 조건

| 다르게 해도 되는 것 | 오버로딩이 되나 |
|---|---|
| 파라미터 **개수** | 된다 |
| 파라미터 **타입** | 된다 |
| 파라미터 **순서**(타입이 다를 때) | 된다 |
| 파라미터 **이름** | **안 된다** — 같은 시그니처다 |
| **반환형** | **안 된다** |
| `throws` 절 | **안 된다** |
| `T[]` 와 `T...` | **안 된다** — 소거하면 같은 배열이다 |

### 가변 인자의 규칙 — 네 줄

- **마지막 파라미터**에만 쓸 수 있고, **하나만** 쓸 수 있다.
- 메서드 안에서는 **그냥 배열**이다(`length`·인덱스).
- 호출부에서 **배열을 직접 넘겨도 된다.**
- 같은 이름의 고정 인자 메서드가 있으면 **고정 쪽이 먼저 뽑힌다**(1·2단계가 먼저다).

## 어디서 틀리나

### 1. `List<Integer>.remove(1)` — 값이 아니라 자리를 지운다

```java
List<Integer> list = new ArrayList<>(List.of(10, 20, 30));
list.remove(1);                       // remove(int index)

List<Integer> list2 = new ArrayList<>(List.of(10, 20, 30));
list2.remove(Integer.valueOf(10));    // remove(Object o)
```

**실행 결과** (`Ex.java`, JDK 21.0.5 — 17·25 동일)

```text
list.remove(1)            -> [10, 30]
list2.remove(Integer(10)) -> [20, 30]
```

```text
javap -c Ex — 대상이 다르다

      43: invokeinterface #53,  2           // InterfaceMethod java/util/List.remove:(I)Ljava/lang/Object;
      96: invokeinterface #66,  2           // InterfaceMethod java/util/List.remove:(Ljava/lang/Object;)Z
```

- `remove(int)` 는 **1라운드**(변환 없음)에서 통과한다. `remove(Object)` 는 박싱이 필요해 2라운드다.
- 그래서 `remove(1)` 은 **`10` 이 아니라 `20` 을 지운다**(인덱스 1).
- 반환형도 다르다 — 하나는 지워진 원소, 하나는 `boolean`. 그래서 대입해 보면 티가 나긴 한다.
- 방어: `Integer` 리스트에서 값을 지울 때는 **항상 `remove(Integer.valueOf(x))`** 또는 `remove((Integer) x)`.

### 2. `null` 은 "가장 구체적인 타입"으로 간다 — 아니면 멈춘다

```java
static void g(Object o) { }
static void g(String s) { }
// g(null) -> ?

static void h(String s)        { }
static void h(StringBuilder b) { }
// h(null) -> ?
```

**실행 결과** (`Ex.java`, JDK 21.0.5 — 17·25 동일)

```text
g(null)        -> g(String)
g((Object)null)-> g(Object)
```

```text
$ javac Ex.java        (h(null) 쪽)
Ex.java:4: error: reference to h is ambiguous
    public static void main(String[] a) { h(null); }
                                          ^
  both method h(String) in Ex and method h(StringBuilder) in Ex match
1 error
```

- `g(null)` 은 **`String` 이 `Object` 보다 구체적**이라 `g(String)` 이 뽑힌다.
- `String` 과 `StringBuilder` 는 **서로 상속 관계가 아니라** 우열이 없다 — 컴파일이 멈춘다.
- 해결은 **캐스트**다: `h((String) null)`.
- 함의: 오버로딩 API 에 `null` 을 넘기는 코드는 **후보가 하나 추가되는 순간 깨진다.**

### 3. 양쪽 다 한 칸씩 넓히면 모호하다

```java
static void f(int x, long y) { }
static void f(long x, int y) { }
// f(1, 2) -> ?
```

```text
$ javac Ex.java
Ex.java:4: error: reference to f is ambiguous
    public static void main(String[] a) { f(1, 2); }
                                          ^
  both method f(int,long) in Ex and method f(long,int) in Ex match
1 error
```

- 어느 쪽도 **모든 자리에서** 상대보다 구체적이지 않다.
- "더 구체적"은 **파라미터 전부에 대해** 성립해야 한다. 하나씩 나눠 가지면 승자가 없다.
- `f(1, 2L)` 이나 `f(1L, 2)` 로 **호출부에서 못박아야** 한다.

### 4. `T[]` 와 `T...` 는 같은 메서드다

```java
static void f(int[] x)  { }
static void f(int... x) { }
```

```text
$ javac Ex.java
Ex.java:3: error: cannot declare both f(int...) and f(int[]) in Ex
    static void f(int... x) { }
                ^
1 error
```

- `...` 는 **문법 설탕**이다. 클래스 파일에는 `[I` 하나로 남는다.
- 그래서 "배열 버전도 만들어 두자"가 안 된다.
- 반환형만 다른 오버로딩도 같은 이유로 막힌다.

  ```text
  Ex.java:3: error: method f(int) is already defined in class Ex
      static String f(int x) { return ""; }
                    ^
  1 error
  ```

### 5. 가변 인자에 `null` 을 넘기면 배열 자체가 `null` 이다

- 위 (2) 절의 `v(null)` 이 그것이다 — 경고는 나오지만 **컴파일은 된다.**
- 메서드 안에서 `for (String s : args)` 를 돌면 **`NullPointerException`** 이다.
- 가변 인자를 받는 메서드는 **`args == null` 을 방어하거나** `Objects.requireNonNull` 을 쓴다.
- 반대로 `v()` 는 **길이 0 배열**이라 안전하다 — 이 둘을 헷갈리면 안 된다.

## 구현 세부사항 대 언어 보장

| 항목 | 누가 보장하나 |
|---|---|
| 3단계 해소 순서(무변환 → 박싱 → 가변 인자) | **언어 보장** — JLS §15.12.2 |
| "더 구체적"이 모든 파라미터에 대해 성립해야 한다는 규칙 | **언어 보장** — JLS §15.12.2.5 |
| 오버로딩이 **컴파일 타임에** 확정된다는 것 | **언어 보장** |
| 가변 인자가 배열로 컴파일된다는 것 | **언어 보장** — JLS §8.4.1 |
| `Integer.valueOf` 가 `-128..127` 을 캐시하는 것 | **구현 세부** — [01번 주제](../01-primitives-and-wrappers/)의 영역 |
| `newarray` / `anewarray` 중 어느 명령이 쓰이는지 | **구현 세부** — 원소 타입에 따른 javac 선택 |
| 경고 문구(`non-varargs call of varargs method ...`) | **구현 세부** — javac 의 진단 메시지 |

★ 핵심: **"어느 메서드가 뽑히나"는 언어 보장이고, "그 과정에서 어떤 명령이 나오나"는 구현 세부다.**\
그래도 `javap` 를 보는 이유는, **뽑힌 결과가 시그니처로 박혀 있어** 지어낼 수 없기 때문이다.

## 언제 쓰고 언제 안 쓰나

| 쓸 것 | 안 쓸 것 |
|---|---|
| 타입이 정말 다른 같은 일 -> 오버로딩(`println(int)`·`println(String)`) | 파라미터 **개수만** 다른 오버로딩 — 기본값 흉내는 위임(`this(...)`)이 낫다 |
| 인자 개수가 정말 가변 -> `String...` | 성능이 중요한 루프 안의 가변 인자 — 호출마다 배열이 생긴다 |
| 오버로딩 대신 **이름을 다르게** 짓기 | 한 후보만 `null` 을 받을 수 있는 오버로딩 세트 |
| 모호하면 호출부에서 캐스트로 못박기 | 기본형과 래퍼를 **같은 자리에** 두는 오버로딩(`remove(int)`/`remove(Object)`) |

판단 규칙 세 줄.

- **오버로딩은 읽는 사람이 어느 것인지 즉시 알 수 있을 때만.** 헷갈리면 이름을 나눈다.
- **가변 인자와 다른 오버로딩을 섞지 않는다.** 3단계가 열리는 조건이 미묘해진다.
- **API 에 오버로딩을 추가하는 것은 소스 호환성을 깰 수 있다.** 기존 `null` 호출이 모호해진다.

## 핵심 문장

- 오버로딩 해소는 **3단계**다 — ① 박싱·가변 인자 없이 ② 박싱 허용 ③ 가변 인자 허용. **앞 단계에서 끝나면 뒤는 안 연다.**
- 그래서 `f(long)` 과 `f(Integer)` 중 `f(1)` 은 **`f(long)`** 이다.
- 해소는 **컴파일 타임**에 끝나고, 결과가 시그니처로 클래스 파일에 박힌다 — **선언 타입만** 본다.
- **가변 인자는 배열이다.** 배열은 호출하는 쪽이 만든다. `v()` 는 길이 0 배열, `v(null)` 은 `null` 그 자체다.
- `null` 은 **가장 구체적인 후보**로 가고, 우열이 없으면 `reference to ... is ambiguous` 로 컴파일이 멈춘다.

## 관련 자료

- [`../README.md`](../README.md) — Java 문법·API 주제 목록(이 주제는 08번)
- [`../01-primitives-and-wrappers/`](../01-primitives-and-wrappers/) — **박싱 자체와 `Integer` 캐시는 거기**, 여기는 **박싱이 후보 선택의 2단계라는 사실**만 쓴다
- [`../../../../oop-basics/`](../../../../oop-basics/) — **다형성 개념은 거기**(파이썬 예제).\
  ★ 오버로딩은 그 문서가 말하는 다형성이 **아니다** — 이름만 같은 별개 메서드다. 그 대비가 여기의 값어치다
- [**09번 주제**](../09-inheritance-overriding/)(상속과 오버라이딩) — **오버로딩(컴파일 타임) 대 오버라이딩(런타임)**의 대비가 그쪽에서 완성된다
- [**17번 주제**](../17-generic-declarations/)(제네릭 선언) — 제네릭 메서드가 후보에 끼면 해소가 한 겹 더 복잡해진다
- [**40번 주제**](../40-list-set-and-immutable-factories/)(`List`·`Set` API) — `remove(int)`/`remove(Object)` 함정의 API 쪽 정본

## 용어 풀이

- **오버로딩(overloading)** — 이름이 같고 파라미터가 다른 메서드를 여럿 두는 것. 컴파일 타임에 갈린다.
- **시그니처(signature)** — 메서드 이름 + 파라미터 타입 목록. **반환형은 포함되지 않는다.**
- **해소(resolution)** — 후보 중 어느 것을 부를지 컴파일러가 정하는 과정. JLS §15.12.
- **적용 가능(applicable)** — 주어진 인자로 그 메서드를 부를 수 있다는 뜻. 단계마다 기준이 달라진다.
- **더 구체적(more specific)** — 후보 둘 중 하나의 파라미터 타입이 **전부** 다른 쪽에 대입 가능할 때. 동점이면 모호.
- **넓히기 변환(widening)** — `int`→`long` 처럼 손실 없는 기본형 변환. 1단계에서 허용된다.
- **오토박싱/언박싱** — 기본형↔래퍼 자동 변환. 2단계에서 허용된다.
- **가변 인자(varargs)** — `T... x`. 마지막 파라미터에만, 하나만. 배열로 컴파일된다.
- **`invokestatic` / `invokevirtual` / `invokeinterface`** — 호출 명령들. 어느 것이든 **대상 시그니처는 컴파일 타임에 고정**된다.
- **문법 설탕(syntactic sugar)** — 더 편한 표기일 뿐 컴파일 결과는 원래 것과 같은 문법.

## 더 들어가면

- **제네릭 메서드가 끼면 단계가 더 있다.** JLS §15.12.2 는 "타입 인자 추론이 필요한 경우"를 각 단계 안에서 따로 다룬다.\
  실무 증상은 같다 — 후보가 늘면 모호해질 확률이 올라간다.
- **`@SafeVarargs`** — 제네릭 가변 인자(`T... args`)는 힙 오염 경고를 낸다.\
  배열은 실체화되는데 제네릭은 소거되기 때문이다. [**19번 주제**](../19-type-erasure/)(타입 소거)가 정본이다.
- **오버로딩 추가는 이진 호환성은 지키지만 소스 호환성을 깰 수 있다.**\
  이미 컴파일된 코드는 시그니처가 박혀 있어 안전하지만, 재컴파일하면 `ambiguous` 가 날 수 있다.
- **`printf` 류는 3단계와 `Object...` 를 같이 쓴다.** `printf("%d", 1)` 은 `int` 를 박싱해 `Object[]` 에 담는다 —\
  한 호출에 박싱 하나와 배열 하나가 생긴다.
