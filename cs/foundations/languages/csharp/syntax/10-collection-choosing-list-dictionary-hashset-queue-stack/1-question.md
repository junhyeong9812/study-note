# csharp/syntax/10 — 컬렉션 선택: `List`·`Dictionary`·`HashSet`·`Queue`/`Stack` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> **환경** — .NET SDK **10.0.401** · 런타임 **.NET 10.0.12** · 타겟 **`net10.0`** · linux-x64.
> 진단은 **영어로 고정**했다(`DOTNET_CLI_UI_LANGUAGE=en` + `csc -preferreduilang:en-US`).
> ★★★ **3·4·5번이 이 주제의 축이다** — **셋을 따로 답하면 안 된다.**
> 3번은 「안 갈렸다」를, 4번은 **그것을 어떻게 갈랐나**를, 5번은 **그래서 몇 판이 근거가 되나**를 묻는다.
> ★★ **4번을 먼저 보면 3번이 안 풀린다** — 순서대로 답하라.
> ★ **8번은 「경고가 안 났다」가 답이다** — 무엇을 물었는지까지 답해야 한다.
> 선행 — [03번](../03-boxing-and-unboxing/)(박싱과 할당 바이트 재는 법) ·
> [01번](../01-value-types-and-reference-types/)(값 타입과 참조 타입).
> 경계 — **자료구조의 원리**는 [`data-structure/01`](../../../../../data-structure/01-dynamic-array/) ·
> [`03`](../../../../../data-structure/03-stack/) ·
> [`04`](../../../../../data-structure/04-queue-deque/) ·
> [`05`](../../../../../data-structure/05-hashmap/)가 정본이다. 여기는 **.NET 에서 무엇을 고르나**다.
> 대비 — Go 갈래 목록([`go/syntax/README.md`](../../../go/syntax/README.md))의 **9번** ·
> Python 갈래 목록([`python/syntax/README.md`](../../../python/syntax/README.md))의 **12번** ·
> Rust 갈래 목록([`rust/syntax/README.md`](../../../rust/syntax/README.md))의 **28번**.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 넷에게 같은 일을 시키면 (예측)

```csharp
// cs10b-four.cs
using System;
using System.Collections.Generic;

var list = new List<string> { "빨강", "초록", "파랑" };
list.Insert(1, "노랑");
Console.WriteLine($"List<string>      [{string.Join(", ", list)}]");
Console.WriteLine($"  list[2] = {list[2]}   Count = {list.Count}   IndexOf(\"파랑\") = {list.IndexOf("파랑")}");
Console.WriteLine($"  Contains(\"파랑\") = {list.Contains("파랑")}   ← 앞에서부터 하나씩 본다");

var dict = new Dictionary<string, int> { ["빨강"] = 1, ["초록"] = 2, ["파랑"] = 3 };
Console.WriteLine($"Dictionary        [{string.Join(", ", dict.Keys)}]");
Console.WriteLine($"  dict[\"초록\"] = {dict["초록"]}   ContainsKey(\"보라\") = {dict.ContainsKey("보라")}");
Console.WriteLine($"  TryGetValue(\"보라\", out v) = {dict.TryGetValue("보라", out int v)}  (v = {v})");

var set = new HashSet<string> { "빨강", "초록", "빨강", "파랑" };
Console.WriteLine($"HashSet           [{string.Join(", ", set)}]   ← \"빨강\" 을 두 번 넣었는데 Count = {set.Count}");
Console.WriteLine($"  Add(\"빨강\") = {set.Add("빨강")}   Add(\"보라\") = {set.Add("보라")}   ← 되돌림값이 「새로 들어갔나」다");

var queue = new Queue<string>();
queue.Enqueue("1번손님"); queue.Enqueue("2번손님"); queue.Enqueue("3번손님");
Console.WriteLine($"Queue             [{string.Join(", ", queue)}]   Dequeue() = {queue.Dequeue()}   ← 먼저 온 사람");

var stack = new Stack<string>();
stack.Push("접시1"); stack.Push("접시2"); stack.Push("접시3");
Console.WriteLine($"Stack             [{string.Join(", ", stack)}]   Pop() = {stack.Pop()}   ← 마지막에 얹은 것");
```

