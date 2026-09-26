# csharp/syntax/33 — LINQ 메서드 구문과 지연 실행 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — ★ **SDK 참조 팩의 XML 문서** `packs/Microsoft.NETCore.App.Ref/10.0.12/ref/net10.0/System.Linq.xml`(로컬에서 열어 확인: `Enumerable.Where` 의 예외 조항 「`source` 또는 `predicate` 가 `null` 이면 **`ArgumentNullException`**」 · `Count` 의 조항 「`source` 가 `null` 이면 `ArgumentNullException` · 개수가 `Int32.MaxValue` 를 넘으면 `OverflowException`」 · `TryGetNonEnumeratedCount` 의 요약 「**열거를 강제하지 않고** 개수를 알아내려 시도한다」 · `AsEnumerable` 의 요약 「입력을 **`IEnumerable<T>` 타입으로** 돌려준다」).\
> ★★★ **이 배치는 외부 네트워크를 쓰지 않았다** — Learn 의 「표준 쿼리 연산자의 실행 방식 분류」 표와 LINQ 개요는 **열어 보지 않았다.** 그 표를 인용하는 대신 **(1) 격자가 실측이다.** XML 문서에는 **「지연 실행」이라는 낱말이 한 번도 없다**((0) — `deferred 0 · lazy 0`) — 그래서 연산자마다 **즉시냐 지연이냐는 이 문서에서 전부 로그로** 가렸다.
> **실행 검증** — 이 문서의 모든 출력은 아래 「이 판」의 도구로 **실제로 돌려 얻은 것**이다(2026-09-26). 블록은 캡처 스크립트가 파일로 받아 조립기가 끼워 넣었다 — 사람이 옮겨 적은 줄은 없다. **대비는 실측이다** — **javac/java 21.0.5** 로 Stream 을 두 번 썼다((5)).
> **버전** — ★★ **언어 쪽 경계는 쟀다** — `-langversion:2` 가 **람다**와 **확장 메서드 선언**에 `CS8023 … 3 or greater` 를 냈고, **확장 메서드 호출 `xs.Where(delegate …)` 는 막지 않았다**((6)). ★ 라이브러리 쪽(`Chunk`·`TryGetNonEnumeratedCount` 가 들어온 .NET 판)은 이 머신에 참조 팩이 **10.0.12 하나뿐**이라 **확인하지 못했다.**
> **경계** — ★★★ **「호출하면 0 줄 · `ToList()` 하면 돈다 · 사슬이 `4 · 4`」 는 [32번](../32-yield-return-iterators-and-deferred-execution/) (6)(7)이 이미 쟀다** — 여기서는 **다시 재지 않고 인용한다.** 여기는 그 다음 두 칸이다 — ① **연산자 16개를 「호출 즉시」와 「첫 `MoveNext`」 두 시점으로 가른 격자** · ② **「지연인데 한 개씩이 아닌」 연산자**(`OrderBy`·`Reverse`·`GroupBy`).\
> ★★ LINQ 가 **`System.Linq.Enumerable` 의 확장 메서드 묶음**인 것은 [30번](../30-extension-methods-and-extension-members/) (1)이 정본이다(`Where` 오버로드 2개가 전부 `static` · `[Extension]`). ★★ 캡처한 변수를 고치면 양쪽이 본다는 것은 [28번](../28-lambdas-and-closure-capture/) (6)이 정본이다 — 여기서는 **그것이 쿼리에서 어떻게 보이나** 한 칸((3)).
> ★★★ **본체 창은 ⑤ 실행 로그 격자다** — 「즉시냐 지연이냐」는 **소스가 로그를 몇 줄 남겼나**로만 보인다. 반환 타입으로는 안 보인다((1) — `ToList` 도 `IEnumerable<T>` 를 구현한다).
>
> ★★ **흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | ★ **돌려준 타입의 이름**(``IEnumerableWhereIterator`1`` · ``OrderedIterator`2`` …) — BCL 내부 클래스라 **판마다 바뀔 수 있다** | ★★★ **로그 줄 수와 순서** · **「호출 즉시 소스를 건드린 칸 N / M」** · **「GetEnumerator 가 안 불린 칸 N / M」** |
> | 예외 **문구**(Java 의 `stream has already been operated upon or closed`) | ★★★ 예외 **타입**(`ArgumentNullException` · `DivideByZeroException` · `IllegalStateException`) · **호출 때냐 열거 때냐** |
> | — | 결과 값(`[5]` · `[3, 4, 5]` · `kim:31 park:31 lee:25`) |

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
| **언어 명세(ECMA-334)** | ★ C# 언어가 약속한 것 | ★ 람다 캡처(변수를 잡는다 — [28번](../28-lambdas-and-closure-capture/)) · 확장 메서드 호출 해석([30번](../30-extension-methods-and-extension-members/)) · 반복자의 지연([32번](../32-yield-return-iterators-and-deferred-execution/)). ★★★ **「`Where` 가 지연이다」는 언어가 아니다** — `Where` 는 **라이브러리 메서드**다 |
| **BCL 계약(XML 문서)** | ★★ 문서가 약속한 것 | ★★ `Where`·`OrderBy`·`Count` 의 **예외 조항**(`null` 인자 → `ArgumentNullException`) · `TryGetNonEnumeratedCount` 의 「열거를 강제하지 않고」 |
| **BCL 구현(System.Linq 10.0.12)** | ★★★ 그것을 **어떻게 짰나** | ★★★ `OrderBy`·`Reverse`·`GroupBy` 가 **첫 `MoveNext` 에서 끝까지** 읽는 것 · `Distinct` 가 **한 개씩**인 것 · `Chunk(2)` 가 **두 개** · ★★★ **`Count()` 가 `ICollection<T>` 면 `Count` 속성만 읽는 것** · 돌려준 타입 이름 |
| **이 판의 관찰** | .NET 10.0.12 · linux-x64 · javac/java 21.0.5 | 로그 줄 수 · Java 예외 문구 |

★★★ **이 주제의 층 구분이 급소다 —**\
**지연 실행은 C# 언어의 성질이 아니라 `System.Linq` 가 그렇게 짠 것**이다. 언어가 주는 것은 [32번](../32-yield-return-iterators-and-deferred-execution/)의 `yield`(지연되는 **도구**)뿐이고, `Where` 를 그 도구로 **지연되게 짠 것**은 BCL 이다. 그래서 **연산자마다 따로 물어야 한다** — (1)이 그 질문을 16번 던진다.

## 한눈에 — 쉽게 말하면

**LINQ 메서드 사슬은 「주문서」를 쓰는 일이다 — `Where`·`Select`·`OrderBy` 를 이을 때는 주문서에 줄이 늘 뿐이고, 요리는 누군가 「접시를 달라」(`MoveNext`)고 할 때 시작된다. 그런데 요리마다 첫 접시를 내는 데 필요한 재료가 다르다.**

