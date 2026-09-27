# csharp/syntax/17 — 인터페이스·기본 구현 멤버·명시적 구현 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·진단·IL·할당 바이트는 **.NET SDK 10.0.401** · 런타임 **10.0.12** · 타겟 **`net10.0`** ·
> **linux-x64** 에서 실제로 돌려 얻은 것이다(2026-09-26).\
> 대비는 **javac 21.0.5** 다. 진단은 **`-preferreduilang:en-US`** 로 영어로 고정했다.\
> ★ 블록은 캡처 스크립트가 파일로 받아 조립기가 끼워 넣은 것이다 — 손으로 옮긴 줄은 없다.\
> ★ 진단을 싣는 블록은 전부 **그 진단을 낸 소스를 같은 블록 안에** 다시 싣는다(`===== 소스: … =====`).
> **읽는 법** — **진단 문구·예외 메시지·IL 오프셋 폭**은 흔들리는 칸이다.\
> 근거로 쓰는 것은 **진단 코드와 `(행,열)` · 예외 타입 이름 · 옵코드와 접두 · 네 판에서 갈린 줄 수 · `cc exit`/`run exit`** 다.
> ★★★ **이 문서는 시간을 재지 않았다.** 「기본 구현이 느리다」 같은 문장이 **한 줄도 없다.**

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ 본문 없는 멤버는 **두 층이 각각 거부**하고, 기본 구현은 **두 경우 다 돈다**

**출력**

```text
===== 소스: cs17b-lib1.cs =====
public interface ILog {
    string Write(string m);
}
===== 소스: cs17b-app.cs =====
using System;
class FileLog : ILog { public string Write(string m) => "쓴다 " + m; }
class Program {
    static void Main() {
        try { Run(); }
        catch (Exception e) { Console.WriteLine($"{e.GetType().Name} : {e.Message}"); }
    }
    static void Run() {
        ILog log = new FileLog();
        Console.WriteLine(log.Write("a"));
        var flush = typeof(ILog).GetMethod("Flush");
        Console.WriteLine(flush is null ? "ILog.Flush 를 찾았나 : 아니오" : $"Flush() = {flush.Invoke(log, null)}");
    }
}
===== csc -target:library -out:lib.dll cs17b-lib1.cs && csc -r:lib.dll -out:ex.dll cs17b-app.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
쓴다 a
ILog.Flush 를 찾았나 : 아니오
===== 소스: cs17b-lib2abs.cs =====
public interface ILog {
    string Write(string m);
    string Flush();                          // 새 멤버 — 본문이 없다
}
===== csc -target:library -out:lib.dll cs17b-lib2abs.cs && dotnet ex.dll    # ex.dll 은 다시 컴파일하지 않았다 (cc exit=0 · run exit=0) =====
TypeLoadException : Method 'Flush' in type 'FileLog' from assembly 'ex, Version=0.0.0.0, Culture=neutral, PublicKeyToken=null' does not have an implementation.
===== csc -r:lib.dll -out:ex2.dll cs17b-app.cs    # 같은 앱을 새 라이브러리로 다시 컴파일 (cc exit=1) =====
cs17b-app.cs(2,17): error CS0535: 'FileLog' does not implement interface member 'ILog.Flush()'
===== 소스: cs17b-lib2dim.cs =====
public interface ILog {
    string Write(string m);
    string Flush() => "ILog 의 기본 Flush";     // 새 멤버 — 본문이 있다 (C# 8)
}
===== csc -target:library -out:lib.dll cs17b-lib2dim.cs && dotnet ex.dll    # ex.dll 은 다시 컴파일하지 않았다 (cc exit=0 · run exit=0) =====
쓴다 a
Flush() = ILog 의 기본 Flush
===== csc -r:lib.dll -out:ex2.dll cs17b-app.cs && dotnet ex2.dll (cc exit=0 · run exit=0) =====
쓴다 a
Flush() = ILog 의 기본 Flush
```

**왜 그런가**

- ★★★ **다시 컴파일 안 한 앱 + 본문 없는 `Flush`** → **`TypeLoadException`**. 「쓴다 a」도 **안 찍혔다.**\
  `Run` 을 JIT 하려고 `FileLog` 를 불러오는 순간 **런타임이 「`Flush` 구현이 없다」며 타입 로드를 거부**했다.\
  ★ **`Flush` 를 부르지도 않는데** 막힌다 — **타입이 계약을 못 채웠기** 때문이다.
- ★★★ **다시 컴파일하면** `CS0535` — **같은 사고를 컴파일러가 말한 것**이다. 층만 다르다.
- ★★★ **기본 구현이 있는 `Flush`** → 다시 컴파일하든 안 하든 **돈다.** `Flush()` 가 **「ILog 의 기본 Flush」** 다.
- ★★ **이것이 C# 8 이 기본 구현을 들인 이유다** — 이전에는 인터페이스에 멤버를 하나 더하는 것이\
  **모든 구현체를 깨는 파괴적 변경**이었다. 이 격자의 윗줄 ✕ 둘을 아랫줄 ○ 둘로 바꾼 것이다.
