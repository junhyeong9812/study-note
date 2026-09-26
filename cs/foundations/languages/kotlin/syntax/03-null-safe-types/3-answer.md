# kotlin/syntax/03 — null 안전 타입: `?`·`?.`·`?:`·`!!` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 모든 출력·예외·에러·바이트코드는 **kotlinc 2.4.20 (JRE 21.0.5)** 과 Temurin **JDK 21.0.5** 의 `javap` 에서 실제로 얻었다.\
> Java 쪽 호출(4번)은 `javac -cp outk` 로 컴파일해 **같은 클래스패스에서 실제로 섞어 돌린 것**이다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★ 이 네 줄은 각각 어떤 에러를 내는가

**출력** (`kotlinc bad.kt`)

```text
bad.kt:3:19: error: initializer type mismatch: expected 'String', actual 'String?'.
    val t: String = s
                  ^
bad.kt:4:14: error: only safe (?.) or non-null asserted (!!.) calls are allowed on a nullable receiver of type 'String?'.
    println(s.length)
             ^
bad.kt:5:21: error: null cannot be a value of a non-null type 'String'.
    val u: String = null
                    ^^^^
```

**왜 그런가**

| | 구문 | 결과 |
|---|---|---|
| `[A]` | `val t: String = s` | 에러 — `initializer type mismatch` |
| `[B]` | `s.length` | 에러 — `only safe (?.) or non-null asserted (!!.) calls…` |
| `[C]` | `val u: String = null` | 에러 — `null cannot be a value of a non-null type 'String'.` |
| `[D]` | `val v: String? = "나"` | **통과** |
| `[E]` | `val w: String? = v` | **통과** |

```text
     String?  ───X───>  String        (대입 불가)
     null     ───X───>  String        (대입 불가)
     String   ───O───>  String?       (반대 방향은 자유)

     String?  에 직접 . 호출 ───X───>  "only safe (?.) or non-null asserted (!!.)"
```

- **세 문구가 다른 이유** — 컴파일러가 **다른 규칙 셋**을 가지고 있어서다.\
  `[A]`는 **타입 대입 규칙**, `[B]`는 **호출 수신자 규칙**, `[C]`는 **리터럴 `null` 전용 규칙**이다.
- `[B]` 의 메시지는 **고치는 법을 안에 담고 있다** — `?.` 또는 `!!.` 를 쓰라고 적혀 있다.\
  이 언어에서 에러 메시지가 교재라고 하는 이유가 여기 있다.
- `String` → `String?` 이 되는 이유는 **non-null 이 nullable 의 부분집합**이기 때문이다.\
  "없을 수 있는 자리" 에 "반드시 있는 값" 을 넣는 것은 안전하다.

### 2. ★★ `?.` 와 `?:` 는 무엇으로 컴파일되는가

**출력** (`javap -c -p outi/Icode2Kt.class`)

```text
  public static final java.lang.Integer safeCall(java.lang.String);
    Code:
       0: aload_0
       1: dup
       2: ifnull        14
       5: invokevirtual #13                 // Method java/lang/String.length:()I
       8: invokestatic  #19                 // Method java/lang/Integer.valueOf:(I)Ljava/lang/Integer;
      11: goto          16
      14: pop
      15: aconst_null
      16: areturn

  public static final int elvis(java.lang.String);
    Code:
       0: aload_0
       1: dup
       2: ifnull        11
       5: invokevirtual #13                 // Method java/lang/String.length:()I
       8: goto          13
      11: pop
      12: iconst_m1
      13: ireturn
```

**왜 그런가**

```text
   aload_0  ──> 스택에 s
   dup      ──> 하나 복사
   ifnull ───────────────┐
      |                  │ (null 이면)
      |                  v
   length()            pop        ← 복사본 버리기
   (…)                 aconst_null / iconst_m1
      |                  |
      └──> return <──────┘
```

