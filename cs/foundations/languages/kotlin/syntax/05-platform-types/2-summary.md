# kotlin/syntax/05 — 플랫폼 타입: Java 경계에서 null 보장이 사라지는 것 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Calling Java from Kotlin — Null-safety and platform types](https://kotlinlang.org/docs/java-interop.html#null-safety-and-platform-types) · [Nullability annotations](https://kotlinlang.org/docs/java-interop.html#nullability-annotations) · [Null safety](https://kotlinlang.org/docs/null-safety.html).
> **실행 검증** — 모든 출력·에러·바이트코드는 **kotlinc 2.4.20 (JRE 21.0.5)** 과 Temurin **JDK 21.0.5** 에서 실제로 얻었다.\
> Java 는 같은 JDK 의 `javac` 로 컴파일해 **한 클래스패스에 섞어 돌렸다.**\
> 애너테이션 실험에는 실제 jar 셋을 썼다 — `annotations-13.0.jar`(kotlinc 동봉) · `jsr305-3.0.2.jar` · `jspecify-1.0.0.jar`(로컬 저장소).
> **버전** — 플랫폼 타입은 1.0 부터. **JSpecify 위반이 경고가 아니라 오류가 된 것은 2.1.0.**
> **경계** — [03번 주제](../03-null-safe-types/)는 **`?`·`?.`·`?:`·`!!` 문법**이 정본이고,\
> [04번 주제](../04-smart-casts/)는 **컴파일러가 좁혀 주는 범위**가 정본이다.\
> 여기는 **「그 둘이 통째로 안 걸리는 구간」** 하나만 다룬다.\
> [`../../언어-특성/README.md`](../../언어-특성/README.md) §2·§9 는 **「그래서 이 언어를 고를 것인가」** 라는 설계 논증이 정본이다.\
> Java 쪽 방어(`Objects.requireNonNull`·경계 검증)는 [`../../../java/syntax/60-null-handling/`](../../../java/syntax/60-null-handling/) 가 정본이다.
> 이 본문은 Claude 작성이다(원고 없음).

## 한눈에 — 쉽게 말하면

**Kotlin 의 null 검사는 「타입을 적은 자리」에서 일어난다.**\
**Java 에서 온 값은 타입이 안 적혀 있고, 그래서 아무 데서도 안 걸린 채 흘러간다 — 내가 타입을 적기 전까지.**

비유 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 검문소가 있는 나라 | Kotlin 코드 |
| 검문소가 없는 나라 | Java 코드 |
| 국경에서 신분증을 안 보고 통과시키는 구간 | **플랫폼 타입** (`String!`) |
| 신분증을 요구하는 순간 = 검문소가 생기는 자리 | 내가 `String` 이라고 **적는** 순간 |
| "없어도 됩니다" 라고 적힌 입국 신고서 | `@Nullable` |
| "반드시 있어야 합니다" 라고 적힌 신고서 | `@NotNull` |
| 신고서 자체를 안 냈을 때 | 애너테이션 없음 → 플랫폼 타입 |

```text
   Java                국경 (플랫폼 타입 구간)            Kotlin
   ────────────────────────────────────────────────────────────────
   return null   ──>   val a = J.giveNull()       ──>  a.length
                       (검사 없음. 타입 String!)       ★ 여기서 JVM 이 터뜨린다

   return null   ──>   val b: String = J.giveNull()  ★ 여기서 Kotlin 이 터뜨린다
                       (내가 타입을 적었다 -> 검사 삽입)
```

**똑같은 구조로** Kotlin 이 동작한다 — **어디서 터지느냐는 Java 가 정하는 게 아니라 내가 타입을 어디에 적었는지가 정한다.**

실무에서 이게 터지는 자리는 **JDBC·JSON 파서·레거시 유틸의 반환값**이다.\
타입을 안 적고 `val x = row.getString("name")` 으로 받으면, **NPE 가 파싱 코드가 아니라 도메인 로직 한가운데서** 난다.

> **플랫폼 타입(platform type)** — Java 에서 온 타입 중 nullability 를 알 수 없는 것.\
> 오류 메시지에서 `String!` 로 표시되고 **소스에 적을 수 없다.** 컴파일러가 null 검사를 **유예**한다.

> **비표기 타입(non-denotable type)** — 컴파일러는 아는데 **소스 코드에 이름으로 적을 수 없는** 타입.\
> 예: `String!`. 그래서 존재를 확인하려면 **에러 메시지를 짜내야** 한다.

## 이 주제가 답하려는 질문

1. 플랫폼 타입은 **어떻게 관찰하는가** — 소스에 못 적는 타입의 존재를 무엇으로 증명하는가.
2. `null` 이 넘어오면 **어디서 터지는가** — 대입하는 줄인가 쓰는 줄인가, 그리고 그것을 무엇이 정하는가.
3. `@Nullable`/`@NotNull` 은 **무엇을 바꾸는가** — 그리고 `-Xjsr305` 는 그중 무엇을 다루는가.

## 동작 방식

### (1) ★ 플랫폼 타입을 관찰하는 법 — 에러 메시지를 짜낸다

