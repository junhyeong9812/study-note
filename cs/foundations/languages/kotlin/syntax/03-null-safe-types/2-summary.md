# kotlin/syntax/03 — null 안전 타입: `?`·`?.`·`?:`·`!!` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Null safety](https://kotlinlang.org/docs/null-safety.html) · [Type checks and casts](https://kotlinlang.org/docs/typecasts.html) · [kotlin-stdlib `let`](https://kotlinlang.org/api/core/kotlin-stdlib/kotlin/let.html).
> **실행 검증** — 모든 출력·예외·에러·바이트코드는 **kotlinc 2.4.20 (JRE 21.0.5)** 과 Temurin **JDK 21.0.5** 의 `javap` 에서 실제로 얻었다.\
> Java 쪽 호출은 같은 JDK 의 `javac` 로 컴파일해 **실제로 섞어 돌렸다.**
> **버전** — `?`·`?.`·`?:`·`!!` 는 1.0. 컴파일러는 **K2**(2.0 이후 기본).
> **경계** — [`../../언어-특성/README.md`](../../언어-특성/README.md) §2 는 **「왜 null 을 타입에 넣은 언어를 고르나」** 와\
> 그 방어선이 끝나는 자리라는 **설계 논증**이 정본이다.\
> 여기는 **「그 문법이 JVM 위에서 무엇으로 내려앉나」** 만 다룬다 — `?.` 가 만드는 분기, `!!` 가 부르는 함수, 컴파일러가 심는 검사.\
> **Java 쪽 대응(`Objects.requireNonNull`·`Optional`)의 정본은 [`../../../java/syntax/60-null-handling/`](../../../java/syntax/60-null-handling/)** 다.\
> **Java 경계에서 이 보장이 사라지는 것은 [05번 주제](../05-platform-types/)** 가 정본이다 — 여기서는 문법만 다룬다.
> 이 본문은 Claude 작성이다(원고 없음).

## 한눈에 — 쉽게 말하면

**Kotlin 의 null 안전은 "`null` 을 조심하는 규율" 이 아니라 "`null` 이 들어갈 수 있는 타입과 없는 타입을 아예 나눈 것" 이다.**\
**그리고 그 둘 사이를 건너는 문은 넷뿐이다.**

비유 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 출입증이 필요한 구역 | non-null 타입 (`String`) |
| 출입증 없이 들어갈 수 있는 구역 | nullable 타입 (`String?`) |
| "없으면 그냥 돌아가라" 는 문 | `?.` (safe call) |
| "없으면 이걸 써라" 는 문 | `?:` (엘비스) |
| "없을 리 없다, 내가 책임진다" 는 문 | `!!` |
| "있으면 이 방에 들어가라" 는 문 | `?.let { }` |
| 정문에 세워 둔 경비 | 컴파일러가 심는 `Intrinsics.checkNotNullParameter` |

```text
       String?  (없을 수 있다)                String  (없을 수 없다)
       ─────────────────────────┐   ┌────────────────────────────
                                │   │
          s?.length  ───────────┼───> 없으면 null 을 내고 끝      (?.)
          s ?: 기본값 ──────────┼───> 없으면 기본값              (?:)
          s!!        ───────────┼───> 없으면 NPE                 (!!)
          s?.let { }  ──────────┼───> 있을 때만 블록 실행         (?.let)
                                │   │
       ─────────────────────────┘   └────────────────────────────
```

**똑같은 구조로** Kotlin 이 동작한다 — `?` 는 **타입에 붙는 표시**이지 변수에 붙는 주의사항이 아니다.

실무에서 이게 터지는 자리는 **`!!` 다.**\
컴파일이 막히니까 `!!` 를 붙여서 통과시키고, **그 순간 언어가 준 보장이 그 줄에서만 취소된다.**

> **null 안전(null safety)** — `null` 이 들어갈 수 있는지를 **타입으로** 구분해 컴파일 시점에 막는 것.\
> 예: `String` 에는 `null` 을 못 넣고 `String?` 에는 넣을 수 있다. **둘은 다른 타입이다.**

