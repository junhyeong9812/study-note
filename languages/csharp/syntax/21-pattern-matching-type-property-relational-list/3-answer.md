# csharp/syntax/21 — 패턴 매칭 — 타입·속성·관계·목록 패턴 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·진단·IL·할당 바이트는 **.NET SDK 10.0.401** · 런타임 **10.0.12** · 타겟 **`net10.0`** ·
> **linux-x64** 에서 실제로 돌려 얻은 것이다(2026-09-26). 대비는 **javac 21.0.5** 다.\
> 진단은 **`-preferreduilang:en-US`** 로 영어로 고정했다.\
> ★ 블록은 캡처 스크립트가 파일로 받아 조립기가 끼워 넣은 것이다 — 손으로 옮긴 줄은 없다.\
> ★ 진단을 싣는 블록은 전부 **그 진단을 낸 소스를 같은 블록 안에** 다시 싣는다(`===== 소스: … =====`).
> **읽는 법** — **진단 문구·IL 오프셋 폭**은 흔들리는 칸이다. ★★ **getter 호출 횟수는 이 판 Roslyn 의 것**이다 — 명세가 아니다.\
> 근거로 쓰는 것은 **옵코드와 부른 멤버 · 진단 코드와 `(행,열)` · 네 판에서 갈린 줄 수** 다.
> ★★★ **이 문서는 시간을 재지 않았다.** 「패턴 매칭이 빠르다」는 문장이 **한 줄도 없다.**

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ 캐스트는 **`isinst` 한 번**, 범위는 **비교 둘**

**출력**

```text
===== 소스: cs21b-il.cs =====
using System;
public static class Probe {
    public static int Decl(object o)   => o is string s ? s.Length : -1;    // 선언 패턴
    public static bool Type(object o)  => o is string;                        // 타입 패턴
    public static bool Range(int x)    => x is >= 0 and < 10;                 // 관계 + and
    public static bool Outside(int x)  => x is < 0 or >= 10;                  // 관계 + or
    public static bool Letter(char c)  => c is not (>= 'a' and <= 'z');      // not + 괄호
}
class Program {
    static void Main() {
        Console.WriteLine($"[1] Decl(\"abc\")={Probe.Decl("abc")} Decl(42)={Probe.Decl(42)}");
        Console.WriteLine($"[2] Range(9)={Probe.Range(9)} Range(10)={Probe.Range(10)} Outside(-1)={Probe.Outside(-1)}");
        Console.WriteLine($"[3] Letter('q')={Probe.Letter('q')} Letter('Q')={Probe.Letter('Q')}");
        foreach (var n in new[] { "Decl", "Type", "Range", "Outside" }) Il.Dump(typeof(Probe), n);
    }
}
===== csc -r:il.dll -out:ex.dll cs21b-il.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
[1] Decl("abc")=3 Decl(42)=-1
[2] Range(9)=True Range(10)=False Outside(-1)=True
[3] Letter('q')=False Letter('Q')=True
--- Probe.Decl ---
  .locals [0] System.String
  IL_0000: ldarg.0
  IL_0001: isinst System.String
  IL_0006: stloc.0
  IL_0007: ldloc.0
  IL_0008: brtrue.s IL_000d
  IL_000a: ldc.i4.m1
  IL_000b: br.s IL_0013
  IL_000d: ldloc.0
  IL_000e: callvirt System.String::get_Length
  IL_0013: ret
--- Probe.Type ---
  IL_0000: ldarg.0
  IL_0001: isinst System.String
  IL_0006: ldnull
  IL_0007: cgt.un
  IL_0009: ret
--- Probe.Range ---
  IL_0000: ldarg.0
  IL_0001: ldc.i4.0
  IL_0002: blt.s IL_000b
  IL_0004: ldarg.0
  IL_0005: ldc.i4.s 10
  IL_0007: clt
  IL_0009: br.s IL_000c
  IL_000b: ldc.i4.0
  IL_000c: ret
--- Probe.Outside ---
  .locals [0] System.Boolean
  IL_0000: ldarg.0
  IL_0001: ldc.i4.0
  IL_0002: blt.s IL_000b
  IL_0004: ldarg.0
  IL_0005: ldc.i4.s 10
  IL_0007: bge.s IL_000b
  IL_0009: br.s IL_000f
  IL_000b: ldc.i4.1
  IL_000c: stloc.0
  IL_000d: br.s IL_0011
  IL_000f: ldc.i4.0
  IL_0010: stloc.0
  IL_0011: ldloc.0
  IL_0012: ret
```

**왜 그런가**

