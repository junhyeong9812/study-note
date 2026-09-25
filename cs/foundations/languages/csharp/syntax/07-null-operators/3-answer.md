# csharp/syntax/07 — 널 관련 연산자 `?.`·`??`·`??=` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> **기준 소스** — [ECMA-334 7판(2023-12)](https://ecma-international.org/publications-and-standards/standards/ecma-334/) · [Microsoft Learn — C# 언어 레퍼런스](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/) · [Learn — `checked`/`unchecked`](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/statements/checked-and-unchecked) · [Learn — 널 허용 값 형식](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/builtin-types/nullable-value-types) · [Learn — 널 허용 참조 형식](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/builtin-types/nullable-reference-types) · [Learn — 멤버 접근·널 조건 연산자](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/operators/member-access-operators)
> **실행 검증** — 이 문서의 모든 출력·진단·IL·할당 바이트는 **.NET SDK 10.0.401** ·\
> 런타임 **`.NET 10.0.12`**(`Microsoft.NETCore.App`) · 타겟 **`net10.0`** · **linux-x64** 에서 실제로 돌려 얻은 것이다(2026-09-25).\
> ★ 블록은 캡처 스크립트가 파일로 받아 조립기가 끼워 넣은 것이다 — 사람이 옮겨 적은 줄은 하나도 없다.\
> ★ 소스 펜스의 첫 줄(`// cs0Nb-….cs` 꼴)도 **캡처가 찍은 것**이다. 원고에 손으로 쓴 배너는 없다.
> **읽는 법** — ★★★ **이 주제의 근거는 「무엇이 안 찍혔나」다.**\
> 프로그램이 `[평가됨]` 을 찍게 만들어 두었으므로, **출력에 없는 줄이 단락의 증거**다.\
> ★ **4번만은 진단이 근거이고, 문구가 아니라 `(행,열)` 을 읽는다.**\
> ★ **`cc exit` 과 `run exit` 을 갈라 적었다.**\
> 자세한 환경과 던진 형태는 [2-summary.md](2-summary.md)의 머리말·(0)절에 있다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ 값 타입 멤버에는 **`Nullable<T>` 한 겹**이 붙고 참조 타입에는 안 붙는다

**출력**

```text
===== 소스: cs07b-type.cs =====
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
===== csc -out:ex.dll cs07b-type.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
cs07b-type.cs(9,27): warning CS8602: Dereference of a possibly null reference.
none?.Count       → 정적 타입 Nullable<Int32>    값 (null)
some?.Count       → 정적 타입 Nullable<Int32>    값 3
some.Count        → 정적 타입 Int32              값 3
none?.Name        → 정적 타입 String             값 (null)
none?.Name?.Length → 정적 타입 Nullable<Int32>    값 (null)
some?.Name!.Length → 정적 타입 Nullable<Int32>    값 2
none?.Self()      → 정적 타입 Node               값 (null)
none?.Count ?? -1 → 정적 타입 Int32              값 -1
none?.Grade       → 정적 타입 Nullable<Char>     값 (null)
```

**왜 그런가**

| 식 | 정적 타입 | 왜 |
|---|---|---|
| `none?.Count` | ★ **`Nullable<Int32>`** | 멤버가 `int`(널 아님 값 타입) → **한 겹** |
| `some?.Count` | ★ **`Nullable<Int32>`** | ★★ **왼쪽이 널이 아니어도 같다** — 타입은 **값과 무관**하다 |
| `some.Count` | **`Int32`** | `?.` 를 안 썼다. **연산자가 타입을 바꾼 것**이다 |
| `none?.Name` | **`String`** | ★ 참조 타입은 이미 널을 담으니 **더 감쌀 것이 없다** |
| `none?.Name?.Length` | **`Nullable<Int32>`** | 마지막 멤버가 `int` 다 |
| `none?.Self()` | **`Node`** | 메서드 반환도 참조 타입이면 그대로 |
| `none?.Grade` | **`Nullable<Char>`** | ★ `int` 만의 규칙이 아니다 — **모든 널 아님 값 타입** |
| `none?.Count ?? -1` | ★★ **`Int32`** | **`??` 가 겹을 벗긴다** |

- ★★★ **타입을 찍은 방법** — 제네릭 메서드 `Show<T>(string, T)` 에 넘기고 **`typeof(T)`** 를 찍었다.\
  `T` 는 **컴파일러가 추론한 정적 타입**이므로 **런타임 값이 널이어도 타입이 나온다.**\
  ★ `v.GetType()` 으로는 **못 한다** — 값이 널이면 부를 대상이 없고,\
  값이 있어도 **박싱 때문에 `Int32` 가 나온다**([08번](../08-nullable-value-types/)).\
  **「정적 타입을 찍는다」와 「런타임 타입을 찍는다」는 다른 실험**이다.
