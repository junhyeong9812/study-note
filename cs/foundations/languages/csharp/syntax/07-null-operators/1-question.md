# csharp/syntax/07 — 널 관련 연산자 `?.`·`??`·`??=` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> **환경** — .NET SDK **10.0.401** · 런타임 **.NET 10.0.12** · 타겟 **`net10.0`** · linux-x64 ·
> `-langversion:latest`(**C# 14 기능이 켜져 있다** — 6번이 거기 달렸다).
> 진단은 **영어로 고정**했다(`DOTNET_CLI_UI_LANGUAGE=en` + `csc -preferreduilang:en-US`).
> ★★★ **이 주제의 중심 창은 「실행 출력」이다** — 「평가되었나 안 되었나」는 부작용으로만 보인다.
> 프로그램들이 `[평가됨]` 을 찍는데, **안 찍힌 줄이 근거**다.
> ★★ **4번만은 진단이 근거다** — 그리고 **문구가 아니라 「열 번호」를 읽어야 한다.**
> ★ **5번을 직관으로 답하지 마라** — 「둘 중 하나는 참이겠지」가 거기서 깨진다.
> 선행 — [06번](../06-nullable-reference-types/)(왜 `?` 를 붙이나) · [01번](../01-value-types-and-reference-types/).
> 이어짐 — [08번](../08-nullable-value-types/)(1번의 `int?` 와 5번의 비교 규칙이 거기서 설명된다).

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★★ 아홉 식의 정적 타입 (예측)

```csharp
// cs07b-type.cs
#nullable enable
using System;

Node? none = null;
Node some = new Node { Count = 3, Name = "xy" };

Show("none?.Count      ", none?.Count);
Show("some?.Count      ", some?.Count);
Show("some.Count       ", some.Count);
Show("none?.Name       ", none?.Name);
Show("none?.Name?.Length", none?.Name?.Length);
Show("some?.Name!.Length", some?.Name!.Length);
Show("none?.Self()     ", none?.Self());
Show("none?.Count ?? -1", none?.Count ?? -1);
Show("none?.Grade      ", none?.Grade);

static void Show<T>(string label, T v)
    => Console.WriteLine($"{label} → 정적 타입 {Name(typeof(T)),-18} 값 {(v is null ? "(null)" : v.ToString())}");

static string Name(Type t) {
    if (t.IsGenericType && t.GetGenericTypeDefinition() == typeof(Nullable<>))
        return "Nullable<" + t.GetGenericArguments()[0].Name + ">";
    return t.Name;
}

public class Node {
    public int Count;
    public string? Name;
    public char Grade = 'A';
    public Node Self() => this;
}
```

- 아홉 줄의 **정적 타입**을 각각 맞힐 수 있는가?
- `none?.Count` 와 `some?.Count` 의 타입은 **같은가 다른가** — 왜인가?
- `none?.Name` 과 `none?.Self()` 에는 **왜 겹이 안 붙는가**?
- `none?.Count ?? -1` 은?
- ★ 이 타입을 **어떻게 찍었는가** — 값이 널인데 타입을 알아낸 방법은?

### 2. ★★★ 어디까지 건너뛰나 (예측)

```csharp
// cs07b-chain.cs
#nullable enable
using System;

Node? n = null;

int? a = n?.Inner.Count;
Console.WriteLine($"n?.Inner.Count   → HasValue={a.HasValue}  ← 예외 없이 사슬 전체를 건너뛴다");

try {
    Inner? mid = n?.Inner;
    Console.WriteLine(mid.Count);
} catch (NullReferenceException e) {
    Console.WriteLine($"(n?.Inner).Count → {e.GetType().Name}  ← 괄호가 단락을 끊는다");
}

Node? z = null;
z?.Take(Loud("인자 A"));
Console.WriteLine("z 가 null 일 때 '인자 A' 가 찍혔나? ↑");

Node y = new Node();
y?.Take(Loud("인자 B"));

int[]? arr = null;
Console.WriteLine($"arr?[0]  → HasValue={(arr?[0]).HasValue}");
int[]? arr2 = new[] { 7, 8 };
Console.WriteLine($"arr2?[1] → {arr2?[1]}");

static int Loud(string s) { Console.WriteLine($"   [평가됨] {s}"); return 1; }

public class Node {
    public Inner Inner = new Inner();
    public void Take(int k) => Console.WriteLine($"   Take({k}) 실행");
}
public class Inner { public int Count = 5; }
```

- `n?.Inner.Count` 는 **예외인가 값 없음인가**?
- `(n?.Inner).Count` 는?
- ★★ **`[평가됨] 인자 A` 가 출력에 있는가 없는가** — 그것이 무엇을 뜻하는가?
- `arr?[0]` 과 `arr2?[1]` 은?

### 3. `??` 와 `??=` 의 오른쪽은 언제 평가되나 (예측)

```csharp
// cs07b-coalesce.cs
#nullable enable
using System;

string? p = null, q = null;
Console.WriteLine($"p ?? q ?? \"끝\"  = {p ?? q ?? "끝"}");

string? r = null;
r ??= Loud("첫 대입");
r ??= Loud("둘째 대입");
Console.WriteLine($"r = {r}   ← 두 번째 오른쪽은 평가조차 안 됐다");

Console.WriteLine($"Pick() ?? \"기본\" = {Pick() ?? "기본"}");

int? maybe = null;
int fixed1 = maybe ?? -1;
Console.WriteLine($"int? null ?? -1 = {fixed1}  (정적 타입 {Name(fixed1)})");

Box b = new Box();
Console.WriteLine($"b.S 는 {(b.S is null ? "null" : b.S)}");
b.S ??= "채움";
Console.WriteLine($"b.S ??= \"채움\" 뒤 → {b.S}");
b.S ??= "다시";
Console.WriteLine($"b.S ??= \"다시\" 뒤 → {b.S}");

static string Loud(string s) { Console.WriteLine($"   [평가됨] {s}"); return s; }
static string? Pick() { Console.WriteLine("   [평가됨] Pick()"); return null; }
static string Name<T>(T _) => typeof(T).Name;

public class Box { public string? S; }
```

- `[평가됨]` 이 **몇 번** 찍히는가 — 어느 것들인가?
- `r ??= …` 를 두 번 했는데 `r` 은 무엇인가?
- `Pick()` 은 평가되었는가 — 왜인가?
- `int? null ?? -1` 의 **정적 타입**은?

### 4. ★★★ 세 줄의 진단이 가리키는 **열** (예측)

```csharp
// cs07b-assoc.cs
int? x = null;
int y = 2;
int? z = 3;
var q1 = x ?? y ?? z;
var q2 = (x ?? y) ?? z;
var q3 = x ?? (y ?? z);
System.Console.WriteLine($"{q1} {q2} {q3}");
```

- 진단이 **몇 줄** 나고 **각각 몇 행 몇 열**인가?
- 세 진단의 **문구는 같은가 다른가**?
- ★★ **q1 의 열 번호가 무엇을 증명하는가**?
- q1 과 q3 중 **어느 것이 q2 와 같은 식**인가?

### 5. ★★★ 널일 때 비교 두 줄 (예측)

```csharp
// cs07b-trap.cs
#nullable enable
using System;

int[]? numbers = null;

Console.WriteLine($"numbers?.Length 는 값이 있나 : {(numbers?.Length).HasValue}");
Console.WriteLine($"numbers?.Length <  2 : {numbers?.Length < 2}");
Console.WriteLine($"numbers?.Length >= 2 : {numbers?.Length >= 2}");
Console.WriteLine($"둘 다 false 다 — 부정이 성립하지 않는다");
Console.WriteLine($"(numbers?.Length ?? 0) < 2 : {(numbers?.Length ?? 0) < 2}   ← ?? 로 접지해야 뜻대로 된다");
Console.WriteLine();

string? s = null;
Console.WriteLine($"s?.Length == 0 : {s?.Length == 0}");
Console.WriteLine($"s?.Length != 0 : {s?.Length != 0}   ← == 와 != 는 3값이 아니다");
Console.WriteLine();

Console.WriteLine($"s?.ToString()      : '{s?.ToString() ?? "(null)"}'");
int? empty = null;
Console.WriteLine($"int? null 의 ToString() : '{empty.ToString()}' (길이 {empty.ToString()!.Length}) ← null 이 아니라 빈 문자열이다");
```

- `numbers?.Length < 2` 와 `numbers?.Length >= 2` 는 각각 무엇인가?
- 그 결과가 **`if` 문에서 무슨 버그**를 만드는가?
- `(numbers?.Length ?? 0) < 2` 는?
- `s?.Length == 0` 과 `s?.Length != 0` 은 — **`<` 와 규칙이 같은가**?
- `int?` 가 널일 때 `ToString()` 은 무엇을 돌려주는가?

### 6. ★ 대입의 왼쪽에 `?.` 를 쓰면 (예측)

```csharp
// cs07b-c14.cs
#nullable enable
using System;

Person? nobody = null;
nobody?.Name = Loud("오른쪽 A");
Console.WriteLine("nobody 가 null 일 때 '오른쪽 A' 가 찍혔나? ↑");

Person somebody = new Person();
somebody?.Name = Loud("오른쪽 B");
Console.WriteLine($"somebody.Name = {somebody.Name}");

int[]? missing = null;
missing?[0] = Count("오른쪽 C");
Console.WriteLine("missing 이 null 일 때 '오른쪽 C' 가 찍혔나? ↑");

int[] present = new int[2];
present?[0] = Count("오른쪽 D");
Console.WriteLine($"present[0] = {present[0]}");

Person? maybe = null;
maybe?.Score += Count("오른쪽 E");
Console.WriteLine("복합 대입도 같다 — '오른쪽 E' 가 찍혔나? ↑");

static string Loud(string s) { Console.WriteLine($"   [평가됨] {s}"); return s; }
static int Count(string s) { Console.WriteLine($"   [평가됨] {s}"); return 1; }

public class Person { public string Name = ""; public int Score; }
```

- `[평가됨]` 이 **몇 번** 찍히는가 — 어느 것들인가?
- 이 문법은 **몇 번째 C# 부터**인가?
- 복합 대입(`+=`)도 되는가? `++` 는?

### 7. ★★ IL 다섯 벌 (왜)

```csharp
// cs07b-il.cs
#nullable enable
Il.Dump(typeof(Probe), "Cond");
Il.Dump(typeof(Probe), "Manual");
Il.Dump(typeof(Probe), "Chain");
Il.Dump(typeof(Probe), "Coalesce");
Il.Dump(typeof(Probe), "Assign");

public static class Probe {
    public static int?   Cond(Node? n)      => n?.Count;
    public static int?   Manual(Node? n)    => n == null ? (int?)null : n.Count;
    public static int?   Chain(Node? n)     => n?.Inner.Count;
    public static string Coalesce(string? s) => s ?? "기본";
    public static void   Assign(Box b)      { b.S ??= "기본"; }
}
public class Node  { public int Count; public Inner Inner = new Inner(); }
public class Inner { public int Count; }
public class Box   { public string? S; }
```

- `Cond` 와 `Manual` 은 **얼마나 다른가**?
- `Chain` 에서 `ldfld` 가 **몇 개**이고 **어느 분기에** 있는가 — 그것이 2번의 무엇을 증명하는가?
- ★★ `Coalesce` 의 **`dup`** 이 무엇을 보장하는가?
- 그 보장이 **어느 관용구**를 성립하게 하는가?

### 8. 못 쓰는 자리 (경계)

```csharp
// cs07b-forbid.cs
#nullable enable

Node? n = null;
int count = n?.Count;          // int? 를 int 에 암묵으로 — 못 한다
string s = n?.Name;            // string? 를 string 에 — 경고만
n?.Count++;                    // 널 조건 접근에 ++ 는 C# 14 에서도 안 된다
System.Console.WriteLine($"{count} {s}");

public class Node { public string? Name; public int Count; }
```

- 네 줄 중 **에러는 몇 개이고 경고는 몇 개**인가?
- ★★ `int count = n?.Count;` 와 `string s = n?.Name;` 이 **왜 심각도가 다른가**?
- `n?.Count++` 의 진단은 무엇이고 **왜 그런가**?

### 9. `?.` 는 예외를 잡는가 (왜)

- `a?.Take(f())` 에서 `a` 가 널일 때 `f()` 는 **실행되는가**?
- `try { a.Take(f()); } catch (NullReferenceException) { }` 와 **무엇이 다른가**?
- `?.` 와 **같은 집안인 연산자** 둘을 댈 수 있는가?

### 10. 언제 쓰고 언제 안 쓰나 (경계)

- `a?.b?.c?.d` 가 널을 돌려줬다. **어디서 끊겼는지 알 수 있는가**?
- `?.` 로 널을 「처리했다」는 말이 정확한가?
- `_cache ??= Build()` 가 **여러 스레드**에서 안전한가?
- `??` 로 기본값을 주는 것과 예외를 던지는 것 중 **무엇을 고르는 기준**은?

### 11. ★★ 06 · 08 과 잇기 (연결)

- `node?.Count` 한 줄에 **두 종류의 물음표**가 나온다 — 각각 무엇인가?
- 그중 **런타임에 존재하는 것**은?
- 1번에서 참조 타입에 겹이 안 붙은 것과 **06번의 어느 사실**이 같은 말인가?
- 5번의 「둘 다 `false`」를 설명하는 정본은 **몇 번 주제**인가?

### 12. 다른 언어와 잇기 (연결)

- Kotlin 에도 `?.` 가 있다 — **결과 타입 규칙**이 같은가?
- TypeScript 의 `?.` 는 트랜스파일 결과에 **무엇을 남기는가** — C# 과 다른가?
- `handler?.Invoke()` 에 해당하는 것이 Java 에 있는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
