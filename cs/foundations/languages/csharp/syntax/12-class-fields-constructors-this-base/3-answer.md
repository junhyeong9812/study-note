# csharp/syntax/12 — 클래스·필드·생성자·`this`/`base` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·진단·IL 은 **.NET SDK 10.0.401** · 런타임 **10.0.12** · 타겟 **`net10.0`** ·
> **linux-x64** 에서 실제로 돌려 얻은 것이다(2026-09-25). C++ 대비는 **g++ 13.3.0 · `-std=c++20`** 이다.\
> 진단은 **`-preferreduilang:en-US`** 로 영어로 고정했고, **`-debug` 를 안 줘** 트레이스에 경로·줄 번호가 안 박힌다.\
> ★ 블록은 캡처 스크립트가 파일로 받아 조립기가 끼워 넣은 것이다 — 손으로 옮긴 줄은 없다.
> **읽는 법** — **진단 문구**와 **숨은 필드 이름의 형식**은 흔들리는 칸이다.\
> 근거로 쓰는 것은 **로그 순서와 번호 · 진단 코드와 `(행,열)` · 예외 타입과 스택 프레임 이름 ·\
> 숨은 필드가 있다는 사실 · `cc exit`/`run exit`** 다.
> ★★★ **이 문서는 시간을 재지 않았다.** 「몇 배 빠르다」는 문장이 **한 줄도 없다**.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ **파생 필드 초기자가 1번**이다 — `Tag=1` · `BaseTag=2`

**출력**

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

**왜 그런가**

```text
   new Derived()

   1. Derived 의 필드 초기자      <- ★★★ 제일 먼저
   2. Base 의 필드 초기자
   3. Base 의 생성자 본문
   4. Derived 의 생성자 본문
```

- ★★★ **파생의 필드 초기자가 기반보다도 먼저** 돈다. 그래서 `Tag=1`, `BaseTag=2` 다.
- ★★ **C# 은 「내 필드 초기자는 남의 코드가 돌기 전에」를 지킨다.**\
  기반 생성자가 무슨 짓을 하든 **파생 필드는 이미 채워져 있다** — 4번이 그 결과다.
- ★ **`: base()` 를 지워도 출력은 같다.** **암묵으로 불리기** 때문이다(7번).

### 2. ★★★ C++ 는 **파생 멤버 초기자가 3번**이다 — 정확히 맞바뀐다

**출력**

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

**왜 그런가**

| 단계 | C++ (g++ 13.3.0) | C# (.NET 10) |
|---|---|---|
| 1 | **기반의 멤버 초기자** | ★★★ **파생의 필드 초기자** |
| 2 | **기반의 생성자 본문** | **기반의 필드 초기자** |
| 3 | ★★★ **파생의 멤버 초기자** | **기반의 생성자 본문** |
| 4 | **파생의 생성자 본문** | **파생의 생성자 본문** |
| 찍힌 값 | `baseTag = 1` · `tag = 3` | `BaseTag = 2` · `Tag = 1` |

- ★★★ **갈리는 것은 「파생의 초기자가 어디로 가느냐」 하나**다. 나머지 셋의 **상대 순서는 같다.**
- ★★ **각 언어가 지키려는 것이 다르다.**\
  C++ 은 「**기반이 완성된 뒤에 파생을 짓는다**」, C# 은 「**내 필드 초기자는 남의 코드보다 먼저**」다.
- ★ **한 클래스 안의 선언 순서 규칙**은 C++ 갈래 [13번](../../../cpp/syntax/13-constructors-member-init-list-and-delegating/) (2)가 정본이다\
  (「**리스트에 적은 순서가 아니라 선언 순서**」 · `-Wreorder` 경고 **g++ 3건 · clang 1건**).\
  ★★ **그 주제는 상속을 다루지 않았다** — 그래서 **기반 ↔ 파생 축은 이 문서에서 새로 쟀다.**

### 3. ★★ 필드 초기자는 **한 줄**만 찍힌다 — `Seed` 는 **7**

