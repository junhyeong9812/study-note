# csharp/syntax/03 — 박싱과 언박싱 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> **환경** — .NET SDK **10.0.401** · 런타임 **.NET 10.0.12** · 타겟 **`net10.0`** · linux-x64.
> 진단은 **영어로 고정**했다(`DOTNET_CLI_UI_LANGUAGE=en` + `csc -preferreduilang:en-US`).
> ★★★ **이 주제에는 컴파일 진단이 거의 없다** — 박싱은 합법적인 암묵 변환이라 **에러도 경고도 안 난다**.
> 그래서 창이 둘이다 — ★★★ **할당 바이트**(`GC.GetAllocatedBytesForCurrentThread`)와 ★★ **IL**.
> ★★ **8번을 외우려 하지 마라** — 「보간 문자열은 박싱한다」가 **이 판에서 뒤집힌다**. 던져서 확인하는 것이 답이다.
> 선행 — [01번](../01-value-types-and-reference-types/)·[02번](../02-struct-vs-class-choosing/).

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★★ 박싱은 몇 바이트를 내나 (예측)

```csharp
// cs03b-alloc.cs
using System;

Warm();

int i = 42;
long l = 42L;
double d = 42.0;
var pt = new Point { X = 1, Y = 2 };
var big = new Big();
bool t = true;

long a0 = GC.GetAllocatedBytesForCurrentThread();
object o1 = i;                       // int 박싱
long a1 = GC.GetAllocatedBytesForCurrentThread();
object o2 = l;                       // long 박싱
long a2 = GC.GetAllocatedBytesForCurrentThread();
object o3 = d;                       // double 박싱
long a3 = GC.GetAllocatedBytesForCurrentThread();
object o4 = pt;                      // 8바이트 구조체 박싱
long a4 = GC.GetAllocatedBytesForCurrentThread();
object o5 = big;                     // 64바이트 구조체 박싱
long a5 = GC.GetAllocatedBytesForCurrentThread();
object o6 = t;                       // bool 박싱
long a6 = GC.GetAllocatedBytesForCurrentThread();
int back = (int)o1;                  // 언박싱
long a7 = GC.GetAllocatedBytesForCurrentThread();
for (int k = 0; k < 1000; k++) { object tmp = k; GC.KeepAlive(tmp); }
long a8 = GC.GetAllocatedBytesForCurrentThread();

Console.WriteLine($"object o = (int)42      : +{a1 - a0} 바이트");
Console.WriteLine($"object o = (long)42     : +{a2 - a1} 바이트");
Console.WriteLine($"object o = (double)42   : +{a3 - a2} 바이트");
Console.WriteLine($"object o = Point(8바이트) : +{a4 - a3} 바이트");
Console.WriteLine($"object o = Big(64바이트)  : +{a5 - a4} 바이트");
Console.WriteLine($"object o = (bool)true   : +{a6 - a5} 바이트");
Console.WriteLine($"int back = (int)o       : +{a7 - a6} 바이트  ← 언박싱");
Console.WriteLine($"박싱 1000번             : +{a8 - a7} 바이트");
Console.WriteLine($"back={back} o2={o2} o3={o3} o4={o4} o5={o5} o6={o6}");

static void Warm() {
    object w1 = 1; object w2 = 1L; object w3 = 1.0; object w4 = new Point();
    object w5 = new Big(); object w6 = false;
    GC.KeepAlive(w1); GC.KeepAlive(w2); GC.KeepAlive(w3);
    GC.KeepAlive(w4); GC.KeepAlive(w5); GC.KeepAlive(w6);
    GC.GetAllocatedBytesForCurrentThread();
}

struct Point { public int X; public int Y; }
struct Big { public long A, B, C, D, E, F, G, H; }
```

- 여덟 줄의 증분을 **각각** 맞힐 수 있는가?
- `int`(4바이트)와 `bool`(1바이트)과 `double`(8바이트)이 **같은가 다른가** — **왜**인가?
- **언박싱**(`int back = (int)o`)은 몇 바이트인가?
- 박싱 1000번이 24000바이트라는 것이 **무엇을 뜻하는가** — Java 였다면 어땠겠는가?

