# csharp/syntax/31 — `IEnumerable<T>` 와 `foreach` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·진단·IL·할당 바이트는 **.NET SDK 10.0.401** · 런타임 **10.0.12** · 타겟 **`net10.0`** ·
> **linux-x64** 에서 실제로 돌려 얻은 것이다(2026-09-26). 대비는 **javac 21.0.5** 다.\
> 진단은 **`-preferreduilang:en-US`** 로 영어로 고정했다.\
> ★ 블록은 캡처 스크립트가 파일로 받아 조립기가 끼워 넣은 것이다 — 손으로 옮긴 줄은 없다.\
> ★ 진단을 싣는 블록은 전부 **그 진단을 낸 소스를 같은 블록 안에** 다시 싣는다(`===== 소스: … =====`).
> **읽는 법** — 근거로 쓰는 것은 **옵코드 · `.try … finally` 의 유무 · 진단 코드 · 할당 바이트의 0 대 비(非)0 · 「네 판에서 갈린 줄 N / M」 · 예외 타입** 이다.
> ★★★ **이 문서는 시간을 재지 않았다.** 「구조체 열거자가 빠르다」는 문장이 **한 줄도 없다.**

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ **된다 — `0` · `0` · `60`** · IL 은 **`call …Walker::MoveNext`** · `Dispose` 는 **안 불린다**

**출력**

```text
===== 소스: cs31b-pattern.cs =====
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
===== csc -optimize -r:il.dll -out:exo.dll cs31b-pattern.cs && dotnet exo.dll (cc exit=0 · run exit=0) =====
[1] Bag 이 구현한 인터페이스 수 : 0
[2] Walker 가 구현한 인터페이스 수 : 0
[3] Probe.Sum(new Bag()) = 60
--- Probe.Sum ---
  .locals [0] System.Int32
  .locals [1] Bag+Walker
  .locals [2] System.Int32
  IL_0000: ldc.i4.0
  IL_0001: stloc.0
  IL_0002: ldarg.0
  IL_0003: callvirt Bag::GetEnumerator
  IL_0008: stloc.1
  IL_0009: br.s IL_0017
  IL_000b: ldloca.s 1
  IL_000d: call Bag+Walker::get_Current
  IL_0012: stloc.2
  IL_0013: ldloc.0
  IL_0014: ldloc.2
  IL_0015: add
  IL_0016: stloc.0
  IL_0017: ldloca.s 1
  IL_0019: call Bag+Walker::MoveNext
  IL_001e: brtrue.s IL_000b
  IL_0020: ldloc.0
  IL_0021: ret
```

**왜 그런가**

- ★★★ `foreach` 는 **`GetEnumerator`·`MoveNext`·`Current` 라는 이름**을 찾았다 — 인터페이스가 0 개여도 된다.
- ★★★ 찾은 **구조체 `Walker` 의 메서드를 `call` 로 직접** 부른다(`ldloca.s 1`).
- ★★ **`Walker` 는 `IDisposable` 이 아니라** `Dispose` 를 부르는 `try`/`finally` 가 **아예 없다.**

### 2. ★★ **`0 1 2`** · C# 8 은 **`CS8400`** · `Plain` 은 **`CS1579`**

**출력**

```text
===== 소스: cs31b-ext.cs =====
using System;
using System.Collections.Generic;
static class RangeExt {
    public static IEnumerator<int> GetEnumerator(this int n) { for (int i = 0; i < n; i++) yield return i; }
}
class Program {
    static void Main() { foreach (var i in 3) Console.Write(i + " "); Console.WriteLine(); }
}
===== csc -out:ex.dll cs31b-ext.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
0 1 2 
===== csc -langversion:8 -out:ex.dll cs31b-ext.cs (cc exit=1) =====
cs31b-ext.cs(7,44): error CS8400: Feature 'extension GetEnumerator' is not available in C# 8.0. Please use language version 9.0 or greater.
===== 소스: cs31b-none.cs =====
class Plain { }
class Program {
    static void Main() { foreach (var x in new Plain()) { } }
}
===== csc -out:ex.dll cs31b-none.cs (cc exit=1) =====
cs31b-none.cs(3,44): error CS1579: foreach statement cannot operate on variables of type 'Plain' because 'Plain' does not contain a public instance or extension definition for 'GetEnumerator'
```