- `list.IndexOf("파랑")` 은 **몇**인가 — `Insert(1, "노랑")` 이 자리를 밀었나?
- ★ `set.Add("빨강")` 의 **되돌림값**은 무엇인가 — `List.Add` 와 왜 시그니처가 다른가?
- ★ `stack` 을 `string.Join` 으로 찍으면 **어느 순서**로 나오는가?

### 2. 하나씩 넣으면서 Capacity 를 찍으면 (예측)

```csharp
// cs10b-capacity.cs
using System;
using System.Collections.Generic;

var list = new List<int>();
int prev = list.Capacity;
Console.WriteLine($"new List<int>()        Count=0  Capacity={list.Capacity}");
for (int i = 0; i < 40; i++) {
    list.Add(i);
    if (list.Capacity != prev) { Console.WriteLine($"   Add #{i + 1} 에서  Count={list.Count,2}  Capacity {prev,2} → {list.Capacity}"); prev = list.Capacity; }
}

var set = new HashSet<int>();
int hp = set.Capacity;
Console.WriteLine($"new HashSet<int>()     Count=0  Capacity={set.Capacity}");
for (int i = 0; i < 40; i++) {
    set.Add(i);
    if (set.Capacity != hp) { Console.WriteLine($"   Add #{i + 1} 에서  Count={set.Count,2}  Capacity {hp,2} → {set.Capacity}"); hp = set.Capacity; }
}

var dict = new Dictionary<string, int>();
int dp = dict.Capacity;
Console.WriteLine($"new Dictionary<,>()    Count=0  Capacity={dict.Capacity}");
for (int i = 0; i < 40; i++) {
    dict[$"k{i}"] = i;
    if (dict.Capacity != dp) { Console.WriteLine($"   Add #{i + 1} 에서  Count={dict.Count,2}  Capacity {dp,2} → {dict.Capacity}"); dp = dict.Capacity; }
}

Console.WriteLine();
Console.WriteLine($"미리 잡아 주면 — new List<int>(5).Capacity       = {new List<int>(5).Capacity}");
Console.WriteLine($"미리 잡아 주면 — new HashSet<int>(5).Capacity    = {new HashSet<int>(5).Capacity}   ← 5 가 아니다");
Console.WriteLine($"미리 잡아 주면 — new Dictionary<string,int>(5).Capacity = {new Dictionary<string, int>(5).Capacity}   ← 5 가 아니다");
Console.WriteLine($"컬렉션 초기화자  — new List<int> {{ 1, 2, 3 }}.Capacity   = {new List<int> { 1, 2, 3 }.Capacity}");
List<int> byExpr = [1, 2, 3];
Console.WriteLine($"컬렉션 식        — List<int> x = [1, 2, 3] 의 Capacity = {byExpr.Capacity}   ← ★ 위와 다르다(11번 주제)");
```

- ★ `List<int>` 의 Capacity 는 **어느 수열**로 커지는가?
- ★★ `HashSet<int>` 과 `Dictionary<,>` 는 **같은 수열인가 다른 수열인가**?
- `new HashSet<int>(5).Capacity` 는 **몇**인가?
- ★★★ 이 수열들은 **보장인가 구현인가** — 어느 문서가 무엇까지 약속하나?

### 3. ★★★ 다섯을 넣고, 하나를 지우고, 하나를 더 넣으면 (예측)

