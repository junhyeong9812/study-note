# csharp/syntax/07 — 널 관련 연산자 `?.`·`??`·`??=` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [ECMA-334 7판(2023-12)](https://ecma-international.org/publications-and-standards/standards/ecma-334/) · [Microsoft Learn — C# 언어 레퍼런스](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/) · [Learn — `checked`/`unchecked`](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/statements/checked-and-unchecked) · [Learn — 널 허용 값 형식](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/builtin-types/nullable-value-types) · [Learn — 널 허용 참조 형식](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/builtin-types/nullable-reference-types) · [Learn — 멤버 접근·널 조건 연산자](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/operators/member-access-operators)
> **실행 검증** — 이 문서의 모든 출력·진단·IL·할당 바이트는 **.NET SDK 10.0.401** ·\
> 런타임 **`.NET 10.0.12`**(`Microsoft.NETCore.App`) · 타겟 **`net10.0`** · **linux-x64** 에서 실제로 돌려 얻은 것이다(2026-09-25).\
> ★ 블록은 캡처 스크립트가 파일로 받아 조립기가 끼워 넣은 것이다 — 사람이 옮겨 적은 줄은 하나도 없다.\
> ★ 소스 펜스의 첫 줄(`// cs0Nb-….cs` 꼴)도 **캡처가 찍은 것**이다. 원고에 손으로 쓴 배너는 없다.
> ★★★ **진단 언어를 영어로 고정했다.** 안 주면 **로캘을 따라 한국어로 나와 재현이 안 된다** —\
> 01\~04 가 실측으로 받은 한국어 판이 ``error CS0029: 암시적으로 'string' 형식을 'int' 형식으로 변환할 수 없습니다.`` 였다.\
> 고정하는 법은 둘을 같이 거는 것이다 — 환경변수 **`DOTNET_CLI_UI_LANGUAGE=en`** 과 `csc` 플래그 **`-preferreduilang:en-US`**.
> **던진 형태** — MSBuild(`dotnet build`·`dotnet run`)를 **안 썼다.** Roslyn 컴파일러를 **직접** 부른다 —\
> 그래야 `bin/`·`obj/` 가 원리상 안 생기고, 진단 경로가 **절대 경로가 아니라 파일명**으로 나오며, 한 판이 0.3초 안에 끝난다.\
> 배너의 `csc` 는 아래 셸 함수이고, `ex.runtimeconfig.json` 은 아래 한 줄짜리 파일이다.
>
> ```text
> export DOTNET_CLI_TELEMETRY_OPTOUT=1 DOTNET_NOLOGO=1
> export DOTNET_CLI_UI_LANGUAGE=en            # ★★★ 안 주면 진단이 한국어로 나온다
> D=$(dirname "$(readlink -f "$(command -v dotnet)")")
> ls "$D"/packs/Microsoft.NETCore.App.Ref/10.0.12/ref/net10.0/*.dll | sed 's/^/-r:/' > refs.rsp
> echo '{"runtimeOptions":{"tfm":"net10.0","framework":{"name":"Microsoft.NETCore.App","version":"10.0.0"}}}' > ex.runtimeconfig.json
> csc() { dotnet exec "$D/sdk/10.0.401/Roslyn/bincore/csc.dll" \
>           -nologo -nostdlib -noconfig @refs.rsp \
>           -preferreduilang:en-US -langversion:latest "$@"; }
> ```
>
> **`-debug` 를 안 줬다** — PDB 가 없으면 스택 트레이스에 **절대 경로와 줄 번호가 안 박힌다**.\
> 그래서 이 문서의 트레이스는 ``at Program.<Main>$(String[] args)`` 에서 끝나고, 어느 머신에서 돌려도 같다.\
> **IL 덤프는 `-optimize` 없이**(기본 디버그) 낸 것이라 `nop` 이 섞여 있고 소스 구조가 그대로 보인다.\
> IL 을 찍는 `cs-il.cs`(82줄, 외부 도구 없이 BCL 만 쓴다)의 전문은 [03번](../03-boxing-and-unboxing/2-summary.md)의 (0)절에 있다.
> **버전** — `?.`·`?[]`·`??` 는 **C# 6부터**(`??` 자체는 **C# 2부터**), `??=` 는 **C# 8부터**,\
> ★ **널 조건 대입**(`a?.B = x`·`a?[i] = x`)은 **C# 14부터**다((7)).\
> 이 문서는 `-langversion:latest` 로 던졌으므로 C# 14 기능이 켜져 있다.
> **경계** — **왜 `?` 를 붙이나**(널 허용 참조 타입)는 [06번](../06-nullable-reference-types/)이 정본이고,\
> **`int?` 가 무엇인가**(`Nullable<T>` 구조체)는 [08번](../08-nullable-value-types/)이 정본이다.\
> ★★★ **이 주제는 그 둘의 가운데**다 — `node?.Count` 한 줄에 **06의 `?`(주석)** 와 **08의 `int?`(진짜 타입)** 가 같이 나온다((1)).\
> 값 타입/참조 타입의 이분은 [01번](../01-value-types-and-reference-types/)이 정본이다.\
> 인덱서(`this[int]`)는 목록의 **14번 주제**, 이벤트와 델리게이트는 목록의 **27번·29번 주제**다.\
> 패턴 매칭(`is null` · `is not null`)은 목록의 **21번 주제**다 — 여기는 **연산자**만 본다.\
> 대비 — Kotlin 의 [널 안전 타입 편](../../../kotlin/syntax/03-null-safe-types/)에도 `?.`·`?:` 가 있는데\
> **결과 타입 규칙이 다르다**((1)). TS 의 [`any`·`unknown`·`never`·`void` 편](../../../ts/syntax/04-any-unknown-never-void/)도 `?.`·`??` 를 갖는다.
> ★★ **흔들리는 칸 / 안 흔들리는 칸** — 제출 전 재대조는 이 표를 기준으로 판정한다.
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | ★ **`GC.GetAllocatedBytesForCurrentThread()` 의 절댓값**(프로세스 시작부터의 누적이다) | ★★★ **두 호출 사이의 증분**과 **그 증분이 0 이냐 아니냐** |
> | 시간·CPU 상태 — 이 문서는 **시간을 한 번도 안 쟀다** | **진단 코드**(`CS0220`·`CS8602` 류) · **진단 문구** · **`(행,열)`** |
> | 객체 주소 · `GetHashCode()` 의 참조형 값 | **`cc exit` 와 `run exit`**(갈라 적었다) |
> | `dotnet` 패치 버전이 오르면 달라질 수 있는 것 | **IL 명령어 열**(`add` · `add.ovf` · `box` · `brtrue.s` · `initobj`) |
> | — | **할당 바이트의 증분값**(24 · 32 · 0) · **타입 크기**(`Unsafe.SizeOf`) |

## 한눈에 — 쉽게 말하면

**`?.` 는 「사람이 없으면 그 줄은 통째로 건너뛰고 빈손으로 돌아오는 심부름」이다.**

「김 과장 책상의 서랍의 세 번째 칸을 열어 봐」라고 시켰는데 **김 과장 자리가 비어 있으면**,
서랍을 찾으러 가지도 않고 세 번째 칸을 세지도 않는다. **그 줄 전체가 없던 일이 된다.**
그리고 심부름꾼은 **빈손으로 돌아온다** — 「없음」을 들고 오는 것이지 화를 내지 않는다.

