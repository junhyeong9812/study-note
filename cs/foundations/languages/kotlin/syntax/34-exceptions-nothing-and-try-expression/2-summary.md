# kotlin/syntax/34 — 예외: 검사 예외 없음·`Nothing` 타입·`try` 가 식이라는 것 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Exceptions](https://kotlinlang.org/docs/exceptions.html)(「Kotlin treats all exceptions as unchecked by default」 · `@Throws` 는 Java 등 검사 예외를 가르는 언어와의 상호운용용 · `throw` 식의 타입이 **`Nothing`**, 「a subtype of all other types」 · `TODO()` 도 `Nothing` · `try` 는 식이고 「The `finally` block is always executed, but it doesn't change the result」).
> **실행 검증** — 이 문서의 모든 출력·에러·경고·바이트코드는 **kotlinc 2.4.20 (JRE 21.0.5)** 과 Temurin **JDK 21.0.5** 의 `javac`·`java`·`javap` 에서 실제로 얻었다.\
> `kotlinc` 15회(에러·경고 줄을 세는 3회 포함 · 컴파일 실패 2벌) · `javac` 7회(실패 2벌 · 경고 1벌) · `java` 8회 · `javap` 3회.\
> ★★ 블록은 전부 **캡처 스크립트가 파일로 받아** 조립한 것이다 — 사람이 옮겨 적지 않았다. 소스 펜스의 첫 줄 배너도 캡처가 찍었다.\
> ★ 한 명령의 출력은 **한 흐름**뿐이다 — 컴파일러 진단은 전부 표준 오류, 프로그램 출력은 전부 표준 출력이라 한 명령 안에서 둘이 섞이는 자리가 없다(예외는 전부 잡아서 찍었다).
> **버전** — 검사 예외 없음·`Nothing`·`try` 식·`@Throws` 는 1.0. ★ **「도달 불가 코드」 경고가 기본으로 안 나오는 것**은 이 판(K2 2.4.20)의 관찰이다((5)).
> **경계** — ★★★ **검사 예외 폐지의 논지**(무엇을 얻고 무엇을 떠넘겼나)는 [`../../언어-특성/README.md`](../../언어-특성/README.md) §8 이 정본이다 — 여기는 **그 결정이 코드에서 어떻게 보이나**(컴파일이 되나·클래스 파일에 무엇이 남나)만 다룬다.\
> 짝은 Java 갈래 [`../../../java/syntax/25-exceptions/`](../../../java/syntax/25-exceptions/) — **검사 예외 규칙과 전파 문법의 Java 쪽 정본**이다. 거기서 본 `javac` 에러 두 문구를 여기서는 **Kotlin 과 한 쌍으로** 던졌다((1)(2)).\
> `@Throws`·`@JvmStatic` 등 **Java 상호운용 애너테이션 하나하나의 바이트코드**는 목록의 **39번 주제**가, `?:` 오른쪽의 `throw`·`return` 관용구는 [03번 주제](../03-null-safe-types/) (7)이, `when` 이 식일 때의 완결성은 [06번 주제](../06-when-expression/)가 정본이다.\
> ★ **대비** — Rust 의 발산 타입 `!` 은 [`../../../rust/syntax/06-functions-and-never-type/`](../../../rust/syntax/06-functions-and-never-type/), TS 의 `never` 는 [`../../../ts/syntax/04-any-unknown-never-void/`](../../../ts/syntax/04-any-unknown-never-void/), 오류를 **값**으로 다루는 Go 는 [`../../../go/syntax/23-error-interface-and-errors-as-values/`](../../../go/syntax/23-error-interface-and-errors-as-values/), `finally` 격자의 JS 판은 [`../../../js/syntax/32-error-handling-and-error/`](../../../js/syntax/32-error-handling-and-error/)가 정본이다.
> 이 본문은 Claude 작성이다(원고 없음).

★ **본체는 둘째 창이다** — 「**같은 모양을 `javac` 와 `kotlinc` 에 던져 컴파일이 되나**」. 검사 예외 폐지는 **실행 결과가 아니라 컴파일러의 반응**으로만 보인다. 셋째 창(`javap` — `Exceptions:` 속성·`java/lang/Void`·`KotlinNothingValueException`)이 그 반응의 **흔적**을 클래스 파일에서 확인한다.

## 이 주제가 쓰는 세 층

| 층 | 뜻 | 근거로 쓰는 것 |
|---|---|---|
| **언어 보장** | 명세·공식 문서가 약속한 것 | ★★★ 모든 예외가 비검사 · `throw` 는 **`Nothing` 타입의 식** · `Nothing` 은 **모든 타입의 하위 타입** · `try` 는 식이고 **`finally` 는 값에 안 들어간다** |
| **구현(JVM 백엔드)** | kotlinc 가 JVM 으로 내리는 방식 | ★★ `Nothing` 반환이 **`java.lang.Void`** · `Nothing` 호출 뒤에 심는 **`KotlinNothingValueException`** · `@Throws` 가 만드는 **`Exceptions:` 속성** |
| **이 판의 관찰** | kotlinc 2.4.20 에서 이번에 본 것 | ★ **「도달 불가」 경고가 `-Wextra` 에서만** 나오는 것 · 진단 문구 · 교집합 타입 표기(`Comparable<*> & Serializable`) |

## 이 판

```text
===== kotlinc -version =====
info: kotlinc-jvm 2.4.20 (JRE 21.0.5+11-LTS)
(exit 0)
```

```text
===== javac -version =====
javac 21.0.5
(exit 0)
```

## 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| **흔들린다** | (이 주제에는 없다) | 해시코드·주소·시간·스레드를 **하나도 안 찍었다** — 예외는 `toString()` 만 찍었다 |
| 안 흔들린다 | 실행 출력 · 예외 메시지 | 같은 판이면 같다 |
| 안 흔들린다 | `javac`·`kotlinc` 진단의 **문구·`파일:줄:칸`·캐럿** · 「물은 N · 줄 M」 | 결정적이다 |
| 안 흔들린다 | `javap` 출력 — 상수 풀 번호까지 | 같은 소스·같은 판이면 같다 |

★ 근거 — 캡처 스크립트를 처음부터 두 번 돌려 **블록 전체를 바이트 단위로 대조**했다(수치는 3-answer 의 「실행 검증」).