**언제 쓰나** — "지금 이 값의 타입이 `String` 인가 `String?` 인가 `String!` 인가" 를 알고 싶을 때.

소스에 못 적는 타입이므로 **직접 확인할 방법이 없다.** 대신 **타입 불일치를 일부러 내서 컴파일러가 실토하게** 한다.

```kotlin
fun probe() {
    val a = J.giveNull()
    val x: Int = a            // 일부러 틀린 타입을 적는다
}
fun probe2() {
    val b: String! = J.giveNull()   // 적을 수 있나?
}
```

**출력** (`kotlinc pt.kt -cp out`)

```text
pt.kt:3:16: error: initializer type mismatch: expected 'Int', actual 'String!'.
    val x: Int = a            // 일부러 틀린 타입을 적는다
               ^
pt.kt:6:18: error: syntax error: Unexpected token.
    val b: String! = J.giveNull()   // 적을 수 있나?
                 ^
```

- ★ **`actual 'String!'`** — 컴파일러가 플랫폼 타입을 **`String!`** 이라고 부른다. 존재가 증명됐다.
- ★ 그런데 **`String!` 을 소스에 적으면 `syntax error: Unexpected token.`** 이다.\
  **컴파일러만 쓸 수 있고 내가 못 쓰는 타입**이다.
- 이 기법은 이 주제 밖에서도 쓴다 — **비표기 타입은 전부 이렇게 짜내서 본다.**
- IDE 가 `String!` 을 보여 주는 것도 같은 정보다. **IDE 없이도 `kotlinc` 하나로 확인된다.**

비용 — 없다. 진단용 코드는 지운다.

### (2) ★★ 어디서 터지나 — 내가 타입을 적은 자리에서 터진다

**언제 쓰나** — 이 주제의 핵심. NPE 스택 트레이스를 볼 때마다.

```kotlin
// Java
public static String giveNull() { return null; }
```

```kotlin
// A. 타입을 안 적는다
val a = J.giveNull()
println(a.length)

// B. String (non-null) 을 적는다
val b: String = J.giveNull()

// C. String? 를 적는다
val c: String? = J.giveNull()
```

**출력** (`K.kt` — 세 경우를 한 프로그램에서)

```text
--- A. 플랫폼 타입을 추론에 맡긴다 ---
대입은 통과했다. a = null
a.length -> java.lang.NullPointerException: Cannot invoke "String.length()" because "a" is null
--- B. 받는 쪽에 String (non-null) 을 적는다 ---
대입에서 터짐 -> java.lang.NullPointerException: giveNull(...) must not be null
--- C. 받는 쪽에 String? 를 적는다 ---
대입 통과: c = null, c?.length = null
--- D. 정상값이면 ---
d = 값, d.length = 1
```

```text
   A. 타입 안 적음               B. String 적음              C. String? 적음
   +---------------------+      +---------------------+     +---------------------+
   | val a = giveNull()  |      | val b: String = …   |     | val c: String? = …  |
   |   대입 통과 ★        |      |   ★ 여기서 터진다    |     |   대입 통과         |
   |   a = null          |      |                     |     |   c = null          |
   | a.length            |      |                     |     | c?.length -> null   |
   |   ★ 여기서 터진다    |      |                     |     |   안 터진다          |
   +---------------------+      +---------------------+     +---------------------+
     JVM 의 helpful NPE          Kotlin 의 NPE               예외 없음
     "because \"a\" is null"     "giveNull(...) must not      
                                  be null"
```

★ **터지는 자리가 셋 다 다르고, 메시지의 출처도 다르다.**

| | 어디서 | 누가 던지나 | 메시지 |
|---|---|---|---|
| A | **쓰는 줄** | **JVM** (helpful NPE) | `Cannot invoke "String.length()" because "a" is null` |
| B | **대입하는 줄** | **Kotlin** | `giveNull(...) must not be null` |
| C | 안 터진다 | — | — |

- ★ **A 의 메시지는 Kotlin 이 만든 것이 아니다.** JVM 14+ 의 helpful NullPointerException 이다 —\
  즉 **Kotlin 은 그 코드에 아무것도 안 넣었다.** (3)의 바이트코드가 그것을 보인다.
- ★ **B 는 Kotlin 이 심은 검사**다. 그래서 **Java 메서드 이름(`giveNull(...)`)이 메시지에 들어 있다.**
- **결론 — 「어디서 터지나」는 Java 가 아니라 내가 정한다.** 타입을 적으면 검사가 생기고, 안 적으면 안 생긴다.

비용 — B 는 참조 비교 한 번. A 는 0(아무것도 안 넣었으니까).

### (3) ★★ 바이트코드가 그것을 그대로 보여 준다

**언제 쓰나** — (2)를 믿게 만들 때.

```kotlin
fun inferred(): Int = J.giveNull().length
fun declared(): Int { val b: String = J.giveNull(); return b.length }
fun optional(): Int? { val c: String? = J.giveNull(); return c?.length }
```

**출력** (`javap -c -p outp/PKt.class`)

