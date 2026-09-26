# csharp/syntax/12 — 클래스·필드·생성자·`this`/`base` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 이 주제의 질문은 **번호 매긴 줄의 순서를 맞히는 것**이 절반이다 —
> 「기반이 먼저」로 뭉개지 말고 **1·2·3·4 에 무엇이 오는지**를 적어라.
> **환경** — .NET SDK 10.0.401 · 런타임 10.0.12 · `net10.0` · linux-x64 ·
> Roslyn `csc` 를 직접 부른다 · `-langversion:latest` · `-preferreduilang:en-US` · **`-debug` 없음**.
> C++ 대비는 **g++ 13.3.0 · `-std=c++20`** 이다.
> ★★ **네 번째 창은 「예외 전문」이다**(5번) — 스택 프레임이 **누가 누구를 불렀나**를 적는다.
> ★ **「부적용인 창」이 있다** — **할당 바이트**. 필드 초기자를 쓰든 본문에서 대입하든
> **같은 객체 하나**가 만들어진다. **「안 쟀다」가 아니라 「잴 것이 없다」다.**
> 선행 — [01번](../01-value-types-and-reference-types/)(값/참조)·[11번](../11-collection-initializers-and-collection-expressions/)(객체 초기화자는 생성자 뒤).
> 대비 — C++ 갈래 목록([`cpp/syntax/README.md`](../../../cpp/syntax/README.md))의 **13번**([`13-constructors-member-init-list-and-delegating/`](../../../cpp/syntax/13-constructors-member-init-list-and-delegating/))·**14번**([`14-destructors-and-deterministic-destruction/`](../../../cpp/syntax/14-destructors-and-deterministic-destruction/)).

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (예측) / (왜) / (경계) / (연결) -->

### 1. ★★★ 네 줄에 번호가 어떻게 붙나 (예측)

```csharp
// cs12b-order.cs
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
```

- **1·2·3·4 에 무엇이 오는지** 네 줄 전부 맞힐 수 있는가?
- ★★★ 끝 줄의 **`Tag`** 와 **`BaseTag`** 값은 각각 얼마인가?
- ★ `: base()` 를 지우면 출력이 달라지는가?

### 2. ★★★ 같은 모양을 C++ 로 던지면 (예측)

```cpp
// cs12b-cpp-order.cpp
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
```

- **1·2·3·4 의 순서**가 1번과 **어디서 갈리는가**?
- ★★★ `tag` 와 `baseTag` 값은 각각 얼마인가?
- ★★ 두 언어가 **각각 무엇을 지키려다** 이렇게 갈렸는지 한 줄로 말할 수 있는가?
- ★ **한 클래스 안의 선언 순서 규칙**은 어느 주제가 정본인가 — 그 주제가 **상속을 다루었는가**?

### 3. ★★ `this()` 로 위임하면 (예측)

```csharp
// cs12b-this.cs
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
```

- `new Two(7)` 에서 **`★ 필드 초기자` 줄이 몇 줄** 찍히는가?
- ★ `Two() 본문` 과 `Two(int) 본문` 중 **먼저 찍히는 것**은?
- ★ 끝의 `Seed` 는 얼마인가 — **왜** 그 값인가?
- ★★ C++ 의 위임 생성자와 **순서가 같은가 다른가**?

### 4. ★★★ 기반 생성자에서 가상 메서드를 부르면 (예측)

```csharp
// cs12b-virtual.cs
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
```

- `Describe()` 는 **기반 것이 불리는가 파생 것이 불리는가**?
- ★★★ 그때 **`FromInitializer`·`FromBody`·`Len`** 은 각각 무엇인가?
- ★★ 그 결과를 **1번의 순서**로 설명할 수 있는가?
- ★★★ 같은 프로그램을 C++ 로 던지면 **어느 함수가 불리는가** — 그때 파생 멤버는?

### 5. ★★ 널을 안 견디게 만들면 (예측)

```csharp
// cs12b-nre.cs
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
```

- **예외 타입**은 무엇이고 **`run exit`** 은 얼마인가?
- ★★★ 스택 프레임 **세 줄**을 위에서부터 적을 수 있는가?
- ★ `cc exit` 은 얼마인가 — 컴파일러가 뭐라고 했는가?
- ★ `_given` 이 `readonly` 인데도 널인 이유는?

### 6. ★★ 기본 생성자(C# 12)가 만드는 것 (예측)

```csharp
// cs12b-primary.cs
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
```

- 네 클래스가 각각 **어떤 필드**를 갖는가 — **`readonly` 인 것**은 어느 것인가?
- ★★★ 기본 생성자 매개변수를 **본문에서 고칠 수 있는가**?
- ★★ **`base` 에만 넘기는** 클래스에는 필드가 생기는가?
- ★ IL 로 보면 손으로 쓴 판과 **무엇이 다른가**?

### 7. ★ 컴파일러가 막아 주는 것 (경계)

- `: base()` 를 **한 글자도 안 적었는데** 에러가 나는 경우가 있는가 — 진단 코드는?
- ★★ `this()` 연쇄가 **자기 자신으로 돌아오면** 어떻게 되는가 — C++ 의 위임 재귀와 어떻게 다른가?
- ★ **기본 생성자(default constructor)는 언제 사라지는가** — 무엇이 그것을 증명하는가?
- ★★ `required` 를 안 채우면 **빠진 멤버마다** 진단이 나는가, **한 건**만 나는가?
- ★ `readonly` 필드에 밖에서 대입하면 진단 문구가 **어디를 예외로 적는가**?

### 8. ★ 필드·프로퍼티·`required` 의 경계 (경계)

- 자동 구현 속성은 **숨은 필드 이름**이 무엇인가 — 식 본문 속성은 **저장소가 있는가**?
- ★★ 채운 적 없는 공개 필드에 **경고가 나는가** — 코드는?
- ★★★ `required` 를 **리플렉션으로 건너뛸 수 있는가** — 그 흔적은 어디에 남는가?
- ★ `readonly int[]` 의 **원소를 바꿀 수 있는가**?

### 9. ★★ 경고를 누가 보나 (경계)

- 생성자 주변 함정 여섯을 심고 `-warn:9` 로 물으면 **몇 건**이 나오는가?
- ★★★ 이 주제에서 컴파일러가 **보는 것**과 **안 보는 것**을 한 줄씩으로 가를 수 있는가?
- ★ 이 주제에서 유일한 「**경고**」는 무엇인가(나머지는 에러이거나 침묵이다)?

### 10. 다른 주제와 잇기 (연결)

- **C++ 의 초기화 리스트**와 대비되는 주제는 어느 갈래 몇 번인가?
- ★★ **결정적 파괴 ↔ GC** 의 대비는 어느 갈래 몇 번이고, C# 은 그 틈을 **무엇으로** 메우나?
- **객체 초기화자가 생성자 뒤에 돈다**는 실측은 몇 번 주제인가?
- **상속과 `virtual`/`override` 의 설계 판**은 몇 번 주제인가?
- **속성의 전모**는 몇 번, **`record`** 는 몇 번인가?
- ★ `struct` 의 생성자 규칙이 다른 것은 몇 번 주제인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
