# kotlin/syntax/05 — 플랫폼 타입: Java 경계에서 null 보장이 사라지는 것 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 모든 출력·에러·바이트코드는 **kotlinc 2.4.20 (JRE 21.0.5)** 과 Temurin **JDK 21.0.5** 에서 실제로 얻었다.\
> Java 는 같은 JDK 의 `javac` 로 컴파일해 **한 클래스패스에 섞어 돌렸다.**\
> 애너테이션 실험에 쓴 jar — `annotations-13.0.jar`(kotlinc 동봉) · `jsr305-3.0.2.jar` · `jspecify-1.0.0.jar`.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★ 소스에 못 적는 타입을 어떻게 관찰하는가

**출력** (`kotlinc pt.kt -cp out`)

```text
pt.kt:3:16: error: initializer type mismatch: expected 'Int', actual 'String!'.
    val x: Int = a            // 일부러 틀린 타입을 적는다
               ^
pt.kt:6:18: error: syntax error: Unexpected token.
    val b: String! = J.giveNull()   // 적을 수 있나?
                 ^
```

**왜 그런가**

- `[A]` 의 `actual` 은 **`String!`** 이다. 컴파일러는 이 타입에 이름을 가지고 있다.
- `[B]` 는 **`syntax error: Unexpected token.`** — `!` 에서 파서가 멈춘다.\
  **에러가 타입 에러가 아니라 문법 에러**라는 점이 중요하다. `String!` 은 **언어의 문법에 없다.**
- 방법 한 문장 — **일부러 맞지 않는 타입을 적어 컴파일러가 `actual` 로 실토하게 한다.**\
  비표기 타입은 전부 이렇게 본다.
- **IDE 없이 `kotlinc` 하나로 확인된다.** IDE 가 `String!` 을 보여 주는 것과 같은 정보다.

### 2. ★★ 이 셋은 각각 어디서 터지는가

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

**왜 그런가**

| | 어디서 | 누가 던지나 | 메시지 |
|---|---|---|---|
| A | **쓰는 줄** | **JVM** (helpful NPE) | `Cannot invoke "String.length()" because "a" is null` |
| B | **대입하는 줄** | **Kotlin** | `giveNull(...) must not be null` |
| C | 안 터진다 | — | — |

```text
   A. 타입 안 적음               B. String 적음              C. String? 적음
   +---------------------+      +---------------------+     +---------------------+
   | val a = giveNull()  |      | val b: String = …   |     | val c: String? = …  |
   |   대입 통과 ★        |      |   ★ 여기서 터진다    |     |   대입 통과         |
   |   a = null          |      |                     |     |   c = null          |
   | a.length            |      |                     |     | c?.length -> null   |
   |   ★ 여기서 터진다    |      |                     |     |   안 터진다          |
   +---------------------+      +---------------------+     +---------------------+
```

- ★ **A 와 B 의 메시지는 다른 쪽이 만들었다.**\
  A 는 **JVM 의 helpful NullPointerException**(JDK 14 도입, 15부터 기본) — 즉 **Kotlin 은 아무것도 안 넣었다.**\
  B 는 **Kotlin 이 심은 검사**다. 그래서 **Java 메서드 이름 `giveNull(...)` 이 메시지에 들어 있다.**
- 구별법 — **메시지에 Java 메서드 이름이 있으면 Kotlin 이 잡은 것, `Cannot invoke … because …` 면 JVM 이 잡은 것.**
- ★ **「어디서 터지나」를 정하는 것은 Java 가 아니라 나다.**\
  같은 Java 메서드인데 **내가 `String` 을 적었는지, `String?` 를 적었는지, 아무것도 안 적었는지**에 따라\
  터지는 줄과 메시지가 전부 달라졌다.

### 3. ★★ 바이트코드에는 무엇이 들어 있는가

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

**왜 그런가**

- 명령 수 — `inferred()` **3개**, `declared()` **7개**, `optional()` **10개**.
- ★ **`inferred()` 에는 검사가 없다.** 같은 코드를 Java 로 썼을 때와 **바이트코드가 같다.**\
  "Kotlin 이 null 을 막아 준다" 는 문장이 이 함수에서는 **한 글자도 참이 아니다.**
