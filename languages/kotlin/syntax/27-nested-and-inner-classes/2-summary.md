# kotlin/syntax/27 — 중첩 클래스와 `inner` — 기본값이 뒤집힌 또 한 곳 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Nested and inner classes](https://kotlinlang.org/docs/nested-classes.html) · [This expressions](https://kotlinlang.org/docs/this-expressions.html)(`this@Outer`) · [Object expressions](https://kotlinlang.org/docs/object-declarations.html#object-expressions).
> **실행 검증** — 이 문서의 모든 출력·에러·바이트코드는 **kotlinc 2.4.20 (JRE 21.0.5)** 과 Temurin **JDK 21.0.5** 의 `javac`·`javap` 에서 실제로 얻었다.\
> `kotlinc` 8회(컴파일 실패 2벌) · `javac` 3회(`--release 17` 1벌 포함) · `java` 6회 · `javap` 4회.\
> ★★ 블록은 전부 **캡처 스크립트가 파일로 받아** 조립한 것이다 — 사람이 옮겨 적지 않았다. 소스 펜스의 첫 줄 배너도 캡처가 찍었다.
> ★★ **Java 를 같은 모양으로 짜서 나란히 던졌다** — 이 주제는 「Java 와 **반대**」가 전부라 한쪽만 보면 반이다.
> ⚠️ 이 문서의 역어셈블은 전부 kotlinc **기본 `-jvm-target` 1.8**, javac **기본 `--release` 21** 이다. javac 는 **`--release 17` 을 한 번 더** 찍었다((3)).
> **버전** — 중첩 클래스·`inner`·`this@Outer` 는 전부 **1.0** 이다. 이 문서에서 판으로 갈리는 것은 **javac 쪽**(안 쓰는 바깥 참조를 버리는가)뿐이다((3)).
> **경계** — 클래스 선언·`init` 순서는 [15번 주제](../15-class-declaration-constructors-and-init/), `object` 식(익명 객체)의 **타입이 어디까지 보이나**는 [25번 주제](../25-object-declaration-companion-and-object-expression/) (4),\
> 람다가 바깥 변수를 잡는 규칙은 [10번 주제](../10-lambdas-and-higher-order-functions/)가 정본이다. 여기는 **「바깥 인스턴스를 잡느냐」** 하나만 본다.\
> ★ `companion object` 에 `inner` 를 못 붙이는 것은 [25번 주제](../25-object-declaration-companion-and-object-expression/) (5)에서 이미 실측했다.
> **대비** — Java 갈래 목록([`java/syntax/README.md`](../../../java/syntax/README.md))의 **12번**([`12-nested-classes/`](../../../java/syntax/12-nested-classes/)) — **같은 JVM 구조(`this$0`)를 기본값만 반대로** 쓴다. 누수 관찰(GC 수거)은 그쪽 (6)이 **JDK 셋으로** 했다.
> 이 본문은 Claude 작성이다(원고 없음).

★ **본체는 셋째 창이다** — 「`javap -p` 로 **`this$0` 필드가 있는가**를 네 칸(Kotlin 두 꼴 × Java 두 꼴)에서 보는 창」.
언어는 「`inner` 는 바깥 인스턴스를 **참조한다**」까지만 약속한다. **그 참조가 `this$0` 이라는 필드로 사는 것은 구현**이고, 필드는 `javap` 에만 보인다.

## 기본값이 뒤집힌 자리들 — 이 갈래의 목록을 잇는다

이 목록([README](../README.md))의 첫째 축이 「**Java 의 기본값을 어디서 뒤집었나**」다. 앞에서 뒤집힌 곳을 이어 적으면:

| 주제 | Java 의 기본 | Kotlin 의 기본 | 반대로 가려면 |
|---|---|---|---|
| [03번](../03-null-safe-types/) null 안전 | 참조는 **null 가능** | **null 불가** | `?` 를 붙인다 |
| [18번](../18-visibility-modifiers/) 가시성 | **package-private** | **`public`** | 수식어를 적는다 |
| [19번](../19-inheritance-open-final-override/) 상속 | **열림**(`final` 을 적어야 닫힌다) | **닫힘**(`final`) | `open` 을 붙인다 |
| ★ **27번 중첩 클래스** | 클래스 안의 클래스는 **바깥을 잡는다**(`static` 을 적어야 안 잡는다) | **안 잡는다** | ★ **`inner` 를 붙인다** |