- ★ **창 이야기** — 윗줄 왼쪽(`CS0535`)은 **진단 창**이 보고, 오른쪽(`TypeLoadException`)은 **진단 창이 원리상 못 본다.**\
  **실행 출력의 예외 타입으로 창을 바꿔 물었다** — 제5의 상태다.

### 2. ★★ **된다** — 각 인터페이스가 **자기 슬롯에 자기 기본 구현**을 쓴다

**출력**

```text
===== 소스: cs17b-twin.cs =====
using System;
interface IA { string Hello() => "IA 의 기본 구현"; }
interface IB { string Hello() => "IB 의 기본 구현"; }
class Both : IA, IB { }                                  // 아무것도 안 적었다
class Pick : IA, IB { public string Hello() => "Pick 이 직접"; }
class Program {
    static void Main() {
        var b = new Both();
        Console.WriteLine($"((IA)b).Hello() = {((IA)b).Hello()}");
        Console.WriteLine($"((IB)b).Hello() = {((IB)b).Hello()}");
        var p = new Pick();
        Console.WriteLine($"((IA)p).Hello() = {((IA)p).Hello()}");
        Console.WriteLine($"((IB)p).Hello() = {((IB)p).Hello()}");
    }
}
===== csc -out:ex.dll cs17b-twin.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
((IA)b).Hello() = IA 의 기본 구현
((IB)b).Hello() = IB 의 기본 구현
((IA)p).Hello() = Pick 이 직접
((IB)p).Hello() = Pick 이 직접
```

**왜 그런가**

- ★★★ `cc exit=0` 이다. `((IA)b)` 는 `IA 의 기본 구현`, `((IB)b)` 는 `IB 의 기본 구현` 이다.
- ★★★ **기본 구현이 클래스로 안 내려오니 클래스 안에서 두 `Hello` 가 만날 일이 없다** —\
  [16번](../16-inheritance-virtual-override-abstract-sealed-new/) (8)의 `CS1061` 이 **불편**이라면 이것이 그 **대가로 얻은 것**이다.
- ★★ **`Pick` 이 공용 `Hello` 를 두면 두 슬롯을 한꺼번에** 채운다 — **클래스 구현이 기본 구현을 이긴다.**

### 3. ★★ **`CS8705`** — 슬롯은 하나인데 후보가 둘이다

**출력**

```text
===== 소스: cs17b-diamond.cs =====
using System;
interface IBase  { string Hello() => "IBase"; }
interface ILeft  : IBase { string IBase.Hello() => "ILeft"; }    // 기반 인터페이스의 기본 구현을 덮는다
interface IRight : IBase { string IBase.Hello() => "IRight"; }
class Both : ILeft, IRight { }
class Program { static void Main() { Console.WriteLine(((IBase)new Both()).Hello()); } }
===== csc -out:ex.dll cs17b-diamond.cs (cc exit=1) =====
cs17b-diamond.cs(5,14): error CS8705: Interface member 'IBase.Hello()' does not have a most specific implementation. Neither 'ILeft.IBase.Hello()', nor 'IRight.IBase.Hello()' are most specific.
```

**왜 그런가**

- ★★★ **`IBase.Hello` 라는 슬롯은 하나**다. `ILeft` 와 `IRight` 가 **그 한 슬롯을 각자 덮었으니** 후보가 둘이고,\
  **어느 쪽도 다른 쪽보다 구체적이지 않다** — 그래서 「가장 구체적인 구현이 없다」.
- ★★ **2번은 슬롯이 둘**(`IA.Hello`·`IB.Hello`)이라 부딪히지 않았다. **같은 조상이 있느냐**가 가르는 선이다.
- ★ 푸는 법은 `Both` 가 `IBase.Hello` 를 **직접** 구현하는 것이다.

### 4. ★★★ 클래스는 바뀌고 **구조체는 `ref` 로 넘겨도 안 바뀐다**

**출력**

```text
===== 소스: cs17b-this.cs =====
using System;
interface ICounter {
    int Count { get; set; }
    string Bump() { Count++; return $"this.GetType()={this.GetType().Name} Count={Count}"; }   // 기본 구현
}
struct SDim : ICounter { public int Count { get; set; } }                       // 기본 구현에 기댄다
struct SOwn : ICounter { public int Count { get; set; }
                         public string Bump() { Count++; return $"SOwn 자신 Count={Count}"; } }
class  CDim : ICounter { public int Count { get; set; } }
class Program {
    static string Via<T>(ref T t) where T : ICounter => t.Bump();
    static void Main() {
        var c = new CDim();
        Console.WriteLine($"[1] {((ICounter)c).Bump()}");
        Console.WriteLine($"    c.Count = {c.Count}");
        var s = new SDim();
        Console.WriteLine($"[2] {((ICounter)s).Bump()}");
        Console.WriteLine($"    s.Count = {s.Count}");
        Console.WriteLine($"[3] {Via(ref s)}");
        Console.WriteLine($"    s.Count = {s.Count}");
        var o = new SOwn();
        Console.WriteLine($"[4] {Via(ref o)}");
        Console.WriteLine($"    o.Count = {o.Count}");
    }
}
===== csc -out:ex.dll cs17b-this.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
[1] this.GetType()=CDim Count=1
    c.Count = 1
[2] this.GetType()=SDim Count=1
    s.Count = 0
[3] this.GetType()=SDim Count=1
    s.Count = 0
[4] SOwn 자신 Count=1
    o.Count = 1
```

