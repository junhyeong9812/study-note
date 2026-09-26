# csharp/syntax/01 — 값 타입과 참조 타입 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> **기준 소스** — [ECMA-334 7판(2023-12)](https://ecma-international.org/publications-and-standards/standards/ecma-334/) · [Microsoft Learn — C# 언어 레퍼런스](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/) · [Learn — 값 형식](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/builtin-types/value-types) · [Learn — 참조 형식](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/keywords/reference-types) · [.NET API — `GC.GetAllocatedBytesForCurrentThread`](https://learn.microsoft.com/en-us/dotnet/api/system.gc.getallocatedbytesforcurrentthread)
> **실행 검증** — 이 문서의 모든 출력·진단·IL·할당 바이트는 **.NET SDK 10.0.401** ·\
> 런타임 **`.NET 10.0.12`**(`Microsoft.NETCore.App`) · 타겟 **`net10.0`** · **linux-x64** 에서 실제로 돌려 얻은 것이다(2026-09-24).\
> ★ 블록은 캡처 스크립트가 파일로 받아 조립기가 끼워 넣은 것이다 — 사람이 옮겨 적은 줄은 하나도 없다.
> **읽는 법** — `GC.GetAllocatedBytesForCurrentThread()` 의 **절댓값은 흔들리는 칸**이다.\
> 근거로 쓰는 것은 **두 호출 사이의 증분**과 **그 증분이 0 이냐 아니냐**다.\
> 진단을 싣는 블록에는 **그 진단을 낸 소스를 같은 자리에** 뒀다 — 줄 번호가 발췌와 어긋나지 않게 하기 위해서다.\
> **`-debug` 를 안 줘서** 예외 트레이스에 절대 경로가 없다. 자세한 환경은 [2-summary.md](2-summary.md) 머리말에 있다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ 구조체는 원본이 안 바뀌고 클래스는 바뀐다 — `s1.X=1` · `c1.X=99`

**출력**

```text
===== 소스: cs01b-copy.cs =====
using System;

var s1 = new Point { X = 1, Y = 2 };
var s2 = s1;                       // 구조체 대입
s2.X = 99;

var c1 = new Node { X = 1, Y = 2 };
var c2 = c1;                       // 클래스 대입
c2.X = 99;

Console.WriteLine($"struct : s1.X={s1.X}  s2.X={s2.X}");
Console.WriteLine($"class  : c1.X={c1.X}  c2.X={c2.X}");

BumpStruct(s1);
BumpClass(c1);
Console.WriteLine($"인자 전달 뒤 : s1.X={s1.X}  c1.X={c1.X}");

Console.WriteLine($"ReferenceEquals(c1, c2) : {ReferenceEquals(c1, c2)}");
Console.WriteLine($"c1.Equals(c2)           : {c1.Equals(c2)}");
Console.WriteLine($"s1.Equals(s2)           : {s1.Equals(s2)}");
var s3 = s1;
Console.WriteLine($"s1.Equals(s3)           : {s1.Equals(s3)}");

static void BumpStruct(Point p) { p.X = 1000; }
static void BumpClass(Node n) { n.X = 1000; }

struct Point { public int X; public int Y; }
class Node { public int X; public int Y; }
===== csc -out:ex.dll cs01b-copy.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
struct : s1.X=1  s2.X=99
class  : c1.X=99  c2.X=99
인자 전달 뒤 : s1.X=1  c1.X=1000
ReferenceEquals(c1, c2) : True
c1.Equals(c2)           : True
s1.Equals(s2)           : False
s1.Equals(s3)           : True
```

**왜 그런가**

| 쓴 것 | 복사된 것 | 결과 |
|---|---|---|
| `var s2 = s1;` | ★ **`Point` 값 8바이트 전체** | `s2` 는 **따로 산다** — `s1.X` 는 `1` |
| `var c2 = c1;` | **참조 8바이트** | **같은 객체**를 본다 — `c1.X` 가 `99` |
| `BumpStruct(s1)` | 값 전체(복사본) | 메서드 안의 `p.X = 1000` 이 **안 돌아온다** |
| `BumpClass(c1)` | 참조(복사본) | 참조가 **같은 객체**를 가리켜 `c1.X` 가 `1000` |

- ★★★ **선언 한 줄(`struct` 냐 `class` 냐)이 결과를 뒤집는다.** 본문 코드는 한 글자도 다르지 않다.
- ★★ **`ReferenceEquals(c1, c2)` 가 `True`** 인 것이 위 결과의 직접 증거다 — **객체가 하나**다.
- ★★ **`Equals` 가 타입마다 다른 기준으로 답한다.**\
  `s1.Equals(s2)` 는 **`False`**(값이 다르다 — `X` 가 `1` 대 `99`),\
  `s1.Equals(s3)` 는 **`True`**(`s3` 는 손대지 않은 복사본이라 값이 같다).\
  `c1.Equals(c2)` 의 `True` 는 **값이 같아서가 아니라 같은 객체여서**다.
  - 구조체는 `ValueType.Equals` 가 **필드 값을 비교**하고, 클래스는 `object.Equals` 가 **참조를 비교**한다.
  - ★ 그 기본 구현의 **대가**는 [02번](../02-struct-vs-class-choosing/)의 (5)에서 잰다 — **참조 필드가 있으면 40배 느렸다.**
  - ★ 동등성 규칙의 정본은 목록의 **19번 주제**다.