- ★ **`declared()` 의 검사는 `astore_0`(대입) 앞**에 있다 — `dup` → `ldc` → `checkNotNullExpressionValue` → `astore_0`.\
  **변수에 담기기 전에 터뜨린다.** 그래서 2번 B 에서 "대입에서 터짐" 이 나왔다. **출력과 바이트코드가 맞물린다.**
- `ldc "giveNull(...)"` 로 **Java 메서드 이름이 상수 풀에 박혀 있다.** 메시지가 여기서 나온다.
- 검사 이름이 [03번](../03-null-safe-types/)의 것과 다르다 — **방향이 반대**다.

| 검사 | 막는 방향 | 정본 |
|---|---|---|
| `checkNotNullParameter` | **Java → Kotlin (들어오는 인자)** | [03번](../03-null-safe-types/) |
| `checkNotNullExpressionValue` | **Java → Kotlin (나오는 반환값)** | **여기** |

- 그리고 **이 검사도 끌 수 있다** — `-Xno-call-assertions` 를 주면 `declared()` 가 `inferred()` 와 같아진다(실측).\
  [03번](../03-null-safe-types/) 6번과 같은 성질이다 — **방어이지 의미가 아니다.**

### 4. ★★ 타입을 안 적으면 그 값은 어디까지 흘러가는가

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

**왜 그런가**

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

| | 결과 | 어느 줄 |
|---|---|---|
| `[1]` | JVM helpful NPE | 쓰는 줄 |
| `[2]` | Kotlin NPE — `giveNull(...) must not be null` | **`add` 하는 줄** |
| `[3]` | **통과** | — |
| `[4]` | Kotlin NPE — 같은 문구 | **호출하는 줄** |
| `[5]` | **통과**, `-1` | — |

- ★ **"대입" 은 맞는 표현이 아니다.** 검사가 생기는 자리를 정확히 적으면 —\
  **플랫폼 값이 「non-null 타입이 적힌 자리」로 건너가는 모든 지점**이다.\
  변수 선언뿐 아니라 **함수 인자(`[4]`)와 제네릭 타입 인자(`[2]`)** 가 전부 그 자리다.
- 그런 자리를 한 번도 안 만나면 **끝까지 안 걸린다**(`[1]`).
- ★ **가장 늦게 발견될 사고는 `[3]`** 이다 — **예외가 안 난다.**\
  `MutableList<String?>` 에 `null` 이 조용히 담기고, 나중에 그 리스트를 순회하는 **완전히 다른 코드**에서 터진다.\
  스택 트레이스에 Java 쪽 흔적이 하나도 안 남는다.
- 실무 규칙 — **경계에서 벗긴다.** 플랫폼 값이 두 번째 파일까지 흘러갔으면 이미 진 것이다.

### 5. ★★ 애너테이션 세 종류는 각각 무엇을 바꾸는가

**출력 ①** (`kotlinc ann/UseA.kt -cp "outann:annotations-13.0.jar"`)

```text
ann/UseA.kt:2:19: error: initializer type mismatch: expected 'String', actual 'String?'.
    val s: String = A.maybeNull()      // @Nullable -> String? 이므로 거부되어야 한다
                  ^
ann/UseA.kt:14:26: error: only safe (?.) or non-null asserted (!!.) calls are allowed on a nullable receiver of type 'String?'.
    println(A.maybeNull().length)      // @Nullable 에 직접 . 호출
                         ^
```

**출력 ③** (`kotlinc spec/UseD.kt -cp "outs:jspecify-1.0.0.jar"`)

```text
spec/UseD.kt:4:19: error: initializer type mismatch: expected 'String', actual 'String?'.
    val b: String = D.maybe()      // @Nullable -> 거부되어야 한다
                  ^
spec/UseD.kt:6:12: error: null cannot be a value of a non-null type 'String'.
    D.take(null)                   // non-null 파라미터에 null -> 거부
           ^^^^
```

**왜 그런가**

| Java 선언 | Kotlin 에서의 타입 | `val s: String = …` |
|---|---|---|
| `@Nullable String` | **`String?`** | **에러** |
| `@NotNull String` | `String` | 통과 |
| 애너테이션 없음 | **`String!`** (플랫폼) | **통과 — 검사만 심긴다** |

- ①의 `actual 'String?'` 가 결정적이다 — **1번에서 짜냈던 `String!` 이 사라지고 `String?` 가 됐다.**\
  **애너테이션이 타입을 바꾼 것**이지 문서를 단 게 아니다.