**왜 그런가**

- ★★★ **`this.GetType()` 은 실제 객체 타입**이다(`CDim`·`SDim`) — 기본 구현 안의 `this` 는 **인터페이스 정적 타입의 참조**로 구현체를 가리킨다.
- ★★★ **클래스 `c.Count = 1`** — 참조가 원본을 가리키니 원본이 바뀐다.
- ★★★ **구조체 `s.Count = 0` 두 번** —
  - `[2]` 는 캐스트로 **박싱한 상자**를 바꿨다.
  - ★★★ `[3]` 은 **`ref` + 제네릭 제약**인데도 안 바뀌었다 — 구조체에 `Bump` 가 **없으니** 인터페이스의 본문을 불러야 하고,\
    그 본문의 `this` 는 **참조여야 하므로** 런타임이 **그 자리에서 상자를 만든다.** 바뀐 것은 그 상자다.
- ★★ **`[4]` 대조군** — `SOwn` 은 **스스로 구현**했으니 `ref` 로 받은 원본에 직접 불려 **`o.Count = 1`** 이다.
- ★ 8번이 그 상자를 **바이트로** 잡는다.

### 5. ★★★ Java 는 **내려오고, 그래서 부딪힌다** — C# 과 정반대

**출력**

```text
===== 소스: j17/Ex17.java =====
interface Greet { default String hello() { return "Greet.hello"; } }
interface Left  { default String hello() { return "Left.hello"; } }
interface Right { default String hello() { return "Right.hello"; } }
class Plain implements Greet { }                    // 아무것도 안 적었다
class Pick implements Left, Right {
    public String hello() { return "Pick : " + Left.super.hello(); }
}
public class Ex17 {
    public static void main(String[] a) throws Exception {
        Plain p = new Plain();
        System.out.println("클래스 변수로 p.hello() : " + p.hello());
        System.out.println("Plain.class.getMethod(\"hello\") 의 선언 타입 : " + Plain.class.getMethod("hello").getDeclaringClass().getName());
        System.out.println("new Pick().hello() : " + new Pick().hello());
    }
}
===== javac -Xlint:all -d j17out j17/Ex17.java && java -cp j17out Ex17 (cc exit=0 · run exit=0) =====
클래스 변수로 p.hello() : Greet.hello
Plain.class.getMethod("hello") 의 선언 타입 : Greet
new Pick().hello() : Pick : Left.hello
===== 소스: j17b/Both.java =====
interface Left  { default String hello() { return "Left.hello"; } }
interface Right { default String hello() { return "Right.hello"; } }
class Both implements Left, Right { }               // 아무것도 안 적었다
===== javac -d j17bout j17b/Both.java (cc exit=1) =====
j17b/Both.java:3: error: types Left and Right are incompatible;
class Both implements Left, Right { }               // 아무것도 안 적었다
^
  class Both inherits unrelated defaults for hello() from types Left and Right
1 error
```

**왜 그런가**

- ★★★ **`p.hello()` 가 클래스 변수로 돈다** · `getMethod("hello")` 가 **찾아진다**(선언 타입 `Greet`) —\
  Java 의 `default` 는 **클래스의 공개 멤버가 된다.** C# 은 `CS1061` 이다.
- ★★★ **`Both.java` 는 컴파일 에러** — `class Both inherits unrelated defaults for hello() from types Left and Right`.\
  **C# 2번의 `Both` 는 통과했다.** 「내려오면 부딪히고, 안 내려오면 안 부딪힌다」 — 한 결정의 두 면이다.
- ★★★ **`Left.super.hello()` 에 해당하는 C# 문법은 없다**(9번).

### 6. ★ **첫째 줄 `CS8926` · 둘째 줄 `CS8920`** — 셋째 줄만 통과

**출력**

```text
===== 소스: cs17b-saerr.cs =====
interface IZero { static abstract int Zero { get; } }
class Z : IZero { public static int Zero => 0; }
class Program {
    static int Get<T>() where T : IZero => T.Zero;
    static void Main() {
        int a = IZero.Zero;          // 인터페이스 이름으로 직접
        int b = Get<IZero>();        // 인터페이스를 타입 인자로
        int c = Get<Z>();            // 구현 타입을 타입 인자로
    }
}
===== csc -out:ex.dll cs17b-saerr.cs 2>&1 | sort (cc exit=1) =====
cs17b-saerr.cs(6,17): error CS8926: A static virtual or abstract interface member can be accessed only on a type parameter.
cs17b-saerr.cs(7,17): error CS8920: The interface 'IZero' cannot be used as type argument. Static member 'IZero.Zero' does not have a most specific implementation in the interface.
```

