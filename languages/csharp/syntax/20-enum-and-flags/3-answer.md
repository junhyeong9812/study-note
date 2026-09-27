# csharp/syntax/20 — `enum` 과 `[Flags]` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·진단·IL·할당 바이트는 **.NET SDK 10.0.401** · 런타임 **10.0.12** · 타겟 **`net10.0`** ·
> **linux-x64** 에서 실제로 돌려 얻은 것이다(2026-09-26). 대비는 **javac 21.0.5** 다.\
> 진단은 **`-preferreduilang:en-US`** 로 영어로 고정했다.\
> ★ 블록은 캡처 스크립트가 파일로 받아 조립기가 끼워 넣은 것이다 — 손으로 옮긴 줄은 없다.\
> ★ 진단을 싣는 블록은 전부 **그 진단을 낸 소스를 같은 블록 안에** 다시 싣는다(`===== 소스: … =====`).
> **읽는 법** — **진단 문구·IL 오프셋 폭**은 흔들리는 칸이다. ★★★ **`HasFlag` 의 바이트는 판마다 다르다 — 그것이 답이다.**\
> 근거로 쓰는 것은 **옵코드 · 진단 코드와 `(행,열)` · 네 판에서 갈린 줄 수와 그 자리 · `IsJITOptimizerDisabled`** 다.
> ★★★ **이 문서는 시간을 재지 않았다.** 「`HasFlag` 가 느리다」는 문장이 **한 줄도 없다.**

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ **`99` · `99` · `False` · `Red`** — 예외 없음, 캐스트는 **명령 0개**

**출력**

```text
===== 소스: cs20b-int.cs =====
using System;
enum Color { Red, Green, Blue }
static class Probe {
    public static bool  IsRed(Color c) => c == Color.Red;
    public static Color Make()         => (Color)99;
    public static int   ToInt(Color c) => (int)c;
}
class Program {
    static void Main() {
        Color c = (Color)99;
        Console.WriteLine($"[1] c.ToString()      : {c}");
        Console.WriteLine($"[2] (int)c            : {(int)c}");
        Console.WriteLine($"[3] Enum.IsDefined(c) : {Enum.IsDefined(c)}");
        Console.WriteLine($"[4] default(Color)    : {default(Color)}");
        Il.Dump(typeof(Probe), "IsRed");
        Il.Dump(typeof(Probe), "Make");
        Il.Dump(typeof(Probe), "ToInt");
    }
}
===== csc -r:il.dll -out:ex.dll cs20b-int.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
[1] c.ToString()      : 99
[2] (int)c            : 99
[3] Enum.IsDefined(c) : False
[4] default(Color)    : Red
--- Probe.IsRed ---
  IL_0000: ldarg.0
  IL_0001: ldc.i4.0
  IL_0002: ceq
  IL_0004: ret
--- Probe.Make ---
  IL_0000: ldc.i4.s 99
  IL_0002: ret
--- Probe.ToInt ---
  IL_0000: ldarg.0
  IL_0001: ret
```

**왜 그런가**

- ★★★ **`(Color)99` 는 에러도 예외도 없다.** `ToString` 은 이름이 없으니 **`99`** 를 찍는다.
- ★★★ **`Make()` 는 `ldc.i4.s 99` · `ret` 두 줄** — **캐스트 명령이 없다.** `ToInt` 도 `ldarg.0` · `ret` 뿐이다. **런타임에 `Color` 는 `int` 와 구별되지 않는다.**
- ★★ **`IsRed` 는 `ldc.i4.0` + `ceq`** — `Color.Red` 는 **정수 상수 0** 으로 박혔다(8번의 원인).
- ★ **`Enum.IsDefined` 가 `False`** — 막는 것은 코드의 몫이다. **`default(Color)` 는 `Red`**(0 이니까).

### 2. ★★★ `[Flags]` 는 **`ToString` 만 바꾼다** — `|` 는 늘 되고 `Parse` 는 늘 받는다

**출력**

