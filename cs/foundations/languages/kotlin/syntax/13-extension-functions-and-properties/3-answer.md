# kotlin/syntax/13 — 확장 함수·확장 프로퍼티: 정적 디스패치 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 모든 출력·에러·경고·바이트코드는 **kotlinc 2.4.20 (JRE 21.0.5)** 과 Temurin **JDK 21.0.5** 의 `javap` 에서 실제로 얻었다.\
> **Java 쪽 호출은 같은 JDK 의 `javac` 로 컴파일해 실제로 섞어 돌렸다**(10번).\
> 역어셈블은 **기본 `-jvm-target`(1.8 · `major version: 52`)** 이 정본이다 —\
> 그래서 문자열 보간이 `StringBuilder` 로 보인다([02번 주제](../02-string-templates-and-raw-strings/)).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★ **파일 클래스의 `static` 메서드**가 되고 수신자는 **첫 파라미터**다

**출력** (`javap -c -p -s out/IcodeKt.class` — 앞 세 메서드)

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
```

**왜 그런가**

- ★★ **`Money.class` 안이 아니라 파일 클래스 `IcodeKt` 안**에 `public static final` 로 들어간다.
  `Money.class` 를 아무리 찍어도 `doubled` 는 없다.
- ★★ **디스크립터가 `(LMoney;)LMoney;`** 다 — **인자를 하나도 안 적었는데 파라미터가 하나**다.
  수신자가 첫 파라미터로 내려간 것이고, 호출부(`use`)는 `invokestatic` 두 번이다.
- ★ **가장 짧은 증거는 `Intrinsics.checkNotNullParameter` 에 넘어가는 이름이 `<this>` 라는 것**이다.
  컴파일러가 그 파라미터를 **"이건 `this` 다"** 라고 이름 붙여 놓았다([03번 주제](../03-null-safe-types/)).
- **확장 프로퍼티는 `getLabel(Money)` 라는 정적 게터**가 된다. **필드는 없다** — 7번이 그 결과다.

### 2. ★★ `Dog(member)` · `Dog(member)` · `Dog(ext)` · **`Animal(ext)`** · `true`

**출력** (`java -cp odisp:kotlin-stdlib.jar DispKt`)

```text
A asDog.speakMember()    : Dog(member)
B asAnimal.speakMember() : Dog(member)
C asDog.speakExt()       : Dog(ext)
D asAnimal.speakExt()    : Animal(ext)
E same object?           : true
```

**왜 그런가**

```text
   두 변수 모두 Dog 객체를 가리킨다 (E: true)

        asDog: Dog  ─┐                 ┌─ speakMember() ─▶ Dog(member)   ← 객체를 본다
                     ├──▶  [ Dog 객체 ]┤
     asAnimal: Animal┘                 └─ speakMember() ─▶ Dog(member)   ← 객체를 본다

        asDog: Dog     ──▶ speakExt() ─▶ Dog(ext)      ← 변수 타입을 본다 ★
     asAnimal: Animal  ──▶ speakExt() ─▶ Animal(ext)   ← 변수 타입을 본다 ★
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

- **멤버는 `invokevirtual`, 확장은 `invokestatic`** 이다.
- ★★ **한 문장으로** — **`invokevirtual` 은 실행할 때 객체의 실제 클래스에서 다시 찾고, `invokestatic` 은 다시 찾지 않는다.**
  그래서 멤버는 둘 다 `Dog` 것이 돌고, 확장은 **적힌 대로** 돈다.
- ★ **두 `speakExt` 는 JVM 에서 파라미터 타입이 다른 오버로드**다 — **수신자가 파라미터이기 때문에** 공존한다(1번).

```text
  public static final java.lang.String speakExt(Animal);
    descriptor: (LAnimal;)Ljava/lang/String;

  public static final java.lang.String speakExt(Dog);
    descriptor: (LDog;)Ljava/lang/String;
```

### 3. ★★ 컴파일은 **통과**한다 — 경고 1건, 그리고 **멤버가 이긴다**

**출력** (`kotlinc shadow.kt -d oshadow`)

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

**왜 그런가**

- ★ **에러가 아니라 경고 1건이고 `exit 0`** 이다. 확장은 조용히 무시되고 프로그램은 돈다.
- **경고는 시그니처가 정확히 겹치는 선언에만 붙는다.** `pour(s: String)` 은 멤버에 짝이 없어
  **경고도 없고 실제로 불린다**(`H`).
