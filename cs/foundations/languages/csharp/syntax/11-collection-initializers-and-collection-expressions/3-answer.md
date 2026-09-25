# csharp/syntax/11 — 컬렉션 초기화와 컬렉션 식(C# 12) — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·진단·IL·할당 바이트는 **.NET SDK 10.0.401** · 런타임 **10.0.12** ·
> 타겟 **`net10.0`** · **linux-x64** 에서 실제로 돌려 얻은 것이다(2026-09-25).\
> 진단은 **`-preferreduilang:en-US`** 로 영어로 고정했고, **`-debug` 를 안 줘** 트레이스에 경로·줄 번호가 안 박힌다.\
> ★ 블록은 캡처 스크립트가 파일로 받아 조립기가 끼워 넣은 것이다 — 손으로 옮긴 줄은 없다.
> **읽는 법** — **할당 바이트의 절댓값**과 **`<PrivateImplementationDetails>` 필드 이름**은 흔들리는 칸이다.\
> 근거로 쓰는 것은 **증분이 0이냐 아니냐 · 대상 타입끼리의 대소 관계 · IL 명령어 열 ·\
> 진단 코드와 `(행,열)` · `cc exit`/`run exit` · `Capacity`** 다.
> ★★★ **절댓값을 인용할 때는 판을 같이 적는다** — 9번이 **네 판을 나란히** 놓았다.
> ★★★ **이 문서는 시간을 재지 않았다.** 「몇 배 빠르다」는 문장이 **한 줄도 없다**.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★ `=` 가 없으면 **고치고**, 있으면 **갈아 끼운다**

**출력**

```text
===== 소스: cs11b-objinit.cs =====
using System;
using System.Collections.Generic;

var p = new Point { X = 1, Y = 2 };
Console.WriteLine($"객체 초기화자           : {p}");

var box = new Box { Label = "바깥", Inner = { X = 7, Y = 8 } };
Console.WriteLine($"중첩 초기화자(=  없음)  : {box.Label} / {box.Inner}   ← Inner 를 새로 만들지 않고 이미 있는 것을 고친다");

var box2 = new Box { Label = "바깥2", Inner = new Point { X = 9, Y = 9 } };
Console.WriteLine($"중첩 초기화자(= 있음)   : {box2.Label} / {box2.Inner}   ← 새로 만들어 갈아 끼운다");

var tags = new Box { Label = "리스트", Tags = { "a", "b" } };
Console.WriteLine($"중첩 컬렉션 초기화자    : {tags.Label} / [{string.Join(", ", tags.Tags)}]   ← Add 를 두 번 부른다");

var old = new Point { X = 5, Y = 5 };
var q = old;
try { q = new Point { X = 1, Y = Boom() }; }
catch (InvalidOperationException) { Console.WriteLine($"초기화자가 도중에 던지면  : q = {q}   ← 옛 객체가 그대로다(변수는 끝에 가서야 대입된다)"); }

static int Boom() => throw new InvalidOperationException("터진다");

class Point { public int X { get; set; } public int Y { get; set; } public override string ToString() => $"({X}, {Y})"; }
class Box {
    public string Label { get; set; } = "";
    public Point Inner { get; set; } = new Point();
    public List<string> Tags { get; } = new List<string>();
}
===== csc -out:ex.dll cs11b-objinit.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
객체 초기화자           : (1, 2)
중첩 초기화자(=  없음)  : 바깥 / (7, 8)   ← Inner 를 새로 만들지 않고 이미 있는 것을 고친다
중첩 초기화자(= 있음)   : 바깥2 / (9, 9)   ← 새로 만들어 갈아 끼운다
중첩 컬렉션 초기화자    : 리스트 / [a, b]   ← Add 를 두 번 부른다
초기화자가 도중에 던지면  : q = (5, 5)   ← 옛 객체가 그대로다(변수는 끝에 가서야 대입된다)
```

**IL**

```text
===== 소스: cs11b-il-init.cs =====
using System;
using System.Collections.Generic;

Il.Dump(typeof(P), "ObjInit");
Il.Dump(typeof(P), "Plain");
Il.Dump(typeof(P), "ColInit");
Il.Dump(typeof(P), "IdxInit");
Il.Dump(typeof(P), "PairInit");

class Pt { public int X { get; set; } public int Y { get; set; } }

static class P {
    public static Pt ObjInit() => new Pt { X = 1, Y = 2 };
    public static Pt Plain() { var p = new Pt(); p.X = 1; p.Y = 2; return p; }
    public static List<int> ColInit() => new List<int> { 1, 2 };
    public static Dictionary<string, int> IdxInit() => new Dictionary<string, int> { ["a"] = 1 };
    public static Dictionary<string, int> PairInit() => new Dictionary<string, int> { { "a", 1 } };
}
===== csc -r:il.dll -out:ex.dll cs11b-il-init.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
--- P.ObjInit ---
  IL_0000: newobj Pt::.ctor
  IL_0005: dup
  IL_0006: ldc.i4.1
  IL_0007: callvirt Pt::set_X
  IL_000c: nop
  IL_000d: dup
  IL_000e: ldc.i4.2
  IL_000f: callvirt Pt::set_Y
  IL_0014: nop
  IL_0015: ret
--- P.Plain ---
  .locals [0] Pt
  .locals [1] Pt
  IL_0000: nop
  IL_0001: newobj Pt::.ctor
  IL_0006: stloc.0
  IL_0007: ldloc.0
  IL_0008: ldc.i4.1
  IL_0009: callvirt Pt::set_X
  IL_000e: nop
  IL_000f: ldloc.0
  IL_0010: ldc.i4.2
  IL_0011: callvirt Pt::set_Y
  IL_0016: nop
  IL_0017: ldloc.0
  IL_0018: stloc.1
  IL_0019: br.s IL_001b
  IL_001b: ldloc.1
  IL_001c: ret
--- P.ColInit ---
  IL_0000: newobj System.Collections.Generic.List<System.Int32>::.ctor
  IL_0005: dup
  IL_0006: ldc.i4.1
  IL_0007: callvirt System.Collections.Generic.List<System.Int32>::Add
  IL_000c: nop
  IL_000d: dup
  IL_000e: ldc.i4.2
  IL_000f: callvirt System.Collections.Generic.List<System.Int32>::Add
  IL_0014: nop
  IL_0015: ret
--- P.IdxInit ---
  IL_0000: newobj System.Collections.Generic.Dictionary<System.String,System.Int32>::.ctor
  IL_0005: dup
  IL_0006: ldstr "a"
  IL_000b: ldc.i4.1
  IL_000c: callvirt System.Collections.Generic.Dictionary<System.String,System.Int32>::set_Item
  IL_0011: nop
  IL_0012: ret
--- P.PairInit ---
  IL_0000: newobj System.Collections.Generic.Dictionary<System.String,System.Int32>::.ctor
  IL_0005: dup
  IL_0006: ldstr "a"
  IL_000b: ldc.i4.1
  IL_000c: callvirt System.Collections.Generic.Dictionary<System.String,System.Int32>::Add
  IL_0011: nop
  IL_0012: ret
```

**왜 그런가**

```text
   Inner = { X = 7 }          get_Inner() 로 꺼내  ->  이미 있는 Point 를 고친다  -> (7, 8)
   Inner = new Point { X = 9 } 새 Point 를 만들어  ->  set_Inner() 로 갈아 끼운다 -> (9, 9)
```

- ★★★ **`Inner = { … }` 는 `Inner` 를 새로 만들지 않는다.** 그래서 **setter 가 없어도 된다** —\
  `Tags` 가 `{ get; }` 뿐인데 `Tags = { "a", "b" }` 가 도는 이유가 그것이다.