- ★★ **참조 타입에 안 붙는 것이 [06번](../06-nullable-reference-types/)과 같은 말**이다 —\
  `string?` 은 **주석**이라 **런타임 타입 체계에 그런 것이 없고**, `typeof(T)` 가 `String` 을 답한다.\
  반대로 `int?` 는 **진짜 타입**이라 `Nullable<Int32>` 가 나온다. **같은 물음표, 다른 것.**
- ★★★ **`??` 가 겹을 벗기는 것이 실무에서 쓰는 형태**다 — `(x?.Length ?? 0)`. 5번에서 그것이 함정을 고친다.

### 2. ★★★ **사슬 전체를 건너뛴다** — 괄호를 치면 터지고, **인자는 평가조차 안 된다**

**출력**

```text
===== 소스: cs07b-chain.cs =====
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
===== csc -out:ex.dll cs07b-chain.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
cs07b-chain.cs(11,23): warning CS8602: Dereference of a possibly null reference.
n?.Inner.Count   → HasValue=False  ← 예외 없이 사슬 전체를 건너뛴다
(n?.Inner).Count → NullReferenceException  ← 괄호가 단락을 끊는다
z 가 null 일 때 '인자 A' 가 찍혔나? ↑
   [평가됨] 인자 B
   Take(1) 실행
arr?[0]  → HasValue=False
arr2?[1] → 8
```

**왜 그런가**

- ★★★ **`n?.Inner.Count` 는 예외가 아니라** 「**값 없음**」이다(`HasValue=False`).\
  `n` 이 널이면 **`.Inner` 도 `.Count` 도 평가하지 않는다** — `?` 하나가 **사슬 전체를 덮는다.**\
  ★ 그래서 **`a` 만 널일 수 있고 나머지는 아니라면 `a?.b.c` 로 충분하다.**
- ★★★ **`(n?.Inner).Count` 는 `NullReferenceException`** 이다.\
  괄호가 **「조심하는 구간」의 끝**을 정한다 — 괄호를 닫는 순간 평범한 `null` 값이 되고, 그 위의 `.Count` 는 그냥 역참조다.\
  ★ **리팩토링에서 괄호를 넣다가 이것을 만든다.** 겉보기에 같은 식인데 하나는 널을 주고 하나는 터진다.
- ★★★ **`[평가됨] 인자 A` 가 출력에 없다.**\
  `z?.Take(Loud("인자 A"))` 에서 `z` 가 널이라 **`Loud` 가 호출조차 되지 않았다.**\
  ★ `y?.Take(Loud("인자 B"))` 는 `y` 가 객체라 **둘 다 찍혔다** — **대조가 근거**다.
- **`arr?[0]`** 도 같은 규칙이다(`HasValue=False`). **`arr2?[1]` 은 `8`.**
- ★ **`?[]` 가 막는 것은 널뿐**이다 — 인덱스가 범위를 벗어나면 그대로 던진다.\
  **이 문서는 그것을 안 던졌다**(Learn 의 서술로만 안다).

### 3. `[평가됨]` 은 **두 번**만 찍힌다 — `??=` 의 두 번째 오른쪽은 평가조차 안 된다

**출력**

```text
===== 소스: cs07b-coalesce.cs =====
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
===== csc -out:ex.dll cs07b-coalesce.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
p ?? q ?? "끝"  = 끝
   [평가됨] 첫 대입
r = 첫 대입   ← 두 번째 오른쪽은 평가조차 안 됐다
   [평가됨] Pick()
Pick() ?? "기본" = 기본
int? null ?? -1 = -1  (정적 타입 Int32)
b.S 는 null
b.S ??= "채움" 뒤 → 채움
b.S ??= "다시" 뒤 → 채움
```

**왜 그런가**

- ★★★ **`[평가됨] 둘째 대입` 이 없다.** `r` 이 이미 `"첫 대입"` 으로 차 있으므로\
  두 번째 `r ??= Loud("둘째 대입")` 은 **오른쪽을 평가하지 않는다.**\
  ★ **이것이 지연 초기화 관용구가 성립하는 이유**다 — `_cache ??= ExpensiveBuild()` 가 **한 번만** 빌드한다.
- **`Pick()` 은 평가됐다** — `??` 의 **왼쪽은 언제나 평가된다.** 널인지 알아야 하기 때문이다.
- **`p ?? q ?? "끝"`** 은 앞 둘이 널이라 `"끝"` 이다.
- ★★ **`int? null ?? -1` 의 정적 타입이 `Int32`** 다 — 1번의 「`??` 가 겹을 벗긴다」가 여기서도 나온다.
- **필드에도 같다** — `b.S ??= "채움"` 뒤에 `b.S ??= "다시"` 를 해도 `채움` 그대로다.
- ★ **`??=` 는 원자적이지 않다.** 여러 스레드가 동시에 들어오면 오른쪽이 여러 번 평가될 수 있다.\
  **이 문서는 단일 스레드에서만 던졌다** — 「안 터졌다」가 「안전하다」가 아니다 → 10번.

