# csharp/syntax/03 — 박싱과 언박싱 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> **기준 소스** — [ECMA-334 7판(2023-12)](https://ecma-international.org/publications-and-standards/standards/ecma-334/) · [Microsoft Learn — C# 언어 레퍼런스](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/) · [Learn — 값 형식](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/builtin-types/value-types) · [Learn — 참조 형식](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/keywords/reference-types) · [.NET API — `GC.GetAllocatedBytesForCurrentThread`](https://learn.microsoft.com/en-us/dotnet/api/system.gc.getallocatedbytesforcurrentthread)
> **실행 검증** — 이 문서의 모든 출력·진단·IL·할당 바이트는 **.NET SDK 10.0.401** ·\
> 런타임 **`.NET 10.0.12`**(`Microsoft.NETCore.App`) · 타겟 **`net10.0`** · **linux-x64** 에서 실제로 돌려 얻은 것이다(2026-09-24).\
> ★ 블록은 캡처 스크립트가 파일로 받아 조립기가 끼워 넣은 것이다 — 사람이 옮겨 적은 줄은 하나도 없다.
> **읽는 법** — ★★★ **할당 바이트는 증분만 근거로 쓴다.** 절댓값(프로세스 누적)은 흔들리는 칸이고,\
> 이 문서는 **한 번도 싣지 않았다.** 더 중요한 것은 **0 이냐 아니냐**다.\
> **IL 덤프는 `-optimize` 없이**(기본 디버그) 낸 것이라 `nop` 이 섞여 있다.\
> ★ **`-debug` 는 안 줬다** — 그래서 예외 트레이스에 절대 경로·줄 번호가 없다.\
> 자세한 환경과 IL 도구의 전문은 [2-summary.md](2-summary.md)의 머리말·(0)절에 있다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ 박싱 **+24** · 언박싱 **+0** · 1000번이면 **+24000**

**출력**

```text
===== 소스: cs03b-alloc.cs =====
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
===== csc -out:ex.dll cs03b-alloc.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
object o = (int)42      : +24 바이트
object o = (long)42     : +24 바이트
object o = (double)42   : +24 바이트
object o = Point(8바이트) : +24 바이트
object o = Big(64바이트)  : +80 바이트
object o = (bool)true   : +24 바이트
int back = (int)o       : +0 바이트  ← 언박싱
박싱 1000번             : +24000 바이트
back=42 o2=42 o3=42 o4=Point o5=Big o6=True
```

**왜 그런가**

| 박싱한 것 | 증분 | 읽는 법 |
|---|---|---|
| `int`(4바이트) | **+24** | 헤더 16 + 값 4 + 패딩 |
| `long`·`double`(8바이트) | **+24** | ★ **같다** |
| `bool`(1바이트) | **+24** | ★★ **같다** — 1바이트에 24바이트다 |
| `Point`(8바이트 구조체) | **+24** | 〃 |
| `Big`(64바이트 구조체) | **+80** | 헤더 16 + 64 |
| **언박싱**(`(int)o`) | ★★★ **+0** | 새 객체를 안 만든다 |
| 박싱 1000번 | **+24000** | ★★★ **하나도 재사용되지 않는다** |

- ★★★ **`int`·`long`·`double`·`bool` 이 전부 24바이트**다. **비용의 대부분이 객체 헤더**(16)라\
  **담는 값의 크기와 거의 무관**하다. ★ 「작은 값이니까 괜찮다」가 **가장 틀린 직관**이다.\
  ★ 8바이트를 넘는 구조체는 그제서야 커진다(`Big` 64바이트 → 80).
- ★★★ **언박싱은 0바이트**다 — 「박싱/언박싱이 비싸다」에서 **비싼 쪽은 박싱뿐**이다.\
  언박싱은 **상자 안의 바이트를 복사해 오는 것**이라 새 객체가 필요 없다(2번의 `unbox.any`).
- ★★★ **박싱 1000번에 24000바이트 — 캐시가 없다.**\
  ★★ **`↔Java`** — Java 는 `Integer` 를 **-128\~127 에서 캐싱**해 같은 작은 값이면 객체를 재사용하지만,\
  **C# 에는 그 캐시가 없다.** 명세가 「**새 객체를 할당한다**」로 적혀 있다 — **캐시 없음이 규정**이다.\
  ★ [01번](../01-value-types-and-reference-types/)의 (6)에서 `ReferenceEquals(5, 5)` 가 **`False`** 였던 것이 같은 사실이다.