- ★ **`Tags = { "a", "b" }` 는 `Add` 를 두 번** 부른다 — 중첩 **컬렉션 초기화자**다.
- ★★ **`q` 는 `(5, 5)`, 즉 옛 객체 그대로**다. **객체를 다 만든 뒤에야 변수에 대입**하기 때문이다.
- ★★★ **IL 이 그 이유다** — 객체 초기화자는 `newobj` → **`dup`** → `set_X` → `dup` → `set_Y` → `ret` 로\
  **지역 변수를 한 번도 안 쓴다.** 손으로 쓴 `Plain()` 은 `stloc.0`/`ldloc.0` 을 쓴다.\
  ★ **스택 위에서 다 채운 뒤 마지막에 내놓는 것**이라 **도중에 던지면 대입 자체가 안 일어난다.**

### 2. ★★★ **에러 셋** — 그리고 `Add` 는 **확장 메서드여도 된다**

**출력 — 막히는 판**

```text
===== 소스: cs11b-add.cs =====
using System;
using System.Collections;
using System.Collections.Generic;

var a = new NoAdd { 1, 2 };
var b = new NoEnumerable { 1, 2 };
Console.WriteLine($"{a} {b}");

class NoAdd : IEnumerable {
    public IEnumerator GetEnumerator() => new List<int>().GetEnumerator();
}
class NoEnumerable {
    public void Add(int x) { }
}
===== csc -out:ex.dll cs11b-add.cs (cc exit=1) =====
cs11b-add.cs(5,21): error CS1061: 'NoAdd' does not contain a definition for 'Add' and no accessible extension method 'Add' accepting a first argument of type 'NoAdd' could be found (are you missing a using directive or an assembly reference?)
cs11b-add.cs(5,24): error CS1061: 'NoAdd' does not contain a definition for 'Add' and no accessible extension method 'Add' accepting a first argument of type 'NoAdd' could be found (are you missing a using directive or an assembly reference?)
cs11b-add.cs(6,26): error CS1922: Cannot initialize type 'NoEnumerable' with a collection initializer because it does not implement 'System.Collections.IEnumerable'
```

**출력 — 통과하는 판**

```text
===== 소스: cs11b-add-ok.cs =====
using System;
using System.Collections;
using System.Collections.Generic;

var seen = new Seen { 1, 2, 3 };
Console.WriteLine($"확장 메서드 Add 로도 컬렉션 초기화자가 성립한다 : 합 = {seen.Sum}");

var two = new TwoArg { { "a", 1 }, { "b", 2 } };
Console.WriteLine($"{{ x, y }} 꼴은 인자 둘짜리 Add 를 찾는다       : {two.Log}");

class Seen : IEnumerable {
    public int Sum;
    public IEnumerator GetEnumerator() => new List<int>().GetEnumerator();
}
static class SeenExt { public static void Add(this Seen s, int x) => s.Sum += x; }

class TwoArg : IEnumerable {
    public string Log = "";
    public void Add(string k, int v) => Log += $"Add({k},{v}) ";
    public IEnumerator GetEnumerator() => new List<int>().GetEnumerator();
}
===== csc -out:ex.dll cs11b-add-ok.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
확장 메서드 Add 로도 컬렉션 초기화자가 성립한다 : 합 = 6
{ x, y } 꼴은 인자 둘짜리 Add 를 찾는다       : Add(a,1) Add(b,2) 
```

**왜 그런가**

| 빠진 것 | 진단 | 어디에 |
|---|---|---|
| `Add` 가 없다 | `CS1061` | ★ **원소마다 하나씩** — `(5,21)` 과 `(5,24)` |
| `IEnumerable` 이 아니다 | `CS1922` | `(6,26)` — **초기화자 전체에 하나** |

- ★★★ **조건이 둘이고 에러 코드가 다르다.** `IEnumerable` 구현과 `Add`, **둘 다** 있어야 한다.
- ★★ **`NoAdd` 쪽이 두 건인 이유** — `{ 1, 2 }` 의 **`1` 자리와 `2` 자리**에서 각각 `Add` 를 찾다 실패한다.\
  열이 21 과 24 로 **원소 위치를 정확히 가리킨다.**
- ★★★ **`Add` 는 확장 메서드여도 된다.** `Seen` 에는 `Add` 가 없는데 `new Seen { 1, 2, 3 }` 이 돌았고 **합이 6**이다.\
  ★ 진단 문구가 이미 그렇게 적고 있었다 — `no accessible extension method 'Add' … could be found`.
- ★ **`{ x, y }` 꼴은 인자 둘짜리 `Add`** 를 찾는다(`Add(a,1) Add(b,2)`).\
  **`Dictionary` 의 `{ "a", 1 }` 이 특별한 문법이 아니라 이 규칙 하나**다.
- ★ **`GetEnumerator` 가 쓸모 있을 필요는 없다** — 두 예제 다 **빈 리스트의 열거자**를 돌려준다.

### 3. ★ 앞은 **던지고** 뒤는 **덮는다** — 그리고 `Capacity` 가 **4 대 3**

**출력**

```text
===== 소스: cs11b-idx.cs =====
using System;
using System.Collections.Generic;

try {
    var d1 = new Dictionary<string, int> { { "a", 1 }, { "a", 2 } };
    Console.WriteLine("Add 꼴  { \"a\", 1 }, { \"a\", 2 }  → 통과했다. 값 = " + d1["a"]);
} catch (ArgumentException ex) {
    Console.WriteLine("Add 꼴  { \"a\", 1 }, { \"a\", 2 }  → " + ex.GetType().Name + ": " + ex.Message);
}

var d2 = new Dictionary<string, int> { ["a"] = 1, ["a"] = 2 };
Console.WriteLine("인덱스 꼴 [\"a\"] = 1, [\"a\"] = 2  → 통과. 값 = " + d2["a"] + ", Count = " + d2.Count);
Console.WriteLine();

var grid = new Grid { [0] = "영", [2] = "둘" };
Console.WriteLine("인덱스 초기화자는 내 타입에도 붙는다 : " + grid.Log);
Console.WriteLine();

var byAdd = new List<int> { 1, 2, 3 };
var byExpr = new List<int>();
Console.WriteLine("컬렉션 초기화자는 Add 를 부르므로 List 의 Capacity 가 " + byAdd.Capacity + " 다");
List<int> byColl = [1, 2, 3];
Console.WriteLine("컬렉션 식은 개수를 미리 알아 Capacity 가 " + byColl.Capacity + " 다");
Console.WriteLine("  같은 세 값인데 빈 자리가 " + (byAdd.Capacity - byAdd.Count) + " 대 " + (byColl.Capacity - byColl.Count) + " 로 다르다");
GC.KeepAlive(byExpr);

class Grid {
    public string Log = "";
    public string this[int i] { get => Log; set => Log += $"set_Item({i}, {value}) "; }
}
===== csc -out:ex.dll cs11b-idx.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
Add 꼴  { "a", 1 }, { "a", 2 }  → ArgumentException: An item with the same key has already been added. Key: a
인덱스 꼴 ["a"] = 1, ["a"] = 2  → 통과. 값 = 2, Count = 1

인덱스 초기화자는 내 타입에도 붙는다 : set_Item(0, 영) set_Item(2, 둘) 

컬렉션 초기화자는 Add 를 부르므로 List 의 Capacity 가 4 다
컬렉션 식은 개수를 미리 알아 Capacity 가 3 다
  같은 세 값인데 빈 자리가 1 대 0 로 다르다
```

**왜 그런가**

| 꼴 | 부르는 것 | 중복 키에서 |
|---|---|---|
| `{ "a", 1 }, { "a", 2 }` | `Add(k, v)` | ★★★ **`ArgumentException`** — `An item with the same key has already been added. Key: a` |
| `["a"] = 1, ["a"] = 2` | `set_Item(k, v)` | ★★ **덮어쓴다** — 값 2 · `Count` **1** |

- ★★★ **같은 뜻처럼 보이는 두 꼴이 중복 키에서 갈린다.** 하나는 던지고 하나는 **조용히 덮는다.**\
  ★ [10번](../10-collection-choosing-list-dictionary-hashset-queue-stack/)의 「넣는 법 셋」 중 **앞의 둘**이 그대로 문법 두 꼴이 된 것이다.