### 4. ★★★ 진단 **3줄** — 문구는 같고 **열이 갈린다.** 그 열이 **오른쪽 결합**을 증명한다

**출력**

```text
===== 소스: cs07b-assoc.cs =====
int? x = null;
int y = 2;
int? z = 3;
var q1 = x ?? y ?? z;
var q2 = (x ?? y) ?? z;
var q3 = x ?? (y ?? z);
System.Console.WriteLine($"{q1} {q2} {q3}");
===== csc -out:ex.dll cs07b-assoc.cs (cc exit=1) =====
cs07b-assoc.cs(4,15): error CS0019: Operator '??' cannot be applied to operands of type 'int' and 'int?'
cs07b-assoc.cs(5,10): error CS0019: Operator '??' cannot be applied to operands of type 'int' and 'int?'
cs07b-assoc.cs(6,16): error CS0019: Operator '??' cannot be applied to operands of type 'int' and 'int?'
```

**왜 그런가**

```text
        1234567890123456
   4:   var q1 = x ?? y ?? z;     진단 (4,15)  →  열 15 = 'y'
   5:   var q2 = (x ?? y) ?? z;   진단 (5,10)  →  열 10 = '('
   6:   var q3 = x ?? (y ?? z);   진단 (6,16)  →  열 16 = 'y'
```

- ★★★ **세 진단의 문구가 한 글자도 같다** — `Operator '??' cannot be applied to operands of type 'int' and 'int?'`.\
  **문구만 보면 셋을 구분할 수 없다.** 갈라 주는 것은 **`(행,열)`** 뿐이다.
- ★★★ **q1 의 에러가 열 15, 곧 `y` 에서 시작한다** — 컴파일러가 **`y ?? z` 를 먼저 묶었다**는 뜻이다.\
  **좌결합이었다면 `(x ?? y)` 가 먼저이므로 열 10 에서 났을 것**이고, **q2 가 정확히 그렇다.**
- ★★★ **q1(열 15)과 q3(열 16)이 같은 짝을 지었다** — 둘 다 `y` 자리다.\
  ★ **`a ?? b ?? c` 는 `a ?? (b ?? c)` 와 같은 식**이다. **오른쪽 결합이 증명됐다.**
- **왜 에러가 나나** — `int y` 는 **널 아님 값 타입**이라 `??` 의 왼쪽에 올 수 없다.\
  ★ **일부러 에러가 나는 식을 만들어 컴파일러가 어느 짝을 지었는지 실토하게 한 것**이다.\
  ★★ 이 사실은 **출력으로는 증명할 수 없다** — 어느 쪽으로 묶어도 결과값이 같기 때문이다.\
  「**진단이 유일한 근거인 자리**」가 이 주제에 하나 있고, 그것이 여기다.

### 5. ★★★ **둘 다 `false`** 다 — 부정이 성립하지 않는다

**출력**

```text
===== 소스: cs07b-trap.cs =====
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
===== csc -out:ex.dll cs07b-trap.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
numbers?.Length 는 값이 있나 : False
numbers?.Length <  2 : False
numbers?.Length >= 2 : False
둘 다 false 다 — 부정이 성립하지 않는다
(numbers?.Length ?? 0) < 2 : True   ← ?? 로 접지해야 뜻대로 된다

s?.Length == 0 : False
s?.Length != 0 : True   ← == 와 != 는 3값이 아니다

s?.ToString()      : '(null)'
int? null 의 ToString() : '' (길이 0) ← null 이 아니라 빈 문자열이다
```

**왜 그런가**

- ★★★ **`numbers?.Length < 2` 도 `false` 이고 `numbers?.Length >= 2` 도 `false`** 다.\
  `numbers` 가 널이라 `numbers?.Length` 가 **「값 없음」인 `int?`** 이고,\
  **`int?` 의 `<`·`>`·`<=`·`>=` 는 한쪽이라도 널이면 `false`** 이기 때문이다.\
  ★ 그 규칙의 정본은 [08번](../08-nullable-value-types/)이다 — **3값 논리**다.
- ★★★ **`if` 문에서 만드는 버그**

  ```text
     if (numbers?.Length < 2) return;      ← numbers 가 null 이면 통과해 버린다
     …그 아래에서 numbers 를 쓴다 …         ← NullReferenceException
  ```

  「짧으면 일찍 빠져나가자」가 **널일 때만 안 빠져나간다.** 가장 널을 조심해야 할 입력에서 **가드가 풀린다.**