- ★★★ **`[1]` `3` · `-1`** · **`[2]` `True` · `False` · `True`** · **`[3]` `False` · `True`**.
- ★★★ **`Decl` 의 캐스트는 `isinst System.String` 하나** — 결과를 **`stloc.0` 으로 바로 `s` 에** 담고, `brtrue.s` 로 null 인지 본다. 두 번째 캐스트가 없다.
- ★★ **`Range` 는 비교 둘** — `ldc.i4.0`·`blt.s`(0 미만이면 거짓) 뒤 `ldc.i4.s 10`·`clt`.
- ★ **`Letter('Q')` 가 `True`** — `not (>= 'a' and <= 'z')` 라 소문자 범위 **밖**이면 참. 괄호를 빼면 `not` 이 먼저 묶여 `(not >= 'a') and <= 'z'` 가 된다(Learn).

### 2. ★★★ **`[3]` 이 `False`** — `== null`·`!= null` 만 연산자를 부르고, 패턴 셋은 안 부른다

**출력**

```text
===== 소스: cs21b-null.cs =====
using System;
class Token {
    public static int Calls;
    public static bool operator ==(Token? a, Token? b) { Calls++; Console.WriteLine("    op_Equality 불림"); return false; }
    public static bool operator !=(Token? a, Token? b) { Calls++; Console.WriteLine("    op_Inequality 불림"); return true; }
    public override bool Equals(object? o) => ReferenceEquals(this, o);
    public override int GetHashCode() => 0;
}
static class Probe {
    public static bool IsNull(Token? t)    => t is null;
    public static bool IsNotNull(Token? t) => t is not null;
    public static bool EqNull(Token? t)    => t == null;
    public static bool NeNull(Token? t)    => t != null;
    public static bool Empty(Token? t)     => t is { };
}
class Program {
    static void Main() {
        Token? none = null;
        Console.WriteLine($"[1] none is null     : {Probe.IsNull(none)}");
        Console.WriteLine($"[2] none is not null : {Probe.IsNotNull(none)}");
        Console.WriteLine($"[3] none == null     : {Probe.EqNull(none)}");
        Console.WriteLine($"[4] none != null     : {Probe.NeNull(none)}");
        Console.WriteLine($"[5] none is {{ }}      : {Probe.Empty(none)}");
        Console.WriteLine($"    연산자 호출 횟수 = {Token.Calls}");
        foreach (var n in new[] { "IsNull", "IsNotNull", "EqNull", "NeNull", "Empty" }) Il.Dump(typeof(Probe), n);
    }
}
===== csc -nullable:enable -r:il.dll -out:ex.dll cs21b-null.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
[1] none is null     : True
[2] none is not null : False
    op_Equality 불림
[3] none == null     : False
    op_Inequality 불림
[4] none != null     : True
[5] none is { }      : False
    연산자 호출 횟수 = 2
--- Probe.IsNull ---
  IL_0000: ldarg.0
  IL_0001: ldnull
  IL_0002: ceq
  IL_0004: ret
--- Probe.IsNotNull ---
  IL_0000: ldarg.0
  IL_0001: ldnull
  IL_0002: cgt.un
  IL_0004: ret
--- Probe.EqNull ---
  IL_0000: ldarg.0
  IL_0001: ldnull
  IL_0002: call Token::op_Equality
  IL_0007: ret
--- Probe.NeNull ---
  IL_0000: ldarg.0
  IL_0001: ldnull
  IL_0002: call Token::op_Inequality
  IL_0007: ret
--- Probe.Empty ---
  IL_0000: ldarg.0
  IL_0001: ldnull
  IL_0002: cgt.un
  IL_0004: ret
```

**왜 그런가**

- ★★★ **`[1]` `True` · `[2]` `False` · `[3]` `False` · `[4]` `True` · `[5]` `False`**, 연산자 호출 **2회** — `op_Equality 불림` 은 `[3]` 앞, `op_Inequality 불림` 은 `[4]` 앞이다.
- ★★★ **null 을 null 과 `==` 했는데 `False`** — `Token.op_Equality` 가 불려 `false` 를 돌려줬다. **`is null` 은 그것을 안 부른다**(Learn 이 「컴파일러가 보장」한다고 적었다).
- ★★ **`IsNotNull` 과 `Empty` 의 IL 은 같다** — 둘 다 `ldnull` · **`cgt.un`**. `IsNull` 은 `ceq`. `EqNull`·`NeNull` 만 **`call Token::op_…`**.

### 3. ★★ **`&&` 만 2회**, 나머지는 전부 **1회**

**출력**

