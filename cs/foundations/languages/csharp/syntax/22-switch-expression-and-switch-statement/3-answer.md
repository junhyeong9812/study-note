# csharp/syntax/22 — `switch` 식과 `switch` 문 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·진단·IL 은 **.NET SDK 10.0.401** · 런타임 **10.0.12** · 타겟 **`net10.0`** ·
> **linux-x64** 에서 실제로 돌려 얻은 것이다(2026-09-26). 대비는 **javac 21.0.5** 다.\
> 진단은 **`-preferreduilang:en-US`** 로 영어로 고정했다.\
> ★ 블록은 캡처 스크립트가 파일로 받아 조립기가 끼워 넣은 것이다 — 손으로 옮긴 줄은 없다.\
> ★ 진단을 싣는 블록은 전부 **그 진단을 낸 소스를 같은 블록 안에** 다시 싣는다(`===== 소스: … =====`).
> **읽는 법** — **진단 문구, 특히 「For example」 뒤의 예시 패턴**은 흔들리는 칸이다.\
> 근거로 쓰는 것은 **진단 코드와 `(행,열)` · `cc exit` · 「완전성 진단이 붙은 칸 N / M」 · 옵코드** 다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ **11 / 18** 칸이 **경고** — `byte` 는 조용, `int` 는 `-1` 이 남고, `sealed` 파생 셋에도 **`CS8509`**

**출력**

```text
===== 소스: cs22b-grid.cs =====
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
===== csc -nullable:enable -out:ex.dll cs22b-grid.cs 2>&1 | sort -t'(' -k2n (cc exit=0) =====
cs22b-grid.cs(7,35): warning CS8509: The switch expression does not handle all possible values of its input type (it is not exhaustive). For example, the pattern 'false' is not covered.
cs22b-grid.cs(9,35): warning CS8509: The switch expression does not handle all possible values of its input type (it is not exhaustive). For example, the pattern '0' is not covered.
cs22b-grid.cs(10,35): warning CS8509: The switch expression does not handle all possible values of its input type (it is not exhaustive). For example, the pattern '-1' is not covered.
cs22b-grid.cs(12,35): warning CS8509: The switch expression does not handle all possible values of its input type (it is not exhaustive). For example, the pattern 'double.NaN' is not covered.
cs22b-grid.cs(13,35): warning CS8509: The switch expression does not handle all possible values of its input type (it is not exhaustive). For example, the pattern ''\0'' is not covered.
cs22b-grid.cs(14,35): warning CS8509: The switch expression does not handle all possible values of its input type (it is not exhaustive). For example, the pattern '_' is not covered.
cs22b-grid.cs(15,35): warning CS8509: The switch expression does not handle all possible values of its input type (it is not exhaustive). For example, the pattern 'not null' is not covered.
cs22b-grid.cs(17,35): warning CS8655: The switch expression does not handle some null inputs (it is not exhaustive). For example, the pattern '_' is not covered.
cs22b-grid.cs(19,35): warning CS8655: The switch expression does not handle some null inputs (it is not exhaustive). For example, the pattern 'null' is not covered.
cs22b-grid.cs(21,45): warning CS8509: The switch expression does not handle all possible values of its input type (it is not exhaustive). For example, the pattern '(false, true)' is not covered.
cs22b-grid.cs(23,35): warning CS8509: The switch expression does not handle all possible values of its input type (it is not exhaustive). For example, the pattern '{ Length: 2 }' is not covered.
===== csc -nullable:disable -out:ex.dll cs22b-grid.cs 2>&1 | sort -t'(' -k2n (cc exit=0) =====
cs22b-grid.cs(7,35): warning CS8509: The switch expression does not handle all possible values of its input type (it is not exhaustive). For example, the pattern 'false' is not covered.
cs22b-grid.cs(9,35): warning CS8509: The switch expression does not handle all possible values of its input type (it is not exhaustive). For example, the pattern '0' is not covered.
cs22b-grid.cs(10,35): warning CS8509: The switch expression does not handle all possible values of its input type (it is not exhaustive). For example, the pattern '-1' is not covered.
cs22b-grid.cs(12,35): warning CS8509: The switch expression does not handle all possible values of its input type (it is not exhaustive). For example, the pattern 'double.NaN' is not covered.
cs22b-grid.cs(13,35): warning CS8509: The switch expression does not handle all possible values of its input type (it is not exhaustive). For example, the pattern ''\0'' is not covered.
cs22b-grid.cs(14,35): warning CS8509: The switch expression does not handle all possible values of its input type (it is not exhaustive). For example, the pattern '_' is not covered.
cs22b-grid.cs(15,35): warning CS8509: The switch expression does not handle all possible values of its input type (it is not exhaustive). For example, the pattern 'not null' is not covered.
cs22b-grid.cs(17,25): warning CS8632: The annotation for nullable reference types should only be used in code within a '#nullable' annotations context.
cs22b-grid.cs(21,45): warning CS8509: The switch expression does not handle all possible values of its input type (it is not exhaustive). For example, the pattern '(false, true)' is not covered.
cs22b-grid.cs(23,35): warning CS8509: The switch expression does not handle all possible values of its input type (it is not exhaustive). For example, the pattern '{ Length: 2 }' is not covered.
===== 칸 세기 — -nullable:enable (CS8509·CS8655 가 붙은 줄) =====
완전성 진단이 붙은 칸 11 / 18
===== 칸 세기 — -nullable:disable (CS8509·CS8655 가 붙은 줄) =====
완전성 진단이 붙은 칸 9 / 18
```

