# csharp/syntax/23 — 튜플과 해체(deconstruction) — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [ECMA-334 7판(2023-12)](https://ecma-international.org/publications-and-standards/standards/ecma-334/) ·
> [Learn — 튜플 타입](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/builtin-types/value-tuples)(열어서 확인: 「튜플 타입은 **값 타입**이고 원소는 **public 필드** — 그래서 **가변** 값 타입」 ·\
> 「컴파일 때 기본 아닌 필드 이름을 **기본 이름(`Item1`…)으로 바꾼다** — 그래서 명시·추론된 이름은 **런타임에 없다**」 · 「튜플 대입과 `==` 는 **필드 이름을 안 본다**」 ·\
> 「`==` 는 **원소를 차례로** 비교하고 **단락**하지만, 비교 전에 **모든 원소를 평가**한다」 · 「**공개 API 에서는 클래스나 구조체를 고려하라**」 · 「타입 안전이 필요하면 **위치 record**」)
> **실행 검증** — 이 문서의 모든 출력·진단·IL·할당 바이트는 아래 「이 판」의 도구로 **실제로 돌려 얻은 것**이다(2026-09-26).\
> ★ 블록은 캡처 스크립트가 파일로 받아 조립기가 끼워 넣은 것이다 — 사람이 옮겨 적은 줄은 하나도 없다.\
> ★★★ **진단 언어를 영어로 고정했다**(`DOTNET_CLI_UI_LANGUAGE=en` + `-preferreduilang:en-US`).
> **버전** — 값 튜플·해체 **C# 7.0** · 이름 추론(tuple projection) **C# 7.1** · 튜플 `==`/`!=` **C# 7.3** · 튜플 별칭 `using X = (int, int)` **C# 12**. ★ 이 문서는 판을 안 가렸다 — `-langversion:latest` 로만 던졌다.
> **경계** — ★★★ **`record` 가 `Deconstruct` 를 생성하는 것**은 [18번](../18-record-value-equality-and-with/) (1)이 정본이다 — 여기서는 **해체가 그것을 부른다**는 것만 인용한다.\
> ★ **`==` 가 원소 타입의 연산자를 부르는 것**의 뿌리는 [19번](../19-equality-equals-gethashcode-operator/) (3) · **위치 패턴이 `Deconstruct` 를 부르는 것**은 [21번](../21-pattern-matching-type-property-relational-list/) (4) ·\
> **다른 어셈블리로 바꿔 끼우는 무대**는 [15번](../15-access-modifiers-and-assembly-boundary/)·[17번](../17-interfaces-default-members-explicit-implementation/)·[20번](../20-enum-and-flags/)과 같다.
> ★ **대비** — Java 에는 튜플이 없다 — Java 갈래 목록([`java/syntax/README.md`](../../../java/syntax/README.md))의 **14번**([`14-records/`](../../../java/syntax/14-records/))이 「여러 값 반환」의 자리를 **record** 로 채운다(이 판에서 Java 는 안 던졌다).
>
> ★★ **흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | 진단 **문구** · 예외 **메시지** | ★★★ **진단 코드**(`CS8123`·`CS1612`·`CS1061`)와 **`(행,열)`** · **예외 타입**(`RuntimeBinderException`·`MissingMethodException`) |
> | **IL 오프셋 폭** | ★★★ **옵코드와 부른 멤버**(`ldfld Item1` · `bne.un.s` · `call String::op_Equality`) |
> | 증분의 절댓값 일부(규칙 24) · JSON 직렬화기의 **기본 설정** | ★★★ **리플렉션이 보여 주는 이름**(`Item1`·`Item2` · `TransformNames`) · **네 판에서 갈린 줄 수** |

## 이 판

```text
===== dotnet --version && dotnet --list-runtimes | grep NETCore (exit=0) =====
10.0.401
Microsoft.NETCore.App 10.0.12 [/home/jun/.local/opt/dotnet/shared/Microsoft.NETCore.App]
===== javac -version (exit=0) =====
javac 21.0.5
```

## 이 갈래가 쓰는 세 층

| 층 | 뜻 | 이 주제에서 근거로 쓰는 것 |
|---|---|---|
| **언어 명세(ECMA-334)** | C# 언어가 약속한 것 | ★★★ **튜플 = `System.ValueTuple<…>`** · 원소 이름은 **컴파일 시점에만** · 대입·`==` 는 **이름을 안 본다** · `==` 는 **원소별 `==`** · 해체는 **`Deconstruct` 를 찾는다**(확장 메서드 포함) |
| **런타임·BCL** | `ValueTuple` 구조체와 `TupleElementNamesAttribute` | ★★★ 필드가 **`Item1`·`Item2`·…·`Rest`** 인 **가변 구조체** · `Equals` 가 **원소의 `Equals`** 를 부르는 것 |
| **이 판의 관찰** | .NET 10.0.12 · linux-x64 | 할당 바이트 · `System.Text.Json` 의 기본 동작(`{}`) · 예외 메시지 |

★★★ **이 주제에서 가장 조심할 칸은 「튜플 이름은 어디에 사는가」다** —\
**값(인스턴스)에는 없고**, 메서드 **반환값·매개변수에 붙은 특성**(`TupleElementNamesAttribute`)에만 있다((1)).\
그래서 **컴파일러는 다른 어셈블리에서도 이름을 보지만**, 값을 **`object`·`dynamic`·직렬화기**에 넘기는 순간 이름이 없다((6)(7)).

## 한눈에 — 쉽게 말하면

**튜플은 이름표를 포장지에만 붙인 상자다 — 상자 안의 칸 이름은 언제나 1번 칸·2번 칸이다.**

택배 상자를 생각하자.

- **`(int Id, string Name)`** — 상자 **겉**에 「1번 칸 = Id, 2번 칸 = Name」이라고 적은 **송장**. 상자 **안**의 칸은 그냥 **1번·2번**(`Item1`·`Item2`)이다.
- **컴파일러** — 송장을 읽는 **택배 기사**. 송장이 붙은 채로 오면(메서드 반환형) **다른 회사(어셈블리)에서 와도** 이름으로 부른다.
- **`dynamic`·`object`·JSON** — 송장을 **떼고** 상자만 받는 창고. 칸 이름이 1번·2번뿐이라 **`Id` 를 찾으면 없다.**
- **`record`** — 칸 **자체에 이름을 새긴** 상자. 송장이 없어도 이름이 보이고, 이름을 바꾸면 **옛 주소로는 못 찾는다**(바이너리 계약).
- **해체 `var (a, b) = x`** — 상자를 열어 칸을 **변수로 꺼내는** 것. 상자가 튜플이 아니어도 **`Deconstruct` 라는 여는 법**만 있으면 된다.

