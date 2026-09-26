# kotlin/syntax/27 — 중첩 클래스와 `inner` — 기본값이 뒤집힌 또 한 곳 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 선행은 [15번 주제](../15-class-declaration-constructors-and-init/)다. [19번 주제](../19-inheritance-open-final-override/)(`final` 기본값)를 먼저 보면 「뒤집힌 기본값」의 결이 보인다.
> ★ Java 쪽 짝은 [`../../../java/syntax/12-nested-classes/`](../../../java/syntax/12-nested-classes/)다 — 이 주제는 **Java 를 같은 모양으로 짜서 나란히** 던졌다.
> 문항 10개 중 코드블록이 붙는 예측형은 5개다.
> 바이트코드를 묻는 문항은 **kotlinc 기본 `-jvm-target` 1.8 · javac 기본 `--release` 21** 기준이다.
> 이 주제의 모든 답은 **kotlinc 2.4.20 · JDK 21.0.5** 에서 실제로 던져 받은 것이다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★★ 네 클래스 중 `this$0` 을 가진 것 (예측)

```kotlin
// nestgrid.kt
class Outer(val name: String) {
    class Nested {
        fun hi() = "nested — 바깥을 모른다"
    }
    inner class Inner {
        fun hi() = "inner — 바깥은 $name"
    }
}

fun main() {
    println(Outer.Nested().hi())
    println(Outer("o1").Inner().hi())
}
```

```java
// NestGrid.java
public class NestGrid {
    String name = "j1";

    static class SNested {
        String hi() { return "static nested — 바깥을 모른다"; }
    }

    class JInner {
        String hi() { return "inner — 바깥은 " + name; }
    }

    public static void main(String[] args) {
        System.out.println(new SNested().hi());
        System.out.println(new NestGrid().new JInner().hi());
    }
}
```

- `javap -p` 로 `Outer$Nested` · `Outer$Inner` · `NestGrid$SNested` · `NestGrid$JInner` 를 보면 **어느 것에 `this$0` 필드**가 있는가?
- 그런 클래스의 **생성자**는 무엇을 인자로 받는가?

### 2. ★★ `inner` 없이 바깥을 쓰거나 둘 수 없는 자리에 두면 (예측)

```kotlin
// nestbad.kt
class Outer(val name: String) {
    class Nested {
        fun hi() = "nested of $name"
    }
}

interface Shape {
    inner class Part
}

object Registry {
    inner class Entry
}

class Host {
    companion object {
        inner class X
    }
}
```

- 에러가 **몇 줄**이고 각각 무엇을 말하는가?
- ★ 진단이 두 가지 `object` 를 **어떤 낱말로** 갈라 부르는가?

### 3. ★ 만드는 쪽이 틀리면 (예측)

```kotlin
// nestctor.kt
class Outer {
    class Nested
    inner class Inner
}

fun main() {
    val a = Outer.Inner()
    val b = Outer().Nested()
}
```

- 두 줄이 각각 어떤 에러를 내는가? 올바른 꼴은 무엇인가?

### 4. ★★★ 바깥을 한 번도 안 쓰는 「잡는 꼴」 (예측)

```kotlin
// nestunused.kt
class Quiet {
    inner class Unused {
        fun hi() = "바깥을 한 번도 안 쓴다"
    }
}
```

```java
// NestUnused.java
public class NestUnused {
    class Unused {
        String hi() { return "바깥을 한 번도 안 쓴다"; }
    }
}
```

- kotlinc 2.4.20 이 만든 `Quiet$Unused` 에 `this$0` 이 있는가?
- javac 21 기본으로 만든 `NestUnused$Unused` 에는? ★ `--release 17` 로 만들면?
- 셋의 **생성자**는 바깥을 인자로 받는가?

### 5. ★★ 익명 객체와 람다는 언제 바깥을 잡나 (예측)

```kotlin
// nestanon.kt
interface Greeter { fun greet(): String }

class Host(val name: String) {
    fun usesOuter(): Greeter = object : Greeter {
        override fun greet() = "hi from $name"
    }
    fun ignoresOuter(): Greeter = object : Greeter {
        override fun greet() = "hi"
    }
    fun lambdaUses(): () -> String = { "lambda $name" }
    fun lambdaIgnores(): () -> String = { "lambda" }
}

fun main() {
    val h = Host("h")
    println("A ${h.usesOuter().greet()}")
    println("B ${h.ignoresOuter().greet()}")
    println("C ${h.lambdaUses()()}")
    println("D ${h.lambdaIgnores()()}")
}
```

- `Host$usesOuter$1` 과 `Host$ignoresOuter$1` 중 `this$0` 을 가진 것은?
- 두 람다의 `invokedynamic` 서명은 각각 무엇을 넘겨받는가?
- ★ 4번의 `inner` 와 비교하면 규칙이 어떻게 다른가?

### 6. Java 와 기본값이 **반대**인 것 (왜)

- 1번의 격자를 근거로 — Kotlin 의 `class B` 와 Java 의 `class B` 는 왜 **정반대**인가?
- 이 갈래에서 **기본값이 뒤집힌 앞의 자리들**을 셋 대 보라. 네 곳의 공통점은?

### 7. inner 객체가 바깥을 붙잡는다는 것의 정확한 뜻 (경계)

- [2-summary](2-summary.md) (4)의 `makeInner()` 가 돌려준 `Listener` 에서 무엇을 따라가면 `Screen` 이 나오는가?
- ★★ 그 블록이 **증명한 것**과 **증명하지 않은 것**을 갈라 보라.

### 8. `this@Outer` (경계)

- `inner class Inner(val name: String)` 안에서 `$name` 과 `${this@Outer.name}` 은 각각 누구의 것인가?
- Java 의 어떤 꼴과 대응하는가?

### 9. `this$0` 은 언어의 것인가 (경계)

- 「`inner` 는 바깥을 참조한다」와 「`inner` 에는 `this$0` 필드가 생긴다」 중 **언어 보장**은 어느 쪽인가?
- 4번의 갈림(kotlinc 는 남기고 javac 21 은 버린다)이 **둘 다 합법**인 이유는?

### 10. 언제 중첩, 언제 `inner` (연결)

- 오래 사는 이벤트 버스에 등록할 콜백을 만들 때 어느 꼴을 고르고 무엇을 인자로 넘기는가?
- [25번 주제](../25-object-declaration-companion-and-object-expression/)의 `Outer$Companion` 은 이 주제의 어느 칸에 들어가는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
