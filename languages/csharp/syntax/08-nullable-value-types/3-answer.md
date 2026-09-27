# csharp/syntax/08 — 널 허용 값 타입 `Nullable<T>` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> **기준 소스** — [ECMA-334 7판(2023-12)](https://ecma-international.org/publications-and-standards/standards/ecma-334/) · [Microsoft Learn — C# 언어 레퍼런스](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/) · [Learn — `checked`/`unchecked`](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/statements/checked-and-unchecked) · [Learn — 널 허용 값 형식](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/builtin-types/nullable-value-types) · [Learn — 널 허용 참조 형식](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/builtin-types/nullable-reference-types) · [Learn — 멤버 접근·널 조건 연산자](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/operators/member-access-operators)
> **실행 검증** — 이 문서의 모든 출력·진단·IL·할당 바이트는 **.NET SDK 10.0.401** ·\
> 런타임 **`.NET 10.0.12`**(`Microsoft.NETCore.App`) · 타겟 **`net10.0`** · **linux-x64** 에서 실제로 돌려 얻은 것이다(2026-09-25).\
> ★ 블록은 캡처 스크립트가 파일로 받아 조립기가 끼워 넣은 것이다 — 사람이 옮겨 적은 줄은 하나도 없다.\
> ★ 소스 펜스의 첫 줄(`// cs0Nb-….cs` 꼴)도 **캡처가 찍은 것**이다. 원고에 손으로 쓴 배너는 없다.
> **읽는 법** — ★★★ **할당 바이트는 증분만 근거로 쓴다.** 절댓값(프로세스 누적)은 흔들리는 칸이고\
> 이 문서는 **한 번도 싣지 않았다.** 더 중요한 것은 **0 이냐 아니냐**다 — 4번이 거기 달렸다.\
> ★★ **8번에서는 IL 을 근거로 쓰지 않는다** — 이 배치에서 **IL 이 지는 유일한 자리**다.\
> ★ **`cc exit` 과 `run exit` 을 갈라 적었다.**\
> 자세한 환경과 던진 형태는 [2-summary.md](2-summary.md)의 머리말·(0)절에 있다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★ **구조체**다 — `System.ValueType` 을 상속하고 `is null` 이 된다

**출력**

```text
===== 소스: cs08b-struct.cs =====
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
===== csc -out:ex.dll cs08b-struct.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
typeof(int?)                          = System.Nullable`1[System.Int32]
typeof(int?) == typeof(Nullable<int>) : True
typeof(int?).IsValueType              : True
typeof(int?).BaseType                 = System.ValueType
Nullable.GetUnderlyingType(typeof(int?)) = System.Int32
Nullable.GetUnderlyingType(typeof(int))  = (null)

none.HasValue            : False
some.HasValue            : True   some.Value = 5
none.GetValueOrDefault() : 0
none.GetValueOrDefault(9): 9
default(int?) is null    : True
none is null             : True   ← 참조가 아닌데 is null 이 된다
some is int unwrapped    : True (unwrapped=5)
none.ToString()          : '' (길이 0)
none.Equals(null)        : True
none.GetHashCode()       : 0
```

**왜 그런가**

- ★★★ **`typeof(int?)` 가 ``System.Nullable`1[System.Int32]``** 다 — **`int?` 는 축약 표기**다.\
  `typeof(int?) == typeof(Nullable<int>)` 가 `True` 인 것이 그 확인이다.
- ★★★ **`IsValueType` 이 `True`, `BaseType` 이 `System.ValueType`** — **구조체다.**\
  ★ 「`null` 을 담는데 값 타입」이 이 주제의 핵심 긴장이고, 나머지 결론이 전부 여기서 나온다.
- **`Nullable.GetUnderlyingType(typeof(int))` 은 `(null)`** 이다.\
  ★ **널 허용이면 기반 타입을, 아니면 널을 준다** — 이것이 판별의 정식 방법이다(5번에서 왜 다른 방법이 안 되는지 나온다).
- ★★ **`none is null` 이 `True`** 다 — **참조가 아닌데 된다.**\
  컴파일러가 이것을 **`!none.HasValue`** 로 바꾸기 때문이다(8번의 `IsNull` IL 이 그 증거다).
- ★ **`none.ToString()` 의 길이가 0** 이다 — **빈 문자열**이지 `"null"` 이 아니다.\
  [07번](../07-null-operators/)의 (6)에서 본 함정이 여기서 설명된다.
- ★ **`none.Equals(null)` 이 `True` 이고 `none.GetHashCode()` 가 `0`** 이다 —\
  ★★ **널인 `int?` 도 사전 키로 쓸 수 있다.** 참조 널이었으면 `GetHashCode` 를 부르다 터졌을 것이다.

### 2. ★ 증가폭이 **정렬**에 달렸다 — `int` 4 → `int?` **8**

**출력**