| 비유 | 실체 | 어디서 보나 |
|---|---|---|
| 칸은 늘 1번·2번 | ★★★ **리플렉션 필드가 `Item1`·`Item2`** · **`Id`·`Name` 은 반환값 특성에만** | (1) |
| 송장만 다른 두 상자는 같다 | ★★★ **`(Id, Name)` 과 `(Key, Label)` 이 `==` 로 `True`** | (2) |
| 칸마다 따로 비교 | ★★★ **`==` 가 `ldfld Item1` 비교 → `ldfld Item2` 를 `String::op_Equality`** | (2) |
| 여는 법만 있으면 된다 | ★★★ **`Version` 에 확장 `Deconstruct` 를 달면 `var (major, minor) = v`** | (3) |
| 송장을 떼면 이름이 없다 | ★★★ **`dynamic` 은 `RuntimeBinderException` · JSON 은 `{}`** | (6)(7) |
| 칸에 새긴 이름 | ★★★ **record 이름을 바꾸면 옛 앱이 `MissingMethodException`** | (6) |

★★★ **이 주제의 본체 그림 — 이름이 사는 곳.**

```text
   소스                                 메타데이터(어셈블리)                                 런타임 값
   ─────────────────────────           ──────────────────────────────────────────          ─────────────────────
   (int Id, string Name) Find()   →    반환형 ValueTuple`2<Int32,String>                →   Item1 = 1
                                       + [TupleElementNames("Id","Name")] ← 반환값에         Item2 = "kim"
                                                                                           (Id·Name 은 어디에도 없다)
   t.Id                           →    ldfld Item1                     ← 컴파일러가 바꿔 쓴다

   record User(int Id, string Name) →  속성 get_Id · get_Name · 필드 <Id>k__BackingField   →   Id = 1, Name = "kim"
   u.Id                           →    callvirt User::get_Id           ← 이름 자체가 호출 대상

   ★★★ 튜플 이름은 「컴파일러에게 주는 쪽지」, record 이름은 「런타임이 찾는 주소」 다.