```text
===== 소스: cs20b-flags.cs =====
using System;
[Flags] enum Perm  { None = 0, Read = 1, Write = 2, Exec = 4 }
        enum Plain {           Read = 1, Write = 2, Exec = 4 }      // [Flags] 가 없다
class Program {
    static void Main() {
        Console.WriteLine($"[1] Perm.Read | Perm.Exec    : {Perm.Read | Perm.Exec}");
        Console.WriteLine($"[2] Plain.Read | Plain.Exec  : {Plain.Read | Plain.Exec}");
        Console.WriteLine($"[3] (Perm)8                  : {(Perm)8}");
        Console.WriteLine($"[4] (Perm)9                  : {(Perm)9}");
        Console.WriteLine($"[5] (Perm)0                  : {(Perm)0}");
        Console.WriteLine($"[6] Enum.Parse<Perm>(\"Read, Write\")  : {Enum.Parse<Perm>("Read, Write")}");
        Console.WriteLine($"[7] Enum.Parse<Plain>(\"Read, Write\") : {Enum.Parse<Plain>("Read, Write")}");
        Console.WriteLine($"[8] Enum.IsDefined(Perm.Read | Perm.Exec) : {Enum.IsDefined(Perm.Read | Perm.Exec)}");
    }
}
===== csc -out:ex.dll cs20b-flags.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
[1] Perm.Read | Perm.Exec    : Read, Exec
[2] Plain.Read | Plain.Exec  : 5
[3] (Perm)8                  : 8
[4] (Perm)9                  : 9
[5] (Perm)0                  : None
[6] Enum.Parse<Perm>("Read, Write")  : Read, Write
[7] Enum.Parse<Plain>("Read, Write") : 3
[8] Enum.IsDefined(Perm.Read | Perm.Exec) : False
```

**왜 그런가**

- ★★★ **`[1]` `Read, Exec` · `[2]` `5`** — 같은 값 5 가 **특성 하나로** 이름 목록과 숫자로 갈렸다.
- ★★★ **`[2]` 는 컴파일된다** — `|` 는 `[Flags]` 가 허락하는 연산이 **아니다**. 모든 enum 에 된다.
- ★★ **`[4]` `9`** — `Read, 8` 이 아니다. 8 에 이름이 없으면 **전체를 숫자로** 찍는다. **`[3]` `8`** · **`[5]` `None`**(0 에 이름이 있다).
- ★★★ **`[7]` `3`** — `[Flags]` 없는 `Plain` 도 **쉼표 목록을 받아 OR 했다.** 그러나 `ToString` 은 `3` — **왕복이 안 맞는다.**
- ★★ **`[8]` `False`** — `IsDefined` 는 **이름 붙은 단일 값**만 안다. **플래그 조합 검증에 쓰면 정상 값을 거절한다.**

### 3. ★★ `All` 은 **`CS8524`** · `Missing` 은 **`CS8509`** — 둘 다 경고, 실행하면 **`SwitchExpressionException`**

**출력**

```text
===== 소스: cs20b-switch.cs =====
using System;
enum Color { Red, Green, Blue }
class Program {
    static string All(Color c) => c switch {
        Color.Red => "빨강", Color.Green => "초록", Color.Blue => "파랑" };      // 이름 붙은 값을 전부 적었다
    static string Missing(Color c) => c switch {
        Color.Red => "빨강", Color.Green => "초록" };                           // Blue 를 빠뜨렸다
    static void Main() {
        Console.Error.WriteLine($"All(Color.Blue) = {All(Color.Blue)}");
        try { Console.Error.WriteLine($"All((Color)99) = {All((Color)99)}"); }
        catch (Exception e) { Console.Error.WriteLine($"잡힘 : {e.GetType().Name}"); }
    }
}
===== csc -out:ex.dll cs20b-switch.cs 2>&1 | sort && dotnet ex.dll (cc exit=0 · run exit=0) =====
cs20b-switch.cs(4,37): warning CS8524: The switch expression does not handle some values of its input type (it is not exhaustive) involving an unnamed enum value. For example, the pattern '(Color)3' is not covered.
cs20b-switch.cs(6,41): warning CS8509: The switch expression does not handle all possible values of its input type (it is not exhaustive). For example, the pattern 'Color.Blue' is not covered.
All(Color.Blue) = 파랑
잡힘 : SwitchExpressionException
```

**왜 그런가**

- ★★★ **`CS8524`** — 이름을 다 적어도 「**이름 없는 enum 값**(예: `(Color)3`)이 안 다뤄졌다」. 1번에서 봤듯 **그 값은 합법**이다.
- ★★★ **`CS8509`** — `Color.Blue` 가 빠졌다. **다른 코드**다.
- ★★ **둘 다 경고**(`cc exit=0`) — 빌드는 된다. 실행하면 `All(Color.Blue)` 는 `파랑`, **`All((Color)99)` 는 `SwitchExpressionException`**.
- ★ 경고를 없애는 법은 **`_ => throw …`**(2-summary 의 형태) — 이름 없는 값까지 받는다.

### 4. ★★★ `p.HasFlag` 는 **세 판 48000 · 한 판 0** — 갈린 줄 **1 / 4**

