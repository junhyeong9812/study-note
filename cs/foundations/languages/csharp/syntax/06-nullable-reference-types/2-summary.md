# csharp/syntax/06 — 널 허용 참조 타입(C# 8) — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [ECMA-334 7판(2023-12)](https://ecma-international.org/publications-and-standards/standards/ecma-334/) · [Microsoft Learn — C# 언어 레퍼런스](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/) · [Learn — `checked`/`unchecked`](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/statements/checked-and-unchecked) · [Learn — 널 허용 값 형식](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/builtin-types/nullable-value-types) · [Learn — 널 허용 참조 형식](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/builtin-types/nullable-reference-types) · [Learn — 멤버 접근·널 조건 연산자](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/operators/member-access-operators)
> **실행 검증** — 이 문서의 모든 출력·진단·IL·할당 바이트는 **.NET SDK 10.0.401** ·\
> 런타임 **`.NET 10.0.12`**(`Microsoft.NETCore.App`) · 타겟 **`net10.0`** · **linux-x64** 에서 실제로 돌려 얻은 것이다(2026-09-25).\
> ★ 블록은 캡처 스크립트가 파일로 받아 조립기가 끼워 넣은 것이다 — 사람이 옮겨 적은 줄은 하나도 없다.\
> ★ 소스 펜스의 첫 줄(`// cs0Nb-….cs` 꼴)도 **캡처가 찍은 것**이다. 원고에 손으로 쓴 배너는 없다.
> ★★★ **진단 언어를 영어로 고정했다.** 안 주면 **로캘을 따라 한국어로 나와 재현이 안 된다** —\
> 01\~04 가 실측으로 받은 한국어 판이 ``error CS0029: 암시적으로 'string' 형식을 'int' 형식으로 변환할 수 없습니다.`` 였다.\
> 고정하는 법은 둘을 같이 거는 것이다 — 환경변수 **`DOTNET_CLI_UI_LANGUAGE=en`** 과 `csc` 플래그 **`-preferreduilang:en-US`**.
> **던진 형태** — MSBuild(`dotnet build`·`dotnet run`)를 **안 썼다.** Roslyn 컴파일러를 **직접** 부른다 —\
> 그래야 `bin/`·`obj/` 가 원리상 안 생기고, 진단 경로가 **절대 경로가 아니라 파일명**으로 나오며, 한 판이 0.3초 안에 끝난다.\
> 배너의 `csc` 는 아래 셸 함수이고, `ex.runtimeconfig.json` 은 아래 한 줄짜리 파일이다.
>
> ```text
> export DOTNET_CLI_TELEMETRY_OPTOUT=1 DOTNET_NOLOGO=1
> export DOTNET_CLI_UI_LANGUAGE=en            # ★★★ 안 주면 진단이 한국어로 나온다
> D=$(dirname "$(readlink -f "$(command -v dotnet)")")
> ls "$D"/packs/Microsoft.NETCore.App.Ref/10.0.12/ref/net10.0/*.dll | sed 's/^/-r:/' > refs.rsp
> echo '{"runtimeOptions":{"tfm":"net10.0","framework":{"name":"Microsoft.NETCore.App","version":"10.0.0"}}}' > ex.runtimeconfig.json
> csc() { dotnet exec "$D/sdk/10.0.401/Roslyn/bincore/csc.dll" \
>           -nologo -nostdlib -noconfig @refs.rsp \
>           -preferreduilang:en-US -langversion:latest "$@"; }
> ```
>
> **`-debug` 를 안 줬다** — PDB 가 없으면 스택 트레이스에 **절대 경로와 줄 번호가 안 박힌다**.\
> 그래서 이 문서의 트레이스는 ``at Program.<Main>$(String[] args)`` 에서 끝나고, 어느 머신에서 돌려도 같다.\
> **IL 덤프는 `-optimize` 없이**(기본 디버그) 낸 것이라 `nop` 이 섞여 있고 소스 구조가 그대로 보인다.\
> IL 을 찍는 `cs-il.cs`(82줄, 외부 도구 없이 BCL 만 쓴다)의 전문은 [03번](../03-boxing-and-unboxing/2-summary.md)의 (0)절에 있다.
> **버전** — 널 허용 참조 타입은 **C# 8부터**. `#nullable` 지시어도 **C# 8부터**다.\
> **.NET 6(C# 10)부터 새 프로젝트 템플릿이 `<Nullable>enable</Nullable>` 을 기본으로 넣는다** —\
> 그전에 만든 프로젝트는 **꺼져 있다.** ★ 「기본이 켜져 있다」와 「템플릿이 켜 준다」는 다른 말이다.\
> 널 상태 분석 특성(`[NotNullWhen]` 등)도 **C# 8/.NET Core 3.0부터**다.
> **경계** — 값 타입의 `?`(`int?`)는 **완전히 다른 기능**이다 — 그쪽 정본은 [08번](../08-nullable-value-types/)이다.\
> 같은 물음표가 **한쪽은 진짜 타입(`Nullable<T>` 구조체), 한쪽은 주석**이다((2)·(5)).\
> 연산자 `?.`·`??`·`??=` 는 [07번](../07-null-operators/)이 정본이다 — 여기는 **타입 쪽**만 본다.\
> 참조 타입이 무엇인지는 [01번](../01-value-types-and-reference-types/)이 정본이다.\
> 제네릭 제약(`where T : class?`·`notnull`)은 목록의 **25번 주제**다.\
> ★★ **직접 대비는 Kotlin 이다** — Kotlin 의 [널 안전 타입 편](../../../kotlin/syntax/03-null-safe-types/).\
> 거기서는 `String` 과 `String?` 이 **타입 시스템의 서로 다른 타입**이고, 여기서는 **런타임에 같은 타입**이다((2)).\
> TypeScript 의 `strictNullChecks` 와 성격이 더 가깝다 — TS 의 [`any`·`unknown`·`never`·`void` 편](../../../ts/syntax/04-any-unknown-never-void/).
> ★★ **흔들리는 칸 / 안 흔들리는 칸** — 제출 전 재대조는 이 표를 기준으로 판정한다.
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | ★ **`GC.GetAllocatedBytesForCurrentThread()` 의 절댓값**(프로세스 시작부터의 누적이다) | ★★★ **두 호출 사이의 증분**과 **그 증분이 0 이냐 아니냐** |
> | 시간·CPU 상태 — 이 문서는 **시간을 한 번도 안 쟀다** | **진단 코드**(`CS0220`·`CS8602` 류) · **진단 문구** · **`(행,열)`** |
> | 객체 주소 · `GetHashCode()` 의 참조형 값 | **`cc exit` 와 `run exit`**(갈라 적었다) |
> | `dotnet` 패치 버전이 오르면 달라질 수 있는 것 | **IL 명령어 열**(`add` · `add.ovf` · `box` · `brtrue.s` · `initobj`) |
> | — | **할당 바이트의 증분값**(24 · 32 · 0) · **타입 크기**(`Unsafe.SizeOf`) |

## 한눈에 — 쉽게 말하면

**`string?` 은 새 타입이 아니라 「컴파일러에게 붙여 둔 포스트잇」이다.**

이삿짐 상자에 「깨지기 쉬움」이라고 써 붙였다고 상자가 튼튼해지지는 않는다.
**상자는 그대로다.** 달라지는 것은 **옮기는 사람이 조심하게 되는 것**뿐이고,
포스트잇을 떼어 버리면(`!`) 아무 일도 안 일어난 것처럼 그냥 옮겨진다 — **그러다 깨진다.**

| 비유 | 실체 |
|---|---|
| **상자 자체는 안 바뀐다** | ★★★ `string` 과 `string?` 의 **IL 이 한 글자도 안 다르다**((2)) |
| **포스트잇은 상자에 남는다** | `NullableAttribute` 가 **메타데이터에 박힌다**((3)) |
| **「조심」이지 「금지」가 아니다** | 경고(`CS8602`)이지 **에러가 아니다**((1)) |
| **회사 규정으로 금지로 올린다** | `csc -warnaserror` → 같은 번호가 **`error` 로 바뀐다**((4)) |
| ★★ **포스트잇을 떼는 것** | `!` — **아무것도 검사하지 않는다.** 런타임에 그대로 깨진다((6)) |
| ★ **방마다 규칙을 다르게 건다** | `#nullable enable` / `disable` — **파일 안에서 구간별로 갈린다**((5)) |
| ★ **옮기는 사람은 눈앞만 본다** | 분석은 **메서드 하나 안에서만** 흐른다 — 헬퍼를 거치면 모른다((7)) |

- ★★★ **이 주제의 한 줄** — `string?` 과 `string` 의 차이는 **컴파일러 분석**이지 **런타임 타입이 아니다.**\
  그래서 **IL 이 같고**((2)), **실행 결과도 같고**((1)), **`NullReferenceException` 은 여전히 난다**((6)).
- ★★★ **그래서 축이 셋이 아니라 넷이다** — 「언어 명세 / 런타임 구현 / 이 판의 관찰」 어디에도 안 들어가는\
  **제4의 것,** 「**정적 분석**」이 이 주제의 본체다. 자세한 것은 「구현 세부사항 대 언어 보장」 절에 있다.
- ★★ **Kotlin 과 갈리는 자리가 여기다** — Kotlin 은 `String` 과 `String?` 이 **타입 시스템에서 다른 타입**이라\
  컴파일러가 **에러로 막고** 실제로 널 검사 코드를 **생성한다.** C# 은 **주석을 읽고 경고할 뿐**이다.

```text
   같은 코드, 다른 「포스트잇」 — 무엇이 갈리고 무엇이 안 갈리나

   소스                     컴파일러 분석            IL / 메타데이터          런타임
   ─────────────────────────────────────────────────────────────────────────────
   int Plain(string s)      s 는 not-null 이다       ldarg.0                 s 가 null 이면
     => s.Length;           → 경고 없음              callvirt get_Length     NullReferenceException
                                                    ret

   int Maybe(string? s)     s 는 maybe-null 이다     ldarg.0        ← 같다   s 가 null 이면
     => s!.Length;          → ! 가 경고를 끈다       callvirt get_Length     NullReferenceException
                                                    ret            ← 같다       ← 같다

                            ▲ 여기만 갈린다          ▲ 메타데이터의
                            (컴파일 시점에만 산다)     NullableContextAttribute 만 1 대 2
```

```text
   널 상태(null-state) 는 「타입」이 아니라 「지금 이 지점의 상태」다

   string? s = Maybe();          s : maybe-null
        │
        ├─ if (s != null) { … }        이 블록 안 s : not-null   ← 언어 규칙이 안다
        │
        ├─ if (MyCheck(s)) { … }       이 블록 안 s : maybe-null ← ★ 메서드 속은 안 본다
        │
        └─ if (!IsNullOrEmpty(s)) { … } 이 블록 안 s : not-null   ← ★ 특성이 알려 줬다
                                                                   [NotNullWhen(false)]
```

> **널 허용 참조 타입(nullable reference type)** — `string?` 처럼 `?` 를 붙인 참조 타입.\
> **새 타입이 아니다** — 같은 `System.String` 에 「널이 올 수 있다」는 주석을 붙인 것이다.

> **널 상태(null-state)** — 컴파일러가 **코드의 각 지점에서** 추적하는 상태. `not-null` 또는 `maybe-null` 둘뿐이다.\
> 변수의 타입이 아니라 **지점**의 성질이라, 같은 변수가 줄마다 다른 상태를 갖는다.

> **널 허용 맥락(nullable context)** — 분석을 켜고 끄는 스위치. **플래그가 둘**이다 —\
> **주석(annotation)**(`?` 를 쓸 수 있나)과 **경고(warning)**(분석 경고를 낼까). 넷의 조합이 가능하다((5)).

> **널 무시 연산자(null-forgiving operator) `!`** — 「내가 책임진다」고 컴파일러에게 말하는 것.\
> ★★ **아무것도 검사하지 않는다.** IL 에 한 바이트도 안 남는다((2)).

> **`NullableAttribute` / `NullableContextAttribute`** — 주석을 **메타데이터에 남기는** 컴파일러 생성 특성.\
> 다른 어셈블리가 내 API 의 널 허용 여부를 읽을 수 있게 한다((3)).

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. **`string?` 과 `string` 은 무엇이 다른가** — 그리고 **그 차이를 어디서 볼 수 있고 어디서 볼 수 없나**((2)·(3)).
2. **경고가 났을 때 무엇을 할 수 있나** — 고치기·`!`·지시어·`-warnaserror` 넷의 성격이 어떻게 다른가((4)\~(6)).
3. **분석이 틀리는 자리는 어디인가** — 그리고 **그것을 고칠 방법이 있나**((7)).

## 동작 방식

### (0) 이 주제가 쓰는 창 — 그리고 창 하나가 비어 있다

| 창 | 무엇을 보여 주나 | 이 주제에서 |
|---|---|---|
| ★★★ **컴파일 진단** | ★★★ **이 주제의 존재 이유** — 경고가 곧 기능이다 | (1)·(4)·(5)·(7) |
| ★★★ **IL** | ★★★ **`string?` 과 `string` 이 같다는 것** — 이 주제의 본체 | (2) |
| **메타데이터**(리플렉션) | 주석이 **어셈블리에 남는 것** | (3) |
| **예외 전문** | `!` 를 쓰면 **여전히 터진다**는 것 | (6) |
| **실행 출력** | 주석을 붙이든 안 붙이든 **실행이 같다**는 것 | (1) |
| ★ **할당 바이트** | ★ **이 주제에서는 쓸 일이 없다** — 아래 | — |

★★★ **다섯 번째 창(할당 바이트)이 비어 있는 것 자체가 결론이다.**\
(2)에서 **IL 이 한 바이트도 안 다르다**는 것을 보이고 나면, **할당도 다를 수가 없다.**
「재 봤더니 같았다」가 아니라 「**잴 것이 없다**」가 맞는 서술이다 —\
★ 01\~04 가 쓰던 다섯 창 중 하나가 **이 주제에서는 부적용**이고, 그 이유를 IL 이 준다.

★★ **반대로 컴파일 진단이 이 주제에서는 중심이다.** [03번](../03-boxing-and-unboxing/)은 진단이 거의 안 나서
할당 바이트가 유일한 창이었는데, **여기는 정반대**다 — **진단 말고는 볼 것이 없고, 그것이 기능의 전부**다.

### (1) ★★★ 경고가 나지만 실행은 그대로다

**언제 쓰나** — 가장 먼저 무는 자리. 「`string?` 을 쓰면 런타임이 막아 주겠지」가 틀린다.

```text
===== 소스: cs06b-warn.cs =====
#nullable enable
using System;

string s = "안녕";
string? t = null;

s = null;                       // ① 널이 될 수 있는 값을 널 아님 타입에
Console.WriteLine(t.Length);    // ② 널일 수 있는 것을 역참조
Console.WriteLine(s);
===== csc -out:ex.dll cs06b-warn.cs && dotnet ex.dll (cc exit=0 · run exit=134) =====
cs06b-warn.cs(7,5): warning CS8600: Converting null literal or possible null value to non-nullable type.
cs06b-warn.cs(8,19): warning CS8602: Dereference of a possibly null reference.
Unhandled exception. System.NullReferenceException: Object reference not set to an instance of an object.
   at Program.<Main>$(String[] args)
```

- **경고가 두 줄** 났다 — `CS8600`(널일 수 있는 값을 널 아님 타입에 대입)과 `CS8602`(널일 수 있는 것을 역참조).
- ★★★ **`cc exit=0` 이다.** 경고이지 **에러가 아니므로 어셈블리가 만들어졌고**, 실행됐고, **터졌다**(`run exit=134`).
- ★★★ **컴파일러가 두 번 경고한 바로 그 자리에서 `NullReferenceException` 이 났다.**\
  분석이 **맞았는데도 아무것도 막지 못했다** — 그것이 이 기능의 성격이다.

**같은 코드에서 `?` 만 빼고(맥락도 안 켜고) 던지면 이렇게 된다.**

```text
===== 소스: cs06b-nowarn.cs =====
using System;

string s = "안녕";
string? t = null;

s = null;
Console.WriteLine(t.Length);
Console.WriteLine(s);
===== csc -out:ex.dll cs06b-nowarn.cs && dotnet ex.dll (cc exit=0 · run exit=134) =====
cs06b-nowarn.cs(4,7): warning CS8632: The annotation for nullable reference types should only be used in code within a '#nullable' annotations context.
Unhandled exception. System.NullReferenceException: Object reference not set to an instance of an object.
   at Program.<Main>$(String[] args)
```

- ★★ **경고가 `CS8632` 하나로 바뀌었다** — 「`#nullable` 주석 맥락 밖에서 `?` 를 쓰지 마라」다.\
  **분석 자체가 꺼져 있으니 `CS8600`·`CS8602` 가 안 난다.**
- ★★★ **그런데 실행 결과는 한 글자도 같다** — `NullReferenceException`, `run exit=134`.\
  **맥락을 켜든 끄든 프로그램은 똑같이 돈다.**

### (2) ★★★ IL 에서 `string?` 과 `string` 은 같다 — 이 주제의 본체

**언제 쓰나** — 「그래서 정확히 무엇이 다른가」에 한 번에 답할 때. **이 절이 이 주제의 중심이다.**

```text
===== 소스: cs06b-il.cs =====
#nullable enable
using System;
using System.Reflection;

Il.Dump(typeof(Probe), "Plain");
Il.Dump(typeof(Probe), "Maybe");

foreach (string name in new[] { "Plain", "Maybe" }) {
    MethodInfo mi = typeof(Probe).GetMethod(name)!;
    ParameterInfo p = mi.GetParameters()[0];
    Console.WriteLine($"{name,-6} 매개변수 런타임 타입 = {p.ParameterType.FullName}");
    Console.WriteLine($"{name,-6} 메서드 메타데이터    = {Nul(mi.GetCustomAttributesData())}");
}

static string Nul(System.Collections.Generic.IList<CustomAttributeData> list) {
    var keep = new System.Collections.Generic.List<string>();
    foreach (CustomAttributeData a in list)
        if (a.AttributeType.Name.Contains("Nullable")) keep.Add(a.ToString());
    return keep.Count == 0 ? "(Nullable 계열 없음)" : string.Join(" ", keep);
}

public static class Probe {
    public static int Plain(string s)  { return s.Length; }
    public static int Maybe(string? s) { return s!.Length; }
}
===== csc -r:il.dll -out:ex.dll cs06b-il.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
--- Probe.Plain ---
  .locals [0] System.Int32
  IL_0000: nop
  IL_0001: ldarg.0
  IL_0002: callvirt System.String::get_Length
  IL_0007: stloc.0
  IL_0008: br.s IL_000a
  IL_000a: ldloc.0
  IL_000b: ret
--- Probe.Maybe ---
  .locals [0] System.Int32
  IL_0000: nop
  IL_0001: ldarg.0
  IL_0002: callvirt System.String::get_Length
  IL_0007: stloc.0
  IL_0008: br.s IL_000a
  IL_000a: ldloc.0
  IL_000b: ret
Plain  매개변수 런타임 타입 = System.String
Plain  메서드 메타데이터    = [System.Runtime.CompilerServices.NullableContextAttribute((Byte)1)]
Maybe  매개변수 런타임 타입 = System.String
Maybe  메서드 메타데이터    = [System.Runtime.CompilerServices.NullableContextAttribute((Byte)2)]
```

- ★★★ **두 덤프가 한 글자도 같다.** `Plain(string s)` 은 `s.Length` 를, `Maybe(string? s)` 는 `s!.Length` 를 쓰는데\
  **`nop` 위치까지 같은 8줄**이다. **`!` 가 IL 에 한 바이트도 안 남았다.**
- ★★★ **매개변수의 런타임 타입도 둘 다 `System.String`** 이다.\
  `String?` 이라는 타입은 **없다.** 리플렉션으로 물어도 안 나온다.
- ★★ **갈리는 것은 메타데이터 한 칸뿐이다** — `NullableContextAttribute((Byte)1)` 대 `((Byte)2)`.\
  **`1` 은 「주석 없음(= 널 아님)」, `2` 는** 「**널 허용**」이다. 이것이 **차이의 전부**다.
- ★★★ **그래서 다음 셋이 전부 따라 나온다.**
  1. **실행이 같다**((1)) — 같은 명령을 돌리므로.
  2. **할당이 같다**((0)) — 잴 것이 없다.
  3. **`NullReferenceException` 이 여전히 난다**((6)) — 검사 코드가 생성되지 않으므로.
- ★★ **Kotlin 과 갈리는 자리가 정확히 여기다.** Kotlin 컴파일러는 `String` 매개변수에 **널 검사 코드를 생성**하고\
  `String` 과 `String?` 을 **타입 시스템에서 다른 타입**으로 다뤄 **에러로 막는다.**\
  C# 은 **명령을 하나도 안 더한다.** 같은 문법 기호가 **다른 종류의 기능**이다.

### (3) ★ 주석은 메타데이터에 남는다

**언제 쓰나** — 「컴파일 시점에만 산다면서 왜 어셈블리에 뭔가 박히나」에 답할 때.\
**다른 어셈블리가 내 API 의 널 허용 여부를 읽으려면 어딘가에 남아 있어야 한다.**

```text
===== 소스: cs06b-meta.cs =====
#nullable enable
using System;
using System.Collections.Generic;
using System.Reflection;

Console.WriteLine($"타입     Box       {Nul(typeof(Box).GetCustomAttributesData())}");
foreach (FieldInfo f in typeof(Box).GetFields())
    Console.WriteLine($"필드     {f.Name,-9} {f.FieldType.Name,-7} {Nul(f.GetCustomAttributesData())}");
MethodInfo mi = typeof(Box).GetMethod("Mix")!;
Console.WriteLine($"메서드   Mix       {Nul(mi.GetCustomAttributesData())}");
foreach (ParameterInfo p in mi.GetParameters())
    Console.WriteLine($"  인자   {p.Name,-9} {p.ParameterType.Name,-7} {Nul(p.GetCustomAttributesData())}");
Console.WriteLine($"어셈블리           {Nul(typeof(Box).Assembly.GetCustomAttributesData())}");

static string Nul(IList<CustomAttributeData> list) {
    var keep = new List<string>();
    foreach (CustomAttributeData a in list)
        if (a.AttributeType.Name.Contains("Nullable"))
            keep.Add(a.AttributeType.Name + "(" + string.Join(",", a.ConstructorArguments) + ")");
    return keep.Count == 0 ? "(없음)" : string.Join(" ", keep);
}

public static class Box {
    public static string  NotNull = "";
    public static string? Maybe   = null;
    public static string Mix(string a, string? b) => a + b;
}
===== csc -out:ex.dll cs06b-meta.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
타입     Box       NullableContextAttribute((Byte)1) NullableAttribute((Byte)0)
필드     NotNull   String  (없음)
필드     Maybe     String  NullableAttribute((Byte)2)
메서드   Mix       (없음)
  인자   a         String  (없음)
  인자   b         String  NullableAttribute((Byte)2)
어셈블리           (없음)
```

- **`NullableAttribute((Byte)2)`** 가 `Maybe` 필드와 `b` 인자에만 붙어 있다.\
  **`NotNull` 필드와 `a` 인자에는 아무것도 없다** — 타입에 붙은 `NullableContextAttribute((Byte)1)` 이 **기본값**을 정하고,\
  **거기서 벗어나는 것만** 따로 표시하는 방식이다(메타데이터를 아끼려는 설계다).
- ★ **어셈블리 수준에는 아무것도 없다.** 널 허용 정보는 **타입·멤버·인자 단위**로 붙는다.
- ★★ **이것이 실제로 쓰이는 자리가 있다** — Learn 이 못 박은 대로 **Entity Framework Core 가 이 특성을 읽어**\
  「널 허용 참조 = 선택 열, 널 아님 = 필수 열」로 해석한다.\
  ★ 그러니까 **「런타임 동작이 안 바뀐다」는 언어 차원의 말**이고,\
  **리플렉션을 쓰는 라이브러리는 실제로 다르게 행동한다.** 둘을 갈라 읽어야 한다.

### (4) ★ 경고이지 에러가 아니다 — 그리고 에러로 올릴 수 있다

**언제 쓰나** — 팀 규약을 정할 때. 「경고는 결국 무시된다」에 대한 답이다.

```text
===== 소스: cs06b-warn.cs =====
#nullable enable
using System;

string s = "안녕";
string? t = null;

s = null;                       // ① 널이 될 수 있는 값을 널 아님 타입에
Console.WriteLine(t.Length);    // ② 널일 수 있는 것을 역참조
Console.WriteLine(s);
===== csc -warnaserror -out:ex.dll cs06b-warn.cs (cc exit=1) =====
cs06b-warn.cs(7,5): error CS8600: Converting null literal or possible null value to non-nullable type.
cs06b-warn.cs(8,19): error CS8602: Dereference of a possibly null reference.
```

- ★★ **같은 번호(`CS8600`·`CS8602`)가 `warning` 에서 `error` 로 바뀌었고 `cc exit` 이 0 에서 1 로 갔다.**\
  **진단 내용은 한 글자도 안 바뀌었다** — 심각도만 올라간 것이다.
- ★ MSBuild 에서는 `<TreatWarningsAsErrors>` 나 `<WarningsAsErrors>Nullable</WarningsAsErrors>` 다.\
  뒤엣것이 실무에서 많이 쓰는 형태다 — **널 경고만 에러로** 올린다.
- ★★★ **그래도 Kotlin 과는 다르다.** Kotlin 은 **언어가 막는 것**이고, 여기는 **빌드 설정이 막는 것**이다.\
  설정을 안 켠 사람이 만든 어셈블리는 그대로 통과하고, **`!` 는 여전히 통과한다.**

### (5) ★ 지시어로 파일 안에서 구간을 가른다

**언제 쓰나** — 큰 코드베이스를 조금씩 옮길 때. 이 기능의 **원래 목적**이 이것이다.

```text
===== 소스: cs06b-directive.cs =====
using System;

Console.WriteLine($"{Region.A(null)} {Region.B(null)} {Region.C(null)}");

public static class Region {
#nullable enable
    public static int A(string? s) => s.Length;        // enable 구간
#nullable disable
    public static int B(string s) => s.Length;         // disable 구간 — 같은 코드
#nullable enable warnings
    public static int C(string s) { s = null; return s.Length; }
#nullable restore
}
===== csc -out:ex.dll cs06b-directive.cs (cc exit=0) =====
cs06b-directive.cs(7,39): warning CS8602: Dereference of a possibly null reference.
cs06b-directive.cs(11,54): warning CS8602: Dereference of a possibly null reference.
```

- **세 구간 중 두 구간만 경고가 났다** — `A`(7번 줄)와 `C`(11번 줄)다.\
  **`#nullable disable` 구간의 `B` 는 같은 코드인데 조용하다.**
- ★★ **맥락은 플래그가 둘이다** — **주석**(`?` 를 쓸 수 있나)과 **경고**(분석을 낼까).\
  `#nullable enable warnings` 는 **경고만** 켠다 — 그래서 `C` 의 `s = null` 과 `s.Length` 가 잡혔다.
- ★ 지시어 목록: `enable` / `disable` / `restore` 셋에 각각 `annotations` · `warnings` 를 붙여 **아홉 조합**이 된다.\
  `restore` 는 **프로젝트 설정으로 되돌린다**는 뜻이다.
- ★★★ **Learn 이 못 박은 함정 하나** — **생성된 코드 파일에는 전역 맥락이 적용되지 않는다.**\
  `*.g.cs`·`*.designer.cs` 로 끝나거나 `<auto-generated>` 주석이 있으면 **분석이 통째로 꺼진다.**\
  ★ 「프로젝트를 켰으니 전부 검사된다」가 여기서 틀린다.

**소스에 지시어를 안 쓰고 컴파일러 플래그로 켤 수도 있다** — MSBuild 의 `<Nullable>enable</Nullable>` 이 이것이다.

```text
===== 소스: cs06b-nowarn.cs =====
using System;

string s = "안녕";
string? t = null;

s = null;
Console.WriteLine(t.Length);
Console.WriteLine(s);
===== csc -nullable:enable -out:ex.dll cs06b-nowarn.cs (cc exit=0) =====
cs06b-nowarn.cs(6,5): warning CS8600: Converting null literal or possible null value to non-nullable type.
cs06b-nowarn.cs(7,19): warning CS8602: Dereference of a possibly null reference.
```

- ★ **(1)의 두 경고가 그대로 돌아왔다.** 소스는 (1)의 `#nullable enable` 판이 아니라\
  **지시어가 없는 판**인데 **플래그만으로 같은 진단이 난다.**
- ★★ 줄 번호가 다른 것에 주의하라 — `(6,5)`·`(7,19)` 다. **지시어 한 줄이 없어서 줄이 하나씩 당겨졌다.**\
  ★ **진단의 `(행,열)` 은 안 흔들리는 칸이지만, 소스가 다르면 당연히 다르다.**

### (6) ★★ `!` 는 아무것도 검사하지 않는다

**언제 쓰나** — 「`!` 를 붙여서 경고를 없앴다」가 무엇을 한 것인지 정확히 알 때.

```text
===== 소스: cs06b-bang.cs =====
#nullable enable
using System;

string? maybe = null;
string sure = maybe!;          // 컴파일러에게 "내가 책임진다"
Console.WriteLine(sure.Length);
===== csc -out:ex.dll cs06b-bang.cs && dotnet ex.dll (cc exit=0 · run exit=134) =====
Unhandled exception. System.NullReferenceException: Object reference not set to an instance of an object.
   at Program.<Main>$(String[] args)
```

- ★★★ **진단이 0줄이다.** `cc exit=0` 이고 경고도 에러도 없다 — **`!` 가 경고를 완전히 지웠다.**\
  ★ 「진단이 0줄이다」가 결론인 블록이라 **명령과 `(cc exit=0 · run exit=134)` 까지 담아** 실었다.
- ★★★ **그리고 `NullReferenceException` 으로 죽었다.**\
  `!` 는 **런타임 검사를 하지 않는다.** (2)에서 본 대로 **IL 에 한 바이트도 안 남는다.**
- ★★ **그래서 `!` 는 「이 값은 널이 아니다」가 아니라 「경고를 끄겠다」다.**\
  틀리면 **아무 도움 없이 터진다** — 경고를 그냥 무시한 것과 **런타임 결과가 똑같다.**
- **`!` 를 써도 되는 자리** — 컴파일러가 알 수 없는 **외부 계약**을 내가 아는 경우다.\
  예: 테스트 코드, `TryGetValue` 뒤의 `out` 변수(특성이 없는 옛 API), 직렬화 프레임워크가 채우는 필드.\
  ★ 그때도 **주석 한 줄로 근거를 적어 두는 것**이 관용구다 — `!` 자체는 이유를 남기지 않는다.

### (7) ★★ 분석이 틀리는 자리 — 메서드를 거치면 모른다

**언제 쓰나** — 「널 검사를 했는데 왜 경고가 나나」에 답할 때.

```text
===== 소스: cs06b-flow.cs =====
#nullable enable
using System;
using System.Diagnostics.CodeAnalysis;

string? s = Maybe();

if (s != null)                 Console.WriteLine(s.Length);   // ① 언어 규칙 — 안다
if (MyCheck(s))                Console.WriteLine(s.Length);   // ② 내 헬퍼 — 모른다
if (!string.IsNullOrEmpty(s))  Console.WriteLine(s.Length);   // ③ BCL — 특성이 있어 안다
if (MyCheckAttr(s))            Console.WriteLine(s.Length);   // ④ 내 헬퍼 + 특성 — 안다

static string? Maybe() => null;
static bool MyCheck(string? x) => x != null;
static bool MyCheckAttr([NotNullWhen(true)] string? x) => x != null;
===== csc -out:ex.dll cs06b-flow.cs (cc exit=0) =====
cs06b-flow.cs(8,50): warning CS8602: Dereference of a possibly null reference.
```

- ★★★ **네 줄 중 한 줄만 경고가 났다** — 8번 줄, 곧 **내가 만든 `MyCheck(s)`** 다.
- **왜 갈리나**
  1. `if (s != null)` — **언어 규칙**이다. 컴파일러가 직접 안다.
  2. `if (MyCheck(s))` — ★ **메서드 본문을 안 본다.** `MyCheck` 가 무엇을 검사하든 **널 상태가 안 바뀐다.**\
     ★★ **바로 옆 줄에 `x != null` 이라고 적혀 있는데도 모른다** — 분석은 **메서드 하나 안에서만** 흐른다.
  3. `if (!string.IsNullOrEmpty(s))` — BCL 에 **`[NotNullWhen(false)]` 특성이 붙어 있어** 안다.
  4. `if (MyCheckAttr(s))` — ★ **내 헬퍼에도 같은 특성을 붙이면 안다.** `[NotNullWhen(true)]` 하나로 고쳐진다.
- ★★★ **그래서 「분석이 틀린다」는 말은 정확하지 않다** — **분석이 모르는 것이고, 알려 주면 안다.**\
  고치는 수단이 셋이다: **특성을 붙인다** · **`!` 로 끈다** · **검사를 인라인한다.**\
  ★ 앞엣것만이 **다음 호출자에게도 전달되는** 고침이다.
- ★ 널 상태 분석 특성 목록: `[NotNull]` · `[MaybeNull]` · `[NotNullWhen]` · `[MaybeNullWhen]` ·\
  `[NotNullIfNotNull]` · `[DoesNotReturn]` · `[DoesNotReturnIf]` · `[MemberNotNull]` · `[MemberNotNullWhen]`.\
  **이 문서는 `[NotNullWhen(true)]` 하나만 던졌다.**

## 문법 — 형태와 규칙

**형태** — 던져서 확인한 것만 싣는다.

```text
===== 소스: cs06b-form.cs =====
using System;

#nullable enable
string  notNull = "안녕";        // 널을 넣으면 경고
string? maybe   = null;          // 널을 넣어도 조용
Console.WriteLine($"notNull.Length = {notNull.Length}");
Console.WriteLine($"maybe 는 {(maybe is null ? "null" : maybe)}");

maybe = "다시";
Console.WriteLine($"maybe!.Length  = {maybe!.Length}   ← ! 는 경고만 끈다. 검사는 안 한다");
#nullable disable

string oblivious = null;         // 맥락이 꺼졌으므로 경고가 없다
Console.WriteLine($"맥락 밖에서는 {(oblivious is null ? "null 도 조용하다" : oblivious)}");

#nullable restore
Console.WriteLine("restore 는 프로젝트 설정으로 되돌린다");
===== csc -out:ex.dll cs06b-form.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
notNull.Length = 2
maybe 는 null
maybe!.Length  = 2   ← ! 는 경고만 끈다. 검사는 안 한다
맥락 밖에서는 null 도 조용하다
restore 는 프로젝트 설정으로 되돌린다
```

- ★ **`#nullable disable` 구간에서 `string oblivious = null;` 이 경고 없이 통과했다** — 같은 파일 안에서 규칙이 갈린다.
- ★ `#nullable restore` 는 「끈다」가 아니라 「**프로젝트 설정으로 되돌린다**」다.

**금지 사례 — `?` 를 못 쓰는 자리. 던져서 받았다.**

```text
===== 소스: cs06b-forbid.cs =====
#nullable enable
using System;

Console.WriteLine("컴파일까지 못 간다");

public class Probe {
    public void A() { var e = System.String?.Empty; Console.WriteLine(e); }   // 멤버 접근의 대상 타입
    public void B() { var o = new object?(); Console.WriteLine(o); }          // 객체 생성 식
    public void C() { object t = "x"; if (t is string? ns) Console.WriteLine(ns); }  // 타입 검사 식
}
===== csc -out:ex.dll cs06b-forbid.cs (cc exit=1) =====
cs06b-forbid.cs(7,31): error CS0119: 'string' is a type, which is not valid in the given context
cs06b-forbid.cs(7,45): error CS0176: Member 'string.Empty' cannot be accessed with an instance reference; qualify it with a type name instead
cs06b-forbid.cs(8,31): error CS8628: Cannot use a nullable reference type in object creation.
cs06b-forbid.cs(9,48): error CS8116: It is not legal to use nullable type 'string?' in a pattern; use the underlying type 'string' instead.
```

**기반 타입은 파일이 통째로 막혀서 따로 던졌다** — 선언 단계 에러라 뒤쪽 진단이 아예 안 나온다.

```text
===== 소스: cs06b-base.cs =====
#nullable enable

System.Console.WriteLine("컴파일까지 못 간다");

public class Derived : System.Object? { }
===== csc -out:ex.dll cs06b-base.cs (cc exit=1) =====
cs06b-base.cs(5,24): error CS1521: Invalid base type
```

| 쓴 것 | 진단 | 무엇을 말하나 |
|---|---|---|
| `System.String?.Empty` | ``CS0119`` + ``CS0176`` | ★ **`?.` 로 파싱된다** — 타입 이름 자리에 `?` 를 붙이면 널 조건 연산자가 돼 버린다 |
| `new object?()` | ``CS8628: Cannot use a nullable reference type in object creation.`` | 런타임에 인스턴스를 만드는 자리다 |
| `t is string? ns` | ``CS8116: It is not legal to use nullable type 'string?' in a pattern`` | ★ **런타임 타입 검사**라 구분할 것이 없다 |
| `class D : System.Object?` | ``CS1521: Invalid base type`` | 런타임 타입 계층에 들어가는 자리다 |

- ★★★ **넷을 외우지 말고 한 줄로 유도하라** — **`string?` 은 타입이 아니라 주석**이다((2)).\
  **타입이 와야 하는 자리에는 주석을 붙일 자리가 없다.**
- ★★★ **그런데 Learn 의 금지 목록에 하나가 더 있고, 그것은 이 판에서 통과한다.**\
  [Learn 의 널 허용 참조 형식 문서](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/builtin-types/nullable-reference-types)는\
  ``catch (Exception? e)`` 를 「not Allowed」로 적어 두었는데, **Roslyn 10.0.401 은 진단을 0줄 내고 정상 실행했다.**

```text
===== 소스: cs06b-catch.cs =====
#nullable enable
using System;

try { throw new InvalidOperationException("일부러"); }
catch (Exception? ex) { Console.WriteLine($"잡혔다: {ex!.Message}"); }
Console.WriteLine("끝");
===== csc -out:ex.dll cs06b-catch.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
잡혔다: 일부러
끝
```

- ★★★ **진단이 0줄이다**(`cc exit=0`)**, 그리고 예외를 정상으로 잡았다**(`run exit=0`).\
  ★ 「문서에 금지라고 적혀 있다」는 **돌려 본 것이 아니다** — 이 갈래가 던져서 확인하는 이유가 이것이다.\
  ★★ 다만 **「통과한다」와 「써도 된다」는 다른 말**이다. `?` 가 아무 뜻이 없으므로 **쓸 이유가 없다** — 위 예제도 `ex!` 를 써야 했다.

**규칙**

- **맥락이 꺼져 있으면 모든 참조 타입이** 「**널 허용 무관심(nullable-oblivious)**」이다 — 경고가 없다.\
  그때도 **기본 상태는 `not-null`** 로 친다.
- **맥락이 켜지면** 참조 타입은 **기본이 널 아님**이고, `?` 를 붙인 것만 널 허용이다.
- **널 상태는 지점의 성질이다** — 같은 변수가 줄마다 `not-null` 과 `maybe-null` 을 오간다.\
  ★ `maybe-null` 을 널 아님 변수에 대입하면 경고가 나고, **그 뒤로도 그 변수가 `maybe-null` 로 남는다.**
- **제네릭에서 `T?` 의 뜻이 타입 인자에 달렸다** — `Box<string>` 이면 `string?`, `Box<int>` 면 **그냥 `int`** 다.\
  ★★ `where T : struct` 를 걸면 `T?` 가 **`Nullable<T>`** 가 된다 — [08번](../08-nullable-value-types/)과 만나는 자리다.
- **필드는 생성자에서 널 아님으로 채워야 한다** — 안 채우면 경고(`CS8618` 계열)다.\
  ★ `required`(C# 11)와 함께 쓰면 호출자에게 의무를 넘길 수 있다([목록의 **13번 주제**](../13-properties-init-required-field/)).

## 어디서 틀리나

1. ★★★ **「`string?` 을 쓰면 런타임이 막아 준다」** — 안 막는다((1)·(6)). **IL 이 같다**((2)).
2. ★★★ **`!` 를 「널 검사」로 읽는 것** — 아무것도 검사하지 않는다((6)). **경고만 끈다.**
3. ★★ **경고를 에러로 읽는 것** — 기본은 경고다((4)). 빌드가 통과하고 배포되고 터진다.
4. ★★ **내가 만든 `IsValid(x)` 를 컴파일러가 이해한다고 믿는 것** — 안 한다((7)).\
   ★ 고치는 법은 `!` 가 아니라 **`[NotNullWhen]` 특성**이다.
5. ★★ **프로젝트에 `<Nullable>enable</Nullable>` 을 넣었으니 전부 검사된다고 믿는 것** —\
   **생성된 코드 파일은 통째로 빠진다**((5)).
6. ★ **경고가 없으니 널이 없다고 믿는 것** — 맥락이 **꺼진 어셈블리에서 온 값**은 `not-null` 로 들어온다.\
   ★ **라이브러리 경계에서 분석이 끊긴다.**
7. ★★ **값 타입의 `?` 와 같은 기능으로 외우는 것** — `int?` 는 **진짜 타입**(`Nullable<int>` 구조체)이고\
   `string?` 은 **주석**이다([08번](../08-nullable-value-types/)). 같은 기호, 다른 기능.
8. ★ **`?` 를 아무 데나 붙이는 것** — 타입이 와야 하는 자리에는 못 붙인다(문법 절의 금지 사례).
9. ★ **`#nullable enable` 의 플래그가 둘이라는 것을 모르는 것** — `enable warnings` 와 `enable annotations` 가 다르다((5)).
10. ★★ **경고 번호를 안 보고 뭉뚱그리는 것** — `CS8600`(대입) · `CS8602`(역참조) · `CS8632`(맥락 밖 `?`) ·\
    `CS8618`(생성자에서 미초기화)이 **서로 다른 실수**다.

## 구현 세부사항 대 언어 보장

★★★ **이 주제는 「세 층」이 안 맞는다 — 제4의 층이 있다.**

01\~04 는 **언어 명세 / 런타임 구현 / 이 판의 관찰** 셋으로 갈랐다.
그런데 널 허용 참조 타입은 **런타임에 존재하지 않고**(IL 이 같다) **명세가 보장하는 실행 동작도 없다.**
살고 있는 곳이 **컴파일러 안**이다.

```text
   네 개의 층 — 이 주제는 세 번째 칸이 비어 있다

   ① 언어 명세 (ECMA-334)
        └─ 무엇이 언제나 참인가:  string? 은 System.String 이다 ·
                                  경고이지 에러가 아니다 · ? 를 쓸 수 없는 문법 자리
   ② ★★★ 정적 분석 (Roslyn 의 널 상태 추적)      ← 이 주제의 본체가 여기 산다
        └─ 컴파일러 판에 달렸다. 명세가 문장 단위로 규정하지 않는다.
           같은 코드가 다음 Roslyn 에서 경고를 더 낼 수도 덜 낼 수도 있다.
   ③ 런타임 (CoreCLR)
        └─ ★ 비어 있다. 생성되는 명령이 하나도 없다((2)).
           단 ★★ 메타데이터를 읽는 라이브러리(EF Core)는 행동이 갈린다((3)).
   ④ 이 판의 관찰
        └─ 경고 번호·문구·(행,열) · NullableContextAttribute 의 바이트값
```

- ★★★ **②가 있다는 것이 이 주제를 다른 주제와 가르는 전부다.**\
  「`checked` 가 `add.ovf` 를 찍는다」([05번](../05-numeric-types-checked-decimal/))는 ①과 ③에 걸쳐 있는데,\
  「`s` 가 여기서 `maybe-null` 이다」는 **②에만 있다.** 실행해도 안 보이고, 명세를 읽어도 줄 단위로는 안 나온다.
- ★★ **그래서 「돌려 봤다」가 이 주제에서는 절반만 증명한다.**\
  나머지 절반은 **컴파일러에게 물어본 것**(진단)이고, 그것이 **판에 달려 있다.**

| 층 | 무엇을 말하나 | 이 주제의 예 |
|---|---|---|
| **언어 명세(ECMA-334)** | 무엇이 **언제나** 참인가 | `string?` 이 `System.String` 인 것 · `!` 가 런타임 동작을 안 바꾸는 것 · `?` 를 못 쓰는 문법 자리 · 맥락이 주석·경고 두 플래그인 것 |
| ★★★ **정적 분석(Roslyn)** | **컴파일러가** 어디까지 추론하나 | `MyCheck(s)` 를 못 알아보는 것((7)) · `IsNullOrEmpty` 를 알아보는 것 · 경고를 내는 정확한 지점 |
| **런타임(CoreCLR)** | 이 판이 **지금** 그렇게 하는 것 | ★ **거의 비어 있다.** `NullReferenceException` 메시지·종료 코드 134 |
| **이 판의 관찰** | 돌려 봤더니 이랬다는 것 | 경고 번호·문구·`(행,열)` · `NullableContextAttribute((Byte)1/2)` · 메타데이터를 아끼는 배치 방식((3)) |

**언어가 보장하는 것**(구현이 바뀌어도 같다)

- **`string?` 과 `string` 이 같은 .NET 타입**인 것 — 새 타입이 생기지 않는다.
- **널 허용 주석이 런타임 동작을 바꾸지 않는** 것 — 컴파일러가 널 검사를 **생성하지 않는다.**
- **기본이 경고이지 에러가 아닌** 것.
- **`!` 가 경고만 끄고 검사를 하지 않는** 것.
- **맥락에 주석·경고 두 플래그가 있고 지시어로 구간을 가를 수 있는** 것.
- **`?` 를 기반 타입·`new`·`is`·`catch` 에 쓸 수 없는** 것.

**컴파일러(Roslyn)에 달린 것**

- ★★ **어떤 코드에서 경고가 나고 안 나는가의 정확한 경계** — 흐름 분석이 개선되면 움직인다.
- **경고 문구와 진단 코드의 배정.**
- **메타데이터에 특성을 붙이는 방식** — `NullableContextAttribute` 로 기본값을 주고 예외만 `NullableAttribute` 로 붙이는 것((3)).

## 언제 쓰고 언제 안 쓰나

| 선택 | 언제 | 대가 |
|---|---|---|
| **`<Nullable>enable</Nullable>`** | ★★ 새 프로젝트 — .NET 6부터 템플릿 기본값이다 | 옛 코드를 옮기면 경고가 쏟아진다 |
| **`#nullable enable` 파일 단위** | 큰 코드베이스를 조금씩 옮길 때 | 파일마다 상태가 달라 헷갈린다 |
| **`annotations` 먼저, `warnings` 나중** | ★ 주석을 먼저 달고 경고는 나중에 고칠 때 | 그 사이에는 분석이 안 돈다 |
| **`-warnaserror`(널 경고만)** | 팀이 「널 경고는 버그」로 합의했을 때 | 라이브러리 경계·생성 코드는 여전히 샌다 |
| **`!`** | ★ 컴파일러가 알 수 없는 **외부 계약**을 내가 아는 자리 | **근거가 코드에 안 남는다** — 주석을 같이 달아라 |
| **`[NotNullWhen]` 등 특성** | ★★ 내 헬퍼가 널 검사를 할 때 | 특성 이름을 알아야 한다 |
| **끄고 사는 것** | 옛 코드베이스 · 생성 코드 위주 프로젝트 | 널 사고를 **컴파일 시점에 못 잡는다** |

- ★★★ **`!` 를 습관적으로 쓰기 시작하면 이 기능 전체가 무의미해진다.**\
  경고가 뜰 때의 올바른 순서는 **① 진짜 널일 수 있나 확인 → ② 검사를 넣거나 설계를 고침 → ③ 그래도 안 되면 특성 → ④ 최후에 `!`** 다.
- ★★ **라이브러리를 만들 때는 켜는 것이 사실상 의무**다 — 메타데이터가 **소비자의 경고를 만들기 때문**이다((3)).\
  안 켜고 배포하면 소비자 쪽에서 **모든 반환값이 널 아님으로 들어간다.**

## 핵심 문장

1. ★★★ **`string?` 과 `string` 의 차이는 컴파일러 분석이지 런타임 타입이 아니다** — **IL 이 한 글자도 안 다르다.**
2. ★★★ **`!` 는 아무것도 검사하지 않는다** — 경고만 끄고, 틀리면 `NullReferenceException` 으로 그대로 터진다.
3. ★★ **경고이지 에러가 아니다** — `-warnaserror` 로 올릴 수 있지만 그것은 **언어가 아니라 빌드 설정**이다.
4. ★★ **주석은 메타데이터에 남는다** — 그래서 **다른 어셈블리가 읽고, EF Core 같은 라이브러리는 실제로 다르게 행동한다.**
5. ★★ **널 상태는 타입이 아니라 「이 지점의 상태」다** — 그래서 메서드를 하나 거치면 초기화된다.
6. ★ **그것을 고치는 것은 `!` 가 아니라 특성이다** — `[NotNullWhen(true)]` 한 줄이 호출자 전부에게 전달된다.
7. ★★★ **이 주제는 「언어 / 런타임 / 관찰」 세 층에 안 들어간다** — **정적 분석이라는 제4의 층**이 본체다.

## 관련 자료

- [07번 — 널 관련 연산자](../07-null-operators/) — `?.`·`??`·`??=`. **이 주제가 「무엇이 널일 수 있나」를 선언하면,\
  07번은 「그러면 어떻게 다루나」다.** 사슬의 가운데다.
- [08번 — 널 허용 값 타입 `Nullable<T>`](../08-nullable-value-types/) — **같은 `?` 기호인데 진짜 타입**이다.\
  ★ 사슬의 끝이자 **이 주제의 반증**이다.
- [01번 — 값 타입과 참조 타입](../01-value-types-and-reference-types/) — 왜 참조 타입만 이 문제가 있나의 정본.
- 목록의 **25번 주제**(제네릭 제약) — `where T : class?` · `notnull` · `T?` 의 해석.
- [목록의 **13번 주제**](../13-properties-init-required-field/)(속성과 `required`) — 생성자에서 필드를 채우라는 경고를 푸는 법.
- 목록의 **53번 주제**(특성 정의와 사용) — `NullableAttribute` 가 무엇인지의 정본.
- **Kotlin 의 [널 안전 타입 편](../../../kotlin/syntax/03-null-safe-types/)** —\
  ★★ **직접 대비**다. Kotlin 은 **타입 시스템**(에러로 막고 검사 코드를 생성), C# 은 **컴파일러 분석**(경고만).
- **TS 의 [`any`·`unknown`·`never`·`void` 편](../../../ts/syntax/04-any-unknown-never-void/)** —\
  `strictNullChecks` 가 성격이 더 가깝다. **둘 다 지우고 나면 런타임에 아무것도 안 남는다.**
- **Java 의 [원시 타입과 래퍼 편](../../../java/syntax/01-primitives-and-wrappers/)** —\
  Java 에는 이 문법이 없고 `Optional` 이나 `@Nullable` 애너테이션으로 우회한다.\
  ★ `Optional` 은 **객체를 하나 더 만든다** — C# 의 주석은 **할당이 0**이다((0)).

## 용어 풀이

- **널 허용 참조 타입** — `?` 를 붙인 참조 타입. **새 타입이 아니라 주석**이다.
- **널 상태(null-state)** — 컴파일러가 각 지점에서 추적하는 `not-null` / `maybe-null`.
- **널 허용 맥락(nullable context)** — 분석 스위치. **주석 플래그**와 **경고 플래그** 둘로 이루어진다.
- **널 무시 연산자 `!`** — 경고를 끄는 연산자. 검사도 변환도 하지 않는다.
- **널 허용 무관심(nullable-oblivious)** — 맥락이 꺼진 코드의 참조 타입 상태. 경고가 안 난다.
- **`NullableAttribute` / `NullableContextAttribute`** — 주석을 메타데이터에 남기는 컴파일러 생성 특성.
- **널 상태 분석 특성** — `[NotNullWhen]` 등. **메서드 경계를 넘어 널 상태를 전달하는** 유일한 수단.
- **`CS8600`** — 널일 수 있는 값을 널 아님 타입에 대입.
- **`CS8602`** — 널일 수 있는 것을 역참조.
- **`CS8632`** — 주석 맥락 밖에서 `?` 를 썼다.

## 더 들어가면

- **`CS8618`**(생성자에서 널 아님 필드 미초기화)과 `required`·`init` 의 관계 — [목록의 **13번 주제**](../13-properties-init-required-field/).
- **`[MemberNotNull]` / `[MemberNotNullWhen]`** — `Initialize()` 를 부르면 필드가 채워진다는 것을 알리는 특성.\
  ★ **이 문서는 안 던졌다.**
- **`[NotNullIfNotNull(nameof(input))]`** — 「입력이 널 아니면 출력도 널 아님」을 잇는 특성. **안 던졌다.**
- **제네릭에서의 `T?`** — 제약이 없으면 값 타입 인자에는 아무 효과가 없다. **안 던졌다.**
- **`default!`** — 널 아님 필드를 「나중에 채운다」고 우기는 관용구. `!` 의 가장 흔한 용례이자 가장 흔한 사고.
- ★ **왜 에러가 아니라 경고인가** — **옛 코드와의 호환**이다. 에러로 만들었으면 C# 8 로 올리는 순간\
  세상의 모든 프로젝트가 빌드에 실패했을 것이다. ★ **Kotlin 은 처음부터 그렇게 설계할 수 있었다** — 새 언어였으니까.\
  **같은 문제에 대한 답이 갈린 이유가 기술이 아니라 역사**인 자리다.
- **널 허용 정보를 읽는 다른 소비자** — EF Core 외에 **직렬화기·검증기·소스 생성기**가 있다.
