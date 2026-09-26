# csharp/syntax/33 — LINQ 메서드 구문과 지연 실행 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력은 **.NET SDK 10.0.401** · 런타임 **10.0.12** · 타겟 **`net10.0`** ·
> **linux-x64** 에서 실제로 돌려 얻은 것이다(2026-09-26). 대비는 **javac/java 21.0.5** 다.\
> ★ 블록은 캡처 스크립트가 파일로 받아 조립기가 끼워 넣은 것이다 — 손으로 옮긴 줄은 없다.\
> **읽는 법** — 근거로 쓰는 것은 **로그 줄 수와 순서 · 호출 수 · 예외 타입과 시점 · 스크립트가 센 「N / M」** 이다. 돌려준 **타입 이름**은 BCL 내부라 근거로 쓰지 않는다.
> ★★★ **이 문서는 시간을 재지 않았다.** 「LINQ 는 느리다」·「`First()` 가 빠르다」는 문장이 **한 줄도 없다.**

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ **호출 즉시 7 / 16**(끝까지 다섯 · 한 줄 둘) · **호출 0 줄인데 첫 `MoveNext` 에서 끝까지 3 / 16**(`OrderBy`·`Reverse`·`GroupBy`)

**출력**

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

**왜 그런가**

- ★★★ **`ToList`·`ToArray`·`Count()`·`Sum()`·`ToDictionary` — 호출 직후 6 줄**(`pull` 다섯 + `end`) · **`Any()`·`First()` — 1 줄.** 즉시 연산자는 **부르는 자리에서** 소스를 읽는다. `Any`·`First` 는 답이 나오자 **멈췄다.**
- ★★★ **`Where`·`Select`·`Take(2)`·`Distinct`·`AsEnumerable` — 0 → 1** · **`Chunk(2)` — 0 → 2** · **`OrderBy`·`Reverse`·`GroupBy` — 0 → 6.** 「지연」 셋 모두 부를 때는 0 줄이지만 **첫 결과에 필요한 양이 다르다.**
- ★★ `ToList`·`ToArray`·`ToDictionary` 는 `MoveNext` 뒤에도 6 — 이미 모은 것을 읽는다.

### 2. ★★ **키 선택자는 넷 다 10 번** · **`Compare` 는 `First()`·`Take(1)` 이 9 번, `foreach` 첫 원소·`ToList()` 가 36 번**

**출력**

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

**왜 그런가**

- ★★★ **키는 전부 계산했다(10)** — 1번의 「첫 `MoveNext` 에서 끝까지」와 같은 사실이다.
- ★★★ **9 는 최솟값 찾기 · 36 은 전부 정렬** — `First()` 와 `Take(1)` 은 `OrderBy` 의 결과 객체가 **뒤에 붙은 연산을 알아보고** 지름길을 탔다. `foreach` 는 그 정보를 안 주므로 **정렬부터** 했다. ★ **BCL 구현**이다 — 문서는 비교 횟수를 약속하지 않는다.

### 3. ★★★ **`ICollection<int>` 열의 `Count()`·`Any()`·`ToList()`·`Contains` 는 `GetEnumerator` 없이** — **4 / 12**

**출력**

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

**왜 그런가**

- ★★★ `Enumerable.Count`·`Any`·`ToList`·`Contains` 가 받은 객체의 **실제 타입을 검사**해 `ICollection<T>` 면 **`Count` 속성 · `CopyTo` · 자기 `Contains`** 로 갔다. `IEnumerable<int>` 만 구현한 쪽은 전부 **`GetEnumerator`**.
- ★★ 조건이 붙은 `Count(x => x > 1)` 와 `Where` 를 거친 `Count()` 는 **양쪽 다 열거**했다 — 하나씩 봐야 하거나, 받은 객체가 이미 `ICollection` 이 아니다.

### 4. ★★★ **`[1]` `[5]` · `[2]` `[3, 4, 5]` · `[3]` `[5, 6]` · `[4]` `[3, 4, 5]`**

**출력**

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

**왜 그런가**

- ★★★ 지연 쿼리 `q` 는 **열거할 때** 소스를 읽고 람다를 부른다 — 그때의 `threshold`(4)와 그때의 `src`(6 이 붙은 것)를 본다.
- ★★★ `snap` 은 `ToList()` 가 **정의한 그 줄에서** 람다를 불러 굳힌 리스트다 — 뒤의 변경이 안 닿는다.