```text
===== 소스: cs08b-size.cs =====
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
===== csc -out:ex.dll cs08b-size.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
bool       1바이트  →  bool?      2바이트   (+1)
byte       1바이트  →  byte?      2바이트   (+1)
char       2바이트  →  char?      4바이트   (+2)
short      2바이트  →  short?     4바이트   (+2)
int        4바이트  →  int?       8바이트   (+4)
long       8바이트  →  long?     16바이트   (+8)
double     8바이트  →  double?   16바이트   (+8)
decimal   16바이트  →  decimal?  24바이트   (+8)
Guid      16바이트  →  Guid?     20바이트   (+4)
```

**왜 그런가**

| 타입 | 원래 | `T?` | 증가폭 | 왜 |
|---|---|---|---|---|
| `bool`·`byte` | 1 | 2 | **+1** | 정렬 요구가 1이라 `bool hasValue` 한 바이트만 붙는다 |
| `char`·`short` | 2 | 4 | **+2** | 2바이트 정렬 |
| `int` | 4 | 8 | **+4** | 4바이트 정렬 — ★ **1바이트만 늘 것 같지만 두 배가 된다** |
| `long`·`double` | 8 | 16 | **+8** | 8바이트 정렬 |
| `decimal` | 16 | 24 | **+8** | 내부가 `int` 넷이라 정렬은 8 |
| `Guid` | 16 | 20 | ★ **+4** | ★ `Guid` 의 정렬 요구가 4다(내부가 `int`+`short`×2+`byte`×8) |

- ★★★ **그래도 힙을 안 쓴다.** 이 바이트가 **스택이나 포함 객체 안에** 그대로 있다.\
  Java 의 `Integer` 는 **참조 8바이트 + 힙 객체 16바이트 이상**이다 — **그림이 완전히 다르다**(12번).
- ★ **`sizeof(int?)` 는 컴파일 에러**다.

```text
===== 소스: cs08b-sizeof.cs =====
using System;

Console.WriteLine(sizeof(int?));
===== csc -out:ex.dll cs08b-sizeof.cs (cc exit=1) =====
cs08b-sizeof.cs(3,19): error CS0233: 'int?' does not have a predefined size, therefore sizeof can only be used in an unsafe context
```

- **`error CS0233`** — `sizeof` 의 **`unsafe` 없는 판은 내장 타입만** 받는다.\
  ★ [01번](../01-value-types-and-reference-types/)의 `sizeof(Point)` 가 받은 **같은 진단**이다.\
  안전한 대안이 **`Unsafe.SizeOf<T>()`** 이고, 위 표가 그것으로 잰 것이다.

### 3. **`InvalidOperationException`** 이다 — `NullReferenceException` 이 아니다

**출력**

```text
===== 소스: cs08b-value.cs =====
using System;

int? none = null;
Console.WriteLine(none.Value);
===== csc -out:ex.dll cs08b-value.cs && dotnet ex.dll (cc exit=0 · run exit=134) =====
Unhandled exception. System.InvalidOperationException: Nullable object must have a value.
   at System.Nullable`1.get_Value()
   at Program.<Main>$(String[] args)
```

**왜 그런가**

- ★★★ **`System.InvalidOperationException: Nullable object must have a value.`** 다.
- ★★★ **널 참조 예외가 날 수가 없다** — **참조가 없기 때문**이다(1번).\
  `Value` 는 **구조체의 속성**이고, 그 속성이 `hasValue` 를 보고 **스스로 던진** 것이다.
- **트레이스가 두 줄**이다 — ``at System.Nullable`1.get_Value()`` 와 `at Program.<Main>$(String[] args)`.\
  ★ `-debug` 를 안 줬는데도 **BCL 프레임의 이름은 나온다**(메서드 이름은 메타데이터에 있다).\
  없는 것은 **파일 경로와 줄 번호**다.
- ★★ **`(int)none` 은 이것과 같은 것**이다 — 명시 캐스트가 `Value` 로 컴파일된다.\
  ★ **캐스트가 더 안전해 보이지만 아니다.** 둘 다 같은 예외를 던진다.
- ★ **예외 타입이 다른 것이 진단에 도움이 된다** — 로그에 `InvalidOperationException: Nullable object must have a value` 가 보이면\
  **널 참조가 아니라** 「**널 허용 값 타입을 잘못 꺼낸 것**」임을 바로 안다.

### 4. ★★★ **`int` 가 박싱된다**(`+24`) — 널이면 **할당이 0이고 널 참조가 된다**

**출력**

```text
===== 소스: cs08b-box.cs =====
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
===== csc -out:ex.dll cs08b-box.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
object = int  (5)    : +24 바이트
object = int? (5)    : +24 바이트   ← int 를 박싱한 것과 같은 수다
object = int? (null) : +0 바이트   ← 아예 할당이 없다

boxedSome is null  : False
boxedNone is null  : True   ← null 참조가 됐다
boxedSome is int   : True
boxedSome is int?  : True
boxedSome.GetType(): System.Int32

(int)boxedSome     : 5
(int?)boxedPlain   : 5   ← 박싱된 int 를 int? 로 언박싱
(int?)boxedNone    : HasValue=False   ← 예외가 아니다
```

**왜 그런가**

- ★★★ **`object = int?(5)` 가 `+24` 바이트로 `object = int(5)` 와 똑같다.**\
  ★ 다만 **숫자만으로는 부족하다** — `Nullable<int>` 도 8바이트라 헤더 16을 더하면 역시 24가 되기 때문이다.\
  **그래서 다음 줄이 결정적이다.**
