# csharp/syntax/30 — 확장 메서드와 확장 멤버(C# 14) — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·진단·IL 은 **.NET SDK 10.0.401** · 런타임 **10.0.12** · 타겟 **`net10.0`** ·
> **linux-x64** 에서 실제로 돌려 얻은 것이다(2026-09-26). 대비는 **javac 21.0.5** 다.\
> 진단은 **`-preferreduilang:en-US`** 로 영어로 고정했다.\
> ★ 블록은 캡처 스크립트가 파일로 받아 조립기가 끼워 넣은 것이다 — 손으로 옮긴 줄은 없다.\
> ★ 진단을 싣는 블록은 전부 **그 진단을 낸 소스를 같은 블록 안에** 다시 싣는다(`===== 소스: … =====`).
> **읽는 법** — 근거로 쓰는 것은 **옵코드 · `[Extension]` 이 붙은 자리 · 진단 코드 · 스크립트가 센 「된 칸 N / M」** 이다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ **두 호출의 IL 이 같다(`call Ext::Twice`)** — 블록 메서드는 `static Thrice(Int32 x)`, 확장 속성은 **`static get_Square(Int32 x)`**

**출력**

```text
===== 소스: cs30b-il.cs =====
using System;
using System.Linq;
using System.Reflection;
using System.Runtime.CompilerServices;
public static class Ext {
    public static int Twice(this int x) => x * 2;
    extension(int x) {
        public int Thrice() => x * 3;
        public int Square => x * x;
    }
}
public static class Use {
    public static int CallSugar(int n) => n.Twice();
    public static int CallPlain(int n) => Ext.Twice(n);
    public static int CallBlock(int n) => n.Thrice() + n.Square;
}
class Program {
    const BindingFlags All = BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Static | BindingFlags.Instance | BindingFlags.DeclaredOnly;
    static void Main() {
        var t = typeof(Ext);
        Console.WriteLine($"Ext : abstract={t.IsAbstract} sealed={t.IsSealed} [Extension]={t.IsDefined(typeof(ExtensionAttribute))}");
        foreach (var m in t.GetMethods(All).OrderBy(m => m.Name, StringComparer.Ordinal))
            Console.WriteLine($"  메서드 {(m.IsStatic ? "static " : "")}{m.ReturnType.Name} {m.Name}({string.Join(", ", m.GetParameters().Select(p => p.ParameterType.Name + " " + p.Name))}) [Extension]={m.IsDefined(typeof(ExtensionAttribute))} specialname={m.IsSpecialName}");
        foreach (var p in t.GetProperties(All))
            Console.WriteLine($"  속성   {p.Name}");
        foreach (var n in t.GetNestedTypes(All).OrderBy(n => n.Name, StringComparer.Ordinal)) {
            Console.WriteLine($"  중첩 타입 {n.Name}");
            foreach (var m in n.GetMembers(All).OrderBy(m => m.Name, StringComparer.Ordinal))
                Console.WriteLine($"    {m.MemberType} {m.Name}");
        }
        Il.Dump(typeof(Use), "CallSugar");
        Il.Dump(typeof(Use), "CallPlain");
        Il.Dump(typeof(Use), "CallBlock");
        Console.WriteLine($"[결과] {Use.CallSugar(5)} {Use.CallPlain(5)} {Use.CallBlock(5)}");
        var where = typeof(Enumerable).GetMethods().Where(m => m.Name == "Where").ToArray();
        Console.WriteLine($"[LINQ] Enumerable.Where 오버로드 {where.Length} 개 · static 인 것 {where.Count(m => m.IsStatic)} · [Extension] 인 것 {where.Count(m => m.IsDefined(typeof(ExtensionAttribute)))} · 첫 매개변수 타입 {where[0].GetParameters()[0].ParameterType.Name}");
    }
}
===== csc -optimize -r:il.dll -out:exo.dll cs30b-il.cs && dotnet exo.dll (cc exit=0 · run exit=0) =====
Ext : abstract=True sealed=True [Extension]=True
  메서드 static Int32 Thrice(Int32 x) [Extension]=True specialname=False
  메서드 static Int32 Twice(Int32 x) [Extension]=True specialname=False
  메서드 static Int32 get_Square(Int32 x) [Extension]=False specialname=False
  중첩 타입 <G>$BA41CFE2B5EDAEB8C1B9062F59ED4D69
    NestedType <M>$DE9F57644BDC66EDA3F1FD365749DA9F
    Property Square
    Method Thrice
    Method get_Square
--- Use.CallSugar ---
  IL_0000: ldarg.0
  IL_0001: call Ext::Twice
  IL_0006: ret
--- Use.CallPlain ---
  IL_0000: ldarg.0
  IL_0001: call Ext::Twice
  IL_0006: ret
--- Use.CallBlock ---
  IL_0000: ldarg.0
  IL_0001: call Ext::Thrice
  IL_0006: ldarg.0
  IL_0007: call Ext::get_Square
  IL_000c: add
  IL_000d: ret
[결과] 10 10 40
[LINQ] Enumerable.Where 오버로드 2 개 · static 인 것 2 · [Extension] 인 것 2 · 첫 매개변수 타입 IEnumerable`1
```

**왜 그런가**

- ★★★ **`CallSugar` = `CallPlain`** — 점 찍기는 소스에만 있다.
- ★★★ **`Thrice(Int32 x)` · `Twice(Int32 x)` 둘 다 `[Extension]=True`** — 블록 형과 `this` 형이 **같은 모양**이다(Learn 「같은 IL」). 클래스 `Ext` 에도 `[Extension]=True`.
- ★★ **확장 속성은 `Ext` 에 속성이 아니라 정적 메서드 `get_Square(Int32 x)`** 로 있다(`[Extension]=False`). 속성 `Square` 는 **표지 중첩 타입 `<G>$…`** 안에 있다 — Roslyn 구현.

### 2. ★★★ **`True` · `NullReferenceException`** — `call` 대 `callvirt`

**출력**

```text
===== 소스: cs30b-null.cs =====
using System;
public static class Ext {
    public static bool IsBlank(this string? s) => s is null || s.Trim().Length == 0;
}
public static class Probe {
    public static bool ViaExtension(string? s) => s.IsBlank();
    public static int ViaInstance(string? s) => s!.GetHashCode();
}
class Program {
    static void Main() {
        string? s = null;
        try { Console.WriteLine($"[1] s.IsBlank() : {Probe.ViaExtension(s)}"); }
        catch (Exception e) { Console.WriteLine($"[1] s.IsBlank() : {e.GetType().Name}"); }
        try { Console.WriteLine($"[2] s.GetHashCode() : {Probe.ViaInstance(s)}"); }
        catch (Exception e) { Console.WriteLine($"[2] s.GetHashCode() : {e.GetType().Name}"); }
        Il.Dump(typeof(Probe), "ViaExtension");
        Il.Dump(typeof(Probe), "ViaInstance");
    }
}
===== csc -nullable:enable -optimize -r:il.dll -out:exo.dll cs30b-null.cs && dotnet exo.dll (cc exit=0 · run exit=0) =====
[1] s.IsBlank() : True
[2] s.GetHashCode() : NullReferenceException
--- Probe.ViaExtension ---
  IL_0000: ldarg.0
  IL_0001: call Ext::IsBlank
  IL_0006: ret