```text
===== 소스: cs21b-getter.cs =====
using System;
class Word {
    public static int Reads;
    readonly string s;
    public Word(string s) => this.s = s;
    public int Len { get { Reads++; return s.Length; } }
}
class Pt {
    public static int Calls;
    public int X, Y;
    public Pt(int x, int y) { X = x; Y = y; }
    public void Deconstruct(out int x, out int y) { Calls++; x = X; y = Y; }
}
class Program {
    static void Main() {
        var w = new Word("pattern");
        Word.Reads = 0; bool a = w.Len > 3 && w.Len < 9;
        Console.WriteLine($"[1] &&                   : {a}  get_Len {Word.Reads}회");
        Word.Reads = 0; bool b = w is { Len: > 3 } and { Len: < 9 };
        Console.WriteLine($"[2] and                  : {b}  get_Len {Word.Reads}회");
        Word.Reads = 0; bool c = w is { Len: > 3 and < 9 };
        Console.WriteLine($"[3] {{ Len: > 3 and < 9 }} : {c}  get_Len {Word.Reads}회");
        Word.Reads = 0;
        int d = w switch { { Len: > 10 } => 3, { Len: > 5 } => 2, { Len: > 0 } => 1, _ => 0 };
        Console.WriteLine($"[4] switch 팔 넷          : {d}  get_Len {Word.Reads}회");
        var p = new Pt(1, 5);
        int e = p switch { (0, 0) => 0, (1, 1) => 1, (1, var y) => y, _ => -1 };
        Console.WriteLine($"[5] 위치 패턴 팔 넷        : {e}  Deconstruct {Pt.Calls}회");
    }
}
===== csc -out:ex.dll cs21b-getter.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
[1] &&                   : True  get_Len 2회
[2] and                  : True  get_Len 1회
[3] { Len: > 3 and < 9 } : True  get_Len 1회
[4] switch 팔 넷          : 2  get_Len 1회
[5] 위치 패턴 팔 넷        : 5  Deconstruct 1회
===== csc -optimize -out:exo.dll cs21b-getter.cs && dotnet exo.dll (cc exit=0 · run exit=0) =====
[1] &&                   : True  get_Len 2회
[2] and                  : True  get_Len 1회
[3] { Len: > 3 and < 9 } : True  get_Len 1회
[4] switch 팔 넷          : 2  get_Len 1회
[5] 위치 패턴 팔 넷        : 5  Deconstruct 1회
```

**왜 그런가**

- ★★★ **`[1]` 2 · `[2]` 1 · `[3]` 1 · `[4]` 1 · `[5]` `Deconstruct` 1.**
- ★★★ **팔이 넷인 `switch` 식도 `get_Len` 1회** — Roslyn 이 팔 전체를 **한 번 읽은 값을 나눠 쓰는 결정 DAG** 로 합친다.
- ★★ **`-optimize` 에서도 같다** — JIT 최적화가 아니라 **컴파일러가 정한 횟수**로 읽힌다(이 탐침의 IL 은 안 찍었다 — 해석이다).
- ★ 이 「1회」가 **약속이 아니라는 것**은 9번.

### 4. ★★★ 길이는 **`ldlen` / `get_Count` / `get_Length`**, 꺼내기는 **`길이 - 1` + 인덱서** — `Rest` 는 **`GetSubArray`**

**출력**