> **safe call(안전 호출)** — `?.` — 수신자가 `null` 이면 호출을 건너뛰고 `null` 을 결과로 내는 연산자.\
> 예: `s?.length` 는 `s` 가 `null` 이면 `null` 이다.

## 이 주제가 답하려는 질문

1. `String` 과 `String?` 는 **정말 다른 타입인가** — 컴파일러가 무엇으로 거부하는가.
2. `?.`·`?:`·`!!` 는 **각각 무엇으로 컴파일되는가** — 마법인가 분기인가.
3. null 안전은 **타입 시스템만의 일인가** — 런타임에 남는 코드가 있는가, 있다면 어디에.

## 동작 방식

### (1) `String` 과 `String?` 는 다른 타입이다 — 세 가지 에러로 확인한다

**언제 쓰나** — Java 에서 넘어와 "변수에 `null` 이 들어갈 수 있다" 를 주석으로 적던 습관을 버릴 때.

```kotlin
val s: String? = "가"
val t: String = s
println(s.length)
val u: String = null
```

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

```text
     String?  ───X───>  String        (대입 불가)
     null     ───X───>  String        (대입 불가)
     String   ───O───>  String?       (반대 방향은 자유)

     String?  에 직접 . 호출 ───X───>  "only safe (?.) or non-null asserted (!!.)"
```

그림 해설:

- **세 에러 문구가 다르다.** 첫째는 타입 불일치, 둘째는 **호출 규칙**, 셋째는 리터럴 `null` 전용이다.
- 둘째 메시지가 특히 값어치가 있다 — **"어떻게 고치는지" 가 메시지 안에 들어 있다**(`?.` 또는 `!!.`).
- 반대 방향(`String` → `String?`)은 자유다. **non-null 은 nullable 의 부분집합**이기 때문이다.
- [01번](../01-val-var-and-basic-types/)의 `Int`/`Int?` 와 같은 구조다. 거기는 **런타임 표현**이 갈렸고, 여기는 **컴파일 규칙**이 갈린다.

비용 — 0. 전부 컴파일 타임이다.

### (2) ★★ `?.` 는 마법이 아니라 분기다

**언제 쓰나** — `?.` 가 런타임에 무슨 일을 하는지 물을 때.

```kotlin
fun safeCall(s: String?): Int? = s?.length
```

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
```

```text
   aload_0  ──> 스택에 s
   dup      ──> 하나 복사
   ifnull ───────────────┐
      |                  │ (null 이면)
      |                  v
   length()            pop        ← 복사본 버리기
   valueOf             aconst_null
      |                  |
      └──> areturn <─────┘
```

- **`ifnull` 이라는 JVM 분기 명령 하나다.** `if (s != null) s.length() else null` 을 손으로 쓴 것과 같다.
- `?.` 사슬이 길어지면 **분기가 그만큼 늘어난다** — 비용은 비교 몇 번이다.
- 반환이 `Int?` 라 **`Integer.valueOf` 로 박싱**된다([01번](../01-val-var-and-basic-types/)의 (6)).

`?:`(엘비스)도 같은 모양이다.

```kotlin
fun elvis(s: String?): Int = s?.length ?: -1
```

```text
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

- ★ **`?.` 와 `?:` 가 한 분기로 합쳐졌고 박싱이 사라졌다**(`int` 반환).\
  두 연산자를 따로 적었는데 컴파일러가 중간 `Integer` 를 만들지 않았다.
- 그래서 **`s?.length ?: -1` 은 `Int?` 를 거쳐 가지 않는다.** 이 관용구가 싼 이유다.

비용 — 분기 한 번. 객체 할당 0.

### (3) ★★ `!!` 는 `Intrinsics.checkNotNull` 이다 — 그리고 메시지가 없다

**언제 쓰나** — `!!` 를 지우자고 설득해야 할 때.

```kotlin
fun bang(s: String?): Int = s!!.length
```

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