★★ 네 줄 중 셋이 「**적지 않으면 더 좁은 쪽**」으로 뒤집혔다 — null 을 못 담고, 상속을 못 하고, 바깥을 못 잡는다(가시성만 예외로 **넓은 쪽**이다 — 그 이야기는 [18번](../18-visibility-modifiers/)이 정본이다).

## 이 주제가 쓰는 세 층

| 층 | 뜻 | 근거로 쓰는 것 |
|---|---|---|
| **언어 보장** | 명세·공식 문서가 약속한 것 | `inner` 없이 바깥 멤버를 쓰면 **컴파일 에러** · `this@Outer` · `inner` 는 **바깥 인스턴스가 있어야 만든다** |
| **구현(JVM 백엔드)** | kotlinc·javac 가 내리는 방식 | ★★★ **`this$0` 필드** · 생성자가 **바깥을 인자로 받는 것** · 람다의 `invokedynamic` 서명 |
| **이 판의 관찰** | kotlinc 2.4.20 · javac 21.0.5 에서 이번에 본 것 | ★ **안 쓰는 바깥 참조를 kotlinc 는 남기고 javac 21 은 버린 것**((3)) |

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
| **흔들린다** | (이 주제에는 없다) | 주소·해시코드를 **하나도 안 찍었다** — (4)는 참조를 **`===` 와 필드값**으로만 읽었다 |
| 안 흔들린다 | ★★★ `javap -p` 의 **필드·생성자 목록** | 이 주제의 답 자체다 |
| 안 흔들린다 | 익명 클래스 이름 `Host$usesOuter$1` | [25번 주제](../25-object-declaration-companion-and-object-expression/)에서 본 **규칙적 이름**이다 |
| 안 흔들린다 | 컴파일 에러의 **문구·`파일:줄:칸`** · 종료 코드 · 출력 | 결정적이다 |
| 해당 없음 | 메모리 크기·GC 수거 | ★★★ **안 쟀다.** 이 문서는 「참조가 **있다**」까지만 말한다 |

★ 근거 — 캡처 스크립트를 처음부터 두 번 돌려 **블록 전체를 바이트 단위로 대조**했다(수치는 3-answer 의 「실행 검증」).

## 한눈에 — 쉽게 말하면

**클래스 안에 클래스를 두면, 안쪽 객체가 「바깥 객체의 열쇠」를 들고 다니느냐가 갈린다.**

본채(바깥 클래스) 안에 방(안쪽 클래스)을 들이는데 —\
**Java 는 방마다 본채 열쇠를 기본으로 달아 준다**(안 달려면 `static`).\
**Kotlin 은 기본으로 안 달아 준다**(달려면 `inner`).

| 비유 | 실체 | 이 문서에서 |
|---|---|---|
| 본채 | 바깥 클래스 `Outer` | (1) |
| 열쇠 없는 별채 | Kotlin `class Nested` · Java `static class` | (1) |
| 본채 열쇠가 달린 방 | Kotlin `inner class` · Java 그냥 `class` | (1) |
| 열쇠 그 자체 | ★★★ 숨은 필드 **`this$0`** | (1)(3) |
| 열쇠가 있으니 본채 물건을 쓴다 | `inner` 안에서 `name`·`this@Outer.name` | (2)(5) |
| 방이 남아 있으면 본채도 못 헐린다 | ★ **inner 객체가 바깥을 붙잡는다** — 참조가 있다 | (4) |
| 그 자리에서 짓는 임시 부스 | `object : T { }` — **쓰면 열쇠를 받고 안 쓰면 안 받는다** | (6) |

```text
                      안 적으면                       적으면
   Java    class B           -> this$0 있음         static class B -> this$0 없음
   Kotlin  class B           -> this$0 없음         inner class B  -> this$0 있음
                                 ^^^^^^^^^^^^^^^^^^^ 같은 칸에서 정반대다
```

## 이 주제가 답하려는 질문

1. `inner` 를 붙이면 클래스 파일에서 **무엇이** 달라지나 — Java 와 같은 모양을 나란히 놓으면.
2. `inner` 를 **안** 붙이면 무엇을 못 하게 되나 — 그 기본값은 무엇을 막아 주나.
3. 익명 객체와 람다는 **언제** 바깥을 잡나.