```

## 이 주제가 답하려는 질문

1. **튜플은 런타임에 무엇인가** — 이름은 어디에 사나((1)).
2. **`==` 는 무엇을 비교하나** — 이름이 다르면, 원소가 클래스면((2)).
3. **해체는 무엇을 부르나** — 튜플이 아닌 타입을 해체하려면((3)).
4. **가변 구조체라서 생기는 일은**((4)) · **8개가 넘으면**((5)).
5. **언제 `record` 로 올려야 하나** — 어셈블리 경계·직렬화·할당((6)(7)(8)(9)).

## 동작 방식

### (0) 이 주제가 쓰는 창

★★★ **본체 창은 ③ 리플렉션이다** — 「이름은 컴파일 시점에만 있다」는 **런타임 타입을 찍어 `Item1`·`Item2` 만 나오는 것**으로만 증명된다.

| 창 | 무엇을 보여 주나 | 이 주제에서 |
|---|---|---|
| ★★★ **③ 리플렉션** | ★★★ 필드 **`Item1`·`Item2`**(`IsInitOnly=False`) · 속성 **0개** · 반환값의 **`TupleElementNamesAttribute`** · 9원소의 **`Rest` 중첩** | (1)(5) |
| ★★ **실행 출력(어셈블리 둘 · `dynamic` · JSON)** | ★★★ **제5의 상태** — 「이름이 경계를 넘나」는 리플렉션으로 **값을 찍어서는 못 본다**(값에 원래 없다). **다른 어셈블리의 컴파일러·`dynamic`·직렬화기에게 이름을 불러 보게** 해서 물었다. ★ 이 창이 못 보는 것 — **리플렉션 기반의 다른 도구**(ORM 등)는 안 던졌다 | (6)(7) |
| ★★ **① IL 덤프** | `==` 가 **`ldfld Item1` · `bne.un.s` · `ldfld Item2` · `call String::op_Equality`** 로 풀린다 | (2) |
| ★★ **② 진단** | `CS8123`(이름이 무시됨) · `CS1612`(인덱서가 돌려준 튜플 수정) · `CS1061`(이름이 바뀐 뒤 다시 컴파일) | (2)(4)(6) |
| ★★ **④ 할당 바이트** | ★★ 값 튜플·`record struct` **0** 대 `Tuple<>`·`record class` **24000** — 2×2 판 격자 | (8) |

### (1) ★★★ 튜플의 실체 — `ValueTuple` 가변 구조체, 이름은 특성에만

**언제 쓰나** — 「튜플 이름을 리플렉션·로그·직렬화에서 볼 수 있나」를 물을 때.

```text
===== 소스: cs23b-refl.cs =====
using System;
using System.Reflection;
using System.Runtime.CompilerServices;
public static class Api {
    public static (int Id, string Name) Find() => (1, "kim");
}
class Program {
    static void Main() {
        var t = Api.Find();
        Type vt = t.GetType();
        Console.WriteLine($"[1] 타입        : {vt}");
        Console.WriteLine($"[2] IsValueType : {vt.IsValueType}");
        foreach (var f in vt.GetFields())
            Console.WriteLine($"[3] 필드        : {f.Name} ({f.FieldType.Name}) IsInitOnly={f.IsInitOnly}");
        Console.WriteLine($"[4] 속성 수     : {vt.GetProperties().Length}");
        var attr = typeof(Api).GetMethod("Find")!.ReturnParameter.GetCustomAttribute<TupleElementNamesAttribute>();
        Console.WriteLine($"[5] 반환값 특성 : {(attr is null ? "없음" : string.Join(",", attr.TransformNames))}");
        Type rt = Tuple.Create(1, "kim").GetType();
        Console.WriteLine($"[6] Tuple.Create: {rt} IsValueType={rt.IsValueType} 필드 {rt.GetFields().Length} · 속성 {rt.GetProperties().Length}");
        var big = (1, 2, 3, 4, 5, 6, 7, 8, 9);
        Console.WriteLine($"[7] 원소 9개    : {big.GetType()}");
        Console.WriteLine($"[8] big.Item9 = {big.Item9} · big.Rest.Item2 = {big.Rest.Item2} · big.Rest = {big.Rest}");
    }
}
===== csc -nullable:enable -out:ex.dll cs23b-refl.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
[1] 타입        : System.ValueTuple`2[System.Int32,System.String]
[2] IsValueType : True
[3] 필드        : Item1 (Int32) IsInitOnly=False
[3] 필드        : Item2 (String) IsInitOnly=False
[4] 속성 수     : 0
[5] 반환값 특성 : Id,Name
[6] Tuple.Create: System.Tuple`2[System.Int32,System.String] IsValueType=False 필드 0 · 속성 2
[7] 원소 9개    : System.ValueTuple`8[System.Int32,System.Int32,System.Int32,System.Int32,System.Int32,System.Int32,System.Int32,System.ValueTuple`2[System.Int32,System.Int32]]
[8] big.Item9 = 9 · big.Rest.Item2 = 9 · big.Rest = (8, 9)
```

- ★★★ **`[1]` 런타임 타입은 ``System.ValueTuple`2[Int32,String]``** · **`[2]` 값 타입**이다.
- ★★★ **`[3]` 필드 이름이 `Item1`·`Item2`** — 소스의 `Id`·`Name` 은 **어디에도 없다.** Learn — 「컴파일 때 기본 이름으로 바꾼다」.
- ★★★ **`IsInitOnly=False`** — `readonly` 가 아니다. **가변 구조체**다((4)).
- ★★ **`[4]` 속성 0개** — 원소는 **필드**다. 속성만 보는 도구(직렬화기 등)는 **아무것도 못 본다**((7)).
- ★★★ **`[5]` `Find()` 의 반환값에 `TupleElementNamesAttribute` 가 붙어 `Id,Name`** — **이름이 사는 유일한 곳**이다. 값이 아니라 **메서드 서명**에 붙는다.
- ★★ **`[6]` `Tuple.Create` 는 ``System.Tuple`2`` — 참조 타입 · 필드 0 · 속성 2**(`Item1`·`Item2`). 옛 `Tuple` 은 **불변 클래스**, 새 `ValueTuple` 은 **가변 구조체**다(Learn 의 대비표 그대로).

> **어느 층인가** — ★★★ 「이름은 런타임에 없다」는 **언어**(Learn 이 명시). 「반환값에 특성으로 남긴다」는 **컴파일러와 BCL 의 약속**(`TupleElementNamesAttribute`)이다.\
> ★ 그래서 **다른 어셈블리의 컴파일러**는 이름을 되살린다 — (6)에서 확인한다.

### (2) ★★★ `==` 는 원소별 `==` — 이름은 안 본다

```text
===== 소스: cs23b-eq.cs =====
using System;
class Money {
    public int Won;
    public Money(int w) => Won = w;
    public override bool Equals(object? o) => o is Money m && m.Won == Won;   // == 는 그대로 둔다
    public override int GetHashCode() => Won;
}
public static class Probe {
    public static bool Eq((int, string) a, (int, string) b) => a == b;
}
class Program {
    static void Main() {
        var a = (Id: 1, Name: "kim");
        (int Key, string Label) b = (1, "kim");
        Console.WriteLine($"[1] a == b       : {a == b}");
        Console.WriteLine($"[2] a.Equals(b)  : {a.Equals(b)}");
        var m1 = (new Money(100), 1);
        var m2 = (new Money(100), 1);
        Console.WriteLine($"[3] m1 == m2     : {m1 == m2}");
        Console.WriteLine($"[4] m1.Equals(m2): {m1.Equals(m2)}");
        Il.Dump(typeof(Probe), "Eq");
    }
}
===== csc -nullable:enable -r:il.dll -out:ex.dll cs23b-eq.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
[1] a == b       : True
[2] a.Equals(b)  : True
[3] m1 == m2     : False
[4] m1.Equals(m2): True
--- Probe.Eq ---
  .locals [0] System.ValueTuple<System.Int32,System.String>
  .locals [1] System.ValueTuple<System.Int32,System.String>
  IL_0000: ldarg.0
  IL_0001: stloc.0
  IL_0002: ldarg.1
  IL_0003: stloc.1
  IL_0004: ldloc.0
  IL_0005: ldfld System.ValueTuple<System.Int32,System.String>::Item1
  IL_000a: ldloc.1
  IL_000b: ldfld System.ValueTuple<System.Int32,System.String>::Item1
  IL_0010: bne.un.s IL_0025
  IL_0012: ldloc.0
  IL_0013: ldfld System.ValueTuple<System.Int32,System.String>::Item2
  IL_0018: ldloc.1
  IL_0019: ldfld System.ValueTuple<System.Int32,System.String>::Item2
  IL_001e: call System.String::op_Equality
  IL_0023: br.s IL_0026
  IL_0025: ldc.i4.0
  IL_0026: ret
===== 소스: cs23b-names.cs =====
class Program {
    static void Main() {
        (int Id, string Name) t = (Key: 1, Label: "kim");     // 이름이 다른 튜플 리터럴을 대입
        var s = (Id: 1, Name: "kim");
        System.Console.WriteLine(t.Id + s.Id);
    }
}
===== csc -out:ex.dll cs23b-names.cs 2>&1 | sort (cc exit=0) =====
cs23b-names.cs(3,36): warning CS8123: The tuple element name 'Key' is ignored because a different name or no name is specified by the target type '(int Id, string Name)'.
cs23b-names.cs(3,44): warning CS8123: The tuple element name 'Label' is ignored because a different name or no name is specified by the target type '(int Id, string Name)'.
```

- ★★★ **`[1]` `(Id, Name)` 과 `(Key, Label)` 이 `==` 로 `True`** — 이름은 비교에 **아무 역할이 없다.** 타입(원소 개수와 각 타입)만 맞으면 된다.
- ★★★ **IL `Probe.Eq`** — `ldfld Item1` 둘 → **`bne.un.s`**(다르면 바로 `false`), `ldfld Item2` 둘 → **`call System.String::op_Equality`**.\
  **원소마다 그 타입의 `==`** 를 부른다. `ValueTuple` 에 `==` 가 정의된 것이 아니라 **컴파일러가 풀어 쓴** 것이다.
- ★★★ **`[3]` `(Money, int)` 둘이 `==` 로 `False`, `[4]` `Equals` 로 `True`** — [19번](../19-equality-equals-gethashcode-operator/) (3)의 **「`Equals` 만 고친 클래스의 `==` 는 참조 비교」** 가 튜플 안에서 그대로 나왔다.\
  `==` 는 원소의 `==`(참조 비교)를, `ValueTuple.Equals` 는 원소의 **`Equals`**(값 비교)를 부른다. **같은 두 튜플이 두 비교에서 갈린다.**
- ★★ **둘째 소스 — `(int Id, string Name) t = (Key: 1, Label: "kim")` 는 `CS8123` 경고 둘** — 「이름 `Key` 는 **무시된다**」. 에러가 아니다 — **대입도 이름을 안 본다**(Learn).

```text
   t1 == t2   (int, string)                         t1.Equals(t2)
   ──────────────────────────                        ─────────────────────────────────
   t1.Item1 == t2.Item1 ?   (bne.un.s)               EqualityComparer<int>.Default.Equals(…)
   t1.Item2 == t2.Item2 ?   (String::op_Equality)    EqualityComparer<string>.Default.Equals(…)
   ★ 원소 타입의 「==」                                ★ 원소 타입의 「Equals」

   원소가 Money(== 없음, Equals 만 고침)면  ==  → False   Equals → True
