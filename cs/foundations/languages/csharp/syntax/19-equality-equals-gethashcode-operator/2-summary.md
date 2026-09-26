# csharp/syntax/19 — 동등성 규칙 — `Equals`/`GetHashCode`/`==` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [ECMA-334 7판(2023-12)](https://ecma-international.org/publications-and-standards/standards/ecma-334/) ·
> [.NET API — `Object.GetHashCode`](https://learn.microsoft.com/en-us/dotnet/api/system.object.gethashcode)(열어서 확인: 「같은 두 객체는 같은 해시」 · 「역은 아니다」 ·\
> 「해시를 **프로세스 밖으로 내보내거나 저장하지 마라**」 · 「값 타입이 `GetHashCode` 를 안 고치면 `ValueType.GetHashCode` 가 **리플렉션으로** 필드에서 계산한다」 · 「`GetHashCode` 를 고치면 `Equals` 도, 그 역도」)
> **실행 검증** — 이 문서의 모든 출력·진단·IL·할당 바이트는 아래 「이 판」의 도구로 **실제로 돌려 얻은 것**이다(2026-09-26).\
> ★ 블록은 캡처 스크립트가 파일로 받아 조립기가 끼워 넣은 것이다 — 사람이 옮겨 적은 줄은 하나도 없다.\
> ★★★ **진단 언어를 영어로 고정했다**(`DOTNET_CLI_UI_LANGUAGE=en` + `-preferreduilang:en-US`).
> **버전** — `Equals`/`GetHashCode`/연산자 오버로드는 **C# 1.0부터** · `IEquatable<T>` 는 **.NET 2.0(제네릭)부터** · `HashCode.Combine` 은 **.NET Core 2.1부터** 다.
> **경계** — ★★★ **해시 테이블의 원리**(칸·충돌·재해싱)는 [`data-structure/05-hashmap/`](../../../../../data-structure/05-hashmap/)이 정본이다 —\
> 그 문서의 「**사전 지식 — hashCode 와 equals 의 약속**」 절이 **계약 한 문장**(같으면 해시도 같다)을, 「**동작 — 조회**」 절이 **칸을 먼저 고르고 그 칸만 `equals` 로 본다**를 그린다.\
> **여기서는** 그 계약을 **C# 에서 어겼을 때 무엇이 조용히 틀리나**만 센다.\
> ★ [10번](../10-collection-choosing-list-dictionary-hashset-queue-stack/)이 이미 잰 것 — **`Equals` 만 고친 키로 `Count = 3`·`CS0659`** — 은 다시 재지 않는다(여기 격자의 `R2` 한 줄로만 잇는다).\
> ★ [02번](../02-struct-vs-class-choosing/)이 이미 잰 것 — **`p1.Equals(p2)` 한 번에 +48 바이트 · `IEquatable<T>` 면 +0** — 은 **한 호출**이었다. 여기서는 **컬렉션 안에서** 다시 본다.\
> ★★★ **앞 사슬** — [18번](../18-record-value-equality-and-with/)이 **record 가 만드는 `==`·`Equals`·`GetHashCode` 의 IL** 을 찍었다. **이 문서의 사고가 record 에서는 안 나는 이유**가 거기 있다.
> ★★★ **대비 — 이 문서는 네 갈래 대비표의 네 번째 칸이다.**\
> Python 갈래 목록([`python/syntax/README.md`](../../../python/syntax/README.md))의 **30번**([`30-repr-eq-hash-contracts/`](../../../python/syntax/30-repr-eq-hash-contracts/)) ·\
> Rust 갈래 목록([`rust/syntax/README.md`](../../../rust/syntax/README.md))의 **28번**([`28-partialeq-eq-partialord-ord-and-hash-contracts/`](../../../rust/syntax/28-partialeq-eq-partialord-ord-and-hash-contracts/)) ·\
> Kotlin 갈래 목록([`kotlin/syntax/README.md`](../../../kotlin/syntax/README.md))의 **32번**([`32-equality-and-equals-contract/`](../../../kotlin/syntax/32-equality-and-equals-contract/)) —\
> ★★★ **셋이 같은 실험(계약 위반 × 해시 컬렉션)을 했다.** 여기서는 **Kotlin 32 의 다섯 모양(`R1`\~`R5`)을 그대로 C# 에 던져 표를 잇는다.**
>
> ★★ **흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | ★★★ **`GetHashCode()` 의 값** — 이 문서는 **한 번도 안 찍었다**((6)은 **가짓수**만 센다) | ★★★ 두 해시가 **같나 다르나** · 여러 판에서 **몇 가지가 나왔나** |
> | ★ 격자 **`R2` 줄의 `Count=2`** — 기본 해시 둘이 **우연히 같으면** 답이 바뀐다(두 캡처에서 같았지만 **보장이 아니다**) | 격자의 나머지 칸 · **「갈린 칸 N / M」 줄** |
> | 진단 **문구** | ★★★ **진단 코드**(`CS0659`·`CS0660`·`CS0661`·`CS0252`·`CS0253`·`CS0216`·`CS0019`)와 **`(행,열)`** |
> | ★ **증분의 절댓값 일부** — 한 판에서 잰 바이트 | ★★★ **네 판에서 갈린 줄 수** · 네 판에서 다 같은 바이트 |
> | **IL 오프셋 폭** | ★★ **옵코드**(`ceq` 대 `call String::op_Equality`) |

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
| **언어 명세(ECMA-334)** | C# 언어가 약속한 것 | ★★★ **`==` 는 정적 타입으로 연산자를 고른다** · `==` 를 정의하면 `!=` 도(`CS0216`) · 구조체에는 `==` 가 없다(`CS0019`) |
| **라이브러리 계약(.NET API 문서)** | BCL 이 약속한 것 | ★★★ **「같으면 해시도 같다」** · 해시를 저장·전송하지 마라 · 기본 `GetHashCode` 는 **보장이 없다** |
| **런타임·BCL 구현** | CoreCLR 이 그렇게 하는 것 | ★★★ `HashSet` 이 **참조 지름길을 안 쓰는 것** · `Contains` 가 **원소 쪽 `Equals`** 를 부르는 것 · `ValueType.GetHashCode` 가 **첫 필드만** 보는 것 · `IsBitwiseEquatable` |
| **이 판의 관찰** | .NET 10.0.12 · linux-x64 | 진단 문구 · 할당 바이트 · `-warn:9` 가 답한 탐침 수 |

★★★ **이 주제는 둘째 칸이 두껍다** — **계약이 언어가 아니라 라이브러리 문서에 산다.** 컴파일러는 **짝을 안 맞춘 것**만 경고하고 **내용**은 안 본다((4)).\
★★ 그리고 **셋째 칸(BCL 구현)이 Kotlin/JDK 와 답을 가르는 자리**가 둘 나온다((1)의 `R1`·`R5`).

## 한눈에 — 쉽게 말하면

**「같다」가 C# 에 셋 있다 — 그리고 셋이 서로 모른다.**

사물함 열쇠를 생각하자.

- **`ReferenceEquals`** — 「**이 열쇠가 그 열쇠인가**」. 물건이 하나냐를 묻는다.
- **`Equals`** — 「**이 열쇠로 그 사물함이 열리나**」. 타입이 **정한 규칙**을 묻는다.
- **`==`** — ★★★ 「**변수에 적힌 타입이 정한 방법**으로 비교하라」. 규칙을 **변수 타입이** 고른다.
- **`GetHashCode`** — 「**몇 번 칸에 있나**」. 해시 컬렉션은 **칸부터 찾고 그 칸만 `Equals` 로 뒤진다.**\
  ★★★ **같은 열쇠가 다른 칸 번호를 받으면** — 칸이 틀려 **`Equals` 는 불리지도 않는다.**

| 비유 | 실체 | 어디서 보나 |
|---|---|---|
| 칸 번호가 틀리면 뒤지지도 않는다 | ★★★ `GetHashCode` 를 안 고치면 **셋은 못 찾고 리스트는 찾는다** | (1) `R2` |
| 넣은 뒤 열쇠를 깎는다 | ★★★ **넣은 그 객체도 못 찾는다** | (1) `R3` |
| 규칙을 변수 타입이 고른다 | ★★★ **`string` 은 `==` 가 값 비교, `object` 로 받으면 참조 비교** | (3) |
| `Equals` 만 고쳤는데 `==` 는 그대로 | ★★★ **클래스의 `==` 는 여전히 참조 비교** — 둘이 어긋난다 | (3) |
| 열쇠 복사본을 만들어 비교 | ★★ 구조체 `Equals` 는 **박싱** — `IEquatable<T>` 가 없앤다 | (5) |

★★★ **이 주제의 본체 그림 — 해시 컬렉션이 `Contains(x)` 를 푸는 두 단계와, 어기면 어디서 새나.**

```text
   HashSet.Contains(x)
        │
        ▼
   ① x.GetHashCode() ─▶ 칸 번호                    ← R2(해시 안 고침) · R3(넣은 뒤 변경) 은 여기서 틀린 칸으로 간다
        │                                              → 그 칸에는 아무것도 없다 → Equals 는 불리지도 않는다
        ▼
   ② 그 칸의 원소 e 마다  e.Equals(x)  ?            ← R1(반사성) · R4(추이성) · R5(대칭성) 은 여기서 틀린 답을 낸다
        │                 ★ 방향: 원소.Equals(인자)   (이 판의 BCL — JDK 는 반대, (1) R5)
        ▼
   true / false

   List.Contains(x) 는 ① 이 없다 — 처음부터 끝까지 ② 만 한다.
   ★★★ 그래서 ① 에서 새는 사고(R2·R3)는 「셋은 틀리고 리스트는 맞는다」로 나타난다.
```