- ★★ **인덱스 초기화자는 내 타입에도 붙는다** — 인덱서만 있으면 `set_Item(0, 영) set_Item(2, 둘)` 이 돈다.
- ★★★ **`Capacity` 가 4 대 3 이다.**\
  `new List<int> { 1, 2, 3 }` 은 `Add` 를 세 번 부르며 **1 → 2 → 4** 로 늘린 자국이고,\
  `List<int> x = [1, 2, 3]` 은 **개수를 미리 알아 정확히 3**을 잡는다(4번의 IL 이 그 이유다).

### 4. ★★★ 넷이 전부 다른 것을 만든다 — `List` 는 `Add` 를 **한 번도** 안 부른다

**출력**

```text
===== 소스: cs11b-expr.cs =====
using System;
using System.Collections.Generic;

int[] other = [30, 40];
int[] a = [10, 20, ..other, 50];
Console.WriteLine($"int[] a = [10, 20, ..other, 50]  →  [{string.Join(", ", a)}]");

List<int> l = [1, ..a, 99];
Console.WriteLine($"List<int> l = [1, ..a, 99]       →  [{string.Join(", ", l)}]  Count={l.Count}");

Span<int> s = [7, 8, 9];
Console.WriteLine($"Span<int> s = [7, 8, 9]          →  [{string.Join(", ", s.ToArray())}]  Length={s.Length}");

IEnumerable<int> e = [1, 2, 3];
Console.WriteLine($"IEnumerable<int> e = [1, 2, 3]   →  런타임 타입 {e.GetType().Name}");

int[] empty = [];
Console.WriteLine($"int[] empty = []                 →  Length={empty.Length}  Array.Empty 와 같은 객체 = {ReferenceEquals(empty, Array.Empty<int>())}");

string[] words = ["하나", "둘"];
string[] more = [..words, "셋"];
Console.WriteLine($"[..words, \"셋\"]                   →  [{string.Join(", ", more)}]");

List<int> src = [1, 2, 3];
int[] fromList = [..src];
Console.WriteLine($"[..src] 에서 src 가 List 여도     →  int[] {{{string.Join(", ", fromList)}}}");

int[] nested = [..(int[])[1, 2], ..(List<int>)[3, 4]];
Console.WriteLine($"서로 다른 컬렉션을 한 줄에 퍼뜨리면 →  [{string.Join(", ", nested)}]");
===== csc -out:ex.dll cs11b-expr.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
int[] a = [10, 20, ..other, 50]  →  [10, 20, 30, 40, 50]
List<int> l = [1, ..a, 99]       →  [1, 10, 20, 30, 40, 50, 99]  Count=7
Span<int> s = [7, 8, 9]          →  [7, 8, 9]  Length=3
IEnumerable<int> e = [1, 2, 3]   →  런타임 타입 <>z__ReadOnlyArray`1
int[] empty = []                 →  Length=0  Array.Empty 와 같은 객체 = True
[..words, "셋"]                   →  [하나, 둘, 셋]
[..src] 에서 src 가 List 여도     →  int[] {1, 2, 3}
서로 다른 컬렉션을 한 줄에 퍼뜨리면 →  [1, 2, 3, 4]
```

**IL**

```text
===== 소스: cs11b-il-expr.cs =====
using System;
using System.Collections.Generic;

Il.Dump(typeof(P), "ConstArr");
Il.Dump(typeof(P), "VarArr");
Il.Dump(typeof(P), "Lst");
Il.Dump(typeof(P), "Spn");
Il.Dump(typeof(P), "Ros");
Il.Dump(typeof(P), "Spread");
Il.Dump(typeof(P), "EmptyArr");
Il.Dump(typeof(P), "Iface");

static class P {
    public static int[] ConstArr() => [1, 2, 3];
    public static int[] VarArr(int a, int b, int c) => [a, b, c];
    public static List<int> Lst() => [1, 2, 3];
    public static int Spn() { Span<int> s = [1, 2, 3]; return s[0]; }
    public static int Ros() { ReadOnlySpan<int> s = [1, 2, 3]; return s[0]; }
    public static int[] Spread(int[] o) => [1, 2, ..o];
    public static int[] EmptyArr() => [];
    public static IEnumerable<int> Iface() => [1, 2, 3];
}
===== csc -r:il.dll -out:ex.dll cs11b-il-expr.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
--- P.ConstArr ---
  IL_0000: ldc.i4.3
  IL_0001: newarr System.Int32
  IL_0006: dup
  IL_0007: ldtoken <PrivateImplementationDetails>::4636993D3E1DA4E9D6B8F87B79E8F7C6D018580D52661950EABC3845C5897A4D
  IL_000c: call System.Runtime.CompilerServices.RuntimeHelpers::InitializeArray
  IL_0011: ret
--- P.VarArr ---
  IL_0000: ldc.i4.3
  IL_0001: newarr System.Int32
  IL_0006: dup
  IL_0007: ldc.i4.0
  IL_0008: ldarg.0
  IL_0009: stelem.i4
  IL_000a: dup
  IL_000b: ldc.i4.1
  IL_000c: ldarg.1
  IL_000d: stelem.i4
  IL_000e: dup
  IL_000f: ldc.i4.2
  IL_0010: ldarg.2
  IL_0011: stelem.i4
  IL_0012: ret
--- P.Lst ---
  .locals [0] System.Int32
  .locals [1] System.Span<System.Int32>
  IL_0000: ldc.i4.3
  IL_0001: stloc.0
  IL_0002: ldloc.0
  IL_0003: newobj System.Collections.Generic.List<System.Int32>::.ctor
  IL_0008: dup
  IL_0009: ldloc.0
  IL_000a: call System.Runtime.InteropServices.CollectionsMarshal::SetCount
  IL_000f: nop
  IL_0010: dup
  IL_0011: call System.Runtime.InteropServices.CollectionsMarshal::AsSpan
  IL_0016: stloc.1
  IL_0017: ldloca.s 1
  IL_0019: ldc.i4.0
  IL_001a: call System.Span<System.Int32>::get_Item
  IL_001f: ldc.i4.1
  IL_0020: stind.i4
  IL_0021: ldloca.s 1
  IL_0023: ldc.i4.1
  IL_0024: call System.Span<System.Int32>::get_Item
  IL_0029: ldc.i4.2
  IL_002a: stind.i4
  IL_002b: ldloca.s 1
  IL_002d: ldc.i4.2
  IL_002e: call System.Span<System.Int32>::get_Item
  IL_0033: ldc.i4.3
  IL_0034: stind.i4
  IL_0035: ret
--- P.Spn ---
  .locals [0] System.Span<System.Int32>
  .locals [1] System.Runtime.CompilerServices.InlineArray3<System.Int32>
  .locals [2] System.Int32
  IL_0000: nop
  IL_0001: ldloca.s 1
  IL_0003: initobj System.Runtime.CompilerServices.InlineArray3<System.Int32>
  IL_0009: ldloca.s 1
  IL_000b: ldc.i4.0
  IL_000c: call <PrivateImplementationDetails>::InlineArrayElementRef
  IL_0011: ldc.i4.1
  IL_0012: stind.i4
  IL_0013: ldloca.s 1
  IL_0015: ldc.i4.1
  IL_0016: call <PrivateImplementationDetails>::InlineArrayElementRef
  IL_001b: ldc.i4.2
  IL_001c: stind.i4
  IL_001d: ldloca.s 1
  IL_001f: ldc.i4.2
  IL_0020: call <PrivateImplementationDetails>::InlineArrayElementRef
  IL_0025: ldc.i4.3
  IL_0026: stind.i4
  IL_0027: ldloca.s 1
  IL_0029: ldc.i4.3
  IL_002a: call <PrivateImplementationDetails>::InlineArrayAsSpan
  IL_002f: stloc.0
  IL_0030: ldloca.s 0
  IL_0032: ldc.i4.0
  IL_0033: call System.Span<System.Int32>::get_Item
  IL_0038: ldind.i4
  IL_0039: stloc.2
  IL_003a: br.s IL_003c
  IL_003c: ldloc.2
  IL_003d: ret