```

- ★ Learn — 「`==` 는 단락하지만 **비교 전에 모든 원소를 평가**한다」. **이 판에서 부작용 순서는 안 찍었다.**

### (3) ★★★ 해체 — `Deconstruct` 라는 이름만 있으면 된다

**언제 쓰나** — 튜플을 돌려받아 **바로 변수 여럿으로** 쓸 때 · **내 타입·남의 타입**을 `var (a, b) = x` 로 열고 싶을 때.

```text
===== 소스: cs23b-decon.cs =====
using System;
static class VersionExt {
    public static void Deconstruct(this Version v, out int major, out int minor) { major = v.Major; minor = v.Minor; }
}
class Pt {
    public int X, Y;
    public Pt(int x, int y) { X = x; Y = y; }
    public void Deconstruct(out int x, out int y) { Console.WriteLine("    Pt.Deconstruct 불림"); x = X; y = Y; }
}
record Person(string Name, int Age);
class Program {
    static (int Min, int Max) MinMax(int[] xs) => (Math.Min(xs[0], xs[^1]), Math.Max(xs[0], xs[^1]));
    static void Main() {
        var (lo, hi) = MinMax(new[] { 7, 3 });
        Console.WriteLine($"[1] lo={lo} hi={hi}");
        var (major, minor) = new Version(10, 2);
        Console.WriteLine($"[2] major={major} minor={minor}");
        var (x, _) = new Pt(4, 5);
        Console.WriteLine($"[3] x={x}");
        var (name, age) = new Person("kim", 30);
        Console.WriteLine($"[4] name={name} age={age}");
        int a = 1, b = 2;
        (a, b) = (b, a);
        Console.WriteLine($"[5] a={a} b={b}");
        Console.WriteLine($"[6] {(new Pt(0, 3) is (0, var y) ? $"y={y}" : "아님")}");
    }
}
===== csc -out:ex.dll cs23b-decon.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
[1] lo=3 hi=7
[2] major=10 minor=2
    Pt.Deconstruct 불림
[3] x=4
[4] name=kim age=30
[5] a=2 b=1
    Pt.Deconstruct 불림
[6] y=3
```

- ★★★ **`[1]` 튜플 반환을 바로 해체** — 값 튜플은 **해체를 언어가 직접** 안다.
- ★★★ **`[2]` `System.Version` 을 해체** — BCL 타입인데 **확장 메서드 `Deconstruct(this Version, out int, out int)`** 하나로 열렸다. **인터페이스도 상속도 필요 없다** — 이름과 `out` 매개변수 모양만 맞으면 된다.
- ★★ **`[3]` 내 클래스의 `Deconstruct`** — 로그 `Pt.Deconstruct 불림` 이 **해체가 그 메서드를 부른다**는 증거다. **`_` 로 버린 원소도** 호출 자체는 일어난다.
- ★★ **`[4]` record 는 `Deconstruct` 를 생성해 준다**([18번](../18-record-value-equality-and-with/) (1)).
- ★★ **`[5]` `(a, b) = (b, a)`** — 임시 변수 없는 교환.
- ★★ **`[6]` 위치 패턴 `(0, var y)` 도 `Deconstruct` 를 부른다**(로그 한 줄) — [21번](../21-pattern-matching-type-property-relational-list/) (4)의 그것이다.

> **어느 층인가** — ★★★ 「해체는 **`Deconstruct` 이름의 인스턴스·확장 메서드**를 찾는다」는 **언어(334)** 다. **패턴 기반**이라 [14번](../14-indexers/)의 패턴 기반 인덱싱과 같은 설계 철학이다.

### (4) ★★ 가변 구조체라서 — 인덱서가 돌려준 튜플은 못 고친다

```text
===== 소스: cs23b-mut.cs =====
using System.Collections.Generic;
class Program {
    static void Main() {
        var arr  = new[] { (Id: 1, Name: "kim") };
        var list = new List<(int Id, string Name)> { (1, "kim") };
        var dict = new Dictionary<string, (int Id, string Name)> { ["k"] = (1, "kim") };
        arr[0].Id = 9;                // 배열 원소
        list[0].Id = 9;               // List 인덱서가 돌려준 값
        dict["k"].Id = 9;             // Dictionary 인덱서가 돌려준 값
    }
}
===== csc -out:ex.dll cs23b-mut.cs 2>&1 | sort (cc exit=1) =====
cs23b-mut.cs(8,9): error CS1612: Cannot modify the return value of 'List<(int Id, string Name)>.this[int]' because it is not a variable
cs23b-mut.cs(9,9): error CS1612: Cannot modify the return value of 'Dictionary<string, (int Id, string Name)>.this[string]' because it is not a variable
===== 소스: cs23b-mut2.cs =====
using System;
using System.Collections.Generic;
class Program {
    static void Main() {
        var arr  = new[] { (Id: 1, Name: "kim") };
        var list = new List<(int Id, string Name)> { (1, "kim") };
        arr[0].Id = 9;
        var copy = list[0];
        copy.Id = 9;
        Console.WriteLine($"[1] arr[0]  = {arr[0]}");
        Console.WriteLine($"[2] list[0] = {list[0]} · copy = {copy}");
    }
}
===== csc -out:ex.dll cs23b-mut2.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
[1] arr[0]  = (9, kim)
[2] list[0] = (1, kim) · copy = (9, kim)
```

- ★★★ **`list[0].Id = 9` · `dict["k"].Id = 9` 는 `CS1612`** — 「인덱서의 **반환값**은 변수가 아니다」. 인덱서는 **튜플의 복사본**을 돌려주므로 고쳐 봐야 **버려진다** — 컴파일러가 그것을 막았다.
- ★★ **배열 `arr[0].Id = 9` 는 된다**(첫 소스 7행에 진단 없음) — 배열 원소는 **변수 자리 그 자체**다.
- ★★★ **복사본을 받아 고치면 원본은 그대로** — `[2]` `list[0]` 은 `(1, kim)`, `copy` 는 `(9, kim)`.

```text
   arr[0].Id = 9        → 배열 칸 안의 구조체를 직접 고친다          ○
   list[0].Id = 9       → get_Item 이 돌려준 「복사본」 을 고친다      ✕ CS1612
   var c = list[0]; c.Id = 9 → 복사본만 바뀐다                        ○ (원본 그대로)

   ★ 01·02번의 「값 타입은 복사된다」 가 가변 구조체에서 가장 날카롭게 드러나는 자리다.
