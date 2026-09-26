# csharp/syntax/21 — 패턴 매칭 — 타입·속성·관계·목록 패턴 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [ECMA-334 7판(2023-12)](https://ecma-international.org/publications-and-standards/standards/ecma-334/) ·
> [Learn — 패턴](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/operators/patterns)(열어서 확인: 「선언 패턴은 식의 결과가 **null 이 아니고** 런타임 타입이 맞을 때 맞는다」 ·\
> 「컴파일러는 `x is null` 을 평가할 때 **사용자가 오버로드한 `==` 를 부르지 않는다고 보장**한다」 · 「빈 속성 패턴 `is { }` 는 **null 아닌 모든 것**과 맞는다」 ·\
> 「**결합 순서가 같은 패턴을 컴파일러가 어떤 순서로 검사하는지는 정해져 있지 않다**」 · 「슬라이스 패턴은 목록 패턴 안에서 **한 번만**」)
> **실행 검증** — 이 문서의 모든 출력·진단·IL·할당 바이트는 아래 「이 판」의 도구로 **실제로 돌려 얻은 것**이다(2026-09-26).\
> ★ 블록은 캡처 스크립트가 파일로 받아 조립기가 끼워 넣은 것이다 — 사람이 옮겨 적은 줄은 하나도 없다.\
> ★★★ **진단 언어를 영어로 고정했다**(`DOTNET_CLI_UI_LANGUAGE=en` + `-preferreduilang:en-US`). **대비는 실측이다** — **javac 21.0.5** 로 Java 패턴을 돌렸다((8)).
> **버전** — ★★ **판 경계는 컴파일러에게 물었다**((7)) — 선언 패턴 **C# 7** · 속성·위치 패턴과 `switch` 식 **C# 8** · 타입만 적는 패턴·관계·`and`/`or`/`not` **C# 9** · 확장 속성 패턴 **C# 10** · 목록·슬라이스 패턴 **C# 11**.
> **경계** — ★★ **`switch` 식·`switch` 문과 완전성 검사**는 목록의 **22번 주제**가 정본이다 — 여기서는 **패턴 하나가 IL 로 무엇이 되나**만 본다.\
> ★ **`Deconstruct` 가 생성되는 것**은 [18번](../18-record-value-equality-and-with/)이, **`==` 가 정적 타입으로 골라지는 것**은 [19번](../19-equality-equals-gethashcode-operator/)이,\
> **패턴 기반 인덱싱(`Length` + `this[int]`)** 은 [14번](../14-indexers/) (5)가, **배열 `..` 이 복사라는 것**은 [09번](../09-arrays-index-and-range/) (3)이 정본이다.
> ★★★ **대비** — Java 갈래 목록([`java/syntax/README.md`](../../../java/syntax/README.md))의 **22번**([`22-instanceof-type-patterns/`](../../../java/syntax/22-instanceof-type-patterns/))·**24번**([`24-record-patterns/`](../../../java/syntax/24-record-patterns/)) ·\
> Kotlin 갈래 목록([`kotlin/syntax/README.md`](../../../kotlin/syntax/README.md))의 **33번**([`33-type-checks-and-casts-is-as/`](../../../kotlin/syntax/33-type-checks-and-casts-is-as/)) — **스마트 캐스트** ·\
> Python 갈래 목록([`python/syntax/README.md`](../../../python/syntax/README.md))의 **39번**([`39-match-statement/`](../../../python/syntax/39-match-statement/)) — **점 없는 이름은 캡처**다.
>
> ★★ **흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | 진단 **문구** | ★★★ **진단 코드**(`CS8985`·`CS8980`·`CS0021`·`CS0270`·`CS0103`·`CS8370`·`CS8400`·`CS8773`·`CS8936`)와 **`(행,열)`** |
> | **IL 오프셋 폭** · 분기 명령의 짧은/긴 꼴 | ★★★ **옵코드와 부른 멤버**(`isinst` · `ldlen` · `get_Count` · `get_Item` · `GetSubArray` · `cgt.un` · `op_Inequality`) |
> | ★ **getter·`Deconstruct` 호출 횟수**(Roslyn 의 결정 DAG 가 정한다 — 명세는 순서를 **정하지 않는다**) | ★★ 이 판에서 그 횟수가 **`csc` 기본과 `-optimize` 에서 같았다**는 것 |
> | 증분의 절댓값 일부(규칙 24) | ★★★ **네 판에서 갈린 줄 수**(스크립트가 센 마지막 줄) |

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
| **언어 명세(ECMA-334 · 기능 명세)** | C# 언어가 약속한 것 | ★★★ 패턴의 **뜻**(선언 패턴은 null 에 안 맞는다 · `is null` 은 오버로드된 `==` 를 안 부른다) · **목록 패턴은 `Length`/`Count` + 인덱서를 요구한다** · ★ **검사 순서는 정하지 않는다** |
| **컴파일러(Roslyn)** | 패턴을 **어떤 IL 로 낮추나** | ★★★ `isinst` + `stloc` · 관계 패턴이 **비교 분기 둘** · 목록 패턴이 **`ldlen`/`get_Count` + 인덱서** · ★★ **여러 팔이 getter 를 한 번만 읽는 것**(결정 DAG) |
| **이 판의 관찰** | .NET 10.0.12 · linux-x64 · javac 21.0.5 | 호출 횟수 1회 · 할당 바이트 · 진단 문구 |

