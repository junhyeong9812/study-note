# csharp/syntax/35 — LINQ 그룹·조인·집계 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — ★ **SDK 참조 팩의 XML 문서** `System.Linq.xml`(로컬에서 열어 확인):\
> `ToLookup` 의 반환 「**각 묶음 안의 값은 `source` 의 순서와 같다**」 · `Aggregate`(시드 없음)의 예외 「`source` 에 원소가 없으면 **`InvalidOperationException`**」 · `Average(int)`·`Max(int)` 도 같은 조항 · `First` 「원본 시퀀스가 비었으면 `InvalidOperationException`」 ·\
> ★★ `MaxBy` 의 예외 「**`TSource` 가 기본형이고 원본이 비었으면** `InvalidOperationException`」 · `Average(int?)` 의 반환 「원본이 비었거나 전부 `null` 이면 **`null`**」 ·\
> ★★★ **제네릭 `Max<T>` 는 빈 입력에 대해 아무 조항이 없다**(예외는 `ArgumentNullException` · `ArgumentException` 둘뿐) — (5)의 `string[] Max()` → `null` 은 **문서가 침묵하는 칸의 관찰**이다.\
> `LeftJoin` 의 반환 「두 시퀀스에 **왼쪽 외부 조인**을 해서 얻은 원소」(이 판에서 호출해 확인 · 같은 XML 에 `RightJoin` 도 있다).
> ★ **이 배치는 외부 네트워크를 쓰지 않았다** — Learn 의 개념 문서는 열지 않았다.
> **실행 검증** — 이 문서의 모든 출력은 아래 「이 판」의 도구로 **실제로 돌려 얻은 것**이다(2026-09-26). 블록은 캡처 스크립트가 파일로 받아 조립기가 끼워 넣었다.
> **버전** — ★ 이 머신의 참조 팩은 **10.0.12 하나뿐**이라 연산자마다 **언제 들어왔나는 확인하지 못했다**(못 잰 것). 이 문서가 말하는 것은 **이 판(.NET 10)에 전부 있다**까지다 — `CountBy`·`MaxBy`·`LeftJoin` 처럼 새로 보이는 것도 판 경계는 적지 않는다.
> **경계** — ★★★ **「지연 쿼리를 두 번 열거하면 소스를 두 번 읽는다」 는 [32번](../32-yield-return-iterators-and-deferred-execution/) (7)이 쟀다** — 여기서는 **그룹 결과**에서 같은 일이 나는지, 그리고 **`ToLookup` 이 그것을 어떻게 막나**를 본다((2)).\
> ★★ `GroupBy` 가 첫 `MoveNext` 에서 **끝까지** 읽는 것은 [33번](../33-linq-method-syntax-and-deferred-execution/) (1)이 정본이다. `group … by`·`join … into` 가 무엇으로 번역되나는 [34번](../34-linq-query-syntax/) (1)이다.\
> ★ 집계의 **원리**(해시로 묶기)는 `cs/data-structure/` 쪽 몫이다. 여기는 **연산자가 무엇을 돌려주나**만 본다.
> ★★★ **본체 창은 둘이다 — ⑤ 실행 로그(「언제 · 몇 번 읽나」)와 ② 빈 입력 결과 격자(「비었을 때 무엇을 주나」).** 둘 다 **값으로만** 보인다 — IL 은 아무 말도 안 한다(전부 보통의 메서드 호출이다).
>
> ★★ **흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | 예외 **문구**(`Sequence contains no elements` · `Index was out of range…`) — 판에 매인다 | ★★★ 예외 **타입** · **「던진 칸 N / M」** · 값(`0` · `null` · `[0]`) |
> | — | ★★★ **로그의 줄 수와 순서**(`Load 본문 #N` · `O:start O:1 I:start …`) · 묶음의 **키 순서와 원소 순서** |

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
| **언어 명세(ECMA-334)** | C# 언어가 약속한 것 | ★ `group … by`·`join … into` 의 **번역**([34번](../34-linq-query-syntax/)) — 이 주제의 동작 자체는 **언어가 아니다** |
| **BCL 계약(XML 문서)** | ★★★ 문서가 약속한 것 | ★★★ **빈 입력의 예외 조항**(`Aggregate`·`Average`·`Max(int)`·`First` → `InvalidOperationException` · `MaxBy` 는 「기본형일 때」) · `Average(int?)` 의 `null` · `ToLookup` 의 **원소 순서** |
| **BCL 구현(System.Linq 10.0.12)** | ★★ 그것을 **어떻게 짰나** | ★★ `GroupBy` 의 **키 순서 = 처음 나온 순서** · ★★★ **`Join` 이 첫 `MoveNext` 에서 바깥 하나를 본 뒤 안쪽을 끝까지 읽는 것** · 바깥이 비면 **안쪽을 안 여는 것** · `string[] Max()` → `null`(문서 침묵) |
| **이 판의 관찰** | .NET 10.0.12 · linux-x64 | 예외 문구 |

★★★ **이 주제의 층 구분이 급소다 —**\
**빈 입력 격자((5))의 칸은 셋으로 갈린다 — 문서가 「던진다」고 약속한 칸 · 문서가 「`null`」 을 약속한 칸 · 문서가 침묵하는 칸.** 앞의 둘은 계약이고, 마지막은 **이 판의 관찰**이다. 같은 `null` 이라도 `int?[] Average()` 와 `string[] Max()` 는 **근거의 세기가 다르다.**

## 한눈에 — 쉽게 말하면