```text
public final class PKt {
  public static final int inferred();
    Code:
       0: invokestatic  #12                 // Method J.giveNull:()Ljava/lang/String;
       3: invokevirtual #17                 // Method java/lang/String.length:()I
       6: ireturn

  public static final int declared();
    Code:
       0: invokestatic  #12                 // Method J.giveNull:()Ljava/lang/String;
       3: dup
       4: ldc           #20                 // String giveNull(...)
       6: invokestatic  #26                 // Method kotlin/jvm/internal/Intrinsics.checkNotNullExpressionValue:(Ljava/lang/Object;Ljava/lang/String;)V
       9: astore_0
      10: aload_0
      11: invokevirtual #17                 // Method java/lang/String.length:()I
      14: ireturn

  public static final java.lang.Integer optional();
    Code:
       0: invokestatic  #12                 // Method J.giveNull:()Ljava/lang/String;
       3: astore_0
       4: aload_0
       5: dup
       6: ifnull        18
       9: invokevirtual #17                 // Method java/lang/String.length:()I
      12: invokestatic  #37                 // Method java/lang/Integer.valueOf:(I)Ljava/lang/Integer;
      15: goto          20
      18: pop
      19: aconst_null
      20: areturn
}
```

```text
   inferred()            declared()                      optional()
   +---------------+     +----------------------------+  +---------------------+
   | invokestatic  |     | invokestatic               |  | invokestatic        |
   | invokevirtual |     | dup                        |  | astore_0            |
   | ireturn       |     | ldc "giveNull(...)"        |  | ifnull ─┐           |
   +---------------+     | checkNotNullExpressionValue|  | length  │           |
     명령 3개              | astore_0   ★ 대입보다 먼저 |  | valueOf │           |
     ★ 검사가 없다         | aload_0                    |  | aconst_null <─┘     |
     Java 와 같은          | invokevirtual              |  +---------------------+
     바이트코드            +----------------------------+     ifnull 분기 (03번)
```

- ★ **`inferred()` 에는 검사가 하나도 없다.** Java 로 같은 코드를 썼을 때와 **바이트코드가 같다.**\
  "Kotlin 이 null 을 막아 준다" 는 문장이 **여기서는 아무 의미가 없다.**
- ★ **`declared()` 의 검사는 `astore_0`(대입) 보다 먼저** 온다 — **변수에 담기기 전에 터뜨린다.**\
  그래서 (2)의 B 에서 "대입에서 터짐" 이 나왔다.
- 함수 이름이 `ldc "giveNull(...)"` 로 **상수 풀에 박혀 있다.** 메시지가 거기서 나온다.
- `optional()` 은 [03번](../03-null-safe-types/)의 `?.` 와 똑같은 `ifnull` 분기다.
- 검사 이름이 [03번](../03-null-safe-types/)의 것과 다르다.

| 검사 | 막는 방향 | 정본 |
|---|---|---|
| `checkNotNullParameter` | **Java → Kotlin (들어오는 인자)** | [03번](../03-null-safe-types/) |
| `checkNotNullExpressionValue` | **Java → Kotlin (나오는 반환값)** | **여기** |

- 그리고 **이 검사도 끌 수 있다** — `-Xno-call-assertions` 를 주면 `declared()` 가 `inferred()` 와 같아진다(실측).

비용 — 참조 비교 한 번. **없앴을 때 잃는 것은 비용이 아니라 진단이다.**

### (4) ★★ 타입을 안 적으면 그 값은 어디까지 흘러가나

**언제 쓰나** — "그럼 대입만 조심하면 되나" 라고 물을 때. **아니다.**

**출력** (`chain.kt`)

```text
--- 1. 사슬로 바로 쓰면 (아무 타입도 안 적음) ---
   -> java.lang.NullPointerException: Cannot invoke "String.length()" because the return value of "J.giveNull()" is null
--- 2. non-null 원소 컬렉션에 담으면 ---
   -> java.lang.NullPointerException: giveNull(...) must not be null
--- 3. nullable 원소 컬렉션에 담으면 ---
   add 통과. list2=[null], size=1
--- 4. non-null 파라미터로 넘기면 ---
   -> java.lang.NullPointerException: giveNull(...) must not be null
--- 5. nullable 파라미터로 넘기면 ---
   needNullable(J.giveNull()) = -1
```

```text
      J.giveNull()   ──>  ?
                          │
       ┌──────────────────┼──────────────────┬──────────────────┐
       │                  │                  │                  │
   바로 .length      List<String> 에      need(s: String)    List<String?> 에
   (타입 안 적음)        add                 로 넘김             add
       │                  │                  │                  │
   JVM NPE            Kotlin NPE          Kotlin NPE         통과 (null 이 담긴다)
   (쓰는 줄)          (add 하는 줄) ★     (호출하는 줄) ★
```

- ★ **검사는 「대입」이 아니라 「declared non-null 자리로 건너가는 모든 지점」에 생긴다.**\
  변수 선언만이 아니라 **함수 인자·제네릭 타입 인자**도 포함된다.