**왜 그런가**

- ★★★ **`CS8926`** — `static abstract` 는 **타입 매개변수로만** 접근한다. `IZero.Zero` 는 **구현이 없는 이름**이다.
- ★★★ **`CS8920`** — **인터페이스 자체를 타입 인자로** 주면 `T.Zero` 가 **구현 없는 멤버**를 가리키게 된다.
- ★ `Get<Z>()` 는 **구현 타입**을 줬으니 통과한다(8번 줄에 진단이 없다).
- ★ Learn 의 문장 — 「`static abstract` 호출은 **컴파일 시점 타입**으로 풀린다」 — 그래서 **어느 타입인지가 컴파일 때 확정돼야** 한다.

### 7. ★★★ **`CS0738`** — 명시적 구현 한 줄만이 푼다

**출력**

```text
===== 소스: cs17b-clash.cs =====
interface IText { string Read(); }
interface INum  { int    Read(); }
class Both : IText, INum {
    public string Read() => "글자";
}
class Program { static void Main() { } }
===== csc -out:ex.dll cs17b-clash.cs (cc exit=1) =====
cs17b-clash.cs(3,21): error CS0738: 'Both' does not implement interface member 'INum.Read()'. 'Both.Read()' cannot implement 'INum.Read()' because it does not have the matching return type of 'int'.
```

```text
===== 소스: cs17b-clash2.cs =====
using System;
using System.Collections;
using System.Collections.Generic;
interface IText { string Read(); }
interface INum  { int    Read(); }
class Both : IText, INum {
    public string Read() => "글자";
    int INum.Read() => 42;                         // 명시적 구현
}
class Bag : IEnumerable<int> {
    public IEnumerator<int> GetEnumerator() { yield return 1; yield return 2; }
    IEnumerator IEnumerable.GetEnumerator() => GetEnumerator();   // 명시적 구현
}
class Program {
    static void Main() {
        var b = new Both();
        Console.WriteLine($"b.Read()          = {b.Read()}");
        Console.WriteLine($"((IText)b).Read() = {((IText)b).Read()}");
        Console.WriteLine($"((INum)b).Read()  = {((INum)b).Read()}");
        foreach (var x in new Bag()) Console.Write($"{x} ");
        Console.WriteLine("← 제네릭 쪽");
        foreach (object x in (IEnumerable)new Bag()) Console.Write($"{x} ");
        Console.WriteLine("← 비제네릭 쪽");
    }
}
===== csc -out:ex.dll cs17b-clash2.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
b.Read()          = 글자
((IText)b).Read() = 글자
((INum)b).Read()  = 42
1 2 ← 제네릭 쪽
1 2 ← 비제네릭 쪽
```

**왜 그런가**

- ★★★ C# 은 **반환 타입으로 오버로드하지 못한다** — `string Read()` 와 `int Read()` 를 **공용으로 나란히** 둘 수 없다.\
  그래서 공용 `Read` 하나로는 `INum.Read()` 를 못 채운다 → `CS0738`.
- ★★★ **`int INum.Read() => 42;`** — 이름이 `INum.Read` 라 **C# 에서 선언할 수 없는 이름**이고, 그래서 공용 `Read` 와 **원리상 안 부딪힌다.**
- ★★ **`IEnumerable<T>` 와 `IEnumerable`** — 둘 다 `GetEnumerator()` 인데 반환이 `IEnumerator<T>` 대 `IEnumerator` 다.\
  **`foreach` 가능한 사용자 컬렉션마다 명시적 구현이 한 줄씩** 있다(`Bag`). 비제네릭 쪽이 **제네릭 쪽에 위임**하는 것이 관례다.
- ★ [16번](../16-inheritance-virtual-override-abstract-sealed-new/) (8)의 `IWalk`/`ISwim` 은 반환까지 같아 **공용 하나로도 됐다** — 거기서는 명시적 구현이 **선택**이었고 여기서는 **유일한 길**이다.

### 8. ★★ **`constrained.`** — 기본 구현에 기댄 구조체는 **호출당 24바이트**, 네 판 모두

**출력**

```text
===== 소스: cs17b-il.cs =====
using System;
interface IGreet { string Hello() => "기본 구현"; }
interface IZero<T> where T : IZero<T> { static abstract T Zero { get; } }
readonly struct Num : IZero<Num> { public static Num Zero => default; }
static class Probe {
    public static string A(IGreet g)          => g.Hello();       // 인터페이스 변수로
    public static string B<T>(T t) where T : IGreet => t.Hello(); // 제네릭 — 제약으로
    public static T      C<T>() where T : IZero<T>  => T.Zero;    // static abstract
}
class Program {
    static void Main() {
        Il.Dump(typeof(Probe), "A");
        Il.Dump(typeof(Probe), "B");
        Il.Dump(typeof(Probe), "C");
    }
}
===== csc -r:il.dll -out:ex.dll cs17b-il.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
--- Probe.A ---
  IL_0000: ldarg.0
  IL_0001: callvirt IGreet::Hello
  IL_0006: ret
--- Probe.B ---
  IL_0000: ldarga.s 0
  IL_0002: constrained. T
  IL_0008: callvirt IGreet::Hello
  IL_000d: ret
--- Probe.C ---
  IL_0000: constrained. T
  IL_0006: call IZero<T>::get_Zero
  IL_000b: ret
```

