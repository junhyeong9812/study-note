# csharp/syntax/14 — 인덱서 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·진단·IL 은 **.NET SDK 10.0.401** · 런타임 **10.0.12** · 타겟 **`net10.0`** ·
> **linux-x64** 에서 실제로 돌려 얻은 것이다(2026-09-26).\
> 진단은 **`-preferreduilang:en-US`** 로 영어로 고정했다.\
> ★ 블록은 캡처 스크립트가 파일로 받아 조립기가 끼워 넣은 것이다 — 손으로 옮긴 줄은 없다.
> **읽는 법** — **진단 문구**와 **IL 오프셋 폭**은 흔들리는 칸이다.\
> 근거로 쓰는 것은 **옵코드 이름과 순서 · 진단 코드와 `(행,열)` · `DefaultMember` 이름 ·
> 할당이 0 인 칸과 0 이 아닌 칸 · `cc exit`/`run exit`** 다.\
> ★★★ **할당 바이트는 2×2 판 격자로 갈랐다**(6번) — 한 판의 절댓값은 근거가 아니다.
> ★★★ **이 문서는 시간을 재지 않았다.** 「인덱서 호출이 메서드보다 느리다」 같은 문장이 **한 줄도 없다.**

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ **`get_Item`·`set_Item` 두 메서드와 `[DefaultMember("Item")]` 안내판**이다

**출력**

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

**왜 그런가**

- ★★★ **타입에 `DefaultMemberAttribute` 가 붙었다.** 소스에 안 적었는데 **컴파일러가 붙였고**,\
  값은 **`Item`** 이다 — 「이 타입의 기본 멤버 이름은 `Item` 이다」라는 안내판이다.\
  리플렉션이 `obj[...]` 를 찾을 때 이 자리를 읽는다.
- ★★★ **메서드는 `get_Item`·`set_Item` 둘뿐이다.** [13번](../13-properties-init-required-field/)의 `get_X`/`set_X` 와 **똑같은 규칙**이고\
  이름만 `Item` 으로 고정된 것이 전부다. ★ **인덱서는 인자를 받는 속성**이라는 말이 이 한 줄로 증명된다.
- ★★★ **속성 목록에 `Item` 이 나오고 `인자=1` 이다.** 인덱서는 **리플렉션에서 속성으로 보인다.**\
  ★★ **속성과 인덱서를 가르는 유일한 칸은 `GetIndexParameters().Length` 다** — 속성은 0, 인덱서는 1 이상.
- ★ `r[1] = "바뀜"` 이 그대로 돌아 `"바뀜"` 이 찍혔다.

```text
   class Row {                        컴파일러가 만든 것
       public string this[int i]      ┌─ [DefaultMember("Item")]   ← 타입에 붙는다
       { get => …; set => …; }        ├─ string get_Item(int i)
   }                                  └─ void   set_Item(int i, string value)

   리플렉션으로 보면
   ┌────────────────────┬──────────┬────────────────────────┐
   │ 속성 이름           │ Item     │ GetIndexParameters()=1 │ ← ★ 속성과 갈리는 유일한 칸
   │ 메서드              │ get_Item · set_Item              │
   │ 타입 어트리뷰트      │ DefaultMemberAttribute           │
   └────────────────────┴──────────┴────────────────────────┘
```

### 2. ★★ **메타데이터만 바뀐다** — 소스는 한 글자도 안 바뀐다

**출력**

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

**왜 그런가**

- ★★★ **메서드가 `get_Cell`/`set_Cell` 이 되고 `DefaultMember` 도 `Cell` 이 됐다.**
- ★★★ **`GetProperty("Item")` 이 「없음」이고 `GetProperty("Cell")` 이 「있음」이다.**\
  리플렉션으로 `Item` 을 찾던 코드는 **이 타입에서 못 찾는다.**
- ★★ **소스는 그대로다** — `g[1, 1] = 5` 와 `g[1,1]` 이 아무 표시 없이 돌았고 `5` 가 찍혔다.\
  ★ 즉 **`[IndexerName]` 의 실효는 메타데이터뿐**이다.
