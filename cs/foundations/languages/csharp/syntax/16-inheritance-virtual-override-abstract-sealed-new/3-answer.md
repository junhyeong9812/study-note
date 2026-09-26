# csharp/syntax/16 — 상속·`virtual`/`override`/`abstract`/`sealed`/`new` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·진단·IL 은 **.NET SDK 10.0.401** · 런타임 **10.0.12** · 타겟 **`net10.0`** ·
> **linux-x64** 에서 실제로 돌려 얻은 것이다(2026-09-26).\
> 대비는 **javac 21.0.5** 와 **g++ 13.3.0 · `-std=c++20`** 이다.\
> 진단은 **`-preferreduilang:en-US`** 로 영어로 고정했다.\
> ★ 블록은 캡처 스크립트가 파일로 받아 조립기가 끼워 넣은 것이다 — 손으로 옮긴 줄은 없다.
> **읽는 법** — **진단 문구**와 **IL 오프셋 폭**은 흔들리는 칸이다.\
> 근거로 쓰는 것은 **격자의 아홉 칸 · 옵코드 이름(`callvirt` 대 `call`) · 진단 코드와 `(행,열)` ·
> `IsPrivate`/`IsFinal`/`IsVirtual` · `cc exit`/`run exit`** 다.
> ★★★ **이 문서는 시간을 재지 않았다.** 「가상 호출이 비가상보다 느리다」 같은 문장이 **한 줄도 없다.**

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ **`Virt` 는 동적 타입, `Plain` 은 정적 타입**이 정한다

**출력**

```text
===== 소스: cs16b-grid.cs =====
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
===== csc -out:ex.dll cs16b-grid.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
정적 Base    · 동적 Base    : Plain=Base.Plain     Virt=Base.Virt
정적 Base    · 동적 Derived : Plain=Base.Plain     Virt=Derived.Virt
정적 Derived · 동적 Derived : Plain=Derived.Plain  Virt=Derived.Virt
((Base)d) 로 캐스트         : Plain=Base.Plain     Virt=Derived.Virt
```

**왜 그런가**

- ★★★ **`Virt` 열** — `Base bd = new Derived()` 에서 **`Derived.Virt`** 가 나왔다.\
  **변수 타입이 `Base` 인데도** 실제 객체를 따라간다. **`override` 는 동적 타입이 정한다.**
- ★★★ **`Plain` 열** — 같은 객체인데 **`Base.Plain`** 이다.\
  `Derived d` 로 받으면 `Derived.Plain` 이고, **`((Base)d)` 로 캐스트하면 다시 `Base.Plain`** 이다.
- ★★★ **넷째 줄이 결정적이다.** **객체는 한 번도 안 바뀌었는데 캐스트 한 번에 답이 바뀐다.**\
  ★ `new` 로 숨긴 것은 **객체의 성질이 아니라 이름 해석의 성질**이다 —\
  **컴파일 시점에 어느 메서드를 부를지 IL 에 박히고**, 런타임은 그것을 그대로 따른다.
- ★★ **비대칭을 한 줄로** — **`Virt` 는 객체가 같으면 값이 같다. `Plain` 은 객체가 같아도 갈린다.**
- ★ 진단은 한 건도 안 났다(`cc exit=0`) — `new` 와 `override` 를 **제대로 적었기 때문**이다. 3번이 그 반대 경우다.

### 2. ★★★ **`CS0506`** — 「virtual, abstract, override 로 표시돼 있지 않다」

**출력**

```text
===== 소스: cs16b-novirt.cs =====
class Base {
    public string Plain() => "Base.Plain";
    public sealed string Odd() => "Base.Odd";
}
class Derived : Base {
    public override string Plain() => "Derived.Plain";
}
class Program { static void Main() { } }
===== csc -out:ex.dll cs16b-novirt.cs 2>&1 | sort (cc exit=1) =====
cs16b-novirt.cs(3,26): error CS0238: 'Base.Odd()' cannot be sealed because it is not an override
cs16b-novirt.cs(6,28): error CS0506: 'Derived.Plain()': cannot override inherited member 'Base.Plain()' because it is not marked virtual, abstract, or override
```

**왜 그런가**

- ★★★ **`CS0506: cannot override inherited member 'Base.Plain()' because it is not marked virtual, abstract, or override`.**\
  ★★★ **이 한 줄이 「C# 은 기본 비가상」의 정본 증거다.** 한정자를 안 적은 메서드는 **열려 있지 않다.**\
  ★ 「문서에 그렇게 적혀 있다」보다 강하다 — **컴파일러가 직접 거절한다.**
- ★★ **`CS0238` — `sealed` 는 `override` 위에만 붙는다.** `public sealed string Odd()` 가 거절됐다.\
  ★★★ **잠글 것이 없는데 잠글 수 없다** — 원래 닫혀 있기 때문이다.\
  ★ 두 진단이 **한 쌍**으로 같은 사실을 말한다 — **기본값이 닫힘**이다.
- ★ `cc exit=1` 이다.

### 3. ★★ **경고 셋 · 코드 두 종류** — 그리고 `cc exit=0` 이다

**출력**

```text
===== 소스: cs16b-hide.cs =====
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
===== csc -out:ex.dll cs16b-hide.cs 2>&1 | sort (cc exit=0) =====
cs16b-hide.cs(10,19): warning CS0114: 'Quiet.Virt()' hides inherited member 'Base.Virt()'. To make the current member override that implementation, add the override keyword. Otherwise add the new keyword.
cs16b-hide.cs(8,19): warning CS0108: 'Quiet.Plain()' hides inherited member 'Base.Plain()'. Use the new keyword if hiding was intended.
cs16b-hide.cs(9,19): warning CS0108: 'Quiet.Tag' hides inherited member 'Base.Tag'. Use the new keyword if hiding was intended.
```