**출력** (`K.kt` 실행 — 예외를 잡아 찍은 것)

```text
!! -> java.lang.NullPointerException
   message = null
   at KKt.bang(K.kt:2)
   at KKt.main(K.kt:4)
   at KKt.main(K.kt)
```

- ★ **`checkNotNull` 은 인자가 하나다**(`(Ljava/lang/Object;)V`) — **메시지를 받을 자리가 없다.**\
  그래서 던져지는 NPE 의 `message` 가 **`null`** 이다.
- 스택 트레이스는 `!!` 가 적힌 줄(`K.kt:2`)을 가리킨다. **어느 줄인지는 알려 주고 무엇이 `null` 이었는지는 안 알려 준다.**
- 비교 — Java 의 `Objects.requireNonNull(x, "메시지")` 는 메시지를 받는다.\
  그 설계 비교의 정본은 [`../../../java/syntax/60-null-handling/`](../../../java/syntax/60-null-handling/).
- **`!!` 를 굳이 써야 하면 `requireNotNull(x) { "왜 없으면 안 되는지" }` 로 바꾼다** — 메시지가 남는다.

비용 — 함수 호출 한 번(JIT 가 인라인한다). **진짜 비용은 진단 정보를 잃는 것이다.**

### (4) ★★ null 안전은 타입 시스템만의 일이 아니다 — 컴파일러가 런타임 검사를 심는다

**언제 쓰나** — "Kotlin 은 컴파일 타임에만 막는 거 아닌가" 라고 물을 때.

```kotlin
fun nonNullParam(s: String, t: String?): Int = s.length + (t?.length ?: 0)
```

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

★ **소스에 없는 검사가 함수 첫 줄에 들어갔다.** 그리고 **non-null 파라미터에만** 들어갔다 —\
`s` 는 검사받고 `t`(nullable)는 안 받는다.

**누가 그 검사에 걸리나** — Java 쪽이다.

```java
System.out.println(KKt.greet(null));   // greet(name: String)
```

**출력** (`java -cp "outk:kotlin-stdlib.jar" J`)

```text
Java 가 null 을 넘김 -> java.lang.NullPointerException
   message = Parameter specified as non-null is null: method KKt.greet, parameter name
   at KKt.greet(K.kt)
   at J.main(J.java:4)
```

- ★ **이 메시지에는 함수 이름과 파라미터 이름이 들어 있다** — `!!` 의 빈 메시지와 정반대다.\
  컴파일러가 `ldc "s"` 로 **이름을 상수로 박아 뒀기 때문**이다.
- 스택의 맨 위가 `KKt.greet` 다 — **Kotlin 함수 안으로 한 발짝 들어온 자리에서 즉시 터진다.**\
  `null` 이 도메인 로직까지 흘러가지 않는다.

**가시성에 따라 검사가 붙기도 하고 안 붙기도 한다.**

```text
  public  fun pub(s: String)     ──> checkNotNullParameter  O
  internal fun intl(s: String)   ──> checkNotNullParameter  O
  private fun priv(s: String)    ──> 없음                   ★
  class C { private fun p(...) } ──> 없음                   ★
  람다 (Function1 로 불린다)      ──> checkNotNullParameter  O
```

- ★ **`private` 함수에는 안 심는다.** **밖에서 부를 수 없으니 검사할 이유가 없다**는 뜻이고,\
  뒤집으면 **이 검사의 목적이 "Kotlin 코드 방어" 가 아니라 "바깥(주로 Java) 방어" 라는 증거**다.
- 람다에는 붙는다 — `Function1.invoke(Object)` 라는 **지워진 시그니처로 불리기 때문**이다.

비용 — 참조 비교 한 번. **공개 함수 수만큼만 생긴다.**

### (5) ★ 그 검사는 플래그로 끌 수 있다 — 그런데 `!!` 는 안 꺼진다

**언제 쓰나** — (4)의 검사가 "언어 보장" 인지 "컴파일러 서비스" 인지 가를 때.

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