```text
===== 소스: cs17b-alloc.cs =====
using System;
interface IShape {
    int Side { get; }
    int Twice() => Side * 2;                                                       // 기본 구현
}
struct Own : IShape { public int Side => 3; public int Twice() => Side * 2; }     // 스스로 구현
struct Dim : IShape { public int Side => 3; }                                       // 기본 구현에 기댄다
class Program {
    static int Call<T>(T t) where T : IShape => t.Twice();
    static long M(Action a) {
        a();                                             // 한 판 데워 놓고
        var b = GC.GetAllocatedBytesForCurrentThread();
        a();
        return GC.GetAllocatedBytesForCurrentThread() - b;
    }
    static void Main() {
        int sink = 0;
        var own = new Own(); var dim = new Dim();
        Console.WriteLine($"Call(own) 1000회 : {M(() => { for (int i = 0; i < 1000; i++) sink += Call(own); })} 바이트");
        Console.WriteLine($"Call(dim) 1000회 : {M(() => { for (int i = 0; i < 1000; i++) sink += Call(dim); })} 바이트");
        Console.WriteLine($"(합 {sink})");
    }
}
===== csc -out:ex.dll cs17b-alloc.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
Call(own) 1000회 : 0 바이트
Call(dim) 1000회 : 24000 바이트
(합 24000)
===== csc -out:ex.dll cs17b-alloc.cs && DOTNET_TieredCompilation=0 dotnet ex.dll (cc exit=0 · run exit=0) =====
Call(own) 1000회 : 0 바이트
Call(dim) 1000회 : 24000 바이트
(합 24000)
===== csc -optimize -out:exo.dll cs17b-alloc.cs && dotnet exo.dll (cc exit=0 · run exit=0) =====
Call(own) 1000회 : 0 바이트
Call(dim) 1000회 : 24000 바이트
(합 24000)
===== csc -optimize -out:exo.dll cs17b-alloc.cs && DOTNET_TieredCompilation=0 dotnet exo.dll (cc exit=0 · run exit=0) =====
Call(own) 1000회 : 0 바이트
Call(dim) 1000회 : 24000 바이트
(합 24000)
===== 네 판 대조 — 「바이트」 줄마다 네 판의 값이 같은가 =====
네 판에서 갈린 줄 0 / 2
```

**왜 그런가**

- ★★★ **`B` 의 IL** — `ldarga.s 0` + **`constrained. T`** + `callvirt`.\
  `constrained.` 은 「`T` 가 값 타입이면 **주소로** 불러라 — **그게 안 되면 박싱해서** 불러라」(ECMA-335).
- ★★★ **`Call(dim)` 1000회 24000 바이트 · `Call(own)` 0.** 기본 구현은 「주소로 부를 수 없는」 쪽이다 —\
  구조체에 그 메서드가 **없고**, 인터페이스 본문의 `this` 는 **참조**여야 한다. 그래서 **호출마다 상자**가 생긴다.
- ★★★ **네 판에서 갈린 줄 0 / 2** — csc 최적화 × 티어링 **네 판이 다 같다.** 근거로 쓸 수 있다(규칙 24).
- ★★ **`C`(`static abstract`) 는 `constrained. T` + `call`** — 수신자가 **없으니** `callvirt`(널 검사·가상 디스패치)가 필요 없다.
- ★ **시간은 안 쟀다** — 잰 것은 **할당**이다.

### 9. ★★ **안 된다** — `CS0175`, preview 에서도

**출력**

```text
===== 소스: cs17b-basecall.cs =====
interface IA { string Hello() => "IA"; }
class C : IA {
    public string Hello() => "C 가 감싼다 : " + base(IA).Hello();    // 특정 인터페이스의 기본 구현을 부르려 한다
}
class Program { static void Main() { } }
===== csc -out:ex.dll cs17b-basecall.cs 2>&1 | sort (cc exit=1) =====
cs17b-basecall.cs(3,45): error CS0175: Use of keyword 'base' is not valid in this context
cs17b-basecall.cs(3,50): error CS0119: 'IA' is a type, which is not valid in the given context
===== csc -langversion:preview -out:ex.dll cs17b-basecall.cs 2>&1 | sort (cc exit=1) =====
cs17b-basecall.cs(3,45): error CS0175: Use of keyword 'base' is not valid in this context
cs17b-basecall.cs(3,50): error CS0119: 'IA' is a type, which is not valid in the given context
```