```text
===== 소스: cs21b-list.cs =====
using System;
using System.Collections.Generic;
public class Bag {                                   // Length 와 this[int] 만 있다 — 인터페이스 없음
    readonly int[] items;
    public Bag(params int[] xs) => items = xs;
    public int Length => items.Length;
    public int this[int i] => items[i];
}
public static class Probe {
    public static int Arr(int[] a)       => a is [1, .., var last] ? last : -1;
    public static int Lst(List<int> a)   => a is [1, .., var last] ? last : -1;
    public static int Own(Bag b)         => b is [1, .., var last] ? last : -1;
    public static int[] Rest(int[] a)    => a is [_, .. var rest] ? rest : a;
}
class Program {
    static void Main() {
        Console.WriteLine($"[1] {Probe.Arr(new[] { 1, 2, 3 })} {Probe.Arr(new[] { 1 })} {Probe.Arr(new[] { 2, 3 })}");
        Console.WriteLine($"[2] {Probe.Lst(new List<int> { 1, 5 })} {Probe.Own(new Bag(1, 7))}");
        Console.WriteLine($"[3] [{string.Join(",", Probe.Rest(new[] { 9, 8, 7 }))}]");
        foreach (var n in new[] { "Arr", "Lst", "Own", "Rest" }) Il.Dump(typeof(Probe), n);
    }
}
===== csc -r:il.dll -out:ex.dll cs21b-list.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
[1] 3 -1 -1
[2] 5 7
[3] [8,7]
--- Probe.Arr ---
  .locals [0] System.Int32
  .locals [1] System.Int32
  IL_0000: ldarg.0
  IL_0001: brfalse.s IL_0019
  IL_0003: ldarg.0
  IL_0004: ldlen
  IL_0005: conv.i4
  IL_0006: stloc.1
  IL_0007: ldloc.1
  IL_0008: ldc.i4.2
  IL_0009: blt.s IL_0019
  IL_000b: ldarg.0
  IL_000c: ldc.i4.0
  IL_000d: ldelem.i4
  IL_000e: ldc.i4.1
  IL_000f: bne.un.s IL_0019
  IL_0011: ldarg.0
  IL_0012: ldloc.1
  IL_0013: ldc.i4.1
  IL_0014: sub
  IL_0015: ldelem.i4
  IL_0016: stloc.0
  IL_0017: br.s IL_001c
  IL_0019: ldc.i4.m1
  IL_001a: br.s IL_001d
  IL_001c: ldloc.0
  IL_001d: ret
--- Probe.Lst ---
  .locals [0] System.Int32
  .locals [1] System.Int32
  IL_0000: ldarg.0
  IL_0001: brfalse.s IL_0024
  IL_0003: ldarg.0
  IL_0004: callvirt System.Collections.Generic.List<System.Int32>::get_Count
  IL_0009: stloc.1
  IL_000a: ldloc.1
  IL_000b: ldc.i4.2
  IL_000c: blt.s IL_0024
  IL_000e: ldarg.0
  IL_000f: ldc.i4.0
  IL_0010: callvirt System.Collections.Generic.List<System.Int32>::get_Item
  IL_0015: ldc.i4.1
  IL_0016: bne.un.s IL_0024
  IL_0018: ldarg.0
  IL_0019: ldloc.1
  IL_001a: ldc.i4.1
  IL_001b: sub
  IL_001c: callvirt System.Collections.Generic.List<System.Int32>::get_Item
  IL_0021: stloc.0
  IL_0022: br.s IL_0027
  IL_0024: ldc.i4.m1
  IL_0025: br.s IL_0028
  IL_0027: ldloc.0
  IL_0028: ret
--- Probe.Own ---
  .locals [0] System.Int32
  .locals [1] System.Int32
  IL_0000: ldarg.0
  IL_0001: brfalse.s IL_0024
  IL_0003: ldarg.0
  IL_0004: callvirt Bag::get_Length
  IL_0009: stloc.1
  IL_000a: ldloc.1
  IL_000b: ldc.i4.2
  IL_000c: blt.s IL_0024
  IL_000e: ldarg.0
  IL_000f: ldc.i4.0
  IL_0010: callvirt Bag::get_Item
  IL_0015: ldc.i4.1
  IL_0016: bne.un.s IL_0024
  IL_0018: ldarg.0
  IL_0019: ldloc.1
  IL_001a: ldc.i4.1
  IL_001b: sub
  IL_001c: callvirt Bag::get_Item
  IL_0021: stloc.0
  IL_0022: br.s IL_0027
  IL_0024: ldc.i4.m1
  IL_0025: br.s IL_0028
  IL_0027: ldloc.0
  IL_0028: ret
--- Probe.Rest ---
  .locals [0] System.Int32[]
  IL_0000: ldarg.0
  IL_0001: brfalse.s IL_0025
  IL_0003: ldarg.0
  IL_0004: ldlen
  IL_0005: conv.i4
  IL_0006: ldc.i4.1
  IL_0007: blt.s IL_0025
  IL_0009: ldarg.0
  IL_000a: ldc.i4.1
  IL_000b: ldc.i4.0
  IL_000c: newobj System.Index::.ctor
  IL_0011: ldc.i4.0
  IL_0012: ldc.i4.1
  IL_0013: newobj System.Index::.ctor
  IL_0018: newobj System.Range::.ctor
  IL_001d: call System.Runtime.CompilerServices.RuntimeHelpers::GetSubArray
  IL_0022: stloc.0
  IL_0023: br.s IL_0028
  IL_0025: ldarg.0
  IL_0026: br.s IL_0029
  IL_0028: ldloc.0
  IL_0029: ret
```

**왜 그런가**

- ★★★ **`[1]` `3 -1 -1`** — `{1}` 은 원소가 둘 미만이라, `{2,3}` 은 첫 원소가 1 이 아니라 실패. **`[2]` `5 7` · `[3]` `[8,7]`.**
- ★★★ **배열 `ldlen`·`conv.i4` · `List<int>` `callvirt get_Count` · `Bag` `callvirt get_Length`.** `Bag` 은 **인터페이스 없이** `Length` + `this[int]` 만으로 컴파일됐다 — [14번](../14-indexers/) (5)의 **패턴 기반 인덱싱**과 같은 규칙이다.
- ★★ **마지막 원소는 `ldloc.1 · ldc.i4.1 · sub` 로 직접 계산**해 `ldelem.i4`/`get_Item` 으로 꺼낸다. **`System.Index` 는 안 나타난다.**
- ★★ **`Rest` 는 `newobj System.Index` 둘 · `newobj System.Range` · `call RuntimeHelpers::GetSubArray`** — 새 배열을 만든다(5번).

### 5. ★★ **`[2]` 56000 · `[4]` 40000**, 나머지 0 — 갈린 줄 **0 / 5**

**출력**

