# csharp/syntax/18 — `record` 와 값 동등성·`with` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [ECMA-334 7판(2023-12)](https://ecma-international.org/publications-and-standards/standards/ecma-334/) ·
> [Learn — Records](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/builtin-types/record)(열어서 확인: 합성 멤버 목록 · 「위치 속성은 `record class`·`readonly record struct` 에서 `init`, `record struct` 에서 읽기·쓰기」 ·\
> 「`Equals(object)` 를 직접 선언하면 에러」 · 「`Equals(R)` 를 직접 쓰면 `GetHashCode` 도 써라」 · 「`with` 는 복제 메서드를 부른 뒤 속성을 설정한다」 · 「복제 메서드의 실제 이름은 컴파일러가 만든다」)
> **실행 검증** — 이 문서의 모든 출력·진단·IL·할당 바이트는 아래 「이 판」의 도구로 **실제로 돌려 얻은 것**이다(2026-09-26).\
> ★ 블록은 캡처 스크립트가 파일로 받아 조립기가 끼워 넣은 것이다 — 사람이 옮겨 적은 줄은 하나도 없다.\
> ★★★ **진단 언어를 영어로 고정했다**(`DOTNET_CLI_UI_LANGUAGE=en` + `-preferreduilang:en-US`).\
> **대비는 실측이다** — **javac 21.0.5 · 25.0.1** 로 `with` 를 던졌다((7)).
> **버전** — **`record`(class) 는 C# 9** · **`record struct`·`readonly record struct` 는 C# 10** 이다. `-langversion:latest` 로 던졌다.
> **경계** — **`init` 접근자와 `modreq(IsExternalInit)`** 는 [13번](../13-properties-init-required-field/)이 정본이다 — 여기서는 **record 가 그것을 만든다는 것**만 본다.\
> ★ **`record struct` 를 고르는 기준·방어적 복사**는 [02번](../02-struct-vs-class-choosing/)이 정본이다.\
> ★★★ **동등성 계약 자체**(`Equals`/`GetHashCode`/`==` 가 어긋날 때)는 목록의 **19번 주제**가 정본이다 — **18→19 는 한 사슬이다.**\
> 여기서는 「**record 가 그 셋을 어떻게 만들어 주나**」까지만 본다.
> ★★★ **대비** — Java 갈래 목록([`java/syntax/README.md`](../../../java/syntax/README.md))의 **14번**([`14-records/`](../../../java/syntax/14-records/)) ·\
> Kotlin 갈래 목록([`kotlin/syntax/README.md`](../../../kotlin/syntax/README.md))의 **22번**([`22-data-class-generated-members/`](../../../kotlin/syntax/22-data-class-generated-members/)).
>
> ★★ **흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | 진단 **문구** | ★★★ **진단 코드**(`CS8852`·`CS0111`·`CS8851`)와 **`(행,열)`** |
> | ★★★ **생성된 멤버의 IL 모양**(순서·상수 `-1521134295`·`EqualityComparer<T>` 경유) — **Roslyn 의 구현** | ★★★ **생성된 멤버의 목록**(이름·접근성·`virtual`) — **명세가 정한 것** |
> | **IL 오프셋 폭** | ★★ **옵코드와 호출 대상**(`callvirt RC::<Clone>$`) |
> | ★ **증분의 절댓값 일부** — 한 판에서 잰 바이트 | ★★★ **네 판에서 갈린 줄 수**(스크립트가 센 마지막 줄) |
> | `GetHashCode()` 의 **값** — 이 문서는 **한 번도 안 찍었다** | 두 값의 해시가 **같나 다르나**(목록의 **19번 주제**에서) |

## 이 판

```text
===== dotnet --version && dotnet --list-runtimes | grep NETCore (exit=0) =====
10.0.401
Microsoft.NETCore.App 10.0.12 [/home/jun/.local/opt/dotnet/shared/Microsoft.NETCore.App]
===== javac -version && ~/.sdkman/candidates/java/25.0.1-tem/bin/javac -version (exit=0) =====
javac 21.0.5
javac 25.0.1
```

## 이 갈래가 쓰는 세 층

| 층 | 뜻 | 이 주제에서 근거로 쓰는 것 |
|---|---|---|
| **언어 명세(ECMA-334 · 레코드 기능 명세)** | C# 언어가 약속한 것 | ★★★ **무엇이 생성되나의 목록** — `Equals(R)`·`Equals(object)`·`GetHashCode`·`ToString`·`PrintMembers`·`Deconstruct`·`==`/`!=`·복제 메서드·복사 생성자·`EqualityContract` · 위치 속성이 `init` 인지 `set` 인지 |
| **컴파일러·런타임 구현(Roslyn · CoreCLR)** | 그렇게 만든 것 | ★★★ **그 멤버들의 IL 모양** — 복제 메서드의 이름 `<Clone>$` · `Equals` 첫머리의 참조 비교 · 해시 섞는 상수 |
| **이 판의 관찰** | .NET 10.0.12 · linux-x64 | 진단 문구 · 할당 바이트 · `-warn:9` 가 답한 탐침 수 |

★★★ **이 주제의 선 — 「생성되는 멤버의 목록은 명세, 그 IL 모양은 구현」.**\
Learn 도 「복제 메서드의 **실제 이름은 컴파일러가 만든다**」고 적는다 — **`<Clone>$` 라는 이름은 약속이 아니다.**

## 한눈에 — 쉽게 말하면

**`record` 는 「내용이 같으면 같은 서류」로 취급받는 서류 양식이다.**

관공서 서류를 생각하자.

- **`class`** — 서류 **원본 한 장**. 내용이 같아도 **다른 장이면 다른 서류**다(참조 동등).
- **`record`** — ★★★ **내용이 같으면 같은 서류**다(값 동등). 컴파일러가 **대조 방법**(`Equals`)·**요약 번호**(`GetHashCode`)·**표지 인쇄**(`ToString`)를 **양식에 미리 찍어 준다.**
- **`with`** — 「**복사본을 떠서** 한 칸만 고쳐 주세요」. ★ **원본은 안 건드린다**(비파괴 변경).
- **`EqualityContract`** — 서류 **양식 번호**. ★★★ **내용이 같아도 양식이 다르면 다른 서류**다.
- **얕은 복사** — 복사본에 **첨부된 폴더**(리스트)는 **같은 폴더**를 가리킨다. 폴더 내용을 고치면 원본도 바뀐다.

| 비유 | 실체 | 어디서 보나 |
|---|---|---|
| 양식에 미리 찍힌 대조·요약·표지 | ★★★ **생성 멤버 16개**(record class) | (1) |
| 복사본을 떠서 고치기 | ★★★ **`with` = `<Clone>$` 호출 + `set_X`** | (2) |
| 양식 번호가 다르면 다른 서류 | ★★★ **`EqualityContract`** — 파생 record 는 **같은 값이어도 `!=`** | (4) |
| 첨부 폴더는 같은 폴더 | ★★ **`with` 는 얕다** · 배열 멤버는 **참조로 비교** | (6) |
| 원본 한 장 대 복사본 | ★★ **record class 는 `with` 마다 힙 할당** · record struct 는 0 | (5) |

★★★ **이 주제의 본체 — 「무엇이 생성되나」 격자.** (1)의 리플렉션 출력을 옮긴 것이다.

