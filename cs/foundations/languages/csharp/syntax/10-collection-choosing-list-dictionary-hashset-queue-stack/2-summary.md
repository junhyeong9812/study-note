# csharp/syntax/10 — 컬렉션 선택: `List`·`Dictionary`·`HashSet`·`Queue`/`Stack` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [ECMA-334 7판(2023-12)](https://ecma-international.org/publications-and-standards/standards/ecma-334/) ·
> [.NET API — `List<T>`](https://learn.microsoft.com/en-us/dotnet/api/system.collections.generic.list-1) ·
> [.NET API — `Dictionary<TKey,TValue>`](https://learn.microsoft.com/en-us/dotnet/api/system.collections.generic.dictionary-2) ·
> [.NET API — `HashSet<T>`](https://learn.microsoft.com/en-us/dotnet/api/system.collections.generic.hashset-1) ·
> [.NET API — `Queue<T>`](https://learn.microsoft.com/en-us/dotnet/api/system.collections.generic.queue-1) ·
> [.NET API — `Stack<T>`](https://learn.microsoft.com/en-us/dotnet/api/system.collections.generic.stack-1) ·
> [.NET API — `Object.GetHashCode`](https://learn.microsoft.com/en-us/dotnet/api/system.object.gethashcode)
> **실행 검증** — 이 문서의 모든 출력·진단·IL·할당 바이트는 아래 「이 판」의 도구로 **실제로 돌려 얻은 것**이다(2026-09-25).\
> ★ 블록은 캡처 스크립트가 파일로 받아 조립기가 끼워 넣은 것이다 — 사람이 옮겨 적은 줄은 하나도 없다.\
> ★ 소스 펜스의 배너도 **캡처가 찍은 것**이다. 원고에 손으로 쓴 배너는 없다.\
> ★★★ **진단 언어를 영어로 고정했다.** 안 그러면 **로캘을 따라 한국어로 나와 재현이 안 된다** —\
> 환경변수 **`DOTNET_CLI_UI_LANGUAGE=en`** 과 `csc` 플래그 **`-preferreduilang:en-US`** 를 같이 건다.
> **던진 형태** — MSBuild(`dotnet build`·`dotnet run`)를 **안 썼다.** Roslyn 컴파일러를 **직접** 부른다 —\
> 그래야 `bin/`·`obj/` 가 안 생기고, 진단 경로가 **절대 경로가 아니라 파일명**으로 나오며, 한 판이 0.3초 안에 끝난다.\
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
>           -preferreduilang:en-US -langversion:latest -target:exe "$@"; }
> ```
>
> **`-debug` 를 안 줬다** — PDB 가 없으면 스택 트레이스에 **절대 경로와 줄 번호가 안 박힌다**.
> **IL 은 외부 도구 없이 본다** — `ilspycmd`·`ildasm` 을 안 깔았다.
> [03번](../03-boxing-and-unboxing/)의 (0)절에 있는 **`cs-il.cs` 전문**을 그대로 써서
> `csc -target:library -out:il.dll cs-il.cs` 로 만들어 두고 `-r:il.dll` 로 참조한다.
> **버전** — 제네릭 컬렉션 넷은 **.NET Framework 2.0 / C# 2.0부터**.
> `Dictionary.TryAdd`·`Queue.TryDequeue`·`Stack.TryPop` 은 **.NET Core 2.0부터**,
> **순회 중 `Remove` 허용**은 **.NET Core 3.0부터**((9)), `HashSet.Capacity`·`Dictionary.Capacity` 는 **.NET 9부터**,
> `PriorityQueue<TElement,TPriority>` 는 **.NET 6부터**다.
> **경계** — **자료구조의 원리**(동적 배열이 왜 두 배로 늘리나 · 해시 표의 버킷·충돌·적재율 · 스택/큐의 정의)는
> [`data-structure/01-dynamic-array/`](../../../../../data-structure/01-dynamic-array/) ·
> [`03-stack/`](../../../../../data-structure/03-stack/) ·
> [`04-queue-deque/`](../../../../../data-structure/04-queue-deque/) ·
> [`05-hashmap/`](../../../../../data-structure/05-hashmap/)가 정본이다.\
> ★ **그쪽은 「왜 그 구조인가」까지, 여기는 「.NET 에서 무엇을 고르고 무엇이 보장인가」부터**다.\
> **박싱 자체**는 [03번](../03-boxing-and-unboxing/), **배열과 슬라이싱**은 [09번](../09-arrays-index-and-range/)이 정본이다.\
> **컬렉션 초기화와 컬렉션 식**은 목록의 **11번 주제**, **`Equals`/`GetHashCode` 계약의 설계**는 **19번 주제**,
> **`IEnumerable<T>` 와 `foreach` 의 풀림**은 **31번 주제**, **제네릭 자체**는 **24번 주제**가 정본이다.
> **대비** — Go 갈래 목록([`go/syntax/README.md`](../../../go/syntax/README.md))의 **9번**([`09-maps-declaration-comma-ok-delete-and-iteration-order/`](../../../go/syntax/09-maps-declaration-comma-ok-delete-and-iteration-order/)) ·
> Python 갈래 목록([`python/syntax/README.md`](../../../python/syntax/README.md))의 **12번**([`12-dict-and-key-requirements/`](../../../python/syntax/12-dict-and-key-requirements/)) ·
> Rust 갈래 목록([`rust/syntax/README.md`](../../../rust/syntax/README.md))의 **28번**([`28-partialeq-eq-partialord-ord-and-hash-contracts/`](../../../rust/syntax/28-partialeq-eq-partialord-ord-and-hash-contracts/)).

## 이 갈래가 쓰는 세 층

| 층 | 뜻 | 이 주제에서 근거로 쓰는 것 |
|---|---|---|
| **언어 명세(ECMA-334)** | C# 언어가 약속한 것 | 이 주제에는 **거의 없다** — 컬렉션은 언어가 아니라 라이브러리다 |
| **런타임·BCL 구현** | CoreCLR 과 `System.Private.CoreLib` 이 그렇게 하는 것 | Capacity 증가 수열 · 순회 순서 · 비교자 선택 · 할당 바이트 |
| **이 판의 관찰** | .NET 10.0.12 · linux-x64 에서 이번에 본 것 | 실행 출력 · 진단 · IL |

★★★ **이 주제는 세 층이 가장 크게 어긋나는 자리다.** 위 표의 첫 칸이 거의 비어 있다는 것 자체가 결론이다 —\
`Dictionary` 의 순회 순서를 **언어가 말하지 않고 문서도 「순서 없음」이라고만 말하는데,
실행해 보면 다섯 번이고 스무 번이고 한 글자도 같게 나온다.**\
그래서 「돌려 봤더니 같더라」가 **가장 잘 통하고 가장 위험한** 주제다.

## 이 판

```text
===== 명령: dotnet --version && dotnet --list-runtimes | grep NETCore && g++ --version | head -1 (exit=0) =====
10.0.401
Microsoft.NETCore.App 10.0.12 [/home/jun/.local/opt/dotnet/shared/Microsoft.NETCore.App]
g++ (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0
```

## 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| **흔들린다** | ★★★ `"alpha".GetHashCode()` 의 **값** | 문자열 해시가 **프로세스마다 다른 씨앗**으로 뽑힌다((5)) — 그래서 이 값을 본문에 안 싣는다 |
| **흔들린다** | `GC.GetAllocatedBytesForCurrentThread()` 의 **절댓값** | 프로세스 시작부터의 누적이다 |
| **판이 바뀌면 바뀐다** | Capacity 수열 `0→4→8→16`·`0→3→7→17→37→89` | **BCL 구현**이다((2)) — 문서가 약속한 적 없다 |
| **판이 바뀌면 바뀐다** | 순회 순서 그 자체 · 할당 바이트 수(24·40·72·4592·1184) | BCL·CoreCLR 구현이다 |
| 안 흔들린다 | ★★★ **20판을 돌려 센 「가짓수」**((5)) | 같은 판에서 재현된다 — 그래서 **이것**을 근거로 쓴다 |
| 안 흔들린다 | **두 할당 측정 사이의 증분**과 **그 증분이 0 이냐 아니냐** | 같은 판·같은 코드면 같다 |
| 안 흔들린다 | **진단 코드**(`CS0659`)·**진단 문구**·**`(행,열)`** | 컴파일러가 정한다 |
| 안 흔들린다 | **예외 타입과 메시지** · **`cc exit` / `run exit`** | 런타임이 정한다 |
| 안 흔들린다 | **IL 명령어 열**(`box` 가 있나 없나) | 컴파일러가 정한다 |

## 한눈에 — 쉽게 말하면

**컬렉션 넷은 「물건을 어떻게 찾을 것이냐」로 갈린다.** 자료구조가 아니라 **찾는 방법**이 기준이다.

| 비유 | 실체 | 찾는 법 |
|---|---|---|
| **번호표 붙은 책장** | `List<T>` | **몇 번째**로 찾는다 — `list[2]` 는 즉시, `Contains` 는 앞에서부터 |
| **이름표 달린 사물함** | `Dictionary<K,V>` | **이름**으로 찾는다 — 키를 알아야 한다 |
| **회원 명부** | `HashSet<T>` | **있나 없나**만 본다 — 값을 따로 안 들고 있다 |
| **매표소 줄** | `Queue<T>` | **제일 먼저 온 것**만 꺼낸다 |
| **접시 더미** | `Stack<T>` | **제일 나중에 얹은 것**만 꺼낸다 |

```text
   「무엇으로 찾을 건가」 하나로 갈린다

         몇 번째?  ──────────────>  List<T>          list[2]
         이름으로? ──────────────>  Dictionary<K,V>  dict["초록"]
         있나 없나만? ───────────>  HashSet<T>       set.Contains(x)
         먼저 온 것부터? ────────>  Queue<T>         Enqueue / Dequeue
         나중 것부터? ───────────>  Stack<T>         Push / Pop

   ★ 「순서대로 순회하고 싶다」는 이 목록에 없다 —
     List 만 순서가 계약이고, 나머지 넷 중 Dictionary·HashSet 은 순서를 약속하지 않는다.
```

- ★★★ **이 주제의 축은 「보장」과 「관찰」이 어긋나는 자리다.**\
  `Dictionary` 를 다섯 번 돌려도 스무 번 돌려도 순회 순서가 **한 글자도 안 갈린다.**\
  그런데 그것은 보장이 아니다 — **삭제와 추가를 섞으면 그 자리에서 깨진다**((4)).
- ★★ **「안 갈렸다」를 가르는 법이 이 주제의 기술**이다. 여러 번 돌리는 것으로는 안 갈린다.\
  **연산을 섞어야** 갈린다((4)), 그리고 **가짓수를 세야** 「몇 판을 돌렸나」가 근거가 된다((5)).
- ★ **넷의 비용 비교는 전부 할당 바이트로 한다**((8)). 「제네릭이 빠르다」는 말은 이 문서에 없다 —\
  **잰 것은 바이트뿐**이고, 시간은 재지 않았다.

```text
   ★★★ 이 주제의 본체 — Dictionary 의 entries 배열

   d["alpha"]=1 … d["echo"]=5 를 차례로 넣으면

     entries  [0]alpha  [1]bravo  [2]charlie  [3]delta  [4]echo
     순회     alpha → bravo → charlie → delta → echo     ← 「넣은 순서」로 보인다

   d.Remove("bravo")                     [1] 이 빈 자리(free list)가 된다

     entries  [0]alpha  [1]  ○     [2]charlie  [3]delta  [4]echo
     순회     alpha → charlie → delta → echo               ← 아직 「넣은 순서」로 보인다

   d["foxtrot"]=6                        ★ 맨 뒤가 아니라 빈 자리 [1] 로 들어간다

     entries  [0]alpha  [1]foxtrot [2]charlie  [3]delta  [4]echo
     순회     alpha → foxtrot → charlie → delta → echo    ★ 여기서 깨진다
```

> **보장(guarantee)** — 명세나 문서가 **약속한 것**. 판이 바뀌어도 지켜진다.\
> 예: `List<T>` 의 인덱서가 넣은 자리의 값을 준다는 것.

> **관찰(observation)** — 이번에 **돌려 보니 그랬던 것**. 다음 판에 바뀌어도 아무도 사과하지 않는다.\
> 예: `Dictionary` 를 스무 번 돌려 순회 순서가 같았던 것((5)).

> **`entries` 배열** — `Dictionary`·`HashSet` 이 원소를 **넣은 차례로 쌓아 두는 내부 배열**.\
> 예: 순회는 이 배열을 앞에서부터 훑는다 — 그래서 「넣은 순서처럼」 보인다. **구현이다.**

> **빈 자리 목록(free list)** — 지워진 칸을 다시 쓰려고 이어 둔 사슬.\
> 예: `b` 를 지우고 `d` 를 지운 뒤 새로 넣으면 **나중에 빈 `d` 자리부터** 채운다((4)).

> **박싱(boxing)** — 값 타입을 힙 객체로 감싸는 것. 자세한 것은 [03번](../03-boxing-and-unboxing/)이 정본이다.\
> 예: `ArrayList.Add(1)` 은 `int` 하나마다 객체 하나를 만든다((8)).

## 이 주제가 답하려는 질문

1. **넷을 무엇으로 고르나** — 자료구조 이름이 아니라 **접근 패턴**으로 고를 수 있나((1)).
2. ★★★ **`Dictionary` 의 순회 순서를 믿어도 되나** — 안 갈리는데 왜 안 되나, 그리고 **어떻게 갈라 보이나**((3)\~(5)).
3. **키에 무엇이 필요한가** — 안 갖추면 **터지나 조용한가**((6)), 그리고 **컴파일러는 말해 주나**((11)).

## 동작 방식

### (0) 이 주제가 쓰는 창

| 창 | 무엇을 보여 주나 | 이 주제에서 |
|---|---|---|
| ★★★ **실행 출력** | ★★★ **순회 순서** — 이 주제의 축이 여기서만 보인다 | (3)·(4)·(5) |
| ★★ **할당 바이트** | 제네릭이 박싱을 피하는 것 · **안 피하는 자리** | (8) |
| **예외 전문** | 없는 키 · 빈 큐 · 순회 중 변경 — **무엇이 터지고 무엇이 조용한가** | (7)·(9) |
| **컴파일 진단** | ★ **거의 말하지 않는다** — 탐침 8개 중 답한 것 **1개**((11)) | (6)·(11) |
| **IL** | `box` 가 어디 찍히나 | (8) |

- ★★ **부적용인 창 — 「진단의 `(행,열)`」이다.**\
  05\~09 는 `??` 와 `..` 의 **결합 방향**을 일부러 에러를 내서 **열**로 갈랐다.\
  이 주제에는 **그렇게 가를 결합 방향이 없다** — 컬렉션은 **연산자가 아니라 메서드 호출**이라
  파싱 우선순위가 걸리는 자리가 생기지 않는다. **「안 쟀다」가 아니라 「잴 것이 없다」다.**\
  ★ 같은 창의 다른 쓰임(계약 위반 경고 `CS0659`)은 (6)·(11)에서 쓴다 — **창을 안 쓴 것이 아니라 그 칸이 없는 것**이다.
- ★★★ **이 주제의 중심 창은 「실행 출력」이다.** 09 는 중심이 할당 바이트였고 03 은 IL 이었는데,
  여기는 **순회 순서**라 **출력 말고는 볼 데가 없다.**\
  그래서 **출력을 어떻게 던지느냐가 전부**다 — 한 판을 다섯 번 돌리는 것으로는 아무것도 안 갈린다((5)).

### (1) 넷을 접근 패턴으로 가른다

**언제 쓰나** — 컬렉션을 고를 때. **「무엇을 담나」가 아니라 「어떻게 찾나」를 먼저 묻는다.**

```text
===== 소스: cs10b-four.cs =====
using System;
using System.Collections.Generic;

var list = new List<string> { "빨강", "초록", "파랑" };
list.Insert(1, "노랑");
Console.WriteLine($"List<string>      [{string.Join(", ", list)}]");
Console.WriteLine($"  list[2] = {list[2]}   Count = {list.Count}   IndexOf(\"파랑\") = {list.IndexOf("파랑")}");
Console.WriteLine($"  Contains(\"파랑\") = {list.Contains("파랑")}   ← 앞에서부터 하나씩 본다");

var dict = new Dictionary<string, int> { ["빨강"] = 1, ["초록"] = 2, ["파랑"] = 3 };
Console.WriteLine($"Dictionary        [{string.Join(", ", dict.Keys)}]");
Console.WriteLine($"  dict[\"초록\"] = {dict["초록"]}   ContainsKey(\"보라\") = {dict.ContainsKey("보라")}");
Console.WriteLine($"  TryGetValue(\"보라\", out v) = {dict.TryGetValue("보라", out int v)}  (v = {v})");

var set = new HashSet<string> { "빨강", "초록", "빨강", "파랑" };
Console.WriteLine($"HashSet           [{string.Join(", ", set)}]   ← \"빨강\" 을 두 번 넣었는데 Count = {set.Count}");
Console.WriteLine($"  Add(\"빨강\") = {set.Add("빨강")}   Add(\"보라\") = {set.Add("보라")}   ← 되돌림값이 「새로 들어갔나」다");

var queue = new Queue<string>();
queue.Enqueue("1번손님"); queue.Enqueue("2번손님"); queue.Enqueue("3번손님");
Console.WriteLine($"Queue             [{string.Join(", ", queue)}]   Dequeue() = {queue.Dequeue()}   ← 먼저 온 사람");

var stack = new Stack<string>();
stack.Push("접시1"); stack.Push("접시2"); stack.Push("접시3");
Console.WriteLine($"Stack             [{string.Join(", ", stack)}]   Pop() = {stack.Pop()}   ← 마지막에 얹은 것");
===== csc -out:ex.dll cs10b-four.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
List<string>      [빨강, 노랑, 초록, 파랑]
  list[2] = 초록   Count = 4   IndexOf("파랑") = 3
  Contains("파랑") = True   ← 앞에서부터 하나씩 본다
Dictionary        [빨강, 초록, 파랑]
  dict["초록"] = 2   ContainsKey("보라") = False
  TryGetValue("보라", out v) = False  (v = 0)
HashSet           [빨강, 초록, 파랑]   ← "빨강" 을 두 번 넣었는데 Count = 3
  Add("빨강") = False   Add("보라") = True   ← 되돌림값이 「새로 들어갔나」다
Queue             [1번손님, 2번손님, 3번손님]   Dequeue() = 1번손님   ← 먼저 온 사람
Stack             [접시3, 접시2, 접시1]   Pop() = 접시3   ← 마지막에 얹은 것
```

| 컬렉션 | 찾는 법 | 순서가 계약인가 | 되돌림값이 말하는 것 |
|---|---|---|---|
| `List<T>` | 인덱스 · `Contains` 는 앞에서부터 | ★ **그렇다** — 넣은 자리에 있다 | `IndexOf` 는 **없으면 −1** |
| `Dictionary<K,V>` | 키 | ★★★ **아니다**((3)) | `TryGetValue` 는 **찾았나** |
| `HashSet<T>` | 값 자신 | ★★★ **아니다**((4)) | ★ `Add` 는 **새로 들어갔나**(중복이면 `False`) |
| `Queue<T>` | 앞에서만 | ★ **그렇다** — FIFO 가 계약 | `TryDequeue` 는 **비었나** |
| `Stack<T>` | 위에서만 | ★ **그렇다** — LIFO 가 계약 | `TryPop` 은 **비었나** |

- ★★ **`HashSet.Add` 의 되돌림값이 이 표에서 가장 자주 놓치는 칸**이다.\
  `List.Add` 는 `void` 인데 `HashSet.Add` 는 `bool` 이고, 그 `bool` 은 「**새로 들어갔나**」다.\
  중복을 세거나 처음 본 것만 처리할 때 **따로 `Contains` 를 부를 필요가 없다.**
- ★ **`Dictionary` 는 인덱서의 읽기와 쓰기가 다르다** — 없는 키를 **읽으면 던지고 쓰면 만든다**((9)).\
  `List` 는 읽기도 쓰기도 **범위 밖이면 던진다.** 같은 `[ ]` 인데 규칙이 다르다.
- **비용** — `List` 의 `Contains` 는 **O(n)**, `Dictionary`·`HashSet` 은 **평균 O(1)**.\
  ★ **그 이유(해시 표가 왜 O(1) 인가)는 [`data-structure/05-hashmap/`](../../../../../data-structure/05-hashmap/)이 정본**이고,
  여기서는 **그래서 무엇을 고르나**까지만 본다.

### (2) ★ `List<T>` 의 Capacity 증가 — 구현이지 보장이 아니다

**언제 쓰나** — 큰 컬렉션을 만들 때. **미리 잡아 주면 재배치를 안 한다.**

```text
===== 소스: cs10b-capacity.cs =====
using System;
using System.Collections.Generic;

var list = new List<int>();
int prev = list.Capacity;
Console.WriteLine($"new List<int>()        Count=0  Capacity={list.Capacity}");
for (int i = 0; i < 40; i++) {
    list.Add(i);
    if (list.Capacity != prev) { Console.WriteLine($"   Add #{i + 1} 에서  Count={list.Count,2}  Capacity {prev,2} → {list.Capacity}"); prev = list.Capacity; }
}

var set = new HashSet<int>();
int hp = set.Capacity;
Console.WriteLine($"new HashSet<int>()     Count=0  Capacity={set.Capacity}");
for (int i = 0; i < 40; i++) {
    set.Add(i);
    if (set.Capacity != hp) { Console.WriteLine($"   Add #{i + 1} 에서  Count={set.Count,2}  Capacity {hp,2} → {set.Capacity}"); hp = set.Capacity; }
}

var dict = new Dictionary<string, int>();
int dp = dict.Capacity;
Console.WriteLine($"new Dictionary<,>()    Count=0  Capacity={dict.Capacity}");
for (int i = 0; i < 40; i++) {
    dict[$"k{i}"] = i;
    if (dict.Capacity != dp) { Console.WriteLine($"   Add #{i + 1} 에서  Count={dict.Count,2}  Capacity {dp,2} → {dict.Capacity}"); dp = dict.Capacity; }
}

Console.WriteLine();
Console.WriteLine($"미리 잡아 주면 — new List<int>(5).Capacity       = {new List<int>(5).Capacity}");
Console.WriteLine($"미리 잡아 주면 — new HashSet<int>(5).Capacity    = {new HashSet<int>(5).Capacity}   ← 5 가 아니다");
Console.WriteLine($"미리 잡아 주면 — new Dictionary<string,int>(5).Capacity = {new Dictionary<string, int>(5).Capacity}   ← 5 가 아니다");
Console.WriteLine($"컬렉션 초기화자  — new List<int> {{ 1, 2, 3 }}.Capacity   = {new List<int> { 1, 2, 3 }.Capacity}");
List<int> byExpr = [1, 2, 3];
Console.WriteLine($"컬렉션 식        — List<int> x = [1, 2, 3] 의 Capacity = {byExpr.Capacity}   ← ★ 위와 다르다(11번 주제)");
===== csc -out:ex.dll cs10b-capacity.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
new List<int>()        Count=0  Capacity=0
   Add #1 에서  Count= 1  Capacity  0 → 4
   Add #5 에서  Count= 5  Capacity  4 → 8
   Add #9 에서  Count= 9  Capacity  8 → 16
   Add #17 에서  Count=17  Capacity 16 → 32
   Add #33 에서  Count=33  Capacity 32 → 64
new HashSet<int>()     Count=0  Capacity=0
   Add #1 에서  Count= 1  Capacity  0 → 3
   Add #4 에서  Count= 4  Capacity  3 → 7
   Add #8 에서  Count= 8  Capacity  7 → 17
   Add #18 에서  Count=18  Capacity 17 → 37
   Add #38 에서  Count=38  Capacity 37 → 89
new Dictionary<,>()    Count=0  Capacity=0
   Add #1 에서  Count= 1  Capacity  0 → 3
   Add #4 에서  Count= 4  Capacity  3 → 7
   Add #8 에서  Count= 8  Capacity  7 → 17
   Add #18 에서  Count=18  Capacity 17 → 37
   Add #38 에서  Count=38  Capacity 37 → 89

미리 잡아 주면 — new List<int>(5).Capacity       = 5
미리 잡아 주면 — new HashSet<int>(5).Capacity    = 7   ← 5 가 아니다
미리 잡아 주면 — new Dictionary<string,int>(5).Capacity = 7   ← 5 가 아니다
컬렉션 초기화자  — new List<int> { 1, 2, 3 }.Capacity   = 4
컬렉션 식        — List<int> x = [1, 2, 3] 의 Capacity = 3   ← ★ 위와 다르다(11번 주제)
```

| 컬렉션 | 이 판에서 본 수열 | 무엇인가 |
|---|---|---|
| `List<int>` | `0 → 4 → 8 → 16 → 32 → 64` | **2배** — 첫 칸만 4 |
| `HashSet<int>` | `0 → 3 → 7 → 17 → 37 → 89` | ★★ **소수**다 — 2배가 아니다 |
| `Dictionary<string,int>` | `0 → 3 → 7 → 17 → 37 → 89` | `HashSet` 과 같은 수열 |
| `new List<int>(5)` | `5` | 준 대로 |
| `new HashSet<int>(5)` · `new Dictionary<,>(5)` | ★ **7** | **소수로 올려 잡는다** |

- ★★★ **이 수열은 전부 BCL 구현이다 — 문서가 약속한 적이 없다.**\
  `List<T>.Capacity` 문서는 「용량이 모자라면 **자동으로 재할당한다**」고만 적는다.
  **몇 배로 늘리는지도, 첫 칸이 4 인지도 약속하지 않는다.**\
  ★ 그래서 **「Add 를 한 번 했으니 Capacity 는 4 겠지」 같은 코드는 계약 위에 서 있지 않다.**
- ★★ **`HashSet`·`Dictionary` 가 소수인 것이 「2배로 늘린다」를 반증한다.** 셋이 같은 규칙일 거라는 짐작이
  **같은 배치 안에서 깨진다** — 하나를 보고 나머지를 미루지 마라.
- ★ **`new HashSet<int>(5)` 가 7 인 것**은 「미리 잡아 준 값이 그대로 Capacity 가 된다」가
  `List` 에만 맞는 말임을 보인다.
- ★ 마지막 두 줄이 **11번 주제로 넘어가는 다리**다 — `new List<int> { 1, 2, 3 }` 은 **Capacity 4**,
  `List<int> x = [1, 2, 3]` 은 **Capacity 3** 이다. **같은 세 값인데 컴파일러가 다른 코드를 낸다.**
- **비용** — 재배치는 **O(현재 개수)** 복사다. `n` 개를 넣는 총비용은 상환 **O(n)** —\
  ★ **그 상환 분석은 [`data-structure/01-dynamic-array/`](../../../../../data-structure/01-dynamic-array/)가 정본**이다.

### (3) ★★★ `Dictionary` 의 순회 순서 — 이 주제의 축

**언제 쓰나** — `foreach (var kv in dict)` 를 쓰는 **모든** 자리.

```text
===== 소스: cs10b-dict-order.cs =====
using System;
using System.Collections.Generic;

var d = new Dictionary<string, int>();
d["alpha"] = 1; d["bravo"] = 2; d["charlie"] = 3; d["delta"] = 4; d["echo"] = 5;
Console.WriteLine($"① 다섯을 차례로 넣고 순회    : {Show(d)}");

d.Remove("bravo");
Console.WriteLine($"② bravo 를 지우고 순회       : {Show(d)}");

d["foxtrot"] = 6;
Console.WriteLine($"③ foxtrot 를 더하고 순회     : {Show(d)}   ★ 맨 뒤가 아니다");

d["golf"] = 7;
Console.WriteLine($"④ golf 를 더 더하고 순회     : {Show(d)}");

var e = new Dictionary<string, int>();
e["echo"] = 5; e["delta"] = 4; e["charlie"] = 3; e["bravo"] = 2; e["alpha"] = 1;
Console.WriteLine($"⑤ 같은 키를 거꾸로 넣고 순회 : {Show(e)}   ← 해시 순서가 아니다");

var f = new Dictionary<string, int>(e);
Console.WriteLine($"⑥ 그것을 복사 생성자로 옮기면: {Show(f)}");

var g = new Dictionary<string, int>();
for (int i = 0; i < 8; i++) g[$"k{i}"] = i;
Console.WriteLine($"⑦ 8개 넣어 리사이즈를 지나면 : {Show(g)}");

static string Show(Dictionary<string, int> d) {
    var parts = new List<string>();
    foreach (var kv in d) parts.Add($"{kv.Key}={kv.Value}");
    return string.Join(" ", parts);
}
===== csc -out:ex.dll cs10b-dict-order.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
① 다섯을 차례로 넣고 순회    : alpha=1 bravo=2 charlie=3 delta=4 echo=5
② bravo 를 지우고 순회       : alpha=1 charlie=3 delta=4 echo=5
③ foxtrot 를 더하고 순회     : alpha=1 foxtrot=6 charlie=3 delta=4 echo=5   ★ 맨 뒤가 아니다
④ golf 를 더 더하고 순회     : alpha=1 foxtrot=6 charlie=3 delta=4 echo=5 golf=7
⑤ 같은 키를 거꾸로 넣고 순회 : echo=5 delta=4 charlie=3 bravo=2 alpha=1   ← 해시 순서가 아니다
⑥ 그것을 복사 생성자로 옮기면: echo=5 delta=4 charlie=3 bravo=2 alpha=1
⑦ 8개 넣어 리사이즈를 지나면 : k0=0 k1=1 k2=2 k3=3 k4=4 k5=5 k6=6 k7=7
```

- ★★★ **①만 보면 「넣은 순서대로 나온다」로 읽힌다.** ⑤가 그 오해를 한 번 걸러 준다 —
  **거꾸로 넣으면 거꾸로 나온다.** 그러니 **해시 순서도 아니다.**
- ★★★ **③에서 깨진다.** `bravo` 를 지우고 `foxtrot` 를 넣었더니 **맨 뒤가 아니라 `alpha` 바로 뒤**다.\
  **삭제 없이 추가만 하면(④·⑦) 영원히 안 깨진다** — 그래서 대부분의 코드가 이 함정을 안 밟고 지나간다.
- ★★ **⑦은 리사이즈를 지나도 순서가 유지되는 것**을 보인다(8개를 넣어 Capacity 가 `3→7→17` 로 두 번 올라갔다).
  재해싱이 **`entries` 배열의 차례를 안 건드리기 때문**이다. **이것도 구현이다.**
- ★★★ **문서가 약속하는 것은 한 줄뿐이다** — 「항목이 돌아오는 **순서는 정해지지 않았다**」.\
  그리고 .NET 문서는 거기에 한 줄을 더 붙인다 —
  **「`Keys` 와 `Values` 의 순서가 서로 같다는 것은 보장한다」.**\
  ★ **약속한 것과 안 한 것을 갈라 읽어라** — 「순서 없음」이라고 다 없는 것이 아니다.

```text
   ★ 같은 질문에 세 언어가 다르게 답한다

   Python 3.7+   삽입 순서가 ★언어 보장★        지우고 넣으면 → 맨 뒤
   C# (.NET)     ★보장 없음★ · 관찰은 삽입 순서 지우고 넣으면 → 빈 자리   ← 여기서 갈린다
   Go            ★무작위★(명세가 정하지 않음)    매 판 섞인다

   세 칸의 「누가 정하나」가 전부 다르다 —
   Python 은 명세, C# 은 BCL 구현, Go 는 명세가 「정하지 않는다」고 못 박고 gc 가 일부러 섞는다.
```

- ★★★ **Go 와 정확히 반대다.** Go 는 **일부러 섞어서** 사람이 순서에 기대지 못하게 한다.\
  .NET 은 **안 섞는다** — 그래서 **기대는 코드가 쓰이고, 그 코드가 대개 잘 돈다.**\
  대비: Go 갈래 목록([`go/syntax/README.md`](../../../go/syntax/README.md))의 **9번**([`09-maps-declaration-comma-ok-delete-and-iteration-order/`](../../../go/syntax/09-maps-declaration-comma-ok-delete-and-iteration-order/)).
- ★★ **Python 과도 반대다.** Python 은 3.6 에서 CPython 구현 세부였던 것을 **3.7 에서 언어 보장으로 승격**했다.\
  C# 은 **20년 넘게 같은 관찰을 주면서 승격하지 않았다.**\
  ★ **그래서 「오래 안 바뀌었으니 보장이겠지」가 여기서 깨진다.**\
  대비: Python 갈래 목록([`python/syntax/README.md`](../../../python/syntax/README.md))의 **12번**([`12-dict-and-key-requirements/`](../../../python/syntax/12-dict-and-key-requirements/)).
- **비용** — 순회는 `entries` 배열을 앞에서부터 훑는 **O(Capacity)** 다. ★ `Count` 가 아니라 **Capacity** 에 비례한다 —
  많이 넣었다가 많이 지운 `Dictionary` 는 **빈 칸까지 훑는다.**

### (4) ★★ 빈 자리 재사용 — 「안 갈렸다」를 어떻게 갈랐나

**언제 쓰나** — 캐시·세션 표처럼 **지우고 넣기를 되풀이하는** 컬렉션을 순회할 때.

```text
===== 소스: cs10b-freelist.cs =====
using System;
using System.Collections.Generic;

var d = new Dictionary<string, int>();
foreach (var k in new[] { "a", "b", "c", "d", "e" }) d[k] = 0;
Console.WriteLine($"넣은 직후            : {string.Join(" ", d.Keys)}");
d.Remove("b");
Console.WriteLine($"b 를 지우고          : {string.Join(" ", d.Keys)}");
d.Remove("d");
Console.WriteLine($"d 도 지우고          : {string.Join(" ", d.Keys)}");
d["X"] = 0;
Console.WriteLine($"X 를 넣으면          : {string.Join(" ", d.Keys)}   ★ d 가 있던 자리다(나중에 빈 자리부터)");
d["Y"] = 0;
Console.WriteLine($"Y 를 넣으면          : {string.Join(" ", d.Keys)}   ★ b 가 있던 자리다");
Console.WriteLine();

var h = new HashSet<string> { "a", "b", "c", "d", "e" };
Console.WriteLine($"HashSet 도 같다 — 넣은 직후 : {string.Join(" ", h)}");
h.Remove("b"); h.Add("Z");
Console.WriteLine($"                b 빼고 Z 넣고 : {string.Join(" ", h)}");
Console.WriteLine();

Console.WriteLine("★ 여기까지는 한 프로세스 안의 이야기다.");
Console.WriteLine("  「여러 판을 돌리면 갈리나」는 다음 블록이 가짓수로 답한다.");
===== csc -out:ex.dll cs10b-freelist.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
넣은 직후            : a b c d e
b 를 지우고          : a c d e
d 도 지우고          : a c e
X 를 넣으면          : a c X e   ★ d 가 있던 자리다(나중에 빈 자리부터)
Y 를 넣으면          : a Y c X e   ★ b 가 있던 자리다

HashSet 도 같다 — 넣은 직후 : a b c d e
                b 빼고 Z 넣고 : a Z c d e

★ 여기까지는 한 프로세스 안의 이야기다.
  「여러 판을 돌리면 갈리나」는 다음 블록이 가짓수로 답한다.
```

- ★★★ **여기가 이 주제에서 가장 중요한 한 줄이다** — **둘을 지우고 둘을 넣으면 순서가 `a Y c X e`** 다.\
  `X` 가 먼저 들어갔는데 **`Y` 보다 뒤에 나온다.** 「넣은 순서」가 아닌 정도가 아니라 **뒤집혔다.**
- ★★ **빈 자리를 나중에 빈 것부터 쓴다**(스택처럼). `b`(1번) → `d`(3번) 순으로 지웠는데
  `X` 가 **3번**, `Y` 가 **1번**에 들어갔다.\
  ★ **이것도 구현이다** — 문서는 빈 자리 재사용을 **한 마디도 말하지 않는다.**
- ★★ **`HashSet` 도 똑같다.** 둘이 같은 `entries` + free list 구조를 쓰기 때문이다.
- ★★★ **여러 번 돌려서는 절대 못 잡는 종류의 사고**다. 같은 프로그램을 몇 번 돌려도 같은 답이 나온다 —\
  **갈리게 하려면 연산을 섞어야 한다.** 「반증이 확증보다 강하다」를 **판이 아니라 연산으로** 실행한 것이다.

### (5) ★★★ 20판의 가짓수 — 순회는 1, 해시는 20

**언제 쓰나** — 「돌려 봤더니 같더라」를 **근거로 쓸지** 판단할 때.

```text
===== 소스: cs10b-variety.cs =====
using System;
using System.Collections.Generic;

var d = new Dictionary<string, int>();
foreach (var k in new[] { "alpha", "bravo", "charlie", "delta", "echo" }) d[k] = 1;
d.Remove("bravo");
d["foxtrot"] = 1;
var keys = new List<string>();
foreach (var kv in d) keys.Add(kv.Key);
Console.WriteLine("순회 " + string.Join(" ", keys));
Console.WriteLine("해시 " + "alpha".GetHashCode());
===== csc -out:ex.dll cs10b-variety.cs && for i in $(seq 1 20); do dotnet ex.dll; done > runs.txt =====
20판을 돌려 서로 다른 줄이 몇 가지인지 센다(한 판의 출력은 싣지 않는다).

  grep '^순회' runs.txt | sort -u | wc -l   →   1
  grep '^해시' runs.txt | sort -u | wc -l   →   20

  순회 줄은 한 가지뿐이라 그대로 싣는다:
  순회 alpha foxtrot charlie delta echo
```

- ★★★ **같은 20판에서 한 줄은 1가지, 다른 한 줄은 20가지다.**\
  **이 런타임은 무작위화를 한다** — 문자열 해시의 씨앗을 **프로세스마다 새로 뽑는다**(해시 DoS 를 막으려고).\
  그런데 **그 무작위가 순회 순서에는 안 새어 나온다.** 순회가 **해시가 아니라 `entries` 배열 차례**를 따르기 때문이다.
- ★★★ **그래서 「20번 돌려도 같았다」는 아무것도 증명하지 못한다.**\
  무작위화가 **없어서** 같은 것이 아니라, **있는데 이 값에는 안 닿아서** 같은 것이다.\
  ★ 그 구조가 바뀌면(예: 순회가 버킷을 훑도록) **같은 프로그램이 매 판 달라진다.** 바꿔도 아무도 계약을 어긴 게 아니다.
- ★★ **한 판의 출력을 안 싣고 「가짓수」를 실었다.** 해시값 스무 개를 실으면 **다시 돌릴 때마다 전부 어긋난다** —\
  **가짓수 20 은 다시 돌려도 20** 이다(32비트 값 스무 개가 겹칠 확률은 1억 분의 1 남짓이다).
- ★ **Python 도 같은 구조다** — `PYTHONHASHSEED` 가 해시를 흔드는데 **dict 순서는 안 흔들린다.**\
  **「해시가 무작위다」와 「순서가 무작위다」는 다른 문장**이고, 세 언어가 이 두 축의 서로 다른 칸에 있다.

### (6) ★ 키 요건 — `GetHashCode` 와 `Equals`

**언제 쓰나** — **내가 만든 타입**을 `Dictionary` 의 키나 `HashSet` 의 원소로 쓸 때.

```text
===== 소스: cs10b-contract.cs =====
using System;
using System.Collections.Generic;

var bad = new HashSet<BadKey> { new BadKey(1), new BadKey(1), new BadKey(1) };
Console.WriteLine($"BadKey  (GetHashCode 없음)  Count = {bad.Count}   Contains(new BadKey(1)) = {bad.Contains(new BadKey(1))}");
var good = new HashSet<GoodKey> { new GoodKey(1), new GoodKey(1), new GoodKey(1) };
Console.WriteLine($"GoodKey (GetHashCode 있음)  Count = {good.Count}   Contains(new GoodKey(1)) = {good.Contains(new GoodKey(1))}");
Console.WriteLine($"  그런데 Equals 는 둘 다 true 다 : {new BadKey(1).Equals(new BadKey(1))} / {new GoodKey(1).Equals(new GoodKey(1))}");
Console.WriteLine();

var m = new GoodKey(1);
var set = new HashSet<GoodKey> { m };
Console.WriteLine($"넣은 직후             Contains(m) = {set.Contains(m)}");
m.X = 99;
Console.WriteLine($"m.X = 99 로 바꾼 뒤   Contains(m) = {set.Contains(m)}   Count = {set.Count}");
Console.WriteLine($"  그래도 순회하면 보인다 : {string.Join(", ", set)}");
Console.WriteLine($"  Remove(m) = {set.Remove(m)}   지운 뒤 Count = {set.Count}   ← 꺼낼 수도 없다");

class BadKey {
    public int X;
    public BadKey(int x) { X = x; }
    public override bool Equals(object o) => o is BadKey b && b.X == X;
    public override string ToString() => $"BadKey({X})";
}
class GoodKey {
    public int X;
    public GoodKey(int x) { X = x; }
    public override bool Equals(object o) => o is GoodKey g && g.X == X;
    public override int GetHashCode() => X.GetHashCode();
    public override string ToString() => $"GoodKey({X})";
}
===== csc -out:ex.dll cs10b-contract.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
cs10b-contract.cs(19,7): warning CS0659: 'BadKey' overrides Object.Equals(object o) but does not override Object.GetHashCode()
BadKey  (GetHashCode 없음)  Count = 3   Contains(new BadKey(1)) = False
GoodKey (GetHashCode 있음)  Count = 1   Contains(new GoodKey(1)) = True
  그런데 Equals 는 둘 다 true 다 : True / True

넣은 직후             Contains(m) = True
m.X = 99 로 바꾼 뒤   Contains(m) = False   Count = 1
  그래도 순회하면 보인다 : GoodKey(99)
  Remove(m) = False   지운 뒤 Count = 1   ← 꺼낼 수도 없다
```

| 심은 것 | 컴파일러 | 실행 결과 |
|---|---|---|
| `Equals` 만 재정의 | ★ **경고 `CS0659`** — 말해 준다 | **중복 셋이 다 들어가고**(`Count = 3`) `Contains` 가 `False` |
| 둘 다 재정의 | 조용 | `Count = 1` · `Contains` 가 `True` |
| 넣은 뒤 키를 고침 | ★★ **아무 말도 없다** | `Contains` 도 `Remove` 도 `False` 인데 **순회하면 보인다** |

- ★★★ **어기면 터지지 않는다 — 값이 사라진다.** 예외도 경고도 없이 `Contains` 가 `False` 를 답한다.\
  ★ **Rust 28번과 똑같은 실패 모드**다(「어기면 터지는 게 아니라 값이 사라진다」).\
  대비: Rust 갈래 목록([`rust/syntax/README.md`](../../../rust/syntax/README.md))의 **28번**([`28-partialeq-eq-partialord-ord-and-hash-contracts/`](../../../rust/syntax/28-partialeq-eq-partialord-ord-and-hash-contracts/)).
- ★★ **Python 은 이 사고를 언어가 막는다.** `__eq__` 만 정의하면 **`__hash__` 를 `None` 으로 꺼 버려**
  그 타입은 아예 키가 못 된다.\
  C# 은 **경고 한 줄을 내고 통과시킨다** — 경고를 안 보면 그대로 배포된다.\
  Rust 는 **`Hash` 를 `derive` 안 하면 키로 쓸 수 없다**(컴파일 에러). **세 언어가 세 단계로 다르다.**
- ★★★ **가변 키는 셋 중 누구도 못 막는다.** 넣은 뒤 `X` 를 고치면 **원래 자리에 그대로 앉은 채 못 찾는 유령**이 된다.\
  `Count` 는 1 인데 `Remove` 도 실패한다 — **지울 수도 없다.**
- **비용** — `GetHashCode` 가 상수를 돌려줘도 **동작은 맞다**(느려질 뿐이다). `Equals` 와 어긋나면 **답이 틀린다.**\
  ★ **둘의 관계는 「같으면 해시도 같아야 한다」 한 방향뿐**이다. 반대는 요구가 아니다(충돌은 정상이다).

### (7) `Queue` 와 `Stack`

**언제 쓰나** — 처리 순서가 **들어온 순서**이거나 **되돌아가는 순서**일 때.

```text
===== 소스: cs10b-queue-stack.cs =====
using System;
using System.Collections.Generic;

var q = new Queue<string>();
q.Enqueue("A"); q.Enqueue("B"); q.Enqueue("C");
Console.WriteLine($"Queue  순회     : {string.Join(" ", q)}");
Console.WriteLine($"Queue  Peek() = {q.Peek()}   Dequeue() = {q.Dequeue()}   남은 것 : {string.Join(" ", q)}");
Console.WriteLine($"Queue  ToArray(): [{string.Join(" ", q.ToArray())}]");
Console.WriteLine();

var s = new Stack<string>();
s.Push("A"); s.Push("B"); s.Push("C");
Console.WriteLine($"Stack  순회     : {string.Join(" ", s)}   ★ 넣은 순서의 거꾸로다");
Console.WriteLine($"Stack  Peek() = {s.Peek()}   Pop() = {s.Pop()}   남은 것 : {string.Join(" ", s)}");
Console.WriteLine($"Stack  ToArray(): [{string.Join(" ", s.ToArray())}]   ★ 이것도 거꾸로다");
Console.WriteLine();

var empty = new Queue<string>();
Console.WriteLine($"빈 Queue 에 TryDequeue = {empty.TryDequeue(out var got)}  (got = {got ?? "null"})");
try { empty.Dequeue(); }
catch (InvalidOperationException ex) { Console.WriteLine($"빈 Queue 에 Dequeue()  → {ex.GetType().Name}: {ex.Message}"); }

var q2 = new Queue<int>();
for (int i = 0; i < 5; i++) q2.Enqueue(i);
for (int i = 0; i < 3; i++) q2.Dequeue();
for (int i = 5; i < 8; i++) q2.Enqueue(i);
Console.WriteLine($"3번 빼고 3번 더 넣어도 순서는 : {string.Join(" ", q2)}   ← 원형 버퍼라 앞이 재활용된다");
===== csc -out:ex.dll cs10b-queue-stack.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
Queue  순회     : A B C
Queue  Peek() = A   Dequeue() = A   남은 것 : B C
Queue  ToArray(): [B C]

Stack  순회     : C B A   ★ 넣은 순서의 거꾸로다
Stack  Peek() = C   Pop() = C   남은 것 : B A
Stack  ToArray(): [B A]   ★ 이것도 거꾸로다

빈 Queue 에 TryDequeue = False  (got = null)
빈 Queue 에 Dequeue()  → InvalidOperationException: Queue empty.
3번 빼고 3번 더 넣어도 순서는 : 3 4 5 6 7   ← 원형 버퍼라 앞이 재활용된다
```

- ★★ **`Stack<T>` 의 순회가 `C B A` 인 것**이 이 절의 함정이다. **`Push` 한 순서의 거꾸로**다 —
  `ToArray()` 도 마찬가지다. **문서가 「LIFO 순서로 돌려준다」고 약속한 자리**라 이건 관찰이 아니라 계약이다.
- ★ **`Queue`·`Stack` 은 순서가 계약**이다((1)의 표). **`Dictionary`·`HashSet` 과 여기서 갈린다** —
  **같은 「순서」라는 말이 어떤 타입에서는 보장이고 어떤 타입에서는 아니다.**
- ★ **빈 것에서 꺼내면 `InvalidOperationException`** 이다(`null` 이 아니다). `Try…` 쪽은 `false` 를 준다.\
  ★ **되돌림값이 다르므로 둘을 섞어 쓰지 마라** — `TryDequeue` 의 `out` 은 실패하면 **기본값**이다.
- **비용** — 둘 다 `Enqueue`/`Push` 상환 **O(1)**, 꺼내기 **O(1)**.\
  `Queue` 가 **원형 버퍼**라 앞칸을 재활용한다(마지막 줄) — ★ **원리는
  [`data-structure/04-queue-deque/`](../../../../../data-structure/04-queue-deque/)가 정본**이다.

### (8) ★★ 제네릭이 박싱을 피한다 — 그리고 안 피하는 자리

**언제 쓰나** — 「왜 GC 가 도나」를 추적할 때. 그리고 **낡은 코드(`ArrayList`)를 고칠 이유**를 댈 때.

```text
===== 소스: cs10b-il.cs =====
using System;
using System.Collections;
using System.Collections.Generic;

Il.Dump(typeof(P), "Old");
Il.Dump(typeof(P), "New");
Il.Dump(typeof(P), "LookUp");

static class P {
    public static void Old(ArrayList a, int v) => a.Add(v);
    public static void New(List<int> a, int v) => a.Add(v);
    public static int LookUp(Dictionary<string, int> d, string k) => d[k];
}
===== csc -r:il.dll -out:ex.dll cs10b-il.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
--- P.Old ---
  IL_0000: ldarg.0
  IL_0001: ldarg.1
  IL_0002: box System.Int32
  IL_0007: callvirt System.Collections.ArrayList::Add
  IL_000c: pop
  IL_000d: ret
--- P.New ---
  IL_0000: ldarg.0
  IL_0001: ldarg.1
  IL_0002: callvirt System.Collections.Generic.List<System.Int32>::Add
  IL_0007: nop
  IL_0008: ret
--- P.LookUp ---
  IL_0000: ldarg.0
  IL_0001: ldarg.1
  IL_0002: callvirt System.Collections.Generic.Dictionary<System.String,System.Int32>::get_Item
  IL_0007: ret
```

```text
===== 소스: cs10b-boxing.cs =====
using System;
using System.Collections;
using System.Collections.Generic;
using System.Runtime.CompilerServices;

class P {
    [MethodImpl(MethodImplOptions.NoInlining)] static void FillOld(ArrayList a) { for (int i = 0; i < 100; i++) a.Add(i); }
    [MethodImpl(MethodImplOptions.NoInlining)] static void FillNew(List<int> a) { for (int i = 0; i < 100; i++) a.Add(i); }
    [MethodImpl(MethodImplOptions.NoInlining)] static int LookPlain(Dictionary<PlainKey, int> d, PlainKey k) { int t = 0; for (int i = 0; i < 100; i++) t += d[k]; return t; }
    [MethodImpl(MethodImplOptions.NoInlining)] static int LookFast(Dictionary<FastKey, int> d, FastKey k) { int t = 0; for (int i = 0; i < 100; i++) t += d[k]; return t; }

    static void Main() {
        var dp = new Dictionary<PlainKey, int> { [new PlainKey(1, 2)] = 7 };
        var df = new Dictionary<FastKey, int> { [new FastKey(1, 2)] = 7 };
        for (int w = 0; w < 3; w++) {
            var wa = new ArrayList(); FillOld(wa);
            var wl = new List<int>(); FillNew(wl);
            LookPlain(dp, new PlainKey(1, 2)); LookFast(df, new FastKey(1, 2));
        }
        long b0, b1;
        b0 = GC.GetAllocatedBytesForCurrentThread(); var al = new ArrayList(); FillOld(al); b1 = GC.GetAllocatedBytesForCurrentThread();
        Console.WriteLine($"ArrayList 에 int 100개 넣기           : +{b1 - b0} 바이트");
        b0 = GC.GetAllocatedBytesForCurrentThread(); var li = new List<int>(); FillNew(li); b1 = GC.GetAllocatedBytesForCurrentThread();
        Console.WriteLine($"List<int> 에 int 100개 넣기           : +{b1 - b0} 바이트");
        Console.WriteLine();
        b0 = GC.GetAllocatedBytesForCurrentThread(); int t1 = LookPlain(dp, new PlainKey(1, 2)); b1 = GC.GetAllocatedBytesForCurrentThread();
        Console.WriteLine($"Dictionary<PlainKey,int> 조회 100번   : +{b1 - b0} 바이트  (합 {t1})   ← IEquatable<T> 없음");
        b0 = GC.GetAllocatedBytesForCurrentThread(); int t2 = LookFast(df, new FastKey(1, 2)); b1 = GC.GetAllocatedBytesForCurrentThread();
        Console.WriteLine($"Dictionary<FastKey,int>  조회 100번   : +{b1 - b0} 바이트  (합 {t2})   ← IEquatable<T> 있음");
        Console.WriteLine();
        Console.WriteLine($"EqualityComparer<PlainKey>.Default 의 실제 타입 : {EqualityComparer<PlainKey>.Default.GetType().Name}");
        Console.WriteLine($"EqualityComparer<FastKey>.Default  의 실제 타입 : {EqualityComparer<FastKey>.Default.GetType().Name}");
        Console.WriteLine($"EqualityComparer<string>.Default   의 실제 타입 : {EqualityComparer<string>.Default.GetType().Name}");
        GC.KeepAlive(al); GC.KeepAlive(li);
    }
}

struct PlainKey { public int A, B; public PlainKey(int a, int b) { A = a; B = b; } }

struct FastKey : IEquatable<FastKey> {
    public int A, B;
    public FastKey(int a, int b) { A = a; B = b; }
    public bool Equals(FastKey o) => A == o.A && B == o.B;
    public override bool Equals(object o) => o is FastKey f && Equals(f);
    public override int GetHashCode() => A * 31 + B;
}
===== csc -out:ex.dll cs10b-boxing.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
ArrayList 에 int 100개 넣기           : +4592 바이트
List<int> 에 int 100개 넣기           : +1184 바이트

Dictionary<PlainKey,int> 조회 100번   : +7200 바이트  (합 700)   ← IEquatable<T> 없음
Dictionary<FastKey,int>  조회 100번   : +0 바이트  (합 700)   ← IEquatable<T> 있음

EqualityComparer<PlainKey>.Default 의 실제 타입 : ObjectEqualityComparer`1
EqualityComparer<FastKey>.Default  의 실제 타입 : GenericEqualityComparer`1
EqualityComparer<string>.Default   의 실제 타입 : StringEqualityComparer
```

| 잰 것 | 증분 | 읽는 법 |
|---|---|---|
| `ArrayList` 에 `int` 100개 | **4592** | IL 에 **`box System.Int32`** 가 찍혀 있다 |
| `List<int>` 에 `int` 100개 | **1184** | ★ IL 에 `box` 가 **없다** — `int` 전용 코드가 생긴다 |
| `Dictionary<PlainKey,int>` 조회 100번 | ★★★ **7200** | **조회 한 번에 72바이트** — 24바이트짜리 박스 셋 |
| `Dictionary<FastKey,int>` 조회 100번 | ★★★ **0** | `IEquatable<T>` 하나 붙인 차이다 |

- ★★★ **제네릭이 박싱을 없앤다는 말은 「담을 때」에만 맞다.** 담는 쪽은 `List<int>` 만으로 해결되는데,
  **키로 쓸 때는 `IEquatable<T>` 를 직접 붙여야** 0 이 된다.
- ★★ **비교자 타입이 그 차이를 이름으로 말해 준다** — `ObjectEqualityComparer` 대 `GenericEqualityComparer`.\
  앞엣것은 `object.Equals(object)` 로 내려가므로 **양쪽을 박싱하고**, `GetHashCode` 에서 한 번 더 박싱한다.
  **24 × 3 = 72** 가 정확히 맞는다.
- ★ **`string` 키는 `StringEqualityComparer` 라는 전용 비교자**가 따로 있다. 가장 흔한 키라서다.
- ★ 박싱 자체(무엇이 몇 바이트인가·`box`/`unbox.any`)는 [03번](../03-boxing-and-unboxing/)이 정본이고,
  여기서는 **컬렉션을 고를 때 그것이 어디서 나오나**만 본다.
- **비용** — `ArrayList` 는 원소마다 **객체 하나**를 만들고 GC 가 그만큼 돈다.\
  ★ **시간은 재지 않았다** — 이 표의 근거는 **바이트뿐**이다.

### (9) 없는 키·순회 중 변경 — 무엇이 터지고 무엇이 조용한가

**언제 쓰나** — 컬렉션을 **고치면서 훑는** 코드를 읽거나 쓸 때.

```text
===== 소스: cs10b-throws.cs =====
using System;
using System.Collections.Generic;

var d = new Dictionary<string, int> { ["a"] = 1, ["b"] = 2, ["c"] = 3 };
try { int x = d["없는키"]; Console.WriteLine(x); }
catch (KeyNotFoundException ex) { Console.WriteLine($"d[\"없는키\"] 읽기 → {ex.GetType().Name}: {ex.Message}"); }
Console.WriteLine($"TryGetValue(\"없는키\", out v) = {d.TryGetValue("없는키", out int v)}  (v = {v})");
Console.WriteLine($"GetValueOrDefault(\"없는키\", -1) = {d.GetValueOrDefault("없는키", -1)}");
Console.WriteLine($"d[\"없는키\"] = 9 로 쓰기 → 예외 없이 들어간다. Count = {Put(d)}");
Console.WriteLine();

try { foreach (var kv in d) d["z"] = 9; }
catch (InvalidOperationException ex) { Console.WriteLine($"순회 중 새 키 Add       → {ex.GetType().Name}: {ex.Message}"); }

var d2 = new Dictionary<string, int> { ["a"] = 1, ["b"] = 2, ["c"] = 3 };
try { foreach (var kv in d2) if (kv.Key == "b") d2.Remove("b");
      Console.WriteLine($"순회 중 Remove          → 안 터졌다. 남은 것 = {string.Join(" ", d2.Keys)}"); }
catch (InvalidOperationException ex) { Console.WriteLine($"순회 중 Remove          → {ex.GetType().Name}: {ex.Message}"); }

var d3 = new Dictionary<string, int> { ["a"] = 1, ["b"] = 2 };
try { foreach (var kv in d3) d3["a"] = 99;
      Console.WriteLine($"순회 중 있는 키 덮어쓰기 → 안 터졌다. d3[\"a\"] = {d3["a"]}"); }
catch (InvalidOperationException ex) { Console.WriteLine($"순회 중 덮어쓰기        → {ex.GetType().Name}: {ex.Message}"); }

var l = new List<int> { 1, 2, 3 };
try { foreach (int x in l) l.Add(4); }
catch (InvalidOperationException ex) { Console.WriteLine($"List 순회 중 Add        → {ex.GetType().Name}: {ex.Message}"); }

static int Put(Dictionary<string, int> d) { d["없는키"] = 9; return d.Count; }
===== csc -out:ex.dll cs10b-throws.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
d["없는키"] 읽기 → KeyNotFoundException: The given key '없는키' was not present in the dictionary.
TryGetValue("없는키", out v) = False  (v = 0)
GetValueOrDefault("없는키", -1) = -1
d["없는키"] = 9 로 쓰기 → 예외 없이 들어간다. Count = 4

순회 중 새 키 Add       → InvalidOperationException: Collection was modified; enumeration operation may not execute.
순회 중 Remove          → 안 터졌다. 남은 것 = a c
순회 중 있는 키 덮어쓰기 → 안 터졌다. d3["a"] = 99
List 순회 중 Add        → InvalidOperationException: Collection was modified; enumeration operation may not execute.
```

| 한 일 | 결과 | 무엇인가 |
|---|---|---|
| 없는 키를 **읽기** | `KeyNotFoundException` | 계약 |
| 없는 키에 **쓰기** | ★ 조용히 **만든다** | 계약 — 인덱서의 읽기·쓰기가 다르다 |
| 순회 중 **새 키 Add** | `InvalidOperationException` | 계약 |
| 순회 중 **`Remove`** | ★★ **안 터진다** | ★★ **.NET Core 3.0부터 「지원한다」고 문서가 못 박은 것** — 계약이다 |
| 순회 중 **있는 키 덮어쓰기** | ★ **안 터진다** | 같은 문서 줄이 덮는다 |
| `List` 순회 중 `Add` | `InvalidOperationException` | 계약 — **`List` 에는 위의 예외가 없다** |

- ★★★ **「순회 중 `Remove` 가 되는 것」은 관찰이 아니라 보장이다.** .NET Core 3.0 에서
  **문서에 한 줄이 추가되면서** 구현 세부가 계약으로 올라왔다.\
  ★ **(3)의 순회 순서는 그 승격이 일어나지 않은 자리**다 — **같은 타입 안에서 두 갈래가 갈린다.**
- ★★ **`List<T>` 에는 그 완화가 없다.** 「`Dictionary` 에서 되니까 `List` 에서도 되겠지」가 여기서 깨진다.
- ★ **`TryGetValue` 와 `GetValueOrDefault` 를 고르는 기준** — 「없음」을 **분기로 다룰 것**이면 앞엣것,
  **기본값으로 때울 것**이면 뒤엣것이다. `out` 변수는 실패하면 **`default`** 다(`0`·`null`).

### (10) 순서가 필요하면 무엇을 쓰나

**언제 쓰나** — (3)을 읽고 나서 「**그럼 어떻게 하나**」가 궁금할 때.

```text
===== 소스: cs10b-sorted.cs =====
using System;
using System.Collections.Generic;
using System.Linq;

var d = new Dictionary<string, int> { ["delta"] = 4, ["alpha"] = 1, ["charlie"] = 3, ["bravo"] = 2 };
Console.WriteLine($"Dictionary 그대로 순회         : {string.Join(" ", d.Keys)}   ← 보장 없음");
Console.WriteLine($"키로 정렬해서 찍으면           : {string.Join(" ", d.Keys.OrderBy(k => k, StringComparer.Ordinal))}");

var sd = new SortedDictionary<string, int> { ["delta"] = 4, ["alpha"] = 1, ["charlie"] = 3, ["bravo"] = 2 };
Console.WriteLine($"SortedDictionary 순회          : {string.Join(" ", sd.Keys)}   ← 키 순서가 계약이다");

var sl = new SortedList<string, int> { ["delta"] = 4, ["alpha"] = 1, ["charlie"] = 3, ["bravo"] = 2 };
Console.WriteLine($"SortedList 순회                : {string.Join(" ", sl.Keys)}");

var ss = new SortedSet<string> { "delta", "alpha", "charlie", "bravo" };
Console.WriteLine($"SortedSet 순회                 : {string.Join(" ", ss)}");
Console.WriteLine();

var q = new PriorityQueue<string, int>();
q.Enqueue("낮음", 3); q.Enqueue("긴급", 1); q.Enqueue("보통", 2); q.Enqueue("긴급2", 1);
var order = new List<string>();
while (q.TryDequeue(out var item, out _)) order.Add(item);
Console.WriteLine($"PriorityQueue 로 꺼낸 순서     : {string.Join(" ", order)}");
Console.WriteLine("  ★ 우선순위가 같은 둘 사이의 순서는 계약이 아니다 — 안정 정렬이 아니라고 문서가 못 박는다.");
===== csc -out:ex.dll cs10b-sorted.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
Dictionary 그대로 순회         : delta alpha charlie bravo   ← 보장 없음
키로 정렬해서 찍으면           : alpha bravo charlie delta
SortedDictionary 순회          : alpha bravo charlie delta   ← 키 순서가 계약이다
SortedList 순회                : alpha bravo charlie delta
SortedSet 순회                 : alpha bravo charlie delta

PriorityQueue 로 꺼낸 순서     : 긴급 긴급2 보통 낮음
  ★ 우선순위가 같은 둘 사이의 순서는 계약이 아니다 — 안정 정렬이 아니라고 문서가 못 박는다.
```

| 쓸 것 | 무엇이 계약인가 | 대가 |
|---|---|---|
| `Dictionary` + 꺼낼 때 `OrderBy` | 정렬 순서 | 꺼낼 때마다 **O(n log n)** |
| `SortedDictionary<K,V>` | **키 순서** | 넣기·찾기가 **O(log n)** (이진 검색 트리) |
| `SortedList<K,V>` | **키 순서** | 찾기 **O(log n)** · 가운데 삽입 **O(n)** · 메모리는 제일 작다 |
| `SortedSet<T>` | **값 순서** | `HashSet` 보다 느리다 |
| `PriorityQueue<T,P>` | **우선순위가 가장 작은 것부터** | ★ **같은 우선순위끼리의 순서는 계약이 아니다** |

- ★★ **「정렬된 순회가 필요하다」와 「넣은 순서가 필요하다」는 다른 요구다.**\
  위 다섯은 전부 **앞엣것**을 푼다. **넣은 순서가 필요하면 `List` 를 곁들여 직접 들고 있어야 한다** —
  BCL 에 「삽입 순서를 보장하는 딕셔너리」는 없다.
- ★ **`PriorityQueue` 는 안정 정렬이 아니라고 문서가 못 박는다.** 위 출력의 `긴급 긴급2` 는
  **이번 판의 관찰**이지 계약이 아니다 — **동률이 중요하면 우선순위에 일련번호를 섞어 넣어라.**

### (11) ★★ 진단은 여기서 거의 말하지 않는다 — 탐침 8개 중 1개

**언제 쓰나** — 「컴파일이 됐으니 괜찮겠지」를 점검할 때.

```text
===== 소스: cs10b-quiet.cs =====
using System;
using System.Collections;
using System.Collections.Generic;

// 이 파일은 이 주제의 사고를 여덟 자리에 일부러 심어 놓은 탐침이다.
// -warn:9 로 컴파일해 컴파일러가 몇 군데에서 말하는지 센다.
public static class Probes {
    public static void P1_ArrayList() {                      // 1. 박싱 — int 를 ArrayList 에
        var a = new ArrayList();
        for (int i = 0; i < 10; i++) a.Add(i);
    }
    public static int P2_StructKey() {                       // 2. IEquatable 없는 struct 키
        var d = new Dictionary<Pair, int> { [new Pair(1, 2)] = 3 };
        return d[new Pair(1, 2)];
    }
    public static string P3_OrderDependency(Dictionary<string, int> d) {  // 3. 순회 순서에 기댄 코드
        foreach (var kv in d) return kv.Key;                 //    「첫 키」를 답으로 쓴다
        return "";
    }
    public static void P4_MutableKey() {                     // 4. 넣은 뒤 키를 고친다
        var k = new Holder { X = 1 };
        var set = new HashSet<Holder> { k };
        k.X = 2;
    }
    public static void P5_RemoveWhileEnumerating(Dictionary<string, int> d) {  // 5. 순회 중 삭제
        foreach (var kv in d) if (kv.Value == 0) d.Remove(kv.Key);
    }
    public static int P6_CapacityDependency() {              // 6. Capacity 증가 규칙에 기댄다
        var l = new List<int>();
        l.Add(1);
        return l.Capacity;                                   //    4 라고 믿는 코드
    }
    public static bool P7_EqualsOnly() {                     // 7. Equals 만 재정의한 타입을 키로
        var set = new HashSet<EqualsOnly> { new EqualsOnly(), new EqualsOnly() };
        return set.Count == 1;
    }
    public static int P8_HashCodeOnly() {                    // 8. GetHashCode 만 재정의한 타입을 키로
        var set = new HashSet<HashOnly> { new HashOnly(), new HashOnly() };
        return set.Count;
    }
}
public struct Pair { public int A, B; public Pair(int a, int b) { A = a; B = b; } }
public class Holder { public int X; public override int GetHashCode() => X; public override bool Equals(object o) => o is Holder h && h.X == X; }
public class EqualsOnly { public override bool Equals(object o) => o is EqualsOnly; }
public class HashOnly { public override int GetHashCode() => 1; }
===== csc -warn:9 -target:library -out:ex.dll cs10b-quiet.cs (cc exit=0) =====
cs10b-quiet.cs(44,14): warning CS0659: 'EqualsOnly' overrides Object.Equals(object o) but does not override Object.GetHashCode()
```

- ★★★ **탐침 여덟 개 중 답한 것은 하나(`CS0659`)뿐이다.** 나머지 일곱은 **경고 한 줄 없이 통과한다** —
  박싱도, `IEquatable` 없는 struct 키도, 순회 순서에 기댄 코드도, 가변 키도, Capacity 에 기댄 코드도.
- ★★ **「경고가 안 났다」와 「안 물어봤다」를 가르려고 `-warn:9` 로 최대 수준을 걸고 던졌다.**
  블록의 `cc exit=0` 과 **한 줄짜리 출력**이 그 증거다 — 물었고, 한 군데만 답했다.
- ★★ **비대칭이 하나 더 있다** — `Equals` 만 재정의하면 `CS0659` 가 나는데,
  **`GetHashCode` 만 재정의하면 아무 말도 안 난다**(탐침 8번). 그쪽은 **동작이 안 틀리기 때문**이다.\
  ★ **컴파일러가 잡아 주는 것은 「계약이 깨지는 방향」 하나뿐**이고, 나머지는 사람 몫이다.
- ★ **그래서 이 주제의 안전망은 진단이 아니라 테스트다.** 「순회 순서에 기대지 않았나」는
  **키를 지웠다 넣는 테스트**로만 잡힌다((4)).

## 문법 — 형태와 규칙

**형태 — 넷으로 하는 일 전부**

```csharp
// (문법 요약 — 이 블록은 돌린 것이 아니라 형태만 모은 것이다)
List<int> list = new();                 // 인덱스로 찾는다
list.Add(1); list.Insert(0, 9); list.RemoveAt(0); list.Remove(1);
int first = list[0]; int n = list.Count; int cap = list.Capacity;
bool has = list.Contains(1);            // O(n)
list.Sort(); list.Reverse();

Dictionary<string, int> dict = new();   // 키로 찾는다
dict["a"] = 1;                          // 없으면 만들고 있으면 덮는다
dict.Add("b", 2);                       // 있으면 ArgumentException
bool ok = dict.TryAdd("b", 3);          // 있으면 false (던지지 않는다)
bool found = dict.TryGetValue("a", out int v);
int fallback = dict.GetValueOrDefault("z", -1);
dict.Remove("a"); dict.ContainsKey("b"); dict.ContainsValue(2);

HashSet<int> set = new();               // 있나 없나만 본다
bool added = set.Add(1);                // ★ 되돌림값이 「새로 들어갔나」다
set.UnionWith(other); set.IntersectWith(other); set.ExceptWith(other);
bool sub = set.IsSubsetOf(other);

Queue<string> q = new();                // 먼저 온 것부터
q.Enqueue("a"); string head = q.Peek(); q.Dequeue(); q.TryDequeue(out string? x);

Stack<string> st = new();               // 나중 것부터
st.Push("a"); string top = st.Peek(); st.Pop(); st.TryPop(out string? y);
```

**금지 사례 — 컴파일러가 막는 것은 이것뿐이다**

```csharp
// (형태만 — 아래 넷은 컴파일 에러다)
var d = new Dictionary<string, int>();
int[] a = d;                     // CS0029 — 컬렉션끼리 암묵 변환은 없다
d[0] = 1;                        // CS1503 — 키 타입이 string 이다
var q = new Queue<int>();
int x = q[0];                    // CS0021 — 큐에는 인덱서가 없다
var s = new HashSet<int>();
int y = s[0];                    // CS0021 — 집합에도 없다
```

- ★★★ **이 목록이 짧은 것이 이 주제의 성질이다.** 컴파일러가 막는 것은 **타입이 안 맞는 자리**뿐이고,
  이 주제의 진짜 사고(순회 순서·키 계약·박싱)는 **전부 통과한다**((11)).
- ★ `new()` 는 타겟 타입 `new`(C# 9)다 — [04번](../04-var-and-target-typed-new/)이 정본이다.
- ★ `Dictionary` 에 넣는 법이 **셋**(`[k] = v` · `Add` · `TryAdd`)이고 **중복 키에서 셋이 다 다르다** —
  덮기 · 던지기 · `false`. 11번 주제의 초기화자 두 꼴이 이 중 앞의 둘로 갈린다.

## 어디서 틀리나

### 1. ★★★ 「돌려 봤는데 순서가 안 바뀌던데」

스무 번을 돌려도 안 바뀐다((5)). **갈리는 것은 판이 아니라 연산**이다 — 지웠다 넣어 보라((4)).\
★ 「여러 번 돌려 보라」라는 평소의 처방이 **이 주제에서는 듣지 않는다.**

### 2. ★★★ 「`Keys` 를 그대로 CSV 헤더로 쓴다」

열 순서가 **데이터가 지워졌다 채워진 뒤에** 바뀐다. 테스트는 **새로 만든 딕셔너리**로 도니까 안 잡힌다.\
★ 고치는 법은 **순서를 코드가 정하는 것**이다 — `OrderBy` 든 고정 배열이든.

### 3. ★★ 「`Equals` 를 재정의했으니 키로 쓸 수 있다」

`CS0659` 가 났는데 경고라서 지나갔다((6)). **중복이 다 들어가고 `Contains` 가 `False`** 다.

### 4. ★★ 「키로 쓰는 객체의 필드를 고친다」

경고가 **아예 없다.** 못 찾고 못 지우는 유령이 남는다((6)).\
★ **키로 쓸 타입은 불변으로 만드는 것**이 유일한 처방이다 — 18번 주제의 `record` 가 그 도구다.

### 5. ★★ 「`struct` 키는 값 타입이라 빠르겠지」

`IEquatable<T>` 가 없으면 **조회마다 72바이트**를 낸다((8)). 참조 타입 키보다 **더** 낼 수도 있다.

### 6. ★ 「`Add` 한 번 했으니 Capacity 는 4 다」

`List` 는 4 지만 `HashSet`·`Dictionary` 는 **3** 이다((2)). **셋이 다른 규칙**이고, 셋 다 보장이 아니다.

### 7. ★ 「`Dictionary` 에서 순회 중 `Remove` 가 됐으니 `List` 도 되겠지」

`List` 는 **던진다**((9)). 완화된 것은 `Dictionary`(와 `ConcurrentDictionary`) 쪽뿐이다.

### 8. ★ 「`Stack` 을 순회하면 넣은 순서로 나오겠지」

**거꾸로** 나온다((7)). `ToArray()` 도 거꾸로다 — 그리고 이것은 **계약**이라 안 바뀐다.

### 9. ★ 「`ArrayList` 나 `List<object>` 나 같은 거 아닌가」

`List<object>` 도 `int` 를 담을 때 **박싱한다.** 박싱을 없애는 것은 **제네릭 인자가 값 타입인 것**이지
제네릭을 쓴다는 사실이 아니다((8)).

## 구현 세부사항 대 언어 보장

| 사실 | 누가 정하나 | 근거 |
|---|---|---|
| `Dictionary` 순회가 **삽입 순서처럼 보이는 것** | ★★★ **BCL 구현** | (3)·(4) — 문서는 「순서 없음」이라고만 적는다 |
| **빈 자리를 나중 것부터 재사용하는 것** | ★★★ **BCL 구현** | (4) — 문서에 한 마디도 없다 |
| `Keys` 와 `Values` 의 **순서가 서로 같은 것** | ★ **문서가 약속** | .NET API 문서 |
| 순회 중 **`Remove` 가 되는 것** | ★★ **문서가 약속**(.NET Core 3.0부터) | (9) |
| 순회 중 **`Add` 가 던지는 것** | 문서가 약속 | (9) |
| Capacity 수열 `4·8·16` · `3·7·17·37·89` | ★★ **BCL 구현** | (2) — 문서는 「자동 재할당」까지만 |
| `new HashSet<int>(5).Capacity == 7` | **BCL 구현** | (2) |
| **문자열 해시가 프로세스마다 다른 것** | ★ **런타임 구현**(해시 DoS 방어) | (5) — 그래서 값을 본문에 안 실었다 |
| 조회 한 번에 **72바이트** | **런타임 구현** | (8) — 박스 24 × 3 이 맞아떨어진다 |
| `ObjectEqualityComparer` / `GenericEqualityComparer` 라는 **이름** | **BCL 내부 타입** | (8) — 공개 계약이 아니다 |
| `Stack` 순회가 **LIFO** 인 것 | ★ **문서가 약속** | (7) |
| `Queue` 가 **FIFO** 인 것 | ★ **문서가 약속** | (7) |
| `Equals` 와 `GetHashCode` 의 **일관성 요구** | ★ **`Object.GetHashCode` 문서의 계약** | (6) |
| `CS0659` 경고가 나는 것 | **컴파일러(Roslyn)** | (6)·(11) |

★★★ **이 표의 무게가 위쪽에 쏠려 있는 것이 이 주제의 결론이다.**\
「순서」라는 한 낱말 안에 **보장 셋과 구현 둘**이 섞여 있고, 그것을 안 가르면
**`Stack` 에서 통하던 직관을 `Dictionary` 에 그대로 쓰게 된다.**

## 언제 쓰고 언제 안 쓰나

- **`List<T>`** — 순서가 뜻을 갖거나 인덱스로 찾을 때. **`Contains` 를 자주 부르면 바꿔라**(O(n)).
- **`Dictionary<K,V>`** — 키로 찾을 때. ★ **순회 순서에 기대는 순간 잘못 고른 것**이다.
- **`HashSet<T>`** — 「있나 없나」와 집합 연산. 값을 들고 있을 필요가 없을 때.
- **`Queue<T>`/`Stack<T>`** — 처리 순서가 FIFO/LIFO 일 때. ★ **`List` 로 흉내 내지 마라** —
  `list.RemoveAt(0)` 은 **O(n)** 이다.
- **`SortedDictionary`/`SortedList`/`SortedSet`** — 정렬된 순회가 **자주** 필요할 때((10)).
  한 번만 필요하면 `OrderBy` 가 싸다.
- **`ArrayList`·`Hashtable`** — 쓰지 마라. 박싱하고((8)) 타입 안전하지 않다. 1.x 호환용이다.
- ★ **동시성이 걸리면 이 넷 중 아무것도 안전하지 않다** — `ConcurrentDictionary` 계열이 따로 있고,
  그 축은 이 목록 밖이다(README 의 「뺀 것」).

## 핵심 문장

- ★★★ **`Dictionary` 의 순회 순서는 보장이 아니다** — 그런데 **스무 판을 돌려도 안 갈린다**((5)).
  갈리게 하려면 **삭제와 추가를 섞어야** 한다((4)).
- ★★★ **이 런타임은 무작위화를 한다 — 다만 해시에만 한다.** 순회는 해시가 아니라
  **`entries` 배열의 차례**를 따라서 그 무작위가 안 새어 나온다((5)).
- ★★★ **Python 은 승격했고 Go 는 일부러 섞고 C# 은 둘 다 안 했다.** 같은 관찰에 세 언어가 세 답을 냈다((3)).
- ★★ **넷은 자료구조가 아니라 접근 패턴으로 고른다**((1)). 「순서」가 어떤 타입에는 계약이고
  어떤 타입에는 아니다((7)·(9)).
- ★★ **키 계약을 어기면 터지지 않고 값이 사라진다**((6)). C# 은 경고 한 줄, Python 은 차단, Rust 는 컴파일 에러다.
- ★★ **제네릭이 박싱을 없애는 것은 「담을 때」뿐**이다 — **키로 쓸 때는 `IEquatable<T>`** 가 있어야 0 이 된다((8)).
- ★ **Capacity 증가 규칙은 셋이 다르고 셋 다 구현이다**((2)).
- ★ **이 주제의 사고는 컴파일러가 거의 안 잡는다** — 탐침 8개 중 답한 것 1개((11)).

## 관련 자료

- ★★ [`data-structure/01-dynamic-array/`](../../../../../data-structure/01-dynamic-array/) —
  **경계**: **동적 배열의 원리**(왜 두 배로 늘리나 · 상환 O(1) 의 유도)는 **거기**다.
  여기는 **.NET 의 `List<T>` 가 실제로 어느 수열을 쓰고 그것이 보장인가**((2))부터다.
- ★★ [`data-structure/05-hashmap/`](../../../../../data-structure/05-hashmap/) —
  **경계**: **해시 표의 원리**(해시 함수·버킷·충돌 해결·적재율·재해싱)는 **거기**다.
  여기는 **BCL 의 `Dictionary` 가 순회 순서를 왜 안 약속하나**((3))부터다.
- [`data-structure/03-stack/`](../../../../../data-structure/03-stack/) ·
  [`data-structure/04-queue-deque/`](../../../../../data-structure/04-queue-deque/) —
  **경계**: 스택·큐의 **정의와 구현**은 거기, 여기는 **BCL 타입의 계약**((7))이다.
- [03번 — 박싱과 언박싱](../03-boxing-and-unboxing/) — **경계**: 박싱이 무엇이고 몇 바이트인가는 거기,
  여기는 **컬렉션 고를 때 그것이 어디서 나오나**((8))다. `cs-il.cs` 전문도 거기 있다.
- [09번 — 배열과 인덱스·범위 연산자](../09-arrays-index-and-range/) — **경계**: 배열과 `Span` 의 슬라이싱은 거기,
  여기는 **배열 위에 얹힌 컬렉션**이다.
- 목록의 **11번 주제** — 컬렉션 초기화와 컬렉션 식. ★ (2)의 마지막 두 줄이 그리로 이어진다.
- 목록의 **19번 주제** — `Equals`/`GetHashCode`/`==` 를 **일관되게 구현하는 법**이 거기다.
  여기는 **안 지켰을 때 컬렉션이 무엇을 하나**((6))까지다.
- 목록의 **31번 주제** — `foreach` 가 어떤 패턴으로 풀리나. (9)의 「순회 중 변경」이 그 위에 선다.
- Go 갈래 목록([`go/syntax/README.md`](../../../go/syntax/README.md))의 **9번**([`09-maps-declaration-comma-ok-delete-and-iteration-order/`](../../../go/syntax/09-maps-declaration-comma-ok-delete-and-iteration-order/)) —
  ★★ **정반대 설계**: 명세가 「정하지 않는다」고 못 박고 gc 가 **일부러 섞는다**.
- Python 갈래 목록([`python/syntax/README.md`](../../../python/syntax/README.md))의 **12번**([`12-dict-and-key-requirements/`](../../../python/syntax/12-dict-and-key-requirements/)) —
  ★★ **승격한 쪽**: 3.6 의 구현 세부가 3.7 에서 언어 보장이 됐다.
- Rust 갈래 목록([`rust/syntax/README.md`](../../../rust/syntax/README.md))의 **28번**([`28-partialeq-eq-partialord-ord-and-hash-contracts/`](../../../rust/syntax/28-partialeq-eq-partialord-ord-and-hash-contracts/)) —
  ★ **같은 실패 모드**: 계약을 어기면 터지는 게 아니라 값이 사라진다.

## 용어 풀이

- **컬렉션(collection)** — 여러 값을 담는 타입의 총칭. `System.Collections.Generic` 에 모여 있다.
- **제네릭 컬렉션** — 담을 타입을 `<T>` 로 받는 컬렉션. 값 타입이면 **전용 코드**가 생겨 박싱이 없다((8)).
- **`entries` 배열** — `Dictionary`·`HashSet` 이 원소를 **넣은 차례로 쌓는** 내부 배열. 순회가 이걸 훑는다((3)).
- **빈 자리 목록(free list)** — 지워진 칸을 이어 둔 사슬. **나중에 빈 것부터** 재사용된다((4)).
- **Capacity** — 지금 잡아 둔 **자리 수**. `Count`(실제 개수)와 다르다((2)).
- **비교자(`IEqualityComparer<T>`)** — 「같은가」와 「해시가 얼마인가」를 담당하는 객체. 컬렉션이 이것을 쓴다((8)).
- **`IEquatable<T>`** — 박싱 없이 같음을 묻는 인터페이스. 붙이면 `GenericEqualityComparer` 가 선택된다((8)).
- **FIFO / LIFO** — 먼저 온 것부터 / 나중 것부터. `Queue`/`Stack` 의 계약이다((7)).
- **해시 무작위화** — 문자열 해시의 씨앗을 프로세스마다 새로 뽑는 것. 해시 충돌 공격을 막는다((5)).
- **`KeyNotFoundException`** — 없는 키를 **읽을 때** 나는 예외. **쓸 때는 안 난다**((9)).
- **원형 버퍼(circular buffer)** — 배열의 앞뒤를 이어 쓰는 방식. `Queue<T>` 가 이걸 쓴다((7)).

## 더 들어가면

- **`Dictionary` 가 왜 삽입 순서처럼 보이나** — `buckets`(해시 → `entries` 첨자)와 `entries`(실제 저장) 두 배열을 쓰고,
  **순회는 `entries` 를 0번부터 훑는다.** 해시는 `buckets` 에만 쓰인다.
  ★ **그래서 해시를 아무리 무작위로 뽑아도 순회 순서에 안 닿는다**((5)).
- **`SortedList` 와 `SortedDictionary` 의 갈림** — 앞엣것은 **배열 두 개**(메모리 적고 가운데 삽입이 O(n)),
  뒤엣것은 **트리**(삽입 O(log n)). 「다 넣고 읽기만」이면 `SortedList`, 「계속 고칠 것」이면 `SortedDictionary` 다.
- **`CollectionsMarshal.GetValueRefOrAddDefault`** — 딕셔너리 값을 **참조로** 꺼내 두 번 조회를 없애는 API(.NET 6).
  `dict[k] = dict[k] + 1` 이 조회를 두 번 하는 것을 한 번으로 줄인다. ★ 이름이 `Marshal` 인 것이 경고다 —
  들고 있는 동안 딕셔너리를 고치면 안 된다.
- **동시성** — 이 넷은 **읽기만 동시에** 안전하다. 쓰기가 섞이면 `ConcurrentDictionary`·`ConcurrentQueue` 가 따로 있다.
  README 가 그 축을 이 목록에서 뺐다.