- ★★ **고치는 법은 `??` 로 접지하는 것** — `(numbers?.Length ?? 0) < 2` 가 `True` 다.\
  ★ Learn 도 이 형태를 권한다. **1번의 「`??` 가 겹을 벗긴다」가 여기서 값을 낸다.**
- ★ **`==`·`!=` 는 규칙이 다르다** — `s?.Length == 0` 은 `false`, `s?.Length != 0` 은 `true` 다.\
  **`<`·`>` 는 3값인데 `==`·`!=` 는 2값**이다. 같은 「널과의 비교」인데 **연산자마다 갈린다.**
- ★★ **`int?` 가 널일 때 `ToString()` 은 빈 문자열**이다(길이 0). **`"null"` 이 아니다.**\
  로그나 문자열 결합에서 **아무것도 안 찍혀 원인을 놓치는** 자리다.

### 6. ★ `[평가됨]` 이 **두 번**(B·D)만 찍힌다 — **C# 14부터**이고 `++` 는 안 된다

**출력**

```text
===== 소스: cs07b-c14.cs =====
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
===== csc -out:ex.dll cs07b-c14.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
cs07b-c14.cs(10,38): warning CS8602: Dereference of a possibly null reference.
cs07b-c14.cs(18,35): warning CS8602: Dereference of a possibly null reference.
nobody 가 null 일 때 '오른쪽 A' 가 찍혔나? ↑
   [평가됨] 오른쪽 B
somebody.Name = 오른쪽 B
missing 이 null 일 때 '오른쪽 C' 가 찍혔나? ↑
   [평가됨] 오른쪽 D
present[0] = 1
복합 대입도 같다 — '오른쪽 E' 가 찍혔나? ↑
```

**왜 그런가**

- **찍힌 것은 `오른쪽 B` 와 `오른쪽 D` 둘**이다. `A`·`C`·`E` 는 **왼쪽이 널이라 평가조차 안 됐다.**
- ★★★ **왼쪽이 널이면 오른쪽도 평가하지 않는다** — 2번의 단락 성질이 **대입에도 그대로** 적용된다.\
  Learn 이 이것을 `if (values is not null) { values[2] = GenerateNextIndex(); }` 와 같다고 못 박았다.
- **`?[]` 판도 된다** — `missing?[0] = …` 에서 `오른쪽 C` 가 안 찍혔다.
- ★ **복합 대입(`+=`)도 된다** — `maybe?.Score += …` 에서 `오른쪽 E` 가 안 찍혔다.
- ★★ **`++`·`--` 는 안 된다** — 8번의 `CS1059` 가 그것이다.\
  Learn 이 못 박은 이유는 **널 조건 식이 「변수」로 분류되지 않기 때문**이다.\
  같은 이유로 **`ref`/`out` 인자로도 못 넘기고 `ref` 대입도 안 된다.**
- ★ **이 절 전체가 `-langversion:latest` 덕분에 컴파일된다.** 옛 언어 버전에서는 전부 에러다.

### 7. ★★ `?.` 는 `if` 로 펼쳐지고, `??` 의 **`dup`** 이 왼쪽을 한 번만 읽는다

**출력**

```text
===== 소스: cs07b-il.cs =====
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
===== csc -r:il.dll -out:ex.dll cs07b-il.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
--- Probe.Cond ---
  .locals [0] System.Nullable<System.Int32>
  IL_0000: ldarg.0
  IL_0001: brtrue.s IL_000e
  IL_0003: ldloca.s 0
  IL_0005: initobj System.Nullable<System.Int32>
  IL_000b: ldloc.0
  IL_000c: br.s IL_0019
  IL_000e: ldarg.0
  IL_000f: ldfld Node::Count
  IL_0014: newobj System.Nullable<System.Int32>::.ctor
  IL_0019: ret
--- Probe.Manual ---
  .locals [0] System.Nullable<System.Int32>
  IL_0000: ldarg.0
  IL_0001: brfalse.s IL_0010
  IL_0003: ldarg.0
  IL_0004: ldfld Node::Count
  IL_0009: newobj System.Nullable<System.Int32>::.ctor
  IL_000e: br.s IL_0019
  IL_0010: ldloca.s 0
  IL_0012: initobj System.Nullable<System.Int32>
  IL_0018: ldloc.0
  IL_0019: ret
--- Probe.Chain ---
  .locals [0] System.Nullable<System.Int32>
  IL_0000: ldarg.0
  IL_0001: brtrue.s IL_000e
  IL_0003: ldloca.s 0
  IL_0005: initobj System.Nullable<System.Int32>
  IL_000b: ldloc.0
  IL_000c: br.s IL_001e
  IL_000e: ldarg.0
  IL_000f: ldfld Node::Inner
  IL_0014: ldfld Inner::Count
  IL_0019: newobj System.Nullable<System.Int32>::.ctor
  IL_001e: ret
--- Probe.Coalesce ---
  IL_0000: ldarg.0
  IL_0001: dup
  IL_0002: brtrue.s IL_000a
  IL_0004: pop
  IL_0005: ldstr "기본"
  IL_000a: ret
--- Probe.Assign ---
  .locals [0] Box
  IL_0000: nop
  IL_0001: ldarg.0
  IL_0002: stloc.0
  IL_0003: ldloc.0
  IL_0004: ldfld Box::S
  IL_0009: brtrue.s IL_0016
  IL_000b: ldloc.0
  IL_000c: ldstr "기본"
  IL_0011: stfld Box::S
  IL_0016: ret
```

