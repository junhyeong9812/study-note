# csharp/syntax/06 — 널 허용 참조 타입(C# 8) — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> **기준 소스** — [ECMA-334 7판(2023-12)](https://ecma-international.org/publications-and-standards/standards/ecma-334/) · [Microsoft Learn — C# 언어 레퍼런스](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/) · [Learn — `checked`/`unchecked`](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/statements/checked-and-unchecked) · [Learn — 널 허용 값 형식](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/builtin-types/nullable-value-types) · [Learn — 널 허용 참조 형식](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/builtin-types/nullable-reference-types) · [Learn — 멤버 접근·널 조건 연산자](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/operators/member-access-operators)
> **실행 검증** — 이 문서의 모든 출력·진단·IL·할당 바이트는 **.NET SDK 10.0.401** ·\
> 런타임 **`.NET 10.0.12`**(`Microsoft.NETCore.App`) · 타겟 **`net10.0`** · **linux-x64** 에서 실제로 돌려 얻은 것이다(2026-09-25).\
> ★ 블록은 캡처 스크립트가 파일로 받아 조립기가 끼워 넣은 것이다 — 사람이 옮겨 적은 줄은 하나도 없다.\
> ★ 소스 펜스의 첫 줄(`// cs0Nb-….cs` 꼴)도 **캡처가 찍은 것**이다. 원고에 손으로 쓴 배너는 없다.
> **읽는 법** — ★★★ **이 주제의 근거는 「컴파일 진단」과 「IL」 둘뿐이다.**\
> 할당 바이트는 **쓰지 않았다** — 3번에서 IL 이 같다는 것을 보이고 나면 **잴 것이 없기 때문**이다.\
> ★ **`cc exit` 과 `run exit` 을 갈라 적었다** — 이 주제에서는 「컴파일은 통과했는데 죽는다」가 기본값이다.\
> 자세한 환경과 던진 형태는 [2-summary.md](2-summary.md)의 머리말·(0)절에 있다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ 경고 **2줄** · `cc exit=0` · `run exit=134` — **경고한 자리에서 그대로 터진다**

**출력**

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

**왜 그런가**

- **`CS8600`**(7번 줄) — 널일 수 있는 값을 **널 아님 타입에 대입**했다(`s = null`).
- **`CS8602`**(8번 줄) — 널일 수 있는 것을 **역참조**했다(`t.Length`).
- ★★★ **`cc exit=0` 이다.** 경고이지 에러가 아니므로 **어셈블리가 만들어졌다.**\
  빌드가 통과하고, 배포되고, 돌다가 **`NullReferenceException`** 으로 죽는다(`run exit=134`).
- ★★★ **컴파일러가 경고한 바로 그 자리에서 터졌다.** 분석은 **맞았다.**\
  맞았는데도 아무것도 막지 못한 것 — 그것이 이 기능의 성격이다.\
  ★ **막는 것은 사람이지 런타임이 아니다.**
- ★ 「경고가 났으니 빌드를 막아야 한다」는 결론이 여기서 나온다 → 7번.

### 2. 진단이 **`CS8632` 한 줄**로 바뀐다 — 그런데 **실행은 한 글자도 같다**

**출력**

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

**왜 그런가**

- **`CS8632`** 는 「`#nullable` 주석 맥락 **밖**에서 `?` 를 쓰지 마라」다.\
  맥락이 꺼져 있으면 `?` 가 **아무 뜻이 없으므로** 컴파일러가 「이거 의도한 거 맞나」라고 묻는 것이다.
- **`CS8600`·`CS8602` 가 안 나는 이유** — **분석 자체가 꺼져 있다.**\
  맥락이 꺼지면 모든 참조 타입이 **널 허용 무관심(nullable-oblivious)** 이 되고, 기본 상태는 `not-null` 로 친다.
- ★★★ **실행 결과는 1번과 한 글자도 같다** — `NullReferenceException`, `run exit=134`.\
  **맥락을 켜든 끄든 프로그램은 똑같이 돈다.** 이것이 3번의 예고편이다.
