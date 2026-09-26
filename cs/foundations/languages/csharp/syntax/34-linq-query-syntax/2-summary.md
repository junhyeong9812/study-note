# csharp/syntax/34 — LINQ 쿼리 구문 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [ECMA-334 7판(2023-12)](https://ecma-international.org/publications-and-standards/standards/ecma-334/) 의 「Query expressions」 절 — ★★★ **이 배치는 외부 네트워크를 쓰지 않아 그 절을 열지 못했다. 절 번호도 확인하지 않았다**(제3의 상태 — 「못 연 것」).\
> 그래서 **번역 규칙은 명세 문장을 인용하지 않고 컴파일러로 증명한다** — 쿼리 구문 열네 꼴과 손으로 쓴 메서드 구문을 **같은 `csc` 로 컴파일해 IL 의 호출 목록을 기계로 견줬다**((1)). 명세가 「이렇게 번역한다」고 말하는 대신, **번역된 결과가 이것과 한 글자도 같다**를 보인다.
> **실행 검증** — 이 문서의 모든 출력·진단·IL 은 아래 「이 판」의 도구로 **실제로 돌려 얻은 것**이다(2026-09-26). 블록은 캡처 스크립트가 파일로 받아 조립기가 끼워 넣었다.
> **버전** — 쿼리 구문 **C# 3** — ★ 이 판에서 `-langversion:2` 가 **`CS8023 … 'query expression' … 3 or greater`** 로 확인해 줬다 · `3` 은 통과((7)).
> **경계** — ★★★ **각 연산자가 즉시냐 지연이냐 · 몇 줄 읽나**는 [33번](../33-linq-method-syntax-and-deferred-execution/)이 정본이다 — 쿼리 구문은 **같은 메서드를 부르므로**((1)) 33번의 격자가 그대로 적용된다. 여기는 **「무엇으로 번역되나」 하나**다.\
> ★★ **「이름만 맞으면 된다」는 [31번](../31-ienumerable-and-foreach/) (1)의 패턴 기반 `foreach` 와 같은 모양**이다 — 인터페이스가 아니라 **메서드 이름**을 찾는다((3)).
> ★★★ **본체 창은 ① IL 호출 목록 격자다** — 번역은 **컴파일 시점**에 일어나고 실행 결과로는 안 보인다(두 구문이 같은 값을 내는 것은 번역의 **증거가 못 된다**). IL 이 **무엇을 부르나**만이 번역을 드러낸다.
>
> ★★ **흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | 진단 **문구** · 진단 **순서**(배너에 `sort`) · IL **오프셋** | ★★★ **진단 코드**(`CS1935`·`CS1936`·`CS1061`·`CS0742`·`CS1002`) · 진단의 **(행,열)** |
> | ★ 컴파일러가 지은 **이름의 숫자**(`<>9__5_0` · `<Q02>b__5_0` · `AnonymousType0`) — Roslyn 구현 | ★★★ **`System.Linq` 호출 목록과 그 순서** · **「호출 목록이 같은 칸 N / M」 · 「옵코드 열까지 같은 칸 N / M」 · 「람다 본문 … N / M」** |
> | — | 익명 타입의 **속성 이름**(`x, y`) · 실행 결과 |

## 이 판

```text
===== dotnet --version && dotnet --list-runtimes | grep NETCore (exit=0) =====
10.0.401
Microsoft.NETCore.App 10.0.12 [/home/jun/.local/opt/dotnet/shared/Microsoft.NETCore.App]
===== javac -version (exit=0) =====
javac 21.0.5
===== java -version (exit=0) =====
openjdk version "21.0.5" 2024-10-15 LTS
OpenJDK Runtime Environment Temurin-21.0.5+11 (build 21.0.5+11-LTS)
OpenJDK 64-Bit Server VM Temurin-21.0.5+11 (build 21.0.5+11-LTS, mixed mode, sharing)
```

## 이 갈래가 쓰는 세 층