- ★ **그래서 이 어트리뷰트는 C# 을 위한 것이 아니다.** 인덱서 개념이 없는 언어에서 이 타입을 쓸 때,\
  또는 `Item` 이라는 이름이 다른 멤버와 충돌할 때 쓴다.
- ★ **다차원 인덱서**(`this[int r, int c]`)의 `인자=2` 도 함께 찍혔다.

### 3. ★ **다섯이 각각 다른 인덱서로 간다** — 인자 타입이 시그니처다

**출력**

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

**왜 그런가**

- ★★ **다섯 줄이 전부 다른 인덱서로 갔다.** 인자 타입이 다르면 **평범한 메서드 오버로드와 같은 규칙**으로 갈린다.
- ★★★ **`r[^1]` 이 `this[Index]` 로, `r[0..2]` 가 `this[Range]` 로 갔다.**\
  ★★★ **`^1` 과 `0..2` 는 문법 설탕이 아니라 `System.Index`·`System.Range` 라는 진짜 타입의 값**이다.\
  `Range 로 왔다 — 0..2` 라고 찍힌 것이 그 증거다 — `Range.ToString()` 이 돌았다.
- ★★★ **인자 타입이 같으면 `CS0111` 이다.** `this[int position]` 과 `this[int id]` 는\
  **매개변수 이름만 다를 뿐 같은 시그니처**다. **이름을 다르게 지어도 소용없다.**
- ★★★ **이것이 9번의 「언제 메서드가 나은가」로 직결된다** — 같은 타입으로 **뜻이 다른 두 조회**는\
  **인덱서로는 원리상 못 만든다.**

### 4. ★★★ **다르다** — `newobj Index` 대 `Length - 1`

**출력**

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

**왜 그런가**

- ★★★ **`this[Index]` 를 선언한 쪽**(`Explicit`)은 `ldc.i4.1 / ldc.i4.1 / newobj System.Index::.ctor` 로\
  **`Index` 값을 만들어 그대로 넘긴다.** 「끝에서 1」이라는 뜻이 **런타임까지 살아 있다.**
- ★★★ **선언 안 한 쪽**(`Pattern`)은 `dup / callvirt get_Length / ldc.i4.1 / sub / callvirt get_Item` 이다.\
  **컴파일러가 `Length - 1` 을 직접 계산해 `int` 인덱서로 보낸다.** `Index` 타입이 **아예 안 나타난다.**
- ★★ **`dup` 이 나오는 이유** — 수신자를 **두 번** 써야 한다(`Length` 를 읽고, 그 다음 `Item` 을 읽는다).\
  스택에서 복제해 두는 것이 `dup` 이다.
- ★★★ **`Pattern` 은 인터페이스를 하나도 구현하지 않았다.** 그런데도 `^1` 이 붙는다 —\
  ★ C# 8 의 **패턴 기반 인덱싱**이다. 타입에 `Length`(또는 `Count`)와 `this[int]` 만 있으면\
  **컴파일러가 모양만 보고** `^`·`..` 을 허용한다. **명목적 타이핑이 아니라 구조적 규칙**인 드문 자리다.
- ★ **`callvirt` 가 나온 것은 가상 호출이라는 뜻이 아니다** — [16번](../16-inheritance-virtual-override-abstract-sealed-new/) (4)가 정본이다.

### 5. ★★ **못 붙인다** — `latest` 는 `CS8652`, `preview` 는 호출이 `CS0029`

**출력**

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

**왜 그런가**

- ★★★ **`-langversion:latest` 에서 `CS8652`** — 「`extension indexers` 는 **Preview 이고 지원되지 않는다**」.\
  **기능 이름을 컴파일러가 직접 말해 준다.**
