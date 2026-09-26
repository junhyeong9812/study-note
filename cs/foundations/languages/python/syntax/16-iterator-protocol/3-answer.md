# python/syntax/16-iterator-protocol — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> [1-question.md](1-question.md)의 번호와 **1:1**로 대응한다. 질문 12개 = 답 12개.
>
> 이 파일의 모든 출력은 `python3` **3.12.3** 에서 실제로 돌려 나온 것이다. 지어낸 출력은 없다.
> 던지는 형태는 `python3 - <파일` 로 고정했다 — 그래서 트레이스백에 **소스 줄과 캐럿이 없다.**
> 단 **타입 이름·예외 문구·`gi_*` 속성**은 구현에 달린 것이라 다른 구현·다른 판에서는 달라진다(11번 답).

## 정답

### 1. 세 조각 — 그리고 마지막 `[]` 는 명세다

**출력**

```text
iter(xs)        -> list_iterator
next            -> a
next            -> b
next            -> StopIteration None | args = ()
next(it, '기본') -> 기본
두 번째 list(it) -> []  <- 예외가 아니다
```

**왜 그런가**

```text
   for item in xs:              와 같다        it = iter(xs)        <- ①
       본문                                    while True:
                                                   try:
                                                       item = next(it)   <- ②
                                                   except StopIteration: <- ③
                                                       break
                                                   본문
```

- ① **`iter(xs)` 가 `list_iterator` 를 낸다.** 리스트 자신은 커서를 안 들고 있다 —
  그래서 같은 리스트를 두 `for` 가 동시에 돌 수 있다.
- ② 값이 다 나오면 ③ **`StopIteration`**. `for` 가 그것을 잡아 **조용히 빠져나간다.**
- `e.value` 가 `None` 이고 `args` 가 비었다 — `return` 없이 끝났기 때문이다(그 `value` 를 쓰는 곳은 [17번](../17-generators-yield/2-summary.md)의 `yield from`).
- `next(it, "기본")` 은 **예외 대신 기본값**을 낸다 — 끝을 예외 없이 감지하는 유일한 내장 수단이다.

★★ **마지막 `[]` 는 명세다 — 구현의 편의가 아니다.**
문서가 계약으로 못 박는다 — *"Once an iterator's `__next__()` method raises `StopIteration`,
it must **continue to do so on subsequent calls**. Implementations that do not obey this property are deemed broken."*

★ **그래서 「소진된 것을 다시 쓰면 빈 결과」는 버그가 아니라 규칙이다.**
고칠 수 있는 것은 언어가 아니라 **내 코드**다 — 두 번 돌 것이면 물질화해야 한다.

### 2. `__iter__` 열은 아무것도 못 가른다

**출력**

```text
python 3.12.3
object           __iter__  __next__  iter(x) is x
[1, 2]               True     False         False
iter([1, 2])         True      True          True
(1, 2)               True     False         False
'ab'                 True     False         False
range(3)             True     False         False
iter(range(3))       True      True          True
gen()                True      True          True
enumerate('ab')      True      True          True
zip('ab', 'cd')      True      True          True
map(str, [1])        True      True          True
reversed([1, 2])     True      True          True
```

**왜 그런가**

- ★ **`__iter__` 열이 전부 `True`** 다. 「이터러블인가」만 말하고 **「몇 번 돌 수 있나」는 하나도 안 말한다.**
- ★★ **`__next__` 열과 `iter(x) is x` 열이 한 칸도 안 어긋난다.** 그것이 계약이다 —
  *"iterators are required to have an `__iter__()` method that **returns the iterator object itself**."*
  즉 **`__next__` 가 있으면 `__iter__` 는 `self` 여야 한다.**

**실무 사고가 나는 네 줄**

```text
   enumerate('ab')   zip('ab','cd')   map(str,[1])   reversed([1,2])
        ▲                 ▲                ▲               ▲
        └────────── 전부 이터레이터다. 두 번째 루프가 빈다 ──────────┘
```