**출력**

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

**왜 그런가**

```text
   new Two(7)                      new Two()

   1. ★ 필드 초기자   <- 한 번       1. ★ 필드 초기자
   2. Two() 본문                    2. Two() 본문
   3. Two(int) 본문                 (끝)
```

- ★★★ **`★ 필드 초기자` 는 한 줄뿐**이다. **`this(…)` 로 위임하는 생성자는 필드 초기자를 돌리지 않고**,\
  **연쇄의 끝**(`base` 로 가는 쪽)에서 **한 번만** 돈다.
- ★★ **`Two() 본문` 이 먼저**다 — 위임받은 쪽이 끝나고 나서 내 본문이 돈다.\
  그래서 `Seed` 가 `-1` 로 채워졌다가 **7 로 덮인다.**
- ★★ **C++ 의 위임 생성자와 순서가 같다** — [13번](../../../cpp/syntax/13-constructors-member-init-list-and-delegating/) (4)도 **본체가 먼저, 위임한 쪽 본문이 나중**이었다.\
  ★ **반대인 것은 1번·2번의 「기반 ↔ 파생」 축 하나뿐**이다.

### 4. ★★★ **파생 것이 불린다** — 그리고 절반만 채워진 상태를 본다

**출력 — C#**

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

**출력 — 같은 프로그램을 C++ 로**

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

**왜 그런가**

| | C# | C++ |
|---|---|---|
| 가상 호출이 가는 곳 | ★★★ **파생 것**(`Child.Describe`) | ★★★ **기반 것**(`Parent::describe`) |
| 그때 파생 초기자는 | ★ **이미 돌았다**(1번의 1단계) | ★ **아직 안 돌았다**(2번의 3단계) |
| 보이는 것 | `FromInitializer` **값 있음** · `FromBody` **null** · `Len` **0** | 파생 상태를 **아예 안 본다** |
| 터지나 | ★★ **`NullReferenceException` 이 날 수 있다**(5번) | **안 난다** |

- ★★★ **C# 은 기반 생성자가 도는 중인데 가상 디스패치가 이미 파생을 가리킨다.**\
  그래서 **파생 코드가 미완성 상태를 본다** — `FromBody` 가 `null`, `Len` 이 `0` 이다.
- ★★★ **1번의 순서가 그대로 값으로 나온다.** `FromInitializer` 만 값이 있는 이유는\
  **파생 필드 초기자가 1단계에서 이미 돌았기 때문**이다.
- ★★★ **C++ 는 정반대 방식으로 위험하다** — **파생 함수가 아예 안 불린다.**\
  `describe() → Parent::describe (기반 버전)` 이다. **의도한 동작이 조용히 사라진다.**
- ★ **C++ 쪽 `len=14`** 는 UTF-8 **바이트 수**이고 C# 의 `Len=6` 은 UTF-16 **코드 단위 수**다.\
  **이 주제와 무관한 차이**이므로 근거로 쓰지 않는다.

### 5. ★★ `NullReferenceException` · `run exit=134` · **`cc exit=0`**

**출력**

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

**왜 그런가**

```text
   at Child.Describe()              <- ★ 파생 것이 불렸다
   at Parent..ctor()                <- ★ 기반 생성자가 그것을 불렀다
   at Child..ctor(String given)     <- ★ 파생 생성자는 아직 본문에 못 들어갔다
   at Program.<Main>$(String[] args)
```

- ★★★ **스택 세 줄이 「누가 누구를 불렀나」를 그대로 적는다.** 4번의 결론이 **값이 아니라 프레임으로** 증명된다.
- ★★ **`run exit=134`**(= 128 + SIGABRT)이고 **`cc exit=0`** 이다 —\
  **컴파일러는 한 마디도 안 했다**(9번의 탐침에서 이 자리가 **0건**이다).
