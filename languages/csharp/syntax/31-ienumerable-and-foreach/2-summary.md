# csharp/syntax/31 — `IEnumerable<T>` 와 `foreach` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [ECMA-334 7판(2023-12)](https://ecma-international.org/publications-and-standards/standards/ecma-334/) §13.9.5 「The foreach statement」 ·
> [Learn — 반복문(`foreach`)](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/statements/iteration-statements)(열어서 확인: 「`foreach` 는 `IEnumerable`·`IEnumerable<T>` 를 구현한 타입에 쓴다 — **그 타입들로 한정되지 않는다**」 ·\
> 「타입에 **공개 매개변수 없는 `GetEnumerator`** 가 있고(**확장 메서드여도 된다**), 그 반환 타입에 **공개 `Current` 속성과 `bool` 을 돌려주는 매개변수 없는 `MoveNext`** 가 있으면 된다」 ·\
> 「`Span<T>` 는 **아무 인터페이스도 구현하지 않는다**」 · 「`null` 에 `foreach` 하면 `NullReferenceException`」).
> **실행 검증** — 이 문서의 모든 출력·진단·IL·할당 바이트는 아래 「이 판」의 도구로 **실제로 돌려 얻은 것**이다(2026-09-26).\
> ★ 블록은 캡처 스크립트가 파일로 받아 조립기가 끼워 넣은 것이다 — 사람이 옮겨 적은 줄은 하나도 없다. **대비는 실측이다** — **javac 21.0.5** 로 같은 수정 두 줄을 던졌다((6)).
> **버전** — `foreach`·`IEnumerable` **C# 1** · `IEnumerable<T>` **C# 2** · **확장 `GetEnumerator` C# 9**(★ `-langversion:8` 에서 **`CS8400 … extension GetEnumerator … 9.0 or greater`** · (2)) · `foreach` 반복 변수 캡처 의미 **C# 5**([28번](../28-lambdas-and-closure-capture/) (3) — **판 플래그에 안 묶였다**).
> **경계** — ★★★ **컬렉션을 무엇으로 고르나**는 [10번](../10-collection-choosing-list-dictionary-hashset-queue-stack/) 이 정본이다 — 여기는 **`foreach` 가 그 컬렉션을 어떻게 도나**만.\
> ★★ **열거자를 손으로 안 쓰고 만드는 법(`yield return`)** 은 [32번](../32-yield-return-iterators-and-deferred-execution/) · ★ **목록 패턴 `[1, .., 3]`** 은 [21번](../21-pattern-matching-type-property-relational-list/) — 그쪽은 `GetEnumerator` 가 아니라 **`Length`/`Count` + 인덱서**를 찾는다(21번 (2)) — **`foreach` 와 무관**하다.\
> ★★ **순회 중 수정의 교차 갈래 대비는 인용한다** — [Java 43번](../../../java/syntax/43-iterator-and-fail-fast/)(`ConcurrentModificationException` · **끝에서 두 번째를 지우면 안 터진다**) · [Rust 38번](../../../rust/syntax/38-vec-api-capacity-retain-and-drain/)(**`E0502` — 컴파일 에러**).
> ★★★ **본체 창은 ① IL 덤프다** — 「패턴으로 풀린다」는 **`call Bag+Walker::MoveNext`**(인터페이스 호출이 아니다)로만 보인다.
>
> ★★ **흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | 진단 **문구** · IL **오프셋 폭** | ★★★ **진단 코드**(`CS8400` · `CS1579`) · **옵코드**(`call …Walker::MoveNext` · `constrained.` + `callvirt IDisposable::Dispose` · `ldelem.i4`) · **`.try … finally` 가 있나** |
> | ★ **증분의 절댓값 일부**(규칙 24 — 짧게 데운 판에서 한 칸이 움직였다 · (5)) | ★★★ 할당 바이트의 **0 대 비(非)0** · **「네 판에서 갈린 줄 N / M」** · 예외 **타입과 메시지** · `_version` 이 **움직였나** |

## 이 판