- 이 넷은 **생긴 모양이 「값의 묶음」이라 리스트처럼 읽힌다.** 그런데 번호표다.
- `rows = zip(a, b)` 를 만들어 두고 **두 군데서 돌면 뒤쪽이 빈다.** 에러가 안 난다.
- ★ **`range` 만 이 무리에서 빠진다** — `iter(r) is r` 이 `False` 라 몇 번이든 돈다([18번](../18-loop-control-and-else/2-summary.md)).
  **`range` 를 「지연되니까 제너레이터겠지」로 묶어 외우면 여기서 틀린다.**

### 3. 한쪽은 잡히고 한쪽은 안 잡힌다 — 안 잡히는 쪽이 나쁘다

**출력**

```text
두 번 돌린다 : [3, 2, 1] [3, 2, 1]
이터레이터를 직접 두 번 : [3, 2, 1] []
iter(c) is c : False | iter(it) is it : True
__next__ 는 있는데 __iter__ 가 남을 주면 : [2, 1]
  next(b) 는 : StopIteration
__next__ 없이 __iter__ 만 : TypeError: iter() returned non-iterator of type 'NoNext'
```

**왜 그런가**

```text
   Countdown (기계)                  CountdownIter (번호표)
   __iter__ -> 새 CountdownIter      __iter__ -> self
                                     __next__ -> 값 또는 StopIteration

   list(c), list(c)  -> [3,2,1] [3,2,1]    매번 새 번호표
   list(it), list(it) -> [3,2,1] []        번호표 하나
```

**두 가지 계약 위반**

| 위반 | 언어가 잡나 | 증상 |
|---|---|---|
| `__iter__` 가 있는데 **`__next__` 가 없다**(`NoNext`) | ★ **잡는다** | `TypeError: iter() returned non-iterator of type 'NoNext'` |
| `__next__` 가 있는데 **`__iter__` 가 남을 준다**(`Broken`) | ✗ **안 잡는다** | `list(b)` 는 `[2, 1]` · `next(b)` 는 즉시 `StopIteration` |

★★ **안 잡히는 쪽이 나쁜 이유 — 같은 객체가 두 얼굴을 갖는다.**

```text
   b 를 for 에 넣으면        ->  __iter__ 를 부른다  ->  남의 번호표  ->  [2, 1]
   b 에 next() 를 부르면     ->  __next__ 를 부른다  ->  즉시 끝      ->  StopIteration
```

**어느 쪽도 예외가 아니다.** 「`for` 로는 값이 나오는데 `next` 로는 안 나온다」는 버그는
**객체를 아무리 들여다봐도 원인이 안 보인다** — 두 메서드가 서로 모순인 것을 언어가 검사하지 않기 때문이다.\
★ 그래서 **「이터레이터의 `__iter__` 는 `self` 다」가 외워야 하는 규칙**이 된다. 문서가 *"deemed broken"* 이라고만 적을 뿐 강제하지 않는다.

★ 실무에서 이 위반을 피하는 가장 쉬운 길은 **`__iter__` 를 제너레이터 함수로 쓰는 것**이다 —
제너레이터가 계약을 자동으로 지킨다([17번](../17-generators-yield/2-summary.md)).

### 4. 세 번 불렸다 — 끝은 `IndexError` 로 알려진다

**출력**

```text
__iter__ 가 있나 : False
__next__ 가 있나 : False
for 가 도나 :
   __getitem__ 0
  받음: x
   __getitem__ 1
  받음: y
   __getitem__ 2
iter(o) -> iterator
   __getitem__ 0
   __getitem__ 1
   __getitem__ 2
list(o) -> ['x', 'y']
   __getitem__ 0
'x' in o -> True
reversed 는?
   TypeError: object of type 'Old' has no len()
```

**왜 그런가**

```text
   for v in o:   -- __iter__ 가 없다 --> o[0]  -> 'x'
                                         o[1]  -> 'y'
                                         o[2]  -> IndexError  -> 끝
```

- ★ **값 두 개를 얻는 데 `__getitem__` 이 세 번 불렸다.** 마지막 한 번이 **끝을 확인하는 호출**이다.
  그 `IndexError` 는 `StopIteration` 으로 **번역돼** 바깥에 안 나온다.