- ★★ **`_given` 이 `readonly` 인데도 널**이다. `readonly` 는 「**생성자에서만 대입**」을 말하지\
  「**생성자가 끝나기 전에도 값이 있다**」를 말하지 않는다. 그 대입은 **4단계**에서 일어난다.
- ★ **`-debug` 를 안 줬으므로** 트레이스에 **경로도 줄 번호도 없다** — 어느 머신에서 돌려도 같다.

### 6. ★★ 본문에서 쓰면 **숨은 필드**가 생기고, 그것은 **`readonly` 가 아니다**

**출력**

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

**IL**

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

**왜 그런가**

| 클래스 | 만들어진 필드 | `readonly` |
|---|---|---|
| `UsedInBody(string name)` — 본문에서 쓴다 | `String <name>P` | ★★★ **아니다** |
| `OnlyToProperty(string name)` — 프로퍼티에만 | `<Name>k__BackingField` | ★ **맞다** |
| `OnlyToBase(string name)` — `base` 에만 | ★★★ **없다** | — |
| `Classic` — 손으로 쓴 판 | `_name` | ★ **맞다** |

- ★★★ **기본 생성자 매개변수를 본문에서 고칠 수 있다** — `Bump()` 가 `이름` → `이름!` 로 바꿨다.\
  **숨은 필드 `<name>P` 가 `readonly` 가 아니기** 때문이다. **손으로 쓴 `Classic._name` 은 `readonly`** 다.
- ★★★ **`base` 에만 넘기면 필드가 아예 안 생긴다** — `OnlyToBase` 의 필드 목록에 **기반의 `Tag` 밖에 없다.**\
  **쓰이지 않으면 저장하지 않는다.**
- ★★ **IL 은 손으로 쓴 판과 한 글자도 같다** — `ldstr` → `ldfld` → `Concat` → `ret`.\
  **`ldfld` 대상 이름만 다르다**(`UsedInBody::<name>P` 대 `Classic::_name`).\
  호출 쪽도 `newobj UsedInBody::.ctor` 한 줄이다 — **런타임에 아무것도 아니다.**
- ★ **그래서 「줄이 준다」가 값이고 「`readonly` 를 잃는다」가 대가**다.\
  불변을 원하면 `class C(string n) { private readonly string _n = n; }` 로 **직접 담으면 된다.**

### 7. ★ `CS7036` · `CS0768` · `CS9035` · `CS0191` 넷이 막는다

**출력 — 암묵 `base()` 와 `this()` 순환**

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

**출력 — 기본 생성자·`required`·`readonly`**

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

**왜 그런가**

| 심은 것 | 진단 | 뜻 |
|---|---|---|
| `class D1 : B1` — 기반에 매개변수 없는 생성자가 없다 | ★★★ **`CS7036`** | **`: base()` 를 안 적어도 부르려 한다** |
| `C1() : this(1)` 과 `C1(int) : this()` | ★★ **`CS0768`** | `Constructor 'C1.C1(int)' cannot call itself through another constructor` |
| `new HasCtor()` — 생성자를 적은 클래스 | ★★★ **`CS7036`** | **기본 생성자가 사라졌다** |
| `new Conf()` — `required` 둘 다 빠뜨림 | ★★ **`CS9035` ×2** | ★ **빠진 멤버마다 한 건** |
| `e.Fixed = 9;` | ★★ **`CS0191`** | 아래 문구 |

- ★★★ **`: base()` 를 한 글자도 안 적었는데 `CS7036`** 이다 — **암묵으로 불린다는 증거**다.\
  `class D2 : B2` 쪽은 기반에 매개변수 없는 생성자가 **있어서** 조용하다.
- ★★★ **`this()` 순환은 `CS0768` 로 컴파일에서 막힌다.**\
  ★ **C++ 의 위임 재귀(`A() : A() {}`)는 UB** 다 — **C# 이 컴파일 시간으로 끌어올린 자리**다.
- ★★★ **기본 생성자는 「생성자를 하나라도 적는 순간」 사라진다.**\
  `class NoCtor { public int X = 0; }` 은 `new NoCtor()` 가 되고, `HasCtor` 는 **`CS7036`** 이다.