**출력**

```text
===== 소스: cs20b-alloc.cs =====
using System;
[Flags] enum Perm { None = 0, Read = 1, Write = 2, Exec = 4 }
class Program {
    static long M(Action a) {
        a();                                             // 한 판 데워 놓고
        var b = GC.GetAllocatedBytesForCurrentThread();
        a();
        return GC.GetAllocatedBytesForCurrentThread() - b;
    }
    static void Main() {
        int sink = 0;
        Perm p = Perm.Read | Perm.Exec;
        Enum boxed = p;
        Console.WriteLine($"p.HasFlag(Perm.Exec)         1000회 : {M(() => { for (int i = 0; i < 1000; i++) sink += p.HasFlag(Perm.Exec) ? 1 : 0; })} 바이트");
        Console.WriteLine($"(p & Perm.Exec) != 0         1000회 : {M(() => { for (int i = 0; i < 1000; i++) sink += (p & Perm.Exec) != 0 ? 1 : 0; })} 바이트");
        Console.WriteLine($"boxed.HasFlag(Perm.Exec)     1000회 : {M(() => { for (int i = 0; i < 1000; i++) sink += boxed.HasFlag(Perm.Exec) ? 1 : 0; })} 바이트");
        Console.WriteLine($"p.ToString()                 1000회 : {M(() => { for (int i = 0; i < 1000; i++) sink += p.ToString().Length; })} 바이트");
        Console.WriteLine($"(합 {sink})");
    }
}
===== csc -out:ex.dll cs20b-alloc.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
p.HasFlag(Perm.Exec)         1000회 : 48000 바이트
(p & Perm.Exec) != 0         1000회 : 0 바이트
boxed.HasFlag(Perm.Exec)     1000회 : 24000 바이트
p.ToString()                 1000회 : 72000 바이트
(합 26000)
===== csc -out:ex.dll cs20b-alloc.cs && DOTNET_TieredCompilation=0 dotnet ex.dll (cc exit=0 · run exit=0) =====
p.HasFlag(Perm.Exec)         1000회 : 48000 바이트
(p & Perm.Exec) != 0         1000회 : 0 바이트
boxed.HasFlag(Perm.Exec)     1000회 : 24000 바이트
p.ToString()                 1000회 : 72000 바이트
(합 26000)
===== csc -optimize -out:exo.dll cs20b-alloc.cs && dotnet exo.dll (cc exit=0 · run exit=0) =====
p.HasFlag(Perm.Exec)         1000회 : 48000 바이트
(p & Perm.Exec) != 0         1000회 : 0 바이트
boxed.HasFlag(Perm.Exec)     1000회 : 24000 바이트
p.ToString()                 1000회 : 72000 바이트
(합 26000)
===== csc -optimize -out:exo.dll cs20b-alloc.cs && DOTNET_TieredCompilation=0 dotnet exo.dll (cc exit=0 · run exit=0) =====
p.HasFlag(Perm.Exec)         1000회 : 0 바이트
(p & Perm.Exec) != 0         1000회 : 0 바이트
boxed.HasFlag(Perm.Exec)     1000회 : 24000 바이트
p.ToString()                 1000회 : 72000 바이트
(합 26000)
===== 네 판 대조 — 「바이트」 줄마다 네 판의 값이 같은가 =====
네 판에서 갈린 줄 1 / 4
```

**왜 그런가**

- ★★★ **`csc` 기본 두 판 48000 · `csc -optimize` × 티어링 기본 48000 · `csc -optimize` × `TieredCompilation=0` 0.**\
  **한 판만 쟀으면 「박싱한다」와 「안 한다」 중 어느 쪽이든 적을 수 있었다** — 규칙 24 가 막은 사고다.
- ★★ **`boxed.HasFlag` 24000(네 판 모두)** — `this` 는 **이미 박싱돼** 있고 **인자 하나만** 박싱한다. `p.HasFlag` 는 둘(IL 의 `box Perm` 둘).
- ★ **`p.ToString()` 72000**(문자열을 만든다) · **비트 연산 0**.

### 5. ★★ 진단은 **탐침 7·8 둘뿐** — `E4.B` 는 **`A`** 로 찍힌다

**출력**

