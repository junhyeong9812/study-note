# python/syntax/18-loop-control-and-else — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> [1-question.md](1-question.md)의 번호와 **1:1**로 대응한다. 질문 12개 = 답 12개.
>
> 이 파일의 모든 출력은 `python3` **3.12.3** 에서 실제로 돌려 나온 것이다. 지어낸 출력은 없다.
> 던지는 형태는 `python3 - <파일` 로 고정했다 — 실행 중 예외에는 **소스 줄과 캐럿이 없다.**
> ★★ **`dis` 결과는 CPython 3.12.3 의 구현이지 언어 보장이 아니다**(2·11번 답).
> 예외 문구·시간 수치·바이트코드는 판이 바뀌면 달라진다.

## 정답

### 1. 세 번 다 뭔가 찍힌다 — 마지막도 `else` 다

**출력**

```text
python 3.12.3
[1,2,3] 에서 2 :
  찾음: 2
[1,2,3] 에서 9 :
  else 가 돌았다 — 끝까지 못 찾음
빈 리스트에서 9 :
  else 가 돌았다 — 끝까지 못 찾음
```

**왜 그런가**

```text
   for x in xs:                      ┌ break 를 만났나?
       if 조건:                      │
           break          ───────────┘ 그렇다 ──> else 를 건너뛴다
   else:
       못 찾았을 때                    아니다 ──> else 가 돈다
                                      (빈 xs 도 "아니다" 다)
```

문서가 두 문장으로 정확히 규정한다 —
*"When the iterator is exhausted, the suite in the `else` clause, if present, is executed, and the loop terminates."* /
*"A `break` statement executed in the first suite terminates the loop **without executing the `else` clause's suite**."*

★★ **「한 번도 안 돌았으니까」로 설명하면 왜 틀리나** — 그 설명은 **두 번째 호출을 설명하지 못한다.**

| 호출 | 몇 번 돌았나 | `break` 했나 | `else` |
|---|---|---|---|
| `find([1,2,3], 2)` | 2회 | **예** | 안 돈다 |
| `find([1,2,3], 9)` | 3회 | 아니오 | **돈다** |
| `find([], 9)` | 0회 | 아니오 | **돈다** |

- 두 번째는 **세 번이나 돌았는데** `else` 가 돌았다. 「몇 번 돌았나」는 아무 상관이 없다.
- 기준은 **`break` 하나**다. 그래서 `else` 가 아니라 **`nobreak`** 라고 읽어야 맞는다.
- ★ 빈 리스트가 `else` 로 가는 것은 **덤으로 따라오는 결과**이지 규칙이 아니다.
  「비었을 때」와 「다 봤는데 없을 때」를 **갈라야 하면 `else` 로는 못 한다** — 별도 검사가 필요하다.

### 2. `after = 1` 이 두 번 나온다 — `else` 는 정상 종료 경로에만 놓인다

**출력**

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

**왜 그런가**

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

- ★ **`after = 1` 이 두 번 나온다**(20\~22 와 32\~34). 컴파일러가 **루프 뒤 코드를 복제**했다.
  두 경로가 **각자의 꼬리**를 갖는 모양이고, 그래서 `else`(28\~30)는 **한쪽 경로에만** 놓인다.
- ★★ **`break` 는 `else` 를 「건너뛰는」 것이 아니라 「안 보는」 것이다.**
  `POP_JUMP_IF_TRUE` 가 18 로 뛰고, 거기서 곧장 20 으로 흐른다 — **26\~30 근처에 가지도 않는다.**
  「건너뛴다」는 표현은 마치 통과하면서 넘어가는 것처럼 들리지만, 바이트코드에는 **그 자리를 지나는 경로 자체가 없다.**
- ★ **`else` 를 판정하는 명령이 하나도 없다.** 플래그도, 비교도, 조건 점프도 없다.
  `END_FOR` 다음에 그냥 놓여 있어 **정상 종료가 흘러들 뿐**이다.

**층 가르기**