--- P.Ros ---
  .locals [0] System.ReadOnlySpan<System.Int32>
  .locals [1] System.Int32
  IL_0000: nop
  IL_0001: ldtoken <PrivateImplementationDetails>::4636993D3E1DA4E9D6B8F87B79E8F7C6D018580D52661950EABC3845C5897A4D4
  IL_0006: call System.Runtime.CompilerServices.RuntimeHelpers::CreateSpan
  IL_000b: stloc.0
  IL_000c: ldloca.s 0
  IL_000e: ldc.i4.0
  IL_000f: call System.ReadOnlySpan<System.Int32>::get_Item
  IL_0014: ldind.i4
  IL_0015: stloc.1
  IL_0016: br.s IL_0018
  IL_0018: ldloc.1
  IL_0019: ret
--- P.Spread ---
  .locals [0] System.Int32
  .locals [1] System.Int32
  .locals [2] System.Int32[]
  .locals [3] System.Int32
  .locals [4] System.Int32[]
  .locals [5] System.ReadOnlySpan<System.Int32>
  .locals [6] System.Span<System.Int32>
  IL_0000: ldc.i4.1
  IL_0001: stloc.0
  IL_0002: ldc.i4.2
  IL_0003: stloc.1
  IL_0004: ldarg.0
  IL_0005: stloc.2
  IL_0006: ldc.i4.0
  IL_0007: stloc.3
  IL_0008: ldc.i4.2
  IL_0009: ldloc.2
  IL_000a: ldlen
  IL_000b: conv.i4
  IL_000c: add
  IL_000d: newarr System.Int32
  IL_0012: stloc.s 4
  IL_0014: ldloc.s 4
  IL_0016: ldloc.3
  IL_0017: ldloc.0
  IL_0018: stelem.i4
  IL_0019: ldloc.3
  IL_001a: ldc.i4.1
  IL_001b: add
  IL_001c: stloc.3
  IL_001d: ldloc.s 4
  IL_001f: ldloc.3
  IL_0020: ldloc.1
  IL_0021: stelem.i4
  IL_0022: ldloc.3
  IL_0023: ldc.i4.1
  IL_0024: add
  IL_0025: stloc.3
  IL_0026: ldloca.s 5
  IL_0028: ldloc.2
  IL_0029: call System.ReadOnlySpan<System.Int32>::.ctor
  IL_002e: ldloca.s 5
  IL_0030: ldloc.s 4
  IL_0032: newobj System.Span<System.Int32>::.ctor
  IL_0037: stloc.s 6
  IL_0039: ldloca.s 6
  IL_003b: ldloc.3
  IL_003c: ldloca.s 5
  IL_003e: call System.ReadOnlySpan<System.Int32>::get_Length
  IL_0043: call System.Span<System.Int32>::Slice
  IL_0048: call System.ReadOnlySpan<System.Int32>::CopyTo
  IL_004d: nop
  IL_004e: ldloc.3
  IL_004f: ldloca.s 5
  IL_0051: call System.ReadOnlySpan<System.Int32>::get_Length
  IL_0056: add
  IL_0057: stloc.3
  IL_0058: ldloc.s 4
  IL_005a: ret
--- P.EmptyArr ---
  IL_0000: call System.Array::Empty
  IL_0005: ret
--- P.Iface ---
  IL_0000: ldc.i4.3
  IL_0001: newarr System.Int32
  IL_0006: dup
  IL_0007: ldtoken <PrivateImplementationDetails>::4636993D3E1DA4E9D6B8F87B79E8F7C6D018580D52661950EABC3845C5897A4D
  IL_000c: call System.Runtime.CompilerServices.RuntimeHelpers::InitializeArray
  IL_0011: newobj <>z__ReadOnlyArray<System.Int32>::.ctor
  IL_0016: ret
```

**왜 그런가**

- ★★★ **`IEnumerable<int> e = [1, 2, 3]` 의 런타임 타입은 `<>z__ReadOnlyArray'1`** 이다 —\
  배열도 리스트도 아닌 **컴파일러가 만든 읽기 전용 감싸개**다. **인터페이스로 받으면 고칠 수 없게 잠가 준다.**
- ★★★ **`int[] empty = []` 은 `Array.Empty<int>()` 와 같은 객체**다(`True`). IL 도 `call System.Array::Empty` 한 줄뿐이다.
- ★ **`[..src]` 에서 `src` 가 `List<int>` 여도 왼쪽이 `int[]` 면 `int[]`** 이 나온다 — **스프레드는 타입을 안 가린다.**
- ★★★ **`List<int> x = [1, 2, 3]` 은 `Add` 를 0번 부른다.**\
  `List..ctor(int)` → **`CollectionsMarshal::SetCount`** → `AsSpan` → **칸에 직접 쓰기**다.\
  ★ 3번의 `Capacity` 3 이 여기서 나온다.
- ★★★ **`Span<int> s = [1, 2, 3]` 의 IL 에 `newarr` 이 없다.**\
  `InlineArray3<int>` 라는 **지역 변수**를 `initobj` 로 만들고, `InlineArrayElementRef` 로 칸에 쓰고,\
  `InlineArrayAsSpan` 으로 span 을 얻는다 — **힙을 한 바이트도 안 쓴다**(5번).
- ★ **스프레드는 `Add` 가 아니라 `CopyTo`** 다 — 길이를 `2 + o.Length` 로 **먼저 계산해 배열 하나만** 만든다.

### 5. ★★★ 0 · 40 · 72 · 112 · 136 — 그리고 **빈 것 중 `List` 만** 32다

**출력**