- ★ **「C# 은 항상 값 전달이다」가 정확한 문장**이다. 참조 타입에서 전달되는 「값」이 **참조**일 뿐이다.

### 2. ★★ `ref` 는 변수 자체를 넘긴다 — `ByValue` 로는 안 바뀐다

**출력**

```text
===== 소스: cs01b-refoutin.cs =====
using System;

var p = new Point { X = 1 };
var n = new Node { X = 1 };

ByRefStruct(ref p);
ByRefClass(ref n);
Console.WriteLine($"ref 뒤        : p.X={p.X}  n.X={n.X}");

Replace(ref n);
Console.WriteLine($"ref 재대입 뒤 : n.X={n.X}");

ByValue(n);
Console.WriteLine($"값 전달 재대입 뒤 : n.X={n.X}");

Out(out Point q);
Console.WriteLine($"out           : q.X={q.X}");

var big = new Point { X = 7 };
Console.WriteLine($"in 으로 읽기  : {ReadOnly(in big)}");

static void ByRefStruct(ref Point p) { p.X = 42; }
static void ByRefClass(ref Node n) { n.X = 42; }
static void Replace(ref Node n) { n = new Node { X = 777 }; }
static void ByValue(Node n) { n = new Node { X = -1 }; }
static void Out(out Point p) { p = new Point { X = 5 }; }
static int ReadOnly(in Point p) { return p.X; }

struct Point { public int X; }
class Node { public int X; }
===== csc -out:ex.dll cs01b-refoutin.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
ref 뒤        : p.X=42  n.X=42
ref 재대입 뒤 : n.X=777
값 전달 재대입 뒤 : n.X=777
out           : q.X=5
in 으로 읽기  : 7
```

**왜 그런가**

| 한정자 | 넘기는 것 | 호출 전 대입 | 안에서 할 수 있는 것 |
|---|---|---|---|
| (없음) | 값의 **복사본** | 필요 | 원본에 안 닿는다 |
| **`ref`** | ★ **변수가 놓인 자리** | 필요 | 읽기·쓰기·**재대입** |
| **`out`** | 〃 | ★ **불필요** | ★ **반드시 대입**해야 한다 |
| **`in`** | 〃 | 필요 | ★ **읽기만** |

- ★★★ **`Replace(ref n)` 뒤 `n.X=777`, `ByValue(n)` 뒤에도 `n.X=777`.**\
  `ByValue` 안에서 `n = new Node { X = -1 }` 을 했는데 밖이 안 바뀐 것 —\
  안쪽의 `n` 은 **참조의 복사본**이라 거기 새 참조를 써도 밖으로 안 나간다.\
  ★★ **이 두 줄이 「참조 타입은 참조 전달이다」를 반증한다.**
- ★★ **참조 타입에 `ref` 를 붙이는 것은 의미가 있다** — 「가리키는 객체의 안을 바꾸는 것」(그건 `ref` 없이도 된다)과\
  「**변수가 가리키는 대상 자체를 갈아 끼우는 것**」(이건 `ref` 라야 된다)은 다른 일이다.
- ★ **`out` 이 `ref` 와 다른 점 둘** — ① 호출 전에 **대입돼 있지 않아도 된다**\
  ② 메서드가 **반드시 대입해야** 컴파일이 된다. 호출 자리에서 `out Point q` 로 **선언**하는 것은 C# 7.0부터다.
- ★ `in` 은 `ReadOnly(in big)` 에서 **7 을 읽었다** — 읽기는 된다. 쓰면 3번이 된다.

### 3. ★ 컴파일이 막힌다 — `error CS8332` · `readonly variable`

**출력**

```text
===== 소스: cs01b-in-write.cs =====
struct Point { public int X; }

class Program {
    static void Write(in Point p) { p.X = 9; }   // in 매개변수에 쓰기
    static void Main() { }
}
===== csc -out:ex.dll cs01b-in-write.cs (cc exit=1) =====
cs01b-in-write.cs(4,37): error CS8332: Cannot assign to a member of variable 'p' or use it as the right hand side of a ref assignment because it is a readonly variable
```

**왜 그런가**

- ★★★ 진단이 이유를 그대로 말한다 — ``because it is a readonly variable``.\
  **`in` 은 성능 최적화가 아니라 타입 수준의 약속**이고, 컴파일러가 그 약속을 **강제한다.**
- ★★ **`in` 을 붙였는데 오히려 복사가 느는 경우가 있다** — `readonly` 가 **아닌** 구조체를 `in` 으로 받으면\
  메서드를 부를 때마다 **방어적 복사**가 생긴다. **경고는 한 줄도 안 난다.**\
  ★ 정본은 [02번](../02-struct-vs-class-choosing/)의 (3)이고, 그 IL 에 `ldobj` 가 찍혀 있다.
- ★ `ref`/`out`/`in` 자체의 정본은 목록의 **44번 주제**다.

### 4. ★★ 에러 **둘** — 값 타입에는 「없음」이 없다

**출력**

