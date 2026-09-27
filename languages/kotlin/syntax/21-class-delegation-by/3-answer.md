# kotlin/syntax/21 — 클래스 위임 (`by`): 상속 대신 합성 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 모든 출력·바이트코드는 **kotlinc 2.4.20 (JRE 21.0.5)** 과 Temurin **JDK 21.0.5** 의 `javap` 에서 실제로 얻었다.\
> 역어셈블은 **기본 `-jvm-target`(1.8 · `major version: 52`)** 이 정본이다.
> ★★ 아래 블록은 전부 **캡처 스크립트가 파일로 받아** 조립한 것이다 — 사람이 옮겨 적은 자리가 없다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ `C` 에서 **`Derived` 의 오버라이드가 안 불린다** — 이 주제의 본체다

**출력**

```text
===== 소스: deleg.kt =====
interface Printer {
    fun printMessage()
    fun printTwice() {
        printMessage()
        printMessage()
    }
}

class BasePrinter(private val x: Int) : Printer {
    override fun printMessage() {
        println("   BasePrinter : $x")
    }
}

class Derived(base: Printer) : Printer by base {
    override fun printMessage() {
        println("   Derived : 내가 가로챘다")
    }
}

fun main() {
    val base = BasePrinter(10)
    println("A base.printTwice()")
    base.printTwice()
    println("B Derived.printMessage()")
    Derived(base).printMessage()
    println("C Derived.printTwice()  ← 함정")
    Derived(base).printTwice()
}
===== kotlinc deleg.kt -d odeleg =====
(exit 0)
===== java -cp odeleg:kotlin-stdlib.jar DelegKt =====
A base.printTwice()
   BasePrinter : 10
   BasePrinter : 10
B Derived.printMessage()
   Derived : 내가 가로챘다
C Derived.printTwice()  ← 함정
   BasePrinter : 10
   BasePrinter : 10
(exit 0)
```

**왜 그런가**

```text
   Derived.printTwice()  ──포워딩──▶  BasePrinter.printTwice()
                                           │
                                           │ 안에서 printMessage() 를 부른다
                                           v
                                       this = BasePrinter
                                           │
                                           v
                                       BasePrinter.printMessage()
                                       ★ Derived 의 override 는 안 불린다
```

- ★★★ **`this` 가 둘이다.** `Derived` 객체와 `BasePrinter` 객체는 **서로 다른 객체**이고, `BasePrinter.printTwice()` 가 도는 동안 `this` 는 **`BasePrinter` 자신**이다.\
  `BasePrinter` 는 자기를 감싼 `Derived` 가 있다는 것을 **모른다.**
- `B` 는 `Derived` 의 것이 불린다 — 내가 직접 오버라이드한 자리라 포워딩이 안 생겼기 때문이다(2번).
- 상속이었다면 달랐다.

**출력** — 같은 구조를 상속으로 쓰면

```text
===== 소스: inherit21.kt =====
open class BasePrinter(private val x: Int) {
    open fun printMessage() {
        println("   BasePrinter : $x")
    }

    fun printTwice() {
        printMessage()
        printMessage()
    }
}

class Derived(x: Int) : BasePrinter(x) {
    override fun printMessage() {
        println("   Derived : 내가 가로챘다")
    }
}

fun main() {
    println("A BasePrinter.printTwice()")
    BasePrinter(10).printTwice()
    println("B Derived.printMessage()")
    Derived(10).printMessage()
    println("C Derived.printTwice()  ← 위임과 달라지는 자리")
    Derived(10).printTwice()
}
===== kotlinc inherit21.kt -d oinherit =====
(exit 0)
===== java -cp oinherit:kotlin-stdlib.jar Inherit21Kt =====
A BasePrinter.printTwice()
   BasePrinter : 10
   BasePrinter : 10
B Derived.printMessage()
   Derived : 내가 가로챘다
C Derived.printTwice()  ← 위임과 달라지는 자리
   Derived : 내가 가로챘다
   Derived : 내가 가로챘다
(exit 0)
```

