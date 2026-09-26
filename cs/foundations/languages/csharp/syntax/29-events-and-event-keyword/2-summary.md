# csharp/syntax/29 — 이벤트와 `event` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [ECMA-334 7판(2023-12)](https://ecma-international.org/publications-and-standards/standards/ecma-334/) ·
> [Learn — `event` 키워드](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/keywords/event)(열어서 확인: 「이벤트는 **선언한 클래스(또는 파생 클래스)나 구조체 안에서만 호출할 수 있는** 멀티캐스트 델리게이트다」 ·\
> 「`abstract` 이면 컴파일러가 **`add`·`remove` 접근자 블록을 만들지 않는다**」 · 「**C# 14 부터 `partial` 이벤트**」 · 예제의 「`SampleEvent?.Invoke(this, …)`」).\
> ★★★ **Learn 의 「파생 클래스 안에서도 호출할 수 있다」는 이 판에서 성립하지 않았다** — 필드형 이벤트를 파생 클래스에서 `E()` 로 부르면 **`CS0070`** 이다((1)). 그 예제도 호출을 **`protected virtual` 메서드로 감싸** 파생 클래스에 연다.
> **실행 검증** — 이 문서의 모든 출력·진단·IL·GC 결과는 아래 「이 판」의 도구로 **실제로 돌려 얻은 것**이다(2026-09-26).\
> ★ 블록은 캡처 스크립트가 파일로 받아 조립기가 끼워 넣은 것이다 — 사람이 옮겨 적은 줄은 하나도 없다.
> **버전** — `event`·`add`/`remove` 접근자 **C# 1** · `?.` **C# 6** · `partial` 이벤트 **C# 14**(Learn — **이 판에서 안 던졌다**).
> **경계** — ★★★ **멀티캐스트 델리게이트 자체**(호출 목록 · 반환값은 마지막 것 · 중간 예외 · `-=` 는 끝에서부터)는 [27번](../27-delegates-and-func-action/) (4)가 정본이다 — **다시 재지 않고 인용한다.**\
> ★★★ **「붙들면 안 풀린다」의 GC 창**은 [28번](../28-lambdas-and-closure-capture/) (5)의 것을 그대로 쓴다 — 여기서는 **붙드는 쪽이 이벤트의 호출 목록**인 경우만 본다.\
> ★ 속성이 `get_`/`set_` 메서드가 되는 것은 [13번](../13-properties-init-required-field/) — (2)의 `add_`/`remove_` 가 같은 모양이다.
> ★★★ **본체 창은 ② 진단 격자다** — 「`event` 가 **무엇을 막나**」는 **막힌 칸을 세야** 보인다.
>
> ★★ **흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | 진단 **문구** · 진단 **순서**(배너에 `sort`) · IL **오프셋 폭** | ★★★ **진단 코드**(`CS0070` · `CS0079` · `CS0066`) · **「막힌 칸 N / M」** |
> | 컴파일러가 지은 캐시 이름(`<>O::<0>__H`) | ★★★ **옵코드**(`callvirt Pub::add_E` · `Delegate::Combine` + `stfld` · `Interlocked::CompareExchange`) · 리플렉션의 **이름과 `specialname`** |
> | GC 가 **언제** 도나 | ★★★ **「회수됐나」 참/거짓** · **「네 판에서 갈린 줄 N / M」** · 호출 목록 **길이** |

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
| **언어 명세(ECMA-334)** | ★★★ **C# 언어가 약속한 것** | ★★★ 필드형 이벤트는 **선언한 타입 밖에서 `+=`·`-=` 의 왼쪽에만** 올 수 있다 · 이벤트의 타입은 **델리게이트**여야 한다 · 접근자를 직접 쓰면 **필드가 없다** |
| **CLI(ECMA-335) · 메타데이터** | 실행 엔진이 보는 것 | ★★ 이벤트는 **메타데이터 항목 하나 + `add_`/`remove_` 메서드**(`specialname`) — 속성과 같은 모양 |
| **컴파일러 구현(Roslyn)** | ★★★ 그것을 **어떻게 적나** | ★★★ 숨은 필드의 **이름이 이벤트와 같다**(`E`) · `add_E` 는 **`Interlocked.CompareExchange` 고리** · 바깥의 `+=` 는 **`callvirt add_E`** |
| **이 판의 관찰** | .NET 10.0.12 · linux-x64 | GC 결과 · 진단 문구 |

★★★ **이 주제의 층 구분 —**\
**「바깥에서는 붙이고 떼기만」은 명세**다. **숨은 필드 · `CompareExchange` 고리는 Roslyn 구현**이다. **누수는 명세도 구현도 아니다** — 「도달 가능한 것은 안 풀린다」는 GC 규칙이 **호출 목록**에 적용된 결과다.

## 한눈에 — 쉽게 말하면

**`event` 는 「구독 신청함」이다 — 밖에서는 신청서를 넣고(`+=`) 빼는(`-=`) 구멍만 보이고, 명단을 읽거나 방송을 트는 것은 주인만 한다.**

- **명단(숨은 델리게이트 필드)** — 구독자들의 호출 목록. 필드 그대로 두면(`public Action F`) **누구나** 명단을 지우고(`= null`) 바꾸고(`= H`) 방송을 튼다(`F()`).
- **신청함의 두 구멍(`add`/`remove`)** — `event` 를 붙이면 **바깥에는 이 두 구멍만** 남는다. 나머지는 **컴파일 에러**다.
- **파생 클래스도 바깥이다** — 자식 클래스도 명단을 못 읽는다. 방송을 열어 주려면 주인이 `protected` 메서드를 따로 만든다.
- **명단에 이름이 있는 한 그 사람은 못 떠난다** — 오래 사는 발행자의 명단에 짧게 살 구독자의 메서드가 남아 있으면 **구독자가 회수되지 않는다.**
- **같은 모양의 새 람다로는 이름을 못 지운다** — `-=` 는 **같은 델리게이트**를 찾는다. 새로 만든 람다는 **다른 것**이다.

| 비유 | 실체 | 어디서 보나 |
|---|---|---|
| 구멍 두 개만 | ★★★ **바깥에서 `+=`·`-=` 는 `ok`, `=`·`E()`·`= null`·`GetInvocationList` 는 `CS0070`** | (1) |
| 자식도 바깥 | ★★★ **파생 클래스 열이 바깥 열과 같다** | (1) |
| 명단은 숨은 필드 | ★★★ **`private Action E` 필드 + `add_E`/`remove_E`(`specialname=True`)** | (2) |
| 구멍은 메서드 호출 | ★★★ 바깥 `p.E += H` → **`callvirt Pub::add_E`** · 필드 `p.F += H` → **`Delegate::Combine` + `stfld`** | (2) |
| 명단이 붙든다 | ★★★ 해제 안 함 **`False`** · 새 람다로 해제 **`False`** · 발행자가 짧게 살면 **`True`** | (4) |
| 새 람다는 다른 이름 | ★★ `-= () => s.OnTick()` 뒤 **`Count` 1** | (3) |

★★★ **이 주제의 본체 그림 — `event` 한 단어가 바꾸는 것.**

```text
   public Action? F;                          public event Action? E;
   ─────────────────────────────              ──────────────────────────────────────────────
   Pub                                        Pub
    └ public Action F   ◀── 누구나             ├ private Action E        ◀── 숨은 필드(이름이 같다 — Roslyn)
                            = · () · null     ├ public  add_E(Action)    ◀── 바깥의 +=  → callvirt add_E
                            · list · += · -=  └ public  remove_E(Action) ◀── 바깥의 -=  → callvirt remove_E

   바깥(Other)에서                              바깥(Other) · 파생(Sub)에서
     p.F += H   → ldfld F · Combine · stfld F      p.E += H   → callvirt add_E            ok
     p.F = null → stfld F           ok             p.E = null → CS0070
     p.F()      → Invoke            ok             p.E()      → CS0070
                                                   p.E.GetInvocationList() → CS0070

   ★★★ event 는 델리게이트에 새 기능을 더하지 않는다 — 바깥에서 쓸 수 있는 식을 += · -= 둘로 줄인다.
```

## 이 주제가 답하려는 질문

1. **`event` 는 델리게이트 필드에 무엇을 막나** — 식 여섯 × 자리 다섯((1)).
2. **`event` 는 무엇으로 컴파일되나** — 숨은 필드 · `add_`/`remove_` · 바깥의 `+=`((2)).
3. **구독 해제를 빠뜨리면 무엇이 안 풀리나 · 무엇으로 떼어지나**((3)(4)).
4. **접근자를 직접 쓰면 무엇이 달라지나**((1)(5)).

## 동작 방식

### (0) 이 주제가 쓰는 창

★★★ **본체 창은 ② 진단 격자다** — 이벤트는 **새로 할 수 있는 것**이 아니라 **못 하게 된 것**으로 정의된다.

| 창 | 무엇을 보여 주나 | 이 주제에서 |
|---|---|---|
| ★★★ **② 진단 격자** | ★★★ 식 여섯 × 자리 다섯 = 30칸 · **`CS0070`**(필드형 · 바깥과 파생) · **`CS0079`**(접근자형 · 안에서도) · `CS0066` | (1)(6) |
| ★★★ **① IL 덤프** | ★★★ 바깥의 `+=` 가 **`callvirt add_E`** 인 것 · 필드의 `+=` 는 **`Combine` + `stfld`** · `add_E` 의 **`CompareExchange` 고리** | (2) |
| ★★ **③ 리플렉션** | ★★ 숨은 필드 `private Action E` · `add_E`/`remove_E` 가 `specialname` · 속성 `P` 의 `get_P`/`set_P` 와 같은 모양 · `raise=(없음)` | (2) |
| ★★★ **GC 창(`WeakReference`)** | ★★★ **제5의 상태** — 「누수」는 할당 바이트로 못 묻는다. [28번](../28-lambdas-and-closure-capture/) (5)의 방법 그대로 **「회수됐나」** 를 2×2 판 격자로 물었다. ★ 이 창이 못 보는 것 — **언제 회수되나** · 메모리 양 | (4) |
| **부적용인 창** | ★ **④ 할당 바이트** — 이 주제의 질문은 **양이 아니라 수명**이다. 구독 한 번의 할당은 [27번](../27-delegates-and-func-action/) (6)(델리게이트 하나 64바이트)과 같은 물음이라 **재지 않았다** | — |

### (1) ★★★ 본체 — `event` 가 막는 것 격자

**언제 쓰나** — 「이 델리게이트를 `public` 으로 열어 두면 **남이 무엇을 할 수 있나**」.

```text
===== 소스: cs29b-grid.cs =====
using System;
class Pub {
    public Action? F;
    public event Action? E;
    Action? store;
    public event Action? C { add { store += value; } remove { store -= value; } }
    void Inside() {
        E += H;                            // cell += event·inside
        E -= H;                            // cell -= event·inside
        E = H;                             // cell = event·inside
        E();                               // cell () event·inside
        E = null;                          // cell =null event·inside
        _ = E!.GetInvocationList();        // cell list event·inside
        C += H;                            // cell += custom·inside
        C -= H;                            // cell -= custom·inside
        C = H;                             // cell = custom·inside
        C();                               // cell () custom·inside
        C = null;                          // cell =null custom·inside
        _ = C!.GetInvocationList();        // cell list custom·inside
    }
    static void H() { }
}
class Sub : Pub {
    void Derived() {
        E += H;                            // cell += event·derived
        E -= H;                            // cell -= event·derived
        E = H;                             // cell = event·derived
        E();                               // cell () event·derived
        E = null;                          // cell =null event·derived
        _ = E!.GetInvocationList();        // cell list event·derived
    }
    static void H() { }
}
class Other {
    static void H() { }
    static void Outside(Pub p) {
        p.F += H;                          // cell += field·outside
        p.F -= H;                          // cell -= field·outside
        p.F = H;                           // cell = field·outside
        p.F();                             // cell () field·outside
        p.F = null;                        // cell =null field·outside
        _ = p.F!.GetInvocationList();      // cell list field·outside
        p.E += H;                          // cell += event·outside
        p.E -= H;                          // cell -= event·outside
        p.E = H;                           // cell = event·outside
        p.E();                             // cell () event·outside
        p.E = null;                        // cell =null event·outside
        _ = p.E!.GetInvocationList();      // cell list event·outside
    }
}
===== csc -nullable:enable -target:library -out:g29.dll cs29b-grid.cs 2>&1 | sort (cc exit=1) =====
cs29b-grid.cs(16,9): error CS0079: The event 'Pub.C' can only appear on the left hand side of += or -=
cs29b-grid.cs(17,9): error CS0079: The event 'Pub.C' can only appear on the left hand side of += or -=
cs29b-grid.cs(18,9): error CS0079: The event 'Pub.C' can only appear on the left hand side of += or -=
cs29b-grid.cs(19,13): error CS0079: The event 'Pub.C' can only appear on the left hand side of += or -=
cs29b-grid.cs(27,9): error CS0070: The event 'Pub.E' can only appear on the left hand side of += or -= (except when used from within the type 'Pub')
cs29b-grid.cs(28,9): error CS0070: The event 'Pub.E' can only appear on the left hand side of += or -= (except when used from within the type 'Pub')
cs29b-grid.cs(29,9): error CS0070: The event 'Pub.E' can only appear on the left hand side of += or -= (except when used from within the type 'Pub')
cs29b-grid.cs(30,13): error CS0070: The event 'Pub.E' can only appear on the left hand side of += or -= (except when used from within the type 'Pub')
cs29b-grid.cs(45,11): error CS0070: The event 'Pub.E' can only appear on the left hand side of += or -= (except when used from within the type 'Pub')
cs29b-grid.cs(46,11): error CS0070: The event 'Pub.E' can only appear on the left hand side of += or -= (except when used from within the type 'Pub')
cs29b-grid.cs(47,11): error CS0070: The event 'Pub.E' can only appear on the left hand side of += or -= (except when used from within the type 'Pub')
cs29b-grid.cs(48,15): error CS0070: The event 'Pub.E' can only appear on the left hand side of += or -= (except when used from within the type 'Pub')
===== python3 cellgrid.py cs29b-grid.cs <위 진단> — 칸마다 진단 코드 =====
식 \ 자리           event·inside     custom·inside    event·derived    field·outside    event·outside
+=               ok               ok               ok               ok               ok
-=               ok               ok               ok               ok               ok
=                ok               CS0079           CS0070           ok               CS0070
()               ok               CS0079           CS0070           ok               CS0070
=null            ok               CS0079           CS0070           ok               CS0070
list             ok               CS0079           CS0070           ok               CS0070
막힌 칸 12 / 30
```

- ★★★ **막힌 칸 12 / 30** — 스크립트가 줄 번호로 칸을 되찾아 셌다.
- ★★★ **필드(`field·outside`)는 여섯 식이 전부 `ok`** — 바깥의 아무나 `p.F = null` 로 **남의 구독을 통째로 지우고**, `p.F()` 로 **발행자 대신 방송**할 수 있다.
- ★★★ **이벤트를 바깥에서(`event·outside`) 쓰면 `+=`·`-=` 만 `ok`** · 나머지 넷(`=` · `()` · `=null` · `list`)이 **`CS0070`** — 「`'Pub.E'` 는 **`+=`·`-=` 의 왼쪽에만** 올 수 있다(`'Pub'` 안에서 쓸 때는 예외)」.
- ★★★ **파생 클래스(`event·derived`)도 바깥과 한 글자도 같다** — 「선언한 타입 안」은 **`Pub` 뿐**이다. Learn 의 「파생 클래스 안에서도 호출할 수 있다」와 **다르다**(머리말).
- ★★ **선언한 클래스 안(`event·inside`)은 여섯 식이 전부 `ok`** — 안에서는 **필드 그대로** 보인다.
- ★★★ **접근자를 직접 쓴 `C`(`custom·inside`)는 안에서도 넷이 `CS0079`** — 「`+=`·`-=` 의 왼쪽에만」(괄호 꼬리가 없다). `C` 에는 **필드가 없으니** 안에서도 읽을 것이 없다((6)).
- ★ **`GetInvocationList` 도 막힌다**(`list` 행) — 바깥에서는 **구독자가 몇인지조차** 물을 수 없다. (3)(4)의 `Count` 는 그래서 **발행자가 직접** 연 속성이다.

### (2) ★★★ IL · 리플렉션 — `event` 는 무엇이 되나

```text
===== 소스: cs29b-il.cs =====
using System;
using System.Linq;
using System.Reflection;
public class Pub {
    public Action? F;
    public event Action? E;
    public int P { get; set; }
}
public static class Use {
    static void H() { }
    public static void AddToField(Pub p) => p.F += H;
    public static void AddToEvent(Pub p) => p.E += H;
}
class Program {
    const BindingFlags All = BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Static | BindingFlags.Instance | BindingFlags.DeclaredOnly;
    static void Main() {
        foreach (var f in typeof(Pub).GetFields(All).OrderBy(f => f.Name, StringComparer.Ordinal))
            Console.WriteLine($"필드   {(f.IsPublic ? "public " : "private")} {f.FieldType.Name} {f.Name}");
        foreach (var m in typeof(Pub).GetMethods(All).OrderBy(m => m.Name, StringComparer.Ordinal))
            Console.WriteLine($"메서드 {(m.IsPublic ? "public " : "private")} {m.Name} (specialname={m.IsSpecialName})");
        foreach (var e in typeof(Pub).GetEvents(All))
            Console.WriteLine($"이벤트 {e.Name} : {e.EventHandlerType!.Name} · add={e.AddMethod!.Name} · remove={e.RemoveMethod!.Name} · raise={(e.RaiseMethod?.Name ?? "(없음)")}");
        foreach (var p in typeof(Pub).GetProperties(All))
            Console.WriteLine($"속성   {p.Name} : get={p.GetMethod!.Name} · set={p.SetMethod!.Name}");
        Il.Dump(typeof(Pub), "add_E");
        Il.Dump(typeof(Use), "AddToField");
        Il.Dump(typeof(Use), "AddToEvent");
    }
}
===== csc -nullable:enable -optimize -r:il.dll -out:exo.dll cs29b-il.cs && dotnet exo.dll (cc exit=0 · run exit=0) =====
cs29b-il.cs(6,26): warning CS0067: The event 'Pub.E' is never used
필드   private Int32 <P>k__BackingField
필드   private Action E
필드   public  Action F
메서드 public  add_E (specialname=True)
메서드 public  get_P (specialname=True)
메서드 public  remove_E (specialname=True)
메서드 public  set_P (specialname=True)
이벤트 E : Action · add=add_E · remove=remove_E · raise=(없음)
속성   P : get=get_P · set=set_P
--- Pub.add_E ---
  .locals [0] System.Action
  .locals [1] System.Action
  .locals [2] System.Action
  IL_0000: ldarg.0
  IL_0001: ldfld Pub::E
  IL_0006: stloc.0
  IL_0007: ldloc.0
  IL_0008: stloc.1
  IL_0009: ldloc.1
  IL_000a: ldarg.1
  IL_000b: call System.Delegate::Combine
  IL_0010: castclass System.Action
  IL_0015: stloc.2
  IL_0016: ldarg.0
  IL_0017: ldflda Pub::E
  IL_001c: ldloc.2
  IL_001d: ldloc.1
  IL_001e: call System.Threading.Interlocked::CompareExchange<System.Action>
  IL_0023: stloc.0
  IL_0024: ldloc.0
  IL_0025: ldloc.1
  IL_0026: bne.un.s IL_0007
  IL_0028: ret
--- Use.AddToField ---
  IL_0000: ldarg.0
  IL_0001: dup
  IL_0002: ldfld Pub::F
  IL_0007: ldsfld Use+<>O::<0>__H
  IL_000c: dup
  IL_000d: brtrue.s IL_0022
  IL_000f: pop
  IL_0010: ldnull
  IL_0011: ldftn Use::H
  IL_0017: newobj System.Action::.ctor
  IL_001c: dup
  IL_001d: stsfld Use+<>O::<0>__H
  IL_0022: call System.Delegate::Combine
  IL_0027: castclass System.Action
  IL_002c: stfld Pub::F
  IL_0031: ret
--- Use.AddToEvent ---
  IL_0000: ldarg.0
  IL_0001: ldsfld Use+<>O::<0>__H
  IL_0006: dup
  IL_0007: brtrue.s IL_001c
  IL_0009: pop
  IL_000a: ldnull
  IL_000b: ldftn Use::H
  IL_0011: newobj System.Action::.ctor
  IL_0016: dup
  IL_0017: stsfld Use+<>O::<0>__H
  IL_001c: callvirt Pub::add_E
  IL_0021: ret
```

- ★★★ **필드가 셋** — `public Action F` · **`private Action E`** · `private Int32 <P>k__BackingField`. 이벤트 `E` 의 **숨은 필드 이름이 `E` 그대로**다(속성의 뒷받침 필드는 `<P>k__BackingField` 라는 **다른 이름**).
- ★★★ **이벤트 `E` → `add_E` · `remove_E`**(둘 다 `public` · `specialname=True`) · 속성 `P` → `get_P` · `set_P`(같은 모양). **`raise=(없음)`** — C# 은 「발생」 메서드를 만들지 않는다. 안에서의 `E()` 는 **필드를 직접 부른다.**
- ★★★ **`add_E` 는 한 번의 `Combine` 이 아니다** — `ldfld E` → `Combine` → **`Interlocked::CompareExchange<Action>`** → 결과가 읽은 값과 다르면 **`bne.un.s IL_0007` 로 되돌아간다.** 여러 스레드가 동시에 구독해도 **하나를 잃지 않는** 고리다(Roslyn 구현).
- ★★★ **`AddToField`(`p.F += H`) 는 `ldfld F` · `Combine` · `castclass` · `stfld F`** — 호출하는 쪽이 **필드를 직접 고친다.** **`AddToEvent`(`p.E += H`) 는 `callvirt Pub::add_E` 한 줄** — 필드에 **손을 못 댄다.**
- ★ 둘 다 `<>O::<0>__H` 캐시를 거친다 — 정적 메서드 그룹 캐시(C# 11, [27번](../27-delegates-and-func-action/) (5)).
- ★ `warning CS0067` — `E` 가 **한 번도 발생되지 않는다**는 경고. 이 프로브는 선언만 보므로 그대로 뒀다.

```text
   p.F += H  (필드)                                  p.E += H  (이벤트)
   ───────────────────────────────                    ─────────────────────────────
   호출자가 직접:                                     호출자는 부탁만:
     t = p.F                     (ldfld)                callvirt Pub::add_E(H)
     t = Delegate.Combine(t, H)                                │
     p.F = t                     (stfld)                       ▼  Pub 안에서 (add_E)
                                                        do { old = E
   ★ 두 스레드가 동시에 하면                                   new = Combine(old, H)
     하나의 H 가 사라질 수 있다                              } while (CompareExchange(ref E, new, old) != old)
     (읽고-고치고-쓰기가 셋으로 갈라져 있다)            ★ 고리 — 남이 먼저 고쳤으면 다시 읽는다
```

- ★★ **그림의 「사라질 수 있다」는 IL 모양에서 읽은 것이다 — 경쟁을 실제로 일으켜 잰 것이 아니다**(이 판에서 **안 돌렸다**).

### (3) ★★ 구독 · 해제 · 발생 — 무엇이 떼어지나

```text
===== 소스: cs29b-raise.cs =====
using System;
class Pub {
    public event Action? Tick;
    public int Count => Tick?.GetInvocationList().Length ?? 0;
    public bool IsNull => Tick is null;
    public void RaiseDirect() => Tick!();
    public void RaiseSafe() => Tick?.Invoke();
}
class Sub {
    public int Seen;
    public void OnTick() => Seen++;
}
class Program {
    static void Main() {
        var p = new Pub();
        Console.WriteLine($"[1] 구독자 0 · Tick is null : {p.IsNull}");
        try { p.RaiseDirect(); Console.WriteLine("[2] Tick!() : 예외 없음"); }
        catch (Exception e) { Console.WriteLine($"[2] Tick!() : {e.GetType().Name}"); }
        try { p.RaiseSafe(); Console.WriteLine("[3] Tick?.Invoke() : 예외 없음"); }
        catch (Exception e) { Console.WriteLine($"[3] Tick?.Invoke() : {e.GetType().Name}"); }
        var s = new Sub();
        var p4 = new Pub(); p4.Tick += s.OnTick; p4.Tick -= s.OnTick;
        Console.WriteLine($"[4] 새 발행자에 += s.OnTick · -= s.OnTick 뒤 Count : {p4.Count}");
        var p5 = new Pub(); p5.Tick += () => s.OnTick(); p5.Tick -= () => s.OnTick();
        Console.WriteLine($"[5] 새 발행자에 += 람다 · -= 같은 모양의 람다 뒤 Count : {p5.Count}");
        Action h = () => s.OnTick();
        var p6 = new Pub(); p6.Tick += h; p6.Tick -= h;
        Console.WriteLine($"[6] 새 발행자에 += h · -= h 뒤 Count : {p6.Count}");
        p5.RaiseSafe();
        Console.WriteLine($"[7] [5] 의 발행자를 한 번 발생시킨 뒤 s.Seen : {s.Seen}");
    }
}
===== csc -nullable:enable -out:ex.dll cs29b-raise.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
[1] 구독자 0 · Tick is null : True
[2] Tick!() : NullReferenceException
[3] Tick?.Invoke() : 예외 없음
[4] 새 발행자에 += s.OnTick · -= s.OnTick 뒤 Count : 0
[5] 새 발행자에 += 람다 · -= 같은 모양의 람다 뒤 Count : 1
[6] 새 발행자에 += h · -= h 뒤 Count : 0
[7] [5] 의 발행자를 한 번 발생시킨 뒤 s.Seen : 1
```

- ★★★ **`[1]`\~`[3]` 구독자가 0 이면 `Tick` 은 `null`** — `Tick!()` 는 **`NullReferenceException`**, `Tick?.Invoke()` 는 **예외 없음.** 빈 호출 목록이 `null` 인 것은 [27번](../27-delegates-and-func-action/) (4) `[9]` 와 같다.
- ★★★ **`[4]` `+= s.OnTick` · `-= s.OnTick` → `0`** — 메서드 그룹을 두 번 변환하면 **다른 델리게이트 객체**지만, `-=` 는 **같은 대상(`Target`) + 같은 메서드**면 같다고 본다.
- ★★★ **`[5]` 같은 모양의 람다로 `-=` → `1`** — 두 람다는 **컴파일러가 만든 메서드가 서로 다르다.** 떼어지지 않는다 — **에러도 경고도 없다.**
- ★★ **`[6]` 람다를 변수 `h` 에 두고 같은 `h` 로 떼면 `0`.**
- ★ **`[7]` `s.Seen` 1** — `[5]` 의 발행자에 **남은 람다가 실제로 불렸다.**

### (4) ★★★ 구독 해제 누락 — 오래 사는 발행자가 구독자를 붙든다

**언제 쓰나** — 「화면·요청처럼 **짧게 사는 객체**가 앱 전체 서비스처럼 **오래 사는 객체**의 이벤트를 구독할 때」.

```text
===== 소스: cs29b-leak.cs =====
using System;
using System.Runtime.CompilerServices;
class Pub {
    public event Action? Tick;
    public int Count => Tick?.GetInvocationList().Length ?? 0;
    public void Clear() => Tick = null;
}
class Sub {
    readonly byte[] big = new byte[10_000_000];
    public void OnTick() => _ = big.Length;
}
class Program {
    static readonly Pub[] longLived = { new(), new(), new(), new(), new(), new(), new() };
    static void StaticHandler() { }
    [MethodImpl(MethodImplOptions.NoInlining)]
    static WeakReference Case(int k) {
        var s = new Sub();
        var p = longLived[k];
        switch (k) {
            case 1: p.Tick += s.OnTick; p.Tick -= s.OnTick; break;
            case 2: p.Tick += s.OnTick; break;
            case 3: p.Tick += () => s.OnTick(); p.Tick -= () => s.OnTick(); break;
            case 4: { Action h = () => s.OnTick(); p.Tick += h; p.Tick -= h; break; }
            case 5: { var shortLived = new Pub(); shortLived.Tick += s.OnTick; break; }
            case 6: p.Tick += StaticHandler; break;
        }
        return new WeakReference(s);
    }
    static bool Collected(WeakReference w) { GC.Collect(); GC.WaitForPendingFinalizers(); GC.Collect(); return !w.IsAlive; }
    static void Main() {
        string[] what = { "", "메서드로 구독 · 해제함", "메서드로 구독 · 해제 안 함", "람다로 구독 · 새 람다로 해제", "람다를 변수에 두고 · 같은 변수로 해제", "짧게 사는 발행자에 구독 · 해제 안 함", "구독자와 무관한 정적 메서드로 구독" };
        var w = new WeakReference[7];
        for (int k = 1; k <= 6; k++) {
            w[k] = Case(k);
            Console.WriteLine($"[{k}] {what[k]} · 오래 사는 발행자 목록 {longLived[k].Count} · 구독자 회수됐나 : {Collected(w[k])}");
        }
        longLived[2].Clear(); longLived[3].Clear();
        Console.WriteLine($"[7] 발행자가 목록을 비운 뒤 [2] 구독자 회수됐나 : {Collected(w[2])}");
        Console.WriteLine($"[8] 발행자가 목록을 비운 뒤 [3] 구독자 회수됐나 : {Collected(w[3])}");
    }
}
===== csc -nullable:enable -out:ex.dll cs29b-leak.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
[1] 메서드로 구독 · 해제함 · 오래 사는 발행자 목록 0 · 구독자 회수됐나 : True
[2] 메서드로 구독 · 해제 안 함 · 오래 사는 발행자 목록 1 · 구독자 회수됐나 : False
[3] 람다로 구독 · 새 람다로 해제 · 오래 사는 발행자 목록 1 · 구독자 회수됐나 : False
[4] 람다를 변수에 두고 · 같은 변수로 해제 · 오래 사는 발행자 목록 0 · 구독자 회수됐나 : True
[5] 짧게 사는 발행자에 구독 · 해제 안 함 · 오래 사는 발행자 목록 0 · 구독자 회수됐나 : True
[6] 구독자와 무관한 정적 메서드로 구독 · 오래 사는 발행자 목록 1 · 구독자 회수됐나 : True
[7] 발행자가 목록을 비운 뒤 [2] 구독자 회수됐나 : True
[8] 발행자가 목록을 비운 뒤 [3] 구독자 회수됐나 : True
===== csc -nullable:enable -out:ex.dll cs29b-leak.cs && DOTNET_TieredCompilation=0 dotnet ex.dll (cc exit=0 · run exit=0) =====
[1] 메서드로 구독 · 해제함 · 오래 사는 발행자 목록 0 · 구독자 회수됐나 : True
[2] 메서드로 구독 · 해제 안 함 · 오래 사는 발행자 목록 1 · 구독자 회수됐나 : False
[3] 람다로 구독 · 새 람다로 해제 · 오래 사는 발행자 목록 1 · 구독자 회수됐나 : False
[4] 람다를 변수에 두고 · 같은 변수로 해제 · 오래 사는 발행자 목록 0 · 구독자 회수됐나 : True
[5] 짧게 사는 발행자에 구독 · 해제 안 함 · 오래 사는 발행자 목록 0 · 구독자 회수됐나 : True
[6] 구독자와 무관한 정적 메서드로 구독 · 오래 사는 발행자 목록 1 · 구독자 회수됐나 : True
[7] 발행자가 목록을 비운 뒤 [2] 구독자 회수됐나 : True
[8] 발행자가 목록을 비운 뒤 [3] 구독자 회수됐나 : True
===== csc -nullable:enable -optimize -out:exo.dll cs29b-leak.cs && dotnet exo.dll (cc exit=0 · run exit=0) =====
[1] 메서드로 구독 · 해제함 · 오래 사는 발행자 목록 0 · 구독자 회수됐나 : True
[2] 메서드로 구독 · 해제 안 함 · 오래 사는 발행자 목록 1 · 구독자 회수됐나 : False
[3] 람다로 구독 · 새 람다로 해제 · 오래 사는 발행자 목록 1 · 구독자 회수됐나 : False
[4] 람다를 변수에 두고 · 같은 변수로 해제 · 오래 사는 발행자 목록 0 · 구독자 회수됐나 : True
[5] 짧게 사는 발행자에 구독 · 해제 안 함 · 오래 사는 발행자 목록 0 · 구독자 회수됐나 : True
[6] 구독자와 무관한 정적 메서드로 구독 · 오래 사는 발행자 목록 1 · 구독자 회수됐나 : True
[7] 발행자가 목록을 비운 뒤 [2] 구독자 회수됐나 : True
[8] 발행자가 목록을 비운 뒤 [3] 구독자 회수됐나 : True
===== csc -nullable:enable -optimize -out:exo.dll cs29b-leak.cs && DOTNET_TieredCompilation=0 dotnet exo.dll (cc exit=0 · run exit=0) =====
[1] 메서드로 구독 · 해제함 · 오래 사는 발행자 목록 0 · 구독자 회수됐나 : True
[2] 메서드로 구독 · 해제 안 함 · 오래 사는 발행자 목록 1 · 구독자 회수됐나 : False
[3] 람다로 구독 · 새 람다로 해제 · 오래 사는 발행자 목록 1 · 구독자 회수됐나 : False
[4] 람다를 변수에 두고 · 같은 변수로 해제 · 오래 사는 발행자 목록 0 · 구독자 회수됐나 : True
[5] 짧게 사는 발행자에 구독 · 해제 안 함 · 오래 사는 발행자 목록 0 · 구독자 회수됐나 : True
[6] 구독자와 무관한 정적 메서드로 구독 · 오래 사는 발행자 목록 1 · 구독자 회수됐나 : True
[7] 발행자가 목록을 비운 뒤 [2] 구독자 회수됐나 : True
[8] 발행자가 목록을 비운 뒤 [3] 구독자 회수됐나 : True
===== 네 판 대조 — 「회수됐나」 줄마다 네 판의 참/거짓이 같은가 =====
네 판에서 갈린 줄 0 / 8 · 첫 판에서 「회수됨(True)」 줄 6 / 8
```

- ★★★ **네 판에서 갈린 줄 0 / 8 · 첫 판에서 「회수됨(True)」 줄 6 / 8** — `csc` 기본/`-optimize` × 티어링 기본/`TC=0` 에서 같다.
- ★★★ **`[2]` 해제 안 함 → `False`** · **`[3]` 새 람다로 해제 → `False`**(목록 길이가 **1** 로 남았다 — (3) `[5]` 와 같은 이유) — 오래 사는 발행자의 호출 목록이 **델리게이트 → `Target` → 구독자 → 10MB `big`** 을 붙든다.
- ★★★ **`[1]` 해제함 · `[4]` 같은 변수로 해제 → `True`** — 목록에서 빠지면 풀린다.
- ★★★ **`[5]` 짧게 사는 발행자에 구독하고 해제 안 함 → `True`** — **해제를 안 해도 새지 않았다.** 붙드는 쪽은 **발행자**다 — 발행자가 먼저 죽으면 명단째 사라진다. **구독자는 발행자를 붙들지 않는다.**
- ★★ **`[6]` 정적 메서드로 구독 → `True`** — 목록은 1 이지만 정적 메서드의 델리게이트는 **구독자 객체를 대상으로 잡지 않는다** — 사슬이 구독자에 닿지 않는다.
- ★★ **`[7]`·`[8]` 발행자가 목록을 비우면 `[2]`·`[3]` 도 `True`** — 누수는 **목록에 남은 한 줄**이 전부다.

```text
   누가 누구를 붙드나 — 화살표 = 「도달 가능」

   longLived (static 배열 — GC 루트)
     └▶ Pub ─▶ Tick 호출 목록 ─▶ Action ─Target─▶ Sub ─▶ byte[10MB]        [2] False
                                  (s.OnTick)

   Sub ─ ─ ─ ✕ ─ ─ ─▶ Pub       ★ 구독자는 발행자를 가리키지 않는다

   shortLived (지역 — 메서드가 끝나면 루트가 아님)
     └▶ Pub ─▶ 목록 ─▶ Action ─▶ Sub                                        [5] True
        ★ 사슬의 머리가 루트가 아니면 사슬 전체가 쓰레기다

   ★★★ 28번 (5)는 「람다가 → 디스플레이 객체를」 붙들었다. 여기는 「발행자의 목록이 → 구독자를」 붙든다.
       GC 의 규칙은 하나다 — 루트에서 닿으면 산다. 달라진 것은 사슬의 모양뿐이다.
```

### (5) ★★ `add`/`remove` 접근자를 직접 쓰면

```text
===== 소스: cs29b-acc.cs =====
using System;
class Pub {
    Action? store;
    public event Action Tick {
        add { Console.WriteLine($"  add    ← {value.Method.Name}"); store += value; }
        remove { Console.WriteLine($"  remove ← {value.Method.Name}"); store -= value; }
    }
    public void Raise() => store?.Invoke();
}
class Program {
    static void A() => Console.WriteLine("  A 실행");
    static void B() => Console.WriteLine("  B 실행");
    static void Main() {
        var p = new Pub();
        Console.WriteLine("[1] p.Tick += A; p.Tick += B;");
        p.Tick += A; p.Tick += B;
        Console.WriteLine("[2] p.Raise()");
        p.Raise();
        Console.WriteLine("[3] p.Tick -= A; p.Raise()");
        p.Tick -= A; p.Raise();
    }
}
===== csc -nullable:enable -out:ex.dll cs29b-acc.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
[1] p.Tick += A; p.Tick += B;
  add    ← A
  add    ← B
[2] p.Raise()
  A 실행
  B 실행
[3] p.Tick -= A; p.Raise()
  remove ← A
  B 실행
```

- ★★★ **바깥의 `p.Tick += A` 가 `add` 블록을 부른다** — `value` 가 `A` 다. `-= A` 는 `remove` 를 부른다. (2)의 `callvirt add_E` 가 **사용자 코드로 바뀐** 것이다.
- ★★ **저장은 발행자가 정한다** — 여기서는 `store` 필드에 `+=` 했다. 딕셔너리·약한 참조 목록 등 **무엇에든** 담을 수 있다 — 그 대가로 (1)의 **`CS0079`** 처럼 안에서도 `Tick()` 을 못 부르고 `store` 를 직접 부른다(`Raise`).

### (6) ★ 판 경계 · 금지 사례

- ★ **이벤트 타입이 델리게이트가 아니면 `CS0066`** — (문법의 형태 블록 끝). `event` 는 **델리게이트 위에서만** 선다.

## 문법 — 형태와 규칙

### 형태

```text
===== 소스: cs29b-form.cs =====
using System;
var t = new Thermo();
t.Changed += (sender, e) => Console.WriteLine($"{((Thermo)sender!).Name} : {e.Old} → {e.New}");
t.Set(21); t.Set(23);
class TempChangedEventArgs(int old, int now) : EventArgs { public int Old => old; public int New => now; }
class Thermo {
    int value = 20;
    public string Name => "thermo";
    public event EventHandler<TempChangedEventArgs>? Changed;
    protected virtual void OnChanged(TempChangedEventArgs e) => Changed?.Invoke(this, e);
    public void Set(int v) { var old = value; value = v; OnChanged(new TempChangedEventArgs(old, v)); }
}
===== csc -nullable:enable -out:ex.dll cs29b-form.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
thermo : 20 → 21
thermo : 21 → 23
===== 소스: cs29b-bad.cs =====
class Pub {
    public event int Count;
}
===== csc -target:library -out:b29.dll cs29b-bad.cs (cc exit=1) =====
cs29b-bad.cs(2,22): error CS0066: 'Pub.Count': event must be of a delegate type
```

- ★★★ **`.NET` 관례** — `EventHandler<TEventArgs>`(인자 `object? sender, TEventArgs e`) · 발생은 **`protected virtual void OnXxx(…)`** 안에서 **`?.Invoke(this, e)`**. 언어가 강제하는 것은 **「델리게이트 타입」** 까지이고, 두 인자 모양은 **관례**다(`Action` 이벤트도 (1)(3)에서 통과했다).
- ★★ **`protected virtual OnChanged`** — (1)에서 파생 클래스가 `E()` 를 못 불렀으니, **파생 클래스에 발생을 열어 주는 길**이 이것이다(Learn 예제도 같다).

### 금지 사례 — 진단이 나는 꼴

| 쓴 꼴 | 진단 코드 | 어디서 |
|---|---|---|
| 바깥·파생에서 필드형 이벤트에 `=` · `E()` · `= null` · `GetInvocationList` | `CS0070` | (1) |
| 접근자를 쓴 이벤트에 안에서도 `=` · `C()` · `= null` · `GetInvocationList` | `CS0079` | (1) |
| 델리게이트가 아닌 타입의 이벤트(`event int`) | `CS0066` | (형태) |
| ★★★ 같은 모양의 **새 람다**로 `-=` | ★★★ **진단 없음** — 안 떼어진다 | (3)(4) |
| ★★★ 구독 해제 누락 | ★★★ **진단 없음** — 구독자가 안 풀린다 | (4) |

## 어디서 틀리나

1. ★★★ **「`event` 는 델리게이트에 기능을 더한다」** — **줄인다.** 바깥에서 쓸 수 있는 식이 **여섯에서 둘**로 준다((1)).
2. ★★★ **「파생 클래스는 부모의 이벤트를 발생시킬 수 있다」** — 필드형 이벤트는 **`CS0070`**. `protected` 메서드로 열어야 한다((1) · 형태).
3. ★★★ **「`-=` 에 같은 모양의 람다를 주면 떼어진다」** — **안 떼어진다**, 조용히((3) `[5]` · (4) `[3]`).
4. ★★★ **「구독 해제를 안 하면 항상 샌다」** — **발행자가 구독자보다 오래 살 때만** 샌다((4) `[5]` `True`).
5. ★★★ **「구독자가 발행자를 붙든다」** — 반대다. **발행자의 목록이 구독자를** 붙든다((4) 그림).
6. ★★ **「`Tick()` 로 발생시키면 된다」** — 구독자가 없으면 `null` 이라 **`NullReferenceException`**((3) `[2]`).
7. ★★ **「이벤트는 필드가 아니다」** — 필드형 이벤트에는 **같은 이름의 `private` 필드가 있다**((2)). 접근자를 직접 쓴 이벤트에만 **없다.**
8. ★ **「`add` 는 `Combine` 한 번」** — Roslyn 은 **`CompareExchange` 고리**를 만든다((2)).

## 구현 세부사항 대 언어 보장

| 무엇 | 층 | 근거 |
|---|---|---|
| **바깥(파생 포함)에서 필드형 이벤트는 `+=`·`-=` 의 왼쪽에만** | ★★★ **언어(334)** | (1) `CS0070` |
| **접근자를 쓴 이벤트는 안에서도 `+=`·`-=` 만** | ★★★ **언어(334)** | (1) `CS0079` |
| **이벤트 타입은 델리게이트** | ★★★ **언어** | `CS0066` |
| **이벤트 = 메타데이터 항목 + `add_`/`remove_`(`specialname`)** | ★★ **CLI(335)** | (2) |
| **숨은 필드의 이름이 이벤트와 같다** | ★★★ **Roslyn 구현** | (2) |
| **`add_E` 의 `CompareExchange` 고리** | ★★★ **Roslyn 구현** | (2) |
| **`-=` 가 같은 대상 + 같은 메서드를 찾는다** | ★★ **런타임(`Delegate.Remove`) + 언어** | (3) |
| **목록에 남은 구독자는 안 풀린다** | ★★ **GC 규칙의 귀결** | (4) |

## 언제 쓰고 언제 안 쓰나

- ★★★ **밖에 알림을 여는 델리게이트는 `event` 로 선언해라** — `public Action` 필드는 바깥이 **남의 구독을 지우고 대신 방송**할 수 있다((1) `field·outside` 전부 `ok`).
- ★★★ **짧게 사는 구독자가 오래 사는 발행자를 구독하면 반드시 떼라** — 뗄 수 있게 **델리게이트를 변수·필드에 들고 있어라**(람다를 바로 넣으면 **뗄 방법이 없다** — (4) `[3]`).
- ★★ **발생은 `?.Invoke`**((3)) · **파생 클래스에는 `protected virtual OnXxx`**(형태).
- ★★ **접근자를 직접 쓰는 것은 저장 방식을 바꿀 때만** — 이벤트가 수십 개인데 대부분 비어 있는 컨트롤 같은 경우. 대가는 **안에서도 목록을 직접 못 부른다**((1)(5)).
- ★ **구독자 하나가 던지면 뒤가 안 불린다** — 발행자가 그것을 막고 싶으면 `GetInvocationList()` 를 **안에서** 돌며 각각 `try` 해야 한다([27번](../27-delegates-and-func-action/) (4) `[3]`\~`[4]`).

## 핵심 문장

1. ★★★ **`event` 는 델리게이트 필드를 숨기고 바깥에 `add`/`remove` 둘만 연다** — 바깥·파생에서 나머지 넷은 `CS0070`(막힌 칸 12 / 30)((1)).
2. ★★★ **바깥의 `+=` 는 `callvirt add_E` 이고, `add_E` 는 `CompareExchange` 고리다** — 필드의 `+=` 는 호출자가 직접 `stfld` 한다((2)).
3. ★★★ **누수는 「발행자의 목록 → 구독자」 사슬이다** — 해제 안 함·새 람다로 해제는 `False`, **발행자가 짧게 살면 해제 안 해도 `True`**((4)).
4. ★★ **`-=` 는 같은 델리게이트를 찾는다** — 같은 모양의 새 람다로는 안 떼어진다((3)).
5. ★★ **접근자를 직접 쓰면 필드가 없어져 안에서도 `CS0079`** 다((1)(5)).

## 관련 자료

- [27번 — 델리게이트](../27-delegates-and-func-action/) — **경계**: 멀티캐스트의 호출 순서·반환값·중간 예외·`-=` 규칙은 거기가 정본. 여기는 **`event` 가 그 위에서 무엇을 막나.**
- [28번 — 람다와 캡처](../28-lambdas-and-closure-capture/) — **경계**: `WeakReference` 로 「회수됐나」를 묻는 방법 · 캡처가 수명을 늘리는 것은 거기. 여기는 **호출 목록이 붙드는** 경우.
- [13번 — 속성](../13-properties-init-required-field/) — 속성이 `get_`/`set_` 가 되는 것. (2)의 `add_`/`remove_` 가 같은 모양.
- [30번 — 확장 메서드](../30-extension-methods-and-extension-members/) — 같은 델리게이트 줄기의 다음 주제(27에서 갈라진다).

## 용어 풀이

- **이벤트(event)** — 델리게이트 타입의 멤버. 바깥에는 **구독(`+=`)·해제(`-=`)** 만 연다.
- **필드형 이벤트(field-like event)** — 접근자 없이 `public event Action? E;` 로 선언한 이벤트. 컴파일러가 **숨은 필드**와 `add`/`remove` 를 만든다.
- **이벤트 접근자(`add`/`remove`)** — `+=`·`-=` 가 부르는 두 메서드. 직접 쓰면 **저장 방식을 고를 수 있다.**
- **발행자(publisher) · 구독자(subscriber)** — 이벤트를 선언하고 발생시키는 쪽 · 거기에 처리기를 붙이는 쪽.
- **호출 목록(invocation list)** — 멀티캐스트 델리게이트가 순서대로 부를 델리게이트들([27번](../27-delegates-and-func-action/)).
- **`specialname`** — 메타데이터 표지. 속성·이벤트·연산자가 만든 메서드(`get_P`·`add_E`)에 붙는다.
- **`Interlocked.CompareExchange`** — 「값이 아직 내가 읽은 그 값이면 새 값으로 바꾼다」를 **원자적으로** 하는 메서드.

## 더 들어가면

- ★ **`partial` 이벤트(C# 14)** — 정의 선언은 필드형, 구현 선언은 `add`/`remove`(Learn). **이 판에서 안 던졌다.**
- ★ **약한 이벤트 패턴** — 구독자를 `WeakReference` 로 들고 있는 접근자((5)의 저장 자리를 바꾸는 것). **안 짰다.**
- ★ **`add_E` 의 고리가 실제로 구독을 잃지 않는지** — 여러 스레드로 경쟁을 걸어 **필드판과 견주는 실험**은 안 돌렸다((2) 그림은 IL 모양에서 읽은 것).
