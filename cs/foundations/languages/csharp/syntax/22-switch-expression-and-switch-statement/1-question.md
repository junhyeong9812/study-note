# csharp/syntax/22 — `switch` 식과 `switch` 문 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> ★★★ 이 주제의 질문은 「**팔들이 입력의 값 공간을 다 덮었나**」 하나로 거의 다 풀린다 — 답이 막히면 **남은 값**을 하나 찾아라.
> **환경** — .NET SDK 10.0.401 · 런타임 10.0.12 · `net10.0` · linux-x64 ·
> Roslyn `csc` 를 직접 부른다 · `-langversion:latest` · `-preferreduilang:en-US`. 대비는 **javac 21.0.5** 다.
> ★★★ **본체 창은 ② 진단 격자다** — 격자는 **스크립트가 칸을 센다.** IL 은 **한 블록**만 찍었다(2번).
> ★ **`enum` 의 완전성**(`CS8509`·`CS8524`)은 [20번](../20-enum-and-flags/)이 먼저 쟀다 — 여기서는 묻지 않는다.
> 선행 — [21번](../21-pattern-matching-type-property-relational-list/)(패턴).

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (예측) / (왜) / (경계) / (연결) -->

### 1. ★★★ `enum` 밖의 완전성 격자 (예측)

```csharp
// cs22b-grid.cs
abstract class Shape { }
sealed class Circle : Shape { }
sealed class Square : Shape { }
sealed class Tri : Shape { }
static class G {
    static int B1(bool b)    => b switch { true => 1, false => 0 };
    static int B2(bool b)    => b switch { true => 1 };
    static int I1(int x)     => x switch { < 0 => -1, 0 => 0, > 0 => 1 };
    static int I2(int x)     => x switch { < 0 => -1, > 0 => 1 };
    static int I3(int x)     => x switch { >= 0 and < 10 => 1, >= 10 => 2 };
    static int Y1(byte x)    => x switch { <= 127 => 0, >= 128 => 1 };
    static int D1(double d)  => d switch { < 0 => -1, >= 0 => 1 };
    static int C1(char c)    => c switch { >= 'a' and <= 'z' => 1 };
    static int S1(Shape s)   => s switch { Circle => 1, Square => 2, Tri => 3 };
    static int S2(Shape s)   => s switch { Circle => 1, Square => 2, Tri => 3, null => 0 };
    static int S3(Shape s)   => s switch { Circle => 1, Square => 2, Tri => 3, Shape => 4 };
    static int N1(string? s) => s switch { "a" => 1, string => 2 };
    static int N2(string s)  => s switch { "a" => 1, string => 2 };
    static int N3(int? x)    => x switch { int v => v };
    static int T1(bool a, bool b) => (a, b) switch { (true, true) => 1, (true, false) => 2, (false, _) => 3 };
    static int T2(bool a, bool b) => (a, b) switch { (true, true) => 1, (true, false) => 2, (false, false) => 3 };
    static int L1(int[] a)   => a switch { [] => 0, [_] => 1, [_, _, ..] => 2 };
    static int L2(int[] a)   => a switch { [] => 0, [_] => 1 };
    static void Main() { }
}
```

- `-nullable:enable` 로 컴파일하면 **어느 줄**에 완전성 진단이 붙는가 — 경고인가 에러인가?
- ★★★ `Y1`(`byte`)과 `I3`(`int`)은 둘 다 두 범위만 적었다 — 결과가 같은가?
- ★★★ `S1` — `abstract Shape` 의 `sealed` 파생 셋을 **다 적었다.** 진단이 붙는가?
- ★★ `D1` 은 `< 0` 과 `>= 0` 을 적었다 — 무엇이 남는가?
- ★★ `-nullable:disable` 로 바꾸면 어느 칸이 달라지는가?

### 2. ★★ 두 팔만 적은 `int` 식을 실행하면 (예측)

```csharp
// cs22b-il.cs
using System;
public static class Probe {
    public static int Full(bool b) => b switch { true => 1, false => 0 };
    public static int Part(int x)  => x switch { 1 => 10, 2 => 20 };
}
class Program {
    static void Main() {
        Console.WriteLine($"[1] Part(2) = {Probe.Part(2)}");
        try { Console.WriteLine($"[2] Part(3) = {Probe.Part(3)}"); }
        catch (Exception e) { Console.WriteLine($"[2] {e.GetType().Name} : {e.Message.Replace(Environment.NewLine, " / ")}"); }
        Il.Dump(typeof(Probe), "Full");
        Il.Dump(typeof(Probe), "Part");
    }
}
```

- `[1]`·`[2]` 에 무엇이 찍히는가?
- ★★★ `Full` 과 `Part` 의 IL 에서 **한쪽에만 있는 호출**은 무엇인가 — 소스에 그 코드가 있는가?
- ★ 그 호출 앞의 `box` 는 왜 필요한가?

### 3. ★★ `break` 가 빠진 `switch` 문 (예측)

