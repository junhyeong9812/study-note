# kotlin/syntax/39 — Java 상호운용 애너테이션 — `@JvmStatic`/`@JvmOverloads`/`@JvmName`/`@JvmField`/`@Throws` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 선행은 [25번 주제](../25-object-declaration-companion-and-object-expression/)(`object`·`companion object` 가 JVM 에서 무엇인가)와 [34번 주제](../34-exceptions-nothing-and-try-expression/)(`@Throws`)다.
> 문항 11개 중 예측형은 5개이고, 그중 코드블록이 붙는 것은 4개다.
> 이 주제의 모든 답은 **kotlinc 2.4.20 · Temurin JDK 21.0.5** 에서 실제로 던져 받은 것이다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★★ 애너테이션 없는 판에 Java 10줄 (예측)

```kotlin
// api0.kt
@file:JvmName("Api")

class Box {
    companion object { fun make(): String = "make" }
    val size: Int = 3
    fun greet(a: String, b: Int = 1, c: String = "c"): String = "$a$b$c"
}

object Reg { fun ping(): String = "ping" }

fun original(): String = "orig"
```

```java
// Calls.java
public class Calls {
    static void run() {
        String r1 = Box.make();
        String r2 = Box.Companion.make();
        String r3 = Reg.ping();
        String r4 = Reg.INSTANCE.ping();
        String r5 = new Box().greet("a");
        String r6 = new Box().greet("a", 1, "c");
        int r7 = new Box().size;
        int r8 = new Box().getSize();
        String r9 = Api.renamed();
        String r10 = Api.original();
    }
}
```

- `javac -cp o39a Calls.java` 는 통과하는가? 막히면 **몇 번째 줄들**이 무엇이라고 말하는가?

### 2. ★★★ 같은 Java 10줄을 애너테이션 붙인 판에 (예측)

```kotlin
// api1.kt
@file:JvmName("Api")

class Box {
    companion object { @JvmStatic fun make(): String = "make" }
    @JvmField val size: Int = 3
    @JvmOverloads fun greet(a: String, b: Int = 1, c: String = "c"): String = "$a$b$c"
}

object Reg { @JvmStatic fun ping(): String = "ping" }

@JvmName("renamed") fun original(): String = "orig"
```

- 이번엔 몇 번째 줄이 막히는가? 1번에서 통과했던 줄 중에 막히게 되는 것이 있는가?

### 3. ★★★ 두 판의 `javap -p` (예측)

- 1·2번 두 판의 `Box` · `Box$Companion` · `Reg` · `Api` 를 `javap -p` 로 보면, 애너테이션마다 **무엇이 생기고 무엇이 사라지는가**? 특히 `make()` 와 `ping()` 은 각 판에서 **몇 개**이고 정적인가?

### 4. ★★ 기본값 위치와 오버로드 (예측)

```kotlin
// jov.kt
@JvmOverloads fun tail2(a: String, b: Int = 1, c: String = "c"): String = "$a$b$c"
@JvmOverloads fun all3(a: String = "a", b: Int = 1, c: String = "c"): String = "$a$b$c"
@JvmOverloads fun mid(a: String, b: Int = 1, c: String): String = "$a$b$c"
fun none(a: String, b: Int = 1, c: String = "c"): String = "$a$b$c"
```

```java
// JMid.java
public class JMid {
    public static void main(String[] args) {
        System.out.println(JovKt.mid("a", "z"));
        System.out.println(JovKt.all3());
        System.out.println(JovKt.all3("x", 5));
    }
}
```

- 네 함수는 JVM 에서 각각 **어떤 서명**들이 되는가? `JMid` 는 컴파일되는가 — 돌리면 무엇이 찍히는가?

### 5. ★★ 달 수 없는 자리 (예측)

```kotlin
// bad39.kt
class C1 {
    @JvmField val a: Int get() = 1
    @JvmField private val b: Int = 2
    @JvmStatic fun s(): Int = 3
    @JvmField var c: Int = 4
        set(v) { field = v }
}
open class C2 { @JvmField open val d: Int = 5 }
interface I3 { @JvmOverloads fun f(x: Int = 1): Int }
```

- 에러가 나는 줄은 어디이고 각각 무엇이라고 말하는가?

### 6. 「추가」와 「교체」 (왜)

- 이미 Java 모듈이 쓰는 공개 API 에 `@JvmStatic`·`@JvmOverloads` 를 더하는 것과 `@JvmField`·`@JvmName` 을 더하는 것은 **Java 호출자에게** 무엇이 다른가?

### 7. `Reg.INSTANCE.ping()` 이 붙인 판에서도 통과하는 이유 (왜)

- 붙인 판의 `Reg` 에는 인스턴스 메서드 `ping()` 이 **없다**. 그런데 `Reg.INSTANCE.ping()` 이 컴파일되는 것은 누구의 규칙 때문인가?

### 8. `@JvmOverloads` 문서 문장과 가운데 기본값 (경계)

- 문서는 오버로드마다 「this parameter and all parameters to the right of it … removed」라고 적는다. 4번의 `mid` 를 이 문장 **글자대로** 예측하면 무엇이고, 실제는 무엇이었나?

### 9. `@Throws` 는 왜 여기서 다시 안 쟀나 (연결)

- [34번 주제](../34-exceptions-nothing-and-try-expression/) (2)가 보인 `@Throws` 의 효과 두 가지(없을 때 Java `catch` 가 받는 에러 · 달았을 때 클래스 파일에 생기는 것)는 무엇인가?

### 10. `@JvmName` 과 value class (연결)

- [26번 주제](../26-value-class-and-boxing/) (5)에서 `@JvmName` 으로 뭉개진 이름을 풀었더니 Java 쪽에서 **무엇이 사라졌나**? 이 문서의 「교체」와 무엇이 다른가?

### 11. `@JvmField` 와 게터 없는 프로퍼티 (경계)

- 5번의 2번째 줄과 5번째 줄은 둘 다 커스텀 접근자인데 **에러 문구가 다르다.** 무엇이 둘을 갈랐나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