**왜 그런가**

- ★★★ **코드가 둘로 갈린다.**
  - **`Plain`**(기반이 **비가상**) → **`CS0108`** — 「숨긴다. 의도했으면 `new` 를 쓰라」.
  - **`Virt`**(기반이 **가상**) → **`CS0114`** — 「숨긴다. **재정의하려면 `override`**, 아니면 `new` 를 쓰라」.
  - ★★★ **`CS0114` 는 선택지를 둘 제시한다** — 기반이 가상일 때만 `override` 가 후보이기 때문이다.
  - ★★ **「`CS0108` 하나」로 외우면 틀린다.** 라이브러리가 가상으로 열어 둔 멤버를 건드릴 때는 **`CS0114`** 쪽이다.
- ★★★ **필드에도 경고가 난다** — `Tag` 에 `CS0108` 이다. **`new` 는 메서드 전용이 아니다.**
- ★★★ **셋 다 경고이고 `cc exit=0` 이다 — 컴파일이 성공한다.**\
  ★★★ **그래서 무섭다.** 경고를 끄고 지나가면 **1번의 격자가 조용히 적용된다.**\
  ★ 이 주제의 경고는 전부 **설계 사고의 신호**이지 스타일 잔소리가 아니다.

### 4. ★★★ **`call` 은 셋뿐이다** — 정적 · 구조체 · `base`

**출력**

```text
===== 소스: cs16b-il.cs =====
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
===== csc -r:il.dll -out:ex.dll cs16b-il.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
--- Probe.A ---
  IL_0000: ldarg.0
  IL_0001: callvirt Base::Plain
  IL_0006: ret
--- Probe.B ---
  IL_0000: ldarg.0
  IL_0001: callvirt Base::Virt
  IL_0006: ret
--- Probe.C ---
  IL_0000: ldarg.0
  IL_0001: callvirt Base::Virt
  IL_0006: ret
--- Probe.D ---
  IL_0000: ldarg.0
  IL_0001: callvirt Shut::Own
  IL_0006: ret
--- Probe.E ---
  IL_0000: call Base::Stat
  IL_0005: ret
--- Probe.F ---
  IL_0000: ldarga.s 0
  IL_0002: call Val::M
  IL_0007: ret
--- Child.Virt ---
  IL_0000: ldstr "Child.Virt "
  IL_0005: ldarg.0
  IL_0006: call Base::Virt
  IL_000b: call System.String::Concat
  IL_0010: ret
```

**왜 그런가**

| 탐침 | 무엇을 불렀나 | 옵코드 | 왜 |
|---|---|---|---|
| A | **비가상** 인스턴스 메서드 | **`callvirt`** | ★★★ 널 검사 때문 |
| B | 가상 메서드 | **`callvirt`** | 진짜 가상 디스패치 |
| C | `sealed` 타입의 가상 메서드 | **`callvirt`** | ★ 컴파일러는 여기서도 안 바꾼다 |
| D | `sealed` 타입의 비가상 메서드 | **`callvirt`** | 널 검사 |
| E | **정적** 메서드 | ★ **`call`** | 수신자가 없다 |
| F | **구조체**의 메서드 | ★ **`call`** | 값 타입이라 널일 수 없다 |
| `Child.Virt` | ★★ **`base.Virt()`** | ★ **`call`** | ★★★ `base` 는 **비가상 호출을 명시**하는 것 |

- ★★★ **답은 널 검사다.** ECMA-335(CLI)의 `callvirt` 는 **수신자가 `null` 이면 `NullReferenceException` 을 던진다.**\
  `call` 은 **그 검사를 안 한다** — `this` 가 널인 채로 메서드 본문에 들어간다.\
  ★★ C# 컴파일러는 「**널 참조로 인스턴스 메서드를 부르면 반드시 예외가 난다**」를 보장하고 싶어서\
  **비가상 메서드에도 `callvirt` 를 쓴다.**
- ★★★ **`E`·`F` 가 그 설명을 확증한다** — **널일 수 없는 두 자리에서만 `call` 이 나왔다.**\
  ★ **한 낱말로 갈리는 이유** — **수신자**다. 정적 메서드는 수신자가 없고,\
  구조체 메서드는 `ldarga.s`(주소 싣기)로 부르므로 널이 원리상 불가능하다.
- ★★★ **`base.Virt()` 가 `call` 인 것**이 네 번째 증거다.\
  ★★★ **`callvirt` 였다면 동적 타입이 `Child` 이므로 `Child.Virt` 가 다시 불려 무한 재귀**가 된다.\
  ★ 여기서는 **「널 검사」보다 「가상 디스패치를 하지 마라」가 우선**이다.
- ★★ **탐침 `C` 가 재미있다** — 타입이 `sealed` 라 **재정의될 수 없는데도** `callvirt` 다.\
  ★★★ **그 최적화는 컴파일러가 아니라 JIT 이 한다**(디버추얼라이제이션). **IL 층에서는 안 바꾼다.**
- ★★★ **그래서 「`callvirt` = 가상 호출」은 틀렸다.** 읽는 법은 「**`callvirt` = 널 검사 + (가상이면) 디스패치**」다.

> **어느 층인가** — ★★★ 「**C# 이 기본 비가상**」은 **ECMA-334**(언어)이고,\
> 「**`callvirt` 가 널 검사를 한다**」는 **ECMA-335**(CLI)다. **다른 층이라 모순이 아니다.**\
> ★★ 「**비가상 호출에도 `callvirt` 를 쓴다**」는 **Roslyn 의 선택**이다 — 명세가 강제하지 않는다.

### 5. ★★ **안 찍힌다** — `callvirt` 가 부르기 전에 막는다

**출력**

