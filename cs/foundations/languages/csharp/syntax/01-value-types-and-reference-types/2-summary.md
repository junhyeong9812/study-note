# csharp/syntax/01 — 값 타입과 참조 타입 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [ECMA-334 7판(2023-12)](https://ecma-international.org/publications-and-standards/standards/ecma-334/) · [Microsoft Learn — C# 언어 레퍼런스](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/) · [Learn — 값 형식](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/builtin-types/value-types) · [Learn — 참조 형식](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/keywords/reference-types) · [.NET API — `GC.GetAllocatedBytesForCurrentThread`](https://learn.microsoft.com/en-us/dotnet/api/system.gc.getallocatedbytesforcurrentthread)
> **실행 검증** — 이 문서의 모든 출력·진단·IL·할당 바이트는 **.NET SDK 10.0.401** ·\
> 런타임 **`.NET 10.0.12`**(`Microsoft.NETCore.App`) · 타겟 **`net10.0`** · **linux-x64** 에서 실제로 돌려 얻은 것이다(2026-09-24).\
> ★ 블록은 캡처 스크립트가 파일로 받아 조립기가 끼워 넣은 것이다 — 사람이 옮겨 적은 줄은 하나도 없다.
> ★★★ **진단 언어를 영어로 고정했다.** 안 그러면 **로캘을 따라 한국어로 나와 재현이 안 된다** —\
> 실측으로 받은 한국어 판이 ``error CS0029: 암시적으로 'string' 형식을 'int' 형식으로 변환할 수 없습니다.`` 였다.\
> 고정하는 법은 둘을 같이 거는 것이다 — 환경변수 **`DOTNET_CLI_UI_LANGUAGE=en`** 과 `csc` 플래그 **`-preferreduilang:en-US`**.
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
> **버전** — 값 타입/참조 타입의 이분은 **C# 1.0부터**. `in` 매개변수는 **C# 7.2부터**,\
> `out` 변수 선언(`Out(out Point q)`)은 **C# 7.0부터**, 구조체의 필드 초기자·매개변수 없는 생성자는 **C# 10부터**다.
> **경계** — 「값이냐 참조냐」라는 **개념 자체**의 정본은 [`foundations/variables-and-memory/`](../../../../variables-and-memory/)다(거기는 파이썬으로 설명한다).\
> 여기는 **C# 에만 있는 쪽** — **언어가 값 타입을 사용자에게 열어 줬다는 것**과 그것이 대입·전달·할당에서 무엇을 바꾸는가다.\
> `struct` 와 `class` 중 **무엇을 고를까**는 [02번](../02-struct-vs-class-choosing/), **박싱**은 [03번](../03-boxing-and-unboxing/)이 정본이다.\
> `ref` 지역·`ref` 반환·`ref struct` 는 목록의 **45번 주제**, `Span<T>` 는 목록의 **46번 주제**다.\
> C++ 의 참조/포인터와는 **축이 다르다** — 그쪽은 C++ 갈래 목록([`cpp/syntax/README.md`](../../../cpp/syntax/README.md))의 **07번**이고,\
> 거기서 갈리는 것은 「**이름이냐 쪽지냐**」인데 여기서 갈리는 것은 「**값이 들어 있냐 참조가 들어 있냐**」다.
>
> ★★ **흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | ★ **`GC.GetAllocatedBytesForCurrentThread()` 의 절댓값**(프로세스 시작부터의 누적이다) | ★★★ **두 호출 사이의 증분**과 **그 증분이 0 이냐 아니냐** |
> | `Stopwatch` 로 잰 **ns 수치** · 그때의 CPU 상태 | **자릿수 차이**(10배·40배 같은 비율) |
> | `GetHashCode()` 값 · 객체 주소 | **진단 코드**(`CS0029` 류) · **진단 문구** · **`(행,열)`** |
> | 빌드 시간 · `dotnet` 패치 버전이 오르면 달라질 수 있는 것 | **`cc exit` 와 `run exit`**(갈라 적었다) |
> | — | **IL 명령어 열**(`box` · `unbox.any` · `ldobj` · `initobj` · `newobj`) |

## 한눈에 — 쉽게 말하면

**값 타입은 「쪽지에 숫자를 적어 둔 것」이고, 참조 타입은 「사물함 번호를 적어 둔 것」이다.**

쪽지를 복사하면 숫자가 복사된다 — 원본을 고쳐도 사본은 그대로다.\
사물함 번호를 복사하면 **번호만** 복사된다 — 한 사람이 사물함 안을 바꾸면 **둘 다 바뀐 것을 본다.**

| 비유 | 실체 |
|---|---|
| **숫자를 적은 쪽지** | `struct Point { int X; }` — 변수 안에 `X` 가 **직접** 있다 |
| **쪽지를 복사한다** | `var s2 = s1;` — **8바이트가 통째로 복사된다**((1)) |
| **사물함 번호를 적은 쪽지** | `class Node { int X; }` — 변수 안에는 **참조**만 있다 |
| **번호를 복사한다** | `var c2 = c1;` — **사물함은 하나다**((1)) |
| ★ **쪽지를 남에게 줄 때도 복사본을 준다** | `Bump(s1)` — 메서드 안의 변경이 **안 돌아온다**((2)) |
| ★★ **「쪽지가 있는 자리 자체」를 넘기는 것** | `ref` — 그제서야 돌아온다((3)) |
| ★★★ **쪽지는 사물함을 안 빌린다** | `new Point()` 는 **힙 할당이 0바이트**다((5)) |

- ★★★ **이 주제의 한 줄** — 「**대입할 때 무엇이 복사되는가**」가 값 타입과 참조 타입을 가르는 유일한 축이다.\
  나머지(널·힙·크기·동일성)는 **전부 거기서 따라 나온다.**
- ★★ **`ref`/`out`/`in` 은 「값이냐 참조냐」와 다른 축**이다((3)) —\
  타입이 정하는 것은 「**변수 안에 무엇이 있나**」이고, `ref` 가 정하는 것은 「**변수 자체를 넘기나**」다.\
  그래서 **참조 타입에도 `ref` 를 붙일 수 있고**, 붙이면 **다른 일**이 일어난다.
- ★★ **`string` 은 참조 타입인데 값처럼 보인다**((6)) — `==` 가 내용을 비교하도록 오버로드돼 있고, **불변**이라 남이 바꿀 수가 없다.\
  ★ 그래서 「`string` 은 값 타입이다」로 잘못 외우기 쉽다. **`ReferenceEquals` 가 그 오해를 한 줄에 깬다.**

```text
   struct Point { int X; int Y; }        class Node { int X; int Y; }

   var s1 = new Point{X=1,Y=2};          var c1 = new Node{X=1,Y=2};
   var s2 = s1;                          var c2 = c1;
   s2.X = 99;                            c2.X = 99;

   스택                                   스택            힙
   +-----------------+                   +--------+      +----------------+
   | s1 : X=1  Y=2   |                   | c1 : ●─┼─┐    | Node  X=99 Y=2 |
   +-----------------+                   +--------+ ├──> +----------------+
   | s2 : X=99 Y=2   |  ← 따로 산다       | c2 : ●─┼─┘      ▲ 하나뿐이다
   +-----------------+                   +--------+

   s1.X == 1   (안 바뀐다)                c1.X == 99  (바뀐다)
```

```text
   "무엇이 복사되나" 한 장

   대입 / 인자 전달 / 컬렉션에 넣기 / 필드에 담기
        │
        ├─ 값 타입   ──> 값 전체(8바이트든 64바이트든)가 복사된다
        │                └─ 그래서 원본이 안 바뀐다
        │
        └─ 참조 타입 ──> 참조(8바이트)만 복사된다
                         └─ 가리키는 객체는 하나이므로 원본도 바뀐 것으로 보인다

   ref 를 붙이면?
        └─ 「변수가 놓인 자리」를 넘긴다 — 타입이 무엇이든 한 겹 더 붙는다
```

