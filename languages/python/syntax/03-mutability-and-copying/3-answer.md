# python/syntax/03-mutability-and-copying — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> [1-question.md](1-question.md)의 번호와 **1:1**로 대응한다. 질문 11개 = 답 11개.
>
> 이 파일의 모든 출력은 `python3` **3.12.3** 에서 실제로 돌려 나온 것이다. 지어낸 출력은 없다.
> 단 **바이트코드 명령 이름·`frozenset` 의 복사 결과·해시 값은 구현 세부사항**이라 다른 구현·다른 버전에서는 달라질 수 있다(9·10번 답).

## 정답

### 1. 얕은 복사 네 형태는 다른가 (예측)

**출력**

```text
list(x)     False True
x[:]        False True
copy.copy   False True
x.copy()    False True
```

**왜 그런가**

**넷 다 한 글자도 다르지 않다.** 전부 「바구니만 새것, 안쪽은 원본 그대로」다.

```text
  원본 ->+-------+
         | o   o |
         +-|---|-+
           v   v
        [1,2] [3,4]   <- 안쪽 물건은 하나뿐
           ^   ^
  복사 ->+-|---|-+     <- 바구니만 새것 (c is orig -> False)
         | o   o |        칸은 같은 물건을 가리킨다 (c[0] is orig[0] -> True)
         +-------+
```

문서의 정의가 넷 다 같은 것을 가리킨다 —\
*"A shallow copy constructs a new compound object and then (to the extent possible) inserts **references** into it to the objects found in the original."*

그래서 안쪽을 바꾸면 원본이 따라 바뀐다.

```python
c = orig[:]
c[0][0] = 99
print(orig)
```

```text
[[99, 2], [3, 4]]
```

**「더 깊은」 것이 있나 — 없다**

| 형태 | 깊이 | 고르는 이유 |
|---|---|---|
| `x[:]` | 얕음 | 짧다. 시퀀스에만 쓴다 |
| `list(x)` | 얕음 | **타입을 바꿔 담을 때**(튜플 → 리스트) |
| `x.copy()` | 얕음 | 뜻이 가장 분명하다. `list`·`dict`·`set` 에 있다 |
| `copy.copy(x)` | 얕음 | **타입을 모르는 임의 객체**에 쓴다 |

dict 도 마찬가지다 — `dict(d)`·`d.copy()`·`copy.copy(d)`·`{**d}` 가 같다.

**여기서 틀리는 자리**

「`copy.copy` 는 모듈에서 오니까 더 제대로 하겠지」가 틀린다.\
**깊이를 바꾸는 유일한 수단은 `copy.deepcopy` 뿐이다.**

### 2. `+=` 와 `= x + y` 가 갈리는 자리 (예측)

**출력**

```text
[1, 2]
[1]
False
```

**왜 그런가 — 한 줄씩**

- `p += [2]` 뒤의 `q` → `[1, 2]`.\
  리스트의 `+=` 는 `list.__iadd__` 를 부르고, 그것은 **같은 객체를 제자리에서 늘린다.**\
  `q` 도 그 객체를 가리키고 있으니 같이 보인다.
- `p = p + [2]` 뒤의 `q` → `[1]`.\
  `p + [2]` 는 **새 리스트**를 만들고 `p` 라는 이름표만 그리로 옮겼다. `q` 는 옛 객체에 남는다.
- 문자열 `s += "c"` 뒤 `id(s) == before` → `False`.\
  문자열은 불변이라 **고칠 방법이 없다.** 새 문자열을 만드는 수밖에 없다.

```text
리스트 p += [2]                        리스트 p = p + [2]
      +--------+                       +-----+        +--------+
 p -> | [1, 2] |                  q -> | [1] |   p -> | [1, 2] |
 q -> +--------+                       +-----+        +--------+
  같은 상자를 고쳤다                     새 상자로 이름표만 옮겼다
```

`id` 로 재 보면 그대로 드러난다.

```python
a = [1, 2]; before = id(a)
a += [3]
print("a += [3]   같은 객체:", id(a) == before, a)
b = [1, 2]; before = id(b)
b = b + [3]
print("b = b+[3]  같은 객체:", id(b) == before, b)
t = (1,); before = id(t)
t += (2,)
print("튜플 t += (2,)  같은 객체:", id(t) == before, t)
```

