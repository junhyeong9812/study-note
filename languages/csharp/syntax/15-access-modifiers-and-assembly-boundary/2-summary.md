# csharp/syntax/15 — 접근 한정자와 어셈블리 경계 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [ECMA-334 7판(2023-12)](https://ecma-international.org/publications-and-standards/standards/ecma-334/) ·
> [Learn — 접근 한정자](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/keywords/access-modifiers) ·
> [Learn — 접근성 수준](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/keywords/accessibility-levels) ·
> [.NET API — `InternalsVisibleToAttribute`](https://learn.microsoft.com/en-us/dotnet/api/system.runtime.compilerservices.internalsvisibletoattribute) ·
> [Learn — `file` 한정 타입(C# 11)](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/keywords/file)
> **실행 검증** — 이 문서의 모든 출력·진단은 아래 「이 판」의 도구로 **실제로 돌려 얻은 것**이다(2026-09-26).\
> ★★★ **이 주제는 어셈블리를 둘 만들어 던졌다** — `liba.dll`(라이브러리)과 `appb.dll`(그것을 참조하는 쪽).\
> **한 파일로는 물을 수 없는 유일한 주제**라서 캡처 스크립트가 **컴파일을 두 번** 돌린다.\
> ★ 블록은 캡처 스크립트가 파일로 받아 조립기가 끼워 넣은 것이다 — 사람이 옮겨 적은 줄은 하나도 없다.\
> ★★★ **진단 언어를 영어로 고정했다**(`DOTNET_CLI_UI_LANGUAGE=en` + `-preferreduilang:en-US`).
> **버전** — 여섯 한정자 중 `private protected` 는 **C# 7.2**, `file` 은 **C# 11** 이다. 나머지는 **C# 1.0부터**.
> **경계** — **접근자 접근성**(`{ get; private set; }`)은 [13번](../13-properties-init-required-field/) (6)이 정본이고,\
> **`protected` 가 상속에서 하는 일**은 [16번](../16-inheritance-virtual-override-abstract-sealed-new/), **클래스 문법 자체**는 [12번](../12-class-fields-constructors-this-base/)이다.\
> 여기서는 「**어디까지 보이나**」만 센다.
> ★★★ **대비** — Java 갈래 목록([`java/syntax/README.md`](../../../java/syntax/README.md))의 **10번**([`10-access-modifiers/`](../../../java/syntax/10-access-modifiers/))이 **직접 대비**다.\
> **javac 21.0.5 로 같은 모양의 프로그램을 던져 (8)에 나란히 놓았다.**\
> ★ C++ 갈래 목록([`cpp/syntax/README.md`](../../../cpp/syntax/README.md))의 **12번**([`12-class-basics-members-access-and-this/`](../../../cpp/syntax/12-class-basics-members-access-and-this/))은 세 단계뿐이라 **어셈블리 축이 아예 없다.**
>
> ★★ **흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | 진단 **문구** — 판마다 다듬인다 | ★★★ **진단 코드**(`CS0122`·`CS1061`·`CS0103`·`CS0281`·`CS0050`…)와 **`(행,열)`** |
> | `CS0281` 문구에 박힌 **어셈블리 버전·`PublicKeyToken` 표기** | ★★★ **어느 멤버가 막히고 어느 멤버가 통과했나** — 이 주제의 답 자체다 |
> | ★ **증분의 절댓값 일부** — 이 주제는 그 칸을 **안 세웠다**(아래 (0)) | ★★ **`cc exit`**(0 인가 1 인가) · **막힌 건수** |
> | 여러 진단이 나올 때 Roslyn 이 내는 **순서** — 배너에 `\| sort` 를 적었다 | ★★ **`FieldAttributes` 의 이름**(`FamORAssem`·`FamANDAssem`) |
> | javac 가 에러를 내는 **순서** | ★★ **javac 의 에러 개수와 어느 필드에 붙었나** |

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
| **언어 명세(ECMA-334)** | C# 언어가 약속한 것 | ★★★ **여섯 한정자의 의미** · **기본 접근성 세 가지** · 일관성 규칙(`CS0050`/`CS0051`) |
| **런타임·CLI 메타데이터** | CoreCLR·CLI 가 그렇게 적는 것 | ★★★ **`FamORAssem`·`FamANDAssem` 이라는 메타데이터 이름**((2)) · `InternalsVisibleTo` 를 읽는 것 |
| **이 판의 관찰** | .NET 10.0.12 · linux-x64 · javac 21.0.5 에서 이번에 본 것 | 진단 문구 · `CS0281` 이 나오는 자리 · javac 의 에러 표기 |

★★★ **이 주제는 세 번째 칸이 얇고 첫 칸이 두껍다.** 접근성은 **컴파일 시점에 전부 결정**되고\
런타임은 거의 관여하지 않는다 — 그래서 **「이 판에서만 그렇다」고 적을 것이 거의 없다.**

## 한눈에 — 쉽게 말하면

**C# 의 접근성은 축이 둘이다 — 「집안(상속)」과 「건물(어셈블리)」.**

회사 건물을 생각하자.

- **`public`** — 길 가는 사람 아무나.
- **`internal`** — ★★★ **이 건물 안 사람 전부**(같은 어셈블리).
- **`protected`** — ★★★ **우리 집안 사람 전부**(파생 클래스). **건물이 달라도 된다.**
- **`protected internal`** — **집안 사람 「또는」 건물 사람**. ★ 둘을 **더한 것**이라 **넓다.**
- **`private protected`** — **집안 사람 「이고 동시에」 건물 사람**. ★ 둘을 **곱한 것**이라 **좁다.**
- **`private`** — 나만.

| 비유 | C# 낱말 | ★★★ 메타데이터에 적히는 이름 | 넓이 |
|---|---|---|---|
| 아무나 | `public` | `Public` | 1위 |
| 집안 **또는** 건물 | `protected internal` | ★★★ **`FamORAssem`** | 2위 |
| 우리 집안 | `protected` | `Family` | 3위 |
| 이 건물 | `internal` | `Assembly` | 3위(★ `protected` 와 **비교 불가**) |
| 집안 **이고** 건물 | `private protected` | ★★★ **`FamANDAssem`** | 5위 |
| 나만 | `private` | `Private` | 6위 |

- ★★★ **C# 낱말이 헷갈리는 자리가 여기다.** `protected internal` 과 `private protected` 는\
  **낱말만 보면 어느 쪽이 넓은지 안 읽힌다.**
- ★★★ **메타데이터 이름을 보면 한 글자로 갈린다** — **`OR` 이면 넓고 `AND` 면 좁다**((2)).\
  이 이름은 리플렉션으로 직접 찍을 수 있다. **외우지 말고 이 표를 머릿속에서 `OR`/`AND` 로 바꿔 읽어라.**

> **어셈블리(assembly)** — `.dll`/`.exe` 하나. C# 의 `internal` 은 **이 단위**로 잘린다.\
> ★★★ **Java 의 package 와 다르다** — package 는 **이름 공간**이고 어셈블리는 **배포 단위**다((8)).

> **친구 어셈블리(friend assembly)** — `[assembly: InternalsVisibleTo("이름")]` 로 지목한 다른 어셈블리.\
> 그쪽에서는 이 어셈블리의 `internal` 이 보인다((4)).

```text
        상속 축 ─────────────────────────────>
   어  │            파생 아님        파생임
   셈  │  같은      internal        internal · protected
   블  │  어셈블리   (·public)        · protected internal · private protected
   리  │
   축  │  다른      public          public · protected
   │  │  어셈블리                    · protected internal
   v  │                            ★ private protected 는 여기서 막힌다

   ★★★ 세 축이 아니라 두 축이고, 여섯 한정자가 그 격자의 서로 다른 칸을 덮는다.
```

## 이 주제가 답하려는 질문

1. **여섯 한정자가 각각 어디까지 열리나** — **같은 어셈블리 / 다른 어셈블리 / 파생 여부** 세 자리에서((1)(3)).
2. **`protected internal` 과 `private protected` 는 어디서 갈리나**((2)(5)).
3. **`internal` 을 뚫는 방법이 있나** — `InternalsVisibleTo`((4)).
4. **한정자를 안 적으면 무엇이 되나** — **최상위 타입·중첩 타입·멤버가 전부 다르다**((6)).
5. **Java 와 어디가 갈리나** — **어셈블리 대 package**((8)).

## 동작 방식

### (0) 이 주제가 쓰는 창

| 창 | 무엇을 보여 주나 | 이 주제에서 |
|---|---|---|
| ★★★ **② 진단 격자** | ★★★ **어느 멤버가 막히고 어느 멤버가 통과했나** — 이 주제의 본체 | (1)(3)(4)(5)(6)(7)(8) |
| ★★ **③ 리플렉션** | ★★★ **`FamORAssem`·`FamANDAssem`** — C# 낱말이 못 보여 주는 것 | (2) |
| **① IL 덤프** | ★ **부적용** — 아래 | — |
| **④ 할당 바이트** | ★ **부적용** — 아래 | — |

- ★★★ **본체는 ② 진단 격자다.** 그리고 **이 주제에서만 진단 격자가 두 어셈블리에 걸쳐 있다** —\
  같은 소스를 **같은 어셈블리에 넣었을 때와 다른 어셈블리에서 참조할 때** 진단이 달라지는 것이 답이다.\
  ★ 캡처 스크립트가 `csc -target:library -out:liba.dll` 과 `csc -r:liba.dll -out:appb.dll` 을 **따로** 돌린다.

```text
   ┌─────────── liba.dll ───────────┐        ┌─────────── appb.dll ───────────┐
   │  public class Vault            │        │  class OutsiderB               │
   │    public    int Pub           │ ─참조─> │    v.Pub       ○               │
   │    protected int Prot          │        │    v.Prot      ✕ CS0122        │
   │    internal  int Intl          │        │    v.Intl      ✕ CS1061 ★없는 것 │
   │    protected internal ProtIntl │        │    v.ProtIntl  ✕ CS0122        │
   │    private protected PrivProt  │        │    v.PrivProt  ✕ CS0122        │
   │    private   int Priv          │        │    v.Priv      ✕ CS1061 ★없는 것 │
   └────────────────────────────────┘        └────────────────────────────────┘
                 │
                 └── [assembly: InternalsVisibleTo("appb")] 한 줄을 넣으면
                     Intl 과 ProtIntl 이 열린다 ── cc exit 가 1 에서 0 으로
```
- ★★ **③ 리플렉션이 (2) 하나를 맡는다** — **C# 낱말로는 못 읽히는 `OR`/`AND` 를 메타데이터가 직접 적어 준다.**\
  ★★★ **이것이 「창을 바꿔 답한 것」이다**(규칙 18-B 의 제5의 상태) — 「어느 쪽이 넓은가」를\
  진단으로 물으면 **격자를 여섯 칸 다 던져야** 알 수 있는데, 리플렉션은 **한 줄로 답한다.**\
  ★ 바꾼 창이 못 보는 것도 적어 둔다 — **메타데이터는 「누가 볼 수 있나」를 말하지 「지금 이 호출이 되나」를 말하지 않는다.** 그래서 (1)(3)이 따로 필요하다.
- ★ **「부적용인 창」 둘 — ① IL 덤프와 ④ 할당 바이트.**\
  접근 한정자는 **멤버 본문을 한 글자도 안 바꾼다.** `public int Pub` 과 `private int Priv` 의\
  **`ldfld` 가 같다.** 바뀌는 것은 **시그니처의 접근성 비트 하나**이고 그것은 (2)가 이미 찍는다.\
  ★★★ **「재 봤더니 같았다」가 아니라 「잴 것이 없다」다**(규칙 18-B).

### (1) ★★★ 여섯 한정자 — 같은 어셈블리에서

**언제 쓰나** — 멤버를 선언할 때마다. **이 절과 (3)이 이 주제의 중심이다.**

```text
===== 소스: cs15b-vault.cs =====
public class Vault {
    public              int Pub      = 1;
    protected           int Prot     = 2;
    internal            int Intl     = 3;
    protected internal  int ProtIntl = 4;
    private protected   int PrivProt = 5;
    private             int Priv     = 6;

    public string Read() => $"{Pub}{Prot}{Intl}{ProtIntl}{PrivProt}{Priv}";
}
===== 소스: cs15b-same.cs =====
class Outsider {            // 같은 어셈블리 · 파생 아님
    void Touch(Vault v) {
        _ = v.Pub;
        _ = v.Prot;
        _ = v.Intl;
        _ = v.ProtIntl;
        _ = v.PrivProt;
        _ = v.Priv;
    }
}
class Heir : Vault {        // 같은 어셈블리 · 파생
    void Touch() {
        _ = Pub;
        _ = Prot;
        _ = Intl;
        _ = ProtIntl;
        _ = PrivProt;
        _ = Priv;
    }
}
===== csc -target:library -out:liba.dll cs15b-vault.cs cs15b-same.cs 2>&1 | sort (cc exit=1) =====
cs15b-same.cs(18,13): error CS0122: 'Vault.Priv' is inaccessible due to its protection level
cs15b-same.cs(4,15): error CS0122: 'Vault.Prot' is inaccessible due to its protection level
cs15b-same.cs(7,15): error CS0122: 'Vault.PrivProt' is inaccessible due to its protection level
cs15b-same.cs(8,15): error CS0122: 'Vault.Priv' is inaccessible due to its protection level
```

- ★★★ **같은 어셈블리 · 파생 아님**(`Outsider`) — **`Prot` 과 `PrivProt` 과 `Priv` 가 막힌다.**\
  `Pub`·`Intl`·`ProtIntl` 은 통과한다. **`internal` 이 같은 어셈블리에서는 `public` 과 구분이 안 된다.**
- ★★★ **같은 어셈블리 · 파생**(`Heir`) — **`Priv` 하나만 막힌다.**\
  `Prot`·`PrivProt` 이 여기서 열린다 — **상속 축이 붙었기 때문**이다.
- ★★ **진단 코드가 전부 `CS0122`** 다 — 「보호 수준 때문에 접근할 수 없다」.\
  ★ **이름이 보이긴 한다**는 뜻이다. (3)에서 이 코드가 **다른 코드로 바뀌는 것**이 이 주제의 핵심 관찰이다.
- ★ **에러 네 건**이고 `cc exit=1` 이다.

### (2) ★★★ 헷갈리는 두 낱말 — 메타데이터가 한 글자로 가른다

```text
===== 소스: cs15b-meta.cs =====
using System;
using System.Reflection;
public class Vault2 {
    public              int Pub      = 1;
    protected           int Prot     = 2;
    internal            int Intl     = 3;
    protected internal  int ProtIntl = 4;
    private protected   int PrivProt = 5;
    private             int Priv     = 6;
}
class Program {
    static void Main() {
        Console.WriteLine($"{"C# 에 쓴 것",-20} {"IL 속성",-14} {"IsAssembly",-11} {"IsFamily",-9} {"IsFamilyOrAssembly",-19} IsFamilyAndAssembly");
        foreach (var f in typeof(Vault2).GetFields(BindingFlags.Public|BindingFlags.NonPublic|BindingFlags.Instance)) {
            var a = f.Attributes & FieldAttributes.FieldAccessMask;
            Console.WriteLine($"{f.Name,-20} {a,-14} {f.IsAssembly,-11} {f.IsFamily,-9} {f.IsFamilyOrAssembly,-19} {f.IsFamilyAndAssembly}");
        }
    }
}
===== csc -out:ex.dll cs15b-meta.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
cs15b-meta.cs(9,29): warning CS0414: The field 'Vault2.Priv' is assigned but its value is never used
C# 에 쓴 것             IL 속성          IsAssembly  IsFamily  IsFamilyOrAssembly  IsFamilyAndAssembly
Pub                  Public         False       False     False               False
Prot                 Family         False       True      False               False
Intl                 Assembly       True        False     False               False
ProtIntl             FamORAssem     False       False     True                False
PrivProt             FamANDAssem    False       False     False               True
Priv                 Private        False       False     False               False
```

- ★★★ **`protected internal` → `FamORAssem`** · **`private protected` → `FamANDAssem`**.\
  **`OR` 은 합집합이라 넓고 `AND` 는 교집합이라 좁다.** C# 낱말로는 절대 안 읽히는 것이 여기 한 줄로 나온다.
- ★★★ **리플렉션 속성 이름도 그대로다** — `IsFamilyOrAssembly` 와 `IsFamilyAndAssembly`.\
  ★ **`internal` 의 이름이 `Assembly` 인 것**도 중요하다 — **C# 낱말이 `internal` 이라 「안쪽」으로 읽히는데**\
  메타데이터는 **「어셈블리」라고 단위를 못 박는다.**
- ★★ **외우는 법** — `protected internal` 은 두 낱말을 **더하는 것**(둘 중 하나만 맞으면 된다),\
  `private protected` 는 `private` 이 앞에 있어 **깎는 것**(둘 다 맞아야 한다).
- ★ `Priv` 에 `CS0414` 경고가 같이 났다 — 안 쓰는 private 필드다. **그것도 출력이다.**

> **어느 층인가** — ★★★ **여섯 한정자의 의미는 명세**다.\
> ★★★ **`FamORAssem`·`FamANDAssem` 이라는 이름은 CLI 메타데이터의 것**이다 — C# 이 아니라 **런타임 층**이고,\
> 그래서 **다른 .NET 언어에서도 같은 이름**으로 보인다.

### (3) ★★★ 다른 어셈블리에서 — `CS0122` 가 `CS1061` 로 바뀐다

```text
===== 소스: cs15b-other.cs =====
class OutsiderB {           // 다른 어셈블리 · 파생 아님
    void Touch(Vault v) {
        _ = v.Pub;
        _ = v.Prot;
        _ = v.Intl;
        _ = v.ProtIntl;
        _ = v.PrivProt;
        _ = v.Priv;
    }
}
class HeirB : Vault {       // 다른 어셈블리 · 파생
    void Touch() {
        _ = Pub;
        _ = Prot;
        _ = Intl;
        _ = ProtIntl;
        _ = PrivProt;
        _ = Priv;
    }
}
class Program { static void Main() { } }
===== csc -target:library -out:liba.dll cs15b-vault.cs (cc exit=0) =====
===== csc -r:liba.dll -out:appb.dll cs15b-other.cs 2>&1 | sort (cc exit=1) =====
cs15b-other.cs(15,13): error CS0103: The name 'Intl' does not exist in the current context
cs15b-other.cs(17,13): error CS0122: 'Vault.PrivProt' is inaccessible due to its protection level
cs15b-other.cs(18,13): error CS0103: The name 'Priv' does not exist in the current context
cs15b-other.cs(4,15): error CS0122: 'Vault.Prot' is inaccessible due to its protection level
cs15b-other.cs(5,15): error CS1061: 'Vault' does not contain a definition for 'Intl' and no accessible extension method 'Intl' accepting a first argument of type 'Vault' could be found (are you missing a using directive or an assembly reference?)
cs15b-other.cs(6,15): error CS0122: 'Vault.ProtIntl' is inaccessible due to its protection level
cs15b-other.cs(7,15): error CS0122: 'Vault.PrivProt' is inaccessible due to its protection level
cs15b-other.cs(8,15): error CS1061: 'Vault' does not contain a definition for 'Priv' and no accessible extension method 'Priv' accepting a first argument of type 'Vault' could be found (are you missing a using directive or an assembly reference?)
```

- ★★★ **`Intl` 과 `Priv` 의 진단 코드가 바뀌었다.**\
  - (1)에서는 `CS0122`(「보호 수준 때문에 접근 불가」) 였는데,\
  - 여기서는 **`CS1061`**(「그런 정의가 **없다**」) 과 **`CS0103`**(「그런 **이름이 없다**」) 이다.
- ★★★ **이것이 이 주제에서 가장 중요한 관찰이다.** 다른 어셈블리에서 `internal` 멤버는\
  **「보이는데 막힌 것」이 아니라 「아예 존재하지 않는 것」으로 보인다.**\
  ★ 컴파일러가 참조 어셈블리의 메타데이터를 읽을 때 **그 멤버를 후보에서 통째로 뺀다.**\
  ★★ **그래서 「확장 메서드를 찾지 못했다」는 문구까지 붙는다** — 이름 해석이 **완전히 실패한 경로**를 탔다는 증거다.
- ★★★ **`Prot`·`ProtIntl`·`PrivProt` 은 여전히 `CS0122` 다** — **이름은 보인다.**\
  `public` 타입의 `protected` 멤버는 **메타데이터에 남아 있어야** 파생 클래스가 쓸 수 있기 때문이다.
- ★★★ **다른 어셈블리 · 파생**(`HeirB`) 에서 **`ProtIntl` 이 통과했다**(15행에 `Intl` 만 에러다).\
  `protected internal` 은 **`OR` 이라 상속 축만 맞아도 열린다.**
- ★★★ **반면 `PrivProt` 은 파생인데도 `CS0122` 로 막혔다**(17행).\
  `private protected` 는 **`AND` 라 어셈블리 축까지 맞아야** 한다. **(2)의 표가 여기서 값으로 확인된다.**

```text
   컴파일러가 참조 어셈블리의 메타데이터를 읽을 때

   public / protected 계열          internal / private
   ┌──────────────────┐            ┌──────────────────┐
   │ 후보 목록에 들어감 │            │ 후보 목록에서 빠짐 │
   └────────┬─────────┘            └────────┬─────────┘
            │ 접근성 검사에서 탈락             │ 이름 해석 자체가 실패
            ▼                                ▼
        CS0122                           CS1061 · CS0103
     「막혔다」                           「없다」
     ★ IDE 자동 완성에 뜬다              ★ 자동 완성에도 안 뜬다
```

### (4) ★★ `InternalsVisibleTo` — 뚫는 것

```text
===== 소스: cs15b-vault.cs =====
public class Vault {
    public              int Pub      = 1;
    protected           int Prot     = 2;
    internal            int Intl     = 3;
    protected internal  int ProtIntl = 4;
    private protected   int PrivProt = 5;
    private             int Priv     = 6;

    public string Read() => $"{Pub}{Prot}{Intl}{ProtIntl}{PrivProt}{Priv}";
}
===== 소스: cs15b-ivt.cs =====
using System.Runtime.CompilerServices;
[assembly: InternalsVisibleTo("appb")]
===== 소스: cs15b-friend.cs =====
using System;
class Friend {                          // 친구 어셈블리 · 파생 아님
    public static string Touch(Vault v) => $"{v.Pub} {v.Intl} {v.ProtIntl}";
}
class Program { static void Main() => Console.WriteLine(Friend.Touch(new Vault())); }
===== csc -target:library -out:libnoivt.dll cs15b-vault.cs && csc -r:libnoivt.dll -out:appb.dll cs15b-friend.cs (cc exit=1) =====
cs15b-friend.cs(3,57): error CS1061: 'Vault' does not contain a definition for 'Intl' and no accessible extension method 'Intl' accepting a first argument of type 'Vault' could be found (are you missing a using directive or an assembly reference?)
cs15b-friend.cs(3,66): error CS0122: 'Vault.ProtIntl' is inaccessible due to its protection level
===== csc -target:library -out:liba.dll cs15b-vault.cs cs15b-ivt.cs && csc -r:liba.dll -out:appb.dll cs15b-friend.cs && dotnet appb.dll (cc exit=0 · run exit=0) =====
1 3 4
```

- ★★★ **위 판은 `cc exit=1`, 아래 판은 `cc exit=0` 이고 `1 3 4` 가 찍혔다.**\
  같은 소스가 **`InternalsVisibleTo` 한 줄로 컴파일이 되고 안 되고가 갈린다.**
- ★★★ **뚫린 것은 `Intl`(internal)과 `ProtIntl`(protected internal) 둘이다.**\
  값 `3`(Intl)과 `4`(ProtIntl)가 실제로 찍혔다 — **선언만 통과한 게 아니라 읽혔다.**
- ★★ **어셈블리 이름으로 지목한다** — 여기서는 `-out:appb.dll` 이므로 이름이 `appb` 다.\
  ★ 강력한 이름(strong name)으로 서명한 어셈블리라면 **공개 키까지 적어야** 한다 — 그 판은 **안 던졌다.**
- ★ 실무에서 이것을 쓰는 자리는 사실상 하나다 — **테스트 어셈블리에서 `internal` 을 보는 것.**

`private protected` 는 친구 어셈블리에서 어떻게 되나.

```text
===== 소스: cs15b-pp.cs =====
class StrangerPP    { void Touch(Vault v) { _ = v.PrivProt; } }   // 친구 어셈블리 · 파생 아님
class Program { static void Main() { } }
===== 소스: cs15b-ppheir.cs =====
class HeirPP : Vault { void Touch() { _ = PrivProt; } }           // 친구 어셈블리 · 파생
class Program { static void Main() { } }
===== csc -r:liba.dll -out:appb.dll cs15b-pp.cs (cc exit=1) =====
cs15b-pp.cs(1,51): error CS0281: Friend access was granted by 'liba, Version=0.0.0.0, Culture=neutral, PublicKeyToken=null', but the public key of the output assembly ('') does not match that specified by the InternalsVisibleTo attribute in the granting assembly.
===== csc -r:liba.dll -out:appb.dll cs15b-ppheir.cs (cc exit=0) =====
```

- ★★★ **파생 아닌 쪽은 막히고**(`StrangerPP`, `cc exit=1`) **파생한 쪽은 통과한다**(`HeirPP`, `cc exit=0`).\
  즉 **친구 어셈블리는 `AND` 의 「어셈블리」 조건을 만족시키고**, 남은 「파생」 조건은 여전히 필요하다.
- ★★ **막힌 쪽의 진단이 `CS0122` 가 아니라 `CS0281` 이다.**\
  문구가 **공개 키가 안 맞는다**고 말하는데 ★★★ **이 판에서 두 어셈블리 모두 `PublicKeyToken=null` 이다** —\
  즉 **문구가 실제 원인을 가리키지 않는다.** 실제 원인은 **파생이 아니라는 것**이다.
- ★★★ **그래서 여기서는 문구를 근거로 쓰지 않는다.** 근거는 **`cc exit` 두 개가 갈렸다는 사실**이다 —\
  같은 어트리뷰트·같은 두 어셈블리에서 **파생 여부 하나만 바꿨더니 0 과 1 로 갈렸다.**\
  ★ 지침의 「진단 문구는 흔들리는 칸」이 **문구가 틀릴 수도 있다**는 형태로 나온 자리다.

### (5) ★★ 세 축 전수 격자

앞 절들을 한 표로 모은다. **전부 위 블록들에서 읽은 것**이고 새로 추측한 칸은 없다.

| 한정자 | 같은 어셈블리<br>파생 아님 | 같은 어셈블리<br>파생 | 다른 어셈블리<br>파생 아님 | 다른 어셈블리<br>파생 | 친구 어셈블리<br>파생 아님 | 친구 어셈블리<br>파생 |
|---|---|---|---|---|---|---|
| `public` | ○ (1) | ○ (1) | ○ (3) | ○ (3) | ○ (4) | ○ |
| `protected internal` | ○ (1) | ○ (1) | ✕ `CS0122` (3) | ★ **○** (3) | ★ **○** (4) | ○ |
| `protected` | ✕ `CS0122` (1) | ○ (1) | ✕ `CS0122` (3) | ○ (3) | ✕ `CS0122` (4) | ○ |
| `internal` | ○ (1) | ○ (1) | ✕ `CS1061` (3) | ✕ `CS0103` (3) | ★ **○** (4) | ○ |
| `private protected` | ✕ `CS0122` (1) | ○ (1) | ✕ `CS0122` (3) | ★ **✕ `CS0122`** (3) | ✕ `CS0281` (4) | ★ **○** (4) |
| `private` | ✕ `CS0122` (1) | ✕ `CS0122` (1) | ✕ `CS1061` (3) | ✕ `CS0103` (3) | ✕ (4) | ✕ |

- ★★★ **읽는 법 셋.**
  1. **`protected internal` 행과 `private protected` 행을 비교하라** — 「다른 어셈블리 · 파생」 칸에서 갈린다.
  2. **`internal` 행과 `private` 행의 진단 코드가 같다** — 다른 어셈블리에서는 둘 다 「**없는 것**」이다.
  3. **`protected` 행은 어셈블리 축을 안 탄다** — 어느 건물이든 집안이면 된다.
- ★ **`internal` 과 `protected` 는 서로 넓고 좁음을 못 정한다** — 서로 다른 축이라 **비교 불가**다.

### (6) ★ 한정자를 안 적으면 — 세 자리가 전부 다르다

```text
===== 소스: cs15b-def.cs =====
class TopDefault { public int N = 1; }              // 최상위 타입 — 한정자 없음
public class Wrapper {
    class NestedDefault { }                         // 중첩 타입 — 한정자 없음
    int memberDefault = 2;                          // 멤버 — 한정자 없음
    public string Show() => $"{memberDefault} {new NestedDefault()}";
}
===== 소스: cs15b-defuse.cs =====
class Probe {
    void Touch(Wrapper w) { _ = w.memberDefault; }
    void MakeTop()        { _ = new TopDefault();  }
}
class Program { static void Main() { } }
===== csc -target:library -out:libdef.dll cs15b-def.cs (cc exit=0) =====
===== csc -target:library -out:same.dll cs15b-def.cs cs15b-defuse.cs (cc exit=1) =====
cs15b-defuse.cs(2,35): error CS0122: 'Wrapper.memberDefault' is inaccessible due to its protection level
===== csc -r:libdef.dll -out:ex.dll cs15b-defuse.cs 2>&1 | sort (cc exit=1) =====
cs15b-defuse.cs(2,35): error CS1061: 'Wrapper' does not contain a definition for 'memberDefault' and no accessible extension method 'memberDefault' accepting a first argument of type 'Wrapper' could be found (are you missing a using directive or an assembly reference?)
cs15b-defuse.cs(3,37): error CS0122: 'TopDefault' is inaccessible due to its protection level
```

- ★★★ **세 자리의 기본값이 전부 다르다.**

| 자리 | 안 적으면 | 근거 |
|---|---|---|
| **최상위 타입** | ★★ **`internal`** | 다른 어셈블리에서 `CS0122` — 같은 어셈블리에서는 통과 |
| **중첩 타입** | ★★★ **`private`** | (7)의 `CS0050` 이 그 증거다 |
| **멤버** | ★★★ **`private`** | 같은 어셈블리에서도 `CS0122` |

- ★★★ **「같은 어셈블리」 판에서도 `memberDefault` 가 막힌 것**이 멤버 기본값의 증거다.\
  ★ **최상위 타입 `TopDefault` 는 같은 어셈블리 판에서 통과했다** — 두 줄 중 한 줄만 에러다.
- ★★★ **다른 어셈블리 판에서는 `TopDefault` 도 `CS0122` 로 막힌다** — 기본값이 `internal` 이라서다.
- ★★ **멤버가 `private` 인 것과 타입이 `internal` 인 것이 다른 이유** — 타입은 **파일 안에서 혼자 쓰이는 일이 없고**,\
  멤버는 **혼자 쓰이는 것이 기본**이기 때문이다. ★ **외우지 말고 「타입은 건물 안, 멤버는 방 안」으로 읽어라.**

```text
   class TopDefault { … }                 ← 최상위 타입   → internal  (건물 안)
   public class Wrapper {
       class NestedDefault { }            ← 중첩 타입     → private   (방 안)
       int memberDefault = 2;             ← 멤버          → private   (방 안)
   }

   같은 어셈블리에서   TopDefault ○   ·  memberDefault ✕ CS0122
   다른 어셈블리에서   TopDefault ✕ CS0122  ·  memberDefault ✕ CS1061
   중첩 타입의 증거는  public 메서드가 돌려주려 할 때 → CS0050
```

### (7) ★★ 좁은 것을 넓은 곳에 노출하면

```text
===== 소스: cs15b-nested.cs =====
public class Wrapper {
    class NestedDefault { }
    public NestedDefault Leak() => new NestedDefault();
}
===== csc -target:library -out:libn.dll cs15b-nested.cs (cc exit=1) =====
cs15b-nested.cs(3,26): error CS0050: Inconsistent accessibility: return type 'Wrapper.NestedDefault' is less accessible than method 'Wrapper.Leak()'
```

```text
===== 소스: cs15b-expose.cs =====
internal class Secret { }
public class Door {
    public   Secret Give() => new Secret();
    public   void   Take(Secret s) { }
    internal Secret Ok()   => new Secret();
}
===== csc -target:library -out:libexp.dll cs15b-expose.cs 2>&1 | sort (cc exit=1) =====
cs15b-expose.cs(3,21): error CS0050: Inconsistent accessibility: return type 'Secret' is less accessible than method 'Door.Give()'
cs15b-expose.cs(4,21): error CS0051: Inconsistent accessibility: parameter type 'Secret' is less accessible than method 'Door.Take(Secret)'
```

- ★★★ **`CS0050` — 반환 타입이 메서드보다 좁다.** `public` 메서드가 `private`/`internal` 타입을 돌려주면 막힌다.
- ★★★ **`CS0051` — 매개변수 타입이 메서드보다 좁다.** 받는 쪽도 같다.
- ★★ **`internal Secret Ok()` 은 통과한다** — 메서드도 `internal` 이면 일관성이 맞는다.\
  **에러가 두 건뿐인 것**이 그 증거다(세 메서드 중 하나가 조용하다).
- ★★★ **`CS0050` 이 (6)의 「중첩 타입 기본값 = `private`」을 증명한다** — `NestedDefault` 에 한정자를 안 적었는데\
  「`Wrapper.NestedDefault` 가 `Wrapper.Leak()` 보다 덜 접근 가능하다」고 컴파일러가 말했다.
- ★ **이것이 왜 필요한가** — 돌려받은 값의 **타입 이름을 쓸 수 없으면** 그 메서드를 못 쓴다.\
  `var` 로 받으면 되지 않나 싶지만, **그러면 그 타입의 멤버를 부르는 순간 다시 막힌다.**

### (8) ★ `file` 한정자(C# 11) — 축이 하나 더

```text
===== 소스: cs15b-file1.cs =====
file class Hidden { public int N = 11; }
public class GateOne { public int Peek() => new Hidden().N; }
===== 소스: cs15b-file2.cs =====
file class Hidden { public int N = 22; }
public class GateTwo { public int Peek() => new Hidden().N; }
===== 소스: cs15b-file3.cs =====
public class Intruder { public int Peek() => new Hidden().N; }
===== csc -target:library -out:libfile.dll cs15b-file1.cs cs15b-file2.cs (cc exit=0) =====
===== csc -target:library -out:libfile.dll cs15b-file1.cs cs15b-file2.cs cs15b-file3.cs (cc exit=1) =====
cs15b-file3.cs(1,50): error CS0246: The type or namespace name 'Hidden' could not be found (are you missing a using directive or an assembly reference?)
```

- ★★★ **같은 이름의 `file class Hidden` 둘이 한 어셈블리에 공존한다**(`cc exit=0`).\
  값이 11 과 22 로 다른 타입인데 **이름 충돌이 안 난다.**
- ★★★ **다른 파일에서 쓰면 `CS0246`**(「그런 타입이나 이름 공간이 없다」).\
  ★ **`CS0122`(보호 수준) 가 아니다** — **`internal` 을 다른 어셈블리에서 볼 때와 같은 성격**이고,\
  즉 **그 파일 밖에서는 이름 자체가 존재하지 않는다.**
- ★★ **무엇을 위한 것인가** — 소스 생성기(source generator)용이다.\
  생성기가 만든 도우미 타입이 **사용자 코드나 다른 생성기와 이름이 겹치는 것**을 막는다.
- ★ **여섯 한정자와 나란히 두면 안 된다** — `file` 은 **접근성 축이 아니라 이름 범위 축**이다.

### (9) ★★★ Java 와 대비 — package 대 어셈블리

★★★ **javac 21.0.5 로 같은 모양을 던졌다**(규칙 26 — 없다고 적기 전에 `which` 와 버전 호출을 남긴다.\
이 판의 `javac -version` 은 위 「이 판」 블록에 있다).

```text
===== 소스: jsrc/vault/Vault.java =====
package vault;
public class Vault {
    public    int pub  = 1;
    protected int prot = 2;
              int pkg  = 3;
    private   int priv = 4;
}
===== 소스: jsrc/vault/Neighbor.java =====
package vault;
public class Neighbor {          // 같은 패키지 · 파생 아님
    void touch(Vault v) {
        int a = v.pub;
        int b = v.prot;
        int c = v.pkg;
        int d = v.priv;
    }
}
===== 소스: jsrc/other/Heir.java =====
package other;
import vault.Vault;
public class Heir extends Vault {   // 다른 패키지 · 파생
    void touch() {
        int a = pub;
        int b = prot;
        int c = pkg;
        int d = priv;
    }
}
===== 소스: jsrc/other/Stranger.java =====
package other;
import vault.Vault;
public class Stranger {             // 다른 패키지 · 파생 아님
    void touch(Vault v) {
        int a = v.pub;
        int b = v.prot;
        int c = v.pkg;
        int d = v.priv;
    }
}
===== javac -d jout jsrc/vault/Vault.java jsrc/vault/Neighbor.java jsrc/other/Heir.java jsrc/other/Stranger.java (cc exit=1) =====
jsrc/vault/Neighbor.java:7: error: priv has private access in Vault
        int d = v.priv;
                 ^
jsrc/other/Heir.java:7: error: pkg is not public in Vault; cannot be accessed from outside package
        int c = pkg;
                ^
jsrc/other/Heir.java:8: error: priv has private access in Vault
        int d = priv;
                ^
jsrc/other/Stranger.java:6: error: prot has protected access in Vault
        int b = v.prot;
                 ^
jsrc/other/Stranger.java:7: error: pkg is not public in Vault; cannot be accessed from outside package
        int c = v.pkg;
                 ^
jsrc/other/Stranger.java:8: error: priv has private access in Vault
        int d = v.priv;
                 ^
6 errors
```

- ★★★ **Java 는 네 단계뿐이다** — `public` · `protected` · **한정자 없음(package-private)** · `private`.\
  C# 의 여섯과 **개수부터 다르다.**
- ★★★ **기본값이 정반대다.**
  - **Java 의 멤버 기본값은 package-private** — 같은 패키지의 아무 클래스나 본다(`Neighbor` 가 `pkg` 를 읽었다).
  - **C# 의 멤버 기본값은 `private`** — 같은 어셈블리라도 못 본다((6)).
- ★★★ **`protected` 의 뜻이 다르다.**
  - **Java 의 `protected` 는 「파생 **또는** 같은 패키지」** — C# 의 `protected internal` 에 가깝다.\
    `Neighbor`(같은 패키지, 파생 아님)가 `prot` 를 **읽었다** — 에러가 `priv` 하나뿐이다.
  - **C# 의 `protected` 는 파생만** — (1)에서 `Outsider` 가 `Prot` 에 막혔다.
- ★★★ **자르는 단위가 다르다.**
  - **package 는 이름 공간**이고 **한 jar 에 여러 package 가 들어간다.** 그래서 **배포 단위와 무관**하다.\
    ★ 그리고 **다른 jar 가 같은 package 이름을 선언하면 뚫린다**(split package). 이 판에서 그 실험은 **안 던졌다.**
  - **어셈블리는 배포 단위**다. `internal` 은 **`.dll` 하나**로 잘린다 — 뚫으려면 **선언한 쪽이 `InternalsVisibleTo` 로 허락**해야 한다((4)).
- ★★ **C# 에만 있는 칸 둘** — `internal`(건물만) 과 `private protected`(집안 `AND` 건물).\
  **Java 에는 대응물이 없다.**
- ★★ **Java 에만 있는 것** — `module-info.java` 의 `exports`(JPMS, Java 9).\
  ★★★ **이 판에서 안 던졌다** — 모듈 경로 설정이 따로 필요하다. Java 갈래 목록([`java/syntax/README.md`](../../../java/syntax/README.md))의 **10번**([`10-access-modifiers/`](../../../java/syntax/10-access-modifiers/))이 그쪽 정본이다.

> ★★★ **한쪽에서만 결론이 서는 자리가 아니다** — **양쪽 다 컴파일 에러로 답했다.**\
> C# 은 `CS0122`/`CS1061`/`CS0103`, Java 는 `error: … has private access` 류다.\
> ★ 다만 **javac 는 소스 줄과 캐럿을 끼워 준다**(`^` 표시) — **C# 진단은 `(행,열)` 만 준다.**\
> 재검증 방식이 다르므로 그 사실을 적어 둔다.

## 문법 — 형태와 규칙

### 형태

```csharp
// cs15b-vault.cs
public class Vault {
    public              int Pub      = 1;
    protected           int Prot     = 2;
    internal            int Intl     = 3;
    protected internal  int ProtIntl = 4;
    private protected   int PrivProt = 5;
    private             int Priv     = 6;

    public string Read() => $"{Pub}{Prot}{Intl}{ProtIntl}{PrivProt}{Priv}";
}
```

- **여섯 한정자는 멤버에 붙는다.** 최상위 타입에는 **`public`·`internal`·`file`** 만 붙는다(`protected` 는 **집안이 없어서** 못 붙는다).
- **중첩 타입에는 여섯이 다 붙는다** — 바깥 타입이 「집」 노릇을 하기 때문이다.
- **두 낱말짜리 둘의 순서는 고정이다** — `protected internal` 과 `private protected`.\
  ★ `internal protected` 는 **같은 뜻으로 받아 준다**(순서만 다르다). `protected private` 은 없다. **이 판에서 따로 안 던졌다.**
- **기본값은 세 자리가 다르다**((6)) — 최상위 타입 `internal` · 중첩 타입 `private` · 멤버 `private`.

### 금지 사례 — 진단이 나는 꼴

| 쓴 꼴 | 진단 코드 | 어디서 |
|---|---|---|
| 같은 어셈블리에서 `protected`·`private protected`·`private` 멤버 접근 | `CS0122` | (1) |
| 다른 어셈블리에서 `internal`·`private` 멤버 접근 | `CS1061`·`CS0103` | (3) — ★ **「없는 것」으로 보인다** |
| 다른 어셈블리 · 파생에서 `private protected` 접근 | `CS0122` | (3) — `AND` 라 막힌다 |
| 친구 어셈블리 · 파생 아님에서 `private protected` 접근 | `CS0281` | (4) — ★ **문구가 원인을 안 가리킨다** |
| 다른 어셈블리에서 한정자 없는 최상위 타입 사용 | `CS0122` | (6) — 기본값이 `internal` |
| `public` 메서드가 `internal`/`private` 타입을 **반환** | `CS0050` | (7) |
| `public` 메서드가 `internal` 타입을 **매개변수로** 받음 | `CS0051` | (7) |
| 다른 파일에서 `file` 타입 사용 | `CS0246` | (8) — ★ **`CS0122` 가 아니다** |

## 어디서 틀리나

1. ★★★ **「`protected internal` 은 `protected` 이면서 `internal`」** — **아니다.** `OR` 이라 **더 넓다**((2)(3)).\
   좁은 쪽은 `private protected`(`AND`)다.
2. ★★★ **「다른 어셈블리에서 `internal` 멤버는 `CS0122` 로 막힌다」** — **`CS1061`/`CS0103` 이다**((3)).\
   **「막힌 것」이 아니라 「없는 것」으로 보인다.** ★ 그래서 IDE 자동 완성에도 안 뜬다.
3. ★★★ **「한정자를 안 적으면 다 `private`」** — **최상위 타입만 `internal` 이다**((6)).
4. ★★ **「`InternalsVisibleTo` 면 다 뚫린다」** — `internal` 과 `protected internal` 만이다((4)).\
   ★ `private protected` 는 **파생까지 돼야** 열린다.
5. ★★ **「`CS0281` 은 강력한 이름 문제다」** — **이 판에서 두 쪽 다 `PublicKeyToken=null` 인데도 났다**((4)).\
   **문구가 원인을 안 가리킨다** — `cc exit` 로 판단하라.
6. ★★ **「`public` 클래스에 `internal` 멤버를 두면 편하다」** — 그 타입이 시그니처에 나오면 `CS0050`/`CS0051` 이다((7)).
7. ★★ **「Java 의 `protected` 와 C# 의 `protected` 가 같다」** — **다르다**((9)).\
   Java 쪽은 **같은 패키지에도 열린다.**
8. ★★ **「package 와 어셈블리는 같은 것」** — package 는 **이름 공간**, 어셈블리는 **배포 단위**다((9)).
9. ★ **「`file` 은 일곱 번째 접근 한정자」** — **접근성 축이 아니라 이름 범위 축**이다((8)).\
   진단 코드가 `CS0246` 인 것이 그 증거다.

## 구현 세부사항 대 언어 보장

| 무엇 | 층 | 근거 |
|---|---|---|
| **여섯 한정자의 의미** | ★★★ **언어 보장** | (1)(3)(5) |
| **기본 접근성 세 가지** | ★★★ **언어 보장** | (6) |
| **일관성 규칙**(`CS0050`/`CS0051`) | ★★★ **언어 보장** | (7) |
| **`file` 이 파일 밖에서 이름째 사라지는 것** | ★★★ **언어 보장**(C# 11) | (8) |
| **`FamORAssem`·`FamANDAssem` 이라는 이름** | ★★★ **CLI 메타데이터** | (2) — C# 이 아니라 런타임 층 |
| **`InternalsVisibleTo` 가 어셈블리 이름으로 지목하는 것** | ★★ **BCL 규약** | (4) |
| **다른 어셈블리의 `internal` 이 `CS1061` 로 보이는 것** | ★★ **Roslyn 의 구현** | (3) — 명세는 「접근 불가」만 정한다 |
| **`CS0281` 문구가 공개 키를 말하는 것** | ★ **이 판의 관찰** | (4) — ★ **원인을 안 가리킨다** |
| **진단 문구 전부** | ★ **이 판의 관찰** | 근거로는 **코드와 `cc exit`** 만 쓴다 |

## 언제 쓰고 언제 안 쓰나

- **`public`** — 이 어셈블리가 **약속한 표면**에만. 한 번 내보내면 **되돌리는 것이 깨는 변경**이다.
- ★★★ **`internal` 이 기본 선택지다.** 라이브러리를 만들 때 **`public` 은 의식적으로 고르는 것**이고\
  나머지는 `internal` 이어야 한다 — 그래야 나중에 자유롭게 고친다.
- **`protected`** — 파생 클래스에 **일부러 열어 주는 확장점**. [16번](../16-inheritance-virtual-override-abstract-sealed-new/)의 `virtual` 과 함께 설계한다.
- **`private protected`** — 「파생은 열어 주되 **다른 어셈블리의 파생은 안 된다**」. 드물게 쓴다.
- **`protected internal`** — **거의 안 쓴다.** `OR` 이라 넓고, 넓다는 것이 잘 안 읽혀 사고가 난다.
- **`InternalsVisibleTo`** — ★ **테스트 어셈블리에만.** 제품 코드끼리 쓰면 **경계가 없어진다.**
- **`file`** — **소스 생성기**용. 손으로 쓰는 코드에서는 거의 쓸 일이 없다.

## 핵심 문장

1. ★★★ **축이 둘이다** — 상속(집안)과 어셈블리(건물). 여섯 한정자가 그 격자의 칸을 나눠 덮는다((5)).
2. ★★★ **`OR` 이면 넓고 `AND` 면 좁다.** `protected internal` = `FamORAssem`, `private protected` = `FamANDAssem`((2)).
3. ★★★ **다른 어셈블리에서 `internal` 은 「막힌 것」이 아니라 「없는 것」이다** — `CS1061`/`CS0103`((3)).
4. ★★ **기본값이 세 자리에서 다르다** — 최상위 타입 `internal`, 중첩 타입·멤버 `private`((6)).
5. ★★ **Java 의 package 는 이름 공간, C# 의 어셈블리는 배포 단위다.** 그래서 **뚫는 방법도 다르다**((9)).

## 관련 자료

- [13번 — 속성과 `init`·`required`·`field`](../13-properties-init-required-field/) — **접근자 접근성**(`{ get; private set; }`)은 그쪽 (6)이 정본이다.
- [16번 — 상속](../16-inheritance-virtual-override-abstract-sealed-new/) — **`protected` 를 설계로 쓰는 법**과 **`virtual` 의 짝**은 그쪽.\
  ★ **명시적 인터페이스 구현이 `private` 인 것**도 그쪽 (8)이다.
- [12번 — 클래스·필드·생성자](../12-class-fields-constructors-this-base/) — **클래스 문법 자체**는 거기, 여기는 **보이는 범위**.
- [11번 — 컬렉션 초기화와 컬렉션 식](../11-collection-initializers-and-collection-expressions/) — 이 배치가 쓰는 `csc` 직접 호출 설정의 출처.
- Java 갈래 목록([`java/syntax/README.md`](../../../java/syntax/README.md))의 **10번**([`10-access-modifiers/`](../../../java/syntax/10-access-modifiers/)) — **직접 대비**((9)).
- C++ 갈래 목록([`cpp/syntax/README.md`](../../../cpp/syntax/README.md))의 **12번**([`12-class-basics-members-access-and-this/`](../../../cpp/syntax/12-class-basics-members-access-and-this/)) — 세 단계뿐이고 **어셈블리 축이 없다.**

## 용어 풀이

- **어셈블리(assembly)** — `.dll`/`.exe` 하나. `internal` 이 잘리는 단위이자 **배포 단위**다.
- **친구 어셈블리(friend assembly)** — `InternalsVisibleTo` 로 지목받아 남의 `internal` 을 보는 어셈블리.
- **`FamORAssem`** — CLI 메타데이터에서 `protected internal`. **집안 `OR` 건물**이라 넓다.
- **`FamANDAssem`** — CLI 메타데이터에서 `private protected`. **집안 `AND` 건물**이라 좁다.
- **package-private** — Java 에서 한정자를 안 적은 멤버. 같은 **패키지**에 열린다. C# 에는 대응물이 없다.
- **split package** — 여러 jar 가 같은 package 이름을 선언하는 것. Java 의 경계가 새는 자리다. **이 판에서 안 던졌다.**
- **`file` 한정 타입** — C# 11. **그 소스 파일 안에서만** 이름이 존재한다. 접근성이 아니라 **이름 범위**다.
- **강력한 이름(strong name)** — 어셈블리를 키로 서명하는 것. 서명하면 `InternalsVisibleTo` 에 **공개 키까지** 적어야 한다. **이 판에서 안 던졌다.**

## 더 들어가면

- ★ **왜 `internal` 이 어셈블리 단위인가** — .NET 에서 **버전이 매겨지고 배포되는 최소 단위가 어셈블리**이기 때문이다.\
  「같이 배포되는 것끼리는 서로 믿는다」가 설계 전제다. Java 는 그 자리에 **package** 를 두었는데,\
  ★★★ **package 는 배포 단위가 아니라서 경계가 샜다** — Java 9 의 모듈이 그것을 고치려는 시도였다((9)).
- ★ **`InternalsVisibleTo` 가 왜 「선언한 쪽」에 붙나** — 반대였다면 **아무나 남의 `internal` 을 볼 수 있다.**\
  ★ 그래서 이것은 **뚫는 구멍이 아니라 허락하는 문**이다.
- ★ **`CS0281` 의 문구 문제**((4))는 **이 판의 관찰**이다 — Roslyn 이 친구 어셈블리 경로에서 실패했을 때\
  같은 진단으로 뭉뚱그리는 것으로 보인다. ★★★ **원인을 추정했을 뿐 Roslyn 소스를 읽지 않았다.**\
  근거로 쓴 것은 **`cc exit` 가 갈렸다는 사실**뿐이다.
