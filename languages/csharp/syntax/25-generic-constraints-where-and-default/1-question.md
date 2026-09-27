# csharp/syntax/25 — 제네릭 제약 `where` 와 `default(T)` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> ★★★ 이 주제의 질문은 「**이 제약은 누가 지키나 — 컴파일러인가 런타임인가**」와 「**`default` 는 생성자를 부르나**」 두 줄로 거의 다 풀린다.
> **환경** — .NET SDK 10.0.401 · 런타임 10.0.12 · `net10.0` · linux-x64 ·
> Roslyn `csc` 를 직접 부른다 · `-langversion:latest`(판 격자 문항만 판을 바꾼다) · `-preferreduilang:en-US`.
> ★★★ **본체 창은 ② 진단 격자다.** 제약 10 × 인자 8 = 80칸을 한 번에 컴파일하고 스크립트가 칸으로 되돌려 센다.
> 선행 — [24번](../24-generics-and-type-parameters/)(제네릭 — 그 (6)이 제약 위반 여섯을 예고편으로 넘겼다).

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (예측) / (왜) / (경계) / (연결) -->

### 1. ★★★ 제약 10 × 타입 인자 8 (예측)

```csharp
// cs25b-grid.cs
using System;
abstract class Shape { }
struct Pt { public int X; public Pt(int x) { X = x; } }
static class K {
    public static void Class<T>()     where T : class { }
    public static void ClassQ<T>()    where T : class? { }
    public static void Struct<T>()    where T : struct { }
    public static void NotNull<T>()   where T : notnull { }
    public static void Unmanaged<T>() where T : unmanaged { }
    public static void New<T>()       where T : new() { }
    public static void IComp<T>()     where T : IComparable { }
    public static void Base<T>()      where T : Shape { }
    public static void Enum<T>()      where T : System.Enum { }
    public static void Deleg<T>()     where T : Delegate { }
}
class Program {
    static void Main() {
        K.Class<int>(); K.Class<int?>(); K.Class<string>(); K.Class<string?>(); K.Class<Shape>(); K.Class<Pt>(); K.Class<DayOfWeek>(); K.Class<Action>();
        K.ClassQ<int>(); K.ClassQ<int?>(); K.ClassQ<string>(); K.ClassQ<string?>(); K.ClassQ<Shape>(); K.ClassQ<Pt>(); K.ClassQ<DayOfWeek>(); K.ClassQ<Action>();
        K.Struct<int>(); K.Struct<int?>(); K.Struct<string>(); K.Struct<string?>(); K.Struct<Shape>(); K.Struct<Pt>(); K.Struct<DayOfWeek>(); K.Struct<Action>();
        K.NotNull<int>(); K.NotNull<int?>(); K.NotNull<string>(); K.NotNull<string?>(); K.NotNull<Shape>(); K.NotNull<Pt>(); K.NotNull<DayOfWeek>(); K.NotNull<Action>();
        K.Unmanaged<int>(); K.Unmanaged<int?>(); K.Unmanaged<string>(); K.Unmanaged<string?>(); K.Unmanaged<Shape>(); K.Unmanaged<Pt>(); K.Unmanaged<DayOfWeek>(); K.Unmanaged<Action>();
        K.New<int>(); K.New<int?>(); K.New<string>(); K.New<string?>(); K.New<Shape>(); K.New<Pt>(); K.New<DayOfWeek>(); K.New<Action>();
        K.IComp<int>(); K.IComp<int?>(); K.IComp<string>(); K.IComp<string?>(); K.IComp<Shape>(); K.IComp<Pt>(); K.IComp<DayOfWeek>(); K.IComp<Action>();
        K.Base<int>(); K.Base<int?>(); K.Base<string>(); K.Base<string?>(); K.Base<Shape>(); K.Base<Pt>(); K.Base<DayOfWeek>(); K.Base<Action>();
        K.Enum<int>(); K.Enum<int?>(); K.Enum<string>(); K.Enum<string?>(); K.Enum<Shape>(); K.Enum<Pt>(); K.Enum<DayOfWeek>(); K.Enum<Action>();
        K.Deleg<int>(); K.Deleg<int?>(); K.Deleg<string>(); K.Deleg<string?>(); K.Deleg<Shape>(); K.Deleg<Pt>(); K.Deleg<DayOfWeek>(); K.Deleg<Action>();
    }
}
```

- 80칸 가운데 **에러로 막히는 칸 · 경고만 나는 칸 · 통과하는 칸**은 각각 몇인가?
- ★★★ `int?` 행 — `Struct`·`Unmanaged`·`IComp`·`New` 중 **통과하는 것**은?
- ★★ `string?` 이 **에러가 아니라 경고**로 떨어지는 칸은 어디인가 — `ClassQ` 는?
- ★★ 인터페이스 제약 위반이 `CS0311` 과 `CS0315` 로 갈리는 기준은?

### 2. ★★★ `default(T)` 를 여러 타입으로 (예측)

