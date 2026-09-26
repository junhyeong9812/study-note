# kotlin/syntax/27 — 중첩 클래스와 `inner` — 기본값이 뒤집힌 또 한 곳 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 모든 출력·에러·바이트코드는 **kotlinc 2.4.20 (JRE 21.0.5)** 과 Temurin **JDK 21.0.5** 의 `javap`·`javac` 에서 실제로 얻었다.\
> 역어셈블은 **kotlinc 기본 `-jvm-target` 1.8 · javac 기본 `--release` 21** 이 정본이다(4번만 `--release 17` 을 더 찍었다).
> ★★ 아래 블록은 전부 **캡처 스크립트가 파일로 받아** 조립한 것이다 — 사람이 옮겨 적은 자리가 없다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ `Outer$Inner` 와 `NestGrid$JInner` — Kotlin 은 **적은 꼴**, Java 는 **안 적은 꼴**

**출력**

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

```text
===== kotlinc nestgrid.kt -d o27g =====
(exit 0)
===== java -cp o27g:kotlin-stdlib.jar NestgridKt =====
nested — 바깥을 모른다
inner — 바깥은 o1
(exit 0)
===== javac -d o27g NestGrid.java =====
(exit 0)
===== java -cp o27g NestGrid =====
static nested — 바깥을 모른다
inner — 바깥은 j1
(exit 0)
```

```text
===== javap -p 'o27g/Outer$Nested.class' 'o27g/Outer$Inner.class' 'o27g/NestGrid$SNested.class' 'o27g/NestGrid$JInner.class' =====
Compiled from "nestgrid.kt"
public final class Outer$Nested {
  public Outer$Nested();
  public final java.lang.String hi();
}
Compiled from "nestgrid.kt"
public final class Outer$Inner {
  final Outer this$0;
  public Outer$Inner(Outer);
  public final java.lang.String hi();
}
Compiled from "NestGrid.java"
class NestGrid$SNested {
  NestGrid$SNested();
  java.lang.String hi();
}
Compiled from "NestGrid.java"
class NestGrid$JInner {
  final NestGrid this$0;
  NestGrid$JInner(NestGrid);
  java.lang.String hi();
}
(exit 0)
```

**왜 그런가**

```text
                 안 적은 꼴                 적은 꼴
   Kotlin        class Nested   없음        inner class Inner    this$0 있음
   Java          class JInner   있음        static class SNested  없음
```

- ★★★ **`this$0` 이 있는 것은 `Outer$Inner`(Kotlin `inner`)와 `NestGrid$JInner`(Java 비정적)** 다. 같은 JVM 장치를 **정반대 기본값**으로 쓴다.
- ★★ 그런 클래스의 생성자는 **바깥을 인자로 받는다** — `Outer$Inner(Outer)` · `NestGrid$JInner(NestGrid)`.
- 출력 네 줄은 **차이를 하나도 안 보인다** — 셋째 창(`javap`)이 본체인 이유다.

### 2. ★★ 에러 네 줄 — 바깥을 수신자로 못 씀 · 인터페이스 · `standalone object` · `companion object`

**출력**

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

```text
===== kotlinc nestbad.kt -d o27b =====
nestbad.kt:3:32: error: outer class 'class Outer : Any' of non-inner class cannot be used as receiver.
        fun hi() = "nested of $name"
                               ^^^^
nestbad.kt:8:5: error: modifier 'inner' is not applicable inside 'interface'.
    inner class Part
    ^^^^^
nestbad.kt:12:5: error: modifier 'inner' is not applicable inside 'standalone object'.
    inner class Entry
    ^^^^^
nestbad.kt:17:9: error: modifier 'inner' is not applicable inside 'companion object'.
        inner class X
        ^^^^^
(exit 1)
```

**왜 그런가**

- ★★★ 첫 줄 「`outer class 'class Outer : Any' of non-inner class cannot be used as receiver.`」 — **중첩 클래스에는 바깥 인스턴스가 없으므로** `name` 의 주인을 정할 수 없다. Java 라면 **조용히 컴파일되고 `this$0` 이 생겼을** 자리다.
- 인터페이스·`object`·`companion object` 는 **잡을 바깥 인스턴스가 없거나 하나뿐**이다 — `inner` 가 뜻이 없다.
- ★ 진단이 **`standalone object`** 와 **`companion object`** 로 두 `object` 를 갈라 부른다.

### 3. ★ `Outer.Inner()` 는 「바깥 수신자가 있어야 한다」, `Outer().Nested()` 는 「그런 이름이 없다」