```text
===== 소스: cs11b-alloc.cs =====
using System;
using System.Collections.Generic;
using System.Collections.Immutable;
using System.Runtime.CompilerServices;

class P {
    [MethodImpl(MethodImplOptions.NoInlining)] static int[] Arr() => [1, 2, 3];
    [MethodImpl(MethodImplOptions.NoInlining)] static int[] ArrVar(int a, int b, int c) => [a, b, c];
    [MethodImpl(MethodImplOptions.NoInlining)] static List<int> Lst() => [1, 2, 3];
    [MethodImpl(MethodImplOptions.NoInlining)] static List<int> LstOld() => new List<int> { 1, 2, 3 };
    [MethodImpl(MethodImplOptions.NoInlining)] static int Spn() { Span<int> s = [1, 2, 3]; return s[0] + s[1] + s[2]; }
    [MethodImpl(MethodImplOptions.NoInlining)] static int Ros() { ReadOnlySpan<int> s = [1, 2, 3]; return s[0] + s[1] + s[2]; }
    [MethodImpl(MethodImplOptions.NoInlining)] static IEnumerable<int> Iface() => [1, 2, 3];
    [MethodImpl(MethodImplOptions.NoInlining)] static int Imm() { ImmutableArray<int> a = [1, 2, 3]; return a[0] + a[1] + a[2]; }
    [MethodImpl(MethodImplOptions.NoInlining)] static int[] Spread(int[] o) => [1, 2, ..o];
    [MethodImpl(MethodImplOptions.NoInlining)] static int[] EmptyArr() => [];
    [MethodImpl(MethodImplOptions.NoInlining)] static List<int> EmptyLst() => [];
    [MethodImpl(MethodImplOptions.NoInlining)] static IEnumerable<int> EmptyIface() => [];
    [MethodImpl(MethodImplOptions.NoInlining)] static int EmptySpn() { Span<int> s = []; return s.Length; }

    static long Measure(Action f) {
        for (int i = 0; i < 10; i++) f();
        long b0 = GC.GetAllocatedBytesForCurrentThread();
        for (int i = 0; i < 100; i++) f();
        long b1 = GC.GetAllocatedBytesForCurrentThread();
        return (b1 - b0) / 100;
    }

    static void Main() {
        int[] o = [4, 5];
        int acc = 0;
        Console.WriteLine($"int[]             x = [1, 2, 3] : {Measure(() => GC.KeepAlive(Arr()))} 바이트/회");
        Console.WriteLine($"int[]             x = [a, b, c] : {Measure(() => GC.KeepAlive(ArrVar(1, 2, 3)))} 바이트/회   ★ 같은 모양인데 다르다");
        Console.WriteLine($"List<int>         x = [1, 2, 3] : {Measure(() => GC.KeepAlive(Lst()))} 바이트/회");
        Console.WriteLine($"new List<int> {{ 1, 2, 3 }}       : {Measure(() => GC.KeepAlive(LstOld()))} 바이트/회");
        Console.WriteLine($"Span<int>         x = [1, 2, 3] : {Measure(() => acc += Spn())} 바이트/회   ★ 스택에 담는다");
        Console.WriteLine($"ReadOnlySpan<int> x = [1, 2, 3] : {Measure(() => acc += Ros())} 바이트/회   ★ 배열이 없는데도 낸다");
        Console.WriteLine($"IEnumerable<int>  x = [1, 2, 3] : {Measure(() => GC.KeepAlive(Iface()))} 바이트/회");
        Console.WriteLine($"ImmutableArray<int> x=[1, 2, 3] : {Measure(() => acc += Imm())} 바이트/회");
        Console.WriteLine($"int[]  x = [1, 2, ..other]      : {Measure(() => GC.KeepAlive(Spread(o)))} 바이트/회");
        Console.WriteLine();
        Console.WriteLine($"int[]             x = []        : {Measure(() => GC.KeepAlive(EmptyArr()))} 바이트/회");
        Console.WriteLine($"IEnumerable<int>  x = []        : {Measure(() => GC.KeepAlive(EmptyIface()))} 바이트/회");
        Console.WriteLine($"Span<int>         x = []        : {Measure(() => acc += EmptySpn())} 바이트/회");
        Console.WriteLine($"List<int>         x = []        : {Measure(() => GC.KeepAlive(EmptyLst()))} 바이트/회   ★ 여기만 0 이 아니다");
        Console.WriteLine();
        Console.WriteLine($"런타임 타입 — IEnumerable<int> x = [1,2,3] 은 {Iface().GetType().Name}");
        Console.WriteLine($"런타임 타입 — IEnumerable<int> x = []      은 {EmptyIface().GetType().Name}");
        Console.WriteLine($"List<int> x = [1,2,3] 의 Capacity = {Lst().Capacity} · new List<int>{{1,2,3}} 의 Capacity = {LstOld().Capacity}");
        Console.WriteLine($"int[] x = [] 은 Array.Empty 와 같은 객체 = {ReferenceEquals(EmptyArr(), Array.Empty<int>())}   (acc={acc % 2})");
    }
}
===== csc -out:ex.dll cs11b-alloc.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
int[]             x = [1, 2, 3] : 112 바이트/회
int[]             x = [a, b, c] : 40 바이트/회   ★ 같은 모양인데 다르다
List<int>         x = [1, 2, 3] : 72 바이트/회
new List<int> { 1, 2, 3 }       : 72 바이트/회
Span<int>         x = [1, 2, 3] : 0 바이트/회   ★ 스택에 담는다
ReadOnlySpan<int> x = [1, 2, 3] : 72 바이트/회   ★ 배열이 없는데도 낸다
IEnumerable<int>  x = [1, 2, 3] : 136 바이트/회
ImmutableArray<int> x=[1, 2, 3] : 112 바이트/회
int[]  x = [1, 2, ..other]      : 40 바이트/회

int[]             x = []        : 0 바이트/회
IEnumerable<int>  x = []        : 0 바이트/회
Span<int>         x = []        : 0 바이트/회
List<int>         x = []        : 32 바이트/회   ★ 여기만 0 이 아니다

런타임 타입 — IEnumerable<int> x = [1,2,3] 은 <>z__ReadOnlyArray`1
런타임 타입 — IEnumerable<int> x = []      은 Int32[]
List<int> x = [1,2,3] 의 Capacity = 3 · new List<int>{1,2,3} 의 Capacity = 4
int[] x = [] 은 Array.Empty 와 같은 객체 = True   (acc=0)
```

**왜 그런가**

| 대상 타입 | 바이트/회 | 읽는 법 |
|---|---|---|
| `Span<int> x = [1, 2, 3]` | ★★★ **0** | `InlineArray3` — 힙을 안 쓴다 |
| `int[] x = []` · `IEnumerable<int> x = []` · `Span<int> x = []` | ★★★ **0** | `Array.Empty` 재사용 |
| `int[] x = [a, b, c]` | **40** | 배열 하나 |
| `int[] x = [1, 2, ..other]` | **40** | ★★ **스프레드도 배열 하나** — 중간 리스트가 없다 |
| `List<int> x = [1, 2, 3]` · `new List<int> { 1, 2, 3 }` | **72** | ★ **둘이 같다** — 객체 32 + 배열 40 |
| `List<int> x = []` | ★★★ **32** | ★★★ **빈 것 중 여기만 0이 아니다** |
| `ReadOnlySpan<int> x = [1, 2, 3]` | **72** | ★★ **배열이 없는데도 낸다**(6번) |
| `int[] x = [1, 2, 3]`(상수) | **112** | ★★★ **배열 40 + 72** |
| `IEnumerable<int> x = [1, 2, 3]` | **136** | 배열 40 + 72 + 감싸개 24 |
| `ImmutableArray<int> x = [1, 2, 3]` | 112 | 배열 경로와 같다 |

- ★★★ **큰 쪽은 상수 판(112)이고, 차이는 72다.** **같은 모양인데 상수가 더 비싸다** — 6번에서 그 72 를 가른다.\
  ★★ **그리고 그 칸은 판을 탄다**(9번). **절댓값을 판 없이 인용하면 안 된다.**
- ★★★ **빈 것 네 줄 중 `List<int> x = []` 만 32**다. **빈 `List` 객체 자체는 만들어야 하기** 때문이다.
- ★ **스프레드는 중간 리스트를 안 만든다** — 40바이트로 `[a, b, c]` 와 같다.
- ★ **`List` 두 꼴의 바이트가 같다** — 갈리는 것은 **`Capacity` 와 `Add` 호출 유무**뿐이다(3번·4번).

### 6. ★★ `byte` 는 **0**, `int` 는 **72** — `ldsflda` 대 `ldtoken` 이다

**출력 — 바이트**

```text
===== 소스: cs11b-blob.cs =====
using System;
using System.Runtime.CompilerServices;

class P {
    [MethodImpl(MethodImplOptions.NoInlining)] static int RosByte() { ReadOnlySpan<byte> s = [1, 2, 3]; return s[0] + s[1] + s[2]; }
    [MethodImpl(MethodImplOptions.NoInlining)] static int RosInt() { ReadOnlySpan<int> s = [1, 2, 3]; return s[0] + s[1] + s[2]; }
    [MethodImpl(MethodImplOptions.NoInlining)] static int ArrByte() { byte[] s = [1, 2, 3]; return s[0] + s[1] + s[2]; }
    [MethodImpl(MethodImplOptions.NoInlining)] static int ArrInt() { int[] s = [1, 2, 3]; return s[0] + s[1] + s[2]; }
    [MethodImpl(MethodImplOptions.NoInlining)] static int NewByte() { byte[] s = new byte[3]; return s.Length; }
    [MethodImpl(MethodImplOptions.NoInlining)] static int NewInt() { int[] s = new int[3]; return s.Length; }

    static long Measure(Func<int> f) {
        for (int i = 0; i < 10; i++) f();
        long b0 = GC.GetAllocatedBytesForCurrentThread();
        for (int i = 0; i < 100; i++) f();
        long b1 = GC.GetAllocatedBytesForCurrentThread();
        return (b1 - b0) / 100;
    }