```

### (5) ★ 원소가 8개를 넘으면 — `Rest` 로 중첩된다

- ★★ **(1) `[7]` 원소 9개 튜플의 런타임 타입은 ``ValueTuple`8[Int32 ×7, ValueTuple`2[Int32,Int32]]``** — 8번째 칸 **`Rest`** 에 나머지가 **튜플로** 들어간다.
- ★★ **`[8]` `big.Item9` 는 `big.Rest.Item2` 와 같다** — `Item9` 는 **컴파일러가 `Rest.Item2` 로 바꿔 쓰는 이름**이다. `big.Rest` 는 `(8, 9)`.
- ★ 그래서 리플렉션으로 `Item9` 를 찾으면 **없다**(필드는 `Item1`\~`Item7`·`Rest`) — 이름 문제와 같은 뿌리다(이 판에서 `GetField("Item9")` 는 안 찍었다).

### (6) ★★★ 어셈블리 둘 — 이름은 넘어가고, 바꿔도 옛 앱은 모른다

**언제 쓰나** — **공개 API 가 튜플을 돌려줄 때** — 「이름이 다른 어셈블리에서 사라지나」.

```text
===== 소스: cs23b-lib1.cs =====
using System.Collections.Generic;
public record User(int Id, string Name);
public static class Repo {
    public static (int Id, string Name) Find() => (1, "kim");
    public static List<(int Id, string Name)> All() => new() { (1, "kim"), (2, "lee") };
    public static User FindUser() => new(1, "kim");
}
===== 소스: cs23b-app.cs =====
using System;
class Program {
    static void Main() {
        var t = Repo.Find();
        Console.WriteLine($"[1] t.Id={t.Id} t.Name={t.Name}");
        foreach (var r in Repo.All()) Console.WriteLine($"[2] r.Id={r.Id}");
        try { dynamic d = Repo.Find(); Console.WriteLine($"[3] d.Id={d.Id}"); }
        catch (Exception e) { Console.WriteLine($"[3] {e.GetType().Name} : {e.Message}"); }
        try { Console.WriteLine($"[4] user.Id={ReadUser()}"); }
        catch (Exception e) { Console.WriteLine($"[4] {e.GetType().Name} : {e.Message}"); }
    }
    static int ReadUser() => Repo.FindUser().Id;
}
===== csc -target:library -out:Repo.dll cs23b-lib1.cs && csc -r:Repo.dll -out:app.dll cs23b-app.cs && dotnet app.dll (cc exit=0 · run exit=0) =====
[1] t.Id=1 t.Name=kim
[2] r.Id=1
[2] r.Id=2
[3] RuntimeBinderException : 'System.ValueTuple<int,string>' does not contain a definition for 'Id'
[4] user.Id=1
===== 소스: cs23b-lib2.cs =====
using System.Collections.Generic;
public record User(int Key, string Label);                 // 이름만 바꿨다
public static class Repo {
    public static (int Key, string Label) Find() => (1, "kim");                     // 이름만 바꿨다
    public static List<(int Key, string Label)> All() => new() { (1, "kim"), (2, "lee") };
    public static User FindUser() => new(1, "kim");
}
===== csc -target:library -out:Repo.dll cs23b-lib2.cs && dotnet app.dll    # app.dll 은 다시 컴파일하지 않았다 (cc exit=0 · run exit=0) =====
[1] t.Id=1 t.Name=kim
[2] r.Id=1
[2] r.Id=2
[3] RuntimeBinderException : 'System.ValueTuple<int,string>' does not contain a definition for 'Id'
[4] MissingMethodException : Method not found: 'Int32 User.get_Id()'.
===== csc -r:Repo.dll -out:app2.dll cs23b-app.cs 2>&1 | sort (cc exit=1) =====
cs23b-app.cs(12,46): error CS1061: 'User' does not contain a definition for 'Id' and no accessible extension method 'Id' accepting a first argument of type 'User' could be found (are you missing a using directive or an assembly reference?)
cs23b-app.cs(5,41): error CS1061: '(int Key, string Label)' does not contain a definition for 'Id' and no accessible extension method 'Id' accepting a first argument of type '(int Key, string Label)' could be found (are you missing a using directive or an assembly reference?)
cs23b-app.cs(5,55): error CS1061: '(int Key, string Label)' does not contain a definition for 'Name' and no accessible extension method 'Name' accepting a first argument of type '(int Key, string Label)' could be found (are you missing a using directive or an assembly reference?)
cs23b-app.cs(6,71): error CS1061: '(int Key, string Label)' does not contain a definition for 'Id' and no accessible extension method 'Id' accepting a first argument of type '(int Key, string Label)' could be found (are you missing a using directive or an assembly reference?)
```

- ★★★ **첫 판 — 다른 어셈블리의 앱이 `t.Id`·`r.Id` 로 불렀다** — `List<(int Id, string Name)>` 안의 이름까지. **컴파일러는 반환값 특성을 읽어 이름을 되살린다.**\
  ★★ **「튜플을 공개 API 로 쓰면 다른 어셈블리에서 이름이 사라진다」는 이 판에서 거짓이었다**(컴파일러가 보는 한).
- ★★★ **`[3]` `dynamic` 은 `RuntimeBinderException`**(「`ValueTuple<int,string>` 에 `Id` 가 없다」) — **런타임 바인더는 특성을 안 본다.** 값에는 `Item1` 뿐이다.
- ★★★ **라이브러리만 바꿔 끼우면**(이름 `Id`→`Key`, 앱은 다시 컴파일 안 함) — **튜플 쪽 `[1]`·`[2]` 는 그대로 돈다.** 앱의 IL 에는 **`Item1`** 만 박혀 있어서다. **이름 변경이 바이너리 호환**이다.
- ★★★ **record 쪽 `[4]` 는 `MissingMethodException`**(「`User.get_Id()` 가 없다」) — **record 의 이름은 호출 대상 자체**라 바꾸면 옛 앱이 깨진다.
- ★★ **같은 앱을 새 라이브러리로 다시 컴파일하면 `CS1061` 넷** — 튜플도 record 도 **소스 호환은 깨진다.**

| 라이브러리가 이름만 바꾸면 | 튜플 `(int Id, …)` | `record User(int Id, …)` |
|---|---|---|
| 다시 컴파일 **안 한** 앱 | ★★★ **그대로 돈다**(`Item1` 만 박혔다) | ★★★ **`MissingMethodException`** |
| 다시 컴파일한 앱 | `CS1061` | `CS1061` |
| `dynamic` 으로 이름 접근 | ★★ **처음부터 실패** — `RuntimeBinderException` | (안 던졌다) |

- ★★ **뜻** — 튜플 이름은 **「주석에 가까운 계약」** 이다. 바꿔도 아무도 모르게 **조용히 뜻이 바뀔 수 있다**(`Id` 와 `Key` 의 **의미가 달라져도** 옛 앱은 그대로 `Item1` 을 읽는다).\
  record 는 **바꾸면 시끄럽게 깨진다.** 어느 쪽이 나은지는 **계약을 얼마나 오래 지켜야 하나**에 달렸다((9)).

### (7) ★★★ 직렬화·`ToString` — 이름이 없는 곳

```text
===== 소스: cs23b-json.cs =====
using System;
using System.Text.Json;
record User(int Id, string Name);
class Program {
    static void Main() {
        (int Id, string Name) t = (1, "kim");
        var u = new User(1, "kim");
        Console.WriteLine($"[1] 튜플 ToString   : {t}");
        Console.WriteLine($"[2] record ToString : {u}");
        Console.WriteLine($"[3] 튜플 JSON       : {JsonSerializer.Serialize(t)}");
        Console.WriteLine($"[4] record JSON     : {JsonSerializer.Serialize(u)}");
        Console.WriteLine($"[5] 튜플 JSON(필드 포함) : {JsonSerializer.Serialize(t, new JsonSerializerOptions { IncludeFields = true })}");
        object o = t;
        Console.WriteLine($"[6] object 로 올린 뒤 : {o.GetType().GetField("Item1")?.GetValue(o)} · Id 필드 {(o.GetType().GetField("Id") is null ? "없음" : "있음")}");
    }
}
===== csc -out:ex.dll cs23b-json.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
[1] 튜플 ToString   : (1, kim)
[2] record ToString : User { Id = 1, Name = kim }
[3] 튜플 JSON       : {}
[4] record JSON     : {"Id":1,"Name":"kim"}
[5] 튜플 JSON(필드 포함) : {"Item1":1,"Item2":"kim"}
[6] object 로 올린 뒤 : 1 · Id 필드 없음
```

- ★★★ **`[3]` 튜플을 `System.Text.Json` 으로 직렬화하면 `{}`** — 빈 객체다. 이 직렬화기는 **기본으로 공개 속성만** 본다((1) `[4]` 속성 0개). **에러도 경고도 없다.**
- ★★ **`[5]` `IncludeFields = true` 로 켜도 `{"Item1":1,"Item2":"kim"}`** — **이름은 끝내 안 나온다.**
- ★★★ **`[4]` record 는 `{"Id":1,"Name":"kim"}`** · **`[2]` `ToString` 도 `User { Id = 1, Name = kim }`** — 튜플 `[1]` 은 `(1, kim)`.
- ★★ **`[6]` `object` 로 올린 뒤 리플렉션** — `Item1` 은 있고 **`Id` 필드는 없다.**
- ★★★ **이것이 「튜플을 공개 API 에 쓰지 마라」의 실제 이유다** — 다른 **컴파일러**는 이름을 보지만, **런타임에 이름을 찾는 모든 것**(직렬화·로그·`dynamic`·바인딩)은 못 본다.

### (8) ★★ 할당 — 값 튜플은 0, `Tuple<>` 은 힙 · 2×2 판 격자

```text
===== 소스: cs23b-alloc.cs =====
using System;
record class RC(int A, int B);
record struct RS(int A, int B);
class Program {
    static (int A, int B) VT(int i)          => (i, i + 1);
    static Tuple<int, int> T(int i)          => Tuple.Create(i, i + 1);
    static RC C(int i)                       => new(i, i + 1);
    static RS S(int i)                       => new(i, i + 1);
    static long M(Action a) {
        for (int i = 0; i < 200; i++) a();
        var b = GC.GetAllocatedBytesForCurrentThread();
        a();
        return GC.GetAllocatedBytesForCurrentThread() - b;
    }
    static void Main() {
        long sink = 0;
        Console.WriteLine($"[1] (int, int) 값 튜플     1000번 : {M(() => { for (int i = 0; i < 1000; i++) sink += VT(i).B; })} 바이트");
        Console.WriteLine($"[2] Tuple<int, int>       1000번 : {M(() => { for (int i = 0; i < 1000; i++) sink += T(i).Item2; })} 바이트");
        Console.WriteLine($"[3] record class          1000번 : {M(() => { for (int i = 0; i < 1000; i++) sink += C(i).B; })} 바이트");
        Console.WriteLine($"[4] record struct         1000번 : {M(() => { for (int i = 0; i < 1000; i++) sink += S(i).B; })} 바이트");
        GC.KeepAlive(sink);
    }
}
===== csc -out:ex.dll cs23b-alloc.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
[1] (int, int) 값 튜플     1000번 : 0 바이트
[2] Tuple<int, int>       1000번 : 24000 바이트
[3] record class          1000번 : 24000 바이트
[4] record struct         1000번 : 0 바이트
===== csc -out:ex.dll cs23b-alloc.cs && DOTNET_TieredCompilation=0 dotnet ex.dll (cc exit=0 · run exit=0) =====
[1] (int, int) 값 튜플     1000번 : 0 바이트
[2] Tuple<int, int>       1000번 : 24000 바이트
[3] record class          1000번 : 24000 바이트
[4] record struct         1000번 : 0 바이트
===== csc -optimize -out:exo.dll cs23b-alloc.cs && dotnet exo.dll (cc exit=0 · run exit=0) =====
[1] (int, int) 값 튜플     1000번 : 0 바이트
[2] Tuple<int, int>       1000번 : 24000 바이트
[3] record class          1000번 : 24000 바이트
[4] record struct         1000번 : 0 바이트
===== csc -optimize -out:exo.dll cs23b-alloc.cs && DOTNET_TieredCompilation=0 dotnet exo.dll (cc exit=0 · run exit=0) =====
[1] (int, int) 값 튜플     1000번 : 0 바이트
[2] Tuple<int, int>       1000번 : 24000 바이트
[3] record class          1000번 : 24000 바이트
[4] record struct         1000번 : 0 바이트
===== 네 판 대조 — 「바이트」 줄마다 네 판의 값이 같은가 =====
네 판에서 갈린 줄 0 / 4
```

- ★★★ **네 판에서 갈린 줄 0 / 4.**
- ★★★ **값 튜플 `(int, int)` 과 `record struct` 는 0**, **`Tuple<int, int>` 와 `record class` 는 1000번에 24000** — 둘 다 참조 타입이라 힙에 간다.
- ★★ **「튜플이 가볍다」의 실체는 「값 타입이라 힙에 안 간다」** 다. **`record struct` 도 똑같이 0** 이므로, **가벼움 때문에 튜플을 고를 이유는 없다** — 이름과 계약이 필요하면 `record struct` 가 같은 값을 낸다.
- ★ **시간은 안 쟀다.**

### (9) ★★★ 언제 `record` 로 올리나 — 판단표

| 상황 | 튜플 | `record`(`struct`/`class`) | 근거 |
|---|---|---|---|
| **메서드 안·private 도우미의 여러 값 반환** | ★★★ **튜플** — 해체가 바로 된다 | 과하다 | (3) |
| **공개 API 반환** | ✕ 이름이 **특성에만** — 런타임 도구가 못 본다 | ★★★ **record** | (6)(7) |
| **직렬화·로그·`dynamic`·바인딩에 넘김** | ✕ `{}` · `(1, kim)` · `RuntimeBinderException` | ★★★ **record** | (7) |
| **이름을 바꿀 수 있어야 함(버전 관리)** | ★ 바꿔도 옛 앱은 **조용히** 돈다 — **뜻이 조용히 바뀔 위험** | ★★ 바꾸면 **시끄럽게** 깨진다 | (6) |
| **값 비교가 원소의 `Equals` 를 따라야 함** | ★ `==` 와 `Equals` 가 **갈릴 수 있다** | ★★ `==` 가 `Equals` 를 부르게 생성된다([18번](../18-record-value-equality-and-with/)) | (2) |
| **컬렉션 안에서 고쳐 쓰기** | ✕ `CS1612` · 복사본 | ★ `record class` 면 참조라 고쳐진다(불변이 기본이지만) | (4) |
| **할당이 문제** | 0 | ★★★ **`record struct` 도 0** | (8) |
| **원소가 여럿(대략 4 이상)이거나 뜻이 중요** | ✕ `Item5`·`Rest` 가 보인다 | ★★★ **record** | (5) |

- ★★★ **요약 — 튜플은 「한 메서드 안에서 잠깐 묶는 것」, record 는 「이름이 계약인 것」.** Learn 도 「공개 API 에서는 클래스나 구조체를 고려하라」·「타입 안전이 필요하면 위치 record」라고 적었다.

## 문법 — 형태와 규칙

### 형태

```text
===== 소스: cs23b-form.cs =====
using System;
using System.Linq;

var (count, avg) = Stats(new[] { 3, 5, 10 });                  // 반환 → 바로 해체
Console.WriteLine($"{count}개 평균 {avg}");

var pairs = new[] { ("kim", 30), ("lee", 25) };
foreach (var (name, age) in pairs.OrderBy(p => p.Item2))       // foreach 에서 해체
    Console.WriteLine($"{name} {age}");

var point = (X: 3, Y: 4);
Console.WriteLine(point switch { (0, 0) => "원점", (var x, 0) => $"x축 {x}", _ => $"{point}" });

static (int Count, double Average) Stats(int[] xs) => (xs.Length, xs.Average());
===== csc -out:ex.dll cs23b-form.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
3개 평균 6
lee 25
kim 30
(3, 4)
```

- ★★★ **반환형에 이름을 달고**(`(int Count, double Average)`), 받는 쪽은 **바로 해체**한다.
- ★★ **`foreach (var (name, age) in …)`** — 원소가 튜플이면 **반복 변수에서 해체**된다.
- ★★ **튜플에도 위치 패턴이 붙는다** — `(0, 0) =>` · `(var x, 0) =>`([21번](../21-pattern-matching-type-property-relational-list/)).
- ★ **`p.Item2`** 처럼 **기본 이름은 언제나 쓸 수 있다** — 이름을 달았어도.

### 금지 사례 — 진단이 나는 꼴

| 쓴 꼴 | 진단 코드 | 어디서 |
|---|---|---|
| 이름이 다른 튜플 리터럴을 이름 붙은 타입에 대입 | `CS8123`(**경고** — 이름이 무시된다) | (2) |
| `List`·`Dictionary` 인덱서가 돌려준 튜플의 원소를 고침 | `CS1612`(에러) | (4) |
| 이름이 바뀐 라이브러리로 다시 컴파일 | `CS1061`(에러) | (6) |
| ★★★ 이름이 다른 두 튜플을 `==` | ★★★ **진단 없음** — `True` | (2) |
| ★★★ 튜플을 JSON 으로 직렬화 | ★★★ **진단 없음** — `{}` | (7) |

## 어디서 틀리나

1. ★★★ **「튜플 이름은 런타임에 있다」** — **필드는 `Item1`·`Item2`** 이고 이름은 **반환값 특성에만** 있다((1)).
2. ★★★ **「튜플을 공개 API 로 쓰면 다른 어셈블리에서 이름이 사라진다」** — **컴파일러는 되살린다**((6)). 사라지는 곳은 **`dynamic`·직렬화·리플렉션**이다((7)).
3. ★★★ **「이름이 다르면 `==` 가 거짓」** — **이름은 안 본다**((2)).
4. ★★★ **「튜플 `==` 는 `Equals` 와 같다」** — **원소의 `==`** 를 부른다. `Equals` 만 고친 클래스 원소에서 **갈린다**((2)).
5. ★★ **「튜플은 불변이다」** — **가변 구조체**다(`IsInitOnly=False`)((1)). 인덱서 경유 수정은 `CS1612`((4)).
6. ★★ **「해체는 튜플·record 만 된다」** — **`Deconstruct` 확장 메서드**면 아무 타입이나((3)).
7. ★★ **「라이브러리 튜플 이름을 바꾸면 옛 앱이 깨진다」** — **조용히 그대로 돈다**((6)). 뜻이 바뀌었어도 모른다.
8. ★★ **「튜플이 record 보다 가볍다」** — **`record struct` 도 0 바이트**((8)).
9. ★ **「`Item9` 라는 필드가 있다」** — **`Rest.Item2`** 다((5)).

## 구현 세부사항 대 언어 보장

| 무엇 | 층 | 근거 |
|---|---|---|
| **튜플 = `ValueTuple`, 이름은 런타임에 없다** | ★★★ **언어 보장** · Learn | (1) |
| **대입·`==` 가 이름을 안 본다** | ★★★ **언어 보장** · Learn | (2) |
| **`==` 가 원소별 `==` 로 풀린다** | ★★★ **언어 보장(C# 7.3 튜플 동등)** | (2) IL |
| **해체가 `Deconstruct`(확장 포함)를 찾는다** | ★★★ **언어 보장** | (3) |
| **이름을 `TupleElementNamesAttribute` 로 남긴다** | ★★ **컴파일러·BCL 의 약속** | (1)(6) |
| **8개부터 `Rest` 중첩** | ★★ **BCL 타입 모양**(``ValueTuple`8``) | (5) |
| **`System.Text.Json` 이 `{}` 를 내는 것** | ★ **라이브러리 기본 설정** | (7) |
| **`dynamic` 이 이름을 못 찾는 것** | ★★ **런타임 바인더** | (6) |
| **할당 바이트 값** | ★ **이 판의 관찰** | (8) |