```text
===== 소스: cs21b-alloc.cs =====
using System;
class Program {
    static long M(Action a) {
        for (int i = 0; i < 200; i++) a();                // 데운다
        var b = GC.GetAllocatedBytesForCurrentThread();
        a();
        return GC.GetAllocatedBytesForCurrentThread() - b;
    }
    static void Main() {
        int[] arr = { 1, 2, 3, 4, 5, 6, 7, 8 };
        string str = "abcdefgh";
        object boxed = 42;
        long sink = 0;
        Console.WriteLine($"[1] arr is [1, .., var last]     1000번 : {M(() => { for (int i = 0; i < 1000; i++) if (arr is [1, .., var last]) sink += last; })} 바이트");
        Console.WriteLine($"[2] arr is [_, .. var rest]      1000번 : {M(() => { for (int i = 0; i < 1000; i++) if (arr is [_, .. var rest]) sink += rest.Length; })} 바이트");
        Console.WriteLine($"[3] span is [_, .. var rest]     1000번 : {M(() => { for (int i = 0; i < 1000; i++) { ReadOnlySpan<int> sp = arr; if (sp is [_, .. var rest]) sink += rest.Length; } })} 바이트");
        Console.WriteLine($"[4] str is [_, .. var rest]      1000번 : {M(() => { for (int i = 0; i < 1000; i++) if (str is [_, .. var rest]) sink += rest.Length; })} 바이트");
        Console.WriteLine($"[5] boxed is int n               1000번 : {M(() => { for (int i = 0; i < 1000; i++) if (boxed is int n) sink += n; })} 바이트");
        GC.KeepAlive(sink);
    }
}
===== csc -out:ex.dll cs21b-alloc.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
[1] arr is [1, .., var last]     1000번 : 0 바이트
[2] arr is [_, .. var rest]      1000번 : 56000 바이트
[3] span is [_, .. var rest]     1000번 : 0 바이트
[4] str is [_, .. var rest]      1000번 : 40000 바이트
[5] boxed is int n               1000번 : 0 바이트
===== csc -out:ex.dll cs21b-alloc.cs && DOTNET_TieredCompilation=0 dotnet ex.dll (cc exit=0 · run exit=0) =====
[1] arr is [1, .., var last]     1000번 : 0 바이트
[2] arr is [_, .. var rest]      1000번 : 56000 바이트
[3] span is [_, .. var rest]     1000번 : 0 바이트
[4] str is [_, .. var rest]      1000번 : 40000 바이트
[5] boxed is int n               1000번 : 0 바이트
===== csc -optimize -out:exo.dll cs21b-alloc.cs && dotnet exo.dll (cc exit=0 · run exit=0) =====
[1] arr is [1, .., var last]     1000번 : 0 바이트
[2] arr is [_, .. var rest]      1000번 : 56000 바이트
[3] span is [_, .. var rest]     1000번 : 0 바이트
[4] str is [_, .. var rest]      1000번 : 40000 바이트
[5] boxed is int n               1000번 : 0 바이트
===== csc -optimize -out:exo.dll cs21b-alloc.cs && DOTNET_TieredCompilation=0 dotnet exo.dll (cc exit=0 · run exit=0) =====
[1] arr is [1, .., var last]     1000번 : 0 바이트
[2] arr is [_, .. var rest]      1000번 : 56000 바이트
[3] span is [_, .. var rest]     1000번 : 0 바이트
[4] str is [_, .. var rest]      1000번 : 40000 바이트
[5] boxed is int n               1000번 : 0 바이트
===== 네 판 대조 — 「바이트」 줄마다 네 판의 값이 같은가 =====
네 판에서 갈린 줄 0 / 5
```

**왜 그런가**

- ★★★ **`int[]` 에 `.. var rest` 는 매번 새 배열**(`GetSubArray`), **문자열은 새 문자열**. **`ReadOnlySpan<int>` 는 뷰라 0** — 같은 패턴인데 **받는 타입의 범위 연산**이 갈랐다([09번](../09-arrays-index-and-range/) (3)).
- ★★ **슬라이스를 안 받는 `[1]` 은 0** · **언박싱 `[5]` 도 0**.
- ★ **네 판에서 갈린 줄 0 / 5** — 이 값들은 판을 안 탔다.

### 6. ★★ `Limit` 은 **상수** — `limit` 은 **`CS0103`**

**출력**

```text
===== 소스: cs21b-const.cs =====
using System;
class Program {
    const int Limit = 5;
    static string A(int x) => x switch { Limit => "첫 팔", var n => $"둘째 팔 n={n}" };
    static void Main() {
        Console.WriteLine($"[1] A(5) = {A(5)}");
        Console.WriteLine($"[2] A(7) = {A(7)}");
    }
}
===== csc -out:ex.dll cs21b-const.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
[1] A(5) = 첫 팔
[2] A(7) = 둘째 팔 n=7
===== 소스: cs21b-capture.cs =====
class Program {
    static string B(int x) => x switch { limit => "첫 팔", _ => "둘째 팔" };   // 선언된 적 없는 이름
    static void Main() { }
}
===== csc -out:ex.dll cs21b-capture.cs 2>&1 | sort (cc exit=1) =====
cs21b-capture.cs(2,42): error CS0103: The name 'limit' does not exist in the current context
```

