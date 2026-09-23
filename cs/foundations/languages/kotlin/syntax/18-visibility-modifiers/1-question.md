# kotlin/syntax/18 — 가시성 수식어: `internal` 이 Java 에 없는 이유 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 선행은 [15번 주제](../15-class-declaration-constructors-and-init/)다.
> ★ **클래스·생성자 선언 형태는 [15번 주제](../15-class-declaration-constructors-and-init/)**, `open`/`override` 는 [19번 주제](../19-inheritance-open-final-override/),
> `@JvmName` 을 비롯한 상호운용 애너테이션 전반은 목록의 **39번 주제**가 정본이다.
> Java 의 네 단계는 [`../../../java/syntax/10-access-modifiers/`](../../../java/syntax/10-access-modifiers/)가 정본이다 — 여기는 **그 자리에 `internal` 을 끼운 결과**만 묻는다.
> 문항 12개 중 코드블록이 붙는 예측형은 6개다.
> 바이트코드를 묻는 문항은 **`kotlinc` 기본 `-jvm-target`(1.8)** 기준이다.
> 이 주제의 모든 답은 **kotlinc 2.4.20 · JRE 21.0.5** 에서 실제로 던져 받은 것이다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★ 한 파일 안에서 네 수식어가 각각 어디까지 보이나 (예측)

```kotlin
// vis.kt
public fun topPublic() = "topPublic"
internal fun topInternal() = "topInternal"
private fun topPrivate() = "topPrivate"

private val topPrivateVal = "topPrivateVal"

open class Box(private val secret: String) {
    public val open1 = "public 멤버"
    internal val open2 = "internal 멤버"
    protected val open3 = "protected 멤버"
    private val open4 = "private 멤버"

    fun peek() = "$open1 / $open2 / $open3 / $open4 / $secret"
}

class SubBox : Box("상위의 private") {
    fun fromSub() = "하위가 보는 것 : $open3"
}

fun main() {
    println("A ${topPublic()} / ${topInternal()} / ${topPrivate()} / $topPrivateVal")
    println("B ${Box("s").peek()}")
    println("C ${SubBox().fromSub()}")
    val b = Box("s")
    println("D 바깥에서 보이는 것 : ${b.open1} / ${b.open2}")
}
```

- `A`·`B`·`C`·`D` 네 줄에 각각 무엇이 찍히는가?
- `main()` 이 `topPrivate()` 을 부를 수 있는 이유는 무엇인가?
- `SubBox` 가 `open4` 를 못 보는 이유는 무엇인가?
- 아무 수식어도 안 붙은 `fun peek()` 의 가시성은 무엇인가?

### 2. ★★ 최상위 선언 앞에 `protected` 를 적으면 (예측)

```kotlin
// toplevel.kt
protected fun topProtected() = "안 된다"

class Holder {
    protected fun m() = "클래스 안에서는 된다"
}
```

- 컴파일되는가? 에러라면 **몇 건**이고 **어느 줄**인가?
- 에러 문구는 「접근할 수 없다」인가 「그 자리에 쓸 수 없다」인가 — 이 차이가 왜 중요한가?
- `class Holder` 안의 `protected` 는 어떻게 되는가?

### 3. ★★ 같은 모듈·같은 컴파일인데 다른 파일에서 최상위 `private` 을 부르면 (예측)

```kotlin
// priv1.kt
private fun onlyInThisFile() = "priv1.kt 안에서만 보인다"

internal fun sameModule() = "같은 모듈이면 보인다"

fun callItHere() = onlyInThisFile()
```

```kotlin
// priv2.kt
fun probe(): String {
    println(sameModule())
    println(onlyInThisFile())
    return "끝"
}
```

- 두 파일을 **한 번에** 컴파일하면 통과하는가?
- `sameModule()` 과 `onlyInThisFile()` 중 어느 쪽이 막히는가?
- 에러 문구의 「in file」 자리에 클래스 멤버였다면 무엇이 오는가?

### 4. ★★★ 같은 두 파일을 따로 컴파일한 것과 같이 컴파일한 것 (예측)

```kotlin
// moda.kt
public fun modaOpen() = "moda 의 public — 안에서 internal 을 부른다 : " + modaSecret()

internal fun modaSecret() = "moda 의 internal"

class Tool {
    internal fun helper() = "Tool.helper (internal 멤버)"
    fun use() = "같은 모듈 안에서는 : " + helper()
}
```

```kotlin
// modb.kt
fun main() {
    println("A " + modaOpen())
    println("B " + Tool().use())
    println("C " + modaSecret())
    println("D " + Tool().helper())
}
```

