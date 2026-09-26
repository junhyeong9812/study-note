# csharp/syntax/34 — LINQ 쿼리 구문 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·진단·IL 은 **.NET SDK 10.0.401** · 런타임 **10.0.12** · 타겟 **`net10.0`** ·
> **linux-x64** 에서 실제로 돌려 얻은 것이다(2026-09-26).\
> 진단은 **`-preferreduilang:en-US`** 로 영어로 고정했다.\
> ★ 블록은 캡처 스크립트가 파일로 받아 조립기가 끼워 넣은 것이다 — 손으로 옮긴 줄은 없다.\
> ★ 진단을 싣는 블록은 전부 **그 진단을 낸 소스를 같은 블록 안에** 다시 싣는다(`===== 소스: … =====`).
> **읽는 법** — 근거로 쓰는 것은 **`System.Linq` 호출 목록 · 스크립트가 센 「N / M」 · 진단 코드와 (행,열)** 이다. 컴파일러가 지은 이름의 숫자는 흔들리는 칸이다.
> ★★★ **이 문서는 시간을 재지 않았다** — 두 구문의 IL 이 같아서 **잴 것이 없다**(8번).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ **`Where → Select` · `Where` · `Select` · `Select(익명) → Where → Select` · `SelectMany` · `OrderByDescending → ThenBy` · `GroupBy` · `GroupBy`(원소 선택자) · `Join` · `GroupJoin` · `Cast → Select` · `Select → Where` · `OrderBy → OrderBy`** — Q04 첫 호출의 둘째 타입 인자는 **`<>f__AnonymousType0<Int32,Int32>`**

**출력**