**왜 그런가**

- ★★★ **`A(5)` 첫 팔 · `A(7)` 둘째 팔 `n=7`** — `Limit` 은 **상수 패턴**(값 5 와 비교)이다. 새 변수가 아니다.
- ★★★ **둘째 소스는 `CS0103`**(이름이 없다) — C# 에서 이름 하나만 적은 패턴은 **상수를 찾는다.** 새 변수는 **`var n`·`int n` 처럼 타입을 달아야** 생긴다.

### 7. ★★ **`CS8985` · `CS0021` · `CS8980` · `CS0270`**

**출력**

```text
===== 소스: cs21b-listerr.cs =====
using System.Collections.Generic;
class Counted { public int Count => 3; }                 // Count 만 있고 인덱서가 없다
class Program {
    static bool A(IEnumerable<int> xs) => xs is [1, ..];
    static bool B(Counted c)           => c is [_, _, _];
    static bool C(int[] a)             => a is [.., 1, ..];
    static void Main() { }
}
===== csc -out:ex.dll cs21b-listerr.cs 2>&1 | sort (cc exit=1) =====
cs21b-listerr.cs(4,49): error CS0021: Cannot apply indexing with [] to an expression of type 'IEnumerable<int>'
cs21b-listerr.cs(4,49): error CS8985: List patterns may not be used for a value of type 'IEnumerable<int>'. No suitable 'Length' or 'Count' property was found.
cs21b-listerr.cs(5,48): error CS0021: Cannot apply indexing with [] to an expression of type 'Counted'
cs21b-listerr.cs(6,56): error CS8980: Slice patterns may only be used once and directly inside a list pattern.
===== 소스: cs21b-typelist.cs =====
using System.Collections.Generic;
class Program {
    static bool D(object o) => o is List<int> [1, ..];          // 타입 바로 뒤에 목록 패턴
    static bool E(object o) => o is List<int> and [1, ..];      // and 로 잇는다
    static void Main() { }
}
===== csc -out:ex.dll cs21b-typelist.cs 2>&1 | sort (cc exit=1) =====
cs21b-typelist.cs(3,47): error CS0270: Array size cannot be specified in a variable declaration (try initializing with a 'new' expression)
```

**왜 그런가**

- ★★★ **`IEnumerable<int>` → `CS8985`**(「`Length`/`Count` 가 없다」) + `CS0021` — 목록 패턴은 **열거하지 않는다.**
- ★★ **`Count` 만 있는 `Counted` → `CS0021`** — 인덱서도 있어야 한다.
- ★ **`..` 두 번 → `CS8980`** · **`List<int> [1, ..]` → `CS0270`** — 배열 타입 선언으로 읽혔다. **`and` 로 이으면** 된다.

### 8. ★★ **10 → 6 → 2 → 1 → 0줄** — 진단 문구가 **요구 판**을 말한다

**출력**

