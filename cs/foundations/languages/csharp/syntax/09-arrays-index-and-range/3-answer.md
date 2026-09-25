# csharp/syntax/09 — 배열과 인덱스·범위 연산자(C# 8) — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> **기준 소스** — [ECMA-334 7판(2023-12)](https://ecma-international.org/publications-and-standards/standards/ecma-334/) · [Microsoft Learn — C# 언어 레퍼런스](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/) · [Learn — 배열](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/builtin-types/arrays) · [Learn — 멤버 접근 연산자와 식](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/operators/member-access-operators) · [Learn — 연산자 우선순위](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/operators/) · [.NET API — `System.Index`](https://learn.microsoft.com/en-us/dotnet/api/system.index) · [.NET API — `System.Range`](https://learn.microsoft.com/en-us/dotnet/api/system.range)
> **실행 검증** — 이 문서의 모든 출력·진단·IL·할당 바이트는 **.NET SDK 10.0.401** ·\
> 런타임 **`.NET 10.0.12`**(`Microsoft.NETCore.App`) · 타겟 **`net10.0`** · **linux-x64** 에서 실제로 돌려 얻은 것이다(2026-09-25).\
> ★ 블록은 캡처 스크립트가 파일로 받아 조립기가 끼워 넣은 것이다 — 사람이 옮겨 적은 줄은 하나도 없다.\
> ★ 소스 펜스의 배너(`===== 소스: cs09b-….cs =====`)도 **캡처가 찍은 것**이다.
> **읽는 법** — ★★★ **할당 바이트는 증분만 근거로 쓴다.** 절댓값(프로세스 누적)은 흔들리는 칸이라\
> 이 문서는 **한 번도 싣지 않았다.** 더 중요한 것은 **0 이냐 아니냐**다 — 4번이 거기 달렸다.\
> ★★ **9번은 출력이 근거가 아니다** — 근거는 **진단의 `(행,열)`** 이다.\
> ★ **`cc exit` 과 `run exit` 을 갈라 적었다.**\
> 자세한 환경과 던진 형태는 [2-summary.md](2-summary.md)의 머리말·(0)절에 있다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. **참조 타입**이다 — `System.Array` 를 상속하고, 대입은 참조를 옮긴다

**출력**

```text
===== 소스: cs09b-ref.cs =====
using System;

int[] a = { 10, 20, 30, 40, 50 };
int[] b = a;                       // 참조만 복사된다
b[0] = 999;

Console.WriteLine($"typeof(int[]).IsValueType      : {typeof(int[]).IsValueType}");
Console.WriteLine($"typeof(int[]).BaseType         = {typeof(int[]).BaseType}");
Console.WriteLine($"typeof(int[]).IsArray          : {typeof(int[]).IsArray}");
Console.WriteLine($"typeof(int[]).GetElementType() = {typeof(int[]).GetElementType()}");
Console.WriteLine($"a is System.Collections.IList  : {a is System.Collections.IList}");
Console.WriteLine();
Console.WriteLine($"ReferenceEquals(a, b)          : {ReferenceEquals(a, b)}");
Console.WriteLine($"b[0] = 999 뒤 a[0]             : {a[0]}");
Console.WriteLine($"a.Length                       : {a.Length}   a.Rank : {a.Rank}");

Bump(a);
Console.WriteLine($"Bump(a) 뒤 a[1]                : {a[1]}   ← 메서드가 원본을 바꿨다");

int[] c = (int[])a.Clone();
c[1] = -1;
Console.WriteLine($"Clone() 뒤 a[1]={a[1]} c[1]={c[1]}  ReferenceEquals={ReferenceEquals(a, c)}");

int[] fresh = new int[3];
Console.WriteLine($"new int[3] 의 원소            : [{string.Join(", ", fresh)}]  ← 0 으로 채워진다");
string[] strs = new string[2];
Console.WriteLine($"new string[2] 의 원소         : [{(strs[0] is null ? "null" : strs[0])}, {(strs[1] is null ? "null" : strs[1])}]");

static void Bump(int[] arr) { arr[1] += 1; }
===== csc -out:ex.dll cs09b-ref.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
typeof(int[]).IsValueType      : False
typeof(int[]).BaseType         = System.Array
typeof(int[]).IsArray          : True
typeof(int[]).GetElementType() = System.Int32
a is System.Collections.IList  : True

ReferenceEquals(a, b)          : True
b[0] = 999 뒤 a[0]             : 999
a.Length                       : 5   a.Rank : 1
Bump(a) 뒤 a[1]                : 21   ← 메서드가 원본을 바꿨다
Clone() 뒤 a[1]=21 c[1]=-1  ReferenceEquals=False
new int[3] 의 원소            : [0, 0, 0]  ← 0 으로 채워진다
new string[2] 의 원소         : [null, null]
```

**왜 그런가**

- ★★★ **`IsValueType` 이 `False`, `BaseType` 이 `System.Array`** 다. **원소가 `int` 여도 배열은 힙 객체**다.\
  [01번](../01-value-types-and-reference-types/)의 이분이 그대로 적용된다 — 변수에 들어 있는 것은 **참조 8바이트**다.
- ★★★ **`int[] b = a;` 는 참조 대입**이라 `ReferenceEquals(a, b)` 가 `True` 이고,\
  `b[0] = 999` 가 **`a[0]` 을 999로** 바꿨다. 원소가 복사되지 않는다.
- ★★ **`Bump(a)` 가 `ref` 없이 원본을 바꿨다**(20 → 21). 헷갈리는 자리는 여기다 —\
  **바뀌지 않는 것은 `a` 라는 변수가 어느 배열을 가리키느냐**뿐이고, **가리키는 배열의 내용**은 누구나 바꾼다.
- **`Clone()` 은 새 객체**라 `ReferenceEquals` 가 `False` 이고 `c[1] = -1` 이 원본을 안 건드렸다.\
  ★ 다만 **얕은 복사**다 — 원소가 참조 타입이면 **가리키는 대상은 공유**된다.
- ★★ **`new string[2]` 가 `[null, null]`** 이다. **[06번](../06-nullable-reference-types/)이 이것을 경고로 잡아 주지 못한다** —\
  `string[]` 은 「널 아님」으로 선언됐는데 런타임에는 널이 들어 있다. **배열 생성은 널 허용 분석의 구멍**이다.

### 2. ★★ 둘 다 **구조체**다 — 그리고 `^0` 은 **길이**다

**출력**