### 2. ★★ IL 은 박싱을 어떻게 적나 (왜)

```csharp
// cs03b-il.cs
Il.Dump(typeof(Probe), "Box");
Il.Dump(typeof(Probe), "Unbox");
Il.Dump(typeof(Probe), "ViaInterface");
Il.Dump(typeof(Probe), "ViaGeneric");

static class Probe {
    public static object Box(int n) { object o = n; return o; }
    public static int Unbox(object o) { int n = (int)o; return n; }
    public static int ViaInterface(int n) { System.IComparable c = n; return c.CompareTo(0); }
    public static int ViaGeneric<T>(T n) where T : System.IComparable<T> { return n.CompareTo(n); }
}
```

- `Box`·`Unbox` 에 나오는 **두 명령**의 이름은?
- `ViaInterface` 에 `box` 가 **몇 개** 나오는가 — 왜 그런가?
- `ViaGeneric` 에는 `box` 가 **있는가 없는가** — 대신 무엇이 있는가?
- 소스에 `box` 라는 글자가 **몇 번** 나오는가?

### 3. ★★ 인터페이스로 올리면 (예측)

```csharp
// cs03b-iface.cs
using System;

Warm();

int n = 42;

long a0 = GC.GetAllocatedBytesForCurrentThread();
IComparable c = n;                          // 인터페이스로 올린다 — 박싱
long a1 = GC.GetAllocatedBytesForCurrentThread();
int r1 = c.CompareTo(0);                    // 인자도 박싱된다(IComparable.CompareTo(object))
long a2 = GC.GetAllocatedBytesForCurrentThread();
int r2 = Gen(n, 0);                         // 제네릭 제약 — 박싱 없음
long a3 = GC.GetAllocatedBytesForCurrentThread();
int r3 = n.CompareTo(0);                    // int.CompareTo(int) 직접 호출
long a4 = GC.GetAllocatedBytesForCurrentThread();
int r4 = Obj(n);                            // object 매개변수 — 박싱
long a5 = GC.GetAllocatedBytesForCurrentThread();

Console.WriteLine($"IComparable c = n     : +{a1 - a0} 바이트  (결과 준비)");
Console.WriteLine($"c.CompareTo(0)        : +{a2 - a1} 바이트  (결과 {r1})");
Console.WriteLine($"Gen<int>(n, 0)        : +{a3 - a2} 바이트  (결과 {r2})");
Console.WriteLine($"n.CompareTo(0)        : +{a4 - a3} 바이트  (결과 {r3})");
Console.WriteLine($"Obj(n)  — object 인자 : +{a5 - a4} 바이트  (결과 {r4})");

static int Gen<T>(T a, T b) where T : IComparable<T> => a.CompareTo(b);
static int Obj(object o) => o.GetHashCode();

static void Warm() {
    int w = 7; IComparable c = w; _ = c.CompareTo(0); _ = Gen(w, 0); _ = w.CompareTo(0); _ = Obj(w);
    GC.GetAllocatedBytesForCurrentThread();
}
```

- 다섯 줄의 증분을 **각각** 맞힐 수 있는가?
- `c.CompareTo(0)` 이 **0 이 아닌** 이유는?
- `Gen<int>(n, 0)`(제네릭 제약)이 **0 인** 이유는?
- 구조체가 인터페이스를 **구현하면** 박싱이 사라지는가?

### 4. ★★ 제네릭 컬렉션과 비제네릭 컬렉션 (예측)