```text
===== dotnet --version && dotnet --list-runtimes | grep NETCore (exit=0) =====
10.0.401
Microsoft.NETCore.App 10.0.12 [/home/jun/.local/opt/dotnet/shared/Microsoft.NETCore.App]
===== javac -version (exit=0) =====
javac 21.0.5
```

## 이 갈래가 쓰는 세 층

| 층 | 뜻 | 이 주제에서 근거로 쓰는 것 |
|---|---|---|
| **언어 명세(ECMA-334)** | ★★★ **C# 언어가 약속한 것** | ★★★ `foreach` 는 **`GetEnumerator`·`MoveNext`·`Current` 를 이름으로 찾는다**(인터페이스가 아니어도) · 열거자가 **`IDisposable` 이면 `finally` 에서 `Dispose`** · 배열은 **인덱스 고리로 풀어도 된다** · 확장 `GetEnumerator`(C# 9) |
| **BCL 계약** | 라이브러리 문서가 약속한 것 | ★★ `List<T>` 열거 중 수정은 **`InvalidOperationException`** · `List<T>.GetEnumerator()` 는 **구조체**를 돌려준다 |
| **런타임 · 컴파일러 구현** | ★★★ 그것을 **어떻게 적나** | ★★★ 구조체 열거자 → **`call` + `constrained. callvirt Dispose`**(박싱 없음) · 인터페이스로 받으면 → **박스 하나** · 배열 → **`ldelem` 고리** · `List<T>._version` · ★ `Dictionary.Remove` 가 열거를 안 깨는 것 |
| **이 판의 관찰** | .NET 10.0.12 · linux-x64 · javac 21.0.5 | 할당 바이트 · 예외 문구 |

★★★ **이 주제의 층 구분 —**\
**「`foreach` 는 패턴으로 풀린다(인터페이스를 안 봐도 된다)」는 명세**다. **「구조체 열거자라서 할당 0」은 BCL 이 구조체를 고른 결과 + 컴파일러가 박싱 없이 부르는 것**이다 — `List<int>` 를 **`IEnumerable<int>` 로 받는 순간** 사라진다.

## 한눈에 — 쉽게 말하면

**`foreach` 는 「책 읽어 주는 사람을 불러 달라」는 주문이다 — 누구를 부를지는 책(컬렉션)이 정하고, 그 사람의 이름표(인터페이스)는 보지 않는다.**

- **책(컬렉션 · `IEnumerable<T>`)** — 「읽어 줄 사람 한 명 보내 주세요」(`GetEnumerator()`) 하나만 할 줄 안다.
- **읽어 주는 사람(열거자 · `IEnumerator<T>`)** — 「다음 줄로(`MoveNext`)」 · 「지금 줄(`Current`)」 · 「끝났으니 책 덮기(`Dispose`)」.
- **이름표를 안 본다** — `GetEnumerator` 라는 **이름**만 있으면 된다. 확장 메서드여도 된다.
- **직원이 오나 파견이 오나** — `List<T>` 는 **구조체 직원**을 보낸다(할당 0). 그런데 주문서에 「`IEnumerable<T>` 아무나」라고 쓰면 **상자에 담아 보낸다**(박싱 — 할당).
- **읽는 도중 책을 고치면** — `List<T>` 는 책에 **개정 번호(`_version`)** 를 적어 두고 매 줄 대조한다. 다르면 **즉시 멈춘다.**

| 비유 | 실체 | 어디서 보나 |
|---|---|---|
| 이름표를 안 본다 | ★★★ 인터페이스 **0 개**인 `Bag` 이 `foreach` 된다 · IL **`call Bag+Walker::MoveNext`** | (1) |
| 확장이어도 된다 | ★★ `foreach (var i in 3)` → **`0 1 2`** · C# 8 **`CS8400`** | (2) |
| 구조체 직원 | ★★★ `List<int>` 를 `List<int>` 로 → **0 바이트** · `constrained. callvirt Dispose` | (4)(5) |
| 상자에 담아 | ★★★ 같은 `List<int>` 를 `IEnumerable<int>` 로 → **40000 바이트**(1000번) | (5) |
| 개정 번호 | ★★★ `Add`·`l[2]=9`·`Remove` → **`InvalidOperationException`** · `_version` **3 → 4 → 5** | (6) |
| 책 덮기 | ★★ 끝까지·`break`·예외 **셋 다** 마지막이 `Dispose` | (7) |

