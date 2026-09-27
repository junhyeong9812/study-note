# kotlin/syntax/26 — `value class`(인라인 클래스) — 언제 박싱되나 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 선행은 [22번 주제](../22-data-class-generated-members/)다. [12번 주제](../12-reified-type-parameters/)(소거)를 먼저 보면 (2)가 쉽다.
> ★ 이 주제는 [29번 주제](../29-type-aliases-and-nested-type-aliases/)(`typealias`)와 짝이다 — 여기는 **새 타입을 만드는 쪽**이다.
> 문항 11개 중 코드블록이 붙는 예측형은 5개다.
> 바이트코드를 묻는 문항은 **`kotlinc` 기본 `-jvm-target`(1.8)** 기준이다.
> ★★★ 이 주제는 **시간을 묻지 않는다** — 「상자에 담기는가」는 `box-impl` 호출의 **유무**로만 묻는다.
> 이 주제의 모든 답은 **kotlinc 2.4.20 · JRE 21.0.5** 에서 실제로 던져 받은 것이다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★★ `lookup` 두 개가 JVM 에서 받는 것 (예측)

```kotlin
// vcsig.kt
@JvmInline
value class UserId(val raw: Long)

fun lookup(id: UserId): String = "user#${id.raw}"
fun lookup(raw: Long): String = "raw#$raw"
fun make(n: Long): UserId = UserId(n)

class Repo {
    fun find(id: UserId): String = "find#${id.raw}"
}

fun main() {
    val id = make(7)
    println("A ${lookup(id)}")
    println("B ${lookup(7L)}")
    println("C ${Repo().find(id)}")
    println("D ${id == UserId(7)} $id")
}
```

- 실행하면 `A`\~`D` 에 무엇이 찍히는가?
- `javap -s -p` 로 보면 `lookup(id: UserId)` 와 `lookup(raw: Long)` 의 **이름**과 **descriptor** 는 각각 무엇인가?
- ★ `make(n: Long): UserId` 의 이름은 뭉개지는가?

### 2. ★★★ 일곱 자리의 `box-impl` 개수 (예측)

```kotlin
// vcbox.kt
@JvmInline
value class Meters(val v: Double)

interface Measured { fun raw(): Double }

@JvmInline
value class Cm(val v: Double) : Measured {
    override fun raw() = v
}

@JvmInline
value class Name(val s: String)

fun plain(m: Meters): Double = m.v
fun nullable(m: Meters?): Double = m?.v ?: -1.0
fun nullableRef(n: Name?): Int = n?.s?.length ?: -1
fun viaInterface(x: Measured): Double = x.raw()
fun viaAny(a: Any): String = a.toString()
fun <T> viaGeneric(t: T): T = t

fun site0() = plain(Meters(1.0))
fun site1() = nullable(Meters(1.0))
fun site2() = nullableRef(Name("ab"))
fun site3() = viaInterface(Cm(1.0))
fun site4() = viaAny(Meters(1.0))
fun site5() = listOf(Meters(1.0))[0].v
fun site6() = viaGeneric(Meters(1.0)).v

fun main() {
    println("${site0()} ${site1()} ${site2()} ${site3()} ${site4()} ${site5()} ${site6()}")
}
```

- `site0` \~ `site6` 각각의 본문에 `box-impl` 호출이 **몇 번** 나타나는가?
- ★★ `site1` 과 `site2` 는 둘 다 nullable 을 받는다. 둘의 답이 **같은가**?
- `unbox-impl` 까지 나타나는 자리는 어디인가?

### 3. ★★ 컴파일되지 않는 값 클래스들 (예측)

```kotlin
// vcbad.kt
value class NoAnno(val v: Int)

@JvmInline
value class Two(val a: Int, val b: Int)

@JvmInline
value class VarProp(var v: Int)

@JvmInline
value class WithField(val v: Int) {
    val twice = v * 2
}

@JvmInline
value class Id(val v: Int)

fun main() {
    val a = Id(1)
    val b = Id(1)
    println(a === b)
}
```

