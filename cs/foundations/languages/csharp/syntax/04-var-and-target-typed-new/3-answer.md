# csharp/syntax/04 — 변수 선언·`var`·타겟 타입 `new` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> **기준 소스** — [ECMA-334 7판(2023-12)](https://ecma-international.org/publications-and-standards/standards/ecma-334/) · [Microsoft Learn — C# 언어 레퍼런스](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/) · [Learn — 값 형식](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/builtin-types/value-types) · [Learn — 참조 형식](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/keywords/reference-types) · [.NET API — `GC.GetAllocatedBytesForCurrentThread`](https://learn.microsoft.com/en-us/dotnet/api/system.gc.getallocatedbytesforcurrentthread)
> **실행 검증** — 이 문서의 모든 출력·진단·IL·할당 바이트는 **.NET SDK 10.0.401** ·\
> 런타임 **`.NET 10.0.12`**(`Microsoft.NETCore.App`) · 타겟 **`net10.0`** · **linux-x64** 에서 실제로 돌려 얻은 것이다(2026-09-24).\
> ★ 블록은 캡처 스크립트가 파일로 받아 조립기가 끼워 넣은 것이다 — 사람이 옮겨 적은 줄은 하나도 없다.
> **읽는 법** — 이 주제의 근거는 거의 전부 **진단 문구**다. 진단 코드·문구·`(행,열)` 은 **안 흔들리는 칸**이고,\
> ★ **「에러가 몇 개 나오나」는 컴파일러가 어디서 포기하느냐에 달린 것**이라 문제의 개수와 다르다(4번).\
> **IL 덤프는 `-optimize` 없이**(기본 디버그) 낸 것이고, **`-debug` 는 안 줘서** 트레이스에 절대 경로가 없다.\
> 자세한 환경은 [2-summary.md](2-summary.md) 머리말에 있다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ 에러 **일곱** — 그 안에 추론된 타입이 그대로 적혀 있다

**출력**

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

**왜 그런가**

