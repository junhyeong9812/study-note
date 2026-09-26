# csharp/syntax/08 — 널 허용 값 타입 `Nullable<T>` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [ECMA-334 7판(2023-12)](https://ecma-international.org/publications-and-standards/standards/ecma-334/) · [Microsoft Learn — C# 언어 레퍼런스](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/) · [Learn — `checked`/`unchecked`](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/statements/checked-and-unchecked) · [Learn — 널 허용 값 형식](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/builtin-types/nullable-value-types) · [Learn — 널 허용 참조 형식](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/builtin-types/nullable-reference-types) · [Learn — 멤버 접근·널 조건 연산자](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/operators/member-access-operators)
> **실행 검증** — 이 문서의 모든 출력·진단·IL·할당 바이트는 **.NET SDK 10.0.401** ·\
> 런타임 **`.NET 10.0.12`**(`Microsoft.NETCore.App`) · 타겟 **`net10.0`** · **linux-x64** 에서 실제로 돌려 얻은 것이다(2026-09-25).\
> ★ 블록은 캡처 스크립트가 파일로 받아 조립기가 끼워 넣은 것이다 — 사람이 옮겨 적은 줄은 하나도 없다.\
> ★ 소스 펜스의 첫 줄(`// cs0Nb-….cs` 꼴)도 **캡처가 찍은 것**이다. 원고에 손으로 쓴 배너는 없다.
> ★★★ **진단 언어를 영어로 고정했다.** 안 주면 **로캘을 따라 한국어로 나와 재현이 안 된다** —\
> 01\~04 가 실측으로 받은 한국어 판이 ``error CS0029: 암시적으로 'string' 형식을 'int' 형식으로 변환할 수 없습니다.`` 였다.\
> 고정하는 법은 둘을 같이 거는 것이다 — 환경변수 **`DOTNET_CLI_UI_LANGUAGE=en`** 과 `csc` 플래그 **`-preferreduilang:en-US`**.
> **던진 형태** — MSBuild(`dotnet build`·`dotnet run`)를 **안 썼다.** Roslyn 컴파일러를 **직접** 부른다 —\
> 그래야 `bin/`·`obj/` 가 원리상 안 생기고, 진단 경로가 **절대 경로가 아니라 파일명**으로 나오며, 한 판이 0.3초 안에 끝난다.\
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
>           -preferreduilang:en-US -langversion:latest "$@"; }
> ```
>
> **`-debug` 를 안 줬다** — PDB 가 없으면 스택 트레이스에 **절대 경로와 줄 번호가 안 박힌다**.\
> 그래서 이 문서의 트레이스는 ``at Program.<Main>$(String[] args)`` 에서 끝나고, 어느 머신에서 돌려도 같다.\
> **IL 덤프는 `-optimize` 없이**(기본 디버그) 낸 것이라 `nop` 이 섞여 있고 소스 구조가 그대로 보인다.\
> IL 을 찍는 `cs-il.cs`(82줄, 외부 도구 없이 BCL 만 쓴다)의 전문은 [03번](../03-boxing-and-unboxing/2-summary.md)의 (0)절에 있다.
> **버전** — `Nullable<T>` 와 `T?` 문법은 **C# 2부터**. 리프티드 연산자·3값 비교도 그때부터다.\
> ★ **[06번](../06-nullable-reference-types/)의 `string?` 보다 여섯 판 먼저 나왔다**(C# 2 대 C# 8) — **같은 기호인데 나이가 다르다.**\
> `is` 패턴으로 꺼내기(`x is int v`)는 **C# 7부터**, `where T : struct` 에서 `T?` 의 해석은 **C# 8부터** 널 맥락과 얽힌다.
> **경계** — `Nullable<T>` 가 **구조체**라는 사실이 이 주제의 토대이고, **값 타입이 무엇인가**는 [01번](../01-value-types-and-reference-types/)이 정본이다.\
> ★★★ **박싱의 정본은 [03번](../03-boxing-and-unboxing/)** 이다 — 여기서는 **그 규칙이 `Nullable<T>` 에서만 예외가 되는 것**만 다룬다((5)).\
> `?.`·`??`·`??=` 는 [07번](../07-null-operators/)이 정본이다 — 여기는 **타입 쪽**이다.\
> 참조 타입의 `?` 는 [06번](../06-nullable-reference-types/)이 정본이고, **완전히 다른 기능**이다((1)).\
> `struct` 를 언제 고르나는 [02번](../02-struct-vs-class-choosing/), 제네릭 제약은 목록의 **25번 주제**,\
> 동등성 규칙은 목록의 **19번 주제**, 패턴 매칭은 목록의 **21번 주제**다.\
> 대비 — Java 의 [원시 타입과 래퍼 편](../../../java/syntax/01-primitives-and-wrappers/).\
> ★★ **거기서는 「널을 담는 정수」가 `Integer` 라는 객체**다 — **힙을 쓴다.** 여기는 **구조체**라 안 쓴다((2)·(5)).
> ★★ **흔들리는 칸 / 안 흔들리는 칸** — 제출 전 재대조는 이 표를 기준으로 판정한다.
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | ★ **`GC.GetAllocatedBytesForCurrentThread()` 의 절댓값**(프로세스 시작부터의 누적이다) | ★★★ **두 호출 사이의 증분**과 **그 증분이 0 이냐 아니냐** |
> | 시간·CPU 상태 — 이 문서는 **시간을 한 번도 안 쟀다** | **진단 코드**(`CS0220`·`CS8602` 류) · **진단 문구** · **`(행,열)`** |
> | 객체 주소 · `GetHashCode()` 의 참조형 값 | **`cc exit` 와 `run exit`**(갈라 적었다) |
> | `dotnet` 패치 버전이 오르면 달라질 수 있는 것 | **IL 명령어 열**(`add` · `add.ovf` · `box` · `brtrue.s` · `initobj`) |
> | — | **할당 바이트의 증분값**(24 · 32 · 0) · **타입 크기**(`Unsafe.SizeOf`) |

## 한눈에 — 쉽게 말하면

**`int?` 는 「숫자 칸 하나 + 「썼음/안 썼음」 체크박스 하나」가 붙은 서식이다.**

종이 서식에 「나이」 칸이 있고 그 옆에 **「기재함」 체크박스**가 있다고 하자.
체크가 안 됐으면 나이 칸에 무엇이 적혀 있든 **읽으면 안 된다.**
서식 자체는 **여전히 종이 한 장**이다 — 어디 다른 서랍에 넣어 둔 것이 아니다.

그런데 이 서식을 **우편으로 부칠 때**(`object` 에 넣을 때) 이상한 일이 일어난다 —
**체크박스를 떼어 내고 숫자만 봉투에 넣거나, 체크가 없으면 아예 빈 봉투를 보낸다.**

| 비유 | 실체 |
|---|---|
| **체크박스 + 숫자 칸** | ★★ `Nullable<T>` 는 **`bool hasValue` + `T value` 를 든 구조체**다((1)·(2)) |
| **종이 한 장이다** | ★ `int?` 는 **8바이트** — `int` 4 + 정렬 포함((2)). **힙을 안 쓴다** |
| **체크 없이 숫자를 읽으면** | `Value` → **`InvalidOperationException`**((4)) |
| ★★★ **봉투에는 숫자만 들어간다** | ★★★ `object o = someInt?` → **`int` 가 박싱된다**((5)) |
| ★★★ **체크가 없으면 빈 봉투다** | ★★★ `object o = nullInt?` → **`null` 참조 · 할당 0바이트**((5)) |
| **봉투를 열어 보면 「숫자」라고 적혀 있다** | `GetType()` 이 **`System.Int32`** 를 답한다((6)) |
| ★ **빈 칸끼리 더하면 빈 칸** | 리프티드 연산자 — 한쪽이 널이면 결과가 널((7)) |
| ★★ **빈 칸과 크기를 견주면 「모름」이 아니라 「아니오」** | `null > 1` 도 `null <= 1` 도 **`false`**((7)) |

- ★★★ **이 주제의 한 줄** — **`int?` 는 참조가 아니라 구조체다.**\
  `null` 이라고 쓰지만 **널 참조가 아니라** 「**`HasValue` 가 `false` 인 값**」이다.\
  그래서 **힙을 안 쓰고**, **`is null` 이 되고**, **`GetType()` 은 부를 수가 없다**((6)).
- ★★★ **박싱만은 예외다** — [03번](../03-boxing-and-unboxing/)이 「값 타입을 `object` 에 넣으면 그 타입이 박싱된다」고 했는데\
  **`Nullable<T>` 는 그 규칙을 따르지 않는다.** `Nullable<int>` 가 아니라 **`int` 가 박싱되고, 널이면 아예 할당이 없다**((5)).
- ★★ **비교는 3값 논리인데 `==` 는 2값이다** — 같은 「널과의 비교」인데 **연산자마다 규칙이 다르다**((7)).\
  [07번](../07-null-operators/)의 `arr?.Length < 2` 함정이 여기서 설명된다.

```text
   int? 는 무엇인가 — 스택 위의 8바이트

   int  n = 5;                 int? m = 5;                  int? none = null;
   ┌──────────┐                ┌──────────┬──────────┐      ┌──────────┬──────────┐
   │    5     │                │  value=5 │ hasValue │      │ value=0  │ hasValue │
   │ 4바이트   │                │  4바이트  │  =true   │      │(안 읽는다)│  =false  │
   └──────────┘                └──────────┴──────────┘      └──────────┴──────────┘
                                      8바이트                       8바이트
                                  ★ 힙이 없다. 참조도 없다.

   Java 의 Integer 였다면
   ┌────────┐      힙
   │  참조   │──> ┌──────────────────┐   ★ 객체 헤더 + 값. null 이면 참조가 null.
   └────────┘     │ 헤더 … value=5   │      C# 은 이 그림이 아니다.
                  └──────────────────┘