```text
===== 소스: cs16b-null.cs =====
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
===== csc -out:ex.dll cs16b-null.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
부르기 직전
잡힘 : NullReferenceException
```

**왜 그런가**

- ★★★ **「본문에 들어왔다」가 안 찍혔다.** 「부르기 직전」 다음이 바로 `잡힘 : NullReferenceException` 이다.
- ★★★ **`Plain()` 은 `this` 를 한 번도 안 쓴다.** 본문이 상수 문자열 하나를 돌려줄 뿐이다.\
  **그런데도 본문에 못 들어간다** — 예외가 **메서드 안이 아니라 호출 지점에서** 났다는 뜻이다.
- ★★★ **이것이 4번의 답을 확증한다.** `call` 이었다면 **본문이 돌아 「본문에 들어왔다」가 찍혔을 것**이다.\
  ★ 즉 **널 검사는 메서드가 `this` 를 쓰는지와 무관하게** `callvirt` 가 한다.
- ★★ **구분 마커를 표준 오류로 찍었다**(규칙 18) — `Console.Error` 라야 순서가 고정된다.\
  ★ 예외를 잡아서 **타입 이름만** 찍었다 — 스택 트레이스는 프레임 표기가 판에 매여 흔들리는 칸이다.

### 6. ★★★ **`Base.Go` 다** — 인터페이스는 `new` 를 안 본다

**출력**

```text
===== 소스: cs16b-newiface.cs =====
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
===== csc -out:ex.dll cs16b-newiface.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
Hider 로      : Hider.Go
((Base)h) 로  : Base.Go
((IRun)h) 로  : Base.Go
Rider 로      : Rider.Go
((IRun)r) 로  : Rider.Go
```

**왜 그런가**

- ★★★ **`((IRun)h).Go()` 가 `Base.Go` 다.** `Hider` 로 직접 부르면 `Hider.Go` 인데\
  **인터페이스로 부르면 `new` 가 안 보인다.**
- ★★★ **`Rider`(override)는 어느 쪽으로 불러도 `Rider.Go` 다.**
- ★★★ **왜 그런가** — 인터페이스 구현은 **`Base` 가 했다.**\
  `IRun.Go` 의 슬롯에는 `Base.Go` 가 들어 있고, `Hider.Go` 는 **그 슬롯을 건드리지 않는 새 메서드**다.\
  `Rider.Go` 는 `override` 라 **그 슬롯을 덮어썼다.**

```text
   Base 의 메서드 슬롯 표             Hider                       Rider
   ┌──────────────┐                 ┌──────────────┐            ┌──────────────┐
   │ [0] Go  ────────> Base.Go      │ [0] Go  ────────> Base.Go  │ [0] Go ───────> Rider.Go  ← 덮어씀
   └──────────────┘                 │ (새 메서드)  ──> Hider.Go   └──────────────┘
          ↑                         └──────────────┘
   IRun.Go 가 가리키는 자리            ★ 슬롯은 그대로다
```

- ★★★ **이것이 `new` 를 쓰면 안 되는 진짜 이유다.** 1번의 격자는 「캐스트하면 달라진다」로 끝나는데,\
  **인터페이스를 거치는 코드는 캐스트를 안 쓴다.**
- ★★★ **캐스트 없이 인터페이스로 받는 코드들** — LINQ(`IEnumerable<T>`) · DI 컨테이너(생성자 인자 타입) ·\
  컬렉션(`IList<T>`·`IDictionary<K,V>`) · 이벤트 핸들러 · 테스트 더블.\
  ★ 즉 **실무 코드의 대부분**이다. 거기서는 **`new` 로 만든 메서드가 영영 안 불린다.**

### 7. ★★★ **안 내려온다** — `CS1061` 이고 `Plain` 에는 그 메서드가 정말로 없다

**출력**

```text
===== 소스: cs16b-dim.cs =====
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
===== csc -out:ex.dll cs16b-dim.cs (cc exit=1) =====
cs16b-dim.cs(11,47): error CS1061: 'Plain' does not contain a definition for 'Hello' and no accessible extension method 'Hello' accepting a first argument of type 'Plain' could be found (are you missing a using directive or an assembly reference?)
```

```text
===== 소스: cs16b-dim2.cs =====
using System;
using System.Reflection;
interface IGreet { string Hello() => "인터페이스의 기본 구현"; }
class Plain : IGreet { }
class Program {
    static void Main() {
        IGreet i = new Plain();
        Console.WriteLine($"인터페이스로 부르면 : {i.Hello()}");
        Console.WriteLine($"Plain 이 선언한 인스턴스 메서드 수 : {typeof(Plain).GetMethods(BindingFlags.Public|BindingFlags.NonPublic|BindingFlags.Instance|BindingFlags.DeclaredOnly).Length}");
        Console.WriteLine($"Plain.GetMethod(\"Hello\") : {(typeof(Plain).GetMethod("Hello") is null ? "없음" : "있음")}");
        var map = typeof(Plain).GetInterfaceMap(typeof(IGreet));
        for (int k = 0; k < map.InterfaceMethods.Length; k++)
            Console.WriteLine($"인터페이스 {map.InterfaceMethods[k].Name} -> 실제 {map.TargetMethods[k].DeclaringType}.{map.TargetMethods[k].Name}");
    }
}
===== csc -out:ex.dll cs16b-dim2.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
인터페이스로 부르면 : 인터페이스의 기본 구현
Plain 이 선언한 인스턴스 메서드 수 : 0
Plain.GetMethod("Hello") : 없음
인터페이스 Hello -> 실제 IGreet.Hello
```

**왜 그런가**

- ★★★ **`p.Hello()` 가 `(11,47)` 에서 `CS1061`** — 「`Plain` 에 `Hello` 라는 정의가 **없다**」.\
  **인터페이스의 기본 구현은 클래스로 상속되지 않는다.**