> **값 타입(value type)** — 변수 안에 **값이 직접** 들어 있는 타입.\
> `int`·`double`·`bool`·`enum` 과 모든 `struct`. 예: `Point p` 는 `p` 자리에 `X`·`Y` 가 그대로 있다.

> **참조 타입(reference type)** — 변수 안에 **객체를 가리키는 참조**가 들어 있는 타입.\
> `class`·`interface`·델리게이트·배열·`string`. 예: `Node n` 은 `n` 자리에 8바이트 참조만 있다.

> **복사(copy)** — 대입·인자 전달·반환·필드 저장에서 일어나는 것.\
> 값 타입은 **값 전체**를, 참조 타입은 **참조만** 복사한다. 이 한 문장이 이 주제의 전부다.

> **힙 할당(heap allocation)** — GC 가 관리하는 영역에서 공간을 얻는 것.\
> 이 문서는 그것을 **`GC.GetAllocatedBytesForCurrentThread()` 의 증분**으로 관찰한다((5)).

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. **변수에 무엇이 들어 있나** — 값이 직접인가 참조인가. 그리고 **그것을 무엇으로 보일 수 있나**((1)·(5)).
2. **대입·인자 전달에서 복사되는 것이 무엇인가** — 그리고 **`ref`/`out`/`in` 이 그것을 어떻게 바꾸나**((2)·(3)).
3. **「값처럼 보이는 것」과 「값인 것」을 가를 수 있나** — `string` 과 `int?` 가 그 시험지다((6)·(7)).

## 동작 방식

### (0) 이 주제가 쓰는 다섯 창

| 창 | 무엇을 보여 주나 | 이 주제에서 |
|---|---|---|
| **실행 출력** | 대입·전달 뒤에 원본이 바뀌었나 | (1)·(2)·(3)·(6) |
| **컴파일 진단** | ★ **언어가 애초에 막는 것** — `null` · `in` 에 쓰기 · `sizeof` | (3)·(7)·(8) |
| **예외 전문** | 「없는 값」을 꺼낼 때 무엇이 터지나 | (7) |
| ★★ **IL**(`Il.Dump`) | ★★ **무엇이 명령으로 갈리고 무엇이 타입으로만 갈리나** | (4) |
| ★★★ **할당 바이트**(`GC.GetAllocatedBytesForCurrentThread`) | ★★★ **구조체가 힙을 안 쓴다는 것** | (5) |

★★★ **다섯 번째 창이 이 갈래의 중심이다.** C# 은 **에러 메시지가 교재인 언어가 아니라서**(C·Rust 와 다르다)\
「값 타입이 스택에 있다」 같은 말을 **진단으로 증명할 수가 없다.** 대신 **할당 바이트가 0 이냐 아니냐**가 그것을 한 줄로 말한다.

★★ **네 번째 창(IL)은 외부 도구 없이 얻었다.** `ilspycmd`·`ildasm` 을 깔지 않았다 —\
`MethodBody.GetILAsByteArray()` 로 메서드 본문 바이트를 받고, 옵코드 표는 `System.Reflection.Emit.OpCodes` 의\
`public static` 필드를 **리플렉션으로 긁어** 만들었다. 그 프로그램 전문은 [03번](../03-boxing-and-unboxing/2-summary.md)의 (0)절에 있다.

★ **이 판이 무엇인지부터 찍어 둔다** — 아래 수치는 전부 이 판의 것이다.

```text
===== 소스: cs00b-env.cs =====
using System;
using System.Runtime;
using System.Runtime.InteropServices;

Console.WriteLine($"FrameworkDescription : {RuntimeInformation.FrameworkDescription}");
Console.WriteLine($"RuntimeIdentifier    : {RuntimeInformation.RuntimeIdentifier}");
Console.WriteLine($"OSArchitecture       : {RuntimeInformation.OSArchitecture}");
Console.WriteLine($"IntPtr.Size          : {IntPtr.Size}");
Console.WriteLine($"IsServerGC           : {GCSettings.IsServerGC}");
Console.WriteLine($"LatencyMode          : {GCSettings.LatencyMode}");
===== csc -out:ex.dll cs00b-env.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
FrameworkDescription : .NET 10.0.12
RuntimeIdentifier    : linux-x64
OSArchitecture       : X64
IntPtr.Size          : 8
IsServerGC           : False
LatencyMode          : Interactive
```

| 칸 | 값 | 이 문서에서 |
|---|---|---|
| `dotnet --version` | **`10.0.401`**(SDK) | 컴파일러 판 |
| `FrameworkDescription` | **`.NET 10.0.12`** | 런타임 판 — 할당 바이트가 여기 달렸다 |
| 타겟 프레임워크 | **`net10.0`** | `ex.runtimeconfig.json` 의 `tfm` |
| `IntPtr.Size` | ★ **8** | ★ **x64** — (5)·(8)의 숫자가 전부 여기에 달렸다 |
| `IsServerGC` | **`False`** | 워크스테이션 GC 에서만 쟀다 |

★ `dotnet --version` 은 셸에서 따로 받은 것이고(**`10.0.401`**), 위 블록은 **프로그램이 런타임에 물어본 것**이다 —\
**SDK 판과 런타임 판이 다른 숫자**라 둘을 갈라 적는다.

### (1) 대입 — 값 타입은 값이 복사되고 참조 타입은 참조가 복사된다

**언제 쓰나** — 가장 먼저 무는 자리. **같은 모양의 문장이 다른 일을 한다.**

```text
===== 소스: cs01b-copy.cs =====
using System;

var s1 = new Point { X = 1, Y = 2 };
var s2 = s1;                       // 구조체 대입
s2.X = 99;

var c1 = new Node { X = 1, Y = 2 };
var c2 = c1;                       // 클래스 대입
c2.X = 99;

Console.WriteLine($"struct : s1.X={s1.X}  s2.X={s2.X}");
Console.WriteLine($"class  : c1.X={c1.X}  c2.X={c2.X}");

BumpStruct(s1);
BumpClass(c1);
Console.WriteLine($"인자 전달 뒤 : s1.X={s1.X}  c1.X={c1.X}");

Console.WriteLine($"ReferenceEquals(c1, c2) : {ReferenceEquals(c1, c2)}");
Console.WriteLine($"c1.Equals(c2)           : {c1.Equals(c2)}");
Console.WriteLine($"s1.Equals(s2)           : {s1.Equals(s2)}");
var s3 = s1;
Console.WriteLine($"s1.Equals(s3)           : {s1.Equals(s3)}");

static void BumpStruct(Point p) { p.X = 1000; }
static void BumpClass(Node n) { n.X = 1000; }

struct Point { public int X; public int Y; }
class Node { public int X; public int Y; }
===== csc -out:ex.dll cs01b-copy.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
struct : s1.X=1  s2.X=99
class  : c1.X=99  c2.X=99
인자 전달 뒤 : s1.X=1  c1.X=1000
ReferenceEquals(c1, c2) : True
c1.Equals(c2)           : True
s1.Equals(s2)           : False
s1.Equals(s3)           : True
```

| 쓴 것 | 한 일 | 그래서 |
|---|---|---|
| `var s2 = s1;` | ★ **`Point` 8바이트가 통째로 복사된다** | `s2.X = 99` 가 **`s1` 에 안 닿는다** |
| `var c2 = c1;` | **참조 8바이트만 복사된다** | `c2.X = 99` 가 **`c1` 에서도 보인다** |

- ★★★ **`s1.X=1` 과 `c1.X=99`** — 한 글자 차이 없는 코드가 **정반대 결과**를 낸다.\
  다른 것은 선언 한 줄뿐이다(`struct` 냐 `class` 냐).
- ★★ **`ReferenceEquals(c1, c2)` 가 `True`** 다 — **같은 객체**라는 뜻이고, 그것이 위 결과의 이유다.
- ★ **`s1.Equals(s2)` 는 `False`, `s1.Equals(s3)` 는 `True`** 다(`s3` 는 손대지 않은 복사본).\
  구조체의 기본 `Equals` 는 **필드 값을 비교**한다 — 「같은 객체냐」가 아니라 「같은 값이냐」다.\
  ★ 그 기본 구현이 **무엇을 대가로 그렇게 하는지**는 [02번](../02-struct-vs-class-choosing/)의 (5)에서 잰다.