- ★★ **`CS9035` 는 빠진 멤버마다** 난다 — `new Conf()` 에서 **두 건**, 이름까지 적는다.
- ★★ **`CS0191` 의 문구가 규칙 전부를 적는다** —\
  `except in a constructor or init-only setter of the type in which the field is defined or a variable initializer`.\
  **쓸 수 있는 자리가 셋으로 못 박혀 있다.**

### 8. ★ 자동 속성은 숨은 필드, 식 본문 속성은 **저장소가 없다** — `required` 는 **지나갈 수 있다**

**출력 — 필드와 프로퍼티**

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

**출력 — `required`**

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

**왜 그런가**

| 적은 것 | 숨은 필드 | 메서드 |
|---|---|---|
| `public int Untouched { get; set; }` | `<Untouched>k__BackingField` | `get_`·`set_` |
| `public int Auto { get; set; } = 3;` | `<Auto>k__BackingField` | `get_`·`set_` |
| `public int Doubled => Fixed * 2;` | ★★★ **없다** | `get_` 만 |
| `public string Text;` | `Text` | — |

- ★★ **채운 적 없는 공개 필드에 경고가 난다** — **`CS0649`**,\
  `Field 'Sample.Text' is never assigned to, and will always have its default value null`.\
  ★ 이 주제에서 유일한 「**경고**」다(9번).
- ★★★ **`required` 를 리플렉션으로 건너뛸 수 있다.** `RuntimeHelpers.GetUninitializedObject` 로 만들면\
  **`Host=null · Port=0`** 인 객체가 **아무 저항 없이** 나온다.
- ★★ **흔적은 메타데이터에 남는다** — `RequiredMemberAttribute` 가 타입에 **박혀 있다**(`True`).\
  **런타임이 그것을 강제하지 않을 뿐**이다. `[SetsRequiredMembers]` 를 단 생성자는 **정상 경로**다.
- ★★ **`readonly int[]` 의 원소는 바꿀 수 있다** — `readonly` 는 **참조만 고정한다**(9번의 탐침 넷째).

### 9. ★★ **0건** — 컴파일러는 「형태」를 막고 「순서」를 하나도 안 막는다

**출력**

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

**왜 그런가**

| 심은 것 | 진단 | 실제로는 |
|---|---|---|
| 기반 생성자에서 가상 메서드 호출 | **0** | ★★★ 파생 것이 불린다(4번) |
| 생성자 본문이 채우는 필드 | **0** | 그 시점에 **null** |
| `Describe()` 가 그 필드를 읽는다 | **0** | ★★★ **`NullReferenceException`**(5번) |
| `readonly` 배열의 내용 변경 | **0** | `readonly` 는 **참조만** 고정한다 |
| 초기화 순서에 기댄 계산 | **0** | 이 판에서는 맞다 — 순서를 바꾸면 깨진다 |
| `this()` 연쇄 | **0** | 정상(순환이면 `CS0768`) |

- ★★★ **탐침 여섯 중 답한 것 0 · 침묵한 것 6**이다. **`-warn:9` 에서도 `cc exit=0` 에 진단 0줄**이다.
- ★★★ **가르는 한 줄** — 컴파일러가 보는 것은 「**형태**」(기본 생성자가 없다·`required` 가 비었다·`readonly` 에 대입했다)이고,\
  안 보는 것은 「**순서 때문에 생기는 사고**」(가상 호출·미완성 상태·`readonly` 배열)다.
- ★ **유일한 「경고」는 `CS0649`** 다(8번). 나머지는 전부 **에러이거나 침묵**이다.

### 10. 다른 주제와 잇기

- **C++ 의 초기화 리스트**와 대비되는 주제는\
  C++ 갈래 목록([`cpp/syntax/README.md`](../../../cpp/syntax/README.md))의 **13번**([`13-constructors-member-init-list-and-delegating/`](../../../cpp/syntax/13-constructors-member-init-list-and-delegating/))이다.\
  ★ **한 클래스 안의 선언 순서**는 거기가 정본이고, **기반 ↔ 파생 축은 여기 1번·2번**이다.
