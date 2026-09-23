# kotlin/syntax/05 — 플랫폼 타입: Java 경계에서 null 보장이 사라지는 것 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 선행은 [03번](../03-null-safe-types/)·[04번](../04-smart-casts/)이다. **이 셋이 한 사슬이고 여기가 정점이다.**
> ★ **문항 11개 중 코드블록이 붙는 예측형이 7개로 상한(6개)을 하나 넘는다.**
> 이 주제는 독립 실패 모드가 그만큼이기 때문이다 — 플랫폼 타입 **관찰**(1) · **터지는 자리**(2) ·
> **바이트코드**(3) · **흘러가는 범위**(4) · **애너테이션 세 종류**(5) · **`-Xjsr305` 의 대상**(6) ·
> **NPE 여섯 경로**(7). 묶으면 복합 문항이 되어 어디서 틀렸는지 못 가린다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★ 소스에 못 적는 타입을 어떻게 관찰하는가 (예측)

```kotlin
// Java: public static String giveNull() { return null; }
fun probe() {
    val a = J.giveNull()
    val x: Int = a                   // [A] 일부러 틀린 타입을 적는다
}
fun probe2() {
    val b: String! = J.giveNull()    // [B] 적을 수 있나?
}
```

- `[A]` 의 에러 메시지에서 `actual` 로 적히는 타입은 무엇인가?
- `[B]` 는 어떤 에러가 나는가?
- 그래서 플랫폼 타입을 확인하는 방법을 한 문장으로 말하면 무엇인가?
- IDE 없이 `kotlinc` 만으로 확인할 수 있는가?

### 2. ★★ 이 셋은 각각 어디서 터지는가 (예측)

```kotlin
// A
val a = J.giveNull()
println(a.length)

// B
val b: String = J.giveNull()

// C
val c: String? = J.giveNull()
println(c?.length)
```

- 셋 중 예외가 나는 것은 무엇이고, **대입하는 줄인가 쓰는 줄인가**?
- 각 예외의 메시지는 무엇인가?
- **A 와 B 의 메시지를 누가 만들었는가** — 같은 쪽인가 다른 쪽인가?
- 「어디서 터지나」를 정하는 것은 Java 인가 나인가?

### 3. ★★ 바이트코드에는 무엇이 들어 있는가 (예측)

```kotlin
fun inferred(): Int = J.giveNull().length
fun declared(): Int { val b: String = J.giveNull(); return b.length }
fun optional(): Int? { val c: String? = J.giveNull(); return c?.length }
```

- 셋의 `javap -c` 출력에서 각각 몇 개의 명령이 보이는가?
- `inferred()` 에 검사가 있는가?
- `declared()` 의 검사는 `astore`(대입) 앞인가 뒤인가 — 그것이 2번의 답과 어떻게 맞는가?
- 검사 함수 이름은 무엇이고, [03번](../03-null-safe-types/)의 것과 어떻게 다른가?

### 4. ★★ 타입을 안 적으면 그 값은 어디까지 흘러가는가 (예측)

```kotlin
J.giveNull().length                              // [1]
val list: MutableList<String> = mutableListOf()
list.add(J.giveNull())                           // [2]
val list2: MutableList<String?> = mutableListOf()
list2.add(J.giveNull())                          // [3]
need(J.giveNull())        // fun need(s: String): Int      // [4]
needNullable(J.giveNull())// fun needNullable(s: String?)  // [5]
```

- 다섯 중 예외가 나는 것은 무엇이고 각각 어느 줄에서인가?
- 검사가 생기는 자리를 한 문장으로 말하면 무엇인가 — "대입" 이 맞는 표현인가?
- `[3]` 은 통과한다. 그 결과 무엇이 어디에 남는가?
- 다섯 중 가장 늦게 발견될 사고는 무엇인가?

### 5. ★★ 애너테이션 세 종류는 각각 무엇을 바꾸는가 (예측)

```java
// ① org.jetbrains.annotations
public static @Nullable String maybeNull()   { return null; }
public static @NotNull  String neverNull()   { return "값"; }
public static          String noAnnotation() { return null; }

// ③ org.jspecify.annotations
@NullMarked public class D {
    public static String give() { return "값"; }
    public static @Nullable String maybe() { return null; }
    public static void take(String s) { }
}
```

