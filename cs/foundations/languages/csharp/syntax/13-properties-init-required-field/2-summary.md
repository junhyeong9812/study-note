# csharp/syntax/13 — 속성(property)과 `init`·`required`·`field` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [ECMA-334 7판(2023-12)](https://ecma-international.org/publications-and-standards/standards/ecma-334/) ·
> [Learn — 속성](https://learn.microsoft.com/en-us/dotnet/csharp/programming-guide/classes-and-structs/properties) ·
> [Learn — `init` 접근자](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/keywords/init) ·
> [Learn — `required` 한정자](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/keywords/required) ·
> [Learn — `field` 키워드(C# 14)](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/keywords/field) ·
> [.NET API — `IsExternalInit`](https://learn.microsoft.com/en-us/dotnet/api/system.runtime.compilerservices.isexternalinit)
> **실행 검증** — 이 문서의 모든 출력·진단·IL 은 아래 「이 판」의 도구로 **실제로 돌려 얻은 것**이다(2026-09-26).\
> ★ 블록은 캡처 스크립트가 파일로 받아 조립기가 끼워 넣은 것이다 — 사람이 옮겨 적은 줄은 하나도 없다.\
> ★ 소스 펜스의 배너도 **캡처가 찍은 것**이다. 원고에 손으로 쓴 배너는 없다.\
> ★★★ **진단 언어를 영어로 고정했다**(`DOTNET_CLI_UI_LANGUAGE=en` + `-preferreduilang:en-US`).\
> **던진 형태** — MSBuild 를 안 쓰고 Roslyn `csc` 를 직접 부른다(설정은 [12번](../12-class-fields-constructors-this-base/) 머리말과 같다).
> **버전** — 속성은 **C# 1.0부터** · 자동 구현 속성은 **C# 3** · 자동 속성 초기자와 getter-only 는 **C# 6** ·\
> **`init` 은 C# 9** · **`required` 는 C# 11** · **`field` 키워드는 C# 14**다. `-langversion:latest` 로 던졌다.
> **경계** — **필드·생성자·초기화 순서**는 [12번](../12-class-fields-constructors-this-base/), **인덱서**는 [14번](../14-indexers/),\
> **접근 한정자의 전모**는 [15번](../15-access-modifiers-and-assembly-boundary/), **`record`** 는 목록의 **18번 주제**가 정본이다.\
> 여기서는 「**속성이 무엇으로 번역되고, 컴파일러가 언제 말하는가**」만 센다.\
> ★ **캡슐화라는 개념 자체**는 [`oop-basics/`](../../../../oop-basics/)가 정본이고, 여기는 **C# 문법**이다.
> ★★ **대비** — 파이썬 갈래 목록([`python/syntax/README.md`](../../../python/syntax/README.md))의 **33번**(`property`·디스크립터)이 같은 질문을 다룬다.\
> 파이썬의 `property` 는 **라이브러리 객체**이고 C# 의 속성은 **언어 문법**이라는 것이 갈림인데, **이 판에서 파이썬은 안 던졌다.**
>
> ★★ **흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | 진단 **문구** — 판마다 다듬인다 | ★★★ **진단 코드**(`CS8852`·`CS9035`·`CS0273`·`CS9258`…)와 **`(행,열)`** |
> | 컴파일러가 만든 **숨은 필드 이름의 형식** | ★★★ **숨은 필드가 있다는 사실과 그 개수** |
> | **IL 오프셋 폭**(`IL_0006`)이 판마다 달라질 수 있다는 것 | ★★★ **옵코드 이름과 순서**(`ldfld`·`stfld`·`call`·`ldflda`) |
> | ★ **증분의 절댓값 일부** — 이 주제는 그 칸을 **안 세웠다**(아래 (0)) | ★★ **`cc exit` 와 `run exit`**(갈라 적었다) · **`modreq` 목록** |
> | 여러 진단이 나올 때 Roslyn 이 내는 **순서** — 그래서 `\| sort` 를 배너에 적었다 | ★ **`-warn:9` 에서 답한 탐침의 개수** |

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
| **언어 명세(ECMA-334)** | C# 언어가 약속한 것 | ★★★ **속성이 접근자 메서드로 컴파일된다는 것 자체** · `init` 이 허용되는 자리 · `required` 검사 · 접근자 접근성 규칙 |
| **런타임·BCL 구현** | CoreCLR·Roslyn 이 그렇게 하는 것 | ★★ **숨은 필드 이름**(`<X>k__BackingField`) · **`IsExternalInit` 이라는 표식의 선택** · IL 의 구체적 모양 |
| **이 판의 관찰** | .NET 10.0.12 · linux-x64 에서 이번에 본 것 | 진단 문구 · `run exit=134` · `-warn:9` 가 답한 탐침 수 |

★★★ **이 주제는 첫 칸과 둘째 칸이 한 줄 위아래로 붙어 있다.**\
「**속성은 메서드다**」는 명세가 정한 것이지만, 「**그 메서드 이름이 `get_X` 이고 숨은 필드 이름이 `<X>k__BackingField` 다**」는 Roslyn 이 정한 것이다.\
(1)에서 그 선을 긋고, 그 뒤로는 매 절마다 다시 긋는다.

## 한눈에 — 쉽게 말하면

**속성은 「필드처럼 생긴 메서드 한 쌍」이다.**

은행 창구를 생각하자.\
**필드**는 금고 문을 그냥 열어 두는 것이다 — 누구나 손을 넣어 꺼내고 넣는다.\
**속성**은 창구 직원 둘을 세우는 것이다 — **내주는 직원**(`get`)과 **받는 직원**(`set`).\
겉에서 보면 `p.Name` 이라 금고를 직접 만지는 것 같은데, **실제로는 직원을 부르고 있다.**

| 비유 | 실체 | 어디서 보나 |
|---|---|---|
| 창구 직원 둘 | ★★★ **`get_Name`·`set_Name` 두 메서드** | (1) IL |
| 창구 뒤의 금고 | **숨은 필드 `<Name>k__BackingField`** | (1) 리플렉션 |
| 받는 직원이 **개점 시간에만** 일한다 | ★★★ **`init` 접근자**(C# 9) | (2)(3) |
| 개점 시간 규칙을 **본사가 아니라 지점장이** 검사한다 | ★★★ **`init` 은 런타임이 아니라 컴파일러가 막는다** | (2) |
| 통장 없이는 계좌를 못 연다 | **`required`**(C# 11) | (4) |
| 금고가 **아예 없는** 창구 | **계산 속성**(식 본문) — 저장소가 없다 | (1) |
| 금고 이름을 **안 지어도 되게** 해 준 것 | **`field` 키워드**(C# 14) | (9) |

> **자동 구현 속성(auto-implemented property)** — `public int X { get; set; }` 처럼 몸통을 안 쓴 속성.\
> 컴파일러가 **숨은 필드 하나와 접근자 둘**을 대신 만든다((1)).

> **계산 속성(computed property)** — `public int Y => X * 2;` 처럼 값을 **그때 계산**하는 속성.\
> ★ **숨은 필드가 안 생긴다**((1)) — 「속성 = 필드 + 껍데기」가 아니라는 증거다.

> ★★ **한국어 「속성」이 둘을 가리킨다.** 이 문서에서 **속성**은 언제나 **property**다.\
> 어트리뷰트(`[Obsolete]` 같은 `attribute`)는 **어트리뷰트**라고만 적고 「속성」이라 부르지 않는다.\
> ★ (2)에서 `RequiredMemberAttribute` 가 나오는데, 그것은 **어트리뷰트**이지 속성이 아니다.

```text
   소스에 쓴 것                         컴파일러가 만든 것

   public int Auto { get; set; }        ┌─ int get_Auto()            ← 메서드
                                        ├─ void set_Auto(int value)  ← 메서드
                                        └─ int <Auto>k__BackingField ← 필드

   public int Twice => Auto * 2;        └─ int get_Twice()           ← 메서드만. 필드 없음

   public int Once { get; init; }       ┌─ int get_Once()
                                        ├─ void set_Once(int value)  ← ★ 반환에 modreq 가 붙는다
                                        └─ int <Once>k__BackingField
```

- ★★★ **`init` 은 새 옵코드도 새 런타임 검사도 아니다.** `set_Once` 는 **평범한 setter** 인데\
  **반환 타입에 `modreq(IsExternalInit)` 라는 표식**이 붙어 있을 뿐이다((2)).\
  표식을 읽고 거절하는 것은 **컴파일러**이고, **런타임은 그냥 부른다**((2)에서 리플렉션으로 뚫는다).

## 이 주제가 답하려는 질문

1. **속성은 무엇으로 컴파일되나** — 자동 구현·계산·`init` 이 각각 무엇을 만드나((1)).
2. **`init` 을 누가 막나** — 컴파일러인가 런타임인가, 그리고 **어디까지 허용되나**((2)(3)).
3. **`required` 가 강제하는 것과 못 막는 것**((4)) — [12번](../12-class-fields-constructors-this-base/)이 값으로 잡은 구멍을 **여기서는 진단으로** 다시 본다.
4. **컴파일러가 무엇을 안 보나**((10)) — 속성 주변의 함정 일곱 중 몇 개가 답하나.

## 동작 방식

### (0) 이 주제가 쓰는 창

| 창 | 무엇을 보여 주나 | 이 주제에서 |
|---|---|---|
| ★★★ **① IL 덤프** | ★★★ **속성이 메서드로 번역된 결과 자체** — 이 주제의 본체 | (1)(2)(8)(9) |
| ★★ **② 진단 격자**(`-warn:9`) | 컴파일러가 보는 것과 안 보는 것 | (3)(4)(5)(6)(8)(10) |
| ★★ **③ 리플렉션** | ★★★ **`modreq(IsExternalInit)`** · 숨은 필드 · `IsSpecialName` | (1)(2) |
| ★ **④ 할당 바이트** | ★★ **부적용** — 아래 | — |

- ★★★ **본체는 ① IL 덤프다.** 이 주제의 결론(「속성은 메서드다」)은 **논쟁이 아니라 덤프**다.\
  덤프는 [03번](../03-boxing-and-unboxing/)이 만든 디스어셈블러를 그대로 쓴다 —\
  `MethodBody.GetILAsByteArray()` 로 본문 바이트를 받고 `OpCodes` 의 정적 필드를 리플렉션으로 긁어 옵코드 표를 만든다. **외부 도구가 0개**다.
- ★★★ **③ 리플렉션이 이 주제에서는 ①과 짝이다.** `init` 은 **IL 본문이 `set` 과 한 글자도 같아서**((2))\
  본문 덤프만으로는 아무것도 안 보인다. **시그니처의 `modreq`** 를 리플렉션으로 읽어야 갈린다.
- ★★ **「부적용인 창」 — ④ 할당 바이트.** 자동 구현 속성을 쓰든 필드를 직접 쓰든 **객체 하나에 필드 하나**다.\
  계산 속성은 **필드가 아예 없어** 견줄 짝이 없다. **「재 봤더니 같았다」가 아니라 「잴 것이 없다」다**(규칙 18-B).
- ★★★ **그래서 이 문서에는 「속성 접근이 필드보다 느리다」는 문장이 한 줄도 없다.**\
  (1)의 덤프가 보여 주는 것은 「**`ldfld` 앞에 `call` 이 하나 더 있다**」는 **형태**이지 **비용**이 아니다.\
  비용을 말하려면 JIT 의 인라인 여부를 재야 하고, **이 판에서는 그 하네스를 안 만들었다.**

### (1) ★★★ 속성은 메서드다 — IL 로 본다

**언제 쓰나** — 속성을 쓸 때마다. **이 절이 이 주제의 중심이다.**

```text
===== 소스: cs13b-auto.cs =====
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
===== csc -r:il.dll -out:ex.dll cs13b-auto.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
메서드 get_Auto   특수이름=True 반환 modreq=[]
메서드 set_Auto   특수이름=True 반환 modreq=[]
메서드 get_Once   특수이름=True 반환 modreq=[]
메서드 set_Once   특수이름=True 반환 modreq=[IsExternalInit]
메서드 get_Twice  특수이름=True 반환 modreq=[]
필드   <Auto>k__BackingField
필드   <Once>k__BackingField
--- Box.get_Auto ---
  IL_0000: ldarg.0
  IL_0001: ldfld Box::<Auto>k__BackingField
  IL_0006: ret
--- Box.set_Auto ---
  IL_0000: ldarg.0
  IL_0001: ldarg.1
  IL_0002: stfld Box::<Auto>k__BackingField
  IL_0007: ret
--- Box.get_Twice ---
  IL_0000: ldarg.0
  IL_0001: call Box::get_Auto
  IL_0006: ldc.i4.2
  IL_0007: mul
  IL_0008: ret
```

- ★★★ **접근자 셋이 전부 진짜 메서드로 나왔다.** `IsSpecialName=True` 는 「이건 사람이 직접 부르라고 만든 이름이 아니다」라는 표시다.
- ★★★ **숨은 필드는 둘뿐이다** — `Auto` 와 `Once` 것. **`Twice` 것이 없다.**\
  계산 속성은 **저장소를 안 만든다** — 「속성은 필드에 껍데기를 씌운 것」이라는 흔한 그림이 여기서 깨진다.
- ★★★ **`get_Twice` 안에서 `call Box::get_Auto` 가 보인다.** 소스에 `Auto * 2` 라고 쓴 것이\
  **필드 읽기가 아니라 메서드 호출**로 번역됐다. 속성을 속성 안에서 쓰면 **호출이 쌓인다.**
- ★★ **`ldfld`/`stfld` 한 줄이 접근자의 전부다.** 자동 구현 속성의 본문에는 그 밖에 아무것도 없다.
- ★ **`set_Once` 의 `반환 modreq=[IsExternalInit]`** 만 다르다 — (2)가 그것을 판다.

> **어느 층인가** — ★★★ **「속성이 접근자 메서드로 컴파일된다」는 명세다**(ECMA-334 §15.7 이 접근자를 함수 멤버로 정의한다).\
> ★★ **「이름이 `get_X`/`set_X` 이고 숨은 필드가 `<X>k__BackingField` 다」는 Roslyn 의 선택**이다 — 바뀔 수 있다.\
> ★ **「계산 속성에 저장소가 없다」는 다시 명세다** — 몸통이 있는 접근자에는 컴파일러가 필드를 만들 이유가 없다.

### (2) ★★★ `init` 은 런타임이 아니라 컴파일러가 막는다

**언제 쓰나** — 「만들 때만 채우고 그 뒤로는 못 바꾸는」 속성을 원할 때.

먼저 **IL 본문**을 `set` 과 나란히 놓는다.

```text
===== 소스: cs13b-initil.cs =====
using System;
public class Cfg {
    public string Name  { get; init; } = "";
    public string Loose { get; set;  } = "";
}
class Program {
    static void Main() {
        Il.Dump(typeof(Cfg), "set_Name");
        Il.Dump(typeof(Cfg), "set_Loose");
    }
}
===== csc -r:il.dll -out:ex.dll cs13b-initil.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
--- Cfg.set_Name ---
  IL_0000: ldarg.0
  IL_0001: ldarg.1
  IL_0002: stfld Cfg::<Name>k__BackingField
  IL_0007: ret
--- Cfg.set_Loose ---
  IL_0000: ldarg.0
  IL_0001: ldarg.1
  IL_0002: stfld Cfg::<Loose>k__BackingField
  IL_0007: ret
```

- ★★★ **한 글자도 같다.** `set_Name`(init) 과 `set_Loose`(set) 의 본문이 `ldarg.0 / ldarg.1 / stfld / ret` 로 똑같다.\
  ★ **여기서 멈추면 「`init` 은 아무것도 아니다」라는 틀린 결론이 나온다.** 창을 바꿔야 한다.

그래서 **리플렉션으로 시그니처**를 읽는다.

```text
===== 소스: cs13b-initrefl.cs =====
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
===== csc -out:ex.dll cs13b-initrefl.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
만든 직후   : 객체 초기자가 넣음
setter 이름 : set_Name
반환 modreq : System.Runtime.CompilerServices.IsExternalInit
리플렉션 뒤 : 리플렉션이 나중에 밀어 넣음
```

- ★★★ **`modreq` 가 `System.Runtime.CompilerServices.IsExternalInit` 이다.**\
  `modreq`(required custom modifier)는 **메서드 시그니처에 붙는 표식**이고, **읽는 쪽이 모르면 그 메서드를 못 쓰게** 되어 있다.\
  C# 컴파일러는 이 표식을 보고 「객체 초기자·생성자·`init` 접근자 밖에서는 거절」한다.
- ★★★ **그런데 `setter.Invoke` 는 그냥 통과한다.** 다 만들어진 객체의 `init` 속성이 **나중에 바뀌었다.**\
  **런타임은 `modreq` 를 검사하지 않는다** — 그것은 **컴파일러에게 보내는 쪽지**다.
- ★★ **이것이 [12번](../12-class-fields-constructors-this-base/)의 `required` 실측과 같은 집안이다.**\
  거기서는 `GetUninitializedObject` 가 `required` 를 그냥 지나갔고(`Host=null`·`Port=0`),\
  **`RequiredMemberAttribute` 는 타입에 박혀 있었다.** 여기 `init` 도 똑같다 — **표식은 남고 강제는 컴파일 시점뿐**이다.
- ★ **그래서 신뢰 경계를 넘는 데이터에는 `init` 도 `required` 도 방어가 아니다.** 방어는 생성자 안의 검사다.

> **어느 층인가** — ★★★ **「`init` 이 컴파일 시점 검사다」는 명세**다(ECMA 는 `init` 접근자를 대입 가능한 문맥으로 정의한다).\
> ★★ **「표식이 `IsExternalInit` 이라는 빈 클래스의 `modreq` 다」는 구현**이다 — 다른 표식으로 바꿔도 명세는 안 깨진다.\
> ★★★ **「런타임이 안 막는다」는 관찰이자 설계**다 — CLI 명세는 `modreq` 를 **호출 규약이 아니라 시그니처 일치**에 쓴다.

### (3) ★ `init` 이 허용되는 자리 — 셋뿐이다

```text
===== 소스: cs13b-initwhere.cs =====
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
===== csc -out:ex.dll cs13b-initwhere.cs 2>&1 | sort (cc exit=1) =====
cs13b-initwhere.cs(12,9): error CS8852: Init-only property or indexer 'Point.X' can only be assigned in an object initializer, or on 'this' or 'base' in an instance constructor or an 'init' accessor.
cs13b-initwhere.cs(6,28): error CS8852: Init-only property or indexer 'Cfg.Name' can only be assigned in an object initializer, or on 'this' or 'base' in an instance constructor or an 'init' accessor.
```

- ★★★ **진단 문구가 허용 목록을 그대로 읊는다** — 「객체 초기자 · 인스턴스 생성자의 `this`/`base` · `init` 접근자」.
- ★ **`with` 식은 에러가 안 났다.** `p with { X = 2 }` 가 통과한 것이 그 증거다 —\
  `with` 는 **복사 생성자 안에서** 대입하므로 「생성자의 `this`」에 해당한다.
- ★★ **같은 클래스의 평범한 메서드에서도 막힌다**(`Cfg.Rename`). 「내 클래스니까 된다」가 아니다 — **시점**이 기준이다.
- ★ 진단 코드는 **`CS8852`** 하나다. 두 자리 모두 같은 코드가 나왔다.

```text
   객체 하나의 일생 ──────────────────────────────────────────────>

   [생성자 본문]  [객체 초기자]  [with 식]        [그 밖의 모든 코드]
        │              │            │                    │
   init │  ○ 된다      │ ○ 된다     │ ○ 된다(복사 생성자)  │  ✕ CS8852
   set  │  ○           │ ○          │ ○                   │  ○ 언제든
   readonly 필드 │ ○ (선언한 타입 안에서만) │  ✕ CS0191 ← 객체 초기자도 「바깥 코드」다

   ★★★ init 의 경계는 「누가 부르나」가 아니라 「언제인가」다.
```

### (4) ★★ `required` — 컴파일러가 언제 말하나

```text
===== 소스: cs13b-required.cs =====
using System;
class User {
    public required string Name { get; init; }
    public int Age { get; set; }
}
class Program {
    static void Main() {
        var a = new User { Name = "가" };
        var b = new User { Age = 3 };
        var c = new User();
    }
}
===== csc -out:ex.dll cs13b-required.cs 2>&1 | sort (cc exit=1) =====
cs13b-required.cs(10,21): error CS9035: Required member 'User.Name' must be set in the object initializer or attribute constructor.
cs13b-required.cs(9,21): error CS9035: Required member 'User.Name' must be set in the object initializer or attribute constructor.
```

- ★★★ **빠진 객체 초기자마다 한 건씩** 나왔다 — `new User { Age = 3 }` 과 `new User()` 둘 다.\
  ★ **`new User { Name = "가" }` 은 조용하다.** 진단이 **속성마다**가 아니라 **생성 지점마다** 붙는다.
- ★★ 진단 코드 **`CS9035`** 는 [12번](../12-class-fields-constructors-this-base/)에서 본 것과 같다.

생성자로 채우면 어떻게 되나.

```text
===== 소스: cs13b-reqctor.cs =====
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
===== csc -out:ex.dll cs13b-reqctor.cs (cc exit=1) =====
cs13b-reqctor.cs(15,21): error CS9035: Required member 'Plain.Name' must be set in the object initializer or attribute constructor.
```

- ★★★ **생성자 안에서 `Name = n` 을 해도 컴파일러는 모른다.** `Plain` 쪽이 `CS9035` 로 막혔다.
- ★★★ **`[SetsRequiredMembers]` 를 붙인 `Marked` 만 통과**했다 — ★ **이것은 검사가 아니라 면제 선언**이다.\
  컴파일러는 그 생성자가 정말 채우는지 **확인하지 않는다.** 빈 생성자에 붙여도 통과한다.
- ★ 그래서 `required` 는 「**채웠음을 증명하라**」가 아니라 「**채웠다고 말하라**」다.

접근성이 어긋나면.

```text
===== 소스: cs13b-reqvis.cs =====
class W { public required int N { get; private init; } }
class Program { static void Main() { } }
===== csc -out:ex.dll cs13b-reqvis.cs (cc exit=1) =====
cs13b-reqvis.cs(1,31): error CS9032: Required member 'W.N' cannot be less visible or have a setter less visible than the containing type 'W'.
```

- ★★ **`required` 인데 setter 가 더 좁으면 `CS9032`.** 바깥에서 채우라고 강제해 놓고 채울 길을 막으면 모순이라서다.

```text
   컴파일 시점 ─────────────────┊───────────── 런타임 ────────────>
                                ┊
   new User { … }  ──> CS9035 검사 ○   ┊   new User { … }      ──> 그냥 돈다
   new Plain("…")  ──> CS9035 검사 ○   ┊   GetUninitializedObject ──> ★ 아무 검사 없음
   [SetsRequiredMembers] ──> 검사 면제  ┊        (12번 (7)이 실측)
                                ┊
   RequiredMemberAttribute 는 타입에 박혀 있다 ── 읽는 것은 컴파일러뿐
```

> ★★ **`required` 가 못 막는 것** — [12번](../12-class-fields-constructors-this-base/) (7)이 이미 실측했다:\
> `RuntimeHelpers.GetUninitializedObject` 로 만들면 **`required` 를 통째로 건너뛴다.**\
> 여기서 다시 재지 않는다 — **같은 사실이고, 그쪽이 정본**이다.

### (5) ★ `readonly` 필드와 `init` 속성은 무엇이 다른가

```text
===== 소스: cs13b-readonly.cs =====
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
===== csc -out:ex.dll cs13b-readonly.cs 2>&1 | sort (cc exit=1) =====
cs13b-readonly.cs(10,25): error CS0191: A readonly field cannot be assigned to (except in a constructor or init-only setter of the type in which the field is defined or a variable initializer)
cs13b-readonly.cs(5,23): error CS0191: A readonly field cannot be assigned to (except in a constructor or init-only setter of the type in which the field is defined or a variable initializer)
```

- ★★★ **`init` 속성은 바깥의 객체 초기자에서 채워지고**(에러가 안 났다), **`readonly` 필드는 거기서 막힌다**(`CS0191`).
- ★★ **`readonly` 는 「누가」가 아니라 「어디에 쓰인 코드인가」로 가른다** — 진단 문구가 그 목록을 읊는다:\
  **선언한 타입의 생성자 · `init` setter · 변수 초기자.** 객체 초기자는 **호출한 쪽 코드**라 거기 안 든다.
- ★ 즉 `init` 속성은 「**바깥이 한 번은 채울 수 있는 불변**」이고, `readonly` 필드는 「**바깥은 아예 못 채우는 불변**」이다.
- ★★ **둘 다 「참조만 고정한다」는 점은 같다** — [12번](../12-class-fields-constructors-this-base/)이 `readonly int[]` 의 원소가 바뀌는 것을 이미 실측했다.

### (6) ★ `get`/`set` 접근성을 따로 주기

```text
===== 소스: cs13b-accessor.cs =====
class Bad {
    public  int A { public get; set; }
    private int B { get; private set; }
    public  int C { protected get; private set; }
}
class Program { static void Main() { } }
===== csc -out:ex.dll cs13b-accessor.cs 2>&1 | sort (cc exit=1) =====
cs13b-accessor.cs(2,28): error CS0273: The accessibility modifier of the 'Bad.A.get' accessor must be more restrictive than the property or indexer 'Bad.A'
cs13b-accessor.cs(3,34): error CS0273: The accessibility modifier of the 'Bad.B.set' accessor must be more restrictive than the property or indexer 'Bad.B'
cs13b-accessor.cs(4,17): error CS0274: Cannot specify accessibility modifiers for both accessors of the property or indexer 'Bad.C'
```

- ★★★ **한쪽만, 더 좁게, 한 접근자에만** — 규칙 셋이 진단 둘로 나온다.
  - `CS0273` — 접근자는 **속성보다 좁아야** 한다. `public int A { public get; … }` 은 같은 높이라 거절.
  - `CS0274` — **두 접근자 모두에** 한정자를 붙일 수 없다.
- ★ 그래서 실무에서 쓰는 꼴은 사실상 하나다 — **`public int Value { get; private set; }`**.

```text
===== 소스: cs13b-privset.cs =====
using System;
class Counter {
    public int Value { get; private set; }
    public void Bump() => Value++;
}
class Program {
    static void Main() {
        var c = new Counter();
        c.Bump();
        Console.WriteLine(c.Value);
        c.Value = 10;
    }
}
===== csc -out:ex.dll cs13b-privset.cs (cc exit=1) =====
cs13b-privset.cs(11,9): error CS0272: The property or indexer 'Counter.Value' cannot be used in this context because the set accessor is inaccessible
```

- ★★ **바깥에서는 `CS0272`** 로 막힌다 — 「set 접근자에 접근할 수 없어서 이 문맥에서 못 쓴다」.\
  ★ **`CS0122`(멤버가 안 보임)가 아니다.** 속성 자체는 보이고 **접근자 하나만** 안 보인다 — 진단 코드가 그 차이를 적는다.

### (7) 인터페이스의 속성 · 자동 속성 초기자

```text
===== 소스: cs13b-iface.cs =====
using System;
public interface IHasName {
    string Name  { get; }          // 인터페이스에 속성이 온다
    int    Count { get; set; }
}
public class Thing : IHasName {
    public string Name  { get; }      = "자동 속성 초기자";   // get 만 + 초기자
    public int    Count { get; set; } = 7;
}
class Program {
    static void Main() {
        IHasName t = new Thing();
        Console.WriteLine($"Name={t.Name}  Count={t.Count}");
    }
}
===== csc -out:ex.dll cs13b-iface.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
Name=자동 속성 초기자  Count=7
```

- ★ **속성은 인터페이스에 올 수 있다.** 인터페이스는 「`get_X` 라는 메서드를 가져라」라고 요구하는 것이므로 자연스럽다.
- ★★ **`{ get; }` 자동 속성에 초기자를 붙일 수 있다**(C# 6). 채울 길이 없어 보이는데,\
  **필드 초기자로 숨은 필드를 채우는 것**이라 가능하다 — 그 순서는 [12번](../12-class-fields-constructors-this-base/) (1)이 정본이다.

### (8) ★ `ref` 반환 속성 — 되는 것과 안 되는 것

```text
===== 소스: cs13b-ref.cs =====
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
===== csc -r:il.dll -out:ex.dll cs13b-ref.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
Plain=99
Slot 의 타입=System.Int32&  set 접근자=없음
--- Holder.get_Slot ---
  IL_0000: ldarg.0
  IL_0001: ldflda Holder::n
  IL_0006: ret
```

- ★★★ **`set` 접근자가 없는데 `h.Slot = 99` 가 통과했다.** `Slot` 의 타입이 **`System.Int32&`** 이고 setter 는 **없다**.\
  대입은 **속성 호출이 아니라 돌려받은 참조에 직접 쓰는 것**이라서다.
- ★★ IL 이 `ldfld` 가 아니라 **`ldflda`**(필드의 주소를 싣는다)다 — **값이 아니라 자리를 돌려준다**는 뜻이 한 줄로 보인다.
- ★ 그래서 **`ref` 반환 속성은 캡슐화를 뚫는다** — 창구 직원이 금고 열쇠를 그대로 내준 셈이다.

무엇이 안 되나.

```text
===== 소스: cs13b-referr.cs =====
class WithSet { int n; public ref int Slot { get => ref n; set { } } }
class Auto    { public ref int Slot { get; } }
class Program { static void Main() { } }
===== csc -out:ex.dll cs13b-referr.cs 2>&1 | sort (cc exit=1) =====
cs13b-referr.cs(1,60): error CS8147: Properties which return by reference cannot have set accessors
cs13b-referr.cs(2,32): error CS8145: Auto-implemented properties cannot return by reference
```

- ★★ **`CS8147` — `ref` 반환 속성에는 `set` 을 못 둔다.** 이미 자리를 줬으니 setter 가 할 일이 없다.
- ★★ **`CS8145` — 자동 구현 속성은 `ref` 로 못 돌려준다.** 몸통을 직접 써서 `ref` 를 만들어 줘야 한다.

### (9) ★ `field` 키워드(C# 14) — 이 판에서 되나

★★★ **없다고 적기 전에 던진다**(규칙 26). 이 판은 `-langversion:latest` 다.

```text
===== 소스: cs13b-field.cs =====
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
===== csc -r:il.dll -out:ex.dll cs13b-field.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
Celsius=-273
필드 <Celsius>k__BackingField : Int32
--- Temp.get_Celsius ---
  IL_0000: ldarg.0
  IL_0001: ldfld Temp::<Celsius>k__BackingField
  IL_0006: ret
```

- ★★★ **된다.** `-langversion:latest` 에서 컴파일도 실행도 통과했고, **숨은 필드 `<Celsius>k__BackingField` 가 생겼다.**
- ★★ **몸통이 있는데도 자동 구현 속성과 같은 이름의 필드가 생겼다** — 이것이 `field` 의 전부다.\
  전에는 `private int _celsius;` 를 손으로 쓰고 이름을 지어야 했던 자리가 사라진다.
- ★ `get => field;` 의 IL 은 (1)의 `get_Auto` 와 **한 글자도 같다.**

그런데 **이미 `field` 라는 이름의 필드가 있으면.**

```text
===== 소스: cs13b-fieldclash.cs =====
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
===== csc -out:ex.dll cs13b-fieldclash.cs 2>&1 | sort (cc exit=0 · run exit=0) =====
cs13b-fieldclash.cs(4,17): warning CS0414: The field 'Clash.field' is assigned but its value is never used
cs13b-fieldclash.cs(5,32): warning CS9258: In language version 14.0, the 'field' keyword binds to a synthesized backing field for the property. To avoid generating a synthesized backing field, and to refer to the existing member, use 'this.field' or '@field' instead.
cs13b-fieldclash.cs(5,46): warning CS9258: In language version 14.0, the 'field' keyword binds to a synthesized backing field for the property. To avoid generating a synthesized backing field, and to refer to the existing member, use 'this.field' or '@field' instead.
cs13b-fieldclash.cs(6,26): warning CS9258: In language version 14.0, the 'field' keyword binds to a synthesized backing field for the property. To avoid generating a synthesized backing field, and to refer to the existing member, use 'this.field' or '@field' instead.
P=7  Direct=0
필드 field
필드 <P>k__BackingField
필드 <Direct>k__BackingField
```

- ★★★ **`Direct=0` 이다.** `public int Direct => field;` 가 **내가 선언한 `private int field = 100` 이 아니라**\
  **컴파일러가 새로 만든 `<Direct>k__BackingField`** 를 읽었다. 값이 `100` 이 아니라 `0` 인 것이 그 증거다.
- ★★★ **필드가 셋 생겼다** — `field`(내가 쓴 것) · `<P>k__BackingField` · `<Direct>k__BackingField`.
- ★★ **경고 `CS9258` 이 세 자리에서 났다** — 「`this.field` 나 `@field` 를 쓰라」고 알려 준다.\
  ★ **에러가 아니라 경고다.** 경고를 끄고 지나가면 **값이 조용히 0 이 된다** — 이 주제에서 가장 나쁜 자리다.
- ★ **`field` 는 문맥 키워드다** — 속성 접근자 몸통 안에서만 키워드이고, 그 밖에서는 평범한 이름이다.

```text
   class Clash {
       private int field = 100;          ← ① 내가 선언한 필드
       public int P      { get => field; … }   ← field 는 ②를 가리킨다
       public int Direct => field;             ← field 는 ③을 가리킨다
   }

   실제로 만들어진 필드 셋
   ┌──────────────────────┬─────────┐
   │ ① field              │  100    │  ← 아무도 안 읽는다  (CS0414)
   │ ② <P>k__BackingField │   7     │  ← P 가 쓴다
   │ ③ <Direct>k__BackingField │ 0  │  ← ★ Direct 가 읽는다. 채운 적이 없다
   └──────────────────────┴─────────┘
                                          경고 CS9258 ×3 — 에러가 아니다
```

> **어느 층인가** — ★★ **「`field` 가 문맥 키워드이고 속성 몸통에서 숨은 필드를 가리킨다」는 C# 14 명세**다.\
> ★★★ **「이 판에서 `-langversion:latest` 로 돌아간다」는 이 판의 관찰**이다 — SDK 10.0.401 · Roslyn.\
> ★ **`CS9258` 이라는 코드와 그 문구**는 Roslyn 의 것이다.

### (10) ★★ 컴파일러가 무엇을 안 보나 — 탐침 일곱

```text
===== 소스: cs13b-probe.cs =====
using System;

// 탐침 1 — 이미 field 라는 멤버가 있는데 속성 몸통에서 field 를 쓴다
class W1 { int field = 1; public int P => field; }

// 탐침 2 — 계산 속성이 자기 자신을 부른다
class W2 { public int P => P; }

// 탐침 3 — set 접근자가 자기 속성에 대입한다
class W3 { public int P { get => 0; set { P = value; } } }

// 탐침 4 — init 만 있는 속성을 아무도 채우지 않는다
class W4 { public string Name { get; init; } }

// 탐침 5 — 쓰이지 않는 private 필드
class W5 { int unused; public int N => 1; }

// 탐침 6 — 대소문자만 다른 필드와 속성이 나란히 있다
class W6 { int value = 1; public int Value => 2; }

// 탐침 7 — get 만 있는 자동 속성을 생성자가 안 채운다
class W7 { public int N { get; } }

class Program { static void Main() { } }
===== csc -warn:9 -out:ex.dll cs13b-probe.cs 2>&1 | sort (cc exit=0) =====
cs13b-probe.cs(16,16): warning CS0169: The field 'W5.unused' is never used
cs13b-probe.cs(19,16): warning CS0414: The field 'W6.value' is assigned but its value is never used
cs13b-probe.cs(4,16): warning CS0414: The field 'W1.field' is assigned but its value is never used
cs13b-probe.cs(4,43): warning CS9258: In language version 14.0, the 'field' keyword binds to a synthesized backing field for the property. To avoid generating a synthesized backing field, and to refer to the existing member, use 'this.field' or '@field' instead.
===== csc -warn:9 -out:ex.dll cs13b-probe.cs 2>&1 | grep -o 'cs13b-probe.cs([0-9]*' | sort -u | wc -l    # 진단이 붙은 탐침은 몇 줄인가 (exit=0) =====
3
```

- ★★★ **탐침 일곱 중 진단이 붙은 줄은 셋**이다. 스크립트가 직접 세어 마지막 줄에 찍었다(`3`).
- ★★★ **답한 것** — `field` 이름 충돌(`CS9258`) · 안 쓰는 private 필드 둘(`CS0169`·`CS0414`).
- ★★★ **침묵한 것 넷이 이 절의 결론이다.**

| 탐침 | 무엇을 심었나 | 답했나 |
|---|---|---|
| 1 | `field` 라는 멤버가 있는데 속성 몸통에서 `field` 를 씀 | ★★ **답함** — `CS9258` + `CS0414` |
| 2 | ★★★ **계산 속성이 자기 자신을 부름**(`public int P => P;`) | ★★★ **침묵** |
| 3 | ★★ **set 접근자가 자기 속성에 대입**(`set { P = value; }`) | ★★★ **침묵** |
| 4 | `init` 만 있는 속성을 아무도 안 채움 | **침묵** |
| 5 | 쓰이지 않는 private 필드 | **답함** — `CS0169` |
| 6 | 대소문자만 다른 필드와 속성이 나란히 | **답함** — `CS0414`(필드가 안 쓰임) |
| 7 | `get` 만 있는 자동 속성을 생성자가 안 채움 | **침묵** |

- ★★★ **탐침 2 와 3 이 이 주제의 급소다.** 둘 다 **무한 재귀**인데 컴파일러가 한 마디도 안 한다.
- ★★ **탐침 7 도 눈여겨보라** — `public int N { get; }` 을 아무도 안 채우면 **`N` 은 영원히 0** 인데 경고가 없다.\
  ★ 필드였다면 `CS0649`(「값이 대입된 적 없다」)가 났다 — [12번](../12-class-fields-constructors-this-base/)이 그것을 실측했다.\
  ★★★ **속성으로 감싸는 순간 그 경고가 사라진다** — 컴파일러가 보는 것은 **숨은 필드가 아니라 접근자**이기 때문이다.

탐침 2 를 실제로 돌리면.

```text
===== 소스: cs13b-loop.cs =====
using System;
class Loop { public int P => P; }
class Program {
    static void Main() {
        Console.Error.WriteLine("부르기 직전");
        Console.Error.WriteLine(new Loop().P);
    }
}
===== csc -out:ex.dll cs13b-loop.cs && dotnet ex.dll 2>&1 | sed -n "1,2p" (cc exit=0 · run exit=134) =====
부르기 직전
Stack overflow.
```

- ★★★ **`cc exit=0`** — 컴파일은 **깨끗하게** 통과했다. **`run exit=134`**(SIGABRT)로 죽는다.
- ★★ **구분 마커를 표준 오류로 찍었다**(규칙 18) — `Console.Error` 로 「부르기 직전」을 먼저 내보내야\
  스택 오버플로 메시지와 **순서가 고정**된다.
- ★ 잘린 꼬리는 배너에 `| sed -n "1,2p"` 로 적혀 있다 — 스택 오버플로 리포트는 프레임 수백 줄이라 대조가 안 된다.

## 문법 — 형태와 규칙

### 형태

```csharp
// cs13b-form.cs
using System;

var s = new Shape { Name = "사각형", Once = 3 };
s.Auto = 4;
s.Guard = -9;
s.Slot = 12;
Console.WriteLine($"{s.Name} {s.Auto} {s.Once} {s.Only} {s.Seed} {s.Twice} {s.Guard} {s.Count} {s.Slot}");

class Shape {
    public int  Auto  { get; set; }               // 자동 구현
    public int  Once  { get; init; }              // init 접근자 (C# 9)
    public int  Only  { get; } = 1;               // getter-only (C# 6) + 자동 속성 초기자
    public int  Seed  { get; set; } = 7;          // 자동 속성 초기자 (C# 6)
    public int  Twice => Auto * 2;                // 계산 속성 — 식 본문
    public int  Guard { get => field;             // field 키워드 (C# 14)
                        set => field = value < 0 ? 0 : value; }
    public int  Count { get; private set; }       // 접근자 접근성
    public required string Name { get; init; }    // required (C# 11)
    int n;
    public ref int Slot => ref n;                 // ref 반환 속성 (C# 7)
}
```

```text
===== 소스: cs13b-form.cs =====
using System;

var s = new Shape { Name = "사각형", Once = 3 };
s.Auto = 4;
s.Guard = -9;
s.Slot = 12;
Console.WriteLine($"{s.Name} {s.Auto} {s.Once} {s.Only} {s.Seed} {s.Twice} {s.Guard} {s.Count} {s.Slot}");

class Shape {
    public int  Auto  { get; set; }               // 자동 구현
    public int  Once  { get; init; }              // init 접근자 (C# 9)
    public int  Only  { get; } = 1;               // getter-only (C# 6) + 자동 속성 초기자
    public int  Seed  { get; set; } = 7;          // 자동 속성 초기자 (C# 6)
    public int  Twice => Auto * 2;                // 계산 속성 — 식 본문
    public int  Guard { get => field;             // field 키워드 (C# 14)
                        set => field = value < 0 ? 0 : value; }
    public int  Count { get; private set; }       // 접근자 접근성
    public required string Name { get; init; }    // required (C# 11)
    int n;
    public ref int Slot => ref n;                 // ref 반환 속성 (C# 7)
}
===== csc -out:ex.dll cs13b-form.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
사각형 4 3 1 7 8 0 0 12
```

- **접근자 이름은 `get`·`set`·`init` 셋뿐이다.** `get` 과 `set`/`init` 은 함께 올 수 있지만 **`set` 과 `init` 은 같이 못 온다.**
- **`init` 은 `set` 자리에 오는 것**이지 별개 접근자가 아니다.
- **`required` 는 속성에도 필드에도 붙는다.** 붙이면 **생성 지점마다** 검사한다((4)).
- **자동 구현 속성에는 몸통이 없다** — 그래서 `ref` 반환이 안 된다((8)).
- ★★ 출력의 마지막 세 칸을 읽어라 — **`Guard=0`**(음수를 `set` 몸통이 잘랐다) · **`Count=0`**(private setter 라 바깥이 못 채웠다) · **`Slot=12`**(setter 없이 대입됐다).

### 금지 사례 — 진단이 나는 꼴

아래는 **위 (1)\~(8)에서 실제로 던져 얻은 진단 코드**를 한 자리에 모은 것이다.
코드가 어느 절의 어느 블록에서 나왔는지 함께 적는다 — **문구는 판에 매이므로 코드로만 읽는다.**

| 쓴 꼴 | 진단 코드 | 어디서 |
|---|---|---|
| `public int A { public get; set; }` | `CS0273` | (6) — 접근자는 속성보다 좁아야 한다 |
| `public int C { protected get; private set; }` | `CS0274` | (6) — 두 접근자 모두에는 못 붙인다 |
| 다 만든 객체에 `p.X = 3`(X 는 `init`) | `CS8852` | (3) — 허용 자리는 셋뿐 |
| `new User { Age = 3 }`(Name 이 `required`) | `CS9035` | (4) — 생성 지점마다 |
| `required` 인데 `private init` | `CS9032` | (4) — 채울 길을 막으면 모순 |
| 바깥에서 `c.Value = 10`(set 이 private) | `CS0272` | (6) — `CS0122` 가 아니다 |
| 객체 초기자로 `readonly` 필드 대입 | `CS0191` | (5) |
| `public ref int S { get => ref n; set { } }` | `CS8147` | (8) |
| `public ref int T { get; }` | `CS8145` | (8) |
| `field` 라는 멤버가 있는데 몸통에서 `field` | `CS9258`(경고) | (9) — ★ **에러가 아니다** |

## 어디서 틀리나

1. ★★★ **「속성은 필드에 껍데기를 씌운 것」** — 계산 속성에는 **필드가 아예 없다**((1)).
2. ★★★ **「`init` 이면 런타임이 지켜 준다」** — **컴파일러만 지킨다**((2)). 리플렉션은 그냥 통과한다.
3. ★★★ **「`required` 면 객체가 항상 채워져 있다」** — [12번](../12-class-fields-constructors-this-base/)이 `GetUninitializedObject` 로 뚫었다.\
   ★ 여기서는 **`[SetsRequiredMembers]` 가 검사가 아니라 면제 선언**인 것을 봤다((4)).
4. ★★★ **`field` 이름 충돌** — 이미 `field` 라는 필드가 있으면 **속성 몸통의 `field` 는 그것이 아니다**((9)).\
   **경고일 뿐이라 값이 조용히 0 이 된다.**
5. ★★ **「속성이 자기를 부르면 컴파일러가 잡아 준다」** — **안 잡는다**((10)). `run exit=134` 로 죽는다.
6. ★★ **「`get` 만 있는 자동 속성을 안 채우면 경고가 난다」** — **안 난다**((10) 탐침 7).\
   필드였으면 `CS0649` 가 났을 자리다.
7. ★★ **「`readonly` 필드와 `init` 속성은 같은 것」** — **바깥이 채울 수 있느냐**가 갈린다((5)).
8. ★ **「접근자 접근성은 아무렇게나 줄 수 있다」** — **더 좁게, 한쪽에만**이다((6)).
9. ★ **「`ref` 반환 속성에 `set` 을 달면 편하다」** — `CS8147` 로 막힌다((8)). 자리를 줬으면 setter 는 할 일이 없다.

## 구현 세부사항 대 언어 보장

| 무엇 | 층 | 근거 |
|---|---|---|
| **속성이 접근자 메서드로 컴파일된다** | ★★★ **언어 보장** | ECMA-334 §15.7 — 접근자는 함수 멤버다 |
| **계산 속성에 저장소가 없다** | ★★★ **언어 보장** | 몸통이 있으면 컴파일러가 필드를 만들 이유가 없다 |
| **`init` 이 세 자리에서만 대입 가능하다** | ★★★ **언어 보장** | `CS8852` 문구가 그 목록이다((3)) |
| **`required` 를 컴파일러가 검사한다** | ★★★ **언어 보장** | `CS9035`((4)) |
| **런타임이 `init`·`required` 를 강제하지 않는다** | ★★ **설계이자 관찰** | (2)의 리플렉션 · [12번](../12-class-fields-constructors-this-base/)의 `GetUninitializedObject` |
| **메서드 이름이 `get_X`/`set_X` 다** | ★★ **구현(Roslyn)** | (1) |
| **숨은 필드 이름이 `<X>k__BackingField` 다** | ★★ **구현(Roslyn)** | (1)(9) |
| **표식이 `modreq(IsExternalInit)` 다** | ★★★ **구현(Roslyn+BCL)** | (2) — 다른 표식이어도 명세는 안 깨진다 |
| **`-warn:9` 에서 탐침 일곱 중 셋만 답한다** | ★ **이 판의 관찰** | (10) — 다음 판에서 늘 수 있다 |
| **진단 문구 전부** | ★ **이 판의 관찰** | 판마다 다듬인다. 근거로는 **코드와 `(행,열)`** 만 쓴다 |

## 언제 쓰고 언제 안 쓰나

- **속성을 쓴다** — 공개하는 데이터 전부. C# 에서 **공개 필드는 관례상 쓰지 않는다**(데이터 바인딩·인터페이스·나중의 검증이 전부 속성을 요구한다).
- **계산 속성을 쓴다** — 값이 **싸고 부작용이 없을 때.** 비싸면 **메서드로** 두어 호출자가 비용을 보게 한다.\
  ★ 판단 기준은 [14번](../14-indexers/) (10)의 「인덱서 대신 메서드」와 같다.
- **`init` 을 쓴다** — 만들고 나면 안 바뀌는 설정 객체. **`record` 의 위치 매개변수도 `init` 속성이 된다**(목록의 **18번 주제**).
- **`required` 를 쓴다** — 생성자 오버로드를 잔뜩 만들기 싫은데 **빠뜨리면 안 되는** 속성이 있을 때.
- **`field` 를 쓴다** — 검증이나 지연 계산 때문에 몸통이 필요한데 **필드 이름을 지을 이유가 없을 때.**
- **안 쓴다** — ★ **`ref` 반환 속성**은 캡슐화를 뚫으므로 성능이 걸린 자리에서만((8)).\
  ★ **`private` 전용 데이터**는 그냥 필드로 둔다 — 속성으로 감싸면 (10) 탐침 7 처럼 **경고까지 잃는다.**

## 핵심 문장

1. ★★★ **속성은 메서드 한 쌍이다.** `get_X`/`set_X` 가 진짜로 존재하고 IL 이 그것을 `call` 한다((1)).
2. ★★★ **계산 속성에는 필드가 없다.** 「속성 = 필드 + 껍데기」는 틀린 그림이다((1)).
3. ★★★ **`init` 은 `modreq(IsExternalInit)` 라는 쪽지다** — 컴파일러가 읽고 런타임은 안 읽는다((2)).
4. ★★ `required` 는 「**채웠음의 증명**」이 아니라 「**생성 지점의 검사**」다. `[SetsRequiredMembers]` 는 **면제 선언**이다((4)).
5. ★★ **컴파일러는 속성의 「형태」만 본다.** 자기 자신을 부르는 속성도, 영영 0 인 getter-only 속성도 통과시킨다((10)).

## 관련 자료

- [12번 — 클래스·필드·생성자·`this`/`base`](../12-class-fields-constructors-this-base/) — **그쪽은 「객체가 만들어질 때 무엇이 도나」까지, 여기는 「그 필드를 어떻게 감싸나」부터.**\
  ★ **초기화 순서·`required` 의 런타임 구멍·`readonly` 의 얕은 불변**은 **전부 그쪽이 정본**이고 여기서는 인용만 했다.
- [14번 — 인덱서](../14-indexers/) — **같은 사슬이다.** 인덱서는 **인자를 받는 속성**이고 `get_Item`/`set_Item` 으로 컴파일된다.
- [15번 — 접근 한정자와 어셈블리 경계](../15-access-modifiers-and-assembly-boundary/) — **접근자 접근성**((6))은 여기까지, **여섯 한정자의 전수**는 그쪽.
- [03번 — 박싱과 언박싱](../03-boxing-and-unboxing/) — 이 문서가 쓰는 **IL 디스어셈블러를 만든 곳**이다.
- [`oop-basics/`](../../../../oop-basics/) — **캡슐화·정보 은닉 개념**은 거기, 여기는 **C# 문법**.
- 목록의 **18번 주제**(`record`) — `record` 의 위치 매개변수는 `init` 속성이 된다.
- 파이썬 갈래 목록([`python/syntax/README.md`](../../../python/syntax/README.md))의 **33번** — `property`·디스크립터. **라이브러리 객체 대 언어 문법**의 대비.

## 용어 풀이

- **속성(property)** — 필드처럼 읽고 쓰지만 실제로는 접근자 메서드가 도는 멤버. **어트리뷰트와 다른 말이다.**
- **접근자(accessor)** — `get`·`set`·`init`. 각각 `get_X`·`set_X` 메서드가 된다.
- **자동 구현 속성(auto-implemented property)** — 몸통 없이 `{ get; set; }` 만 쓴 속성. 숨은 필드가 생긴다.
- **숨은 필드(backing field)** — 자동 구현 속성이 값을 두는 자리. 이 판에서는 `<X>k__BackingField`.
- **계산 속성(computed property)** — 몸통에서 값을 만들어 돌려주는 속성. 저장소가 없다.
- **`modreq`(required custom modifier)** — 메서드 시그니처에 붙는 표식. **모르는 컴파일러는 그 멤버를 못 쓴다.**
- **`IsExternalInit`** — `init` 접근자를 표시하는 **빈 클래스**. 값이 아니라 **이름이 전부**인 타입이다.
- **문맥 키워드(contextual keyword)** — 특정 문맥에서만 키워드인 낱말. `field` 가 그렇다(C# 14).
- **`IsSpecialName`** — 「사람이 직접 부르는 이름이 아니다」라는 메타데이터 플래그.

## 더 들어가면

- ★ **`init` 이 왜 `modreq` 인가** — `modopt`(선택 표식)였다면 **`init` 을 모르는 옛 컴파일러가 그냥 setter 로 부를 수 있다.**\
  `modreq` 라야 「모르면 쓰지 마라」가 강제된다. 표식 하나의 선택이 **하위 호환의 방향을 정한 자리**다.
- ★ **`IsExternalInit` 이 BCL 에 없던 시절** — .NET 5 이전 타겟에서는 **그 빈 클래스를 사용자가 직접 선언**해야 `init` 이 컴파일됐다.\
  **타입의 이름만 맞으면 됐다** — `modreq` 가 이름으로 맞춰지기 때문이다. **안 돌려 봤다**(이 판은 net10.0 뿐이다).
- ★ **속성과 JIT 인라인** — 접근자가 `ldfld` 한 줄이면 JIT 이 인라인해 필드 접근과 같아지는 것이 통설이지만,\
  ★★★ **이 판에서 안 쟀다.** 재려면 인라인 여부를 직접 관찰하는 하네스가 필요하다 — **「안 돌려 본 것」으로 남긴다.**