```text
===== 소스: cs34b-q.cs =====
using System.Linq;
public static class Q {
    static readonly int[] xs = { 1, 2, 3 }, ys = { 2, 3, 4 };
    static readonly object[] objs = { 1, 2 };
    public static object Q01() => from x in xs where x > 1 select x * 2;
    public static object Q02() => from x in xs where x > 1 select x;
    public static object Q03() => from x in xs select x;
    public static object Q04() => from x in xs let y = x * 2 where y > 2 select y;
    public static object Q05() => from x in xs from y in ys select x + y;
    public static object Q06() => from x in xs orderby x descending, x % 2 select x;
    public static object Q07() => from x in xs group x by x % 2;
    public static object Q08() => from x in xs group x * 10 by x % 2;
    public static object Q09() => from x in xs join y in ys on x equals y select x + y;
    public static object Q10() => from x in xs join y in ys on x equals y into g select g.Count();
    public static object Q11() => from int x in objs select x;
    public static object Q12() => from x in xs select x into z where z > 1 select z;
    public static object Q13() => from x in xs where x > 1 select x;
    public static object Q14() => from x in xs orderby x orderby x % 2 select x;
}
===== csc -optimize -target:library -out:q34.dll cs34b-q.cs (cc exit=0) =====
===== 소스: cs34b-il.cs =====
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
public static class M {
    static readonly int[] xs = { 1, 2, 3 }, ys = { 2, 3, 4 };
    static readonly object[] objs = { 1, 2 };
    public static object M01() => xs.Where(x => x > 1).Select(x => x * 2);
    public static object M02() => xs.Where(x => x > 1);
    public static object M03() => xs.Select(x => x);
    public static object M04() => xs.Select(x => new { x, y = x * 2 }).Where(t => t.y > 2).Select(t => t.y);
    public static object M05() => xs.SelectMany(x => ys, (x, y) => x + y);
    public static object M06() => xs.OrderByDescending(x => x).ThenBy(x => x % 2);
    public static object M07() => xs.GroupBy(x => x % 2);
    public static object M08() => xs.GroupBy(x => x % 2, x => x * 10);
    public static object M09() => xs.Join(ys, x => x, y => y, (x, y) => x + y);
    public static object M10() => xs.GroupJoin(ys, x => x, y => y, (x, g) => g.Count());
    public static object M11() => objs.Cast<int>().Select(x => x);
    public static object M12() => xs.Select(x => x).Where(z => z > 1);
    public static object M13() => xs.Where(x => x > 1).Select(x => x);
    public static object M14() => xs.OrderBy(x => x).OrderBy(x => x % 2);
}
class Program {
    static string[] Lines(Type t, string name) {
        var w = new StringWriter(); var o = Console.Out; Console.SetOut(w);
        Il.Dump(t, name); Console.SetOut(o);
        return w.ToString().Split('\n', StringSplitOptions.RemoveEmptyEntries).Skip(1).ToArray();
    }
    static List<string> Calls(Type t, string name) => Lines(t, name)
        .Where(l => l.Contains(": call ") && l.Contains("System.Linq."))
        .Select(l => l.Substring(l.IndexOf("System.Linq.")).Replace("System.Linq.Enumerable::", "").Replace("System.", ""))
        .ToList();
    static List<string> Ops(Type t, string name) => OpsOf(Lines(t, name));
    static List<string> OpsOf(string[] lines) => lines
        .Where(l => l.Contains(": ")).Select(l => l.Split(": ")[1].Split(' ')[0]).ToList();
    static Dictionary<string, List<List<string>>> LambdaBodies(Type t) {
        var c = Il.Nested(t, "<>c");
        var ms = c.GetMethods(System.Reflection.BindingFlags.Instance | System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Public | System.Reflection.BindingFlags.DeclaredOnly)
                  .Where(m => m.Name.Contains("b__")).OrderBy(m => m.MetadataToken).ToList();
        var d = new Dictionary<string, List<List<string>>>();
        foreach (var m in ms) {
            var w = new StringWriter(); var o = Console.Out; Console.SetOut(w);
            Il.Dump(m); Console.SetOut(o);
            string key = m.Name.Substring(2, 2);
            if (!d.ContainsKey(key)) d[key] = new();
            d[key].Add(OpsOf(w.ToString().Split('\n', StringSplitOptions.RemoveEmptyEntries).Skip(1).ToArray()));
        }
        return d;
    }
    static void Main() {
        int n = 0, sameCalls = 0, sameOps = 0;
        Console.WriteLine(string.Join("\t", "꼴", "쿼리 구문의 System.Linq 호출 (IL 순서)", "메서드 구문과 호출 목록", "옵코드 열"));
        for (int i = 1; i <= 14; i++) {
            var a = Calls(typeof(Q), $"Q{i:00}"); var b = Calls(typeof(M), $"M{i:00}");
            bool eq = a.SequenceEqual(b), op = Ops(typeof(Q), $"Q{i:00}").SequenceEqual(Ops(typeof(M), $"M{i:00}"));
            n++; if (eq) sameCalls++; if (op) sameOps++;
            string[] cells = { $"Q{i:00}", string.Join(" → ", a), eq ? "같다" : "다르다: " + string.Join(" → ", b), op ? "같다" : "다르다" };
            if (cells.Length != 4) throw new Exception("칸 수 어긋남");
            Console.WriteLine(string.Join("\t", cells));
        }
        Console.WriteLine($"호출 목록이 같은 칸 {sameCalls} / {n}");
        Console.WriteLine($"옵코드 열까지 같은 칸 {sameOps} / {n}");
        var lq = LambdaBodies(typeof(Q)); var lm = LambdaBodies(typeof(M));
        int forms = 0, sameCount = 0, pairs = 0, sameBodies = 0;
        foreach (var k in lq.Keys.OrderBy(k => k, StringComparer.Ordinal)) {
            forms++;
            var a = lq[k]; var b = lm.GetValueOrDefault(k) ?? new();
            if (a.Count != b.Count) continue;
            sameCount++;
            foreach (var (x, y) in a.Zip(b)) { pairs++; if (x.SequenceEqual(y)) sameBodies++; }
        }
        Console.WriteLine($"람다 본문 — 람다 개수가 같은 꼴 {sameCount} / {forms} · 그 안에서 옵코드 열이 같은 람다 {sameBodies} / {pairs}");
        foreach (var t in typeof(Q).Assembly.GetTypes().Where(t => t.Name.Contains("AnonymousType")))
            Console.WriteLine($"q34.dll 에 컴파일러가 만든 타입 {t.Name} · 속성 {string.Join(", ", t.GetProperties().Select(p => p.Name))}");
        Il.Dump(typeof(Q), "Q02");
        Il.Dump(typeof(Q), "Q03");
    }
}
===== csc -optimize -r:il.dll -r:q34.dll -out:exo.dll cs34b-il.cs && dotnet exo.dll (cc exit=0 · run exit=0) =====
꼴	쿼리 구문의 System.Linq 호출 (IL 순서)	메서드 구문과 호출 목록	옵코드 열
Q01	Where<Int32> → Select<Int32,Int32>	같다	같다
Q02	Where<Int32>	같다	같다
Q03	Select<Int32,Int32>	같다	같다
Q04	Select<Int32,<>f__AnonymousType0<Int32,Int32>> → Where<<>f__AnonymousType0<Int32,Int32>> → Select<<>f__AnonymousType0<Int32,Int32>,Int32>	같다	같다
Q05	SelectMany<Int32,Int32,Int32>	같다	같다
Q06	OrderByDescending<Int32,Int32> → ThenBy<Int32,Int32>	같다	같다
Q07	GroupBy<Int32,Int32>	같다	같다
Q08	GroupBy<Int32,Int32,Int32>	같다	같다
Q09	Join<Int32,Int32,Int32,Int32>	같다	같다
Q10	GroupJoin<Int32,Int32,Int32,Int32>	같다	같다
Q11	Cast<Int32> → Select<Int32,Int32>	같다	같다
Q12	Select<Int32,Int32> → Where<Int32>	같다	같다
Q13	Where<Int32>	다르다: Where<Int32> → Select<Int32,Int32>	다르다
Q14	OrderBy<Int32,Int32> → OrderBy<Int32,Int32>	같다	같다
호출 목록이 같은 칸 13 / 14
옵코드 열까지 같은 칸 13 / 14
람다 본문 — 람다 개수가 같은 꼴 13 / 14 · 그 안에서 옵코드 열이 같은 람다 25 / 25
q34.dll 에 컴파일러가 만든 타입 <>f__AnonymousType0`2 · 속성 x, y
--- Q.Q02 ---
  IL_0000: ldsfld Q::xs
  IL_0005: ldsfld Q+<>c::<>9__4_0
  IL_000a: dup
  IL_000b: brtrue.s IL_0024
  IL_000d: pop
  IL_000e: ldsfld Q+<>c::<>9
  IL_0013: ldftn Q+<>c::<Q02>b__4_0
  IL_0019: newobj System.Func<System.Int32,System.Boolean>::.ctor
  IL_001e: dup
  IL_001f: stsfld Q+<>c::<>9__4_0
  IL_0024: call System.Linq.Enumerable::Where<System.Int32>
  IL_0029: ret