- ★★ 상속에서는 **객체가 하나**다. `printTwice()` 안의 `this` 도 `Derived` 이므로 **가상 디스패치로 `Derived.printMessage()` 가 불린다.**\
  `C` 줄이 **「내가 가로챘다」 두 번**으로 바뀐다.
- 이것이 **self 문제**다. 위임은 「가진다」이고 상속은 「된다」인데, 그 차이가 **정확히 이 한 줄에서 드러난다.**

### 2. ★★ 필드 **1개** · 메서드 **2개** — 포워딩 몸통은 **두 줄**이다

**출력**

```text
===== javap -p odeleg/Derived.class =====
Compiled from "deleg.kt"
public final class Derived implements Printer {
  private final Printer $$delegate_0;
  public Derived(Printer);
  public void printMessage();
  public void printTwice();
}
(exit 0)
===== javap -c -p odeleg/Derived.class =====
Compiled from "deleg.kt"
public final class Derived implements Printer {
  private final Printer $$delegate_0;

  public Derived(Printer);
    Code:
       0: aload_1
       1: ldc           #11                 // String base
       3: invokestatic  #17                 // Method kotlin/jvm/internal/Intrinsics.checkNotNullParameter:(Ljava/lang/Object;Ljava/lang/String;)V
       6: aload_0
       7: invokespecial #20                 // Method java/lang/Object."<init>":()V
      10: aload_0
      11: aload_1
      12: putfield      #24                 // Field $$delegate_0:LPrinter;
      15: return

  public void printMessage();
    Code:
       0: ldc           #29                 // String    Derived : 내가 가로챘다
       2: getstatic     #35                 // Field java/lang/System.out:Ljava/io/PrintStream;
       5: swap
       6: invokevirtual #41                 // Method java/io/PrintStream.println:(Ljava/lang/Object;)V
       9: return

  public void printTwice();
    Code:
       0: aload_0
       1: getfield      #24                 // Field $$delegate_0:LPrinter;
       4: invokeinterface #44,  1           // InterfaceMethod Printer.printTwice:()V
       9: return
}
(exit 0)
```

**왜 그런가**

- 필드는 **`private final Printer $$delegate_0` 하나**다. 생성자가 받은 값을 `putfield` 로 한 번 넣고 끝이다.
- 메서드는 둘 — `printMessage()`(내가 쓴 것)와 `printTwice()`(**컴파일러가 만든 포워딩**).
- 포워딩 몸통은 **두 줄**이다.
  ```text
  0: aload_0
  1: getfield      $$delegate_0
  4: invokeinterface Printer.printTwice:()V
  9: return
  ```
  조건도 분기도 없다 — **그래서 오버라이드를 볼 방법이 없다**(1번).
- ★★ `javap` 의 첫 줄이 「`public final class Derived implements Printer`」다. **`extends BasePrinter` 가 없다.**\
  `Derived` 는 `BasePrinter` 를 **상속하지 않는다** — `is BasePrinter` 는 `false` 다.
- ★ 그래서 「`by` 는 상속의 간편 문법」이라는 읽기는 틀렸다. **타입 계층이 아예 다르다.**

### 3. ★★★ `[log]` 가 **한 번만** 찍힌다 — 기본 구현도 포워딩된다

**출력**