| 생성 멤버 | `record`(class) | `record struct` | `readonly record struct` | 평범한 `class`(대조) |
|---|---|---|---|---|
| 위치 속성의 `set_` | ★★★ **`init`**(`modreq(IsExternalInit)`) | ★★★ **`set`**(읽기·쓰기) | ★★★ **`init`** | (손으로 쓴 `init`) |
| `Equals(object)` | `public virtual` | `public virtual` | `public virtual` | ✕ |
| `Equals(R)` — `IEquatable<R>` | `public virtual` | `public virtual`(★ 인터페이스 구현이라) | `public virtual` | ✕ |
| `GetHashCode()` · `ToString()` | `public virtual` | `public virtual` | `public virtual` | ✕ |
| `op_Equality` · `op_Inequality` | `public static` | `public static` | `public static` | ✕ |
| `Deconstruct(out …)` | ✔ | ✔ | ✔ | ✕ |
| `PrintMembers(StringBuilder)` | ★ **`protected virtual`** | ★ **`private`** | ★ **`private`** | ✕ |
| **`EqualityContract`** | ★★★ **`protected virtual`** | ★★★ **✕ 없다** | ★★★ **✕ 없다** | ✕ |
| **복제 메서드(`<Clone>$`)** | ★★★ **`public virtual`** | ★★★ **✕ 없다** | ★★★ **✕ 없다** | ✕ |
| **복사 생성자 `.ctor(R)`** | ★★★ **`protected`** | ✕ | ✕ | ✕ |
| 메서드·생성자 합계 | **16** | **13** | **13** | **5** |

- ★★★ **struct 쪽에 없는 셋(`EqualityContract`·복제 메서드·복사 생성자)이 같은 이유다** — 구조체는 **상속이 없고**(양식 번호가 필요 없다)\
  **대입이 곧 복사**다(복제 메서드가 필요 없다). Learn 의 문장 — 「`record struct` 의 값은 **대입 때 복사된다**」.
- ★★★ **`record struct` 만 위치 속성이 `set` 이다** — 이름에 `record` 가 붙었다고 불변이 아니다.

## 이 주제가 답하려는 질문

1. **`record` 한 줄이 무엇을 만드나** — 그리고 **struct 쪽은 무엇이 빠지나**((1)).
2. **`with` 는 실제로 무엇을 부르나**((2)).
3. **생성된 `Equals` 는 무엇을 비교하나** — 그리고 **파생 record 와 기반 record 는 왜 안 같나**((3)(4)).
4. **셋 중 무엇이 불변이고 무엇이 할당하나**((5)).
5. **어디서 조용히 틀리나** — 얕은 복사·배열 멤버·가변 멤버((6)(8)).

## 동작 방식

### (0) 이 주제가 쓰는 창

★★★ **본체 창은 ③ 리플렉션이다** — 「무엇이 생성되나」는 **소스에 한 글자도 없다.** 리플렉션만이 그 목록을 읽는다.

| 창 | 무엇을 보여 주나 | 이 주제에서 |
|---|---|---|
| ★★★ **③ 리플렉션** | ★★★ **생성 멤버 목록**(이름·접근성·`virtual`·`modreq`) — 본체 | (1)(4) |
| ★★★ **① IL 덤프** | ★★★ **`with` → `<Clone>$`** · 생성된 `Equals` 의 **참조 비교 지름길**과 **`EqualityContract` 비교** | (2)(3) |
| ★★ **④ 할당 바이트** | `with` 가 **새 객체를 만드나** — record class 대 struct · **2×2 판 격자** | (5) |
| ★★ **② 진단 격자** | `CS8852`(init 에 대입) · `CS0111`(생성 멤버를 손으로) · `CS8851`(`Equals` 만 손으로) · **탐침 N 중 답한 것** | (5)(8) |

- ★★★ **① 과 ③ 이 짝이다** — ③ 은 「**있다**」를, ① 은 「**무엇을 한다**」를 말한다.\
  ★ ③ 만 보면 `<Clone>$` 가 **있다**는 것만 알고, `with` 가 **그것을 부른다**는 것은 ① 이 말한다.
- ★ **④ 는 「적용」이다** — record class 의 `with` 는 **새 객체를 만든다.** 잴 것이 있다.

### (1) ★★★ 생성 멤버 — 리플렉션으로 전부

**언제 쓰나** — 「`record` 로 바꾸면 무엇이 생기나」를 물을 때. **이 절이 이 주제의 중심이다.**

```text
===== 소스: cs18b-gen.cs =====
using System;
using System.Linq;
using System.Reflection;

public record                 RC(string Name, int Age);    // record class (C# 9)
public record struct          RS(string Name, int Age);    // record struct (C# 10)
public readonly record struct RR(string Name, int Age);    // readonly record struct (C# 10)
public class PC { public string Name { get; init; } = ""; public int Age { get; init; } }   // 대조군 — 평범한 클래스

class Program {
    static string Acc(MethodBase m) =>
        m.IsPublic ? "public" : m.IsFamily ? "protected" : m.IsPrivate ? "private" : m.IsAssembly ? "internal" : "?";
    static void Show(Type t) {
        var ms = t.GetMembers(BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance | BindingFlags.Static | BindingFlags.DeclaredOnly)
                  .OfType<MethodBase>()
                  .Select(m => {
                      var ps  = string.Join(",", m.GetParameters().Select(p => p.ParameterType.Name));
                      var mod = m is MethodInfo mi && mi.ReturnParameter.GetRequiredCustomModifiers().Length > 0 ? " modreq(IsExternalInit)" : "";
                      return $"{Acc(m),-9}{(m.IsStatic ? " static" : "")}{(m.IsVirtual ? " virtual" : "")} {m.Name}({ps}){mod}";
                  })
                  .OrderBy(x => x, StringComparer.Ordinal).ToArray();
        Console.WriteLine($"=== {t.Name} — {(t.IsValueType ? "struct" : "class")} · 메서드·생성자 {ms.Length}개 · 인터페이스 [{string.Join(",", t.GetInterfaces().Select(i => i.Name))}] ===");
        foreach (var x in ms) Console.WriteLine("  " + x);
    }
    static void Main() { Show(typeof(RC)); Show(typeof(RS)); Show(typeof(RR)); Show(typeof(PC)); }
}
===== csc -out:ex.dll cs18b-gen.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
=== RC — class · 메서드·생성자 16개 · 인터페이스 [IEquatable`1] ===
  protected .ctor(RC)
  protected virtual PrintMembers(StringBuilder)
  protected virtual get_EqualityContract()
  public    .ctor(String,Int32)
  public    Deconstruct(String&,Int32&)
  public    get_Age()
  public    get_Name()
  public    set_Age(Int32) modreq(IsExternalInit)
  public    set_Name(String) modreq(IsExternalInit)
  public    static op_Equality(RC,RC)
  public    static op_Inequality(RC,RC)
  public    virtual <Clone>$()
  public    virtual Equals(Object)
  public    virtual Equals(RC)
  public    virtual GetHashCode()
  public    virtual ToString()
=== RS — struct · 메서드·생성자 13개 · 인터페이스 [IEquatable`1] ===
  private   PrintMembers(StringBuilder)
  public    .ctor(String,Int32)
  public    Deconstruct(String&,Int32&)
  public    get_Age()
  public    get_Name()
  public    set_Age(Int32)
  public    set_Name(String)
  public    static op_Equality(RS,RS)
  public    static op_Inequality(RS,RS)
  public    virtual Equals(Object)
  public    virtual Equals(RS)
  public    virtual GetHashCode()
  public    virtual ToString()
=== RR — struct · 메서드·생성자 13개 · 인터페이스 [IEquatable`1] ===
  private   PrintMembers(StringBuilder)
  public    .ctor(String,Int32)
  public    Deconstruct(String&,Int32&)
  public    get_Age()
  public    get_Name()
  public    set_Age(Int32) modreq(IsExternalInit)
  public    set_Name(String) modreq(IsExternalInit)
  public    static op_Equality(RR,RR)
  public    static op_Inequality(RR,RR)
  public    virtual Equals(Object)
  public    virtual Equals(RR)
  public    virtual GetHashCode()
  public    virtual ToString()
=== PC — class · 메서드·생성자 5개 · 인터페이스 [] ===
  public    .ctor()
  public    get_Age()
  public    get_Name()
  public    set_Age(Int32) modreq(IsExternalInit)
  public    set_Name(String) modreq(IsExternalInit)