★★★ **이 주제의 본체 그림 — `foreach (var x in xs) 몸통` 이 풀리는 모양.**

```text
   foreach (var x in xs) 몸통          ── 컴파일러가 이름으로 찾는다 ──▶

     var e = xs.GetEnumerator();         ① GetEnumerator 가 xs 의 타입에 있나? 없으면 확장에서(C# 9)
     try {                               ② 그 반환 타입에 MoveNext() · Current 가 있나?
         while (e.MoveNext()) {          ★ 인터페이스(IEnumerable) 는 이 과정에 필요 없다
             var x = e.Current;
             몸통                         (C# 5 부터 x 는 반복마다 새 변수 — 28번)
         }
     } finally {                         ③ e 의 타입이 IDisposable 이면 여기서 Dispose
         e.Dispose();                        · 구조체면  constrained. callvirt Dispose  (박싱 없음)
     }                                       · 인터페이스면  if (e != null) callvirt Dispose
                                             · IDisposable 이 아니면  try/finally 자체가 없다 ((1))

   xs 가 배열이면 ── 위 모양이 아니라   for (i = 0; i < xs.Length; i++) { x = xs[i]; 몸통 }   (ldelem · 열거자 없음)
```

## 이 주제가 답하려는 질문

1. **`foreach` 는 무엇을 찾아 무엇으로 풀리나** — 패턴 · 확장 · 배열((1)(2)(4)).
2. **`IEnumerable`·`IEnumerator`·컬렉션은 각각 무슨 일을 하나**((3)).
3. **받는 타입이 할당을 바꾸나** — 구조체 열거자 대 박싱((4)(5)).
4. **순회 중 수정 · `Dispose`** — 언제 터지고 언제 불리나((6)(7)).

## 동작 방식

### (0) 이 주제가 쓰는 창

★★★ **본체 창은 ① IL 덤프다.**