## 한눈에 — 쉽게 말하면

**Java 의 검사 예외는 「위험물 신고서」다.** `throws IOException` 이라고 적힌 메서드를 부르는 쪽은 **신고서에 서명**(잡거나 다시 신고)하지 않으면 **통관(컴파일)이 안 된다.**
**Kotlin 은 신고서 제도를 없앴다.** 같은 위험물이 **서명 없이 통과**하고, 터지면 그때 터진다. 대신 **Java 쪽 세관**은 여전히 신고서를 보므로, Kotlin 이 신고서를 안 써 주면(`@Throws` 없음) Java 는 **「그런 위험물은 신고된 적 없다」며 잡는 것조차 거부**한다.

그리고 **`Nothing` 은 「돌아오지 않는 편도표」다.** 표를 끊은 사람(`throw`·`TODO()`·`fail()`)은 **다음 줄로 안 돌아온다** — 그래서 컴파일러는 그 자리의 타입을 **무엇이든 될 수 있는 바닥**으로 취급한다.

| 비유 | 실체 | 이 문서에서 |
|---|---|---|
| 위험물 신고서 | 검사 예외 — `throws` 절 | (1) |
| 서명 없이 통과 | Kotlin 에서 `JIo.read()` 를 **안 잡아도** 컴파일 | (1) |
| 「신고된 적 없다」며 거부 | Java 의 `exception IOException is never thrown …` | (2) |
| 신고서를 대신 써 주기 | `@Throws` → 클래스 파일의 **`Exceptions:` 속성** | (2) |
| 편도표 | `Nothing` — 반환이 없는 식 | (3) |
| 표를 끊었는데 돌아온 승객을 막는 검문 | `KotlinNothingValueException` | (3)(7) |
| 편도표 뒤의 좌석(좌석 번호 없음) | 도달 불가 코드 — 경고는 `-Wextra` 에서만 | (5) |
| 출구 검문소 | `finally` — 값은 못 바꾸지만 **끝은 바꿔 쥘 수 있다** | (6) |

```text
   Java 소스가 부르면                           Kotlin 소스가 부르면
   +----------------------------------+         +----------------------------------+
   | JIo.read()   // throws IOException|         | JIo.read()   // 같은 메서드       |
   |   잡거나 선언하지 않으면           |         |   잡든 안 잡든                    |
   |   -> javac 「unreported exception」|         |   -> kotlinc 통과 (exit 0)        |
   +----------------------------------+         +----------------------------------+

   Kotlin 이 던지고 Java 가 잡으면
   plain()                      -> 클래스 파일에 Exceptions: 없음 -> Java catch (IOException) 거부
   @Throws(IOException::class)  -> Exceptions: throws IOException  -> Java 가 잡아야 한다
```

## 이 주제가 답하려는 질문

1. 검사 예외가 없다는 것은 **어느 창에서** 보이나 — 같은 모양을 `javac` 와 `kotlinc` 에 던지면. 그리고 **반대 방향**(Kotlin 을 Java 가 부를 때)은.
2. `Nothing` 은 **타입 추론에서** 무엇을 하나 — `?:`·`if` 의 한쪽에 오면 결과 타입이 어떻게 되나. JVM 에서는 무엇이 되나.
3. `try` 가 식이라는 것은 **`finally` 와 어떻게** 맞물리나 — 값은 누가 정하고, 끝은 누가 바꿔 쥐나.

## 동작 방식

### (0) ★★★ 이 주제가 쓰는 창 — 그리고 「부적용인 창」

| 창 | 무엇을 보여 주나 | 어디서 왔나 |
|---|---|---|
| ★★★ **`javac` 대 `kotlinc` — 같은 모양을 던져 컴파일이 되나** | 검사 예외 규칙이 **있는 언어와 없는 언어**((1)(2)) | ★ **본체 창** · Java 25번의 창을 한 쌍으로 |
| ★★ **`javap -v`/`-c`** | `Exceptions:` 속성((2)) · `Void`·`KotlinNothingValueException`((3)(7)) | 이 갈래의 기본 창 |
| ★★ **일부러 틀린 타입 — 진단의 `actual '…'`** | `Nothing` 이 **추론을 어떻게 바꾸나**((4)) — 추론 타입을 컴파일러가 스스로 말하게 한다 | 규칙 18-C 의 변형 |
| ★ **경고 세기 — 기본 대 `-Wextra`** | 「도달 불가」 경고가 **어디서 나오나**((5)) | 규칙 18-A |
| ★ **격자 — `try` 3 × `finally` 3** | `finally` 가 끝을 바꿔 쥐는 칸을 **스크립트가 센다**((6)) | JS 32편의 격자를 그대로 옮겼다 |
| **부적용 — 실행 시간** | 「예외는 느리다」·「`Result` 가 빠르다」는 **재지 않았다** | — |
| **부적용 — 할당 계수** | 예외 객체 생성 비용은 이 주제의 질문이 아니다 | — |

### (1) ★★★ 같은 `throws IOException` 을 두 언어가 부르면

**언제 쓰나** — 「Kotlin 에서는 검사 예외가 없다」를 **눈으로** 확인할 때.

```java
// JIo.java
import java.io.IOException;

public class JIo {
    public static String read() throws IOException {
        throw new IOException("disk");
    }
}
```

```java
// CallJ.java
public class CallJ {
    public static void main(String[] args) {
        System.out.println(JIo.read());
    }
}
```

```kotlin
// callj.kt
fun noCatch(): String = JIo.read()

fun main() {
    val r = try { JIo.read() } catch (e: java.io.IOException) { "caught ${e.message}" }
    println("A $r")
    println("B " + runCatching { noCatch() }.exceptionOrNull())
}
```

```text
===== javac -d o34j JIo.java CallJ.java =====
CallJ.java:3: error: unreported exception IOException; must be caught or declared to be thrown
        System.out.println(JIo.read());
                                   ^
1 error
(exit 1)
===== javac -d o34k JIo.java =====
(exit 0)
===== kotlinc -cp o34k callj.kt -d o34k =====
(exit 0)
===== java -cp o34k:kotlin-stdlib.jar CalljKt =====
A caught disk
B java.io.IOException: disk
(exit 0)
```

