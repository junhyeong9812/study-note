# csharp/syntax/08 — 널 허용 값 타입 `Nullable<T>` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> **환경** — .NET SDK **10.0.401** · 런타임 **.NET 10.0.12** · 타겟 **`net10.0`** · linux-x64.
> 진단은 **영어로 고정**했다(`DOTNET_CLI_UI_LANGUAGE=en` + `csc -preferreduilang:en-US`).
> ★★★ **4번이 이 주제의 중심이다** — [03번](../03-boxing-and-unboxing/)의 규칙이 **거기서만 깨진다.**
> 03번의 「+24바이트」를 기억해 두고 오라. **같은 자로 잰다.**
> ★★ **6번을 「둘 중 하나는 참이겠지」로 답하지 마라** — 거기서 직관이 깨진다.
> ★ **8번은 IL 을 믿으면 틀린다** — 이 배치에서 **IL 이 근거로 지는 유일한 자리**다.
> 선행 — [01번](../01-value-types-and-reference-types/)(값 타입) · [03번](../03-boxing-and-unboxing/)(박싱) ·
> [06번](../06-nullable-reference-types/)(참조 타입의 `?`) · [07번](../07-null-operators/)(연산자).
> 대비 — Java 의 [원시 타입과 래퍼 편](../../../java/syntax/01-primitives-and-wrappers/).

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★ `int?` 에게 자기가 무엇인지 물으면 (예측)

```csharp
// cs08b-struct.cs
#nullable enable
using System;

Console.WriteLine($"typeof(int?)                          = {typeof(int?)}");
Console.WriteLine($"typeof(int?) == typeof(Nullable<int>) : {typeof(int?) == typeof(Nullable<int>)}");
Console.WriteLine($"typeof(int?).IsValueType              : {typeof(int?).IsValueType}");
Console.WriteLine($"typeof(int?).BaseType                 = {typeof(int?).BaseType}");
Console.WriteLine($"Nullable.GetUnderlyingType(typeof(int?)) = {Nullable.GetUnderlyingType(typeof(int?))}");
Console.WriteLine($"Nullable.GetUnderlyingType(typeof(int))  = {(Nullable.GetUnderlyingType(typeof(int))?.ToString() ?? "(null)")}");
Console.WriteLine();

int? none = null;
int? some = 5;
Console.WriteLine($"none.HasValue            : {none.HasValue}");
Console.WriteLine($"some.HasValue            : {some.HasValue}   some.Value = {some.Value}");
Console.WriteLine($"none.GetValueOrDefault() : {none.GetValueOrDefault()}");
Console.WriteLine($"none.GetValueOrDefault(9): {none.GetValueOrDefault(9)}");
Console.WriteLine($"default(int?) is null    : {default(int?) is null}");
Console.WriteLine($"none is null             : {none is null}   ← 참조가 아닌데 is null 이 된다");
if (some is int unwrapped) Console.WriteLine($"some is int unwrapped    : True (unwrapped={unwrapped})");
Console.WriteLine($"none.ToString()          : '{none.ToString()}' (길이 {none.ToString()!.Length})");
Console.WriteLine($"none.Equals(null)        : {none.Equals(null)}");
Console.WriteLine($"none.GetHashCode()       : {none.GetHashCode()}");
```

- `typeof(int?)` 는 무엇을 찍는가? `IsValueType` 은? `BaseType` 은?
- `Nullable.GetUnderlyingType(typeof(int))` 는 무엇인가?
- ★★ **`none is null` 이 참인가** — 참조가 아닌데 어떻게 되는가?
- `none.ToString()` 의 **길이**는?
- `none.Equals(null)` 과 `none.GetHashCode()` 는?

### 2. ★ 한 겹이 얼마나 드나 (예측)