```text
a += [3]   같은 객체: True [1, 2, 3]
b = b+[3]  같은 객체: False [1, 2, 3]
튜플 t += (2,)  같은 객체: False (1, 2)
```

**`+=` 의 의미가 타입마다 다른가 — 명세는 하나다**

언어 레퍼런스는 누적 대입을 「**먼저 연산하고, 그 결과를 원래 대상에 다시 대입한다**」로 정의한다.\
타입별로 갈리는 것은 **「먼저 연산하고」 단계에서 제자리 고치기가 가능한가**다.

| 타입 | `__iadd__` 가 있나 | 결과 |
|---|---|---|
| `list` | 있다 — 제자리에서 늘리고 **자기 자신** 반환 | 같은 객체, 공유된 이름에 보인다 |
| `str`·`tuple`·`int` | 없다 — `__add__` 로 떨어진다 | 새 객체, 공유된 이름엔 안 보인다 |

```python
L = [1]
print("L.__iadd__([2]) is L:", L.__iadd__([2]) is L, L)
```

```text
L.__iadd__([2]) is L: True [1, 2]
```

**여기서 틀리는 자리**

문자열·정수로만 시험하면 `+=` 와 `= x + y` 가 **구별이 안 된다.** 둘 다 새 객체를 만들기 때문이다.\
리스트를 공유한 상태에서만 증상이 난다.

### 3. 불변 안의 가변 (예측)

**출력**

```text
([1], '고정')
True
```

**왜 그런가**

언어 레퍼런스가 이 경우를 직접 적어 두었다 —\
*"The value of an immutable container object that contains a reference to a mutable object can change when the latter's value is changed; however the container is still considered immutable, because the collection of objects it contains cannot be changed."*

```text
    t = ([], "고정")
         +---+-------+
    t -> | o | "고정" |   <- 이 "칸 구성" 은 못 바꾼다 (튜플의 약속)
         +-|-+-------+
           v
          [ ]              <- 이 상자의 "내용" 은 바꿀 수 있다 (튜플의 소관 아님)
```

- `t[0].append(1)` 은 **튜플을 건드리지 않았다.** 튜플이 가리키는 리스트를 바꿨을 뿐이다.
- 그래서 `id(t)` 가 그대로다 — **튜플은 아무 일도 안 했다.** 둘째 줄 `True` 가 그 증거다.

**「튜플은 불변」이 보장하는 것 — 정확히 한 가지**

「**어느 객체들을 가리킬지 안 바꾼다**」뿐이다.\
그 객체들이 스스로 변하는 것은 보장 범위 밖이다.

| 말 | 참인가 |
|---|---|
| 튜플의 칸 구성은 안 바뀐다 | ○ (언어 보장) |
| 튜플의 `id` 는 안 바뀐다 | ○ |
| 튜플 안에 보이는 값은 안 바뀐다 | ✗ — 이 문항이 반례다 |
| 튜플은 언제나 해시 가능하다 | ✗ — 8번 답 |

**여기서 틀리는 자리**

```python
CONFIG = ({"debug": False},)
CONFIG[0]["debug"] = True
print(CONFIG)      # ({'debug': True},)
```

「튜플로 감쌌으니 상수다」라고 믿는 코드는 여기서 조용히 무너진다.

### 4. 에러가 났는데 값이 바뀌어 있다 (예측)

**출력**

```text
TypeError: 'tuple' object does not support item assignment
([1, 3], 'x')
TypeError: 'tuple' object does not support item assignment
(1, 'x')
```

★ **오류 메시지는 두 번 똑같은데 결과가 다르다.** 첫 튜플은 **바뀌었고**, 둘째 튜플은 **그대로다.**

**왜 그런가 — `dis` 가 답한다**

```python
import dis
dis.dis(compile("t[0] += [3]", "<aug>", "exec"))
```

```text
  0           0 RESUME                   0

  1           2 LOAD_NAME                0 (t)
              4 LOAD_CONST               0 (0)
              6 COPY                     2
              8 COPY                     2
             10 BINARY_SUBSCR
             14 LOAD_CONST               1 (3)
             16 BUILD_LIST               1
             18 BINARY_OP               13 (+=)
             22 SWAP                     3
             24 SWAP                     2
             26 STORE_SUBSCR
             30 RETURN_CONST             2 (None)
```