```text
===== 소스: cs01b-null.cs =====
struct Point { public int X; }

class Program {
    static void Main() {
        int i = null;
        Point p = null;
        string s = null;
        object o = null;
        int? q = null;
        System.Console.WriteLine($"{i} {p} {s} {o} {q}");
    }
}
===== csc -out:ex.dll cs01b-null.cs (cc exit=1) =====
cs01b-null.cs(5,17): error CS0037: Cannot convert null to 'int' because it is a non-nullable value type
cs01b-null.cs(6,19): error CS0037: Cannot convert null to 'Point' because it is a non-nullable value type
cs01b-null.cs(1,27): warning CS0649: Field 'Point.X' is never assigned to, and will always have its default value 0
```

**왜 그런가**

| 쓴 것 | 결과 | 왜 |
|---|---|---|
| `int i = null;` | ★ **`error CS0037`** | 값 타입에는 **널을 담을 비트 조합이 없다** |
| `Point p = null;` | ★ **`error CS0037`** | 사용자 구조체도 같다 |
| `string s = null;` | **통과**(경고도 없다) | 참조 타입에는 **널 참조**가 있다 |
| `object o = null;` | **통과** | 〃 |
| `int? q = null;` | **통과** | `Nullable<int>` 가 **그 자리를 만들어 준다** |

- ★★★ 진단의 꼬리가 이유다 — ``because it is a non-nullable value type``.\
  **값 타입은 모든 비트 조합이 이미 어떤 값**이라 「없음」을 표현할 자리가 남지 않는다.
- ★★ **`string s = null;` 이 경고도 안 나는 것**은 이 문서가 **널 허용 참조 타입 분석을 안 켰기** 때문이다.\
  `#nullable enable`(또는 `-nullable:enable`)을 켜면 그제서야 경고가 난다 — 그 정본은 [목록의 **06번 주제**](../06-nullable-reference-types/)다.\
  ★ **널 허용 참조 타입은 런타임 타입이 아니라 컴파일러 분석**이다.
- ★ 경고 `CS0649`(「never assigned」)는 **질문과 무관한 잡음**이라 이 소스에서는 필드를 초기화해 지웠다.

### 5. ★★★ `string` 은 참조 타입이다 — `a == c` 는 참인데 `ReferenceEquals(a, c)` 는 거짓

**출력**

```text
===== 소스: cs01b-string.cs =====
using System;

string a = "hello";
string b = "hello";
string c = new string(['h', 'e', 'l', 'l', 'o']);
string d = a;

Console.WriteLine($"a == b                  : {a == b}");
Console.WriteLine($"a == c                  : {a == c}");
Console.WriteLine($"ReferenceEquals(a, b)   : {ReferenceEquals(a, b)}");
Console.WriteLine($"ReferenceEquals(a, c)   : {ReferenceEquals(a, c)}");
Console.WriteLine($"ReferenceEquals(a, d)   : {ReferenceEquals(a, d)}");

string e = a;
a = a.ToUpper();                 // 바꾼 것처럼 보이는 자리
Console.WriteLine($"a={a}  e={e}");
Console.WriteLine($"ReferenceEquals(a, e)   : {ReferenceEquals(a, e)}");

object boxed1 = 5;
object boxed2 = 5;
Console.WriteLine($"ReferenceEquals(5, 5)   : {ReferenceEquals(boxed1, boxed2)}");
===== csc -out:ex.dll cs01b-string.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
a == b                  : True
a == c                  : True
ReferenceEquals(a, b)   : True
ReferenceEquals(a, c)   : False
ReferenceEquals(a, d)   : True
a=HELLO  e=hello
ReferenceEquals(a, e)   : False
ReferenceEquals(5, 5)   : False
```

**왜 그런가**

| 줄 | 결과 | 왜 |
|---|---|---|
| `a == b` · `a == c` | **둘 다 `True`** | ★ `string` 이 **`==` 를 내용 비교로 오버로드**했다 |
| `ReferenceEquals(a, b)` | **`True`** | ★ 같은 **리터럴**은 **인터닝**돼 한 객체다 |
| `ReferenceEquals(a, c)` | ★★★ **`False`** | `new string(...)` 은 **새 객체**다 |
| `ReferenceEquals(a, d)` | **`True`** | `d = a` 는 **참조 복사**다 |
| `a = a.ToUpper()` 뒤 `e` | **`hello`** | ★★★ `string` 은 **불변** — 새 객체를 만들어 `a` 에 다시 대입한 것 |
| `ReferenceEquals(a, e)` | **`False`** | 그래서 둘은 **다른 객체**다 |
| `ReferenceEquals(5, 5)` | ★★ **`False`** | 박싱된 두 `int` 는 **다른 객체**다 |

- ★★★ **`a == c`(참)와 `ReferenceEquals(a, c)`(거짓)가 갈리는 것**이 「`string` 은 참조 타입」의 증거다.\
  값 타입이었다면 **「참조가 같냐」라는 질문 자체가 성립하지 않는다.**
- ★★ **값처럼 보이는 이유는 둘뿐**이다 — ① `==` 오버로드 ② **불변성**.\
  참조를 공유해도 **남이 바꿀 수가 없어** 값처럼 써도 탈이 안 난다.
- ★★★ **마지막 줄이 `↔Java` 에서 갈린다.** Java 는 `Integer` 를 **-128\~127 에서 캐싱**해\
  `Integer.valueOf(5) == Integer.valueOf(5)` 가 **참**이지만, **C# 에는 그 캐시가 없다.**\
  박싱할 때마다 **새 객체**이고, 7번의 「박싱 1000번 = 24000바이트」가 같은 사실을 바이트로 말한다.\
  ★ 정본은 [03번](../03-boxing-and-unboxing/)이다.

