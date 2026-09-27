# csharp/syntax/20 — `enum` 과 `[Flags]` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [ECMA-334 7판(2023-12)](https://ecma-international.org/publications-and-standards/standards/ecma-334/) ·
> [Learn — 열거형](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/builtin-types/enum)(열어서 확인: 「열거형은 **기반 정수 타입의 이름 붙은 상수**로 정의되는 **값 타입**」 ·\
> 「`E` 의 기본값은 **`(E)0`** — 0 에 해당하는 멤버가 **없어도**」 · 「리터럴 `0` 은 **어느 열거형으로든 암시적 변환**된다」 · 「`(Season)4` 는 **`4`** 를 찍는다」 · 「`Enum.IsDefined` 로 확인하라」)
> **실행 검증** — 이 문서의 모든 출력·진단·IL·할당 바이트는 아래 「이 판」의 도구로 **실제로 돌려 얻은 것**이다(2026-09-26).\
> ★ 블록은 캡처 스크립트가 파일로 받아 조립기가 끼워 넣은 것이다 — 사람이 옮겨 적은 줄은 하나도 없다.\
> ★★★ **진단 언어를 영어로 고정했다**(`DOTNET_CLI_UI_LANGUAGE=en` + `-preferreduilang:en-US`).\
> **대비는 실측이다** — **javac 21.0.5** 로 같은 캐스트를 던졌다((8)).
> **버전** — `enum`·`[Flags]` 는 **C# 1.0부터** · 제네릭 `Enum.IsDefined<T>`·`Enum.Parse<T>` 는 **.NET 5 / .NET Core 2.0 계열 API** 다(이 문서는 판을 안 가렸다 — .NET 10 에서만 던졌다).
> **경계** — **정수 타입·`checked`** 는 [05번](../05-numeric-types-checked-decimal/)이 정본이다 — `enum` 은 **그 정수 위의 껍데기**다.\
> ★ **`switch` 식의 완결성 검사 전반**은 목록의 **22번 주제**가 정본이다 — 여기서는 **`enum` 에서 그것이 어떻게 새나**만 본다.\
> ★ **박싱 자체**는 [03번](../03-boxing-and-unboxing/)이 정본이다.
> ★★★ **대비** — Java 갈래 목록([`java/syntax/README.md`](../../../java/syntax/README.md))의 **13번**([`13-enum-classes/`](../../../java/syntax/13-enum-classes/)) — Java `enum` 은 **진짜 클래스**다.\
> Kotlin 갈래 목록([`kotlin/syntax/README.md`](../../../kotlin/syntax/README.md))의 **26번**([`26-value-class-and-boxing/`](../../../kotlin/syntax/26-value-class-and-boxing/)) — 「**값 하나를 감싼 껍데기**」의 다른 설계 ·\
> Rust 갈래 목록([`rust/syntax/README.md`](../../../rust/syntax/README.md))의 **17번**([`17-enums-and-data-carrying-variants/`](../../../rust/syntax/17-enums-and-data-carrying-variants/)) — **데이터를 싣는 변형**. ★ 둘은 **대비만** 한다(이 판에서 던지지 않았다).
>
> ★★ **흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | 진단 **문구** | ★★★ **진단 코드**(`CS8509`·`CS8524`·`CS0019`·`CS0221`·`CS0266`)와 **`(행,열)`** |
> | **IL 오프셋 폭** | ★★★ **옵코드**(`ldc.i4.s 99` · `ceq` · `box Perm`) — **변환 명령이 없다는 것** |
> | ★★★ **증분의 절댓값 일부** — 특히 **`HasFlag` 의 48 바이트는 판에 따라 0 이 된다**((6)) | ★★★ **네 판에서 갈린 줄 수**(스크립트가 센 마지막 줄) · **어느 판에서 갈렸나** |
> | 「데운 정도」 — 티어 1 로 올라가는 시점은 **시간에 달린다**((6)의 긴 데우기 판) | ★★ `IsJITOptimizerDisabled` 의 **`True`/`False`** |

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
| **언어 명세(ECMA-334)** | C# 언어가 약속한 것 | ★★★ **정수와 명시적 변환이 늘 된다**(`(Color)99`) · 리터럴 `0` 의 암시적 변환 · 상수 범위 검사(`CS0221`) · 멤버 이름은 **컴파일 시점 상수** |
| **런타임·BCL(`System.Enum`)** | CoreCLR·BCL 이 그렇게 하는 것 | ★★★ `ToString`·`IsDefined`·`Parse`·`HasFlag` 의 동작 · **`[Flags]` 를 보고 `ToString` 을 바꾸는 것** · 필드 `value__` |
| **이 판의 관찰** | .NET 10.0.12 · linux-x64 · javac 21.0.5 | ★★★ **`HasFlag` 박싱이 판에 따라 0 과 48 을 오가는 것** · 진단 문구 |

★★★ **이 주제에서 `[Flags]` 는 둘째 칸이다** — `|` 는 `[Flags]` 가 없어도 컴파일되고((3) `[2]`), `[Flags]` 규칙을 어겨도 **진단이 없다**((7) 탐침 1·2).\
`ToString` 이 `"Read, Exec"` 를 찍느냐 `"5"` 를 찍느냐는 **BCL 이 런타임에 특성을 읽어서** 정한다((3)).

## 한눈에 — 쉽게 말하면

**`enum` 은 정수에 붙인 이름표다 — 이름표가 없는 정수도 그대로 들어간다.**

엘리베이터 층 버튼을 생각하자.

- **`enum Color { Red, Green, Blue }`** — 버튼 **0·1·2 에 이름표**를 붙인 것. 버튼 자체는 **그냥 번호**다.
- **`(Color)99`** — ★★★ **99층 버튼을 누르는 것**. 그런 층은 없는데 **엘리베이터(런타임)는 막지 않는다.** 이름표만 없을 뿐이다.
- **`Enum.IsDefined`** — 「**이 번호에 이름표가 있나**」를 묻는 것. 막아 주지는 않는다 — **물어봐야 안다.**
- **`[Flags]`** — 버튼이 아니라 **스위치 여러 개**다. 켠 것들의 이름을 **쉼표로 이어** 읽어 준다.
- **라이브러리의 enum** — ★★ 이름표는 **컴파일 때 번호로 바뀌어** 내 프로그램에 박힌다. 라이브러리가 이름표 순서를 바꾸면 **내 프로그램은 옛 번호를 누른다.**

| 비유 | 실체 | 어디서 보나 |
|---|---|---|
| 버튼은 그냥 번호다 | ★★★ **`Color.Red` 는 IL 에서 `ldc.i4.0`** · `(Color)99` 는 **`ldc.i4.s 99` 한 줄** | (1) |
| 없는 층도 눌린다 | ★★★ **`(Color)99` 는 에러 없이 `99`** · `IsDefined` 는 `False` | (1) |
| 스위치 이름을 쉼표로 | ★★★ **`[Flags]` 면 `"Read, Exec"`, 없으면 `"5"`** | (3) |
| 이름표가 번호로 박힌다 | ★★★ **라이브러리 enum 순서를 바꾸면 `Green` 이 `Yellow` 로 읽힌다** | (5) |
| 모든 층을 다 적었는데 경고 | ★★ **`switch` 식은 이름 없는 값까지 요구한다**(`CS8524`) | (4) |

★★★ **이 주제의 본체 그림 — `enum` 은 IL 에서 사라진다.**

```text
   C# 소스                              IL (Probe.IsRed · Make · ToInt)
   ───────────────────────────          ─────────────────────────────────
   c == Color.Red                  →    ldarg.0 / ldc.i4.0 / ceq            ← Red 는 0 이라는 정수
   (Color)99                       →    ldc.i4.s 99                         ← 캐스트 명령이 없다
   (int)c                          →    ldarg.0                             ← 변환 명령이 없다

   ★★★ 이름(Red)·타입(Color)·캐스트는 전부 컴파일러 안에서만 산다.
       IL 에 남는 것은 정수 하나 — 그래서 (Color)99 를 막을 자리가 런타임에 없다.
```