세 단계짜리 문장이다.

```text
 단계             명령               무슨 일이 일어나나
 ---------------  -----------------  --------------------------------
 1. 꺼낸다         BINARY_SUBSCR      t[0] -> 그 리스트 객체
 2. 제자리에 더한다  BINARY_OP 13 (+=)  list.__iadd__ 가 그 리스트를
                                      제자리에서 늘린다   <- 여기서 값이 바뀐다
 3. 도로 넣는다     STORE_SUBSCR       t[0] = <그 리스트> 를 시도
                                      튜플이 거부 -> TypeError  <- 여기서 터진다
```

**2단계에서 이미 바뀌었고 3단계에서 터진다.** 되돌리는 절차가 없다.

이것은 명세대로다 — 언어 레퍼런스가 누적 대입을 「**연산한 다음 원래 대상에 다시 대입한다**」로 정의하기 때문이다.\
`STORE_SUBSCR` 이 그 「다시 대입」이고, 튜플이 그것만 거부한다.

**원소가 불변이면 값도 안 바뀐다 — 대비**

```text
가변 원소 ([1], "x")                  불변 원소 (1, "x")
 2단계: 리스트가 제자리에서 늘어난다      2단계: 새 정수 2 가 만들어진다
        (원본이 바뀐다)                        (원본은 그대로)
 3단계: STORE_SUBSCR -> TypeError      3단계: STORE_SUBSCR -> TypeError
 결과: 에러 + 값 변경                   결과: 에러만
```

정수에는 `__iadd__` 가 없어 `__add__` 로 떨어지고, 그건 **새 객체를 만든다.**\
원본 `1` 은 손끝 하나 안 닿았으므로 3단계에서 터져도 남는 자국이 없다.

**에러 없이 같은 일을 하려면 3단계를 안 만든다**

```python
v = ([1], "x")
v[0].extend([3])
print("extend 판:", v, " (에러 없음)")
```

```text
extend 판: ([1, 3], 'x')  (에러 없음)
```

`extend`·`append` 는 **메서드 호출일 뿐**이라 「다시 대입」 단계가 없다.

**여기서 틀리는 자리 — 이 주제 최악의 자리**

```python
try:
    u[0] += [3]
except TypeError:
    pass            # <- 여기서 삼키면
```

**에러도 없고 변경만 남는다.** 로그에도 아무것도 안 남는다.

> **조용한 실패(silent failure)** — 에러 없이 정상처럼 끝나는데 결과만 틀린 것.\
> 예: 여기서는 에러가 나긴 하는데, 그 에러를 잡아 넘기면 「아무 일도 없었다」로 읽히고 값은 이미 바뀌어 있다.

### 5. 깊은 복사와 순환·공유 (예측)

**출력**

```text
True False
True False
```

**왜 그런가 — 한 줄씩**

- `b[2] is b` → `True`.\
  복사본도 **자기 자신을 가리키는 순환**이 됐다. 구조가 그대로 옮겨졌다.
- `b is a` → `False`.\
  원본과는 완전히 갈렸다. 두 순환 구조가 따로 존재한다.
- `dst[0] is dst[1]` → `True`.\
  원본이 **같은 객체를 두 번** 담고 있었으므로 복사본도 그렇다.
- `dst[0] is src[0]` → `False`.\
  그래도 원본과는 갈렸다.

```text
 원본                              깊은 복사본
   a                                 b
   +-----------+                     +-----------+
   | 1, 2, o   |                     | 1, 2, o   |
   +-------|---+                     +-------|---+
      ^    |                            ^    |
      +----+                            +----+
  a 는 자기를 가리킨다               b 도 자기를 가리킨다 (a 가 아니라)
```

**「전부 새로 만든다」와 어떻게 다른가**

문서가 해법을 적는다 — *"keeping a `memo` dictionary of objects already copied during the current copying pass."*