--- Q.Q03 ---
  IL_0000: ldsfld Q::xs
  IL_0005: ldsfld Q+<>c::<>9__5_0
  IL_000a: dup
  IL_000b: brtrue.s IL_0024
  IL_000d: pop
  IL_000e: ldsfld Q+<>c::<>9
  IL_0013: ldftn Q+<>c::<Q03>b__5_0
  IL_0019: newobj System.Func<System.Int32,System.Int32>::.ctor
  IL_001e: dup
  IL_001f: stsfld Q+<>c::<>9__5_0
  IL_0024: call System.Linq.Enumerable::Select<System.Int32,System.Int32>
  IL_0029: ret
```

**왜 그런가**

- ★★★ **쿼리 구문은 절마다 정해진 이름의 메서드 호출로 바뀐다** — 스크립트가 손으로 쓴 메서드 구문과 견줘 **호출 목록 13 / 14 · 옵코드 열 13 / 14** 가 같았다(갈린 하나는 대조군 Q13).
- ★★ **Q05** 두 `from` 은 결과 선택자가 있는 **`SelectMany`(타입 인자 셋)** 하나 · **Q10** `join … into` 는 **`GroupJoin`** · **Q11** `from int x` 는 **`Cast<Int32>`** 가 앞에 붙는다 · **Q14** `orderby` 두 번은 **`OrderBy` 두 번**.

### 2. ★★★ **컴파일되고 돈다** — `[1]` · `Box.Where 불림` · `Box.Select 불림` · ``[2] 결과 타입 Box`1 · Value = 42`` · `[3] … = False`