- ★★★ **`i.Hello()` 는 돌아간다.** **같은 객체인데 변수 타입이 인터페이스면 되고 클래스면 안 된다.**
- ★★★ **리플렉션이 이유를 적는다.**
  - **`Plain` 이 선언한 인스턴스 메서드 수 = 0**.
  - **`Plain.GetMethod("Hello")` = 없음**.
  - **인터페이스 맵**: `Hello` → **`IGreet.Hello`** — 구현이 **인터페이스 쪽에 그대로 있다.**
  - ★ 즉 「**보이는데 막힌 것**」이 아니라 「**정말 없는 것**」이다.\
    ★★ [15번](../15-access-modifiers-and-assembly-boundary/) (2)에서 다른 어셈블리의 `internal` 이 `CS1061` 로 사라진 것과 **같은 성격**이다.
- ★★ **왜 이렇게 설계했나** — 기본 구현이 클래스로 내려오면 **다중 상속의 충돌 문제**가 그대로 들어온다.\
  인터페이스 둘이 같은 이름의 기본 구현을 주면 클래스가 어느 것을 쓸지 정할 수 없다.\
  ★ 그래서 **인터페이스 타입으로 부를 때만** 쓰이게 막았다.
- ★★★ **Java 의 `default` 메서드와 정반대다** — 그쪽은 클래스로 내려와 그냥 불린다(10번).

### 8. ★ 다섯 진단

**출력**

```text
===== 소스: cs16b-abstract.cs =====
abstract class Shape {
    public abstract double Area();
    public abstract double Perimeter() => 0;      // 본문이 있는 abstract
    public virtual  string Name() => "도형";
}
class Circle : Shape { }                          // 구현을 안 했다
class Program { static void Main() { } }
===== csc -out:ex.dll cs16b-abstract.cs 2>&1 | sort (cc exit=1) =====
cs16b-abstract.cs(3,28): error CS0500: 'Shape.Perimeter()' cannot declare a body because it is marked abstract
cs16b-abstract.cs(6,7): error CS0534: 'Circle' does not implement inherited abstract member 'Shape.Area()'
cs16b-abstract.cs(6,7): error CS0534: 'Circle' does not implement inherited abstract member 'Shape.Perimeter()'
```

```text
===== 소스: cs16b-abs2.cs =====
abstract class Shape {
    public abstract double Area();
    public virtual  string Name() => "도형";
}
class Circle : Shape {
    public override double Area() => 3.14;
}
class Program {
    static void Main() {
        Shape ok = new Circle();          // 파생은 만들어진다
        var   no = new Shape();           // 추상 클래스 자체는?
    }
}
===== csc -out:ex.dll cs16b-abs2.cs (cc exit=1) =====
cs16b-abs2.cs(11,20): error CS0144: Cannot create an instance of the abstract type or interface 'Shape'
```

```text
===== 소스: cs16b-sealed.cs =====
class A         { public virtual       string M() => "A"; }
class B : A     { public sealed override string M() => "B"; }
class C : B     { public override      string M() => "C"; }   // 더는 못 연다
sealed class S  { }
class T : S     { }                                            // sealed 클래스를 상속
class Program { static void Main() { } }
===== csc -out:ex.dll cs16b-sealed.cs 2>&1 | sort (cc exit=1) =====
cs16b-sealed.cs(3,47): error CS0239: 'C.M()': cannot override inherited member 'B.M()' because it is sealed
cs16b-sealed.cs(5,11): error CS0509: 'T': cannot derive from sealed type 'S'
```

**왜 그런가**

| 쓴 꼴 | 코드 | 뜻 |
|---|---|---|
| `abstract` 멤버에 **본문** | **`CS0500`** | 「문틀만」이라는 뜻이 진단으로 나온다 |
| `abstract` 멤버를 **구현 안 함** | **`CS0534`** | ★ **빠진 멤버마다 한 건씩** — 둘이면 둘이다 |
| `abstract` 타입을 **`new`** | **`CS0144`** | 「추상 타입이나 인터페이스의 인스턴스를 만들 수 없다」 |
| `sealed override` 를 다시 `override` | **`CS0239`** | 사슬을 거기서 닫는다 |
| `sealed class` 를 **상속** | **`CS0509`** | 타입 단위로 닫는다 |

- ★★★ **`CS0534` 가 「파생 클래스 선언 자체」에 붙는다**(`(6,7)` — `class Circle` 줄).\
  호출 지점이 아니라 **선언 지점**이다 — 「이 클래스는 존재할 수 없다」는 뜻이다.
- ★★★ **`Shape ok = new Circle();` 은 조용하다.** 막히는 것은 **`new Shape()` 하나**다.\
  ★ **변수 타입은 추상이어도 된다** — 추상 타입은 **만들 수 없을 뿐 가리킬 수는 있다.**\
  ★★ 그것이 추상 클래스의 존재 이유다.
- ★ **`sealed` 의 두 쓰임이 다른 코드로 갈린다** — 멤버는 `CS0239`, 클래스는 `CS0509`.\
  ★★ **`sealed override`** 는 **`virtual` 로 연 문을 중간에서 다시 잠그는 것**이다 —\
  깊은 상속 사슬의 예측 불가를 줄이는 도구다.

### 9. ★★ **`private`·`final`·`virtual` 셋이 한꺼번에** 박힌다

**출력**