## 이 주제가 답하려는 질문

1. **`enum` 은 런타임에 무엇인가** — 정수인가 객체인가((1)(2)).
2. **`[Flags]` 는 무엇을 바꾸나** — 무엇은 안 바꾸나((3)).
3. **`switch` 식은 `enum` 을 완결되게 강제하나**((4)).
4. **`HasFlag` 는 박싱하나** — 판을 바꾸면((6)).
5. **Java·Kotlin·Rust 의 열거형과 무엇이 다른가**((8)).

## 동작 방식

### (0) 이 주제가 쓰는 창

★★★ **본체 창은 ① IL 덤프다** — 「`enum` 이 정수 위의 껍데기」는 **IL 에 `Color` 가 안 남는 것**으로만 증명된다.

| 창 | 무엇을 보여 주나 | 이 주제에서 |
|---|---|---|
| ★★★ **① IL 덤프** | ★★★ **`ldc.i4.s 99` 한 줄** · 비교가 **`ceq`** · 캐스트가 **명령 0개** · `HasFlag` 의 **`box Perm` 둘** | (1)(6) |
| ★★★ **④ 할당 바이트** | ★★★ **`HasFlag` 가 판에 따라 48 과 0 을 오간다** — 2×2 판 격자 **두 벌**(짧게·길게 데우기) | (6) |
| ★★ **③ 리플렉션** | 인스턴스 필드 **`value__`** 하나 + 상수 필드 · `BaseType = System.Enum` · 크기 | (2) |
| ★★ **② 진단 격자** | `CS8509`·`CS8524`(switch 식) · **탐침 N 중 답한 것** · `CS0019`·`CS0221`·`CS0266` | (4)(7) |
| ★★ **실행 출력의 이름** | ★★ **제5의 상태** — 라이브러리 교체 뒤 **진단은 원리상 못 본다.** `ToString` 이 찍는 **이름**으로 물었다 | (5) |

- ★★★ **④ 가 이 주제에서 가장 강한 규칙 24 사례다** — `HasFlag` 의 박싱이 **네 판 중 한 판에서만 0** 이었고,\
  **오래 데우면 두 판에서 0** 이 됐다. 「.NET Core 이후 JIT 이 없앴다」는 말은 **절반만 맞다**((6)).

### (1) ★★★ `(Color)99` — 정수가 그대로 들어간다

**언제 쓰나** — 정수(DB 값·직렬화된 값·사용자 입력)를 `enum` 으로 바꿀 때마다.

```text
===== 소스: cs20b-int.cs =====
using System;
enum Color { Red, Green, Blue }
static class Probe {
    public static bool  IsRed(Color c) => c == Color.Red;
    public static Color Make()         => (Color)99;
    public static int   ToInt(Color c) => (int)c;
}
class Program {
    static void Main() {
        Color c = (Color)99;
        Console.WriteLine($"[1] c.ToString()      : {c}");
        Console.WriteLine($"[2] (int)c            : {(int)c}");
        Console.WriteLine($"[3] Enum.IsDefined(c) : {Enum.IsDefined(c)}");
        Console.WriteLine($"[4] default(Color)    : {default(Color)}");
        Il.Dump(typeof(Probe), "IsRed");
        Il.Dump(typeof(Probe), "Make");
        Il.Dump(typeof(Probe), "ToInt");
    }
}
===== csc -r:il.dll -out:ex.dll cs20b-int.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
[1] c.ToString()      : 99
[2] (int)c            : 99
[3] Enum.IsDefined(c) : False
[4] default(Color)    : Red
--- Probe.IsRed ---
  IL_0000: ldarg.0
  IL_0001: ldc.i4.0
  IL_0002: ceq
  IL_0004: ret
--- Probe.Make ---
  IL_0000: ldc.i4.s 99
  IL_0002: ret
--- Probe.ToInt ---
  IL_0000: ldarg.0
  IL_0001: ret
```

- ★★★ **`[1]` `c.ToString()` 이 `99`** — 이름이 없으니 **숫자**를 찍는다. **예외가 없다.**
- ★★★ **`[3]` `Enum.IsDefined(c)` 가 `False`** — **물어야만** 안다. 캐스트는 막지 않는다.
- ★★ **`[4]` `default(Color)` 는 `Red`** — `Red` 가 **0** 이기 때문이다. Learn — 「기본값은 **`(E)0`**, 0 멤버가 **없어도**」.
- ★★★ **IL `Make` 가 `ldc.i4.s 99` 한 줄**이다 — **`(Color)` 캐스트는 명령을 하나도 안 만든다.**\
  **`ToInt` 도 `ldarg.0` 뿐** — `(int)c` 도 명령이 없다. **런타임에는 `Color` 와 `int` 의 구분이 없다.**
- ★★★ **`IsRed` 가 `ldc.i4.0` + `ceq`** — `Color.Red` 는 **정수 상수 0** 으로 박혔다((5)에서 이것이 사고가 된다).

> **어느 층인가** — ★★★ 「**정수 ↔ 열거형 명시적 변환은 늘 허용된다**」는 **언어(334)** 다. 범위 검사가 **없는 것**도 명세다.\
> ★ 그래서 **`(Color)99` 를 막는 것은 언어의 일이 아니라 코드의 일**이다 — `IsDefined` 나 `switch` 의 `_` 로.

### (2) ★★ 리플렉션 — `enum` 은 필드 하나짜리 구조체다

```text
===== 소스: cs20b-refl.cs =====
using System;
using System.Reflection;
using System.Runtime.CompilerServices;
enum Color { Red, Green, Blue }
enum Small : byte { A = 1, B = 200 }
class Program {
    static void Main() {
        foreach (var f in typeof(Color).GetFields(BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance | BindingFlags.Static))
            Console.WriteLine($"필드 {f.Name,-8} static={f.IsStatic,-5} literal={f.IsLiteral,-5} 타입={f.FieldType.Name}");
        Console.WriteLine($"Color 의 BaseType = {typeof(Color).BaseType} · IsValueType = {typeof(Color).IsValueType}");
        Console.WriteLine($"기반 타입 : Color={Enum.GetUnderlyingType(typeof(Color)).Name} · Small={Enum.GetUnderlyingType(typeof(Small)).Name}");
        Console.WriteLine($"크기      : Color={Unsafe.SizeOf<Color>()} · Small={Unsafe.SizeOf<Small>()}");
    }
}
===== csc -out:ex.dll cs20b-refl.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
필드 value__  static=False literal=False 타입=Int32
필드 Red      static=True  literal=True  타입=Color
필드 Green    static=True  literal=True  타입=Color
필드 Blue     static=True  literal=True  타입=Color
Color 의 BaseType = System.Enum · IsValueType = True
기반 타입 : Color=Int32 · Small=Byte
크기      : Color=4 · Small=1
```

- ★★★ **인스턴스 필드는 `value__` 하나**(`Int32`) — `enum` 값의 **실체 전부**다.
- ★★★ **`Red`·`Green`·`Blue` 는 `static`·`literal` 필드** — **상수**다. 메타데이터에 이름과 값이 있을 뿐 **메모리에 객체가 없다.**
- ★★ **`BaseType` 은 `System.Enum`**, **`IsValueType` 은 `True`** — 구조체다.
- ★★ **`Small : byte` 는 크기 1**, `Color` 는 4 — **기반 타입이 크기**다.\
  ★ 기반 타입을 좁히면 **범위 밖 상수가 컴파일 에러**(`CS0221`, (7))가 된다 — [05번](../05-numeric-types-checked-decimal/)의 상수 검사와 같은 자리다.

### (3) ★★★ `[Flags]` 가 바꾸는 것 — `ToString` 과 `Parse` 뿐이다

**언제 쓰나** — 권한·옵션처럼 **여러 개를 동시에** 켜는 값을 만들 때.