**출력**

```text
===== 소스: cs34b-user.cs =====
using System;
class Box<T> {
    public readonly T Value;
    public Box(T v) { Value = v; }
    public Box<U> Select<U>(Func<T, U> f) { Console.WriteLine("  Box.Select 불림"); return new Box<U>(f(Value)); }
    public Box<T> Where(Func<T, bool> p) { Console.WriteLine("  Box.Where 불림"); return p(Value) ? this : new Box<T>(default!); }
}
class Program {
    static void Main() {
        var b = new Box<int>(21);
        Console.WriteLine("[1] from x in b where x > 10 select x * 2");
        var r = from x in b where x > 10 select x * 2;
        Console.WriteLine($"[2] 결과 타입 {r.GetType().Name} · Value = {r.Value}");
        Console.WriteLine($"[3] b is System.Collections.IEnumerable = {b is System.Collections.IEnumerable}");
    }
}
===== csc -nullable:enable -out:ex.dll cs34b-user.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
[1] from x in b where x > 10 select x * 2
  Box.Where 불림
  Box.Select 불림
[2] 결과 타입 Box`1 · Value = 42
[3] b is System.Collections.IEnumerable = False
```

**왜 그런가**

- ★★★ 쿼리 구문은 먼저 `b.Where(…).Select(…)` 로 **바꿔 쓰이고**, 그 뒤 **보통의 메서드 호출**로 해석된다. `Box<T>` 에 그 **이름의 인스턴스 메서드**가 있으니 된다 — `IEnumerable` 도 `System.Linq` 도 필요 없다.

### 3. ★★★ **막힌 칸 17 / 18** — `Only<int>` 의 `select` 만 `ok` · `List<int>` 열은 **`CS1935`** · `Only<int>`·`int` 열은 **`CS1936`** · ★ **`orderby` 행은 셋 다 `CS1061` 이고 열 38**(다른 행은 열 28)

**출력**

```text
===== 소스: cs34b-miss.cs =====
using System;
using System.Collections.Generic;
class Only<T> { public Only<U> Select<U>(Func<T, U> f) => new Only<U>(); }
class P {
    static void M(Only<int> o, List<int> l, int n) {
        var a1 = from x in o select x + 1;                       // cell select Only<int>
        var a2 = from x in l select x + 1;                       // cell select List<int>
        var a3 = from x in n select x + 1;                       // cell select int
        var b1 = from x in o where x > 1 select x;               // cell where Only<int>
        var b2 = from x in l where x > 1 select x;               // cell where List<int>
        var b3 = from x in n where x > 1 select x;               // cell where int
        var c1 = from x in o orderby x select x;                 // cell orderby Only<int>
        var c2 = from x in l orderby x select x;                 // cell orderby List<int>
        var c3 = from x in n orderby x select x;                 // cell orderby int
        var d1 = from x in o group x by x;                       // cell group Only<int>
        var d2 = from x in l group x by x;                       // cell group List<int>
        var d3 = from x in n group x by x;                       // cell group int
        var e1 = from x in o from y in o select x + y;           // cell from-from Only<int>
        var e2 = from x in l from y in l select x + y;           // cell from-from List<int>
        var e3 = from x in n from y in n select x + y;           // cell from-from int
        var f1 = from x in o join y in o on x equals y select x; // cell join Only<int>
        var f2 = from x in l join y in l on x equals y select x; // cell join List<int>
        var f3 = from x in n join y in n on x equals y select x; // cell join int
    }
    static void Main() { }
}
===== csc -out:ex.dll cs34b-miss.cs 2>&1 | sort (cc exit=1) =====
cs34b-miss.cs(10,28): error CS1935: Could not find an implementation of the query pattern for source type 'List<int>'.  'Where' not found.  Are you missing required assembly references or a using directive for 'System.Linq'?
cs34b-miss.cs(11,28): error CS1936: Could not find an implementation of the query pattern for source type 'int'.  'Where' not found.
cs34b-miss.cs(12,38): error CS1061: 'Only<int>' does not contain a definition for 'OrderBy' and no accessible extension method 'OrderBy' accepting a first argument of type 'Only<int>' could be found (are you missing a using directive or an assembly reference?)
cs34b-miss.cs(13,38): error CS1061: 'List<int>' does not contain a definition for 'OrderBy' and no accessible extension method 'OrderBy' accepting a first argument of type 'List<int>' could be found (are you missing a using directive or an assembly reference?)
cs34b-miss.cs(14,38): error CS1061: 'int' does not contain a definition for 'OrderBy' and no accessible extension method 'OrderBy' accepting a first argument of type 'int' could be found (are you missing a using directive or an assembly reference?)
cs34b-miss.cs(15,28): error CS1936: Could not find an implementation of the query pattern for source type 'Only<int>'.  'GroupBy' not found.
cs34b-miss.cs(16,28): error CS1935: Could not find an implementation of the query pattern for source type 'List<int>'.  'GroupBy' not found.  Are you missing required assembly references or a using directive for 'System.Linq'?
cs34b-miss.cs(17,28): error CS1936: Could not find an implementation of the query pattern for source type 'int'.  'GroupBy' not found.
cs34b-miss.cs(18,28): error CS1936: Could not find an implementation of the query pattern for source type 'Only<int>'.  'SelectMany' not found.
cs34b-miss.cs(19,28): error CS1935: Could not find an implementation of the query pattern for source type 'List<int>'.  'SelectMany' not found.  Are you missing required assembly references or a using directive for 'System.Linq'?
cs34b-miss.cs(20,28): error CS1936: Could not find an implementation of the query pattern for source type 'int'.  'SelectMany' not found.
cs34b-miss.cs(21,28): error CS1936: Could not find an implementation of the query pattern for source type 'Only<int>'.  'Join' not found.
cs34b-miss.cs(22,28): error CS1935: Could not find an implementation of the query pattern for source type 'List<int>'.  'Join' not found.  Are you missing required assembly references or a using directive for 'System.Linq'?
cs34b-miss.cs(23,28): error CS1936: Could not find an implementation of the query pattern for source type 'int'.  'Join' not found.
cs34b-miss.cs(7,28): error CS1935: Could not find an implementation of the query pattern for source type 'List<int>'.  'Select' not found.  Are you missing required assembly references or a using directive for 'System.Linq'?
cs34b-miss.cs(8,28): error CS1936: Could not find an implementation of the query pattern for source type 'int'.  'Select' not found.
cs34b-miss.cs(9,28): error CS1936: Could not find an implementation of the query pattern for source type 'Only<int>'.  'Where' not found.
===== python3 cellgrid.py cs34b-miss.cs <위 진단> — 칸마다 진단 코드 =====
식 \ 자리           Only<int>        List<int>        int
select           ok               CS1935           CS1936
where            CS1936           CS1935           CS1936
orderby          CS1061           CS1061           CS1061
group            CS1936           CS1935           CS1936
from-from        CS1936           CS1935           CS1936
join             CS1936           CS1935           CS1936
막힌 칸 17 / 18
```

**왜 그런가**

- ★★★ **`CS1936`** — 번역된 이름(`Where`·`GroupBy`·`SelectMany`·`Join`·`Select`)이 원본 타입에 **없다.** **`CS1935`** — 같은 사정인데 원본이 **`IEnumerable<T>`** 라서 「`System.Linq` 를 `using` 했나」 힌트가 붙었다.
- ★★ **`orderby` 는 쿼리 패턴 진단을 안 거치고** 보통의 `CS1061`(멤버 없음)로 나왔고, 위치도 원본(열 28)이 아니라 **정렬 키**(열 38)다 — Roslyn 의 진단 설계다(규칙 18-C: 열이 근거).

### 4. ★★ **`[9, 8] · 4 · [9, 8]`** · 둘째는 **`CS0742` + `CS1002` 셋**(5행) · **`CS0742`**(6행)

**출력**

```text
===== 소스: cs34b-mix.cs =====
using System;
using System.Linq;
class Program {
    static void Main() {
        int[] xs = { 5, 3, 8, 1, 9, 2 };
        var top2 = (from x in xs where x > 2 orderby x descending select x).Take(2).ToList();
        int n = (from x in xs where x % 2 == 1 select x).Count();
        var same = xs.Where(x => x > 2).OrderByDescending(x => x).Take(2).ToList();
        Console.WriteLine($"[{string.Join(", ", top2)}] · {n} · [{string.Join(", ", same)}]");
    }
}
===== csc -out:ex.dll cs34b-mix.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
[9, 8] · 4 · [9, 8]
===== 소스: cs34b-kw.cs =====
using System.Linq;
class P {
    static void Main() {
        int[] xs = { 1, 2, 3 };
        var a = from x in xs where x > 1 take 2 select x;
        var b = from x in xs where x > 1;
    }
}
===== csc -out:ex.dll cs34b-kw.cs (cc exit=1) =====
cs34b-kw.cs(5,42): error CS0742: A query body must end with a select clause or a group clause
cs34b-kw.cs(5,42): error CS1002: ; expected
cs34b-kw.cs(5,47): error CS1002: ; expected
cs34b-kw.cs(5,49): error CS1002: ; expected
cs34b-kw.cs(6,41): error CS0742: A query body must end with a select clause or a group clause
```

**왜 그런가**

- ★★ 쿼리 구문에는 `Take`·`Count` 칸이 없다 — **괄호로 묶어 메서드 구문을 잇는다.** 같은 뜻의 메서드 사슬과 결과가 같다.
- ★★ `take` 는 절 낱말이 아니다 — 파서는 `where x > 1` 뒤에서 쿼리가 끝났다고 보고 「`select`/`group` 으로 끝나야 한다」(`CS0742`)를 낸다. `select` 없이 끝낸 둘째 줄도 같은 `CS0742`.

### 5. ★★★ **Q02 의 `select x` 는 사라졌고(`Where` 하나) · Q03 의 `select x` 는 `Select(x => x)` 로 남았다**

- ★★★ `where` 뒤의 `select x` 는 원소를 그대로 내니 **할 일이 없어 빠진다.** 그런데 **`from x in xs select x` 에서 그것까지 빼면 쿼리의 결과가 `xs` 그 자체**가 된다 — 호출자가 **원본 배열을 손에 쥐고 고칠 수 있게** 된다. 퇴화 쿼리가 `Select` 를 남기는 까닭으로 읽힌다(★ 명세 문장은 이 배치에서 안 열었다 — 관찰은 IL 의 「남았다」까지).

### 6. ★★ **`y` 는 익명 타입 ``<>f__AnonymousType0`2`` 의 속성**(속성 `x, y`) — 뒤의 절은 `t => t.y` 로 읽는다

