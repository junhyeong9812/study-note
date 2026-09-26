# csharp/syntax/03 — 박싱과 언박싱 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [ECMA-334 7판(2023-12)](https://ecma-international.org/publications-and-standards/standards/ecma-334/) · [Microsoft Learn — C# 언어 레퍼런스](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/) · [Learn — 값 형식](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/builtin-types/value-types) · [Learn — 참조 형식](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/keywords/reference-types) · [.NET API — `GC.GetAllocatedBytesForCurrentThread`](https://learn.microsoft.com/en-us/dotnet/api/system.gc.getallocatedbytesforcurrentthread)
> **실행 검증** — 이 문서의 모든 출력·진단·IL·할당 바이트는 **.NET SDK 10.0.401** ·\
> 런타임 **`.NET 10.0.12`**(`Microsoft.NETCore.App`) · 타겟 **`net10.0`** · **linux-x64** 에서 실제로 돌려 얻은 것이다(2026-09-24).\
> ★ 블록은 캡처 스크립트가 파일로 받아 조립기가 끼워 넣은 것이다 — 사람이 옮겨 적은 줄은 하나도 없다.
> ★★★ **진단 언어를 영어로 고정했다.** 안 그러면 **로캘을 따라 한국어로 나와 재현이 안 된다** —\
> 실측으로 받은 한국어 판이 ``error CS0029: 암시적으로 'string' 형식을 'int' 형식으로 변환할 수 없습니다.`` 였다.\
> 고정하는 법은 둘을 같이 거는 것이다 — 환경변수 **`DOTNET_CLI_UI_LANGUAGE=en`** 과 `csc` 플래그 **`-preferreduilang:en-US`**.
> **던진 형태** — MSBuild(`dotnet build`·`dotnet run`)를 **안 썼다.** Roslyn 컴파일러를 **직접** 부른다 —\
> 그래야 `bin/`·`obj/` 가 안 생기고, 진단 경로가 **절대 경로가 아니라 파일명**으로 나오며, 한 판이 0.3초 안에 끝난다.\
> 배너의 `csc` 는 아래 셸 함수이고, `ex.runtimeconfig.json` 은 아래 한 줄짜리 파일이다.
>
> ```text
> export DOTNET_CLI_TELEMETRY_OPTOUT=1 DOTNET_NOLOGO=1
> export DOTNET_CLI_UI_LANGUAGE=en            # ★★★ 안 주면 진단이 한국어로 나온다
> D=$(dirname "$(readlink -f "$(command -v dotnet)")")
> ls "$D"/packs/Microsoft.NETCore.App.Ref/10.0.12/ref/net10.0/*.dll | sed 's/^/-r:/' > refs.rsp
> echo '{"runtimeOptions":{"tfm":"net10.0","framework":{"name":"Microsoft.NETCore.App","version":"10.0.0"}}}' > ex.runtimeconfig.json
> csc() { dotnet exec "$D/sdk/10.0.401/Roslyn/bincore/csc.dll" \
>           -nologo -nostdlib -noconfig @refs.rsp \
>           -preferreduilang:en-US -langversion:latest -target:exe "$@"; }
> ```
>
> **`-debug` 를 안 줬다** — PDB 가 없으면 스택 트레이스에 **절대 경로와 줄 번호가 안 박힌다**.\
> 그래서 이 문서의 트레이스는 ``at Program.<Main>$(String[] args)`` 에서 끝나고, 어느 머신에서 돌려도 같다.
> **버전** — 박싱·언박싱은 **C# 1.0부터**(CLI 의 `box`/`unbox` 명령이 그 뿌리다).\
> 제네릭으로 박싱을 피하는 것은 **C# 2.0부터** · 보간 문자열 핸들러는 **C# 10부터**다.
> **경계** — 「값 타입이 무엇인가」는 [01번](../01-value-types-and-reference-types/), 「`struct` 를 언제 고르나」는 [02번](../02-struct-vs-class-choosing/)이 정본이다.\
> 여기는 **값 타입이 참조 세계로 올라갈 때 무슨 일이 나나**만 본다.\
> **제네릭 자체**는 목록의 **24번 주제**(런타임까지 타입이 남는 것 — `↔Java` 가 가장 크게 갈리는 자리),\
> **제네릭 제약**은 **25번**, **컬렉션 선택**은 **10번**, **문자열 보간**은 **47번 주제**가 정본이다.\
> `Nullable<T>` 의 박싱 특례는 [01번](../01-value-types-and-reference-types/)의 (7)에서 봤고, 정본은 [목록의 **08번 주제**](../08-nullable-value-types/)다.
>
> ★★ **흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | ★ **`GC.GetAllocatedBytesForCurrentThread()` 의 절댓값**(프로세스 시작부터의 누적이다) | ★★★ **두 호출 사이의 증분**과 **그 증분이 0 이냐 아니냐** |
> | `Stopwatch` 로 잰 **ns 수치** · 그때의 CPU 상태 | **자릿수 차이**(10배·40배 같은 비율) |
> | `GetHashCode()` 값 · 객체 주소 | **진단 코드**(`CS0029` 류) · **진단 문구** · **`(행,열)`** |
> | 빌드 시간 · `dotnet` 패치 버전이 오르면 달라질 수 있는 것 | **`cc exit` 와 `run exit`**(갈라 적었다) |
> | — | **IL 명령어 열**(`box` · `unbox.any` · `ldobj` · `initobj` · `newobj`) |

## 한눈에 — 쉽게 말하면

**박싱은 「숫자를 상자에 담아 사물함에 넣는 것」이다.** 상자값이 **24바이트**이고, 넣을 때마다 **새 상자**다.

참조만 담을 수 있는 자리(`object`·인터페이스·`ArrayList`)에 값 타입을 넣으려면\
**힙에 객체를 하나 만들어 그 안에 값을 복사해야** 한다. 그게 박싱이다.

