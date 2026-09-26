# csharp/syntax/17 — 인터페이스·기본 구현 멤버·명시적 구현 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [ECMA-334 7판(2023-12)](https://ecma-international.org/publications-and-standards/standards/ecma-334/) ·
> [Learn — `interface` 키워드](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/keywords/interface)(열어서 확인: 「기본 구현 멤버는 **인터페이스 인스턴스로만** 접근된다」 · 「`static abstract` 호출은 **컴파일 시점 타입**으로 풀린다」) ·
> [ECMA-335(CLI) — `constrained.` 접두](https://ecma-international.org/publications-and-standards/standards/ecma-335/)
> **실행 검증** — 이 문서의 모든 출력·진단·IL·할당 바이트는 아래 「이 판」의 도구로 **실제로 돌려 얻은 것**이다(2026-09-26).\
> ★ 블록은 캡처 스크립트가 파일로 받아 조립기가 끼워 넣은 것이다 — 사람이 옮겨 적은 줄은 하나도 없다.\
> ★★★ **진단 언어를 영어로 고정했다**(`DOTNET_CLI_UI_LANGUAGE=en` + `-preferreduilang:en-US`).\
> **대비는 실측이다** — **javac 21.0.5** 로 같은 모양을 던졌다((7)).
> **버전** — 인터페이스·명시적 구현은 **C# 1.0부터** · **기본 구현 멤버는 C# 8** · **`static abstract` 멤버는 C# 11** 이다.\
> `-langversion:latest` 로 던졌다.
> **경계** — [16번](../16-inheritance-virtual-override-abstract-sealed-new/)이 **이미 잰 것은 다시 재지 않는다** —\
> ★★★ 「기본 구현이 클래스로 **안 내려온다**(`CS1061`·리플렉션상 선언 메서드 0개)」·「`new` 로 숨긴 것을 인터페이스로 부르면 `Base.Go`」·\
> 「명시적 구현이 `private=True final=True virtual=True`」·「`callvirt` 는 널 검사」는 **거기가 정본**이다.\
> ★★★ **이 문서는 그 결론 위에 선다** — 과녁은 둘뿐이다. **기본 구현 멤버가 무엇을 푸나**(인터페이스 진화)와 **명시적 구현이 무엇을 푸나**(이름 충돌).\
> ★ **박싱 자체**는 [03번](../03-boxing-and-unboxing/)이 정본이다.
> ★★★ **대비** — Java 갈래 목록([`java/syntax/README.md`](../../../java/syntax/README.md))의 **11번**([`11-interfaces-default-methods/`](../../../java/syntax/11-interfaces-default-methods/))이\
> `default` 메서드와 충돌 해소(`X.super.m()`)의 정본이다. 여기서는 **C# 과 갈리는 두 자리만** 다시 던졌다((7)).
>
> ★★ **흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | 진단 **문구** — 판마다 다듬인다 | ★★★ **진단 코드**(`CS0535`·`CS0738`·`CS8705`·`CS0175`·`CS8926`·`CS8920`)와 **`(행,열)`** |
> | **IL 오프셋 폭**(`IL_0008`) | ★★★ **옵코드 이름과 접두**(`constrained.` · `callvirt` 대 `call`) |
> | ★ **증분의 절댓값 일부** — 한 판에서 잰 바이트 | ★★★ **네 판에서 갈린 줄 수**(스크립트가 센 마지막 줄) · 그 네 판에서 다 같은 바이트 |
> | 예외 **메시지 문구**(`TypeLoadException` 의 영어 문장) | ★★★ **예외 타입 이름** · **`cc exit` 와 `run exit`**(갈라 적었다) |
> | javac 의 진단 **표기 형식** | ★ **`-warn:9` 에서 답한 탐침의 개수** |

## 이 판

```text
===== dotnet --version && dotnet --list-runtimes | grep NETCore (exit=0) =====
10.0.401
Microsoft.NETCore.App 10.0.12 [/home/jun/.local/opt/dotnet/shared/Microsoft.NETCore.App]
===== javac -version && ~/.sdkman/candidates/java/25.0.1-tem/bin/javac -version (exit=0) =====
javac 21.0.5
javac 25.0.1
```

## 이 갈래가 쓰는 세 층

| 층 | 뜻 | 이 주제에서 근거로 쓰는 것 |
|---|---|---|
| **언어 명세(ECMA-334)** | C# 언어가 약속한 것 | ★★★ 구현 안 한 멤버가 있으면 `CS0535` · 기본 구현은 **인터페이스로만** 보인다 · 가장 구체적인 구현이 하나여야 한다(`CS8705`) |
| **런타임·CLI(ECMA-335)** | CoreCLR 이 그렇게 하는 것 | ★★★ **다시 컴파일 안 한 앱이 새 라이브러리를 만났을 때**(`TypeLoadException` 대 정상 실행) · `constrained.` 접두 |
| **이 판의 관찰** | .NET 10.0.12 · linux-x64 · javac 21.0.5 | 진단 문구 · 예외 메시지 · 할당 바이트 · `-warn:9` 가 답한 탐침 수 |

★★★ **이 주제에서 첫 칸과 둘째 칸이 갈리는 자리는 「다시 컴파일했느냐」다.**\
컴파일러(언어 층)는 **소스를 다시 볼 때만** 말한다. **이미 배포된 바이너리**가 새 인터페이스를 만나는 순간은\
**런타임(CLI 층)이 말한다** — 그리고 **다른 창으로** 말한다((1)).

## 한눈에 — 쉽게 말하면

**인터페이스는 「계약서」다. 기본 구현 멤버는 「계약서에 붙은 표준 조항」이다.**

아파트 관리 규약을 생각하자.

- **인터페이스** — 「세대는 이 일들을 **해야 한다**」는 규약.
- **새 의무 조항을 추가한다** — ★★★ **이미 입주한 세대가 전부 위반자가 된다.** 규약을 고쳤을 뿐인데.
- **기본 구현 멤버** — 「이 조항은 **안 적은 세대는 표준 방식으로 한다**」라고 **규약에 방법까지 적어 두는 것.**\
  기존 세대는 **아무것도 안 해도 된다.**
- **그런데 표준 방식은 「관리실에 물으면」 알려 준다** — 세대(클래스) 문 앞에 붙지 않는다.\
  ★ 세대 이름으로 물으면 **「그런 조항 없다」**(`CS1061`, [16번](../16-inheritance-virtual-override-abstract-sealed-new/) (8)).
- **명시적 구현** — 한 세대가 **두 규약에 같은 이름의 의무**를 졌을 때, **어느 규약의 것인지 문패를 따로 다는 것.**

| 비유 | 실체 | 어디서 보나 |
|---|---|---|
| 새 의무 조항이 기존 세대를 위반자로 만든다 | ★★★ **`CS0535`** — 다시 컴파일하면 · **`TypeLoadException`** — 안 하면 | (1) |
| 표준 방식을 규약에 적어 둔다 | ★★★ **기본 구현 멤버** — 두 경우 다 **돈다** | (1) |
| 표준 방식은 관리실에만 있다 | 기본 구현은 **인터페이스 타입으로만** 불린다 | (2) · [16번](../16-inheritance-virtual-override-abstract-sealed-new/) (8) |
| 두 규약의 같은 이름 의무 | ★★★ **반환 타입이 다르면 `CS0738`** — 명시적 구현만이 푼다 | (4) |
| 두 규약이 같은 조항을 서로 다르게 적었다 | 관련 없는 둘이면 **충돌 없음** · 같은 조상을 덮으면 **`CS8705`** | (5) |

★★★ **이 주제의 본체 그림 — 인터페이스에 멤버를 하나 더했을 때의 격자.**

```text
                              앱을 다시 컴파일한다          앱을 다시 컴파일하지 않는다
                              (소스가 새 인터페이스를 본다)   (예전 ex.dll + 새 lib.dll)
   ┌───────────────────────┬────────────────────────────┬────────────────────────────┐
   │ 새 멤버에 본문이 없다  │  ✕ CS0535                  │  ✕ TypeLoadException        │
   │ (string Flush();)      │    컴파일러가 막는다          │    런타임이 타입 로드를 거부 │
   ├───────────────────────┼────────────────────────────┼────────────────────────────┤
   │ 새 멤버에 본문이 있다  │  ○ 돈다                     │  ○ 돈다                     │
   │ (string Flush() => …)  │    Flush() = 기본 구현        │    Flush() = 기본 구현        │
   └───────────────────────┴────────────────────────────┴────────────────────────────┘

   ★★★ 윗줄의 두 ✕ 는 같은 사고를 두 층이 각각 말하는 것이다.
   ★★★ 아랫줄이 기본 구현 멤버가 들어온 이유 전부다 — 「인터페이스 진화」.
```

- ★★★ **이 격자의 네 칸을 전부 실제로 찍었다**((1)). 그림은 결과를 옮긴 것이다.

## 이 주제가 답하려는 질문

1. **기본 구현 멤버는 무엇을 푸나** — 인터페이스에 멤버를 더해도 **기존 구현이 안 깨지게**((1)).
2. **명시적 구현은 무엇을 푸나** — **이름은 같은데 한 메서드로는 둘 다 못 채우는** 충돌((4)).
3. **기본 구현 안의 `this` 는 무엇이고, 구조체가 거기 기대면 무슨 일이 나나**((3)(6)).
4. **`static abstract` 멤버는 무엇을 여나** — 제네릭 수학((8)).
5. **Java `default` 와 어디서 갈리나**((7)).

## 동작 방식

### (0) 이 주제가 쓰는 창

★★★ **본체 창은 ② 진단이다** — 「`CS0535` 가 나오나 안 나오나」가 인터페이스 진화의 답이다.\
★★ **그런데 진단 창은 절반만 본다** — **다시 컴파일한 앱**만 본다. 다시 컴파일 **안 한** 앱의 운명은\
**실행 출력의 예외 타입**(`TypeLoadException`)으로만 물을 수 있다. ★★★ **제5의 상태 — 같은 질문을 다른 창으로 물었다.**

| 창 | 무엇을 보여 주나 | 이 주제에서 |
|---|---|---|
| ★★★ **② 진단 격자** | **`CS0535`** 가 나오나 · 충돌 진단(`CS0738`·`CS8705`·`CS0175`·`CS8926`·`CS8920`) | (1)(4)(5)(8)(10) |
| ★★★ **실행 출력의 예외 타입** | ★★★ **제5의 상태** — 진단 창이 못 보는 「다시 컴파일 안 한 바이너리」를 **런타임에 물었다** | (1) |
| ★★ **① IL 덤프** | 인터페이스 호출이 **`callvirt`** · 제네릭 호출에 붙는 **`constrained.`** · `static abstract` 의 **`call`** | (6)(8) |
| ★★ **③ 리플렉션** | 인터페이스 멤버의 **`abstract`/`virtual`/`static`** 조합 · 인터페이스 맵 | (9) |
| ★★ **④ 할당 바이트** | ★★★ **구조체가 기본 구현에 기대면 제네릭 호출마다 박싱** — **2×2 판 격자** | (6) |

- ★★★ **④ 할당 바이트가 「적용」인 것이 16편과 다르다.** 16편에서는 **부적용**이었다(객체가 하나이고 크기가 같다).\
  **여기서는 잴 것이 있다** — 구조체 + 기본 구현 조합에서 **숨은 박싱**이 나온다((6)).
- ★ **왜 제5의 상태인가** — 「앱을 다시 컴파일하지 않았다」는 상황은 **컴파일러가 원리상 관여하지 않는 자리**다.\
  「못 잰 것」도 「부적용」도 아니고 **창을 바꿔 답한 것**이다. ★ 바꾼 창(예외 타입)이 못 보는 것 —\
  **예외가 언제 나는가**(타입 로드 시점)와 **어디서 나는가**는 이 판의 관찰이다((1) 아래).

### (1) ★★★ 인터페이스에 멤버를 더하면 — 네 칸 전부

**언제 쓰나** — 라이브러리의 **공개 인터페이스를 고칠 때마다.** 이 절이 이 주제의 중심이다.

라이브러리(`lib.dll`)와 앱(`ex.dll`)을 **따로** 빌드했다. 앱은 v1 라이브러리로 컴파일한 뒤 **그대로 두고**\
라이브러리만 v2 로 바꿔 끼웠다 — 배포된 앱이 **라이브러리 업데이트를 받는** 모양이다.

```text
===== 소스: cs17b-lib1.cs =====
public interface ILog {
    string Write(string m);
}
===== 소스: cs17b-app.cs =====
using System;
class FileLog : ILog { public string Write(string m) => "쓴다 " + m; }
class Program {
    static void Main() {
        try { Run(); }
        catch (Exception e) { Console.WriteLine($"{e.GetType().Name} : {e.Message}"); }
    }
    static void Run() {
        ILog log = new FileLog();
        Console.WriteLine(log.Write("a"));
        var flush = typeof(ILog).GetMethod("Flush");
        Console.WriteLine(flush is null ? "ILog.Flush 를 찾았나 : 아니오" : $"Flush() = {flush.Invoke(log, null)}");
    }
}
===== csc -target:library -out:lib.dll cs17b-lib1.cs && csc -r:lib.dll -out:ex.dll cs17b-app.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
쓴다 a
ILog.Flush 를 찾았나 : 아니오
===== 소스: cs17b-lib2abs.cs =====
public interface ILog {
    string Write(string m);
    string Flush();                          // 새 멤버 — 본문이 없다
}
===== csc -target:library -out:lib.dll cs17b-lib2abs.cs && dotnet ex.dll    # ex.dll 은 다시 컴파일하지 않았다 (cc exit=0 · run exit=0) =====
TypeLoadException : Method 'Flush' in type 'FileLog' from assembly 'ex, Version=0.0.0.0, Culture=neutral, PublicKeyToken=null' does not have an implementation.
===== csc -r:lib.dll -out:ex2.dll cs17b-app.cs    # 같은 앱을 새 라이브러리로 다시 컴파일 (cc exit=1) =====
cs17b-app.cs(2,17): error CS0535: 'FileLog' does not implement interface member 'ILog.Flush()'
===== 소스: cs17b-lib2dim.cs =====
public interface ILog {
    string Write(string m);
    string Flush() => "ILog 의 기본 Flush";     // 새 멤버 — 본문이 있다 (C# 8)
}
===== csc -target:library -out:lib.dll cs17b-lib2dim.cs && dotnet ex.dll    # ex.dll 은 다시 컴파일하지 않았다 (cc exit=0 · run exit=0) =====
쓴다 a
Flush() = ILog 의 기본 Flush
===== csc -r:lib.dll -out:ex2.dll cs17b-app.cs && dotnet ex2.dll (cc exit=0 · run exit=0) =====
쓴다 a
Flush() = ILog 의 기본 Flush
```

- ★★★ **첫 판** — v1 끼리는 정상이다. `ILog` 에 `Flush` 가 **없다.**
- ★★★ **본문 없는 `Flush` 를 더한 v2 를 끼우면** — 앱을 **한 글자도 안 고쳤는데** `TypeLoadException` 이다.\
  ★★ **「쓴다 a」조차 안 찍혔다** — `Run` 을 JIT 하려고 `FileLog` 타입을 불러오는 순간 거부됐다.\
  **`FileLog` 가 `Flush` 를 안 부르는데도** 막힌다 — **타입 자체가 계약을 못 채워서** 로드가 안 된다.
- ★★★ **같은 앱을 v2 로 다시 컴파일하면** `CS0535` — 「`FileLog` 가 `ILog.Flush()` 를 구현하지 않는다」.\
  ★ **윗줄과 같은 사고를 컴파일러가 말한 것**이다. **층이 다를 뿐 사고는 하나다.**
- ★★★ **본문 있는 `Flush`(기본 구현)를 더한 v2 를 끼우면** — **다시 컴파일 안 한 앱이 그냥 돈다.**\
  리플렉션으로 부른 `Flush()` 가 **「ILog 의 기본 Flush」** 를 돌려준다.
- ★★★ **다시 컴파일해도 돈다** — 진단 0줄에 `cc exit=0` 이다.

> **어느 층인가** — ★★★ 「구현 안 한 추상 멤버가 있으면 **컴파일 에러**」는 **언어(334)** 다.\
> ★★★ 「그런 타입은 **로드되지 않는다**」는 **CLI(335)** 의 타입 로드 규칙이다.\
> ★ 예외가 **`Run` 을 JIT 할 때** 났다는 것은 **이 판의 관찰**이다 — 타입 로드 시점은 런타임이 정한다.\
> 그래서 앱은 `Main` 의 `try` 를 `Run` 바깥에 두었다. **`Main` 안에서 `new FileLog()` 를 했으면 `Main` 자체가 JIT 안 돼 `catch` 도 못 탔을 것이다.**

- ★★★ **이것이 기본 구현 멤버가 C# 8 에 들어온 이유다.** 인터페이스는 **한번 배포하면 못 고치는 계약**이었다 —\
  멤버 하나를 더하는 것이 **모든 구현체를 깨는 파괴적 변경**이었기 때문이다. 기본 구현이 그 칸을 ○ 로 바꿨다.

### (2) 기본 구현은 인터페이스로만 부른다 — 16편의 결론 위에서

[16번](../16-inheritance-virtual-override-abstract-sealed-new/) (8)이 이미 쟀다 — **`new Plain().Hello()` 는 `CS1061`** 이고 **`Plain` 이 선언한 메서드는 0개**다.\
★★★ **여기서는 그 결론이 (1)과 어떻게 맞물리는지만 본다.**

- (1)의 앱은 `Flush` 를 **리플렉션으로** 불렀다(`typeof(ILog).GetMethod("Flush")`) — **인터페이스 타입에서** 찾은 것이다.\
  **`FileLog` 에서 찾았으면 없었다.**
- ★★★ **그래서 「기본 구현 = 인터페이스 진화용」이 설계의 뜻이다.** 기본 구현이 클래스로 내려오면\
  **클래스의 공개 표면이 라이브러리 업데이트로 바뀐다** — 그러면 (5)의 충돌이 **클래스 쪽에서** 터진다.

### (3) ★★ 기본 구현 안의 `this` — 그리고 구조체

**언제 쓰나** — 기본 구현이 **상태를 바꾸는** 멤버를 부를 때.

```text
===== 소스: cs17b-this.cs =====
using System;
interface ICounter {
    int Count { get; set; }
    string Bump() { Count++; return $"this.GetType()={this.GetType().Name} Count={Count}"; }   // 기본 구현
}
struct SDim : ICounter { public int Count { get; set; } }                       // 기본 구현에 기댄다
struct SOwn : ICounter { public int Count { get; set; }
                         public string Bump() { Count++; return $"SOwn 자신 Count={Count}"; } }
class  CDim : ICounter { public int Count { get; set; } }
class Program {
    static string Via<T>(ref T t) where T : ICounter => t.Bump();
    static void Main() {
        var c = new CDim();
        Console.WriteLine($"[1] {((ICounter)c).Bump()}");
        Console.WriteLine($"    c.Count = {c.Count}");
        var s = new SDim();
        Console.WriteLine($"[2] {((ICounter)s).Bump()}");
        Console.WriteLine($"    s.Count = {s.Count}");
        Console.WriteLine($"[3] {Via(ref s)}");
        Console.WriteLine($"    s.Count = {s.Count}");
        var o = new SOwn();
        Console.WriteLine($"[4] {Via(ref o)}");
        Console.WriteLine($"    o.Count = {o.Count}");
    }
}
===== csc -out:ex.dll cs17b-this.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
[1] this.GetType()=CDim Count=1
    c.Count = 1
[2] this.GetType()=SDim Count=1
    s.Count = 0
[3] this.GetType()=SDim Count=1
    s.Count = 0
[4] SOwn 자신 Count=1
    o.Count = 1
```

- ★★★ **`this.GetType()` 은 실제 객체의 타입이다**(`CDim`·`SDim`). 기본 구현 안의 `this` 는\
  **정적 타입이 인터페이스인 참조**이고, 가리키는 것은 **구현체**다. `Count++` 는 **구현체의 속성**을 부른다.
- ★★★ **클래스는 원본이 바뀐다**(`c.Count = 1`).
- ★★★ **구조체는 원본이 안 바뀐다**(`s.Count = 0`) — **`[2]` 도 `[3]` 도.**
  - `[2]` 는 `(ICounter)s` 로 **박싱한 상자**를 바꿨다 — 그건 [03번](../03-boxing-and-unboxing/)이 말한 그대로다.
  - ★★★ **`[3]` 이 급소다** — **`ref` 로 넘기고 제네릭 제약으로 불렀는데도** 원본이 안 바뀌었다.\
    기본 구현의 `this` 는 **인터페이스 참조여야 하므로** 런타임이 **그 자리에서 상자를 만든다.**
  - ★★ **`[4]` 가 대조군이다** — 구조체가 **스스로 구현하면**(`SOwn`) 같은 `Via(ref o)` 가 **원본을 바꾼다**(`o.Count = 1`).
```text
   Via(ref s)  — s 는 SDim(구조체), Bump 는 인터페이스의 기본 구현

   스택의 s                         힙
   ┌──────────┐    그 자리에서      ┌──────────────────┐
   │ Count = 0│ ── 박싱(복사) ────▶ │ 상자: SDim        │
   └──────────┘                     │ Count = 0 → 1    │ ◀── 기본 구현의 this (인터페이스 참조)
        ▲                           └──────────────────┘
        │                                  │ Bump 가 끝나면 아무도 안 가리킨다
   s.Count = 0 그대로                        ▼
                                          (버려진다 — 24바이트, (6))

   SOwn 이면: 상자 없음 — constrained. 이 ref 로 받은 원본 주소에 직접 부른다 → o.Count = 1

   ★★★ ref 는 「원본 주소를 넘겼다」는 뜻일 뿐, 기본 구현은 그 주소를 쓸 수 없다.
```

- ★★★ **결론 — 구조체가 「상태를 바꾸는 기본 구현」에 기대면 그 변경은 어디에도 안 남는다.** 경고도 없다((10) 탐침 4).

### (4) ★★★ 명시적 구현이 푸는 것 — 한 메서드로는 둘 다 못 채울 때

**언제 쓰나** — 두 인터페이스가 **같은 이름·같은 매개변수**에 **다른 반환 타입**을 요구할 때.

★ [16번](../16-inheritance-virtual-override-abstract-sealed-new/) (8)의 `IWalk.Move`/`ISwim.Move` 는 **반환 타입까지 같았다** — 그래서 **공용 메서드 하나로도 둘 다 채울 수** 있었고,\
명시적 구현은 **「다르게 동작시키고 싶어서」** 쓴 것이었다. **여기는 명시적 구현이 「유일한 길」인 경우**다.

```text
===== 소스: cs17b-clash.cs =====
interface IText { string Read(); }
interface INum  { int    Read(); }
class Both : IText, INum {
    public string Read() => "글자";
}
class Program { static void Main() { } }
===== csc -out:ex.dll cs17b-clash.cs (cc exit=1) =====
cs17b-clash.cs(3,21): error CS0738: 'Both' does not implement interface member 'INum.Read()'. 'Both.Read()' cannot implement 'INum.Read()' because it does not have the matching return type of 'int'.
```

- ★★★ **`CS0738`** — 「`Both.Read()` 는 반환 타입이 `int` 가 아니라서 `INum.Read()` 를 구현할 수 없다」.\
  C# 은 **반환 타입으로 오버로드하지 못한다** — `string Read()` 와 `int Read()` 를 **한 클래스에 공용으로 둘 수 없다.**

```text
===== 소스: cs17b-clash2.cs =====
using System;
using System.Collections;
using System.Collections.Generic;
interface IText { string Read(); }
interface INum  { int    Read(); }
class Both : IText, INum {
    public string Read() => "글자";
    int INum.Read() => 42;                         // 명시적 구현
}
class Bag : IEnumerable<int> {
    public IEnumerator<int> GetEnumerator() { yield return 1; yield return 2; }
    IEnumerator IEnumerable.GetEnumerator() => GetEnumerator();   // 명시적 구현
}
class Program {
    static void Main() {
        var b = new Both();
        Console.WriteLine($"b.Read()          = {b.Read()}");
        Console.WriteLine($"((IText)b).Read() = {((IText)b).Read()}");
        Console.WriteLine($"((INum)b).Read()  = {((INum)b).Read()}");
        foreach (var x in new Bag()) Console.Write($"{x} ");
        Console.WriteLine("← 제네릭 쪽");
        foreach (object x in (IEnumerable)new Bag()) Console.Write($"{x} ");
        Console.WriteLine("← 비제네릭 쪽");
    }
}
===== csc -out:ex.dll cs17b-clash2.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
b.Read()          = 글자
((IText)b).Read() = 글자
((INum)b).Read()  = 42
1 2 ← 제네릭 쪽
1 2 ← 비제네릭 쪽
```

- ★★★ **`int INum.Read() => 42` 한 줄이 푼다.** 이름이 `INum.Read` 라 **공용 `Read` 와 충돌하지 않는다.**
- ★★★ **BCL 이 매일 쓰는 모양이다** — `IEnumerable<T>` 는 `IEnumerable` 을 상속하고,\
  둘 다 **`GetEnumerator()`** 를 요구하는데 **반환 타입이 다르다**(`IEnumerator<T>` 대 `IEnumerator`).\
  **`foreach` 가 가능한 모든 사용자 컬렉션이 명시적 구현을 한 줄씩 갖고 있다**(`Bag`).
- ★★ **두 `foreach` 가 같은 `1 2` 를 찍었다** — 비제네릭 쪽이 **제네릭 쪽에 위임**했기 때문이다. 이것이 관례다.

```text
   class Bag : IEnumerable<int>

       public  IEnumerator<int> GetEnumerator()          ← 공용 — foreach 가 고른다
       IEnumerator IEnumerable.GetEnumerator()           ← 명시적 — 이름이 「IEnumerable.GetEnumerator」
                    │                                       (C# 에서 선언할 수 없는 이름이라 충돌이 원리상 없다)
                    └──── return GetEnumerator(); ────────▶ 공용 쪽에 위임

   ★★★ 같은 이름 · 같은 매개변수 · 다른 반환 타입 — 명시적 구현만이 둘을 동시에 채운다.
```

### (5) ★★ 기본 구현끼리 부딪히면 — 관련 없는 둘 대 같은 조상

**언제 쓰나** — 「기본 구현이 클래스로 안 내려오는 게 무슨 이득이냐」고 물을 때.

```text
===== 소스: cs17b-twin.cs =====
using System;
interface IA { string Hello() => "IA 의 기본 구현"; }
interface IB { string Hello() => "IB 의 기본 구현"; }
class Both : IA, IB { }                                  // 아무것도 안 적었다
class Pick : IA, IB { public string Hello() => "Pick 이 직접"; }
class Program {
    static void Main() {
        var b = new Both();
        Console.WriteLine($"((IA)b).Hello() = {((IA)b).Hello()}");
        Console.WriteLine($"((IB)b).Hello() = {((IB)b).Hello()}");
        var p = new Pick();
        Console.WriteLine($"((IA)p).Hello() = {((IA)p).Hello()}");
        Console.WriteLine($"((IB)p).Hello() = {((IB)p).Hello()}");
    }
}
===== csc -out:ex.dll cs17b-twin.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
((IA)b).Hello() = IA 의 기본 구현
((IB)b).Hello() = IB 의 기본 구현
((IA)p).Hello() = Pick 이 직접
((IB)p).Hello() = Pick 이 직접
```

- ★★★ **컴파일이 된다**(`cc exit=0`). `IA` 와 `IB` 가 **같은 이름의 기본 구현**을 주는데 `Both` 는 **아무것도 안 적었다.**
- ★★★ **`((IA)b)` 는 IA 것, `((IB)b)` 는 IB 것** — 각 인터페이스 **자기 슬롯에 자기 기본 구현**이 들어간다.\
  **클래스로 안 내려오니 클래스 안에서 부딪힐 일이 없다.** 이것이 (2)에서 말한 「설계의 뜻」이다.
- ★★ **`Pick` 이 공용 `Hello` 를 두면 두 슬롯을 다 채운다** — 클래스 구현이 **기본 구현을 이긴다.**

```text
===== 소스: cs17b-diamond.cs =====
using System;
interface IBase  { string Hello() => "IBase"; }
interface ILeft  : IBase { string IBase.Hello() => "ILeft"; }    // 기반 인터페이스의 기본 구현을 덮는다
interface IRight : IBase { string IBase.Hello() => "IRight"; }
class Both : ILeft, IRight { }
class Program { static void Main() { Console.WriteLine(((IBase)new Both()).Hello()); } }
===== csc -out:ex.dll cs17b-diamond.cs (cc exit=1) =====
cs17b-diamond.cs(5,14): error CS8705: Interface member 'IBase.Hello()' does not have a most specific implementation. Neither 'ILeft.IBase.Hello()', nor 'IRight.IBase.Hello()' are most specific.
```

- ★★★ **같은 조상(`IBase`)의 멤버를 두 파생 인터페이스가 각자 덮으면** `CS8705` —\
  「`IBase.Hello()` 에 **가장 구체적인 구현이 없다**. `ILeft.IBase.Hello()` 도 `IRight.IBase.Hello()` 도 가장 구체적이지 않다」.\
  ★ **슬롯이 하나**(`IBase.Hello`)인데 **후보가 둘**이라서다. 관련 없는 둘((5) 위)은 **슬롯이 둘**이었다.
- ★ 푸는 법은 클래스가 **`IBase.Hello` 를 직접 구현**하는 것이다(명시적이든 공용이든).

```text
===== 소스: cs17b-basecall.cs =====
interface IA { string Hello() => "IA"; }
class C : IA {
    public string Hello() => "C 가 감싼다 : " + base(IA).Hello();    // 특정 인터페이스의 기본 구현을 부르려 한다
}
class Program { static void Main() { } }
===== csc -out:ex.dll cs17b-basecall.cs 2>&1 | sort (cc exit=1) =====
cs17b-basecall.cs(3,45): error CS0175: Use of keyword 'base' is not valid in this context
cs17b-basecall.cs(3,50): error CS0119: 'IA' is a type, which is not valid in the given context
===== csc -langversion:preview -out:ex.dll cs17b-basecall.cs 2>&1 | sort (cc exit=1) =====
cs17b-basecall.cs(3,45): error CS0175: Use of keyword 'base' is not valid in this context
cs17b-basecall.cs(3,50): error CS0119: 'IA' is a type, which is not valid in the given context
```

- ★★★ **클래스 안에서 특정 인터페이스의 기본 구현을 부를 방법이 없다** — `base(IA).Hello()` 는 `CS0175`·`CS0119`.\
  ★★ **`-langversion:preview` 에서도 같다**(이 판).\
  ★★★ **Java 는 된다** — `Left.super.hello()`((7)).\
  ★ 이 문법의 **설계 이력은 확인하지 않았다** — 확인한 것은 **이 판에서 안 된다**는 것뿐이다.
- ★ 그래서 C# 에서 **「기본 구현을 감싸서 조금 바꾸기」를 클래스 쪽에서 할 문법이 없다.**\
  ★ `((IA)this).Hello()` 는 인터페이스 슬롯을 거치므로 **클래스가 그 슬롯을 채웠다면 자기 자신**으로 돌아올 것이다 — **이 판에서 던지지 않았다.**

### (6) ★★ IL 과 할당 바이트 — 구조체의 숨은 박싱

**언제 쓰나** — (3)의 `[3]` 이 **왜** 원본을 못 바꿨는지, 그리고 그게 **비용**인지 물을 때.

```text
===== 소스: cs17b-il.cs =====
using System;
interface IGreet { string Hello() => "기본 구현"; }
interface IZero<T> where T : IZero<T> { static abstract T Zero { get; } }
readonly struct Num : IZero<Num> { public static Num Zero => default; }
static class Probe {
    public static string A(IGreet g)          => g.Hello();       // 인터페이스 변수로
    public static string B<T>(T t) where T : IGreet => t.Hello(); // 제네릭 — 제약으로
    public static T      C<T>() where T : IZero<T>  => T.Zero;    // static abstract
}
class Program {
    static void Main() {
        Il.Dump(typeof(Probe), "A");
        Il.Dump(typeof(Probe), "B");
        Il.Dump(typeof(Probe), "C");
    }
}
===== csc -r:il.dll -out:ex.dll cs17b-il.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
--- Probe.A ---
  IL_0000: ldarg.0
  IL_0001: callvirt IGreet::Hello
  IL_0006: ret
--- Probe.B ---
  IL_0000: ldarga.s 0
  IL_0002: constrained. T
  IL_0008: callvirt IGreet::Hello
  IL_000d: ret
--- Probe.C ---
  IL_0000: constrained. T
  IL_0006: call IZero<T>::get_Zero
  IL_000b: ret
```

- ★★★ **`A`(인터페이스 변수)** — 그냥 `callvirt IGreet::Hello` 다. 16편 (4)의 모양 그대로다.
- ★★★ **`B`(제네릭 제약)** — **`ldarga.s 0`**(주소를 싣는다) + **`constrained. T`** + `callvirt`.\
  `constrained.` 은 「**`T` 가 값 타입이면 박싱하지 말고 주소로 불러라, 단 불가능하면 박싱해라**」라는 접두다(ECMA-335).\
  ★★★ **기본 구현은 「불가능한 쪽」이다** — 구조체 자신에게 `Hello` 가 **없으니** 인터페이스의 본문을 불러야 하고,\
  그 본문의 `this` 는 **참조**여야 한다. 그래서 **런타임이 상자를 만든다.**
- ★★ **`C`(`static abstract`)** — **`constrained. T` + `call`**. 수신자가 **없으니** `callvirt` 가 아니다((8)).

그 상자가 **실제로 할당되는지** 2×2 판 격자로 쟀다(규칙 24).

```text
===== 소스: cs17b-alloc.cs =====
using System;
interface IShape {
    int Side { get; }
    int Twice() => Side * 2;                                                       // 기본 구현
}
struct Own : IShape { public int Side => 3; public int Twice() => Side * 2; }     // 스스로 구현
struct Dim : IShape { public int Side => 3; }                                       // 기본 구현에 기댄다
class Program {
    static int Call<T>(T t) where T : IShape => t.Twice();
    static long M(Action a) {
        a();                                             // 한 판 데워 놓고
        var b = GC.GetAllocatedBytesForCurrentThread();
        a();
        return GC.GetAllocatedBytesForCurrentThread() - b;
    }
    static void Main() {
        int sink = 0;
        var own = new Own(); var dim = new Dim();
        Console.WriteLine($"Call(own) 1000회 : {M(() => { for (int i = 0; i < 1000; i++) sink += Call(own); })} 바이트");
        Console.WriteLine($"Call(dim) 1000회 : {M(() => { for (int i = 0; i < 1000; i++) sink += Call(dim); })} 바이트");
        Console.WriteLine($"(합 {sink})");
    }
}
===== csc -out:ex.dll cs17b-alloc.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
Call(own) 1000회 : 0 바이트
Call(dim) 1000회 : 24000 바이트
(합 24000)
===== csc -out:ex.dll cs17b-alloc.cs && DOTNET_TieredCompilation=0 dotnet ex.dll (cc exit=0 · run exit=0) =====
Call(own) 1000회 : 0 바이트
Call(dim) 1000회 : 24000 바이트
(합 24000)
===== csc -optimize -out:exo.dll cs17b-alloc.cs && dotnet exo.dll (cc exit=0 · run exit=0) =====
Call(own) 1000회 : 0 바이트
Call(dim) 1000회 : 24000 바이트
(합 24000)
===== csc -optimize -out:exo.dll cs17b-alloc.cs && DOTNET_TieredCompilation=0 dotnet exo.dll (cc exit=0 · run exit=0) =====
Call(own) 1000회 : 0 바이트
Call(dim) 1000회 : 24000 바이트
(합 24000)
===== 네 판 대조 — 「바이트」 줄마다 네 판의 값이 같은가 =====
네 판에서 갈린 줄 0 / 2
```

- ★★★ **`Call(dim)` 만 1000회에 24000 바이트** — 한 번에 24바이트, **빈 구조체 하나를 박싱한 크기**다.\
  **`Call(own)` 은 0** 이다 — 구조체가 **스스로 구현하면** `constrained.` 이 **박싱 없이 직접** 부른다.
- ★★★ **네 판에서 갈린 줄 0 / 2.** csc 최적화 × 티어링 네 판 전부 같다 — **근거로 쓸 수 있다.**

| 판 | `Call(own)` | `Call(dim)` | 움직였나 |
|---|---|---|---|
| 기본 | 0 | 24000 | — |
| `DOTNET_TieredCompilation=0` | 0 | 24000 | ★ 안 움직임 |
| `csc -optimize` | 0 | 24000 | ★ 안 움직임 |
| 둘 다 | 0 | 24000 | ★ 안 움직임 |

- ★★★ **시간은 안 쟀다.** 「기본 구현은 느리다」는 문장이 이 문서에 없다 — 잰 것은 **할당 횟수**다.
- ★★ **이 비용과 (3)의 의미 사고가 같은 뿌리다** — **상자가 생기니** 비용이 들고, **상자가 바뀌니** 원본이 안 바뀐다.

### (7) ★★★ Java `default` 와 대비 — 두 자리가 정반대

```text
===== 소스: j17/Ex17.java =====
interface Greet { default String hello() { return "Greet.hello"; } }
interface Left  { default String hello() { return "Left.hello"; } }
interface Right { default String hello() { return "Right.hello"; } }
class Plain implements Greet { }                    // 아무것도 안 적었다
class Pick implements Left, Right {
    public String hello() { return "Pick : " + Left.super.hello(); }
}
public class Ex17 {
    public static void main(String[] a) throws Exception {
        Plain p = new Plain();
        System.out.println("클래스 변수로 p.hello() : " + p.hello());
        System.out.println("Plain.class.getMethod(\"hello\") 의 선언 타입 : " + Plain.class.getMethod("hello").getDeclaringClass().getName());
        System.out.println("new Pick().hello() : " + new Pick().hello());
    }
}
===== javac -Xlint:all -d j17out j17/Ex17.java && java -cp j17out Ex17 (cc exit=0 · run exit=0) =====
클래스 변수로 p.hello() : Greet.hello
Plain.class.getMethod("hello") 의 선언 타입 : Greet
new Pick().hello() : Pick : Left.hello
===== 소스: j17b/Both.java =====
interface Left  { default String hello() { return "Left.hello"; } }
interface Right { default String hello() { return "Right.hello"; } }
class Both implements Left, Right { }               // 아무것도 안 적었다
===== javac -d j17bout j17b/Both.java (cc exit=1) =====
j17b/Both.java:3: error: types Left and Right are incompatible;
class Both implements Left, Right { }               // 아무것도 안 적었다
^
  class Both inherits unrelated defaults for hello() from types Left and Right
1 error
```

- ★★★ **Java 는 `default` 가 클래스로 내려온다** — `p.hello()` 가 **클래스 변수로** 돌고,\
  `Plain.class.getMethod("hello")` 가 **찾아진다**(선언 타입은 `Greet`). C# 은 [16번](../16-inheritance-virtual-override-abstract-sealed-new/) (8)의 `CS1061` 이다.
- ★★★ **그 대가로 Java 는 관련 없는 두 `default` 가 클래스에서 부딪힌다** —\
  `types Left and Right are incompatible; class Both inherits unrelated defaults`. **C# 은 같은 모양이 통과했다**((5) `Both`).
- ★★★ **Java 는 `Left.super.hello()` 로 특정 인터페이스의 것을 부를 수 있다.** C# 은 `CS0175`((5)).

```text
                             C#                              Java
   기본 구현이 클래스로       ✕ 안 내려온다 (CS1061)            ○ 내려온다
   관련 없는 두 기본 구현      ○ 충돌 없음 — 슬롯이 따로          ✕ 컴파일 에러 — 클래스에서 부딪힌다
   특정 인터페이스 것 부르기   ✕ base(IA) 없음 (CS0175)          ○ Left.super.hello()
   같은 조상을 둘이 덮으면     ✕ CS8705                         ✕ (같은 계열 에러)

   ★★★ 한 결정(「클래스로 내려오나」)이 아래 두 줄을 정반대로 만든다.
```

- ★ **마지막 줄의 Java 칸은 이 판에서 던지지 않았다** — 「같은 계열」은 [Java 11번](../../../java/syntax/11-interfaces-default-methods/)의 충돌 규칙에서 읽은 것이다.

### (8) ★ `static abstract` 멤버 — 인스턴스 없는 계약

**언제 쓰나** — 「**타입이** `Zero` 를 갖고 `+` 를 안다」를 제네릭에서 요구하고 싶을 때(제네릭 수학).

```text
===== 소스: cs17b-sa.cs =====
using System;
using System.Numerics;
interface IMonoid<T> where T : IMonoid<T> {
    static abstract T Zero { get; }
    static abstract T operator +(T a, T b);
}
readonly record struct Meter(double V) : IMonoid<Meter> {
    public static Meter Zero => new(0);
    public static Meter operator +(Meter a, Meter b) => new(a.V + b.V);
}
static class Alg {
    public static T Sum<T>(T[] xs) where T : IMonoid<T> {
        T acc = T.Zero;
        foreach (var x in xs) acc = acc + x;
        return acc;
    }
    public static T SumNum<T>(T[] xs) where T : INumber<T> {        // BCL 의 제네릭 수학 (.NET 7)
        T acc = T.Zero;
        foreach (var x in xs) acc += x;
        return acc;
    }
}
class Program {
    static void Main() {
        Console.WriteLine(Alg.Sum(new[] { new Meter(1.5), new Meter(2) }));
        Console.WriteLine(Alg.SumNum(new[] { 1, 2, 3 }));
        Console.WriteLine(Alg.SumNum(new[] { 1.5m, 2.25m }));
    }
}
===== csc -out:ex.dll cs17b-sa.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
Meter { V = 3.5 }
6
3.75
```

- ★★★ **`T.Zero`·`acc + x` 가 제네릭 안에서 된다.** `T` 에 인스턴스가 없어도 **타입에게** 묻는다.
- ★★ **BCL 이 이미 이 모양이다** — `INumber<T>` 로 `int` 와 `decimal` 을 **한 함수**로 더했다(`6` · `3.75`).
- ★★★ **IL 은 `constrained. T` + `call`** 이다((6)의 `C`). **`callvirt` 가 아니다** — 수신자가 없고,\
  Learn 이 적은 대로 「**컴파일 시점 타입으로 풀린다**」. **런타임 가상 디스패치가 아니다.**

```text
===== 소스: cs17b-saerr.cs =====
interface IZero { static abstract int Zero { get; } }
class Z : IZero { public static int Zero => 0; }
class Program {
    static int Get<T>() where T : IZero => T.Zero;
    static void Main() {
        int a = IZero.Zero;          // 인터페이스 이름으로 직접
        int b = Get<IZero>();        // 인터페이스를 타입 인자로
        int c = Get<Z>();            // 구현 타입을 타입 인자로
    }
}
===== csc -out:ex.dll cs17b-saerr.cs 2>&1 | sort (cc exit=1) =====
cs17b-saerr.cs(6,17): error CS8926: A static virtual or abstract interface member can be accessed only on a type parameter.
cs17b-saerr.cs(7,17): error CS8920: The interface 'IZero' cannot be used as type argument. Static member 'IZero.Zero' does not have a most specific implementation in the interface.
```

- ★★★ **`CS8926`** — `IZero.Zero` 처럼 **인터페이스 이름으로 직접** 부를 수 없다. **타입 매개변수로만** 부른다.
- ★★★ **`CS8920`** — **인터페이스 자체를 타입 인자로** 줄 수 없다. `IZero` 에는 `Zero` 의 **구현이 없기** 때문이다.
- ★ `Get<Z>()` 는 통과한다(진단이 8번 줄에 없다).

### (9) ★ 리플렉션 — 인터페이스 멤버의 한정자 조합

```text
===== 소스: cs17b-refl.cs =====
using System;
using System.Reflection;
interface IShape {
    double Area();                                  // 본문 없음
    string Name() => "도형";                         // 기본 구현 멤버 (C# 8)
    static abstract IShape Unit();                  // static abstract (C# 11)
    static string Kind() => "모양";                  // 정적 멤버 — 본문이 있다
    private string Secret() => "비밀";               // private 멤버 (C# 8)
}
class Sq : IShape {
    public double Area() => 1;
    public static IShape Unit() => new Sq();
}
class Program {
    static void Main() {
        foreach (var m in typeof(IShape).GetMethods(BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance | BindingFlags.Static | BindingFlags.DeclaredOnly))
            Console.WriteLine($"{m.Name,-7} abstract={m.IsAbstract,-5} virtual={m.IsVirtual,-5} static={m.IsStatic,-5} private={m.IsPrivate,-5} 본문={(m.GetMethodBody() is null ? "없음" : "있음")}");
        var map = typeof(Sq).GetInterfaceMap(typeof(IShape));
        for (int k = 0; k < map.InterfaceMethods.Length; k++)
            Console.WriteLine($"맵 {map.InterfaceMethods[k].Name,-7} -> {map.TargetMethods[k].DeclaringType!.Name}.{map.TargetMethods[k].Name}");
        Console.WriteLine($"Sq 가 선언한 인스턴스 메서드 : {string.Join(", ", Array.ConvertAll(typeof(Sq).GetMethods(BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance | BindingFlags.DeclaredOnly), m => m.Name))}");
    }
}
===== csc -out:ex.dll cs17b-refl.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
Area    abstract=True  virtual=True  static=False private=False 본문=없음
Name    abstract=False virtual=True  static=False private=False 본문=있음
Unit    abstract=True  virtual=True  static=True  private=False 본문=없음
Kind    abstract=False virtual=False static=True  private=False 본문=있음
Secret  abstract=False virtual=False static=False private=True  본문=있음
맵 Area    -> Sq.Area
맵 Name    -> IShape.Name
맵 Unit    -> Sq.Unit
Sq 가 선언한 인스턴스 메서드 : Area
```

- ★★★ **`static abstract` 는 `abstract=True virtual=True static=True`** — **클래스에서는 불가능한 조합**이다.\
  클래스의 `static` 메서드는 `virtual` 일 수 없다([16번](../16-inheritance-virtual-override-abstract-sealed-new/)).
- ★★ **기본 구현 멤버(`Name`)는 `abstract=False virtual=True`** — 본문이 있고, **구현체가 덮을 수 있는 슬롯**이다.
- ★★ **인터페이스에 `private` 멤버가 있다**(`Secret`) — C# 8 부터다. **기본 구현들이 공유하는 도우미**용이다.
- ★★★ **인터페이스 맵이 `Name -> IShape.Name`** — `Sq` 가 안 채운 슬롯은 **인터페이스 자신의 본문**이 채운다.\
  **`Sq` 가 선언한 인스턴스 메서드는 `Area` 하나**뿐이다 — 16편 (8)의 「정말 없다」가 여기서도 같다.
- ★ 맵에 **`Unit`(static abstract)도 나온다** — 정적 멤버도 **인터페이스 계약의 슬롯**이다.

### (10) ★★ 컴파일러가 무엇을 안 보나 — 탐침 일곱

```text
===== 소스: cs17b-probe.cs =====
using System;

// 탐침 1 — 기본 구현이 있는 멤버와 같은 이름의 private 메서드를 클래스가 둔다
interface I1 { string Hello() => "I1 의 기본 구현"; }
class C1 : I1 { string Hello() => "C1 의 것"; }

// 탐침 2 — 같은 이름인데 반환 타입이 다른 public 메서드를 클래스가 둔다
interface I2 { string Hello() => "I2 의 기본 구현"; }
class C2 : I2 { public int Hello() => 2; }

// 탐침 3 — 파생 인터페이스가 기반 인터페이스와 같은 시그니처를 다시 선언한다
interface I3Base { string Go(); }
interface I3 : I3Base { string Go(); }

// 탐침 4 — 구조체가 상태를 바꾸는 기본 구현에 기댄다
interface I4 { int Count { get; set; } void Bump() => Count++; }
struct S4 : I4 { public int Count { get; set; } }

// 탐침 5 — 기본 구현이 자기 자신을 부른다
interface I5 { string Loop() => Loop(); }

// 탐침 6 — 기본 구현과 같은 이름의 static 메서드를 클래스가 둔다
interface I6 { string Name() => "I6 의 기본 구현"; }
class C6 : I6 { public static string Name() => "C6 의 static"; }

// 탐침 7 — 기반 클래스의 public 메서드가 인터페이스를 대신 구현한다
interface I7 { string Tag(); }
class C7Base { public string Tag() => "C7Base 의 것"; }
class C7 : C7Base, I7 { }

class Program {
    static void Main() {
        Console.WriteLine($"탐침 1 : ((I1)new C1()).Hello() = {((I1)new C1()).Hello()}");
        Console.WriteLine($"탐침 2 : ((I2)new C2()).Hello() = {((I2)new C2()).Hello()}");
        var s = new S4(); ((I4)s).Bump();
        Console.WriteLine($"탐침 4 : ((I4)s).Bump() 뒤 s.Count = {s.Count}");
        Console.WriteLine($"탐침 6 : ((I6)new C6()).Name() = {((I6)new C6()).Name()}");
        Console.WriteLine($"탐침 7 : ((I7)new C7()).Tag() = {((I7)new C7()).Tag()}");
    }
}
===== csc -warn:9 -out:ex.dll cs17b-probe.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
cs17b-probe.cs(13,32): warning CS0108: 'I3.Go()' hides inherited member 'I3Base.Go()'. Use the new keyword if hiding was intended.
탐침 1 : ((I1)new C1()).Hello() = I1 의 기본 구현
탐침 2 : ((I2)new C2()).Hello() = I2 의 기본 구현
탐침 4 : ((I4)s).Bump() 뒤 s.Count = 0
탐침 6 : ((I6)new C6()).Name() = I6 의 기본 구현
탐침 7 : ((I7)new C7()).Tag() = C7Base 의 것
===== csc -warn:9 -out:ex.dll cs17b-probe.cs 2>&1 | grep -o "cs17b-probe.cs([0-9]*" | sort -u | wc -l    # 탐침 7개 중 진단이 붙은 줄은 몇 개인가 (exit=0) =====
1
```

- ★★★ **탐침 일곱 중 진단이 붙은 줄은 하나다** — 스크립트가 직접 세어 마지막 줄에 찍었다(`1`).

| 탐침 | 무엇을 심었나 | 답했나 | 실행하면 |
|---|---|---|---|
| 1 | 기본 구현 멤버와 **같은 이름의 `private` 메서드** | ★★★ **침묵** | 기본 구현이 불린다 — **클래스의 것은 무시** |
| 2 | 같은 이름 · **다른 반환 타입의 `public`** | ★★★ **침묵** | 기본 구현이 불린다 |
| 3 | 파생 인터페이스가 **같은 시그니처를 다시 선언** | **답함** — `CS0108` | — |
| 4 | ★★★ **구조체가 상태를 바꾸는 기본 구현에 기댐** | ★★★ **침묵** | `s.Count = 0` — (3)의 사고 |
| 5 | 기본 구현이 **자기 자신을 부름** | **침묵** | (안 불렀다 — 스택 넘침일 것이다) |
| 6 | 기본 구현과 **같은 이름의 `static`** 메서드 | **침묵** | 기본 구현이 불린다 |
| 7 | **기반 클래스의 `public`** 이 인터페이스를 채움 | **침묵** (★ 정상이다) | `C7Base 의 것` |

- ★★★ **탐침 1·2·6 이 같은 모양이다** — 클래스가 **구현하려고 쓴 것 같은** 메서드를 두었는데 **구현이 안 됐고**,\
  **기본 구현이 조용히 그 자리를 채웠다.** ★★ **기본 구현이 없었다면 `CS0737`/`CS0738`/`CS0736` 같은 에러로 드러났을 자리다** —\
  ★★★ **기본 구현이 오타·실수를 삼킨다.** 인터페이스 진화의 **대가**다.
- ★ 「기본 구현이 없었다면 에러」는 **(4)의 `CS0738` 에서 한 모양만 실측**했고, 나머지 코드(`CS0737`·`CS0736`)는 **이 판에서 안 던졌다.**
- ★★ **탐침 4 가 가장 나쁘다** — 결과가 **틀렸는데** 아무 신호가 없다.
- ★ **탐침 5 는 실행하지 않았다** — 스택 넘침은 `catch` 로 못 잡아 프로세스가 죽는다. **「안 돌려 봄」** 이다.
- ★ **탐침 7 이 침묵인 것은 정상**이다 — 기반 클래스의 공용 메서드가 인터페이스를 채우는 것은 **C# 1.0 부터의 규칙**이다.

## 문법 — 형태와 규칙

### 형태

```csharp
// cs17b-form.cs
using System;

IStore s = new MemStore();
Console.WriteLine(s.Put("k", "v"));
Console.WriteLine(s.Describe());                  // 기본 구현 — 인터페이스 변수로만 부른다
Console.WriteLine(s is IDisposable);

interface IStore {
    string Put(string k, string v);               // 구현해야 하는 멤버
    string Describe() => $"{GetType().Name} (기본 설명)";  // 기본 구현 멤버 — 나중에 추가해도 기존 구현이 안 깨진다
}
sealed class MemStore : IStore, IDisposable {
    public string Put(string k, string v) => $"{k}={v}";
    void IDisposable.Dispose() { }                // 명시적 구현 — 클래스의 공개 표면에서 숨긴다
}
```

```text
===== 소스: cs17b-form.cs =====
using System;

IStore s = new MemStore();
Console.WriteLine(s.Put("k", "v"));
Console.WriteLine(s.Describe());                  // 기본 구현 — 인터페이스 변수로만 부른다
Console.WriteLine(s is IDisposable);

interface IStore {
    string Put(string k, string v);               // 구현해야 하는 멤버
    string Describe() => $"{GetType().Name} (기본 설명)";  // 기본 구현 멤버 — 나중에 추가해도 기존 구현이 안 깨진다
}
sealed class MemStore : IStore, IDisposable {
    public string Put(string k, string v) => $"{k}={v}";
    void IDisposable.Dispose() { }                // 명시적 구현 — 클래스의 공개 표면에서 숨긴다
}
===== csc -out:ex.dll cs17b-form.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
k=v
MemStore (기본 설명)
True
```

- ★★★ **`Describe()` 는 `IStore` 변수로 불렀다** — `MemStore` 변수로는 못 부른다((2)).
- ★★ **`IDisposable.Dispose` 는 명시적 구현**이다 — `MemStore` 의 **공개 표면에 `Dispose` 가 안 보인다.**\
  ★ 이것이 명시적 구현의 두 번째 쓰임이다 — **이름 충돌이 아니라 「표면 정리」**.
- **추상 멤버는 암시적으로 `public` 이고 다른 접근 한정자를 못 붙인다**(Learn).
- **기본 구현이 있는 멤버는 접근 한정자를 붙일 수 있다**(`private` 도 — (9)의 `Secret`).
- **인터페이스는 인스턴스 필드를 못 가진다** — 그래서 (3)의 `Count` 는 **속성**으로 선언하고 구현체가 채웠다.

### 금지 사례 — 진단이 나는 꼴

| 쓴 꼴 | 진단 코드 | 어디서 |
|---|---|---|
| 인터페이스 멤버를 구현 안 함 | `CS0535`(에러) | (1) — ★★★ **인터페이스 진화의 정본 증거** |
| 같은 이름·다른 반환 타입을 공용 메서드 하나로 | `CS0738`(에러) | (4) |
| 같은 조상 멤버를 두 파생 인터페이스가 각자 덮음 | `CS8705`(에러) | (5) |
| `base(IA).Hello()` | `CS0175`·`CS0119`(에러) | (5) |
| `static abstract` 를 인터페이스 이름으로 직접 | `CS8926`(에러) | (8) |
| `static abstract` 를 가진 인터페이스를 타입 인자로 | `CS8920`(에러) | (8) |
| 파생 인터페이스가 같은 시그니처를 `new` 없이 다시 선언 | `CS0108`(**경고**) | (10) |
| 클래스 변수로 기본 구현 호출 | `CS1061`(에러) | [16번](../16-inheritance-virtual-override-abstract-sealed-new/) (8) |

★★★ **에러가 많은 주제인데 가장 나쁜 사고는 에러가 아닌 쪽에 있다** — (10)의 **침묵 여섯**과\
(1)의 **다시 컴파일 안 한 바이너리**(진단이 원리상 안 닿는 자리)다.

## 어디서 틀리나

1. ★★★ **「인터페이스에 메서드 하나 더하는 건 괜찮다」** — **본문이 없으면 모든 구현체가 깨진다**((1)).\
   다시 컴파일하면 `CS0535`, 안 하면 **`TypeLoadException`** 이다.
2. ★★★ **「다시 컴파일 안 했으니 새 멤버는 상관없다」** — **안 부르는 멤버 때문에도 타입 로드가 거부된다**((1)).
3. ★★★ **「기본 구현 멤버는 클래스가 물려받는다」** — **안 받는다**([16번](../16-inheritance-virtual-override-abstract-sealed-new/) (8)). Java 와 **정반대**((7)).
4. ★★★ **「구조체도 기본 구현으로 상태를 바꿀 수 있다」** — **바뀌는 것은 상자다**((3)). `ref` + 제네릭으로도 **안 된다.**
5. ★★ **「명시적 구현은 취향이다」** — **반환 타입만 다른 충돌은 명시적 구현 없이 못 푼다**((4) `CS0738`).
6. ★★ **「기본 구현끼리 이름이 같으면 무조건 충돌한다」** — **관련 없는 둘은 충돌이 없다**((5)). **같은 조상을 덮을 때만** `CS8705`.
7. ★★ **「기본 구현을 클래스에서 감싸 쓸 수 있다」** — **`base(IA)` 가 없다**((5) `CS0175`). Java 의 `X.super` 와 다르다.
8. ★★ **「클래스에 같은 이름을 두면 구현한 것이다」** — **`private`·다른 반환·`static` 은 구현이 아니고**, 기본 구현이 있으면 **말없이 넘어간다**((10)).
9. ★ **「`static abstract` 는 인터페이스 이름으로 부른다」** — **타입 매개변수로만**((8) `CS8926`).
10. ★ **「`static abstract` 도 가상 디스패치다」** — **컴파일 시점 타입**으로 풀린다. IL 이 `call` 이다((6)(8)).

## 구현 세부사항 대 언어 보장

| 무엇 | 층 | 근거 |
|---|---|---|
| **구현 안 한 추상 인터페이스 멤버는 컴파일 에러** | ★★★ **언어 보장(334)** | (1) `CS0535` |
| **기본 구현이 있으면 구현체가 안 채워도 된다** | ★★★ **언어 보장(334, C# 8)** | (1) |
| **기본 구현은 인터페이스 타입으로만 접근된다** | ★★★ **언어 보장(334)** · Learn | [16번](../16-inheritance-virtual-override-abstract-sealed-new/) (8) |
| **가장 구체적인 구현이 하나여야 한다** | ★★★ **언어 보장(334)** | (5) `CS8705` |
| **`static abstract` 는 타입 매개변수로만 접근** | ★★★ **언어 보장(334, C# 11)** | (8) `CS8926` |
| **계약을 못 채운 타입은 로드되지 않는다** | ★★★ **CLI 보장(335)** | (1) `TypeLoadException` |
| **`constrained.` 이 값 타입을 박싱 없이 부르되, 불가능하면 박싱한다** | ★★★ **CLI 보장(335)** | (6) |
| **예외가 `Run` 을 JIT 할 때 나는 것** | ★ **이 판의 관찰** | (1) — 타입 로드 시점은 런타임이 정한다 |
| **`Call(dim)` 이 호출당 24바이트** | ★ **이 판의 관찰**(2×2 판 격자에서 안 움직임) | (6) — 크기는 런타임의 객체 배치 |
| **`base(IA)` 가 `-langversion:preview` 에서도 안 되는 것** | ★ **이 판의 관찰** | (5) — 다음 판에서 바뀔 수 있다 |
| **`-warn:9` 에서 탐침 일곱 중 하나만 답하는 것** | ★ **이 판의 관찰** | (10) |
| **진단 문구·예외 메시지 전부** | ★ **이 판의 관찰** | 근거로는 **코드와 예외 타입**만 쓴다 |

## 언제 쓰고 언제 안 쓰나

- ★★★ **기본 구현 멤버는 「이미 배포된 인터페이스에 멤버를 더할 때」 쓴다.** 그것이 존재 이유다((1)).\
  ★ **새로 설계하는 인터페이스에 처음부터 기본 구현을 잔뜩 넣지 마라** — (10)에서 봤듯 **구현 실수를 삼킨다.**
- ★★★ **구조체가 구현할 인터페이스에는 「상태를 바꾸는 기본 구현」을 두지 마라**((3)(6)) — 결과가 **틀리고** 비용도 든다.
- ★★ **명시적 구현은 두 자리에 쓴다** — ① **반환 타입만 다른 충돌**((4)) ② **공개 표면에서 숨기고 싶은 멤버**(`IDisposable.Dispose` 를 감추고 `Close` 를 보이게 하는 관례 — (형태)).
- ★★ **「기본 구현 + 약간의 변형」이 필요하면 도우미를 `protected`/`private static` 멤버로 인터페이스에 두어라** — 클래스에서 `base(IA)` 로 부를 수 없다((5)).
- ★ **`static abstract` 는 「타입이 가진 연산」을 요구할 때** — 수·단위·파서 같은 것. **인스턴스 다형성이 필요하면 쓰지 마라**((8)).

## 핵심 문장

1. ★★★ **인터페이스에 본문 없는 멤버를 더하면 다시 컴파일한 앱은 `CS0535`, 안 한 앱은 `TypeLoadException` 이다.** 기본 구현이 둘 다 ○ 로 바꾼다((1)).
2. ★★★ **기본 구현의 `this` 는 인터페이스 참조다 — 구조체는 그 자리에서 박싱되어 원본이 안 바뀐다**((3)). 제네릭 호출에서도 **호출당 24바이트**가 네 판 모두에서 나왔다((6)).
3. ★★★ **명시적 구현은 「반환 타입만 다른 같은 이름」을 푸는 유일한 길이다** — `CS0738`((4)). `IEnumerable<T>` 가 매일 쓴다.
4. ★★ **기본 구현이 클래스로 안 내려오므로 관련 없는 두 기본 구현은 충돌하지 않는다** — Java 는 반대로 충돌한다((5)(7)).
5. ★★ **기본 구현은 구현 실수를 삼킨다** — `private`·다른 반환·`static` 메서드가 **말없이** 무시된다((10)).

## 관련 자료

- [16번 — 상속·`virtual`/`override`/`abstract`/`sealed`/`new`](../16-inheritance-virtual-override-abstract-sealed-new/) — ★★★ **이 문서의 바닥이다.**\
  **경계**: 「기본 구현이 클래스로 안 내려온다」·「`new` 가 인터페이스 슬롯을 못 건드린다」·「명시적 구현의 `private`+`final`+`virtual`」·「`callvirt` 는 널 검사」는 **거기서 쟀다.**\
  **여기서는** 그 위에서 **인터페이스 진화·이름 충돌·구조체의 숨은 박싱·`static abstract`** 만 봤다.
- [03번 — 박싱과 언박싱](../03-boxing-and-unboxing/) — **박싱 자체**의 정본이고, 이 문서가 쓰는 **IL 디스어셈블러를 만든 곳**이다.
- [14번 — 인덱서](../14-indexers/) — **명시적 구현 인덱서**가 (4)의 규칙을 따른다.
- [15번 — 접근 한정자와 어셈블리 경계](../15-access-modifiers-and-assembly-boundary/) — (1)의 **두 어셈블리** 실험과 같은 무대.
- 목록의 **24번 주제**(제네릭과 타입 매개변수)·**25번 주제**(제네릭 제약) — (6)(8)의 **`constrained.`·`where T :`** 의 정본이 될 자리다.
- Java 갈래 목록([`java/syntax/README.md`](../../../java/syntax/README.md))의 **11번**([`11-interfaces-default-methods/`](../../../java/syntax/11-interfaces-default-methods/)) —\
  **경계**: `default` 메서드의 **도입 이유·충돌 해소 세 규칙·`X.super.m()`** 은 거기가 정본이다. 여기서는 **C# 과 정반대인 두 자리**만 다시 던졌다((7)).
- Kotlin 갈래 목록([`kotlin/syntax/README.md`](../../../kotlin/syntax/README.md))의 **20번**([`20-interfaces-default-impl-and-super/`](../../../kotlin/syntax/20-interfaces-default-impl-and-super/)) — `super<T>` 로 고르는 쪽. **이 판에서 던지지 않았다.**

## 용어 풀이

- **기본 구현 멤버(default interface member)** — 본문을 가진 인터페이스 멤버(C# 8). **인터페이스 타입으로만** 불린다.
- **인터페이스 진화(interface evolution)** — 이미 배포된 인터페이스에 멤버를 더하는 것. 본문이 없으면 **파괴적 변경**이다.
- **명시적 인터페이스 구현(explicit interface implementation)** — `int INum.Read() => …` 꼴. **클래스 이름으로는 안 불린다.**
- **가장 구체적인 구현(most specific implementation)** — 인터페이스 멤버 하나에 대해 런타임이 고를 **단 하나의** 구현. 둘이면 `CS8705`.
- **`TypeLoadException`** — 런타임이 타입을 메모리에 올리다가 **계약 위반**을 발견했을 때 던지는 예외.
- **`constrained.`** — IL 접두. 「`T` 가 값 타입이면 **주소로** 부르고, 그게 안 되면 박싱해서 불러라」.
- **`static abstract` 멤버** — 구현 **타입이** 정적으로 가져야 하는 멤버(C# 11). 제네릭 수학의 바탕이다.
- **인터페이스 맵(interface map)** — 인터페이스 슬롯마다 **실제로 어느 메서드가 불리나**를 적은 표. `GetInterfaceMap` 으로 읽는다.

## 더 들어가면

- ★ **`static virtual` 멤버** — `static abstract` 의 짝으로, **기본 본문이 있는** 정적 인터페이스 멤버다. **이 판에서 안 던졌다.**
- ★ **`ref struct` 와 기본 구현** — Learn 은 「기본 구현 멤버를 더하면 그 인터페이스를 구현하는 `ref struct` 는 그 멤버를 **명시적으로 선언해야** 한다」고 적는다.\
  ★ `ref struct` 는 박싱될 수 없으니 (6)의 상자를 만들 수 없기 때문으로 읽힌다 — **이 판에서 던지지 않았다.**
- ★ **(1)의 예외 시점** — 이 판에서는 `Run` 의 JIT 때 났다. **ReadyToRun·NativeAOT** 로 미리 컴파일하면 시점이 달라질 수 있다 — **안 쟀다.**