- `A.noAnnotation()` 은 `null` 을 돌려주는데도 **`val s: String` 에 그냥 들어간다**(컴파일 통과).\
  플랫폼 타입이기 때문이다 — 대신 3번의 검사가 심겨 **런타임에** 터진다.
- ③의 `@NullMarked` 는 **그 클래스 전체의 기본값을 non-null 로 뒤집는다.**\
  `val a: String = D.give()` 는 **통과했고**(기본이 non-null), `D.take(null)` 은 **에러**다.\
  플랫폼 타입이 그 클래스 표면에서 **통째로 사라진다.**
- **JSpecify 위반이 경고가 아니라 오류가 된 것은 Kotlin 2.1.0 부터**다.
- 실무 결론 — **우리 팀 Java 코드에는 `@NullMarked` 하나가 애너테이션 수십 개보다 낫다.**

### 6. ★★ `-Xjsr305` 는 정확히 무엇을 하는가

**출력 ②** (평범한 `@Nullable` — 네 조건)

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

**출력 ⑥** (`@TypeQualifierDefault` 로 만든 기본값 — 같은 네 조건)

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

**왜 그런가**

```text
   -Xjsr305=  │ (없음)      │ ignore      │ warn        │ strict
   ───────────┼─────────────┼─────────────┼─────────────┼──────────────
   ② 평범한   │ 에러        │ 에러        │ 에러        │ 에러      ★ 안 바뀐다
     @Nullable│             │             │             │
   ⑥ 기본값   │ 경고        │ 아무 말 없음 │ 경고        │ 에러      ★ 이것을 다룬다
     애너테이션│             │             │             │
```

- ★ **②는 네 조건에서 결과가 한 글자도 안 바뀐다.** **평범한 `@Nullable`/`@Nonnull` 은 항상 지켜진다.**\
  이것이 이 실험의 값어치다 — 플래그 이름만 보고 "JSR-305 전체를 켜고 끄는 것" 이라고 읽으면 **틀린다.**
- ★ **`-Xjsr305` 가 다루는 것은 `@TypeQualifierDefault`·`@TypeQualifierNickname` 으로 만든 「기본값 애너테이션」뿐**이다.
- **기본값은 `warn`** 이다 — 플래그를 안 줬을 때와 `-Xjsr305=warn` 의 출력이 **한 글자도 같다.**\
  이것이 기본값을 확인한 방법이다(문서를 읽은 게 아니라 **출력을 맞춰 봤다**).
- ★ **가장 위험한 것은 `ignore`** 다. **경고조차 안 나온다.**\
  `strict` 는 에러라 눈에 띄고 `warn` 은 경고라도 남는데, `ignore` 는 **아무 흔적이 없다.**\
  빌드 스크립트에서 이 값을 보면 "왜 껐는지" 를 물어야 한다.
- JSpecify 의 `@NullMarked` 도 같은 종류의 "기본값" 이다 — `-Xjsr305=ignore` 를 주면\
  `D.take(null)` 의 에러가 **사라지고** `@Nullable` 쪽 에러만 남았다(실측).

### 7. ★★ 「Kotlin 은 NPE 가 없다」가 거짓인 자리를 전부 대라

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

**왜 그런가**

| # | 경로 | 예외 | 메시지 |
|---|---|---|---|
| 1 | `!!` | `java.lang.NullPointerException` | **없음**(`null`) |
| 2 | 플랫폼 타입 | `java.lang.NullPointerException` | JVM helpful NPE |
| 3 | `lateinit` | ★ **`kotlin.UninitializedPropertyAccessException`** | `lateinit property name has not been initialized` |
| 4 | 초기화 중 접근 | `java.lang.NullPointerException` | JVM helpful NPE |
| 5 | 명시적 `throw` | `java.lang.NullPointerException` | 내가 쓴 것 |
| 6 | Java 가 컬렉션에 `null` | `java.lang.NullPointerException` | JVM helpful NPE |

- ★ **NPE 가 아닌 것은 3번이다.** `lateinit` 은 **Kotlin 전용 예외**를 던진다.\
  목록에 "`lateinit` 도 NPE 원인" 이라고 적는 글이 많은데 **클래스가 다르다** — `catch (e: NullPointerException)` 에 안 걸린다.\
  `::name.isInitialized` 로 **미리 확인할 수 있다**(출력의 `isInitialized = false`).