- ★★★ **`boxedSome.GetType()` 이 `System.Int32`** 다 — **`Nullable<int>` 가 아니다.**\
  **`int` 가 박싱된 것**이 확정된다. **바이트와 타입 둘을 같이 봐야** 증명이 닫힌다.
- ★★★ **`object = int?(null)` 이 `+0` 바이트이고 `boxedNone is null` 이 `True`** 다.\
  **아무것도 만들지 않고 그냥 널 참조가 됐다.**
- ★★★ **그래서 [03번](../03-boxing-and-unboxing/)의 규칙이 여기서 깨진다.**\
  거기서 「값 타입을 `object` 에 넣으면 **매번 새 객체가 생긴다**」를 확정했는데,\
  **`Nullable<T>` 는 그 규칙의 유일한 예외**다 — **널이면 할당이 아예 없다.**\
  ★★ **같은 자(할당 바이트)로 앞 주제를 되받은 것**이 이 문항의 구조다.
- ★★ **`boxedSome is int` 도 `True`, `boxedSome is int?` 도 `True`** 다.\
  ★ **`is` 로는 둘을 구분할 수 없다.** Learn 이 「`is` 를 판별에 쓰지 마라」고 못 박은 이유다(5번).
- **되돌리기는 양방향**이다 — `(int)boxedSome` 도 되고, **박싱된 `int` 를 `(int?)` 로 언박싱**하는 것도 된다.
- ★★ **`(int?)boxedNone` 은 예외가 아니라 `HasValue=False`** 다.\
  **널 참조를 `T?` 로 언박싱하는 것은 합법**이다 — [03번](../03-boxing-and-unboxing/)에서 `(int)null` 이 예외였던 것과 대비된다.
- ★★★ **이것은 구현이 아니라 언어 보장**이다. Learn 이 두 줄로 못 박았다 —\
  **`HasValue` 가 `false` 면 박싱 결과가 널 참조**, **`true` 면 기반 타입 `T` 를 박싱**한다.\
  ★ 그러니 **어느 런타임에서도 같다.** 「+24」만이 이 판의 관찰이다.

### 5. ★★ **`System.Int32`** 를 답하고, **널이면 `NullReferenceException`** 이다

**출력**

```text
===== 소스: cs08b-gettype.cs =====
using System;

int? some = 17;
Console.WriteLine($"some.GetType() = {some.GetType()}   ← Nullable<int> 가 아니다");

int? none = null;
Console.WriteLine(none.GetType());
===== csc -out:ex.dll cs08b-gettype.cs && dotnet ex.dll (cc exit=0 · run exit=134) =====
some.GetType() = System.Int32   ← Nullable<int> 가 아니다
Unhandled exception. System.NullReferenceException: Object reference not set to an instance of an object.
   at System.Object.GetType()
   at Program.<Main>$(String[] args)
```

**왜 그런가**

- ★★★ **`some.GetType()` 이 `System.Int32`** 다.\
  **`GetType()` 은 `object` 의 메서드**라 부르는 순간 **박싱이 일어나고**,\
  4번의 규칙대로 **`int` 가 박싱되므로** 그 객체의 타입이 `Int32` 다.
- ★★★ **`none.GetType()` 은 `NullReferenceException`** 이다.\
  박싱 결과가 **널 참조**라 **부를 대상이 없다.**\
  트레이스의 끝에서 두 번째 줄이 **`at System.Object.GetType()`** 인 것이 그 근거다.\
  ★★ **구조체의 메서드를 불렀는데 널 참조 예외가 나는** 희귀한 자리다 — 3번의 `InvalidOperationException` 과 **다른 예외**다.
- ★★★ **그래서 판별은 `typeof` + `Nullable.GetUnderlyingType`** 이다(1번).

```text
   "이 값이 널 허용 값 타입인가" 를 묻는 세 방법

   x.GetType()                 ✘  박싱이 먼저 일어나 Int32 가 나온다 · 널이면 터진다
   x is int?                   ✘  박싱된 int 도 True 다 (4번)
   Nullable.GetUnderlyingType(typeof(T)) != null   ✔  Type 을 직접 본다 — 박싱이 없다
```

- ★ **핵심은** 「**값이 아니라 `Type` 을 물어야 한다**」는 것이다.\
  값을 거치면 **무조건 박싱을 지나고, 박싱은 널 허용을 지워 버린다.**

### 6. ★★★ **비교 넷이 전부 `false`** 다 — `==` 는 2값이고 정렬은 또 다르다

**출력**

```text
===== 소스: cs08b-lifted.cs =====
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
===== csc -out:ex.dll cs08b-lifted.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
b + c   = 3
a + c   = null
a * c   = null
-a      = null

a == null : True
a == a2   : True   ← 둘 다 null 이면 true 다 (SQL 의 NULL 과 다르다)
a == b    : False
a != b    : True

a >  1 : False
a <= 1 : False   ← 부정이 성립하지 않는다
a <  1 : False
a >= 1 : False
!(a > 1) : True   ← 이것만 true 다

Comparer<int?>.Default.Compare(null, 1) = -1
  ← 정렬은 null 을 「가장 작은 것」으로 본다. 비교 연산자와 규칙이 다르다.

true  & null = null
true  | null = True   ← null 이 섞여도 결과가 난다
false & null = False   ← 〃
false | null = null
!null        = null
```

