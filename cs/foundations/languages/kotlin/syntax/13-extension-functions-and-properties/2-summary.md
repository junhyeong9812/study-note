# kotlin/syntax/13 — 확장 함수·확장 프로퍼티: 정적 디스패치 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Extensions](https://kotlinlang.org/docs/extensions.html) · [Calling Kotlin from Java](https://kotlinlang.org/docs/java-to-kotlin-interop.html) · [Null safety](https://kotlinlang.org/docs/null-safety.html) · [Visibility modifiers](https://kotlinlang.org/docs/visibility-modifiers.html).
> **실행 검증** — 이 문서의 모든 출력·에러·경고·바이트코드는 **kotlinc 2.4.20 (JRE 21.0.5)** 과 Temurin **JDK 21.0.5** 의 `javap` 에서 실제로 얻었다.\
> **Java 쪽 호출은 같은 JDK 의 `javac` 로 컴파일해 실제로 섞어 돌렸다.**\
> `kotlinc` 14회 · `javac` 1회 · `java` 8회 · `javap` 8회. 컴파일 실패 시나리오 5벌 · 경고 시나리오 3벌.
> ⚠️ **`-jvm-target` 을 밝히지 않은 바이트코드 주장은 반쪽이다.** 이 문서의 역어셈블은 **기본값 1.8**(`major version: 52`)이다 —\
> 그래서 문자열 보간이 `StringBuilder` 로 보인다([02번 주제](../02-string-templates-and-raw-strings/)).
> **버전** — 확장 함수·확장 프로퍼티·`@JvmName` 은 전부 **1.0**. 이 문서에 버전으로 갈리는 항목은 없다.
> **경계** — ★ **「정적 디스패치라는 천장」이 무엇을 뜻하는지, 왜 그 대가를 치르고도 쓰는지는\
> [`../../언어-특성/README.md`](../../언어-특성/README.md) §7 이 정본이다.** 여기는 **선언 문법 · 해소 순서 · 멤버와 충돌할 때의 규칙**만 다룬다.\
> 수신자 지정 람다(`A.() -> Unit`)와 DSL 은 [목록의 **37번 주제**](../37-lambdas-with-receiver-and-type-safe-builders/), `infix` 확장은 [09번 주제](../09-varargs-spread-local-and-infix-functions/),\
> scope function 은 [목록의 **14번 주제**](../14-scope-functions/), `operator` 확장은 [목록의 **31번 주제**](../31-operator-overloading-infix-and-invoke/),\
> `@JvmName` 을 포함한 상호운용 애너테이션 **전체**는 [목록의 **39번 주제**](../39-java-interop-annotations/)가 정본이다 —\
> 여기서는 `@JvmName` 을 **디스크립터 충돌을 푸는 도구로만** 쓴다.\
> `Intrinsics.checkNotNullParameter` 의 정본은 [03번 주제](../03-null-safe-types/)다.
> 이 본문은 Claude 작성이다(원고 없음).

## 한눈에 — 쉽게 말하면

**확장 함수는 클래스에 메서드를 넣는 것이 아니다. 점 찍고 부를 수 있게 생긴 `static` 함수다.**

`m.doubled()` 라고 적지만 컴파일된 것은 `doubled(m)` 이다.\
겉모습만 멤버이고 실체는 **바깥에 있는 함수**이며, 수신자는 **첫 번째 파라미터**로 들어간다.

> **디스패치(dispatch)** — 같은 이름의 함수가 여럿일 때 **어느 것을 실제로 부를지 고르는 일**.\
> 고르는 시점이 둘이다 — **컴파일할 때** 고르면 정적, **실행할 때 객체를 보고** 고르면 가상(virtual).

여기서 모든 것이 따라 나온다. 실체가 바깥의 `static` 함수이므로 —\
**객체를 보고 고를 수가 없고**(정적 디스패치), **`private` 멤버를 못 보고**, **필드를 못 만들고**,\
**임포트해야 보이고**, **수신자가 null 이어도 된다.**

비유 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 가게 안에 새로 들인 메뉴 | 멤버 함수 — 클래스 안에 있다 |
| 가게 앞 노점이 그 가게 이름으로 파는 것 | 확장 함수 — 클래스 밖의 `static` 함수 |
| 노점이 가게 금고를 못 연다 | 확장은 `private` 멤버를 못 본다 |
| 노점은 가게 간판만 보고 손님을 맞는다 | 정적 디스패치 — **선언 타입**으로 고른다 |
| 가게 안에 같은 메뉴가 있으면 손님은 가게로 들어간다 | 멤버가 이긴다 |
| 노점은 그 골목에 들어와야 보인다 | 임포트가 필요하다 |
| 노점은 문 닫은 가게 앞에도 설 수 있다 | `String?` 수신자 — null 이어도 부른다 |

```text
   멤버 함수                            확장 함수
   +-----------------------------+      +--------------------------------+
   | class Money {               |      | class Money { ... }            |
   |   fun doubled(): Money      |      |                                |
   | }                           |      | fun Money.doubled(): Money     |
   |                             |      |   ↓ 컴파일하면                 |
   | Money.doubled()             |      | static doubled(Money)          |
   |   ← 클래스 안에 산다        |      |   ← 클래스 밖에 산다           |
   +-----------------------------+      +--------------------------------+
     m.doubled()                          m.doubled()
     → invokevirtual                      → invokestatic doubled(m)
```

**소스에서 점 찍는 모양이 같아서 착각하지만, 나오는 명령어가 다르다.**

## 이 주제가 답하려는 질문

1. 확장 함수는 **무엇으로 컴파일되는가** — 그리고 수신자는 어디로 가는가.
2. 같은 객체인데 **변수 타입만 다르면** 왜 다른 확장이 불리는가 — 멤버는 왜 안 그런가.
3. 멤버와 확장의 이름이 겹치면 **누가 이기고**, 확장이 **못 하는 것**은 무엇인가.

## 동작 방식

### (1) ★★ 확장은 `static` 메서드다 — 수신자는 **첫 파라미터**다

**언제 쓰나** — "확장 함수는 클래스에 메서드를 추가하는 문법" 이라고 믿을 때.

```kotlin
class Money(val won: Int)

fun Money.doubled(): Money = Money(won * 2)

val Money.label: String get() = "${won}원"

fun String?.orNone(): String = this ?: "none"

fun use(m: Money): String = m.doubled().label

fun useNull(s: String?): String = s.orNone()
```

**출력** (`javap -c -p -s out/IcodeKt.class`)

```text
Compiled from "icode.kt"
public final class IcodeKt {
  public static final Money doubled(Money);
    descriptor: (LMoney;)LMoney;
    Code:
       0: aload_0
       1: ldc           #9                  // String <this>
       3: invokestatic  #15                 // Method kotlin/jvm/internal/Intrinsics.checkNotNullParameter:(Ljava/lang/Object;Ljava/lang/String;)V
       6: new           #17                 // class Money
       9: dup
      10: aload_0
      11: invokevirtual #21                 // Method Money.getWon:()I
      14: iconst_2
      15: imul
      16: invokespecial #25                 // Method Money."<init>":(I)V
      19: areturn

  public static final java.lang.String getLabel(Money);
    descriptor: (LMoney;)Ljava/lang/String;
    Code:
       0: aload_0
       1: ldc           #9                  // String <this>
       3: invokestatic  #15                 // Method kotlin/jvm/internal/Intrinsics.checkNotNullParameter:(Ljava/lang/Object;Ljava/lang/String;)V
       6: new           #31                 // class java/lang/StringBuilder
       9: dup
      10: invokespecial #34                 // Method java/lang/StringBuilder."<init>":()V
      13: aload_0
      14: invokevirtual #21                 // Method Money.getWon:()I
      17: invokevirtual #38                 // Method java/lang/StringBuilder.append:(I)Ljava/lang/StringBuilder;
      20: ldc           #39                 // int 50896
      22: invokevirtual #42                 // Method java/lang/StringBuilder.append:(C)Ljava/lang/StringBuilder;
      25: invokevirtual #46                 // Method java/lang/StringBuilder.toString:()Ljava/lang/String;
      28: areturn

  public static final java.lang.String orNone(java.lang.String);
    descriptor: (Ljava/lang/String;)Ljava/lang/String;
    Code:
       0: aload_0
       1: dup
       2: ifnonnull     8
       5: pop
       6: ldc           #52                 // String none
       8: areturn

  public static final java.lang.String use(Money);
    descriptor: (LMoney;)Ljava/lang/String;
    Code:
       0: aload_0
       1: ldc           #59                 // String m
       3: invokestatic  #15                 // Method kotlin/jvm/internal/Intrinsics.checkNotNullParameter:(Ljava/lang/Object;Ljava/lang/String;)V
       6: aload_0
       7: invokestatic  #61                 // Method doubled:(LMoney;)LMoney;
      10: invokestatic  #63                 // Method getLabel:(LMoney;)Ljava/lang/String;
      13: areturn

  public static final java.lang.String useNull(java.lang.String);
    descriptor: (Ljava/lang/String;)Ljava/lang/String;
    Code:
       0: aload_0
       1: invokestatic  #66                 // Method orNone:(Ljava/lang/String;)Ljava/lang/String;
       4: areturn
}
```