```text
  끌 수 있는 것                          못 끄는 것
  +--------------------------------+    +--------------------------------+
  | checkNotNullParameter           |    | ?.  (ifnull 분기)              |
  | checkNotNullExpressionValue     |    | ?:  (ifnull 분기)              |
  |   (05번 플랫폼 타입)             |    | !!  (checkNotNull) ★           |
  +--------------------------------+    +--------------------------------+
     = 컴파일러가 얹은 방어 코드            = 언어가 정한 의미
```

- ★ **`checkNotNullParameter` 는 사라지는데 `!!` 의 `checkNotNull` 은 남는다.**\
  앞엣것은 **방어**이고 뒤엣것은 **의미**이기 때문이다. `!!` 는 "여기서 `null` 이면 터뜨려라" 라는 **요청** 자체다.
- `?.` 의 `ifnull` 도 그대로 남는다 — 당연하다. 그게 없으면 코드의 뜻이 바뀐다.
- **그래서 (4)의 검사는 "언어 보장" 이 아니라 "Kotlin/JVM 컴파일러의 서비스" 다.** 플래그 하나로 없어진다.

비용 — 플래그를 켜면 검사가 사라져 조금 빨라지지만, **Java 경계의 NPE 가 늦게·나쁜 메시지로 터진다.** 권하지 않는다.

### (6) `?.` 사슬 — 중간이 `null` 이면 전체가 `null`

**언제 쓰나** — 중첩 객체를 파고들 때.

```kotlin
class Addr(val city: String?)
class User(val addr: Addr?)

full.addr?.city?.length
```

**출력** (`ex.kt`)

```text
--- 1. ?. 사슬 ---
full   -> 2
noAddr -> null
noCity -> null
null u -> null
```

```text
   full.addr?.city?.length
        │      │     │
        │      │     └── 여기까지 왔으면 Int
        │      └──────── city 가 null 이면 여기서 끝 -> 전체 null
        └─────────────── addr 가 null 이면 여기서 끝 -> 전체 null

   결과 타입은 언제나 Int?  (어디서 끊겼는지는 알 수 없다)
```

- ★ **어디서 끊겼는지는 결과에 안 남는다.** 셋 다 `null` 이다.\
  구분이 필요하면 사슬을 쪼개거나 `?: error("addr 없음")` 을 중간에 넣는다.
- 결과 타입은 **항상 nullable** 이다 — 사슬 끝이 non-null 이어도 `Int?` 다.

비용 — 링크 수만큼의 `ifnull` 분기.

### (7) `?:` 오른쪽에 `return`·`throw` 를 놓는 관용구

**언제 쓰나** — "없으면 여기서 끝낸다" 를 한 줄로 적을 때.

```kotlin
fun label(u: User?): String {
    val city = u?.addr?.city ?: return "주소 없음"
    return "도시=$city"
}
fun need(s: String?): Int = (s ?: throw IllegalArgumentException("s 가 없다")).length
```

**출력** (`ex.kt` · `ext.kt`)

```text
label(full)=도시=서울  label(noAddr)=주소 없음
```

```text
--- ?: 오른쪽에 throw ---
need(null) -> IllegalArgumentException: s 가 없다
need("가") -> 1
```

- ★ **`return`·`throw` 의 타입이 `Nothing`** 이라서 이게 성립한다.\
  `Nothing` 은 **모든 타입의 하위 타입**이므로 `?:` 의 오른쪽 어디에나 들어간다.\
  그래서 왼쪽 결과 타입이 `String?` 이어도 **`city` 의 타입은 `String`** 이 된다.
- `Nothing` 자체의 정본은 [목록의 **34번 주제**](../34-exceptions-nothing-and-try-expression/)(예외·`Nothing` 타입)가 된다.
- **이 관용구가 `!!` 의 실질적인 대체재다** — 터지는 건 같지만 **메시지를 남길 수 있다.**

비용 — 분기 한 번.

### (8) nullable 수신자를 받는 확장 함수 — `?.` 없이 불린다