★★★ **이 주제에서 가장 조심할 칸은 「getter 를 한 번만 읽는다」다** — 관찰은 **1회**지만 명세는 **순서도 횟수도 약속하지 않는다**((4)).\
그래서 **부작용이 있는 속성을 패턴에 넣지 마라**가 결론이지, 「한 번만 부른다」가 결론이 아니다.

## 한눈에 — 쉽게 말하면

**패턴은 「검사하고 꺼내기」를 한 문장에 적는 것이다 — 컴파일러가 그것을 평범한 비교와 분기로 풀어 쓴다.**

공항 보안 검색대를 생각하자.

- **`o is string s`** — 「**이 가방이 여행가방이면**, 그 가방을 `s` 라고 부르자」. 검사와 이름 붙이기가 **한 동작**이다.
- **`x is >= 0 and < 10`** — 「무게가 **0 이상 10 미만**」. 저울을 **두 번** 보는 것이 아니라 **한 번 올려 두고 두 눈금을 읽는** 것.
- **`w is { Len: > 3 }`** — 「가방의 **길이 칸**을 열어 보고 3 보다 크면」. **null 이면 안 연다**(맞지 않는다).
- **`a is [1, .., var last]`** — 「**첫 칸이 1** 이고 **마지막 칸을 `last`** 라고 부르자」. 검색대는 **개수(`Length`)를 먼저 세고** 칸 번호로 꺼낸다.
- **`t is not null`** — 「**비어 있지 않으면**」. 가방 주인이 **자기만의 비교 규칙**(오버로드한 `==`)을 붙여 놔도 **검색대는 그것을 안 쓴다.**

| 비유 | 실체 | 어디서 보나 |
|---|---|---|
| 검사와 이름 붙이기가 한 동작 | ★★★ **`isinst System.String` → `stloc.0`** — 캐스트 결과를 **그대로 변수에** | (1) |
| 저울을 한 번 올리고 두 눈금 | ★★ **`ldc.i4.0` · `blt.s` · `ldc.i4.s 10` · `clt`** — 비교 둘 | (1) |
| 칸을 열어 본다 | ★★★ **여러 팔이 있어도 `get_Len` 1회**(이 판) | (4) |
| 개수를 먼저 센다 | ★★★ **배열은 `ldlen`, `List` 는 `get_Count`, 내 타입은 `get_Length`** + 인덱서 | (2) |
| 주인의 비교 규칙을 안 쓴다 | ★★★ **`is not null` 은 `cgt.un`**, `!= null` 은 **`call Token::op_Inequality`** | (3) |

★★★ **이 주제의 본체 그림 — 패턴 하나가 IL 로 무엇이 되나.**

```text
   C# 패턴                               IL (이 판의 Roslyn)
   ──────────────────────────────        ──────────────────────────────────────────────
   o is string s                    →    isinst String / stloc.0 / ldloc.0 / brtrue      ← 캐스트 한 번
   x is >= 0 and < 10               →    ldc.i4.0 / blt.s … / ldc.i4.s 10 / clt          ← 비교 둘
   t is not null                    →    ldnull / cgt.un                                  ← 연산자 호출 없음
   t != null                        →    ldnull / call Token::op_Inequality               ← 오버로드가 불린다
   a is [1, .., var last]  (int[])  →    ldlen / conv.i4 / ldc.i4.2 / blt / ldelem …     ← 길이 + 인덱스
   a is [1, .., var last]  (List)   →    callvirt get_Count / … / callvirt get_Item
   a is [_, .. var rest]   (int[])  →    newobj Range / call RuntimeHelpers::GetSubArray ← ★ 새 배열

   ★★★ 새 명령은 하나도 없다 — 전부 평범한 비교·분기·호출로 풀린다.
       다만 「무엇을 부르나」가 패턴 종류마다 다르고, 그 차이가 null 처리와 할당에서 드러난다.
```

## 이 주제가 답하려는 질문

1. **패턴은 IL 로 무엇이 되나** — 새 기계가 있나, 평범한 비교로 풀리나((1)(2)).
2. **`is not null` 과 `!= null` 은 같은가** — 연산자를 오버로드한 타입에서((3)).
3. **속성 패턴의 getter 는 몇 번 불리나** — 그것은 보장인가((4)).
4. **목록 패턴은 어떤 타입에 붙나** — 무엇을 요구하나, 할당은 있나((2)(5)(6)).
5. **이름 하나가 상수인지 새 변수인지 무엇이 가르나** — Python·Java·Kotlin 과((8)).