| 층 | 뜻 | 이 주제에서 근거로 쓰는 것 |
|---|---|---|
| **언어 명세(ECMA-334)** | ★★★ C# 언어가 약속한 것 — ★ **이 배치는 문장을 안 열었다** | ★★★ **쿼리 구문을 메서드 호출로 바꿔 쓰는 번역** 그 자체 · 절마다 **어느 이름**을 부르나(`where`→`Where` · `from…from`→`SelectMany` · `join…into`→`GroupJoin` · `let`→`Select` + 익명 타입) · **번역은 이름으로 찾는다**(인터페이스 불필요) · 퇴화 쿼리의 `Select` |
| **컴파일러 구현(Roslyn)** | ★★ 그것을 **어떻게 적나** | ★★ 익명 타입 이름 **``<>f__AnonymousType0`2``** · 람다 캐시 필드 `<>9__N_M` · ★★ **`orderby` 만 `CS1061` 로 보고하는 것**((4)) · 진단 문구 |
| **BCL(System.Linq)** | 라이브러리 | ★ 번역이 도착한 **`Enumerable.Where` 등 그 자체** — 동작은 [33번](../33-linq-method-syntax-and-deferred-execution/) |
| **이 판의 관찰** | .NET 10.0.12 · Roslyn(SDK 10.0.401) | 진단 문구 |

★★★ **이 주제의 층 구분이 급소다 —**\
**쿼리 구문은 BCL 기능이 아니라 언어 기능이다.** `System.Linq` 는 번역이 **도착하는 곳**일 뿐이다 — 그 증거가 (3)이다: **`System.Linq` 를 `using` 하지 않고, `IEnumerable` 도 아닌 사용자 타입**에 쿼리 구문이 통했다.

## 한눈에 — 쉽게 말하면

**쿼리 구문은 「서식이 정해진 주문 양식」이다 — 컴파일러가 양식의 칸(`from`·`where`·`select`)을 읽어 메서드 호출 문장으로 **바꿔 쓴 뒤에야** 그 문장을 컴파일한다. 바꿔 쓸 때는 **이름**만 본다.**

- **양식 → 문장** — `from x in xs where x > 1 select x * 2` 는 `xs.Where(x => x > 1).Select(x => x * 2)` 로 바뀐다. **IL 이 한 글자도 같다**(옵코드 열까지 — (1)).
- **이름만 본다** — 바꿔 쓴 문장에 `.Where(…)` 가 있으면 **`Where` 라는 메서드를 찾을 뿐**이다. `IEnumerable` 이 아니어도, `System.Linq` 가 없어도 **그 이름이 있으면 된다**((3)).
- **빈칸 채우기(`let`)** — 중간 값을 이름 붙여 두면 컴파일러가 **익명 타입 `{ x, y }`** 를 만들어 두 값을 한 상자에 넣고 흘려보낸다((1) Q04).
- **양식에 없는 칸** — `Take`·`Count`·`Distinct` 는 **양식에 칸이 없다.** 괄호로 묶고 점으로 잇는다((5)).
- **이름이 없으면** — 「이 양식을 받아 줄 메서드가 없다」는 **`CS1936`**, `IEnumerable` 인데 `using System.Linq` 가 없으면 힌트가 붙은 **`CS1935`**((4)).

| 비유 | 실체 | 어디서 보나 |
|---|---|---|
| 양식을 문장으로 | ★★★ 열네 꼴의 `System.Linq` 호출 목록이 손으로 쓴 메서드 구문과 **같은 칸 13 / 14**(Q13 은 일부러 다르게 쓴 대조군) | (1) |
| 한 글자도 같다 | ★★★ **옵코드 열까지 같은 칸 13 / 14** · **람다 본문 25 / 25** | (1) |
| 빈칸 채우기 | ★★★ `let` → **`Select<Int32,<>f__AnonymousType0<Int32,Int32>>`** · 속성 **`x, y`** | (1) |
| 이름만 본다 | ★★★ `System.Linq` 없는 `Box<T>` 에 **`Box.Where 불림` · `Box.Select 불림`** · `IEnumerable` 인가 **`False`** | (3) |
| 받아 줄 메서드가 없다 | ★★★ **`CS1936`**(`Only<int>`·`int`) · **`CS1935`**(`List<int>` — `System.Linq` 힌트) · ★ `orderby` 만 **`CS1061`** — **막힌 칸 17 / 18** | (4) |
| 양식에 없는 칸 | ★★ `(from … select x).Take(2)` · `take` 를 쓰면 **`CS0742`** | (5) |

★★★ **이 주제의 본체 그림 — 절마다 무엇으로 바뀌나((1) 이 IL 로 확인한 것).**

```text
   쿼리 구문                                           번역된 메서드 호출 (IL 의 System.Linq 호출 순서)
   ────────────────────────────────────────           ─────────────────────────────────────────────────────
   from x in xs where x > 1 select x * 2               xs.Where(x => x > 1).Select(x => x * 2)          Q01
   from x in xs where x > 1 select x                   xs.Where(x => x > 1)                ← select 가 사라짐   Q02
   from x in xs select x                               xs.Select(x => x)                   ← select 가 남음     Q03
   from x in xs let y = x * 2 where y > 2 select y     xs.Select(x => new { x, y = x * 2 })                  Q04
                                                         .Where(t => t.y > 2).Select(t => t.y)
   from x in xs from y in ys select x + y              xs.SelectMany(x => ys, (x, y) => x + y)             Q05
   orderby x descending, x % 2                         .OrderByDescending(x => x).ThenBy(x => x % 2)       Q06
   orderby x orderby x % 2                             .OrderBy(x => x).OrderBy(x => x % 2)  ← 뒤가 덮는다   Q14
   group x by x % 2          /  group x * 10 by …      .GroupBy(x => x % 2)  /  .GroupBy(k, x => x * 10)   Q07 Q08
   join y in ys on x equals y select …                 .Join(ys, x => x, y => y, (x, y) => …)              Q09
   join y in ys on x equals y into g select …          .GroupJoin(ys, x => x, y => y, (x, g) => …)         Q10
   from int x in objs select x                         objs.Cast<int>().Select(x => x)                     Q11
   … select x into z where z > 1 select z              xs.Select(x => x).Where(z => z > 1)                 Q12

   ★★★ 번역은 「이 이름의 메서드를 이 인자로 불러라」 까지다. 그 메서드가 Enumerable 의 것인지는 번역이 모른다 — (3).