**언제 쓰나** — `s.isNullOrEmpty()` 가 왜 컴파일되는지 물을 때.

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

- **확장 함수는 수신자를 첫 인자로 받는 정적 함수**라서, 수신자 타입을 `String?` 으로 선언하면\
  `null` 에서도 호출된다. **멤버 함수는 그럴 수 없다**(디스패치를 위해 객체가 필요하다).
- ★ **함정** — `Any?.toString()` 이 그런 확장이라 `s.toString()` 은 **`"null"` 이라는 넉 자 문자열**을 돌려준다.\
  `null` 이 아니다. `s?.toString()` 이라야 `null` 이다. **한 글자 차이로 다른 값**이다.
- 그리고 `s?.toString()` 에는 경고가 붙는다.

```text
ext.kt:6:39: warning: redundant call of conversion method.
    println("s?.toString()     = ${s?.toString()}")
                                      ^^^^^^^^^^
```

- 컬렉션 쪽에도 같은 형태가 있다 — `filterNotNull()`·`orEmpty()`.

```text
--- 5. 컬렉션 ---
filterNotNull -> [가, 다]
orEmpty -> []
```

- 확장 함수 자체의 정본은 [목록의 **13번 주제**](../13-extension-functions-and-properties/)이고, 컬렉션 연산은 [목록의 **40번 주제**](../40-read-only-collections-and-runtime-types/)부터가 정본이 된다. 여기서는 **존재만** 짚는다.

비용 — 정적 호출 한 번.

## 문법 — 형태와 규칙

```kotlin
// 타입
val a: String  = "가"      // null 불가
val b: String? = null      // null 가능

// 네 가지 문
b?.length                  // safe call      -> Int?
b ?: "기본"                 // 엘비스          -> String
b!!                        // 단정            -> String (없으면 NPE)
b?.let { it.length }       // 있을 때만 블록   -> Int?

// 안전 캐스트
val any: Any = "문자열"
any as? String             // 실패하면 null
any as  Int                // 실패하면 ClassCastException

// 관용구
val v = b ?: return        // 없으면 조기 반환
val w = b ?: throw IllegalArgumentException("없다")
requireNotNull(b) { "왜 필요한지" }

// nullable 수신자 확장
b.isNullOrEmpty()          // ?. 없이 호출된다
b.orEmpty()                // null 이면 ""
listOfNullable.filterNotNull()
```

규칙 불릿.

- **`?` 는 타입에 붙는다.** `String?` 은 `String` 의 "옵션" 이 아니라 **다른 타입**이다.
- `?.` 의 결과는 **항상 nullable** 이다. 사슬 끝이 non-null 이어도 그렇다.
- `?:` 는 **왼쪽이 `null` 일 때만** 오른쪽을 평가한다(단락 평가).
- `as?` 는 실패하면 `null`, `as` 는 `ClassCastException` 이다.

**출력** (`ex.kt`)

```text
--- 4. as? ---
any as? String -> 문자열
any as? Int    -> null
any as Int -> ClassCastException: class java.lang.String cannot be cast to class java.lang.Integer (java.lang.String and java.lang.Integer are in module java.base of loader 'bootstrap')
```

- `?.let { }` 은 **블록이 안 돌 수도 있다.** 부수효과를 넣으면 조용히 건너뛴다.

**출력** (`ex.kt`)

```text
--- 3. ?.let ---
t?.let -> 3
s?.let -> null
let 본문이 돈 횟수 = 1
```

## 어디서 틀리나