**`GroupBy` 는 「분류 요령이 적힌 쪽지」, `ToLookup` 은 「이미 분류해 놓은 서랍장」이다 — 쪽지는 볼 때마다 원본 더미를 처음부터 다시 분류하고, 서랍장은 만들 때 한 번 분류해 두고 계속 연다.**

- **쪽지(`GroupBy`)** — 만들 때 더미를 **안 본다**(지연). `foreach` 할 때마다 **처음부터 다시 분류**한다 — 두 번 돌면 원본을 **두 번** 읽는다((2)).
- **서랍장(`ToLookup`)** — 만드는 **그 자리에서** 더미를 끝까지 분류한다(즉시). 그 뒤로는 원본을 **다시 안 본다.** 없는 서랍을 열면 **빈 서랍**이 나온다(예외가 아니다)((1)).
- **짝 맞추기(`Join`)** — 오른쪽 더미를 **한 번 통째로** 서랍장으로 만들어 두고, 왼쪽을 하나씩 들고 가서 맞는 서랍을 연다. 짝이 없는 쪽은 **사라진다**((3)(4)).
- **빈 더미를 합치면(`Aggregate`·`Sum`·`Max`)** — 「0 부터 더해라」처럼 **시작값이 있으면** 시작값이 답이다. 시작값 없이 「첫 장부터 합쳐라」면 **첫 장이 없어서** 던진다((5)).

| 비유 | 실체 | 어디서 보나 |
|---|---|---|
| 쪽지는 볼 때마다 다시 | ★★★ `GroupBy` 결과를 `foreach` 둘 + `Count()` → **`Load 본문` 3 번** | (2) |
| 서랍장은 한 번 | ★★★ `ToLookup` → **만드는 줄에서 1 번** · 그 뒤 `foreach` 둘 + `Count` 는 **0 번** | (2) |
| 빈 서랍 | ★★ `lk[4].Count()` → **`0`** · `lk.Contains(4)` → **`False`** · `GroupBy` 결과에는 키 4 가 **아예 없다** | (1) |
| 오른쪽을 통째로 | ★★★ 첫 `MoveNext` 로그 **`O:start O:1 I:start I:2 I:3 I:3 I:4 I:end O:2`** · 바깥이 비면 **`I:` 0 줄** | (3) |
| 짝 없는 쪽은 사라진다 | ★★ `Join` 에 `lee` 가 없다 · `LeftJoin`·`GroupJoin + DefaultIfEmpty` 에는 `lee-(없음)` | (4) |
| 시작값이 없으면 던진다 | ★★★ 빈 입력 **던진 칸 10 / 22** · 시드 없는 `Aggregate` **던짐** · 시드 있는 판 **`0`** · `Sum` **`0`** | (5) |

★★★ **이 주제의 본체 그림 — 「몇 번 읽나」 두 가지.**

```text
   GroupBy (지연 — 쪽지)                               ToLookup (즉시 — 서랍장)
   ────────────────────────────────                    ────────────────────────────────
   var g = Load().GroupBy(k)     Load 0 번              var lk = Load().ToLookup(k)   Load 1 번 ← 여기서 끝까지
   foreach (… in g)              Load +1 (끝까지)       foreach (… in lk)             +0
   foreach (… in g)              Load +1 (처음부터)     foreach (… in lk)             +0
   g.Count()                     Load +1                lk.Count                      +0
                                 ───────                                              ───────
                                 3 번                                                 1 번

   Join(outer, inner)  — 첫 MoveNext 하나에서
   ─────────────────────────────────────────────────────────────────────────────
   O:start O:1  →  I:start I:2 I:3 I:3 I:4 I:end  →  O:2  → 첫 결과 2-2
   바깥 하나를 보고    안쪽을 통째로 읽어 서랍장으로       바깥을 다시 한 칸씩
   ★ 바깥이 비면 안쪽은 한 번도 안 열린다 ((3) [4])

   ★★★ 「여러 번 열거된다」 는 GroupBy 의 결함이 아니라 지연의 성질이다 — 32편 (7)과 같은 뿌리. 막으려면 즉시 쪽(ToLookup · ToList)으로 굳힌다.
```

## 이 주제가 답하려는 질문

1. **`GroupBy` 의 결과는 어떤 모양인가** — 키 순서 · 원소 순서 · 없는 키((1)).
2. **그룹 결과는 왜 여러 번 열거되나 — `ToLookup` 과 무엇이 다른가**((2)) · **`Join` 은 안쪽을 언제 · 몇 번 읽나**((3)).
3. **조인의 모양** — 내부 · 그룹 · 왼쪽 외부 두 꼴 · `Zip`((4)).
4. **빈 입력에서 누가 던지고 누가 값을 주나**((5)).

## 동작 방식

### (0) 이 주제가 쓰는 창

★★★ **본체 창은 ⑤ 실행 로그 + ② 빈 입력 결과 격자다.**

| 창 | 무엇을 보여 주나 | 이 주제에서 |
|---|---|---|
| ★★★ **⑤ 실행 로그** | ★★★ `Load 본문 #N`(소스를 몇 번 읽었나) · 바깥/안쪽 소스의 `start`·원소·`end` 순서 | (2)(3) |
| ★★★ **② 빈 입력 결과 격자** | ★★★ 22 칸 — 값 또는 예외 타입·문구 · **「던진 칸 N / M」** | (5) |
| ★★ **실행 결과** | ★★ 묶음의 키·원소 순서 · 조인 결과의 모양 | (1)(4) |
| **① IL 덤프** | ★ **잴 것이 없다** — 전부 `call Enumerable::…` 한 줄씩이다. 동작은 **라이브러리 안**에 있다 | — |
| **④ 할당 바이트** | ★ **안 쟀다** — 질문이 「몇 번 읽나」다(로그가 답한다) | — |
| **부적용인 창** | ① | — |