**왜 그런가**

- **산술은** 「**하나라도 널이면 널**」이다 — `a + c`·`a * c`·`-a` 전부 `null`.\
  `b + c`(둘 다 값)만 `3` 이다. **리프티드 연산자**의 규칙이다.
- ★★ **`a == a2`(둘 다 널)가 `True`** 다.\
  ★★★ **SQL 과 정반대**다 — SQL 의 `NULL = NULL` 은 「모름」인데 **C# 은 널끼리 같다고 본다.**\
  `a == null` 도 `True`, `a == b`(널 대 값)는 `False`, `a != b` 는 `True`. **`==`/`!=` 는 2값이다.**
- ★★★ **`a > 1` · `a <= 1` · `a < 1` · `a >= 1` 이 전부 `False`** 다.\
  **널이 섞이면 무조건 `false`** — 「모름」을 `false` 로 접어 버린다.
- ★★★ **그래서 `!(a > 1)` 만 `True` 다 — 부정이 성립하지 않는다.**\
  `!(a > 1)` 과 `a <= 1` 이 **같지 않다.** 수학에서 참인 항등식이 여기서 깨진다.\
  ★ Learn 이 명시적으로 경고한 자리다 — 「`<=` 가 `false` 라고 해서 `>` 가 `true` 라고 가정하지 마라」.\
  ★★ **`if`/`else` 로 나눈 두 갈래가 널에서 같은 쪽으로 간다** — 이것이 실무 사고다.
- ★★★ **`Comparer<int?>.Default.Compare(null, 1)` 이 `-1`** 이다 — **정렬은 널을 「가장 작은 것」으로 본다.**\
  ★ **모순이 아니라 규칙이 셋인 것**이다.

| 연산 | 널이 섞이면 | 근거 |
|---|---|---|
| `==` · `!=` | **2값** — 널끼리 같다 | 출력의 `a == a2` 가 `True` |
| `<` · `>` · `<=` · `>=` | ★★★ **전부 `false`** | 출력의 넷이 전부 `False` |
| `Comparer<T?>.Default` | ★★ **널이 최소** | 출력의 `-1` |

- ★★ **같은 데이터를 「필터」와 「정렬」에 쓰면 두 규칙이 충돌한다** — 조용히 틀리는 자리다.\
  `Where(x => x.Age > 18).OrderBy(x => x.Age)` 에서 **널은 필터에서 빠지는데 정렬에서는 맨 앞에 온다.**
- ★★ **`bool?` 의 `&`·`|` 는 산술 규칙을 안 따른다** —\
  `true | null` 이 **`True`**, `false & null` 이 **`False`** 다.\
  **한쪽만으로 답이 정해지면 널이 섞여도 결과가 난다** — **SQL 의 3값 논리와 같은 규칙**이다.\
  ★ Learn 이 「이 절의 규칙을 따르지 않는다」고 따로 주를 달아 둔 자리다.\
  ★★ 그런데 **`&&`·`||` 는 `bool?` 에 못 쓴다** — 단락 평가가 「모름」에서 성립하지 않기 때문이다(**이 문서는 안 던졌다**).

### 7. 다섯 가지 — 그리고 **`(int)x` 는 `x.Value` 와 같은 것**이다

**출력**

```text
===== 소스: cs08b-form.cs =====
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
===== csc -out:ex.dll cs08b-form.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
int? none = null        : HasValue=False
int? some = 42          : HasValue=True  Value=42
int? from int (암묵)    : 7
int  from int? (명시)   : 42
?? 로 접지             : -1
GetValueOrDefault()     : 0
GetValueOrDefault(9)    : 9
some is int v           : v=42
none is not int         : 맞다
Nullable<int> 와 int? 는 같은 타입 : True
int?[3] 의 기본값        : [1, null, null]
Nullable.GetUnderlyingType(typeof(int?)) = System.Int32
```

**왜 그런가**

| 방법 | 널일 때 | 언제 쓰나 |
|---|---|---|
| `x.Value` | ★ **`InvalidOperationException`**(3번) | `HasValue` 를 **바로 앞에서** 확인했을 때만 |
| `(int)x` | ★ **같은 예외** — `Value` 로 컴파일된다 | 〃. **캐스트라고 안전한 것이 아니다** |
| `x ?? 기본값` | **기본값** | ★★ 가장 흔한 형태([07번](../07-null-operators/)) |
| `x.GetValueOrDefault()` | **`default(T)`**(`int` 면 `0`) | 기본값이 `default` 로 충분할 때 |
| `x.GetValueOrDefault(9)` | **`9`** | `??` 와 같은 일을 메서드로 |
| `if (x is int v)` | **블록에 안 들어간다** | ★★ **검사와 꺼내기를 한 문장에** — Learn 이 권하는 형태 |