**왜 그런가**

- ★★★ **`enable` — 줄 7·9·10·12·13·14·15·17·19·21·23**, 전부 **경고**(`cc exit=0`). 조용한 칸은 6·8·11·16·18·20·22.
- ★★★ **`Y1` 은 조용, `I3` 은 `CS8509`(예시 `'-1'`)** — `byte` 는 0\~255 라 두 범위로 끝나고, `int` 는 **음수가 남는다.** 컴파일러가 범위를 실제로 계산한다.
- ★★★ **`S1` 에 `CS8509`(예시 `'_'`)** — 계층이 **열려 있다**(7번).
- ★★ **`D1` 은 `double.NaN`** 이 남는다 — NaN 은 어느 비교도 거짓이다.
- ★★ **`disable` 에서 9 / 18** — **줄 17(`string?`)·19(`int?`)의 `CS8655` 가 사라진다.** 줄 17 에는 `?` 표기에 대한 `CS8632` 만 남는다(완전성 진단이 아니라 스크립트가 안 셌다).

### 2. ★★ **`[1]` `20` · `[2]` `SwitchExpressionException`** — `Part` 에만 **`ThrowSwitchExpressionException`**

**출력**

```text
===== 소스: cs22b-il.cs =====
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
===== csc -r:il.dll -out:ex.dll cs22b-il.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
cs22b-il.cs(4,41): warning CS8509: The switch expression does not handle all possible values of its input type (it is not exhaustive). For example, the pattern '0' is not covered.
[1] Part(2) = 20
[2] SwitchExpressionException : Non-exhaustive switch expression failed to match its input. / Unmatched value was 3.
--- Probe.Full ---
  .locals [0] System.Int32
  IL_0000: ldarg.0
  IL_0001: brtrue.s IL_0005
  IL_0003: br.s IL_0009
  IL_0005: ldc.i4.1
  IL_0006: stloc.0
  IL_0007: br.s IL_000d
  IL_0009: ldc.i4.0
  IL_000a: stloc.0
  IL_000b: br.s IL_000d
  IL_000d: ldloc.0
  IL_000e: ret
--- Probe.Part ---
  .locals [0] System.Int32
  IL_0000: ldarg.0
  IL_0001: ldc.i4.1
  IL_0002: beq.s IL_000c
  IL_0004: br.s IL_0006
  IL_0006: ldarg.0
  IL_0007: ldc.i4.2
  IL_0008: beq.s IL_0011
  IL_000a: br.s IL_0016
  IL_000c: ldc.i4.s 10
  IL_000e: stloc.0
  IL_000f: br.s IL_0022
  IL_0011: ldc.i4.s 20
  IL_0013: stloc.0
  IL_0014: br.s IL_0022
  IL_0016: ldarg.0
  IL_0017: box System.Int32
  IL_001c: call <PrivateImplementationDetails>::ThrowSwitchExpressionException
  IL_0021: nop
  IL_0022: ldloc.0
  IL_0023: ret
```