```text
===== 소스: cs20b-flags.cs =====
using System;
[Flags] enum Perm  { None = 0, Read = 1, Write = 2, Exec = 4 }
        enum Plain {           Read = 1, Write = 2, Exec = 4 }      // [Flags] 가 없다
class Program {
    static void Main() {
        Console.WriteLine($"[1] Perm.Read | Perm.Exec    : {Perm.Read | Perm.Exec}");
        Console.WriteLine($"[2] Plain.Read | Plain.Exec  : {Plain.Read | Plain.Exec}");
        Console.WriteLine($"[3] (Perm)8                  : {(Perm)8}");
        Console.WriteLine($"[4] (Perm)9                  : {(Perm)9}");
        Console.WriteLine($"[5] (Perm)0                  : {(Perm)0}");
        Console.WriteLine($"[6] Enum.Parse<Perm>(\"Read, Write\")  : {Enum.Parse<Perm>("Read, Write")}");
        Console.WriteLine($"[7] Enum.Parse<Plain>(\"Read, Write\") : {Enum.Parse<Plain>("Read, Write")}");
        Console.WriteLine($"[8] Enum.IsDefined(Perm.Read | Perm.Exec) : {Enum.IsDefined(Perm.Read | Perm.Exec)}");
    }
}
===== csc -out:ex.dll cs20b-flags.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
[1] Perm.Read | Perm.Exec    : Read, Exec
[2] Plain.Read | Plain.Exec  : 5
[3] (Perm)8                  : 8
[4] (Perm)9                  : 9
[5] (Perm)0                  : None
[6] Enum.Parse<Perm>("Read, Write")  : Read, Write
[7] Enum.Parse<Plain>("Read, Write") : 3
[8] Enum.IsDefined(Perm.Read | Perm.Exec) : False
```

- ★★★ **`[1]` `[Flags]` 면 `Read, Exec`**, **`[2]` 없으면 `5`** — 같은 값 5 인데 **특성 하나로 `ToString` 이 갈렸다.**
- ★★★ **`|` 연산은 `[Flags]` 가 없어도 된다**(`[2]` 가 컴파일됐다) — **`[Flags]` 는 연산을 허락하는 것이 아니다.**\
  **`ToString` 이 런타임에 특성을 읽어** 결과를 바꾼다. ★ 두 enum 의 `|` IL 을 나란히 찍지는 않았다.
- ★★ **`[3]` `(Perm)8` 은 `8`**, **`[4]` `(Perm)9` 도 `9`** — 9 = 1 + 8 인데 **8 에 이름이 없으니 전체를 숫자로** 찍는다(`Read, 8` 이 아니다).
- ★★ **`[5]` `(Perm)0` 은 `None`** — 0 에 이름을 붙였기 때문이다.
- ★★★ **`[7]` `Enum.Parse<Plain>("Read, Write")` 가 `3`** — **`[Flags]` 가 없는데도 쉼표 목록을 받아 OR 했다.** `ToString` 은 `3` 이라 **왕복이 비대칭**이다.
- ★★ **`[8]` `Enum.IsDefined(Read | Exec)` 는 `False`** — `IsDefined` 는 **이름 붙은 값 하나**를 찾는다. **조합은 정의된 값이 아니다.**\
  ★ 그래서 **플래그 enum 의 검증에 `IsDefined` 를 쓰면 정상 조합을 거절한다.**

```text
   Perm 값 5  =  0b0101
                   │ │
                   │ └─ Read  (1)
                   └─── Exec  (4)

   [Flags] 있음:  ToString → "Read, Exec"      Parse("Read, Exec") → 5
   [Flags] 없음:  ToString → "5"               Parse("Read, Exec") → 5   ← ★ 받긴 받는다

   ★★★ 비트 연산(|, &) 은 둘 다 컴파일된다 — [Flags] 가 허락하는 것이 아니다.
   ★★★ 바뀌는 것은 BCL 의 문자열 변환 하나다.
```

### (4) ★★ `switch` 식과 `enum` — 모든 이름을 적어도 경고

**언제 쓰나** — `enum` 을 `switch` 로 나눌 때.

```text
===== 소스: cs20b-switch.cs =====
using System;
enum Color { Red, Green, Blue }
class Program {
    static string All(Color c) => c switch {
        Color.Red => "빨강", Color.Green => "초록", Color.Blue => "파랑" };      // 이름 붙은 값을 전부 적었다
    static string Missing(Color c) => c switch {
        Color.Red => "빨강", Color.Green => "초록" };                           // Blue 를 빠뜨렸다
    static void Main() {
        Console.Error.WriteLine($"All(Color.Blue) = {All(Color.Blue)}");
        try { Console.Error.WriteLine($"All((Color)99) = {All((Color)99)}"); }
        catch (Exception e) { Console.Error.WriteLine($"잡힘 : {e.GetType().Name}"); }
    }
}
===== csc -out:ex.dll cs20b-switch.cs 2>&1 | sort && dotnet ex.dll (cc exit=0 · run exit=0) =====
cs20b-switch.cs(4,37): warning CS8524: The switch expression does not handle some values of its input type (it is not exhaustive) involving an unnamed enum value. For example, the pattern '(Color)3' is not covered.
cs20b-switch.cs(6,41): warning CS8509: The switch expression does not handle all possible values of its input type (it is not exhaustive). For example, the pattern 'Color.Blue' is not covered.
All(Color.Blue) = 파랑
잡힘 : SwitchExpressionException
```

- ★★★ **이름 붙은 셋을 다 적은 `All` 에 `CS8524`** — 「**이름 없는 enum 값**이 안 다뤄졌다. 예: `(Color)3`」.\
  ★★ (1)에서 봤듯 **`(Color)3` 은 합법**이므로, 컴파일러는 **이름을 다 적어도 완결로 치지 않는다.**
- ★★★ **`Blue` 를 빠뜨린 `Missing` 에 `CS8509`** — 「**`Color.Blue`** 가 안 다뤄졌다」. **코드가 다르다.**
- ★★★ **둘 다 경고**이고 `cc exit=0` 이다 — **빌드는 된다.**
- ★★★ **실행하면 `All((Color)99)` 가 `SwitchExpressionException`** — 컴파일러가 경고한 바로 그 자리에서 터진다.
- ★ **구분 마커를 표준 오류로** 찍었다(규칙 18).

```text
                   이름을 빠뜨림            이름은 다 적음               _ 까지 적음
   C# switch 식     CS8509 (경고)           CS8524 (경고)                 조용함
                   → (실행 안 함)            → SwitchExpressionException     → _ 가 받는다((형태))
   Kotlin when      ✕ 컴파일 에러(24번 실측)   (안 던졌다)
   Rust match       (안 던졌다)               (안 던졌다)

   ★★★ C# 만 가운데 칸이 「경고」다 — enum 에 이름 없는 값이 들어올 수 있기 때문이다.
```

- ★ **표의 Kotlin·Rust 칸은 이 판에서 던지지 않았다** — Kotlin `when` 의 완결성은 Kotlin 갈래 목록의 **23번**([`23-sealed-classes-and-when-exhaustiveness/`](../../../kotlin/syntax/23-sealed-classes-and-when-exhaustiveness/))·**24번**([`24-enum-class-vs-sealed/`](../../../kotlin/syntax/24-enum-class-vs-sealed/))이 정본이다(24번이 `enum` 주체의 `'when' expression must be exhaustive` 를 실측했다).\
  Rust `match` 칸은 **이 판에서 확인하지 않았다.** ★ Java `switch` 식의 완결성 에러는 [Java 21번](../../../java/syntax/21-switch-statement-and-expression/)이 실측했다.

### (5) ★★★ 라이브러리 enum 의 순서를 바꾸면 — 제5의 상태

**언제 쓰나** — **공개 라이브러리의 `enum` 을 고칠 때.** 17번 주제의 인터페이스 진화와 같은 무대다.

