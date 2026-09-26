# csharp/syntax/28 — 람다식과 클로저 캡처 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> ★★★ 이 주제의 질문은 「**캡처된 변수는 힙 객체의 필드가 된다 — 그 객체는 범위마다 하나다**」 한 줄로 거의 다 풀린다. **몇 개의 객체가 언제 생기나**를 세라.
> **환경** — .NET SDK 10.0.401 · 런타임 10.0.12 · `net10.0` · linux-x64 ·
> Roslyn `csc` 를 직접 부른다 · `-langversion:latest`(판 격자 문항만 판을 바꾼다) · `-preferreduilang:en-US`. 대비는 **javac 21.0.5** 다.
> ★★★ **본체 창은 ① IL 덤프와 ③ 리플렉션이다.** 수명은 **`WeakReference` 의 「회수됐나」** 로 물었다(2×2 판 격자).
> 선행 — [27번](../27-delegates-and-func-action/)(델리게이트 — `Target` 과 `<>c` 캐시).

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (예측) / (왜) / (경계) / (연결) -->

### 1. ★★★ 캡처하는 람다 · 안 하는 람다 · `static` 람다를 열어 보면 (예측)

```csharp
// cs28b-il.cs
using System;
using System.Linq;
using System.Reflection;
public static class Probe {
    public static Func<int> Capture() {
        int n = 10;
        Func<int> f = () => n;
        n = 20;
        return f;
    }
    public static Func<int, int> NoCapture() => x => x + 1;
    public static Func<int, int> StaticLambda() => static x => x + 1;
}
class Program {
    const BindingFlags All = BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Static | BindingFlags.Instance | BindingFlags.DeclaredOnly;
    static void Main() {
        Console.WriteLine($"[0] Probe.Capture()() = {Probe.Capture()()}");
        foreach (var n in new[] { "Capture", "NoCapture", "StaticLambda" }) Il.Dump(typeof(Probe), n);
        foreach (var t in typeof(Probe).GetNestedTypes(BindingFlags.NonPublic).OrderBy(t => t.Name, StringComparer.Ordinal)) {
            Console.WriteLine($"=== 컴파일러가 만든 타입 {t.Name} (sealed={t.IsSealed})");
            foreach (var f in t.GetFields(All).OrderBy(f => f.Name, StringComparer.Ordinal))
                Console.WriteLine($"    필드   {(f.IsStatic ? "static " : "")}{f.FieldType.Name} {f.Name}");
            foreach (var m in t.GetMethods(All).OrderBy(m => m.Name, StringComparer.Ordinal)) {
                Console.WriteLine($"    메서드 {(m.IsStatic ? "static " : "")}{m.Name}");
                Il.Dump(t, m.Name);
            }
        }
    }
}
```

- `[0]` 은 `10` 인가 `20` 인가?
- ★★★ `Capture` 의 IL 첫 명령은? `n = 10`·`n = 20` 은 어떤 명령이 되나?
- ★★★ 컴파일러가 만든 타입은 몇 개이고, 각각 어떤 필드·메서드를 갖나?
- ★★ `NoCapture` 와 `StaticLambda` 의 IL 은 다른가?

### 2. ★★ `static` 람다 다섯 개 (예측)

```csharp
// cs28b-static.cs
using System;
class Program {
    int field = 1;
    const int K = 5;
    static int S = 2;
    void M() {
        int local = 3;
        Func<int> a = static () => local;
        Func<int> b = static () => field;
        Func<int> c = static () => this.field;
        Func<int> d = static () => K + S;
        Func<int, int> e = static x => x * K;
    }
    static void Main() { }
}
```

- 다섯 람다 중 **진단이 나는 것**과 그 코드는?
- ★ `-langversion:8` 로 던지면 무엇이 더해지나?

### 3. ★★★ 루프 셋에서 만든 람다를 나중에 부르면 — 판 넷으로 (예측)

```csharp
// cs28b-loop.cs
using System;
using System.Collections.Generic;
class Program {
    static string Run(List<Func<int>> fs) { string s = ""; foreach (var f in fs) s += f() + " "; return s.TrimEnd(); }
    static void Main() {
        var a = new List<Func<int>>();
        for (int i = 0; i < 3; i++) a.Add(delegate { return i; });
        var b = new List<Func<int>>();
        foreach (int j in new int[] { 0, 1, 2 }) b.Add(delegate { return j; });
        var c = new List<Func<int>>();
        IEnumerator<int> e = ((IEnumerable<int>)new int[] { 0, 1, 2 }).GetEnumerator();
        int k;
        while (e.MoveNext()) { k = e.Current; c.Add(delegate { return k; }); }
        Console.WriteLine("for=" + Run(a) + ";foreach=" + Run(b) + ";hand=" + Run(c));
    }
}
```