```text
 "전부 새로" 라면                       실제 (memo 를 쓰면)
  src = [shared, shared]                src = [shared, shared]
   -> 복사본 두 벌이 따로 생긴다           -> "이미 복사했다" 를 기억해
   -> dst[0] is dst[1] 이 False             같은 복사본을 재사용
   -> 원본의 구조가 깨진다                -> dst[0] is dst[1] 이 True
                                        -> 원본의 구조가 보존된다
```

- `memo` 가 없으면 순환 구조에서 **무한 루프**에 빠진다. 그게 문서가 적은 첫째 문제다.
- `memo` 가 있으면 무한 루프도 막고, **공유 구조까지 보존**된다. 두 효과가 한 장치에서 나온다.

**한 문장으로**

`deepcopy` 는 「전부 새로 만든다」가 아니라 「**객체 그래프의 모양을 보존하면서 새로 만든다**」이다.

**여기서 틀리는 자리**

「깊게 복사했으니 두 벌로 완전히 쪼개졌겠지」가 틀린다.\
원본이 한 객체를 여러 자리에서 공유했으면 **복사본도 공유한다.** 그것이 올바른 동작이다.

### 6. 복사가 안 되는 것 (예측)

**출력**

```text
Lock: cannot pickle '_thread.lock' object
함수: True
모듈: cannot pickle 'module' object
```

**왜 그런가**

문서의 한 문장에 **서로 다른 결과 셋**이 섞여 있다 —\
*"This module does not copy types like module, method, stack trace, stack frame, file, socket, window, or any similar types. It does 'copy' functions and classes (shallow and deeply), by returning the original object unchanged."*

```text
 ① 에러를 낸다               ② 원본을 그대로 돌려준다        ③ 복사할 게 없다
 lock, file, socket,        함수, 클래스                   int, str, tuple
 module                     ("copy" 에 따옴표가 붙은        (불변이라 새로
 -> TypeError                이유가 이것이다)               만들 이유가 없다)
    cannot pickle ...       -> is 원본 이 True             -> is 원본 이 True
```

세 자원이 전부 같은 모양이다.

```python
import copy, threading, socket
lock = threading.Lock()
try:
    copy.deepcopy(lock)
except TypeError as e:
    print("Lock  -> TypeError:", e)
f = open("ex.py")
try:
    copy.deepcopy(f)
except TypeError as e:
    print("파일  -> TypeError:", e)
f.close()
s = socket.socket()
try:
    copy.deepcopy(s)
except TypeError as e:
    print("소켓  -> TypeError:", e)
s.close()
```

```text
Lock  -> TypeError: cannot pickle '_thread.lock' object
파일  -> TypeError: cannot pickle 'TextIOWrapper' instances
소켓  -> TypeError: cannot pickle 'socket' object
```

**오류 메시지가 힌트다**

전부 `cannot pickle ...` 이다. `copy` 는 `__copy__`/`__deepcopy__` 훅이 없으면 **`pickle` 의 `__reduce_ex__` 경로로 떨어진다.**\
그래서 「직렬화 못 하는 것」과 「복사 못 하는 것」의 목록이 겹친다.

```python
class NoHook:
    def __init__(self): self.data = [1]
n = NoHook()
print("__reduce_ex__ 로 떨어진다:", type(n.__reduce_ex__(4)))
```

```text
__reduce_ex__ 로 떨어진다: <class 'tuple'>
```

**얕은 복사도 안 된다**

```python
lock2 = threading.Lock()
try:
    copy.copy(lock2)
except TypeError as e:
    print("Lock 얕은 복사도 TypeError:", e)
```

```text
Lock 얕은 복사도 TypeError: cannot pickle '_thread.lock' object
```

훅이 없으면 얕은 복사도 같은 경로로 떨어지기 때문이다.

**여기서 배울 것**

**「안 복사한다」는 「조용히 공유한다」가 아니다** — 이 갈래에서는 드물게 **에러로 드러난다.**\
덕분에 「복사한 줄 알았는데 파일 핸들이 공유됐다」는 사고는 안 난다.\
대신 객체 안에 락이 하나 섞이면 **구조 전체가 복사 불가**가 된다.

### 7. 왜 기본이 얕은가 (왜)

**한 문장**

**컨테이너의 칸도 이름표이기 때문이다** — 복사는 「이름표를 새 바구니에 옮겨 담는 일」이고, 이름표를 옮긴다고 물건이 복제되지는 않는다.