```text
===== 소스: cs09b-index.cs =====
using System;

var i = ^1;
var r = 1..^1;
Console.WriteLine($"var i = ^1;     i.GetType() = {i.GetType()}");
Console.WriteLine($"var r = 1..^1;  r.GetType() = {r.GetType()}");
Console.WriteLine($"typeof(Index).IsValueType : {typeof(Index).IsValueType}   typeof(Range).IsValueType : {typeof(Range).IsValueType}");
Console.WriteLine();

Index e1 = ^1, e0 = ^0, s2 = 2;
Console.WriteLine($"^1 : Value={e1.Value} IsFromEnd={e1.IsFromEnd}  ToString()='{e1}'");
Console.WriteLine($"^0 : Value={e0.Value} IsFromEnd={e0.IsFromEnd}  ToString()='{e0}'");
Console.WriteLine($" 2 : Value={s2.Value} IsFromEnd={s2.IsFromEnd}  ToString()='{s2}'");
Console.WriteLine($"Index.Start={Index.Start}  Index.End={Index.End}  (Index.End 의 IsFromEnd={Index.End.IsFromEnd})");
Console.WriteLine();

int len = 5;
Console.WriteLine($"^1.GetOffset(5) = {e1.GetOffset(len)}");
Console.WriteLine($"^0.GetOffset(5) = {e0.GetOffset(len)}   ← 길이와 같다");
Console.WriteLine($" 2.GetOffset(5) = {s2.GetOffset(len)}");
Console.WriteLine();

Console.WriteLine($"1..^1 : Start={r.Start} End={r.End}  ToString()='{r}'");
Console.WriteLine($"Range.All : Start={Range.All.Start} End={Range.All.End}  ToString()='{Range.All}'");
var ol = r.GetOffsetAndLength(5);
Console.WriteLine($"(1..^1).GetOffsetAndLength(5) = (offset={ol.Offset}, length={ol.Length})");
Console.WriteLine();

int[] a = { 10, 20, 30, 40, 50 };
Console.WriteLine($"a[^1]   = {a[^1]}     a[^5] = {a[^5]}");
Console.WriteLine($"a[1..^1] = [{string.Join(", ", a[1..^1])}]");
Console.WriteLine($"a[..2]   = [{string.Join(", ", a[..2])}]");
Console.WriteLine($"a[3..]   = [{string.Join(", ", a[3..])}]");
Console.WriteLine($"a[..]    = [{string.Join(", ", a[..])}]   ← 전체");
Console.WriteLine($"a[2..2]  = [{string.Join(", ", a[2..2])}] (길이 {a[2..2].Length})  ← 빈 배열, 예외가 아니다");
Console.WriteLine($"a[^3..^1] = [{string.Join(", ", a[^3..^1])}]");
===== csc -out:ex.dll cs09b-index.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
var i = ^1;     i.GetType() = System.Index
var r = 1..^1;  r.GetType() = System.Range
typeof(Index).IsValueType : True   typeof(Range).IsValueType : True

^1 : Value=1 IsFromEnd=True  ToString()='^1'
^0 : Value=0 IsFromEnd=True  ToString()='^0'
 2 : Value=2 IsFromEnd=False  ToString()='2'
Index.Start=0  Index.End=^0  (Index.End 의 IsFromEnd=True)

^1.GetOffset(5) = 4
^0.GetOffset(5) = 5   ← 길이와 같다
 2.GetOffset(5) = 2

1..^1 : Start=1 End=^1  ToString()='1..^1'
Range.All : Start=0 End=^0  ToString()='0..^0'
(1..^1).GetOffsetAndLength(5) = (offset=1, length=3)

a[^1]   = 50     a[^5] = 10
a[1..^1] = [20, 30, 40]
a[..2]   = [10, 20]
a[3..]   = [40, 50]
a[..]    = [10, 20, 30, 40, 50]   ← 전체
a[2..2]  = [] (길이 0)  ← 빈 배열, 예외가 아니다
a[^3..^1] = [30, 40]
```

**왜 그런가**

| 쓴 것 | `Value` | `IsFromEnd` | `GetOffset(5)` |
|---|---|---|---|
| `^1` | 1 | `True` | **4** |
| ★★★ `^0` | 0 | `True` | ★★★ **5** — 길이와 같다 |
| `2` | 2 | `False` | 2 |

- ★★★ **`var i = ^1;` 이 `System.Index`, `var r = 1..^1;` 이 `System.Range`** 다.\
  **둘 다 `IsValueType` 이 `True`** — 구조체이고, 인덱싱 밖에서도 **변수·필드·인자로 쓸 수 있는 1급 값**이다.
- ★★★ **`^0.GetOffset(5)` 가 5** 다. 「끝에서 0번째」는 **마지막 원소가 아니라 그 다음 자리**이고,\
  그 자리가 **곧 길이**다. 그래서 3번이 터진다.
- ★ **`Index.End` 가 `^0`** 이고 `Range.All` 이 `0..^0` 으로 찍힌다 — **BCL 이 같은 규칙으로 이름을 붙였다.**
- ★★ **`a[2..2]` 는 빈 배열**이고 예외가 아니다(길이 0).\
  **인덱싱의 경계**(원소가 있어야 한다)와 **슬라이싱의 경계**(시작 ≤ 끝 ≤ 길이면 된다)가 **다른 규칙**이다.
- **`GetOffsetAndLength(5)` 가 `(1, 3)`** 을 준다 — 내 타입에 `Slice(start, length)` 를 달 때 **이것이 다리**다(5번).

### 3. **`IndexOutOfRangeException`** — 컴파일러는 안 막는다

**출력**

```text
===== 소스: cs09b-end0.cs =====
using System;

int[] a = { 10, 20, 30, 40, 50 };
Console.WriteLine(a[^0]);
===== csc -out:ex.dll cs09b-end0.cs && dotnet ex.dll (cc exit=0 · run exit=134) =====
Unhandled exception. System.IndexOutOfRangeException: Index was outside the bounds of the array.
   at Program.<Main>$(String[] args)
```

**왜 그런가**

- ★★★ **`a[^0]` 은 `a[a.Length]`** 이고, 길이 5인 배열에 5번 원소는 없다. **`run exit=134`** 로 죽었다.
- ★★★ **컴파일은 통과했다**(`cc exit=0`). `^` 는 **산술로 풀리는 것**이라(8번)\
  컴파일러 입장에서는 `a[a.Length - 0]` 과 다를 바 없고, **배열 인덱스 검사는 런타임의 일**이다.\
  ★ **상수라서 잡힐 것 같지만 안 잡힌다** — 「컴파일러가 아는 것처럼 보이는데 안 막는 자리」다.
- ★★ **`a[3..^0]` 은 정상**이다. 범위의 **끝은 포함하지 않으므로**, 끝이 길이와 같아도 된다.\
  ★ **같은 `^0` 이 인덱스 자리에서는 반드시 틀리고 범위의 끝 자리에서는 정상**이다 —\
  「`^0` 이 나쁜 것」이 아니라 **어느 자리에 쓰느냐**가 정한다.
- **메시지가 `Index was outside the bounds of the array.`** 다. ★ `^` 를 썼다는 흔적이 **메시지에 없다** —\
  `-debug` 를 안 줘서 줄 번호도 없다. **이 예외만 보고 `^0` 을 의심하기는 어렵다**는 뜻이다.

### 4. ★★★ **배열은 복사(+40), `Span` 은 뷰(+0)** — 출력은 같고 바이트가 갈린다

**출력**