- **주문서에 적기(지연 연산자 호출)** — `Where`·`Select`·`OrderBy`·`GroupBy` … 를 불러도 **재료 창고(소스)는 한 번도 안 열린다.** 16개 중 9개가 그렇다((1)).
- **바로 요리하기(즉시 연산자)** — `ToList`·`ToArray`·`Count()`·`Sum()`·`ToDictionary` 는 **부르는 순간 창고를 끝까지** 턴다. `Any()`·`First()` 는 **한 개만** 꺼내고 멈춘다.
- **첫 접시에 필요한 재료가 다르다** — `Where` 는 **재료 하나**면 첫 접시가 나온다. `OrderBy` 는 **가장 작은 것**을 내야 하니 **창고를 끝까지 봐야** 첫 접시가 나온다. 「지연」이라고 해서 **「한 개씩」이 아니다.**
- **주문서의 빈칸(캡처한 변수)** — 「`threshold` 보다 큰 것」이라고 적었으면 **요리할 때의 `threshold`** 를 본다((3)).
- **주문서는 몇 번이든 다시 낼 수 있다** — C# 의 `IEnumerable<T>` 는 다시 열거하면 **처음부터 다시 요리**한다. Java `Stream` 은 **한 번 쓰면 끝**이다((5)).

| 비유 | 실체 | 어디서 보나 |
|---|---|---|
| 주문서에 적기만 | ★★★ 지연 연산자 **호출 직후 로그 0 줄** — 16 중 9 | (1) |
| 바로 요리 | ★★★ `ToList`·`ToArray`·`Count()`·`Sum()`·`ToDictionary` **호출 직후 6 줄**(끝까지) · `Any()`·`First()` **1 줄** — **7 / 16** | (1) |
| 첫 접시에 창고 전부 | ★★★ `OrderBy`·`Reverse`·`GroupBy` — 호출 0 줄 · **첫 `MoveNext` 뒤 6 줄** — **3 / 16** | (1) |
| 재료는 다 보되 요리는 덜 | ★★ `OrderBy(…).First()` — 키 10 번 · **`Compare` 9 번**(최솟값만) · `foreach` 첫 원소는 **36 번**(전부 정렬) | (1-b) |
| 창고를 안 열고 개수 | ★★★ `ICollection<T>` 의 `Count()`·`Any()` 는 **`Count 속성`만** — **`GetEnumerator` 가 안 불린 칸 4 / 12** | (2) |
| 빈칸은 요리할 때 읽는다 | ★★★ 정의 뒤 `threshold = 4` → **`[5]`** · 미리 `ToList` 한 것은 **`[3, 4, 5]`** | (3) |
| 주문서 검사는 적을 때 | ★★ `null` 소스·`null` 람다는 **호출 때** `ArgumentNullException` · 람다 **안**의 예외는 **열거 때** | (4) |
| 다시 낼 수 있나 | ★★★ C# **2 · 2** · Java **`IllegalStateException`** | (5) |

★★★ **이 주제의 본체 그림 — 「언제 소스를 건드리나」 세 갈래.**

```text
   연산자를 부른 순간                첫 MoveNext 한 번                   (소스 로그 줄 수 · (1) 실측)
   ──────────────────────────        ─────────────────────────────────
   ┌ 지연 · 한 개씩 ─────────┐
   │ Where  Select  Take(2)  │        1 줄   pull(3)                       ← 첫 원소 하나면 첫 결과가 나온다
   │ Distinct  AsEnumerable  │  0 줄
   └─────────────────────────┘
   ┌ 지연 · 몇 개씩 ─────────┐
   │ Chunk(2)                │  0 줄  2 줄   pull(3) pull(1)               ← 한 덩어리를 채워야 첫 결과
   └─────────────────────────┘
   ┌ 지연 · 전부 먼저 ───────┐
   │ OrderBy  Reverse        │  0 줄  6 줄   pull(3)…pull(5) end           ← 가장 작은 것 · 마지막 것 · 모든 키를
   │ GroupBy                 │                                              알려면 끝까지 봐야 한다
   └─────────────────────────┘
   ┌ 즉시 ───────────────────┐
   │ ToList ToArray Count()  │  6 줄  (MoveNext 는 이미 모은 것을 읽는다 — 소스는 더 안 열린다)
   │ Sum() ToDictionary      │
   │ Any()  First()          │  1 줄  (값이 돌아왔다 — 열거자가 없다)
   └─────────────────────────┘

   ★★★ 「지연」 은 「부를 때 안 돈다」 까지만 말한다. 「첫 결과를 낼 때 얼마나 읽나」 는 연산자마다 다르다.
```

## 이 주제가 답하려는 질문

1. **어느 연산자가 부르는 순간 소스를 읽고, 어느 것이 첫 `MoveNext` 까지 미루나 — 미룬 것은 첫 `MoveNext` 에서 얼마나 읽나**((1)).
2. **`Count()` 는 언제 열거하지 않나** — `ICollection<T>` 의 형 검사((2)).
3. **지연이 만드는 함정 둘** — 캡처한 변수가 **나중 값**으로 읽히는 것((3)) · 인자 검사와 람다 안 예외의 **시점이 갈리는** 것((4)).
4. **Java `Stream` 과 무엇이 갈리나** — 다시 쓰기((5)).

## 동작 방식

### (0) 이 주제가 쓰는 창

★★★ **본체 창은 ⑤ 실행 로그 격자다.**

| 창 | 무엇을 보여 주나 | 이 주제에서 |
|---|---|---|
| ★★★ **⑤ 실행 로그 격자** | ★★★ 소스가 남긴 `pull(…)`·`end` 의 **줄 수 · 순서** — 호출 직후 / 첫 `MoveNext` 뒤 · `Count 속성`·`GetEnumerator`·`CopyTo` 호출 · 키 선택자·`Compare` **호출 수** | (1)(1-b)(2) |
| ★★ **실행 결과** | ★★ 캡처한 변수를 바꾼 뒤의 결과 · 예외 **타입**과 **시점**(호출 / 열거) · Java 짝 | (3)(4)(5) |
| ★ **② 진단** | ★ `-langversion:2` 의 `CS8023`(람다) — 판 경계 | (6) |
| **① IL 덤프** | ★ **이 주제는 안 쓴다** — `xs.Where(f)` 가 `call Enumerable::Where` 인 것은 [30번](../30-extension-methods-and-extension-members/) (1)이 찍었다(인용) | — |
| **④ 할당 바이트** | ★ **안 쟀다** — 이 주제의 질문(「언제 읽나」)은 할당이 아니라 **로그 줄 수**가 답한다. 반복자 객체의 할당은 [32번](../32-yield-return-iterators-and-deferred-execution/) (8)이 쟀다 | — |
| **부적용인 창** | 없다 | — |

```text
===== cd packs/Microsoft.NETCore.App.Ref/10.0.12/ref/net10.0 && echo "deferred $(grep -c -i deferred System.Linq.xml) · lazy $(grep -c -i lazy System.Linq.xml) · member $(grep -c "<member " System.Linq.xml)" (exit=0) =====
deferred 0 · lazy 0 · member 244
```