```text
01번의 모델                         03번의 귀결
 이름 -> 객체                        리스트의 칸 -> 객체
 대입은 이름표를 붙이는 일             복사는 칸(이름표)을 새 바구니에
                                     옮겨 담는 일
       |                                    |
       v                                    v
 b = a 가 복사가 아니다               c = a[:] 가 "한 겹만" 복사다
```

**세 가지가 따라 나온다**

1. **얕은 것이 기본인 이유** — 파이썬은 객체를 이름표로 다루므로, 「복사」의 가장 자연스러운 뜻이 「참조를 옮겨 담기」다.
2. **깊은 복사가 특별 요청인 이유** — 얼마나 깊이 내려갈지는 언어가 모른다. 순환이 있으면 무한히 내려간다.\
   그래서 `memo` 같은 장치를 갖춘 **별도 모듈**이 필요했다.
3. **불변 원소면 문제가 안 되는 이유** — 물건을 아무도 못 바꾸므로 공유돼도 관찰되지 않는다.\
   그래서 **증상은 언제나 중첩 가변 컨테이너에서만 난다.**

**한 줄 판정기**

「복사했다」고 말할 때마다 「**어디까지?**」를 붙여서 말하라.\
그 한마디가 이 주제의 사고를 전부 막는다.

### 8. 무엇을 dict 키로 쓸 수 있나 (경계)

**출력**

```text
hash(([1], 2)) -> TypeError: unhashable type: 'list'
hash(((1,), 2)) 있음
```

**왜 그런가**

```text
 해시 가능 조건의 사슬

   값이 안 변한다  ->  해시가 안 변한다  ->  dict/set 에 넣을 수 있다
        ^
        |
   튜플은 "자기 칸 구성" 은 안 변하지만
   칸이 가리키는 객체가 변하면 값도 변한다
        -> 그래서 튜플의 해시는 "내용물 전부가 해시 가능할 때만" 계산된다
```

- 튜플의 해시는 **원소들의 해시를 모아** 만든다. 그러니 원소 하나라도 해시 불가면 튜플도 불가다.
- `((1,), 2)` 는 원소가 `(1,)` 과 `2` — 둘 다 불변이고 해시 가능하니 된다.

**오류가 `tuple` 이 아니라 `list` 를 가리키는 것 — 무엇을 뜻하나**

**튜플이 안쪽에게 해시를 물어보다 거기서 터졌다**는 뜻이다.\
즉 **「불변이다」와 「해시 가능하다」가 다른 말**이라는 증거다.

| 말 | 튜플에 대해 |
|---|---|
| 불변이다 | **언제나** 참 — 칸 구성이 안 바뀐다 |
| 해시 가능하다 | **내용에 달렸다** — 안쪽이 전부 해시 가능해야 한다 |

```python
for v in ([1], {1: 2}, {1}):
    try:
        hash(v)
    except TypeError as e:
        print(f"hash({v!r:8}) -> TypeError: {e}")
```

```text
hash([1]     ) -> TypeError: unhashable type: 'list'
hash({1: 2}  ) -> TypeError: unhashable type: 'dict'
hash({1}     ) -> TypeError: unhashable type: 'set'
```

집합에 넣어도 같은 오류다 — **같은 규칙이 dict 키와 set 원소에 함께 적용된다.**

```python
s = set()
try:
    s.add([1])
except TypeError as e:
    print("set.add([1]) -> TypeError:", e)
```

```text
set.add([1]) -> TypeError: unhashable type: 'list'
```

**실무 관용구**

리스트를 키로 쓰고 싶으면 **얼려서 넣는다** — `tuple(lst)` 나 `frozenset(s)`.\
단 **얼린 뒤에 원본이 바뀌어도 키는 안 바뀐다.** 스냅숏을 찍은 것이지 링크가 아니다.

### 9. 불변이면 복사가 자기 자신인가 (경계)

**측정값**

```text
int        copy is 원본: True   deepcopy is 원본: True
str        copy is 원본: True   deepcopy is 원본: True
tuple      copy is 원본: True   deepcopy is 원본: True
frozenset  copy is 원본: True   deepcopy is 원본: False
```

**답: 「관찰」로 적어야 한다**