```text
   소스가 적은 것                 클래스 파일에 있는 것
   +-------------------+          +--------------------------------------+
   | fun Money.doubled |   ──▶    | public static final Money doubled(   |
   |   (): Money       |          |     Money )                          |
   +-------------------+          |   descriptor: (LMoney;)LMoney;       |
                                  +--------------------------------------+
   | m.doubled()       |   ──▶    | aload_0                              |
   +-------------------+          | invokestatic doubled:(LMoney;)LMoney;|
                                  +--------------------------------------+
```

그림 해설:

- ★★ **`static` 이다.** `Money` 클래스 안이 아니라 **파일 클래스 `IcodeKt` 안**에 있다.\
  `Money.class` 를 아무리 찍어도 `doubled` 는 없다.
- ★★ **수신자가 첫 파라미터다.** 디스크립터가 `(LMoney;)LMoney;` — 인자를 하나도 안 적었는데 파라미터가 하나다.\
  가장 짧은 증거는 `Intrinsics.checkNotNullParameter` 에 넘어가는 **이름이 `<this>`** 라는 것이다.\
  컴파일러가 그 파라미터를 "이건 `this` 다" 라고 이름 붙여 놓았다([03번 주제](../03-null-safe-types/)).
- **확장 프로퍼티는 `getLabel(Money)` 라는 정적 게터**가 된다. 필드는 **없다** — (5)에서 그 결과를 본다.
- ★ **`orNone` 에는 그 null 검사가 없다.** 수신자를 `String?` 로 적었기 때문이다 — (6)의 근거다.
- 호출부(`use`)는 `invokestatic` 두 번이다. **멤버 호출이었다면 `invokevirtual`** 이 나왔을 것이고,\
  그 차이가 (2)에서 결과를 바꾼다.

비용 — 객체가 안 생긴다. 확장 호출은 **정적 호출 한 번**이고 가상 함수 테이블을 거치지 않는다.

### (2) ★★ 정적 디스패치 — **선언 타입**이 고른다. 멤버와 정반대다

**언제 쓰나** — 상위 타입 변수에 하위 타입 객체를 담아 놓고 확장을 부를 때. **이 주제의 심장이다.**

```kotlin
open class Animal {
    open fun speakMember(): String = "Animal(member)"
}

class Dog : Animal() {
    override fun speakMember(): String = "Dog(member)"
}

fun Animal.speakExt(): String = "Animal(ext)"
fun Dog.speakExt(): String = "Dog(ext)"

fun main() {
    val asDog: Dog = Dog()
    val asAnimal: Animal = Dog()

    println("A asDog.speakMember()    : ${asDog.speakMember()}")
    println("B asAnimal.speakMember() : ${asAnimal.speakMember()}")
    println("C asDog.speakExt()       : ${asDog.speakExt()}")
    println("D asAnimal.speakExt()    : ${asAnimal.speakExt()}")
    println("E same object?           : ${asDog.javaClass == asAnimal.javaClass}")
}
```

**출력** (`java -cp odisp:kotlin-stdlib.jar DispKt`)

```text
A asDog.speakMember()    : Dog(member)
B asAnimal.speakMember() : Dog(member)
C asDog.speakExt()       : Dog(ext)
D asAnimal.speakExt()    : Animal(ext)
E same object?           : true
```

```text
   두 변수 모두 Dog 객체를 가리킨다 (E: true)

        asDog: Dog  ─┐                 ┌─ speakMember() ─▶ Dog(member)   ← 객체를 본다
                     ├──▶  [ Dog 객체 ]┤
     asAnimal: Animal┘                 └─ speakMember() ─▶ Dog(member)   ← 객체를 본다

        asDog: Dog     ──▶ speakExt() ─▶ Dog(ext)      ← 변수 타입을 본다 ★
     asAnimal: Animal  ──▶ speakExt() ─▶ Animal(ext)   ← 변수 타입을 본다 ★
```

**같은 객체인데 멤버는 둘 다 `Dog`, 확장은 변수 타입대로 갈린다.** 이것이 대비의 전부다.

바이트코드가 이유를 말한다. 같은 네 호출을 `println` 없이 따로 적어 찍었다.

```kotlin
open class Animal {
    open fun speakMember(): String = "Animal(member)"
}

class Dog : Animal() {
    override fun speakMember(): String = "Dog(member)"
}

fun Animal.speakExt(): String = "Animal(ext)"
fun Dog.speakExt(): String = "Dog(ext)"

fun callMemberAsDog(x: Dog): String = x.speakMember()
fun callMemberAsAnimal(x: Animal): String = x.speakMember()
fun callExtAsDog(x: Dog): String = x.speakExt()
fun callExtAsAnimal(x: Animal): String = x.speakExt()
```

**출력** (`javap -c -p odc/DispcodeKt.class` — 호출부 네 개만 발췌)

```text
  public static final java.lang.String callMemberAsDog(Dog);
    Code:
       0: aload_0
       1: ldc           #26                 // String x
       3: invokestatic  #15                 // Method kotlin/jvm/internal/Intrinsics.checkNotNullParameter:(Ljava/lang/Object;Ljava/lang/String;)V
       6: aload_0
       7: invokevirtual #32                 // Method Dog.speakMember:()Ljava/lang/String;
      10: areturn

  public static final java.lang.String callMemberAsAnimal(Animal);
    Code:
       0: aload_0
       1: ldc           #26                 // String x
       3: invokestatic  #15                 // Method kotlin/jvm/internal/Intrinsics.checkNotNullParameter:(Ljava/lang/Object;Ljava/lang/String;)V
       6: aload_0
       7: invokevirtual #36                 // Method Animal.speakMember:()Ljava/lang/String;
      10: areturn

  public static final java.lang.String callExtAsDog(Dog);
    Code:
       0: aload_0
       1: ldc           #26                 // String x
       3: invokestatic  #15                 // Method kotlin/jvm/internal/Intrinsics.checkNotNullParameter:(Ljava/lang/Object;Ljava/lang/String;)V
       6: aload_0
       7: invokestatic  #39                 // Method speakExt:(LDog;)Ljava/lang/String;
      10: areturn

  public static final java.lang.String callExtAsAnimal(Animal);
    Code:
       0: aload_0
       1: ldc           #26                 // String x
       3: invokestatic  #15                 // Method kotlin/jvm/internal/Intrinsics.checkNotNullParameter:(Ljava/lang/Object;Ljava/lang/String;)V
       6: aload_0
       7: invokestatic  #42                 // Method speakExt:(LAnimal;)Ljava/lang/String;
      10: areturn
```

그림 해설:

- 멤버 쪽은 `invokevirtual Dog.speakMember` 와 `invokevirtual Animal.speakMember` 로 **적힌 클래스가 다른데**,\
  `invokevirtual` 은 **실행할 때 객체의 실제 클래스에서 다시 찾는다.** 그래서 둘 다 `Dog` 의 것이 돈다.