```

## 이 주제가 답하려는 질문

1. **쿼리 구문의 각 절은 어떤 메서드 호출로 번역되나 — 손으로 쓴 메서드 구문과 IL 이 같은가**((1)).
2. **번역은 무엇을 찾나** — 인터페이스인가 이름인가((3)) · **없으면 무엇이 나나**((4)).
3. **쿼리 구문으로 못 쓰는 것은 어떻게 섞나**((5)) · **어느 쪽이 읽기 쉬운 자리인가**((6)).

## 동작 방식

### (0) 이 주제가 쓰는 창

★★★ **본체 창은 ① IL 호출 목록 격자다.**

| 창 | 무엇을 보여 주나 | 이 주제에서 |
|---|---|---|
| ★★★ **① IL 호출 목록** | ★★★ 쿼리 구문 메서드와 메서드 구문 메서드의 **`call System.Linq.Enumerable::…` 목록 · 옵코드 열 · 람다 본문 옵코드 열**을 스크립트가 견줘 **N / M** | (1) |
| ★★ **③ 리플렉션** | ★★ 컴파일러가 만든 **익명 타입**과 그 속성 이름 | (1) |
| ★★★ **② 진단 격자** | ★★★ 절 여섯 × 원본 타입 셋 — **`CS1935`/`CS1936`/`CS1061`** · `CS0742` · 판 경계 `CS8023` | (4)(5)(7) |
| ★★ **실행 로그** | ★★ 사용자 타입의 **`Box.Where 불림`** — 번역이 **그 메서드**에 도착했다 | (3) |
| **④ 할당 바이트 · 시간** | ★★★ **잴 것이 없다(제4의 상태)** — (1)에서 대조군을 뺀 **옵코드 열 13 / 13 · 람다 본문 25 / 25** 가 같았다. 두 구문의 런타임이 **다를 재료가 IL 에 없다.** 「쿼리 구문이 느리다」는 **재서 반박할 것이 아니라 IL 로 성립하지 않는다** | — |
| **부적용인 창** | 위의 ④ | — |

### (1) ★★★ 본체 — 열네 꼴의 IL 호출 목록 격자

**언제 쓰나** — 「`from … join … into` 는 **무엇을 부르나**」 · 「쿼리 구문과 메서드 구문은 **다른 코드**가 되나」.

★ 쿼리 구문은 `cs34b-q.cs` 에만 있고(라이브러리 `q34.dll`), 메서드 구문 짝과 비교기는 `cs34b-il.cs` 에 있다. **Q13 은 대조군** — Q02 와 **같은 쿼리**인데 짝을 일부러 `.Where(…).Select(x => x)` 로 썼다. 비교기가 **다른 것을 다르다고 말하는지** 보려는 칸이다(규칙 22 — 「0 건」이 결론인 격자는 그 0 이 진짜인지 물어야 한다).

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

- ★★★ **호출 목록이 같은 칸 13 / 14 · 옵코드 열까지 같은 칸 13 / 14** — 갈린 하나는 **대조군 Q13** 이다(`Where<Int32>` 대 `Where<Int32> → Select<Int32,Int32>`). 비교기는 **다른 것을 다르다고** 말했다. 나머지 열셋은 **호출 목록도, 옵코드의 차례도** 같다.
- ★★★ **람다 본문 — 람다 개수가 같은 꼴 13 / 14 · 그 안에서 옵코드 열이 같은 람다 25 / 25** — 개수가 다른 하나는 대조군(M13 의 `Select(x => x)` 가 하나 더)이다. 람다의 **몸까지** 같은 코드가 됐다.
- ★★★ **Q02 `from x in xs where x > 1 select x` → `Where` 하나 · Q03 `from x in xs select x` → `Select` 하나** — 앞에 `where` 가 있으면 끝의 `select x` 는 **아무 일도 안 하므로 빠진다.** 그런데 **`select x` 만 있는 쿼리는 `Select(x => x)` 를 남긴다**(아래 IL). 빼면 쿼리의 결과가 **`xs` 그 자체**가 되어 호출자가 원본 배열을 손에 쥐게 되기 때문으로 읽힌다(명세의 문장은 안 열었다 — 관찰은 「남았다」까지).
- ★★★ **Q04 `let` → `Select<Int32,<>f__AnonymousType0<Int32,Int32>>` 로 시작** — `x` 와 `y` 를 **한 상자**에 담아 흘려보낸다. 스크립트가 찍은 **``q34.dll 에 컴파일러가 만든 타입 <>f__AnonymousType0`2 · 속성 x, y``** 가 그 상자다. 이 상자를 **투명 식별자**라고 부른다 — 쿼리 뒤쪽에서는 `t.y` 가 아니라 그냥 `y` 로 보인다.
- ★★ **Q05 두 `from` → `SelectMany` 하나(타입 인자 셋 — 결과 선택자가 있는 판)** · **Q10 `join … into` → `GroupJoin`** · **Q11 `from int x` → `Cast<Int32>` 뒤 `Select`** · **Q12 `into` → 앞 쿼리를 통째로 새 `from` 의 원본으로.**
- ★★ **Q06 `orderby x descending, x % 2` → `OrderByDescending` → `ThenBy`** — **쉼표 뒤의 키가 `ThenBy`** 다. [33번](../33-linq-method-syntax-and-deferred-execution/) 형태의 「`OrderBy` 를 두 번 이으면 덮어쓴다」를 피하는 꼴이 쿼리 구문에서는 **쉼표 하나**다· ★★ **Q14 `orderby x orderby x % 2` → `OrderBy` → `OrderBy`** — 절을 **두 번** 쓰면 쿼리 구문에서도 **덮어쓰기**가 그대로 난다(진단 없음).