- 그래서 규칙을 이렇게 고쳐 적는다 — **플랫폼 값은 non-null 타입이 적힌 첫 자리에서 걸린다.**\
  그런 자리를 한 번도 안 만나면 **끝까지 안 걸린다**(1번).
- ★ 3번이 가장 나쁘다 — `MutableList<String?>` 에 담으면 **`null` 이 컬렉션에 조용히 들어간다.**\
  나중에 그 리스트를 순회하다 **완전히 다른 곳에서** 터진다.

비용 — 검사 한 번씩.

### (5) ★★ `@Nullable`/`@NotNull` 을 붙이면 무엇이 달라지나 — 세 가지 애너테이션을 던져 봤다

**언제 쓰나** — 우리 팀 Java 코드에 무엇을 붙일지 정할 때.

**① JetBrains 애너테이션** (`org.jetbrains.annotations` — `annotations-13.0.jar`, kotlinc 에 동봉)

```java
public static @Nullable String maybeNull()   { return null; }
public static @NotNull  String neverNull()   { return "값"; }
public static          String noAnnotation() { return null; }
```

**출력** (`kotlinc ann/UseA.kt -cp "outann:annotations-13.0.jar"`)

```text
ann/UseA.kt:2:19: error: initializer type mismatch: expected 'String', actual 'String?'.
    val s: String = A.maybeNull()      // @Nullable -> String? 이므로 거부되어야 한다
                  ^
ann/UseA.kt:14:26: error: only safe (?.) or non-null asserted (!!.) calls are allowed on a nullable receiver of type 'String?'.
    println(A.maybeNull().length)      // @Nullable 에 직접 . 호출
                         ^
```

- ★ **`@Nullable` 이 붙으면 타입이 `String!` 이 아니라 `String?` 이 된다** — `actual 'String?'` 가 증거다.\
  (1)에서 짜냈던 `String!` 이 사라졌다.
- `@NotNull` 이 붙으면 `String` 이다 — `val s: String = A.neverNull()` 이 통과했다.
- 애너테이션이 없으면 그대로 플랫폼 타입이라 **통과한다**(`A.noAnnotation()` 도 `val s: String` 에 들어갔다).
- **즉 애너테이션은 "문서" 가 아니라 「타입을 바꾸는 선언」이다.** Java 쪽에서는 아무것도 안 바뀌는데\
  Kotlin 쪽에서는 컴파일 에러가 된다.

**② JSR-305** (`javax.annotation` — `jsr305-3.0.2.jar`)

```text
=== (플래그 없음) ===
jsr/UseB.kt:1:26: error: initializer type mismatch: expected 'String', actual 'String?'.
fun f1() { val s: String = B.maybeNull(); println(s) }
                         ^
=== -Xjsr305=ignore ===
jsr/UseB.kt:1:26: error: initializer type mismatch: expected 'String', actual 'String?'.
=== -Xjsr305=warn ===
jsr/UseB.kt:1:26: error: initializer type mismatch: expected 'String', actual 'String?'.
=== -Xjsr305=strict ===
jsr/UseB.kt:1:26: error: initializer type mismatch: expected 'String', actual 'String?'.
```

- ★ **네 조건에서 결과가 한 글자도 다르지 않다.** **`-Xjsr305` 는 평범한 `@Nullable`/`@Nonnull` 에 아무 영향이 없다.**\
  이 둘은 **언제나 지켜진다.**
- 그러면 `-Xjsr305` 는 무엇을 하는가 — (6)이 답한다.

**③ JSpecify** (`org.jspecify.annotations` — `jspecify-1.0.0.jar`)

```java
@NullMarked
public class D {
    public static String give()            { return "값"; }   // 기본이 non-null
    public static @Nullable String maybe() { return null; }
    public static void take(String s)      { … }
}
```

```text
=== JSpecify (기본) ===
spec/UseD.kt:4:19: error: initializer type mismatch: expected 'String', actual 'String?'.
    val b: String = D.maybe()      // @Nullable -> 거부되어야 한다
                  ^
spec/UseD.kt:6:12: error: null cannot be a value of a non-null type 'String'.
    D.take(null)                   // non-null 파라미터에 null -> 거부
           ^^^^
```

- ★ **`@NullMarked` 하나로 그 클래스 전체의 기본값이 non-null 로 뒤집힌다** —\
  `val a: String = D.give()` 가 통과했고, `D.take(null)` 은 **에러**다.
- **기본이 오류다**(경고가 아니다). Kotlin **2.1.0** 부터의 동작이다.
- 즉 **Java 라이브러리가 JSpecify 를 채택했으면 이 주제의 구멍이 그 라이브러리 표면에서 거의 사라진다.**

비용 — 컴파일 타임. 런타임 코드는 안 바뀐다.

### (6) ★ `-Xjsr305` 가 실제로 다루는 것 — 「기본값 애너테이션」이다

**언제 쓰나** — 빌드 스크립트에서 이 플래그를 봤을 때.

(5)②에서 안 걸렸으므로, 이번에는 **`@TypeQualifierDefault` 로 만든 커스텀 기본값**을 던졌다.

