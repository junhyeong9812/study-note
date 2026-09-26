# csharp/syntax/30 — 확장 메서드와 확장 멤버(C# 14) — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> ★★★ 이 주제의 질문은 「**확장 멤버는 전부 정적 메서드이고, 수신자는 첫 인자다 — 컴파일러가 이름을 찾을 때 마지막에야 본다**」 한 줄로 거의 다 풀린다.
> **환경** — .NET SDK 10.0.401 · 런타임 10.0.12 · `net10.0` · linux-x64 ·
> Roslyn `csc` 를 직접 부른다 · `-langversion:latest`(판 격자 문항만 판을 바꾼다) · `-preferreduilang:en-US`. 대비는 **javac 21.0.5** 다.
> ★★★ **본체 창은 ① IL 덤프다**(「정적 메서드의 문법 설탕」). C# 14 의 범위는 **② 판 격자**로 물었다.
> 선행 — [27번](../27-delegates-and-func-action/)(정적 메서드 · 메서드 그룹) · [14번](../14-indexers/) (7)(확장 인덱서).

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (예측) / (왜) / (경계) / (연결) -->

### 1. ★★★ `this` 확장 메서드 · `extension` 블록의 메서드와 속성을 열어 보면 (예측)

```csharp
// cs30b-il.cs
using System;
using System.Linq;
using System.Reflection;
using System.Runtime.CompilerServices;
public static class Ext {
    public static int Twice(this int x) => x * 2;
    extension(int x) {
        public int Thrice() => x * 3;
        public int Square => x * x;
    }
}
public static class Use {
    public static int CallSugar(int n) => n.Twice();
    public static int CallPlain(int n) => Ext.Twice(n);
    public static int CallBlock(int n) => n.Thrice() + n.Square;
}
class Program {
    const BindingFlags All = BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Static | BindingFlags.Instance | BindingFlags.DeclaredOnly;
    static void Main() {
        var t = typeof(Ext);
        Console.WriteLine($"Ext : abstract={t.IsAbstract} sealed={t.IsSealed} [Extension]={t.IsDefined(typeof(ExtensionAttribute))}");
        foreach (var m in t.GetMethods(All).OrderBy(m => m.Name, StringComparer.Ordinal))
            Console.WriteLine($"  메서드 {(m.IsStatic ? "static " : "")}{m.ReturnType.Name} {m.Name}({string.Join(", ", m.GetParameters().Select(p => p.ParameterType.Name + " " + p.Name))}) [Extension]={m.IsDefined(typeof(ExtensionAttribute))} specialname={m.IsSpecialName}");
        foreach (var p in t.GetProperties(All))
            Console.WriteLine($"  속성   {p.Name}");
        foreach (var n in t.GetNestedTypes(All).OrderBy(n => n.Name, StringComparer.Ordinal)) {
            Console.WriteLine($"  중첩 타입 {n.Name}");
            foreach (var m in n.GetMembers(All).OrderBy(m => m.Name, StringComparer.Ordinal))
                Console.WriteLine($"    {m.MemberType} {m.Name}");
        }
        Il.Dump(typeof(Use), "CallSugar");
        Il.Dump(typeof(Use), "CallPlain");
        Il.Dump(typeof(Use), "CallBlock");
        Console.WriteLine($"[결과] {Use.CallSugar(5)} {Use.CallPlain(5)} {Use.CallBlock(5)}");
        var where = typeof(Enumerable).GetMethods().Where(m => m.Name == "Where").ToArray();
        Console.WriteLine($"[LINQ] Enumerable.Where 오버로드 {where.Length} 개 · static 인 것 {where.Count(m => m.IsStatic)} · [Extension] 인 것 {where.Count(m => m.IsDefined(typeof(ExtensionAttribute)))} · 첫 매개변수 타입 {where[0].GetParameters()[0].ParameterType.Name}");
    }
}
```

- `CallSugar`(`n.Twice()`)와 `CallPlain`(`Ext.Twice(n)`)의 IL 은 다른가?
- ★★★ `extension` 블록의 `Thrice` 와 속성 `Square` 는 `Ext` 에서 무엇이 되나? `[Extension]` 표지는 어디에 붙나?
- ★★ `Ext` 에 **속성** `Square` 가 보이나? 컴파일러가 만든 중첩 타입이 있나?

### 2. ★★★ `null` 인 수신자로 부르면 (예측)