- **개수가 증명하는 것** — 이 경로에는 **길이를 미리 묻는 단계가 없다.**
  `__len__` 을 안 부르고 **터질 때까지 밀어 본다.** 그래서 `reversed` 는 안 되고(`__len__` 이 필요하다) `for` 는 된다.
- `iter(o)` 가 **`iterator`** 라는 이름의 객체를 낸다 — **언어가 번호표를 대신 만들어 준다.**
- `in` 도 같은 경로다 — 0번에서 찾고 멈췄다(`__getitem__ 0` 한 번만 찍혔다).

**`hasattr(o, '__iter__')` 검사가 잘못되는 것**

- ★ **`False` 가 나오는데 `for` 는 돈다.** 「이터러블이 아니다」로 판정하고 `list(o)` 를 안 하면 **멀쩡히 순회 가능한 객체를 거부**한다.
- 바른 검사는 **`iter(x)` 를 실제로 걸어 보고 `TypeError` 를 잡는 것**이다(9번 답).

★ **문서가 이 대체 경로를 「시퀀스 프로토콜」이라고 부른다** — `__getitem__` 을 0부터 정수로 부른다.
새로 쓰는 코드에서 일부러 쓸 이유는 없고, **남의 코드를 읽다 「왜 이게 `for` 에 들어가지」 할 때 답이 되는 지식**이다.

### 5. `RuntimeError` — 3.6 이전에는 조용히 잘렸다

**출력**

```text
[1, 2]
Traceback (most recent call last):
  File "<stdin>", line 3, in take_two
StopIteration

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "<stdin>", line 6, in <module>
RuntimeError: generator raised StopIteration
```

**왜 그런가**

```text
   3.6 이전                              3.7 이후 (PEP 479)
   next(it) 가 StopIteration            next(it) 가 StopIteration
        │                                     │
   제너레이터 밖으로 샌다                  RuntimeError 로 바뀐다
        │                                     │
   바깥 for 가 "끝났다" 로 읽는다          터진다
        │                                     │
   list(...) -> [1]   ★ 조용히 하나만     추적 가능한 실패
```

- ★★ **3.6 이전이었다면 둘째 줄은 `[1]`** 이었다. **예외 없이, 경고 없이, 하나만 나오고 끝.**
  두 개를 달라고 했는데 하나만 오는데 **아무도 안 알려 준다.**
- PEP 479 가 바꾼 것은 **「무음 실패」를 「시끄러운 실패」로** 바꾼 것이다. 동작을 고친 것이 아니라 **진단을 만든 것**이다.
- 트레이스백이 **두 덩어리**인 것도 그 설계다 — `The above exception was the **direct cause** of` 로
  **원인이던 `StopIteration` 이 지워지지 않고 남는다.** 어느 줄에서 샜는지가 첫 덩어리에 있다.
- 고치는 법: `next(it, None)` 로 **기본값을 주거나**, `try/except StopIteration: return` 으로 **명시적으로 끝낸다.**

★ 이 머신에 3.6 이하가 없어 **옛 동작은 직접 못 돌려 봤다** — PEP 479 문서 근거다.
3.5\~3.6 에서는 `from __future__ import generator_stop` 로 미리 켜는 선택이었고, **3.7 부터 무조건**이다.

### 6. 셋이 한 글자도 안 다르다 — 그리고 검사가 값을 먹었다

**출력**

```text
--- 바깥에서 보이는 것만으로 넷을 가를 수 있나 ---
  bool=True  iter(x) is x=True  next(x,'없음')=1        <- 아직 안 돈 제너레이터
  bool=True  iter(x) is x=True  next(x,'없음')='없음'     <- 소진된 제너레이터
  bool=True  iter(x) is x=True  next(x,'없음')='없음'     <- 처음부터 빈 이터레이터
  bool=True  iter(x) is x=True  next(x,'없음')='없음'     <- 소진된 리스트 이터레이터

--- 제너레이터만은 안이 보인다 (CPython 내성) ---
  만든 직후      gi_frame=True   gi_running=False  gi_suspended=False 
  next 1회    gi_frame=True   gi_running=False  gi_suspended=True  
  소진 후       gi_frame=False  gi_running=False  gi_suspended=False 

--- 남은 개수 힌트도 둘을 못 가른다 ---
  소진 전 iter([1,2]).__length_hint__() = 2
  소진 후                               = 0
  iter([]).__length_hint__()            = 0
```