## 동작 방식

### (0) ★★★ 이 주제가 쓰는 창 — 그리고 「부적용인 창」

| 창 | 무엇을 보여 주나 | 어디서 왔나 |
|---|---|---|
| **실행 출력** | 네 꼴이 **다 같은 일을 한다** — 차이가 출력에 안 보인다 | 이 갈래의 기본 창 |
| **컴파일 진단** | `inner` 없이 바깥을 쓰면 · 인터페이스/`object`/companion 안의 `inner` · 생성자 호출 규칙((2)) | 이 갈래의 기본 창 |
| ★★★ **`javap -p` 의 `this$0`** | 네 칸 격자 — **누가 바깥 참조 필드를 갖나**((1)(3)) | ★ **본체 창** |
| ★★ **javac `--release` 를 바꿔 다시 찍기** | 안 쓰는 참조를 **버리는 것이 판에 달린다**((3)) | [Java 12번](../../../java/syntax/12-nested-classes/) (6)에서 쓰던 창 |
| ★ **리플렉션으로 `this$0` 을 읽기** | 참조가 **실제로 바깥 객체를 가리키는가**((4)) | ★ 이 주제의 고유 창 |
| ★ **`invokedynamic` 서명 읽기** | 람다가 **무엇을 넘겨받나**((6)) | [10번 주제](../10-lambdas-and-higher-order-functions/)의 창 |
| **부적용 — 메모리·GC** | ★★★ **안 쟀다.** 「새는가」는 GC 를 돌려야 답이 나오는 질문이다 | [Java 12번](../../../java/syntax/12-nested-classes/) (6)이 JDK 셋에서 수거를 관찰했다 |

★★ **제5의 상태 — 「같은 질문을 다른 창으로 물었다」.**
「바깥을 붙잡나」는 원래 **GC 가 거둬 가나**로 물을 질문이다. 이 문서는 그것을 **「참조 필드가 있고 그 값이 바깥 객체인가」** 로 바꿔 물었다((4)).\
★ 바꾼 창의 한계 — **참조가 있으면 GC 가 못 거둔다**는 것은 JVM 의 도달 가능성 규칙이지만, **실제로 메모리가 얼마나 남는지·언제 문제가 되는지**는 이 창이 **못 본다.**

### (1) ★★★ 네 칸 격자 — Kotlin 두 꼴 × Java 두 꼴

**언제 쓰나** — 「`inner` 가 뭘 바꾸나」를 한 번에 볼 때. **같은 모양을 두 언어로** 짰다.

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

**출력은 네 줄이 다 같은 일을 했다.** 차이는 클래스 파일에 있다.

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

```text
                         안 적은 꼴                          적은 꼴
                         ---------------------------------   ---------------------------------
   Kotlin               class Nested                         inner class Inner
                          Outer$Nested()                       final Outer this$0;      <- ★
                          (필드 없음)                          Outer$Inner(Outer)

   Java                 class JInner                         static class SNested
                          final NestGrid this$0;   <- ★        NestGrid$SNested()
                          NestGrid$JInner(NestGrid)            (필드 없음)
```

- ★★★ **`this$0` 은 Kotlin 에서는 「적은 꼴」(`inner`)에, Java 에서는 「안 적은 꼴」에 있다.** 같은 JVM 장치를 **정반대 기본값**으로 쓴다.
- ★★ **생성자가 바깥을 인자로 받는다** — `Outer$Inner(Outer)`·`NestGrid$JInner(NestGrid)`. 그래서 **바깥 인스턴스 없이는 못 만든다**((2)의 두 번째 블록).
- ★ **JVM 에는 「중첩」이라는 개념이 거의 없다** — `Outer$Inner` 는 **따로 떨어진 클래스 파일**이고, 「바깥을 안다」는 것은 **필드 하나 + 생성자 인자 하나**로 구현된다. 이것이 **구현**이고 언어가 약속한 것은 「바깥 인스턴스를 참조한다」까지다.

### (2) ★★ `inner` 가 없으면 **바깥을 못 쓴다** — 그리고 못 두는 자리

