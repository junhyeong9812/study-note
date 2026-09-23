# kotlin/syntax/21 — 클래스 위임 (`by`): 상속 대신 합성 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Delegation](https://kotlinlang.org/docs/delegation.html) · [Interfaces](https://kotlinlang.org/docs/interfaces.html) · [Delegated properties](https://kotlinlang.org/docs/delegated-properties.html).
> **실행 검증** — 이 문서의 모든 출력·바이트코드는 **kotlinc 2.4.20 (JRE 21.0.5)** 과 Temurin **JDK 21.0.5** 에서 실제로 얻었다.\
> `kotlinc` 8회(컴파일 실패 1벌) · `java` 6회 · `javap` 7회.\
> ★★ 블록은 전부 **캡처 스크립트가 파일로 받아** 조립한 것이다 — 사람이 옮겨 적지 않았다.
> ⚠️ **`-jvm-target` 을 밝히지 않은 바이트코드 주장은 반쪽이다.** 이 문서의 역어셈블은 전부 **기본값 1.8**(`major version: 52`)이다.
> **버전** — `class A(b: B) : B by b` 는 **1.0** 이다. 그 뒤로 바뀐 적이 없다.
> ★★ **경계 — `by` 라는 같은 낱말이 두 곳에 쓰인다.**\
> **프로퍼티 위임**(`val x: String by lazy { … }`)은 [17번 주제](../17-delegated-properties/)가 **정본**이고 여기서 다시 쓰지 않는다.\
> 여기는 **클래스 위임**(`class A : B by b`)만 다룬다 — 앞엣것은 `getValue`/`setValue` **규약**으로 풀리고, 뒤엣것은 **포워딩 메서드**로 풀린다.
> 인터페이스와 그 기본 구현은 [20번 주제](../20-interfaces-default-impl-and-super/), `open`/`override` 는 [19번 주제](../19-inheritance-open-final-override/)가 정본이다.
> 이 본문은 Claude 작성이다(원고 없음).

★ **흔들리는 칸 / 안 흔들리는 칸** — 제출 전 재대조에서 「고칠 것」과 「설계상 다른 것」을 가르는 선언이다.

| 흔들린다 | 안 흔들린다 |
|---|---|
| (이 주제에는 없다 — 해시코드·시간을 싣지 않았다. `===` 비교는 찍되 **주소는 안 찍었다**) | `javap` 출력 **전체**(`$$delegate_0` 이라는 이름·필드 순서·상수 풀 번호) |
| | 모든 **종료 코드** · `println` 출력 |

> 근거 — 캡처 스크립트를 두 번 돌려 **블록 95개(실행 52 + 소스 43)를 바이트 단위로 대조**했다(전체 결과는 3-answer 의 「실행 검증」).

## 한눈에 — 쉽게 말하면

**클래스 위임은 「이 계약은 내가 서명하되, 일은 저 사람이 한다」는 선언이다.**

[20번 주제](../20-interfaces-default-impl-and-super/)에서 인터페이스를 구현하려면 **메서드를 전부 적어야** 했다.\
그 메서드들이 전부 「가진 객체에게 그대로 넘기기」뿐이라면 — 그 지루한 코드를 **컴파일러가 대신 써 준다.**

> **포워딩 메서드(forwarding method)** — 「받아서 그대로 남에게 넘기는」 메서드.\
> 예: `override fun add(item: String) { inner.add(item) }` — 컴파일러가 이런 것을 **인터페이스 멤버 수만큼** 만들어 준다.

비유는 문서 끝까지 이것 하나로 고정한다 — **하청**이다.

| 비유 | 실체 |
|---|---|
| 내가 계약서에 서명한다 | `class A : B` — 타입은 `A` 가 진다 |
| 실제 일은 하청업체가 한다 | `by b` — 호출이 `b` 로 간다 |
| 계약 항목 수만큼 전달 창구를 만든다 | 포워딩 메서드 |
| 하청업체 연락처를 계약 때 적어 고정한다 | `private final $$delegate_0` 필드 |
| 한 항목만 내가 직접 한다 | `override fun …` |
| ★★ **하청업체는 내가 직접 하는 줄 모른다** | **이 주제의 함정** |
| 하청을 여러 곳에 준다 | 인터페이스 여럿 위임 |

