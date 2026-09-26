# csharp/syntax/13 — 속성(property)과 `init`·`required`·`field` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·진단·IL 은 **.NET SDK 10.0.401** · 런타임 **10.0.12** · 타겟 **`net10.0`** ·
> **linux-x64** 에서 실제로 돌려 얻은 것이다(2026-09-26).\
> 진단은 **`-preferreduilang:en-US`** 로 영어로 고정했다.\
> ★ 블록은 캡처 스크립트가 파일로 받아 조립기가 끼워 넣은 것이다 — 손으로 옮긴 줄은 없다.
> **읽는 법** — **진단 문구**와 **숨은 필드 이름의 형식**은 흔들리는 칸이다.\
> 근거로 쓰는 것은 **옵코드 이름과 순서 · 진단 코드와 `(행,열)` · `modreq` 목록 ·
> 숨은 필드가 있다는 사실과 개수 · `cc exit`/`run exit`** 다.\
> ★ 진단이 둘 이상인 블록은 배너에 **`| sort`** 가 적혀 있다 — Roslyn 이 내는 순서가 판마다 갈리기 때문이다.
> ★★★ **이 문서는 시간을 재지 않았다.** 「속성이 필드보다 느리다」 같은 문장이 **한 줄도 없다.**

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ **메서드 다섯 · 필드 둘**이다 — 계산 속성에는 저장소가 없다

**출력**

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

**왜 그런가**

- ★★★ **속성 셋에 메서드 다섯**이다. `Auto` 가 둘(`get`/`set`), `Once` 가 둘(`get`/`init`), `Twice` 가 하나(`get` 만).\
  전부 **`IsSpecialName=True`** — 「사람이 이 이름으로 직접 부르라고 만든 게 아니다」라는 표시다.
- ★★★ **필드는 둘뿐이다.** `<Auto>k__BackingField` 와 `<Once>k__BackingField`.\
  **`Twice` 것이 없다** — 계산 속성은 **값을 두는 자리를 안 만든다.**\
  「속성은 필드에 껍데기를 씌운 것」이라는 흔한 그림이 여기서 깨진다.
- ★★★ **`get_Twice` 의 둘째 줄이 `call Box::get_Auto` 다.** 소스에 `Auto * 2` 라고 적은 것이\
  **필드 읽기가 아니라 메서드 호출**로 번역됐다 — 속성을 속성 안에서 쓰면 **호출이 쌓인다.**
- ★★ 자동 구현 접근자의 본문은 **`ldfld`·`stfld` 한 줄이 전부**다. 그 밖에 아무것도 없다.
- ★ **`set_Once` 의 `반환 modreq=[IsExternalInit]`** 하나만 다르다 — 2번이 그것을 판다.

> **어느 층인가** — ★★★ **속성이 접근자 메서드로 컴파일되는 것은 명세**다(ECMA-334 §15.7).\
> ★★ **이름이 `get_X` 이고 숨은 필드가 `<X>k__BackingField` 인 것은 Roslyn 의 선택**이다.

### 2. ★★★ **통한다** — `init` 을 막는 것은 컴파일러뿐이다

**출력**

먼저 IL 본문을 `set` 과 나란히 놓는다.

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

그 다음 시그니처를 리플렉션으로 읽는다.

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

**왜 그런가**

- ★★★ **IL 본문이 한 글자도 같다.** `set_Name`(init) 과 `set_Loose`(set) 둘 다\
  `ldarg.0 / ldarg.1 / stfld / ret` 네 줄이다. **본문 덤프만 보면 `init` 은 아무것도 아니다.**
- ★★★ **갈리는 곳은 시그니처다** — `반환 modreq : System.Runtime.CompilerServices.IsExternalInit`.\
  `modreq`(required custom modifier)는 **읽는 쪽이 모르면 그 멤버를 못 쓰게** 만드는 표식이고,\
  C# 컴파일러는 이것을 보고 「객체 초기자·생성자·`init` 접근자 밖에서는 거절」한다.