### 6. ★ `int?` 는 구조체다 — 다만 박싱하면 `Nullable` 이 벗겨진다

**출력**

```text
===== 소스: cs01b-nullable.cs =====
using System;

int? q = null;
Console.WriteLine($"q.HasValue          : {q.HasValue}");
Console.WriteLine($"q.GetType() 호출 전 : q is Nullable<int> 인가 — 아래 세 줄로 본다");
Console.WriteLine($"typeof(int?)        : {typeof(int?)}");
Console.WriteLine($"q == null           : {q == null}");

q = 5;
Console.WriteLine($"q.Value             : {q.Value}");
object o = q;                     // 박싱하면 Nullable 이 벗겨진다
Console.WriteLine($"((object)q).GetType() : {o!.GetType()}");

int? r = null;
object? ro = r;
Console.WriteLine($"((object)null int?) is null : {ro is null}");

try {
    int? z = null;
    Console.WriteLine(z.Value);
} catch (InvalidOperationException ex) {
    Console.WriteLine($"z.Value          : {ex.GetType().Name}: {ex.Message}");
}
===== csc -out:ex.dll cs01b-nullable.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
q.HasValue          : False
q.GetType() 호출 전 : q is Nullable<int> 인가 — 아래 세 줄로 본다
typeof(int?)        : System.Nullable`1[System.Int32]
q == null           : True
q.Value             : 5
((object)q).GetType() : System.Int32
((object)null int?) is null : True
z.Value          : InvalidOperationException: Nullable object must have a value.
```

**왜 그런가**

- ★★★ **`typeof(int?)` 가 ``System.Nullable`1[System.Int32]``** 를 답한다 — **제네릭 구조체**다.\
  `int?` 는 「참조 타입이 된 것」이 아니라 「**`HasValue` 와 `value` 를 함께 든 값 타입**」이다.
- ★★★ **`((object)q).GetType()` 이 `System.Int32`** 다 — **박싱이 `Nullable` 을 특별 취급**한다.\
  값이 있으면 **속의 `int` 를** 박싱하고, 값이 없으면 **`null` 참조**를 만든다.\
  ★ 그래서 바로 다음 줄에서 `(object)(int?)null is null` 이 **`True`** 다.\
  ★★ **이건 언어가 아니라 CLI(ECMA-335)의 박싱 규칙**이다.
- ★ 값이 없는 `.Value` 는 **`InvalidOperationException: Nullable object must have a value.`** 다.\
  `q == null` 은 `==` 가 `HasValue` 를 보도록 정의돼 있어서 `True` 가 나온다.
- ★ 정본은 [목록의 **08번 주제**](../08-nullable-value-types/)다.

### 7. ★★★ `new Point()` 는 **0바이트** · `new Node()` 는 **24바이트**

**출력**

```text
===== 소스: cs01b-alloc.cs =====
using System;

// 워밍업 — 첫 호출이 끌고 오는 할당을 측정 밖으로 뺀다.
Warm();

long a0 = GC.GetAllocatedBytesForCurrentThread();
var p = new Point { X = 1, Y = 2 };
long a1 = GC.GetAllocatedBytesForCurrentThread();
var n = new Node { X = 1, Y = 2 };
long a2 = GC.GetAllocatedBytesForCurrentThread();
var arrS = new Point[1000];
long a3 = GC.GetAllocatedBytesForCurrentThread();
var arrC = new Node[1000];
long a4 = GC.GetAllocatedBytesForCurrentThread();
for (int i = 0; i < 1000; i++) arrC[i] = new Node();
long a5 = GC.GetAllocatedBytesForCurrentThread();

Console.WriteLine($"new Point()      : +{a1 - a0} 바이트");
Console.WriteLine($"new Node()       : +{a2 - a1} 바이트");
Console.WriteLine($"new Point[1000]  : +{a3 - a2} 바이트");
Console.WriteLine($"new Node[1000]   : +{a4 - a3} 바이트");
Console.WriteLine($"거기에 Node 1000개 채우기 : +{a5 - a4} 바이트");
Console.WriteLine($"(합계는 흔들리는 칸이다 — 읽을 것은 0 이냐 아니냐와 증분이다)");
Console.WriteLine($"p.X={p.X} n.X={n.X} arrS.Length={arrS.Length} arrC[0]!.X={arrC[0]!.X}");

static void Warm() { var _ = new Node(); var __ = new Point[1]; GC.GetAllocatedBytesForCurrentThread(); }

struct Point { public int X; public int Y; }
class Node { public int X; public int Y; }
===== csc -out:ex.dll cs01b-alloc.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
new Point()      : +0 바이트
new Node()       : +24 바이트
new Point[1000]  : +8024 바이트
new Node[1000]   : +8024 바이트
거기에 Node 1000개 채우기 : +24000 바이트
(합계는 흔들리는 칸이다 — 읽을 것은 0 이냐 아니냐와 증분이다)
p.X=1 n.X=1 arrS.Length=1000 arrC[0]!.X=0
```

**왜 그런가**