| 틀리는 형태 | 무슨 일이 일어나나 | 고치는 법 |
|---|---|---|
| 컴파일이 막혀서 `!!` 를 붙임 | 그 줄에서 언어 보장이 취소된다. 터지면 **메시지가 없다** | `?:` + `return`/`throw` 또는 `requireNotNull` |
| `s.toString()` 으로 null 을 다룸 | `"null"` **넉 자 문자열**이 나온다 | `s?.toString()` 또는 `s ?: "(없음)"` |
| `?.` 사슬로 뭉뚱그림 | 어디서 끊겼는지 알 수 없다 | 사슬을 쪼개거나 중간에 `?: error(...)` |
| `?.let { }` 안에 부수효과 | `null` 이면 조용히 안 돈다 | 조건을 명시하거나 `?: run { }` 로 else 를 적는다 |
| `!!` 를 여러 개 이어 씀 (`a!!.b!!.c!!`) | 어느 `!!` 가 터졌는지 줄 번호로만 안다 | 사슬을 쪼갠다 |
| non-null 이라 믿고 Java 에서 호출 | `Parameter specified as non-null is null` NPE | 경계에 `@Nullable` 을 달거나 Kotlin 쪽을 `?` 로 연다([05번](../05-platform-types/)) |
| 플랫폼 타입을 `?` 없이 받음 | 컴파일은 통과하고 **런타임에 터진다** | **[05번 주제](../05-platform-types/)가 정본** |
| `as` 로 캐스트 | 실패하면 `ClassCastException` | 분기로 처리할 거면 `as?` + `?:` |
| null 검사 뒤에도 `?.` 를 요구받음 | 스마트 캐스트가 거부된 것이다 | **[04번 주제](../04-smart-casts/)가 정본** |

## 구현 세부사항 대 언어 보장

| 사실 | 누가 보장하나 | 근거 |
|---|---|---|
| `String` 에 `null` 을 못 넣는다 | **언어** | 컴파일 에러 3종 |
| `?.` 가 수신자가 `null` 이면 `null` 을 낸다 | **언어** | 명세 + 실측 |
| `?:` 가 왼쪽이 `null` 일 때만 오른쪽을 평가한다 | **언어** | 명세 |
| `!!` 가 `null` 이면 NPE 를 던진다 | **언어** | 명세 |
| **`?.` 가 `ifnull` 분기로 내려간다** | **구현** | `javap` |
| **`!!` 가 `Intrinsics.checkNotNull` 이다** | **구현** | `javap` |
| **`!!` 의 NPE 메시지가 `null` 인 것** | **구현** | 실행 — 인자 하나짜리 오버로드라서 |
| **non-null 파라미터에 검사가 심기는 것** | **구현**(끌 수 있다) ★ | `javap` + `-Xno-param-assertions` |
| **그 NPE 메시지 문구** | **구현** | 실행 — `Parameter specified as non-null is null: …` |
| **`private` 함수에는 안 심는 것** | **구현** | `javap` |
| `Nothing` 이 모든 타입의 하위 타입인 것 | **언어** | 명세 — `?: return` 이 성립하는 근거 |

★ **가장 중요한 구분 한 줄** — **`?.`·`?:`·`!!` 는 끌 수 없고(언어 의미), 파라미터 검사는 끌 수 있다(컴파일러 방어).**\
그래서 "Kotlin 은 런타임에도 null 을 막는다" 는 **기본 설정에서만 참인 문장**이다.

## 언제 쓰고 언제 안 쓰나

| 상황 | 고르는 것 | 왜 |
|---|---|---|
| 없으면 아무것도 안 해도 될 때 | `?.` | 분기를 안 적어도 된다 |
| 없으면 기본값이 있을 때 | `?:` | 결과가 non-null 이 된다 |
| 없으면 여기서 끝내야 할 때 | `?: return` / `?: throw` | 아래 코드가 non-null 을 본다 |
| 없으면 프로그래밍 오류일 때 | `requireNotNull(x) { "…" }` | 메시지가 남는다 |
| 있을 때만 여러 줄을 돌릴 때 | `?.let { }` | 지역 `val` 이 생겨 스마트 캐스트 문제도 함께 풀린다([04번](../04-smart-casts/)) |
| 타입이 맞을 때만 쓸 때 | `as?` + `?:` | 예외 대신 값으로 처리 |
| 경계에서 외부 입력을 받을 때 | 즉시 검증 후 non-null 도메인 타입으로 | 안쪽이 `?` 를 안 본다 |
| **`!!`** | **거의 언제나 안 쓴다** | 메시지가 없고 보장이 취소된다 |

