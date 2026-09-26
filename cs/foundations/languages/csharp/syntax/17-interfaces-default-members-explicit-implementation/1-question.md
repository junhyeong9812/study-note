# csharp/syntax/17 — 인터페이스·기본 구현 멤버·명시적 구현 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> ★★★ 이 주제의 질문은 「**다시 컴파일했나 안 했나**」를 늘 갈라 묻는다 — 같은 사고를 **컴파일러와 런타임이 각각** 말한다.
> **환경** — .NET SDK 10.0.401 · 런타임 10.0.12 · `net10.0` · linux-x64 ·
> Roslyn `csc` 를 직접 부른다 · `-langversion:latest` · `-preferreduilang:en-US`. 대비는 **javac 21.0.5** 다.
> ★★★ **본체 창은 ② 진단이다** — 그런데 **다시 컴파일 안 한 바이너리**는 진단이 원리상 못 본다.
> 그 칸은 **실행 출력의 예외 타입**으로 물었다(**제5의 상태 — 창을 바꿔 답한 것**).
> ★★ **④ 할당 바이트는 적용이다**(16편에서는 부적용이었다) — 2×2 판 격자로 쟀고 **시간은 안 쟀다.**
> 선행 — [16번](../16-inheritance-virtual-override-abstract-sealed-new/)(★★★ **기본 구현이 클래스로 안 내려오는 것**은 거기서 쟀다)·[03번](../03-boxing-and-unboxing/)(박싱).
> 대비 — Java 갈래 목록([`java/syntax/README.md`](../../../java/syntax/README.md))의 **11번**([`11-interfaces-default-methods/`](../../../java/syntax/11-interfaces-default-methods/)).

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (예측) / (왜) / (경계) / (연결) -->

### 1. ★★★ 라이브러리의 인터페이스만 바꿔 끼우면 (예측)

앱(`ex.dll`)은 아래 v1 라이브러리로 **한 번만** 컴파일했다. 그 뒤 **라이브러리만** 두 가지 v2 로 바꿔 끼운다.

```csharp
// cs17b-lib1.cs
public interface ILog {
    string Write(string m);
}
```

```csharp
// cs17b-app.cs
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
```

```csharp
// cs17b-lib2abs.cs
public interface ILog {
    string Write(string m);
    string Flush();                          // 새 멤버 — 본문이 없다
}
```

```csharp
// cs17b-lib2dim.cs
public interface ILog {
    string Write(string m);
    string Flush() => "ILog 의 기본 Flush";     // 새 멤버 — 본문이 있다 (C# 8)
}
```

- 첫 판(v1 끼리)은 무엇을 찍는가?
- ★★★ `cs17b-lib2abs.cs` 로 바꿔 끼우고 **앱은 다시 컴파일하지 않은 채** 돌리면 무엇이 찍히는가 — 「쓴다 a」는 찍히는가?
- ★★★ 같은 앱을 그 라이브러리로 **다시 컴파일하면** 어떤 진단 코드가 나오는가?
- ★★★ `cs17b-lib2dim.cs` 로 바꿔 끼우면 — 다시 컴파일한 쪽과 안 한 쪽이 각각 어떻게 되는가?
- ★ 이 네 칸이 **기본 구현 멤버가 C# 8 에 들어온 이유**와 어떻게 이어지는가?

### 2. ★★ 관련 없는 두 인터페이스가 같은 이름의 기본 구현을 줄 때 (예측)

```csharp
// cs17b-twin.cs
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
```

- ★★★ **컴파일이 되는가?**
- 되면 네 줄에 무엇이 찍히는가?
- ★ 이 결과가 「기본 구현이 클래스로 안 내려온다」와 어떻게 이어지는가?

### 3. ★★ 같은 조상의 멤버를 두 파생 인터페이스가 각자 덮으면 (예측)

```csharp
// cs17b-diamond.cs
using System;
interface IBase  { string Hello() => "IBase"; }
interface ILeft  : IBase { string IBase.Hello() => "ILeft"; }    // 기반 인터페이스의 기본 구현을 덮는다
interface IRight : IBase { string IBase.Hello() => "IRight"; }
class Both : ILeft, IRight { }
class Program { static void Main() { Console.WriteLine(((IBase)new Both()).Hello()); } }
```

- 컴파일이 되는가 — 안 되면 진단 코드는?
- ★★ 2번과 무엇이 달라서 결과가 갈리는가 — **슬롯**이라는 말로 설명할 수 있는가?

### 4. ★★★ 기본 구현이 상태를 바꾼 뒤의 원본 (예측)

```csharp
// cs17b-this.cs
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
```

- `[1]`\~`[4]` 의 `this.GetType()` 은 각각 무엇인가?
- ★★★ `c.Count` · `s.Count`(두 번) · `o.Count` 는 각각 몇인가?
- ★★★ `[3]` 은 **`ref` 로 넘기고 제네릭 제약으로** 불렀다 — 그래도 원본이 안 바뀐다면 왜인가?