| 본 것 | 어느 층인가 |
|---|---|
| **`break` 가 `else` 를 실행하지 않는다** | ★ **언어 보장** — 8.3 의 문장 그대로 |
| **이터레이터가 소진되면 `else` 가 실행된다** | ★ **언어 보장** — 8.3 |
| `else` 가 `END_FOR` **바로 뒤 오프셋**에 놓인 것 | **CPython 구현** |
| **루프 뒤 코드가 복제**된 것 | **CPython 구현** — 최적화의 결과 |
| 명령 이름(`FOR_ITER`·`END_FOR`·`POP_JUMP_IF_TRUE`·`RETURN_CONST`) | **CPython 구현** — 3.11 에는 다른 이름이 있다 |
| 오프셋 숫자 전부 | **CPython 구현** |

★★ **즉 「무엇이 일어나나」는 명세이고, 「그것이 왜 공짜인가」만 바이트코드가 더해 준다.**
`else` 에 런타임 비용이 없다는 것은 **이 구현의 사실**이지 명세가 약속한 것이 아니다.

### 3. 세 덩어리 — 그리고 `break` 없는 `else` 는 냄새다

**출력**

```text
while ... else  : 조건이 거짓이 되어 끝 -> else 돈다, n = 3
break 로 끝난 while : else 는 안 돌았다, n = 2
  continue 는 else 를 건드리지 않는다 : 0
  continue 는 else 를 건드리지 않는다 : 2
  -> else 돌았다
```

**왜 그런가**

- 첫 덩어리 — `while` 의 `else` 는 **조건이 거짓이 되어 끝났을 때** 돈다. `n` 이 3이 되어 조건이 깨졌다.
- 둘째 덩어리 — `break` 로 나갔으니 `else` 가 **안 돌았다.** `n` 이 2에서 멈춘 것이 그 증거다.
- 셋째 덩어리 — ★ **`continue` 가 `1` 을 건너뛰었는데도 `else` 가 돌았다.**
  `continue` 는 **루프를 나간 것이 아니라 회차를 건너뛴 것**이라 정상 종료 경로가 그대로 살아 있다.

★★ **「`break` 없는 `while ... else`」가 냄새인 이유** — `else` 가 **100% 확률로 돈다.**
조건이 없는 분기는 분기가 아니다. 그런 코드를 보면 둘 중 하나다:

1. `break` 를 쓰려다 빠뜨렸다(버그),
2. `else` 를 `if`/`else` 로 오해하고 「조건이 거짓이면」이라 생각하고 썼다(오독).

★ 어느 쪽이든 **`else` 를 지우고 다음 줄에 그냥 쓰면 동작이 똑같다** — 그것이 판정법이다.

### 4. `c` 를 아예 안 봤다 — 예외가 아니라 결과가 틀린다

**출력**

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

**왜 그런가**

★ **`본 것` 에 `c` 가 없다.** 루프가 `c` 를 **한 번도 못 봤다** — 그러니 지울 기회조차 없었다.

```text
   xs = [a, b, c, d, e]        커서는 정수 하나다

   커서 0 -> a
   커서 1 -> b   ──remove('b')──>  xs = [a, c, d, e]
                                      0  1  2  3
   커서 2 -> ?   원래 자리 2 는 'c' 였는데 지금은 'd' 다
              ^^^ c 를 건너뛴다. 예외 없음
```

- 둘째 덩어리가 그것을 맨손으로 보인다 — `b` 를 지운 뒤 `next` 가 **`c` 가 아니라 `d`** 를 냈다.
  `__length_hint__` 도 3에서 2로 **한 번에** 줄었다(한 칸 소비 + 한 칸 삭제).
- ★ **왜 예외가 아닌가** — 리스트 인덱싱은 **범위만 맞으면 언제나 안전**하다.
  커서가 2를 가리키고 리스트 길이가 4면 **메모리 안전이 안 깨진다.** 그러니 언어가 막을 이유가 없다.
  깨지는 것은 **의미**이지 안전이 아니다.
- 셋째 덩어리는 반대 방향 — 돌면서 붙이면 **끝이 영영 안 온다.**

★★ **`dict` 의 값만 바꾸는 것이 통과하는 이유**