그런데 **괄호를 치면 이야기가 달라진다.** `(김 과장?.서랍).세번째칸` 은
「김 과장 서랍까지만 조심하고, **그다음은 그냥 열어라**」다 — 빈손 위에서 서랍을 여니 **터진다.**

| 비유 | 실체 |
|---|---|
| **자리에 없으면 그 줄을 통째로 건너뛴다** | `a?.b.c` — 중간에서 멈추는 게 아니라 **사슬 전체**를 건너뛴다((2)) |
| **괄호를 치면 거기서 조심이 끝난다** | `(a?.b).c` → **`NullReferenceException`**((2)) |
| **빈손으로 돌아온다** | ★★ `int` 필드를 `?.` 로 읽으면 **`int?`** 가 된다((1)) |
| **심부름을 안 갔으니 준비물도 안 산다** | `a?.Take(f())` 에서 `a` 가 널이면 **`f()` 가 평가조차 안 된다**((3)) |
| **「없으면 이걸로」** | `??` — 앞이 널일 때만 뒤를 본다((4)) |
| **「비어 있을 때만 채워라」** | `??=` — 이미 차 있으면 **오른쪽을 평가도 안 한다**((4)) |
| ★ **없는 사람 책상에 서류를 안 놓는다** | C# 14 의 `a?.B = x` — `a` 가 널이면 **오른쪽도 평가 안 한다**((7)) |

- ★★★ **이 주제의 한 줄** — `?.` 는 「**널이면 건너뛴다**」이고, 그 대가로 **결과 타입이 한 겹 널 허용이 된다.**\
  `int` → `int?` 가 되는 그 한 겹이 이 주제에서 가장 많이 틀리는 자리다((1)·(6)).
- ★★ **`?.` 는 단락(short-circuit)이다** — `&&` 처럼 **뒤를 아예 평가하지 않는다.** 예외를 잡는 것이 아니다((3)).
- ★★★ **`?.` 의 결과를 비교에 바로 쓰지 마라** — `arr?.Length < 2` 가 **`arr` 이 널일 때 `false`** 다((6)).\
  「길이가 2보다 작다」의 반대가 「2 이상」이 **아니다.** 그 규칙의 정본은 [08번](../08-nullable-value-types/)이다.

```text
   a?.b.c 는 어디까지 건너뛰나

   a?.b.c                          (a?.b).c
   ────────────────                ────────────────
   a 가 null 인가?                  a 가 null 인가?
     │                                │
     ├─ 예 ──> 전체가 null            ├─ 예 ──> (a?.b) 가 null
     │         .b 도 .c 도            │          그 위에서 .c 를 그냥 한다
     │         평가 안 한다            │             ↓
     │                                │         NullReferenceException
     └─ 아니오 ──> a.b.c              └─ 아니오 ──> a.b.c

   ★ 괄호가 「조심하는 구간」의 끝을 정한다.
```

```text
   ?. 가 결과 타입에 하는 일 — 한 겹이 붙는다

   식                 멤버의 타입          ?. 의 결과 타입
   ─────────────────────────────────────────────────────
   node.Count         int                  int          (?. 를 안 썼다)
   node?.Count        int       ──한 겹──> int?          ★ 값 타입이면 Nullable<int> 가 된다
   node?.Name         string?   ──그대로─> string?       ★ 참조 타입은 이미 null 을 담으니 안 붙는다
   node?.Name?.Length int       ──한 겹──> int?
   node?.Count ?? -1  int?      ──?? 로──> int           ★ ?? 가 그 겹을 벗긴다

   ★★ 「참조 타입에는 안 붙는다」가 핵심이다 — 06번의 ? 는 주석이고
      여기서 붙는 ? 는 08번의 진짜 타입이다. 같은 기호, 다른 것.
```

> **널 조건 연산자(null-conditional operator) `?.` · `?[]`** — 왼쪽이 널이 아닐 때만 멤버·요소 접근을 하고,\
> 널이면 **그 사슬 전체를 건너뛰고 널을 결과로 삼는** 연산자. **C# 6부터.**

> **단락 평가(short-circuiting)** — 앞의 결과에 따라 **뒤를 아예 평가하지 않는 것.**\
> `&&`·`||` 와 같은 성질이다. **예외를 잡아서 무시하는 것이 아니다** — 애초에 실행을 안 한다((3)).

> **널 병합 연산자(null-coalescing operator) `??`** — 왼쪽이 널이면 오른쪽을 결과로 삼는다.\
> **오른쪽 결합**이라 `a ?? b ?? c` 는 `a ?? (b ?? c)` 다((5)).

> **널 병합 대입 `??=`** — 왼쪽이 널일 때만 대입한다. **C# 8부터.**\
> 이미 값이 있으면 **오른쪽을 평가하지 않는다**((4)).

> **널 조건 대입** — `a?.B = x` 처럼 **대입의 왼쪽**에 `?.` 를 쓰는 것. **C# 14부터.**\
> `a` 가 널이면 **오른쪽도 평가하지 않는다**((7)). `++`·`--` 는 **여전히 안 된다.**

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. **`?.` 의 결과가 무슨 타입인가** — 그리고 **언제 한 겹이 붙고 언제 안 붙나**((1)).
2. **어디까지 건너뛰나** — 사슬·괄호·인자 평가 셋을 각각 답할 수 있나((2)·(3)).
3. **이 연산자들이 무엇으로 컴파일되나** — 그리고 그것이 **무엇을 보장하나**((8)).

## 동작 방식

### (0) 이 주제가 쓰는 다섯 창

| 창 | 무엇을 보여 주나 | 이 주제에서 |
|---|---|---|
| ★★★ **실행 출력** | ★★★ **평가되나 안 되나** — 단락을 보이는 유일한 방법 | (1)·(3)·(4)·(6)·(7) |
| ★★★ **IL** | ★★★ **`?.` 가 무엇으로 펼쳐지나** · `??` 가 왼쪽을 몇 번 평가하나 | (8) |
| ★★ **컴파일 진단** | ★★ **`??` 의 결합 방향을 「열 번호」로 증명한다** | (5) |
| **예외 전문** | 괄호가 단락을 끊는 것 | (2) |
| ★ **할당 바이트** | ★ **이 주제에서는 안 썼다** — 아래 | — |

★★★ **이 주제의 중심 창은 「실행 출력」이다.** 특이한 자리다 —\
[03번](../03-boxing-and-unboxing/)은 할당 바이트, [06번](../06-nullable-reference-types/)은 진단이 중심이었는데,
**「평가되었나 안 되었나」는 오직 부작용(출력)으로만 보인다.**
그래서 이 문서의 프로그램들은 **`[평가됨]` 이라고 찍는 헬퍼**를 쓴다 — **안 찍힌 줄이 근거**다.

★★ **진단이 결정적으로 쓰이는 자리가 하나 있다** — (5)의 `??` 결합 방향이다.\
**에러의 「열 번호」가 컴파일러가 어느 짝을 지었는지 말해 준다.** 출력으로는 절대 안 보이는 것을 진단이 보여 준다.

★ **할당 바이트는 안 썼다** — `?.` 는 값 타입 멤버에서 `Nullable<T>` 를 만드는데\
그것은 **구조체라 힙을 안 쓴다**([08번](../08-nullable-value-types/)이 정본이다). 여기서 다시 잴 이유가 없다.

### (1) ★★★ `?.` 의 결과 타입 — `int` 가 `int?` 가 된다

