# csharp/syntax/06 — 널 허용 참조 타입(C# 8) — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> **환경** — .NET SDK **10.0.401** · 런타임 **.NET 10.0.12** · 타겟 **`net10.0`** · linux-x64.
> 진단은 **영어로 고정**했다(`DOTNET_CLI_UI_LANGUAGE=en` + `csc -preferreduilang:en-US`).
> ★★★ **이 주제의 창은 컴파일 진단과 IL 둘이다.** 할당 바이트는 **쓸 일이 없다** — 왜인지가 3번의 답이다.
> ★★★ **3번이 이 주제의 본체다.** 거기서 막히면 나머지가 전부 안 풀린다.
> ★★ **「런타임이 막아 준다」로 답하지 마라** — 1번·4번이 그 전제를 직접 뒤집는다.
> 선행 — [01번](../01-value-types-and-reference-types/)(참조 타입) ·
> 짝 — [07번](../07-null-operators/)(연산자) · [08번](../08-nullable-value-types/)(값 타입의 `?`).
> 대비 — Kotlin 의 [널 안전 타입 편](../../../kotlin/syntax/03-null-safe-types/) ·
> TS 의 [`any`·`unknown`·`never`·`void` 편](../../../ts/syntax/04-any-unknown-never-void/).

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★★ 경고가 나면 그다음은 (예측)

```csharp
// cs06b-warn.cs
#nullable enable
using System;

string s = "안녕";
string? t = null;

s = null;                       // ① 널이 될 수 있는 값을 널 아님 타입에
Console.WriteLine(t.Length);    // ② 널일 수 있는 것을 역참조
Console.WriteLine(s);
```

- **진단이 몇 줄** 나고 **번호가 무엇**인가 — 각각 몇 번 줄인가?
- **`cc exit`** 은 몇인가 — 어셈블리가 **만들어지는가**?
- **`run exit`** 은 몇이고 **무엇이 출력되는가**?
- 컴파일러가 경고한 자리와 실제로 터진 자리는 **같은가**?

### 2. `?` 를 빼고 맥락도 안 켜면 (예측)

```csharp
// cs06b-nowarn.cs
using System;

string s = "안녕";
string? t = null;

s = null;
Console.WriteLine(t.Length);
Console.WriteLine(s);
```

- **진단이 몇 줄**이고 번호는?
- `CS8600`·`CS8602` 는 **왜 안 나오는가**?
- **실행 결과는 1번과 같은가 다른가**?

### 3. ★★★ 두 메서드의 IL (예측)

```csharp
// cs06b-il.cs
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
```

- `Plain` 과 `Maybe` 의 IL 덤프는 **각각 몇 줄**이고 **어디가 다른가**?
- `!` 는 IL 에 **몇 바이트**를 남기는가?
- 리플렉션이 답하는 **매개변수 타입**은 각각 무엇인가 — `String?` 이라는 타입이 있는가?
- **메타데이터에서 갈리는 것**은 무엇인가 — 그 값은?
- ★★ 이 결과에서 **따라 나오는 결론 셋**을 댈 수 있는가?

### 4. ★★ `!` 를 붙이면 (예측)

```csharp
// cs06b-bang.cs
#nullable enable
using System;

string? maybe = null;
string sure = maybe!;          // 컴파일러에게 "내가 책임진다"
Console.WriteLine(sure.Length);
```

- **진단이 몇 줄** 나오는가?
- **`cc exit`** 과 **`run exit`** 은?
- `!` 는 **무엇을 검사하는가**?

### 5. ★★ 네 줄 중 몇 줄에 경고가 나나 (예측)

```csharp
// cs06b-flow.cs
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
```

- **몇 번 줄**에 경고가 나는가?
- `MyCheck` 와 `string.IsNullOrEmpty` 는 **무엇이 다른가**?
- `MyCheckAttr` 에 붙은 것이 무엇이고 **왜 그것이 통하는가**?
- 「널 검사를 했는데 경고가 난다」를 고치는 **세 가지 방법**과 그중 **가장 좋은 것**은?

### 6. ★ 구간마다 규칙이 다르면 (예측)

```csharp
// cs06b-directive.cs
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
```

- **세 메서드 중 몇 개**에 경고가 나는가 — 어느 것인가?
- `#nullable enable warnings` 가 `#nullable enable` 과 **무엇이 다른가**?
- 맥락의 **플래그가 몇 개**이고 이름이 무엇인가?
- ★ **분석이 통째로 꺼지는 파일**이 있다 — 어떤 파일인가?

### 7. 경고를 에러로 올리면 (경계)

- `csc -warnaserror` 를 주면 1번의 진단이 **어떻게 바뀌는가** — 번호는? `cc exit` 은?
- MSBuild 에서 **널 경고만** 에러로 올리는 속성은?
- 그렇게 해도 **Kotlin 과 같아지지 않는** 이유 둘을 댈 수 있는가?

### 8. 주석은 어디에 남는가 (왜)

- `string?` 이 런타임 타입이 아니라면 **다른 어셈블리는 그것을 어떻게 아는가**?
- 특성이 **모든 멤버**에 붙는가 — 아니라면 붙는 기준은?
- 「런타임 동작이 안 바뀐다」가 **거짓이 되는 라이브러리**를 하나 댈 수 있는가?

### 9. ★★ Learn 이 「못 쓴다」고 적어 둔 다섯 자리 (경계)

- 기반 클래스 · `new` · `is` 패턴 · `catch` 절 · 멤버 접근의 대상 타입.\
  **던지면 몇 개가 막히는가** — 다섯 전부인가?
- `System.String?.Empty` 의 진단이 **왜 널 관련 번호가 아닌가**?
- ★ 다섯을 **외우지 않고 한 줄로 유도**할 수 있는가?
- Kotlin 이었다면 그중 몇이 됐겠는가?

### 10. ★★ 같은 물음표, 다른 기능 (연결)

- `string?` 과 `int?` 는 **같은 기능인가**?
- 둘 중 어느 쪽이 **런타임에 존재하는 타입**인가?
- `where T : struct` 를 건 제네릭에서 `T?` 는 무엇이 되는가?
- 두 물음표가 **같은 코드에서 만나는** 자리를 하나 댈 수 있는가?

### 11. `!` 를 언제 쓰나 (경계)

- `!` 를 써도 되는 자리 **셋**을 댈 수 있는가?
- 경고가 떴을 때의 **올바른 처리 순서**는?
- `!` 가 남기지 못하는 것은 무엇인가?

### 12. 다른 언어와 잇기 (연결)

- Kotlin 의 널 안전이 이것과 **결정적으로 다른** 점 둘은?
- TypeScript 의 `strictNullChecks` 와는 **어느 쪽이 더 가까운가** — 왜인가?
- Java 의 `Optional` 이 C# 의 주석과 **할당 면에서** 어떻게 다른가?
- C# 이 이것을 **에러가 아니라 경고로 만든 이유**는 기술인가 역사인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