```java
@Nonnull
@TypeQualifierDefault({ElementType.METHOD, ElementType.PARAMETER})
@Retention(RetentionPolicy.RUNTIME)
public @interface NonNullApi {}

@NonNullApi
public class C {
    public static String give() { return null; }
    public static void take(String s) { … }
}
```

```kotlin
C.take(null)
```

**출력** (`kotlinc qual/UseC.kt -cp "outq:jsr305-3.0.2.jar"` — 네 조건)

```text
=== -Xjsr305=none (플래그 없음) ===
qual/UseC.kt:4:12: warning: Java type mismatch: inferred type is 'Nothing?', but 'String' was expected.
    C.take(null)
           ^^^^
=== -Xjsr305=ignore ===
(출력 없음 — 경고도 에러도 없이 컴파일 성공)
=== -Xjsr305=warn ===
qual/UseC.kt:4:12: warning: Java type mismatch: inferred type is 'Nothing?', but 'String' was expected.
    C.take(null)
           ^^^^
=== -Xjsr305=strict ===
qual/UseC.kt:4:12: error: null cannot be a value of a non-null type 'String'.
    C.take(null)
           ^^^^
```

```text
   -Xjsr305=  │ ignore      │ warn (기본)  │ strict
   ───────────┼─────────────┼──────────────┼──────────────
   결과        │ 아무 말 없음 │ 경고         │ 에러
   타입        │ String!     │ String!      │ String
```

- ★ **`-Xjsr305` 는 「커스텀 기본값 애너테이션」(`@TypeQualifierDefault`·`@TypeQualifierNickname`)만 다룬다.**\
  평범한 `@Nullable`/`@Nonnull` 은 (5)②에서 본 대로 **플래그와 무관하게 항상 오류**다.
- **플래그를 안 주면 `warn` 이다** — `none` 과 `warn` 의 출력이 같다.
- ★ **`ignore` 가 가장 위험하다** — **경고조차 안 나온다.** 무효한 것이 조용히 통과한다.
- JSpecify 의 `@NullMarked` 도 같은 종류의 "기본값" 이다 — `-Xjsr305=ignore` 를 주면\
  `D.take(null)` 의 에러가 **사라지고** `@Nullable` 쪽 에러만 남았다(실측).

비용 — 컴파일 타임만.

### (7) ★★ 「Kotlin 은 NPE 가 없다」가 거짓인 자리 — 여섯을 전부 터뜨렸다

**언제 쓰나** — 이 사슬(03 → 04 → 05)의 결론을 한 화면에 담을 때.

**출력** (`npe/NpeK.kt` · `npe/JList.java`)

```text
--- 1. !! ---
   java.lang.NullPointerException: null
--- 2. 플랫폼 타입 ---
   java.lang.NullPointerException: Cannot invoke "String.length()" because "b" is null
--- 3. lateinit 초기화 전 접근 ---
   kotlin.UninitializedPropertyAccessException: lateinit property name has not been initialized
   isInitialized = false
--- 4. 초기화 중 열린 멤버 접근 (leaking this) ---
   init 에서 v.length = NullPointerException
--- 5. 명시적 throw ---
   java.lang.NullPointerException: 직접 던졌다
--- 6. Java 가 MutableList<String> 에 null 을 넣는다 ---
   원소 길이 = 1
Java 가 null 을 넣은 리스트 -> java.lang.NullPointerException: Cannot invoke "String.length()" because "s" is null
```

| # | 경로 | 예외 | 막는 법 |
|---|---|---|---|
| 1 | **`!!`** | `NullPointerException` (**message 없음**) | 안 쓴다([03번](../03-null-safe-types/)) |
| 2 | **플랫폼 타입** | JVM helpful NPE | 경계에서 타입을 적는다 (이 문서) |
| 3 | **`lateinit` 초기화 전** | ★ **`UninitializedPropertyAccessException`** — **NPE 가 아니다** | `isInitialized` 로 확인 |
| 4 | **초기화 중 열린 멤버 접근** | NPE — **`String` 타입이 `null` 을 들고 있다** | 생성자에서 `open` 멤버를 안 부른다 |
| 5 | **명시적 `throw`** | 내가 던진 것 | — |
| 6 | **Java 가 컬렉션에 `null` 을 넣음** | JVM helpful NPE | 경계에서 복사·검증 |

★ **3번이 목록에서 자주 잘못 적히는 자리다** — `lateinit` 은 **NPE 를 안 던진다.**\
`kotlin.UninitializedPropertyAccessException` 이라는 **Kotlin 전용 예외**다. 메시지에 프로퍼티 이름이 들어 있다.

★ **4번이 가장 무섭다** — 자세히 보면 이렇다.

```kotlin
open class Base { open val v: String = "기본"; init { println(peek()) } ; open fun peek(): String? = v }
class Derived : Base() { override val v: String = "파생"; override fun peek(): String? = v }
```

**출력** (`leak.kt`)

```text
--- 초기화 중 오버라이드된 non-null 프로퍼티는 null 이다 ---
   Base.init: v = null
   생성 후:    v = 파생
   v 의 선언 타입은 String (non-null) 인데 init 시점에는 null 이었다
--- 그 값을 non-null 로 쓰면 ---
   java.lang.NullPointerException: Cannot invoke "String.length()" because the return value of "BadBase.getV()" is null
```