- ★★★ **같은 메서드, 다른 반응** — Java 소스는 「`unreported exception IOException; must be caught or declared to be thrown`」로 **컴파일이 멈추고**(`exit 1`), Kotlin 소스는 **`noCatch()` 처럼 아무것도 안 잡은 함수까지** 통과한다(`exit 0`).
- ★★ **예외가 사라진 것이 아니다** — `B java.io.IOException: disk`. 검사 예외 폐지는 **컴파일 시점의 의무**를 없앤 것이지, 런타임의 예외를 없앤 것이 아니다.
- ★ `A caught disk` — Kotlin 도 `catch (e: IOException)` 은 **쓸 수 있다.** 안 써도 되는 것일 뿐이다.
- Java 쪽 규칙 자체(무엇이 검사 예외인가 · `Throwable` 도 검사 예외라는 것)는 [Java 25번](../../../java/syntax/25-exceptions/)이 정본이다.

### (2) ★★★ 반대 방향 — Kotlin 이 던지고 Java 가 잡으면

**언제 쓰나** — Kotlin 라이브러리를 Java 코드가 쓸 때.

```kotlin
// kio.kt
import java.io.IOException

fun plain(): String = throw IOException("plain")

@Throws(IOException::class)
fun declared(): String = throw IOException("declared")
```

```java
// UseK1.java
import java.io.IOException;

public class UseK1 {
    static void a() {
        try { KioKt.plain(); } catch (IOException e) { }
    }
    static void b() {
        KioKt.declared();
    }
}
```

```java
// UseK2.java
import java.io.IOException;

public class UseK2 {
    public static void main(String[] args) {
        try { KioKt.declared(); } catch (IOException e) { System.out.println("A " + e); }
        try { KioKt.plain(); } catch (Exception e) {
            System.out.println("B " + e.getClass().getName() + " / instanceof IOException = " + (e instanceof IOException));
        }
    }
}
```

```text
===== kotlinc kio.kt -d o34t =====
(exit 0)
===== javac -cp o34t -d o34t UseK1.java =====
UseK1.java:5: error: exception IOException is never thrown in body of corresponding try statement
        try { KioKt.plain(); } catch (IOException e) { }
                               ^
UseK1.java:8: error: unreported exception IOException; must be caught or declared to be thrown
        KioKt.declared();
                      ^
2 errors
(exit 1)
===== javac -cp o34t:kotlin-stdlib.jar -d o34t UseK2.java =====
(exit 0)
===== java -cp o34t:kotlin-stdlib.jar UseK2 =====
A java.io.IOException: declared
B java.io.IOException / instanceof IOException = true
(exit 0)
```

```text
===== javap -v -p o34t/KioKt.class | grep -E 'String (plain|declared)\(\);|Exceptions:|throws ' =====
  public static final java.lang.String plain();
  public static final java.lang.String declared() throws java.io.IOException;
    Exceptions:
      throws java.io.IOException
(exit 0)
```

- ★★★ **`a()` — 「`exception IOException is never thrown in body of corresponding try statement`」.** `plain()` 은 실제로 `IOException` 을 던지는데, **Java 컴파일러는 그 사실을 모른다** — 클래스 파일에 `throws` 가 없으니 「안 던지는 메서드의 검사 예외를 잡으려 한다」로 읽는다. Java 는 **던지지 않는 검사 예외의 `catch` 를 에러로** 막는 언어라, 잡는 것조차 못 한다.
- ★★ **`b()` — 「`unreported exception IOException`」.** `@Throws` 를 단 `declared()` 는 **Java 에게 진짜 검사 예외 메서드**가 된다 — 이제는 **안 잡으면** 에러다. `@Throws` 는 Java 호출자를 **도와주는 동시에 의무를 지운다.**
- ★★ **`javap` 의 차이는 한 줄이다** — `declared() throws java.io.IOException` + `Exceptions: throws java.io.IOException`. `plain()` 에는 **아무것도 없다.** 검사 예외는 **JVM 의 강제가 아니라 `javac` 가 이 속성을 읽어 하는 검사**다.
- ★★ **`B java.io.IOException / instanceof IOException = true`** — `catch (Exception e)` 로는 `plain()` 의 `IOException` 이 **잡힌다.** 우회로는 있지만, **「어떤 검사 예외가 올지」를 Java 쪽이 알 방법은 사라졌다.**
- ★ `@Throws` 가 **Kotlin 호출자에게는 아무 효과가 없다** — Kotlin 쪽 규칙은 (1) 그대로다. 애너테이션 하나하나의 바이트코드는 목록의 **39번 주제**가 정본이다.

### (3) ★★ `Nothing` — 돌아오지 않는 식의 타입

**언제 쓰나** — `?: throw`·`TODO()`·`error()`·`fail()` 뒤의 타입이 왜 성립하는지 볼 때.

```kotlin
// nothing.kt
import kotlin.test.fail

fun die(msg: String): Nothing = throw IllegalStateException(msg)

fun n1(): Int {
    TODO()
    return 1
}

fun n2(s: String?): Int {
    val t = s ?: die("none")
    return t.length
}

fun n3(flag: Boolean): Int {
    val v = if (flag) 10 else throw IllegalArgumentException("no")
    return v
}

fun n4(): Int {
    fail("stop")
    return 4
}

fun main() {
    println("A " + runCatching { n1() }.exceptionOrNull())
    println("B ${n2("abc")} " + runCatching { n2(null) }.exceptionOrNull())
    println("C ${n3(true)} " + runCatching { n3(false) }.exceptionOrNull())
    println("D " + runCatching { n4() }.exceptionOrNull())
    val xs: List<String> = emptyList<Nothing>()
    println("E ${xs.size}")
}
```

```text
===== kotlinc -cp kotlin-test.jar nothing.kt -d o34n =====
(exit 0)
===== java -cp o34n:kotlin-stdlib.jar:kotlin-test.jar NothingKt =====
A kotlin.NotImplementedError: An operation is not implemented.
B 3 java.lang.IllegalStateException: none
C 10 java.lang.IllegalArgumentException: no
D java.lang.AssertionError: stop
E 0
(exit 0)
```