| 비유 | 실체 |
|---|---|
| **숫자를 상자에 담는다** | `object o = 42;` — ★ **힙에 24바이트** |
| **상자값이 늘 같다** | `int`·`long`·`double`·`bool` 전부 **24바이트**((1)) |
| ★ **큰 물건은 큰 상자** | 64바이트 구조체는 **80바이트**((1)) |
| **상자에서 꺼내는 것** | `int n = (int)o;` — ★★ **꺼내는 건 공짜다**(0바이트)((1)) |
| ★★★ **상자 겉에 타입이 적혀 있다** | 언박싱은 **정확히 그 타입**이라야 한다 — `(long)o` 는 **던진다**((6)) |
| ★★ **상자를 안 쓰는 길** | **제네릭** — `List<int>` 는 **0바이트**((4)) |
| ★★★ **모르고 담는 자리** | `string.Format` · `params object[]` — **IL 에 `box` 가 찍혀 있다**((7)) |

- ★★★ **이 주제의 창은 「할당 바이트」다.** 박싱은 **에러도 경고도 안 내고 조용히 힙을 쓴다** —\
  `GC.GetAllocatedBytesForCurrentThread()` 의 증분이 **그것을 보는 유일한 창**이다.
- ★★★ **그 다음 창이 IL 이다.** 소스에 `box` 라는 글자가 없어도 **IL 에는 있다**((2)·(7)).\
  「여기서 박싱이 나나?」는 **IL 을 보면 추측이 필요 없다.**
- ★★ **예상이 뒤집히는 자리가 (7)이다** — `$"n={n}"` 과 `"n=" + n` 은 **이 판에서 박싱을 안 한다.**\
  `string.Format("n={0}", n)` 과 `params object[]` 는 **한다.** 셋이 같아 보이는데 갈린다.

```text
   object o = 42;   가 하는 일

   스택                    힙
   +---------+            +--------------------------+
   | o : ●───┼──────────> | 객체 헤더 16바이트          |
   +---------+            | 값    42     (4바이트)     |
                          | (정렬 패딩)                |
                          +--------------------------+
                            └─ 합 24바이트 (실측 +24)

   int n = (int)o;  가 하는 일
                          상자 안의 4바이트를 n 자리로 복사한다
                          ★ 새 객체를 안 만든다 → 할당 +0
```

```text
   ★★★ 같은 일을 세 가지로 쓰면 — 박싱이 나는 곳과 안 나는 곳

   $"n={n}"                  IL: AppendFormatted<int>      → box 없음   (+32바이트, 문자열뿐)
   "n=" + n                  IL: Int32::ToString, Concat   → box 없음   (+64바이트, 문자열 둘)
   string.Format("n={0}", n) IL: ★ box System.Int32        → 박싱       (+56바이트)
   SumObj(n, n)              IL: ★ newarr object; box ×2   → 박싱 둘     (+88바이트)
   SumInt(n, n)              IL: newarr int32; stelem.i4   → box 없음   (+32바이트)

   ★ 「보간 문자열은 박싱한다」는 이 판에서 틀렸다 — 던져서 확인할 것이지 외울 것이 아니다.
```

> **박싱(boxing)** — 값 타입의 값을 **힙 객체에 복사해 담는 것**. 그 결과는 **참조 타입**이다.\
> 예: `object o = 42;` 는 힙에 24바이트를 얻고 거기에 `42` 를 복사한다.

> **언박싱(unboxing)** — 박싱된 객체에서 **값을 도로 꺼내는 것**.\
> **정확한 타입**이라야 하고, 아니면 `InvalidCastException` 이다((6)). ★ **할당은 0** 이다((1)).

> **`box` / `unbox.any`** — 박싱·언박싱을 하는 IL 명령. **소스에 안 보여도 IL 에는 보인다**((2)).

> **제네릭 인스턴스화** — C# 제네릭은 **값 타입마다 전용 코드를 만든다**.\
> 그래서 `List<int>` 가 `int` 를 **박싱 없이** 담는다((4)). `↔Java` 와 가장 크게 갈리는 자리다.

## 이 주제가 답하려는 질문

1. **박싱이 어디서 나나** — 소스만 보고 짚을 수 있나, 아니면 **무엇을 봐야** 하나((1)·(2)·(7)).
2. **얼마를 내나** — **바이트로** 말할 수 있나. 그리고 **언박싱도 내나**((1)).
3. **어떻게 피하나** — 제네릭이 그것을 **왜** 없애나((4)), 그리고 **못 피하는 자리**는 어디인가((3)).

## 동작 방식

### (0) 이 주제가 쓰는 창 — 그리고 IL 을 보는 법

| 창 | 무엇을 보여 주나 | 이 주제에서 |
|---|---|---|
| ★★★ **할당 바이트** | ★★★ **박싱이 났는지, 몇 바이트인지** | (1)·(3)·(4)·(5)·(7) |
| ★★★ **IL** | ★★★ **`box` 가 어디 찍혔는지** — 소스에 안 보이는 것 | (2)·(7) |
| **예외 전문** | 언박싱이 실패했을 때 | (6) |
| **실행 출력** | 언박싱이 **어떤 타입에 허용되는지** | (6) |
| **컴파일 진단** | ★ 이 주제에서는 **거의 안 나온다** — 그것 자체가 특징이다 | — |

★★★ **박싱은 컴파일 진단을 안 낸다.** 합법적인 암묵 변환이라 **에러도 경고도 없다** —\
이 주제가 「에러가 교재인 갈래」와 정반대인 이유이고, **그래서 할당 바이트가 유일한 창**이 된다.

★★ **IL 은 외부 도구 없이 얻었다.** `ilspycmd`·`ildasm` 을 **깔지 않았다**(네트워크·디스크를 더 쓴다).\
대신 **BCL 만으로** 된다 — 메서드 본문 바이트는 `MethodBody.GetILAsByteArray()` 가 주고,\
옵코드 표는 `System.Reflection.Emit.OpCodes` 의 `public static` 필드를 **리플렉션으로 긁어** 만든다.