```

```text
   ★★★ 박싱만은 03번의 규칙을 안 따른다

   object o = (int)5;        →  힙에 [헤더 | 5]           +24바이트   (03번의 규칙 그대로)
   object o = (int?)5;       →  힙에 [헤더 | 5]           +24바이트   ★ Nullable<int> 가 아니라 int 다
   object o = (int?)null;    →  아무것도 안 만든다          +0바이트    ★ 그냥 null 참조가 된다

   그 귀결
     o is int          → true          o.GetType()  → System.Int32   (Nullable<int> 가 아니다)
     (int?)o           → 되돌아온다     none.GetType() → NullReferenceException  ★ 부를 대상이 없다
```

> **`Nullable<T>`** — `T value` 와 `bool hasValue` 를 든 **구조체**. `T?` 는 그 축약 표기다.\
> `T` 는 **널 아님 값 타입**이라야 한다 — 참조 타입도, `int?` 자체도 넣을 수 없다(문법 절).

> **`HasValue` / `Value`** — 체크박스와 숫자 칸. `HasValue` 가 `false` 일 때 `Value` 를 읽으면\
> **`InvalidOperationException`** 이다((4)). 안전한 짝이 **`GetValueOrDefault()`** 다.

> **리프티드 연산자(lifted operator)** — `T` 의 연산자를 `T?` 로 「들어 올린」 것.\
> **한쪽이라도 널이면 결과가 널**이다 — 단 **비교와 `bool?` 논리는 예외**다((7)).

> **3값 논리(three-valued logic)** — `true`/`false` 에 「모름」이 더해진 논리.\
> ★ C# 의 `<`·`>` 는 **「모름」을 `false` 로 접어 버린다** — 그래서 **부정이 성립하지 않는다**((7)).

> **박싱** — 값 타입을 `object`·인터페이스에 담을 때 힙에 객체를 만드는 것([03번](../03-boxing-and-unboxing/)).\
> ★★★ **`Nullable<T>` 에서만 규칙이 다르다**((5)).

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. **`int?` 는 무엇인가** — 타입인가 주석인가, 힙을 쓰나 안 쓰나, 크기가 얼마인가((1)·(2)).
2. **`object` 에 넣으면 무엇이 되나** — [03번](../03-boxing-and-unboxing/)의 규칙이 여기서 왜 깨지나((5)·(6)).
3. **널이 섞인 연산과 비교는 무엇을 돌려주나** — 그리고 **왜 부정이 성립하지 않나**((7)).

## 동작 방식

### (0) 이 주제가 쓰는 다섯 창

| 창 | 무엇을 보여 주나 | 이 주제에서 |
|---|---|---|
| ★★★ **할당 바이트** | ★★★ **박싱이 `int` 인 것과 널이면 0인 것** — 이 주제의 중심 | (5) |
| ★★ **IL** | ★★ **`box Nullable<int>` 라고 적혀 있는데 런타임이 다르게 한다** | (8) |
| **실행 출력** | 타입·크기·리프티드·3값 비교 | (1)·(2)·(6)·(7) |
| **예외 전문** | `Value` 를 잘못 읽은 것 · `GetType()` 이 터지는 것 | (4)·(6) |
| **컴파일 진단** | ★ `sizeof(int?)` 가 막히는 것 · 못 감싸는 타입 | (2)·문법 절 |

★★★ **이 주제의 중심은 할당 바이트다** — [03번](../03-boxing-and-unboxing/)과 같은 창이고, **그것이 의도다.**\
03번이 「값 타입을 `object` 에 넣으면 +24바이트」를 확정했으므로,
여기서 같은 자를 대어 `int?` 가 **똑같이 +24**(`Nullable<int>` 의 +32 가 아니라)라는 것을 보이면
「**`Nullable<int>` 가 아니라 `int` 가 박싱됐다**」가 증명된다. **같은 도구로 앞 주제를 되받는 구조**다.

★★ **IL 이 여기서 특이하게 쓰인다** — (8)의 덤프에는 **`box System.Nullable<System.Int32>`** 라고 적혀 있다.\
**IL 을 믿으면 틀린다.** 런타임이 그 명령을 **특별 취급**하기 때문이다.
★ 「IL 이 근거다」라고 앞 주제들에서 계속 말했는데, **여기가 그 한계**다 — **IL 과 할당 바이트가 갈린다.**

### (1) ★★ `int?` 는 `Nullable<int>` 구조체다

**언제 쓰나** — 가장 먼저 무는 자리. 「`null` 이니까 참조겠지」가 틀린다.

```text
===== 소스: cs08b-struct.cs =====
#nullable enable
using System;

Console.WriteLine($"typeof(int?)                          = {typeof(int?)}");
Console.WriteLine($"typeof(int?) == typeof(Nullable<int>) : {typeof(int?) == typeof(Nullable<int>)}");
Console.WriteLine($"typeof(int?).IsValueType              : {typeof(int?).IsValueType}");
Console.WriteLine($"typeof(int?).BaseType                 = {typeof(int?).BaseType}");
Console.WriteLine($"Nullable.GetUnderlyingType(typeof(int?)) = {Nullable.GetUnderlyingType(typeof(int?))}");
Console.WriteLine($"Nullable.GetUnderlyingType(typeof(int))  = {(Nullable.GetUnderlyingType(typeof(int))?.ToString() ?? "(null)")}");
Console.WriteLine();