- ★★ 확장 쪽은 `invokestatic speakExt:(LDog;)` 와 `invokestatic speakExt:(LAnimal;)` 로 **아예 다른 메서드가 박혀 있다.**\
  `invokestatic` 은 **다시 찾지 않는다.** 실행 시점에 바꿀 여지가 없다.
- ★ 두 `speakExt` 는 이름이 같지만 JVM 에서는 **파라미터 타입이 다른 오버로드**다.

**출력** (`javap -s -p odisp/DispKt.class`)

```text
Compiled from "disp.kt"
public final class DispKt {
  public static final java.lang.String speakExt(Animal);
    descriptor: (LAnimal;)Ljava/lang/String;

  public static final java.lang.String speakExt(Dog);
    descriptor: (LDog;)Ljava/lang/String;

  public static final void main();
    descriptor: ()V

  public static void main(java.lang.String[]);
    descriptor: ([Ljava/lang/String;)V
}
```

- ★ **수신자가 파라미터이기 때문에 오버로드가 된 것이다.** (1)과 같은 사실의 다른 얼굴이다.

비용 — 다형성을 포기하는 대신 가상 호출이 사라진다. **고를 수 없다는 것이 대가다.**

### (3) ★ 멤버가 이긴다 — **상속해 온 멤버도** 이긴다

**언제 쓰나** — 남의 클래스에 편한 이름의 확장을 붙였는데 그 이름이 이미 있을 때.

```kotlin
class Cup {
    fun pour(): String = "member"
    fun pour(n: Int): String = "member($n)"
}

fun Cup.pour(): String = "extension"
fun Cup.pour(s: String): String = "extension($s)"

fun main() {
    val c = Cup()
    println("F c.pour()      : ${c.pour()}")
    println("G c.pour(1)     : ${c.pour(1)}")
    println("H c.pour(\"x\")   : ${c.pour("x")}")
}
```

**출력** (`kotlinc shadow.kt -d oshadow` · 컴파일은 **성공**한다)

```text
===== 소스: shadow.kt =====
class Cup {
    fun pour(): String = "member"
    fun pour(n: Int): String = "member($n)"
}

fun Cup.pour(): String = "extension"
fun Cup.pour(s: String): String = "extension($s)"

fun main() {
    val c = Cup()
    println("F c.pour()      : ${c.pour()}")
    println("G c.pour(1)     : ${c.pour(1)}")
    println("H c.pour(\"x\")   : ${c.pour("x")}")
}
===== kotlinc shadow.kt =====
shadow.kt:6:9: warning: this extension is shadowed by a member: 'fun pour(): String' defined in 'Cup'.
fun Cup.pour(): String = "extension"
        ^^^^
(exit 0)
```

**출력** (`java -cp oshadow:kotlin-stdlib.jar ShadowKt`)

```text
F c.pour()      : member
G c.pour(1)     : member(1)
H c.pour("x")   : extension(x)
```

- ★ **에러가 아니라 경고다.** 확장은 조용히 무시되고 프로그램은 돈다 —\
  **컴파일은 통과하고 동작만 내 뜻과 다른** 모양이라 이 갈래에서 가장 잘 놓친다.
- ★ **경고는 시그니처가 정확히 겹치는 것에만 붙는다.** `pour(s: String)` 은 멤버에 짝이 없어\
  **경고도 없고 실제로 불린다**(`H`).
- ★★ **상속해 온 멤버도 이긴다.** 확장을 **더 좁은 타입**에 달아도 소용없다.

```kotlin
open class Base {
    fun tag(): String = "Base.member"
}
class Derived : Base()

fun Derived.tag(): String = "Derived.extension"

fun main() {
    val d = Derived()
    println("Q Derived var, member on Base vs ext on Derived : ${d.tag()}")
}
```

**출력** (`kotlinc probe1.kt -d op1` 와 `java -cp op1:kotlin-stdlib.jar Probe1Kt`)

```text
===== 소스: probe1.kt =====
open class Base {
    fun tag(): String = "Base.member"
}
class Derived : Base()

fun Derived.tag(): String = "Derived.extension"

fun main() {
    val d = Derived()
    println("Q Derived var, member on Base vs ext on Derived : ${d.tag()}")
}
===== kotlinc probe1.kt =====
probe1.kt:6:13: warning: this extension is shadowed by a member: 'fun tag(): String' defined in 'Base'.
fun Derived.tag(): String = "Derived.extension"
            ^^^
(exit 0)
===== java Probe1Kt =====
Q Derived var, member on Base vs ext on Derived : Base.member
```

- ★★ **「더 구체적인 쪽이 이긴다」가 통하지 않는 유일한 자리다.** `Derived` 가 `Base` 보다 좁은데도 **멤버가 이긴다.**\
  경고문이 `defined in 'Base'` 라고 **어느 클래스의 멤버에게 졌는지** 알려 준다.
- 해소 순서를 한 문장으로 옮기면 — **멤버(상속 포함)를 먼저 다 보고, 없을 때만 확장을 본다.**

비용 — 라이브러리가 나중에 같은 이름의 멤버를 추가하면 **내 확장이 조용히 죽는다.** 경고만 남는다.

### (4) ★★ 클래스 **안에** 선언한 확장은 수신자가 **둘**이다 — 한쪽은 가상, 한쪽은 정적

**언제 쓰나** — "확장은 오버라이드가 안 된다" 를 규칙으로 외우려 할 때. **그 규칙은 최상위 확장에만 맞다.**

```kotlin
open class Animal
class Dog : Animal()

open class Printer {
    open fun Animal.render(): String = "Printer/Animal"
    open fun Dog.render(): String = "Printer/Dog"
    fun show(a: Animal): String = a.render()
}

class LoudPrinter : Printer() {
    override fun Animal.render(): String = "LoudPrinter/Animal"
    override fun Dog.render(): String = "LoudPrinter/Dog"
}

fun main() {
    val dogAsAnimal: Animal = Dog()
    println("R Printer().show(Dog)      : ${Printer().show(dogAsAnimal)}")
    println("S LoudPrinter().show(Dog)  : ${LoudPrinter().show(dogAsAnimal)}")
}
```

**출력** (`kotlinc probe2.kt -d op2` — **경고도 에러도 없다**)

```text
===== 소스: probe2.kt =====
open class Animal
class Dog : Animal()

open class Printer {
    open fun Animal.render(): String = "Printer/Animal"
    open fun Dog.render(): String = "Printer/Dog"
    fun show(a: Animal): String = a.render()
}

class LoudPrinter : Printer() {
    override fun Animal.render(): String = "LoudPrinter/Animal"
    override fun Dog.render(): String = "LoudPrinter/Dog"
}

fun main() {
    val dogAsAnimal: Animal = Dog()
    println("R Printer().show(Dog)      : ${Printer().show(dogAsAnimal)}")
    println("S LoudPrinter().show(Dog)  : ${LoudPrinter().show(dogAsAnimal)}")
}
===== kotlinc probe2.kt =====
(exit 0)
===== java Probe2Kt =====
R Printer().show(Dog)      : Printer/Animal
S LoudPrinter().show(Dog)  : LoudPrinter/Animal
```

```text
   fun Animal.render()  를  Printer  안에 선언하면 수신자가 둘이 된다

      Printer / LoudPrinter   ← 디스패치 수신자 (dispatch receiver)
            │                    **가상** — 실행할 때 객체를 본다  ▶ R 과 S 가 갈린다
            │
            └── Animal / Dog  ← 확장 수신자 (extension receiver)
                                 **정적** — 컴파일할 때 선언 타입을 본다 ▶ 둘 다 Animal 쪽
```

**출력** (`javap -s -p op2/Printer.class`)

```text
Compiled from "probe2.kt"
public class Printer {
  public Printer();
    descriptor: ()V

  public java.lang.String render(Animal);
    descriptor: (LAnimal;)Ljava/lang/String;

  public java.lang.String render(Dog);
    descriptor: (LDog;)Ljava/lang/String;

  public final java.lang.String show(Animal);
    descriptor: (LAnimal;)Ljava/lang/String;
}
```

**출력** (`javap -c -p op2/Printer.class` — `show` 만 발췌)

