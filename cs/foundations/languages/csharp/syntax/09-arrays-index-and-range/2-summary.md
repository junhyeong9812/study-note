# csharp/syntax/09 — 배열과 인덱스·범위 연산자(C# 8) — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [ECMA-334 7판(2023-12)](https://ecma-international.org/publications-and-standards/standards/ecma-334/) · [Microsoft Learn — C# 언어 레퍼런스](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/) · [Learn — 배열](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/builtin-types/arrays) · [Learn — 멤버 접근 연산자와 식(`^`·`..`)](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/operators/member-access-operators) · [Learn — 연산자 우선순위](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/operators/) · [.NET API — `System.Index`](https://learn.microsoft.com/en-us/dotnet/api/system.index) · [.NET API — `System.Range`](https://learn.microsoft.com/en-us/dotnet/api/system.range)
> **실행 검증** — 이 문서의 모든 출력·진단·IL·할당 바이트는 **.NET SDK 10.0.401** ·\
> 런타임 **`.NET 10.0.12`**(`Microsoft.NETCore.App`) · 타겟 **`net10.0`** · **linux-x64** 에서 실제로 돌려 얻은 것이다(2026-09-25).\
> ★ 블록은 캡처 스크립트가 파일로 받아 조립기가 끼워 넣은 것이다 — 사람이 옮겨 적은 줄은 하나도 없다.\
> ★ 소스 펜스의 배너도 **캡처가 찍은 것**이다. 원고에 손으로 쓴 배너는 없다.
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
> **`-debug` 를 안 줬다** — PDB 가 없으면 스택 트레이스에 **절대 경로와 줄 번호가 안 박힌다**.\
> 그래서 이 문서의 트레이스는 ``at Program.<Main>$(String[] args)`` 에서 끝나고, 어느 머신에서 돌려도 같다.
> **버전** — 배열은 **C# 1.0부터**. **인덱스 연산자 `^` 와 범위 연산자 `..` 는 C# 8부터**이고,\
> 그것을 받는 **`System.Index`·`System.Range` 타입은 .NET Core 3.0 / .NET Standard 2.1 부터**다.\
> `List<T>.Slice` 는 **.NET 8부터**라 그 판 이후에서만 `list[1..^1]` 이 컴파일된다((5)).
> **경계** — **동적 배열의 원리**(왜 두 배로 늘리나·상환 O(1))는 [`data-structure/01-dynamic-array/`](../../../../../data-structure/01-dynamic-array/)가 정본이다.\
> 여기는 **.NET 에서 무엇이 무엇으로 풀리고 무엇이 할당을 내나**만 본다.\
> **값 타입과 참조 타입**은 [01번](../01-value-types-and-reference-types/), **박싱**은 [03번](../03-boxing-and-unboxing/)이 정본이다.\
> **컬렉션 선택**은 목록의 **10번 주제**, **컬렉션 식 `[1, 2, ..other]`** 는 **11번 주제**,\
> **`Span<T>`·`Memory<T>` 자체**는 **46번 주제**, **인덱서 설계**는 **14번 주제**가 정본이다.
> **대비** — Rust 갈래 목록([`rust/syntax/README.md`](../../../rust/syntax/README.md))의 **15번**([`15-slices-ranges-and-utf8-boundaries/`](../../../rust/syntax/15-slices-ranges-and-utf8-boundaries/)) ·
> Python 갈래 목록([`python/syntax/README.md`](../../../python/syntax/README.md))의 **9번**([`09-sequence-ops-and-slicing/`](../../../python/syntax/09-sequence-ops-and-slicing/)) ·
> Go 갈래 목록([`go/syntax/README.md`](../../../go/syntax/README.md))의 **5번**([`05-arrays-vs-slices-value-and-header/`](../../../go/syntax/05-arrays-vs-slices-value-and-header/)).
>
> ★★ **흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | ★ `GC.GetAllocatedBytesForCurrentThread()` 의 **절댓값**(프로세스 시작부터의 누적이다) | ★★★ **두 호출 사이의 증분**과 **그 증분이 0 이냐 아니냐** |
> | 객체 주소 · `GetHashCode()` 값 · 빌드 시간 | **진단 코드**(`CS0019` 류) · **진단 문구** · ★★ **`(행,열)`** |
> | `dotnet` 패치 버전이 오르면 달라질 수 있는 바이트 수(40·48·72·88·168) | **`cc exit` 과 `run exit`**(갈라 적었다) |
> | — | ★★★ **IL 명령어 열**(`ldelem.i4` · `GetSubArray` · `Slice` · `Substring`) |

## 한눈에 — 쉽게 말하면

**배열을 `..` 로 자르는 것은 복사기로 그 대목을 뽑는 것**이고,\
**`Span<T>` 를 `..` 로 자르는 것은 그 대목에 책갈피 두 개를 꽂는 것**이다.

복사기는 **새 종이**가 나온다 — 거기에 낙서해도 원본은 멀쩡하고, 대신 **종이값**을 낸다.\
책갈피는 **종이가 안 생긴다** — 공짜인 대신, 거기에 낙서하면 **원본이 더러워진다.**

| 비유 | 실체 |
|---|---|
| **복사기로 뽑는다** | `int[] copy = a[1..^1];` — ★★★ **+40바이트**((3)) |
| **책갈피를 꽂는다** | `Span<int> view = a.AsSpan()[1..^1];` — ★★★ **+0바이트**((3)) |
| **복사본에 낙서해도 원본은 멀쩡** | `copy[0] = -1;` 뒤 `a[1]` 은 **20 그대로**((3)) |
| **책갈피 자리에 낙서하면 원본이 바뀐다** | `view[0] = -2;` 뒤 `a[1]` 이 **−2**((3)) |
| ★★ **복사기를 몰래 태우는 자리** | `Span<int> s = a[1..^1];` — **AsSpan() 을 빼먹으면 +40**((3)) |
| **뒤에서 몇 번째** | `a[^1]` — ★ 런타임 타입은 **`System.Index`**((2)) |
| ★★★ **끝 다음 자리** | `^0` 은 원소가 아니라 **길이 그 자체**다 — `a[^0]` 은 **던진다**((2)·(3)) |
| **쪽수 범위** | `1..^1` — ★ 런타임 타입은 **`System.Range`**((2)) |

- ★★★ **이 주제의 중심 창은 「할당 바이트」다.** 「복사냐 뷰냐」는 **출력만 봐서는 안 갈린다** —\
  `a[1..^1]` 과 `a.AsSpan()[1..^1]` 은 **같은 값을 준다.** 갈리는 것은 **증분 바이트와 쓰기 결과**뿐이다.
- ★★★ **그 다음 창이 IL 이다.** `..` 하나가 **세 가지 다른 메서드**로 풀린다((4)) —\
  배열이면 `GetSubArray`(**복사**), `Span` 이면 `Slice`(**뷰**), `string` 이면 `Substring`(**복사**).
- ★★ **`^` 는 IL 에 아예 안 남는다.** `a[^1]` 은 `ldlen; ldc.i4.1; sub; ldelem.i4` 로 풀려\
  **`Index` 객체가 만들어지지 않는다**((4)). 「타입이 있다」와 「런타임에 그 타입이 쓰인다」는 다른 말이다.

```text
   int[] a = { 10, 20, 30, 40, 50 };

   앞 기준     0    1    2    3    4
             +----+----+----+----+----+
             | 10 | 20 | 30 | 40 | 50 |
             +----+----+----+----+----+
   끝 기준   ^5   ^4   ^3   ^2   ^1   ^0
                                       └─ ★★★ ^0 은 원소가 아니라 「끝 다음」 = Length(5)
                                          a[^0] 은 IndexOutOfRangeException ((2))

   a[^1] = 50        a[1..^1] = [20, 30, 40]        a[2..2] = [] (빈 배열, 예외 아님)
```

```text
   ★★★ 이 주제의 본체 — 같은 [20, 30, 40] 을 두 방법으로 얻으면

   int[] copy = a[1..^1];                  Span<int> view = a.AsSpan()[1..^1];

   a +----+----+----+----+----+            a +----+----+----+----+----+
     | 10 | 20 | 30 | 40 | 50 |              | 10 | 20 | 30 | 40 | 50 |
     +----+----+----+----+----+              +----+----+----+----+----+
            |    |    |                             ^              ^
            v    v    v  (값 복사)                   |              |
  copy +----+----+----+                     view  (참조 + 시작 1 + 길이 3)
       | 20 | 30 | 40 |  ← 새 배열 +40바이트        ← 새 저장소 없음 +0바이트
       +----+----+----+

   copy[0] = -1  →  a[1] 은 20 그대로        view[0] = -2  →  a[1] 이 -2 로 바뀐다
```

> **인덱스 연산자 `^`**(index-from-end operator) — **끝에서 몇 번째**인지를 나타내는 **접두 단항 연산자**.\
> 예: `a[^1]` 은 마지막 원소다. `^n` 은 `a[a.Length - n]` 과 같다.

> **범위 연산자 `..`**(range operator) — **시작과 끝**을 묶어 `System.Range` 를 만드는 **이항 연산자**.\
> 예: `a[1..^1]` 은 「1번부터 끝 바로 앞까지」다. **끝은 포함하지 않는다**(half-open).