int? none = null;
int? some = 5;
Console.WriteLine($"none.HasValue            : {none.HasValue}");
Console.WriteLine($"some.HasValue            : {some.HasValue}   some.Value = {some.Value}");
Console.WriteLine($"none.GetValueOrDefault() : {none.GetValueOrDefault()}");
Console.WriteLine($"none.GetValueOrDefault(9): {none.GetValueOrDefault(9)}");
Console.WriteLine($"default(int?) is null    : {default(int?) is null}");
Console.WriteLine($"none is null             : {none is null}   ← 참조가 아닌데 is null 이 된다");
if (some is int unwrapped) Console.WriteLine($"some is int unwrapped    : True (unwrapped={unwrapped})");
Console.WriteLine($"none.ToString()          : '{none.ToString()}' (길이 {none.ToString()!.Length})");
Console.WriteLine($"none.Equals(null)        : {none.Equals(null)}");
Console.WriteLine($"none.GetHashCode()       : {none.GetHashCode()}");
===== csc -out:ex.dll cs08b-struct.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
typeof(int?)                          = System.Nullable`1[System.Int32]
typeof(int?) == typeof(Nullable<int>) : True
typeof(int?).IsValueType              : True
typeof(int?).BaseType                 = System.ValueType
Nullable.GetUnderlyingType(typeof(int?)) = System.Int32
Nullable.GetUnderlyingType(typeof(int))  = (null)

none.HasValue            : False
some.HasValue            : True   some.Value = 5
none.GetValueOrDefault() : 0
none.GetValueOrDefault(9): 9
default(int?) is null    : True
none is null             : True   ← 참조가 아닌데 is null 이 된다
some is int unwrapped    : True (unwrapped=5)
none.ToString()          : '' (길이 0)
none.Equals(null)        : True
none.GetHashCode()       : 0
```

- ★★★ **`typeof(int?)` 가 ``System.Nullable`1[System.Int32]``** 다 — **`int?` 는 그 축약 표기**일 뿐이다.\
  `typeof(int?) == typeof(Nullable<int>)` 가 `True` 인 것이 그 확인이다.
- ★★★ **`IsValueType` 이 `True` 이고 `BaseType` 이 `System.ValueType`** 이다 — **구조체다.**\
  ★ 「`null` 을 담는데 값 타입」이 이 주제의 핵심 긴장이다.
- **`Nullable.GetUnderlyingType`** 이 `int?` 에는 `System.Int32` 를, `int` 에는 `(null)` 을 준다.\
  ★ **이것이 「`Type` 이 널 허용 값 타입인가」를 판별하는 정식 방법**이다((6)에서 왜 다른 방법이 안 되는지 나온다).
- ★★ **`none is null` 이 `True`** 다 — **참조가 아닌데 `is null` 이 된다.**\
  컴파일러가 이것을 **`!none.HasValue`** 로 바꾸기 때문이다((8)의 `IsNull` 이 그 IL 이다).
- **`some is int unwrapped`** 로 **검사와 꺼내기를 한 번에** 한다(C# 7 패턴). Learn 이 권하는 형태다.
- ★ **`none.ToString()` 이 빈 문자열**이다(길이 0) — **`"null"` 이 아니다.**\
  [07번](../07-null-operators/)의 (6)에서 본 그 함정이다.
- ★ **`none.Equals(null)` 이 `True`** 이고 **`none.GetHashCode()` 가 `0`** 이다 —\
  **널인 `int?` 도 사전 키로 쓸 수 있다.** 참조 널이었으면 못 했을 일이다.

### (2) ★ 크기 — 한 겹이 **공짜가 아니다**

**언제 쓰나** — 배열·구조체 필드에 `T?` 를 넣을지 정할 때.

```text
===== 소스: cs08b-size.cs =====
using System;
using System.Runtime.CompilerServices;

Row("bool",  Unsafe.SizeOf<bool>(),  Unsafe.SizeOf<bool?>());
Row("byte",  Unsafe.SizeOf<byte>(),  Unsafe.SizeOf<byte?>());
Row("char",  Unsafe.SizeOf<char>(),  Unsafe.SizeOf<char?>());
Row("short", Unsafe.SizeOf<short>(), Unsafe.SizeOf<short?>());
Row("int",   Unsafe.SizeOf<int>(),   Unsafe.SizeOf<int?>());
Row("long",  Unsafe.SizeOf<long>(),  Unsafe.SizeOf<long?>());
Row("double",Unsafe.SizeOf<double>(),Unsafe.SizeOf<double?>());
Row("decimal",Unsafe.SizeOf<decimal>(),Unsafe.SizeOf<decimal?>());
Row("Guid",  Unsafe.SizeOf<Guid>(),  Unsafe.SizeOf<Guid?>());

static void Row(string name, int bare, int lifted)
    => Console.WriteLine($"{name,-8} {bare,3}바이트  →  {name + "?",-9}{lifted,3}바이트   (+{lifted - bare})");
===== csc -out:ex.dll cs08b-size.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
bool       1바이트  →  bool?      2바이트   (+1)
byte       1바이트  →  byte?      2바이트   (+1)
char       2바이트  →  char?      4바이트   (+2)
short      2바이트  →  short?     4바이트   (+2)
int        4바이트  →  int?       8바이트   (+4)
long       8바이트  →  long?     16바이트   (+8)
double     8바이트  →  double?   16바이트   (+8)
decimal   16바이트  →  decimal?  24바이트   (+8)
Guid      16바이트  →  Guid?     20바이트   (+4)
```

- ★★ **`int` 4바이트 → `int?` 8바이트.** `bool hasValue` 하나 때문에 **두 배가 됐다.**\
  ★ 1바이트만 늘 것 같지만 **정렬(alignment)** 때문에 4바이트가 붙는다.
- **`byte?` 는 2바이트**(1 + 1), **`long?` 은 16바이트**(8 + 8), **`Guid?` 는 20바이트**(16 + 4).\
  ★ **증가폭이 타입의 정렬 요구에 달렸다** — `byte` 는 +1, `int` 는 +4, `long`·`double` 은 +8.
- ★★★ **그래도 힙을 안 쓴다.** 8바이트가 **스택이나 포함 객체 안에** 그대로 있다.\
  Java 의 `Integer` 는 **참조 8바이트 + 힙 객체 16바이트 이상**이다 — **그림이 완전히 다르다.**
- ★ **`sizeof(int?)` 는 컴파일 에러**다.

```text
===== 소스: cs08b-sizeof.cs =====
using System;

Console.WriteLine(sizeof(int?));
===== csc -out:ex.dll cs08b-sizeof.cs (cc exit=1) =====
cs08b-sizeof.cs(3,19): error CS0233: 'int?' does not have a predefined size, therefore sizeof can only be used in an unsafe context
```

- **`error CS0233: 'int?' does not have a predefined size, therefore sizeof can only be used in an unsafe context`**.\
  ★ `sizeof` 의 **`unsafe` 없는 판은 내장 타입만** 받는다([01번](../01-value-types-and-reference-types/)의 `sizeof(Point)` 와 같은 진단이다).\
  안전한 대안이 **`Unsafe.SizeOf<T>()`** 이고, 위 표가 그것으로 잰 것이다.

### (3) 값을 꺼내는 네 가지 방법

**언제 쓰나** — 코드 리뷰에서 「이건 터질 수 있나」를 판단할 때.

| 방법 | 널일 때 | 언제 쓰나 |
|---|---|---|
| `x.Value` | ★ **`InvalidOperationException`**((4)) | `HasValue` 를 **바로 앞에서** 확인했을 때만 |
| `(int)x` | ★ **`InvalidOperationException`**(같은 것으로 컴파일된다) | 〃 |
| `x ?? 기본값` | **기본값** | ★★ 가장 흔한 형태 — [07번](../07-null-operators/) |
| `x.GetValueOrDefault()` | **`default(T)`**(`int` 면 `0`) | 기본값이 `default` 로 충분할 때 |
| `x.GetValueOrDefault(9)` | **`9`** | `??` 와 같은 일을 메서드로 |
| `if (x is int v)` | **블록에 안 들어간다** | ★★ **검사와 꺼내기를 한 번에** — Learn 이 권하는 형태 |

- ★★ **`x ?? 0` 과 `x.GetValueOrDefault()` 는 같은 값을 준다** — 취향 문제다.\
  ★ 다만 **`GetValueOrDefault()` 는 「기본값이 무엇인지」가 코드에 안 보인다.** 읽는 쪽에는 `?? 0` 이 낫다.
- ★★★ **`x.Value` 와 `(int)x` 가 같은 것**이라는 점이 중요하다 — **캐스트가 더 안전해 보이지만 아니다.**

### (4) `Value` 를 잘못 읽으면 — 예외 전문

**언제 쓰나** — 「`NullReferenceException` 이 나겠지」를 반증할 때.

```text
===== 소스: cs08b-value.cs =====
using System;