- `kotlinc moda.kt` → `kotlinc modb.kt -cp omoda` 로 **나눠** 던지면 무엇이 나오는가?
- 같은 두 파일을 `kotlinc moda.kt modb.kt` 로 **한 번에** 던지면 무엇이 나오는가?
- 소스가 한 글자도 안 바뀌었는데 결과가 갈린다면, **모듈 경계는 무엇인가**?
- `modaOpen()` 은 왜 모듈 밖에서 보이는가 — 그 몸통이 `internal` 을 부르는데도?

### 5. ★★★ `javap` 로 본 `internal` 은 무엇으로 되어 있나 (예측)

```kotlin
// mangle.kt
internal class Hidden {
    internal fun onlyHere() = "Hidden.onlyHere"
}

open class Named {
    internal fun plain() = "plain"

    @JvmName("renamed")
    internal fun withJvmName() = "withJvmName"

    protected fun prot() = "prot"
    private fun priv() = "priv"
    fun use() = priv()
}
```

- `Hidden` 클래스의 **접근 수식어**는 무엇으로 나오는가?
- `plain()`·`withJvmName()`·`prot()`·`priv()` 는 각각 **어떤 이름과 어떤 수식어**로 나오는가?
- `-module-name` 을 안 주면 접미가 어떻게 바뀌는가?
- 최상위 `internal` 함수(`modaSecret()`)도 같은 접미가 붙는가?

### 6. ★★ Java 파일을 섞어 컴파일하면 `internal` 이 보이나 (예측)

```java
// UseInternal.java
public class UseInternal {
    public static void main(String[] args) {
        System.out.println("A " + ModaKt.modaOpen());
        System.out.println("B " + ModaKt.modaSecret());
        System.out.println("C " + new Tool().helper$moda());
    }
}
```

- `javac` 는 통과하는가 — **경고는 몇 건**인가?
- `B`·`C` 줄에 무엇이 찍히는가?
- 같은 이름을 **Kotlin 쪽에서** 백틱으로 감싸 부르면 어떻게 되는가?
- 그래서 `internal` 을 막는 것은 **누구**인가?

### 7. `@JvmName` 을 붙이면 왜 뭉개기가 사라지나 (왜)

- 이름 뭉개기가 애초에 **무엇을 하려고** 있는 장치인가?
- `@JvmName` 을 붙인 사람이 컴파일러에게 한 말을 한 문장으로 옮겨 보라.
- 그 결과 **모듈 울타리 쪽에서는 무엇이 사라지는가**?

### 8. `internal` 을 보안 경계로 쓸 수 있나 (경계)

- 「보안 경계」와 「실수 방지」를 가르는 기준은 무엇인가?
- Kotlin 컴파일러를 **안 거치는** 경로를 셋 이상 대 보라.
- 그럼 진짜로 막으려면 무엇이 필요한가?

### 9. 최상위 `private` 과 Java 의 package-private 은 무엇이 다른가 (경계)

- 같은 폴더의 다른 파일에서 보이는가?
- 같은 패키지 선언(`package a.b`)을 쓴 다른 파일에서는?
- 이 둘이 헷갈리면 어떤 버그가 아니라 어떤 **불편**이 생기는가?

### 10. ★ 공개 함수가 좁은 타입을 내놓으면 (경계)

```kotlin
// forbid18.kt
private class Secret(val v: Int)

fun leak(): Secret = Secret(1)

internal class Half(val v: Int)

public fun half(): Half = Half(1)

class Box2 {
    private val hidden = 1
}

fun outside(b: Box2) = b.hidden
```

- 에러는 몇 건이고 각각 어느 규칙을 어긴 것인가?
- 「`public` 함수가 `private-in-file` 반환 타입을 노출한다」는 말이 막으려는 사고는 무엇인가?
- 세 번째 에러는 앞의 둘과 성격이 어떻게 다른가?

### 11. Java 의 네 단계와 짝지으면 어디가 빈칸인가 (연결)

- Java 의 `public`·`protected`·package-private·`private` 을 Kotlin 의 넷과 짝지어 보라.
- **짝이 없는 칸**은 어느 쪽에 몇 개인가?
- Kotlin 의 `protected` 가 Java 의 `protected` 보다 **좁은** 이유는 무엇인가?

### 12. 가시성이 오버라이드에서 어느 방향으로 움직이나 (연결)

- 상위의 `protected` 멤버를 하위에서 `public` 으로 넓힐 수 있는가?
- 반대로 `public` 을 `protected` 로 좁힐 수 있는가?
- 그 규칙이 [19번 주제](../19-inheritance-open-final-override/)의 어느 결론과 같은 뿌리인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