```csharp
// cs08b-size.cs
using System;
using System.Runtime.CompilerServices;

Row("bool",  Unsafe.SizeOf<bool>(),  Unsafe.SizeOf<bool?>());
Row("byte",  Unsafe.SizeOf<byte>(),  Unsafe.SizeOf<byte?>());
Row("char",  Unsafe.SizeOf<char>(),  Unsafe.SizeOf<char?>());
Row("short", Unsafe.SizeOf<short>(), Unsafe.SizeOf<short?>());
Row("int",   Unsafe.SizeOf<int>(),   Unsafe.SizeOf<int?>());
Row("long",  Unsafe.SizeOf<long>(),  Unsafe.SizeOf<long?>());
Row("double",Unsafe.SizeOf<double>(),Unsafe.SizeOf<double?>());
Row("decimal",Unsafe.SizeOf<decimal>(),Unsafe.SizeOf<decimal?>());
Row("Guid",  Unsafe.SizeOf<Guid>(),  Unsafe.SizeOf<Guid?>());

static void Row(string name, int bare, int lifted)
    => Console.WriteLine($"{name,-8} {bare,3}바이트  →  {name + "?",-9}{lifted,3}바이트   (+{lifted - bare})");
```

- 아홉 줄의 **증가폭**을 각각 맞힐 수 있는가?
- `byte?` 와 `long?` 의 증가폭이 **왜 다른가**?
- `Guid?` 는 왜 +4 인가?
- ★ `sizeof(int?)` 를 쓰면 어떻게 되는가 — **에러 번호**는?

### 3. `Value` 를 널일 때 읽으면 (예측)

```csharp
// cs08b-value.cs
using System;

int? none = null;
Console.WriteLine(none.Value);
```

- **예외 타입**과 **메시지 전문**은?
- ★★ `NullReferenceException` **이 아닌 이유**는?
- 트레이스에 **몇 줄**이 찍히고 그중 BCL 프레임은 무엇인가?
- `(int)none` 은 이것과 **같은가 다른가**?

### 4. ★★★ `object` 에 넣으면 무엇이 박싱되나 (예측)

```csharp
// cs08b-box.cs
#nullable enable
using System;

Warm();

int plain = 5;
int? some = 5;
int? none = null;

long b0 = GC.GetAllocatedBytesForCurrentThread();
object boxedPlain = plain;
long b1 = GC.GetAllocatedBytesForCurrentThread();
object? boxedSome = some;
long b2 = GC.GetAllocatedBytesForCurrentThread();
object? boxedNone = none;
long b3 = GC.GetAllocatedBytesForCurrentThread();

Console.WriteLine($"object = int  (5)    : +{b1 - b0} 바이트");
Console.WriteLine($"object = int? (5)    : +{b2 - b1} 바이트   ← int 를 박싱한 것과 같은 수다");
Console.WriteLine($"object = int? (null) : +{b3 - b2} 바이트   ← 아예 할당이 없다");
Console.WriteLine();
Console.WriteLine($"boxedSome is null  : {boxedSome is null}");
Console.WriteLine($"boxedNone is null  : {boxedNone is null}   ← null 참조가 됐다");
Console.WriteLine($"boxedSome is int   : {boxedSome is int}");
Console.WriteLine($"boxedSome is int?  : {boxedSome is int?}");
Console.WriteLine($"boxedSome.GetType(): {boxedSome!.GetType()}");
Console.WriteLine();
Console.WriteLine($"(int)boxedSome     : {(int)boxedSome}");
Console.WriteLine($"(int?)boxedPlain   : {((int?)boxedPlain)!.Value}   ← 박싱된 int 를 int? 로 언박싱");
Console.WriteLine($"(int?)boxedNone    : HasValue={((int?)boxedNone).HasValue}   ← 예외가 아니다");

static void Warm() {
    int? w = 1; object a = 1; object? b = w;
    GC.KeepAlive(a); GC.KeepAlive(b);
    GC.GetAllocatedBytesForCurrentThread();
}
```

- **세 줄의 할당 바이트**를 각각 맞힐 수 있는가?
- ★★★ `boxedSome.GetType()` 은 무엇을 답하는가?
- ★★★ `boxedNone is null` 은? 그 줄의 할당은?
- `boxedSome is int` 와 `boxedSome is int?` 는 각각 무엇인가 — **판별에 쓸 수 있는가**?
- `(int?)boxedNone` 은 예외인가 아닌가?
- ★★ 이 결과가 [03번](../03-boxing-and-unboxing/)의 규칙에 무엇을 하는가?

### 5. ★★ `GetType()` 을 부르면 (예측)

```csharp
// cs08b-gettype.cs
using System;

int? some = 17;
Console.WriteLine($"some.GetType() = {some.GetType()}   ← Nullable<int> 가 아니다");

int? none = null;
Console.WriteLine(none.GetType());
```