## 이 주제가 답하려는 질문

1. **계약을 어기면 해시 컬렉션이 무엇을 조용히 틀리나** — 다섯 모양 × `HashSet`/`List`((1)).
2. **C# 은 네 갈래 중 어디에 서나** — 무엇이 막아 주고 무엇이 안 막아 주나((2)).
3. **`==` 와 `Equals` 는 왜 어긋나나** — 정적 타입이 연산자를 고른다((3)).
4. **컴파일러는 무엇을 경고하나**((4)).
5. **`IEquatable<T>` 는 무엇을 바꾸나** — 박싱((5)).

## 동작 방식

### (0) 이 주제가 쓰는 창

★★★ **본체 창은 실행 출력 격자다** — 네 창 밖의 것이다([16번](../16-inheritance-virtual-override-abstract-sealed-new/)의 「정적 × 동적 격자」와 같은 자리).\
계약 위반은 **예외도 진단도 없이 값만 틀린다** — **값을 찍어 칸을 세는 것** 말고는 드러낼 방법이 없다.

| 창 | 무엇을 보여 주나 | 이 주제에서 |
|---|---|---|
| ★★★ **실행 출력 격자** | ★★★ **계약 위반 × 자료구조** — `HashSet` 과 `List` 가 **갈린 칸 N / M** | (1) |
| ★★★ **② 진단 격자** | `CS0659`·`CS0660`·`CS0661`·`CS0252`·`CS0253` — **탐침 N 중 답한 것** | (4) |
| ★★ **① IL 덤프** | `==` 가 **`ceq`(참조) 인가 `call op_Equality`(값) 인가** — 정적 타입이 고른 결과 | (3) |
| ★★ **④ 할당 바이트** | `IEquatable<T>` 유무 × `List`/`HashSet` — **2×2 판 격자** | (5) |
| ★ **③ 리플렉션** | ★ 런타임 내부 판정 **`IsBitwiseEquatable<T>`** — (5)의 뜻밖의 0 바이트를 설명한다 | (5) |

- ★★★ **① IL 이 (3)의 결정적 증거다** — `Money` 의 `==` 와 `object` 의 `==` 는 **같은 `ceq`** 이고,\
  `string` 의 `==` 만 **`call String::op_Equality`** 다. **변수 타입이 연산자를 골랐다는 것이 옵코드에 박혀 있다.**

### (1) ★★★ 계약 위반 × 자료구조 격자 — 본체

**언제 쓰나** — 「`Equals` 를 대충 써도 어디선가 터지겠지」라고 생각할 때. **안 터진다.**

[Kotlin 32번](../../../kotlin/syntax/32-equality-and-equals-contract/) (4)의 키 다섯을 **그대로** C# 으로 옮겼다.

| 키 | 깬 것 | 어떻게 |
|---|---|---|
| `R1` | **반사성** — `a.Equals(a)` | `Equals` 가 **늘 `false`** · 해시는 정직(`V`) |
| `R2` | **해시 규약** | `Equals` 만 값으로 · `GetHashCode` 는 **`object` 것 그대로** |
| `R3` | **넣은 뒤 변경** | `record R3` 의 **가변 필드** — 넣고 나서 `V` 를 바꾼다 |
| `R4` | **추이성** | 「차이 1 이하면 같다」 · 해시는 **전부 `0`**(해시 규약은 지킨다) |
| `R5` | **대칭성** | `R5("A").Equals("a")` 는 `true`, `"a".Equals(R5("A"))` 는 `false` |
| `R6` | (대조군) | 평범한 `record` |

```text
===== 소스: cs19b-grid.cs =====
using System;
using System.Collections.Generic;

// R1 — 반사성을 깬다: Equals 가 늘 false · 해시는 정직하다
class R1 { public int V; public R1(int v) => V = v;
    public override bool Equals(object? o) => false;
    public override int GetHashCode() => V; }

// R2 — GetHashCode 를 안 고친다: Equals 만 값으로
#pragma warning disable CS0659
class R2 { public int V; public R2(int v) => V = v;
    public override bool Equals(object? o) => o is R2 r && r.V == V; }
#pragma warning restore CS0659

// R3 — 넣은 뒤 바꾼다: record 의 가변 필드
record R3 { public int V; public R3(int v) => V = v; }

// R4 — 추이성을 깬다: 차이 1 이하면 같다 · 해시는 전부 0 (해시 규약은 지킨다)
class R4 { public int V; public R4(int v) => V = v;
    public override bool Equals(object? o) => o is R4 r && Math.Abs(r.V - V) <= 1;
    public override int GetHashCode() => 0; }

// R5 — 대칭성을 깬다: 문자열과도 같다고 답한다
class R5 { public string S; public R5(string s) => S = s;
    public override bool Equals(object? o) => o switch {
        R5 r     => string.Equals(r.S, S, StringComparison.OrdinalIgnoreCase),
        string t => string.Equals(t, S, StringComparison.OrdinalIgnoreCase),
        _        => false };
    public override int GetHashCode() => S.ToLowerInvariant().GetHashCode(); }

// R6 — 대조군
record R6(int V);

class Program {
    static int split, cells;
    static void Row(string name, Func<object> make, Action<object>? mutate = null) {
        var k = make();
        var set = new HashSet<object> { k };
        set.Add(make());
        mutate?.Invoke(k);
        var list = new List<object> { k };
        bool sk = set.Contains(k), sn = set.Contains(make());
        bool lk = list.Contains(k), ln = list.Contains(make());
        cells += 2;
        if (sk != lk) split++;
        if (sn != ln) split++;
        Console.WriteLine($"{name,-3}| Count={set.Count} | set.Contains(k)={sk,-5} | set.Contains(new)={sn,-5} | list.Contains(k)={lk,-5} | list.Contains(new)={ln,-5}");
    }
    static void Main() {
        Row("R1", () => new R1(1));
        Row("R2", () => new R2(1));
        Row("R3", () => new R3(1), o => ((R3)o).V = 2);
        Row("R6", () => new R6(1));
        Console.WriteLine($"set 과 list 가 갈린 칸 {split} / {cells}");
        var a = new HashSet<object>(); foreach (var v in new[] { 1, 3, 2 }) a.Add(new R4(v));
        var b = new HashSet<object>(); foreach (var v in new[] { 2, 1, 3 }) b.Add(new R4(v));
        Console.WriteLine($"R4 | order 1,3,2 -> Count={a.Count} | order 2,1,3 -> Count={b.Count}");
        var s1 = new HashSet<object> { new R5("A") };
        var s2 = new HashSet<object> { "a" };
        Console.WriteLine($"R5 | {{R5(A)}}.Contains(\"a\")={s1.Contains("a")} | {{\"a\"}}.Contains(R5(A))={s2.Contains(new R5("A"))}");
        Console.WriteLine($"R5 | R5(A).Equals(\"a\")={new R5("A").Equals("a")} | \"a\".Equals(R5(A))={"a".Equals(new R5("A"))}");
    }
}
===== csc -nullable:enable -out:ex.dll cs19b-grid.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
R1 | Count=2 | set.Contains(k)=False | set.Contains(new)=False | list.Contains(k)=False | list.Contains(new)=False
R2 | Count=2 | set.Contains(k)=True  | set.Contains(new)=False | list.Contains(k)=True  | list.Contains(new)=True 
R3 | Count=1 | set.Contains(k)=False | set.Contains(new)=False | list.Contains(k)=True  | list.Contains(new)=False
R6 | Count=1 | set.Contains(k)=True  | set.Contains(new)=True  | list.Contains(k)=True  | list.Contains(new)=True 
set 과 list 가 갈린 칸 2 / 8
R4 | order 1,3,2 -> Count=2 | order 2,1,3 -> Count=1
R5 | {R5(A)}.Contains("a")=True | {"a"}.Contains(R5(A))=False
R5 | R5(A).Equals("a")=True | "a".Equals(R5(A))=False
```

**격자** — `k` 는 넣은 그 객체, `new` 는 **같은 값으로 새로 만든** 객체다.

| 키 | `Count`(두 번 넣음) | `set.Contains(k)` | `set.Contains(new)` | `list.Contains(k)` | `list.Contains(new)` | 무엇을 잃었나 |
|---|---|---|---|---|---|---|
| `R1` 반사성 | **2** | ★★★ **`False`** | `False` | `False` | `False` | ★★★ **넣은 그 객체로도 못 찾는다** |
| `R2` 해시 누락 | **2** | `True` | ★★★ **`False`** | `True` | ★★★ **`True`** | 리스트는 찾고 **셋은 못 찾는다** |
| `R3` 넣은 뒤 변경 | 1 | ★★★ **`False`** | `False` | ★★ **`True`** | `False` | ★ **셋 안에 있는데** 그 객체로도 못 찾는다 |
| `R6` 대조군 | 1 | `True` | `True` | `True` | `True` | — |

