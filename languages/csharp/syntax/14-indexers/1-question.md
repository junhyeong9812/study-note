# csharp/syntax/14 — 인덱서 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> **환경** — .NET SDK 10.0.401 · 런타임 10.0.12 · `net10.0` · linux-x64 ·
> Roslyn `csc` 를 직접 부른다 · `-langversion:latest`(확장 인덱서만 `preview` 로도) · `-preferreduilang:en-US`.
> ★★★ **본체 창은 ③ 리플렉션이다** — 인덱서의 IL 본문은 평범한 배열 접근이라 볼 것이 없고,
> 갈리는 것은 **이름(`Item`)과 타입에 붙는 `DefaultMemberAttribute`** 다.
> ★★ **① IL 덤프는 5번에서만 본체가 된다** — `^1` 이 **두 갈래로** 풀린다.
> ★★ **④ 할당 바이트는 이 주제에서 쓴다**(9번) — 다만 **한 판의 절댓값은 근거가 아니므로**
> `csc -optimize` × `DOTNET_TieredCompilation` **2×2 판 격자**를 돌려 「움직인 칸」을 세었다.
> ★★★ **이 파일에는 시간을 잰 문장이 없다** — 「인덱서 호출이 메서드보다 느리다」는 **안 쟀다.**
> 선행 — [13번](../13-properties-init-required-field/)(**한 사슬이다** — 인덱서는 인자를 받는 속성이다)·[03번](../03-boxing-and-unboxing/)(박싱).
> 이어지는 것 — [16번](../16-inheritance-virtual-override-abstract-sealed-new/)(명시적 인터페이스 구현이 `private` 인 것).
> 대비 — 파이썬 갈래 목록([`python/syntax/README.md`](../../../python/syntax/README.md))의 **32번**([`32-container-protocol/`](../../../python/syntax/32-container-protocol/)).

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (예측) / (왜) / (경계) / (연결) -->

### 1. ★★★ 인덱서 하나가 만든 것을 전부 적을 수 있나 (예측)

```csharp
// cs14b-basic.cs
using System;
using System.Reflection;

public class Row {
    readonly string[] cells = { "가", "나", "다" };
    public string this[int i] { get => cells[i]; set => cells[i] = value; }
}

class Program {
    static void Main() {
        var r = new Row();
        r[1] = "바뀜";
        Console.WriteLine(r[1]);
        foreach (var a in typeof(Row).GetCustomAttributes(false))
            Console.WriteLine($"타입 어트리뷰트 {a}");
        foreach (var p in typeof(Row).GetProperties())
            Console.WriteLine($"속성   이름={p.Name} 인자={p.GetIndexParameters().Length}");
        foreach (var m in typeof(Row).GetMethods(BindingFlags.Public|BindingFlags.Instance|BindingFlags.DeclaredOnly))
            Console.WriteLine($"메서드 {m.Name}");
        var da = (DefaultMemberAttribute)typeof(Row).GetCustomAttributes(typeof(DefaultMemberAttribute), false)[0];
        Console.WriteLine($"DefaultMember = {da.MemberName}");
    }
}
```

- **메서드 이름**이 무엇으로 찍히는가?
- ★★★ **타입에 어트리뷰트가 붙는가** — 내가 안 적었는데?
- ★★ 속성 목록에 무엇이 나오고 **인자 개수**는 몇인가?
- ★ 속성과 인덱서를 가르는 **유일한 칸**은 무엇인가?

### 2. ★★ `[IndexerName("Cell")]` 을 붙이면 무엇이 달라지나 (예측)