```text
===== 소스: cs09b-alloc.cs =====
using System;

Warm();

int[] a = { 10, 20, 30, 40, 50 };

long b0 = GC.GetAllocatedBytesForCurrentThread();
int[] copy = a[1..^1];                        // 배열의 .. — 새 배열
long b1 = GC.GetAllocatedBytesForCurrentThread();
Span<int> view = a.AsSpan()[1..^1];           // Span 의 .. — 뷰
long b2 = GC.GetAllocatedBytesForCurrentThread();
int one = a[^1];                              // 끝 기준 인덱싱
long b3 = GC.GetAllocatedBytesForCurrentThread();
int[] whole = a[..];                          // 전체 범위
long b4 = GC.GetAllocatedBytesForCurrentThread();
int[] none = a[2..2];                         // 빈 범위
long b5 = GC.GetAllocatedBytesForCurrentThread();
Span<int> sneaky = a[1..^1];                  // Span 에 받아도 배열 인덱서가 먼저 돈다
long b6 = GC.GetAllocatedBytesForCurrentThread();
string s = "abcdef";
string sub = s[1..^1];                        // string 의 .. — Substring
long b7 = GC.GetAllocatedBytesForCurrentThread();
ReadOnlySpan<char> chars = s.AsSpan()[1..^1]; // ReadOnlySpan 의 .. — 뷰
long b8 = GC.GetAllocatedBytesForCurrentThread();

Console.WriteLine($"int[] copy   = a[1..^1]            : +{b1 - b0} 바이트");
Console.WriteLine($"Span<int>    = a.AsSpan()[1..^1]   : +{b2 - b1} 바이트");
Console.WriteLine($"int one      = a[^1]               : +{b3 - b2} 바이트");
Console.WriteLine($"int[] whole  = a[..]               : +{b4 - b3} 바이트");
Console.WriteLine($"int[] none   = a[2..2]             : +{b5 - b4} 바이트  (길이 {none.Length})");
Console.WriteLine($"Span<int>    = a[1..^1]            : +{b6 - b5} 바이트  ← AsSpan() 을 안 거쳤다");
Console.WriteLine($"string sub   = s[1..^1]            : +{b7 - b6} 바이트  (\"{sub}\")");
Console.WriteLine($"ROSpan<char> = s.AsSpan()[1..^1]   : +{b8 - b7} 바이트  (길이 {chars.Length})");
Console.WriteLine();

copy[0] = -1;
Console.WriteLine($"copy[0] = -1 뒤  a[1] = {a[1]}   ← 원본이 안 바뀐다");
view[0] = -2;
Console.WriteLine($"view[0] = -2 뒤  a[1] = {a[1]}   ← 원본이 바뀐다");
sneaky[0] = -3;
Console.WriteLine($"sneaky[0] = -3 뒤 a[1] = {a[1]}   ← 안 바뀐다 (복사본을 보고 있다)");
Console.WriteLine($"a = [{string.Join(", ", a)}]  one={one}  whole.Length={whole.Length}");
Console.WriteLine($"ReferenceEquals(a, a[..]) : {ReferenceEquals(a, a[..])}");
Console.WriteLine();

long c0 = GC.GetAllocatedBytesForCurrentThread();
for (int k = 0; k < 1000; k++) { int[] t = a[1..^1]; GC.KeepAlive(t); }
long c1 = GC.GetAllocatedBytesForCurrentThread();
int acc = 0;
long d0 = GC.GetAllocatedBytesForCurrentThread();
for (int k = 0; k < 1000; k++) { Span<int> t = a.AsSpan()[1..^1]; acc += t[0]; }
long d1 = GC.GetAllocatedBytesForCurrentThread();
Console.WriteLine($"배열 슬라이스 1000번 : +{c1 - c0} 바이트");
Console.WriteLine($"Span 슬라이스 1000번 : +{d1 - d0} 바이트   (acc={acc})");

static void Warm() {
    int[] w = { 1, 2, 3 };
    int[] wc = w[0..2];
    Span<int> ws = w.AsSpan()[0..2];
    string wsx = "abc"[0..2];
    ReadOnlySpan<char> wrs = "abc".AsSpan()[0..2];
    GC.KeepAlive(wc); GC.KeepAlive(wsx);
    GC.KeepAlive(ws.Length + wrs.Length);
    GC.GetAllocatedBytesForCurrentThread();
}
===== csc -out:ex.dll cs09b-alloc.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
int[] copy   = a[1..^1]            : +40 바이트
Span<int>    = a.AsSpan()[1..^1]   : +0 바이트
int one      = a[^1]               : +0 바이트
int[] whole  = a[..]               : +48 바이트
int[] none   = a[2..2]             : +0 바이트  (길이 0)
Span<int>    = a[1..^1]            : +40 바이트  ← AsSpan() 을 안 거쳤다
string sub   = s[1..^1]            : +32 바이트  ("bcde")
ROSpan<char> = s.AsSpan()[1..^1]   : +0 바이트  (길이 4)

copy[0] = -1 뒤  a[1] = 20   ← 원본이 안 바뀐다
view[0] = -2 뒤  a[1] = -2   ← 원본이 바뀐다
sneaky[0] = -3 뒤 a[1] = -2   ← 안 바뀐다 (복사본을 보고 있다)
a = [10, -2, 30, 40, 50]  one=50  whole.Length=5
ReferenceEquals(a, a[..]) : False

배열 슬라이스 1000번 : +40000 바이트
Span 슬라이스 1000번 : +0 바이트   (acc=-2000)
```

**왜 그런가**

| 쓴 것 | 증분 | 읽는 법 |
|---|---|---|
| `int[] copy = a[1..^1]` | ★★★ **+40** | 헤더 16 + 길이 8 + `int` 3개 12 → 정렬해 40 |
| ★★★ `Span<int> = a.AsSpan()[1..^1]` | ★★★ **+0** | 저장소를 안 만든다 |
| `int one = a[^1]` | **+0** | `^` 는 산술로 풀린다(8번) |
| `int[] whole = a[..]` | **+48** | ★ **전체라도 새 배열**이다 |
| `int[] none = a[2..2]` | ★★ **+0** | 빈 배열은 재사용된다 |
| ★★★ `Span<int> = a[1..^1]` | ★★★ **+40** | **`AsSpan()` 을 안 거쳤다** |
| `string sub = s[1..^1]` | **+32** | `Substring` — 문자열도 복사 |
| `ROSpan<char> = s.AsSpan()[1..^1]` | **+0** | 문자열에도 뷰가 있다 |
| 배열 슬라이스 1000번 | **+40000** | 하나도 재사용되지 않는다 |
| `Span` 슬라이스 1000번 | ★★★ **+0** | **루프에서 갈리는 것이 이것** |

- ★★★ **`copy` 와 `view` 는 같은 `[20, 30, 40]` 을 준다.** 출력으로는 못 가른다.\
  갈리는 것은 **증분 바이트**와 **쓰기 뒤의 원본**뿐이다 —\
  `copy[0] = -1` 뒤 `a[1]` 은 **20 그대로**이고, `view[0] = -2` 뒤 `a[1]` 은 **−2** 다.
- ★★★ **`Span<int> sneaky = a[1..^1];` 이 +40** 이다. 이것이 이 주제에서 가장 조용한 함정이다.\
  `int[]` → `Span<int>` **암묵 변환**이 있어 컴파일은 되지만, **평가 순서가 정해져 있다** —\
  ① 배열 인덱서가 돌아 **새 배열을 만들고** ② 그 배열을 span 으로 감싼다.\
  `sneaky[0] = -3` 이 원본을 **안 바꾼 것**이 그 증거다(`a[1]` 이 −2 그대로).\
  ★ **공짜로 만드는 유일한 형태는 `a.AsSpan()[1..^1]`** — `AsSpan()` 이 **먼저** 와야 한다.
- ★★ **`a[..]` 가 +48이고 `ReferenceEquals` 가 `False`** 다. **「전체 범위」는 항등이 아니라 전체 복사**다.\
  ★ 뒤집어 읽으면 **배열을 복사하는 가장 짧은 문법**이 `a[..]` 다.
- ★★ **`a[2..2]` 가 +0 인 것은 언어 보장이 아니다.** 보장은 「빈 배열이 나온다」까지이고,\
  **새로 안 만들고 `Array.Empty<T>()` 를 준다는 것은 이 런타임의 구현**이다.
- ★★★ **루프에서 40000 대 0** 이다. 「배열 슬라이스가 비싸다」의 실체가 이 두 줄이다.\
  ★ 다만 **시간은 재지 않았다** — 이 문서가 근거로 쓴 것은 **바이트뿐**이다.

### 5. ★★ **`Length` 또는 `Count` + 인덱서**면 `^`, 거기에 **`Slice`** 가 있으면 `..`

**출력**