- ★★★ **마지막 줄 「`set 과 list 가 갈린 칸 2 / 8`」** — Kotlin 은 **`3 / 8`** 이었다. ★★★ **하나가 줄었다 — `R1` 이다.**
- ★★★ **`R1` — C# 의 `HashSet` 은 넣은 그 객체(`k`)로도 못 찾는다**(`False`). **Kotlin(JDK `HashMap`)은 찾았다**(`true`).\
  JDK 는 **해시가 같으면 `==`(동일성)를 먼저** 보고 맞으면 `equals` 를 **건너뛴다**(Kotlin 32 의 결론).\
  **이 판의 .NET `HashSet` 은 그 지름길이 없다** — 늘 `Equals` 를 부르고, `Equals` 가 `false` 라 답도 `false` 다.\
  ★★ 그래서 C# 에서는 **`set` 과 `list` 가 같은 답(`False`)** 을 내 **「갈린 칸」에서 빠졌다.**\
  ★★★ **이것은 BCL 구현의 차이다** — 어느 쪽도 언어의 약속이 아니다. ★ [18번](../18-record-value-equality-and-with/) (3)이 본 **record 의 `Equals` 안의 `beq` 지름길**은 **`Equals` 안**에 있다 — **컬렉션이 아니라.**
- ★★★ **`R2`** — 규약을 깬 것은 **`GetHashCode` 하나**인데, `HashSet` 은 **칸을 먼저 고르고** 거기서만 `Equals` 를 부른다.\
  새 객체는 **다른 칸**을 보므로 `Equals` 가 **불리지도 않는다.** `List` 는 해시를 안 쓰니 **멀쩡하다.** [10번](../10-collection-choosing-list-dictionary-hashset-queue-stack/) (6)의 `Count = 3` 과 같은 사고다.
- ★★★ **`R3`** — `V` 를 바꾸자 해시가 바뀌어 **넣을 때와 다른 칸**을 본다. **셋 안에 들어 있는데** `Contains(k)` 가 `False` 다. Kotlin 과 **같다.**

그 아래 세 줄이 **추이성**(`R4`)과 **대칭성**(`R5`)이다 — 셋·리스트 격자가 아니라 **순서·방향**을 찍었다.

- ★★★ **`R4`** — 같은 세 값 `1`·`2`·`3` 을 **넣는 순서만 바꿨는데** `Count=2` 와 `Count=1` 로 갈렸다. **Kotlin 과 같다.**\
  `1,3,2` 순이면 `1`·`3` 이 서로 달라 둘 다 들어가고 `2` 는 `1` 과 「같다」며 튕긴다. `2,1,3` 순이면 `2` 가 먼저 앉아 둘 다 튕긴다.\
  ★★ **추이성이 없으면 「몇 개인가」가 넣는 순서의 함수**가 된다.
- ★★★ **`R5` — 방향이 Kotlin 과 정반대다.**
  - C#: `{R5(A)}.Contains("a")` **`True`** · `{"a"}.Contains(R5(A))` **`False`**
  - Kotlin: `{R5(A)}.contains("a")` **`false`** · `{"a"}.contains(R5(A))` **`true`**
  - ★★★ **이 판의 .NET `HashSet` 은 「원소.Equals(인자)」를, JDK 는 「인자.equals(원소)」를 부른다.**\
    마지막 줄이 두 방향의 `Equals` 를 직접 찍었다 — `R5(A).Equals("a")` 는 `True`, `"a".Equals(R5(A))` 는 `False`.\
    C# 은 **원소(`R5`)의 너그러운 `Equals`** 가 불려 `True`, JDK 는 **인자의 엄격한 `equals`** 가 불려 `false` 다.
  - ★★ **대칭성을 깨면 「누가 인자로 오느냐」에 답이 달리고, 그 방향은 라이브러리마다 다르다.** 대칭이 지켜지면 방향이 상관없다 — **그것이 대칭성 조항의 존재 이유다.**

```text
                        C# (.NET 10 BCL)             Kotlin (JDK HashMap)
   R1 set.Contains(k)   False — 지름길 없음            true  — 동일성 먼저
   R5 contains 방향      원소.Equals(인자)              인자.equals(원소)
   갈린 칸               2 / 8                         3 / 8

   ★★★ 같은 계약 위반인데 「어느 칸이 틀리나」가 라이브러리 구현에 달렸다.
       계약을 지키면 이 표의 모든 칸이 같아진다.
```

### (2) ★★★ 네 갈래 대비표 — C# 칸을 채운다

[Python 30번](../../../python/syntax/30-repr-eq-hash-contracts/) 동작 10 이 「**C# 칸은 폴더가 없어 실측이 아니다**」라며 비워 둔 표다. 여기서 채운다.\
★ **Python·Rust·Kotlin 칸은 그 갈래 문서의 결론을 옮긴 것**이고, **C# 칸만 이 문서의 실측**이다.

| 축 | Python | Rust | Kotlin(JVM) | ★ C# |
|---|---|---|---|---|
| 계약 문장이 사는 곳 | 데이터 모델 문서 | std 문서 | `Any.equals` 문서(= Java javadoc) | ★ **`Object.GetHashCode` API 문서** |
| 컴파일러가 **내용**을 강제하나 | ✘ | ✘ — `impl` 의 **존재**만 | ✘ | ★★★ **✘** — (4)의 탐침 셋이 침묵 |
| ★ **짝을 안 맞추면** 언제 걸리나 | 런타임 — `__hash__` 가 **`None`** → `TypeError` | ★ **컴파일** — `Eq + Hash` 경계 | ★★ **아무 데서도** — `-Wextra` 도 **경고 0줄** | ★★★ **컴파일 경고** — **`CS0659`**(`Equals` 만) · `CS0660`/`CS0661`(`==` 만) — **그러나 경고라 빌드는 된다** |
| 반사성을 깬 키 · **넣은 그 객체로** 찾나 | ✔ — **정체 지름길**(CPython) | (그 실험은 **딴 객체**로 물어 `None`) | ✔ — JDK 가 **동일성 먼저** | ★★★ **✘ `False`** — 지름길 없음((1) `R1`) |
| 해시 누락 · 셋 대 리스트 | (`TypeError` 가 먼저 막는다 — **`__hash__` 를 일부러 써야** 이 모양이 된다) | (컴파일이 먼저 막는다) | 셋 `false` · 리스트 `true` | ★★★ 셋 **`False`** · 리스트 **`True`** — Kotlin 과 같다 |
| 넣은 뒤 변경 | **조용하다** — 못 꺼낸다(그 갈래 12번) | (그 갈래에서 안 봤다) | 셋이 **넣은 그 객체도** 못 찾는다 | ★★★ 같다 — **`Contains(k)` `False`** |
| 추이성 · 넣는 순서 | (그 갈래에서 안 봤다) | (그 갈래에서 안 봤다) | `size` 가 **순서에 달린다**(2 / 1) | ★★★ 같다 — **`Count` 2 / 1** |
| 대칭성 · `contains` 방향 | (그 갈래에서 안 봤다) | ★ 한쪽만 `impl` 하면 **컴파일 에러**(`E0369`) — 반대 방향이 **없다** | `인자.equals(원소)` | ★★★ **`원소.Equals(인자)`** — **Kotlin 과 반대**((1) `R5`) |
| **`==` 가 `equals` 와 어긋날 수 있나** | ✘ — `==` 가 **`__eq__`** 다 | ✘ — `==` 가 **`PartialEq::eq`** 다 | ✘ — `==` 가 **`equals` + 널 처리** 다 | ★★★ **✔ 어긋난다** — **정적 타입이 연산자를 고른다**((3)) |
| 해시값을 문서에 적을 수 있나 | ✘ — `str` 해시에 소금 | ✘ — 안정 보장 없음 | ✘ — 「실행 간 일관 불필요」 | ★★★ **✘** — **`struct`·`string` 이 8판 8가지**((6)) |

- ★★★ **C# 만 가진 칸이 둘이다.**
  - **`==` 가 `Equals` 와 어긋날 수 있다** — 나머지 셋은 `==` 가 **곧 그 언어의 같음 메서드**인데, C# 의 `==` 는 **별도 연산자**이고 **정적 타입이 고른다.** (3)이 이 주제의 두 번째 급소다.
  - **짝 안 맞춤이 「경고」로 나온다** — Python(런타임 에러)·Rust(컴파일 에러)보다 늦고 **Kotlin(침묵)보다 이르다.**\
    ★★ **그런데 경고라서 빌드가 된다** — [10번](../10-collection-choosing-list-dictionary-hashset-queue-stack/) (6)이 `CS0659` 를 받은 채 `Count = 3` 을 찍었다.
- ★★ **C# 칸이 Kotlin 칸과 갈리는 두 자리(`R1`·`R5`)는 BCL 구현**이다 — 언어가 아니다. **계약을 지키면 사라지는 차이**다.

```text
   짝을 안 맞춘 것을 언제 잡나 (이르다 → 늦다)

   Rust     컴파일 에러    ── Eq + Hash 경계가 없으면 HashMap 키가 못 된다
   C#       컴파일 경고    ── CS0659 · CS0660 · CS0661  (★ 빌드는 된다)
   Python   런타임 에러    ── __eq__ 만 쓰면 __hash__ = None → TypeError
   Kotlin   아무 데서도    ── equals 만 고쳐도 -Wextra 경고 0줄

   ★★★ 넷 다 「내용이 맞는지」 는 안 본다 — (1) 의 R1·R4·R5 는 어느 언어에서도 컴파일된다.
```