- **둘 다 `ifnull` 분기 하나다.** `?.` 는 마법이 아니라 `if (s != null) … else …` 를 컴파일러가 대신 적은 것이다.
- 반환 디스크립터가 다르다 — `safeCall` 은 **`java.lang.Integer`**(nullable 이라 박싱), `elvis` 는 **`int`**.
- ★ **`elvis` 에는 `Integer.valueOf` 가 없다.** 두 연산자를 따로 적었는데 컴파일러가 **한 분기로 합쳐**\
  중간 `Int?` 를 아예 만들지 않았다.
- 그래서 **`s?.length ?: -1` 은 `Int?` 를 거치지 않는다.** 이 관용구가 싼 이유이고,\
  "`?.` 를 쓰면 박싱이 생긴다" 는 말이 **엘비스와 붙었을 때는 틀린** 이유다.

### 3. ★★ `!!` 는 무엇으로 컴파일되고 터지면 어떤 메시지를 내는가

**출력** (`javap -c -p outi/Icode2Kt.class`)

```text
  public static final int bang(java.lang.String);
    Code:
       0: aload_0
       1: dup
       2: invokestatic  #29                 // Method kotlin/jvm/internal/Intrinsics.checkNotNull:(Ljava/lang/Object;)V
       5: invokevirtual #13                 // Method java/lang/String.length:()I
       8: ireturn
```

**출력** (`K.kt` — `bang(null)` 을 잡아서 찍은 것)

```text
!! -> java.lang.NullPointerException
   message = null
   at KKt.bang(K.kt:2)
   at KKt.main(K.kt:4)
   at KKt.main(K.kt)
```

**왜 그런가**

- 호출은 **`Intrinsics.checkNotNull`** 이고 시그니처가 **`(Ljava/lang/Object;)V` — 인자 하나**다.\
  **메시지를 받을 자리가 없다.**
- 그래서 예외는 평범한 `java.lang.NullPointerException` 이고 **`message` 가 `null`** 이다.\
  JVM 의 helpful NPE(`Cannot invoke … because …`)도 아니다 — **Kotlin 이 직접 던진 것**이기 때문이다.
- 스택 맨 위는 `KKt.bang(K.kt:2)` — **`!!` 가 적힌 줄**을 가리킨다.\
  즉 **"어느 줄" 은 알려 주고 "무엇이 왜 없었는지" 는 안 알려 준다.**
- 대신 쓸 것은 셋이다.

| 상황 | 대체 | 남는 정보 |
|---|---|---|
| 없으면 흐름을 끝낸다 | `?: return` / `?: throw IllegalArgumentException("…")` | 직접 쓴 메시지 |
| 없으면 프로그래밍 오류 | `requireNotNull(x) { "왜 필요한지" }` | 람다 메시지(조건이 참이면 안 만든다) |
| 있을 때만 쓴다 | `?.let { }` | — |

- Java 쪽 대응(`Objects.requireNonNull` 이 메시지를 받는 것)의 정본은\
  [`../../../java/syntax/60-null-handling/`](../../../java/syntax/60-null-handling/).

### 4. ★★ 이 함수에서 컴파일러가 심는 검사는 무엇이고 누가 걸리는가

**출력** (`javap -c -p outi/Icode2Kt.class`)

```text
  public static final int nonNullParam(java.lang.String, java.lang.String);
    Code:
       0: aload_0
       1: ldc           #34                 // String s
       3: invokestatic  #38                 // Method kotlin/jvm/internal/Intrinsics.checkNotNullParameter:(Ljava/lang/Object;Ljava/lang/String;)V
       6: aload_0
       7: invokevirtual #13                 // Method java/lang/String.length:()I
      10: aload_1
      11: dup
      12: ifnull        21
      15: invokevirtual #13                 // Method java/lang/String.length:()I
      18: goto          23
      21: pop
      22: iconst_0
      23: iadd
      24: ireturn
```

**출력** (`java -cp "outk:kotlin-stdlib.jar" J` — Java 가 Kotlin 함수에 `null` 을 넘긴 것)