```text
===== 소스: cs09b-custom.cs =====
using System;
using System.Collections.Generic;

var bag = new Bag(new[] { 1, 2, 3, 4, 5 });
Console.WriteLine("Bag : Length + this[int] + Slice");
Console.WriteLine($"  bag[^1]    = {bag[^1]}");
Console.WriteLine($"  bag[1..^1] = {bag[1..^1]}");

var cnt = new Counted(new[] { 1, 2, 3, 4, 5 });
Console.WriteLine("Counted : Count + this[int] + Slice   ← Length 가 아니라 Count 다");
Console.WriteLine($"  cnt[^1]    = {cnt[^1]}");
Console.WriteLine($"  cnt[1..^1] = {cnt[1..^1]}");

var ex = new Explicit(new[] { 1, 2, 3, 4, 5 });
Console.WriteLine("Explicit : this[Index] · this[Range] 를 직접 받았다");
Console.WriteLine($"  ex[^2]   = {ex[^2]}");
Console.WriteLine($"  ex[1..3] = {ex[1..3]}");
Console.WriteLine($"  ex[2]    = {ex[2]}");

Console.WriteLine("List<int> : BCL 이 같은 계약을 만족하나?");
var list = new List<int> { 1, 2, 3, 4, 5 };
Console.WriteLine($"  List<int>.Slice 가 있나 : {typeof(List<int>).GetMethod("Slice") is not null}");
Console.WriteLine($"  list[^1]    = {list[^1]}");
var sub = list[1..^1];
Console.WriteLine($"  list[1..^1] = [{string.Join(", ", sub)}]  (타입 {sub.GetType().Name})");
sub[0] = -1;
Console.WriteLine($"  sub[0] = -1 뒤 list[1] = {list[1]}   ← 복사다");

class Bag {
    readonly int[] _items;
    public Bag(int[] items) => _items = items;
    public int Length => _items.Length;
    public int this[int i] => _items[i];
    public Bag Slice(int start, int length) => new Bag(_items[start..(start + length)]);
    public override string ToString() => "[" + string.Join(", ", _items) + "]";
}

class Counted {
    readonly int[] _items;
    public Counted(int[] items) => _items = items;
    public int Count => _items.Length;
    public int this[int i] => _items[i];
    public Counted Slice(int start, int length) => new Counted(_items[start..(start + length)]);
    public override string ToString() => "[" + string.Join(", ", _items) + "]";
}

class Explicit {
    readonly int[] _items;
    public Explicit(int[] items) => _items = items;
    public string this[Index i] => $"this[Index] 가 받았다 — {i} → {_items[i.GetOffset(_items.Length)]}";
    public string this[Range r] {
        get { var ol = r.GetOffsetAndLength(_items.Length); return $"this[Range] 가 받았다 — {r} → offset={ol.Offset} length={ol.Length}"; }
    }
}
===== csc -out:ex.dll cs09b-custom.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
Bag : Length + this[int] + Slice
  bag[^1]    = 5
  bag[1..^1] = [2, 3, 4]
Counted : Count + this[int] + Slice   ← Length 가 아니라 Count 다
  cnt[^1]    = 5
  cnt[1..^1] = [2, 3, 4]
Explicit : this[Index] · this[Range] 를 직접 받았다
  ex[^2]   = this[Index] 가 받았다 — ^2 → 4
  ex[1..3] = this[Range] 가 받았다 — 1..3 → offset=1 length=2
  ex[2]    = this[Index] 가 받았다 — 2 → 3
List<int> : BCL 이 같은 계약을 만족하나?
  List<int>.Slice 가 있나 : True
  list[^1]    = 5
  list[1..^1] = [2, 3, 4]  (타입 List`1)
  sub[0] = -1 뒤 list[1] = 2   ← 복사다
```

**왜 그런가**

- ★★★ **암묵 지원의 계약은 두 줄이다.**\
  `^` — **`int` 를 받는 인덱서** + **`Length` 또는 `Count` 라는 `int` 속성**.\
  `..` — 거기에 **`Slice(int start, int length)`**.
- ★★ **`Counted` 가 `Count` 만으로 둘 다 받았다.** 이름은 **둘 중 아무거나** 된다.\
  ★ **`Size` 는 안 된다**(7번의 `CS1503`). 계약이 **이름을 못 박은** 자리다.
- ★★ **명시 지원은 계약이 다르다** — `this[Index]`·`this[Range]` 를 직접 선언하면 `Slice` 가 필요 없다.\
  `Explicit` 에서 **`ex[2]` 도 `this[Index]` 로 갔다** — `int` → `Index` **암묵 변환**이 있기 때문이다.\
  ★ 그래서 `this[Index]` 를 달면 **기존 `this[int]` 호출까지 그쪽으로 끌려갈 수 있다**(오버로드가 둘이면 `int` 쪽이 더 잘 맞아 그쪽이 이긴다).
- ★★★ **`List<int>` 에 `Slice(int, int)` 가 있다**(`True`). 그래서 **`list[1..^1]` 이 컴파일되고**\
  결과 타입이 **`List<int>`** 다. ★★ **뷰가 아니라 복사**다 — `sub[0] = -1` 이 `list[1]` 을 안 바꿨다.
- ★★★ **「`List<T>` 는 범위 연산자가 안 된다」는 낡은 문장**이다. `List<T>.Slice` 는 **.NET 8부터**이고,\
  이 판(.NET 10.0.12 · 2026-09-25 확인)에서는 된다. **도구의 성질에는 판과 확인 날짜를 같이 적는다.**

### 6. **다차원은 객체 하나(+88), 배열의 배열은 객체 넷(+168)**

**출력**

```text
===== 소스: cs09b-dims.cs =====
using System;

Warm();

long b0 = GC.GetAllocatedBytesForCurrentThread();
int[,] md = new int[3, 4];
long b1 = GC.GetAllocatedBytesForCurrentThread();
int[][] jag = new int[3][];
for (int i = 0; i < 3; i++) jag[i] = new int[4];
long b2 = GC.GetAllocatedBytesForCurrentThread();
int[] flat = new int[12];
long b3 = GC.GetAllocatedBytesForCurrentThread();

md[1, 2] = 7;
jag[1][2] = 7;

Console.WriteLine($"new int[3,4]                  : +{b1 - b0} 바이트");
Console.WriteLine($"new int[3][] + int[4] 셋       : +{b2 - b1} 바이트");
Console.WriteLine($"new int[12]                   : +{b3 - b2} 바이트");
Console.WriteLine();
Console.WriteLine($"int[,]  : Rank={md.Rank} Length={md.Length} GetLength(0)={md.GetLength(0)} GetLength(1)={md.GetLength(1)}");
Console.WriteLine($"int[][] : Rank={jag.Rank} Length={jag.Length} jag[0].Length={jag[0].Length}");
Console.WriteLine($"md.GetType()  = {md.GetType()}");
Console.WriteLine($"jag.GetType() = {jag.GetType()}");
Console.WriteLine($"md[1,2]={md[1, 2]}   jag[1][2]={jag[1][2]}");
Console.WriteLine();

jag[2] = new int[7];
Console.WriteLine($"jag[2] = new int[7] 뒤 jag[2].Length = {jag[2].Length}   ← 줄마다 길이가 달라도 된다");
Console.WriteLine($"jag[^1].Length = {jag[^1].Length}   ← 바깥 배열에는 ^ 가 된다");
Console.WriteLine($"jag[0..2].Length = {jag[0..2].Length}   ← 바깥 배열에는 .. 도 된다");
Console.WriteLine();

int total = 0;
foreach (int v in md) total += v;
Console.WriteLine($"foreach (int v in md) 의 합 = {total}   ← int[,] 는 원소를 직접 준다");
Console.WriteLine($"md 의 원소 수 {md.Length} = 3 × 4");
foreach (int[] row in jag) Console.WriteLine($"  foreach (int[] row in jag) — row.Length = {row.Length}   ← 줄을 준다");