```text
  public final java.lang.String show(Animal);
    Code:
       0: aload_1
       1: ldc           #32                 // String a
       3: invokestatic  #21                 // Method kotlin/jvm/internal/Intrinsics.checkNotNullParameter:(Ljava/lang/Object;Ljava/lang/String;)V
       6: aload_0
       7: aload_1
       8: invokevirtual #34                 // Method render:(LAnimal;)Ljava/lang/String;
      11: areturn
```

그림 해설:

- ★★ **여기서는 `static` 이 아니다.** `public java.lang.String render(Animal);` — **인스턴스 메서드**다.\
  `Printer` 인스턴스가 곧 디스패치 수신자이고, 확장 수신자만 파라미터로 들어갔다.
- ★★ **`invokevirtual` 한 줄에 두 성질이 같이 들어 있다.** `aload_0`(디스패치 수신자)은 실행할 때 클래스를 다시 찾으므로 **가상**,\
  그런데 **디스크립터 `(LAnimal;)` 은 이미 박혀 있어서** 확장 수신자는 **정적**이다.\
  `R`/`S` 가 갈리는 것과 둘 다 `Animal` 인 것이 **한 명령어에서 동시에 일어난다.**
- ★ 그래서 **「확장은 오버라이드할 수 없다」는 문장은 최상위 확장에만 맞다.** 클래스 멤버로 선언한 확장은\
  `open`/`override` 가 **붙고 실제로 가상 디스패치된다** — 단 **확장 수신자 쪽은 여전히 정적**이다.\
  최상위 확장에서 `open`/`override` 를 못 쓰는 이유는 (9)에서 에러로 확인한다.

비용 — 이 형태는 **수신자가 둘**이라 읽기가 급격히 어려워진다. DSL 말고는 잘 쓰지 않는다([목록의 **37번 주제**](../37-lambdas-with-receiver-and-type-safe-builders/)).

### (5) 확장 프로퍼티에는 **backing field 가 없다** — 그래서 초기화가 안 된다

**언제 쓰나** — 확장 프로퍼티에 `= 값` 을 적었을 때.

```kotlin
class Cup(val ml: Int)

val Cup.cups: Int = ml / 200
```

**출력** (`kotlinc bad1.kt -d o1`)

```text
===== 소스: bad1.kt =====
class Cup(val ml: Int)

val Cup.cups: Int = ml / 200
===== kotlinc bad1.kt =====
bad1.kt:3:21: error: unresolved reference 'ml'.
val Cup.cups: Int = ml / 200
                    ^^
bad1.kt:3:21: error: extension property cannot be initialized because it has no backing field.
val Cup.cups: Int = ml / 200
                    ^^^^^^^^
```

- ★ **눈에 먼저 들어오는 것은 첫 줄인데 진짜 이유는 둘째 줄이다.**\
  `unresolved reference 'ml'` 은 "초기화 식에서는 아직 수신자가 없다" 는 부수 증상이고,\
  근본은 **`extension property cannot be initialized because it has no backing field`** 다.
- ★ 이유는 (1)에서 이미 봤다 — 확장 프로퍼티는 **`getLabel(Money)` 라는 정적 게터일 뿐**이다.\
  값을 넣어 둘 **칸이 남의 클래스에 생기지 않는다.**
- 고치는 법은 **`get()` 으로 계산하는 것**이다.

```kotlin
class Cup(val ml: Int)

val Cup.cups: Int get() = ml / 200
```

- 상태를 붙이고 싶으면 확장으로는 안 되고 **`Map` 같은 바깥 저장소**를 직접 써야 한다.\
  `field` 키워드와 backing field 의 정본은 [목록의 **16번 주제**](../16-properties-backing-field-lateinit-const/)다.

비용 — 매 호출 계산이다. 캐시할 자리가 없다.

### (6) ★ null 수신자 확장이 되는 이유 — **검사를 안 심는다**

**언제 쓰나** — `String?.orEmpty()` 가 왜 `?.` 없이 불리는지 물을 때.

```kotlin
fun String?.orNone(): String = if (this == null) "none" else this
fun String.shout(): String = this + "!"

fun main() {
    val s: String? = null
    println("K null.orNone()          : ${s.orNone()}")
    println("L \"hi\".orNone()          : ${"hi".orNone()}")
    println("M null.orEmpty() (stdlib): '${s.orEmpty()}'")
    println("N null.toString() (stdlib): ${s.toString()}")
}
```

**출력** (`java -cp onul:kotlin-stdlib.jar NulKt`)

```text
K null.orNone()          : none
L "hi".orNone()          : hi
M null.orEmpty() (stdlib): ''
N null.toString() (stdlib): null
```

**출력** (`javap -c -p -s onul/NulKt.class` — 두 함수만 발췌)

```text
Compiled from "nul.kt"
public final class NulKt {
  public static final java.lang.String orNone(java.lang.String);
    descriptor: (Ljava/lang/String;)Ljava/lang/String;
    Code:
       0: aload_0
       1: dup
       2: ifnonnull     8
       5: pop
       6: ldc           #10                 // String none
       8: areturn

  public static final java.lang.String shout(java.lang.String);
    descriptor: (Ljava/lang/String;)Ljava/lang/String;
    Code:
       0: aload_0
       1: ldc           #17                 // String <this>
       3: invokestatic  #23                 // Method kotlin/jvm/internal/Intrinsics.checkNotNullParameter:(Ljava/lang/Object;Ljava/lang/String;)V
       6: new           #25                 // class java/lang/StringBuilder
       9: dup
      10: invokespecial #29                 // Method java/lang/StringBuilder."<init>":()V
      13: aload_0
      14: invokevirtual #33                 // Method java/lang/StringBuilder.append:(Ljava/lang/String;)Ljava/lang/StringBuilder;
      17: bipush        33
      19: invokevirtual #36                 // Method java/lang/StringBuilder.append:(C)Ljava/lang/StringBuilder;
      22: invokevirtual #40                 // Method java/lang/StringBuilder.toString:()Ljava/lang/String;
      25: areturn
```

```text
   두 함수의 디스크립터는 한 글자도 다르지 않다

     orNone : (Ljava/lang/String;)Ljava/lang/String;   ← 검사 없음  → this 가 null 일 수 있다
     shout  : (Ljava/lang/String;)Ljava/lang/String;   ← checkNotNullParameter("<this>")
                                                          → 들어오는 순간 터진다
```

- ★★ **null 가능성은 디스크립터에 없다.** 갈리는 것은 **`Intrinsics.checkNotNullParameter` 를 심었느냐**뿐이다.\
  수신자가 그냥 파라미터이기 때문에 **파라미터의 null 규칙이 그대로 적용된 것**이다((1)).
- 멤버 함수였다면 애초에 불가능하다 — **null 에 대고 `invokevirtual` 을 하면 `NullPointerException`** 이다.\
  확장이니까 **`this` 가 null 인 채로 몸통에 들어올 수 있다.**
- 그래서 몸통 안에서 **`this == null` 을 검사해야 한다.** 스마트 캐스트가 거기서 일한다([04번 주제](../04-smart-casts/)).
- `orEmpty()`·`Any?.toString()` 이 stdlib 의 같은 형태다(`M`·`N`).
- 수신자가 `String` 인 쪽에 `String?` 를 넘기면 컴파일이 막는다.

```kotlin
fun String.shout(): String = this + "!"

fun call(s: String?): String = s.shout()
```

**출력** (`kotlinc bad4.kt -d o4`)

```text
===== 소스: bad4.kt =====
fun String.shout(): String = this + "!"

fun call(s: String?): String = s.shout()
===== kotlinc bad4.kt =====
bad4.kt:3:33: error: only safe (?.) or non-null asserted (!!.) calls are allowed on a nullable receiver of type 'String?'.
fun call(s: String?): String = s.shout()
                                ^
```

비용 — 없다. 오히려 null 검사 한 번이 **덜** 심긴다. 대신 **몸통에서 직접 null 을 다뤄야 한다.**

### (7) 확장은 `private` 멤버를 **못 본다**

**언제 쓰나** — 확장으로 클래스 내부를 손보려 할 때.

```kotlin
class Cup(val ml: Int) {
    private val secret: Int = 7
}

fun Cup.peek(): Int = secret
```

**출력** (`kotlinc bad2.kt -d o2`)