    static void Main() {
        long rb = Measure(RosByte), ri = Measure(RosInt);
        long ab = Measure(ArrByte), ai = Measure(ArrInt);
        long nb = Measure(NewByte), ni = Measure(NewInt);
        Console.WriteLine($"new byte[3]                    : {nb,4} 바이트/회   ← 배열 자체의 값");
        Console.WriteLine($"new int[3]                     : {ni,4} 바이트/회   ← 배열 자체의 값");
        Console.WriteLine($"byte[] x = [1, 2, 3]           : {ab,4} 바이트/회   (배열 {nb} + {ab - nb})");
        Console.WriteLine($"int[]  x = [1, 2, 3]           : {ai,4} 바이트/회   (배열 {ni} + {ai - ni})");
        Console.WriteLine($"ReadOnlySpan<byte> x = [1,2,3] : {rb,4} 바이트/회   ← 배열이 없다");
        Console.WriteLine($"ReadOnlySpan<int>  x = [1,2,3] : {ri,4} 바이트/회   ← 배열이 없는데도 낸다");
        Console.WriteLine();
        Console.WriteLine($"★ 배열 값을 뺀 나머지가 상수 블록 경로의 몫이다 — byte {ab - nb} · int {ai - ni} · ROSpan<byte> {rb} · ROSpan<int> {ri}");
    }
}
===== csc -out:ex.dll cs11b-blob.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
new byte[3]                    :   32 바이트/회   ← 배열 자체의 값
new int[3]                     :   40 바이트/회   ← 배열 자체의 값
byte[] x = [1, 2, 3]           :  104 바이트/회   (배열 32 + 72)
int[]  x = [1, 2, 3]           :  112 바이트/회   (배열 40 + 72)
ReadOnlySpan<byte> x = [1,2,3] :    0 바이트/회   ← 배열이 없다
ReadOnlySpan<int>  x = [1,2,3] :   72 바이트/회   ← 배열이 없는데도 낸다

★ 배열 값을 뺀 나머지가 상수 블록 경로의 몫이다 — byte 72 · int 72 · ROSpan<byte> 0 · ROSpan<int> 72
```

**출력 — IL**

```text
===== 소스: cs11b-il-blob.cs =====
using System;

Il.Dump(typeof(P), "RosByte");
Il.Dump(typeof(P), "RosInt");

static class P {
    public static int RosByte() { ReadOnlySpan<byte> s = [1, 2, 3]; return s[0]; }
    public static int RosInt()  { ReadOnlySpan<int>  s = [1, 2, 3]; return s[0]; }
}
===== csc -r:il.dll -out:ex.dll cs11b-il-blob.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
--- P.RosByte ---
  .locals [0] System.ReadOnlySpan<System.Byte>
  .locals [1] System.Int32
  IL_0000: nop
  IL_0001: ldloca.s 0
  IL_0003: ldsflda <PrivateImplementationDetails>::039058C6F2C0CB492C533B0A4D14EF77CC0F78ABCCCED5287D84A1A2011CFB81
  IL_0008: ldc.i4.3
  IL_0009: call System.ReadOnlySpan<System.Byte>::.ctor
  IL_000e: ldloca.s 0
  IL_0010: ldc.i4.0
  IL_0011: call System.ReadOnlySpan<System.Byte>::get_Item
  IL_0016: ldind.u1
  IL_0017: stloc.1
  IL_0018: br.s IL_001a
  IL_001a: ldloc.1
  IL_001b: ret
--- P.RosInt ---
  .locals [0] System.ReadOnlySpan<System.Int32>
  .locals [1] System.Int32
  IL_0000: nop
  IL_0001: ldtoken <PrivateImplementationDetails>::4636993D3E1DA4E9D6B8F87B79E8F7C6D018580D52661950EABC3845C5897A4D4
  IL_0006: call System.Runtime.CompilerServices.RuntimeHelpers::CreateSpan
  IL_000b: stloc.0
  IL_000c: ldloca.s 0
  IL_000e: ldc.i4.0
  IL_000f: call System.ReadOnlySpan<System.Int32>::get_Item
  IL_0014: ldind.i4
  IL_0015: stloc.1
  IL_0016: br.s IL_0018
  IL_0018: ldloc.1
  IL_0019: ret
```

**왜 그런가**

```text
   ReadOnlySpan<byte> s = [1, 2, 3];     ldsflda <데이터 필드>   -> 주소를 바로 준다  -> 0바이트
   ReadOnlySpan<int>  s = [1, 2, 3];     ldtoken <데이터 필드>
                                         call RuntimeHelpers::CreateSpan            -> ★ 72바이트
```

- ★★★ **둘 다 배열을 안 만드는데 바이트가 갈린다** — `byte` 0 · `int` 72.
- ★★★ **IL 의 첫 명령 하나가 이유다** — `byte` 쪽은 **`ldsflda`**(정적 필드의 주소), `int` 쪽은 **`ldtoken`** 이다.\
  ★ **1바이트 원소는 바이트 순서 문제가 없어 데이터 블록을 그대로 가리킬 수 있고**,\
  `int` 는 그럴 수 없어 **런타임에 물어봐야** 한다. 그 `ldtoken` 이 **런타임 핸들 객체 72바이트**를 만든다.
- ★★ **`byte[] x = [1, 2, 3]` 도 배열 32 + 72** 다 — **배열을 만드는 경로는 `byte` 여도 `ldtoken`** 을 쓴다.\
  `int[]` 는 40 + 72 다. **나머지 72 가 둘이 같다.**
- ★ 그래서 `+72` 는 「상수 블록을 쓰는 값」이 아니라 **「`ldtoken` 이 핸들을 만드는 값」이고**,\
  JIT 이 최적화 단계에 이르면 **사라진다**(9번).

### 7. ★ 셋 다 막힌다 — `CS9176` 둘 · `CS9174` 하나

**출력**

```text
===== 소스: cs11b-target.cs =====
using System;
using System.Collections.Generic;

var x = [];
var y = [1, 2, 3];
object o = [1, 2, 3];
Console.WriteLine($"{x} {y} {o}");
===== csc -out:ex.dll cs11b-target.cs (cc exit=1) =====
cs11b-target.cs(4,9): error CS9176: There is no target type for the collection expression.
cs11b-target.cs(5,9): error CS9176: There is no target type for the collection expression.
cs11b-target.cs(6,12): error CS9174: Cannot initialize type 'object' with a collection expression because the type is not constructible.
```

**왜 그런가**

| 코드 | 진단 | 뜻 |
|---|---|---|
| `var x = [];` | `CS9176` | 대상 타입이 없다 |
| `var y = [1, 2, 3];` | `CS9176` | ★ **원소가 있어도 마찬가지** — 추론하지 않는다 |
| `object o = [1, 2, 3];` | `CS9174` | ★★ `the type is not constructible` |

- ★★★ **컬렉션 식은 스스로 타입을 정하지 않는다.** `var` 는 **오른쪽에서** 타입을 받고 컬렉션 식은 **왼쪽에서** 받으니\
  **서로 기다리다 끝난다.** [04번](../04-var-and-target-typed-new/)의 타겟 타입 `new` 와 **같은 이유**다.
- ★★ **코드가 둘로 갈린다** — **대상 타입이 아예 없는 것**(`CS9176`)과 **있는데 만들 수 없는 것**(`CS9174`).\
  **뒤쪽 문구가 이 문법의 한 줄 요약**이다 — 「**만들 수 있는 타입에만 붙는다**」.
- ★ **그래서 컬렉션 식은 런타임에 실패하지 않는다** — **대상 타입이 안 맞으면 전부 컴파일 에러**이기 때문이다.\
  ★ 이것이 이 주제에서 **「예외 전문」이 부적용인 창**인 이유다.

### 8. ★★ 같은 에러 · 열만 **16 대 15** — 값으로는 못 가른다

**출력**

```text
===== 소스: cs11b-prec.cs =====
using System;