```text
===== 소스: count.kt =====
interface Repo {
    val size: Int
    var label: String
    fun add(item: String)
    fun find(key: String): String?
    fun clear()
    fun addAll(items: List<String>) {
        for (i in items) add(i)
    }
}

class MemoryRepo : Repo {
    private val items = mutableListOf<String>()
    override val size get() = items.size
    override var label = "memory"
    override fun add(item: String) { items += item }
    override fun find(key: String) = items.firstOrNull { it == key }
    override fun clear() = items.clear()
}

class LoggingRepo(private val inner: Repo) : Repo by inner {
    override fun add(item: String) {
        println("   [log] add($item)")
        inner.add(item)
    }
}

fun main() {
    val r = LoggingRepo(MemoryRepo())
    println("A 하나 넣는다")
    r.add("a")
    println("B addAll 로 둘 넣는다")
    r.addAll(listOf("b", "c"))
    println("C size=${r.size} / find(\"b\")=${r.find("b")} / label=${r.label}")
}
===== kotlinc count.kt -d ocount =====
(exit 0)
===== java -cp ocount:kotlin-stdlib.jar CountKt =====
A 하나 넣는다
   [log] add(a)
B addAll 로 둘 넣는다
C size=3 / find("b")=b / label=memory
(exit 0)
```

**왜 그런가**

- `A` — 내가 `r.add("a")` 를 직접 불렀으므로 `LoggingRepo.add` 가 돌고 `[log]` 가 찍힌다.
- `B` — `addAll` 은 **인터페이스의 기본 구현**인데 `LoggingRepo` 가 안 덮었으므로 **포워딩**된다.\
  포워딩을 타고 `MemoryRepo` 로 가면, 그 안의 `add(i)` 는 **`MemoryRepo` 자기 것**이다. `[log]` 가 **0번** 찍힌다.
- `C` — `size=3` 이다. **`a`·`b`·`c` 셋이 다 들어갔다.**
- ★★★ **일은 다 됐고 로그만 빠졌다.** 예외도 경고도 없고 결과값도 맞다 — 빠진 것은 **가로채기뿐**이다.\
  결과만 보는 테스트는 **통과한다.** 이것이 이 함정이 위험한 이유다(8번).
- ★★ 「인터페이스에 기본 구현이 있으니 그건 인터페이스 쪽에서 돌겠지」가 **거짓**이다. 위임은 **인터페이스 멤버 전부**를 포워딩한다(4번).

### 4. 멤버 **7개** · 포워딩 **6개** · 필드 이름은 `$$delegate_0` 이 **아니다**

**출력**

```text
===== javap -p ocount/Repo.class =====
Compiled from "count.kt"
public interface Repo {
  public abstract int getSize();
  public abstract java.lang.String getLabel();
  public abstract void setLabel(java.lang.String);
  public abstract void add(java.lang.String);
  public abstract java.lang.String find(java.lang.String);
  public abstract void clear();
  public default void addAll(java.util.List<java.lang.String>);
  public static void access$addAll$jd(Repo, java.util.List);
}
(exit 0)
===== javap -p ocount/LoggingRepo.class =====
Compiled from "count.kt"
public final class LoggingRepo implements Repo {
  private final Repo inner;
  public LoggingRepo(Repo);
  public void add(java.lang.String);
  public int getSize();
  public java.lang.String getLabel();
  public void setLabel(java.lang.String);
  public java.lang.String find(java.lang.String);
  public void clear();
  public void addAll(java.util.List<java.lang.String>);
}
(exit 0)
```

**왜 그런가**

| `Repo` 의 멤버(`javap` 기준) | 몇으로 세나 | `LoggingRepo` 에서 |
|---|---|---|
| `val size` | `getSize()` **1개** | 포워딩 |
| `var label` | `getLabel()`·`setLabel()` **2개** | 포워딩 둘 |
| `fun add` | 1개 | ★ **내가 오버라이드** |
| `fun find` | 1개 | 포워딩 |
| `fun clear` | 1개 | 포워딩 |
| `fun addAll`(기본 구현) | 1개 | ★ **포워딩**(3번의 함정) |
| 합계 | **7개** | 메서드 7개 = 오버라이드 1 + **포워딩 6** |

- ★ **프로퍼티는 접근자 단위로 센다.** `var` 하나가 메서드 **둘**이다.
- ★ `access$addAll$jd` 는 **인터페이스 쪽의 합성 메서드**라 구현 클래스의 멤버 수에 안 들어간다([20번 주제](../20-interfaces-default-impl-and-super/) 6번).
- ★★ 필드 이름이 **`inner`** 다 — `$$delegate_0` 이 아니다.\
  위임 대상을 `private val inner: Repo` **프로퍼티로 받았기 때문에** 컴파일러가 그 필드를 **그대로 재사용**한다(6번).\
  「`javap` 에서 `$$delegate_0` 을 찾아라」로 외우면 여기서 못 찾는다.