```text
   dict 의 검사 =  "순회 시작 때의 크기" 와 "지금 크기" 를 비교한다

   d["a"] = 99      -> 크기 그대로 2   -> 통과
   d["새"] = 1      -> 크기 3          -> RuntimeError
   del d["a"]       -> 크기 1          -> RuntimeError
```

- 검사가 **크기만** 본다. 값을 바꾸는 것은 **해시 테이블 배치를 안 건드리므로** 안전하고, 실제로 허용된다.
- 크기가 바뀌면 **테이블 재배치(rehash)** 가 일어날 수 있어 **커서가 가리키는 메모리가 무효**가 된다 —
  그래서 dict·set 은 **막아야만 한다.** 리스트는 그럴 위험이 없어 안 막는다.
- ★ **문구가 자료형마다 다르다** — dict 는 소문자 `dictionary`, set 은 **대문자 `Set`**([13번](../13-set-and-frozenset/2-summary.md)).

★ **고치는 법 셋** — 사본을 돌기(`for x in list(xs)`) · 새로 만들기(컴프리헨션) · 뒤에서부터 인덱스.
셋 다 같은 답(`['a','d','e']`)을 낸다. 문서(튜토리얼 4장)가 앞의 둘을 권한다 —
*"it is usually more straight-forward to **loop over a copy of the collection or to create a new collection**."*

### 5. `3` 이 증발했다 — 「ignore」가 아니라 「읽고 버린다」

**출력**

```text
--- zip 이 삼킨 원소 ---
  zip 결과      : [(1, 'a'), (2, 'b')]
  왼쪽에 남은 것 : [4]  <- 3 이 사라졌다
```

**왜 그런가**

```text
   zip(left, "ab")    left = 1, 2, 3, 4  (이터레이터)

   1회: left -> 1, "ab" -> 'a'   => (1, 'a')
   2회: left -> 2, "ab" -> 'b'   => (2, 'b')
   3회: left -> 3   ★ 꺼냈다!    그다음 "ab" 가 끝  => 멈춘다
        ^^^^^^^^^  3 은 결과에도 없고 left 에도 없다
```

★★ **문서의 낱말과 실제가 어긋나는 자리다.**

| 문서의 말 | 실제 |
|---|---|
| *"It will **ignore** the remaining items in the longer iterables"* | **하나는 ignore 가 아니라 consume 된다** |
| *"The **left-to-right** evaluation order of the iterables is guaranteed."* | 그 보장 때문에 **왼쪽을 먼저 꺼내고** 오른쪽이 끝난 걸 나중에 안다 |

- 「무시한다」는 **안 읽는다**로 읽히기 쉽다. 그런데 **읽어 놓고 버린다.**
- 시퀀스(리스트·문자열)를 넘기면 **원본이 그대로 남으니 티가 안 난다.**
  ★ **이터레이터를 넘겼을 때만 증거가 남는다** — 그래서 이 실험은 `iter([1,2,3,4])` 로 던져야 보인다.
- 실무에서 물리는 자리: **파일·제너레이터·`csv.reader` 를 `zip` 으로 묶고** 나중에 나머지를 쓰려 할 때.
  한 줄이 사라져 있고 **에러가 없다.**
- ★ 두 번째 문장(왼쪽에서 오른쪽)이 **원인이자 보장**이다. 순서가 보장되니 「어느 쪽이 삼켜지나」는 예측 가능하다 —
  **마지막에 꺼낸 그 왼쪽 값**이다.

### 6. 한 칸 어긋난다 — 그리고 두 `True` 는 다른 말이다

**출력**

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

**왜 그런가**

★ **`enumerate(xs, 1)` 의 수를 `xs[i]` 에 넣으면 한 칸 어긋난다.**

```text
   xs = ['x', 'y']
   enumerate(xs, 1)  ->  (1, 'x')  (2, 'y')
                          ^         ^
                          xs[1] 은 'y'   xs[2] 는 IndexError
```

- `start` 는 **세는 수**이지 인덱스가 아니다. **원소를 건너뛰지 않는다** — `['x','y']` 가 온전히 둘 다 나왔다.
- 「1번부터 보여 주려고」 `start=1` 을 쓰는 것은 옳고, **그 수로 다시 색인하는 것**이 틀렸다.
  값이 필요하면 **쌍의 두 번째 원소**를 쓰면 된다.