**왜 그런가**

| 메서드 | IL 이 말하는 것 |
|---|---|
| `Cond`(`n?.Count`) | `brtrue.s` 로 갈라 널이면 `initobj Nullable<int>`(값 없음), 아니면 `ldfld` + `newobj Nullable<int>::.ctor` |
| `Manual`(삼항 연산자로 손으로 쓴 것) | ★ **거의 같다** — 분기 방향이 `brfalse.s` 로 뒤집혔을 뿐이다 |
| `Chain`(`n?.Inner.Count`) | ★★★ **`ldfld Inner` 와 `ldfld Count` 가 둘 다 「널 아님」 분기에만** 있다 |
| `Coalesce`(`s ?? "기본"`) | ★★★ **`dup` · `brtrue.s` · `pop`** |
| `Assign`(`b.S ??= "기본"`) | `ldfld` **한 번** 읽고 `brtrue.s`, 널일 때만 `stfld` |

- ★★★ **`Chain` 이 2번을 명령으로 증명한다** — 널 경로에 **`ldfld` 가 하나도 없다.**\
  「사슬 전체를 건너뛴다」가 **생성된 코드의 성질**이지 런타임의 배려가 아니다.\
  ★ 예외를 잡는 코드였다면 `ldfld` 가 있고 `try`/`catch` 가 있었을 것이다 — **없다.**
- ★★ **`Cond` 와 `Manual` 이 거의 같다** — `?.` 는 **문법 설탕**이다.\
  ★ 「`?.` 가 느리다」가 설 자리가 없다. **이 문서는 시간을 안 쟀지만 명령이 같다는 것은 보였다.**
- ★★★ **`Coalesce` 의 `dup` 이 「왼쪽을 한 번만 평가한다」를 증명한다.**\
  스택에 올린 값을 **복제해서** 검사하고, 널이면 `pop` 하고 기본값을 올린다.\
  **두 번 읽지 않는다.**
- ★★★ **그 보장이 성립하게 하는 관용구가 `handler?.Invoke()`** 다.\
  이벤트 델리게이트를 **한 번 읽어 두고** 그 값으로 호출하므로,\
  검사한 뒤에 다른 스레드가 구독을 취소해도 **이미 읽은 델리게이트가 돈다.**\
  ★ 손으로 쓰면 `var h = PropertyChanged; if (h != null) h(…);` 인데 **`?.` 가 같은 일을 한 줄로 한다.**\
  ★★ **이것은 언어 명세의 보장**이다 — Roslyn 이 `dup` 대신 지역 변수를 써도 성질은 안 바뀐다.\
  **명령은 관찰이고, 「한 번만 평가한다」는 보장이다.** 갈라 읽어라.
- ★ **`Assign` 도 `ldfld` 가 한 번**이다 — `??=` 가 필드를 두 번 읽지 않는다.

### 8. 에러 **2** · 경고 **2** — 값 타입은 에러, 참조 타입은 경고다

**출력**

```text
===== 소스: cs07b-forbid.cs =====
#nullable enable

Node? n = null;
int count = n?.Count;          // int? 를 int 에 암묵으로 — 못 한다
string s = n?.Name;            // string? 를 string 에 — 경고만
n?.Count++;                    // 널 조건 접근에 ++ 는 C# 14 에서도 안 된다
System.Console.WriteLine($"{count} {s}");

public class Node { public string? Name; public int Count; }
===== csc -out:ex.dll cs07b-forbid.cs (cc exit=1) =====
cs07b-forbid.cs(4,13): error CS0266: Cannot implicitly convert type 'int?' to 'int'. An explicit conversion exists (are you missing a cast?)
cs07b-forbid.cs(6,1): error CS1059: The operand of an increment or decrement operator must be a variable, property or indexer
cs07b-forbid.cs(4,13): warning CS8629: Nullable value type may be null.
cs07b-forbid.cs(5,12): warning CS8600: Converting null literal or possible null value to non-nullable type.
```

**왜 그런가**