- ★ `c1.Equals(c2)` 가 `True` 인 것은 **값이 같아서가 아니라 같은 객체여서**다 —\
  `class` 는 `Equals` 를 기본으로 **참조 비교**한다. 동등성의 정본은 목록의 **19번 주제**다.

### (2) 인자 전달 — 대입과 같은 규칙이다

**언제 쓰나** — 「메서드에 넘겼는데 안 바뀐다」 할 때. **새 규칙이 아니라 (1)의 규칙이다.**

위 블록의 셋째 줄이 그것이다.

```text
인자 전달 뒤 : s1.X=1  c1.X=1000
```

- ★★★ **`BumpStruct(s1)` 은 `s1` 을 못 바꾸고 `BumpClass(c1)` 은 바꾼다.**\
  둘 다 **값 전달**인데 결과가 다르다 — **넘긴 「값」이 다르기 때문**이다.\
  구조체는 **구조체 값**을 넘겼고, 클래스는 **참조 값**을 넘겼다.
- ★★ **「C# 은 항상 값 전달이다」가 정확한 표현**이다. `ref` 가 붙기 전까지는 그렇다((3)).\
  ★ 「참조 타입은 참조 전달이다」는 **틀린 요약**이다 — (3)의 `ByValue(n)` 이 그 반례다.

### (3) ★★ `ref`/`out`/`in` 이 바꾸는 것 — 타입과 다른 축이다

**언제 쓰나** — 「메서드가 내 변수를 바꾸게 하고 싶다」 · 「큰 구조체를 복사 없이 넘기고 싶다」.

```text
===== 소스: cs01b-refoutin.cs =====
using System;

var p = new Point { X = 1 };
var n = new Node { X = 1 };

ByRefStruct(ref p);
ByRefClass(ref n);
Console.WriteLine($"ref 뒤        : p.X={p.X}  n.X={n.X}");

Replace(ref n);
Console.WriteLine($"ref 재대입 뒤 : n.X={n.X}");

ByValue(n);
Console.WriteLine($"값 전달 재대입 뒤 : n.X={n.X}");

Out(out Point q);
Console.WriteLine($"out           : q.X={q.X}");

var big = new Point { X = 7 };
Console.WriteLine($"in 으로 읽기  : {ReadOnly(in big)}");

static void ByRefStruct(ref Point p) { p.X = 42; }
static void ByRefClass(ref Node n) { n.X = 42; }
static void Replace(ref Node n) { n = new Node { X = 777 }; }
static void ByValue(Node n) { n = new Node { X = -1 }; }
static void Out(out Point p) { p = new Point { X = 5 }; }
static int ReadOnly(in Point p) { return p.X; }

struct Point { public int X; }
class Node { public int X; }
===== csc -out:ex.dll cs01b-refoutin.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
ref 뒤        : p.X=42  n.X=42
ref 재대입 뒤 : n.X=777
값 전달 재대입 뒤 : n.X=777
out           : q.X=5
in 으로 읽기  : 7
```

| 한정자 | 넘기는 것 | 호출 전 대입 | 메서드 안에서 | 이 판의 결과 |
|---|---|---|---|---|
| (없음) | **값의 복사본** | 필요 | 원본에 안 닿는다 | `ByValue(n)` 뒤에도 `n.X=777` |
| **`ref`** | ★ **변수가 놓인 자리** | 필요 | 읽기·쓰기·**재대입** | `p.X=42` · `n.X=777` |
| **`out`** | 〃 | ★ **불필요** | ★ **반드시 대입해야 나간다** | `q.X=5` |
| **`in`** | 〃 | 필요 | ★ **읽기만** | `7` 을 읽었다 |

- ★★★ **`Replace(ref n)` 이 `n` 자체를 새 객체로 갈아 끼운다**(`n.X=777`).\
  **참조 타입에 `ref` 를 붙이는 것이 무의미하지 않다** — 「가리키는 객체를 바꾸는 것」과\
  「**변수가 가리키는 대상을 바꾸는 것**」은 다른 일이고, 뒤엣것은 `ref` 라야 된다.
- ★★ 바로 다음 줄이 그 대조다 — **`ByValue(n)` 안에서 `n = new Node{X=-1}` 을 해도 밖의 `n` 은 `777` 그대로**다.\
  안쪽의 `n` 은 **참조의 복사본**이라 거기 새 참조를 써도 밖에 안 나간다.
- ★ **`out` 은 「호출 전에 대입하지 않아도 되는 대신 메서드가 반드시 대입해야 하는」 계약**이다.\
  `out Point q` 처럼 **호출 자리에서 변수를 선언**하는 것은 **C# 7.0부터**다.
- ★★ 「**`in` 은 복사를 피하려고 참조로 넘기되 못 쓰게 막는 것**」이다. 쓰려고 하면 컴파일에서 막힌다.

```text
===== 소스: cs01b-in-write.cs =====
struct Point { public int X; }

class Program {
    static void Write(in Point p) { p.X = 9; }   // in 매개변수에 쓰기
    static void Main() { }
}
===== csc -out:ex.dll cs01b-in-write.cs (cc exit=1) =====
cs01b-in-write.cs(4,37): error CS8332: Cannot assign to a member of variable 'p' or use it as the right hand side of a ref assignment because it is a readonly variable
```

- ★★★ 진단이 정확히 그 말을 한다 — ``because it is a readonly variable``.\
  `in` 은 **성능 최적화가 아니라 타입 수준의 약속**이고, 컴파일러가 그 약속을 강제한다.
- ★★ **그런데 `in` 에는 조용한 대가가 있다** — `readonly` 가 아닌 구조체를 `in` 으로 받으면\
  **메서드를 부를 때마다 복사본이 생긴다**(방어적 복사). 그 정본은 [02번](../02-struct-vs-class-choosing/)의 (3)이고,\
  ★ **이 배치에서 가장 조용한 함정**이다.
- ★ `ref`/`out`/`in` 자체의 정본은 목록의 **44번 주제**다. 여기서는 **「값이냐 참조냐」와 다른 축**이라는 것까지만 본다.

### (4) ★★ IL — 무엇이 명령으로 갈리고 무엇이 타입으로만 갈리나

**언제 쓰나** — 「컴파일러가 실제로 무엇을 적었나」를 볼 때. **도식으로 지어내지 않는 자리**다.

```text
===== 소스: cs01b-il.cs =====
Il.Dump(typeof(Probe), "MakeStruct");
Il.Dump(typeof(Probe), "MakeClass");
Il.Dump(typeof(Probe), "CopyStruct");
Il.Dump(typeof(Probe), "CopyClass");

static class Probe {
    public static Point MakeStruct() { var p = new Point(); p.X = 1; return p; }
    public static Node MakeClass() { var n = new Node(); n.X = 1; return n; }
    public static int CopyStruct(Point a) { var b = a; b.X = 9; return a.X; }
    public static int CopyClass(Node a) { var b = a; b.X = 9; return a.X; }
}

struct Point { public int X; public int Y; }
class Node { public int X; public int Y; }
===== csc -r:il.dll -out:ex.dll cs01b-il.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
--- Probe.MakeStruct ---
  .locals [0] Point
  .locals [1] Point
  IL_0000: nop
  IL_0001: ldloca.s 0
  IL_0003: initobj Point
  IL_0009: ldloca.s 0
  IL_000b: ldc.i4.1
  IL_000c: stfld Point::X
  IL_0011: ldloc.0
  IL_0012: stloc.1
  IL_0013: br.s IL_0015
  IL_0015: ldloc.1
  IL_0016: ret
--- Probe.MakeClass ---
  .locals [0] Node
  .locals [1] Node
  IL_0000: nop
  IL_0001: newobj Node::.ctor
  IL_0006: stloc.0
  IL_0007: ldloc.0
  IL_0008: ldc.i4.1
  IL_0009: stfld Node::X
  IL_000e: ldloc.0
  IL_000f: stloc.1
  IL_0010: br.s IL_0012
  IL_0012: ldloc.1
  IL_0013: ret
--- Probe.CopyStruct ---
  .locals [0] Point
  .locals [1] System.Int32
  IL_0000: nop
  IL_0001: ldarg.0
  IL_0002: stloc.0
  IL_0003: ldloca.s 0
  IL_0005: ldc.i4.s 9
  IL_0007: stfld Point::X
  IL_000c: ldarg.0
  IL_000d: ldfld Point::X
  IL_0012: stloc.1
  IL_0013: br.s IL_0015
  IL_0015: ldloc.1
  IL_0016: ret
--- Probe.CopyClass ---
  .locals [0] Node
  .locals [1] System.Int32
  IL_0000: nop
  IL_0001: ldarg.0
  IL_0002: stloc.0
  IL_0003: ldloc.0
  IL_0004: ldc.i4.s 9
  IL_0006: stfld Node::X
  IL_000b: ldarg.0
  IL_000c: ldfld Node::X
  IL_0011: stloc.1
  IL_0012: br.s IL_0014
  IL_0014: ldloc.1
  IL_0015: ret
```