int[] a = [10, 20, 30, 40];
int[] r1 = [.. 1..3];
int[] r2 = [..(1..3)];
int[] r3 = [.. a[1..3]];
Console.WriteLine(r1.Length + r2.Length + r3.Length);
===== csc -out:ex.dll cs11b-prec.cs (cc exit=1) =====
cs11b-prec.cs(4,16): error CS9212: Spread operator '..' cannot operate on variables of type 'Range' because 'Range' does not contain a public instance or extension definition for 'GetEnumerator'
cs11b-prec.cs(5,15): error CS9212: Spread operator '..' cannot operate on variables of type 'Range' because 'Range' does not contain a public instance or extension definition for 'GetEnumerator'
```

**왜 그런가**

```text
   int[] r1 = [.. 1..3];        (4,16)   「1..3」 전체가 하나의 피연산자다
   int[] r2 = [..(1..3)];       (5,15)   괄호를 쳐도 같은 에러 — 열만 괄호만큼 다르다
   int[] r3 = [.. a[1..3]];     에러 없음 — a[1..3] 은 int[] 라 열거 가능하다
```

- ★★★ **두 줄이 같은 에러**(`CS9212`, `'Range' does not contain … 'GetEnumerator'`)를 낸다.\
  **괄호를 쳐도 안 쳐도 같다**는 것이 **`..` 가 `1..3` 전체를 피연산자로 잡았다**는 증거다.\
  ★ **`(4,16)` 과 `(5,15)`** — **열 차이가 괄호 한 칸**뿐이다.
- ★★★ **값으로는 원리상 못 가른다.** `..` 가 어느 쪽으로 묶이든 **성공하는 식이 없기** 때문이다 —\
  **일부러 에러를 내고 열을 읽는 것**이 유일한 창이다.
- ★ **`[.. a[1..3]]` 은 통과한다**(에러가 두 건뿐이다). **같은 `..` 가 한 줄에서 두 뜻**으로 쓰인다 —\
  바깥의 `..` 는 **스프레드**, `a[1..3]` 안의 `..` 는 **범위 연산자**([09번](../09-arrays-index-and-range/))다.
- ★ **스프레드가 요구하는 것은 `GetEnumerator`** 다 — 진단 문구가 그대로 적고 있다.

### 9. ★★★ 움직인 칸은 **셋**, 폭은 전부 **72의 배수**다

**출력 — 네 판**

```text
===== csc -out:ex.dll cs11b-tier.cs && dotnet ex.dll   (csc 기본 · 티어링 기본) =====
int[]            x = [1, 2, 3] :  112
int[]            x = [a, b, c] :   40
List<int>        x = [1, 2, 3] :   72
Span<int>        x = [1, 2, 3] :    0
ReadOnlySpan<int>x = [1, 2, 3] :   72
IEnumerable<int> x = [1, 2, 3] :  136
int[]            x = []        :    0
List<int>        x = []        :   32   (acc=0)
===== csc -out:ex.dll cs11b-tier.cs && DOTNET_TieredCompilation=0 dotnet ex.dll =====
int[]            x = [1, 2, 3] :  112
int[]            x = [a, b, c] :   40
List<int>        x = [1, 2, 3] :   72
Span<int>        x = [1, 2, 3] :    0
ReadOnlySpan<int>x = [1, 2, 3] :   72
IEnumerable<int> x = [1, 2, 3] :  136
int[]            x = []        :    0
List<int>        x = []        :   32   (acc=0)
===== csc -optimize -out:exo.dll cs11b-tier.cs && dotnet exo.dll =====
int[]            x = [1, 2, 3] :  112
int[]            x = [a, b, c] :   40
List<int>        x = [1, 2, 3] :   72
Span<int>        x = [1, 2, 3] :    0
ReadOnlySpan<int>x = [1, 2, 3] :    0
IEnumerable<int> x = [1, 2, 3] :  136
int[]            x = []        :    0
List<int>        x = []        :   32   (acc=0)
===== csc -optimize -out:exo.dll cs11b-tier.cs && DOTNET_TieredCompilation=0 dotnet exo.dll =====
int[]            x = [1, 2, 3] :   40
int[]            x = [a, b, c] :   40
List<int>        x = [1, 2, 3] :   72
Span<int>        x = [1, 2, 3] :    0
ReadOnlySpan<int>x = [1, 2, 3] :    0
IEnumerable<int> x = [1, 2, 3] :   64
int[]            x = []        :    0
List<int>        x = []        :   32   (acc=0)
```

**출력 — 탐침 여덟**

```text
===== 소스: cs11b-quiet.cs =====
using System;
using System.Collections.Generic;