- ★★ `let` 은 **`Select(x => new { x, y = x * 2 })`** 로 번역되어 두 값을 한 상자에 담는다. 속성 이름은 **쿼리의 변수 이름**(`x`·`let` 의 `y`)이다. 상자를 담은 변수(**투명 식별자**)는 소스에 안 보이고, `where y > 2` 는 **`t.y > 2`** 가 된다.

### 7. ★★★ **비교기가 「다른 것을 다르다고」 말하는지 보는 대조군이다** — 없으면 「같은 칸 13 / 13」이 **비교기가 늘 「같다」를 내는 고장**과 구분되지 않는다

- ★★★ 규칙 22 — **「0 건」이 결론인 격자일수록 그 0 이 진짜인지 따로 물어야 한다.** Q13 이 **`다르다`** 를 받았기 때문에 나머지 열셋의 **`같다`** 가 근거가 된다.

### 8. ★★★ **IL 이 같으므로 두 구문의 런타임이 다를 재료가 없다 — 제4의 상태(「잴 것이 없다」)**

- ★★★ 대조군을 뺀 **옵코드 열 13 / 13 · 람다 본문 25 / 25** 가 같다. 같은 옵코드를 같은 차례로 도는 두 메서드의 시간을 재면 **잡음만 잰다.** 「쿼리 구문이 느리다」는 **재서 반박하는 것이 아니라 IL 로 성립하지 않는다.**