### 5. ★★ **`[1]`·`[2]` 호출 때 `ArgumentNullException`** · **`[3]`·`[4]` 열거 때 `DivideByZeroException`**

**출력**

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

**왜 그런가**

- ★★★ **인자 검사는 호출 때** — XML 문서가 `source`·`predicate` 에 `ArgumentNullException` 조항을 두고, 이 판은 **부르는 줄에서** 던졌다.
- ★★★ **람다 안의 예외는 열거 때** — 람다는 열거 때 불린다. `OrderBy` 는 첫 `MoveNext` 에서 **모든 키**를 계산하므로 0 이 어디 있든 첫 `MoveNext` 에서 터진다.

### 6. ★★★ **C# `둘째 : 2`** · **Java `둘째 : java.lang.IllegalStateException: stream has already been operated upon or closed`**

**출력**

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

**왜 그런가**

- ★★★ C# `IEnumerable<T>` 는 **`GetEnumerator` 를 부를 때마다 새로** 돈다 — 다시 쓸 수 있고 **매번 비용을 낸다.** Java `Stream` 은 **파이프라인 한 번**이라 두 번째 최종 연산에서 던진다.

### 7. ★★★ **`OrderBy` 는 「가장 작은 것」 · `Reverse` 는 「마지막 것」 · `GroupBy` 는 「첫 키의 전부」를 알아야 해서 끝까지** — **`Distinct` 는 「처음 본 것」이라 하나로 된다**

- ★★★ **첫 결과의 정의**가 읽는 양을 정한다. 뒤에 더 작은 것이 있을지 · 어디가 끝인지 · 같은 키가 또 나올지는 **끝을 봐야** 안다. `Distinct` 의 첫 결과는 **첫 원소 그 자체**다(아직 본 것이 없으니 중복일 수 없다).
- ★★ **2번은 다른 것을 말한다** — 1번은 **「얼마나 읽나」**(끝까지)이고 2번은 **「읽은 뒤 무엇을 하나」**(정렬 대 최솟값)다. `First()` 도 **끝까지 읽기는** 한다(키 10 번).

### 8. ★★ **못 가른다** — 셋 다 `IEnumerable` 이라 1번 스크립트가 `MoveNext` 를 불렀다(`6 → 6`) · `AsEnumerable` 의 타입은 **`<Src>d__1`**(소스 그 자체)

- ★★ `List<T>`·배열·`Dictionary` 도 `IEnumerable<T>` 를 구현한다. **이름(`To…`)** 과 **로그**로 가른다.
- ★ `AsEnumerable` 은 **객체를 바꾸지 않고 정적 타입만** `IEnumerable<T>` 로 바꾼다(XML 요약 「입력을 `IEnumerable<T>` 타입으로 돌려준다」). 그 쓸모는 [36번](../36-iqueryable-and-expression-trees/) — 뒤쪽을 `Enumerable` 쪽 메서드로 **골라 부르게** 하는 것.

### 9. ★★★ **BCL 구현이다 — 언어 보장이 아니다** · XML `Count` 에는 **예외 두 조항과 반환값뿐** · 약속하는 쪽은 **`TryGetNonEnumeratedCount`**

- ★★★ C# 언어는 `Count()` 가 무엇을 하는지 모른다 — 그것은 **라이브러리 메서드**다. 그 메서드의 문서(XML)에도 `ICollection` 지름길 조항이 없다. 남는 것은 **이 판의 구현**이다.
- ★★ `TryGetNonEnumeratedCount` 의 요약이 「**열거를 강제하지 않고** 개수를 알아내려 시도한다」 — 못 알면 `false` 다.

### 10. ★★ **BCL 의 LINQ 는 32번 (2)의 `DoubledSplit` 모양이다 — 바깥에서 검사하고 안쪽이 지연** · 4번 `[1]` 은 **람다가 `threshold` 변수를 잡았기** 때문

- ★★ [32번](../32-yield-return-iterators-and-deferred-execution/) (2)의 `Doubled` 는 `yield` 가 메서드 전체를 반복자로 만들어 검사가 늦었다. `Enumerable.Where` 는 **호출 때** 던졌으니 **바깥 = 검사**가 따로 있는 모양이다(구현은 열어 보지 않았다 — 관찰은 시점까지).
- ★ [28번](../28-lambdas-and-closure-capture/) (6) — 람다와 바깥 코드가 **같은 변수**를 본다. 지연 실행은 그 람다를 **나중에** 부를 뿐이다.