```text
   class Derived(base: Printer) : Printer by base
        |
        v
   +---------------------------------------------+
   | Derived                                     |
   |   $$delegate_0 ─────────────▶ BasePrinter   |
   |                                             |
   |   printMessage()  <- 내가 override 했다      |
   |   printTwice()  ──┐                         |
   +-------------------│-------------------------+
                       │ 컴파일러가 만든 포워딩
                       v
              $$delegate_0.printTwice()
                       │
                       v
              BasePrinter.printTwice() 안에서 printMessage() 를 부르면
              ★ BasePrinter 자기 것이 불린다 — Derived 의 것이 아니다
```

「**타입은 내가 지고 일은 남이 한다**」가 절반이고, 나머지 절반은 「**그 남이 나를 모른다**」이다.

## 이 주제가 답하려는 질문

1. `by` 는 **무엇으로 풀리나** — 상속인가, 필드 하나와 메서드 몇 개인가.
2. 위임 대상이 **내 오버라이드를 볼 수 있나.**
3. 위임 대상을 **나중에 바꿀 수 있나.**

## 동작 방식

### (1) ★★ `by` 는 **필드 하나 + 포워딩 메서드들**로 풀린다

**언제 쓰나** — 인터페이스를 구현해야 하는데 대부분의 구현을 이미 가진 객체가 있을 때.

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

**바이트코드로 보면**

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

```text
   Derived 가 실제로 가진 것
   +------------------------------------------------------+
   | private final Printer $$delegate_0                    |  <- 필드 1개
   | public void printMessage()   <- 내가 쓴 몸통           |
   | public void printTwice()     <- 컴파일러가 만든 포워딩  |
   +------------------------------------------------------+
        printTwice() 의 몸통은 두 줄이다
           getfield $$delegate_0
           invokeinterface Printer.printTwice
```

- ★★ **상속이 아니다.** `Derived` 는 `Printer` 를 `implements` 할 뿐 `BasePrinter` 를 **상속하지 않는다**(`javap` 의 `implements Printer` 에 `extends` 가 없다).
- 생성자가 받은 값을 `$$delegate_0` 에 **한 번 넣고 끝**이다(`putfield`).
- 포워딩 몸통은 **`getfield` → `invokeinterface`** 두 줄뿐이다. 조건도 분기도 없다.
- ★ 그래서 「위임하면 느려지나」는 **이 문서가 재지 않았다.** 메서드 하나가 더 끼는 것은 보이지만 **비용은 안 쟀으므로 말하지 않는다.**

### (2) ★★★ 함정 — **위임 대상은 내 오버라이드를 모른다**

**언제 쓰나** — 위임으로 데코레이터를 만들 때. 이 주제에서 **반드시 데어 봐야 하는 자리**다.

(1)의 출력을 다시 보라 — `C` 줄이 그것이다.

```text
   A  base.printTwice()          -> BasePrinter : 10  ×2      (당연하다)
   B  Derived.printMessage()     -> Derived : 내가 가로챘다   (당연하다)
   C  Derived.printTwice()       -> BasePrinter : 10  ×2      ★ 여기다
```

```text
   Derived.printTwice()  ──포워딩──▶  BasePrinter.printTwice()
                                          │
                                          │  안에서 printMessage() 를 부른다
                                          v
                                      this 는 BasePrinter 다
                                          │
                                          v
                                      BasePrinter.printMessage()
                                      ★ Derived 의 override 는 안 불린다
```

- ★★★ `BasePrinter.printTwice()` 안의 `this` 는 **`BasePrinter` 자신**이다. `Derived` 라는 객체가 있다는 것을 **모른다.**
- **상속이었다면 달랐다.** 상속에서는 `this` 가 하나뿐이라 상위 메서드 안의 호출도 하위 구현으로 간다(가상 디스패치).\
  위임은 **객체가 둘**이다 — `Derived` 와 `BasePrinter`. `this` 도 둘이다.
- ★★ 이것을 **self 문제** 또는 **깨진 위임(broken delegation)** 이라고 부른다.

