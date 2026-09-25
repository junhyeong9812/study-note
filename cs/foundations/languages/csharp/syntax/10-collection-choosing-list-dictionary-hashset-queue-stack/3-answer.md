# csharp/syntax/10 — 컬렉션 선택: `List`·`Dictionary`·`HashSet`·`Queue`/`Stack` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 질문 → (막히면) 서머리 → 그래도 막히면 여기다.
> 번호는 [1-question.md](1-question.md)와 **1:1**이다.
> **예측형 정답은 「출력」이 맨 먼저**다 — 해설이 먼저 오면 답을 찾다가 해설을 지나친다.
> 블록은 전부 **캡처 스크립트가 받은 파일**이다. 손으로 옮겨 적은 줄은 없다.
> ★★★ **3·4·5는 한 덩어리다** — 「안 갈렸다」(3) → 「이렇게 갈랐다」(4) → 「그래서 몇 판이 근거인가」(5).

## 정답

### 1. **인덱스는 밀리고, `Add` 는 「새로 들어갔나」를 돌려주고, `Stack` 은 거꾸로 나온다**

**출력**

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

**왜 그런가**

- `Insert(1, "노랑")` 이 뒤를 한 칸씩 밀어 `"파랑"` 이 **3번**이 됐다. `List` 는 **순서가 계약**이다.
- ★ `HashSet.Add` 는 **`bool`** 이고 그 값은 「**새로 들어갔나**」다 — 이미 있으면 `False`.\
  `List.Add` 는 `void` 인데 시그니처가 다른 이유가 그것이다. **중복을 세는 코드가 `Contains` 를 따로 안 불러도 된다.**
- ★ `Stack` 의 순회는 **`C B A`** — `Push` 한 순서의 거꾸로다. 이건 **문서가 약속한 LIFO 순서**라 계약이다(7번).
- `Dictionary`·`HashSet` 을 찍은 줄도 「넣은 순서처럼」 보이는데, **그쪽은 계약이 아니다**(3번).

### 2. **`List` 는 2배, `HashSet`·`Dictionary` 는 소수 — 그리고 셋 다 구현이다**

**출력**

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

**왜 그런가**

| 컬렉션 | 수열 | 무엇인가 |
|---|---|---|
| `List<int>` | `0 → 4 → 8 → 16 → 32 → 64` | **2배** — 첫 칸만 4 |
| `HashSet<int>` | `0 → 3 → 7 → 17 → 37 → 89` | ★★ **소수** |
| `Dictionary<string,int>` | `0 → 3 → 7 → 17 → 37 → 89` | `HashSet` 과 같다 |

- ★★★ **어느 것도 문서가 약속한 적이 없다.** `List<T>.Capacity` 문서는
  「용량이 모자라면 **자동으로 재할당한다**」까지만 적는다 — **배율도, 첫 칸도 안 적는다.**
- ★★ **`new HashSet<int>(5)` 가 7** 인 것이 그 사실을 드러낸다. 해시 표는 **소수 크기**를 쓰려고
  올려 잡는다 — **준 값이 그대로 Capacity 가 되는 것은 `List` 뿐**이다.
- ★ 마지막 두 줄 — `new List<int> { 1, 2, 3 }` 은 **Capacity 4**(Add 를 세 번 부른다),
  `List<int> x = [1, 2, 3]` 은 **Capacity 3**(개수를 미리 안다). **11번 주제가 그 갈림을 다룬다.**

### 3. ★★★ **넣은 순서로 보이지만 해시 순서는 아니고, 지웠다 넣으면 깨진다**

**출력**

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

**왜 그런가**

- ①만 보면 「삽입 순서 보장」으로 읽힌다. **⑤가 그 오해를 한 번 거른다** — 거꾸로 넣으면 거꾸로 나오므로
  **해시 순서가 아니다.** 순회는 **`entries` 배열을 0번부터 훑는다.**
- ★★★ **③에서 깨진다.** `foxtrot` 이 **맨 뒤가 아니라 `alpha` 바로 뒤**다 —
  `bravo` 가 비운 1번 칸을 그대로 받았다.
- ★ **삭제 없이 추가만 하면(④·⑦) 영원히 안 깨진다.** 그래서 대부분의 코드가 함정을 안 밟고 지나간다.
- ★★ **⑦은 리사이즈를 두 번 지나도(3 → 7 → 17) 순서가 유지된다.** 재해싱이 `buckets` 만 다시 만들고
  **`entries` 의 차례는 안 건드리기 때문**이다.