- ★★ **결정적 파괴 ↔ GC** 의 대비는 C++ 갈래의 **14번**([`14-destructors-and-deterministic-destruction/`](../../../cpp/syntax/14-destructors-and-deterministic-destruction/))과 [01번](../01-value-types-and-reference-types/)이다.\
  ★ **C++ 은 스코프를 벗어나면 끝**이고 **C# 은 GC 가 언제 치울지 모른다** —\
  그 틈을 **`IDisposable`/`using`**(목록의 **37번 주제**)이 메운다.
- **객체 초기화자가 생성자 뒤에 돈다**는 실측은 [11번](../11-collection-initializers-and-collection-expressions/) (1)이다 —\
  IL 의 `newobj` → `dup` → `set_…` 가 그 증거였다.
- **상속과 `virtual`/`override` 의 설계 판**은 목록의 **16번 주제**다. 4번의 처방(훅을 두지 않는다·`sealed`)이 거기로 이어진다.
- **속성의 전모는 13번**, **`record` 는 18번 주제**다. `record` 의 위치 매개변수는 `init` 프로퍼티가 되어\
  **6번의 `readonly` 문제가 없다.**
- ★ **`struct` 의 생성자 규칙**은 [02번](../02-struct-vs-class-choosing/)이 정본이다 — 필드 초기자 제약이 다르다.

## 실행 검증

| 무엇 | 몇 번·어디서 | 결과 |
|---|---|---|
| `cs12b-order.cs` 초기화 순서 | csc 1회 | ★★★ **파생 초기자 → 기반 초기자 → 기반 본문 → 파생 본문** · `Tag=1` `BaseTag=2` |
| `cs12b-cpp-order.cpp` C++ 대비 | g++ 1회 | ★★★ **기반 초기자 → 기반 본문 → 파생 초기자 → 파생 본문** · `tag=3` `baseTag=1` |
| `cs12b-this.cs` `this()` 위임 | csc 1회(2판) | ★★★ 필드 초기자 **1회** · 위임받은 쪽이 **먼저** |
| `cs12b-virtual.cs` 가상 호출 | csc 1회 | ★★★ **파생 것이 불린다** · `FromBody=null` · `Len=0` |
| `cs12b-cpp-virtual.cpp` C++ 대비 | g++ 1회 | ★★★ **기반 것이 불린다**(`Parent::describe`) |
| `cs12b-nre.cs` 예외 전문 | csc 1회 | ★★★ `NullReferenceException` · **`cc exit=0` · `run exit=134`** · 프레임 3줄 |
| `cs12b-primary.cs` 기본 생성자 | csc 1회(4타입) | ★★★ `<name>P` 는 **`readonly` 아님** · `base` 전용은 **필드 없음** |
| `cs12b-il-primary.cs` IL | csc 1회(4메서드) | ★★ 손으로 쓴 판과 **이름만 다르다** |
| `cs12b-implicit.cs` 암묵 `base()` | csc 1회 | **에러 2건** — `CS7036` · `CS0768` |
| `cs12b-diag.cs` 진단 넷 | csc 1회 | **에러 5건** — `CS7036` · `CS9035` ×3 · `CS0191` |
| `cs12b-required.cs` `required` | csc 1회 | ★★★ `GetUninitializedObject` 로 **`Host=null` `Port=0`** · 특성은 **박혀 있다** |
| `cs12b-field-prop.cs` 필드·프로퍼티 | csc 1회 | ★★ 숨은 필드 넷 · 식 본문 속성은 **저장소 없음** · **`CS0649` 1건** |
| `cs12b-quiet.cs` 탐침 여섯 | csc 1회(`-warn:9`) | ★★★ **진단 0줄 · `cc exit=0`** |
| `cs12b-form.cs` 형태 | csc 1회 | 일곱 꼴이 전부 컴파일·실행됐다 |