```csharp
// cs25b-default.cs
using System;
using System.Globalization;
struct Pt { public int X; public string? Name; public Pt(int x) { X = x; Name = "set"; } }
struct Pz { public int X; public Pz() { X = 7; } }
static class G {
    public static T Def<T>() => default!;
    public static T Make<T>() where T : new() => new T();
    public static string Show<T>(T v) => v is null ? "null" : Convert.ToString(v, CultureInfo.InvariantCulture)!;
}
class Program {
    static void Main() {
        Console.WriteLine($"[1] Def<int>()        = {G.Show(G.Def<int>())}");
        Console.WriteLine($"[2] Def<int?>()       = {G.Show(G.Def<int?>())}");
        Console.WriteLine($"[3] Def<string>()     = {G.Show(G.Def<string>())}");
        Console.WriteLine($"[4] Def<bool>()       = {G.Show(G.Def<bool>())}");
        Console.WriteLine($"[5] Def<double>()     = {G.Show(G.Def<double>())}");
        Console.WriteLine($"[6] Def<DateTime>()   = {G.Def<DateTime>().ToString("o", CultureInfo.InvariantCulture)}");
        Console.WriteLine($"[7] Def<DayOfWeek>()  = {G.Show(G.Def<DayOfWeek>())}");
        var p = G.Def<Pt>();
        Console.WriteLine($"[8] Def<Pt>()         = X={p.X} Name={G.Show(p.Name)}");
        Console.WriteLine($"[9] Def<(int,string)>() = {G.Def<(int, string)>()}");
        Console.WriteLine($"[10] Def<Pz>().X      = {G.Def<Pz>().X}");
        Console.WriteLine($"[11] Make<Pz>().X     = {G.Make<Pz>().X}");
        Console.WriteLine($"[12] default(Pz).X    = {default(Pz).X} · new Pz().X = {new Pz().X}");
    }
}
```

- `[1]`\~`[9]` 에 무엇이 찍히는가? `[8]` 의 `Name` 은 생성자가 넣은 `"set"` 인가?
- ★★★ `[10]`\~`[12]` — `default(Pz)` 와 `new Pz()` 와 `Make<Pz>()` 의 `X` 는?

### 3. ★★ 제약을 바꾼 `new T()` 셋의 IL (예측)

```csharp
// cs25b-il.cs
using System;
public static class G {
    public static T Def<T>() => default!;
    public static T NewAny<T>() where T : new() => new T();
    public static T NewStruct<T>() where T : struct => new T();
    public static T NewClass<T>() where T : class, new() => new T();
}
class Program {
    static void Main() {
        foreach (var n in new[] { "Def", "NewAny", "NewStruct", "NewClass" }) Il.Dump(typeof(G), n);
    }
}
```

- `Def` 의 IL 에서 `T` 가 나오는 명령은?
- ★★ `NewStruct`(`where T : struct`)의 `new T()` 는 `NewAny` 와 **다른 명령**으로 컴파일되는가?

### 4. ★★ 생성자가 던지는 타입을 `new T()` 로 만들면 (예측)

```csharp
// cs25b-throw.cs
using System;
class Boom { public Boom() { throw new InvalidOperationException("ctor failed"); } }
static class G { public static T Make<T>() where T : new() => new T(); }
class Program {
    static void Main() {
        try { new Boom(); }
        catch (Exception e) { Console.WriteLine($"[1] new Boom()    → {e.GetType().FullName}: {e.Message}"); }
        try { G.Make<Boom>(); }
        catch (Exception e) {
            Console.WriteLine($"[2] Make<Boom>() → {e.GetType().FullName}: {e.Message}");
            Console.WriteLine($"    InnerException → {e.InnerException?.GetType().FullName}: {e.InnerException?.Message}");
        }
    }
}
```

- `[1]` 과 `[2]` 에서 잡힌 예외 **타입**은 각각?
- ★ `catch (InvalidOperationException)` 만 써 두었다면 `[2]` 는 잡히는가?

### 5. ★★★ 컴파일러를 건너뛰고 제약을 어기면 (예측)