```text
===== 소스: cs20b-lib1.cs =====
public enum Color { Red, Green, Blue }
===== 소스: cs20b-app.cs =====
using System;
class Program {
    static void Main() {
        Color c = Color.Green;
        Console.WriteLine($"Color.Green 을 담은 변수 : {c} · (int) {(int)c}");
    }
}
===== csc -target:library -out:lib.dll cs20b-lib1.cs && csc -r:lib.dll -out:ex.dll cs20b-app.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
Color.Green 을 담은 변수 : Green · (int) 1
===== 소스: cs20b-lib2.cs =====
public enum Color { Red, Yellow, Green, Blue }     // 가운데에 하나 끼워 넣었다
===== csc -target:library -out:lib.dll cs20b-lib2.cs && dotnet ex.dll    # ex.dll 은 다시 컴파일하지 않았다 (cc exit=0 · run exit=0) =====
Color.Green 을 담은 변수 : Yellow · (int) 1
```

- ★★★ **앱을 다시 컴파일하지 않았는데 `Color.Green` 이 `Yellow` 로 읽힌다** — `(int) 1` 은 그대로다.\
  (1)의 IL 처럼 **`Color.Green` 은 앱 안에 정수 `1` 로 박혔고**, 새 라이브러리에서 **1 의 이름이 `Yellow`** 다.
- ★★★ **예외도 경고도 없다.** 값은 **조용히 다른 뜻**이 됐다.
- ★★ **제5의 상태** — 이 사고는 **컴파일러가 원리상 못 본다**(앱을 다시 컴파일하지 않았다). **`ToString` 이 찍은 이름**으로 창을 바꿔 물었다.\
  ★ 바꾼 창이 못 보는 것 — **이름이 없는 값**이었다면(예: 뒤에 추가) `ToString` 은 숫자를 찍었을 것이고, **비교(`== Color.Green`)는 이름을 거치지 않으니 아무것도 안 보인다.**
- ★★ **처방** — 공개 `enum` 에는 **명시적 값**을 적고(`Red = 0, Green = 1, …`), **가운데 끼우지 말고 뒤에 추가**한다. **값을 저장·전송하면** 그 값은 **영원한 계약**이다.\
  ★ [Java 13번](../../../java/syntax/13-enum-classes/)이 같은 사고를 **`ordinal()`** 에서 잡았다 — 「상수 하나가 가운데 끼는 순간 **에러 없이 다른 값으로 읽힌다**」.

### (6) ★★★ `HasFlag` 는 박싱하나 — 판 격자 두 벌

**언제 쓰나** — 「`HasFlag` 는 박싱하니 쓰지 마라 / .NET Core 부터 JIT 이 없앴으니 괜찮다」 두 말을 들었을 때.

먼저 IL 이다.

```text
===== 소스: cs20b-hfil.cs =====
using System;
[Flags] enum Perm { None = 0, Read = 1, Write = 2, Exec = 4 }
static class Probe {
    public static bool H(Perm p) => p.HasFlag(Perm.Exec);
    public static bool B(Perm p) => (p & Perm.Exec) != 0;
}
class Program { static void Main() { Il.Dump(typeof(Probe), "H"); Il.Dump(typeof(Probe), "B"); } }
===== csc -optimize -r:il.dll -out:ex.dll cs20b-hfil.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
--- Probe.H ---
  IL_0000: ldarg.0
  IL_0001: box Perm
  IL_0006: ldc.i4.4
  IL_0007: box Perm
  IL_000c: call System.Enum::HasFlag
  IL_0011: ret
--- Probe.B ---
  IL_0000: ldarg.0
  IL_0001: ldc.i4.4
  IL_0002: and
  IL_0003: ldc.i4.0
  IL_0004: cgt.un
  IL_0006: ret
```

- ★★★ **`H`(`HasFlag`) 는 `box Perm` 이 둘** — `this` 와 인자를 **둘 다 박싱해서** `Enum::HasFlag(Enum)` 를 부른다. **`csc -optimize` 로 컴파일해도** IL 은 이렇다.
- ★★ **`B`(비트 연산) 는 `and` + `cgt.un`** — 박싱이 없다.
- ★★★ **IL 에는 박싱이 있다.** 그것을 **없애느냐는 JIT 의 일**이다. 그래서 **판을 바꿔 재야** 한다(규칙 24).

```text
===== 소스: cs20b-alloc.cs =====
using System;
[Flags] enum Perm { None = 0, Read = 1, Write = 2, Exec = 4 }
class Program {
    static long M(Action a) {
        a();                                             // 한 판 데워 놓고
        var b = GC.GetAllocatedBytesForCurrentThread();
        a();
        return GC.GetAllocatedBytesForCurrentThread() - b;
    }
    static void Main() {
        int sink = 0;
        Perm p = Perm.Read | Perm.Exec;
        Enum boxed = p;
        Console.WriteLine($"p.HasFlag(Perm.Exec)         1000회 : {M(() => { for (int i = 0; i < 1000; i++) sink += p.HasFlag(Perm.Exec) ? 1 : 0; })} 바이트");
        Console.WriteLine($"(p & Perm.Exec) != 0         1000회 : {M(() => { for (int i = 0; i < 1000; i++) sink += (p & Perm.Exec) != 0 ? 1 : 0; })} 바이트");
        Console.WriteLine($"boxed.HasFlag(Perm.Exec)     1000회 : {M(() => { for (int i = 0; i < 1000; i++) sink += boxed.HasFlag(Perm.Exec) ? 1 : 0; })} 바이트");
        Console.WriteLine($"p.ToString()                 1000회 : {M(() => { for (int i = 0; i < 1000; i++) sink += p.ToString().Length; })} 바이트");
        Console.WriteLine($"(합 {sink})");
    }
}
===== csc -out:ex.dll cs20b-alloc.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
p.HasFlag(Perm.Exec)         1000회 : 48000 바이트
(p & Perm.Exec) != 0         1000회 : 0 바이트
boxed.HasFlag(Perm.Exec)     1000회 : 24000 바이트
p.ToString()                 1000회 : 72000 바이트
(합 26000)
===== csc -out:ex.dll cs20b-alloc.cs && DOTNET_TieredCompilation=0 dotnet ex.dll (cc exit=0 · run exit=0) =====
p.HasFlag(Perm.Exec)         1000회 : 48000 바이트
(p & Perm.Exec) != 0         1000회 : 0 바이트
boxed.HasFlag(Perm.Exec)     1000회 : 24000 바이트
p.ToString()                 1000회 : 72000 바이트
(합 26000)
===== csc -optimize -out:exo.dll cs20b-alloc.cs && dotnet exo.dll (cc exit=0 · run exit=0) =====
p.HasFlag(Perm.Exec)         1000회 : 48000 바이트
(p & Perm.Exec) != 0         1000회 : 0 바이트
boxed.HasFlag(Perm.Exec)     1000회 : 24000 바이트
p.ToString()                 1000회 : 72000 바이트
(합 26000)
===== csc -optimize -out:exo.dll cs20b-alloc.cs && DOTNET_TieredCompilation=0 dotnet exo.dll (cc exit=0 · run exit=0) =====
p.HasFlag(Perm.Exec)         1000회 : 0 바이트
(p & Perm.Exec) != 0         1000회 : 0 바이트
boxed.HasFlag(Perm.Exec)     1000회 : 24000 바이트
p.ToString()                 1000회 : 72000 바이트
(합 26000)
===== 네 판 대조 — 「바이트」 줄마다 네 판의 값이 같은가 =====
네 판에서 갈린 줄 1 / 4
```

- ★★★ **`p.HasFlag` 가 세 판에서 48000, 한 판에서 0** — **`csc -optimize` × `TieredCompilation=0`** 에서만 0 이다.\
  **네 판에서 갈린 줄 1 / 4.** ★★★ **한 판만 쟀으면 둘 중 어느 결론이든 적을 수 있었다.**
- ★★ **`boxed.HasFlag` 는 네 판 모두 24000** — 이미 박싱된 `Enum` 에 부르니 **인자 하나만** 박싱한다.
- ★ **`p.ToString()` 72000** — 문자열을 만드니 당연히 할당한다(대조). **비트 연산은 0.**

그런데 **왜 그 한 판만** 0 인가. 두 가지를 더 물었다.