## 동작 방식

### (0) 이 주제가 쓰는 창

★★★ **본체 창은 ① IL 덤프다** — 「패턴은 문법 설탕이고 평범한 비교로 풀린다」는 IL 로만 증명된다.

| 창 | 무엇을 보여 주나 | 이 주제에서 |
|---|---|---|
| ★★★ **① IL 덤프** | `isinst`+`stloc` · 관계 패턴의 비교 둘 · 목록 패턴의 **`ldlen`/`get_Count`/`get_Length` + 인덱서** · `is not null` 의 **`cgt.un`** | (1)(2)(3) |
| ★★ **실행 로그(부작용 계수)** | ★★ **제5의 상태** — getter·`Deconstruct` 호출 횟수는 IL 을 읽어도 알 수 있지만 **여러 팔이 겹칠 때 몇 번인지는 로그가 더 곧다**. 연산자 호출 여부도 로그로 | (3)(4) |
| ★★ **② 진단 격자** | 목록 패턴을 거절하는 코드(`CS8985`·`CS0021`·`CS8980`) · **판 경계 다섯 벌**(`-langversion` 7.3\~11) · 캡처 대신 `CS0103` | (5)(7)(8) |
| ★★ **④ 할당 바이트** | ★★ **슬라이스 패턴 `.. var rest` 가 배열·문자열에서 할당, `Span` 에서 0** — 2×2 판 격자 | (6) |
| ③ **리플렉션** | ★ **부적용** — 패턴은 타입을 만들지 않는다. 메타데이터에 남는 것이 없어 **잴 것이 없다**(18-B) | — |

### (1) ★★★ 선언·관계 패턴 — 캐스트 한 번, 비교 둘

**언제 쓰나** — `object`·기반 타입으로 받은 값을 **검사하고 바로 쓰고 싶을 때** · 범위를 한 줄로 적고 싶을 때.

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

- ★★★ **`Decl` 은 `isinst System.String` → `stloc.0` → `ldloc.0` → `brtrue.s`** — **캐스트는 `isinst` 한 번**이고, 그 결과(참조 또는 null)를 **그대로 `s` 에 담는다.**\
  「`is` 로 검사하고 `(string)o` 로 한 번 더 캐스트」하던 옛 꼴의 **두 번째 캐스트가 없다.**
- ★★ **`Type`(`o is string`) 은 `isinst` + `ldnull` + `cgt.un`** — 변수를 안 만들면 **「null 이 아닌가」로만** 쓴다.
- ★★★ **`Range`(`x is >= 0 and < 10`) 는 `ldc.i4.0` · `blt.s` · `ldc.i4.s 10` · `clt`** — **비교 둘**이다. `x` 를 두 번 읽지만 **`ldarg.0` 이라 부작용이 없다.**
- ★★ **`Outside`(`or`) 는 지역 변수 `Boolean` 하나**를 두고 분기한다 — **`or` 은 단락 평가처럼** 첫 비교가 맞으면 둘째를 안 본다.
- ★ **`Letter('Q')` 가 `True`** — `not (>= 'a' and <= 'z')` 는 **괄호가 있어야** 뜻대로 묶인다. Learn — 「`not` 이 `and` 보다 **먼저** 묶인다」.

> **어느 층인가** — ★★★ 「선언 패턴은 null 에 안 맞는다」는 **언어(334)** 다. 그것이 **`isinst` 의 null 결과**로 풀리는 것은 **Roslyn** 이다.\
> ★ 「`isinst` 다음 `stloc`」 모양을 외우지 마라 — **캐스트가 한 번**이라는 **성질**이 외울 것이다([16번](../16-inheritance-virtual-override-abstract-sealed-new/) (4)가 `callvirt` 에서 같은 말을 했다).

### (2) ★★★ 목록 패턴 — 길이를 세고 인덱서로 꺼낸다

**언제 쓰나** — 「첫 원소가 1 이고 마지막을 꺼내라」처럼 **모양**으로 분기할 때.

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

- ★★★ **배열(`Arr`)은 `ldlen` · `conv.i4`**, **`List<int>`(`Lst`)는 `callvirt get_Count`**, **내 타입 `Bag`(`Own`)은 `callvirt get_Length`** — **길이를 먼저 읽는다.**
- ★★★ 그 길이가 **`ldc.i4.2` 보다 작으면**(`blt.s`) 바로 실패 — `[1, .., var last]` 는 **원소가 적어도 둘**이어야 한다(`Arr(new[] { 1 })` 가 `-1`).
- ★★★ **마지막 원소는 `길이 - 1` 을 직접 계산**(`ldloc.1` · `ldc.i4.1` · `sub`)해 **`ldelem.i4` / `get_Item`** 으로 꺼낸다.\
  ★★ **[14번](../14-indexers/) (5)의 패턴 기반 인덱싱과 같은 규칙**이다 — `Bag` 은 **인터페이스가 하나도 없는데** `Length` + `this[int]` 만으로 목록 패턴이 붙었다. **`System.Index` 가 IL 에 안 나타난다.**
