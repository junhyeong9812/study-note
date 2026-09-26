# csharp/syntax/16 — 상속·`virtual`/`override`/`abstract`/`sealed`/`new` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> ★★★ 이 주제의 질문은 「**정적 타입 × 동적 타입 격자를 채울 수 있나**」가 절반이다 —
> 「파생 것이 불린다」로 뭉개지 말고 **네 줄 각각에 무엇이 나오는지** 적어라.
> **환경** — .NET SDK 10.0.401 · 런타임 10.0.12 · `net10.0` · linux-x64 ·
> Roslyn `csc` 를 직접 부른다 · `-langversion:latest` · `-preferreduilang:en-US`.
> 대비는 **javac 21.0.5** 와 **g++ 13.3.0 · `-std=c++20`** 이다.
> ★★★ **본체 창은 ① IL 덤프다** — 4번의 「기본 비가상인데 왜 `callvirt` 인가」는
> **덤프 없이는 물을 수조차 없다.**
> ★★ **짝이 되는 것은 실행 출력 격자**다 — IL 만 보면 「`callvirt` 니까 다 가상」이라는 **틀린 결론**이 나온다.
> ★ **「부적용인 창」이 있다** — **④ 할당 바이트.** `new` 로 숨기든 `override` 하든 **객체는 하나**이고
> `virtual` 을 붙인다고 객체가 커지지도 않는다(메서드 테이블은 **타입당 하나**).
> **「안 쟀다」가 아니라 「잴 것이 없다」다.**
> ★★★ **이 파일에는 「가상 호출이 느리다」는 문장이 없다** — 이 판에서 **안 쟀다.**
> 선행 — [12번](../12-class-fields-constructors-this-base/)(★ **생성자 속 가상 호출**이 거기 정본이다)·[15번](../15-access-modifiers-and-assembly-boundary/)(`protected`).
> 대비 — Java 갈래 목록([`java/syntax/README.md`](../../../java/syntax/README.md))의 **09번**([`09-inheritance-overriding/`](../../../java/syntax/09-inheritance-overriding/))·**11번**([`11-interfaces-default-methods/`](../../../java/syntax/11-interfaces-default-methods/)) ·
> C++ 갈래 목록([`cpp/syntax/README.md`](../../../cpp/syntax/README.md))의 **19번**.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (예측) / (왜) / (경계) / (연결) -->

### 1. ★★★ 네 줄에 무엇이 찍히나 (예측)

```csharp
// cs16b-grid.cs
using System;

class Base {
    public         string Plain()  => "Base.Plain";
    public virtual string Virt()   => "Base.Virt";
}
class Derived : Base {
    public new      string Plain() => "Derived.Plain";   // new — 숨긴다
    public override string Virt()  => "Derived.Virt";    // override — 재정의한다
}

class Program {
    static void Main() {
        Base    b  = new Base();
        Base    bd = new Derived();     // 정적 Base · 동적 Derived
        Derived d  = new Derived();
        Console.WriteLine($"정적 Base    · 동적 Base    : Plain={b.Plain(),-14} Virt={b.Virt()}");
        Console.WriteLine($"정적 Base    · 동적 Derived : Plain={bd.Plain(),-14} Virt={bd.Virt()}");
        Console.WriteLine($"정적 Derived · 동적 Derived : Plain={d.Plain(),-14} Virt={d.Virt()}");
        Console.WriteLine($"((Base)d) 로 캐스트         : Plain={((Base)d).Plain(),-14} Virt={((Base)d).Virt()}");
    }
}
```

- **네 줄 × 두 칸 여덟 개**를 전부 맞힐 수 있는가?
- ★★★ 둘째 줄의 `Plain` 은 `Base.Plain` 인가 `Derived.Plain` 인가?
- ★★★ 넷째 줄(`((Base)d)`)이 셋째 줄과 다른가 — **객체는 한 번도 안 바뀌었는데**?
- ★ `Virt` 열과 `Plain` 열 중 **객체가 같으면 값이 같은** 쪽은 어디인가?

### 2. ★★★ `virtual` 없이 `override` 하면 (예측)

```csharp
// cs16b-novirt.cs
class Base {
    public string Plain() => "Base.Plain";
    public sealed string Odd() => "Base.Odd";
}
class Derived : Base {
    public override string Plain() => "Derived.Plain";
}
class Program { static void Main() { } }
```

- **진단 코드**가 무엇이고 문구가 무엇을 요구하는가?
- ★★ `public sealed string Odd()` 쪽은 왜 막히는가 — 코드는?
- ★ 이 블록이 **「C# 은 기본 비가상」의 증거**가 되는 이유를 한 줄로 댈 수 있는가?

### 3. ★★ `new` 를 안 적으면 경고가 몇 종류 나오나 (예측)