```text
===== javap -c -p o34n/NothingKt.class | awk '/ (die|n1|n2|n4)\(/,/^$/' =====
  public static final java.lang.Void die(java.lang.String);
    Code:
       0: aload_0
       1: ldc           #9                  // String msg
       3: invokestatic  #15                 // Method kotlin/jvm/internal/Intrinsics.checkNotNullParameter:(Ljava/lang/Object;Ljava/lang/String;)V
       6: new           #17                 // class java/lang/IllegalStateException
       9: dup
      10: aload_0
      11: invokespecial #21                 // Method java/lang/IllegalStateException."<init>":(Ljava/lang/String;)V
      14: athrow

  public static final int n1();
    Code:
       0: new           #26                 // class kotlin/NotImplementedError
       3: dup
       4: aconst_null
       5: iconst_1
       6: aconst_null
       7: invokespecial #29                 // Method kotlin/NotImplementedError."<init>":(Ljava/lang/String;ILkotlin/jvm/internal/DefaultConstructorMarker;)V
      10: athrow

  public static final int n2(java.lang.String);
    Code:
       0: aload_0
       1: dup
       2: ifnonnull     20
       5: pop
       6: ldc           #34                 // String none
       8: invokestatic  #36                 // Method die:(Ljava/lang/String;)Ljava/lang/Void;
      11: pop
      12: new           #38                 // class kotlin/KotlinNothingValueException
      15: dup
      16: invokespecial #41                 // Method kotlin/KotlinNothingValueException."<init>":()V
      19: athrow
      20: astore_1
      21: aload_1
      22: invokevirtual #46                 // Method java/lang/String.length:()I
      25: ireturn

  public static final int n4();
    Code:
       0: ldc           #62                 // String stop
       2: invokestatic  #67                 // Method kotlin/test/AssertionsKt.fail:(Ljava/lang/String;)Ljava/lang/Void;
       5: pop
       6: new           #38                 // class kotlin/KotlinNothingValueException
       9: dup
      10: invokespecial #41                 // Method kotlin/KotlinNothingValueException."<init>":()V
      13: athrow
(exit 0)
```

- ★★★ **`die` 의 JVM 반환 타입은 `java.lang.Void`** 다(`die(Ljava/lang/String;)Ljava/lang/Void;`). JVM 에는 「돌아오지 않는다」는 타입이 없으므로 **값이 `null` 하나뿐인 `Void`** 로 내렸다 — 이것은 **백엔드의 선택**이다.
- ★★★ **`n2` 의 `8: invokestatic die` 바로 뒤에 `12: new KotlinNothingValueException … 19: athrow`.** `die` 가 **만에 하나 돌아오면** 그 자리에서 터뜨리는 검문이다. 언어가 「안 돌아온다」고 약속했으니 **돌아왔다는 것 자체가 불변식 위반**이다((7)에서 실제로 터뜨린다).
- ★★ **`n4` 의 `return 4` 는 클래스 파일에 없다** — `fail("stop")` 뒤가 곧바로 `KotlinNothingValueException` 검문이다. `kotlin.test.fail` 도 반환 타입이 `Nothing` 이라 **그 뒤를 컴파일러가 버렸다.**
- ★★ **`n1` 은 `TODO()` 호출이 아니라 `new NotImplementedError … athrow`** 다 — `TODO()` 가 `inline` 이라 몸통이 펼쳐졌고, 그래서 호출 뒤 검문도 필요 없다. 출력 `A` 의 메시지 「`An operation is not implemented.`」가 그 예외다.
- ★★ **`E 0`** — `val xs: List<String> = emptyList<Nothing>()` 가 컴파일된다. `Nothing` 이 **모든 타입의 하위 타입**이고 `List` 가 공변이라 `List<Nothing>` 은 `List<String>` 의 하위 타입이다([28번 주제](../28-generics-variance-in-out-star-where/)).
- ★ `B`·`C` — `?: die(…)` 와 `else throw …` 가 성립하는 근거가 (4)다. `?:` 관용구 자체는 [03번 주제](../03-null-safe-types/) (7)이 정본이다.

### (4) ★★ 추론 타입을 컴파일러가 말하게 하기

**언제 쓰나** — 「`?:` 오른쪽이 `throw` 면 왼쪽이 non-null 로 좁혀진다」를 **추측이 아니라 출력으로** 보고 싶을 때.

```kotlin
// infer.kt
fun p1(s: String?) { val t = s ?: throw IllegalStateException(); val z: Int = t }
fun p2(s: String?) { val t = s ?: return; val z: Int = t }
fun p3() { val n = null; val z: Int = n }
fun p4(f: Boolean) { val v = if (f) 1 else "s"; val z: String = v }
fun p5(f: Boolean) { val v = if (f) 1 else error("e"); val z: String = v }
fun p6() { val r = try { 1 } catch (e: Exception) { "s" }; val z: Int = r }
fun p7() { val xs = listOf(null); val z: Int = xs }
fun p8() { val e = throw IllegalStateException(); val z: Int = e }
```

```text
===== kotlinc infer.kt -d o34i =====
infer.kt:1:77: error: initializer type mismatch: expected 'Int', actual 'String'.
fun p1(s: String?) { val t = s ?: throw IllegalStateException(); val z: Int = t }
                                                                            ^
infer.kt:2:54: error: initializer type mismatch: expected 'Int', actual 'String'.
fun p2(s: String?) { val t = s ?: return; val z: Int = t }
                                                     ^
infer.kt:3:37: error: initializer type mismatch: expected 'Int', actual 'Nothing?'.
fun p3() { val n = null; val z: Int = n }
                                    ^
infer.kt:4:63: error: initializer type mismatch: expected 'String', actual 'Comparable<*> & Serializable'.
fun p4(f: Boolean) { val v = if (f) 1 else "s"; val z: String = v }
                                                              ^
infer.kt:5:70: error: initializer type mismatch: expected 'String', actual 'Int'.
fun p5(f: Boolean) { val v = if (f) 1 else error("e"); val z: String = v }
                                                                     ^
infer.kt:6:71: error: initializer type mismatch: expected 'Int', actual 'Comparable<*> & Serializable'.
fun p6() { val r = try { 1 } catch (e: Exception) { "s" }; val z: Int = r }
                                                                      ^
infer.kt:7:46: error: initializer type mismatch: expected 'Int', actual 'List<Nothing?>'.
fun p7() { val xs = listOf(null); val z: Int = xs }
                                             ^
(exit 1)
===== echo "물은 함수 $(grep -c '^fun ' infer.kt) · error 줄 $(kotlinc infer.kt -d o34i2 2>&1 | grep -c ': error:')" =====
물은 함수 8 · error 줄 7
(exit 0)
```