> **self 문제(self problem)** — 위임한 객체 안에서 `this` 가 「바깥 객체」가 아니라 「자기 자신」을 가리켜 오버라이드가 안 먹는 것.\
> 예: `Derived` 가 `printMessage()` 를 덮어도 `BasePrinter.printTwice()` 는 자기 것을 부른다.

- ★ 같은 함정이 (3)의 `addAll` 에서 **한 번 더** 나온다 — 인터페이스의 **기본 구현**도 포워딩 대상이기 때문이다.
- 피하는 법은 **설계뿐**이다 — 위임 대상의 메서드가 **서로를 부르지 않게** 하거나, 겹치는 메서드를 **전부 직접 오버라이드**하거나, 위임 대신 **상속**을 쓴다.

### (3) ★★ 포워딩 메서드는 **인터페이스 멤버 수만큼** 생긴다 — 기본 구현도 포함이다

**언제 쓰나** — 위임이 무엇을 대신 써 주는지 세어 볼 때. 그리고 (2)의 함정 범위를 알 때.

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

```text
   interface Repo 의 멤버 (javap 기준 7개)
     getSize  getLabel  setLabel  add  find  clear  addAll
        |        |         |       |    |      |      |
        v        v         v       v    v      v      v
   class LoggingRepo
     포워딩    포워딩    포워딩   ★내것  포워딩  포워딩  포워딩
                                                        └─ 기본 구현인데도 포워딩된다
   메서드 7개 = 오버라이드 1 + 포워딩 6      필드 1개
```

- ★ **프로퍼티는 접근자 단위로 센다.** `val size` 는 `getSize()` 하나, `var label` 은 `getLabel()`·`setLabel()` **둘**이다.
- ★★ **`addAll` 은 인터페이스에 기본 구현이 있는데도 포워딩된다.** 그래서 `B` 줄에서 `[log]` 가 **안 찍힌다** — (2)의 함정이 여기서 재현된다.\
  `addAll` 이 부르는 `add` 는 **`MemoryRepo` 의 `add`** 다.
- `C` 줄은 `size=3` 이다 — **일은 제대로 됐고 로그만 빠졌다.** ★ 이것이 이 함정이 무서운 이유다. **예외도 경고도 없고 결과도 맞다.** 빠진 것은 **가로채기**뿐이다.
- ★ 필드 이름이 `$$delegate_0` 이 아니라 **`inner`** 다 — 위임 대상을 `private val` 프로퍼티로 받으면 **그 필드를 그대로 재사용**한다((5)).

### (4) ★★ 위임 대상은 **생성자에서 고정**된다 — 바꿀 수 없다

**언제 쓰나** — 「런타임에 하청업체를 갈아 끼우자」는 생각이 들 때.

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

```text
   class Swappable(var target: Printer) : Printer by target

   생성자 ──┬──▶ $$delegate_0 = first   (final · 다시 못 쓴다)
            └──▶ target       = first   (var · 바꿀 수 있다)

   s.target = second   ──▶  target 만 바뀐다
   s.printMessage()    ──▶  $$delegate_0 를 본다 = 여전히 first
```

- ★★★ `target` 을 바꿔도 **동작이 안 바뀐다.** `C` 줄이 `target === second` 가 `true` 라고 말하는데도 `B` 줄은 여전히 `첫 번째` 다.
- `javap` 이 이유를 말한다 — **필드가 둘**이다. `private final Printer $$delegate_0` 과 `private Printer target`.\
  `by target` 은 **생성자 시점의 값을 복사해** 별도의 `final` 필드에 넣는다.
- ★★ **경고가 한 줄도 없다.** `kotlinc` 가 `exit 0` 으로 통과시킨다 — 이 함정도 **조용하다.**
- ★ 그래서 위임 대상은 **`val` 로 받는 것이 정직하다.** `var` 로 받으면 「바꿀 수 있다」고 읽히는데 실제로는 아니다.

### (5) ★ 위임 대상을 어떻게 받느냐에 따라 **필드 모양이 다섯으로 갈린다**

**언제 쓰나** — `javap` 에서 `$$delegate_0` 이 안 보일 때 당황하지 않으려고.

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