```csharp
// cs16b-hide.cs
using System;
class Base {
    public string Plain() => "Base.Plain";
    public int    Tag     = 1;
    public virtual string Virt() => "Base.Virt";
}
class Quiet : Base {
    public string Plain() => "Quiet.Plain";       // new 를 안 적었다
    public int    Tag     = 2;                    // 필드도 숨겨진다
    public string Virt()  => "Quiet.Virt";        // 가상인데 override 를 안 적었다
}
class Program { static void Main() { } }
```

- **경고가 몇 건**이고 **코드가 몇 종류**인가?
- ★★★ `Plain`(기반 비가상)과 `Virt`(기반 **가상**)의 **코드가 같은가 다른가** — 다르면 왜인가?
- ★★ **필드**에도 경고가 나는가?
- ★★★ `cc exit` 는 0 인가 1 인가 — 그것이 왜 무서운가?

### 4. ★★★ 여섯 탐침 중 `call` 이 나오는 자리는 몇 개인가 (예측)

```csharp
// cs16b-il.cs
using System;

class Base {
    public         string Plain() => "Base.Plain";
    public virtual string Virt()  => "Base.Virt";
    public static  string Stat()  => "Base.Stat";
}
sealed class Shut : Base {
    public sealed override string Virt() => "Shut.Virt";
    public string Own() => "Shut.Own";
}
class Child : Base {
    public override string Virt() => "Child.Virt " + base.Virt();     // base 호출
}
struct Val { public string M() => "Val.M"; }

static class Probe {
    public static string A(Base b) => b.Plain();      // 비가상 인스턴스 메서드
    public static string B(Base b) => b.Virt();       // 가상 메서드
    public static string C(Shut s) => s.Virt();       // sealed 타입의 가상 메서드
    public static string D(Shut s) => s.Own();        // sealed 타입의 비가상 메서드
    public static string E()       => Base.Stat();    // 정적 메서드
    public static string F(Val v)  => v.M();          // 구조체의 메서드
}

class Program {
    static void Main() {
        foreach (var n in new[] { "A", "B", "C", "D", "E", "F" }) Il.Dump(typeof(Probe), n);
        Il.Dump(typeof(Child), "Virt");
    }
}
```

- **A\~F 와 `Child.Virt` 일곱 자리**에 각각 `call` 과 `callvirt` 중 무엇이 나오는가?
- ★★★ **비가상 메서드인 `A` 에 `callvirt` 가 나온다면 왜인가**?
- ★★ `E`(정적)와 `F`(구조체)가 다른 이유를 한 낱말로 댈 수 있는가?
- ★★★ `base.Virt()` 가 `call` 이어야 하는 이유는 무엇인가 — `callvirt` 면 무슨 일이 나는가?
- ★ `C`(sealed 타입의 가상 메서드)가 `callvirt` 인 것은 최적화를 **누가** 하기 때문인가?

### 5. ★★ 널 참조로 비가상 메서드를 부르면 (왜)

```csharp
// cs16b-null.cs
using System;

class Base { public string Plain() => "본문에 들어왔다"; }   // 가상이 아니다. this 를 안 쓴다

class Program {
    static void Main() {
        Base b = null;
        Console.Error.WriteLine("부르기 직전");
        try { Console.Error.WriteLine(b.Plain()); }
        catch (Exception e) { Console.Error.WriteLine($"잡힘 : {e.GetType().Name}"); }
    }
}
```

- 「본문에 들어왔다」가 찍히는가?
- ★★★ `Plain()` 은 **`this` 를 한 번도 안 쓰는데** 왜 예외가 나는가?
- ★ 이 블록이 4번의 답을 **어떻게 확증하는가**?

### 6. ★★★ `new` 로 숨긴 것을 인터페이스로 부르면 (예측)

```csharp
// cs16b-newiface.cs
using System;
interface IRun { string Go(); }
class Base : IRun { public virtual string Go() => "Base.Go"; }
class Hider : Base { public new string Go() => "Hider.Go"; }      // override 가 아니라 new
class Rider : Base { public override string Go() => "Rider.Go"; }

class Program {
    static void Main() {
        Hider h = new Hider();
        Rider r = new Rider();
        Console.WriteLine($"Hider 로      : {h.Go()}");
        Console.WriteLine($"((Base)h) 로  : {((Base)h).Go()}");
        Console.WriteLine($"((IRun)h) 로  : {((IRun)h).Go()}");
        Console.WriteLine($"Rider 로      : {r.Go()}");
        Console.WriteLine($"((IRun)r) 로  : {((IRun)r).Go()}");
    }
}
```

- **다섯 줄**에 각각 무엇이 찍히는가?
- ★★★ `((IRun)h).Go()` 는 `Hider.Go` 인가 `Base.Go` 인가?
- ★★★ 그 답이 **`new` 를 쓰면 안 되는 진짜 이유**인 까닭은 무엇인가?
- ★ 어떤 코드들이 **캐스트를 안 쓰고 인터페이스로 받는가**?