### (1) ★★ `GroupBy` 의 모양 — 키 순서 · 없는 키 · 원소 순서

```text
===== 소스: cs35b-group.cs =====
using System;
using System.Linq;
class Program {
    static void Main() {
        string[] words = { "bb", "a", "ccc", "d", "ee", "fffff", "g" };
        Console.WriteLine("[1] words.GroupBy(w => w.Length)");
        foreach (var g in words.GroupBy(w => w.Length))
            Console.WriteLine($"    키 {g.Key} : [{string.Join(", ", g)}]");
        var lk = words.ToLookup(w => w.Length);
        Console.WriteLine($"[2] lk.Count = {lk.Count} · lk.Contains(4) = {lk.Contains(4)} · lk[4].Count() = {lk[4].Count()}");
        var counts = words.CountBy(w => w.Length).Select(p => $"{p.Key}:{p.Value}");
        Console.WriteLine($"[3] CountBy : {string.Join(" ", counts)}");
    }
}
===== csc -out:ex.dll cs35b-group.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
[1] words.GroupBy(w => w.Length)
    키 2 : [bb, ee]
    키 1 : [a, d, g]
    키 3 : [ccc]
    키 5 : [fffff]
[2] lk.Count = 4 · lk.Contains(4) = False · lk[4].Count() = 0
[3] CountBy : 2:2 1:3 3:1 5:1
```

- ★★★ **키 순서가 `2 · 1 · 3 · 5`** — 정렬이 아니라 **키가 처음 나온 순서**다(`bb` 가 첫 원소라 2 가 먼저). ★ **이 판의 관찰** — XML 문서의 `GroupBy` 반환 조항은 「키와 원소 시퀀스를 가진 `IGrouping` 들」까지만 말한다.
- ★★★ **원소 순서도 원본 순서** — 키 1 은 `[a, d, g]`(원본에서 나온 차례). `ToLookup` 은 이것을 **문서가 약속**한다(「각 묶음 안의 값은 `source` 의 순서와 같다」).
- ★★★ **키 4 는 없다** — 길이 4 인 낱말이 없으니 **빈 묶음이 생기지 않는다.** `GroupBy` 는 **있는 키만** 만든다.
- ★★ **`[2]` `lk[4].Count()` → `0` · `lk.Contains(4)` → `False`** — `ILookup` 에 없는 키를 물으면 **빈 시퀀스**를 준다. `Dictionary` 의 `KeyNotFoundException` 과 **다르다.** 그래서 「키가 있나」는 **`Contains`** 로 물어야 한다(`Count() == 0` 은 「있는데 비었다」와 구분이 안 된다 — 다만 위처럼 `GroupBy`·`ToLookup` 은 빈 묶음을 안 만든다).
- ★ **`[3]` `CountBy`** — 묶음을 만들지 않고 **키별 개수**만. 키 순서가 `GroupBy` 와 같다.

### (2) ★★★ 본체 — 그룹 결과를 두 번 돌면 · `GroupBy` 대 `ToLookup`

**언제 쓰나** — 「`GroupBy` 결과를 변수에 두고 **두 군데서** 썼더니 DB 를 두 번 읽었다」.

```text
===== 소스: cs35b-twice.cs =====
using System;
using System.Collections.Generic;
using System.Linq;
class Program {
    static int reads;
    static IEnumerable<string> Load() {
        reads++;
        Console.WriteLine($"    Load 본문 #{reads}");
        yield return "bb"; yield return "a"; yield return "ccc"; yield return "d";
    }
    static void Main() {
        Console.WriteLine("[1] var g = Load().GroupBy(w => w.Length);");
        var g = Load().GroupBy(w => w.Length);
        Console.WriteLine("[2] foreach (var x in g) 첫째");
        foreach (var x in g) { }
        Console.WriteLine("[3] foreach (var x in g) 둘째");
        foreach (var x in g) { }
        Console.WriteLine("[4] g.Count()");
        _ = g.Count();
        Console.WriteLine($"    GroupBy 쪽 Load 본문 {reads} 번");
        reads = 0;
        Console.WriteLine("[5] var lk = Load().ToLookup(w => w.Length);");
        var lk = Load().ToLookup(w => w.Length);
        Console.WriteLine("[6] foreach (var x in lk) 첫째");
        foreach (var x in lk) { }
        Console.WriteLine("[7] foreach (var x in lk) 둘째");
        foreach (var x in lk) { }
        Console.WriteLine("[8] lk.Count");
        _ = lk.Count;
        Console.WriteLine($"    ToLookup 쪽 Load 본문 {reads} 번");
    }
}
===== csc -out:ex.dll cs35b-twice.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
[1] var g = Load().GroupBy(w => w.Length);
[2] foreach (var x in g) 첫째
    Load 본문 #1
[3] foreach (var x in g) 둘째
    Load 본문 #2
[4] g.Count()
    Load 본문 #3
    GroupBy 쪽 Load 본문 3 번
[5] var lk = Load().ToLookup(w => w.Length);
    Load 본문 #1
[6] foreach (var x in lk) 첫째
[7] foreach (var x in lk) 둘째
[8] lk.Count
    ToLookup 쪽 Load 본문 1 번
```