```text
   Q04 — let 은 무엇이 되나 (IL 의 호출 목록을 풀어 쓴 것)

   from x in xs                         xs
   let y = x * 2                          .Select(x => new { x, y = x * 2 })        ← <>f__AnonymousType0<Int32,Int32>
   where y > 2                            .Where(t => t.y > 2)                      ← 투명 식별자 t — 소스에는 안 보인다
   select y                               .Select(t => t.y)

   ★ 소스의 y 는 변수처럼 보이지만 실제로는 「상자의 속성」 이다. 상자 이름은 Roslyn 이 짓는다(숫자는 흔들리는 칸).
```

### (2) ★★ 퇴화 쿼리 — Q02 와 Q03 의 IL

위 블록 끝의 두 덤프가 그것이다 — **Q02 는 `call Enumerable::Where<Int32>` 에서 끝나고**, **Q03 은 `call Enumerable::Select<Int32,Int32>` 로 끝난다.** 둘 다 람다를 `<>9__N_0` 필드에 **캐시**한다(Roslyn 구현 — [28번](../28-lambdas-and-closure-capture/) (1)의 캡처 없는 람다와 같은 모양).

### (3) ★★★ 번역은 이름으로 찾는다 — `System.Linq` 없는 사용자 타입

**언제 쓰나** — 「쿼리 구문은 **`IEnumerable` 전용**인가」 · 「내 타입에 쿼리 구문을 쓰게 할 수 있나」.

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