```text
===== 소스: bad2.kt =====
class Cup(val ml: Int) {
    private val secret: Int = 7
}

fun Cup.peek(): Int = secret
===== kotlinc bad2.kt =====
bad2.kt:5:23: error: cannot access 'val secret: Int': it is private in 'Cup'.
fun Cup.peek(): Int = secret
                      ^^^^^^
```

- ★ **확장은 클래스 바깥에 있으므로 바깥에서 보이는 것만 본다.** (1)의 `static` 이라는 사실의 직접 귀결이다.
- 그래서 확장은 **캡슐화를 뚫지 못한다** — 남의 타입에 함수를 붙이면서도 안전한 이유다.
- 대신 **`internal` 은 같은 모듈이면 보인다**(모듈 경계의 정본은 [목록의 **18번 주제**](../18-visibility-modifiers/)).

비용 — 없다. **못 하는 것이 값어치인 자리다.**

### (8) ★ 임포트해야 보인다 — 그리고 **그것이 장점이다**

**언제 쓰나** — 다른 패키지의 확장을 쓸 때.

```kotlin
package mylib

fun String.shout(): String = uppercase() + "!"
```

```kotlin
package app

fun call(s: String): String = s.shout()
```

**출력** (`kotlinc imp/lib.kt imp/useNoImport.kt -d oimp`)

```text
===== 소스: imp/lib.kt =====
package mylib

fun String.shout(): String = uppercase() + "!"
===== 소스: imp/useNoImport.kt =====
package app

fun call(s: String): String = s.shout()
===== kotlinc imp/lib.kt imp/useNoImport.kt =====
imp/useNoImport.kt:3:33: error: unresolved reference 'shout' on receiver of type 'String'.
fun call(s: String): String = s.shout()
                                ^^^^^
```

`import` 한 줄을 넣으면 통과한다.

```kotlin
package app

import mylib.shout

fun call2(s: String): String = s.shout()
```

**출력** (`kotlinc imp/lib.kt imp/useWithImport.kt -d oimp2`)

```text
===== 소스: imp/useWithImport.kt =====
package app

import mylib.shout

fun call2(s: String): String = s.shout()
===== kotlinc imp/lib.kt imp/useWithImport.kt =====
(exit 0)
```

- ★ **에러 문구가 정확하다** — `unresolved reference 'shout' on receiver of type 'String'`.\
  "그런 이름이 없다" 가 아니라 **"이 수신자 타입에 그 이름이 안 보인다"** 라고 말한다.
- ★★ **이것이 확장의 핵심 장점이다.** 확장은 **그 파일이 임포트한 만큼만 존재한다.**\
  남이 `String` 에 확장을 100개 붙여도 **내 파일의 `String` 은 깨끗하다** — 전역 오염이 없다.
- 같은 이름의 확장이 두 라이브러리에 있으면 **어느 쪽을 임포트했는지가 결정한다.**\
  `import mylib.shout as loudly` 처럼 별칭도 쓸 수 있다.
- **같은 파일·같은 패키지에서는 임포트가 필요 없다.**

비용 — 임포트 한 줄. IDE 가 자동으로 넣어 주지만 **코드 리뷰에서는 그 줄이 곧 출처 표시**다.

### (9) ★ 소거와 만나는 자리 — **디스크립터가 같아 충돌한다**

**언제 쓰나** — 타입 인자만 다른 확장을 둘 적을 때.

```kotlin
fun List<Int>.describe(): String = "ints"
fun List<String>.describe(): String = "strings"
```

**출력** (`kotlinc bad3.kt -d o3`)

```text
===== 소스: bad3.kt =====
fun List<Int>.describe(): String = "ints"
fun List<String>.describe(): String = "strings"
===== kotlinc bad3.kt =====
bad3.kt:1:1: error: platform declaration clash: The following declarations have the same JVM signature (describe(Ljava/util/List;)Ljava/lang/String;):
    fun List<Int>.describe(): String defined in root package
    fun List<String>.describe(): String defined in root package
fun List<Int>.describe(): String = "ints"
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
bad3.kt:2:1: error: platform declaration clash: The following declarations have the same JVM signature (describe(Ljava/util/List;)Ljava/lang/String;):
    fun List<Int>.describe(): String defined in root package
    fun List<String>.describe(): String defined in root package
fun List<String>.describe(): String = "strings"
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
```

```text
   Kotlin 이 보는 것              JVM 이 보는 것
   +----------------------+      +-------------------------------------------+
   | List<Int>.describe   | ──▶  | describe(Ljava/util/List;)Ljava/lang/String;|
   | List<String>.describe| ──▶  | describe(Ljava/util/List;)Ljava/lang/String;|
   +----------------------+      +-------------------------------------------+
        서로 다른 타입                     **같은 시그니처** — 둘을 못 담는다
```

- ★ **(1)과 (2)가 합쳐진 결과다.** 확장은 **정적 메서드**이고 수신자는 **파라미터**인데,\
  그 파라미터 타입에서 **타입 인자가 소거된다**(`List<Int>` → `java.util.List`).\
  그래서 **오버로드가 성립하지 않는다.**
- 소거가 무엇을 지우는지의 정본은 [`../../../java/syntax/19-type-erasure/`](../../../java/syntax/19-type-erasure/) 이고,\
  Kotlin 이 그것을 **뚫는 방법**은 [12번 주제](../12-reified-type-parameters/)다.
- 고치는 법은 **JVM 쪽 이름을 따로 주는 것**이다.

```kotlin
@JvmName("describeInts")
fun List<Int>.describe(): String = "ints"

@JvmName("describeStrings")
fun List<String>.describe(): String = "strings"

fun main() {
    println("I listOf(1,2).describe()   : ${listOf(1, 2).describe()}")
    println("J listOf(\"a\").describe()   : ${listOf("a").describe()}")
}
```

**출력** (`java -cp ojn:kotlin-stdlib.jar JnKt`)

```text
I listOf(1,2).describe()   : ints
J listOf("a").describe()   : strings
```

**출력** (`javap -s -p ojn/JnKt.class`)

```text
Compiled from "jn.kt"
public final class JnKt {
  public static final java.lang.String describeInts(java.util.List<java.lang.Integer>);
    descriptor: (Ljava/util/List;)Ljava/lang/String;

  public static final java.lang.String describeStrings(java.util.List<java.lang.String>);
    descriptor: (Ljava/util/List;)Ljava/lang/String;

  public static final void main();
    descriptor: ()V

  public static void main(java.lang.String[]);
    descriptor: ([Ljava/lang/String;)V
}
```

- ★ **Kotlin 쪽 호출은 `describe()` 그대로다.** 바뀐 것은 **클래스 파일의 이름뿐**이고,\
  고르는 일은 여전히 **컴파일 타임에 선언 타입으로** 한다.
- `@JvmName` 전체의 정본은 [목록의 **39번 주제**](../39-java-interop-annotations/)다.

비용 — 애너테이션 두 줄. Java 에서 볼 이름이 달라진다.

### (10) 최상위 확장에는 `open`/`override` 라는 낱말이 **안 붙는다**

**언제 쓰나** — 확장으로 다형성을 흉내 내려 할 때.

```kotlin
open class Animal
class Dog : Animal()

open fun Animal.speak(): String = "animal"
override fun Dog.speak(): String = "dog"
```

**출력** (`kotlinc bad5.kt -d o5`)

```text
===== 소스: bad5.kt =====
open class Animal
class Dog : Animal()

open fun Animal.speak(): String = "animal"
override fun Dog.speak(): String = "dog"
===== kotlinc bad5.kt =====
bad5.kt:4:1: error: modifier 'open' is not applicable to 'top level function'.
open fun Animal.speak(): String = "animal"
^^^^
bad5.kt:5:1: error: modifier 'override' is not applicable to 'top level function'.
override fun Dog.speak(): String = "dog"
^^^^^^^^
```

- ★ **「오버라이드되지 않는다」보다 「오버라이드라는 낱말이 아예 안 붙는다」가 정확하다.**\
  컴파일러는 확장을 특별 취급하지 않는다 — 그냥 **최상위 함수**라서 거부한다.