**언제 쓰나** — 이 주제에서 **가장 먼저 무는 자리.** 「왜 `int` 에 넣을 수가 없지?」가 여기서 풀린다.

정적 타입을 찍는 방법이 하나 있다 — **제네릭 메서드에 넘기고 `typeof(T)` 를 찍는 것**이다.
`T` 는 **컴파일러가 추론한 정적 타입**이므로, 런타임 값이 널이어도 **타입은 그대로 나온다.**

```text
===== 소스: cs07b-type.cs =====
#nullable enable
using System;

Node? none = null;
Node some = new Node { Count = 3, Name = "xy" };

Show("none?.Count      ", none?.Count);
Show("some?.Count      ", some?.Count);
Show("some.Count       ", some.Count);
Show("none?.Name       ", none?.Name);
Show("none?.Name?.Length", none?.Name?.Length);
Show("some?.Name!.Length", some?.Name!.Length);
Show("none?.Self()     ", none?.Self());
Show("none?.Count ?? -1", none?.Count ?? -1);
Show("none?.Grade      ", none?.Grade);

static void Show<T>(string label, T v)
    => Console.WriteLine($"{label} → 정적 타입 {Name(typeof(T)),-18} 값 {(v is null ? "(null)" : v.ToString())}");

static string Name(Type t) {
    if (t.IsGenericType && t.GetGenericTypeDefinition() == typeof(Nullable<>))
        return "Nullable<" + t.GetGenericArguments()[0].Name + ">";
    return t.Name;
}

public class Node {
    public int Count;
    public string? Name;
    public char Grade = 'A';
    public Node Self() => this;
}
===== csc -out:ex.dll cs07b-type.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
cs07b-type.cs(9,27): warning CS8602: Dereference of a possibly null reference.
none?.Count       → 정적 타입 Nullable<Int32>    값 (null)
some?.Count       → 정적 타입 Nullable<Int32>    값 3
some.Count        → 정적 타입 Int32              값 3
none?.Name        → 정적 타입 String             값 (null)
none?.Name?.Length → 정적 타입 Nullable<Int32>    값 (null)
some?.Name!.Length → 정적 타입 Nullable<Int32>    값 2
none?.Self()      → 정적 타입 Node               값 (null)
none?.Count ?? -1 → 정적 타입 Int32              값 -1
none?.Grade       → 정적 타입 Nullable<Char>     값 (null)
```

- ★★★ **`none?.Count` 의 정적 타입이 `Nullable<Int32>`** 다. 필드는 `int` 인데 **한 겹이 붙었다.**\
  `some?.Count`(왼쪽이 널이 아닐 때)도 **똑같이 `Nullable<Int32>`** 다 — **타입은 값과 무관**하다.
- **`some.Count`(`?.` 없이)는 `Int32`** 다. **연산자가 타입을 바꾼 것**이지 널 여부가 바꾼 것이 아니다.
- ★★ **참조 타입에는 안 붙는다** — `none?.Name` 이 `String` 이고 `none?.Self()` 가 `Node` 다.\
  **참조 타입은 이미 널을 담을 수 있으므로** 더 감쌀 것이 없다.\
  ★ 여기가 [06번](../06-nullable-reference-types/)과 만나는 자리다 — 컴파일러 분석 차원에서는 `string?` 이지만\
  **런타임 타입은 `String` 하나**라 `typeof(T)` 가 `String` 을 답한다.
- ★ **`char` 도 값 타입이라 `Nullable<Char>`** 가 된다. `int` 만의 규칙이 아니다.
- ★★★ **`??` 가 그 겹을 벗긴다** — `none?.Count ?? -1` 의 정적 타입이 **`Int32`** 다.\
  **이것이 `?.` 와 `??` 를 짝으로 쓰는 이유**다((6)에서 이 짝이 함정을 고친다).

### (2) ★★ 사슬 전체를 건너뛴다 — 괄호가 그것을 끊는다

**언제 쓰나** — `a?.b.c` 를 쓸까 `a?.b?.c` 를 쓸까 고를 때.

```text
===== 소스: cs07b-chain.cs =====
#nullable enable
using System;

Node? n = null;

int? a = n?.Inner.Count;
Console.WriteLine($"n?.Inner.Count   → HasValue={a.HasValue}  ← 예외 없이 사슬 전체를 건너뛴다");

try {
    Inner? mid = n?.Inner;
    Console.WriteLine(mid.Count);
} catch (NullReferenceException e) {
    Console.WriteLine($"(n?.Inner).Count → {e.GetType().Name}  ← 괄호가 단락을 끊는다");
}

Node? z = null;
z?.Take(Loud("인자 A"));
Console.WriteLine("z 가 null 일 때 '인자 A' 가 찍혔나? ↑");

Node y = new Node();
y?.Take(Loud("인자 B"));

int[]? arr = null;
Console.WriteLine($"arr?[0]  → HasValue={(arr?[0]).HasValue}");
int[]? arr2 = new[] { 7, 8 };
Console.WriteLine($"arr2?[1] → {arr2?[1]}");

static int Loud(string s) { Console.WriteLine($"   [평가됨] {s}"); return 1; }

public class Node {
    public Inner Inner = new Inner();
    public void Take(int k) => Console.WriteLine($"   Take({k}) 실행");
}
public class Inner { public int Count = 5; }
===== csc -out:ex.dll cs07b-chain.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
cs07b-chain.cs(11,23): warning CS8602: Dereference of a possibly null reference.
n?.Inner.Count   → HasValue=False  ← 예외 없이 사슬 전체를 건너뛴다
(n?.Inner).Count → NullReferenceException  ← 괄호가 단락을 끊는다
z 가 null 일 때 '인자 A' 가 찍혔나? ↑
   [평가됨] 인자 B
   Take(1) 실행
arr?[0]  → HasValue=False
arr2?[1] → 8
```

- ★★★ **`n?.Inner.Count` 가 예외 없이 「값 없음」이 됐다.**\
  `n` 이 널이면 **`.Inner` 도 `.Count` 도 평가하지 않는다** — **`?` 하나가 사슬 전체를 덮는다.**\
  ★ 그래서 **`a` 만 널일 수 있고 `b`·`c` 는 널이 아니라면 `a?.b.c` 로 충분하다.**
- ★★★ **`(n?.Inner).Count` 는 `NullReferenceException` 이다.**\
  괄호가 **「조심하는 구간」의 끝**을 정한다. 괄호를 닫는 순간 그냥 `null` 값이 되고, 그 위의 `.Count` 는 평범한 역참조다.\
  ★ **리팩토링에서 괄호를 넣다가 이것을 만든다** — 겉보기에 같은 식인데 하나는 널을 돌려주고 하나는 터진다.
- ★★ **`?[]` 도 같다** — `arr?[0]` 이 「값 없음」이고 `arr2?[1]` 이 `8` 이다.
- ★ **인덱스가 범위를 벗어나면 그것은 그대로 던진다** — `?[]` 가 막는 것은 **널뿐**이다.\
  ★ **이 문서는 그것을 안 던졌다**(Learn 의 서술로만 안다).

### (3) ★★★ 인자는 평가조차 되지 않는다

**언제 쓰나** — 「`?.` 가 예외를 잡아 주는 건가?」를 스스로 반증할 때.

(2)의 블록 가운데 두 줄이 이 질문의 답이다.

```text
   z?.Take(Loud("인자 A"));      ← z 가 null  →  '인자 A' 가 한 번도 안 찍혔다
   y?.Take(Loud("인자 B"));      ← y 가 객체  →  '인자 B' 와 Take(1) 이 찍혔다
```