### (3) ★★★ `==` 와 `Equals` 가 어긋나는 자리 — 정적 타입이 연산자를 고른다

**언제 쓰나** — `Equals` 를 고친 클래스에 `==` 를 쓸 때 · `object`·제네릭으로 문자열을 비교할 때.

```text
===== 소스: cs19b-opeq.cs =====
using System;
class Money {
    public int Won;
    public Money(int w) => Won = w;
    public override bool Equals(object? o) => o is Money m && m.Won == Won;
    public override int GetHashCode() => Won;
}
static class Probe {
    public static bool A(Money a, Money b)   => a == b;
    public static bool B(string a, string b) => a == b;
    public static bool C(object a, object b) => a == b;
    public static bool D<T>(T a, T b) where T : class => a == b;
}
class Program {
    static void Main() {
        var a = new Money(100); var b = new Money(100);
        Console.WriteLine($"[1] Money  a == b           : {a == b}");
        Console.WriteLine($"[2] Money  a.Equals(b)      : {a.Equals(b)}");
        string s = "hello";
        string t = new string("hello".ToCharArray());      // 내용이 같은 다른 객체
        object os = s, ot = t;
        Console.WriteLine($"[3] string s == t           : {s == t}");
        Console.WriteLine($"[4] object os == ot         : {os == ot}");
        Console.WriteLine($"[5] object os.Equals(ot)    : {os.Equals(ot)}");
        Console.WriteLine($"[6] Probe.D<string>(s, t)   : {Probe.D(s, t)}");
        Console.WriteLine($"[7] object.Equals(s, t)     : {object.Equals(s, t)}");
        Console.WriteLine($"[8] ReferenceEquals(s, t)   : {ReferenceEquals(s, t)}");
        foreach (var n in new[] { "A", "B", "C", "D" }) Il.Dump(typeof(Probe), n);
    }
}
===== csc -nullable:enable -r:il.dll -out:ex.dll cs19b-opeq.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
[1] Money  a == b           : False
[2] Money  a.Equals(b)      : True
[3] string s == t           : True
[4] object os == ot         : False
[5] object os.Equals(ot)    : True
[6] Probe.D<string>(s, t)   : False
[7] object.Equals(s, t)     : True
[8] ReferenceEquals(s, t)   : False
--- Probe.A ---
  IL_0000: ldarg.0
  IL_0001: ldarg.1
  IL_0002: ceq
  IL_0004: ret
--- Probe.B ---
  IL_0000: ldarg.0
  IL_0001: ldarg.1
  IL_0002: call System.String::op_Equality
  IL_0007: ret
--- Probe.C ---
  IL_0000: ldarg.0
  IL_0001: ldarg.1
  IL_0002: ceq
  IL_0004: ret
--- Probe.D ---
  IL_0000: ldarg.0
  IL_0001: box T
  IL_0006: ldarg.1
  IL_0007: box T
  IL_000c: ceq
  IL_000e: ret
===== csc -nullable:enable -warn:9 -r:il.dll -out:ex.dll cs19b-opeq.cs    # 같은 소스를 -warn:9 로 — 진단이 몇 줄인가 (cc exit=0) =====
```

- ★★★ **`[1]` `Money a == b` 가 `False`, `[2]` `a.Equals(b)` 가 `True`** — **`Equals` 만 고친 클래스의 `==` 는 여전히 참조 비교**다.\
  IL `Probe.A` 가 **`ceq`**(두 참조를 그대로 비교) 다. **`Equals` 는 불리지도 않는다.**
- ★★★ **`[3]` `string s == t` 는 `True`** — 내용이 같은 **다른 객체**(`[8]` `ReferenceEquals` 가 `False`)인데도.\
  IL `Probe.B` 가 **`call System.String::op_Equality`** — `string` 은 `==` 를 **오버로드**해 두었다.
- ★★★ **`[4]` 같은 두 문자열을 `object` 변수로 받으면 `False`** — IL `Probe.C` 가 다시 **`ceq`** 다.\
  ★★★ **객체는 한 글자도 안 바뀌었는데 변수 타입이 바뀌자 답이 바뀌었다** — 연산자 오버로드는 **정적 타입으로 고른다**(가상 디스패치가 아니다).\
  [16번](../16-inheritance-virtual-override-abstract-sealed-new/) (1)의 **`new` 가 정적 타입으로 갈리는 것**과 같은 모양이다.
- ★★ **`[5]` 그런데 `os.Equals(ot)` 는 `True`** — `Equals` 는 **가상**이라 실제 객체(`string`)의 것이 불린다.
- ★★★ **`[6]` `Probe.D<string>(s, t)` 가 `False`** — `where T : class` 제네릭 안의 `==` 는 **`T` 에 무엇이 오든 참조 비교**다.\
  IL 이 **`box T` · `box T` · `ceq`** — 컴파일 시점에 `T` 가 `string` 인지 모르니 `op_Equality` 를 고를 수 없다.\
  ★ **유명한 함정**이다 — 제네릭 코드가 **문자열을 참조로** 비교한다.
- ★★ **`[7]` `object.Equals(s, t)` 는 `True`** — 정적 `object.Equals` 는 널을 처리한 뒤 **가상 `Equals`** 를 부른다. **제네릭에서 값 비교가 필요하면 이쪽**(또는 `EqualityComparer<T>.Default`)이다.

```text
                      정적 타입이 고른 것           IL                      결과
   Money  a == b       (오버로드 없음) 참조 비교      ceq                     False  ← Equals 와 어긋남
   string s == t       string.op_Equality          call String::op_Equality True
   object os == ot     (오버로드 없음) 참조 비교      ceq                     False  ← 같은 객체들인데
   T(class) a == b     (T 를 모른다) 참조 비교        box · box · ceq         False  ← T 가 string 이어도
   object.Equals(s,t)  가상 Equals                  (호출)                   True

   ★★★ == 는 「변수에 적힌 타입」 이 고르고, Equals 는 「실제 객체」 가 고른다.
```

> **어느 층인가** — ★★★ **「연산자는 정적 타입으로 고른다」는 언어(334)** 다. 「`string` 이 `==` 를 오버로드했다」는 **BCL 의 선택**이다.\
> ★ **[18번](../18-record-value-equality-and-with/) (3)이 본 대로 record 는 `op_Equality` 가 `Equals` 를 부르게 생성된다** — 그래서 record 의 `[1]` 은 `True` 가 된다.

### (4) ★★ 컴파일러가 무엇을 경고하나 — 탐침 열

```text
===== 소스: cs19b-probe.cs =====
using System;
using System.Collections.Generic;

// 탐침 1 — Equals 만 재정의한다
class P1 { public int V { get; set; } public override bool Equals(object? o) => o is P1 p && p.V == V; }

// 탐침 2 — == 와 != 만 정의한다
class P2 { public int V { get; set; }
    public static bool operator ==(P2? a, P2? b) => a?.V == b?.V;
    public static bool operator !=(P2? a, P2? b) => !(a == b); }

// 탐침 3 — == · != · Equals 를 정의하고 GetHashCode 는 안 쓴다
class P3 { public int V { get; set; }
    public static bool operator ==(P3? a, P3? b) => a?.V == b?.V;
    public static bool operator !=(P3? a, P3? b) => !(a == b);
    public override bool Equals(object? o) => o is P3 p && p.V == V; }

// 탐침 4 — GetHashCode 만 재정의한다
class P4 { public int V { get; set; } public override int GetHashCode() => V; }

// 탐침 5 — IEquatable<T> 만 구현한다 (Equals(object)·GetHashCode 는 그대로)
class P5 : IEquatable<P5> { public int V { get; set; } public bool Equals(P5? o) => o is not null && o.V == V; }

// 탐침 6 — Equals 를 안 고친 구조체
struct P6 { public int V { get; set; } }

class Program {
    static void Main() {
        object o = "ab";
        string s = new string("ab".ToCharArray());
        Console.WriteLine($"탐침 7 : o == s  → {o == s}");
        Console.WriteLine($"탐침 8 : s == o  → {s == o}");
        var p6 = new P6();
        Console.WriteLine($"탐침 9 : p6.Equals(p6) → {p6.Equals(p6)}");
        int n = 1;
        Console.WriteLine($"탐침 10 : n == n → {n == n}");
        Console.WriteLine($"탐침 2 : new P2 {{ V = 1 }} == new P2 {{ V = 1 }} → {new P2 { V = 1 } == new P2 { V = 1 }} · HashSet Count → {new HashSet<P2> { new() { V = 1 }, new() { V = 1 } }.Count}");
        Console.WriteLine($"탐침 5 : ((object)x).Equals(y) → {((object)new P5 { V = 1 }).Equals(new P5 { V = 1 })} · HashSet Count → {new HashSet<P5> { new() { V = 1 }, new() { V = 1 } }.Count}");
    }
}
===== csc -nullable:enable -warn:9 -out:ex.dll cs19b-probe.cs 2>&1 | sort && dotnet ex.dll (cc exit=0 · run exit=0) =====
cs19b-probe.cs(13,7): warning CS0659: 'P3' overrides Object.Equals(object o) but does not override Object.GetHashCode()
cs19b-probe.cs(13,7): warning CS0661: 'P3' defines operator == or operator != but does not override Object.GetHashCode()
cs19b-probe.cs(31,47): warning CS0252: Possible unintended reference comparison; to get a value comparison, cast the left hand side to type 'string'
cs19b-probe.cs(32,47): warning CS0253: Possible unintended reference comparison; to get a value comparison, cast the right hand side to type 'string'
cs19b-probe.cs(36,47): warning CS1718: Comparison made to same variable; did you mean to compare something else?
cs19b-probe.cs(5,7): warning CS0659: 'P1' overrides Object.Equals(object o) but does not override Object.GetHashCode()
cs19b-probe.cs(8,7): warning CS0660: 'P2' defines operator == or operator != but does not override Object.Equals(object o)
cs19b-probe.cs(8,7): warning CS0661: 'P2' defines operator == or operator != but does not override Object.GetHashCode()
탐침 7 : o == s  → False
탐침 8 : s == o  → False
탐침 9 : p6.Equals(p6) → True
탐침 10 : n == n → True
탐침 2 : new P2 { V = 1 } == new P2 { V = 1 } → True · HashSet Count → 2
탐침 5 : ((object)x).Equals(y) → False · HashSet Count → 2
===== csc -nullable:enable -warn:9 -out:ex.dll cs19b-probe.cs 2>&1 | grep -o "cs19b-probe.cs([0-9]*" | sort -u | wc -l    # 탐침 10개 중 진단이 붙은 줄은 몇 개인가 (exit=0) =====
6
```