static void Warm() {
    int[,] w = new int[2, 2];
    int[][] wj = new int[2][];
    wj[0] = new int[2]; wj[1] = new int[2];
    int[] wf = new int[4];
    GC.KeepAlive(w); GC.KeepAlive(wj); GC.KeepAlive(wf);
    GC.GetAllocatedBytesForCurrentThread();
}
===== csc -out:ex.dll cs09b-dims.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
new int[3,4]                  : +88 바이트
new int[3][] + int[4] 셋       : +168 바이트
new int[12]                   : +72 바이트

int[,]  : Rank=2 Length=12 GetLength(0)=3 GetLength(1)=4
int[][] : Rank=1 Length=3 jag[0].Length=4
md.GetType()  = System.Int32[,]
jag.GetType() = System.Int32[][]
md[1,2]=7   jag[1][2]=7

jag[2] = new int[7] 뒤 jag[2].Length = 7   ← 줄마다 길이가 달라도 된다
jag[^1].Length = 7   ← 바깥 배열에는 ^ 가 된다
jag[0..2].Length = 2   ← 바깥 배열에는 .. 도 된다

foreach (int v in md) 의 합 = 7   ← int[,] 는 원소를 직접 준다
md 의 원소 수 12 = 3 × 4
  foreach (int[] row in jag) — row.Length = 4   ← 줄을 준다
  foreach (int[] row in jag) — row.Length = 4   ← 줄을 준다
  foreach (int[] row in jag) — row.Length = 7   ← 줄을 준다
```

**왜 그런가**

| | `int[3,4]` | `int[3][]` | `int[12]` |
|---|---|---|---|
| 할당 | **+88** | **+168** | **+72** |
| 객체 수 | **1** | **4**(바깥 1 + 줄 3) | **1** |
| `Rank` | **2** | **1** | 1 |
| `Length` | **12**(전체 원소) | **3**(줄 수) | 12 |
| `foreach` | **원소**(`int`) | **줄**(`int[]`) | 원소 |
| 줄마다 다른 길이 | 불가능 | ★ **가능** | — |
| `^`·`..` | ★★ **못 쓴다**(7번) | ★ 바깥 배열에는 된다 | 된다 |

- ★★ **+168 이 +88 의 약 두 배**인 것은 **객체 헤더를 네 번 내기 때문**이다.\
  원소 수는 12로 같은데 그릇이 넷이라 헤더·길이 칸이 네 벌 든다.
- ★ **평평한 `int[12]` 가 +72 로 가장 싸다.** 「행 × 열 + 열」을 손으로 계산해 쓰는 방식이\
  **메모리로는 항상 이긴다** — 대신 인덱스 계산의 실수를 사람이 진다.
- ★ **`int[,]` 의 `Rank` 가 2** 이고 `Length` 가 **12**(전체 원소)인데,\
  **`int[][]` 의 `Rank` 는 1** 이고 `Length` 가 **3**(줄 수)이다. **`int[][]` 은 2차원 배열이 아니다.**
- ★ **`jag[^1]`·`jag[0..2]` 는 된다** — 바깥 배열은 그냥 `int[][]` 라는 1차원 배열이기 때문이다.
- ★ **`foreach` 가 주는 것이 다르다** — `int[,]` 는 **원소**(12번 돈다), `int[][]` 는 **줄**(3번 돈다).\
  그래서 `jag` 쪽은 **중첩 루프**가 필요하다.
- ★ **`jag[2] = new int[7]` 이 통한다** — 줄마다 길이가 달라도 되는 것이 배열의 배열을 고르는 **유일한 이유**다.\
  ★ 대가는 **`jag[0]` 이 널일 수 있다**는 실패 모드다(`int[,]` 에는 없다).

### 7. **`CS1503` 둘 · `CS0021` · `CS0029` 둘 · `CS0022`** — 무엇이 없어서인지가 다 다르다

**출력**

```text
===== 소스: cs09b-nolength.cs =====
using System;
using System.Collections.Generic;

var sz = new SizeOnly();
Console.WriteLine(sz[^1]);

var nosl = new NoSlice();
Console.WriteLine(nosl[^1]);
Console.WriteLine(nosl[1..^1]);

var set = new HashSet<int> { 1, 2, 3 };
Console.WriteLine(set[^1]);

class SizeOnly {
    public int Size => 3;
    public int this[int i] => i;
}

class NoSlice {
    public int Length => 3;
    public int this[int i] => i;
}
===== csc -out:ex.dll cs09b-nolength.cs (cc exit=1) =====
cs09b-nolength.cs(5,22): error CS1503: Argument 1: cannot convert from 'System.Index' to 'int'
cs09b-nolength.cs(9,24): error CS1503: Argument 1: cannot convert from 'System.Range' to 'int'
cs09b-nolength.cs(12,19): error CS0021: Cannot apply indexing with [] to an expression of type 'HashSet<int>'
```

```text
===== 소스: cs09b-dimsfail.cs =====
using System;

int[,] md = new int[3, 4];
Console.WriteLine(md[^1, 0]);
Console.WriteLine(md[0..1, 0]);
Console.WriteLine(md[^1]);

int[][] jag = new int[3][];
Console.WriteLine(jag[^1]);
===== csc -out:ex.dll cs09b-dimsfail.cs (cc exit=1) =====
cs09b-dimsfail.cs(4,22): error CS0029: Cannot implicitly convert type 'System.Index' to 'int'
cs09b-dimsfail.cs(5,22): error CS0029: Cannot implicitly convert type 'System.Range' to 'int'
cs09b-dimsfail.cs(6,19): error CS0022: Wrong number of indices inside []; expected 2
```

**왜 그런가**

| 진단 | 어디서 | 무엇이 없어서 |
|---|---|---|
| `CS1503`(`Index` → `int`) | `sz[^1]` | ★ `Size` 는 `Length`·`Count` 가 **아니다** |
| `CS1503`(`Range` → `int`) | `nosl[1..^1]` | ★ `Slice(int, int)` 가 없다(`^` 는 됐다) |
| `CS0021` | `set[^1]` | `HashSet<T>` 에 **인덱서가 아예 없다** |
| `CS0029`(`Index` → `int`) | `md[^1, 0]` | ★★ 다차원 인덱서는 **`int` 를 직접 받는 언어 기능** |
| `CS0029`(`Range` → `int`) | `md[0..1, 0]` | 〃 |
| `CS0022` | `md[^1]` | **차원 수**가 먼저 걸린다 |

- ★★ **`CS1503`(인자 변환 실패)과 `CS0029`(암묵 변환 없음)가 갈리는 이유**는 **무엇이 인덱싱을 하느냐**다.\
  사용자 타입의 `this[int]` 는 **메서드처럼 인자 해석**을 하므로 `CS1503` 이고,\
  배열의 다차원 인덱싱은 **언어에 박힌 연산**이라 **변환 실패**(`CS0029`)로 난다.
- ★ **`nosl[^1]` 은 진단에 없다** — `Length` 와 인덱서가 있으니 `^` 는 성립한다.\
  **`..` 만 안 되는 자리**가 실제로 있다는 뜻이고, 그래서 계약을 **두 줄로 나눠 외워야** 한다(5번).
- ★ **`jag[^1]` 도 진단에 없다** — 배열의 배열은 **바깥이 1차원 배열**이라 (5)의 계약이 아니라 **배열 규칙**이 적용된다.
- ★★ **`md[^1]` 이 `CS0022`** 인 것은 **차원 수 검사가 먼저**라는 뜻이다.\
  ★ 「인덱스 타입이 틀렸다」와 「인덱스 개수가 틀렸다」는 **다른 단계**에서 잡힌다.
- ★ **`HashSet<T>` 의 `CS0021` 은 성질이 다르다** — 나머지는 「계약을 덜 갖췄다」이고 이것은\
  **「순서가 없어 걸 자리가 없다」다**. 집합에 「끝에서 첫 번째」라는 개념이 없다(목록의 **10번 주제**).

### 8. ★★ **`^` 는 산술로, `..` 는 세 메서드로** 풀린다

**출력**

```text
===== 소스: cs09b-il.cs =====
Il.Dump(typeof(Probe), "ArrIndex");
Il.Dump(typeof(Probe), "ArrRange");
Il.Dump(typeof(Probe), "SpanRange");
Il.Dump(typeof(Probe), "StrRange");