- ★★★ **`[1]` `GroupBy` 를 부른 뒤에는 `Load 본문` 0 줄** — 지연이다([33번](../33-linq-method-syntax-and-deferred-execution/) (1)의 `GroupBy` 칸).
- ★★★ **`[2]`·`[3]` `foreach` 두 번 → `#1` · `#2` · `[4]` `g.Count()` → `#3` — GroupBy 쪽 Load 본문 3 번.** `g` 는 묶음들을 **들고 있지 않다** — 「묶어라」는 **방법**을 들고 있다. 소비할 때마다 **원본을 처음부터 다시 읽어 다시 묶는다.** [32번](../32-yield-return-iterators-and-deferred-execution/) (7)의 「두 번 열거하면 두 번」이 **그룹 결과에서도 그대로**다.
- ★★★ **`[5]` `ToLookup` → 그 줄에서 `#1` · 그 뒤 `[6]`\~`[8]` 은 0 줄 — ToLookup 쪽 Load 본문 1 번.** `ToLookup` 은 **즉시** — 만들 때 끝까지 읽어 **서랍장을 채우고**, 그 뒤로는 원본을 안 본다.
- ★★ **`g.Count()` 도 읽는다** — 「묶음이 몇 개인가」를 알려면 **묶어 봐야** 한다. [33번](../33-linq-method-syntax-and-deferred-execution/) (2)의 `ICollection` 지름길은 `GroupBy` 결과에 **없다**(그것은 컬렉션이 아니다).

### (3) ★★★ `Join` 은 안쪽을 언제 읽나 — 바깥·안쪽 소스 로그

**언제 쓰나** — 「`Join` 의 **어느 쪽**이 한 번에 메모리로 올라오나」 · 「바깥이 비었는데 안쪽 쿼리가 나가나」.

```text
===== 소스: cs35b-join.cs =====
using System;
using System.Collections.Generic;
using System.Linq;
class Program {
    static readonly List<string> log = new();
    static IEnumerable<int> Traced(string tag, int[] xs) {
        log.Add($"{tag}:start");
        foreach (var x in xs) { log.Add($"{tag}:{x}"); yield return x; }
        log.Add($"{tag}:end");
    }
    static string Take() { var s = string.Join(" ", log); log.Clear(); return s; }
    static void Main() {
        int[] outer = { 1, 2, 3 }, inner = { 2, 3, 3, 4 };
        var j = Traced("O", outer).Join(Traced("I", inner), o => o, i => i, (o, i) => $"{o}-{i}");
        Console.WriteLine($"[1] Join 직후          : {Take()}");
        using var e = j.GetEnumerator();
        e.MoveNext();
        Console.WriteLine($"[2] 첫 MoveNext → {e.Current}  : {Take()}");
        var rest = new List<string>();
        while (e.MoveNext()) rest.Add(e.Current);
        Console.WriteLine($"[3] 나머지 {string.Join(" ", rest)}   : {Take()}");
        var none = Traced("O", new int[0]).Join(Traced("I", inner), o => o, i => i, (o, i) => o).ToList();
        Console.WriteLine($"[4] 바깥이 빈 Join → {none.Count} 개 : {Take()}");
    }
}
===== csc -out:ex.dll cs35b-join.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
[1] Join 직후          : 
[2] 첫 MoveNext → 2-2  : O:start O:1 I:start I:2 I:3 I:3 I:4 I:end O:2
[3] 나머지 3-3 3-3   : O:3 O:end
[4] 바깥이 빈 Join → 0 개 : O:start O:end
```

- ★★★ **`[1]` `Join` 직후 0 줄** — 지연이다.
- ★★★ **`[2]` 첫 `MoveNext` → `O:start O:1 I:start I:2 I:3 I:3 I:4 I:end O:2`** — 바깥에서 **하나(`O:1`)** 를 본 **뒤에** 안쪽을 **`start` 부터 `end` 까지 통째로** 읽었다. 그다음 바깥을 다시 한 칸씩(`O:2`) 당겨 첫 짝 `2-2` 를 냈다. **안쪽 = 한 번에 버퍼링 · 바깥 = 한 칸씩 흘림.**
- ★★★ **`[3]` 나머지 `3-3 3-3` → `O:3 O:end`** — 안쪽은 **다시 안 읽었다.** 안쪽에 `3` 이 둘이라 짝도 둘이다. 바깥 `1` 은 짝이 없어 **결과에 없다**(내부 조인).
- ★★★ **`[4]` 바깥이 빈 `Join` → `O:start O:end` — 안쪽 `I:` 0 줄.** 바깥에서 첫 원소를 **못 얻으면 안쪽을 열지도 않는다.** ★ 이 순서(바깥 한 칸 → 안쪽 전부)는 **BCL 구현**이다 — XML 문서는 조인의 **결과**만 말하고 읽는 순서는 말하지 않는다.

### (4) ★★ 조인의 모양 — 내부 · `GroupJoin` · 왼쪽 외부 두 꼴 · `Zip`