- ★ **4번이 가장 무섭다.** 자세히 보면 이렇다.

**출력** (`leak.kt`)

```text
--- 초기화 중 오버라이드된 non-null 프로퍼티는 null 이다 ---
   Base.init: v = null
   생성 후:    v = 파생
   v 의 선언 타입은 String (non-null) 인데 init 시점에는 null 이었다
--- 그 값을 non-null 로 쓰면 ---
   java.lang.NullPointerException: Cannot invoke "String.length()" because the return value of "BadBase.getV()" is null
```

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

- `v` 의 선언 타입은 **`String`(non-null)** 인데 그 시점의 값은 **`null`** 이다. **타입이 거짓말을 한다.**
- ★ **컴파일러 경고가 한 줄도 안 붙는다** — `-Werror` 를 줘도 조용히 컴파일된다.

```text
$ kotlinc -Werror leak.kt -jvm-target 21 -d outleak3/
(출력 없음)
```

- 즉 **언어도 컴파일러도 막지 않는 유일한 자리**다. 나머지 다섯은 최소한 문법(`!!`·`throw`)이나\
  타입(`lateinit`)으로 "여기가 위험하다" 는 표시가 소스에 남는데, **4번만 아무 표시가 없다.**\
  Java 에도 같은 문제가 있지만 Java 는 **애초에 non-null 을 약속하지 않았다** —\
  정본은 [`../../../java/syntax/06-initialization-order/`](../../../java/syntax/06-initialization-order/).

### 8. 이 주제에서 "언어 보장" 은 어디까지인가

| 사실 | 어느 쪽 | 근거 |
|---|---|---|
| Java 타입은 플랫폼 타입이 된다 | **언어**(Kotlin/JVM) | 명세 + `actual 'String!'` |
| 플랫폼 타입은 소스에 못 적는다 | **언어** | `syntax error: Unexpected token.` |
| non-null 타입을 적으면 검사가 생긴다 | **언어** | 명세 + 실측 |
| `@Nullable`/`@NotNull` 이 타입을 바꾼다 | **언어** | 실측 3종 |
| JSpecify 위반이 오류다 | **언어**(2.1.0 부터) | 실측 |
| **`checkNotNullExpressionValue` 라는 이름** | **구현** | `javap` |
| **`giveNull(...) must not be null` 문구** | **구현** | 실행 |
| **검사가 `astore` 앞에 오는 것** | **구현** | `javap` |
| **`inferred()` 에 검사가 없는 것** | **구현** | `javap` |
| **A 의 NPE 메시지** | **JVM 구현** | helpful NPE (JDK 14+, 15부터 기본) |
| **`-Xjsr305` 의 기본값이 `warn`** | **구현** | 실측 — `none` 과 출력이 같다 |
| **초기화 중 접근에 경고가 없는 것** | **구현** | `-Werror` 로도 조용 |

- 공식 문서가 **하지 않는다**고 적는 것 — *"Kotlin does not issue nullability errors at compile time, but the call may fail at runtime."*\
  즉 **플랫폼 타입 구간에는 컴파일 시점 보장이 없다**고 문서가 스스로 말한다.
- ★ **고쳐 쓴 문장** — "Kotlin 이 null 을 막는다" 가 아니라\
  **"Kotlin 은 내가 타입을 적은 자리에서 null 을 막는다. 안 적은 자리에서는 아무것도 하지 않는다."**
- 설계 논증 쪽 정본은 [`../../언어-특성/README.md`](../../언어-특성/README.md) §2 —\
  "플랫폼 타입은 **검사가 유예된 구간**이고, 검사는 개발자가 타입을 적는 순간 일어난다" 가 같은 말이다.

### 9. 경계에서 무엇을 하는가

```kotlin
// 나쁜 형태 — 타입을 안 적는다
val name = row.getString("name")      // String! — 검사 없음
process(name)                          // 여기까지 그냥 흘러간다

// 값이 정말 없을 수 있을 때
val name: String? = row.getString("name")
val safe = name ?: return

// 값이 없으면 버그일 때
val name: String = row.getString("name")   // 즉시 터진다

// 메시지를 남기고 싶을 때
val name = requireNotNull(row.getString("name")) { "name 컬럼이 비어 있다" }
```

**왜 그런가**