★★ 위 블록은 **dotnet 설치 디렉토리에서** 돌린 것이다(배너의 `cd` 는 그 아래 상대 경로). **`<member ` 줄 244 개 중 `deferred`·`lazy` 0 줄** — XML 문서는 **예외 조항과 반환값**만 말하고 **「언제 읽나」는 말하지 않는다.** 그래서 이 주제는 로그로만 답한다.

★ **제5의 상태 — 같은 질문을 다른 창으로 물었다.** 「`Count()` 가 열거했나」는 성능 계측으로 물을 수도 있지만 **재지 않았다.** 대신 **소스 타입이 `GetEnumerator` 를 불렸는지 스스로 적게** 했다((2)). 이 창은 **「불렸나」만 보고 「얼마나 걸렸나」는 못 본다.**

### (1) ★★★ 본체 — 즉시 대 지연 격자: 연산자 16 × 두 시점

**언제 쓰나** — 「이 사슬 끝에 무엇을 붙이면 **그 자리에서** DB·파일을 읽나」 · 「`OrderBy` 뒤에 `Take(1)` 을 붙이면 **하나만** 읽나」.

```text
===== 소스: cs33b-grid.cs =====
using System;
using System.Collections;
using System.Collections.Generic;
using System.Linq;
class Program {
    static readonly List<string> log = new();
    static IEnumerable<int> Src() {
        foreach (var x in new[] { 3, 1, 4, 2, 5 }) { log.Add($"pull({x})"); yield return x; }
        log.Add("end");
    }
    static int rows, touched, drained;
    static void Row(string name, Func<IEnumerable<int>, object> op) {
        log.Clear();
        object r = op(Src());
        int atCall = log.Count;
        string atFirst = "-";
        if (r is IEnumerable en) { var e = en.GetEnumerator(); e.MoveNext(); atFirst = log.Count.ToString(); }
        rows++;
        if (atCall > 0) touched++;
        if (atCall == 0 && log.Contains("end")) drained++;
        string[] cells = { name, atCall.ToString(), atFirst, r.GetType().Name, string.Join(" ", log) };
        if (cells.Length != 5) throw new Exception("칸 수 어긋남");
        Console.WriteLine(string.Join("\t", cells));
    }
    static void Main() {
        Console.WriteLine(string.Join("\t", "연산자", "호출직후", "첫MoveNext뒤", "돌려준타입(이 판)", "소스 로그"));
        Row("Where", s => s.Where(x => x > 0));
        Row("Select", s => s.Select(x => x * 10));
        Row("OrderBy", s => s.OrderBy(x => x));
        Row("Take(2)", s => s.Take(2));
        Row("Distinct", s => s.Distinct());
        Row("Reverse", s => s.Reverse());
        Row("GroupBy", s => s.GroupBy(x => x % 2));
        Row("Chunk(2)", s => s.Chunk(2));
        Row("AsEnumerable", s => s.AsEnumerable());
        Row("ToList", s => s.ToList());
        Row("ToArray", s => s.ToArray());
        Row("Count()", s => s.Count());
        Row("Any()", s => s.Any());
        Row("First()", s => s.First());
        Row("Sum()", s => s.Sum());
        Row("ToDictionary", s => s.ToDictionary(x => x));
        Console.WriteLine($"호출 즉시 소스를 건드린 칸 {touched} / {rows}");
        Console.WriteLine($"호출 직후 0 줄 · 첫 MoveNext 뒤 end 가 찍힌 칸 {drained} / {rows}");
    }
}
===== csc -out:ex.dll cs33b-grid.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
연산자	호출직후	첫MoveNext뒤	돌려준타입(이 판)	소스 로그
Where	0	1	IEnumerableWhereIterator`1	pull(3)
Select	0	1	IEnumerableSelectIterator`2	pull(3)
OrderBy	0	6	OrderedIterator`2	pull(3) pull(1) pull(4) pull(2) pull(5) end
Take(2)	0	1	IEnumerableSkipTakeIterator`1	pull(3)
Distinct	0	1	DistinctIterator`1	pull(3)
Reverse	0	6	ReverseIterator`1	pull(3) pull(1) pull(4) pull(2) pull(5) end
GroupBy	0	6	GroupByIterator`2	pull(3) pull(1) pull(4) pull(2) pull(5) end
Chunk(2)	0	2	<EnumerableChunkIterator>d__40`1	pull(3) pull(1)
AsEnumerable	0	1	<Src>d__1	pull(3)
ToList	6	6	List`1	pull(3) pull(1) pull(4) pull(2) pull(5) end
ToArray	6	6	Int32[]	pull(3) pull(1) pull(4) pull(2) pull(5) end
Count()	6	-	Int32	pull(3) pull(1) pull(4) pull(2) pull(5) end
Any()	1	-	Boolean	pull(3)
First()	1	-	Int32	pull(3)
Sum()	6	-	Int32	pull(3) pull(1) pull(4) pull(2) pull(5) end
ToDictionary	6	6	Dictionary`2	pull(3) pull(1) pull(4) pull(2) pull(5) end
호출 즉시 소스를 건드린 칸 7 / 16
호출 직후 0 줄 · 첫 MoveNext 뒤 end 가 찍힌 칸 3 / 16
```

- ★★★ **호출 즉시 소스를 건드린 칸 7 / 16** — 스크립트가 셌다. `ToList`·`ToArray`·`Count()`·`Sum()`·`ToDictionary` 는 **6 줄**(`pull` 다섯 + `end` — **끝까지**), `Any()`·`First()` 는 **1 줄**(`pull(3)` 에서 멈춤). 나머지 9개는 **호출 직후 0 줄**이다.
- ★★★ **호출 직후 0 줄 · 첫 `MoveNext` 뒤 `end` 가 찍힌 칸 3 / 16** — **`OrderBy`·`Reverse`·`GroupBy`**. 부를 때는 [32번](../32-yield-return-iterators-and-deferred-execution/) (6)처럼 0 줄인데, **첫 결과 하나를 달라는 순간 소스를 끝까지** 읽었다(`pull(3) pull(1) pull(4) pull(2) pull(5) end`).
- ★★★ **`Distinct` 는 그 셋과 다르다 — 첫 `MoveNext` 뒤 1 줄.** 「본 적 있나」를 **지금까지 본 것**으로만 판단하면 되니, 첫 원소는 **바로** 낸다. ★ 「`Distinct` 도 전부 끌어온다」는 **이 판에서 틀렸다.**
- ★★ **`Chunk(2)` 는 2 줄** — 덩어리 하나를 채울 만큼. 「지연」 안에 **한 개 · 몇 개 · 전부**가 다 있다.
- ★★ **`AsEnumerable` 의 타입이 `<Src>d__1`** — **소스 그 자체**다. 「`IEnumerable<T>` 로 **보이게**」만 한다(XML 문서의 요약 그대로). 그 쓸모는 [36번](../36-iqueryable-and-expression-trees/)에 있다.
- ★★ **`ToList`·`ToArray`·`ToDictionary` 의 「첫 MoveNext 뒤」 가 6 그대로** — 이미 모은 컬렉션을 읽으니 **소스는 더 안 열린다.** ★★★ 그리고 이 셋의 결과도 **`IEnumerable` 이다** — 스크립트의 `r is IEnumerable` 이 참이라 `MoveNext` 를 불렀다. **반환 타입으로는 즉시·지연을 못 가른다.**