- ★★★ **`-langversion:preview` 로 던지면 `CS8652` 두 건이 사라진다.** 즉 **인스턴스 확장 인덱서 선언 자체는 preview 에서 열린다.**
- ★★★ **남는 에러 둘이 결론이다.**
  - **`CS0106`** — `static` 은 여전히 안 된다. **7번의 제약이 확장으로도 안 풀린다.**
  - **`CS9303`** — 이름 없는 수신자 블록(`extension(int[])`)에는 **인스턴스 멤버를 못 둔다.**
- ★★ **두 코드의 성격이 다르다** — `CS8652` 는 「**다음 판을 기다리라**」이고,\
  `CS0106`·`CS9303` 은 「**원리상 안 된다**」다.\
  ★★★ **한 낱말로 「미지원」이라 적으면 이 둘이 뭉개진다**(지침 §2-1 규칙 9의 `ERROR 1064` 대 `ERROR 1235` 와 같은 꼴).
- ★★★ **선언이 통과해도 호출이 막힌다.** `a["first"]` 가 **`CS0029: Cannot implicitly convert type 'string' to 'int'`** 로 죽었다 —\
  확장 인덱서가 **후보로 아예 안 올라왔고** 배열의 기본 인덱싱으로 해석됐다.\
  ★ 진단이 `(10,29)` 로 **호출 자리**를 가리키는 것이 그 증거다.
- ★★★ **「통과도 출력이다」가 그대로 나온 자리다** — 선언만 보고 「preview 에서 된다」고 적으면 틀린다.\
  ★ 이것은 「**못 잰 것**」이 아니라 「**이 판에서는 안 되는 것**」이다. 판정 근거가 블록 둘로 남아 있다.

### 6. ★★ **0 · 24000 · 0** — 그리고 2×2 네 판이 전부 같다

**출력**

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

**왜 그런가**

- ★★★ **`this[object]` 만 24,000 바이트**다. 1000회에 24바이트씩 — **`int` 하나를 박싱한 크기**다.\
  [03번](../03-boxing-and-unboxing/)이 정본인 그 비용이 **인덱서 오버로드 선택으로 새어 들어온 것**이다.
- ★★★ **`this[int]` 와 `Get(int)` 가 둘 다 0 이다.** 즉 **인덱서라서 비싼 것이 아니다** —\
  **인자 타입이 `object` 라서** 비싸다. ★ 이 구분을 놓치면 「인덱서는 느리다」는 틀린 결론이 나온다.
- ★★★ **판 격자 — 움직인 칸 0 / 12.**

| 판 | `this[int]` | `this[object]` | `Get(int)` | 움직였나 |
|---|---|---|---|---|
| 기본 | 0 | 24000 | 0 | — |
| `csc -optimize` | 0 | 24000 | 0 | ★ **안 움직임** |
| `DOTNET_TieredCompilation=0` | 0 | 24000 | 0 | ★ **안 움직임** |
| 둘 다 | 0 | 24000 | 0 | ★ **안 움직임** |

- ★★★ **그래서 이 수치를 근거로 쓸 수 있다**(규칙 24).\
  ★ [11번](../11-collection-initializers-and-collection-expressions/)에서는 컬렉션 식의 할당이 **판마다 움직여**\
  「상수 쪽이 더 비싸다」로 읽힐 뻔했다(tier-0 JIT 의 잡음). **여기는 한 칸도 안 움직였다.**
- ★★ **왜 안 움직이나** — 이 수치는 **시간이 아니라 계수**에서 나온다.\
  박싱은 「몇 번 할당했나」이고, 그 횟수는 **JIT 의 최적화 수준과 무관**하다.\
  지침이 적은 대로 「계수는 판을 잘 안 타고, 시간과 바이트는 잘 탄다」인데,\
  ★ **이 바이트는 계수에서 나온 바이트**라 안정적이다.
- ★★ **측정 방법** — `GC.GetAllocatedBytesForCurrentThread()` 의 차이를 읽고,\
  **한 판 먼저 데워 놓고**(JIT·정적 초기화가 첫 판에 섞이지 않게) 두 번째 판만 잰다.