**출력**

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

```text
===== kotlinc nestctor.kt -d o27c =====
nestctor.kt:7:19: error: constructor of the inner class 'inner class Inner : Any' can only be called with a receiver of the containing class.
    val a = Outer.Inner()
                  ^^^^^
nestctor.kt:8:21: error: unresolved reference 'Nested' on receiver of type 'Outer'.
    val b = Outer().Nested()
                    ^^^^^^
(exit 1)
```

**왜 그런가**

- ★★ inner 의 생성자는 **바깥을 인자로 받으므로**(1번의 `Outer$Inner(Outer)`) **`outer.Inner()`** 로만 만든다.
- 중첩은 **타입 이름을 거쳐** `Outer.Nested()` 로 만든다 — 인스턴스를 거치면 「`unresolved reference 'Nested' on receiver of type 'Outer'.`」.

### 4. ★★★ kotlinc 는 **남기고**, javac 21 은 **버리고**, `--release 17` 은 **남긴다** — 생성자는 셋 다 바깥을 받는다

**출력**

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

```text
===== kotlinc nestunused.kt -d o27u =====
(exit 0)
===== javac -d o27u NestUnused.java =====
(exit 0)
===== javac --release 17 -d o27u17 NestUnused.java =====
(exit 0)
===== javap -p 'o27u/Quiet$Unused.class' 'o27u/NestUnused$Unused.class' 'o27u17/NestUnused$Unused.class' =====
Compiled from "nestunused.kt"
public final class Quiet$Unused {
  final Quiet this$0;
  public Quiet$Unused(Quiet);
  public final java.lang.String hi();
}
Compiled from "NestUnused.java"
class NestUnused$Unused {
  NestUnused$Unused(NestUnused);
  java.lang.String hi();
}
Compiled from "NestUnused.java"
class NestUnused$Unused {
  final NestUnused this$0;
  NestUnused$Unused(NestUnused);
  java.lang.String hi();
}
(exit 0)
```

**왜 그런가**

- ★★★ **kotlinc 는 `inner` 라고 적었으면 안 써도 `this$0` 을 둔다** — 적은 대로 한다.
- ★★ **javac 는 목표 릴리스에 따라 갈린다** — 21 기본은 필드를 버렸고 `--release 17` 은 남겼다. 같은 컴파일러·같은 소스다. [Java 12번](../../../java/syntax/12-nested-classes/) (6)이 익명 클래스로 본 17↔21 갈림과 같은 집안이다.
- ★ 생성자는 **셋 다 바깥을 받는다** — javac 21 은 **받고 저장만 안 한다.**
- 그래서 「안 쓰면 안 잡는다」에 기대지 마라. **안 잡으려면 Kotlin 은 `inner` 를 안 적고 Java 는 `static` 을 적는다.**

### 5. ★★ **쓴 쪽만** 잡는다 — `usesOuter` 에만 `this$0`, 람다는 `(LHost;)` 대 `()`

**출력**

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

```text
===== kotlinc nestanon.kt -d o27a =====
(exit 0)
===== java -cp o27a:kotlin-stdlib.jar NestanonKt =====
A hi from h
B hi
C lambda h
D lambda
(exit 0)
```

```text
===== javap -p 'o27a/Host$usesOuter$1.class' 'o27a/Host$ignoresOuter$1.class' =====
Compiled from "nestanon.kt"
public final class Host$usesOuter$1 implements Greeter {
  final Host this$0;
  Host$usesOuter$1(Host);
  public java.lang.String greet();
}
Compiled from "nestanon.kt"
public final class Host$ignoresOuter$1 implements Greeter {
  Host$ignoresOuter$1();
  public java.lang.String greet();
}
(exit 0)
```

```text
===== javap -c -p o27a/Host.class | grep -E '^  public final|invokedynamic' =====
  public final java.lang.String getName();
  public final Greeter usesOuter();
  public final Greeter ignoresOuter();
  public final kotlin.jvm.functions.Function0<java.lang.String> lambdaUses();
       1: invokedynamic #60,  0             // InvokeDynamic #0:invoke:(LHost;)Lkotlin/jvm/functions/Function0;
  public final kotlin.jvm.functions.Function0<java.lang.String> lambdaIgnores();
       0: invokedynamic #67,  0             // InvokeDynamic #1:invoke:()Lkotlin/jvm/functions/Function0;
(exit 0)
```

**왜 그런가**