| 쓴 것 | 증분 | 읽는 법 |
|---|---|---|
| `new Point { X=1, Y=2 }` | ★★★ **+0** | 힙을 **안 썼다** — 변수 자리에 바로 들어갔다 |
| `new Node { X=1, Y=2 }` | **+24** | 객체 헤더 16 + 필드 8 |
| `new Point[1000]` | **+8024** | `Point` 8바이트 × 1000 + 배열 헤더 24 |
| `new Node[1000]` | **+8024** | ★★ **같은 숫자인데 뜻이 정반대다** — 참조 8바이트 × 1000 |
| 거기에 `Node` 1000개 | **+24000** | 그제서야 **객체들**이 생긴다 |
| 박싱 1000번 | **+24000** | 박싱 하나가 `new Node()` 와 같은 24바이트다 |

- ★★★ **첫 줄의 `+0` 이 이 주제에서 가장 강한 한 줄**이다. 「값 타입은 힙을 안 쓴다」를 **수치로** 얻었다.
- ★★★ **두 배열의 8024 가 같은 것은 우연**이다 — `Point` 가 **마침 참조 하나와 같은 8바이트**라서다.\
  뜻은 정반대다: 앞엣것은 **`Point` 1000개가 이미 다 들어 있고**, 뒤엣것은 **`null` 1000개**다.\
  뒤엣것을 실제로 쓰려면 **24000 바이트를 더** 내야 한다 — 그것이 「값 타입 배열이 싸다」의 근거다.
- ★★ **근거로 쓸 수 있는 칸은 증분**이다. **절댓값(프로세스 누적)은 흔들리는 칸**이라 이 문서는 **한 번도 싣지 않았다.**\
  ★ 그래서 마지막 줄에 「합계는 흔들리는 칸이다」를 프로그램이 직접 찍게 해 뒀다.
- ★★ **「힙을 안 쓴다」는 「스택에 있다」와 같은 말이 아니다.** 구조체가 **클래스의 필드**이거나 **배열의 원소**이거나\
  **박싱**되면 힙에 있다(위 표의 4\~6번째 줄이 전부 그 경우다).\
  ★★★ **ECMA-334 는 「스택」이라는 저장 위치를 보장하지 않는다** — 보장되는 것은 **복사 의미론**이다.

### 8. ★★ 에러 **셋** — `sizeof(int)` 만 통과한다

**출력**

```text
===== 소스: cs01b-sizeof.cs =====
struct Point { public int X = 0; public int Y = 0; public Point() { } }
struct Holder { public string S = ""; public Holder() { } }

class Program {
    static void Main() {
        int a = sizeof(int);
        int b = sizeof(Point);
        int c = sizeof(Holder);
        int d = sizeof(string);
        System.Console.WriteLine($"{a} {b} {c} {d}");
    }
}
===== csc -out:ex.dll cs01b-sizeof.cs (cc exit=1) =====
cs01b-sizeof.cs(7,17): error CS0233: 'Point' does not have a predefined size, therefore sizeof can only be used in an unsafe context
cs01b-sizeof.cs(8,17): warning CS8500: This takes the address of, gets the size of, or declares a pointer to a managed type ('Holder')
cs01b-sizeof.cs(8,17): error CS0233: 'Holder' does not have a predefined size, therefore sizeof can only be used in an unsafe context
cs01b-sizeof.cs(9,17): warning CS8500: This takes the address of, gets the size of, or declares a pointer to a managed type ('string')
cs01b-sizeof.cs(9,17): error CS0233: 'string' does not have a predefined size, therefore sizeof can only be used in an unsafe context
```

**왜 그런가**

- ★★★ **`sizeof(int)` 은 컴파일러가 아는 고정 크기**라 통과하고, **사용자 구조체의 크기는 런타임이 정하는 것**이라\
  안전한 문맥에서는 못 묻게 막았다 — ``does not have a predefined size``.
- ★★ **`Holder`(`string` 필드가 있는 구조체)와 `string` 은 `unsafe` 로도 안 된다** —\
  경고 `CS8500` 이 ``takes the address of … a managed type`` 으로 그 이유를 말한다.
- 안전한 대안은 **`Unsafe.SizeOf<T>()`** 이고, `unsafe` 를 켜면 `sizeof(Point)` 도 된다.