★ **마지막에서 두 번째 줄의 `True` 두 개는 다른 말이다.**

```text
   range(0, 5) == range(0, 5, 1)   ->  True    같은 수열이다 (step 1 이 기본값)
   range(0)    == range(5, 0)      ->  True    ★ 둘 다 "빈 수열" 이라 같다
                                                start·stop 이 전혀 다른데도 같다
```

문서가 그 성질을 적는다 — *"two range objects are considered equal if they represent the **same sequence of values**.
(Note that two range objects that compare equal might have different `start`, `stop` and `step` attributes ...)"*\
★ **`==` 가 속성이 아니라 「만들어 내는 수열」을 본다.** 빈 것끼리는 전부 같다.

★★ **`iter(r) is r` 이 `False` 인 것이 이 표의 결론이다** —
`enumerate` 는 `True`(이터레이터), `range` 는 `False`(시퀀스). **두 줄이 정확히 반대다.**

### 7. 「else」가 조건을 암시한다

**출력** — 오독이 깨지는 자리.

```text
빈 리스트에서 9 :
  else 가 돌았다 — 끝까지 못 찾음
```

**왜 그런가**

- ★ **`if`/`else`·`try`/`else`·`while`/`else` 에서 `else` 는 전부 「앞의 것이 아니면」으로 읽힌다.**
  그래서 `for`/`else` 도 「**루프가 아니면**」 = 「**루프가 안 돌았으면**」으로 읽게 된다.
- 그런데 실제 조건은 **`break` 라는 점프가 안 일어났을 때**다. 「루프가 얼마나 돌았나」와 **아무 상관이 없다.**
- ★ **바꿔 읽는 낱말은 `nobreak`** 다. 이 낱말로 읽으면 세 호출이 전부 한 번에 맞는다.
- ★ 파이썬 설계자 본인이 이 이름 선택을 후회한다고 밝힌 적이 있을 만큼 **알려진 오독**이다.
  팀 코드에서는 **플래그 변수**나 **함수로 빼서 `return` 으로 탈출**하는 쪽이 읽기 쉽다.

★ **판정 한 줄** — 「`break` 가 어디 있나」를 먼저 찾아라. 없으면 그 `else` 는 **아무 일도 안 하는 장식**이다(3번 답).

### 8. 터지는 것과 조용한 것

**출력**

```text
  dict : RuntimeError: dictionary changed size during iteration
  set  : RuntimeError: Set changed size during iteration
  값만 바꾸는 것은 된다 : {'a': 99, 'b': 2}
```

```text
  본 것   : ['a', 'b', 'd', 'e']
  남은 것 : ['a', 'c', 'd', 'e']  <- c 를 못 지웠다
```

**왜 그런가**

| 자료형 | 연산 | 결과 | 왜 |
|---|---|---|---|
| `list` | `remove`·`del`·`pop` | ★ **조용히 건너뛴다** | 커서가 정수. **범위만 맞으면 안전**하다 |
| `list` | `append`·`insert` | ★ **안 끝나거나 같은 것을 다시 본다** | 〃 |
| `dict` | 키 추가·삭제 | `RuntimeError` | 크기가 바뀌면 **재배치**가 일어날 수 있다 |
| `dict` | **값만** 변경 | **통과** | 배치를 안 건드린다. 검사가 **크기만** 본다 |
| `set` | `add`·`remove` | `RuntimeError` | dict 와 같은 구조 |
| `frozenset`·`tuple`·`str` | — | **불가능** | 불변이라 이 문제가 없다 |

★★ **갈리는 기준은 「위험한가」가 아니라 「메모리 안전이 깨지나」다.**

- 리스트는 **연속된 포인터 배열**이라 인덱스 접근이 언제나 안전하다 → **안 막는다.**
- dict·set 은 **해시 테이블**이라 크기가 바뀌면 내부 배치가 통째로 옮겨질 수 있다 → **막아야 한다.**
- ★ **그러므로 「리스트는 괜찮다」로 읽으면 안 된다.** 안전한 것이지 **옳은 것이 아니다.**
  언어가 안 막을 뿐 결과는 틀린다. 문서(튜토리얼 4장)가 **권고로** 막는 이유다.