```text
===== 소스: cs20b-probe.cs =====
using System;

// 탐침 1 — [Flags] 인데 값이 2의 거듭제곱이 아니고 겹친다
[Flags] enum F1 { Read = 1, Write = 2, Both = 3, Exec = 3 }

// 탐침 2 — [Flags] 인데 0 에 이름이 없다
[Flags] enum F2 { Read = 1, Write = 2 }

// 탐침 3 — 0 에 해당하는 멤버가 없는 enum
enum E3 { A = 1, B = 2 }

// 탐침 4 — 두 이름이 같은 값을 가진다
enum E4 { A = 1, B = 1 }

enum Color { Red, Green, Blue }

class Program {
    static void Main() {
        Color c = Color.Red;
        Console.WriteLine($"탐침 5 : c == 0 → {c == 0}");                                        // 리터럴 0 과 비교
        switch (c) { case Color.Red: Console.WriteLine("탐침 6 : switch 문"); break; }          // 일부만 다룬 switch 문
        Console.WriteLine($"탐침 7 : {c switch { Color.Red => 1, Color.Green => 2 }}");           // Blue 가 빠진 switch 식
        Console.WriteLine($"탐침 8 : {c switch { Color.Red => 1, Color.Green => 2, Color.Blue => 3 }}");
        Console.WriteLine($"탐침 9 : E3.A | E3.B → {E3.A | E3.B}");                             // [Flags] 없는 enum 에 |
        Console.WriteLine($"탐침 10 : default(E3) → {default(E3)} · IsDefined → {Enum.IsDefined(default(E3))}");
        Console.WriteLine($"탐침 4 : E4.B → {E4.B} · E4.A == E4.B → {E4.A == E4.B}");
    }
}
===== csc -warn:9 -out:ex.dll cs20b-probe.cs 2>&1 | sort && dotnet ex.dll (cc exit=0 · run exit=0) =====
cs20b-probe.cs(22,39): warning CS8509: The switch expression does not handle all possible values of its input type (it is not exhaustive). For example, the pattern 'Color.Blue' is not covered.
cs20b-probe.cs(23,39): warning CS8524: The switch expression does not handle some values of its input type (it is not exhaustive) involving an unnamed enum value. For example, the pattern '(Color)3' is not covered.
탐침 5 : c == 0 → True
탐침 6 : switch 문
탐침 7 : 1
탐침 8 : 1
탐침 9 : E3.A | E3.B → 3
탐침 10 : default(E3) → 0 · IsDefined → False
탐침 4 : E4.B → A · E4.A == E4.B → True
===== csc -warn:9 -out:ex.dll cs20b-probe.cs 2>&1 | grep -o "cs20b-probe.cs([0-9]*" | sort -u | wc -l    # 탐침 10개 중 진단이 붙은 줄은 몇 개인가 (exit=0) =====
2
```

**왜 그런가**

- ★★★ **진단이 붙은 줄 2** — `CS8509`(탐침 7) · `CS8524`(탐침 8). **둘 다 `switch` 식**이다.
- ★★★ **탐침 4 `E4.B → A`** — `A` 와 `B` 가 같은 값 1 이라 **런타임은 어느 이름인지 모른다.** `ToString` 이 하나를 골라 찍었다.
- ★★ **탐침 5 `c == 0` 은 컴파일된다**(`True`) — 리터럴 `0` 은 어느 enum 으로든 암시적 변환된다(Learn). **`1` 이면 `CS0019`**(6번).
- ★★ **탐침 6(`switch` 문)은 진단 없음**, 탐침 7(`switch` 식)은 `CS8509` — **완결성은 식에만** 있다.
- ★ 탐침 1·2(`[Flags]` 설계 규칙 위반)·3·9·10 은 **침묵**. 탐침 10 — `default(E3)` 가 **`0`**, `IsDefined` **`False`**.

### 6. ★★ **`CS0019` · `CS0221` · `CS0266` · `CS0266`**

**출력**

```text
===== 소스: cs20b-err.cs =====
enum Color { Red, Green, Blue }
enum Small : byte { A = 1 }
class Program {
    static void Main() {
        Color c = Color.Red;
        _ = c == 1;                 // 리터럴 1 과 비교
        _ = (Small)300;             // 기반 타입 범위 밖의 상수
        Color d = 2;                // 정수를 그대로 대입
        int n = Color.Blue;         // enum 을 그대로 int 에
        _ = (d, n);
    }
}
===== csc -out:ex.dll cs20b-err.cs 2>&1 | sort (cc exit=1) =====
cs20b-err.cs(6,13): error CS0019: Operator '==' cannot be applied to operands of type 'Color' and 'int'
cs20b-err.cs(7,13): error CS0221: Constant value '300' cannot be converted to a 'Small' (use 'unchecked' syntax to override)
cs20b-err.cs(8,19): error CS0266: Cannot implicitly convert type 'int' to 'Color'. An explicit conversion exists (are you missing a cast?)
cs20b-err.cs(9,17): error CS0266: Cannot implicitly convert type 'Color' to 'int'. An explicit conversion exists (are you missing a cast?)
```

