# csharp/syntax/27 — 델리게이트와 `Func`/`Action` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·진단·IL·할당 바이트는 **.NET SDK 10.0.401** · 런타임 **10.0.12** · 타겟 **`net10.0`** ·
> **linux-x64** 에서 실제로 돌려 얻은 것이다(2026-09-26). 대비는 **javac 21.0.5** 다.\
> 진단은 **`-preferreduilang:en-US`** 로 영어로 고정했다.\
> ★ 블록은 캡처 스크립트가 파일로 받아 조립기가 끼워 넣은 것이다 — 손으로 옮긴 줄은 없다.\
> ★ 진단을 싣는 블록은 전부 **그 진단을 낸 소스를 같은 블록 안에** 다시 싣는다(`===== 소스: … =====`).
> **읽는 법** — 근거로 쓰는 것은 **리플렉션 결과 · 진단 코드 · 옵코드 · 실행 로그의 순서 · 스크립트가 센 줄 수** 다.
> ★★★ **이 문서는 시간을 재지 않았다.** 「델리게이트가 느리다/빠르다」는 문장이 **한 줄도 없다.**

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ 둘 다 **`MulticastDelegate` 를 상속한 봉인 클래스** — 그래도 **다른 타입**

**출력**

```text
===== 소스: cs27b-refl.cs =====
using System;
using System.Linq;
using System.Reflection;
delegate int Op(int x);
class Program {
    static string Members(Type t) => string.Join(" ", t.GetMethods(BindingFlags.Public | BindingFlags.Instance | BindingFlags.DeclaredOnly).Select(m => m.Name).OrderBy(n => n, StringComparer.Ordinal))
        + " | ctor(" + string.Join(",", t.GetConstructors()[0].GetParameters().Select(p => p.ParameterType.Name)) + ")";
    static void Main() {
        foreach (var t in new[] { typeof(Op), typeof(Func<int, int>) }) {
            Console.WriteLine($"[A] {t.Name,-8} IsClass={t.IsClass} IsSealed={t.IsSealed} BaseType={t.BaseType!.FullName}");
            Console.WriteLine($"    선언한 공개 메서드 : {Members(t)}");
            var inv = t.GetMethod("Invoke")!;
            Console.WriteLine($"    Invoke 서명 : {inv.ReturnType.Name} Invoke({string.Join(",", inv.GetParameters().Select(p => p.ParameterType.Name))})");
        }
        Console.WriteLine($"[B] typeof(Op) == typeof(Func<int,int>) : {typeof(Op) == typeof(Func<int, int>)}");
        Console.WriteLine($"[C] Func<int,int> 를 Op 자리에 넣을 수 있나(IsAssignableFrom) : {typeof(Op).IsAssignableFrom(typeof(Func<int, int>))}");
        Op op = x => x + 1;
        Console.WriteLine($"[D] op.Method.Name = {op.Method.Name} · op.Target 의 타입 = {op.Target?.GetType().Name}");
    }
}
===== csc -out:ex.dll cs27b-refl.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
[A] Op       IsClass=True IsSealed=True BaseType=System.MulticastDelegate
    선언한 공개 메서드 : BeginInvoke EndInvoke Invoke | ctor(Object,IntPtr)
    Invoke 서명 : Int32 Invoke(Int32)
[A] Func`2   IsClass=True IsSealed=True BaseType=System.MulticastDelegate
    선언한 공개 메서드 : BeginInvoke EndInvoke Invoke | ctor(Object,IntPtr)
    Invoke 서명 : Int32 Invoke(Int32)