**왜 그런가**

- ★★ **아래 세 줄이 완전히 같다.** 소진된 제너레이터 · 처음부터 빈 이터레이터 · 소진된 리스트 이터레이터 —
  **`bool`·`iter(x) is x`·`next(x, 기본)` 어느 것으로도 안 갈린다.**
- ★ **`bool` 이 넷 다 `True`** 다. **빈 이터레이터도 참**이다 — `bool([])` 이 `False` 인 것과 정반대다.
  `__bool__` 도 `__len__` 도 없으니 **기본값인 참**이 된다. **`if it:` 는 아무 정보도 안 준다.**
- **`__length_hint__` 도 못 가른다** — 소진된 것과 빈 것이 둘 다 `0` 이다. 게다가 문서상 **힌트일 뿐**이다.

**★ 검사하는 행위 자체가 무엇을 했나**

첫 줄의 `next(x, '없음')` 이 **`1` 을 반환했다** — 즉 **그 값을 꺼내 버렸다.**\
★★ **「남았나」를 물어본 대가로 하나가 사라졌다.** 되돌릴 방법이 없다.
이 주제에서 가장 얄궂은 자리다 — **관찰이 대상을 바꾼다.**

**`gi_frame` 으로 알 수 있는 것과 없는 것**

| 알 수 있다 | 알 수 없다 |
|---|---|
| **끝났나**(`gi_frame` 이 `None`) | **소진돼서 끝났나 `close()` 로 닫혔나** |
| **지금 멈춰 있나**(`gi_suspended`) | **몇 개 남았나** |
| **돌고 있나**(`gi_running`) | 제너레이터가 **아닌** 이터레이터의 상태 — `map`·`zip` 에는 이런 창이 아예 없다 |

★ **그리고 이 창은 CPython 의 내성 기능**이다. 다른 구현에 이 속성이 이 모양으로 있으리라는 보장이 없다.
상태 이름과 전이는 [17번](../17-generators-yield/2-summary.md)이 정본이다.

★★ **결론 — 객체를 심문해서는 답이 안 나온다. 「누가 먼저 소비했나」를 봐야 한다.**

### 7. 그 계약이 없으면 `for` 가 둘을 구분해야 한다

**출력** — 계약이 지켜질 때와 깨졌을 때.

```text
iter(c) is c : False | iter(it) is it : True
__next__ 는 있는데 __iter__ 가 남을 주면 : [2, 1]
  next(b) 는 : StopIteration
```

**왜 그런가**

★ **한 문장** — 계약이 있어서 **`for` 가 「받은 것이 기계인지 번호표인지 묻지 않고」 무조건 `iter()` 를 걸 수 있다.**

```text
   for x in obj:   ->   it = iter(obj)   ->   기계면 새 번호표
                                              번호표면 자기 자신
                        그다음은 똑같이 next(it) 반복
```

- 계약이 없다면 `for` 는 **먼저 「이게 이터레이터인가」를 판정**하고 두 갈래로 갈라야 한다.
- 그러면 **`for` 뿐 아니라** `list()`·`sum()`·`min()`·언패킹·`in`·컴프리헨션이 **전부** 같은 판정을 따로 해야 한다.
- 계약 한 줄로 **소비하는 쪽 코드 전체가 단일 경로**가 된다. 그래서 이 계약은 **편의가 아니라 설계의 축**이다.
- ★ 그리고 이 계약 덕분에 `it = iter(x); for a in it: ...; for b in it: ...` 처럼
  **한 소스를 여러 루프가 이어받는** 관용구가 가능해진다(3번 답의 `list(it), list(it)` 가 그 성질이다).

### 8. `[9]` — 센티널은 결과에 안 들어간다

**출력**

```text
--- pop 이 0 을 낼 때까지 ---
[9]
```