```text
===== 소스: cs01b-sizeof-unsafe.cs =====
using System;
using System.Runtime.CompilerServices;

unsafe {
    Console.WriteLine($"sizeof(int)    = {sizeof(int)}");
    Console.WriteLine($"sizeof(Point)  = {sizeof(Point)}");
}
Console.WriteLine($"Unsafe.SizeOf<int>()    = {Unsafe.SizeOf<int>()}");
Console.WriteLine($"Unsafe.SizeOf<Point>()  = {Unsafe.SizeOf<Point>()}");
Console.WriteLine($"Unsafe.SizeOf<Holder>() = {Unsafe.SizeOf<Holder>()}");
Console.WriteLine($"Unsafe.SizeOf<Node>()   = {Unsafe.SizeOf<Node>()}");
Console.WriteLine($"Unsafe.SizeOf<string>() = {Unsafe.SizeOf<string>()}");

Console.WriteLine($"IsRefOrContainsRefs<int>()    = {RuntimeHelpers.IsReferenceOrContainsReferences<int>()}");
Console.WriteLine($"IsRefOrContainsRefs<Point>()  = {RuntimeHelpers.IsReferenceOrContainsReferences<Point>()}");
Console.WriteLine($"IsRefOrContainsRefs<Holder>() = {RuntimeHelpers.IsReferenceOrContainsReferences<Holder>()}");
Console.WriteLine($"IsRefOrContainsRefs<Node>()   = {RuntimeHelpers.IsReferenceOrContainsReferences<Node>()}");

struct Point { public int X; public int Y; }
struct Holder { public string S; }
class Node { public int X; public int Y; }
===== csc -unsafe -out:ex.dll cs01b-sizeof-unsafe.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
sizeof(int)    = 4
sizeof(Point)  = 8
Unsafe.SizeOf<int>()    = 4
Unsafe.SizeOf<Point>()  = 8
Unsafe.SizeOf<Holder>() = 8
Unsafe.SizeOf<Node>()   = 8
Unsafe.SizeOf<string>() = 8
IsRefOrContainsRefs<int>()    = False
IsRefOrContainsRefs<Point>()  = False
IsRefOrContainsRefs<Holder>() = True
IsRefOrContainsRefs<Node>()   = True
```

| 물어본 것 | 값 | 읽는 법 |
|---|---|---|
| `sizeof(Point)` · `Unsafe.SizeOf<Point>()` | **8** | `int` 둘 |
| `Unsafe.SizeOf<Node>()` · `Unsafe.SizeOf<string>()` | ★★★ **둘 다 8** | **참조 하나의 크기**다 — **객체 크기가 아니다** |
| `IsReferenceOrContainsReferences<Point>()` | **`False`** | 참조가 하나도 없다 |
| `IsReferenceOrContainsReferences<Holder>()` | ★ **`True`** | `string` 필드 하나가 **구조체 전체의 성질을 바꾼다** |

- ★★★ **`Unsafe.SizeOf<클래스>()` 가 답하는 것은 참조의 크기**다. 7번에서 `new Node()` 가 **24바이트**였다.\
  **크기를 물을 때 「무엇의 크기냐」를 먼저 정해야 한다.**
- ★★ **`IsReferenceOrContainsReferences<T>()` 가 진짜 경계선**이다 — 참조를 하나라도 품으면\
  GC 가 그 안을 훑어야 하고 `Span<T>`·`memcpy` 최적화 대상에서 빠진다. 정본은 목록의 **46번 주제**다.

### 9. ★★ IL 은 **만들 때만** 갈린다 — 대입은 같은 명령이다

**출력**

```text
===== 소스: cs01b-il.cs =====
Il.Dump(typeof(Probe), "MakeStruct");
Il.Dump(typeof(Probe), "MakeClass");
Il.Dump(typeof(Probe), "CopyStruct");
Il.Dump(typeof(Probe), "CopyClass");

static class Probe {
    public static Point MakeStruct() { var p = new Point(); p.X = 1; return p; }
    public static Node MakeClass() { var n = new Node(); n.X = 1; return n; }
    public static int CopyStruct(Point a) { var b = a; b.X = 9; return a.X; }
    public static int CopyClass(Node a) { var b = a; b.X = 9; return a.X; }
}

struct Point { public int X; public int Y; }
class Node { public int X; public int Y; }
===== csc -r:il.dll -out:ex.dll cs01b-il.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
--- Probe.MakeStruct ---
  .locals [0] Point
  .locals [1] Point
  IL_0000: nop
  IL_0001: ldloca.s 0
  IL_0003: initobj Point
  IL_0009: ldloca.s 0
  IL_000b: ldc.i4.1
  IL_000c: stfld Point::X
  IL_0011: ldloc.0
  IL_0012: stloc.1
  IL_0013: br.s IL_0015
  IL_0015: ldloc.1
  IL_0016: ret
--- Probe.MakeClass ---
  .locals [0] Node
  .locals [1] Node
  IL_0000: nop
  IL_0001: newobj Node::.ctor
  IL_0006: stloc.0
  IL_0007: ldloc.0
  IL_0008: ldc.i4.1
  IL_0009: stfld Node::X
  IL_000e: ldloc.0
  IL_000f: stloc.1
  IL_0010: br.s IL_0012
  IL_0012: ldloc.1
  IL_0013: ret
--- Probe.CopyStruct ---
  .locals [0] Point
  .locals [1] System.Int32
  IL_0000: nop
  IL_0001: ldarg.0
  IL_0002: stloc.0
  IL_0003: ldloca.s 0
  IL_0005: ldc.i4.s 9
  IL_0007: stfld Point::X
  IL_000c: ldarg.0
  IL_000d: ldfld Point::X
  IL_0012: stloc.1
  IL_0013: br.s IL_0015
  IL_0015: ldloc.1
  IL_0016: ret
--- Probe.CopyClass ---
  .locals [0] Node
  .locals [1] System.Int32
  IL_0000: nop
  IL_0001: ldarg.0
  IL_0002: stloc.0
  IL_0003: ldloc.0
  IL_0004: ldc.i4.s 9
  IL_0006: stfld Node::X
  IL_000b: ldarg.0
  IL_000c: ldfld Node::X
  IL_0011: stloc.1
  IL_0012: br.s IL_0014
  IL_0014: ldloc.1
  IL_0015: ret
```