```text
Java 가 null 을 넘김 -> java.lang.NullPointerException
   message = Parameter specified as non-null is null: method KKt.greet, parameter name
   at KKt.greet(K.kt)
   at J.main(J.java:4)
```

**왜 그런가**

- 함수 **첫 세 명령**이 소스에 없는 검사다 — `aload_0`(값) · `ldc "s"`(이름) · `checkNotNullParameter`.
- ★ **`s`(non-null)만 검사받고 `t`(`String?`)는 안 받는다.** nullable 파라미터는 `null` 이 정상이므로 검사할 게 없다.
- Java 가 `null` 을 넘기면 **`Parameter specified as non-null is null: method KKt.greet, parameter name`** 이다.\
  3번의 빈 메시지와 정반대로 **함수 이름과 파라미터 이름이 들어 있다** — `ldc` 로 이름을 상수 풀에 박아 뒀기 때문이다.
- 스택 맨 위가 `KKt.greet` 다. **Kotlin 함수 안으로 한 발짝 들어온 자리에서 즉시 터진다** —\
  `null` 이 도메인 로직 깊은 곳까지 흘러가지 않는다. [`java/syntax/60`](../../../java/syntax/60-null-handling/) 의 "즉시 실패" 와 같은 설계다.
- **결론** — Kotlin 의 null 안전은 타입 시스템만이 아니라 **런타임 코드이기도 하다.**\
  다만 그 코드는 (6)에서 보듯 **끌 수 있다.**

### 5. ★★ 이 다섯 함수 중 `checkNotNullParameter` 가 안 붙는 것은

**출력** (`javap -c -p outv/VisKt.class` · `outv/C.class` — 검사 호출만 추려 찍었다)

```text
=== VisKt ===
  public static final int pub(java.lang.String);
       3: invokestatic  #15                 // Method kotlin/jvm/internal/Intrinsics.checkNotNullParameter:(Ljava/lang/Object;Ljava/lang/String;)V
  public static final int intl(java.lang.String);
       3: invokestatic  #15                 // Method kotlin/jvm/internal/Intrinsics.checkNotNullParameter:(Ljava/lang/Object;Ljava/lang/String;)V
  private static final int priv(java.lang.String);
    Code:
  public static final int localUser(java.lang.String);
       3: invokestatic  #15                 // Method kotlin/jvm/internal/Intrinsics.checkNotNullParameter:(Ljava/lang/Object;Ljava/lang/String;)V
  private static final int localUser$lambda$0(java.lang.String);
       3: invokestatic  #15                 // Method kotlin/jvm/internal/Intrinsics.checkNotNullParameter:(Ljava/lang/Object;Ljava/lang/String;)V
=== C ===
  public C(java.lang.String);
       3: invokestatic  #15                 // Method kotlin/jvm/internal/Intrinsics.checkNotNullParameter:(Ljava/lang/Object;Ljava/lang/String;)V
  public final int m(java.lang.String);
       3: invokestatic  #15                 // Method kotlin/jvm/internal/Intrinsics.checkNotNullParameter:(Ljava/lang/Object;Ljava/lang/String;)V
  private final int p(java.lang.String);
       1: invokevirtual #35                 // Method java/lang/String.length:()I
  public final int use(java.lang.String);
       3: invokestatic  #15                 // Method kotlin/jvm/internal/Intrinsics.checkNotNullParameter:(Ljava/lang/Object;Ljava/lang/String;)V
```

**왜 그런가**

```text
  public  fun pub(s: String)      ──> 검사 O
  internal fun intl(s: String)    ──> 검사 O
  private fun priv(s: String)     ──> 검사 X  ★
  class C { fun m(...) }          ──> 검사 O
  class C { private fun p(...) }  ──> 검사 X  ★
  생성자 C(name: String)           ──> 검사 O
  람다 (Function1 로 불린다)        ──> 검사 O  ★
```