```

- ★★★ **`record RC` 는 16개**, **`record struct` 둘은 13개**, **평범한 클래스는 5개**다. 위 격자가 이 출력을 옮긴 것이다.
- ★★★ **`protected .ctor(RC)`** — **복사 생성자**. `with` 의 복제가 이것을 쓴다((2)).
- ★★★ **`public virtual <Clone>$()`** — 복제 메서드. ★ **`<` `>` 가 든 이름은 C# 에서 선언할 수 없다** — 그래서 사용자 코드와 원리상 안 부딪힌다.\
  ★★ Learn — 「복제 메서드를 **재정의할 수 없고**, 어떤 record 에도 **`Clone` 이라는 멤버를 만들 수 없다**」.
- ★★★ **`protected virtual get_EqualityContract()`** — record class 에만 있다. (4)의 주인공이다.
- ★★ **`PrintMembers` 가 class 는 `protected virtual`, struct 는 `private`** — 파생 record 가 **자기 멤버를 덧붙여 찍으려면** 열려 있어야 한다. struct 는 파생이 없다.
- ★★★ **`set_Age` 의 `modreq(IsExternalInit)`** — [13번](../13-properties-init-required-field/)이 잰 **`init` 의 표식**이다. **`RS` 에만 없다.**
- ★ **인터페이스는 셋 다 ``IEquatable`1`` 하나** — 목록의 **19번 주제**에서 이것이 **박싱을 피하는 문**임을 본다.

### (2) ★★★ `with` 가 부르는 것 — IL

**언제 쓰나** — 「`with` 는 속성을 바꾸는 문법인가 새 객체를 만드는 문법인가」를 물을 때.

```text
===== 소스: cs18b-with.cs =====
using System;
public record        RC(string Name, int Age);
public record struct RS(string Name, int Age);
static class Probe {
    public static RC WithC(RC r) => r with { Age = 30 };
    public static RS WithS(RS r) => r with { Age = 30 };
}
class Program {
    static void Main() {
        Il.Dump(typeof(Probe), "WithC");
        Il.Dump(typeof(Probe), "WithS");
        Il.Dump(typeof(RC), "<Clone>$");
        // <Clone>$ 의 newobj 가 어느 생성자를 부르는지 — 토큰을 풀어 매개변수 타입을 찍는다
        var il  = typeof(RC).GetMethod("<Clone>$")!.GetMethodBody()!.GetILAsByteArray()!;
        var ctor = typeof(RC).Module.ResolveMethod(BitConverter.ToInt32(il, 2))!;
        Console.WriteLine($"newobj 의 대상 : {ctor.DeclaringType!.Name}({string.Join(",", Array.ConvertAll(ctor.GetParameters(), p => p.ParameterType.Name))}) · public={ctor.IsPublic} protected={ctor.IsFamily}");
    }
}
===== csc -r:il.dll -out:ex.dll cs18b-with.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
--- Probe.WithC ---
  IL_0000: ldarg.0
  IL_0001: callvirt RC::<Clone>$
  IL_0006: dup
  IL_0007: ldc.i4.s 30
  IL_0009: callvirt RC::set_Age
  IL_000e: nop
  IL_000f: ret
--- Probe.WithS ---
  .locals [0] RS
  IL_0000: ldarg.0
  IL_0001: stloc.0
  IL_0002: ldloca.s 0
  IL_0004: ldc.i4.s 30
  IL_0006: call RS::set_Age
  IL_000b: nop
  IL_000c: ldloc.0
  IL_000d: ret
--- RC.<Clone>$ ---
  IL_0000: ldarg.0
  IL_0001: newobj RC::.ctor
  IL_0006: ret
newobj 의 대상 : RC(RC) · public=False protected=True
```

- ★★★ **`WithC` 는 `callvirt RC::<Clone>$` → `dup` → `callvirt RC::set_Age`** 다.\
  **복제한 새 객체에 `init` 세터를 부른다** — `init` 은 원래 **객체 초기자에서만** 되는데 `with` 도 그 자격을 갖는다.
- ★★★ **`<Clone>$` 의 본문은 `newobj RC::.ctor`** 이고, 토큰을 풀어 보니 **`RC(RC)` — `protected` 복사 생성자**다.
- ★★★ **`<Clone>$` 가 `callvirt`(가상)인 이유가 (4)에서 드러난다** — `Pt` 변수에 `Tagged` 가 들었을 때 **`Tagged` 의 복제가 불려** 결과도 `Tagged` 다.
- ★★★ **`WithS`(record struct) 에는 복제가 없다** — `ldarg.0` → `stloc.0`(**대입이 곧 복사**) → `ldloca.s 0` → `call RS::set_Age`.\
  ★ `callvirt` 가 아니라 **`call`** 이다 — 구조체라 널일 수 없다([16번](../16-inheritance-virtual-override-abstract-sealed-new/) (4)).

```text
   record class                                    record struct
   r with { Age = 30 }                             r with { Age = 30 }
        │                                               │
        ▼                                               ▼
   callvirt <Clone>$  ──▶ newobj .ctor(RC)          ldarg.0 / stloc.0       ← 대입이 곧 복사
        │                  (힙에 새 객체)                │                     (스택의 사본)
        ▼                                               ▼
   callvirt set_Age(30)   ← init 세터                call set_Age(30)        ← 보통 세터
        │                                               │
        ▼                                               ▼
   새 참조를 돌려준다                                 사본 값을 돌려준다

   ★★★ 왼쪽은 힙 할당이 있고 오른쪽은 없다 — (5)의 바이트가 이 그림이다.
```

> **어느 층인가** — ★★★ 「`with` 는 **복제한 뒤 설정한다**」는 **명세**(Learn 도 그렇게 적는다).\
> ★★ **`<Clone>$` 라는 이름**과 **`dup` 으로 이어 붙이는 IL 모양**은 **Roslyn 의 구현**이다.

### (3) ★★ 생성된 `Equals`·`GetHashCode`·`==` 의 IL

**언제 쓰나** — 「record 의 `Equals` 는 무엇을 무엇과 비교하나」를 물을 때. ★ 목록의 **19번 주제**의 격자를 읽는 열쇠다.

```text
===== 소스: cs18b-eqil.cs =====
using System;
record Pt(int X);
class Program {
    static void Main() {
        Il.Dump(typeof(Pt), "Equals", typeof(Pt));
        Il.Dump(typeof(Pt), "GetHashCode");
        Il.Dump(typeof(Pt), "op_Equality");
    }
}
===== csc -optimize -r:il.dll -out:ex.dll cs18b-eqil.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
--- Pt.Equals(Pt) ---
  IL_0000: ldarg.0
  IL_0001: ldarg.1
  IL_0002: beq.s IL_0033
  IL_0004: ldarg.1
  IL_0005: brfalse.s IL_0031
  IL_0007: ldarg.0
  IL_0008: callvirt Pt::get_EqualityContract
  IL_000d: ldarg.1
  IL_000e: callvirt Pt::get_EqualityContract
  IL_0013: call System.Type::op_Equality
  IL_0018: brfalse.s IL_0031
  IL_001a: call System.Collections.Generic.EqualityComparer<System.Int32>::get_Default
  IL_001f: ldarg.0
  IL_0020: ldfld Pt::<X>k__BackingField
  IL_0025: ldarg.1
  IL_0026: ldfld Pt::<X>k__BackingField
  IL_002b: callvirt System.Collections.Generic.EqualityComparer<System.Int32>::Equals
  IL_0030: ret
  IL_0031: ldc.i4.0
  IL_0032: ret
  IL_0033: ldc.i4.1
  IL_0034: ret
--- Pt.GetHashCode ---
  IL_0000: call System.Collections.Generic.EqualityComparer<System.Type>::get_Default
  IL_0005: ldarg.0
  IL_0006: callvirt Pt::get_EqualityContract
  IL_000b: callvirt System.Collections.Generic.EqualityComparer<System.Type>::GetHashCode
  IL_0010: ldc.i4 -1521134295
  IL_0015: mul
  IL_0016: call System.Collections.Generic.EqualityComparer<System.Int32>::get_Default
  IL_001b: ldarg.0
  IL_001c: ldfld Pt::<X>k__BackingField
  IL_0021: callvirt System.Collections.Generic.EqualityComparer<System.Int32>::GetHashCode
  IL_0026: add
  IL_0027: ret
--- Pt.op_Equality ---
  IL_0000: ldarg.0
  IL_0001: ldarg.1
  IL_0002: beq.s IL_0011
  IL_0004: ldarg.0
  IL_0005: brfalse.s IL_000f
  IL_0007: ldarg.0
  IL_0008: ldarg.1
  IL_0009: callvirt Pt::Equals
  IL_000e: ret
  IL_000f: ldc.i4.0
  IL_0010: ret
  IL_0011: ldc.i4.1
  IL_0012: ret
```