- ★★★ **`setter.Invoke` 는 그냥 통과했다.** 다 만들어진 객체의 `init` 속성이 나중에 바뀌었다 —\
  **런타임은 `modreq` 를 검사하지 않는다.** 그것은 **컴파일러에게 보내는 쪽지**다.
- ★★ **[12번](../12-class-fields-constructors-this-base/)의 `required` 실측과 같은 집안이다.**\
  거기서는 `GetUninitializedObject` 가 `required` 를 그냥 지나갔고 `RequiredMemberAttribute` 는 박혀 있었다.\
  **표식은 남고 강제는 컴파일 시점뿐**이라는 점이 똑같다.
- ★ **그래서 신뢰 경계를 넘는 입력에는 `init` 도 `required` 도 방어가 아니다.** 방어는 생성자 안의 검사다.

```text
   set_Name 의 시그니처

   void modreq(IsExternalInit) set_Name(string value)
        └────────┬──────────┘
                 │
     ┌───────────┴────────────┐
     │                        │
   C# 컴파일러가 읽는다      CLR 은 안 읽는다
     │                        │
   객체 초기자·생성자·       MethodInfo.Invoke ──> 그냥 부른다
   init 접근자 밖이면 CS8852      「리플렉션이 나중에 밀어 넣음」

   ★★★ 표식은 메타데이터에 남고, 강제는 컴파일 시점에만 있다.
```

> ★★ **창을 바꿔야 보이는 자리**다(규칙 18-B 의 제5의 상태와 같은 꼴) — ① IL 덤프로는 아무것도 안 보이고\
> ③ 리플렉션으로 물어야 답이 나온다. **그래서 이 주제는 창을 둘 쓴다.**

### 3. ★★ **셋뿐이다** — 객체 초기자 · 생성자의 `this`/`base` · `init` 접근자

**출력**

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

**왜 그런가**

- ★★★ **진단 문구가 허용 목록을 그대로 읊는다** — 「an object initializer, or on `this` or `base` in an instance constructor, or an `init` accessor」.
- ★★ **에러는 두 건**이고 둘 다 **`CS8852`** 다. 붙은 자리는 `(12,9)` 의 `p.X = 3` 과 `(6,28)` 의 `Rename()` 안이다.
- ★★★ **`var q = p with { X = 2 };` 는 에러가 안 났다.** `with` 식은 **컴파일러가 만든 복사 생성자 안에서** 대입하므로\
  「인스턴스 생성자의 `this`」에 해당한다. **허용 목록에 `with` 가 따로 안 적혀 있는 이유**가 그것이다.
- ★★ **`Cfg()` 생성자 안의 대입도 통과**했다(5행에 에러가 없다). 반면 **평범한 메서드 `Rename()` 은 막혔다** —\
  **「내 클래스인가」가 아니라 「생성 중인가」가 기준**이다.

### 4. ★★ **모른다** — 생성자로 채워도 `CS9035` 가 난다

**출력**

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

```text
===== 소스: cs13b-reqvis.cs =====
class W { public required int N { get; private init; } }
class Program { static void Main() { } }
===== csc -out:ex.dll cs13b-reqvis.cs (cc exit=1) =====
cs13b-reqvis.cs(1,31): error CS9032: Required member 'W.N' cannot be less visible or have a setter less visible than the containing type 'W'.
```

**왜 그런가**

- ★★★ **진단이 「속성마다」가 아니라 「생성 지점마다」 붙는다.** `new User { Age = 3 }` 과 `new User()` 각각 한 건씩이고,\
  제대로 채운 `new User { Name = "가" }` 은 조용하다.
- ★★★ **생성자 안에서 `Name = n` 을 해도 컴파일러는 모른다** — `Plain` 쪽이 `CS9035` 로 막혔다.\
  **컴파일러는 생성자 본문을 분석해 「채웠는지」를 판정하지 않는다.**
