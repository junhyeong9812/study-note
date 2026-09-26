# csharp/syntax/31 — `IEnumerable<T>` 와 `foreach` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> ★★★ 이 주제의 질문은 「**`foreach` 는 인터페이스가 아니라 `GetEnumerator`·`MoveNext`·`Current` 라는 이름을 찾고, 찾은 타입 그대로 부른다**」 한 줄로 거의 다 풀린다. **그 타입이 구조체인가 인터페이스인가**를 세라.
> **환경** — .NET SDK 10.0.401 · 런타임 10.0.12 · `net10.0` · linux-x64 ·
> Roslyn `csc` 를 직접 부른다 · `-langversion:latest`(판 문항만 판을 바꾼다) · `-preferreduilang:en-US`. 대비는 **javac 21.0.5** 다.
> ★★★ **본체 창은 ① IL 덤프다**(「`foreach` 가 무엇으로 풀리나」). 할당은 **2×2 판 격자**로 쟀다.
> 선행 — [10번](../10-collection-choosing-list-dictionary-hashset-queue-stack/)(컬렉션) · [24번](../24-generics-and-type-parameters/)(제네릭) · [30번](../30-extension-methods-and-extension-members/)(확장 메서드).

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (예측) / (왜) / (경계) / (연결) -->

### 1. ★★★ 인터페이스를 하나도 구현하지 않은 `Bag` 을 `foreach` 하면 (예측)

```csharp
// cs31b-pattern.cs
using System;
public class Bag {
    readonly int[] items = { 10, 20, 30 };
    public Walker GetEnumerator() => new Walker(items);
    public struct Walker {
        readonly int[] a; int i;
        public Walker(int[] a) { this.a = a; i = -1; }
        public bool MoveNext() => ++i < a.Length;
        public int Current => a[i];
        public void Dispose() => Console.WriteLine("  Walker.Dispose 불림");
    }
}
public static class Probe {
    public static int Sum(Bag b) { int s = 0; foreach (var x in b) s += x; return s; }
}
class Program {
    static void Main() {
        Console.WriteLine($"[1] Bag 이 구현한 인터페이스 수 : {typeof(Bag).GetInterfaces().Length}");
        Console.WriteLine($"[2] Walker 가 구현한 인터페이스 수 : {typeof(Bag.Walker).GetInterfaces().Length}");
        Console.WriteLine($"[3] Probe.Sum(new Bag()) = {Probe.Sum(new Bag())}");
        Il.Dump(typeof(Probe), "Sum");
    }
}
```

- 컴파일되나? `[1]`\~`[3]` 은?
- ★★★ `Sum` 의 IL 에서 `MoveNext`·`get_Current` 는 **어떤 명령**으로 불리나?
- ★★ `Walker.Dispose` 는 불리나?

### 2. ★★ 확장 메서드 `GetEnumerator` 로 `int` 를 `foreach` 할 수 있나 (경계)

- `static IEnumerator<int> GetEnumerator(this int n)` 을 두고 `foreach (var i in 3)` 을 쓰면? `-langversion:8` 에서는 진단 코드가 무엇인가?
- ★ `GetEnumerator` 가 아예 없는 타입을 `foreach` 하면 진단 코드는?

### 3. ★★ 세 역할을 리플렉션으로 물으면 (예측)

```csharp
// cs31b-roles.cs
using System;
using System.Collections.Generic;
using System.Linq;
class Program {
    static string Own(Type t) => string.Join(" ", t.GetMembers().Where(m => m.DeclaringType == t && m is not System.Reflection.MethodInfo { IsSpecialName: true }).Select(m => m.Name).OrderBy(n => n, StringComparer.Ordinal));
    static void Main() {
        foreach (var t in new[] { typeof(IEnumerable<int>), typeof(IEnumerator<int>), typeof(ICollection<int>), typeof(IList<int>) })
            Console.WriteLine($"{t.Name,-15} 자기 멤버 : {Own(t)}  ·  상위 : {string.Join(",", t.GetInterfaces().Select(i => i.Name).OrderBy(n => n, StringComparer.Ordinal))}");
        var ge = typeof(List<int>).GetMethods().Where(m => m.Name == "GetEnumerator" && m.DeclaringType == typeof(List<int>)).Select(m => m.ReturnType.Name + (m.ReturnType.IsValueType ? " (struct)" : ""));
        Console.WriteLine($"List<int> 의 공개 GetEnumerator 반환 타입 : {string.Join(",", ge)}");
        IEnumerable<int> seq = new List<int> { 1 };
        var e = seq.GetEnumerator();
        Console.WriteLine($"IEnumerable<int> 로 받아 부른 GetEnumerator 의 실제 타입 : {e.GetType().Name} · 그 실제 타입이 값 타입인가 : {e.GetType().IsValueType}");
    }
}
```