```text
   s ?: throw …          String?  와  Nothing  의 공통 상위 타입   -> String          (p1)
   s ?: return           String?  와  Nothing                     -> String          (p2)
   if (f) 1 else error() Int      와  Nothing                     -> Int             (p5)
   if (f) 1 else "s"     Int      와  String                      -> Comparable<*> & Serializable  (p4)
   null                  -                                        -> Nothing?        (p3)
   throw …               Nothing  -> 어디에나 대입된다              -> 에러 없음 ★      (p8)
```

- ★★★ **물은 함수 8 · 에러 줄 7.** 에러가 **안 난 `p8` 이 결론의 절반**이다 — `val e = throw …` 의 타입 `Nothing` 은 `Int` 에 **대입된다.** 바닥 타입이므로.
- ★★★ **`p1`·`p2` 의 `actual 'String'`** — `String?` 과 `Nothing` 을 합치면 `Nothing` 은 **아무것도 보태지 않는다.** 그래서 `?:` 가 벗긴 `String` 이 그대로 남는다. `p5`(`Int` 와 `error()`)도 같은 이유로 **`Int`** 다.
- ★★ **`p4`·`p6` 은 대조군이다** — 한쪽이 `Nothing` 이 아니면 `Int` 와 `String` 의 공통 상위 타입 **`Comparable<*> & Serializable`** 이 된다. `try`/`catch` 도 `if` 와 같은 규칙으로 두 가지를 합친다(`p6`).
- ★ **`p3` 의 `Nothing?`**, **`p7` 의 `List<Nothing?>`** — `null` 리터럴 하나의 타입이 `Nothing?` 이다. 「값이 `null` 하나뿐인 타입」이다.
- ★ 교집합 표기 `&` 는 **이 판 진단의 표기**다 — 추론 결과 자체는 언어 규칙이지만 **그것을 어떻게 적어 보이나**는 판에 매인다.

### (5) ★★ 도달 불가 코드 — 경고는 **`-Wextra` 에서만**

```kotlin
// unr.kt
fun u1(): Int {
    return 1
    println("after return")
}
fun u2(): Int {
    throw IllegalStateException()
    println("after throw")
}
fun u3(): Int {
    TODO()
    println("after TODO")
}
```

```text
===== kotlinc unr.kt -d o34u =====
(exit 0)
===== kotlinc -Wextra unr.kt -d o34u2 =====
unr.kt:3:5: warning: unreachable code.
    println("after return")
    ^^^^^^^^^^^^^^^^^^^^^^^
unr.kt:7:5: warning: unreachable code.
    println("after throw")
    ^^^^^^^^^^^^^^^^^^^^^^
unr.kt:11:5: warning: unreachable code.
    println("after TODO")
    ^^^^^^^^^^^^^^^^^^^^^
(exit 0)
===== echo "물은 자리 3 · 기본 warning 줄 $(kotlinc unr.kt -d o34u3 2>&1 | grep -c ': warning:') · -Wextra warning 줄 $(kotlinc -Wextra unr.kt -d o34u4 2>&1 | grep -c ': warning:')" =====
물은 자리 3 · 기본 warning 줄 0 · -Wextra warning 줄 3
(exit 0)
```

- ★★★ **물은 자리 3 · 기본 경고 0 · `-Wextra` 경고 3.** 이 판에서 「`unreachable code.`」는 **기본으로 안 나온다.** `-Wextra` 를 줘야 `return`·`throw`·`TODO()` 뒤의 세 줄이 전부 잡힌다.
- ★★ **세 자리가 같은 경고**라는 것이 곧 `Nothing` 의 뜻이다 — 컴파일러에게 `TODO()` 는 `throw` 와 **같은 부류의 식**이다.
- ★ **경고가 없다고 도달 가능한 것이 아니다** — 기본 빌드에서 `TODO()` 뒤의 코드는 **조용히 버려진다**((3)의 `n4` 처럼 클래스 파일에도 없다). 「경고 0」은 이 판에서 **안 물어본 것과 구분이 안 된다**(규칙 18-A).

### (6) ★★★ `try` 는 식이다 — 그리고 `finally` 는 끝을 바꿔 쥔다

**값은 `try` 또는 `catch` 의 마지막 식**이고, **`finally` 의 마지막 식은 버려진다.**

```kotlin
// tryval.kt
fun parse(s: String): Int = try {
    s.toInt()
} catch (e: NumberFormatException) {
    -1
} finally {
    println("  finally($s)")
    999
}

fun main() {
    println("A ${parse("42")}")
    println("B ${parse("x")}")
    val v = try { 1 } finally { 2 }
    println("C $v")
}
```

```text
===== kotlinc tryval.kt -d o34v =====
tryval.kt:7:5: warning: expression is unused.
    999
    ^^^
tryval.kt:13:33: warning: expression is unused.
    val v = try { 1 } finally { 2 }
                                ^
(exit 0)
===== java -cp o34v:kotlin-stdlib.jar TryvalKt =====
  finally(42)
A 42
  finally(x)
B -1
C 1
(exit 0)
```

- ★★★ **`A 42` · `B -1` · `C 1`** — `finally` 의 `999`·`2` 는 **값에 안 들어간다.** 컴파일러가 「`expression is unused.`」 경고로 그것을 직접 말한다(7번째 줄·13번째 줄).
- ★ `finally(42)` 가 **`A 42` 보다 먼저** 찍힌다 — `finally` 는 `try` 식의 값이 **호출자에게 넘어가기 전에** 돈다.

**그런데 `finally` 가 `return`·`throw` 로 끝나면** 값이 아니라 **끝(완료 방식) 자체**가 바뀐다. `try` 가 끝나는 세 방식 × `finally` 가 끝나는 세 방식 = 9칸을 스크립트가 전부 돌렸다.