★★ **`OrderBy` 가 왜 끝까지 읽나 — 첫 결과를 내려면 무엇을 알아야 하나.**

```text
   Where(x => x > 0)       첫 결과 = 「조건을 만족하는 첫 원소」       → pull(3) 에서 답이 나온다
   Distinct()              첫 결과 = 「처음 본 원소」                   → pull(3) 에서 답이 나온다
   Chunk(2)                첫 결과 = 「앞의 두 개」                     → pull(3) pull(1)
   OrderBy(x => x)         첫 결과 = 「가장 작은 원소」                 → 뒤에 더 작은 것이 있을지 모른다 → end 까지
   Reverse()               첫 결과 = 「마지막 원소」                    → 마지막이 어디인지 end 를 봐야 안다
   GroupBy(x => x % 2)     첫 결과 = 「첫 키의 묶음 전부」              → 그 키의 원소가 뒤에 또 있을지 모른다 → end 까지

   ★ 이 표는 「왜 그럴 수밖에 없나」 의 설명이다 — 로그는 그 설명과 맞았다(이 판).
     「어떻게 모으나(배열에 담나 · 정렬을 언제 하나)」 는 BCL 구현이고 여기서 재지 않았다.
     Java 의 sorted 가 「상태 있는 연산」 이라 다 모일 때까지 막히는 것과 같은 모양이다(Java 45편).
```

### (1-b) ★★ 그런데 첫 원소만 원하면 — `First()` 는 정렬하지 않았다

**언제 쓰나** — 「`OrderBy(…).First()` 는 **다 정렬한 뒤** 첫 것을 집나」.

```text
===== 소스: cs33b-sort.cs =====
using System;
using System.Collections.Generic;
using System.Linq;
class Counting : IComparer<int> {
    public int calls;
    public int Compare(int a, int b) { calls++; return a.CompareTo(b); }
}
class Program {
    static int keys;
    static int Key(int x) { keys++; return x; }
    static void Run(string label, Func<IEnumerable<int>, Counting, object> consume) {
        var src = new List<int> { 8, 3, 9, 1, 7, 2, 6, 4, 5, 0 };
        var cmp = new Counting(); keys = 0;
        var r = consume(src, cmp);
        Console.WriteLine($"{label,-36} 결과 {r,-3} · 키 선택자 {keys,2} 번 · Compare {cmp.calls,2} 번");
    }
    static void Main() {
        Run("[1] OrderBy(Key, cmp).First()", (s, c) => s.OrderBy(Key, c).First());
        Run("[2] OrderBy(Key, cmp).Take(1).ToList()", (s, c) => s.OrderBy(Key, c).Take(1).ToList()[0]);
        Run("[3] foreach 로 첫 원소만 보고 break", (s, c) => { foreach (var x in s.OrderBy(Key, c)) return x; return -1; });
        Run("[4] OrderBy(Key, cmp).ToList()", (s, c) => s.OrderBy(Key, c).ToList().Count);
    }
}
===== csc -out:ex.dll cs33b-sort.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
[1] OrderBy(Key, cmp).First()        결과 0   · 키 선택자 10 번 · Compare  9 번
[2] OrderBy(Key, cmp).Take(1).ToList() 결과 0   · 키 선택자 10 번 · Compare  9 번
[3] foreach 로 첫 원소만 보고 break         결과 0   · 키 선택자 10 번 · Compare 36 번
[4] OrderBy(Key, cmp).ToList()       결과 10  · 키 선택자 10 번 · Compare 36 번
```

- ★★★ **네 소비자 모두 키 선택자 10 번** — 원소 10개의 키를 **전부** 계산했다. (1)의 「첫 `MoveNext` 에서 끝까지 읽는다」와 맞는다.
- ★★★ **그런데 `Compare` 가 갈린다 — `[1]` `First()` · `[2]` `Take(1).ToList()` 는 9 번, `[3]` `foreach` 첫 원소 · `[4]` `ToList()` 는 36 번.** 9 는 원소 10개에서 **최솟값 하나를 찾는** 비교 수이고, 36 은 **전부 정렬**한 수다(같은 입력 · 같은 판에서 결정적).
- ★★★ **같은 「첫 원소 하나」인데 `foreach` 로 꺼내면 전부 정렬했다** — `OrderBy` 가 돌려준 객체가 **뒤에 무엇이 붙었는지**(`First` · `Take(1)`)를 보고 **최솟값 찾기로 바꿔 탔다**는 뜻이다. `foreach` 는 그 정보를 안 주니 **정렬부터** 한다.
- ★★★ **이것은 BCL 구현이다** — XML 문서의 `OrderBy`·`First` 어디에도 비교 횟수 약속은 없다. ★ 「그래서 `First()` 가 빠르다」는 **재지 않았다** — 잰 것은 **`Compare` 호출 수**다.
- ★ (1) 격자의 `OrderBy` 칸(6 줄)은 **「읽은 양」** 이고, 이 표는 **「그 뒤에 한 일」** 이다. 둘을 같은 것으로 읽지 마라.

### (2) ★★★ `Count()` 는 언제 열거하지 않나 — `ICollection<T>` 의 형 검사

**언제 쓰나** — 「`list.Count()` 와 `list.Count` 가 다른가」 · 「`Any()` 로 비었는지 물으면 **첫 원소를 꺼내나**」.