| 상황 | 적는 것 | 얻는 것 |
|---|---|---|
| 정말 없을 수 있다 | `String?` | 안 터지고, 이후 코드가 `?` 를 보고 처리한다 |
| 없으면 버그다 | `String` | 경계에서 즉시 터진다(3번의 검사) |
| 메시지가 필요하다 | `requireNotNull(x) { "…" }` | `giveNull(...) must not be null` 보다 훨씬 낫다 |
| 우리 팀 Java 코드 | **JSpecify `@NullMarked`** | 클래스 전체에서 플랫폼 타입이 사라진다(5번) |

- 경계가 두 곳 이상으로 퍼지면 — **어느 쪽에서 들어온 `null` 인지 못 가린다.**\
  그리고 4번의 `[3]` 처럼 **예외조차 안 나는 경로**가 생기면 추적이 불가능해진다.
- Java 쪽의 같은 문제 의식(방어 시점 셋)은 [`../../../java/syntax/60-null-handling/`](../../../java/syntax/60-null-handling/) 가 정본이다.

### 10. 플랫폼 타입은 타입 인자에도 번지는가

**출력** (`kotlinc probe2.kt -cp outjl` — 1번의 짜내기 기법)

```text
probe2.kt:3:16: error: initializer type mismatch: expected 'Int', actual '(Mutable)List<String!>!'.
    val x: Int = l          // 타입을 실토하게 한다
               ^
probe2.kt:4:16: error: initializer type mismatch: expected 'Int', actual 'String!'.
    val y: Int = l[0]
               ^
```

**왜 그런가**

- Java 의 `List<String>` 은 Kotlin 에서 **`(Mutable)List<String!>!`** 이다.
- ★ **`!` 가 두 군데** 붙는다 — **컬렉션 자체도 플랫폼이고 원소 하나하나도 플랫폼**이다.\
  원소를 꺼내면 그것도 `String!` 이다(둘째 에러).
- `(Mutable)` 이라는 표기는 **읽기 전용인지 가변인지도 모른다**는 뜻이다.\
  Kotlin 은 `List`/`MutableList` 를 타입으로 가르는데 **Java 의 `List` 하나로는 어느 쪽인지 결정할 수 없다.**\
  그래서 **nullability 와 가변성 두 가지를 동시에 유예**한다.\
  읽기 전용 컬렉션 이야기는 [`../../언어-특성/README.md`](../../언어-특성/README.md) §5 가 정본이다.
- ★ **그래서 `?` 하나로는 못 막는다.** `val l: List<String>?` 로 받아도 **원소의 `null` 은 그대로 들어온다.**\
  막으려면 `List<String?>` 로 받아 `filterNotNull()` 하거나, 경계에서 원소별로 검증한다.\
  7번의 6번 경로(Java 가 `MutableList<String>` 에 `null` 을 넣은 것)가 바로 이 구멍이다.

### 11. 이 사슬(03 → 04 → 05)을 한 문장으로 잇기

| | 검사 | 막는 방향 | 정본 |
|---|---|---|---|
| 03 | `checkNotNullParameter` | **Java → Kotlin (들어오는 인자)** | [03번](../03-null-safe-types/) |
| 05 | `checkNotNullExpressionValue` | **Java → Kotlin (나오는 반환값)** | 여기 |

- **두 검사는 방향이 반대다.** 03 은 "Java 가 내 함수에 `null` 을 넘기는 것" 을 막고,\
  05 는 "Java 함수가 내게 `null` 을 돌려주는 것" 을 막는다. **국경의 양쪽 문**이다.
- **[04번](../04-smart-casts/)의 방어가 여기서 안 걸리는 이유** —\
  04 는 **"이미 nullable 이라고 인정한 값" 을 좁히려 할 때** 작동한다.\
  플랫폼 타입은 **애초에 nullable 이라고 인정되지 않았으므로** 검사도 스마트 캐스트도 필요 없다.\
  ★ 즉 04 가 아홉 자리에서 깐깐하게 막아 준 그 방어가, 여기서는 **한 자리에서도 안 걸린다.**\
  **깐깐한 것이 안전한 게 아니라, 깐깐할 대상이 있어야 안전하다.**