### 2. ★★ `box` 와 `unbox.any` — 그리고 제네릭의 `constrained.`

**출력**

```text
===== 소스: cs03b-il.cs =====
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
===== csc -r:il.dll -out:ex.dll cs03b-il.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
--- Probe.Box ---
  .locals [0] System.Object
  .locals [1] System.Object
  IL_0000: nop
  IL_0001: ldarg.0
  IL_0002: box System.Int32
  IL_0007: stloc.0
  IL_0008: ldloc.0
  IL_0009: stloc.1
  IL_000a: br.s IL_000c
  IL_000c: ldloc.1
  IL_000d: ret
--- Probe.Unbox ---
  .locals [0] System.Int32
  .locals [1] System.Int32
  IL_0000: nop
  IL_0001: ldarg.0
  IL_0002: unbox.any System.Int32
  IL_0007: stloc.0
  IL_0008: ldloc.0
  IL_0009: stloc.1
  IL_000a: br.s IL_000c
  IL_000c: ldloc.1
  IL_000d: ret
--- Probe.ViaInterface ---
  .locals [0] System.IComparable
  .locals [1] System.Int32
  IL_0000: nop
  IL_0001: ldarg.0
  IL_0002: box System.Int32
  IL_0007: stloc.0
  IL_0008: ldloc.0
  IL_0009: ldc.i4.0
  IL_000a: box System.Int32
  IL_000f: callvirt System.IComparable::CompareTo
  IL_0014: stloc.1
  IL_0015: br.s IL_0017
  IL_0017: ldloc.1
  IL_0018: ret
--- Probe.ViaGeneric ---
  .locals [0] System.Int32
  IL_0000: nop
  IL_0001: ldarga.s 0
  IL_0003: ldarg.0
  IL_0004: constrained. T
  IL_000a: callvirt IComparable<T>::CompareTo
  IL_000f: stloc.0
  IL_0010: br.s IL_0012
  IL_0012: ldloc.0
  IL_0013: ret
```

**왜 그런가**

| 메서드 | 핵심 명령 | 읽는 법 |
|---|---|---|
| `Box(int n)` | ★ **`box System.Int32`** | 소스의 `object o = n;` 한 줄이 이것이다 |
| `Unbox(object o)` | ★ **`unbox.any System.Int32`** | 명령 하나이고 할당이 없다 |
| `ViaInterface(int n)` | ★★★ **`box` 가 둘** | 올릴 때 하나, **인자로 넘길 때** 또 하나 |
| `ViaGeneric<T>(T n)` | ★★★ **`constrained. T` → `callvirt`** | ★★★ **`box` 가 없다** |

- ★★★ **`ViaInterface` 에 `box` 가 두 개**다. `IComparable c = n;` 에서 하나,\
  `c.CompareTo(0)` 의 **인자**에서 또 하나 — `IComparable.CompareTo` 의 매개변수가 **`object`** 이기 때문이다.\
  ★ 3번이 그것을 **+24 두 번**으로 확인한다.
- ★★★ **`constrained.` 가 제네릭의 답**이다 —\
  「`T` 가 값 타입이면 **박싱하지 말고 그 타입의 메서드를 직접** 불러라」는 IL 접두사다.\
  런타임이 **`T` 마다 전용 코드를 만들어** 그것을 가능하게 한다(4번).
- ★★★ **소스에 `box` 라는 글자는 한 번도 안 나온다.** 그것이 이 절의 값어치다 —\
  **박싱은 문법이 아니라 변환**이라 **소스를 아무리 읽어도 안 보인다.** 그래서 IL 을 본다.

### 3. ★★ **+24 · +24 · +0 · +0 · +24** — 인터페이스는 두 번 박싱한다

**출력**

```text
===== 소스: cs03b-iface.cs =====
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
===== csc -out:ex.dll cs03b-iface.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
IComparable c = n     : +24 바이트  (결과 준비)
c.CompareTo(0)        : +24 바이트  (결과 1)
Gen<int>(n, 0)        : +0 바이트  (결과 1)
n.CompareTo(0)        : +0 바이트  (결과 1)
Obj(n)  — object 인자 : +24 바이트  (결과 42)
```

**왜 그런가**