int? none = null;
Console.WriteLine(none.Value);
===== csc -out:ex.dll cs08b-value.cs && dotnet ex.dll (cc exit=0 · run exit=134) =====
Unhandled exception. System.InvalidOperationException: Nullable object must have a value.
   at System.Nullable`1.get_Value()
   at Program.<Main>$(String[] args)
```

- ★★★ **`NullReferenceException` 이 아니라 `InvalidOperationException`** 이다.\
  **참조가 아니므로 널 참조 예외가 날 수가 없다** — 구조체의 속성이 스스로 던진 것이다.
- **메시지가 `Nullable object must have a value.`** 이고, **트레이스에 ``System.Nullable`1.get_Value()`` 가 찍혔다.**\
  ★ `-debug` 를 안 줬는데도 **BCL 프레임은 이름이 나온다**(메서드 이름은 메타데이터에 있다).
- ★ **예외 타입이 다른 것이 진단에 도움이 된다** — 로그에 `InvalidOperationException: Nullable object must have a value` 가 보이면\
  **널 참조가 아니라** 「**널 허용 값 타입을 잘못 꺼낸 것**」임을 바로 안다.

### (5) ★★★ 박싱 — 03번의 규칙이 여기서만 깨진다

**언제 쓰나** — 이 주제에서 **가장 중요한 자리.** [03번](../03-boxing-and-unboxing/)과 짝으로 읽는다.

```text
===== 소스: cs08b-box.cs =====
#nullable enable
using System;

Warm();

int plain = 5;
int? some = 5;
int? none = null;

long b0 = GC.GetAllocatedBytesForCurrentThread();
object boxedPlain = plain;
long b1 = GC.GetAllocatedBytesForCurrentThread();
object? boxedSome = some;
long b2 = GC.GetAllocatedBytesForCurrentThread();
object? boxedNone = none;
long b3 = GC.GetAllocatedBytesForCurrentThread();

Console.WriteLine($"object = int  (5)    : +{b1 - b0} 바이트");
Console.WriteLine($"object = int? (5)    : +{b2 - b1} 바이트   ← int 를 박싱한 것과 같은 수다");
Console.WriteLine($"object = int? (null) : +{b3 - b2} 바이트   ← 아예 할당이 없다");
Console.WriteLine();
Console.WriteLine($"boxedSome is null  : {boxedSome is null}");
Console.WriteLine($"boxedNone is null  : {boxedNone is null}   ← null 참조가 됐다");
Console.WriteLine($"boxedSome is int   : {boxedSome is int}");
Console.WriteLine($"boxedSome is int?  : {boxedSome is int?}");
Console.WriteLine($"boxedSome.GetType(): {boxedSome!.GetType()}");
Console.WriteLine();
Console.WriteLine($"(int)boxedSome     : {(int)boxedSome}");
Console.WriteLine($"(int?)boxedPlain   : {((int?)boxedPlain)!.Value}   ← 박싱된 int 를 int? 로 언박싱");
Console.WriteLine($"(int?)boxedNone    : HasValue={((int?)boxedNone).HasValue}   ← 예외가 아니다");

static void Warm() {
    int? w = 1; object a = 1; object? b = w;
    GC.KeepAlive(a); GC.KeepAlive(b);
    GC.GetAllocatedBytesForCurrentThread();
}
===== csc -out:ex.dll cs08b-box.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
object = int  (5)    : +24 바이트
object = int? (5)    : +24 바이트   ← int 를 박싱한 것과 같은 수다
object = int? (null) : +0 바이트   ← 아예 할당이 없다

boxedSome is null  : False
boxedNone is null  : True   ← null 참조가 됐다
boxedSome is int   : True
boxedSome is int?  : True
boxedSome.GetType(): System.Int32

(int)boxedSome     : 5
(int?)boxedPlain   : 5   ← 박싱된 int 를 int? 로 언박싱
(int?)boxedNone    : HasValue=False   ← 예외가 아니다
```

- ★★★ **`object = int?(5)` 가 `+24` 바이트**다 — **`object = int(5)` 와 똑같다.**\
  `Nullable<int>` 는 8바이트이므로 그것을 박싱했다면 **헤더 16 + 8 = 24**… 도 24라서 헷갈릴 수 있다.\
  **그래서 숫자만으로는 부족하고, 다음 줄들이 결정적이다.**
- ★★★ **`boxedSome.GetType()` 이 `System.Int32`** 다 — **`Nullable<int>` 가 아니다.**\
  **`int` 가 박싱된 것**이 확정된다.
- ★★★ **`object = int?(null)` 이 `+0` 바이트이고 `boxedNone is null` 이 `True`** 다.\
  **아무것도 만들지 않고 그냥 널 참조가 됐다.**\
  ★ [03번](../03-boxing-and-unboxing/)의 「값 타입을 `object` 에 넣으면 힙 할당이 생긴다」가 **여기서 깨진다.**
- ★★ **`boxedSome is int` 도 `True` 이고 `boxedSome is int?` 도 `True`** 다.\
  ★ **`is` 로는 둘을 구분할 수 없다** — Learn 이 못 박은 대로 **`is` 를 판별에 쓰면 안 된다**((6)).
- **되돌리기는 양방향으로 된다** — `(int)boxedSome` 도, **박싱된 `int` 를 `(int?)` 로 언박싱**하는 것도 된다.\
  ★★ **`(int?)boxedNone` 은 예외가 아니라 `HasValue=False`** 다 — **널 참조를 `T?` 로 언박싱하는 것은 합법**이다.\
  ★ [03번](../03-boxing-and-unboxing/)에서 `(int)null` 이 예외였던 것과 대비된다.
- ★★★ **이것은 언어가 보장하는 규칙**이다. Learn 이 두 줄로 못 박았다 —\
  **`HasValue` 가 `false` 면 박싱 결과가 널 참조**, **`true` 면 기반 타입 `T` 를 박싱**한다.\
  **구현 세부가 아니라 명세다.**

### (6) `GetType()` 이 `Nullable<int>` 를 안 준다 — 그리고 널이면 터진다

**언제 쓰나** — 리플렉션으로 「이거 널 허용인가」를 물을 때. **틀린 방법이 자연스러워 보인다.**

```text
===== 소스: cs08b-gettype.cs =====
using System;

int? some = 17;
Console.WriteLine($"some.GetType() = {some.GetType()}   ← Nullable<int> 가 아니다");

int? none = null;
Console.WriteLine(none.GetType());
===== csc -out:ex.dll cs08b-gettype.cs && dotnet ex.dll (cc exit=0 · run exit=134) =====
some.GetType() = System.Int32   ← Nullable<int> 가 아니다
Unhandled exception. System.NullReferenceException: Object reference not set to an instance of an object.
   at System.Object.GetType()
   at Program.<Main>$(String[] args)