**왜 그런가**

| 보는 곳 | 값 타입 | 참조 타입 | 읽는 법 |
|---|---|---|---|
| **만들 때** | ★★★ **`initobj Point`** | ★★★ **`newobj Node::.ctor`** | **힙을 쓰느냐가 여기서 갈린다** |
| **지역에 대입** | `stloc.0` | `stloc.0` | ★ **같다** |
| **필드에 쓰기** | `ldloca.s 0` → `stfld` | `ldloc.0` → `stfld` | 값 타입은 **자리**(주소)를 먼저 얹는다 |
| **`.locals`** | `[0] Point` | `[0] Node` | ★★★ **여기가 진짜 차이다** |

- ★★★ **`MakeStruct` 에 `newobj` 가 없다.** `initobj` 는 **이미 있는 자리를 0 으로 미는 명령**이고 할당이 아니다 —\
  7번의 `+0 바이트`와 같은 사실을 다른 창으로 본 것이다.
- ★★★ **`CopyStruct` 와 `CopyClass` 의 명령어 열이 거의 같다.** 둘 다 `ldarg.0` → `stloc.0` 이고,\
  갈리는 것은 `ldloca.s 0` 대 `ldloc.0` **한 줄뿐**이다(값 타입의 필드에 쓰려면 **자리의 주소**가 필요하다).\
  ★★ **무엇이 복사되는지는 「명령」이 아니라 `.locals` 의 「타입」이 정한다.**\
  `stloc.0` 은 「평가 스택 맨 위를 0번 지역에 넣어라」일 뿐이고, 그 지역이 `Point` 면 8바이트가 들어간다.
- ★★★ **그래서 이 절로 「구조체 대입이 느리다」를 증명할 수 없다** — 명령 수가 같다.\
  ★ 비용은 **명령이 다루는 타입의 크기**에 있고, 이 문서는 **그것을 재지 않았다.** 정본은 [02번](../02-struct-vs-class-choosing/)이다.
- ★ IL 은 **외부 도구 없이** 얻었다(`ilspycmd`·`ildasm` 안 깔았다). 방법은 [03번](../03-boxing-and-unboxing/2-summary.md)의 (0)절에 있다.

### 10. ★ `ReferenceEquals` 에 값 타입을 넣으면 **항상 거짓**이다

**왜 그런가**

- `ReferenceEquals(object, object)` 의 매개변수가 **`object`** 라, 값 타입을 넣으면 **양쪽 다 박싱**된다.\
  박싱은 **매번 새 객체**를 만들므로 **두 참조가 같을 수가 없다.**
- ★★ 5번의 마지막 줄이 그 실측이다 — **`ReferenceEquals(5, 5)` 가 `False`**.\
  ★ Java 라면 `Integer` 캐시 때문에 참이 나왔을 자리다.
- **묻는 법을 갈라 쓴다** — 「같은 값이냐」는 **`Equals`**(또는 `==`), 「같은 객체냐」는 **`ReferenceEquals`**.\
  ★ 값 타입에 「같은 객체냐」를 묻는 것은 **질문 자체가 성립하지 않는다.**

### 11. 잇는 자리

- **「`struct` 를 언제 고르나」** — [02번 — `struct` 대 `class` 고르기](../02-struct-vs-class-choosing/).\
  크기·불변성·복사 비용·**방어적 복사**가 거기다. 3번의 `in` 이 거기서 결론난다.
- **「값 타입이 `object` 로 올라갈 때」** — [03번 — 박싱과 언박싱](../03-boxing-and-unboxing/).\
  5번의 `ReferenceEquals(5, 5)` 와 7번의 「박싱 1000번」이 거기서 이어진다.
- **`ref`/`out`/`in` 자체** — 목록의 **44번 주제**. 여기서는 **「값이냐 참조냐」와 다른 축**이라는 것까지만 봤다.
- **「값이냐 참조냐」라는 개념 자체** — [`foundations/variables-and-memory/`](../../../../variables-and-memory/)(파이썬으로 설명한다).\
  **그쪽은 「참조가 무엇인가」까지, 여기는 「언어가 값 타입을 열어 줬을 때 무엇이 달라지나」부터.**
- **C++ 과의 축 차이** — C++ 갈래 목록([`cpp/syntax/README.md`](../../../cpp/syntax/README.md))의 **07번**.\
  ★★ 거기서 갈리는 것은 「**이름이냐 쪽지냐**」이고 **둘 다 참조 의미론**이다.\
  C# 의 구조체 대입은 **C++ 의 `Point p = q;`** 와 같고, C# 의 클래스 대입은 **C++ 의 `Point* p = q;`** 와 같다.\
  ★ 「대입이 무엇을 복사하나」가 축인 또 하나의 갈래는 Go 다 — Go 갈래 목록([`go/syntax/README.md`](../../../go/syntax/README.md))의 **05번**.

## 실행 검증

**무엇을 몇 번 어느 판에서 돌렸나** — 아래 블록은 전부 **.NET SDK 10.0.401 / 런타임 10.0.12 / `net10.0` / linux-x64** 에서\
캡처 스크립트로 받은 것이다. **제출 직전에 전부 다시 돌려 `diff -rq` 로 대조했다.**