- 규칙 한 문장 — **밖에서 부를 수 있는 표면에만 심는다.** `private` 은 그 표면이 아니다.
- ★ **람다에는 붙는다.** `localUser$lambda$0` 은 `private static` 인데도 검사가 있다.\
  이유는 **타입 소거**다 — 람다는 `Function1.invoke(Object)` 라는 지워진 시그니처로 불리므로\
  **호출자가 `Object` 자리에 `null` 을 넣을 수 있다.** 즉 여기도 "밖에서 부를 수 있는 표면" 이다.\
  소거의 정본은 [`../../../java/syntax/19-type-erasure/`](../../../java/syntax/19-type-erasure/).
- ★ **이 사실이 검사의 목적을 말해 준다** — **Kotlin 코드끼리는 타입 검사로 이미 막았으므로 검사가 필요 없다.**\
  런타임 검사는 **타입 검사를 안 거친 호출자**(Java·리플렉션·지워진 시그니처)를 위한 것이다.

### 6. ★★ 어느 검사는 플래그로 끌 수 있고 어느 것은 못 끄는가

**출력** (`kotlinc -Xno-param-assertions icode2.kt` → `javap`)

```text
  public static final int nonNullParam(java.lang.String, java.lang.String);
    Code:
       0: aload_0
       1: invokevirtual #13                 // Method java/lang/String.length:()I
       4: aload_1
       5: dup
       6: ifnull        15
       9: invokevirtual #13                 // Method java/lang/String.length:()I
      12: goto          17
      15: pop
      16: iconst_0
      17: iadd
      18: ireturn
```

**출력** (`kotlinc -Xno-call-assertions -Xno-param-assertions -Xno-receiver-assertions icode2.kt` → `javap`)

```text
  public static final int bang(java.lang.String);
    Code:
       0: aload_0
       1: dup
       2: invokestatic  #29                 // Method kotlin/jvm/internal/Intrinsics.checkNotNull:(Ljava/lang/Object;)V
       5: invokevirtual #13                 // Method java/lang/String.length:()I
       8: ireturn
```

**왜 그런가**

```text
  끌 수 있는 것                          못 끄는 것
  +--------------------------------+    +--------------------------------+
  | checkNotNullParameter           |    | ?.  (ifnull 분기)              |
  | checkNotNullExpressionValue     |    | ?:  (ifnull 분기)              |
  |   (05번 플랫폼 타입)            |    | !!  (checkNotNull) ★           |
  +--------------------------------+    +--------------------------------+
     = 컴파일러가 얹은 방어 코드            = 언어가 정한 의미
```

- 첫 명령 뒤 `nonNullParam` 에서 **`ldc "s"` 와 `checkNotNullParameter` 두 줄이 사라졌다.**\
  `ifnull` 분기는 그대로 남아 있다.
- 세 플래그를 다 줘도 **`bang` 의 `checkNotNull` 은 남는다.**
- 가르는 기준 — **코드의 뜻이 바뀌면 못 끈다.**\
  `?.` 를 끄면 `null` 에서 호출이 일어나 버려 뜻이 달라진다. `!!` 를 끄면 "터뜨려라" 라는 **요청 자체**가 사라진다.\
  반면 `checkNotNullParameter` 는 **없어도 정상 경로의 결과가 같다** — 그래서 끌 수 있다.
- ★ **그러므로 "Kotlin 은 런타임에도 null 을 막는다" 는 기본 설정에서만 참인 문장이다.**\
  플래그를 켠 모듈에서는 Java 가 넘긴 `null` 이 **깊은 곳에서 나쁜 메시지로** 터진다.

### 7. `?.` 사슬이 중간에 끊기면

**출력** (`ex.kt`)

```text
--- 1. ?. 사슬 ---
full   -> 2
noAddr -> null
noCity -> null
null u -> null
```

**왜 그런가**

```text
   full.addr?.city?.length
        │      │     │
        │      │     └── 여기까지 왔으면 Int
        │      └──────── city 가 null 이면 여기서 끝 -> 전체 null
        └─────────────── addr 가 null 이면 여기서 끝 -> 전체 null

   결과 타입은 언제나 Int?  (어디서 끊겼는지는 알 수 없다)
```