### 5. ★★ 같은 모양을 javac 에 던지면 (예측)

```java
// Ex17.java
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
```

```java
// Both.java
interface Left  { default String hello() { return "Left.hello"; } }
interface Right { default String hello() { return "Right.hello"; } }
class Both implements Left, Right { }               // 아무것도 안 적었다
```

- ★★★ `p.hello()` 는 **클래스 변수로** 도는가 — `getMethod("hello")` 는 찾아지는가?
- ★★★ `Both.java` 는 컴파일되는가 — **C# 2번의 `Both`** 와 같은가?
- ★ `Left.super.hello()` 에 해당하는 C# 문법이 있는가?

### 6. ★ `static abstract` 멤버를 부르는 세 방식 (예측)

```csharp
// cs17b-saerr.cs
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
```

- 세 줄 중 **몇 번째 줄**이 막히는가 — 각각의 진단 코드는?
- ★ 막히지 않는 줄은 **무엇을 타입 인자로** 줬는가?

### 7. ★★★ 반환 타입만 다른 같은 이름 — 공용 메서드 하나로 안 되는 이유 (왜)

- `interface IText { string Read(); }` 와 `interface INum { int Read(); }` 를 한 클래스가 구현한다. `public string Read()` 하나만 두면 **어떤 진단**이 나오는가?
- ★★★ 그것을 푸는 **한 줄**은 무엇이고, 왜 그 한 줄은 공용 `Read` 와 **충돌하지 않는가**?
- ★★ BCL 에서 이 모양을 **매일** 쓰는 인터페이스 쌍은 무엇인가?

### 8. ★★ 제네릭 제약으로 기본 구현을 부르는 IL 과 그 비용 (왜)

- `static string B<T>(T t) where T : IGreet => t.Hello();` 의 IL 에 `callvirt` 앞에 붙는 **접두**는 무엇이고, 그 접두의 뜻은?
- ★★★ `T` 가 **기본 구현에 기대는 빈 구조체**일 때와 **스스로 구현한 구조체**일 때, 1000회 호출의 할당 바이트는 각각 어떤가?
- ★★ 그 바이트가 **2×2 판 격자**(csc 최적화 × 티어링)에서 움직였는가 — 근거로 쓸 수 있는가?
- ★ `static abstract` 멤버를 부르는 IL 은 `callvirt` 인가 `call` 인가 — 왜인가?

### 9. ★★ 클래스 안에서 특정 인터페이스의 기본 구현을 부르기 (경계)

- `base(IA).Hello()` 는 되는가 — `-langversion:preview` 에서는?
- ★★ Java 의 무엇과 대비되는가?
- ★ 그래서 「기본 구현을 감싸서 조금 바꾸기」가 필요할 때 인터페이스 쪽에 무엇을 두어야 하는가?

### 10. ★★ 기본 구현 옆에 심은 함정들 (경계)

- 다음을 심고 `-warn:9` 로 물었다 — ① 기본 구현과 같은 이름의 `private` 메서드 ② 같은 이름·다른 반환 타입의 `public` 메서드 ③ 파생 인터페이스가 같은 시그니처를 다시 선언 ④ 구조체가 상태를 바꾸는 기본 구현에 기댐 ⑤ 기본 구현이 자기 자신을 부름 ⑥ 같은 이름의 `static` 메서드 ⑦ 기반 클래스의 `public` 이 인터페이스를 채움.
- **몇 줄**에 진단이 붙는가 — 어느 것이 답하는가?
- ★★★ ①·②·⑥ 을 실행하면 **누구의 메서드**가 불리는가 — 기본 구현이 **없었다면** 어떻게 드러났을 자리인가?

### 11. ★ 인터페이스 멤버의 한정자 조합 (경계)

- 리플렉션으로 보면 `static abstract` 멤버의 `IsAbstract`·`IsVirtual`·`IsStatic` 은 각각 무엇인가 — **클래스에서는 가능한 조합인가**?
- ★ 기본 구현 멤버의 `IsAbstract`·`IsVirtual` 은? 인터페이스에 `private` 멤버를 둘 수 있는가?
- ★ 기본 구현에 기댄 클래스의 **인터페이스 맵**은 그 슬롯을 누구로 채우는가?

### 12. 다른 주제와 잇기 (연결)

- ★★★ **기본 구현이 클래스로 안 내려온다**는 것을 `CS1061` 과 리플렉션으로 잰 것은 몇 번 주제인가?
- **박싱 자체**와 이 문서의 **IL 디스어셈블러**는 몇 번 주제가 정본인가?
- ★ Java `default` 메서드의 **충돌 해소 세 규칙**은 어느 갈래 몇 번인가?
- ★ `constrained.`·`where T :` 의 정본이 될 자리는 이 목록의 몇 번 주제인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