**왜 그런가**

- ★★★ **`c == 1` 은 `CS0019`** — `0` 이 아닌 리터럴은 비교도 안 된다.
- ★★★ **`(Small)300` 은 `CS0221`** — **상수**가 `byte` 범위를 넘었다. 컴파일러가 **상수이니까** 잡았다.
- ★★ **`Color d = 2` · `int n = Color.Blue` 는 `CS0266`** — 캐스트 없이는 어느 방향도 안 된다.
- ★ **변수였다면** 컴파일은 되고 값이 **잘릴** 것이다([05번](../05-numeric-types-checked-decimal/)의 `unchecked` 기본값) — **이 판에서 enum 으로는 던지지 않았다.**

### 7. ★★★ **디버그 빌드는 JIT 최적화를 끄고**, 릴리스 빌드는 **데워진 뒤에만** 박싱이 사라진다

**출력**

```text
===== 소스: cs20b-dbg.cs =====
using System;
using System.Diagnostics;
using System.Reflection;
class Program {
    static void Main() {
        var d = Assembly.GetExecutingAssembly().GetCustomAttribute<DebuggableAttribute>();
        Console.WriteLine(d is null ? "DebuggableAttribute 없음"
                                    : $"IsJITOptimizerDisabled={d.IsJITOptimizerDisabled} · IsJITTrackingEnabled={d.IsJITTrackingEnabled}");
    }
}
===== csc -out:ex.dll cs20b-dbg.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
IsJITOptimizerDisabled=True · IsJITTrackingEnabled=True
===== csc -optimize -out:ex.dll cs20b-dbg.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
IsJITOptimizerDisabled=False · IsJITTrackingEnabled=False
```

```text
===== 소스: cs20b-allocw.cs =====
using System;
[Flags] enum Perm { None = 0, Read = 1, Write = 2, Exec = 4 }
class Program {
    static long M(Action a) {
        for (int w = 0; w < 200; w++) a();               // 오래 데운다 — 티어 1 로 올라갈 시간을 준다
        System.Threading.Thread.Sleep(500);
        for (int w = 0; w < 200; w++) a();
        var b = GC.GetAllocatedBytesForCurrentThread();
        a();
        return GC.GetAllocatedBytesForCurrentThread() - b;
    }
    static void Main() {
        int sink = 0;
        Perm p = Perm.Read | Perm.Exec;
        Enum boxed = p;
        Console.WriteLine($"p.HasFlag(Perm.Exec)         1000회 : {M(() => { for (int i = 0; i < 1000; i++) sink += p.HasFlag(Perm.Exec) ? 1 : 0; })} 바이트");
        Console.WriteLine($"(p & Perm.Exec) != 0         1000회 : {M(() => { for (int i = 0; i < 1000; i++) sink += (p & Perm.Exec) != 0 ? 1 : 0; })} 바이트");
        Console.WriteLine($"boxed.HasFlag(Perm.Exec)     1000회 : {M(() => { for (int i = 0; i < 1000; i++) sink += boxed.HasFlag(Perm.Exec) ? 1 : 0; })} 바이트");
        Console.WriteLine($"p.ToString()                 1000회 : {M(() => { for (int i = 0; i < 1000; i++) sink += p.ToString().Length; })} 바이트");
        Console.WriteLine($"(합 {sink})");
    }
}
===== csc -out:ex.dll cs20b-allocw.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
p.HasFlag(Perm.Exec)         1000회 : 48000 바이트
(p & Perm.Exec) != 0         1000회 : 0 바이트
boxed.HasFlag(Perm.Exec)     1000회 : 24000 바이트
p.ToString()                 1000회 : 72000 바이트
(합 5213000)
===== csc -out:ex.dll cs20b-allocw.cs && DOTNET_TieredCompilation=0 dotnet ex.dll (cc exit=0 · run exit=0) =====
p.HasFlag(Perm.Exec)         1000회 : 48000 바이트
(p & Perm.Exec) != 0         1000회 : 0 바이트
boxed.HasFlag(Perm.Exec)     1000회 : 24000 바이트
p.ToString()                 1000회 : 72000 바이트
(합 5213000)
===== csc -optimize -out:exo.dll cs20b-allocw.cs && dotnet exo.dll (cc exit=0 · run exit=0) =====
p.HasFlag(Perm.Exec)         1000회 : 0 바이트
(p & Perm.Exec) != 0         1000회 : 0 바이트
boxed.HasFlag(Perm.Exec)     1000회 : 24000 바이트
p.ToString()                 1000회 : 72000 바이트
(합 5213000)
===== csc -optimize -out:exo.dll cs20b-allocw.cs && DOTNET_TieredCompilation=0 dotnet exo.dll (cc exit=0 · run exit=0) =====
p.HasFlag(Perm.Exec)         1000회 : 0 바이트
(p & Perm.Exec) != 0         1000회 : 0 바이트
boxed.HasFlag(Perm.Exec)     1000회 : 24000 바이트
p.ToString()                 1000회 : 72000 바이트
(합 5213000)
===== 네 판 대조 — 「바이트」 줄마다 네 판의 값이 같은가 =====
네 판에서 갈린 줄 1 / 4
```