## 언제 쓰고 언제 안 쓰나

- ★★★ **private 메서드의 여러 값 반환 · 한 메서드 안에서 잠깐 묶기 → 튜플 + 해체**((3)).
- ★★★ **공개 API · 직렬화 · 로그 · 이름이 계약인 데이터 → `record`**((6)(7)(9)).
- ★★ **튜플에 `Equals` 만 고친 클래스를 넣고 `==` 로 비교하지 마라** — `Equals` 로((2)).
- ★★ **튜플을 컬렉션에 넣고 원소를 고치려 하지 마라** — 통째로 바꿔 넣는다((4)).
- ★ **남의 타입을 해체하고 싶으면 `Deconstruct` 확장 메서드**((3)).

## 핵심 문장

1. ★★★ **튜플은 가변 구조체 `ValueTuple` 이고, 필드는 `Item1`·`Item2` 다** — 이름은 반환값의 `TupleElementNamesAttribute` 에만 있다((1)).
2. ★★★ **`==` 는 이름을 안 보고 원소별 `==` 를 부른다** — `Equals` 와 갈릴 수 있다((2)).
3. ★★★ **해체는 `Deconstruct` 이름만 찾는다** — 확장 메서드로 아무 타입이나((3)).
4. ★★★ **다른 어셈블리의 컴파일러는 이름을 되살리지만, `dynamic`·JSON 은 못 본다** — `RuntimeBinderException` · `{}`((6)(7)).
5. ★★ **이름을 바꿔도 옛 앱은 튜플이면 조용히 돌고, record 면 `MissingMethodException`** — 튜플 이름은 바이너리 계약이 아니다((6)).