**왜 그런가**

- ★★★ `base(IA).Hello()` 는 **`CS0175`**(`base` 를 여기서 못 쓴다) · **`CS0119`**(`IA` 는 타입이라 여기 못 온다).\
  **`-langversion:preview` 에서도 같았다**(이 판).
- ★★★ **Java 는 `Left.super.hello()`** 로 된다(5번).
- ★★ 그래서 「기본 구현을 감싸서 조금 바꾸기」가 필요하면 **인터페이스 쪽에 도우미**(`protected`/`private static` 멤버)를 두고\
  클래스의 구현이 **그 도우미를 부르게** 설계한다. ★ 이 설계 자체는 **이 판에서 던지지 않았다.**

### 10. ★★ **진단은 한 줄뿐** — ①②⑥ 은 **기본 구현이 조용히 이긴다**

**출력**

```text
===== 소스: cs17b-probe.cs =====
using System;

// 탐침 1 — 기본 구현이 있는 멤버와 같은 이름의 private 메서드를 클래스가 둔다
interface I1 { string Hello() => "I1 의 기본 구현"; }
class C1 : I1 { string Hello() => "C1 의 것"; }

// 탐침 2 — 같은 이름인데 반환 타입이 다른 public 메서드를 클래스가 둔다
interface I2 { string Hello() => "I2 의 기본 구현"; }
class C2 : I2 { public int Hello() => 2; }

// 탐침 3 — 파생 인터페이스가 기반 인터페이스와 같은 시그니처를 다시 선언한다
interface I3Base { string Go(); }
interface I3 : I3Base { string Go(); }

// 탐침 4 — 구조체가 상태를 바꾸는 기본 구현에 기댄다
interface I4 { int Count { get; set; } void Bump() => Count++; }
struct S4 : I4 { public int Count { get; set; } }

// 탐침 5 — 기본 구현이 자기 자신을 부른다
interface I5 { string Loop() => Loop(); }

// 탐침 6 — 기본 구현과 같은 이름의 static 메서드를 클래스가 둔다
interface I6 { string Name() => "I6 의 기본 구현"; }
class C6 : I6 { public static string Name() => "C6 의 static"; }

// 탐침 7 — 기반 클래스의 public 메서드가 인터페이스를 대신 구현한다
interface I7 { string Tag(); }
class C7Base { public string Tag() => "C7Base 의 것"; }
class C7 : C7Base, I7 { }

class Program {
    static void Main() {
        Console.WriteLine($"탐침 1 : ((I1)new C1()).Hello() = {((I1)new C1()).Hello()}");
        Console.WriteLine($"탐침 2 : ((I2)new C2()).Hello() = {((I2)new C2()).Hello()}");
        var s = new S4(); ((I4)s).Bump();
        Console.WriteLine($"탐침 4 : ((I4)s).Bump() 뒤 s.Count = {s.Count}");
        Console.WriteLine($"탐침 6 : ((I6)new C6()).Name() = {((I6)new C6()).Name()}");
        Console.WriteLine($"탐침 7 : ((I7)new C7()).Tag() = {((I7)new C7()).Tag()}");
    }
}
===== csc -warn:9 -out:ex.dll cs17b-probe.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
cs17b-probe.cs(13,32): warning CS0108: 'I3.Go()' hides inherited member 'I3Base.Go()'. Use the new keyword if hiding was intended.
탐침 1 : ((I1)new C1()).Hello() = I1 의 기본 구현
탐침 2 : ((I2)new C2()).Hello() = I2 의 기본 구현
탐침 4 : ((I4)s).Bump() 뒤 s.Count = 0
탐침 6 : ((I6)new C6()).Name() = I6 의 기본 구현
탐침 7 : ((I7)new C7()).Tag() = C7Base 의 것
===== csc -warn:9 -out:ex.dll cs17b-probe.cs 2>&1 | grep -o "cs17b-probe.cs([0-9]*" | sort -u | wc -l    # 탐침 7개 중 진단이 붙은 줄은 몇 개인가 (exit=0) =====
1
```

**왜 그런가**

- ★★★ **진단이 붙은 줄은 하나**(`CS0108`, ③)다. 스크립트가 센 마지막 줄이 `1` 이다.
- ★★★ **①·②·⑥ 을 실행하면 전부 인터페이스의 기본 구현이 불렸다** — `private`·다른 반환·`static` 은 **구현이 아니다.**\
  ★★ **기본 구현이 없었다면** 이 셋은 **에러**로 드러났을 자리다(②의 모양은 7번 `CS0738` 로 실측).\
  ★★★ **기본 구현이 구현 실수를 삼킨다** — 인터페이스 진화의 대가다.
- ★★★ **④ 가 가장 나쁘다** — `s.Count = 0` 으로 **결과가 틀렸는데** 아무 신호가 없다(4번과 같은 사고).
- ★ ⑤ 는 **실행하지 않았다** — 스택 넘침은 `catch` 로 못 잡는다. **「안 돌려 봄」** 이다.
- ★ ⑦ 이 침묵인 것은 **정상**이다 — 기반 클래스의 공용 메서드가 인터페이스를 채우는 것은 C# 1.0 부터다.