- ★★★ **`[평가됨] 인자 A` 가 출력에 없다.** `Loud("인자 A")` 는 **호출조차 되지 않았다.**
- ★★★ **그래서 `?.` 는 「예외를 잡는 것」이 아니라** 「**실행을 건너뛰는 것**」이다.\
  `try { z.Take(Loud(…)); } catch (NullReferenceException) { }` 였다면 **`Loud` 는 이미 실행됐을 것**이다.\
  ★ **부작용이 있는 인자를 넘길 때 이 차이가 버그가 된다** — 카운터를 올리거나 큐에서 꺼내는 인자라면.
- ★ **`&&`·`||` 와 같은 집안**이다. 「단락 평가」라는 말이 그 뜻이다.
- ★★ Learn 이 못 박은 성질 하나 — **`?.` 는 왼쪽 피연산자를 한 번만 평가한다.**\
  확인한 뒤에 다른 스레드가 널로 바꿔도 **이미 읽어 둔 값을 쓴다.** (8)의 IL 이 그것을 보인다.

### (4) `??` 와 `??=` — 오른쪽은 필요할 때만 평가된다

**언제 쓰나** — 기본값을 주는 자리. 그리고 「지연 초기화」 관용구.

```text
===== 소스: cs07b-coalesce.cs =====
#nullable enable
using System;

string? p = null, q = null;
Console.WriteLine($"p ?? q ?? \"끝\"  = {p ?? q ?? "끝"}");

string? r = null;
r ??= Loud("첫 대입");
r ??= Loud("둘째 대입");
Console.WriteLine($"r = {r}   ← 두 번째 오른쪽은 평가조차 안 됐다");

Console.WriteLine($"Pick() ?? \"기본\" = {Pick() ?? "기본"}");

int? maybe = null;
int fixed1 = maybe ?? -1;
Console.WriteLine($"int? null ?? -1 = {fixed1}  (정적 타입 {Name(fixed1)})");

Box b = new Box();
Console.WriteLine($"b.S 는 {(b.S is null ? "null" : b.S)}");
b.S ??= "채움";
Console.WriteLine($"b.S ??= \"채움\" 뒤 → {b.S}");
b.S ??= "다시";
Console.WriteLine($"b.S ??= \"다시\" 뒤 → {b.S}");

static string Loud(string s) { Console.WriteLine($"   [평가됨] {s}"); return s; }
static string? Pick() { Console.WriteLine("   [평가됨] Pick()"); return null; }
static string Name<T>(T _) => typeof(T).Name;

public class Box { public string? S; }
===== csc -out:ex.dll cs07b-coalesce.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
p ?? q ?? "끝"  = 끝
   [평가됨] 첫 대입
r = 첫 대입   ← 두 번째 오른쪽은 평가조차 안 됐다
   [평가됨] Pick()
Pick() ?? "기본" = 기본
int? null ?? -1 = -1  (정적 타입 Int32)
b.S 는 null
b.S ??= "채움" 뒤 → 채움
b.S ??= "다시" 뒤 → 채움
```

- **`p ?? q ?? "끝"`** 에서 앞 둘이 널이라 `"끝"` 이 나왔다.
- ★★★ **`r ??= Loud("첫 대입")` 다음의 `r ??= Loud("둘째 대입")` 에서 `[평가됨] 둘째 대입` 이 안 찍혔다.**\
  `r` 이 이미 차 있으므로 **오른쪽을 평가하지 않는다.**\
  ★ **이것이 지연 초기화 관용구가 성립하는 이유**다 — `_cache ??= ExpensiveBuild()` 가 **한 번만** 빌드한다.
- ★ **`Pick()` 은 평가됐다** — `??` 의 **왼쪽은 언제나 평가된다.** 널인지 알아야 하니 당연하다.
- ★★ **`int? null ?? -1` 의 정적 타입이 `Int32`** 다 — (1)에서 본 「겹을 벗긴다」가 여기서도 나온다.
- ★ **필드에도 쓴다** — `b.S ??= "채움"` 뒤에 `b.S ??= "다시"` 를 해도 `채움` 그대로다.

### (5) ★★★ `??` 는 오른쪽 결합이다 — 그것을 「열 번호」가 증명한다

**언제 쓰나** — 「`a ?? b ?? c` 가 어떻게 묶이나」를 **출력이 아닌 것으로** 증명할 때.

★★ **이것은 출력으로 증명할 수 없다.** 어느 쪽으로 묶어도 값이 같기 때문이다.
그래서 **일부러 컴파일 에러가 나는 식**을 만들고 **에러가 가리키는 열**을 읽는다.

```text
===== 소스: cs07b-assoc.cs =====
int? x = null;
int y = 2;
int? z = 3;
var q1 = x ?? y ?? z;
var q2 = (x ?? y) ?? z;
var q3 = x ?? (y ?? z);
System.Console.WriteLine($"{q1} {q2} {q3}");
===== csc -out:ex.dll cs07b-assoc.cs (cc exit=1) =====
cs07b-assoc.cs(4,15): error CS0019: Operator '??' cannot be applied to operands of type 'int' and 'int?'
cs07b-assoc.cs(5,10): error CS0019: Operator '??' cannot be applied to operands of type 'int' and 'int?'
cs07b-assoc.cs(6,16): error CS0019: Operator '??' cannot be applied to operands of type 'int' and 'int?'
```

```text
   var q1 = x ?? y ?? z;      ← 에러가 (4,15)  =  'y' 가 있는 열
   var q2 = (x ?? y) ?? z;    ← 에러가 (5,10)  =  '(' 가 있는 열
   var q3 = x ?? (y ?? z);    ← 에러가 (6,16)  =  'y' 가 있는 열

        1234567890123456
        var q1 = x ?? y ?? z;
                 ↑    ↑
                열10  열15
```

- ★★★ **q1 의 에러가 `y` 에서 시작한다** — 컴파일러가 **`y ?? z` 를 먼저 묶었다**는 뜻이다.\
  좌결합이었다면 `(x ?? y)` 가 먼저이므로 **열 10** 에서 났을 것이다 — **q2 가 정확히 그렇다.**
- ★★★ **q1 과 q3 이 같은 짝을 지었다**(열 15 와 열 16, 둘 다 `y` 자리).\
  **`a ?? b ?? c` 는 `a ?? (b ?? c)` 와 같은 식**이다. **오른쪽 결합**이 증명됐다.
- ★ **진단 문구는 셋이 같다** — `Operator '??' cannot be applied to operands of type 'int' and 'int?'`.\
  **문구만 보면 셋을 구분할 수 없고, `(행,열)` 이 갈라 준다.**\
  ★★ 「진단의 `(행,열)` 은 안 흔들리는 칸」이라고 머리말에 선언해 둔 것이 여기서 값을 낸다.
- ★ **왜 에러가 나나** — `int y` 는 **널 아님 값 타입**이라 `??` 의 왼쪽에 올 수 없다.\
  일부러 그렇게 만들어 **컴파일러가 어느 짝을 지었는지 실토하게** 한 것이다.

### (6) ★★★ `?.` 의 결과를 비교에 바로 쓰지 마라

**언제 쓰나** — 「길이가 2보다 작으면」 같은 조건을 쓸 때. **실무에서 가장 조용히 틀리는 자리다.**