> **뷰(view)** — 데이터를 복사하지 않고 **원본의 한 구간을 가리키기만 하는 것**.\
> 예: `Span<int>` 는 「어느 배열의 몇 번째부터 몇 개」라는 정보만 든다 — 원소는 원본에 그대로 있다.

> **`System.Index` · `System.Range`** — `^`·`..` 의 결과를 담는 **구조체**. 값 타입이라 힙을 안 쓴다.\
> 예: `var i = ^1;` 의 `i` 는 `System.Index` 이고 `i.Value == 1`, `i.IsFromEnd == true` 다((2)).

## 이 주제가 답하려는 질문

1. **`a[1..^1]` 이 무엇을 만드나** — 복사인가 뷰인가, 그리고 **어느 창으로 그것을 가르나**((3)).
2. **`^`·`..` 가 문법인가 타입인가** — `var i = ^1;` 의 타입은 무엇이고 IL 에는 무엇이 남나((2)·(4)).
3. **내 타입에 이것을 달려면 무엇이 필요한가** — 그리고 **못 다는 타입은 무엇이 없어서 그런가**((5)).

## 동작 방식

### (0) 이 주제가 쓰는 창

| 창 | 무엇을 보여 주나 | 이 주제에서 |
|---|---|---|
| ★★★ **할당 바이트** | ★★★ **복사냐 뷰냐** — 출력이 같은 둘을 가르는 유일한 창 | (3)·(6) |
| ★★ **IL** | `..` 하나가 어느 메서드로 풀리나 · **`^` 는 아예 안 남는 것** | (4) |
| ★★ **컴파일 진단** | 내 타입에 무엇이 없어서 안 되나((5)) · ★★ **결합 방향**을 `(행,열)`로((7)) | (5)·(6)·(7) |
| **예외 전문** | `a[^0]` 이 **런타임에** 터지는 것 — 컴파일러는 안 막는다 | (2) |
| **실행 출력** | `Index`·`Range` 의 속성값 · 범위 표기 대여섯 가지의 결과 | (1)·(2)·(5)·(6) |

- ★ **부적용인 창 — 없다.** 이 주제는 **다섯 창을 전부 쓴다.**\
  ★★ 「안 쟀다」가 아니라 **다섯 자리가 각각 다른 것을 말한다** — 할당 바이트가 (3)을, IL 이 (4)를,\
  진단이 (5)·(7)을, 예외가 (2)를, 출력이 나머지를 맡는다. **하나를 빼면 그 절의 근거가 없어진다.**
- ★★★ **특히 「출력」만으로는 이 주제의 결론이 안 난다.** `a[1..^1]` 과 `a.AsSpan()[1..^1]` 은\
  **같은 세 숫자를 준다.** 복사와 뷰를 가르는 것은 **증분 바이트**와 **쓰기 뒤의 원본**뿐이다.
- **IL 은 외부 도구 없이 얻었다.** `ilspycmd`·`ildasm` 을 깔지 않았고, [03번](../03-boxing-and-unboxing/)의 (0)절에 있는\
  `cs-il.cs`(BCL 의 `MethodBody.GetILAsByteArray()` + `OpCodes` 리플렉션)를 **그대로 재사용**했다.\
  덤프는 `-optimize` 없이 낸 것이라 `nop` 이 섞이고 소스 구조가 그대로 보인다.

### (1) 배열은 참조 타입이다

**언제 쓰나** — `int[]` 를 메서드에 넘기기 전에, 그리고 `=` 로 다른 변수에 담기 전에.

```text
===== 소스: cs09b-ref.cs =====
using System;

int[] a = { 10, 20, 30, 40, 50 };
int[] b = a;                       // 참조만 복사된다
b[0] = 999;

Console.WriteLine($"typeof(int[]).IsValueType      : {typeof(int[]).IsValueType}");
Console.WriteLine($"typeof(int[]).BaseType         = {typeof(int[]).BaseType}");
Console.WriteLine($"typeof(int[]).IsArray          : {typeof(int[]).IsArray}");
Console.WriteLine($"typeof(int[]).GetElementType() = {typeof(int[]).GetElementType()}");
Console.WriteLine($"a is System.Collections.IList  : {a is System.Collections.IList}");
Console.WriteLine();
Console.WriteLine($"ReferenceEquals(a, b)          : {ReferenceEquals(a, b)}");
Console.WriteLine($"b[0] = 999 뒤 a[0]             : {a[0]}");
Console.WriteLine($"a.Length                       : {a.Length}   a.Rank : {a.Rank}");

Bump(a);
Console.WriteLine($"Bump(a) 뒤 a[1]                : {a[1]}   ← 메서드가 원본을 바꿨다");

int[] c = (int[])a.Clone();
c[1] = -1;
Console.WriteLine($"Clone() 뒤 a[1]={a[1]} c[1]={c[1]}  ReferenceEquals={ReferenceEquals(a, c)}");

int[] fresh = new int[3];
Console.WriteLine($"new int[3] 의 원소            : [{string.Join(", ", fresh)}]  ← 0 으로 채워진다");
string[] strs = new string[2];
Console.WriteLine($"new string[2] 의 원소         : [{(strs[0] is null ? "null" : strs[0])}, {(strs[1] is null ? "null" : strs[1])}]");

static void Bump(int[] arr) { arr[1] += 1; }
===== csc -out:ex.dll cs09b-ref.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
typeof(int[]).IsValueType      : False
typeof(int[]).BaseType         = System.Array
typeof(int[]).IsArray          : True
typeof(int[]).GetElementType() = System.Int32
a is System.Collections.IList  : True

ReferenceEquals(a, b)          : True
b[0] = 999 뒤 a[0]             : 999
a.Length                       : 5   a.Rank : 1
Bump(a) 뒤 a[1]                : 21   ← 메서드가 원본을 바꿨다
Clone() 뒤 a[1]=21 c[1]=-1  ReferenceEquals=False
new int[3] 의 원소            : [0, 0, 0]  ← 0 으로 채워진다
new string[2] 의 원소         : [null, null]
```

- ★★★ **`typeof(int[]).IsValueType` 이 `False`** 이고 **`BaseType` 이 `System.Array`** 다.\
  원소가 `int`(값 타입)여도 **배열 자체는 힙 객체**다 — [01번](../01-value-types-and-reference-types/)의 이분이 여기 그대로 적용된다.
- ★★ **`int[] b = a;` 는 원소를 복사하지 않는다.** `ReferenceEquals(a, b)` 가 `True` 이고,\
  `b[0] = 999` 가 `a[0]` 을 바꿨다. **배열 대입은 참조 대입이다.**
- ★★ **메서드에 넘겨도 같다.** `Bump(a)` 가 `a[1]` 을 20에서 21로 바꿨다 —\
  `ref` 를 안 붙여도 **가리키는 배열의 내용**은 바뀐다(바뀌지 않는 것은 **`a` 라는 변수가 무엇을 가리키느냐**뿐이다).
- **복사가 필요하면 명시적으로 한다** — `Clone()`(얕은 복사) 또는 `a[..]`((3))·`Array.Copy`.
- **원소의 기본값은 그 타입의 `default`** 다 — `new int[3]` 은 `[0, 0, 0]`, `new string[2]` 는 `[null, null]`.\
  ★ `new string[2]` 가 널로 채워지는 것이 [06번](../06-nullable-reference-types/)이 **경고로 잡아 주지 못하는** 대표 자리다.
- **비용** — 대입·인자 전달은 **참조 하나(8바이트)** 복사다. 원소 수와 무관하게 O(1) 이다.

### (2) `Index`·`Range` 는 문법이 아니라 타입이다 — 그리고 `^0` 은 길이다

**언제 쓰나** — `^1` 을 변수에 담거나, 메서드 인자로 넘기거나, `a[^0]` 이 왜 터지는지 물을 때.