**언제 쓰나** — Java 습관대로 중첩 클래스에서 바깥 필드를 쓰다가 막힐 때.

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

| 쓴 꼴 | 진단 | 뜻 |
|---|---|---|
| 중첩(`inner` 없음)에서 `$name` | 「`outer class 'class Outer : Any' of non-inner class cannot be used as receiver.`」 | ★★★ **바깥 인스턴스가 없으니** 누구의 `name` 인지 정할 수 없다 |
| 인터페이스 안의 `inner class` | 「`modifier 'inner' is not applicable inside 'interface'.`」 | 인터페이스에는 **인스턴스 상태가 없다** — 잡을 바깥이 없다 |
| `object` 안의 `inner class` | 「`modifier 'inner' is not applicable inside 'standalone object'.`」 | `object` 는 **하나뿐**이라 잡을 필요가 없다 — 그냥 이름으로 부른다 |
| `companion object` 안의 `inner class` | 「`modifier 'inner' is not applicable inside 'companion object'.`」 | 〃 — companion 도 **클래스당 하나**인 객체다 |

- ★★★ 첫 에러의 문구가 이 주제를 요약한다 — 「**non-inner class** 에서는 바깥 클래스를 **수신자(receiver)로 쓸 수 없다**」. Java 라면 **아무 말 없이 컴파일되고 `this$0` 이 생기는** 자리다.
- ★ 「`standalone object`」 와 「`companion object`」 — 진단이 **두 종류의 `object` 를 낱말로 갈라** 부른다. companion **자신**에 `inner` 를 붙이는 것(`inner companion object`)의 금지는 [25번 주제](../25-object-declaration-companion-and-object-expression/) (5)가 실측했다 — 여기는 **그 안에 둔 클래스**다.

**만드는 쪽의 규칙** — 누가 누구를 수신자로 만드나

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

- ★★ `Outer.Inner()` — 「`constructor of the inner class ... can only be called with a receiver of the containing class.`」. **바깥 인스턴스가 있어야** `outer.Inner()` 로 만든다 — (1)의 `Outer$Inner(Outer)` 생성자가 그 이유다.
- ★ `Outer().Nested()` — 반대로 **중첩 클래스는 인스턴스를 거쳐 못 만든다**(「`unresolved reference 'Nested' on receiver of type 'Outer'.`」). `Outer.Nested()` 로 **타입 이름**을 거친다.
- ★ Java 의 `outer.new Inner()` 가 Kotlin 에서는 **`outer.Inner()`** 다 — `new` 가 없을 뿐 모양이 같다.

### (3) ★★ 바깥을 **한 번도 안 쓰면** — kotlinc 와 javac 가 갈린다

**언제 쓰나** — 「안 쓰니까 참조도 안 남겠지」라고 판단하려 할 때. **그 판단이 컴파일러와 판에 달려 있다.**

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

```text
   바깥을 안 쓰는 「잡는 꼴」                    this$0 필드    생성자
   -------------------------------------------   ------------   -------------------------
   Kotlin  inner class Unused   (kotlinc 2.4.20)     있다        Quiet$Unused(Quiet)
   Java    class Unused         (javac 21 기본)      없다  ★     NestUnused$Unused(NestUnused)
   Java    class Unused         (--release 17)       있다        NestUnused$Unused(NestUnused)
```

- ★★★ **kotlinc 는 `inner` 가 바깥을 안 써도 `this$0` 을 남겼다.** 「`inner` 라고 적었다 = 잡는다」로 **적은 대로** 한다.
- ★★ **javac 21 은 버렸고 `--release 17` 은 남겼다** — 같은 javac 판이 **목표 릴리스에 따라** 다르게 내린다. [Java 12번](../../../java/syntax/12-nested-classes/) (6)이 **익명 클래스**로 본 것(JDK 17 은 남기고 21·25 는 버림)과 같은 갈림을 **멤버 클래스**에서 다시 봤다.
- ★ 그래도 **생성자는 셋 다 바깥을 인자로 받는다** — javac 21 은 **받기는 받고 저장을 안 한다.** 만드는 쪽의 규칙((2))은 그대로다.
- ★★ 그래서 **「안 쓰면 안 잡는다」는 보장이 아니다.** 잡기 싫으면 **Kotlin 은 `inner` 를 안 적는 것**이, Java 는 **`static` 을 적는 것**이 유일하게 확실한 길이다 — Kotlin 의 기본값이 바로 그쪽이다.