| 쓴 것 | 할당 | 왜 |
|---|---|---|
| `IComparable c = n;` | **+24** | 인터페이스는 **참조 타입 자리**다 |
| `c.CompareTo(0)` | **+24** | ★★ 인자 `0` 이 **`object` 로 박싱**된다 |
| `Gen<int>(n, 0)`(제네릭 제약) | ★★★ **+0** | `IComparable<T>` 제약이면 박싱이 없다 |
| `n.CompareTo(0)` | **+0** | `int.CompareTo(int)` 오버로드가 직접 뽑힌다 |
| `Obj(n)`(`object` 매개변수) | **+24** | 매개변수 타입이 `object` 다 |

- ★★★ **비제네릭 `IComparable`(+24 두 번)과 제네릭 제약(+0)의 대비**가 이 절의 결론이다.
- ★★ **구조체가 인터페이스를 구현해도 박싱은 안 사라진다.**\
  **인터페이스 타입 변수에 담는 순간** 박싱이다 — **구현 여부가 아니라 「담는 자리」가 정한다.**\
  ★ 피하려면 **제네릭 제약**(`where T : IComparable<T>`)으로 받는다.
- ★ **API 설계의 결론** — 값 타입을 받는 API 는 `object`·비제네릭 인터페이스 말고\
  **제네릭 매개변수 + 제약**으로 받는다(목록의 **25번 주제**).

### 4. ★★ `ArrayList` **+24000** · `List<int>` **+0** — 꺼낼 때는 둘 다 0

**출력**

```text
===== 소스: cs03b-generic.cs =====
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
===== csc -out:ex.dll cs03b-generic.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
ArrayList.Add 1000번  : +24000 바이트
List<int>.Add 1000번  : +0 바이트
ArrayList 에서 1000번 꺼내 더하기 : +0 바이트 (합 499500)
List<int> 에서 1000번 꺼내 더하기 : +0 바이트 (합 499500)
```

**왜 그런가**

| 쓴 것 | 할당 | 왜 |
|---|---|---|
| `ArrayList.Add(i)` 1000번 | ★ **+24000** | 원소마다 **박싱**(24 × 1000) |
| `List<int>.Add(i)` 1000번 | ★★★ **+0** | ★★★ **`int[]` 에 그냥 들어간다** |
| `ArrayList` 에서 1000번 꺼내기 | **+0** | 언박싱은 할당이 없다(1번) |
| `List<int>` 에서 1000번 꺼내기 | **+0** | 꺼낼 것이 없다 |

- ★★★ **`+24000` 대 `+0`** — 「제네릭이 왜 필요한가」의 답이 이 두 숫자다.\
  ★ 용량(`capacity: 1000`)을 미리 줘서 **배열 재할당을 측정 밖으로 뺐다** — 남은 것이 **박싱뿐**이다.
- ★★★ **`↔Java` 에서 가장 크게 갈리는 자리다.**\
  Java 의 제네릭은 **타입 소거**라 `List<Integer>` 가 런타임에 `List<Object>` 이고 **원소가 전부 박싱된 객체**다.\
  C# 은 **런타임까지 타입이 남아** `List<int>` 가 **진짜 `int[]`** 를 든다.\
  ★ 정본은 목록의 **24번 주제**다.
- ★ **꺼낼 때는 둘 다 0** 이다 — **비용은 넣을 때 다 났다.**

### 5. ★★ 오버로드가 있으면 0, `object` 를 받으면 24

**출력**

```text
===== 소스: cs03b-equals.cs =====
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
===== csc -out:ex.dll cs03b-equals.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
a.Equals(b)           = True   +0 바이트
a.Equals(ob)          = True   +0 바이트
a.Equals((object)b)   = True   +24 바이트
object.Equals(a, b)   = True   +48 바이트
a.GetHashCode()       = 42   +0 바이트
구조체.GetHashCode()   = 0 아님   +24 바이트
```

**왜 그런가**

| 쓴 것 | 할당 | 왜 |
|---|---|---|
| `a.Equals(b)`(둘 다 `int`) | **+0** | ★ `int.Equals(int)` **오버로드가 있다** |
| `a.Equals(ob)`(`ob` 는 이미 박싱됨) | **+0** | ★★ **앞줄에서 이미 박싱했다** |
| `a.Equals((object)b)` | **+24** | ★ **여기서 박싱한다** |
| `object.Equals(a, b)` | **+48** | ★★ **둘 다** 박싱된다 |
| `int.GetHashCode()` | **+0** | 오버라이드가 있다 |
| 구조체의 `GetHashCode()` | ★ **+24** | ★★ **`ValueType.GetHashCode()` 는 `this` 를 박싱**한다 |