- ★ 그래서 (4)의 **멤버 확장**은 에러가 안 났던 것이다. 그쪽은 최상위 함수가 아니다.
- 다형성이 필요하면 **확장이 아니라 인터페이스**를 쓴다.

비용 — 없다. **설계 선택을 컴파일러가 앞당겨 알려 준다.**

### (11) Java 에서 보면 — **수신자를 첫 인자로 주는 정적 메서드**

**언제 쓰나** — Kotlin 확장을 Java 에서 부를 때.

```java
public class UseExt {
    public static void main(String[] a) {
        System.out.println("O Java: NulKt.orNone(null)  : " + NulKt.orNone(null));
        System.out.println("P Java: NulKt.shout(\"hi\")    : " + NulKt.shout("hi"));
    }
}
```

**출력** (`javac -cp onul:kotlin-stdlib.jar UseExt.java -d oj` → `java -cp oj:onul:kotlin-stdlib.jar UseExt`)

```text
O Java: NulKt.orNone(null)  : none
P Java: NulKt.shout("hi")    : hi!
```

- ★ **Java 에는 점 찍는 문법이 없다.** `NulKt.orNone(s)` 처럼 **파일 클래스의 정적 메서드**로 부른다.\
  (1)에서 본 그대로이고, 이 호출이 **확장이 정적 메서드라는 것의 마지막 확인**이다.
- 파일 클래스 이름은 `<파일명>Kt` 다. `@JvmName` 으로 바꿀 수 있다([목록의 **39번 주제**](../39-java-interop-annotations/)).

비용 — Java 쪽에서는 **확장이라는 문법적 편의가 통째로 사라진다.**

## 문법 — 형태와 규칙

```kotlin
// 1) 확장 함수 — 수신자 타입을 이름 앞에 적는다
fun Money.doubled(): Money = Money(won * 2)        // this 를 생략하고 멤버를 쓸 수 있다
fun Money.plus(o: Money) = Money(won + o.won)      // 인자도 받는다
fun String?.orNone(): String = this ?: "none"      // nullable 수신자

// 2) 확장 프로퍼티 — get() 만 된다
val Money.label: String get() = "${won}원"
var Money.tag: String                               // var 는 set 도 필요하다
    get() = "t$won"
    set(v) { /* 저장할 곳이 없다 — 바깥 저장소가 필요하다 */ }
// val Money.bad: Int = 1                           // ERROR: no backing field

// 3) 제네릭 확장
fun <T> List<T>.second(): T = this[1]
fun <T : Comparable<T>> List<T>.maxOrFirst(): T = maxOrNull() ?: this[0]

// 4) 클래스 안에 선언하면 수신자가 둘이다 — open/override 가 된다
open class Printer {
    open fun Animal.render(): String = "Printer/Animal"
    fun show(a: Animal): String = a.render()
}

// 5) 임포트
// import mylib.shout
// import mylib.shout as loudly

// 6) JVM 이름 충돌을 풀 때
@JvmName("describeInts")
fun List<Int>.describe(): String = "ints"
```

금지 사례(에러가 나는 형태).

```kotlin
val Cup.cups: Int = ml / 200        // ERROR: extension property cannot be initialized …
fun Cup.peek(): Int = secret        // ERROR: cannot access 'val secret' … it is private in 'Cup'
fun call(s: String?) = s.shout()    // ERROR: only safe (?.) or non-null asserted (!!.) calls …
open fun Animal.speak() = "a"       // ERROR: modifier 'open' is not applicable to 'top level function'
fun List<Int>.describe() = "i"      // ERROR: platform declaration clash (List<String> 짝이 있을 때)
fun List<String>.describe() = "s"
```

규칙 불릿.

- **확장은 `static` 함수다.** 수신자는 **첫 파라미터**이고 이름은 `<this>` 다.
- **정적 디스패치다.** 고르는 기준은 **변수의 선언 타입**이지 객체의 실제 타입이 아니다.
- **멤버가 이긴다.** 상속해 온 멤버도 이긴다. 시그니처가 다르면 확장이 산다.
- **확장 프로퍼티에는 backing field 가 없다.** `get()` 으로만 만든다.
- **`private` 멤버를 못 본다.** `internal` 은 같은 모듈이면 본다.
- **임포트해야 보인다** — 그리고 그 덕에 전역이 안 더러워진다.
- **최상위 확장에는 `open`/`override` 가 안 붙는다.** 클래스 멤버로 선언한 확장에는 붙는다.

## 어디서 틀리나

| 틀리는 형태 | 무슨 일이 일어나나 | 고치는 법 |
|---|---|---|
| 확장이 클래스에 들어간다고 생각 | `Money.class` 에 없다. `IcodeKt` 의 `static` 메서드다 | `javap` 로 한 번 확인한다 |
| 상위 타입 변수로 확장을 부름 | **상위 타입 쪽 확장**이 불린다(`D Animal(ext)`) | 다형성이 필요하면 확장이 아니라 인터페이스 |
| 멤버와 같은 시그니처로 확장을 만듦 | **경고만 나고 조용히 무시된다** | 이름을 바꾼다. 경고를 에러로 올린다 |
| 더 좁은 타입에 달면 이긴다고 생각 | **상속한 멤버에게도 진다**(`Q Base.member`) | 「멤버 먼저, 확장 나중」이 절대 규칙이다 |
| 확장 프로퍼티에 `= 값` | `extension property cannot be initialized …` | `get()` 으로 계산한다 |
| 에러 첫 줄(`unresolved reference`)만 읽음 | 진짜 원인은 **둘째 줄**이다 | 진단을 끝까지 읽는다 |
| 확장으로 `private` 를 만짐 | `cannot access … it is private in 'Cup'` | 클래스 안으로 넣거나 `internal` 로 연다 |
| `String?` 를 `String` 수신자에 넘김 | `only safe (?.) or non-null asserted (!!.) calls …` | 수신자를 `String?` 로 선언하거나 `?.` |
| `String?` 수신자 몸통에서 `this` 를 바로 씀 | `this` 가 **null 일 수 있다** | 몸통에서 `this == null` 을 먼저 본다 |
| 타입 인자만 다른 확장 둘 | `platform declaration clash` — **소거 때문** | `@JvmName` 으로 가른다 |
| 최상위 확장에 `open`/`override` | `modifier … is not applicable to 'top level function'` | 인터페이스로 푼다 |
| 「확장은 오버라이드가 안 된다」로 외움 | **클래스 멤버 확장은 된다** — 확장 수신자만 정적이다 | 최상위/멤버를 갈라 기억한다 |
| 임포트 없이 다른 패키지 확장 사용 | `unresolved reference 'shout' on receiver of type 'String'` | `import mylib.shout` |
| Java 에서 점 찍어 부르려 함 | 그런 문법이 없다 | `NulKt.orNone(s)` 로 부른다 |

## 구현 세부사항 대 언어 보장

| 사실 | 누가 보장하나 | 근거 |
|---|---|---|
| 확장이 수신자를 **첫 인자로 받는** 함수인 것 | **언어** | 문서 + `javap` + Java 호출 |
| **정적 디스패치** — 선언 타입으로 고르는 것 | **언어** | 문서 + 실행(`C`/`D`) |
| 멤버가 확장을 이기는 것 | **언어** | 문서 + 실행(`F`) + 경고 |
| **상속한 멤버도** 이기는 것 | **언어** | 실행(`Q`) + 경고문의 `defined in 'Base'` |
| 확장 프로퍼티에 backing field 가 없는 것 | **언어** | 컴파일 에러 |
| 확장이 `private` 멤버를 못 보는 것 | **언어** | 컴파일 에러 |
| nullable 수신자 확장이 되는 것 | **언어** | 실행(`K`) + 컴파일 에러(`bad4`) |
| 임포트가 필요한 것 | **언어** | 컴파일 에러 |
| 최상위 확장에 `open`/`override` 가 안 붙는 것 | **언어** | 컴파일 에러 |
| 멤버 확장의 **디스패치 수신자가 가상**인 것 | **언어** | 실행(`R`/`S`) |
| 멤버 확장의 **확장 수신자가 정적**인 것 | **언어** | 실행(`R`/`S`) |
| 타입 인자만 다른 확장이 충돌하는 것 | **언어(JVM 타깃)** | 컴파일 에러 |
| **`IcodeKt` 라는 파일 클래스에 담기는 것** | **구현** | `javap` |
| **`invokestatic` 이라는 명령 이름** | **구현** ★ | `javap` |
| **파라미터 이름이 `<this>` 인 것** | **구현** ★ | `javap` |
| **확장 프로퍼티가 `getLabel(Money)` 인 것** | **구현** | `javap` |
| **`Intrinsics.checkNotNullParameter` 를 심는 것** | **구현** | `javap` ([03번 주제](../03-null-safe-types/)) |
| **멤버 확장이 인스턴스 메서드 `render(Animal)` 인 것** | **구현** | `javap` |
| 경고 문구(`this extension is shadowed by a member: …`) | **구현** | 컴파일 출력 |