- ★★★ **`Equals(Pt)` 의 첫 세 줄이 `ldarg.0` · `ldarg.1` · `beq.s`** — **같은 참조면 바로 `true`**(참조 비교 지름길).\
  ★★ 목록의 **19번 주제**에서 **`HashSet` 은 이런 지름길을 안 쓴다**는 것을 본다 — **지름길은 record 의 `Equals` 안에** 있다.
- ★★★ **그다음이 `EqualityContract` 둘을 `Type::op_Equality` 로 비교** — **실제 타입이 같아야** 같다((4)).
- ★★★ **필드마다 `EqualityComparer<int>.Default.Equals`** — ★ 그래서 `double` 멤버는 **`double.Equals`** 로 비교되고\
  **`NaN` 이 `NaN` 과 같다**((8) 탐침 5). 배열 멤버는 **`EqualityComparer<int[]>.Default`** — **참조 비교**다((6)).
- ★★ **`GetHashCode` 도 `EqualityContract` 를 섞는다** — `-1521134295` 를 곱해 필드 해시를 더한다.\
  ★★★ **이 상수와 섞는 방식은 구현이다** — 명세는 「**같은 값이면 같은 해시**」만 약속한다.
- ★★ **`op_Equality` 는 참조가 같으면 `true`, 왼쪽이 널이면 `false`, 아니면 `Equals` 를 부른다** — **`==` 와 `Equals` 가 원리상 안 어긋난다.**\
  ★★★ 목록의 **19번 주제**가 다루는 「`==` 와 `Equals` 가 어긋나는 사고」가 **record 에서는 안 나는 이유**가 이 여섯 줄이다.

### (4) ★★★ `EqualityContract` — 같은 값인데 `!=`

**언제 쓰나** — record 를 **상속**할 때.

```text
===== 소스: cs18b-contract.cs =====
using System;
using System.Reflection;
record Pt(int X);
record Tagged(int X) : Pt(X);                  // 멤버를 하나도 안 더한 파생 record
record Pt3(int X, int Z) : Pt(X);
class Program {
    static string Contract(object o) =>
        ((Type)o.GetType().GetProperty("EqualityContract", BindingFlags.NonPublic | BindingFlags.Instance)!.GetValue(o)!).Name;
    static void Main() {
        Pt a = new Pt(1);
        Pt b = new Tagged(1);
        Console.WriteLine($"a = {a} · b = {b}");
        Console.WriteLine($"a == b : {a == b} · a.Equals(b) : {a.Equals(b)} · b.Equals(a) : {b.Equals(a)}");
        Console.WriteLine($"a.EqualityContract = {Contract(a)} · b.EqualityContract = {Contract(b)}");
        Pt c = b with { X = 2 };
        Console.WriteLine($"Pt 변수 b 에 with : {c} · c.GetType() = {c.GetType().Name}");
        Pt d = new Pt3(1, 9), e = new Pt3(1, 7);
        Console.WriteLine($"Pt 변수로 받은 Pt3(1,9) == Pt3(1,7) : {d == e}");
    }
}
===== csc -out:ex.dll cs18b-contract.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
a = Pt { X = 1 } · b = Tagged { X = 1 }
a == b : False · a.Equals(b) : False · b.Equals(a) : False
a.EqualityContract = Pt · b.EqualityContract = Tagged
Pt 변수 b 에 with : Tagged { X = 2 } · c.GetType() = Tagged
Pt 변수로 받은 Pt3(1,9) == Pt3(1,7) : False
```

- ★★★ **`Pt(1)` 과 `Tagged(1)` 은 멤버가 하나도 안 다른데 `a == b` 가 `False`** 다.\
  **`a.Equals(b)` 도 `b.Equals(a)` 도 `False`** — ★★★ **대칭이다.**
- ★★★ **`EqualityContract` 가 `Pt` 대 `Tagged`** — (3)의 `Type::op_Equality` 에서 갈렸다.
- ★★★ **왜 이렇게 설계했나 — 대칭성 때문이다.** 계약형 `Equals` 를 손으로 쓰면 흔히\
  「`Pt` 는 `X` 만 보고 `Tagged` 는 `X` 와 타입을 본다」가 되어 **`a.Equals(b)` 와 `b.Equals(a)` 가 갈린다** — 목록의 **19번 주제**의 `R5` 모양이다.\
  record 는 **양쪽이 똑같이 「실제 타입 + 멤버」를 본다**.
```text
   Pt a = new Pt(1)                    Pt b = new Tagged(1)
   ┌───────────────────────┐          ┌───────────────────────┐
   │ EqualityContract = Pt │          │ EqualityContract = Tagged │
   │ X = 1                 │          │ X = 1                 │
   └───────────────────────┘          └───────────────────────┘

   a.Equals(b):  ① 같은 참조?  아니오
                 ② b 가 null?  아니오
                 ③ Pt == Tagged ?  ★ 아니오  → false   (X 는 보지도 않는다)
   b.Equals(a):  ③ Tagged == Pt ?  ★ 아니오  → false   ← 같은 규칙이라 대칭

   ★★★ 멤버가 같아도 「양식 번호」가 다르면 다르다 — 그리고 양쪽이 똑같이 그렇게 본다.
```

- ★★ **`Pt` 변수 `b` 에 `with` 를 해도 결과가 `Tagged`** 다 — `<Clone>$` 가 **가상**이기 때문이다((2)).\
  ★ Learn — 「`with` 결과는 **피연산자의 런타임 타입**을 갖는다」.
- ★ **`Pt3(1,9)` 와 `Pt3(1,7)` 은 `Pt` 변수로 받아도 `False`** — **파생 멤버 `Z` 까지** 비교한다. **정적 타입이 아니라 런타임 타입**이 정한다.

### (5) ★★ `record` 대 `record struct` 대 `readonly record struct`

**언제 쓰나** — 셋 중 무엇을 고를지.

```text
===== 소스: cs18b-mut.cs =====
record                 RC(int X);
record struct          RS(int X);
readonly record struct RR(int X);
class Program {
    static void Main() {
        var c = new RC(1);
        c.X = 2;
        var s = new RS(1);
        s.X = 2;
        var r = new RR(1);
        r.X = 2;
    }
}
===== csc -out:ex.dll cs18b-mut.cs 2>&1 | sort (cc exit=1) =====
cs18b-mut.cs(11,9): error CS8852: Init-only property or indexer 'RR.X' can only be assigned in an object initializer, or on 'this' or 'base' in an instance constructor or an 'init' accessor.
cs18b-mut.cs(7,9): error CS8852: Init-only property or indexer 'RC.X' can only be assigned in an object initializer, or on 'this' or 'base' in an instance constructor or an 'init' accessor.
```

- ★★★ **`RC.X` 와 `RR.X` 에 대입하면 `CS8852`**(init 전용), **`RS.X` 는 조용히 통과**한다(8번 줄에 진단이 없다).\
  ★★★ **`record struct` 는 가변이다** — (1)의 `set_Age` 에 `modreq` 가 없던 그것이다.\
  ★ [02번](../02-struct-vs-class-choosing/)은 `readonly record struct` 만 던졌다 — **이 판이 `record struct` 의 가변을 처음 찍었다.**

