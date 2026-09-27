# csharp/syntax/21 — 패턴 매칭 — 타입·속성·관계·목록 패턴 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> ★★★ 이 주제의 질문은 「**패턴 하나가 IL 로 무엇이 되나**」 하나로 거의 다 풀린다 — 답이 막히면 무엇을 **부르는지**(연산자·getter·인덱서)를 떠올려라.
> **환경** — .NET SDK 10.0.401 · 런타임 10.0.12 · `net10.0` · linux-x64 ·
> Roslyn `csc` 를 직접 부른다 · `-langversion:latest` · `-preferreduilang:en-US`. 대비는 **javac 21.0.5** 다.
> ★★★ **본체 창은 ① IL 덤프다.** getter·연산자 호출은 **실행 로그**로, 할당은 **2×2 판 격자**로 물었다.
> 선행 — [16번](../16-inheritance-virtual-override-abstract-sealed-new/)(상속·타입 계층) · 함께 보면 좋은 것 — [14번](../14-indexers/)(패턴 기반 인덱싱)·[19번](../19-equality-equals-gethashcode-operator/)(`==` 가 고르는 것).

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (예측) / (왜) / (경계) / (연결) -->

### 1. ★★★ 선언 패턴과 관계 패턴의 IL (예측)

```csharp
// cs21b-il.cs
using System;
public static class Probe {
    public static int Decl(object o)   => o is string s ? s.Length : -1;    // 선언 패턴
    public static bool Type(object o)  => o is string;                        // 타입 패턴
    public static bool Range(int x)    => x is >= 0 and < 10;                 // 관계 + and
    public static bool Outside(int x)  => x is < 0 or >= 10;                  // 관계 + or
    public static bool Letter(char c)  => c is not (>= 'a' and <= 'z');      // not + 괄호
}
class Program {
    static void Main() {
        Console.WriteLine($"[1] Decl(\"abc\")={Probe.Decl("abc")} Decl(42)={Probe.Decl(42)}");
        Console.WriteLine($"[2] Range(9)={Probe.Range(9)} Range(10)={Probe.Range(10)} Outside(-1)={Probe.Outside(-1)}");
        Console.WriteLine($"[3] Letter('q')={Probe.Letter('q')} Letter('Q')={Probe.Letter('Q')}");
        foreach (var n in new[] { "Decl", "Type", "Range", "Outside" }) Il.Dump(typeof(Probe), n);
    }
}
```

- `[1]`\~`[3]` 에 무엇이 찍히는가?
- ★★★ `Decl` 의 IL 에서 **캐스트에 해당하는 명령**은 몇 개이고, 그 결과는 어디로 가는가?
- ★★ `Range` 는 `x` 와 상수를 **몇 번** 비교하는가?
- ★ `Letter('Q')` 는 왜 그 값인가 — 괄호를 빼면 어떻게 묶이는가?

### 2. ★★★ 연산자를 오버로드한 타입을 null 과 견주면 (예측)

```csharp
// cs21b-null.cs
using System;
class Token {
    public static int Calls;
    public static bool operator ==(Token? a, Token? b) { Calls++; Console.WriteLine("    op_Equality 불림"); return false; }
    public static bool operator !=(Token? a, Token? b) { Calls++; Console.WriteLine("    op_Inequality 불림"); return true; }
    public override bool Equals(object? o) => ReferenceEquals(this, o);
    public override int GetHashCode() => 0;
}
static class Probe {
    public static bool IsNull(Token? t)    => t is null;
    public static bool IsNotNull(Token? t) => t is not null;
    public static bool EqNull(Token? t)    => t == null;
    public static bool NeNull(Token? t)    => t != null;
    public static bool Empty(Token? t)     => t is { };
}
class Program {
    static void Main() {
        Token? none = null;
        Console.WriteLine($"[1] none is null     : {Probe.IsNull(none)}");
        Console.WriteLine($"[2] none is not null : {Probe.IsNotNull(none)}");
        Console.WriteLine($"[3] none == null     : {Probe.EqNull(none)}");
        Console.WriteLine($"[4] none != null     : {Probe.NeNull(none)}");
        Console.WriteLine($"[5] none is {{ }}      : {Probe.Empty(none)}");
        Console.WriteLine($"    연산자 호출 횟수 = {Token.Calls}");
        foreach (var n in new[] { "IsNull", "IsNotNull", "EqNull", "NeNull", "Empty" }) Il.Dump(typeof(Probe), n);
    }
}
```

- `[1]`\~`[5]` 에 무엇이 찍히고, **`op_…` 불림** 로그는 어느 줄 앞에 나오는가?
- ★★★ `[3]` 은 null 을 null 과 비교했다 — 결과는?
- ★★ `IsNotNull` 과 `Empty` 의 IL 은 어떻게 다른가?