```csharp
// cs10b-dict-order.cs
using System;
using System.Collections.Generic;

var d = new Dictionary<string, int>();
d["alpha"] = 1; d["bravo"] = 2; d["charlie"] = 3; d["delta"] = 4; d["echo"] = 5;
Console.WriteLine($"① 다섯을 차례로 넣고 순회    : {Show(d)}");

d.Remove("bravo");
Console.WriteLine($"② bravo 를 지우고 순회       : {Show(d)}");

d["foxtrot"] = 6;
Console.WriteLine($"③ foxtrot 를 더하고 순회     : {Show(d)}   ★ 맨 뒤가 아니다");

d["golf"] = 7;
Console.WriteLine($"④ golf 를 더 더하고 순회     : {Show(d)}");

var e = new Dictionary<string, int>();
e["echo"] = 5; e["delta"] = 4; e["charlie"] = 3; e["bravo"] = 2; e["alpha"] = 1;
Console.WriteLine($"⑤ 같은 키를 거꾸로 넣고 순회 : {Show(e)}   ← 해시 순서가 아니다");

var f = new Dictionary<string, int>(e);
Console.WriteLine($"⑥ 그것을 복사 생성자로 옮기면: {Show(f)}");

var g = new Dictionary<string, int>();
for (int i = 0; i < 8; i++) g[$"k{i}"] = i;
Console.WriteLine($"⑦ 8개 넣어 리사이즈를 지나면 : {Show(g)}");

static string Show(Dictionary<string, int> d) {
    var parts = new List<string>();
    foreach (var kv in d) parts.Add($"{kv.Key}={kv.Value}");
    return string.Join(" ", parts);
}
```

- ①의 순서는 무엇인가 — 그리고 ⑤를 보면 **①의 순서가 무엇에서 오는지** 알 수 있나?
- ★★★ ③에서 `foxtrot` 은 **어디**에 나오는가?
- ⑦은 리사이즈를 두 번 지나는데 순서가 **유지되는가**?
- ★★ 이 중 **문서가 약속한 것**은 몇 줄인가?
- ★★ `buckets` 와 `entries` 두 배열 중 **순회가 훑는 것**은 어느 쪽인가 — 그래서 해시 무작위화가 왜 안 닿는가?

### 4. ★★★ 둘을 지우고 둘을 넣으면 (예측)

```csharp
// cs10b-freelist.cs
using System;
using System.Collections.Generic;

var d = new Dictionary<string, int>();
foreach (var k in new[] { "a", "b", "c", "d", "e" }) d[k] = 0;
Console.WriteLine($"넣은 직후            : {string.Join(" ", d.Keys)}");
d.Remove("b");
Console.WriteLine($"b 를 지우고          : {string.Join(" ", d.Keys)}");
d.Remove("d");
Console.WriteLine($"d 도 지우고          : {string.Join(" ", d.Keys)}");
d["X"] = 0;
Console.WriteLine($"X 를 넣으면          : {string.Join(" ", d.Keys)}   ★ d 가 있던 자리다(나중에 빈 자리부터)");
d["Y"] = 0;
Console.WriteLine($"Y 를 넣으면          : {string.Join(" ", d.Keys)}   ★ b 가 있던 자리다");
Console.WriteLine();

var h = new HashSet<string> { "a", "b", "c", "d", "e" };
Console.WriteLine($"HashSet 도 같다 — 넣은 직후 : {string.Join(" ", h)}");
h.Remove("b"); h.Add("Z");
Console.WriteLine($"                b 빼고 Z 넣고 : {string.Join(" ", h)}");
Console.WriteLine();

Console.WriteLine("★ 여기까지는 한 프로세스 안의 이야기다.");
Console.WriteLine("  「여러 판을 돌리면 갈리나」는 다음 블록이 가짓수로 답한다.");
```

- ★★★ 마지막 줄의 순서는 무엇인가 — `X` 와 `Y` 중 **어느 쪽이 앞**인가?
- ★★ `HashSet` 도 **같은 일**이 벌어지는가?
- ★ 이것을 **여러 번 돌려서** 알아낼 수 있었겠는가?

### 5. ★★★ 같은 프로그램을 스무 판 돌려 가짓수를 세면 (예측)

```csharp
// cs10b-variety.cs
using System;
using System.Collections.Generic;

var d = new Dictionary<string, int>();
foreach (var k in new[] { "alpha", "bravo", "charlie", "delta", "echo" }) d[k] = 1;
d.Remove("bravo");
d["foxtrot"] = 1;
var keys = new List<string>();
foreach (var kv in d) keys.Add(kv.Key);
Console.WriteLine("순회 " + string.Join(" ", keys));
Console.WriteLine("해시 " + "alpha".GetHashCode());
```