- ★★★ **`[SetsRequiredMembers]` 는 검사가 아니라 면제 선언이다.** `Marked` 만 통과했고,\
  **그 어트리뷰트가 정말 채우는지 컴파일러는 확인하지 않는다** — 빈 생성자에 붙여도 통과한다.\
  ★ 그래서 `required` 는 「**채웠음을 증명하라**」가 아니라 「**채웠다고 말하라**」다.
- ★★ **`CS9032`** — `required` 인데 setter 가 타입보다 좁으면 막힌다.\
  바깥에서 채우라고 강제해 놓고 채울 길을 막으면 모순이라서다.
- ★★ **런타임은 강제하지 않는다** — [12번](../12-class-fields-constructors-this-base/) (7)이 `RuntimeHelpers.GetUninitializedObject` 로\
  `required` 를 통째로 건너뛴 것을 실측했다(`Host=null`·`Port=0`). **여기서 다시 재지 않았다 — 그쪽이 정본이다.**

### 5. ★ **`init` 은 바깥이 한 번 채울 수 있고 `readonly` 는 아예 못 채운다**

**출력**

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

**왜 그런가**

- ★★★ **에러 두 건이 전부 `F`(readonly 필드)에 붙었다** — `(10,25)` 의 `new R { F = 9 }` 와 `(5,23)` 의 메서드 안 대입.\
  **`new R { P = 9 }`(init 속성)는 조용하다.**
- ★★★ **진단 문구가 허용 목록을 읊는다** — 「선언한 타입의 **생성자** · **`init`-only setter** · **변수 초기자**」.
- ★★ **객체 초기자가 그 목록에 안 드는 이유** — 객체 초기자는 **호출한 쪽에 있는 코드**다.\
  `new R { F = 9 }` 는 `R` 밖에서 `F` 에 대입하는 것이라 「선언한 타입의 생성자」가 아니다.\
  ★ 반면 `init` 속성은 **setter 가 `R` 안에 있으므로** 바깥이 불러도 된다.
- ★ 정리하면 — **`init` 속성 = 「바깥이 한 번은 채울 수 있는 불변」**, **`readonly` 필드 = 「바깥은 아예 못 채우는 불변」**.
- ★★ **둘 다 「참조만 고정한다」는 점은 같다** — [12번](../12-class-fields-constructors-this-base/)이 `readonly int[]` 의 원소가 바뀌는 것을 실측했다.

### 6. ★★★ **된다** — 그리고 이름이 겹치면 `Direct` 가 **0** 이 된다

**출력**

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

**왜 그런가**

- ★★★ **`field` 키워드가 이 판에서 돈다.** `-langversion:latest` 에서 `cc exit=0 · run exit=0` 이고,\
  숨은 필드 **`<Celsius>k__BackingField`** 가 생겼다. `t.Celsius` 는 **`-273`**(`set` 몸통의 하한이 먹었다).
- ★★ **몸통이 있는데도 자동 구현 속성과 같은 숨은 필드가 생기는 것**이 `field` 의 전부다.\
  전에는 `private int _celsius;` 를 손으로 쓰고 **이름을 지어야** 했던 자리가 사라진다.\
  ★ `get => field;` 의 IL 은 1번의 `get_Auto` 와 **한 글자도 같다.**
- ★★★ **이름이 겹치면 `Direct=0` 이다.** `public int Direct => field;` 가 **내가 선언한 `private int field = 100` 이 아니라**\
  **컴파일러가 새로 만든 `<Direct>k__BackingField`** 를 읽었다. 값이 100 이 아니라 0 인 것이 그 증거다.
- ★★★ **필드가 셋 찍혔다** — `field`(내가 쓴 것) · `<P>k__BackingField` · `<Direct>k__BackingField`.\
  하나의 이름이 **두 가지 것**을 가리키게 된 셈이다.
- ★★ **에러가 아니라 경고 `CS9258` 이 세 자리에서 났다.** 「`this.field` 나 `@field` 를 쓰라」고 알려 준다.\
  ★★★ **경고를 끄고 지나가면 값이 조용히 0 이 된다** — 이 주제에서 가장 나쁜 자리다.\
  ★ `CS0414`(「`Clash.field` 는 대입만 되고 안 쓰인다」)가 **같이 나오는 것**이 두 번째 신호다.