```text
===== 소스: cs07b-trap.cs =====
#nullable enable
using System;

int[]? numbers = null;

Console.WriteLine($"numbers?.Length 는 값이 있나 : {(numbers?.Length).HasValue}");
Console.WriteLine($"numbers?.Length <  2 : {numbers?.Length < 2}");
Console.WriteLine($"numbers?.Length >= 2 : {numbers?.Length >= 2}");
Console.WriteLine($"둘 다 false 다 — 부정이 성립하지 않는다");
Console.WriteLine($"(numbers?.Length ?? 0) < 2 : {(numbers?.Length ?? 0) < 2}   ← ?? 로 접지해야 뜻대로 된다");
Console.WriteLine();

string? s = null;
Console.WriteLine($"s?.Length == 0 : {s?.Length == 0}");
Console.WriteLine($"s?.Length != 0 : {s?.Length != 0}   ← == 와 != 는 3값이 아니다");
Console.WriteLine();

Console.WriteLine($"s?.ToString()      : '{s?.ToString() ?? "(null)"}'");
int? empty = null;
Console.WriteLine($"int? null 의 ToString() : '{empty.ToString()}' (길이 {empty.ToString()!.Length}) ← null 이 아니라 빈 문자열이다");
===== csc -out:ex.dll cs07b-trap.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
numbers?.Length 는 값이 있나 : False
numbers?.Length <  2 : False
numbers?.Length >= 2 : False
둘 다 false 다 — 부정이 성립하지 않는다
(numbers?.Length ?? 0) < 2 : True   ← ?? 로 접지해야 뜻대로 된다

s?.Length == 0 : False
s?.Length != 0 : True   ← == 와 != 는 3값이 아니다

s?.ToString()      : '(null)'
int? null 의 ToString() : '' (길이 0) ← null 이 아니라 빈 문자열이다
```

- ★★★ **`numbers?.Length < 2` 와 `numbers?.Length >= 2` 가 둘 다 `false`** 다.\
  `numbers` 가 널이라 `numbers?.Length` 가 **「값 없음」인 `int?`** 이고,\
  **`int?` 의 `<`·`>`·`<=`·`>=` 는 한쪽이라도 널이면 `false`** 이기 때문이다([08번](../08-nullable-value-types/)이 정본이다).
- ★★★ **그래서 「부정이 성립하지 않는다」** — `!(a < b)` 가 `a >= b` 가 **아니다.**\
  `if (numbers?.Length < 2) return;` 이라고 쓰면 **널일 때 통과해 버린다.**
- ★★ **고치는 법은 `??` 로 접지하는 것**이다 — `(numbers?.Length ?? 0) < 2` 가 `True` 다.\
  ★ Learn 도 이 형태를 권한다. **(1)에서 본 「`??` 가 겹을 벗긴다」가 여기서 값을 낸다.**
- ★ **`==`·`!=` 는 3값이 아니다** — `s?.Length == 0` 은 `false`, `s?.Length != 0` 은 `true` 다.\
  **`<`·`>` 와 `==` 의 규칙이 다르다.** 같은 「널과의 비교」인데 갈린다.
- ★★ **`int?` 의 `ToString()` 은 널이 아니라 빈 문자열**을 돌려준다 — 길이 0.\
  로그·문자열 결합에서 **「null」 이라고 찍힐 줄 알았는데 아무것도 안 찍히는** 자리다.

### (7) ★ C# 14 — 대입의 왼쪽에도 `?.` 를 쓴다

**언제 쓰나** — 「객체가 있으면 채우고 없으면 넘어가라」를 `if` 없이 쓸 때.

```text
===== 소스: cs07b-c14.cs =====
#nullable enable
using System;

Person? nobody = null;
nobody?.Name = Loud("오른쪽 A");
Console.WriteLine("nobody 가 null 일 때 '오른쪽 A' 가 찍혔나? ↑");

Person somebody = new Person();
somebody?.Name = Loud("오른쪽 B");
Console.WriteLine($"somebody.Name = {somebody.Name}");

int[]? missing = null;
missing?[0] = Count("오른쪽 C");
Console.WriteLine("missing 이 null 일 때 '오른쪽 C' 가 찍혔나? ↑");

int[] present = new int[2];
present?[0] = Count("오른쪽 D");
Console.WriteLine($"present[0] = {present[0]}");

Person? maybe = null;
maybe?.Score += Count("오른쪽 E");
Console.WriteLine("복합 대입도 같다 — '오른쪽 E' 가 찍혔나? ↑");

static string Loud(string s) { Console.WriteLine($"   [평가됨] {s}"); return s; }
static int Count(string s) { Console.WriteLine($"   [평가됨] {s}"); return 1; }

public class Person { public string Name = ""; public int Score; }
===== csc -out:ex.dll cs07b-c14.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
cs07b-c14.cs(10,38): warning CS8602: Dereference of a possibly null reference.
cs07b-c14.cs(18,35): warning CS8602: Dereference of a possibly null reference.
nobody 가 null 일 때 '오른쪽 A' 가 찍혔나? ↑
   [평가됨] 오른쪽 B
somebody.Name = 오른쪽 B
missing 이 null 일 때 '오른쪽 C' 가 찍혔나? ↑
   [평가됨] 오른쪽 D
present[0] = 1
복합 대입도 같다 — '오른쪽 E' 가 찍혔나? ↑
```

- **`nobody?.Name = Loud("오른쪽 A")` 에서 `[평가됨] 오른쪽 A` 가 안 찍혔다.**\
  ★★★ **왼쪽이 널이면 오른쪽도 평가하지 않는다.** (3)의 성질이 대입에도 그대로 적용된다.
- **`missing?[0] = …` 도 같다**(`?[]` 판).
- ★ **복합 대입도 된다** — `maybe?.Score += …` 에서 오른쪽이 평가되지 않았다.
- ★★ **`++`·`--` 는 여전히 안 된다** — 문법 절의 금지 사례에 그 진단이 있다.\
  ★ Learn 이 못 박은 이유는 **널 조건 식이 「변수」로 분류되지 않기 때문**이다 —\
  같은 이유로 `ref`/`out` 인자로도 못 넘긴다.
- ★ **이 문서는 `-langversion:latest` 로 던졌다.** 옛 언어 버전에서는 이 절 전체가 컴파일 에러다.

### (8) ★★ IL — `?.` 는 `if` 로 펼쳐지고 `??` 는 왼쪽을 한 번만 읽는다

**언제 쓰나** — 「단락이 진짜인가」·「스레드 안전이 무슨 뜻인가」를 명령 수준에서 확인할 때.