- ★★★ **익명 객체는 바깥을 쓸 때만** `this$0` 과 `(Host)` 생성자를 갖는다.
- ★★ 람다는 필드 대신 **`invokedynamic` 의 인자**로 넘겨받는다 — 쓰면 `(LHost;)`, 안 쓰면 `()`.
- ★ 4번과의 차이 — **`inner` 는 적은 대로**(안 써도 잡는다), **익명 객체·람다는 쓴 대로**다.

### 6. 같은 JVM 장치를 **반대 기본값**으로 쓴다 — 앞의 자리들은 03 null 불가 · 18 `public` · 19 `final`

- Kotlin 의 `class B` 는 Java 의 **`static class B`** 와 같은 칸이고, Java 의 `class B` 는 Kotlin 의 **`inner class B`** 와 같은 칸이다(1번 격자).
- 앞의 뒤집힌 자리 — [03번](../03-null-safe-types/)(참조가 **null 불가**가 기본) · [18번](../18-visibility-modifiers/)(**`public`** 이 기본) · [19번](../19-inheritance-open-final-override/)(**`final`** 이 기본).
- ★ 공통점 — 03·19·27 은 **적지 않으면 좁은 쪽**(null 못 담음·상속 못 함·바깥 못 잡음)이다. 18 만 넓은 쪽으로 갔다.

### 7. `this$0` 을 따라가면 `Screen` 이 나온다 — **참조가 있다**는 증명이고 **메모리가 샌다**는 증명은 아니다

```text
===== kotlinc nestref.kt -d o27r =====
(exit 0)
===== java -cp o27r:kotlin-stdlib.jar NestrefKt =====
A inner  -> title=home pixels=1000000
B nested -> null
(exit 0)
```

- ★★★ `makeInner()` 가 돌려준 것은 `Listener` 하나인데, 그 **`this$0` 필드값이 `Screen("home")`** 이었다(`pixels=1000000`). `Screen` 을 담은 변수는 없다.
- ★★ 증명한 것 — **`Listener` 가 사는 동안 `Screen` 에 닿을 수 있다.** 증명하지 않은 것 — **GC 가 실제로 못 거두는지·얼마가 남는지.** 그 관찰은 [Java 12번](../../../java/syntax/12-nested-classes/) (6)이 GC 를 돌려서 했다.
- 그 블록의 소스는 [2-summary](2-summary.md) (4)의 `nestref.kt` 다.

### 8. `$name` 은 inner 자기 것, `this@Outer.name` 은 바깥 것 — Java 의 `Outer.this.name`

```text
===== kotlinc nestlabel.kt -d o27l =====
(exit 0)
===== java -cp o27l:kotlin-stdlib.jar NestlabelKt =====
A a/O inner-tag/outer-tag
B b/O inner-tag/outer-tag
C c/P inner-tag/outer-tag
(exit 0)
```

- 이름이 겹치면 **가장 안쪽이 이긴다** — `a`·`inner-tag`. **`this@Outer`** 가 바깥을 지목한다 — `O`·`outer-tag`.
- 같은 바깥에서 만든 `i1`·`i2` 는 **같은 `O`** 를 본다. 소스는 [2-summary](2-summary.md) (5)의 `nestlabel.kt` 다.

### 9. 「참조한다」가 언어 보장이고 `this$0` 은 구현이다 — 그래서 남겨도 버려도 합법이다

- 언어가 약속하는 것은 **「`inner` 는 바깥 인스턴스를 참조할 수 있다」·「중첩은 못 한다」** 까지다. 그 참조를 **필드 하나로 사는 모양**(`this$0`)으로 만든 것은 JVM 위의 구현이다.
- 바깥을 **안 쓰는** 코드에서 참조를 남기든 버리든 **프로그램의 뜻은 같다** — 그래서 kotlinc 의 선택(남김)도 javac 21 의 선택(버림)도 규칙 위반이 아니다. **그러니 어느 쪽에도 기대지 마라.**

### 10. **중첩 + 필요한 값만 인자로** — `Outer$Companion` 은 「안 잡는 칸」이다

- 오래 사는 곳에 등록할 콜백은 **`inner` 로 만들지 않는다.** 바깥 전체에 닿는 참조가 따라가기 때문이다(7번). 필요한 값만 생성자 인자로 넘기는 **중첩 클래스**로 만든다.
- [25번 주제](../25-object-declaration-companion-and-object-expression/)의 `Outer$Companion` 은 **바깥 인스턴스를 안 잡는 정적 중첩 모양**이다 — 그래서 `inner companion object` 가 막혔고, 2번에서 **그 안에 둔 `inner class`** 도 막혔다.

## 실행 검증