```text
===== 소스: cs16b-explicit.cs =====
using System;
using System.Reflection;
interface IWalk { string Move(); }
interface ISwim { string Move(); }
class Duck : IWalk, ISwim {
    string IWalk.Move() => "걷는다";
    string ISwim.Move() => "헤엄친다";
    public string Move() => "그냥 움직인다";
}
class Program {
    static void Main() {
        var d = new Duck();
        Console.WriteLine($"d.Move()            = {d.Move()}");
        Console.WriteLine($"((IWalk)d).Move()   = {((IWalk)d).Move()}");
        Console.WriteLine($"((ISwim)d).Move()   = {((ISwim)d).Move()}");
        foreach (var m in typeof(Duck).GetMethods(BindingFlags.Public|BindingFlags.NonPublic|BindingFlags.Instance|BindingFlags.DeclaredOnly))
            Console.WriteLine($"메서드 {m.Name,-12} private={m.IsPrivate} final={m.IsFinal} virtual={m.IsVirtual}");
    }
}
===== csc -out:ex.dll cs16b-explicit.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
d.Move()            = 그냥 움직인다
((IWalk)d).Move()   = 걷는다
((ISwim)d).Move()   = 헤엄친다
메서드 IWalk.Move   private=True final=True virtual=True
메서드 ISwim.Move   private=True final=True virtual=True
메서드 Move         private=False final=False virtual=False
```

**왜 그런가**

- ★★★ **`private=True final=True virtual=True`** — 셋이 동시에 참이다.\
  ★★★ **C# 소스에는 한정자를 하나도 못 적는데** 메타데이터에는 셋이 다 있다.

| 플래그 | 왜 필요한가 |
|---|---|
| **`private`** | 클래스 이름으로는 못 부르게 — `d.Move()` 는 **공개 `Move`** 로 간다 |
| **`virtual`** | 인터페이스 디스패치가 **슬롯을 거쳐야** 하므로 |
| **`final`** | 파생이 `override` 로 덮을 수 없게 — 덮으려면 **다시 명시적으로 구현**해야 한다 |

- ★★★ **이름이 `IWalk.Move` 다** — **점이 들어간 이름은 C# 에서 선언할 수 없는 이름**이라 충돌이 원리상 없다.\
  ★★★ **그래서 같은 시그니처의 인터페이스 둘을 한 클래스가 구현할 수 있다** —\
  `IWalk.Move` 와 `ISwim.Move` 와 공개 `Move` **셋이 공존**하고 셋 다 다른 값을 돌려준다.
- ★★ **공개 `Move` 는 `private=False final=False virtual=False` 다** — **평범한 비가상 메서드**다.\
  ★ 그것이 인터페이스를 구현하지 **않는다는 것**도 이 줄이 말한다(구현했다면 `final`+`virtual` 이 붙는다).
- ★ **[15번](../15-access-modifiers-and-assembly-boundary/)의 여섯 한정자 중 어디에도 안 든다** — **일곱 번째 자리**다.\
  한정자를 적을 수 없는데 `private` 이 되고, 그러면서 인터페이스로는 열려 있다.\
  ★★ [14번](../14-indexers/) (8)의 명시적 구현 인덱서가 **같은 규칙**을 따른다.

### 10. ★★★ 세 언어의 기본값

**출력**

```text
===== 소스: j16/Ex16.java =====
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
===== javac -Xlint:all -d j16out j16/Ex16.java && java -cp j16out Ex16 (cc exit=0 · run exit=0) =====
정적 Base    · 동적 Base    : plain=Base.plain      tag=1
정적 Base    · 동적 Derived : plain=Derived.plain   tag=1
정적 Derived · 동적 Derived : plain=Derived.plain   tag=2
===== 소스: j16b/Shut.java =====
class Locked {
    final String shut() { return "Locked.shut"; }
}
class Picker extends Locked {
    String shut() { return "Picker.shut"; }
}
===== javac -d j16bout j16b/Shut.java (cc exit=1) =====
j16b/Shut.java:5: error: shut() in Picker cannot override shut() in Locked
    String shut() { return "Picker.shut"; }
           ^
  overridden method is final
1 error
```

```text
===== 소스: cs16b-cpp.cpp =====
#include <cstdio>

struct Base {
    const char* plain() const { return "Base::plain"; }            // 기본 비가상 — C# 과 같다
    virtual const char* virt() const { return "Base::virt"; }
    virtual ~Base() = default;
};
struct Derived : Base {
    const char* plain() const { return "Derived::plain"; }         // new 같은 키워드가 없다
    const char* virt() const override { return "Derived::virt"; }
};

int main() {
    Base b; Derived d; Base& bd = d;
    std::printf("정적 Base    · 동적 Base    : plain=%-15s virt=%s\n", b.plain(), b.virt());
    std::printf("정적 Base    · 동적 Derived : plain=%-15s virt=%s\n", bd.plain(), bd.virt());
    std::printf("정적 Derived · 동적 Derived : plain=%-15s virt=%s\n", d.plain(), d.virt());
}
===== g++ -std=c++20 -Wall -Wextra -Woverloaded-virtual -o cppex16 cs16b-cpp.cpp && ./cppex16 (cc exit=0 · run exit=0) =====
정적 Base    · 동적 Base    : plain=Base::plain     virt=Base::virt
정적 Base    · 동적 Derived : plain=Base::plain     virt=Derived::virt
정적 Derived · 동적 Derived : plain=Derived::plain  virt=Derived::virt
===== 소스: cs16b-cpperr.cpp =====
struct Base    { const char* plain() const { return "Base"; } };
struct Derived : Base {
    const char* plain() const override { return "Derived"; }
};
int main() { }
===== g++ -std=c++20 -Wall -Wextra -o /dev/null cs16b-cpperr.cpp (cc exit=1) =====
cs16b-cpperr.cpp:3:17: error: ‘const char* Derived::plain() const’ marked ‘override’, but does not override
    3 |     const char* plain() const override { return "Derived"; }
      |                 ^~~~~
```