- ★★★ 「순회」 줄은 **몇 가지**이고 「해시」 줄은 **몇 가지**인가?
- ★★★ 둘이 갈린다면 — 이 런타임은 **무엇을 무작위화하고 무엇을 안 하는가**?
- ★★ 그래서 「스무 번 돌려도 같았다」는 **무엇을 증명하는가**?

### 6. ★★ `Equals` 만 재정의한 타입을 키로 쓰면 (예측)

```csharp
// cs10b-contract.cs
using System;
using System.Collections.Generic;

var bad = new HashSet<BadKey> { new BadKey(1), new BadKey(1), new BadKey(1) };
Console.WriteLine($"BadKey  (GetHashCode 없음)  Count = {bad.Count}   Contains(new BadKey(1)) = {bad.Contains(new BadKey(1))}");
var good = new HashSet<GoodKey> { new GoodKey(1), new GoodKey(1), new GoodKey(1) };
Console.WriteLine($"GoodKey (GetHashCode 있음)  Count = {good.Count}   Contains(new GoodKey(1)) = {good.Contains(new GoodKey(1))}");
Console.WriteLine($"  그런데 Equals 는 둘 다 true 다 : {new BadKey(1).Equals(new BadKey(1))} / {new GoodKey(1).Equals(new GoodKey(1))}");
Console.WriteLine();

var m = new GoodKey(1);
var set = new HashSet<GoodKey> { m };
Console.WriteLine($"넣은 직후             Contains(m) = {set.Contains(m)}");
m.X = 99;
Console.WriteLine($"m.X = 99 로 바꾼 뒤   Contains(m) = {set.Contains(m)}   Count = {set.Count}");
Console.WriteLine($"  그래도 순회하면 보인다 : {string.Join(", ", set)}");
Console.WriteLine($"  Remove(m) = {set.Remove(m)}   지운 뒤 Count = {set.Count}   ← 꺼낼 수도 없다");

class BadKey {
    public int X;
    public BadKey(int x) { X = x; }
    public override bool Equals(object o) => o is BadKey b && b.X == X;
    public override string ToString() => $"BadKey({X})";
}
class GoodKey {
    public int X;
    public GoodKey(int x) { X = x; }
    public override bool Equals(object o) => o is GoodKey g && g.X == X;
    public override int GetHashCode() => X.GetHashCode();
    public override string ToString() => $"GoodKey({X})";
}
```

- ★★ 컴파일러가 **무슨 진단**을 내는가 — 에러인가 경고인가?
- ★★★ `bad.Count` 는 **몇**이고 `bad.Contains(new BadKey(1))` 은 무엇인가?
- ★★★ 넣은 뒤 `m.X` 를 고치면 — `Contains`·`Remove`·**순회**가 각각 무엇을 답하는가?

### 7. `Stack` 의 순회는 거꾸로 나온다 (경계)

```csharp
// cs10b-queue-stack.cs
using System;
using System.Collections.Generic;

var q = new Queue<string>();
q.Enqueue("A"); q.Enqueue("B"); q.Enqueue("C");
Console.WriteLine($"Queue  순회     : {string.Join(" ", q)}");
Console.WriteLine($"Queue  Peek() = {q.Peek()}   Dequeue() = {q.Dequeue()}   남은 것 : {string.Join(" ", q)}");
Console.WriteLine($"Queue  ToArray(): [{string.Join(" ", q.ToArray())}]");
Console.WriteLine();

var s = new Stack<string>();
s.Push("A"); s.Push("B"); s.Push("C");
Console.WriteLine($"Stack  순회     : {string.Join(" ", s)}   ★ 넣은 순서의 거꾸로다");
Console.WriteLine($"Stack  Peek() = {s.Peek()}   Pop() = {s.Pop()}   남은 것 : {string.Join(" ", s)}");
Console.WriteLine($"Stack  ToArray(): [{string.Join(" ", s.ToArray())}]   ★ 이것도 거꾸로다");
Console.WriteLine();

var empty = new Queue<string>();
Console.WriteLine($"빈 Queue 에 TryDequeue = {empty.TryDequeue(out var got)}  (got = {got ?? "null"})");
try { empty.Dequeue(); }
catch (InvalidOperationException ex) { Console.WriteLine($"빈 Queue 에 Dequeue()  → {ex.GetType().Name}: {ex.Message}"); }

var q2 = new Queue<int>();
for (int i = 0; i < 5; i++) q2.Enqueue(i);
for (int i = 0; i < 3; i++) q2.Dequeue();
for (int i = 5; i < 8; i++) q2.Enqueue(i);
Console.WriteLine($"3번 빼고 3번 더 넣어도 순서는 : {string.Join(" ", q2)}   ← 원형 버퍼라 앞이 재활용된다");
```

