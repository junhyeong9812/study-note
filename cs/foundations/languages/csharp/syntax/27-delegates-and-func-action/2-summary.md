# csharp/syntax/27 — 델리게이트와 `Func`/`Action` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [ECMA-335(CLI) 6판](https://ecma-international.org/publications-and-standards/standards/ecma-335/) · [ECMA-334 7판(2023-12)](https://ecma-international.org/publications-and-standards/standards/ecma-334/) ·
> [Learn — 람다 식](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/operators/lambda-expressions)(열어서 확인: 「람다는 **델리게이트 타입으로 변환**된다 — 값을 안 돌려주면 `Action`, 돌려주면 `Func`」 · 「오버로드가 **하나뿐인 메서드 그룹**은 자연 타입이 있다」) ·
> [Learn — C# 버전 이력](https://learn.microsoft.com/en-us/dotnet/csharp/whats-new/csharp-version-history)(열어서 확인: C# 1.0 「**Delegates**」 · 2.0 「**Method group conversions (delegates)**」·「Anonymous methods」 · 11 「**Improved method group conversion to delegate**」) ·
> [Learn — 제네릭의 공변성과 반공변성](https://learn.microsoft.com/en-us/dotnet/standard/generics/covariance-and-contravariance)(열어서 확인: 「`Func` 는 반환이 공변·인자가 반변」 · 「**델리게이트는 타입이 정확히 같아야 결합된다**」).
> **실행 검증** — 이 문서의 모든 출력·진단·IL·할당 바이트는 아래 「이 판」의 도구로 **실제로 돌려 얻은 것**이다(2026-09-26).\
> ★ 블록은 캡처 스크립트가 파일로 받아 조립기가 끼워 넣은 것이다 — 사람이 옮겨 적은 줄은 하나도 없다. **대비는 실측이다** — **javac 21.0.5** 로 함수형 인터페이스 한 쌍을 던졌다((3)).
> **버전** — 델리게이트 **C# 1** · 메서드 그룹 변환·익명 메서드 **C# 2** · 람다 **C# 3** · ★★★ **정적 메서드 그룹의 델리게이트 캐시 C# 11** — **`-langversion:10` 대 `11` 판 격자 × 2×2 로 확정했다**((6)(7)).
> **경계** — ★★ **람다가 무엇을 캡처하나**는 [28번](../28-lambdas-and-closure-capture/)이 정본이다 — 여기서는 람다를 **「델리게이트 값을 만드는 한 방법」** 으로만 쓴다.\
> ★ **`event` 가 델리게이트 필드에 거는 제한**은 목록의 **29번 주제** · **변성**(`Func<in T, out TResult>`)은 [26번](../26-covariance-and-contravariance-out-in/) ·\
> ★★ **Java 쪽 정본** — 람다 = `invokedynamic` 은 [Java 29번](../../../java/syntax/29-lambda-expressions/) (2) · 함수형 인터페이스 지도는 [Java 31번](../../../java/syntax/31-functional-interfaces/) · Kotlin SAM 변환은 Kotlin 갈래 목록([`kotlin/syntax/README.md`](../../../kotlin/syntax/README.md))의 **36번**(폴더가 아직 없다).
> ★★★ **본체 창은 ③ 리플렉션이다** — 「델리게이트는 **타입**이다」는 **런타임에게 그 타입을 물어서** 보인다.
>
> ★★ **흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | 진단 **문구** · 진단 **순서**(배너에 `sort`) | ★★★ **진단 코드**(`CS0029` · `CS0030`) · javac `exit` |
> | **IL 오프셋 폭** · 컴파일러가 지은 이름(`<>9__4_0` · `<0>__Twice`) | ★★★ **옵코드**(`ldftn` · `newobj …::.ctor` · `ldsfld`·`stsfld` 캐시 · `callvirt …::Invoke`) |
> | 증분의 절댓값 일부(규칙 24) | ★★★ **「같은 판 안에서 갈린 줄 N / M」 · 「10 판과 11 판이 갈린 줄 N / M」** · 멀티캐스트 **실행 로그의 순서** |

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
| **CLI 명세(ECMA-335)** | ★★★ **실행 엔진이 약속한 것** | ★★★ 델리게이트는 **`System.MulticastDelegate` 를 상속한 봉인 클래스**이고 `Invoke` 를 가진다 · **이름이 다른 두 델리게이트 타입은 다른 타입** |
| **언어 명세(ECMA-334)** | C# 언어가 약속한 것 | 서명이 같아도 **델리게이트 타입 사이에 변환이 없다**(`CS0029`) · 멀티캐스트 호출 순서와 **반환값은 마지막 것** · `-=` 는 **끝에서부터 일치하는 목록**을 뗀다 |
| **컴파일러 구현(Roslyn)** | 그것을 **어떻게 적나** | ★★★ 메서드 그룹 변환 = `ldftn` + `newobj` · **캡처 없는 람다는 `<>c` 에 캐시** · ★★★ **C# 11 부터 정적 메서드 그룹도 `<>O` 에 캐시** |
| **이 판의 관찰** | .NET 10.0.12 · linux-x64 · javac 21.0.5 | 델리게이트 한 개 **64바이트** · 진단 문구 |

★★★ **이 주제의 층 구분 —**\
**「델리게이트는 타입이다」는 CLI 명세**다(봉인 클래스 · `Invoke`). **「정적 메서드 그룹은 한 번만 만든다」는 Roslyn 11 의 선택**이다 — 언어 판을 10 으로 내리면 **같은 컴파일러가 매번 새로 만든다.**

## 한눈에 — 쉽게 말하면

**델리게이트는 「이 서명의 일을 할 사람」을 적은 명함이다 — 그런데 명함은 회사마다 양식이 다르다.**

- **명함 양식 = 델리게이트 타입** — `Func<int,int>` 양식과 내가 만든 `Op` 양식은 **적힌 칸(서명)이 같아도 다른 양식**이다. 서로 **옮겨 적지 못한다**(`CS0029`).
- **옮기려면 새 명함에 「이 명함의 주인에게 전화」라고 적는다** — `new Op(f)` · `f.Invoke` → 새 델리게이트의 **대상이 원래 델리게이트**다.
- **명함 묶음 = 멀티캐스트** — `+=` 로 여럿을 묶으면 **차례로 전화**한다. 답은 **마지막 사람의 답만** 남고, 중간 사람이 **사고를 치면 뒤는 전화를 못 받는다.**
- **명함 인쇄 = 메서드 그룹 변환** — `Use(Twice)` 라고 쓸 때마다 **명함을 새로 찍던 것**(C# 10)이 **한 장 찍어 두고 재사용**(C# 11)으로 바뀌었다. 단 **인스턴스 메서드**(`p.Inc`)는 **누구 것인지 적어야 해서** 여전히 매번 찍는다.

| 비유 | 실체 | 어디서 보나 |
|---|---|---|
| 양식이 다르다 | ★★★ `Op`·`Func<int,int>` **둘 다 `MulticastDelegate` 를 상속한 봉인 클래스**, `Invoke` 서명도 같은데 **`typeof` 가 다르다** | (1) |
| 옮겨 적지 못한다 | ★★★ **`CS0029`**(대입) · **`CS0030`**(캐스트도) · Java 도 `incompatible types` | (2)(3) |
| 새 명함에 「전화」 | ★★ `f.Invoke` · `new Op(f)` → `Method.Name = Invoke` · ``Target = Func`2`` | (2) |
| 명함 묶음 | ★★★ 반환값 **`3`**(마지막) · `Boom` 뒤의 **`C` 가 안 불림** · `-=` 가 **마지막 `A`** 를 뗌 | (4) |
| 한 장 찍어 재사용 | ★★★ `Use(Twice)` 1000번 **C# 10: 64000 바이트 → C# 11: 0** · 인스턴스는 **둘 다 64000** | (6)(7) |

★★★ **이 주제의 본체 그림 — 델리게이트 한 개의 속.**

```text
   Func<int,int> f = Twice;          Op op = x => x + 1;
   ─────────────────────────         ──────────────────────────────
   ┌ Func`2 (sealed class) ┐         ┌ Op (sealed class) ────────┐
   │  _target  = null      │         │  _target  = <>c 싱글턴    │    ← 캡처 없는 람다의 대상
   │  _methodPtr = &Twice  │         │  _methodPtr = &<Main>b__1_0│
   │  Invoke(int) : int    │         │  Invoke(int) : int        │    ← 같은 서명
   └───────── base: MulticastDelegate ─────────────────────────────┘

   op = f;          ✕ CS0029   (서명이 같아도 다른 클래스)
   op = f.Invoke;   ○          (새 Op 를 만들고 _target = f, _methodPtr = &Func.Invoke)

   ★★★ 델리게이트 = 「대상 + 메서드 포인터」 를 든 봉인 클래스 — 타입 이름이 곧 정체다.
```

## 이 주제가 답하려는 질문

1. **델리게이트가 「타입」이라는 것은 무엇으로 보이나**((1)).
2. **서명이 같은 두 델리게이트 타입은 서로 대입되나** — Java 는((2)(3)).
3. **멀티캐스트의 반환값 · 중간 예외 · `-=`** 는 어떻게 되나((4)).
4. **메서드 그룹 변환은 매번 새 델리게이트를 만드나** — 판을 바꾸면((5)(6)(7)).

## 동작 방식

### (0) 이 주제가 쓰는 창

★★★ **본체 창은 ③ 리플렉션이다** — 「델리게이트는 클래스다」는 **런타임에게 물어서**만 보인다.

| 창 | 무엇을 보여 주나 | 이 주제에서 |
|---|---|---|
| ★★★ **③ 리플렉션** | ★★★ `IsClass`·`IsSealed`·`BaseType = MulticastDelegate` · 선언된 `Invoke` · **`typeof(Op) != typeof(Func<int,int>)`** · `Method`·`Target` · `GetInvocationList()` | (1)(2)(4) |
| ★★★ **① IL 덤프** | ★★★ **`ldftn` + `newobj Func::.ctor`** · 캡처 없는 람다의 **`<>c` 캐시** · ★★★ **C# 10 대 11 에서 `Static()` 의 IL 이 갈린다**(`<>O::<0>__Twice`) | (5) |
| ★★★ **④ 할당 바이트** | ★★★ **`-langversion:10` 대 `11` × 2×2 = 8판** — 정적 메서드 그룹 **64000 → 0** · 인스턴스 메서드 그룹은 **그대로** | (6) |
| ★★ **② 진단 격자** | ★★ `CS0029`·`CS0030` · Java `incompatible types` — 한 쌍 | (2)(3) |
| **부적용인 창** | 없다 — 네 창을 다 썼다 | — |

### (1) ★★★ 본체 — 델리게이트는 타입이다

**언제 쓰나** — 「`Func<int,int>` 와 내가 선언한 `delegate int Op(int)` 는 같은 것인가」.

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

- ★★★ **`[A]` 둘 다 `IsClass=True IsSealed=True BaseType=System.MulticastDelegate`** — 델리게이트 선언 한 줄이 **봉인 클래스 하나**가 된다. **`Func<int,int>` 도 BCL 에 선언된 그런 클래스일 뿐**이다.
- ★★★ **선언한 공개 메서드가 `BeginInvoke EndInvoke Invoke` · 생성자 `(Object, IntPtr)`** — 생성자가 받는 둘이 **대상 객체와 메서드 포인터**다(본체 그림).
- ★★★ **`Invoke` 서명이 둘 다 `Int32 Invoke(Int32)`** 인데 **`[B]` `typeof(Op) == typeof(Func<int,int>)` 가 `False`**, **`[C]` `IsAssignableFrom` 도 `False`** — **서명이 같아도 다른 클래스**다.
- ★★ **`[D]` 람다 `x => x + 1` 을 담은 `op` 의 `Method.Name = <Main>b__1_0` · `Target` 의 타입 `<>c`** — 캡처 없는 람다는 **컴파일러가 만든 싱글턴 `<>c` 의 인스턴스 메서드**가 된다([28번](../28-lambdas-and-closure-capture/)의 본체).

### (2) ★★★ 서명이 같은 두 델리게이트 타입 — 대입도 캐스트도 안 된다

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

- ★★★ **`Op a = f;` → `CS0029`**(암시적 변환 없음) · **`Op b = (Op)f;` → `CS0030`**(**변환 자체가 없다** — 캐스트로도 못 간다).
- ★★ [26번](../26-covariance-and-contravariance-out-in/) (1)의 `CS0266`(인터페이스 사이 — 「명시적 변환은 있다」)과 대비된다 — **델리게이트 클래스끼리는 상속 관계가 없다.**

**건너가는 길**

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

- ★★★ **`f.Invoke`(메서드 그룹)와 `new Op(f)` 는 둘 다 된다** — 결과 `a(2) = 20` · `b(2) = 20`.
- ★★★ **새 델리게이트의 `Method.Name = Invoke` · ``Target = Func`2``** — **`f` 를 감싼 새 `Op`** 다(`[4]` `ReferenceEquals(a.Target, f)` `True`). 호출은 **한 단계 더** 거친다.
- ★ `new Op(f)` 도 **같은 모양**(`[3]`)으로 풀렸다 — 두 문법은 **같은 일**을 한다(이 판의 관찰).

### (3) ★★★ Java 짝 — 함수형 인터페이스도 같다

```text
===== 소스: G27.java =====
import java.util.function.Function;
interface Op { int apply(int x); }
class G27 {
    void f() {
        Function<Integer, Integer> f = x -> x * 10;
        Op a = f;
    }
}
===== javac -d j27out j27/G27.java (cc exit=1) =====
j27/G27.java:6: error: incompatible types: Function<Integer,Integer> cannot be converted to Op
        Op a = f;
               ^
1 error
===== 소스: Ex27.java =====
import java.util.function.Function;
interface Op { int apply(int x); }
public class Ex27 {
    public static void main(String[] args) {
        Function<Integer, Integer> f = x -> x * 10;
        Op a = f::apply;
        System.out.println("a.apply(2) = " + a.apply(2));
        System.out.println("a 의 클래스가 f 의 클래스와 같나 : " + (a.getClass() == f.getClass()));
    }
}
===== javac -d j27out j27/Ex27.java && java -cp j27out Ex27 (cc exit=0 · run exit=0) =====
a.apply(2) = 20
a 의 클래스가 f 의 클래스와 같나 : false
```

- ★★★ **`Op a = f;` 가 javac `incompatible types: Function<Integer,Integer> cannot be converted to Op`** — Java 의 함수형 인터페이스도 **이름이 곧 타입**이다. **C# 과 같은 결론**이다.
- ★★★ **건너가는 길도 같다** — `Op a = f::apply;`(메서드 참조) 가 통과하고 `a.apply(2) = 20`. C# 의 **`f.Invoke`** 와 **1:1** 이다.
- ★★ **`a.getClass() == f.getClass()` 가 `false`** — 새 객체가 생겼다. Java 람다·메서드 참조가 **`invokedynamic` 으로 실행 시점에 객체를 만드는** 것은 [Java 29번](../../../java/syntax/29-lambda-expressions/) (2)가 정본이다.

```text
                          C#                                    Java
   함수 타입의 정체         델리게이트 = 봉인 클래스(CLI 가 앎)      함수형 인터페이스 = 추상 메서드 하나인 인터페이스
   서명이 같은 두 타입       ✕ CS0029 / CS0030                      ✕ incompatible types
   건너가기                 f.Invoke · new Op(f)                   f::apply
   람다 → 객체              컴파일 시점에 클래스(<>c)·필드 캐시         실행 시점에 invokedynamic + LambdaMetafactory
   여러 개 묶기(멀티캐스트)   ○ += (언어·CLI 기능)                    ✕ (없다 — 리스트에 담아 돈다)

   ★ 「이름이 타입이다」 는 두 언어가 같고, 「무엇으로 만드나 · 묶을 수 있나」 가 다르다.
```

### (4) ★★★ 멀티캐스트 — 반환값 · 중간 예외 · `-=`

**언제 쓰나** — 「`+=` 로 셋을 붙이면 무엇이 돌아오나 · 하나가 던지면 · 하나를 떼면」.

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

- ★★★ **`[1]`\~`[2]` `A,B,C` 가 차례로 실행되고 `f()` 의 반환값은 `3`** — **마지막 것의 반환값만** 남는다. 앞의 `1`·`2` 는 **버려진다.**
- ★★★ **`[3]`\~`[4]` `A,Boom,C` — `A 실행`·`Boom 실행` 뒤에 `C 실행` 이 없다** — 예외가 호출 목록을 **거기서 끊는다.** 나머지를 부르려면 `GetInvocationList()` 를 직접 돌며 각각 `try` 해야 한다.
- ★★★ **`[5]`\~`[6]` `A,B,A` 에서 `-= A` 하면 `A,B`** — **끝에서부터** 찾아 **마지막 `A`** 를 뗐다.
- ★★★ **`[7]` `(A,B,C) - (B,C)` 는 `A`** — **연속된 부분 목록**이 일치하면 통째로 뗀다. **`[8]` `(A,B,C) - (A,C)` 는 그대로 `A,B,C`** — `A,C` 는 **연속이 아니라** 일치하지 않는다.
- ★★ **`[9]` `A -= A` 는 `(null)`** — 목록이 비면 델리게이트 자체가 **`null`** 이다. 그래서 컴파일러가 **`CS8601` 널 경고**를 두 줄(18행 `h -= A` · 25행 `one -= A`)에 냈다 — `-=`·`-` 의 결과는 **널일 수 있다.**

```text
   f = A; f += B; f += C;          호출 목록 [A][B][C]
   f()                              A → B → C  · 반환값 = C 의 것(3)
   g = A + Boom + C;  g()           A → Boom ✕ 예외 ── C 는 안 불린다
   h = [A][B][A];  h -= A           끝에서부터 찾는다 → [A][B]
   [A][B][C] - [B][C]               연속 부분 목록 일치 → [A]
   [A][B][C] - [A][C]               연속이 아니다 → 그대로 [A][B][C]
   [A] - [A]                        빈 목록 → null
```

### (5) ★★★ IL — 메서드 그룹 변환은 `ldftn` + `newobj`, C# 11 에서 정적인 것만 캐시

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

- ★★★ **C# 10 판 `Static()` 은 `ldnull` · `ldftn P::Twice` · `newobj Func::.ctor`** — 부를 때마다 **새 델리게이트**를 만든다. 대상이 없어 `ldnull` 이다.
- ★★★ **C# 11 판 `Static()` 은 `ldsfld P+<>O::<0>__Twice` · `dup` · `brtrue.s` 로 캐시를 먼저 보고**, 비어 있을 때만 `newobj` 뒤 `stsfld` 로 **저장**한다 — **같은 소스 · 같은 컴파일러 · 판 하나 차이**다.
- ★★★ **`Instance()`(`Inc` — 인스턴스 메서드)는 두 판이 같다** — `ldarg.0`(대상 `this`) · `ldftn` · `newobj`. **대상이 호출마다 다를 수 있어 캐시할 수 없다.**
- ★★ **`Lambda()`(캡처 없는 람다)는 두 판 다 `<>c::<>9__4_0` 캐시** — 람다 캐시는 **C# 11 이전부터** 있었다. **11 이 한 일은 정적 메서드 그룹을 람다와 같은 대우로 올린 것**이다.
- ★★ **`Call` 은 `callvirt Func::Invoke`** — 델리게이트 호출은 **`Invoke` 메서드 호출**이다.

### (6) ★★★ 할당 바이트 — C# 10 대 11 × 2×2 판 격자

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

- ★★★ **(가) 같은 판 안에서 네 판이 갈린 줄 0 / 4** — 최적화·티어링과 무관하다.
- ★★★ **(나) 10 판과 11 판이 갈린 줄 2 / 4** — **`[1]` 정적 메서드 그룹 `Use(Twice)` 가 64000 → 0**, **`[4]` 두 번 변환한 델리게이트가 `ReferenceEquals` `False` → `True`**.
- ★★★ **안 갈린 두 줄** — **`[2]` 캡처 없는 람다는 두 판 다 0**, **`[3]` 인스턴스 메서드 그룹 `p.Inc` 는 두 판 다 64000**.
- ★★ **64000 = 1000 × 64바이트** — 이 판에서 `Func<int,int>` 하나가 **64바이트**다(관찰).
- ★ **시간은 안 쟀다.** 「델리게이트는 느리다」·「메서드 그룹이 람다보다 빠르다」는 **이 문서에 근거가 없다** — 잰 것은 **할당 바이트**뿐이다.

### (7) ★ 판 경계 — 무엇이 언어이고 무엇이 컴파일러인가

- ★★★ **C# 11 의 변화는 문법이 아니라 코드 생성**이다 — 소스는 한 글자도 안 바뀌었는데 **IL 과 할당과 `ReferenceEquals`** 가 바뀌었다. Learn 버전 이력은 이것을 「**Improved method group conversion to delegate**」 한 줄로 적는다.
- ★★ **「두 번 변환하면 다른 객체」에 기대는 코드가 C# 11 에서 깨질 수 있다** — `[4]` 가 `False` → `True`. 델리게이트를 **키로 쓰거나 동일성으로 비교하는 코드**의 자리다.

## 문법 — 형태와 규칙

### 형태

```text
===== 소스: cs27b-form.cs =====
using System;
using System.Collections.Generic;

Func<int, int, int> add = (a, b) => a + b;
Action<string> say = s => Console.Write($"<{s}>");
Predicate<int> even = n => n % 2 == 0;
Transform shout = Upper;
say += s => Console.Write($"[{s.Length}]");
say("hi");
Console.WriteLine();
Console.WriteLine($"{add(2, 3)} · {even(4)} · {shout("abc")} · {Apply(new List<int> { 1, 2, 3 }, x => x * x)}");

static string Upper(string s) => s.ToUpperInvariant();
static string Apply(List<int> xs, Func<int, int> f) => string.Join(",", xs.ConvertAll(x => f(x)));

delegate string Transform(string s);
===== csc -out:ex.dll cs27b-form.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
<hi>[2]
5 · True · ABC · 1,4,9
```

- ★★★ **`Func<…, TResult>` 는 값을 돌려주는 것, `Action<…>` 은 안 돌려주는 것, `Predicate<T>` 는 `Func<T, bool>` 과 서명이 같은 다른 타입**이다.
- ★★ **`delegate string Transform(string s);`** — 내 델리게이트 타입. 이름이 **뜻을 말할 때**(`Transform`) 쓴다.
- ★★ **메서드 그룹 `Upper` 를 그대로 대입** · **람다 둘을 `+=` 로 묶기**(`<hi>[2]`) — `Action` 멀티캐스트는 **반환값이 없어** (4)의 「마지막 것만」 문제가 없다.

### 금지 사례 — 진단이 나는 꼴

| 쓴 꼴 | 진단 코드 | 어디서 |
|---|---|---|
| 서명이 같은 다른 델리게이트 타입에 대입 | `CS0029` | (2) |
| 그 사이의 명시적 캐스트 | `CS0030` | (2) |
| `-=`·`-` 결과를 널 불가 변수에 | `CS8601`(**경고**) | (4) |
| Java 에서 서명이 같은 다른 함수형 인터페이스에 대입 | javac `incompatible types` | (3) |

## 어디서 틀리나

1. ★★★ **「서명이 같으면 같은 델리게이트다」** — **다른 클래스**다(`CS0029`·`CS0030`)((1)(2)).
2. ★★★ **「멀티캐스트는 모든 반환값을 모은다」** — **마지막 것만**((4) `[2]`).
3. ★★★ **「하나가 던져도 나머지는 불린다」** — **거기서 끊긴다**((4) `[3]`\~`[4]`).
4. ★★ **「`-=` 는 처음 것을 뗀다」** — **마지막 일치**를 뗀다 · 부분 목록은 **연속일 때만**((4) `[6]`\~`[8]`).
5. ★★★ **「메서드 그룹은 매번 할당한다」** — **C# 11 부터 정적 메서드 그룹은 캐시**다. **인스턴스 메서드 그룹은 여전히 매번**((6)).
6. ★★ **「C# 11 캐시는 JIT 최적화다」** — **IL 이 바뀌었다**(Roslyn) · 네 판이 같다((5)(6)).
7. ★★ **「델리게이트는 느리다」** — 이 문서는 **시간을 안 쟀다.**
8. ★ **「`-=` 로 다 떼도 빈 델리게이트가 남는다」** — **`null`** 이다((4) `[9]`).

## 구현 세부사항 대 언어 보장

| 무엇 | 층 | 근거 |
|---|---|---|
| **델리게이트 = `MulticastDelegate` 를 상속한 봉인 클래스 · `Invoke`** | ★★★ **CLI 명세(ECMA-335)** | (1) |
| **서명이 같아도 다른 델리게이트 타입 사이 변환 없음** | ★★★ **언어(334) · CLI** | (2) |
| **멀티캐스트 호출 순서 · 반환값은 마지막 · `-=` 규칙** | ★★★ **언어 · BCL(`Delegate.Remove`)** | (4) |
| **메서드 그룹 변환 = `ldftn` + `newobj`** | ★★ **Roslyn 구현** | (5) |
| **캡처 없는 람다 · (C# 11 부터) 정적 메서드 그룹의 캐시** | ★★ **Roslyn 구현**(언어 판이 켠다) | (5)(6) |
| **델리게이트 한 개 64바이트** | ★ **이 판의 관찰** | (6) |

## 언제 쓰고 언제 안 쓰나

- ★★★ **공개 API 는 `Func`/`Action` 을 먼저 써라** — 호출자가 **아무 람다·메서드 그룹이나** 바로 넘긴다. 내 델리게이트 타입을 쓰면 **호출자의 `Func` 가 `CS0029` 에 막힌다**((2)).
- ★★ **내 델리게이트 타입은 이름이 뜻을 더할 때·`ref`/`out` 매개변수가 필요할 때** — 대신 경계에서 `f.Invoke` 로 **감싸는 비용**을 기억해라((2)).
- ★★★ **반환값이 있는 델리게이트를 멀티캐스트로 쓰지 마라** — 앞의 결과가 **조용히 버려진다.** 모두 필요하면 `GetInvocationList()` 를 돌아라((4)).
- ★★ **여러 구독자 중 하나가 던질 수 있으면 목록을 직접 돌며 각각 잡아라**((4) `[3]`).
- ★ **할당을 아껴야 하는 반복문에서는 인스턴스 메서드 그룹을 루프 밖에서 한 번 변환해 두라** — C# 11 캐시는 **정적**만이다((6) `[3]`).

## 핵심 문장

1. ★★★ **델리게이트는 `MulticastDelegate` 를 상속한 봉인 클래스**다 — 서명이 같아도 **이름이 다르면 다른 타입**이고 `CS0029`·`CS0030` 이다((1)(2)). Java 함수형 인터페이스도 같다((3)).
2. ★★★ **멀티캐스트는 차례로 부르고 마지막 반환값만 남기며, 중간 예외에서 끊긴다** · `-=` 는 **마지막 일치(연속 부분 목록)** 를 뗀다((4)).
3. ★★★ **메서드 그룹 변환은 `ldftn` + `newobj`** — **C# 11 부터 정적 메서드 그룹만 캐시**된다: `Use(Twice)` 1000번 **64000 → 0** · 인스턴스는 **그대로**((5)(6)).
4. ★★ **그 캐시는 언어 판이 켜는 Roslyn 코드 생성**이다 — 네 판(최적화·티어링)이 같다((6)(7)).

## 관련 자료

- [28번 — 람다와 클로저](../28-lambdas-and-closure-capture/) — **경계**: 람다가 **무엇을 캡처해 어떤 클래스가 되나**는 거기. 여기는 **델리게이트 값**까지.
- [26번 — 공변·반변](../26-covariance-and-contravariance-out-in/) — `Func<in T, out TResult>` 의 변성 · 델리게이트 사이 `CS0266`.
- 목록의 **29번 주제**(`event`) — 델리게이트 필드에 `+=`/`-=` 만 허락하는 제한.
- 목록의 **33번 주제**(LINQ) — `Func` 를 받는 자리의 대부분.
- Java 갈래 목록([`java/syntax/README.md`](../../../java/syntax/README.md))의 **29번**([`29-lambda-expressions/`](../../../java/syntax/29-lambda-expressions/)) · **31번**([`31-functional-interfaces/`](../../../java/syntax/31-functional-interfaces/)) · **30번**([`30-method-references/`](../../../java/syntax/30-method-references/)) — **경계**: `invokedynamic`·`java.util.function` 지도·메서드 참조 네 형태는 거기.
- Kotlin 갈래 목록([`kotlin/syntax/README.md`](../../../kotlin/syntax/README.md))의 **10번**([`10-lambdas-and-higher-order-functions/`](../../../kotlin/syntax/10-lambdas-and-higher-order-functions/)) · **36번**(함수 타입·`fun interface`·SAM 변환 — 폴더가 아직 없다).

## 용어 풀이

- **델리게이트(delegate)** — 메서드를 가리키는 **타입**. 대상 객체 + 메서드 포인터를 든 봉인 클래스.
- **`Func<…, TResult>` · `Action<…>`** — BCL 이 미리 선언해 둔 제네릭 델리게이트 타입.
- **메서드 그룹(method group)** — 괄호 없이 쓴 메서드 이름(`Twice`). 델리게이트 타입으로 **변환**된다.
- **멀티캐스트(multicast)** — 델리게이트 하나가 **호출 목록**에 여러 메서드를 든 것. `+=` 로 붙인다.
- **호출 목록(invocation list)** — `GetInvocationList()` 가 돌려주는 델리게이트 배열.
- **`ldftn`** — 메서드의 함수 포인터를 스택에 올리는 IL 명령. 델리게이트 생성자에 넘긴다.
- **`<>c` · `<>O`** — Roslyn 이 만든 숨은 클래스. `<>c` 는 캡처 없는 람다의 싱글턴과 캐시, `<>O` 는 C# 11 의 정적 메서드 그룹 캐시.

## 더 들어가면

- ★ **`BeginInvoke`/`EndInvoke`** — 선언에는 있지만(1) .NET Core 이후 **지원하지 않는다고 알려져 있다** — **이 판에서 안 불러 봤다.**
- ★ **함수 포인터(`delegate*`, C# 9)** — 델리게이트 객체 없이 부르는 길(Learn 버전 이력 C# 9: 「델리게이트 객체를 만드는 데 필요한 **할당을 피한다**」). **안 던졌다.**
- ★ **변성 델리게이트의 결합** — Learn: 「타입이 정확히 같아야 결합된다」. `Action<object>` 를 담은 `Action<string>` 변수에 `Action<string>` 을 `+=` 하면 — **안 던졌다.**