| 창 | 무엇을 보여 주나 | 이 주제에서 |
|---|---|---|
| ★★★ **① IL 덤프** | ★★★ 패턴 호출 **`call …Walker::MoveNext`** · 구조체 열거자의 **`constrained. callvirt IDisposable::Dispose`** · 인터페이스판의 **`callvirt IEnumerator::MoveNext`** + 널 검사 · 배열의 **`ldelem.i4` 고리** · `.try … finally` 가 **있나 없나** | (1)(4) |
| ★★★ **④ 할당 바이트** | ★★★ 같은 `List<int>` 가 받는 타입에 따라 **0 대 40000** · 배열 **0 대 32000** — 2×2 판 격자 | (5) |
| ★★ **③ 리플렉션** | ★★ 인터페이스 **0 개** · 세 인터페이스의 **자기 멤버** · `List<int>.GetEnumerator()` 가 **구조체** · `_version` 필드 | (1)(3)(6) |
| ★★ **② 진단 격자** | ★ `CS8400`(C# 8 의 확장 `GetEnumerator`) · `CS1579`(`GetEnumerator` 없음) | (2) |
| **부적용인 창** | 없다 — 네 창을 다 썼다 | — |

### (1) ★★★ 본체 — 인터페이스 없이 `foreach` 된다

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

- ★★★ **`[1]`·`[2]` 인터페이스 수 `0` · `0` — 그런데 `[3]` `Sum` 이 `60`** — `Bag` 은 `IEnumerable` 을 **구현하지 않았다.** `foreach` 는 **`GetEnumerator` 라는 이름**만 찾았다.
- ★★★ **IL — `callvirt Bag::GetEnumerator` · `call Bag+Walker::get_Current` · `call Bag+Walker::MoveNext`** — **인터페이스 메서드 호출이 한 줄도 없다.** 찾은 **구조체의 메서드를 직접** 부른다(`ldloca.s 1` — 지역 변수의 주소로).
- ★★★ **`Walker.Dispose 불림` 이 안 찍혔고, IL 에 `.try … finally` 가 없다** — `Walker` 는 `public void Dispose()` 를 **가졌지만 `IDisposable` 이 아니다.** 패턴은 `GetEnumerator`·`MoveNext`·`Current` 까지이고 **`Dispose` 는 인터페이스로 찾는다**(`ref struct` 는 예외라고 알려져 있다 — **이 판에서 안 던졌다**).
- ★ `callvirt Bag::GetEnumerator` — 비가상 인스턴스 메서드도 `callvirt` 로 불러 **널 검사**를 얻는다([16번](../16-inheritance-virtual-override-abstract-sealed-new/)).

### (2) ★★ 확장 메서드 `GetEnumerator` · 없는 타입

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

- ★★★ **`foreach (var i in 3)` → `0 1 2`** — `int` 에는 `GetEnumerator` 가 없는데, **확장 메서드** `GetEnumerator(this int n)` 를 찾았다([30번](../30-extension-methods-and-extension-members/)).
- ★★ **`-langversion:8` → `CS8400 … 'extension GetEnumerator' … 9.0 or greater`** — C# 9 의 기능이다. 컴파일러가 **기능 이름을 직접** 말한다.
- ★★ **`Plain` → `CS1579`** — 「`'Plain'` 에 공개 인스턴스 **또는 확장** `GetEnumerator` 정의가 없다」 — 진단 문구가 **찾는 순서를 그대로** 말한다.

### (3) ★★ 세 역할 — 리플렉션으로

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

- ★★★ **`IEnumerable<T>` 의 자기 멤버는 `GetEnumerator` 하나** — 「열거자를 **하나 만들어 준다**」가 전부다. 몇 개인지·몇 번째인지 **모른다.**
- ★★★ **`IEnumerator<T>` 의 자기 멤버는 `Current`** · 상위 `IEnumerator`(`MoveNext`·`Reset`)와 **`IDisposable`** — **커서**다. `IDisposable` 을 상속하므로 **제네릭 열거자는 항상 `Dispose` 가 있다.**
- ★★ **`ICollection<T>` 가 비로소 `Count`·`Add`·`Remove`·`Contains`** — 「셀 수 있고 고칠 수 있는 것」. `IList<T>` 가 **인덱스**(`Item`·`IndexOf`·`Insert`·`RemoveAt`)를 더한다.
- ★★★ **`List<int>` 의 공개 `GetEnumerator` 는 `Enumerator (struct)`** — **구조체**다. **`IEnumerable<int>` 로 받아 부르면 실제 타입은 여전히 `Enumerator`(값 타입)** 인데, 그것을 **`IEnumerator<int>` 변수에 담았다** — 값 타입을 인터페이스 변수에 담는 것은 **박싱**이다([03번](../03-boxing-and-unboxing/)).

```text
   역할 셋 — 「무엇을 할 줄 아나」

   IEnumerable<T>      GetEnumerator()               ← 「읽어 줄 사람 보내 줘」 · 개수도 순서 번호도 모른다
        │ 만든다
        ▼
   IEnumerator<T>      MoveNext() · Current · Reset() · Dispose()   ← 커서 · 한 방향 · 한 번
                                                                       (Reset 은 32번 반복자에서 던진다)
   ICollection<T>      + Count · Add · Remove · Contains · …         ← 셀 수 있고 고칠 수 있다
   IList<T>            + this[i] · IndexOf · Insert · RemoveAt        ← 번호로 간다

   ★★ foreach 가 필요로 하는 것은 맨 위 한 줄(의 「모양」)뿐이다. Count 도 인덱스도 안 쓴다.
```

### (4) ★★★ IL — 구조체 열거자 · 인터페이스 열거자 · 배열

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

- ★★★ **`OverList`** — 지역 `[1]` 이 **`List+Enumerator<Int32>`**(중첩 구조체) · `ldloca.s 1` + **`call …Enumerator::MoveNext`/`get_Current`** · `finally` 에서 **`constrained. …List+Enumerator<Int32>` + `callvirt IDisposable::Dispose`** — **박싱 없이** 구조체의 `Dispose` 를 부른다.
- ★★★ **`OverSeq`** — 지역 `[1]` 이 **`IEnumerator<Int32>`** · **`callvirt IEnumerable<Int32>::GetEnumerator`** · **`callvirt IEnumerator::MoveNext`** · `finally` 에서 **`brfalse.s` 널 검사 후 `callvirt Dispose`** — 전부 **인터페이스 호출**이다.
- ★★★ **`OverArray`** — **`GetEnumerator` 가 없다.** `ldloc.2`(인덱스) · `ldelem.i4` · `ldlen` · `blt.s` — **`for` 고리로** 풀었다. `try`/`finally` 도 없다.
- ★ 덤프기는 이 배치에서 **중첩 제네릭 타입 이름**(`List+Enumerator<Int32>`)을 제대로 적게 고쳤다 — 앞 배치 판은 `List<Int32>` 로 **바깥 이름만** 적었다.

### (5) ★★★ 할당 바이트 — 받는 타입이 할당을 바꾼다 · 2×2 판 격자

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

- ★★★ **네 판에서 갈린 줄 0 / 4** — **`[1]` 0 · `[2]` 40000 · `[3]` 0 · `[4]` 32000**.
- ★★★ **`[1]` 대 `[2]` — 같은 `List<int>` 객체**다. `List<int>` 로 받으면 **구조체 열거자를 스택에** 두고, `IEnumerable<int>` 로 받으면 **`GetEnumerator()` 가 인터페이스 변수로 돌아와 박스**가 된다((3)(4)). **`foreach` 한 번마다 박스 하나**다.
- ★★ **`[3]` 대 `[4]`** — 배열도 `int[]` 로 받으면 **열거자 자체가 없다**((4) `ldelem` 고리). `IEnumerable<int>` 로 받으면 배열의 **열거자 객체**가 생긴다.
- ★★ **제네릭 코드에서의 뜻** — 매개변수를 `IEnumerable<T>` 로 받는 메서드는 **무엇을 넘기든 열거자 할당**을 한다. [24번](../24-generics-and-type-parameters/) 의 「제네릭은 값 타입마다 코드를 따로 만든다」는 **타입 인자가 값 타입일 때** 이야기고, 여기의 박싱은 **인터페이스 변수**에서 생긴다 — 다른 축이다.
- ★★★ **흔들린 칸이 있었다** — 첫 캡처는 **짧게 데운 판**(200번)이었고 `-optimize` + 티어링 기본 칸에서 **`[4]` 가 한 번 `32`** 로 나왔다(나머지 세 판 `32000`). 그 뒤 같은 dll 을 6번 다시 돌려 **6번 다 `32000`** 이었다 — **데우는 도중 티어가 바뀐** 잡음으로 보고, 캡처를 **길게 데우는 판**(200 + 쉼 + 300 + 쉼 + 300)으로 바꿨다. 위 블록이 그 판이다(규칙 24).
- ★★★ **「구조체 열거자가 빠르다」는 이 문서가 잰 것이 아니다** — 잰 것은 **할당 바이트**뿐이다. 시간은 안 쟀다.

### (6) ★★★ 순회 중에 고치면 — `_version` 대조 · Java 와 한 쌍

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

- ★★★ **`[1]`\~`[3]` `List` 는 `Add`·`l[2] = 9`·`Remove` 전부 `InvalidOperationException: Collection was modified; enumeration operation may not execute.`** — **값을 덮어쓰는 `l[2] = 9` 도** 수정이다.
- ★★★ **`[8]` `_version` — 처음 `3` · `Add` 뒤 `4` · `l[0]=7` 뒤 `5` · 읽기 뒤 `5`** — 쓰기마다 오르는 **개정 번호**다. 열거자는 만들 때의 번호를 들고 있다가 `MoveNext` 마다 대조한다(BCL 구현 — **필드 이름은 계약이 아니다**).
- ★★★ **`[3]` — 마지막 원소 직전(`x==2`)에서 마지막 원소를 지워도 C# 은 던진다. Java 는 `끝까지 돎`** — [Java 43번](../../../java/syntax/43-iterator-and-fail-fast/)이 먼저 실측한 **「끝에서 두 번째를 지우면 안 터지고 마지막 원소를 조용히 건너뛴다」** 가 여기서도 재현됐다. Java 의 `hasNext()` 는 **`cursor != size` 만 보고 검사 없이 끝나고**(Java 43번), C# `List<T>` 의 `MoveNext` 는 **끝에 닿을 때도 번호를 대조**한다.
- ★★ **`[4]`·`[5]` `Dictionary` 는 `Remove`·기존 키 덮어쓰기에서 `끝까지 돎` · `[6]` 새 키 추가만 던진다** — `Dictionary` 는 **모든 쓰기에서 번호를 올리지 않는다**(이 판의 관찰 — 계약으로 읽지 마라).
- ★★ **`[7]` 배열은 `끝까지 돎`** — 배열 `foreach` 는 **인덱스 고리**라 대조할 번호가 없다((4)).

```text
   순회 중 수정 — 세 언어가 막는 시점

                   막는 때        같은 모양 [3] (끝에서 두 번째에서 마지막을 지움)
   C#   List<T>    실행 · 매 MoveNext 대조          → InvalidOperationException
   Java ArrayList  실행 · next() 에서 대조          → 안 던짐 · 마지막 원소를 건너뜀 (Java 43편)
   Rust Vec        컴파일 · 빌림 검사 E0502         → 빌드가 안 된다 (Rust 38편)

   ★★★ C# 과 Java 는 「실행 시점의 최선 노력」 이고 Rust 는 「컴파일 시점의 금지」 다.
       C# 과 Java 가 갈린 칸은 「끝에 닿을 때도 대조하나」 한 곳이다.
```

### (7) ★★ `Dispose` 는 언제 불리나

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

- ★★★ **`[1]` 끝까지 — `MoveNext → False` 다음 `Dispose`** · **`[2]` `break` — `몸통 2` 다음 바로 `Dispose`** · **`[3]` 몸통이 던짐 — `Dispose` 다음 `바깥 catch`** — (4)의 **`finally`** 그대로다. 셋 다 **`Dispose` 가 한 번**.
- ★★ **`Current` 는 반복마다 한 번** — 몸통이 `x` 를 쓰기 **전에** 읽힌다(`Current → 1` 다음 `몸통 1`).

## 문법 — 형태와 규칙

### 형태

```text
===== 소스: cs31b-form.cs =====
using System;
using System.Collections.Generic;

var words = new List<string> { "b", "a", "c" };
foreach (var w in words) Console.Write(w);
Console.Write(" · ");
foreach (var (k, v) in new Dictionary<string, int> { ["x"] = 1 }) Console.Write($"{k}={v}");
Console.Write(" · ");
using (IEnumerator<string> e = words.GetEnumerator())
    while (e.MoveNext()) Console.Write(e.Current);
Console.WriteLine();
===== csc -out:ex.dll cs31b-form.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
bac · x=1 · bac
```

- ★★★ **`foreach (var w in words)`** — 가장 흔한 꼴. `List<T>` 면 구조체 열거자((4)(5)).
- ★★ **`foreach (var (k, v) in dict)`** — `KeyValuePair` 의 **해체**([23번](../23-tuples-and-deconstruction/)).
- ★★ **`using (IEnumerator<string> e = …) while (e.MoveNext()) …`** — `foreach` 를 **손으로 푼** 꼴. (본체 그림의 `try`/`finally` 가 `using` 이다.)

### 금지 사례 — 진단이 나는 꼴

| 쓴 꼴 | 진단 코드 | 어디서 |
|---|---|---|
| `GetEnumerator` 가 없는 타입을 `foreach` | `CS1579` | (2) |
| C# 8 이하에서 확장 `GetEnumerator` 로 `foreach` | `CS8400` | (2) |
| ★★★ `List<T>` 를 도는 중에 `Add`·`Remove`·`l[i] = …` | ★★★ **진단 없음** — 실행 시 `InvalidOperationException` | (6) |
| ★★ 열거자에 `Dispose()` 만 있고 `IDisposable` 이 아님 | ★★ **진단 없음** — `Dispose` 가 안 불린다 | (1) |

## 어디서 틀리나

1. ★★★ **「`foreach` 하려면 `IEnumerable` 을 구현해야 한다」** — **이름만** 있으면 된다. 확장 메서드여도 된다((1)(2)).
2. ★★★ **「`foreach` 는 인터페이스를 거친다」** — 찾은 타입을 **그대로** 부른다. `List<T>` 면 **구조체 `call`**((4)).
3. ★★★ **「`List<T>` 의 `foreach` 는 할당이 없다」** — **`List<T>` 로 받을 때만**이다. **`IEnumerable<T>` 로 받으면 매번 박스**((5) 40000).
4. ★★★ **「값만 바꾸는 `l[i] = …` 는 괜찮다」** — `List<T>` 에서는 **수정**이다((6) `[2]`).
5. ★★★ **「C# 도 Java 처럼 끝에서 두 번째를 지우면 안 터진다」** — C# 은 **터진다**((6) `[3]`).
6. ★★ **「`Dictionary` 에서 순회 중 `Remove` 는 항상 던진다」** — 이 판은 **안 던졌다**. 새 키 추가만 던졌다((6)).
7. ★★ **「열거자에 `Dispose` 메서드만 있으면 `foreach` 가 부른다」** — **`IDisposable` 이어야** 부른다((1)).
8. ★ **「배열 `foreach` 도 열거자를 만든다」** — **인덱스 고리**다((4)).

## 구현 세부사항 대 언어 보장

| 무엇 | 층 | 근거 |
|---|---|---|
| **`foreach` 는 `GetEnumerator`/`MoveNext`/`Current` 를 이름으로 찾는다** | ★★★ **언어(334 §13.9.5)** | (1) |
| **확장 `GetEnumerator`** | ★★★ **언어(C# 9)** | (2) |
| **열거자가 `IDisposable` 이면 `finally` 에서 `Dispose`** | ★★★ **언어** | (4)(7) |
| **배열은 인덱스 고리로** | ★★ **언어가 허용 · Roslyn 이 그렇게 함** | (4) |
| **`List<T>.GetEnumerator()` 가 구조체** | ★★ **BCL 설계**(공개 API 모양) | (3) |
| **구조체 열거자를 `constrained.` 로 박싱 없이 `Dispose`** | ★★ **Roslyn 구현** | (4) |
| **`List<T>` 열거 중 수정이 `InvalidOperationException`** | ★★ **BCL 계약** | (6) |
| **`_version` 필드 · `Dictionary.Remove` 가 안 깨는 것** | ★ **BCL 구현 · 이 판의 관찰** | (6) |
| **할당 바이트 값** | ★ **이 판의 관찰** | (5) |

## 언제 쓰고 언제 안 쓰나

- ★★★ **뜨거운 경로에서 열거자 할당을 없애고 싶으면 매개변수를 구체 타입(`List<T>`·배열·`Span<T>`)으로 받아라** — `IEnumerable<T>` 로 받으면 **호출마다 할당**이다((5)). 할당이 문제인지는 **재 보고** 판단해라 — 이 문서는 시간을 안 쟀다.
- ★★★ **순회 중에 지울 것은 따로 모아 두었다가 순회 뒤에 지워라** — 또는 `List<T>.RemoveAll(조건)`. 「이 판에서 안 터졌다」(`Dictionary`)에 기대지 마라((6)).
- ★★ **열거자를 직접 만들면 `IDisposable` 을 붙여라** — 안 붙이면 `foreach` 가 정리를 안 부른다((1)).
- ★★ **열거자를 손으로 쓰지 마라** — 대부분 `yield return` 이 낫다([32번](../32-yield-return-iterators-and-deferred-execution/)).

## 핵심 문장

1. ★★★ **`foreach` 는 인터페이스가 아니라 `GetEnumerator`·`MoveNext`·`Current` 라는 이름을 찾는다** — 인터페이스 0 개인 `Bag` 이 되고, IL 은 **`call …Walker::MoveNext`**((1)).
2. ★★★ **찾은 타입 그대로 부른다** — `List<int>` 로 받으면 구조체(할당 0), **`IEnumerable<int>` 로 받으면 박스(1000번 40000)** — 네 판 같음((4)(5)).
3. ★★★ **`List<T>` 는 쓰기마다 `_version` 을 올리고 `MoveNext` 마다 대조한다** — 끝에서 두 번째에서도 던진다(**Java 는 안 던진다 · Rust 는 컴파일 에러**)((6)).
4. ★★ **`Dispose` 는 `finally` 에 있다** — 끝까지·`break`·예외 모두 한 번. 단 **`IDisposable` 이어야**((1)(7)).
5. ★★ **배열은 열거자 없이 인덱스 고리로 풀린다**((4)).

## 관련 자료

- [10번 — 컬렉션 고르기](../10-collection-choosing-list-dictionary-hashset-queue-stack/) — **경계**: 컬렉션 선택 기준은 거기. 여기는 **`foreach` 가 그것을 도는 방법.**
- [03번 — 박싱](../03-boxing-and-unboxing/) — 값 타입을 인터페이스 변수에 담으면 박스((3)(5)).
- [24번 — 제네릭](../24-generics-and-type-parameters/) — 값 타입 인자별 코드 · `__Canon`. (5)의 박싱과는 **다른 축**.
- [28번 — 람다와 캡처](../28-lambdas-and-closure-capture/) (3) — `foreach` 반복 변수가 반복마다 새 변수(C# 5).
- [30번 — 확장 메서드](../30-extension-methods-and-extension-members/) — (2)의 확장 `GetEnumerator`.
- [32번 — `yield return`](../32-yield-return-iterators-and-deferred-execution/) — 열거자를 컴파일러가 만든다.
- [21번 — 패턴 매칭](../21-pattern-matching-type-property-relational-list/) — **경계**: 목록 패턴은 `Length`/`Count` + 인덱서를 찾는다 — `foreach` 의 패턴과 **다른 이름**이다.
- Java 갈래 목록([`java/syntax/README.md`](../../../java/syntax/README.md))의 **43번**([`43-iterator-and-fail-fast/`](../../../java/syntax/43-iterator-and-fail-fast/)) — fail-fast 와 그 구멍.
- Rust 갈래 목록([`rust/syntax/README.md`](../../../rust/syntax/README.md))의 **38번**([`38-vec-api-capacity-retain-and-drain/`](../../../rust/syntax/38-vec-api-capacity-retain-and-drain/)) — 순회 중 수정이 `E0502`.

## 용어 풀이

- **열거 가능(enumerable)** — `GetEnumerator()` 로 열거자를 만들어 주는 것(`IEnumerable<T>`).
- **열거자(enumerator)** — 한 방향으로 한 칸씩 가는 커서(`IEnumerator<T>` — `MoveNext`·`Current`·`Dispose`).
- **패턴 기반(pattern-based)** — 인터페이스가 아니라 **정해진 이름의 멤버**가 있는지로 문법을 허락하는 방식.
- **구조체 열거자** — `List<T>.Enumerator` 처럼 값 타입인 열거자. 구체 타입으로 받으면 할당이 없다.
- **`constrained.` 접두** — 값 타입의 인터페이스 메서드를 **박싱 없이** 부르게 하는 IL 접두.
- **fail-fast** — 순회 중 수정을 **최선 노력으로** 감지해 즉시 던지는 것.
- **`_version`** — `List<T>` 가 쓰기마다 올리는 숨은 개정 번호(BCL 구현).

## 더 들어가면

- ★ **`ref struct` 열거자의 패턴 `Dispose`**(C# 8) — `IDisposable` 없이도 부른다고 알려져 있다. **이 판에서 안 던졌다.**
- ★ **`Span<T>` 의 `foreach` · `foreach (ref var x in span)`** — Learn 예제가 있다. **안 던졌다.**
- ★ **`await foreach`(C# 8)** — `GetAsyncEnumerator` 패턴. 비동기 묶음에서.
- ★ **`IEnumerable<T>` 로 받은 `foreach` 를 JIT 이 탈가상화해 박싱을 없애는 판** — (5)의 흔들린 칸이 그 흔적일 수 있다. **확인하지 않았다.**