```text
===== 소스: cs35b-shape.cs =====
using System;
using System.Linq;
class Program {
    static void Main() {
        var people = new[] { (Id: 1, Name: "kim"), (Id: 2, Name: "lee"), (Id: 3, Name: "park") };
        var orders = new[] { (PersonId: 1, Item: "pen"), (PersonId: 3, Item: "cup"), (PersonId: 1, Item: "ink"), (PersonId: 9, Item: "box") };
        var inner = people.Join(orders, p => p.Id, o => o.PersonId, (p, o) => $"{p.Name}-{o.Item}");
        Console.WriteLine($"[1] Join            : {string.Join(" ", inner)}");
        var gj = people.GroupJoin(orders, p => p.Id, o => o.PersonId, (p, os) => $"{p.Name}[{string.Join(",", os.Select(o => o.Item))}]");
        Console.WriteLine($"[2] GroupJoin       : {string.Join(" ", gj)}");
        var left = people.GroupJoin(orders, p => p.Id, o => o.PersonId, (p, os) => (p, os))
                         .SelectMany(t => t.os.DefaultIfEmpty(), (t, o) => $"{t.p.Name}-{o.Item ?? "(없음)"}");
        Console.WriteLine($"[3] GroupJoin + DefaultIfEmpty : {string.Join(" ", left)}");
        var left10 = people.LeftJoin(orders, p => p.Id, o => o.PersonId, (p, o) => $"{p.Name}-{o.Item ?? "(없음)"}");
        Console.WriteLine($"[4] LeftJoin        : {string.Join(" ", left10)}");
        var zip = people.Zip(new[] { "A", "B" }, (p, g) => $"{p.Name}{g}");
        Console.WriteLine($"[5] Zip (3 개 · 2 개) : {string.Join(" ", zip)}");
    }
}
===== csc -out:ex.dll cs35b-shape.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
[1] Join            : kim-pen kim-ink park-cup
[2] GroupJoin       : kim[pen,ink] lee[] park[cup]
[3] GroupJoin + DefaultIfEmpty : kim-pen kim-ink lee-(없음) park-cup
[4] LeftJoin        : kim-pen kim-ink lee-(없음) park-cup
[5] Zip (3 개 · 2 개) : kimA leeB
```

- ★★★ **`[1]` `Join` — `kim-pen kim-ink park-cup`** — 주문이 없는 `lee` 가 **빠지고**, 사람이 없는 주문 `box`(9번) 도 **빠진다.** 양쪽 **짝이 있는 것만**(내부 조인). 결과 순서는 **바깥(`people`) 순서**, 한 사람 안에서는 **안쪽 순서**(`pen` 이 `ink` 보다 먼저).
- ★★★ **`[2]` `GroupJoin` — `kim[pen,ink] lee[] park[cup]`** — 바깥 원소마다 **한 줄**이고 짝을 **묶음으로** 준다. **`lee[]` — 빈 묶음이 있다.** (1)의 `GroupBy` 에는 빈 묶음이 **없었다** — 두 연산자가 여기서 갈린다.
- ★★★ **`[3]` `GroupJoin` + `SelectMany(… DefaultIfEmpty())` = `[4]` `LeftJoin` — 둘 다 `kim-pen kim-ink lee-(없음) park-cup`** — 빈 묶음에 **기본값 하나**를 넣어 펼치면 왼쪽 외부 조인이 된다. `LeftJoin` 은 **그 관용구를 한 메서드로** 준 것이다(결과가 한 글자도 같다).
- ★★ **`[5]` `Zip` — 3 개와 2 개 → `kimA leeB`** — 키가 아니라 **위치**로 짝짓고, **짧은 쪽**에서 멈춘다. `park` 는 사라진다(예외 없음).

### (5) ★★★ 빈 입력 격자 — 누가 던지고 누가 값을 주나

**언제 쓰나** — 「필터 결과가 비었을 때 `Max()` 가 **던지나 `0` 을 주나**」 · 「`Aggregate` 에 시드를 줘야 하나」.

```text
===== 소스: cs35b-empty.cs =====
using System;
using System.Collections;
using System.Linq;
class Program {
    static int n, threw;
    static void Cell(string name, Func<object?> f) {
        n++;
        string r;
        try {
            var v = f();
            r = v is null ? "null" : v is IEnumerable e && v is not string ? $"[{string.Join(",", e.Cast<object>())}]" : v.ToString()!;
        }
        catch (Exception e) { threw++; r = $"{e.GetType().Name} — {e.Message}"; }
        Console.WriteLine($"{name}\t{r}");
    }
    static void Main() {
        int[] e = { };
        string[] s = { };
        int?[] ni = { };
        Cell("int[] Sum()", () => e.Sum());
        Cell("int[] Count()", () => e.Count());
        Cell("int[] Average()", () => e.Average());
        Cell("int[] Max()", () => e.Max());
        Cell("int[] Min()", () => e.Min());
        Cell("int[] MaxBy(x => x)", () => e.MaxBy(x => x));
        Cell("int[] Aggregate((a, b) => a + b)", () => e.Aggregate((a, b) => a + b));
        Cell("int[] Aggregate(0, (a, b) => a + b)", () => e.Aggregate(0, (a, b) => a + b));
        Cell("int[] First()", () => e.First());
        Cell("int[] FirstOrDefault()", () => e.FirstOrDefault());
        Cell("int[] Single()", () => e.Single());
        Cell("int[] Last()", () => e.Last());
        Cell("int[] ElementAt(0)", () => e.ElementAt(0));
        Cell("string[] Max()", () => s.Max());
        Cell("string[] MaxBy(x => x.Length)", () => s.MaxBy(x => x.Length));
        Cell("string[] Aggregate((a, b) => a + b)", () => s.Aggregate((a, b) => a + b));
        Cell("int?[] Max()", () => ni.Max());
        Cell("int?[] Average()", () => ni.Average());
        Cell("int?[] Sum()", () => ni.Sum());
        Cell("int[] GroupBy(x => x).Count()", () => e.GroupBy(x => x).Count());
        Cell("int[] DefaultIfEmpty()", () => e.DefaultIfEmpty());
        Cell("int[] DefaultIfEmpty(-1)", () => e.DefaultIfEmpty(-1));
        Console.WriteLine($"던진 칸 {threw} / {n}");
    }
}
===== csc -nullable:enable -out:ex.dll cs35b-empty.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
int[] Sum()	0
int[] Count()	0
int[] Average()	InvalidOperationException — Sequence contains no elements
int[] Max()	InvalidOperationException — Sequence contains no elements
int[] Min()	InvalidOperationException — Sequence contains no elements
int[] MaxBy(x => x)	InvalidOperationException — Sequence contains no elements
int[] Aggregate((a, b) => a + b)	InvalidOperationException — Sequence contains no elements
int[] Aggregate(0, (a, b) => a + b)	0
int[] First()	InvalidOperationException — Sequence contains no elements
int[] FirstOrDefault()	0
int[] Single()	InvalidOperationException — Sequence contains no elements
int[] Last()	InvalidOperationException — Sequence contains no elements
int[] ElementAt(0)	ArgumentOutOfRangeException — Index was out of range. Must be non-negative and less than the size of the collection. (Parameter 'index')
string[] Max()	null
string[] MaxBy(x => x.Length)	null
string[] Aggregate((a, b) => a + b)	InvalidOperationException — Sequence contains no elements
int?[] Max()	null
int?[] Average()	null
int?[] Sum()	0
int[] GroupBy(x => x).Count()	0
int[] DefaultIfEmpty()	[0]
int[] DefaultIfEmpty(-1)	[-1]
던진 칸 10 / 22
```