### 11. ★★ **Java 46편과 같은 예외 · Java 45편의 `sorted` 와 같은 「다 모은 뒤」** · Python 은 **빈 것** — 세 언어가 **다시 돈다 · 던진다 · 비었다**로 갈린다

- ★★ [Java 46번](../../../java/syntax/46-terminal-operations/) — `stream has already been operated upon or closed` 로 같은 문구. [Java 45번](../../../java/syntax/45-intermediate-operations/) — `sorted` 는 **상태 있는 연산**이라 전부 모일 때까지 막힌다 — 1번의 `OrderBy` 줄과 같은 모양이다. ★ 다만 Java 45편은 `distinct` 도 그쪽에 두었고, C# `Distinct` 는 이 판에서 **한 개씩**이었다(Java 쪽은 여기서 재지 않았다).
- ★ [Python 15번](../../../python/syntax/15-generator-expressions-lazy-eval/) §4 — 두 번째 소비가 **예외 없이 빈 결과**.

## 실행 검증

| 무엇 | 몇 번·어디서 | 결과 |
|---|---|---|
| `cs33b-grid.cs` | csc 1회 · 실행 1회 | ★★★ **호출 즉시 7 / 16** · **첫 `MoveNext` 에서 끝까지 3 / 16** · `Distinct` 1 · `Chunk(2)` 2 |
| `cs33b-sort.cs` | csc 1회 · 실행 1회 | ★★★ 키 10 · `Compare` **9 · 9 · 36 · 36** |
| `cs33b-count.cs` | csc 1회 · 실행 1회 | ★★★ **GetEnumerator 가 안 불린 칸 4 / 12** |
| `cs33b-capture.cs` | csc 1회 · 실행 1회 | `[5]` · `[3, 4, 5]` · `[5, 6]` · `[3, 4, 5]` |
| `cs33b-when.cs` | csc 1회 · 실행 1회 | 호출 때 `ArgumentNullException` 둘 · 열거 때 `DivideByZeroException` 둘 |
| `cs33b-reuse.cs` · `Reuse33.java` | csc·javac 1회씩 · 실행 1회씩 | C# `2 · 2` · Java `2 · IllegalStateException` |
| `System.Linq.xml` | `grep` 1회 | `deferred 0 · lazy 0 · member 244` |
| `cs33b-form.cs` | csc 1회 · 실행 1회 | `kim:31 park:31 lee:25` · `choi kim lee park` |
| `cs33b-v2.cs` · `cs33b-v2e.cs` | csc 3회(`-langversion:2` 둘 · `3` 하나) | 람다 `CS8023` · 확장 메서드 **호출**은 통과 · **선언**은 `CS8023` |

**구현 의존 항목** — 다음은 **이 판(.NET SDK 10.0.401 · 런타임 10.0.12)에서만** 그렇다.

- ★★★ **연산자별로 첫 `MoveNext` 에 읽는 양**(`Distinct` 1 · `Chunk(2)` 2 · `OrderBy`·`Reverse`·`GroupBy` 끝까지) · **`ICollection<T>` 지름길** · **`First()`·`Take(1)` 의 최솟값 지름길(`Compare` 9)** · 돌려준 타입 이름 · Java 예외 문구.

**언어·문서가 보장하는 것**(구현이 바뀌어도 같다)

- **람다가 변수를 잡는다**(언어) · **`null` 인자 → `ArgumentNullException`**(XML 문서) · **`TryGetNonEnumeratedCount` 가 열거를 강제하지 않는다**(XML 문서).

**안 돌려 본 것 / 못 잰 것 / 잴 것이 없는 것**

- **안 돌려 본 것** — ★ Learn 의 「실행 방식 분류」 표(외부 네트워크를 안 썼다) · 옛 .NET **런타임** 판(참조 팩이 10.0.12 하나뿐) · `OrderBy(…).Last()`·`ElementAt` 의 지름길 · Java `distinct` 의 버퍼링.
- **못 잰 것** — ★★★ **시간**.
- **잴 것이 없는 것** — ★ **IL 창** — 이 주제의 질문은 「언제 읽나」라 IL 이 답하지 않는다([30번](../30-extension-methods-and-extension-members/) 인용).

**버전이 올랐을 때 다시 돌려야 하는 것**

- ★★★ **1번 · 2번 · 3번** — 전부 **BCL 구현**을 잰 것이다. `System.Linq` 가 판마다 지름길을 늘리거나 바꾸면 줄 수·호출 수가 바뀐다(언어는 안 바뀐다).