- 에러가 **몇 줄**이고 각각 무엇을 말하는가?
- ★ 첫 에러의 문구에 들어 있는 **판에 매인 낱말**은 무엇인가?

### 4. ★ `init` 이 있는 값 클래스 (예측)

```kotlin
// vcinit.kt
@JvmInline
value class Percent(val v: Int) {
    init { require(v in 0..100) { "0..100 밖: $v" } }
    fun half() = Percent(v / 2)
}

fun main() {
    val a = Percent(40)
    val b = Percent(40)
    System.err.println("A ${a == b} ${a.hashCode() == b.hashCode()} ${a.hashCode()}")
    System.err.println("B $a ${a.half()}")
    System.err.println("C ${setOf(a, b).size}")
    System.err.println("D 직전")
    Percent(140)
    System.err.println("E 안 찍힌다")
}
```

- 표준 오류에 무엇이 어떤 순서로 찍히는가? 종료 코드는?
- 트레이스의 첫 프레임은 **어느 메서드**인가?

### 5. ★★ Java 에서 부르면 (예측)

```kotlin
// vcjava.kt
@JvmInline
value class UserId(val raw: Long) {
    init { require(raw > 0) { "양수만: $raw" } }
}

fun lookup(id: UserId): String = "user#${id.raw}"

@JvmName("lookupRaw")
fun lookupNamed(id: UserId): String = "named#${id.raw}"
```

```java
// CallIt.java
public class CallIt {
    public static void main(String[] args) {
        System.out.println(VcjavaKt.lookup(7L));
    }
}
```

```java
// CallOk.java
public class CallOk {
    public static void main(String[] args) {
        System.out.println(VcjavaKt.lookupRaw(7L));
        System.out.println(VcjavaKt.lookupRaw(-1L));
    }
}
```

- `CallIt.java` 는 컴파일되는가? 안 된다면 에러 문구는?
- `CallOk.java` 는 무엇을 찍는가? ★★ 둘째 줄에서 `init` 의 `require` 가 도는가?

### 6. 이름을 뭉개는 이유 (왜)

- 1번의 두 `lookup` 이 이름까지 같았다면 JVM 에서 무슨 일이 생기는가?
- 해시 글자는 **함수 이름**에서 오는가, **파라미터 타입**에서 오는가? 1번의 `Repo.find` 로 답해 보라.

### 7. nullable 이 박싱되는 조건 (경계)

- 「nullable 이면 박싱된다」는 왜 **반만** 맞는가?
- 알맹이가 `Double` 일 때와 `String` 일 때 `Meters?`·`Name?` 의 JVM 파라미터 타입은 각각 무엇인가?

### 8. `===` 가 금지되는 이유 (왜)

- 2번의 결과를 근거로 — 같은 값이 **어떤 자리에서는 `double`, 어떤 자리에서는 상자**라면 참조 비교의 답은 무엇에 달리게 되는가?

### 9. `box-impl` 이 보인다 = 느리다? (경계)

- 이 문서가 **안 잰 것**은 무엇인가? `box-impl` 호출의 유무로 답할 수 있는 것과 없는 것을 갈라 보라.
- 그 질문을 제대로 재려면 무엇이 필요한가?

### 10. `data class` 와 `value class` (연결)

- [22번 주제](../22-data-class-generated-members/)의 `data class` 와 **자동으로 생기는 것**이 같은 것·다른 것은 무엇인가?
- 필드가 둘이면 어느 쪽인가?

### 11. 다른 언어의 「값을 감싸는 새 타입」 (연결)

- C# `struct` 는 `List<T>` 에서 박싱되는가? Kotlin `value class` 와 왜 반대인가?
- Rust newtype 에는 왜 이 주제의 질문 자체가 없는가?
- [29번 주제](../29-type-aliases-and-nested-type-aliases/) `typealias UserId = Long` 이라면 1번의 두 `lookup` 은 어떻게 되겠는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