★ **가장 중요한 구분 한 줄** — **「`invokestatic` 이 나온다」는 `javap` 로 본 구현이고,\
언어가 약속하는 것은 「선언 타입으로 고른다」 쪽이다.**\
명령 이름이 아니라 **「디스패치되지 않는다」는 성질**을 외운다.

## 언제 쓰고 언제 안 쓰나

| 상황 | 고르는 것 | 왜 |
|---|---|---|
| 남의 타입(`String`·`LocalDate`)에 내 도메인 말을 붙일 때 | 확장 | 클래스를 안 열고 어휘만 늘린다 |
| 그 동작이 **하위 타입마다 달라져야** 할 때 | 멤버 또는 인터페이스 | 확장은 **못 고른다**((2)) |
| 내가 소유한 클래스의 핵심 동작 | 멤버 | 확장으로 흩어 놓을 이유가 없다 |
| 내부 상태를 읽어야 할 때 | 멤버 | 확장은 `private` 를 못 본다((7)) |
| 상태를 **저장**해야 할 때 | 멤버 프로퍼티 | 확장에는 backing field 가 없다((5)) |
| null 일 수 있는 값을 자연스럽게 다룰 때 | `T?` 수신자 확장 | `?.` 없이 부를 수 있다((6)) |
| 유틸 클래스(`StringUtils`)를 만들려 할 때 | 확장 | 호출부가 `s.shout()` 로 읽힌다 |
| 공개 API 로 내놓을 때 | 멤버를 먼저 고려 | 확장은 **나중에 멤버가 생기면 조용히 진다**((3)) |
| Java 에서도 많이 쓸 API | 멤버 또는 `@JvmName` 붙인 확장 | Java 에서는 정적 메서드로만 보인다((11)) |
| 타입 인자만 다른 두 확장이 필요할 때 | `@JvmName` 으로 가른다 | 소거 때문에 충돌한다((9)) |
| 블록 안에서 `this` 를 바꾸고 싶을 때 | 수신자 지정 람다 | [목록의 **37번 주제**](../37-lambdas-with-receiver-and-type-safe-builders/)가 정본이다 |

판단 규칙 두 줄.

- **「이 동작이 타입마다 달라질 수 있나」로 정한다.** 달라질 수 있으면 확장은 틀린 도구다 — **고를 수가 없다.**
- **「내가 이 클래스를 고칠 수 있나」로 정한다.** 고칠 수 있으면 대개 멤버가 맞다.\
  확장의 값어치는 **못 고치는 타입**에서 나온다.

## 핵심 문장

- ★★ **확장은 멤버가 아니다.** `static` 메서드이고 **수신자가 첫 파라미터**다 — `javap` 의 `descriptor: (LMoney;)LMoney;` 와\
  `Intrinsics.checkNotNullParameter` 에 넘어가는 이름 **`<this>`** 가 그 증거다.
- ★★ **정적 디스패치** — 같은 객체라도 **변수의 선언 타입**이 무엇을 부를지 정한다(`C Dog(ext)` 대 `D Animal(ext)`).\
  멤버는 정반대로 **둘 다 `Dog(member)`** 다.
- 그 차이는 **`invokestatic` 과 `invokevirtual`** 로 갈린다. `invokestatic` 은 **실행할 때 다시 찾지 않는다.**
- ★ **멤버가 이긴다 — 상속해 온 멤버도 이긴다.** `Derived` 확장이 `Base` 멤버에게 졌다(`Q Base.member`).\
  에러가 아니라 **경고**이고, 시그니처가 다르면 확장은 산다(`H extension(x)`).
- ★★ **클래스 안에 선언한 확장은 수신자가 둘**이다 — **디스패치 수신자는 가상, 확장 수신자는 정적**(`R Printer/Animal` 대 `S LoudPrinter/Animal`).\
  그래서 **「확장은 오버라이드가 안 된다」는 최상위 확장에만 맞다.**
- **확장 프로퍼티에는 backing field 가 없다.** `= 값` 은 컴파일 에러이고 `get()` 만 된다.
- **확장은 `private` 멤버를 못 본다.** 캡슐화를 뚫지 못하는 것이 안전의 근거다.
- ★ **nullable 수신자 확장이 되는 이유는 null 검사를 안 심기 때문**이다. 디스크립터는 `String` 수신자와 **한 글자도 같다.**
- **임포트해야 보인다** — 확장은 **그 파일이 임포트한 만큼만 존재한다.** 전역 오염이 없다.
- ★ **타입 인자만 다른 확장은 소거 때문에 충돌한다**(`platform declaration clash`). `@JvmName` 으로 가른다.
- Java 에서는 **`NulKt.orNone(s)`** 처럼 정적 메서드로 부른다 — 점 찍는 문법이 통째로 사라진다.

## 관련 자료

- [`../README.md`](../README.md) — Kotlin 문법·API 주제 목록(이 주제는 13번)
- ★ [`../../언어-특성/README.md`](../../언어-특성/README.md) §7 — **정적 디스패치라는 천장의 *의미* 가 거기 정본이다.**\
  **왜 그 대가를 치르고도 확장을 쓰나**(클래스를 안 열고 어휘를 늘리는 값)와 DSL 논지는 거기까지,\
  **여기는 선언 문법·해소 순서·멤버 충돌 규칙부터**다
- [08번 주제](../08-function-declaration-default-and-named-args/) — **직접 선행.** 함수 선언·기본 인자·`@JvmOverloads`.\
  확장에도 기본 인자를 그대로 쓸 수 있다
- [10번 주제](../10-lambdas-and-higher-order-functions/) — 함수 타입과 람다. **수신자 지정 함수 타입**(`Int.() -> String`)이\
  `Function1` 로 내려가는 것이 거기 있다 — 이 문서의 **첫 파라미터**와 같은 이야기다
- [12번 주제](../12-reified-type-parameters/) — **소거를 뚫는 법.** (9)의 `platform declaration clash` 가\
  소거에서 온 것이고, 그것을 함수 쪽에서 푸는 방법이 거기다
- [`../../../java/syntax/19-type-erasure/`](../../../java/syntax/19-type-erasure/) — **소거의 정본.**\
  `List<Int>` 와 `List<String>` 이 왜 같은 디스크립터가 되는지는 거기까지, 여기는 **그것이 확장에서 내는 에러**부터
- ★ [`../../../java/syntax/11-interfaces-default-methods/`](../../../java/syntax/11-interfaces-default-methods/) — **Java 쪽 짝.**\
  둘 다 「남의 타입에 메서드 추가」인데 **디스패치가 정반대**다(아래 「더 들어가면」)
- [03번 주제](../03-null-safe-types/) — `Intrinsics.checkNotNullParameter` 의 정본.\
  (6)의 「검사를 안 심는다」가 거기 위에 서 있다. `String?.orEmpty()` 같은 nullable 수신자 확장도 거기서 먼저 나왔다