| 보는 곳 | 값 타입 | 참조 타입 | 읽는 법 |
|---|---|---|---|
| **객체를 만들 때** | ★★★ **`initobj Point`** | ★★★ **`newobj Node::.ctor`** | **힙을 쓰느냐가 여기서 갈린다** |
| **지역에 대입할 때** | `stloc.0` | `stloc.0` | ★ **같다** |
| **필드에 쓸 때** | `ldloca.s 0` → `stfld` | `ldloc.0` → `stfld` | 값 타입은 **자리**(주소)를 먼저 얹는다 |
| **`.locals` 선언** | `[0] Point` | `[0] Node` | ★★★ **여기가 진짜 차이다** |

- ★★★ **`MakeStruct` 에는 `newobj` 가 없다.** `initobj Point` 는 **이미 있는 자리를 0 으로 미는 명령**이고\
  **할당이 아니다.** `MakeClass` 의 `newobj` 는 **힙에서 공간을 얻는 명령**이다 — (5)가 그것을 바이트로 확인한다.
- ★★★ **`CopyStruct` 와 `CopyClass` 의 명령어 열이 거의 같다**(`ldarg.0` → `stloc.0`).\
  갈리는 것은 `ldloca.s 0` 대 `ldloc.0` **한 줄뿐**이고, **무엇이 복사되는지는 명령이 아니라 `.locals` 의 타입이 정한다.**\
  ★ 이것이 이 절의 값어치다 — 「복사 명령이 따로 있을 것」이라는 예상이 **틀린다.**\
  `stloc.0` 은 **평가 스택 맨 위를 0번 지역에 넣어라**일 뿐이고, 그 지역이 `Point` 면 8바이트가, `Node` 면 참조가 들어간다.
- ★★ **그러니 「구조체 대입이 느리다」를 IL 에서 읽으려 하면 안 읽힌다.** 명령 수는 같다.\
  ★ 비용은 **명령이 다루는 타입의 크기**에 있고, 그 판단의 정본은 [02번](../02-struct-vs-class-choosing/)이다.

### (5) ★★★ 할당 바이트 — 구조체는 힙을 안 쓴다

**언제 쓰나** — 「값 타입은 스택에 있다」는 말을 **확인**할 때. **이 창이 이 주제에서 가장 강하다.**

```text
===== 소스: cs01b-alloc.cs =====
using System;

// 워밍업 — 첫 호출이 끌고 오는 할당을 측정 밖으로 뺀다.
Warm();

long a0 = GC.GetAllocatedBytesForCurrentThread();
var p = new Point { X = 1, Y = 2 };
long a1 = GC.GetAllocatedBytesForCurrentThread();
var n = new Node { X = 1, Y = 2 };
long a2 = GC.GetAllocatedBytesForCurrentThread();
var arrS = new Point[1000];
long a3 = GC.GetAllocatedBytesForCurrentThread();
var arrC = new Node[1000];
long a4 = GC.GetAllocatedBytesForCurrentThread();
for (int i = 0; i < 1000; i++) arrC[i] = new Node();
long a5 = GC.GetAllocatedBytesForCurrentThread();

Console.WriteLine($"new Point()      : +{a1 - a0} 바이트");
Console.WriteLine($"new Node()       : +{a2 - a1} 바이트");
Console.WriteLine($"new Point[1000]  : +{a3 - a2} 바이트");
Console.WriteLine($"new Node[1000]   : +{a4 - a3} 바이트");
Console.WriteLine($"거기에 Node 1000개 채우기 : +{a5 - a4} 바이트");
Console.WriteLine($"(합계는 흔들리는 칸이다 — 읽을 것은 0 이냐 아니냐와 증분이다)");
Console.WriteLine($"p.X={p.X} n.X={n.X} arrS.Length={arrS.Length} arrC[0]!.X={arrC[0]!.X}");

static void Warm() { var _ = new Node(); var __ = new Point[1]; GC.GetAllocatedBytesForCurrentThread(); }

struct Point { public int X; public int Y; }
class Node { public int X; public int Y; }
===== csc -out:ex.dll cs01b-alloc.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
new Point()      : +0 바이트
new Node()       : +24 바이트
new Point[1000]  : +8024 바이트
new Node[1000]   : +8024 바이트
거기에 Node 1000개 채우기 : +24000 바이트
(합계는 흔들리는 칸이다 — 읽을 것은 0 이냐 아니냐와 증분이다)
p.X=1 n.X=1 arrS.Length=1000 arrC[0]!.X=0
```

| 쓴 것 | 증분 | 읽는 법 |
|---|---|---|
| `new Point { X=1, Y=2 }` | ★★★ **+0 바이트** | 힙을 **안 썼다** |
| `new Node { X=1, Y=2 }` | **+24 바이트** | 힙에서 얻었다(헤더 16 + 필드 8) |
| `new Point[1000]` | **+8024 바이트** | ★ 8바이트 × 1000 + 배열 헤더 24 |
| `new Node[1000]` | **+8024 바이트** | ★★ **같은 숫자인데 뜻이 정반대다** |
| 거기에 `Node` 1000개 채우기 | **+24000 바이트** | 그제서야 객체가 생긴다 |

- ★★★ **`new Point()` 의 증분이 정확히 0 이다.** 「값 타입은 힙을 안 쓴다」를 **말이 아니라 수치로** 얻었다.
- ★★★ **`Point[1000]` 과 `Node[1000]` 이 둘 다 8024 인 것은 우연**이다 —\
  `Point` 가 **마침 참조 하나와 같은 8바이트**라서다. 뜻은 정반대다:\
  앞엣것은 **`Point` 1000개가 이미 다 들어 있고**, 뒤엣것은 **`null` 1000개**다.\
  ★ 뒤엣것을 실제로 쓰려면 **24000 바이트를 더** 내야 하고, 그것이 「값 타입 배열이 싸다」의 근거다.
- ★★ **절댓값은 흔들리는 칸**이다(머리말 표). 근거로 쓰는 것은 **증분**과 **0 이냐 아니냐**다.\
  ★ 그래서 이 문서는 **누적값을 한 번도 싣지 않았다** — 두 번 찍어 뺀 값만 싣는다.
- ★ **주의 — 「힙을 안 쓴다」는 「스택에 있다」와 같은 말이 아니다.** 구조체가 **클래스의 필드**이거나\
  **박싱**되면 힙에 있다(위 표의 마지막 줄이 그것이다). 「어디 사느냐」는 **그 값이 어디 담겼느냐**가 정한다.\
  ★★ **ECMA-334 는 「스택」이라는 말을 보장하지 않는다** — 아래 「구현 세부사항 대 언어 보장」을 보라.