- ★★ **문서가 약속한 줄은 둘**이다 — 「순서는 정해지지 않았다」와 「**`Keys` 와 `Values` 의 순서는 서로 같다**」.\
  ★ **「순서 없음」이라고 다 없는 것이 아니다** — 약속한 것과 안 한 것을 갈라 읽어라.
- ★★★ **`buckets` 와 `entries` 중 순회가 훑는 것은 `entries` 다.** 해시는 **`buckets` 에만** 쓰인다 —
  그래서 해시를 아무리 무작위로 뽑아도(5번) 순회 순서에 안 닿는다.\
  ★ 같은 이유로 **순회 비용은 `Count` 가 아니라 Capacity 에 비례**한다(지워진 칸도 훑는다).

### 4. ★★★ **`a Y c X e`** — 먼저 넣은 `X` 가 `Y` 보다 뒤에 나온다

**출력**

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

**왜 그런가**

```text
   entries   [0]a  [1]b  [2]c  [3]d  [4]e

   Remove("b")   →  [1] 이 빈 자리가 된다            free: 1
   Remove("d")   →  [3] 도 빈 자리가 된다            free: 3 → 1   ★ 나중 것이 앞에 선다

   d["X"] = 0    →  free 의 머리(3) 를 쓴다          [3] = X
   d["Y"] = 0    →  다음(1) 을 쓴다                  [1] = Y

   entries   [0]a  [1]Y  [2]c  [3]X  [4]e
   순회       a  →  Y  →  c  →  X  →  e             ★ 넣은 순서가 뒤집혔다
```

- ★★★ **빈 자리 목록이 스택처럼 동작한다** — 나중에 빈 칸부터 채운다.\
  그래서 `X`(먼저) 가 `Y`(나중) 보다 **뒤**에 나온다. 「넣은 순서가 아니다」 정도가 아니라 **역전**이다.
- ★★ **`HashSet` 도 같다.** 둘이 같은 `entries` + free list 구조를 쓴다.
- ★★★ **여러 번 돌려서는 절대 못 잡는다.** 같은 프로그램을 몇 번 돌려도 같은 답이 나온다(5번).\
  **갈리게 하는 것은 판이 아니라 연산**이다 — 「반증이 확증보다 강하다」를 **판이 아니라 연산으로** 실행한 것이다.
- ★★ **Python 과 여기서 정확히 갈린다** — Python 은 지우고 넣으면 **맨 뒤**로 가고, 그것이 **언어 보장**이다.\
  C# 은 **빈 자리로** 가고, 그것은 **아무 약속도 아니다.**

### 5. ★★★ **순회는 1가지, 해시는 20가지** — 무작위화는 있는데 순회에 안 닿는다

**출력**

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

**왜 그런가**

- ★★★ **같은 20판에서 한 줄은 한 가지, 다른 한 줄은 스무 가지다.**\
  이 런타임은 **문자열 해시의 씨앗을 프로세스마다 새로 뽑는다**(해시 충돌 공격을 막으려고).\
  **무작위화가 없어서 순회가 같은 게 아니라, 있는데 그 값에 안 닿아서** 같다(3번의 `entries`).
- ★★★ **그래서 「스무 번 돌려도 같았다」는 아무것도 증명하지 못한다.**\
  구현이 순회 방식을 바꾸면 같은 프로그램이 매 판 달라지고, **아무도 계약을 어긴 게 아니다.**
- ★★ **한 판의 출력을 안 싣고 「가짓수」를 실었다.** 해시값 스무 개를 실으면 다시 돌릴 때마다 전부 어긋난다 —\
  **가짓수 20 은 다시 돌려도 20** 이다. 32비트 값 스무 개가 겹칠 확률은 1억 분의 1 남짓이다.
- ★ **Python 도 같은 구조다** — `PYTHONHASHSEED` 가 해시를 흔드는데 dict 순서는 안 흔들린다.\
  **「해시가 무작위다」와 「순서가 무작위다」는 다른 문장**이고, Go 만 **뒤엣것**을 한다.

### 6. ★★ **경고 하나(`CS0659`)가 나고, 중복 셋이 다 들어가고, `Contains` 가 `False` 다**