- ★ **맥락을 켜는 방법이 하나 더 있다** — 소스를 안 고치고 컴파일러 플래그로 켜는 것이다\
  (MSBuild 의 `<Nullable>enable</Nullable>`).

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

- ★★ **1번의 두 경고가 그대로 돌아왔다.** 소스에는 `#nullable enable` 이 **없는데도** 같은 진단이 난다.
- ★ **줄 번호가 `(6,5)`·`(7,19)` 로 하나씩 당겨진 것**에 주의하라 — 지시어 한 줄이 없기 때문이다.\
  **진단의 `(행,열)` 은 안 흔들리는 칸이지만, 소스가 다르면 당연히 다르다.**

### 3. ★★★ **IL 이 한 글자도 안 다르다** — `!` 는 **0바이트**다

**출력**

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

**왜 그런가**

- ★★★ **두 덤프가 8줄씩 완전히 같다.** `nop` 위치까지 같다.\
  `Plain` 은 `s.Length`, `Maybe` 는 `s!.Length` 인데 **생성된 명령이 동일**하다 — **`!` 는 IL 에 0바이트를 남긴다.**
- ★★★ **리플렉션이 답하는 매개변수 타입도 둘 다 `System.String`** 이다.\
  ★ **`String?` 이라는 타입은 존재하지 않는다.** 런타임 타입 체계에 그런 것이 없다.
- ★★ **갈리는 것은 메타데이터 한 칸**이다 — `NullableContextAttribute((Byte)1)` 대 `((Byte)2)`.\
  **`1` 이 「널 아님」, `2` 가** 「**널 허용**」이다. 이것이 두 메서드 차이의 **전부**다.
- ★★★ **여기서 따라 나오는 결론 셋**
  1. ★ **실행이 같다**(1번·2번) — 같은 명령을 돌리므로.
  2. ★ **할당도 같다** — 명령이 같으니 **잴 것이 없다.**\
     이 주제에서 **할당 바이트 창이 비어 있는 이유**가 이것이다(「재 봤더니 같았다」가 아니라 **「잴 것이 없다」**).
  3. ★ **`NullReferenceException` 이 여전히 난다**(4번) — 널 검사 코드가 **생성되지 않으므로**.
- ★★★ **Kotlin 과 갈리는 자리가 정확히 여기다.** Kotlin 컴파일러는 널 아님 매개변수에 **검사 코드를 생성**하고,\
  `String` 과 `String?` 을 **타입 시스템에서 다른 타입**으로 다뤄 **에러로 막는다.**\
  C# 은 **명령을 하나도 더하지 않는다.** 같은 물음표 기호가 **다른 종류의 기능**이다.

### 4. ★★ 진단 **0줄** · `cc exit=0` · **`run exit=134`** — `!` 는 **아무것도 검사하지 않는다**

**출력**

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

**왜 그런가**

- ★★★ **진단이 0줄이다.** `!` 가 경고를 **완전히** 지웠다 — 남은 것이 하나도 없다.\
  ★ 「진단이 0줄이다」가 이 문항의 결론이므로 **명령과 `(cc exit=0 · run exit=134)` 까지 담긴 블록**으로 실었다.\
  산문으로 「경고가 안 났다」라고만 적으면 **다시 던질 수 없고, 도구가 못 보는 것과 구분도 안 된다.**
- ★★★ **그리고 `NullReferenceException` 으로 죽었다.**\
  `!` 는 **런타임 검사를 하지 않는다** — 3번에서 본 대로 **IL 에 한 바이트도 안 남는다.**
- ★★ **그러니까 `!` 는 「이 값은 널이 아니다」가 아니라 「경고를 끄겠다」다.**\
  틀리면 **아무 도움 없이 터진다.** 경고를 그냥 무시한 것과 **런타임 결과가 완전히 같다.**
- ★ **차이는 하나뿐이다** — `!` 는 **의도를 남긴다.** 「여기는 내가 확인했다」는 표시다.\
  그래서 **주석으로 근거를 같이 달지 않으면 그 유일한 값마저 사라진다** → 11번.

### 5. ★★ **8번 줄 한 곳**만 경고가 난다

**출력**

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

**왜 그런가**