```text
===== 소스: cs33b-count.cs =====
using System;
using System.Collections;
using System.Collections.Generic;
using System.Linq;
class Traced : ICollection<int> {
    public static readonly List<string> log = new();
    readonly List<int> items = new() { 3, 1, 4 };
    public int Count { get { log.Add("Count 속성"); return items.Count; } }
    public IEnumerator<int> GetEnumerator() { log.Add("GetEnumerator"); return items.GetEnumerator(); }
    IEnumerator IEnumerable.GetEnumerator() => GetEnumerator();
    public bool IsReadOnly => true;
    public void Add(int item) => throw new NotSupportedException();
    public void Clear() => throw new NotSupportedException();
    public bool Contains(int item) { log.Add("Contains"); return items.Contains(item); }
    public void CopyTo(int[] array, int i) { log.Add("CopyTo"); items.CopyTo(array, i); }
    public bool Remove(int item) => throw new NotSupportedException();
}
class SeqOnly : IEnumerable<int> {
    readonly List<int> items = new() { 3, 1, 4 };
    public IEnumerator<int> GetEnumerator() { Traced.log.Add("GetEnumerator"); return items.GetEnumerator(); }
    IEnumerator IEnumerable.GetEnumerator() => GetEnumerator();
}
class Program {
    static int cells, skipped;
    static void Pair(string name, Func<IEnumerable<int>, object> op) {
        var outs = new List<string> { name };
        foreach (IEnumerable<int> s in new IEnumerable<int>[] { new Traced(), new SeqOnly() }) {
            Traced.log.Clear();
            var r = op(s);
            cells++;
            if (!Traced.log.Contains("GetEnumerator")) skipped++;
            outs.Add($"{r} · {string.Join(" / ", Traced.log)}");
        }
        if (outs.Count != 3) throw new Exception("칸 수 어긋남");
        Console.WriteLine(string.Join("\t", outs));
    }
    static void Main() {
        Console.WriteLine(string.Join("\t", "호출", "ICollection<int> 구현", "IEnumerable<int> 만 구현"));
        Pair("Count()", s => s.Count());
        Pair("Any()", s => s.Any());
        Pair("ToList().Count", s => s.ToList().Count);
        Pair("Contains(4)", s => s.Contains(4));
        Pair("Count(x => x > 1)", s => s.Count(x => x > 1));
        Pair("Where(x => true).Count()", s => s.Where(x => true).Count());
        Console.WriteLine($"GetEnumerator 가 안 불린 칸 {skipped} / {cells}");
    }
}
===== csc -out:ex.dll cs33b-count.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
호출	ICollection<int> 구현	IEnumerable<int> 만 구현
Count()	3 · Count 속성	3 · GetEnumerator
Any()	True · Count 속성	True · GetEnumerator
ToList().Count	3 · Count 속성 / CopyTo	3 · GetEnumerator
Contains(4)	True · Contains	True · GetEnumerator
Count(x => x > 1)	2 · GetEnumerator	2 · GetEnumerator
Where(x => true).Count()	3 · GetEnumerator	3 · GetEnumerator
GetEnumerator 가 안 불린 칸 4 / 12
```

- ★★★ **`GetEnumerator` 가 안 불린 칸 4 / 12** — 전부 **`ICollection<int>` 열**이다. `Count()` · `Any()` 는 **`Count 속성`** 만, `ToList()` 는 **`Count 속성 / CopyTo`**, `Contains(4)` 는 **자기 `Contains`** 를 불렀다. **열거자를 한 번도 안 만들었다.**
- ★★★ **같은 호출이 `IEnumerable<int>` 만 구현한 타입에서는 전부 `GetEnumerator`** — 값(`3` · `True`)은 **같고 가는 길만 다르다.** `Enumerable.Count` 가 **받은 객체의 실제 타입을 검사**해 지름길을 탔다는 뜻이다.
- ★★ **`Count(x => x > 1)` 와 `Where(x => true).Count()` 는 `ICollection` 에서도 `GetEnumerator`** — 조건이 붙으면 **하나씩 봐야** 하고, `Where` 를 거치면 받은 객체가 **`ICollection` 이 아니게** 된다.
- ★★★ **이것은 언어도 문서화된 계약도 아니다 — BCL 구현이다.** XML 문서의 `Count` 에는 「`ICollection` 이면」이라는 조항이 **없다**(열어 확인한 것: 예외 두 개와 반환값뿐). 명시적으로 **「열거하지 않고」를 약속하는 것은 `TryGetNonEnumeratedCount`** 쪽이다(요약 「열거를 강제하지 않고 개수를 알아내려 시도한다」).

### (3) ★★★ 쿼리를 정의한 뒤 캡처한 변수를 바꾸면

**언제 쓰나** — 「필터 조건을 변수로 만들어 쿼리를 **먼저** 만들어 두고, 조건을 바꾼 뒤 결과를 읽었다」.

```text
===== 소스: cs33b-capture.cs =====
using System;
using System.Collections.Generic;
using System.Linq;
class Program {
    static void Main() {
        var src = new List<int> { 1, 2, 3, 4, 5 };
        int threshold = 2;
        var q = src.Where(x => x > threshold);
        var snap = src.Where(x => x > threshold).ToList();
        threshold = 4;
        Console.WriteLine($"[1] q    : [{string.Join(", ", q)}]");
        Console.WriteLine($"[2] snap : [{string.Join(", ", snap)}]");
        src.Add(6);
        Console.WriteLine($"[3] src.Add(6) 뒤 q    : [{string.Join(", ", q)}]");
        Console.WriteLine($"[4] src.Add(6) 뒤 snap : [{string.Join(", ", snap)}]");
    }
}
===== csc -out:ex.dll cs33b-capture.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
[1] q    : [5]
[2] snap : [3, 4, 5]
[3] src.Add(6) 뒤 q    : [5, 6]
[4] src.Add(6) 뒤 snap : [3, 4, 5]
```

- ★★★ **`[1]` `q` 는 `[5]`** — `q` 를 **만들 때** `threshold` 는 2 였지만 **돌릴 때** 4 다. 람다는 `threshold` 의 **값이 아니라 변수를** 잡았다([28번](../28-lambdas-and-closure-capture/) (6) — 「캡처한 변수를 고치면 양쪽이 본다」). 지연 실행은 그 람다를 **열거 때** 부른다.
- ★★★ **`[2]` `snap` 은 `[3, 4, 5]`** — `ToList()` 가 **그 자리에서** 람다를 불러 결과를 **리스트로** 굳혔다.
- ★★ **`[3]` `src.Add(6)` 뒤 `q` 는 `[5, 6]` · `[4]` `snap` 은 그대로** — 지연 쿼리는 **소스도 열거 때** 읽는다. 「결과를 들고 있다」가 아니라 「**만드는 방법**을 들고 있다」([32번](../32-yield-return-iterators-and-deferred-execution/) (7))가 변수와 소스 **양쪽**에 걸린다.

```text
   q    = src.Where(x => x > threshold)         snap = src.Where(x => x > threshold).ToList()
          │                                            │
          │ 들고 있는 것: 「src 를 읽고 threshold 와 견줘라」   │ 들고 있는 것: [3, 4, 5]   ← 이 줄에서 람다가 돌았다
          │                                            │
   threshold = 4 ; src.Add(6)                   (아무 영향 없음)
          │
   foreach → 이제서야 src 를 읽고, 지금의 threshold(4) 와 견준다 → [5, 6]
```

### (4) ★★ 인자 검사는 호출 때 · 람다 안의 예외는 열거 때

**언제 쓰나** — 「`null` 을 넘겼는데 **어디서** 터지나」 · 「`OrderBy` 의 키 선택자가 던지면 `OrderBy` 줄인가 `foreach` 줄인가」.