**왜 그런가**

- ★★ `GetEnumerator` 찾기는 **인스턴스 → 확장** 순서다(C# 9). `CS1579` 의 문구가 「public instance **or extension** definition」 이다.

### 3. ★★ **`GetEnumerator` · `Current`(+ `MoveNext`·`Reset`·`Dispose` 상속) · `Count`·`Add`·…** — `List<int>` 는 **구조체 `Enumerator`**

**출력**

```text
===== 소스: cs31b-roles.cs =====
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
===== csc -out:ex.dll cs31b-roles.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
IEnumerable`1   자기 멤버 : GetEnumerator  ·  상위 : IEnumerable
IEnumerator`1   자기 멤버 : Current  ·  상위 : IDisposable,IEnumerator
ICollection`1   자기 멤버 : Add Clear Contains CopyTo Count IsReadOnly Remove  ·  상위 : IEnumerable,IEnumerable`1
IList`1         자기 멤버 : IndexOf Insert Item RemoveAt  ·  상위 : ICollection`1,IEnumerable,IEnumerable`1
List<int> 의 공개 GetEnumerator 반환 타입 : Enumerator (struct)
IEnumerable<int> 로 받아 부른 GetEnumerator 의 실제 타입 : Enumerator · 그 실제 타입이 값 타입인가 : True
```

**왜 그런가**

- ★★★ **`IEnumerable<T>` = 열거자를 만든다 · `IEnumerator<T>` = 커서 · `ICollection<T>` = 셀 수 있고 고칠 수 있다.**
- ★★ `IEnumerable<int>` 로 받아도 **실제 열거자는 같은 구조체**다 — 그것이 **`IEnumerator<int>` 변수**에 담기는 순간 박스가 된다(9번).

### 4. ★★★ **`OverList`·`OverSeq` 에 `finally`** — 구조체는 **`constrained. callvirt Dispose`**, 인터페이스는 **널 검사 후 `callvirt Dispose`** · 배열은 **`GetEnumerator` 없음**

**출력**

```text
===== 소스: cs31b-il.cs =====
using System.Collections.Generic;
public static class L {
    public static int OverList(List<int> xs) { int s = 0; foreach (var x in xs) s += x; return s; }
    public static int OverSeq(IEnumerable<int> xs) { int s = 0; foreach (var x in xs) s += x; return s; }
    public static int OverArray(int[] xs) { int s = 0; foreach (var x in xs) s += x; return s; }
}
class Program {
    static void Main() { Il.Dump(typeof(L), "OverList"); Il.Dump(typeof(L), "OverSeq"); Il.Dump(typeof(L), "OverArray"); }
}
===== csc -optimize -r:il.dll -out:exo.dll cs31b-il.cs && dotnet exo.dll (cc exit=0 · run exit=0) =====
--- L.OverList ---
  .locals [0] System.Int32
  .locals [1] System.Collections.Generic.List+Enumerator<System.Int32>
  .locals [2] System.Int32
  .try IL_0009 to IL_0022 finally IL_0022 to IL_0030
  IL_0000: ldc.i4.0
  IL_0001: stloc.0
  IL_0002: ldarg.0
  IL_0003: callvirt System.Collections.Generic.List<System.Int32>::GetEnumerator
  IL_0008: stloc.1
  IL_0009: br.s IL_0017
  IL_000b: ldloca.s 1
  IL_000d: call System.Collections.Generic.List+Enumerator<System.Int32>::get_Current
  IL_0012: stloc.2
  IL_0013: ldloc.0
  IL_0014: ldloc.2
  IL_0015: add
  IL_0016: stloc.0
  IL_0017: ldloca.s 1
  IL_0019: call System.Collections.Generic.List+Enumerator<System.Int32>::MoveNext
  IL_001e: brtrue.s IL_000b
  IL_0020: leave.s IL_0030
  IL_0022: ldloca.s 1
  IL_0024: constrained. System.Collections.Generic.List+Enumerator<System.Int32>
  IL_002a: callvirt System.IDisposable::Dispose
  IL_002f: endfinally
  IL_0030: ldloc.0
  IL_0031: ret
--- L.OverSeq ---
  .locals [0] System.Int32
  .locals [1] System.Collections.Generic.IEnumerator<System.Int32>
  .locals [2] System.Int32
  .try IL_0009 to IL_0020 finally IL_0020 to IL_002a
  IL_0000: ldc.i4.0
  IL_0001: stloc.0
  IL_0002: ldarg.0
  IL_0003: callvirt System.Collections.Generic.IEnumerable<System.Int32>::GetEnumerator
  IL_0008: stloc.1
  IL_0009: br.s IL_0016
  IL_000b: ldloc.1
  IL_000c: callvirt System.Collections.Generic.IEnumerator<System.Int32>::get_Current
  IL_0011: stloc.2
  IL_0012: ldloc.0
  IL_0013: ldloc.2
  IL_0014: add
  IL_0015: stloc.0
  IL_0016: ldloc.1
  IL_0017: callvirt System.Collections.IEnumerator::MoveNext
  IL_001c: brtrue.s IL_000b
  IL_001e: leave.s IL_002a
  IL_0020: ldloc.1
  IL_0021: brfalse.s IL_0029
  IL_0023: ldloc.1
  IL_0024: callvirt System.IDisposable::Dispose
  IL_0029: endfinally
  IL_002a: ldloc.0
  IL_002b: ret
--- L.OverArray ---
  .locals [0] System.Int32
  .locals [1] System.Int32[]
  .locals [2] System.Int32
  .locals [3] System.Int32
  IL_0000: ldc.i4.0
  IL_0001: stloc.0
  IL_0002: ldarg.0
  IL_0003: stloc.1
  IL_0004: ldc.i4.0
  IL_0005: stloc.2
  IL_0006: br.s IL_0014
  IL_0008: ldloc.1
  IL_0009: ldloc.2
  IL_000a: ldelem.i4
  IL_000b: stloc.3
  IL_000c: ldloc.0
  IL_000d: ldloc.3
  IL_000e: add
  IL_000f: stloc.0
  IL_0010: ldloc.2
  IL_0011: ldc.i4.1
  IL_0012: add
  IL_0013: stloc.2
  IL_0014: ldloc.2
  IL_0015: ldloc.1
  IL_0016: ldlen
  IL_0017: conv.i4
  IL_0018: blt.s IL_0008
  IL_001a: ldloc.0
  IL_001b: ret
```

**왜 그런가**

- ★★★ `List<int>` 로 받으면 **`List+Enumerator<Int32>` 지역 변수 + `call`** · `IEnumerable<int>` 로 받으면 **`IEnumerator<Int32>` 지역 변수 + `callvirt`** · 배열은 **`ldelem.i4` 인덱스 고리**.

### 5. ★★★ **`0` · `40000` · `0` · `32000`** — 네 판 **0 / 4**

**출력**

```text
===== 소스: cs31b-alloc.cs =====
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
===== csc -out:ex.dll cs31b-alloc.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
[1] List<int> 를 List<int> 로 foreach        1000번 : 0 바이트
[2] List<int> 를 IEnumerable<int> 로 foreach 1000번 : 40000 바이트
[3] int[] 를 int[] 로 foreach                1000번 : 0 바이트
[4] int[] 를 IEnumerable<int> 로 foreach     1000번 : 32000 바이트
===== csc -out:ex.dll cs31b-alloc.cs && DOTNET_TieredCompilation=0 dotnet ex.dll (cc exit=0 · run exit=0) =====
[1] List<int> 를 List<int> 로 foreach        1000번 : 0 바이트
[2] List<int> 를 IEnumerable<int> 로 foreach 1000번 : 40000 바이트
[3] int[] 를 int[] 로 foreach                1000번 : 0 바이트
[4] int[] 를 IEnumerable<int> 로 foreach     1000번 : 32000 바이트
===== csc -optimize -out:exo.dll cs31b-alloc.cs && dotnet exo.dll (cc exit=0 · run exit=0) =====
[1] List<int> 를 List<int> 로 foreach        1000번 : 0 바이트
[2] List<int> 를 IEnumerable<int> 로 foreach 1000번 : 40000 바이트
[3] int[] 를 int[] 로 foreach                1000번 : 0 바이트
[4] int[] 를 IEnumerable<int> 로 foreach     1000번 : 32000 바이트
===== csc -optimize -out:exo.dll cs31b-alloc.cs && DOTNET_TieredCompilation=0 dotnet exo.dll (cc exit=0 · run exit=0) =====
[1] List<int> 를 List<int> 로 foreach        1000번 : 0 바이트
[2] List<int> 를 IEnumerable<int> 로 foreach 1000번 : 40000 바이트
[3] int[] 를 int[] 로 foreach                1000번 : 0 바이트
[4] int[] 를 IEnumerable<int> 로 foreach     1000번 : 32000 바이트
===== 네 판 대조 — 「바이트」 줄마다 네 판의 값이 같은가 =====
네 판에서 갈린 줄 0 / 4
```

**왜 그런가**

- ★★★ 받는 타입이 **구체 타입이면 0**, **`IEnumerable<int>` 면 `foreach` 마다 열거자 객체 하나** — 같은 `List<int>` 인데 갈린다(9번).
- ★★ 첫 캡처(짧게 데운 판)에서는 **한 칸이 한 번 움직였다**(`[4]` 가 `32`) — 길게 데운 판으로 바꾸자 **네 판 0 / 4**(요약 (5)).

### 6. ★★★ **`[1]`·`[2]`·`[3]`·`[6]` 이 던진다** · `_version` **`3 → 4 → 5 → 5`** · Java 는 **`[3]` 을 안 던진다**

**출력**

```text
===== 소스: cs31b-mod.cs =====
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
===== csc -out:ex.dll cs31b-mod.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
[1] List · x==1 에서 Add(9)          : InvalidOperationException: Collection was modified; enumeration operation may not execute.
[2] List · x==1 에서 l[2] = 9        : InvalidOperationException: Collection was modified; enumeration operation may not execute.
[3] List · x==2 에서 Remove(3)       : InvalidOperationException: Collection was modified; enumeration operation may not execute.
[4] Dictionary · 키 1 에서 Remove(2)  : 끝까지 돎
[5] Dictionary · 키 1 에서 d[2] = 9   : 끝까지 돎
[6] Dictionary · 키 1 에서 d[4] = 9   : InvalidOperationException: Collection was modified; enumeration operation may not execute.
[7] 배열 · x==1 에서 a[2] = 9          : 끝까지 돎
[8] List 의 숨은 필드 _version : 처음 3 · Add 뒤 4 · l[0]=7 뒤 5 · 읽기 l[0] 뒤 5
===== 소스: Ex31.java =====
import java.util.*;
public class Ex31 {
    static void t(String n, Runnable r) {
        try { r.run(); System.out.println(n + " : 끝까지 돎"); }
        catch (RuntimeException e) { System.out.println(n + " : " + e.getClass().getSimpleName()); }
    }
    public static void main(String[] args) {
        t("[1] ArrayList · x==1 에서 add(9)", () -> { var l = new ArrayList<>(List.of(1, 2, 3)); for (int x : l) if (x == 1) l.add(9); });
        t("[3] ArrayList · x==2 에서 remove(3)", () -> { var l = new ArrayList<>(List.of(1, 2, 3)); for (int x : l) if (x == 2) l.remove(Integer.valueOf(3)); });
    }
}
===== javac -d j31out j31/Ex31.java && java -cp j31out Ex31 (cc exit=0 · run exit=0) =====
[1] ArrayList · x==1 에서 add(9) : ConcurrentModificationException
[3] ArrayList · x==2 에서 remove(3) : 끝까지 돎
```

**왜 그런가**

- ★★★ `List<T>` 는 **모든 쓰기**(값 덮어쓰기 포함)에서 `_version` 을 올리고, 열거자가 `MoveNext` 마다 대조한다 — **끝에 닿을 때도.**
- ★★★ Java `ArrayList` 는 `[3]` 에서 **`cursor == size` 가 되어 검사 없이 끝난다** — 마지막 원소 `3` 을 지운 것은 맞지만, **이 모양은 조용히 통과**한다([Java 43번](../../../java/syntax/43-iterator-and-fail-fast/) 의 「끝에서 두 번째」).
- ★★ `Dictionary` 는 **`Remove`·기존 키 덮어쓰기에서 안 던졌다**(이 판) · 새 키만 던졌다. 배열은 번호가 없다.

### 7. ★★ **셋 다 `Dispose`** — `[3]` 은 `Dispose` 다음에 `바깥 catch`

**출력**

```text
===== 소스: cs31b-dispose.cs =====
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
===== csc -out:ex.dll cs31b-dispose.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
[1] 끝까지
  GetEnumerator
  MoveNext → True
  Current → 1
  몸통 1
  MoveNext → True
  Current → 2
  몸통 2
  MoveNext → True
  Current → 3
  몸통 3
  MoveNext → False
  Dispose
[2] x == 2 에서 break
  GetEnumerator
  MoveNext → True
  Current → 1
  몸통 1
  MoveNext → True
  Current → 2
  몸통 2
  Dispose
[3] x == 1 에서 몸통이 던진다
  GetEnumerator
  MoveNext → True
  Current → 1
  몸통 1
  Dispose
  바깥 catch : body
```

**왜 그런가**

- ★★ 4번의 `finally` — 정상 종료·`break`·예외 모두 `Dispose` 를 **한 번** 부르고, 예외는 그 **뒤에** 바깥으로 나간다.

### 8. ★★★ **이름으로 찾고 찾은 타입 그대로 부른다** — `Dispose` 만은 **`IDisposable` 로** 찾는다

- ★★★ 1번 — 인터페이스 0 개인 `Bag` 이 컴파일됐다. 4번 — `List<int>` 판도 **`call …Enumerator::MoveNext`** 로 인터페이스를 안 거친다. 그래서 「`foreach` 는 `IEnumerable` 을 안 봐도 된다」.
- ★★ 그런데 1번 `Walker` 의 `public void Dispose()` 는 **안 불렸다** — `Dispose` 는 이름 패턴이 아니라 **열거자 타입이 `IDisposable` 인가**로 정한다(`ref struct` 예외는 이 판에서 안 던졌다).

### 9. ★★★ **`IEnumerable<int>` 변수로 받은 `GetEnumerator()` 가 인터페이스를 돌려주므로 구조체가 박스에 담긴다**

- ★★★ 4번 — `OverSeq` 는 `callvirt IEnumerable<Int32>::GetEnumerator` 로 **`IEnumerator<Int32>`** 를 받는다. 3번 — 그 실제 타입은 **값 타입 `Enumerator`** 다. 값 타입이 인터페이스 변수에 담기면 박싱([03번](../03-boxing-and-unboxing/)) — 5번 `[2]` 40000.
- ★★ [24번](../24-generics-and-type-parameters/) 과의 경계 — 거기는 **제네릭 타입 인자**가 값 타입일 때 코드를 따로 만드는 이야기이고, 여기는 **변수의 선언 타입이 인터페이스**라서 생기는 박싱이다. `IEnumerable<T>` 를 받는 제네릭 메서드는 **`T` 가 무엇이든** 이 박싱을 한다.

### 10. ★★ **C# 실행(매 `MoveNext`) · Java 실행(`next()`) · Rust 컴파일(`E0502`)** — 갈린 칸은 **「끝에 닿을 때도 대조하나」**

- ★★ 6번 블록 + [Java 43번](../../../java/syntax/43-iterator-and-fail-fast/) + [Rust 38번](../../../rust/syntax/38-vec-api-capacity-retain-and-drain/)(순회 중 `push`·`remove` 는 **빌림이 살아 있는 동안** 컴파일 에러).

### 11. 잇기

- ★★ **[32번](../32-yield-return-iterators-and-deferred-execution/)** — `yield return` 이 `MoveNext`/`Current`/`Dispose` 를 가진 클래스를 **컴파일러가 만든다.**
- ★ **아니다** — 목록 패턴은 **`Length`/`Count` + 인덱서**를 찾는다([21번](../21-pattern-matching-type-property-relational-list/) (2)).

## 실행 검증

| 무엇 | 몇 번·어디서 | 결과 |
|---|---|---|
| `cs31b-pattern.cs` | csc 1회(`-optimize`) · 실행 1회 | ★★★ 인터페이스 0 · `call …Walker::MoveNext` · `finally` 없음 |
| `cs31b-ext.cs` · `cs31b-none.cs` | csc 3회(latest · 8) · 실행 1회 | `0 1 2` · `CS8400` · `CS1579` |
| `cs31b-roles.cs` | csc 1회 · 실행 1회 | 세 역할의 멤버 · `Enumerator (struct)` |
| `cs31b-il.cs` | csc 1회(`-optimize`) · 실행 1회 | 구조체 `constrained.` · 인터페이스 `callvirt` · 배열 `ldelem` |
| `cs31b-alloc.cs` | **2×2 판 격자**(길게 데움) | ★★★ `0 · 40000 · 0 · 32000` · **갈린 줄 0 / 4** — ★ 짧게 데운 첫 판에서 한 칸이 `32` |
| `cs31b-mod.cs` · `Ex31.java` | csc 1회 · 실행 1회 · javac 1회 · java 1회 | ★★★ List 셋 · Dictionary 새 키 던짐 · `_version` · **Java `[3]` 안 던짐** |
| `cs31b-dispose.cs` | csc 1회 · 실행 1회 | 셋 다 `Dispose` 한 번 |
| `cs31b-form.cs` | csc 1회 · 실행 1회 | `bac · x=1 · bac` |

**구현 의존 항목** — 다음은 **이 판(.NET SDK 10.0.401 · 런타임 10.0.12 · javac 21.0.5)에서만** 그렇다.

- ★★★ **할당 바이트 값 · `_version` 필드 · `Dictionary` 의 `Remove`/덮어쓰기가 열거를 안 깨는 것 · `constrained.` 로 부르는 모양** — BCL · Roslyn · 이 판.

**언어가 보장하는 것**(구현이 바뀌어도 같다)

- **패턴 기반 `foreach` · 확장 `GetEnumerator`(C# 9) · `IDisposable` 열거자의 `finally` `Dispose`.**

**안 돌려 본 것 / 못 잰 것 / 잴 것이 없는 것**

- **안 돌려 본 것** — ★ `ref struct` 패턴 `Dispose` · `Span<T>` `foreach` · `foreach (ref …)` · `await foreach`.
- **못 잰 것** — ★★★ **시간**.
- **잴 것이 없는 것** — 없다.

**버전이 올랐을 때 다시 돌려야 하는 것**

- ★★★ **5번** — JIT 이 인터페이스 `foreach` 의 열거자를 **스택으로 내리게 되면**(탈가상화 + 탈출 분석) `[2]`·`[4]` 가 0 으로 움직인다. 첫 캡처의 흔들린 한 칸이 그 신호일 수 있다.
- ★★ **6번 `[4]`·`[5]`** — `Dictionary` 의 판 관찰.