```text
                    C#                     Java                  C++
   기본값        ★ 비가상               ★ 가상                ★ 비가상
   열려면        virtual                (필요 없음)            virtual
   닫으려면      (기본)                  final                  (기본)
   덮으려면      override               (그냥 쓴다)            override 는 검사용
   숨기려면      new                    ★ 불가능(메서드)        ★ 키워드 없음
   안 적으면     ★ 경고 CS0108/CS0114   ★ 경고 없음            ★ 경고 없음
   필드는        정적 타입              ★ 정적 타입(같다)       정적 타입(같다)
```

**왜 그런가**

- ★★★ **Java 에서 `Derived.plain` 이 `Base` 변수로 불렸다** — 한정자를 하나도 안 적었는데 **재정의**다.\
  ★★★ **`-Xlint:all` 에서 경고가 한 줄도 안 났다.** C# 이라면 `CS0108` 이 났을 자리다.
- ★★★ **Java 에서 메서드를 숨기는 방법은 없다.** 같은 시그니처를 쓰면 **무조건 재정의**다.\
  닫으려면 **`final`** 을 적어야 하고, 그것을 덮으려 하면\
  **`shut() in Picker cannot override shut() in Locked` / `overridden method is final`** 로 막힌다.
- ★★★ **필드는 세 언어가 같다** — Java 에서도 `bd.tag` 가 **1**(Base 의 것) 이다.\
  ★★ **「메서드는 재정의되고 필드는 숨겨진다」는 비대칭이 Java 에도 그대로 있다.**\
  ★ C# 은 그 비대칭을 **메서드에까지** 끌고 온 것이고(기본 비가상), Java 는 **필드에만** 둔다.
- ★★★ **C++ 은 기본 비가상인 점이 C# 과 같은데 숨김 키워드가 없다.**\
  `Derived::plain` 이 `Base::plain` 을 가리는데 **`-Wall -Wextra -Woverloaded-virtual` 에서 경고가 0건**이다.\
  ★★★ **같은 기본값에서 도구의 태도가 갈린다** — C# 은 잔소리를 하고 C++ 은 조용하다.
- ★★ **C++ 의 `override` 는 C# 의 `override` 와 같은 일이 아니다.**\
  C# 의 `override` 는 **「덮겠다」는 선언**이고(안 적으면 `CS0114` 경고이지만 컴파일은 된다),\
  C++ 의 `override` 는 **「덮는지 검사하라」는 요청**이다 — 안 적어도 덮이고, 적었는데 안 덮으면\
  **`marked 'override', but does not override`** 로 막힌다.\
  ★ **C# 의 `CS0506` 과 하는 일은 비슷한데 낱말의 방향이 반대**다.
- ★ **재검증 방식이 다르다** — **g++ 와 javac 는 소스 줄과 캐럿을 끼워 준다.**\
  **C# 진단은 `(행,열)` 만** 주므로 **소스 배너를 같은 블록에 싣는 것**이 필수다.

### 11. ★★ **여덟 중 다섯만 답한다** — 생성자 속 가상 호출은 여전히 침묵이다

**출력**

```text
===== 소스: cs16b-probe.cs =====
using System;

// 탐침 1 — 파생에서 같은 이름을 다시 쓰는데 new 를 안 적었다
class P1A { public string M() => "A"; }
class P1B : P1A { public string M() => "B"; }

// 탐침 2 — 숨길 것이 없는데 new 를 적었다
class P2A { }
class P2B : P2A { public new string M() => "B"; }

// 탐침 3 — 생성자에서 가상 메서드를 부른다 (12편이 값으로 잡은 함정)
class P3A { public P3A() { Describe(); } public virtual void Describe() { } }
class P3B : P3A { readonly string s = "늦게 채워진다"; public override void Describe() => Console.WriteLine(s.Length); }

// 탐침 4 — Equals 만 덮고 GetHashCode 를 안 덮었다
class P4 { public override bool Equals(object o) => true; }

// 탐침 5 — sealed 클래스에 protected 멤버를 둔다
sealed class P5 { protected int n = 1; public int N => n; }

// 탐침 6 — 파생이 기반의 가상 메서드를 override 했는데 base 를 안 부른다
class P6A { public virtual void Setup() { } }
class P6B : P6A { public override void Setup() { } }

// 탐침 7 — 상속 사슬이 깊은데 중간이 아무것도 안 한다
class P7A { public virtual int V() => 1; }
class P7B : P7A { }
class P7C : P7B { public override int V() => 3; }

// 탐침 8 — 기반의 필드를 파생이 같은 이름으로 다시 선언한다
class P8A { public int Tag = 1; }
class P8B : P8A { public int Tag = 2; }

class Program { static void Main() { } }
===== csc -warn:9 -out:ex.dll cs16b-probe.cs 2>&1 | sort (cc exit=0) =====
cs16b-probe.cs(16,7): warning CS0659: 'P4' overrides Object.Equals(object o) but does not override Object.GetHashCode()
cs16b-probe.cs(19,33): warning CS0628: 'P5.n': new protected member declared in sealed type
cs16b-probe.cs(32,30): warning CS0108: 'P8B.Tag' hides inherited member 'P8A.Tag'. Use the new keyword if hiding was intended.
cs16b-probe.cs(5,33): warning CS0108: 'P1B.M()' hides inherited member 'P1A.M()'. Use the new keyword if hiding was intended.
cs16b-probe.cs(9,37): warning CS0109: The member 'P2B.M()' does not hide an accessible member. The new keyword is not required.
===== csc -warn:9 -out:ex.dll cs16b-probe.cs 2>&1 | grep -o "cs16b-probe.cs([0-9]*" | sort -u | wc -l    # 탐침 8개 중 진단이 붙은 줄은 몇 개인가 (exit=0) =====
5
```

**왜 그런가**