```text
===== 소스: cs07b-il.cs =====
#nullable enable
Il.Dump(typeof(Probe), "Cond");
Il.Dump(typeof(Probe), "Manual");
Il.Dump(typeof(Probe), "Chain");
Il.Dump(typeof(Probe), "Coalesce");
Il.Dump(typeof(Probe), "Assign");

public static class Probe {
    public static int?   Cond(Node? n)      => n?.Count;
    public static int?   Manual(Node? n)    => n == null ? (int?)null : n.Count;
    public static int?   Chain(Node? n)     => n?.Inner.Count;
    public static string Coalesce(string? s) => s ?? "기본";
    public static void   Assign(Box b)      { b.S ??= "기본"; }
}
public class Node  { public int Count; public Inner Inner = new Inner(); }
public class Inner { public int Count; }
public class Box   { public string? S; }
===== csc -r:il.dll -out:ex.dll cs07b-il.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
--- Probe.Cond ---
  .locals [0] System.Nullable<System.Int32>
  IL_0000: ldarg.0
  IL_0001: brtrue.s IL_000e
  IL_0003: ldloca.s 0
  IL_0005: initobj System.Nullable<System.Int32>
  IL_000b: ldloc.0
  IL_000c: br.s IL_0019
  IL_000e: ldarg.0
  IL_000f: ldfld Node::Count
  IL_0014: newobj System.Nullable<System.Int32>::.ctor
  IL_0019: ret
--- Probe.Manual ---
  .locals [0] System.Nullable<System.Int32>
  IL_0000: ldarg.0
  IL_0001: brfalse.s IL_0010
  IL_0003: ldarg.0
  IL_0004: ldfld Node::Count
  IL_0009: newobj System.Nullable<System.Int32>::.ctor
  IL_000e: br.s IL_0019
  IL_0010: ldloca.s 0
  IL_0012: initobj System.Nullable<System.Int32>
  IL_0018: ldloc.0
  IL_0019: ret
--- Probe.Chain ---
  .locals [0] System.Nullable<System.Int32>
  IL_0000: ldarg.0
  IL_0001: brtrue.s IL_000e
  IL_0003: ldloca.s 0
  IL_0005: initobj System.Nullable<System.Int32>
  IL_000b: ldloc.0
  IL_000c: br.s IL_001e
  IL_000e: ldarg.0
  IL_000f: ldfld Node::Inner
  IL_0014: ldfld Inner::Count
  IL_0019: newobj System.Nullable<System.Int32>::.ctor
  IL_001e: ret
--- Probe.Coalesce ---
  IL_0000: ldarg.0
  IL_0001: dup
  IL_0002: brtrue.s IL_000a
  IL_0004: pop
  IL_0005: ldstr "기본"
  IL_000a: ret
--- Probe.Assign ---
  .locals [0] Box
  IL_0000: nop
  IL_0001: ldarg.0
  IL_0002: stloc.0
  IL_0003: ldloc.0
  IL_0004: ldfld Box::S
  IL_0009: brtrue.s IL_0016
  IL_000b: ldloc.0
  IL_000c: ldstr "기본"
  IL_0011: stfld Box::S
  IL_0016: ret
```

| 메서드 | 무엇을 보이나 |
|---|---|
| `Cond`(`n?.Count`) | `brtrue.s` 로 갈라 **한쪽은 `initobj`(값 없음), 한쪽은 `ldfld` + `newobj Nullable<int>::.ctor`** |
| `Manual`(`n == null ? … : …`) | ★ **거의 같은 IL** — 분기 방향(`brfalse.s`)만 뒤집혔다 |
| `Chain`(`n?.Inner.Count`) | ★★★ **`ldfld Inner` 와 `ldfld Count` 가 둘 다 널 아님 쪽에만** 있다 |
| `Coalesce`(`s ?? "기본"`) | ★★ **`dup` · `brtrue.s` · `pop`** — 왼쪽을 **한 번만** 읽는다 |
| `Assign`(`b.S ??= "기본"`) | ★ **`ldfld` 한 번 읽고 `brtrue.s`**, 널일 때만 `stfld` |

- ★★★ **`Chain` 이 (2)를 명령으로 증명한다** — `n` 이 널인 경로에는 `ldfld` 가 **하나도 없다.**\
  「사슬 전체를 건너뛴다」가 **생성된 코드의 성질**이지 런타임의 배려가 아니다.
- ★★ **`Cond` 와 `Manual` 이 거의 같다** — `?.` 는 **문법 설탕**이고, 손으로 쓴 `if` 와 같은 코드로 풀린다.\
  ★ 「`?.` 가 느리다」는 주장이 설 자리가 없다. **이 문서는 시간을 안 쟀지만, 명령이 같다는 것은 보였다.**
- ★★★ **`Coalesce` 의 `dup`** 이 「왼쪽을 한 번만 평가한다」를 증명한다.\
  스택에 올린 값을 **복제해서** 검사하고, 널이면 `pop` 하고 기본값을 올린다.\
  ★ **그래서 `handler?.Invoke()` 가 이벤트 호출의 스레드 안전 관용구**가 된다 —\
  검사한 값과 호출하는 값이 **같은 값**임이 명령 수준에서 보장된다(Learn 이 못 박은 성질이다).
- ★ **`Assign` 도 `ldfld` 가 한 번**이다 — `??=` 가 필드를 두 번 읽지 않는다.

## 문법 — 형태와 규칙

**형태** — 던져서 확인한 것만 싣는다.

```text
===== 소스: cs07b-form.cs =====
#nullable enable
using System;

Node? node = null;
int[]? arr = null;

Console.WriteLine($"node?.Name          : {node?.Name ?? "(null)"}");
Console.WriteLine($"node?.Count         : HasValue={(node?.Count).HasValue}");
Console.WriteLine($"arr?[0]             : HasValue={(arr?[0]).HasValue}");
Console.WriteLine($"node?.Name ?? \"기본\" : {node?.Name ?? "기본"}");

string? text = null;
text ??= "채움";
Console.WriteLine($"text ??= \"채움\"      : {text}");

Node real = new Node { Name = "이름", Count = 3 };
Console.WriteLine($"real?.Name?.Length  : {real?.Name?.Length}");
Console.WriteLine($"real?.Sub?.Deep     : {real?.Sub?.Deep ?? "(null)"}");

// 이벤트·델리게이트의 스레드 안전 호출 관용구
Action? handler = null;
handler?.Invoke();
Console.WriteLine("handler?.Invoke() — null 이어도 예외가 아니다");
handler += () => Console.WriteLine("   구독자 실행");
handler?.Invoke();

// C# 14 — 널 조건 대입
Node? nobody = null;
nobody?.Name = "안 들어간다";
Console.WriteLine($"nobody 는 여전히 {(nobody is null ? "null" : "객체")}");

public class Node { public string? Name; public int Count; public Sub? Sub; }
public class Sub { public string Deep = "깊은 값"; }
===== csc -out:ex.dll cs07b-form.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
node?.Name          : (null)
node?.Count         : HasValue=False
arr?[0]             : HasValue=False
node?.Name ?? "기본" : 기본
text ??= "채움"      : 채움
real?.Name?.Length  : 2
real?.Sub?.Deep     : (null)
handler?.Invoke() — null 이어도 예외가 아니다
   구독자 실행
nobody 는 여전히 null
```

- ★ **`handler?.Invoke()`** 가 이 주제의 대표 관용구다 — 구독자가 없어도 예외가 아니다((8)).
- ★ **`real?.Sub?.Deep` 이 `(null)`** 인 것에 주의하라 — `Sub` 가 널이라 **두 번째 `?`** 가 일한 것이다.\
  `real?.Sub.Deep` 이었으면 **터졌을 것**이다. **널일 수 있는 자리마다 `?` 가 필요하다.**

**금지 사례 — 던져서 받은 것**

```text
===== 소스: cs07b-forbid.cs =====
#nullable enable

Node? n = null;
int count = n?.Count;          // int? 를 int 에 암묵으로 — 못 한다
string s = n?.Name;            // string? 를 string 에 — 경고만
n?.Count++;                    // 널 조건 접근에 ++ 는 C# 14 에서도 안 된다
System.Console.WriteLine($"{count} {s}");

public class Node { public string? Name; public int Count; }
===== csc -out:ex.dll cs07b-forbid.cs (cc exit=1) =====
cs07b-forbid.cs(4,13): error CS0266: Cannot implicitly convert type 'int?' to 'int'. An explicit conversion exists (are you missing a cast?)
cs07b-forbid.cs(6,1): error CS1059: The operand of an increment or decrement operator must be a variable, property or indexer
cs07b-forbid.cs(4,13): warning CS8629: Nullable value type may be null.
cs07b-forbid.cs(5,12): warning CS8600: Converting null literal or possible null value to non-nullable type.
```