- ★★★ **마지막 줄이 조용한 자리**다 — 오버라이드가 없는 구조체를 **`Dictionary` 키로 쓰면**\
  **해시를 구할 때마다 24바이트**를 낸다. 루프 안이면 그대로 쌓인다.\
  ★ 고치는 법은 [02번](../02-struct-vs-class-choosing/)의 (5)·(6) — `IEquatable<T>` 나 `record struct`.
- ★★ **`a.Equals(ob)` 가 0 인 것을 「공짜」로 읽으면 안 된다.**\
  **박싱 비용이 사라진 게 아니라 `object ob = b;` 줄에서 이미 났다.**\
  ★ 이 문서는 그 줄을 **측정 구간 밖**에 뒀다 — 「어디서 났나」를 갈라 보이기 위해서다.
- ★ **오버로드가 있는지가 전부**다. `int` 는 `Equals(int)` 와 `GetHashCode()` 오버라이드를 둘 다 갖고 있다.

### 6. ★★ 예외 **둘** — 그리고 **열거형만 봐준다**

**출력**

```text
===== 소스: cs03b-unbox-rules.cs =====
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
===== csc -out:ex.dll cs03b-unbox-rules.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
(int)o           : 42
(long)(int)o     : 42
o is int         : True
o is long        : False
o as string       : (null)
(long)o          : InvalidCastException: Unable to cast object of type 'System.Int32' to type 'System.Int64'.
(MyEnum)e        : B
(int)e           : 1  ← 예외가 안 났다
(int)(object)(byte)7 : InvalidCastException: Unable to cast object of type 'System.Byte' to type 'System.Int32'.
```

**왜 그런가**

| 쓴 것 | 결과 | 읽는 법 |
|---|---|---|
| `(int)o` | **42** | 정확한 타입이라 된다 |
| `(long)(int)o` | **42** | ★ **두 단계**로 쓴다 |
| `o is int` / `o is long` | **`True` / `False`** | ★ **패턴 매칭도 정확한 타입만** 본다 |
| `o as string` | `(null)` | `as` 는 **참조 타입·`T?`** 에만 쓴다 |
| `(long)o` | **`InvalidCastException`** | 한 단계로는 안 된다 |
| ★★★ **박싱된 `enum` → `(int)`** | ★★★ **예외 없이 `1`** | ★★★ **런타임이 봐준다** |
| 박싱된 `byte` → `(int)` | **`InvalidCastException`** | ★ **숫자끼리는 안 봐준다** |

- ★★★ **여섯째 줄이 예상을 뒤집는다.** `(int)e`(`e` 는 박싱된 `MyEnum`)가 **통과한다.**\
  ★★★ **이것이 「언어의 규칙인가 런타임의 규칙인가」의 답**이다 —\
  **C# 명세는 「정확한 타입」을 요구**하지만 **CLI(ECMA-335)는 열거형과 그 기반 타입의 언박싱을 허용**한다.\
  **런타임이 언어보다 관대한 자리**이고, 컴파일러가 통과시키면 런타임이 받아 준다.
- ★★ **바로 다음 줄이 그 관대함의 경계**다 — `byte` → `(int)` 는 **던진다.**\
  ★ **「숫자니까 되겠지」가 안 통한다** — 되는 것은 **열거형 ↔ 기반 타입**뿐이다.
- ★ **안전하게 쓰는 법** — `o is int n` 패턴, 또는 `o as int?`.\
  `o as int` 는 **컴파일이 안 된다**(`as` 는 널이 될 수 있는 타입만 받는다).

### 7. ★ `InvalidCastException` · `run exit=134` · 표준 출력은 **0줄**

**출력**

```text
===== 소스: cs03b-unbox-fail.cs =====
object o = 42;
long n = (long)o;
System.Console.WriteLine(n);
===== csc -out:ex.dll cs03b-unbox-fail.cs && dotnet ex.dll (cc exit=0 · run exit=134) =====
Unhandled exception. System.InvalidCastException: Unable to cast object of type 'System.Int32' to type 'System.Int64'.
   at Program.<Main>$(String[] args)
```

**왜 그런가**