**왜 그런가**

- ★★★ **`csc` 기본 → `IsJITOptimizerDisabled=True`** · **`csc -optimize` → `False`**. `HasFlag` 박싱을 없애는 것은 **JIT 최적화**다.\
  그래서 **`csc` 기본 두 판은 티어링이 뭐든, 얼마나 데우든 48000** 이다(두 블록 모두).
- ★★★ **`csc -optimize` × 티어링 기본** — 짧게 데우면 **48000**, **200회 + 0.5초 + 200회** 데우면 **0**.\
  짧게는 **티어 0(최적화 안 된 첫 JIT)** 코드를, 길게는 **티어 1(최적화 JIT)** 코드를 재고 있었다고 읽힌다.
- ★★★ **「JIT 이 `HasFlag` 박싱을 없앤다」는 「최적화된 어셈블리 + 최적화 JIT 코드」에서만 참**이다.
- ★ **직접 찍지 않은 것** — **티어링 상태 자체**(어느 메서드가 티어 몇인지). **데우는 양을 바꿨을 때 칸이 움직인 것**만 실측이고, 「티어 0/1」은 그것을 설명하는 **해석**이다.

### 8. ★★★ **`Yellow`** — `(int)` 은 `1` 그대로

**출력**

```text
===== 소스: cs20b-lib1.cs =====
public enum Color { Red, Green, Blue }
===== 소스: cs20b-app.cs =====
using System;
class Program {
    static void Main() {
        Color c = Color.Green;
        Console.WriteLine($"Color.Green 을 담은 변수 : {c} · (int) {(int)c}");
    }
}
===== csc -target:library -out:lib.dll cs20b-lib1.cs && csc -r:lib.dll -out:ex.dll cs20b-app.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
Color.Green 을 담은 변수 : Green · (int) 1
===== 소스: cs20b-lib2.cs =====
public enum Color { Red, Yellow, Green, Blue }     // 가운데에 하나 끼워 넣었다
===== csc -target:library -out:lib.dll cs20b-lib2.cs && dotnet ex.dll    # ex.dll 은 다시 컴파일하지 않았다 (cc exit=0 · run exit=0) =====
Color.Green 을 담은 변수 : Yellow · (int) 1
```

**왜 그런가**

- ★★★ **1번의 `IsRed` IL 처럼 `Color.Green` 은 앱 안에 정수 `1` 로 박혔다.** 새 라이브러리에서 **1 의 이름이 `Yellow`** 다.
- ★★ **진단 창이 못 보는 이유** — 앱을 **다시 컴파일하지 않았다.** 컴파일러가 관여할 틈이 원리상 없다.\
  그래서 **`ToString` 이 찍는 이름**으로 창을 바꿔 물었다(제5의 상태). ★ 비교(`== Color.Green`)는 이름을 안 거치니 **그 창도 못 본다.**
- ★ Java 는 **`ordinal()`** 에서 같은 모양을 잡았다 — 「상수 하나가 가운데 끼는 순간 **에러 없이 다른 값으로 읽힌다**」(Java 13번).

### 9. ★ 인스턴스 필드 **`value__` 하나** — 멤버는 전부 `static literal`

**출력**

