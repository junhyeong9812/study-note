# csharp/syntax/20 — `enum` 과 `[Flags]` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> ★★★ 이 주제의 질문은 「**런타임에 `enum` 은 무엇인가**」 하나로 거의 다 풀린다 — 답이 막히면 IL 을 떠올려라.
> **환경** — .NET SDK 10.0.401 · 런타임 10.0.12 · `net10.0` · linux-x64 ·
> Roslyn `csc` 를 직접 부른다 · `-langversion:latest` · `-preferreduilang:en-US`. 대비는 **javac 21.0.5** 다.
> ★★★ **본체 창은 ① IL 덤프다.** ★★★ **④ 할당 바이트는 판 격자 두 벌**(짧게·길게 데우기)로 쟀다 — **한 판의 값으로 답하지 마라.**
> ★★ 라이브러리 교체 실험은 **진단 창이 원리상 못 보는 자리**라 **`ToString` 이 찍는 이름**으로 물었다(제5의 상태).
> 선행 — [05번](../05-numeric-types-checked-decimal/)(정수 타입)·[03번](../03-boxing-and-unboxing/)(박싱).

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (예측) / (왜) / (경계) / (연결) -->

### 1. ★★★ 정의 안 된 정수를 캐스트하면 (예측)

```csharp
// cs20b-int.cs
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
```

- `[1]`\~`[4]` 에 무엇이 찍히는가 — **예외가 나는가**?
- ★★★ `Make()` 의 IL 은 몇 줄이고, **캐스트에 해당하는 명령**이 있는가?
- ★★ `IsRed` 의 IL 에서 `Color.Red` 는 무엇으로 바뀌어 있는가?

### 2. ★★★ 특성 하나를 붙이고 뗐을 때 (예측)

```csharp
// cs20b-flags.cs
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
```

- `[1]`\~`[8]` 에 무엇이 찍히는가?
- ★★★ `[2]` 는 **컴파일이 되는가** — `[Flags]` 가 없는데 `|` 를 썼다.
- ★★ `[4]` 는 `Read, 8` 인가 다른 것인가?
- ★★★ `[7]` — `[Flags]` 없는 enum 의 `Parse` 가 쉼표 목록을 받는가?

### 3. ★★ 이름을 빠뜨린 `switch` 식과 다 적은 `switch` 식 (예측)

```csharp
// cs20b-switch.cs
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
```

- 컴파일하면 **어느 메서드**에 **어떤 코드**의 진단이 붙는가 — 경고인가 에러인가?
- ★★★ 이름을 **다 적은** `All` 에도 진단이 붙는가 — 붙는다면 무엇을 요구하는가?
- ★★ 실행하면 두 줄에 무엇이 찍히는가?

### 4. ★★★ 플래그 검사 네 가지의 할당 바이트 (예측)

```csharp
// cs20b-alloc.cs
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
```

- 네 줄 중 **0 이 아닌** 줄은 어느 것인가?
- ★★★ `p.HasFlag(Perm.Exec)` 는 **`csc` 기본 · `csc -optimize` × 티어링 기본 · `DOTNET_TieredCompilation=0`** 네 판에서 각각 몇 바이트인가?
- ★★ `boxed.HasFlag` 는 왜 `p.HasFlag` 의 절반인가?

### 5. ★★ 정수 위의 껍데기 주변에 심은 탐침들 (예측)

```csharp
// cs20b-probe.cs
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
```

- `-warn:9` 로 컴파일하면 **어느 탐침**에 진단이 붙는가?
- ★★★ 탐침 4 의 `E4.B` 는 무엇으로 찍히는가?
- ★★ 탐침 5 는 컴파일되는가 — `0` 대신 `1` 이면?
- ★ 탐침 6(`switch` **문**)과 탐침 7(`switch` **식**)의 진단은 어떻게 다른가?

### 6. ★★ 정수와 enum 사이의 에러들 (예측)

```csharp
// cs20b-err.cs
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
```

- 네 줄 각각의 **진단 코드**는?
- ★★ `(Small)300` 이 **변수**였다면 어떻게 됐을 것인가 — 이 판에서 던졌는가?

### 7. ★★★ `HasFlag` 의 바이트를 가른 것 (왜)

- `csc` 기본으로 만든 어셈블리의 `IsJITOptimizerDisabled` 는 무엇인가 — `csc -optimize` 는?
- ★★★ 그것이 4번 격자의 **`csc` 기본 두 판**을 어떻게 설명하는가?
- ★★★ `csc -optimize` × 티어링 기본 판은 **짧게 데울 때와 길게 데울 때** 각각 몇 바이트였나 — 무엇이 달라졌다고 읽히는가?
- ★★ 「.NET Core 이후 JIT 이 `HasFlag` 박싱을 없앴다」는 말은 **어떤 조건에서** 참인가?
- ★ 이 해석 중 **직접 찍지 않은 것**은 무엇인가?

### 8. ★★★ 라이브러리 enum 의 가운데에 멤버를 끼우면 (왜)

- 앱은 `Color { Red, Green, Blue }` 로 컴파일했고, 라이브러리만 `Color { Red, Yellow, Green, Blue }` 로 바꿔 끼웠다. `Color.Green` 을 담은 변수는 무엇으로 찍히는가?
- ★★★ 1번의 **어느 IL** 이 이 사고의 원인인가?
- ★★ 이 사고는 왜 **진단 창이 원리상 못 보는가** — 그래서 무엇으로 물었나?
- ★ Java 갈래에서 같은 모양의 사고를 무엇에서 잡았나?

### 9. ★ 리플렉션으로 본 enum 의 실체 (경계)

- `Color` 의 필드를 전부 찍으면 **인스턴스 필드**는 몇 개이고 이름은?
- ★★ `Red` 같은 멤버는 `static`·`literal` 인가?
- ★ `Color` 의 `BaseType` 과 `IsValueType` · `Small : byte` 의 크기는?

### 10. ★★ Java·Kotlin·Rust 의 열거형과 (경계)

- javac 에 `(Color) 99` 를 던지면? Java 에서 정수로 enum 을 얻는 유일한 길은 무엇이고, 그것은 범위를 검사하는가?
- ★★★ C# 만 가진 「이름 없는 값」이 **완결성 검사**를 어떻게 바꿨나?
- ★ Kotlin 에서 「값 하나를 감싼 껍데기」는 어느 기능이 맡는가? Rust 는 무엇을 더 싣는가?

### 11. 다른 주제와 잇기 (연결)

- ★★ `enum` 이 올라탄 **정수 타입·`checked`** 의 정본은 몇 번 주제인가?
- ★★ `switch` 식 **완결성 검사 전반**의 정본은 이 목록의 몇 번 주제인가?
- ★ 8번과 **같은 무대**(두 어셈블리 · 다시 컴파일 안 한 앱)를 쓴 주제는?
- ★ Java `ordinal()` 의 사고는 어느 갈래 몇 번인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