- [04번 주제](../04-smart-casts/) — nullable 수신자 몸통에서 `this == null` 을 검사한 뒤 쓰는 것
- [09번 주제](../09-varargs-spread-local-and-infix-functions/) — `infix` **확장** 함수의 형태와 우선순위
- [목록의 **14번 주제**](../14-scope-functions/)(scope function) — `let`/`run`/`apply`/`also` 가 전부 **확장 함수**다. 이 문법의 대표 사용처
- [목록의 **16번 주제**](../16-properties-backing-field-lateinit-const/)(프로퍼티 — backing field·`field`) — (5)에서 「없다」고 한 그것의 정본
- [목록의 **18번 주제**](../18-visibility-modifiers/)(가시성 수식어) — `internal` 이 확장에서 보이는 범위
- [목록의 **31번 주제**](../31-operator-overloading-infix-and-invoke/)(연산자 오버로딩·`invoke` 규약) — `operator fun` 확장으로 기호를 만드는 것
- [목록의 **36번 주제**](../36-function-types-fun-interface-and-sam-conversion/)(함수 타입·`fun interface`·SAM) · [목록의 **37번 주제**](../37-lambdas-with-receiver-and-type-safe-builders/)(수신자 지정 람다와 DSL) — `A.() -> Unit` 의 정본
- [목록의 **39번 주제**](../39-java-interop-annotations/)(Java 상호운용 애너테이션) — `@JvmName` 전체. 여기서는 **충돌 해소 도구로만** 썼다
- [목록의 **40번 주제**](../40-read-only-collections-and-runtime-types/)\~**48번 주제**(컬렉션·문자열 stdlib) — 그 API 의 상당수가 **확장 함수**다

## 용어 풀이

- **확장 함수(extension function)** — 클래스 바깥에서 선언하지만 `수신자.이름()` 으로 부를 수 있는 함수.
- **수신자(receiver)** — 점 앞에 오는 값. 확장에서는 **첫 파라미터**가 된다.
- **확장 수신자(extension receiver)** — `fun Animal.render()` 의 `Animal` 쪽. **정적**으로 고른다.
- **디스패치 수신자(dispatch receiver)** — 확장을 클래스 멤버로 선언했을 때 그 **클래스 인스턴스** 쪽. **가상**으로 고른다.
- **디스패치(dispatch)** — 이름이 같은 함수 여럿 중 실제로 부를 것을 고르는 일.
- **정적 디스패치(static dispatch)** — **컴파일할 때** 고르는 것. 확장이 이것이다.
- **가상 디스패치(virtual dispatch)** — **실행할 때 객체의 실제 클래스를 보고** 고르는 것. 멤버가 이것이다.
- **`invokestatic` / `invokevirtual`** — 각각 정적·가상 호출 JVM 명령. `invokevirtual` 만 실행 시 다시 찾는다.
- **디스크립터(descriptor)** — JVM 이 메서드를 식별하는 문자열. `(LMoney;)LMoney;` 처럼 **타입만** 적힌다.
- **backing field** — 프로퍼티 값을 실제로 담는 숨은 필드. **확장 프로퍼티에는 없다.**
- **shadow(가려짐)** — 확장이 같은 시그니처의 멤버에 밀려 안 불리는 것. 경고로만 알려 준다.
- **타입 소거(type erasure)** — 컴파일 후 타입 인자가 사라지는 것. `List<Int>` 가 `java.util.List` 가 된다.
- **platform declaration clash** — 서로 다른 Kotlin 선언이 **같은 JVM 시그니처**가 되어 나는 에러.
- **`@JvmName`** — 그 선언이 클래스 파일에서 가질 이름을 지정하는 애너테이션.
- **파일 클래스** — 최상위 선언들이 담기는 자동 생성 클래스. `nul.kt` → `NulKt`.
- **`Intrinsics.checkNotNullParameter`** — 컴파일러가 non-null 파라미터에 심는 런타임 검사.

---

## 더 들어가면

- ★★ **Java 의 `default` 메서드와 정확히 반대다.** 둘 다 「남의 타입에 메서드를 추가한다」인데 디스패치가 뒤집혀 있다.

| | Kotlin 확장 함수 | Java `default` 메서드 |
|---|---|---|
| 어디에 선언하나 | 클래스 **밖** | 인터페이스 **안** |
| 컴파일 결과 | `static` 메서드 + 수신자 첫 파라미터 | 인터페이스의 **인스턴스 메서드** |
| 호출 명령 | `invokestatic` | `invokeinterface` |
| 디스패치 | **정적** — 선언 타입 | **가상** — 실제 타입 |
| 하위 타입이 바꿀 수 있나 | **없다** | **`override` 로 바꾼다** |
| 원 타입을 고쳐야 하나 | **아니다** | **인터페이스를 고쳐야 한다** |
| 임포트 | 필요하다 | 필요 없다 |

  정본은 [`../../../java/syntax/11-interfaces-default-methods/`](../../../java/syntax/11-interfaces-default-methods/) 다.\
  **확장은 「안 고쳐도 된다」를 사고, 「고를 수 없다」를 판다.** `default` 메서드는 그 반대다.
- ★ **같은 이름의 확장이 `Any` 와 `String` 에 둘 다 있으면 무엇이 불리나** — 던져서 확인했다.\
  여기서도 기준은 **선언 타입**이다.

```kotlin
class Cup {
    val size: Int = 1
}

val Cup.size: Int get() = 99

fun Any.kind(): String = "Any"
fun String.kind(): String = "String"

fun main() {
    println("T member property vs extension property : ${Cup().size}")
    val s: Any = "hi"
    println("U ext on Any vs String, var typed Any   : ${s.kind()}")
    println("V ext on Any vs String, literal String  : ${"hi".kind()}")
}
```

**출력** (`kotlinc probe3.kt -d op3` → `java -cp op3:kotlin-stdlib.jar Probe3Kt`)

```text
===== 소스: probe3.kt =====
class Cup {
    val size: Int = 1
}

val Cup.size: Int get() = 99

fun Any.kind(): String = "Any"
fun String.kind(): String = "String"

fun main() {
    println("T member property vs extension property : ${Cup().size}")
    val s: Any = "hi"
    println("U ext on Any vs String, var typed Any   : ${s.kind()}")
    println("V ext on Any vs String, literal String  : ${"hi".kind()}")
}
===== kotlinc probe3.kt =====
probe3.kt:5:9: warning: this extension is shadowed by a member: 'val size: Int' defined in 'Cup'.
val Cup.size: Int get() = 99
        ^^^^
(exit 0)
===== java Probe3Kt =====
T member property vs extension property : 1
U ext on Any vs String, var typed Any   : Any
V ext on Any vs String, literal String  : String
```

  **`s` 안에 들어 있는 것은 `"hi"` 인데 `Any` 쪽이 불린다**(`U`). (2)와 같은 규칙이 **확장끼리의 경쟁**에도 적용된다.\
  ★ **확장 프로퍼티도 멤버 프로퍼티에 진다**(`T` 가 99 가 아니라 1)는 것과, **경고 문구가 `val size: Int` 로 프로퍼티를 가리킨다**는 것도 같이 나왔다.
- **stdlib 은 이 문법 위에 서 있다.** `String.isBlank()`·`List.map()`·`let`/`apply`·`Any?.toString()` 이 전부 확장이다.\
  그래서 `kotlin-stdlib.jar` 를 `javap` 로 열면 `StringsKt`·`CollectionsKt` 같은 **정적 메서드 덩어리**가 보인다.\
  (**이 문서에서는 `NulKt`·`IcodeKt` 같은 내 파일만 찍었고 stdlib 클래스는 안 찍었다.**)
- **확장 프로퍼티에 상태를 붙이는 관용구**는 바깥 `Map` 을 쓰는 것이다 —\
  키가 수신자 객체이므로 **누수가 생기기 쉽다**(약한 참조가 필요하다). **이 문서에서는 그 형태를 돌려 보지 않았다.**
- ★ **이 문서에서 성능은 한 번도 재지 않았다.** `javap` 로 본 것은 **명령어가 `invokestatic` 이냐 `invokevirtual` 이냐**까지이고,\
  "그래서 어느 쪽이 빠르다" 는 하지 않은 주장이다.
- **못 잰 것** — 「라이브러리가 나중에 같은 이름의 멤버를 추가하면 내 확장이 죽는다」는 (3)의 경고로 **성질만 확인**했고,\
  **실제로 버전을 올려 재현하지는 않았다**(그러려면 같은 라이브러리의 두 판본이 필요하다).