```

- ★★★ **`some.GetType()` 이 `System.Int32`** 다. **`Nullable<int>` 가 아니다.**\
  **`GetType()` 은 `object` 의 메서드**라 부르는 순간 **박싱이 일어나고**, (5)의 규칙대로 **`int` 가 박싱되기 때문**이다.
- ★★★ **널이면 `NullReferenceException`** 이다.\
  박싱 결과가 **널 참조**라 **`GetType()` 을 부를 대상이 없다.**\
  ★ 트레이스에 **`at System.Object.GetType()`** 이 찍힌 것이 그 근거다.\
  ★★ **구조체의 메서드를 불렀는데 널 참조 예외가 나는** 희귀한 자리다.
- ★★ **그래서 판별은 `typeof` 와 `Nullable.GetUnderlyingType` 으로 한다**((1)).\
  `GetType()` 도 `is` 도 **둘 다 못 쓴다** — 앞엣것은 박싱 때문에, 뒤엣것은 (5)에서 본 대로 둘 다 `True` 라서.

### (7) ★★ 리프티드 연산자와 3값 비교

**언제 쓰나** — 널이 섞인 산술·비교를 쓸 때. **[07번](../07-null-operators/)의 함정이 여기서 설명된다.**

```text
===== 소스: cs08b-lifted.cs =====
#nullable enable
using System;

int? a = null, a2 = null, b = 1, c = 2;

Console.WriteLine($"b + c   = {Fmt(b + c)}");
Console.WriteLine($"a + c   = {Fmt(a + c)}");
Console.WriteLine($"a * c   = {Fmt(a * c)}");
Console.WriteLine($"-a      = {Fmt(-a)}");
Console.WriteLine();
Console.WriteLine($"a == null : {a == null}");
Console.WriteLine($"a == a2   : {a == a2}   ← 둘 다 null 이면 true 다 (SQL 의 NULL 과 다르다)");
Console.WriteLine($"a == b    : {a == b}");
Console.WriteLine($"a != b    : {a != b}");
Console.WriteLine();
Console.WriteLine($"a >  1 : {a > 1}");
Console.WriteLine($"a <= 1 : {a <= 1}   ← 부정이 성립하지 않는다");
Console.WriteLine($"a <  1 : {a < 1}");
Console.WriteLine($"a >= 1 : {a >= 1}");
Console.WriteLine($"!(a > 1) : {!(a > 1)}   ← 이것만 true 다");
Console.WriteLine();
Console.WriteLine($"Comparer<int?>.Default.Compare(null, 1) = {System.Collections.Generic.Comparer<int?>.Default.Compare(a, b)}");
Console.WriteLine($"  ← 정렬은 null 을 「가장 작은 것」으로 본다. 비교 연산자와 규칙이 다르다.");
Console.WriteLine();

bool? t = true, f = false, u = null;
Console.WriteLine($"true  & null = {Fmt(t & u)}");
Console.WriteLine($"true  | null = {Fmt(t | u)}   ← null 이 섞여도 결과가 난다");
Console.WriteLine($"false & null = {Fmt(f & u)}   ← 〃");
Console.WriteLine($"false | null = {Fmt(f | u)}");
Console.WriteLine($"!null        = {Fmt(!u)}");

static string Fmt<T>(T? v) where T : struct => v.HasValue ? v.Value.ToString()! : "null";
===== csc -out:ex.dll cs08b-lifted.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
b + c   = 3
a + c   = null
a * c   = null
-a      = null

a == null : True
a == a2   : True   ← 둘 다 null 이면 true 다 (SQL 의 NULL 과 다르다)
a == b    : False
a != b    : True

a >  1 : False
a <= 1 : False   ← 부정이 성립하지 않는다
a <  1 : False
a >= 1 : False
!(a > 1) : True   ← 이것만 true 다

Comparer<int?>.Default.Compare(null, 1) = -1
  ← 정렬은 null 을 「가장 작은 것」으로 본다. 비교 연산자와 규칙이 다르다.

true  & null = null
true  | null = True   ← null 이 섞여도 결과가 난다
false & null = False   ← 〃
false | null = null
!null        = null
```

- **산술은** 「**하나라도 널이면 널**」이다 — `a + c`·`a * c`·`-a` 가 전부 `null` 이다.
- ★★ **`==` 는 2값이다** — `a == null` 이 `True`, **`a == a2`(둘 다 널)가 `True`**, `a == b` 가 `False`.\
  ★ **SQL 의 `NULL = NULL` 이 「모름」인 것과 정반대**다. **C# 은 널끼리 같다고 본다.**
- ★★★ **`<`·`>`·`<=`·`>=` 는 넷 다 `false`** 다.\
  `a > 1` 도 `false`, `a <= 1` 도 `false`. **「모름」을 `false` 로 접어 버린다.**
- ★★★ **그래서 `!(a > 1)` 만 `true` 다** — **부정이 성립하지 않는다.**\
  `!(a > 1)` 은 `a <= 1` 과 **같지 않다.** 수학에서 참인 항등식이 여기서 깨진다.\
  ★ Learn 이 그것을 명시적으로 경고했다 — 「`<=` 가 `false` 라고 해서 `>` 가 `true` 라고 가정하지 마라」.
- ★★★ **`Comparer<int?>.Default.Compare(null, 1)` 이 `-1`** 이다 — **정렬은 널을 「가장 작은 것」으로 본다.**\
  ★★ **비교 연산자와 규칙이 다르다.** `null < 1` 은 `false` 인데 **정렬하면 널이 앞에 온다.**\
  ★ **같은 데이터를 「필터」와 「정렬」에 쓰면 두 규칙이 충돌한다** — 조용히 틀리는 자리다.
- ★★ **`bool?` 의 `&`·`|` 는 산술 규칙을 안 따른다** —\
  `true | null` 이 **`True`** 이고 `false & null` 이 **`False`** 다.\
  **한쪽만으로 답이 정해지면 널이 섞여도 결과가 난다** — SQL 의 3값 논리와 같은 규칙이다.\
  ★ Learn 이 「이 절의 규칙을 따르지 않는다」고 따로 주를 달아 둔 자리다.

### (8) ★★ IL — `box Nullable<int>` 라고 적혀 있는데 런타임이 다르게 한다

**언제 쓰나** — 「IL 이 근거다」의 **한계**를 보일 때.

```text
===== 소스: cs08b-il.cs =====
#nullable enable
Il.Dump(typeof(Probe), "BoxPlain");
Il.Dump(typeof(Probe), "BoxNullable");
Il.Dump(typeof(Probe), "LiftedAdd");
Il.Dump(typeof(Probe), "IsNull");

public static class Probe {
    public static object  BoxPlain(int n)         => n;
    public static object? BoxNullable(int? n)     => n;
    public static int?    LiftedAdd(int? a, int? b) => a + b;
    public static bool    IsNull(int? a)          => a == null;
}
===== csc -r:il.dll -out:ex.dll cs08b-il.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
--- Probe.BoxPlain ---
  IL_0000: ldarg.0
  IL_0001: box System.Int32
  IL_0006: ret
--- Probe.BoxNullable ---
  IL_0000: ldarg.0
  IL_0001: box System.Nullable<System.Int32>
  IL_0006: ret
--- Probe.LiftedAdd ---
  .locals [0] System.Nullable<System.Int32>
  .locals [1] System.Nullable<System.Int32>
  .locals [2] System.Nullable<System.Int32>
  IL_0000: ldarg.0
  IL_0001: stloc.0
  IL_0002: ldarg.1
  IL_0003: stloc.1
  IL_0004: ldloca.s 0
  IL_0006: call System.Nullable<System.Int32>::get_HasValue
  IL_000b: ldloca.s 1
  IL_000d: call System.Nullable<System.Int32>::get_HasValue
  IL_0012: and
  IL_0013: brtrue.s IL_0020
  IL_0015: ldloca.s 2
  IL_0017: initobj System.Nullable<System.Int32>
  IL_001d: ldloc.2
  IL_001e: br.s IL_0034
  IL_0020: ldloca.s 0
  IL_0022: call System.Nullable<System.Int32>::GetValueOrDefault
  IL_0027: ldloca.s 1
  IL_0029: call System.Nullable<System.Int32>::GetValueOrDefault
  IL_002e: add
  IL_002f: newobj System.Nullable<System.Int32>::.ctor
  IL_0034: ret