- ★★★ **탐침 열 중 진단이 붙은 줄은 여섯**이다 — 스크립트가 직접 세어 마지막 줄에 찍었다(`6`).

| 탐침 | 무엇을 심었나 | 답했나 | 실행하면 |
|---|---|---|---|
| 1 | `Equals` 만 재정의 | **답함** — `CS0659` | ([10번](../10-collection-choosing-list-dictionary-hashset-queue-stack/) (6)의 `Count = 3`) |
| 2 | `==`·`!=` 만 정의 | ★★ **답함** — `CS0660` + `CS0661` | ★★★ `==` 는 **`True`** 인데 **`HashSet` 은 `Count 2`** — 셋은 `Equals`·`GetHashCode` 를 쓴다 |
| 3 | `==`·`!=`·`Equals` · `GetHashCode` 없음 | **답함** — `CS0659` + `CS0661` | — |
| 4 | `GetHashCode` 만 재정의 | ★★ **침묵** | — (동작이 안 틀린다 — [10번](../10-collection-choosing-list-dictionary-hashset-queue-stack/)의 결론) |
| 5 | ★★★ **`IEquatable<T>` 만 구현** | ★★★ **침묵** | ★★★ `((object)x).Equals(y)` **`False`** · **`HashSet` `Count 2`** |
| 6 | `Equals` 를 안 고친 구조체 | **침묵** | — ((5)의 박싱) |
| 7 | `object == string` | ★★★ **답함** — `CS0252` | **`False`** |
| 8 | `string == object` | ★★★ **답함** — `CS0253` | **`False`** |
| 9 | 구조체 `p6.Equals(p6)` | **침묵** | `True` |
| 10 | `n == n` | **답함** — `CS1718` | `True` |

- ★★★ **탐침 5 가 가장 조용한 함정이다** — `IEquatable<T>.Equals(P5)` 만 구현하고 **`Equals(object)`·`GetHashCode` 를 안 고치면**\
  **경고가 하나도 없다.** 그런데 **`HashSet<P5>` 는 `Equals(P5)` 로 비교하면서 해시는 `object` 것을 써서** `Count 2` 가 되고,\
  `object` 로 받으면 **참조 비교**(`False`)다. ★ **`CS0659` 는 `Equals(object)` 재정의만 본다** — 이 모양을 모른다.
- ★★★ **탐침 7·8 이 (3)의 함정을 컴파일러가 잡아 주는 자리**다 — **한쪽이 `string`, 다른 쪽이 `object`** 일 때만.\
  ★★ **양쪽이 다 `object` 이면**((3)의 `[4]`) **경고가 없다** — (3) 블록의 마지막 배너 — **`-warn:9` 로 다시 던져도 진단 0줄**(`cc exit=0`)이다.\
  ★ **제네릭의 `==`**((3)의 `[6]`)·**`Equals` 만 고친 `Money` 의 `==`**((3)의 `[1]`) 에도 같은 블록에서 경고가 없었다.
- ★★ **탐침 2** — `==` 는 값인데 컬렉션은 참조 — **(3)의 반대 방향 어긋남**이다. 경고 둘이 정확히 그것을 가리킨다.

```text
===== 소스: cs19b-op2.cs =====
class Half { public static bool operator ==(Half a, Half b) => true; }      // != 를 안 적었다
struct Pt { public int X; }
class Program {
    static void Main() {
        var p = new Pt(); var q = new Pt();
        bool same = p == q;                                                  // 구조체에 == 를 쓴다
    }
}
===== csc -out:ex.dll cs19b-op2.cs 2>&1 | sort (cc exit=1) =====
cs19b-op2.cs(1,42): error CS0216: The operator 'Half.operator ==(Half, Half)' requires a matching operator '!=' to also be defined
cs19b-op2.cs(1,7): warning CS0660: 'Half' defines operator == or operator != but does not override Object.Equals(object o)
cs19b-op2.cs(1,7): warning CS0661: 'Half' defines operator == or operator != but does not override Object.GetHashCode()
```

- ★★★ **`CS0216`** — `==` 를 정의하면 **`!=` 도 정의해야** 한다(에러). 짝은 **여기서만 강제**된다.
- ★★★ **`CS0019`** — **구조체에는 `==` 가 없다**(정의 안 하면). 구조체의 「같음」은 **`Equals` 뿐**이다.
- ★ **`CS0660`/`CS0661` 이 에러와 함께 나왔다** — 순서는 `| sort` 로 고정했다.

### (5) ★★ `IEquatable<T>` 와 박싱 — 컬렉션 안에서

**언제 쓰나** — 구조체를 **`HashSet`·`Dictionary` 키**로 쓰거나 **`List.Contains`** 를 돌 때.

★ [02번](../02-struct-vs-class-choosing/) (5)이 **한 호출**을 쟀다 — `p1.Equals(p2)` **+48** · `IEquatable<T>` **+0**. 여기서는 **컬렉션 안에서** 2×2 로 다시 잰다.

```text
===== 소스: cs19b-alloc.cs =====
using System;
using System.Collections.Generic;
struct Plain { public int A; public int B; }                              // Equals 를 안 고쳤다
struct Fast : IEquatable<Fast> {
    public int A; public int B;
    public bool Equals(Fast o) => A == o.A && B == o.B;
    public override bool Equals(object? o) => o is Fast f && Equals(f);
    public override int GetHashCode() => HashCode.Combine(A, B);
}
class Program {
    static long M(Action a) {
        a();                                             // 한 판 데워 놓고
        var b = GC.GetAllocatedBytesForCurrentThread();
        a();
        return GC.GetAllocatedBytesForCurrentThread() - b;
    }
    static void Main() {
        int sink = 0;
        var lp = new List<Plain>    { new() { A = 1, B = 2 } };
        var lf = new List<Fast>     { new() { A = 1, B = 2 } };
        var hp = new HashSet<Plain> { new() { A = 1, B = 2 } };
        var hf = new HashSet<Fast>  { new() { A = 1, B = 2 } };
        var kp = new Plain { A = 1, B = 2 }; var kp2 = new Plain { A = 1, B = 2 };
        var kf = new Fast  { A = 1, B = 2 };
        Console.WriteLine($"List<Plain>.Contains    1000회 : {M(() => { for (int i = 0; i < 1000; i++) sink += lp.Contains(kp) ? 1 : 0; })} 바이트");
        Console.WriteLine($"List<Fast>.Contains     1000회 : {M(() => { for (int i = 0; i < 1000; i++) sink += lf.Contains(kf) ? 1 : 0; })} 바이트");
        Console.WriteLine($"HashSet<Plain>.Contains 1000회 : {M(() => { for (int i = 0; i < 1000; i++) sink += hp.Contains(kp) ? 1 : 0; })} 바이트");
        Console.WriteLine($"HashSet<Fast>.Contains  1000회 : {M(() => { for (int i = 0; i < 1000; i++) sink += hf.Contains(kf) ? 1 : 0; })} 바이트");
        Console.WriteLine($"kp.Equals(kp2)          1000회 : {M(() => { for (int i = 0; i < 1000; i++) sink += kp.Equals(kp2) ? 1 : 0; })} 바이트");
        int h = 0;                                       // 해시 값은 프로세스마다 다르다 — 찍지 않는다
        Console.WriteLine($"kp.GetHashCode()        1000회 : {M(() => { for (int i = 0; i < 1000; i++) h ^= kp.GetHashCode(); })} 바이트");
        GC.KeepAlive(h);
        Console.WriteLine($"(합 {sink})");
    }
}
===== csc -nullable:enable -out:ex.dll cs19b-alloc.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
List<Plain>.Contains    1000회 : 0 바이트
List<Fast>.Contains     1000회 : 0 바이트
HashSet<Plain>.Contains 1000회 : 72000 바이트
HashSet<Fast>.Contains  1000회 : 0 바이트
kp.Equals(kp2)          1000회 : 48000 바이트
kp.GetHashCode()        1000회 : 24000 바이트
(합 10000)
===== csc -nullable:enable -out:ex.dll cs19b-alloc.cs && DOTNET_TieredCompilation=0 dotnet ex.dll (cc exit=0 · run exit=0) =====
List<Plain>.Contains    1000회 : 0 바이트
List<Fast>.Contains     1000회 : 0 바이트
HashSet<Plain>.Contains 1000회 : 72000 바이트
HashSet<Fast>.Contains  1000회 : 0 바이트
kp.Equals(kp2)          1000회 : 48000 바이트
kp.GetHashCode()        1000회 : 24000 바이트
(합 10000)
===== csc -nullable:enable -optimize -out:exo.dll cs19b-alloc.cs && dotnet exo.dll (cc exit=0 · run exit=0) =====
List<Plain>.Contains    1000회 : 0 바이트
List<Fast>.Contains     1000회 : 0 바이트
HashSet<Plain>.Contains 1000회 : 72000 바이트
HashSet<Fast>.Contains  1000회 : 0 바이트
kp.Equals(kp2)          1000회 : 48000 바이트
kp.GetHashCode()        1000회 : 24000 바이트
(합 10000)
===== csc -nullable:enable -optimize -out:exo.dll cs19b-alloc.cs && DOTNET_TieredCompilation=0 dotnet exo.dll (cc exit=0 · run exit=0) =====
List<Plain>.Contains    1000회 : 0 바이트
List<Fast>.Contains     1000회 : 0 바이트
HashSet<Plain>.Contains 1000회 : 72000 바이트
HashSet<Fast>.Contains  1000회 : 0 바이트
kp.Equals(kp2)          1000회 : 48000 바이트
kp.GetHashCode()        1000회 : 24000 바이트
(합 10000)
===== 네 판 대조 — 「바이트」 줄마다 네 판의 값이 같은가 =====
네 판에서 갈린 줄 0 / 6
```