할당 바이트를 2×2 판 격자로 쟀다(규칙 24).

```text
===== 소스: cs18b-alloc.cs =====
using System;
record                 RC(int X, int Y);
record struct          RS(int X, int Y);
readonly record struct RR(int X, int Y);
class Program {
    static long M(Action a) {
        a();                                             // 한 판 데워 놓고
        var b = GC.GetAllocatedBytesForCurrentThread();
        a();
        return GC.GetAllocatedBytesForCurrentThread() - b;
    }
    static void Main() {
        int sink = 0;
        var c = new RC(1, 2); var s = new RS(1, 2); var r = new RR(1, 2);
        var c2 = new RC(1, 2); var s2 = new RS(1, 2); var r2 = new RR(1, 2);
        Console.WriteLine($"with RC           1000회 : {M(() => { for (int i = 0; i < 1000; i++) sink += (c with { X = i }).X; })} 바이트");
        Console.WriteLine($"with RS           1000회 : {M(() => { for (int i = 0; i < 1000; i++) sink += (s with { X = i }).X; })} 바이트");
        Console.WriteLine($"with RR           1000회 : {M(() => { for (int i = 0; i < 1000; i++) sink += (r with { X = i }).X; })} 바이트");
        Console.WriteLine($"== RC             1000회 : {M(() => { for (int i = 0; i < 1000; i++) sink += c == c2 ? 1 : 0; })} 바이트");
        Console.WriteLine($"== RS             1000회 : {M(() => { for (int i = 0; i < 1000; i++) sink += s == s2 ? 1 : 0; })} 바이트");
        Console.WriteLine($"== RR             1000회 : {M(() => { for (int i = 0; i < 1000; i++) sink += r == r2 ? 1 : 0; })} 바이트");
        Console.WriteLine($"RS.Equals(object) 1000회 : {M(() => { for (int i = 0; i < 1000; i++) sink += s.Equals((object)s2) ? 1 : 0; })} 바이트");
        Console.WriteLine($"(합 {sink})");
    }
}
===== csc -out:ex.dll cs18b-alloc.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
with RC           1000회 : 24000 바이트
with RS           1000회 : 0 바이트
with RR           1000회 : 0 바이트
== RC             1000회 : 0 바이트
== RS             1000회 : 0 바이트
== RR             1000회 : 0 바이트
RS.Equals(object) 1000회 : 24000 바이트
(합 3005000)
===== csc -out:ex.dll cs18b-alloc.cs && DOTNET_TieredCompilation=0 dotnet ex.dll (cc exit=0 · run exit=0) =====
with RC           1000회 : 24000 바이트
with RS           1000회 : 0 바이트
with RR           1000회 : 0 바이트
== RC             1000회 : 0 바이트
== RS             1000회 : 0 바이트
== RR             1000회 : 0 바이트
RS.Equals(object) 1000회 : 24000 바이트
(합 3005000)
===== csc -optimize -out:exo.dll cs18b-alloc.cs && dotnet exo.dll (cc exit=0 · run exit=0) =====
with RC           1000회 : 24000 바이트
with RS           1000회 : 0 바이트
with RR           1000회 : 0 바이트
== RC             1000회 : 0 바이트
== RS             1000회 : 0 바이트
== RR             1000회 : 0 바이트
RS.Equals(object) 1000회 : 24000 바이트
(합 3005000)
===== csc -optimize -out:exo.dll cs18b-alloc.cs && DOTNET_TieredCompilation=0 dotnet exo.dll (cc exit=0 · run exit=0) =====
with RC           1000회 : 24000 바이트
with RS           1000회 : 0 바이트
with RR           1000회 : 0 바이트
== RC             1000회 : 0 바이트
== RS             1000회 : 0 바이트
== RR             1000회 : 0 바이트
RS.Equals(object) 1000회 : 24000 바이트
(합 3005000)
===== 네 판 대조 — 「바이트」 줄마다 네 판의 값이 같은가 =====
네 판에서 갈린 줄 0 / 7
```

- ★★★ **`with RC` 만 1000회에 24000 바이트** — 한 번에 24바이트, **`int` 둘을 가진 객체 하나**다. `<Clone>$` 의 `newobj` 가 그것이다.
- ★★★ **`with RS`·`with RR` 은 0** — 스택의 사본이다((2)의 그림).
- ★★ **`==` 는 셋 다 0** — 생성된 `op_Equality` 가 **`Equals(R)`**(`IEquatable<R>`)를 부르니 박싱이 없다.
- ★★ **`RS.Equals(object)` 는 24000** — `(object)s2` 로 넘기는 순간 **인자가 박싱**된다. **`Equals(RS)` 를 쓰면 0**(`==` 줄).
- ★★★ **네 판에서 갈린 줄 0 / 7.** 근거로 쓸 수 있다.

| 판 | `with RC` | `with RS`·`RR` | `==` 셋 | `RS.Equals(object)` | 움직였나 |
|---|---|---|---|---|---|
| 기본 | 24000 | 0 | 0 | 24000 | — |
| `DOTNET_TieredCompilation=0` | 24000 | 0 | 0 | 24000 | ★ 안 움직임 |
| `csc -optimize` | 24000 | 0 | 0 | 24000 | ★ 안 움직임 |
| 둘 다 | 24000 | 0 | 0 | 24000 | ★ 안 움직임 |

- ★★★ **이 표는 「`record struct` 가 빠르다」가 아니다** — 잰 것은 **할당 바이트**이고 **시간은 안 쟀다.**\
  ★ 구조체는 **대입마다 복사**하므로, 멤버가 많으면 **복사 비용**이 커진다 — 그것도 **안 쟀다.** 고르는 기준은 [02번](../02-struct-vs-class-choosing/)이다.

### (6) ★★ 얕다 — `with` 와 배열 멤버

**언제 쓰나** — record 에 **배열·리스트**를 담을 때.

```text
===== 소스: cs18b-shallow.cs =====
using System;
using System.Collections.Generic;
record Arr(int[] Xs);
record Bag(List<int> Xs);
class Program {
    static void Main() {
        Console.WriteLine($"[1] new Arr(new[] {{1,2}}) == new Arr(new[] {{1,2}}) : {new Arr(new[] { 1, 2 }) == new Arr(new[] { 1, 2 })}");
        var shared = new[] { 1, 2 };
        Console.WriteLine($"[2] new Arr(shared) == new Arr(shared)         : {new Arr(shared) == new Arr(shared)}");
        var a = new Bag(new List<int> { 1 });
        var b = a with { };
        b.Xs.Add(2);
        Console.WriteLine($"[3] b.Xs.Add(2) 뒤 a.Xs.Count                   : {a.Xs.Count}");
        Console.WriteLine($"[4] ReferenceEquals(a, b) : {ReferenceEquals(a, b)} · ReferenceEquals(a.Xs, b.Xs) : {ReferenceEquals(a.Xs, b.Xs)}");
        Console.WriteLine($"[5] a == b                                     : {a == b}");
        Console.WriteLine($"[6] a.ToString()                               : {a}");
    }
}
===== csc -out:ex.dll cs18b-shallow.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
[1] new Arr(new[] {1,2}) == new Arr(new[] {1,2}) : False
[2] new Arr(shared) == new Arr(shared)         : True
[3] b.Xs.Add(2) 뒤 a.Xs.Count                   : 2
[4] ReferenceEquals(a, b) : False · ReferenceEquals(a.Xs, b.Xs) : True
[5] a == b                                     : True
[6] a.ToString()                               : Bag { Xs = System.Collections.Generic.List`1[System.Int32] }
```

- ★★★ **`[1]` 내용이 같은 배열 둘은 `False`**, **`[2]` 같은 배열 하나를 넣은 둘은 `True`** —\
  배열 멤버는 `EqualityComparer<int[]>.Default` 로 비교되고, 배열은 `Equals` 를 안 고쳤으니 **참조 비교**다((3)).
- ★★★ **`[3]` `b.Xs.Add(2)` 뒤 `a.Xs.Count` 가 `2`** — `with` 는 **리스트를 복사하지 않고 참조를 복사**한다.\
  **`[4]` 가 증거다** — 두 record 는 다른 객체(`False`)인데 **두 리스트는 같은 객체**(`True`)다.
- ★★ **`[5]` 그래서 `a == b` 가 `True`** — 같은 리스트를 가리키니 멤버가 같다. ★ 「**다른 복사본인데 같다**」가 아니라 「**속이 공유돼서 같다**」이다.
- ★ **`[6]` `ToString` 은 리스트 내용을 안 찍는다** — ``List`1[System.Int32]`` 다. 로그로 내용을 확인할 수 없다.

