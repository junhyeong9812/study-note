# csharp/syntax/25 — 제네릭 제약 `where` 와 `default(T)` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [ECMA-335(CLI) 6판](https://ecma-international.org/publications-and-standards/standards/ecma-335/) · [ECMA-334 7판(2023-12)](https://ecma-international.org/publications-and-standards/standards/ecma-334/) ·
> [Learn — `where`(제네릭 형식 제약)](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/keywords/where-generic-type-constraint)(열어서 확인: 「`notnull` 을 어기면 **다른 제약과 달리** 컴파일러가 **에러 대신 경고**를 낸다」 ·\
> 「nullable 문맥에서 `class` 제약은 **널 불가 참조 타입**을 요구한다 — 널 허용까지 받으려면 `class?`」 · 「`unmanaged` 제약은 형식이 **`struct` 여야 함을 강제**한다」 ·\
> 「`T` 가 `struct` 면 `T?` 는 `Nullable<T>`, 참조 타입이면 `T?` 는 null 이 유효한 값이라는 뜻 — **`T?` 의 뜻이 모호해진다**」) ·
> [Learn — C# 버전 이력](https://learn.microsoft.com/en-us/dotnet/csharp/whats-new/csharp-version-history)(열어서 확인: 7.3 「**더 많은 제네릭 제약**」 · 「**오버로드 해결의 모호한 경우가 줄었다**」 · 8.0 「unmanaged 구성 타입」).
> **실행 검증** — 이 문서의 모든 출력·진단·IL·할당 바이트는 아래 「이 판」의 도구로 **실제로 돌려 얻은 것**이다(2026-09-26).\
> ★ 블록은 캡처 스크립트가 파일로 받아 조립기가 끼워 넣은 것이다 — 사람이 옮겨 적은 줄은 하나도 없다. 진단은 영어로 고정했다(`DOTNET_CLI_UI_LANGUAGE=en` + `-preferreduilang:en-US`).
> **버전** — 제약 `class`·`struct`·`new()`·인터페이스·기반 클래스 **C# 2.0** · `Enum`·`Delegate`·`unmanaged` **C# 7.3** · `notnull`·`class?` **C# 8** · 제약 없는 `T?` **C# 9** — ★ **`-langversion` 판 격자로 직접 확인했다**((7)).
> **경계** — ★★★ **[24번](../24-generics-and-type-parameters/)이 예고편으로 던진 제약 위반 여섯(`CS0452`·`CS0453`×2·`CS0310`·`CS8377`·`CS8714`)은 다시 싣지 않는다** — 그 여섯을 **80칸 격자의 일부로** 넓힌다((1)).\
> ★ `new T()` 가 `Activator::CreateInstance` 라는 것도 24편 (2)가 먼저 찍었다 — 여기서는 **제약을 바꿔도 같은가 · 생성자가 던지면 무엇이 되나**만 더 묻는다((3)(4)).\
> ★ `where T : class` 안의 `==` 가 `box`·`box`·`ceq` 로 **참조 비교**라는 것은 [19번](../19-equality-equals-gethashcode-operator/) (3)이 정본이다 — 인용만 한다.\
> ★ `enum` 자체는 [20번](../20-enum-and-flags/) · 공변·반변은 [26번](../26-covariance-and-contravariance-out-in/).
> ★★★ **본체 창은 ② 진단 격자다** — 제약 10 × 타입 인자 8 = **80칸**을 한 번에 컴파일해 **스크립트가 칸마다 되돌려 센다.**
>
> ★★ **흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | 진단 **문구** · 진단 **순서**(그래서 `sort` 를 배너에 적었다) | ★★★ **진단 코드** · **`(행,열)`** · **`cc exit`** |
> | **IL 오프셋 폭** | ★★★ **옵코드와 토큰**(`initobj T` · `call System.Activator::CreateInstance<T>`) |
> | 증분의 절댓값 일부(규칙 24) | ★★★ **「막힌 칸 N / M」 · 「네 판에서 갈린 줄 N / M」**(스크립트가 센 마지막 줄) |
> | — | ★★ 리플렉션 플래그 이름(`ReferenceTypeConstraint` 등) · 예외 **타입** |

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
| **CLI 명세(ECMA-335)** | ★★★ **실행 엔진이 약속한 것** | ★★★ `class`·`struct`·`new()`·타입 제약은 **메타데이터의 플래그와 타입 목록**으로 남고 **런타임이 다시 검사한다**((5) [B]) |
| **언어 명세(ECMA-334)** | C# 언어가 약속한 것 | 제약 위반은 **컴파일 에러** · `default(T)` 는 **그 타입의 기본값** · 제약은 **서명의 일부가 아니다**((6)) |
| **컴파일러 구현(Roslyn)** | 그것을 **어떻게 적나** | ★★★ `notnull`·`class?` 는 **플래그가 없고 `Nullable` 특성뿐** · `unmanaged` 는 `struct` 플래그 + **`IsUnmanaged` 특성** · `new T()` 는 `Activator.CreateInstance<T>` |
| **이 판의 관찰** | .NET 10.0.12 · linux-x64 | 할당 바이트 · 진단 문구 · 예외 메시지 |

★★★ **이 주제의 층 구분이 결정적이다 —**\
**같은 `where` 줄에 적힌 제약이 서로 다른 층에 산다.** `class`·`struct`·`new()`·인터페이스·기반 클래스는 **CLI 가 강제**하고, `notnull`·`class?` 는 **컴파일러의 널 분석**일 뿐이며, `unmanaged` 는 **반쯤**만 CLI 에 있다((5)).

## 한눈에 — 쉽게 말하면

**제약은 「이 자리에 들어올 손님의 자격 조건」이다 — 그런데 문지기가 둘이다.**

회관 대관을 생각하자.

- **입구의 안내원(컴파일러)** — 신청서를 보고 **자격이 안 되면 돌려보낸다**(에러). 몇몇 항목은 **주의만 주고 들여보낸다**(`notnull` 경고).
- **건물 경비(런타임)** — 안내원을 **건너뛰고 뒷문으로 들어와도**(리플렉션 `MakeGenericMethod`) **다시 막는다** — 단 **경비가 아는 조건만**이다. 「널 아님」은 경비 수첩에 없어 그냥 통과한다.
- **빈 좌석의 기본 상태(`default(T)`)** — 좌석마다 다르다. 숫자 좌석은 **0**, 참조 좌석은 **빈자리(null)**, 구조체 좌석은 **모든 칸이 0 인 세트**.
- **「새로 하나 주세요」(`new T()`)** — 안내원이 직접 만들지 않고 **대행사(`Activator`)에 전화**한다. 만들다 사고가 나면 대행사가 **자기 봉투에 넣어** 돌려준다(`TargetInvocationException`).

| 비유 | 실체 | 어디서 보나 |
|---|---|---|
| 자격 조건표 | ★★★ **80칸 중 막힌 칸 47 · 경고만 4 · 통과 29** | (1) |
| 뒷문으로 와도 경비가 막는다 | ★★★ `MakeGenericMethod(typeof(int))` 로 `class` 제약을 어기면 **`ArgumentException`** | (5) |
| 경비 수첩에 없는 조건 | ★★★ **`unmanaged` 에 참조를 품은 구조체가 뒷문으로 통과** · `notnull` 은 **플래그가 `None`** | (5) |
| 좌석마다 다른 빈 상태 | ★★★ `0` · `null` · `False` · `Sunday` · `0001-01-01…` · **구조체는 전부 0** | (2) |
| 대행사에 전화 | ★★★ `new T()` 는 **제약을 바꿔도 `Activator::CreateInstance<T>`** | (3) |
| 대행사 봉투 | ★★★ 생성자 예외가 **`TargetInvocationException` 안에** | (4) |

★★★ **이 주제의 본체 그림 — 한 줄의 `where` 가 세 층으로 흩어진다.**

```text
   where T : ...            컴파일러(Roslyn)가 막나      메타데이터에 무엇이 남나                   런타임이 다시 막나
   ─────────────            ────────────────────        ──────────────────────────────           ────────────────
   class                    에러  CS0452                 ReferenceTypeConstraint 플래그            ○  ArgumentException
   class?                   에러  CS0452 (값 타입만)       같은 플래그 + Nullable(2) 특성             ○  (값 타입만)
   struct                   에러  CS0453                 NotNullableValueType + DefaultCtor 플래그  ○
   new()                    에러  CS0310                 DefaultConstructorConstraint 플래그       ○
   인터페이스 · 기반 클래스     에러  CS0311/0312/0313/0315  타입 목록                                ○
   Enum · Delegate          에러  CS0311/0312/0315       타입 목록(System.Enum · System.Delegate)  ○
   unmanaged                에러  CS8377                 struct 플래그 + IsUnmanaged 특성           △  struct 만 — 「참조 없음」 은 안 본다
   notnull                  경고  CS8714                 플래그 None (NullableContext 특성뿐)      ✕  아무것도 안 본다

   ★★★ 위 넷째 열이 「○」인 것만 CLI 명세의 제약이다. 나머지는 컴파일러가 혼자 지키는 약속이다.
```

## 이 주제가 답하려는 질문

1. **어떤 제약에 어떤 인자가 막히나** — 80칸 격자((1)).
2. **`default(T)` 는 타입마다 무엇인가** — 그리고 **`new T()` 와 언제 다른가**((2)(3)).
3. **`new T()` 는 무엇으로 컴파일되고, 생성자가 던지면**((3)(4)).
4. **제약은 누가 지키나** — 컴파일러만인가 런타임도인가((5)).
5. **제약은 오버로드와 어떻게 얽히나** — 서명·후보 거르기((6)) · **언제 들어왔나**((7)) · **`T?` 가 무엇이 되나**((8)).

## 동작 방식

### (0) 이 주제가 쓰는 창

★★★ **본체 창은 ② 진단 격자다** — 「이 인자가 이 제약을 통과하나」는 **컴파일러에게 물어서** 답한다.

| 창 | 무엇을 보여 주나 | 이 주제에서 |
|---|---|---|
| ★★★ **② 진단 격자** | ★★★ **제약 10 × 인자 8 = 80칸** — 진단의 `(행,열)` 을 칸으로 되돌려 **「막힌 칸 N / M」** 을 센다 · **판 격자**(`-langversion` 7.2\~9)로 **도입 판** | (1)(6)(7) |
| ★★★ **③ 리플렉션** | ★★★ 제약이 **메타데이터에 무엇으로 남나** · `MakeGenericMethod` 로 **컴파일러를 건너뛰면 런타임이 막나** · `default(T)` 의 실제 값 | (2)(5)(8) |
| ★★ **① IL 덤프** | ★★ `default(T)` → **`initobj T`** · `new T()` → **`Activator::CreateInstance<T>`** — 제약 셋에서 같다 | (3) |
| ★ **④ 할당 바이트** | ★ `new T()` 가 **객체 하나 말고 더 할당하나** — 2×2 판 격자 | (9) |
| **부적용인 창** | 없다 — 네 창을 다 썼다. ★ 단 **`notnull`·`class?` 에는 ④ 가 잴 것이 없다**(런타임 타입이 `string` 과 `string?` 에서 같다 — [06번](../06-nullable-reference-types/)의 결론) — 제4의 상태 | — |

### (1) ★★★ 본체 — 제약 10 × 타입 인자 8 = 80칸

**언제 쓰나** — 「이 제약을 걸면 누가 못 들어오나」를 **한 표로** 답할 때.

```text
===== 소스: cs25b-grid.cs =====
using System;
abstract class Shape { }
struct Pt { public int X; public Pt(int x) { X = x; } }
static class K {
    public static void Class<T>()     where T : class { }
    public static void ClassQ<T>()    where T : class? { }
    public static void Struct<T>()    where T : struct { }
    public static void NotNull<T>()   where T : notnull { }
    public static void Unmanaged<T>() where T : unmanaged { }
    public static void New<T>()       where T : new() { }
    public static void IComp<T>()     where T : IComparable { }
    public static void Base<T>()      where T : Shape { }
    public static void Enum<T>()      where T : System.Enum { }
    public static void Deleg<T>()     where T : Delegate { }
}
class Program {
    static void Main() {
        K.Class<int>(); K.Class<int?>(); K.Class<string>(); K.Class<string?>(); K.Class<Shape>(); K.Class<Pt>(); K.Class<DayOfWeek>(); K.Class<Action>();
        K.ClassQ<int>(); K.ClassQ<int?>(); K.ClassQ<string>(); K.ClassQ<string?>(); K.ClassQ<Shape>(); K.ClassQ<Pt>(); K.ClassQ<DayOfWeek>(); K.ClassQ<Action>();
        K.Struct<int>(); K.Struct<int?>(); K.Struct<string>(); K.Struct<string?>(); K.Struct<Shape>(); K.Struct<Pt>(); K.Struct<DayOfWeek>(); K.Struct<Action>();
        K.NotNull<int>(); K.NotNull<int?>(); K.NotNull<string>(); K.NotNull<string?>(); K.NotNull<Shape>(); K.NotNull<Pt>(); K.NotNull<DayOfWeek>(); K.NotNull<Action>();
        K.Unmanaged<int>(); K.Unmanaged<int?>(); K.Unmanaged<string>(); K.Unmanaged<string?>(); K.Unmanaged<Shape>(); K.Unmanaged<Pt>(); K.Unmanaged<DayOfWeek>(); K.Unmanaged<Action>();
        K.New<int>(); K.New<int?>(); K.New<string>(); K.New<string?>(); K.New<Shape>(); K.New<Pt>(); K.New<DayOfWeek>(); K.New<Action>();
        K.IComp<int>(); K.IComp<int?>(); K.IComp<string>(); K.IComp<string?>(); K.IComp<Shape>(); K.IComp<Pt>(); K.IComp<DayOfWeek>(); K.IComp<Action>();
        K.Base<int>(); K.Base<int?>(); K.Base<string>(); K.Base<string?>(); K.Base<Shape>(); K.Base<Pt>(); K.Base<DayOfWeek>(); K.Base<Action>();
        K.Enum<int>(); K.Enum<int?>(); K.Enum<string>(); K.Enum<string?>(); K.Enum<Shape>(); K.Enum<Pt>(); K.Enum<DayOfWeek>(); K.Enum<Action>();
        K.Deleg<int>(); K.Deleg<int?>(); K.Deleg<string>(); K.Deleg<string?>(); K.Deleg<Shape>(); K.Deleg<Pt>(); K.Deleg<DayOfWeek>(); K.Deleg<Action>();
    }
}
===== csc -nullable:enable -out:ex.dll cs25b-grid.cs 2>&1 | sort | awk '!s[$3]++' | sort -k3,3 (cc exit=1) =====
cs25b-grid.cs(23,124): error CS0310: 'Action' must be a non-abstract type with a public parameterless constructor in order to use it as parameter 'T' in the generic type or method 'K.New<T>()'
cs25b-grid.cs(24,138): error CS0311: The type 'System.Action' cannot be used as type parameter 'T' in the generic type or method 'K.IComp<T>()'. There is no implicit reference conversion from 'System.Action' to 'System.IComparable'.
cs25b-grid.cs(25,26): error CS0312: The type 'int?' cannot be used as type parameter 'T' in the generic type or method 'K.Base<T>()'. The nullable type 'int?' does not satisfy the constraint of 'Shape'.
cs25b-grid.cs(24,27): error CS0313: The type 'int?' cannot be used as type parameter 'T' in the generic type or method 'K.IComp<T>()'. The nullable type 'int?' does not satisfy the constraint of 'System.IComparable'. Nullable types can not satisfy any interface constraints.
cs25b-grid.cs(24,101): error CS0315: The type 'Pt' cannot be used as type parameter 'T' in the generic type or method 'K.IComp<T>()'. There is no boxing conversion from 'Pt' to 'System.IComparable'.
cs25b-grid.cs(18,101): error CS0452: The type 'Pt' must be a reference type in order to use it as parameter 'T' in the generic type or method 'K.Class<T>()'
cs25b-grid.cs(20,145): error CS0453: The type 'Action' must be a non-nullable value type in order to use it as parameter 'T' in the generic type or method 'K.Struct<T>()'
cs25b-grid.cs(22,166): error CS8377: The type 'Action' must be a non-nullable value type, along with all fields at any level of nesting, in order to use it as parameter 'T' in the generic type or method 'K.Unmanaged<T>()'
cs25b-grid.cs(24,61): warning CS8631: The type 'string?' cannot be used as type parameter 'T' in the generic type or method 'K.IComp<T>()'. Nullability of type argument 'string?' doesn't match constraint type 'System.IComparable'.
cs25b-grid.cs(18,61): warning CS8634: The type 'string?' cannot be used as type parameter 'T' in the generic type or method 'K.Class<T>()'. Nullability of type argument 'string?' doesn't match 'class' constraint.
cs25b-grid.cs(21,27): warning CS8714: The type 'int?' cannot be used as type parameter 'T' in the generic type or method 'K.NotNull<T>()'. Nullability of type argument 'int?' doesn't match 'notnull' constraint.
===== 격자 — 위 컴파일의 진단 전부를 (제약, 인자) 칸으로 되돌린 표 =====
제약 \ 인자     int             int?            string          string?         Shape           Pt              DayOfWeek       Action
Class       CS0452          CS0452          ok              CS8634(w)       ok              CS0452          CS0452          ok
ClassQ      CS0452          CS0452          ok              ok              ok              CS0452          CS0452          ok
Struct      ok              CS0453          CS0453          CS0453          CS0453          ok              ok              CS0453
NotNull     ok              CS8714(w)       ok              CS8714(w)       ok              ok              ok              ok
Unmanaged   ok              CS8377          CS8377          CS8377          CS8377          ok              ok              CS8377
New         ok              ok              CS0310          CS0310          CS0310          ok              ok              CS0310
IComp       ok              CS0313          ok              CS8631(w)       CS0311          CS0315          ok              CS0311
Base        CS0315          CS0312          CS0311          CS0311          ok              CS0315          CS0315          CS0311
Enum        CS0315          CS0312          CS0311          CS0311          CS0311          CS0315          ok              CS0311
Deleg       CS0315          CS0312          CS0311          CS0311          CS0311          CS0315          CS0315          ok
막힌 칸(에러) 47 / 80 · 경고만 난 칸 4 / 80 · 통과 칸 29 / 80
```

- ★★★ **막힌 칸 47 / 80 · 경고만 난 칸 4 / 80 · 통과 칸 29 / 80** — 스크립트가 **진단의 `(행,열)` 로 칸을 되돌려** 셌다. 한 칸 = 한 호출이다.
- ★★★ **첫 블록은 코드마다 첫 진단 한 줄** — 에러 코드가 **여덟 가지**(`CS0310`·`CS0311`·`CS0312`·`CS0313`·`CS0315`·`CS0452`·`CS0453`·`CS8377`), 경고가 **세 가지**(`CS8631`·`CS8634`·`CS8714`)다.
- ★★★ **인터페이스·기반 클래스·`Enum`·`Delegate` 는 「왜 안 되나」로 코드가 갈린다** —\
  **`CS0311`** 참조 타입인데 **암시적 참조 변환이 없다** · **`CS0315`** 값 타입인데 **박싱 변환이 없다** · **`CS0312`** `int?` 가 **기반 클래스** 제약을 못 채운다 · **`CS0313`** `int?` 가 **인터페이스** 제약을 못 채운다(「**Nullable 은 어떤 인터페이스 제약도 못 채운다**」).
- ★★★ **`int?` 행이 가장 얄궂다** — `Struct` **`CS0453`**(「**널 불가** 값 타입」) · `Unmanaged` **`CS8377`** · `IComp` **`CS0313`** 인데 **`New<int?>` 는 통과**한다 — `Nullable<int>` 는 **공개 기본 생성자가 있는 구조체**이기 때문이다.
- ★★ **`string?` 은 에러가 아니라 경고로 떨어지는 칸이 셋** — `Class` 에 **`CS8634`**, `IComp` 에 **`CS8631`**, `NotNull` 에 **`CS8714`**. **`ClassQ`(`class?`) 는 `string?` 을 경고 없이 받는다.** 널 허용은 **컴파일러의 분석**([06번](../06-nullable-reference-types/))이라 에러로 올라가지 않는다.
- ★★ **`Shape`(추상 클래스)** — `Class`·`NotNull`·`Base` 통과, **`New` 는 `CS0310`**(「**추상이 아닌** 타입 + 공개 기본 생성자」).
- ★ **`DayOfWeek`(enum)** 는 `Struct`·`Unmanaged`·`New`·`IComp`·`Enum` 을 **전부** 통과한다 — enum 은 정수 위의 구조체다([20번](../20-enum-and-flags/)).

### (2) ★★★ `default(T)` — 타입마다 다른 값

```text
===== 소스: cs25b-default.cs =====
using System;
using System.Globalization;
struct Pt { public int X; public string? Name; public Pt(int x) { X = x; Name = "set"; } }
struct Pz { public int X; public Pz() { X = 7; } }
static class G {
    public static T Def<T>() => default!;
    public static T Make<T>() where T : new() => new T();
    public static string Show<T>(T v) => v is null ? "null" : Convert.ToString(v, CultureInfo.InvariantCulture)!;
}
class Program {
    static void Main() {
        Console.WriteLine($"[1] Def<int>()        = {G.Show(G.Def<int>())}");
        Console.WriteLine($"[2] Def<int?>()       = {G.Show(G.Def<int?>())}");
        Console.WriteLine($"[3] Def<string>()     = {G.Show(G.Def<string>())}");
        Console.WriteLine($"[4] Def<bool>()       = {G.Show(G.Def<bool>())}");
        Console.WriteLine($"[5] Def<double>()     = {G.Show(G.Def<double>())}");
        Console.WriteLine($"[6] Def<DateTime>()   = {G.Def<DateTime>().ToString("o", CultureInfo.InvariantCulture)}");
        Console.WriteLine($"[7] Def<DayOfWeek>()  = {G.Show(G.Def<DayOfWeek>())}");
        var p = G.Def<Pt>();
        Console.WriteLine($"[8] Def<Pt>()         = X={p.X} Name={G.Show(p.Name)}");
        Console.WriteLine($"[9] Def<(int,string)>() = {G.Def<(int, string)>()}");
        Console.WriteLine($"[10] Def<Pz>().X      = {G.Def<Pz>().X}");
        Console.WriteLine($"[11] Make<Pz>().X     = {G.Make<Pz>().X}");
        Console.WriteLine($"[12] default(Pz).X    = {default(Pz).X} · new Pz().X = {new Pz().X}");
    }
}
===== csc -nullable:enable -out:ex.dll cs25b-default.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
[1] Def<int>()        = 0
[2] Def<int?>()       = null
[3] Def<string>()     = null
[4] Def<bool>()       = False
[5] Def<double>()     = 0
[6] Def<DateTime>()   = 0001-01-01T00:00:00.0000000
[7] Def<DayOfWeek>()  = Sunday
[8] Def<Pt>()         = X=0 Name=null
[9] Def<(int,string)>() = (0, )
[10] Def<Pz>().X      = 0
[11] Make<Pz>().X     = 7
[12] default(Pz).X    = 0 · new Pz().X = 7
```

- ★★★ **`int` `0` · `int?` `null` · `string` `null` · `bool` `False` · `double` `0` · `DateTime` `0001-01-01T00:00:00.0000000` · `DayOfWeek` `Sunday`** — **「0 인 비트」가 그 타입으로 읽힌 값**이다. `Sunday` 는 **값 0 인 이름**이다.
- ★★★ **`[8]` 구조체 `Pt` 는 `X=0 Name=null`** — **모든 필드가 각자의 기본값**이다. 생성자가 `Name = "set"` 을 넣는데도 **생성자는 안 불린다.**
- ★★★ **`[10]`\~`[12]` `Pz` 는 매개변수 없는 생성자가 `X = 7` 을 넣는 구조체(C# 10)** — **`default(Pz).X = 0` 인데 `new Pz().X = 7`**, **`Make<Pz>()`(`new T()`) 도 `7`** 이다.\
  ★ **`default` 와 `new` 는 구조체에서 갈린다** — `default` 는 **생성자를 안 부르고 0 으로 채운다.**
- ★ **`[9]` 튜플 `(0, )`** — `(int, string)` 의 기본값은 **`(0, null)`** 이고, `null` 이 빈 문자열로 찍혔다.

```text
   default(T) 가 만드는 것 — 「생성자 없이, 전부 0 인 비트」

   int        [00 00 00 00]                          → 0
   bool       [00]                                   → False
   DayOfWeek  [00 00 00 00]  (enum = 정수)            → Sunday  (값 0 인 이름)
   string     [00 … 00]      (참조 한 칸)             → null
   int?       [00][00 00 00 00]  (HasValue=false)    → null
   Pt         [X=00 00 00 00][Name=00 … 00]          → X=0 · Name=null   ← 생성자 안 불림
   Pz         [X=00 00 00 00]                        → X=0               ← new Pz() 는 X=7

   ★★★ default(T) 는 「타입이 무엇이든 0 으로 채운 칸」 — 그래서 T 를 몰라도 IL 한 줄(initobj T)로 된다((3)).
```

### (3) ★★ IL — `initobj T` 와 `Activator::CreateInstance<T>`

```text
===== 소스: cs25b-il.cs =====
using System;
public static class G {
    public static T Def<T>() => default!;
    public static T NewAny<T>() where T : new() => new T();
    public static T NewStruct<T>() where T : struct => new T();
    public static T NewClass<T>() where T : class, new() => new T();
}
class Program {
    static void Main() {
        foreach (var n in new[] { "Def", "NewAny", "NewStruct", "NewClass" }) Il.Dump(typeof(G), n);
    }
}
===== csc -r:il.dll -out:ex.dll cs25b-il.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
--- G.Def ---
  .locals [0] T
  IL_0000: ldloca.s 0
  IL_0002: initobj T
  IL_0008: ldloc.0
  IL_0009: ret
--- G.NewAny ---
  IL_0000: call System.Activator::CreateInstance<T>
  IL_0005: ret
--- G.NewStruct ---
  IL_0000: call System.Activator::CreateInstance<T>
  IL_0005: ret
--- G.NewClass ---
  IL_0000: call System.Activator::CreateInstance<T>
  IL_0005: ret
===== csc -optimize -r:il.dll -out:exo.dll cs25b-il.cs && dotnet exo.dll (cc exit=0 · run exit=0) =====
--- G.Def ---
  .locals [0] T
  IL_0000: ldloca.s 0
  IL_0002: initobj T
  IL_0008: ldloc.0
  IL_0009: ret
--- G.NewAny ---
  IL_0000: call System.Activator::CreateInstance<T>
  IL_0005: ret
--- G.NewStruct ---
  IL_0000: call System.Activator::CreateInstance<T>
  IL_0005: ret
--- G.NewClass ---
  IL_0000: call System.Activator::CreateInstance<T>
  IL_0005: ret
```

- ★★★ **`Def` 는 `ldloca.s 0` → `initobj T` → `ldloc.0`** — 지역 변수 한 칸을 **0 으로 채워** 돌려준다. `T` 가 무엇이든 **한 명령**이다.
- ★★★ **`new T()` 는 제약이 `new()` · `struct` · `class, new()` 어느 것이든 `call System.Activator::CreateInstance<T>` 한 줄** — `struct` 제약이어도 `initobj` 로 **바꾸지 않는다.** (2)의 `Pz` 처럼 **구조체에도 생성자가 있을 수 있기 때문**이다.
- ★★ **`-optimize` 판도 한 글자도 같다** — 최적화가 바꾸는 자리가 아니다.
- ★ 24편 (2)의 덤프는 `call System.Activator::CreateInstance` 였다 — **같은 명령**이다. 이번 판의 IL 도구가 **제네릭 메서드의 타입 인자(`<T>`)까지 찍게** 고쳐졌을 뿐이다.

### (4) ★★ `new T()` 의 생성자가 던지면

```text
===== 소스: cs25b-throw.cs =====
using System;
class Boom { public Boom() { throw new InvalidOperationException("ctor failed"); } }
static class G { public static T Make<T>() where T : new() => new T(); }
class Program {
    static void Main() {
        try { new Boom(); }
        catch (Exception e) { Console.WriteLine($"[1] new Boom()    → {e.GetType().FullName}: {e.Message}"); }
        try { G.Make<Boom>(); }
        catch (Exception e) {
            Console.WriteLine($"[2] Make<Boom>() → {e.GetType().FullName}: {e.Message}");
            Console.WriteLine($"    InnerException → {e.InnerException?.GetType().FullName}: {e.InnerException?.Message}");
        }
    }
}
===== csc -out:ex.dll cs25b-throw.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
[1] new Boom()    → System.InvalidOperationException: ctor failed
[2] Make<Boom>() → System.Reflection.TargetInvocationException: Exception has been thrown by the target of an invocation.
    InnerException → System.InvalidOperationException: ctor failed
===== csc -optimize -out:exo.dll cs25b-throw.cs && DOTNET_TieredCompilation=0 dotnet exo.dll (cc exit=0 · run exit=0) =====
[1] new Boom()    → System.InvalidOperationException: ctor failed
[2] Make<Boom>() → System.Reflection.TargetInvocationException: Exception has been thrown by the target of an invocation.
    InnerException → System.InvalidOperationException: ctor failed
```

- ★★★ **직접 `new Boom()` 은 `InvalidOperationException`**, **`Make<Boom>()`(`new T()`) 은 `System.Reflection.TargetInvocationException`** 이고 원래 예외는 **`InnerException`** 에 있다.
- ★★★ **`catch (InvalidOperationException)` 을 써 둔 코드는 `new T()` 경로에서 못 잡는다** — (3)의 **`Activator` 경유**가 코드의 동작으로 새어 나오는 자리다.
- ★ 두 판(기본 / `-optimize`+`TC=0`)이 같다. **「`Activator` 가 감싼다」는 이 판의 관찰**이다 — 언어 명세는 `new T()` 를 **무엇으로 구현할지** 정하지 않는다.

### (5) ★★★ 리플렉션 — 제약은 어디에 남고, 누가 다시 지키나

**언제 쓰나** — 「제약은 컴파일러가 지키는 것 아닌가 — 런타임은 모르나」.

```text
===== 소스: cs25b-refl.cs =====
using System;
using System.Linq;
struct HasRef { public string S; public HasRef(string s) { S = s; } }
abstract class Shape { }
static class G {
    public static string Class<T>()     where T : class => typeof(T).Name;
    public static string ClassQ<T>()    where T : class? => typeof(T).Name;
    public static string Struct<T>()    where T : struct => typeof(T).Name;
    public static string New<T>()       where T : new() => typeof(T).Name;
    public static string NotNull<T>()   where T : notnull => typeof(T).Name;
    public static string Unmanaged<T>() where T : unmanaged => typeof(T).Name;
    public static string IComp<T>()     where T : IComparable<T> => typeof(T).Name;
    public static string Enum<T>()      where T : System.Enum => typeof(T).Name;
}
class Program {
    static string Attrs(System.Collections.Generic.IList<System.Reflection.CustomAttributeData> xs) =>
        string.Join(",", xs.Select(a => a.AttributeType.Name.Replace("Attribute", "") + "(" + string.Join(",", a.ConstructorArguments.Select(x => x.Value)) + ")"));
    static void Try(string m, Type arg) {
        try { var r = typeof(G).GetMethod(m)!.MakeGenericMethod(arg).Invoke(null, null); Console.WriteLine($"   {m,-9}<{arg.Name,-11}> ok → {r}"); }
        catch (Exception e) { Console.WriteLine($"   {m,-9}<{arg.Name,-11}> {e.GetType().Name}"); }
    }
    static void Main() {
        Console.WriteLine($"[A] 제약이 메타데이터에 남은 모양 (클래스 G 의 특성=[{Attrs(typeof(G).GetCustomAttributesData())}])");
        foreach (var n in new[] { "Class", "ClassQ", "Struct", "New", "NotNull", "Unmanaged", "IComp", "Enum" }) {
            var mi = typeof(G).GetMethod(n)!;
            var t = mi.GetGenericArguments()[0];
            Console.WriteLine($"   {n,-9} 플래그={t.GenericParameterAttributes} · 타입=[{string.Join(",", t.GetGenericParameterConstraints().Select(c => c.Name))}] · T 특성=[{Attrs(t.GetCustomAttributesData())}] · 메서드 특성=[{Attrs(mi.GetCustomAttributesData())}]");
        }
        Console.WriteLine("[B] 컴파일러를 건너뛰고 MakeGenericMethod 로 어긴 인자를 넣으면");
        Try("Class", typeof(int)); Try("Struct", typeof(string)); Try("Struct", typeof(int?)); Try("New", typeof(Shape));
        Try("IComp", typeof(Shape)); Try("Enum", typeof(int)); Try("Unmanaged", typeof(string));
        Try("Unmanaged", typeof(HasRef)); Try("NotNull", typeof(string));
    }
}
===== csc -nullable:enable -out:ex.dll cs25b-refl.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
[A] 제약이 메타데이터에 남은 모양 (클래스 G 의 특성=[NullableContext(1),Nullable(0)])
   Class     플래그=ReferenceTypeConstraint · 타입=[] · T 특성=[] · 메서드 특성=[]
   ClassQ    플래그=ReferenceTypeConstraint · 타입=[] · T 특성=[Nullable(2)] · 메서드 특성=[]
   Struct    플래그=NotNullableValueTypeConstraint, DefaultConstructorConstraint · 타입=[ValueType] · T 특성=[] · 메서드 특성=[NullableContext(0)]
   New       플래그=DefaultConstructorConstraint · 타입=[] · T 특성=[Nullable(2)] · 메서드 특성=[]
   NotNull   플래그=None · 타입=[] · T 특성=[] · 메서드 특성=[]
   Unmanaged 플래그=NotNullableValueTypeConstraint, DefaultConstructorConstraint · 타입=[ValueType] · T 특성=[IsUnmanaged()] · 메서드 특성=[NullableContext(0)]
   IComp     플래그=None · 타입=[IComparable`1] · T 특성=[Nullable(0)] · 메서드 특성=[]
   Enum      플래그=None · 타입=[Enum] · T 특성=[Nullable(0)] · 메서드 특성=[]
[B] 컴파일러를 건너뛰고 MakeGenericMethod 로 어긴 인자를 넣으면
   Class    <Int32      > ArgumentException
   Struct   <String     > ArgumentException
   Struct   <Nullable`1 > ArgumentException
   New      <Shape      > ArgumentException
   IComp    <Shape      > ArgumentException
   Enum     <Int32      > ArgumentException
   Unmanaged<String     > ArgumentException
   Unmanaged<HasRef     > ok → HasRef
   NotNull  <String     > ok → String
```

- ★★★ **[A] `class`·`struct`·`new()` 는 CLI 플래그**(`ReferenceTypeConstraint` · `NotNullableValueTypeConstraint` · `DefaultConstructorConstraint`), **인터페이스·`Enum` 은 타입 목록**으로 남는다.
- ★★★ **`struct` 는 플래그 둘**(`NotNullableValueTypeConstraint, DefaultConstructorConstraint`) + 타입 `ValueType` — **값 타입이면 기본 생성자가 있다**는 뜻까지 CLI 가 적는다.
- ★★★ **`class?` 는 `class` 와 플래그가 같다** — 다른 것은 **`Nullable(2)` 특성**뿐이다. **`notnull` 은 플래그가 `None`** — 클래스에 붙은 **`NullableContext(1)`** 이 전부다.
- ★★★ **`unmanaged` 는 `struct` 와 플래그가 같고 `IsUnmanaged` 특성이 더 붙는다.**
- ★★★ **[B] 컴파일러를 건너뛰어도 런타임이 막는다** — `Class<Int32>` · `Struct<String>` · `Struct<Nullable>` · `New<Shape>` · `IComp<Shape>` · `Enum<Int32>` · `Unmanaged<String>` 이 전부 **`ArgumentException`**.
- ★★★ **그런데 `Unmanaged<HasRef>`(문자열 필드를 품은 구조체)는 `ok`** — 런타임은 **`struct` 플래그만** 본다. **「참조를 품지 않는다」는 컴파일러 혼자의 약속**이다. **`NotNull<String>` 도 `ok`** — 런타임에 `string?` 과 `string` 이 **같은 타입**이라 가를 것이 없다.

> **어느 층인가** — ★★★ **플래그가 있는 제약은 ECMA-335 가 보장**한다(런타임 검사까지). **`notnull`·`class?`·`unmanaged` 의 「참조 없음」은 Roslyn 이 특성으로 적은 것**이고, 그 특성을 읽는 것은 **다음 컴파일러**다 — 다른 언어·리플렉션은 지키지 않을 수 있다.

### (6) ★★ 제약과 오버로드 — 서명으로는 못 가른다 · 후보는 거른다

```text
===== 소스: cs25b-sig.cs =====
static class S {
    public static void G<T>(T x) where T : class { }
    public static void G<T>(T x) where T : struct { }
}
class Program { static void Main() { } }
===== csc -out:ex.dll cs25b-sig.cs (cc exit=1) =====
cs25b-sig.cs(3,24): error CS0111: Type 'S' already defines a member called 'G' with the same parameter types
===== 소스: cs25b-ovl.cs =====
using System;
static class O {
    public static string F<T>(T x) where T : struct => "F<T>(T) where T : struct";
    public static string F(object o) => "F(object)";
}
class Program {
    static void Main() {
        Console.WriteLine($"O.F(1)   → {O.F(1)}");
        Console.WriteLine($"O.F(\"s\") → {O.F("s")}");
    }
}
===== csc -langversion:7.2 -out:ex.dll cs25b-ovl.cs && dotnet ex.dll (cc exit=1) =====
cs25b-ovl.cs(9,43): error CS0453: The type 'string' must be a non-nullable value type in order to use it as parameter 'T' in the generic type or method 'O.F<T>(T)'
===== csc -langversion:7.3 -out:ex.dll cs25b-ovl.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
O.F(1)   → F<T>(T) where T : struct
O.F("s") → F(object)
===== csc -langversion:latest -out:ex.dll cs25b-ovl.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
O.F(1)   → F<T>(T) where T : struct
O.F("s") → F(object)
```

- ★★★ **제약만 다른 두 `G<T>(T)` 는 `CS0111`**(「**같은 매개변수 타입**의 멤버가 이미 있다」) — **제약은 서명의 일부가 아니다.**
- ★★★ **그런데 「제약은 오버로드 해결에 안 참여한다」는 C# 7.2 까지의 이야기다** — `F<T>(T) where T : struct` 와 `F(object)` 에 `"s"` 를 넘기면\
  **7.2 는 `CS0453`**(제네릭 후보를 골라 놓고 **제약 위반으로 실패**) · **7.3 부터는 `F(object)`** 가 골라진다. **제약을 어기는 후보를 먼저 걸러 낸다.**
- ★ Learn 의 버전 이력이 7.3 에 「**오버로드 해결의 모호한 경우가 줄었다**」로 적은 것이 이 자리다. **판 격자 한 번이 문서의 한 줄을 실측으로 바꿨다.**

### (7) ★★ 판 경계 — 제약 문법은 언제 들어왔나

```text
===== 소스: cs25b-ver.cs =====
using System;
static class V {
    public static void A<T>() where T : Enum { }
    public static void B<T>() where T : Delegate { }
    public static void C<T>() where T : unmanaged { }
    public static void D<T>() where T : notnull { }
    public static T? E<T>() => default;
}
class Program { static void Main() { } }
===== csc -langversion:7.2 -out:ex.dll cs25b-ver.cs 2>&1 | sort (cc exit=1) =====
cs25b-ver.cs(3,41): error CS8320: Feature 'enum generic type constraints' is not available in C# 7.2. Please use language version 7.3 or greater.
cs25b-ver.cs(4,41): error CS8320: Feature 'delegate generic type constraints' is not available in C# 7.2. Please use language version 7.3 or greater.
cs25b-ver.cs(5,41): error CS8320: Feature 'unmanaged generic type constraints' is not available in C# 7.2. Please use language version 7.3 or greater.
cs25b-ver.cs(6,41): error CS8320: Feature 'notnull generic type constraint' is not available in C# 7.2. Please use language version 8.0 or greater.
cs25b-ver.cs(7,19): error CS8627: A nullable type parameter must be known to be a value type or non-nullable reference type unless language version '9.0' or greater is used. Consider changing the language version or adding a 'class', 'struct', or type constraint.
cs25b-ver.cs(7,20): error CS8320: Feature 'nullable reference types' is not available in C# 7.2. Please use language version 8.0 or greater.
===== csc -langversion:7.3 -out:ex.dll cs25b-ver.cs 2>&1 | sort (cc exit=1) =====
cs25b-ver.cs(6,41): error CS8370: Feature 'notnull generic type constraint' is not available in C# 7.3. Please use language version 8.0 or greater.
cs25b-ver.cs(7,19): error CS8627: A nullable type parameter must be known to be a value type or non-nullable reference type unless language version '9.0' or greater is used. Consider changing the language version or adding a 'class', 'struct', or type constraint.
cs25b-ver.cs(7,20): error CS8370: Feature 'nullable reference types' is not available in C# 7.3. Please use language version 8.0 or greater.
===== csc -langversion:8 -out:ex.dll cs25b-ver.cs 2>&1 | sort (cc exit=1) =====
cs25b-ver.cs(7,19): error CS8627: A nullable type parameter must be known to be a value type or non-nullable reference type unless language version '9.0' or greater is used. Consider changing the language version or adding a 'class', 'struct', or type constraint.
cs25b-ver.cs(7,20): warning CS8632: The annotation for nullable reference types should only be used in code within a '#nullable' annotations context.
===== csc -langversion:9 -out:ex.dll cs25b-ver.cs 2>&1 | sort (cc exit=0) =====
cs25b-ver.cs(7,20): warning CS8632: The annotation for nullable reference types should only be used in code within a '#nullable' annotations context.
===== 판 × 줄 — 줄마다 에러 코드(없으면 ok). 3 Enum · 4 Delegate · 5 unmanaged · 6 notnull · 7 제약 없는 T? =====
C# 7.2;3:CS8320;4:CS8320;5:CS8320;6:CS8320;7:CS8320,CS8627
C# 7.3;3:ok;4:ok;5:ok;6:CS8370;7:CS8370,CS8627
C# 8;3:ok;4:ok;5:ok;6:ok;7:CS8627
C# 9;3:ok;4:ok;5:ok;6:ok;7:ok
막힌 칸 8 / 20
```

- ★★★ **막힌 칸 8 / 20** — **7.2 에서 `Enum`·`Delegate`·`unmanaged`·`notnull`·`T?` 전부**, **7.3 에서 `notnull`·`T?`**, **8 에서 `T?`** 만, **9 에서 0**.
- ★★★ **진단 문구에 요구 판이 박혀 나온다** — `'enum generic type constraints' … 7.3` · `'notnull generic type constraint' … 8.0` · 제약 없는 `T?` 는 `CS8627` 이 **`'9.0' or greater`** 를 말한다.
- ★ 코드 자체도 판마다 다르다 — **7.2 는 `CS8320`, 7.3 은 `CS8370`**(같은 「기능 없음」인데 **요청 판별로 번호가 다르다**).

### (8) ★★★ `T?` 가 무엇이 되나 — 그리고 조건 연산자 안의 `default`

```text
===== 소스: cs25b-tq.cs =====
using System;
static class F {
    public static T? Any<T>(bool hit, T v) => hit ? v : default;
    public static T? Val<T>(bool hit, T v) where T : struct => hit ? v : default;
    public static T? Val2<T>(bool hit, T v) where T : struct => hit ? v : default(T?);
    public static T? Ref<T>(bool hit, T v) where T : class => hit ? v : default;
}
class Program {
    static string S(object? o) => o is null ? "null" : o.ToString()!;
    static string Ret(string m) => typeof(F).GetMethod(m)!.MakeGenericMethod(typeof(int)).ReturnType.Name;
    static void Main() {
        Console.WriteLine($"[1] Any(false, 5)   = {S(F.Any(false, 5))} · Any<int> 반환 타입 {Ret("Any")}");
        Console.WriteLine($"[2] Val(false, 5)   = {S(F.Val(false, 5))} · Val<int> 반환 타입 {Ret("Val")}");
        Console.WriteLine($"[3] Val2(false, 5)  = {S(F.Val2(false, 5))} · Val2<int> 반환 타입 {Ret("Val2")}");
        Console.WriteLine($"[4] Any(false, \"a\") = {S(F.Any(false, "a"))}");
        Console.WriteLine($"[5] Ref(false, \"a\") = {S(F.Ref(false, "a"))}");
    }
}
===== csc -nullable:enable -out:ex.dll cs25b-tq.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
[1] Any(false, 5)   = 0 · Any<int> 반환 타입 Int32
[2] Val(false, 5)   = 0 · Val<int> 반환 타입 Nullable`1
[3] Val2(false, 5)  = null · Val2<int> 반환 타입 Nullable`1
[4] Any(false, "a") = null
[5] Ref(false, "a") = null
```

- ★★★ **`[1]` 제약 없는 `T?` 에 `int` 를 넣으면 반환 타입이 `Int32`** — **`Nullable<int>` 가 아니다.** 그래서 「없음」이 **`null` 이 아니라 `0`** 으로 나온다.
- ★★★ **`[2]` `struct` 제약이면 반환 타입이 ``Nullable`1`` 인데도 값이 `0`** — `hit ? v : default` 에서 **`default` 의 타입은 조건식의 타입 `T`** 로 정해진다. `default(T)`=`0` 을 만든 뒤 `T?` 로 **감싸** 돌려준다.
- ★★★ **`[3]` `default(T?)` 로 적어야 `null`** 이다.
- ★ **`[4]`·`[5]` 참조 타입은 어느 쪽이든 `null`** — 참조 타입의 `T?` 는 **같은 타입에 붙은 주석**일 뿐이다.

```text
   T? 의 뜻 — 제약이 정한다

   제약        T 에 int 를 넣으면      T 에 string 을 넣으면       「없음」을 돌려주려면
   (없음)      T? = int   (!)          T? = string (주석)          default → 0 / null
   struct      T? = Nullable<int>      (못 넣는다 CS0453)           default(T?) → null   ← default 만 쓰면 0
   class       (못 넣는다 CS0452)       T? = string (주석)          default → null

   ★★★ 제약 없는 T? 에서 값 타입은 「널이 될 수 있는 타입」 이 되지 않는다.
```

### (9) ★ 할당 바이트 — `new T()` 는 객체 하나 말고 더 할당하나

```text
===== 소스: cs25b-alloc.cs =====
using System;
class Node { public int V = 1; }
struct Pv { public int V; public Pv(int v) { V = v; } }
static class G {
    public static T Make<T>() where T : new() => new T();
    public static T Def<T>() => default!;
}
class Program {
    static long M(Action a) {
        for (int i = 0; i < 200; i++) a();
        var b = GC.GetAllocatedBytesForCurrentThread();
        a();
        return GC.GetAllocatedBytesForCurrentThread() - b;
    }
    static void Main() {
        long sink = 0;
        Console.WriteLine($"[1] new Node()      1000번 : {M(() => { for (int i = 0; i < 1000; i++) sink += new Node().V; })} 바이트");
        Console.WriteLine($"[2] G.Make<Node>()  1000번 : {M(() => { for (int i = 0; i < 1000; i++) sink += G.Make<Node>().V; })} 바이트");
        Console.WriteLine($"[3] G.Make<Pv>()    1000번 : {M(() => { for (int i = 0; i < 1000; i++) sink += G.Make<Pv>().V; })} 바이트");
        Console.WriteLine($"[4] G.Def<Node>()   1000번 : {M(() => { for (int i = 0; i < 1000; i++) sink += G.Def<Node>() is null ? 1 : 0; })} 바이트");
        Console.WriteLine($"[5] G.Def<Pv>()     1000번 : {M(() => { for (int i = 0; i < 1000; i++) sink += G.Def<Pv>().V; })} 바이트");
        GC.KeepAlive(sink);
    }
}
===== csc -out:ex.dll cs25b-alloc.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
[1] new Node()      1000번 : 24000 바이트
[2] G.Make<Node>()  1000번 : 24000 바이트
[3] G.Make<Pv>()    1000번 : 0 바이트
[4] G.Def<Node>()   1000번 : 0 바이트
[5] G.Def<Pv>()     1000번 : 0 바이트
===== csc -out:ex.dll cs25b-alloc.cs && DOTNET_TieredCompilation=0 dotnet ex.dll (cc exit=0 · run exit=0) =====
[1] new Node()      1000번 : 24000 바이트
[2] G.Make<Node>()  1000번 : 24000 바이트
[3] G.Make<Pv>()    1000번 : 0 바이트
[4] G.Def<Node>()   1000번 : 0 바이트
[5] G.Def<Pv>()     1000번 : 0 바이트
===== csc -optimize -out:exo.dll cs25b-alloc.cs && dotnet exo.dll (cc exit=0 · run exit=0) =====
[1] new Node()      1000번 : 24000 바이트
[2] G.Make<Node>()  1000번 : 24000 바이트
[3] G.Make<Pv>()    1000번 : 0 바이트
[4] G.Def<Node>()   1000번 : 0 바이트
[5] G.Def<Pv>()     1000번 : 0 바이트
===== csc -optimize -out:exo.dll cs25b-alloc.cs && DOTNET_TieredCompilation=0 dotnet exo.dll (cc exit=0 · run exit=0) =====
[1] new Node()      1000번 : 24000 바이트
[2] G.Make<Node>()  1000번 : 24000 바이트
[3] G.Make<Pv>()    1000번 : 0 바이트
[4] G.Def<Node>()   1000번 : 0 바이트
[5] G.Def<Pv>()     1000번 : 0 바이트
===== 네 판 대조 — 「바이트」 줄마다 네 판의 값이 같은가 =====
네 판에서 갈린 줄 0 / 5
```

- ★★★ **네 판에서 갈린 줄 0 / 5** — **`new Node()` 24000 과 `G.Make<Node>()` 24000 이 같다** · `Make<Pv>`(구조체) **0** · `default(T)` 는 **둘 다 0**.
- ★★ **`Activator` 경유여도 이 판에서 추가 할당은 없었다** — 객체 **24바이트 × 1000** 이 전부다.
- ★ **시간은 안 쟀다.** 「`new T()` 는 느리다」는 **이 문서에 근거가 없다.**

## 문법 — 형태와 규칙

### 형태

```text
===== 소스: cs25b-form.cs =====
using System;
using System.Collections.Generic;

Console.WriteLine($"{Max(3, 9)} · {Max("pear", "apple")} · {Fresh<List<int>>().Count} · {Name(DayOfWeek.Friday)} · {Sum(new[] { 1, 2, 3 })}");

static T Max<T>(T a, T b) where T : IComparable<T> => a.CompareTo(b) >= 0 ? a : b;
static T Fresh<T>() where T : new() => new T();
static string Name<T>(T v) where T : struct, Enum => $"{typeof(T).Name}.{v}";
static int Sum<T>(T[] xs) where T : unmanaged, IConvertible {
    int s = 0;
    foreach (var x in xs) s += x.ToInt32(null);
    return s;
}
===== csc -out:ex.dll cs25b-form.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
9 · pear · 0 · DayOfWeek.Friday · 6
```

- ★★★ **제약을 여럿 걸 때 순서가 있다** — `struct`/`class`/기반 클래스가 **맨 앞**, 인터페이스가 가운데, **`new()` 는 맨 끝**(Learn).
- ★★ **`where T : struct, Enum`** — enum 만 받는 제네릭(7.3). (1)의 `Enum` 행에서 통과한 인자는 **`DayOfWeek` 하나**였다.
- ★★ **`where T : unmanaged, IConvertible`** — `unmanaged` 는 `struct` 를 **포함**한다((5)의 플래그가 같다). Learn 은 둘을 **함께 쓸 수 없다**고 적는다.
- ★ **`new()` 는 인자 없는 생성자만** — 인자를 받는 생성자는 제약으로 표현할 수 없다.

### 금지 사례 — 진단이 나는 꼴

| 쓴 꼴 | 진단 코드 | 어디서 |
|---|---|---|
| `class` 제약에 값 타입 | `CS0452` | (1) |
| `struct`·`unmanaged` 에 참조 타입·`int?` | `CS0453` · `CS8377` | (1) |
| `new()` 에 추상 클래스·`string`·델리게이트 | `CS0310` | (1) |
| 인터페이스·기반 클래스 제약 위반 | `CS0311`(참조) · `CS0315`(값) · `CS0312`/`CS0313`(`int?`) | (1) |
| `class`·인터페이스 제약에 `string?` | `CS8634` · `CS8631`(**경고**) | (1) |
| `notnull` 에 `int?`·`string?` | `CS8714`(**경고**) | (1) |
| ★★★ 제약만 다른 오버로드 둘 | `CS0111` | (6) |
| 7.2 판에 `Enum`/`unmanaged` 제약 · 8 판에 제약 없는 `T?` | `CS8320` · `CS8627` | (7) |

## 어디서 틀리나

1. ★★★ **「제약은 컴파일러가 지키는 것」** — `class`·`struct`·`new()`·타입 제약은 **런타임도 다시 막는다**((5) [B]). 반대로 **`notnull`·`unmanaged` 의 「참조 없음」은 런타임이 모른다.**
2. ★★★ **「`default(T)` 와 `new T()` 는 같다」** — 매개변수 없는 생성자가 있는 구조체에서 **`0` 대 `7`**((2)).
3. ★★★ **「제약 없는 `T?` 는 `Nullable<T>`」** — **`T` 그대로**다. `int` 면 `null` 이 아니라 `0`((8) [1]).
4. ★★★ **「`struct` 제약의 `T?` 에 `default` 를 주면 `null`」** — 조건식 안에서는 **`0` 이 감싸여 나온다**((8) [2]).
5. ★★★ **「제약은 오버로드 해결에 안 참여한다」** — **7.3 부터 후보를 거른다**((6)). 다만 **서명은 못 가른다**(`CS0111`).
6. ★★ **「`new T()` 는 생성자 예외를 그대로 던진다」** — **`TargetInvocationException` 으로 감싼다**(이 판 · (4)).
7. ★★ **「`struct` 제약이면 `int?` 도」** — **`CS0453`**. 반대로 **`new()` 는 `int?` 를 받는다**((1)).
8. ★★ **「`where T : class` 면 `==` 가 `string` 을 값으로 비교한다」** — **참조 비교**다([19번](../19-equality-equals-gethashcode-operator/) (3)의 `box`·`box`·`ceq`).
9. ★ **「`notnull` 을 어기면 컴파일이 안 된다」** — **경고**다((1)). 경고를 에러로 올리려면 `-warnaserror` 류가 따로 필요하다.

## 구현 세부사항 대 언어 보장

| 무엇 | 층 | 근거 |
|---|---|---|
| **`class`·`struct`·`new()`·타입 제약이 메타데이터에 남고 런타임이 검사** | ★★★ **CLI 명세(ECMA-335)** | (5) |
| **제약 위반이 컴파일 에러 · 제약은 서명이 아니다** | ★★★ **언어(334)** | (1)(6) |
| **`default(T)` 가 그 타입의 기본값** | ★★★ **언어** | (2) |
| **7.3 부터 제약 위반 후보를 거른다** | ★★ **언어 판(7.3)** | (6) |
| **`notnull`·`class?` 가 경고 · 특성으로만 남는다** | ★★ **Roslyn(널 분석)** | (1)(5) |
| **`unmanaged` = `struct` 플래그 + `IsUnmanaged` 특성** | ★★ **Roslyn** | (5) |
| **`new T()` → `Activator.CreateInstance<T>`** | ★ **Roslyn 구현** | (3) |
| **생성자 예외가 `TargetInvocationException` 으로** | ★ **이 판(BCL)의 관찰** | (4) |
| **할당 바이트 값** | ★ **이 판의 관찰** | (9) |

## 언제 쓰고 언제 안 쓰나

- ★★★ **제약은 「안에서 무엇을 부를 것인가」만큼만** — `CompareTo` 가 필요하면 `IComparable<T>`, `new T()` 가 필요하면 `new()`. **필요 없는 제약은 호출자를 좁힌다**((1)의 47칸).
- ★★★ **「없음」을 돌려주는 제네릭은 `T?` 의 뜻을 제약으로 못 박아라** — 제약 없는 `T?` 는 값 타입에서 **`0` 을 「없음」으로 돌려준다**((8)). `struct` 쪽이면 **`default(T?)`** 로.
- ★★ **생성 비용·예외 경로가 중요하면 `new()` 대신 `Func<T>` 를 받아라** — `Activator` 경유와 예외 감싸기를 피한다((4)). 델리게이트는 [27번](../27-delegates-and-func-action/).
- ★★ **`notnull`·`class?` 는 문서화 도구로** — 런타임 보장이 아니다((5)).
- ★ **`unmanaged` 는 포인터·`stackalloc`·직렬화에서** — 「참조 없음」을 **컴파일러가** 보증한다. 리플렉션으로 넣는 쪽은 스스로 지켜야 한다.

## 핵심 문장

1. ★★★ **제약 10 × 인자 8 = 80칸에서 막힌 칸 47 · 경고만 4 · 통과 29** — `int?` 는 `struct`·`unmanaged`·인터페이스에 막히고 `new()` 는 통과한다((1)).
2. ★★★ **`class`·`struct`·`new()`·타입 제약은 CLI 가 다시 지키고, `notnull`·`class?`·`unmanaged` 의 「참조 없음」은 컴파일러만 지킨다**((5)).
3. ★★★ **`default(T)` 는 「생성자 없이 전부 0」** — 구조체에서는 **`new T()` 와 값이 다르다**((2)).
4. ★★★ **제약 없는 `T?` 는 값 타입에서 `T` 그대로**다 — 「없음」이 `0` 이 된다((8)).
5. ★★ **제약은 서명이 아니다(`CS0111`) · 그러나 7.3 부터 후보를 거른다**((6)).

## 관련 자료

- [24번 — 제네릭](../24-generics-and-type-parameters/) (2)(6) — `new T()` 의 IL 과 제약 위반 **여섯**을 먼저 던졌다. **경계**: 「런타임까지 남는다」는 거기, **제약 전수와 `default(T)`** 는 여기.
- [19번 — 동등성](../19-equality-equals-gethashcode-operator/) (3) — `where T : class` 의 `==` 가 참조 비교.
- [20번 — `enum`](../20-enum-and-flags/) — `where T : Enum` 의 대상.
- [06번 — 널 허용 참조 타입](../06-nullable-reference-types/) · [08번 — `Nullable<T>`](../08-nullable-value-types/) — `notnull`·`class?`·`int?` 칸의 배경.
- [26번 — 공변·반변](../26-covariance-and-contravariance-out-in/) — 제약 다음의 제네릭 사슬.
- Java 갈래 목록([`java/syntax/README.md`](../../../java/syntax/README.md))의 **17번**([`17-generic-declarations/`](../../../java/syntax/17-generic-declarations/)) — **경계**: Java 의 상한 `extends` 는 거기(소거 위에서 `new T()` 가 원리상 없다 — 24편 (3)).
- Kotlin 갈래 목록([`kotlin/syntax/README.md`](../../../kotlin/syntax/README.md))의 **28번**([`28-generics-variance-in-out-star-where/`](../../../kotlin/syntax/28-generics-variance-in-out-star-where/)) — Kotlin 의 `where` 와 상한.

## 용어 풀이

- **제약(constraint)** — 타입 매개변수에 올 수 있는 인자의 조건. `where T : …`.
- **`default(T)`** — `T` 의 기본값. 값 타입은 모든 필드가 0, 참조 타입은 `null`. 생성자를 부르지 않는다.
- **`initobj`** — 주소가 가리키는 값 타입 칸을 0 으로 채우는 IL 명령. `T` 가 참조 타입이면 `null` 을 넣는다.
- **`Activator.CreateInstance<T>()`** — 런타임에 `T` 의 매개변수 없는 생성자를 찾아 부르는 BCL 메서드.
- **`TargetInvocationException`** — 리플렉션으로 부른 대상이 던진 예외를 감싸는 예외. 원래 예외는 `InnerException`.
- **`GenericParameterAttributes`** — 리플렉션이 돌려주는 제약 플래그 묶음(ECMA-335 의 타입 매개변수 플래그).
- **`NullableContext`·`Nullable` 특성** — 널 허용 주석을 메타데이터에 남기려고 Roslyn 이 붙이는 특성. 런타임은 읽지 않는다.
- **비관리형 타입(unmanaged type)** — 참조를 어느 깊이에도 품지 않는 값 타입.

## 더 들어가면

- ★ **`allows ref struct` 반(反)제약(C# 13)** — `ref struct` 를 타입 인자로 받게 한다(Learn). **이 판에서 안 던졌다.**
- ★ **`where T : default`(C# 9)** — 재정의에서 `T?` 의 뜻을 고르는 제약. **안 던졌다.**
- ★ **정적 추상 멤버 제약**(`where T : INumber<T>` — 제네릭 수학) — [17번](../17-interfaces-default-members-explicit-implementation/) (8)의 `static abstract` 가 뿌리다. 여기서는 안 다뤘다.