**출력**

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

**왜 그런가**

| 심은 것 | 컴파일러 | 실행 |
|---|---|---|
| `Equals` 만 재정의 | ★ **경고 `CS0659`** | `Count = 3` · `Contains = False` |
| 둘 다 재정의 | 조용 | `Count = 1` · `Contains = True` |
| 넣은 뒤 키를 고침 | ★★ **아무 말 없음** | `Contains`·`Remove` 가 `False` 인데 **순회하면 보인다** |

- ★★★ **어기면 터지지 않고 값이 사라진다.** `GetHashCode` 가 없으면 `object` 의 기본 구현
  (객체마다 다른 값)이 쓰여 **같은 값인 셋이 서로 다른 칸**으로 간다.\
  `Equals` 는 여전히 `True` 인데 **그 `Equals` 가 불릴 기회가 없다** — 해시가 다르면 아예 비교를 안 한다.
- ★★★ **가변 키는 그 어떤 경고도 없다.** 넣을 때의 해시 자리에 앉은 채 값만 바뀌어,
  **못 찾고 못 지우는 유령**이 된다. `Count` 는 1 인데 `Remove` 가 `False` 다.
- ★ **세 언어가 세 단계로 다르다** —\
  **Python**: `__eq__` 만 정의하면 `__hash__` 를 **`None` 으로 꺼** 버려 키가 못 된다(차단).\
  **Rust**: `Hash` 를 안 달면 **컴파일 에러**(차단).\
  **C#**: **경고 한 줄**을 내고 통과시킨다.
- ★ 그래도 **실패 모드는 Rust 28번과 똑같다** — 「터지는 게 아니라 값이 사라진다」.
  차단 여부가 달라도 **어겼을 때 일어나는 일은 같다.**

### 7. **계약이다** — `Dictionary` 의 순서와 정반대 자리

**출력**

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

**왜 그런가**

- ★★ **`Stack<T>` 의 순회와 `ToArray()` 가 LIFO 인 것은 문서가 약속한 것**이다.\
  `Dictionary` 의 순서는 같은 문서가 「**정해지지 않았다**」고 적는다 —\
  **같은 「순서」라는 낱말이 타입에 따라 보장이기도 하고 아니기도 하다.**
- **빈 큐** — `Dequeue()` 는 `InvalidOperationException: Queue empty.` 를 던지고,
  `TryDequeue` 는 **`false` 와 `out` 기본값**(`null`)을 준다.\
  ★ **되돌림 방식이 다르므로 둘을 섞어 쓰지 마라** — `out` 은 실패하면 `default` 다.
- ★ **`3 4 5 6 7`** 은 `Queue<T>` 가 **원형 버퍼**라서다. 앞에서 뺀 칸을 뒤에서 재활용하므로
  3번 빼고 3번 넣어도 배열을 새로 잡지 않는다.\
  원리는 [`data-structure/04-queue-deque/`](../../../../../data-structure/04-queue-deque/)가 정본이다.

### 8. **.NET Core 3.0부터 문서가 「`Remove` 는 된다」고 약속했다**

**출력**

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

**왜 그런가**

| 한 일 | 결과 | 누가 정하나 |
|---|---|---|
| 없는 키 **읽기** | `KeyNotFoundException` | 계약 |
| 없는 키 **쓰기** | 조용히 만든다 | 계약 |
| 순회 중 **새 키 Add** | `InvalidOperationException` | 계약 |
| 순회 중 **`Remove`** | ★★ 안 터진다 | ★★ **계약**(.NET Core 3.0부터) |
| 순회 중 **덮어쓰기** | 안 터진다 | 계약(같은 문서 줄) |
| `List` 순회 중 `Add` | `InvalidOperationException` | 계약 — **완화가 없다** |

- ★★★ **이것이 「구현 세부가 계약으로 승격한」 사례다.** 원래는 버전 의존 동작이었는데
  .NET Core 3.0 에서 **문서에 한 줄이 붙으면서** 약속이 됐다.\
  ★ **3번의 순회 순서는 그 승격이 안 일어난 자리**다 — **같은 타입 안에서 두 갈래가 갈린다.**