```csharp
// cs30b-null.cs
using System;
public static class Ext {
    public static bool IsBlank(this string? s) => s is null || s.Trim().Length == 0;
}
public static class Probe {
    public static bool ViaExtension(string? s) => s.IsBlank();
    public static int ViaInstance(string? s) => s!.GetHashCode();
}
class Program {
    static void Main() {
        string? s = null;
        try { Console.WriteLine($"[1] s.IsBlank() : {Probe.ViaExtension(s)}"); }
        catch (Exception e) { Console.WriteLine($"[1] s.IsBlank() : {e.GetType().Name}"); }
        try { Console.WriteLine($"[2] s.GetHashCode() : {Probe.ViaInstance(s)}"); }
        catch (Exception e) { Console.WriteLine($"[2] s.GetHashCode() : {e.GetType().Name}"); }
        Il.Dump(typeof(Probe), "ViaExtension");
        Il.Dump(typeof(Probe), "ViaInstance");
    }
}
```

- `[1]`·`[2]` 는?
- ★★ 두 메서드의 IL 은 **호출 명령**이 어떻게 다른가?

### 3. ★★ 이름이 겹치면 · 정적 타입과 실제 타입이 다르면 (예측)

```csharp
// cs30b-win.cs
using System;
class Greeter {
    public string Hello() => "Greeter.Hello (인스턴스)";
}
static class Ext {
    public static string Hello(this Greeter g) => "Ext.Hello (확장)";
    public static string Describe(this object o) => "Describe(object)";
    public static string Describe(this string s) => "Describe(string)";
}
class Program {
    static void Main() {
        var g = new Greeter();
        Console.WriteLine($"[1] g.Hello()       : {g.Hello()}");
        Console.WriteLine($"[2] Ext.Hello(g)    : {Ext.Hello(g)}");
        string s = "x";
        object o = s;
        Console.WriteLine($"[3] s.Describe()    : {s.Describe()}");
        Console.WriteLine($"[4] o.Describe()    : {o.Describe()}  (o 의 실제 타입 = {o.GetType().Name})");
    }
}
```

- `[1]`\~`[4]` 는?

### 4. ★★★ 확장 멤버 일곱 종류 × 판 셋 (예측)

- 다음 일곱을 각각 한 파일로 만들어 선언하고 **한 번 불러 본다** — `this` 확장 메서드 · 블록의 인스턴스 메서드 · 인스턴스 속성 · 정적 메서드 · 정적 속성 · 연산자 · 인덱서.
- ★★★ `-langversion:13`·`14`·`preview` 에서 각각 **되는 칸**은? 안 되는 칸의 진단은?
- ★★ C# 13 에서 `extension` 블록을 쓰면 「이 기능은 C# 14 부터」 류 진단이 나오나?
- ★★ preview 에서 인덱서는 선언만 통과하나, 부르기까지 되나?

### 5. ★★ Java 로 `"hi".shout()` (예측)

- 같은 클래스에 `static String shout(String s)` 를 두고 `"hi".shout()` 를 부르면 javac 는?
- ★ Java 에서 같은 일을 하는 관용 형태는?

### 6. ★★★ 1번·2번의 IL 이 말하는 것 (왜)

- 1번과 2번의 IL 한 줄씩으로 「확장 메서드는 정적 메서드의 문법 설탕」을 증명하거나 반증하라.

### 7. ★★★ 3번의 `[1]`·`[4]` 가 그렇게 나온 이유 (왜)

- 3번 `[1]`·`[4]` 를 「컴파일러가 이름을 찾는 순서」와 「가상 호출이 아니다」로 설명하라.

### 8. ★★ C# 14 가 넓힌 범위와 안 넓힌 범위 (경계)

- 4번에 비추어 C# 14 에서 새로 된 것 · 여전히 안 되는 것은? 확장 속성은 IL 에서 무엇인가?

### 9. ★★ 무엇이 명세이고 무엇이 구현인가 (왜)

- 「확장 메서드 = 첫 인자가 수신자인 정적 메서드」·「인스턴스 멤버 우선」·「`<G>$…` 중첩 타입」·「인덱서가 preview」는 각각 어느 층인가?

### 10. ★★ `foreach` 와 확장 메서드 (연결)

- 확장 메서드 `GetEnumerator` 로 `int` 를 `foreach` 할 수 있나 — 몇 번 주제의 무엇과 이어지나?

### 11. 다른 주제와 잇기 (연결)

- ★★ 확장 인덱서를 먼저 던진 주제는? 그때 무엇이 나왔나?
- ★ LINQ 의 `Select`·`Where` 는 무엇으로 정의돼 있고, 그 게으름은 몇 번 주제인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