- ★★★ **`Rest`(`[_, .. var rest]`)는 `newobj System.Index` 둘 · `newobj System.Range` · `call RuntimeHelpers::GetSubArray`** — **새 배열을 만든다**((6)에서 바이트로 확인).\
  [09번](../09-arrays-index-and-range/) (3)의 「**배열의 `..` 은 복사**」가 **패턴 안에서도** 그대로다.

```text
   a is [1, .., var last]                         a is [_, .. var rest]
   ──────────────────────────                     ─────────────────────────────
   n = 길이 (ldlen · get_Count · get_Length)       n = 길이
   n < 2 이면 실패                                   n < 1 이면 실패
   a[0] == 1 ?        (ldelem · get_Item)          rest = a[1..]   ← GetSubArray(a, Range)
   last = a[n - 1]    (sub 로 직접 계산)                               ★ 배열이면 새 배열
                                                                     ★ Span 이면 뷰((6))
   ★★★ 「타입이 IList 를 구현하나」 는 안 본다 — 길이 속성과 int 인덱서만 본다.
```

### (3) ★★★ `is not null` 은 연산자를 안 부른다 — `!= null` 은 부른다

**언제 쓰나** — `==`/`!=` 를 **오버로드한 타입**을 null 과 비교할 때. [19번](../19-equality-equals-gethashcode-operator/) (3)의 「`==` 는 정적 타입이 고른다」의 짝이다.

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

- ★★★ **`[3]` `none == null` 이 `False`** — null 을 null 과 비교했는데 **거짓**이다. **`Token.op_Equality` 가 불려**(로그 한 줄) 그것이 `false` 를 돌려줬다.
- ★★★ **`[1]` `is null` · `[2]` `is not null` · `[5]` `is { }` 는 로그가 없다** — 연산자 호출 횟수 **2** 는 `[3]`·`[4]` 의 것뿐이다.
- ★★★ IL — **`IsNull` 은 `ceq`**, **`IsNotNull`·`Empty` 는 `cgt.un`**(참조를 **부호 없는 정수로 비교** — null 은 0), **`EqNull`·`NeNull` 은 `call Token::op_…`**.
- ★★ **`is { }` 와 `is not null` 의 IL 이 한 글자도 같다** — Learn 의 「빈 속성 패턴은 null 아닌 모든 것」 그대로다. 차이는 **`is { } x` 로 변수를 만들 수 있다**는 것뿐.

> **어느 층인가** — ★★★ **「`x is null` 은 사용자 `==` 를 부르지 않는다」는 Learn 이 「컴파일러가 보장한다」고 적은 언어 보장**이다.\
> ★ 그래서 **null 검사는 `is null`/`is not null` 로** — 남이 만든 타입의 `==` 가 무엇을 하든 **null 검사의 뜻이 안 바뀐다.** [07번](../07-null-operators/)이 「패턴 매칭과의 경계」로 남겨 둔 자리가 이것이다.

### (4) ★★ getter 는 몇 번 불리나 — 관찰은 1회, 보장은 없다

**언제 쓰나** — 속성 패턴에 **계산이 비싸거나 부작용이 있는 속성**을 넣으려 할 때.

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

- ★★★ **`[1]` `&&` 로 쓴 식은 `get_Len` 2회**, **`[2]` 같은 조건을 `and` 패턴으로 쓰면 1회**, **`[3]` 한 속성 안에 `> 3 and < 9` 도 1회.**
- ★★★ **`[4]` 팔이 넷인 `switch` 식도 `get_Len` 1회** — 팔마다 다시 읽지 않는다. Roslyn 이 팔 전체를 **결정 DAG**(한 번 읽은 값을 공유하는 분기 그래프)로 합치기 때문이다.
- ★★ **`[5]` 위치 패턴 팔 넷에서 `Deconstruct` 도 1회.**
- ★★ **`csc` 기본과 `csc -optimize` 가 같다** — JIT 최적화가 아니라 **컴파일러가** 정한 횟수로 읽힌다(★ 이 탐침의 IL 은 **찍지 않았다** — 해석이다).
- ★★★ **그러나 명세는 이것을 약속하지 않는다** — Learn: 「**결합 순서가 같은 패턴을 검사하는 순서는 정해져 있지 않다.** 오른쪽 패턴을 먼저 볼 수도 있다」.\
  ★ 그러니 **1회에 기대는 코드도, 2회에 기대는 코드도 틀렸다.** 결론은 **「속성 패턴에는 부작용 없는 속성만」** 이다.

