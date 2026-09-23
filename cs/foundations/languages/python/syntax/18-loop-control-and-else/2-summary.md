# python/syntax/18-loop-control-and-else — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **이 본문은 원고가 아니라 Claude 작성이다**(문법·API 갈래는 원고 없이 공식 문서로 접지한다).
>
> **기준 소스** — 열어서 확인한 것만.
> - [8.3. The `for` statement](https://docs.python.org/3.12/reference/compound_stmts.html#the-for-statement) — `else` 절과 `break`
> - [4. More Control Flow Tools](https://docs.python.org/3.12/tutorial/controlflow.html) — **순회 중 변경에 대한 경고**(언어 레퍼런스가 아니라 튜토리얼에 있다)
> - [8.2. The `while` statement](https://docs.python.org/3.12/reference/compound_stmts.html#the-while-statement) — `else` 가 도는 조건
> - [`enumerate`](https://docs.python.org/3.12/library/functions.html#enumerate) · [`zip`](https://docs.python.org/3.12/library/functions.html#zip)(**`strict`**) · [`range`](https://docs.python.org/3.12/library/stdtypes.html#ranges)
> - [`dis`](https://docs.python.org/3.12/library/dis.html) — 바이트코드
>
> **실행 검증** — 이 문서에 실린 출력은 전부 `python3` **3.12.3**(Linux, x86_64)에서 실제로 돌려 나온 것이다. 지어낸 출력은 없다.\
> ★ **던지는 형태를 하나로 고정했다** — `python3 - <파일` 로 던져 트레이스백이 `File "<stdin>", line N` 이 된다.
> 그래서 **실행 중 예외에는 소스 줄과 캐럿이 안 나온다.**\
> ★★ **`dis` 결과는 CPython 3.12.3 의 구현이지 언어 보장이 아니다.** 이 문서의 바이트코드 블록마다 그 표시를 달았다.\
> **수치** — `range` 의 `in` 시간은 `timeit` **중앙값을 세 판** 냈다. 머신은 Linux x86_64.\
> **버전** — `for`/`while`·`else`·`break`·`continue`·`enumerate`·`range` 는 이 노트 범위(3.10\~3.13)에서 안 바뀌었다.
> 갈리는 것은 하나다 — **`zip(..., strict=True)` 가 3.10 부터**(PEP 618). 3.11.15 에서도 같은 문구가 나왔다(대조 확인).\
> **★ 흔들리는 칸 / 안 흔들리는 칸** — 재대조에서 「고칠 것」과 「설계상 안 맞는 것」을 기계적으로 가르려고 미리 선언한다.
>
> | 흔들린다 | 안 흔들린다(근거로 써도 되는 칸) |
> |---|---|
> | `range` 의 `in` **나노초 값** | 「크기를 100만 배로 해도 안 변한다」는 성질 |
> | (판이 오르면) 바이트코드 **명령 이름·오프셋** | `else` 블록이 **정상 종료 경로에만** 놓인다는 배치 |
> | (판이 오르면) `RuntimeError`·`ValueError` **문구** | 예외 **종류** · `File "<stdin>", line N` |
> | (판이 오르면) `getsizeof(range(...))` = `48` | **순회 중 `remove` 의 결과 `['a','c','d','e']`** — 커서 규칙의 결과라 결정적이다 |
>
> **선행** — [16-iterator-protocol](../16-iterator-protocol/2-summary.md)(**`for` 가 안에서 무엇을 부르나 — 정본**) ·
> [09-sequence-ops-and-slicing](../09-sequence-ops-and-slicing/2-summary.md)(시퀀스와 슬라이싱) ·
> [12-dict-and-key-requirements](../12-dict-and-key-requirements/2-summary.md)·[13-set-and-frozenset](../13-set-and-frozenset/2-summary.md)(순회 중 변경의 짝).

## 한눈에 — 쉽게 말하면

**`else` 는 「아니면」이 아니라 「끝까지 갔으면」이다.**

이름이 잘못 붙은 문법이라 그렇게 읽힌다. 실제로는 **`nobreak`** 라고 읽어야 맞는다.

```text
   for x in xs:                      ┌ break 를 만났나?
       if 조건:                      │
           break          ───────────┘ 그렇다 ──> else 를 건너뛴다
   else:
       못 찾았을 때                    아니다 ──> else 가 돈다
                                      (빈 xs 도 "아니다" 다)
```

★ **`break` 가 없으면 `else` 는 언제나 돈다** — 심지어 **한 번도 안 돌았어도** 돈다.

**비유 대응표** — 이 문서는 끝까지 이 대응을 지킨다.

| 비유 | 실체 | 확인하는 법 |
|---|---|---|
| 「끝까지 갔으면」 | `for`/`while` 의 `else` | `break` 를 넣었다 뺐다 해 본다 |
| 중간에 나가면 못 받는 도장 | `break` 가 `else` 를 건너뛴다 | `dis` — `break` 가 `else` 블록을 **뛰어넘는다** |
| 한 칸 쉬는 것은 나가는 게 아니다 | `continue` 는 `else` 를 안 건드린다 | 돌려 보면 `else` 가 돈다 |
| ★ **줄 서 있는데 앞사람이 빠지면 한 명을 건너뛴다** | 순회 중 리스트 변경 | **예외가 없다.** 결과만 틀린다 |
| 줄 자체가 바뀌면 진행이 막힌다 | 순회 중 dict·set 변경 | `RuntimeError` 로 **터진다** |
| 짧은 줄에 맞춰 끝낸다 | `zip` | 남은 쪽은 버려진다 — **한 개는 삼켜진다** |
| ★ **`range` 는 번호표가 아니라 기계다** | `range` 는 시퀀스 | `iter(r) is r` 이 `False` |

**똑같은 구조다** — 실무에서 이게 물리는 자리도 굳어 있다.\
「**순회하면서 지웠더니 하나 걸러 남았다**」와 「**`zip` 으로 묶었더니 데이터가 조용히 줄었다**」가 그것이다.
둘 다 **에러가 안 난다.**

> **`break`** — 루프를 즉시 빠져나가는 것. **`else` 를 건너뛴다.**\
> 예: 「찾았으니 그만」. 찾았다는 사실이 `else` 를 안 도는 것으로 표현된다.

> **`continue`** — 이번 회차만 건너뛰고 다음 회차로 가는 것. **`else` 는 그대로 돈다.**\
> 예: 「이건 건너뛰고 계속」. 루프를 나간 것이 아니다.

## 이 주제가 답하려는 질문

1. **`else` 는 언제 도나** — 「아니면」으로 읽으면 왜 틀리나. 바이트코드에서 그 `else` 는 **어디에 붙어 있나.**
2. **순회 중에 컨테이너를 바꾸면 무엇이 일어나나** — 왜 어떤 것은 터지고 어떤 것은 **조용히 틀리나.**
3. **`range`·`enumerate`·`zip` 중 무엇이 다시 돌 수 있나** — 셋을 한 묶음으로 외우면 어디서 틀리나.

## 동작 방식

> 이 절이 본문이다. 이 주제의 네 번째 창은 **`dis`** 다 —
> 「`else` 가 어디에 붙어 있나」는 소스만 봐서는 **대칭으로 보이고**, 바이트코드에서는 **대칭이 아니다.**

### 1. ★ `else` 는 별도 블록이 아니다 — 루프의 정상 종료 뒤에 이어 붙는다

**언제 쓰나** — 「끝까지 찾았는데 없더라」를 플래그 변수 없이 쓸 때.

```text
===== 소스: ex.py =====
import sys
print("python", ".".join(map(str, sys.version_info[:3])))

def find(xs, target):
    for x in xs:
        if x == target:
            print("  찾음:", x)
            break
    else:
        print("  else 가 돌았다 — 끝까지 못 찾음")

print("[1,2,3] 에서 2 :"); find([1, 2, 3], 2)
print("[1,2,3] 에서 9 :"); find([1, 2, 3], 9)
print("빈 리스트에서 9 :"); find([], 9)
```

```text
python 3.12.3
[1,2,3] 에서 2 :
  찾음: 2
[1,2,3] 에서 9 :
  else 가 돌았다 — 끝까지 못 찾음
빈 리스트에서 9 :
  else 가 돌았다 — 끝까지 못 찾음
```

★ **빈 리스트에서도 `else` 가 돈다.** 「한 번도 안 돌았으니 `else`」가 아니라 「**`break` 를 안 만났으니 `else`**」다.
`if`/`else` 로 읽으면 이 줄에서 틀린다.

**★ 바이트코드로 보면 `else` 가 어디 붙어 있는지 보인다**

```text
===== 소스: ex.py =====
import dis
src = """
for x in xs:
    if x:
        break
else:
    found = 0
after = 1
"""
print("===== 소스: 위 for ... else =====")
dis.dis(compile(src, "<forelse>", "exec"))
```

```text
===== 소스: 위 for ... else =====
  0           0 RESUME                   0

  2           2 LOAD_NAME                0 (xs)
              4 GET_ITER
        >>    6 FOR_ITER                 8 (to 26)
             10 STORE_NAME               1 (x)

  3          12 LOAD_NAME                1 (x)
             14 POP_JUMP_IF_TRUE         1 (to 18)
             16 JUMP_BACKWARD            6 (to 6)

  4     >>   18 POP_TOP

  7          20 LOAD_CONST               1 (1)
             22 STORE_NAME               3 (after)
             24 RETURN_CONST             2 (None)

  2     >>   26 END_FOR

  6          28 LOAD_CONST               0 (0)
             30 STORE_NAME               2 (found)

  7          32 LOAD_CONST               1 (1)
             34 STORE_NAME               3 (after)
             36 RETURN_CONST             2 (None)
```

★★ **이 결과는 CPython 3.12.3 의 구현이지 언어 보장이 아니다.** 명령 이름도 오프셋도 판마다 바뀐다.\
그래도 **모양이 말해 주는 것**은 분명하다.

```text
   정상 종료 경로                       break 경로
   ─────────────────                  ─────────────────
   FOR_ITER 가 소진되면                POP_JUMP_IF_TRUE -> 18
        └─> 26 END_FOR                      18 POP_TOP   (이터레이터를 버린다)
            28 LOAD_CONST 0  ┐                20 LOAD_CONST 1 ┐
            30 STORE_NAME found │ else          22 STORE_NAME after │ 루프 다음 줄
            32 LOAD_CONST 1  ┐                24 RETURN_CONST
            34 STORE_NAME after │ 루프 다음 줄
```

그림 해설 — 오프셋을 따라 읽는다.

- ★ **`else` 블록(28\~30)은 `END_FOR`(26) **바로 뒤**에 있다.** 즉 **루프가 정상으로 빠져나오면 그냥 흘러든다.**
  따로 검사하는 명령이 **하나도 없다** — 플래그도, 비교도 없다.
- ★★ **`break` 는 `else` 를 「건너뛰는」 것이 아니라 아예 다른 자리(18)로 뛴다.**
  거기서 곧장 `after = 1`(20\~22)로 가고 **26\~30 을 쳐다보지도 않는다.**
- ★ **`after = 1` 이 두 번 나온다**(20\~24 와 32\~36). 컴파일러가 **루프 뒤 코드를 복제**해 붙인 것이다.
  두 경로가 각각 자기 꼬리를 갖는 모양이라, **`else` 는 「정상 종료 경로에만 놓인 코드」임이 드러난다.**

★★ **그래서 `else` 라는 이름이 틀린 것이다.** 조건이 없다. 「조건이 거짓일 때」가 아니라
「**`break` 라는 점프가 안 일어났을 때 자연히 지나가는 자리**」다.

**비용** — 플래그 변수(`found = False`)가 사라져 코드가 짧아진다.\
대신 **읽는 사람의 열에 아홉이 `if`/`else` 로 오독한다.** 팀 코드에서는 주석 한 줄이 필요하다.

### 2. `while ... else` 와 `continue`

**언제 쓰나** — 재시도 루프에서 「다 써도 못 했을 때」를 쓸 때.

```text
===== 소스: ex.py =====
n = 0
while n < 3:
    n += 1
else:
    print("while ... else  : 조건이 거짓이 되어 끝 -> else 돈다, n =", n)

n = 0
while n < 3:
    n += 1
    if n == 2:
        break
else:
    print("이 줄은 안 찍힌다")
print("break 로 끝난 while : else 는 안 돌았다, n =", n)

for i in range(3):
    if i == 1:
        continue
    print("  continue 는 else 를 건드리지 않는다 :", i)
else:
    print("  -> else 돌았다")
```

```text
while ... else  : 조건이 거짓이 되어 끝 -> else 돈다, n = 3
break 로 끝난 while : else 는 안 돌았다, n = 2
  continue 는 else 를 건드리지 않는다 : 0
  continue 는 else 를 건드리지 않는다 : 2
  -> else 돌았다
```

- `while` 의 `else` 는 **조건이 거짓이 되어 끝났을 때** 돈다. `for` 와 같은 규칙이다(`break` 만이 막는다).
- ★ **`continue` 는 `else` 를 안 건드린다.** 루프를 **나간 것이 아니기** 때문이다.
  `1` 이 건너뛰어졌는데도 `else` 가 돌았다.
- 「`break` 없는 `while ... else`」는 `else` 가 **항상** 도는 죽은 코드다 — 그런 코드를 보면 `break` 가 빠진 것이다.

**비용** — 재시도 루프에서 「전부 실패」 처리를 한 자리에 모을 수 있다.\
대신 `while True:` + `break` 두 개짜리 루프에서는 어느 `break` 가 어디로 가는지 헷갈린다.

### 3. ★★ 순회 중 변경 — 리스트는 조용히 건너뛰고 dict·set 은 터진다

**언제 쓰나** — 목록에서 조건에 맞는 것을 지울 때. 이 주제의 값이 여기 몰린다.

문서가 경고한다 — *"Code that **modifies a collection while iterating over that same collection** can be tricky to get right.
Instead, it is usually more straight-forward to **loop over a copy of the collection or to create a new collection**."*
★ **이 경고는 언어 레퍼런스가 아니라 튜토리얼에 있다** — 즉 「하지 마라」는 권고이고, 리스트에 대해서는 **언어가 막지 않는다.**

```text
   xs = [a, b, c, d, e]        이터레이터는 "정수 커서" 하나다

   커서 0 -> a               "b 를 지워라"
   커서 1 -> b   ──지움──>   xs = [a, c, d, e]
   커서 2 -> ?              원래 자리 2 는 'c' 였는데 지금은 'd' 다
              ^^^
              ★ c 를 건너뛴다. 예외 없음
```

```text
===== 소스: ex.py =====
print("--- 순회 중 remove — 예외가 없다 ---")
xs = ["a", "b", "c", "d", "e"]
seen = []
for x in xs:
    seen.append(x)
    if x in ("b", "c"):
        xs.remove(x)
print("  본 것   :", seen)
print("  남은 것 :", xs, " <- c 를 못 지웠다")

print()
print("--- 왜 그런가: 리스트 이터레이터는 정수 커서다 ---")
ys = ["a", "b", "c", "d", "e"]
it = iter(ys)
print("  next ->", next(it), "| 남은 개수 힌트 :", it.__length_hint__())
print("  next ->", next(it), "| 남은 개수 힌트 :", it.__length_hint__())
ys.remove("b")
print("  'b' 를 지웠다 -> ys =", ys, "| 남은 개수 힌트 :", it.__length_hint__())
print("  next ->", next(it), " <- 'c' 가 아니라")

print()
print("--- 순회 중 append 는 안 끝난다 (3개만 보고 끊는다) ---")
zs = [1]
out = []
for v in zs:
    out.append(v)
    zs.append(v + 1)
    if len(out) == 5:
        break
print("  본 것 :", out, "| 리스트 길이 :", len(zs))

print()
print("--- dict/set 은 터진다 ---")
d = {"a": 1, "b": 2}
try:
    for k in d:
        d[k + "!"] = 0
except RuntimeError as e:
    print("  dict :", type(e).__name__ + ":", e)
s = {"a", "b"}
try:
    for v in s:
        s.add(v + "!")
except RuntimeError as e:
    print("  set  :", type(e).__name__ + ":", e)
d2 = {"a": 1, "b": 2}
d2["a"] = 99
print("  값만 바꾸는 것은 된다 :", d2)
```

```text
--- 순회 중 remove — 예외가 없다 ---
  본 것   : ['a', 'b', 'd', 'e']
  남은 것 : ['a', 'c', 'd', 'e']  <- c 를 못 지웠다

--- 왜 그런가: 리스트 이터레이터는 정수 커서다 ---
  next -> a | 남은 개수 힌트 : 4
  next -> b | 남은 개수 힌트 : 3
  'b' 를 지웠다 -> ys = ['a', 'c', 'd', 'e'] | 남은 개수 힌트 : 2
  next -> d  <- 'c' 가 아니라

--- 순회 중 append 는 안 끝난다 (3개만 보고 끊는다) ---
  본 것 : [1, 2, 3, 4, 5] | 리스트 길이 : 6

--- dict/set 은 터진다 ---
  dict : RuntimeError: dictionary changed size during iteration
  set  : RuntimeError: Set changed size during iteration
  값만 바꾸는 것은 된다 : {'a': 99, 'b': 2}
```

그림 해설 — 네 덩어리가 각각 무엇을 보인다.

- ★★ **첫 덩어리가 이 주제의 조용한 실패다.** `b`·`c` 를 지우라고 했는데 **`c` 가 남았다.**
  `for` 가 `c` 를 **아예 안 봤기** 때문이다(`본 것` 에 `c` 가 없다). **예외도 경고도 없다.**
- ★ **둘째 덩어리가 그 원인을 맨손으로 보인다** — `b` 를 지우자 커서가 가리키던 자리가 **한 칸씩 당겨졌고**,
  다음 `next` 가 `c` 가 아니라 `d` 를 냈다. `__length_hint__` 도 3에서 2로 **한 번에 줄었다.**
- ★ **셋째 덩어리는 반대 방향이다** — 돌면서 붙이면 **끝이 영영 안 온다.** `break` 로 끊어야 출력이 나온다.
- ★★ **넷째 덩어리가 [12번](../12-dict-and-key-requirements/2-summary.md)·[13번](../13-set-and-frozenset/2-summary.md)과의 짝이다** —
  dict·set 은 **크기가 바뀌면 `RuntimeError`** 다. **값만 바꾸는 것은 통과**한다(크기만 보기 때문).

★★ **같은 실수인데 자료형에 따라 「터짐」과 「조용히 틀림」으로 갈린다.**

| 자료형 | 순회 중 크기 변경 | 결과 |
|---|---|---|
| `list` | `remove`·`del`·`append` | ★ **예외 없음.** 건너뛰거나 안 끝난다 |
| `dict` | 키 추가·삭제 | `RuntimeError: dictionary changed size during iteration` |
| `set` | `add`·`remove` | `RuntimeError: Set changed size during iteration`(대문자 `S`) |
| `dict` | **값만** 변경 | 통과한다 |

**고치는 법 셋 — 전부 같은 답을 낸다**

```text
===== 소스: ex.py =====
print("--- 사본을 돌면 ---")
xs = ["a", "b", "c", "d", "e"]
seen = []
for x in list(xs):
    seen.append(x)
    if x in ("b", "c"):
        xs.remove(x)
print("  본 것   :", seen)
print("  남은 것 :", xs)

print("--- 새로 만들면 ---")
ys = ["a", "b", "c", "d", "e"]
ys = [y for y in ys if y not in ("b", "c")]
print("  결과 :", ys)

print("--- 뒤에서부터 인덱스로 돌면 ---")
zs = ["a", "b", "c", "d", "e"]
for i in range(len(zs) - 1, -1, -1):
    if zs[i] in ("b", "c"):
        del zs[i]
print("  결과 :", zs)
```

```text
--- 사본을 돌면 ---
  본 것   : ['a', 'b', 'c', 'd', 'e']
  남은 것 : ['a', 'd', 'e']
--- 새로 만들면 ---
  결과 : ['a', 'd', 'e']
--- 뒤에서부터 인덱스로 돌면 ---
  결과 : ['a', 'd', 'e']
```

- ★ **사본을 돌면 `본 것` 에 다섯 개가 다 있다.** 그것이 고쳐졌다는 증거다.
- **새로 만드는 쪽**([14번](../14-comprehensions/2-summary.md))이 가장 읽기 쉽고 실무 기본값이다.
- **뒤에서부터**는 사본을 안 만들어 메모리를 아끼지만 **읽기 어렵다.** 아주 큰 리스트에서만.

**비용** — 사본 쪽은 원소 수만큼 메모리를 더 쓴다.\
대신 **이 버그는 테스트가 잘 못 잡는다** — 연속해서 지울 것이 없으면 증상이 안 나기 때문이다.

### 4. `enumerate` — 세는 수만 바꾼다

**언제 쓰나** — 번호를 붙여 돌 때. `range(len(xs))` 를 쓰고 있을 때.

```text
===== 소스: ex.py =====
import sys, itertools
print("python", ".".join(map(str, sys.version_info[:3])))

print("--- enumerate ---")
print("  기본      :", list(enumerate("abc")))
print("  start=1   :", list(enumerate("abc", start=1)))
print("  세는 수만 바뀐다 :", list(enumerate(["x", "y"], 1)))
e = enumerate("ab")
print("  iter(e) is e :", iter(e) is e, " <- 이터레이터다")

print()
print("--- zip 은 짧은 쪽에서 끊는다 ---")
print("  zip        :", list(zip([1, 2, 3], "ab")))
print("  zip_longest:", list(itertools.zip_longest([1, 2, 3], "ab", fillvalue="-")))

print()
print("--- range 는 이터레이터가 아니라 시퀀스다 ---")
r = range(5)
print("  iter(r) is r :", iter(r) is r)
print("  두 번 돌아도 :", list(r), list(r))
print("  len          :", len(r), "| r[2] :", r[2], "| r[-1] :", r[-1], "| r[1:3] :", r[1:3])
print("  4999999 in range(10_000_000) :", 4_999_999 in range(10_000_000))
print("  getsizeof(range(10_000_000)) :", sys.getsizeof(range(10_000_000)))
print("  == 는 값 비교 :", range(0, 5) == range(0, 5, 1), "|", range(0) == range(5, 0))
print("  타입들       :", type(r).__name__, "/", type(iter(r)).__name__)
```

```text
python 3.12.3
--- enumerate ---
  기본      : [(0, 'a'), (1, 'b'), (2, 'c')]
  start=1   : [(1, 'a'), (2, 'b'), (3, 'c')]
  세는 수만 바뀐다 : [(1, 'x'), (2, 'y')]
  iter(e) is e : True  <- 이터레이터다

--- zip 은 짧은 쪽에서 끊는다 ---
  zip        : [(1, 'a'), (2, 'b')]
  zip_longest: [(1, 'a'), (2, 'b'), (3, '-')]

--- range 는 이터레이터가 아니라 시퀀스다 ---
  iter(r) is r : False
  두 번 돌아도 : [0, 1, 2, 3, 4] [0, 1, 2, 3, 4]
  len          : 5 | r[2] : 2 | r[-1] : 4 | r[1:3] : range(1, 3)
  4999999 in range(10_000_000) : True
  getsizeof(range(10_000_000)) : 48
  == 는 값 비교 : True | True
  타입들       : range / range_iterator
```

그림 해설 — 세 덩어리가 각각 무엇을 말한다.

- ★ **`start=1` 은 「세는 수」만 바꾼다.** 원소를 건너뛰지 않는다 — `['x','y']` 가 `(1,'x')`·`(2,'y')` 로 온전히 나왔다.
  **인덱스가 아니라 번호**다. `xs[i]` 로 다시 접근하려고 `start=1` 을 쓰면 **한 칸 어긋난다.**
- ★ **`enumerate` 는 이터레이터다**(`iter(e) is e` 가 참). **두 번 못 돈다**([16번](../16-iterator-protocol/2-summary.md)).
- **`zip` 은 짧은 쪽에서 끊는다** — `3` 이 결과에 없다. 다음 절이 그 `3` 이 **어디로 갔는지** 보인다.
- ★★ **`range` 는 이터레이터가 아니다** — `iter(r) is r` 이 `False` 라 **두 번 돌아도 둘 다 나온다.**
  `len`·인덱싱·음수 인덱스·슬라이스가 전부 된다. **`range` 는 「지연된 시퀀스」이지 「제너레이터」가 아니다.**
- **`getsizeof(range(10_000_000))` 이 `48`** 이다 — 시작·끝·걸음 세 수만 들고 있다.
- **`==` 가 값 비교다** — `range(0)` 과 `range(5, 0)` 이 둘 다 **빈 range** 라 같다고 나왔다.

**비용** — `enumerate` 는 인덱스 계산을 없앤다.\
대신 **이터레이터라 두 번 못 돈다.** `range` 는 반대다 — **몇 번이든 돌고 메모리가 상수**다.

### 5. ★ `zip` 이 삼킨 원소 — 그리고 `strict=True`

**언제 쓰나** — 길이가 다를 수 있는 두 목록을 묶을 때. 이 절이 「조용히 데이터가 준다」의 정본이다.

```text
   zip(left, "ab")    left = 1, 2, 3, 4  (이터레이터)

   1회: left 에서 1, "ab" 에서 'a'  -> (1, 'a')
   2회: left 에서 2, "ab" 에서 'b'  -> (2, 'b')
   3회: left 에서 3  ★ 꺼냈다!  그다음 "ab" 가 끝  -> 멈춘다
        ^^^^^^^^^^^  3 은 결과에도 없고 left 에도 없다
```

```text
===== 소스: ex.py =====
print("--- zip 이 삼킨 원소 ---")
left = iter([1, 2, 3, 4])
print("  zip 결과      :", list(zip(left, "ab")))
print("  왼쪽에 남은 것 :", list(left), " <- 3 이 사라졌다")
```

```text
--- zip 이 삼킨 원소 ---
  zip 결과      : [(1, 'a'), (2, 'b')]
  왼쪽에 남은 것 : [4]  <- 3 이 사라졌다
```

★★ **`3` 이 증발했다.** 결과 튜플에도 없고 남은 이터레이터에도 없다.
`zip` 이 **왼쪽부터 꺼내 보고** 오른쪽이 끝난 것을 알았을 때, **이미 꺼낸 왼쪽 값은 되돌릴 수 없기** 때문이다.\
★ 문서가 잘라 내는 것 자체는 적는다 — *"By default, `zip()` stops when the shortest iterable is exhausted.
It will **ignore the remaining items in the longer iterables**, cutting off the result to the length of the shortest iterable"* ·
*"The **left-to-right evaluation order** of the iterables is guaranteed."*
★★ **그런데 「꺼내 놓고 버린다」는 것은 문서 문장으로는 안 나온다** — 위 실행이 그것을 보인 것이다.
「무시한다(ignore)」는 낱말은 **안 읽는다**로도 읽히는데, 실제로는 **읽고 버린다.**

**★ `strict=True`(3.10+)는 그것을 예외로 바꾼다**

```text
===== 소스: ex.py =====
print(list(zip([1, 2, 3], "ab", strict=True)))
```

```text
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
ValueError: zip() argument 2 is shorter than argument 1
```

반대 방향도 문구가 다르다.

```text
===== 소스: ex.py =====
print(list(zip("ab", [1, 2, 3], strict=True)))
```

```text
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
ValueError: zip() argument 2 is longer than argument 1
```

- ★ **`shorter` 와 `longer` 로 문구가 갈린다.** 어느 쪽이 길었는지까지 알려 준다 —
  **몇 번째 인자**인지도 번호로 말한다.
- ★ **3.11.15 에서도 같은 문구**가 나왔다(대조 확인). 그래도 **문구는 보장이 아니다** — 종류(`ValueError`)만 명세다.
- 세 갈래를 골라 쓴다.

| 상황 | 쓰는 것 |
|---|---|
| 길이가 같아야 **맞는** 데이터다 | ★ **`strict=True`** — 다르면 터진다 |
| 짧은 쪽에 맞추는 것이 **의도**다 | 기본 `zip` |
| 긴 쪽에 맞추고 빈 칸을 채운다 | `itertools.zip_longest(fillvalue=...)` |

★★ **기본값이 「조용히 자르기」인 것이 이 함수의 위험이다.** 3.10 이전에는 `strict` 가 아예 없었다.

**비용** — `strict=True` 는 길이 검사 때문에 **끝까지 한 칸 더** 본다. 무시할 만하다.\
대신 **이터레이터를 넘기면 예외가 나도 이미 소비된 것은 못 되돌린다.**

### 6. `range` 가 시퀀스인 것 — 재 본 것

★ 아래는 **이 머신에서 실제로 잰 값**이다(측정 조건은 머리말에 있다). **절댓값이 아니라 기울기를 읽는다.**

```text
===== 소스: ex.py =====
import statistics, timeit
def med(stmt, setup, n, r=11):
    return statistics.median(timeit.repeat(stmt, setup=setup, number=n, repeat=r)) / n * 1e9
for size in (1_000, 1_000_000, 1_000_000_000):
    t = med(f"{size-1} in r", f"r = range({size})", 20000)
    print(f"  range({size:>13})  마지막 원소 in  {t:7.1f} ns")
```

세 판을 돌린 결과다. ★ **다시 돌리면 또 달라진다** — 대조할 것은 숫자가 아니라 아래에 적은 성질이다.
(`--- 판 N ---` 줄은 세 판을 가르려고 붙인 것이고 스크립트가 찍는 것이 아니다.)

```text
--- 판 1 ---
  range(         1000)  마지막 원소 in     45.1 ns
  range(      1000000)  마지막 원소 in     41.4 ns
  range(   1000000000)  마지막 원소 in     41.5 ns
--- 판 2 ---
  range(         1000)  마지막 원소 in     40.2 ns
  range(      1000000)  마지막 원소 in     40.0 ns
  range(   1000000000)  마지막 원소 in     39.1 ns
--- 판 3 ---
  range(         1000)  마지막 원소 in     41.7 ns
  range(      1000000)  마지막 원소 in     40.1 ns
  range(   1000000000)  마지막 원소 in     39.6 ns
```

★ **재현되는 것은 절댓값이 아니라 이것이다** — **크기를 100만 배로 늘려도 시간이 안 변한다.**
판 안에서의 흔들림(39\~45 ns)이 크기에 따른 변화보다 크다.\
★ 이것이 가능한 이유는 **`range` 가 값을 안 들고 「수식」만 들고 있기 때문**이다 —
`in` 을 산술로 판정한다(`getsizeof` 가 `48` 인 것과 같은 사실의 두 얼굴).\
★★ **단 정수일 때만이다** — `"x" in range(10)` 처럼 정수가 아니면 **처음부터 끝까지 훑는다.** 그때는 상수가 아니다.

**비용** — `range` 는 크기와 무관하게 48바이트이고 `in` 도 상수 시간이다.\
대신 **정수가 아닌 것을 찾으면 선형**이 된다.

## 문법 — 형태와 규칙

```python
for 타깃 in 이터러블:
    ...
    continue          # 이번 회차만 건너뛴다 — else 를 안 건드린다
    break             # 루프를 나간다 — ★ else 를 건너뛴다
else:
    ...               # break 없이 끝났을 때만

while 조건:
    ...
else:
    ...               # 조건이 거짓이 되어 끝났을 때만

enumerate(it, start=0)          # (번호, 값) — ★ 번호이지 인덱스가 아니다
zip(a, b)                       # 짧은 쪽에서 끊는다
zip(a, b, strict=True)          # 3.10+ — 길이가 다르면 ValueError
itertools.zip_longest(a, b, fillvalue=None)
range(stop) · range(start, stop[, step])   # ★ 시퀀스다. 여러 번 돈다
```

규칙 여섯.

1. **`else` 는 `break` 가 없을 때만** 돈다. 한 번도 안 돌았어도 돈다.
2. **`continue` 는 `else` 를 안 건드린다.** 루프를 나간 것이 아니다.
3. **순회 중에 컨테이너의 크기를 바꾸지 않는다.** 리스트는 조용히 틀리고 dict·set 은 `RuntimeError` 다.
4. **`enumerate` 의 `start` 는 번호이지 인덱스가 아니다.** `xs[i]` 로 되돌아가면 어긋난다.
5. **`zip` 의 기본은 조용히 자르기**다. 길이를 검사해야 하면 `strict=True`(3.10+).
6. **`range` 는 이터레이터가 아니다.** `enumerate`·`zip`·`map` 과 한 묶음으로 외우면 틀린다.

**금지 사례 — 에러가 나는 자리, 그리고 에러가 안 나는 자리**

```python
for k in d: d[k] = 0; d["새"] = 1    # RuntimeError — dict 크기 변경
for v in s: s.add(v + "!")           # RuntimeError — set 크기 변경
zip([1,2,3], "ab", strict=True)      # ValueError — 길이 다름
break                                # SyntaxError — 루프 밖
for x in xs: xs.remove(x)            # ★ 에러가 안 난다. 결과만 틀린다
```

```text
===== 소스: ex.py =====
if True:
    break
```

```text
  File "<stdin>", line 2
SyntaxError: 'break' outside loop
```

`continue` 도 같은 층이고 문구만 다르다.

```text
===== 소스: ex.py =====
continue
```

```text
  File "<stdin>", line 1
SyntaxError: 'continue' not properly in loop
```

★ **이 두 `SyntaxError` 에는 소스 줄도 캐럿도 안 나온다.** 같은 `SyntaxError` 인데
[19번](../19-function-argument-rules/2-summary.md)의 `def f(a=1, b)` 류는 줄과 캐럿이 나온다 —
**파서가 잡는 것과 그다음 단계가 잡는 것이 다르기 때문**이다(그 갈림의 정본도 19번이다).

★ **이것만 `SyntaxError` 다** — 정의(컴파일) 시점이라 **그 줄이 안 도는 자리에 있어도 프로그램이 시작조차 안 한다.**
나머지는 전부 실행 시점이다. 그 층 구분의 정본은 [19번](../19-function-argument-rules/2-summary.md)이다.

## 어디서 틀리나

### (1) `else` 를 「아니면」으로 읽는다

**조건이 없다.** `break` 가 안 일어나면 도는 자리다. **빈 이터러블에서도 돈다.**

### (2) `continue` 가 `else` 를 막는다고 믿는다

**안 막는다.** `break` 만 막는다.

### (3) 순회하면서 리스트를 지운다

★ **예외가 안 난다.** 연속된 원소를 지우면 **하나 걸러 남는다.**\
고치는 법: `for x in list(xs)` · 컴프리헨션으로 새로 만들기 · 뒤에서부터 인덱스.

### (4) dict·set 도 리스트처럼 조용할 것이라 믿는다

**터진다.** `RuntimeError: dictionary changed size during iteration` / `Set changed size during iteration`.\
★ **dict 의 값만 바꾸는 것은 통과**한다 — 크기만 보기 때문이다.

### (5) `enumerate(xs, 1)` 의 번호로 `xs[i]` 를 한다

**한 칸 어긋난다.** `start` 는 번호이지 인덱스가 아니다.

### (6) `enumerate`·`zip` 을 두 번 돈다

**이터레이터다.** 두 번째가 빈다([16번](../16-iterator-protocol/2-summary.md)).

### (7) `zip` 이 길이를 검사할 것이라 믿는다

**조용히 자른다.** 게다가 **긴 쪽의 원소 하나가 삼켜진다** — 결과에도 없고 원본 이터레이터에도 없다.\
고치는 법: `strict=True`(3.10+) 또는 `zip_longest`.

### (8) `range` 를 제너레이터로 안다

**시퀀스다.** 두 번 돌고, `len`·인덱싱·슬라이스가 된다. `iter(r) is r` 이 `False`.

### (9) `range` 의 `in` 이 언제나 상수라고 믿는다

**정수일 때만**이다. 정수가 아니면 처음부터 끝까지 훑는다.

### (10) `for i in range(len(xs))` 로 인덱스를 돌린다

값이 필요하면 `for x in xs`, 번호도 필요하면 `enumerate`.\
★ **인덱스가 진짜 필요한 자리는 「순회 중 삭제를 뒤에서부터」 정도**다.

## 구현 세부사항 대 언어 보장

세 층으로 가른다. ★ **이 주제는 「언어 보장」이 두껍다** — `else` 의 의미도, 순회 중 변경의 위험도 문서에 있다.\
구현 쪽에 남는 것은 **그것이 어떤 명령으로 실현되나**와 **예외 문구**다.

| 층 | 무엇인가 | 어떻게 확인했나 |
|---|---|---|
| **언어 보장** | 언어·라이브러리 레퍼런스가 정한 것 | 공식 문서 문장을 열어서 인용 |
| **CPython 구현** | 이 구현이 그렇게 하는 것 | `dis` · 실행 |
| **이 판·이 머신의 관찰** | 3.12.3·이 머신에서 그랬을 뿐 | 예외 문구 · 시간 수치 |

### 언어 보장

| 사실 | 근거 |
|---|---|
| `for` 의 `else` 는 **이터레이터가 소진되면** 실행된다 | 8.3 — *"When the iterator is exhausted, the suite in the `else` clause, if present, is executed, and the loop terminates."* |
| `while` 의 `else` 는 **조건이 거짓이 되어 끝났을 때** 실행된다 | 8.2 |
| **`break` 는 `else` 절을 실행하지 않고 루프를 끝낸다** | 8.3 — *"A `break` statement executed in the first suite terminates the loop **without executing the `else` clause's suite**."* |
| 순회 중 컬렉션 변경은 **까다롭다** — 사본을 돌거나 새로 만들라 | 튜토리얼 4장 — *"Code that modifies a collection while iterating over that same collection can be tricky to get right."* ★ **권고이지 금지가 아니다** |
| `enumerate(it, start)` 는 **`start` 부터 세는 수**와 값을 쌍으로 낸다 | `enumerate` |
| `zip` 은 **가장 짧은 입력이 소진되면 멈추고 긴 쪽의 나머지를 무시한다** · 평가 순서는 **왼쪽에서 오른쪽**이 보장된다 | `zip` — *"stops when the shortest iterable is exhausted ... ignore the remaining items"* · *"The left-to-right evaluation order of the iterables is guaranteed."* |
| `zip(..., strict=True)` 는 길이가 다르면 **`ValueError`**(3.10+) | `zip` · PEP 618 |
| `range` 는 **`collections.abc.Sequence` ABC 를 구현**한다 — 포함 검사·인덱스·슬라이스·음수 인덱스 | Ranges — *"Range objects implement the `collections.abc.Sequence` ABC"* |
| `range` 는 **크기와 무관하게 같은 (작은) 메모리**를 쓴다 — `start`·`stop`·`step` 만 저장한다 | Ranges — *"will always take the same (small) amount of memory, no matter the size of the range"* |
| `range` 의 `in` 은 **`int` 에 대해 상수 시간**이다 | Ranges(3.2 변경) — *"Test `int` objects for membership in **constant time** instead of iterating through all items."* |
| `range` 의 `==` 는 **시퀀스로** 비교한다 — `start`·`stop`·`step` 이 달라도 같을 수 있다 | Ranges — *"two range objects are considered equal if they represent the same sequence of values"* |

### CPython 구현 세부사항

| 사실 | 어떻게 확인했나 |
|---|---|
| `else` 가 **`END_FOR` 바로 뒤에** 놓이고 `break` 는 **다른 오프셋으로** 뛴다 | `dis` |
| **루프 뒤 코드가 복제**된다(`after = 1` 이 두 번) | `dis` |
| 명령 이름 `FOR_ITER`·`END_FOR`·`POP_JUMP_IF_TRUE`·`RETURN_CONST` | `dis` — 판마다 바뀐다 |
| 리스트 이터레이터가 **정수 커서**로 구현된 것 | 실행 — 지운 뒤 `next` 가 한 칸 건너뛴다 |
| `__length_hint__` 가 커서 기준으로 줄어드는 것 | 실행 |
| dict·set 의 변경 검사가 **크기만** 본다 | 실행 — 값만 바꾸면 통과([12번](../12-dict-and-key-requirements/2-summary.md)) |
| `getsizeof(range(10_000_000))` 이 `48` | 실행 — 빌드·비트 폭에 달렸다 |
| 예외 **문구** 전부 | 실행 |

### 이 판(3.12.3)·이 머신의 관찰

| 관찰 | 어디가 흔들리나 |
|---|---|
| 바이트코드 오프셋·명령 이름 | **판마다 다르다.** 3.11 에는 `PRECALL` 류가 더 있다 |
| `RuntimeError` 문구 — dict 는 소문자 `dictionary`, set 은 대문자 `Set` | 종류는 명세, 문구는 아니다 |
| `ValueError: zip() argument 2 is shorter than argument 1` | 3.11.15 에서도 같았다 — **그래도 보장이 아니다** |
| `range` 의 `in` 시간 39\~45 ns | 머신·부하. **「크기에 안 변한다」는 성질만** 재현된다 |
| `getsizeof(range(...))` 이 `48` | 구현 값 |
| `순회 중 remove` 에서 남은 것이 `['a','c','d','e']` | **결정적이다** — 커서 규칙의 결과라 매번 같다 |

### 그래서 이렇게 적으면 틀린다

- ✗ 「`else` 는 루프가 한 번도 안 돌았을 때 돈다」\
  ○ **`break` 가 없었을 때** 돈다. 빈 것도 세 번 돈 것도 똑같이 `else` 로 간다.
- ✗ 「`continue` 도 `else` 를 건너뛴다」 → **안 건너뛴다.**
- ✗ 「순회 중에 지우면 에러가 난다」\
  ○ **리스트는 에러가 안 난다.** dict·set 만 터진다.
- ✗ 「dict 는 순회 중에 아무것도 못 바꾼다」 → **값은 바꿀 수 있다.** 크기만 본다.
- ✗ 「`zip` 은 짧은 쪽까지만 읽는다」\
  ○ **긴 쪽에서 한 개를 더 꺼내 버린다.** 그 원소는 어디에도 안 남는다.
- ✗ 「`range` 는 제너레이터다」\
  ○ **시퀀스**다. 두 번 돌고 인덱싱·슬라이스가 된다.
- ✗ 「`range` 의 `in` 은 언제나 O(1)」 → **정수일 때만**이다.
- ✗ 「`dis` 로 봤으니 어느 파이썬에서나 그렇다」\
  ○ **`dis` 는 CPython 구현**이다. `else` 의 **의미**는 명세지만 **배치**는 아니다.

**판정 기준 한 줄**: **`else` 를 물으면 「`break` 가 있었나」를 보고, 순회 중 변경을 물으면 「터지나 조용하나」부터 갈라라.**

## 언제 쓰고 언제 안 쓰나

| 상황 | 판정 |
|---|---|
| 「찾으면 쓰고 끝까지 못 찾으면 따로 처리」 | **`for ... else`** — 플래그 변수가 사라진다 |
| 재시도 N 번, 다 실패하면 따로 처리 | **`while ... else`** 또는 `for ... else` |
| 팀 코드이고 읽는 사람이 많다 | ★ **플래그 변수** — `else` 는 오독률이 높다 |
| 조건에 맞는 것만 남긴다 | **컴프리헨션으로 새로 만든다** — 순회 중 삭제를 안 한다 |
| 아주 큰 리스트에서 제자리로 지운다 | **뒤에서부터 인덱스** — 사본을 안 만든다 |
| 번호를 붙여 돈다 | **`enumerate`** — `range(len(xs))` 를 안 쓴다 |
| 길이가 같아야 맞는 두 목록 | ★ **`zip(..., strict=True)`**(3.10+) |
| 길이가 달라도 되는 두 목록 | 기본 `zip` 또는 `zip_longest` |
| 큰 수 범위를 돌거나 멤버십만 본다 | **`range`** — 48바이트에 정수 `in` 이 상수 시간 |
| 같은 번호 묶음을 **두 번** 돈다 | **`range`** (이터레이터가 아니다) — `enumerate`·`zip` 은 안 된다 |

## 핵심 문장

- **`else` 는 「아니면」이 아니라 「`break` 를 안 만났으면」이다.** 조건이 없고, 빈 이터러블에서도 돈다.
- **바이트코드에서 `else` 는 `END_FOR` 바로 뒤에 놓인다** — 검사하는 명령이 하나도 없고, `break` 는 그 자리를 **아예 지나쳐** 다른 오프셋으로 뛴다. 컴파일러가 **루프 뒤 코드를 복제**한다. ★ 이것은 CPython 구현이지 보장이 아니다.
- **`continue` 는 `else` 를 안 건드린다.**
- ★★ **순회 중 리스트 변경은 예외가 없다** — 커서가 정수라서 **한 칸 건너뛴다.** dict·set 은 **크기만 보고 `RuntimeError`** 를 던진다.
- **`enumerate` 의 `start` 는 번호이지 인덱스가 아니다.** 그리고 `enumerate` 는 **이터레이터**라 두 번 못 돈다.
- ★ **`zip` 은 긴 쪽에서 한 개를 삼킨다** — 결과에도 없고 원본 이터레이터에도 안 남는다. `strict=True`(3.10+)가 그것을 `ValueError` 로 바꾼다.
- ★ **`range` 는 이터레이터가 아니라 시퀀스다** — `iter(r) is r` 이 `False` 라 두 번 돌고, 크기와 무관하게 48바이트이며, **정수** `in` 이 상수 시간이다.

## 관련 자료

- 목록: [python/syntax 주제 목록](../README.md) — 이 주제는 **18번**
- 선행: [16-iterator-protocol](../16-iterator-protocol/2-summary.md) — **`for` 가 안에서 무엇을 부르나의 정본.**\
  **경계**: 그쪽은 `iter`·`next`·`StopIteration` 계약까지, 여기는 **그 위에 얹힌 흐름 제어**부터다.
- 선행: [09-sequence-ops-and-slicing](../09-sequence-ops-and-slicing/2-summary.md) — `range` 가 시퀀스라는 말의 뜻. 슬라이스가 왜 되나.
- 짝: [12-dict-and-key-requirements](../12-dict-and-key-requirements/2-summary.md)·[13-set-and-frozenset](../13-set-and-frozenset/2-summary.md) — **순회 중 변경이 터지는 쪽.**\
  **경계**: 그쪽은 해시·키 요건까지, 여기는 **「리스트만 조용하다」는 대조**부터다.
- 함께 보는 곳: [14-comprehensions](../14-comprehensions/2-summary.md) — 순회 중 삭제를 안 하는 정석.
- 함께 보는 곳: [15-generator-expressions-lazy-eval](../15-generator-expressions-lazy-eval/2-summary.md) — `range` 와 제너레이터가 어떻게 다른가.
- 함께 보는 곳: [17-generators-yield](../17-generators-yield/2-summary.md) — `for` 가 제너레이터를 소비하는 쪽.
- 함께 보는 곳: [19-function-argument-rules](../19-function-argument-rules/2-summary.md) — `SyntaxError`(정의 시점)와 실행 시점 오류를 가르는 층의 정본.
- 이어지는 곳: 목록의 **44번 주제** 「`itertools`」 — `zip_longest`·`islice`·`groupby` 의 정본.
- 이어지는 곳: 목록의 **39번 주제** 「`match` 문」 — 또 하나의 흐름 제어.
- 기존 노트: [`cs/foundations/python-basics/`](../../../../python-basics/) — `for`·`while` 을 「이렇게 쓴다」까지가 그쪽이다.\
  **경계**: 여기는 「**`else` 가 언제 돌고 순회 중 변경이 무엇을 망가뜨리나**」부터다.
- 공식 문서: [`for` 문](https://docs.python.org/3.12/reference/compound_stmts.html#the-for-statement) · [`zip`](https://docs.python.org/3.12/library/functions.html#zip) · [Ranges](https://docs.python.org/3.12/library/stdtypes.html#ranges) · [PEP 618](https://peps.python.org/pep-0618/)

## 용어 풀이

- **`break`**: 루프를 즉시 나가는 문. **`else` 를 건너뛴다.**
- **`continue`**: 이번 회차만 건너뛰고 다음으로 가는 문. **`else` 를 안 건드린다.**
- **루프의 `else`**: `break` 없이 끝났을 때 도는 절. 「아니면」이 아니라 「**끝까지 갔으면**」이다.\
  예: `nobreak` 라고 읽으면 안 틀린다.
- **순회 중 변경(mutation during iteration)**: 루프가 도는 동안 그 컨테이너의 크기를 바꾸는 것.\
  예: 리스트는 **조용히 건너뛰고** dict·set 은 `RuntimeError` 다.
- **커서(cursor)**: 리스트 이터레이터가 들고 있는 **정수 위치**. 원본이 짧아지면 가리키는 원소가 바뀐다.
- **`enumerate(it, start)`**: `(번호, 값)` 쌍을 내는 이터레이터. **번호이지 인덱스가 아니다.**
- **`zip`**: 여러 이터러블을 묶는 이터레이터. **짧은 쪽에서 끊고**, 긴 쪽에서 **한 개를 더 꺼내 버린다.**
- **`strict=True`**: 3.10+ `zip` 의 옵션. 길이가 다르면 `ValueError`.\
  예: 문구가 `shorter`/`longer` 로 갈려 어느 쪽이 길었는지 알려 준다.
- **`range`**: 시작·끝·걸음 세 수만 들고 있는 **불변 시퀀스**. 이터레이터가 아니다.\
  예: 크기와 무관하게 48바이트이고 **정수** `in` 이 상수 시간이다.
- **바이트코드(bytecode)**: 파이썬 소스를 컴파일한 중간 명령. `dis` 로 본다.\
  ★ **CPython 의 구현이지 언어 보장이 아니다.**

## 더 들어가면

- **`for ... else` 를 쓰지 말자는 주장**도 오래됐다 — 언어 설계자 본인이 이름 선택을 후회한다고 밝힌 적이 있다.
  **읽는 사람이 `if`/`else` 로 오독하는 비율**이 높기 때문이다. 팀 코드에서는 플래그 변수나 함수 분리(`return` 으로 탈출)가 더 안전하다.
- **`try`/`finally` 안의 `break`** 는 `finally` 를 반드시 돌린 뒤에 나간다(목록의 **25번 주제**).
- **`itertools.zip_longest`** 의 `fillvalue` 는 **하나**뿐이다 — 이터러블마다 다른 채움값을 주려면 직접 짜야 한다(목록의 **44번 주제**).
- **`enumerate` 의 `start` 에 음수·큰 수**도 들어간다 — 세는 수일 뿐이라 제약이 없다.
- **비동기 판**은 `async for` 이고 `else` 도 붙는다(목록의 **51번 주제**).
- **순회 중 변경을 언어가 아예 막는 것이 옳은가**는 설계 논쟁이다 — dict·set 은 **해시 테이블 재배치**로 메모리 안전이 깨질 수 있어 막고,
  리스트는 인덱스 접근이라 **안전하긴 해서** 안 막는다. **「안전하다」와 「옳다」가 다른 자리**다.