```text
===== 소스: cs20b-dbg.cs =====
using System;
using System.Diagnostics;
using System.Reflection;
class Program {
    static void Main() {
        var d = Assembly.GetExecutingAssembly().GetCustomAttribute<DebuggableAttribute>();
        Console.WriteLine(d is null ? "DebuggableAttribute 없음"
                                    : $"IsJITOptimizerDisabled={d.IsJITOptimizerDisabled} · IsJITTrackingEnabled={d.IsJITTrackingEnabled}");
    }
}
===== csc -out:ex.dll cs20b-dbg.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
IsJITOptimizerDisabled=True · IsJITTrackingEnabled=True
===== csc -optimize -out:ex.dll cs20b-dbg.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
IsJITOptimizerDisabled=False · IsJITTrackingEnabled=False
```

- ★★★ **`csc` 기본(최적화 없음)으로 만든 어셈블리는 `IsJITOptimizerDisabled=True`** — ★★★ **JIT 최적화가 꺼진다.**\
  **그래서 `csc` 기본 두 판은 티어링과 무관하게 48000** 이다. `HasFlag` 의 박싱을 없애는 것이 **JIT 최적화**이기 때문이다.
- ★★ **`csc -optimize` 는 `False`** — 최적화가 켜진다. 그런데도 **티어링 기본 판이 48000** 이었다 —\
  **짧게 데운 측정(`a()` 한 번)은 아직 티어 0(최적화 안 된 첫 JIT) 코드를 재고 있었기 때문**으로 읽힌다. **길게 데워** 확인했다.

```text
===== 소스: cs20b-allocw.cs =====
using System;
[Flags] enum Perm { None = 0, Read = 1, Write = 2, Exec = 4 }
class Program {
    static long M(Action a) {
        for (int w = 0; w < 200; w++) a();               // 오래 데운다 — 티어 1 로 올라갈 시간을 준다
        System.Threading.Thread.Sleep(500);
        for (int w = 0; w < 200; w++) a();
        var b = GC.GetAllocatedBytesForCurrentThread();
        a();
        return GC.GetAllocatedBytesForCurrentThread() - b;
    }
    static void Main() {
        int sink = 0;
        Perm p = Perm.Read | Perm.Exec;
        Enum boxed = p;
        Console.WriteLine($"p.HasFlag(Perm.Exec)         1000회 : {M(() => { for (int i = 0; i < 1000; i++) sink += p.HasFlag(Perm.Exec) ? 1 : 0; })} 바이트");
        Console.WriteLine($"(p & Perm.Exec) != 0         1000회 : {M(() => { for (int i = 0; i < 1000; i++) sink += (p & Perm.Exec) != 0 ? 1 : 0; })} 바이트");
        Console.WriteLine($"boxed.HasFlag(Perm.Exec)     1000회 : {M(() => { for (int i = 0; i < 1000; i++) sink += boxed.HasFlag(Perm.Exec) ? 1 : 0; })} 바이트");
        Console.WriteLine($"p.ToString()                 1000회 : {M(() => { for (int i = 0; i < 1000; i++) sink += p.ToString().Length; })} 바이트");
        Console.WriteLine($"(합 {sink})");
    }
}
===== csc -out:ex.dll cs20b-allocw.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
p.HasFlag(Perm.Exec)         1000회 : 48000 바이트
(p & Perm.Exec) != 0         1000회 : 0 바이트
boxed.HasFlag(Perm.Exec)     1000회 : 24000 바이트
p.ToString()                 1000회 : 72000 바이트
(합 5213000)
===== csc -out:ex.dll cs20b-allocw.cs && DOTNET_TieredCompilation=0 dotnet ex.dll (cc exit=0 · run exit=0) =====
p.HasFlag(Perm.Exec)         1000회 : 48000 바이트
(p & Perm.Exec) != 0         1000회 : 0 바이트
boxed.HasFlag(Perm.Exec)     1000회 : 24000 바이트
p.ToString()                 1000회 : 72000 바이트
(합 5213000)
===== csc -optimize -out:exo.dll cs20b-allocw.cs && dotnet exo.dll (cc exit=0 · run exit=0) =====
p.HasFlag(Perm.Exec)         1000회 : 0 바이트
(p & Perm.Exec) != 0         1000회 : 0 바이트
boxed.HasFlag(Perm.Exec)     1000회 : 24000 바이트
p.ToString()                 1000회 : 72000 바이트
(합 5213000)
===== csc -optimize -out:exo.dll cs20b-allocw.cs && DOTNET_TieredCompilation=0 dotnet exo.dll (cc exit=0 · run exit=0) =====
p.HasFlag(Perm.Exec)         1000회 : 0 바이트
(p & Perm.Exec) != 0         1000회 : 0 바이트
boxed.HasFlag(Perm.Exec)     1000회 : 24000 바이트
p.ToString()                 1000회 : 72000 바이트
(합 5213000)
===== 네 판 대조 — 「바이트」 줄마다 네 판의 값이 같은가 =====
네 판에서 갈린 줄 1 / 4
```

- ★★★ **200회 + 0.5초 + 200회 데운 뒤 재자 `csc -optimize` 두 판이 다 0** — 티어 1(최적화 JIT)로 올라간 코드가 **박싱을 없앴다.**\
  **`csc` 기본 두 판은 여전히 48000** — 최적화가 **꺼진 어셈블리**라 오래 데워도 안 된다.
- ★★★ **결론 — 「`HasFlag` 박싱을 JIT 이 없앤다」는 「최적화된 어셈블리 + 최적화 JIT 코드」에서만 참이다.**\
  **디버그 빌드에서는 늘 박싱하고**, 릴리스 빌드도 **첫 JIT(티어 0) 동안은** 박싱한다.

| 판 | 짧게 데움 | 길게 데움 | 왜 |
|---|---|---|---|
| `csc` 기본 · 티어링 기본 | 48000 | 48000 | ★★★ **어셈블리가 JIT 최적화를 끈다**(`IsJITOptimizerDisabled=True`) |
| `csc` 기본 · `TieredCompilation=0` | 48000 | 48000 | 〃 |
| `csc -optimize` · 티어링 기본 | ★ **48000** | ★★★ **0** | 짧게는 **티어 0** 코드 · 길게는 **티어 1** 코드 |
| `csc -optimize` · `TieredCompilation=0` | ★★★ **0** | **0** | 처음부터 **최적화 JIT** |

- ★★★ **움직인 칸이 둘**이다 — [11번](../11-collection-initializers-and-collection-expressions/)의 규칙 24 사례(「상수 쪽이 비싸다」가 tier-0 잡음)와 **같은 원인**이 이번에는 **반대 방향**(「박싱 없다」가 판에 따라 참)으로 나왔다.
- ★★ **「어느 판이 진짜인가」가 아니다** — 셋 다 진짜다. **어느 조건에서 무엇이 되나**가 결론이다.
- ★★★ **시간은 안 쟀다.** 「`HasFlag` 가 느리다」는 문장이 이 문서에 없다.
- ★ **「티어 0 코드를 재고 있었다」는 해석**이다 — 티어링 상태를 **직접 찍지 않았고**, **데우는 양을 바꿨을 때 칸이 움직인 것**만 실측이다.\
  ★ 「0.5초」는 티어링이 **시간에 기대어** 올라가기 때문에 넣었다 — 그래서 이 칸은 **머리말에서** 「**흔들리는 칸**」으로 선언했다.

### (7) ★★ 컴파일러가 무엇을 안 보나 — 탐침 열

