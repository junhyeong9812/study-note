# csharp/syntax/12 — 클래스·필드·생성자·`this`/`base` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [ECMA-334 7판(2023-12)](https://ecma-international.org/publications-and-standards/standards/ecma-334/) ·
> [Learn — 생성자](https://learn.microsoft.com/en-us/dotnet/csharp/programming-guide/classes-and-structs/constructors) ·
> [Learn — 기본 생성자(primary constructor)](https://learn.microsoft.com/en-us/dotnet/csharp/whats-new/tutorials/primary-constructors) ·
> [Learn — `required` 한정자](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/keywords/required) ·
> [Learn — `readonly`](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/keywords/readonly) ·
> [.NET API — `RuntimeHelpers.GetUninitializedObject`](https://learn.microsoft.com/en-us/dotnet/api/system.runtime.compilerservices.runtimehelpers.getuninitializedobject)
> **실행 검증** — 이 문서의 모든 출력·진단·IL 은 아래 「이 판」의 도구로 **실제로 돌려 얻은 것**이다(2026-09-25).\
> ★ 블록은 캡처 스크립트가 파일로 받아 조립기가 끼워 넣은 것이다 — 사람이 옮겨 적은 줄은 하나도 없다.\
> ★ 소스 펜스의 배너도 **캡처가 찍은 것**이다. 원고에 손으로 쓴 배너는 없다.\
> ★★★ **진단 언어를 영어로 고정했다**(`DOTNET_CLI_UI_LANGUAGE=en` + `-preferreduilang:en-US`).\
> **던진 형태** — MSBuild 를 안 쓰고 Roslyn `csc` 를 직접 부른다(설정은 [11번](../11-collection-initializers-and-collection-expressions/) 머리말과 같다).\
> **`-debug` 를 안 줬다** — 그래서 (4)의 스택 트레이스에 **절대 경로도 줄 번호도 안 박힌다.**
> **버전** — 클래스·필드·생성자·`this`/`base` 는 **C# 1.0부터**. **`init` 은 C# 9**, **`required` 는 C# 11**,\
> **기본 생성자(primary constructor)가 클래스에까지 온 것은 C# 12부터**다. `-langversion:latest` 로 던졌다.
> **경계** — **상속과 `virtual`/`override` 의 설계 판**은 목록의 **16번**, **속성(property)의 전모**는 **13번**,\
> **접근 한정자**는 **15번**, **`record`** 는 **18번**, **`IDisposable`/`using`** 은 **37번 주제**가 정본이다.\
> 여기서는 「**객체가 만들어질 때 무엇이 어떤 순서로 도는가**」만 센다.\
> ★ **클래스라는 개념 자체**는 [`oop-basics/`](../../../../oop-basics/)가 정본이고, 여기는 **C# 문법**이다.
> ★★★ **대비** — C++ 갈래 목록([`cpp/syntax/README.md`](../../../cpp/syntax/README.md))의 **13번**([`13-constructors-member-init-list-and-delegating/`](../../../cpp/syntax/13-constructors-member-init-list-and-delegating/))이 **직접 대비**다.\
> (1)에서 **초기화 순서를 두 언어에서 나란히 찍어** 대비표를 만들고, (4)에서 **생성자 속 가상 호출**을 다시 나란히 놓는다.\
> ★ **결정적 파괴 쪽 대비**는 C++ 갈래의 **14번**([`14-destructors-and-deterministic-destruction/`](../../../cpp/syntax/14-destructors-and-deterministic-destruction/))과 [01번](../01-value-types-and-reference-types/)이 맡는다.
>
> ★★ **흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | 객체 주소 · `GetHashCode()` · 실행 시간 | ★★★ **로그가 찍힌 순서와 번호** — 이 주제의 답 자체다 |
> | 진단 문구가 판마다 다듬일 수 있다는 것 | ★★ **진단 코드**(`CS7036`·`CS0768`·`CS9035`·`CS0191`·`CS0649`)와 **`(행,열)`** |
> | 컴파일러가 만든 **숨은 필드 이름의 형식**이 바뀔 수 있다는 것 | ★★★ **숨은 필드가 있다는 사실과 그 개수**(`<Auto>k__BackingField` 류) |
> | — | ★★ **`cc exit` 와 `run exit`**(갈라 적었다) · **예외 타입과 스택 프레임 이름** |

## 이 판

```text
===== 명령: dotnet --version && dotnet --list-runtimes | grep NETCore && g++ --version | head -1 (exit=0) =====
10.0.401
Microsoft.NETCore.App 10.0.12 [/home/jun/.local/opt/dotnet/shared/Microsoft.NETCore.App]
g++ (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0
```

## 이 갈래가 쓰는 세 층

| 층 | 뜻 | 이 주제에서 근거로 쓰는 것 |
|---|---|---|
| **언어 명세(ECMA-334)** | C# 언어가 약속한 것 | ★★★ **초기화 순서**((1)) · `base()` 가 암묵인 것 · `this()` 연쇄 규칙 · `required`·`readonly` 검사 |
| **런타임·BCL 구현** | CoreCLR·Roslyn 이 그렇게 하는 것 | ★★ **숨은 필드 이름**(`<name>P`·`<Auto>k__BackingField`) · IL · `GetUninitializedObject` 가 생성자를 건너뛰는 것 |
| **이 판의 관찰** | .NET 10.0.12 · linux-x64 에서 이번에 본 것 | 진단 문구 · 스택 트레이스의 프레임 이름 · `run exit=134` |

★★★ **이 주제는 첫 칸이 가장 두껍다** — [11번](../11-collection-initializers-and-collection-expressions/)과 정반대다.\
**초기화 순서는 명세가 정해 둔 것**이고, 그래서 대비표(1)가 「구현이 그렇다」가 아니라 **「언어가 그렇게 정했다」가 된다**.

## 한눈에 — 쉽게 말하면

**C# 의 생성은 「아래층부터 짓는데, 내 짐은 먼저 들여놓는다」이다.**

집을 짓는다고 하자.\
**기초 → 1층 → 2층** 순으로 짓는 것은 당연하다. C++ 도 C# 도 같다.

그런데 C# 에는 이상한 규칙이 하나 있다 —\
**2층에 놓을 가구를 기초 공사보다 먼저 들여놓는다.**\
`public int Tag = 1;` 같은 **필드 초기자**가 그렇다. **기반 클래스보다도 먼저** 돈다.

| 비유 | 실체 | C++ 와 같나 |
|---|---|---|
| 기초부터 짓는다 | **기반 생성자가 파생보다 먼저 돈다** | ★ **같다** |
| ★★★ **2층 가구를 기초보다 먼저 들인다** | ★★★ **파생의 필드 초기자가 기반보다 먼저 돈다** | ★★★ **정반대다**((1)) |
| 같은 설계도를 두 번 안 쓴다 | **`this()` 위임 — 필드 초기자는 한 번만** | 같다 |
| 기초 공사를 안 적어도 한다 | **`base()` 는 암묵**이다 | 같다 |
| ★★ **기초 공사 중에 2층 사람을 부르면** | ★★ **생성자에서 가상 메서드를 부르면 파생 것이 불린다** | ★★★ **C++ 은 기반 것이 불린다**((4)) |

> **필드 초기자(field initializer)** — 필드 선언에 붙인 초기값.\
> 예: `public int Tag = 1;` — ★ **생성자 본문보다 먼저**, 그리고 **기반 클래스보다도 먼저** 돈다((1)).

> **기본 생성자(primary constructor)** — 클래스 이름 뒤 괄호로 받는 매개변수(C# 12).\
> 예: `class Savings(string id) : Account(id) { … }`

```text
   C++ (13번)                              C#  (여기 (1))

   1. 기반의 멤버 초기자                     1. ★ 파생의 필드 초기자
   2. 기반의 생성자 본문                     2. 기반의 필드 초기자
   3. ★ 파생의 멤버 초기자                   3. 기반의 생성자 본문
   4. 파생의 생성자 본문                     4. 파생의 생성자 본문

   ^^^^^^^^^^^^^^^^^^^^^^^^                ^^^^^^^^^^^^^^^^^^^^^^^^
   파생 멤버는 기반이 다 끝난 뒤            파생 필드가 제일 먼저
```

- ★★★ **1번과 3번 자리가 맞바뀐다.** 이것이 이 배치의 대비 전부이고, (1)에서 **두 언어를 같은 프로그램 모양으로 찍어** 증명한다.
- ★★★ **그 차이가 (4)에서 결과로 나온다** — 생성자에서 가상 메서드를 부르면\
  **C# 은 파생 필드 초기자가 이미 끝나 있고**, **C++ 은 파생 함수가 아예 안 불린다.**

## 이 주제가 답하려는 질문

1. **객체 하나가 만들어질 때 무엇이 몇 번, 어떤 순서로 도나** — **C++ 와 어디가 반대인가**((1)).
2. **`this()` 로 위임하면 필드 초기자가 몇 번 도나**((2)), **`base()` 를 안 적으면 어떻게 되나**((3)).
3. **생성자에서 가상 메서드를 부르면 무엇을 보게 되나** — **값으로**((4)).
4. **컴파일러가 무엇을 막아 주고 무엇을 안 막아 주나**((7)(8)(9)).

## 동작 방식

### (0) 이 주제가 쓰는 창

| 창 | 무엇을 보여 주나 | 이 주제에서 |
|---|---|---|
| ★★★ **실행 출력** | ★★★ **무엇이 몇 번, 어떤 순서로 돌았나** — 이 주제의 축 | (1)·(2)·(4)·(6)·(7) |
| ★★ **컴파일 진단** | 기본 생성자가 사라진 것 · `this()` 재귀 · `required`·`readonly` | (3)·(8) |
| ★★ **예외 전문** | ★★★ **생성자에서 가상 메서드를 부르면 실제로 터지는 자리** | (4) |
| **IL** | 기본 생성자가 만든 숨은 필드 · `Greet()` 가 무엇을 읽나 | (6) |
| ★ **할당 바이트** | ★★ **부적용** — 아래 | — |

- ★★★ **중심 창은 실행 출력이다.** 초기화 순서는 **논쟁거리가 아니라 로그**다 —\
  (1)이 **번호를 매겨 전수로 찍고**, 같은 모양의 C++ 프로그램을 옆에 둔다.
- ★★★ **네 번째 창은 예외 전문이다.** (4)의 「생성자에서 가상 메서드」는 **값만 찍으면 「좀 이상하네」에서 끝난다** —\
  **실제로 `NullReferenceException` 을 터뜨려** 스택 프레임(`at Child.Describe()` → `at Parent..ctor()`)을 보여야\
  **「누가 누구를 불렀나」가 증명된다.**
- ★★ **「부적용인 창」 — 할당 바이트.** [03번](../03-boxing-and-unboxing/)·[11번](../11-collection-initializers-and-collection-expressions/)이 중심으로 쓴 그 창이 여기엔 **잴 것이 없다.**\
  필드 초기자를 쓰든 생성자 본문에서 대입하든 **같은 객체 하나**가 만들어진다 — **순서만 다르고 크기도 개수도 같다.**\
  ★ **기본 생성자(C# 12)도 마찬가지다** — (6)에서 **필드 하나짜리 클래스**가 되는 것을 리플렉션으로 확인했고,\
  손으로 쓴 판과 **필드 개수가 같다.** **「재 봤더니 같았다」가 아니라 「잴 것이 없다」다.**

### (1) ★★★ 초기화 순서 전수 — 그리고 C++ 와의 대비표

**언제 쓰나** — 상속이 있는 클래스를 만들 때마다. **이 절이 이 주제의 중심이다.**

```text
===== 소스: cs12b-order.cs =====
using System;

Console.WriteLine("new Derived() 를 부른다");
var d = new Derived();
Console.WriteLine($"끝 — Tag={d.Tag}  BaseTag={d.BaseTag}");

static class Log { public static int Seq; public static int Step(string w) { Console.WriteLine($"  {++Seq}. {w}"); return Seq; } }

class Base {
    public int BaseTag = Log.Step("Base 의 필드 초기자");
    public Base() { Log.Step("Base 의 생성자 본문"); }
}
class Derived : Base {
    public int Tag = Log.Step("Derived 의 필드 초기자");
    public Derived() : base() { Log.Step("Derived 의 생성자 본문"); }
}
===== csc -out:ex.dll cs12b-order.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
new Derived() 를 부른다
  1. Derived 의 필드 초기자
  2. Base 의 필드 초기자
  3. Base 의 생성자 본문
  4. Derived 의 생성자 본문
끝 — Tag=1  BaseTag=2
```

★★★ **같은 모양의 프로그램을 C++ 로 던지면.**

```text
===== 소스: cs12b-cpp-order.cpp =====
#include <cstdio>

static int seq = 0;
static int step(const char* what) { std::printf("  %d. %s\n", ++seq, what); return seq; }

struct Base {
    int baseTag = step("Base 의 멤버 초기자");
    Base() { step("Base 의 생성자 본문"); }
};
struct Derived : Base {
    int tag = step("Derived 의 멤버 초기자");
    Derived() { step("Derived 의 생성자 본문"); }
};

int main() {
    std::printf("Derived d; 를 만든다\n");
    Derived d;
    std::printf("끝 — tag = %d, baseTag = %d\n", d.tag, d.baseTag);
}
===== g++ -std=c++20 -Wall -Wextra -o cppex cs12b-cpp-order.cpp && ./cppex (cc exit=0 · run exit=0) =====
Derived d; 를 만든다
  1. Base 의 멤버 초기자
  2. Base 의 생성자 본문
  3. Derived 의 멤버 초기자
  4. Derived 의 생성자 본문
끝 — tag = 3, baseTag = 1
```

| 단계 | C++ (g++ 13.3.0) | C# (.NET 10) |
|---|---|---|
| 1 | **기반의 멤버 초기자** | ★★★ **파생의 필드 초기자** |
| 2 | **기반의 생성자 본문** | **기반의 필드 초기자** |
| 3 | ★★★ **파생의 멤버 초기자** | **기반의 생성자 본문** |
| 4 | **파생의 생성자 본문** | **파생의 생성자 본문** |
| 찍힌 번호 | `baseTag = 1` · `tag = 3` | `BaseTag = 2` · `Tag = 1` |

그림 해설 (한 단계씩):

- ★★★ **파생의 초기자가 C++ 에서는 3번째, C# 에서는 1번째다.** **정확히 맞바뀐다.**\
  ★ 찍힌 번호가 그 증거다 — C++ 은 `tag = 3`, C# 은 `Tag = 1` 이다.
- ★★★ **나머지 셋의 상대 순서는 같다** — 기반의 초기자 → 기반의 본문 → 파생의 본문.\
  **갈리는 것은 「파생의 초기자가 어디로 가느냐」 하나**다.
- ★★ **이유는 각 언어가 지키려는 것이 다르기 때문**이다.\
  C++ 은 「**기반이 완성된 뒤에 파생을 짓는다**」를 지키고,\
  C# 은 「**내 필드 초기자는 내 생성자 본문보다 먼저, 그리고 남의 코드가 돌기 전에**」를 지킨다.\
  ★★★ **그래서 C# 에서는 기반 생성자가 도는 동안 파생 필드가 이미 채워져 있다** — (4)가 그 결과다.
- ★ **한 클래스 안에서의 선언 순서 규칙**은 이 문서가 다시 재지 않았다.\
  C++ 쪽은 [13번](../../../cpp/syntax/13-constructors-member-init-list-and-delegating/) (2)가 **`-Wreorder` 경고 g++ 3건·clang 1건**까지 찍어 두었고,\
  「**리스트에 적은 순서가 아니라 선언 순서**」가 그 결론이다. ★★ **여기서 새로 잰 것은 「기반 ↔ 파생」 축**이다 —\
  [13번](../../../cpp/syntax/13-constructors-member-init-list-and-delegating/)이 **상속을 다루지 않았기 때문**이다.

**비용** — 0. 다만 **이 순서를 모르면 (4)의 버그를 만든다.**

### (2) ★★ `this()` 위임 — 필드 초기자는 **한 번만** 돈다

**언제 쓰나** — 생성자 여럿이 같은 일을 할 때.

```text
===== 소스: cs12b-this.cs =====
using System;

Console.WriteLine("① new Two(7) — this() 로 위임하는 쪽");
var a = new Two(7);
Console.WriteLine($"   Tag={a.Tag}  Seed={a.Seed}");
Console.WriteLine();
Log.Seq = 0;
Console.WriteLine("② new Two() — 위임받는 쪽");
var b = new Two();
Console.WriteLine($"   Tag={b.Tag}  Seed={b.Seed}");

static class Log { public static int Seq; public static int Step(string w) { Console.WriteLine($"  {++Seq}. {w}"); return Seq; } }

class Two {
    public int Tag = Log.Step("★ 필드 초기자 — 몇 번 도나");
    public int Seed;
    public Two() { Log.Step("Two() 본문"); Seed = -1; }
    public Two(int seed) : this() { Log.Step($"Two(int) 본문 — Seed 를 {seed} 로 덮는다"); Seed = seed; }
}
===== csc -out:ex.dll cs12b-this.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
① new Two(7) — this() 로 위임하는 쪽
  1. ★ 필드 초기자 — 몇 번 도나
  2. Two() 본문
  3. Two(int) 본문 — Seed 를 7 로 덮는다
   Tag=1  Seed=7

② new Two() — 위임받는 쪽
  1. ★ 필드 초기자 — 몇 번 도나
  2. Two() 본문
   Tag=1  Seed=-1
```

```text
   new Two(7)                                  new Two()

   1. 필드 초기자   <- ★ 한 번                  1. 필드 초기자
   2. Two() 본문    <- this() 가 먼저 돈다       2. Two() 본문
   3. Two(int) 본문 <- 그다음 내 본문
```

- ★★★ **`Two(int seed) : this()` 를 불러도 필드 초기자는 한 번만** 돈다(`★ 필드 초기자` 줄이 **1번 한 줄**).\
  ★ **`this()` 로 위임하는 생성자는 필드 초기자를 돌리지 않고**, **연쇄의 끝**(`base` 로 가는 쪽)에서 한 번만 돈다.
- ★★ **위임받은 쪽이 먼저 끝나고 그다음 내 본문**이다 — `Two() 본문` 이 `Two(int) 본문` 보다 먼저다.\
  그래서 `Seed` 가 `-1` 로 채워졌다가 **7 로 덮인다.**
- ★★ **C++ 의 위임 생성자와 순서가 같다** — [13번](../../../cpp/syntax/13-constructors-member-init-list-and-delegating/) (4)에서도 **본체가 먼저, 위임한 쪽 본문이 나중**이었다.\
  ★ **여기는 C++ 와 반대가 아니다.** 반대인 것은 (1)의 **기반 ↔ 파생 축** 하나뿐이다.

**비용** — 0. **중복이 사라지는 것**이 값이다.

### (3) ★ `base()` 는 암묵이다 — 그리고 기본 생성자는 언제 사라지나

**언제 쓰나** — 상속받은 클래스에 생성자를 적을 때.

```text
===== 소스: cs12b-implicit.cs =====
using System;

class B1 { public B1(int x) { Console.WriteLine(x); } }
class D1 : B1 { public D1() { } }
class B2 { public B2() { } public B2(int x) { Console.WriteLine(x); } }
class D2 : B2 { public D2() { } }
class C1 { public C1() : this(1) { } public C1(int x) : this() { Console.WriteLine(x); } }
===== csc -target:library -out:ex.dll cs12b-implicit.cs (cc exit=1) =====
cs12b-implicit.cs(4,24): error CS7036: There is no argument given that corresponds to the required parameter 'x' of 'B1.B1(int)'
cs12b-implicit.cs(7,55): error CS0768: Constructor 'C1.C1(int)' cannot call itself through another constructor
```

| 심은 것 | 진단 | 뜻 |
|---|---|---|
| `class D1 : B1` — `B1` 에 **매개변수 없는 생성자가 없다** | ★★★ **`CS7036`** | **`: base()` 를 안 적어도 부르려 한다** |
| `class D2 : B2` — `B2` 에 **있다** | ★ **없음** | 암묵 호출이 성공한다 |
| `C1() : this(1)` 과 `C1(int) : this()` | ★★ **`CS0768`** | **`this()` 연쇄가 자기 자신으로 돌아오면 막는다** |

- ★★★ **`: base()` 를 한 글자도 안 적었는데 `CS7036` 이 난다.** **암묵으로 불린다는 증거**다.\
  ★ 그래서 **기반에 매개변수 없는 생성자가 없으면 파생 생성자마다 `: base(…)` 를 적어야 한다.**
- ★★★ **기본 생성자는 「생성자를 하나라도 적는 순간」 사라진다** — (8)의 `HasCtor` 가 그 실측이다.\
  `class HasCtor { public HasCtor(int x) … }` 에 `new HasCtor()` 를 쓰면 **`CS7036`** 이다.\
  ★ **`class NoCtor { public int X = 0; }` 은 그대로 `new NoCtor()` 가 된다** — 생성자를 안 적었기 때문이다.
- ★★ **`this()` 연쇄가 순환하면 `CS0768` 로 막힌다.** **컴파일 시간에 잡힌다** —\
  C++ 의 위임 재귀(`A() : A() {}`)가 **UB 인 것과 갈리는 자리**다([13번](../../../cpp/syntax/13-constructors-member-init-list-and-delegating/) (4)).

**비용** — 0.

### (4) ★★★ 생성자에서 가상 메서드를 부르면 — 값을 찍어 본다

**언제 쓰나** — 「초기화 훅」을 기반 클래스에 두고 싶을 때. **C# 에서 가장 조용한 사고**다.

```text
===== 소스: cs12b-virtual.cs =====
using System;

Console.WriteLine("new Child(\"내가 준 값\") 을 만든다");
var c = new Child("내가 준 값");
Console.WriteLine($"끝 — FromInitializer=「{c.FromInitializer}」  FromBody=「{c.FromBody}」  Len={c.Len}");

static class Log { public static int Seq; public static int Step(string w) { Console.WriteLine($"  {++Seq}. {w}"); return Seq; } }

abstract class Parent {
    protected Parent() {
        Log.Step("Parent 생성자 본문 — 여기서 Describe() 를 부른다");
        Console.WriteLine($"      Describe() → {Describe()}");
    }
    public abstract string Describe();
}
class Child : Parent {
    public string FromInitializer = "필드 초기자가 넣은 값";
    public string FromBody;
    public int Len;
    public Child(string given) {
        Log.Step("Child 생성자 본문");
        FromBody = given;
        Len = given.Length;
    }
    public override string Describe() =>
        $"FromInitializer=「{FromInitializer ?? "null"}」  FromBody=「{(FromBody is null ? "null" : FromBody)}」  Len={Len}";
}
===== csc -out:ex.dll cs12b-virtual.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
new Child("내가 준 값") 을 만든다
  1. Parent 생성자 본문 — 여기서 Describe() 를 부른다
      Describe() → FromInitializer=「필드 초기자가 넣은 값」  FromBody=「null」  Len=0
  2. Child 생성자 본문
끝 — FromInitializer=「필드 초기자가 넣은 값」  FromBody=「내가 준 값」  Len=6
```

```text
   new Child("내가 준 값")

   1. ★ Child 의 필드 초기자      FromInitializer = "필드 초기자가 넣은 값"  <- 이미 채워졌다
   2. Parent 생성자 본문          Describe() 를 부른다
                                    -> ★★★ Child.Describe 가 불린다 (파생 것)
                                    -> FromInitializer 는 값이 있고
                                       FromBody 는 null · Len 은 0     <- 본문이 아직 안 돌았다
   3. Child 생성자 본문           FromBody·Len 을 채운다
```

- ★★★ **`Describe()` 가 파생 것으로 불린다.** 기반 생성자가 도는 중인데 **가상 디스패치는 이미 파생을 가리킨다.**
- ★★★ **절반만 초기화된 상태가 보인다** — `FromInitializer` 는 **값이 있고**(필드 초기자가 1번에 돌았다),\
  `FromBody` 는 **null**, `Len` 은 **0** 이다. **(1)의 순서가 그대로 값으로 나온 것**이다.
- ★★ **이 예제는 `?? "null"` 로 널을 견디게 만들어 놓았다.** 그러지 않으면 **터진다** — 아래에서 터뜨린다.

★★★ **널을 안 견디게 하면 실제로 무엇이 나오나.**

```text
===== 소스: cs12b-nre.cs =====
using System;

// 생성자에서 가상 메서드를 부르면 — 파생 쪽 본문이 아직 안 돌았다
var c = new Child("내가 준 값");
Console.WriteLine(c.Describe());

abstract class Parent {
    protected Parent() { Console.Error.WriteLine("  [Parent 생성자] 이제 Describe() 를 부른다"); Console.Error.WriteLine("  " + Describe()); }
    public abstract string Describe();
}
sealed class Child : Parent {
    private readonly string _given;
    public Child(string given) { _given = given; }
    public override string Describe() => "길이 " + _given.Length;
}
===== csc -out:ex.dll cs12b-nre.cs && dotnet ex.dll (cc exit=0 · run exit=134) =====
  [Parent 생성자] 이제 Describe() 를 부른다
Unhandled exception. System.NullReferenceException: Object reference not set to an instance of an object.
   at Child.Describe()
   at Parent..ctor()
   at Child..ctor(String given)
   at Program.<Main>$(String[] args)
```

- ★★★ **`NullReferenceException` 이고, 스택이 누가 누구를 불렀는지 그대로 적는다** —\
  `at Child.Describe()` → `at Parent..ctor()` → `at Child..ctor(String given)`.\
  ★ **`run exit=134`** 이고 **`cc exit=0`** 이다 — **컴파일러는 한 마디도 안 했다**((9)).
- ★★ **`readonly` 필드여도 막아 주지 않는다** — `_given` 은 `readonly` 인데 **그 시점에 아직 널**이다.

★★★ **같은 프로그램을 C++ 로 던지면 완전히 다른 일이 일어난다.**

```text
===== 소스: cs12b-cpp-virtual.cpp =====
// 생성자에서 가상 함수를 부르면 — C++ 은 어디로 가나
#include <cstdio>
#include <string>

struct Parent {
    Parent() {
        std::printf("  [Parent 생성자 본문] 여기서 describe() 를 부른다\n");
        std::printf("      describe() → %s\n", describe().c_str());
    }
    virtual ~Parent() = default;
    virtual std::string describe() const { return "Parent::describe (기반 버전)"; }
};

struct Child : Parent {
    std::string fromInitializer = "멤버 초기자가 넣은 값";
    std::string fromBody;
    int len = -1;
    explicit Child(const std::string& given) {
        std::printf("  [Child 생성자 본문]\n");
        fromBody = given;
        len = static_cast<int>(given.size());
    }
    std::string describe() const override {
        return "fromInitializer=「" + fromInitializer + "」 fromBody=「" + fromBody +
               "」 len=" + std::to_string(len);
    }
};

int main() {
    std::printf("Child c(\"내가 준 값\"); 을 만든다\n");
    Child c("내가 준 값");
    std::printf("끝 — %s\n", c.describe().c_str());
}
===== g++ -std=c++20 -Wall -Wextra -o cppex cs12b-cpp-virtual.cpp && ./cppex (cc exit=0 · run exit=0) =====
Child c("내가 준 값"); 을 만든다
  [Parent 생성자 본문] 여기서 describe() 를 부른다
      describe() → Parent::describe (기반 버전)
  [Child 생성자 본문]
끝 — fromInitializer=「멤버 초기자가 넣은 값」 fromBody=「내가 준 값」 len=14
```

| | C# | C++ |
|---|---|---|
| 기반 생성자에서 가상 호출이 가는 곳 | ★★★ **파생 것**(`Child.Describe`) | ★★★ **기반 것**(`Parent::describe`) |
| 그때 파생 필드 초기자는 | ★ **이미 돌았다** | ★ **아직 안 돌았다** |
| 그래서 보이는 것 | **절반만 채워진 파생 상태** | **파생 상태를 아예 안 본다** |
| 터지나 | ★★ **`NullReferenceException` 이 날 수 있다** | **안 난다**(다른 함수가 불린다) |

- ★★★ **두 언어가 정반대로 안전하지 않다.** C# 은 **파생 코드가 미완성 상태를 본다**,\
  C++ 은 **파생 코드가 아예 안 불려 의도한 동작이 조용히 사라진다.**\
  ★ **둘 다 「생성자에서 가상 함수를 부르지 마라」로 귀결되는데 이유가 다르다.**
- ★ **C++ 쪽 `len=14`** 는 `"내가 준 값"` 의 **바이트 수**다(UTF-8) — C# 의 `Len=6` 은 **UTF-16 코드 단위 수**다.\
  ★ **이 주제와는 무관한 차이**이므로 근거로 쓰지 않는다.

**비용** — 0. **처방은 하나다** — **생성자에서 가상 메서드를 부르지 않는다.**\
필요하면 **생성이 끝난 뒤 부르는 `Initialize()` 를 따로** 두거나 **`sealed`** 로 막는다.

### (5) ★ 필드와 프로퍼티 — 무엇이 저장소를 갖나

**언제 쓰나** — 「필드로 둘까 프로퍼티로 둘까」에서.

```text
===== 소스: cs12b-field-prop.cs =====
using System;
using System.Reflection;

var t = typeof(Sample);
Console.WriteLine("필드   : " + string.Join(" · ", Array.ConvertAll(
    t.GetFields(BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic),
    f => f.Name + (f.IsInitOnly ? " (readonly)" : ""))));
Console.WriteLine("프로퍼티: " + string.Join(" · ", Array.ConvertAll(t.GetProperties(), p => p.Name)));
Console.WriteLine("메서드  : " + string.Join(" · ", Array.ConvertAll(
    Array.FindAll(t.GetMethods(BindingFlags.Instance | BindingFlags.Public | BindingFlags.DeclaredOnly), m => m.IsSpecialName),
    m => m.Name)));
Console.WriteLine();

var s = new Sample(5);
Console.WriteLine($"기본값 — 생성자가 안 건드린 자동 프로퍼티 Untouched = {s.Untouched} · 필드 Text = {(s.Text is null ? "null" : s.Text)}");
Console.WriteLine($"읽기 전용 프로퍼티 Doubled = {s.Doubled}   ← 저장소가 없다(계산해서 돌려준다)");
Console.WriteLine($"자동 프로퍼티 Auto = {s.Auto}   ← 이름이 <Auto>k__BackingField 인 숨은 필드가 있다");

class Sample {
    public readonly int Fixed;
    public int Untouched { get; set; }
    public string Text;
    public int Auto { get; set; } = 3;
    public int Doubled => Fixed * 2;
    public Sample(int v) { Fixed = v; }
}
===== csc -out:ex.dll cs12b-field-prop.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
cs12b-field-prop.cs(22,19): warning CS0649: Field 'Sample.Text' is never assigned to, and will always have its default value null
필드   : Fixed (readonly) · <Untouched>k__BackingField · Text · <Auto>k__BackingField
프로퍼티: Untouched · Auto · Doubled
메서드  : get_Untouched · set_Untouched · get_Auto · set_Auto · get_Doubled

기본값 — 생성자가 안 건드린 자동 프로퍼티 Untouched = 0 · 필드 Text = null
읽기 전용 프로퍼티 Doubled = 10   ← 저장소가 없다(계산해서 돌려준다)
자동 프로퍼티 Auto = 3   ← 이름이 <Auto>k__BackingField 인 숨은 필드가 있다
```

| 적은 것 | 숨은 필드 | 메서드 | 기본값 |
|---|---|---|---|
| `public readonly int Fixed;` | `Fixed (readonly)` | — | 생성자에서만 |
| `public int Untouched { get; set; }` | `<Untouched>k__BackingField` | `get_`·`set_` | **0** |
| `public string Text;` | `Text` | — | ★ **null**(`CS0649` 경고) |
| `public int Auto { get; set; } = 3;` | `<Auto>k__BackingField` | `get_`·`set_` | **3** |
| `public int Doubled => Fixed * 2;` | ★★★ **없다** | `get_` 만 | 계산한다 |

- ★★★ **자동 프로퍼티는 숨은 필드 하나 + 메서드 둘**이다. `<Untouched>k__BackingField` 가 리플렉션에 그대로 보인다.
- ★★★ **식 본문 프로퍼티(`=> …`)는 저장소가 없다** — 필드 목록에 없고 `get_Doubled` 하나뿐이다.
- ★★ **`CS0649` 가 붙은 자리가 있다** — `Field 'Sample.Text' is never assigned to, and will always have its default value null`.\
  **공개 필드를 안 채우면 컴파일러가 말해 준다** — 이 주제에서 **컴파일러가 말해 주는 몇 안 되는 자리**다((9)).
- ★ **프로퍼티의 전모는 목록의 13번 주제**다. 여기서는 「**무엇이 필드가 되나**」까지만 본다.

**비용** — 자동 프로퍼티는 **필드 하나 + 호출 둘**. 식 본문 프로퍼티는 **저장소 0**이다.

### (6) ★★ 기본 생성자(C# 12) — 무엇을 줄이나, 무엇을 잃나

**언제 쓰나** — 생성자가 「매개변수를 필드에 넣기만」 할 때.

```text
===== 소스: cs12b-primary.cs =====
using System;
using System.Reflection;

foreach (var t in new[] { typeof(UsedInBody), typeof(OnlyToProperty), typeof(OnlyToBase), typeof(Classic) }) {
    var fs = t.GetFields(BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic);
    var names = Array.ConvertAll(fs, f => $"{f.FieldType.Name} {f.Name}" + (f.IsInitOnly ? " (readonly)" : ""));
    var cs = Array.ConvertAll(t.GetConstructors(), c => "(" + string.Join(", ", Array.ConvertAll(c.GetParameters(), p => p.ParameterType.Name + " " + p.Name)) + ")");
    Console.WriteLine($"{t.Name,-16} 필드 [{(names.Length == 0 ? "없음" : string.Join("] [", names))}]  생성자 {string.Join(" ", cs)}");
}
Console.WriteLine();
var u = new UsedInBody("이름");
Console.WriteLine($"기본 생성자 매개변수는 본문에서 보인다 : {u.Greet()}");
Console.WriteLine($"★ 그리고 고칠 수도 있다               : {u.Bump()} → {u.Greet()}");
Console.WriteLine($"  같은 자리에 손으로 쓴 필드는 readonly 를 달 수 있다 : Classic 의 _name");

class UsedInBody(string name) {
    public string Greet() => "안녕 " + name;
    public string Bump() { name += "!"; return name; }
}
class OnlyToProperty(string name) { public string Name { get; } = name; }
class BaseOf(string tag) { public string Tag = tag; }
class OnlyToBase(string name) : BaseOf(name) { }
class Classic {
    private readonly string _name;
    public Classic(string name) { _name = name; }
    public string Greet() => "안녕 " + _name;
}
===== csc -out:ex.dll cs12b-primary.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
UsedInBody       필드 [String <name>P]  생성자 (String name)
OnlyToProperty   필드 [String <Name>k__BackingField (readonly)]  생성자 (String name)
OnlyToBase       필드 [String Tag]  생성자 (String name)
Classic          필드 [String _name (readonly)]  생성자 (String name)

기본 생성자 매개변수는 본문에서 보인다 : 안녕 이름
★ 그리고 고칠 수도 있다               : 이름! → 안녕 이름!
  같은 자리에 손으로 쓴 필드는 readonly 를 달 수 있다 : Classic 의 _name
```

```text
===== 소스: cs12b-il-primary.cs =====
using System;

Il.Dump(typeof(UsedInBody), "Greet");
Il.Dump(typeof(Classic), "Greet");
Il.Dump(typeof(OnlyToProperty), "get_Name");
Il.Dump(typeof(Caller), "Make");

class UsedInBody(string name) { public string Greet() => "안녕 " + name; }
class OnlyToProperty(string name) { public string Name { get; } = name; }
class Classic { private readonly string _name; public Classic(string name) { _name = name; } public string Greet() => "안녕 " + _name; }
static class Caller { public static object Make() => new UsedInBody("x"); }
===== csc -r:il.dll -out:ex.dll cs12b-il-primary.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
--- UsedInBody.Greet ---
  IL_0000: ldstr "안녕 "
  IL_0005: ldarg.0
  IL_0006: ldfld UsedInBody::<name>P
  IL_000b: call System.String::Concat
  IL_0010: ret
--- Classic.Greet ---
  IL_0000: ldstr "안녕 "
  IL_0005: ldarg.0
  IL_0006: ldfld Classic::_name
  IL_000b: call System.String::Concat
  IL_0010: ret
--- OnlyToProperty.get_Name ---
  IL_0000: ldarg.0
  IL_0001: ldfld OnlyToProperty::<Name>k__BackingField
  IL_0006: ret
--- Caller.Make ---
  IL_0000: ldstr "x"
  IL_0005: newobj UsedInBody::.ctor
  IL_000a: ret
```

| 클래스 | 만들어진 필드 | `readonly` 인가 |
|---|---|---|
| `class UsedInBody(string name)` — 본문에서 쓴다 | `String <name>P` | ★★★ **아니다** |
| `class OnlyToProperty(string name)` — 프로퍼티에만 넘긴다 | `<Name>k__BackingField` | ★ **맞다** |
| `class OnlyToBase(string name)` — `base` 에만 넘긴다 | ★★★ **없다**(기반의 `Tag` 뿐) | — |
| `class Classic` — 손으로 쓴 판 | `_name` | ★ **맞다** |

- ★★★ **기본 생성자 매개변수를 본문에서 쓰면 숨은 필드가 생긴다**(`<name>P`).\
  **그리고 그 필드는 `readonly` 가 아니다** — 실제로 **고쳐진다**(`Bump()` 가 `이름` → `이름!`).\
  ★★ **손으로 쓴 `Classic` 의 `_name` 은 `readonly`** 다. **그것이 잃는 것**이다.
- ★★★ **`base` 에만 넘기면 필드가 아예 안 생긴다** — `OnlyToBase` 의 필드 목록에 기반의 `Tag` 밖에 없다.\
  **쓰이지 않으면 저장하지 않는다.**
- ★★ **IL 로 보면 `Greet()` 는 손으로 쓴 판과 한 글자도 같다** — `ldfld` 대상 이름만 다르다\
  (`UsedInBody::<name>P` 대 `Classic::_name`). **기본 생성자는 런타임에 아무것도 아니다.**
- ★ **호출 쪽도 같다** — `newobj UsedInBody::.ctor` 한 줄이다.

**비용** — **줄어드는 것은 소스 줄**이고, **잃는 것은 `readonly`** 다.\
★ **불변을 원하면 `class C(string n) { private readonly string _n = n; }`** 처럼 **직접 받아 두면 된다.**

### (7) ★ `required`(C# 11) — 누가 보는가

**언제 쓰나** — 「이 프로퍼티는 반드시 채워져야 한다」를 **생성자 없이** 말하고 싶을 때.

```text
===== 소스: cs12b-required.cs =====
#nullable enable
using System;

var ok = new Conf { Host = "example.com", Port = 443 };
Console.WriteLine($"객체 초기화자로 채운 것            : {ok.Host}:{ok.Port}");

var viaCtor = new Conf2("host2", 8080);
Console.WriteLine($"SetsRequiredMembers 를 단 생성자   : {viaCtor.Host}:{viaCtor.Port}");

Console.WriteLine();
Console.WriteLine("★ required 는 컴파일러가 보는 것이다 — 리플렉션은 그 문을 안 지난다.");
var sneaky = (Conf)System.Runtime.CompilerServices.RuntimeHelpers.GetUninitializedObject(typeof(Conf));
Console.WriteLine($"GetUninitializedObject 로 만든 것  : Host={(sneaky.Host is null ? "null" : sneaky.Host)}  Port={sneaky.Port}");
Console.WriteLine($"  Conf 에 RequiredMemberAttribute 가 박혀 있나 : {Attribute.IsDefined(typeof(Conf), typeof(System.Runtime.CompilerServices.RequiredMemberAttribute))}");

class Conf { public required string Host { get; init; } public required int Port { get; init; } }
class Conf2 {
    public required string Host { get; init; }
    public required int Port { get; init; }
    [System.Diagnostics.CodeAnalysis.SetsRequiredMembers]
    public Conf2(string h, int p) { Host = h; Port = p; }
}
===== csc -out:ex.dll cs12b-required.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
객체 초기화자로 채운 것            : example.com:443
SetsRequiredMembers 를 단 생성자   : host2:8080

★ required 는 컴파일러가 보는 것이다 — 리플렉션은 그 문을 안 지난다.
GetUninitializedObject 로 만든 것  : Host=null  Port=0
  Conf 에 RequiredMemberAttribute 가 박혀 있나 : True
```

- ★★ **객체 초기화자로 채우면 통과**하고, **`[SetsRequiredMembers]` 를 단 생성자로도** 통과한다.
- ★★★ **`required` 는 컴파일러가 보는 것이다.** `RuntimeHelpers.GetUninitializedObject` 로 만들면\
  **`Host=null · Port=0`** 인 객체가 **아무 저항 없이** 나온다.
- ★★ **그런데 흔적은 메타데이터에 남는다** — `RequiredMemberAttribute` 가 타입에 **박혀 있다**(`True`).\
  **런타임이 그것을 강제하지 않을 뿐**이다.
- ★ **안 채우면 컴파일 에러다** — (8)의 `CS9035` 가 그 자리이고, **빠진 멤버마다 한 건씩** 난다.

**비용** — 0. **런타임 검사가 아니라는 것**만 알면 된다.

### (8) ★ 컴파일러가 막아 주는 것 — 진단 네 가지

**언제 쓰나** — 「이건 컴파일러가 잡아 주겠지」를 확인할 때.

```text
===== 소스: cs12b-diag.cs =====
#nullable enable
using System;

var a = new NoCtor();
var b = new HasCtor();
var c = new Conf { Host = "h" };
var d = new Conf();
var e = new Ro(1);
e.Fixed = 9;

class NoCtor { public int X = 0; }
class HasCtor { public int X; public HasCtor(int x) { X = x; } }
class Conf { public required string Host { get; init; } public required int Port { get; init; } }
class Ro { public readonly int Fixed; public Ro(int v) { Fixed = v; } }
===== csc -out:ex.dll cs12b-diag.cs (cc exit=1) =====
cs12b-diag.cs(5,13): error CS7036: There is no argument given that corresponds to the required parameter 'x' of 'HasCtor.HasCtor(int)'
cs12b-diag.cs(6,13): error CS9035: Required member 'Conf.Port' must be set in the object initializer or attribute constructor.
cs12b-diag.cs(7,13): error CS9035: Required member 'Conf.Host' must be set in the object initializer or attribute constructor.
cs12b-diag.cs(7,13): error CS9035: Required member 'Conf.Port' must be set in the object initializer or attribute constructor.
cs12b-diag.cs(9,1): error CS0191: A readonly field cannot be assigned to (except in a constructor or init-only setter of the type in which the field is defined or a variable initializer)
```

| 심은 것 | 진단 | 뜻 |
|---|---|---|
| `new NoCtor()` — 생성자를 안 적은 클래스 | ★ **없음** | 기본 생성자가 살아 있다 |
| `new HasCtor()` — 생성자를 적은 클래스 | ★★★ **`CS7036`** | **기본 생성자가 사라졌다** |
| `new Conf { Host = "h" }` — `Port` 를 빠뜨림 | ★★ **`CS9035`** | `required` 가 빠졌다 |
| `new Conf()` — 둘 다 빠뜨림 | ★★ **`CS9035` ×2** | ★ **빠진 멤버마다 한 건** |
| `e.Fixed = 9;` — `readonly` 필드에 대입 | ★★ **`CS0191`** | 생성자·초기자 밖에서는 못 쓴다 |

- ★★★ **`CS0191` 의 문구가 규칙 전부를 적는다** —\
  `except in a constructor or init-only setter of the type in which the field is defined or a variable initializer`.\
  **「어디서 쓸 수 있나」가 세 곳으로 못 박혀 있다.**
- ★★ **`CS9035` 는 빠진 멤버마다 난다** — `new Conf()` 에서 **두 건**이다. **어느 것이 빠졌는지 이름까지** 적는다.
- ★ **`NoCtor` 만 조용하다** — 생성자를 하나도 안 적었으므로 **기본 생성자가 남아 있다.**

**비용** — 0.

### (9) 경고를 누가 보나 — 탐침 여섯

「경고가 안 났다」를 산문으로 적으면 **안 물어본 것과 물었는데 조용한 것이 구분되지 않는다.**\
그래서 **생성자 주변의 함정 여섯**을 한 파일에 심고 **`-warn:9`**(최고 경고 수준)로 물었다.

```text
===== 소스: cs12b-quiet.cs =====
using System;

// 생성자 주변의 함정을 여섯 자리에 심었다. -warn:9 로 컴파일해 몇 군데에서 말하는지 센다.
public abstract class P1Base {
    protected P1Base() { Console.WriteLine(Describe()); }   // 1. 생성자에서 가상 메서드
    public abstract string Describe();
}
public class P1Derived : P1Base {
    private string _set;                                     // 2. 생성자 본문이 채우는 필드
    public P1Derived(string s) { _set = s; }
    public override string Describe() => _set.Length.ToString();  // 3. 그 필드를 Describe 가 읽는다
}
public class P2 {
    public readonly int[] Fixed = new int[3];                // 4. readonly 인데 내용은 바뀐다
    public void Change() { Fixed[0] = 99; }
}
public class P3Base { public P3Base() { } }
public class P3 : P3Base {
    public int A = 1;
    public int B;
    public P3() { B = A + 1; }                               // 5. 초기화 순서에 기댄 계산
}
public class P4 {
    public int X;
    public P4() : this(0) { }                                // 6. this() 연쇄
    public P4(int x) { X = x; }
}
===== csc -warn:9 -target:library -out:ex.dll cs12b-quiet.cs (cc exit=0) =====
```

| 심은 것 | 진단 | 실제로는 |
|---|---|---|
| 기반 생성자에서 가상 메서드 호출 | ★★★ **0** | ★★★ **파생 것이 불린다**((4)) |
| 생성자 본문이 채우는 필드 | ★★★ **0** | 그 시점에 **null** |
| `Describe()` 가 그 필드를 읽는다 | ★★★ **0** | ★★★ **`NullReferenceException`**((4)) |
| `readonly` 배열의 내용 변경 | ★★★ **0** | `readonly` 는 **참조만** 고정한다 |
| 초기화 순서에 기댄 계산(`B = A + 1`) | ★★★ **0** | 이 판에서는 맞다 — 순서를 바꾸면 깨진다 |
| `this()` 연쇄 | ★★★ **0** | 정상(순환이면 `CS0768`) |

- ★★★ **탐침 여섯 중 답한 것 0 · 침묵한 것 6이다.** **`-warn:9` 에서도 `cc exit=0` 에 진단 0줄**이다.
- ★★★ **이 주제에서 컴파일러가 보는 것은 「형태」뿐이다**((8)의 넷) — **「순서 때문에 생기는 사고」는 한 건도 안 본다.**\
  그 자리를 메우는 것이 **(1)의 로그**와 **(4)의 예외 전문**이다.
- ★★ **`readonly` 가 참조만 고정하는 것**도 0건이다 — (8)의 `CS0191` 은 **재대입**만 잡는다.

## 문법 — 형태와 규칙

### 형태

```csharp
// cs12b-form.cs
using System;

var a = new Account("111", 1000);
var b = new Account("222");
var c = new Savings("333", 500, 0.03m);
Console.WriteLine($"{a.Describe()} / {b.Describe()} / {c.Describe()}");

class Account {
    private readonly string _id;              // ① readonly 필드 — 생성자에서만 쓴다
    public decimal Balance { get; private set; }   // ② 자동 프로퍼티
    public string Owner { get; init; } = "미상";   // ③ init 전용(C# 9)
    public int Version = 1;                   // ④ 필드 초기자 — 본문보다 먼저 돈다

    public Account(string id, decimal opening) {   // ⑤ 본체 생성자
        _id = id;
        Balance = opening;
    }
    public Account(string id) : this(id, 0m) { }   // ⑥ this() 위임 — 필드 초기자는 한 번만

    public virtual string Describe() => $"{_id}:{Balance:0}({Owner},v{Version})";
}

class Savings(string id, decimal opening, decimal rate) : Account(id, opening) {
    // ⑦ 기본 생성자(C# 12) — 매개변수가 본문 전체에서 보이고, base 로 넘긴다
    public decimal Rate => rate;
    public override string Describe() => base.Describe() + $"+{rate:0.00}";
}
```

```text
===== 소스: cs12b-form.cs =====
using System;

var a = new Account("111", 1000);
var b = new Account("222");
var c = new Savings("333", 500, 0.03m);
Console.WriteLine($"{a.Describe()} / {b.Describe()} / {c.Describe()}");

class Account {
    private readonly string _id;              // ① readonly 필드 — 생성자에서만 쓴다
    public decimal Balance { get; private set; }   // ② 자동 프로퍼티
    public string Owner { get; init; } = "미상";   // ③ init 전용(C# 9)
    public int Version = 1;                   // ④ 필드 초기자 — 본문보다 먼저 돈다

    public Account(string id, decimal opening) {   // ⑤ 본체 생성자
        _id = id;
        Balance = opening;
    }
    public Account(string id) : this(id, 0m) { }   // ⑥ this() 위임 — 필드 초기자는 한 번만

    public virtual string Describe() => $"{_id}:{Balance:0}({Owner},v{Version})";
}

class Savings(string id, decimal opening, decimal rate) : Account(id, opening) {
    // ⑦ 기본 생성자(C# 12) — 매개변수가 본문 전체에서 보이고, base 로 넘긴다
    public decimal Rate => rate;
    public override string Describe() => base.Describe() + $"+{rate:0.00}";
}
===== csc -out:ex.dll cs12b-form.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
111:1000(미상,v1) / 222:0(미상,v1) / 333:500(미상,v1)+0.03
```

### 규칙

- **초기화 순서는 파생 필드 초기자 → 기반 필드 초기자 → 기반 생성자 본문 → 파생 생성자 본문**이다((1)).
- **`: base()` 는 안 적어도 불린다.** 기반에 매개변수 없는 생성자가 없으면 **`CS7036`** 이다((3)).
- **`: this(…)` 로 위임하면 필드 초기자는 연쇄의 끝에서 한 번만** 돈다((2)).
- **생성자를 하나라도 적으면 기본 생성자가 사라진다**((8)).
- **`readonly` 필드는 생성자·`init` setter·필드 초기자에서만** 대입된다((8)). **참조만 고정한다**((9)).
- **`required` 는 컴파일러가 검사한다** — 리플렉션 생성은 지나간다((7)).
- **기본 생성자 매개변수는 본문에서 쓰면 숨은 필드가 되고, 그 필드는 `readonly` 가 아니다**((6)).
- **생성자에서 가상 메서드를 부르면 파생 것이 불리고, 그 시점에 파생 생성자 본문은 아직 안 돌았다**((4)).

### 금지 사례 — 다섯 줄이 각각 막힌다

```text
===== 소스: cs12b-implicit.cs =====
using System;

class B1 { public B1(int x) { Console.WriteLine(x); } }
class D1 : B1 { public D1() { } }
class B2 { public B2() { } public B2(int x) { Console.WriteLine(x); } }
class D2 : B2 { public D2() { } }
class C1 { public C1() : this(1) { } public C1(int x) : this() { Console.WriteLine(x); } }
===== csc -target:library -out:ex.dll cs12b-implicit.cs (cc exit=1) =====
cs12b-implicit.cs(4,24): error CS7036: There is no argument given that corresponds to the required parameter 'x' of 'B1.B1(int)'
cs12b-implicit.cs(7,55): error CS0768: Constructor 'C1.C1(int)' cannot call itself through another constructor
```

```text
===== 소스: cs12b-diag.cs =====
#nullable enable
using System;

var a = new NoCtor();
var b = new HasCtor();
var c = new Conf { Host = "h" };
var d = new Conf();
var e = new Ro(1);
e.Fixed = 9;

class NoCtor { public int X = 0; }
class HasCtor { public int X; public HasCtor(int x) { X = x; } }
class Conf { public required string Host { get; init; } public required int Port { get; init; } }
class Ro { public readonly int Fixed; public Ro(int v) { Fixed = v; } }
===== csc -out:ex.dll cs12b-diag.cs (cc exit=1) =====
cs12b-diag.cs(5,13): error CS7036: There is no argument given that corresponds to the required parameter 'x' of 'HasCtor.HasCtor(int)'
cs12b-diag.cs(6,13): error CS9035: Required member 'Conf.Port' must be set in the object initializer or attribute constructor.
cs12b-diag.cs(7,13): error CS9035: Required member 'Conf.Host' must be set in the object initializer or attribute constructor.
cs12b-diag.cs(7,13): error CS9035: Required member 'Conf.Port' must be set in the object initializer or attribute constructor.
cs12b-diag.cs(9,1): error CS0191: A readonly field cannot be assigned to (except in a constructor or init-only setter of the type in which the field is defined or a variable initializer)
```

- ★ **다섯 에러가 이 주제의 규칙 넷에 대응한다** — **암묵 `base()`**(`CS7036`) · **`this()` 순환**(`CS0768`) ·\
  **`required`**(`CS9035`) · **`readonly`**(`CS0191`).
- ★★ **`CS0768` 이 C++ 와 갈리는 자리다** — C++ 의 위임 재귀는 **UB** 인데 C# 은 **컴파일에서 막는다**.

## 어디서 틀리나

### 1. ★★★ 「C# 도 기반부터 다 짓고 파생을 짓는다」

- ★ **파생의 필드 초기자가 제일 먼저다**((1)). **C++ 와 정확히 반대**인 자리가 여기 하나다.

### 2. ★★★ 「생성자에서 가상 메서드를 부르면 기반 것이 불린다」

- ★ **C++ 에서는 그렇고 C# 에서는 아니다**((4)). **C# 은 파생 것이 불리고 절반만 채워진 상태를 본다.**
- ★★ **컴파일러는 한 마디도 안 한다**((9)). `NullReferenceException` 으로만 드러난다.

### 3. ★★ 「`this()` 를 쓰면 필드 초기자가 두 번 돈다」

- ★ **한 번이다**((2)). 위임하는 쪽은 필드 초기자를 **안 돌린다.**

### 4. ★★ 「`readonly` 면 안 바뀐다」

- ★ **참조만 고정한다**((9)). `readonly int[]` 의 **원소는 바뀐다.**

### 5. ★★ 「`required` 면 런타임에도 보장된다」

- ★ **컴파일러가 보는 것이다**((7)). `GetUninitializedObject` 는 **그 문을 안 지난다.**

### 6. ★ 「기본 생성자(C# 12)는 그냥 줄여 쓰기다」

- ★ **`readonly` 를 잃는다**((6)). 본문에서 쓰면 **고칠 수 있는 숨은 필드**가 생긴다.

### 7. ★ 「생성자를 적어도 `new T()` 는 되겠지」

- ★ **`CS7036`** 이다((8)). **기본 생성자는 하나라도 적는 순간 사라진다.**

## 구현 세부사항 대 언어 보장

| 층 | 이 주제에서 해당하는 것 | 어떻게 확인했나 | **도구가 못 보는 것** |
|---|---|---|---|
| **언어 명세(ECMA-334)** | ★★★ **초기화 순서 넷**((1)) · **`base()` 암묵 호출**((3)) · **`this()` 위임에서 필드 초기자 1회**((2)) · **생성자를 적으면 기본 생성자가 사라지는 것**((8)) · **가상 호출이 파생으로 가는 것**((4)) · `readonly`·`required` 의 검사 자리((7)(8)) | 로그 순서 · 진단 코드 + `cc exit` | ★★★ **「그 순서 때문에 생기는 사고」는 한 건도 안 본다**((9)) |
| **런타임·BCL 구현** | ★★ **숨은 필드 이름**(`<name>P`·`<Auto>k__BackingField`) · **`base` 에만 넘기면 필드가 안 생기는 것**((6)) · `GetUninitializedObject` 가 생성자를 건너뛰는 것((7)) · IL 이 손으로 쓴 판과 같은 것((6)) | 리플렉션 출력 · IL 덤프 | ★★ **이름 형식은 Roslyn 이 정한다** — 판이 오르면 바뀔 수 있다 |
| **이 판의 관찰** | 진단 문구 · 스택 트레이스 프레임 이름(`at Parent..ctor()`) · `run exit=134` | 예외 전문 | ★ **`-debug` 를 주면 줄 번호가 붙어 트레이스가 달라진다** |

### 「도구가 못 보는 것」을 층마다

| 사실 | 층 | `csc` 기본 | `csc -warn:9` | 실행 출력 | 예외 전문 |
|---|---|---|---|---|---|
| 기본 생성자가 사라졌다 | 명세 | **error** | error | — | — |
| `required` 를 안 채웠다 | 명세 | **error** | error | — | — |
| `readonly` 에 재대입 | 명세 | **error** | error | — | — |
| ★★★ **초기화 순서 자체** | 명세 | ★★★ **0건** | ★★★ **0건** | ★ **여기만 보인다** | — |
| ★★★ **생성자 속 가상 호출** | 명세 | ★★★ **0건** | ★★★ **0건** | ★ 값이 이상하다 | ★★★ **여기서 증명된다** |
| ★★ **`readonly` 배열의 내용 변경** | 명세 | ★★★ **0건** | ★★★ **0건** | ★ 보인다 | — |
| 공개 필드를 안 채움 | 명세 | ★ **`CS0649` 경고** | 경고 | — | — |

- ★★ **이 표의 결론 세 줄**
  - **컴파일러는 「형태」를 다 막고 「순서」를 하나도 안 막는다.**
  - **초기화 순서는 로그로만, 가상 호출 사고는 예외 전문으로만** 드러난다.
  - **`CS0649` 하나**가 이 주제에서 유일한 「**경고**」다 — 나머지는 전부 에러이거나 침묵이다.

### ★ 진단이 0줄인 것도 블록으로 받았다

(9)가 그 자리다. **탐침 여섯 중 답한 것 0 · 침묵한 것 6**이고 **`cc exit=0`** 이다.\
그 침묵을 메우는 것이 (1)의 번호 매긴 로그와 (4)의 스택 트레이스다.

## 언제 쓰고 언제 안 쓰나

| 상황 | 고르는 것 | 왜 |
|---|---|---|
| 모든 생성자가 같은 기본값을 쓴다 | **필드 초기자** | 생성자마다 되풀이하지 않는다 |
| 생성자 여럿이 같은 일을 한다 | **`this(…)` 위임** | 필드 초기자가 **한 번만** 돈다((2)) |
| 한 번 정하면 안 바뀐다 | **`readonly` 필드** 또는 **`init` 프로퍼티** | 대입 자리가 못 박힌다((8)) |
| 반드시 채워져야 한다 | ★ **`required`** | 생성자를 안 늘리고 강제한다((7)) — 단 **컴파일 시간만** |
| 매개변수를 필드에 넣기만 한다 | ★ **기본 생성자(C# 12)** | 줄이 준다 — 단 **`readonly` 를 잃는다**((6)) |
| 불변까지 원한다 | ★★ **`class C(string n) { private readonly string _n = n; }`** | 기본 생성자로 받고 **직접 `readonly` 필드에 담는다** |
| 기반에 초기화 훅을 두고 싶다 | ★★★ **두지 않는다** | 생성자 속 가상 호출은 **절반만 채워진 상태**를 본다((4)) |
| 그래도 훅이 필요하다 | **생성이 끝난 뒤 부르는 `Initialize()`** 또는 **`sealed`** | 가상 디스패치를 안 타거나 재정의를 막는다 |

- ★ **「기본 생성자로 다 바꾸자」가 아니다.** (6)이 잰 것은 **필드 하나가 `readonly` 를 잃는다**는 것이고,\
  그것이 **불변 설계에서는 비용**이다.

## 핵심 문장

- **C# 의 초기화 순서는 파생 필드 초기자 → 기반 필드 초기자 → 기반 본문 → 파생 본문**이다.
- **C++ 와 정확히 맞바뀌는 자리는 「파생의 초기자가 어디로 가느냐」 하나**다.
- **생성자에서 가상 메서드를 부르면 C# 은 파생 것을 부르고, C++ 은 기반 것을 부른다** — **둘 다 안 된다.**
- **`this()` 위임에서 필드 초기자는 한 번만** 돌고, **`base()` 는 안 적어도 불린다.**
- **생성자를 하나라도 적으면 기본 생성자가 사라진다.**
- **`required` 는 컴파일러가 보는 것이고, `readonly` 는 참조만 고정한다.**
- **기본 생성자(C# 12)가 줄이는 것은 소스 줄이고, 잃는 것은 `readonly`** 다.

## 관련 자료

- ★★★ C++ 갈래 목록([`cpp/syntax/README.md`](../../../cpp/syntax/README.md))의 **13번**([`13-constructors-member-init-list-and-delegating/`](../../../cpp/syntax/13-constructors-member-init-list-and-delegating/)) — **직접 대비.**\
  ★ **한 클래스 안의 선언 순서 규칙**은 거기가 정본이고(그쪽 (2)), **여기 (1)은 「기반 ↔ 파생」 축을 새로 잰 것**이다.
- C++ 갈래의 **14번**([`14-destructors-and-deterministic-destruction/`](../../../cpp/syntax/14-destructors-and-deterministic-destruction/)) — **파괴 쪽 대비.**\
  ★ **C++ 은 스코프를 벗어나면 끝**이고, **C# 은 GC 가 언제 치울지 모른다** — 그 틈을 `IDisposable`/`using` 이 메운다(목록의 **37번 주제**).
- [01번](../01-value-types-and-reference-types/) — **값 타입과 참조 타입.** 위 대비의 토대다.
- [11번](../11-collection-initializers-and-collection-expressions/) — **객체 초기화자는 생성자가 끝난 뒤** 돈다. (1)의 순서가 거기서 이어진다.
- 목록의 **13번 주제** — 속성(property)의 전모. (5)는 **무엇이 필드가 되나**까지다.
- 목록의 **16번 주제** — 상속과 `virtual`/`override`. (4)의 **설계 판**이 거기다.
- 목록의 **15번 주제** — 접근 한정자. (5)의 `public`/`private` 선택이 거기가 정본이다.
- 목록의 **18번 주제** — `record`. **생성자·동등성·`with` 를 한꺼번에 주는 길**이다.
- [`oop-basics/`](../../../../oop-basics/) — 클래스·캡슐화 개념. 여기는 **C# 문법**이다.

## 용어 풀이

> **필드 초기자(field initializer)** — 필드 선언에 붙인 초기값.\
> 예: `public int Tag = 1;` — ★ **기반 클래스보다도 먼저** 돈다((1)).

> **생성자 연쇄(constructor chaining)** — `: this(…)` 나 `: base(…)` 로 다른 생성자를 먼저 돌리는 것.\
> 예: `Two(int seed) : this()` — ★ **위임받은 쪽이 먼저 끝난다**((2)).

> **암묵 `base()`** — 생성자에 `: base(…)` 를 안 적으면 **매개변수 없는 기반 생성자**가 불린다.\
> 예: 기반에 그것이 없으면 **`CS7036`** 이다((3)).

> **기본 생성자(default constructor)** — 생성자를 하나도 안 적었을 때 컴파일러가 주는 매개변수 없는 생성자.\
> 예: 하나라도 적으면 **사라진다**((8)).

> **기본 생성자(primary constructor)** — 클래스 이름 뒤 괄호로 받는 매개변수(C# 12).\
> 예: `class Savings(string id) : Account(id)` — ★ **본문에서 쓰면 숨은 필드가 생기고 `readonly` 가 아니다**((6)).\
> ★★ 위의 default constructor 와 **한국어 이름이 겹친다** — 이 문서는 **괄호 안 영어로 가른다.**

> **`readonly` 필드** — 생성자·`init` setter·필드 초기자에서만 대입되는 필드.\
> 예: `readonly int[] a` 는 **`a` 를 바꾸는 것만 막고 `a[0]` 은 못 막는다**((9)).

> **`required` 멤버(C# 11)** — 객체를 만들 때 **반드시 채워야** 하는 프로퍼티·필드.\
> 예: 안 채우면 **`CS9035`**. ★ **리플렉션 생성은 지나간다**((7)).

> **자동 구현 속성(auto-implemented property)** — `{ get; set; }`. 컴파일러가 **숨은 필드**를 만든다.\
> 예: `<Auto>k__BackingField`((5)).

> **식 본문 속성(expression-bodied property)** — `=> 식`. **저장소가 없다.**\
> 예: `public int Doubled => Fixed * 2;` — 필드 목록에 없다((5)).

> **`RuntimeHelpers.GetUninitializedObject`** — **생성자를 안 돌리고** 객체를 만드는 API.\
> 예: `required` 를 **그대로 지나간다**((7)). 직렬화기가 쓰는 길이다.

## 더 들어가면

- **`record` 와 기본 생성자** — `record` 의 위치 매개변수는 **`init` 프로퍼티**가 되어 (6)의 `readonly` 문제가 없다.\
  정본은 목록의 **18번 주제**.
- **정적 생성자(`static` constructor)** — 타입마다 한 번 도는 초기화. **언제 도는지가 미묘하다**(`beforefieldinit`).\
  이 문서는 **인스턴스 쪽만** 던졌다.
- **`init` 전용 setter(C# 9)** — 객체 초기화자까지만 쓸 수 있는 setter. (5)의 `Owner` 가 그 예다.
- **구조체의 생성자** — `struct` 는 규칙이 다르다(필드 초기자 제약·`default` 생성). 정본은 [02번](../02-struct-vs-class-choosing/).