[B] typeof(Op) == typeof(Func<int,int>) : False
[C] Func<int,int> 를 Op 자리에 넣을 수 있나(IsAssignableFrom) : False
[D] op.Method.Name = <Main>b__1_0 · op.Target 의 타입 = <>c
```

**왜 그런가**

- ★★★ **`[A]` 두 줄이 똑같다** — `IsClass=True IsSealed=True BaseType=System.MulticastDelegate` · 메서드 `BeginInvoke EndInvoke Invoke` · 생성자 `(Object, IntPtr)`(대상 + 메서드 포인터) · `Int32 Invoke(Int32)`.
- ★★★ **`[B]` `False` · `[C]` `False`** — 서명이 같아도 **다른 클래스**이고 상속 관계가 없다.
- ★★ **`[D]` `Target` 은 `<>c`** — 캡처 없는 람다는 컴파일러가 만든 싱글턴의 메서드(`<Main>b__1_0`)가 된다([28번](../28-lambdas-and-closure-capture/)).

### 2. ★★★ **`CS0029` · `CS0030`** — 건너가려면 **`f.Invoke` · `new Op(f)`**(대상이 `f`)

**출력**

```text
===== 소스: cs27b-type.cs =====
using System;
delegate int Op(int x);
class Program {
    static void Main() {
        Func<int, int> f = x => x * 10;
        Op a = f;
        Op b = (Op)f;
    }
}
===== csc -out:ex.dll cs27b-type.cs 2>&1 | sort (cc exit=1) =====
cs27b-type.cs(6,16): error CS0029: Cannot implicitly convert type 'System.Func<int, int>' to 'Op'
cs27b-type.cs(7,16): error CS0030: Cannot convert type 'System.Func<int, int>' to 'Op'
```

```text
===== 소스: cs27b-bridge.cs =====
using System;
delegate int Op(int x);
class Program {
    static void Main() {
        Func<int, int> f = x => x * 10;
        Op a = f.Invoke;
        Op b = new Op(f);
        Console.WriteLine($"[1] a(2) = {a(2)} · b(2) = {b(2)}");
        Console.WriteLine($"[2] a.Method.Name = {a.Method.Name} · a.Target 의 타입 = {a.Target?.GetType().Name}");
        Console.WriteLine($"[3] b.Method.Name = {b.Method.Name} · b.Target 의 타입 = {b.Target?.GetType().Name}");
        Console.WriteLine($"[4] ReferenceEquals(a.Target, f) = {ReferenceEquals(a.Target, f)}");
    }
}
===== csc -out:ex.dll cs27b-bridge.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
[1] a(2) = 20 · b(2) = 20
[2] a.Method.Name = Invoke · a.Target 의 타입 = Func`2
[3] b.Method.Name = Invoke · b.Target 의 타입 = Func`2
[4] ReferenceEquals(a.Target, f) = True
```

**왜 그런가**

- ★★★ **`Op a = f;` 는 `CS0029`, `(Op)f` 는 `CS0030`** — 두 클래스 사이에 **변환이 아예 없다**(인터페이스 사이의 `CS0266` 과 다르다 — [26번](../26-covariance-and-contravariance-out-in/)).
- ★★★ **`[2]`·`[3]` `Method.Name = Invoke` · ``Target = Func`2``** · **`[4]` `True`** — 새 `Op` 가 **`f` 를 대상으로 `Func.Invoke` 를 가리킨다.** 한 단계 감싼 것이다.

### 3. ★★★ 반환값 **`3`** · `Boom` 뒤 **`C` 는 안 불림** · `-=` 는 **마지막 일치**

**출력**

```text
===== 소스: cs27b-multi.cs =====
using System;
class Program {
    static int A() { Console.WriteLine("  A 실행"); return 1; }
    static int B() { Console.WriteLine("  B 실행"); return 2; }
    static int C() { Console.WriteLine("  C 실행"); return 3; }
    static int Boom() { Console.WriteLine("  Boom 실행"); throw new InvalidOperationException("boom"); }
    static string Names(Delegate? d) => d is null ? "(null)" : string.Join(",", Array.ConvertAll(d.GetInvocationList(), x => x.Method.Name));
    static void Main() {
        Func<int> f = A; f += B; f += C;
        Console.WriteLine($"[1] 호출 목록 : {Names(f)}");
        int r = f();
        Console.WriteLine($"[2] f() 의 반환값 : {r}");
        Func<int> g = A; g += Boom; g += C;
        Console.WriteLine($"[3] 호출 목록 : {Names(g)}");
        try { g(); } catch (Exception e) { Console.WriteLine($"[4] g() → {e.GetType().Name}: {e.Message}"); }
        Func<int> h = A; h += B; h += A;
        Console.WriteLine($"[5] 떼기 전 : {Names(h)}");
        h -= A;
        Console.WriteLine($"[6] h -= A 뒤 : {Names(h)}");
        Func<int> k = A; k += B; k += C;
        Func<int> bc = B; bc += C;
        Func<int> ac = A; ac += C;
        Console.WriteLine($"[7] (A,B,C) -= (B,C) : {Names(k - bc)}");
        Console.WriteLine($"[8] (A,B,C) -= (A,C) : {Names(k - ac)}");
        Func<int> one = A; one -= A;
        Console.WriteLine($"[9] A -= A : {Names(one)}");
    }
}
===== csc -nullable:enable -out:ex.dll cs27b-multi.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
cs27b-multi.cs(18,9): warning CS8601: Possible null reference assignment.
cs27b-multi.cs(25,28): warning CS8601: Possible null reference assignment.
[1] 호출 목록 : A,B,C
  A 실행
  B 실행
  C 실행
[2] f() 의 반환값 : 3
[3] 호출 목록 : A,Boom,C
  A 실행
  Boom 실행
[4] g() → InvalidOperationException: boom
[5] 떼기 전 : A,B,A
[6] h -= A 뒤 : A,B
[7] (A,B,C) -= (B,C) : A
[8] (A,B,C) -= (A,C) : A,B,C
[9] A -= A : (null)
```