- ★ 같은 대조를 [12번](../12-dict-and-key-requirements/2-summary.md)·[13번](../13-set-and-frozenset/2-summary.md)이 반대쪽에서 다룬다 —
  그쪽에서는 **터지는 것**이 주제고, 여기서는 **안 터지는 것**이 주제다.

### 9. 셋을 고르는 기준 — 기본값이 가장 위험하다

**출력**

```text
  zip        : [(1, 'a'), (2, 'b')]
  zip_longest: [(1, 'a'), (2, 'b'), (3, '-')]
```

```text
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
ValueError: zip() argument 2 is shorter than argument 1
```

```text
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
ValueError: zip() argument 2 is longer than argument 1
```

**왜 그런가**

| 상황 | 쓰는 것 | 길이가 다르면 |
|---|---|---|
| 길이가 같아야 **맞는** 데이터다(행과 열, 키와 값) | ★ **`zip(..., strict=True)`** | `ValueError` — **몇 번째 인자가 더 짧은지/긴지**까지 |
| 짧은 쪽에 맞추는 것이 **의도**다(앞 N 개만) | 기본 `zip` | 조용히 잘린다 |
| 긴 쪽에 맞추고 빈 칸을 채운다 | `itertools.zip_longest(fillvalue=...)` | 채운다 |

- ★ **`strict` 는 3.10 부터**다(PEP 618). 그 이전에는 **길이 검사 수단이 언어에 없었다** —
  `len()` 을 따로 비교하는 수밖에 없었고, **이터레이터에는 `len` 이 없어** 그마저 안 됐다([16번](../16-iterator-protocol/2-summary.md)).
- ★ **문구가 `shorter`/`longer` 로 갈린다.** 어느 쪽이 길었는지까지 말해 준다 —
  같은 `ValueError` 인데 **원인 방향이 메시지에 들어 있다.**
- **3.11.15 에서도 같은 문구**가 나왔다(대조 확인). ★ **그래도 문구는 보장이 아니다** — 종류(`ValueError`)만 명세다.

★★ **기본값이 「조용히 자르기」인 것이 이 함수의 위험**이다. 문서도 *"it's recommended to use the `strict=True` option"* 이라고
**권한다** — 기본값이 안전한 쪽이 아니라는 뜻이다.

### 10. 「지연되는 것들」로 묶으면 `range` 에서 틀린다

**출력** — 반증하는 한 줄.

```text
  iter(r) is r : False
  두 번 돌아도 : [0, 1, 2, 3, 4] [0, 1, 2, 3, 4]
```

같은 실행의 대조군.

```text
  iter(e) is e : True  <- 이터레이터다
```

**왜 그런가**

```text
   "지연된다" 로 묶으면                실제로 갈리는 축은 이것이다
   range · enumerate · zip · genexp    ┌────────────────────────────┐
                                       │ iter(x) is x 가 True 인가?  │
                                       └────────────────────────────┘
                                          True  -> enumerate·zip·map·genexp
                                          False -> ★ range
```

| 성질 | `range` | `enumerate`·`zip`·`map`·제너레이터 표현식 |
|---|---|---|
| `iter(x) is x` | **`False`** | `True` |
| 두 번 돌 수 있나 | ★ **된다** | 안 된다(두 번째가 빈다) |
| `len(x)` | **된다**(`5`) | `TypeError` |
| 인덱싱·슬라이스 | **된다**(`r[2]`·`r[1:3]`) | `TypeError` |
| 메모리 | **48바이트 고정** | 고정(값을 안 들고 있다) |
| `in` | **정수면 상수 시간** | 앞에서부터 훑고 **소비한다** |

★★ **한 줄 반증** — `r = range(3); print(list(r), list(r))` 가 **둘 다** `[0, 1, 2]` 를 낸다.
같은 것을 `enumerate` 로 하면 두 번째가 `[]` 다.