- ★★★ **시간은 한 줄도 안 쟀다.**

### 7. ★ **`CS0106`** — 문법 수준의 제약이다

**출력**

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

**왜 그런가**

- ★★★ **`CS0106: The modifier 'static' is not valid for this item`.**
- ★★ **왜 문법 수준인가** — 인덱서는 `obj[i]` 문법을 받는 멤버인데 `static` 이면 **수신자가 없다.**\
  그러면 `Table[0]` 이라고 써야 하는데, 그 자리의 대괄호는 이미 **배열 타입 표기**(`Table[]`)로 쓰이고 있다.\
  ★ **파서가 둘을 가를 수 없다** — 구현이 게을러서가 아니다.
- ★ **확장으로도 안 풀린다** — 5번에서 `extension(int[]) { public static int this[char c] … }` 가\
  **preview 에서도 `CS0106`** 으로 막혔다.

### 8. ★ **`private` 이다** — 안내판은 인터페이스 쪽에 붙는다

**출력**

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

**왜 그런가**

- ★★ **`메서드 ILookup.get_Item  private=True`** — 명시적 구현 인덱서는 **클래스 밖에서 직접 못 부른다.**\
  `l[3]` 로 부를 수 있었던 것은 **변수 타입이 `ILookup` 이기 때문**이다.
- ★★★ **`DefaultMemberAttribute` 가 `ILookup` 에만 있고 `Impl` 에는 없다.**\
  `Impl` 은 **자기 인덱서를 선언한 적이 없다** — 인터페이스가 요구한 것을 채웠을 뿐이다.\
  ★ 안내판은 「**이 타입에 인덱서가 선언되어 있다**」는 표시이므로 `Impl` 에는 붙을 이유가 없다.
- ★ **부르려면 캐스트가 필요하다** — `((ILookup)impl)[3]`.\
  ★★ 이 성질의 정본은 [16번](../16-inheritance-virtual-override-abstract-sealed-new/) (8)이다 — 거기서 `IsFinal`·`IsVirtual` 까지 함께 찍었다.

```text
   interface ILookup { string this[int i] { get; } }   ← [DefaultMember] 가 여기 붙는다
            ▲
            │ 구현
   class Impl : ILookup {                              ← 안내판이 안 붙는다
       string ILookup.this[int i] => …                 ← 이름이 ILookup.get_Item · private
   }

   Impl impl = new Impl();
   impl[3]            ──>  ✕  클래스에는 인덱서가 없다
   ((ILookup)impl)[3] ──>  ○  「명시적 인덱서 — 3」
```

### 9. ★★★ **실패 사례 넷 중 하나라도 걸리면** 메서드로 간다

**왜 그런가**

| 실패 사례 | 어디서 | 그래서 무엇을 쓰나 |
|---|---|---|
| ★★★ **같은 인자 타입으로 뜻이 다른 두 조회** | 3번 `CS0111` | **이름 있는 메서드 둘** — `ByPosition(int)`·`ById(int)` |
| ★★★ **`object` 로 받는 인덱서** | 6번 24,000바이트 | **제네릭 메서드**나 **정확한 타입의 오버로드** |
| ★★ **타입 바깥에서 붙이고 싶을 때** | 5번 `CS8652`·`CS9303` | **확장 메서드** — 확장 인덱서는 이 판에서 안 된다 |
| ★★ **수신자 없이 부르고 싶을 때** | 7번 `CS0106` | **정적 메서드** — `static` 인덱서는 없다 |

- ★★★ **같은 `int` 로 뜻이 다른 두 조회는 원리상 못 만든다.** 3번의 `CS0111` 이 그 증명이다.\
  **매개변수 이름을 다르게 지어도 시그니처는 같다.**