**왜 그런가**

- ★★★ **`[2]` `3`** — 마지막 것의 반환값만 남는다. **`[3]`\~`[4]` `A 실행`·`Boom 실행` 뒤 `C 실행` 이 없다** — 예외가 목록을 끊었다.
- ★★★ **`[6]` `A,B`**(끝의 `A` 를 뗐다) · **`[7]` `A`**(연속 부분 목록 `B,C` 일치) · **`[8]` `A,B,C`**(`A,C` 는 연속이 아니다) · **`[9]` `(null)`**.
- ★ **`CS8601` 경고 두 줄** — 18행 `h -= A` 와 25행 `one -= A`. `-=` 결과가 **`null` 일 수 있어서**다.

### 4. ★★★ **`Static()` 만** 달라진다 — 11 판은 **`<>O` 캐시**

**출력**

```text
===== 소스: cs27b-il.cs =====
using System;
public class P {
    static int Twice(int x) => x * 2;
    int Inc(int x) => x + 1;
    public static Func<int, int> Static() => Twice;
    public Func<int, int> Instance() => Inc;
    public static Func<int, int> Lambda() => x => x * 2;
    public static int Call(Func<int, int> f) => f(3);
}
class Program {
    static void Main() {
        foreach (var n in new[] { "Static", "Instance", "Lambda", "Call" }) Il.Dump(typeof(P), n);
    }
}
===== csc -langversion:10 -optimize -r:il.dll -out:exo.dll cs27b-il.cs && dotnet exo.dll (cc exit=0 · run exit=0) =====
--- P.Static ---
  IL_0000: ldnull
  IL_0001: ldftn P::Twice
  IL_0007: newobj System.Func<System.Int32,System.Int32>::.ctor
  IL_000c: ret
--- P.Instance ---
  IL_0000: ldarg.0
  IL_0001: ldftn P::Inc
  IL_0007: newobj System.Func<System.Int32,System.Int32>::.ctor
  IL_000c: ret
--- P.Lambda ---
  IL_0000: ldsfld P+<>c::<>9__4_0
  IL_0005: dup
  IL_0006: brtrue.s IL_001f
  IL_0008: pop
  IL_0009: ldsfld P+<>c::<>9
  IL_000e: ldftn P+<>c::<Lambda>b__4_0
  IL_0014: newobj System.Func<System.Int32,System.Int32>::.ctor
  IL_0019: dup
  IL_001a: stsfld P+<>c::<>9__4_0
  IL_001f: ret
--- P.Call ---
  IL_0000: ldarg.0
  IL_0001: ldc.i4.3
  IL_0002: callvirt System.Func<System.Int32,System.Int32>::Invoke
  IL_0007: ret
===== csc -langversion:11 -optimize -r:il.dll -out:exo.dll cs27b-il.cs && dotnet exo.dll (cc exit=0 · run exit=0) =====
--- P.Static ---
  IL_0000: ldsfld P+<>O::<0>__Twice
  IL_0005: dup
  IL_0006: brtrue.s IL_001b
  IL_0008: pop
  IL_0009: ldnull
  IL_000a: ldftn P::Twice
  IL_0010: newobj System.Func<System.Int32,System.Int32>::.ctor
  IL_0015: dup
  IL_0016: stsfld P+<>O::<0>__Twice
  IL_001b: ret
--- P.Instance ---
  IL_0000: ldarg.0
  IL_0001: ldftn P::Inc
  IL_0007: newobj System.Func<System.Int32,System.Int32>::.ctor
  IL_000c: ret
--- P.Lambda ---
  IL_0000: ldsfld P+<>c::<>9__4_0
  IL_0005: dup
  IL_0006: brtrue.s IL_001f
  IL_0008: pop
  IL_0009: ldsfld P+<>c::<>9
  IL_000e: ldftn P+<>c::<Lambda>b__4_0
  IL_0014: newobj System.Func<System.Int32,System.Int32>::.ctor
  IL_0019: dup
  IL_001a: stsfld P+<>c::<>9__4_0
  IL_001f: ret
--- P.Call ---
  IL_0000: ldarg.0
  IL_0001: ldc.i4.3
  IL_0002: callvirt System.Func<System.Int32,System.Int32>::Invoke
  IL_0007: ret
```

