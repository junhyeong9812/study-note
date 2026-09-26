# csharp/syntax/13 — 속성(property)과 `init`·`required`·`field` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 이 주제의 질문은 **「컴파일러가 무엇을 만들었나」와 「컴파일러가 언제 말하나」 둘**로 갈린다 —
> 앞쪽은 **IL 과 리플렉션**으로, 뒤쪽은 **진단 코드**로 답한다.
> **환경** — .NET SDK 10.0.401 · 런타임 10.0.12 · `net10.0` · linux-x64 ·
> Roslyn `csc` 를 직접 부른다 · `-langversion:latest` · `-preferreduilang:en-US`.
> ★★★ **본체 창은 ① IL 덤프다** — 「속성은 메서드다」는 논쟁이 아니라 덤프다.
> ★★ **짝이 되는 창은 ③ 리플렉션**이다 — `init` 은 **IL 본문이 `set` 과 한 글자도 같아서**
> 시그니처의 `modreq` 를 읽어야 갈린다.
> ★ **「부적용인 창」이 있다** — **④ 할당 바이트.** 자동 구현 속성을 쓰든 필드를 쓰든
> **객체 하나에 필드 하나**이고 계산 속성은 **필드가 아예 없다**. **「안 쟀다」가 아니라 「잴 것이 없다」다.**
> ★★★ **이 파일에는 「속성 접근이 필드보다 느리다」는 문장이 없다** — 이 판에서 **안 쟀다.**
> 선행 — [12번](../12-class-fields-constructors-this-base/)(필드·생성자·초기화 순서)·[03번](../03-boxing-and-unboxing/)(IL 덤프 도구).
> 이어지는 것 — [14번](../14-indexers/)(인덱서는 **인자를 받는 속성**이다)·[15번](../15-access-modifiers-and-assembly-boundary/)(접근 한정자).
> 대비 — 파이썬 갈래 목록([`python/syntax/README.md`](../../../python/syntax/README.md))의 **33번**(`property`·디스크립터).

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (예측) / (왜) / (경계) / (연결) -->

### 1. ★★★ 이 클래스가 만든 멤버를 전부 적을 수 있나 (예측)

```csharp
// cs13b-auto.cs
using System;
using System.Reflection;

public class Box {
    public int Auto  { get; set; }       // 자동 구현 속성
    public int Once  { get; init; }      // init 접근자 (C# 9)
    public int Twice => Auto * 2;        // 계산 속성 — 식 본문
}

class Program {
    static void Main() {
        foreach (var m in typeof(Box).GetMethods(BindingFlags.Public|BindingFlags.Instance|BindingFlags.DeclaredOnly))
            Console.WriteLine($"메서드 {m.Name,-10} 특수이름={m.IsSpecialName} 반환 modreq=[{string.Join(",", Array.ConvertAll(m.ReturnParameter.GetRequiredCustomModifiers(), t => t.Name))}]");
        foreach (var f in typeof(Box).GetFields(BindingFlags.Public|BindingFlags.NonPublic|BindingFlags.Instance))
            Console.WriteLine($"필드   {f.Name}");
        Il.Dump(typeof(Box), "get_Auto");
        Il.Dump(typeof(Box), "set_Auto");
        Il.Dump(typeof(Box), "get_Twice");
    }
}
```

- **메서드가 몇 개** 나오고 이름이 각각 무엇인가?
- ★★★ **필드가 몇 개** 나오는가 — 속성이 셋인데?
- ★★ `get_Twice` 의 IL 첫 세 줄은 무엇인가 — `ldfld` 인가 `call` 인가?
- ★ `set_Once` 만 다른 칸이 하나 있다. 무엇인가?

### 2. ★★★ `init` 을 리플렉션으로 밀면 통하나 (예측)

```csharp
// cs13b-initrefl.cs
using System;
using System.Reflection;
public class Cfg { public string Name { get; init; } = "처음"; }
class Program {
    static void Main() {
        var c = new Cfg { Name = "객체 초기자가 넣음" };
        Console.WriteLine($"만든 직후   : {c.Name}");
        var setter = typeof(Cfg).GetProperty("Name")!.GetSetMethod(true)!;
        Console.WriteLine($"setter 이름 : {setter.Name}");
        Console.WriteLine($"반환 modreq : {string.Join(",", Array.ConvertAll(setter.ReturnParameter.GetRequiredCustomModifiers(), t => t.FullName))}");
        setter.Invoke(c, new object[] { "리플렉션이 나중에 밀어 넣음" });
        Console.WriteLine($"리플렉션 뒤 : {c.Name}");
    }
}
```