```text
   선언                                          생긴 필드
   -------------------------------------------   ------------------------------------
   class PlainParam(base: Printer)      : … by base   $$delegate_0          (1개)
   class ValParam(val base: Printer)    : … by base   base                  (1개·재사용)
   class PrivateValParam(private val …) : … by base   base                  (1개·재사용)
   class VarParam(var base: Printer)    : … by base   $$delegate_0 + base   (2개)
   class NewEachTime                    : … by Named("…")  $$delegate_0     (1개·타입은 Named)
```

- ★★ **`val` 로 받으면 `$$delegate_0` 이 아예 안 생긴다.** 이미 `final` 필드가 있으니 컴파일러가 **그것을 그대로 쓴다.**
- `var` 로 받으면 **둘 다 생긴다** — 프로퍼티는 바뀌어야 하고 위임 대상은 고정이어야 하므로 **같은 필드를 쓸 수 없다**((4)).
- `NewEachTime` 처럼 **식을 바로 쓸 수도 있다.** 그때 필드 타입은 인터페이스가 아니라 **그 식의 타입**(`Named`)이다.
- ★ 어느 모양이든 **위임 필드는 언제나 `final`** 이다 — (4)의 결론이 다섯 판 모두에서 같다.

### (6) 인터페이스 여럿에 위임하면 필드도 여럿이다

**언제 쓰나** — 서로 다른 계약을 각각 다른 객체가 이행하게 할 때. **상속으로는 못 하는 일**이다.

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

- `$$delegate_0` · `$$delegate_1` 로 **번호가 붙는다.** 위임한 인터페이스 수만큼 필드가 생긴다.
- ★★ **클래스는 하나만 상속할 수 있지만 인터페이스는 여럿 위임할 수 있다.** 이것이 「상속 대신 합성」의 실질적인 이득이다.
- ★ [20번 주제](../20-interfaces-default-impl-and-super/)의 충돌 규칙이 여기에도 걸린다 — 두 인터페이스에 **같은 시그니처**가 있으면 위임만으로는 안 되고 `override` 가 강제된다.

## 문법 — 형태와 규칙

**형태** — 위임 대상을 받는 네 가지 방식이 전부 도는 예제다.

```text
===== 소스: form21.kt =====
interface Engine {
    fun start(): String
}

class RealEngine : Engine {
    override fun start() = "부릉"
}

class Car1(e: Engine) : Engine by e
class Car2(private val e: Engine) : Engine by e
class Car3 : Engine by RealEngine()
class Car4(e: Engine) : Engine by e {
    override fun start() = "조용히"
}

fun main() {
    val r = RealEngine()
    println("Z ${Car1(r).start()} ${Car2(r).start()} ${Car3().start()} ${Car4(r).start()}")
}
===== kotlinc form21.kt -d oform =====
(exit 0)
===== java -cp oform:kotlin-stdlib.jar Form21Kt =====
Z 부릉 부릉 부릉 조용히
(exit 0)
```

**금지 사례**

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

**규칙 불릿**

- 형태는 `class A(b: B) : B by b` — **상위 타입 뒤에 `by` 와 식**을 적는다.
- **위임은 인터페이스에만 된다.** 클래스에는 안 된다(「`delegation is supported only for interfaces.`」).
- `by` 뒤의 식은 **그 인터페이스 타입**이어야 한다.
- 위임 대상은 **생성자 시점에 고정**된다 — `var` 로 받아도 못 바꾼다((4)).
- 포워딩은 **인터페이스 멤버 전부**에 생긴다. **기본 구현이 있는 멤버도 포함**이다((3)).
- 직접 `override` 한 멤버는 **포워딩이 안 생긴다** — 대신 (2)의 함정이 따라온다.
- 여러 인터페이스에 각각 위임할 수 있다((6)).
- ★ **`by` 뒤의 식은 생성자 파라미터를 쓸 수 있다** — 이것은 클래스 위임에만 있는 특권이다. 프로퍼티 위임([17번 주제](../17-delegated-properties/))과 문법이 겹쳐 보이지만 **푸는 방식이 전혀 다르다.**

## 어디서 틀리나

1. ★★★ **위임 대상이 내 오버라이드를 본다고 믿는다**((2)). 데코레이터를 만들었는데 **로그가 반만 찍힌다.**\
   ★ 결과는 맞고 가로채기만 빠지므로 **테스트가 결과만 보면 통과한다.**