`frozenset` 하나가 이미 반례다. 넷 중 셋이 같았다고 규칙이 되지 않는다.

```text
 "불변이면 deepcopy 가 자기 자신" 이라는 규칙을 세우면
   int / str / tuple   -> 맞는다   (세 판)
   frozenset           -> 틀린다   (한 판)

 규칙이 아니라 "타입마다 copy 가 어떻게 처리하기로 했나" 의 문제다.
```

- 문서는 **「불변 객체는 자기 자신을 돌려준다」고 적지 않는다.** 적은 것은 함수·클래스에 대해서뿐이다.
- 그러니 그 동작은 **CPython `copy` 구현이 타입별로 정해 둔 것**이고, 버전이 바뀌면 달라질 수 있다.
- ★ 이 갈래가 정확히 여기서 틀린다 — **「세 판에서 같았다」를 보장으로 읽는 것.**

**튜플도 내용에 달렸다 — 같은 종류의 함정**

```python
import copy
t = (1, "a", (2, 3))
print("전부 불변인 튜플 deepcopy is 원본:", copy.deepcopy(t) is t)

u = ([1], [2])
du = copy.deepcopy(u)
cu = copy.copy(u)
print("가변 품은 튜플  copy is 원본:", cu is u)
print("가변 품은 튜플  deepcopy is 원본:", du is u, " / 안쪽 is:", du[0] is u[0])
```

```text
전부 불변인 튜플 deepcopy is 원본: True
가변 품은 튜플  copy is 원본: True
가변 품은 튜플  deepcopy is 원본: False  / 안쪽 is: False
```

```text
 얕은 복사                       깊은 복사
  튜플이면 언제나 자기 자신         내용이 전부 불변 -> 자기 자신
  (바구니를 새로 짜도 의미 없음)     하나라도 가변 -> 새 튜플
```

**그래서 쓸 수 있는 것**

`copy.deepcopy(t) is t` 의 결과가 **「이 튜플이 정말로 얼어 있나」의 판정기**가 된다 — 이것은 써도 되는 관찰이다.\
반대로 **「불변이니 복사가 공짜」라고 코드가 가정하면 안 된다.**

**적는 법**

- ✗ 「불변 객체는 `deepcopy` 해도 같은 객체다.」
- ○ 「`int`·`str`·`tuple` 은 **이 판에서** 같은 객체가 돌아왔고, `frozenset` 은 아니었다. 문서가 보장하는 것은 함수·클래스뿐이다.」

### 10. 세 층 가르기 (경계)

**① 언어 보장** — 레퍼런스가 정한 것.

| 사실 | 근거 |
|---|---|
| 가변성은 **타입이 정한다**. 수·문자열·튜플은 불변, dict·list 는 가변 | 데이터 모델 3.1 |
| 불변 컨테이너가 가변 객체를 가리키면 그 값이 변할 수 있고, **그래도 컨테이너는 불변**이다 | 데이터 모델 3.1 |
| 얕은 복사는 **참조**를, 깊은 복사는 **복사본**을 새 컨테이너에 넣는다 | `copy` 모듈 |
| `deepcopy` 는 `memo` 로 순환·중복 복사를 다룬다 | `copy` 모듈 |
| 모듈·메서드·스택 트레이스·스택 프레임·파일·소켓·윈도 류는 복사하지 않는다 | `copy` 모듈 |
| 함수와 클래스는 얕게도 깊게도 **원본을 그대로 돌려준다** | `copy` 모듈 |
| 누적 대입은 **연산 후 원래 대상에 다시 대입한다** | 언어 레퍼런스 7.2.1 |
| dict 얕은 복사는 `dict.copy()`, 리스트는 전체 슬라이스로 | `copy` 모듈 |

**② CPython 구현 세부사항** — 이 구현이 그럴 뿐이다.

| 사실 | 어떻게 확인했나 |
|---|---|
| `t[0] += [3]` 이 `BINARY_SUBSCR` → `BINARY_OP 13` → `STORE_SUBSCR` 로 컴파일된다 | `dis` 출력 |
| `list.__iadd__` 가 제자리에서 늘리고 **자기 자신**을 돌려준다 | `L.__iadd__([2]) is L` 가 `True` |
| 복사 실패 메시지가 `cannot pickle ...` 이다 | 훅이 없으면 `pickle` 경로로 떨어지는 구현 |
| 정수의 해시가 값 자신이다 | `hash(1000)` 이 `1000` |
| 문자열 해시가 시드로 무작위화된다 | 다섯 판이 전부 달랐다 |