### (7) ★★ Java `record` 와 대비 — `with` 가 없다

```text
===== 소스: j18/Ex18.java =====
record Pt(int x, int y) { }
public class Ex18 {
    public static void main(String[] a) {
        Pt p = new Pt(1, 2);
        Pt q = p with { x = 9; };            // C# 의 with 를 그대로 쓴다
        System.out.println(q);
    }
}
===== javac -d j18out j18/Ex18.java (cc exit=1) =====
j18/Ex18.java:5: error: ';' expected
        Pt q = p with { x = 9; };            // C# 의 with 를 그대로 쓴다
                ^
j18/Ex18.java:5: error: not a statement
        Pt q = p with { x = 9; };            // C# 의 with 를 그대로 쓴다
                 ^
j18/Ex18.java:5: error: ';' expected
        Pt q = p with { x = 9; };            // C# 의 with 를 그대로 쓴다
                     ^
3 errors
===== ~/.sdkman/candidates/java/25.0.1-tem/bin/javac --enable-preview --release 25 -d j18out25 j18/Ex18.java (cc exit=1) =====
j18/Ex18.java:5: error: ';' expected
        Pt q = p with { x = 9; };            // C# 의 with 를 그대로 쓴다
                ^
j18/Ex18.java:5: error: not a statement
        Pt q = p with { x = 9; };            // C# 의 with 를 그대로 쓴다
                 ^
j18/Ex18.java:5: error: ';' expected
        Pt q = p with { x = 9; };            // C# 의 with 를 그대로 쓴다
                     ^
3 errors
===== 소스: j18/Ex18b.java =====
record Pt(int x, int y) {
    Pt withX(int nx) { return new Pt(nx, y); }      // 손으로 쓴 wither
}
public class Ex18b {
    public static void main(String[] a) {
        Pt p = new Pt(1, 2);
        System.out.println(p + " -> " + p.withX(9) + " · p.equals(new Pt(1, 2)) = " + p.equals(new Pt(1, 2)));
    }
}
===== javac -d j18out j18/Ex18b.java && java -cp j18out Ex18b (cc exit=0 · run exit=0) =====
Pt[x=1, y=2] -> Pt[x=9, y=2] · p.equals(new Pt(1, 2)) = true
```

- ★★★ **javac 21 은 `with` 를 문법으로 모른다** — `';' expected` · `not a statement`. **파서 단계에서** 막혔다.
- ★★★ **javac 25 에 `--enable-preview` 를 줘도 같다** — 이 판에서 Java 에는 `with` 에 해당하는 문법이 **미리보기로도 없다.**
- ★★ **Java 는 손으로 `withX` 를 쓴다**(`Pt[x=9, y=2]`). 동등성은 **같다**(`p.equals(new Pt(1, 2)) = true`).
- ★ Java record 의 `equals`/`hashCode`/`toString` 이 **`invokedynamic` 한 줄**이라는 것은 [Java 14번](../../../java/syntax/14-records/)이 잰 것이다.\
  **C# 은 (3)에서 본 대로 IL 로 풀어서 박는다** — 같은 기능을 **컴파일 때 짜느냐 런타임에 짜느냐**가 갈린다.
- ★ Kotlin `data class` 의 `copy` 는 **본문 프로퍼티를 초기값으로 되돌린다**는 것이 [Kotlin 22번](../../../kotlin/syntax/22-data-class-generated-members/)의 결론이다.\
  C# `with` 는 **복사 생성자가 모든 필드를 복사**하므로 그 모양이 아니다((형태)의 `Label` 이 `민수(31)` 로 따라 바뀐 것은 **계산 속성**이라서다). ★ **본문의 `init` 속성**으로는 **이 판에서 던지지 않았다.**

```text
                         C# record               Java record              Kotlin data class
   비파괴 변경            with { X = 1 }           ✕ 문법 없음(25 preview 도)  copy(x = 1)
   동등성 구현            IL 로 풀어 박는다          invokedynamic 한 줄         메서드로 생성
   상속                  record 끼리 된다          ✕ final                  ✕ 상속당할 수 없다
   값 타입판              record struct            ✕                        (value class — 다른 것)
   위치 속성 불변          class·readonly struct     ✔ final                  val 이면
```

- ★ **표의 Java·Kotlin 칸 중 「비파괴 변경」 Java 만 이 판에서 던졌다** — 나머지는 각 갈래 문서의 결론을 옮겼다.

### (8) ★★ 컴파일러가 무엇을 안 보나 — 탐침 일곱

```text
===== 소스: cs18b-probe.cs =====
using System;
using System.Collections.Generic;

// 탐침 1 — Equals(R1) 를 손으로 쓰고 GetHashCode 는 안 쓴다
record R1(int X) { public virtual bool Equals(R1? o) => o is not null && o.X == X; }

// 탐침 2 — 위치 매개변수가 배열이다
record R2(int[] Xs);

// 탐침 3 — 위치 매개변수가 가변 컬렉션이다
record R3(List<int> Xs);

// 탐침 4 — record struct 를 셋의 키로 쓰고, 넣은 뒤 바꾼다
record struct R4(int X);

// 탐침 5 — double 을 담는다
record R5(double V);

// 탐침 6 — 위치 밖에 가변 속성을 둔다
record R6(int X) { public int Y { get; set; } }

// 탐침 7 — GetHashCode 만 손으로 쓴다
record R7(int X) { public override int GetHashCode() => 0; }

class Program {
    static void Main() {
        Console.WriteLine($"탐침 2 : new R2(new[] {{1}}) == new R2(new[] {{1}}) = {new R2(new[] { 1 }) == new R2(new[] { 1 })}");
        var set = new HashSet<R4>(); var k = new R4(1); set.Add(k); k.X = 2;
        Console.WriteLine($"탐침 4 : 넣은 뒤 k.X = 2 · set.Contains(k) = {set.Contains(k)} · set.Contains(new R4(1)) = {set.Contains(new R4(1))}");
        double x = double.NaN, y = double.NaN;
        Console.WriteLine($"탐침 5 : new R5(x) == new R5(y) = {new R5(x) == new R5(y)} · x == y = {x == y}   (x, y 는 둘 다 double.NaN)");
        var h = new HashSet<R6>(); var r6 = new R6(1); h.Add(r6); r6.Y = 5;
        Console.WriteLine($"탐침 6 : 넣은 뒤 Y = 5 · set.Contains(r6) = {h.Contains(r6)}");
    }
}
===== csc -nullable:enable -warn:9 -out:ex.dll cs18b-probe.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
cs18b-probe.cs(5,40): warning CS8851: 'R1' defines 'Equals' but not 'GetHashCode'
탐침 2 : new R2(new[] {1}) == new R2(new[] {1}) = False
탐침 4 : 넣은 뒤 k.X = 2 · set.Contains(k) = False · set.Contains(new R4(1)) = True
탐침 5 : new R5(x) == new R5(y) = True · x == y = False   (x, y 는 둘 다 double.NaN)
탐침 6 : 넣은 뒤 Y = 5 · set.Contains(r6) = False
===== csc -nullable:enable -warn:9 -out:ex.dll cs18b-probe.cs 2>&1 | grep -o "cs18b-probe.cs([0-9]*" | sort -u | wc -l    # 탐침 7개 중 진단이 붙은 줄은 몇 개인가 (exit=0) =====
1
```