- 네 줄 중 **`MyCheck(s)` 한 줄만** `CS8602` 가 났다. 나머지 셋은 조용하다.

| 줄 | 코드 | 경고 | 왜 |
|---|---|---|---|
| 7 | `if (s != null)` | 없음 | **언어 규칙**이다. 컴파일러가 직접 안다 |
| 8 | `if (MyCheck(s))` | ★ **`CS8602`** | **메서드 본문을 안 본다.** 바로 옆 줄에 `x != null` 이 있어도 모른다 |
| 9 | `if (!string.IsNullOrEmpty(s))` | 없음 | BCL 에 **`[NotNullWhen(false)]`** 가 붙어 있어 안다 |
| 10 | `if (MyCheckAttr(s))` | 없음 | ★ **내 헬퍼에 `[NotNullWhen(true)]`** 를 붙였더니 안다 |

- ★★★ **널 상태는 「타입」이 아니라 「이 지점의 상태」다.** 메서드 호출을 하나 건너면 **상태가 초기화된다.**\
  분석은 **메서드 하나 안에서만** 흐르고, 경계를 넘는 정보는 **오직 특성으로만** 전달된다.
- ★★ **그래서 「분석이 틀린다」는 말은 정확하지 않다** — **모르는 것이고, 알려 주면 안다.**
- **고치는 세 방법과 순위**
  1. ★★★ **특성을 붙인다**(`[NotNullWhen(true)]`) — **유일하게 모든 호출자에게 전달되는** 고침이다.
  2. **검사를 인라인한다**(`if (s != null)`) — 확실하지만 헬퍼의 뜻이 사라진다.
  3. ★ **`!` 로 끈다** — **호출자마다 반복해야 하고 근거가 안 남는다.** 최후 수단이다.
- ★ 특성 목록 — `[NotNull]` · `[MaybeNull]` · `[NotNullWhen]` · `[MaybeNullWhen]` · `[NotNullIfNotNull]` ·\
  `[DoesNotReturn]` · `[DoesNotReturnIf]` · `[MemberNotNull]` · `[MemberNotNullWhen]`.\
  **이 문서는 `[NotNullWhen(true)]` 하나만 던졌다.**

### 6. ★ **`A` 와 `C` 둘**에 경고가 나고 `B` 는 조용하다

**출력**

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

**왜 그런가**

- **7번 줄이 `A`, 11번 줄이 `C`** 다. `#nullable disable` 구간의 `B` 는 **같은 역참조인데 조용하다.**
- ★★ **맥락은 플래그가 둘이다.**

| 지시어 | 주석 플래그 | 경고 플래그 | 이 블록에서 |
|---|---|---|---|
| `#nullable enable` | 켬 | 켬 | `A` — `string?` 이 뜻을 갖고 경고도 난다 |
| `#nullable disable` | 끔 | 끔 | `B` — 분석이 통째로 꺼진다 |
| `#nullable enable warnings` | 프로젝트 설정 | 켬 | `C` — `?` 없이도 **분석 경고만** 난다 |
| `#nullable restore` | 프로젝트 설정 | 프로젝트 설정 | 되돌리기 |

- ★ `enable`/`disable`/`restore` 셋에 `annotations`·`warnings` 를 붙여 **아홉 조합**이 된다.\
  **이 기능의 원래 목적이** 「**큰 코드베이스를 조금씩 옮기는 것**」이라 이렇게 잘게 쪼개 놓은 것이다.
- ★★★ **분석이 통째로 꺼지는 파일이 있다** — **생성된 코드**다.\
  `<auto-generated>` 주석이 있거나 `*.g.cs`·`*.generated.cs`·`*.designer.cs` 로 끝나거나\
  `.editorconfig` 에서 `generated_code = true` 인 파일에는 **전역 맥락이 적용되지 않는다.**\
  ★ 「프로젝트를 켰으니 전부 검사된다」가 여기서 틀린다.

### 7. 같은 번호가 **`error` 로 바뀌고 `cc exit` 이 1** 이 된다

**출력**

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

**왜 그런가**