- ★★ 그 거꾸로가 **계약인가 관찰인가** — (3)의 `Dictionary` 순서와 무엇이 다른가?
- 빈 큐에서 `Dequeue()` 와 `TryDequeue()` 는 **되돌림 방식**이 어떻게 갈리는가?
- ★ 3번 빼고 3번 더 넣은 큐가 `3 4 5 6 7` 인 것은 **어느 구조** 때문인가?

### 8. 순회 중 `Remove` 는 되고 `Add` 는 터진다 (경계)

```csharp
// cs10b-throws.cs
using System;
using System.Collections.Generic;

var d = new Dictionary<string, int> { ["a"] = 1, ["b"] = 2, ["c"] = 3 };
try { int x = d["없는키"]; Console.WriteLine(x); }
catch (KeyNotFoundException ex) { Console.WriteLine($"d[\"없는키\"] 읽기 → {ex.GetType().Name}: {ex.Message}"); }
Console.WriteLine($"TryGetValue(\"없는키\", out v) = {d.TryGetValue("없는키", out int v)}  (v = {v})");
Console.WriteLine($"GetValueOrDefault(\"없는키\", -1) = {d.GetValueOrDefault("없는키", -1)}");
Console.WriteLine($"d[\"없는키\"] = 9 로 쓰기 → 예외 없이 들어간다. Count = {Put(d)}");
Console.WriteLine();

try { foreach (var kv in d) d["z"] = 9; }
catch (InvalidOperationException ex) { Console.WriteLine($"순회 중 새 키 Add       → {ex.GetType().Name}: {ex.Message}"); }

var d2 = new Dictionary<string, int> { ["a"] = 1, ["b"] = 2, ["c"] = 3 };
try { foreach (var kv in d2) if (kv.Key == "b") d2.Remove("b");
      Console.WriteLine($"순회 중 Remove          → 안 터졌다. 남은 것 = {string.Join(" ", d2.Keys)}"); }
catch (InvalidOperationException ex) { Console.WriteLine($"순회 중 Remove          → {ex.GetType().Name}: {ex.Message}"); }

var d3 = new Dictionary<string, int> { ["a"] = 1, ["b"] = 2 };
try { foreach (var kv in d3) d3["a"] = 99;
      Console.WriteLine($"순회 중 있는 키 덮어쓰기 → 안 터졌다. d3[\"a\"] = {d3["a"]}"); }
catch (InvalidOperationException ex) { Console.WriteLine($"순회 중 덮어쓰기        → {ex.GetType().Name}: {ex.Message}"); }

var l = new List<int> { 1, 2, 3 };
try { foreach (int x in l) l.Add(4); }
catch (InvalidOperationException ex) { Console.WriteLine($"List 순회 중 Add        → {ex.GetType().Name}: {ex.Message}"); }

static int Put(Dictionary<string, int> d) { d["없는키"] = 9; return d.Count; }
```

- ★★ 그 둘이 갈린 것은 **언제부터**이고 **누가 정한 것**인가?
- ★★ 같은 일을 `List` 에서 하면 **어느 쪽**인가 — 그리고 왜 갈리는가?
- ★ 없는 키를 **읽는 것**과 **쓰는 것**은 왜 결과가 다른가?

### 9. ★★ `struct` 키 조회 100번이 7200바이트를 낸다 (왜)