```text
===== kotlinc -version =====
info: kotlinc-jvm 2.4.20 (JRE 21.0.5+11-LTS)
(exit 0)
```

```text
===== java -version =====
openjdk version "21.0.5" 2024-10-15 LTS
OpenJDK Runtime Environment Temurin-21.0.5+11 (build 21.0.5+11-LTS)
OpenJDK 64-Bit Server VM Temurin-21.0.5+11 (build 21.0.5+11-LTS, mixed mode, sharing)
(exit 0)
```

```text
===== javac -version =====
javac 21.0.5
(exit 0)
```

★ **흔들리는 칸과 안 흔들리는 칸**

| 흔들린다 | 안 흔들린다 |
|---|---|
| **없다** — 주소·해시코드를 찍지 않았다 | `javap -p` 의 **필드·생성자 목록** · `invokedynamic` 서명 |
| | 컴파일 에러의 **문구·`파일:줄:칸`** · 익명 클래스 이름 |
| | 모든 **종료 코드** · 출력 |

> 근거 — 캡처 스크립트를 처음부터 다시 돌려 **블록 전체를 바이트 단위로 대조**했다.
>
> 실측 — `capture.sh blocks` 와 `capture.sh blocks-recheck` 를 처음부터 따로 돌려 `normalize-shaky.py` 로 대조했다 —\
> **블록 101개 · 동일 101 · 흔들린 칸 0 · ★고칠 것 0**(26\~29 네 주제를 한 캡처로 받았다). `diff -rq` 도 차이 0 이다.\
> ★ **정규화 규칙은 하나도 안 썼다** — 기본 넷(주소·PID·스레드 id·시간)에 걸리는 칸이 애초에 없었다.

| 프로그램 | 무엇을 확인했나 | 돌린 방법 |
|---|---|---|
| `nestgrid.kt` + `NestGrid.java` | ★★★ **네 칸 격자** — 누가 `this$0` 을 갖나 | `kotlinc`·`javac` → `java` → `javap -p` |
| `nestunused.kt` + `NestUnused.java` | ★★★ **안 쓰는 바깥 참조** — kotlinc · javac 21 · `--release 17` | `kotlinc` · `javac` 두 판 → `javap -p` |
| `nestref.kt` | ★★ 참조가 **실제로 바깥 객체를 가리키는가**(리플렉션) | `kotlinc` → `java` |
| `nestbad.kt` | `inner` 없이 바깥 사용 · 인터페이스·`object`·companion 안의 `inner` | `kotlinc`(컴파일 실패가 결과) |
| `nestctor.kt` | 만드는 쪽의 규칙 | `kotlinc`(컴파일 실패가 결과) |
| `nestlabel.kt` | `this@Outer` · 이름 가림 | `kotlinc` → `java` |
| `nestanon.kt` | ★★ 익명 객체·람다가 **쓴 만큼** 잡는 것 | `kotlinc` → `java` → `javap -p` · `javap -c -p`(필터) |
| `form27.kt` | 형태 한 벌(`Z`·`Y`·`X`) | `kotlinc` → `java` |

**구현 의존 항목** — `this$0` 이라는 **필드 이름과 존재**, 바깥을 받는 생성자, 안 쓰는 참조를 **남기느냐 버리느냐**(kotlinc·javac·목표 릴리스마다 다름), 익명 클래스 이름 규칙, 람다의 `invokedynamic` 서명 — 컴파일러·판의 산출물이다.\
반면 **「기본은 중첩이고 `inner` 라야 바깥을 잡는다」「inner 는 바깥 인스턴스가 있어야 만든다」「`this@Outer`」「인터페이스·`object` 안의 `inner` 금지」** 는 **언어의 계약**이다.

**★ 던져 봤더니 예상과 달랐던 것 — 두 건**

1. ★★★ **javac 21 이 바깥을 안 쓰는 멤버 클래스에서 `this$0` 을 버렸다.** 「Java 의 비정적 중첩은 늘 `this$0` 을 갖는다」로 격자를 짜려 했는데, 바깥을 안 쓰는 판에서는 **필드가 없었다**(`--release 17` 에서는 있었다). 그래서 1번 격자는 **바깥을 쓰는 모양**으로 짜고, 안 쓰는 모양은 4번으로 따로 세웠다.
2. ★★ **kotlinc 는 반대로 안 쓰는 `inner` 에도 `this$0` 을 남겼다.** 두 컴파일러가 같은 질문에 **다른 답**을 냈다 — 「안 쓰면 안 잡는다」는 어느 언어에서도 기대면 안 되는 성질이다.