### (6) ★★ `string` — 참조 타입인데 값처럼 보인다

**언제 쓰나** — 「`string` 은 값 타입 아닌가?」 할 때. **한 블록이 그 오해를 끝낸다.**

```text
===== 소스: cs01b-string.cs =====
using System;

string a = "hello";
string b = "hello";
string c = new string(['h', 'e', 'l', 'l', 'o']);
string d = a;

Console.WriteLine($"a == b                  : {a == b}");
Console.WriteLine($"a == c                  : {a == c}");
Console.WriteLine($"ReferenceEquals(a, b)   : {ReferenceEquals(a, b)}");
Console.WriteLine($"ReferenceEquals(a, c)   : {ReferenceEquals(a, c)}");
Console.WriteLine($"ReferenceEquals(a, d)   : {ReferenceEquals(a, d)}");

string e = a;
a = a.ToUpper();                 // 바꾼 것처럼 보이는 자리
Console.WriteLine($"a={a}  e={e}");
Console.WriteLine($"ReferenceEquals(a, e)   : {ReferenceEquals(a, e)}");

object boxed1 = 5;
object boxed2 = 5;
Console.WriteLine($"ReferenceEquals(5, 5)   : {ReferenceEquals(boxed1, boxed2)}");
===== csc -out:ex.dll cs01b-string.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
a == b                  : True
a == c                  : True
ReferenceEquals(a, b)   : True
ReferenceEquals(a, c)   : False
ReferenceEquals(a, d)   : True
a=HELLO  e=hello
ReferenceEquals(a, e)   : False
ReferenceEquals(5, 5)   : False
```

| 쓴 것 | 결과 | 왜 |
|---|---|---|
| `a == b` · `a == c` | **둘 다 `True`** | ★ `string` 이 `==` 를 **내용 비교로 오버로드**했다 |
| `ReferenceEquals(a, b)` | **`True`** | ★★ **리터럴이 인터닝**돼 같은 객체다 |
| `ReferenceEquals(a, c)` | ★★★ **`False`** | `new string(...)` 은 **새 객체**다 — `==` 는 참인데! |
| `a = a.ToUpper()` 뒤 `e` | **`hello` 그대로** | ★★★ **`string` 은 불변** — 바꾼 게 아니라 **새 객체를 만들어 `a` 에 다시 대입**한 것 |
| `ReferenceEquals(5, 5)` | ★★ **`False`** | 박싱된 두 `int` 는 **다른 객체**다 |

- ★★★ **`a == c` 가 `True` 인데 `ReferenceEquals(a, c)` 가 `False`** — 이 한 줄이 「`string` 은 참조 타입이다」의 증거다.\
  값 타입이었다면 **참조라는 개념 자체가 없어** 이 질문이 성립하지 않는다.
- ★★ **「값처럼 보이는」 이유는 둘**이다 — ① `==` 가 **내용 비교로 오버로드**돼 있고\
  ② **불변**이라 남이 들고 있는 객체를 바꿀 수가 없다. **참조를 공유해도 안전**하므로 값처럼 써도 탈이 안 난다.
- ★★★ **`ReferenceEquals(5, 5)` 가 `False` 인 것은 `↔Java` 에서 크게 갈리는 자리**다.\
  Java 는 `Integer` 를 **-128\~127 에서 캐싱**해 `Integer.valueOf(5) == Integer.valueOf(5)` 가 참이지만,\
  **C# 에는 그 캐시가 없다** — 박싱할 때마다 **새 객체**다((5)의 「박싱 1000번 = 24000바이트」가 같은 사실이다).\
  ★ 박싱의 정본은 [03번](../03-boxing-and-unboxing/)이다.

### (7) ★ `null` 을 담을 수 있는 것과 없는 것

**언제 쓰나** — 「`int` 에 `null` 을 넣고 싶다」 할 때. **언어가 컴파일에서 막는다.**

```text
===== 소스: cs01b-null.cs =====
struct Point { public int X; }

class Program {
    static void Main() {
        int i = null;
        Point p = null;
        string s = null;
        object o = null;
        int? q = null;
        System.Console.WriteLine($"{i} {p} {s} {o} {q}");
    }
}
===== csc -out:ex.dll cs01b-null.cs (cc exit=1) =====
cs01b-null.cs(5,17): error CS0037: Cannot convert null to 'int' because it is a non-nullable value type
cs01b-null.cs(6,19): error CS0037: Cannot convert null to 'Point' because it is a non-nullable value type
cs01b-null.cs(1,27): warning CS0649: Field 'Point.X' is never assigned to, and will always have its default value 0
```

- ★★★ 진단이 이유까지 말한다 — ``because it is a non-nullable value type``.\
  **값 타입은 「값이 없는 상태」라는 걸 표현할 자리가 없다** — 모든 비트 조합이 이미 어떤 값이다.
- ★ `string s = null;` 과 `object o = null;` 은 **에러가 아니다**(경고도 없다 — 이 문서는 널 허용 분석을 안 켰다).\
  ★ `#nullable enable` 이 그 경고를 켜는 것이고, 그 정본은 [목록의 **06번 주제**](../06-nullable-reference-types/)다.

그러면 `int?` 는 무엇인가.

```text
===== 소스: cs01b-nullable.cs =====
using System;

int? q = null;
Console.WriteLine($"q.HasValue          : {q.HasValue}");
Console.WriteLine($"q.GetType() 호출 전 : q is Nullable<int> 인가 — 아래 세 줄로 본다");
Console.WriteLine($"typeof(int?)        : {typeof(int?)}");
Console.WriteLine($"q == null           : {q == null}");

q = 5;
Console.WriteLine($"q.Value             : {q.Value}");
object o = q;                     // 박싱하면 Nullable 이 벗겨진다
Console.WriteLine($"((object)q).GetType() : {o!.GetType()}");

int? r = null;
object? ro = r;
Console.WriteLine($"((object)null int?) is null : {ro is null}");

try {
    int? z = null;
    Console.WriteLine(z.Value);
} catch (InvalidOperationException ex) {
    Console.WriteLine($"z.Value          : {ex.GetType().Name}: {ex.Message}");
}
===== csc -out:ex.dll cs01b-nullable.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
q.HasValue          : False
q.GetType() 호출 전 : q is Nullable<int> 인가 — 아래 세 줄로 본다
typeof(int?)        : System.Nullable`1[System.Int32]
q == null           : True
q.Value             : 5
((object)q).GetType() : System.Int32
((object)null int?) is null : True
z.Value          : InvalidOperationException: Nullable object must have a value.
```

| 쓴 것 | 결과 | 읽는 법 |
|---|---|---|
| `typeof(int?)` | ``System.Nullable`1[System.Int32]`` | ★★ **`int?` 도 구조체다** — 값 타입이다 |
| `q == null` | **`True`** | `==` 가 `HasValue` 를 보도록 정의돼 있다 |
| `((object)q).GetType()` | ★★★ **`System.Int32`** | ★★★ **박싱하면 `Nullable` 이 벗겨진다** |
| `(object)(int?)null is null` | **`True`** | 값이 없는 `int?` 는 **박싱하면 `null` 참조**가 된다 |
| `z.Value`(값이 없을 때) | `InvalidOperationException: Nullable object must have a value.` | 예외로 터진다 |

- ★★★ **`int?` 는 참조 타입이 아니다.** `Nullable<int>` 라는 **구조체**이고, 안에 `bool HasValue` 와 `int value` 가 있다.\
  **「널을 담을 수 있게 된 것」이지 「참조 타입이 된 것」이 아니다.**
- ★★★ **박싱이 `Nullable` 을 특별 취급한다** — `object o = q` 는 `Nullable<int>` 를 박싱하는 게 아니라\
  **값이 있으면 그 `int` 를, 없으면 `null` 참조를** 만든다. 런타임이 정한 **특례**이고, 그래서 `GetType()` 이 `System.Int32` 다.\
  ★ `int?` 자체의 정본은 [목록의 **08번 주제**](../08-nullable-value-types/)다.