- `IEnumerable<T>` · `IEnumerator<T>` · `ICollection<T>` 가 **자기 멤버**로 가진 것은?
- ★★ `List<int>` 의 공개 `GetEnumerator` 는 무엇을 돌려주나? `IEnumerable<int>` 로 받아 부르면?

### 4. ★★★ `List<int>` · `IEnumerable<int>` · `int[]` 를 `foreach` 한 IL (예측)

```csharp
// cs31b-il.cs
using System.Collections.Generic;
public static class L {
    public static int OverList(List<int> xs) { int s = 0; foreach (var x in xs) s += x; return s; }
    public static int OverSeq(IEnumerable<int> xs) { int s = 0; foreach (var x in xs) s += x; return s; }
    public static int OverArray(int[] xs) { int s = 0; foreach (var x in xs) s += x; return s; }
}
class Program {
    static void Main() { Il.Dump(typeof(L), "OverList"); Il.Dump(typeof(L), "OverSeq"); Il.Dump(typeof(L), "OverArray"); }
}
```

- ★★★ 셋 중 `try`/`finally` 가 있는 것은? `Dispose` 는 어떤 명령으로 불리나?
- ★★ `OverArray` 에 `GetEnumerator` 가 있나?

### 5. ★★★ 할당 바이트 — 네 줄 · 2×2 판 격자 (예측)

```csharp
// cs31b-alloc.cs
using System;
using System.Collections.Generic;
class Program {
    static long M(Action a) {
        for (int i = 0; i < 200; i++) a();
        System.Threading.Thread.Sleep(300);
        for (int i = 0; i < 300; i++) a();
        System.Threading.Thread.Sleep(300);
        for (int i = 0; i < 300; i++) a();
        var b = GC.GetAllocatedBytesForCurrentThread();
        a();
        return GC.GetAllocatedBytesForCurrentThread() - b;
    }
    static int OverList(List<int> xs) { int s = 0; foreach (var x in xs) s += x; return s; }
    static int OverSeq(IEnumerable<int> xs) { int s = 0; foreach (var x in xs) s += x; return s; }
    static int OverArray(int[] xs) { int s = 0; foreach (var x in xs) s += x; return s; }
    static void Main() {
        var list = new List<int> { 1, 2, 3, 4, 5, 6, 7, 8, 9, 10 };
        var arr = list.ToArray();
        long sink = 0;
        Console.WriteLine($"[1] List<int> 를 List<int> 로 foreach        1000번 : {M(() => { for (int i = 0; i < 1000; i++) sink += OverList(list); })} 바이트");
        Console.WriteLine($"[2] List<int> 를 IEnumerable<int> 로 foreach 1000번 : {M(() => { for (int i = 0; i < 1000; i++) sink += OverSeq(list); })} 바이트");
        Console.WriteLine($"[3] int[] 를 int[] 로 foreach                1000번 : {M(() => { for (int i = 0; i < 1000; i++) sink += OverArray(arr); })} 바이트");
        Console.WriteLine($"[4] int[] 를 IEnumerable<int> 로 foreach     1000번 : {M(() => { for (int i = 0; i < 1000; i++) sink += OverSeq(arr); })} 바이트");
        GC.KeepAlive(sink);
    }
}
```

- 네 줄의 바이트는? 네 판(2×2)에서 갈리는 줄이 있나?

### 6. ★★★ 순회 중에 고치면 — C# 일곱 줄 · Java 두 줄 (예측)