### 5. ★★★ **안 바뀐다** — 경고도 **0건**이다

**출력**

```text
===== 소스: fixed.kt =====
interface Printer {
    fun printMessage()
}

class Named(private val label: String) : Printer {
    override fun printMessage() {
        println("   Named($label)")
    }
}

class Swappable(var target: Printer) : Printer by target

fun main() {
    val first = Named("첫 번째")
    val second = Named("두 번째")
    val s = Swappable(first)
    println("A 처음")
    s.printMessage()
    s.target = second
    println("B target 을 바꾼 뒤")
    s.printMessage()
    println("C target 자체는 바뀌었나 : ${s.target === second}")
}
===== kotlinc fixed.kt -d ofixed =====
(exit 0)
===== java -cp ofixed:kotlin-stdlib.jar FixedKt =====
A 처음
   Named(첫 번째)
B target 을 바꾼 뒤
   Named(첫 번째)
C target 자체는 바뀌었나 : true
(exit 0)
===== javap -p ofixed/Swappable.class =====
Compiled from "fixed.kt"
public final class Swappable implements Printer {
  private final Printer $$delegate_0;
  private Printer target;
  public Swappable(Printer);
  public final Printer getTarget();
  public final void setTarget(Printer);
  public void printMessage();
}
(exit 0)
```

**왜 그런가**

```text
   class Swappable(var target: Printer) : Printer by target

   생성자 ──┬──▶ $$delegate_0 = first   (private final · 다시 못 쓴다)
            └──▶ target       = first   (private · var 라 바뀐다)

   s.target = second   ──▶ target 만 바뀐다
   s.printMessage()    ──▶ $$delegate_0 를 본다 = 여전히 first
```

- `A`·`B` 둘 다 `Named(첫 번째)` 다. `C` 는 `target === second` 가 **`true`** 라고 말한다 — **프로퍼티는 분명히 바뀌었는데 동작이 안 바뀐다.**
- `javap` 가 이유를 말한다 — **필드가 둘**이다.\
  `private final Printer $$delegate_0` 과 `private Printer target`.\
  `by target` 은 **생성자 시점의 값을 복사**해 별도의 `final` 필드에 넣는다.
- ★★ **컴파일 경고가 0건**이다(`kotlinc … (exit 0)`). 이 함정도 조용하다.
- ★ 그래서 위임 대상은 **`val` 로 받는 것이 정직하다.** `var` 로 받으면 「바꿀 수 있다」고 읽히는데 실제로는 아니다.\
  런타임에 갈아 끼워야 한다면 **포워딩을 손으로 적어야** 한다.

### 6. ★ 다섯 판 — `val` 로 받으면 `$$delegate_0` 이 **안 생긴다**

**출력**

```text
===== 소스: fields.kt =====
interface Printer {
    fun printMessage()
}

class PlainParam(base: Printer) : Printer by base
class ValParam(val base: Printer) : Printer by base
class PrivateValParam(private val base: Printer) : Printer by base
class VarParam(var base: Printer) : Printer by base
class NewEachTime : Printer by Named("현장에서 만든 것")

class Named(private val label: String) : Printer {
    override fun printMessage() = println("   Named($label)")
}
===== kotlinc fields.kt -d ofields =====
(exit 0)
===== javap -p ofields/PlainParam.class ofields/ValParam.class ofields/PrivateValParam.class ofields/VarParam.class ofields/NewEachTime.class =====
Compiled from "fields.kt"
public final class PlainParam implements Printer {
  private final Printer $$delegate_0;
  public PlainParam(Printer);
  public void printMessage();
}
Compiled from "fields.kt"
public final class ValParam implements Printer {
  private final Printer base;
  public ValParam(Printer);
  public final Printer getBase();
  public void printMessage();
}
Compiled from "fields.kt"
public final class PrivateValParam implements Printer {
  private final Printer base;
  public PrivateValParam(Printer);
  public void printMessage();
}
Compiled from "fields.kt"
public final class VarParam implements Printer {
  private final Printer $$delegate_0;
  private Printer base;
  public VarParam(Printer);
  public final Printer getBase();
  public final void setBase(Printer);
  public void printMessage();
}
Compiled from "fields.kt"
public final class NewEachTime implements Printer {
  private final Named $$delegate_0;
  public NewEachTime();
  public void printMessage();
}
(exit 0)
```