```kotlin
// fgrid.kt
fun cell(t: Char, f: Char): String {
    try {
        when (t) {
            'N' -> {}
            'R' -> return "T-return"
            else -> throw IllegalStateException("T-throw")
        }
    } finally {
        when (f) {
            'N' -> {}
            'R' -> return "F-return"
            else -> throw IllegalArgumentException("F-throw")
        }
    }
    return "after-try"
}

fun outcome(block: () -> String): String =
    try { "value " + block() } catch (e: Exception) { "exception " + e.message }

fun main() {
    val alone = mapOf('N' to "value after-try", 'R' to "value T-return", 'T' to "exception T-throw")
    var lost = 0
    for (f in "NRT") for (t in "NRT") {
        val got = outcome { cell(t, f) }
        val same = got == alone[t]
        if (!same) lost++
        println("try=$t finally=$f -> $got ; same as try alone: $same")
    }
    println("cells where the try outcome differs: $lost / 9")
}
```

```text
===== kotlinc -Wextra fgrid.kt -d o34f =====
(exit 0)
===== java -cp o34f:kotlin-stdlib.jar FgridKt =====
try=N finally=N -> value after-try ; same as try alone: true
try=R finally=N -> value T-return ; same as try alone: true
try=T finally=N -> exception T-throw ; same as try alone: true
try=N finally=R -> value F-return ; same as try alone: false
try=R finally=R -> value F-return ; same as try alone: false
try=T finally=R -> value F-return ; same as try alone: false
try=N finally=T -> exception F-throw ; same as try alone: false
try=R finally=T -> exception F-throw ; same as try alone: false
try=T finally=T -> exception F-throw ; same as try alone: false
cells where the try outcome differs: 6 / 9
(exit 0)
```

```text
                         finally 가 정상 종료   finally 가 return     finally 가 throw
   try 가 정상 종료        after-try (그대로)     F-return  ★          F-throw  ★
   try 가 return          T-return  (그대로)     F-return  ★          F-throw  ★
   try 가 throw           T-throw   (그대로)     F-return  ★ 예외 소실  F-throw  ★ 예외 교체
```

- ★★★ **`6 / 9`** — `finally` 가 `return`·`throw` 로 끝난 여섯 칸은 **전부 `finally` 의 것**이 나간다. `try=T finally=R` 은 **예외가 통째로 사라지고 `F-return` 이 값으로** 나온다.
- ★★ **`-Wextra` 로 컴파일했는데 진단이 0줄이다.** `finally` 안의 `return` 을 Kotlin 은 **경고조차 안 한다** — Java 는 `-Xlint:finally` 로 「`finally clause cannot complete normally`」를 준다(3-answer 10번).
- ★ JS 의 같은 격자도 **`6 / 9`** 였다([JS 32번](../../../js/syntax/32-error-handling-and-error/)) — `finally` 의 완료가 `try` 의 완료를 덮는 규칙은 세 언어가 같다.

### (7) ★★ 돌아온 `Nothing` — `KotlinNothingValueException`

**언제 쓰나** — `Nothing` 을 반환한다고 선언된 멤버를 **Java 가 구현**할 때.

```kotlin
// stopper.kt
interface Stopper {
    fun stop(): Nothing
}
```

```java
// JStop.java
public class JStop implements Stopper {
    @Override
    public Void stop() {
        return null;
    }
}
```

```kotlin
// usestop.kt
fun halt(s: Stopper): Int {
    s.stop()
}

fun main() {
    println("A " + runCatching { halt(JStop()) }.exceptionOrNull())
}
```

```text
===== kotlinc stopper.kt -d o34s =====
(exit 0)
===== javac -cp o34s -d o34s JStop.java =====
(exit 0)
===== kotlinc -cp o34s usestop.kt -d o34s =====
(exit 0)
===== java -cp o34s:kotlin-stdlib.jar UsestopKt =====
A kotlin.KotlinNothingValueException
(exit 0)
===== javap -c -p o34s/UsestopKt.class | awk '/ halt\(/,/^$/' =====
  public static final int halt(Stopper);
    Code:
       0: aload_0
       1: ldc           #9                  // String s
       3: invokestatic  #15                 // Method kotlin/jvm/internal/Intrinsics.checkNotNullParameter:(Ljava/lang/Object;Ljava/lang/String;)V
       6: aload_0
       7: invokeinterface #21,  1           // InterfaceMethod Stopper.stop:()Ljava/lang/Void;
      12: pop
      13: new           #23                 // class kotlin/KotlinNothingValueException
      16: dup
      17: invokespecial #27                 // Method kotlin/KotlinNothingValueException."<init>":()V
      20: athrow
(exit 0)
```

- ★★★ **`A kotlin.KotlinNothingValueException`** — Java 는 `Nothing` 을 모르므로 `Void` 를 돌려주는 **평범한 메서드**로 구현했고 `null` 을 돌려줬다. Kotlin 호출자 쪽에 kotlinc 가 심은 **`13: new KotlinNothingValueException … 20: athrow`** 가 그 「돌아온 승객」을 막았다.
- ★★ **`halt` 는 `return` 없이 컴파일됐다** — `s.stop()` 이 `Nothing` 이니 **그 뒤는 도달 불가**이고, 반환 타입 `Int` 를 채울 필요가 없다. 그 약속이 깨졌을 때 **엉뚱한 값이 흘러나가지 않게** 하는 것이 검문의 몫이다.
- ★ `javac` 는 `JStop` 을 **경고 없이** 받았다 — `Nothing` 의 약속은 **Kotlin 컴파일러 안에서만** 강제된다.

### (8) ★ `x + TODO()` — 바닥 타입이 오버로드를 흐린다

```kotlin
// amb.kt
fun sum(x: Int): Int {
    val y = x + TODO()
    return y
}
```

```text
===== kotlinc amb.kt -d o34a =====
amb.kt:2:15: error: overload resolution ambiguity between candidates:
fun plus(other: Byte): Int
fun plus(other: Short): Int
fun plus(other: Int): Int
fun plus(other: Long): Long
fun plus(other: Float): Float
fun plus(other: Double): Double
    val y = x + TODO()
              ^
(exit 1)
```

