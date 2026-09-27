# csharp/syntax/23 — 튜플과 해체(deconstruction) — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> ★★★ 이 주제의 질문은 「**튜플 원소의 이름은 어디에 사나**」 하나로 거의 다 풀린다 — 답이 막히면 **값·메서드 서명·컴파일러** 중 어디를 보는지 떠올려라.
> **환경** — .NET SDK 10.0.401 · 런타임 10.0.12 · `net10.0` · linux-x64 ·
> Roslyn `csc` 를 직접 부른다 · `-langversion:latest` · `-preferreduilang:en-US`.
> ★★★ **본체 창은 ③ 리플렉션이다.** 「이름이 경계를 넘나」는 **다른 어셈블리·`dynamic`·JSON 에게 이름을 불러 보게** 해서 물었다(제5의 상태).
> 선행 — [18번](../18-record-value-equality-and-with/)(`record` 와 생성되는 `Deconstruct`).

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (예측) / (왜) / (경계) / (연결) -->

### 1. ★★★ 이름 붙은 튜플을 리플렉션으로 (예측)

```csharp
// cs23b-refl.cs
using System;
using System.Reflection;
using System.Runtime.CompilerServices;
public static class Api {
    public static (int Id, string Name) Find() => (1, "kim");
}
class Program {
    static void Main() {
        var t = Api.Find();
        Type vt = t.GetType();
        Console.WriteLine($"[1] 타입        : {vt}");
        Console.WriteLine($"[2] IsValueType : {vt.IsValueType}");
        foreach (var f in vt.GetFields())
            Console.WriteLine($"[3] 필드        : {f.Name} ({f.FieldType.Name}) IsInitOnly={f.IsInitOnly}");
        Console.WriteLine($"[4] 속성 수     : {vt.GetProperties().Length}");
        var attr = typeof(Api).GetMethod("Find")!.ReturnParameter.GetCustomAttribute<TupleElementNamesAttribute>();
        Console.WriteLine($"[5] 반환값 특성 : {(attr is null ? "없음" : string.Join(",", attr.TransformNames))}");
        Type rt = Tuple.Create(1, "kim").GetType();
        Console.WriteLine($"[6] Tuple.Create: {rt} IsValueType={rt.IsValueType} 필드 {rt.GetFields().Length} · 속성 {rt.GetProperties().Length}");
        var big = (1, 2, 3, 4, 5, 6, 7, 8, 9);
        Console.WriteLine($"[7] 원소 9개    : {big.GetType()}");
        Console.WriteLine($"[8] big.Item9 = {big.Item9} · big.Rest.Item2 = {big.Rest.Item2} · big.Rest = {big.Rest}");
    }
}
```

- `[1]`\~`[8]` 에 무엇이 찍히는가?
- ★★★ `[3]` 필드 이름은 `Id`·`Name` 인가? `IsInitOnly` 는?
- ★★★ `[5]` — 이름은 **어디에서** 찾을 수 있는가?
- ★★ `[7]` 원소 9개 튜플의 런타임 타입은 어떤 모양인가?

### 2. ★★★ 이름이 다른 튜플 · 클래스 원소를 담은 튜플의 비교 (예측)

```csharp
// cs23b-eq.cs
using System;
class Money {
    public int Won;
    public Money(int w) => Won = w;
    public override bool Equals(object? o) => o is Money m && m.Won == Won;   // == 는 그대로 둔다
    public override int GetHashCode() => Won;
}
public static class Probe {
    public static bool Eq((int, string) a, (int, string) b) => a == b;
}
class Program {
    static void Main() {
        var a = (Id: 1, Name: "kim");
        (int Key, string Label) b = (1, "kim");
        Console.WriteLine($"[1] a == b       : {a == b}");
        Console.WriteLine($"[2] a.Equals(b)  : {a.Equals(b)}");
        var m1 = (new Money(100), 1);
        var m2 = (new Money(100), 1);
        Console.WriteLine($"[3] m1 == m2     : {m1 == m2}");
        Console.WriteLine($"[4] m1.Equals(m2): {m1.Equals(m2)}");
        Il.Dump(typeof(Probe), "Eq");
    }
}
```