```csharp
// cs10b-boxing.cs
using System;
using System.Collections;
using System.Collections.Generic;
using System.Runtime.CompilerServices;

class P {
    [MethodImpl(MethodImplOptions.NoInlining)] static void FillOld(ArrayList a) { for (int i = 0; i < 100; i++) a.Add(i); }
    [MethodImpl(MethodImplOptions.NoInlining)] static void FillNew(List<int> a) { for (int i = 0; i < 100; i++) a.Add(i); }
    [MethodImpl(MethodImplOptions.NoInlining)] static int LookPlain(Dictionary<PlainKey, int> d, PlainKey k) { int t = 0; for (int i = 0; i < 100; i++) t += d[k]; return t; }
    [MethodImpl(MethodImplOptions.NoInlining)] static int LookFast(Dictionary<FastKey, int> d, FastKey k) { int t = 0; for (int i = 0; i < 100; i++) t += d[k]; return t; }

    static void Main() {
        var dp = new Dictionary<PlainKey, int> { [new PlainKey(1, 2)] = 7 };
        var df = new Dictionary<FastKey, int> { [new FastKey(1, 2)] = 7 };
        for (int w = 0; w < 3; w++) {
            var wa = new ArrayList(); FillOld(wa);
            var wl = new List<int>(); FillNew(wl);
            LookPlain(dp, new PlainKey(1, 2)); LookFast(df, new FastKey(1, 2));
        }
        long b0, b1;
        b0 = GC.GetAllocatedBytesForCurrentThread(); var al = new ArrayList(); FillOld(al); b1 = GC.GetAllocatedBytesForCurrentThread();
        Console.WriteLine($"ArrayList 에 int 100개 넣기           : +{b1 - b0} 바이트");
        b0 = GC.GetAllocatedBytesForCurrentThread(); var li = new List<int>(); FillNew(li); b1 = GC.GetAllocatedBytesForCurrentThread();
        Console.WriteLine($"List<int> 에 int 100개 넣기           : +{b1 - b0} 바이트");
        Console.WriteLine();
        b0 = GC.GetAllocatedBytesForCurrentThread(); int t1 = LookPlain(dp, new PlainKey(1, 2)); b1 = GC.GetAllocatedBytesForCurrentThread();
        Console.WriteLine($"Dictionary<PlainKey,int> 조회 100번   : +{b1 - b0} 바이트  (합 {t1})   ← IEquatable<T> 없음");
        b0 = GC.GetAllocatedBytesForCurrentThread(); int t2 = LookFast(df, new FastKey(1, 2)); b1 = GC.GetAllocatedBytesForCurrentThread();
        Console.WriteLine($"Dictionary<FastKey,int>  조회 100번   : +{b1 - b0} 바이트  (합 {t2})   ← IEquatable<T> 있음");
        Console.WriteLine();
        Console.WriteLine($"EqualityComparer<PlainKey>.Default 의 실제 타입 : {EqualityComparer<PlainKey>.Default.GetType().Name}");
        Console.WriteLine($"EqualityComparer<FastKey>.Default  의 실제 타입 : {EqualityComparer<FastKey>.Default.GetType().Name}");
        Console.WriteLine($"EqualityComparer<string>.Default   의 실제 타입 : {EqualityComparer<string>.Default.GetType().Name}");
        GC.KeepAlive(al); GC.KeepAlive(li);
    }
}

struct PlainKey { public int A, B; public PlainKey(int a, int b) { A = a; B = b; } }

struct FastKey : IEquatable<FastKey> {
    public int A, B;
    public FastKey(int a, int b) { A = a; B = b; }
    public bool Equals(FastKey o) => A == o.A && B == o.B;
    public override bool Equals(object o) => o is FastKey f && Equals(f);
    public override int GetHashCode() => A * 31 + B;
}
```

- ★★★ 조회 **한 번에 72바이트**인데, 이것을 **24바이트짜리 박스 몇 개**로 설명하나?
- ★★ `FastKey` 쪽이 **0** 인 것은 **무엇 하나**의 차이인가?
- ★ 기본 비교자의 타입 이름이 셋으로 갈리는데, **이름이 무엇을 말해 주는가**?