- ★★★ **던진 칸 10 / 22** — 스크립트가 셌다.
- ★★★ **`int[]` 의 `Average()`·`Max()`·`Min()`·`MaxBy`·시드 없는 `Aggregate`·`First()`·`Single()`·`Last()` → `InvalidOperationException`**(`Sequence contains no elements`) — 「첫 원소」나 「시작값」이 있어야 답이 서는 연산이다. `ElementAt(0)` 만 **`ArgumentOutOfRangeException`**(위치가 범위 밖).
- ★★★ **값을 준 칸 — `Sum()` `0` · `Count()` `0` · 시드 있는 `Aggregate` `0`(시드 그대로) · `FirstOrDefault()` `0` · `GroupBy(…).Count()` `0` · `DefaultIfEmpty()` `[0]` · `DefaultIfEmpty(-1)` `[-1]`.** 합은 **항등원 0** 에서 시작하니 비어도 선다.
- ★★★ **같은 `Max`·`MaxBy` 가 타입에 따라 갈린다 — `int[]` 는 던지고 `string[]`·`int?[]` 는 `null`.** 참조형·널 허용 값형은 「없음」을 **`null` 로 말할 수 있어서**다. ★ 그런데 **근거의 세기가 다르다:**

```text
   빈 입력의 null — 누가 약속했나 (XML 문서를 열어 대조한 것)

   int?[] Average()          null     ← 문서가 약속: 「비었거나 전부 null 이면 null」
   int?[] Max()              null     ← 문서의 예외 조항에 빈 입력이 없다 (반환 조항도 빈 입력을 말하지 않는다)
   string[] Max()            null     ← 제네릭 Max<T> — 빈 입력에 대해 문서가 침묵 → 이 판의 관찰
   string[] MaxBy(…)         null     ← 문서가 「TSource 가 기본형이고 비었으면 던진다」 — 참조형은 그 조항 밖
   int[] MaxBy(…)            던짐      ← 그 조항 안 (기본형 + 빈 입력)
   string[] Aggregate(…)     던짐      ← 시드 없는 Aggregate 는 타입과 무관하게 「원소가 없으면」 던진다 (문서)

   ★★★ 같은 「null 이 나왔다」 라도 위 둘째·셋째 줄은 계약이 아니다. 기대려면 DefaultIfEmpty · 시드 · MaxBy 의 조항 쪽으로.
```

- ★★ **시드가 갈림길이다** — `Aggregate((a, b) => a + b)` 는 **첫 원소를 시작값**으로 쓰니 비면 던지고, `Aggregate(0, …)` 는 **`0` 을 시작값**으로 쓰니 비어도 `0` 이다. `Sum` 이 비어도 `0` 인 것과 같은 모양이다. ★ Java 는 같은 갈림을 **`Optional`** 로 준다 — 시드 없는 `reduce` 가 빈 스트림에서 `Optional.empty`([Java 46번](../../../java/syntax/46-terminal-operations/)). **C# 은 던지고 Java 는 비어 있음을 값으로 준다.**

## 문법 — 형태와 규칙

### 형태

```text
===== 소스: cs35b-form.cs =====
using System;
using System.Linq;

int[] xs = { 3, 1, 4, 1, 5 };
Console.WriteLine(xs.Aggregate((acc, x) => acc - x));
Console.WriteLine(xs.Aggregate("", (acc, x) => acc + x));
Console.WriteLine(xs.Aggregate(0, (acc, x) => acc + x, acc => $"합 {acc}"));
var byParity = xs.GroupBy(x => x % 2 == 0 ? "짝" : "홀", (k, g) => $"{k}:{g.Sum()}");
Console.WriteLine(string.Join(" ", byParity));
===== csc -out:ex.dll cs35b-form.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
-8
31415
합 14
홀:10 짝:4
```