### 3. ★★ 속성 패턴과 위치 패턴이 부르는 횟수 (예측)

```csharp
// cs21b-getter.cs
using System;
class Word {
    public static int Reads;
    readonly string s;
    public Word(string s) => this.s = s;
    public int Len { get { Reads++; return s.Length; } }
}
class Pt {
    public static int Calls;
    public int X, Y;
    public Pt(int x, int y) { X = x; Y = y; }
    public void Deconstruct(out int x, out int y) { Calls++; x = X; y = Y; }
}
class Program {
    static void Main() {
        var w = new Word("pattern");
        Word.Reads = 0; bool a = w.Len > 3 && w.Len < 9;
        Console.WriteLine($"[1] &&                   : {a}  get_Len {Word.Reads}회");
        Word.Reads = 0; bool b = w is { Len: > 3 } and { Len: < 9 };
        Console.WriteLine($"[2] and                  : {b}  get_Len {Word.Reads}회");
        Word.Reads = 0; bool c = w is { Len: > 3 and < 9 };
        Console.WriteLine($"[3] {{ Len: > 3 and < 9 }} : {c}  get_Len {Word.Reads}회");
        Word.Reads = 0;
        int d = w switch { { Len: > 10 } => 3, { Len: > 5 } => 2, { Len: > 0 } => 1, _ => 0 };
        Console.WriteLine($"[4] switch 팔 넷          : {d}  get_Len {Word.Reads}회");
        var p = new Pt(1, 5);
        int e = p switch { (0, 0) => 0, (1, 1) => 1, (1, var y) => y, _ => -1 };
        Console.WriteLine($"[5] 위치 패턴 팔 넷        : {e}  Deconstruct {Pt.Calls}회");
    }
}
```

- `[1]`\~`[5]` 의 호출 횟수는 각각?
- ★★★ `[4]` 의 `switch` 식은 팔이 넷인데 `get_Len` 을 팔마다 부르는가?
- ★★ `csc -optimize` 로 바꾸면 횟수가 바뀌는가?

### 4. ★★★ 목록 패턴 — 배열·`List`·내 타입 (예측)

```csharp
// cs21b-list.cs
using System;
using System.Collections.Generic;
public class Bag {                                   // Length 와 this[int] 만 있다 — 인터페이스 없음
    readonly int[] items;
    public Bag(params int[] xs) => items = xs;
    public int Length => items.Length;
    public int this[int i] => items[i];
}
public static class Probe {
    public static int Arr(int[] a)       => a is [1, .., var last] ? last : -1;
    public static int Lst(List<int> a)   => a is [1, .., var last] ? last : -1;
    public static int Own(Bag b)         => b is [1, .., var last] ? last : -1;
    public static int[] Rest(int[] a)    => a is [_, .. var rest] ? rest : a;
}
class Program {
    static void Main() {
        Console.WriteLine($"[1] {Probe.Arr(new[] { 1, 2, 3 })} {Probe.Arr(new[] { 1 })} {Probe.Arr(new[] { 2, 3 })}");
        Console.WriteLine($"[2] {Probe.Lst(new List<int> { 1, 5 })} {Probe.Own(new Bag(1, 7))}");
        Console.WriteLine($"[3] [{string.Join(",", Probe.Rest(new[] { 9, 8, 7 }))}]");
        foreach (var n in new[] { "Arr", "Lst", "Own", "Rest" }) Il.Dump(typeof(Probe), n);
    }
}
```

- `[1]`\~`[3]` 에 무엇이 찍히는가?
- ★★★ 세 메서드(`Arr`·`Lst`·`Own`)가 **길이를 읽는 명령**은 각각 무엇인가? `Bag` 은 인터페이스를 하나도 구현하지 않았다 — 컴파일되는가?
- ★★ `last` 를 꺼내려고 IL 은 인덱스를 어떻게 구하는가 — `System.Index` 가 나타나는가?
- ★★ `Rest` 의 IL 에는 무엇이 새로 나타나는가?

### 5. ★★ 목록 패턴 다섯 줄의 할당 바이트 (예측)