### (4) ★★ inner 객체가 바깥을 **붙잡는다** — 참조가 있다는 것을 런타임에 읽기

**언제 쓰나** — 리스너·콜백을 `inner` 로 만들어 오래 사는 곳에 등록할 때.

```kotlin
// nestref.kt
class Screen(val title: String) {
    val pixels = IntArray(1_000_000)

    inner class Listener {
        fun onClick() = "clicked on $title"
    }

    class Detached {
        fun onClick() = "clicked"
    }
}

fun makeInner(): Any = Screen("home").Listener()
fun makeNested(): Any = Screen.Detached()

fun outerOf(x: Any): Any? {
    val f = x.javaClass.declaredFields.firstOrNull { it.name == "this\$0" } ?: return null
    f.isAccessible = true
    return f.get(x)
}

fun main() {
    val a = makeInner()
    val b = makeNested()
    val sa = outerOf(a) as Screen?
    println("A inner  -> title=${sa?.title} pixels=${sa?.pixels?.size}")
    println("B nested -> ${outerOf(b)}")
}
```

```text
===== kotlinc nestref.kt -d o27r =====
(exit 0)
===== java -cp o27r:kotlin-stdlib.jar NestrefKt =====
A inner  -> title=home pixels=1000000
B nested -> null
(exit 0)
```

- ★★★ `makeInner()` 가 돌려준 것은 **`Listener` 하나**다. `Screen("home")` 은 어떤 변수에도 안 담겼는데, **`Listener` 의 `this$0` 을 따라가면 그 `Screen` 이 나온다** — `title=home pixels=1000000`.
- ★★ 즉 **`Listener` 가 살아 있는 동안 백만 칸짜리 `IntArray` 를 가진 `Screen` 에 닿을 수 있다.** 이것이 「inner 객체가 바깥을 붙잡는다」의 **정확한 뜻**이다.
- ★ `Detached`(그냥 중첩)는 **그런 필드가 없다**(`null`) — 바깥과 **아무 끈도 없다.**
- ★★★ **이 블록은 메모리를 안 쟀다.** 「새어서 얼마가 남는다」는 GC 를 돌려 수거를 관찰해야 하는 질문이고, 그것은 [Java 12번](../../../java/syntax/12-nested-classes/) (6)이 한 일이다. 여기는 **참조가 있다**까지다.
- ★ `this$0` 이라는 **이름을 코드에 적은 것**은 구현에 기대는 것이다 — 관찰용일 뿐 **프로덕션 코드가 이 이름에 기대면 안 된다.**

### (5) ★ `this@Outer` — 이름이 겹칠 때 바깥을 부르는 법

**언제 쓰나** — `inner` 안에 바깥과 **같은 이름**의 멤버가 있을 때.

```kotlin
// nestlabel.kt
class Outer(val name: String) {
    val tag = "outer-tag"

    inner class Inner(val name: String) {
        val tag = "inner-tag"
        fun show() = "$name/${this@Outer.name} $tag/${this@Outer.tag}"
    }
}

fun main() {
    val o = Outer("O")
    val i1 = o.Inner("a")
    val i2 = o.Inner("b")
    println("A ${i1.show()}")
    println("B ${i2.show()}")
    println("C ${Outer("P").Inner("c").show()}")
}
```

```text
===== kotlinc nestlabel.kt -d o27l =====
(exit 0)
===== java -cp o27l:kotlin-stdlib.jar NestlabelKt =====
A a/O inner-tag/outer-tag
B b/O inner-tag/outer-tag
C c/P inner-tag/outer-tag
(exit 0)
```

- `$name`·`$tag` 는 **가장 안쪽**(자기 것)이 이긴다 — `a`·`inner-tag`.
- ★★ **`this@Outer.name`** 은 **라벨로 바깥을 지목**한다 — `O`·`outer-tag`. 라벨 이름은 **바깥 클래스 이름**이다.
- ★ `i1`·`i2` 가 **같은 `O`** 를 본다 — 한 바깥에서 inner 객체를 여럿 만들면 **전부 같은 바깥을 가리킨다.** `C` 는 다른 바깥(`P`)에서 만든 것이다.
- ★ Java 의 `Outer.this.name` 이 Kotlin 의 **`this@Outer.name`** 이다.