```text
===== 소스: cs20b-probe.cs =====
using System;

// 탐침 1 — [Flags] 인데 값이 2의 거듭제곱이 아니고 겹친다
[Flags] enum F1 { Read = 1, Write = 2, Both = 3, Exec = 3 }

// 탐침 2 — [Flags] 인데 0 에 이름이 없다
[Flags] enum F2 { Read = 1, Write = 2 }

// 탐침 3 — 0 에 해당하는 멤버가 없는 enum
enum E3 { A = 1, B = 2 }

// 탐침 4 — 두 이름이 같은 값을 가진다
enum E4 { A = 1, B = 1 }

enum Color { Red, Green, Blue }

class Program {
    static void Main() {
        Color c = Color.Red;
        Console.WriteLine($"탐침 5 : c == 0 → {c == 0}");                                        // 리터럴 0 과 비교
        switch (c) { case Color.Red: Console.WriteLine("탐침 6 : switch 문"); break; }          // 일부만 다룬 switch 문
        Console.WriteLine($"탐침 7 : {c switch { Color.Red => 1, Color.Green => 2 }}");           // Blue 가 빠진 switch 식
        Console.WriteLine($"탐침 8 : {c switch { Color.Red => 1, Color.Green => 2, Color.Blue => 3 }}");
        Console.WriteLine($"탐침 9 : E3.A | E3.B → {E3.A | E3.B}");                             // [Flags] 없는 enum 에 |
        Console.WriteLine($"탐침 10 : default(E3) → {default(E3)} · IsDefined → {Enum.IsDefined(default(E3))}");
        Console.WriteLine($"탐침 4 : E4.B → {E4.B} · E4.A == E4.B → {E4.A == E4.B}");
    }
}
===== csc -warn:9 -out:ex.dll cs20b-probe.cs 2>&1 | sort && dotnet ex.dll (cc exit=0 · run exit=0) =====
cs20b-probe.cs(22,39): warning CS8509: The switch expression does not handle all possible values of its input type (it is not exhaustive). For example, the pattern 'Color.Blue' is not covered.
cs20b-probe.cs(23,39): warning CS8524: The switch expression does not handle some values of its input type (it is not exhaustive) involving an unnamed enum value. For example, the pattern '(Color)3' is not covered.
탐침 5 : c == 0 → True
탐침 6 : switch 문
탐침 7 : 1
탐침 8 : 1
탐침 9 : E3.A | E3.B → 3
탐침 10 : default(E3) → 0 · IsDefined → False
탐침 4 : E4.B → A · E4.A == E4.B → True
===== csc -warn:9 -out:ex.dll cs20b-probe.cs 2>&1 | grep -o "cs20b-probe.cs([0-9]*" | sort -u | wc -l    # 탐침 10개 중 진단이 붙은 줄은 몇 개인가 (exit=0) =====
2
```

- ★★★ **탐침 열 중 진단이 붙은 줄은 둘**이다(`CS8509`·`CS8524` — 둘 다 `switch` 식).

| 탐침 | 무엇을 심었나 | 답했나 | 실행하면 |
|---|---|---|---|
| 1 | `[Flags]` 인데 값이 겹치고 2의 거듭제곱이 아님 | ★★ **침묵** | — |
| 2 | `[Flags]` 인데 0 에 이름 없음 | **침묵** | — |
| 3 | 0 멤버가 없는 enum | ★★ **침묵** | 탐침 10 — `default(E3)` 가 **`0`**, `IsDefined` **`False`** |
| 4 | 두 이름이 같은 값 | ★★ **침묵** | ★★★ **`E4.B` 가 `A` 로 찍힌다** |
| 5 | ★★ **리터럴 `0` 과 비교** | ★★★ **침묵** — 컴파일된다 | `True` |
| 6 | 일부만 다룬 `switch` **문** | ★★★ **침묵** | — |
| 7 | `Blue` 가 빠진 `switch` 식 | **답함** — `CS8509` | `1` |
| 8 | 이름을 다 적은 `switch` 식 | **답함** — `CS8524` | `1` |
| 9 | `[Flags]` 없는 enum 에 `\|` | **침묵** | **`3`** — 숫자로 찍힌다 |
| 10 | `default` 가 이름 없는 값 | **침묵** | `0` |

- ★★★ **탐침 4 — `E4.B` 가 `A`** 로 찍힌다. 값이 같으면 **런타임은 어느 이름인지 모른다** — `ToString` 이 **하나를 골라** 찍는다.\
  ★ 어느 이름을 고르는지는 **BCL 구현**이다. 로그가 **내가 쓴 이름과 다른 이름**을 보여 준다.
- ★★★ **탐침 5 — `c == 0` 은 되고 `c == 1` 은 `CS0019`**(아래). Learn — 「**리터럴 `0` 은 어느 열거형으로든 암시적 변환된다**」.
- ★★★ **탐침 6 — `switch` 문은 완결성을 전혀 안 본다.** 경고는 **`switch` 식에만** 있다.
- ★ **탐침 1·2** — `[Flags]` 의 **설계 규칙**(2의 거듭제곱 · `None = 0`)은 컴파일러가 **안 본다.** 분석기(CA 규칙)의 몫이다 — **이 판에서 분석기는 안 켰다.**

```text
===== 소스: cs20b-err.cs =====
enum Color { Red, Green, Blue }
enum Small : byte { A = 1 }
class Program {
    static void Main() {
        Color c = Color.Red;
        _ = c == 1;                 // 리터럴 1 과 비교
        _ = (Small)300;             // 기반 타입 범위 밖의 상수
        Color d = 2;                // 정수를 그대로 대입
        int n = Color.Blue;         // enum 을 그대로 int 에
        _ = (d, n);
    }
}
===== csc -out:ex.dll cs20b-err.cs 2>&1 | sort (cc exit=1) =====
cs20b-err.cs(6,13): error CS0019: Operator '==' cannot be applied to operands of type 'Color' and 'int'
cs20b-err.cs(7,13): error CS0221: Constant value '300' cannot be converted to a 'Small' (use 'unchecked' syntax to override)
cs20b-err.cs(8,19): error CS0266: Cannot implicitly convert type 'int' to 'Color'. An explicit conversion exists (are you missing a cast?)
cs20b-err.cs(9,17): error CS0266: Cannot implicitly convert type 'Color' to 'int'. An explicit conversion exists (are you missing a cast?)
```

- ★★★ **`c == 1` 은 `CS0019`** — 0 이 아닌 정수 리터럴은 **비교조차 안 된다.** 탐침 5 의 `0` 과 **짝**이다.
- ★★★ **`(Small)300` 은 `CS0221`** — **상수**가 기반 타입(`byte`) 범위를 넘으면 **컴파일 에러**다. ★ 변수였다면 런타임에 **조용히 잘린다**([05번](../05-numeric-types-checked-decimal/)의 `unchecked` — **이 판에서 enum 으로는 안 던졌다**).
- ★★ **`Color d = 2` · `int n = Color.Blue` 는 `CS0266`** — 정수 ↔ enum 은 **명시적 캐스트**만 된다(0 만 예외).

### (8) ★★ Java·Kotlin·Rust 와 대비

```text
===== 소스: j20/Ex20.java =====
enum Color { RED, GREEN, BLUE }
public class Ex20 {
    public static void main(String[] a) {
        Color c = (Color) 99;                  // C# 처럼 정수를 캐스트해 본다
        System.out.println(c);
    }
}
===== javac -d j20out j20/Ex20.java (cc exit=1) =====
j20/Ex20.java:4: error: incompatible types: int cannot be converted to Color
        Color c = (Color) 99;                  // C# 처럼 정수를 캐스트해 본다
                          ^
1 error
===== 소스: j20/Ex20b.java =====
enum Color { RED, GREEN, BLUE }
public class Ex20b {
    public static void main(String[] a) {
        System.out.println(Color.class.getSuperclass() + " · GREEN.ordinal()=" + Color.GREEN.ordinal());
        try { System.out.println(Color.values()[99]); }
        catch (Exception e) { System.out.println("잡힘 : " + e.getClass().getSimpleName()); }
    }
}
===== javac -d j20out j20/Ex20b.java && java -cp j20out Ex20b (cc exit=0 · run exit=0) =====
class java.lang.Enum · GREEN.ordinal()=1
잡힘 : ArrayIndexOutOfBoundsException
```