- ★★ **`x ?? 0` 과 `x.GetValueOrDefault()` 는 같은 값**이다.\
  ★ 다만 **`GetValueOrDefault()` 는 「기본값이 무엇인지」가 코드에 안 보인다.** 읽는 쪽에는 `?? 0` 이 낫다.
- ★★★ **`int?[3]` 의 원소 기본값이 전부 널**이다 — `default(int?)` 가 「값 없음」이기 때문이다.\
  **`int[3]` 이었으면 `0` 셋**이다.\
  ★ **「0 과 없음을 구분하고 싶다」가 이 타입을 쓰는 이유**이고, 배열 기본값이 그것을 한 줄로 보인다.
- ★ **`Nullable<int>` 와 `int?` 의 `GetType()` 이 같다** — 같은 타입의 두 표기일 뿐이다.

### 8. ★★ IL 에는 **`box System.Nullable<System.Int32>`** 라고 적혀 있다 — **그리고 그것을 믿으면 틀린다**

**출력**

```text
===== 소스: cs08b-il.cs =====
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
===== csc -r:il.dll -out:ex.dll cs08b-il.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
--- Probe.BoxPlain ---
  IL_0000: ldarg.0
  IL_0001: box System.Int32
  IL_0006: ret
--- Probe.BoxNullable ---
  IL_0000: ldarg.0
  IL_0001: box System.Nullable<System.Int32>
  IL_0006: ret
--- Probe.LiftedAdd ---
  .locals [0] System.Nullable<System.Int32>
  .locals [1] System.Nullable<System.Int32>
  .locals [2] System.Nullable<System.Int32>
  IL_0000: ldarg.0
  IL_0001: stloc.0
  IL_0002: ldarg.1
  IL_0003: stloc.1
  IL_0004: ldloca.s 0
  IL_0006: call System.Nullable<System.Int32>::get_HasValue
  IL_000b: ldloca.s 1
  IL_000d: call System.Nullable<System.Int32>::get_HasValue
  IL_0012: and
  IL_0013: brtrue.s IL_0020
  IL_0015: ldloca.s 2
  IL_0017: initobj System.Nullable<System.Int32>
  IL_001d: ldloc.2
  IL_001e: br.s IL_0034
  IL_0020: ldloca.s 0
  IL_0022: call System.Nullable<System.Int32>::GetValueOrDefault
  IL_0027: ldloca.s 1
  IL_0029: call System.Nullable<System.Int32>::GetValueOrDefault
  IL_002e: add
  IL_002f: newobj System.Nullable<System.Int32>::.ctor
  IL_0034: ret
--- Probe.IsNull ---
  IL_0000: ldarga.s 0
  IL_0002: call System.Nullable<System.Int32>::get_HasValue
  IL_0007: ldc.i4.0
  IL_0008: ceq
  IL_000a: ret
```

**왜 그런가**

- ★★★ **`BoxNullable` 의 명령이 `box System.Nullable<System.Int32>`** 다.\
  **명령만 읽으면 「`Nullable<int>` 를 박싱한다」로 보인다** — 그런데 4번에서 잰 것은 **`int` 박싱**이었다.
- ★★★ **어긋난 것이 아니라 `box` 명령이 `Nullable<T>` 를 특별 취급하는 것**이다.\
  **CLI 가 그렇게 규정했고**, C# 명세도 같은 결과를 규정한다(4번).\
  **틀린 것은 측정이 아니라 「명령 이름이 곧 동작이다」라는 읽기**다.
- ★★★ **그래서 여기가 이 배치에서 IL 이 지는 유일한 자리다.**\
  [05번](../05-numeric-types-checked-decimal/)에서는 IL 이 `checked` 를 확정했고,\
  [06번](../06-nullable-reference-types/)에서는 IL 이 「`string?` 과 `string` 이 같다」를 확정했고,\
  [07번](../07-null-operators/)에서는 IL 이 단락을 확정했다.\
  **여기서는 할당 바이트가 IL 을 이긴다.** ★ **창이 다섯인 이유가 이것이다** — 하나로는 안 된다.
- **`LiftedAdd` 가 리프티드 연산자의 전개다** —\
  `get_HasValue` 둘을 **`and`** 로 묶고, 거짓이면 `initobj`(널), 참이면 **`GetValueOrDefault` 둘을 `add`** 한 뒤 `newobj`.\
  ★★ **`Value` 가 아니라 `GetValueOrDefault` 를 쓴다** — 이미 `HasValue` 를 확인했으니 **예외 검사를 두 번 할 이유가 없다.**\
  ★ 컴파일러가 **예외를 던질 수 없는 경로를 고른 것**이다.
- **`IsNull`(`a == null`)이 `get_HasValue` + `ldc.i4.0` + `ceq`** 다 — **참조 비교가 아니다.**\
  ★ 1번의 「`none is null` 이 `True`」가 이 IL 로 설명된다. **`null` 이라는 글자가 `HasValue` 검사로 바뀐다.**
- ★ **`BoxPlain` 과 `BoxNullable` 이 둘 다 3줄**이다 — **타입 토큰 하나만 다르다.**\
  소스로도 IL 로도 차이가 거의 안 보이고, **나머지는 런타임이 한다.**