- ★★★ **`using System.Linq` 가 없다 · `Box<T>` 는 `IEnumerable` 이 아니다(`[3]` `False`) — 그런데 쿼리 구문이 컴파일되고 돈다.** 번역된 문장 `b.Where(x => x > 10).Select(x => x * 2)` 에서 **`Where`·`Select` 라는 이름의 인스턴스 메서드**를 찾았고, 있었다.
- ★★★ **`Box.Where 불림` → `Box.Select 불림` 순** — (1)의 Q01 과 **같은 차례**다. 결과 타입은 **``Box`1``**, 값은 **`42`**.
- ★★ **이것이 「쿼리 구문은 언어 기능」의 증거다** — [31번](../31-ienumerable-and-foreach/) (1)에서 `foreach` 가 **인터페이스 없이 `GetEnumerator` 이름**만으로 된 것과 같은 모양이다. 두 언어 기능 모두 **이름을 찾는 번역**이다.

```text
   컴파일러가 하는 일 — 두 단계

   ① 바꿔 쓰기 (이름을 모른다)              ② 보통 메서드 호출로 컴파일 (이름을 찾는다)
   from x in b where x > 10 select x * 2      b.Where(…)   → 인스턴스 메서드 Box<int>.Where ✓
        │                                        .Select(…) → 인스턴스 메서드 Box<int>.Select ✓
        └──▶ b.Where(x => x > 10)                        (없으면 확장 메서드 — System.Linq 가 using 이면 Enumerable.Where)
                .Select(x => x * 2)
   ★ ① 에는 IEnumerable 도 System.Linq 도 없다. ② 는 보통의 메서드 호출 해석이다 — 30편의 확장 메서드 규칙이 여기서 쓰인다.