| 쓴 것 | 진단이 말한 타입 |
|---|---|
| `var a = 1;` | **`int`** |
| `var b = 1.0;` | **`double`** |
| `var c = "x";` | **`string`** |
| `var d = new[] { 1, 2, 3 };` | **`int[]`** |
| `var e = (1, "x");` | ★ **`(int, string)`** — 값 튜플 |
| `var f = () => 1;` | ★★ **`Func<int>`** — 람다의 자연 타입(C# 10) |
| `var g = 1 switch { … };` | ★★★ **`object`** |

- ★★★ **없는 멤버(`Nope()`)를 부르면 `CS1061` 이 「무엇이 그 멤버를 안 갖고 있는지」를 말해 준다.**\
  그 **작은따옴표 안**이 곧 컴파일러가 추론한 타입이다. **일곱 줄이 한 번에** 나온다.
- ★★★ **마지막 줄이 `object` 인 이유** — `switch` 식의 두 갈래가 `(object)"a"` 와 `2` 라\
  **둘을 다 담을 수 있는 공통 타입**이 `object` 다.\
  ★★ **「`var` 를 쓰면 구체적인 타입이 온다」가 항상 참은 아니다.**\
  ★ 그리고 그 자리에서 `2` 가 **박싱**된다 — 정본은 [03번](../03-boxing-and-unboxing/)이다.
- ★★★ **`GetType()` 보다 나은 이유는 「컴파일 타임 타입」을 답하기 때문**이다(2번).\
  ★ 실행이 필요 없고 IDE 도 필요 없다 — **컴파일러에게 직접 묻는 것**이다.

### 2. ★★ `GetType()` 은 **`Dog`** 를 답하지만 `var` 가 본 것은 **`Animal`** 이다

**출력**

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

**왜 그런가**

| 쓴 것 | `GetType()` | `var` 가 추론한 타입 |
|---|---|---|
| `var a = 1;` | `System.Int32` | `int` — ★ **같다** |
| `var b = (object)"x";` | ★★★ **`System.String`** | ★★★ **`object`** — **갈린다** |
| `var c = (Animal)new Dog();` | ★★★ **`Dog`** | ★★★ **`Animal`** — **갈린다** |
| `dynamic d = 1;` → `d = "x";` | `Int32` → `String` | ★ **타입이 없다** |

- ★★★ **`c.Fetch()`(`Dog` 에만 있는 메서드)는 컴파일이 안 된다.**\
  `var` 가 본 것은 **`Animal`** 이기 때문이다 — `GetType()` 이 `Dog` 를 답해도 그렇다.\
  ★★ **그래서 「`GetType()` 으로 확인했다」가 근거가 못 된다.**
- ★★ **`c.Speak()` 가 `멍` 을 답하는 것은 가상 디스패치**다.\
  ★★★ **「어느 멤버를 부를 수 있나」는 컴파일 타임 타입이, 「어느 구현이 뽑히나」는 런타임 타입이 정한다.**\
  둘이 다른 질문이라 답도 다르다.
- ★ **`dynamic` 은 둘 다 아니다** — 같은 변수의 `GetType()` 이 `Int32` 였다가 `String` 이 된다.\
  컴파일 타임 타입이라는 것이 **아예 없다**(8번).

### 3. ★★ 에러 **여덟** — 진단 코드가 **여섯 종류**다

**출력**

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

**왜 그런가**

| 쓴 것 | 진단 | 왜 |
|---|---|---|
| `var a;` | ``CS0818: Implicitly-typed variables must be initialized`` | 추론할 근거가 없다 |
| `var b = null;` | ``CS0815: Cannot assign <null> to an implicitly-typed variable`` | ★ **`null` 에는 타입이 없다** |
| `var c = default;` | ``CS8716: There is no target type for the default literal.`` | ★ **`default` 는 타겟이 필요한 식**이다 |
| `var d = 1, e = "x";` | ``CS0819: Implicitly-typed variables cannot have multiple declarators`` | 한 선언에 타입이 둘일 수 없다 |
| `var f = (x) => x;` | ``CS8917: The delegate type could not be inferred.`` | 매개변수 타입을 모른다 |
| `var g = int.Parse;` | ``CS8917`` | ★★ **오버로드가 여럿**이라 못 고른다 |
| `var[] h = { 1, 2 };` | ``CS0825`` | `var` 의 배열이라는 건 없다 |
| `var i = new();` | ``CS8754: There is no target type for 'new()'`` | ★★★ **양쪽 다 안 적었다**(7번) |

- ★★★ **`var b = null;` 과 `var c = default;` 가 다른 진단을 받는다.**\
  `null` 은 **「타입 없는 리터럴」**(`CS0815`), `default` 는 **「타겟이 필요한 식」**(`CS8716`)이다.\
  ★ **`object b = null;` 과 `int c = default;` 는 둘 다 된다** — **왼쪽이 있으면 되는 것**이다.
- ★★★ **`var g = int.Parse;` 가 막히는 이유는 「메서드 그룹이라서」가 아니다.**\
  `int.Parse` 에 **오버로드가 여럿**이라 자연 타입을 못 고르는 것이고,\
  5번에서 **오버로드가 하나뿐인 `Console.ReadLine` 은 통과한다.**
- ★ `CS8917` 이 **두 번** 나온 것(`f` 와 `g`)이 그 사실을 한 자리에서 보여 준다 — **같은 원인**이다.

### 4. ★ 에러 **셋** — 진단 코드는 **한 종류**(`CS0825`)

**출력**

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

**왜 그런가**

- ★★ **`var` 는 「지역 변수 선언」에만** 쓴다 — ``may only appear within a local variable declaration or in script code``.\
  **필드·반환 타입·매개변수가 전부 같은 `CS0825`** 다. ★ 외울 것이 하나다.
- ★★★ **3번은 여덟 개가 한 번에 나왔는데 여기는 셋이다.**\
  여기 셋은 전부 **선언(시그니처) 자리**의 에러라, Roslyn 이 **그 타입의 본문 바인딩을 더 진행하지 않는다.**\
  ★★★ **「에러가 몇 개 나오나」는 컴파일러가 어디서 포기하느냐에 달린 것**이지 **문제의 개수가 아니다.**\
  ★ 그래서 이 문서는 **「에러 개수」를 근거로 쓸 때 반드시 어느 소스에서 나온 것인지 같이 적었다.**

### 5. ★★ 다섯 줄 **전부 컴파일된다** — 람다도 익명 타입도 담긴다

**출력**

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

**왜 그런가**

| 쓴 것 | 추론된 타입 |
|---|---|
| `var f = () => 1;` | ★★ ``System.Func`1[System.Int32]`` — **C# 10부터** |
| `var g = (int x) => x + 1;` | ``System.Func`2[System.Int32,System.Int32]`` |
| `var h = Console.ReadLine;` | ★★ ``System.Func`1[System.String]`` |
| `var i = new List<int> { 1, 2 };` | ``System.Collections.Generic.List`1[System.Int32]`` |
| `var j = new { Won = 100, Cur = "KRW" };` | ★★★ ``<>f__AnonymousType0`2`` |

- ★★★ **「`var f = () => 1;` 이 안 된다」는 C# 9 까지의 이야기**다.\
  **C# 10부터 람다와 메서드 그룹에 자연 타입**이 생겨 `var` 에 담긴다.
- ★★★ **`Console.ReadLine` 은 되고 `int.Parse` 는 안 되는 것(3번)은 오버로드 개수가 가른다.**\
  `Console.ReadLine()` 은 **하나뿐**이라 자연 타입 ``System.Func`1[System.String]`` 이 정해지고,\
  `int.Parse` 는 **여럿**이라 못 고른다(`CS8917`).
- ★★★ **익명 타입은 `var` 가 아니면 적을 방법이 없다** — 이름이 ``<>f__AnonymousType0`2`` 라\
  **소스에 쓸 수 있는 식별자가 아니다.** ★ **`var` 가 선택이 아니라 필수인 유일한 자리**다.

### 6. ★★ 여섯 줄 **전부 컴파일된다** — 타겟은 「문맥이 요구하는 타입」이다

**출력**

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

**왜 그런가**

| 쓴 것 | 타겟은 무엇인가 |
|---|---|
| `Dictionary<string, List<int>> d = new();` | 변수의 **선언 타입** |
| `List<int> l = new(capacity: 4) { 1, 2 };` | 〃 — ★ **인자와 초기자도 같이** 쓴다 |
| `Point p = new(1, 2);` · `Point q = new();` | 〃 |
| `Take(new())` | ★★ **매개변수 타입** |
| `static Point Make() => new(9, 9);` | ★★ **반환 타입** |

- ★★★ **「왼쪽에 타입이 있으면 된다」는 부정확하다.**\
  정확한 문장은 「**문맥이 타입을 요구하면 된다**」이고, 그 문맥에는\
  **매개변수·반환 타입·필드 타입·`return` 자리**가 전부 포함된다.
- ★★ **`Take(new())` 는 읽기 어려운 쪽**이다 — 호출부만 봐서는 무엇이 만들어지는지 모른다.\
  ★ 컴파일이 된다고 쓸 일은 아니다(10번).

### 7. ★ ``error CS8754: There is no target type for 'new()'``

**출력**

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

**왜 그런가**

- ★★★ **`var` 는 오른쪽에서 타입을 얻고, `new()` 는 왼쪽(문맥)에서 얻는다.**\
  **둘 다 비면 타입이 나올 데가 아무 데도 없다.**
- ★ **고치는 법은 둘** — `var x = new Foo();` 또는 `Foo x = new();`.\
  ★★ **한쪽에만 적으면 된다** — 그래서 `var` 와 타겟 타입 `new()` 는 **경쟁이 아니라 짝**이다.

### 8. ★★ 에러 **둘** — 둘 다 `var` 쪽에서만 났다

**출력**

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

**왜 그런가**

| 쓴 것 | `var` | `dynamic` |
|---|---|---|
| 없는 멤버 호출 | ★★★ **`error CS1061`** | ★★★ **컴파일 통과** |
| 다른 타입 재대입 | ★★★ **`error CS0029`** | ★★★ **통과** |

- ★★★ **`dynamic` 의 두 줄은 아무 말도 안 듣는다.**\
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
  ★★★ **메시지 본문이 `CS1061` 과 거의 같다** — ``'int' does not contain a definition for 'Nope'``.\
  **같은 판단을 언제 하느냐만 다르다.**
- ★ 트레이스의 ``at CallSite.Target(Closure, CallSite, Object)`` 가 **호출 사이트**라는 기계다.\
  그 기계가 IL 에 그대로 찍힌다(9번). `run exit=134` 다.

### 9. ★★ 세 문법의 IL 바이트가 **`SequenceEqual` 로 `True`** 다

**출력**

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

**왜 그런가**

- ★★★ **`WithVar` · `WithExplicit` · `WithTargetNew` 의 IL 이 한 바이트도 다르지 않다.**\
  눈으로 비교한 게 아니라 **프로그램이 `GetILAsByteArray()` 를 받아 직접 대조**했다.
- ★★★ **그러니 `var` 를 고르는 기준에 성능은 안 들어간다.** 남는 판단은 **가독성뿐**이다(10번).
- ★★ `dynamic` 은 전혀 다르다.

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
  ``Microsoft.CSharp.RuntimeBinder.Binder::InvokeMember`` · `CSharpArgumentInfo` · `CallSite<…>::Create` 를 만들어\
  **정적 필드에 캐시하는 기계**가 통째로 들어간다(`ldsfld` → `brfalse.s` → 만들고 `stsfld`).
- ★★ **그 기계가 「런타임 바인딩」의 실체**다.\
  ★★★ **다만 이 문서는 그 비용을 시간으로 재지 않았다** — 잰 것은 **IL 줄 수**뿐이다.\
  호출 사이트는 **첫 호출에만** 만들어지고 그 뒤는 캐시를 타므로, **줄 수를 속도로 읽으면 안 된다.**

### 10. ★ 판단 기준은 한 문장이다

**왜 그런가**

- **`var` 가 필수인 자리** — ★★★ **익명 타입**(5번). 이름을 적을 방법이 없다.
- **명시 타입을 적어야 하는 자리 셋**\
  ① **오른쪽이 메서드 호출**이라 타입이 안 보일 때(`var x = Parse(s);`)\
  ② **인터페이스로 받고 싶을 때**(`IList<int> l = new List<int>();` — `var` 면 `List<int>` 가 된다)\
  ③ **`var` 가 예상 밖 타입을 추론할 때**(1번의 `object`).
- **타겟 타입 `new()` 를 피하는 게 나은 자리** — ★ **매개변수 자리**(`Take(new())`)(6번).\
  호출부만 봐서는 무엇이 만들어지는지 모른다.
- ★★★ **판단 기준 한 문장 — 「읽는 사람이 이 줄만 보고 타입을 아는가」.**\
  ★★ **IL 이 같으므로 성능은 기준이 아니다**(9번).

### 11. 잇는 자리

- **제네릭 메서드의 타입 인자 추론** — 목록의 **24번 주제**.\
  **여기는 지역 변수 선언까지, 거기는 타입 인자부터.**
- **`var` 가 `object` 를 추론하면** — 그 자리에서 값 타입이 **박싱**된다.\
  정본은 [03번 — 박싱과 언박싱](../03-boxing-and-unboxing/)이고, 1번의 마지막 줄이 정확히 그 자리다.
- **컬렉션 식 `[1, 2, ..other]`**(C# 12) — [목록의 **11번 주제**](../11-collection-initializers-and-collection-expressions/).\
  ★ `new()` 와 **같은 집안**인 이유는 **자기 타입이 없고 타겟이 있어야 하는 식**이라서다.
- **`Program.<Main>$(String[] args)`** — **최상위 문**이 만든 이름이다(목록의 **52번 주제**).\
  ★ 컴파일러가 `Program` 클래스와 `<Main>$` 메서드를 **합성**한 결과이고,\
  이 배치의 모든 예외 트레이스에 그 이름이 찍혀 있다.
- **튜플** — 1번의 `(int, string)` 은 목록의 **23번 주제**.\
  **람다의 자연 타입**은 목록의 **28번 주제**.

## 실행 검증

**무엇을 몇 번 어느 판에서 돌렸나** — 아래 블록은 전부 **.NET SDK 10.0.401 / 런타임 10.0.12 / `net10.0` / linux-x64** 에서\
캡처 스크립트로 받았다. **제출 직전에 전부 다시 돌려 `diff -rq` 로 대조했다.**

| 블록 | 무엇을 고정하나 | 명령 |
|---|---|---|
| `cs04b-inferred.cs` | ★★★ `CS1061` **일곱** — `int`·`double`·`string`·`int[]`·`(int, string)`·`Func<int>`·`object` | `csc` 만 |
| `cs04b-var-runtime.cs` | ★★ `GetType()` 이 **`Dog`** · `Speak()` 가 `멍` · `dynamic` 이 `Int32`→`String` | `csc` + 실행 |
| `cs04b-var-local.cs` | ★★ 에러 **여덟** · 코드 **여섯 종류** | `csc` 만 |
| `cs04b-var-decl.cs` | ★ 에러 **셋** · `CS0825` **한 종류** | 〃 |
| `cs04b-var-ok.cs` | ★★ 람다·메서드 그룹·익명 타입이 **담긴다** | `csc` + 실행 |
| `cs04b-target-new.cs` | ★★ 매개변수·반환 자리에서도 **된다** | 〃 |
| `cs04b-var-new.cs` | `error CS8754` | `csc` 만 |
| `cs04b-dynamic.cs` | ★★ 에러 **둘** — 둘 다 `var` 쪽 | 〃 |
| `cs04b-dynamic-run.cs` | `RuntimeBinderException` 전문 · `run exit=134` | `csc` + 실행 |
| `cs04b-il.cs` | ★★★ 세 문법의 IL 바이트가 **같다**(`SequenceEqual`) | `csc -r:il.dll` + 실행 |
| `cs04b-il-dynamic.cs` | ★★ `dynamic` 은 **80줄** | 〃 (`wc -l` · `head -20`) |

**구현 의존 항목** — 다음은 **이 환경(.NET 10.0.12 · Roslyn · x64 linux)에서만** 그렇다.

- ★★★ **세 문법의 IL 바이트가 같은 것** — **Roslyn 의 결과**다.\
  **언어가 보장하는 것은** 「**의미가 같다**」이고 **바이트가 같은 것이 아니다.**
- ★★ **`dynamic` 의 IL 이 80줄인 것** — Roslyn 과 `Microsoft.CSharp` 의 구현이다.\
  「런타임 바인딩이다」가 보장이고 **줄 수가 보장이 아니다.**
- ★ **익명 타입의 이름 ``<>f__AnonymousType0`2``** — 컴파일러가 붙이는 이름이고 **명세에 없다.**
- ★★ **에러가 한 번에 몇 개 나오는가**(3번의 8개 대 4번의 3개) — **컴파일러가 어디서 포기하느냐**다.
- ★ **IL 덤프의 `nop`** — `-optimize` 를 안 준 결과다.
- 진단 문구 · 예외 메시지 · 트레이스 형식 · 종료 코드 134 — 구현.

**언어가 보장하는 것**(구현이 바뀌어도 같다)

- **`var` 가 지역 변수 선언에만 쓰이고 초기자가 필요한** 것.
- ★★★ **`var` 가 정적 타입이고 `dynamic` 과 다른** 것 — 「의미가 명시 타입과 같다」가 명세다.
- **`null`·`default` 를 `var` 에 못 담는** 것 · **한 선언에 하나만 쓰는** 것.
- **타겟 타입 `new()` 가 문맥이 타입을 요구하는 자리에서 되는** 것(C# 9).
- **람다·메서드 그룹의 자연 타입**(C# 10) · **오버로드가 여럿이면 못 고르는** 것.
- **익명 타입을 `var` 로만 받을 수 있는** 것.

**안 돌려 본 것 / 못 잰 것**

- **안 돌려 본 것** — **C# 9 이하에서 `var f = () => 1;`**(이 머신에 .NET 10 만 있다) ·\
  **제네릭 메서드의 타입 인자 추론**(목록의 **24번 주제**) · **`is var x` 패턴**(목록의 **21번 주제**) ·\
  **`ref var`·`scoped var`**(목록의 **45번 주제**) · **컬렉션 식 `[1, 2]`**([목록의 **11번 주제**](../11-collection-initializers-and-collection-expressions/)) ·\
  **`-optimize` 를 켠 IL**.
- **못 잰 것** — ★★ **`dynamic` 의 실제 비용.**\
  9번이 잰 것은 **IL 줄 수**이고 **시간이 아니다.**\
  호출 사이트는 **첫 호출에만** 만들어지고 그 뒤는 **정적 필드 캐시**를 타므로,\
  **줄 수와 실행 시간이 비례하지 않는다.** 재려면 **반복 호출 하네스**가 따로 필요하다.\
  ★ 그래서 이 문서는 **「`dynamic` 이 느리다」를 적지 않았다** — 적은 것은 「**IL 이 80줄이다**」뿐이다.

**버전이 올랐을 때 다시 돌려야 하는 것**

- ★★ **9번의 IL 동일성** — Roslyn 이 바뀌면 움직인다(결론 「의미가 같다」는 안 움직인다).
- ★ **5번의 자연 타입** — 새 판이 `var` 에 담을 수 있는 것을 더 넓힐 수 있다.
- ★ **3·4번의 에러 개수** — 컴파일러가 포기하는 지점이 바뀌면 움직인다.
- **진단 문구와 진단 코드** 전부.