```csharp
// cs23b-names.cs
class Program {
    static void Main() {
        (int Id, string Name) t = (Key: 1, Label: "kim");     // 이름이 다른 튜플 리터럴을 대입
        var s = (Id: 1, Name: "kim");
        System.Console.WriteLine(t.Id + s.Id);
    }
}
```

- `[1]`\~`[4]` 에 무엇이 찍히는가?
- ★★★ `Probe.Eq` 의 IL 은 두 원소를 **각각 무엇으로** 비교하는가 — `ValueTuple` 의 메서드를 부르는가?
- ★★ 둘째 소스는 컴파일되는가? 진단이 붙는다면 경고인가 에러인가?

### 3. ★★ 여러 가지를 해체하면 (예측)

```csharp
// cs23b-decon.cs
using System;
static class VersionExt {
    public static void Deconstruct(this Version v, out int major, out int minor) { major = v.Major; minor = v.Minor; }
}
class Pt {
    public int X, Y;
    public Pt(int x, int y) { X = x; Y = y; }
    public void Deconstruct(out int x, out int y) { Console.WriteLine("    Pt.Deconstruct 불림"); x = X; y = Y; }
}
record Person(string Name, int Age);
class Program {
    static (int Min, int Max) MinMax(int[] xs) => (Math.Min(xs[0], xs[^1]), Math.Max(xs[0], xs[^1]));
    static void Main() {
        var (lo, hi) = MinMax(new[] { 7, 3 });
        Console.WriteLine($"[1] lo={lo} hi={hi}");
        var (major, minor) = new Version(10, 2);
        Console.WriteLine($"[2] major={major} minor={minor}");
        var (x, _) = new Pt(4, 5);
        Console.WriteLine($"[3] x={x}");
        var (name, age) = new Person("kim", 30);
        Console.WriteLine($"[4] name={name} age={age}");
        int a = 1, b = 2;
        (a, b) = (b, a);
        Console.WriteLine($"[5] a={a} b={b}");
        Console.WriteLine($"[6] {(new Pt(0, 3) is (0, var y) ? $"y={y}" : "아님")}");
    }
}
```

- `[1]`\~`[6]` 과 로그 줄은 어떤 순서로 찍히는가?
- ★★★ `[2]` — `System.Version` 은 튜플도 record 도 아니다. 무엇이 해체를 가능하게 했나?
- ★ `[3]` 은 `y` 를 `_` 로 버렸다 — `Deconstruct` 는 불리는가?

### 4. ★★ 컬렉션 안의 튜플을 고치면 (예측)

```csharp
// cs23b-mut.cs
using System.Collections.Generic;
class Program {
    static void Main() {
        var arr  = new[] { (Id: 1, Name: "kim") };
        var list = new List<(int Id, string Name)> { (1, "kim") };
        var dict = new Dictionary<string, (int Id, string Name)> { ["k"] = (1, "kim") };
        arr[0].Id = 9;                // 배열 원소
        list[0].Id = 9;               // List 인덱서가 돌려준 값
        dict["k"].Id = 9;             // Dictionary 인덱서가 돌려준 값
    }
}
```

```csharp
// cs23b-mut2.cs
using System;
using System.Collections.Generic;
class Program {
    static void Main() {
        var arr  = new[] { (Id: 1, Name: "kim") };
        var list = new List<(int Id, string Name)> { (1, "kim") };
        arr[0].Id = 9;
        var copy = list[0];
        copy.Id = 9;
        Console.WriteLine($"[1] arr[0]  = {arr[0]}");
        Console.WriteLine($"[2] list[0] = {list[0]} · copy = {copy}");
    }
}
```

- 첫 소스의 **어느 줄**에 진단이 붙는가 — 배열 줄은?
- ★★ 둘째 소스의 `[1]`·`[2]` 는?

### 5. ★★★ 라이브러리만 이름을 바꿔 끼우면 (예측)

```csharp
// cs23b-lib1.cs
using System.Collections.Generic;
public record User(int Id, string Name);
public static class Repo {
    public static (int Id, string Name) Find() => (1, "kim");
    public static List<(int Id, string Name)> All() => new() { (1, "kim"), (2, "lee") };
    public static User FindUser() => new(1, "kim");
}
```