2. ★★★ **인터페이스의 기본 구현은 포워딩 안 될 것이라고 믿는다**((3)의 `addAll`). 된다 — 그래서 함정의 범위가 **생각보다 넓다.**
3. ★★ **위임 대상을 런타임에 바꾸려 한다**((4)). **경고 없이 안 바뀐다.**
4. ★★ **`by` 를 상속으로 읽는다.** `Derived` 는 `BasePrinter` 를 상속하지 않는다 — `is BasePrinter` 가 `false` 다.
5. ★ **프로퍼티 위임과 헷갈린다.** 같은 `by` 지만 [17번 주제](../17-delegated-properties/)의 것은 `getValue`/`setValue` **규약**으로 풀리고, 여기 것은 **포워딩 메서드**로 풀린다. 공통점은 **낱말뿐**이다.
6. ★ **클래스에 위임하려 한다.** 인터페이스에만 된다.
7. ★ **`javap` 에서 `$$delegate_0` 을 못 찾고 당황한다.** `val` 로 받으면 그 이름이 안 생긴다((5)).
8. ★ **「위임이 상속보다 빠르다/느리다」고 말한다.** 이 문서는 **재지 않았다** — 포워딩 한 겹이 보일 뿐이다.

## 구현 세부사항 대 언어 보장

| 항목 | 어느 쪽인가 | 근거 |
|---|---|---|
| `class A : B by b` 가 포워딩을 만들어 주는 것 | **언어 보장** | (1) |
| 위임이 **인터페이스에만** 되는 것 | **언어 보장** | 「문법」의 금지 사례 |
| 위임 대상이 **생성자에서 고정**되는 것 | **언어 보장** | (4) |
| 오버라이드한 멤버를 위임 대상이 **못 보는 것** | **언어 보장**(포워딩의 정의에서 따라 나온다) | (2) |
| 기본 구현이 있는 멤버도 포워딩되는 것 | **언어 보장** | (3) |
| 필드 이름이 `$$delegate_0` 인 것 | **JVM 백엔드의 구현** | (1)·(5) |
| `val` 로 받으면 필드를 **재사용**하는 것 | **구현 세부**(최적화) | (5) |
| 포워딩이 `invokeinterface` 인 것 | **구현 세부** | (1) |
| 포워딩 메서드의 **개수** | 인터페이스 멤버 수에서 따라 나온다 | (3) |

## 언제 쓰고 언제 안 쓰나

| 상황 | 고르는 것 | 왜 |
|---|---|---|
| 기존 구현을 감싸 한두 개만 바꾼다 | **위임** | 나머지를 안 적어도 된다 |
| 감싼 것의 메서드가 **서로를 부른다** | ★ **위임을 쓰지 마라** | (2)의 함정이 난다 — 상속이나 전면 재구현 |
| 서로 다른 계약을 다른 객체가 이행한다 | **위임 여럿** | (6) — 상속으로는 못 한다 |
| 구현을 런타임에 갈아 끼운다 | **직접 위임 코드를 쓴다** | (4) — `by` 는 고정이다 |
| 공통 상태까지 물려줘야 한다 | **추상 클래스** | [19번 주제](../19-inheritance-open-final-override/) |
| 계약만 주고 구현은 각자 | **인터페이스** | [20번 주제](../20-interfaces-default-impl-and-super/) |
| 프로퍼티 하나의 읽기·쓰기를 맡긴다 | **프로퍼티 위임** | [17번 주제](../17-delegated-properties/) — 다른 `by` 다 |

## 핵심 문장

1. `by` 는 **필드 하나와 포워딩 메서드들**로 풀린다 — 상속이 아니다.
2. ★★★ **위임 대상은 내 오버라이드를 모른다.** 그 안에서 부르는 것은 자기 구현이다.
3. 포워딩은 **인터페이스 멤버 전부**에 생긴다 — **기본 구현이 있는 것도** 포함이다.
4. 위임 대상은 **생성자에서 고정**된다. `var` 로 받아도 **경고 없이** 안 바뀐다.
5. **여럿에 위임할 수 있다** — 상속이 하나만 되는 자리에서 이것이 값을 낸다.

## 관련 자료