```text
===== 소스: cs09b-index.cs =====
using System;

var i = ^1;
var r = 1..^1;
Console.WriteLine($"var i = ^1;     i.GetType() = {i.GetType()}");
Console.WriteLine($"var r = 1..^1;  r.GetType() = {r.GetType()}");
Console.WriteLine($"typeof(Index).IsValueType : {typeof(Index).IsValueType}   typeof(Range).IsValueType : {typeof(Range).IsValueType}");
Console.WriteLine();

Index e1 = ^1, e0 = ^0, s2 = 2;
Console.WriteLine($"^1 : Value={e1.Value} IsFromEnd={e1.IsFromEnd}  ToString()='{e1}'");
Console.WriteLine($"^0 : Value={e0.Value} IsFromEnd={e0.IsFromEnd}  ToString()='{e0}'");
Console.WriteLine($" 2 : Value={s2.Value} IsFromEnd={s2.IsFromEnd}  ToString()='{s2}'");
Console.WriteLine($"Index.Start={Index.Start}  Index.End={Index.End}  (Index.End 의 IsFromEnd={Index.End.IsFromEnd})");
Console.WriteLine();

int len = 5;
Console.WriteLine($"^1.GetOffset(5) = {e1.GetOffset(len)}");
Console.WriteLine($"^0.GetOffset(5) = {e0.GetOffset(len)}   ← 길이와 같다");
Console.WriteLine($" 2.GetOffset(5) = {s2.GetOffset(len)}");
Console.WriteLine();

Console.WriteLine($"1..^1 : Start={r.Start} End={r.End}  ToString()='{r}'");
Console.WriteLine($"Range.All : Start={Range.All.Start} End={Range.All.End}  ToString()='{Range.All}'");
var ol = r.GetOffsetAndLength(5);
Console.WriteLine($"(1..^1).GetOffsetAndLength(5) = (offset={ol.Offset}, length={ol.Length})");
Console.WriteLine();

int[] a = { 10, 20, 30, 40, 50 };
Console.WriteLine($"a[^1]   = {a[^1]}     a[^5] = {a[^5]}");
Console.WriteLine($"a[1..^1] = [{string.Join(", ", a[1..^1])}]");
Console.WriteLine($"a[..2]   = [{string.Join(", ", a[..2])}]");
Console.WriteLine($"a[3..]   = [{string.Join(", ", a[3..])}]");
Console.WriteLine($"a[..]    = [{string.Join(", ", a[..])}]   ← 전체");
Console.WriteLine($"a[2..2]  = [{string.Join(", ", a[2..2])}] (길이 {a[2..2].Length})  ← 빈 배열, 예외가 아니다");
Console.WriteLine($"a[^3..^1] = [{string.Join(", ", a[^3..^1])}]");
===== csc -out:ex.dll cs09b-index.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
var i = ^1;     i.GetType() = System.Index
var r = 1..^1;  r.GetType() = System.Range
typeof(Index).IsValueType : True   typeof(Range).IsValueType : True

^1 : Value=1 IsFromEnd=True  ToString()='^1'
^0 : Value=0 IsFromEnd=True  ToString()='^0'
 2 : Value=2 IsFromEnd=False  ToString()='2'
Index.Start=0  Index.End=^0  (Index.End 의 IsFromEnd=True)

^1.GetOffset(5) = 4
^0.GetOffset(5) = 5   ← 길이와 같다
 2.GetOffset(5) = 2

1..^1 : Start=1 End=^1  ToString()='1..^1'
Range.All : Start=0 End=^0  ToString()='0..^0'
(1..^1).GetOffsetAndLength(5) = (offset=1, length=3)

a[^1]   = 50     a[^5] = 10
a[1..^1] = [20, 30, 40]
a[..2]   = [10, 20]
a[3..]   = [40, 50]
a[..]    = [10, 20, 30, 40, 50]   ← 전체
a[2..2]  = [] (길이 0)  ← 빈 배열, 예외가 아니다
a[^3..^1] = [30, 40]
```

| 쓴 것 | `Value` | `IsFromEnd` | `GetOffset(5)` | 읽는 법 |
|---|---|---|---|---|
| `^1` | 1 | `True` | **4** | 끝에서 첫 번째 = 앞에서 네 번째 |
| ★★★ `^0` | 0 | `True` | ★★★ **5** | **길이와 같다** — 원소가 아니다 |
| `2` | 2 | `False` | 2 | `int` 는 `Index` 로 **암묵 변환**된다 |

- ★★★ **`var i = ^1;` 의 타입이 `System.Index`** 이고 **`var r = 1..^1;` 의 타입이 `System.Range`** 다.\
  둘 다 **`IsValueType` 이 `True`** — 구조체다. **인덱싱 안에만 쓸 수 있는 문법이 아니라 1급 값**이다.
- ★★★ **`^0` 의 `GetOffset(5)` 가 5** 다. 길이 5인 배열에 5번 원소는 없으므로 **`a[^0]` 은 반드시 터진다.**\
  ★ **컴파일러는 이것을 안 막는다** — 아래 블록이 `cc exit=0 · run exit=134` 다.\
  ★★ 그런데 **범위의 끝으로는 `^0` 이 정상**이다(`a[3..^0]` = `a[3..]`). **끝은 포함하지 않기 때문**이다.
- ★ **`Index.End` 가 `^0` 이고 `Index.Start` 가 `0`** 이다. `Range.All` 은 `0..^0` 으로 찍힌다.
- **`Range.GetOffsetAndLength(5)`** 가 `(offset=1, length=3)` 을 준다 —\
  ★ 내 타입에 `Slice(int, int)` 를 달 때 **이 메서드가 다리**가 된다((5)).
- ★★ **`a[2..2]` 는 예외가 아니라 빈 배열**이다(길이 0). Python 의 슬라이싱과 같은 성질이고,\
  **인덱싱**(`a[^0]`)과 **슬라이싱**(`a[5..5]`)의 경계 규칙이 **다르다**는 뜻이다.
```text
===== 소스: cs09b-end0.cs =====
using System;

int[] a = { 10, 20, 30, 40, 50 };
Console.WriteLine(a[^0]);
===== csc -out:ex.dll cs09b-end0.cs && dotnet ex.dll (cc exit=0 · run exit=134) =====
Unhandled exception. System.IndexOutOfRangeException: Index was outside the bounds of the array.
   at Program.<Main>$(String[] args)
```

- ★★★ **컴파일은 통과하고 런타임에 죽는다** — `cc exit=0` 인데 `run exit=134` 다.\
  `^` 는 산술로 풀리는 것이라((4)) 컴파일러가 보기에 `a[a.Length - 0]` 과 다를 바 없고,\
  **배열 인덱스 검사는 런타임의 일**이다. ★ 상수라 잡힐 것 같은데 **안 잡힌다.**
- ★ **메시지에 `^` 의 흔적이 없다** — `Index was outside the bounds of the array.` 뿐이다.\
  `-debug` 를 안 줘서 줄 번호도 없다. **이 예외만 보고 `^0` 을 의심하기는 어렵다.**
- **비용** — `Index`·`Range` 는 구조체라 **힙을 안 쓴다.** (3)의 측정이 그것을 확인한다.

### (3) ★★★ 배열의 `..` 는 복사, `Span<T>` 의 `..` 는 뷰 — 이 주제의 본체

**언제 쓰나** — 루프 안에서 자를 때. 그리고 **「왜 GC 가 도나」를 추적할 때.**

```text
===== 소스: cs09b-alloc.cs =====
using System;

Warm();

int[] a = { 10, 20, 30, 40, 50 };

long b0 = GC.GetAllocatedBytesForCurrentThread();
int[] copy = a[1..^1];                        // 배열의 .. — 새 배열
long b1 = GC.GetAllocatedBytesForCurrentThread();
Span<int> view = a.AsSpan()[1..^1];           // Span 의 .. — 뷰
long b2 = GC.GetAllocatedBytesForCurrentThread();
int one = a[^1];                              // 끝 기준 인덱싱
long b3 = GC.GetAllocatedBytesForCurrentThread();
int[] whole = a[..];                          // 전체 범위
long b4 = GC.GetAllocatedBytesForCurrentThread();
int[] none = a[2..2];                         // 빈 범위
long b5 = GC.GetAllocatedBytesForCurrentThread();
Span<int> sneaky = a[1..^1];                  // Span 에 받아도 배열 인덱서가 먼저 돈다
long b6 = GC.GetAllocatedBytesForCurrentThread();
string s = "abcdef";
string sub = s[1..^1];                        // string 의 .. — Substring
long b7 = GC.GetAllocatedBytesForCurrentThread();
ReadOnlySpan<char> chars = s.AsSpan()[1..^1]; // ReadOnlySpan 의 .. — 뷰
long b8 = GC.GetAllocatedBytesForCurrentThread();

Console.WriteLine($"int[] copy   = a[1..^1]            : +{b1 - b0} 바이트");
Console.WriteLine($"Span<int>    = a.AsSpan()[1..^1]   : +{b2 - b1} 바이트");
Console.WriteLine($"int one      = a[^1]               : +{b3 - b2} 바이트");
Console.WriteLine($"int[] whole  = a[..]               : +{b4 - b3} 바이트");
Console.WriteLine($"int[] none   = a[2..2]             : +{b5 - b4} 바이트  (길이 {none.Length})");
Console.WriteLine($"Span<int>    = a[1..^1]            : +{b6 - b5} 바이트  ← AsSpan() 을 안 거쳤다");
Console.WriteLine($"string sub   = s[1..^1]            : +{b7 - b6} 바이트  (\"{sub}\")");
Console.WriteLine($"ROSpan<char> = s.AsSpan()[1..^1]   : +{b8 - b7} 바이트  (길이 {chars.Length})");
Console.WriteLine();

copy[0] = -1;
Console.WriteLine($"copy[0] = -1 뒤  a[1] = {a[1]}   ← 원본이 안 바뀐다");
view[0] = -2;
Console.WriteLine($"view[0] = -2 뒤  a[1] = {a[1]}   ← 원본이 바뀐다");
sneaky[0] = -3;
Console.WriteLine($"sneaky[0] = -3 뒤 a[1] = {a[1]}   ← 안 바뀐다 (복사본을 보고 있다)");
Console.WriteLine($"a = [{string.Join(", ", a)}]  one={one}  whole.Length={whole.Length}");
Console.WriteLine($"ReferenceEquals(a, a[..]) : {ReferenceEquals(a, a[..])}");
Console.WriteLine();

long c0 = GC.GetAllocatedBytesForCurrentThread();
for (int k = 0; k < 1000; k++) { int[] t = a[1..^1]; GC.KeepAlive(t); }
long c1 = GC.GetAllocatedBytesForCurrentThread();
int acc = 0;
long d0 = GC.GetAllocatedBytesForCurrentThread();
for (int k = 0; k < 1000; k++) { Span<int> t = a.AsSpan()[1..^1]; acc += t[0]; }
long d1 = GC.GetAllocatedBytesForCurrentThread();
Console.WriteLine($"배열 슬라이스 1000번 : +{c1 - c0} 바이트");
Console.WriteLine($"Span 슬라이스 1000번 : +{d1 - d0} 바이트   (acc={acc})");

static void Warm() {
    int[] w = { 1, 2, 3 };
    int[] wc = w[0..2];
    Span<int> ws = w.AsSpan()[0..2];
    string wsx = "abc"[0..2];
    ReadOnlySpan<char> wrs = "abc".AsSpan()[0..2];
    GC.KeepAlive(wc); GC.KeepAlive(wsx);
    GC.KeepAlive(ws.Length + wrs.Length);
    GC.GetAllocatedBytesForCurrentThread();
}
===== csc -out:ex.dll cs09b-alloc.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
int[] copy   = a[1..^1]            : +40 바이트
Span<int>    = a.AsSpan()[1..^1]   : +0 바이트
int one      = a[^1]               : +0 바이트
int[] whole  = a[..]               : +48 바이트
int[] none   = a[2..2]             : +0 바이트  (길이 0)
Span<int>    = a[1..^1]            : +40 바이트  ← AsSpan() 을 안 거쳤다
string sub   = s[1..^1]            : +32 바이트  ("bcde")
ROSpan<char> = s.AsSpan()[1..^1]   : +0 바이트  (길이 4)

copy[0] = -1 뒤  a[1] = 20   ← 원본이 안 바뀐다
view[0] = -2 뒤  a[1] = -2   ← 원본이 바뀐다
sneaky[0] = -3 뒤 a[1] = -2   ← 안 바뀐다 (복사본을 보고 있다)
a = [10, -2, 30, 40, 50]  one=50  whole.Length=5
ReferenceEquals(a, a[..]) : False

배열 슬라이스 1000번 : +40000 바이트
Span 슬라이스 1000번 : +0 바이트   (acc=-2000)
```