```text
===== 소스: cs33b-when.cs =====
using System;
using System.Collections.Generic;
using System.Linq;
class Program {
    static void Try(string label, Func<IEnumerable<int>> call) {
        IEnumerable<int> q;
        try { q = call(); Console.WriteLine($"{label,-36} 호출 : 돌아옴"); }
        catch (Exception e) { Console.WriteLine($"{label,-36} 호출 : {e.GetType().Name}"); return; }
        try { foreach (var _ in q) { } Console.WriteLine($"{label,-36} 열거 : 끝까지 돎"); }
        catch (Exception e) { Console.WriteLine($"{label,-36} 열거 : {e.GetType().Name}"); }
    }
    static void Main() {
        IEnumerable<int> none = null!;
        int[] xs = { 1, 0, 2 };
        Try("[1] none.Where(x => x > 0)", () => none.Where(x => x > 0));
        Try("[2] xs.Where(null)", () => xs.Where((Func<int, bool>)null!));
        Try("[3] xs.Select(x => 10 / x)", () => xs.Select(x => 10 / x));
        Try("[4] xs.OrderBy(x => 10 / x)", () => xs.OrderBy(x => 10 / x));
    }
}
===== csc -out:ex.dll cs33b-when.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
[1] none.Where(x => x > 0)           호출 : ArgumentNullException
[2] xs.Where(null)                   호출 : ArgumentNullException
[3] xs.Select(x => 10 / x)           호출 : 돌아옴
[3] xs.Select(x => 10 / x)           열거 : DivideByZeroException
[4] xs.OrderBy(x => 10 / x)          호출 : 돌아옴
[4] xs.OrderBy(x => 10 / x)          열거 : DivideByZeroException
```

- ★★★ **`[1]` `null` 소스 · `[2]` `null` 람다 → 호출 : `ArgumentNullException`** — **열거까지 안 간다.** [32번](../32-yield-return-iterators-and-deferred-execution/) (2)에서 `yield` 메서드 안의 검사가 **열거 때** 터진 것과 **반대**다. BCL 의 LINQ 는 32번 (2)의 **「바깥 메서드 + 안쪽 반복자」 관용구로 짜여** 있다고 읽힌다(구현을 열어 보지는 않았다 — 관찰은 「호출 때 터졌다」까지). XML 문서가 두 인자에 **`ArgumentNullException` 조항**을 둔다.
- ★★★ **`[3]` `Select(x => 10 / x)` · `[4]` `OrderBy(x => 10 / x)` → 호출 : 돌아옴 · 열거 : `DivideByZeroException`** — 람다는 **열거 때** 불리므로 람다 안의 예외도 **열거 때**다. `OrderBy` 는 **첫 `MoveNext` 에서** 키를 **전부** 계산하므로((1)) 0 이 **몇 번째에 있든** 첫 `MoveNext` 에서 터진다.

### (5) ★★★ 두 번 쓰기 — C# `IEnumerable<T>` 대 Java `Stream`

```text
===== 소스: cs33b-reuse.cs =====
using System;
using System.Collections.Generic;
using System.Linq;
class Program {
    static void Main() {
        IEnumerable<int> q = new List<int> { 1, 2, 3, 4 }.Where(x => x % 2 == 0);
        try { Console.WriteLine($"첫째 : {q.Count()}"); } catch (Exception e) { Console.WriteLine($"첫째 : {e.GetType().FullName}"); }
        try { Console.WriteLine($"둘째 : {q.Count()}"); } catch (Exception e) { Console.WriteLine($"둘째 : {e.GetType().FullName}"); }
    }
}
===== csc -out:ex.dll cs33b-reuse.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
첫째 : 2
둘째 : 2
===== 소스: Reuse33.java =====
import java.util.List;
import java.util.stream.Stream;
class Reuse33 {
    public static void main(String[] args) {
        Stream<Integer> q = List.of(1, 2, 3, 4).stream().filter(x -> x % 2 == 0);
        try { System.out.println("첫째 : " + q.count()); } catch (Exception e) { System.out.println("첫째 : " + e); }
        try { System.out.println("둘째 : " + q.count()); } catch (Exception e) { System.out.println("둘째 : " + e); }
    }
}
===== javac -d j33out j33/Reuse33.java && java -cp j33out Reuse33 (cc exit=0 · run exit=0) =====
첫째 : 2
둘째 : java.lang.IllegalStateException: stream has already been operated upon or closed
```

- ★★★ **C# `q.Count()` 두 번 → `2` · `2`** — 같은 `IEnumerable<T>` 를 다시 열거하면 **처음부터 다시** 돈다([32번](../32-yield-return-iterators-and-deferred-execution/) (7) — 본문이 두 번 돈다). **다시 쓸 수는 있다 — 매번 비용을 낸다.**
- ★★★ **Java `q.count()` 두 번 → `2` · `IllegalStateException`** — `Stream` 은 **한 번 쓰면 닫힌다.** [Java 44번](../../../java/syntax/44-stream-creation/) · [Java 46번](../../../java/syntax/46-terminal-operations/)이 같은 예외를 쟀다.
- ★★ **둘 다 지연이지만 「주문서」의 성질이 다르다** — C# 은 **다시 낼 수 있는 주문서**(`IEnumerable<T>` 가 `GetEnumerator` 를 매번 새로), Java 는 **한 번 쓰는 영수증**(`Stream` 객체가 곧 파이프라인 한 번).

```text
   같은 모양의 사슬 · 두 번 소비

                      C# IEnumerable<T>                 Java Stream<T>
   만들기              src.Where(…)          0 줄        list.stream().filter(…)     (지연)
   첫째 소비           Count() → 2                        count() → 2
   둘째 소비           Count() → 2  (다시 돈다)           count() → IllegalStateException
   다시 쓰려면          그대로 다시 부른다                   list.stream() 부터 다시 만든다

   ★ C# 쪽 함정은 「두 번 돈다」(비용) · Java 쪽 함정은 「두 번 못 쓴다」(예외). 방향이 반대다.
```

### (6) ★★ 판 경계 — `-langversion:2` 가 막는 것 · 안 막는 것

```text
===== 소스: cs33b-v2.cs =====
using System.Collections.Generic;
using System.Linq;
class P {
    static void Main() {
        int[] xs = { 1, 2, 3 };
        IEnumerable<int> a = xs.Where(x => x > 1);
        IEnumerable<int> b = xs.Where(delegate (int x) { return x > 1; });
        IEnumerable<int> c = Enumerable.Where(xs, delegate (int x) { return x > 1; });
    }
}
===== csc -langversion:2 -out:ex.dll cs33b-v2.cs (cc exit=1) =====
cs33b-v2.cs(6,41): error CS8023: Feature 'lambda expression' is not available in C# 2. Please use language version 3 or greater.
===== csc -langversion:3 -out:ex.dll cs33b-v2.cs (cc exit=0) =====
===== 소스: cs33b-v2e.cs =====
static class E { public static int Twice(this int x) { return x * 2; } }
class P { static void Main() { int n = 3.Twice(); } }
===== csc -langversion:2 -out:ex.dll cs33b-v2e.cs (cc exit=1) =====
cs33b-v2e.cs(1,42): error CS8023: Feature 'extension method' is not available in C# 2. Please use language version 3 or greater.
```