## 관련 자료

- [18번 — `record`](../18-record-value-equality-and-with/) (1) — ★★★ **`Deconstruct` 생성**의 정본. **경계**: 생성 멤버 목록은 거기, **해체가 그것을 부르는 것**은 여기.
- [19번 — 동등성](../19-equality-equals-gethashcode-operator/) (3) — `==` 와 `Equals` 가 어긋나는 뿌리((2)의 `Money`).
- [21번 — 패턴 매칭](../21-pattern-matching-type-property-relational-list/) (4) — 위치 패턴이 `Deconstruct` 를 부른다.
- [14번 — 인덱서](../14-indexers/) — 「이름과 모양만 맞으면 된다」는 **패턴 기반** 설계의 다른 자리.
- [15번 — 접근 한정자와 어셈블리 경계](../15-access-modifiers-and-assembly-boundary/)·[20번 — `enum`](../20-enum-and-flags/) (5) — **라이브러리만 바꿔 끼우는** 같은 무대.
- [01번 — 값 타입과 참조 타입](../01-value-types-and-reference-types/) — (4)의 복사본 사고의 뿌리.
- Java 갈래 목록([`java/syntax/README.md`](../../../java/syntax/README.md))의 **14번**([`14-records/`](../../../java/syntax/14-records/)) — Java 는 튜플 없이 **record** 로 여러 값을 돌려준다.