판단 규칙 두 줄.

- **`!!` 를 쓰고 싶어지면 그 자리는 「`null` 이면 어떻게 할지 아직 안 정한 자리」다.** 정하고 나면 나머지 셋 중 하나가 된다.
- **`?` 는 경계에서 벗기고 안쪽으로 들이지 않는다.** 도메인 타입에 `?` 가 번지면 검사가 코드 전체로 퍼진다.

## 핵심 문장

- `String` 과 `String?` 는 **다른 타입**이다. 컴파일러는 대입·호출·리터럴 세 자리에서 각각 다른 문구로 거부한다.
- `?.` 는 마법이 아니라 **`ifnull` 분기 하나**다. `?:` 와 붙으면 **박싱도 안 생긴다.**
- `!!` 는 `Intrinsics.checkNotNull` 이고 **인자가 하나라 메시지를 담을 자리가 없다** — 터지면 `message = null`.
- 컴파일러는 **non-null 파라미터에 런타임 검사를 심는다.** 그런데 **`private` 함수에는 안 심는다** — 목적이 Java 방어라는 증거다.
- **`?.`·`?:`·`!!` 는 끌 수 없고 파라미터 검사는 `-Xno-param-assertions` 로 꺼진다.** 앞은 의미, 뒤는 방어다.
- `?: return` 이 성립하는 이유는 **`Nothing` 이 모든 타입의 하위 타입**이기 때문이다.
- `s.toString()` 은 `null` 이 아니라 **`"null"` 넉 자**다.

## 관련 자료

- [`../README.md`](../README.md) — Kotlin 문법·API 주제 목록(이 주제는 03번)
- [`../../언어-특성/README.md`](../../언어-특성/README.md) §2 — **「왜 null 을 타입에 넣었나」라는 설계 논증이 거기 정본**이다. 여기는 그 문법의 바이트코드까지
- [01번 주제](../01-val-var-and-basic-types/) — `Int`/`Int?` 가 **런타임 표현**에서 갈리는 것. 이 문서의 `String`/`String?` 와 짝이다
- [04번 주제](../04-smart-casts/) — **null 검사 뒤에 `?.` 가 여전히 필요해지는 자리**의 정본
- [05번 주제](../05-platform-types/) — **이 보장이 Java 경계에서 사라지는 자리**의 정본. 이 사슬의 정점이다
- [`../../../java/syntax/60-null-handling/`](../../../java/syntax/60-null-handling/) — **Java 쪽 정본.** `Objects.requireNonNull` 의 메시지 설계, 방어 시점 셋, 컬렉션별 null 정책
- [`../../../java/syntax/38-optional/`](../../../java/syntax/38-optional/) — Java 가 **런타임 객체**로 푼 쪽. Kotlin 이 **타입**으로 푼 것과의 대비
- [목록의 **33번 주제**](../33-type-checks-and-casts-is-as/)(`is`/`as`/`as?`) — 캐스트 전체의 정본
- [목록의 **34번 주제**](../34-exceptions-nothing-and-try-expression/)(예외·`Nothing` 타입) — `?: return` 의 근거인 `Nothing`
- 목록의 **51번 주제**(`require`/`check`/`error`) — `requireNotNull` 의 정본
- 목록의 **58번 주제**(null 처리 관용구) — 계층별 배치 판단

## 용어 풀이