- ★★ **진단 내용이 한 글자도 안 바뀌었다** — `CS8600`·`CS8602` 그대로이고 `(행,열)` 도 같다.\
  **`warning` 이 `error` 로 바뀌고 `cc exit` 이 0 에서 1 로 갔을 뿐**이다.
- MSBuild 에서 **널 경고만** 올리는 속성은 **`<WarningsAsErrors>Nullable</WarningsAsErrors>`** 다.\
  (`<TreatWarningsAsErrors>` 는 모든 경고를 올린다 — 실무에서는 앞엣것을 많이 쓴다.)
- ★★★ **그래도 Kotlin 과 같아지지 않는 이유 둘 — 그리고 덤 하나**
  1. ★ **`!` 가 여전히 통한다**(4번) — 에러가 아니라 **경고 자체가 사라지므로** `-warnaserror` 가 잡을 것이 없다.
  2. ★ **라이브러리 경계에서 샌다** — 맥락을 안 켠 어셈블리에서 오는 값은 `not-null` 로 들어온다.\
     **내 설정은 내가 컴파일한 코드에만 걸린다**([05번](../05-numeric-types-checked-decimal/)의 `-checked+` 와 같은 집안이다).
  3. ★ 덧붙여 **생성 코드가 통째로 빠진다**(6번).

### 8. **메타데이터 특성**에 남는다 — 그리고 **모든 멤버에 붙지는 않는다**

**출력**

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

**왜 그런가**

- `string?` 이 런타임 타입이 아니므로, 다른 어셈블리가 읽으려면 **어딘가에 따로 적어 둬야** 한다.\
  그 자리가 **`NullableAttribute` / `NullableContextAttribute`** 다.
- ★★ **붙는 기준이 「기본값에서 벗어난 것만」이다.**\
  타입 `Box` 에 `NullableContextAttribute((Byte)1)` 이 붙어 「**이 타입 안의 기본은 널 아님**」을 선언하고,\
  거기서 벗어나는 `Maybe` 필드와 `b` 인자에만 `NullableAttribute((Byte)2)` 가 붙었다.\
  **`NotNull` 필드와 `a` 인자에는 아무것도 없다** — 메타데이터를 아끼는 설계다.
- ★ **어셈블리 수준에는 아무것도 없다.** 정보는 **타입·멤버·인자 단위**로 산다.
- ★★★ **「런타임 동작이 안 바뀐다」가 거짓이 되는 라이브러리 — Entity Framework Core** 다.\
  Learn 이 못 박은 대로 EF Core 는 이 특성을 **리플렉션으로 읽어**\
  「널 허용 참조 = 선택(nullable) 열, 널 아님 = 필수(required) 열」로 스키마를 만든다.\
  ★ 그러니까 **「런타임 동작이 안 바뀐다」는 언어 차원의 말**이고,\
  **메타데이터를 읽는 라이브러리는 실제로 다르게 행동한다.** 둘을 갈라 읽어야 한다.\
  같은 성격의 소비자가 더 있다 — **직렬화기·검증기·소스 생성기**.

### 9. ★★★ **넷은 막히고 하나는 통과한다** — 문서의 목록이 이 판에서 갈렸다

**출력**

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

**기반 타입은 선언 단계 에러라 파일이 통째로 막힌다 — 따로 던졌다.**

```text
===== 소스: cs06b-base.cs =====
#nullable enable

System.Console.WriteLine("컴파일까지 못 간다");

public class Derived : System.Object? { }
===== csc -out:ex.dll cs06b-base.cs (cc exit=1) =====
cs06b-base.cs(5,24): error CS1521: Invalid base type
```

**왜 그런가**

| 쓴 것 | 진단 | 왜 |
|---|---|---|
| `System.String?.Empty` | ``CS0119`` + ``CS0176`` | ★ **`?.` 로 파싱돼 버린다** — 타입 이름 뒤의 `?` 는 널 조건 연산자다 |
| `new object?()` | ``CS8628`` | 런타임에 인스턴스를 만드는 자리다 |
| `t is string? ns` | ``CS8116`` | ★ **런타임 타입 검사**라 `string` 과 구분할 것이 없다 |
| `class D : System.Object?` | ``CS1521`` | 런타임 타입 계층에 들어가는 자리다 |