- [17번 주제](../17-delegated-properties/) — **프로퍼티 위임**. 같은 `by` 지만 `getValue`/`setValue` 규약으로 풀린다. **그쪽이 프로퍼티 위임의 정본**이고 여기는 클래스 위임만.
- [20번 주제](../20-interfaces-default-impl-and-super/) — 인터페이스. **기본 구현이 무엇인지**는 거기, **그것도 포워딩된다**는 사실은 여기.
- [19번 주제](../19-inheritance-open-final-override/) — 상속. **위임이 무엇을 대신하는지**를 알려면 먼저 거기를 읽는다.
- [13번 주제](../13-extension-functions-and-properties/) — 확장 함수. 「남의 타입에 기능을 더한다」의 또 다른 답이고 **정적 디스패치**라는 천장이 있다.
- [`../../../java/syntax/11-interfaces-default-methods/`](../../../java/syntax/11-interfaces-default-methods/) — Java 에는 이 문법이 **없다.** 같은 일을 하려면 포워딩 메서드를 **손으로 전부 적는다.**
- 목록의 **22번 주제** — `data class` 는 위임과 자주 함께 쓰인다(감싼 값 객체).

## 용어 풀이

> **클래스 위임(class delegation)** — 인터페이스 구현을 다른 객체에 넘기는 문법.\
> 예: `class Derived(b: Printer) : Printer by b`.

> **포워딩 메서드(forwarding method)** — 받아서 그대로 남에게 넘기는 메서드.\
> 예: `void printTwice() { $$delegate_0.printTwice(); }` — 컴파일러가 만든다.

> **합성(composition)** — 기능을 물려받는 대신 **가진 객체에게 시키는** 설계.\
> 예: `Derived` 가 `BasePrinter` 를 **가지고** 있다. 상속은 **되는** 것이다.

> **self 문제(self problem)** — 위임 대상 안에서 `this` 가 자기 자신이라 바깥의 오버라이드가 안 먹는 것.\
> 예: `BasePrinter.printTwice()` 가 `Derived.printMessage()` 를 못 부른다.

> **데코레이터(decorator)** — 원본을 감싸 앞뒤로 무언가를 덧붙이는 패턴.\
> 예: `LoggingRepo` — 단 (2)의 함정 때문에 **감싼 것의 내부 호출은 못 가로챈다.**

> **`$$delegate_0`** — 컴파일러가 만드는 위임 필드의 이름.\
> 예: 여럿 위임하면 `$$delegate_1` 로 번호가 붙는다. **이름 자체는 구현 세부**다.

> **`invokeinterface`** — 인터페이스 메서드를 부르는 JVM 명령.\
> 예: 포워딩 몸통이 `getfield` 다음에 이것을 쓴다.

## 더 들어가면

- **self 문제는 Kotlin 만의 것이 아니다.** 위임·합성을 쓰는 모든 언어에 있다.\
  이것을 언어 차원에서 푼 것이 **Self 언어의 위임**과 **Rust 의 trait 기본 구현** 같은 설계이고, 「위임 대상이 바깥 `this` 를 받는」 형태가 필요하다.\
  Kotlin 은 그 길을 안 갔다 — **포워딩 한 겹이라는 단순한 모델**을 유지했다.
- **그래서 관용구가 하나 생긴다** — 위임 대상이 자기 메서드를 서로 부르지 않게 **인터페이스를 잘게 쪼개는 것**이다.\
  (3)의 `Repo` 에서 `addAll` 을 인터페이스 기본 구현이 아니라 **확장 함수**로 뺐다면 함정이 안 났을 것이다([13번 주제](../13-extension-functions-and-properties/)).\
  ★ 대신 확장 함수는 **오버라이드가 아예 안 되므로** 문제를 없앤 것이 아니라 **다른 쪽으로 옮긴 것**이다.
- **`by` 라는 낱말을 두 문법이 공유하는 것**이 Kotlin 의 드문 선택이다. 「이 일을 남에게 맡긴다」는 **뜻**이 같을 뿐,\
  푸는 기계는 전혀 다르다 — 한쪽은 **연산자 규약**([17번 주제](../17-delegated-properties/)), 한쪽은 **포워딩 메서드 생성**이다.