--- Probe.IsNull ---
  IL_0000: ldarga.s 0
  IL_0002: call System.Nullable<System.Int32>::get_HasValue
  IL_0007: ldc.i4.0
  IL_0008: ceq
  IL_000a: ret
```

- ★★★ **`BoxNullable` 의 IL 이 `box System.Nullable<System.Int32>`** 다.\
  **명령만 읽으면 「`Nullable<int>` 를 박싱한다」로 보인다** — 그런데 (5)에서 잰 것은 **`int` 박싱**이었다.
- ★★★ **어긋나는 것이 아니라 `box` 명령이 `Nullable<T>` 를 특별 취급하는 것**이다.\
  **CLI 가 그렇게 규정했고**, C# 명세도 같은 결과를 규정한다((5)).\
  ★★ **그래서 여기가 「IL 을 근거로 쓴다」의 한계다** — **명령 이름이 곧 동작이 아니다.**\
  ★ 01\~07 에서 IL 이 결정적 근거였는데, **이 한 자리에서는 할당 바이트가 IL 을 이긴다.**
- **`LiftedAdd` 가 리프티드 연산자의 전개를 그대로 보인다** —\
  `get_HasValue` 둘을 `and` 로 묶고, 거짓이면 `initobj`(널), 참이면 **`GetValueOrDefault` 둘을 `add`** 한 뒤 `newobj`.\
  ★ **`Value` 가 아니라 `GetValueOrDefault` 를 쓴다** — 이미 `HasValue` 를 확인했으니 **예외 검사를 두 번 할 이유가 없다.**
- **`IsNull`(`a == null`)이 `get_HasValue` + `ceq`** 다 — **참조 비교가 아니다.**\
  ★ (1)의 「`none is null` 이 `True`」가 이 IL 로 설명된다.
- ★ **`BoxPlain` 과 `BoxNullable` 의 명령 수가 같다**(3줄) — 소스만 봐서는 차이가 안 보이고,\
  **IL 로도 「타입 토큰이 다르다」까지만 보인다.** 나머지는 **런타임이 한다.**

## 문법 — 형태와 규칙

**형태** — 던져서 확인한 것만 싣는다.

```text
===== 소스: cs08b-form.cs =====
using System;

int? none = null;
int? some = 42;
int  plain = 7;

Console.WriteLine($"int? none = null        : HasValue={none.HasValue}");
Console.WriteLine($"int? some = 42          : HasValue={some.HasValue}  Value={some.Value}");
Console.WriteLine($"int? from int (암묵)    : {(int?)plain}");
Console.WriteLine($"int  from int? (명시)   : {(int)some}");
Console.WriteLine($"?? 로 접지             : {none ?? -1}");
Console.WriteLine($"GetValueOrDefault()     : {none.GetValueOrDefault()}");
Console.WriteLine($"GetValueOrDefault(9)    : {none.GetValueOrDefault(9)}");

// is 패턴으로 검사와 꺼내기를 한 번에 (Learn 이 권하는 형태)
if (some is int v) Console.WriteLine($"some is int v           : v={v}");
if (none is not int) Console.WriteLine($"none is not int         : 맞다");

// Nullable<T> 와 T? 는 같은 것을 가리킨다
Nullable<int> spelled = 5;
int? shorthand = 5;
Console.WriteLine($"Nullable<int> 와 int? 는 같은 타입 : {spelled.GetType() == shorthand.GetType()}");

// 배열·컬렉션에도 그대로 쓴다
int?[] row = new int?[3];
row[0] = 1;
Console.WriteLine($"int?[3] 의 기본값        : [{string.Join(", ", Array.ConvertAll(row, x => x.HasValue ? x.Value.ToString() : "null"))}]");

// 널 허용 값 타입을 널 허용 값 타입으로 또 감쌀 수는 없다 → 금지 사례에서 던진다
Console.WriteLine($"Nullable.GetUnderlyingType(typeof(int?)) = {Nullable.GetUnderlyingType(typeof(int?))}");
===== csc -out:ex.dll cs08b-form.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
int? none = null        : HasValue=False
int? some = 42          : HasValue=True  Value=42
int? from int (암묵)    : 7
int  from int? (명시)   : 42
?? 로 접지             : -1
GetValueOrDefault()     : 0
GetValueOrDefault(9)    : 9
some is int v           : v=42
none is not int         : 맞다
Nullable<int> 와 int? 는 같은 타입 : True
int?[3] 의 기본값        : [1, null, null]
Nullable.GetUnderlyingType(typeof(int?)) = System.Int32
```

- ★ **`int? from int (암묵)`** — 값 타입 `T` 에서 `T?` 로는 **암묵 변환**이고, 거꾸로는 **명시 캐스트**다.
- ★★ **`if (some is int v)`** 가 Learn 이 권하는 형태다 — **검사와 꺼내기가 한 문장**이고,\
  `HasValue` 를 확인하고 `Value` 를 읽는 두 단계보다 **틀릴 자리가 없다.**
- ★ **`int?[3]` 의 원소 기본값이 전부 널**이다 — `default(int?)` 가 「값 없음」이기 때문이다.\
  ★★ **`int[3]` 이었으면 `0` 셋**이었다. **「0 과 없음을 구분하고 싶다」가 이 타입을 쓰는 이유**다.

**금지 사례 — 던져서 받은 셋**

```text
===== 소스: cs08b-forbid.cs =====
using System;