### (8) ★ 크기를 재려면 — `sizeof` 는 `unsafe` 가 필요하다

**언제 쓰나** — 「이 구조체가 몇 바이트지?」 할 때. **그 질문이 막히는 것 자체가 재료다.**

```text
===== 소스: cs01b-sizeof.cs =====
struct Point { public int X = 0; public int Y = 0; public Point() { } }
struct Holder { public string S = ""; public Holder() { } }

class Program {
    static void Main() {
        int a = sizeof(int);
        int b = sizeof(Point);
        int c = sizeof(Holder);
        int d = sizeof(string);
        System.Console.WriteLine($"{a} {b} {c} {d}");
    }
}
===== csc -out:ex.dll cs01b-sizeof.cs (cc exit=1) =====
cs01b-sizeof.cs(7,17): error CS0233: 'Point' does not have a predefined size, therefore sizeof can only be used in an unsafe context
cs01b-sizeof.cs(8,17): warning CS8500: This takes the address of, gets the size of, or declares a pointer to a managed type ('Holder')
cs01b-sizeof.cs(8,17): error CS0233: 'Holder' does not have a predefined size, therefore sizeof can only be used in an unsafe context
cs01b-sizeof.cs(9,17): warning CS8500: This takes the address of, gets the size of, or declares a pointer to a managed type ('string')
cs01b-sizeof.cs(9,17): error CS0233: 'string' does not have a predefined size, therefore sizeof can only be used in an unsafe context
```

- ★★★ **`sizeof(int)` 은 되는데 `sizeof(Point)` 는 안 된다.**\
  내장 타입은 **컴파일러가 아는 고정 크기**가 있지만, 사용자 구조체의 크기는 **런타임이 정하는 것**이라\
  안전한 문맥에서는 못 묻게 막았다.
- ★★ **관리 타입(`string` 을 담은 구조체·`class`)은 `unsafe` 로도 안 된다** — 경고 `CS8500` 이 그 이유를 말한다.
- ★ `unsafe` 를 켜고 던지면, 그리고 `Unsafe.SizeOf<T>()` 를 쓰면 이렇게 나온다.

```text
===== 소스: cs01b-sizeof-unsafe.cs =====
using System;
using System.Runtime.CompilerServices;

unsafe {
    Console.WriteLine($"sizeof(int)    = {sizeof(int)}");
    Console.WriteLine($"sizeof(Point)  = {sizeof(Point)}");
}
Console.WriteLine($"Unsafe.SizeOf<int>()    = {Unsafe.SizeOf<int>()}");
Console.WriteLine($"Unsafe.SizeOf<Point>()  = {Unsafe.SizeOf<Point>()}");
Console.WriteLine($"Unsafe.SizeOf<Holder>() = {Unsafe.SizeOf<Holder>()}");
Console.WriteLine($"Unsafe.SizeOf<Node>()   = {Unsafe.SizeOf<Node>()}");
Console.WriteLine($"Unsafe.SizeOf<string>() = {Unsafe.SizeOf<string>()}");

Console.WriteLine($"IsRefOrContainsRefs<int>()    = {RuntimeHelpers.IsReferenceOrContainsReferences<int>()}");
Console.WriteLine($"IsRefOrContainsRefs<Point>()  = {RuntimeHelpers.IsReferenceOrContainsReferences<Point>()}");
Console.WriteLine($"IsRefOrContainsRefs<Holder>() = {RuntimeHelpers.IsReferenceOrContainsReferences<Holder>()}");
Console.WriteLine($"IsRefOrContainsRefs<Node>()   = {RuntimeHelpers.IsReferenceOrContainsReferences<Node>()}");

struct Point { public int X; public int Y; }
struct Holder { public string S; }
class Node { public int X; public int Y; }
===== csc -unsafe -out:ex.dll cs01b-sizeof-unsafe.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
sizeof(int)    = 4
sizeof(Point)  = 8
Unsafe.SizeOf<int>()    = 4
Unsafe.SizeOf<Point>()  = 8
Unsafe.SizeOf<Holder>() = 8
Unsafe.SizeOf<Node>()   = 8
Unsafe.SizeOf<string>() = 8
IsRefOrContainsRefs<int>()    = False
IsRefOrContainsRefs<Point>()  = False
IsRefOrContainsRefs<Holder>() = True
IsRefOrContainsRefs<Node>()   = True
```

| 물어본 것 | 값 | 읽는 법 |
|---|---|---|
| `sizeof(Point)` / `Unsafe.SizeOf<Point>()` | **8** | `int` 둘 |
| `Unsafe.SizeOf<Node>()` · `Unsafe.SizeOf<string>()` | ★★ **둘 다 8** | ★★★ **참조 하나의 크기**다 — 객체 크기가 아니다 |
| `IsReferenceOrContainsReferences<Point>()` | **`False`** | 참조가 하나도 없다 |
| `IsReferenceOrContainsReferences<Holder>()` | ★ **`True`** | `string` 필드 하나가 **구조체 전체의 성질을 바꾼다** |

- ★★★ **`Unsafe.SizeOf<Node>()` 가 8 인 것은 함정**이다 — 그것은 **참조의 크기**이고 `Node` 객체의 크기가 아니다.\
  (5)에서 `new Node()` 가 **24바이트**를 썼다. **크기를 물을 때 「무엇의 크기냐」를 먼저 정해야 한다.**
- ★★ **`IsReferenceOrContainsReferences<T>()` 가 진짜 경계선**이다 —\
  **참조를 하나라도 품으면** GC 가 그 안을 훑어야 하고, `Span<T>`·`memcpy` 최적화 대상에서 빠진다.\
  ★ 구조체를 고를 때 보는 축 하나가 여기다([02번](../02-struct-vs-class-choosing/)).

## 문법 — 형태와 규칙

### 형태

```csharp
// cs01b-copy.cs
using System;

var s1 = new Point { X = 1, Y = 2 };
var s2 = s1;                       // 구조체 대입
s2.X = 99;

var c1 = new Node { X = 1, Y = 2 };
var c2 = c1;                       // 클래스 대입
c2.X = 99;

Console.WriteLine($"struct : s1.X={s1.X}  s2.X={s2.X}");
Console.WriteLine($"class  : c1.X={c1.X}  c2.X={c2.X}");

BumpStruct(s1);
BumpClass(c1);
Console.WriteLine($"인자 전달 뒤 : s1.X={s1.X}  c1.X={c1.X}");

Console.WriteLine($"ReferenceEquals(c1, c2) : {ReferenceEquals(c1, c2)}");
Console.WriteLine($"c1.Equals(c2)           : {c1.Equals(c2)}");
Console.WriteLine($"s1.Equals(s2)           : {s1.Equals(s2)}");
var s3 = s1;
Console.WriteLine($"s1.Equals(s3)           : {s1.Equals(s3)}");

static void BumpStruct(Point p) { p.X = 1000; }
static void BumpClass(Node n) { n.X = 1000; }

struct Point { public int X; public int Y; }
class Node { public int X; public int Y; }
```

규칙 불릿.

- **값 타입** — `struct`·`enum`·`int`·`double`·`bool`·`char`·`decimal`·튜플(`(int, string)`)·`Nullable<T>`.\
  **참조 타입** — `class`·`interface`·델리게이트·**배열**·`string`·`object`·`record`(기본).
- **대입·인자 전달·반환·필드 저장은 전부 「복사」다.** 값 타입은 **값 전체**, 참조 타입은 **참조**를 복사한다((1)·(2)).
- **`ref`/`out`/`in` 은 「변수 자체」를 넘긴다**((3)). **타입과 직교하는 축**이라 참조 타입에도 붙는다.
- **값 타입에는 `null` 을 못 넣는다**((7)). `T?`(`Nullable<T>`)가 그 자리를 만들어 주고, **그것도 구조체**다.
- **`new` 가 붙었다고 힙을 쓰는 게 아니다**((5)) — 구조체의 `new` 는 **초기화**이고 `initobj`/생성자 호출이다((4)).
- **`sizeof` 는 내장 타입 말고는 `unsafe` 가 필요하다**((8)). 안전한 대안은 `Unsafe.SizeOf<T>()` 다.
- **`string` 은 참조 타입이다**((6)) — `==` 오버로드와 불변성이 그것을 **값처럼 보이게** 할 뿐이다.

