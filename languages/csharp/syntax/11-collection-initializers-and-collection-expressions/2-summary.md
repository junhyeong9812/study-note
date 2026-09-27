# csharp/syntax/11 — 컬렉션 초기화와 컬렉션 식(C# 12) — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [ECMA-334 7판(2023-12)](https://ecma-international.org/publications-and-standards/standards/ecma-334/) ·
> [Learn — 객체·컬렉션 초기화자](https://learn.microsoft.com/en-us/dotnet/csharp/programming-guide/classes-and-structs/object-and-collection-initializers) ·
> [Learn — 컬렉션 식](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/operators/collection-expressions) ·
> [.NET API — `Array.Empty<T>`](https://learn.microsoft.com/en-us/dotnet/api/system.array.empty) ·
> [.NET API — `CollectionsMarshal`](https://learn.microsoft.com/en-us/dotnet/api/system.runtime.interopservices.collectionsmarshal) ·
> [.NET API — `GC.GetAllocatedBytesForCurrentThread`](https://learn.microsoft.com/en-us/dotnet/api/system.gc.getallocatedbytesforcurrentthread)
> **실행 검증** — 이 문서의 모든 출력·진단·IL·할당 바이트는 아래 「이 판」의 도구로 **실제로 돌려 얻은 것**이다(2026-09-25).\
> ★ 블록은 캡처 스크립트가 파일로 받아 조립기가 끼워 넣은 것이다 — 사람이 옮겨 적은 줄은 하나도 없다.\
> ★ 소스 펜스의 배너도 **캡처가 찍은 것**이다. 원고에 손으로 쓴 배너는 없다.\
> ★★★ **진단 언어를 영어로 고정했다.** 안 그러면 **로캘을 따라 한국어로 나와 재현이 안 된다** —\
> 환경변수 **`DOTNET_CLI_UI_LANGUAGE=en`** 과 `csc` 플래그 **`-preferreduilang:en-US`** 를 같이 건다.
> **던진 형태** — MSBuild(`dotnet build`·`dotnet run`)를 **안 썼다.** Roslyn 컴파일러를 **직접** 부른다 —\
> 그래야 `bin/`·`obj/` 가 안 생기고, 진단 경로가 **절대 경로가 아니라 파일명**으로 나오며, 한 판이 0.3초 안에 끝난다.\
> 배너의 `csc` 는 아래 셸 함수이고, `ex.runtimeconfig.json` 은 아래 한 줄짜리 파일이다.
>
> ```text
> export DOTNET_CLI_TELEMETRY_OPTOUT=1 DOTNET_NOLOGO=1
> export DOTNET_CLI_UI_LANGUAGE=en            # ★★★ 안 주면 진단이 한국어로 나온다
> D=$(dirname "$(readlink -f "$(command -v dotnet)")")
> ls "$D"/packs/Microsoft.NETCore.App.Ref/10.0.12/ref/net10.0/*.dll | sed 's/^/-r:/' > refs.rsp
> echo '{"runtimeOptions":{"tfm":"net10.0","framework":{"name":"Microsoft.NETCore.App","version":"10.0.0"}}}' > ex.runtimeconfig.json
> csc() { dotnet exec "$D/sdk/10.0.401/Roslyn/bincore/csc.dll" \
>           -nologo -nostdlib -noconfig @refs.rsp \
>           -preferreduilang:en-US -langversion:latest -target:exe "$@"; }
> ```
>
> **`-debug` 를 안 줬다** — PDB 가 없으면 스택 트레이스에 **절대 경로와 줄 번호가 안 박힌다**.
> **IL 은 외부 도구 없이 본다** — `ilspycmd`·`ildasm` 을 안 깔았다.
> [03번](../03-boxing-and-unboxing/)의 (0)절에 있는 **`cs-il.cs` 전문**을 그대로 써서
> `csc -target:library -out:il.dll cs-il.cs` 로 만들어 두고 `-r:il.dll` 로 참조한다.
> **버전** — **객체·컬렉션 초기화자는 C# 3.0부터**, **인덱스 초기화자는 C# 6.0부터**,
> **컬렉션 식 `[…]` 과 스프레드 `..` 는 C# 12부터**다. `-langversion:latest` 로 던졌다.
> **경계** — **어떤 컬렉션을 고르나**는 [10번](../10-collection-choosing-list-dictionary-hashset-queue-stack/)이 정본이고, 여기는 **그것을 어떻게 채우나**만 본다.\
> **박싱**은 [03번](../03-boxing-and-unboxing/), **배열과 `..` 범위 연산자**는 [09번](../09-arrays-index-and-range/), **타겟 타입 `new`** 는 [04번](../04-var-and-target-typed-new/)이 정본이다.\
> **`Span<T>` 자체**는 목록의 **46번**, **`IEnumerable<T>` 와 `foreach`** 는 **31번**, **`required`** 는 **13번 주제**가 정본이다.\
> ★ `Dictionary` 의 「넣는 법 셋」(`[k]=v`·`Add`·`TryAdd`)은 [10번](../10-collection-choosing-list-dictionary-hashset-queue-stack/)이 정본이고, 여기서는 **초기화자 두 꼴이 그중 앞의 둘로 갈리는 것**만 본다((3)).
>
> ★★ **흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | `GC.GetAllocatedBytesForCurrentThread()` 의 **절댓값**(프로세스 누적이다) | ★★★ **두 호출 사이의 증분**과 **그 증분이 0 이냐 아니냐** |
> | ★★★ **증분의 절댓값 일부** — **판에 따라 움직인다**((6)에서 네 판을 나란히 놓았다) | ★★★ **대상 타입끼리의 대소 관계** — 네 판 전부에서 같았다 |
> | 컴파일러가 만든 **`<PrivateImplementationDetails>` 필드 이름**(해시) | ★★★ **IL 명령어 열**(`newarr`·`stelem`·`ldtoken`·`ldsflda`·`InlineArray3`·`CreateSpan`) |
> | 진단 문구가 판마다 다듬일 수 있다는 것 | ★★ **진단 코드**(`CS1061`·`CS1922`·`CS9176`·`CS9174`·`CS9212`)와 **`(행,열)`** |
> | 실행 시간 | ★★ **`cc exit` 와 `run exit`**(갈라 적었다) · **`Capacity` 값** |

## 이 판

```text
===== 명령: dotnet --version && dotnet --list-runtimes | grep NETCore && g++ --version | head -1 (exit=0) =====
10.0.401
Microsoft.NETCore.App 10.0.12 [/home/jun/.local/opt/dotnet/shared/Microsoft.NETCore.App]
g++ (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0
```

## 이 갈래가 쓰는 세 층

| 층 | 뜻 | 이 주제에서 근거로 쓰는 것 |
|---|---|---|
| **언어 명세(ECMA-334)** | C# 언어가 약속한 것 | **무엇이 컴파일되고 무엇이 에러인가** · `Add` 를 찾는다는 규칙 · 대상 타입이 있어야 한다는 규칙 |
| **런타임·BCL 구현** | Roslyn·CoreCLR·BCL 이 그렇게 하는 것 | ★★★ **컬렉션 식이 어떤 IL 로 풀리나** · 할당 바이트 · `Capacity` · `Array.Empty` 재사용 |
| **이 판의 관찰** | .NET 10.0.12 · linux-x64 에서 이번에 본 것 | ★★ **할당 바이트의 절댓값** — (6)에서 **판을 바꾸면 움직이는 칸**을 갈라 적었다 |

★★★ **이 주제는 첫 칸이 「되나 안 되나」만 말하고, 「얼마인가」는 전부 둘째·셋째 칸이다.**\
`List<int> x = [1, 2, 3];` 이 컴파일된다는 것만 명세가 약속하고,\
**그것이 `Add` 세 번인지 `CollectionsMarshal.SetCount` 한 번인지는 컴파일러가 정한다**((5)).

## 한눈에 — 쉽게 말하면

**컬렉션 식 `[…]` 은 「내용만 적고 그릇은 왼쪽에 맡기는 것」이다.**

카페에서 「아메리카노 셋」이라고만 말한다고 하자.\
**컵에 담을지, 텀블러에 담을지, 쟁반째 줄지는 「받는 쪽」이 정한다.**\
같은 말인데 나오는 물건이 다르다.

`[1, 2, 3]` 도 그렇다. **오른쪽은 한 글자도 같은데 왼쪽 타입에 따라 다른 것이 만들어진다.**

| 비유 | 실체 | 이 문서에서 |
|---|---|---|
| 내용만 말한다 | `[1, 2, 3]` | (4) |
| ★★★ **받는 쪽이 그릇을 정한다** | ★★★ **대상 타입(target type)** — `int[]`·`List<int>`·`Span<int>` | (5)(6) |
| 받는 쪽이 없으면 주문이 안 된다 | ★★ **`var x = [];` 는 컴파일 에러** | (7) |
| 다른 잔의 내용을 부어 넣는다 | ★★ **스프레드 `..other`** | (4)(5) |
| ★★ **빈 주문은 공짜다** | ★★ **`int[] x = []` 는 할당 0** | (6) |
| 옛 방식 — 그릇을 먼저 사고 하나씩 담는다 | **`new List<int> { 1, 2, 3 }`** — `Add` 세 번 | (2)(5) |

> **컬렉션 식(collection expression)** — C# 12 의 `[…]`. **대상 타입이 무엇을 만들지 정한다.**\
> 예: `int[] a = [1, 2, 3];` 과 `List<int> l = [1, 2, 3];` 은 **오른쪽이 같고 만들어지는 것이 다르다.**

> **스프레드 원소(spread element)** — `..식`. **그 컬렉션의 원소를 그 자리에 펼친다.**\
> 예: `int[] a = [10, 20, ..other, 50];`

```text
   같은 오른쪽, 다른 왼쪽                 무엇이 만들어지나 (IL 로 확인 — (5))

   int[]             x = [1, 2, 3];   ->  newarr int32  +  상수 블록을 복사
   int[]             x = [a, b, c];   ->  newarr int32  +  stelem 세 번
   List<int>         x = [1, 2, 3];   ->  List ctor + CollectionsMarshal.SetCount + Span 에 직접 쓰기
   Span<int>         x = [1, 2, 3];   ->  ★ InlineArray3 — 힙을 안 쓴다
   ReadOnlySpan<int> x = [1, 2, 3];   ->  RuntimeHelpers.CreateSpan (읽기 전용 데이터를 가리킨다)
   IEnumerable<int>  x = [1, 2, 3];   ->  배열 + 읽기 전용 감싸개 하나 더
   int[]             x = [];          ->  ★ Array.Empty<int>() — 새로 안 만든다
```

- ★★★ **일곱 줄이 전부 다른 IL 이다.** 「컬렉션 식은 설탕이다」라고 말하면 **이 일곱 줄이 한 덩어리로 보인다.**
- ★★★ **그 차이가 할당 바이트로 그대로 나온다**((6)) — 0바이트부터 136바이트까지.

## 이 주제가 답하려는 질문

1. **컬렉션 초기화자는 무엇을 찾나** — 「`Add` 를 부른다」는 **어디까지 참인가**((2)).
2. **컬렉션 식은 대상 타입마다 무엇을 만드나** — **IL 과 바이트로** 가를 수 있나((5)(6)).
3. **빈 `[]` 는 공짜인가** — **어느 타입에서** 공짜인가((6)).
4. **대상 타입이 없으면 어떻게 되나**((7)), 그리고 **`..` 는 어디까지 묶이나**((8)).

## 동작 방식

### (0) 이 주제가 쓰는 창

| 창 | 무엇을 보여 주나 | 이 주제에서 |
|---|---|---|
| ★★★ **IL** | ★★★ **같은 `[…]` 가 대상 타입마다 다른 것으로 풀리는 것** | (1)·(5) |
| ★★★ **할당 바이트** | ★★★ **그 차이가 얼마인가** · **빈 것이 공짜인가** | (6) |
| **실행 출력** | 무엇이 만들어졌나 · `Capacity` · 런타임 타입 | (1)·(3)·(4) |
| **컴파일 진단** | `Add` 를 못 찾을 때 · 대상 타입이 없을 때 · ★ **`..` 의 결합**을 `(행,열)` 로 | (2)·(7)·(8)·(9) |
| ★ **예외 전문** | ★★ **부적용** — 아래 | — |

- ★★★ **중심 창은 둘이다 — IL 과 할당 바이트.** [10번](../10-collection-choosing-list-dictionary-hashset-queue-stack/)은 중심이 **실행 출력**(순회 순서)이었는데,\
  **여기는 출력이 전부 같다.** `[1, 2, 3]` 은 어느 대상 타입에서도 **1, 2, 3** 을 내놓는다 —\
  **갈리는 것은 값이 아니라 무엇이 만들어졌나**이고, 그것은 **IL 과 바이트로만** 보인다.
- ★★ **「부적용인 창」 — 예외 전문.** 컬렉션 식은 **런타임에 던질 자리가 원리적으로 없다** —\
  대상 타입이 안 맞으면 **전부 컴파일 에러**다((7)). (3)에서 본 `ArgumentException` 은\
  **컬렉션 초기화자가 부르는 `Add` 의 계약**이지 초기화 문법 자체의 것이 아니고, 그 정본은 [10번](../10-collection-choosing-list-dictionary-hashset-queue-stack/)이다.\
  **「안 쟀다」가 아니라 「실을 전문이 없다」다** — 그래서 (3)은 **타입과 메시지만** 잡아 찍었다.
- ★★★ **네 번째 창을 하나 더 썼다 — 진단의 `(행,열)`.** `..` 가 어디까지 묶이는지는\
  **값으로는 원리상 못 가른다.** (8)에서 **일부러 에러를 내고 열을 읽는다.**
- ★★★ **측정 조건을 하나 더 선언한다** — (6)의 할당 바이트는 **판을 타는 칸이 있다.**\
  `csc -optimize` 여부와 **티어드 JIT** 여부로 **네 판**을 나란히 돌려, **움직이는 칸을 표로 갈라 놓았다.**\
  ★ 본문의 수치는 **이 문서의 기본 판**(`csc` 기본 · 티어링 기본)의 것이다.

### (1) ★★ 객체 초기화자 — `=` 하나가 「고친다」와 「갈아 끼운다」를 가른다

**언제 쓰나** — 생성자 인자로 다 못 받는 객체를 만들 때.

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

```text
   new Box { Inner = { X = 7 } }        new Box { Inner = new Point { X = 9 } }
             ^^^^^^^^^^^^^^^                      ^^^^^^^^^^^^^^^^^^^^^^^^
             = 뒤가 { } 뿐              = 뒤가 new
             -> get_Inner() 로 꺼내       -> 새 Point 를 만들어
                이미 있는 것을 고친다        set_Inner() 로 갈아 끼운다
```

- ★★★ **`Inner = { … }` 는 `Inner` 를 새로 만들지 않는다.** **이미 있는 것을 꺼내 고친다** —\
  그래서 **`Inner` 의 setter 가 없어도 된다.** (`Tags = { "a", "b" }` 도 같다 — `Add` 를 두 번 부른다.)
- ★★ **초기화자가 도중에 던지면 변수는 옛 값 그대로**다(`q = (5, 5)`).\
  **객체를 다 만든 뒤에야 변수에 대입**하기 때문이다 — 아래 IL 이 그대로 보여 준다.

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

- ★★★ **객체 초기화자는 지역 변수를 안 쓴다** — `newobj` → **`dup`** → `set_X` → `dup` → `set_Y` → `ret`.\
  **스택 위에서 다 채운 뒤 마지막에 내놓는다.** 손으로 쓴 `Plain()` 은 `stloc`/`ldloc` 를 쓴다.\
  ★ **그래서 「도중에 던지면 옛 값이 남는다」가 문법의 성질이 아니라 IL 의 모양**이다.
- ★★ **컬렉션 초기화자는 `Add`, 인덱스 초기화자는 `set_Item`** 이다 — `ColInit` 과 `IdxInit` 을 나란히 보면 한 줄만 다르다.
- ★ **`{ "a", 1 }` 꼴도 `Add`** 다(`PairInit`) — **인자 둘짜리 `Add`** 를 찾는다((2)).
- ★ **`nop` 이 섞여 있는 것은 `-optimize` 없이 낸 덤프이기 때문**이다. 이 문서의 모든 IL 이 그 판이다.

**비용** — 객체 초기화자 자체는 0. **프로퍼티 setter 호출 수만큼**이 전부다.

### (2) ★★★ 컬렉션 초기화자는 무엇을 찾나 — 던져서 확인한다

**언제 쓰나** — 내가 만든 타입에 `{ … }` 를 붙이고 싶을 때.

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

- ★★★ **조건이 둘이다.** `IEnumerable` 을 구현해야 하고(`CS1922`), **`Add` 가 있어야 한다**(`CS1061`).\
  **둘 중 하나만 빠져도 안 된다** — 그리고 **에러 코드가 다르다.**
- ★★ **`CS1061` 은 원소마다 하나씩 난다**(`(5,21)` 과 `(5,24)`) — `{ 1, 2 }` 의 **`1` 자리와 `2` 자리**다.
- ★ **`IEnumerable` 은 제네릭이 아니어도 된다** — 비제네릭 `System.Collections.IEnumerable` 로 충분하다.

★★ **그런데 `Add` 는 「그 타입의 메서드」가 아니어도 된다.**

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

- ★★★ **확장 메서드 `Add` 로도 성립한다.** `Seen` 에는 `Add` 가 없는데 `new Seen { 1, 2, 3 }` 이 돌았고 **합이 6**이다.\
  ★ 진단 문구가 이미 그렇게 적고 있었다 — `no accessible extension method 'Add' … could be found`.
- ★★ **`{ x, y }` 꼴은 인자 둘짜리 `Add`** 를 찾는다(`Add(a,1) Add(b,2)`).\
  **`Dictionary` 의 `{ "a", 1 }` 이 특별한 문법이 아니라 이 규칙 하나**다.
- ★ **`GetEnumerator` 가 실제로 쓸모 있을 필요는 없다** — 두 예제 모두 **빈 리스트의 열거자**를 돌려준다.\
  **컴파일러는 「구현했나」만 본다.**

**비용** — 원소 하나당 **`Add` 호출 하나**. (5)에서 컬렉션 식과 갈린다.

### (3) ★ 인덱스 초기화자 — 중복 키에서 두 꼴이 갈린다

**언제 쓰나** — `Dictionary` 를 리터럴처럼 적을 때.

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

| 꼴 | 부르는 것 | 중복 키에서 | `Count` |
|---|---|---|---|
| `{ "a", 1 }, { "a", 2 }` | `Add(k, v)` | ★★★ **`ArgumentException`** | — |
| `["a"] = 1, ["a"] = 2` | `set_Item(k, v)` | ★★ **덮어쓴다** | 1 |

- ★★★ **같은 뜻처럼 보이는 두 꼴이 중복 키에서 갈린다.** `Add` 꼴은 던지고, 인덱스 꼴은 **조용히 덮는다.**\
  ★ [10번](../10-collection-choosing-list-dictionary-hashset-queue-stack/)의 「넣는 법 셋」 중 **앞의 둘**이 그대로 문법 두 꼴이 된 것이다.
- ★★ **인덱스 초기화자는 내가 만든 타입에도 붙는다** — 인덱서만 있으면 된다(`set_Item(0, 영) set_Item(2, 둘)`).
- ★★★ **같은 세 값인데 `Capacity` 가 다르다** — `new List<int> { 1, 2, 3 }` 은 **4**, `List<int> x = [1, 2, 3]` 은 **3** 이다.\
  ★ 앞쪽은 `Add` 를 세 번 부르며 **1 → 2 → 4 로 늘린 자국**이고, 뒤쪽은 **개수를 미리 알아 정확히 잡은 것**이다((5)).

**비용** — 원소 하나당 `set_Item` 하나. **중복 키가 조용히 덮이는 것**이 진짜 비용이다.

### (4) ★★★ 컬렉션 식 — 무엇이 만들어지나

**언제 쓰나** — C# 12 이후 컬렉션을 적는 자리 전부.

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

- ★★★ **오른쪽이 같은데 왼쪽이 다르면 다른 것이 만들어진다.** `int[]`·`List<int>`·`Span<int>`·`IEnumerable<int>` 넷이 전부 성립한다.
- ★★★ **`IEnumerable<int> e = [1, 2, 3]` 의 런타임 타입이 `<>z__ReadOnlyArray'1`** 다 —\
  **배열도 리스트도 아닌 컴파일러가 만든 읽기 전용 감싸개**다. **인터페이스로 받으면 고칠 수 없게 잠가 준다.**
- ★★★ **`int[] empty = []` 는 `Array.Empty<int>()` 와 같은 객체**다(`True`). **새로 만들지 않는다.**
- ★★ **스프레드는 타입을 안 가린다** — `[..src]` 에서 `src` 가 `List<int>` 여도 왼쪽이 `int[]` 면 배열이 나오고,\
  **배열과 리스트를 한 줄에 섞어 펼쳐도 된다**(`[..(int[])[1, 2], ..(List<int>)[3, 4]]`).
- ★ **`Span<int> s = [7, 8, 9]` 가 그냥 된다** — 이것이 (6)에서 **0바이트**가 되는 자리다.

**비용** — 대상 타입마다 다르다. (5)에서 IL 로, (6)에서 바이트로 가른다.

### (5) ★★★ 대상 타입마다 다른 IL 로 풀린다

**언제 쓰나** — 「컬렉션 식은 그냥 설탕이지」라고 말하고 싶을 때.

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

| 대상 타입 | 핵심 IL | 무엇을 만드나 |
|---|---|---|
| `int[]` (상수) | `newarr` + **`ldtoken`** + `InitializeArray` | 배열 하나 + **상수 블록을 통째로 복사** |
| `int[]` (변수) | `newarr` + `stelem.i4` ×3 | 배열 하나 + **한 칸씩 쓰기** |
| `List<int>` | `List..ctor(int)` + **`CollectionsMarshal::SetCount`** + `AsSpan` | ★★★ **`Add` 를 한 번도 안 부른다** |
| `Span<int>` | **`InlineArray3<int>`** + `InlineArrayAsSpan` | ★★★ **힙을 안 쓴다 — 스택 위의 인라인 배열** |
| `ReadOnlySpan<int>` | **`RuntimeHelpers::CreateSpan`** | 읽기 전용 데이터를 **가리키기만** 한다 |
| `int[]` (스프레드) | `ldlen` 으로 길이를 더해 `newarr` + `ReadOnlySpan::CopyTo` | ★★ **`Add` 가 아니라 `CopyTo`** 다 |
| `int[]` (빈 것) | **`Array::Empty`** | ★★★ **아무것도 안 만든다** |
| `IEnumerable<int>` | 배열 + **`<>z__ReadOnlyArray..ctor`** | 배열 + 감싸개 하나 |

- ★★★ **`List<int> x = [1, 2, 3]` 이 `Add` 를 한 번도 안 부른다.** `CollectionsMarshal.SetCount` 로 **길이를 먼저 맞추고**\
  `AsSpan()` 을 받아 **칸에 직접 쓴다.** ★ (3)의 `Capacity` 3 대 4 가 여기서 나온다.
- ★★★ **`Span<int> s = [1, 2, 3]` 에 `newarr` 이 없다.** `InlineArray3<int>` 라는 **지역 변수**를 만들고\
  거기에 쓴 뒤 `InlineArrayAsSpan` 으로 span 을 얻는다 — **힙을 한 바이트도 안 쓴다**((6)).
- ★★ **스프레드는 `Add` 가 아니라 `CopyTo`** 다. 길이를 `2 + o.Length` 로 **먼저 계산해 배열 하나만** 만든다 —\
  **중간 리스트를 만들지 않는다.**
- ★★ **`[]` 는 `Array.Empty<T>()` 호출 한 줄**이다. **`newarr` 자체가 없다.**
- ★ **`ldtoken` 과 `ldsflda` 가 갈리는 자리가 있다** — (6)에서 그 차이가 **바이트로** 나온다.

**비용** — (6)에서 센다.

### (6) ★★★ 할당 바이트로 갈라라 — 그리고 어느 칸이 판을 타나

**언제 쓰나** — 뜨거운 경로에서 컬렉션 식을 쓸 때. **이 절이 이 주제의 중심이다.**

측정 방식은 [03번](../03-boxing-and-unboxing/)·[10번](../10-collection-choosing-list-dictionary-hashset-queue-stack/)과 같다 — **워밍업 → `b0` → 연산 100회 → `b1` → 증분 ÷ 100.**\
메서드는 전부 `[MethodImpl(MethodImplOptions.NoInlining)]` 로 **인라인을 막았다.**

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

| 대상 타입 | 바이트/회 | 읽는 법 |
|---|---|---|
| `Span<int> x = [1, 2, 3]` | ★★★ **0** | **힙을 안 쓴다**((5)의 `InlineArray3`) |
| `int[] x = []` · `IEnumerable<int> x = []` | ★★★ **0** | `Array.Empty` 를 돌려준다 |
| `Span<int> x = []` | 0 | 〃 |
| `int[] x = [a, b, c]` | **40** | 배열 하나(헤더 16 + 길이 8 + 12 + 정렬) |
| `int[] x = [1, 2, ..other]` | **40** | ★★ **스프레드도 배열 하나**다 — 중간 리스트가 없다 |
| `List<int> x = [1, 2, 3]` | **72** | List 객체 32 + 배열 40 |
| `new List<int> { 1, 2, 3 }` | **72** | ★ **같다** — 값은 같고 `Capacity` 만 다르다((3)) |
| ★ `List<int> x = []` | ★★★ **32** | ★★★ **여기만 0 이 아니다** — 빈 `List` 객체는 만들어야 한다 |
| `ReadOnlySpan<int> x = [1, 2, 3]` | **72** | ★★ **배열이 없는데도 낸다** — 아래에서 파헤친다 |
| `int[] x = [1, 2, 3]`(상수) | **112** | ★★ **배열 40 + 72** |
| `IEnumerable<int> x = [1, 2, 3]` | **136** | 배열 40 + 72 + 감싸개 24 |

- ★★★ **`Span` 이 0이고 `List<int> x = []` 만 빈 것 중에서 32다.** 「빈 것은 공짜」가 **어디까지 참인지**가 이 표다.
- ★★★ **`int[] x = [1, 2, 3]`(상수, 112)이 `int[] x = [a, b, c]`(변수, 40)보다 크다.**\
  **같은 모양인데 72바이트가 더 든다** — 그 72 가 무엇인지 아래에서 가른다.

★★ **그 72 의 정체 — 원소 크기 하나로 갈린다.**

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

- ★★★ **`ReadOnlySpan<byte>` 는 0이고 `ReadOnlySpan<int>` 는 72다.** 둘 다 배열을 안 만드는데 갈린다.
- ★★★ **IL 이 이유를 그대로 보여 준다** — `byte` 쪽은 **`ldsflda`**(데이터 필드의 주소를 바로 준다)이고,\
  `int` 쪽은 **`ldtoken` + `RuntimeHelpers::CreateSpan`** 이다.\
  ★ **1바이트 원소는 바이트 순서 문제가 없어 데이터 블록을 그대로 가리킬 수 있고**,\
  **`int` 는 그럴 수 없어 런타임에 물어봐야 한다** — 그 `ldtoken` 이 **회당 72바이트**를 낸다.
- ★★ **`byte[] x = [1, 2, 3]` 도 배열 32 + 72** 다 — **배열을 만드는 경로는 `byte` 여도 `ldtoken` 을 쓴다.**
- ★ 그래서 `+72` 는 「상수 블록을 쓰는 것」의 값이 아니라 **「`ldtoken` 이 런타임 핸들을 만드는 것」의 값이다**.

★★★ **그런데 그 72 는 판을 탄다 — 네 판을 나란히 돌렸다.**

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

| 줄 | csc 기본 · 티어링 기본 | csc 기본 · `TC=0` | `-optimize` · 티어링 기본 | `-optimize` · `TC=0` |
|---|---|---|---|---|
| `int[] x = [1, 2, 3]` | 112 | 112 | 112 | ★★★ **40** |
| `int[] x = [a, b, c]` | 40 | 40 | 40 | 40 |
| `List<int> x = [1, 2, 3]` | 72 | 72 | 72 | 72 |
| `Span<int> x = [1, 2, 3]` | ★ **0** | 0 | 0 | 0 |
| `ReadOnlySpan<int> x = [1, 2, 3]` | 72 | 72 | ★★★ **0** | ★★★ **0** |
| `IEnumerable<int> x = [1, 2, 3]` | 136 | 136 | 136 | ★★ **64** |
| `int[] x = []` | 0 | 0 | 0 | 0 |
| `List<int> x = []` | 32 | 32 | 32 | 32 |

- ★★★ **움직인 칸은 셋뿐이다** — 상수 배열(112 → 40) · `ReadOnlySpan<int>`(72 → 0) · `IEnumerable`(136 → 64).\
  **움직인 폭이 전부 72 이거나 그 배수**다. **`ldtoken` 이 만드는 핸들 객체가 최적화 단계에서 사라지는 것**이다.
- ★★★ **움직이지 않은 칸이 결론이다** — **`Span` 은 언제나 0**, **`int[]` 하나는 40**, **`List` 는 72**,\
  **빈 `int[]` 는 0**, **빈 `List` 는 32**. **대상 타입끼리의 대소 관계는 네 판 전부에서 같았다.**
- ★★ **한 판만 보고 절댓값을 인용하면 안 된다.** 「`[1, 2, 3]` 이 112바이트다」는 **이 문서의 기본 판에서만** 참이다.\
  ★ 「**돌려 본 판을 밝히지 않은 수치는 근거가 아니다**」가 여기서 그대로 성립한다.
- ★ **왜 `-optimize` 만으로는 안 되고 `TC=0` 까지 필요했나** — **티어드 JIT 이 tier-0 로 먼저 컴파일**하고,\
  이 프로그램은 **너무 빨리 끝나 tier-1 승격이 오지 않기 때문**이다. **긴 서비스에서는 승격된 쪽이 정상 상태**다.

**비용** — 표 그대로다. ★ **뜨거운 경로에서 셋을 기억하면 된다** — **`Span` 은 0 · 배열 하나면 40 · `List` 면 72.**

### (7) ★★ 대상 타입이 없으면 — 전부 컴파일 에러다

**언제 쓰나** — `var` 에 `[…]` 를 쓰고 싶을 때.

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

| 코드 | 진단 | 뜻 |
|---|---|---|
| `var x = [];` | `CS9176` | ★★★ **대상 타입이 없다** |
| `var y = [1, 2, 3];` | `CS9176` | ★ **원소가 있어도 마찬가지다** — 추론하지 않는다 |
| `object o = [1, 2, 3];` | `CS9174` | ★★ **`object` 는 「만들 수 있는 타입」이 아니다** |

- ★★★ **컬렉션 식은 스스로 타입을 정하지 않는다.** `var` 는 **오른쪽에서 타입을 받는 문법**인데\
  컬렉션 식은 **왼쪽에서 타입을 받는 식**이라 **서로 기다리다 끝난다.**\
  ★ [04번](../04-var-and-target-typed-new/)의 타겟 타입 `new` 와 **정확히 같은 이유로 `var new()` 가 안 되는 것**이다.
- ★★ **에러 코드가 둘로 갈린다** — **대상 타입이 아예 없는 것**(`CS9176`)과\
  **대상 타입은 있는데 만들 수 없는 것**(`CS9174`). **뒤쪽이 정보가 더 많다.**
- ★ 그래서 「**컬렉션 식은 런타임에 실패하지 않는다**」가 성립한다 — (0)의 「부적용인 창」이 여기서 나온다.

**비용** — 0. **타입을 한 번 더 적는 것**이 전부다.

### (8) ★★ `..` 는 어디까지 묶이나 — 진단의 `(행,열)` 로 증명한다

**언제 쓰나** — `..` 가 **범위 연산자**([09번](../09-arrays-index-and-range/))이기도 하기 때문에 헷갈릴 때.

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

```text
   int[] r1 = [.. 1..3];        열 16 -> 「1..3」 전체를 하나의 피연산자로 봤다
   int[] r2 = [..(1..3)];       열 15 -> 괄호 친 것과 같은 자리다
   int[] r3 = [.. a[1..3]];     ★ 에러가 없다 -> 배열 슬라이스는 열거 가능하다
                 ^
                 여기서 1..3 은 인덱서의 인자다
```

- ★★★ **`[.. 1..3]` 과 `[..(1..3)]` 이 같은 에러를 낸다** — `CS9212`, `'Range' does not contain … 'GetEnumerator'`.\
  **괄호를 쳐도 안 쳐도 같다는 것**이 **스프레드가 `1..3` 전체를 피연산자로 잡았다**는 증거다.\
  ★ **`(4,16)` 과 `(5,15)`** — **열이 괄호 위치만큼만 다르다.**
- ★★★ **값으로는 이것을 못 가른다.** `..` 가 어느 쪽으로 묶이든 **성공하는 식이 없기 때문**이다 —\
  **일부러 에러를 내고 열을 읽는 것**이 유일한 창이다.
- ★★ **`[.. a[1..3]]` 은 통과한다**(에러가 두 건뿐이다). `a[1..3]` 은 **`int[]` 라 열거 가능**하고,\
  그 안의 `1..3` 은 **범위 연산자**다 — **같은 `..` 가 한 줄에서 두 뜻으로 쓰인다.**
- ★ 스프레드가 요구하는 것은 「**`GetEnumerator` 가 있는 것**」이다. 진단 문구가 그대로 적고 있다.

**비용** — 0. **`Range` 를 펼치려면 `Enumerable.Range` 를 써야 한다**는 것만 기억하면 된다.

### (9) 경고를 누가 보나 — 탐침 여덟

「경고가 안 났다」를 산문으로 적으면 **안 물어본 것과 물었는데 조용한 것이 구분되지 않는다.**\
그래서 **값은 같고 비용만 다른 자리 여덟 개**를 한 파일에 심고 **`-warn:9`**(최고 경고 수준)로 물었다.

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

| 심은 것 | 진단 | 실제로는 |
|---|---|---|
| `int[] => [1, 2, 3]`(상수) | 0 | 112바이트/회 |
| `int[] => [a, b, c]` | 0 | **40바이트/회** |
| `ReadOnlySpan<int> = [1, 2, 3]` | 0 | 72바이트/회 |
| `Span<int> = [1, 2, 3]` | 0 | **0바이트/회** |
| `IEnumerable<int> => [1, 2, 3]` | 0 | 136바이트/회 |
| `List<int> => []` | 0 | **32바이트/회** |
| `int[] => []` | 0 | **0바이트/회** |
| 스프레드가 복사한다 | 0 | `CopyTo` |

- ★★★ **탐침 여덟 중 답한 것 0 · 침묵한 것 8이다.** **`-warn:9` 에서도 `cc exit=0` 에 진단 0줄**이다.
- ★★★ **이 주제에서 컴파일러가 말해 주는 것은 「되나 안 되나」뿐이고, 「얼마인가」는 한 줄도 말하지 않는다.**\
  ★ 그래서 **할당 바이트가 유일한 창**이 된다 — [03번](../03-boxing-and-unboxing/)의 박싱과 **같은 성질의 주제**다.

## 문법 — 형태와 규칙

### 형태

```csharp
// cs11b-form.cs
using System;
using System.Collections.Generic;

// ① 객체 초기화자 — 생성자 뒤에 { 프로퍼티 = 값 }
var p = new Point { X = 1, Y = 2 };

// ② 중첩 — = 없이 쓰면 이미 있는 것을 고친다
var b1 = new Box { Label = "a", Inner = { X = 7 } };
// ③ 중첩 — = 를 쓰면 새로 만들어 갈아 끼운다
var b2 = new Box { Label = "b", Inner = new Point { X = 9 } };

// ④ 컬렉션 초기화자 — Add 를 부른다
List<int> l1 = new List<int> { 1, 2, 3 };
// ⑤ 인자 둘짜리 Add
var d1 = new Dictionary<string, int> { { "a", 1 }, { "b", 2 } };
// ⑥ 인덱스 초기화자 — set_Item 을 부른다
var d2 = new Dictionary<string, int> { ["a"] = 1, ["b"] = 2 };

// ⑦ 컬렉션 식(C# 12) — 대상 타입이 무엇을 만들지 정한다
int[]            a  = [1, 2, 3];
List<int>        l2 = [1, 2, 3];
Span<int>        s  = [1, 2, 3];
IEnumerable<int> e  = [1, 2, 3];
// ⑧ 스프레드
int[] joined = [0, ..a, ..l2, 99];
// ⑨ 빈 것
int[] empty = [];

Console.WriteLine($"{p} {b1.Inner} {b2.Inner} {l1.Count} {d1.Count} {d2.Count}");
Console.WriteLine($"{a.Length} {l2.Count} {s.Length} {string.Join(",", e)} {joined.Length} {empty.Length}");

class Point { public int X { get; set; } public int Y { get; set; } public override string ToString() => $"({X}, {Y})"; }
class Box { public string Label { get; set; } = ""; public Point Inner { get; set; } = new Point(); }
```

```text
===== 소스: cs11b-form.cs =====
using System;
using System.Collections.Generic;

// ① 객체 초기화자 — 생성자 뒤에 { 프로퍼티 = 값 }
var p = new Point { X = 1, Y = 2 };

// ② 중첩 — = 없이 쓰면 이미 있는 것을 고친다
var b1 = new Box { Label = "a", Inner = { X = 7 } };
// ③ 중첩 — = 를 쓰면 새로 만들어 갈아 끼운다
var b2 = new Box { Label = "b", Inner = new Point { X = 9 } };

// ④ 컬렉션 초기화자 — Add 를 부른다
List<int> l1 = new List<int> { 1, 2, 3 };
// ⑤ 인자 둘짜리 Add
var d1 = new Dictionary<string, int> { { "a", 1 }, { "b", 2 } };
// ⑥ 인덱스 초기화자 — set_Item 을 부른다
var d2 = new Dictionary<string, int> { ["a"] = 1, ["b"] = 2 };

// ⑦ 컬렉션 식(C# 12) — 대상 타입이 무엇을 만들지 정한다
int[]            a  = [1, 2, 3];
List<int>        l2 = [1, 2, 3];
Span<int>        s  = [1, 2, 3];
IEnumerable<int> e  = [1, 2, 3];
// ⑧ 스프레드
int[] joined = [0, ..a, ..l2, 99];
// ⑨ 빈 것
int[] empty = [];

Console.WriteLine($"{p} {b1.Inner} {b2.Inner} {l1.Count} {d1.Count} {d2.Count}");
Console.WriteLine($"{a.Length} {l2.Count} {s.Length} {string.Join(",", e)} {joined.Length} {empty.Length}");

class Point { public int X { get; set; } public int Y { get; set; } public override string ToString() => $"({X}, {Y})"; }
class Box { public string Label { get; set; } = ""; public Point Inner { get; set; } = new Point(); }
===== csc -out:ex.dll cs11b-form.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
(1, 2) (7, 0) (9, 0) 3 2 2
3 3 3 1,2,3 8 0
```

### 규칙

- **객체 초기화자**는 **생성자가 끝난 뒤** 돌고, **변수에는 마지막에 대입**된다((1)).
- **중첩 초기화자에 `=` 를 안 쓰면 이미 있는 것을 고치고, 쓰면 새로 만들어 갈아 끼운다**((1)).
- **컬렉션 초기화자**는 **`IEnumerable` 구현**과 **`Add`** 둘 다 요구한다. **`Add` 는 확장 메서드여도 된다**((2)).
- **`{ x, y }` 꼴은 인자 둘짜리 `Add`**, **`[k] = v` 꼴은 인덱서 `set_Item`** 을 부른다((2)(3)).
- **컬렉션 식 `[…]` 은 대상 타입이 있어야 한다.** `var` 로는 못 받는다((7)).
- **대상 타입이 무엇을 만들지 정한다** — 배열·`List`·`Span`·인터페이스가 **전부 다른 IL** 이다((5)).
- **스프레드 `..x` 는 `x` 가 열거 가능해야** 한다. **`Range` 는 열거 가능하지 않다**((8)).
- **빈 `[]` 는 배열·인터페이스·`Span` 에서 할당 0**이고, **`List<T>` 에서만 32바이트**다((6)).

### 금지 사례 — 다섯 줄이 각각 막힌다

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

- ★ **다섯 에러가 이 주제의 규칙 셋에 대응한다** — **`Add` 가 있어야 한다**(`CS1061`) ·\
  **`IEnumerable` 이어야 한다**(`CS1922`) · **대상 타입이 있어야 한다**(`CS9176`·`CS9174`).
- ★★ **`CS9174` 의 문구가 가장 정확하다** — `the type is not constructible`.\
  「**컬렉션 식은 만들 수 있는 타입에만 붙는다**」가 이 문법의 한 줄 요약이다.

## 어디서 틀리나

### 1. ★★★ 「`List<int> x = [1, 2, 3]` 은 `Add` 세 번이다」

- ★ **한 번도 안 부른다.** `CollectionsMarshal.SetCount` 로 길이를 맞추고 **span 에 직접 쓴다**((5)).
- ★★ **그 자국이 `Capacity` 에 남는다** — 컬렉션 식은 **3**, 초기화자는 **4**((3)).

### 2. ★★★ 「컬렉션 식은 그냥 설탕이다」

- ★ **대상 타입마다 다른 것이 만들어진다**((5)). **`Span` 은 힙을 아예 안 쓴다**((6)).

### 3. ★★★ 「같은 값이면 같은 비용이다」

- ★ **`[1, 2, 3]` 이 `[a, b, c]` 보다 72바이트 비쌌다**((6)) — 그리고 **그 72 는 판을 탄다.**
- ★★ **한 판의 절댓값을 인용하지 마라** — 네 판을 나란히 놓아야 **무엇이 결론인지** 보인다.

### 4. ★★ 「빈 `[]` 는 공짜다」

- ★ **`List<int> x = []` 만 32바이트**다((6)). 배열·인터페이스·`Span` 은 0이다.

### 5. ★★ 「`var x = [1, 2, 3];` 은 되겠지」

- ★ **`CS9176`** 이다((7)). 컬렉션 식은 **왼쪽에서 타입을 받는다.**

### 6. ★★ 「`{ "a", 1 }` 과 `["a"] = 1` 은 같다」

- ★ **중복 키에서 갈린다** — 앞은 **던지고** 뒤는 **덮는다**((3)).

### 7. ★ 「`..` 는 범위 연산자다」

- ★ **컬렉션 식 안에서는 스프레드**다. **`Range` 를 펼치려 들면 `CS9212`** 다((8)).

## 구현 세부사항 대 언어 보장

| 층 | 이 주제에서 해당하는 것 | 어떻게 확인했나 | **도구가 못 보는 것** |
|---|---|---|---|
| **언어 명세(ECMA-334)** | ★★ **무엇이 컴파일되나** — `IEnumerable` + `Add` 요구((2)) · **대상 타입 요구**((7)) · 스프레드 피연산자는 열거 가능해야 한다((8)) · 초기화자가 **생성자 뒤에** 돌고 **변수에는 마지막에** 대입되는 것((1)) | 진단 코드 + `(행,열)` + `cc exit` | ★★★ **「얼마인가」는 한 줄도 말하지 않는다**((9)) |
| **런타임·BCL 구현** | ★★★ **컬렉션 식이 풀리는 IL 전부**((5)) — `InlineArray3` · `CollectionsMarshal.SetCount` · `CreateSpan` · `<>z__ReadOnlyArray` · `Array.Empty` 재사용 · **`Capacity` 3 대 4**((3)) · `ldsflda` 대 `ldtoken`((6)) | IL 덤프 · 실행 출력 | ★★ **Roslyn 이 판을 올리며 다른 IL 을 낼 수 있다** — 명세가 정한 것이 아니다 |
| **이 판의 관찰** | ★★★ **할당 바이트의 절댓값**((6)) — **네 판 중 세 칸이 움직였다** · 진단 문구 · `<PrivateImplementationDetails>` 필드 이름 | 네 판을 나란히 | ★★★ **한 판만 보면 「상수가 더 비싸다」가 성질로 보인다** — 아니다 |

### 「도구가 못 보는 것」을 층마다

| 사실 | 층 | `csc` 기본 | `csc -warn:9` | IL | 할당 바이트 |
|---|---|---|---|---|---|
| `Add` 가 없다 | 명세 | **error** | error | — | — |
| 대상 타입이 없다 | 명세 | **error** | error | — | — |
| ★★★ **`List` 가 `Add` 를 안 부른다** | 구현 | ★★★ **0건** | ★★★ **0건** | ★ **보인다** | — |
| ★★★ **`Span` 이 힙을 안 쓴다** | 구현 | ★★★ **0건** | ★★★ **0건** | ★ **보인다** | ★ **보인다** |
| ★★ **상수 배열이 72바이트 더 낸다** | 이 판 | ★★★ **0건** | ★★★ **0건** | ★ **`ldtoken` 이 보인다** | ★★★ **여기만 보인다** |
| ★★ **`List<int> x = []` 이 32바이트** | 구현 | 0건 | 0건 | — | ★★★ **여기만 보인다** |
| `Capacity` 3 대 4 | 구현 | 0건 | 0건 | ★ 간접 | ★ 출력으로 |

- ★★ **이 표의 결론 세 줄**
  - **컴파일러는 「되나 안 되나」에서 멈춘다** — 탐침 여덟이 전부 0건이다((9)).
  - **IL 은 「무엇을 만드나」를 말하고, 할당 바이트는 「얼마인가」를 말한다** — 둘 다 있어야 한다.
  - **할당 바이트의 절댓값은 판을 탄다** — **대소 관계만 네 판에서 같았다**((6)).

### ★ 진단이 0줄인 것도 블록으로 받았다

(9)가 그 자리다. **탐침 여덟 중 답한 것 0 · 침묵한 것 8**이고 **`cc exit=0`** 이다.\
그 침묵을 메우는 것이 (5)의 IL 과 (6)의 바이트다.

## 언제 쓰고 언제 안 쓰나

| 상황 | 고르는 것 | 왜 |
|---|---|---|
| 짧은 목록을 넘긴다 | ★★ **`ReadOnlySpan<T>` 또는 `Span<T>` 로 받는 API** | **0바이트**((6)) |
| 배열이 필요하다 | **`int[] x = [ … ]`** | 배열 하나뿐 — 40바이트 |
| 나중에 추가한다 | **`List<T> x = [ … ]`** | `Capacity` 가 **정확히 맞는다**((3)) |
| 밖으로 내보내되 못 고치게 한다 | ★ **`IEnumerable<T>` 로 받는다** | 읽기 전용 감싸개가 붙는다((4)) — 대신 **+24바이트** |
| 빈 컬렉션을 돌려준다 | ★★★ **`int[] x = []`** | `Array.Empty` 재사용 — **0바이트**((6)) |
| 빈 `List` 를 돌려준다 | ★ **그래도 32바이트는 낸다** | 객체를 만들어야 한다((6)) |
| 내 타입에 `{ … }` 를 붙이고 싶다 | **`IEnumerable` + `Add`** | 둘 다 필요하다((2)) |
| `Dictionary` 를 적는다 | ★★ **`["k"] = v`(덮기) 또는 `{ "k", v }`(중복 시 던지기)** | **중복 키에서 갈린다**((3)) |
| 정수 범위를 펼친다 | **`[..Enumerable.Range(1, 3)]`** | `Range` 는 열거 가능하지 않다((8)) |

- ★ **「컬렉션 식으로 바꾸면 무조건 빨라진다」가 아니다.** `List` 판은 **바이트가 같았고**((6)),\
  달라진 것은 **`Capacity` 와 `Add` 호출 유무**였다.

## 핵심 문장

- **컬렉션 식 `[…]` 은 대상 타입이 무엇을 만들지 정한다** — 오른쪽이 같아도 **일곱 가지 다른 IL** 이 나온다.
- **`Span<int> x = [1, 2, 3]` 은 힙을 한 바이트도 안 쓴다.**
- **`List<int> x = [1, 2, 3]` 은 `Add` 를 한 번도 안 부른다** — `Capacity` 가 3 대 4 로 그 자국을 남긴다.
- **빈 `[]` 는 배열·인터페이스·`Span` 에서 0바이트이고, `List<T>` 에서만 32바이트다.**
- **컬렉션 초기화자는 `IEnumerable` 과 `Add` 둘 다 요구하고, `Add` 는 확장 메서드여도 된다.**
- **할당 바이트의 절댓값은 판을 탄다** — 네 판에서 같았던 것은 **대소 관계**뿐이다.
- **`..` 가 어디까지 묶이는지는 값이 아니라 진단의 `(행,열)` 로 증명한다.**

## 관련 자료

- [10번](../10-collection-choosing-list-dictionary-hashset-queue-stack/) — **무엇을 고르나**. 여기는 **어떻게 채우나**까지.\
  ★ 「넣는 법 셋」(`[k]=v`·`Add`·`TryAdd`)이 거기가 정본이고, (3)은 **그중 둘이 문법 두 꼴이 된 것**만 본다.
- [03번](../03-boxing-and-unboxing/) — **`cs-il.cs` 전문과 할당 바이트 측정법**이 거기서 왔다. **컴파일러가 침묵하는 주제**라는 성질도 같다.
- [09번](../09-arrays-index-and-range/) — **`..` 는 거기서 범위 연산자**다. (8)이 그 짝이다.
- [04번](../04-var-and-target-typed-new/) — **타겟 타입 `new`**. (7)의 `CS9176` 이 같은 집안이다.
- [01번](../01-value-types-and-reference-types/) — 값 타입과 참조 타입. `Span<T>` 가 스택에 사는 이유의 토대.
- 목록의 **46번 주제** — `Span<T>`·`Memory<T>`·`stackalloc` 의 전모. (6)의 0바이트가 거기서 설명된다.
- 목록의 **31번 주제** — `IEnumerable<T>` 와 `foreach`. (4)의 `<>z__ReadOnlyArray` 가 거기로 이어진다.
- 목록의 **19번 주제** — `Equals`/`GetHashCode` 계약. `Dictionary` 키의 중복 판정이 거기가 정본이다.
- C++ 갈래 목록([`cpp/syntax/README.md`](../../../cpp/syntax/README.md))의 **4번**([`04-brace-initialization-narrowing-and-initializer-list/`](../../../cpp/syntax/04-brace-initialization-narrowing-and-initializer-list/)) —\
  ★ **C++ 의 `{}` 초기화와 `std::initializer_list`**. **거기는 `{}` 가 타입을 좁히는 검사까지 하고**,\
  **여기는 `[]` 가 대상 타입에서 타입을 받는다** — **방향이 반대**다.

## 용어 풀이

> **객체 초기화자(object initializer)** — `new T { P = v, … }`. **생성자가 끝난 뒤** 프로퍼티를 채운다.\
> 예: `new Point { X = 1, Y = 2 }` — IL 에서 `newobj` → `dup` → `set_X` 순이다((1)).

> **컬렉션 초기화자(collection initializer)** — `new T { a, b }`. **`Add` 를 원소마다 부른다.**\
> 예: `new List<int> { 1, 2 }` — `Add(1)`, `Add(2)`.

> **인덱스 초기화자(index initializer)** — `new T { [k] = v }`. **인덱서 `set_Item` 을 부른다**(C# 6).\
> 예: `new Dictionary<string,int> { ["a"] = 1 }` — ★ 중복 키를 **조용히 덮는다**((3)).

> **컬렉션 식(collection expression)** — C# 12 의 `[…]`. **대상 타입이 무엇을 만들지 정한다.**\
> 예: `Span<int> s = [1, 2, 3];` — **힙을 안 쓴다**((6)).

> **대상 타입(target type)** — 식이 놓인 자리가 요구하는 타입.\
> 예: `List<int> l = [1, 2, 3];` 의 `List<int>`. ★ **없으면 `CS9176`** 이다((7)).

> **스프레드 원소(spread element)** — `..식`. 그 컬렉션의 원소를 그 자리에 펼친다.\
> 예: `[1, 2, ..other]` — ★ IL 은 `Add` 가 아니라 **`CopyTo`** 다((5)).

> **인라인 배열(inline array)** — 고정 길이 배열을 **구조체 안에 통째로** 박아 넣는 것(.NET 8).\
> 예: `Span<int> s = [1, 2, 3]` 이 `InlineArray3<int>` 라는 **지역 변수**로 풀린다((5)).

> **`CollectionsMarshal.SetCount`** — `List<T>` 의 개수를 **직접** 정하는 API.\
> 예: 컬렉션 식이 `List` 를 만들 때 이것으로 길이를 맞추고 span 에 직접 쓴다((5)).

> **`Array.Empty<T>()`** — 길이 0 배열 **하나를 재사용**하는 BCL 캐시.\
> 예: `int[] x = []` 이 **그것과 같은 객체**였다(`True` — (4)).

> **티어드 JIT(tiered compilation)** — 처음에는 빨리 컴파일하고(tier-0), 자주 불리면 다시 최적화(tier-1)하는 것.\
> 예: (6)에서 **승격이 오기 전 tier-0 판**과 **`DOTNET_TieredCompilation=0` 판**의 바이트가 달랐다.

## 더 들어가면

- **컬렉션 식과 빌더 패턴** — `[CollectionBuilder]` 특성으로 **내 타입도 `[…]` 으로 만들게** 할 수 있다.\
  이 문서는 **BCL 타입에만** 던졌다.
- **`params` 컬렉션(C# 13)** — `params ReadOnlySpan<int>` 를 받는 메서드. (6)의 0바이트 경로와 같은 집안이다.
- **`ImmutableArray<T>`** — (6)에서 **112바이트**였다. 정본은 별도 주제가 없어 **이 문서의 관찰까지**다.
- **`<PrivateImplementationDetails>`** — 컴파일러가 상수 데이터를 모아 두는 숨은 타입.\
  필드 이름이 **내용의 해시**라 **흔들리는 칸**이다.