- ★ 예외 전문은 ``System.InvalidCastException: Unable to cast object of type 'System.Int32' to type 'System.Int64'.`` 이고,\
  트레이스는 ``   at Program.<Main>$(String[] args)`` 한 줄이다.
- ★★ **트레이스가 거기서 끝나는 것은 PDB 를 안 만들었기 때문**이다.\
  `-debug` 를 주면 ``in /절대경로/ex.cs:line N`` 이 붙어 **머신마다 달라진다** — 그래서 일부러 안 줬다.
- ★ **종료 코드는 134**(SIGABRT)다. 관리되지 않은 예외로 런타임이 프로세스를 죽인 것이다.
- ★★★ **이 블록은 표준 출력을 한 줄도 안 찍는다.** 예외(표준 오류)와 섞지 않으려고 그렇게 만들었다.\
  ★ 이 런타임이 **종료 전에 표준 출력을 비우는지**는 따로 던져 확인했고([2-summary.md](2-summary.md)의 (0)),\
  **비웠다.** 그래도 **「이 판의 관찰」이라 규칙은 그대로 지켰다.**

### 8. ★★★ 다섯 중 **둘**만 박싱한다 — 보간 문자열은 안 한다

**출력**

```text
===== 소스: cs03b-hidden-il.cs =====
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
===== csc -r:il.dll -out:ex.dll cs03b-hidden-il.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
--- Probe.Interp ---
  .locals [0] System.Runtime.CompilerServices.DefaultInterpolatedStringHandler
  IL_0000: ldloca.s 0
  IL_0002: ldc.i4.2
  IL_0003: ldc.i4.1
  IL_0004: call System.Runtime.CompilerServices.DefaultInterpolatedStringHandler::.ctor
  IL_0009: ldloca.s 0
  IL_000b: ldstr "n="
  IL_0010: call System.Runtime.CompilerServices.DefaultInterpolatedStringHandler::AppendLiteral
  IL_0015: nop
  IL_0016: ldloca.s 0
  IL_0018: ldarg.0
  IL_0019: call System.Runtime.CompilerServices.DefaultInterpolatedStringHandler::AppendFormatted
  IL_001e: nop
  IL_001f: ldloca.s 0
  IL_0021: call System.Runtime.CompilerServices.DefaultInterpolatedStringHandler::ToStringAndClear
  IL_0026: ret
--- Probe.Concat ---
  IL_0000: ldstr "n="
  IL_0005: ldarga.s 0
  IL_0007: call System.Int32::ToString
  IL_000c: call System.String::Concat
  IL_0011: ret
--- Probe.Format ---
  IL_0000: ldstr "n={0}"
  IL_0005: ldarg.0
  IL_0006: box System.Int32
  IL_000b: call System.String::Format
  IL_0010: ret
--- Probe.ParamsObject ---
  IL_0000: ldc.i4.2
  IL_0001: newarr System.Object
  IL_0006: dup
  IL_0007: ldc.i4.0
  IL_0008: ldarg.0
  IL_0009: box System.Int32
  IL_000e: stelem.ref
  IL_000f: dup
  IL_0010: ldc.i4.1
  IL_0011: ldarg.0
  IL_0012: box System.Int32
  IL_0017: stelem.ref
  IL_0018: call Probe::SumObj
  IL_001d: ret
--- Probe.ParamsInt ---
  IL_0000: ldc.i4.2
  IL_0001: newarr System.Int32
  IL_0006: dup
  IL_0007: ldc.i4.0
  IL_0008: ldarg.0
  IL_0009: stelem.i4
  IL_000a: dup
  IL_000b: ldc.i4.1
  IL_000c: ldarg.0
  IL_000d: stelem.i4
  IL_000e: call Probe::SumInt
  IL_0013: ret
```