- ★ **그래서 이 갈래에서 유난히 잘 놓친다** — **컴파일은 통과하고 동작만 내 뜻과 다르다.**
  라이브러리가 나중에 같은 이름의 멤버를 추가하면 **내 확장이 조용히 죽고 경고만 남는다.**
  (★ 그 시나리오는 **실제로 버전을 올려 재현하지는 않았다** — 같은 라이브러리의 두 판본이 필요하다.)

### 4. ★★ `Base.member` · `1` · `Any` · `String` — **상속한 멤버도 이긴다**

**출력** (`kotlinc probe1.kt -d op1` → `java -cp op1:kotlin-stdlib.jar Probe1Kt`)

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

**왜 그런가**

- ★★ **`Q` 가 `Base.member` 다.** `Derived` 확장이 `Base` **멤버에게 졌다** —
  **「더 구체적인 쪽이 이긴다」가 통하지 않는 유일한 자리**다.
- **경고문이 `defined in 'Base'` 라고 어느 클래스의 멤버에게 졌는지 알려 준다.**
- **해소 순서를 한 문장으로** — **멤버(상속 포함)를 먼저 다 보고, 없을 때만 확장을 본다.**
- ★ **확장 프로퍼티도 멤버 프로퍼티에 진다**(`T` 가 99 가 아니라 **1**). 경고 문구가 `val size: Int` 로 프로퍼티를 가리킨다.
- ★ **`U`/`V` 는 2번과 같은 규칙이다.** `s` 안에 든 것은 `"hi"` 인데 **선언 타입이 `Any` 라 `Any` 쪽이 불린다.**
  **확장끼리의 경쟁에도 정적 디스패치가 그대로 적용된다.**

### 5. ★★ 컴파일된다 — **수신자가 둘**이고 한쪽만 가상이다

**출력** (`kotlinc probe2.kt -d op2` → `java -cp op2:kotlin-stdlib.jar Probe2Kt`)

```text
===== kotlinc probe2.kt =====
(exit 0)
===== java Probe2Kt =====
R Printer().show(Dog)      : Printer/Animal
S LoudPrinter().show(Dog)  : LoudPrinter/Animal
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

**왜 그런가**

- **경고도 에러도 없다**(`exit 0`). 클래스 멤버로 선언한 확장에는 **`open`/`override` 가 붙고 실제로 가상 디스패치된다.**
- ★★ **`static` 이 아니다** — `public java.lang.String render(Animal);` 로 **인스턴스 메서드**다.
  `Printer` 인스턴스가 **디스패치 수신자**이고, 확장 수신자만 파라미터로 들어갔다.

```text
      Printer / LoudPrinter   ← 디스패치 수신자 : **가상**  ▶ R 과 S 가 갈린다
            │
            └── Animal / Dog  ← 확장 수신자     : **정적**  ▶ 둘 다 Animal 쪽
```

- ★★ **`invokevirtual` 한 명령어에 두 성질이 같이 들어 있다.**
  `aload_0`(디스패치 수신자)은 실행할 때 클래스를 다시 찾으므로 **가상**인데,
  **디스크립터 `(LAnimal;)` 이 이미 박혀 있어** 확장 수신자는 **정적**이다.
  `R`/`S` 가 갈리는 것과 둘 다 `Animal` 인 것이 **한 명령어에서 동시에** 일어난다.
- ★ 그래서 **「확장은 오버라이드할 수 없다」는 최상위 확장에만 맞다**(10번).

### 6. ★ `none` · `hi` · `''` · `null` — 갈리는 것은 **검사를 심었느냐**뿐이다

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

**왜 그런가**

- ★★ **두 디스크립터는 한 글자도 다르지 않다**(`(Ljava/lang/String;)Ljava/lang/String;`).
  **null 가능성은 디스크립터에 안 남는다.**
- ★ **갈리는 것은 `Intrinsics.checkNotNullParameter` 를 심었느냐 한 줄**이다.
  `shout` 의 3번 자리에 그것이 있고 `orNone` 에는 **없다** —
  수신자가 그냥 파라미터이므로 **파라미터의 null 규칙이 그대로 적용된 것**이다(1번).
- **멤버였다면 애초에 불가능하다** — null 에 `invokevirtual` 을 하면 `NullPointerException` 이다.
  확장이니까 **`this` 가 null 인 채로 몸통에 들어올 수 있고**, 몸통에서 `this == null` 을 검사한다([04번 주제](../04-smart-casts/)).
- **`String` 수신자에 `String?` 를 넘기면 컴파일이 막는다.**

```text
===== 소스: bad4.kt =====
fun String.shout(): String = this + "!"