**③ 이 판(3.12.3)의 관찰** — 버전이 오르면 다시 찍어야 한다.

| 관찰 | 어디가 흔들리나 |
|---|---|
| `frozenset` 의 `deepcopy` 가 **다른 객체**를 돌려준다 | 다른 불변 타입은 자기 자신이었다. 타입별 사정이다(9번 답) |
| 문자열 해시가 실행마다 다르다 | `PYTHONHASHSEED` 무작위화. 끄면 고정된다 |
| 문자열 집합 순회 순서가 실행마다 다르다 | 위와 같은 원인 |
| 정수 집합 `{1,2,3,4,5}` 순회가 `[1, 2, 3, 4, 5]` 로 나온다 | **정렬 보장이 아니다.** 크기·삽입 이력이 바뀌면 달라진다 |
| `BINARY_OP 13` 이라는 명령 번호 | 번호·이름은 판마다 바뀐다 |

**여러 번 돌려 갈린 것 — 그 증거**

같은 3.12.3 에서 다섯 번 돌린 결과다.

```python
# python3 -c "print(hash('python'))" 를 다섯 번
```

```text
4305410804426682121
9018109709149324239
-7577092440730756586
8527627890207874063
7548617485361651948
```

```python
# python3 -c "print(list({'a','b','c','d','e'}))" 를 다섯 번
```

```text
['c', 'b', 'd', 'a', 'e']
['c', 'e', 'b', 'a', 'd']
['d', 'b', 'a', 'e', 'c']
['d', 'a', 'e', 'c', 'b']
['e', 'd', 'a', 'b', 'c']
```

정수 쪽은 안 흔들린다.

```python
# python3 -c "print(hash(1000), hash(1.5), hash((1,2)))" 를 다섯 번
```

```text
1000 1152921504606846977 -3550055125485641917
1000 1152921504606846977 -3550055125485641917
1000 1152921504606846977 -3550055125485641917
1000 1152921504606846977 -3550055125485641917
1000 1152921504606846977 -3550055125485641917
```

★ **한 판만 보면 「정수도 문자열도 해시가 정해져 있다」로 오해한다.** 반증이 확증보다 강하다.

**그래서 이렇게 적으면 틀린다**

- ✗ 「`copy.copy` 는 한 단계, `list(x)` 는 껍데기만 복사한다」 → **넷 다 같다.**
- ✗ 「튜플은 불변이므로 안의 값이 안 바뀐다」 → 문서 자신이 반대를 적는다.
- ✗ 「`deepcopy` 는 전부 새로 만든다」 → **그래프 모양을 보존한다.**
- ✗ 「불변 객체는 `deepcopy` 해도 자기 자신이다」 → `frozenset` 이 아니었다.
- ✗ 「`t[0] += [1]` 은 에러니까 아무 일도 안 일어난다」 → **이미 바뀌어 있다.**

### 11. 실무에서 물리는 자리 (연결)

**증상**

```python
DEFAULT = {"retries": 3, "hosts": ["a"]}

def handle(req):
    cfg = DEFAULT.copy()
    cfg["hosts"].append(req)
    return cfg

handle("b"); handle("c")
print(DEFAULT)
```

```text
{'retries': 3, 'hosts': ['a', 'b', 'c']}
```

**진단 — 세 걸음**

```text
 1. cfg is DEFAULT ?        -> False   "복사는 됐다"
 2. cfg["hosts"] is
    DEFAULT["hosts"] ?      -> True    "안쪽은 안 됐다"   <- 원인
 3. retries 는 왜 멀쩡하나?  -> 정수는 불변이라
                               공유돼도 관찰되지 않는다
```

★ 3번이 이 버그가 **늦게 발견되는 이유**다. 스칼라 값만 바꾸는 테스트는 전부 통과한다.

**고치는 선택지 셋 — 비용과 함께**