| 쓴 것 | 증분 | 읽는 법 |
|---|---|---|
| `int[] copy = a[1..^1]` | ★★★ **+40** | 헤더 16 + 길이 8 + `int` 3개 12 → 정렬해 40 |
| ★★★ `Span<int> = a.AsSpan()[1..^1]` | ★★★ **+0** | **저장소를 안 만든다** — 참조·시작·길이뿐 |
| `int one = a[^1]` | **+0** | `^` 는 산술로 풀린다((4)) |
| `int[] whole = a[..]` | **+48** | ★ **전체 범위도 새 배열이다** — `ReferenceEquals` 가 `False` |
| `int[] none = a[2..2]` | ★★ **+0** | **빈 배열은 재사용된다**(`Array.Empty<T>()`) |
| ★★ `Span<int> = a[1..^1]` | ★★★ **+40** | **`AsSpan()` 을 빼먹으면 배열 인덱서가 먼저 돈다** |
| `string sub = s[1..^1]` | **+32** | `Substring` — 문자열도 **복사**다((4)) |
| `ROSpan<char> = s.AsSpan()[1..^1]` | **+0** | 문자열에도 뷰가 있다 |
| 배열 슬라이스 **1000번** | **+40000** | ★ **하나도 재사용되지 않는다** |
| `Span` 슬라이스 **1000번** | ★★★ **+0** | **루프에서 갈리는 것이 이것이다** |

- ★★★ **출력만 보면 둘이 같다.** `copy` 도 `view` 도 `[20, 30, 40]` 이다.\
  **갈리는 것은 증분 바이트와 「쓰면 원본이 바뀌나」뿐**이고, 그래서 **할당 바이트가 이 주제의 중심 창**이다.
- ★★★ **쓰기가 결론을 못 박는다** — `copy[0] = -1` 뒤 `a[1]` 은 **20 그대로**이고,\
  `view[0] = -2` 뒤 `a[1]` 은 **−2** 다. **복사는 끊어져 있고 뷰는 이어져 있다.**
- ★★★ **가장 조용한 함정은 `Span<int> sneaky = a[1..^1];`** 다. **+40바이트**가 났고,\
  `sneaky[0] = -3` 이 원본을 **안 바꿨다.** `int[]` → `Span<int>` 암묵 변환이 있어 **컴파일은 되지만**,\
  **배열 인덱서가 먼저 돌아 복사본을 만든 뒤** 그 복사본 위에 span 을 얹은 것이다.\
  ★ **「Span 에 받았으니 공짜겠지」가 여기서 깨진다** — 공짜로 만드는 것은 **`AsSpan()` 을 먼저 부르는 것**이다.
- ★★ **`a[2..2]` 가 +0** 인 것은 **런타임 구현**이다(길이 0이면 `Array.Empty<T>()` 를 준다).\
  ★ **언어가 보장하는 것은 「빈 배열이 나온다」까지**이고 「새로 안 만든다」는 관찰이다.
- ★ **`a[..]` 가 +48** 인 것이 이 표에서 가장 자주 놓치는 칸이다. **전체 범위는 「아무 일도 안 함」이 아니라 「전부 복사」다**.\
  ★ 그래서 `a[..]` 는 **배열을 복사하는 가장 짧은 문법**이기도 하다((1)의 `Clone()` 과 같은 일을 한다).
- **비용** — 배열 `..` 은 **O(잘린 길이)** 시간에 **O(잘린 길이)** 힙. `Span` `..` 은 **O(1)** 시간에 **0바이트**.

### (4) IL — `..` 하나가 세 가지로 풀린다

**언제 쓰나** — 「여기서 복사가 나나?」를 **추측하지 않고** 볼 때.

```text
===== 소스: cs09b-il.cs =====
Il.Dump(typeof(Probe), "ArrIndex");
Il.Dump(typeof(Probe), "ArrRange");
Il.Dump(typeof(Probe), "SpanRange");
Il.Dump(typeof(Probe), "StrRange");

static class Probe {
    public static int    ArrIndex(int[] a) => a[^1];
    public static int[]  ArrRange(int[] a) => a[1..^1];
    public static System.Span<int> SpanRange(System.Span<int> s) => s[1..^1];
    public static string StrRange(string s) => s[1..^1];
}
===== csc -r:il.dll -out:ex.dll cs09b-il.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
--- Probe.ArrIndex ---
  IL_0000: ldarg.0
  IL_0001: dup
  IL_0002: ldlen
  IL_0003: conv.i4
  IL_0004: ldc.i4.1
  IL_0005: sub
  IL_0006: ldelem.i4
  IL_0007: ret
--- Probe.ArrRange ---
  IL_0000: ldarg.0
  IL_0001: ldc.i4.1
  IL_0002: call System.Index::op_Implicit
  IL_0007: ldc.i4.1
  IL_0008: ldc.i4.1
  IL_0009: newobj System.Index::.ctor
  IL_000e: newobj System.Range::.ctor
  IL_0013: call System.Runtime.CompilerServices.RuntimeHelpers::GetSubArray
  IL_0018: ret
--- Probe.SpanRange ---
  .locals [0] System.Span`1[[System.Int32, System.Private.CoreLib, Version=10.0.0.0, Culture=neutral, PublicKeyToken=7cec85d7bea7798e]]&
  IL_0000: ldarga.s 0
  IL_0002: stloc.0
  IL_0003: ldloc.0
  IL_0004: ldc.i4.1
  IL_0005: ldloc.0
  IL_0006: call System.Span<System.Int32>::get_Length
  IL_000b: ldc.i4.1
  IL_000c: sub
  IL_000d: ldc.i4.1
  IL_000e: sub
  IL_000f: call System.Span<System.Int32>::Slice
  IL_0014: ret
--- Probe.StrRange ---
  .locals [0] System.String
  IL_0000: ldarg.0
  IL_0001: stloc.0
  IL_0002: ldloc.0
  IL_0003: ldc.i4.1
  IL_0004: ldloc.0
  IL_0005: callvirt System.String::get_Length
  IL_000a: ldc.i4.1
  IL_000b: sub
  IL_000c: ldc.i4.1
  IL_000d: sub
  IL_000e: callvirt System.String::Substring
  IL_0013: ret