- ★★★ **외우지 말고 한 줄로 유도하라** — **`string?` 은 타입이 아니라 주석**이다(3번).\
  **타입이 와야 하는 자리에는 주석을 붙일 자리가 없다.**
- ★★ **Kotlin 이었다면 이 중 여럿이 된다** — 거기서는 `String?` 이 **진짜 타입**이라 `is String?` 이 뜻을 갖는다.\
  **금지 목록이 기능의 성격을 드러내는** 자리다.

★★★ **그런데 Learn 의 목록에 하나가 더 있고, 그것은 이 판에서 통과했다.**

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

- ★★★ [Learn 의 널 허용 참조 형식 문서](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/builtin-types/nullable-reference-types)는\
  ``catch (Exception? e)`` 를 「not Allowed」로 적어 두었다.\
  **Roslyn 10.0.401 은 진단을 0줄 내고**(`cc exit=0`) **예외를 정상으로 잡았다**(`run exit=0`).
- ★★★ 「문서에 금지라고 적혀 있다」는 **돌려 본 것이 아니다.**\
  [05번](../05-numeric-types-checked-decimal/)의 **포화 변환**과 같은 집안의 사례가 **이 배치에서 두 번째로 나왔다.**
- ★★ 다만 **「통과한다」와 「써도 된다」는 다른 말**이다 — `?` 가 아무 뜻이 없어 **쓸 이유가 없고**,\
  위 예제도 결국 `ex!` 를 써야 했다.

### 10. ★★ **같은 기호, 다른 기능이다** — `int?` 만 런타임에 존재한다

**답**

| | `string?`(널 허용 **참조** 타입) | `int?`(널 허용 **값** 타입) |
|---|---|---|
| 런타임 타입 | ★ **`System.String`** — `?` 가 없다 | ★ **`System.Nullable<System.Int32>`** — 진짜 구조체다 |
| 생기는 것 | **주석(메타데이터)** 만 | ★ **타입 하나**(`HasValue`·`Value` 를 든 구조체) |
| 크기 | 안 바뀐다(참조 8바이트) | ★ **`int` 4바이트 → `int?` 8바이트** |
| 언제부터 | **C# 8** | **C# 2** |
| 끄고 켜기 | ★ **맥락으로 끌 수 있다** | ★ **못 끈다** — 언어 기능이다 |
| 검사 코드 | ★ **생성 안 됨** | ★ **생성됨**(리프티드 연산자) |
| 위반하면 | **경고**(`CS8602`) | ★ **컴파일 에러**(`int x = maybeInt;` 는 안 된다) |

- ★★★ **정본은 [08번](../08-nullable-value-types/)** 이다. 거기서 `Nullable<T>` 가 **`struct` 라는 것**부터 다룬다.
- **`where T : struct` 를 건 제네릭에서 `T?` 는 `Nullable<T>`** 가 된다.\
  제약이 없으면 값 타입 인자에는 **아무 효과가 없다**(`Box<int>` 의 `T?` 는 그냥 `int`).
- ★★ **두 물음표가 같은 코드에서 만나는 자리** — **[07번](../07-null-operators/)의 `?.`** 다.\
  `node?.Count` 에서 **`node` 쪽 `?`(참조, 주석)** 와 **결과 타입 `int?`(값, 진짜 타입)** 가 한 식에 같이 나온다.\
  ★ **그 한 줄이 06 → 07 → 08 사슬을 잇는다.**

### 11. **외부 계약을 내가 아는 자리**에만 — 그리고 근거를 주석으로 남긴다

**답**

- **`!` 를 써도 되는 자리 셋**
  1. ★ **테스트 코드** — `Assert` 뒤라 널이 아님을 아는 자리.
  2. ★ **특성이 없는 옛 API 뒤** — `TryGetValue` 같은 패턴에서 `true` 를 확인한 뒤의 `out` 변수.
  3. ★ **프레임워크가 채우는 필드** — 직렬화기·DI 컨테이너가 리플렉션으로 넣어 주는 것(`default!` 관용구).
