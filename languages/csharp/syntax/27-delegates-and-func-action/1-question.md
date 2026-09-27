# csharp/syntax/27 — 델리게이트와 `Func`/`Action` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> ★★★ 이 주제의 질문은 「**델리게이트는 대상 + 메서드 포인터를 든 봉인 클래스다**」 한 줄로 거의 다 풀린다 — **클래스이니 이름이 곧 타입**이고, **대상이 없으면(정적) 캐시할 수 있다.**
> **환경** — .NET SDK 10.0.401 · 런타임 10.0.12 · `net10.0` · linux-x64 ·
> Roslyn `csc` 를 직접 부른다 · `-langversion:latest`(판 격자 문항만 `10`·`11`) · `-preferreduilang:en-US`. 대비는 **javac 21.0.5** 다.
> ★★★ **본체 창은 ③ 리플렉션이다.** 할당 바이트는 **`-langversion:10` 대 `11` × 2×2 = 8판**으로 쟀다.
> 선행 — [24번](../24-generics-and-type-parameters/)(제네릭 — `Func<T, TResult>` 도 제네릭 타입이다).

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (예측) / (왜) / (경계) / (연결) -->

### 1. ★★★ 내 델리게이트와 `Func<int,int>` 를 리플렉션으로 (예측)

```csharp
// cs27b-refl.cs
using System;
using System.Linq;
using System.Reflection;
delegate int Op(int x);
class Program {
    static string Members(Type t) => string.Join(" ", t.GetMethods(BindingFlags.Public | BindingFlags.Instance | BindingFlags.DeclaredOnly).Select(m => m.Name).OrderBy(n => n, StringComparer.Ordinal))
        + " | ctor(" + string.Join(",", t.GetConstructors()[0].GetParameters().Select(p => p.ParameterType.Name)) + ")";
    static void Main() {
        foreach (var t in new[] { typeof(Op), typeof(Func<int, int>) }) {
            Console.WriteLine($"[A] {t.Name,-8} IsClass={t.IsClass} IsSealed={t.IsSealed} BaseType={t.BaseType!.FullName}");
            Console.WriteLine($"    선언한 공개 메서드 : {Members(t)}");
            var inv = t.GetMethod("Invoke")!;
            Console.WriteLine($"    Invoke 서명 : {inv.ReturnType.Name} Invoke({string.Join(",", inv.GetParameters().Select(p => p.ParameterType.Name))})");
        }
        Console.WriteLine($"[B] typeof(Op) == typeof(Func<int,int>) : {typeof(Op) == typeof(Func<int, int>)}");
        Console.WriteLine($"[C] Func<int,int> 를 Op 자리에 넣을 수 있나(IsAssignableFrom) : {typeof(Op).IsAssignableFrom(typeof(Func<int, int>))}");
        Op op = x => x + 1;
        Console.WriteLine($"[D] op.Method.Name = {op.Method.Name} · op.Target 의 타입 = {op.Target?.GetType().Name}");
    }
}
```

- `[A]` 두 타입의 `IsClass`·`IsSealed`·`BaseType` 과 선언된 공개 메서드는?
- ★★★ `Invoke` 서명이 같다면 `[B]`·`[C]` 는?
- ★★ `[D]` 람다를 담은 델리게이트의 `Target` 은 무엇인가?

### 2. ★★★ 서명이 같은 두 델리게이트 타입 사이 (예측)

```csharp
// cs27b-type.cs
using System;
delegate int Op(int x);
class Program {
    static void Main() {
        Func<int, int> f = x => x * 10;
        Op a = f;
        Op b = (Op)f;
    }
}
```

```csharp
// cs27b-bridge.cs
using System;
delegate int Op(int x);
class Program {
    static void Main() {
        Func<int, int> f = x => x * 10;
        Op a = f.Invoke;
        Op b = new Op(f);
        Console.WriteLine($"[1] a(2) = {a(2)} · b(2) = {b(2)}");
        Console.WriteLine($"[2] a.Method.Name = {a.Method.Name} · a.Target 의 타입 = {a.Target?.GetType().Name}");
        Console.WriteLine($"[3] b.Method.Name = {b.Method.Name} · b.Target 의 타입 = {b.Target?.GetType().Name}");
        Console.WriteLine($"[4] ReferenceEquals(a.Target, f) = {ReferenceEquals(a.Target, f)}");
    }
}
```

- 첫 소스의 두 줄은 각각 어떤 진단인가?
- ★★ 둘째 소스의 `[1]`\~`[4]` 는 — `a` 의 `Method` 와 `Target` 은 무엇인가?

### 3. ★★★ 호출 목록 셋을 부르고 떼면 (예측)