```

### (4) ★★★ 이름이 없으면 — 절 여섯 × 원본 타입 셋

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

- ★★★ **막힌 칸 17 / 18** — 통과한 것은 **`Only<int>` 의 `select`** 하나다. `Only<T>` 는 `Select` 만 가졌다.
- ★★★ **`CS1936` — 「원본 타입에 대한 쿼리 패턴 구현을 못 찾았다 · `'Where' not found`」** — `Only<int>` 와 `int` 가 이것이다. **어느 이름**이 없는지를 문구가 말한다(`Where` · `GroupBy` · `SelectMany` · `Join` · `Select`).
- ★★★ **`CS1935` — 같은 문구 + 「`System.Linq` 의 `using` 지시문이 빠졌나?」** — `List<int>` 열 전부다. 컴파일러가 **`IEnumerable` 을 알아보고** 힌트를 더 줬다. 코드가 둘로 갈리는 것이 **「이 타입은 LINQ 대상일 법하다」를 컴파일러가 가른 흔적**이다.
- ★★★ **`orderby` 행만 세 열 전부 `CS1061` — 그리고 열이 38 이다** — 다른 행은 전부 **(행,28)**(원본 식 `o`·`l`·`n` 의 자리)을 가리키는데, `orderby` 는 **(행,38)**(정렬 키 `x` 의 자리)을 가리키며 **보통의 「멤버가 없다」** 진단을 냈다. `orderby` 의 번역은 쿼리 패턴 진단을 거치지 않고 **바로 `OrderBy` 호출로 해석**되는 것으로 읽힌다(Roslyn 구현 — 규칙 18-C: **열 번호가 근거**다).

### (5) ★★ 쿼리 구문으로 못 쓰는 연산자 — 섞어 쓰는 꼴 · 없는 낱말

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

- ★★★ **`(from … select x).Take(2).ToList()` → `[9, 8]` · `(from … select x).Count()` → `4`** — 쿼리 구문에는 `Take`·`Count` 칸이 없다. **괄호로 묶어 메서드 구문을 잇는다.** 같은 뜻의 메서드 구문(`same`)과 결과가 같다.
- ★★★ **`take 2` 를 절처럼 쓰면 `CS0742`**(「쿼리 몸통은 `select` 나 `group` 절로 끝나야 한다」) + **`CS1002`**(`;` 가 필요하다) 셋 — 파서는 `take` 를 **절로 모른다.** `where x > 1` 뒤에서 쿼리가 끝났다고 보고, 끝이 `select` 가 아니라서 `CS0742` 를 냈다. **`select` 없는 쿼리(`b`)도 같은 `CS0742`** 다.

### (6) ★★ 어느 쪽이 읽기 쉬운 자리인가 — 판단(재지 않은 것)

★★★ **이 절은 판단이다** — 가독성은 재지 않았다. (1)에서 **두 구문의 IL 이 같으므로** 고르는 기준은 **읽는 사람 쪽**뿐이다.

| 자리 | 쿼리 구문이 짧아지는 까닭 | 메서드 구문이 짧아지는 까닭 |
|---|---|---|
| **`join`** | ★★ `on p.Id equals o.PersonId` — 키 선택자 둘과 결과 선택자를 **절로** 쓴다. 메서드 구문은 람다 셋 | — |
| **`let`** | ★★ 중간 값에 이름 — 메서드 구문은 **익명 타입을 손으로** 만들어야 한다(Q04 의 `M04`) | — |
| **두 `from`** | ★★ `from x … from y …` — 메서드 구문은 `SelectMany` 의 **두 람다** | — |
| **`Take`·`Count`·`First`·`Distinct`** | — | ★★ 쿼리 구문에 **칸이 없다** — 괄호로 묶어야 한다((5)) |
| **`Where` 하나 · `Select` 하나** | — | ★ `xs.Where(x => x > 1)` 한 줄이면 된다 |
| **사용자 확장 메서드를 잇기** | — | ★ 쿼리 구문은 **정해진 이름**만 번역한다 |

### (7) ★ 판 경계 — `-langversion:2` 와 `3`

```text
===== 소스: cs34b-v2.cs =====
using System.Collections.Generic;
using System.Linq;
class P {
    static void Main() {
        int[] xs = { 1, 2, 3 };
        IEnumerable<int> q = from x in xs where x > 1 select x;
    }
}
===== csc -langversion:2 -out:ex.dll cs34b-v2.cs (cc exit=1) =====
cs34b-v2.cs(6,30): error CS8023: Feature 'query expression' is not available in C# 2. Please use language version 3 or greater.
===== csc -langversion:3 -out:ex.dll cs34b-v2.cs (cc exit=0) =====
```

- ★★ **`2` → `CS8023 … 'query expression' …` 한 줄(6,30) · `3` → 통과** — 쿼리 구문은 **C# 3** 이다. 쿼리 안의 람다(`x > 1`)는 **따로 진단이 안 나왔다** — 쿼리 식 하나로 보고됐다. [33번](../33-linq-method-syntax-and-deferred-execution/) (6)의 메서드 구문 쪽은 **람다**가 막혔다.

## 문법 — 형태와 규칙

### 형태

```text
===== 소스: cs34b-form.cs =====
using System;
using System.Linq;

var people = new[] { (Id: 1, Name: "kim"), (Id: 2, Name: "lee"), (Id: 3, Name: "park") };
var orders = new[] { (PersonId: 1, Amount: 30), (PersonId: 3, Amount: 10), (PersonId: 1, Amount: 5) };

var report =
    from p in people
    join o in orders on p.Id equals o.PersonId
    let big = o.Amount >= 10
    orderby p.Name, o.Amount descending
    select $"{p.Name}:{o.Amount}{(big ? "!" : "")}";
Console.WriteLine(string.Join(" ", report));

var byPerson =
    from o in orders
    group o.Amount by o.PersonId into g
    select $"{g.Key}={g.Sum()}";