- ★★★ **비용의 기준 하나 더** — `obj[i]` 는 **배열 접근처럼 보이므로** 읽는 사람이 **비용을 의심하지 않는다.**\
  DB 를 치거나 파일을 읽거나 락을 잡는다면 **메서드로 두어 호출자가 비용을 보게** 한다.\
  ★ 이 기준은 [13번](../13-properties-init-required-field/)의 「계산 속성 대 메서드」와 **같은 기준**이다.
- ★ **인자가 셋 이상이면** 거의 언제나 메서드가 낫다 — `t[a, b, c]` 는 **매개변수 이름이 안 보여** 무슨 뜻인지 읽히지 않는다.\
  메서드는 이름과 인자 이름이 둘 다 보인다.

### 10. 잇기

- ★★★ **[13번](../13-properties-init-required-field/)과 한 사슬인 이유** — 둘 다 「**메서드로 컴파일되는 문법**」이다.\
  속성이 `get_X`/`set_X` 를 만들고 인덱서가 `get_Item`/`set_Item` 을 만든다. **인덱서는 인자를 받는 속성**이다.
- **박싱 24바이트의 정본**은 [03번](../03-boxing-and-unboxing/)이다.
- ★★ **명시적 인터페이스 구현이 `private` 인 것**의 정본은 [16번](../16-inheritance-virtual-override-abstract-sealed-new/) (8)이다.
- **인덱스 초기화 구문**(`new T { [0] = "가" }`)과 **컬렉션 식**(`[1, 2, 3]`)은 둘 다 [11번](../11-collection-initializers-and-collection-expressions/)인데\
  ★★★ **같은 기능이 아니다** — 앞쪽은 인덱서를 보고, 뒤쪽은 `Add`/`CollectionBuilder` 를 본다.\
  **대괄호가 같다고 같은 기능이 아니다.**
- **`^`·`..` 연산자 자체**는 [09번](../09-arrays-index-and-range/)이다. 여기서는 **내 타입이 그것을 받는 쪽**만 봤다.
- ★ **파이썬과 갈리는 한 칸** — 파이썬은 `__getitem__` 이라는 **약속된 이름**을 찾고,\
  C# 은 **`DefaultMemberAttribute` 라는 메타데이터**를 남긴다 — 그래서 C# 은 **이름을 바꿀 수 있다**(2번).\
  파이썬 갈래 목록([`python/syntax/README.md`](../../../python/syntax/README.md))의 **32번**([`32-container-protocol/`](../../../python/syntax/32-container-protocol/))이 그쪽 정본이다.

## 실행 검증

| 무엇 | 몇 번·어디서 | 결과 |
|---|---|---|
| `cs14b-basic.cs` 인덱서 → 메서드 | csc 1회 | ★★★ `get_Item`/`set_Item` · `DefaultMember = Item` · `인자=1` |
| `cs14b-name.cs` `[IndexerName]` | csc 1회 | ★★★ `get_Cell` · `GetProperty("Item")` **없음** |
| `cs14b-overload.cs` 오버로드 다섯 | csc 1회 | 다섯이 각각 다른 인덱서로 · `Range` 가 `0..2` 로 찍힘 |
| `cs14b-dup.cs` 같은 인자 타입 | csc 1회 | **`CS0111`** |
| `cs14b-il.cs` `^1` 의 IL | csc 1회(2메서드) | ★★★ `newobj Index` 대 `dup`/`sub` — **다르다** |
| `cs14b-static.cs` `static` 인덱서 | csc 1회 | **`CS0106`** |
| `cs14b-ext.cs` 확장 인덱서 | csc **2회**(`latest`·`preview`) | ★★★ `CS8652` 2건이 preview 에서 사라지고 `CS0106`·`CS9303` 남음 |
| `cs14b-extuse.cs` 확장 인덱서 호출 | csc 1회(`preview`) | ★★★ **`CS0029`** — 후보에 안 올라온다 |
| `cs14b-iface.cs` 명시적 구현 | csc 1회 | `private=True` · `DefaultMember` 는 **인터페이스에만** |
| `cs14b-alloc.cs` 할당 바이트 | csc **4회**(2×2 판 격자) | ★★★ `0 / 24000 / 0` · **움직인 칸 0 / 12** |
| `cs14b-form.cs` 형태 | csc 1회 | 여섯 꼴이 전부 컴파일·실행됐다 |