- ★★★ **javac — `(Color) 99` 가 `incompatible types: int cannot be converted to Color`.** Java `enum` 은 **클래스**라 정수가 들어갈 자리가 없다.
- ★★ **`Color` 의 부모는 `java.lang.Enum`** · `GREEN.ordinal()` 은 `1` · `values()[99]` 는 **`ArrayIndexOutOfBoundsException`** — **정수에서 enum 으로 가는 길이 배열 인덱스뿐**이고, 그것은 **범위를 검사한다.**
- ★ Java 의 `enum` 이 싱글턴 객체·상수별 본문·`EnumSet` 을 갖는 것은 [Java 13번](../../../java/syntax/13-enum-classes/)이 정본이다.

```text
                 C# enum                Java enum                  Kotlin enum class           Rust enum
   런타임 실체    ★ 정수(value__)         객체(싱글턴)                  객체(싱글턴)                  판별값 + (변형마다) 데이터
   정수 → enum   ★ (E)99 된다 — 에러 없음  ✕ incompatible types(실측)    (안 던졌다)                   (안 던졌다)
   enum → 정수   (int)c — 명령 0개         ordinal()                    ordinal                      as i32 — C 스타일만
   완결성 검사    ★ 경고(CS8509/8524)      switch 식 에러                when 에러                     (그 갈래 참조)
   변형마다 데이터 ✕                       필드(모두 같은 모양)            필드(모두 같은 모양)            ★ 변형마다 다른 모양

   ★★★ C# 만 「이름 없는 값」 이 합법이다 — 그래서 완결성이 경고로 내려앉았다.
```

- ★ **이 판이 던진 것은 C# 열과 Java 의 「정수 → enum」 칸뿐**이다. 나머지는 각 갈래 문서에서 읽었다 —\
  Java `switch` 식의 완결성 에러(`does not cover all possible input values`)는 [Java 21번](../../../java/syntax/21-switch-statement-and-expression/),\
  Kotlin `when` 의 완결성 에러(`'when' expression must be exhaustive`)는 [Kotlin 24번](../../../kotlin/syntax/24-enum-class-vs-sealed/),\
  Rust 의 **`as i32` 는 C 스타일 열거형에서만 되고 데이터를 담으면 `E0605`** 인 것은 [Rust 17번](../../../rust/syntax/17-enums-and-data-carrying-variants/)이 실측했다.
- ★ **Kotlin 에서 값 하나를 감싸는 것**은 `enum` 이 아니라 **`value class`**([Kotlin 26번](../../../kotlin/syntax/26-value-class-and-boxing/))다 — **타입 안전을 지키면서** 박싱을 줄이는 설계다.\
  C# `enum` 은 **타입 안전 일부(범위)를 내주고** 정수 그대로의 비용을 얻었다.

## 문법 — 형태와 규칙

### 형태

```csharp
// cs20b-form.cs
using System;

var p = Perm.Read | Perm.Write;
Console.WriteLine($"{p} · {(int)p} · {(p & Perm.Write) != 0} · {Enum.IsDefined(Level.Warn)} · {(byte)Level.Error}");
Console.WriteLine(Describe(Level.Warn));

static string Describe(Level l) => l switch {
    Level.Info  => "정보",
    Level.Warn  => "경고",
    Level.Error => "오류",
    _ => throw new ArgumentOutOfRangeException(nameof(l), l, null)       // 이름 없는 값까지 막는다
};

[Flags] enum Perm { None = 0, Read = 1 << 0, Write = 1 << 1, Exec = 1 << 2 }   // 0 에 이름 · 2의 거듭제곱
enum Level : byte { Info = 1, Warn = 2, Error = 3 }                              // 기반 타입 · 명시적 값
```

```text
===== 소스: cs20b-form.cs =====
using System;

var p = Perm.Read | Perm.Write;
Console.WriteLine($"{p} · {(int)p} · {(p & Perm.Write) != 0} · {Enum.IsDefined(Level.Warn)} · {(byte)Level.Error}");
Console.WriteLine(Describe(Level.Warn));

static string Describe(Level l) => l switch {
    Level.Info  => "정보",
    Level.Warn  => "경고",
    Level.Error => "오류",
    _ => throw new ArgumentOutOfRangeException(nameof(l), l, null)       // 이름 없는 값까지 막는다
};

[Flags] enum Perm { None = 0, Read = 1 << 0, Write = 1 << 1, Exec = 1 << 2 }   // 0 에 이름 · 2의 거듭제곱
enum Level : byte { Info = 1, Warn = 2, Error = 3 }                              // 기반 타입 · 명시적 값
===== csc -out:ex.dll cs20b-form.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
Read, Write · 3 · True · True · 3
경고
```

- ★★★ **`[Flags]` enum 은 `None = 0` + 2의 거듭제곱**(`1 << n`) — `ToString` 이 조합을 이름으로 읽는다((3)).
- ★★ **검사는 `(p & Perm.Write) != 0`** — 박싱 없는 비트 연산이다((6)). `HasFlag` 는 **최적화 빌드의 데워진 코드에서만** 박싱이 사라진다.
- ★★ **기반 타입(`: byte`)과 명시적 값** — 크기를 정하고, **값이 계약**임을 드러낸다((2)(5)).
- ★★★ **`switch` 식 끝의 `_ => throw`** — **이름 없는 값까지 막는다.** `CS8524` 가 사라진다((4)).
- **`enum` 안에 메서드를 못 둔다**(Learn) — 기능은 확장 멤버로 붙인다.

### 금지 사례 — 진단이 나는 꼴

| 쓴 꼴 | 진단 코드 | 어디서 |
|---|---|---|
| enum 과 **0 이 아닌** 정수 리터럴을 `==` | `CS0019`(에러) | (7) |
| 기반 타입 범위 밖의 **상수**를 캐스트 | `CS0221`(에러) | (7) |
| 정수 ↔ enum 을 **캐스트 없이** 대입 | `CS0266`(에러) | (7) |
| `switch` 식에서 이름 하나를 빠뜨림 | `CS8509`(**경고**) | (4)(7) |
| `switch` 식에서 이름은 다 적고 `_` 없음 | `CS8524`(**경고**) | (4)(7) |
| ★★★ **`(Color)99`** | ★★★ **진단 없음** — 합법이다 | (1) |
| ★★★ enum 과 리터럴 **`0`** 을 `==` | ★★★ **진단 없음** | (7) 탐침 5 |
| ★★★ 일부만 다룬 `switch` **문** | ★★★ **진단 없음** | (7) 탐침 6 |

## 어디서 틀리나

1. ★★★ **「`enum` 변수에는 정의된 값만 들어간다」** — **`(Color)99` 가 에러 없이 들어간다**((1)). IL 에 캐스트가 없다.
2. ★★★ **「`[Flags]` 를 붙여야 `|` 를 쓸 수 있다」** — **`|` 는 늘 된다.** `[Flags]` 는 **`ToString` 을 바꿀 뿐**이다((3)).
3. ★★★ **「`switch` 식에 이름을 다 적었으니 완결이다」** — **`CS8524`** · 실행하면 **`SwitchExpressionException`**((4)). `_` 가 필요하다.
4. ★★★ **「라이브러리 enum 에 멤버를 끼워 넣어도 괜찮다」** — **다시 컴파일 안 한 앱의 값이 다른 이름**이 된다((5)).
5. ★★★ **「`HasFlag` 는 박싱한다 / 안 한다」** — **판에 달렸다**((6)). 디버그 빌드는 늘 박싱, 릴리스는 데워진 뒤에만 0.
6. ★★ **「`IsDefined` 로 플래그 값을 검증한다」** — **조합은 `False`** 다((3) `[8]`).
7. ★★ **「`[Flags]` 가 없으면 `Parse` 가 쉼표를 거절한다」** — **받아서 OR 한다**((3) `[7]`).
8. ★★ **「`ToString` 은 내가 쓴 이름을 찍는다」** — **값이 같은 이름이 둘이면 하나를 골라** 찍는다((7) 탐침 4).
9. ★ **「enum 과 정수는 비교가 안 된다」** — **리터럴 `0` 은 된다**((7) 탐침 5). `1` 은 `CS0019`.
10. ★ **「`switch` 문도 완결성을 검사한다」** — **식만** 한다((7) 탐침 6).

## 구현 세부사항 대 언어 보장