```text
===== 소스: cs21b-ver.cs =====
class Box { public Box Inner = null; public int V = 0; }
class Program {
    static bool L03(object o) => o is string s;                 // 선언 패턴
    static bool L04(object o) => o is Box { V: 3 };             // 속성 패턴
    static int  L05(object o) => o switch { Box => 1, _ => 0 }; // switch 식 · 타입만 적은 팔
    static bool L06(int x)    => x is > 3;                      // 관계 패턴
    static bool L07(int x)    => x is 1 or 2;                   // or
    static bool L08(object o) => o is not null;                 // not
    static bool L09(Box b)    => b is { Inner.V: 1 };           // 확장 속성 패턴
    static bool L10(int[] a)  => a is [1, ..];                  // 목록 패턴
    static void Main() { }
}
===== csc -langversion:7.3 -out:ex.dll cs21b-ver.cs 2>&1 | grep ': error ' | sort -t'(' -k2n (cc exit=1) =====
cs21b-ver.cs(4,39): error CS8370: Feature 'recursive patterns' is not available in C# 7.3. Please use language version 8.0 or greater.
cs21b-ver.cs(5,36): error CS8370: Feature 'recursive patterns' is not available in C# 7.3. Please use language version 8.0 or greater.
cs21b-ver.cs(5,45): error CS8370: Feature 'type pattern' is not available in C# 7.3. Please use language version 9.0 or greater.
cs21b-ver.cs(5,55): error CS8370: Feature 'recursive patterns' is not available in C# 7.3. Please use language version 8.0 or greater.
cs21b-ver.cs(6,39): error CS8370: Feature 'relational pattern' is not available in C# 7.3. Please use language version 9.0 or greater.
cs21b-ver.cs(7,41): error CS8370: Feature 'or pattern' is not available in C# 7.3. Please use language version 9.0 or greater.
cs21b-ver.cs(8,39): error CS8370: Feature 'not pattern' is not available in C# 7.3. Please use language version 9.0 or greater.
cs21b-ver.cs(9,39): error CS8370: Feature 'recursive patterns' is not available in C# 7.3. Please use language version 8.0 or greater.
cs21b-ver.cs(9,48): error CS8370: Feature 'extended property patterns' is not available in C# 7.3. Please use language version 10.0 or greater.
cs21b-ver.cs(10,39): error CS8370: Feature 'list pattern' is not available in C# 7.3. Please use language version 11.0 or greater.
===== csc -langversion:8 -out:ex.dll cs21b-ver.cs 2>&1 | grep ': error ' | sort -t'(' -k2n (cc exit=1) =====
cs21b-ver.cs(5,45): error CS8400: Feature 'type pattern' is not available in C# 8.0. Please use language version 9.0 or greater.
cs21b-ver.cs(6,39): error CS8400: Feature 'relational pattern' is not available in C# 8.0. Please use language version 9.0 or greater.
cs21b-ver.cs(7,41): error CS8400: Feature 'or pattern' is not available in C# 8.0. Please use language version 9.0 or greater.
cs21b-ver.cs(8,39): error CS8400: Feature 'not pattern' is not available in C# 8.0. Please use language version 9.0 or greater.
cs21b-ver.cs(9,48): error CS8400: Feature 'extended property patterns' is not available in C# 8.0. Please use language version 10.0 or greater.
cs21b-ver.cs(10,39): error CS8400: Feature 'list pattern' is not available in C# 8.0. Please use language version 11.0 or greater.
===== csc -langversion:9 -out:ex.dll cs21b-ver.cs 2>&1 | grep ': error ' | sort -t'(' -k2n (cc exit=1) =====
cs21b-ver.cs(9,48): error CS8773: Feature 'extended property patterns' is not available in C# 9.0. Please use language version 10.0 or greater.
cs21b-ver.cs(10,39): error CS8773: Feature 'list pattern' is not available in C# 9.0. Please use language version 11.0 or greater.
===== csc -langversion:10 -out:ex.dll cs21b-ver.cs 2>&1 | grep ': error ' | sort -t'(' -k2n (cc exit=1) =====
cs21b-ver.cs(10,39): error CS8936: Feature 'list pattern' is not available in C# 10.0. Please use language version 11.0 or greater.
===== csc -langversion:11 -out:ex.dll cs21b-ver.cs 2>&1 | grep ': error ' | sort -t'(' -k2n (cc exit=0) =====
```

**왜 그런가**

- ★★★ **속성·위치(`'recursive patterns'`) 8.0 · 관계·`or`·`not`·타입만(`'type pattern'`) 9.0 · 확장 속성 10.0 · 목록 11.0** — 문구의 **「Please use language version N or greater」** 가 답이다.
- ★ **`Box => 1` 은 9** — `switch` 식(8)보다 한 판 늦다. 8 에서는 `Box _ =>` 로 적었다.
- ★ 진단 코드는 판마다 다르다(`CS8370`·`CS8400`·`CS8773`·`CS8936`) — 외울 것은 코드가 아니라 **판 번호**다.

### 9. ★★★ **관찰이다** — 명세는 검사 순서를 **정하지 않는다**

- ★★★ **1회는 Roslyn 의 결정 DAG 가 정한 것**이다. Learn — 「결합 순서가 같은 패턴을 컴파일러가 검사하는 순서는 **정해지지 않았다**. 오른쪽 패턴을 먼저 볼 수도 있다」.
- ★★ 그러니 **부작용이 있거나(계수·로그·지연 초기화) 매번 값이 바뀌는 속성**을 패턴에 넣지 마라 — 몇 번·어느 순서로 불릴지 약속이 없다.
- ★ **`&&` 는 식 두 개**라 언어가 **왼쪽부터 두 번** 평가하도록 정한다 — 그래서 2회는 보장이다.

### 10. ★★ Java 는 **타입·레코드 패턴 + `when`**, 속성·관계·목록은 없다 — Python 은 **이름 하나가 캡처**

**출력**

```text
===== 소스: Ex21.java =====
record Point(int x, int y) { }
public class Ex21 {
    static String show(Object o) {
        if (o instanceof String s && s.length() > 3) return "긴 문자열 " + s;
        if (o instanceof Point(int x, int y) && x == y) return "대각선 " + x;
        return switch (o) {
            case Integer i when i > 0 -> "양수 " + i;
            case Point(var x, var y)  -> "점 " + x + "," + y;
            default                   -> "그 밖";
        };
    }
    public static void main(String[] a) {
        for (Object o : new Object[] { "pattern", new Point(2, 2), 7, new Point(1, 3), "ab" })
            System.out.println(show(o));
    }
}
===== javac -d j21out j21/Ex21.java && java -cp j21out Ex21 (cc exit=0 · run exit=0) =====
긴 문자열 pattern
대각선 2
양수 7
점 1,3
그 밖
```

**왜 그런가**