```csharp
// cs21b-alloc.cs
using System;
class Program {
    static long M(Action a) {
        for (int i = 0; i < 200; i++) a();                // 데운다
        var b = GC.GetAllocatedBytesForCurrentThread();
        a();
        return GC.GetAllocatedBytesForCurrentThread() - b;
    }
    static void Main() {
        int[] arr = { 1, 2, 3, 4, 5, 6, 7, 8 };
        string str = "abcdefgh";
        object boxed = 42;
        long sink = 0;
        Console.WriteLine($"[1] arr is [1, .., var last]     1000번 : {M(() => { for (int i = 0; i < 1000; i++) if (arr is [1, .., var last]) sink += last; })} 바이트");
        Console.WriteLine($"[2] arr is [_, .. var rest]      1000번 : {M(() => { for (int i = 0; i < 1000; i++) if (arr is [_, .. var rest]) sink += rest.Length; })} 바이트");
        Console.WriteLine($"[3] span is [_, .. var rest]     1000번 : {M(() => { for (int i = 0; i < 1000; i++) { ReadOnlySpan<int> sp = arr; if (sp is [_, .. var rest]) sink += rest.Length; } })} 바이트");
        Console.WriteLine($"[4] str is [_, .. var rest]      1000번 : {M(() => { for (int i = 0; i < 1000; i++) if (str is [_, .. var rest]) sink += rest.Length; })} 바이트");
        Console.WriteLine($"[5] boxed is int n               1000번 : {M(() => { for (int i = 0; i < 1000; i++) if (boxed is int n) sink += n; })} 바이트");
        GC.KeepAlive(sink);
    }
}
```

- 다섯 줄 중 **0 이 아닌** 줄은 어느 것인가?
- ★★★ `[2]` 와 `[3]` 은 같은 패턴인데 무엇이 갈랐나?
- ★ 네 판(`csc` 기본/`-optimize` × 티어링 기본/`TieredCompilation=0`)에서 갈린 줄은 몇 개인가?

### 6. ★★ 이름 하나를 패턴 자리에 적으면 (예측)

```csharp
// cs21b-const.cs
using System;
class Program {
    const int Limit = 5;
    static string A(int x) => x switch { Limit => "첫 팔", var n => $"둘째 팔 n={n}" };
    static void Main() {
        Console.WriteLine($"[1] A(5) = {A(5)}");
        Console.WriteLine($"[2] A(7) = {A(7)}");
    }
}
```

```csharp
// cs21b-capture.cs
class Program {
    static string B(int x) => x switch { limit => "첫 팔", _ => "둘째 팔" };   // 선언된 적 없는 이름
    static void Main() { }
}
```

- `A(5)` · `A(7)` 은 무엇을 돌려주는가 — `Limit` 은 새 변수인가?
- ★★★ 둘째 소스는 컴파일되는가 — 된다면 `limit` 에 무엇이 담기는가?

### 7. ★★ 목록 패턴이 거절되는 자리 (경계)

- `IEnumerable<int>` 에 `[1, ..]` 을 쓰면? 진단 코드는?
- ★★ `Count` 만 있고 인덱서가 없는 타입이면?
- ★ 슬라이스 `..` 를 두 번 쓰면? · `o is List<int> [1, ..]` 처럼 **타입 바로 뒤에** 쓰면?

### 8. ★★ 판 경계를 기억 말고 컴파일러에게 묻기 (왜)

- 한 파일을 `-langversion:7.3`·`8`·`9`·`10`·`11` 로 던지면 진단 줄 수는 어떻게 줄어드는가?
- ★★★ 속성 패턴·관계 패턴·`or`/`not`·확장 속성 패턴·목록 패턴의 요구 판은 각각 몇인가 — **진단의 어느 부분**이 그것을 말하는가?
- ★ `switch` 식 팔에 `Box => 1` 처럼 **타입 이름만** 적는 것은 몇 판부터인가?

### 9. ★★★ getter 가 한 번만 불린 것은 약속인가 (왜)

- 3번의 「1회」는 **어느 층**의 사실인가 — 명세는 무엇이라고 하는가?
- ★★ 그렇다면 **어떤 속성을 패턴에 넣으면 안 되는가**?
- ★ `&&` 로 쓴 `[1]` 의 2회는 왜 명세가 보장하는가?

### 10. ★★ Java·Kotlin·Python 의 패턴과 (경계)

- Java 21 에 있는 C# 패턴의 짝은? **Java 에 없는 C# 패턴**은?
- ★★ Kotlin `is` 와 C# `is T x` 는 무엇이 다른가?
- ★★★ Python `match` 의 `case red:` 와 C# 의 6번 둘째 소스는 왜 정반대로 동작하는가?

### 11. 다른 주제와 잇기 (연결)

- ★★ 목록 패턴이 따르는 **패턴 기반 인덱싱**의 정본은 몇 번 주제인가?
- ★★ 위치 패턴이 부르는 `Deconstruct` 를 **자동 생성**하는 주제는?
- ★★ 2번의 `!= null` 이 연산자를 고르는 규칙의 정본은?
- ★ **팔 여럿의 완전성·도달 불가**는 이 목록의 몇 번 주제인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