- ★★★ **`HashSet<Plain>.Contains` 가 1000회에 72000** — 호출당 **72 = 24(해시 박싱) + 48(`Equals` 의 `this`·인자 박싱)**.\
  아래 두 줄이 그 분해다 — `kp.GetHashCode()` **24000**, `kp.Equals(kp2)` **48000**.
- ★★★ **`HashSet<Fast>` 는 0** — `EqualityComparer<Fast>.Default` 가 **`IEquatable<Fast>` 를 보고** `Equals(Fast)` 를 부른다. 해시도 재정의했으니 박싱이 없다.
- ★★★ **뜻밖의 칸 — `List<Plain>.Contains` 가 0 이다.** `IEquatable` 이 **없는데도**.\
  ★ 브리핑·교과서의 「`IEquatable<T>` 가 없으면 박싱한다」가 **이 칸에서는 틀렸다.** 아래가 그 이유다.
- ★★★ **네 판에서 갈린 줄 0 / 6** — 근거로 쓸 수 있다.

| 판 | `List<Plain>` | `List<Fast>` | `HashSet<Plain>` | `HashSet<Fast>` | `Equals` 직접 | `GetHashCode` 직접 | 움직였나 |
|---|---|---|---|---|---|---|---|
| 기본 | 0 | 0 | 72000 | 0 | 48000 | 24000 | — |
| `DOTNET_TieredCompilation=0` | 0 | 0 | 72000 | 0 | 48000 | 24000 | ★ 안 움직임 |
| `csc -optimize` | 0 | 0 | 72000 | 0 | 48000 | 24000 | ★ 안 움직임 |
| 둘 다 | 0 | 0 | 72000 | 0 | 48000 | 24000 | ★ 안 움직임 |

```text
===== 소스: cs19b-bitwise.cs =====
using System;
using System.Collections.Generic;
using System.Reflection;
using System.Runtime.CompilerServices;
struct Plain    { public int A; public int B; }
struct RefField { public int A; public string S; }
struct Fast : IEquatable<Fast> {
    public int A; public int B;
    public bool Equals(Fast o) => A == o.A && B == o.B;
    public override bool Equals(object? o) => o is Fast f && Equals(f);
    public override int GetHashCode() => HashCode.Combine(A, B);
}
class Program {
    // 런타임 내부 판정 — 「바이트째 비교해도 되는 타입인가」. 비공개 API 라 리플렉션으로 부른다.
    static bool Bitwise<T>() => (bool)typeof(RuntimeHelpers)
        .GetMethod("IsBitwiseEquatable", BindingFlags.NonPublic | BindingFlags.Static)!
        .MakeGenericMethod(typeof(T)).Invoke(null, null)!;
    static long M(Action a) { a(); var b = GC.GetAllocatedBytesForCurrentThread(); a(); return GC.GetAllocatedBytesForCurrentThread() - b; }
    static void Main() {
        _ = new Fast { A = 1, B = 2 };
        Console.WriteLine($"IsBitwiseEquatable : Plain={Bitwise<Plain>()} · RefField={Bitwise<RefField>()} · Fast={Bitwise<Fast>()} · int={Bitwise<int>()}");
        int sink = 0;
        var lr = new List<RefField> { new() { A = 1, S = "x" } }; var kr = new RefField { A = 1, S = "x" };
        Console.WriteLine($"List<RefField>.Contains 1000회 : {M(() => { for (int i = 0; i < 1000; i++) sink += lr.Contains(kr) ? 1 : 0; })} 바이트");
        int r1 = new RefField { A = 1, S = "x" }.GetHashCode(), r2 = new RefField { A = 2, S = "x" }.GetHashCode(), r3 = new RefField { A = 1, S = "y" }.GetHashCode();
        Console.WriteLine($"RefField 해시 : (1,x) 와 (2,x) 같나 {r1 == r2} · (1,x) 와 (1,y) 같나 {r1 == r3}");
        int p1 = new Plain { A = 1, B = 2 }.GetHashCode(), p2 = new Plain { A = 1, B = 3 }.GetHashCode(), p3 = new Plain { A = 9, B = 2 }.GetHashCode();
        Console.WriteLine($"Plain 해시    : (1,2) 와 (1,3) 같나 {p1 == p2} · (1,2) 와 (9,2) 같나 {p1 == p3}");
        Console.WriteLine($"RefField (1,x) 와 (1,y) 의 Equals : {new RefField { A = 1, S = "x" }.Equals(new RefField { A = 1, S = "y" })}");
        Console.WriteLine($"(합 {sink})");
    }
}
===== csc -nullable:enable -optimize -out:ex.dll cs19b-bitwise.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
IsBitwiseEquatable : Plain=True · RefField=False · Fast=False · int=True
List<RefField>.Contains 1000회 : 152000 바이트
RefField 해시 : (1,x) 와 (2,x) 같나 False · (1,x) 와 (1,y) 같나 True
Plain 해시    : (1,2) 와 (1,3) 같나 False · (1,2) 와 (9,2) 같나 False
RefField (1,x) 와 (1,y) 의 Equals : False
(합 2000)
```

- ★★★ **`IsBitwiseEquatable<Plain>` 이 `True`** — 런타임이 「**참조가 없고 `Equals` 를 안 고친 구조체는 바이트째 비교해도 된다**」고 판정했다.\
  `List.Contains` 는 그 판정이 참이면 **`Equals` 를 안 부르고 메모리를 직접 비교**하는 길로 간다 — 그래서 박싱이 **0** 이다.\
  ★ 이 설명은 **판정값(`True`/`False`)과 바이트(0 대 152000)가 함께 맞는다**는 데까지가 실측이고, `List.Contains` 의 **내부 분기 코드는 읽지 않았다.**
- ★★★ **`RefField`(참조 필드가 있는 구조체)는 `False`** 이고, **`List<RefField>.Contains` 는 1000회에 152000** — 호출당 **152**, [02번](../02-struct-vs-class-choosing/) (5)의 `r1.Equals(r2)` **+152** 와 같다(리플렉션 경로).
- ★ **`Fast` 는 `False`** — `Equals` 를 고쳤으니 바이트 비교로 대신할 수 없다. 대신 `IEquatable` 경로라 0 이다.
- ★★★ **`RefField` 의 기본 해시는 첫 필드만 본다** — `(1,x)` 와 `(1,y)` 의 해시가 **같고**(`True`), `(1,x)` 와 `(2,x)` 는 **다르다.**\
  **`Equals` 는 둘을 다르다고 하는데**(`False`) 해시는 같다 — **계약 위반은 아니지만**(역은 요구하지 않는다) **충돌이 많아진다.**\
  ★★ .NET API 문서는 「`ValueType.GetHashCode` 는 **필드 값으로** 계산한다」고만 적는다 — **「첫 필드만」은 이 판의 구현**이다.
- ★ **`Plain` 해시는 두 필드를 다 본다**(두 쌍 모두 `False`) — 참조 없는 구조체는 **다른 경로**다.

```text
   구조체 키로 Contains 할 때 — 이 판의 세 경로

   참조 없음 · Equals 안 고침     → IsBitwiseEquatable = True  → 바이트 직접 비교        List 0 · HashSet 은 해시·Equals 박싱 72
   참조 있음 · Equals 안 고침     → 리플렉션 경로(필드마다)                              List 152
   IEquatable<T> 구현             → Equals(T) 직접                                      List 0 · HashSet 0

   ★★★ 「IEquatable 이 없으면 박싱」 은 HashSet 에서는 맞고, List<참조 없는 구조체> 에서는 틀렸다.
   ★★★ 어느 경우든 IEquatable<T> + GetHashCode 를 쓰면 두 컬렉션 다 0 이다.
```