**왜 그런가**

- ★★★ **10 판 `Static()` 은 `ldnull` · `ldftn` · `newobj`**(매번 새로), **11 판은 `ldsfld <>O::<0>__Twice` → 비었을 때만 `newobj` → `stsfld`**(한 번만).
- ★★ **`Instance()` 는 대상이 `this`(`ldarg.0`)** — 대상이 호출마다 다를 수 있어 **정적 필드 하나에 캐시할 수 없다.** `Lambda()` 는 **두 판 다 `<>c` 캐시**, `Call()` 은 두 판 다 **`callvirt Func::Invoke`**.

### 5. ★★★ **10 판 64000 · 0 · 64000 · `False`** → **11 판 0 · 0 · 64000 · `True`**

**출력**

```text
===== 소스: cs27b-alloc.cs =====
using System;
class Program {
    static int Twice(int x) => x * 2;
    int Inc(int x) => x + 1;
    static int Use(Func<int, int> f) => f(1);
    static long M(Action a) {
        for (int i = 0; i < 200; i++) a();
        var b = GC.GetAllocatedBytesForCurrentThread();
        a();
        return GC.GetAllocatedBytesForCurrentThread() - b;
    }
    static void Main() {
        var p = new Program();
        long sink = 0;
        Console.WriteLine($"[1] Use(Twice)       정적 메서드 그룹     1000번 : {M(() => { for (int i = 0; i < 1000; i++) sink += Use(Twice); })} 바이트");
        Console.WriteLine($"[2] Use(x => x * 2)  캡처 없는 람다       1000번 : {M(() => { for (int i = 0; i < 1000; i++) sink += Use(x => x * 2); })} 바이트");
        Console.WriteLine($"[3] Use(p.Inc)       인스턴스 메서드 그룹 1000번 : {M(() => { for (int i = 0; i < 1000; i++) sink += Use(p.Inc); })} 바이트");
        Func<int, int> x1 = Twice, x2 = Twice;
        Console.WriteLine($"[4] Twice 를 두 번 변환한 두 델리게이트 ReferenceEquals : {ReferenceEquals(x1, x2)}");
        GC.KeepAlive(sink);
    }
}
===== csc -langversion:10 -out:ex.dll cs27b-alloc.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
[1] Use(Twice)       정적 메서드 그룹     1000번 : 64000 바이트
[2] Use(x => x * 2)  캡처 없는 람다       1000번 : 0 바이트
[3] Use(p.Inc)       인스턴스 메서드 그룹 1000번 : 64000 바이트
[4] Twice 를 두 번 변환한 두 델리게이트 ReferenceEquals : False
===== csc -langversion:10 -out:ex.dll cs27b-alloc.cs && DOTNET_TieredCompilation=0 dotnet ex.dll (cc exit=0 · run exit=0) =====
[1] Use(Twice)       정적 메서드 그룹     1000번 : 64000 바이트
[2] Use(x => x * 2)  캡처 없는 람다       1000번 : 0 바이트
[3] Use(p.Inc)       인스턴스 메서드 그룹 1000번 : 64000 바이트
[4] Twice 를 두 번 변환한 두 델리게이트 ReferenceEquals : False
===== csc -langversion:10 -optimize -out:exo.dll cs27b-alloc.cs && dotnet exo.dll (cc exit=0 · run exit=0) =====
[1] Use(Twice)       정적 메서드 그룹     1000번 : 64000 바이트
[2] Use(x => x * 2)  캡처 없는 람다       1000번 : 0 바이트
[3] Use(p.Inc)       인스턴스 메서드 그룹 1000번 : 64000 바이트
[4] Twice 를 두 번 변환한 두 델리게이트 ReferenceEquals : False
===== csc -langversion:10 -optimize -out:exo.dll cs27b-alloc.cs && DOTNET_TieredCompilation=0 dotnet exo.dll (cc exit=0 · run exit=0) =====
[1] Use(Twice)       정적 메서드 그룹     1000번 : 64000 바이트
[2] Use(x => x * 2)  캡처 없는 람다       1000번 : 0 바이트
[3] Use(p.Inc)       인스턴스 메서드 그룹 1000번 : 64000 바이트
[4] Twice 를 두 번 변환한 두 델리게이트 ReferenceEquals : False
===== csc -langversion:11 -out:ex.dll cs27b-alloc.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
[1] Use(Twice)       정적 메서드 그룹     1000번 : 0 바이트
[2] Use(x => x * 2)  캡처 없는 람다       1000번 : 0 바이트
[3] Use(p.Inc)       인스턴스 메서드 그룹 1000번 : 64000 바이트
[4] Twice 를 두 번 변환한 두 델리게이트 ReferenceEquals : True
===== csc -langversion:11 -out:ex.dll cs27b-alloc.cs && DOTNET_TieredCompilation=0 dotnet ex.dll (cc exit=0 · run exit=0) =====
[1] Use(Twice)       정적 메서드 그룹     1000번 : 0 바이트
[2] Use(x => x * 2)  캡처 없는 람다       1000번 : 0 바이트
[3] Use(p.Inc)       인스턴스 메서드 그룹 1000번 : 64000 바이트
[4] Twice 를 두 번 변환한 두 델리게이트 ReferenceEquals : True
===== csc -langversion:11 -optimize -out:exo.dll cs27b-alloc.cs && dotnet exo.dll (cc exit=0 · run exit=0) =====
[1] Use(Twice)       정적 메서드 그룹     1000번 : 0 바이트
[2] Use(x => x * 2)  캡처 없는 람다       1000번 : 0 바이트
[3] Use(p.Inc)       인스턴스 메서드 그룹 1000번 : 64000 바이트
[4] Twice 를 두 번 변환한 두 델리게이트 ReferenceEquals : True
===== csc -langversion:11 -optimize -out:exo.dll cs27b-alloc.cs && DOTNET_TieredCompilation=0 dotnet exo.dll (cc exit=0 · run exit=0) =====
[1] Use(Twice)       정적 메서드 그룹     1000번 : 0 바이트
[2] Use(x => x * 2)  캡처 없는 람다       1000번 : 0 바이트
[3] Use(p.Inc)       인스턴스 메서드 그룹 1000번 : 64000 바이트
[4] Twice 를 두 번 변환한 두 델리게이트 ReferenceEquals : True
===== 대조 — 줄마다 (가) 같은 판 안의 네 판이 같은가 (나) 10 판과 11 판이 같은가 =====
(가) 같은 판 안에서 네 판이 갈린 줄 0 / 4
(나) 10 판과 11 판이 갈린 줄 2 / 4
```