- **경고가 떴을 때의 올바른 순서**
  1. **진짜 널일 수 있나 확인한다** — 대개 여기서 설계 문제가 나온다.
  2. **검사를 넣거나 설계를 고친다**(널이 안 오게 만든다).
  3. **특성을 붙인다**(5번) — 헬퍼가 원인이면 이것이 정답이다.
  4. ★ **최후에 `!`** — 그리고 **왜 안전한지 주석을 단다.**
- ★★★ **`!` 가 남기지 못하는 것은 「이유」다.** 다음 사람은 `!` 만 보고\
  **「확인하고 붙인 것」인지 「경고를 끄려고 붙인 것」인지 구분할 수 없다.**
- ★★ **`!` 를 습관적으로 쓰기 시작하면 이 기능 전체가 무의미해진다** —\
  `!` 는 경고를 **완전히** 지우므로(4번) `-warnaserror` 도 잡지 못한다.

### 12. 다른 언어와 잇기

- **Kotlin** — [널 안전 타입 편](../../../kotlin/syntax/03-null-safe-types/). **결정적으로 다른 점 둘**
  1. ★★★ **타입 시스템이다** — `String` 과 `String?` 이 **서로 다른 타입**이라 컴파일러가 **에러로 막는다.**
  2. ★★★ **검사 코드를 생성한다** — 널 아님 매개변수에 런타임 검사가 들어간다.\
     C# 은 **명령을 하나도 안 더한다**(3번).
- **TypeScript** — [`any`·`unknown`·`never`·`void` 편](../../../ts/syntax/04-any-unknown-never-void/).\
  ★★ **이쪽이 훨씬 가깝다.** `strictNullChecks` 도 **컴파일 시점에만 살고**,\
  `!` 에 해당하는 비-널 단언(`x!`)도 있고, **지우고 나면 런타임에 아무것도 안 남는다.**\
  ★ 차이는 **C# 은 메타데이터를 남긴다**는 것이다(8번) — TS 는 `.d.ts` 라는 **별도 파일**로 남긴다.
- **Java** — [원시 타입과 래퍼 편](../../../java/syntax/01-primitives-and-wrappers/).\
  Java 에는 이 문법이 없고 `Optional<T>` 나 `@Nullable` 애너테이션으로 우회한다.\
  ★★ **`Optional` 은 객체를 하나 더 만든다** — **힙 할당이 생긴다**([03번](../03-boxing-and-unboxing/)).\
  C# 의 주석은 **할당이 0**이고(3번), `int?` 도 **구조체라 힙을 안 쓴다**([08번](../08-nullable-value-types/)).\
  ★ **같은 문제에 세 언어가 준 답의 비용이 전부 다르다.**
- ★★★ **C# 이 에러가 아니라 경고로 만든 이유는 역사다.**\
  에러로 만들었으면 C# 8 로 올리는 순간 **세상의 모든 프로젝트가 빌드에 실패했을 것**이다.\
  Kotlin 은 **새 언어라 처음부터 그렇게 설계할 수 있었다.**\
  ★ **기술의 차이가 아니라 「언제 태어났나」의 차이**인 자리다.

## 실행 검증

**무엇을 몇 번 어느 판에서 돌렸나** — 아래 블록은 전부 **.NET SDK 10.0.401 / 런타임 10.0.12 / `net10.0` / linux-x64** 에서\
캡처 스크립트로 받았다. **제출 직전에 전부 다시 돌려 정규화 대조했다.**