```text
   w.Len > 3 && w.Len < 9                  w is { Len: > 3 } and { Len: < 9 }
   ─────────────────────────               ───────────────────────────────────
   get_Len ─▶ >3 ?                          get_Len ─▶ t
   get_Len ─▶ <9 ?     ← 두 번 읽는다          t > 3 ? ─▶ t < 9 ?   ← 한 번 읽고 나눠 쓴다

   ★★ 왼쪽은 언어가 「두 번」 을 약속한다(식 두 개).
   ★★ 오른쪽의 「한 번」 은 이 판 Roslyn 의 선택이다 — 명세는 순서·횟수를 안 정한다.
```

### (5) ★★ 목록 패턴이 거절되는 자리

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

- ★★★ **`IEnumerable<int>` 는 `CS8985`** — 「`Length` 나 `Count` 속성이 없다」. **목록 패턴은 열거를 안 한다** — 길이와 인덱서가 있어야 한다.
- ★★ **`Count` 만 있고 인덱서가 없는 `Counted` 는 `CS0021`**(인덱싱 불가) — **둘 다** 있어야 한다.
- ★★ **`[.., 1, ..]` 은 `CS8980`** — 슬라이스는 **한 번만**. 「가운데 어딘가에 1」은 패턴으로 못 쓴다.
- ★★ **`o is List<int> [1, ..]` 은 `CS0270`**(「변수 선언에 배열 크기를 적을 수 없다」) — 파서가 `List<int>[…]` 를 **배열 타입**으로 읽었다. **`and` 로 이으면**(`E`) 진단이 없다.

### (6) ★★ 슬라이스 패턴의 할당 — 2×2 판 격자

**언제 쓰나** — 「목록 패턴은 공짜인가」를 물을 때. **시간은 재지 않았다.**

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

- ★★★ **네 판에서 갈린 줄 0 / 5** — 이 표의 값은 판을 안 탄다.
- ★★★ **`[1]` 슬라이스 없는 목록 패턴은 0** · **`[2]` `int[]` 에 `.. var rest` 는 56000**(1000번 — 한 번에 새 배열 하나) · **`[4]` 문자열에 `.. var rest` 는 40000**(새 문자열).
- ★★★ **`[3]` `ReadOnlySpan<int>` 에 `.. var rest` 는 0** — `Span` 의 슬라이스는 **뷰**다. [09번](../09-arrays-index-and-range/) (3)의 복사/뷰 갈림이 **패턴 안에서도 그대로**다.
- ★ **`[5]` `boxed is int n` 은 0** — 언박싱은 할당이 없다([03번](../03-boxing-and-unboxing/) (1)).
- ★★ **「패턴은 할당이 없다」가 아니다** — **슬라이스를 변수로 받으면** 그 타입의 범위 연산이 불린다. **`..` 만 쓰고 받지 않으면 0**(`[1]`).

### (7) ★★ 판 경계 — `-langversion` 을 바꿔 컴파일러에게 묻는다

**언제 쓰나** — 「이 패턴은 몇 판부터인가」를 **기억이 아니라 진단으로** 답할 때.

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

- ★★★ **진단이 판마다 줄어든다** — 7.3 에서 10줄 → 8 에서 6줄 → 9 에서 2줄 → 10 에서 1줄 → **11 에서 0줄**(`cc exit=0`).
- ★★★ **진단 문구에 기능 이름과 요구 판이 박혀 있다** — `'recursive patterns'`(속성·위치, **8.0**) · `'type pattern'`·`'relational pattern'`·`'or pattern'`·`'not pattern'`(**9.0**) · `'extended property patterns'`(**10.0**) · `'list pattern'`(**11.0**).
- ★★ **줄 5 의 `Box => 1`** — `switch` 식 자체는 8 인데 **타입 이름만 적은 팔**은 9 다(`'type pattern'`). C# 8 에서는 `Box _ => 1` 로 적어야 했다.
- ★ **진단 코드가 판마다 다르다**(`CS8370`·`CS8400`·`CS8773`·`CS8936`) — **「몇 판 기능이 이 판에 없다」 코드가 판마다 따로** 있다. 코드보다 **문구 속 판 번호**가 읽기 쉽다(문구는 흔들리는 칸이니 **요구 판 숫자**만 근거로 쓴다).

| 패턴 | 요구 판(진단이 말한 것) |
|---|---|
| `o is string s`(선언) | ≤ 7.3 — 7.3 에서 진단 없음 |
| `{ V: 3 }`(속성) · `switch` 식 · 위치 | **8.0** |
| `Box =>`(타입만) · `> 3` · `or` · `not` | **9.0** |
| `{ Inner.V: 1 }`(확장 속성) | **10.0** |
| `[1, ..]`(목록) | **11.0** |