같은 실행의 앞부분이 두 인자 꼴의 모양을 보인다.

```text
--- iter(callable, sentinel) ---
타입      : callable_iterator
iter(it) is it : True
  받음: 'ab\n'
  받음: 'cd\n'
  받음: 'ef\n'
```

**왜 그런가**

```text
   [3, 1, 0, 9] 에 pop() 을 반복해서 부른다 (뒤에서 뺀다)

   1회차: pop() -> 9   센티널 0 과 다르다  -> 값으로 낸다
   2회차: pop() -> 0   센티널 0 과 같다    -> 멈춘다. ★ 이 0 은 안 낸다
                                              (그리고 이미 리스트에서 빠졌다)
   결과: [9]
```

- ★ **`pop()` 이 뒤에서 뺀다**는 것이 핵심이다. `3` 이 아니라 `9` 가 먼저 나온다.
- ★ **센티널은 결과에 안 들어간다.** 문서 — *"the iterator will call `object` ... until the returned value equals `sentinel`"*
  — 같아지는 그 값은 **끝 신호이지 원소가 아니다.**
- 그래서 `readline()` 판에서도 **마지막 빈 문자열 `''` 이 결과에 없다.** 세 줄만 나왔다.
- 두 인자 꼴은 **`while True: v = f(); if v == s: break` 를 한 줄로** 줄인 것이고, 결과가 `callable_iterator` 라
  **그대로 `for` 에 들어간다.** `iter(it) is it` 이 참이니 이것도 **번호표**다.

### 9. 둘 다 `__getitem__` 만 있는 것을 놓친다

**출력**

```text
isinstance(Old(), Iterable) : False
for 는 도나 : [1, 2]
```

(`Old` 는 `__getitem__` 만 가진 클래스다.)

**왜 그런가**

| 검사 | `__getitem__` 만 있는 객체에 | 왜 |
|---|---|---|
| `hasattr(x, '__iter__')` | **`False`** — 틀린 답 | 속성 하나만 본다 |
| `isinstance(x, collections.abc.Iterable)` | **`False`** — 틀린 답 | `__subclasshook__` 이 **`__iter__` 만** 본다 |
| ★ `iter(x)` 를 걸어 보고 `TypeError` 를 잡는다 | **참** — 바른 답 | 언어가 실제로 쓰는 경로와 같다 |

```python
def is_iterable(x):
    try:
        iter(x)
    except TypeError:
        return False
    return True
```

★ **문서가 `abc.Iterable` 의 이 한계를 직접 적는다** — `__iter__` 만으로 판정하므로
「`iter()` 로 순회 가능한 유일한 신뢰할 만한 판정법은 `iter(obj)` 를 부르는 것」이라는 취지다.\
★ **「검사기가 무엇을 못 보는가」를 아는 것이 요점**이다 — 두 검사 모두 **거짓 음성**을 낸다.
거짓 양성이 아니라 거짓 음성이라 **조용히 기능이 빠진다**(멀쩡한 객체를 거부한다).

### 10. 호출하는 쪽과 받는 쪽에서 각각 한 줄

**출력** — 막고 싶은 증상이다.

```text
이터레이터를 직접 두 번 : [3, 2, 1] []
```

**왜 그런가**

```text
   호출하는 쪽                              받는 쪽
   ───────────────────────────────         ───────────────────────────────
   process(list(rows))                     def process(rows):
        ^^^^^                                  if iter(rows) is rows:
   이터레이터를 넘기지 않는다                      rows = list(rows)
                                              ...
```

| 자리 | 막는 법 | 대가 |
|---|---|---|
| **호출하는 쪽** | `zip`·`map`·제너레이터를 그대로 넘기지 말고 **`list()` 로 감싸 넘긴다** | 메모리를 쓴다([15번](../15-generator-expressions-lazy-eval/2-summary.md)) |
| **받는 쪽** | `if iter(x) is x: x = list(x)` — **방어적 물질화** | 무한 이터러블을 받으면 **안 끝난다** |
| **둘 다 아닌 자리** | 함수를 **한 번만 순회하도록** 고친다 | 대개 이것이 진짜 해법이다 |
| 계약을 문서로 | 타입 힌트에 `Sequence[T]` 를 쓴다(`Iterable[T]` 가 아니라) | **런타임 강제는 없다**([목록의 **40번 주제**](../40-type-hints-at-runtime/)) |