### 9. ★★ **같은 모양이다 — 둘 다 「이름을 찾는 번역」**

- ★★ **바꿔 쓰기** — `foreach` 는 `GetEnumerator()`·`MoveNext()`·`Current` 로, 쿼리 구문은 `Where(…)`·`Select(…)` 로 바꿔 쓴다. 이 단계는 **인터페이스를 모른다.**
- ★★ **메서드 찾기** — 바꿔 쓴 문장을 **보통의 호출 해석**으로 푼다. 인스턴스 메서드가 있으면 그것, 없으면 확장 메서드([30번](../30-extension-methods-and-extension-members/)). [31번](../31-ienumerable-and-foreach/) (1)의 `foreach` 도, 2번의 `Box<T>` 도 **인스턴스 메서드**로 풀렸다.

### 10. ★★ **`join`·`let`·두 `from` 은 쿼리 구문 · `Take`·`Count` 로 끝나면 메서드 구문** — **성능과는 관계없다**(8번) · 쿼리 구문의 결과는 **33번 격자의 `Where`·`Select` 칸 — 지연**

- ★★ 판단의 근거는 **람다·익명 타입을 손으로 쓰는 양**뿐이다. IL 이 같다.
- ★ 쿼리 구문은 `Where`·`Select` 등을 **부를 뿐**이므로 [33번](../33-linq-method-syntax-and-deferred-execution/) (1)의 그 칸 그대로다 — **호출 직후 0 줄.** `orderby`·`group` 이 들어가면 33번의 **「첫 `MoveNext` 에서 끝까지」** 칸이다.