- ★★★ **시간은 안 쟀다.** 「`IEquatable` 이 빠르다」는 문장이 이 문서에 없다 — 잰 것은 **할당 바이트**다.\
  ★ 시간은 [02번](../02-struct-vs-class-choosing/) (5)이 **한 호출 단위로** 쟀다(자릿수 차이 — 그쪽이 정본).

### (6) ★ 해시 값은 문서에 적지 않는다 — 가짓수만

**언제 쓰나** — 해시를 **로그·DB·캐시 키**로 쓰고 싶어질 때.

```text
===== 소스: cs19b-hash.cs =====
using System;
struct Plain { public int A; public int B; }
class Obj { }
class Program {
    static void Main() {
        Console.WriteLine($"{new Plain { A = 1, B = 2 }.GetHashCode()} {new Obj().GetHashCode()} {"alpha".GetHashCode()} {1.GetHashCode()}");
    }
}
===== csc -out:ex.dll cs19b-hash.cs (cc exit=0) =====
===== for i in 1 2 3 4 5 6 7 8; do dotnet ex.dll; done | awk ...    # 8판을 돌려 열마다 서로 다른 값이 몇 가지인가 (exit=0) =====
Plain(1,2) 8가지 · new Obj() 1가지 · "alpha" 8가지 · 1 1가지 (8판 중)
```

- ★★★ **같은 프로그램을 8번 돌렸다** — 값이 아니라 **열마다 서로 다른 값의 가짓수**를 셌다(규칙 11).
  - **`Plain(1,2)` 8가지** — ★★★ **같은 구조체 값의 기본 해시가 프로세스마다 다르다.** 씨앗이 섞인다.
  - **`"alpha"` 8가지** — 문자열 해시도 프로세스마다 다르다([10번](../10-collection-choosing-list-dictionary-hashset-queue-stack/) (5)와 같다).
  - **`new Obj()` 1가지** · **`1` 1가지** — ★ 이 판에서는 안 움직였지만 **보장이 아니다**.\
    ★ `int` 의 해시가 값 자체인 것은 구현이고, 객체 기본 해시가 1가지였던 것은 **이 판의 관찰**이다.
- ★★★ .NET API 문서 — 「해시를 **직렬화하거나 DB 에 저장하지 마라** · **프로세스 밖으로 보내지 마라**」.
- ★ **그래서 이 문서의 격자는 해시 값을 한 번도 찍지 않고 「같나 다르나」만 찍었다.**

## 문법 — 형태와 규칙

### 형태

```csharp
// cs19b-form.cs
using System;
using System.Collections.Generic;

var a = new Money(100, "KRW"); var b = new Money(100, "KRW");
Console.WriteLine($"{a == b} {a.Equals(b)} {a.Equals((object)b)} {a.GetHashCode() == b.GetHashCode()} {new HashSet<Money> { a, b }.Count}");

sealed class Money : IEquatable<Money> {                       // sealed — 파생이 대칭성을 깨지 못하게
    public int Won { get; }                                     // 불변 — 넣은 뒤 해시가 안 바뀐다
    public string Currency { get; }
    public Money(int won, string currency) { Won = won; Currency = currency; }
    public bool Equals(Money? o) => o is not null && Won == o.Won && Currency == o.Currency;
    public override bool Equals(object? o) => Equals(o as Money);               // 한 곳으로 모은다
    public override int GetHashCode() => HashCode.Combine(Won, Currency);       // Equals 가 보는 것만 섞는다
    public static bool operator ==(Money? x, Money? y) => x is null ? y is null : x.Equals(y);
    public static bool operator !=(Money? x, Money? y) => !(x == y);
}
```

```text
===== 소스: cs19b-form.cs =====
using System;
using System.Collections.Generic;

var a = new Money(100, "KRW"); var b = new Money(100, "KRW");
Console.WriteLine($"{a == b} {a.Equals(b)} {a.Equals((object)b)} {a.GetHashCode() == b.GetHashCode()} {new HashSet<Money> { a, b }.Count}");

sealed class Money : IEquatable<Money> {                       // sealed — 파생이 대칭성을 깨지 못하게
    public int Won { get; }                                     // 불변 — 넣은 뒤 해시가 안 바뀐다
    public string Currency { get; }
    public Money(int won, string currency) { Won = won; Currency = currency; }
    public bool Equals(Money? o) => o is not null && Won == o.Won && Currency == o.Currency;
    public override bool Equals(object? o) => Equals(o as Money);               // 한 곳으로 모은다
    public override int GetHashCode() => HashCode.Combine(Won, Currency);       // Equals 가 보는 것만 섞는다
    public static bool operator ==(Money? x, Money? y) => x is null ? y is null : x.Equals(y);
    public static bool operator !=(Money? x, Money? y) => !(x == y);
}
===== csc -nullable:enable -warn:9 -out:ex.dll cs19b-form.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
True True True True 1
```

- ★★★ **`-warn:9` 에서 진단 0줄**이다 — 다섯 멤버가 **짝이 맞기** 때문이다.
- ★★★ **`Equals(object)` 는 `Equals(Money?)` 로 모은다** — 규칙을 **한 곳**에 둔다. 셋이 어긋날 틈을 없앤다.
- ★★★ **`GetHashCode` 는 `Equals` 가 보는 필드만** 섞는다(`HashCode.Combine`) — 더 섞으면 계약이 깨지고, 덜 섞으면 충돌만 는다.
- ★★ **`==` 는 널을 먼저 처리하고 `Equals` 를 부른다** — `==` 와 `Equals` 가 **어긋날 수 없게**. [18번](../18-record-value-equality-and-with/) (3)의 생성 IL 이 같은 모양이다.
- ★★ **`sealed`** — 파생이 `Equals` 를 덮어 **대칭성**을 깨지 못하게((1) `R5`, [18번](../18-record-value-equality-and-with/) (4)).
- ★★ **불변 속성** — 넣은 뒤 해시가 **안 바뀌게**((1) `R3`).
- ★ **이 다섯을 손으로 쓰기 싫으면 `record` 다** — 컴파일러가 같은 모양을 만든다([18번](../18-record-value-equality-and-with/)).

### 금지 사례 — 진단이 나는 꼴

| 쓴 꼴 | 진단 코드 | 어디서 |
|---|---|---|
| `Equals` 만 재정의 | `CS0659`(**경고**) | (4) · [10번](../10-collection-choosing-list-dictionary-hashset-queue-stack/) (6) |
| `==`/`!=` 만 정의 · `Equals` 없음 | `CS0660`(**경고**) | (4) |
| `==`/`!=` 만 정의 · `GetHashCode` 없음 | `CS0661`(**경고**) | (4) |
| `==` 만 정의 · `!=` 없음 | `CS0216`(에러) | (4) |
| 구조체에 `==` | `CS0019`(에러) | (4) |
| `object == string` / `string == object` | `CS0252` / `CS0253`(**경고**) | (4) |
| `n == n` | `CS1718`(**경고**) | (4) |
| ★★★ `IEquatable<T>` 만 구현 · `Equals(object)`·`GetHashCode` 없음 | ★★★ **진단 없음** | (4) 탐침 5 |
| ★★★ 양쪽 다 `object` 인 `==` · 제네릭 `where T : class` 의 `==` | ★★★ **진단 없음** | (3) |

## 어디서 틀리나

1. ★★★ **「`Equals` 를 고쳤으니 `==` 도 값 비교다」** — **클래스의 `==` 는 참조 비교 그대로**다((3) `[1]`). 연산자는 **따로** 정의해야 한다.
2. ★★★ **「`string` 은 `==` 가 값 비교니 어디서든 안전하다」** — **`object` 로 받거나 제네릭 `T` 로 받으면 참조 비교**다((3) `[4]`·`[6]`).
3. ★★★ **「계약을 어기면 어디선가 예외가 난다」** — **안 난다.** `Count` 가 늘고 `Contains` 가 `False` 일 뿐이다((1)).
4. ★★★ **「`List` 로 테스트했더니 맞다」** — **`List` 는 해시를 안 쓴다.** `R2`·`R3` 은 **셋에서만** 틀린다((1)).
5. ★★ **「넣은 그 객체로는 늘 찾아진다」** — **C# `HashSet` 은 지름길이 없다**((1) `R1`). JDK·CPython 과 다르다.
6. ★★ **「`contains` 는 인자의 `equals` 를 부른다」** — **이 판의 .NET 은 원소 쪽**이다((1) `R5`). 대칭을 지키면 상관없다.
7. ★★ **「`IEquatable<T>` 만 구현하면 된다」** — **`Equals(object)`·`GetHashCode` 도** 고쳐야 한다. **경고도 안 나온다**((4) 탐침 5).
8. ★★ **「`IEquatable` 이 없으면 무조건 박싱한다」** — **`List<참조 없는 구조체>` 는 0** 이었다((5)). ★ 다만 **`HashSet` 은 72바이트**다.
9. ★★ **「구조체 기본 해시는 모든 필드를 본다」** — **참조 필드가 있으면 첫 필드만** 봤다(이 판의 구현, (5)).
10. ★ **「해시값을 캐시 키로 저장해도 된다」** — **프로세스마다 다르다**((6) 8판 8가지).

## 구현 세부사항 대 언어 보장