- ★★★ **탐침 일곱 중 진단이 붙은 줄은 하나**다(`CS8851`, 탐침 1).

| 탐침 | 무엇을 심었나 | 답했나 | 실행하면 |
|---|---|---|---|
| 1 | `Equals(R1)` 를 손으로 · `GetHashCode` 는 안 씀 | **답함** — `CS8851` | — |
| 2 | ★★ **위치 매개변수가 배열** | ★★★ **침묵** | 내용이 같아도 **`False`** |
| 3 | 위치 매개변수가 **가변 리스트** | **침묵** | ((6)의 얕은 복사) |
| 4 | ★★ **`record struct` 를 셋의 키로 · 넣은 뒤 변경** | **침묵** | `Contains(k)` **`False`** · `Contains(new R4(1))` **`True`** |
| 5 | `double` 을 담음 | **침묵** | ★★★ **`NaN` 을 담은 둘이 `True`** — `x == y` 는 `False` |
| 6 | ★★ **위치 밖의 가변 속성** | ★★★ **침묵** | 넣은 뒤 바꾸면 **`Contains` 가 `False`** |
| 7 | `GetHashCode` 만 손으로(상수 `0`) | **침묵** | — (규약은 지킨다 — 느려질 뿐) |

- ★★★ **탐침 4 가 재미있다** — **셋 안의 것은 사본**이다. `k.X = 2` 는 **내 변수 `k`** 만 바꿨고 셋 안의 `R4(1)` 은 그대로다.\
  그래서 `Contains(new R4(1))` 이 `True` 다. ★★ **클래스 키였다면 셋 안의 객체가 바뀌어 길을 잃는다**(목록의 **19번 주제**의 `R3`).\
  **struct 키는 「길을 잃는」 대신 「내가 들고 있는 것과 셋 안의 것이 달라진다」.**
- ★★★ **탐침 5** — 생성된 `Equals` 는 필드를 **`double.Equals`** 로 비교하고(`EqualityComparer<double>`), 그것은 **`NaN` 을 같다고 본다.**\
  **`==` 연산자(IEEE)와 답이 반대다.** ★ Java record 도 같은 선택을 했다([Java 14번](../../../java/syntax/14-records/) — 「`NaN` 은 같다」).
- ★★★ **탐침 6** — **위치 밖의 멤버도 동등성에 들어간다**(Learn: 「**선언한 모든 필드**」). 가변이면 **키로 쓰는 순간 위험**하다.
- ★ 탐침 1 의 `CS8851` 은 Learn 의 권고 문장(「`Equals(R)` 를 쓰면 `GetHashCode` 도」)이 **진단으로 강제된** 자리다.

```text
===== 소스: cs18b-dup.cs =====
record R(int X) {
    public override bool Equals(object o) => false;       // 컴파일러가 만드는 것을 손으로 쓴다
}
class Program { static void Main() { } }
===== csc -out:ex.dll cs18b-dup.cs (cc exit=1) =====
cs18b-dup.cs(2,26): error CS0111: Type 'R' already defines a member called 'Equals' with the same parameter types
```

- ★★★ **`Equals(object)` 는 손으로 못 쓴다** — `CS0111`(이미 같은 매개변수의 `Equals` 가 있다).\
  Learn — 「**`Equals(object)` 를 명시적으로 선언하면 에러다**」. **`Equals(R)` 는 쓸 수 있다**(탐침 1).
- ★ 즉 record 에서 동등성을 바꾸는 **유일한 문이 `Equals(R)` + `GetHashCode`** 다 — 그래서 `==` 와 `Equals(object)` 가 **자동으로 따라온다**((3)).

## 문법 — 형태와 규칙

### 형태

```csharp
// cs18b-form.cs
using System;

var p = new Person("민수", 30);
var older = p with { Age = 31 };                  // 비파괴 변경 — 새 객체
var (name, age) = older;                          // 해체 — Deconstruct
Console.WriteLine($"{p} / {older} / {name},{age} / {p == new Person("민수", 30)}");
var m = new Money(1000, "KRW");
Console.WriteLine($"{m} / {m with { Won = 2000 }}");

public record Person(string Name, int Age) {      // 위치 record — init 속성 둘
    public string Label => $"{Name}({Age})";      // 본문 멤버를 더해도 된다 — 동등성에는 안 들어간다
}
public readonly record struct Money(int Won, string Currency);   // 값 타입 · 불변
```

```text
===== 소스: cs18b-form.cs =====
using System;

var p = new Person("민수", 30);
var older = p with { Age = 31 };                  // 비파괴 변경 — 새 객체
var (name, age) = older;                          // 해체 — Deconstruct
Console.WriteLine($"{p} / {older} / {name},{age} / {p == new Person("민수", 30)}");
var m = new Money(1000, "KRW");
Console.WriteLine($"{m} / {m with { Won = 2000 }}");

public record Person(string Name, int Age) {      // 위치 record — init 속성 둘
    public string Label => $"{Name}({Age})";      // 본문 멤버를 더해도 된다 — 동등성에는 안 들어간다
}
public readonly record struct Money(int Won, string Currency);   // 값 타입 · 불변
===== csc -out:ex.dll cs18b-form.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
Person { Name = 민수, Age = 30, Label = 민수(30) } / Person { Name = 민수, Age = 31, Label = 민수(31) } / 민수,31 / True
Money { Won = 1000, Currency = KRW } / Money { Won = 2000, Currency = KRW }
```

- ★★★ **위치 record** — `record Person(string Name, int Age)` 한 줄이 **`init` 속성 둘 + 생성자 + `Deconstruct` + 동등성 + `ToString`** 이다((1)).
- ★★ **본문 멤버를 더할 수 있다** — `Label` 은 **계산 속성**이라 `with` 뒤에도 새 값(`민수(31)`)을 따라간다.\
  ★ **`ToString` 에는 들어가고**(`Label = 민수(30)`), **동등성에는 안 들어간다** — 필드가 없기 때문이다.
- **`var (name, age) = older`** — 생성된 `Deconstruct` 다. 해체 전반은 목록의 **23번 주제**가 정본이다.
- **`readonly record struct`** — 값 타입 + 불변. **`record struct` 에 `readonly` 가 없으면 가변이다**((5)).
- **record 는 record 만 상속**한다 — 클래스와 record 는 서로 상속 못 한다(Learn).

### 금지 사례 — 진단이 나는 꼴

| 쓴 꼴 | 진단 코드 | 어디서 |
|---|---|---|
| `record`·`readonly record struct` 의 위치 속성에 대입 | `CS8852`(에러) | (5) |
| `Equals(object)` 를 손으로 선언 | `CS0111`(에러) | (8) |
| `Equals(R)` 를 손으로 쓰고 `GetHashCode` 는 안 씀 | `CS8851`(**경고**) | (8) |
| `record struct` 의 위치 속성에 대입 | ★★★ **진단 없음** — 가변이다 | (5) |

## 어디서 틀리나

1. ★★★ **「`record` 면 불변이다」** — **`record struct` 는 위치 속성이 `set` 이다**((1)(5)). `readonly` 를 붙여야 한다.
2. ★★★ **「`with` 는 속성을 바꾼다」** — **복제한 새 객체**다. record class 면 **호출마다 힙 할당**이다((2)(5)).
3. ★★★ **「같은 값이면 파생 record 와 기반 record 도 같다」** — **`EqualityContract` 가 달라 `!=`** 다((4)).
4. ★★★ **「`with` 는 깊은 복사다」** — **얕다.** 리스트는 공유된다((6)).
5. ★★ **「record 는 배열 내용을 비교한다」** — **배열은 참조로 비교**된다((6)(8)).
6. ★★ **「record 의 `==` 는 IEEE 비교다」** — 필드마다 **`Equals`** 라 **`NaN` 이 같다**((8) 탐침 5).
7. ★★ **「동등성은 위치 매개변수만 본다」** — **모든 필드**를 본다. 위치 밖의 가변 속성도 들어간다((8) 탐침 6).
8. ★ **「`<Clone>$` 를 부르면 된다 / `Clone` 을 재정의하면 된다」** — 이름은 **구현**이고, `Clone` 멤버는 **만들 수조차 없다**(Learn).
9. ★ **「Java record 에도 `with` 가 있다」** — **javac 25 preview 에서도 없다**((7)).