## 실행 검증

| 무엇 | 몇 번·어디서 | 결과 |
|---|---|---|
| `cs34b-q.cs` + `cs34b-il.cs` | csc 2회(`-optimize` · 라이브러리 + 실행 파일) · 실행 1회 | ★★★ **호출 목록 13 / 14 · 옵코드 열 13 / 14 · 람다 본문 25 / 25** · 익명 타입 `x, y` |
| `cs34b-user.cs` | csc 1회 · 실행 1회 | ★★★ `Box.Where 불림` → `Box.Select 불림` · `IEnumerable` 아님 |
| `cs34b-miss.cs` | csc 1회(`sort`) + cellgrid 1회 | ★★★ **막힌 칸 17 / 18** · `CS1935`·`CS1936`·`CS1061` |
| `cs34b-mix.cs` · `cs34b-kw.cs` | csc 2회 · 실행 1회 | `[9, 8] · 4 · [9, 8]` · `CS0742`·`CS1002` |
| `cs34b-form.cs` | csc 1회 · 실행 1회 | `kim:30! kim:5 park:10!` · `1=35 3=10` |
| `cs34b-v2.cs` | csc 2회(`-langversion:2` · `3`) | `CS8023 … 'query expression'` · 통과 |

**구현 의존 항목** — 다음은 **이 판(.NET SDK 10.0.401 의 Roslyn)에서만** 그렇다.

- ★★ 익명 타입·람다 캐시 필드의 **이름** · **`CS1935`/`CS1936` 의 갈림과 `orderby` 의 `CS1061`** · 진단 문구.

**언어가 보장하는 것**(구현이 바뀌어도 같다)

- **쿼리 구문이 메서드 호출로 번역된다 · 절마다 부르는 이름 · 이름으로 찾는다 · 퇴화 쿼리가 `Select` 를 남긴다 · `let` 이 익명 타입으로.** ★ 명세 **문장**은 이 배치에서 안 열었다 — 보장이라고 적은 근거는 **IL 이 그 번역대로라는 것**과, 번역이 언어 기능이라는 2번의 증거다.

**안 돌려 본 것 / 못 잰 것 / 잴 것이 없는 것**

- **안 돌려 본 것** — ★ `join` 의 복합 키.
- **못 잰 것** — ★★ **명세 원문**(외부 네트워크를 안 썼다 — 절 번호 미확인).
- **잴 것이 없는 것** — ★★★ **할당 바이트 · 시간** — IL 이 같다(8번).

**버전이 올랐을 때 다시 돌려야 하는 것**

- ★★ **3번** — 진단 설계가 바뀌면(예: `orderby` 도 쿼리 패턴 진단으로) 격자가 바뀐다. **1번**은 언어 규칙이라 바뀌지 않아야 한다 — 바뀌면 그것이 뉴스다.
