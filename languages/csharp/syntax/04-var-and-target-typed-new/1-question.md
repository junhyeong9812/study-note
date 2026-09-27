# csharp/syntax/04 — 변수 선언·`var`·타겟 타입 `new` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> **환경** — .NET SDK **10.0.401** · 런타임 **.NET 10.0.12** · 타겟 **`net10.0`** · linux-x64.
> 진단은 **영어로 고정**했다(`DOTNET_CLI_UI_LANGUAGE=en` + `csc -preferreduilang:en-US`).
> ★★★ **이 주제는 진단이 교재다** — 값의 대부분이 **에러 문구** 안에 있다.
> ★★ **`GetType()` 으로 확인했다는 답은 함정이다**(2번) — 그것은 **런타임 타입**이다.
> ★ **「람다는 `var` 에 못 담는다」를 의심해라** — 5번에서 판이 바뀐다.
> 선행 — [01번](../01-value-types-and-reference-types/). 형제 [03번](../03-boxing-and-unboxing/)과 (1)에서 이어진다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★★ 컴파일러는 무엇으로 추론했나 (예측)

```csharp
// cs04b-inferred.cs
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
```

- 에러가 **몇 개** 나는가?
- 각 에러가 말하는 **타입 일곱 개**를 맞힐 수 있는가?
- `var g = 1 switch { 1 => (object)"a", _ => 2 };` 가 **무엇으로** 추론되는가 — **왜**인가?
- 이 기법이 `GetType()` 보다 나은 **이유**는?

### 2. ★★ `GetType()` 은 무엇을 답하나 (경계)

```csharp
// cs04b-var-runtime.cs
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
```

- `var c = an;`(선언 타입이 `Animal`)의 `GetType()` 은 무엇을 답하는가?
- 그러면 `c.Fetch()`(`Dog` 에만 있는 메서드)는 **컴파일되는가**?
- `c.Speak()` 가 **어느 구현**을 부르는가 — 1번의 답과 **왜 다른가**?
- 「어느 멤버를 부를 수 있나」와 「어느 구현이 뽑히나」를 각각 **무엇이** 정하는가?

### 3. ★★ 지역 변수 자리의 여덟 줄 (예측)

```csharp
// cs04b-var-local.cs
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
```

- 에러가 **몇 개** 나는가 — 진단 코드를 **각각** 맞힐 수 있는가?
- `var b = null;` 과 `var c = default;` 가 **다른 진단**을 받는 이유는?
- `var g = int.Parse;` 가 막히는 이유가 「메서드 그룹이라서」인가 **다른 것**인가?
- `object b = null;` 은 되는가?

### 4. ★ 선언 자리에서는 (예측)

```csharp
// cs04b-var-decl.cs
class Holder {
    var field = 1;                      // ① 필드
}

class Program {
    static var Method() => 1;           // ② 반환 타입
    static void Param(var x) { }        // ③ 매개변수
    static void Main() { }
}
```

- 에러가 **몇 개** 나는가 — 진단 코드는 **몇 종류**인가?
- 3번은 여덟 개가 한 번에 나왔는데 여기는 왜 다른가?
- 「에러 개수」가 **문제의 개수**인가?

### 5. ★★ 람다·메서드 그룹·익명 타입을 담으면 (예측)

```csharp
// cs04b-var-ok.cs
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
```

- 다섯 줄이 **전부 컴파일되는가**?
- `var f = () => 1;` 은 무엇으로 추론되는가 — **C# 몇부터**인가?
- `Console.ReadLine` 은 되고 `int.Parse` 는 안 되는(3번) **이유**는?
- **`var` 가 선택이 아니라 필수**인 자리는 어디인가?

### 6. ★★ 타겟 타입 `new()` 는 어디까지 되나 (예측)

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

- 여섯 줄이 **전부 컴파일되는가**?
- `Take(new())` 에서 타겟은 **무엇**인가?
- `static Point Make() => new(9, 9);` 는?
- 「왼쪽에 타입이 있으면 된다」가 정확한 문장인가?

### 7. ★ `var x = new();` (경계)

- 컴파일되는가 — 진단 코드와 문구는?
- **왜** 그런가 — `var` 와 `new()` 는 각각 **어디서** 타입을 얻는가?
- 고치는 방법 **둘**은?

### 8. ★★ `var` 와 `dynamic` (예측)

```csharp
// cs04b-dynamic.cs
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
```

- 에러가 **몇 개** 나는가 — **어느 줄**에서 나는가?
- `dynamic` 쪽 두 줄은 **왜** 통과하는가?
- 그러면 `dynamic` 의 틀림은 **언제** 드러나는가 — 예외 이름과 메시지는?
- 그 메시지가 `var` 쪽 진단과 **얼마나 다른가**?

### 9. ★★ `var` 는 무엇을 바꾸나 (왜)

```csharp
// cs04b-il.cs
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
```

- 세 메서드의 IL 이 **같은가 다른가** — 어떻게 확인했는가?
- 그러면 `var` 를 고르는 기준에 **성능이 들어가는가**?
- `dynamic` 으로 같은 일을 하면 IL 이 **몇 줄**이 되는가?
- 그 줄들이 **무엇을 만드는** 코드인가?

### 10. ★ 무엇을 쓸까 (경계)

- **`var` 가 필수**인 자리는?
- **명시 타입을 적어야 하는** 자리 셋은?
- **타겟 타입 `new()` 를 피하는 게 나은** 자리는?
- 판단 기준을 **한 문장**으로 줄이면?

### 11. 다른 주제와 잇기 (연결)

- **제네릭 메서드의 타입 인자 추론**은 목록의 몇 번인가?
- `var` 가 `object` 를 추론하면 그 자리에서 무슨 일이 나는가 — 어느 주제가 정본인가?
- `[1, 2, ..other]`(컬렉션 식)이 `new()` 와 **같은 집안**인 이유는 — 목록의 몇 번인가?
- 예외 트레이스의 `Program.<Main>$(String[] args)` 라는 이름은 **무엇이 만든** 것인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