```csharp
// cs27b-multi.cs
using System;
class Program {
    static int A() { Console.WriteLine("  A 실행"); return 1; }
    static int B() { Console.WriteLine("  B 실행"); return 2; }
    static int C() { Console.WriteLine("  C 실행"); return 3; }
    static int Boom() { Console.WriteLine("  Boom 실행"); throw new InvalidOperationException("boom"); }
    static string Names(Delegate? d) => d is null ? "(null)" : string.Join(",", Array.ConvertAll(d.GetInvocationList(), x => x.Method.Name));
    static void Main() {
        Func<int> f = A; f += B; f += C;
        Console.WriteLine($"[1] 호출 목록 : {Names(f)}");
        int r = f();
        Console.WriteLine($"[2] f() 의 반환값 : {r}");
        Func<int> g = A; g += Boom; g += C;
        Console.WriteLine($"[3] 호출 목록 : {Names(g)}");
        try { g(); } catch (Exception e) { Console.WriteLine($"[4] g() → {e.GetType().Name}: {e.Message}"); }
        Func<int> h = A; h += B; h += A;
        Console.WriteLine($"[5] 떼기 전 : {Names(h)}");
        h -= A;
        Console.WriteLine($"[6] h -= A 뒤 : {Names(h)}");
        Func<int> k = A; k += B; k += C;
        Func<int> bc = B; bc += C;
        Func<int> ac = A; ac += C;
        Console.WriteLine($"[7] (A,B,C) -= (B,C) : {Names(k - bc)}");
        Console.WriteLine($"[8] (A,B,C) -= (A,C) : {Names(k - ac)}");
        Func<int> one = A; one -= A;
        Console.WriteLine($"[9] A -= A : {Names(one)}");
    }
}
```

- `[2]` 의 반환값은? `[3]`\~`[4]` 에서 `C 실행` 은 찍히는가?
- ★★★ `[6]`\~`[9]` 는?
- ★ 컴파일러가 경고를 내는 줄이 있는가?

### 4. ★★★ 메서드 그룹 · 인스턴스 메서드 그룹 · 람다의 IL을 두 판으로 (예측)

```csharp
// cs27b-il.cs
using System;
public class P {
    static int Twice(int x) => x * 2;
    int Inc(int x) => x + 1;
    public static Func<int, int> Static() => Twice;
    public Func<int, int> Instance() => Inc;
    public static Func<int, int> Lambda() => x => x * 2;
    public static int Call(Func<int, int> f) => f(3);
}
class Program {
    static void Main() {
        foreach (var n in new[] { "Static", "Instance", "Lambda", "Call" }) Il.Dump(typeof(P), n);
    }
}
```

- `-langversion:10` 과 `11` 에서 **달라지는 메서드**는 넷 중 어느 것인가?
- ★★ `Instance()` 가 두 판에서 **같은 이유**는?

### 5. ★★★ 할당 바이트를 판 여덟 개로 (예측)

```csharp
// cs27b-alloc.cs
using System;
class Program {
    static int Twice(int x) => x * 2;
    int Inc(int x) => x + 1;
    static int Use(Func<int, int> f) => f(1);
    static long M(Action a) {
        for (int i = 0; i < 200; i++) a();
        var b = GC.GetAllocatedBytesForCurrentThread();
        a();
        return GC.GetAllocatedBytesForCurrentThread() - b;
    }
    static void Main() {
        var p = new Program();
        long sink = 0;
        Console.WriteLine($"[1] Use(Twice)       정적 메서드 그룹     1000번 : {M(() => { for (int i = 0; i < 1000; i++) sink += Use(Twice); })} 바이트");
        Console.WriteLine($"[2] Use(x => x * 2)  캡처 없는 람다       1000번 : {M(() => { for (int i = 0; i < 1000; i++) sink += Use(x => x * 2); })} 바이트");
        Console.WriteLine($"[3] Use(p.Inc)       인스턴스 메서드 그룹 1000번 : {M(() => { for (int i = 0; i < 1000; i++) sink += Use(p.Inc); })} 바이트");
        Func<int, int> x1 = Twice, x2 = Twice;
        Console.WriteLine($"[4] Twice 를 두 번 변환한 두 델리게이트 ReferenceEquals : {ReferenceEquals(x1, x2)}");
        GC.KeepAlive(sink);
    }
}
```

- `[1]`\~`[4]` 는 C# 10 판과 11 판에서 각각?
- ★★★ 같은 판 안(최적화·티어링 2×2)에서 갈리는 줄이 있는가?

### 6. ★★ Java 의 함수형 인터페이스 (경계)

- `interface Op { int apply(int x); }` 에 `Function<Integer,Integer> f` 를 그대로 대입하면 javac 는?
- ★★ C# 의 `f.Invoke` 에 해당하는 Java 의 건너가는 길은?
- ★ 두 언어가 **다른** 자리 하나를 대라(만드는 방식 또는 묶기).

### 7. ★★★ C# 11 의 변화는 무엇이 바꾼 것인가 (왜)

- 소스가 같은데 할당이 바뀐 것은 **언어 명세·Roslyn·JIT** 중 무엇의 일인가 — 무엇으로 가리나?
- ★★ 이 변화가 **깨뜨릴 수 있는 코드**는 어떤 모양인가?

### 8. ★★ 멀티캐스트 반환값을 모두 받으려면 (경계)

- 반환값이 있는 델리게이트를 `+=` 로 묶어 쓰면 무엇을 잃나?
- ★ 모두 받거나, 하나가 던져도 나머지를 부르려면?

### 9. ★ 공개 API 에서 무엇을 받나 (경계)

- 매개변수를 내 `delegate int Op(int)` 로 받으면 호출자에게 무엇이 생기나 — `Func<int,int>` 로 받으면?

### 10. 다른 주제와 잇기 (연결)

- ★★ 람다가 **무엇을 캡처해 어떤 클래스가 되나**의 정본은 몇 번 주제인가?
- ★ 델리게이트 필드에 `+=`/`-=` 만 허락하는 문법은 몇 번 주제인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