```text
===== 소스: cs03b-hidden-alloc.cs =====
using System;

Warm();

int n = 42;

long a0 = GC.GetAllocatedBytesForCurrentThread();
string s1 = $"n={n}";
long a1 = GC.GetAllocatedBytesForCurrentThread();
string s2 = "n=" + n;
long a2 = GC.GetAllocatedBytesForCurrentThread();
string s3 = string.Format("n={0}", n);
long a3 = GC.GetAllocatedBytesForCurrentThread();
int c1 = SumObj(n, n);
long a4 = GC.GetAllocatedBytesForCurrentThread();
int c2 = SumInt(n, n);
long a5 = GC.GetAllocatedBytesForCurrentThread();
string s4 = "n=42";
long a6 = GC.GetAllocatedBytesForCurrentThread();

Console.WriteLine($"$\"n={{n}}\"            : +{a1 - a0} 바이트  ({s1})");
Console.WriteLine($"\"n=\" + n             : +{a2 - a1} 바이트  ({s2})");
Console.WriteLine($"string.Format(...)   : +{a3 - a2} 바이트  ({s3})");
Console.WriteLine($"params object[] 호출  : +{a4 - a3} 바이트  (원소 {c1}개)");
Console.WriteLine($"params int[] 호출     : +{a5 - a4} 바이트  (원소 {c2}개)");
Console.WriteLine($"리터럴 \"n=42\"        : +{a6 - a5} 바이트  ({s4})");

static int SumObj(params object[] xs) => xs.Length;
static int SumInt(params int[] xs) => xs.Length;

static void Warm() {
    int w = 1;
    _ = $"n={w}"; _ = "n=" + w; _ = string.Format("n={0}", w);
    _ = SumObj(w, w); _ = SumInt(w, w);
    GC.GetAllocatedBytesForCurrentThread();
}
===== csc -out:ex.dll cs03b-hidden-alloc.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
$"n={n}"            : +32 바이트  (n=42)
"n=" + n             : +64 바이트  (n=42)
string.Format(...)   : +56 바이트  (n=42)
params object[] 호출  : +88 바이트  (원소 2개)
params int[] 호출     : +32 바이트  (원소 2개)
리터럴 "n=42"        : +0 바이트  (n=42)
```

**왜 그런가**

| 쓴 것 | IL | 박싱 | 할당 |
|---|---|---|---|
| `$"n={n}"` | `DefaultInterpolatedStringHandler::AppendFormatted` | ★★★ **없다** | **+32** |
| `"n=" + n` | `Int32::ToString` → `String::Concat` | ★★ **없다** | ★ **+64** |
| `string.Format("n={0}", n)` | ★★★ **`box System.Int32`** | ★★★ **있다** | **+56** |
| `SumObj(params object[])` | ★★★ **`newarr System.Object` + `box` ×2** | ★★★ **있다** | ★ **+88** |
| `SumInt(params int[])` | `newarr System.Int32` + `stelem.i4` | **없다** | **+32** |

- ★★★ **「보간 문자열은 박싱한다」가 이 판에서 틀렸다.**\
  C# 10부터 `$"…"` 는 **`DefaultInterpolatedStringHandler`** 로 컴파일되고,\
  그 `AppendFormatted<T>(T value)` 가 **제네릭**이라 박싱이 안 난다.\
  ★ **`string.Format` 은 `params object[]` 를 받으므로 여전히 박싱한다** — 셋이 같아 보이는데 갈린다.
- ★★★ **`params object[]` 가 가장 비싸다(+88)** — **배열 하나 + 박싱 둘**이다.\
  `params int[]` 로 받으면 **배열만**(+32) 든다.
- ★★★ **가장 많이 쓰는 것은 `"n=" + n`(+64)인데 박싱은 없다.**\
  `int.ToString()` 이 문자열 하나를 만들고 `Concat` 이 결과 문자열을 또 만든 것이다.\
  ★★ **「할당이 가장 많다」와 「박싱한다」가 같은 줄에 없다** — 9번이 그 이야기다.
- ★★★ **결론 — 박싱이 나는 자리는 판마다 다르므로 던져 본다.**\
  **C# 9 이하에서는 보간 문자열도 `string.Format` 으로 풀려 박싱했다.**\
  ★ 이 문서는 **.NET 10 한 판만** 던졌다 — 옛 판은 이 머신에 없다.

### 9. ★ 다른 질문이다 — IL 로 하나, 바이트로 하나

**왜 그런가**

- ★★★ **「박싱이 있나」는 IL 로 보고, 「얼마를 쓰나」는 할당 바이트로 본다.**\
  8번의 표가 그것을 한 눈에 보여 준다 — **박싱 없는 `"n=" + n` 이 할당은 가장 많다**(+64).\
  **박싱하는 `string.Format` 은 그보다 적다**(+56).
- ★ `"n=" + n` 이 쓰는 것은 **문자열 둘**이다 — `int.ToString()` 의 결과와 `Concat` 의 결과.\
  박싱은 **한 번도 안 난다**(IL 에 `box` 가 없다).