```csharp
// cs31b-mod.cs
using System;
using System.Collections.Generic;
class Program {
    static void T(string n, Action a) {
        try { a(); Console.WriteLine($"{n,-34} : 끝까지 돎"); }
        catch (Exception e) { Console.WriteLine($"{n,-34} : {e.GetType().Name}: {e.Message}"); }
    }
    static void Main() {
        T("[1] List · x==1 에서 Add(9)", () => { var l = new List<int> { 1, 2, 3 }; foreach (var x in l) if (x == 1) l.Add(9); });
        T("[2] List · x==1 에서 l[2] = 9", () => { var l = new List<int> { 1, 2, 3 }; foreach (var x in l) if (x == 1) l[2] = 9; });
        T("[3] List · x==2 에서 Remove(3)", () => { var l = new List<int> { 1, 2, 3 }; foreach (var x in l) if (x == 2) l.Remove(3); });
        T("[4] Dictionary · 키 1 에서 Remove(2)", () => { var d = new Dictionary<int, int> { [1] = 1, [2] = 2, [3] = 3 }; foreach (var kv in d) if (kv.Key == 1) d.Remove(2); });
        T("[5] Dictionary · 키 1 에서 d[2] = 9", () => { var d = new Dictionary<int, int> { [1] = 1, [2] = 2, [3] = 3 }; foreach (var kv in d) if (kv.Key == 1) d[2] = 9; });
        T("[6] Dictionary · 키 1 에서 d[4] = 9", () => { var d = new Dictionary<int, int> { [1] = 1, [2] = 2, [3] = 3 }; foreach (var kv in d) if (kv.Key == 1) d[4] = 9; });
        T("[7] 배열 · x==1 에서 a[2] = 9", () => { var a = new[] { 1, 2, 3 }; foreach (var x in a) if (x == 1) a[2] = 9; });
        var v = typeof(List<int>).GetField("_version", System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance)!;
        var l8 = new List<int> { 1, 2, 3 };
        Console.WriteLine($"[8] List 의 숨은 필드 _version : 처음 {v.GetValue(l8)} · Add 뒤 {Step(l8, v, () => l8.Add(4))} · l[0]=7 뒤 {Step(l8, v, () => l8[0] = 7)} · 읽기 l[0] 뒤 {Step(l8, v, () => _ = l8[0])}");
    }
    static object Step(List<int> l, System.Reflection.FieldInfo f, Action a) { a(); return f.GetValue(l)!; }
}
```

- `[1]`\~`[7]` 중 던지는 줄은? `[8]` 의 `_version` 은 어떻게 움직이나?
- ★★★ 같은 `[3]`(마지막 원소 직전에서 마지막 원소를 지움)을 Java `ArrayList` 로 하면?

### 7. ★★ `Dispose` 는 언제 불리나 — 끝까지 · `break` · 몸통이 던지면 (예측)

```csharp
// cs31b-dispose.cs
using System;
using System.Collections;
using System.Collections.Generic;
class Traced : IEnumerable<int> {
    public IEnumerator<int> GetEnumerator() { Console.WriteLine("  GetEnumerator"); return new E(); }
    IEnumerator IEnumerable.GetEnumerator() => GetEnumerator();
    class E : IEnumerator<int> {
        int i;
        public int Current { get { Console.WriteLine($"  Current → {i}"); return i; } }
        object IEnumerator.Current => Current;
        public bool MoveNext() { i++; bool r = i <= 3; Console.WriteLine($"  MoveNext → {r}"); return r; }
        public void Reset() => throw new NotSupportedException();
        public void Dispose() => Console.WriteLine("  Dispose");
    }
}
class Program {
    static void Main() {
        Console.WriteLine("[1] 끝까지");
        foreach (var x in new Traced()) Console.WriteLine($"  몸통 {x}");
        Console.WriteLine("[2] x == 2 에서 break");
        foreach (var x in new Traced()) { Console.WriteLine($"  몸통 {x}"); if (x == 2) break; }
        Console.WriteLine("[3] x == 1 에서 몸통이 던진다");
        try { foreach (var x in new Traced()) { Console.WriteLine($"  몸통 {x}"); throw new InvalidOperationException("body"); } }
        catch (InvalidOperationException e) { Console.WriteLine($"  바깥 catch : {e.Message}"); }
    }
}
```

- 세 경우 각각 로그의 마지막 줄은?

### 8. ★★★ 1번이 컴파일된 이유 · `Walker.Dispose` 의 운명 (왜)

- 1번과 4번을 근거로 「`foreach` 는 `IEnumerable` 을 봐야 하나」에 답하라. 1번의 `Walker.Dispose` 는 불렸나, 그 이유는?

### 9. ★★★ 5번의 `[1]` 대 `[2]` (왜)

- 5번의 `[1]` 대 `[2]` 를 4번 IL 과 3번 리플렉션으로 설명하라. ([24번](../24-generics-and-type-parameters/) 과 어디서 이어지나?)

### 10. ★★ 순회 중 수정 — C# · Java · Rust (경계)

- 세 언어는 「순회 중 수정」을 각각 **언제** 막나(실행 · 실행 · 컴파일)? 6번 `[3]` 에서 C# 과 Java 가 갈린 이유는?

### 11. 다른 주제와 잇기 (연결)

- ★★ `yield return` 으로 1번의 `Walker` 같은 열거자를 손으로 안 쓰고 만드는 주제는?
- ★ 목록 패턴 `[1, .., 3]` 은 `foreach` 의 패턴과 같은 이름(`GetEnumerator`)을 쓰나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