static class Probe {
    public static int    ArrIndex(int[] a) => a[^1];
    public static int[]  ArrRange(int[] a) => a[1..^1];
    public static System.Span<int> SpanRange(System.Span<int> s) => s[1..^1];
    public static string StrRange(string s) => s[1..^1];
}
===== csc -r:il.dll -out:ex.dll cs09b-il.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
--- Probe.ArrIndex ---
  IL_0000: ldarg.0
  IL_0001: dup
  IL_0002: ldlen
  IL_0003: conv.i4
  IL_0004: ldc.i4.1
  IL_0005: sub
  IL_0006: ldelem.i4
  IL_0007: ret
--- Probe.ArrRange ---
  IL_0000: ldarg.0
  IL_0001: ldc.i4.1
  IL_0002: call System.Index::op_Implicit
  IL_0007: ldc.i4.1
  IL_0008: ldc.i4.1
  IL_0009: newobj System.Index::.ctor
  IL_000e: newobj System.Range::.ctor
  IL_0013: call System.Runtime.CompilerServices.RuntimeHelpers::GetSubArray
  IL_0018: ret
--- Probe.SpanRange ---
  .locals [0] System.Span`1[[System.Int32, System.Private.CoreLib, Version=10.0.0.0, Culture=neutral, PublicKeyToken=7cec85d7bea7798e]]&
  IL_0000: ldarga.s 0
  IL_0002: stloc.0
  IL_0003: ldloc.0
  IL_0004: ldc.i4.1
  IL_0005: ldloc.0
  IL_0006: call System.Span<System.Int32>::get_Length
  IL_000b: ldc.i4.1
  IL_000c: sub
  IL_000d: ldc.i4.1
  IL_000e: sub
  IL_000f: call System.Span<System.Int32>::Slice
  IL_0014: ret
--- Probe.StrRange ---
  .locals [0] System.String
  IL_0000: ldarg.0
  IL_0001: stloc.0
  IL_0002: ldloc.0
  IL_0003: ldc.i4.1
  IL_0004: ldloc.0
  IL_0005: callvirt System.String::get_Length
  IL_000a: ldc.i4.1
  IL_000b: sub
  IL_000c: ldc.i4.1
  IL_000d: sub
  IL_000e: callvirt System.String::Substring
  IL_0013: ret
```

**왜 그런가**

| 소스 | 핵심 IL | 무엇을 뜻하나 |
|---|---|---|
| `a[^1]` | `dup` → `ldlen` → `conv.i4` → `ldc.i4.1` → `sub` → `ldelem.i4` | ★★★ **`Index` 가 안 만들어진다** |
| `a[1..^1]` | ★★★ `RuntimeHelpers::GetSubArray` | **복사** |
| `span[1..^1]` | ★★★ `Span<System.Int32>::Slice` | **뷰** |
| `str[1..^1]` | ★★★ `String::Substring` | **복사** |

- ★★★ **`a[^1]` 의 IL 에 `Index` 가 한 번도 안 나온다.** `dup; ldlen; conv.i4; ldc.i4.1; sub; ldelem.i4` —\
  **배열 길이를 읽어 빼는 산술**로 완전히 풀렸다(이것을 **로워링**이라 한다).\
  ★ 그래서 4번에서 `a[^1]` 이 **+0바이트**였다. 「`Index` 라는 타입이 있다」(2번)와\
  **「런타임에 그 타입이 쓰인다」는 다른 문장**이다.
- ★★ **`a[1..^1]` 에는 `newobj System.Index::.ctor` 와 `newobj System.Range::.ctor` 가 있다.**\
  ★ 둘 다 **구조체**라 힙 할당이 아니다 — 4번의 +40은 **`GetSubArray` 가 만든 배열 몫**이다.
- ★★★ **같은 `[1..^1]` 이 받는 쪽에 따라 세 메서드로 갈린다.** 이것이 4번 바이트 차이의 **원인**이다 —\
  `GetSubArray` 는 **새 배열을 만들어 복사**하고, `Span<T>.Slice` 는 **필드 셋을 다시 채울** 뿐이며,\
  `String.Substring` 은 **새 문자열**을 만든다.
- ★ **`Span` 쪽에는 `Range` 객체도 안 만들어진다** — 컴파일러가 `Slice(start, length)` 를 **미리 계산해** 넘긴다\
  (`get_Length` → `sub` → `sub` 가 그 계산이다).
- ★★ **이 절의 값어치**는 여기 있다 — **소스에는 `Copy` 라는 글자가 한 번도 없는데 IL 에는 있다.**\
  「여기서 복사가 나나?」는 IL 을 보면 **추측이 필요 없다.**

### 9. ★★ **`..` 가 `-` 보다 세게 묶는다** — 근거는 진단이 가리키는 열이다

**출력**

```text
===== 소스: cs09b-prec.cs =====
using System;

string s = "x";
var a = 0..1 - s;
var b = (0..1) - s;
var c = 0..(1 - s);
var d = ^1 - s;
var e = ^(1 - s);

int[] arr = { 10, 20, 30, 40, 50 };
var f = arr[1..arr.Length - 1];
Console.WriteLine($"{a} {b} {c} {d} {e} {f}");
===== csc -out:ex.dll cs09b-prec.cs (cc exit=1) =====
cs09b-prec.cs(4,9): error CS0019: Operator '-' cannot be applied to operands of type 'Range' and 'string'
cs09b-prec.cs(5,9): error CS0019: Operator '-' cannot be applied to operands of type 'Range' and 'string'
cs09b-prec.cs(6,13): error CS0019: Operator '-' cannot be applied to operands of type 'int' and 'string'
cs09b-prec.cs(7,9): error CS0019: Operator '-' cannot be applied to operands of type 'Index' and 'string'
cs09b-prec.cs(8,11): error CS0019: Operator '-' cannot be applied to operands of type 'int' and 'string'
cs09b-prec.cs(11,13): error CS0019: Operator '-' cannot be applied to operands of type 'Range' and 'int'
```

**왜 그런가**

| 소스 | 열 | 피연산자 타입 | 어떻게 묶였나 |
|---|---|---|---|
| `0..1 - s` | **9** | `Range` 와 `string` | ★★★ **`(0..1) - s`** |
| `(0..1) - s` | **9** | `Range` 와 `string` | 괄호와 **결과가 같다** |
| `0..(1 - s)` | **13** | `int` 와 `string` | 괄호로 강제해야 이렇게 된다 |
| `^1 - s` | **9** | `Index` 와 `string` | **`(^1) - s`** |
| `^(1 - s)` | **11** | `int` 와 `string` | 괄호로 강제해야 이렇게 된다 |
| ★★ `arr[1..arr.Length - 1]` | **13** | ★★★ `Range` 와 `int` | **`(1..arr.Length) - 1`** |

- ★★★ **진단 문구는 여섯 줄이 전부 같은 형식**(`CS0019: Operator '-' cannot be applied to …`)이고,\
  **갈리는 것은 열과 피연산자 타입뿐**이다. **값으로는 원리상 못 가른다** — 어느 쪽으로 묶어도\
  「컴파일이 안 된다」는 같기 때문이다. **일부러 에러를 내고 열을 읽는 것**이 유일한 증명이다.