- ★ **세 주제를 한 문장으로** —\
  **[03번](../03-null-safe-types/)이 `null` 을 타입으로 만들어 문을 세우고,\
  [04번](../04-smart-casts/)이 그 문을 언제 자동으로 열어 줄지를 정하며,\
  05번은 그 문이 아예 서 있지 않은 구간이다.**
- Java 쪽 정본 — [`../../../java/syntax/60-null-handling/`](../../../java/syntax/60-null-handling/)(방어 시점 셋·`requireNonNull`)와\
  [`../../../java/syntax/38-optional/`](../../../java/syntax/38-optional/)(런타임 객체로 푼 쪽).\
  설계 논증은 [`../../언어-특성/README.md`](../../언어-특성/README.md) §2·§9.

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
| `pt.kt` | `actual 'String!'` 과 `String!` 을 못 적는 것 | `kotlinc pt.kt -cp out` (에러가 결과) |
| `J.java` + `K.kt` | **어디서 터지나** A/B/C/D 네 경우 | `javac -d out J.java` → `kotlinc K.kt -cp out -d out/` → `java` |
| `P.kt` | `inferred`/`declared`/`optional` 의 바이트코드 | `javap -c -p outp/PKt.class` |
| `P.kt` (`-Xno-call-assertions`) | 검사가 사라져 `inferred` 와 같아지는 것 | `javap` 한 번 더 |
| `chain.kt` | 플랫폼 값이 컬렉션·파라미터로 흐르는 5경우 | `kotlinc -cp out` → `java` |
| `ann/A.java` + `ann/UseA.kt` | **JetBrains** `@Nullable`/`@NotNull`/무애너테이션 | `javac -cp annotations-13.0.jar` → `kotlinc -cp "outann:annotations-13.0.jar"` |
| `jsr/B.java` + `jsr/UseB.kt` | **JSR-305 평범한 판** — `-Xjsr305` **네 조건** | `kotlinc` 4회 |
| `qual/NonNullApi.java` + `qual/C.java` + `qual/UseC.kt` | **`@TypeQualifierDefault`** — `-Xjsr305` **네 조건** | `kotlinc` 4회 |
| `spec/D.java` + `spec/UseD.kt` | **JSpecify `@NullMarked`** — 기본 · `-Xjsr305=ignore` | `javac -cp jspecify-1.0.0.jar` → `kotlinc` 2회 |
| `npe/NpeK.kt` + `npe/JList.java` | NPE 경로 **여섯 전부** | `kotlinc -cp out` → `javac -cp outnpe` → `java` 2회 |
| `leak.kt` | 초기화 중 non-null 프로퍼티가 `null` 인 것, **경고 없음** | `kotlinc` · `kotlinc -Werror` → `java` |
| `JL.java` + `probe2.kt` | `List<String>` 이 `(Mutable)List<String!>!` 인 것 | `kotlinc -cp outjl` (에러가 결과) |

**구현 의존 항목** — `javap` 의 명령 목록·상수 풀 번호, `checkNotNullExpressionValue` 라는 이름,
`giveNull(...) must not be null` 문구, 검사가 `astore` 앞에 오는 것, JVM helpful NPE 의 문장 형태,
`-Xjsr305` 의 기본값과 경고 문구, `(Mutable)List<String!>!` 라는 표기 — **이 컴파일러·이 JDK 의 산출물**이다.\
반면 "Java 타입은 플랫폼 타입이 된다"·"플랫폼 타입은 소스에 못 적는다"·
"애너테이션이 타입을 바꾼다"·"`@NullMarked` 가 기본값을 뒤집는다" 는 **언어 규칙**이다.

**네 조건을 다 찍은 것** — `-Xjsr305` 는 **두 실험 × 네 조건 = 8회** 컴파일했다.
평범한 `@Nullable` 쪽(②)만 찍었으면 **"이 플래그는 아무것도 안 한다"** 는 틀린 결론을,
`@TypeQualifierDefault` 쪽(⑥)만 찍었으면 **"이 플래그가 JSR-305 전체를 켜고 끈다"** 는 틀린 결론을 냈을 것이다.
**둘을 나란히 찍어야만 경계가 보인다.**

**「없다」도 출력으로 확인한 것** — 7번 4의 경고는 `kotlinc -Werror` 가 **아무것도 출력하지 않는 것**이 근거다.
"경고가 안 나오더라" 가 아니라 **경고를 에러로 승격시켜도 통과한다**는 출력이다.