### 9. **`CS0266` 하나와 `CS0453` 둘** — 그리고 값 타입은 **에러**다

**출력**

```text
===== 소스: cs08b-forbid.cs =====
using System;

int? maybe = null;
int plain = maybe;                 // 암묵 변환이 없다
Nullable<int?> nested = null;      // 널 허용을 또 감쌀 수 없다
Nullable<string> refType = null;   // 참조 타입은 못 감싼다
Console.WriteLine($"{plain} {nested.HasValue} {refType.HasValue}");
===== csc -out:ex.dll cs08b-forbid.cs (cc exit=1) =====
cs08b-forbid.cs(4,13): error CS0266: Cannot implicitly convert type 'int?' to 'int'. An explicit conversion exists (are you missing a cast?)
cs08b-forbid.cs(5,10): error CS0453: The type 'int?' must be a non-nullable value type in order to use it as parameter 'T' in the generic type or method 'Nullable<T>'
cs08b-forbid.cs(6,10): error CS0453: The type 'string' must be a non-nullable value type in order to use it as parameter 'T' in the generic type or method 'Nullable<T>'
```

**왜 그런가**

| 쓴 것 | 진단 | 왜 |
|---|---|---|
| `int plain = maybe;` | ★ **`error CS0266`** | **진짜 타입이라 변환이 없으면 컴파일이 안 된다** |
| `Nullable<int?> nested` | **`error CS0453`** | `Nullable<T>` 의 제약이 `where T : struct` — `int?` 는 널 아님 값 타입이 아니다 |
| `Nullable<string> refType` | **`error CS0453`** | 참조 타입도 그 제약을 못 넘는다 |

- ★★★ **첫 줄이 이 주제와 [06번](../06-nullable-reference-types/)을 가르는 한 줄이다.**

| | `int x = maybeInt;` | `string s = maybeStr;` |
|---|---|---|
| 진단 | ★ **`error CS0266`** | **`warning CS8600`** |
| 왜 | `int?` 는 **진짜 타입** — 변환 규칙이 막는다 | `string?` 은 **주석** — 분석이 경고할 뿐이다 |
| 빌드 | **실패한다** | **통과한다** |

  ★★ **같은 물음표인데 강제력이 다르다.** 이것이 두 기능 차이의 가장 짧은 요약이다.
- ★ **`int??` 라고 쓰면 진단이 다르다** — **문법 오류**로 먼저 걸린다(`CS1001`·`CS1003`, 파서 단계).\
  `Nullable<int?>` 는 **파싱은 되고 제약에서 걸리므로 `CS0453`** 이다.\
  ★ **같은 「두 번 감싸기」인데 잡히는 단계가 다르다** — 진단 번호가 그것을 말해 준다.

### 10. **「0 과 없음의 구분」 외에** 「**외부 스키마를 그대로 옮기는 것**」이 있다

**답**

- **`T?` 를 쓰는 이유 둘**
  1. ★★ **0 과 없음을 구분해야 할 때** — 7번의 `int?[3]` 이 그 그림이다.
  2. ★★ **외부 스키마가 널을 갖고 있을 때** — **DB 의 `NULL` 열**·JSON 의 생략된 필드·미입력 폼.\
     ★ 여기서는 「구분하고 싶다」가 아니라 「**구분되어 있는 것을 잃지 않고 옮긴다**」가 동기다.\
     EF Core 가 널 허용 값 타입을 **선택 열**로 읽는다([06번](../06-nullable-reference-types/)의 메타데이터 이야기와 같은 집안이다).
- **센티널(`-1`)과 견주면**

| | `int?` | 센티널 `-1` |
|---|---|---|
| 크기 | ★ **두 배**(2번) | 그대로 |
| 안전 | ★★ **컴파일러가 강제한다**(9번) | ★ **아무도 강제하지 않는다** — 문서에 안 적히면 잊힌다 |
| 충돌 | 없다 | ★★ **실제 값이 `-1` 일 수 있으면 조용히 틀린다** |
| 비교 | ★ **3값이라 조심해야 한다**(6번) | 평범하다 |

  ★ **센티널은 「범위에 확실히 여유가 있고 핫한 자리」에서만** 고른다.
- ★★★ **비교가 걸리는 자리에서는 먼저 접지하라** — `(x ?? 0) < 2` 다(6번·[07번](../07-null-operators/)).\
  **`T?` 를 조건식에 날것으로 넣는 것이 이 주제 사고의 대부분**이다.
- **`double?` 의 대안은 `NaN`** 이다 — `double` 은 「없음」을 표현할 수단을 **자체로 갖는다.**\
  ★★ 그 대안의 함정은 **`NaN == NaN` 이 `false`** 라는 것이다([05번](../05-numeric-types-checked-decimal/)).\
  ★ **`double?` 의 3값 비교를 피하려다 `NaN` 의 비반사성으로 옮겨 가는 것**이라, 함정을 바꿀 뿐이다.

### 11. ★★ 06 · 07 과 잇기

**답**