### (8) ★★ 이름 하나 — 상수인가 새 변수인가 · Java 와 대비

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

- ★★★ **`Limit => …` 은 상수 패턴**이다 — `A(5)` 는 첫 팔, `A(7)` 은 둘째 팔. **`Limit` 이 새 변수로 「캡처」되지 않는다.**
- ★★★ **선언된 적 없는 `limit` 은 `CS0103`**(이름이 없다) — C# 은 **캡처하려면 `var n` 이나 `int n` 을 적어야** 한다. **이름 하나만 적어서는 절대 새 변수가 안 생긴다.**
- ★★ Python `match` 는 반대다 — **점 없는 이름은 캡처 패턴**이라 `case red:` 가 **무엇이든 삼킨다**([Python 39번](../../../python/syntax/39-match-statement/) — `name capture 'red' makes remaining patterns unreachable`).\
  **C# 은 상수 패턴과 선언 패턴이 문법(타입/`var` 유무)으로 갈려서** 그 사고가 원리상 없다.

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

- ★★ **Java 21 은 `instanceof String s`(타입 패턴) · 레코드 패턴 `Point(int x, int y)` · `case … when`** 을 가진다 — C# 의 **선언·위치 패턴·`when`** 과 같은 자리다.
- ★★ **Java 에 없는 것** — **속성 패턴**(`{ Len: > 3 }`) · **관계 패턴**(`> 3`) · **`and`/`or`/`not` 조합** · **목록 패턴**. Java 는 이것들을 **`&&` 조건이나 `when` 절**로 적는다(위 소스의 `&& s.length() > 3`).\
  ★ 이 차이는 **이 판에서 Java 쪽을 던져 확인하지 않았다** — Java 갈래의 [22번](../../../java/syntax/22-instanceof-type-patterns/)·[23번](../../../java/syntax/23-switch-pattern-matching/)·[24번](../../../java/syntax/24-record-patterns/)이 정본이다.
- ★★ **Kotlin `is` 는 스마트 캐스트** — 검사 뒤 **같은 변수가 그 타입으로 보인다**(새 이름이 없다). C# `is T x` 는 **새 이름**을 만든다.\
  [Kotlin 33번](../../../kotlin/syntax/33-type-checks-and-casts-is-as/)이 C# `is`/`as` 를 직접 던져 대비했다(그 문서의 (8)).

```text
                     검사하고 꺼내기                 이름 하나만 적으면
   C#  is/switch      o is string s  (새 이름)       상수 패턴 — 없으면 CS0103
   Java instanceof    o instanceof String s          (case 에 이름만 — 이 판에서 안 던졌다)
   Kotlin is          if (o is String) o.length      (스마트 캐스트 — 새 이름 없음)
   Python match       case str() as s                ★ 캡처 — 무엇이든 맞는다

   ★★★ C# 은 「새 변수는 반드시 타입이나 var 를 달고 나온다」 — 그래서 상수와 캡처가 헷갈릴 수 없다.
```

## 문법 — 형태와 규칙

### 형태

```text
===== 소스: cs21b-form.cs =====
using System;
using System.Collections.Generic;

Console.WriteLine(Describe("hello"));
Console.WriteLine(Describe(new List<int> { 1, 2, 3 }));
Console.WriteLine(Describe(new Order(3, 120m)));
Console.WriteLine(Describe(null));

static string Describe(object? o) => o switch {
    null                                    => "없음",
    string { Length: 0 }                    => "빈 문자열",
    string s                                => $"문자열 {s.Length}자",
    List<int> and [var first, .., var last] => $"목록 {first}..{last}",
    Order { Qty: > 0, Total: >= 100m }      => "큰 주문",
    Order(var q, _)                         => $"주문 {q}개",
    _                                       => "그 밖",
};

record Order(int Qty, decimal Total);
===== csc -nullable:enable -out:ex.dll cs21b-form.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
문자열 5자
목록 1..3
큰 주문
없음
```

- ★★★ **`null` 팔을 맨 위에** — 뒤의 타입·속성 패턴은 **어차피 null 에 안 맞는다**((1)). 명시하면 뜻이 드러난다.
- ★★ **좁은 것 먼저**(`string { Length: 0 }` → `string s`) — 뒤집으면 앞 팔이 뒤 팔을 가려 **컴파일 에러**다(22번 주제의 `CS8510`).
- ★★ **타입 뒤에 목록 패턴을 바로 못 붙인다** — `o is List<int> [1, ..]` 는 **배열 타입 선언으로 읽혀 `CS0270`**((5)의 둘째 소스)이라 **`List<int> and [ … ]`** 로 적었다.
- ★★ **`Order(var q, _)`** — 위치 패턴은 **`Deconstruct` 를 부른다**. record 는 그것을 **생성해 준다**([18번](../18-record-value-equality-and-with/) (1)).
- ★ **속성 패턴 안의 속성은 부작용이 없어야** 한다((4)).