**왜 그런가**

- ★★★ **`Part` 의 IL 에만 `call <PrivateImplementationDetails>::ThrowSwitchExpressionException`** 가 있다 — 소스에 없는 **보이지 않는 `_ => throw` 팔**을 컴파일러가 끼웠다. `Full`(`bool` 두 팔)에는 없다.
- ★ **`box System.Int32`** — 예외에 **안 맞은 값**(`Unmatched value was 3.`)을 싣기 위해서다. 던질 때만 돈다.
- ★ 경고 `CS8509` 는 빌드를 막지 않았다(`cc exit=0`).

### 3. ★★ **컴파일 안 된다** — **`CS0163`**(줄 5) · **`CS8070`**(줄 10)

**출력**

```text
===== 소스: cs22b-fall.cs =====
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
===== csc -out:ex.dll cs22b-fall.cs 2>&1 | sort (cc exit=1) =====
cs22b-fall.cs(10,13): error CS8070: Control cannot fall out of switch from final case label ('default:')
cs22b-fall.cs(5,13): error CS0163: Control cannot fall through from one case label ('case 1:') to another
```

**왜 그런가**

- ★★★ **`CS0163`** — `case 1:` 구역이 `break` 없이 `case 2:` 로 **흘러 내려가려** 했다. C·Java 라면 `F(1)` 은 `one two ` 였을 것이다 — **C# 은 에러**다.
- ★★ **`CS8070`** — 마지막 `default:` 도 **끝에서 빠져나가면 에러**. 마지막 구역도 `break` 가 필요하다.

### 4. ★★ **`one two` · `one two` · `two` · `other one two`**

**출력**

```text
===== 소스: cs22b-goto.cs =====
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
===== csc -out:ex.dll cs22b-goto.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
F(0) = one two 
F(1) = one two 
F(2) = two 
F(7) = other one two 
```

**왜 그런가**

- ★★★ **`goto case 2;` 로 적어서 흘러간다** — `F(7)` 은 `default` → `goto case 1` → `goto case 2` 사슬.
- ★ **`case 0:` 은 본문이 없어 `case 1:` 과 한 구역**이다 — 흘러내림 금지는 **본문 있는 구역**에만 걸린다.

### 5. ★★ **`CS8510` 둘 · `CS8120` · `CS0161`** — 전부 **에러**, `G` 는 **통과**

**출력**

```text
===== 소스: cs22b-unreach.cs =====
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
===== csc -out:ex.dll cs22b-unreach.cs 2>&1 | sort (cc exit=1) =====
cs22b-unreach.cs(2,62): error CS8510: The pattern is unreachable. It has already been handled by a previous arm of the switch expression or it is impossible to match.
cs22b-unreach.cs(3,59): error CS8510: The pattern is unreachable. It has already been handled by a previous arm of the switch expression or it is impossible to match.
cs22b-unreach.cs(5,19): error CS0161: 'Program.S(object)': not all code paths return a value
cs22b-unreach.cs(8,18): error CS8120: The switch case is unreachable. It has already been handled by a previous case or it is impossible to match.
```

**왜 그런가**

