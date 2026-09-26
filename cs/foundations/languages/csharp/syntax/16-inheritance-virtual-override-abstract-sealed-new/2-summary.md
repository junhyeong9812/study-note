# csharp/syntax/16 — 상속·`virtual`/`override`/`abstract`/`sealed`/`new` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [ECMA-334 7판(2023-12)](https://ecma-international.org/publications-and-standards/standards/ecma-334/) ·
> [Learn — 상속](https://learn.microsoft.com/en-us/dotnet/csharp/fundamentals/object-oriented/inheritance) ·
> [Learn — `virtual`](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/keywords/virtual) ·
> [Learn — `new` 한정자](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/keywords/new-modifier) ·
> [Learn — 인터페이스의 기본 구현 멤버(C# 8)](https://learn.microsoft.com/en-us/dotnet/csharp/whats-new/tutorials/default-interface-methods-versions) ·
> [ECMA-335(CLI) — `callvirt`](https://ecma-international.org/publications-and-standards/standards/ecma-335/)
> **실행 검증** — 이 문서의 모든 출력·진단·IL 은 아래 「이 판」의 도구로 **실제로 돌려 얻은 것**이다(2026-09-26).\
> ★ 블록은 캡처 스크립트가 파일로 받아 조립기가 끼워 넣은 것이다 — 사람이 옮겨 적은 줄은 하나도 없다.\
> ★★★ **진단 언어를 영어로 고정했다**(`DOTNET_CLI_UI_LANGUAGE=en` + `-preferreduilang:en-US`).\
> **대비는 실측이다** — **javac 21.0.5** 와 **g++ 13.3.0 · `-std=c++20`** 으로 같은 모양을 던졌다((9)).
> **버전** — 상속·`virtual`/`override`/`new`/`abstract`/`sealed` 는 **C# 1.0부터** ·\
> **인터페이스 기본 구현 멤버는 C# 8** 이다. `-langversion:latest` 로 던졌다.
> **경계** — **클래스·생성자·초기화 순서**는 [12번](../12-class-fields-constructors-this-base/), **속성**은 [13번](../13-properties-init-required-field/),\
> **접근 한정자**는 [15번](../15-access-modifiers-and-assembly-boundary/), **인터페이스 설계 전반**은 목록의 **17번 주제**가 정본이다.\
> 여기서는 「**어느 메서드가 불리나**」만 센다.\
> ★ **상속·다형성 개념 자체**는 [`oop-basics/`](../../../../oop-basics/)가 정본이고, 여기는 **C# 의 기본값**이다.
> ★★★ **대비 둘** — Java 갈래 목록([`java/syntax/README.md`](../../../java/syntax/README.md))의 **09번**([`09-inheritance-overriding/`](../../../java/syntax/09-inheritance-overriding/))은 **기본 가상**이고,\
> C++ 갈래 목록([`cpp/syntax/README.md`](../../../cpp/syntax/README.md))의 **19번**은 **기본 비가상인데 `new` 같은 키워드가 없다.**\
> ★ 인터페이스 기본 구현 쪽 대비는 Java 갈래 목록의 **11번**([`11-interfaces-default-methods/`](../../../java/syntax/11-interfaces-default-methods/))이다.
>
> ★★ **흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | 진단 **문구** — 판마다 다듬인다 | ★★★ **진단 코드**(`CS0506`·`CS0108`·`CS0114`·`CS0239`·`CS0144`…)와 **`(행,열)`** |
> | **IL 오프셋 폭**(`IL_0006`)이 판마다 달라질 수 있다는 것 | ★★★ **옵코드 이름**(`callvirt` 대 `call`)과 **호출 대상의 타입 이름** |
> | g++·javac 의 진단 **표기 형식** | ★★★ **격자의 아홉 칸** — 이 주제의 답 자체다 |
> | ★ **증분의 절댓값 일부** — 이 주제는 그 칸을 **안 세웠다**(아래 (0)) | ★★ **`cc exit` 와 `run exit`**(갈라 적었다) · **`IsPrivate`/`IsFinal`/`IsVirtual`** |
> | 여러 진단이 나올 때 Roslyn 이 내는 **순서** — 배너에 `\| sort` 를 적었다 | ★ **`-warn:9` 에서 답한 탐침의 개수** |

## 이 판

```text
===== dotnet --version && dotnet --list-runtimes | grep NETCore (exit=0) =====
10.0.401
Microsoft.NETCore.App 10.0.12 [/home/jun/.local/opt/dotnet/shared/Microsoft.NETCore.App]
===== javac -version && g++ --version | head -1 (exit=0) =====
javac 21.0.5
g++ (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0
```

## 이 갈래가 쓰는 세 층

| 층 | 뜻 | 이 주제에서 근거로 쓰는 것 |
|---|---|---|
| **언어 명세(ECMA-334)** | C# 언어가 약속한 것 | ★★★ **기본 비가상** · `new` 로 숨기는 것이 **정적 타입**으로 갈리는 것 · `override`/`sealed`/`abstract` 규칙 |
| **런타임·CLI(ECMA-335)** | CoreCLR·Roslyn 이 그렇게 하는 것 | ★★★ **`callvirt` 가 널 검사를 한다는 것** · 명시적 구현이 `private`+`final`+`virtual` 인 것 |
| **이 판의 관찰** | .NET 10.0.12 · linux-x64 · javac 21.0.5 · g++ 13.3.0 | 진단 문구 · `-warn:9` 가 답한 탐침 수 · `run exit` |

★★★ **이 주제는 첫 칸과 둘째 칸의 선이 가장 잘 안 보인다.**\
「**기본 비가상**」은 명세인데, 「**그런데 IL 은 `callvirt` 를 쓴다**」는 CLI 의 것이고,\
둘이 **모순처럼 보인다**((4)에서 푼다). **선을 매 절마다 긋는다.**

## 한눈에 — 쉽게 말하면

**C# 에서 메서드는 기본적으로 「닫혀 있다」.**

건물 열쇠를 생각하자.

- **`virtual`** — 「이 문은 **파생이 바꿔 달아도 된다**」고 **일부러 열어 둔 것**.
- **한정자 없음** — ★★★ **닫혀 있다.** 파생이 같은 이름을 써도 **문이 안 바뀐다.**
- **`override`** — 열어 둔 문에 **자기 열쇠를 다는 것**. 누가 열든 **새 열쇠**가 돈다.
- **`new`** — ★★★ **문 앞에 「내 문」이라고 팻말만 세우는 것.** 뒷문으로 들어온 사람은 **원래 문**을 쓴다.
- **`sealed override`** — 자기 열쇠를 달고 **더는 못 바꾸게 잠그는 것**.
- **`abstract`** — 「문틀만 있고 문은 없다. 파생이 반드시 달아라」.

| 비유 | 실체 | 어디서 보나 |
|---|---|---|
| 기본은 닫힌 문 | ★★★ **`virtual` 없이 `override` 하면 `CS0506`** | (2) |
| 팻말만 세우기 | ★★★ **`new` 는 정적 타입으로만 갈린다** | (1)(6) |
| 팻말을 안 세우면 잔소리 | ★★ **`CS0108`(비가상) / `CS0114`(가상)** — **둘이 다르다** | (3) |
| 뒷문으로 들어오면 원래 문 | ★★★ **인터페이스로 부르면 `new` 가 안 보인다** | (6) |
| 문틀만 있는 것 | **`abstract`** — 건물 자체를 못 짓는다(`CS0144`) | (7) |
| 열쇠를 잠그는 것 | **`sealed override`**(`CS0239`) · **`sealed class`**(`CS0509`) | (7) |

> **정적 타입(static type)** — **변수에 적힌 타입.** 컴파일러가 보는 것.\
> **동적 타입(dynamic type)** — **그 변수가 실제로 가리키는 객체의 타입.** 런타임이 보는 것.\
> ★★★ **이 주제 전체가 「어느 쪽이 정하나」를 묻는다.**

> ★★ **한국어 「숨김」이 둘을 가리킨다.** 이 문서에서 **숨김**은 언제나 **`new` 한정자로 가리는 것**(hiding)이다.\
> **접근 한정자로 안 보이게 하는 것**([15번](../15-access-modifiers-and-assembly-boundary/))은 「**안 보임**」이라고만 적는다.

★★★ **이 주제의 본체 그림 — 정적 타입 × 동적 타입 격자.**

```text
                        ┌──────────── 동적 타입(실제 객체) ────────────┐
                        │      Base              │     Derived        │
   ┌────────────────────┼────────────────────────┼────────────────────┤
 정│  Base              │  Plain: Base.Plain     │  Plain: Base.Plain │  ← ★ new 는 안 보인다
 적│  (Base b = …)      │  Virt : Base.Virt      │  Virt : Derived.Virt│
   ├────────────────────┼────────────────────────┼────────────────────┤
 타│  Derived           │      (불가능)           │  Plain: Derived.Plain│ ← ★ new 가 보인다
 입│  (Derived d = …)   │                        │  Virt : Derived.Virt│
   └────────────────────┴────────────────────────┴────────────────────┘

   ★★★ Virt 행은 「동적 타입」만 본다   — override
   ★★★ Plain 행은 「정적 타입」만 본다  — new
```

- ★★★ **이 격자 하나가 이 주제의 답 전부다.** (1)이 그것을 **실제 출력으로** 찍는다.

## 이 주제가 답하려는 질문

1. **`new` 와 `override` 의 호출 결과가 어떻게 갈리나** — **정적 타입 × 동적 타입 격자**로((1)(6)).
2. **C# 이 기본 비가상인데 왜 IL 은 `callvirt` 를 쓰나**((4)).
3. **컴파일러가 무엇을 막고 무엇을 경고만 하나**((2)(3)(7)(10)).
4. **인터페이스의 기본 구현은 클래스로 내려오나**((8)).
5. **Java·C++ 와 어디가 갈리나**((9)).

## 동작 방식

### (0) 이 주제가 쓰는 창

| 창 | 무엇을 보여 주나 | 이 주제에서 |
|---|---|---|
| ★★★ **① IL 덤프** | ★★★ **`callvirt` 대 `call`** — 이 주제의 본체 | (4)(5) |
| ★★★ **실행 출력 격자** | ★★★ **정적 × 동적 아홉 칸** — 결론 자체 | (1)(6)(8)(9) |
| ★★ **② 진단 격자** | 막는 것과 경고만 하는 것 | (2)(3)(7)(10) |
| ★★ **③ 리플렉션** | ★★★ **명시적 구현이 `private`+`final`+`virtual`** · 인터페이스 맵 | (8) |
| ★ **④ 할당 바이트** | ★★ **부적용** — 아래 | — |

- ★★★ **본체는 ① IL 덤프다.** (4)의 「기본 비가상인데 왜 `callvirt` 인가」는 **덤프 없이는 물을 수조차 없다.**\
  덤프는 [03번](../03-boxing-and-unboxing/)이 만든 디스어셈블러를 그대로 쓴다 — **외부 도구가 0개**다.
- ★★★ **실행 출력 격자가 짝이다.** IL 만 보면 「`callvirt` 니까 다 가상이겠네」로 **틀린 결론**이 나온다.\
  **격자를 값으로 찍어야** `new` 가 정적 타입으로 갈리는 것이 보인다.
- ★★ **③ 리플렉션이 (8) 하나를 맡는다** — 명시적 인터페이스 구현은 **C# 소스에 한정자를 못 적는데**\
  메타데이터에는 `private`·`final`·`virtual` 이 **한꺼번에** 박혀 있다. 소스로는 못 읽는 것을 리플렉션이 읽는다.
- ★★ **「부적용인 창」 — ④ 할당 바이트.** `new` 로 숨기든 `override` 하든 **객체는 하나**이고 크기가 같다.\
  `virtual` 을 붙인다고 객체에 무엇이 더 붙지도 않는다(메서드 테이블은 **타입당 하나**다).\
  ★★★ **「재 봤더니 같았다」가 아니라 「잴 것이 없다」다**(규칙 18-B).
- ★★★ **그래서 이 문서에는 「가상 호출이 비가상 호출보다 느리다」는 문장이 한 줄도 없다.**\
  (4)의 덤프가 보여 주는 것은 **옵코드 이름**이지 **비용**이 아니다. 비용을 재려면 JIT 의 인라인·디버추얼라이제이션을\
  관찰해야 하고, **이 판에서 그 하네스를 안 만들었다.**

### (1) ★★★ 정적 타입 × 동적 타입 격자 — 실제 출력

**언제 쓰나** — 상속이 있는 코드를 읽을 때마다. **이 절이 이 주제의 중심이다.**

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

- ★★★ **`Virt` 열은 동적 타입만 본다.** `Base bd = new Derived()` 에서 **`Derived.Virt`** 가 나왔다.
- ★★★ **`Plain` 열은 정적 타입만 본다.** 같은 객체인데 **`Base.Plain`** 이 나왔다.\
  `Derived d` 로 받으면 `Derived.Plain` 이고, **`((Base)d)` 로 캐스트하면 다시 `Base.Plain`** 이다.
- ★★★ **네 번째 줄이 결정적이다.** **객체는 한 번도 안 바뀌었는데 캐스트 한 번에 답이 바뀐다** —\
  `new` 로 숨긴 것은 **객체의 성질이 아니라 이름 해석의 성질**이라는 뜻이다.
- ★★ **`Virt` 는 네 줄에서 두 가지 값만 나온다**(`Base.Virt`·`Derived.Virt`), 그리고 **객체가 같으면 값이 같다.**\
  **`Plain` 은 객체가 같아도 값이 갈린다.** 이 비대칭이 이 주제의 전부다.

> **어느 층인가** — ★★★ **전부 명세다.** ECMA-334 는 `new` 를 **이름 숨기기**로, `override` 를 **가상 디스패치**로 정의한다.\
> **런타임이 정하는 것이 아니다** — `Plain` 의 답은 **컴파일 시점에 이미 결정돼 IL 에 박힌다**((5)).

### (2) ★★★ `virtual` 없이 `override` 하면 — 기본 비가상의 증거

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

- ★★★ **`CS0506: cannot override inherited member 'Base.Plain()' because it is not marked virtual, abstract, or override`.**\
  **이 한 줄이 「C# 은 기본 비가상」의 정본 증거다.** 한정자를 안 적은 메서드는 **열려 있지 않다.**
- ★★ **`CS0238` — `sealed` 는 `override` 위에만 붙는다.** `public sealed string Odd()` 는 거절된다.\
  ★ **잠글 것이 없는데 잠글 수 없다** — 원래 닫혀 있기 때문이다.\
  ★★★ **이 두 진단이 한 쌍으로 「기본값이 닫힘」을 말한다.**
- ★ `cc exit=1` 이다.

### (3) ★★ `new` 를 안 적으면 — 경고 코드가 **둘로 갈린다**

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

- ★★★ **`CS0108`(비가상) 과 `CS0114`(가상) 는 다른 코드다.**
  - **`Plain`**(기반이 비가상) → **`CS0108`** — 「숨긴다. 의도했으면 `new` 를 쓰라」.
  - **`Virt`**(기반이 **가상**) → **`CS0114`** — 「숨긴다. **재정의하려면 `override`**, 아니면 `new` 를 쓰라」.\
    ★★★ **선택지를 둘 제시한다** — 기반이 가상일 때만 `override` 가 후보이기 때문이다.
- ★★★ **필드도 숨겨진다** — `Tag` 에 `CS0108` 이 났다. **`new` 는 메서드 전용이 아니다.**
- ★★★ **셋 다 경고이고 `cc exit=0` 이다.** **컴파일은 성공한다.**\
  ★ 경고를 끄고 지나가면 **(1)의 격자가 조용히 적용된다** — 이 주제에서 가장 나쁜 자리다.
- ★★ **「`CS0108` 만 있다」고 외우면 틀린다** — 실제로 마주치는 것은 대개 `CS0114` 쪽이다.\
  ★ 기반을 가상으로 열어 둔 라이브러리를 쓸 때 나오기 때문이다.

### (4) ★★★ 기본 비가상인데 왜 `callvirt` 가 나오나

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

- ★★★ **여섯 탐침 중 넷이 `callvirt` 다** — `Plain`(비가상) 까지 포함해서.\
  **「`callvirt` = 가상 호출」이 아니다.**
- ★★★ **`call` 이 나온 자리는 셋뿐이다.**

| 탐침 | 무엇을 불렀나 | 옵코드 | 왜 |
|---|---|---|---|
| A | 비가상 인스턴스 메서드 | **`callvirt`** | ★★★ 널 검사 때문 |
| B | 가상 메서드 | **`callvirt`** | 진짜 가상 디스패치 |
| C | `sealed` 타입의 가상 메서드 | **`callvirt`** | ★ 컴파일러는 여기서도 안 바꾼다 |
| D | `sealed` 타입의 비가상 메서드 | **`callvirt`** | 널 검사 |
| E | **정적** 메서드 | **`call`** | 수신자가 없다 — 널일 수 없다 |
| F | **구조체**의 메서드 | **`call`** | 값 타입이라 널일 수 없다 |
| `Child.Virt` | ★★ **`base.Virt()`** | **`call`** | ★★★ **`base` 는 비가상 호출을 명시하는 것** |

- ★★★ **답은 널 검사다.** ECMA-335 의 `callvirt` 는 **수신자가 `null` 이면 `NullReferenceException` 을 던진다.**\
  `call` 은 그 검사를 **안 한다** — `this` 가 널인 채로 메서드 본문에 들어간다.\
  ★★ C# 컴파일러는 「**널 참조로 메서드를 부르면 반드시 예외가 난다**」를 보장하고 싶어서\
  **비가상 메서드에도 `callvirt` 를 쓴다.**
- ★★★ **`E`·`F` 가 그 설명을 확증한다** — **널일 수 없는 두 자리에서만 `call` 이 나왔다.**\
  ★ 정적 메서드는 수신자가 없고, 구조체 메서드는 `ldarga.s`(주소 싣기)로 부르므로 **널이 원리상 불가능**하다.
- ★★★ **`base.Virt()` 가 `call` 인 것**이 네 번째 증거다 — 여기서는 **널 검사보다 「가상 디스패치를 하지 마라」가 우선**이다.\
  `callvirt` 를 쓰면 **`Child.Virt` 가 자기 자신을 불러 무한 재귀**가 된다.
- ★★ **탐침 C 가 재미있다** — 타입이 `sealed` 라 **재정의될 수 없는데도** `callvirt` 다.\
  ★★★ **그 최적화는 컴파일러가 아니라 JIT 이 한다**(디버추얼라이제이션). **IL 층에서는 안 바꾼다.**
- ★★★ **널 검사 주장을 값으로 확인한다.**

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

- ★★★ **`Plain()` 은 `this` 를 한 번도 안 쓰는 비가상 메서드**다. 그런데 **본문에 못 들어간다** —\
  「본문에 들어왔다」가 안 찍히고 `NullReferenceException` 이 잡혔다.\
  ★★★ **`call` 이었다면 본문이 돌았을 것**이다. **`callvirt` 가 부르기 전에 막은 것**이다.
- ★★ **구분 마커를 표준 오류로 찍었다**(규칙 18) — `Console.Error` 라야 순서가 고정된다.

> **어느 층인가** — ★★★ 「**C# 이 기본 비가상**」은 **ECMA-334**(언어)이고,\
> ★★★ 「**`callvirt` 가 널 검사를 한다**」는 **ECMA-335**(CLI)다. **두 명세가 다른 층**이라 모순이 아니다.\
> ★★ **「비가상 호출에도 `callvirt` 를 쓴다」는 Roslyn 의 선택**이다 — 명세가 강제하지 않는다.

### (5) ★ `base.M()` — 사슬이 어떻게 도나

```text
===== 소스: cs16b-base.cs =====
using System;
class A     { public virtual  string Chain() => "A"; }
class B : A { public override string Chain() => base.Chain() + "→B"; }
class C : B { public override string Chain() => base.Chain() + "→C"; }
class Program {
    static void Main() {
        A a = new C();
        Console.WriteLine($"정적 A · 동적 C : {a.Chain()}");
        Il.Dump(typeof(C), "Chain");
    }
}
===== csc -r:il.dll -out:ex.dll cs16b-base.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
정적 A · 동적 C : A→B→C
--- C.Chain ---
  IL_0000: ldarg.0
  IL_0001: call B::Chain
  IL_0006: ldstr "→C"
  IL_000b: call System.String::Concat
  IL_0010: ret
```

- ★★★ **`A→B→C` 가 찍혔다.** `a.Chain()` 이 `C.Chain` 으로 디스패치되고(동적 타입),\
  그 안의 `base.Chain()` 이 `B.Chain` 을 **비가상으로** 부르고, 다시 `A.Chain` 을 부른다.
- ★★★ **IL 이 `call B::Chain` 이다.** `callvirt` 가 아니다 —\
  ★ `callvirt` 였다면 **동적 타입이 `C` 이므로 `C.Chain` 이 다시 불려 무한 재귀**가 된다.
- ★★ **`base` 는 「한 단계 위」만 가리킨다.** `C` 에서 `A.Chain` 을 직접 부를 방법은 **없다** —\
  `B` 가 `base` 를 안 부르면 `A` 는 영영 안 돈다. ★ **그것이 (10) 탐침 6 의 자리다.**

### (6) ★★★ `new` 로 숨긴 것을 인터페이스로 부르면

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

- ★★★ **`((IRun)h).Go()` 가 `Base.Go` 다.** `Hider` 로 직접 부르면 `Hider.Go` 인데,\
  **인터페이스로 부르면 `new` 가 안 보인다.**
- ★★★ **`Rider`(override)는 어느 쪽으로 불러도 `Rider.Go` 다.**
- ★★★ **왜 그런가** — 인터페이스 구현은 **`Base` 가 했다.** `IRun.Go` 의 슬롯에는 `Base.Go` 가 들어 있고,\
  `Hider.Go` 는 **그 슬롯을 건드리지 않는 새 메서드**다. `Rider.Go` 는 **그 슬롯을 덮어썼다.**
- ★★★ **이것이 `new` 가 위험한 진짜 이유다.** (1)의 격자는 「캐스트하면 달라진다」로 끝나는데,\
  **인터페이스를 거치는 코드는 캐스트를 안 쓴다** — LINQ·DI 컨테이너·컬렉션이 전부 인터페이스로 받는다.\
  ★ 그런 코드에서는 **`new` 로 만든 메서드가 영영 안 불린다.**

```text
   Base 의 메서드 슬롯 표             Hider                       Rider
   ┌──────────────┐                 ┌──────────────┐            ┌──────────────┐
   │ [0] Go  ────────> Base.Go      │ [0] Go  ────────> Base.Go  │ [0] Go ───────> Rider.Go  ← 덮어씀
   └──────────────┘                 │ (새 메서드)  ──> Hider.Go   └──────────────┘
          ↑                         └──────────────┘
   IRun.Go 가 가리키는 자리            ★ 슬롯은 그대로다

   ★★★ 인터페이스는 슬롯을 본다. new 로 만든 메서드는 슬롯 밖에 있다.
```

### (7) ★ `abstract` 와 `sealed`

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

- ★★★ **`CS0534` — 추상 멤버를 구현 안 하면 파생 클래스 선언 자체가 막힌다.** 빠진 멤버마다 한 건씩이다.
- ★★ **`CS0500` — `abstract` 에 본문을 못 둔다.** 「문틀만」이라는 뜻이 진단으로 나온다.
- ★★★ **`CS0144` — 추상 타입은 `new` 로 못 만든다.** `new Circle()` 은 통과하고 `new Shape()` 만 막힌다.\
  ★ **`Shape ok = new Circle()` 이 조용한 것**이 대비다 — **변수 타입은 추상이어도 된다.**
- ★★★ **`CS0239` — `sealed override` 는 사슬을 거기서 닫는다.** `C` 가 더는 못 연다.\
  ★ 즉 **`virtual` 로 연 문을 중간에서 다시 잠글 수 있다.**
- ★★ **`CS0509` — `sealed class` 는 상속 자체가 막힌다.** 멤버 단위가 아니라 **타입 단위**다.
- ★ **`sealed` 의 두 쓰임이 다른 진단으로 갈린다** — 메서드는 `CS0239`, 클래스는 `CS0509`.

### (8) ★★ 명시적 인터페이스 구현 · 인터페이스 기본 구현

먼저 **명시적 구현이 무엇이 되나.**

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

- ★★★ **`private=True final=True virtual=True`** — 세 플래그가 **한꺼번에** 박힌다.\
  ★ **C# 소스에는 한정자를 하나도 못 적는데** 메타데이터에는 셋이 다 있다.
  - **`private`** — 클래스 이름으로는 못 부른다. **캐스트해야** 한다.
  - **`virtual`** — 인터페이스 디스패치가 **슬롯을 거쳐야** 하므로 가상이어야 한다.
  - **`final`** — 파생이 `override` 로 덮을 수 없다(**다시 명시적으로 구현해야** 한다).
- ★★★ **이름이 `IWalk.Move` 다** — 점이 들어간 이름은 **C# 에서 선언할 수 없는 이름**이라 충돌이 원리상 없다.
- ★★ **그래서 같은 시그니처의 인터페이스 둘을 한 클래스가 구현할 수 있다** — `IWalk.Move` 와 `ISwim.Move` 가 공존한다.\
  ★ [15번](../15-access-modifiers-and-assembly-boundary/)의 여섯 한정자로는 설명이 안 되는 **일곱 번째 자리**다.

다음은 **유명한 함정.**

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

- ★★★ **`p.Hello()` 가 `CS1061` 로 막힌다.** 「`Plain` 에 `Hello` 라는 정의가 **없다**」.\
  **인터페이스의 기본 구현은 클래스로 상속되지 않는다.**
- ★★★ **`i.Hello()` 는 돌아간다.** 같은 객체인데 **변수 타입이 인터페이스면 되고 클래스면 안 된다.**
- ★★★ **리플렉션이 이유를 적는다** — **`Plain` 이 선언한 인스턴스 메서드가 0 개**이고,\
  **인터페이스 맵의 `Hello` 가 `IGreet.Hello` 를 가리킨다.**\
  ★ **`Plain` 에는 그 메서드가 정말로 없다** — 「보이는데 막힌 것」이 아니다.\
  ★★ [15번](../15-access-modifiers-and-assembly-boundary/) (3)의 `CS1061` 과 같은 성격의 「**없음**」이다.
- ★★ **왜 이렇게 설계했나** — 기본 구현이 클래스로 내려오면 **다중 상속의 충돌 문제**가 그대로 들어온다.\
  인터페이스 둘이 같은 이름의 기본 구현을 주면 클래스가 어느 것을 쓸지 정할 수 없다.\
  ★ 그래서 **인터페이스 타입으로 부를 때만** 쓰이게 막았다.
- ★★★ **(9)에서 Java 와 정면으로 갈린다** — Java 의 `default` 메서드는 **클래스로 내려온다.**

```text
   C#                                   Java
   interface IGreet {                   interface IGreet {
       string Hello() => "…";               default String hello() { … }
   }                                    }
   class Plain : IGreet { }             class Plain implements IGreet { }

   new Plain().Hello()   → CS1061 ✕     new Plain().hello()   → 돈다 ○
   ((IGreet)p).Hello()   → 돈다 ○        ((IGreet)p).hello()  → 돈다 ○

   ★★★ 같은 기능처럼 보이는데 「클래스로 내려오나」가 정반대다.
```

### (9) ★★★ Java·C++ 와 대비 — 세 언어의 기본값

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

- ★★★ **Java 는 한정자 없는 메서드가 그대로 재정의된다.** `Derived.plain` 이 **`Base` 변수로도 불렸다** —\
  **`-Xlint:all` 에서 경고가 한 줄도 안 났다.** C# 이라면 `CS0108` 이 났을 자리다.
- ★★★ **Java 에서 메서드를 「숨기는 것」은 불가능하다.** 같은 시그니처를 쓰면 **무조건 재정의**다.\
  닫으려면 **`final`** 을 적어야 하고, 그것을 덮으려 하면 **`shut() in Picker cannot override shut() in Locked`** 로 막힌다.
- ★★★ **필드는 세 언어가 같다** — Java 에서도 `bd.tag` 가 **1**(Base 의 것) 이다.\
  ★★ **「메서드는 재정의되고 필드는 숨겨진다」는 비대칭이 Java 에도 그대로 있다.**\
  ★ C# 은 그 비대칭이 **메서드에도** 있는 것이고(기본 비가상), Java 는 **필드에만** 있다.
- ★★★ **C++ 은 기본 비가상인 점이 C# 과 같은데 `new` 같은 키워드가 없다.**\
  `Derived::plain` 이 `Base::plain` 을 가리는데 **`-Wall -Wextra -Woverloaded-virtual` 에서 경고가 0건**이다.\
  ★★★ **C# 은 잔소리를 하고 C++ 은 조용하다** — 같은 기본값에서 **도구의 태도가 갈린다.**
- ★★ **C++ 의 `override` 는 「덮는다」가 아니라 「덮는지 검사하라」다.**\
  `virtual` 이 아닌 것에 `override` 를 적으면 **`marked 'override', but does not override`** 로 막힌다.\
  ★ C# 의 `CS0506` 과 **같은 일을 하는데 낱말의 뜻이 다르다** — C# 의 `override` 는 **선언**이고 C++ 의 것은 **검사**다.
- ★ **재검증 방식이 다르다** — **g++ 와 javac 는 소스 줄과 캐럿을 끼워 준다.**\
  **C# 진단은 `(행,열)` 만** 주므로 **소스 배너를 같은 블록에 싣는 것**이 필수다.

### (10) ★★ 컴파일러가 무엇을 안 보나 — 탐침 여덟

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

- ★★★ **탐침 여덟 중 진단이 붙은 줄은 다섯**이다. 스크립트가 직접 세어 마지막 줄에 찍었다(`5`).

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
  생성자에서 가상 메서드를 부르면 **파생 것이 불리고**, 그때 **파생 필드가 아직 안 채워져 `FromBody=null`** 이었다.\
  ★★★ **12편은 `-warn:9` 탐침 여섯에서 경고 0건**이었고, **이번 판에서도 여전히 침묵**이다.\
  ★★★ **이 갈래에서 같은 결론이 두 번 확인됐다** — 컴파일러는 「형태」만 보고 「순서 사고」는 안 본다.
- ★★ **탐침 6 도 침묵이다** — `override` 가 `base` 를 안 불러 기반의 초기화가 통째로 빠져도 말이 없다.\
  ★ (5)에서 봤듯 **`base` 는 사슬이라 한 군데만 끊겨도 아래가 다 안 돈다.**
- ★★ **탐침 2 의 `CS0109` 가 반가운 자리다** — **쓸데없는 `new` 를 알려 준다.**\
  ★ 기반에서 메서드를 지웠는데 파생의 `new` 가 남아 있는 상황이 그것이다.
- ★★ **탐침 5 의 `CS0628`** — `sealed` 클래스에 `protected` 를 두면 **볼 사람이 없다.**\
  ★ 이 주제([16번](../16-inheritance-virtual-override-abstract-sealed-new/))와 [15번](../15-access-modifiers-and-assembly-boundary/)이 만나는 유일한 진단이다.
- ★ **탐침 7 이 침묵인 것은 정상이다** — 중간 클래스가 아무것도 안 하는 것은 **흔하고 올바른 설계**다.

## 문법 — 형태와 규칙

### 형태

```csharp
// cs16b-form.cs
using System;

Console.WriteLine(new Circle(2).Describe());
Console.WriteLine(((IShape)new Circle(2)).Tag());

interface IShape { string Tag() => "인터페이스 기본 구현"; }

abstract class Shape : IShape {                      // abstract — 직접 못 만든다
    public abstract double Area();                   // 파생이 반드시 구현한다
    public virtual  string Name() => "도형";          // 열어 둔다
    public          string Id()   => "#";            // 기본 비가상 — 닫혀 있다
    string IShape.Tag() => "명시적 구현 — private 이다";
    public string Describe() => $"{Name()}({Area():0.0}){Id()}";
}
class Circle(double r) : Shape {
    public override double Area()  => 3.14 * r * r;
    public sealed  override string Name() => "원";    // 여기서 사슬을 닫는다
    public new     string Id()   => "@";             // 숨긴다 — Describe 는 못 본다
}
```

```text
===== 소스: cs16b-form.cs =====
using System;

Console.WriteLine(new Circle(2).Describe());
Console.WriteLine(((IShape)new Circle(2)).Tag());

interface IShape { string Tag() => "인터페이스 기본 구현"; }

abstract class Shape : IShape {                      // abstract — 직접 못 만든다
    public abstract double Area();                   // 파생이 반드시 구현한다
    public virtual  string Name() => "도형";          // 열어 둔다
    public          string Id()   => "#";            // 기본 비가상 — 닫혀 있다
    string IShape.Tag() => "명시적 구현 — private 이다";
    public string Describe() => $"{Name()}({Area():0.0}){Id()}";
}
class Circle(double r) : Shape {
    public override double Area()  => 3.14 * r * r;
    public sealed  override string Name() => "원";    // 여기서 사슬을 닫는다
    public new     string Id()   => "@";             // 숨긴다 — Describe 는 못 본다
}
===== csc -out:ex.dll cs16b-form.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
원(12.6)#
명시적 구현 — private 이다
```

- ★★★ **출력의 첫 줄이 `원(12.6)#` 이다.** `Describe()` 안에서 `Name()` 은 **`원`**(가상이라 파생 것) 인데\
  `Id()` 는 **`#`**(비가상이라 `Shape` 것) 이다. ★ **`Circle.Id` 는 `new` 라 `Describe` 에서 안 보인다.**\
  **(1)의 격자가 한 줄 안에서 동시에 일어난 것**이다.
- ★★★ **둘째 줄이 `명시적 구현 — private 이다` 다.** 인터페이스 기본 구현이 있는데도\
  **`Shape` 의 명시적 구현이 이긴다** — 클래스가 구현하면 기본 구현은 안 쓰인다.
- **`virtual` 없이는 `override` 를 못 쓴다**((2)).
- **`sealed` 는 `override` 위에만 붙는다**((2)(7)).
- **`abstract` 멤버는 `abstract` 클래스에만 둘 수 있고 본문을 못 가진다**((7)).
- **`new` 는 메서드·필드·속성·타입에 다 붙는다**((3)).

### 금지 사례 — 진단이 나는 꼴

| 쓴 꼴 | 진단 코드 | 어디서 |
|---|---|---|
| `virtual` 아닌 것을 `override` | `CS0506`(에러) | (2) — ★ **기본 비가상의 정본 증거** |
| `override` 아닌 것에 `sealed` | `CS0238`(에러) | (2) |
| 기반의 **비가상** 멤버를 `new` 없이 다시 선언 | `CS0108`(**경고**) | (3)(10) |
| 기반의 **가상** 멤버를 `override`·`new` 없이 다시 선언 | `CS0114`(**경고**) | (3) |
| 숨길 것이 없는데 `new` | `CS0109`(**경고**) | (10) |
| `sealed override` 를 다시 `override` | `CS0239`(에러) | (7) |
| `sealed class` 를 상속 | `CS0509`(에러) | (7) |
| `abstract` 멤버에 본문 | `CS0500`(에러) | (7) |
| `abstract` 멤버를 구현 안 함 | `CS0534`(에러) | (7) |
| `abstract` 타입을 `new` | `CS0144`(에러) | (7) |
| 클래스 변수로 인터페이스 기본 구현 호출 | `CS1061`(에러) | (8) |
| `Equals` 만 덮음 | `CS0659`(**경고**) | (10) |
| `sealed` 클래스에 `protected` 멤버 | `CS0628`(**경고**) | (10) |

★★★ **에러와 경고의 선이 이 표의 요점이다** — **`new`/`override` 를 빠뜨린 것은 전부 경고**다.\
컴파일은 통과하고 **(1)의 격자가 조용히 적용된다.**

## 어디서 틀리나

1. ★★★ **「파생에서 같은 이름을 쓰면 재정의된다」** — C# 에서는 **아니다**((1)(2)).\
   Java 를 먼저 배운 사람이 반드시 걸리는 자리다((9)).
2. ★★★ **「`callvirt` 니까 가상 호출이다」** — **비가상 메서드도 `callvirt` 다**((4)).\
   이유는 **널 검사**이고, `call` 이 나오는 곳은 **정적·구조체·`base`** 셋뿐이다.
3. ★★★ **「`new` 로 숨긴 것도 결국 불린다」** — **인터페이스로 부르면 영영 안 불린다**((6)).\
   LINQ·DI·컬렉션이 전부 인터페이스로 받는다.
4. ★★★ **「인터페이스 기본 구현은 클래스가 물려받는다」** — **안 받는다**((8)). `CS1061` 이다.\
   ★ Java 의 `default` 메서드와 **정반대**다((9)).
5. ★★ **「`new` 를 빠뜨리면 `CS0108` 하나」** — **기반이 가상이면 `CS0114`** 다((3)). 문구도 다르다.
6. ★★ **「경고니까 괜찮다」** — (1)의 격자가 **조용히 적용된다.** 이 주제의 경고는 전부 **설계 사고의 신호**다.
7. ★★ **「생성자에서 가상 메서드를 부르면 컴파일러가 잡아 준다」** — **안 잡는다**((10) 탐침 3).\
   [12번](../12-class-fields-constructors-this-base/) (4)가 **값으로** 잡은 함정이고, **이번 판에서도 여전히 침묵**이다.
8. ★★ **「명시적 인터페이스 구현은 그냥 부를 수 있다」** — **`private` 이라 캐스트해야** 한다((8)).
9. ★ **「`sealed` 는 클래스에만 쓴다」** — **`sealed override`** 로 **사슬 중간을 닫는** 쓰임이 있다((7)).
10. ★ **「C++ 도 기본 비가상이니 C# 과 같다」** — **C++ 은 숨겨도 경고가 없다**((9)).\
    같은 기본값인데 **도구의 태도가 다르다.**

## 구현 세부사항 대 언어 보장

| 무엇 | 층 | 근거 |
|---|---|---|
| **기본 비가상** | ★★★ **언어 보장(334)** | (2) `CS0506` |
| **`new` 가 정적 타입으로 갈리는 것** | ★★★ **언어 보장(334)** | (1) 격자 |
| **`override` 가 동적 타입으로 갈리는 것** | ★★★ **언어 보장(334)** | (1) 격자 |
| **인터페이스 기본 구현이 클래스로 안 내려오는 것** | ★★★ **언어 보장(334, C# 8)** | (8) `CS1061` |
| **명시적 구현이 `private` 인 것** | ★★★ **언어 보장(334)** | (8) |
| **`callvirt` 가 널 검사를 하는 것** | ★★★ **CLI 보장(335)** | (4) — **언어가 아니라 런타임 층** |
| **비가상 호출에도 `callvirt` 를 쓰는 것** | ★★ **구현(Roslyn)** | (4) — 명세가 강제하지 않는다 |
| **`sealed` 타입에서도 `callvirt` 인 것** | ★★ **구현(Roslyn)** | (4) — 최적화는 JIT 의 몫 |
| **명시적 구현에 `final`+`virtual` 이 같이 박히는 것** | ★★ **구현(Roslyn+CLI)** | (8) |
| **`-warn:9` 에서 탐침 여덟 중 다섯만 답하는 것** | ★ **이 판의 관찰** | (10) — 다음 판에서 늘 수 있다 |
| **진단 문구 전부** | ★ **이 판의 관찰** | 근거로는 **코드와 `(행,열)`** 만 쓴다 |

## 언제 쓰고 언제 안 쓰나

- ★★★ **`virtual` 은 「일부러 여는 것」이다.** C# 의 기본값이 닫힘인 것은 **설계 의도**다 —\
  열린 문은 **계약**이 된다. 파생이 무엇을 깨뜨릴 수 있는지 생각하고 열어라.
- **`abstract`** — 「기반은 이 일을 할 줄 모른다」가 사실일 때. 기본 구현을 억지로 만들지 마라.
- **`sealed class`** — 상속을 **설계하지 않은** 클래스에. ★ 열어 두는 것이 공짜가 아니다.
- **`sealed override`** — 사슬을 여기서 끝내고 싶을 때. **깊은 상속 사슬의 예측 불가를 줄인다.**
- ★★★ **`new` 는 거의 언제나 쓰지 마라.** (6)에서 봤듯 **인터페이스를 거치는 순간 무력해진다.**\
  ★ 정당한 자리는 하나뿐이다 — **내가 못 고치는 기반 클래스가 나중에 같은 이름의 멤버를 추가했을 때**\
  이름을 안 바꾸고 넘어가는 것. **그때조차 `CS0108` 을 보고 의식적으로 적어야** 한다.
- ★★ **생성자에서 가상 메서드를 부르지 마라** — [12번](../12-class-fields-constructors-this-base/) (4)가 값으로, 여기 (10)이 침묵으로 확인했다.
- ★★ **`protected` 와 `virtual` 은 함께 설계한다** — 확장점은 **보이는 것**과 **바꿀 수 있는 것**이 둘 다 필요하다([15번](../15-access-modifiers-and-assembly-boundary/)).

## 핵심 문장

1. ★★★ **C# 은 기본 비가상이다.** `virtual` 없이 `override` 하면 `CS0506` 이다((2)).
2. ★★★ **`override` 는 동적 타입이 정하고 `new` 는 정적 타입이 정한다.** 객체가 같아도 캐스트로 답이 바뀐다((1)).
3. ★★★ **`callvirt` 는 「가상」이 아니라 「널 검사」다.** `call` 은 **정적·구조체·`base`** 세 자리에만 나온다((4)).
4. ★★★ **인터페이스 기본 구현은 클래스로 안 내려온다** — `CS1061`((8)). **Java 와 정반대**((9)).
5. ★★ **`new`/`override` 를 빠뜨린 것은 전부 경고다.** 컴파일은 통과하고 격자가 조용히 적용된다((3)).

## 관련 자료

- [12번 — 클래스·필드·생성자·`this`/`base`](../12-class-fields-constructors-this-base/) — **초기화 순서**와 **생성자 속 가상 호출**의 정본.\
  ★★★ 거기서 **생성자가 부른 가상 메서드가 파생 것을 불러 `FromBody=null`** 이 된 것을 값으로 잡았다.\
  **여기서는 그 함정에 컴파일러가 여전히 침묵한다는 것만 다시 확인**했다((10)).
- [13번 — 속성](../13-properties-init-required-field/) — 속성도 `virtual`/`override` 가 붙는다. **접근자 접근성**은 그쪽 (6)이 정본.
- [14번 — 인덱서](../14-indexers/) — **명시적 인터페이스 구현 인덱서**((4))가 이 주제 (8)의 규칙을 따른다.
- [15번 — 접근 한정자와 어셈블리 경계](../15-access-modifiers-and-assembly-boundary/) — **`protected` 의 경계**와\
  ★ **명시적 구현이 여섯 한정자로 설명 안 되는 일곱 번째 자리**라는 것.
- [03번 — 박싱과 언박싱](../03-boxing-and-unboxing/) — 이 문서가 쓰는 **IL 디스어셈블러를 만든 곳**이다.
- 목록의 **17번 주제**(인터페이스·기본 구현·명시적 구현) — **인터페이스 설계 전반**은 그쪽이 정본이다.\
  여기서는 **상속과 부딪히는 자리**((6)(8))만 봤다.
- [`oop-basics/`](../../../../oop-basics/) — **상속·다형성 개념**은 거기, 여기는 **C# 의 기본값**.
- Java 갈래 목록([`java/syntax/README.md`](../../../java/syntax/README.md))의 **09번**([`09-inheritance-overriding/`](../../../java/syntax/09-inheritance-overriding/))·**11번**([`11-interfaces-default-methods/`](../../../java/syntax/11-interfaces-default-methods/)) — **직접 대비**((9)).
- C++ 갈래 목록([`cpp/syntax/README.md`](../../../cpp/syntax/README.md))의 **19번** — 기본 비가상인데 숨김 키워드가 없다((9)).

## 용어 풀이

- **정적 타입(static type)** — 변수에 적힌 타입. 컴파일러가 보는 것.
- **동적 타입(dynamic type)** — 변수가 실제로 가리키는 객체의 타입. 런타임이 보는 것.
- **가상 디스패치(virtual dispatch)** — 동적 타입을 보고 어느 구현을 부를지 런타임이 고르는 것.
- **숨김(hiding)** — `new` 한정자로 기반의 멤버를 가리는 것. **접근 한정자의 「안 보임」과 다른 말이다.**
- **`callvirt`** — CLI 옵코드. **수신자 널 검사 + (가상이면) 가상 디스패치.** 비가상 메서드에도 쓰인다.
- **`call`** — CLI 옵코드. **널 검사도 가상 디스패치도 안 한다.** 정적·구조체·`base` 에 쓰인다.
- **디버추얼라이제이션(devirtualization)** — JIT 이 가상 호출을 직접 호출로 바꾸는 최적화. **IL 층이 아니다.**
- **기본 구현 멤버(default interface member)** — 인터페이스가 본문을 가진 멤버(C# 8). **클래스로 안 내려온다.**
- **명시적 인터페이스 구현(explicit interface implementation)** — `string IWalk.Move() => …` 꼴.\
  메타데이터에 `private`+`final`+`virtual` 이 한꺼번에 박힌다.

## 더 들어가면

- ★ **왜 C# 은 기본을 닫았나** — 「**상속은 설계해야 한다**」는 입장이다.\
  기반 클래스를 고쳤을 때 파생이 조용히 깨지는 문제(fragile base class)를 **기본값으로** 줄인다.\
  ★★★ 그 대가가 **`new` 라는 키워드가 필요해진 것**이고, (6)에서 봤듯 **그 키워드가 반쪽짜리**다.
- ★ **JIT 의 디버추얼라이제이션** — `sealed` 타입이나 파생이 로드되지 않은 타입의 가상 호출을\
  런타임이 직접 호출로 바꾼다. ★★★ **이 판에서 안 관찰했다** — JIT 덤프 하네스가 따로 필요하다.\
  그래서 이 문서에 **속도에 관한 문장이 한 줄도 없다.**
- ★ **`new` 가 붙은 멤버의 메타데이터** — IL 에는 `newslot` 이라는 플래그가 있다.\
  ★★★ **이 판에서 그 플래그를 직접 안 찍었다** — 리플렉션의 `MethodAttributes` 로 볼 수 있지만 (8)에서는\
  명시적 구현만 찍었다. **다음 판에서 물을 자리다.**