```csharp
// cs23b-app.cs
using System;
class Program {
    static void Main() {
        var t = Repo.Find();
        Console.WriteLine($"[1] t.Id={t.Id} t.Name={t.Name}");
        foreach (var r in Repo.All()) Console.WriteLine($"[2] r.Id={r.Id}");
        try { dynamic d = Repo.Find(); Console.WriteLine($"[3] d.Id={d.Id}"); }
        catch (Exception e) { Console.WriteLine($"[3] {e.GetType().Name} : {e.Message}"); }
        try { Console.WriteLine($"[4] user.Id={ReadUser()}"); }
        catch (Exception e) { Console.WriteLine($"[4] {e.GetType().Name} : {e.Message}"); }
    }
    static int ReadUser() => Repo.FindUser().Id;
}
```

```csharp
// cs23b-lib2.cs
using System.Collections.Generic;
public record User(int Key, string Label);                 // 이름만 바꿨다
public static class Repo {
    public static (int Key, string Label) Find() => (1, "kim");                     // 이름만 바꿨다
    public static List<(int Key, string Label)> All() => new() { (1, "kim"), (2, "lee") };
    public static User FindUser() => new(1, "kim");
}
```

- `lib1` 로 컴파일한 앱을 돌리면 `[1]`\~`[4]` 는?
- ★★★ 라이브러리만 `lib2` 로 바꿔 끼우고 **앱은 다시 컴파일하지 않으면** — 튜플 쪽 `[1]`·`[2]` 와 record 쪽 `[4]` 는 각각?
- ★★ 같은 앱을 `lib2` 로 **다시 컴파일**하면?

### 6. ★★ 튜플과 record 를 직렬화하면 (예측)

```csharp
// cs23b-json.cs
using System;
using System.Text.Json;
record User(int Id, string Name);
class Program {
    static void Main() {
        (int Id, string Name) t = (1, "kim");
        var u = new User(1, "kim");
        Console.WriteLine($"[1] 튜플 ToString   : {t}");
        Console.WriteLine($"[2] record ToString : {u}");
        Console.WriteLine($"[3] 튜플 JSON       : {JsonSerializer.Serialize(t)}");
        Console.WriteLine($"[4] record JSON     : {JsonSerializer.Serialize(u)}");
        Console.WriteLine($"[5] 튜플 JSON(필드 포함) : {JsonSerializer.Serialize(t, new JsonSerializerOptions { IncludeFields = true })}");
        object o = t;
        Console.WriteLine($"[6] object 로 올린 뒤 : {o.GetType().GetField("Item1")?.GetValue(o)} · Id 필드 {(o.GetType().GetField("Id") is null ? "없음" : "있음")}");
    }
}
```

- `[1]`\~`[6]` 에 무엇이 찍히는가?
- ★★★ `[3]` 은 에러인가, 경고인가, 아니면?

### 7. ★★ 네 가지 「여러 값 묶음」의 할당 (경계)

- 값 튜플 `(int, int)` · `Tuple<int, int>` · `record class` · `record struct` 를 **1000번씩 돌려받으면** 각각 몇 바이트인가?
- ★★ 네 판(2×2)에서 값이 갈리는가?
- ★★★ 「튜플은 가벼워서 쓴다」는 이 결과 앞에서 무엇이 남는가?

### 8. ★★★ 튜플을 `record` 로 올려야 하는 자리 (왜)

- **공개 API 반환**에서 튜플의 문제는 정확히 무엇인가 — 5·6번 중 어느 것이 근거인가?
- ★★ **이름을 바꿀 가능성**이 있는 데이터라면 튜플과 record 중 어느 쪽이 더 위험한가 — 왜 「조용히 도는 것」이 위험한가?
- ★ 튜플이 **맞는** 자리는 어디인가?

### 9. ★★ 이름이 경계를 넘는지를 리플렉션만으로 못 묻는 이유 (왜)

- 1번 `[3]` 처럼 **값의 타입**을 찍어서는 왜 답이 안 나오는가?
- ★★ 그래서 어떤 창으로 바꿔 물었나 — 그 창이 **못 보는 것**은?

### 10. 다른 주제와 잇기 (연결)

- ★★★ record 가 `Deconstruct` 를 생성한다는 것의 정본은?
- ★★ 2번 `[3]`·`[4]` 가 갈린 뿌리는 몇 번 주제의 무엇인가?
- ★ 위치 패턴이 `Deconstruct` 를 부르는 것은 몇 번 주제에서 로그로 봤나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