- ★★★ **줄 2 `string` 은 `object` 에 가려져 `CS8510`** · **줄 3 `5` 는 `> 0` 에 가려져 `CS8510`** — 범위 포함 관계를 계산한다.
- ★★★ **`G` 의 `5` 는 진단 없음** — 앞 팔에 **`when` 가드**가 있어 아무것도 「다 받았다」고 치지 않는다.
- ★★ **`S` 의 `case string` 은 `CS8120`**(문의 도달 불가) · **`CS0161`** — `case object:` 는 **null 에 안 맞아**([21번](../21-pattern-matching-type-property-relational-list/) (1)) null 이면 `switch` 를 빠져나가 **값을 돌려주지 않는 경로**가 생긴다.

### 6. ★★ **진단 0줄** · `[1]` `원` · `[2]` `초기값`

**출력**

```text
===== 소스: cs22b-stmt.cs =====
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
===== csc -warn:9 -out:ex.dll cs22b-stmt.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
[1] 원
[2] 초기값
```

**왜 그런가**

- ★★★ **`switch` 문은 완전성을 안 본다** — `-warn:9` 로도 조용하다. 안 맞은 `Square` 는 **아무 일 없이 지나간다**(Learn — 「제어가 빠져나간다」).
- ★ [20번](../20-enum-and-flags/) 탐침 6 이 `enum` 에서 같은 것을 봤다.

### 7. ★★★ `'_'` 는 **「이 컴파일 단위가 모르는 파생」** — `closed` 는 미리보기 + 특성 직접 정의로만 돌았다

**출력**

```text
===== 소스: cs22b-closed0.cs =====
closed class Shape { }
class Program { static void Main() { } }
===== csc -out:ex.dll cs22b-closed0.cs 2>&1 | sort (cc exit=1) =====
cs22b-closed0.cs(1,14): error CS0656: Missing compiler required member 'System.Runtime.CompilerServices.IsClosedTypeAttribute..ctor'
cs22b-closed0.cs(1,14): error CS8652: The feature 'closed classes' is currently in Preview and *unsupported*. To use Preview features, use the 'preview' language version.
===== csc -langversion:preview -out:ex.dll cs22b-closed0.cs 2>&1 | sort (cc exit=1) =====
cs22b-closed0.cs(1,14): error CS0656: Missing compiler required member 'System.Runtime.CompilerServices.IsClosedTypeAttribute..ctor'
===== 소스: cs22b-closed.cs =====
using System;
namespace System.Runtime.CompilerServices { sealed class IsClosedTypeAttribute : Attribute { } }   // .NET 10 BCL 에 없어 직접 둔다
closed class Shape { }
sealed class Circle : Shape { }
sealed class Square : Shape { }
class Program {
    static int All(Shape s)  => s switch { Circle => 1, Square => 2 };
    static int Some(Shape s) => s switch { Circle => 1 };
    static void Main() {
        Console.WriteLine($"[1] All(new Square()) = {All(new Square())}");
        Console.WriteLine($"[2] typeof(Shape).IsAbstract = {typeof(Shape).IsAbstract}");
    }
}
===== csc -langversion:preview -out:ex.dll cs22b-closed.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
cs22b-closed.cs(8,35): warning CS8509: The switch expression does not handle all possible values of its input type (it is not exhaustive). For example, the pattern 'Square' is not covered.
[1] All(new Square()) = 2
[2] typeof(Shape).IsAbstract = True
```

**왜 그런가**