// 컬렉션 식의 「값」은 전부 같고 「비용」만 다른 자리를 여섯 개 심었다.
// -warn:9 로 컴파일해 컴파일러가 몇 군데에서 말하는지 센다.
public static class Probes {
    public static int[] Q1() => [1, 2, 3];                           // 1. 상수 경로 — 112바이트/회
    public static int[] Q2(int a, int b, int c) => [a, b, c];        // 2. 같은 모양인데 40바이트/회
    public static int Q3() { ReadOnlySpan<int> s = [1, 2, 3]; return s[0]; }  // 3. 72바이트/회
    public static int Q4() { Span<int> s = [1, 2, 3]; return s[0]; }          // 4. 0바이트/회
    public static IEnumerable<int> Q5() => [1, 2, 3];                // 5. 감싸개가 하나 더 — 136바이트/회
    public static List<int> Q6() => [];                              // 6. 빈 것도 32바이트/회
    public static int[] Q7() => [];                                  // 7. 빈 것이 0바이트/회
    public static int Q8(int[] src) { int t = 0; foreach (int[] x in new[] { (int[])[..src] }) t += x.Length; return t; }  // 8. 스프레드가 복사한다
}
===== csc -warn:9 -target:library -out:ex.dll cs11b-quiet.cs (cc exit=0) =====
```

**왜 그런가**

| 줄 | csc 기본·티어링 기본 | csc 기본·`TC=0` | `-optimize`·티어링 기본 | `-optimize`·`TC=0` |
|---|---|---|---|---|
| `int[] x = [1, 2, 3]` | 112 | 112 | 112 | ★★★ **40** |
| `ReadOnlySpan<int> x = [1, 2, 3]` | 72 | 72 | ★★★ **0** | ★★★ **0** |
| `IEnumerable<int> x = [1, 2, 3]` | 136 | 136 | 136 | ★★ **64** |
| `int[] x = [a, b, c]` · `List` · `Span` · 빈 것들 | ★ **전부 그대로** | 그대로 | 그대로 | 그대로 |

- ★★★ **움직인 칸은 셋뿐이고, 움직인 폭이 전부 72(또는 그 배수)다** — 112→40 · 72→0 · 136→64.\
  **그 72 가 6번의 `ldtoken` 핸들**이다. **JIT 이 최적화 단계에 이르면 사라진다.**
- ★★★ **안 움직인 것이 결론이다** — **`Span` 은 언제나 0**, **배열 하나는 40**, **`List` 는 72**,\
  **빈 `int[]` 는 0**, **빈 `List` 는 32**. ★ **대상 타입끼리의 대소 관계가 네 판 전부에서 같았다.**
- ★★ **`-optimize` 만으로는 상수 배열이 안 내려갔다.** **티어드 JIT 이 tier-0 로 먼저 컴파일**하는데\
  이 프로그램은 **너무 빨리 끝나 tier-1 승격이 오지 않기** 때문이다 —\
  ★ **긴 서비스에서는 승격된 쪽(마지막 열)이 정상 상태**다.
- ★★★ **`-warn:9` 로 탐침 여덟을 물으면 0건**이다(`cc exit=0`, 진단 한 줄도 없다).\
  **컴파일러는 「되나 안 되나」만 말하고 「얼마인가」는 한 줄도 말하지 않는다** —\
  [03번](../03-boxing-and-unboxing/)의 박싱과 **같은 성질의 주제**다.

### 10. 다른 주제와 잇기

- **무엇을 고르나**의 정본은 [10번](../10-collection-choosing-list-dictionary-hashset-queue-stack/)이다.\
  ★ 「넣는 법 셋」이 거기서 **덮기(`[k]=v`) · 던지기(`Add`) · `false`(`TryAdd`)** 로 갈리고,\
  **그중 앞의 둘이 여기 3번의 문법 두 꼴**이 된다.
- **할당 바이트 재는 법과 `cs-il.cs` 전문**은 [03번](../03-boxing-and-unboxing/) (0)절에서 왔다.\
  ★ **컴파일러가 침묵하는 주제**라는 성질도 같다(9번).
- **`..` 가 범위 연산자인** 주제는 [09번](../09-arrays-index-and-range/)이다. 8번이 그 짝이다.
- **`var` 와 타겟 타입 `new`** 는 [04번](../04-var-and-target-typed-new/)이다 — 7번의 `CS9176` 이 같은 집안이다.
- ★★ **`Span<T>` 가 0바이트인 이유**의 정본은 목록의 **46번 주제**다.\
  여기(4번·5번)는 **IL 에 `newarr` 이 없다는 것과 증분이 0이라는 것**까지만 본다.
- ★★ **C++ 의 `{}` 초기화와 방향이 반대다** —\
  C++ 갈래 목록([`cpp/syntax/README.md`](../../../cpp/syntax/README.md))의 **4번**([`04-brace-initialization-narrowing-and-initializer-list/`](../../../cpp/syntax/04-brace-initialization-narrowing-and-initializer-list/))에서\
  **`{}` 는 「이 값들이 이 타입에 들어가나」를 검사한다**(좁히기 금지).\
  **여기 `[]` 는 반대로 「왼쪽 타입이 무엇을 만들라고 하나」를 받는다** — **검사가 아니라 지시**다.

## 실행 검증

| 무엇 | 몇 번·어디서 | 결과 |
|---|---|---|
| `cs11b-objinit.cs` 객체 초기화자 | csc 1회 | ★★ `= ` 없으면 고치고 있으면 갈아 끼운다 · 던지면 **옛 값 유지** |
| `cs11b-il-init.cs` IL | csc 1회(5메서드) | ★★★ 초기화자는 **`dup`** 만 쓴다 · `Add`/`set_Item` 이 갈린다 |
| `cs11b-add.cs` `Add` 없음 | csc 1회 | **에러 3건** — `CS1061` ×2 · `CS1922` |
| `cs11b-add-ok.cs` 확장 `Add` | csc 1회 | ★★★ **확장 메서드로도 성립**(합 6) · 인자 둘짜리 `Add` |
| `cs11b-idx.cs` 인덱스 초기화자 | csc 1회 | ★★ 중복 키 — **던지기 대 덮기** · `Capacity` **4 대 3** |
| `cs11b-expr.cs` 컬렉션 식 | csc 1회(8줄) | ★★★ `<>z__ReadOnlyArray'1` · `Array.Empty` 동일 객체 **True** |
| `cs11b-il-expr.cs` 대상 타입별 IL | csc 1회(8메서드) | ★★★ **여덟이 전부 다르다** · `List` 는 `Add` **0회** · `Span` 에 `newarr` 없음 |
| `cs11b-alloc.cs` 할당 바이트 | csc 1회(13줄) | ★★★ **0 · 40 · 72 · 112 · 136** · 빈 것 중 `List` 만 **32** |
| `cs11b-blob.cs` 원소 크기 | csc 1회(6줄) | ★★★ `ROSpan<byte>` **0** · `ROSpan<int>` **72** |
| `cs11b-il-blob.cs` 그 이유 | csc 1회 | ★★★ **`ldsflda` 대 `ldtoken`** |
| `cs11b-target.cs` 대상 타입 없음 | csc 1회 | **에러 3건** — `CS9176` ×2 · `CS9174` |
| `cs11b-prec.cs` `..` 결합 | csc 1회 | ★★ `CS9212` **`(4,16)` 과 `(5,15)`** · `a[1..3]` 은 통과 |
| `cs11b-tier.cs` 네 판 | csc 2회 × 실행 2회 = **4판** | ★★★ **움직인 칸 3 · 폭은 전부 72의 배수** |
| `cs11b-quiet.cs` 탐침 여덟 | csc 1회(`-warn:9`) | ★★★ **진단 0줄 · `cc exit=0`** |
| `cs11b-form.cs` 형태 | csc 1회 | 아홉 꼴이 전부 컴파일·실행됐다 |

**구현 의존 항목** — 다음은 **이 판(.NET SDK 10.0.401 · 런타임 10.0.12 · linux-x64)에서만** 그렇다.

- ★★★ **컬렉션 식이 풀리는 IL 전부** — `InlineArray3` · `CollectionsMarshal.SetCount` · `CreateSpan` · `<>z__ReadOnlyArray`.\
  **명세가 정한 것이 아니라 Roslyn 이 고른 것**이고, 판이 오르면 바뀔 수 있다.
- ★★★ **할당 바이트의 절댓값** — 9번이 **네 판에서 세 칸이 움직이는 것**을 보였다.
- ★★ **`Capacity` 4 대 3** — `List<T>` 의 증가 수열은 BCL 구현이다.
- ★★ **`ldsflda` 대 `ldtoken`** 의 갈림(원소 크기 1바이트 경계) — Roslyn 의 선택이다.
- ★ **진단 문구** · **`<PrivateImplementationDetails>` 필드 이름**(내용의 해시다).

**언어가 보장하는 것**(구현이 바뀌어도 같다)

- **객체 초기화자가 생성자 뒤에 돌고, 변수에는 마지막에 대입되는** 것.
- **중첩 초기화자에 `=` 가 없으면 이미 있는 것을 고치는** 것.
- **컬렉션 초기화자가 `IEnumerable` 구현과 `Add` 를 요구하는** 것, **`Add` 가 확장 메서드여도 되는** 것.
- **`{ x, y }` 가 인자 둘짜리 `Add`, `[k] = v` 가 인덱서를 부르는** 것.
- **컬렉션 식에 대상 타입이 있어야 하는** 것(`var` 로 못 받는다).
- **스프레드 피연산자가 열거 가능해야 하는** 것.

**안 돌려 본 것 / 못 잰 것**

- **안 돌려 본 것** — ★ **`-langversion:11` 이하 판**(컬렉션 식이 없는 판에서 진단이 어떻게 나오는지) ·\
  ★ **`[CollectionBuilder]` 로 내 타입을 `[…]` 으로 만드는 판** ·\
  ★ **`params` 컬렉션(C# 13)** · ★ **Windows·arm64 판**(할당 바이트가 헤더 크기에 달려 있다) ·\
  ★ **원소가 100개·1000개일 때의 경로**(전부 3원소로만 쟀다 — 큰 배열에서 `Add` 경로와 갈릴 수 있다) ·\
  ★ **`SortedDictionary`·`ImmutableList` 등 다른 대상 타입**.
- **못 잰 것** — ★★★ **「그래서 얼마나 빠른가」.**\
  이 문서가 센 것은 **할당 바이트와 IL 명령까지**다. **바이트는 시간이 아니다** —\
  GC 압력·캐시·JIT 인라인이 전부 빠져 있다. **재려면 벤치마크 하네스가 따로 필요하다.**
- ★ 「**부적용인 창**」 — **예외 전문.** 컬렉션 식은 **런타임에 던질 자리가 원리적으로 없다**(7번).\
  3번의 `ArgumentException` 은 **`Add` 의 계약**이라 정본이 [10번](../10-collection-choosing-list-dictionary-hashset-queue-stack/)이고, 여기서는 **타입과 메시지만** 잡아 찍었다.

**버전이 올랐을 때 다시 돌려야 하는 것**

- ★★★ **4번·6번의 IL 전부** — Roslyn 이 코드 생성을 바꾸면 **표가 통째로 움직인다.**
- ★★★ **5번·9번의 할당 바이트** — 런타임이 `ldtoken` 핸들을 캐시하기 시작하면 **72가 사라진다.**
- ★★ **3번의 `Capacity` 4** — `List<T>` 의 증가 수열이 바뀌면 움직인다.
- ★ **9번의 탐침 여덟이 계속 0건인지** — 컴파일러가 「이 자리는 비싸다」를 말하기 시작할 수 있다.