- ★★★ **런타임에 타입이 생기는 쪽은 `int?`** 다.\
  `int?` 는 **`System.Nullable<System.Int32>` 라는 구조체**이고(1번),\
  `string?` 은 **메타데이터의 `NullableAttribute` 한 칸**일 뿐이다([06번](../06-nullable-reference-types/)의 3번).
- ★★★ **그래서 같은 실수의 심각도가 갈린다** — 9번의 표가 그것이다.\
  **값 타입은 에러, 참조 타입은 경고.** 하나는 **변환 규칙**이 막고 하나는 **정적 분석**이 알려 줄 뿐이다.
- ★★★ **[07번](../07-null-operators/)의 `arr?.Length < 2` 는 여기 6번의 규칙으로 설명된다.**\
  `arr?.Length` 가 **`int?`** 이고, **`int?` 의 `<` 는 널이 섞이면 `false`** 다.\
  ★ **그래서 `< 2` 도 `>= 2` 도 `false`** 이고, `if` 가드가 널에서 풀린다.
- ★★ **`?.` 가 값 타입 멤버에서 만드는 것은 정확히 `Nullable<T>`** 다([07번](../07-null-operators/)의 1번).\
  `node?.Count` 의 정적 타입이 `Nullable<Int32>` 인 것이 그것이고,\
  **그 한 줄에 06의 `?`(주석)와 08의 `?`(타입)가 같이 나온다.**
- ★★★ **세 주제가 한 사슬인 이유**

```text
   06번  무엇이 널일 수 있나를 선언한다        string?  = 주석  (컴파일러 분석)
     │                                            ↓ 위반하면 경고
   07번  그러면 어떻게 다루나                    ?. ?? ??=      (연산자)
     │                                            ↓ ?. 의 결과가 값 타입이면
   08번  널을 담는 진짜 타입은 무엇인가          int?     = 타입  (구조체)
                                                  ↓ 위반하면 에러
```

### 12. Java 와 잇기 — **같은 문제에 다른 답**

**답**

| | Java `Integer` | C# `int?` |
|---|---|---|
| 정체 | ★ **객체(참조 타입)** | ★ **구조체(값 타입)**(1번) |
| 메모리 | 참조 8바이트 **+ 힙 객체**(헤더 포함) | ★ **8바이트가 제자리에**(2번) — **힙 없음** |
| `null` | **진짜 널 참조** | ★ **`HasValue == false` 인 값** |
| 널인 채 꺼내면 | **`NullPointerException`** | ★ **`InvalidOperationException`**(3번) |
| `==` | ★★ **참조 비교** — 캐시 범위(대개 −128\~127)에서만 우연히 맞는다 | ★ **값 비교** — 캐시 개념이 없다(6번) |
| `object` 에 넣기 | 이미 객체라 그대로 | ★★★ **`int` 가 박싱되고 널이면 할당 0**(4번) |

- ★★★ **`Integer` 의 `==` 함정이 C# 의 `int?` 에는 없다.**\
  Java 는 `Integer a = 1000, b = 1000; a == b` 가 **`false`** 다(캐시 범위 밖이라 다른 객체).\
  ★ C# 의 `int?` 는 **값 타입이라 `==` 가 값 비교로 컴파일되고**, **캐시라는 것이 존재할 수 없다.**\
  ★★ [03번](../03-boxing-and-unboxing/)에서 본 「**박싱은 캐시하지 않는다**」와 같은 방향의 설계다.
- ★★ **대가는 크기다.** C# 은 「힙을 안 쓰는 대신 4바이트가 8바이트가 되는 것」을 골랐고,\
  Java 는 「크기는 그대로인 대신 객체 하나를 더 만드는 것」을 골랐다.\
  ★ **널 안전의 비용을 어디서 치르나가 갈린다** — [07번](../07-null-operators/)의 12번에서 Kotlin 과 대비한 것과 같은 축이다.
- ★ **Java 에는 `Nullable<T>` 에 해당하는 것이 없다** — 원시 타입에 널을 담으려면 **래퍼로 올려야** 한다.\
  그래서 `int` 와 `Integer` 사이에 **오토박싱**이 끼고, 거기서 또 `NullPointerException` 이 난다.

## 실행 검증

**무엇을 몇 번 어느 판에서 돌렸나** — 아래 블록은 전부 **.NET SDK 10.0.401 / 런타임 10.0.12 / `net10.0` / linux-x64** 에서\
캡처 스크립트로 받았다. **제출 직전에 전부 다시 돌려 정규화 대조했다.**