### 금지 사례 — 던져서 받은 넷

| 쓴 것 | 진단 | 무엇을 말하나 |
|---|---|---|
| `int i = null;` | ``error CS0037: Cannot convert null to 'int' because it is a non-nullable value type`` | 값 타입에는 「없음」이 없다 |
| `Point p = null;` | ``error CS0037: Cannot convert null to 'Point' because it is a non-nullable value type`` | 사용자 구조체도 같다 |
| `in` 매개변수에 `p.X = 9;` | ``error CS8332: Cannot assign to a member of variable 'p' … because it is a readonly variable`` | `in` 은 읽기 전용 약속이다 |
| `sizeof(Point)` | ``error CS0233: 'Point' does not have a predefined size, therefore sizeof can only be used in an unsafe context`` | 크기는 런타임이 정한다 |

### 고를 것을 손으로 돌리는 순서

1. **「이 변수를 복사했을 때 따로 살아야 하나?」** — 그러면 **값 타입**.
2. **「여러 곳에서 같은 것을 보고 같이 바뀌어야 하나?」** — 그러면 **참조 타입**.
3. **「없음(`null`)을 표현해야 하나?」** — 참조 타입은 공짜, 값 타입은 `T?`((7)).
4. **「메서드가 내 변수를 갈아 끼워야 하나?」** — **`ref`**(타입과 무관하게)((3)).
5. **「크고 안 바뀌는 값을 자주 넘기나?」** — **`in`** — 단 **`readonly struct` 로 만들고 나서**([02번](../02-struct-vs-class-choosing/)).
6. 나머지 판단(크기·불변성·복사 비용)은 [02번](../02-struct-vs-class-choosing/)이 정본이다.

## 어디서 틀리나

### 1. ★★★ 「값 타입은 스택에, 참조 타입은 힙에 있다」

**절반만 맞다**((5)). 값 타입이 **클래스의 필드**이거나 **배열의 원소**이거나 **박싱**되면 **힙에 있다.**\
정확한 문장은 「**값 타입은 담긴 자리에 산다**」이고, 「스택」은 **그 자리가 마침 스택일 때의 이야기**다.\
★★ ECMA-334 는 스택·힙이라는 **저장 위치를 보장하지 않는다** — 아래 표를 보라.

### 2. ★★★ 「참조 타입은 참조 전달이다」

**아니다**((2)·(3)). C# 은 `ref` 가 없으면 **항상 값 전달**이고, 참조 타입에서 전달되는 「값」이 **참조**일 뿐이다.\
반례가 (3)의 `ByValue(n)` 이다 — 안에서 `n = new Node()` 를 해도 **밖은 안 바뀐다.**

### 3. ★★★ 「`string` 은 값 타입이다」

**아니다**((6)). `ReferenceEquals(a, c)` 가 **`False`** 인데 `a == c` 는 **`True`** 다.\
★ 값처럼 **보이는** 이유는 **`==` 오버로드**와 **불변성** 둘뿐이다.

### 4. ★★ 「`int?` 는 참조 타입이다」