### (6) ★★ 익명 객체와 람다 — **쓰면 잡고 안 쓰면 안 잡는다**

**언제 쓰나** — `object : Listener { }` 나 람다를 메서드 안에서 만들 때. **`inner` 라는 낱말이 없는데도** 바깥을 잡을 수 있다.

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

```text
   만든 것                               바깥을 쓰나   무엇을 받나
   -----------------------------------   -----------   ------------------------------------------
   object : Greeter { ... $name ... }       쓴다       Host$usesOuter$1(Host)    + this$0 필드
   object : Greeter { ... "hi" ... }        안 쓴다    Host$ignoresOuter$1()     필드 없음
   { "lambda $name" }                       쓴다       invokedynamic ... (LHost;)
   { "lambda" }                             안 쓴다    invokedynamic ... ()
```

- ★★★ **익명 객체는 바깥을 쓸 때만 잡는다** — `usesOuter` 쪽에만 `this$0` 과 `(Host)` 생성자가 있다. (3)에서 **`inner` 는 안 써도 잡았던 것**과 다르다 — `inner` 는 **적은 대로**, 익명 객체는 **쓴 대로**다.
- ★★ **람다도 쓴 만큼만 받는다** — `invokedynamic` 의 서명이 `(LHost;)` 와 `()` 로 갈렸다. 람다는 **필드가 아니라 인자로** 바깥을 넘겨받는다([10번 주제](../10-lambdas-and-higher-order-functions/)).
- ★ **클래스 파일 개수로 가르지 마라** — 람다는 `invokedynamic` 으로 만들어지므로 「바깥을 잡나」는 **파일이 아니라 서명**(`(LHost;)` 대 `()`)으로 갈린다.
- ★ 익명 객체의 **타입이 어디까지 보이나**는 [25번 주제](../25-object-declaration-companion-and-object-expression/) (4)가 정본이다.

## 문법 — 형태와 규칙

**형태** — 바깥이 필요 없는 보조 타입은 **중첩**, 바깥 상태에 스스로 등록하는 것은 **`inner`** 로 나눈 최소 예제다.

```kotlin
// form27.kt
class Tree(val name: String) {
    private val nodes = mutableListOf<Node>()

    class Stats(val count: Int)

    inner class Node(val label: String) {
        init { nodes += this }
        fun path() = "${this@Tree.name}/$label"
    }

    fun stats() = Stats(nodes.size)
}

fun main() {
    val t = Tree("root")
    val a = t.Node("a")
    t.Node("b")
    println("Z ${a.path()}")
    println("Y ${t.stats().count}")
    println("X ${Tree.Stats(9).count}")
}
```

```text
===== kotlinc form27.kt -d o27f =====
(exit 0)
===== java -cp o27f:kotlin-stdlib.jar Form27Kt =====
Z root/a
Y 2
X 9
(exit 0)
```

**규칙 불릿**

- 클래스 안의 클래스는 **기본이 중첩**이다 — 바깥 인스턴스를 **모른다**(Java 의 `static` 중첩과 같은 모양, (1)).
- **`inner`** 를 붙여야 바깥 인스턴스를 잡는다. 클래스 파일에 **`this$0`** 과 **바깥을 받는 생성자**가 생긴다((1)).
- `inner` 객체는 **`바깥.Inner()`** 로 만들고, 중첩은 **`Outer.Nested()`** 로 만든다((2)).
- 바깥 멤버를 이름으로 부르되, 겹치면 **`this@Outer`** 로 지목한다((5)).
- **인터페이스·`object`·`companion object`** 안에는 `inner` 를 못 둔다((2) — 셋 다 던졌다).
- **익명 객체·람다**는 `inner` 표기 없이 **쓴 만큼** 바깥을 잡는다((6)).

## 어디서 틀리나