- ★★ **`List<T>` 에는 그 완화가 없다.** 「`Dictionary` 에서 되니까」가 여기서 깨진다.\
  `List` 는 원소를 밀어내야 해서 **순회 위치 자체가 무효**가 되지만,
  `Dictionary` 의 `Remove` 는 `entries` 의 한 칸만 비우므로 훑던 첨자가 여전히 유효하다.
- ★ **인덱서의 읽기와 쓰기가 다른 것**은 `Dictionary` 의 설계다 — 읽기는 「있어야 한다」,
  쓰기는 「없으면 만든다」. `List` 는 **둘 다 범위 안이어야** 한다.

### 9. ★★ **박스 셋 × 24바이트 = 72** — `IEquatable<T>` 하나의 차이다

**출력**

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

**왜 그런가**

- ★★★ **조회 한 번에 72바이트 = 24 × 3.**\
  `IEquatable<T>` 가 없으면 `EqualityComparer<T>.Default` 가 **`ObjectEqualityComparer`** 를 고르고,
  그 비교자는 `object.Equals(object)` 로 내려간다 —\
  **`GetHashCode` 에서 한 번, `Equals` 의 양쪽에서 두 번**, 합쳐 **박스 셋**이다.
- ★★ **비교자 타입 이름이 그 사실을 말해 준다** —
  `ObjectEqualityComparer` / `GenericEqualityComparer` / `StringEqualityComparer`.\
  ★ 이름에 `Object` 가 박힌 쪽이 **`object` 를 지나간다**는 뜻이고, 그것이 곧 박싱이다.
  ★ **다만 이 이름들은 BCL 내부 타입이라 공개 계약이 아니다** — 이름이 바뀌어도 아무도 안 알려 준다.
- ★★ **IL 이 담는 쪽을 못 박는다** — `ArrayList.Add` 앞에 **`box System.Int32`** 가 있고
  `List<int>.Add` 앞에는 **없다.** 제네릭이 `int` 전용 코드를 만들기 때문이다([03번](../03-boxing-and-unboxing/)).
- ★★★ **그래서 「제네릭이 박싱을 없앤다」는 담을 때에만 맞다.**
  **키로 쓸 때는 `IEquatable<T>` 를 직접 붙여야** 0 이 된다 — 제네릭만으로는 안 된다.
- ★ **시간은 재지 않았다.** 이 답의 근거는 **바이트뿐**이다.

### 10. ★★ **여덟 중 하나** — `CS0659` 만 답했고 `cc exit=0` 이다

**출력**

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

**왜 그런가**

- ★★★ **탐침 8개 중 진단이 난 것은 1개**다. 나머지 일곱 — 박싱 · `IEquatable` 없는 struct 키 ·
  순회 순서에 기댄 코드 · 가변 키 · 순회 중 삭제 · Capacity 에 기댄 코드 · `GetHashCode` 만 재정의 —
  는 **`-warn:9` 에서도 한 줄도 안 난다.**
- ★★ **「경고가 안 났다」와 「안 물어봤다」를 가르려고 최대 경고 수준으로 던졌다.**
  블록의 `cc exit=0` 과 **한 줄짜리 출력**이 그 증거다 — **물었고, 한 군데만 답했다.**
- ★★ **탐침 7·8의 비대칭** — `Equals` 만 재정의하면 `CS0659` 가 나는데
  **`GetHashCode` 만 재정의하면 아무 말이 없다.**\
  뒤엣것은 **동작이 안 틀리기 때문**이다(해시가 뭉쳐 느려질 뿐 답은 맞다).\
  ★ **컴파일러가 잡는 것은 「답이 틀리는 방향」 하나뿐**이다.
- ★ **그래서 이 주제의 안전망은 진단이 아니라 테스트다.** 순회 순서 의존은
  **키를 지웠다 넣는 테스트**로만 잡힌다(4번).

### 11. **있나 없나면 `HashSet`, 넣은 순서가 필요하면 `Dictionary` 로는 안 된다**

**왜 그런가**

- 「**이미 본 것인지만 알면 된다**」 → **`HashSet<T>`**. 값을 들고 있을 필요가 없고 `Add` 가
  「처음 보는 것인가」를 바로 돌려준다.