```csharp
// cs-il.cs
using System;
using System.Reflection;
using System.Reflection.Emit;

// 네 번째 창 — 메서드의 IL 을 찍는다. 외부 도구(ilspycmd·ildasm)를 쓰지 않고
// BCL 만으로 한다: 메서드 본문 바이트는 MethodBody.GetILAsByteArray() 로 받고,
// 옵코드 표는 OpCodes 의 public static 필드를 리플렉션으로 긁어 만든다.
public static class Il {
    static readonly OpCode[] One = new OpCode[256];
    static readonly OpCode[] Two = new OpCode[256];

    static Il() {
        foreach (var f in typeof(OpCodes).GetFields(BindingFlags.Public | BindingFlags.Static)) {
            var op = (OpCode)f.GetValue(null)!;
            if (op.Size == 1) One[op.Value & 0xFF] = op; else Two[op.Value & 0xFF] = op;
        }
    }

    public static void Dump(Type t, string method) {
        var m = t.GetMethod(method, BindingFlags.Public | BindingFlags.NonPublic
                                  | BindingFlags.Static | BindingFlags.Instance)!;
        Console.WriteLine($"--- {t.Name}.{method} ---");
        var body = m.GetMethodBody()!;
        foreach (var lv in body.LocalVariables)
            Console.WriteLine($"  .locals [{lv.LocalIndex}] {Short(lv.LocalType)}");
        byte[] il = body.GetILAsByteArray()!;
        int i = 0;
        while (i < il.Length) {
            int at = i;
            OpCode op;
            if (il[i] == 0xFE) { op = Two[il[i + 1]]; i += 2; } else { op = One[il[i]]; i += 1; }
            string arg = "";
            switch (op.OperandType) {
                case OperandType.InlineNone: break;
                case OperandType.ShortInlineI:
                case OperandType.ShortInlineVar: arg = " " + il[i]; i += 1; break;
                case OperandType.InlineI: arg = " " + BitConverter.ToInt32(il, i); i += 4; break;
                case OperandType.InlineVar: arg = " " + BitConverter.ToInt16(il, i); i += 2; break;
                case OperandType.ShortInlineBrTarget:
                    arg = " IL_" + (i + 1 + (sbyte)il[i]).ToString("x4"); i += 1; break;
                case OperandType.InlineBrTarget:
                    arg = " IL_" + (i + 4 + BitConverter.ToInt32(il, i)).ToString("x4"); i += 4; break;
                case OperandType.InlineString:
                    arg = " \"" + m.Module.ResolveString(BitConverter.ToInt32(il, i)) + "\""; i += 4; break;
                case OperandType.InlineMethod:
                case OperandType.InlineField:
                case OperandType.InlineType:
                case OperandType.InlineTok: {
                    int tok = BitConverter.ToInt32(il, i); i += 4;
                    try { arg = " " + Member(m, tok); } catch { arg = " (token)"; }
                    break;
                }
                case OperandType.InlineSig: i += 4; arg = " (sig)"; break;
                case OperandType.ShortInlineR: i += 4; arg = " (r4)"; break;
                case OperandType.InlineR: arg = " " + BitConverter.ToDouble(il, i); i += 8; break;
                case OperandType.InlineI8: arg = " " + BitConverter.ToInt64(il, i); i += 8; break;
                case OperandType.InlineSwitch: {
                    int n = BitConverter.ToInt32(il, i); i += 4 + 4 * n; arg = " (switch)"; break;
                }
                default: i = il.Length; break;
            }
            Console.WriteLine($"  IL_{at:x4}: {op.Name}{arg}");
        }
    }

    static string Member(MethodBase ctx, int tok) {
        var ga = ctx.DeclaringType?.GetGenericArguments();
        var ma = ctx.IsGenericMethod ? ctx.GetGenericArguments() : null;
        var mi = ctx.Module.ResolveMember(tok, ga, ma)!;
        if (mi is Type t) return Short(t);
        var owner = mi.DeclaringType is null ? "?" : Short(mi.DeclaringType);
        return owner + "::" + mi.Name;
    }

    static string Short(Type t) {
        if (!t.IsGenericType) return t.FullName ?? t.Name;
        var n = (t.FullName ?? t.Name);
        n = n.Substring(0, n.IndexOf('`'));
        var args = string.Join(",", Array.ConvertAll(t.GetGenericArguments(), Short));
        return n + "<" + args + ">";
    }
}
```

★ 이 파일을 `csc -target:library -out:il.dll cs-il.cs` 로 한 번 만들어 두고,\
블록마다 `csc -r:il.dll …` 으로 참조한다. **덤프는 `-optimize` 없이(기본 디버그) 낸 것**이라\
`nop` 이 섞여 있고 소스 구조가 그대로 보인다.

★★ **한 가지 더 — 이 문서는 표준 출력과 예외를 한 블록에 섞지 않았다.**\
섞으면 파이프로 받을 때 순서가 뒤집히는 언어가 있기 때문이다. **이 런타임은 어떤지 한 번 던져 봤다.**

```text
===== 소스: cs03b-order.cs =====
using System;

Console.WriteLine("표준 출력 1");
Console.WriteLine("표준 출력 2");
Console.WriteLine("표준 출력 3");
object o = 42;
long n = (long)o;
Console.WriteLine(n);
===== csc -out:ex.dll cs03b-order.cs && dotnet ex.dll (cc exit=0 · run exit=134) =====
표준 출력 1
표준 출력 2
표준 출력 3
Unhandled exception. System.InvalidCastException: Unable to cast object of type 'System.Int32' to type 'System.Int64'.
   at Program.<Main>$(String[] args)