fun call(s: String?): String = s.shout()
===== kotlinc bad4.kt =====
bad4.kt:3:33: error: only safe (?.) or non-null asserted (!!.) calls are allowed on a nullable receiver of type 'String?'.
fun call(s: String?): String = s.shout()
                                ^
```

### 7. 확장 프로퍼티에는 **칸이 없고**, 확장은 **금고를 못 연다**

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

**왜 그런가**

- **에러는 두 줄**이고, ★ **눈에 먼저 들어오는 첫 줄이 진짜 원인이 아니다.**
  `unresolved reference 'ml'` 은 "초기화 식에서는 아직 수신자가 없다" 는 **부수 증상**이고,
  근본은 **둘째 줄** `extension property cannot be initialized because it has no backing field` 다.
- **둘 다 1번에서 곧바로 따라 나온다** — 확장은 **클래스 밖의 `static` 함수**다.
  그러니 **값을 넣어 둘 칸이 남의 클래스에 생기지 않고**(`get()` 으로 계산해야 한다),
  **바깥에서 보이는 것만 본다**(`private` 을 못 본다. `internal` 은 같은 모듈이면 보인다).
- ★ **`private` 을 못 보는 것은 값어치다** — 남의 타입에 함수를 붙이면서도 **캡슐화를 뚫지 못한다.**
  backing field 의 정본은 [목록의 **16번 주제**](../16-properties-backing-field-lateinit-const/), 모듈 경계는 [목록의 **18번 주제**](../18-visibility-modifiers/)다.

### 8. `unresolved reference … on receiver of type 'String'` — 그래서 전역이 안 더러워진다

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

**출력** (`kotlinc imp/lib.kt imp/useWithImport.kt -d oimp2`)

```text
===== 소스: imp/useWithImport.kt =====
package app

import mylib.shout

fun call2(s: String): String = s.shout()
===== kotlinc imp/lib.kt imp/useWithImport.kt =====
(exit 0)
```

**왜 그런가**

- ★ **문구가 정확하다** — 「그런 이름이 없다」가 아니라 「**이 수신자 타입에 그 이름이 안 보인다**」(`on receiver of type 'String'`)다.
  **존재의 문제가 아니라 가시성의 문제**라고 말하는 것이다.
- ★★ **확장은 그 파일이 임포트한 만큼만 존재한다.** 남이 `String` 에 확장을 100개 붙여도
  **내 파일의 `String` 은 깨끗하다** — **전역 오염이 없다.**
- **같은 이름이 두 라이브러리에 있으면 「어느 쪽을 임포트했는지」가 결정한다.**
  `import mylib.shout as loudly` 로 별칭도 쓸 수 있다. **같은 파일·같은 패키지면 임포트가 필요 없다.**

### 9. `platform declaration clash` — **소거 + 수신자가 파라미터**의 합작이다

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

**왜 그런가**

- **에러 이름은 `platform declaration clash`** 이고, 대는 **JVM 시그니처는 `describe(Ljava/util/List;)Ljava/lang/String;`** 다.
- ★ **1번과 2번이 합쳐진 결과다.** 확장은 **정적 메서드**이고 수신자는 **파라미터**인데(1번),
  그 파라미터 타입에서 **타입 인자가 소거된다**(`List<Int>` → `java.util.List`).
  그래서 **2번에서 성립하던 오버로드가 여기서는 성립하지 않는다.**
  소거의 정본은 [`../../../java/syntax/19-type-erasure/`](../../../java/syntax/19-type-erasure/),
  Kotlin 이 함수 쪽에서 그것을 뚫는 방법은 [12번 주제](../12-reified-type-parameters/)다.
- **고치는 법은 `@JvmName` 으로 JVM 쪽 이름을 가르는 것**이다.

**출력** (`java -cp ojn:kotlin-stdlib.jar JnKt` · `javap -s -p ojn/JnKt.class`)

```text
I listOf(1,2).describe()   : ints
J listOf("a").describe()   : strings
```

```text
Compiled from "jn.kt"
public final class JnKt {
  public static final java.lang.String describeInts(java.util.List<java.lang.Integer>);
    descriptor: (Ljava/util/List;)Ljava/lang/String;