- ★★★ **`-langversion:2` → `CS8023 … 'lambda expression' … 3 or greater` 하나(6행)** — `a` 의 람다만 막혔다.
- ★★★ **`b` `xs.Where(delegate (int x) { … })` 는 막히지 않았다** — 확장 메서드 **호출** 꼴인데 C# 2 로도 컴파일됐다. `c` 의 정적 호출은 당연히 된다(`Enumerable.Where` 는 그냥 정적 메서드다 — [30번](../30-extension-methods-and-extension-members/)).
- ★★★ **확장 메서드 선언(`this int x`)은 막힌다** — (1,42) 의 `CS8023`(`'extension method'`). 같은 파일의 호출 `3.Twice()` 에는 진단이 없다. **판이 막는 것은 선언 쪽**이다.
- ★★ **「LINQ 는 C# 3」의 언어 쪽 몸통은 람다·확장 메서드 선언(과 [34번](../34-linq-query-syntax/)의 쿼리 구문)** 으로 드러났다. 이미 선언된 확장 메서드의 **호출**을 판으로 막지 않는 것은 **이 판 Roslyn 의 성질**이다.
- ★ **두 파일로 나눈 까닭** — 처음에 한 파일에 넣었더니 **선언 쪽 `CS8023` 하나만** 나오고 람다 쪽 `CS8023` 이 **사라졌다**(선언 단계의 오류가 있으면 메서드 본문 진단을 안 낸 것으로 읽힌다). 진단 0 줄이 「막히지 않았다」를 뜻하려면 **다른 오류가 없는 파일**이어야 한다.

## 문법 — 형태와 규칙

### 형태

```text
===== 소스: cs33b-form.cs =====
using System;
using System.Linq;

var people = new[] { ("kim", 31), ("lee", 25), ("park", 31), ("choi", 19) };
var names = people
    .Where(p => p.Item2 >= 20)
    .OrderByDescending(p => p.Item2)
    .ThenBy(p => p.Item1)
    .Select(p => $"{p.Item1}:{p.Item2}")
    .ToList();
Console.WriteLine(string.Join(" ", names));

var twice = people.OrderByDescending(p => p.Item2).OrderBy(p => p.Item1).Select(p => p.Item1);
Console.WriteLine(string.Join(" ", twice));
===== csc -out:ex.dll cs33b-form.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
kim:31 park:31 lee:25
choi kim lee park
```

- ★★★ **메서드 구문 = 확장 메서드를 점으로 잇는 것** — `people.Where(…)` 는 `Enumerable.Where(people, …)` 다([30번](../30-extension-methods-and-extension-members/)). 줄마다 하나씩 두면 읽힌다.
- ★★ **정렬의 두 번째 키는 `ThenBy`/`ThenByDescending`** — 첫 줄은 나이 내림차순 안에서 이름순(`kim:31 park:31 lee:25`). ★★ **`OrderBy` 를 두 번 이으면 둘째 줄처럼 `choi kim lee park`** — 앞의 나이 정렬이 **흔적 없이** 이름순으로 덮였다(진단 없음).
- ★★ **사슬 끝의 `ToList()`** — 결과를 **여기서 굳힌다**는 표시다((3)).

### 금지 사례 — 진단이 나는 꼴 · 진단 없이 틀리는 꼴

| 쓴 꼴 | 무엇이 나나 | 어디서 |
|---|---|---|
| `null` 소스에 `Where` | ★★ **호출 때** `ArgumentNullException` | (4) |
| 람다 안에서 0 으로 나누기 | ★★ **열거 때** `DivideByZeroException` — 정의한 줄이 아니다 | (4) |
| ★★★ 쿼리 정의 뒤 캡처 변수 변경 | ★★★ **진단 없음** — 결과가 **나중 값**으로 바뀐다 | (3) |
| ★★★ 같은 지연 쿼리를 두 번 소비 | ★★★ **진단 없음** — 두 번 돈다 · Java 는 `IllegalStateException` | (5) |
| ★★ `OrderBy(…).First()` 로 「하나만 읽겠지」 | ★★ **진단 없음** — `OrderBy` 는 첫 `MoveNext` 에서 **끝까지** 읽는다 | (1) |

## 어디서 틀리나

1. ★★★ **「지연 연산자는 원소를 한 개씩 당긴다」** — `OrderBy`·`Reverse`·`GroupBy` 는 **첫 `MoveNext` 에서 끝까지**(3 / 16)((1)).
2. ★★★ **「`Distinct` 도 다 모은 뒤 낸다」** — **한 개씩**이다(첫 `MoveNext` 뒤 1 줄)((1)).
3. ★★ **「`OrderBy(…).First()` 는 전부 정렬한 뒤 첫 것을 집는다」** — 이 판은 **최솟값만 찾았다**(`Compare` 9). 전부 정렬하는 것은 `foreach` 로 꺼낼 때다(36)((1-b)).
4. ★★★ **「`IEnumerable<T>` 를 돌려주면 지연이다」** — `ToList`·`ToArray`·`ToDictionary` 도 `IEnumerable` 을 구현한다. **이름**(`To…`)과 **로그**로 가른다((1)).
5. ★★★ **「`Any()` 는 컬렉션이면 첫 원소를 꺼낸다」** — `ICollection<T>` 면 **`Count` 속성만** 읽었다((2)). ★ 단 이것은 **BCL 구현**이다.
6. ★★★ **「쿼리를 만들 때의 변수 값이 들어간다」** — **열거할 때의 값**이다((3)).
7. ★★ **「LINQ 의 `null` 검사도 `yield` 처럼 늦게 터진다」** — 인자 검사는 **호출 때**, 람다 안의 예외는 **열거 때**((4)).
8. ★★ **「`IEnumerable<T>` 도 Java `Stream` 처럼 한 번만 쓸 수 있다」** — **다시 돈다**((5)).
9. ★ **「LINQ 는 느리다」** — **이 문서가 잰 것이 아니다.** 잰 것은 **로그 줄 수**다.

## 구현 세부사항 대 언어 보장

| 무엇 | 층 | 근거 |
|---|---|---|
| **람다가 변수를 잡는다(값이 아니라)** | ★★★ **언어** | (3) · [28번](../28-lambdas-and-closure-capture/) |
| **`xs.Where(f)` 가 `Enumerable.Where(xs, f)` 로 풀린다** | ★★★ **언어**(확장 메서드 호출) | [30번](../30-extension-methods-and-extension-members/) |
| **`null` 인자 → `ArgumentNullException`** | ★★ **BCL 계약**(XML 문서의 예외 조항) | (4) |
| **`TryGetNonEnumeratedCount` 가 열거를 강제하지 않는다** | ★★ **BCL 계약**(XML 요약) | (2) 의 근거 |
| **어느 연산자가 즉시이고 어느 것이 지연인가** | ★★ **BCL 계약**(Learn 의 분류 표 — ★ **이 배치는 안 열었다**) · ★★★ **로그는 이 판의 관찰** | (1) |
| **`OrderBy`·`Reverse`·`GroupBy` 가 첫 `MoveNext` 에서 끝까지 · `Distinct` 가 한 개씩 · `Chunk(2)` 가 두 개** | ★★★ **BCL 구현**(첫 결과의 정의상 셋은 그럴 수밖에 없다 — 모으는 **방법**은 구현) | (1) |
| **`Count()`·`Any()`·`ToList()` 가 `ICollection<T>` 를 알아본다** | ★★★ **BCL 구현** | (2) |
| **`OrderBy(…).First()`·`Take(1)` 이 정렬 대신 최솟값 찾기(`Compare` 9 대 36)** | ★★★ **BCL 구현** | (1-b) |
| **돌려준 타입 이름** | ★ **BCL 구현**(내부 클래스) | (1) |
| **Java `Stream` 재사용 → `IllegalStateException`** | ★★ **Java API 계약**(Java 46편) · 문구는 이 판 | (5) |