### 7. ★★ 인터페이스 기본 구현은 클래스로 내려오나 (예측)

```csharp
// cs16b-dim.cs
using System;
interface IGreet {
    string Hello() => "인터페이스의 기본 구현";     // C# 8 기본 구현 멤버
}
class Plain : IGreet { }                            // 아무것도 안 적었다
class Program {
    static void Main() {
        var p = new Plain();
        IGreet i = p;
        Console.WriteLine($"인터페이스로 부르면 : {i.Hello()}");
        Console.WriteLine($"클래스로 부르면     : {p.Hello()}");
    }
}
```

- **컴파일되는가** — 안 되면 **어느 줄**에서 **무슨 코드**인가?
- ★★★ 같은 객체를 `IGreet` 변수로 받으면 되는가?
- ★★ `Plain` 이 **선언한 인스턴스 메서드가 몇 개**인지 리플렉션으로 물으면?
- ★★★ Java 의 `default` 메서드와 같은가 다른가?

### 8. ★ `abstract` 와 `sealed` 의 진단 다섯 (경계)

- `abstract` 멤버에 **본문**을 두면 · **구현을 안 하면** · **타입을 `new` 하면** 각각 코드가 무엇인가?
- ★★ `sealed override` 를 다시 `override` 하면 · `sealed class` 를 상속하면 각각 무엇인가?
- ★ `Shape ok = new Circle();` 은 왜 조용한가?

### 9. ★★ 명시적 인터페이스 구현에 무엇이 박히나 (경계)

- 명시적으로 구현한 메서드의 **`IsPrivate`·`IsFinal`·`IsVirtual`** 은 각각 무엇인가?
- ★★★ **C# 소스에는 한정자를 하나도 못 적는데** 왜 셋이 다 박히는가?
- ★★ **메서드 이름**이 무엇으로 찍히는가 — 그래서 무엇이 가능해지는가?
- ★ 이것은 [15번](../15-access-modifiers-and-assembly-boundary/)의 여섯 한정자 중 어디에 드는가?

### 10. ★★★ 세 언어의 기본값을 표로 채울 수 있나 (연결)

```java
// Ex16.java
class Base {
    String plain() { return "Base.plain"; }              // 한정자 없음 — 그래도 가상이다
    int tag = 1;
}
class Derived extends Base {
    String plain() { return "Derived.plain"; }           // new 도 @Override 도 안 적었다
    int tag = 2;
}
public class Ex16 {
    public static void main(String[] a) {
        Base b = new Base();
        Base bd = new Derived();
        Derived d = new Derived();
        System.out.printf("정적 Base    · 동적 Base    : plain=%-15s tag=%d%n", b.plain(), b.tag);
        System.out.printf("정적 Base    · 동적 Derived : plain=%-15s tag=%d%n", bd.plain(), bd.tag);
        System.out.printf("정적 Derived · 동적 Derived : plain=%-15s tag=%d%n", d.plain(), d.tag);
    }
}
```

- ★★★ Java 에서 `Derived.plain` 은 **`Base` 변수로 불리는가** — `-Xlint:all` 에서 **경고가 나는가**?
- ★★ Java 에서 메서드를 **숨기는** 방법이 있는가?
- ★★★ Java 의 **필드**는 어느 타입을 보는가 — C# 과 같은가?
- ★★★ C++ 은 기본 비가상인데 숨겼을 때 **경고가 나는가**?
- ★★ C++ 의 `override` 는 C# 의 `override` 와 **같은 일**을 하는가?

### 11. ★★ 컴파일러가 안 보는 것 (경계)

- 상속 주변 함정 **여덟**을 심고 `-warn:9` 로 물으면 **몇 줄**에 진단이 붙는가?
- ★★★ **생성자에서 가상 메서드를 부르는 것**에 경고가 나는가 — 그 함정을 **값으로** 잡은 것은 몇 번 주제인가?
- ★★ **`override` 가 `base` 를 안 부르는 것**에 경고가 나는가?
- ★ **숨길 것이 없는데 `new` 를 적으면** 어떻게 되는가 — 그 경고가 왜 반가운가?

### 12. 다른 주제와 잇기 (연결)

- ★★★ **생성자 속 가상 호출**과 **초기화 순서**의 정본은 몇 번 주제인가?
- **인터페이스 설계 전반**은 몇 번 주제인가 — 여기서는 무엇만 봤는가?
- ★★ **명시적 구현 인덱서**가 이 주제의 규칙을 따르는 것은 몇 번 주제인가?
- **`protected` 의 경계**와 **`sealed` 클래스의 `protected` 경고**는 몇 번 주제와 맞닿는가?
- ★ 이 문서가 쓰는 **IL 디스어셈블러**는 어느 주제가 만들었나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