- ★★★ **`0..1 - s` 의 열이 9(=`0` 자리)이고 타입이 `Range`** 라는 것은 **`..` 가 먼저 묶였다**는 뜻이다.\
  `(0..1) - s` 와 **열·타입·문구가 한 글자도 같다** — 괄호를 친 것과 파싱 결과가 같다는 증명이다.\
  ★ 반대로 `0..(1 - s)` 는 열이 **13**(=`1` 자리)이고 타입이 **`int`** 다. **괄호가 있어야 그렇게 된다.**
- ★★★ **실전의 귀결** — `arr[1..arr.Length - 1]` 이 **컴파일되지 않는다**(`Range` 에서 `int` 를 빼라가 된다).\
  ★ 고치는 법은 괄호(`arr[1..(arr.Length - 1)]`)이지만, **더 나은 답은 `arr[1..^1]`** 이다 —\
  `^` 가 있는 이유가 바로 **길이에서 빼는 산술을 안 쓰게** 하는 것이다.
- ★ **`^` 는 단항이라 더 세게 묶는다** — `^1 - s` 가 `Index` 와 `string` 의 뺄셈이 됐다(열 9).
- ★★ **Learn 의 연산자 우선순위표에서 `x..y` 가 곱셈·덧셈보다 위**에 있다. 이 여섯 줄이 그 표의 실증이다.

### 10. **읽기만 하면 뷰, 보관하면 복사** — 그리고 `Span` 이 못 가는 자리가 있다

**답**

| 상황 | 고를 것 | 근거 |
|---|---|---|
| 부분을 **읽기만** 하고 루프가 돈다 | ★★★ `a.AsSpan()[1..^1]` | **0바이트**(4번) |
| 부분을 **떼어 보관**한다 | `a[1..^1]` | 원본이 바뀌어도 따라 바뀌면 안 된다 |
| 부분을 **필드·`async`·`yield`** 에 담는다 | `a[1..^1]` 또는 `Memory<T>` | ★ `Span<T>` 는 **거기 못 들어간다** |
| 마지막 원소 | `a[^1]` | 할당 0(4번) · `Length - 1` 보다 덜 틀린다 |
| 배열 전체 복사 | `a[..]` · `Clone()` · `Array.Copy` | 셋 다 **얕은 복사**다 |
| 격자, 줄 길이 같음 | `int[,]` | 객체 **하나**(6번) |
| 격자, 줄 길이 다름 | `int[][]` | 다차원으로는 표현 불가 |
| 크기가 변한다 | `List<T>` | **배열은 크기 고정** — 목록의 **10번 주제** |

- ★★★ **`Span<T>` 를 못 쓰는 자리** — **클래스의 필드** · **`async` 메서드의 `await` 를 건너는 지역변수** ·\
  **`yield return` 이 있는 메서드** · **람다가 캡처하는 변수** · **제네릭 타입 인자**(`List<Span<int>>`).\
  전부 **「힙으로 탈출할 수 있는 자리」라는 한 가지 이유**다(목록의 **46번 주제**가 정본).\
  ★ 그래서 **`Span<T>` 는 「메서드 안에서 잠깐」 쓰는 도구**이지 저장 형식이 아니다.
- ★ **`a[..]` 와 `Clone()` 과 `Array.Copy` 의 차이** — `a[..]` 는 **범위를 골라 복사**할 수 있고,\
  `Clone()` 은 **전체만**(그리고 `object` 를 돌려줘 캐스트가 필요하다), `Array.Copy` 는 **이미 있는 배열에** 채운다\
  (**새 할당 없이** 재사용할 수 있는 유일한 형태다).
- ★ **`int[,]` 대 `int[][]` 의 기준 셋** — ① **줄 길이가 같은가** ② **메모리·캐시가 중요한가**\
  ③ **줄 하나를 따로 넘길 일이 있는가**(`int[][]` 은 `jag[0]` 을 그냥 `int[]` 로 넘긴다 — `int[,]` 는 못 한다).

### 11. **Rust 는 기본이 뷰, C# 은 기본이 복사** — 기본값이 반대다

**답**

| | Rust | Python | Go | C# |
|---|---|---|---|---|
| 부분을 얻는 문법 | `&v[1..4]` | `a[1:4]` | `s[1:4]` | `a[1..4]` |
| 그 결과 | ★ **슬라이스(뷰)** | ★ **새 리스트(복사)** | ★ **슬라이스(뷰)** | ★ **새 배열(복사)** |
| 반대를 얻으려면 | `.to_vec()` | `a[1:4]` 가 이미 복사 | `append([]T{}, s...)` | ★ **`AsSpan()`** 을 먼저 |
| 끝에서 세기 | `v[v.len()-1]` | ★ **`a[-1]`** | `s[len(s)-1]` | ★ **`a[^1]`** |
| 끝 기준의 정체 | — | ★ **같은 `int` 에 음수** | — | ★★ **`Index` 라는 다른 타입** |

- ★★★ **Rust 와 C# 의 `..` 는 글자만 같고 기본값이 반대다.** Rust 의 `&v[1..4]` 는 **복사가 없고**\
  복사하려면 `.to_vec()` 을 붙인다. C# 의 `a[1..4]` 는 **복사이고** 뷰를 얻으려면 `AsSpan()` 을 붙인다.\
  ★ **Rust 에서 넘어오면 4번의 +40 에서, C# 에서 Rust 로 가면 수명 에러에서 걸린다.**
- ★★★ **Python 의 `a[-1]` 과 C# 의 `a[^1]` 은 층위가 다르다.** 파이썬은 **`int` 자리에 음수를 넣는 것**이라\
  인덱스가 **런타임에 음수인지 검사**된다. C# 은 **`Index` 라는 별도 타입**이고(2번)\
  배열에서는 **컴파일 시점에 `Length - n` 산술로 풀린다**(8번). ★ **C# 에서 `a[-1]` 은 음수로 해석되지 않고\
  그냥 범위 밖이라 `IndexOutOfRangeException`** 이다 — 3번과 같은 예외다.
- ★★ **Go 의 「배열」은 C# 의 「배열」과 다른 물건**이다. Go 의 `[5]int` 는 **값 타입**이라 대입하면 복사되고,\
  일상에서 쓰는 것은 **슬라이스**(포인터·len·cap 헤더)다. C# 은 **배열이 참조 타입**(1번)이고\
  **`Span<T>` 가 그 헤더에 해당**한다. ★ 즉 **Go 슬라이스 ≈ C# `Span<T>`** 이고 **Go 배열 ≈ C# 고정 크기 구조체**다.