**왜 그런가**

| 선언 | 생기는 필드 | 개수 |
|---|---|---|
| `class PlainParam(base: Printer) : Printer by base` | `$$delegate_0` | 1 |
| `class ValParam(val base: Printer) : Printer by base` | **`base`**(재사용) | 1 |
| `class PrivateValParam(private val base: Printer) : Printer by base` | **`base`**(재사용) | 1 |
| `class VarParam(var base: Printer) : Printer by base` | `$$delegate_0` **+** `base` | **2** |
| `class NewEachTime : Printer by Named("…")` | `$$delegate_0`(타입이 **`Named`**) | 1 |

- ★★ **`val` 로 받으면 이미 `final` 필드가 있으므로** 컴파일러가 그것을 그대로 쓴다. 필드를 하나 더 만들 이유가 없다.
- `var` 는 **바뀌어야 하는 필드**라 위임에 쓸 수 없다 — 그래서 둘 다 생긴다(5번).
- `NewEachTime` 처럼 **식을 바로 쓸 수 있다.** 그때 필드 타입은 인터페이스가 아니라 **그 식의 정적 타입**(`Named`)이다.
- ★★★ 다섯 판 **전부 위임 필드가 `final`** 이다. 이것이 5번의 결론을 뒷받침한다 — **위임 대상은 구조적으로 고정**이다.

### 7. 된다 — `$$delegate_0` · `$$delegate_1` 로 번호가 붙는다

**출력**

```text
===== 소스: multi.kt =====
interface Reader {
    fun read(): String
}

interface Writer {
    fun write(s: String)
}

class FileReader : Reader {
    override fun read() = "파일에서 읽음"
}

class ConsoleWriter : Writer {
    override fun write(s: String) = println("   콘솔 : $s")
}

class ReadWrite(r: Reader, w: Writer) : Reader by r, Writer by w

fun main() {
    val rw = ReadWrite(FileReader(), ConsoleWriter())
    println("A ${rw.read()}")
    println("B")
    rw.write("씀")
}
===== kotlinc multi.kt -d omulti =====
(exit 0)
===== java -cp omulti:kotlin-stdlib.jar MultiKt =====
A 파일에서 읽음
B
   콘솔 : 씀
(exit 0)
===== javap -p omulti/ReadWrite.class =====
Compiled from "multi.kt"
public final class ReadWrite implements Reader,Writer {
  private final Reader $$delegate_0;
  private final Writer $$delegate_1;
  public ReadWrite(Reader, Writer);
  public java.lang.String read();
  public void write(java.lang.String);
}
(exit 0)
```

**왜 그런가**

- 위임한 인터페이스 수만큼 필드가 생기고 **`_0`·`_1` 로 번호**가 붙는다.
- ★★ **상속으로는 못 한다.** 클래스는 하나만 상속할 수 있으므로 「읽기는 A 에게, 쓰기는 B 에게」를 상속으로 표현할 방법이 없다.\
  이것이 「상속 대신 합성」이 **실질적으로 이기는** 자리다.