int? maybe = null;
int plain = maybe;                 // 암묵 변환이 없다
Nullable<int?> nested = null;      // 널 허용을 또 감쌀 수 없다
Nullable<string> refType = null;   // 참조 타입은 못 감싼다
Console.WriteLine($"{plain} {nested.HasValue} {refType.HasValue}");
===== csc -out:ex.dll cs08b-forbid.cs (cc exit=1) =====
cs08b-forbid.cs(4,13): error CS0266: Cannot implicitly convert type 'int?' to 'int'. An explicit conversion exists (are you missing a cast?)
cs08b-forbid.cs(5,10): error CS0453: The type 'int?' must be a non-nullable value type in order to use it as parameter 'T' in the generic type or method 'Nullable<T>'
cs08b-forbid.cs(6,10): error CS0453: The type 'string' must be a non-nullable value type in order to use it as parameter 'T' in the generic type or method 'Nullable<T>'
```

| 쓴 것 | 진단 | 무엇을 말하나 |
|---|---|---|
| `int plain = maybe;` | ``error CS0266: Cannot implicitly convert type 'int?' to 'int'`` | ★★★ **진짜 타입이라 변환이 필요하다.** [06번](../06-nullable-reference-types/)의 `string?` 은 **경고**였다 |
| `Nullable<int?> nested` | ``error CS0453: The type 'int?' must be a non-nullable value type …`` | ★ **두 번 감쌀 수 없다.** `int??` 는 **문법 오류**로 먼저 걸린다 |
| `Nullable<string> refType` | ``error CS0453: The type 'string' must be a non-nullable value type …`` | ★ **참조 타입은 못 감싼다** — 이미 널을 담으니까 |

- ★★★ **첫 줄이 이 주제와 [06번](../06-nullable-reference-types/)을 가르는 한 줄이다.**\
  **값 타입은 에러, 참조 타입은 경고.** 같은 물음표인데 **강제력이 다르다.**
- ★ **`Nullable<T>` 의 제약이 `where T : struct`** 라서 두 에러가 같은 번호(`CS0453`)로 나온다.

**규칙**

- **`T?` 는 `Nullable<T>` 의 축약**이고 `T` 는 **널 아님 값 타입**이라야 한다.
- **`T` → `T?` 는 암묵**, **`T?` → `T` 는 명시**(그리고 널이면 `InvalidOperationException`).
- **산술 연산자는 리프티드**된다 — 한쪽이라도 널이면 결과가 널((7)).
- **`==`·`!=` 는 2값**(널끼리 같다), **`<`·`>`·`<=`·`>=` 는 널이 섞이면 `false`** ((7)).
- **`bool?` 의 `&`·`|` 는 예외**다 — 한쪽만으로 답이 정해지면 결과가 난다((7)).
- ★★ **박싱은 기반 타입 `T` 로 되고, 널이면 널 참조가 된다**((5)) — **언어 보장**이다.
- **`GetType()`·`is` 로 널 허용 여부를 판별할 수 없다** — `typeof` + `Nullable.GetUnderlyingType` 을 쓴다((6)).
- **`where T : struct` 제네릭에서 `T?` 는 `Nullable<T>`** 다(목록의 **25번 주제**).

## 어디서 틀리나

1. ★★★ **`int?` 를 참조로 아는 것** — **구조체**다((1)). 힙을 안 쓰고, `Value` 오류도 널 참조 예외가 아니다((4)).
2. ★★★ **`object` 에 넣으면 `Nullable<int>` 가 박싱된다고 믿는 것** — **`int` 가 박싱된다**((5)).
3. ★★★ **널인 `int?` 의 `GetType()` 을 부르는 것** — **`NullReferenceException`** 이다((6)).\
   **구조체의 메서드인데 널 참조 예외가 난다.**
4. ★★★ **`a > 1` 이 `false` 니까 `a <= 1` 은 `true` 겠지** — **둘 다 `false`** 다((7)).\
   **`if`/`else` 로 나눈 두 갈래가 널에서 같은 쪽으로 간다.**
5. ★★ **정렬과 비교의 규칙이 같다고 믿는 것** — `Comparer` 는 널을 **최소**로 보는데 `<` 는 `false` 다((7)).
6. ★★ **`is int?` 로 판별하려는 것** — 박싱된 `int` 도 `True` 다((5)).
7. ★ **`x.Value` 를 습관적으로 쓰는 것** — `??`·`GetValueOrDefault`·`is` 패턴이 더 안전하다((3)).
8. ★ **`(int)x` 가 `x.Value` 보다 안전하다고 믿는 것** — **같은 것**이다((3)).
9. ★ **크기가 안 는다고 믿는 것** — `int` 4 → `int?` 8 이다((2)). 큰 배열에서 두 배가 된다.
10. ★★ **`string?` 과 같은 기능으로 외우는 것** — 하나는 **주석**, 하나는 **타입**이다.\
    **위반하면 하나는 경고, 하나는 에러**다(문법 절).
11. ★ **`int?` 의 `ToString()` 이 `"null"` 을 준다고 믿는 것** — **빈 문자열**이다((1)).
12. ★★ **`bool?` 의 `&`·`|` 를 산술과 같은 규칙으로 읽는 것** — 다르다((7)).

## 구현 세부사항 대 언어 보장

★★ **이 주제는 「IL 이 근거다」가 처음으로 흔들리는 자리다.**

| 층 | 무엇을 말하나 | 이 주제의 예 |
|---|---|---|
| **언어 명세(ECMA-334)** | 무엇이 **언제나** 참인가 | `T?` 가 `Nullable<T>` 인 것 · 구조체인 것 · 리프티드 규칙 · **3값 비교가 `false` 인 것** · ★★ **박싱이 `T` 로 되고 널이면 널 참조인 것** · `Value` 가 `InvalidOperationException` 인 것 |
| **CLI(ECMA-335) / 런타임** | `box` 명령이 무엇을 하나 | ★★★ **`box Nullable<int>` 가 `int` 박싱 또는 널 참조를 만드는 것** — 명령 이름과 동작이 다르다((8)) |
| **런타임(CoreCLR) 구현** | 이 판이 **지금** 그렇게 하는 것 | 박싱 **+24바이트** · `int?` **8바이트**·`Guid?` **20바이트**(정렬) · 예외 메시지 · 종료 코드 134 |
| **이 판의 관찰** | 돌려 봤더니 이랬다는 것 | IL 의 정확한 명령 열 · `GetValueOrDefault` 를 쓰는 코드 생성((8)) · 트레이스에 ``System.Nullable`1.get_Value()`` 가 찍히는 것 |

- ★★★ **「`box` 명령이 `Nullable<T>` 를 특별 취급한다」는 구현이 아니라 규정**이다.\
  그래서 **어느 런타임에서도 `int` 가 박싱된다** — 「이 판에서만 그렇다」가 **아니다.**
- ★★ **반면 「+24바이트」는 구현**이다 — 객체 헤더 16과 최소 객체 크기 24가 **x64 CoreCLR 의 값**이다([03번](../03-boxing-and-unboxing/)).\
  ★ **「+0 이냐 아니냐」는 보장이고 「+24 냐」는 관찰**이다. 갈라 읽어라.
- ★★ **크기 8·16·20바이트도 구현**이다 — 필드 배치와 정렬은 런타임이 정한다.\
  ★ **「`T` 보다 크다」는 성질**이고 **「정확히 얼마」는 관찰**이다.

**언어가 보장하는 것**(구현이 바뀌어도 같다)

- **`T?` 가 `Nullable<T>` 이고 값 타입(구조체)인** 것 · **`T` 가 널 아님 값 타입이라야 하는** 것.
- **`T` → `T?` 암묵 · `T?` → `T` 명시**이고 널이면 **`InvalidOperationException`** 인 것.
- **리프티드 산술이** 「**하나라도 널이면 널**」인 것.
- **`==`/`!=` 가 2값이고(널끼리 같다), `<`·`>`·`<=`·`>=` 가 널이 섞이면 `false`** 인 것.
- **`bool?` 의 `&`·`|` 가 그 예외인** 것.
- ★★ **박싱이 기반 타입 `T` 로 되고, `HasValue` 가 `false` 면 널 참조가 되는** 것.
- **그 귀결로 `GetType()` 이 기반 타입을 주고 널이면 못 부르는** 것.
- **`is` 로 `T` 와 `T?` 를 구분할 수 없는** 것.

**구현에 달린 것**

- **박싱 +24바이트** · **`int?` 8바이트·`Guid?` 20바이트** 같은 **정확한 수치**.
- **IL 의 명령 열** — `GetValueOrDefault` 를 쓸지 `Value` 를 쓸지는 Roslyn 이 고른다.
- **예외 메시지 문구**·**트레이스 형식**·**종료 코드 134**.

## 언제 쓰고 언제 안 쓰나

| 쓸 것 | 언제 | 대가 |
|---|---|---|
| **`int?` 등 `T?`** | ★★ **「0 과 없음을 구분해야 하는」 값** — DB 의 `NULL`·미입력 폼 필드·선택적 설정 | 크기 두 배((2)) · 비교가 3값((7)) |
| **`T` + 센티널**(`-1`·`0`) | 성능이 결정적이고 범위에 여유가 있을 때 | ★ **센티널이 실제 값과 충돌**할 수 있다. 문서에 안 적히면 사고가 난다 |
| **`T` + `bool` 플래그를 손으로** | — | ★ `Nullable<T>` 가 정확히 그것이다. 직접 만들 이유가 없다 |
| **`TryGetValue` 류** | **실패 이유가 여럿**일 때 | `out` 이 읽기 흐름을 끊는다 |
| ★ **`?? 기본값`**([07번](../07-null-operators/)) | 널을 **즉시** 접지할 때 | — |
| ★★ **`is T v` 패턴** | 검사와 꺼내기를 한 번에 | — |