- 「**순서대로 꺼내되 넣은 순서를 지켜야 한다**」 → ★★ **`Dictionary` 로는 안 된다.**\
  BCL 에 **「삽입 순서를 보장하는 딕셔너리」가 없다.** `List<K>` 로 순서를 따로 들고 있거나,
  값에 순번을 넣어 꺼낼 때 정렬해야 한다.\
  ★ **정렬된 순회**라면 `SortedDictionary`·`SortedList`·`SortedSet` 이 답이지만,
  **그것은 다른 요구**다(「키 순서」≠「넣은 순서」).
- ★ `list.RemoveAt(0)` 은 **O(n)** 이다 — 뒤를 전부 한 칸씩 당긴다.
  `Queue<T>` 는 원형 버퍼라 **O(1)** 이다(7번). **큐를 `List` 로 흉내 내면 여기서 진다.**

### 12. ★ **같은 관찰에 네 언어가 네 답을 냈다**

**왜 그런가**

| 언어 | 순회 순서 | 키 계약 위반 |
|---|---|---|
| **Go** | ★ **무작위** — 명세가 「정하지 않는다」고 못 박고 gc 가 **일부러 섞는다** | (맵 키는 `==` 가 되면 된다) |
| **Python** | ★ **삽입 순서 — 언어 보장**(3.7부터. 3.6 에서는 CPython 구현) | ★ **차단** — `__hash__` 를 `None` 으로 끈다 |
| **C#** | ★★★ **보장 없음** · 관찰은 삽입 순서처럼 | ★ **경고 한 줄**(`CS0659`) 뒤 통과 |
| **Rust** | (`HashMap` 은 무작위 씨앗) | ★ **컴파일 에러** — `Hash` 가 없으면 키가 못 된다 |

- ★★ **Go 가 섞는 목적은 「사람이 기대지 못하게」다.** .NET 은 안 섞으므로 **기대는 코드가 쓰이고,
  그 코드가 대개 잘 돈다** — 그래서 사고가 **늦게, 운영에서** 난다.
- ★★ **Python 은 승격시켰다.** 같은 「오래 안 바뀐 관찰」을 C# 은 20년 넘게 승격하지 않았다 —\
  ★ **「오래 안 바뀌었으니 보장이겠지」가 여기서 깨진다.**
- **[03번](../03-boxing-and-unboxing/)과 잇기** — 제네릭이 박싱을 없애는 것은 **담을 때**다.
  **찾을 때는 `IEquatable<T>` 가 있어야** 한다(9번).
- **[09번](../09-arrays-index-and-range/)과 잇기** — `List<T>` 는 안쪽에 **`T[]` 배열 하나**를 들고
  Capacity 가 모자라면 새 배열로 옮긴다. `list[1..^1]` 이 되는 것도 `List<T>.Slice`(.NET 8) 때문이다.

## 실행 검증

| 무엇을 | 어떻게 | 몇 번 |
|---|---|---|
| 출력·진단·IL·할당 바이트 전부 | `capture.sh` 가 파일로 받고 조립기가 끼워 넣음 | **캡처 2회**(제출 전 재대조 포함) |
| 순회 순서의 안정성 | 같은 바이너리를 **20판** 돌려 `sort -u` 로 가짓수 | 1가지 |
| 문자열 해시의 무작위성 | 같은 20판에서 `sort -u` | 20가지 |
| C# 판 | `dotnet --version` → `10.0.401` · 런타임 `10.0.12` · `net10.0` · linux-x64 | — |
| 진단 언어 | `DOTNET_CLI_UI_LANGUAGE=en` + `-preferreduilang:en-US` | — |

**구현 의존 항목**(판이 오르면 다시 찍을 것)

- Capacity 수열(`4·8·16` / `3·7·17·37·89`) — (2)
- `Dictionary`·`HashSet` 의 순회 순서와 빈 자리 재사용 — (3)·(4)
- 할당 바이트(4592 · 1184 · 7200 · 72) — (9)
- 비교자 타입 이름(`ObjectEqualityComparer` 등) — (9)
- `PriorityQueue` 의 동률 순서 — 서머리 (10)

**안 흔들리는 것**(판이 올라도 근거로 남는 것)

- 문서가 약속한 줄(`Keys`/`Values` 순서 일치 · 순회 중 `Remove` · `Stack` 의 LIFO · `Queue` 의 FIFO)
- 진단 코드와 문구(`CS0659`) · 예외 타입과 메시지 · `cc exit` / `run exit`
- IL 에 `box` 가 있나 없나
- **20판의 가짓수**(1 대 20)