## 구현 세부사항 대 언어 보장

| 무엇 | 층 | 근거 |
|---|---|---|
| **생성 멤버의 목록**(동등성·`ToString`·`PrintMembers`·`Deconstruct`·연산자·복제·복사 생성자·`EqualityContract`) | ★★★ **언어 보장** | (1) · Learn |
| **위치 속성이 class·readonly struct 는 `init`, struct 는 `set`** | ★★★ **언어 보장** | (1)(5) `CS8852` |
| **`with` 가 복제한 뒤 설정한다 · 결과가 피연산자의 런타임 타입** | ★★★ **언어 보장** | (2)(4) |
| **파생 record 는 실제 타입이 같아야 같다** | ★★★ **언어 보장** | (4) |
| **`Equals(object)` 를 손으로 못 쓴다** | ★★★ **언어 보장** | (8) `CS0111` |
| **복제 메서드의 이름 `<Clone>$`** | ★★ **구현(Roslyn)** — Learn 도 「컴파일러가 만든 이름」 | (1)(2) |
| **`Equals` 첫머리의 참조 비교 지름길** | ★★ **구현(Roslyn)** | (3) |
| **해시 섞는 상수 `-1521134295` · `EqualityComparer<T>.Default` 경유** | ★★ **구현(Roslyn)** | (3) |
| **`with RC` 가 호출당 24바이트** | ★ **이 판의 관찰**(2×2 에서 안 움직임) | (5) |
| **`-warn:9` 에서 탐침 일곱 중 하나만 답한 것** | ★ **이 판의 관찰** | (8) |

## 언제 쓰고 언제 안 쓰나

- ★★★ **「내용이 같으면 같은 것」인 데이터 — DTO·메시지·설정값·값 객체 — 에 `record` 를 쓴다.**
- ★★★ **정체성이 있는 것(엔터티) 에는 쓰지 마라** — Learn 도 「EF Core 엔터티에 **적절하지 않다**」(참조 동등이 필요하다)고 적는다.
- ★★ **키로 쓸 record 는 모든 멤버를 불변으로** — 위치 밖 가변 속성 하나가 셋을 깨뜨린다((8) 탐침 6).
- ★★ **배열·리스트를 담을 거면** `Equals(R)`·`GetHashCode` 를 손으로 쓰거나(`CS8851` 짝을 지켜라) **불변 컬렉션**을 담아라((6)).
- ★ **`record struct` 는 `readonly` 와 함께** — 가변 struct 의 함정을 그대로 갖는다([02번](../02-struct-vs-class-choosing/)).
- ★ **상속은 얕게** — `EqualityContract` 때문에 **기반 타입 변수로 섞어 비교**하면 늘 다르다((4)). 봉인(`sealed record`)이 기본값으로 무난하다.

## 핵심 문장

1. ★★★ **`record` 한 줄은 16개 멤버를 만든다** — struct 쪽은 **`EqualityContract`·복제 메서드·복사 생성자가 빠진 13개**다((1)).
2. ★★★ **`with` 는 `<Clone>$`(복사 생성자) + `init` 세터**다 — record class 면 **호출마다 할당**, struct 면 **대입 복사**다((2)(5)).
3. ★★★ **`EqualityContract` 때문에 파생과 기반은 같은 값이어도 `!=`** 이고, 그 덕에 **대칭성이 지켜진다**((4)).
4. ★★ **생성된 `==` 는 `Equals` 를 부르므로 둘이 어긋나지 않는다** — 목록의 **19번 주제**의 사고가 record 에서는 안 난다((3)).
5. ★★ **`record struct` 는 가변이고, `with` 와 배열 비교는 얕다**((5)(6)).

## 관련 자료

- 목록의 **19번 주제**(동등성 규칙) — ★★★ **18→19 는 한 사슬이다.** 여기서 본 **생성된 `==`·`Equals` 의 IL**((3))이 19번의 **「어긋나는 사고」가 record 에서 안 나는 이유**다.
- [13번 — 속성과 `init`](../13-properties-init-required-field/) — **`init`·`modreq(IsExternalInit)`** 의 정본. record 가 그것을 **만든다**.
- [02번 — `struct` 대 `class`](../02-struct-vs-class-choosing/) — **`record struct` 고르는 기준**과 **`readonly record struct` 의 `CS8852`**.
- [16번 — 상속](../16-inheritance-virtual-override-abstract-sealed-new/) — `<Clone>$` 와 `EqualityContract` 가 **`virtual`** 인 뜻.
- [03번 — 박싱](../03-boxing-and-unboxing/) — `RS.Equals(object)` 의 24바이트가 그것이다((5)).
- 목록의 **23번 주제**(튜플과 해체) — `Deconstruct` 의 정본이 될 자리.
- Java 갈래 목록([`java/syntax/README.md`](../../../java/syntax/README.md))의 **14번**([`14-records/`](../../../java/syntax/14-records/)) —\
  **경계**: Java record 의 **컴팩트 생성자·`invokedynamic` 동등성·방어 복사**는 거기가 정본이다. 여기서는 **`with` 가 없다는 것만** 던졌다((7)).
- Kotlin 갈래 목록([`kotlin/syntax/README.md`](../../../kotlin/syntax/README.md))의 **22번**([`22-data-class-generated-members/`](../../../kotlin/syntax/22-data-class-generated-members/)) — `copy` 가 **본문 프로퍼티를 되돌린다.**

## 용어 풀이

- **`record`** — 값 동등성·`ToString`·해체·`with` 를 컴파일러가 만들어 주는 타입(C# 9 class · C# 10 struct).
- **값 동등성(value equality)** — **같은 타입이고 같은 값을 가지면** 같다고 보는 것. 클래스의 기본은 **참조 동등성**이다.
- **위치 매개변수(positional parameter)** — `record P(int X)` 의 `X`. 속성·생성자·`Deconstruct` 가 여기서 나온다.
- **비파괴 변경(nondestructive mutation)** — 원본을 두고 **바뀐 사본**을 만드는 것. `with` 식.
- **복제 메서드(clone method)** — `with` 가 부르는 가상 메서드. 이름은 컴파일러가 만든다(이 판: `<Clone>$`).
- **복사 생성자(copy constructor)** — `protected R(R original)`. 모든 필드를 복사한다.
- **`EqualityContract`** — record class 의 `protected virtual Type` 속성. **실제 타입**을 돌려주어 동등성에 섞인다.
- **`PrintMembers`** — `ToString` 이 부르는 도우미. 파생 record 가 **덧붙여 찍게** class 에서는 `protected virtual` 이다.
- **얕은 복사(shallow copy)** — 참조 멤버는 **참조만** 복사하는 것. 가리키는 객체는 공유된다.

## 더 들어가면

- ★ **`sealed` record 의 생성 멤버** — `EqualityContract`·`PrintMembers` 의 한정자가 달라진다(Learn 에 표가 있다). **이 판에서 안 찍었다.**
- ★ **사용자 정의 복사 생성자** — 직접 쓰면 컴파일러가 안 만든다(Learn). **깊은 복사**를 넣는 자리다. **안 던졌다.**
- ★ **`record struct` 의 매개변수 없는 생성자** — 모든 필드를 기본값으로(Learn). **안 찍었다.**
- ★ **C# 15 의 `closed` record** — Learn 이 「직접 파생을 선언 어셈블리로 제한한다」고 적는다. **이 판(`latest`)의 범위 밖**이다.