Console.WriteLine(string.Join(" ", byPerson));
===== csc -out:ex.dll cs34b-form.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
kim:30! kim:5 park:10!
1=35 3=10
```

- ★★★ **`from 변수 in 원본`** 으로 시작해 **`select` 나 `group … by …`** 로 끝난다 — 끝이 없으면 `CS0742`((5)).
- ★★★ **`join … in … on 바깥키 equals 안쪽키`** — `==` 가 아니라 **`equals`** 이고, **왼쪽이 바깥**이다. `join … into g` 면 `GroupJoin`.
- ★★ **`let 이름 = 식`** — 뒤의 모든 절에서 보인다(투명 식별자).
- ★★ **`orderby 키1, 키2 descending`** — 쉼표가 `ThenBy` 다.
- ★★ **`group 원소 by 키 into g`** — `into` 로 **이어 쓰기**. 둘째 줄의 `1=35 3=10` 이 그것이다.

### 금지 사례 — 진단이 나는 꼴

| 쓴 꼴 | 진단 코드 | 어디서 |
|---|---|---|
| 원본 타입에 번역된 메서드가 없음 | `CS1936` | (4) |
| `IEnumerable<T>` 인데 `using System.Linq` 가 없음 | `CS1935` | (4) |
| `orderby` 인데 `OrderBy` 가 없음 | `CS1061`(★ 쿼리 패턴 진단이 아니다) | (4) |
| `select`/`group` 으로 끝나지 않는 쿼리 · 없는 절 낱말(`take`) | `CS0742` | (5) |
| C# 2 에서 쿼리 구문 | `CS8023` | (7) |
| ★★★ 쿼리 구문과 메서드 구문의 속도 차이를 기대 | ★★★ **진단 없음 · 차이 없음** — IL 이 같다 | (1) |

## 어디서 틀리나

1. ★★★ **「쿼리 구문은 메서드 구문과 다른 코드가 된다(그래서 느리다/빠르다)」** — 대조군을 빼면 **옵코드 열까지 같다 13 / 13 · 람다 본문 25 / 25**((1)).
2. ★★★ **「쿼리 구문은 `IEnumerable` 전용이다」** — **이름만 있으면 된다.** `System.Linq` 없이 사용자 타입에 통했다((3)).
3. ★★★ **「`select x` 는 늘 `Select(x => x)` 가 된다」** — `where` 뒤에서는 **빠지고**, `select x` 만 있는 쿼리에서만 **남는다**((1) Q02·Q03).
4. ★★ **「`let` 은 지역 변수다」** — **익명 타입의 속성**이다(`<>f__AnonymousType0` · `x, y`)((1) Q04).
5. ★★ **「`join` 의 `equals` 는 `==` 로 써도 된다」** — `equals` 다. 양쪽 순서도 **바깥 먼저**다(형태).
6. ★★ **「`orderby` 를 두 번 쓰면 두 키로 정렬된다」** — `OrderBy` → `OrderBy`, **뒤가 덮는다.** 쉼표를 써라((1) Q14).
7. ★★ **「`Take`·`Count` 도 절로 쓸 수 있다」** — `CS0742`. 괄호로 묶어 잇는다((5)).
8. ★ **「쿼리 패턴이 없으면 늘 `CS1936`」** — `IEnumerable` 이면 `CS1935`, **`orderby` 는 `CS1061`**((4)).

## 구현 세부사항 대 언어 보장

| 무엇 | 층 | 근거 |
|---|---|---|
| **쿼리 구문이 메서드 호출로 번역된다 · 절마다 부르는 이름** | ★★★ **언어**(명세의 번역 규칙 — ★ 문장은 안 열었다. **IL 로 증명**) | (1) |
| **번역은 이름으로 찾는다 · 인터페이스 불필요** | ★★★ **언어** | (3) |
| **`where` 뒤의 `select x` 는 빠지고, 홀로 선 `select x` 는 남는다** | ★★★ **언어**(퇴화 쿼리 규칙) — 관찰은 IL | (1)(2) |
| **`let` 이 익명 타입(투명 식별자)으로 번역된다** | ★★★ **언어** · 타입 **이름**(``<>f__AnonymousType0`2``)은 ★ **Roslyn** | (1) |
| **람다 캐시 필드 `<>9__N_M`** | ★ **Roslyn 구현** | (2) |
| **`CS1935` 와 `CS1936` 의 갈림 · `orderby` 의 `CS1061`** | ★★ **Roslyn 구현**(진단 설계) | (4) |
| **번역이 도착한 `Enumerable` 메서드의 동작(지연 등)** | ★★ **BCL** — [33번](../33-linq-method-syntax-and-deferred-execution/) | — |

## 언제 쓰고 언제 안 쓰나