- `some.GetType()` 은 무엇인가 — **왜 그런가**?
- **`none.GetType()` 은**?
- 트레이스의 **마지막에서 두 번째 줄**은 무엇인가?
- 그렇다면 「이 값이 널 허용 값 타입인가」를 **어떻게 판별하는가**?

### 6. ★★★ 널이 섞인 연산과 비교 (예측)

```csharp
// cs08b-lifted.cs
#nullable enable
using System;

int? a = null, a2 = null, b = 1, c = 2;

Console.WriteLine($"b + c   = {Fmt(b + c)}");
Console.WriteLine($"a + c   = {Fmt(a + c)}");
Console.WriteLine($"a * c   = {Fmt(a * c)}");
Console.WriteLine($"-a      = {Fmt(-a)}");
Console.WriteLine();
Console.WriteLine($"a == null : {a == null}");
Console.WriteLine($"a == a2   : {a == a2}   ← 둘 다 null 이면 true 다 (SQL 의 NULL 과 다르다)");
Console.WriteLine($"a == b    : {a == b}");
Console.WriteLine($"a != b    : {a != b}");
Console.WriteLine();
Console.WriteLine($"a >  1 : {a > 1}");
Console.WriteLine($"a <= 1 : {a <= 1}   ← 부정이 성립하지 않는다");
Console.WriteLine($"a <  1 : {a < 1}");
Console.WriteLine($"a >= 1 : {a >= 1}");
Console.WriteLine($"!(a > 1) : {!(a > 1)}   ← 이것만 true 다");
Console.WriteLine();
Console.WriteLine($"Comparer<int?>.Default.Compare(null, 1) = {System.Collections.Generic.Comparer<int?>.Default.Compare(a, b)}");
Console.WriteLine($"  ← 정렬은 null 을 「가장 작은 것」으로 본다. 비교 연산자와 규칙이 다르다.");
Console.WriteLine();

bool? t = true, f = false, u = null;
Console.WriteLine($"true  & null = {Fmt(t & u)}");
Console.WriteLine($"true  | null = {Fmt(t | u)}   ← null 이 섞여도 결과가 난다");
Console.WriteLine($"false & null = {Fmt(f & u)}   ← 〃");
Console.WriteLine($"false | null = {Fmt(f | u)}");
Console.WriteLine($"!null        = {Fmt(!u)}");

static string Fmt<T>(T? v) where T : struct => v.HasValue ? v.Value.ToString()! : "null";
```

- 산술 네 줄의 결과는?
- `a == a2`(둘 다 널)는 무엇인가 — SQL 과 **같은가**?
- ★★★ `a > 1` · `a <= 1` · `a < 1` · `a >= 1` **넷의 결과**는?
- 그렇다면 `!(a > 1)` 은?
- ★★ `Comparer<int?>.Default.Compare(null, 1)` 은 무엇이고, 그것이 **위 결과와 모순인가**?
- `bool?` 의 `&`·`|` 다섯 줄은?

### 7. 값을 꺼내는 방법들 (경계)

```csharp
// cs08b-form.cs
using System;

int? none = null;
int? some = 42;
int  plain = 7;

Console.WriteLine($"int? none = null        : HasValue={none.HasValue}");
Console.WriteLine($"int? some = 42          : HasValue={some.HasValue}  Value={some.Value}");
Console.WriteLine($"int? from int (암묵)    : {(int?)plain}");
Console.WriteLine($"int  from int? (명시)   : {(int)some}");
Console.WriteLine($"?? 로 접지             : {none ?? -1}");
Console.WriteLine($"GetValueOrDefault()     : {none.GetValueOrDefault()}");
Console.WriteLine($"GetValueOrDefault(9)    : {none.GetValueOrDefault(9)}");

// is 패턴으로 검사와 꺼내기를 한 번에 (Learn 이 권하는 형태)
if (some is int v) Console.WriteLine($"some is int v           : v={v}");
if (none is not int) Console.WriteLine($"none is not int         : 맞다");

// Nullable<T> 와 T? 는 같은 것을 가리킨다
Nullable<int> spelled = 5;
int? shorthand = 5;
Console.WriteLine($"Nullable<int> 와 int? 는 같은 타입 : {spelled.GetType() == shorthand.GetType()}");

// 배열·컬렉션에도 그대로 쓴다
int?[] row = new int?[3];
row[0] = 1;
Console.WriteLine($"int?[3] 의 기본값        : [{string.Join(", ", Array.ConvertAll(row, x => x.HasValue ? x.Value.ToString() : "null"))}]");

// 널 허용 값 타입을 널 허용 값 타입으로 또 감쌀 수는 없다 → 금지 사례에서 던진다
Console.WriteLine($"Nullable.GetUnderlyingType(typeof(int?)) = {Nullable.GetUnderlyingType(typeof(int?))}");
```