- `addr` 이 `null` 일 때도, `city` 가 `null` 일 때도, 수신자 자체가 `null` 일 때도 **전부 `null`** 이다.
- ★ **결과만 보고는 어디서 끊겼는지 알 수 없다.** 세 원인이 한 값으로 뭉개진다.
- 결과 타입은 **항상 nullable** 이다 — `length` 가 non-null `Int` 를 돌려줘도 사슬 전체는 `Int?` 다.
- 알아야 하면 **사슬을 쪼갠다.**

```kotlin
val addr = user.addr ?: error("주소 없음")
val city = addr.city ?: error("도시 없음")
city.length
```

  또는 중간에 `?: return`/`?: throw` 를 끼운다(8번).

### 8. `?:` 오른쪽에 `return`/`throw` 가 들어가는 이유는

**출력** (`ex.kt` · `ext.kt`)

```text
label(full)=도시=서울  label(noAddr)=주소 없음
```

```text
--- ?: 오른쪽에 throw ---
need(null) -> IllegalArgumentException: s 가 없다
need("가") -> 1
```

**왜 그런가**

```kotlin
fun label(u: User?): String {
    val city = u?.addr?.city ?: return "주소 없음"
    return "도시=$city"
}
```

- `city` 의 타입은 **`String`**(non-null)이다. 왼쪽이 `String?` 인데도 그렇다.
- `return` 과 `throw` 의 타입은 **`Nothing`** 이다 — **값이 하나도 없는 타입**.
- 성립시키는 성질은 **`Nothing` 이 모든 타입의 하위 타입**이라는 것이다.\
  `?:` 의 결과 타입은 양쪽의 **공통 상위 타입**인데, 오른쪽이 `Nothing` 이면 **왼쪽의 non-null 판**이 그대로 답이 된다.

```text
   u?.addr?.city   :  String?
   return "…"      :  Nothing   ← 모든 타입의 하위
   -------------------------------
   공통 상위 타입   :  String    ★ null 이 빠진다
```

- `!!` 보다 나은 점 — **메시지를 남길 수 있다.** `?: throw IllegalArgumentException("s 가 없다")` 는\
  3번의 `message = null` 과 달리 이유가 적힌다. 그리고 `return` 판은 **아예 예외를 안 쓴다.**
- `Nothing` 자체의 정본은 [목록의 **34번 주제**](../34-exceptions-nothing-and-try-expression/)(예외·`Nothing` 타입).

### 9. `s.toString()` 과 `s?.toString()` 은 어떻게 다른가

**출력** (`ext.kt`)

```text
s.isNullOrEmpty() = true
s.toString()      = null
s.orEmpty()       = []
s?.toString()     = null
t.isNullOrEmpty() = false
--- ?. 와 확장 함수의 차이 ---
null 수신자에 확장 함수는 호출된다 — 멤버 함수는 안 된다
n.toString() = null  ("null" 이라는 문자열)
```

**경고**

```text
ext.kt:6:39: warning: redundant call of conversion method.
    println("s?.toString()     = ${s?.toString()}")
                                      ^^^^^^^^^^
```

**왜 그런가**

- ★ **두 값이 화면에는 똑같이 `null` 로 찍히는데 타입과 정체가 다르다.**

| 식 | 값 | 타입 |
|---|---|---|
| `s.toString()` | **`"null"` — 넉 자짜리 문자열** | `String` |
| `s?.toString()` | **진짜 `null`** | `String?` |

- `s.length` 는 4가 된다. **한 글자(`?`) 차이로 값이 다르다.**\
  화면 출력으로는 구분이 안 되므로 **`println` 만으로는 못 잡는다.**
- `s.isNullOrEmpty()` 가 되는 이유 — **확장 함수는 수신자를 첫 인자로 받는 정적 함수**이고,\
  수신자 타입을 `CharSequence?` 로 선언해 두었기 때문이다. `null` 을 인자로 받는 것은 문제가 안 된다.
