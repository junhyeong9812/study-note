# python/syntax/15-generator-expressions-lazy-eval — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **이 본문은 원고가 아니라 Claude 작성이다**(문법·API 갈래는 원고 없이 공식 문서로 접지한다).
>
> **기준 소스** — 열어서 확인한 것만.
> - [6.2.8. Generator expressions](https://docs.python.org/3.12/reference/expressions.html#generator-expressions) — 괄호 규칙 · **즉시 평가되는 부분**
> - [6.2.4. Displays for lists, sets and dictionaries](https://docs.python.org/3.12/reference/expressions.html#displays-for-lists-sets-and-dictionaries) — 감춰진 스코프
> - [`sys.getsizeof`](https://docs.python.org/3.12/library/sys.html#sys.getsizeof) — **무엇을 세고 무엇을 안 세나**
> - [`tracemalloc`](https://docs.python.org/3.12/library/tracemalloc.html) · [`get_traced_memory`](https://docs.python.org/3.12/library/tracemalloc.html#tracemalloc.get_traced_memory) — 실제로 잡힌 바이트
> - [`itertools.islice`](https://docs.python.org/3.12/library/itertools.html#itertools.islice)
>
> **실행 검증** — 이 문서에 실린 출력은 전부 `python3` **3.12.3**(Linux, x86_64)에서 실제로 돌려 나온 것이다. 지어낸 출력은 없다.\
> ★ **던지는 형태를 하나로 고정했다** — 이 갈래는 `python3 - <파일` 로 던져 트레이스백이 `File "<stdin>", line N` 이 되게 했다.
> 그래서 **실행 중 예외에는 소스 줄과 캐럿이 안 나온다.** 반대로 **`SyntaxError` 에는 나온다**(컴파일러가 아직 소스를 들고 있어서다 — 그대로 실었다).\
> **수치** — 메모리는 `sys.getsizeof` 와 `tracemalloc.get_traced_memory()` 두 창으로 쟀고, 시간은 `timeit` **중앙값을 세 판** 냈다.
> 머신은 Linux x86_64. **대조할 것은 숫자가 아니라 「원소 수를 늘려도 한쪽만 안 변한다」는 성질이다.**\
> **버전** — 제너레이터 표현식 자체는 **2.4+** 이고 이 노트가 다루는 범위(3.10\~3.13)에서 문법이 안 바뀌었다.
> 갈리는 것은 **바이트코드**다 — 리스트 컴프리헨션이 **3.12 부터 인라인**되고(PEP 709) 제너레이터 표현식은 **안 된다.** 3.11.15 로 대조했다.\
> **★ 흔들리는 칸 / 안 흔들리는 칸** — 재대조에서 「고칠 것」과 「설계상 안 맞는 것」을 기계적으로 가르려고 미리 선언한다.
>
> | 흔들린다(다시 돌리면 값이 달라진다) | 안 흔들린다(근거로 써도 되는 칸) |
> |---|---|
> | `getsizeof`·`tracemalloc` 의 **절댓값** · 배수 `42243` | **대소 관계와 자릿수** · 「`N` 에 비례하나 안 하나」 |
> | `timeit` 의 마이크로초와 비 | 「앞 1개만」 쪽의 **100배 자릿수** |
> | 코드 객체 주소 `0x740a5cf4eb10` | **코드 객체가 따로 있다/없다** 는 사실 |
> | (판이 오르면) 바이트코드 **명령 이름·오프셋** | 예외 **종류** · `File "<stdin>", line N` · **소진 여부** |
>
> **선행** — [14-comprehensions](../14-comprehensions/2-summary.md)(**괄호 하나 차이의 정본** — 평가 시점·감춰진 스코프) ·
> [09-sequence-ops-and-slicing](../09-sequence-ops-and-slicing/2-summary.md)(리스트가 무엇을 들고 있나).\
> **정본 이웃** — [17-generators-yield](../17-generators-yield/2-summary.md)가 **제너레이터 객체 자체의 정본**이다.
> `yield`·프레임·`send`·`close`·상태 전이는 전부 그쪽이고, 여기는 **「표현식 꼴로 만든 것이 메모리에서 무엇을 하나」** 만 다룬다.

## 한눈에 — 쉽게 말하면

**리스트 컴프리헨션은 장을 다 봐서 냉장고에 채우는 것이고, 제너레이터 표현식은 장보기 목록만 들고 있는 것이다.**

목록은 품목이 백 개든 백만 개든 종이 한 장이다. 냉장고는 아니다.\
그래서 「**지연 평가**」는 말로 증명되지 않는다 — **냉장고를 열어 무게를 재야** 증명된다.

```text
  [x * 2 for x in range(1_000_000)]        (x * 2 for x in range(1_000_000))
  ┌───────────────────────────────┐        ┌──────────────────┐
  │ 0 2 4 6 8 ... 1999998         │        │ 만드는 방법       │
  │ 백만 칸이 실제로 있다           │        │ + 어디까지 갔나   │
  └───────────────────────────────┘        └──────────────────┘
        8,448,728 바이트                            200 바이트
        (원소까지 세면 40 MB)                   (원소 수와 무관)
```

**비유 대응표** — 이 문서는 끝까지 이 대응을 지킨다.

| 비유 | 실체 | 확인하는 법 |
|---|---|---|
| 냉장고를 채운다 | 물질화 | `sys.getsizeof` 가 원소 수에 비례한다 |
| 목록 한 장 | 제너레이터 객체 | `getsizeof` 가 원소 수와 **무관하다** |
| 장을 볼 때 실제로 돈 돈 | `tracemalloc` 최대치 | `get_traced_memory()[1]` |
| 목록을 써 놓기만 하면 아무것도 안 산다 | 지연 평가 | 만드는 줄에서 부작용이 안 찍힌다 |
| **가게 이름만은 지금 정한다** | 첫 `for` 의 iterable 즉시 평가 | 없는 이름을 주면 **만드는 자리**에서 `NameError` |
| 산 것은 다시 못 산다 | 소진 | 두 번째 `sum` 이 `0` |
| 끝없는 진열대에서 다섯 개만 | 무한 수열 + `islice` | 안 멈춘다 |

**똑같은 구조다** — 실무에서 이게 물리는 자리도 굳어 있다.\
「**집계를 두 번 했더니 두 번째가 `0` 이었다**」와 「**메모리가 터져서 제너레이터로 바꿨는데 안 줄었다**」가 그것이다.
뒤엣것은 대개 중간에 `list()` 나 `sorted()` 가 한 번 끼어 있는 경우다.

> **지연 평가(lazy evaluation)** — 값을 미리 다 만들어 두지 않고 요청받을 때 하나씩 만드는 방식.\
> 예: 백만 개를 더하는데 백만 칸을 안 쓰고 한 칸으로 끝낸다.

> **물질화(materialize)** — 지연된 것을 `list()`·`tuple()`·`sorted()` 로 전부 꺼내 실제 자료구조로 만드는 것.\
> 예: 개수를 세거나 두 번 돌려면 필요하고, **그 순간 메모리 이점이 사라진다.**

## 이 주제가 답하려는 질문

1. **「메모리를 아낀다」를 어떻게 증명하나** — 값은 똑같이 나오는데 무엇이 다른가. 무엇으로 재야 속지 않나.
2. **무엇이 늦고 무엇이 안 늦나** — 「전부 지연된다」는 틀렸다. **어느 한 조각만은 지금 평가된다.**
3. **언제 리스트로 물질화해야 하나** — 지연이 공짜가 아닌 자리는 어디인가.

## 동작 방식

> 이 절이 본문이다. 이 주제의 그림은 **메모리 그림**이고, 그 그림을 읽어 주는 것은 **바이트 수**다.

### 1. ★ 괄호 하나 — 증거는 값이 아니라 바이트다

**언제 쓰나** — 큰 입력을 훑을 때. 「리스트로 할까 제너레이터로 할까」를 정할 때.

두 형태는 **값이 같다.** 그래서 값으로는 아무것도 증명되지 않는다.\
★ **재야 하는 것은 「쓰인 바이트」다.** 같은 크기(백만 개)를 양쪽에 똑같이 던졌다.

```text
===== 소스: ex.py =====
import sys
print("python", ".".join(map(str, sys.version_info[:3])), "|", sys.implementation.name)
N = 1_000_000
lc = [x * 2 for x in range(N)]
ge = (x * 2 for x in range(N))
print("list comp  getsizeof :", sys.getsizeof(lc))
print("gen  expr  getsizeof :", sys.getsizeof(ge))
print("배수                 :", sys.getsizeof(lc) // sys.getsizeof(ge))
print("합이 같나            :", sum(lc) == sum(x * 2 for x in range(N)))
```

```text
python 3.12.3 | cpython
list comp  getsizeof : 8448728
gen  expr  getsizeof : 200
배수                 : 42243
합이 같나            : True
```

그림 해설 — 출력의 어느 숫자가 무엇인지.

- **합이 같다.** 두 형태는 **결과가 구분되지 않는다** — 그래서 값만 보면 차이를 영영 못 본다.
- 리스트는 **8,448,728 바이트**. 백만 개 × 포인터 8바이트 + 여유분이다.
- 제너레이터는 **200 바이트**. 백만 개를 「만드는 방법」만 들고 있다.
- ★ **대조할 것은 `42243` 이라는 숫자가 아니라 「`N` 을 10배로 해도 오른쪽만 안 변한다」는 성질이다.**

**그런데 `getsizeof` 는 절반만 말한다 — 두 번째 창이 필요하다**

```text
===== 소스: ex.py =====
import tracemalloc
N = 1_000_000
tracemalloc.start()
total = sum([x * 2 for x in range(N)])
cur, peak = tracemalloc.get_traced_memory()
print(f"[...]  합={total}  현재={cur:>9}  최대={peak:>9} 바이트")
tracemalloc.reset_peak()
total = sum(x * 2 for x in range(N))
cur, peak = tracemalloc.get_traced_memory()
print(f"(...)  합={total}  현재={cur:>9}  최대={peak:>9} 바이트")
tracemalloc.stop()
```

```text
[...]  합=999999000000  현재=       32  최대= 40444616 바이트
(...)  합=999999000000  현재=      182  최대=      646 바이트
```

★★ **최대치가 40 MB 대 646 바이트다.** `getsizeof` 가 말한 8.4 MB 보다 **다섯 배 가까이 크다.**\
리스트 자신은 8.4 MB 지만, 그 안에 든 **정수 객체 백만 개가 따로 잡히기 때문**이다.
`getsizeof` 는 그것을 안 센다(다음 절).

- **`현재`(cur)가 둘 다 거의 0 이다** — `sum` 이 끝나면 리스트가 회수되므로 **끝난 뒤에 재면 차이가 안 보인다.**
  ★ 그래서 **재야 하는 것은 「지금」이 아니라 「최대」다.** OOM 은 최대치에서 난다.
- ★ **대조할 것은 `40444616` 이라는 숫자가 아니라 「왼쪽은 `N` 에 비례하고 오른쪽은 안 변한다」는 성질이다.**
  수치는 인터프리터 판·할당기 상태에 따라 다시 돌리면 달라진다.

> **`tracemalloc`** — 파이썬이 할당한 블록을 추적하는 표준 모듈.\
> 예: `start()` 뒤 `get_traced_memory()` 가 `(현재, 최대)` 두 값을 준다. `reset_peak()` 로 최대치만 다시 센다.

**비용** — 지연 쪽은 메모리가 원소 수와 무관해진다.\
대신 **`tracemalloc` 을 켠 동안은 프로그램이 느려진다** — 측정용이지 상시로 켜 두는 것이 아니다.

### 2. ★ `getsizeof` 가 재는 것과 안 재는 것 — 이 주제의 조용한 함정

**언제 쓰나** — 「제너레이터로 바꿨는데 메모리가 안 줄었다」를 조사할 때.

```text
===== 소스: ex.py =====
import sys
print("getsizeof 는 무엇을 세나")
small = [x for x in range(5)]
print("  [0..4] 리스트 자신 :", sys.getsizeof(small))
print("  원소 5개의 합      :", sum(sys.getsizeof(x) for x in small))
print("  gen expr           :", sys.getsizeof(x for x in range(5)))
print("  gen expr (100만)   :", sys.getsizeof(x for x in range(1_000_000)))
print("  빈 리스트          :", sys.getsizeof([]))
```

```text
getsizeof 는 무엇을 세나
  [0..4] 리스트 자신 : 120
  원소 5개의 합      : 140
  gen expr           : 192
  gen expr (100만)   : 192
  빈 리스트          : 56
```

```text
   sys.getsizeof([0,1,2,3,4])  =  120
   ┌──────────────────────────────────┐
   │ 리스트 머리 56 + 포인터 5칸 × 8 …  │   <- 여기까지만 센다
   └──────────────────────────────────┘
        │   │   │   │   │
        v   v   v   v   v
      [28][28][28][28][28]   <- 정수 객체 5개 = 140 바이트. 안 센다
```

그림 해설.

- **리스트 자신(120)보다 원소들의 합(140)이 더 크다.** 작은 리스트에서도 이미 그렇다.
- ★ **제너레이터는 5개짜리든 100만개짜리든 `192` 로 같다.** 이것이 「원소 수와 무관」의 직접 증거다.
- ★ **그런데 1번 절에서는 `200` 이었다.** 식이 `x` 가 아니라 `x * 2` 라 **평가 스택이 한 칸 더 필요해서**다 —
  **제너레이터 객체의 크기는 「몇 개냐」가 아니라 「식이 얼마나 복잡하냐」에 달렸다.** 둘 다 원소 수와는 무관하다.
- 문서가 `getsizeof` 의 범위를 못 박는다 — *"Only the memory consumption directly attributed to the object is accounted for,
  **not the memory consumption of objects it refers to**."*

★★ **그래서 `getsizeof` 하나로 「메모리를 아꼈다」를 주장하면 안 된다.**
그것은 「**목록 종이의 무게**」이고, 우리가 알고 싶은 것은 「**냉장고 안 물건의 무게**」다. 둘째 창이 `tracemalloc` 이다.

**비용** — `getsizeof` 는 즉시·무료다.\
대신 **참조하는 것을 안 세므로 과소평가한다.** 중첩 컨테이너에서는 몇 배씩 틀린다.

### 3. ★ 전부 늦지는 않는다 — 첫 `for` 의 iterable 만은 지금 평가된다

**언제 쓰나** — 제너레이터를 만들어 놓고 원본을 건드릴 때. 예외가 어느 줄에서 나는지 따질 때.

문서가 그 한 조각을 콕 집는다 — *"the iterable expression in the leftmost `for` clause is **immediately evaluated**,
so that an error produced by it will be emitted at the point where the generator expression is defined."*
규칙의 정본은 [14번](../14-comprehensions/2-summary.md)이고, 여기서는 **「어디까지가 지금이고 어디부터가 나중인가」를 던져서 가른다.**

```text
   ge = (x        for x in 여기        for y in 저기        if 조건)
         ^^                ^^^^^              ^^^^^           ^^^^
         나중              ★ 지금             나중            나중
```

```text
===== 소스: ex.py =====
print("--- 1. 이름을 갈아 끼우면 ---")
src = [1, 2, 3]
g = (n for n in src)
src = [9, 9, 9]
print("  list(g) :", list(g))

print("--- 2. 같은 객체를 고치면 ---")
src2 = [1, 2, 3]
g2 = (n for n in src2)
src2.append(4)
print("  list(g2):", list(g2))

print("--- 3. 첫 for 의 이터러블은 즉시 평가된다 ---")
try:
    g3 = (x for x in nope_first)
except NameError as e:
    print("  만드는 자리에서 NameError:", e)

print("--- 4. 둘째 for 의 이터러블은 늦다 ---")
g4 = (x for outer in [[1, 2]] for x in nope_second)
print("  만들기는 됐다 ->", type(g4).__name__)
try:
    next(g4)
except NameError as e:
    print("  next 할 때 NameError:", e)
```

```text
--- 1. 이름을 갈아 끼우면 ---
  list(g) : [1, 2, 3]
--- 2. 같은 객체를 고치면 ---
  list(g2): [1, 2, 3, 4]
--- 3. 첫 for 의 이터러블은 즉시 평가된다 ---
  만드는 자리에서 NameError: name 'nope_first' is not defined
--- 4. 둘째 for 의 이터러블은 늦다 ---
  만들기는 됐다 -> generator
  next 할 때 NameError: name 'nope_second' is not defined
```

그림 해설 — 네 판이 각각 무엇을 가른다.

- **1번과 2번이 짝이다.** 이름을 갈아 끼우면 **안 따라가고**, 같은 객체를 고치면 **따라간다.**\
  만들 때 잡아 둔 것은 **그때의 객체**이지 **이름**이 아니기 때문이다. 4가 결과에 들어간 것은 그 객체를 나중에 훑었기 때문이다.
- **3번이 「지금」의 증거다** — 아직 아무도 `next` 를 안 했는데 **대입하는 줄에서** 터졌다.
- ★ **4번이 「나중」의 증거다** — 없는 이름이 **둘째 `for`** 에 있으면 제너레이터가 **멀쩡히 만들어지고**,
  `next` 를 부르는 순간에야 터진다. **한 식 안에서 평가 시점이 둘로 갈린다.**

★★ **그래서 「제너레이터 표현식은 아무것도 안 한다」는 틀렸다.** 첫 iterable 하나는 **반드시 지금 평가되고**,
`iter()` 까지 걸린다(바이트코드로 아래 「구현 세부사항」에서 확인한다).

**비용** — 첫 iterable 을 미리 잡아 두므로 **원본이 사라져도 제너레이터는 산다.**\
대신 **그 객체가 나중에 바뀌면 결과가 따라 바뀐다** — 만들고 나서 원본을 고치는 코드는 읽는 사람을 속인다.

### 4. ★ 한 번 돌면 끝이다 — 두 번째는 예외가 아니라 빈 것

**언제 쓰나** — 같은 것을 두 번 집계할 때. 함수에 제너레이터를 넘길 때.

```text
===== 소스: ex.py =====
g = (n for n in range(5))
print("첫 판 sum :", sum(g))
print("둘째 판   :", sum(g))
print("list      :", list(g))
print("max 는?   :", max(g, default="없음"))

lst = [n for n in range(5)]
print("리스트는 몇 번이든 :", sum(lst), sum(lst), list(lst))
```

```text
첫 판 sum : 10
둘째 판   : 0
list      : []
max 는?   : 없음
리스트는 몇 번이든 : 10 10 [0, 1, 2, 3, 4]
```

★★ **둘째 `sum` 이 `0` 이다 — 예외도 경고도 없다.**
`0` 은 **합이 0 인 경우와 글자 하나 다르지 않다.** 로그에도 안 남는다.\
★ **`max` 는 `default=` 를 안 주면 여기서 터진다** — 빈 것에서 최대를 못 구하기 때문이다. 즉 **함수마다 증상이 다르다**:
`sum` 은 `0`, `list` 는 `[]`, `max` 는 `ValueError`. **같은 원인이 세 얼굴로 나온다.**

```text
   리스트                       제너레이터 표현식
   ┌───────────────┐            ┌───────────────┐
   │ 0 1 2 3 4     │  sum -> 10 │ 커서 ──────>  │  sum -> 10
   │ 그대로 있다    │  sum -> 10 │ 커서 끝에 있다 │  sum ->  0
   └───────────────┘            └───────────────┘
                                   되감기가 없다
```

★ 왜 되감기가 없는지(프레임이 어떻게 소진되는지)는 [17번](../17-generators-yield/2-summary.md)이 정본이다.
여기서는 「**표현식 꼴로 만들어도 똑같이 당한다**」는 사실만 확인한다.

**비용** — 한 번 훑고 버릴 것이면 이것이 가장 싸다.\
대신 **두 번 쓸 가능성이 조금이라도 있으면 리스트가 맞다.** 두 번째가 조용히 틀리는 값이 되기 때문이다.

### 5. ★ 끝이 없는 것도 담긴다 — 그래서 `islice` 가 짝이다

**언제 쓰나** — 「조건에 맞는 처음 N 개」를 구할 때. 리스트로는 아예 표현이 안 되는 자리다.

```text
   naturals()  0 1 2 3 4 5 ...  (끝이 없다)
        │
        ▼  (n * n for n in naturals())
   squares     0 1 4 9 16 25 ...
        │
        ▼  (s for s in squares if s % 2 == 1)
   odd         1 9 25 49 81 ...
        │
        ▼  islice(odd, 5)
   결과        [1, 9, 25, 49, 81]      <- 딱 5개만 계산됐다
```

```text
===== 소스: ex.py =====
def naturals():
    n = 0
    while True:
        yield n
        n += 1

import itertools
squares = (n * n for n in naturals())
odd = (s for s in squares if s % 2 == 1)
print("처음 다섯 개 :", list(itertools.islice(odd, 5)))
print("이어서 세 개 :", list(itertools.islice(odd, 3)))
```

```text
처음 다섯 개 : [1, 9, 25, 49, 81]
이어서 세 개 : [121, 169, 225]
```

그림 해설.

- 파이프라인을 **세 겹** 쌓았는데 **어느 단계도 미리 안 돈다.** 각 단계가 한 개씩 끌어온다.
- ★ **둘째 `islice` 가 `[1, 9, 25]` 가 아니라 `[121, 169, 225]` 다** — **이어서** 나온다.
  파이프라인 전체가 **하나의 커서**를 공유하기 때문이다. 4번 절의 소진과 같은 성질이다.
- `list(odd)` 를 쓰면 **영영 안 끝난다.** 지연이 「끝없는 것」을 담을 수 있게 해 준 대신,
  **물질화하는 순간 프로그램이 멈춘다.**

> **`itertools.islice(it, n)`** — 이터러블에서 앞 `n` 개만 잘라 주는 지연 도구.\
> 예: 슬라이스(`xs[:5]`)와 달리 **인덱싱이 없는 것에도** 걸리고, **끝없는 것에도** 걸린다.

**비용** — 필요한 만큼만 계산한다. 앞 5개를 쓰면 5개만 계산된다.\
대신 **`islice` 는 앞에서부터 버리며 센다** — `islice(it, 1000000, 1000005)` 는 백만 개를 실제로 꺼내 버린다. 공짜 건너뛰기가 아니다.

### 6. ★ 지연이 공짜가 아닌 자리 — 무엇을 못 하나

**언제 쓰나** — 제너레이터로 바꾸고 나서 코드가 깨졌을 때.

```text
===== 소스: ex.py =====
g = (n for n in range(5))
try:
    len(g)
except TypeError as e:
    print("len(g)       -> TypeError:", e)
try:
    g[0]
except TypeError as e:
    print("g[0]         -> TypeError:", e)
print("sorted 는 되나 :", sorted(n for n in [3, 1, 2]), " <- 속으로 리스트를 만든다")
g2 = (n for n in range(5))
print("3 in g2      :", 3 in g2, "| 남은 것 :", list(g2), " <- in 이 먹었다")
print("개수를 세려면 :", sum(1 for _ in range(5)), " <- 그 순간 다 돈다")
```

```text
len(g)       -> TypeError: object of type 'generator' has no len()
g[0]         -> TypeError: 'generator' object is not subscriptable
sorted 는 되나 : [1, 2, 3]  <- 속으로 리스트를 만든다
3 in g2      : True | 남은 것 : [4]  <- in 이 먹었다
개수를 세려면 : 5  <- 그 순간 다 돈다
```

- **`len`·인덱싱·슬라이싱이 없다.** 아직 몇 개인지 모르고, 세려면 꺼내야 하고, 꺼내면 소진된다.
- ★ **`sorted` 는 「된다」가 아니라 「속으로 리스트를 만든다」다.** 정렬은 전부를 봐야 하므로
  **여기서 메모리 이점이 통째로 사라진다.** `min`·`max`·`sum` 은 한 칸으로 되지만 `sorted`·`reversed` 는 아니다.
- ★ **`in` 이 값을 먹는다.** `3 in g2` 가 0·1·2·3 을 꺼내 버려 `4` 만 남았다.
  **검사했을 뿐인데 상태가 바뀐다** — 이 주제에서 가장 눈에 안 띄는 자리다.

**비용** — 못 하는 것이 있다는 게 대가다.\
「**`len` 이나 인덱싱이 한 줄이라도 필요하면 그 자리는 리스트다**」가 판정 기준이다.

### 7. 비용 — 재 본 것

★ 아래는 **이 머신에서 실제로 잰 값**이다(측정 조건은 머리말에 있다). **절댓값이 아니라 기울기를 읽는다.**

```text
===== 소스: ex.py =====
import statistics, timeit
def med(stmt, n, r=11):
    return statistics.median(timeit.repeat(stmt, number=n, repeat=r)) / n * 1e6
n = 2000
a = med("sum([x * 2 for x in range(1000)])", n)
b = med("sum(x * 2 for x in range(1000))", n)
print(f"전부 소비   [..] {a:8.1f} us   (..) {b:8.1f} us   비 {b/a:5.2f}")
c = med("next(iter([x * 2 for x in range(1000)]))", n)
d = med("next(iter(x * 2 for x in range(1000)))", n)
print(f"앞 1개만    [..] {c:8.1f} us   (..) {d:8.1f} us   비 {d/c:5.2f}")
```

세 판을 돌린 결과다. ★ **다시 돌리면 또 달라진다** — 대조할 것은 숫자가 아니라 아래에 적은 성질이다.
(`--- 판 N ---` 줄은 세 판을 가르려고 붙인 것이고 스크립트가 찍는 것이 아니다.)

```text
--- 판 1 ---
전부 소비   [..]     28.5 us   (..)     30.8 us   비  1.08
앞 1개만    [..]     23.3 us   (..)      0.3 us   비  0.01
--- 판 2 ---
전부 소비   [..]     28.3 us   (..)     34.0 us   비  1.20
앞 1개만    [..]     23.0 us   (..)      0.2 us   비  0.01
--- 판 3 ---
전부 소비   [..]     29.1 us   (..)     42.1 us   비  1.45
앞 1개만    [..]     31.8 us   (..)      0.2 us   비  0.01
```

★ **두 줄의 신뢰도가 다르다 — 그것이 이 표의 요점이다.**

| 줄 | 세 판의 비 | 신호 대 잡음 | 읽는 법 |
|---|---|---|---|
| **전부 소비** | 1.08 · 1.20 · 1.45 | **신호가 잡음에 가깝다**(판마다 30% 넘게 흔들렸다) | 「제너레이터가 좀 느릴 수 있다」까지만. **「느리다」로 단정할 근거가 안 된다** |
| **앞 1개만** | 0.01 · 0.01 · 0.01 | **100배** | 「앞쪽만 필요하면 제너레이터가 압도적」은 이 줄이 근거다 |

★★ **그래서 「제너레이터가 느리다」는 이 측정으로는 주장하지 않는다.**
근거가 서는 것은 **「전부 소비하면 이점이 없다」와 「앞쪽만 쓰면 100배 차이가 난다」** 둘뿐이다.\
★ 3.12 에서 리스트 컴프리헨션이 **인라인**됐다는 것(PEP 709)도 이 줄에 섞여 있다 — 아래 「구현 세부사항」을 보라.

## 문법 — 형태와 규칙

```python
(x * 2 for x in xs)                 # 제너레이터 표현식
(x for x in xs if 조건)              # 필터
(x for a in xss for x in a)          # 중첩 — for 를 쓴 순서대로
sum(x * 2 for x in xs)               # ★ 유일한 인자면 괄호를 생략할 수 있다
sum((x * 2 for x in xs), 10)         # 인자가 둘이면 괄호가 필요하다
list(gen) · tuple(gen) · set(gen)    # 물질화
itertools.islice(gen, n)             # 앞 n 개만
```

규칙 다섯.

1. **소괄호면 제너레이터, 대괄호면 리스트.** 값은 같고 **언제 만드냐**가 다르다([14번](../14-comprehensions/2-summary.md)).
2. **함수의 유일한 인자일 때만 괄호를 생략**할 수 있다. 인자가 둘이면 `SyntaxError` 다.
3. **첫 `for` 의 iterable 만 즉시 평가**된다. 나머지 `for`·`if`·식은 전부 `next()` 때 평가된다.
4. **한 번 소진하면 끝**이다. 되감기가 없다.
5. **`len`·인덱싱·슬라이싱이 없다.** 필요하면 물질화해야 하고, 그 순간 이점이 사라진다.

**금지 사례 — 에러가 나는 자리**

```python
sum(n for n in range(4), 10)    # SyntaxError — 유일한 인자가 아닌데 괄호가 없다
len(gen)                        # TypeError — 개수를 모른다
gen[0]                          # TypeError — 첨자가 없다
list(무한_제너레이터)             # 에러가 아니다 — 영영 안 끝난다
```

★ **`SyntaxError` 만은 소스 줄과 캐럿이 나온다**(머리말의 던지는 형태 참고).

```text
===== 소스: ex.py =====
print(sum(n for n in range(4), 10))
```

```text
  File "<stdin>", line 1
    print(sum(n for n in range(4), 10))
              ^^^^^^^^^^^^^^^^^^^
SyntaxError: Generator expression must be parenthesized
```

★ 메시지가 고칠 방법을 그대로 말한다 — `sum((n for n in range(4)), 10)` 으로 감싸면 된다.
**이것은 정의 시점(컴파일) 오류라 그 줄이 안 도는 자리에 있어도 프로그램이 시작조차 안 된다**(그 층 구분의 정본은 [19번](../19-function-argument-rules/2-summary.md)).

## 어디서 틀리나

### (1) `getsizeof` 하나로 「메모리를 아꼈다」를 주장한다

**리스트 자신만 세고 원소는 안 센다.** 실측에서 8.4 MB 로 보였던 것이 실제로는 **40 MB** 였다.\
고치는 법: `tracemalloc` 의 **최대치**를 같이 본다.

### (2) 다 끝난 뒤에 메모리를 잰다

`현재` 값은 둘 다 거의 0 이다. **재야 하는 것은 최대치**다 — OOM 은 거기서 난다.

### (3) 중간에 `list()`·`sorted()` 가 끼어 있다

「제너레이터로 바꿨는데 메모리가 안 줄었다」의 대부분이 이것이다.\
**`sorted`·`reversed`·`len`·인덱싱이 하나라도 있으면 그 자리에서 전부 물질화된다.**

### (4) 두 번 돌린다

두 번째가 **예외가 아니라 `0`·`[]`** 다. 함수에 넘기면 그 함수가 조용히 빈 것을 받는다.\
★ **`sum` 은 `0`, `list` 는 `[]`, `max` 는 `ValueError`** — 같은 원인이 세 얼굴로 나온다.

### (5) `in` 으로 검사한 뒤 다시 쓴다

**검사가 값을 먹는다.** `3 in g` 뒤에 `list(g)` 를 하면 앞쪽이 사라져 있다.

### (6) 「전부 지연된다」고 믿는다

**첫 `for` 의 iterable 은 지금 평가된다.** 없는 이름이면 **만드는 줄에서** 터진다.\
반대로 **둘째 `for` 의 이름은 `next()` 때** 터진다 — 한 식 안에서 시점이 둘로 갈린다.

### (7) 만들어 놓고 원본을 고친다

**이름을 갈아 끼우면 안 따라가고, 같은 객체를 고치면 따라간다.** 읽는 사람이 둘을 구분 못 한다.

### (8) 부작용을 제너레이터 표현식으로 짠다

**아무도 소비 안 하면 한 번도 안 돈다.** 「DB 에 다 넣었는데 한 행도 안 들어갔다」가 이 모양이다.\
그 정본은 [14번](../14-comprehensions/2-summary.md)과 [17번](../17-generators-yield/2-summary.md)에 있다.

### (9) 무한 수열을 물질화한다

**에러가 안 난다.** 프로그램이 그냥 안 끝난다. `islice` 로 끊어야 한다.

### (10) 「제너레이터가 빠르다」로 외운다

**전부 소비하면 이점이 없다**(실측에서 오히려 조금 느렸고, 그마저 잡음 범위였다).
이점은 **앞쪽만 쓸 때**와 **메모리**에 있다.

## 구현 세부사항 대 언어 보장

세 층으로 가른다. ★ **이 주제는 「언어 보장」과 「구현」이 깔끔하게 갈린다** —
**무엇이 언제 평가되나**는 전부 명세이고, **그것을 어떤 명령으로 하나**와 **몇 바이트냐**는 전부 구현이다.

| 층 | 무엇인가 | 어떻게 확인했나 |
|---|---|---|
| **언어 보장** | 언어 레퍼런스가 정한 것 | 공식 문서 문장을 열어서 인용 |
| **CPython 구현** | 이 구현이 그렇게 하는 것 | `dis` · 3.11.15 로 대조 |
| **이 판·이 머신의 관찰** | 3.12.3·이 머신에서 그랬을 뿐 | 바이트 수·시간 수치 |

### 언어 보장

| 사실 | 근거 |
|---|---|
| 제너레이터 표현식은 **새 제너레이터 객체를 낸다** | 6.2.8 — *"A generator expression yields a new generator object."* |
| **가장 왼쪽 `for` 의 iterable 식은 즉시 평가**되고, 거기서 난 에러는 **정의된 자리**에서 나온다 | 6.2.8 — *"immediately evaluated, so that an error produced by it will be emitted at the point where the generator expression is defined"* |
| 나머지 식은 **제너레이터가 호출될 때** 지연 평가된다 | 6.2.8 — *"The other expressions ... are lazily evaluated."* |
| 가장 왼쪽 iterable 을 빼면 **감춰진 중첩 스코프**에서 돈다 | 6.2.4 |
| **유일한 인자일 때만 괄호를 생략**할 수 있다 | 6.2.8 — *"only be omitted on calls with only one argument"* |
| `getsizeof` 는 **그 객체가 참조하는 것의 메모리는 안 센다** | `sys.getsizeof` — *"not the memory consumption of objects it refers to"* |

★ **「두 번째가 빈 결과」도 언어 보장이다** — 소진된 이터레이터는 계속 `StopIteration` 을 내도록 정해져 있다([16번](../16-iterator-protocol/2-summary.md)). 구현 편의가 아니다.

### CPython 구현 세부사항

| 사실 | 어떻게 확인했나 |
|---|---|
| **리스트 컴프리헨션이 3.12 부터 인라인**된다(PEP 709) — 별도 코드 객체가 없다 | `dis` — 3.12 와 3.11.15 를 나란히 |
| **제너레이터 표현식은 인라인 대상이 아니다** — `MAKE_FUNCTION` + `CALL` 이 그대로 | `dis` — 두 판이 같다 |
| 제너레이터 쪽 바이트코드에 **`GET_ITER` 가 `CALL` 보다 먼저** 있다 | `dis` — 「첫 iterable 즉시 평가」의 기계 증거 |
| `CALL_INTRINSIC_1 3 (INTRINSIC_STOPITERATION_ERROR)` 가 코드 끝에 깔린다 | `dis` — PEP 479 의 자리([16번](../16-iterator-protocol/2-summary.md)) |
| 제너레이터 객체가 `192`·`200` 바이트인 것 | `getsizeof` — **판·빌드·식의 복잡도에 달렸다** |
| 리스트가 `8448728` 바이트인 것 | 과할당 정책의 결과 |

```text
===== 소스: ex.py =====
import dis
print("===== [x for x in it] =====")
dis.dis(compile("[x for x in it]", "<lc>", "eval"))
print("===== (x for x in it) =====")
dis.dis(compile("(x for x in it)", "<ge>", "eval"))
```

```text
===== [x for x in it] =====
  0           0 RESUME                   0

  1           2 LOAD_NAME                0 (it)
              4 GET_ITER
              6 LOAD_FAST_AND_CLEAR      0 (x)
              8 SWAP                     2
             10 BUILD_LIST               0
             12 SWAP                     2
        >>   14 FOR_ITER                 4 (to 26)
             18 STORE_FAST               0 (x)
             20 LOAD_FAST                0 (x)
             22 LIST_APPEND              2
             24 JUMP_BACKWARD            6 (to 14)
        >>   26 END_FOR
             28 SWAP                     2
             30 STORE_FAST               0 (x)
             32 RETURN_VALUE
        >>   34 SWAP                     2
             36 POP_TOP
             38 SWAP                     2
             40 STORE_FAST               0 (x)
             42 RERAISE                  0
ExceptionTable:
  10 to 26 -> 34 [2]
===== (x for x in it) =====
  0           0 RESUME                   0

  1           2 LOAD_CONST               0 (<code object <genexpr> at 0x740a5cf4eb10, file "<ge>", line 1>)
              4 MAKE_FUNCTION            0
              6 LOAD_NAME                0 (it)
              8 GET_ITER
             10 CALL                     0
             18 RETURN_VALUE

Disassembly of <code object <genexpr> at 0x740a5cf4eb10, file "<ge>", line 1>:
  1           0 RETURN_GENERATOR
              2 POP_TOP
              4 RESUME                   0
              6 LOAD_FAST                0 (.0)
        >>    8 FOR_ITER                 6 (to 24)
             12 STORE_FAST               1 (x)
             14 LOAD_FAST                1 (x)
             16 YIELD_VALUE              1
             18 RESUME                   1
             20 POP_TOP
             22 JUMP_BACKWARD            8 (to 8)
        >>   24 END_FOR
             26 RETURN_CONST             0 (None)
        >>   28 CALL_INTRINSIC_1         3 (INTRINSIC_STOPITERATION_ERROR)
             30 RERAISE                  1
ExceptionTable:
  4 to 26 -> 28 [0] lasti
```

★★ **이 결과는 CPython 3.12.3 의 구현이지 언어 보장이 아니다.** 명령 이름도 배치도 판마다 바뀐다.\
★ `0x740a5cf4eb10` 은 **매번 다른 값**이다 — 대조할 것은 주소가 아니라 「**코드 객체가 따로 있다**」는 성질이다.

바이트코드가 말하는 것 셋.

1. **리스트 쪽에는 코드 객체가 없다.** `BUILD_LIST`·`LIST_APPEND` 가 바깥 코드에 **그대로 펴 들어갔다**(PEP 709).
2. **제너레이터 쪽에는 `<genexpr>` 코드 객체가 따로 있고** `MAKE_FUNCTION` 으로 함수를 만들어 `CALL` 한다.
   **인라인 대상이 아니다** — 그래서 트레이스백에 `in <genexpr>` 줄이 남는다.
3. ★★ **`LOAD_NAME it` → `GET_ITER` 가 `CALL` 보다 앞에 있다.** 제너레이터를 **만들기도 전에** `it` 을 읽어
   `iter()` 를 걸어 놓고, 그것을 인자(`.0`)로 넘긴다. **「첫 iterable 즉시 평가」가 바이트코드에 그대로 박혀 있다.**

**3.11.15 로 대조한 결과 — 리스트 쪽만 달라진다**

```text
===== 소스: ex.py =====
import dis
dis.dis(compile("[x for x in it]", "<lc>", "eval"))
```

```text
  0           0 RESUME                   0

  1           2 LOAD_CONST               0 (<code object <listcomp> at 0x773d92d1ef50, file "<lc>", line 1>)
              4 MAKE_FUNCTION            0
              6 LOAD_NAME                0 (it)
              8 GET_ITER
             10 PRECALL                  0
             14 CALL                     0
             24 RETURN_VALUE

Disassembly of <code object <listcomp> at 0x773d92d1ef50, file "<lc>", line 1>:
  1           0 RESUME                   0
              2 BUILD_LIST               0
              4 LOAD_FAST                0 (.0)
        >>    6 FOR_ITER                 4 (to 16)
              8 STORE_FAST               1 (x)
             10 LOAD_FAST                1 (x)
             12 LIST_APPEND              2
             14 JUMP_BACKWARD            5 (to 6)
        >>   16 RETURN_VALUE
```

★ **3.11 에서는 리스트 컴프리헨션도 제너레이터 표현식과 똑같은 모양**이었다 — 코드 객체 + `MAKE_FUNCTION` + `CALL`.
3.12 에서 **한쪽만** 인라인됐다.\
★ **그래도 `LOAD_NAME it` → `GET_ITER` 가 `CALL` 앞에 있는 것은 두 판이 같다** — 즉시 평가 규칙은 명세라 안 흔들린다.

### 이 판(3.12.3)·이 머신의 관찰

| 관찰 | 어디가 흔들리나 |
|---|---|
| `getsizeof` 가 리스트 `8448728` · 제너레이터 `200`/`192` | **과할당 정책·빌드·식의 복잡도.** 배수 `42243` 은 `N` 에 달렸다 |
| `tracemalloc` 최대치 `40444616` 대 `646` | **할당기 상태.** 재현되는 것은 「한쪽만 `N` 에 비례한다」는 성질뿐 |
| `timeit` 수치와 비(`1.08`\~`1.45`, `0.01`) | **머신·부하.** 앞 줄은 **잡음 범위**이고 뒤 줄만 근거가 된다 |
| 바이트코드 명령 이름·오프셋 | 3.11.15 에서 다르다(`PRECALL` 이 있다) |
| 코드 객체 주소 `0x740a5cf4eb10` | **매 실행 다르다.** 의미 없는 숫자다 |
| 예외 **문구** 전부 | 예외 **종류**는 명세지만 문구는 아니다 |

### 그래서 이렇게 적으면 틀린다

- ✗ 「제너레이터 표현식은 아무것도 평가하지 않는다」\
  ○ **첫 `for` 의 iterable 은 즉시 평가되고 `iter()` 까지 걸린다.** 바이트코드에 박혀 있다.
- ✗ 「`getsizeof` 로 메모리를 확인했다」\
  ○ **참조하는 것을 안 센다.** 실측에서 8.4 MB 대 40 MB 로 다섯 배 어긋났다.
- ✗ 「제너레이터는 리스트보다 빠르다」\
  ○ **전부 소비하면 이점이 없다.** 이점은 **메모리**와 **앞쪽만 쓸 때**에 있다.
- ✗ 「소진된 제너레이터를 다시 쓰면 에러가 난다」\
  ○ **`0`·`[]` 가 나온다.** `max` 만 `ValueError` 라 증상이 함수마다 다르다.
- ✗ 「제너레이터로 바꾸면 메모리가 준다」\
  ○ **중간에 `sorted`·`len`·인덱싱이 하나라도 있으면 그 자리에서 전부 물질화된다.**
- ✗ 「`[..]` 와 `(..)` 는 바이트코드도 비슷하다」\
  ○ **3.12 에서 둘 중 리스트 쪽만 인라인됐다**(PEP 709 는 list·dict·set 을 인라인하고 제너레이터 표현식은 빼 둔다).
  그리고 그것은 **구현이지 보장이 아니다.**
- ✗ 「`in` 으로 확인하는 것은 읽기니까 안전하다」\
  ○ **값을 먹는다.** 확인 자체가 상태를 바꾼다.

**판정 기준 한 줄**: **「값이 같은데 무엇이 다른가」를 물으면 바이트를 재고, 「언제 평가되나」를 물으면 첫 `for` 만 떼어 보라.**

## 언제 쓰고 언제 안 쓰나

| 상황 | 판정 |
|---|---|
| 큰 입력을 **한 번** 훑어 합·최대·최소를 낸다 | **제너레이터 표현식** — `sum(x for x in ...)` |
| 조건에 맞는 **처음 N 개**만 필요하다 | **제너레이터 표현식** + `islice` |
| 끝이 없거나 개수를 모른다 | **제너레이터 표현식** — 리스트로는 표현이 안 된다 |
| 단계를 파이프라인으로 잇는다 | **제너레이터 표현식** — 중간 리스트가 안 생긴다 |
| **두 번 이상** 돌아야 한다 | **리스트** — 두 번째가 조용히 빈 것이 된다 |
| `len`·인덱싱·슬라이싱이 한 줄이라도 있다 | **리스트** |
| 정렬해야 한다 | **리스트** — `sorted` 가 어차피 전부 물질화한다 |
| 원소가 적다(수십\~수백) | **리스트** — 지연은 공짜가 아니고 읽기도 어렵다 |
| 부작용(쓰기·전송)이 목적이다 | **둘 다 아니다** — `for` 문을 쓴다 |

## 핵심 문장

- **값으로는 두 형태를 구분할 수 없다.** 「지연 평가」는 **쓰인 바이트**로만 증명된다.
- **`getsizeof` 는 그 객체 자신만 센다.** 리스트 안의 정수까지 보려면 `tracemalloc` 의 **최대치**를 봐야 한다 — 실측에서 8.4 MB 대 40 MB 였다.
- **제너레이터 객체의 크기는 원소 수와 무관**하다. 5개든 100만개든 `192` 였다. 달라진 것은 **식의 복잡도**뿐이다(`200`).
- **전부 늦지는 않는다.** 가장 왼쪽 `for` 의 iterable 만은 **지금** 평가되고 `iter()` 까지 걸린다 — 바이트코드의 `GET_ITER` 가 `CALL` 앞에 있다.
- **둘째 `for` 의 이름은 `next()` 때 터진다.** 한 식 안에서 평가 시점이 둘로 갈린다.
- **한 번 돌면 끝이고 두 번째는 예외가 아니다** — `sum` 은 `0`, `list` 는 `[]`, `max` 만 `ValueError`.
- **`in` 이 값을 먹는다.** 검사가 상태를 바꾸는 드문 자리다.
- **3.12 에서 컴프리헨션이 인라인됐다**(PEP 709 — list·dict·set 셋 다. 이 주제에서는 리스트 쪽을 본다).
  제너레이터 표현식은 **대상이 아니라** 여전히 코드 객체 + `CALL` 이다 — **구현이지 보장이 아니다.**

## 관련 자료

- 목록: [python/syntax 주제 목록](../README.md) — 이 주제는 **15번**
- 선행: [14-comprehensions](../14-comprehensions/2-summary.md) — **괄호 하나 차이의 정본.**\
  **경계**: 그쪽은 **평가 시점·감춰진 스코프·네 가지 형태**까지, 여기는 「**그래서 메모리에서 무엇이 달라지나**」부터다.
- 선행: [09-sequence-ops-and-slicing](../09-sequence-ops-and-slicing/2-summary.md) — 리스트가 무엇을 들고 있나. 슬라이싱이 제너레이터에 없는 이유.
- 정본 이웃: [17-generators-yield](../17-generators-yield/2-summary.md) — **제너레이터 객체 자체의 정본.**\
  **경계**: `yield`·프레임·`send`·`close`·`yield from`·상태 전이는 전부 그쪽이다. 여기는 **표현식 꼴과 메모리**만 다룬다.
- 함께 보는 곳: [16-iterator-protocol](../16-iterator-protocol/2-summary.md) — 「소진되면 빈 것이 나온다」가 왜 규칙인지.
- 함께 보는 곳: [18-loop-control-and-else](../18-loop-control-and-else/2-summary.md) — `range` 가 제너레이터가 **아닌** 이유(두 번 돈다).
- 함께 보는 곳: [19-function-argument-rules](../19-function-argument-rules/2-summary.md) — `SyntaxError`(정의 시점)와 `TypeError`(호출 시점)를 가르는 층의 정본.
- 이어지는 곳: 목록의 **44번 주제** 「`itertools`」 — `islice`·`chain`·`tee` 의 정본.
- 원리: [`cs/data-structure/`](../../../../../data-structure/) — 동적 배열이 왜 과할당하나.\
  **경계**: 그쪽은 **왜 2배씩 늘리나**까지, 여기는 **그래서 `getsizeof` 가 왜 그 숫자냐**부터다.
- 기존 노트: [`cs/foundations/python-basics/`](../../../../python-basics/) — 컴프리헨션을 쓰는 법까지가 그쪽이다.
- 공식 문서: [6.2.8. Generator expressions](https://docs.python.org/3.12/reference/expressions.html#generator-expressions) · [`sys.getsizeof`](https://docs.python.org/3.12/library/sys.html#sys.getsizeof) · [`tracemalloc`](https://docs.python.org/3.12/library/tracemalloc.html) · [PEP 709](https://peps.python.org/pep-0709/)

## 용어 풀이

- **제너레이터 표현식(generator expression)**: 소괄호 안에 `식 for 이름 in 이터러블` 을 쓴 것. 값을 만들지 않고 **만드는 방법**을 들고 있는 객체를 낸다.
- **지연 평가(lazy evaluation)**: 요청받을 때 하나씩 계산하는 방식. 반대는 **즉시 평가(eager evaluation)** 다.
- **물질화(materialize)**: `list()`·`tuple()`·`sorted()` 로 전부 꺼내 실제 자료구조로 만드는 것.\
  개수를 세거나 두 번 돌려면 필요하고, **그 순간 메모리 이점이 사라진다.**
- **소진(exhaustion)**: 끝까지 꺼내 더 낼 것이 없어진 상태. 다시 쓰면 에러가 아니라 **빈 결과**다.
- **`sys.getsizeof(obj)`**: 그 객체 **자신이** 쓰는 바이트. **참조하는 것은 안 센다.**\
  예: 리스트는 포인터 칸만 세고 그 안의 정수 객체는 안 센다.
- **`tracemalloc`**: 파이썬이 할당한 블록을 추적하는 표준 모듈. `get_traced_memory()` 가 `(현재, 최대)` 를 준다.\
  예: 다 끝난 뒤의 「현재」는 0 에 가까우므로 **「최대」를 봐야** 한다.
- **파이프라인(pipeline)**: 제너레이터를 여러 겹 이어 한 원소씩 흘려보내는 구조.\
  예: 세 겹을 쌓아도 중간 리스트가 하나도 안 생긴다.
- **`itertools.islice(it, n)`**: 앞 `n` 개만 잘라 주는 지연 도구. 인덱싱이 없는 것에도 걸린다.
- **인라인화(inlining)**: 별도 함수 호출로 처리하던 것을 부르는 쪽에 그대로 펴 넣는 최적화.\
  예: PEP 709 가 3.12 에서 **컴프리헨션만** 그렇게 했다. 제너레이터 표현식은 대상이 아니다.
- **과할당(over-allocation)**: 리스트가 다음 `append` 를 대비해 필요보다 큰 칸을 잡아 두는 것.\
  예: 백만 개 리스트의 `getsizeof` 가 딱 800만이 아니라 `8448728` 인 이유다.

## 더 들어가면

- **`itertools.tee`** 는 「두 번 돌아야 한다」의 유일한 지연 해법처럼 보이지만 **공짜가 아니다** —
  한쪽이 앞서 나가면 그만큼을 **내부 버퍼에 쌓아 둔다.** 앞뒤 차이가 크면 리스트를 만드는 것과 같아진다(목록의 **44번 주제**).
- **파일 객체가 그 자체로 이터레이터다** — `for line in f:` 가 한 줄씩 읽는다.
  그래서 `f.read().split("\n")` 대신 `f` 를 그냥 도는 것이 10GB 파일의 정답이다(목록의 **48번 주제**).
- **비동기 판이 따로 있다** — `(x async for x in agen)` 은 **비동기 제너레이터**를 만든다(3.6+, PEP 530). 목록의 **51번 주제**.
- **개수를 세는 관용구**는 `sum(1 for _ in it)` 이다. `len(list(it))` 보다 메모리를 안 쓰지만 **둘 다 소진시킨다.**