```csharp
// cs25b-refl.cs
using System;
using System.Linq;
struct HasRef { public string S; public HasRef(string s) { S = s; } }
abstract class Shape { }
static class G {
    public static string Class<T>()     where T : class => typeof(T).Name;
    public static string ClassQ<T>()    where T : class? => typeof(T).Name;
    public static string Struct<T>()    where T : struct => typeof(T).Name;
    public static string New<T>()       where T : new() => typeof(T).Name;
    public static string NotNull<T>()   where T : notnull => typeof(T).Name;
    public static string Unmanaged<T>() where T : unmanaged => typeof(T).Name;
    public static string IComp<T>()     where T : IComparable<T> => typeof(T).Name;
    public static string Enum<T>()      where T : System.Enum => typeof(T).Name;
}
class Program {
    static string Attrs(System.Collections.Generic.IList<System.Reflection.CustomAttributeData> xs) =>
        string.Join(",", xs.Select(a => a.AttributeType.Name.Replace("Attribute", "") + "(" + string.Join(",", a.ConstructorArguments.Select(x => x.Value)) + ")"));
    static void Try(string m, Type arg) {
        try { var r = typeof(G).GetMethod(m)!.MakeGenericMethod(arg).Invoke(null, null); Console.WriteLine($"   {m,-9}<{arg.Name,-11}> ok → {r}"); }
        catch (Exception e) { Console.WriteLine($"   {m,-9}<{arg.Name,-11}> {e.GetType().Name}"); }
    }
    static void Main() {
        Console.WriteLine($"[A] 제약이 메타데이터에 남은 모양 (클래스 G 의 특성=[{Attrs(typeof(G).GetCustomAttributesData())}])");
        foreach (var n in new[] { "Class", "ClassQ", "Struct", "New", "NotNull", "Unmanaged", "IComp", "Enum" }) {
            var mi = typeof(G).GetMethod(n)!;
            var t = mi.GetGenericArguments()[0];
            Console.WriteLine($"   {n,-9} 플래그={t.GenericParameterAttributes} · 타입=[{string.Join(",", t.GetGenericParameterConstraints().Select(c => c.Name))}] · T 특성=[{Attrs(t.GetCustomAttributesData())}] · 메서드 특성=[{Attrs(mi.GetCustomAttributesData())}]");
        }
        Console.WriteLine("[B] 컴파일러를 건너뛰고 MakeGenericMethod 로 어긴 인자를 넣으면");
        Try("Class", typeof(int)); Try("Struct", typeof(string)); Try("Struct", typeof(int?)); Try("New", typeof(Shape));
        Try("IComp", typeof(Shape)); Try("Enum", typeof(int)); Try("Unmanaged", typeof(string));
        Try("Unmanaged", typeof(HasRef)); Try("NotNull", typeof(string));
    }
}
```

- `[A]` — `class` 와 `class?` 의 **플래그**는 다른가? `notnull` 의 플래그는?
- ★★★ `[B]` 아홉 줄 가운데 **`ok` 가 나오는 줄**은 어느 것인가?

### 6. ★★★ `T?` 셋과 조건 연산자 안의 `default` (예측)

```csharp
// cs25b-tq.cs
using System;
static class F {
    public static T? Any<T>(bool hit, T v) => hit ? v : default;
    public static T? Val<T>(bool hit, T v) where T : struct => hit ? v : default;
    public static T? Val2<T>(bool hit, T v) where T : struct => hit ? v : default(T?);
    public static T? Ref<T>(bool hit, T v) where T : class => hit ? v : default;
}
class Program {
    static string S(object? o) => o is null ? "null" : o.ToString()!;
    static string Ret(string m) => typeof(F).GetMethod(m)!.MakeGenericMethod(typeof(int)).ReturnType.Name;
    static void Main() {
        Console.WriteLine($"[1] Any(false, 5)   = {S(F.Any(false, 5))} · Any<int> 반환 타입 {Ret("Any")}");
        Console.WriteLine($"[2] Val(false, 5)   = {S(F.Val(false, 5))} · Val<int> 반환 타입 {Ret("Val")}");
        Console.WriteLine($"[3] Val2(false, 5)  = {S(F.Val2(false, 5))} · Val2<int> 반환 타입 {Ret("Val2")}");
        Console.WriteLine($"[4] Any(false, \"a\") = {S(F.Any(false, "a"))}");
        Console.WriteLine($"[5] Ref(false, \"a\") = {S(F.Ref(false, "a"))}");
    }
}
```

- `[1]`\~`[5]` 에 무엇이 찍히는가?
- ★★★ `[2]` 와 `[3]` 은 반환 타입이 같다 — 값도 같은가?

### 7. ★★ 제약만 다른 두 메서드 · 제약 위반 후보 (경계)

- 제약만 다른 `G<T>(T) where T : class` 와 `G<T>(T) where T : struct` 를 한 클래스에 두면?
- ★★★ `F<T>(T) where T : struct` 와 `F(object)` 에 `"s"` 를 넘기면 — **C# 7.2 와 7.3** 에서 답이 같은가?

### 8. ★★ 제약 문법의 도입 판 (경계)

- `Enum`·`Delegate`·`unmanaged`·`notnull` 제약과 **제약 없는 `T?`** 는 각각 **몇 판부터**인가 — 무엇으로 확인하나?

### 9. ★★★ 제약은 누가 보장하나 (왜)

- `class`·`struct`·`new()` 제약과 `notnull`·`class?` 제약은 **어느 층**의 약속인가?
- ★★★ `unmanaged` 는 왜 「반쯤」인가?

### 10. ★ `new T()` 의 비용 (경계)

- `G.Make<Node>()` 는 `new Node()` 보다 **바이트를 더** 할당했나 — 판을 바꿔도?
- ★ 이 문서에서 「`new T()` 가 느리다」를 말할 수 있나?

### 11. 다른 주제와 잇기 (연결)

- ★★ `where T : class` 안의 `==` 가 참조 비교인 IL 을 찍은 주제는?
- ★ `new()` 제약 대신 무엇을 받으면 `Activator` 경유를 피하나 — 그 정본은 몇 번 주제인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