- ★★★ **`Aggregate(func)`** — 첫 원소가 시작값(`3 - 1 - 4 - 1 - 5 = -8`) · **`Aggregate(seed, func)`** — 시드가 시작값이고 **누적 타입이 원소 타입과 달라도 된다**(`""` 에 이어 붙여 `31415`) · **`Aggregate(seed, func, resultSelector)`** — 끝에 한 번 바꾼다(`합 14`).
- ★★ **`GroupBy(키, (키, 묶음) => 결과)`** — 결과 선택자를 주면 `IGrouping` 대신 **바로 결과**를 준다(`홀:10 짝:4` — 키 순서는 처음 나온 순서).

### 금지 사례 — 진단 없이 틀리는 꼴

| 쓴 꼴 | 무엇이 나나 | 어디서 |
|---|---|---|
| 빈 입력에 시드 없는 `Aggregate` · `Max()` · `Average()` · `First()` | ★★★ `InvalidOperationException` — **컴파일러는 모른다** | (5) |
| ★★★ `GroupBy` 결과를 변수에 두고 여러 번 소비 | ★★★ **진단 없음** — 원본을 **소비 횟수만큼** 읽는다 | (2) |
| ★★ `Join` 으로 「주문 없는 사람도」 기대 | ★★ **진단 없음** — 짝 없는 쪽이 **사라진다** | (4) |
| ★★ `Zip` 에 길이가 다른 두 시퀀스 | ★★ **진단 없음 · 예외 없음** — 짧은 쪽에서 멈춘다 | (4) |
| ★ `lookup[없는키]` 로 「키가 있나」 판단 | ★ **예외 없음** — 빈 시퀀스. `Contains` 를 써라 | (1) |

## 어디서 틀리나

1. ★★★ **「`GroupBy` 결과는 묶음들을 들고 있다」** — **묶는 방법**을 들고 있다. 소비할 때마다 원본을 다시 읽는다(3 번)((2)).
2. ★★★ **「`ToLookup` 은 `GroupBy` 의 다른 이름이다」** — **즉시**다. 만드는 줄에서 끝까지 읽고 그 뒤 0 번((2)).
3. ★★★ **「`Join` 은 두 쪽을 번갈아 읽는다」** — 첫 `MoveNext` 에서 **안쪽을 통째로** 읽는다. 바깥이 비면 안쪽은 **안 연다**((3)).
4. ★★★ **「빈 입력의 `Aggregate` 는 기본값을 준다」** — 시드가 없으면 **던진다.** 시드가 있으면 시드((5)).
5. ★★★ **「`Max()` 는 빈 입력에서 늘 던진다」** — `int[]` 는 던지고 **`string[]`·`int?[]` 는 `null`.** ★ 그 `null` 중 일부는 **문서가 침묵하는 관찰**이다((5)).
6. ★★ **「`GroupBy` 는 키 순서로 정렬한다」** — **처음 나온 순서**다(`2 · 1 · 3 · 5`)((1)).
7. ★★ **「`GroupJoin` 도 짝 없는 쪽을 버린다」** — **빈 묶음**을 준다(`lee[]`) · `GroupBy` 에는 빈 묶음이 없다((1)(4)).
8. ★ **「`Zip` 은 길이가 다르면 던진다」** — 짧은 쪽에서 **조용히** 멈춘다((4)).

## 구현 세부사항 대 언어 보장

| 무엇 | 층 | 근거 |
|---|---|---|
| **빈 입력 → `InvalidOperationException`(시드 없는 `Aggregate` · `Average(int)` · `Max(int)` · `First`)** | ★★★ **BCL 계약**(XML 예외 조항) | (5) |
| **`MaxBy` 가 기본형 + 빈 입력에서만 던진다** | ★★★ **BCL 계약**(XML) | (5) |
| **`Average(int?)` 의 빈 입력 → `null`** | ★★★ **BCL 계약**(XML 반환 조항) | (5) |
| **`Max(int?)`·제네릭 `Max<T>` 의 빈 입력 → `null`** | ★ **이 판의 관찰**(문서 침묵) | (5) |
| **`ToLookup` 묶음 안의 원소 순서 = 원본 순서** | ★★★ **BCL 계약**(XML 반환 조항) | (1) |
| **`GroupBy` 의 키 순서 = 처음 나온 순서 · 원소 순서** | ★★ **BCL 구현**(XML 은 말하지 않는다) — 이 판의 관찰 | (1) |
| **`GroupBy` 는 지연 · `ToLookup` 은 즉시** | ★★ **BCL**(이 판의 로그 — [33번](../33-linq-method-syntax-and-deferred-execution/) (1)과 같은 방법) | (2) |
| **`Join` 이 바깥 한 칸 뒤 안쪽을 통째로 · 바깥이 비면 안쪽을 안 연다** | ★★★ **BCL 구현** | (3) |
| **`LeftJoin` = `GroupJoin` + `DefaultIfEmpty`** | ★★ 결과가 같다는 것은 **이 판의 관찰** · 왼쪽 외부 조인이라는 것은 **XML 계약** | (4) |
| **`group … by` → `GroupBy` · `join … into` → `GroupJoin`** | ★★★ **언어**(번역) | [34번](../34-linq-query-syntax/) |

## 언제 쓰고 언제 안 쓰나