- ★ **`field` 는 문맥 키워드다** — 속성 접근자 몸통 안에서만 키워드이고 그 밖에서는 평범한 이름이다.

### 7. ★ **`set` 없이 대입이 된다** — 값이 아니라 자리를 돌려주기 때문

**출력**

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

```text
===== 소스: cs13b-referr.cs =====
class WithSet { int n; public ref int Slot { get => ref n; set { } } }
class Auto    { public ref int Slot { get; } }
class Program { static void Main() { } }
===== csc -out:ex.dll cs13b-referr.cs 2>&1 | sort (cc exit=1) =====
cs13b-referr.cs(1,60): error CS8147: Properties which return by reference cannot have set accessors
cs13b-referr.cs(2,32): error CS8145: Auto-implemented properties cannot return by reference
```

**왜 그런가**

- ★★★ **`h.Slot = 99` 가 통과했고 `Plain` 이 99 를 읽는다.** 그런데 **`set 접근자=없음`** 이다.\
  대입이 **속성 호출이 아니라 돌려받은 참조에 직접 쓰는 것**이라서다.
- ★★ **`Slot` 의 타입이 `System.Int32&`** 로 찍힌다 — `&` 가 참조 타입임을 적는다.
- ★★ **IL 이 `ldfld` 가 아니라 `ldflda` 다**(필드의 주소를 싣는다). **값이 아니라 자리를 돌려준다**는 뜻이 한 줄로 보인다.
- ★ 그래서 **`ref` 반환 속성은 캡슐화를 뚫는다** — 창구 직원이 금고 열쇠를 그대로 내준 셈이다.\
  성능이 걸린 자리(큰 구조체 배열 등)가 아니면 쓸 이유가 없다.
- ★★ 안 되는 것 둘 — **`CS8147`**(`ref` 반환에 `set` 을 못 둔다. 자리를 줬으니 setter 가 할 일이 없다) ·\
  **`CS8145`**(자동 구현 속성은 `ref` 로 못 돌려준다. 몸통을 직접 써야 한다).

### 8. ★ **더 좁게 · 한쪽에만** — 두 규칙이 진단 둘로 나온다

**출력**

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

**왜 그런가**

- ★★★ **`CS0273` — 접근자 한정자는 속성보다 「더 제한적」이어야 한다.**\
  `public int A { public get; set; }` 은 **같은 높이**라 거절된다. 넓히는 것은 물론 안 된다.
- ★★★ **`CS0274` — 두 접근자 모두에는 못 붙인다.** 둘 다 좁히면 **속성 자체의 접근성이 무슨 뜻인지** 없어지기 때문이다.
- ★ 그래서 실무에서 쓰는 꼴은 사실상 하나다 — **`public int Value { get; private set; }`**.
- ★★ **바깥에서 대입하면 `CS0272` 이지 `CS0122` 가 아니다.**\
  `CS0122` 는 「멤버 자체가 안 보인다」이고 `CS0272` 는 「**속성은 보이는데 set 접근자만** 안 보인다」다.\
  ★ **진단 코드가 그 차이를 적는다** — 읽을 때 둘을 섞지 마라.

```text
   속성의 접근성          접근자에 붙일 수 있는 것
   ───────────────────────────────────────────────────
   public          ──>   protected · internal · private   ○ (더 좁다)
   public          ──>   public                            ✕ CS0273 (같은 높이)
   private         ──>   private                           ✕ CS0273 (같은 높이)
   아무거나         ──>   get 과 set 둘 다                   ✕ CS0274

   ★ 남는 꼴은 사실상 하나 —  public int Value { get; private set; }
     바깥에서 대입하면  CS0272  (CS0122 가 아니다 — 속성 자체는 보인다)
```