## 용어 풀이

- **값 튜플(value tuple)** — `(int, string)` 문법이 만드는 `System.ValueTuple<…>` 구조체. 원소는 **public 필드**. C# 7.0.
- **`System.Tuple`** — 옛 튜플. **불변 참조 타입**이고 원소는 **속성**.
- **튜플 원소 이름** — `(int Id, …)` 의 `Id`. **컴파일 시점에만** 있고 메타데이터에는 **`TupleElementNamesAttribute`** 로 남는다.
- **해체(deconstruction)** — `var (a, b) = x`. 튜플이면 원소를, 아니면 **`Deconstruct(out …)`** 을 불러 꺼낸다.
- **`Rest`** — 8번째 칸. 원소가 8개 이상이면 나머지를 **튜플로 담는** 필드.
- **바이너리 호환** — 의존 앱을 **다시 컴파일하지 않고** 라이브러리만 바꿔도 도는 것.

## 더 들어가면

- ★ **튜플 `==` 의 평가 순서** — Learn 은 「비교 전에 모든 원소를 평가」라고 적었다. **이 판에서 부작용 순서를 찍지 않았다.**
- ★ **`using Pair = (int A, int B);`(C# 12 별칭)** — 새 타입이 아니다(Learn). **이 판에서 안 던졌다.**
- ★ **ORM·다른 직렬화기(Newtonsoft 등)** 가 튜플 이름을 보는지 — **안 던졌다.**