- **멤버 함수는 그럴 수 없다.** 가상 디스패치를 하려면 **객체가 있어야** 메서드 테이블을 찾는다.\
  `null` 에는 테이블이 없다 — 그래서 언어가 아니라 **JVM 이 막는다.**
- `s?.toString()` 에는 **`redundant call of conversion method`** 경고가 붙는다 —\
  `String?` 에 `toString()` 을 부르면 같은 `String?` 이 나오므로 컴파일러가 군더더기로 본 것이다.

### 10. 어느 것이 언어 보장이고 어느 것이 컴파일러 구현인가

| 사실 | 어느 쪽 | 근거 |
|---|---|---|
| `String` 에 `null` 을 못 넣는다 | **언어** | 컴파일 에러 3종 |
| `?.` 가 `null` 이면 `null` 을 낸다 | **언어** | 명세 + 실측 |
| `?:` 가 단락 평가한다 | **언어** | 명세 |
| `!!` 가 `null` 이면 NPE | **언어** | 명세 |
| `Nothing` 이 모든 타입의 하위 타입 | **언어** | 명세 |
| **`?.` 가 `ifnull` 로 내려간다** | **구현** | `javap` |
| **`!!` 가 `Intrinsics.checkNotNull` 이다** | **구현** | `javap` |
| **`!!` 의 NPE 메시지가 없는 것** | **구현** | 실행 — 인자 1개 오버로드 선택 |
| **non-null 파라미터 검사** | **구현 — 그리고 끌 수 있다** ★ | `javap` + `-Xno-param-assertions` |
| **그 NPE 의 문구** | **구현** | 실행 |
| **`private` 함수에 안 심는 것** | **구현** | `javap` |

- ★ **"Kotlin 은 런타임에도 null 을 막는다" 는 조건 없이 참이 아니다.**\
  참인 범위는 **기본 설정으로 컴파일된 공개 표면**까지다.\
  플래그를 켜면 사라지고(6번), `private` 함수에는 애초에 없으며(5번),\
  Java 경계에서 **들어오는** 쪽은 [05번](../05-platform-types/)에서 또 한 번 뚫린다.
- 설계 논증 쪽 정본은 [`../../언어-특성/README.md`](../../언어-특성/README.md) §2 —\
  "타입 시스템이 주는 것은 한 경계에서의 거부이고, 그 경계를 어디에 그을지는 설계가 정한다" 가 같은 말이다.

### 11. 다른 주제와 잇기

- **null 검사 뒤에도 `?.` 를 요구받는 자리 → [04번 주제](../04-smart-casts/)** 가 정본.\
  `var` 프로퍼티·커스텀 getter·다른 모듈의 `val` 에서 스마트 캐스트가 거부되고,\
  그때 나오는 메시지가 1번 `[B]` 와 **같은 문구**(`only safe (?.) or non-null asserted (!!.)…`)인 경우가 있다.
- **Java 경계에서 보장이 사라지는 것 → [05번 주제](../05-platform-types/)** 가 정본.\
  이 문서의 `checkNotNullParameter` 는 **Java 가 들어올 때**를 막고,\
  05번의 `checkNotNullExpressionValue` 는 **Java 에서 나올 때**를 막는다. **방향이 반대인 두 검사**다.
- **Java 쪽 대응 → [`../../../java/syntax/60-null-handling/`](../../../java/syntax/60-null-handling/)** 가 정본.\
  방어 시점 셋(경계·생성자·반환값), `requireNonNull` 의 메시지 설계, 컬렉션별 `null` 정책이 거기 있다.\
  `Optional` 이라는 **런타임 객체**로 푼 쪽은 [`../../../java/syntax/38-optional/`](../../../java/syntax/38-optional/).
- **`requireNotNull`** — 목록의 **51번 주제**(`require`/`check`/`error`/`TODO`)가 정본이 된다.

---

## 실행 검증

**환경**