```

- ★ **CoreCLR 10 은 종료 전에 표준 출력을 비운다** — 파이프로 받아도 **세 줄이 예외보다 먼저** 나왔다.\
  ★★ **그래도 이 문서는 섞지 않았다** — 「이 판에서 유지됐다」는 **보장이 아니라 관찰**이고,\
  (6)의 예외 블록은 **stdout 을 한 줄도 안 찍게** 만들었다.

### (1) ★★★ 박싱은 힙을 쓰고, 언박싱은 안 쓴다

**언제 쓰나** — 「박싱이 비싸다」는 말을 **바이트로** 확인할 때. **이 절이 이 주제의 중심이다.**

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

| 박싱한 것 | 증분 | 읽는 법 |
|---|---|---|
| `int`(4바이트) | **+24** | 헤더 16 + 값 4 + 패딩 |
| `long`·`double`(8바이트) | **+24** | ★ **같다** — 헤더가 지배한다 |
| `bool`(1바이트) | **+24** | ★★ **같다** — 1바이트를 담는 데 24바이트다 |
| `Point`(8바이트 구조체) | **+24** | 〃 |
| `Big`(64바이트 구조체) | **+80** | 헤더 16 + 64 |
| ★★ **언박싱**(`(int)o`) | ★★★ **+0** | **새 객체를 안 만든다** |
| 박싱 1000번 | **+24000** | ★ **하나도 재사용되지 않는다** |

- ★★★ **`bool` 하나를 박싱하는 데 24바이트**다. **담는 값의 크기가 아니라 객체 헤더가 비용의 대부분**이다.\
  ★ 그래서 「작은 값이니까 괜찮다」가 **가장 틀린 직관**이다.
- ★★★ **언박싱은 0바이트**다. 「박싱/언박싱이 비싸다」에서 비싼 쪽은 **박싱뿐**이다.\
  ★ 언박싱은 **상자 안의 바이트를 복사해 오는 것**이라 새 객체가 필요 없다((2)의 `unbox.any`).
- ★★★ **박싱 1000번에 24000바이트** — **캐시가 없다.**\
  ★★ `↔Java` 에서 크게 갈리는 자리다. Java 는 `Integer` 를 **-128\~127 에서 캐싱**해\
  같은 작은 값이면 **객체를 재사용**하지만, **C# 에는 그 캐시가 없다.**\
  [01번](../01-value-types-and-reference-types/)의 (6)에서 `ReferenceEquals(5, 5)` 가 **`False`** 였던 것이 같은 사실이다.
- ★★ **절댓값은 흔들리는 칸**이다. 이 표의 근거는 **증분**이고, 더 중요한 것은 **0 이냐 아니냐**다.

### (2) IL — `box` 와 `unbox.any`

**언제 쓰나** — 「여기서 박싱이 나나?」를 **추측하지 않고** 볼 때.

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

| 메서드 | 핵심 명령 | 읽는 법 |
|---|---|---|
| `Box(int n)` | ★ **`box System.Int32`** | 소스의 `object o = n;` 한 줄이 이것이다 |
| `Unbox(object o)` | ★ **`unbox.any System.Int32`** | 할당이 없다((1)의 +0) |
| `ViaInterface(int n)` | ★★★ **`box` 가 둘** | **올릴 때 한 번, 인자로 넘길 때 또 한 번** |
| `ViaGeneric<T>(T n)` | ★★★ **`constrained. T` → `callvirt`** | ★★★ **`box` 가 없다** |

- ★★★ **`ViaInterface` 에 `box` 가 두 개**다. `IComparable c = n;` 에서 하나,\
  `c.CompareTo(0)` 의 **인자**(`IComparable.CompareTo(object)`)에서 또 하나.\
  ★ **인터페이스로 올리면 인자까지 박싱된다** — (3)이 그것을 바이트로 확인한다.
- ★★★ **`constrained.` 접두사가 제네릭의 답**이다.\
  「`T` 가 값 타입이면 **박싱하지 말고 그 타입의 메서드를 직접** 불러라」는 뜻이고,\
  런타임이 **`T` 마다 전용 코드를 만들어** 그것을 가능하게 한다((4)).
- ★★ **소스에는 `box` 라는 글자가 한 번도 안 나온다.** 그것이 이 절의 값어치다 —\
  **박싱은 문법이 아니라 변환**이라 소스를 아무리 읽어도 안 보인다.

### (3) 인터페이스로 올릴 때 — 두 번 박싱된다

**언제 쓰나** — 「`IComparable` 로 받으면 편한데」 할 때.

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

| 쓴 것 | 할당 | 왜 |
|---|---|---|
| `IComparable c = n;` | **+24** | ★ 인터페이스는 **참조 타입 자리**다 |
| `c.CompareTo(0)` | **+24** | ★★ 인자 `0` 이 **`object` 로 박싱**된다 |
| `Gen<int>(n, 0)`(제네릭 제약) | ★★★ **+0** | `IComparable<T>` 로 제약하면 박싱이 없다 |
| `n.CompareTo(0)` | **+0** | `int.CompareTo(int)` 오버로드가 직접 뽑힌다 |
| `Obj(n)`(`object` 매개변수) | **+24** | 매개변수 타입이 `object` 다 |

- ★★★ **`IComparable`(비제네릭)과 `IComparable<T>`(제네릭)의 차이가 여기서 24바이트 대 0바이트**다.\
  **제네릭 인터페이스와 제네릭 제약**이 그 둘을 없앤다.
- ★★ **구조체가 인터페이스를 구현해도 박싱이 사라지지 않는다** —\
  **인터페이스 타입 변수에 담는 순간** 박싱이다. 피하려면 **제네릭 제약**으로 받는다.
- ★ **API 설계의 결론** — 값 타입을 받는 API 는 `object`·비제네릭 인터페이스 말고\
  **제네릭 매개변수 + 제약**으로 받는다. `where T : IComparable<T>` 가 그 형태다(목록의 **25번 주제**).

### (4) ★★ 제네릭이 박싱을 없앤다 — `List<int>` 대 `ArrayList`

**언제 쓰나** — 「제네릭이 왜 좋은가」를 **한 줄로** 말할 때.

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

| 쓴 것 | 할당 | 왜 |
|---|---|---|
| `ArrayList.Add(i)` 1000번 | ★ **+24000** | 원소마다 **박싱** |
| `List<int>.Add(i)` 1000번 | ★★★ **+0** | ★★★ **`int[]` 에 그냥 들어간다** |
| `ArrayList` 에서 1000번 꺼내기 | **+0** | 언박싱은 할당이 없다((1)) |
| `List<int>` 에서 1000번 꺼내기 | **+0** | 꺼낼 것이 없다 |

- ★★★ **`+24000` 대 `+0`** — 「제네릭이 왜 필요한가」의 답이 이 두 숫자다.\
  ★ 용량(`capacity: 1000`)을 미리 줘서 **배열 재할당을 측정 밖으로 뺐다** — 그래서 남은 것이 **박싱뿐**이다.
- ★★★ **이것이 `↔Java` 에서 가장 크게 갈리는 자리**다.\
  Java 의 제네릭은 **타입 소거**라 `List<Integer>` 가 런타임에 `List<Object>` 이고 **원소가 전부 박싱된 `Integer`** 다.\
  C# 은 **런타임까지 타입이 남아** `List<int>` 가 **진짜 `int[]`** 를 든다.\
  ★ 정본은 목록의 **24번 주제**다.
- ★ **꺼낼 때는 둘 다 0** 이다 — 언박싱에 할당이 없기 때문이다. **비용은 넣을 때 다 났다.**

### (5) `object.Equals` 오버로드가 박싱을 부른다

**언제 쓰나** — 「같은지 비교하는데 왜 할당이 나지?」 할 때.

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

| 쓴 것 | 할당 | 왜 |
|---|---|---|
| `a.Equals(b)`(둘 다 `int`) | **+0** | ★ `int.Equals(int)` **오버로드가 있다** |
| `a.Equals(ob)`(`ob` 는 이미 박싱됨) | **+0** | ★★ **이미 박싱된 것을 넘기면 추가 비용이 없다** |
| `a.Equals((object)b)` | **+24** | ★ **여기서 박싱한다** |
| `object.Equals(a, b)` | **+48** | ★★ **둘 다** 박싱된다 |
| `int.GetHashCode()` | **+0** | 오버라이드가 있다 |
| 구조체의 `GetHashCode()` | ★ **+24** | ★★ **`ValueType.GetHashCode()` 는 `this` 를 박싱**한다 |

- ★★★ **마지막 줄이 조용한 자리**다 — 오버라이드가 없는 구조체를 `Dictionary` **키로 쓰면**\
  **해시를 구할 때마다 24바이트**를 낸다. ★ [02번](../02-struct-vs-class-choosing/)의 (5)와 같은 집안이다.
- ★★ **오버로드가 있는지가 전부**다. `int` 는 `Equals(int)` 와 `GetHashCode()` 오버라이드를 둘 다 갖고 있어 공짜다.\
  **내 구조체에는 그게 없다** — `IEquatable<T>` 를 구현하거나 `record struct` 를 쓴다([02번](../02-struct-vs-class-choosing/)의 (5)·(6)).
- ★ **`a.Equals(ob)` 가 0인 것**은 **`ob` 가 이미 박싱돼 있었기** 때문이다.\
  박싱 비용이 **사라진 게 아니라 앞줄에서 이미 났다.**

### (6) ★★ 언박싱이 실패하면 — `InvalidCastException`

**언제 쓰나** — 「`object` 에서 꺼내려는데 터진다」 할 때.

```text
===== 소스: cs03b-unbox-fail.cs =====
object o = 42;
long n = (long)o;
System.Console.WriteLine(n);
===== csc -out:ex.dll cs03b-unbox-fail.cs && dotnet ex.dll (cc exit=0 · run exit=134) =====
Unhandled exception. System.InvalidCastException: Unable to cast object of type 'System.Int32' to type 'System.Int64'.
   at Program.<Main>$(String[] args)