| 쓴 것 | 진단 | 왜 |
|---|---|---|
| `int count = n?.Count;` | ★ **`error CS0266`** | ★★★ **1번의 「한 겹」이 에러로 드러난다** — `int?` → `int` 암묵 변환이 없다 |
| `string s = n?.Name;` | **`warning CS8600`** | ★ 참조 타입은 **경고**다 — [06번](../06-nullable-reference-types/)의 규칙이다 |
| `n?.Count++;` | **`error CS1059`** | ★★ **널 조건 식은 「변수」가 아니다** — C# 14 에서도 `++` 는 금지다 |
| (같은 줄) | **`warning CS8629`** | ★ **값 타입 쪽 경고 번호는 따로 있다** — `CS8602` 가 아니다 |

- ★★★ **같은 실수가 값 타입에서는 에러이고 참조 타입에서는 경고다.**
  - `int?` 는 **진짜 타입**이라 변환이 없으면 **컴파일이 안 된다**([08번](../08-nullable-value-types/)).
  - `string?` 은 **주석**이라 **경고로 끝난다**([06번](../06-nullable-reference-types/)).
  - ★ **06 → 07 → 08 사슬이 한 블록에서 전부 보이는 자리**다.
- ★★ **널 관련 경고 번호가 둘로 갈린다** — 참조 타입은 `CS8600`·`CS8602`, **값 타입은 `CS8629`** 다.\
  ★ 「널 경고」라고 뭉뚱그리면 **어느 쪽 `?` 이야기인지 놓친다.**
- ★ **고치는 법** — `int count = n?.Count ?? 0;` 또는 `int? count = n?.Count;`.

### 9. **잡는 것이 아니라 실행을 안 하는 것**이다

**답**

- ★★★ **`a?.Take(f())` 에서 `a` 가 널이면 `f()` 는 실행되지 않는다**(2번의 `인자 A`).
- ★★★ **`try`/`catch` 와 결정적으로 다르다.**

```text
   a?.Take(f());                              try { a.Take(f()); }
                                              catch (NullReferenceException) { }
   ────────────────────────────────           ────────────────────────────────
   a 가 null 이면                              a 가 null 이면
     f() 를 호출하지 않는다  ← 부작용 없음        f() 를 먼저 호출한다  ← ★ 부작용이 일어난다
     예외가 나지 않는다                          그다음 .Take 에서 예외가 난다
     결과는 「값 없음」                           예외를 삼킨다 — 다른 NRE 까지 함께 삼킨다
```

- ★★ **부작용이 있는 인자에서 이 차이가 버그가 된다** — 카운터를 올리거나 큐에서 꺼내는 인자라면.
- ★★ **`catch (NullReferenceException)` 은 더 나쁘다** — `Take` **안쪽**에서 난 널 예외까지 함께 삼킨다.\
  `?.` 는 **그 한 접근만** 건너뛴다.
- **같은 집안인 연산자** — **`&&` 와 `||`** 다. 「단락 평가」라는 말이 그 뜻이다.\
  ★ 덧붙여 **`??`·`??=` 도 같은 집안**이다(3번).
- ★ **IL 이 이것을 확정한다**(7번) — 널 경로에 `ldfld` 도 `call` 도 없다. **`try` 블록도 없다.**

### 10. **미룬 것**이지 처리한 것이 아니다 — 그리고 `??=` 는 스레드 안전이 아니다

**답**

- ★★★ **`a?.b?.c?.d` 가 널을 돌려줬을 때 어디서 끊겼는지 알 수 없다.**\
  네 자리 중 어디였는지 **출력에도 예외에도 안 남는다.**\
  ★ **진단이 필요하면 `if` 로 풀고 단계마다 메시지를 붙여라.**
- ★★★ **「`?.` 로 널을 처리했다」는 부정확하다** — **미룬 것**이다.\
  미룬 널은 **더 먼 곳에서 다시 나타나고**, 그때는 원인이 안 보인다.\
  ★ 널이 **버그**인 자리에서는 **터지는 편이 낫다** — 스택 트레이스가 원인을 가리킨다.
- ★★ **`_cache ??= Build()` 는 여러 스레드에서 안전하지 않다.**\
  `??=` 는 **읽고·비교하고·쓰는** 세 단계이고 **원자적이지 않다**(7번의 IL 이 그렇다).\
  둘이 동시에 들어오면 **`Build()` 가 두 번 돌 수 있다.**\
  ★★ **이 문서는 단일 스레드에서만 던졌다** — **「안 터졌다」가 「안전하다」가 아니다.**\
  스레드 안전이 필요하면 `Lazy<T>` 나 `Interlocked.CompareExchange` 를 쓴다(**이 문서는 안 던졌다**).