```text
info: kotlinc-jvm 2.4.20 (JRE 21.0.5+11-LTS)
openjdk version "21.0.5" 2024-10-15 LTS
OpenJDK Runtime Environment Temurin-21.0.5+11 (build 21.0.5+11-LTS)
```

| 프로그램 | 무엇을 확인했나 | 돌린 방법 |
|---|---|---|
| `bad.kt` | `String`/`String?` 거부 3종과 **서로 다른 문구** | `kotlinc bad.kt` (컴파일 실패가 결과) |
| `ex.kt` | `?.` 사슬 4경우, `?:`, `?.let` 실행 횟수, `as?`/`as`, `filterNotNull`/`orEmpty`, `!!` 메시지 | `kotlinc` → `java` |
| `icode2.kt` | `?.`·`!!`·`?:`·non-null 파라미터의 바이트코드 | `javap -c -p outi/Icode2Kt.class` |
| `icode2.kt` (플래그) | `-Xno-param-assertions` 로 검사가 사라지는 것, 세 플래그를 다 줘도 `!!` 가 남는 것 | `javap` 두 번 |
| `vis.kt` | 가시성별 `checkNotNullParameter` 유무 6경우 (람다 포함) | `javap -c -p outv/VisKt.class` · `outv/C.class` |
| `K.kt` + `J.java` | `!!` 의 NPE 와 **Java 가 넘긴 `null` 의 NPE** 를 나란히 | `kotlinc K.kt` → `javac -cp outk J.java` → `java` 두 번 |
| `ext.kt` | `s.toString()` 대 `s?.toString()`, `isNullOrEmpty`, `?: throw`, **경고 1건** | `kotlinc` (경고) → `java` |
| kotlin-stdlib | `Intrinsics` 의 null 검사 오버로드 전수 | `javap -cp kotlin-stdlib.jar -p kotlin.jvm.internal.Intrinsics` |

**구현 의존 항목** — `javap` 의 명령 목록·상수 풀 번호, `Intrinsics` 의 함수 이름,
NPE 메시지 문구(`Parameter specified as non-null is null: …`), `!!` 의 빈 메시지,
`private` 함수에 검사가 없는 것, `-Xno-*-assertions` 플래그 이름 — 전부 **이 컴파일러 버전의 산출물**이다.\
반면 "`String`/`String?` 는 다른 타입"·"`?.` 는 `null` 이면 `null`"·"`?:` 는 단락 평가"·
"`Nothing` 이 모든 타입의 하위 타입" 은 **언어 규칙**이라 버전·타깃과 무관하다.

**양쪽을 다 돌린 것** — 4번은 **Kotlin 안에서 부른 판(`KKt`)과 Java 에서 부른 판(`J`)을 둘 다** 실행했다.
Kotlin 안에서만 돌리면 `checkNotNullParameter` 가 **한 번도 안 걸린다** — 타입 검사가 앞에서 막기 때문이다.
**검사가 실제로 일하는 것을 보려면 Java 쪽에서 불러야 한다.**

**★ 던져 봤더니 예상과 달랐던 것** — `-Xno-param-assertions` 로 컴파일한 뒤 Java 가 `null` 을 넘기면
"더 깊은 곳에서 터질 것" 이라고 예상했다. **안 터졌다.**

```text
$ kotlinc -Xno-param-assertions K.kt -jvm-target 21 -d outk2f/
$ javac -cp outk2f -d outk2f J.java
$ java -cp "outk2f:kotlin-stdlib.jar" J
안녕 null
```

`fun greet(name: String): String = "안녕 $name"` 의 `name` 은 **non-null 타입인데 `null` 을 들고 있고**,
보간은 그것을 `"null"` 넉 자로 바꿔([02번](../02-string-templates-and-raw-strings/)의 4번) **아무 일 없이 완주했다.**
**예외도 경고도 없다.** 타입이 거짓말을 한 채로 값이 흘러간다.

이것이 이 검사를 끄면 안 되는 진짜 이유다 — 잃는 것은 "좋은 에러 메시지" 가 아니라 **실패한다는 사실 자체**다.