| 블록 | 무엇을 고정하나 | 명령 |
|---|---|---|
| `cs01b-copy.cs` | ★ 구조체 `s1.X=1` · 클래스 `c1.X=99` · `ReferenceEquals` 참 | `csc` + 실행 |
| `cs01b-refoutin.cs` | ★★ `ByValue` 뒤에도 `777` — 참조 타입도 값 전달이다 | 〃 |
| `cs01b-in-write.cs` | `error CS8332`(readonly variable) | `csc` 만 |
| `cs01b-null.cs` | ★ `error CS0037` **둘** — `int`·`Point` | 〃 |
| `cs01b-string.cs` | ★★★ `a == c` 참 · `ReferenceEquals(a, c)` 거짓 · `ReferenceEquals(5,5)` 거짓 | `csc` + 실행 |
| `cs01b-nullable.cs` | ``Nullable`1[System.Int32]`` · 박싱하면 `System.Int32` | 〃 |
| `cs01b-alloc.cs` | ★★★ `new Point()` **+0** · `new Node()` **+24** | 〃 |
| `cs01b-sizeof.cs` | ★ `error CS0233` **셋** · 경고 `CS8500` 둘 | `csc` 만 |
| `cs01b-sizeof-unsafe.cs` | `sizeof(Point)=8` · `Unsafe.SizeOf<Node>()=8` · `IsRef…<Holder>()=True` | `csc -unsafe` + 실행 |
| `cs01b-il.cs` | ★★ `initobj` 대 `newobj` · 대입은 **같은 명령** | `csc -r:il.dll` + 실행 |

**구현 의존 항목** — 다음은 **이 환경(.NET 10.0.12 · CoreCLR · x64 linux)에서만** 그렇다.

- ★ **박싱·객체 하나가 24바이트인 것**(헤더 16 + 필드 8) — **32비트에서 다르다.** 이 문서는 **x64 만** 돌렸다.
- ★ **IL 명령 이름**(`initobj`·`newobj`·`ldloca.s`) — **Roslyn 이 낸 코드**다.\
  결론은 「**힙을 쓰느냐**」이고 **명령 이름 하나하나가 결론이 아니다.**
- ★ **`(object)(int?)` 가 `Nullable` 을 벗기는 것** — **CLI(ECMA-335)의 박싱 규칙**이고 언어 보장이 아니다.
- ★ **리터럴이 아닌 문자열의 `ReferenceEquals`** — 인터닝 정책은 구현이 정한다.
- 진단 문구·진단 코드·**에러 개수** — Roslyn 구현.
- ★ **`GCSettings.IsServerGC` 가 `False`**(워크스테이션 GC)인 판에서만 쟀다.

**언어가 보장하는 것**(구현이 바뀌어도 같다)

- **값 타입 대입이 값을 복사하고 참조 타입 대입이 참조를 복사하는** 것.
- **인자 전달이 기본으로 값 전달인** 것 · **`ref`/`out`/`in` 의 의미**.
- **값 타입에 `null` 을 못 넣는** 것 · **`T?` 가 `Nullable<T>` 라는** 것.
- **`sizeof` 가 내장 타입 말고는 `unsafe` 를 요구하는** 것.
- **`string` 이 참조 타입이고 불변이며 `==` 가 내용 비교인** 것.

**보장이 아닌 것 — 관찰로만 읽는다**

- ★★★ **「값 타입은 스택에 있다」** — 명세가 **저장 위치를 규정하지 않는다.**\
  관찰된 것은 「**힙 할당 증분이 0 이다**」까지다(7번).
- ★ **할당 바이트의 절댓값** — 프로세스 누적이라 흔들린다. 이 문서는 **증분만** 싣는다.

**안 돌려 본 것 / 못 잰 것**

- **안 돌려 본 것** — **32비트 런타임**(이 머신에 없다) · **서버 GC** · **`ref` 지역·`ref` 반환·`ref struct`**(목록의 **45번 주제**) ·\
  **`Span<T>`·`stackalloc`**(목록의 **46번 주제**) · **`#nullable enable` 을 켠 판**([목록의 **06번 주제**](../06-nullable-reference-types/)) ·\
  **`Unsafe.As`·`MemoryMarshal`** · **`record class` 와 `record struct` 의 대비**(정본은 [02번](../02-struct-vs-class-choosing/)).
- **못 잰 것** — ★ **「구조체 대입이 빠른가 느린가」를 수치로.**\
  9번이 보인 것은 「**IL 명령 수가 같다**」까지이고, 실제 비용은 **복사되는 바이트 수**에 달렸다.\
  ★ 그것을 재려면 **크기를 바꿔 가며 도는 벤치마크 하네스**가 따로 필요하다 —\
  이 문서는 **수치를 적지 않았다.** [02번](../02-struct-vs-class-choosing/)이 **`Equals` 쪽 한 축만** 쟀다.

**버전이 올랐을 때 다시 돌려야 하는 것**

- ★ **IL 명령 열**(9번) — Roslyn 이 바뀌면 가장 먼저 움직인다.
- ★ **할당 증분 24·8024·24000**(7번) — 객체 헤더 크기가 바뀌면 움직인다. **증분이 0 이냐 아니냐**는 안 움직인다.
- **진단 문구와 진단 코드**(3·4·8번).
- ★ **`Unsafe.SizeOf<string>()`** — 참조 크기라 32비트에서 4 가 된다.
