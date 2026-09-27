# csharp/syntax/04 — 변수 선언·`var`·타겟 타입 `new` — 정리 (힌트)

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
> **버전** — `var` 는 **C# 3.0부터** · **타겟 타입 `new()`** 는 **C# 9부터** ·\
> **람다·메서드 그룹의 자연 타입**(`var f = () => 1;`)은 **C# 10부터** · `dynamic` 은 **C# 4부터**다.\
> ★ 「`var f = () => 1;` 이 안 된다」는 **C# 9 까지의 이야기**다 — (4)에서 던져 확인했다.
> **경계** — 「값이냐 참조냐」는 [01번](../01-value-types-and-reference-types/), 「`struct` 냐 `class` 냐」는 [02번](../02-struct-vs-class-choosing/),\
> 「값 타입이 `object` 로 올라갈 때」는 [03번](../03-boxing-and-unboxing/)이 정본이다.\
> 여기는 **선언하는 자리의 문법**만 본다 — 「**타입을 누가 적나**」다.\
> **타입 추론 전반**(제네릭 메서드의 타입 인자 추론)은 목록의 **24번 주제**,\
> **`dynamic`** 은 이 목록에서 **뺀 주제**다(README 의 「뺀 것과 이유」) — 여기서는 **`var` 와의 대비 한 줄**만 둔다.\
> **컬렉션 식 `[1, 2, ..other]`**(C# 12)은 [목록의 **11번 주제**](../11-collection-initializers-and-collection-expressions/)다.
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

**`var` 는 「타입을 안 적는 것」이지 「타입이 없는 것」이 아니다.**\
타겟 타입 `new()` 는 그 **반대쪽**이다 — **왼쪽에 적고 오른쪽을 비운다.**

| 비유 | 실체 |
|---|---|
| **왼쪽만 적는다** | `Dictionary<string, List<int>> d = new();` — 타겟 타입 `new`(C# 9) |
| **오른쪽만 적는다** | `var d = new Dictionary<string, List<int>>();` — `var`(C# 3) |
| ★★★ **양쪽 다 안 적으면** | `var x = new();` — ★★★ **컴파일 에러**((6)) |
| ★★★ **어느 쪽을 적든 결과는 같다** | ★★★ **IL 바이트가 한 글자도 다르지 않다**((8)) |
| ★ **타입이 진짜 없는 것** | `dynamic` — **런타임에 찾는다**((7)) |
| ★★ **추론한 타입을 보고 싶으면** | ★★ **일부러 타입 에러를 낸다**((1)) |

- ★★★ **`var` 는 컴파일 타임에 타입이 정해진다.** `dynamic` 과 **완전히 다르다** —\
  `var a = 1;` 뒤에 `a = "x";` 를 쓰면 **컴파일 에러**이고, `dynamic` 은 **통과한다**((7)).
- ★★★ **추론된 타입을 찍는 법** — `GetType()` 은 **런타임 타입**이라 답이 다를 수 있다((2)).\
  **컴파일 타임 타입**을 보려면 **없는 멤버를 불러 에러 문구를 읽는다**((1)).\
  ``error CS1061: 'int' does not contain a definition for 'Nope'`` 의 **`'int'`** 가 그것이다.
- ★★ **`var` 와 타겟 타입 `new` 는 경쟁이 아니라 짝**이다 — **한쪽에 타입을 적기만 하면 된다.**\
  ★ 고르는 기준은 「**읽는 사람이 타입을 어디서 보는 게 나은가**」다((9)).

```text
   타입을 누가 적나

   var d = new Dictionary<string, List<int>>();     오른쪽에 적었다
   └─ 컴파일러가 왼쪽을 채운다

   Dictionary<string, List<int>> d = new();         왼쪽에 적었다
                                     └─ 컴파일러가 오른쪽을 채운다

   var x = new();                                   ★ 아무도 안 적었다
   └──────┴─ error CS8754: There is no target type for 'new()'

   dynamic y = new Foo();                           ★ 컴파일러가 손을 뗀다
   └─ 모든 멤버 호출이 런타임 바인딩이 된다 — IL 이 80줄로 불어난다((8))
```

```text
   ★★ 추론된 타입을 어떻게 보나 — 두 창이 다른 답을 한다

   Animal an = new Dog();
   var c = an;

   c.GetType()        → Dog       ← 런타임 타입 (그 자리에 진짜 있는 것)
   c.Nope() 의 에러   → 'Animal'  ← 컴파일 타임 타입 (var 가 추론한 것)

   ★ 둘이 갈리는 자리가 있으므로 "GetType() 으로 확인했다" 는 근거가 못 된다.
```

> **`var`** — 「초기자의 타입으로 이 지역 변수의 타입을 정하라」는 지시(C# 3.0).\
> **암묵적 타입 지정**이지 **동적 타입이 아니다.** 예: `var a = 1;` 은 `int a = 1;` 과 **같은 IL** 이다((8)).

> **타겟 타입 `new()`**(target-typed new) — 「왼쪽이 요구하는 타입으로 만들어라」(C# 9).\
> 예: `Point p = new(1, 2);` · `Take(new())` 처럼 **매개변수 타입**으로도 추론된다((5)).

> **자연 타입(natural type)** — 식 자체가 스스로 갖는 타입.\
> `() => 1` 은 C# 10부터 **`Func<int>`** 라는 자연 타입을 갖는다 — 그래서 `var` 에 담긴다((4)).

> **`dynamic`** — 「컴파일러는 손을 떼고 런타임에 멤버를 찾아라」(C# 4).\
> ★ 틀리면 **컴파일이 아니라 실행에서** 터진다((7)).

## 이 주제가 답하려는 질문

1. **`var` 는 무엇을 미루나** — **타이핑**인가 **타입 결정**인가((1)·(7)·(8)).
2. **추론된 타입을 어떻게 확인하나** — `GetType()` 으로 **왜 안 되나**((1)·(2)).
3. **어디서 막히나** — `var` 가 안 되는 자리와 `new()` 가 안 되는 자리를 **전수로** 댈 수 있나((3)·(6)).

## 동작 방식

### (0) 이 주제가 쓰는 창

| 창 | 무엇을 보여 주나 | 이 주제에서 |
|---|---|---|
| ★★★ **컴파일 진단** | ★★★ **추론된 타입 그 자체** — 이 주제의 값이 여기 몰린다 | (1)·(3)·(6)·(7) |
| **실행 출력** | `GetType()` 이 답하는 **런타임 타입** | (2)·(4)·(5) |
| **예외 전문** | `dynamic` 이 **실행에서** 터지는 것 | (7) |
| ★★ **IL** | ★★★ **세 문법이 같은 바이트를 낸다는 것** · `dynamic` 은 안 그렇다는 것 | (8) |
| **할당 바이트** | ★ 이 주제에서는 **안 썼다** — 쓸 자리가 없다 | — |

★★★ **이 주제는 「진단이 교재」인 몇 안 되는 C# 주제**다.\
박싱([03번](../03-boxing-and-unboxing/))이 **아무 말도 안 하는** 주제였다면, 여기는 **말을 너무 많이 하는** 주제다 —\
그리고 **그 말 속에 답이 들어 있다**((1)).

### (1) ★★★ `var` 가 추론한 타입을 찍는 법 — 일부러 틀린다

**언제 쓰나** — 「이거 무슨 타입이지?」 할 때. **IDE 없이, 실행 없이** 본다.

```text
===== 소스: cs04b-inferred.cs =====
var a = 1;
var b = 1.0;
var c = "x";
var d = new[] { 1, 2, 3 };
var e = (1, "x");
var f = () => 1;
var g = 1 switch { 1 => (object)"a", _ => 2 };

a.Nope();
b.Nope();
c.Nope();
d.Nope();
e.Nope();
f.Nope();
g.Nope();
===== csc -out:ex.dll cs04b-inferred.cs (cc exit=1) =====
cs04b-inferred.cs(9,3): error CS1061: 'int' does not contain a definition for 'Nope' and no accessible extension method 'Nope' accepting a first argument of type 'int' could be found (are you missing a using directive or an assembly reference?)
cs04b-inferred.cs(10,3): error CS1061: 'double' does not contain a definition for 'Nope' and no accessible extension method 'Nope' accepting a first argument of type 'double' could be found (are you missing a using directive or an assembly reference?)
cs04b-inferred.cs(11,3): error CS1061: 'string' does not contain a definition for 'Nope' and no accessible extension method 'Nope' accepting a first argument of type 'string' could be found (are you missing a using directive or an assembly reference?)
cs04b-inferred.cs(12,3): error CS1061: 'int[]' does not contain a definition for 'Nope' and no accessible extension method 'Nope' accepting a first argument of type 'int[]' could be found (are you missing a using directive or an assembly reference?)
cs04b-inferred.cs(13,3): error CS1061: '(int, string)' does not contain a definition for 'Nope' and no accessible extension method 'Nope' accepting a first argument of type '(int, string)' could be found (are you missing a using directive or an assembly reference?)
cs04b-inferred.cs(14,3): error CS1061: 'Func<int>' does not contain a definition for 'Nope' and no accessible extension method 'Nope' accepting a first argument of type 'Func<int>' could be found (are you missing a using directive or an assembly reference?)
cs04b-inferred.cs(15,3): error CS1061: 'object' does not contain a definition for 'Nope' and no accessible extension method 'Nope' accepting a first argument of type 'object' could be found (are you missing a using directive or an assembly reference?)
```

| 쓴 것 | 진단이 말한 타입 |
|---|---|
| `var a = 1;` | **`int`** |
| `var b = 1.0;` | **`double`** |
| `var c = "x";` | **`string`** |
| `var d = new[] { 1, 2, 3 };` | **`int[]`** |
| `var e = (1, "x");` | ★ **`(int, string)`** — 값 튜플 |
| `var f = () => 1;` | ★★ **`Func<int>`** — 람다의 자연 타입(C# 10) |
| `var g = 1 switch { 1 => (object)"a", _ => 2 };` | ★★★ **`object`** — 두 가지의 공통 타입 |

- ★★★ **없는 멤버(`Nope()`)를 부르면 `CS1061` 이 「무엇이 그 멤버를 안 갖고 있는지」를 말해 준다.**\
  그 **작은따옴표 안**이 곧 **컴파일러가 추론한 타입**이다. **일곱 줄이 한 번에 나온다.**
- ★★★ **이것이 `GetType()` 보다 나은 이유** — `GetType()` 은 **런타임 타입**이다((2)).\
  `var` 가 추론한 것은 **정적 타입**이고, 둘은 **갈릴 수 있다.**
- ★★ **마지막 줄이 재미있다** — `switch` 식의 두 갈래가 `string` 과 `int` 라 **공통 타입이 `object`** 가 됐다.\
  ★ 「`var` 를 쓰면 구체적인 타입이 온다」가 **항상 참은 아니다.**

### (2) ★ `GetType()` 은 다른 것을 답한다

**언제 쓰나** — 「`GetType()` 으로 확인하면 되지 않나?」 할 때.

```text
===== 소스: cs04b-var-runtime.cs =====
using System;

var a = 1;
object o = a;
Console.WriteLine($"var a = 1            : GetType()={o.GetType()}");

object boxed = "x";
var b = boxed;                       // 컴파일 타임 타입은 object
Console.WriteLine($"var b = (object)\"x\"  : GetType()={b.GetType()}");

Animal an = new Dog();
var c = an;                          // 컴파일 타임 타입은 Animal
Console.WriteLine($"var c = (Animal)Dog  : GetType()={c.GetType()}");
Console.WriteLine($"                      : Speak()={c.Speak()}");

dynamic d = 1;
Console.WriteLine($"dynamic d = 1        : GetType()={d.GetType()}");
d = "x";
Console.WriteLine($"d = \"x\" 뒤          : GetType()={d.GetType()}");

class Animal { public virtual string Speak() => "…"; }
class Dog : Animal { public override string Speak() => "멍"; public string Fetch() => "물어옴"; }
===== csc -out:ex.dll cs04b-var-runtime.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
var a = 1            : GetType()=System.Int32
var b = (object)"x"  : GetType()=System.String
var c = (Animal)Dog  : GetType()=Dog
                      : Speak()=멍
dynamic d = 1        : GetType()=System.Int32
d = "x" 뒤          : GetType()=System.String
```

| 쓴 것 | `GetType()` | `var` 가 추론한 타입 |
|---|---|---|
| `var a = 1;` | `System.Int32` | `int` — ★ **같다** |
| `var b = (object)"x";` | ★★★ **`System.String`** | ★★★ **`object`** — **갈린다**((1)의 `g`) |
| `var c = (Animal)new Dog();` | ★★★ **`Dog`** | ★★★ **`Animal`** — **갈린다** |
| `dynamic d = 1;` → `d = "x";` | `System.Int32` → `System.String` | ★ **타입이 없다** |

- ★★★ **`var c = an;`(선언 타입이 `Animal`)의 `GetType()` 이 `Dog` 를 답한다.**\
  그런데 `c.Fetch()`(`Dog` 에만 있는 메서드)는 **컴파일이 안 된다** — `var` 가 본 것은 **`Animal`** 이기 때문이다.\
  ★★ **「`GetType()` 으로 확인했다」가 근거가 못 되는 이유**가 이것이다.
- ★ `c.Speak()` 가 **`멍`** 을 답하는 것은 **가상 디스패치**다 — 정적 타입은 `Animal` 이지만 호출은 실제 객체로 간다.\
  ★ 「**어느 멤버를 부를 수 있나**」는 정적 타입이, 「**어느 구현이 뽑히나**」는 런타임 타입이 정한다.
- ★★ **`dynamic` 은 둘 다 아니다** — 같은 변수가 `Int32` 였다가 `String` 이 된다((7)).

### (3) ★★ `var` 가 안 되는 자리 — 전수로 던졌다

**언제 쓰나** — 「여기 `var` 쓰면 안 되나?」 할 때.

선언 자리부터.

```text
===== 소스: cs04b-var-decl.cs =====
class Holder {
    var field = 1;                      // ① 필드
}

class Program {
    static var Method() => 1;           // ② 반환 타입
    static void Param(var x) { }        // ③ 매개변수
    static void Main() { }
}
===== csc -out:ex.dll cs04b-var-decl.cs (cc exit=1) =====
cs04b-var-decl.cs(6,12): error CS0825: The contextual keyword 'var' may only appear within a local variable declaration or in script code
cs04b-var-decl.cs(2,5): error CS0825: The contextual keyword 'var' may only appear within a local variable declaration or in script code
cs04b-var-decl.cs(7,23): error CS0825: The contextual keyword 'var' may only appear within a local variable declaration or in script code
```

- ★★ **`var` 는 「지역 변수 선언」에만** 쓴다 — ``may only appear within a local variable declaration or in script code``.\
  필드·반환 타입·매개변수는 **전부 `CS0825`** 다. ★ **에러 문구가 하나**라 외우기 쉽다.

지역 변수 자리 안에서도 여덟 군데가 막힌다.

```text
===== 소스: cs04b-var-local.cs =====
using System;

class Program {
    static void Main() {
        var a;                          // ① 초기자가 없다
        var b = null;                   // ② null 로 초기화
        var c = default;                // ③ default 리터럴
        var d = 1, e = "x";             // ④ 한 선언에 타입이 둘
        var f = (x) => x;               // ⑤ 매개변수 타입을 모르는 람다
        var g = int.Parse;              // ⑥ 오버로드가 여럿인 메서드 그룹
        var[] h = { 1, 2 };             // ⑦ var 의 배열
        var i = new();                  // ⑧ var 와 타겟 타입 new
        Console.WriteLine($"{a}{b}{c}{d}{e}{f}{g}{h}{i}");
    }
}
===== csc -out:ex.dll cs04b-var-local.cs (cc exit=1) =====
cs04b-var-local.cs(5,13): error CS0818: Implicitly-typed variables must be initialized
cs04b-var-local.cs(6,13): error CS0815: Cannot assign <null> to an implicitly-typed variable
cs04b-var-local.cs(7,17): error CS8716: There is no target type for the default literal.
cs04b-var-local.cs(8,9): error CS0819: Implicitly-typed variables cannot have multiple declarators
cs04b-var-local.cs(9,17): error CS8917: The delegate type could not be inferred.
cs04b-var-local.cs(10,17): error CS8917: The delegate type could not be inferred.
cs04b-var-local.cs(11,9): error CS0825: The contextual keyword 'var' may only appear within a local variable declaration or in script code
cs04b-var-local.cs(12,17): error CS8754: There is no target type for 'new()'
```

| 쓴 것 | 진단 | 왜 |
|---|---|---|
| `var a;` | ``CS0818: Implicitly-typed variables must be initialized`` | ★ 추론할 근거가 없다 |
| `var b = null;` | ``CS0815: Cannot assign <null> to an implicitly-typed variable`` | `null` 에는 타입이 없다 |
| `var c = default;` | ``CS8716: There is no target type for the default literal.`` | ★ `default` 도 **타겟이 필요**하다 |
| `var d = 1, e = "x";` | ``CS0819: Implicitly-typed variables cannot have multiple declarators`` | ★ 한 선언에 타입이 둘일 수 없다 |
| `var f = (x) => x;` | ``CS8917: The delegate type could not be inferred.`` | 매개변수 타입을 모른다 |
| `var g = int.Parse;` | ``CS8917`` | ★★ **오버로드가 여럿**이라 못 고른다 |
| `var[] h = { 1, 2 };` | ``CS0825`` | `var` 의 배열이라는 건 없다 |
| `var i = new();` | ``CS8754: There is no target type for 'new()'`` | ★★★ **양쪽 다 안 적었다**((6)) |

- ★★★ **여덟 줄이 한 번에 나온다** — Roslyn 이 여기서는 첫 에러에서 멈추지 않았다.\
  ★ 앞의 선언 자리 블록은 **셋만** 나왔다(선언이 깨지면 본문 바인딩을 멈춘다).\
  **「에러가 몇 개 나오나」는 컴파일러가 어디서 포기하느냐에 달린 것**이지 **문제의 개수가 아니다.**
- ★★ **`var b = null;` 과 `var c = default;` 가 다른 진단**을 받는다 —\
  `null` 은 **「타입 없는 리터럴」**, `default` 는 「**타겟이 필요한 식**」이다.\
  ★ `object b = null;` 과 `int c = default;` 는 **둘 다 된다** — 왼쪽이 있으면 되는 것이다.
- ★★ **`var g = int.Parse;` 가 막히는 이유는** 「메서드 그룹이라서」가 아니라 「**오버로드가 여럿이라서**」다.\
  (4)에서 **오버로드가 하나뿐인 메서드 그룹은 통과한다.**

### (4) `var` 가 되는 자리 — C# 10 이 넓혔다

**언제 쓰나** — 「람다는 `var` 에 못 담지?」 할 때. **판이 바뀐 자리**다.

```text
===== 소스: cs04b-var-ok.cs =====
using System;
using System.Collections.Generic;

var f = () => 1;                        // C# 10 — 람다의 자연 타입
var g = (int x) => x + 1;               // 매개변수 타입을 적은 람다
var h = Console.ReadLine;               // 오버로드가 하나뿐인 메서드 그룹
var i = new List<int> { 1, 2 };
var j = new { Won = 100, Cur = "KRW" }; // 익명 타입 — var 말고는 적을 수가 없다

Console.WriteLine($"var f = () => 1        : {f.GetType()}  → {f()}");
Console.WriteLine($"var g = (int x)=>x+1   : {g.GetType()}  → {g(1)}");
Console.WriteLine($"var h = Console.ReadLine: {h.GetType()}");
Console.WriteLine($"var i = new List<int>  : {i.GetType()}  → {i.Count}개");
Console.WriteLine($"var j = new {{ ... }}    : {j.GetType()}  → {j}");
===== csc -out:ex.dll cs04b-var-ok.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
var f = () => 1        : System.Func`1[System.Int32]  → 1
var g = (int x)=>x+1   : System.Func`2[System.Int32,System.Int32]  → 2
var h = Console.ReadLine: System.Func`1[System.String]
var i = new List<int>  : System.Collections.Generic.List`1[System.Int32]  → 2개
var j = new { ... }    : <>f__AnonymousType0`2[System.Int32,System.String]  → { Won = 100, Cur = KRW }
```

| 쓴 것 | 추론된 타입 |
|---|---|
| `var f = () => 1;` | ★★ ``System.Func`1[System.Int32]`` — **C# 10부터** |
| `var g = (int x) => x + 1;` | ``System.Func`2[System.Int32,System.Int32]`` |
| `var h = Console.ReadLine;` | ★★ ``System.Func`1[System.String]`` — **오버로드가 하나뿐**이라 된다 |
| `var i = new List<int> { 1, 2 };` | ``System.Collections.Generic.List`1[System.Int32]`` |
| `var j = new { Won = 100, Cur = "KRW" };` | ★★★ **``<>f__AnonymousType0`2``** — **`var` 말고는 적을 수가 없다** |

- ★★★ **「`var f = () => 1;` 이 안 된다」는 C# 9 까지의 이야기**다.\
  C# 10부터 **람다와 메서드 그룹에 자연 타입**이 생겨 `var` 에 담긴다.
- ★★★ **익명 타입은 `var` 가 아니면 적을 방법이 없다** — 이름이 ``<>f__AnonymousType0`2`` 라\
  **소스에 쓸 수 있는 식별자가 아니다.** ★ `var` 가 **선택이 아니라 필수**인 유일한 자리다.
- ★ **`Console.ReadLine` 은 되고 `int.Parse` 는 안 되는 것**((3))이 짝을 이룬다 — **오버로드 개수**가 가른다.

### (5) 타겟 타입 `new()` — 왼쪽에 적고 오른쪽을 비운다

**언제 쓰나** — 제네릭 타입 이름이 길 때. **C# 9부터.**

```text
===== 소스: cs04b-target-new.cs =====
using System;
using System.Collections.Generic;

Dictionary<string, List<int>> d = new();          // C# 9 — 타겟 타입 new
List<int> l = new(capacity: 4) { 1, 2 };
Point p = new(1, 2);
Point q = new();

Console.WriteLine($"Dictionary<string, List<int>> d = new() : {d.GetType()}  Count={d.Count}");
Console.WriteLine($"List<int> l = new(4) {{1,2}}             : Count={l.Count} Capacity={l.Capacity}");
Console.WriteLine($"Point p = new(1, 2)                    : {p}");
Console.WriteLine($"Point q = new()                        : {q}");

Console.WriteLine($"Take(new()) — 매개변수 기본형으로 추론    : {Take(new())}");
Console.WriteLine($"Make() 반환 자리                        : {Make()}");

static string Take(Point pt) => pt.ToString();
static Point Make() => new(9, 9);

readonly record struct Point(int X, int Y);
===== csc -out:ex.dll cs04b-target-new.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
Dictionary<string, List<int>> d = new() : System.Collections.Generic.Dictionary`2[System.String,System.Collections.Generic.List`1[System.Int32]]  Count=0
List<int> l = new(4) {1,2}             : Count=2 Capacity=4
Point p = new(1, 2)                    : Point { X = 1, Y = 2 }
Point q = new()                        : Point { X = 0, Y = 0 }
Take(new()) — 매개변수 기본형으로 추론    : Point { X = 0, Y = 0 }
Make() 반환 자리                        : Point { X = 9, Y = 9 }
```

| 쓴 것 | 되는가 | 왜 |
|---|---|---|
| `Dictionary<string, List<int>> d = new();` | ✔ | 변수의 선언 타입이 타겟이다 |
| `List<int> l = new(capacity: 4) { 1, 2 };` | ✔ | ★ **인자와 초기자도 같이** 쓴다 |
| `Point p = new(1, 2);` | ✔ | 생성자 인자도 된다 |
| `Take(new())` | ★★ ✔ | ★★ **매개변수 타입**이 타겟이 된다 |
| `static Point Make() => new(9, 9);` | ★★ ✔ | ★★ **반환 타입**이 타겟이 된다 |

- ★★★ **타겟은 「변수의 선언 타입」만이 아니다** — **매개변수**·**반환 타입**·필드 타입·`return` 자리 전부다.\
  ★ 「왼쪽에 타입이 있으면」이 아니라 「**문맥이 타입을 요구하면**」이 정확한 문장이다.
- ★★ `Take(new())` 는 **읽기 어려운 쪽**으로 기운다 — 호출부만 봐서는 무엇이 만들어지는지 모른다.\
  ★ 이 문법을 **어디까지 쓸지**는 (9)의 판단이다.

### (6) ★ 둘이 충돌하는 자리 — `var x = new()`

**언제 쓰나** — 「둘 다 쓰면 더 짧지 않나?」 할 때.

```text
===== 소스: cs04b-var-new.cs =====
class Program {
    static void Main() {
        var x = new();                  // var 와 타겟 타입 new 를 같이
        System.Console.WriteLine(x);
    }
}
===== csc -out:ex.dll cs04b-var-new.cs (cc exit=1) =====
cs04b-var-new.cs(3,17): error CS8754: There is no target type for 'new()'
```

- ★★★ ``error CS8754: There is no target type for 'new()'`` —\
  **`var` 는 오른쪽에서 타입을 얻고 `new()` 는 왼쪽에서 얻는데, 둘 다 비면 아무 데도 없다.**
- ★ **한쪽에 타입을 적기만 하면 된다** — `var x = new Foo();` 또는 `Foo x = new();`.\
  ★★ 이것이 「`var` 와 타겟 타입 `new` 는 경쟁이 아니라 짝」이라는 말의 뜻이다.

### (7) ★★ `dynamic` 과의 차이 — 컴파일이냐 실행이냐

**언제 쓰나** — 「`var` 는 동적 타입 아닌가?」 할 때. **이 절이 그 오해를 끝낸다.**

```text
===== 소스: cs04b-dynamic.cs =====
class Program {
    static void Main() {
        var a = 1;
        a.Nope();                       // var — 컴파일 타임에 막힌다

        dynamic b = 1;
        b.Nope();                       // dynamic — 컴파일은 통과한다

        var c = 1;
        c = "x";                        // var — 타입이 고정돼 있다

        dynamic d = 1;
        d = "x";                        // dynamic — 된다
        System.Console.WriteLine($"{a}{b}{c}{d}");
    }
}
===== csc -out:ex.dll cs04b-dynamic.cs (cc exit=1) =====
cs04b-dynamic.cs(4,11): error CS1061: 'int' does not contain a definition for 'Nope' and no accessible extension method 'Nope' accepting a first argument of type 'int' could be found (are you missing a using directive or an assembly reference?)
cs04b-dynamic.cs(10,13): error CS0029: Cannot implicitly convert type 'string' to 'int'
```

| 쓴 것 | `var` | `dynamic` |
|---|---|---|
| 없는 멤버 호출 | ★★★ **`error CS1061`**(컴파일) | ★★★ **컴파일 통과** |
| 다른 타입 재대입 | ★★★ **`error CS0029`**(컴파일) | ★★★ **통과** |

- ★★★ **에러가 둘 다 `var` 쪽에서만 났다.** `dynamic` 의 두 줄은 **아무 말도 안 듣는다.**\
  `var` 는 **타입을 안 적는 것**이고, `dynamic` 은 **타입 검사를 끄는 것**이다.
- 그러면 `dynamic` 의 틀림은 언제 드러나는가.

```text
===== 소스: cs04b-dynamic-run.cs =====
dynamic b = 1;
b.Nope();
===== csc -out:ex.dll cs04b-dynamic-run.cs && dotnet ex.dll (cc exit=0 · run exit=134) =====
Unhandled exception. Microsoft.CSharp.RuntimeBinder.RuntimeBinderException: 'int' does not contain a definition for 'Nope'
   at CallSite.Target(Closure, CallSite, Object)
   at System.Dynamic.UpdateDelegates.UpdateAndExecuteVoid1[T0](CallSite site, T0 arg0)
   at Program.<Main>$(String[] args)
```

- ★★★ **실행에서 터진다** — ``Microsoft.CSharp.RuntimeBinder.RuntimeBinderException: 'int' does not contain a definition for 'Nope'``.\
  ★★ **메시지 본문이 `CS1061` 과 거의 같다** — 같은 판단을 **언제 하느냐**만 다르다.
- ★ 트레이스에 ``at CallSite.Target(Closure, CallSite, Object)`` 가 보인다 —\
  **호출 사이트(call site)라는 기계**가 런타임에 메서드를 찾는다. 그 기계가 IL 에 그대로 찍힌다((8)).

### (8) ★★ IL — 세 문법이 **한 바이트도 다르지 않다**

**언제 쓰나** — 「`var` 를 쓰면 뭔가 달라지나?」 할 때. **이 절이 그 질문을 끝낸다.**

```text
===== 소스: cs04b-il.cs =====
using System;
using System.Reflection;

Il.Dump(typeof(Probe), "WithVar");
Il.Dump(typeof(Probe), "WithExplicit");
Il.Dump(typeof(Probe), "WithTargetNew");

byte[] Body(string n) =>
    typeof(Probe).GetMethod(n, BindingFlags.Public | BindingFlags.Static)!
                 .GetMethodBody()!.GetILAsByteArray()!;

System.Console.WriteLine($"--- IL 바이트 대조 ---");
System.Console.WriteLine($"WithVar == WithExplicit  : {Body("WithVar").AsSpan().SequenceEqual(Body("WithExplicit"))}");
System.Console.WriteLine($"WithVar == WithTargetNew : {Body("WithVar").AsSpan().SequenceEqual(Body("WithTargetNew"))}");

static class Probe {
    public static int WithVar() { var s = new System.Text.StringBuilder(); s.Append('a'); return s.Length; }
    public static int WithExplicit() { System.Text.StringBuilder s = new System.Text.StringBuilder(); s.Append('a'); return s.Length; }
    public static int WithTargetNew() { System.Text.StringBuilder s = new(); s.Append('a'); return s.Length; }
}
===== csc -r:il.dll -out:ex.dll cs04b-il.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
--- Probe.WithVar ---
  .locals [0] System.Text.StringBuilder
  .locals [1] System.Int32
  IL_0000: nop
  IL_0001: newobj System.Text.StringBuilder::.ctor
  IL_0006: stloc.0
  IL_0007: ldloc.0
  IL_0008: ldc.i4.s 97
  IL_000a: callvirt System.Text.StringBuilder::Append
  IL_000f: pop
  IL_0010: ldloc.0
  IL_0011: callvirt System.Text.StringBuilder::get_Length
  IL_0016: stloc.1
  IL_0017: br.s IL_0019
  IL_0019: ldloc.1
  IL_001a: ret
--- Probe.WithExplicit ---
  .locals [0] System.Text.StringBuilder
  .locals [1] System.Int32
  IL_0000: nop
  IL_0001: newobj System.Text.StringBuilder::.ctor
  IL_0006: stloc.0
  IL_0007: ldloc.0
  IL_0008: ldc.i4.s 97
  IL_000a: callvirt System.Text.StringBuilder::Append
  IL_000f: pop
  IL_0010: ldloc.0
  IL_0011: callvirt System.Text.StringBuilder::get_Length
  IL_0016: stloc.1
  IL_0017: br.s IL_0019
  IL_0019: ldloc.1
  IL_001a: ret
--- Probe.WithTargetNew ---
  .locals [0] System.Text.StringBuilder
  .locals [1] System.Int32
  IL_0000: nop
  IL_0001: newobj System.Text.StringBuilder::.ctor
  IL_0006: stloc.0
  IL_0007: ldloc.0
  IL_0008: ldc.i4.s 97
  IL_000a: callvirt System.Text.StringBuilder::Append
  IL_000f: pop
  IL_0010: ldloc.0
  IL_0011: callvirt System.Text.StringBuilder::get_Length
  IL_0016: stloc.1
  IL_0017: br.s IL_0019
  IL_0019: ldloc.1
  IL_001a: ret
--- IL 바이트 대조 ---
WithVar == WithExplicit  : True
WithVar == WithTargetNew : True
```

- ★★★ **`WithVar` · `WithExplicit` · `WithTargetNew` 의 IL 바이트가 `SequenceEqual` 로 `True`** 다.\
  눈으로 비교한 게 아니라 **프로그램이 바이트 배열을 직접 대조**했다.
- ★★★ **그러니 `var` 는 성능·의미와 아무 상관이 없다.** 남는 판단은 **가독성뿐**이다((9)).
- ★★ `dynamic` 은 **전혀 다르다.**

```text
===== 소스: cs04b-il-dynamic.cs =====
Il.Dump(typeof(Probe), "WithDynamic");

static class Probe {
    public static int WithDynamic() { dynamic s = new System.Text.StringBuilder(); s.Append('a'); return (int)s.Length; }
}
===== csc -r:il.dll -out:ex.dll cs04b-il-dynamic.cs && dotnet ex.dll | wc -l (cc exit=0 · run exit=0) =====
80
```

```text
===== 소스: cs04b-il-dynamic.cs =====
Il.Dump(typeof(Probe), "WithDynamic");

static class Probe {
    public static int WithDynamic() { dynamic s = new System.Text.StringBuilder(); s.Append('a'); return (int)s.Length; }
}
===== csc -r:il.dll -out:ex.dll cs04b-il-dynamic.cs && dotnet ex.dll | head -20 (cc exit=0 · run exit=0) =====
--- Probe.WithDynamic ---
  .locals [0] System.Object
  .locals [1] System.Int32
  IL_0000: nop
  IL_0001: newobj System.Text.StringBuilder::.ctor
  IL_0006: stloc.0
  IL_0007: ldsfld Probe+<>o__0::<>p__0
  IL_000c: brfalse.s IL_0010
  IL_000e: br.s IL_004e
  IL_0010: ldc.i4 256
  IL_0015: ldstr "Append"
  IL_001a: ldnull
  IL_001b: ldtoken Probe
  IL_0020: call System.Type::GetTypeFromHandle
  IL_0025: ldc.i4.2
  IL_0026: newarr Microsoft.CSharp.RuntimeBinder.CSharpArgumentInfo
  IL_002b: dup
  IL_002c: ldc.i4.0
  IL_002d: ldc.i4.0
  IL_002e: ldnull
```

- ★★★ **같은 일을 하는 메서드가 IL 로 80줄**이다(위 셋은 16\~17줄이었다).\
  `Microsoft.CSharp.RuntimeBinder.Binder::InvokeMember` · `CSharpArgumentInfo` · `CallSite` 를 만들어 **캐시하는 기계**가 통째로 들어간다.
- ★★ **그 기계가 「런타임 바인딩」의 실체**다 — `dynamic` 이 공짜가 아닌 이유이고,\
  ★ **다만 이 문서는 그 비용을 시간으로 재지 않았다.** 잰 것은 **IL 줄 수**뿐이다.

### (9) 무엇을 쓸지 손으로 돌리는 순서

1. **익명 타입인가?** — **`var` 말고는 방법이 없다**((4)).
2. **오른쪽에 타입 이름이 이미 보이나?**(`new Dictionary<…>()`·캐스트) — **`var`** 가 중복을 지운다.
3. **왼쪽 타입이 길고 오른쪽이 `new` 뿐인가?** — **타겟 타입 `new()`**((5)).
4. **오른쪽이 메서드 호출이라 타입이 안 보이나?**(`var x = Parse(s);`) — **명시 타입**을 적는다.
5. **`Take(new())` 처럼 문맥이 멀어지나?** — ★ **적는 쪽이 낫다.**
6. **런타임에 멤버를 찾아야 하나?** — 그때만 `dynamic` 이고, **거의 없다.**

★ **판단 기준은 하나다 — 「읽는 사람이 이 줄만 보고 타입을 아는가」.**\
★★ **IL 이 같으므로 성능은 기준이 아니다**((8)).

## 문법 — 형태와 규칙

### 형태

```csharp
// cs04b-target-new.cs
using System;
using System.Collections.Generic;

Dictionary<string, List<int>> d = new();          // C# 9 — 타겟 타입 new
List<int> l = new(capacity: 4) { 1, 2 };
Point p = new(1, 2);
Point q = new();

Console.WriteLine($"Dictionary<string, List<int>> d = new() : {d.GetType()}  Count={d.Count}");
Console.WriteLine($"List<int> l = new(4) {{1,2}}             : Count={l.Count} Capacity={l.Capacity}");
Console.WriteLine($"Point p = new(1, 2)                    : {p}");
Console.WriteLine($"Point q = new()                        : {q}");

Console.WriteLine($"Take(new()) — 매개변수 기본형으로 추론    : {Take(new())}");
Console.WriteLine($"Make() 반환 자리                        : {Make()}");

static string Take(Point pt) => pt.ToString();
static Point Make() => new(9, 9);

readonly record struct Point(int X, int Y);
```

규칙 불릿.

- **`var` 는 지역 변수 선언에만 쓴다**((3)). 필드·반환 타입·매개변수는 `CS0825` 다.
- **`var` 는 초기자가 있어야 하고, 한 선언에 하나만** 쓴다((3)).
- **`null`·`default` 는 `var` 에 못 담는다**((3)) — 타입이 없거나 타겟이 필요하다.
- ★ **람다·메서드 그룹은 C# 10부터 `var` 에 담긴다**((4)) — 단 **오버로드가 여럿이면** `CS8917` 이다.
- **익명 타입은 `var` 로만 받을 수 있다**((4)).
- **타겟 타입 `new()` 는 문맥이 타입을 요구하는 자리 전부에서** 된다((5)) — 변수·매개변수·반환·필드.
- ★★★ **`var x = new();` 는 안 된다**((6)) — 양쪽 다 타입이 없다.
- ★★★ **`var` 는 정적 타입이다**((7)·(8)) — `dynamic` 과 다르고, IL 이 명시 타입과 **같다.**

### 금지 사례 — 던져서 받은 열하나

| 쓴 것 | 진단 |
|---|---|
| `var field = 1;`(필드) | ``error CS0825: The contextual keyword 'var' may only appear within a local variable declaration or in script code`` |
| `static var Method() => 1;` | ``error CS0825`` |
| `static void Param(var x) { }` | ``error CS0825`` |
| `var[] h = { 1, 2 };` | ``error CS0825`` |
| `var a;` | ``error CS0818: Implicitly-typed variables must be initialized`` |
| `var b = null;` | ``error CS0815: Cannot assign <null> to an implicitly-typed variable`` |
| `var c = default;` | ``error CS8716: There is no target type for the default literal.`` |
| `var d = 1, e = "x";` | ``error CS0819: Implicitly-typed variables cannot have multiple declarators`` |
| `var f = (x) => x;` | ``error CS8917: The delegate type could not be inferred.`` |
| `var g = int.Parse;` | ``error CS8917`` |
| `var i = new();` | ``error CS8754: There is no target type for 'new()'`` |

### 추론된 타입을 보는 두 가지 방법

| 방법 | 무엇을 답하나 | 언제 틀리나 |
|---|---|---|
| ★★★ **없는 멤버를 불러 `CS1061` 을 읽는다** | ★★★ **컴파일 타임 타입** | — |
| `GetType()` | **런타임 타입** | ★★ 선언 타입과 실제 객체가 다를 때((2)) |

## 어디서 틀리나

### 1. ★★★ 「`var` 는 동적 타입이다」

**아니다**((7)·(8)). `var a = 1;` 뒤에 `a = "x";` 는 **`error CS0029`** 다.\
★ IL 이 명시 타입과 **한 바이트도 다르지 않다.**

### 2. ★★★ 「`GetType()` 으로 `var` 가 추론한 타입을 확인한다」

**다른 것을 답한다**((2)). `var c = (Animal)new Dog();` 의 `GetType()` 은 **`Dog`** 인데\
`var` 가 추론한 것은 **`Animal`** 이다. ★ **컴파일 타임 타입은 일부러 낸 타입 에러로 본다**((1)).

### 3. ★★ 「`var` 를 쓰면 구체적인 타입이 온다」

**공통 타입이 올 수도 있다**((1)의 마지막 줄) — `switch` 식의 두 갈래가 `string` 과 `int` 면 **`object`** 다.

### 4. ★★ 「람다는 `var` 에 못 담는다」

**C# 10부터 담긴다**((4)). ★ 단 **매개변수 타입을 안 적으면** `CS8917` 이고,\
**오버로드가 여럿인 메서드 그룹**도 `CS8917` 이다.

### 5. ★★ 「`var x = new();` 가 제일 짧다」

**컴파일 에러다**((6)) — ``CS8754``. **한쪽에는 타입을 적어야 한다.**

### 6. ★★ 「타겟 타입 `new()` 는 변수 선언에서만 된다」

**매개변수·반환 타입에서도 된다**((5)). ★ 그래서 `Take(new())` 같은 **읽기 어려운 코드**도 컴파일된다.

### 7. ★ 「`var b = null;` 은 `object` 로 추론되겠지」

**`CS0815` 다**((3)). `null` 에는 타입이 없다. ★ `object b = null;` 은 된다 — **왼쪽이 있으면 되는 것**이다.

### 8. ★ 「`var` 는 성능에 영향이 있다」

**없다**((8)). IL 바이트가 **`SequenceEqual` 로 `True`** 다.

### 9. ★ 「`dynamic` 도 어차피 런타임에 같은 일 한다」

**IL 이 80줄 대 16줄**이다((8)). 호출 사이트를 만들어 캐시하는 기계가 통째로 들어간다.\
★ **다만 이 문서는 시간을 재지 않았다** — 잰 것은 **줄 수**뿐이다.

### 10. 「Java 의 `var` 와 같다」

**거의 같다** — Java 10의 `var` 도 지역 변수 전용이고 정적 타입이다.\
★★ **다른 칸은 타겟 타입 `new()` 가 Java 에 없다는 것**이고,\
★ Java 의 `var` 는 **람다·메서드 참조를 못 담는다**(C# 10은 담는다((4))).

## 구현 세부사항 대 언어 보장

| 사실 | 누가 보장하나 |
|---|---|
| **`var` 가 지역 변수 선언에만 쓰이는** 것 · **초기자가 필요한** 것 | **언어**(ECMA-334) |
| **`var` 가 정적 타입이고 `dynamic` 과 다른** 것 | **언어** |
| **`null`·`default` 를 `var` 에 못 담는** 것 | **언어** |
| **타겟 타입 `new()` 가 문맥이 타입을 요구하는 자리에서 되는** 것 | **언어**(C# 9 기능 명세) |
| **람다·메서드 그룹의 자연 타입** | **언어**(C# 10 기능 명세) |
| **익명 타입을 `var` 로만 받을 수 있는** 것 | **언어** |
| ★★★ **`var` 와 명시 타입의 IL 이 같은** 것 | ★★★ **관찰**이다. 「의미가 같다」는 **언어 보장**이고, **바이트가 같은 것은 Roslyn 의 결과**다 |
| ★ **익명 타입의 이름이 ``<>f__AnonymousType0`2`` 인** 것 | ★ **컴파일러 구현**이다. 이름 규칙은 명세에 없다 |
| ★★ **`dynamic` 의 IL 이 80줄인** 것 | ★★ **Roslyn + `Microsoft.CSharp` 의 구현**이다. 「런타임 바인딩이다」가 보장이고 **줄 수가 보장이 아니다** |
| ★ **에러가 한 번에 몇 개 나오는가**((3)의 3개 대 8개) | ★ **컴파일러가 어디서 포기하느냐**에 달렸다 — **문제의 개수가 아니다** |
| 진단 문구 · 진단 코드 | **컴파일러 구현**(Roslyn) |

## 언제 쓰고 언제 안 쓰나

**`var` 를 쓰는 자리**\
① **익명 타입**(필수)((4)) ② **오른쪽에 타입 이름이 이미 보일 때**(`new`·캐스트·`as`)\
③ **`foreach` 변수**처럼 타입이 뻔할 때.

**명시 타입을 적는 자리**\
① **오른쪽이 메서드 호출**이라 타입이 안 보일 때 ② **인터페이스로 받고 싶을 때**(`IList<int> l = new List<int>();`)\
③ **`var` 가 예상 밖 타입을 추론할 때**((1)의 `object`).

**타겟 타입 `new()` 를 쓰는 자리**\
① **왼쪽 타입이 길고 오른쪽이 `new` 뿐일 때** ② **필드 선언**(타입을 한 번만 적는다).\
★ **매개변수 자리(`Take(new())`)는 피하는 쪽**이 읽기 좋다((5)).

**`dynamic` 은 거의 안 쓴다** — README 의 「뺀 것과 이유」에도 그렇게 적혀 있다.\
★ 쓰는 자리는 COM 상호운용·`ExpandoObject` 정도다.

## 핵심 문장

1. **`var` 는 타입을 안 적는 것이지 타입이 없는 것이 아니다** — IL 이 명시 타입과 같다.
2. **추론된 타입은 일부러 낸 타입 에러로 본다** — `GetType()` 은 **런타임 타입**이라 갈릴 수 있다.
3. **`var` 가 안 되는 자리는 열하나였다** — 선언 자리 넷, 지역 변수 안에서 일곱.
4. **`var` 와 타겟 타입 `new()` 는 짝이다** — 한쪽에만 적으면 되고, **둘 다 비면 `CS8754`** 다.
5. **람다·메서드 그룹은 C# 10부터 `var` 에 담긴다** — 단 오버로드가 여럿이면 못 고른다.
6. **`dynamic` 은 검사를 끄는 것이다** — 같은 판단을 **실행 시점**에 하고, IL 이 80줄이 된다.

## 관련 자료

- [01번 — 값 타입과 참조 타입](../01-value-types-and-reference-types/) — `var s2 = s1;` 이 **`Point`** 로 추론되는 것.\
  ★ **무엇이 복사되는지**는 거기가 정본이다.
- [02번 — `struct` 대 `class` 고르기](../02-struct-vs-class-choosing/) — `Point p = new(1, 2);` 로 `readonly record struct` 를 만드는 자리.
- [03번 — 박싱과 언박싱](../03-boxing-and-unboxing/) — ★★ (1)의 마지막 줄(`object` 로 추론)이 거기서 **박싱**으로 이어진다.\
  **`var` 가 `object` 를 추론하면 그 자리에서 값 타입이 박싱된다.**
- 목록의 **24번 주제**(제네릭) — **제네릭 메서드의 타입 인자 추론**은 거기다.\
  **여기는 지역 변수 선언까지, 거기는 타입 인자부터.**
- [목록의 **11번 주제**](../11-collection-initializers-and-collection-expressions/)(컬렉션 초기화와 컬렉션 식) — `[1, 2, ..other]`(C# 12)가 **타겟 타입이 필요한 또 하나의 식**이다.
- 목록의 **23번 주제**(튜플과 해체) — (1)의 `(int, string)` 이 거기서 본론이 된다.
- 목록의 **28번 주제**(람다식과 클로저) — (4)의 자연 타입이 거기서 본론이 된다.
- 목록의 **52번 주제**(최상위 문과 진입점) — 이 문서의 모든 예제가 최상위 문이고,\
  ★ **예외 트레이스의 ``Program.<Main>$(String[] args)``** 가 그것이 만든 이름이다.

## 용어 풀이

> **`var`** — 「초기자의 타입으로 이 지역 변수의 타입을 정하라」(C# 3.0). **정적 타입**이다.

> **타겟 타입 `new()`** — 「문맥이 요구하는 타입으로 만들어라」(C# 9).\
> 예: `Point p = new(1, 2);` · `Take(new())` · `static Point Make() => new(9, 9);`

> **자연 타입(natural type)** — 식이 스스로 갖는 타입.\
> `() => 1` 은 C# 10부터 `Func<int>` 라는 자연 타입을 갖는다((4)).

> **익명 타입(anonymous type)** — `new { Won = 100 }` 이 만드는 이름 없는 타입.\
> 컴파일러가 ``<>f__AnonymousType0`2`` 같은 이름을 붙이는데 **소스에 쓸 수 없는 이름**이라 `var` 가 필수다.

> **`dynamic`** — 컴파일 타임 검사를 끄고 **런타임에 멤버를 찾는 것**(C# 4).\
> 틀리면 `RuntimeBinderException` 이다((7)).

> **호출 사이트(call site)** — `dynamic` 호출 하나마다 만들어지는 **바인딩 캐시**.\
> IL 에 `CallSite` · `CSharpArgumentInfo` · `Binder::InvokeMember` 로 찍힌다((8)).

> **컴파일 타임 타입 대 런타임 타입** — 앞엣것은 **어느 멤버를 부를 수 있나**를,\
> 뒤엣것은 **어느 구현이 뽑히나**를 정한다((2)).

## 더 들어가면

- **제네릭 메서드의 타입 인자 추론** — `Max(1, 2)` 가 `Max<int>` 로 푸는 것. ★ 안 던졌다(목록의 **24번 주제**).
- **`var` 패턴**(`is var x`) — 패턴 매칭의 `var` 는 **여기 `var` 와 다른 문법**이다. ★ 안 던졌다(목록의 **21번 주제**).
- **`ref var`·`scoped var`** — `ref` 지역과 함께 쓰는 형태. ★ 안 던졌다(목록의 **45번 주제**).
- **컬렉션 식 `[1, 2]`**(C# 12) — `new()` 와 같은 「타겟이 필요한 식」 집안. ★ 안 던졌다([목록의 **11번 주제**](../11-collection-initializers-and-collection-expressions/)).
- **`dynamic` 의 실제 비용** — ★ **못 쟀다.** (8)이 잰 것은 **IL 줄 수**이고 **시간이 아니다.**\
  호출 사이트는 **첫 호출에만** 만들어지고 그 뒤는 캐시를 타므로, **시간을 재려면 반복 호출 하네스**가 필요하다.
- **C# 9 이하에서 `var f = () => 1;`** — ★ **못 던졌다.** 이 머신에는 .NET 10 만 있다.