| 쓴 것 | 진단 | 무엇을 말하나 |
|---|---|---|
| `int count = n?.Count;` | ``error CS0266: Cannot implicitly convert type 'int?' to 'int'`` | ★★★ **(1)의 「한 겹」이 여기서 에러로 드러난다** |
| `string s = n?.Name;` | ``warning CS8600`` | ★ 참조 타입은 **경고**다 — [06번](../06-nullable-reference-types/)의 규칙이 적용된다 |
| `n?.Count++;` | ``error CS1059: The operand of an increment or decrement operator must be a variable, property or indexer`` | ★★ **널 조건 식은 「변수」가 아니다** — C# 14 에서도 `++` 는 안 된다 |
| — | ``warning CS8629: Nullable value type may be null.`` | ★ **값 타입 쪽 경고 번호는 따로 있다**(`CS8602` 가 아니다) |

- ★★★ **같은 실수가 값 타입에서는 에러이고 참조 타입에서는 경고다.**\
  `int?` 는 **진짜 타입**이라 변환이 없으면 컴파일이 안 되고([08번](../08-nullable-value-types/)),\
  `string?` 은 **주석**이라 경고로 끝난다([06번](../06-nullable-reference-types/)).\
  ★ **06 → 07 → 08 사슬이 한 블록에서 전부 보이는 자리**다.

**규칙**

- **`?.`·`?[]` 는 단락한다** — 사슬 중 하나가 널이면 **나머지를 평가하지 않는다**((2)·(3)).
- **괄호는 단락을 끊는다** — `(a?.b).c` 는 보호되지 않는다((2)).
- **결과 타입은** 「**한 겹 널 허용**」이다 — 멤버가 값 타입 `T` 면 `T?`, 참조 타입이면 그대로((1)).
- **`?.` 는 왼쪽을 한 번만 평가한다**((8)) — 그래서 이벤트 호출에 안전하다.
- **`??` 는 오른쪽 결합**이고((5)), **왼쪽이 널일 때만 오른쪽을 평가**한다.
- **`??` 의 왼쪽은 널이 될 수 있는 것**이라야 한다 — 널 아님 값 타입이면 `CS0019` 다((5)).
- **`??=` 는 왼쪽이 널일 때만 대입**하고 그때만 오른쪽을 평가한다((4)).
- **C# 14 의 널 조건 대입**은 참조 타입 대상에서 `=` 와 복합 대입에만 되고 **`++`·`--` 는 안 된다**((7)).

## 어디서 틀리나

1. ★★★ **`?.` 의 결과를 `int` 에 바로 넣으려는 것** — `CS0266` 이다(문법 절). **한 겹이 붙는다**((1)).
2. ★★★ **`arr?.Length < 2` 를 「널이면 참」으로 읽는 것** — **`false`** 다((6)).\
   **부정도 성립하지 않는다.** `(arr?.Length ?? 0) < 2` 로 접지해야 한다.
3. ★★★ **`(a?.b).c` 로 괄호를 치는 것** — 단락이 끊긴다((2)). **리팩토링 중에 생긴다.**
4. ★★ **`?.` 가 예외를 잡아 준다고 믿는 것** — 잡는 게 아니라 **실행을 안 한다**((3)).\
   부작용이 있는 인자를 넘기면 그 부작용도 안 일어난다.
5. ★★ **`a?.b?.c` 에서 `?` 를 하나 빠뜨리는 것** — **널일 수 있는 자리마다** 필요하다(문법 절).
6. ★ **`?[]` 가 범위 초과도 막아 줄 거라고 믿는 것** — **널만** 막는다.
7. ★ **`int?` 의 `ToString()` 이 `"null"` 을 준다고 믿는 것** — **빈 문자열**이다((6)).
8. ★★ **`??=` 의 오른쪽이 매번 평가된다고 믿는 것** — 안 된다((4)). **지연 초기화가 성립하는 근거**다.
9. ★ **`??` 를 좌결합으로 읽는 것** — 오른쪽 결합이다((5)). 타입이 섞이면 결과가 갈린다.
10. ★★ **`?.` 로 널을 「처리했다」고 생각하는 것** — **미룬 것**이다.\
    `a?.b?.c?.d` 는 어디서 널이 됐는지 **알려 주지 않는다.** 진단이 필요한 자리에서는 `if` 가 낫다.

## 구현 세부사항 대 언어 보장

| 층 | 무엇을 말하나 | 이 주제의 예 |
|---|---|---|
| **언어 명세(ECMA-334)** | 무엇이 **언제나** 참인가 | 단락 평가 · 결과 타입이 `T?` 가 되는 것 · `??` 의 오른쪽 결합 · **왼쪽을 한 번만 평가하는 것** · 괄호가 단락을 끊는 것 |
| **정적 분석(Roslyn)** | 컴파일러가 어디까지 추론하나 | `CS8629`·`CS8600` 이 나는 정확한 자리(문법 절) — [06번](../06-nullable-reference-types/)의 축이다 |
| **런타임(CoreCLR) 구현** | 이 판이 **지금** 그렇게 하는 것 | `NullReferenceException` 메시지·종료 코드 134 |
| **이 판의 관찰** | 돌려 봤더니 이랬다는 것 | ★ **IL 의 정확한 명령 열**((8)) · 진단의 `(행,열)`((5)) · `nop` 의 유무 |

**언어가 보장하는 것**(구현이 바뀌어도 같다)

- **`?.`·`?[]` 가 단락하는 것** — 사슬의 나머지와 **인자까지** 평가하지 않는다.
- **괄호가 단락을 끊는 것** — `(a?.b).c` 는 보호되지 않는다.
- **멤버가 널 아님 값 타입 `T` 면 결과가 `T?`** 인 것.
- ★★ **`?.` 가 왼쪽 피연산자를 한 번만 평가하는 것** — 이것이 **명세의 보장**이라 이벤트 관용구가 성립한다.
- **`??` 가 오른쪽 결합이고 왼쪽이 널일 때만 오른쪽을 평가하는 것.**
- **`??=` 가 왼쪽이 널일 때만 대입·평가하는 것.**
- **C# 14 의 널 조건 대입에서 왼쪽이 널이면 오른쪽을 평가하지 않는 것**, 그리고 **`++`·`--` 가 금지인 것.**

**구현(Roslyn)에 달린 것**

- ★ **IL 의 정확한 명령 열**((8)) — `dup`/`pop` 을 쓸지 지역 변수를 쓸지는 컴파일러가 고른다.\
  ★★ **다만 「왼쪽을 한 번만 평가한다」는 언어 보장**이므로, **명령이 바뀌어도 그 성질은 안 바뀐다.**\
  **무엇이 근거이고 무엇이 관찰인지 갈라 읽어라.**
- **`nop` 의 유무** — `-optimize` 를 안 준 결과다.
- **진단 문구와 `(행,열)`** — 다만 (5)의 **열 번호가 어느 토큰을 가리키나**는 문법이 정한 결합 방향의 귀결이다.