1. ★★★ **Java 습관대로 중첩 클래스에서 바깥 필드를 쓴다.** 「`... of non-inner class cannot be used as receiver.`」((2)). **`inner` 를 붙여야** 한다.
2. ★★★ **Kotlin 의 `class B` 를 Java 의 `class B` 로 읽는다.** **정반대다** — Kotlin 은 안 잡고 Java 는 잡는다((1)).
3. ★★ **`inner` 로 만든 리스너를 오래 사는 곳에 등록한다.** 리스너가 사는 동안 **바깥 전체에 닿을 수 있다**((4)). 필요한 것만 인자로 넘기고 중첩으로 만든다.
4. ★★ **「바깥을 안 쓰니 참조가 안 남겠지」라고 판단한다.** **kotlinc 는 `inner` 면 남긴다**((3)). javac 는 **판(목표 릴리스)에 따라** 갈린다.
5. ★ **`Outer.Inner()` 로 만들려 한다.** 「`... can only be called with a receiver of the containing class.`」((2)).
6. ★ **익명 객체는 안전하다고 믿는다.** **바깥을 쓰면 `this$0` 이 생긴다**((6)) — `inner` 라고 안 적었어도.
7. ★ **인터페이스·`object`·`companion object` 안에 `inner` 를 둔다.** 잡을 바깥 인스턴스가 없다((2)).

## 구현 세부사항 대 언어 보장

| 항목 | 어느 쪽인가 | 근거 |
|---|---|---|
| 기본이 **중첩**(바깥 인스턴스 없음) · `inner` 라야 잡는다 | **언어 보장** | (2)의 에러 |
| `inner` 객체는 **바깥 인스턴스가 있어야** 만든다 | **언어 보장** | (2)의 두 번째 블록 |
| `this@Outer` | **언어 보장** | (5) |
| 인터페이스·`object`·`companion object` 안의 `inner` 금지 | **언어 보장** | (2) |
| 바깥 참조가 **`this$0` 이라는 필드**로 사는 것 · 생성자가 바깥을 받는 것 | ★★★ **JVM 백엔드의 구현** | (1) |
| **안 쓰는 `inner` 도 `this$0` 을 남기는 것** | **kotlinc 2.4.20 의 관찰** | (3) |
| javac 가 **안 쓰는 참조를 버리는 것**(21 기본) · 남기는 것(`--release 17`) | **javac 의 구현 · 목표 릴리스에 매인다** | (3) |
| 익명 객체·람다가 **쓴 만큼만** 잡는 것 | **JVM 백엔드의 구현**(이 판의 관찰) | (6) |
| 참조가 있으면 GC 가 **못 거둔다** | **JVM 의 도달 가능성 규칙** — 이 문서는 수거를 **안 쟀다** | (4) |
| 진단 **문구 그 자체** | **컴파일러 판의 산출물** | 전부 |

★★ **언어가 약속하는 것은 「바깥을 참조한다/안 한다」까지**다. **「`this$0` 이 생긴다」는 그 약속을 JVM 위에서 지키는 방법**이고, 「안 쓰면 버린다」는 **컴파일러마다·판마다 다른 최적화**다.

## 언제 쓰고 언제 안 쓰나

| 상황 | 고르는 것 | 왜 |
|---|---|---|
| 바깥과 개념상 한 덩어리지만 **바깥 상태를 안 쓰는** 보조 타입(`Tree.Stats`·빌더·결과 타입) | **그냥 중첩** — Kotlin 의 기본값 | 끈이 없다((1)) |
| 바깥 인스턴스의 상태를 **읽고 고쳐야** 하는 것(`Tree.Node` 가 `nodes` 에 등록) | **`inner`** | (5)·형태 예제 |
| 오래 사는 곳(이벤트 버스·캐시)에 등록할 콜백 | **중첩 + 필요한 값만 인자로** | (4) — `inner` 면 바깥 전체에 닿는다 |
| 한 번 쓰고 버리는 구현 | `object` 식·람다 | (6) — 단 **바깥을 쓰면 잡는다** |
| `object`·인터페이스 안의 보조 타입 | **중첩만** 된다 | (2) |

## 핵심 문장