**구현 의존 항목** — 다음은 **이 판(.NET SDK 10.0.401 · 런타임 10.0.12 · linux-x64 · g++ 13.3.0)에서만** 그렇다.

- ★★ **숨은 필드 이름의 형식**(`<name>P` · `<Auto>k__BackingField`) — Roslyn 이 정한다.
- ★★ **`base` 에만 넘기면 필드가 안 생기는 최적화** — 명세가 요구한 것이 아니다.
- ★ **진단 문구 전부** · **스택 트레이스의 프레임 표기**(`at Parent..ctor()`) · **`run exit=134`**(SIGABRT).
- ★ **C++ 쪽 `len=14`** — UTF-8 바이트 수라 **소스 인코딩에 달려 있다.** 근거로 쓰지 않았다.

**언어가 보장하는 것**(구현이 바뀌어도 같다)

- **파생 필드 초기자 → 기반 필드 초기자 → 기반 생성자 본문 → 파생 생성자 본문** 순서.
- **`: base()` 가 암묵으로 불리는** 것.
- **`this(…)` 위임에서 필드 초기자가 한 번만 도는** 것.
- **생성자를 하나라도 적으면 기본 생성자가 사라지는** 것.
- **생성자에서 부른 가상 메서드가 파생 것으로 디스패치되는** 것.
- **`readonly` 가 생성자·`init` setter·필드 초기자에서만 대입되는** 것(그리고 **참조만 고정하는** 것).
- **`required` 를 컴파일러가 검사하는** 것(그리고 **런타임이 강제하지 않는** 것).

**안 돌려 본 것 / 못 잰 것**

- **안 돌려 본 것** — ★ **`struct` 판**(필드 초기자 제약이 다르다 — [02번](../02-struct-vs-class-choosing/)) ·\
  ★ **정적 생성자(`static` constructor)와 `beforefieldinit`** · ★ **`record` 의 위치 매개변수 판** ·\
  ★ **`-langversion:10` 이하**(기본 생성자가 없는 판에서 진단이 어떻게 나오는지) ·\
  ★ **`-debug` 를 준 판**(트레이스에 줄 번호가 붙는다) · ★ **clang 으로 C++ 대비 두 건**(g++ 로만 쟀다) ·\
  ★ **상속이 3단 이상인 판**(2단만 쟀다).
- **못 잰 것** — ★★★ **「필드 초기자와 생성자 본문 대입 중 무엇이 더 싼가」.**\
  ★ C++ 쪽은 [13번](../../../cpp/syntax/13-constructors-member-init-list-and-delegating/) (1)이 **생성자·대입 호출 횟수로 1 대 2** 를 셌는데,\
  **C# 에는 그 계수가 성립하지 않는다** — 필드 대입은 **호출이 아니라 `stfld` 한 줄**이라 셀 대상이 없다.\
  **재려면 벤치마크 하네스가 따로 필요하다.**
- ★ 「**부적용인 창**」 — **할당 바이트.** 필드 초기자를 쓰든 본문에서 대입하든 **같은 객체 하나**가 만들어진다.\
  기본 생성자(C# 12)도 **필드 개수가 손으로 쓴 판과 같다**(6번). **「안 쟀다」가 아니라 「잴 것이 없다」다.**

**버전이 올랐을 때 다시 돌려야 하는 것**

- ★★ **6번의 숨은 필드 이름과 `base` 전용 최적화** — Roslyn 이 바꾸면 움직인다.
- ★★ **9번의 탐침 여섯이 계속 0건인지** — 컴파일러가 「생성자에서 가상 메서드」를 경고하기 시작할 수 있다.
- ★ **5번의 스택 프레임 표기** — 런타임이 바꾸면 움직인다.
- ★ **1번·2번의 순서** — **명세가 정한 것이라 바뀔 일이 없다.** 바뀌면 그것이 뉴스다.