```

| 소스 | 핵심 IL | 읽는 법 |
|---|---|---|
| `a[^1]`(배열) | `ldlen` → `conv.i4` → `ldc.i4.1` → `sub` → `ldelem.i4` | ★★★ **`Index` 가 안 만들어진다** |
| `a[1..^1]`(배열) | ★★★ `RuntimeHelpers::GetSubArray` | **복사** — 새 배열을 돌려준다 |
| `s[1..^1]`(`Span`) | ★★★ `Span<System.Int32>::Slice` | **뷰** — 참조·시작·길이만 바꾼다 |
| `s[1..^1]`(`string`) | ★★★ `String::Substring` | **복사** — 새 문자열을 돌려준다 |

- ★★★ **`^` 는 IL 에 한 글자도 안 남는다.** `a[^1]` 이 `dup; ldlen; conv.i4; ldc.i4.1; sub; ldelem.i4` 다 —\
  **배열 길이를 읽어 빼는 산술**로 완전히 풀린다. ★ 「`Index` 라는 타입이 있다」는 (2)에서 사실이지만,\
  **배열 인덱싱에서는 그 타입이 런타임에 등장하지 않는다.** 둘은 다른 이야기다.
- ★★ **`..` 는 다르다** — `ArrRange` 에 `newobj System.Index::.ctor` 와 `newobj System.Range::.ctor` 가 찍혀 있다.\
  ★ 다만 **둘 다 구조체라 힙 할당이 아니다**((3)에서 배열 몫 40바이트만 났다).
- ★★★ **같은 `[1..^1]` 이 받는 쪽에 따라 세 메서드로 갈린다.** 이것이 (3)의 바이트 차이의 **원인**이다 —\
  `GetSubArray` 는 **`Array.Copy` 를 부르는 BCL 헬퍼**이고, `Span<T>.Slice` 는 **필드 셋을 새로 채우는 것**뿐이다.
- ★ **`Span` 쪽에도 `Range` 객체가 안 만들어진다** — 컴파일러가 `Slice(start, length)` 로 **미리 계산해** 넘긴다.
- **비용** — IL 을 읽는 값어치는 여기 있다: **소스에는 `Copy` 라는 글자가 없는데 IL 에는 있다.**

### (5) 내 타입에 `^`·`..` 를 달려면

**언제 쓰나** — 내가 만든 컬렉션·버퍼에 `[^1]`·`[1..^1]` 을 쓰고 싶을 때.

```text
===== 소스: cs09b-custom.cs =====
using System;
using System.Collections.Generic;

var bag = new Bag(new[] { 1, 2, 3, 4, 5 });
Console.WriteLine("Bag : Length + this[int] + Slice");
Console.WriteLine($"  bag[^1]    = {bag[^1]}");
Console.WriteLine($"  bag[1..^1] = {bag[1..^1]}");

var cnt = new Counted(new[] { 1, 2, 3, 4, 5 });
Console.WriteLine("Counted : Count + this[int] + Slice   ← Length 가 아니라 Count 다");
Console.WriteLine($"  cnt[^1]    = {cnt[^1]}");
Console.WriteLine($"  cnt[1..^1] = {cnt[1..^1]}");

var ex = new Explicit(new[] { 1, 2, 3, 4, 5 });
Console.WriteLine("Explicit : this[Index] · this[Range] 를 직접 받았다");
Console.WriteLine($"  ex[^2]   = {ex[^2]}");
Console.WriteLine($"  ex[1..3] = {ex[1..3]}");
Console.WriteLine($"  ex[2]    = {ex[2]}");

Console.WriteLine("List<int> : BCL 이 같은 계약을 만족하나?");
var list = new List<int> { 1, 2, 3, 4, 5 };
Console.WriteLine($"  List<int>.Slice 가 있나 : {typeof(List<int>).GetMethod("Slice") is not null}");
Console.WriteLine($"  list[^1]    = {list[^1]}");
var sub = list[1..^1];
Console.WriteLine($"  list[1..^1] = [{string.Join(", ", sub)}]  (타입 {sub.GetType().Name})");
sub[0] = -1;
Console.WriteLine($"  sub[0] = -1 뒤 list[1] = {list[1]}   ← 복사다");

class Bag {
    readonly int[] _items;
    public Bag(int[] items) => _items = items;
    public int Length => _items.Length;
    public int this[int i] => _items[i];
    public Bag Slice(int start, int length) => new Bag(_items[start..(start + length)]);
    public override string ToString() => "[" + string.Join(", ", _items) + "]";
}

class Counted {
    readonly int[] _items;
    public Counted(int[] items) => _items = items;
    public int Count => _items.Length;
    public int this[int i] => _items[i];
    public Counted Slice(int start, int length) => new Counted(_items[start..(start + length)]);
    public override string ToString() => "[" + string.Join(", ", _items) + "]";
}

class Explicit {
    readonly int[] _items;
    public Explicit(int[] items) => _items = items;
    public string this[Index i] => $"this[Index] 가 받았다 — {i} → {_items[i.GetOffset(_items.Length)]}";
    public string this[Range r] {
        get { var ol = r.GetOffsetAndLength(_items.Length); return $"this[Range] 가 받았다 — {r} → offset={ol.Offset} length={ol.Length}"; }
    }
}
===== csc -out:ex.dll cs09b-custom.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
Bag : Length + this[int] + Slice
  bag[^1]    = 5
  bag[1..^1] = [2, 3, 4]
Counted : Count + this[int] + Slice   ← Length 가 아니라 Count 다
  cnt[^1]    = 5
  cnt[1..^1] = [2, 3, 4]
Explicit : this[Index] · this[Range] 를 직접 받았다
  ex[^2]   = this[Index] 가 받았다 — ^2 → 4
  ex[1..3] = this[Range] 가 받았다 — 1..3 → offset=1 length=2
  ex[2]    = this[Index] 가 받았다 — 2 → 3