```csharp
// cs03b-generic.cs
using System;
using System.Collections;
using System.Collections.Generic;

Warm();

var al = new ArrayList(1000);
var ls = new List<int>(1000);

long a0 = GC.GetAllocatedBytesForCurrentThread();
for (int i = 0; i < 1000; i++) al.Add(i);          // ArrayList — 원소마다 박싱
long a1 = GC.GetAllocatedBytesForCurrentThread();
for (int i = 0; i < 1000; i++) ls.Add(i);          // List<int> — 박싱 없음
long a2 = GC.GetAllocatedBytesForCurrentThread();

long s1 = 0;
for (int i = 0; i < 1000; i++) s1 += (int)al[i]!;  // 꺼낼 때 언박싱
long a3 = GC.GetAllocatedBytesForCurrentThread();
long s2 = 0;
for (int i = 0; i < 1000; i++) s2 += ls[i];
long a4 = GC.GetAllocatedBytesForCurrentThread();

Console.WriteLine($"ArrayList.Add 1000번  : +{a1 - a0} 바이트");
Console.WriteLine($"List<int>.Add 1000번  : +{a2 - a1} 바이트");
Console.WriteLine($"ArrayList 에서 1000번 꺼내 더하기 : +{a3 - a2} 바이트 (합 {s1})");
Console.WriteLine($"List<int> 에서 1000번 꺼내 더하기 : +{a4 - a3} 바이트 (합 {s2})");

static void Warm() {
    var a = new ArrayList(4); var l = new List<int>(4);
    for (int i = 0; i < 4; i++) { a.Add(i); l.Add(i); }
    long z = 0; for (int i = 0; i < 4; i++) { z += (int)a[i]!; z += l[i]; }
    GC.KeepAlive(z);
    GC.GetAllocatedBytesForCurrentThread();
}
```

- 네 줄의 증분을 **각각** 맞힐 수 있는가?
- **꺼낼 때**는 어느 쪽이 더 드는가?
- 이것이 Java 의 `List<Integer>` 와 **어떻게 다른가**?

### 5. ★★ `Equals` 를 부르는 네 가지 (예측)

```csharp
// cs03b-equals.cs
using System;

Warm();

int a = 42;
int b = 42;
object ob = b;

long g0 = GC.GetAllocatedBytesForCurrentThread();
bool r1 = a.Equals(b);            // int.Equals(int) — 오버로드가 있다
long g1 = GC.GetAllocatedBytesForCurrentThread();
bool r2 = a.Equals(ob);           // int.Equals(object) — 인자가 이미 박싱돼 있다
long g2 = GC.GetAllocatedBytesForCurrentThread();
bool r3 = a.Equals((object)b);    // 여기서 박싱한다
long g3 = GC.GetAllocatedBytesForCurrentThread();
bool r4 = object.Equals(a, b);    // 둘 다 박싱된다
long g4 = GC.GetAllocatedBytesForCurrentThread();
int h1 = a.GetHashCode();         // 오버라이드가 있어 박싱 없음
long g5 = GC.GetAllocatedBytesForCurrentThread();
var pt = new NoOverride { X = 1 };
int h2 = pt.GetHashCode();        // ValueType.GetHashCode()
long g6 = GC.GetAllocatedBytesForCurrentThread();

Console.WriteLine($"a.Equals(b)           = {r1}   +{g1 - g0} 바이트");
Console.WriteLine($"a.Equals(ob)          = {r2}   +{g2 - g1} 바이트");
Console.WriteLine($"a.Equals((object)b)   = {r3}   +{g3 - g2} 바이트");
Console.WriteLine($"object.Equals(a, b)   = {r4}   +{g4 - g3} 바이트");
Console.WriteLine($"a.GetHashCode()       = {h1}   +{g5 - g4} 바이트");
Console.WriteLine($"구조체.GetHashCode()   = {(h2 == 0 ? "0" : "0 아님")}   +{g6 - g5} 바이트");

static void Warm() {
    int x = 1, y = 1; object o = y;
    _ = x.Equals(y); _ = x.Equals(o); _ = x.Equals((object)y); _ = object.Equals(x, y);
    _ = x.GetHashCode(); _ = new NoOverride().GetHashCode();
    GC.GetAllocatedBytesForCurrentThread();
}

struct NoOverride { public int X; }
```

- 여섯 줄의 증분을 **각각** 맞힐 수 있는가?
- `a.Equals(b)` 는 0인데 `a.Equals((object)b)` 는 왜 24인가?
- `a.Equals(ob)`(`ob` 는 이미 박싱됨)가 0인 것을 **어떻게 읽어야** 하는가?
- 구조체의 `GetHashCode()` 가 0이 아닌 것이 **어디서 문제가 되는가**?

### 6. ★★ 언박싱은 어디까지 되나 (예측)