--- Probe.ViaInstance ---
  IL_0000: ldarg.0
  IL_0001: callvirt System.Object::GetHashCode
  IL_0006: ret
```

**왜 그런가**

- ★★★ 확장은 `IsBlank(null)` **정적 호출**이라 호출은 성공하고 본문이 `null` 을 처리한다. 인스턴스 메서드는 **`callvirt`** 가 대상 `null` 에서 던진다([16번](../16-inheritance-virtual-override-abstract-sealed-new/)).

### 3. ★★ **인스턴스 · 확장 · `Describe(string)` · `Describe(object)`**

**출력**

```text
===== 소스: cs30b-win.cs =====
using System;
class Greeter {
    public string Hello() => "Greeter.Hello (인스턴스)";
}
static class Ext {
    public static string Hello(this Greeter g) => "Ext.Hello (확장)";
    public static string Describe(this object o) => "Describe(object)";
    public static string Describe(this string s) => "Describe(string)";
}
class Program {
    static void Main() {
        var g = new Greeter();
        Console.WriteLine($"[1] g.Hello()       : {g.Hello()}");
        Console.WriteLine($"[2] Ext.Hello(g)    : {Ext.Hello(g)}");
        string s = "x";
        object o = s;
        Console.WriteLine($"[3] s.Describe()    : {s.Describe()}");
        Console.WriteLine($"[4] o.Describe()    : {o.Describe()}  (o 의 실제 타입 = {o.GetType().Name})");
    }
}
===== csc -out:ex.dll cs30b-win.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
[1] g.Hello()       : Greeter.Hello (인스턴스)
[2] Ext.Hello(g)    : Ext.Hello (확장)
[3] s.Describe()    : Describe(string)
[4] o.Describe()    : Describe(object)  (o 의 실제 타입 = String)
```

**왜 그런가**

- ★★ 7번.

### 4. ★★★ **된 칸 13 / 21** — 14 는 인덱서만 빼고 여섯 · 13 은 블록이 전부 **파서 에러** · preview 인덱서는 **`CS0029`**

**출력**

```text
===== 소스: classic.cs =====
static class E {
    public static int Twice(this int x) => x * 2;
}
class Program { static void Main() { System.Console.WriteLine(3.Twice()); } }
===== 소스: method.cs =====
static class E {
    extension(int x) { public int Twice() => x * 2; }
}
class Program { static void Main() { System.Console.WriteLine(3.Twice()); } }
===== 소스: prop.cs =====
static class E {
    extension(int x) { public int Double => x * 2; }
}
class Program { static void Main() { System.Console.WriteLine(3.Double); } }
===== 소스: smethod.cs =====
static class E {
    extension(int) { public static int Zero() => 0; }
}
class Program { static void Main() { System.Console.WriteLine(int.Zero()); } }
===== 소스: sprop.cs =====
static class E {
    extension(int) { public static int Seven => 7; }
}
class Program { static void Main() { System.Console.WriteLine(int.Seven); } }
===== 소스: oper.cs =====
static class E {
    extension(string) { public static string operator *(string a, int n) => a + n; }
}
class Program { static void Main() { System.Console.WriteLine("a" * 3); } }
===== 소스: indexer.cs =====
static class E {
    extension(int[] a) { public int this[string k] => a[0] + k.Length; }
}
class Program { static void Main() { System.Console.WriteLine(new int[] { 5 }["ab"]); } }
===== 격자 — 파일마다 csc -langversion:{13,14,preview} -out:ex.dll k30/<종류>.cs · 되면 ok=<dotnet ex.dll 의 출력>, 안 되면 진단 코드 =====
kind      C# 13                     C# 14                     preview
classic   ok=6                      ok=6                      ok=6
method    CS1022,CS1513             ok=6                      ok=6
prop      CS1022,CS1513             ok=6                      ok=6
smethod   CS1001,CS1022,CS1513      ok=0                      ok=0
sprop     CS1001,CS1022,CS1513      ok=7                      ok=7
oper      CS1001,CS1022,CS1513      ok=a3                     ok=a3
indexer   CS1022,CS1513             CS8652                    CS0029
된 칸 13 / 21
===== csc -langversion:13 -out:ex.dll k30/prop.cs (cc exit=1) =====
k30/prop.cs(2,24): error CS1513: } expected
k30/prop.cs(3,1): error CS1022: Type or namespace definition, or end-of-file expected
===== csc -langversion:preview -out:ex.dll k30/indexer.cs (cc exit=1) =====
k30/indexer.cs(4,79): error CS0029: Cannot implicitly convert type 'string' to 'int'
===== csc -langversion:2 -out:ex.dll k30/classic.cs (cc exit=1) =====
k30/classic.cs(2,29): error CS8023: Feature 'extension method' is not available in C# 2. Please use language version 3 or greater.
```

**왜 그런가**

- ★★★ **C# 14 — 인스턴스 메서드·속성 · 정적 메서드·속성 · 연산자가 된다.** 인덱서는 `CS8652`(Preview). `this` 형은 **세 판 모두.**
- ★★★ **C# 13 — `CS1513`·`CS1022`·`CS1001`** — 판 안내(「14 이상을 쓰라」)가 **없다.** `extension` 이 13 에서는 키워드가 아니다. 대조로 `this` 형을 `-langversion:2` 에 던지면 **`CS8023 … 3 or greater`** 로 판을 말한다.
- ★★ **preview 인덱서 — 선언은 통과, 호출은 `CS0029`** — 확장 인덱서가 **후보에 안 오른다**([14번](../14-indexers/) (7)과 같다).

### 5. ★★ **`cannot find symbol` · `symbol: method shout()` · `location: class String`** — 관용은 **정적 유틸** `Strs.shout("hi")`

**출력**

```text
===== 소스: Ex30.java =====
final class Strs {
    private Strs() { }
    static String shout(String s) { return s.toUpperCase() + "!"; }
}
public class Ex30 {
    public static void main(String[] args) {
        System.out.println(Strs.shout("hi"));
    }
}
===== javac -d j30out j30/Ex30.java && java -cp j30out Ex30 (cc exit=0 · run exit=0) =====
HI!
===== 소스: G30.java =====
class G30 {
    static String shout(String s) { return s.toUpperCase() + "!"; }
    void f() {
        String r = "hi".shout();
    }
}
===== javac -d j30out j30/G30.java (cc exit=1) =====
j30/G30.java:4: error: cannot find symbol
        String r = "hi".shout();
                       ^
  symbol:   method shout()
  location: class String