- **`??` 대 예외를 고르는 기준** — 값이 **없어도 되는 것**이면 `??`,\
  **있어야 하는 것**이면 `ArgumentNullException.ThrowIfNull` 이다.\
  ★ 「기본값이 명확한가」를 물어라. 기본값이 「어쩔 수 없이 고른 것」이면 **버그를 숨기는 것**이다.

### 11. ★★ `node?.Count` 한 줄에 **두 종류의 물음표**가 있다

**답**

```text
   Node? node = null;
   var x = node?.Count;
        ▲        ▲
        │        └─ ?.  → 결과가 int?  = Nullable<Int32>   ← ★ 08번. 진짜 타입(구조체)
        │
        └─ 선언의 Node? → 런타임 타입은 그냥 Node          ← ★ 06번. 주석(메타데이터)
```

- ★★★ **런타임에 존재하는 것은 `int?` 쪽뿐**이다.\
  `Node?` 는 **메타데이터의 `NullableAttribute` 한 칸**으로만 남고([06번](../06-nullable-reference-types/)),\
  `int?` 는 **`System.Nullable<System.Int32>` 라는 구조체**다([08번](../08-nullable-value-types/)).
- ★★ **1번에서 참조 타입에 겹이 안 붙은 것**이 곧 **「`string?` 은 타입이 아니다」**(06번 3번)와 같은 말이다.\
  겹을 붙일 타입 자체가 없다.
- **5번의 「둘 다 `false`」를 설명하는 정본은 [08번](../08-nullable-value-types/)** 이다 — **리프티드 비교의 3값 논리**.
- ★★★ **그래서 세 주제가 한 사슬이다**
  1. [06번](../06-nullable-reference-types/) — **무엇이 널일 수 있나**를 선언한다(주석).
  2. **07번(여기)** — **그러면 어떻게 다루나**(연산자).
  3. [08번](../08-nullable-value-types/) — **널을 담는 진짜 타입**은 무엇인가(구조체).

### 12. 다른 언어와 잇기