- ★ **`val v: String` 은 non-null 타입인데 `null` 을 들고 있다.** 타입이 거짓말을 한다.
- ★ **kotlinc 는 경고 한 줄도 안 낸다** — `-Werror` 를 줘도 조용히 컴파일된다(실측).\
  **언어도 컴파일러도 막지 않는 유일한 자리**다.

```text
   new Derived()
      │
      ├─ Base 의 생성자 시작
      │     v 필드 = "기본"        (Base 의 초기화)
      │     init { peek() }        ← 가상 호출 -> Derived.peek()
      │          Derived.v 는 아직 대입 전 -> null ★
      │
      └─ Derived 의 생성자
            v 필드 = "파생"        (여기서야 대입된다)
```

비용 — 없다. **비용이 아니라 이 자리를 아느냐 모르느냐의 문제다.**

## 문법 — 형태와 규칙

이 주제에는 **새로 배울 문법이 없다.** `String!` 은 못 적기 때문이다.\
대신 **경계에서 무엇을 적을 것인가**가 전부다.

```kotlin
// 나쁜 형태 — 타입을 안 적는다
val name = row.getString("name")      // String! — 검사 없음
process(name)                          // 여기까지 그냥 흘러간다

// 좋은 형태 1 — 없을 수 있다고 인정한다
val name: String? = row.getString("name")
val safe = name ?: return

// 좋은 형태 2 — 없으면 안 된다고 선언한다 (즉시 터진다)
val name: String = row.getString("name")   // checkNotNullExpressionValue 가 심긴다

// 좋은 형태 3 — 메시지를 남긴다
val name = requireNotNull(row.getString("name")) { "name 컬럼이 비어 있다" }
```

규칙 불릿.

- **플랫폼 타입은 변수·파라미터·반환 타입 어디에도 못 적는다.** 유일한 관찰 수단은 (1)의 에러 짜내기다.
- **타입을 적는 순간 검사가 생긴다.** 안 적으면 안 생긴다 — 이것이 전부다.
- Java 쪽을 고칠 수 있으면 **애너테이션이 최선**이다((5)). 특히 `@NullMarked`(JSpecify)는 클래스 전체를 덮는다.
- Java 쪽을 못 고치면 **Kotlin 경계에서 한 번에 벗긴다.** 안쪽으로 플랫폼 값을 들이지 않는다.

## 어디서 틀리나

| 틀리는 형태 | 무슨 일이 일어나나 | 고치는 법 |
|---|---|---|
| `val x = javaCall()` | 검사가 **하나도** 안 생긴다. 바이트코드가 Java 와 같다 | 타입을 적는다 |
| 플랫폼 값을 그대로 안쪽으로 전달 | NPE 가 **경계에서 먼 곳**에서 난다 | 경계에서 벗긴다 |
| `MutableList<String?>` 에 담기 | `null` 이 컬렉션에 **조용히** 들어간다 | `filterNotNull()` 또는 원소 타입을 `String` 으로 |
| "Kotlin 이니까 NPE 안 난다" | 여섯 경로가 있다((7)) | 경로별로 다른 방어 |
| `lateinit` 을 NPE 로 예상 | `UninitializedPropertyAccessException` 이다 | 잡을 때 타입을 맞춘다 |
| 생성자에서 `open` 멤버 호출 | non-null 프로퍼티가 `null` 이다. **경고도 없다** | 생성자에서 가상 호출을 안 한다 |
| `-Xjsr305=ignore` | 경고조차 사라진다 | `strict` 를 쓰거나 최소한 기본값(`warn`)을 둔다 |
| `@Nullable` 을 "문서" 로 생각 | Kotlin 에서는 **타입이 바뀐다** | 붙이면 컴파일이 깨질 수 있음을 안다 |
| `-Xno-call-assertions` 로 성능 튜닝 | (3)의 검사가 사라져 **더 나중에 더 나쁜 메시지로** 터진다 | 하지 않는다 |

## 구현 세부사항 대 언어 보장

| 사실 | 누가 보장하나 | 근거 |
|---|---|---|
| Java 타입은 플랫폼 타입이 된다 | **언어**(Kotlin/JVM) | 명세 + `actual 'String!'` |
| 플랫폼 타입은 소스에 못 적는다 | **언어** | `syntax error: Unexpected token.` |
| non-null 타입을 적으면 검사가 생긴다 | **언어** | 명세 + 실측 |
| `@Nullable`/`@NotNull` 이 타입을 바꾼다 | **언어** | 실측 3종 |
| JSpecify 위반이 오류다 | **언어**(2.1.0 부터) | 실측 |
| **`checkNotNullExpressionValue` 라는 이름** | **구현** | `javap` |
| **`giveNull(...) must not be null` 문구** | **구현** | 실행 |
| **그 검사가 `astore` 보다 먼저인 것** | **구현** | `javap` |
| **`inferred()` 에 검사가 없는 것** | **구현** | `javap` — `-Xno-call-assertions` 와 같은 결과 |
| **A 의 NPE 메시지** | **JVM 구현** | helpful NPE (JDK 14+, 15부터 기본) |
| **`-Xjsr305` 의 기본값이 `warn` 인 것** | **구현** | 실측 — `none` 과 `warn` 출력이 같다 |
| **초기화 중 접근에 경고가 없는 것** | **구현** | `-Werror` 로도 조용하다 |