```csharp
// cs14b-name.cs
using System;
using System.Reflection;
using System.Runtime.CompilerServices;

public class Grid2 {
    readonly int[,] m = new int[2, 2];
    [IndexerName("Cell")]
    public int this[int r, int c] { get => m[r, c]; set => m[r, c] = value; }
}
class Program {
    static void Main() {
        var g = new Grid2();
        g[1, 1] = 5;
        Console.WriteLine($"g[1,1]={g[1,1]}");
        var da = (DefaultMemberAttribute)typeof(Grid2).GetCustomAttributes(typeof(DefaultMemberAttribute), false)[0];
        Console.WriteLine($"DefaultMember = {da.MemberName}");
        foreach (var p in typeof(Grid2).GetProperties())
            Console.WriteLine($"속성   이름={p.Name} 인자={p.GetIndexParameters().Length}");
        foreach (var mm in typeof(Grid2).GetMethods(BindingFlags.Public|BindingFlags.Instance|BindingFlags.DeclaredOnly))
            Console.WriteLine($"메서드 {mm.Name}");
        Console.WriteLine($"GetProperty(\"Item\") -> {(typeof(Grid2).GetProperty("Item") is null ? "없음" : "있음")}");
        Console.WriteLine($"GetProperty(\"Cell\") -> {(typeof(Grid2).GetProperty("Cell") is null ? "없음" : "있음")}");
    }
}
```

- **메서드 이름**과 **`DefaultMember`** 는 각각 무엇으로 찍히는가?
- ★★★ `GetProperty("Item")` 은 **있음인가 없음인가**?
- ★★ **소스에서 `g[1,1]` 로 쓰는 것**은 바뀌는가?
- ★ 그래서 이 어트리뷰트는 **누구를 위한 것**인가?

### 3. ★ 인덱서 다섯이 각각 어디로 가나 (예측)

```csharp
// cs14b-overload.cs
using System;
class Roster {
    readonly string[] names = { "가", "나", "다" };
    public string this[int position] => $"int 으로 왔다 — {names[position]}";
    public string this[string key]   => $"string 으로 왔다 — {key}";
    public string this[int a, int b] => $"둘로 왔다 — {a},{b}";
    public string this[Index i]      => $"Index 로 왔다 — {names[i]}";
    public string this[Range r]      => $"Range 로 왔다 — {r}";
}
class Program {
    static void Main() {
        var r = new Roster();
        Console.WriteLine(r[0]);
        Console.WriteLine(r["문자"]);
        Console.WriteLine(r[1, 2]);
        Console.WriteLine(r[^1]);
        Console.WriteLine(r[0..2]);
    }
}
```

- 다섯 줄이 각각 **어느 인덱서**로 가는가?
- ★★★ `r[^1]` 과 `r[0..2]` 는 **무슨 타입의 값**을 만드는가?
- ★★ 인자 타입이 **같은** 인덱서 둘을 두면 어떻게 되는가 — 매개변수 이름을 다르게 지으면?

### 4. ★★★ `^1` 은 IL 로 무엇이 되나 — 두 클래스에서 (예측)

```csharp
// cs14b-il.cs
using System;

public class Explicit {                                  // this[Index] 를 직접 선언
    readonly int[] items = { 1, 2, 3, 4, 5 };
    public int this[Index i] => items[i];
}
public class Pattern {                                   // Length + this[int] 만 있다
    readonly int[] items = { 1, 2, 3, 4, 5 };
    public int Length => items.Length;
    public int this[int i] => items[i];
}
public static class Probe {
    public static int FromExplicit(Explicit e) => e[^1];
    public static int FromPattern(Pattern p)   => p[^1];
}
class Program {
    static void Main() {
        Il.Dump(typeof(Probe), "FromExplicit");
        Il.Dump(typeof(Probe), "FromPattern");
    }
}
```

- ★★★ `Explicit`(`this[Index]` 를 선언함) 쪽과 `Pattern`(안 선언함) 쪽의 IL 이 **같은가 다른가**?
- ★★ `Pattern` 쪽에 **`dup` 과 `sub`** 가 나오는 이유는 무엇인가?
- ★ `Pattern` 은 **인터페이스를 하나도 구현하지 않았는데** 왜 `^1` 이 붙는가?

### 5. ★★ C# 14 확장 멤버로 인덱서를 붙일 수 있나 (예측)

```csharp
// cs14b-ext.cs
using System;
public static class Ext {
    extension(int[] a) {                                   // C# 14 확장 멤버
        public int Second => a[1];
        public int this[string name] => name == "first" ? a[0] : a[^1];
    }
    extension(int[]) {
        public static int[] Empty => Array.Empty<int>();
        public static int this[char c] => (int)c;
    }
}
class Program { static void Main() { } }
```

