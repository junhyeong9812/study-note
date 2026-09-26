# csharp/syntax/22 — `switch` 식과 `switch` 문 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [ECMA-334 7판(2023-12)](https://ecma-international.org/publications-and-standards/standards/ecma-334/) ·
> [Learn — `switch` 식](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/operators/switch-expression)(열어서 확인: 「팔은 **글 순서대로** 평가된다」 · 「아래 팔이 위 팔에 **다 가려지면 컴파일러가 에러**」 ·\
> 「어느 팔도 안 맞으면 런타임이 예외를 던진다 — .NET Core 3.0 이후 **`SwitchExpressionException`**」 · 「**대부분의 경우** 모든 입력을 다루지 않으면 경고」 · 「**목록 패턴은 경고를 안 낸다**」) ·\
> [Learn — 선택문](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/statements/selection-statements)(열어서 확인: 「**한 구역에서 다음 구역으로 흘러 내려갈 수 없다**」 · 「흉내 내려면 `goto`」 ·\
> 「레이블 여럿을 한 구역에 달 수 있다」 · 「어느 case 도 안 맞고 `default` 가 없으면 **제어가 `switch` 문을 빠져나간다**」) ·\
> [Learn — 패턴 · Closed hierarchy patterns](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/operators/patterns)(열어서 확인: 「**C# 15 부터** `closed` 클래스를 받는 `switch` 식은 **직접 파생을 다 다루면 완전하다**」)
> **실행 검증** — 이 문서의 모든 출력·진단·IL 은 아래 「이 판」의 도구로 **실제로 돌려 얻은 것**이다(2026-09-26).\
> ★ 블록은 캡처 스크립트가 파일로 받아 조립기가 끼워 넣은 것이다 — 사람이 옮겨 적은 줄은 하나도 없다.\
> ★★★ **진단 언어를 영어로 고정했다**(`DOTNET_CLI_UI_LANGUAGE=en` + `-preferreduilang:en-US`). **대비는 실측이다** — **javac 21.0.5** 로 `sealed` 인터페이스의 `switch` 를 던졌다((3)).
> **버전** — `switch` 문 **C# 1.0**(패턴 `case` 는 **C# 7**) · **`switch` 식 C# 8** · 관계·`and`/`or` 팔 **C# 9** · 목록 팔 **C# 11** · ★★ **`closed` 클래스는 C# 15 미리보기**((3) — 이 판에서는 `-langversion:preview` + 특성 직접 정의로만 돌았다).
> **경계** — ★★★ **`enum` 에서의 완전성**(`CS8509`·`CS8524` · 이름을 다 적어도 경고 · 실행하면 `SwitchExpressionException` · `switch` 문은 완전성을 안 본다)은 [20번](../20-enum-and-flags/) (4)(7)이 **이미 쟀다** — 여기서는 **인용만** 하고 **`enum` 밖**(`bool`·정수 범위·`double`·타입 계층·`null`·튜플·목록)으로 간다.\
> ★ **패턴 하나가 IL 로 무엇이 되나**는 [21번](../21-pattern-matching-type-property-relational-list/)이 정본이다. 여기는 **팔 여럿의 집합** — 완전성과 도달 불가.
> ★★★ **대비** — Java 갈래 목록([`java/syntax/README.md`](../../../java/syntax/README.md))의 **21번**([`21-switch-statement-and-expression/`](../../../java/syntax/21-switch-statement-and-expression/))·**15번**([`15-sealed-classes/`](../../../java/syntax/15-sealed-classes/)) ·\
> Kotlin 갈래 목록([`kotlin/syntax/README.md`](../../../kotlin/syntax/README.md))의 **23번**([`23-sealed-classes-and-when-exhaustiveness/`](../../../kotlin/syntax/23-sealed-classes-and-when-exhaustiveness/)) ·\
> Rust 갈래 목록([`rust/syntax/README.md`](../../../rust/syntax/README.md))의 **18번**([`18-match-and-exhaustiveness/`](../../../rust/syntax/18-match-and-exhaustiveness/)) — ★ Kotlin·Rust 는 **각 갈래의 실측을 인용**한다(이 판에서 던지지 않았다).
>
> ★★ **흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | 진단 **문구** — 특히 「For example, the pattern '…'」 속의 **예시 패턴**(컴파일러가 하나를 골라 보여 준다) | ★★★ **진단 코드**(`CS8509`·`CS8655`·`CS8510`·`CS8120`·`CS0163`·`CS8070`·`CS0161`·`CS8652`·`CS0656`)와 **`(행,열)`** |
> | **IL 오프셋 폭** | ★★★ **옵코드와 부른 멤버**(`box` · `ThrowSwitchExpressionException`) — **완전하면 그 팔이 없다는 것** |
> | ★ 미리보기 기능의 **동작 전부**((3) `closed`) — 판이 오르면 바뀔 수 있다 | ★★★ **「완전성 진단이 붙은 칸 N / M」**(스크립트가 센 마지막 줄) · `cc exit` |

## 이 판

```text
===== dotnet --version && dotnet --list-runtimes | grep NETCore (exit=0) =====
10.0.401
Microsoft.NETCore.App 10.0.12 [/home/jun/.local/opt/dotnet/shared/Microsoft.NETCore.App]
===== javac -version (exit=0) =====
javac 21.0.5
```

## 이 갈래가 쓰는 세 층

| 층 | 뜻 | 이 주제에서 근거로 쓰는 것 |
|---|---|---|
| **언어 명세(ECMA-334)** | C# 언어가 약속한 것 | ★★★ **`switch` 문의 흘러내림 금지**(`CS0163`) · 팔은 **글 순서** · 가려진 팔은 **에러** · 안 맞으면 **예외** · ★ **닫힌 계층이 없다**(C# 14 까지) |
| **컴파일러(Roslyn)** | 완전성을 **어떻게 판정하고 무엇을 경고하나** | ★★★ **완전성 누락이 경고**(`CS8509`·`CS8655`)인 것 · 예시 패턴을 고르는 것 · **안 맞는 팔을 IL 로 끼워 넣는 것** |
| **이 판의 관찰** | .NET 10.0.12 · linux-x64 · javac 21.0.5 | 격자의 칸 수 · 진단 문구 · 미리보기 `closed` 의 동작 |

★★★ **이 주제에서 가장 중요한 칸 — 완전성 누락은 C# 에서 「경고」다.**\
Java `switch` 식((3))·Kotlin `when`·Rust `match` 는 **에러**다. C# 이 경고인 까닭은 [20번](../20-enum-and-flags/)이 보인 **「이름 없는 enum 값」** 과 이 문서 (3)의 **「닫힌 계층이 없다」** 에 있다 — **컴파일러가 「이것이 전부」라고 말할 근거가 늘 부족하다.**

## 한눈에 — 쉽게 말하면

**`switch` 식은 「빠짐없이 다뤘나」를 컴파일러가 세어 주는 분기이고, `switch` 문은 「구역마다 반드시 나가라」만 지키는 분기다.**

우편물 분류대를 생각하자.

- **`switch` 식** — 칸마다 **우편번호 범위**가 적힌 분류대. 직원(컴파일러)이 **「이 번호는 어느 칸에도 안 들어간다」** 를 **미리 짚어** 준다(경고). 그래도 빌드는 된다 — 실제로 그런 편지가 오면 **바닥에 떨어뜨리고 경보를 울린다**(`SwitchExpressionException`).
- **`switch` 문** — 칸마다 **작업 지시서**. 직원은 빠진 번호를 **안 센다.** 대신 **한 칸의 작업을 끝내고 옆 칸으로 흘러가는 것**은 절대 못 하게 한다(`CS0163`). 옆 칸으로 가려면 **「2번 칸으로 가라」** 고 써야 한다(`goto case 2`).
- **닫힌 계층이 없다** — 「원·정사각형·삼각형」 칸을 다 만들어도, **내일 누가 「오각형」을 새로 만들 수 있다**(다른 어셈블리에서 파생). 그래서 직원은 **「그 밖(`_`)」 칸**을 요구한다.
- **위 칸이 아래 칸을 가린다** — 「모든 편지」 칸이 맨 위에 있으면 아래 「등기」 칸은 **영원히 빈다** — 이것은 **경고가 아니라 에러**다(`CS8510`).

| 비유 | 실체 | 어디서 보나 |
|---|---|---|
| 빠진 번호를 미리 짚는다 | ★★★ **완전성 진단이 붙은 칸 11 / 18**(`-nullable:enable`) — 전부 **경고** | (1) |
| 바닥에 떨어뜨리고 경보 | ★★★ **불완전한 식에만** IL 에 **`box` + `ThrowSwitchExpressionException`** 팔이 끼워진다 | (2) |
| 내일 오각형이 생길 수 있다 | ★★★ **`abstract` + `sealed` 파생 셋을 다 적어도 `CS8509`**(예시 `'_'`) | (3) |
| 옆 칸으로 흘러가지 마라 | ★★★ **`CS0163`**(흘러내림) · **`CS8070`**(마지막 구역에서 빠져나감) | (4) |
| 위 칸이 가린다 | ★★★ **`CS8510`**(식) · **`CS8120`**(문) — **에러** | (5) |

★★★ **이 주제의 본체 그림 — 완전성은 「값 공간을 덮었나」다.**

```text
   입력 타입의 값 공간                          팔이 덮은 것                       남은 것 → 진단
   ────────────────────────────                ──────────────────────           ──────────────────────
   bool      { false, true }                   true                              false        → CS8509
   int       (-∞ … +∞)                         < 0 , > 0                         0            → CS8509
   int                                         >= 0 and < 10 , >= 10             음수(-1)     → CS8509
   byte      { 0 … 255 }                       <= 127 , >= 128                   (없음)       → 조용
   double    실수 + NaN                         < 0 , >= 0                        NaN          → CS8509
   Shape     Circle·Square·Tri + ★「미래의 파생」  Circle , Square , Tri             _            → CS8509
   string?   문자열 + null                      "a" , string                      null         → CS8655 (nullable 켜야)
   (bool,bool) 네 칸                            (T,T) (T,F) (F,F)                 (F,T)        → CS8509

   ★★★ 남은 것이 비면 조용하다. 컴파일러가 「남은 것」 을 하나 골라 예시로 보여 준다.
   ★★★ Shape 줄만 다르다 — 남은 것이 「이 컴파일 단위가 모르는 타입」 이다.
```

## 이 주제가 답하려는 질문

1. **`enum` 밖에서 완전성은 어떻게 판정되나** — `bool`·정수·`double`·타입 계층·`null`·튜플·목록((1)).
2. **불완전하면 무엇이 일어나나** — 컴파일 때와 실행 때((2)).
3. **왜 C# 은 타입 계층을 다 적어도 경고하나** — 닫힌 계층 · Java `sealed` 와((3)).
4. **`switch` 문은 무엇을 막고 무엇을 안 막나** — 흘러내림 · `goto case` · 완전성((4)).
5. **팔 순서가 틀리면** — 도달 불가 팔((5)).

## 동작 방식

### (0) 이 주제가 쓰는 창

★★★ **본체 창은 ② 진단 격자다** — 「완전한가」는 **컴파일러가 대답하는 질문**이라 진단의 유무로만 답이 나온다.

| 창 | 무엇을 보여 주나 | 이 주제에서 |
|---|---|---|
| ★★★ **② 진단 격자** | ★★★ **완전성 격자 18칸 × `-nullable` 두 벌** — 스크립트가 **「진단이 붙은 칸 N / M」** 을 센다 · `CS0163`·`CS8070`·`CS8510`·`CS8120` | (1)(3)(4)(5) |
| ★★ **① IL 덤프** | ★★ **불완전한 식에만 끼워지는 `ThrowSwitchExpressionException` 팔** — 완전한 `bool` 식에는 없다 | (2) |
| ★ **③ 리플렉션** | ★ 미리보기 `closed` 클래스가 **`IsAbstract=True`** 가 되고 **`IsClosedTypeAttribute`** 를 다는 것 | (3) |
| ④ **할당 바이트** | ★ **부적용** — 이 주제의 질문은 **컴파일 시점의 판정**이다. 실패 팔의 `box` 는 **던질 때만** 돈다. 재지 않은 게 아니라 **물을 것이 없다**(18-B) | — |

- ★★ **[20번](../20-enum-and-flags/)이 이미 잰 것** — `enum` 에서 **이름 하나를 빠뜨리면 `CS8509`, 이름을 다 적어도 `CS8524`**(이름 없는 값), **둘 다 경고**, 실행하면 **`SwitchExpressionException`**, **`switch` 문은 완전성을 안 본다**(그 문서의 탐침 6). 이 문서는 그것을 **다시 재지 않는다.**

### (1) ★★★ 완전성 격자 — `enum` 밖 18칸

**언제 쓰나** — 「`switch` 식에 `_` 를 꼭 달아야 하나」를 **타입마다** 답할 때.

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

- ★★★ **`-nullable:enable` 에서 11 / 18, `disable` 에서 9 / 18** — 스크립트가 **`CS8509`·`CS8655` 가 붙은 줄**만 셌다(`CS8632` 같은 다른 경고는 안 센다).
- ★★★ **값 공간을 다 덮으면 조용하다** — `bool` 두 칸(줄 6) · `int` 의 `< 0`/`0`/`> 0`(줄 8) · **`byte` 의 `<= 127`/`>= 128`(줄 11)** · 튜플 네 칸(줄 20) · 목록 `[]`/`[_]`/`[_, _, ..]`(줄 22).\
  ★★ **컴파일러가 정수 범위를 실제로 계산한다** — `byte` 는 0\~255 라 두 범위로 끝나고, `int` 는 `>= 0` 만으로는 **음수가 남는다**(줄 10 예시 `'-1'`).
- ★★★ **`double` 은 `< 0`/`>= 0` 으로 안 끝난다**(줄 12 예시 `'double.NaN'`) — NaN 은 **어느 비교도 거짓**이다.
- ★★ **`char` 범위 하나**(줄 13) 예시가 `'\0'` — 컴파일러는 **빠진 값 중 하나**를 보여 준다. 어느 것을 고르는지는 흔들리는 칸이다.
- ★★★ **줄 23 — 목록 패턴 `[]`/`[_]` 만 적으면 `CS8509`(예시 `{ Length: 2 }`)** — ★★ **Learn 의 「목록 패턴은 경고를 안 낸다」와 다르다**(이 판 실측). 문서보다 컴파일러가 최신이다.
- ★★★ **`null` 칸은 `-nullable` 에 달렸다** — `string?`(줄 17)·`int?`(줄 19)가 **`enable` 에서만 `CS8655`**. `disable` 에서는 null 이 **안 세어진다**(줄 17 에는 `?` 표기에 대한 `CS8632` 만 남는다).\
  ★ 줄 18(`string`, `?` 없음)은 **둘 다 조용** — 널 불가 타입이라 null 을 요구하지 않는다([06번](../06-nullable-reference-types/)의 「분석이지 런타임 타입이 아니다」와 같은 자리 — **실행 때 null 이 오면 예외다**).

| 줄 | 입력 · 팔 | `enable` | `disable` | 예시 패턴 |
|---|---|---|---|---|
| 6 | `bool` · `true`·`false` | 조용 | 조용 | — |
| 7 | `bool` · `true` | `CS8509` | `CS8509` | `false` |
| 8 | `int` · `< 0`·`0`·`> 0` | 조용 | 조용 | — |
| 9 | `int` · `< 0`·`> 0` | `CS8509` | `CS8509` | `0` |
| 10 | `int` · `>= 0 and < 10`·`>= 10` | `CS8509` | `CS8509` | `-1` |
| 11 | `byte` · `<= 127`·`>= 128` | 조용 | 조용 | — |
| 12 | `double` · `< 0`·`>= 0` | `CS8509` | `CS8509` | `double.NaN` |
| 13 | `char` · `'a'`\~`'z'` | `CS8509` | `CS8509` | `'\0'` |
| 14 | `Shape` · 파생 셋 | ★★★ `CS8509` | `CS8509` | `_` |
| 15 | `Shape` · 파생 셋 + `null` | ★★★ `CS8509` | `CS8509` | `not null` |
| 16 | `Shape` · 파생 셋 + `Shape` | 조용 | 조용 | — |
| 17 | `string?` · `"a"`·`string` | `CS8655` | (`CS8632` 만) | `_` |
| 18 | `string` · `"a"`·`string` | 조용 | 조용 | — |
| 19 | `int?` · `int v` | `CS8655` | 조용 | `null` |
| 20 | `(bool, bool)` · 세 팔로 네 칸 | 조용 | 조용 | — |
| 21 | `(bool, bool)` · `(F,T)` 빠짐 | `CS8509` | `CS8509` | `(false, true)` |
| 22 | `int[]` · `[]`·`[_]`·`[_, _, ..]` | 조용 | 조용 | — |
| 23 | `int[]` · `[]`·`[_]` | ★★ `CS8509` | `CS8509` | `{ Length: 2 }` |

### (2) ★★ 불완전하면 — IL 에 실패 팔이 끼워진다

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

- ★★★ **`Full`(`bool` 두 팔)의 IL 에는 예외 경로가 없다** — `brtrue` 로 가르고 끝난다.
- ★★★ **`Part`(`1`·`2` 만)에는 `ldarg.0` · `box System.Int32` · `call <PrivateImplementationDetails>::ThrowSwitchExpressionException`** 가 **끼워져 있다** — 소스에 없는 **보이지 않는 `_ => throw` 팔**이다.
- ★★ **예외 메시지에 안 맞은 값이 실린다**(`Unmatched value was 3.`) — 그래서 값을 **`box`** 한다. **던질 때만** 도는 경로라 평소 할당은 없다(④ 부적용).
- ★ 경고 `CS8509`(예시 `'0'`)는 **빌드를 막지 않았다**(`cc exit=0`).

```text
   x switch { 1 => 10, 2 => 20 }                       컴파일러가 끼운 것
   ─────────────────────────────                       ─────────────────────────────────────
   x == 1 ? → 10                                        (그대로)
   x == 2 ? → 20                                        (그대로)
   (아무것도 안 적음)                                     box x → ThrowSwitchExpressionException(x)

   ★★★ 경고를 무시해도 「조용히 기본값」 이 되지는 않는다 — 반드시 예외다.
```

> **어느 층인가** — ★★★ **「안 맞으면 예외」는 언어(334)** 다. 예외 타입이 `SwitchExpressionException` 인 것은 **.NET Core 3.0 이후 런타임**(Learn — .NET Framework 는 `InvalidOperationException`).\
> ★ `<PrivateImplementationDetails>` 도우미로 던지는 모양은 **Roslyn** 이다.

### (3) ★★★ 닫힌 계층이 없다 — `abstract` + `sealed` 파생 셋을 다 적어도 `CS8509`

**언제 쓰나** — 「도형 종류를 다 적었는데 왜 `_` 를 달라고 하나」.

- ★★★ **격자 줄 14 — `abstract class Shape` 와 `sealed` 파생 셋을 다 적어도 `CS8509`**(예시 `'_'`).\
  **`sealed` 는 「파생의 파생」을 막을 뿐, `Shape` 의 새 파생을 막지 않는다.** 다른 어셈블리가 내일 `Pentagon : Shape` 를 만들 수 있다 — 컴파일러는 **이 컴파일 단위가 모든 파생을 안다고 가정하지 않는다.**
- ★★ **줄 15 — `null` 팔까지 달면 예시가 `'not null'`** 로 바뀐다 — 「null 은 덮였고, null 아닌 **모르는 파생**이 남았다」는 뜻이다.
- ★★ **줄 16 — 기반 타입 팔 `Shape => 4` 를 달면 조용하다.** `_` 대신 **「그 밖의 `Shape`」** 를 적는 것이다(null 은 여전히 안 맞는다 — 매개변수가 **널 불가 `Shape`** 라 null 을 요구받지 않을 뿐이다).

**그런데 C# 15 에 `closed` 가 온다** — Learn 은 「**C# 15 부터** `closed` 클래스는 직접 파생을 다 다루면 완전하다」고 적었다. 이 판의 컴파일러에게 던졌다.

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

- ★★★ **기본(`-langversion:latest` = C# 14)에서는 `CS8652`** — 「`'closed classes'` 는 **미리보기이고 지원되지 않는다**」 + **`CS0656`**(필요한 특성 `IsClosedTypeAttribute` 가 없다).
- ★★★ **`-langversion:preview` 로도 `CS0656`** — **Roslyn(SDK 10.0.401)은 기능을 아는데 .NET 10 BCL 에 특성이 없다.**
- ★★★ **특성을 직접 정의하면 돌았다** — `All`(파생 둘을 다 적음)은 **진단 없음**, `Some`(하나 빠짐)은 **`CS8509`(예시 `'Square'`)** — **예시가 `'_'` 가 아니라 빠진 파생의 이름이다.**
- ★★ **리플렉션 — `typeof(Shape).IsAbstract` 가 `True`** — Learn 의 「`closed` 는 **암시적으로 `abstract`**」 그대로다.
- ★★★ **결론 — 「C# 에는 닫힌 계층이 없다」는 C# 14 까지 참이고, 이 판에서는 미리보기로만 열린다.** 특성을 흉내 내 돌린 것은 **실험**이지 쓸 수 있는 기능이 아니다(판이 오르면 동작이 바뀔 수 있다 — 흔들리는 칸).

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

- ★★★ **Java 21 — `sealed interface Shape permits Circle, Square` 에 두 `case` 만 적으면 `default` 없이 컴파일되고 돈다.** `permits` 가 **닫힌 목록**이라서다.
- ★★★ **하나를 빼면 `error: the switch expression does not cover all possible input values`** — **에러**다(`cc exit=1`). C# 의 `CS8509` 는 **경고**(`cc exit=0`).
- ★ Kotlin `when` 도 `sealed` 에 대해 **에러**(`'when' expression must be exhaustive`, [Kotlin 23번](../../../kotlin/syntax/23-sealed-classes-and-when-exhaustiveness/) 실측) · Rust `match` 도 **에러**(`E0004`, [Rust 18번](../../../rust/syntax/18-match-and-exhaustiveness/) 실측) — **이 판에서 둘은 안 던졌다.**

```text
                   계층이 닫혀 있나              하나를 빠뜨리면                  다 적으면
   C# 14           ✕ (abstract 는 열려 있다)      CS8509 경고 · cc exit=0         CS8509 '_' 경고
   C# 15 미리보기    closed (이 판: 특성 직접 정의)   CS8509 경고 'Square'           ★ 조용
   Java 21         sealed … permits             ★ 에러 · javac exit=1           ★ 조용 · default 불필요
   Kotlin          sealed class                 ★ 에러(Kotlin 23번)              조용
   Rust            enum                         ★ E0004 에러(Rust 18번)          조용

   ★★★ C# 만 「빠뜨림」 이 경고다 — 그리고 C# 14 까지는 「다 적음」 도 경고다.
```

### (4) ★★★ `switch` 문 — 흘러내림 금지 · `goto case` · 완전성은 안 본다

**언제 쓰나** — 값이 아니라 **문장(부작용)** 을 고를 때 · C·Java 의 `switch` 습관을 가져왔을 때.

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

- ★★★ **`case 1:` 이 `break` 없이 `case 2:` 로 가려 하면 `CS0163`** — 「한 case 레이블에서 다른 레이블로 **흘러 내려갈 수 없다**」. C·Java 의 흘러내림이 **C# 에서는 에러**다.
- ★★★ **마지막 `default:` 도 끝에서 빠져나가면 `CS8070`** — 「마지막 case 레이블에서 `switch` 밖으로 **흘러 나갈 수 없다**」. **마지막 구역도 `break` 가 필요하다.**

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

- ★★★ **흘러내림이 필요하면 `goto case 2;`** 로 **적어서** 간다 — `F(1)` 이 `one two`, `F(7)` 이 `other one two`(`default` → `case 1` → `case 2`).
- ★★ **빈 레이블은 쌓을 수 있다** — `case 0:` 과 `case 1:` 은 **한 구역**이라 `F(0)` 도 `one two`. **본문이 있는 구역만** 반드시 끝나야 한다.

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

- ★★★ **`switch` 문은 완전성을 안 본다** — `Circle` 만 다뤘는데 **`-warn:9` 로도 진단 0줄**(`cc exit=0`), `Square` 는 **초기값 그대로** 지나간다. Learn — 「안 맞고 `default` 가 없으면 **제어가 빠져나간다**」.\
  ★ [20번](../20-enum-and-flags/) 탐침 6(`enum`)과 **같은 결론이 타입 계층에서도** 나왔다.

```text
                     흘러내림                  완전성                         안 맞으면
   switch 문(C#)      ✕ CS0163 · goto case     ✕ 안 본다(진단 0줄)              ★ 그냥 지나간다
   switch 식(C#)      (구역이 없다)              ★ CS8509/CS8655 경고             ★ SwitchExpressionException
   switch 문(C·Java)  ○ 기본 동작               (C 는 안 본다 · Java 는 21번 참조) 그냥 지나간다

   ★★★ C# switch 문이 막는 것은 「조용한 흘러내림」 하나다. 빠진 case 는 막지 않는다.
```

### (5) ★★ 팔 순서 — 가려진 팔은 에러

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

- ★★★ **`object => …` 뒤의 `string => …` 는 `CS8510`**(식) — 앞 팔이 **이미 다 받았다.** 경고가 아니라 **에러**다.
- ★★★ **`> 0` 뒤의 `5` 도 `CS8510`** — 컴파일러가 **범위의 포함 관계를 계산**한다.
- ★★ **`> 0 when x % 2 == 0` 뒤의 `5` 는 통과**(줄 4 에 진단 없음) — **`when` 가드가 붙은 팔은 아무것도 「다 받았다」고 치지 않는다.** 가드는 컴파일러가 못 푼다.
- ★★ **`switch` 문에서는 `CS8120`**(「case 가 도달 불가」) — 코드만 다르고 같은 판정이다.
- ★★ **그리고 `S` 는 `CS0161`**(모든 경로가 값을 돌려주지 않는다) — **`case object:` 는 null 에 안 맞으므로** null 이 들어오면 `switch` 를 빠져나간다. [21번](../21-pattern-matching-type-property-relational-list/) (1)의 「타입 패턴은 null 에 안 맞는다」가 여기서 **흐름 분석**으로 나타났다.

> **어느 층인가** — ★★★ **「가려진 팔은 에러」는 언어**(Learn — 「컴파일러가 에러를 낸다」). ★★ **「완전성 누락은 경고」는 Roslyn 의 선택**이다 — 명세는 불완전한 `switch` 식을 **허용하고 런타임 예외로** 정의한다.

## 문법 — 형태와 규칙

### 형태

```text
===== 소스: cs22b-form.cs =====
using System;

Console.WriteLine(Grade(95));
try { Grade(-3); } catch (ArgumentOutOfRangeException e) { Console.WriteLine(e.GetType().Name); }
Console.WriteLine(Area(new Circle(1)));
Log(2);

static string Grade(int score) => score switch {
    < 0 or > 100 => throw new ArgumentOutOfRangeException(nameof(score)),
    >= 90        => "A",
    >= 70        => "B",
    _            => "C",
};

static double Area(Shape s) => s switch {
    Circle c => Math.Round(Math.PI * c.R * c.R, 2),
    Square q => q.A * q.A,
    _        => throw new ArgumentException("모르는 도형", nameof(s)),   // 닫힌 계층이 없으니 막는다
};

static void Log(int level) {
    switch (level) {
        case 1:
        case 2:                                   // 빈 case 는 쌓을 수 있다
            Console.WriteLine("낮음");
            break;
        default:
            Console.WriteLine("높음");
            break;
    }
}

abstract record Shape;
sealed record Circle(double R) : Shape;
sealed record Square(double A) : Shape;
===== csc -out:ex.dll cs22b-form.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
A
ArgumentOutOfRangeException
3.14
낮음
```

- ★★★ **범위는 관계 패턴으로, 위에서부터 좁혀 간다** — `< 0 or > 100` 을 먼저 던지고 `>= 90` → `>= 70` → `_`.
- ★★★ **타입 계층의 `switch` 식에는 `_ => throw`** — C# 14 에는 닫힌 계층이 없다((3)). **`_` 는 「모르는 파생」을 받는 자리**다.
- ★★ **`switch` 문의 빈 레이블 쌓기**(`case 1: case 2:`)는 되고, **본문 있는 구역의 흘러내림**은 `CS0163` 이다((4)).
- ★ **`switch` 식은 값이 필요할 때, `switch` 문은 문장(부작용)을 고를 때.**

### 금지 사례 — 진단이 나는 꼴

| 쓴 꼴 | 진단 코드 | 어디서 |
|---|---|---|
| `switch` 식이 값 공간을 다 덮지 않음 | `CS8509`(**경고**) | (1) |
| nullable 켠 채 null 을 안 다룸 | `CS8655`(**경고**) | (1) |
| 앞 팔이 뒤 팔을 다 가림(식) | `CS8510`(에러) | (5) |
| 앞 case 가 뒤 case 를 다 가림(문) | `CS8120`(에러) | (5) |
| 본문 있는 구역에서 다음 구역으로 흘러내림 | `CS0163`(에러) | (4) |
| 마지막 구역에서 빠져나감 | `CS8070`(에러) | (4) |
| `closed` 를 기본 판에서 | `CS8652` + `CS0656`(에러) | (3) |
| ★★★ `abstract` + `sealed` 파생을 다 적은 식 | ★★★ **`CS8509`** — 닫힌 계층이 없다 | (3) |
| ★★★ 일부만 다룬 `switch` **문** | ★★★ **진단 없음** | (4) |

## 어디서 틀리나

1. ★★★ **「`sealed` 파생을 다 적었으니 완전하다」** — **C# 14 에서는 `CS8509`**((3)). 계층이 열려 있다. Java `sealed`·Kotlin `sealed` 와 다르다.
2. ★★★ **「경고를 무시하면 기본값이 나온다」** — **`SwitchExpressionException`** 이다((2)). 컴파일러가 던지는 팔을 끼워 넣는다.
3. ★★★ **「`switch` 문도 빠진 case 를 경고한다」** — **진단 0줄**이다((4)). 빠진 값은 조용히 지나간다.
4. ★★★ **「C# `switch` 문은 C 처럼 흘러내린다」** — **`CS0163`**. `goto case` 로 적어야 한다((4)).
5. ★★ **「`>= 0` 과 `< 0` 이면 `double` 은 끝이다」** — **NaN** 이 남는다((1)).
6. ★★ **「nullable 을 꺼도 null 은 검사된다」** — **`CS8655` 는 `enable` 에서만**((1)). 꺼 두면 null 이 **런타임 예외로** 새어 나온다.
7. ★★ **「목록 패턴은 완전성 경고가 없다」**(Learn) — **이 판은 `CS8509` 를 냈다**((1) 줄 23).
8. ★★ **「`when` 가드 팔도 뒤를 가린다」** — **가드 팔은 가리지 않는다**((5)).
9. ★ **「마지막 `default:` 는 `break` 가 없어도 된다」** — **`CS8070`**((4)).

## 구현 세부사항 대 언어 보장

| 무엇 | 층 | 근거 |
|---|---|---|
| **`switch` 문의 흘러내림 금지** | ★★★ **언어 보장(334)** | (4) `CS0163`·`CS8070` |
| **팔은 글 순서 · 가려진 팔은 에러** | ★★★ **언어 보장** · Learn | (5) |
| **불완전한 `switch` 식은 안 맞으면 예외** | ★★★ **언어 보장** | (2) |
| **예외 타입이 `SwitchExpressionException`** | ★★ **런타임(.NET Core 3.0+)** · Learn | (2) |
| **완전성 누락이 에러가 아니라 경고** | ★★ **Roslyn** | (1) |
| **예시 패턴을 무엇으로 고르나** | ★ **Roslyn 구현** | (1) |
| **목록 패턴에도 완전성 경고** | ★ **Roslyn 구현**(Learn 과 다름) | (1) 줄 23 |
| **null 완전성이 nullable 문맥에 달린 것** | ★★ **컴파일러 분석**([06번](../06-nullable-reference-types/)) | (1) 줄 17·19 |
| **닫힌 계층(`closed`)** | ★★ **C# 15 미리보기** — 이 판에서는 BCL 특성이 없다 | (3) |

## 언제 쓰고 언제 안 쓰나

- ★★★ **값을 고르면 `switch` 식** — 완전성 경고가 붙고, 빠진 자리가 **예외로** 드러난다.
- ★★★ **타입 계층의 `switch` 식에는 `_ => throw new …`** — 모르는 파생이 **조용히 새지 않게**((3)). C# 15 의 `closed` 가 정식이 되면 **다시 판단**하라.
- ★★ **`CS8509` 를 경고로 두지 말고 에러로 올리는 것**을 고려하라 — `-warnaserror:CS8509`(★ **이 판에서 이 플래그를 던지지는 않았다**). Java·Kotlin·Rust 가 에러로 하는 일을 C# 은 **설정으로** 한다.
- ★★ **`switch` 문은 부작용을 고를 때만** — 완전성을 안 봐 주니 **`default:` 를 직접** 달아라.
- ★ **nullable 을 켜라** — 안 켜면 null 칸이 격자에서 사라진다((1)).

## 핵심 문장

1. ★★★ **C# `switch` 식의 완전성 누락은 경고다** — 격자 18칸 중 11칸(`enable`)이 **전부 경고**였고 빌드는 됐다((1)).
2. ★★★ **불완전한 식에는 컴파일러가 `ThrowSwitchExpressionException` 팔을 끼운다** — 조용한 기본값은 없다((2)).
3. ★★★ **C# 14 에는 닫힌 계층이 없다** — `sealed` 파생을 다 적어도 `CS8509`. Java `sealed` 는 에러까지 가고, C# 15 `closed` 는 이 판에서 미리보기다((3)).
4. ★★★ **`switch` 문은 흘러내림을 막고(`CS0163`) 완전성은 안 본다** — 흘러가려면 `goto case`((4)).
5. ★★ **가려진 팔은 에러(`CS8510`·`CS8120`)** — 단 `when` 가드 팔은 아무것도 가리지 않는다((5)).

## 관련 자료

- [20번 — `enum` 과 `[Flags]`](../20-enum-and-flags/) (4)(7) — ★★★ **`enum` 에서의 완전성**(`CS8509`·`CS8524`)이 먼저 쟀다. **경계**: 이름 없는 enum 값은 거기, **enum 밖**은 여기.
- [21번 — 패턴 매칭](../21-pattern-matching-type-property-relational-list/) — 팔 하나(패턴)의 IL · null 에 안 맞는 것.
- [06번 — 널 허용 참조 타입](../06-nullable-reference-types/) — `CS8655` 가 `-nullable` 에 달린 이유.
- [16번 — 상속·`sealed`](../16-inheritance-virtual-override-abstract-sealed-new/) (7) — **`sealed` 가 막는 것은 파생의 파생**이다.
- Java 갈래 목록([`java/syntax/README.md`](../../../java/syntax/README.md))의 **21번**([`21-switch-statement-and-expression/`](../../../java/syntax/21-switch-statement-and-expression/))·**15번**([`15-sealed-classes/`](../../../java/syntax/15-sealed-classes/)) — **경계**: Java 의 흘러내림·`yield`·`permits` 는 거기.
- Kotlin 갈래 목록([`kotlin/syntax/README.md`](../../../kotlin/syntax/README.md))의 **23번**([`23-sealed-classes-and-when-exhaustiveness/`](../../../kotlin/syntax/23-sealed-classes-and-when-exhaustiveness/)) — `when` 완전성은 **에러**.
- Rust 갈래 목록([`rust/syntax/README.md`](../../../rust/syntax/README.md))의 **18번**([`18-match-and-exhaustiveness/`](../../../rust/syntax/18-match-and-exhaustiveness/)) — `match` 완전성은 **`E0004` 에러**.

## 용어 풀이

- **`switch` 식(switch expression)** — `x switch { 패턴 => 값, … }`. **값을 돌려주는 식**. C# 8.
- **`switch` 문(switch statement)** — `switch (x) { case …: 문장; break; }`. **구역(section)** 을 고르는 문장.
- **완전성(exhaustiveness)** — 팔들이 입력 타입의 **모든 값**을 덮었나. C# 에서는 누락이 **경고**다.
- **흘러내림(fall-through)** — 한 구역 끝에서 다음 구역으로 이어 실행되는 것. C# 에서는 에러(`CS0163`).
- **도달 불가 팔** — 앞 팔이 이미 다 받아 **절대 안 골라지는** 팔. 에러(`CS8510`·`CS8120`).
- **닫힌 계층(closed hierarchy)** — 「파생이 이것이 전부」라고 선언된 타입 계층. Java `sealed … permits` · Kotlin `sealed` · **C# 15 `closed`(미리보기)**.
- **`when` 가드** — 패턴 뒤의 추가 조건. 컴파일러가 풀지 못해 **완전성·도달 불가 판정에서 빠진다.**

## 더 들어가면

- ★ **`-warnaserror:CS8509`·`.editorconfig` 로 경고를 에러로** — **이 판에서 안 던졌다.**
- ★ **`closed` 의 다른 어셈블리 규칙** — Learn 은 「직접 파생이 `internal` 이면 다른 어셈블리의 `switch` 는 완전하지 않다」고 적었다. **이 판에서 안 던졌다**(미리보기 · 특성을 흉내 낸 판이라 판이 오르면 다시).
- ★ **`switch` 문의 IL(점프 표 `switch` 옵코드)** — 조밀한 정수 case 는 `switch` 옵코드로, 성긴 case 는 비교 사슬로 풀린다고 알려져 있으나 **이 판에서 찍지 않았다.**