- ★★★ **`sealed` 는 「그 클래스의 파생」을 막을 뿐 `Shape` 의 새 파생을 막지 않는다** — 다른 어셈블리가 `Pentagon : Shape` 를 만들 수 있어, 컴파일러는 `_` 를 요구한다.
- ★★ **`S2` 의 `'not null'`** — null 은 덮였고 **null 아닌 모르는 파생**이 남았다는 뜻. **`S3` 은 `Shape =>` 팔**이 그 자리를 받아 조용하다.
- ★★★ **기본 판: `CS8652`(미리보기·미지원) + `CS0656`(특성 없음)** · **`-langversion:preview`: `CS0656`** — Roslyn 은 기능을 알지만 **.NET 10 BCL 에 `IsClosedTypeAttribute` 가 없다.**\
  **특성을 직접 정의하니 돌았다** — `All` 조용, **`Some` 은 `CS8509` 에 예시 `'Square'`**(빠진 파생의 **이름**). `IsAbstract` 는 `True`.
- ★ 이것은 **흉내 낸 판의 실험**이다 — 쓸 수 있는 기능이라는 뜻이 아니다.

### 8. ★★★ Java 는 **에러**(`javac exit=1`), 다 적으면 `default` 없이 **통과**

**출력**

```text
===== 소스: Ex22.java =====
sealed interface Shape permits Circle, Square { }
record Circle(double r) implements Shape { }
record Square(double a) implements Shape { }
public class Ex22 {
    static String name(Shape s) {
        return switch (s) {
            case Circle c -> "원";
            case Square q -> "정사각형";
        };
    }
    public static void main(String[] a) { System.out.println(name(new Square(2))); }
}
===== javac -d j22out j22/Ex22.java && java -cp j22out Ex22 (cc exit=0 · run exit=0) =====
정사각형
===== 소스: Ex22b.java =====
sealed interface Shape permits Circle, Square { }
record Circle(double r) implements Shape { }
record Square(double a) implements Shape { }
public class Ex22b {
    static String name(Shape s) {
        return switch (s) {
            case Circle c -> "원";
        };
    }
}
===== javac -d j22bout j22b/Ex22b.java (cc exit=1) =====
j22b/Ex22b.java:6: error: the switch expression does not cover all possible input values
        return switch (s) {
               ^
1 error
```

**왜 그런가**

- ★★★ **`the switch expression does not cover all possible input values`**(`cc exit=1`) — `permits` 가 **닫힌 목록**이라 Java 는 누락을 **에러**로 막고, 다 적으면 `default` 가 필요 없다.
- ★★ **Kotlin `when` — 에러**(`'when' expression must be exhaustive`, [Kotlin 23번](../../../kotlin/syntax/23-sealed-classes-and-when-exhaustiveness/)) · **Rust `match` — `E0004` 에러**([Rust 18번](../../../rust/syntax/18-match-and-exhaustiveness/)). 이 판에서 둘은 안 던졌다.
- ★★ C# 에서는 **경고를 에러로 올리는 설정**(`-warnaserror:CS8509` 류)이 필요하다 — **이 판에서 그 플래그를 던지지는 않았다.**

### 9. ★★ **`L2` 에 `CS8509`**(예시 `{ Length: 2 }`) — **실측을 근거로** 적는다

- ★★ Learn 의 「목록 패턴은 경고를 안 낸다」와 **이 판의 Roslyn 이 다르다.** 1번 격자 줄 23 이 그 블록이다.
- ★ 문서는 **「무엇이 옳은가」** 를, 실행은 **「지금 무엇이 되나」** 를 말한다 — 이 문서는 **실측 + 「Learn 과 다름」** 을 함께 적었다.

### 10. ★★ **식**은 완전성을 경고하고 안 맞으면 예외 · **문**은 흘러내림만 막고 안 맞으면 지나간다

| | 흘러내림 | 완전성 | 안 맞으면 |
|---|---|---|---|
| `switch` 식 | (구역이 없다) | ★★★ `CS8509`/`CS8655` **경고** | ★★★ `SwitchExpressionException` |
| `switch` 문 | ★★★ `CS0163` **에러** — `goto case` | ★★★ **안 본다** | ★★ 그냥 지나간다 |

- ★ 부작용을 `switch` 식으로 고르면 **팔마다 값을 돌려줘야** 해 억지 값이나 람다 호출이 끼어든다 — 그때는 문이 맞다.