- `-langversion:latest` 에서 **에러가 몇 건** 나고 코드는 무엇인가?
- ★★★ `-langversion:preview` 로 바꾸면 **몇 건이 사라지고 몇 건이 남는가**?
- ★★ 남은 두 코드는 각각 무엇을 말하는가 — **「다음 판을 기다리라」와 「원리상 안 된다」** 중 어느 쪽인가?
- ★★★ preview 에서 선언이 통과한 인스턴스 확장 인덱서를 **실제로 호출하면** 어떻게 되는가?

### 6. ★★ 인덱서 셋의 할당 바이트는 얼마인가 (예측)

```csharp
// cs14b-alloc.cs
using System;

class Dict {
    readonly int[] cells = { 10, 20, 30 };
    public int this[int i]      => cells[i];
    public int this[object key] => cells[(int)key];
    public int Get(int i)       => cells[i];
}

class Program {
    static long M(Action a) {
        a();                                             // 한 판 데워 놓고
        var b = GC.GetAllocatedBytesForCurrentThread();
        a();
        return GC.GetAllocatedBytesForCurrentThread() - b;
    }
    static void Main() {
        var d = new Dict();
        int sink = 0;
        Console.WriteLine($"this[int]    1000회 : {M(() => { for (int i = 0; i < 1000; i++) sink += d[1]; })} 바이트");
        Console.WriteLine($"this[object] 1000회 : {M(() => { for (int i = 0; i < 1000; i++) sink += d[(object)1]; })} 바이트");
        Console.WriteLine($"Get(int)     1000회 : {M(() => { for (int i = 0; i < 1000; i++) sink += d.Get(1); })} 바이트");
        Console.WriteLine($"(합 {sink})");
    }
}
```

- 세 줄에 각각 **몇 바이트**가 찍히는가?
- ★★★ 0 이 아닌 칸은 **왜** 0 이 아닌가 — 인덱서라서인가, 인자 타입 때문인가?
- ★★ `csc -optimize` × `DOTNET_TieredCompilation` **2×2** 를 돌리면 **몇 칸이 움직이는가**?
- ★ 이 수치를 **근거로 써도 되는 이유**는 무엇인가?

### 7. ★ 인덱서는 `static` 이 되나 (경계)

- `public static int this[int i]` 를 쓰면 **진단 코드**는 무엇인가?
- ★★ 그것이 **구현의 한계**인가 **문법 수준의 제약**인가 — 왜 그렇게 말할 수 있는가?
- ★ C# 14 확장 멤버로 **정적 인덱서**를 만들면 어떻게 되는가?

### 8. ★ 명시적 인터페이스 구현 인덱서 (경계)

- 명시적으로 구현한 인덱서는 **`private` 인가**?
- ★★ `DefaultMemberAttribute` 는 **인터페이스에 붙는가 클래스에 붙는가** — 왜 그런가?
- ★ 그 인덱서를 부르려면 무엇이 필요한가?

### 9. ★★★ 언제 인덱서 대신 메서드가 나은가 (왜)

- **실패 사례 넷**을 각각 진단 코드나 수치와 함께 댈 수 있는가?
- ★★★ 같은 `int` 로 **뜻이 다른 두 조회**를 인덱서로 만들 수 있는가?
- ★★ 인덱서가 비싸거나 부작용이 있으면 왜 나쁜가 — **읽는 사람의 기대**로 답하라.
- ★ 인자가 **셋 이상**이면 왜 메서드가 나은가?

### 10. 다른 주제와 잇기 (연결)

- ★★★ 이 주제가 **13번과 한 사슬인 이유**는 무엇인가 — 공통점을 한 문장으로.
- **박싱 24바이트**의 정본은 몇 번 주제인가?
- ★★ **명시적 인터페이스 구현이 `private` 인 것**의 정본은 몇 번 주제인가?
- **인덱스 초기화 구문**과 **컬렉션 식**은 몇 번 주제인가 — 둘은 같은 기능인가?
- **`^`·`..` 연산자 자체**는 몇 번 주제인가?
- ★ 파이썬의 `__getitem__` 과 C# 인덱서가 갈리는 **한 칸**은 무엇인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