| 무엇 | 층 | 근거 |
|---|---|---|
| **정수 ↔ enum 명시적 변환이 늘 된다 · 범위 검사 없음** | ★★★ **언어 보장(334)** | (1) IL `ldc.i4.s 99` |
| **리터럴 `0` 의 암시적 변환** | ★★★ **언어 보장(334)** · Learn | (7) 탐침 5 |
| **기본값이 `(E)0`** | ★★★ **언어 보장(334)** · Learn | (1) `[4]` · (7) 탐침 10 |
| **enum 멤버가 컴파일 시점 상수로 박힌다** | ★★★ **언어 보장(334)** | (1) IL · (5) |
| **상수 범위 밖 캐스트가 에러** | ★★★ **언어 보장(334)** | (7) `CS0221` |
| **`CS8509`·`CS8524` 가 경고인 것** | ★★ **컴파일러(Roslyn)** | (4) |
| **`[Flags]` 가 `ToString`·`Parse` 를 바꾸는 것** | ★★ **BCL** | (3) |
| **값이 같은 두 이름 중 `ToString` 이 고르는 것** | ★ **BCL 구현** | (7) 탐침 4 |
| **`HasFlag` 박싱을 JIT 이 없애는 것** | ★ **JIT 구현** — 판에 달렸다 | (6) |
| **`csc` 기본 빌드가 JIT 최적화를 끄는 것** | ★★ **컴파일러·런타임 관례**(`DebuggableAttribute`) | (6) |
| **인스턴스 필드 이름 `value__`** | ★★ **CLI 관례** | (2) |

## 언제 쓰고 언제 안 쓰나

- ★★★ **닫힌 선택지에 `enum` 을 쓰되, 바깥에서 들어오는 정수는 `IsDefined`(단일 값) 또는 `switch` 의 `_` 로 막아라**((1)(4)).
- ★★★ **공개 `enum` 에는 명시적 값을 적고, 뒤에만 추가하라** — 저장·전송된 값은 영원한 계약이다((5)).
- ★★ **여러 개를 동시에 켜는 값은 `[Flags]` + `None = 0` + 2의 거듭제곱**((3)). **검증은 「알려진 비트 외에 켜진 것이 없나」**(`(v & ~All) == 0`)로 — `IsDefined` 는 조합을 거절한다.
- ★★ **뜨거운 경로의 플래그 검사는 비트 연산**으로 — `HasFlag` 의 0 은 **조건부**다((6)).
- ★★ **상태마다 다른 데이터가 붙으면 `enum` 이 아니다** — record 계층·패턴 매칭(목록의 **21번 주제**)으로 간다. Rust 의 데이터 싣는 변형이 그 모양이다.
- ★ **값이 같은 두 이름을 두지 마라** — 로그가 다른 이름을 찍는다((7) 탐침 4). 별칭이 필요하면 **`[Obsolete]`** 를 붙여 하나로 몰아라(**이 판에서 안 던졌다**).

## 핵심 문장

1. ★★★ **`enum` 은 IL 에서 정수다** — `(Color)99` 는 `ldc.i4.s 99` 한 줄이고 **에러 없이 `99`** 를 찍는다((1)).
2. ★★★ **`[Flags]` 는 `ToString`·`Parse` 만 바꾼다** — `|` 는 `[Flags]` 없이도 되고, `[Flags]` 규칙 위반에 진단이 없다((3)(7)).
3. ★★★ **`switch` 식은 이름을 다 적어도 `CS8524`** 이다 — 이름 없는 값이 들어올 수 있기 때문이다((4)).
4. ★★★ **라이브러리 enum 의 순서를 바꾸면 다시 컴파일 안 한 앱의 값이 다른 이름이 된다** — 멤버가 상수로 박히기 때문이다((5)).
5. ★★★ **`HasFlag` 의 박싱은 판에 달렸다** — 네 판 중 한 판(길게 데우면 두 판)에서만 0 이다. **디버그 빌드는 JIT 최적화가 꺼진다**((6)).

## 관련 자료

- [05번 — 숫자 타입·`checked`](../05-numeric-types-checked-decimal/) — ★★ **`enum` 이 올라탄 정수**의 정본. **경계**: 오버플로·`checked` 는 거기, 여기는 **그 정수에 붙은 이름표**다.
- [03번 — 박싱](../03-boxing-and-unboxing/) — `HasFlag` 의 `box Perm` 둘이 그것이다.
- 목록의 **17번 주제**(인터페이스 진화) — (5)와 **같은 무대**(두 어셈블리 · 다시 컴파일 안 한 앱).
- 목록의 **21번 주제**(패턴 매칭)·**22번 주제**(`switch` 식과 `switch` 문) — **완결성 검사 전반**의 정본. 여기서는 **enum 에서 새는 자리**만 봤다.
- Java 갈래 목록([`java/syntax/README.md`](../../../java/syntax/README.md))의 **13번**([`13-enum-classes/`](../../../java/syntax/13-enum-classes/)) — **경계**: Java `enum` 의 **싱글턴·상수별 본문·`EnumSet`·`ordinal` 사고**는 거기가 정본이다.
- Kotlin 갈래 목록([`kotlin/syntax/README.md`](../../../kotlin/syntax/README.md))의 **24번**([`24-enum-class-vs-sealed/`](../../../kotlin/syntax/24-enum-class-vs-sealed/))·**26번**([`26-value-class-and-boxing/`](../../../kotlin/syntax/26-value-class-and-boxing/)) — `enum class` 대 `sealed` · **값 하나를 감싼 껍데기의 다른 설계**.
- Rust 갈래 목록([`rust/syntax/README.md`](../../../rust/syntax/README.md))의 **17번**([`17-enums-and-data-carrying-variants/`](../../../rust/syntax/17-enums-and-data-carrying-variants/)) — **데이터를 싣는 변형.**

## 용어 풀이

- **열거형(enum)** — 기반 정수 타입의 **이름 붙은 상수** 묶음. 런타임 실체는 **정수 하나**(`value__`)다.
- **기반 타입(underlying type)** — `enum E : byte` 의 `byte`. 기본은 `int`. 크기와 범위를 정한다.
- **`[Flags]`** — 「이 enum 은 비트 조합이다」라는 **특성**. BCL 의 `ToString`·`Parse` 가 읽는다. **컴파일러는 그 규칙 위반에 진단을 안 냈다.**
- **`Enum.IsDefined`** — 값이 **이름 붙은 멤버 하나**와 같은가. 조합은 `False`.
- **`SwitchExpressionException`** — `switch` 식에서 어느 갈래도 안 맞았을 때 런타임이 던지는 예외.
- **티어드 컴파일(tiered compilation)** — JIT 이 먼저 **빠르게 대충**(티어 0) 번역하고, 자주 불리면 **최적화해서 다시**(티어 1) 번역하는 방식. `DOTNET_TieredCompilation=0` 이면 처음부터 최적화한다.
- **`DebuggableAttribute`·`IsJITOptimizerDisabled`** — 어셈블리에 박히는 표식. `True` 면 **JIT 이 최적화를 안 한다.** `csc` 기본 빌드가 `True` 였다.

## 더 들어가면

- ★ **`Enum.GetValues`·`GetNames` 의 할당** · **제네릭 `Enum` 제약(`where T : struct, Enum`)** — **이 판에서 안 던졌다.**
- ★ **`HasFlag` 의 티어링 상태를 직접 보기** — `DOTNET_JitStdOutFile`·ETW 로 티어 전환을 찍을 수 있다고 알려져 있으나 **이 판에서 안 썼다.** (6)의 「티어 0 을 재고 있었다」는 **데우는 양을 바꿔 본 간접 증거**다.
- ★ **이 발견이 앞 주제들의 2×2 격자에 주는 뜻** — `csc` 기본 두 칸은 **「최적화가 꺼진 JIT」** 이었다. 그 칸들이 안 움직였다면 **최적화가 결과에 상관없는 계수**였다는 뜻이고, 움직였다면 **JIT 최적화가 그 차이**다.