- ★★ **Java 21 의 짝** — `instanceof String s`(선언 패턴) · `Point(int x, int y)`(위치 패턴) · `case … when`(`when` 가드).\
  **Java 에 없는 것** — 속성·관계·`and`/`or`/`not`·목록 패턴. Java 는 `&&`·`when` 으로 적는다(이 판에서 Java 쪽 부재를 **던져 확인하지는 않았다**).
- ★★ **Kotlin `is` 는 스마트 캐스트**(같은 변수가 좁은 타입으로 보인다) · **C# `is T x` 는 새 이름**을 만든다.
- ★★★ **Python 은 점 없는 이름이 캡처 패턴**이라 `case red:` 가 **모든 값에 맞는다**. **C# 은 이름 하나가 상수 패턴**이라 없으면 `CS0103` — 새 변수는 **반드시 `var`/타입을 단다.**

### 11. 잇기

- ★★ **패턴 기반 인덱싱** — [14번](../14-indexers/) (5).
- ★★ **`Deconstruct` 자동 생성** — [18번](../18-record-value-equality-and-with/).
- ★★ **`==` 는 정적 타입이 고른다** — [19번](../19-equality-equals-gethashcode-operator/) (3).
- ★ **완전성·도달 불가** — 목록의 **22번 주제**.

## 실행 검증

| 무엇 | 몇 번·어디서 | 결과 |
|---|---|---|
| `cs21b-il.cs` 선언·관계 패턴 IL | csc 1회 | ★★★ `isinst` 한 번 · 비교 둘 |
| `cs21b-list.cs` 목록 패턴 IL | csc 1회 | ★★★ `ldlen`/`get_Count`/`get_Length` + 인덱서 · `GetSubArray` |
| `cs21b-listerr.cs` · `cs21b-typelist.cs` | csc 2회 | `CS8985`·`CS0021`×2·`CS8980` · `CS0270` |
| `cs21b-null.cs` null 검사 다섯 | csc 1회(`-nullable:enable`) | ★★★ 연산자 호출 **2**(`==`·`!=` 만) · `is not null` 은 `cgt.un` |
| `cs21b-getter.cs` 호출 횟수 | csc 2회(기본·`-optimize`) | ★★★ `&&` 2 · 나머지 1 · 두 판 같음 |
| `cs21b-const.cs` · `cs21b-capture.cs` | csc 2회 | 상수 패턴 · `CS0103` |
| `cs21b-ver.cs` 판 경계 | csc 5회(`-langversion` 7.3\~11) | ★★★ 10 → 6 → 2 → 1 → 0 |
| `cs21b-alloc.cs` 슬라이스 할당 | **2×2 판 격자** | ★★★ 배열 56000 · 문자열 40000 · `Span` 0 · **갈린 줄 0 / 5** |
| `Ex21.java` | javac 1회 · java 1회 | 타입·레코드 패턴·`when` |
| `cs21b-form.cs` 형태 | csc 1회 | `문자열 5자` · `목록 1..3` · `큰 주문` · `없음` |

**구현 의존 항목** — 다음은 **이 판(.NET SDK 10.0.401 · 런타임 10.0.12)에서만** 그렇다.

- ★★★ **getter·`Deconstruct` 1회** — Roslyn 결정 DAG. 명세는 순서·횟수를 약속하지 않는다.
- ★★ **IL 의 구체적 모양**(`cgt.un`·`sub`·`GetSubArray`) · **진단 코드 번호와 문구**.

**언어가 보장하는 것**(구현이 바뀌어도 같다)

- **선언·타입·속성 패턴은 null 에 안 맞는다** · **`is null` 은 사용자 `==` 를 안 부른다**.
- **목록 패턴은 길이 속성 + 인덱서를 요구한다** · **슬라이스는 한 번만** · **각 패턴의 요구 판**.

**안 돌려 본 것 / 못 잰 것 / 잴 것이 없는 것**

- **안 돌려 본 것** — ★ **`when` 절 사이에서 getter 가 다시 읽히는지** · ★ **Java 에 속성·관계 패턴이 없다는 것을 javac 로** · ★ **`Span<char>` 을 문자열 상수와 맞추기**.
- **못 잰 것** — ★★★ **시간** — 한 줄도 안 쟀다.
- **잴 것이 없는 것** — ★ **③ 리플렉션** — 패턴은 메타데이터에 아무것도 안 남긴다.

**버전이 올랐을 때 다시 돌려야 하는 것**

- ★★★ **3번의 호출 횟수** — Roslyn 이 결정 DAG 를 바꾸면 움직일 수 있다. **움직여도 명세 위반이 아니다.**
- ★★ **5번의 판 격자** — 배열 슬라이스가 복사라는 것은 BCL 의 선택이다.
- ★ **8번** — 새 판이 나오면 진단 코드가 하나 더 생긴다(C# 15 의 `closed` 는 22번 주제가 던졌다).