### 9. ★ **올 수 있고 · 붙일 수 있다** — 인터페이스는 메서드를 요구하는 것이기 때문

**출력**

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

**왜 그런가**

- ★ **속성은 인터페이스에 올 수 있다.** 인터페이스가 요구하는 것은 결국 **`get_Name` 이라는 메서드**이므로 자연스럽다.\
  `{ get; }` 만 요구한 `Name` 을 구현 쪽이 **getter-only 자동 속성**으로 채웠다.
- ★★ **`{ get; }` 자동 속성에도 초기자를 붙일 수 있다**(C# 6). setter 가 없어 채울 길이 없어 보이는데,\
  **초기자는 속성이 아니라 숨은 필드를 채우는 필드 초기자**라서 가능하다.
- ★ **그 초기자가 도는 시점**은 [12번](../12-class-fields-constructors-this-base/) (1)이 정본이다 —\
  **파생의 필드 초기자가 기반보다 먼저** 돈다.
- ★ `Count` 는 `{ get; set; } = 7` 이라 인터페이스의 `{ get; set; }` 요구를 그대로 채운다.

### 10. ★★★ **일곱 중 셋만 답한다** — 무한 재귀 둘이 그대로 통과한다

**출력**

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

**왜 그런가**

- ★★★ **진단이 붙은 줄은 셋**이고, 스크립트가 직접 세어 마지막 줄에 **`3`** 을 찍었다(사람이 안 셌다).

| 탐침 | 무엇을 심었나 | 답했나 |
|---|---|---|
| 1 | `field` 라는 멤버가 있는데 속성 몸통에서 `field` 를 씀 | ★★ **답함** — `CS9258` + `CS0414` |
| 2 | ★★★ **계산 속성이 자기 자신을 부름**(`public int P => P;`) | ★★★ **침묵** |
| 3 | ★★ **set 접근자가 자기 속성에 대입**(`set { P = value; }`) | ★★★ **침묵** |
| 4 | `init` 만 있는 속성을 아무도 안 채움 | **침묵** |
| 5 | 쓰이지 않는 private 필드 | **답함** — `CS0169` |
| 6 | 대소문자만 다른 필드와 속성이 나란히 | **답함** — `CS0414` |
| 7 | `get` 만 있는 자동 속성을 생성자가 안 채움 | **침묵** |

- ★★★ **탐침 2 와 3 이 급소다.** 둘 다 **무한 재귀**인데 `-warn:9` 에서 한 마디도 안 한다.\
  실제로 돌리면 **`cc exit=0` · `run exit=134`**(SIGABRT)로 죽는다.
- ★★★ **탐침 7 이 두 번째 급소다.** `public int N { get; }` 을 아무도 안 채우면 **`N` 은 영원히 0** 인데 경고가 없다.\
  ★ **필드였다면 `CS0649`**(「값이 대입된 적 없다」)가 났다 — [12번](../12-class-fields-constructors-this-base/)이 그것을 실측했다.\
  ★★★ **속성으로 감싸는 순간 그 경고가 사라진다** — 컴파일러가 보는 것은 **숨은 필드가 아니라 접근자**이기 때문이다.
- ★★ **한 줄씩으로 가르면** — 컴파일러는 **「형태」를 본다**(한정자 조합·접근성·`required` 를 채웠나·표식이 맞나).\
  ★★★ **「의미」는 안 본다**(이 속성이 자기를 부르나 · 이 값이 언젠가 채워지나).\
  [12번](../12-class-fields-constructors-this-base/)이 **탐침 여섯에 0건**으로 같은 결론을 냈다 — **이 갈래에서 두 번째 확인**이다.
- ★ **구분 마커를 표준 오류로 찍었다**(규칙 18) — `Console.Error` 라야 스택 오버플로 메시지와 순서가 고정된다.\
  잘린 꼬리는 배너에 `| sed -n "1,2p"` 로 적혀 있다(리포트가 프레임 수백 줄이라 대조가 안 된다).

### 11. 잇기

- ★★★ **초기화 순서·`required` 의 런타임 구멍·`readonly` 의 얕은 불변**은 전부 [12번](../12-class-fields-constructors-this-base/)이 정본이다.\
  여기서는 **다시 재지 않고 인용만** 했다.
- ★★★ **[14번](../14-indexers/)은 이 주제와 한 사슬이다** — 인덱서는 **인자를 받는 속성**이고,\
  `get_Item`/`set_Item` 으로 컴파일된다. 「메서드로 컴파일되는 문법」이라는 점이 같다.
- **접근 한정자 여섯의 전수**는 [15번](../15-access-modifiers-and-assembly-boundary/)이다. 여기서는 **접근자 접근성**((8))만 봤다.
- ★ 이 문서가 쓰는 **IL 디스어셈블러**는 [03번](../03-boxing-and-unboxing/)이 만들었다 — 외부 도구가 0개다.
- **`record` 의 위치 매개변수가 `init` 속성이 되는 것**은 목록의 **18번 주제**다.
- ★ **파이썬과 갈리는 층** — 파이썬의 `property` 는 **디스크립터 프로토콜 위의 라이브러리 객체**이고\
  C# 의 속성은 **언어 문법이자 메타데이터**다. 파이썬 갈래 목록([`python/syntax/README.md`](../../../python/syntax/README.md))의 **33번**이 그쪽 정본인데, **이 판에서 파이썬은 안 던졌다.**

## 실행 검증

| 무엇 | 몇 번·어디서 | 결과 |
|---|---|---|
| `cs13b-auto.cs` 속성 → 메서드 | csc 1회 | ★★★ **메서드 5 · 필드 2** · `get_Twice` 가 `call get_Auto` |
| `cs13b-initil.cs` `init` 대 `set` IL | csc 1회 | ★★★ **본문이 한 글자도 같다** |
| `cs13b-initrefl.cs` `modreq` | csc 1회 | ★★★ `IsExternalInit` · **리플렉션으로 뚫린다** |
| `cs13b-initwhere.cs` 허용 자리 | csc 1회 | **`CS8852` 2건** · `with` 는 통과 |
| `cs13b-required.cs` `required` | csc 1회 | **`CS9035` 2건** — 생성 지점마다 |
| `cs13b-reqctor.cs` `[SetsRequiredMembers]` | csc 1회 | ★★★ 표시 없는 생성자는 **`CS9035`** |
| `cs13b-reqvis.cs` 접근성 | csc 1회 | **`CS9032`** |
| `cs13b-readonly.cs` `readonly` 대 `init` | csc 1회 | **`CS0191` 2건** · `init` 쪽은 조용 |
| `cs13b-accessor.cs` 접근자 접근성 | csc 1회 | **`CS0273` 2건 · `CS0274` 1건** |
| `cs13b-privset.cs` `private set` | csc 1회 | **`CS0272`**(`CS0122` 아님) |
| `cs13b-iface.cs` 인터페이스·초기자 | csc 1회 | `Name=자동 속성 초기자  Count=7` |
| `cs13b-ref.cs` `ref` 반환 속성 | csc 1회 | ★★★ **`ldflda`** · `System.Int32&` · **setter 없음** |
| `cs13b-referr.cs` 안 되는 것 | csc 1회 | **`CS8147` · `CS8145`** |
| `cs13b-field.cs` `field` 키워드 | csc 1회 | ★★★ **된다** · `<Celsius>k__BackingField` · `-273` |
| `cs13b-fieldclash.cs` 이름 충돌 | csc 1회 | ★★★ **`Direct=0`** · 필드 3개 · **`CS9258` ×3**(경고) |
| `cs13b-probe.cs` 탐침 일곱 | csc 1회(`-warn:9`) | ★★★ **진단이 붙은 줄 3** · 무한 재귀 둘은 침묵 |
| `cs13b-loop.cs` 무한 재귀 | csc 1회 | ★★★ **`cc exit=0` · `run exit=134`** |

**구현 의존 항목** — 다음은 **이 판(.NET SDK 10.0.401 · 런타임 10.0.12 · linux-x64)에서만** 그렇다.

- ★★ **접근자 이름**(`get_X`/`set_X`)과 **숨은 필드 이름**(`<X>k__BackingField`) — Roslyn 이 정한다.
- ★★★ **`init` 의 표식이 `IsExternalInit` 이라는 것** — 다른 타입이어도 명세는 안 깨진다.
- ★★ **`-warn:9` 에서 탐침 일곱 중 셋만 답한 것** — 다음 판에서 늘 수 있다.
- ★★ **`field` 키워드가 `-langversion:latest` 로 돈 것** — C# 14 의 판정이다.
- ★ **진단 문구 전부** · **`run exit=134`**(SIGABRT) · **IL 오프셋 폭**.

**언어가 보장하는 것**(구현이 바뀌어도 같다)

- **속성이 접근자 메서드로 컴파일되는** 것.
- **계산 속성에 저장소가 생기지 않는** 것.
- **`init` 이 객체 초기자·생성자의 `this`/`base`·`init` 접근자에서만 대입 가능한** 것.
- **`required` 를 컴파일러가 생성 지점마다 검사하는** 것, 그리고 **`[SetsRequiredMembers]` 가 면제 선언인** 것.
- **`readonly` 가 선언한 타입의 생성자·`init` setter·변수 초기자에서만 대입되는** 것.
- **접근자 한정자가 속성보다 좁아야 하고 한쪽에만 붙는** 것.
- **자동 구현 속성이 `ref` 로 돌려줄 수 없는** 것, **`ref` 반환 속성에 `set` 을 둘 수 없는** 것.
- **`field` 가 속성 접근자 몸통 안에서 문맥 키워드인** 것(C# 14).

**안 돌려 본 것 / 못 잰 것 / 잴 것이 없는 것**

- **안 돌려 본 것** — ★ **`-langversion:13` 이하에서 `field` 가 어떤 진단을 내는지** ·\
  ★ **`struct` 의 속성**(`readonly struct` 의 접근자 제약이 다르다 — [02번](../02-struct-vs-class-choosing/)) ·\
  ★ **`static` 속성과 정적 생성자** · ★ **인터페이스의 `static abstract` 속성**(C# 11) ·\
  ★ **`record` 의 위치 매개변수가 만드는 `init` 속성**(목록의 **18번 주제**) ·\
  ★ **net5.0 이전 타겟에서 `IsExternalInit` 을 직접 선언하는 판**(이 판은 net10.0 뿐이다).
- **못 잰 것** — ★★★ **「속성 접근이 필드 접근보다 비싼가」.**\
  접근자가 `ldfld` 한 줄이면 JIT 이 인라인해 같아진다는 것이 통설이지만,\
  **재려면 인라인 여부를 직접 관찰하는 하네스가 필요하고 이 판에서는 안 만들었다.**\
  ★ **한 판의 절댓값은 근거가 아니다**(규칙 24) — 그래서 **수치를 하나도 안 적었다.**
- ★ 「**부적용인 창**」 — **④ 할당 바이트.** 자동 구현 속성을 쓰든 필드를 쓰든 **객체 하나에 필드 하나**이고,\
  계산 속성은 **필드가 아예 없어 견줄 짝이 없다.** **「안 쟀다」가 아니라 「잴 것이 없다」다**(규칙 18-B).

**버전이 올랐을 때 다시 돌려야 하는 것**

- ★★★ **10번의 탐침 일곱** — 컴파일러가 자기 참조 속성을 경고하기 시작하면 이 절의 결론이 바뀐다.
- ★★ **6번의 `CS9258`** — `field` 이름 충돌이 경고에서 에러로 올라갈 수 있다.
- ★★ **1번의 숨은 필드 이름** — Roslyn 이 바꾸면 움직인다.
- ★ **2번·3번·5번의 진단 코드** — **명세가 정한 것이라 바뀔 일이 없다.** 바뀌면 그것이 뉴스다.