- ★★★ **묶은 결과를 여러 번 쓰면 `ToLookup`(또는 `GroupBy(…).ToList()`)** — `GroupBy` 를 변수에 두면 소비마다 원본을 다시 읽는다((2)).
- ★★★ **한 번 흘려 보낼 결과면 `GroupBy`** — 지연이라 만들 때 비용이 없다.
- ★★★ **빈 입력이 가능한 집계에는 시드를 줘라** — `Aggregate(seed, …)` · `Sum` · `DefaultIfEmpty(기본값).Max()`. 시드 없는 `Aggregate`·`Max()`·`Average()` 는 **던진다**((5)).
- ★★ **「없으면 `null`」이 필요하면 널 허용 타입으로 올려라** — `xs.Select(x => (int?)x).Max()` 꼴. ★ 다만 (5)의 표처럼 **어느 `null` 이 계약인지** 확인하고 기대라.
- ★★ **왼쪽 외부 조인은 `LeftJoin` 이 있는 판이면 그것** — 없는 판이면 `GroupJoin` + `SelectMany` + `DefaultIfEmpty`((4) — 결과가 같다).
- ★ **`Join` 에서 작은 쪽을 안쪽에** — 안쪽이 **통째로 메모리에 올라온다**((3)). ★ 「그래서 빠르다」는 **재지 않았다** — 잰 것은 **읽는 순서**다.

## 핵심 문장

1. ★★★ **`GroupBy` 결과는 묶는 방법이다 — 두 번 돌고 한 번 세면 원본을 3 번 읽는다. `ToLookup` 은 만들 때 1 번으로 끝난다**((2)).
2. ★★★ **`Join` 은 바깥 하나를 본 뒤 안쪽을 통째로 읽어 두고 바깥을 흘린다 — 바깥이 비면 안쪽을 안 연다**((3)).
3. ★★★ **빈 입력 던진 칸 10 / 22 — 시작값이 없는 연산(시드 없는 `Aggregate`·`Max`·`Average`·`First`)이 던지고, 항등원·시드가 있는 연산(`Sum`·`Count`·시드 `Aggregate`)이 값을 준다**((5)).
4. ★★ **`Max` 의 `null` 은 타입이 정하고, 그 `null` 이 계약인지는 문서가 정한다 — `Average(int?)` 는 약속, 제네릭 `Max<T>` 는 침묵**((5)).
5. ★★ **`GroupBy` 에는 빈 묶음이 없고 `GroupJoin` 에는 있다 — 그 빈 묶음에 `DefaultIfEmpty` 를 넣으면 `LeftJoin` 과 같아진다**((1)(4)).

## 관련 자료

- [32번 — `yield return` 반복자와 지연 실행](../32-yield-return-iterators-and-deferred-execution/) (7) — **경계**: 「두 번 열거하면 두 번」은 거기서 쟀다. 여기는 **그룹 결과**와 그것을 막는 `ToLookup`.
- [33번 — LINQ 메서드 구문과 지연 실행](../33-linq-method-syntax-and-deferred-execution/) (1) — `GroupBy` 가 첫 `MoveNext` 에서 끝까지 읽는 칸 · (2) `ICollection` 지름길.
- [34번 — LINQ 쿼리 구문](../34-linq-query-syntax/) (1) — `group … by` · `join … into` 의 번역.
- 다음 — [36번 — `IQueryable`](../36-iqueryable-and-expression-trees/) — 같은 `GroupBy`·`Join` 이 **번역**되어 원격에서 돌 때.
- Java 갈래 목록([`java/syntax/README.md`](../../../java/syntax/README.md))의 **46번**([`46-terminal-operations/`](../../../java/syntax/46-terminal-operations/) — 빈 스트림의 `reduce` 는 `Optional.empty`) · **48번**([`48-collectors-grouping/`](../../../java/syntax/48-collectors-grouping/) — `groupingBy`).
- Kotlin 갈래 목록([`kotlin/syntax/README.md`](../../../kotlin/syntax/README.md))의 **44번**(`fold` 와 `reduce` 가 빈 입력에서 갈리는 지점) — ★ 폴더가 아직 없어 링크하지 않는다. 같은 갈림(시드 유무)이 그 주제의 과녁이다.

## 용어 풀이

- **`IGrouping<TKey, TElement>`** — 키 하나와 그 키의 원소 시퀀스. `GroupBy` 결과의 원소.
- **`ILookup<TKey, TElement>`** — 키로 묶음을 찾는 **이미 만들어진** 사전 꼴. 없는 키는 빈 시퀀스.
- **내부 조인(inner join)** — 양쪽에 짝이 있는 것만 남긴다(`Join`).
- **그룹 조인(group join)** — 바깥 원소마다 짝들을 묶음으로(`GroupJoin`). 짝이 없으면 빈 묶음.
- **왼쪽 외부 조인(left outer join)** — 바깥 원소를 전부 남기고 짝이 없으면 기본값(`LeftJoin` · `GroupJoin` + `DefaultIfEmpty`).
- **시드(seed)** — `Aggregate` 의 시작값. 빈 입력에서 그대로 답이 된다.

## 더 들어가면

- ★ **`Join` 의 안쪽이 무한 시퀀스면** — 통째로 읽으니 끝나지 않는다고 (3)에서 **추론**된다. 돌리지 않았다(끝나지 않는 실험이다).
- ★ **연산자마다 들어온 판** — 옛 참조 팩이 없어 확인하지 못했다. 옛 SDK 를 받을 수 있는 환경에서 `LeftJoin`·`CountBy` 의 유무를 찍을 자리다.