- **nullable 타입** — `null` 을 담을 수 있는 타입. 타입 뒤에 `?` 를 붙여 만든다. `String?` 처럼.
- **non-null 타입** — `null` 을 담을 수 없는 타입. Kotlin 의 **기본값**이다.
- **safe call (`?.`)** — 수신자가 `null` 이면 호출을 건너뛰고 `null` 을 내는 연산자. `ifnull` 분기로 컴파일된다.
- **엘비스 연산자 (`?:`)** — 왼쪽이 `null` 이면 오른쪽 값을 내는 연산자. 이름은 기호가 엘비스 프레슬리의 머리 모양을 닮아서다.
- **단정 연산자 (`!!`)** — "여기는 `null` 이 아니다" 를 컴파일러에게 강제로 통보하는 연산자. 틀리면 NPE.
- **`Intrinsics`** — kotlin-stdlib 안의 내부 유틸 클래스. 컴파일러가 만든 검사 호출이 전부 여기로 간다.
- **`checkNotNull` / `checkNotNullParameter`** — 각각 `!!` 용(인자 1개, 메시지 없음)과 파라미터 방어용(인자 2개, 이름 포함).
- **`ifnull`** — 스택 맨 위가 `null` 이면 분기하는 JVM 명령. `?.`·`?:` 의 정체.
- **`Nothing`** — 값이 하나도 없는 타입. `throw`·`return` 의 타입이고 **모든 타입의 하위 타입**이다.
- **안전 캐스트 (`as?`)** — 캐스트에 실패하면 예외 대신 `null` 을 내는 연산자.
- **확장 함수(extension function)** — 타입 밖에서 선언하는 함수. 수신자를 `T?` 로 선언하면 `null` 에서도 불린다.

---

## 더 들어가면

- `Intrinsics` 가 가진 null 검사 함수를 전부 찍어 보면 이렇다.

```text
$ javap -cp kotlin-stdlib.jar -p kotlin.jvm.internal.Intrinsics | grep -iE 'checkNotNull|IsNotNull'
  public static void checkNotNull(java.lang.Object);
  public static void checkNotNull(java.lang.Object, java.lang.String);
  public static void checkExpressionValueIsNotNull(java.lang.Object, java.lang.String);
  public static void checkNotNullExpressionValue(java.lang.Object, java.lang.String);
  public static void checkReturnedValueIsNotNull(java.lang.Object, java.lang.String, java.lang.String);
  public static void checkReturnedValueIsNotNull(java.lang.Object, java.lang.String);
  public static void checkFieldIsNotNull(java.lang.Object, java.lang.String, java.lang.String);
  public static void checkFieldIsNotNull(java.lang.Object, java.lang.String);
  public static void checkParameterIsNotNull(java.lang.Object, java.lang.String);
  public static void checkNotNullParameter(java.lang.Object, java.lang.String);
```

  ★ **`checkNotNull` 에는 메시지를 받는 오버로드가 있는데 `!!` 는 그쪽을 안 쓴다** —\
  즉 **메시지를 못 담는 게 아니라 안 담기로 한 것**이다. `!!` 는 "설명할 게 없는 단정" 으로 설계됐다.\
  `…IsNotNull` 로 끝나는 것들은 **1.4 이전에 쓰던 옛 이름**이다 — stdlib 가 옛 바이너리를 위해 계속 들고 있다.\
  `checkNotNullExpressionValue` 는 [05번](../05-platform-types/)이 정본이다.
- `-Xno-param-assertions` 는 Kotlin 코드만으로 이뤄진 모듈에서 **바이너리 크기와 호출 비용을 줄인다.**\
  대신 Java 나 리플렉션으로 들어오는 `null` 이 **깊은 곳에서** 터진다. 라이브러리 개발에는 권하지 않는다.
- 람다에 `checkNotNullParameter` 가 붙는 것은 **타입 소거** 때문이다 — `Function1.invoke(Object)` 로 불리므로\
  호출자가 `null` 을 넣을 수 있다. 소거의 정본은 [`../../../java/syntax/19-type-erasure/`](../../../java/syntax/19-type-erasure/).
- `?.` 사슬 중간에 `?.also { }` 를 끼우면 **어디서 끊겼는지** 로그로 남길 수 있다. 다만 `also` 는 `null` 이면 안 돈다.
- `!!` 를 금지하는 팀 규약은 **정적 분석 도구의 규칙**으로 강제하는 것이 보통이다(이 문서에서 도구를 돌려 보지는 않았다).\
  언어가 안 막는 것을 도구가 막는 형태다 — Java 의 `@Nullable` 과 **방향이 반대**다.