- `x.Value` · `(int)x` · `x ?? 기본값` · `x.GetValueOrDefault()` · `is int v` 가 **널일 때 각각 무엇을 하는가**?
- `(int)x` 가 `x.Value` 보다 **안전한가**?
- `int?[3]` 의 원소 기본값은 — `int[3]` 과 무엇이 다른가?

### 8. ★★ IL 은 무엇이라고 적어 놓았나 (왜)

```csharp
// cs08b-il.cs
#nullable enable
Il.Dump(typeof(Probe), "BoxPlain");
Il.Dump(typeof(Probe), "BoxNullable");
Il.Dump(typeof(Probe), "LiftedAdd");
Il.Dump(typeof(Probe), "IsNull");

public static class Probe {
    public static object  BoxPlain(int n)         => n;
    public static object? BoxNullable(int? n)     => n;
    public static int?    LiftedAdd(int? a, int? b) => a + b;
    public static bool    IsNull(int? a)          => a == null;
}
```

- `BoxNullable` 의 박싱 명령에 **어떤 타입 토큰**이 적혀 있는가?
- ★★★ 그것이 4번의 측정과 **어긋나는가** — 어긋난다면 **무엇이 틀린 것인가**?
- `LiftedAdd` 는 `Value` 를 쓰는가 `GetValueOrDefault` 를 쓰는가 — **왜**인가?
- `IsNull`(`a == null`)은 **참조 비교인가**?

### 9. 못 쓰는 자리 (경계)

```csharp
// cs08b-forbid.cs
using System;

int? maybe = null;
int plain = maybe;                 // 암묵 변환이 없다
Nullable<int?> nested = null;      // 널 허용을 또 감쌀 수 없다
Nullable<string> refType = null;   // 참조 타입은 못 감싼다
Console.WriteLine($"{plain} {nested.HasValue} {refType.HasValue}");
```

- 세 줄의 **진단 번호**는?
- ★★★ 첫 줄이 [06번](../06-nullable-reference-types/)의 같은 실수와 **심각도가 어떻게 다른가** — **왜**인가?
- `int??` 라고 쓰면 어떻게 되는가 — `Nullable<int?>` 와 **같은 진단인가**?

### 10. 무엇을 고르나 (경계)

- 「0 과 없음을 구분한다」 말고 `T?` 를 쓰는 **다른 이유**가 있는가?
- 센티널 값(`-1`)을 쓰는 것과 견주면 **무엇을 잃고 무엇을 얻는가**?
- 비교가 걸리는 자리에서는 **무엇을 먼저 해야** 하는가?
- `double?` 에는 왜 대안이 하나 더 있는가 — 그 대안의 함정은?

### 11. ★★ 06 · 07 과 잇기 (연결)

- `string?` 과 `int?` 중 **런타임에 타입이 생기는 쪽**은?
- 같은 실수(`int x = maybe;` / `string s = maybeStr;`)의 **심각도가 왜 갈리는가**?
- [07번](../07-null-operators/)의 `arr?.Length < 2` 가 **여기 어느 규칙**으로 설명되는가?
- `?.` 가 값 타입 멤버에서 만드는 것이 **정확히 무엇**인가?

### 12. Java 와 잇기 (연결)

- Java 의 `Integer` 와 C# 의 `int?` 가 **메모리에서 어떻게 다른가**?
- 널인 채로 꺼내면 **각각 무슨 예외**인가?
- Java 의 `Integer` 에 있는 **`==` 함정**이 C# 의 `int?` 에도 있는가 — 왜인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