### 11. ★ **`abstract=True virtual=True static=True`** — 클래스에서는 불가능한 조합

**출력**

```text
===== 소스: cs17b-refl.cs =====
using System;
using System.Reflection;
interface IShape {
    double Area();                                  // 본문 없음
    string Name() => "도형";                         // 기본 구현 멤버 (C# 8)
    static abstract IShape Unit();                  // static abstract (C# 11)
    static string Kind() => "모양";                  // 정적 멤버 — 본문이 있다
    private string Secret() => "비밀";               // private 멤버 (C# 8)
}
class Sq : IShape {
    public double Area() => 1;
    public static IShape Unit() => new Sq();
}
class Program {
    static void Main() {
        foreach (var m in typeof(IShape).GetMethods(BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance | BindingFlags.Static | BindingFlags.DeclaredOnly))
            Console.WriteLine($"{m.Name,-7} abstract={m.IsAbstract,-5} virtual={m.IsVirtual,-5} static={m.IsStatic,-5} private={m.IsPrivate,-5} 본문={(m.GetMethodBody() is null ? "없음" : "있음")}");
        var map = typeof(Sq).GetInterfaceMap(typeof(IShape));
        for (int k = 0; k < map.InterfaceMethods.Length; k++)
            Console.WriteLine($"맵 {map.InterfaceMethods[k].Name,-7} -> {map.TargetMethods[k].DeclaringType!.Name}.{map.TargetMethods[k].Name}");
        Console.WriteLine($"Sq 가 선언한 인스턴스 메서드 : {string.Join(", ", Array.ConvertAll(typeof(Sq).GetMethods(BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance | BindingFlags.DeclaredOnly), m => m.Name))}");
    }
}
===== csc -out:ex.dll cs17b-refl.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
Area    abstract=True  virtual=True  static=False private=False 본문=없음
Name    abstract=False virtual=True  static=False private=False 본문=있음
Unit    abstract=True  virtual=True  static=True  private=False 본문=없음
Kind    abstract=False virtual=False static=True  private=False 본문=있음
Secret  abstract=False virtual=False static=False private=True  본문=있음
맵 Area    -> Sq.Area
맵 Name    -> IShape.Name
맵 Unit    -> Sq.Unit
Sq 가 선언한 인스턴스 메서드 : Area
```

**왜 그런가**

- ★★★ **`static abstract` 멤버(`Unit`)** 는 세 플래그가 **전부 True** 다. 클래스의 `static` 메서드는 `virtual` 일 수 없으니 **인터페이스에만 있는 조합**이다.
- ★★ **기본 구현 멤버(`Name`)** 는 `abstract=False virtual=True` — 본문이 있고 **덮을 수 있는 슬롯**이다.
- ★★ **`private` 멤버(`Secret`)** 가 있다 — C# 8 부터 인터페이스가 가질 수 있다. `virtual=False` 라 **슬롯이 아니다.**
- ★★★ **인터페이스 맵이 `Name -> IShape.Name`** — `Sq` 가 안 채운 슬롯을 **인터페이스 자신의 본문**이 채운다.\
  `Sq` 가 선언한 인스턴스 메서드는 **`Area` 하나**다.

### 12. 잇기

- ★★★ **기본 구현이 클래스로 안 내려오는 것**(`CS1061` · 선언 메서드 0개 · 맵이 `IGreet.Hello`)은 [16번](../16-inheritance-virtual-override-abstract-sealed-new/) (8)이 쟀다.
- **박싱 자체**와 **IL 디스어셈블러**는 [03번](../03-boxing-and-unboxing/)이다.
- ★ Java `default` 의 **충돌 해소 세 규칙**은 Java 갈래 목록([`java/syntax/README.md`](../../../java/syntax/README.md))의 **11번**([`11-interfaces-default-methods/`](../../../java/syntax/11-interfaces-default-methods/))이다.
- ★ `constrained.`·`where T :` 의 정본은 목록의 **24번 주제**(제네릭)·**25번 주제**(제네릭 제약)가 될 자리다.

## 실행 검증