### 금지 사례 — 진단이 나는 꼴

| 쓴 꼴 | 진단 코드 | 어디서 |
|---|---|---|
| `IEnumerable<T>` 에 목록 패턴 | `CS8985` | (5) |
| `Count` 만 있고 인덱서가 없는 타입에 목록 패턴 | `CS0021` | (5) |
| 슬라이스 `..` 를 두 번 | `CS8980` | (5) |
| 타입 바로 뒤에 목록 패턴(`List<int> [1, ..]`) | `CS0270` — 배열 타입으로 읽힌다 | (5) |
| 선언 안 된 이름 하나를 패턴에 | `CS0103` — ★ 캡처가 아니다 | (8) |
| 판이 낮은데 새 패턴 | `CS8370`(7.3)·`CS8400`(8)·`CS8773`(9)·`CS8936`(10) | (7) |
| ★★★ `x != null` 을 연산자 오버로드 타입에 | ★★★ **진단 없음** — 연산자가 불린다 | (3) |

## 어디서 틀리나

1. ★★★ **「`is not null` 과 `!= null` 은 같다」** — **`!= null` 은 오버로드된 연산자를 부른다**((3)). `none == null` 이 `False` 인 타입이 실제로 있을 수 있다.
2. ★★★ **「패턴은 getter 를 한 번만 부른다」** — **이 판의 관찰**이다. 명세는 **순서를 안 정한다**((4)).
3. ★★★ **「목록 패턴은 `IEnumerable` 에 된다」** — **`CS8985`**. 길이와 인덱서가 필요하다((5)).
4. ★★★ **「목록 패턴은 할당이 없다」** — **`.. var rest` 를 배열·문자열에 쓰면 할당**한다((6)). `Span` 이면 0.
5. ★★ **「`IList` 를 구현해야 목록 패턴이 붙는다」** — **`Length` + `this[int]` 만 있으면** 된다((2) `Bag`).
6. ★★ **「`o is string s` 는 캐스트를 두 번 한다」** — **`isinst` 한 번**이다((1)).
7. ★★ **「`case limit:` 은 값을 `limit` 에 받는다」** — C# 에서는 **`CS0103`**((8)). Python 과 반대다.
8. ★ **「`not >= 'a' and <= 'z'` 는 범위의 부정이다」** — `not` 이 먼저 묶인다. **괄호**가 필요하다((1)).
9. ★ **「`switch` 식은 C# 8 이니 `Box =>` 도 8 이다」** — 타입만 적는 팔은 **9**((7)).

## 구현 세부사항 대 언어 보장