- ★★★ **진단이 붙은 줄은 다섯**이고, 스크립트가 직접 세어 마지막 줄에 **`5`** 를 찍었다(사람이 안 셌다).

| 탐침 | 무엇을 심었나 | 답했나 |
|---|---|---|
| 1 | 비가상 메서드를 `new` 없이 다시 선언 | **답함** — `CS0108` |
| 2 | 숨길 것이 없는데 `new` 를 적음 | ★★ **답함** — `CS0109` |
| 3 | ★★★ **생성자에서 가상 메서드를 부름** | ★★★ **침묵** |
| 4 | `Equals` 만 덮고 `GetHashCode` 안 덮음 | **답함** — `CS0659` |
| 5 | `sealed` 클래스에 `protected` 멤버 | ★★ **답함** — `CS0628` |
| 6 | ★★ **`override` 가 `base` 를 안 부름** | ★★★ **침묵** |
| 7 | 상속 사슬 중간이 아무것도 안 함 | **침묵** (★ 정상이다) |
| 8 | 기반의 필드를 파생이 같은 이름으로 | **답함** — `CS0108` |

- ★★★ **탐침 3 이 급소다.** [12번](../12-class-fields-constructors-this-base/) (4)가 **값으로** 잡은 함정이다 —\
  생성자에서 가상 메서드를 부르면 **파생 것이 불리고**, 그때 파생 필드 초기자가 아직 안 돌아\
  **`FromBody=null`·`Len=0`** 이었다. **거기가 정본이라 여기서 다시 재지 않았다.**
- ★★★ **12편은 `-warn:9` 탐침 여섯에서 경고 0건**이었고, **이번 판 탐침 3 도 침묵**이다.\
  ★★★ **이 갈래에서 같은 결론이 두 번 확인됐다** — **컴파일러는 「형태」만 보고 「순서 사고」는 안 본다.**
- ★★ **탐침 6 도 침묵이다** — `override` 가 `base` 를 안 불러 기반 초기화가 통째로 빠져도 말이 없다.\
  ★ 5번에서 봤듯 **`base` 는 사슬이라 한 군데만 끊겨도 아래가 전부 안 돈다.**
- ★★ **탐침 2 의 `CS0109` 가 반가운 자리다** — **쓸데없는 `new` 를 알려 준다.**\
  ★ 기반에서 멤버를 지웠는데 파생의 `new` 가 남아 있는 상황이 그것이고,\
  **그대로 두면 다음 사람이 「기반에 뭔가 있겠거니」로 잘못 읽는다.**
- ★★ **탐침 5 의 `CS0628`** — `sealed` 클래스에 `protected` 를 두면 **볼 사람이 없다.**\
  ★ 이 주제와 [15번](../15-access-modifiers-and-assembly-boundary/)이 만나는 유일한 진단이다.
- ★ **탐침 7 이 침묵인 것은 정상이다** — 중간 클래스가 아무것도 안 하는 것은 흔하고 올바른 설계다.\
  ★★ 「**침묵 = 문제 없음**」이 아니라 「**침묵 = 컴파일러가 판단하지 않음**」이다. 탐침 3·6 이 그 증거다.

### 12. 잇기

- ★★★ **생성자 속 가상 호출과 초기화 순서**의 정본은 [12번](../12-class-fields-constructors-this-base/)이다.\
  거기 (1)이 **파생 필드 초기자가 1번**임을 찍었고 (4)가 **`FromBody=null`** 을 값으로 잡았다.
- **인터페이스 설계 전반**은 목록의 **17번 주제**다. 여기서는 **상속과 부딪히는 자리**(6번·7번·9번)만 봤다.
- ★★ **명시적 구현 인덱서**는 [14번](../14-indexers/) (8)이고, 이 주제 9번의 규칙을 그대로 따른다.
- **`protected` 의 경계**는 [15번](../15-access-modifiers-and-assembly-boundary/)이다.\
  ★ **`sealed` 클래스의 `protected` 경고**(`CS0628`, 11번 탐침 5)가 두 주제가 만나는 자리다.\
  ★★ **접근성과 가상성은 독립 축**이다 — `public` 인데 비가상일 수 있고 `protected` 인데 가상일 수 있다.
- ★ 이 문서가 쓰는 **IL 디스어셈블러**는 [03번](../03-boxing-and-unboxing/)이 만들었다 — 외부 도구가 0개다.

## 실행 검증

| 무엇 | 몇 번·어디서 | 결과 |
|---|---|---|
| `cs16b-grid.cs` 정적 × 동적 격자 | csc 1회 | ★★★ `Virt` 는 동적 · `Plain` 은 정적 · **캐스트로 답이 바뀐다** |
| `cs16b-novirt.cs` `virtual` 없이 `override` | csc 1회 | ★★★ **`CS0506`** · `CS0238` |
| `cs16b-hide.cs` `new` 를 안 적으면 | csc 1회 | ★★★ **`CS0108` ×2 · `CS0114` ×1** · **`cc exit=0`** |
| `cs16b-il.cs` `callvirt` 대 `call` | csc 1회(7메서드) | ★★★ **`call` 은 셋뿐** — 정적·구조체·`base` |
| `cs16b-null.cs` 널 검사 | csc 1회 | ★★★ 본문에 **안 들어간다** · `NullReferenceException` |
| `cs16b-base.cs` `base` 사슬 | csc 1회 | `A→B→C` · IL 이 **`call B::Chain`** |
| `cs16b-newiface.cs` 인터페이스로 부르면 | csc 1회 | ★★★ `((IRun)h).Go()` = **`Base.Go`** |
| `cs16b-abstract.cs` · `cs16b-abs2.cs` | csc 2회 | **`CS0500`·`CS0534` ×2·`CS0144`** |
| `cs16b-sealed.cs` `sealed` 둘 | csc 1회 | **`CS0239`·`CS0509`** |
| `cs16b-explicit.cs` 명시적 구현 | csc 1회 | ★★★ **`private=True final=True virtual=True`** |
| `cs16b-dim.cs` · `cs16b-dim2.cs` | csc 2회 | ★★★ **`CS1061`** · 선언 메서드 **0개** · 맵이 `IGreet.Hello` |
| `cs16b-probe.cs` 탐침 여덟 | csc 1회(`-warn:9`) | ★★★ **진단이 붙은 줄 5** · 탐침 3·6·7 침묵 |
| `Ex16.java` · `Shut.java` | javac 2회 | ★★★ **경고 0건에 재정의** · `final` 은 **에러** |
| `cs16b-cpp.cpp` · `cs16b-cpperr.cpp` | g++ 2회 | ★★★ 숨김에 **경고 0건** · `override` 는 **검사용** |
| `cs16b-form.cs` 형태 | csc 1회 | `원(12.6)#` — **한 줄 안에서 격자가 동시에** |