| 무엇 | 몇 번·어디서 | 결과 |
|---|---|---|
| `cs17b-lib1/lib2abs/lib2dim/app.cs` 인터페이스 진화 | csc 6회 · 실행 4회(두 어셈블리) | ★★★ **`TypeLoadException` · `CS0535` · 기본 구현은 두 경우 다 ○** |
| `cs17b-clash.cs` · `cs17b-clash2.cs` | csc 2회 | ★★★ **`CS0738`** → 명시적 구현 한 줄로 해소 |
| `cs17b-twin.cs` 관련 없는 두 기본 구현 | csc 1회 | ★★★ **`cc exit=0`** · 슬롯마다 자기 것 |
| `cs17b-diamond.cs` 같은 조상을 둘이 덮음 | csc 1회 | ★★★ **`CS8705`** |
| `cs17b-basecall.cs` `base(IA)` | csc 2회(`latest`·`preview`) | **`CS0175`·`CS0119`** 둘 다 |
| `cs17b-this.cs` `this` 와 구조체 | csc 1회 | ★★★ 구조체 원본 **`0`** — `ref`+제네릭으로도 |
| `cs17b-alloc.cs` 할당 바이트 | **2×2 판 격자** | ★★★ `Call(dim)` **24000** · `Call(own)` **0** · **갈린 줄 0 / 2** |
| `cs17b-il.cs` IL | csc 1회 | ★★ **`constrained. T` + `callvirt`** · `static abstract` 는 **`call`** |
| `cs17b-refl.cs` 리플렉션 | csc 1회 | ★★★ `static abstract` = **abstract·virtual·static 전부 True** |
| `cs17b-sa.cs` · `cs17b-saerr.cs` | csc 2회 | `Meter { V = 3.5 }`·`6`·`3.75` · **`CS8926`·`CS8920`** |
| `cs17b-probe.cs` 탐침 일곱 | csc 1회(`-warn:9`) + 실행 | ★★★ **진단이 붙은 줄 1** · ①②⑥ 기본 구현이 이긴다 |
| `Ex17.java` · `Both.java` | javac 2회 | ★★★ `default` 는 **내려온다** · 관련 없는 둘은 **에러** |
| `cs17b-form.cs` 형태 | csc 1회 | `MemStore (기본 설명)` |

**구현 의존 항목** — 다음은 **이 판(.NET SDK 10.0.401 · 런타임 10.0.12 · javac 21.0.5)에서만** 그렇다.

- ★★★ **`TypeLoadException` 이 `Run` 을 JIT 할 때 난 것** — 타입 로드 시점은 런타임이 정한다. **ReadyToRun·NativeAOT 에서는 안 쟀다.**
- ★★ **`Call(dim)` 이 호출당 24바이트** — 박싱 여부는 `constrained.` 의 CLI 규칙이지만 **크기**는 객체 배치다.
- ★★ **`base(IA)` 가 `preview` 에서도 막힌 것** · **`-warn:9` 에서 탐침 일곱 중 하나만 답한 것**.
- ★ **진단 문구 · 예외 메시지 · IL 오프셋 폭 · javac 의 진단 표기**.

**언어가 보장하는 것**(구현이 바뀌어도 같다)

- **구현 안 한 추상 인터페이스 멤버는 컴파일 에러**(`CS0535`) · **기본 구현이 있으면 안 채워도 된다**(C# 8).
- **기본 구현은 인터페이스 타입으로만 접근된다** · **가장 구체적인 구현이 하나여야 한다**(`CS8705`).
- **`static abstract` 는 타입 매개변수로만 접근된다**(C# 11).
- **계약을 못 채운 타입은 로드되지 않는다** · **`constrained.` 은 불가능하면 박싱한다** — ★ 이 둘은 **CLI(ECMA-335) 보장**이다.

**안 돌려 본 것 / 못 잰 것 / 잴 것이 없는 것**

- **안 돌려 본 것** — ★★ **탐침 ⑤(자기 자신을 부르는 기본 구현)의 실행**(스택 넘침은 `catch` 로 못 잡는다) ·\
  ★★ **`static virtual` 멤버** · ★★ **`ref struct` 가 기본 구현 멤버를 가진 인터페이스를 구현할 때**(Learn 은 명시적 선언이 필요하다고 적는다) ·\
  ★ **`CS0737`·`CS0736`**(10번에서 「기본 구현이 없었다면」의 나머지 두 모양) · ★ **`((IA)this).Hello()` 의 재귀** ·\
  ★ **Java 에서 같은 조상을 둘이 덮는 모양**(7번 그림의 마지막 줄 Java 칸) · ★ **Kotlin 의 `super<T>`**.
- **못 잰 것** — ★★★ **「기본 구현 호출이 느린가」.** 잰 것은 **할당 바이트**이고 **시간은 한 줄도 안 쟀다.**
- **잴 것이 없는 것** — ★ 없다. **④ 할당 바이트는 이 주제에서 적용**이다(16편과 다르다).

**버전이 올랐을 때 다시 돌려야 하는 것**

- ★★★ **1번의 네 칸** — 특히 **예외가 나는 시점**. ★ 런타임의 타입 로드 방식이 바뀌면 「쓴다 a」가 찍힐 수도 있다.
- ★★★ **8번의 판 격자** — JIT 이 기본 구현 호출의 상자를 없애기 시작하면 `24000` 이 움직인다. **그때도 2×2 로 재라.**
- ★★ **9번의 `preview`** · **10번의 탐침** — 새 진단이 생기면 표가 바뀐다.
- ★ **2·3·6·7번** — 명세가 정한 것이라 바뀔 일이 없다. 바뀌면 그것이 뉴스다.