- `for` · `foreach` · `hand` 는 각각 무엇을 찍나?
- ★★★ `-langversion:3`·`4`(C# 5 이전)로 던지면 `foreach` 칸이 바뀌나?
- ★★ `hand` 와 `for` 는 같은 숫자인가?

### 4. ★★★ 람다를 붙들면 무엇이 안 풀리나 (예측)

```csharp
// cs28b-life.cs
using System;
using System.Runtime.CompilerServices;
class Program {
    static Func<int>? keep;
    [MethodImpl(MethodImplOptions.NoInlining)]
    static WeakReference Make(bool hold) {
        var big = new byte[10_000_000];
        Func<int> f = () => big.Length;
        if (hold) keep = f;
        return new WeakReference(big);
    }
    [MethodImpl(MethodImplOptions.NoInlining)]
    static WeakReference MakeSibling() {
        var big = new byte[10_000_000];
        int small = 1;
        Func<int> usesBig = () => big.Length;
        Func<int> usesSmall = () => small;
        keep = usesSmall;
        return new WeakReference(big);
    }
    static bool Collected(WeakReference w) { GC.Collect(); GC.WaitForPendingFinalizers(); GC.Collect(); return !w.IsAlive; }
    static void Main() {
        var w1 = Make(hold: true);
        Console.WriteLine($"[1] 람다를 정적 필드에 둔 채 GC · big 회수됐나 : {Collected(w1)}");
        keep = null;
        Console.WriteLine($"[2] 정적 필드를 비운 뒤 GC · big 회수됐나     : {Collected(w1)}");
        var w2 = Make(hold: false);
        Console.WriteLine($"[3] 람다를 어디에도 안 둔 경우 GC · big 회수됐나 : {Collected(w2)}");
        var w3 = MakeSibling();
        Console.WriteLine($"[4] usesSmall 만 정적 필드에 둔 채 GC · big 회수됐나 : {Collected(w3)}");
        keep = null;
        Console.WriteLine($"[5] 그것도 비운 뒤 GC · big 회수됐나           : {Collected(w3)}");
    }
}
```

- `[1]`\~`[5]` 는 각각 `True` 인가 `False` 인가?
- ★★★ `[4]` — `usesSmall` 은 `big` 을 읽지 않는다. 그래도?
- ★ 네 판(2×2)에서 갈리는 줄이 있는가?

### 5. ★★★ 캡처한 변수를 바깥에서 · 람다 안에서 고치면 (예측)

```csharp
// cs28b-mut.cs
using System;
class Program {
    static void Main() {
        int count = 1;
        Func<int> read = () => count;
        Action bump = () => count += 100;
        Console.WriteLine($"[1] read() = {read()}");
        count = 2;
        Console.WriteLine($"[2] count = 2 뒤 read() = {read()}");
        bump();
        Console.WriteLine($"[3] bump() 뒤 count = {count} · read() = {read()}");
    }
}
```

- `[1]`\~`[3]` 은?
- ★★★ 같은 모양을 Java 로 적으면(캡처 뒤 대입 · 람다 안 `count += 100`) javac 는?

### 6. ★★ 할당 바이트 — 캡처 · 캡처 없음 · `static` (예측)

```csharp
// cs28b-alloc.cs
using System;
class Program {
    static int Use(Func<int, int> f) => f(1);
    static long M(Action a) {
        for (int i = 0; i < 200; i++) a();
        var b = GC.GetAllocatedBytesForCurrentThread();
        a();
        return GC.GetAllocatedBytesForCurrentThread() - b;
    }
    static void Main() {
        long sink = 0;
        Console.WriteLine($"[1] 캡처하는 람다  Use(x => x + i)       1000번 : {M(() => { for (int i = 0; i < 1000; i++) sink += Use(x => x + i); })} 바이트");
        Console.WriteLine($"[2] 캡처 없는 람다 Use(x => x + 1)       1000번 : {M(() => { for (int i = 0; i < 1000; i++) sink += Use(x => x + 1); })} 바이트");
        Console.WriteLine($"[3] static 람다    Use(static x => x + 1) 1000번 : {M(() => { for (int i = 0; i < 1000; i++) sink += Use(static x => x + 1); })} 바이트");
        GC.KeepAlive(sink);
    }
}
```

- 세 줄의 바이트는? `[2]` 와 `[3]` 은 다른가?
- ★★ `[1]` 의 끝자리가 1000 의 배수가 아니라면 무엇 때문인가?

### 7. ★★★ `for` 와 `foreach` 의 IL 은 어디가 다른가 (경계)

- 3번의 결과를 **`newobj <>c__DisplayClass` 의 위치** 한 가지로 설명하라.

### 8. ★★★ 무엇이 명세이고 무엇이 구현인가 (왜)

- 「값이 아니라 변수를 캡처한다」·「디스플레이 클래스가 생긴다」·「형제 람다가 큰 객체를 붙든다」는 각각 어느 층인가?
- ★★ C# 5 의 `foreach` 변화를 `-langversion` 판 격자로 보일 수 없었던 이유는?

### 9. ★★ `static` 람다를 왜 쓰나 (경계)

- 1번·6번에 비추어 `static` 람다의 이득은 **성능**인가 **다른 것**인가?

### 10. ★★ 반복 변수 함정 — 다른 언어와 (경계)

- C# 의 `for`·`foreach`·옛 `foreach` 는 Go(1.21 대 1.22)·JS(`var` 대 `let`)·Python 의 어느 숫자와 같은가?
- ★ Go 가 한 빌드 안에서 두 의미를 냈던 방법을 C# 은 왜 못 쓰나?

### 11. 다른 주제와 잇기 (연결)

- ★★ 「람다」라는 개념 자체의 정본은 어디이고, 그 절에 캡처가 있나?
- ★ 이벤트 구독 해제 누락 누수는 이 주제의 어느 절과 같은 뿌리인가 — 몇 번 주제인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