- ★★★ **`join`·`let`·여러 `from` 이 들어가면 쿼리 구문** — 람다 셋·익명 타입을 손으로 안 써도 된다((6)).
- ★★★ **`Where`/`Select` 하나 · `Take`·`Count`·`First` 로 끝나면 메서드 구문** — 쿼리 구문은 괄호로 묶어야 한다((5)).
- ★★ **섞어 써도 된다** — `(from … select …).Take(2)` 는 **같은 메서드 사슬**이다((5)). 한 파일 안에서 한쪽으로 고집할 **기술적 이유가 없다**((1)).
- ★★ **도메인 타입에 쿼리 구문을 주고 싶으면 `Select`/`Where`/`SelectMany` 이름의 메서드를 둬라**((3)) — ★ 다만 그것은 **「LINQ 연산자처럼 동작한다」는 약속을 읽는 사람에게 주는 것**이니, 이름의 뜻을 지켜라(판단).

## 핵심 문장

1. ★★★ **쿼리 구문은 컴파일러가 메서드 호출로 바꿔 쓰는 언어 기능이다 — IL 의 호출 목록 13 / 14(대조군 하나), 옵코드 열까지 13 / 14, 람다 본문 25 / 25 가 같다**((1)).
2. ★★★ **번역은 이름으로 찾는다 — `System.Linq` 도 `IEnumerable` 도 없이 `Where`/`Select` 를 가진 타입에 통한다**((3)).
3. ★★★ **`let` 은 익명 타입으로, 두 `from` 은 `SelectMany` 로, `join … into` 는 `GroupJoin` 으로 — 홀로 선 `select x` 만 `Select` 를 남긴다**((1)).
4. ★★ **이름이 없으면 `CS1936`, `IEnumerable` 이면 `CS1935`, `orderby` 는 `CS1061` — 막힌 칸 17 / 18**((4)).
5. ★★ **두 구문은 같은 코드이므로 고르는 기준은 읽는 사람뿐이다**((6)).

## 관련 자료

- [33번 — LINQ 메서드 구문과 지연 실행](../33-linq-method-syntax-and-deferred-execution/) — **경계**: 연산자가 즉시냐 지연이냐는 거기. 쿼리 구문은 **같은 메서드**를 부르므로 그 격자를 그대로 쓴다.
- [31번 — `IEnumerable<T>` 와 `foreach`](../31-ienumerable-and-foreach/) (1) — 이름 기반 패턴의 짝(`GetEnumerator`).
- [30번 — 확장 메서드](../30-extension-methods-and-extension-members/) — 번역된 호출이 `Enumerable` 에 도착하는 길.
- [28번 — 람다와 캡처](../28-lambdas-and-closure-capture/) (1) — 캡처 없는 람다의 `<>9__` 캐시.
- 다음 — [35번 — 그룹·조인·집계](../35-linq-grouping-joins-and-aggregation/)(`group`·`join` 의 결과 모양) · [36번 — `IQueryable`](../36-iqueryable-and-expression-trees/)(같은 쿼리 구문이 `Queryable` 에 도착하면).

## 용어 풀이

- **쿼리 구문(query syntax)** — `from … where … select …` 꼴. 컴파일러가 메서드 호출로 바꿔 쓴다.
- **메서드 구문(method syntax)** — `xs.Where(…).Select(…)` 꼴. 쿼리 구문이 번역되어 도착하는 모양.
- **쿼리 패턴(query pattern)** — 번역이 찾는 메서드 이름의 모음(`Select`·`Where`·`SelectMany`·`Join`·`GroupJoin`·`OrderBy`·`ThenBy`·`GroupBy`·`Cast`).
- **퇴화 쿼리(degenerate query)** — `from x in xs select x` 처럼 원소를 그대로 내는 쿼리. `Select(x => x)` 를 남긴다.
- **투명 식별자(transparent identifier)** — `let`·두 `from`·`join` 뒤에 컴파일러가 만든 익명 타입 변수. 소스에는 안 보인다.
- **`CS1935` / `CS1936`** — 쿼리 패턴 구현을 못 찾았다는 진단. 앞쪽은 `System.Linq` 힌트가 붙는다.

## 더 들어가면

- ★ **명세의 번역 규칙 원문** — 이 배치는 외부 네트워크를 안 써서 **절 번호도 문장도 확인하지 않았다.** 다음 판에서 열어 (1)의 표와 대조할 자리다.