**아니다**((7)). `Nullable<int>` 라는 **구조체**다. `typeof(int?)` 가 ``System.Nullable`1[System.Int32]`` 를 답한다.\
★ 다만 **박싱하면 `Nullable` 이 벗겨져** `GetType()` 이 `System.Int32` 를 답한다 — 이건 **런타임 특례**다.

### 5. ★★ 「구조체 대입이 느리다 / 빠르다」

**이 문서는 안 쟀다.** (4)에서 본 것은 「**IL 명령 수가 같다**」까지이고,\
비용은 **명령이 다루는 타입의 크기**에 달렸다. **재지 않은 성능 주장은 하지 않는다** —\
크기와 복사 비용의 정본은 [02번](../02-struct-vs-class-choosing/)이다.

### 6. ★★ 「`new` 를 쓰면 힙을 쓴다」

**아니다**((4)·(5)). `new Point()` 는 **0바이트**이고 IL 이 `initobj` 다.\
★ C# 의 `new` 는 「**할당하라**」가 아니라 「**초기화하라**」에 가깝다.

### 7. ★★ 「`in` 을 붙이면 공짜로 빨라진다」

**아니다.** `readonly` 가 아닌 구조체를 `in` 으로 받으면 **호출마다 조용히 복사본이 생긴다**(방어적 복사).\
★ 그 정본은 [02번](../02-struct-vs-class-choosing/)의 (3)이고, **경고가 한 줄도 안 난다.**

### 8. ★ 「`sizeof` 로 구조체 크기를 잰다」

**안전한 문맥에서는 막힌다**((8)). `unsafe` 를 켜거나 `Unsafe.SizeOf<T>()` 를 쓴다.\
★ 그리고 **`Unsafe.SizeOf<클래스>()` 는 객체 크기가 아니라 참조 크기(8)** 다.

### 9. ★ 「`ReferenceEquals` 로 값 타입을 비교한다」

**뜻이 없다.** 값 타입을 넣으면 **둘 다 박싱**돼 **항상 `False`** 가 나온다((6)의 마지막 줄).\
★ `ReferenceEquals(5, 5)` 가 `False` 인 게 그 예다.

### 10. 「Java 를 알면 그대로 온다」

**한 칸이 다르다.** Java 에는 **사용자 정의 값 타입이 없다**(JEP 401 은 아직 미리보기다).\
★ 그래서 Java 의 「원시 타입 대 객체」 이분은 **고정된 8종**이지만, C# 은 **내가 만들 수 있다.**\
★★ 그리고 **`Integer` 캐시가 C# 에는 없다**((6)) — `ReferenceEquals(5, 5)` 가 **`False`** 다.

## 구현 세부사항 대 언어 보장

| 사실 | 누가 보장하나 |
|---|---|
| **값 타입 대입이 값을 복사하고 참조 타입 대입이 참조를 복사하는** 것 | **언어**(ECMA-334) |
| **인자 전달이 기본으로 값 전달인** 것 · **`ref`/`out`/`in` 의 의미** | **언어** |
| **값 타입에 `null` 을 못 넣는** 것 · **`T?` 가 `Nullable<T>` 인** 것 | **언어** |
| **`sizeof` 가 내장 타입 말고는 `unsafe` 를 요구하는** 것 | **언어** |
| **`string` 이 참조 타입이고 불변이며 `==` 가 내용 비교인** 것 | **언어** + BCL |
| ★★★ **값 타입이 「스택」에 있다는 것** | ★★★ **아무도 보장하지 않는다.** 명세는 **저장 위치를 규정하지 않는다** — 관찰되는 것은 「**힙 할당이 0 이다**」까지다((5)) |
| ★★ **박싱 하나가 24바이트인 것** · **`Node` 가 24바이트인 것** | ★★ **CoreCLR 10 의 구현**(헤더 16 + 필드). 64비트 x64 기준이고 **32비트에서 다르다** |
| ★ **문자열 리터럴이 인터닝돼 `ReferenceEquals(a, b)` 가 참인** 것 | ★ 리터럴 인터닝은 **명세가 요구**하지만, ``ReferenceEquals(new string(...), 리터럴)`` 이 거짓인 것은 **구현 관찰**이다 |
| ★ **`(object)(int?)` 가 `Nullable` 을 벗기는** 것 | ★ **CLI(ECMA-335)의 박싱 규칙** — 언어가 아니라 런타임이 정한다 |
| ★ **IL 명령 이름**(`initobj`·`newobj`·`ldobj`) | ★ **Roslyn 이 낸 코드**다. 최적화가 바뀌면 달라질 수 있다 — 결론은 「**힙을 쓰느냐**」이지 명령 이름이 아니다 |
| 진단 문구 · 진단 코드 · **에러를 몇 개로 세는가** | **컴파일러 구현**(Roslyn) |

## 언제 쓰고 언제 안 쓰나

**값 타입이 사는 자리 셋**\
① **작고 값으로 다뤄야 하는 것** — 좌표·금액·기간·식별자.\
② **배열·리스트에 잔뜩 담는 것** — (5)에서 봤듯 **객체 1000개 값을 안 낸다.**\
③ **널이 의미 없는 것** — 「없는 좌표」가 말이 안 되면 값 타입이 그것을 타입으로 말한다.

**참조 타입이 사는 자리 셋**\
① **동일성이 있는 것**(같은 주문·같은 사용자) — 복사되면 안 되는 것.\
② **크거나 자라는 것** — 복사 비용이 실제로 드는 것.\
③ **상속·다형성이 필요한 것** — 구조체는 상속을 못 한다([02번](../02-struct-vs-class-choosing/)).

**고민되면 `class` 가 기본값이다.** 값 타입은 **이유가 있을 때** 고른다 —\
그 이유를 대는 법이 [02번](../02-struct-vs-class-choosing/)이고, **그 이유가 대개 박싱**이라 [03번](../03-boxing-and-unboxing/)이 뒤따른다.

## 핵심 문장

1. **대입할 때 무엇이 복사되는가** — 값 타입은 값 전체, 참조 타입은 참조. 나머지는 전부 여기서 따라 나온다.
2. **C# 은 `ref` 가 없으면 항상 값 전달이다** — 「참조 타입은 참조 전달」은 틀린 요약이다((3)의 `ByValue`).
3. **`new Point()` 는 0바이트다** — `new` 가 곧 할당은 아니고, IL 이 `initobj` 로 그것을 적는다.
4. **`string` 은 참조 타입이다** — `a == c` 가 참인데 `ReferenceEquals(a, c)` 가 거짓이다.
5. **`int?` 는 구조체다** — 다만 박싱하면 `Nullable` 이 벗겨져 `GetType()` 이 `System.Int32` 를 답한다.
6. **「스택에 있다」는 보장이 아니다** — 보장되는 것은 복사 의미론이고, 관찰되는 것은 힙 할당이 0 이라는 것이다.

## 관련 자료

- [`foundations/variables-and-memory/`](../../../../variables-and-memory/) — ★ 「값이냐 참조냐」 **개념 자체**의 정본(파이썬).\
  **그쪽은 「참조가 무엇인가」까지, 여기는 「언어가 값 타입을 열어 줬을 때 무엇이 달라지나」부터.**
- [02번 — `struct` 대 `class` 고르기](../02-struct-vs-class-choosing/) — ★★ **그래서 무엇을 고르나.**\
  크기·불변성·복사 비용·방어적 복사가 거기다. (3)의 `in` 이 거기서 결론난다.
- [03번 — 박싱과 언박싱](../03-boxing-and-unboxing/) — ★★ **값 타입이 참조 세계로 올라갈 때.**\
  (6)의 `ReferenceEquals(5, 5)` 와 (5)의 「박싱 1000번 = 24000바이트」가 거기서 이어진다.
- [04번 — 변수 선언·`var`·타겟 타입 `new`](../04-var-and-target-typed-new/) — **선언 자리의 문법.**\
  (1)의 `var s2 = s1;` 이 왜 `Point` 로 추론되는지가 거기다.
- [목록의 **06번 주제**](../06-nullable-reference-types/)(널 허용 참조 타입) — (7)에서 `string s = null;` 이 경고 없이 통과한 이유.
- [목록의 **08번 주제**](../08-nullable-value-types/)(`Nullable<T>`) — ★ (7)의 정본.
- 목록의 **19번 주제**(동등성 규칙) — (1)의 `Equals` 가 타입마다 다른 이유.
- 목록의 **44번 주제**(`ref`/`out`/`in`) — ★ (3)의 정본.
- 목록의 **45번 주제**(`ref` 지역·`ref struct`) · **46번 주제**(`Span<T>`) — (8)의 `IsReferenceOrContainsReferences` 가 거기서 쓰인다.
- C++ 갈래 목록([`cpp/syntax/README.md`](../../../cpp/syntax/README.md))의 **07번**(참조와 포인터) —\
  ★★ **축이 다르다.** 거기서 갈리는 것은 「이름이냐 쪽지냐」이고 **둘 다 참조 의미론**이다.\
  여기서 갈리는 것은 「**값이 들어 있냐 참조가 들어 있냐**」다. C++ 의 `Point p = q;` 는 **C# 의 구조체 대입과 같고**,\
  C# 의 `Node n = m;` 은 **C++ 의 `Point* p = q;` 와 같다.**
- Go 갈래 목록([`go/syntax/README.md`](../../../go/syntax/README.md))의 **05번**(배열과 슬라이스) —\
  ★ 같은 집안의 질문이다. Go 도 **배열은 값, 슬라이스는 헤더**라 「대입이 무엇을 복사하나」가 축이다.

## 용어 풀이

> **값 타입(value type)** — 변수 안에 값이 직접 들어 있는 타입. `struct`·`enum`·내장 숫자·튜플·`Nullable<T>`.

> **참조 타입(reference type)** — 변수 안에 참조만 들어 있는 타입. `class`·배열·`string`·델리게이트·인터페이스.

> **값 전달(pass by value)** — 인자의 **복사본**을 넘기는 것. C# 의 기본값이며, 참조 타입에서는 **참조가 복사**된다.

> **`ref` 전달** — **변수가 놓인 자리**를 넘기는 것. 메서드가 그 변수를 **갈아 끼울 수 있다**.\
> 예: `Replace(ref n)` 안에서 `n = new Node()` 를 하면 밖의 `n` 도 새 객체를 본다.

> **`in` 매개변수** — 자리를 넘기되 **읽기만** 허용하는 것(C# 7.2). 쓰면 `CS8332` 로 막힌다.

> **힙 할당(heap allocation)** — GC 영역에서 공간을 얻는 것.\
> 예: `new Node()` 가 24바이트. `new Point()` 는 **0바이트**다.

> **인터닝(interning)** — 같은 내용의 문자열 리터럴을 **한 객체로 공유**하는 것.\
> 예: `"hello"` 를 두 번 써도 `ReferenceEquals` 가 참이다.

> **박싱(boxing)** — 값 타입을 힙 객체로 감싸 참조 타입 자리에 넣는 것. 정본은 [03번](../03-boxing-and-unboxing/).

> **IL(Intermediate Language)** — C# 컴파일러가 내는 중간 코드. `.dll` 안에 들어 있고 런타임이 JIT 로 기계어로 바꾼다.\
> 예: `initobj` 는 자리를 0 으로 밀라는 것, `newobj` 는 힙에서 객체를 만들라는 것.

## 더 들어가면

- **`ref` 지역·`ref` 반환** — 「참조를 값처럼 들고 다니기」. ★ 이 문서는 안 던졌다. 정본은 목록의 **45번 주제**.
- **`ref struct`·`Span<T>`** — 힙으로 탈출할 수 없는 구조체. ★ 안 던졌다(목록의 **45**·**46번 주제**).
- **32비트에서의 크기** — (5)·(8)의 숫자는 전부 **x64** 다. `IntPtr.Size == 8` 을 머리말에서 확인했다.\
  ★ 32비트 런타임은 **안 돌려 봤다**(이 머신에 없다).
- **서버 GC** — `GCSettings.IsServerGC` 가 **`False`**(워크스테이션 GC)인 판에서만 쟀다.\
  ★ 할당 **증분**은 GC 모드와 무관하지만, **안 돌려 봤다는 사실**을 적어 둔다.
- **`Unsafe.As`·`MemoryMarshal`** — 값 타입의 비트를 직접 다루는 도구. ★ 안 던졌다.
- **`record class` 와 `record struct`** — `record` 는 기본이 참조 타입이다. 정본은 [02번](../02-struct-vs-class-choosing/)과 목록의 **18번 주제**.
