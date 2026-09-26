# csharp/syntax/14 — 인덱서 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [ECMA-334 7판(2023-12)](https://ecma-international.org/publications-and-standards/standards/ecma-334/) ·
> [Learn — 인덱서](https://learn.microsoft.com/en-us/dotnet/csharp/programming-guide/indexers/) ·
> [Learn — 인덱스와 범위](https://learn.microsoft.com/en-us/dotnet/csharp/tutorials/ranges-indexes) ·
> [.NET API — `IndexerNameAttribute`](https://learn.microsoft.com/en-us/dotnet/api/system.runtime.compilerservices.indexernameattribute) ·
> [.NET API — `DefaultMemberAttribute`](https://learn.microsoft.com/en-us/dotnet/api/system.reflection.defaultmemberattribute)
> **실행 검증** — 이 문서의 모든 출력·진단·IL 은 아래 「이 판」의 도구로 **실제로 돌려 얻은 것**이다(2026-09-26).\
> ★ 블록은 캡처 스크립트가 파일로 받아 조립기가 끼워 넣은 것이다 — 사람이 옮겨 적은 줄은 하나도 없다.\
> ★ 소스 펜스의 배너도 **캡처가 찍은 것**이다. 원고에 손으로 쓴 배너는 없다.\
> ★★★ **진단 언어를 영어로 고정했다**(`DOTNET_CLI_UI_LANGUAGE=en` + `-preferreduilang:en-US`).
> **버전** — 인덱서는 **C# 1.0부터** · `Index`/`Range`(`^1`·`..`)는 **C# 8** · 확장 멤버는 **C# 14**다.\
> `-langversion:latest` 로 던졌고, 확장 인덱서만 `-langversion:preview` 로도 한 번 더 던졌다((7)).
> **경계** — **속성의 전모**는 [13번](../13-properties-init-required-field/), **배열과 `^`·`..` 연산자 자체**는 [09번](../09-arrays-index-and-range/),\
> **컬렉션 고르기**는 [10번](../10-collection-choosing-list-dictionary-hashset-queue-stack/)이 정본이다.\
> 여기서는 「**내 타입에 대괄호를 붙이면 무엇이 생기나**」만 센다.
> ★★★ **[13번](../13-properties-init-required-field/)과 한 사슬이다.** 둘 다 「**메서드로 컴파일되는 문법**」이고,\
> 인덱서는 한마디로 **인자를 받는 속성**이다. 13편의 `get_X`/`set_X` 가 여기서 `get_Item`/`set_Item` 이 된다.
> ★★ **대비** — 파이썬 갈래 목록([`python/syntax/README.md`](../../../python/syntax/README.md))의 **32번**([`32-container-protocol/`](../../../python/syntax/32-container-protocol/))이 같은 자리다 —\
> 파이썬은 `__getitem__` 이라는 **약속된 이름**을 찾고, C# 은 **`DefaultMemberAttribute` 라는 메타데이터**를 남긴다((1)).\
> ★ C++ 갈래 목록([`cpp/syntax/README.md`](../../../cpp/syntax/README.md))의 **22번**(연산자 오버로딩)이 `operator[]` 쪽인데 **이 판에서 C++ 은 안 던졌다.**
>
> ★★ **흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | 진단 **문구** — 판마다 다듬인다 | ★★★ **진단 코드**(`CS0111`·`CS0106`·`CS8652`·`CS9303`…)와 **`(행,열)`** |
> | **IL 오프셋 폭**(`IL_000d`)이 판마다 달라질 수 있다는 것 | ★★★ **옵코드 이름과 순서**(`callvirt`·`newobj`·`dup`·`sub`) |
> | ★ **증분의 절댓값 일부** — 아래 (9)에서 **2×2 판 격자**로 갈랐다 | ★★★ **할당이 0 인 칸과 0 이 아닌 칸**(네 판에서 한 글자도 안 움직였다) |
> | 여러 진단이 나올 때 Roslyn 이 내는 **순서** — 배너에 `\| sort` 를 적었다 | ★★ **`cc exit` 와 `run exit`**(갈라 적었다) · **`DefaultMember` 이름** |

## 이 판

```text
===== dotnet --version && dotnet --list-runtimes | grep NETCore (exit=0) =====
10.0.401
Microsoft.NETCore.App 10.0.12 [/home/jun/.local/opt/dotnet/shared/Microsoft.NETCore.App]
===== javac -version && g++ --version | head -1 (exit=0) =====
javac 21.0.5
g++ (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0
```

## 이 갈래가 쓰는 세 층

| 층 | 뜻 | 이 주제에서 근거로 쓰는 것 |
|---|---|---|
| **언어 명세(ECMA-334)** | C# 언어가 약속한 것 | ★★★ **인덱서가 접근자 메서드로 컴파일된다는 것** · **`static` 인덱서가 없다는 것** · 오버로드 규칙 |
| **런타임·BCL 구현** | CoreCLR·Roslyn 이 그렇게 하는 것 | ★★ **기본 이름이 `Item` 이라는 것** · `DefaultMemberAttribute` 를 쓰는 것 · `^1` 이 풀리는 모양 |
| **이 판의 관찰** | .NET 10.0.12 · linux-x64 에서 이번에 본 것 | 진단 문구 · 확장 인덱서가 **preview 에서도 막힌** 것 · 할당 바이트 |

## 한눈에 — 쉽게 말하면

**인덱서는 「인자를 받는 속성」이다.**

[13번](../13-properties-init-required-field/)의 은행 창구를 그대로 쓴다.\
속성은 창구 직원 둘을 세우는 것이었다 — **내주는 직원**(`get_X`)과 **받는 직원**(`set_X`).\
인덱서는 **그 창구에 번호표를 받는 칸이 붙은 것**이다 — 직원 이름이 `get_Item`/`set_Item` 으로 바뀌고,\
**번호표가 메서드의 매개변수**가 된다.

| 비유 | 실체 | 어디서 보나 |
|---|---|---|
| 번호표를 받는 창구 직원 | ★★★ **`get_Item(int i)`·`set_Item(int i, T v)`** | (1) |
| 「우리 창구의 기본 이름은 `Item` 입니다」라는 안내판 | ★★★ **`[DefaultMember("Item")]`** — 타입에 붙는다 | (1) |
| 안내판의 이름을 바꿔 다는 것 | **`[IndexerName("Cell")]`** | (2) |
| 번호표 대신 **이름표**·**좌표**·**끝기준**을 받는 창구 | **인덱서 오버로드**(`string`·`int,int`·`Index`·`Range`) | (3) |
| ★ 창구는 **사람이 앉아야** 한다 | ★★★ **`static` 인덱서가 없다**((6)) | (6) |
| 번호표를 **상자에 담아** 건네면 | ★★ **`object` 인덱서는 박싱한다**((9)) | (9) |

> **인덱서(indexer)** — `obj[...]` 문법을 받는 멤버. `public T this[int i] { get; set; }` 꼴로 선언한다.

> **`DefaultMemberAttribute`** — 「이 타입의 기본 멤버 이름은 이것이다」를 적는 **타입 수준 어트리뷰트**.\
> ★ 리플렉션이 `obj[...]` 를 찾을 때 읽는 자리이고, **컴파일러가 자동으로 붙인다**((1)).

```text
   소스에 쓴 것                              컴파일러가 만든 것

   public string this[int i]                 ┌─ [DefaultMember("Item")]  ← 타입에 붙는다
   { get => …; set => …; }                   │
                                             ├─ string get_Item(int i)
                                             └─ void   set_Item(int i, string value)

   [IndexerName("Cell")]                     ┌─ [DefaultMember("Cell")]
   public int this[int r, int c]             ├─ int  get_Cell(int r, int c)
   { get => …; set => …; }                   └─ void set_Cell(int r, int c, int value)
```

- ★★★ **속성과 다른 점은 딱 둘이다** — **이름이 `Item` 으로 고정**되고(바꾸려면 어트리뷰트),\
  **타입에 `DefaultMember` 라는 안내판이 붙는다.** 나머지는 [13번](../13-properties-init-required-field/)과 같다.

## 이 주제가 답하려는 질문

1. **인덱서는 무엇으로 컴파일되나** — 속성과 무엇이 같고 무엇이 다른가((1)(2)).
2. **`^1` 과 `..` 은 IL 로 무엇이 되나** — 내가 인덱서를 선언했을 때와 안 했을 때가 다른가((5)).
3. **인덱서로 할 수 없는 것은 무엇인가** — `static`·확장·같은 인자 타입 둘((4)(6)(7)).
4. **언제 인덱서 대신 메서드를 쓰나** — **실패 사례**로((9)(10)).

## 동작 방식

### (0) 이 주제가 쓰는 창

| 창 | 무엇을 보여 주나 | 이 주제에서 |
|---|---|---|
| ★★★ **③ 리플렉션** | ★★★ **`get_Item`·`DefaultMemberAttribute`** — 이 주제의 본체 | (1)(2)(8) |
| ★★ **② 진단 격자** | 못 하는 것 셋(`static`·중복·확장) | (4)(6)(7) |
| ★★ **① IL 덤프** | ★★★ **`^1` 이 풀리는 두 가지 모양** | (5) |
| ★★ **④ 할당 바이트** | ★★ **쓴다** — `object` 인덱서의 박싱. **2×2 판 격자로 갈랐다** | (9) |

- ★★★ **본체는 ③ 리플렉션이다.** [13번](../13-properties-init-required-field/)은 IL 이 본체였는데 여기는 다르다 —\
  인덱서의 **IL 본문은 평범한 배열 접근**이라 볼 것이 없고, **갈리는 것은 이름과 타입 어트리뷰트**다.
- ★★ **① IL 덤프는 (5)에서만 본체가 된다.** `^1` 이 **내가 `this[Index]` 를 선언했을 때와 안 했을 때**\
  **다른 코드로 풀리는 것**은 덤프로만 보인다.
- ★★ **④ 할당 바이트를 이 주제는 쓴다.** [13번](../13-properties-init-required-field/)에서는 「잴 것이 없다」였는데 여기는 잴 것이 있다 —\
  **`this[object]` 오버로드가 박싱을 만든다**((9)). ★★★ **다만 한 판의 절댓값은 근거가 아니므로**(규칙 24)\
  **`csc -optimize` × `DOTNET_TieredCompilation` 2×2** 를 돌려 **움직인 칸이 없음**을 확인했다.

### (1) ★★★ 인덱서는 `get_Item`/`set_Item` 이다

**언제 쓰나** — 내 타입에 대괄호를 붙일 때마다. **이 절이 이 주제의 중심이다.**

```text
===== 소스: cs14b-basic.cs =====
using System;
using System.Reflection;

public class Row {
    readonly string[] cells = { "가", "나", "다" };
    public string this[int i] { get => cells[i]; set => cells[i] = value; }
}

class Program {
    static void Main() {
        var r = new Row();
        r[1] = "바뀜";
        Console.WriteLine(r[1]);
        foreach (var a in typeof(Row).GetCustomAttributes(false))
            Console.WriteLine($"타입 어트리뷰트 {a}");
        foreach (var p in typeof(Row).GetProperties())
            Console.WriteLine($"속성   이름={p.Name} 인자={p.GetIndexParameters().Length}");
        foreach (var m in typeof(Row).GetMethods(BindingFlags.Public|BindingFlags.Instance|BindingFlags.DeclaredOnly))
            Console.WriteLine($"메서드 {m.Name}");
        var da = (DefaultMemberAttribute)typeof(Row).GetCustomAttributes(typeof(DefaultMemberAttribute), false)[0];
        Console.WriteLine($"DefaultMember = {da.MemberName}");
    }
}
===== csc -out:ex.dll cs14b-basic.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
바뀜
타입 어트리뷰트 System.Reflection.DefaultMemberAttribute
속성   이름=Item 인자=1
메서드 get_Item
메서드 set_Item
DefaultMember = Item
```

- ★★★ **타입에 `DefaultMemberAttribute` 가 붙었다.** 내가 안 적었는데 **컴파일러가 붙였다.**\
  값은 **`Item`** 이다 — 「이 타입의 기본 멤버 이름은 `Item` 이다」라는 안내판이다.
- ★★★ **속성 목록에 `Item` 이 있고 인자가 1개다.** 인덱서는 **리플렉션에서 속성으로 보인다** —\
  다만 `GetIndexParameters().Length` 가 0 이 아니다. **그것이 속성과 인덱서를 가르는 유일한 칸**이다.
- ★★★ **메서드는 `get_Item`·`set_Item` 둘뿐이다.** [13번](../13-properties-init-required-field/)의 `get_X`/`set_X` 와 **똑같은 규칙**이고\
  이름만 `Item` 으로 고정됐다.
- ★ `r[1] = "바뀜"` 이 그대로 돌았다 — 배열 원소처럼 읽고 쓴다.

> **어느 층인가** — ★★★ **「인덱서가 접근자 메서드로 컴파일된다」는 명세**다.\
> ★★ **「기본 이름이 `Item` 이고 `DefaultMemberAttribute` 로 적는다」는 구현 규약**이다 —\
> 그래서 (2)에서 **이름을 바꿀 수 있다.**

### (2) ★★ `[IndexerName]` 으로 이름을 바꾸면 무엇이 달라지나

```text
===== 소스: cs14b-name.cs =====
using System;
using System.Reflection;
using System.Runtime.CompilerServices;

public class Grid2 {
    readonly int[,] m = new int[2, 2];
    [IndexerName("Cell")]
    public int this[int r, int c] { get => m[r, c]; set => m[r, c] = value; }
}
class Program {
    static void Main() {
        var g = new Grid2();
        g[1, 1] = 5;
        Console.WriteLine($"g[1,1]={g[1,1]}");
        var da = (DefaultMemberAttribute)typeof(Grid2).GetCustomAttributes(typeof(DefaultMemberAttribute), false)[0];
        Console.WriteLine($"DefaultMember = {da.MemberName}");
        foreach (var p in typeof(Grid2).GetProperties())
            Console.WriteLine($"속성   이름={p.Name} 인자={p.GetIndexParameters().Length}");
        foreach (var mm in typeof(Grid2).GetMethods(BindingFlags.Public|BindingFlags.Instance|BindingFlags.DeclaredOnly))
            Console.WriteLine($"메서드 {mm.Name}");
        Console.WriteLine($"GetProperty(\"Item\") -> {(typeof(Grid2).GetProperty("Item") is null ? "없음" : "있음")}");
        Console.WriteLine($"GetProperty(\"Cell\") -> {(typeof(Grid2).GetProperty("Cell") is null ? "없음" : "있음")}");
    }
}
===== csc -out:ex.dll cs14b-name.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
g[1,1]=5
DefaultMember = Cell
속성   이름=Cell 인자=2
메서드 get_Cell
메서드 set_Cell
GetProperty("Item") -> 없음
GetProperty("Cell") -> 있음
```

- ★★★ **메서드 이름이 `get_Cell`/`set_Cell` 로 바뀌고 `DefaultMember` 도 `Cell` 이 된다.**
- ★★★ **`GetProperty("Item")` 이 「없음」이다.** 리플렉션으로 `Item` 을 찾던 코드는 **이 타입에서 못 찾는다.**\
  ★ 이것이 `[IndexerName]` 의 유일한 실효다 — **소스에서 `g[1,1]` 로 쓰는 것은 한 글자도 안 바뀐다.**
- ★★ **그래서 `[IndexerName]` 은 C# 을 위한 것이 아니다.** 인덱서 개념이 없는 언어에서 이 타입을 쓸 때\
  `get_Item` 이라는 이름이 어색하거나 충돌할 때 쓴다.
- ★ **다차원 인덱서**(`this[int r, int c]`)가 그대로 돌았다 — `GetIndexParameters().Length` 가 **2** 다.

### (3) ★ 인덱서 오버로드 — 무엇으로든 받을 수 있다

```text
===== 소스: cs14b-overload.cs =====
using System;
class Roster {
    readonly string[] names = { "가", "나", "다" };
    public string this[int position] => $"int 으로 왔다 — {names[position]}";
    public string this[string key]   => $"string 으로 왔다 — {key}";
    public string this[int a, int b] => $"둘로 왔다 — {a},{b}";
    public string this[Index i]      => $"Index 로 왔다 — {names[i]}";
    public string this[Range r]      => $"Range 로 왔다 — {r}";
}
class Program {
    static void Main() {
        var r = new Roster();
        Console.WriteLine(r[0]);
        Console.WriteLine(r["문자"]);
        Console.WriteLine(r[1, 2]);
        Console.WriteLine(r[^1]);
        Console.WriteLine(r[0..2]);
    }
}
===== csc -out:ex.dll cs14b-overload.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
int 으로 왔다 — 가
string 으로 왔다 — 문자
둘로 왔다 — 1,2
Index 로 왔다 — 다
Range 로 왔다 — 0..2
```

- ★★ **다섯 개가 전부 다른 인덱서다.** 인자 타입이 다르면 **평범한 메서드 오버로드와 같은 규칙**으로 갈린다.
- ★★★ **`r[^1]` 이 `this[Index]` 로 갔고 `r[0..2]` 가 `this[Range]` 로 갔다.**\
  `^1` 과 `0..2` 는 **`System.Index`·`System.Range` 라는 진짜 타입의 값**이다 — 문법 설탕이 아니라 **타입**이다.
- ★ `r[1, 2]` 가 `this[int, int]` 로 간다. **다차원 인덱서는 인자가 여럿인 인덱서**일 뿐이고, 배열의 `[,]` 와는 다른 이야기다.

무엇이 안 되나.

```text
===== 소스: cs14b-dup.cs =====
class Roster {
    readonly string[] names = { "가", "나", "다" };
    public string this[int position] => names[position];      // 자리로 찾기
    public string this[int id]       => names[id - 100];      // 사번으로 찾기
}
class Program { static void Main() { } }
===== csc -out:ex.dll cs14b-dup.cs (cc exit=1) =====
cs14b-dup.cs(4,19): error CS0111: Type 'Roster' already defines a member called 'this' with the same parameter types
```

- ★★ **`CS0111` — 인자 타입이 같으면 이름을 달리 지어도 소용없다.**\
  `this[int position]` 과 `this[int id]` 는 **매개변수 이름만 다를 뿐 같은 시그니처**다.
- ★★★ **이것이 (10)의 「언제 메서드가 나은가」로 직결된다** — 같은 타입으로 **뜻이 다른 두 조회**를 하고 싶으면\
  **인덱서로는 원리상 못 한다.** `ByPosition(int)`·`ById(int)` 처럼 **이름을 주어야** 한다.

### (4) 명시적 인터페이스 구현으로서의 인덱서

```text
===== 소스: cs14b-iface.cs =====
using System;
using System.Reflection;
public interface ILookup { string this[int i] { get; } }
public class Impl : ILookup {
    string ILookup.this[int i] => $"명시적 인덱서 — {i}";
}
class Program {
    static void Main() {
        ILookup l = new Impl();
        Console.WriteLine(l[3]);
        foreach (var m in typeof(Impl).GetMethods(BindingFlags.Public|BindingFlags.NonPublic|BindingFlags.Instance|BindingFlags.DeclaredOnly))
            Console.WriteLine($"메서드 {m.Name}  private={m.IsPrivate}");
        foreach (var a in typeof(Impl).GetCustomAttributes(false))    Console.WriteLine($"Impl 의 어트리뷰트    {a}");
        foreach (var a in typeof(ILookup).GetCustomAttributes(false)) Console.WriteLine($"ILookup 의 어트리뷰트 {a}");
    }
}
===== csc -out:ex.dll cs14b-iface.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
명시적 인덱서 — 3
메서드 ILookup.get_Item  private=True
ILookup 의 어트리뷰트 System.Reflection.DefaultMemberAttribute
```

- ★★ **명시적 구현 인덱서는 `private=True` 다.** 이름이 `ILookup.get_Item` 이고 **클래스 밖에서 직접 못 부른다.**\
  ★ `l[3]` 로 부를 수 있는 것은 **`ILookup` 타입의 변수**이기 때문이다.
- ★★★ **`DefaultMemberAttribute` 가 `ILookup` 에는 있고 `Impl` 에는 없다.**\
  `Impl` 은 **자기 인덱서를 선언한 적이 없으므로**(인터페이스 것을 구현했을 뿐) 안내판을 안 단다.
- ★ 이 성질은 [16번](../16-inheritance-virtual-override-abstract-sealed-new/) (8)의 **명시적 인터페이스 구현이 `private` 인 것**과 같은 규칙이다 —\
  거기서 `IsFinal`·`IsVirtual` 까지 함께 찍었다.

### (5) ★★★ `^1` 과 `..` 은 IL 로 무엇이 되나 — 두 갈래다

```text
===== 소스: cs14b-il.cs =====
using System;

public class Explicit {                                  // this[Index] 를 직접 선언
    readonly int[] items = { 1, 2, 3, 4, 5 };
    public int this[Index i] => items[i];
}
public class Pattern {                                   // Length + this[int] 만 있다
    readonly int[] items = { 1, 2, 3, 4, 5 };
    public int Length => items.Length;
    public int this[int i] => items[i];
}
public static class Probe {
    public static int FromExplicit(Explicit e) => e[^1];
    public static int FromPattern(Pattern p)   => p[^1];
}
class Program {
    static void Main() {
        Il.Dump(typeof(Probe), "FromExplicit");
        Il.Dump(typeof(Probe), "FromPattern");
    }
}
===== csc -r:il.dll -out:ex.dll cs14b-il.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
--- Probe.FromExplicit ---
  IL_0000: ldarg.0
  IL_0001: ldc.i4.1
  IL_0002: ldc.i4.1
  IL_0003: newobj System.Index::.ctor
  IL_0008: callvirt Explicit::get_Item
  IL_000d: ret
--- Probe.FromPattern ---
  IL_0000: ldarg.0
  IL_0001: dup
  IL_0002: callvirt Pattern::get_Length
  IL_0007: ldc.i4.1
  IL_0008: sub
  IL_0009: callvirt Pattern::get_Item
  IL_000e: ret
```

- ★★★ **내가 `this[Index]` 를 선언했으면**(`Explicit`) — `ldc.i4.1 / ldc.i4.1 / newobj System.Index::.ctor` 로\
  **`Index` 값을 만들어 그대로 넘긴다.** 「끝에서 1」이라는 뜻이 **런타임까지 살아 있다.**
- ★★★ **선언 안 했으면**(`Pattern`) — `dup / callvirt get_Length / ldc.i4.1 / sub / callvirt get_Item` 이다.\
  **컴파일러가 `Length - 1` 을 직접 계산해 `int` 인덱서로 보낸다.** `Index` 타입이 **아예 안 나타난다.**
- ★★★ **같은 소스 `e[^1]`·`p[^1]` 이 완전히 다른 코드가 된다.** 이것이 이 절의 결론이다.\
  ★ 뒤쪽을 **패턴 기반 인덱싱**이라 부른다 — 타입이 `Length`(또는 `Count`)와 `this[int]` 만 갖고 있으면\
  **인터페이스를 구현하지 않아도** `^`·`..` 이 붙는다.
- ★★ **`dup` 이 보이는 것**이 패턴 쪽의 증거다 — 수신자를 두 번 써야 하므로(`Length` 읽기 + `Item` 읽기) 스택에서 복제한다.
- ★ **`callvirt` 가 나온 것은 가상 호출이라는 뜻이 아니다** — 자세한 것은 [16번](../16-inheritance-virtual-override-abstract-sealed-new/) (4)가 정본이다.

```text
   소스는 한 글자도 같다 ──  x[^1]

   ┌─ this[Index] 를 선언했나? ─┐
   │                            │
  예                           아니오 (Length 와 this[int] 만 있다)
   │                            │
   ▼                            ▼
  newobj System.Index          dup
  callvirt get_Item            callvirt get_Length
                               ldc.i4.1
   「끝에서 1」이 런타임까지       sub
    살아 있다                    callvirt get_Item

                               ★ Index 타입이 아예 안 나타난다
```

> **어느 층인가** — ★★★ **「패턴 기반 인덱싱이 있다」는 C# 8 명세**다.\
> ★★ **「`dup`/`sub` 라는 구체적 코드 모양」은 Roslyn 의 것**이다.

### (6) ★ 인덱서는 `static` 이 안 된다

```text
===== 소스: cs14b-static.cs =====
class Table {
    static readonly int[] data = { 1, 2, 3 };
    public static int this[int i] => data[i];
}
class Program { static void Main() { } }
===== csc -out:ex.dll cs14b-static.cs (cc exit=1) =====
cs14b-static.cs(3,23): error CS0106: The modifier 'static' is not valid for this item
```

- ★★★ **`CS0106: The modifier 'static' is not valid for this item`.**
- ★★ **왜인가** — 인덱서는 `obj[i]` 문법을 받는 멤버인데, `static` 이면 **수신자가 없다.**\
  `Table[0]` 이라고 쓰면 **타입 이름 뒤의 대괄호가 배열 타입 표기(`Table[]`)와 충돌**한다.\
  ★ 즉 **문법 수준의 제약**이지 구현의 한계가 아니다.
- ★ C# 11 의 `static abstract` 인터페이스 멤버에도 인덱서는 없다 — **이 판에서 따로 안 던졌다.**

### (7) ★★ C# 14 확장 멤버로 인덱서를 열 수 있나 — 던져서 확인

★★★ **없다고 적기 전에 던진다**(규칙 26). C# 14 는 `extension` 블록을 열었다.

```text
===== 소스: cs14b-ext.cs =====
using System;
public static class Ext {
    extension(int[] a) {                                   // C# 14 확장 멤버
        public int Second => a[1];
        public int this[string name] => name == "first" ? a[0] : a[^1];
    }
    extension(int[]) {
        public static int[] Empty => Array.Empty<int>();
        public static int this[char c] => (int)c;
    }
}
class Program { static void Main() { } }
===== csc -out:ex.dll cs14b-ext.cs 2>&1 | sort (cc exit=1) =====
cs14b-ext.cs(5,20): error CS8652: The feature 'extension indexers' is currently in Preview and *unsupported*. To use Preview features, use the 'preview' language version.
cs14b-ext.cs(9,27): error CS0106: The modifier 'static' is not valid for this item
cs14b-ext.cs(9,27): error CS8652: The feature 'extension indexers' is currently in Preview and *unsupported*. To use Preview features, use the 'preview' language version.
cs14b-ext.cs(9,27): error CS9303: 'this[]': cannot declare instance members in an extension block with an unnamed receiver parameter
===== csc -langversion:preview -out:ex.dll cs14b-ext.cs 2>&1 | sort (cc exit=1) =====
cs14b-ext.cs(9,27): error CS0106: The modifier 'static' is not valid for this item
cs14b-ext.cs(9,27): error CS9303: 'this[]': cannot declare instance members in an extension block with an unnamed receiver parameter
```

- ★★★ **`-langversion:latest` 에서 `CS8652`** — 「확장 인덱서는 **Preview 이고 지원되지 않는다**」.\
  **기능 이름을 컴파일러가 직접 말해 준다**(`extension indexers`).
- ★★★ **`-langversion:preview` 로 다시 던지면 `CS8652` 가 사라진다.** 즉 **인스턴스 확장 인덱서는 preview 에서 열린다.**
- ★★★ **그래도 남는 에러 둘이 결론이다** — `CS0106`(`static` 은 여전히 안 된다) ·\
  `CS9303`(이름 없는 수신자 `extension(int[])` 블록에는 인스턴스 멤버를 못 둔다).\
  ★ 즉 **「정적 확장 인덱서」는 preview 에서도 안 된다** — (6)의 제약이 확장으로도 안 풀린다.
- ★ **`CS8652` 와 `CS0106` 은 성격이 다르다** — 앞쪽은 「다음 판을 기다리라」이고 뒤쪽은 「원리상 안 된다」다.\
  ★★ **한 낱말로 「미지원」이라고 적으면 이 둘이 뭉개진다**(지침 §2-1 규칙 9).

인스턴스 확장 인덱서만 남기고 실제로 써 보면.

```text
===== 소스: cs14b-extuse.cs =====
using System;
public static class Ext {
    extension(int[] a) {
        public int this[string name] => name == "first" ? a[0] : a[^1];
    }
}
class Program {
    static void Main() {
        int[] a = { 10, 20, 30 };
        Console.WriteLine(a["first"]);
    }
}
===== csc -langversion:preview -out:ex.dll cs14b-extuse.cs 2>&1 | sort (cc exit=1) =====
cs14b-extuse.cs(10,29): error CS0029: Cannot implicitly convert type 'string' to 'int'
```

- ★★★ **`CS0029: Cannot implicitly convert type 'string' to 'int'`.**\
  `a["first"]` 에서 **확장 인덱서가 후보로 아예 안 올라왔고** 배열의 기본 인덱싱으로 해석됐다.
- ★★★ **선언은 통과하는데 호출이 안 된다** — 지침의 「**통과도 출력이다**」가 그대로 나온 자리다.\
  **선언만 보고 「preview 에서 된다」고 적으면 틀린다.** 이 판에서 **확장 인덱서는 쓸 수 없다.**
- ★ 진단의 줄·열이 `(10,29)` 로 **호출 자리**를 가리키는 것이 그 증거다.

> ★★★ **이것이 이 주제의 「제3의 상태」다** — 「**못 잰 것**」이 아니라 「**이 판에서는 안 되는 것**」이다.\
> 그리고 **안 된다는 판정 자체가 두 진단으로 갈려 있다**(`CS8652` 대 `CS0106`/`CS9303`).

### (8) 인덱서와 컬렉션 초기화의 만남

- ★ 인덱서가 있으면 **인덱스 초기화 구문**(`new T { [0] = "가" }`)을 쓸 수 있다 —\
  그 문법 자체는 [11번](../11-collection-initializers-and-collection-expressions/)이 정본이고 **여기서 다시 재지 않았다.**
- ★★ 다만 경계를 적어 둔다 — **컬렉션 식**(`[1, 2, 3]`)은 인덱서와 무관하다.\
  그쪽은 `Add` 메서드나 `CollectionBuilder` 를 본다. **대괄호가 같다고 같은 기능이 아니다.**

### (9) ★★ 할당 바이트 — `object` 인덱서가 박싱한다 · 2×2 판 격자

```text
===== 소스: cs14b-alloc.cs =====
using System;

class Dict {
    readonly int[] cells = { 10, 20, 30 };
    public int this[int i]      => cells[i];
    public int this[object key] => cells[(int)key];
    public int Get(int i)       => cells[i];
}

class Program {
    static long M(Action a) {
        a();                                             // 한 판 데워 놓고
        var b = GC.GetAllocatedBytesForCurrentThread();
        a();
        return GC.GetAllocatedBytesForCurrentThread() - b;
    }
    static void Main() {
        var d = new Dict();
        int sink = 0;
        Console.WriteLine($"this[int]    1000회 : {M(() => { for (int i = 0; i < 1000; i++) sink += d[1]; })} 바이트");
        Console.WriteLine($"this[object] 1000회 : {M(() => { for (int i = 0; i < 1000; i++) sink += d[(object)1]; })} 바이트");
        Console.WriteLine($"Get(int)     1000회 : {M(() => { for (int i = 0; i < 1000; i++) sink += d.Get(1); })} 바이트");
        Console.WriteLine($"(합 {sink})");
    }
}
===== csc -out:ex.dll cs14b-alloc.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
this[int]    1000회 : 0 바이트
this[object] 1000회 : 24000 바이트
Get(int)     1000회 : 0 바이트
(합 120000)
===== csc -optimize -out:ex.dll cs14b-alloc.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
this[int]    1000회 : 0 바이트
this[object] 1000회 : 24000 바이트
Get(int)     1000회 : 0 바이트
(합 120000)
===== csc -out:ex.dll cs14b-alloc.cs && DOTNET_TieredCompilation=0 dotnet ex.dll (cc exit=0 · run exit=0) =====
this[int]    1000회 : 0 바이트
this[object] 1000회 : 24000 바이트
Get(int)     1000회 : 0 바이트
(합 120000)
===== csc -optimize -out:ex.dll cs14b-alloc.cs && DOTNET_TieredCompilation=0 dotnet ex.dll (cc exit=0 · run exit=0) =====
this[int]    1000회 : 0 바이트
this[object] 1000회 : 24000 바이트
Get(int)     1000회 : 0 바이트
(합 120000)
```

- ★★★ **`this[object]` 만 24,000 바이트**다. 1000회에 24바이트씩 — **`int` 하나를 박싱한 크기**다.\
  [03번](../03-boxing-and-unboxing/)이 정본인 그 비용이 **인덱서 오버로드 선택으로 새어 들어온 것**이다.
- ★★★ **`this[int]` 와 `Get(int)` 는 둘 다 0 이다.** 즉 **인덱서라서 비싼 것이 아니다** —\
  **인자 타입이 `object` 라서** 비싼 것이다. 이 구분을 놓치면 틀린 결론이 나온다.
- ★★★ **판 격자 — 네 칸 전부 한 글자도 같았다.**

| 판 | `this[int]` | `this[object]` | `Get(int)` | 움직였나 |
|---|---|---|---|---|
| 기본 | 0 | 24000 | 0 | — |
| `csc -optimize` | 0 | 24000 | 0 | ★ **안 움직임** |
| `DOTNET_TieredCompilation=0` | 0 | 24000 | 0 | ★ **안 움직임** |
| 둘 다 | 0 | 24000 | 0 | ★ **안 움직임** |

- ★★★ **움직인 칸 0 / 12.** 그래서 이 수치는 **근거로 쓸 수 있다**(규칙 24).\
  ★ [11번](../11-collection-initializers-and-collection-expressions/)에서 「상수 쪽이 더 비싸다」로 읽힐 뻔한 사고가\
  **tier-0 JIT 의 잡음**이었던 것과 대비된다 — 거기서는 **셋이 움직였다.**
- ★★ **이 실험이 계수형이라 판을 잘 안 탄다** — 박싱은 **할당 횟수**이지 **시간**이 아니다.\
  지침이 적은 대로 「계수는 판을 잘 안 타고, 시간과 바이트는 잘 탄다」인데,\
  ★ **이 바이트는 시간이 아니라 계수에서 나온 것**이라 안정적이다.
- ★★★ **시간은 한 줄도 안 쟀다.** 「인덱서 호출이 메서드 호출보다 느리다/빠르다」는 문장이 이 문서에 없다.

```text
   d[1]                      d[(object)1]
   ─────────────             ─────────────────────────────
   스택의 int 1              스택의 int 1
        │                         │  박싱 — 힙에 24바이트
        │                         ▼
        │                    ┌──────────────┐
        │                    │ 헤더 │ 1     │   ← 1000회면 24,000바이트
        │                    └──────────────┘
        ▼                         ▼
   get_Item(int)             get_Item(object) ──> 언박싱해서 (int)key

   ★ 비싼 것은 「인덱서」가 아니라 「object 인자」다. Get(int) 도 0바이트다.
```

### (10) ★★ 언제 인덱서 대신 메서드가 나은가 — 실패 사례로

**실패 사례 셋**이 앞 절들에서 이미 나왔다. 그것이 판단 기준이다.

| 실패 사례 | 어디서 | 그래서 무엇을 쓰나 |
|---|---|---|
| ★★★ **같은 인자 타입으로 뜻이 다른 두 조회** | (3) `CS0111` | **이름 있는 메서드 둘** — `ByPosition(int)`·`ById(int)` |
| ★★★ **`object` 로 받는 인덱서** | (9) 24,000바이트 | **제네릭 메서드**나 **정확한 타입의 오버로드** |
| ★★ **타입 바깥에서 붙이고 싶을 때** | (7) `CS8652`·`CS9303` | **확장 메서드** — 확장 인덱서는 이 판에서 안 된다 |
| ★★ **수신자 없이 부르고 싶을 때** | (6) `CS0106` | **정적 메서드** — `static` 인덱서는 없다 |

- ★★★ **일반 기준 하나 더** — 인덱서는 **싸고 부작용이 없어야** 한다.\
  `obj[i]` 는 **배열 접근처럼 보이므로** 읽는 사람이 **비용을 의심하지 않는다.**\
  DB 를 치거나 파일을 읽는다면 **메서드로 두어 호출자가 비용을 보게** 한다.\
  ★ 이 기준은 [13번](../13-properties-init-required-field/)의 「계산 속성 대 메서드」와 **같은 기준**이다.
- ★ **인자가 셋 이상이면** 거의 언제나 메서드가 낫다 — `t[a, b, c]` 는 **무슨 뜻인지 읽히지 않는다.**

```text
   내 타입에 대괄호를 달까?

   같은 인자 타입으로 뜻이 다른 조회가 둘 이상인가? ──예──> 메서드 (CS0111 로 막힌다)
                   │아니오
   인자를 object 로 받아야 하나? ───────────────────예──> 제네릭 메서드 (24바이트/호출)
                   │아니오
   타입 바깥에서 붙여야 하나? ─────────────────────예──> 확장 메서드 (CS8652·CS9303)
                   │아니오
   수신자 없이 불러야 하나? ──────────────────────예──> 정적 메서드 (CS0106)
                   │아니오
   비싸거나 부작용이 있나? ───────────────────────예──> 메서드 (읽는 사람이 비용을 의심하지 않는다)
                   │아니오
                   ▼
              인덱서를 단다
```

## 문법 — 형태와 규칙

### 형태

```csharp
// cs14b-form.cs
using System;
using System.Runtime.CompilerServices;

var t = new Table();
t[0] = "영";
Console.WriteLine($"{t[0]} {t["키"]} {t[1, 1]} {t[^1]} {t[0..2]} {t.Get(1)}");

class Table {
    readonly string[] cells = { "가", "나", "다" };
    public string this[int i]        { get => cells[i]; set => cells[i] = value; }  // 읽고 쓰는 인덱서
    public string this[string key]   => $"키({key})";                               // 오버로드 — 다른 인자 타입
    public string this[int r, int c] => $"격자({r},{c})";                           // 다차원
    public string this[Index i]      => $"끝기준({cells[i]})";                      // Index 를 받는다
    public string this[Range r]      => $"범위({r})";                               // Range 를 받는다
    public string Get(int i) => cells[i];                                           // 같은 일을 하는 메서드
}
```

```text
===== 소스: cs14b-form.cs =====
using System;
using System.Runtime.CompilerServices;

var t = new Table();
t[0] = "영";
Console.WriteLine($"{t[0]} {t["키"]} {t[1, 1]} {t[^1]} {t[0..2]} {t.Get(1)}");

class Table {
    readonly string[] cells = { "가", "나", "다" };
    public string this[int i]        { get => cells[i]; set => cells[i] = value; }  // 읽고 쓰는 인덱서
    public string this[string key]   => $"키({key})";                               // 오버로드 — 다른 인자 타입
    public string this[int r, int c] => $"격자({r},{c})";                           // 다차원
    public string this[Index i]      => $"끝기준({cells[i]})";                      // Index 를 받는다
    public string this[Range r]      => $"범위({r})";                               // Range 를 받는다
    public string Get(int i) => cells[i];                                           // 같은 일을 하는 메서드
}
===== csc -out:ex.dll cs14b-form.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
영 키(키) 격자(1,1) 끝기준(다) 범위(0..2) 나
```

- **`this` 키워드로 선언한다** — 이름을 못 짓는 것이 속성과 다른 첫 번째 점이다.
- **`get`·`set` 은 속성과 같다.** `init` 도 붙일 수 있다(이 판에서 따로 안 던졌다).
- **오버로드는 인자 타입으로만 갈린다**((3)) — 매개변수 이름은 아무 소용이 없다.
- **`Index`·`Range` 를 직접 받을 수 있다**((5)) — 안 받으면 **패턴 기반 인덱싱**으로 풀린다.
- ★ 출력의 칸을 읽어라 — `t[0]` 가 `"영"` 으로 바뀌었고(`set` 이 돌았다), 나머지 다섯이 **서로 다른 오버로드**로 갔다.

### 금지 사례 — 진단이 나는 꼴

| 쓴 꼴 | 진단 코드 | 어디서 |
|---|---|---|
| `this[int position]` 과 `this[int id]` 를 함께 | `CS0111` | (3) — 매개변수 이름은 시그니처가 아니다 |
| `public static int this[int i]` | `CS0106` | (6) — `static` 인덱서는 없다 |
| `extension(int[] a) { public int this[string n] … }` | `CS8652` | (7) — `latest` 에서. **preview 면 사라진다** |
| `extension(int[]) { public static int this[char c] … }` | `CS0106`·`CS9303` | (7) — **preview 에서도 안 된다** |
| preview 로 선언한 확장 인덱서를 실제로 호출 | `CS0029` | (7) — 후보에 안 올라온다 |

## 어디서 틀리나

1. ★★★ **「인덱서는 배열이니까 공짜」** — **메서드 호출**이다((1)). 비싸면 메서드로 두어 비용을 보이게 하라((10)).
2. ★★★ **「`^1` 은 언제나 `Index` 를 만든다」** — **내가 `this[Index]` 를 선언했을 때만**이다((5)).\
   안 했으면 컴파일러가 `Length - 1` 을 직접 계산한다.
3. ★★★ **「같은 `int` 로 두 가지 조회를 만들면 된다」** — `CS0111` 로 막힌다((3)).\
   **매개변수 이름을 다르게 지어도 소용없다.**
4. ★★★ **「`object` 인덱서 하나면 다 받는다」** — **호출마다 박싱**이 생긴다((9)). 1000회에 24,000바이트.
5. ★★ **「C# 14 확장 멤버로 인덱서도 붙일 수 있다」** — **이 판에서는 못 붙인다**((7)).\
   `latest` 는 `CS8652`, `preview` 는 선언은 되는데 **호출이 `CS0029` 로 막힌다.**
6. ★★ **「`[IndexerName]` 을 바꾸면 소스도 바뀐다」** — **안 바뀐다**((2)). 바뀌는 것은 **메타데이터와 리플렉션**뿐이다.
7. ★★ **「명시적 구현 인덱서는 그냥 부를 수 있다」** — **`private` 이라 캐스트해야** 한다((4)).
8. ★ **「`static` 인덱서가 없는 것은 구현의 한계」** — **문법 수준의 제약**이다((6)).
9. ★ **「대괄호가 같으니 컬렉션 식도 인덱서를 본다」** — 무관하다((8)). 그쪽은 `Add`/`CollectionBuilder` 를 본다.

## 구현 세부사항 대 언어 보장

| 무엇 | 층 | 근거 |
|---|---|---|
| **인덱서가 접근자 메서드로 컴파일된다** | ★★★ **언어 보장** | (1) |
| **`static` 인덱서가 없다** | ★★★ **언어 보장** | (6) `CS0106` |
| **인자 타입이 같으면 오버로드가 안 된다** | ★★★ **언어 보장** | (3) `CS0111` |
| **패턴 기반 인덱싱이 있다**(`Length` + `this[int]`) | ★★★ **언어 보장**(C# 8) | (5) |
| **기본 이름이 `Item` 이다** | ★★ **구현 규약** | (1) — 그래서 `[IndexerName]` 으로 바꿀 수 있다 |
| **`DefaultMemberAttribute` 로 적는다** | ★★ **구현 규약(BCL)** | (1)(2) |
| **`^1` 이 `dup`/`sub` 로 풀리는 구체적 코드** | ★★ **구현(Roslyn)** | (5) |
| **확장 인덱서가 preview 에서도 못 쓰인다** | ★ **이 판의 관찰** | (7) — 다음 판에서 열릴 수 있다 |
| **`this[object]` 가 24바이트씩 할당한다** | ★★ **런타임 구현** | (9) — 박싱 크기는 런타임이 정한다 |
| **진단 문구 전부** | ★ **이 판의 관찰** | 근거로는 **코드와 `(행,열)`** 만 쓴다 |

## 언제 쓰고 언제 안 쓰나

- **쓴다** — 타입이 **컬렉션처럼 읽히는 것이 자연스러울 때**(행·표·버퍼·사전).\
  「원소를 꺼낸다」가 **한 낱말로 설명되는** 경우다.
- **쓴다** — `Length`/`Count` 와 `this[int]` 가 있으면 **`^`·`..` 이 공짜로 붙는다**((5)). 그 자체로 값이 있다.
- **안 쓴다** — (10)의 실패 사례 넷에 하나라도 걸릴 때.\
  ★★★ 특히 **같은 타입으로 뜻이 다른 두 조회**는 **원리상 인덱서로 못 한다.**
- **안 쓴다** — 비싸거나 부작용이 있을 때. `obj[i]` 는 **읽는 사람이 비용을 의심하지 않는 문법**이다.

## 핵심 문장

1. ★★★ **인덱서는 인자를 받는 속성이다.** `get_Item`/`set_Item` 두 메서드와 `[DefaultMember]` 안내판이 전부다((1)).
2. ★★★ **`^1` 은 두 갈래로 풀린다.** `this[Index]` 를 선언했으면 `newobj Index`, 안 했으면 `Length - 1`((5)).
3. ★★★ **인덱서로 못 하는 것 셋** — `static`((6)) · 같은 인자 타입 둘((3)) · 확장으로 붙이기((7), 이 판 기준).
4. ★★ **비싼 것은 인덱서가 아니라 `object` 인자다.** `this[int]` 는 0바이트, `this[object]` 는 24바이트/호출((9)).
5. ★★ **`[IndexerName]` 이 바꾸는 것은 메타데이터뿐이다.** 소스는 한 글자도 안 바뀐다((2)).

## 관련 자료

- [13번 — 속성과 `init`·`required`·`field`](../13-properties-init-required-field/) — **한 사슬이다.**\
  **그쪽은 「이름 있는 접근자」까지, 여기는 「인자를 받는 접근자」부터.** 접근자 접근성·`init` 은 전부 그쪽이 정본이다.
- [16번 — 상속](../16-inheritance-virtual-override-abstract-sealed-new/) — **명시적 인터페이스 구현이 `private` 인 것**((4))의 정본.\
  `callvirt` 가 왜 나오는지도 그쪽 (4)에 있다.
- [11번 — 컬렉션 초기화와 컬렉션 식](../11-collection-initializers-and-collection-expressions/) — **인덱스 초기화 구문**((8))과 **컬렉션 식**의 정본.
- [10번 — 컬렉션 고르기](../10-collection-choosing-list-dictionary-hashset-queue-stack/) — **어떤 컬렉션을 쓸까**는 거기, 여기는 **내 타입에 대괄호 달기**.
- [03번 — 박싱과 언박싱](../03-boxing-and-unboxing/) — **(9)의 24바이트가 어디서 오는지**의 정본. IL 디스어셈블러도 거기서 만들었다.
- [09번](../09-arrays-index-and-range/)(배열과 인덱스·범위 연산자) — **`^`·`..` 연산자 자체**는 그쪽.
- 파이썬 갈래 목록([`python/syntax/README.md`](../../../python/syntax/README.md))의 **32번**([`32-container-protocol/`](../../../python/syntax/32-container-protocol/)) — `__getitem__` 대비.

## 용어 풀이

- **인덱서(indexer)** — `obj[...]` 문법을 받는 멤버. `this` 키워드로 선언한다.
- **`Item`** — 인덱서 접근자의 기본 이름. `get_Item`/`set_Item` 이 된다.
- **`DefaultMemberAttribute`** — 타입에 붙는 「기본 멤버 이름」 안내판. 컴파일러가 자동으로 붙인다.
- **`IndexerNameAttribute`** — 그 이름을 바꾸는 어트리뷰트. 소스 문법은 안 바뀐다.
- **패턴 기반 인덱싱(pattern-based indexing)** — `Length`/`Count` 와 `this[int]` 만으로 `^`·`..` 이 붙는 규칙(C# 8).
- **`System.Index`·`System.Range`** — `^1`·`0..2` 가 만드는 **진짜 값 타입**. 문법 설탕이 아니다.
- **박싱(boxing)** — 값 타입을 `object` 로 올릴 때 힙에 담는 것. [03번](../03-boxing-and-unboxing/)이 정본이다.
- **확장 멤버(extension member)** — C# 14 의 `extension` 블록. 인덱서는 **이 판에서 안 열린다**((7)).

## 더 들어가면

- ★ **`this[Index]` 를 선언하면 무엇이 좋아지나** — (5)에서 봤듯 **`Length` 를 안 읽는다.**\
  `Length` 가 비싼 타입(지연 계산·원격)이라면 그 차이가 실제 비용이 된다. ★★★ **이 판에서 그 비용은 안 쟀다.**
- ★ **`this[Range]` 와 슬라이스** — 패턴 쪽은 `Slice(int, int)` 라는 이름의 메서드를 찾는다.\
  ★★★ **이 판에서 `Slice` 패턴은 안 던졌다** — `this[Range]` 를 직접 선언한 판만 봤다((3)).
- ★ **인덱서에 `ref` 반환을 붙일 수 있나** — `List<T>` 에는 없지만 `Span<T>` 에는 있다.\
  ★★★ **이 판에서 안 던졌다.** [13번](../13-properties-init-required-field/) (8)의 `ref` 반환 속성 규칙이 어떻게 이어지는지는 확인 안 했다.