★ **받는 쪽 방어가 만능이 아닌 이유** — 무한 수열을 `list()` 로 감싸면 그 자리에서 멈춘다([15번](../15-generator-expressions-lazy-eval/2-summary.md) 5번 답).
**「두 번 돌아야 한다」와 「무한을 받는다」는 동시에 만족할 수 없다.**\
★ 가장 강한 방어는 **한 번만 도는 코드**다 — 두 번 도는 설계를 고치는 것.

### 11. 세 층

**출력** — 층을 가르는 근거로 쓴 것.

```text
python 3.12.3
iter(xs)        -> list_iterator
두 번째 list(it) -> []  <- 예외가 아니다
```

**왜 그런가**

**언어 보장**

| 사실 | 근거 |
|---|---|
| 이터레이터의 `__iter__` 는 **자기 자신**을 돌려줘야 한다 | Iterator Types |
| `__next__` 는 값 또는 **`StopIteration`** | 〃 |
| **한 번 `StopIteration` 을 내면 계속 내야** 한다 | 〃 — *"must continue to do so on subsequent calls"* |
| `__iter__` 없이 **`__getitem__`(0부터)** 만 있어도 순회된다 | `iter()` |
| `iter(callable, sentinel)` — **센티널은 결과에 안 들어간다** | `iter()` |
| `next(it, default)` 는 예외 대신 기본값 | `next()` |
| 제너레이터 안에서 샌 `StopIteration` 은 **`RuntimeError`**(3.7+) | **PEP 479** |
| `__length_hint__` 는 **힌트**이지 보장이 아니다 | `operator.length_hint` |

**CPython 구현 세부사항**

| 사실 | 어떻게 확인했나 |
|---|---|
| 타입 이름 `list_iterator`·`range_iterator`·`callable_iterator`·`iterator` | 실행 — **이름은 구현의 것** |
| `gi_frame`·`gi_running`·`gi_suspended` 로 제너레이터 안을 본다 | 실행 — 3.11.15 에도 있었다 |
| 소진된 제너레이터의 `gi_frame` 이 `None` 이 되는 것 | 실행 |
| `list_iterator.__length_hint__()` 가 소진 후 `0` | 실행 |
| `iter()` 가 대체 경로용 이터레이터를 **대신 만들어 주는 것** | 실행 |
| 예외 **문구** 전부 | 실행 |

**이 판(3.12.3)의 관찰**

| 관찰 | 어디가 흔들리나 |
|---|---|
| `TypeError: 'list' object is not an iterator` 등 문구 | 종류는 명세, 문구는 아니다 |
| `RuntimeError: generator raised StopIteration` 문구 | 위와 같다 |
| 트레이스백이 **두 덩어리**로 나오는 것 | 예외 체이닝의 표시 방식 |
| `__getitem__` 이 **3번** 불린 것 | 대체 경로가 `IndexError` 로 끝을 안다는 결과 |
| `iter([3,1,0,9].pop, 0)` 이 `[9]` 인 것 | `list.pop()` 이 **뒤에서** 뺀다는 문서화된 동작의 결과 |

★ **판정 기준 한 줄** — **「무엇이 계약인가」는 명세에 있고, 「그 객체를 어떻게 들여다보나」는 이 구현에 있다.**

### 12. 네 주제의 경계

**출력** — 경계를 가르는 근거 하나씩.

```text
range(3)             True     False         False     <- 18번: 이터레이터가 아니다
gen()                True      True          True     <- 17번: 제너레이터
  소진 후       gi_frame=False                        <- 17번의 상태 전이
gen  expr  getsizeof : 200                            <- 15번: 메모리
```

**왜 그런가**