| 무엇 | 층 | 근거 |
|---|---|---|
| **선언·타입 패턴은 null 에 안 맞는다** | ★★★ **언어 보장(334)** · Learn | (1)(3) |
| **`is null` 이 사용자 `==` 를 안 부른다** | ★★★ **언어 보장** — Learn 「컴파일러가 보장」 | (3) |
| **목록 패턴의 요구(길이 속성 + 인덱서)** | ★★★ **언어 보장(C# 11 명세)** | (2)(5) |
| **같은 결합 순서의 패턴을 검사하는 순서** | ★★★ **정해지지 않음(명세)** | (4) |
| **getter·`Deconstruct` 가 1회 불리는 것** | ★ **Roslyn 구현**(결정 DAG) | (4) |
| **`isinst`+`stloc` · `cgt.un` · `GetSubArray` 라는 IL 모양** | ★★ **Roslyn 구현** | (1)(2)(3) |
| **배열 슬라이스가 복사, `Span` 슬라이스가 뷰** | ★★ **BCL 타입의 범위 연산**(09번) | (6) |
| **판 경계(7.3/8/9/10/11)** | ★★★ **언어 판** — 진단으로 확인 | (7) |

## 언제 쓰고 언제 안 쓰나

- ★★★ **null 검사는 `is null`/`is not null`** — 오버로드된 `==` 에 뜻을 안 맡긴다((3)).
- ★★★ **「검사 + 캐스트」는 `is T x` 한 줄로** — 두 번 캐스트할 이유가 없다((1)).
- ★★ **범위는 관계 패턴 `>= a and < b`** — `x` 가 **비싼 식**이면 특히 그렇다(한 번 평가한다).
- ★★ **목록 패턴의 `.. var rest` 는 뜨거운 경로에서 `Span` 으로** — 배열·문자열이면 매번 새로 만든다((6)).
- ★★ **속성 패턴에는 부작용 없는 속성만** — 호출 횟수는 약속이 아니다((4)).
- ★ **분기가 셋을 넘으면 `switch` 식으로** — 완전성 검사가 붙는다(22번 주제).

## 핵심 문장

1. ★★★ **패턴은 새 기계가 아니다** — `isinst`·비교·`ldlen`/`get_Count`·인덱서 호출로 풀린다((1)(2)).
2. ★★★ **`is not null` 은 연산자를 안 부르고 `!= null` 은 부른다** — 로그 2줄이 `[3]`·`[4]` 의 것뿐이다((3)).
3. ★★★ **목록 패턴은 `Length`/`Count` + `this[int]` 를 요구한다** — `IEnumerable` 은 `CS8985`, 인터페이스는 안 본다((2)(5)).
4. ★★ **getter 1회는 관찰이고 보장이 아니다** — 명세는 검사 순서를 정하지 않는다((4)).
5. ★★ **슬라이스를 받으면 배열·문자열은 할당, `Span` 은 0** — 네 판에서 갈린 줄 0 / 5((6)).

## 관련 자료

- 목록의 **22번 주제**(`switch` 식과 `switch` 문) — **완전성 검사·팔 순서(`CS8510`)** 의 정본. **경계**: 여기는 패턴 하나의 IL, 거기는 **팔 여럿의 집합**.
- [14번 — 인덱서](../14-indexers/) (5) — **패턴 기반 인덱싱**의 정본. 목록 패턴이 같은 규칙으로 풀린다((2)).
- [09번 — 배열·인덱스·범위](../09-arrays-index-and-range/) (3) — **배열 `..` 은 복사, `Span` 은 뷰**((6)).
- [18번 — record](../18-record-value-equality-and-with/) — 위치 패턴이 부르는 **`Deconstruct` 를 생성**한다.
- [19번 — 동등성](../19-equality-equals-gethashcode-operator/) (3) — **`==` 는 정적 타입이 고른다** · (3)의 `!= null` 이 그 연산자를 부른다.
- [07번 — 널 연산자](../07-null-operators/) — 「패턴 매칭과의 경계」로 `is null` 을 이 주제에 넘겼다.
- Java 갈래 목록([`java/syntax/README.md`](../../../java/syntax/README.md))의 **22번**([`22-instanceof-type-patterns/`](../../../java/syntax/22-instanceof-type-patterns/))·**24번**([`24-record-patterns/`](../../../java/syntax/24-record-patterns/)) — **경계**: Java 패턴의 흐름 스코프·레코드 패턴 중첩은 거기.
- Kotlin 갈래 목록([`kotlin/syntax/README.md`](../../../kotlin/syntax/README.md))의 **33번**([`33-type-checks-and-casts-is-as/`](../../../kotlin/syntax/33-type-checks-and-casts-is-as/)) — **스마트 캐스트**.
- Python 갈래 목록([`python/syntax/README.md`](../../../python/syntax/README.md))의 **39번**([`39-match-statement/`](../../../python/syntax/39-match-statement/)) — **캡처 패턴**.

## 용어 풀이

- **패턴(pattern)** — 값이 어떤 **모양**인지 검사하고, 맞으면 부분을 **꺼내** 이름을 붙이는 문법. `is`·`switch` 식·`switch` 문에서 쓴다.
- **선언 패턴** — `T x`. 타입이 맞고 **null 이 아니면** 맞고, 값을 `x` 에 담는다.
- **관계 패턴** — `< 3`·`>= 0` 처럼 **상수와 비교**하는 패턴(C# 9).
- **속성 패턴** — `{ Len: > 3 }`. **null 이 아니고** 속성마다 안쪽 패턴이 맞으면 맞는다.
- **목록 패턴 · 슬라이스 패턴** — `[1, .., var last]` · 그 안의 `..`(0개 이상). C# 11.
- **`isinst`** — IL 의 「이 타입으로 캐스트해 보고, 안 되면 null」 명령.
- **결정 DAG** — 여러 패턴을 **한 번 읽은 값을 공유하는 분기 그래프**로 합친 것. Roslyn 이 쓰는 방식이고 명세가 아니다.
- **스마트 캐스트** — Kotlin 에서 검사 뒤 **같은 변수**가 좁은 타입으로 보이는 것.

## 더 들어가면

- ★ **결정 DAG 가 getter 를 두 번 읽게 되는 자리** — `when` 절 사이에 끼면 다시 읽을 수 있다고 알려져 있으나 **이 판에서 안 던졌다.**
- ★ **목록 패턴의 완전성** — 22번 주제의 완전성 격자가 `[] / [_]` 만 적은 배열에 `CS8509`(`{ Length: 2 }`)를 냈다. Learn 은 「목록 패턴은 경고를 안 낸다」고 적어 **실측과 다르다** — 거기서 다룬다.
- ★ **`Span<char>` 을 문자열 상수 패턴과 맞추는 것**(Learn 이 언급) — **이 판에서 안 던졌다.**