- **마지막 줄에 무엇이 찍히는가** — 예외인가, 바뀐 값인가?
- ★★★ `반환 modreq` 칸에 무엇이 찍히는가?
- ★★ `init` setter 와 평범한 `set` setter의 **IL 본문**은 얼마나 다른가?
- ★ 그래서 **`init` 을 막는 것은 누구인가**?

### 3. ★★ `init` 이 허용되는 자리는 몇 군데인가 (예측)

```csharp
// cs13b-initwhere.cs
using System;
record Point { public int X { get; init; } }
class Cfg {
    public string Name { get; init; } = "";
    public Cfg() { Name = "생성자에서는 된다"; }
    public void Rename() { Name = "메서드에서는?"; }
}
class Program {
    static void Main() {
        var p = new Point { X = 1 };        // 객체 초기자 — 된다
        var q = p with { X = 2 };           // with 식 — 된다
        p.X = 3;                            // 그 밖 — ?
    }
}
```

- **에러가 몇 건** 나고 **몇 행**에 붙는가?
- ★★ `p with { X = 2 }` 는 왜 통과하는가?
- ★ 같은 클래스의 평범한 메서드(`Rename`)에서 `init` 속성에 대입하면 어떻게 되는가?
- ★ 진단 코드는 무엇인가?

### 4. ★★ `required` 를 생성자에서 채우면 컴파일러가 알아주나 (예측)

```csharp
// cs13b-reqctor.cs
using System;
using System.Diagnostics.CodeAnalysis;
class Plain {
    public required string Name { get; init; }
    public Plain(string n) { Name = n; }                         // 표시 없음
}
class Marked {
    public required string Name { get; init; }
    [SetsRequiredMembers] public Marked(string n) { Name = n; }  // 표시 있음
}
class Program {
    static void Main() {
        var m = new Marked("표시한 생성자");
        Console.WriteLine(m.Name);
        var p = new Plain("표시 안 한 생성자");
    }
}
```

- **에러가 몇 건** 나고 어느 클래스에 붙는가?
- ★★★ `[SetsRequiredMembers]` 는 **검사인가 선언인가**?
- ★ 빈 생성자에 그 어트리뷰트를 붙이면 통과하는가?
- ★★ `required` 를 **런타임이 강제하는가** — 그 답은 어느 주제가 실측했나?

### 5. ★ `readonly` 필드와 `init` 속성은 어디서 갈리나 (예측)

```csharp
// cs13b-readonly.cs
using System;
class R {
    public readonly int F = 1;
    public int P { get; init; } = 1;
    public void M() { F = 2; }
}
class Program {
    static void Main() {
        var a = new R { P = 9 };     // init 속성 — 바깥에서 객체 초기자로
        var b = new R { F = 9 };     // readonly 필드 — 같은 자리에서?
    }
}
```

- **에러가 몇 건** 나고 **어느 줄**에 붙는가 — `P = 9` 인가 `F = 9` 인가?
- ★★★ 진단 문구가 읊는 **허용 목록 셋**은 무엇인가?
- ★ 객체 초기자가 그 목록에 **안 드는 이유**는 무엇인가?

### 6. ★★ `field` 키워드가 이 판에서 되나 — 그리고 이름이 겹치면 (예측)

```csharp
// cs13b-field.cs
using System;
using System.Reflection;
public class Temp {
    public int Celsius {
        get => field;                                        // C# 14 의 field 키워드
        set => field = value < -273 ? -273 : value;
    }
}
class Program {
    static void Main() {
        var t = new Temp();
        t.Celsius = -500;
        Console.WriteLine($"Celsius={t.Celsius}");
        foreach (var f in typeof(Temp).GetFields(BindingFlags.Public|BindingFlags.NonPublic|BindingFlags.Instance))
            Console.WriteLine($"필드 {f.Name} : {f.FieldType.Name}");
        Il.Dump(typeof(Temp), "get_Celsius");
    }
}
```