- ★★ **그래서 「할당을 줄이자」와 「박싱을 없애자」는 다른 작업**이다.\
  박싱을 다 없애도 문자열 할당은 남고, 그것은 `StringBuilder`·`Span<char>` 의 영역이다(목록의 **47번 주제**).

### 10. ★ 다섯 도구 — 그리고 그냥 둬도 되는 자리

**왜 그런가**

**박싱을 지우는 도구 다섯**

1. **제네릭 컬렉션** — `List<int>`·`Dictionary<int, V>`(4번).
2. **제네릭 제약** — `where T : IComparable<T>`(3번).
3. **`IEquatable<T>` 구현** — `Equals(T)` 오버로드를 만든다(5번).
4. **`params` 타입 고르기** — `params object[]` 대신 `params int[]`·제네릭·`ReadOnlySpan<T>`(8번).
5. **보간 문자열** — `string.Format` 대신 `$"…"`(8번).

- ★ **값 타입을 받는 API 는 `object`·비제네릭 인터페이스 말고 제네릭 매개변수 + 제약**으로 잡는다.
- ★★ **그냥 둬도 되는 자리** — 한 번만 일어나는 것(시작 시 설정 읽기) · 호출 빈도가 낮은 것.\
  **24바이트가 문제가 되려면 루프 안이라야 한다**(4번의 1000번 = 24000바이트).
- ★★★ **반드시 지워야 하는 자리 셋** — **루프 안** · **`Dictionary`·`HashSet` 의 키**(5번) ·\
  **로그·직렬화처럼 초당 수천 번 도는 경로**(8번).
- ★ **다만 이 문서가 말할 수 있는 것은 바이트이고 시간은 안 쟀다.**\
  할당이 곧 느림은 아니다 — **GC 압력으로 바뀌는 지점**은 이 문서의 범위 밖이다.

### 11. 잇는 자리

- **「제네릭이 런타임까지 타입을 유지한다」** — 목록의 **24번 주제**. ★★★ 4번의 정본이고 **`↔Java` 가 가장 크게 갈린다.**
- **「`IEquatable<T>` 로 박싱을 없앤다」** — [02번 — `struct` 대 `class` 고르기](../02-struct-vs-class-choosing/)의 (5)·(6).
- **「보간 문자열이 무엇으로 컴파일되나」** — 목록의 **47번 주제**. ★ 8번의 정본이다.
- **`ReferenceEquals(5, 5)` 가 거짓인 것** — [01번](../01-value-types-and-reference-types/)의 (6).\
  1번의 「박싱 1000번 = 24000바이트」와 **같은 사실을 다른 창으로** 본 것이다.