| 방법 | 코드 | 비용 | 언제 |
|---|---|---|---|
| ① 필요한 깊이만 손으로 | `cfg = {**DEFAULT, "hosts": DEFAULT["hosts"][:]}` | 가장 싸다. **내가 깊이를 알아야 한다** | 구조가 얕고 고정일 때 (대부분) |
| ② 깊은 복사 | `cfg = copy.deepcopy(DEFAULT)` | 그래프 전체를 훑는다. 파일·락이 섞이면 **`TypeError` 로 죽는다** | 구조가 깊고 모를 때 |
| ③ 애초에 불변으로 | `DEFAULT = {"retries": 3, "hosts": ("a",)}` 또는 `dataclass(frozen=True)` | 설계를 바꿔야 한다. **문제 자체가 사라진다** | 새로 짜는 코드 |

**한 문장으로**

세 선택지의 진짜 차이는 「**어디까지 갈라야 하는지를 누가 아느냐**」다.\
①은 내가 알고, ②는 몰라도 되지만 비싸고, ③은 **갈릴 것이 없게 만든다.**

관련 주제로 이어진다 — 가변 객체가 함수 정의에 붙들리는 경우는 [20-mutable-default-args](../20-mutable-default-args/2-summary.md),\
불변 구조체 설계는 [목록의 **36번 주제**](../36-dataclasses/) 「`dataclasses`」 가 정본이다.

---

## 실행 검증

이 파일에 실린 출력은 전부 아래 환경에서 직접 돌려 얻었다.

```text
$ python3 --version
Python 3.12.3
$ python3 -c "import sys; print(sys.implementation.name)"
cpython
```

| 문항 | 무엇을 돌렸나 | 몇 번 |
|---|---|---|
| 1 | 얕은 복사 네 형태(list·dict 각각), 안쪽 변경 후 원본 확인 | 각 1회 |
| 2 | `+=` 대 `= x + y` 를 list·str·tuple 에서, `__iadd__` 의 반환 | 각 1회 |
| 3 | `t[0].append(1)` 전후의 `id(t)` | 1회 |
| 4 | `t[0] += [3]` 가변·불변 두 판, `dis`, `extend` 대안 | 각 1회 |
| 5 | 순환 참조 `deepcopy`, 공유 객체 `deepcopy` | 각 1회 |
| 6 | Lock·파일·소켓·모듈의 `deepcopy`, 함수·클래스의 `deepcopy`, `copy.copy(Lock)` | 각 1회 |
| 8 | `hash` 가능·불가능 7종, 튜플 중첩 두 판, `set.add([1])` | 각 1회 |
| 9 | 불변 4종의 `copy`/`deepcopy`, 튜플 두 판 | 각 1회 |
| 10 | `hash('python')` · `hash(1000)` · 문자열 집합 순회 · 정수 집합 순회 | **각 5·5·5·3회** |
| 11 | `DEFAULT.copy()` 오염 재현 | 1회 |

**여러 번 돌려 갈린 것**

- **문자열 해시는 실행마다 다르다.** 다섯 판이 전부 달랐다(10번 답).
- **문자열 집합의 순회 순서도 실행마다 다르다.** 다섯 판이 전부 달랐다.
- 정수 해시·정수 집합 순회는 세\~다섯 판에서 같았다 — 그래도 **보장이 아니라 관찰**이다.
- `id()` 값은 실행마다 다르다. 근거로 쓴 것은 **같은 줄의 `id` 가 서로 같은지**뿐이다.

**구현 의존 항목 — 버전이 오르면 다시 찍을 것**

| 다시 찍을 것 | 왜 |
|---|---|
| 4번의 `dis` 출력 | 명령 이름·번호는 판마다 바뀐다 |
| 9번의 `frozenset` deepcopy 결과 | 문서가 보장하지 않는다 |
| 6번의 오류 메시지 문구 | `cannot pickle ...` 은 구현 경로의 산물이다 |
| 10번의 해시·순회 출력 전부 | 매 실행 다르다 |

나머지(얕은/깊은 복사의 정의, `memo`, 복사 불가 타입 목록, 누적 대입의 세 단계, 불변 컨테이너 안의 가변)는 **언어·라이브러리 보장**이므로 어떤 구현에서도 같아야 한다.