**왜 그런가**

- ★★★ **(나) 10 판과 11 판이 갈린 줄 2 / 4** — `[1]` 정적 메서드 그룹과 `[4]` `ReferenceEquals`. **`[2]` 람다 0 · `[3]` 인스턴스 메서드 그룹 64000 은 두 판이 같다.**
- ★★★ **(가) 같은 판 안에서 갈린 줄 0 / 4** — 최적화·티어링이 바꾸는 자리가 아니다. **IL 이 바뀐 것**이다(4번).

### 6. ★★ javac **`incompatible types`** · 건너가기는 **`f::apply`** · 다른 자리는 **만드는 방식과 멀티캐스트**

- ★★ **`Op a = f;` → `incompatible types: Function<Integer,Integer> cannot be converted to Op`** — Java 함수형 인터페이스도 **이름이 곧 타입**(요약 (3)).
- ★★ **`Op a = f::apply;`** 가 통과하고 `a.apply(2) = 20` — C# `f.Invoke` 와 같다. `a.getClass() == f.getClass()` 는 `false`.
- ★ **다른 자리** — C# 람다는 **컴파일 시점에 클래스(`<>c`)와 캐시 필드**가 생기고, Java 는 **실행 시점 `invokedynamic`** 으로 만든다([Java 29번](../../../java/syntax/29-lambda-expressions/) (2)). **C# 은 `+=` 멀티캐스트가 있고 Java 는 없다.**