- **`params ReadOnlySpan<T>`**(C# 13) — 목록의 **46번 주제**(`Span<T>`).\
  8번의 `params int[]` 가 내는 **배열 32바이트까지** 지운다. ★ 이 문서는 **안 던졌다.**
- **제네릭 제약 `where`** — 목록의 **25번 주제**(3번의 `Gen<T>` 가 거기다).
- **컬렉션 선택** — [목록의 **10번 주제**](../10-collection-choosing-list-dictionary-hashset-queue-stack/)(4번의 선택 기준).

## 실행 검증

**무엇을 몇 번 어느 판에서 돌렸나** — 아래 블록은 전부 **.NET SDK 10.0.401 / 런타임 10.0.12 / `net10.0` / linux-x64** 에서\
캡처 스크립트로 받았다. **제출 직전에 전부 다시 돌려 `diff -rq` 로 대조했다.**

| 블록 | 무엇을 고정하나 | 명령 |
|---|---|---|
| `cs03b-alloc.cs` | ★★★ 박싱 **+24**(`bool` 도) · `Big` **+80** · 언박싱 **+0** · 1000번 **+24000** | `csc` + 실행 |
| `cs03b-il.cs` | ★★ `box` · `unbox.any` · `ViaInterface` 의 **`box` 둘** · `constrained.` | `csc -r:il.dll` + 실행 |
| `cs03b-iface.cs` | **+24 · +24 · +0 · +0 · +24** | `csc` + 실행 |
| `cs03b-generic.cs` | ★★★ `ArrayList` **+24000** · `List<int>` **+0** | 〃 |
| `cs03b-equals.cs` | **+0 · +0 · +24 · +48 · +0 · +24** | 〃 |
| `cs03b-unbox-fail.cs` | `InvalidCastException` 전문 · `run exit=134` | 〃 |
| `cs03b-unbox-rules.cs` | ★★★ **열거형은 통과 · `byte` 는 예외** | 〃 |
| `cs03b-hidden-il.cs` | ★★★ 보간·`+` 는 **`box` 없음** · `Format`·`params object[]` 는 **있음** | `csc -r:il.dll` + 실행 |
| `cs03b-hidden-alloc.cs` | **+32 · +64 · +56 · +88 · +32 · +0** | `csc` + 실행 |
| `cs03b-order.cs` | ★ 표준 출력이 예외보다 **먼저** 나온 것(파이프로 받아도) | 〃 |

**구현 의존 항목** — 다음은 **이 환경(.NET 10.0.12 · CoreCLR · x64 linux)에서만** 그렇다.

- ★★★ **박싱 하나가 24바이트인 것** — **객체 헤더 16바이트**가 x64 CoreCLR 의 값이다. **32비트에서 다르다.**
- ★★★ **보간 문자열이 박싱을 안 하는 것** — **C# 10의 컴파일 방식**이다.\
  **C# 9 이하에서는 `string.Format` 으로 풀려 박싱했다.** ★ **옛 판은 이 머신에 없어 못 던졌다.**
- ★★★ **열거형을 기반 타입으로 언박싱할 수 있는 것** — **CLI 의 관대함**이고 **C# 명세는 정확한 타입을 요구한다.**\
  ★ 「명세가 요구하는 것」과 「런타임이 받아 주는 것」이 **갈리는 자리**다.
- ★★ **`"n=" + n` 이 `Int32::ToString` → `String::Concat` 으로 풀리는 것** — Roslyn 의 코드 생성.
- ★ **IL 덤프의 `nop`** — `-optimize` 를 안 준 결과다. 켜면 사라진다.
- ★ **표준 출력이 예외보다 먼저 나온 것** — **이 런타임의 flush 동작**이다. **보장이 아니다.**
- 예외 메시지 문구 · 트레이스 형식 · 종료 코드 134 — 런타임 구현.

**언어가 보장하는 것**(구현이 바뀌어도 같다)

- **값 타입 → `object`·인터페이스가 박싱이고 암묵 변환인** 것.
- ★★ **박싱이 매번 새 객체를 만드는** 것 — **캐시가 없는 것이 규정**이다.
- **언박싱이 명시 캐스트이고, 타입이 안 맞으면 `InvalidCastException` 인** 것.
- **제네릭이 값 타입 인자에 대해 박싱하지 않는** 것(CLI 의 제네릭 인스턴스화).
- **`object.Equals(object, object)` 의 매개변수가 `object` 라 박싱이 필요한** 것.

**안 돌려 본 것 / 못 잰 것**

- **안 돌려 본 것** — **C# 9 이하의 보간 문자열**(옛 판이 없다) · **`-optimize` 를 켠 IL** ·\
  **`params ReadOnlySpan<T>`**(C# 13 — 목록의 **46번 주제**) · **`Unsafe.Unbox<T>`** ·\
  **박싱된 값 타입을 인터페이스로 제자리 변경하기**(방어적 복사와 같은 집안으로 보이나 **확인 안 했다**) ·\
  **`string.Format` 의 다른 오버로드** · **32비트 런타임** · **서버 GC**.
- **못 잰 것** — ★★ **「박싱이 얼마나 느린가」.**\
  이 문서가 잰 것은 **바이트**이고 **시간이 아니다.**\
  박싱의 진짜 비용은 **GC 압력**으로 나타나는데, 그것을 재려면 **할당률과 GC 일시정지를 함께 보는 하네스**가 필요하다.\
  ★ 그래서 이 문서는 **「느리다」를 한 번도 적지 않았다** — 적은 것은 「**몇 바이트를 쓴다**」뿐이다.

**버전이 올랐을 때 다시 돌려야 하는 것**

- ★★★ **8번의 다섯 줄** — 컴파일 방식이 바뀌면 **가장 먼저 움직인다.** `params` 쪽이 특히 그렇다.
- ★★ **6번의 열거형 언박싱** — CLI 의 관대함이 좁아지면 바뀐다.
- ★ **1번의 24·80** — 객체 헤더가 바뀌면 움직인다. **증분이 0 이냐 아니냐**는 안 움직인다.
- ★ **2번의 IL 명령 열** — Roslyn 이 바뀌면 움직인다.