## 언제 쓰고 언제 안 쓰나

| 쓸 것 | 언제 | 안 쓸 때 |
|---|---|---|
| **`a?.b`** | 널이 **정상 상태**인 자리 — 선택적 설정·빈 컬렉션 | 널이 **버그**인 자리 — 거기서는 터져야 원인을 안다 |
| **`a?.b.c`** | `a` 만 널일 수 있을 때 | `b` 도 널일 수 있으면 `a?.b?.c` 라야 한다 |
| **`handler?.Invoke()`** | ★★ 이벤트 발생 — **관용구다**((8)) | — |
| **`x ?? 기본값`** | 기본값이 **명확한** 자리 | 기본값이 「어쩔 수 없이 고른 것」이면 오히려 버그를 숨긴다 |
| **`_cache ??= Build()`** | ★ 지연 초기화 — 한 번만 평가된다((4)) | **여러 스레드**가 동시에 들어오는 자리(이것은 원자적이지 않다) |
| **`a?.B = x`**(C# 14) | 「있으면 채워라」 | — |
| **`if (a is null) …`** | ★★ **널의 원인을 알아야 할 때** | — |

- ★★★ **`?.` 를 길게 잇는 것은 대개 설계 신호다.** `a?.b?.c?.d?.e` 가 널을 돌려줬을 때\
  **어디서 끊겼는지 알 수 없다.** 진단이 필요하면 `if` 로 풀고 각 단계에 메시지를 붙여라.
- ★★ **「널이면 그냥 넘어간다」가 맞는 자리인지 매번 물어라.** `?.` 는 널을 **처리한 것이 아니라 미룬 것**이다.\
  미룬 널은 **더 먼 곳에서 다시 나타난다** — 그때는 원인이 안 보인다.
- ★ **`??` 로 기본값을 주는 것과 예외를 던지는 것 중 무엇이 맞나** — 값이 **없어도 되는 것**이면 `??`,\
  **있어야 하는 것**이면 `ArgumentNullException.ThrowIfNull` 이다.

## 핵심 문장

1. ★★★ **`?.` 는 결과 타입에 한 겹을 붙인다** — `int` 가 `int?` 가 되고, 참조 타입에는 안 붙는다.
2. ★★★ **`?.` 는 사슬 전체를 건너뛴다** — 중간에서 멈추는 것이 아니고, **인자도 평가하지 않는다.**
3. ★★★ **괄호가 단락을 끊는다** — `(a?.b).c` 는 보호되지 않고 터진다.
4. ★★ **`?.` 의 결과를 `<`·`>` 에 바로 쓰지 마라** — 널이면 **양쪽이 다 `false`** 다. `??` 로 접지하라.
5. ★★ **`??` 는 오른쪽 결합이다** — 그리고 그것을 **컴파일 에러의 열 번호**가 증명한다.
6. ★★ **`??=` 의 오른쪽은 필요할 때만 평가된다** — 지연 초기화 관용구가 여기서 나온다.
7. ★ **`?.` 는 왼쪽을 한 번만 평가한다** — IL 의 `dup` 이 그것이고, 이벤트 호출 관용구의 근거다.

## 관련 자료

- [06번 — 널 허용 참조 타입](../06-nullable-reference-types/) — **왜 `?` 를 붙이나**의 정본. 이 주제의 **앞**이다.
- [08번 — 널 허용 값 타입 `Nullable<T>`](../08-nullable-value-types/) — **`int?` 가 무엇인가**의 정본.\
  ★★★ (1)의 「한 겹」과 (6)의 「양쪽이 다 `false`」가 **거기서 설명된다.** 이 주제의 **뒤**다.
- [01번 — 값 타입과 참조 타입](../01-value-types-and-reference-types/) — 왜 값 타입에만 겹이 붙나.
- [05번 — 숫자 타입](../05-numeric-types-checked-decimal/) — `int` 가 왜 널을 못 담나(값 타입이라서).
- 목록의 **14번 주제**(인덱서) — `?[]` 가 인덱서에도 적용된다.
- 목록의 **21번 주제**(패턴 매칭) — `is null`·`is not null` 이 `== null` 과 갈리는 자리.
- 목록의 **27번·29번 주제**(델리게이트·이벤트) — `handler?.Invoke()` 관용구의 정본.
- **Kotlin 의 [널 안전 타입 편](../../../kotlin/syntax/03-null-safe-types/)** — `?.` 와 엘비스 `?:` 가 있다.\
  ★ **기호는 비슷한데 타입 규칙이 다르다** — Kotlin 에는 `Int?` 와 `Int` 의 구분이 **박싱**과 얽혀 있다.
- **TS 의 [`any`·`unknown`·`never`·`void` 편](../../../ts/syntax/04-any-unknown-never-void/)** — `?.`·`??` 를 그대로 갖고 있다.\
  ★ 거기는 **런타임 검사가 실제로 생성된다**(트랜스파일 결과에 `!== null` 이 남는다).

## 용어 풀이

- **널 조건 연산자 `?.` / `?[]`** — 왼쪽이 널이 아닐 때만 접근하고, 널이면 사슬 전체를 건너뛴다.
- **단락 평가** — 앞의 결과에 따라 **뒤를 아예 실행하지 않는 것**. 예외 처리와 다르다.
- **널 병합 연산자 `??`** — 왼쪽이 널이면 오른쪽. **오른쪽 결합**이다.
- **널 병합 대입 `??=`** — 왼쪽이 널일 때만 대입. **C# 8부터.**
- **널 조건 대입** — 대입의 왼쪽에 쓰는 `?.`. **C# 14부터.** `++`·`--` 는 제외다.
- **리프티드(lifted) 결과 타입** — 값 타입 멤버에 `?.` 를 쓸 때 붙는 `Nullable<T>` 한 겹.
- **`CS0266`** — `int?` 를 `int` 에 암묵 변환할 수 없다(값 타입 쪽 **에러**).
- **`CS8629`** — 널 허용 값 타입이 널일 수 있다(값 타입 쪽 **경고**).
- **`CS1059`** — `++`/`--` 의 피연산자가 변수·속성·인덱서라야 한다.
- **`dup` / `pop`** — 스택 위 값을 복제·제거하는 IL 명령. `??` 가 왼쪽을 한 번만 읽는 근거((8)).

## 더 들어가면

- **`?.` 와 확장 메서드** — 확장 메서드는 **`this` 가 널이어도 호출된다.**\
  그래서 `list?.MyExtension()` 과 `list.MyExtension()` 이 다르게 동작한다. **이 문서는 안 던졌다.**
- **`??` 와 `throw` 식**(C# 7) — `x ?? throw new ArgumentNullException(nameof(x))` 관용구. **안 던졌다.**
- **`ArgumentNullException.ThrowIfNull`**(.NET 6) — 널 검사의 현대적 형태. **안 던졌다.**
- **`?.` 와 `await`** — `task?.ConfigureAwait(false)` 의 결과가 널일 수 있어 `await` 가 막힌다. **안 던졌다.**
- **`??=` 의 원자성** — **원자적이지 않다.** 여러 스레드가 동시에 들어오면 오른쪽이 여러 번 평가될 수 있다.\
  ★ **이 문서는 단일 스레드에서만 던졌다** — 「안 터졌다」가 「안전하다」가 아니다.
- **패턴 매칭과의 경계** — `is null` 은 **`==` 오버로드를 무시한다.** 연산자를 오버로드한 타입에서 갈린다.