**구현 의존 항목** — 다음은 **이 판(.NET SDK 10.0.401 · 런타임 10.0.12 · linux-x64)에서만** 그렇다.

- ★★ **기본 이름이 `Item` 이고 `DefaultMemberAttribute` 로 적는다는 것** — 구현 규약이다.
- ★★ **`^1` 이 `dup`/`sub` 로 풀리는 구체적 코드** — Roslyn 이 정한다.
- ★★★ **확장 인덱서가 preview 에서도 못 쓰이는 것** — **다음 판에서 열릴 수 있다.**\
  ★ **그때 다시 던질 자리**로 `cs14b-ext.cs`·`cs14b-extuse.cs` 두 블록이 남아 있다.
- ★★ **박싱 24바이트** — 객체 헤더 크기는 런타임과 플랫폼이 정한다(x64 기준).
- ★ **진단 문구 전부** · **IL 오프셋 폭**.

**언어가 보장하는 것**(구현이 바뀌어도 같다)

- **인덱서가 접근자 메서드로 컴파일되는** 것.
- **`static` 인덱서가 없는** 것(문법 수준 제약).
- **인자 타입이 같으면 오버로드가 안 되는** 것 — 매개변수 이름은 시그니처가 아니다.
- **패턴 기반 인덱싱**(`Length`/`Count` + `this[int]` 만으로 `^`·`..` 이 붙는 것, C# 8).
- **`^1`·`0..2` 가 `System.Index`·`System.Range` 값인** 것 — 문법 설탕이 아니다.
- **명시적 인터페이스 구현이 `private` 인** 것.

**안 돌려 본 것 / 못 잰 것 / 잴 것이 없는 것**

- **안 돌려 본 것** — ★★ **`Slice(int, int)` 패턴**(`this[Range]` 를 직접 선언한 판만 봤다) ·\
  ★★ **`ref` 반환 인덱서**(`Span<T>` 가 그렇게 한다 — [13번](../13-properties-init-required-field/) (8)의 규칙이 어떻게 이어지는지 확인 안 했다) ·\
  ★ **`init` 인덱서** · ★ **`static abstract` 인터페이스 멤버로서의 인덱서**(C# 11) ·\
  ★ **인덱스 초기화 구문**(`new T { [0] = "가" }` — [11번](../11-collection-initializers-and-collection-expressions/)이 정본이라 여기서 안 재고 경계만 적었다) ·\
  ★ **`struct` 의 인덱서**(방어적 복사가 걸린다 — [02번](../02-struct-vs-class-choosing/)).
- **못 잰 것** — ★★★ **「인덱서 호출이 같은 일을 하는 메서드 호출보다 비싼가」.**\
  6번은 **할당**을 쟀지 **시간**을 재지 않았다. 시간을 재려면 벤치마크 하네스가 따로 필요하고\
  **한 판의 절댓값은 근거가 안 된다**(규칙 24). **그래서 수치를 하나도 안 적었다.**
- ★ 「**부적용인 창**」 — 없다. **이 주제는 네 창을 다 썼다** — 13번과 다른 점이다.

**버전이 올랐을 때 다시 돌려야 하는 것**

- ★★★ **5번의 확장 인덱서** — preview 딱지가 떨어지면 결론이 통째로 바뀐다. **블록 둘이 그대로 다시 던져진다.**
- ★★ **6번의 2×2 격자** — 런타임이 박싱을 없애는 최적화를 넣으면 움직인다.
- ★★ **1번·2번의 `DefaultMember` 규약** — Roslyn 이 바꾸면 움직인다.
- ★ **3번·4번·7번** — **명세가 정한 것이라 바뀔 일이 없다.** 바뀌면 그것이 뉴스다.