1 error
```

**왜 그런가**

- ★★ Java 는 `"hi".shout()` 의 이름을 **`String` 에서만** 찾는다. 확장이라는 **두 번째 찾기 단계가 없다.** 정적 유틸 호출은 C# 확장의 **IL 모양을 소스에 그대로** 쓴 것이다.

### 6. ★★★ **`call Ext::Twice` 두 줄이 같다 · `null` 수신자가 `call` 로 인자에 실린다**

- ★★★ 1번 — `n.Twice()` 와 `Ext.Twice(n)` 가 **`ldarg.0` · `call Ext::Twice` · `ret`** 으로 **한 글자도 같다.** 2번 — `s.IsBlank()` 가 **`call Ext::IsBlank`**(인스턴스 호출이면 `callvirt`)라 `null` 이 **그냥 첫 인자**로 간다. 둘을 합치면 **「정적 메서드 + 수신자는 첫 인자」** 다.

### 7. ★★★ **인스턴스 멤버 찾기가 먼저 끝나고 · 확장은 오버로드 해석이다**

- ★★★ `[1]` — `g.Hello()` 는 **`Greeter` 에서 인스턴스 `Hello` 를 찾는 순간 끝난다.** 확장은 **인스턴스 찾기가 실패했을 때만** 본다(경고도 없다).
- ★★★ `[4]` — `o.Describe()` 는 `o` 의 **선언 타입 `object`** 로 `Describe(this object)` 를 고른다. 확장 호출은 **`call`**(1번)이라 실행 시점에 **다시 고를 기회가 없다.**

### 8. ★★ **넓힌 것 — 인스턴스 속성 · 정적 메서드·속성 · 연산자 / 안 넓힌 것 — 인덱서(이 판)** — 확장 속성은 **정적 메서드 `get_X(수신자)`**

- ★★ 4번 격자의 C# 14 열 + 1번의 `get_Square(Int32 x)`. Learn 은 인덱서를 **C# 15** 로 적었다 — 이 판(10.0.401)의 preview 는 **선언만** 받는다.

### 9. ★★ **명세 · 명세 · Roslyn · 이 판(과 C# 15 예정)**

- ★★★ **「정적 메서드 + 첫 인자」·「인스턴스 우선」 = 언어 명세.** **`<G>$…` 표지 타입 · `get_Square(Int32)` 의 모양 = Roslyn 구현.** **인덱서가 preview 인 것 = 이 판의 관찰**(Learn 이 C# 15 로 예고).

### 10. ★★ **된다(C# 9)** — [31번](../31-ienumerable-and-foreach/) (2)

- ★★ `foreach` 는 **`GetEnumerator` 라는 이름을 패턴으로 찾고, 확장 메서드까지 본다.** `foreach (var i in 3)` 이 `0 1 2` 를 찍고, `-langversion:8` 은 **`CS8400 … extension GetEnumerator`** 다.

### 11. 잇기

- ★★ **[14번](../14-indexers/) (7)** — `latest` 에서 `CS8652` · preview 에서 선언 통과 · 호출하면 `CS0029`.
- ★ **확장 메서드**(1번 `[LINQ]` — `Where` 오버로드 둘이 전부 `static` · `[Extension]`) — 게으름은 **[32번](../32-yield-return-iterators-and-deferred-execution/) (6)**.

## 실행 검증

| 무엇 | 몇 번·어디서 | 결과 |
|---|---|---|
| `cs30b-il.cs` | csc 1회(`-optimize`) · 실행 1회 | ★★★ `call Ext::Twice` ×2 · `get_Square(Int32)` · `<G>$…` · LINQ `[Extension]` |
| `cs30b-null.cs` | csc 1회 · 실행 1회 | `True` · NRE · `call` 대 `callvirt` |
| `cs30b-win.cs` | csc 1회 · 실행 1회 | 인스턴스 우선 · `Describe(object)` |
| `k30/*.cs` 일곱 | csc 21회(13·14·preview) + 대조 3회 · 실행 13회 | ★★★ **된 칸 13 / 21** · 13 파서 에러 · 14 인덱서 `CS8652` · preview `CS0029` · 2 판 `CS8023` |
| `Ex30.java` · `G30.java` | javac 2회 · java 1회 | `HI!` · `cannot find symbol` |
| `cs30b-form.cs` | csc 1회 · 실행 1회 | `HELLO! · h · ababab · 6` |

**구현 의존 항목** — 다음은 **이 판(.NET SDK 10.0.401 · 런타임 10.0.12 · javac 21.0.5)에서만** 그렇다.

- ★★★ **블록 멤버의 메타데이터 모양(`get_Square(Int32)` · `<G>$…` · `[Extension]` 이 안 붙는 것) · C# 13 의 파서 에러 모양 · 인덱서가 preview** — Roslyn.

**언어가 보장하는 것**(구현이 바뀌어도 같다)

- **정적 메서드 + 첫 인자 · 인스턴스 우선 · 선언 타입으로 고른다 · C# 14 블록의 메서드·속성·정적·연산자.**

**안 돌려 본 것 / 못 잰 것 / 잴 것이 없는 것**

- **안 돌려 본 것** — ★ `ref` 수신자 · 모호성 `CS0121` · 제네릭 블록의 추론 실패.
- **못 잰 것** — 없다.
- **잴 것이 없는 것** — ★ **④ 할당 바이트** — 확장 호출은 정적 호출 한 번이다(IL 에 `newobj`·`box` 없음).

**버전이 올랐을 때 다시 돌려야 하는 것**

- ★★★ **4번 인덱서 행** — C# 15 가 나오면 `preview` 칸이 `ok` 로 움직일 것이다(Learn). **움직였다는 사실을 남겨라.**
- ★★ **1번** — 표지 타입의 모양이 바뀌면 리플렉션 줄이 갈린다.