★ **이 주제에서 가장 중요한 구분** — **"Kotlin 이 null 을 막는다" 는 언어 보장이 아니라 「내가 타입을 적은 자리에 한한 보장」이다.**\
플랫폼 타입 구간에는 **언어가 약속한 것이 없다.** 공식 문서도 그렇게 적는다 —\
*"Kotlin does not issue nullability errors at compile time, but the call may fail at runtime."*

## 언제 쓰고 언제 안 쓰나

| 상황 | 하는 것 | 왜 |
|---|---|---|
| Java 라이브러리를 부를 때 | **경계에서 타입을 적는다** | 안 적으면 검사가 아예 없다 |
| 값이 정말 없을 수 있을 때 | `String?` 로 받고 `?:` 로 처리 | 안 터진다 |
| 값이 없으면 버그일 때 | `String` 으로 받는다 | 경계에서 즉시 터진다 |
| 메시지가 필요할 때 | `requireNotNull(x) { "…" }` | `giveNull(...) must not be null` 보다 낫다 |
| 우리 팀 Java 코드일 때 | **JSpecify `@NullMarked`** | 클래스 전체의 기본값을 뒤집는다 |
| 남의 Java 라이브러리일 때 | 경계 래퍼를 하나 만든다 | 한 자리에서만 벗긴다 |
| 컬렉션을 받을 때 | 원소 타입을 정하고 필요하면 복사 | Java 는 `null` 원소를 넣을 수 있다 |
| 성능 때문에 검사를 끄고 싶을 때 | **안 끈다** | 잃는 것은 비용이 아니라 실패한다는 사실 |

판단 규칙 두 줄.

- **`val x = javaCall()` 을 보면 타입이 비어 있는 것을 「미결정」으로 읽는다.** 그 줄에서 결정한다.
- **경계는 한 곳이어야 한다.** 플랫폼 값이 두 번째 파일까지 흘러갔으면 이미 진 것이다.

## 핵심 문장

- 플랫폼 타입은 **`String!`** 이라 불리고 **소스에 못 적는다.** 관찰하려면 **일부러 타입 불일치를 내서 `actual` 을 읽는다.**
- **어디서 터지느냐는 Java 가 아니라 내가 타입을 적은 자리가 정한다** — 안 적으면 쓰는 줄(JVM NPE), 적으면 그 줄(Kotlin NPE).
- `inferred()` 의 바이트코드에는 **검사가 하나도 없다.** Java 로 쓴 것과 같다.
- 검사는 대입만이 아니라 **non-null 타입이 적힌 모든 자리**(함수 인자·제네릭 인자)에 생긴다.
- `@Nullable`/`@NotNull` 은 문서가 아니라 **타입을 바꾸는 선언**이다. JSpecify `@NullMarked` 는 클래스 전체를 덮는다.
- **`-Xjsr305` 는 커스텀 기본값 애너테이션만 다룬다.** 평범한 `@Nullable` 은 플래그와 무관하게 항상 오류다.
- 「Kotlin 은 NPE 가 없다」가 거짓인 자리는 여섯이고, 그중 **`lateinit` 은 NPE 조차 아니며**,\
  **초기화 중 접근은 경고도 안 나온다.**

## 관련 자료

- [`../README.md`](../README.md) — Kotlin 문법·API 주제 목록(이 주제는 05번)
- [03번 주제](../03-null-safe-types/) — **`?`·`?.`·`?:`·`!!` 문법의 정본.** 거기의 `checkNotNullParameter` 와 여기의 `checkNotNullExpressionValue` 는 **방향이 반대인 두 검사**다
- [04번 주제](../04-smart-casts/) — **컴파일러가 좁혀 주는 범위의 정본.** 거기서 아홉 자리를 막아 주는 그 방어가 **여기서는 아예 안 걸린다**
- [01번 주제](../01-val-var-and-basic-types/) — `Int`/`Int?` 의 런타임 표현. 플랫폼 타입의 `Int!` 도 같은 문제를 갖는다
- [`../../언어-특성/README.md`](../../언어-특성/README.md) §2·§9 — **「그래서 이 언어를 고를 것인가」라는 설계 논증이 거기 정본.** 상호운용의 실제 비용·Spring 맥락도 거기
- [`../../../java/syntax/60-null-handling/`](../../../java/syntax/60-null-handling/) — **Java 쪽 정본.** 방어 시점 셋, `@NonNull` 이 런타임에 아무것도 안 막는다는 실측
- [`../../../java/syntax/38-optional/`](../../../java/syntax/38-optional/) — Java 가 **런타임 객체**로 푼 쪽
- [`../../../java/syntax/06-initialization-order/`](../../../java/syntax/06-initialization-order/) — (7)의 4번(초기화 중 접근)이 **Java 에서도 같은 문제**라는 것의 정본
- [목록의 **16번 주제**](../16-properties-backing-field-lateinit-const/)(`lateinit`·`const`·backing field) — `lateinit` 의 정본
- [목록의 **19번 주제**](../19-inheritance-open-final-override/)(`open`/`final` 기본값) — 초기화 중 가상 호출이 가능한 이유
- [목록의 **39번 주제**](../39-java-interop-annotations/)(Java 상호운용 애너테이션) — 반대 방향(Kotlin → Java)의 상호운용