- ①에서 `val s: String = A.maybeNull()` 은 통과하는가? 에러 메시지의 `actual` 은 무엇인가?
- ①에서 `A.noAnnotation()` 은 어떻게 되는가?
- ③의 `@NullMarked` 는 무엇을 뒤집는가 — `D.take(null)` 은 통과하는가?
- JSpecify 위반이 **경고가 아니라 오류**가 된 것은 어느 버전부터인가?

### 6. ★★ `-Xjsr305` 는 정확히 무엇을 하는가 (예측)

```java
// ② 평범한 JSR-305
public static @Nullable String maybeNull() { return null; }

// ⑥ @TypeQualifierDefault 로 만든 기본값
@Nonnull @TypeQualifierDefault({METHOD, PARAMETER}) public @interface NonNullApi {}
@NonNullApi public class C { public static void take(String s) { } }
```

- ②를 `-Xjsr305` 의 네 조건(없음/`ignore`/`warn`/`strict`)에서 컴파일하면 결과가 달라지는가?
- ⑥의 `C.take(null)` 을 같은 네 조건에서 컴파일하면 각각 무엇이 나오는가?
- 플래그를 안 줬을 때의 기본값은 무엇인가 — 무엇으로 확인했는가?
- 네 조건 중 가장 위험한 것은 무엇이고 왜인가?

### 7. ★★ 「Kotlin 은 NPE 가 없다」가 거짓인 자리를 전부 대라 (예측)

```kotlin
val a: String? = null; a!!.length                        // [1]
val b = J.giveNull(); b.length                           // [2]
class Late { lateinit var name: String }; Late().name    // [3]
open class BadBase { open val v: String = "기본"; init { v.length } }
class Bad : BadBase() { override val v: String = "파생" }; Bad()   // [4]
throw NullPointerException("직접 던졌다")                   // [5]
// Java 가 MutableList<String> 에 null 을 넣고 Kotlin 이 순회        // [6]
```

- 여섯의 예외 클래스와 메시지는 각각 무엇인가?
- 여섯 중 **NPE 가 아닌 것**은 무엇인가?
- `[4]` 에서 `v` 의 선언 타입은 무엇이고 그 시점의 값은 무엇인가?
- `[4]` 에 컴파일러 경고가 붙는가 — `-Werror` 를 줘도 그런가?

### 8. 이 주제에서 "언어 보장" 은 어디까지인가 (경계)

- "Java 타입은 플랫폼 타입이 된다" 는 어느 쪽인가?
- "`checkNotNullExpressionValue` 가 `astore` 앞에 온다" 는 어느 쪽인가?
- 공식 문서는 플랫폼 타입에 대해 **무엇을 하지 않는다**고 적는가?
- "Kotlin 이 null 을 막는다" 는 문장을 정확히 고쳐 쓰면 무엇인가?

### 9. 경계에서 무엇을 하는가 (왜)

- 값이 정말 없을 수 있을 때와 없으면 버그일 때, 각각 무엇을 적는가?
- 메시지를 남기려면 무엇을 쓰는가?
- 우리 팀 Java 코드라면 무엇을 붙이는 것이 최선인가?
- 경계가 두 곳 이상으로 퍼지면 무엇이 문제인가?

### 10. 플랫폼 타입은 타입 인자에도 번지는가 (경계)

- Java 의 `List<String>` 은 Kotlin 에서 정확히 어떤 타입인가?
- `!` 가 몇 군데 붙는가?
- `(Mutable)` 이라는 표기는 무엇을 뜻하는가?
- 그래서 `?` 하나로 막을 수 있는가?

### 11. 이 사슬(03 → 04 → 05)을 한 문장으로 잇기 (연결)

- [03번](../03-null-safe-types/)의 `checkNotNullParameter` 와 이 주제의 `checkNotNullExpressionValue` 는 무엇이 다른가?
- [04번](../04-smart-casts/)이 아홉 자리에서 막아 주는 방어가 이 주제에서는 왜 안 걸리는가?
- 세 주제를 한 문장으로 이으면 무엇인가?
- Java 쪽에서 같은 문제를 어떻게 다루는지의 정본은 어디인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