- ★ **공통점은 「값을 미리 안 만든다」뿐**이다. 거기서 「그럼 한 번만 돌겠네」로 넘어가는 것이 틀린 추론이다.
- `range` 는 **지연된 시퀀스**다 — 만드는 방법을 들고 있지만 **커서는 안 들고 있다.**
  커서는 `iter(r)` 를 부를 때마다 **새로** 생긴다(`range_iterator`).
- ★ 반대로 「`range` 는 리스트 같은 것」으로 외우면 **메모리에서 틀린다** — 10억짜리도 48바이트다.
  「**시퀀스이되 값을 안 들고 있다**」가 정확한 자리다.
- 지연의 값어치와 메모리 증명은 [15번](../15-generator-expressions-lazy-eval/2-summary.md)이, 계약은 [16번](../16-iterator-protocol/2-summary.md)이 정본이다.

### 11. 세 층

**출력** — 층을 가르는 근거로 쓴 것.

```text
python 3.12.3
  dict : RuntimeError: dictionary changed size during iteration
  getsizeof(range(10_000_000)) : 48
```

시간 수치는 세 판을 냈다.

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

**왜 그런가**

**언어 보장**

| 사실 | 근거 |
|---|---|
| 이터레이터가 소진되면 **`else` 가 실행**된다 | 8.3 — *"When the iterator is exhausted, the suite in the `else` clause, if present, is executed"* |
| **`break` 는 `else` 를 실행하지 않고** 루프를 끝낸다 | 8.3 — *"without executing the `else` clause's suite"* |
| 순회 중 컬렉션 변경은 **까다롭다** — 사본을 돌거나 새로 만들라 | 튜토리얼 4장 — ★ **권고이지 금지가 아니다** |
| `zip` 은 **짧은 쪽에서 멈추고 나머지를 무시**한다 · **왼쪽에서 오른쪽** 평가 순서가 보장된다 | `zip` |
| `zip(..., strict=True)` 는 길이가 다르면 **`ValueError`**(3.10+) | `zip` · PEP 618 |
| `range` 는 **`collections.abc.Sequence` ABC 를 구현**한다 | Ranges |
| `range` 는 **크기와 무관하게 같은 (작은) 메모리**를 쓴다 | Ranges |
| `range` 의 `in` 은 **`int` 에 대해 상수 시간** | Ranges(3.2 변경) |
| `range` 의 `==` 는 **같은 수열이면 같다** — 속성이 달라도 | Ranges |

**CPython 구현 세부사항**

| 사실 | 어떻게 확인했나 |
|---|---|
| `else` 가 **`END_FOR` 바로 뒤**에 놓이고 **루프 뒤 코드가 복제**된다 | `dis` |
| 명령 이름·오프셋 전부 | `dis` — 판마다 다르다 |
| 리스트 이터레이터가 **정수 커서**인 것 | 실행 — 지운 뒤 `next` 가 한 칸 건너뛴다 |
| dict·set 의 검사가 **크기만** 보는 것 | 실행 — 값만 바꾸면 통과 |
| `getsizeof(range(10_000_000))` 이 `48` | 실행 — 빌드·비트 폭에 달렸다 |
| `__length_hint__` 값 | 실행 — **힌트**라 보장이 아니다 |
| 예외 **문구** 전부 | 실행 |

**이 판(3.12.3)·이 머신의 관찰**

| 관찰 | 어디가 흔들리나 |
|---|---|
| 바이트코드 오프셋·명령 이름 | **판마다 다르다** |
| `RuntimeError` 문구 — dict 는 `dictionary`, set 은 대문자 `Set` | 종류는 명세, 문구는 아니다 |
| `ValueError: zip() argument 2 is shorter than argument 1` | 3.11.15 에서도 같았다 — **그래도 보장이 아니다** |
| `range` 의 `in` 39\~45 ns | 머신·부하. ★ **재현되는 것은 「크기를 100만 배로 해도 안 변한다」는 성질뿐**이다 |
| `getsizeof(range(...))` 이 `48` | 구현 값 |
| 순회 중 `remove` 의 결과 `['a','c','d','e']` | ★ **결정적이다** — 커서 규칙의 결과라 매번 같다 |

★ **판정 기준 한 줄** — **「무엇이 일어나나」는 명세, 「왜 공짜인가·왜 안 터지나」는 이 구현.**