### 10. ★★ 사고를 여덟 자리에 심고 `-warn:9` 로 던지면 (경계)

```csharp
// cs10b-quiet.cs
using System;
using System.Collections;
using System.Collections.Generic;

// 이 파일은 이 주제의 사고를 여덟 자리에 일부러 심어 놓은 탐침이다.
// -warn:9 로 컴파일해 컴파일러가 몇 군데에서 말하는지 센다.
public static class Probes {
    public static void P1_ArrayList() {                      // 1. 박싱 — int 를 ArrayList 에
        var a = new ArrayList();
        for (int i = 0; i < 10; i++) a.Add(i);
    }
    public static int P2_StructKey() {                       // 2. IEquatable 없는 struct 키
        var d = new Dictionary<Pair, int> { [new Pair(1, 2)] = 3 };
        return d[new Pair(1, 2)];
    }
    public static string P3_OrderDependency(Dictionary<string, int> d) {  // 3. 순회 순서에 기댄 코드
        foreach (var kv in d) return kv.Key;                 //    「첫 키」를 답으로 쓴다
        return "";
    }
    public static void P4_MutableKey() {                     // 4. 넣은 뒤 키를 고친다
        var k = new Holder { X = 1 };
        var set = new HashSet<Holder> { k };
        k.X = 2;
    }
    public static void P5_RemoveWhileEnumerating(Dictionary<string, int> d) {  // 5. 순회 중 삭제
        foreach (var kv in d) if (kv.Value == 0) d.Remove(kv.Key);
    }
    public static int P6_CapacityDependency() {              // 6. Capacity 증가 규칙에 기댄다
        var l = new List<int>();
        l.Add(1);
        return l.Capacity;                                   //    4 라고 믿는 코드
    }
    public static bool P7_EqualsOnly() {                     // 7. Equals 만 재정의한 타입을 키로
        var set = new HashSet<EqualsOnly> { new EqualsOnly(), new EqualsOnly() };
        return set.Count == 1;
    }
    public static int P8_HashCodeOnly() {                    // 8. GetHashCode 만 재정의한 타입을 키로
        var set = new HashSet<HashOnly> { new HashOnly(), new HashOnly() };
        return set.Count;
    }
}
public struct Pair { public int A, B; public Pair(int a, int b) { A = a; B = b; } }
public class Holder { public int X; public override int GetHashCode() => X; public override bool Equals(object o) => o is Holder h && h.X == X; }
public class EqualsOnly { public override bool Equals(object o) => o is EqualsOnly; }
public class HashOnly { public override int GetHashCode() => 1; }
```

- ★★★ **몇 군데**에서 진단이 나오는가 — 그리고 **어느 자리**인가?
- ★★ 탐침 7번과 8번은 대칭인데 **한쪽만** 경고가 나는 이유는?
- ★ `cc exit` 이 **0** 인 것은 무엇을 말하는가?

### 11. 넷 중 무엇을 고르나 (경계)

- 「이미 본 것인지만 알면 된다」 — 무엇을 고르나?
- 「순서대로 꺼내되 넣은 순서를 지켜야 한다」 — `Dictionary` 로 되나?
- ★ `list.RemoveAt(0)` 으로 큐를 흉내 내면 무엇이 나빠지는가?

### 12. ★ 다른 갈래·앞 주제와 잇기 (연결)

- Go 의 맵은 **왜 일부러 섞는가** — .NET 과 목적이 어떻게 다른가?
- Python 은 같은 관찰을 **어떻게 처리했는가**(3.6 → 3.7)?
- Rust 는 `Hash` 를 안 단 타입을 키로 쓰면 **어느 단계**에서 막는가?
- 제네릭 컬렉션이 박싱을 없애는 것은 **담을 때인가 찾을 때인가**([03번](../03-boxing-and-unboxing/))?
- `List<T>` 가 안쪽에 들고 있는 것은 무엇인가([09번](../09-arrays-index-and-range/))?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|---|---|---|---|
| | | | |