## 용어 풀이

- **플랫폼 타입(platform type)** — Java 에서 온, nullability 를 알 수 없는 타입. `String!` 로 표시되고 소스에 못 적는다.
- **비표기 타입(non-denotable type)** — 컴파일러는 아는데 소스에 이름으로 적을 수 없는 타입.
- **`checkNotNullExpressionValue`** — 플랫폼 값이 non-null 자리로 건너갈 때 컴파일러가 심는 런타임 검사.
- **helpful NullPointerException** — NPE 메시지에 "어느 식이 `null` 이었는지" 를 적어 주는 JVM 기능. **JDK 14 도입, 15 부터 기본.**
- **`@Nullable` / `@NotNull`** — Java 선언에 nullability 를 적는 애너테이션. Kotlin 에서는 **타입이 바뀐다.**
- **JSR-305** — `javax.annotation` 패키지의 애너테이션 표준(안). 평범한 것과 **기본값 지정용**이 나뉜다.
- **`@TypeQualifierDefault`** — 클래스·패키지 전체의 기본 nullability 를 정하는 메타 애너테이션. **`-Xjsr305` 가 다루는 대상.**
- **JSpecify** — nullability 애너테이션의 새 표준. `@NullMarked` 로 범위 전체의 기본을 non-null 로 뒤집는다.
- **`-Xjsr305`** — 커스텀 기본값 애너테이션을 어떻게 다룰지 정하는 kotlinc 플래그. `ignore`/`warn`(기본)/`strict`.
- **`lateinit`** — 나중에 대입하겠다고 선언하는 `var`. 대입 전에 읽으면 **`UninitializedPropertyAccessException`.**
- **leaking this** — 생성 중인 객체를 밖으로(또는 가상 호출로) 노출해 **아직 초기화 안 된 상태**가 보이게 하는 것.

---

## 더 들어가면

- 플랫폼 타입은 **타입 인자에도 번진다.** (1)의 짜내기 기법으로 확인했다.

```text
probe2.kt:3:16: error: initializer type mismatch: expected 'Int', actual '(Mutable)List<String!>!'.
    val x: Int = l          // 타입을 실토하게 한다
               ^
probe2.kt:4:16: error: initializer type mismatch: expected 'Int', actual 'String!'.
    val y: Int = l[0]
               ^
```

  ★ Java 의 `List<String>` 은 Kotlin 에서 **`(Mutable)List<String!>!`** 이다 — **`!` 가 두 군데**다.\
  컬렉션 자체도 플랫폼이고 **원소 하나하나도 플랫폼**이다. 그래서 `?` 하나로는 못 막는다((4)의 3번이 그 결과다).\
  `(Mutable)` 이라는 표기는 **읽기 전용인지 가변인지도 모른다**는 뜻이다 — 읽기 전용 컬렉션 이야기는\
  [`../../언어-특성/README.md`](../../언어-특성/README.md) §5 가 정본이다.
- `-Xjsr305` 에는 **애너테이션별 지정**도 있다(`-Xjsr305=@org.example.Anno:strict` 꼴).\
  전체를 `strict` 로 올리면 레거시 의존성이 깨지므로 **문제 있는 패키지만 골라 올리는** 쓰임이다(이 문서에서 돌려 보지는 않았다).
- (7)의 4번은 **Java 에도 그대로 있는 문제**다 — 생성자에서 오버라이드된 메서드를 부르면 하위 필드가 아직 기본값이다.\
  다른 점은 **Kotlin 이 "그 필드는 `null` 일 수 없다" 고 타입으로 약속해 놓고 그 약속을 깬다**는 것이다.\
  정본은 [`../../../java/syntax/06-initialization-order/`](../../../java/syntax/06-initialization-order/).
- `Intrinsics` 에는 옛 이름의 검사도 남아 있다 — `checkExpressionValueIsNotNull`·`checkParameterIsNotNull`.\
  1.4 이전에 컴파일된 코드가 부르던 것이고, **stdlib 는 옛 바이너리를 위해 계속 들고 있다**([03번](../03-null-safe-types/)의 「더 들어가면」에 전수 출력이 있다).
- 이 사슬의 요약 한 줄 — **[03번](../03-null-safe-types/)이 문을 만들고, [04번](../04-smart-casts/)이 문을 자동으로 열어 주며,\
  05번은 그 문이 아예 없는 구간이다.** 셋을 따로 외우면 "왜 Kotlin 에서 NPE 가 나지" 를 못 푼다.