- 두 인터페이스에 **같은 시그니처**가 있으면 [20번 주제](../20-interfaces-default-impl-and-super/) 3번의 규칙이 그대로 걸린다 — 「`must override … because it inherits multiple interface methods`」가 나고 **`override` 를 직접 적어야** 한다.\
  ★ 그때 `super<T>` 는 못 쓴다(위임 대상은 상위 타입이 아니다) — **위임 필드를 직접 들고 있다가 골라 불러야** 한다.

### 8. **위임 대상의 메서드가 서로를 부를 때** 쓰면 안 된다

**왜 그런가**

- 함정이 나는 조건 한 문장 — 「**내가 오버라이드한 메서드를, 위임 대상의 다른 메서드가 안에서 부를 때**」.\
  ★ 그 「다른 메서드」에는 **인터페이스의 기본 구현도 포함**된다(3번의 `addAll`).
- 고를 수 있는 길 셋 —
  1. **상속으로 바꾼다** — `this` 가 하나가 되어 가상 디스패치가 산다(1번의 대비).
  2. **겹치는 메서드를 전부 직접 오버라이드한다** — 포워딩을 없애 버린다.
  3. **인터페이스를 쪼갠다** — 서로를 부르는 메서드를 인터페이스 밖(확장 함수 등)으로 뺀다(11번).
- ★★★ 조용한 이유 — **예외 0건 · 경고 0건 · 결과값 정상**이다(3번의 `size=3`).\
  드러나는 것은 **부수 효과가 안 일어난 것**뿐이다. 로그·측정·캐시 무효화·감사 기록처럼 **결과에 안 나타나는 일**을 가로채려 할 때 조용히 샌다.
- ★ 그래서 데코레이터를 위임으로 만들었다면 **「감싼 객체가 자기 메서드를 부르는가」를 먼저 읽어야** 한다.

### 9. 안 된다 — **인터페이스에만** 된다

**출력**

```text
===== 소스: forbid21.kt =====
open class Machine {
    open fun run() = "machine"
}

class Robot(m: Machine) : Machine by m

interface Engine {
    fun start(): String
}

class NotEngine

class Car(n: NotEngine) : Engine by n
===== kotlinc forbid21.kt -d oforbid =====
forbid21.kt:5:27: error: delegation is supported only for interfaces.
class Robot(m: Machine) : Machine by m
                          ^^^^^^^
forbid21.kt:5:27: error: this type has a constructor, so it must be initialized here.
class Robot(m: Machine) : Machine by m
                          ^^^^^^^
forbid21.kt:13:37: error: type mismatch: inferred type is 'NotEngine', but 'Engine' was expected.
class Car(n: NotEngine) : Engine by n
                                    ^
(exit 1)
```

**왜 그런가**

- 에러 3건 —\
  「`delegation is supported only for interfaces.`」 ·\
  「`this type has a constructor, so it must be initialized here.`」 ·\
  「`type mismatch: inferred type is 'NotEngine', but 'Engine' was expected.`」
- ★ 앞의 둘이 **같은 줄**에서 난다. 클래스를 상위 타입으로 적으면 **생성자를 불러야** 하는데 `by` 는 생성자를 안 부른다 — 그래서 두 번째 에러가 따라온다.
- 왜 클래스에는 안 되나 — **포워딩으로는 상속을 흉내 낼 수 없기 때문**이다.\
  클래스를 상위 타입으로 적으면 **그 클래스의 상태(필드)와 생성자까지 물려받아야** 하는데, 포워딩 메서드는 **메서드만** 넘긴다.\
  ★ 게다가 클래스는 `final` 멤버를 가질 수 있어([19번 주제](../19-inheritance-open-final-override/)) **포워딩으로 덮을 수 없는 자리**가 생긴다.
- 세 번째 에러가 말하듯 `by` 뒤의 식은 **그 인터페이스 타입**이어야 한다. 아무 객체나 넘길 수 없다.

### 10. **낱말만 같고 기계는 전혀 다르다**

**왜 그런가**