```csharp
// cs22b-fall.cs
class Program {
    static string F(int x) {
        string r = "";
        switch (x) {
            case 1:
                r += "one ";
            case 2:
                r += "two ";
                break;
            default:
                r += "other ";
        }
        return r;
    }
    static void Main() { }
}
```

- 컴파일되는가? 진단이 붙는다면 **어느 줄 · 어느 코드**인가?
- ★★ C·Java 에서라면 `F(1)` 은 무엇을 돌려줬을까 — C# 은?

### 4. ★★ `goto case` 와 빈 레이블 (예측)

```csharp
// cs22b-goto.cs
using System;
class Program {
    static string F(int x) {
        string r = "";
        switch (x) {
            case 0:                               // 빈 case — 다음 레이블과 한 구역
            case 1:
                r += "one ";
                goto case 2;
            case 2:
                r += "two ";
                break;
            default:
                r += "other ";
                goto case 1;
        }
        return r;
    }
    static void Main() {
        foreach (var x in new[] { 0, 1, 2, 7 }) Console.WriteLine($"F({x}) = {F(x)}");
    }
}
```

- `F(0)`·`F(1)`·`F(2)`·`F(7)` 은 각각?
- ★ `case 0:` 에는 본문이 없다 — 3번의 진단이 왜 안 나는가?

### 5. ★★ 팔 순서를 바꿔 적으면 (예측)

```csharp
// cs22b-unreach.cs
class Program {
    static string E(object o) => o switch { object => "obj", string => "str" };
    static string R(int x)    => x switch { > 0 => "pos", 5 => "five", _ => "etc" };
    static string G(int x)    => x switch { > 0 when x % 2 == 0 => "even", 5 => "five", _ => "etc" };
    static string S(object o) {
        switch (o) {
            case object: return "obj";
            case string: return "str";
        }
    }
    static void Main() { }
}
```

- 어느 줄에 어떤 진단이 붙는가 — 경고인가 에러인가?
- ★★★ `R` 과 `G` 는 둘 다 `5` 를 `> 0` 뒤에 뒀다 — 결과가 같은가?
- ★★ `S` 에는 도달 불가 말고 진단이 하나 더 붙는다 — 왜인가?

### 6. ★★ 일부만 다룬 `switch` 문 (예측)

```csharp
// cs22b-stmt.cs
using System;
abstract class Shape { }
sealed class Circle : Shape { }
sealed class Square : Shape { }
class Program {
    static string F(Shape s) {
        string r = "초기값";
        switch (s) {
            case Circle: r = "원"; break;
        }
        return r;
    }
    static void Main() {
        Console.WriteLine($"[1] {F(new Circle())}");
        Console.WriteLine($"[2] {F(new Square())}");
    }
}
```

- `-warn:9` 로 컴파일하면 진단이 몇 줄인가?
- `[1]`·`[2]` 에 무엇이 찍히는가?

### 7. ★★★ 타입 계층의 완전성과 C# 15 의 `closed` (왜)

- 1번 `S1` 의 예시 패턴 `'_'` 는 무엇을 뜻하는가 — `sealed` 는 무엇을 막고 무엇을 안 막나?
- ★★ `S2`(null 팔 추가)의 예시가 `'not null'` 로 바뀌는 이유는? `S3` 은 왜 조용한가?
- ★★★ Learn 이 말하는 **C# 15 의 `closed`** 를 이 판의 컴파일러에 던지면 무엇이 나오나 — 어떻게 해야 돌았고, 돌았을 때 `Some` 의 예시 패턴은?

### 8. ★★★ Java `sealed` 의 `switch` 식과 (경계)

- Java 21 에서 `sealed interface … permits` 의 `switch` 식에 case 하나를 빼면? `default` 없이 다 적으면?
- ★★ Kotlin `when`·Rust `match` 에서 누락은 무엇인가 — 각 갈래 어디서 쟀나?
- ★★ C# 에서 그것을 에러로 만들려면 무엇을 해야 하는가?

### 9. ★★ Learn 이 적은 목록 패턴의 완전성 (경계)

- Learn 은 「목록 패턴은 완전성 경고를 안 낸다」고 적었다. 1번 `L2` 는?
- ★ 그렇다면 어느 쪽을 근거로 적어야 하는가?

### 10. ★★ `switch` 식과 `switch` 문을 고르는 기준 (왜)

- 각각 **무엇을 막아 주고 무엇을 안 막나**(흘러내림 · 완전성 · 안 맞으면)?
- ★ 부작용을 고르는 분기에 `switch` 식을 억지로 쓰면 무엇이 불편한가?

### 11. 다른 주제와 잇기 (연결)

- ★★★ `enum` 에서 **이름을 다 적어도** 경고가 나는 자리는 몇 번 주제에서 쟀나 — 그 코드는?
- ★★ 5번 `S` 의 `CS0161` 은 **몇 번 주제의 어떤 사실**에서 나오나?
- ★ `CS8655` 가 `-nullable` 에 달린 이유의 정본은?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