| 무엇 | 층 | 근거 |
|---|---|---|
| **연산자는 정적 타입으로 고른다** | ★★★ **언어 보장(334)** | (3) IL `ceq` 대 `call op_Equality` |
| **`==` 를 정의하면 `!=` 도** · **구조체에 기본 `==` 없음** | ★★★ **언어 보장(334)** | (4) `CS0216`·`CS0019` |
| **「같으면 해시도 같다」 · 역은 아님 · 해시를 저장하지 마라** | ★★★ **라이브러리 계약(API 문서)** | (1)(6) |
| **`CS0659`·`CS0660`·`CS0661`·`CS0252`·`CS0253`** 이 **경고**인 것 | ★★ **컴파일러 구현(Roslyn)** — 명세는 계약 내용을 안 본다 | (4) |
| **`HashSet` 에 참조 지름길이 없는 것** | ★★ **BCL 구현** | (1) `R1` — JDK 는 있다 |
| **`HashSet.Contains` 가 `원소.Equals(인자)` 인 것** | ★★ **BCL 구현** | (1) `R5` — JDK 는 반대 |
| **`IsBitwiseEquatable` 로 `List.Contains` 가 바이트 비교하는 것** | ★ **런타임 구현** | (5) — 내부 분기 코드는 **안 읽었다** |
| **`ValueType.GetHashCode` 가 참조 필드 구조체에서 첫 필드만 보는 것** | ★ **런타임 구현** | (5) |
| **구조체·문자열 기본 해시가 프로세스마다 다른 것** | ★ **런타임 구현** | (6) — 문서는 「다를 수 있다」만 약속 |
| **할당 바이트 72·48·24·152** | ★ **이 판의 관찰**(2×2 에서 안 움직임) | (5) |

## 언제 쓰고 언제 안 쓰나

- ★★★ **값으로 같아야 하는 타입이면 먼저 `record` 를 고려하라** — 다섯 멤버가 **짝이 맞게 생성**된다([18번](../18-record-value-equality-and-with/)).
- ★★★ **손으로 쓸 거면 다섯을 한 벌로** — `IEquatable<T>.Equals(T)` · `Equals(object)` · `GetHashCode` · `==` · `!=`((형태)).\
  ★ 하나라도 빠지면 (4)의 경고가 나거나(좋은 경우) **탐침 5 처럼 침묵**한다(나쁜 경우).
- ★★★ **해시 컬렉션의 키는 불변으로** — `R3` 는 경고도 예외도 없다.
- ★★ **제네릭 코드에서 값 비교는 `EqualityComparer<T>.Default.Equals` 나 `object.Equals`** — `where T : class` 의 `==` 는 참조 비교다((3) `[6]`).
- ★★ **구조체 키에는 `IEquatable<T>` + `GetHashCode`** — `HashSet`·`Dictionary` 에서 박싱이 **0** 이 된다((5)).
- ★ **부동소수점 근사 비교를 `Equals` 로 쓰지 마라** — 추이성이 깨진다((1) `R4`). **별도 메서드**로 둬라.
- ★ **`Equals` 를 다른 타입(문자열 등)과 같다고 답하게 쓰지 마라** — 대칭성이 깨지고 **컬렉션마다 답이 다르다**((1) `R5`).

## 핵심 문장

1. ★★★ **계약 위반은 예외가 아니라 조용한 오답이다** — C# 격자는 **`HashSet` 과 `List` 가 갈린 칸 2 / 8**, Kotlin 은 3 / 8 이었다((1)).
2. ★★★ **C# 의 `==` 는 정적 타입이 고르는 별도 연산자다** — `Equals` 만 고친 클래스·`object` 로 받은 문자열·제네릭 `T` 에서 **참조 비교**가 된다((3)).
3. ★★★ **C# 은 짝 안 맞춤을 「경고」로 잡는다**(`CS0659`·`CS0660`·`CS0661`) — Rust 보다 늦고 Kotlin 보다 이르다. **`IEquatable<T>` 만 쓴 모양은 못 잡는다**((2)(4)).
4. ★★ **Kotlin 과 갈리는 `R1`·`R5` 는 BCL 구현의 차이다** — 계약을 지키면 사라진다((1)).
5. ★★ **`IEquatable<T>` 는 `HashSet` 의 박싱 72바이트를 0 으로 만든다** — `List<참조 없는 구조체>` 는 원래 0 이었다(`IsBitwiseEquatable`)((5)).

## 관련 자료

- ★★★ [`data-structure/05-hashmap/`](../../../../../data-structure/05-hashmap/) — **경계**: **해시 표의 원리**(칸·충돌·체이닝·재해싱)와 **계약 한 문장**은 거기다 —\
  그 문서의 「**사전 지식 — hashCode 와 equals 의 약속**」·「**동작 — 조회**」 절. **여기는 C# 에서 어겼을 때의 증상**이다.
- [18번 — `record` 와 값 동등성](../18-record-value-equality-and-with/) — ★★★ **앞 사슬.** 생성된 `op_Equality` 가 `Equals` 를 부르는 IL((3))이\
  **이 문서 (3)의 사고가 record 에서 안 나는 이유**다. `EqualityContract` 가 **대칭성**을 지킨다((4)).
- [10번 — 컬렉션 선택](../10-collection-choosing-list-dictionary-hashset-queue-stack/) — **`Equals` 만 고친 키의 `Count = 3`·`CS0659`** 와 **문자열 해시가 프로세스마다 다른 것**을 먼저 쟀다.
- [02번 — `struct` 대 `class`](../02-struct-vs-class-choosing/) — **구조체 `Equals` 한 호출의 +48·+152·+0** 과 **시간**(자릿수)의 정본.
- [16번 — 상속](../16-inheritance-virtual-override-abstract-sealed-new/) — **정적 타입이 고르는 것**(`new`)과 가상이 고르는 것(`override`)의 격자. (3)이 같은 모양이다.
- Python 갈래 목록([`python/syntax/README.md`](../../../python/syntax/README.md))의 **30번**([`30-repr-eq-hash-contracts/`](../../../python/syntax/30-repr-eq-hash-contracts/)) — **`__hash__ = None` 스위치 · 정체 지름길.** 그 문서 동작 10 의 표를 (2)가 잇는다.
- Rust 갈래 목록([`rust/syntax/README.md`](../../../rust/syntax/README.md))의 **28번**([`28-partialeq-eq-partialord-ord-and-hash-contracts/`](../../../rust/syntax/28-partialeq-eq-partialord-ord-and-hash-contracts/)) — **타입 경계로 막는 쪽** · 대칭은 `impl` 두 벌.
- Kotlin 갈래 목록([`kotlin/syntax/README.md`](../../../kotlin/syntax/README.md))의 **32번**([`32-equality-and-equals-contract/`](../../../kotlin/syntax/32-equality-and-equals-contract/)) — ★★★ **(1)의 다섯 모양의 출처.** `3 / 8` · JDK 동일성 지름길.
- Java 갈래 목록([`java/syntax/README.md`](../../../java/syntax/README.md))의 **27번**([`27-equals-hashcode-contract/`](../../../java/syntax/27-equals-hashcode-contract/)) — `equals` 5조항·`hashCode` 3조항의 **javadoc 계약**.

## 용어 풀이

- **참조 동등성(reference equality)** — 같은 객체인가. `ReferenceEquals`·클래스의 기본 `==`.
- **값 동등성(value equality)** — 타입이 정한 규칙으로 같은가. `Equals` 를 재정의해 만든다.
- **동치 관계(equivalence relation)** — **반사**(a=a)·**대칭**(a=b 면 b=a)·**추이**(a=b, b=c 면 a=c). `Equals` 계약의 뼈대다.
- **해시 규약** — 「`Equals` 로 같으면 `GetHashCode` 도 같다」. 역은 요구하지 않는다(충돌은 합법).
- **연산자 오버로드(operator overloading)** — `public static bool operator ==(…)`. **정적 타입으로 고른다.**
- **`IEquatable<T>`** — `bool Equals(T other)` 를 약속하는 인터페이스. `EqualityComparer<T>.Default` 가 이것을 보면 **박싱 없이** 부른다.
- **`EqualityComparer<T>.Default`** — 컬렉션이 쓰는 비교자. `IEquatable<T>` 가 있으면 그것을, 없으면 `Equals(object)` 를 쓴다.
- **`IsBitwiseEquatable<T>`** — 런타임 내부 판정. 「바이트째 비교해도 `Equals` 와 같은가」. 비공개 API 다.
- **정체 지름길(identity shortcut)** — 컬렉션이 **같은 참조면 `Equals` 를 건너뛰는** 최적화. JDK·CPython 에 있고 **이 판의 .NET `HashSet` 에는 없었다.**

## 더 들어가면

- ★ **`Dictionary<K,V>`** — 같은 `EqualityComparer<K>` 를 쓰므로 `HashSet` 과 같은 답일 것이다 — **이 판에서 격자로 안 던졌다.**
- ★ **`IEqualityComparer<T>` 를 따로 넘기기** — 타입을 못 고칠 때 **컬렉션 쪽에 규칙을 준다.** `StringComparer.OrdinalIgnoreCase` 가 대표다. **안 던졌다.**
- ★ **`HashSet` 내부의 비교 방향** — (1) `R5` 는 **결과로** 방향을 읽었다. **소스 코드는 읽지 않았다.**
- ★ **`double` 의 `==` 대 `Equals`** — `NaN` 이 갈린다. [18번](../18-record-value-equality-and-with/) (8) 탐침 5 가 record 안에서 봤다.