| 블록 | 무엇을 고정하나 | 명령 |
|---|---|---|
| `cs06b-warn.cs` | `CS8600`·`CS8602` · `cc exit=0` · `run exit=134` | `csc` + 실행 |
| 〃 (`-warnaserror`) | ★ **같은 번호가 `error` 로, `cc exit=1`** | `csc -warnaserror` |
| `cs06b-nowarn.cs` | `CS8632` 하나 · ★ **실행 결과가 같은 것** | `csc` + 실행 |
| 〃 (`-nullable:enable`) | ★ 소스를 안 고치고 플래그로 켠 것 | `csc -nullable:enable` |
| `cs06b-il.cs` | ★★★ **IL 8줄이 동일** · 매개변수 타입 `System.String` · `NullableContextAttribute` 1 대 2 | `csc -r:il.dll` + 실행 |
| `cs06b-meta.cs` | `NullableAttribute((Byte)2)` 가 **벗어난 것에만** 붙는 것 | `csc` + 실행 |
| `cs06b-directive.cs` | ★ 구간별 경고(`A`·`C` 만) | `csc` 만 |
| `cs06b-bang.cs` | ★★★ **진단 0줄** · `run exit=134` | `csc` + 실행 |
| `cs06b-flow.cs` | ★★ **네 줄 중 8번 줄 하나만** 경고 | `csc` 만 |

**구현(Roslyn)에 달린 항목** — 다음은 **이 컴파일러 판에서만** 그렇다.

- ★★ **어떤 코드에서 경고가 나고 안 나는가의 정확한 경계**(5번) — **흐름 분석이 개선되면 움직인다.**\
  ★ 「지금 경고가 안 난다」가 「안전하다」가 **아니다.**
- **경고 문구와 `(행,열)`** · **`NullableContextAttribute` 의 바이트값 1·2** ·\
  **특성을 「기본값 + 예외」로 배치하는 방식**(8번).
- **IL 의 `nop`** — `-optimize` 를 안 준 결과다(**이 문서는 안 켰다**). 켜면 사라지지만 **두 덤프가 같은 것은 안 바뀐다.**
- **`NullReferenceException` 의 메시지 문구**·**종료 코드 134**.

**언어가 보장하는 것**(구현이 바뀌어도 같다)

- **`string?` 과 `string` 이 같은 .NET 타입**인 것.
- **널 허용 주석이 런타임 동작을 바꾸지 않는** 것 — 널 검사가 **생성되지 않는다.**
- **기본이 경고이지 에러가 아닌** 것 · **`!` 가 경고만 끄는** 것.
- **맥락에 주석·경고 두 플래그가 있고 지시어로 구간을 가를 수 있는** 것.
- **`?` 를 기반 타입·`new`·`is`·`catch`·멤버 접근 대상에 쓸 수 없는** 것.
- **생성된 코드 파일에 전역 맥락이 적용되지 않는** 것.

**안 돌려 본 것 / 못 잰 것**

- **안 돌려 본 것** — **`CS8618`**(생성자에서 널 아님 필드 미초기화)과 `required`·`init` 의 상호작용(목록의 **13번 주제**) ·\
  **`[MemberNotNull]`·`[NotNullIfNotNull]`** · **제네릭에서의 `T?` 와 `where T : class?`·`notnull`**(목록의 **25번 주제**) ·\
  **`default!` 관용구** · **생성 코드 파일에서 맥락이 꺼지는 것**(Learn 의 서술로만 안다 — **직접 안 던졌다**) ·\
  **EF Core 가 특성을 읽는 것**(Learn 의 서술로만 안다 — **직접 안 던졌다**) · **`.editorconfig` 의 `generated_code`**.
- **못 잰 것** — ★★ **「이 분석이 실제로 널 사고를 몇 % 막나」.**\
  그것은 코드베이스 통계이지 컴파일러 실험이 아니다. 이 문서가 보인 것은 **무엇이 갈리고 무엇이 안 갈리나**뿐이다.
- ★ **할당 바이트는 「안 잰 것」이 아니라 「잴 것이 없는 것」이다** — 3번이 그 근거다. 둘을 갈라 적는다.

**버전이 올랐을 때 다시 돌려야 하는 것**

- ★★★ **5번의 네 줄** — **흐름 분석이 가장 자주 바뀌는 자리**다. 경고가 줄어들 수 있다.
- ★★ **3번의 IL 두 덤프** — Roslyn 이 바뀌면 명령이 움직일 수 있다.\
  **다만 「둘이 같다」는 언어가 보장하는 것**이라 안 바뀐다. **무엇이 근거인지 갈라 읽어라.**
- ★ **8번의 특성 배치** — 메타데이터 최적화 방식이 바뀌면 붙는 자리가 움직인다.