| | 프로퍼티 위임([17번](../17-delegated-properties/)) | 클래스 위임(이 주제) |
|---|---|---|
| 형태 | `val x: T by 위임객체` | `class A : B by 위임객체` |
| 무엇으로 푸나 | **연산자 규약**(`getValue`/`setValue`) | **포워딩 메서드 생성** |
| 위임 객체의 요건 | 인터페이스 구현 **불필요** — 이름·시그니처만 맞으면 된다 | 그 **인터페이스 타입**이어야 한다 |
| 생기는 것 | `x$delegate` 필드 + `$$delegatedProperties` 배열 | `$$delegate_0` 필드 + 포워딩 메서드들 |
| 대상 | 프로퍼티 **하나** | 인터페이스 **전체** |
| 함정 | 위임 객체가 언제 만들어지나·스레드 모드 | ★ **오버라이드를 못 본다**(1번) |

- ★ 공통점은 **뜻**뿐이다 — 「이 일을 남에게 맡긴다」. **기계는 공유하지 않는다.**
- ★★ 그래서 한쪽 지식을 다른 쪽에 옮기면 틀린다. 예를 들어 프로퍼티 위임의 「규약만 맞으면 된다」를 클래스 위임에 가져오면 9번의 세 번째 에러를 만난다.
- 프로퍼티 위임의 정본은 [17번 주제](../17-delegated-properties/)다 — **여기서 다시 쓰지 않는다.**

### 11. **「된다」인가 「가진다」인가**가 기준이다

**왜 그런가**

- 상속으로 1번을 다시 쓰면 — `C` 줄이 **「Derived : 내가 가로챘다」 두 번**으로 바뀐다(1번의 두 번째 블록).\
  객체가 하나가 되어 `printTwice()` 안의 `this` 도 `Derived` 이기 때문이다.\
  ★ 대신 **`BasePrinter` 를 `open` 으로 열어야** 하고([19번 주제](../19-inheritance-open-final-override/)), 계층이 생겨 **다른 것을 상속할 수 없게** 된다.
- 확장 함수로 `addAll` 을 빼면 — **함정이 사라지는 것이 아니라 자리를 옮긴다.**\
  확장 함수는 [13번 주제](../13-extension-functions-and-properties/)의 **정적 디스패치**라 애초에 오버라이드가 **안 된다.**\
  「가로채지 못한다」는 결과는 같은데, **컴파일 시점에 그것이 명백해진다**는 것이 다르다. ★ **조용한 함정을 드러난 제약으로 바꾸는 것**이 이 선택의 값이다.
- 한 줄 기준 — 「**이것이 저것의 한 종류인가(is-a), 저것을 가지고 있는가(has-a)**」.\
  `LoggingRepo` 는 `Repo` **이면서** `Repo` 를 **가지고 있다** — 그래서 위임이 맞고, 대신 self 문제를 안고 간다.
- ★ 실무에서 자주 쓰는 판정 — **감싼 객체의 메서드가 서로를 부르면 위임을 쓰지 마라**(8번).

## 실행 검증

```text
===== kotlinc -version =====
info: kotlinc-jvm 2.4.20 (JRE 21.0.5+11-LTS)
(exit 0)
===== java -version =====
openjdk version "21.0.5" 2024-10-15 LTS
OpenJDK Runtime Environment Temurin-21.0.5+11 (build 21.0.5+11-LTS)
OpenJDK 64-Bit Server VM Temurin-21.0.5+11 (build 21.0.5+11-LTS, mixed mode, sharing)
(exit 0)
===== javac -version =====
javac 21.0.5
(exit 0)
```

★ **흔들리는 칸과 안 흔들리는 칸**(제출 전 재대조에서 「고칠 것」과 「설계상 다른 것」을 가르는 선언이다)

| 흔들린다 | 안 흔들린다 |
|---|---|
| **없다** — 해시코드·시간·순서를 싣지 않았다 | `javap` 출력 **전체**(`$$delegate_0` 이라는 이름·필드 순서·오프셋·상수 풀 번호) |
| (5번의 `===` 는 **참조 비교의 참/거짓**만 찍었고 주소는 안 찍었다) | 모든 **종료 코드** · `println` 출력 |
| | 컴파일 에러의 **문구·`파일:줄:칸`** |