### 12. 시작조차 못 하는 오류는 둘뿐이다

**출력**

```text
  File "<stdin>", line 2
SyntaxError: 'break' outside loop
```

```text
  File "<stdin>", line 1
SyntaxError: 'continue' not properly in loop
```

**왜 그런가**

```text
   층 1  파서·컴파일러가 읽을 때        SyntaxError
         └ 'break' outside loop        ★ 그 줄이 안 도는 자리에 있어도 프로그램이 시작조차 안 한다
   층 2  실행할 때                      RuntimeError · ValueError · IndexError ...
         └ dict 순회 중 변경            ★ 그 줄에 닿아야 난다
   층 3  아무 일도 안 난다              순회 중 리스트 변경
         └ 결과만 틀린다
```

- 이 주제에서 **층 1 은 `break`·`continue` 를 루프 밖에 쓴 것** 둘뿐이다.
  나머지(`RuntimeError`·`ValueError`)는 전부 **층 2** 이고, 가장 위험한 것은 **층 3**(4번 답)이다.
- ★ **이 두 `SyntaxError` 에는 소스 줄도 캐럿도 안 나온다.**
  같은 `SyntaxError` 인데 [19번](../19-function-argument-rules/2-summary.md)의 `def f(a=1, b)` 류는 **줄과 캐럿이 나온다** —
  **파서가 잡는 것**과 **파서를 통과한 뒤 심볼 테이블 단계에서 잡는 것**이 다르기 때문이다.
  그 갈림을 전수로 다루는 것이 [19번](../19-function-argument-rules/2-summary.md)이다.
- ★★ **층을 아는 것이 디버깅 순서를 정한다** — 층 1 은 **실행 전에** 전부 잡히고, 층 2 는 **그 경로를 타야** 잡히고,
  층 3 은 **테스트가 값을 확인해야만** 잡힌다. 이 주제의 대표 버그(순회 중 리스트 변경)가 하필 층 3 이다.

## 실행 검증

이 문서와 [2-summary.md](2-summary.md)에 실린 출력은 전부 아래처럼 돌려서 얻었다.

| 무엇을 | 어떻게 | 몇 번 | 어디에 |
|---|---|---|---|
| `for ... else` 세 호출 | `python3 - <ex.py` · 3.12.3 | 1회 | 1번 답 |
| `dis` — `for ... else` + `break` | 〃 | 1회 | 2번 답 |
| `while ... else` · `break` · `continue` | 〃 | 1회 | 3번 답 |
| 순회 중 `remove`·커서 관찰·`append`·dict·set | 〃 | 1회 | 4번 답 |
| 고치는 법 3종(사본·새로 만들기·뒤에서부터) | 〃 | 1회 | 2-summary 동작 3 |
| `zip` 이 삼킨 원소 | 〃 | 1회 | 5번 답 |
| `zip(strict=True)` 양방향 | 〃 | 2회(짧은 쪽·긴 쪽) | 9번 답 |
| `zip(strict=True)` 3.11 대조 | `python3.11 -c` | 1회 | 9·11번 답 |
| `enumerate`·`zip`·`range` 성질 | `python3 - <ex.py` | 1회 | 6번 답 |
| `range` 의 `in` 시간 (`timeit` 중앙값, `repeat=11`) | 〃 | **3판** | 11번 답 |
| `break`·`continue` 를 루프 밖에 | 〃 | 2회 | 12번 답 |

**구현 의존 항목 — 버전이 오르면 다시 돌려야 할 것**

- **바이트코드 전부**(2번 답) — 명령 이름·오프셋·복제 여부.
- **예외 문구 전부**(4·9·12번 답) — 종류는 명세, 문구는 아니다.
- **`getsizeof(range(...))` = `48`**(6번 답) — 빌드·비트 폭.
- **`__length_hint__` 값**(4번 답) — 힌트라 보장이 아니다.
- **`range` 의 `in` 시간**(11번 답) — 「크기에 안 변한다」는 성질만 재현된다.
- **`SyntaxError` 에 캐럿이 없는 것**(12번 답) — 진단 표시 방식이라 판마다 바뀔 수 있다.