1. Kotlin 은 클래스 안의 클래스가 **기본으로 바깥을 안 잡는다** — Java 와 **정반대 기본값**이다.
2. `inner` 를 붙이면 **`this$0` 필드와 바깥을 받는 생성자**가 생긴다 — Java 의 비정적 중첩과 **같은 JVM 구조**다.
3. `inner` 없이 바깥 멤버를 쓰면 「**non-inner class** … cannot be used as receiver」 — Java 라면 조용히 잡았을 자리다.
4. **kotlinc 는 `inner` 가 바깥을 안 써도 참조를 남긴다.** 「안 쓰면 안 잡는다」는 보장이 아니다.
5. 익명 객체와 람다는 **쓴 만큼만** 잡는다 — `inner` 는 **적은 대로**, 익명 객체는 **쓴 대로**다.
6. inner 객체는 **바깥 전체에 닿는 참조**를 들고 다닌다 — 그래서 기본값이 「안 잡는다」인 것에 값어치가 있다.

## 관련 자료

- [03번](../03-null-safe-types/) · [18번](../18-visibility-modifiers/) · [19번 주제](../19-inheritance-open-final-override/) — **기본값이 뒤집힌 앞의 자리들**. 위 표가 그 목록을 잇는다.
- [15번 주제](../15-class-declaration-constructors-and-init/) — 클래스 선언·생성자. `inner` 의 생성자도 같은 규칙에 **바깥 인자 하나**가 더해진 것이다.
- [25번 주제](../25-object-declaration-companion-and-object-expression/) — `object` 식의 타입·`companion` 의 `inner` 금지. 여기는 **익명 객체가 바깥을 잡는가**까지다.
- [10번 주제](../10-lambdas-and-higher-order-functions/) — 람다의 캡처. 여기는 **람다가 바깥 인스턴스를 넘겨받는가**만 본다.
- [`../../../java/syntax/12-nested-classes/`](../../../java/syntax/12-nested-classes/) — Java 의 중첩 네 종류. ★ **`this$0`·nestmate·GC 수거 관찰**의 정본이다.

## 용어 풀이

> **중첩 클래스(nested class)** — 다른 클래스 **안에 선언**된 클래스. Kotlin 에서는 **기본으로 바깥 인스턴스를 모른다.**\
> 예: `class Outer { class Nested }` → `Outer.Nested()`.

> **`inner` 클래스** — 바깥 클래스의 **인스턴스를 참조하는** 중첩 클래스. 바깥 멤버를 이름으로 쓸 수 있다.\
> 예: `class Outer { inner class Inner }` → `outer.Inner()`.

> **`this$0`** — 컴파일러가 inner 클래스에 넣는 **바깥 인스턴스 참조 필드**의 이름. `javap -p` 로 보인다. 이름은 구현이다.

> **`this@Outer`** — 라벨 붙은 `this`. inner 안에서 **바깥 인스턴스**를 명시적으로 부른다.

> **수신자(receiver)** — 멤버를 부를 때 그 멤버가 속한 객체. `name` 만 적으면 컴파일러가 수신자를 찾는다 — 중첩 클래스에서는 **바깥이 후보에 없다.**

> **익명 객체** — `object : T { … }` 로 그 자리에서 만드는 이름 없는 객체. 바깥을 **쓰면** `this$0` 을 갖는다.

> **`invokedynamic`** — 람다를 **별도 클래스 파일 없이** 만드는 JVM 명령. 그 서명의 인자 목록이 **람다가 넘겨받는 것**이다.

## 더 들어가면

- **기본값을 뒤집은 값어치** — Java 에서는 `static` 을 **빠뜨리면 아무 말 없이** 바깥을 잡는다((1)의 격자 · 컴파일러가 침묵한다). Kotlin 은 **적지 않으면 안 잡는 쪽**을 골라, 바깥이 필요한데 빠뜨린 경우를 **컴파일 에러로** 드러낸다 — (2)의 첫 에러가 그것이다. 실수의 방향이 「조용히 붙잡는다」에서 「시끄럽게 막힌다」로 바뀐 것이다. 필요하면 `inner` 한 낱말이면 된다.
- **(3)의 갈림이 알려 주는 것** — javac 는 「안 쓰는 참조는 버려도 된다」고 판단해 **최적화**했고(목표 릴리스에 매여), kotlinc 는 **적은 것을 그대로** 내렸다. 둘 다 언어 규칙을 어긴 것이 아니다 — 언어는 「참조한다」만 약속하므로 **안 쓰는 참조를 버리는 것도, 남기는 것도 합법**이다. **그래서 둘 다 근거로 삼으면 안 된다.**