- ★ **Python 의 `a[1:4]` 가 복사인 것은 C# 과 같다** — 두 언어 다 **뷰를 쓰려면 다른 타입**을 부른다\
  (파이썬은 `memoryview`, C# 은 `Span<T>`).

### 12. ★ 배열이 **참조 타입**이라서 뷰가 성립하고, `Span` 이 **구조체**라서 0바이트다

**답**

- ★★★ **4번의 뷰가 성립하는 전제가 1번이다.** `Span<int>` 가 드는 것은 **원본 배열을 가리키는 참조 + 시작 + 길이**다.\
  배열이 **힙에 있는 독립 객체**([01번](../01-value-types-and-reference-types/))라서 그 참조가 유효하고,\
  **원본이 살아 있는 한 뷰가 가리키는 데이터도 살아 있다**(GC 가 span 을 통해서도 배열을 붙잡는다).
- ★★★ **`Span<T>` 가 구조체라서 +0** 이다. `Span<int> view = …` 가 힙을 안 쓴 것은\
  **span 자체가 스택에 놓이는 값**이기 때문이다([01번](../01-value-types-and-reference-types/)의 값 타입).\
  ★ 「뷰라서 0」이 아니라 **「뷰를 담는 그릇이 값 타입이라서 0」이다** — 한 겹 더 들어가야 맞는 설명이다.
- ★★ **이 주제에서 박싱은 한 번도 안 났다.** `Index`·`Range`·`Span<T>` 가 전부 구조체인데\
  **`object`·인터페이스로 올린 자리가 없기** 때문이다([03번](../03-boxing-and-unboxing/)).\
  ★ 반대로 **`foreach (object o in arr)`** 처럼 쓰면 원소마다 박싱이 난다 — 이 문서는 그렇게 쓰지 않았다.
- ★★ **증분으로만 읽는 이유** — `GC.GetAllocatedBytesForCurrentThread()` 는 **프로세스 시작부터의 누적**이라\
  절댓값이 매 실행 다르다. 두 호출 사이의 **차이**만 안 흔들린다([03번](../03-boxing-and-unboxing/)에서 굳힌 규칙이다).\
  ★ 그리고 **워밍업을 먼저 돌린다** — 첫 호출에서 타입 초기화·JIT 가 섞여 들어오기 때문이다.

## 실행 검증

**무엇을 몇 번 어느 판에서 돌렸나** — 아래 블록은 전부 **.NET SDK 10.0.401 / 런타임 10.0.12 / `net10.0` / linux-x64** 에서\
캡처 스크립트로 받았다. **제출 직전에 전부 다시 돌려 정규화 대조했다.**

| 블록 | 무엇을 고정하나 | 명령 |
|---|---|---|
| `cs09b-ref.cs` | 배열이 **참조 타입** · 대입·인자 전달이 원본을 바꾸는 것 · `new string[2]` 가 널 | `csc` + 실행 |
| `cs09b-index.cs` | ★★ `Index`·`Range` 가 **구조체** · **`^0.GetOffset(5) == 5`** · `a[2..2]` 가 빈 배열 | 〃 |
| `cs09b-end0.cs` | `IndexOutOfRangeException` 전문 · **`cc exit=0 · run exit=134`** | 〃 |
| `cs09b-alloc.cs` | ★★★ **+40 대 +0** · `a[..]` 가 +48 · 빈 범위 +0 · **`Span` 에 받아도 +40** · 1000번 40000 대 0 | 〃 |
| `cs09b-il.cs` | ★★★ `GetSubArray` · `Span<T>::Slice` · `String::Substring` · **`^` 가 IL 에 없는 것** | `csc -r:il.dll` + 실행 |
| `cs09b-custom.cs` | ★★ `Count` 로도 되는 것 · `this[Index]`/`this[Range]` · **`List<T>.Slice` 가 있는 것** | `csc` + 실행 |
| `cs09b-nolength.cs` | `CS1503` 둘 · `CS0021` | `csc` 만(`cc exit=1`) |
| `cs09b-dims.cs` | ★ **+88 대 +168 대 +72** · `Rank`·`Length` · `foreach` 가 주는 것 | `csc` + 실행 |
| `cs09b-dimsfail.cs` | `CS0029` 둘 · `CS0022` | `csc` 만(`cc exit=1`) |
| `cs09b-prec.cs` | ★★★ **`(행,열)` 여섯 줄** — `..` 가 `-` 보다 세게 묶는 증거 | 〃 |

**구현 의존 항목** — 다음은 **이 환경(.NET 10.0.12 · CoreCLR · x64 linux)에서만** 그렇다.

- ★★ **+40 · +48 · +32 · +72 · +88 · +168** — 객체 헤더 16과 배열 길이 칸 8, 정렬 규칙이 x64 CoreCLR 의 값이다.\
  ★★★ **「+0 이냐 아니냐」는 언어·타입 계약이고 「정확히 얼마」는 관찰이다.** 갈라 읽어라.
- ★★ **빈 범위 `a[2..2]` 가 +0** — **`Array.Empty<T>()` 재사용은 런타임 구현**이다.\
  언어가 보장하는 것은 「빈 배열이 나온다」까지다.
- **IL 의 명령 열** — 로워링 형태는 Roslyn 이 고른다. ★ `-optimize` 를 **안 줬다**.\
  **`GetSubArray`/`Slice`/`Substring` 로 갈린다는 사실 자체는 언어 명세가 정한 번역**이다.
- **예외 메시지 문구**·**종료 코드 134**·**`List<T>.Slice` 의 존재**(.NET 8부터라 이전 판에서는 5번이 다르다).

**언어가 보장하는 것**(구현이 바뀌어도 같다)

- **배열이 참조 타입이고 `System.Array` 를 상속하는** 것 · **원소가 `default` 로 채워지는** 것.
- **`^n` 이 `Length - n` 이고 `^0` 이 길이와 같은** 것 · **범위의 끝을 포함하지 않는** 것.
- **배열·`string` 의 `..` 가 새 것을 만들고, `Span<T>`·`ReadOnlySpan<T>` 의 `..` 가 뷰인** 것.
- **`Length`/`Count` + 인덱서면 `^`, 거기에 `Slice` 가 있으면 `..` 가 되는** 것 · **`this[Index]`/`this[Range]` 가 우선하는** 것.
- **다차원 배열 `int[,]` 에 `^`·`..` 가 없는** 것 · **`int[][]` 의 `Rank` 가 1인** 것.
- ★★ **`..` 가 `+`·`-`·`*` 보다 세게 묶는** 것(연산자 우선순위표).

**안 돌려 본 것 / 못 잰 것**

- **안 돌려 본 것** — **시간**(이 문서는 **바이트와 명령만** 쟀다) · **`Memory<T>`·`ArraySegment<T>`**(46번 주제) ·\
  **`stackalloc`** · **3차원 이상 배열**(`int[,,]`) · **가변 하한 배열**(`Array.CreateInstance` 로 만드는 것) ·\
  **배열 공변성**(`object[] o = new string[2]` 이 런타임에 던지는 것) · **`Span<T>` 를 필드에 두면 나는 진단**(**던져서 확인 안 했다**) ·\
  **`-optimize` 를 켠 IL** · **32비트 런타임에서의 바이트 수** · **`List<T>` 말고 다른 BCL 타입의 `Slice`**.
- **못 잰 것** — ★★ **「`Span` 이 배열 슬라이스보다 얼마나 빠른가」.**\
  잰 것은 **할당 바이트**이고 **시간이 아니다.** ★ 그래서 이 문서는 **「빠르다」를 한 번도 적지 않았다** —\
  적은 것은 「**0바이트**」와 「**객체를 안 만든다**」뿐이다.
- ★ **`int[,]` 가 캐시에 유리하다는 주장도 안 적었다** — 그것은 **재야 할 것**이고, 잰 것은 **객체 수와 바이트**뿐이다.

**버전이 올랐을 때 다시 돌려야 하는 것**

- ★★ **4번·6번의 바이트 수** — 객체 레이아웃이 바뀌면 움직인다. **`+0` 인 칸들은 안 움직인다.**
- ★★ **5번의 `List<T>.Slice`** — BCL 이 다른 타입에도 `Slice` 를 더하면 **컴파일되는 범위가 넓어진다.**\
  ★ **없어지지는 않는다**(호환성) — 그래서 **다시 돌릴 때 봐야 할 것은 「늘었나」다**.
- ★ **8번의 IL** — Roslyn 이 바뀌면 명령이 움직인다. **세 메서드로 갈린다는 사실은 안 움직인다.**
- ★ **9번** — 연산자 우선순위는 **언어 규칙**이라 안 움직인다. 움직이면 그것은 **언어가 바뀐 것**이다.