```

- ★★★ **`int` 를 박싱해 놓고 `(long)` 으로 꺼내면 던진다** — ``Unable to cast object of type 'System.Int32' to type 'System.Int64'.``\
  **언박싱은 암묵 숫자 변환을 안 한다.** `(long)(int)o` 처럼 **두 단계**로 써야 한다.
- ★★ **트레이스가 `at Program.<Main>$(String[] args)` 에서 끝난다** — **PDB 를 안 만들었기** 때문이다.\
  그래서 절대 경로·줄 번호가 안 박히고 **어느 머신에서 돌려도 같다.** `run exit=134`(SIGABRT)다.
- ★ **이 블록은 표준 출력을 한 줄도 안 찍는다** — 예외와 섞지 않으려고 일부러 그렇게 만들었다((0)).

무엇이 되고 무엇이 안 되는지 전수로 던져 보면 이렇다.

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

| 쓴 것 | 결과 | 읽는 법 |
|---|---|---|
| `(int)o`(`o` 는 박싱된 `int`) | **42** | 정확한 타입이라 된다 |
| `(long)(int)o` | **42** | ★ **두 단계**로 쓴다 |
| `o is int` / `o is long` | **`True` / `False`** | ★ **패턴 매칭도 정확한 타입만** 본다 |
| `o as string` | `(null)` | `as` 는 **참조 타입에만** 쓰고 실패하면 `null` 이다 |
| `(long)o` | **`InvalidCastException`** | 한 단계로는 안 된다 |
| ★★★ **박싱된 `enum` 을 `(int)` 로** | ★★★ **예외가 안 났다 — `1`** | ★★★ **런타임이 열거형과 그 기반 타입을 같게 본다** |
| 박싱된 `byte` 를 `(int)` 로 | **`InvalidCastException`** | ★ **숫자끼리는 안 봐준다** |

- ★★★ **여섯째 줄이 예상을 뒤집는 자리**다. `(int)e`(`e` 는 박싱된 `MyEnum`)가 **통과한다.**\
  ★★ **C# 명세는 「정확한 타입」을 요구하지만 CLI(ECMA-335)는 열거형과 그 기반 타입의 언박싱을 허용**한다.\
  **런타임이 언어보다 관대한 자리**이고, 그래서 **컴파일러가 통과시키면 런타임이 받아 준다.**
- ★★ **바로 다음 줄이 그 관대함의 경계**다 — `byte` 를 `(int)` 로 꺼내는 것은 **던진다.**\
  ★ **「숫자니까 되겠지」가 안 통한다** — 되는 것은 **열거형 ↔ 기반 타입**뿐이다.
- ★ **안전하게 쓰는 법** — `o is int n` 패턴이나 `o as 타입` 을 쓴다. `as` 는 **참조 타입과 `T?`** 에만 쓸 수 있다.

### (7) ★★★ 숨은 박싱 — 던져서 확인할 것이지 외울 것이 아니다

**언제 쓰나** — 「로그 한 줄 찍는데 할당이 나나?」 할 때. ★★ **여기서 흔한 상식이 반은 틀린다.**

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

| 쓴 것 | IL | 박싱이 있나 |
|---|---|---|
| `$"n={n}"` | `DefaultInterpolatedStringHandler::AppendFormatted` | ★★★ **없다** |
| `"n=" + n` | `Int32::ToString` → `String::Concat` | ★★ **없다** |
| `string.Format("n={0}", n)` | ★★★ **`box System.Int32`** | ★★★ **있다** |
| `SumObj(params object[])` | ★★★ **`newarr System.Object` + `box` ×2** | ★★★ **있다 — 배열까지** |
| `SumInt(params int[])` | `newarr System.Int32` + `stelem.i4` | **없다** |

할당으로도 확인했다.

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

- ★★★ **「보간 문자열은 박싱한다」가 이 판에서 틀렸다.**\
  C# 10 부터 보간 문자열은 **`DefaultInterpolatedStringHandler`** 로 컴파일되고,\
  그 `AppendFormatted<T>(T value)` 가 **제네릭**이라 박싱이 안 난다.\
  ★ **`string.Format` 은 `params object[]` 를 받으므로 여전히 박싱한다** — 셋이 같아 보이는데 갈린다.
- ★★★ **`params object[]` 가 가장 비싸다(+88)** — **배열 하나 + 박싱 둘**이다.\
  ★ `params int[]`(또는 C# 13의 `params ReadOnlySpan<T>`)로 받으면 **배열만**(+32) 든다.
- ★★ **`"n=" + n` 이 64바이트인 것**은 **`int.ToString()` 의 문자열 하나 + 결과 문자열 하나**다.\
  박싱은 없는데 **할당이 가장 많다** — ★★★ **「할당이 있다」와 「박싱이 있다」는 다른 질문**이다.\
  이 표의 두 창(IL 과 바이트)을 **갈라서 읽어야** 그것이 보인다.
- ★★★ **결론 — 박싱은 판마다 다르므로 던져 본다.** 이 절의 다섯 줄은 **.NET 10 의 관찰**이고,\
  **C# 9 이하에서는 보간 문자열도 `string.Format` 으로 풀려 박싱했다.**

## 문법 — 형태와 규칙

### 형태

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

규칙 불릿.

- **박싱은 값 타입 → `object`·`dynamic`·인터페이스 **암묵 변환**이다.** 캐스트를 안 써도 일어난다.
- **박싱 하나가 이 판에서 24바이트**(값이 8바이트 이하일 때)이고, **캐시가 없다**((1)).
- **언박싱은 명시 캐스트**(`(int)o`)이고 **할당이 0** 이다((1)).
- ★★★ **언박싱은 정확한 타입이라야 한다**((6)). 예외는 **열거형 ↔ 기반 타입** 하나다.
- **제네릭이 박싱을 없앤다**((4)) — 값 타입마다 전용 코드가 만들어지기 때문이다.
- ★ **인터페이스로 올리면 박싱**이고, **제네릭 제약**으로 받으면 안 난다((3)).
- ★★ **`object.Equals`·`ValueType.GetHashCode` 같은 「`object` 를 받는 멤버」가 박싱을 부른다**((5)).
- ★★★ **보간 문자열과 `+` 연결은 이 판에서 박싱을 안 하고, `string.Format` 과 `params object[]` 는 한다**((7)).

### 금지 사례 — 던져서 받은 둘

| 쓴 것 | 무엇이 나오나 |
|---|---|
| 박싱된 `int` 를 `(long)` 으로 | ``System.InvalidCastException: Unable to cast object of type 'System.Int32' to type 'System.Int64'.`` |
| 박싱된 `byte` 를 `(int)` 로 | ``System.InvalidCastException: Unable to cast object of type 'System.Byte' to type 'System.Int32'.`` |

★★ **그리고 「금지되지 않는 것」이 이 주제의 본체다** — 박싱 자체는 **에러도 경고도 없다.**\
표에 넣을 자리가 없고, 그래서 **할당 바이트가 유일한 창**이 된다((0)).

### 박싱을 지우는 도구 다섯

1. **제네릭 컬렉션** — `List<int>`·`Dictionary<int, V>`((4)).
2. **제네릭 제약** — `where T : IComparable<T>`((3)).
3. **`IEquatable<T>` 구현** — `Equals(T)` 오버로드를 만든다((5), [02번](../02-struct-vs-class-choosing/)).
4. **`params` 를 제네릭·`int[]`·`ReadOnlySpan<T>` 로** — `params object[]` 를 피한다((7)).
5. **보간 문자열** — `string.Format` 대신 `$"…"`((7)).

## 어디서 틀리나

### 1. ★★★ 「박싱은 작은 값이면 싸다」

**`bool` 하나도 24바이트**다((1)). **비용의 대부분이 객체 헤더**라 **담는 값의 크기와 거의 무관**하다.

### 2. ★★★ 「박싱/언박싱이 비싸다」

**비싼 쪽은 박싱뿐**이다((1)). **언박싱은 0바이트**이고, IL 로도 `unbox.any` 한 명령이다((2)).

### 3. ★★★ 「보간 문자열은 박싱한다」

**이 판에서는 안 한다**((7)). C# 10부터 `DefaultInterpolatedStringHandler` 로 풀리고\
`AppendFormatted<T>` 가 **제네릭**이다. ★ **`string.Format` 은 여전히 박싱한다.**

### 4. ★★★ 「같은 값이면 상자를 재사용한다」

**안 한다**((1)) — 박싱 1000번에 **24000바이트**다.\
★★ **`↔Java`** — Java 는 `Integer` 를 -128\~127 에서 캐싱하지만 **C# 에는 그 캐시가 없다.**\
[01번](../01-value-types-and-reference-types/)의 (6)에서 `ReferenceEquals(5, 5)` 가 **`False`** 였다.

### 5. ★★ 「구조체가 인터페이스를 구현하면 박싱이 없다」

**인터페이스 타입에 담는 순간 박싱**이다((3)). 구현 여부가 아니라 **담는 자리**가 정한다.\
★ 피하려면 **제네릭 제약**으로 받는다.

### 6. ★★ 「언박싱은 숫자끼리 알아서 맞춰 준다」

**안 맞춰 준다**((6)). `(long)o` 는 던지고 `(long)(int)o` 라야 한다.\
★ **예외는 열거형 ↔ 기반 타입 하나**이고, **`byte` → `int` 는 던진다.**

### 7. ★★ 「`Dictionary` 키로 구조체를 쓰면 빠르다」

**`GetHashCode()` 오버라이드가 없으면 호출마다 24바이트**다((5)).\
★ `record struct` 나 `IEquatable<T>` + `GetHashCode()` 오버라이드가 필요하다.

### 8. ★ 「할당이 있으면 박싱이다」

**다른 질문이다**((7)). `"n=" + n` 은 **박싱이 없는데 할당이 64바이트**다(문자열 둘).\
★ **IL 로 「박싱이 있나」를, 바이트로 「얼마를 쓰나」를 갈라서 본다.**

### 9. ★ 「`as` 로 언박싱한다」

**`as` 는 참조 타입과 `T?` 에만** 쓴다((6)). `o as int` 는 컴파일이 안 되고 `o as int?` 라야 한다.

### 10. 「Java 의 오토박싱과 같다」

**두 칸이 다르다.** ① **캐시가 없다**((1)) ② **제네릭이 박싱을 지운다**((4)) —\
Java 는 타입 소거라 `List<Integer>` 의 원소가 **전부 박싱된 객체**다.

## 구현 세부사항 대 언어 보장

| 사실 | 누가 보장하나 |
|---|---|
| **값 타입 → `object`·인터페이스가 박싱인** 것 · **암묵 변환인** 것 | **언어**(ECMA-334) |
| **언박싱이 명시 캐스트이고 타입이 안 맞으면 `InvalidCastException` 인** 것 | **언어** |
| ★★ **박싱이 매번 새 객체를 만드는** 것 | ★★ **언어**다 — 명세가 「새 객체를 할당한다」로 적혀 있다. **캐시가 없는 것이 규정**이다 |
| **제네릭이 값 타입 인자에 대해 박싱하지 않는** 것 | **CLI**(ECMA-335)의 제네릭 인스턴스화 |
| ★★★ **박싱 하나가 24바이트인** 것 · **큰 구조체가 80바이트인** 것 | ★★★ **CoreCLR 10 · x64 의 구현**(헤더 16). **32비트에서 다르다** |
| ★★★ **열거형을 기반 타입으로 언박싱할 수 있는** 것 | ★★★ **CLI 의 관대함**이다 — **C# 명세는 정확한 타입을 요구한다.** 언어보다 런타임이 넓은 자리 |
| ★★★ **보간 문자열이 박싱을 안 하는** 것 | ★★★ **C# 10 의 컴파일 방식**(보간 문자열 핸들러)이다. **C# 9 이하에서는 `string.Format` 으로 풀려 박싱했다** |
| ★ **`"n=" + n` 이 `Int32::ToString` → `String::Concat` 으로 풀리는** 것 | ★ **Roslyn 의 코드 생성**이다 |
| ★ **`(object)(int?)` 가 `Nullable` 을 벗기는** 것 | ★ **CLI 의 박싱 규칙**([01번](../01-value-types-and-reference-types/)의 (7)) |
| ★ **IL 명령 이름**(`box`·`unbox.any`·`constrained.`) | ★ **CLI 의 명령 집합**이다 — 이름 자체는 표준이지만 **어디 찍히는지는 컴파일러 몫**이다 |
| 예외 메시지 문구 · 트레이스 형식 | **런타임 구현** |

## 언제 쓰고 언제 안 쓰나

**박싱을 그냥 둬도 되는 자리**\
① **한 번만 일어나는 것** — 설정 읽기·시작 시 한 번.\
② **이미 참조 타입인 것을 다루는 코드** — 박싱이 안 난다.\
③ **호출 빈도가 낮은 것.** ★ **24바이트가 문제가 되려면 루프 안이라야 한다.**

**반드시 지워야 하는 자리 셋**\
① **루프 안**((4)의 1000번 = 24000바이트) ② **`Dictionary`·`HashSet` 의 키**((5))\
③ **로그·직렬화처럼 초당 수천 번 도는 경로**((7)).

**지우는 법** — 제네릭 컬렉션 · 제네릭 제약 · `IEquatable<T>` · `params` 타입 고르기 · 보간 문자열.

**★ 다만 먼저 재라.** 이 문서가 말할 수 있는 것은 **바이트**이고, **시간은 안 쟀다.**\
할당이 곧 느림은 아니다 — **GC 압력으로 바뀌는 지점**은 이 문서의 범위 밖이다.

## 핵심 문장

1. **박싱은 힙을 쓰고 언박싱은 안 쓴다** — +24 대 +0.
2. **비용은 담는 값이 아니라 객체 헤더가 낸다** — `bool` 하나도 24바이트다.
3. **C# 에는 박싱 캐시가 없다** — 1000번이면 24000바이트다(`↔Java`).
4. **제네릭이 박싱을 지운다** — `List<int>` 는 0, `ArrayList` 는 24000.
5. **언박싱은 정확한 타입이라야 한다** — 예외는 **열거형 ↔ 기반 타입** 하나뿐이다.
6. **「할당이 있다」와 「박싱이 있다」는 다른 질문이다** — IL 과 바이트를 갈라서 본다.
7. **박싱이 나는 자리는 판마다 다르다 — 던져 본다.** 보간 문자열은 .NET 10 에서 안 한다.

## 관련 자료

- [01번 — 값 타입과 참조 타입](../01-value-types-and-reference-types/) — ★ **선행.**\
  (1)의 「박싱 1000번 = 24000바이트」가 거기 (6)의 `ReferenceEquals(5, 5)` 와 같은 사실이다.
- [02번 — `struct` 대 `class` 고르기](../02-struct-vs-class-choosing/) — ★★ (5)의 `Equals` 박싱이 거기 (5)의 **+48** 이다.\
  **거기는 「무엇을 고르나」, 여기는 「고른 것이 참조 세계로 갈 때」.**
- [04번 — 변수 선언·`var`·타겟 타입 `new`](../04-var-and-target-typed-new/) — `var` 가 **정적 타입**이라\
  박싱이 어디서 나는지 **컴파일 타임에 정해진다**는 것이 거기서 이어진다.
- 목록의 **24번 주제**(제네릭) — ★★★ **(4)의 정본.**\
  「C# 제네릭이 런타임까지 타입을 유지한다」가 거기이고, **`↔Java` 가 가장 크게 갈리는 자리**다.
- 목록의 **25번 주제**(제네릭 제약 `where`) — ★ (3)의 `where T : IComparable<T>` 가 거기다.
- [목록의 **10번 주제**](../10-collection-choosing-list-dictionary-hashset-queue-stack/)(컬렉션 선택) — (4)의 `List` 대 `ArrayList` 선택 기준.
- 목록의 **19번 주제**(동등성 규칙) — (5)의 계약 쪽 정본.
- 목록의 **47번 주제**(문자열 — 보간·`StringBuilder`) — ★ (7)의 정본.\
  「보간 문자열이 무엇으로 컴파일되나」가 거기서 본론이 된다.
- [목록의 **08번 주제**](../08-nullable-value-types/)(`Nullable<T>`) — 박싱 특례.
- 목록의 **46번 주제**(`Span<T>`) — `params ReadOnlySpan<T>`(C# 13)가 (7)의 배열 할당까지 지우는 길.

## 용어 풀이

> **박싱(boxing)** — 값 타입의 값을 힙 객체에 **복사해 담는 것**. 결과는 참조 타입이다.\
> 예: `object o = 42;` — 이 판에서 **24바이트**.

> **언박싱(unboxing)** — 박싱된 객체에서 값을 도로 꺼내는 것. **할당은 0** 이고 **정확한 타입**이라야 한다.

> **`box` / `unbox.any`** — 박싱·언박싱의 IL 명령. **소스에 `box` 라는 글자가 없어도 IL 에는 있다**((2)).

> **`constrained.`** — 제네릭 메서드에서 「`T` 가 값 타입이면 박싱하지 말고 직접 불러라」는 IL 접두사.\
> 제네릭이 박싱을 없애는 원리가 이것이다((2)).

> **객체 헤더(object header)** — 힙 객체마다 붙는 고정 비용. 이 판에서 **16바이트**(메서드 테이블 포인터 + 동기화 블록).\
> 박싱 비용의 대부분이 여기다.

> **보간 문자열 핸들러(interpolated string handler)** — C# 10부터 `$"…"` 가 풀리는 대상.\
> `AppendFormatted<T>` 가 제네릭이라 **박싱이 안 난다**((7)).

> **타입 소거(type erasure)** — Java 제네릭이 런타임에 타입 인자를 지우는 것.\
> C# 은 **안 지운다** — 그래서 `List<int>` 가 진짜 `int[]` 를 든다((4)).

## 더 들어가면

- **`params ReadOnlySpan<T>`**(C# 13) — (7)의 `params int[]` 가 내는 **배열 32바이트까지** 지운다. ★ 안 던졌다.
- **`Unsafe.Unbox<T>`** — 박싱된 값을 **참조로** 꺼내는 것. ★ 안 던졌다.
- **박싱된 값 타입을 제자리에서 바꾸기** — 인터페이스를 통한 변경이 **상자 안의 복사본**을 바꾸는지.\
  ★ **안 던졌다** — [02번](../02-struct-vs-class-choosing/)의 방어적 복사와 같은 집안일 것으로 보이나 **확인하지 않았다.**
- **GC 세대와 박싱** — 24바이트가 언제 문제가 되는지. ★ **이 문서의 범위 밖**이고 [`foundations/memory-management/`](../../../../memory-management/)가 정본이다.
- **C# 9 이하의 보간 문자열** — (7)의 결론이 **판에 달렸다**는 것을 확인하려면 옛 판을 돌려야 한다.\
  ★ **이 머신에는 .NET 10 만 있어 못 던졌다.**
- **`string.Format` 의 오버로드** — `string.Format(string, object)` 말고 **제네릭 오버로드**가 있는지.\
  ★ 안 봤다. 이 문서가 던진 것은 `string.Format("n={0}", n)` **한 형태**다.