| 주제 | 어디까지 | 이 주제는 어디부터 |
|---|---|---|
| [15번](../15-generator-expressions-lazy-eval/2-summary.md) 제너레이터 표현식 | **괄호 하나가 메모리에서 무엇을 바꾸나** · 평가 시점 · 물질화 판단 | 그 객체가 **지켜야 하는 계약**부터 |
| [17번](../17-generators-yield/2-summary.md) 제너레이터 함수 | `yield`·프레임·상태 이름·`send`·`close`·`yield from` — **제너레이터 고유의 전부** | **제너레이터가 아닌 것**(리스트·`map`·`__getitem__` 객체)까지 덮는 계약부터 |
| [18번](../18-loop-control-and-else/2-summary.md) 반복 제어 | `for`/`while`·`else`·`break` 의 **흐름**, `range`·`enumerate`·`zip` 의 성질, 순회 중 변경 | 그 `for` 가 **안쪽에서 무엇을 부르는가**부터 |
| [14번](../14-comprehensions/2-summary.md) 컴프리헨션 | 네 가지 형태 · 스코프 · 평가 시점 | 그 문법들이 **얹혀 있는 계약**부터 |

★ **겹치는 것 하나를 골라 보면 경계가 분명해진다** — 「`for` 는 `iter`+`next`+`StopIteration` 이다」는
[17번](../17-generators-yield/2-summary.md)도 쓰고 여기도 쓴다. 다른 점은 **대상**이다:
17번은 **제너레이터가 어떻게 소비되나**를, 여기는 **모든 이터러블이 같은 세 조각으로 소비된다**는 것을 말한다.

## 실행 검증

이 문서와 [2-summary.md](2-summary.md)에 실린 출력은 전부 아래처럼 돌려서 얻었다.

| 무엇을 | 어떻게 | 몇 번 | 어디에 |
|---|---|---|---|
| `iter`/`next`/`StopIteration` 손 재현 | `python3 - <ex.py` · 3.12.3 | 1회 | 1번 답 |
| 열한 개 객체의 세 열 표 | 〃 | 1회 | 2번 답 |
| 이터러블·이터레이터 클래스 + 계약 위반 2종 | 〃 | 1회 | 3번 답 |
| `__getitem__` 대체 경로 | 〃 | 1회 | 4번 답 |
| PEP 479 `RuntimeError` 전문 | 〃 | 1회 | 5번 답 |
| 소진 대 공집합 — `bool`·`iter is`·`next(기본)`·`__length_hint__` | 〃 | 1회 | 6번 답 |
| `gi_frame`·`gi_running`·`gi_suspended` 3단계 | 〃 | 1회 | 6번 답 |
| `gi_suspended` 가 3.11 에도 있나 | `python3.11 -c` | 1회 | 11번 답 |
| `iter(callable, sentinel)` 2종 | `python3 - <ex.py` | 1회 | 8번 답 |
| 금지 사례 3종(`next`·`len`·첨자) | 〃 | 1회 | 2-summary 「문법」 |
| `isinstance(Old(), Iterable)` · 파일의 `iter(f) is f` | `python3 - <<'PY'` | 1회 | 9번 답 · 2-summary 「더 들어가면」 |

**못 돌려 본 것 — 「안 돌려 본 것」과 구분해 적는다**

- ★ **PEP 479 이전 동작**(3.6 이하에서 `list(take_two(iter([1])))` 가 `[1]` 이 되는 것) —
  **이 머신에 3.6 이하가 없다.** 설치 없이는 잴 수 없으므로 **PEP 문서 근거**로만 적었다.
  3.12.3 에는 끄는 스위치가 없어 같은 인터프리터에서 재현할 방법도 없다.

**구현 의존 항목 — 버전이 오르면 다시 돌려야 할 것**

- **타입 이름 전부**(1·8번 답) — `list_iterator`·`callable_iterator`·`iterator`.
- **`gi_*` 속성**(6번 답) — CPython 내성. 다른 구현에 있으리라는 보장이 없다.
- **예외 문구 전부**(3·4·5번 답) — 종류는 명세, 문구는 아니다.
- **`__length_hint__` 값**(6번 답) — 힌트라 정확할 의무가 없다.
- **트레이스백의 두 덩어리 표시**(5번 답) — 체이닝의 표시 방식.