- **Kotlin** — [널 안전 타입 편](../../../kotlin/syntax/03-null-safe-types/).\
  `?.` 와 엘비스 `?:`(C# 의 `??` 에 해당)가 있어 **기호는 비슷하다.**\
  ★★ **다른 것은 타입 체계다** — Kotlin 은 `Int` 와 `Int?` 가 **타입 시스템의 다른 타입**이고,\
  `Int?` 는 **박싱된 표현**으로 내려간다. C# 의 `int?` 는 **박싱 없는 구조체**다([08번](../08-nullable-value-types/)).\
  ★ **널 안전의 대가를 어디서 치르나가 갈린다** — Kotlin 은 **할당**, C# 은 **크기**(4바이트 → 8바이트).
- **TypeScript** — [`any`·`unknown`·`never`·`void` 편](../../../ts/syntax/04-any-unknown-never-void/).\
  `?.`·`??` 를 **문법까지 그대로** 갖고 있다.\
  ★★ **다른 것은 「남는 것」이다** — TS 의 `?.` 는 **트랜스파일 결과에 실제 널 검사가 남는다**(런타임 기능이다).\
  타입 주석은 지워지는데 **`?.` 는 안 지워진다.**\
  ★ C# 도 마찬가지로 **`?.` 는 IL 에 분기가 남고**(7번) **`string?` 주석은 안 남는다**([06번](../06-nullable-reference-types/)).\
  **두 언어가 같은 자리에서 같게 갈렸다.**
- **Java** — [원시 타입과 래퍼 편](../../../java/syntax/01-primitives-and-wrappers/).\
  ★ **`?.` 에 해당하는 문법이 없다.** `Optional.map` 사슬이나 `if` 를 써야 하고,\
  `handler?.Invoke()` 에 해당하는 것도 **`if (h != null) h.run();` 을 손으로 쓴다.**\
  ★★ 그래서 Java 에서는 **「한 번만 읽었나」를 사람이 지켜야 한다** — C# 은 언어가 보장한다(7번).

## 실행 검증

**무엇을 몇 번 어느 판에서 돌렸나** — 아래 블록은 전부 **.NET SDK 10.0.401 / 런타임 10.0.12 / `net10.0` / linux-x64 /\
`-langversion:latest`** 에서 캡처 스크립트로 받았다. **제출 직전에 전부 다시 돌려 정규화 대조했다.**

| 블록 | 무엇을 고정하나 | 명령 |
|---|---|---|
| `cs07b-type.cs` | ★★★ `?.` 의 정적 타입 9벌 — `int` → `Nullable<Int32>`, 참조 타입은 그대로 | `csc` + 실행 |
| `cs07b-chain.cs` | ★★★ 사슬 단락 · 괄호가 끊는 것 · **인자 미평가** · `?[]` | 〃 |
| `cs07b-coalesce.cs` | ★★ `??=` 의 오른쪽이 **두 번째에 평가 안 되는** 것 | 〃 |
| `cs07b-assoc.cs` | ★★★ **진단 3줄의 열 번호**가 오른쪽 결합을 증명 | `csc` 만(`cc exit=1`) |
| `cs07b-trap.cs` | ★★★ `< 2` 와 `>= 2` 가 **둘 다 `false`** · `??` 접지 | `csc` + 실행 |
| `cs07b-c14.cs` | ★ C# 14 널 조건 대입 — 오른쪽 미평가 3건 | 〃 |
| `cs07b-il.cs` | ★★★ `Chain` 의 `ldfld` 배치 · `Coalesce` 의 **`dup`** | `csc -r:il.dll` + 실행 |
| `cs07b-form.cs` | 연산자 전체 형태 · `handler?.Invoke()` | `csc` + 실행 |
| `cs07b-forbid.cs` | ★★ **에러 2 · 경고 2** — 값 타입은 에러, 참조 타입은 경고 | `csc` 만(`cc exit=1`) |

**구현에 달린 항목**

- ★ **IL 의 정확한 명령 열**(7번) — `dup`/`pop` 을 쓸지 지역 변수를 쓸지는 Roslyn 이 고른다.\
  ★★ **「왼쪽을 한 번만 평가한다」는 언어 보장**이므로 명령이 바뀌어도 성질은 안 바뀐다.
- **`nop` 의 유무** — `-optimize` 를 안 준 결과다(**이 문서는 안 켰다**).
- **진단 문구·`(행,열)`** — 다만 4번의 **열이 어느 토큰을 가리키나**는 문법이 정한 결합 방향의 귀결이다.
- **`NullReferenceException` 메시지**·**종료 코드**.

**언어가 보장하는 것**(구현이 바뀌어도 같다)

- **`?.`·`?[]` 가 단락하는 것** — 사슬의 나머지와 **인자까지** 평가하지 않는다.
- **괄호가 단락을 끊는 것.**
- **멤버가 널 아님 값 타입 `T` 면 결과가 `T?`** 이고 **참조 타입이면 그대로**인 것.
- ★★ **`?.` 가 왼쪽 피연산자를 한 번만 평가하는 것.**
- **`??` 가 오른쪽 결합이고, 왼쪽이 널일 때만 오른쪽을 평가하는 것.**
- **`??=` 가 왼쪽이 널일 때만 대입·평가하는 것.**
- **C# 14 널 조건 대입에서 왼쪽이 널이면 오른쪽을 평가하지 않는 것**과 **`++`·`--` 가 금지인 것.**
- **`int?` 의 `<`·`>`·`<=`·`>=` 가 널이 섞이면 `false` 인 것**([08번](../08-nullable-value-types/)이 정본).

**안 돌려 본 것 / 못 잰 것**

- **안 돌려 본 것** — **`?[]` 의 범위 초과**(Learn 의 서술로만 안다) ·\
  **`?.` 와 확장 메서드의 상호작용**(확장 메서드는 `this` 가 널이어도 호출된다 — **확인 안 했다**) ·\
  **`x ?? throw …`**(C# 7 throw 식) · **`ArgumentNullException.ThrowIfNull`** ·\
  **`?.` 뒤의 `await`** · **`Lazy<T>`·`Interlocked` 를 쓴 스레드 안전 지연 초기화** ·\
  **옛 `-langversion`** 에서 6번이 막히는 것(**던지면 확인되나 안 던졌다**) ·\
  **`is null` 과 `== null` 이 연산자 오버로드에서 갈리는 것**(목록의 **21번 주제**).
- **못 잰 것** — ★★ **`??=` 의 멀티스레드 동작.**\
  단일 스레드로는 **원자성을 반증할 수 없다** — 경쟁을 재현하려면 스레드 하네스가 필요하고,\
  ★ **「안 터졌다」가 「안전하다」가 아니므로** 이 문서는 **IL 이 세 단계라는 것**만 근거로 적었다(7번).
- ★ **할당 바이트는 「안 잰 것」이 아니라 「여기서 잴 이유가 없는 것」이다** —\
  `?.` 가 만드는 `Nullable<T>` 는 **구조체라 힙을 안 쓴다.** 정본은 [08번](../08-nullable-value-types/)이다.

**버전이 올랐을 때 다시 돌려야 하는 것**

- ★★ **7번의 IL 다섯 벌** — Roslyn 이 바뀌면 명령이 움직인다. **성질(단락·한 번 평가)은 안 움직인다.**
- ★ **4번의 열 번호** — 진단 위치 계산이 바뀌면 움직인다. **결합 방향 자체는 문법이라 안 움직인다.**
- ★ **6번** — C# 14 기능이라 **`-langversion` 을 바꾸면 통째로 갈린다.**