- ★★ **「타입 불일치」가 아니라 「`overload resolution ambiguity`」** 다. `TODO()` 의 `Nothing` 은 `Byte`·`Short`·`Int`·`Long`·`Float`·`Double` **어디에나 맞으므로** 여섯 `plus` 가 **전부 후보로 남는다.** 바닥 타입이라 가를 기준이 없다.
- ★ 그래서 `TODO()` 는 **식의 한가운데가 아니라 몸통 전체**(`fun f(): Int = TODO()`)에 두는 것이 관용이다 — 거기서는 기대 타입이 하나라 모호성이 없다.

## 문법 — 형태와 규칙

**형태** — `?: throw` · `try`/`catch` 식이 한 함수에서 도는 최소 예제다.

```kotlin
// form34.kt
fun parsePort(s: String?): Int {
    val raw = s ?: throw IllegalArgumentException("port missing")
    return try { raw.toInt() } catch (e: NumberFormatException) { -1 }
}

fun main() {
    println("A ${parsePort("8080")} ${parsePort("x")}")
    println("B " + runCatching { parsePort(null) }.exceptionOrNull())
}
```

```text
===== kotlinc form34.kt -d o34z =====
(exit 0)
===== java -cp o34z:kotlin-stdlib.jar Form34Kt =====
A 8080 -1
B java.lang.IllegalArgumentException: port missing
(exit 0)
```

**규칙 불릿**

- Kotlin 의 예외는 **전부 비검사**다 — 잡지도 선언하지도 않아도 컴파일된다((1)).
- Java 에게 검사 예외를 알리려면 **`@Throws(X::class)`** — 클래스 파일에 `Exceptions:` 가 생긴다((2)).
- `throw` 는 **식**이고 타입은 **`Nothing`** — `?:`·`if`·`when` 의 한쪽에 둘 수 있다((3)(4)).
- `Nothing` 을 돌려주는 함수(`TODO()`·`error()`·`fail()`·직접 만든 `die`) 뒤는 **도달 불가**다((3)(5)).
- `null` 리터럴의 타입은 **`Nothing?`** 다((4)).
- `try` 는 **식** — 값은 `try` 또는 `catch` 의 마지막 식, **`finally` 는 값에 안 들어간다**((6)).
- `finally` 가 `return`·`throw` 로 끝나면 **그것이 이긴다** — 예외가 사라질 수 있다((6)).

## 어디서 틀리나

1. ★★★ **Kotlin 함수의 예외를 Java 에서 `catch (IOException e)` 로 잡으려 한다.** `@Throws` 가 없으면 「`is never thrown in body`」로 **컴파일이 안 된다**((2)).
2. ★★★ **`@Throws` 를 달면 Java 호출자가 편해지기만 한다고 믿는다.** 이제 **안 잡으면** 「`unreported exception`」이다((2)) — 공개 API 에 나중에 달면 Java 호출자가 깨진다.
3. ★★ **「Kotlin 은 검사 예외가 없으니 예외가 덜 난다」.** 예외는 그대로 난다((1) `B`). 사라진 것은 **컴파일러의 알림**뿐이다.
4. ★★ **`TODO()` 뒤에 코드를 두고 경고를 기다린다.** 이 판은 **기본으로 경고가 없다** — `-Wextra` 에서만 나온다((5)).
5. ★★ **`finally` 에서 `return` 한다.** 던져진 예외가 **조용히 사라진다**((6) `try=T finally=R`). Kotlin 은 `-Wextra` 로도 경고하지 않는다.
6. ★ **`finally` 의 마지막 식을 값으로 쓰려 한다.** 버려진다 — 「`expression is unused`」((6)).
7. ★ **`x + TODO()` 처럼 식 가운데에 `TODO()` 를 둔다.** 오버로드 모호성((8)).
8. ★ **`Nothing` 반환 멤버를 Java 가 구현한다.** 돌아오는 순간 `KotlinNothingValueException`((7)).

## 구현 세부사항 대 언어 보장

| 항목 | 어느 쪽인가 | 근거 |
|---|---|---|
| 모든 예외가 비검사 — 잡거나 선언하지 않아도 된다 | ★★★ **언어 보장** | 문서 · (1) |
| `throw` 가 `Nothing` 타입의 식 · `Nothing` 이 모든 타입의 하위 타입 | ★★★ **언어 보장** | 문서 · (3)(4) |
| `try` 가 식 · `finally` 가 값을 안 바꾼다 | **언어 보장** | 문서 · (6) |
| `finally` 의 `return`/`throw` 가 끝을 바꿔 쥔다 | **언어 규칙**(Java·JS 와 같다) | (6) — 격자 |
| `@Throws` → **`Exceptions:` 속성** | ★ **JVM 백엔드의 구현** — 애너테이션의 목적은 문서가, 속성 이름은 JVM 이 정한다 | (2) |
| Java 가 `catch` 를 거부하는 것 | ★ **`javac` 의 규칙**(Java 언어) — Kotlin 이 아니다 | (2) |
| `Nothing` → **`java.lang.Void`** | ★★ **JVM 백엔드의 구현** | (3) |
| `Nothing` 호출 뒤의 **`KotlinNothingValueException` 검문** | ★★ **JVM 백엔드의 구현** | (3)(7) |
| `TODO()` 가 펼쳐져 `new NotImplementedError` 가 되는 것 | **stdlib 의 선택**(`inline`) | (3) |
| 「도달 불가」 경고가 `-Wextra` 에서만 | ★ **이 판(K2 2.4.20)의 관찰** | (5) |
| 교집합 타입 표기 · 진단 문구 | **이 판의 산출물** | (4)(8) |

★★ **가장 조심할 자리** — 「`throw` 의 타입이 `Nothing`」은 언어가 약속하지만, **「그래서 JVM 에서 `Void` 다」는 약속이 아니다.** 같은 코드가 JS·Native 백엔드에서 무엇이 되는지는 이 문서가 **재지 않았다.**

## 언제 쓰고 언제 안 쓰나