> 근거 — 캡처 스크립트를 처음부터 두 번 돌려 **블록 95개(실행 52 + 소스 43)를 바이트 단위로 대조**했고, **달라진 파일은 0개**였다.

| 프로그램 | 무엇을 확인했나 | 돌린 방법 |
|---|---|---|
| `deleg.kt` | ★★★ **위임 대상이 오버라이드를 못 보는 것**(`C` 줄) | `kotlinc` → `java` · `javap -p` · `javap -c` |
| `inherit21.kt` | 같은 구조를 **상속으로 쓰면 `C` 가 달라지는 것** | `kotlinc` → `java` |
| `count.kt` | ★★ **기본 구현도 포워딩되는 것**(`[log]` 가 한 번) · 멤버 7 대 포워딩 6 | `kotlinc` → `java` · `javap -p` 2회 |
| `fixed.kt` | ★★ 위임 대상이 **생성자에서 고정**되는 것 · 필드 2개 · **경고 0건** | `kotlinc` → `java` · `javap -p` |
| `fields.kt` | 위임 필드의 **다섯 모양** — `val` 이면 `$$delegate_0` 이 안 생긴다 | `kotlinc` → `javap -p` |
| `multi.kt` | 인터페이스 **여럿 위임** — `$$delegate_0`·`$$delegate_1` | `kotlinc` → `java` · `javap -p` |
| `form21.kt` | 위임 대상을 받는 **네 형태**가 실제로 도는 것(`Z`) | `kotlinc` → `java` |
| `forbid21.kt` | **인터페이스에만** 되는 것 · 타입 불일치 | `kotlinc` (컴파일 실패가 결과) |

**구현 의존 항목** — `$$delegate_0` 이라는 **이름**과 번호 규칙, `val` 로 받으면 필드를 **재사용**하는 것,
포워딩이 `invokeinterface` 인 것, 상수 풀 번호·오프셋 — **전부 이 컴파일러 판의 산출물**이다.\
반면 **「`by` 는 포워딩을 만들어 준다」·「인터페이스에만 된다」·「위임 대상은 생성자에서 고정된다」·
「위임 대상은 오버라이드를 못 본다」·「기본 구현이 있는 멤버도 포워딩된다」·「여럿에 위임할 수 있다」**
는 **언어의 계약**이다.

**★ 던져 봤더니 예상과 달랐던 것 — 두 건**

1. ★★★ **`javap` 에서 `$$delegate_0` 을 못 찾았다.** `count.kt` 의 `LoggingRepo` 에는 그 이름이 **없고 `inner` 가 있다**(4번).
   위임 대상을 `private val` 로 받으면 컴파일러가 **그 프로퍼티 필드를 그대로 재사용**한다.
   「위임하면 `$$delegate_0` 이 생긴다」를 검사 조건으로 쓰면 **거짓 음성**이 난다 —
   그래서 `fields.kt` 로 **다섯 판을 따로 찍어** 규칙을 확정했다(6번).
2. ★★ **`var` 로 받았을 때 경고가 한 건도 없었다.** 「바꿔도 안 먹는다」는 것은 사람이 거의 반드시 틀리는 자리인데
   `kotlinc` 가 **`exit 0` 으로 조용히 통과**시킨다(5번). 필드가 둘 생긴다는 사실은 `javap` 로만 보인다.

**안 터진 것도 출력이다** — `count.kt` 의 `C` 줄이 `size=3` 이다.
**함정에 빠진 실행이 정상적인 결과를 낸다** — 예외도 경고도 없고 데이터도 맞다.
빠진 것은 **로그 두 줄**뿐이고, 그것은 결과값을 보는 테스트로는 **절대 안 걸린다.**
이 주제에서 「통과한 실행이 가장 위험한 근거」라는 말이 성립하는 자리가 여기다.