- **컴파일되는가** — 된다면 **필드 이름**은 무엇으로 찍히는가?
- ★ `t.Celsius` 는 얼마인가?

```csharp
// cs13b-fieldclash.cs
using System;
using System.Reflection;
public class Clash {
    private int field = 100;                       // 이미 field 라는 이름의 필드가 있다
    public int P      { get => field; set => field = value; }
    public int Direct => field;
}
class Program {
    static void Main() {
        var c = new Clash();
        c.P = 7;
        Console.WriteLine($"P={c.P}  Direct={c.Direct}");
        foreach (var f in typeof(Clash).GetFields(BindingFlags.NonPublic|BindingFlags.Instance))
            Console.WriteLine($"필드 {f.Name}");
    }
}
```

- ★★★ **`Direct` 는 얼마인가** — 100 인가 0 인가?
- ★★★ **필드가 몇 개** 찍히는가?
- ★★ 이때 나오는 것은 **에러인가 경고인가** — 코드는?

### 7. ★ `ref` 반환 속성으로 할 수 있는 것과 없는 것 (경계)

```csharp
// cs13b-ref.cs
using System;
public class Holder {
    int n = 7;
    public ref int Slot  => ref n;     // ref 로 돌려주는 속성
    public     int Plain => n;
}
class Program {
    static void Main() {
        var h = new Holder();
        h.Slot = 99;                   // set 접근자가 없는데 대입이 된다
        Console.WriteLine($"Plain={h.Plain}");
        var p = typeof(Holder).GetProperty("Slot")!;
        Console.WriteLine($"Slot 의 타입={p.PropertyType}  set 접근자={(p.SetMethod is null ? "없음" : "있음")}");
        Il.Dump(typeof(Holder), "get_Slot");
    }
}
```

- `h.Slot = 99` 가 통과하는가 — **`set` 접근자가 없는데**?
- ★★ `Slot` 의 **타입**은 무엇으로 찍히는가?
- ★★ IL 에 `ldfld` 가 나오는가 **다른 것**이 나오는가?
- ★ 자동 구현 속성을 `ref` 로 돌려주면 어떻게 되는가?

### 8. ★ `get`/`set` 접근성을 따로 주는 규칙 (경계)

- 접근자에 한정자를 붙일 때 지켜야 하는 것 **둘**은 무엇인가?
- ★★ **두 접근자 모두에** 붙이면 어떻게 되는가 — 진단 코드는?
- ★★ 바깥에서 `private set` 인 속성에 대입하면 **`CS0122` 인가 다른 코드인가** — 왜 다른가?

### 9. ★ 속성이 인터페이스와 초기자에서 어떻게 사나 (경계)

- 속성이 **인터페이스에 올 수 있는가** — 올 수 있다면 왜 자연스러운가?
- ★★ `{ get; }` 뿐인 자동 속성에 **초기자**를 붙일 수 있는가 — 채울 길이 없어 보이는데?
- ★ 그 초기자는 **언제** 도는가 — 그 순서는 어느 주제가 정본인가?

### 10. ★★★ 컴파일러가 안 보는 것은 무엇인가 (경계)

- 속성 주변 함정 **일곱**을 심고 `-warn:9` 로 물으면 **몇 줄**에 진단이 붙는가?
- ★★★ **계산 속성이 자기 자신을 부르면** 컴파일러가 말하는가 — 돌리면 어떻게 되는가?
- ★★ `public int N { get; }` 을 아무도 안 채우면 경고가 나는가 — **필드였다면** 어땠겠는가?
- ★ 이 주제에서 컴파일러가 보는 것과 안 보는 것을 **한 줄씩**으로 가를 수 있는가?

### 11. 다른 주제와 잇기 (연결)

- **초기화 순서**와 **`required` 의 런타임 구멍**은 어느 주제가 정본인가?
- ★★ **인덱서**가 이 주제와 한 사슬인 이유는 무엇인가 — 인덱서는 무엇으로 컴파일되는가?
- **접근 한정자 여섯의 전수**는 몇 번 주제인가?
- ★ 이 문서가 쓰는 **IL 디스어셈블러**는 어느 주제가 만들었나?
- **`record` 의 위치 매개변수**가 `init` 속성이 되는 것은 몇 번 주제인가?
- ★ 파이썬의 `property` 와 C# 의 속성이 갈리는 **층**은 무엇인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