### 7. ★★★ **Roslyn 의 코드 생성**이다 — IL 이 바뀌었고, 네 판(JIT 조건)이 같다

- ★★★ **가리는 법** — ① 4번에서 **같은 컴파일러의 IL 이 판 하나로 갈렸다**(`<>O` 캐시) ② 5번 **(가) 0 / 4**(JIT 최적화·티어링과 무관). 언어 **문법**은 그대로라 명세의 변화가 아니라 **언어 판이 켜는 코드 생성**이다.
- ★★ **깨질 수 있는 코드** — 「두 번 변환한 델리게이트는 **다른 객체**」에 기대는 것(동일성 비교 · 델리게이트를 키로 쓰는 사전 · 참조 동일성으로 구독 여부를 가리는 것). `[4]` 가 `False` → `True` 로 바뀌었다.

### 8. ★★ **앞의 반환값이 조용히 버려진다** — `GetInvocationList()` 를 직접 돌아라

- ★★ 3번 `[2]` — `A`·`B` 의 `1`·`2` 는 **어디에도 안 남는다.**
- ★ **목록을 돌며 각각 `Invoke` + `try`** 하면 모든 반환값을 모으고, 하나가 던져도 나머지를 부를 수 있다.

### 9. ★ 내 델리게이트로 받으면 **호출자의 `Func` 가 `CS0029` 에 막힌다**

- ★ 호출자는 `f.Invoke`/`new Op(f)` 로 **감싸야** 한다(2번). `Func<int,int>` 로 받으면 **람다·메서드 그룹·기존 `Func` 를 그대로** 넘긴다.

### 10. 잇기

- ★★ **람다의 캡처와 생성 클래스** — [28번](../28-lambdas-and-closure-capture/).
- ★ **`event`** — 목록의 **29번 주제**.

## 실행 검증

| 무엇 | 몇 번·어디서 | 결과 |
|---|---|---|
| `cs27b-refl.cs` | csc 1회 · 실행 1회 | ★★★ 봉인 클래스 · `MulticastDelegate` · `typeof` 다름 |
| `cs27b-type.cs` | csc 1회 | `CS0029` · `CS0030` |
| `cs27b-bridge.cs` | csc 1회 · 실행 1회 | `Invoke` · ``Func`2`` 대상 |
| `G27.java` · `Ex27.java` | javac 2회 · java 1회 | `incompatible types` · `f::apply` 통과 |
| `cs27b-multi.cs` | csc 1회 · 실행 1회 | ★★★ 반환값 3 · `C` 안 불림 · `-=` 규칙 · `CS8601` ×2 |
| `cs27b-il.cs` | csc 2회(`10` · `11`, `-optimize`) · 실행 2회 | ★★★ `Static()` 만 갈림(`<>O` 캐시) |
| `cs27b-alloc.cs` | **판 둘 × 2×2 = 8판** | ★★★ **같은 판 안 0 / 4 · 판 사이 2 / 4** |
| `cs27b-form.cs` | csc 1회 · 실행 1회 | `<hi>[2]` · `5 · True · ABC · 1,4,9` |

**구현 의존 항목** — 다음은 **이 판(.NET SDK 10.0.401 · 런타임 10.0.12 · javac 21.0.5)에서만** 그렇다.

- ★★★ **캐시 필드의 모양과 이름**(`<>c` · `<>O::<0>__Twice`) — Roslyn · ★ **델리게이트 64바이트** · 진단 문구.

**언어·CLI 가 보장하는 것**(구현이 바뀌어도 같다)

- **델리게이트 = 봉인 클래스 · 이름이 다르면 다른 타입**(ECMA-335/334) · **멀티캐스트 순서·마지막 반환값·예외에서 끊김 · `-=` 규칙**.

**안 돌려 본 것 / 못 잰 것 / 잴 것이 없는 것**

- **안 돌려 본 것** — ★ `BeginInvoke` · 함수 포인터 `delegate*` · 변성 델리게이트의 결합 · 제네릭 정적 메서드 그룹의 캐시.
- **못 잰 것** — ★★★ **시간**.
- **잴 것이 없는 것** — 없다.

**버전이 올랐을 때 다시 돌려야 하는 것**

- ★★★ **4·5번** — 캐시 정책은 Roslyn 이다. **인스턴스 메서드 그룹까지 캐시하게 되면 `[3]` 이 움직인다.**