List<int> : BCL 이 같은 계약을 만족하나?
  List<int>.Slice 가 있나 : True
  list[^1]    = 5
  list[1..^1] = [2, 3, 4]  (타입 List`1)
  sub[0] = -1 뒤 list[1] = 2   ← 복사다
```

- ★★★ **암묵 지원의 계약은 두 줄이다.**\
  ★ `^` 를 받으려면 — **`int` 를 받는 인덱서** + **`Length` 또는 `Count` 라는 `int` 속성**.\
  ★ `..` 를 받으려면 — 거기에 **`Slice(int start, int length)`** 를 더한다.
- ★★ **`Length` 가 아니라 `Count` 여도 된다.** `Counted` 가 `Count` 만으로 `cnt[^1]`·`cnt[1..^1]` 둘 다 받았다.\
  ★ **`Size` 는 안 된다** — 이름이 그 둘 중 하나라야 한다((6)의 진단이 그것을 보인다).
- ★★ **명시 지원도 된다** — `this[Index]`·`this[Range]` 인덱서를 직접 선언하면 그쪽이 쓰인다.\
  `Explicit` 에서 `ex[2]` 도 `this[Index]` 로 갔다 — **`int` → `Index` 암묵 변환**이 있기 때문이다.\
  ★ 암묵 지원과 달리 **`Slice` 가 필요 없고**, 대신 `GetOffset`/`GetOffsetAndLength` 를 직접 불러야 한다((2)).
- ★★★ **BCL 도 이 계약으로 동작한다** — `List<int>` 에 **`Slice(int, int)` 가 있어서** `list[1..^1]` 이 컴파일된다.\
  ★★ **그 결과는 뷰가 아니라 `List<int>` 복사본**이다(`sub[0] = -1` 이 `list[1]` 을 안 바꿨다).\
  ★ **「`List<T>` 는 범위 연산자가 안 된다」는 낡은 문장**이다 — `List<T>.Slice` 는 **.NET 8부터**다.\
  **도구의 성질을 적을 때는 판과 확인 날짜를 같이 적는다**(이 판은 .NET 10.0.12 · 2026-09-25 확인).

```text
   내 타입에 무엇을 달면 무엇이 되나

   this[int]  +  Length 또는 Count                 →  [^1]      이 된다
       │                     │
       │                     └── 이름이 Size 면 안 된다 (CS1503, (6))
       │
       +  Slice(int start, int length)             →  [1..^1]   도 된다

   this[Index]                                     →  [^1]      이 된다 (Slice 불필요)
   this[Range]                                     →  [1..^1]   이 된다 (Slice 불필요)
```

### (6) 무엇이 없으면 안 되나 · 다차원 배열과 배열의 배열

**언제 쓰나** — 컴파일이 안 될 때 **무엇이 없어서인지** 가를 때. 그리고 2차원 데이터를 담을 그릇을 고를 때.

```text
===== 소스: cs09b-nolength.cs =====
using System;
using System.Collections.Generic;

var sz = new SizeOnly();
Console.WriteLine(sz[^1]);

var nosl = new NoSlice();
Console.WriteLine(nosl[^1]);
Console.WriteLine(nosl[1..^1]);

var set = new HashSet<int> { 1, 2, 3 };
Console.WriteLine(set[^1]);

class SizeOnly {
    public int Size => 3;
    public int this[int i] => i;
}

class NoSlice {
    public int Length => 3;
    public int this[int i] => i;
}
===== csc -out:ex.dll cs09b-nolength.cs (cc exit=1) =====
cs09b-nolength.cs(5,22): error CS1503: Argument 1: cannot convert from 'System.Index' to 'int'
cs09b-nolength.cs(9,24): error CS1503: Argument 1: cannot convert from 'System.Range' to 'int'
cs09b-nolength.cs(12,19): error CS0021: Cannot apply indexing with [] to an expression of type 'HashSet<int>'
```

| 진단 | 무엇이 없어서 | 읽는 법 |
|---|---|---|
| `CS1503`(`Index` → `int`) | `Size` 는 `Length`·`Count` 가 아니다 | ★ **인덱서는 있는데 길이 이름이 틀렸다** |
| `CS1503`(`Range` → `int`) | `Slice(int, int)` 가 없다 | ★ `^` 는 되는데 `..` 만 안 되는 자리 |
| `CS0021` | `HashSet<T>` 에는 인덱서가 아예 없다 | ★ **순서가 없는 컬렉션**에는 걸 자리가 없다 |

- ★★ **진단 문구가 계약을 그대로 읽어 준다** — 「`System.Index` 를 `int` 로 바꿀 수 없다」는\
  **컴파일러가 `int` 인덱서밖에 못 찾았다**는 뜻이다. 길이 속성을 못 찾으면 `^` 를 산술로 풀 수가 없다.

```text
===== 소스: cs09b-dims.cs =====
using System;

Warm();

long b0 = GC.GetAllocatedBytesForCurrentThread();
int[,] md = new int[3, 4];
long b1 = GC.GetAllocatedBytesForCurrentThread();
int[][] jag = new int[3][];
for (int i = 0; i < 3; i++) jag[i] = new int[4];
long b2 = GC.GetAllocatedBytesForCurrentThread();
int[] flat = new int[12];
long b3 = GC.GetAllocatedBytesForCurrentThread();

md[1, 2] = 7;
jag[1][2] = 7;

Console.WriteLine($"new int[3,4]                  : +{b1 - b0} 바이트");
Console.WriteLine($"new int[3][] + int[4] 셋       : +{b2 - b1} 바이트");
Console.WriteLine($"new int[12]                   : +{b3 - b2} 바이트");
Console.WriteLine();
Console.WriteLine($"int[,]  : Rank={md.Rank} Length={md.Length} GetLength(0)={md.GetLength(0)} GetLength(1)={md.GetLength(1)}");
Console.WriteLine($"int[][] : Rank={jag.Rank} Length={jag.Length} jag[0].Length={jag[0].Length}");
Console.WriteLine($"md.GetType()  = {md.GetType()}");
Console.WriteLine($"jag.GetType() = {jag.GetType()}");
Console.WriteLine($"md[1,2]={md[1, 2]}   jag[1][2]={jag[1][2]}");
Console.WriteLine();

jag[2] = new int[7];
Console.WriteLine($"jag[2] = new int[7] 뒤 jag[2].Length = {jag[2].Length}   ← 줄마다 길이가 달라도 된다");
Console.WriteLine($"jag[^1].Length = {jag[^1].Length}   ← 바깥 배열에는 ^ 가 된다");
Console.WriteLine($"jag[0..2].Length = {jag[0..2].Length}   ← 바깥 배열에는 .. 도 된다");
Console.WriteLine();

int total = 0;
foreach (int v in md) total += v;
Console.WriteLine($"foreach (int v in md) 의 합 = {total}   ← int[,] 는 원소를 직접 준다");
Console.WriteLine($"md 의 원소 수 {md.Length} = 3 × 4");
foreach (int[] row in jag) Console.WriteLine($"  foreach (int[] row in jag) — row.Length = {row.Length}   ← 줄을 준다");

static void Warm() {
    int[,] w = new int[2, 2];
    int[][] wj = new int[2][];
    wj[0] = new int[2]; wj[1] = new int[2];
    int[] wf = new int[4];
    GC.KeepAlive(w); GC.KeepAlive(wj); GC.KeepAlive(wf);
    GC.GetAllocatedBytesForCurrentThread();
}
===== csc -out:ex.dll cs09b-dims.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
new int[3,4]                  : +88 바이트
new int[3][] + int[4] 셋       : +168 바이트
new int[12]                   : +72 바이트

int[,]  : Rank=2 Length=12 GetLength(0)=3 GetLength(1)=4
int[][] : Rank=1 Length=3 jag[0].Length=4
md.GetType()  = System.Int32[,]
jag.GetType() = System.Int32[][]
md[1,2]=7   jag[1][2]=7

jag[2] = new int[7] 뒤 jag[2].Length = 7   ← 줄마다 길이가 달라도 된다
jag[^1].Length = 7   ← 바깥 배열에는 ^ 가 된다
jag[0..2].Length = 2   ← 바깥 배열에는 .. 도 된다

foreach (int v in md) 의 합 = 7   ← int[,] 는 원소를 직접 준다
md 의 원소 수 12 = 3 × 4
  foreach (int[] row in jag) — row.Length = 4   ← 줄을 준다
  foreach (int[] row in jag) — row.Length = 4   ← 줄을 준다
  foreach (int[] row in jag) — row.Length = 7   ← 줄을 준다
```

| | `int[3,4]`(다차원) | `int[3][]`(배열의 배열) |
|---|---|---|
| 할당 | ★ **+88바이트** — 객체 **하나** | ★ **+168바이트** — 객체 **넷** |
| `Rank` | **2** | **1**(바깥 배열이다) |
| `Length` | **12**(전체 원소 수) | **3**(줄 수) |
| 원소 접근 | `md[1, 2]` | `jag[1][2]` — **간접 참조가 둘** |
| 줄마다 다른 길이 | ★ **불가능** | ★ **가능**(`jag[2] = new int[7]`) |
| `^`·`..` | ★★ **못 쓴다**(아래 진단) | ★ **바깥 배열에는 된다** |
| `foreach` | **원소**를 준다 | **줄**(`int[]`)을 준다 |

```text
===== 소스: cs09b-dimsfail.cs =====
using System;

int[,] md = new int[3, 4];
Console.WriteLine(md[^1, 0]);
Console.WriteLine(md[0..1, 0]);
Console.WriteLine(md[^1]);

int[][] jag = new int[3][];
Console.WriteLine(jag[^1]);
===== csc -out:ex.dll cs09b-dimsfail.cs (cc exit=1) =====
cs09b-dimsfail.cs(4,22): error CS0029: Cannot implicitly convert type 'System.Index' to 'int'
cs09b-dimsfail.cs(5,22): error CS0029: Cannot implicitly convert type 'System.Range' to 'int'
cs09b-dimsfail.cs(6,19): error CS0022: Wrong number of indices inside []; expected 2
```

- ★★ **`int[,]` 에는 `^`·`..` 가 안 된다.** `md[^1, 0]` 이 `CS0029`(`Index` → `int` 암묵 변환 없음)이고\
  `md[0..1, 0]` 도 같은 모양이다. ★ **다차원 인덱서는 `int` 매개변수 둘을 직접 받는 언어 기능**이라\
  (5)의 계약(`Length` + `Slice`)이 **적용되지 않는다.**
- ★ **`md[^1]`(인덱스 하나)은 다른 진단이다** — `CS0022 Wrong number of indices inside []; expected 2`.\
  **차원 수가 먼저 걸린다.**
- ★★ **`int[3][]` 은 `+168` 로 다차원의 두 배 가까이 든다.** 객체가 **넷**(바깥 하나 + 줄 셋)이라\
  **객체 헤더를 네 번 낸다**((3)의 표와 같은 이유다). 대신 **줄마다 길이가 달라도 된다.**
- ★ **`new int[12]`(평평한 1차원)은 +72** 로 가장 싸다. 「행 × 열」을 직접 계산해 쓰는 방식이\
  **메모리로는 항상 이긴다** — 그 대신 인덱스 계산을 손으로 한다.
- **비용** — 다차원은 **곱셈 한 번**으로 주소를 낸다. 배열의 배열은 **참조를 두 번 따라간다**(캐시에 불리하다).\
  ★ 다만 **이 문서는 시간을 재지 않았다** — 여기서 근거로 쓴 것은 **바이트와 객체 수**뿐이다.

### (7) ★★ 결합 방향은 진단의 `(행,열)` 로 증명한다

**언제 쓰나** — `a[1..n-1]` 을 쓰려다 컴파일이 깨졌을 때. **값으로는 원리상 못 가르는 것**이다.

```text
===== 소스: cs09b-prec.cs =====
using System;

string s = "x";
var a = 0..1 - s;
var b = (0..1) - s;
var c = 0..(1 - s);
var d = ^1 - s;
var e = ^(1 - s);

int[] arr = { 10, 20, 30, 40, 50 };
var f = arr[1..arr.Length - 1];
Console.WriteLine($"{a} {b} {c} {d} {e} {f}");
===== csc -out:ex.dll cs09b-prec.cs (cc exit=1) =====
cs09b-prec.cs(4,9): error CS0019: Operator '-' cannot be applied to operands of type 'Range' and 'string'
cs09b-prec.cs(5,9): error CS0019: Operator '-' cannot be applied to operands of type 'Range' and 'string'
cs09b-prec.cs(6,13): error CS0019: Operator '-' cannot be applied to operands of type 'int' and 'string'
cs09b-prec.cs(7,9): error CS0019: Operator '-' cannot be applied to operands of type 'Index' and 'string'
cs09b-prec.cs(8,11): error CS0019: Operator '-' cannot be applied to operands of type 'int' and 'string'
cs09b-prec.cs(11,13): error CS0019: Operator '-' cannot be applied to operands of type 'Range' and 'int'
```

| 소스 | 진단의 열 | 어느 타입끼리 | 그래서 어떻게 묶였나 |
|---|---|---|---|
| `0..1 - s` | **9**(`0` 자리) | `Range` 와 `string` | ★★★ **`(0..1) - s`** |
| `(0..1) - s` | **9** | `Range` 와 `string` | 괄호를 친 것과 **결과가 같다** |
| `0..(1 - s)` | **13**(`1` 자리) | `int` 와 `string` | 괄호로 강제해야 이렇게 된다 |
| `^1 - s` | **9**(`^` 자리) | `Index` 와 `string` | **`(^1) - s`** |
| `^(1 - s)` | **11**(`1` 자리) | `int` 와 `string` | 괄호로 강제해야 이렇게 된다 |
| ★★ `arr[1..arr.Length - 1]` | **13** | ★★★ **`Range` 와 `int`** | **`(1..arr.Length) - 1`** |

- ★★★ **`..` 는 `-` 보다 세게 묶는다.** 진단 문구는 여섯 줄이 **전부 `CS0019` 에 같은 형식**이고,\
  **갈리는 것은 열과 피연산자 타입뿐**이다. 값으로는 이것을 가를 수가 없다 — **일부러 에러를 내야 보인다.**
- ★★★ **그 귀결이 실전의 함정이다** — `arr[1..arr.Length - 1]` 이 **컴파일되지 않는다.**\
  `(1..arr.Length) - 1` 로 묶여 「`Range` 에서 `int` 를 빼라」가 되기 때문이다.\
  ★ **고치는 법은 괄호다** — `arr[1..(arr.Length - 1)]`. 더 나은 법은 **`arr[1..^1]`** 이다.
- ★★ **Learn 의 연산자 우선순위표에서 `x..y` 가 곱셈·덧셈보다 위**에 있다. 이 진단이 그 표의 실증이다.
- ★ **`^` 는 단항이라 더 세게 묶는다** — `^1 - s` 가 `Index` 와 `string` 의 뺄셈이 됐다.
- **비용** — 없다. **컴파일 시점에 전부 끝난다.**

## 문법 — 형태와 규칙

**형태**

```text
   인덱스                                범위
   a[0]        앞에서 0번               a[1..3]     1번부터 3번 앞까지 (2개)
   a[^1]       끝에서 1번 (마지막)       a[1..]      1번부터 끝까지
   a[^n]       = a[a.Length - n]        a[..3]      처음부터 3번 앞까지
   a[^0]       ★ 터진다 (= a[a.Length]) a[..]       전부 (★ 복사본)
                                        a[1..^1]    양끝 하나씩 뺀 것
                                        a[^3..^1]   끝에서 3번째부터 끝에서 1번째 앞까지
                                        a[2..2]     빈 것 (예외 아님)

   Index i = ^1;       Range r = 1..^1;       ← 변수에 담을 수 있다 (구조체)
   int off = i.GetOffset(len);                ← 길이를 줘야 자리가 정해진다
   var (o, l) = r.GetOffsetAndLength(len);
```

**규칙**

- **범위의 끝은 포함하지 않는다**(half-open). `a[1..3]` 은 원소 **둘**이다.
- **`^0` 은 길이와 같다.** 인덱스로 쓰면 터지고, **범위의 끝으로 쓰면 정상**이다.
- **`int` 는 `Index` 로 암묵 변환된다.** 그래서 `a[2]` 와 `a[(Index)2]` 가 같다.
- **`Index`·`Range` 는 구조체다.** 변수·필드·매개변수에 담아도 힙을 안 쓴다.
- ★ **`..` 는 `-`·`+`·`*` 보다 세게 묶는다.** `1..n-1` 은 `(1..n)-1` 이다((7)).
- ★ **배열·`string` 의 `..` 는 복사, `Span<T>`·`ReadOnlySpan<T>` 의 `..` 는 뷰**다((3)).
- ★ **다차원 배열 `int[,]` 에는 `^`·`..` 가 없다**((6)).

**금지 사례**(전부 (5)·(6)·(7)에서 던져 확인한 것)

```text
   sz[^1]                  길이 속성 이름이 Size 다            → CS1503
   nosl[1..^1]             Slice(int, int) 가 없다             → CS1503
   set[^1]                 HashSet<T> 에 인덱서가 없다          → CS0021
   md[^1, 0]               다차원 배열에는 Index 를 못 준다     → CS0029
   md[^1]                  차원 수가 안 맞는다                 → CS0022
   arr[1..arr.Length - 1]  (1..Length) - 1 로 묶인다           → CS0019
   a[^0]                   컴파일은 된다 ★ 런타임에 터진다      → IndexOutOfRangeException
```

## 어디서 틀리나

- ★★★ **「Span 변수에 받으면 공짜」가 아니다.** `Span<int> s = a[1..^1];` 은 **+40바이트**이고\
  **원본과 끊어진다**((3)). 공짜로 만드는 것은 **`a.AsSpan()[1..^1]`** — `AsSpan()` 이 먼저다.
- ★★★ **`a[..]` 를 「아무 일도 안 함」으로 읽는 것.** **전부 복사**다(+48). 반대로 **복사가 목적이면 가장 짧은 문법**이다.
- ★★★ **`arr[1..arr.Length - 1]` 이 컴파일 안 된다**((7)). `..` 가 `-` 보다 세게 묶는다.\
  ★ 이 자리에서 괄호로 때우기 전에 **`arr[1..^1]` 을 먼저 떠올려라** — 그게 이 연산자가 있는 이유다.
- ★★ **`a[^0]` 을 「마지막 원소」로 읽는 것.** `^1` 이 마지막이고 **`^0` 은 길이**다((2)).\
  ★ **Python 의 `a[-1]` 에서 넘어오면 반드시 한 번 걸린다** — 거기서는 `-1` 이 마지막인데\
  여기서는 `^1` 이 마지막이다. **`^` 다음 숫자는 「뒤에서 몇 번째」이지 「음수 인덱스」가 아니다.**
- ★★ **루프 안에서 배열을 자르는 것.** 1000번에 **40000바이트**다((3)). `Span` 이면 **0** 이다.\
  ★ 그런데 **`Span<T>` 는 필드·`async` 메서드·`yield` 안에 못 둔다**(46번 주제) — 그래서 만능이 아니다.
- ★ **`int[][]` 을 「2차원 배열」이라 부르는 것.** `Rank` 가 **1** 이고 `Length` 가 **줄 수**다((6)).\
  ★ `jag[0]` 이 **널일 수 있다**는 것도 `int[,]` 에는 없는 실패 모드다.
- ★ **`Length` 대신 `Size`·`Count()` 를 쓴 타입에 `^` 가 안 되는 것.** `Count` **속성**은 되고\
  `Count()` **확장 메서드**는 안 된다 — 계약이 요구하는 것은 **속성**이다((5)).
- ★ **`Clone()` 이 얕은 복사인 것.** `string[]` 을 `Clone()` 하면 **참조가 복사**된다. 원소가 참조 타입이면\
  두 배열이 **같은 객체들**을 가리킨다([01번](../01-value-types-and-reference-types/)의 얕은/깊은 복사).

## 구현 세부사항 대 언어 보장

| | 누가 정하나 | 이 판의 관찰 |
|---|---|---|
| `^`·`..` 가 있다는 것 · **끝을 포함하지 않는다**는 것 | ★ **언어**(C# 8) | — |
| `Index`·`Range` 가 **구조체**인 것 | ★ **BCL 타입 정의** | `IsValueType` = `True`((2)) |
| 배열 `..` 이 **새 배열**인 것 | ★ **언어**(`GetSubArray` 로 번역된다고 명세가 정한다) | `ReferenceEquals` = `False`((3)) |
| `Span<T>` `..` 이 **뷰**인 것 | ★ **`Span<T>` 의 계약** | +0바이트((3)) |
| ★ **+40 · +48 · +88 · +168 같은 수** | ★★ **CoreCLR 의 객체 레이아웃** | x64 linux, .NET 10.0.12 |
| ★★ **빈 범위가 +0** 인 것 | ★★★ **런타임 구현**(`Array.Empty<T>()` 재사용) | +0((3)) |
| `a[^1]` 이 IL 에 **`Index` 없이** 풀리는 것 | ★ **Roslyn 의 로워링** | (4) — `-optimize` 없이 본 것 |
| `List<T>` 에 `Slice` 가 있는 것 | ★★ **BCL 의 판**(.NET 8부터) | `True`((5)) |
| `a[^0]` 이 **`IndexOutOfRangeException`** 인 것 | ★ **언어**(배열 인덱스 검사) | 메시지 문구는 구현 |

- ★★★ **「+0 이냐 아니냐」는 언어 보장이고 「+40 이냐」는 관찰이다.** 갈라 읽어라.\
  `Span<T>` 가 저장소를 안 만든다는 것은 **타입의 계약**이지만, 배열 헤더가 24바이트인 것은 **이 런타임의 수**다.
- ★★ **빈 범위 +0 은 언어가 보장하지 않는다.** 「빈 배열이 나온다」까지가 보장이다.

## 언제 쓰고 언제 안 쓰나

| 상황 | 무엇을 쓰나 | 왜 |
|---|---|---|
| 마지막 원소 하나 | `a[^1]` | ★ 할당 0 · `a.Length - 1` 보다 덜 틀린다 |
| 부분을 **읽기만** 하고 루프가 돈다 | ★★★ `a.AsSpan()[1..^1]` | **0바이트**((3)) |
| 부분을 **떼어 보관**해야 한다 | `a[1..^1]` | 원본이 바뀌어도 안 따라 바뀌어야 하니 복사가 맞다 |
| 부분을 **필드·`async`·`yield`** 에 담아야 한다 | `a[1..^1]` 또는 `Memory<T>` | ★ `Span<T>` 는 거기 못 들어간다(46번 주제) |
| 배열 전체 복사 | `a[..]` 또는 `Clone()` | 같은 일을 한다((3)·(1)) |
| 2차원 격자 · 줄 길이가 **같다** | `int[,]` | ★ 객체 **하나** — 메모리·캐시에 유리((6)) |
| 줄마다 길이가 **다르다** | `int[][]` | 다차원으로는 표현이 안 된다 |
| 크기가 계속 변한다 | ★ `List<T>` | **배열은 크기가 고정**이다 — 목록의 **10번 주제** |
| 문자열 일부를 **읽기만** | `s.AsSpan()[1..^1]` | `s[1..^1]` 은 **새 문자열**이다((3)) |

## 핵심 문장

- **배열은 참조 타입이다** — 원소가 값 타입이어도 그렇다. 대입·인자 전달은 참조 하나를 옮긴다((1)).
- **`^`·`..` 는 문법인 동시에 타입이다** — `Index`·`Range` 라는 **구조체**가 뒤에 있다((2)).\
  다만 **배열 인덱싱에서는 `^` 가 IL 에 남지 않는다**((4)). 「타입이 있다」와 「런타임에 쓰인다」는 다르다.
- ★★★ **`..` 는 받는 쪽이 무엇이냐에 따라 복사도 되고 뷰도 된다** — 배열·`string` 은 복사, `Span` 은 뷰다.\
  **출력으로는 못 가른다. 할당 바이트와 쓰기 결과로 가른다**((3)·(4)).
- **`^0` 은 원소가 아니라 길이다** — 인덱스로 쓰면 터지고 범위의 끝으로 쓰면 정상이다((2)).
- **`..` 는 `-` 보다 세게 묶는다** — `1..n-1` 은 `(1..n)-1` 이고, 그 증거는 **진단의 열**이다((7)).

## 관련 자료

- [`data-structure/01-dynamic-array/`](../../../../../data-structure/01-dynamic-array/) — ★ **동적 배열의 원리**(두 배 확장·상환 O(1))가 정본.\
  **그쪽은 「왜 그렇게 커지나」까지, 여기는 「.NET 에서 무엇이 할당을 내나」부터**다.
- [01번](../01-value-types-and-reference-types/) — 배열이 **참조 타입**인 것의 정본. 얕은 복사도 거기다.
- [03번](../03-boxing-and-unboxing/) — ★ 이 문서가 쓴 **`cs-il.cs`** 의 전문이 그 (0)절에 있다. 할당 바이트를 재는 법도 거기서 굳혔다.
- [06번](../06-nullable-reference-types/) — `new string[2]` 가 널로 채워지는 것을 **경고가 못 잡는** 이유.
- 목록의 **10번 주제** — 크기가 변하는 그릇(`List<T>`·`Dictionary`)을 고르는 자리.
- 목록의 **11번 주제** — `[1, 2, ..other]` 컬렉션 식. **`..` 라는 글자가 거기서는 「스프레드」로 쓰인다.**
- 목록의 **14번 주제** — 인덱서를 **설계**하는 자리. 여기 (5)는 「`^`·`..` 를 받으려면 무엇이 필요한가」까지다.
- 목록의 **46번 주제** — `Span<T>`·`Memory<T>`·`stackalloc` 의 정본. **왜 필드에 못 두나**가 거기 있다.
- Rust 갈래 목록([`rust/syntax/README.md`](../../../rust/syntax/README.md))의 **15번**([`15-slices-ranges-and-utf8-boundaries/`](../../../rust/syntax/15-slices-ranges-and-utf8-boundaries/)) —\
  ★★ **Rust 의 `..` 와 C# 의 `..` 는 다른 물건**이다. Rust 의 `&v[1..4]` 는 **기본이 뷰**(슬라이스)이고\
  복사하려면 `.to_vec()` 을 붙인다. C# 은 **기본이 복사**이고 뷰를 얻으려면 `AsSpan()` 을 붙인다. **기본값이 반대다.**
- Python 갈래 목록([`python/syntax/README.md`](../../../python/syntax/README.md))의 **9번**([`09-sequence-ops-and-slicing/`](../../../python/syntax/09-sequence-ops-and-slicing/)) —\
  ★★ **음수 인덱스 `a[-1]` 대 `a[^1]`.** 파이썬은 **같은 `int` 자리에 음수를 넣는 것**이고,\
  C# 은 **`Index` 라는 다른 타입**이다. 그래서 C# 에서는 `a[-1]` 이 **런타임에 터지지** 음수로 해석되지 않는다.
- Go 갈래 목록([`go/syntax/README.md`](../../../go/syntax/README.md))의 **5번**([`05-arrays-vs-slices-value-and-header/`](../../../go/syntax/05-arrays-vs-slices-value-and-header/)) —\
  ★★ Go 는 **배열이 값 타입**이고 슬라이스가 **헤더**(포인터·len·cap)다. C# 은 **배열이 참조 타입**이고\
  `Span<T>` 가 그 헤더에 해당한다. **「배열」이라는 낱말이 가리키는 것이 두 언어에서 다르다.**

## 용어 풀이

- **배열(array)** — 같은 타입의 원소를 **붙여 놓고 번호로 찾는** 고정 크기 그릇. C# 에서는 **참조 타입**이다.
- **인덱스 연산자 `^`** — 끝에서 몇 번째인지를 나타내는 접두 연산자. `^1` 이 마지막이다.
- **범위 연산자 `..`** — 시작과 끝을 묶어 `Range` 를 만드는 연산자. **끝은 포함하지 않는다.**
- **half-open 구간** — 시작은 포함하고 끝은 빼는 구간. `1..3` 은 1, 2 두 개다.
- **`System.Index`** — `^n` 과 `n` 을 함께 담는 구조체. `Value` 와 `IsFromEnd` 두 칸이다.
- **`System.Range`** — `Index` 둘(`Start`·`End`)을 담는 구조체.
- **뷰(view)** — 복사 없이 원본의 한 구간을 가리키는 것. `Span<T>` 가 그것이다.
- **`Span<T>`** — 「어느 저장소의 몇 번째부터 몇 개」를 담는 **ref 구조체**. 힙에 못 올라간다(46번 주제).
- **`GetSubArray`** — 배열 범위 인덱싱이 풀려서 불리는 **BCL 헬퍼**. 새 배열을 만들어 복사한다((4)).
- **다차원 배열(`int[,]`)** — 직사각형 격자를 **객체 하나**로 담는 배열. `Rank` 가 2다.
- **배열의 배열(`int[][]`)** — 배열을 원소로 갖는 배열. 줄마다 길이가 달라도 된다.
- **얕은 복사(shallow copy)** — 칸의 값만 복사하는 것. 원소가 참조면 **가리키는 대상은 공유**된다.
- **로워링(lowering)** — 컴파일러가 상위 문법을 더 단순한 형태로 바꾸는 것. `a[^1]` → `a[a.Length - 1]`((4)).

## 더 들어가면

- ★ **`Index`·`Range` 를 메서드 매개변수로 받는 API 설계** — `void Print(Range r)` 처럼 받으면\
  호출 쪽이 `1..^1` 을 그대로 넘긴다. 길이를 **호출된 쪽에서** 알기 때문에 경계 계산이 한곳에 모인다.
- ★ **`Array.Copy`·`Buffer.BlockCopy`·`CopyTo`** — `..` 이 안 풀어 주는 자리(겹치는 구간 이동 등).
- ★ **`stackalloc` + `Span<T>`** — 작은 버퍼를 **힙을 아예 안 쓰고** 잡는 법(46번 주제).
- ★ **`ReadOnlySpan<char>` 로 파싱하기** — `int.Parse(s.AsSpan()[1..^1])` 처럼 **문자열을 안 만들고** 파싱하는 관용구.
- ★ **`System.Runtime.CompilerServices.RuntimeHelpers`** — `GetSubArray` 말고도 컴파일러가 부르는 헬퍼가 여럿 있다.\
  **「소스에 없는 호출」을 찾을 때 IL 에서 이 이름이 자주 보인다.**