```csharp
// cs03b-unbox-rules.cs
using System;

object o = 42;

Console.WriteLine($"(int)o           : {(int)o}");
Console.WriteLine($"(long)(int)o     : {(long)(int)o}");
Console.WriteLine($"o is int         : {o is int}");
Console.WriteLine($"o is long        : {o is long}");
Console.WriteLine($"o as string       : {((o as string) ?? "(null)")}");

try { long bad = (long)o; Console.WriteLine($"(long)o          : {bad}"); }
catch (InvalidCastException ex) { Console.WriteLine($"(long)o          : {ex.GetType().Name}: {ex.Message}"); }

object e = MyEnum.B;
Console.WriteLine($"(MyEnum)e        : {(MyEnum)e}");
try { int u = (int)e; Console.WriteLine($"(int)e           : {u}  ← 예외가 안 났다"); }
catch (InvalidCastException ex) { Console.WriteLine($"(int)e           : {ex.GetType().Name}: {ex.Message}"); }

object b = (byte)7;
try { int u = (int)b; Console.WriteLine($"(int)(object)(byte)7 : {u}"); }
catch (InvalidCastException ex) { Console.WriteLine($"(int)(object)(byte)7 : {ex.GetType().Name}: {ex.Message}"); }

enum MyEnum { A, B }
```

- 여덟 줄 중 **예외가 나는** 것은 몇 줄인가?
- 박싱된 `enum` 을 `(int)` 로 꺼내면 어떻게 되는가 — **왜** 그런가?
- 박싱된 `byte` 를 `(int)` 로 꺼내면?
- 「정확한 타입이라야 한다」는 **언어의 규칙인가 런타임의 규칙인가**?

### 7. ★ 언박싱이 실패하면 (경계)

- 예외 이름과 메시지 전문은 무엇인가?
- 종료 코드는?
- 이 블록에 **표준 출력이 한 줄도 없는** 이유는?

### 8. ★★★ 이 다섯 줄 중 박싱하는 것은 (예측)

```csharp
// cs03b-hidden-il.cs
Il.Dump(typeof(Probe), "Interp");
Il.Dump(typeof(Probe), "Concat");
Il.Dump(typeof(Probe), "Format");
Il.Dump(typeof(Probe), "ParamsObject");
Il.Dump(typeof(Probe), "ParamsInt");

static class Probe {
    public static string Interp(int n) => $"n={n}";
    public static string Concat(int n) => "n=" + n;
    public static string Format(int n) => string.Format("n={0}", n);
    public static int ParamsObject(int n) => SumObj(n, n);
    public static int ParamsInt(int n) => SumInt(n, n);
    static int SumObj(params object[] xs) => xs.Length;
    static int SumInt(params int[] xs) => xs.Length;
}
```

- 다섯 중 IL 에 **`box` 가 찍히는** 것은 몇 개인가?
- `$"n={n}"` 과 `string.Format("n={0}", n)` 이 **같은가 다른가**?
- `params object[]` 와 `params int[]` 는?
- 할당 바이트로 보면 **가장 많이 쓰는** 것은 무엇인가 — 그것이 **박싱 때문인가**?

### 9. ★ 「할당이 있다」와 「박싱이 있다」 (왜)

- 이 둘이 **같은 질문인가 다른 질문인가**?
- `"n=" + n` 이 그 예다 — 무엇이 있고 무엇이 없는가?
- 두 질문을 각각 **무엇으로** 보는가?

### 10. ★ 박싱을 지우는 도구 (경계)

- 다섯 가지를 댈 수 있는가?
- 값 타입을 받는 API 를 설계할 때 **매개변수를 어떻게** 잡아야 하는가?
- 박싱을 **그냥 둬도 되는** 자리는 어디인가?

### 11. 다른 주제와 잇기 (연결)

- 「제네릭이 런타임까지 타입을 유지한다」의 정본은 목록의 몇 번인가?
- 「`IEquatable<T>` 를 구현해 박싱을 없앤다」가 본론이 되는 주제는?
- 「보간 문자열이 무엇으로 컴파일되나」의 정본은 목록의 몇 번인가?
- `ReferenceEquals(5, 5)` 가 거짓인 것을 본 주제는?
- `params ReadOnlySpan<T>` 는 목록의 몇 번과 이어지는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