| 상황 | 고르는 것 | 왜 |
|---|---|---|
| Java 가 부를 공개 함수가 검사 예외를 던진다 | ★ `@Throws` | (2) — 없으면 Java 가 잡지도 못한다 |
| 없으면 여기서 끝낸다 | `?: throw` · `?: return` · `?: error(…)` | (3)(4) — 뒤는 non-null |
| 「불가능한 경우」 가지 | `error("…")` · 직접 만든 `Nothing` 함수 | (3) — 타입 추론을 안 흐린다 |
| 아직 안 만든 몸통 | `TODO()` 를 **몸통 전체**에 | (8) — 식 가운데는 모호성 |
| 실패를 값으로 넘긴다 | `runCatching`·`Result` | **컴파일러가 강제하지 않는 관용구**다([`../../언어-특성/README.md`](../../언어-특성/README.md) §8) |
| 정리 작업 | `finally` — **`return`·`throw` 금지** | (6) — 예외가 사라진다 |
| 경고로 도달 불가를 잡고 싶다 | `-Wextra` | (5) |

## 핵심 문장

1. Kotlin 에는 검사 예외가 없다 — 같은 `throws IOException` 메서드를 **Java 는 안 잡으면 컴파일 에러, Kotlin 은 통과**다.
2. 반대로 Kotlin 함수를 Java 가 부를 때 `@Throws` 가 없으면 **Java 는 그 예외를 `catch` 조차 못 한다** — 클래스 파일에 `Exceptions:` 가 없기 때문이다.
3. `throw` 는 **`Nothing` 타입의 식**이다 — 바닥 타입이라 `?:`·`if` 의 한쪽에 오면 **다른 쪽 타입이 그대로** 남는다.
4. JVM 에서 `Nothing` 은 `Void` 이고, 호출 뒤에 **`KotlinNothingValueException` 검문**이 심긴다 — 돌아오면 안 되는 것이 돌아오는 경우를 막는다.
5. `try` 는 식이고 `finally` 는 **값을 못 바꾼다** — 하지만 `return`·`throw` 로 끝나면 **끝을 바꿔 쥔다**(9칸 중 6칸).

## 관련 자료

- [`../../언어-특성/README.md`](../../언어-특성/README.md) §8 — ★★★ **검사 예외 폐지의 논지.** 그쪽은 「무엇을 얻고 무엇을 떠넘겼나」까지, 여기는 「**컴파일러와 클래스 파일에 어떻게 보이나**」부터.
- [`../../../java/syntax/25-exceptions/`](../../../java/syntax/25-exceptions/) — ★★ **짝.** Java 의 검사/비검사 규칙과 전파 문법. (1)(2)의 `javac` 문구의 정본.
- [06번 주제](../06-when-expression/) — `when` 가지의 `throw`. `NoWhenBranchMatchedException` 의 `athrow` 도 거기.
- [03번 주제](../03-null-safe-types/) — `?:` 오른쪽의 `return`·`throw` 관용구. (3)(4)가 그 근거를 채운다.
- [28번 주제](../28-generics-variance-in-out-star-where/) — 공변. (3)의 `E 0`.
- 목록의 **39번 주제** — `@Throws` 를 포함한 Java 상호운용 애너테이션 하나하나.
- [`../../../rust/syntax/06-functions-and-never-type/`](../../../rust/syntax/06-functions-and-never-type/) · [`../../../ts/syntax/04-any-unknown-never-void/`](../../../ts/syntax/04-any-unknown-never-void/) · [`../../../go/syntax/23-error-interface-and-errors-as-values/`](../../../go/syntax/23-error-interface-and-errors-as-values/) · [`../../../js/syntax/32-error-handling-and-error/`](../../../js/syntax/32-error-handling-and-error/) — 바닥 타입·오류 값·`finally` 격자의 다른 언어 판.

## 용어 풀이

> **검사 예외(checked exception)** — 부르는 쪽이 **잡거나 다시 선언해야** 컴파일되는 예외. Java 의 `Exception` 하위(단 `RuntimeException` 제외). Kotlin 에는 없다.

> **`@Throws`** — Kotlin 함수가 던지는 예외를 **Java 에게 알리는** 애너테이션. 클래스 파일의 `Exceptions:` 속성이 된다.\
> 예: `@Throws(IOException::class) fun read(): String`.

> **`Exceptions:` 속성** — 클래스 파일에서 메서드의 `throws` 목록을 담는 곳. `javac` 가 이것을 읽어 검사 예외 규칙을 적용한다.

> **`Nothing`** — 값이 **하나도 없는** 타입. 돌아오지 않는 식(`throw`·`return`·`TODO()`)의 타입이고 **모든 타입의 하위 타입**이다.

> **바닥 타입(bottom type)** — 타입 계층의 맨 아래. 어디에나 대입된다. Kotlin `Nothing` · Rust `!` · TS `never`.

> **`Nothing?`** — 값이 `null` **하나뿐인** 타입. `null` 리터럴의 타입.

> **`KotlinNothingValueException`** — `Nothing` 을 돌려준다던 호출이 **돌아왔을 때** kotlinc 가 심은 검문이 던지는 예외.

> **`finally`** — `try` 가 어떻게 끝나든 도는 블록. **값은 못 바꾸지만** `return`·`throw` 로 **끝을 바꿔 쥘 수** 있다.

## 더 들어가면

- **왜 `Void` 인가** — JVM 의 메서드는 반드시 무언가를 반환하는 서명을 가져야 한다(`V` 조차 「반환 없음」이지 「돌아오지 않음」이 아니다). `Nothing` 을 `V`(void)로 내리면 `?: die()` 같은 **식 자리**에 쓸 수 없으므로, **참조 타입이면서 값이 `null` 하나뿐인 `Void`** 가 가장 가까운 자리다. 그 `null` 이 실제로 흘러나오는 경우를 막는 것이 (7)의 검문이다.
- **검사 예외가 있었다면 람다는 어떻게 되나** — `(Int) -> Int` 같은 함수 타입에는 **예외 목록을 적을 칸이 없다**([36번 주제](../36-function-types-fun-interface-and-sam-conversion/)의 `Function1`). Java 가 `Function<T,R>` 안에서 검사 예외를 던지지 못해 감싸기를 반복하는 것이 그 비용이고, 이 논점은 [`../../언어-특성/README.md`](../../언어-특성/README.md) §8 이 정본이다.