## 언제 쓰고 언제 안 쓰나

- ★★★ **여러 번 읽을 결과 · 조건 변수를 곧 바꿀 결과면 `ToList()` 로 굳혀라** — (3)의 `snap` · [32번](../32-yield-return-iterators-and-deferred-execution/) (7).
- ★★★ **한 번만 흘려 보낼 결과면 사슬째 둬라** — `Take`·`First` 가 필요한 만큼만 당긴다([32번](../32-yield-return-iterators-and-deferred-execution/) (6)의 `4 · 4`).
- ★★★ **`OrderBy` 앞에서 거를 수 있으면 먼저 걸러라** — `OrderBy` 는 **받은 것 전부**를 첫 `MoveNext` 에서 읽는다((1)). ★ 「그래서 빠르다」는 **재지 않았다** — 잰 것은 **읽는 줄 수**다.
- ★★ **「비었나」는 `Any()`** — `Count() > 0` 은 `IEnumerable<T>` 만 구현한 것이면 **끝까지** 센다((1) `Count()` 6 줄 대 `Any()` 1 줄).
- ★★ **「세기 싸면 세고, 아니면 말고」는 `TryGetNonEnumeratedCount`** — 열거하지 않는다는 것을 **문서가 약속**하는 쪽이다((2)).

## 핵심 문장

1. ★★★ **지연 실행은 언어가 아니라 `System.Linq` 가 짠 것이다 — 연산자마다 로그로 물어야 한다: 호출 즉시 소스를 건드린 칸 7 / 16**((1)).
2. ★★★ **「지연」은 「부를 때 안 돈다」까지만 말한다 — `OrderBy`·`Reverse`·`GroupBy` 는 첫 `MoveNext` 에서 끝까지, `Distinct` 는 한 개씩, `Chunk(2)` 는 두 개**((1)).
3. ★★★ **`ICollection<T>` 면 `Count()`·`Any()` 가 열거자를 안 만든다(4 / 12) — 문서가 아니라 구현이다. 약속이 필요하면 `TryGetNonEnumeratedCount`**((2)).
4. ★★★ **지연 쿼리는 변수와 소스를 열거 때 읽는다 — 정의 뒤에 바꾸면 결과가 바뀐다**((3)).
5. ★★ **C# 은 두 번 돌고 Java 는 두 번째에 던진다 — 같은 지연, 반대의 함정**((5)).

## 관련 자료

- [32번 — `yield return` 반복자와 지연 실행](../32-yield-return-iterators-and-deferred-execution/) (6)(7) — **경계**: 「사슬을 만들면 0 줄 · `ToList` 하면 `4 · 4` · 두 번 열거하면 두 번」은 거기서 쟀다. 여기는 **연산자별 두 시점 격자**와 **전부 읽는 지연 연산자.**
- [30번 — 확장 메서드](../30-extension-methods-and-extension-members/) (1) — LINQ 가 `Enumerable` 의 확장 메서드인 것.
- [28번 — 람다와 캡처](../28-lambdas-and-closure-capture/) (6) — 캡처한 변수를 고치면 양쪽이 본다.
- [31번 — `IEnumerable<T>` 와 `foreach`](../31-ienumerable-and-foreach/) — `ICollection<T>`·`IEnumerable<T>` 의 역할.
- 다음 — [34번 — 쿼리 구문](../34-linq-query-syntax/) · [35번 — 그룹·조인·집계](../35-linq-grouping-joins-and-aggregation/) · [36번 — `IQueryable`](../36-iqueryable-and-expression-trees/).
- Java 갈래 목록([`java/syntax/README.md`](../../../java/syntax/README.md))의 **44번**([`44-stream-creation/`](../../../java/syntax/44-stream-creation/)) · **45번**([`45-intermediate-operations/`](../../../java/syntax/45-intermediate-operations/) — `sorted`·`distinct` 는 **상태 있는 연산**) · **46번**([`46-terminal-operations/`](../../../java/syntax/46-terminal-operations/) — 재사용 `IllegalStateException`). ★ Java 45편은 `distinct` 를 `sorted` 와 같은 「모았다가 내보내는」 쪽에 두었다 — **C# `Distinct` 는 이 판에서 한 개씩**이었다. 두 언어의 구현이 다른 것인지는 **Java 쪽을 여기서 재지 않았다.**
- Python 갈래 목록([`python/syntax/README.md`](../../../python/syntax/README.md))의 **15번**([`15-generator-expressions-lazy-eval/`](../../../python/syntax/15-generator-expressions-lazy-eval/)) §4 — 두 번째 소비는 **예외가 아니라 빈 것**. 세 언어가 세 갈래다(C# 다시 돈다 · Java 던진다 · Python 비었다).
- JS 갈래 목록([`js/syntax/README.md`](../../../js/syntax/README.md))의 **21번**([`21-iterator-helpers/`](../../../js/syntax/21-iterator-helpers/)) — 이터레이터 헬퍼의 지연.
- Kotlin 갈래 목록([`kotlin/syntax/README.md`](../../../kotlin/syntax/README.md))의 **42번**(컬렉션 변환 — 기본 **즉시**) · **47번**(`Sequence` — 지연). ★ 폴더가 아직 없어 링크하지 않는다.

## 용어 풀이

- **지연 실행(deferred execution)** — 연산자를 부를 때가 아니라 **결과를 열거할 때** 소스를 읽는 것.
- **즉시 실행(immediate execution)** — 부르는 그 자리에서 소스를 읽어 값·컬렉션을 돌려주는 것(`ToList`·`Count()`·`First()`).
- **버퍼링(buffering)** — 첫 결과를 내기 전에 소스를 **모아 두는** 것. `OrderBy`·`Reverse`·`GroupBy` 가 그렇다((1)).
- **`ICollection<T>`** — 개수(`Count` 속성)·`Contains`·`CopyTo` 를 가진 컬렉션 인터페이스. `List<T>`·배열이 구현한다.
- **`TryGetNonEnumeratedCount`** — 열거 없이 개수를 알 수 있으면 알려 주는 메서드(.NET 6).
- **`AsEnumerable`** — 입력을 `IEnumerable<T>` **타입으로만** 보이게 하는 메서드. 객체는 그대로다.

## 더 들어가면

- ★ **`OrderBy(…).Last()` · `ElementAt(k)`** — (1-b)처럼 정렬을 건너뛰는 지름길이 더 있는지는 **`First`·`Take(1)` 만 쟀다.**
- ★ **판 경계** — `Distinct`·`Chunk` 의 당기는 개수가 옛 .NET 에서도 같았는지 **옛 판을 안 돌렸다.**