- ★★★ **`T?` 를 「DB 의 `NULL` 을 그대로 담는 그릇」으로 쓰는 것이 가장 정석**이다.\
  EF Core 도 널 허용 값 타입을 **선택 열**로 읽는다([06번](../06-nullable-reference-types/)의 메타데이터 이야기와 같은 집안이다).
- ★★ **비교가 걸리는 자리에서는 즉시 접지하라** — `(x ?? 0) < 2` 다((7)·[07번](../07-null-operators/)).\
  **`T?` 를 조건식에 날것으로 넣는 것이 이 주제 사고의 대부분**이다.
- ★ **큰 배열·핫 루프에서는 크기를 따져라** — `int?[1_000_000]` 은 `int[1_000_000]` 의 **두 배**다.\
  별도의 비트맵 + `int[]` 이 더 나을 수 있다(**이 문서는 안 쟀다**).
- ★ **`double?` 에는 `NaN` 이라는 대안이 이미 있다** — `double` 은 「없음」을 표현할 수단을 자체로 갖는다.\
  ★ 다만 `NaN` 은 **`==` 가 자기 자신과도 거짓**이라([05번](../05-numeric-types-checked-decimal/)) 다른 함정이 온다.

## 핵심 문장

1. ★★★ **`int?` 는 참조가 아니라 `Nullable<int>` 구조체다** — `null` 은 널 참조가 아니라 **`HasValue == false`** 다.
2. ★★★ **박싱만은 [03번](../03-boxing-and-unboxing/)의 규칙을 안 따른다** — **`int` 가 박싱되고, 널이면 할당이 0이다.**
3. ★★★ **`GetType()` 도 `is` 도 널 허용 판별에 못 쓴다** — 박싱이 먼저 일어나기 때문이다. `typeof` + `GetUnderlyingType` 이다.
4. ★★★ **`<`·`>` 는 널이 섞이면 양쪽이 다 `false`** 다 — **부정이 성립하지 않는다.**
5. ★★ **`==` 는 2값이고 정렬은 널을 최소로 본다** — **세 규칙이 서로 다르다.**
6. ★★ **한 겹은 공짜가 아니다** — `int` 4바이트가 `int?` 8바이트가 된다.
7. ★★ **여기서 IL 이 할당 바이트에 진다** — `box Nullable<int>` 라고 적혀 있는데 실제로는 `int` 가 박싱된다.

## 관련 자료

- [03번 — 박싱과 언박싱](../03-boxing-and-unboxing/) — ★★★ **(5)의 짝**이다. 거기가 규칙, 여기가 예외다.\
  거기의 **+24바이트**라는 자를 그대로 대어 **`int` 가 박싱됐다**를 잰다.
- [01번 — 값 타입과 참조 타입](../01-value-types-and-reference-types/) — `Nullable<T>` 가 구조체라는 사실이 그 위에 선다.
- [02번 — `struct` 대 `class`](../02-struct-vs-class-choosing/) — 작은 구조체의 크기·복사 비용 판단.
- [06번 — 널 허용 참조 타입](../06-nullable-reference-types/) — ★★ **같은 물음표, 다른 기능.**\
  위반이 **경고**(거기)와 **에러**(여기)로 갈리는 것이 그 차이의 요약이다.
- [07번 — 널 관련 연산자](../07-null-operators/) — `?.` 의 결과가 `T?` 가 되는 것과 **`arr?.Length < 2` 함정**의 짝.
- [05번 — 숫자 타입](../05-numeric-types-checked-decimal/) — `double` 의 `NaN` 이 「없음」의 다른 표현인 것.
- 목록의 **19번 주제**(동등성) — `Nullable<T>` 의 `Equals`·`GetHashCode` 가 기반 타입에 위임하는 것.
- 목록의 **21번 주제**(패턴 매칭) — `is int v`·`is not int` 가 이 타입에서 가장 깔끔한 형태인 이유.
- 목록의 **25번 주제**(제네릭 제약) — `where T : struct` 에서 `T?` 가 `Nullable<T>` 가 되는 것.
- **Java 의 [원시 타입과 래퍼 편](../../../java/syntax/01-primitives-and-wrappers/)** —\
  ★★★ **가장 크게 갈리는 대비**다. Java 의 `Integer` 는 **객체**라 **힙을 쓰고**, `null` 이 **진짜 널 참조**다.\
  그래서 Java 에서는 **언박싱이 `NullPointerException`** 인데 C# 은 **`InvalidOperationException`** 이다((4)).\
  ★ 캐시 때문에 `Integer` 는 `==` 가 값 범위에 따라 갈리기까지 한다 — C# 의 `int?` 에는 그 문제가 **없다**(값 타입이므로).

## 용어 풀이

- **`Nullable<T>`** — `T value` 와 `bool hasValue` 를 든 구조체. `T?` 는 축약 표기다.
- **`HasValue` / `Value`** — 값이 있는지와 그 값. 없는데 `Value` 를 읽으면 `InvalidOperationException`.
- **`GetValueOrDefault()`** — 없으면 `default(T)`(또는 인자로 준 값)를 준다. **예외를 안 던진다.**
- **리프티드 연산자** — `T` 의 연산자를 `T?` 로 들어 올린 것. 한쪽이 널이면 결과가 널.
- **3값 비교** — `<`·`>`·`<=`·`>=` 가 널이 섞이면 `false` 인 규칙. **부정이 성립하지 않는다.**
- **`Nullable.GetUnderlyingType`** — `Type` 이 널 허용 값 타입이면 기반 타입을, 아니면 널을 준다.\
  **판별의 정식 방법**이다.
- **`CS0453`** — `Nullable<T>` 의 `T` 가 널 아님 값 타입이 아니다.
- **`CS0266`** — `int?` 를 `int` 에 암묵 변환할 수 없다(**에러**).
- **`CS0233`** — `sizeof` 를 `unsafe` 없이 쓸 수 없는 타입이다.
- **`Unsafe.SizeOf<T>()`** — `sizeof` 의 안전한 대안. 이 문서의 크기 표가 그것으로 잰 것이다.

## 더 들어가면

- **`Nullable<T>` 의 실제 필드 배치** — `value` 가 먼저인지 `hasValue` 가 먼저인지는 **런타임이 정한다.**\
  ★ **이 문서는 크기만 쟀고 배치는 안 봤다.**
- **`Nullable.Compare` / `Nullable.Equals`** — 정적 헬퍼. (7)의 `Comparer<int?>` 와 같은 규칙이다. **안 던졌다.**
- **`where T : struct` 제네릭에서의 `T?`** — 목록의 **25번 주제**. **안 던졌다.**
- **`Span<T?>` 와 `Nullable<T>` 의 레이아웃** — 상호운용에서 문제가 되는 자리. **안 던졌다.**
- **`[NotNullWhen]` 등 널 상태 특성이 값 타입에 쓰이는 것** — `TryParse(out int? result)` 류. **안 던졌다.**
- ★ **왜 `Nullable<Nullable<T>>` 를 막았나** — `T?` 를 「한 겹」으로 고정하면 **리프티드 규칙이 단순해진다.**\
  두 겹을 허용하면 「널인데 어느 층의 널인가」가 생긴다 — **[06번](../06-nullable-reference-types/)의 `string??` 이 없는 것과 같은 이유**다.
- ★★ **`int?` 의 `Equals` 가 기반 타입에 위임한다** — 그래서 `((int?)5).Equals(5)` 가 `True` 다.\
  **박싱 규칙((5))과 같은 설계 방향**이다 — 「겉보기에 `int` 처럼 굴게 한다」.