```text
===== 소스: cs20b-refl.cs =====
using System;
using System.Reflection;
using System.Runtime.CompilerServices;
enum Color { Red, Green, Blue }
enum Small : byte { A = 1, B = 200 }
class Program {
    static void Main() {
        foreach (var f in typeof(Color).GetFields(BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance | BindingFlags.Static))
            Console.WriteLine($"필드 {f.Name,-8} static={f.IsStatic,-5} literal={f.IsLiteral,-5} 타입={f.FieldType.Name}");
        Console.WriteLine($"Color 의 BaseType = {typeof(Color).BaseType} · IsValueType = {typeof(Color).IsValueType}");
        Console.WriteLine($"기반 타입 : Color={Enum.GetUnderlyingType(typeof(Color)).Name} · Small={Enum.GetUnderlyingType(typeof(Small)).Name}");
        Console.WriteLine($"크기      : Color={Unsafe.SizeOf<Color>()} · Small={Unsafe.SizeOf<Small>()}");
    }
}
===== csc -out:ex.dll cs20b-refl.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
필드 value__  static=False literal=False 타입=Int32
필드 Red      static=True  literal=True  타입=Color
필드 Green    static=True  literal=True  타입=Color
필드 Blue     static=True  literal=True  타입=Color
Color 의 BaseType = System.Enum · IsValueType = True
기반 타입 : Color=Int32 · Small=Byte
크기      : Color=4 · Small=1
```

**왜 그런가**

- ★★★ **`value__`(`Int32`)** 가 enum 값의 **실체 전부**다.
- ★★ **`Red`·`Green`·`Blue` 는 `static=True literal=True`** — 메타데이터 상수다. **객체가 없다.**
- ★ **`BaseType = System.Enum` · `IsValueType = True`** · **`Small` 크기 1**, `Color` 4.

### 10. ★★ Java 는 **`incompatible types`** — 이름 없는 값이 **원리상 없다**

**출력**

```text
===== 소스: j20/Ex20.java =====
enum Color { RED, GREEN, BLUE }
public class Ex20 {
    public static void main(String[] a) {
        Color c = (Color) 99;                  // C# 처럼 정수를 캐스트해 본다
        System.out.println(c);
    }
}
===== javac -d j20out j20/Ex20.java (cc exit=1) =====
j20/Ex20.java:4: error: incompatible types: int cannot be converted to Color
        Color c = (Color) 99;                  // C# 처럼 정수를 캐스트해 본다
                          ^
1 error
===== 소스: j20/Ex20b.java =====
enum Color { RED, GREEN, BLUE }
public class Ex20b {
    public static void main(String[] a) {
        System.out.println(Color.class.getSuperclass() + " · GREEN.ordinal()=" + Color.GREEN.ordinal());
        try { System.out.println(Color.values()[99]); }
        catch (Exception e) { System.out.println("잡힘 : " + e.getClass().getSimpleName()); }
    }
}
===== javac -d j20out j20/Ex20b.java && java -cp j20out Ex20b (cc exit=0 · run exit=0) =====
class java.lang.Enum · GREEN.ordinal()=1
잡힘 : ArrayIndexOutOfBoundsException
```

**왜 그런가**

- ★★★ **`(Color) 99` 는 `incompatible types: int cannot be converted to Color`** — Java `enum` 은 클래스다.
- ★★ 정수에서 enum 을 얻는 길은 **`values()[i]`** 뿐이고, **`[99]` 는 `ArrayIndexOutOfBoundsException`** — **범위를 검사한다.**
- ★★★ **C# 만 이름 없는 값이 합법**이라 `switch` 식의 완결성이 **에러가 아니라 경고**로 내려앉았다(3번). Java `switch` 식·Kotlin `when` 은 **에러**다(각 갈래의 실측).
- ★ Kotlin 에서 값 하나를 감싸는 것은 **`value class`**(Kotlin 26번) · Rust `enum` 은 **변형마다 다른 데이터**를 싣는다(Rust 17번).

### 11. 잇기

- ★★ **정수 타입·`checked`** — [05번](../05-numeric-types-checked-decimal/).
- ★★ **`switch` 식 완결성 전반** — 목록의 **22번 주제**.
- ★ **같은 무대** — [17번](../17-interfaces-default-members-explicit-implementation/) (1)의 인터페이스 진화(다시 컴파일 안 한 앱이 새 라이브러리를 만난다).
- ★ **`ordinal()` 사고** — Java 갈래 목록([`java/syntax/README.md`](../../../java/syntax/README.md))의 **13번**([`13-enum-classes/`](../../../java/syntax/13-enum-classes/)).

## 실행 검증