  public static final java.lang.String describeStrings(java.util.List<java.lang.String>);
    descriptor: (Ljava/util/List;)Ljava/lang/String;
```

- ★ **Kotlin 쪽 호출 이름은 안 바뀐다** — `describe()` 그대로다. 바뀐 것은 **클래스 파일의 이름뿐**이고,
  고르는 일은 여전히 **컴파일 타임에 선언 타입으로** 한다. `@JvmName` 전체의 정본은 목록의 **39번 주제**다.

### 10. `modifier … is not applicable to 'top level function'` — Java 에서는 `NulKt.orNone(s)`

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

**출력** (`javac -cp onul:kotlin-stdlib.jar UseExt.java -d oj` → `java -cp oj:onul:kotlin-stdlib.jar UseExt`)

```text
O Java: NulKt.orNone(null)  : none
P Java: NulKt.shout("hi")    : hi!
```

**왜 그런가**

- ★ **「오버라이드되지 않는다」보다 「오버라이드라는 낱말이 아예 안 붙는다」가 정확하다.**
  컴파일러는 확장을 특별 취급하지 않는다 — **그냥 최상위 함수**라서 거부한다.
  그래서 5번의 **멤버 확장**은 에러가 안 났던 것이다(그쪽은 최상위 함수가 아니다).
- **Java 에는 점 찍는 문법이 없다.** `NulKt.orNone(s)` 처럼 **파일 클래스의 정적 메서드**로 부른다 —
  1번에서 본 그대로이고, **이 호출이 「확장은 정적 메서드」의 마지막 확인**이다.
- **파일 클래스 이름은 `<파일명>Kt`**(`nul.kt` → `NulKt`)이고 **`@JvmName` 으로 바꿀 수 있다**(목록의 **39번 주제**).

### 11. Java `default` 메서드와 **정확히 반대**다

| | Kotlin 확장 함수 | Java `default` 메서드 |
|---|---|---|
| 어디에 선언하나 | 클래스 **밖** | 인터페이스 **안** |
| 컴파일 결과 | `static` 메서드 + 수신자 첫 파라미터 | 인터페이스의 **인스턴스 메서드** |
| 호출 명령 | `invokestatic` | `invokeinterface` |
| 디스패치 | **정적** — 선언 타입 | **가상** — 실제 타입 |
| 하위 타입이 바꿀 수 있나 | **없다** | **`override` 로 바꾼다** |
| 원 타입을 고쳐야 하나 | **아니다** | **인터페이스를 고쳐야 한다** |
| 임포트 | 필요하다 | 필요 없다 |

- ★ **확장은 「안 고쳐도 된다」를 사고, 「고를 수 없다」를 판다.** `default` 메서드는 그 반대다.
  정본은 [`../../../java/syntax/11-interfaces-default-methods/`](../../../java/syntax/11-interfaces-default-methods/)다.
- **`let`/`run`/`with`/`apply`/`also` 는 전부 확장 함수**다(그리고 전부 `inline` 이다 —
  [11번 주제](../11-inline-functions/)). 이 문법의 대표 사용처이고 정본은 [목록의 **14번 주제**](../14-scope-functions/)다.
- **stdlib 이 이 문법 위에 서 있다** — `String.isBlank()`·`List.map()`·`Any?.toString()` 이 전부 확장이라
  `kotlin-stdlib.jar` 에는 `StringsKt`·`CollectionsKt` 같은 **정적 메서드 덩어리**가 들어 있다.
  (★ **이 문서는 그 stdlib 클래스를 직접 찍어 보지는 않았다** — 내가 만든 파일만 `javap` 했다.)

## 실행 검증

```text
info: kotlinc-jvm 2.4.20 (JRE 21.0.5+11-LTS)
openjdk version "21.0.5" 2024-10-15 LTS
OpenJDK Runtime Environment Temurin-21.0.5+11 (build 21.0.5+11-LTS)
OpenJDK 64-Bit Server VM Temurin-21.0.5+11 (build 21.0.5+11-LTS, mixed mode, sharing)
```

| 프로그램 | 무엇을 확인했나 | 돌린 방법 |
|---|---|---|
| `icode.kt` | 확장이 **`static` + 수신자 첫 파라미터**인 것 · `<this>` · 확장 프로퍼티 게터 | `kotlinc` → `javap -c -p -s` |
| `disp.kt` · `dispcode.kt` | `A`\~`E` — **정적 디스패치** · `invokevirtual` 대 `invokestatic` · 오버로드 | `kotlinc` 2회 → `java` · `javap -s -p` · `javap -c -p` |
| `shadow.kt` | `F`·`G`·`H` — **멤버가 이기는 것**과 경고가 붙는 범위 | `kotlinc`(경고 1건) → `java` |
| `probe1.kt` | `Q` — **상속한 멤버도 이기는 것** · 경고문의 `defined in 'Base'` | `kotlinc`(경고 1건) → `java` |
| `probe3.kt` | `T`·`U`·`V` — 확장 프로퍼티도 지는 것 · **확장끼리도 선언 타입** | `kotlinc`(경고 1건) → `java` |
| `probe2.kt` | `R`·`S` — 멤버 확장의 **수신자 둘** · 한 `invokevirtual` 에 두 성질 | `kotlinc`(무경고) → `java` · `javap -s -p` · `javap -c -p` |
| `bad1.kt` | 확장 프로퍼티에 backing field 가 **없는 것**(에러 2줄) | `kotlinc` (컴파일 실패가 결과) |
| `bad2.kt` | 확장이 `private` 멤버를 **못 보는 것** | `kotlinc` (컴파일 실패가 결과) |
| `nul.kt` | `K`\~`N` · **검사를 안 심는다**는 것(디스크립터는 같다) | `kotlinc` → `java` · `javap -c -p -s` |
| `bad4.kt` | `String` 수신자에 `String?` 를 넘기면 막히는 것 | `kotlinc` (컴파일 실패가 결과) |
| `imp/` 3벌 | 임포트가 **필요한 것**과 그 에러 문구의 정확함 | `kotlinc` 2회 (실패 1 · 통과 1) |
| `bad3.kt` · `jn.kt` | `platform declaration clash` 와 `@JvmName` 으로 가르기 (`I`·`J`) | `kotlinc` 2회 → `java` · `javap -s -p` |
| `bad5.kt` | 최상위 확장에 `open`/`override` 가 **안 붙는 것** | `kotlinc` (컴파일 실패가 결과) |
| `UseExt.java` | Java 에서 **`NulKt.orNone(s)`** 로 부르는 것 (`O`·`P`) | `javac` → `java` |

**구현 의존 항목** — `javap` 의 명령 이름·상수 풀 번호, `IcodeKt`·`NulKt` 라는 파일 클래스 이름,
파라미터 이름 `<this>`, 확장 프로퍼티가 `getLabel(Money)` 인 것, `Intrinsics.checkNotNullParameter` 를 심는 자리,
멤버 확장이 인스턴스 메서드 `render(Animal)` 인 것, 경고 문구 — **전부 이 컴파일러 버전의 산출물**이다.\
반면 **「수신자를 첫 인자로 받는다」·「정적 디스패치」·「멤버가 이긴다(상속 포함)」·「backing field 가 없다」·
「`private` 을 못 본다」·「nullable 수신자가 된다」·「임포트가 필요하다」·「최상위 확장에 `open`/`override` 가 안 붙는다」**
는 **언어 규칙**이라 타깃과 무관하다.

**★ 던져 봤더니 예상과 달랐던 것 — 세 건**

1. ★★ **「확장은 오버라이드가 안 된다」가 반쪽이었다.** **클래스 멤버로 선언한 확장은 `open`/`override` 가 붙고
   실제로 가상 디스패치된다**(`R Printer/Animal` 대 `S LoudPrinter/Animal`).
   정적인 것은 **확장 수신자 쪽**뿐이고, 그 둘이 **한 `invokevirtual` 안에서 동시에** 일어났다.
2. ★ **「더 구체적인 쪽이 이긴다」가 여기서는 틀렸다.** `Derived` 확장이 `Base` **멤버**에게 졌다(`Q Base.member`).
   기준은 구체성이 아니라 「**멤버 먼저, 확장 나중**」이었다.
3. ★ **멤버와 겹친 확장이 에러가 아니라 경고였다.** `exit 0` 으로 통과하고 **동작만 다르다** —
   그리고 **시그니처가 어긋나면 경고조차 안 난다**(`H extension(x)`).

**안 걸린 것도 출력이다** — `probe2.kt` 는 **경고도 에러도 없이** `exit 0` 이었다.
수신자가 둘이 되는 가장 헷갈리는 형태인데 컴파일러가 **아무 말도 하지 않는다** —
「경고가 없다」가 「읽기 쉽다」를 뜻하지 않는다.