**구현 의존 항목** — 다음은 **이 판(.NET SDK 10.0.401 · Roslyn · javac 21.0.5 · g++ 13.3.0)에서만** 그렇다.

- ★★★ **비가상 호출에도 `callvirt` 를 쓰는 것** — 명세가 강제하지 않는 **Roslyn 의 선택**이다.
- ★★★ **`sealed` 타입의 가상 호출도 `callvirt` 인 것** — 디버추얼라이제이션은 **JIT 의 몫**이다.
- ★★ **명시적 구현에 `final`+`virtual` 이 같이 박히는 것.**
- ★★ **`-warn:9` 에서 탐침 여덟 중 다섯만 답한 것** — 다음 판에서 늘 수 있다.
- ★ **진단 문구 전부** · **IL 오프셋 폭** · **javac·g++ 의 진단 표기 형식**.

**언어가 보장하는 것**(구현이 바뀌어도 같다)

- **기본 비가상** — `virtual`/`abstract`/`override` 가 아닌 멤버는 재정의할 수 없다.
- **`override` 가 동적 타입으로, `new` 가 정적 타입으로 갈리는** 것.
- **`new` 로 숨긴 멤버가 인터페이스 디스패치에 안 보이는** 것.
- **인터페이스의 기본 구현이 클래스로 상속되지 않는** 것(C# 8).
- **명시적 인터페이스 구현이 클래스 이름으로 안 불리는** 것.
- **`sealed override` 가 사슬을 닫고 `sealed class` 가 상속을 막는** 것.
- **`abstract` 타입을 인스턴스화할 수 없고 파생이 반드시 구현해야 하는** 것.
- **`callvirt` 가 널 수신자에 예외를 던지는** 것 — ★ 이것은 **CLI(ECMA-335) 보장**이다.

**안 돌려 본 것 / 못 잰 것 / 잴 것이 없는 것**

- **안 돌려 본 것** — ★★ **`newslot` 플래그를 리플렉션으로 직접 찍는 판**(9번은 명시적 구현만 찍었다) ·\
  ★★ **JIT 의 디버추얼라이제이션 관찰**(JIT 덤프 하네스가 따로 필요하다) ·\
  ★★ **인터페이스 둘이 같은 이름의 기본 구현을 줄 때의 충돌**(7번의 설계 이유를 값으로 확인 안 했다) ·\
  ★ **속성·인덱서·이벤트의 `virtual`/`override`**(메서드만 던졌다 — [13번](../13-properties-init-required-field/)·[14번](../14-indexers/)) ·\
  ★ **제네릭 타입의 가상 메서드와 공변 반환**(C# 9) ·\
  ★ **`abstract override`**(재추상화) · ★ **Java 의 `module-info`·C++ 의 `final` 클래스** ·\
  ★ **상속 4단 이상**(3단까지만 던졌다).
- **못 잰 것** — ★★★ **「가상 호출이 비가상 호출보다 비싼가」.**\
  IL 은 **옵코드 이름**을 말하지 **비용**을 말하지 않는다. JIT 이 인라인하거나 디버추얼라이즈하면\
  **IL 의 `callvirt` 가 기계어에서 직접 호출이 된다.** 재려면 그 하네스가 필요하고 **이 판에서는 안 만들었다.**\
  ★ **한 판의 절댓값은 근거가 아니다**(규칙 24) — 그래서 **수치를 하나도 안 적었다.**
- ★ 「**부적용인 창**」 — **④ 할당 바이트.** `new` 로 숨기든 `override` 하든 **객체는 하나**이고 크기가 같다.\
  `virtual` 을 붙인다고 객체가 커지지도 않는다 — **메서드 테이블은 타입당 하나**다.\
  ★★★ **「안 쟀다」가 아니라 「잴 것이 없다」다**(규칙 18-B).

**버전이 올랐을 때 다시 돌려야 하는 것**

- ★★★ **11번의 탐침 여덟** — 컴파일러가 「생성자 속 가상 호출」을 경고하기 시작하면 이 절의 결론이 바뀐다.\
  ★ [12번](../12-class-fields-constructors-this-base/)과 **함께** 다시 던져야 한다.
- ★★ **4번의 옵코드 표** — Roslyn 이 `sealed` 타입에서 `call` 로 바꾸기 시작하면 `C` 칸이 움직인다.
- ★★ **10번의 javac·g++ 판** — 두 컴파일러가 숨김 경고를 넣으면 표가 바뀐다.\
  ★ **「경고 0건」은 판과 확인 날짜를 같이 적어야 한다** — 도구의 성질은 조용히 낡는다.
- ★ **1번·2번·6번·7번·8번·9번** — **명세가 정한 것이라 바뀔 일이 없다.** 바뀌면 그것이 뉴스다.