| 무엇 | 몇 번·어디서 | 결과 |
|---|---|---|
| `cs20b-int.cs` `(Color)99` + IL | csc 1회 | ★★★ `99` · 예외 없음 · **`ldc.i4.s 99` 한 줄** |
| `cs20b-refl.cs` 리플렉션 | csc 1회 | ★★★ **`value__` 하나** · 멤버는 `static literal` · `byte` 면 크기 1 |
| `cs20b-flags.cs` `[Flags]` | csc 1회 | ★★★ `Read, Exec` 대 `5` · `Parse` 는 둘 다 받음 · `IsDefined(조합)` `False` |
| `cs20b-switch.cs` `switch` 식 | csc 1회 | ★★★ **`CS8524` · `CS8509`** · `SwitchExpressionException` |
| `cs20b-hfil.cs` `HasFlag` IL | csc 1회(`-optimize`) | ★★★ **`box Perm` 둘** |
| `cs20b-alloc.cs` 짧게 데움 | **2×2 판 격자** | ★★★ `HasFlag` **48000 ×3 · 0 ×1** · **갈린 줄 1 / 4** |
| `cs20b-allocw.cs` 길게 데움 | **2×2 판 격자** | ★★★ `HasFlag` **48000 ×2 · 0 ×2** · **갈린 줄 1 / 4** |
| `cs20b-dbg.cs` `DebuggableAttribute` | csc 2회 | ★★★ 기본 **`IsJITOptimizerDisabled=True`** · `-optimize` **`False`** |
| `cs20b-lib1/lib2/app.cs` 라이브러리 교체 | csc 3회 · 실행 2회 | ★★★ `Green` → **`Yellow`** · `(int) 1` |
| `cs20b-probe.cs` 탐침 열 | csc 1회(`-warn:9`) + 실행 | ★★★ **진단이 붙은 줄 2** · `E4.B → A` · `c == 0` 통과 |
| `cs20b-err.cs` | csc 1회 | **`CS0019`·`CS0221`·`CS0266` ×2** |
| `Ex20.java` · `Ex20b.java` | javac 2회 | ★★★ **`incompatible types`** · `values()[99]` 는 예외 |
| `cs20b-form.cs` 형태 | csc 1회 | `Read, Write · 3 · True · True · 3` · `경고` |

**구현 의존 항목** — 다음은 **이 판(.NET SDK 10.0.401 · 런타임 10.0.12 · javac 21.0.5)에서만** 그렇다.

- ★★★ **`HasFlag` 박싱이 어느 판에서 사라지나** — JIT 과 티어링 정책의 구현이다. **길게 데운 판은 시간에 기대므로 흔들릴 수 있다.**
- ★★ **`csc` 기본 빌드가 `IsJITOptimizerDisabled=True` 인 것** — 컴파일러의 기본값이다.
- ★★ **값이 같은 두 이름 중 `ToString` 이 `A` 를 고른 것** · **`value__` 라는 이름** · **`-warn:9` 탐침 열 중 둘**.

**언어가 보장하는 것**(구현이 바뀌어도 같다)

- **정수 ↔ enum 명시적 변환이 늘 되고 범위 검사가 없다** · **리터럴 `0` 의 암시적 변환** · **기본값 `(E)0`**.
- **enum 멤버는 컴파일 시점 상수** — 다른 어셈블리의 값이 **내 IL 에 박힌다**(8번).
- **상수의 범위 밖 캐스트는 에러**(`CS0221`) · **캐스트 없는 정수 ↔ enum 대입은 에러**(`CS0266`).

**안 돌려 본 것 / 못 잰 것 / 잴 것이 없는 것**

- **안 돌려 본 것** — ★★ **변수로 범위 밖 값을 `(Small)` 캐스트**(잘림) · ★★ **`Missing` 에 `Blue` 를 넣어 실행** ·\
  ★ **`[Obsolete]` 별칭** · ★ **`Enum.GetValues`/`GetNames` 의 할당** · ★ **Kotlin·Rust 의 열거형을 이 판에서 직접**.
- **못 잰 것** — ★★★ **티어링 상태 자체.** 7번의 「티어 0/1」은 **데우는 양을 바꿔 본 간접 증거**다.\
  ★★★ **시간** — 한 줄도 안 쟀다.
- **잴 것이 없는 것** — 없다. **④ 할당 바이트는 적용**이다.

**버전이 올랐을 때 다시 돌려야 하는 것**

- ★★★ **4·7번의 판 격자 두 벌** — 티어 0 이 `HasFlag` 를 인라인하기 시작하거나 디버그 빌드 정책이 바뀌면 **칸이 움직인다.** 반드시 **2×2 로** 다시 재라.
- ★★ **5번의 탐침** — Roslyn 이 `[Flags]` 설계 규칙이나 `switch` 문 완결성에 경고를 넣으면 **둘이 늘어난다.**
- ★ **1·2·6·8·9번** — 명세가 정한 것이라 바뀔 일이 없다. 바뀌면 그것이 뉴스다.