| 블록 | 무엇을 고정하나 | 명령 |
|---|---|---|
| `cs08b-struct.cs` | ★★ 구조체·`ValueType`·`is null`·`ToString()` 길이 0 | `csc` + 실행 |
| `cs08b-size.cs` | ★ 크기 아홉 벌 — `int` 4→8 · `Guid` 16→20 | 〃 |
| `cs08b-sizeof.cs` | `CS0233` | `csc` 만(`cc exit=1`) |
| `cs08b-value.cs` | `InvalidOperationException` 전문 · `run exit=134` | `csc` + 실행 |
| `cs08b-box.cs` | ★★★ **+24 · +24 · +0** · `GetType()` 이 `Int32` · `(int?)null` 이 합법 | 〃 |
| `cs08b-gettype.cs` | ★★★ 널이면 **`NullReferenceException`**(`at System.Object.GetType()`) | 〃 |
| `cs08b-lifted.cs` | ★★★ 비교 **넷 다 `False`** · `==` 는 2값 · `Comparer` 는 `-1` · `bool?` 논리 | 〃 |
| `cs08b-il.cs` | ★★ **`box Nullable<int>`** · `LiftedAdd` 가 `GetValueOrDefault` 를 쓰는 것 | `csc -r:il.dll` + 실행 |
| `cs08b-form.cs` | 꺼내는 방법 여섯 · `int?[3]` 기본값 | `csc` + 실행 |
| `cs08b-forbid.cs` | ★★ `CS0266` 하나 · `CS0453` 둘 | `csc` 만(`cc exit=1`) |

**구현 의존 항목** — 다음은 **이 환경(.NET 10.0.12 · CoreCLR · x64 linux)에서만** 그렇다.

- ★★ **박싱 +24바이트** — 객체 헤더 16과 최소 객체 크기 24가 x64 CoreCLR 의 값이다([03번](../03-boxing-and-unboxing/)).\
  ★★★ **「+0 이냐 아니냐」는 언어 보장이고 「+24 냐」는 관찰이다.** 갈라 읽어라.
- **크기 8·16·20·24바이트** — 필드 배치와 정렬을 런타임이 정한다.\
  ★ **「`T` 보다 크다」는 성질**이고 **「정확히 얼마」는 관찰**이다.
- **IL 의 명령 열** — `GetValueOrDefault` 를 쓸지 `Value` 를 쓸지는 Roslyn 이 고른다.\
  ★ `-optimize` 를 안 줬다(**이 문서는 안 켰다**).
- **예외 메시지 문구**·**트레이스 형식**·**종료 코드 134**.

**언어가 보장하는 것**(구현이 바뀌어도 같다)

- **`T?` 가 `Nullable<T>` 이고 값 타입(구조체)인** 것 · **`T` 가 널 아님 값 타입이라야 하는** 것.
- **`T` → `T?` 암묵 · `T?` → `T` 명시**이고 널이면 **`InvalidOperationException`** 인 것.
- **리프티드 산술이** 「**하나라도 널이면 널**」인 것.
- **`==`/`!=` 가 2값이고, `<`·`>`·`<=`·`>=` 가 널이 섞이면 `false`** 인 것 · **`bool?` 의 `&`·`|` 가 예외인** 것.
- ★★★ **박싱이 기반 타입 `T` 로 되고, `HasValue` 가 `false` 면 널 참조가 되는** 것.
- **그 귀결로 `GetType()` 이 기반 타입을 주고 널이면 못 부르는** 것 · **`is` 로 `T` 와 `T?` 를 구분할 수 없는** 것.

**안 돌려 본 것 / 못 잰 것**

- **안 돌려 본 것** — **`Nullable<T>` 의 필드 배치**(크기만 쟀다) · **`Nullable.Compare`/`Nullable.Equals` 정적 헬퍼** ·\
  **`bool?` 에 `&&`·`||` 를 쓰는 것**(안 된다는 것을 **던져서 확인하지 않았다**) ·\
  **`where T : struct` 제네릭에서의 `T?`**(목록의 **25번 주제**) · **`Span<T?>` 의 레이아웃** ·\
  **`TryParse(out int? r)` 류의 널 상태 특성** · **32비트 런타임**(크기가 거기서 같은지 **확인 안 했다**) ·\
  **`int?[1_000_000]` 과 `int[1_000_000]` 의 실제 메모리 차이**(계산은 쉬우나 **재지 않았다**).
- **못 잰 것** — ★★ **「`int?` 가 `int` 보다 얼마나 느린가」.**\
  이 문서가 잰 것은 **바이트와 명령**이고 **시간이 아니다.**\
  ★ 그래서 **「느리다」를 한 번도 적지 않았다** — 적은 것은 「**두 배 크다**」와 「**분기가 하나 는다**」뿐이다.
- ★ **12번의 Java 쪽 수치는 던진 것이 아니다** — **Java 갈래의 문서를 참조한 것**이고,\
  이 문서가 실제로 던진 것은 **C# 쪽뿐**이다. 대비의 근거 세기가 **좌우로 다르다.**

**버전이 올랐을 때 다시 돌려야 하는 것**

- ★★ **4번의 +24** — 객체 레이아웃이 바뀌면 움직인다. **`+0` 과 `GetType()` 이 `Int32` 인 것은 안 움직인다.**
- ★★ **2번의 크기 아홉 벌** — 필드 배치가 바뀌면 움직인다. 특히 **`Guid?` 의 20** 이 예민하다.
- ★ **8번의 IL** — Roslyn 이 바뀌면 명령이 움직인다. **`box` 가 `Nullable<T>` 를 특별 취급하는 것은 안 움직인다.**
- ★ **6번** — 전부 언어 규칙이라 **안 움직인다.** 움직이면 그것은 **언어가 바뀐 것**이다.