### 11. 잇기

- ★★★ **`enum` 의 `CS8524`**(이름을 다 적어도 경고) · `CS8509` — [20번](../20-enum-and-flags/) (4).
- ★★ **「타입 패턴은 null 에 안 맞는다」** — [21번](../21-pattern-matching-type-property-relational-list/) (1).
- ★ **`CS8655` 와 nullable 문맥** — [06번](../06-nullable-reference-types/).

## 실행 검증

| 무엇 | 몇 번·어디서 | 결과 |
|---|---|---|
| `cs22b-grid.cs` 완전성 격자 | csc 2회(`-nullable:enable`/`disable`) + 칸 세기 2회 | ★★★ **11 / 18** · **9 / 18** · 전부 경고 |
| `cs22b-il.cs` 실패 팔 IL | csc 1회 · 실행 1회 | ★★★ 불완전한 식에만 `ThrowSwitchExpressionException` |
| `cs22b-fall.cs` 흘러내림 | csc 1회 | ★★★ `CS0163` · `CS8070` |
| `cs22b-goto.cs` | csc 1회 · 실행 1회 | `goto case` 사슬 · 빈 레이블 |
| `cs22b-unreach.cs` 도달 불가 | csc 1회 | ★★★ `CS8510`×2 · `CS8120` · `CS0161` · 가드 팔은 통과 |
| `cs22b-stmt.cs` 문의 완전성 | csc 1회(`-warn:9`) · 실행 1회 | ★★★ 진단 0줄 · `초기값` |
| `cs22b-closed0.cs` · `cs22b-closed.cs` | csc 3회(기본·preview×2) · 실행 1회 | ★★★ `CS8652`+`CS0656` · 특성 직접 정의로 동작 |
| `Ex22.java` · `Ex22b.java` | javac 2회 · java 1회 | ★★★ 다 적으면 통과 · 빼면 **에러** |
| `cs22b-form.cs` 형태 | csc 1회 · 실행 1회 | `A` · `ArgumentOutOfRangeException` · `3.14` · `낮음` |

**구현 의존 항목** — 다음은 **이 판(.NET SDK 10.0.401 · 런타임 10.0.12 · javac 21.0.5)에서만** 그렇다.

- ★★★ **완전성 누락이 경고인 것** · **예시 패턴** · **목록 패턴에도 경고가 나는 것**(Learn 과 다름).
- ★★★ **`closed` 의 동작 전부** — 미리보기이고, 특성을 흉내 냈다.

**언어가 보장하는 것**(구현이 바뀌어도 같다)

- **`switch` 문의 흘러내림 금지** · **팔은 글 순서 · 가려진 팔은 에러** · **불완전한 식은 안 맞으면 예외**.

**안 돌려 본 것 / 못 잰 것 / 잴 것이 없는 것**

- **안 돌려 본 것** — ★★ **`-warnaserror:CS8509`** · ★ **`closed` 의 다른 어셈블리 규칙** · ★ **`switch` 문의 점프 표 IL** · ★ **Kotlin·Rust 를 이 판에서 직접**.
- **못 잰 것** — 없다.
- **잴 것이 없는 것** — ★ **④ 할당 바이트** — 완전성은 컴파일 시점의 판정이다.

**버전이 올랐을 때 다시 돌려야 하는 것**

- ★★★ **7번** — C# 15 가 정식이 되고 BCL 에 `IsClosedTypeAttribute` 가 들어오면 **기본 판에서 조용해질** 수 있다. 그때 1번 격자 줄 14 도 `closed` 로 다시 던져라.
- ★★ **1번 격자** — 예시 패턴·목록 패턴 경고는 Roslyn 판에 달렸다. **칸 수를 다시 세라.**
- ★ **3·4·5번** — 명세가 정한 것이라 바뀔 일이 없다.
