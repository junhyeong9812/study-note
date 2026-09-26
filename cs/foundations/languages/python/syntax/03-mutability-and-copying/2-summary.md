# python/syntax/03-mutability-and-copying — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **이 본문은 원고가 아니라 Claude 작성이다**(문법·API 갈래는 원고 없이 공식 문서로 접지한다).
>
> **기준 소스** — 열어서 확인한 것만.
> - [3.1. Objects, values and types](https://docs.python.org/3.12/reference/datamodel.html) — 가변·불변의 정의, 「불변 컨테이너 안의 가변 객체」 단서
> - [`copy` — Shallow and deep copy operations](https://docs.python.org/3.12/library/copy.html) — 얕은/깊은 복사의 정의, `memo`, 복사 안 되는 타입, `__copy__`/`__deepcopy__`
> - [7.2.1. Augmented assignment statements](https://docs.python.org/3.12/reference/simple_stmts.html#augmented-assignment-statements) — `+=` 가 「먼저 계산하고 다시 대입한다」는 규정
>
> **실행 검증** — 이 문서에 실린 출력은 전부 `python3` **3.12.3**(Linux, x86_64)에서 실제로 돌려 나온 것이다. 지어낸 출력은 없다.
> **버전** — 가변·불변 모델과 `copy` 모듈은 Python 3 전체 공통. 바이트코드 명령 이름(`BINARY_OP 13` 등)은 **3.12 의 것**이다.
> **선행** — [목록의 **01번 주제**](../01-object-and-name-binding/) 「객체와 이름 바인딩 모델」. **복사가 왜 얕은지는 바인딩 모델에서 곧바로 따라 나온다.**

## 한눈에 — 쉽게 말하면

**복사는 바구니를 새로 만드는 것이지, 안에 든 물건을 새로 만드는 것이 아니다.**

01번에서 「변수는 이름표」라고 했다. 리스트 안의 칸도 똑같은 **이름표**다.\
그러니 리스트를 복사하면 **바구니만 새것이고, 안의 이름표는 옛 물건에 그대로 붙는다.**

```text
얕은 복사 (기본)                         깊은 복사
 새 바구니 + 옛 이름표                     새 바구니 + 새 물건

  원본 ->+-------+                       원본 ->+-------+
         | o   o |                              | o   o |
         +-|---|-+                              +-|---|-+
           v   v                                  v   v
        [1,2] [3,4]   <- 물건은 하나              [1,2] [3,4]
           ^   ^                                
  복사 ->+-|---|-+                       복사 ->+-------+
         | o   o |                              | o   o |
         +-------+                              +-|---|-+
                                                  v   v
  복사본의 [1,2] 를 바꾸면                       [1,2] [3,4]  <- 새 물건
  원본에서도 바뀐다                              완전히 따로 논다
```

**비유 대응표** — 이 문서는 끝까지 이 대응을 지킨다.

| 비유 | 실체 | 확인하는 법 |
|---|---|---|
| 바구니 | 컨테이너 객체(list·dict·set) | `c is orig` 가 `False` |
| 바구니의 칸 | 원소를 가리키는 참조 | `c[0] is orig[0]` 로 본다 |
| 물건 | 원소 객체 | 이게 공유되면 얕은 복사 |
| 새 물건까지 만들기 | `copy.deepcopy` | `c[0] is orig[0]` 가 `False` |
| 못 옮기는 물건 | 파일·소켓·락 | `deepcopy` 가 `TypeError` 를 낸다 |

**똑같은 구조다** — 실무에서 이게 물리는 자리는 한결같다.\
설정 딕셔너리를 복사해 기본값을 만들었는데 **한 요청이 바꾼 게 다음 요청에 남는 것**,\
테스트 픽스처를 `.copy()` 로 나눠 줬는데 **테스트끼리 서로 오염되는 것.**\
둘 다 「바구니만 새것」이었기 때문이다.

> **가변(mutable)** — 만들어진 뒤에도 자기 값을 바꿀 수 있는 객체. `list`·`dict`·`set`·`bytearray`.\
> 예: `a.append(1)` 뒤에도 `a` 는 **같은 객체**다. `id(a)` 가 안 변한다.

> **불변(immutable)** — 만들어진 뒤 값을 못 바꾸는 객체. `int`·`float`·`str`·`tuple`·`frozenset`·`bytes`.\
> 예: `s += "c"` 는 `s` 를 바꾼 게 아니라 **새 문자열을 만들어 이름표를 옮긴** 것이다.

> **얕은 복사(shallow copy)** — 문서의 정의 그대로, *"constructs a new compound object and then (to the extent possible) inserts **references** into it to the objects found in the original."*\
> 예: 바구니만 새로 짜고 물건은 원본 것을 가리킨다.

> **깊은 복사(deep copy)** — *"constructs a new compound object and then, recursively, inserts **copies** into it of the objects found in the original."*\
> 예: 바구니도 물건도, 물건 안의 물건까지 전부 새로 만든다.

## 이 주제가 답하려는 질문

1. **어디까지 갈라지나** — `list(x)`·`x[:]`·`copy.copy`·`copy.deepcopy` 는 각각 어느 깊이까지 새것인가.
2. **불변이면 안전한가** — `tuple` 은 불변인데 왜 안의 리스트가 바뀌는가.
3. **깊은 복사가 만능인가** — 순환 참조는 어떻게 되고, 아예 복사가 안 되는 것은 무엇인가.

## 동작 방식

> 이 절이 본문이다. 그림을 먼저 두고 그 그림을 문장으로 읽는다.

### 1. 가변과 불변 — `id` 가 답한다

**언제 쓰나** — 「이 연산이 객체를 바꿨나, 새로 만들었나」를 판정할 때.

```text
가변: 내용을 바꾼다                     불변: 새 객체를 만든다
 a = [1, 2]                            s = "ab"
 a += [3]                              s += "c"

      +-----------+                       +------+       +-------+
 a -> | [1, 2, 3] |                  (버려짐)| "ab" | s ->| "abc" |
      +-----------+                       +------+       +-------+
 id(a) 그대로                           id(s) 가 바뀐다
```

```python
a = [1, 2]; before = id(a)
a += [3]
print("a += [3]   같은 객체:", id(a) == before, a)
b = [1, 2]; before = id(b)
b = b + [3]
print("b = b+[3]  같은 객체:", id(b) == before, b)

s = "ab"; before = id(s)
s += "c"
print("문자열 s += 'c' 같은 객체:", id(s) == before, s)
t = (1,); before = id(t)
t += (2,)
print("튜플 t += (2,)  같은 객체:", id(t) == before, t)
```

```text
a += [3]   같은 객체: True [1, 2, 3]
b = b+[3]  같은 객체: False [1, 2, 3]
문자열 s += 'c' 같은 객체: False abc
튜플 t += (2,)  같은 객체: False (1, 2)
```

그림 해설.

- 리스트의 `+=` 는 **같은 객체를 고친다.** `id` 가 그대로다.
- 리스트의 `= x + y` 는 **새 객체를 만든다.** `id` 가 바뀐다.
- 문자열·튜플은 `+=` 라고 써도 새 객체가 된다 — **고칠 방법이 없으므로 만드는 수밖에 없다.**
- 그래서 **같은 `+=` 인데 공유 상태에서 결과가 갈린다.**

```python
p = [1]; q = p
p += [2]
print("p += 뒤 q:", q)
p = [1]; q = p
p = p + [2]
print("p = p+ 뒤 q:", q)
```

```text
p += 뒤 q: [1, 2]
p = p+ 뒤 q: [1]
```

**비용** — `+=` 는 제자리에서 늘리므로 반복문에서 싸다(리스트 기준).\
대신 **공유된 객체를 조용히 바꾼다**는 대가를 치른다.

### 2. 불변은 해시할 수 있고 가변은 못 한다

**언제 쓰나** — dict 키나 set 원소로 쓸 수 있는지 판정할 때.

```text
       불변                            가변
  값이 안 변한다                  값이 언제든 변한다
        |                               |
  해시가 안 변한다                 해시가 변해 버린다
        |                               |
  dict 키 / set 원소 O            dict 키 / set 원소 X
```

```python
for v in (42, "s", (1, 2), frozenset({1})):
    print(f"hash({v!r:14}) 있음")
for v in ([1], {1: 2}, {1}):
    try:
        hash(v)
    except TypeError as e:
        print(f"hash({v!r:8}) -> TypeError: {e}")
```

```text
hash(42            ) 있음
hash('s'           ) 있음
hash((1, 2)        ) 있음
hash(frozenset({1})) 있음
hash([1]     ) -> TypeError: unhashable type: 'list'
hash({1: 2}  ) -> TypeError: unhashable type: 'dict'
hash({1}     ) -> TypeError: unhashable type: 'set'
```

튜플은 **안에 든 것까지** 불변이어야 한다.

```python
try:
    hash(([1], 2))
except TypeError as e:
    print("hash(([1], 2)) -> TypeError:", e)
print("hash(((1,), 2)) 있음")
```

```text
hash(([1], 2)) -> TypeError: unhashable type: 'list'
hash(((1,), 2)) 있음
```

그림 해설.

- 오류 메시지가 `tuple` 이 아니라 **`list`** 를 가리킨다 — 튜플이 안쪽에게 해시를 물어보다 거기서 터진 것이다.
- 즉 **「튜플이 불변이다」와 「튜플이 해시 가능하다」는 다른 말**이다. 뒤엣것은 내용물에 달렸다.
- 값(해시) 자체는 적지 않았다 — **문자열 해시는 실행할 때마다 다르다**(「어디서 틀리나」 (5)).

**비용** — 해시 가능한 키 덕에 dict 조회가 O(1)이다.\
대신 **가변 객체를 키로 못 쓴다** — 그래서 `frozenset`·`tuple` 로 얼려서 넣는 관용구가 생긴다.

### 3. 얕은 복사 네 형태는 전부 같은 일을 한다

**언제 쓰나** — 리스트를 「따로 쓰려고」 복사할 때.

```text
list(x)      x[:]       copy.copy(x)     x.copy()
    \         |              |             /
     +--------+------+-------+------------+
                     v
        전부 "바구니만 새것" — 같은 결과
```

```python
import copy
orig = [[1, 2], [3, 4]]
forms = {
    "list(x)":    list(orig),
    "x[:]":       orig[:],
    "copy.copy":  copy.copy(orig),
    "x.copy()":   orig.copy(),
}
for name, c in forms.items():
    print(f"{name:11} 바깥 is 원본: {c is orig!s:5}  안쪽[0] is 원본[0]: {c[0] is orig[0]}")
```

```text
list(x)     바깥 is 원본: False  안쪽[0] is 원본[0]: True
x[:]        바깥 is 원본: False  안쪽[0] is 원본[0]: True
copy.copy   바깥 is 원본: False  안쪽[0] is 원본[0]: True
x.copy()    바깥 is 원본: False  안쪽[0] is 원본[0]: True
```

그래서 안쪽을 바꾸면 원본이 따라 바뀐다.

```python
c = orig[:]
c[0][0] = 99
print("얕은 복사본의 안쪽을 바꾸면 원본:", orig)
```

```text
얕은 복사본의 안쪽을 바꾸면 원본: [[99, 2], [3, 4]]
```

dict 도 네 형태가 같다.

```python
d = {"k": [1]}
forms = {"dict(x)": dict(d), "x.copy()": d.copy(), "copy.copy": copy.copy(d), "{**x}": {**d}}
for n, c in forms.items():
    print(f"{n:11} 바깥 is: {c is d!s:5}  안쪽 is: {c['k'] is d['k']}")
```

```text
dict(x)     바깥 is: False  안쪽 is: True
x.copy()    바깥 is: False  안쪽 is: True
copy.copy   바깥 is: False  안쪽 is: True
{**x}       바깥 is: False  안쪽 is: True
```

그림 해설.

- 네 형태의 **결과가 한 글자도 다르지 않다.** 고르는 기준은 성능·가독성이지 깊이가 아니다.
- 「`copy.copy` 는 좀 더 깊겠지」가 틀린다. 문서의 정의가 넷 다 같은 일을 가리킨다.
- **원소가 전부 불변이면 얕은 복사로 충분하다.** 문제는 안에 리스트·dict 가 들어 있을 때다.
- 01번의 모델로 읽으면 당연하다 — 바구니의 칸은 **이름표**이고, 복사는 이름표를 옮겨 담은 것뿐이다.

**비용** — 얕은 복사는 원소 개수에 비례한다(O(n)). 원소 내용은 안 훑는다.\
대신 **중첩이 있으면 「따로 쓰려던」 목적을 달성하지 못한다.**

### 4. 불변 안에 가변 — 튜플이 지키는 것과 안 지키는 것

**언제 쓰나** — 「튜플로 만들었으니 안전하다」고 믿을 때.

언어 레퍼런스가 이 경우를 직접 적어 두었다 —\
*"The value of an immutable container object that contains a reference to a mutable object can change when the latter's value is changed; however the container is still considered immutable, because the collection of objects it contains cannot be changed."*

```text
 튜플이 지키는 것                    튜플이 안 지키는 것
 "어떤 상자들을 담을지"                "그 상자 안의 내용"

    t = ([], "고정")
         +---+-------+
    t -> | o | "고정" |   <- 이 칸 구성은 못 바꾼다 (불변)
         +-|-+-------+
           v
          [ ]              <- 이 상자 내용은 바꿀 수 있다 (가변)
```

```python
t = ([], "고정")
print("전:", t)
t[0].append(1)
print("후:", t)
before = id(t)
t[0].append(2)
print("t 자체 id 불변:", id(t) == before, t)
```

```text
전: ([], '고정')
후: ([1], '고정')
t 자체 id 불변: True ([1, 2], '고정')
```

그림 해설.

- 튜플이 지키는 약속은 「**어느 객체들을 가리킬지 안 바꾼다**」뿐이다.
- 가리키는 객체가 스스로 변하는 것은 튜플의 소관이 아니다.
- `id(t)` 가 안 변한 것이 그 증거다 — **튜플은 아무 일도 안 했다.**

**비용** — 튜플은 해시 가능·안전한 키라는 이점이 있다.\
대신 **「튜플이니 불변이다」가 내용물까지 보장하지 않는다.** 정말 얼리려면 안쪽도 불변으로 만들어야 한다.

### 5. 이 주제의 정점 — `t[0] += [1]` 은 에러를 내면서도 값을 바꾼다

**언제 쓰나** — 튜플 안의 리스트에 `+=` 를 써 봤을 때. **에러가 났는데 값이 바뀌어 있다.**

```python
u = ([1], "x")
print("전:", u)
try:
    u[0] += [3]
except TypeError as e:
    print("TypeError:", e)
print("후:", u, "  <- 바뀌었다")
```

```text
전: ([1], 'x')
TypeError: 'tuple' object does not support item assignment
후: ([1, 3], 'x')   <- 바뀌었다
```

**왜 둘 다 일어나나 — `dis` 가 답한다**

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

```text
 단계             명령               무슨 일이 일어나나
 ---------------  -----------------  --------------------------------
 1. 꺼낸다         BINARY_SUBSCR      t[0] -> 그 리스트 객체
 2. 제자리에 더한다  BINARY_OP 13 (+=)  list.__iadd__ 가 그 리스트를
                                      "제자리에서" 늘린다  <- 여기서 값이 바뀐다
 3. 도로 넣는다     STORE_SUBSCR       t[0] = <그 리스트> 를 시도
                                      튜플이 거부 -> TypeError  <- 여기서 터진다
```

**2단계에서 이미 바뀌었고 3단계에서 터진다.** 되돌리는 절차가 없다.

`__iadd__` 가 **자기 자신을 돌려준다**는 것이 2단계의 핵심이다.

```python
L = [1]
print("L.__iadd__([2]) is L:", L.__iadd__([2]) is L, L)
```

```text
L.__iadd__([2]) is L: True [1, 2]
```

**원소가 불변이면 값도 안 바뀐다 — 대비해서 보면 분명하다**

```python
t = (1, "x")
print("전:", t)
try:
    t[0] += 1
except TypeError as e:
    print("TypeError:", e)
print("후:", t, "  <- 하나도 안 바뀌었다")
```

```text
전: (1, 'x')
TypeError: 'tuple' object does not support item assignment
후: (1, 'x')   <- 하나도 안 바뀌었다
```

```text
가변 원소                              불변 원소
 ([1], "x")                           (1, "x")
 2단계: 리스트가 제자리에서 늘어난다      2단계: 새 정수 2 가 만들어진다
        (원본이 바뀐다)                        (원본은 그대로)
 3단계: STORE_SUBSCR -> TypeError      3단계: STORE_SUBSCR -> TypeError
 결과: 에러 + 값 변경                   결과: 에러만
```

그림 해설.

- **오류 메시지가 같고 결과가 다르다.** 메시지만 보면 무슨 일이 있었는지 알 수 없다.
- 에러를 잡아 무시하는 코드(`except TypeError: pass`)가 있으면 **바뀐 채로 조용히 지나간다.**
- 같은 일을 에러 없이 하려면 3단계를 안 만들면 된다.

```python
v = ([1], "x")
v[0].extend([3])
print("extend 판:", v, " (에러 없음)")
```

```text
extend 판: ([1, 3], 'x')  (에러 없음)
```

**비용** — `+=` 는 제자리 연산이라 빠르다.\
대신 **「읽고 → 고치고 → 다시 쓴다」 세 단계**라서, 세 번째 단계가 실패해도 두 번째는 이미 일어나 있다.

### 6. 깊은 복사와 순환 참조 — `memo` 가 하는 일

**언제 쓰나** — 중첩 구조를 정말로 따로 쓰고 싶을 때.

문서가 깊은 복사의 두 문제를 적고, 해법도 적는다 —\
문제는 *"Recursive objects ... may cause a recursive loop"* 과 *"it may copy too much"* 이고,\
해법은 *"keeping a `memo` dictionary of objects already copied during the current copying pass"* 이다.

```text
 순환 참조                           memo 가 하는 일
   a = [1, 2]                        "이 객체는 이미 복사했다"를 기억
   a.append(a)                        -> 두 번째로 만나면 그 복사본을 재사용
                                      -> 무한 루프가 안 생긴다
      +-----------+
 a -> | 1, 2, o   |
      +-------|---+
         ^    |
         +----+
```

```python
import copy
a = [1, 2]
a.append(a)
print("원본:", a)
b = copy.deepcopy(a)
print("깊은 복사:", b)
print("b[2] is b:", b[2] is b, " / b is a:", b is a)
```

```text
원본: [1, 2, [...]]
깊은 복사: [1, 2, [...]]
b[2] is b: True  / b is a: False
```

`memo` 는 **원본의 공유 구조까지 보존한다.**

```python
shared = [0]
src = [shared, shared]
dst = copy.deepcopy(src)
print("원본은 같은 객체 둘:", src[0] is src[1])
print("깊은 복사도 같은 객체 둘:", dst[0] is dst[1])
print("원본과는 분리:", dst[0] is src[0])
```

```text
원본은 같은 객체 둘: True
깊은 복사도 같은 객체 둘: True
원본과는 분리: False
```

그림 해설.

- `b[2] is b` 가 `True` 다 — **복사본도 자기 자신을 가리키는 순환**이 됐다. 구조가 그대로 옮겨졌다.
- `b is a` 는 `False` 다 — 원본과는 완전히 갈렸다.
- 같은 객체를 두 번 담고 있으면 복사본도 「**같은 객체 두 번**」이 된다. 두 벌로 쪼개지지 않는다.
- 즉 `deepcopy` 는 「전부 새로 만든다」가 아니라 「**객체 그래프의 모양을 보존하면서 새로 만든다**」이다.

**비용** — `memo` 표를 들고 객체 그래프 전체를 훑으므로 얕은 복사보다 훨씬 비싸다.\
대신 순환·공유 구조에서 무한 루프도, 잘못된 분리도 안 생긴다.

### 7. 깊은 복사가 안 되는 것 — 파일·소켓·락

**언제 쓰나** — 객체 안에 자원 핸들이 섞여 있을 때.

문서가 목록을 그대로 적는다 —\
*"This module does not copy types like module, method, stack trace, stack frame, file, socket, window, or any similar types."*

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

**★ 「안 복사한다」가 세 가지 다른 결과를 뜻한다.** 문서의 한 문장에 섞여 있다.

```text
 ① 에러를 낸다              ② 원본을 그대로 돌려준다        ③ 애초에 복사할 게 없다
 lock, file, socket,       함수, 클래스                   int, str, tuple
 module                    (문서: "It does 'copy'          (불변이라 새로 만들
 -> TypeError               functions and classes ...      필요가 없다)
                            by returning the original
                            object unchanged")
```

```python
import copy, math
def fn(): pass
class C: pass
print("함수 deepcopy is 원본:", copy.deepcopy(fn) is fn)
print("클래스 deepcopy is 원본:", copy.deepcopy(C) is C)
try:
    copy.deepcopy(math)
except TypeError as e:
    print("모듈 deepcopy -> TypeError:", e)
```

```text
함수 deepcopy is 원본: True
클래스 deepcopy is 원본: True
모듈 deepcopy -> TypeError: cannot pickle 'module' object
```

```python
for obj in (42, "문자열", (1, 2), frozenset({1, 2})):
    sc = copy.copy(obj); dc = copy.deepcopy(obj)
    print(f"{type(obj).__name__:10} copy is 원본: {sc is obj!s:5}  deepcopy is 원본: {dc is obj}")
```

```text
int        copy is 원본: True   deepcopy is 원본: True
str        copy is 원본: True   deepcopy is 원본: True
tuple      copy is 원본: True   deepcopy is 원본: True
frozenset  copy is 원본: True   deepcopy is 원본: False
```

그림 해설.

- `lock`·`file`·`socket`·`module` 은 **에러**다. 「복사 안 됨」이 조용하지 않다 — 다행이다.
- 함수·클래스는 **원본을 그대로 돌려준다.** 에러가 아니라 「복사한 척」이다.
- 불변 객체는 `deepcopy` 도 **자기 자신**을 돌려준다 — 새로 만들 이유가 없기 때문이다.
- ★ 그런데 `frozenset` 만 `False` 다. 불변인데도 새 객체가 나온다 — **「불변이면 자기 자신」은 규칙이 아니라 타입별 사정**이라는 뜻이다. 이 판의 관찰로 적는다.
- 오류 메시지가 전부 `cannot pickle ...` 인 것이 힌트다 — **`copy` 는 훅이 없으면 `pickle` 의 `__reduce_ex__` 로 떨어진다.**

**비용** — 자원 핸들이 섞인 객체는 깊은 복사 자체가 불가능하다.\
대신 그 사실이 **에러로 드러나므로** 「복사했다고 믿었는데 핸들이 공유됐다」는 사고는 안 난다.

### 8. 튜플의 깊은 복사는 내용에 달렸다

**언제 쓰나** — 「불변이니 복사가 필요 없다」고 넘길 때.

```text
전부 불변인 튜플                     가변을 품은 튜플
 t = (1, "a", (2, 3))                t = ([1], [2])
 deepcopy(t) is t  ->  True          deepcopy(t) is t  ->  False
 (새로 만들 이유가 없다)               (안쪽을 복사해야 하니
                                      튜플도 새로 만든다)
```

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

그림 해설.

- **얕은 복사는 어느 쪽이든 자기 자신**이다 — 튜플은 바구니를 새로 짜도 의미가 없으니 그냥 돌려준다.
- **깊은 복사는 내용에 달렸다.** 안쪽이 전부 불변이면 자기 자신, 하나라도 가변이면 새 튜플.
- 즉 `deepcopy(t) is t` 의 결과가 **「이 튜플이 정말로 얼어 있나」의 판정기**가 된다.

**비용** — 불변 객체의 깊은 복사는 공짜다(자기 자신 반환).\
대신 **가변을 품은 순간 값이 아니라 구조를 훑는 비용**이 생긴다.

## 문법 — 형태와 규칙

```python
import copy

c = x[:]                  # 시퀀스 얕은 복사 (list·tuple·str)
c = list(x)               # 얕은 복사 + 타입 고정
c = x.copy()              # list·dict·set 의 메서드
c = {**d}                 # dict 얕은 복사
c = copy.copy(x)          # 임의 객체 얕은 복사
c = copy.deepcopy(x)      # 임의 객체 깊은 복사
c = copy.deepcopy(x, memo)  # memo 를 직접 넘길 수도 있다

class Node:
    def __copy__(self): ...          # 얕은 복사를 가로챈다
    def __deepcopy__(self, memo): ...  # 깊은 복사를 가로챈다 (memo 를 받는다)
```

규칙은 다섯이다.

1. **얕은 복사 네 형태는 결과가 같다.** `list(x)`·`x[:]`·`copy.copy(x)`·`x.copy()`.\
   고르는 기준은 깊이가 아니라 가독성이다.
2. **불변 객체는 복사해도 자기 자신이 돌아오기도 한다.** `int`·`str`·`tuple` 이 그렇고 `frozenset` 은 `deepcopy` 에서 아니었다 — **규칙이 아니라 타입별 사정**이다.
3. **`deepcopy` 는 `memo` 로 순환·공유를 다룬다.** 「전부 새로」가 아니라 「그래프 모양을 보존하며 새로」다.
4. **파일·소켓·락·모듈은 복사 자체가 안 된다.** `TypeError: cannot pickle ...` 이 난다.
5. **`__copy__`/`__deepcopy__` 훅으로 가로챌 수 있다.** 훅이 없으면 `pickle` 의 `__reduce_ex__` 경로로 떨어진다. 여기서는 **존재만** 알아 둔다.

```python
class Hooked:
    def __copy__(self):
        print("  __copy__ 불림"); return "얕은 결과"
    def __deepcopy__(self, memo):
        print("  __deepcopy__ 불림"); return "깊은 결과"

import copy
h = Hooked()
print(copy.copy(h))
print(copy.deepcopy(h))
```

```text
  __copy__ 불림
얕은 결과
  __deepcopy__ 불림
깊은 결과
```

## 어디서 틀리나

### (1) `.copy()` 로 설정을 나눠 줬는데 서로 오염된다

```python
DEFAULT = {"retries": 3, "hosts": ["a"]}
cfg = DEFAULT.copy()
cfg["hosts"].append("b")
print(DEFAULT)      # {'retries': 3, 'hosts': ['a', 'b']}
```

`retries` 를 바꾸는 테스트는 통과한다 — **정수는 불변이라 공유돼도 티가 안 나기 때문이다.**\
증상은 **중첩 컨테이너가 있을 때만** 난다. 그래서 늦게 발견된다.

### (2) 「튜플로 감쌌으니 안전하다」

```python
CONFIG = ({"debug": False},)
CONFIG[0]["debug"] = True
print(CONFIG)       # ({'debug': True},)
```

튜플은 **칸 구성**만 지킨다. 내용물은 소관이 아니다.

### (3) `+=` 가 에러를 내고도 값을 바꾼 것을 못 본다

```python
u = ([1], "x")
try:
    u[0] += [3]
except TypeError:
    pass            # <- 여기서 삼키면
print(u)            # ([1, 3], 'x')   이미 바뀌어 있다
```

`except ...: pass` 로 넘기면 **에러도 없고 변경만 남는다.** 이 주제 최악의 자리다.

### (4) `deepcopy` 를 기본값처럼 쓴다

`deepcopy` 는 객체 그래프 전체를 훑는다. 큰 구조에서는 눈에 띄게 느리고,\
안에 파일·락이 섞이면 **`TypeError` 로 죽는다.**\
필요한 깊이만 손으로 복사하는 쪽이 나은 경우가 많다 — `{k: v[:] for k, v in d.items()}` 처럼.

### (5) 해시 값을 「같은 버전이면 같다」로 믿는다

**문자열 해시는 실행할 때마다 다르다.** 같은 3.12.3 에서 다섯 번 돌린 것이다.

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

정수는 안 흔들린다.

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

그래서 **문자열 집합의 순회 순서도 실행마다 바뀐다.**

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

정수 집합은 안 바뀐다(정수의 해시가 값 자신이라서다).

```python
# python3 -c "print(list({1,2,3,4,5}))" 를 세 번
```

```text
[1, 2, 3, 4, 5]
[1, 2, 3, 4, 5]
[1, 2, 3, 4, 5]
```

**세 판만 비교하면 「정수 집합은 정렬돼 나온다」로 오해한다** — 그것도 보장이 아니라 관찰이다.\
★ 해시가 걸린 주제에서는 **같은 버전에서 여러 번** 돌려야 한다. 반증이 확증보다 강하다.

## 구현 세부사항 대 언어 보장

세 층으로 가른다.

| 층 | 무엇인가 | 어떻게 확인했나 |
|---|---|---|
| **언어 보장** | 언어 레퍼런스·라이브러리 레퍼런스가 정한 것 | 공식 문서 문장을 열어서 인용 |
| **CPython 구현** | 이 구현이 그렇게 하는 것 | 실행 + `dis` 로 확인 |
| **이 판의 관찰** | 3.12.3 에서 그랬을 뿐 | 「관찰」로 명기 |

### 언어 보장

| 사실 | 근거 |
|---|---|
| 객체의 가변성은 **타입이 정한다**. 수·문자열·튜플은 불변, dict·list 는 가변 | 데이터 모델 3.1 |
| 불변 컨테이너가 가변 객체를 가리키면 **그 값이 변할 수 있다.** 그래도 컨테이너는 여전히 불변이다 | 데이터 모델 3.1 |
| 얕은 복사는 새 컨테이너에 **참조**를 넣고, 깊은 복사는 **복사본**을 넣는다 | `copy` 모듈 |
| `deepcopy` 는 `memo` 로 순환·중복 복사를 다룬다 | `copy` 모듈 |
| `copy` 는 모듈·메서드·스택 트레이스·스택 프레임·파일·소켓·윈도 류를 복사하지 않는다 | `copy` 모듈 |
| 함수와 클래스는 얕게도 깊게도 **원본을 그대로 돌려준다** | `copy` 모듈 |
| dict 의 얕은 복사는 `dict.copy()`, 리스트는 전체 슬라이스로 만든다 | `copy` 모듈 |
| 클래스는 `__copy__`/`__deepcopy__` 로 복사를 재정의할 수 있다 | `copy` 모듈 |
| 누적 대입(`x += y`)은 **먼저 연산하고 그 결과를 원래 대상에 다시 대입한다** | 언어 레퍼런스 7.2.1 |

★ 마지막 줄이 5번 절의 근거다. **「다시 대입한다」가 명세에 있으므로, 튜플이 거부하는 것도 명세대로**다.

### CPython 구현 세부사항

| 사실 | 어떻게 확인했나 |
|---|---|
| `t[0] += [3]` 이 `BINARY_SUBSCR` → `BINARY_OP 13` → `STORE_SUBSCR` 로 컴파일된다 | `dis` 출력 |
| `list.__iadd__` 가 제자리에서 늘리고 **자기 자신을 돌려준다** | `L.__iadd__([2]) is L` 가 `True` |
| 복사 실패 메시지가 `cannot pickle ...` 이다 | 훅이 없으면 `pickle` 경로로 떨어지는 구현 |
| 정수의 해시가 값 자신이라 정수 집합의 순회가 정렬처럼 보인다 | `hash(1000)` 이 `1000` |

### 이 판(3.12.3)의 관찰

| 관찰 | 어디가 흔들리나 |
|---|---|
| `frozenset` 의 `deepcopy` 가 **원본과 다른 객체**를 돌려준다 | 다른 불변 타입은 자기 자신이었다. 타입별 사정이다 |
| 문자열 해시가 **실행마다 다르다** | `PYTHONHASHSEED` 무작위화. 끄면 고정된다 |
| 문자열 집합 순회 순서가 실행마다 다르다 | 위와 같은 원인 |
| 정수 집합 `{1,2,3,4,5}` 의 순회가 `[1, 2, 3, 4, 5]` 로 나온다 | **정렬 보장이 아니다.** 크기·삽입 이력이 바뀌면 달라진다 |
| `BINARY_OP 13 (+=)` 이라는 명령 번호 | 번호·이름은 판마다 바뀐다 |

### 그래서 이렇게 적으면 틀린다

- ✗ 「`copy.copy` 는 한 단계, `list(x)` 는 껍데기만 복사한다」\
  → **넷 다 같다.** 실측에서 한 글자도 다르지 않았다.
- ✗ 「튜플은 불변이므로 안의 값이 안 바뀐다」\
  → 문서 자신이 반대를 적는다. 튜플이 지키는 것은 **칸 구성**뿐이다.
- ✗ 「`deepcopy` 는 전부 새로 만든다」\
  → **그래프 모양을 보존한다.** 원본이 같은 객체를 두 번 담았으면 복사본도 그렇다.
- ✗ 「불변 객체는 `deepcopy` 해도 자기 자신이다」\
  → `frozenset` 이 아니었다. **관찰을 규칙으로 승격하지 마라.**
- ✗ 「`t[0] += [1]` 은 에러니까 아무 일도 안 일어난다」\
  → **이미 바뀌어 있다.** 에러는 세 번째 단계에서 났다.

**판정 기준 한 줄**: **「복사했다」고 말할 때마다 「어디까지?」를 붙여서 말하라.** 그 한마디가 이 주제의 사고를 전부 막는다.

## 언제 쓰고 언제 안 쓰나

| 쓰는 것 | 상황 |
|---|---|
| 얕은 복사(`x[:]`·`.copy()`) | 원소가 **전부 불변**일 때 — 숫자·문자열·튜플 목록 |
| 얕은 복사 | 「바구니만 갈라 놓으면 되는」 경우 — 정렬한 판을 따로 들고 싶을 때 |
| `copy.deepcopy` | 중첩 구조를 정말 따로 써야 하고, **안에 자원 핸들이 없을 때** |
| 손으로 한 겹 복사 | `{k: v[:] for k, v in d.items()}` — 깊이를 내가 아는 경우. 가장 빠르고 안전하다 |
| 아예 불변으로 설계 | `tuple`·`frozenset`·`dataclass(frozen=True)` — 복사 문제가 사라진다 |
| `__deepcopy__` 훅 | 자원 핸들을 가진 클래스를 복사 가능하게 만들 때 |

**안 쓰는 자리**는 둘이다.\
**튜플 원소에 `+=` 를 쓰지 마라** — 에러를 내면서 값을 바꾼다. `extend`/`append` 를 쓴다.\
**`deepcopy` 를 습관으로 쓰지 마라** — 비싸고, 자원 핸들이 섞이면 죽는다.

## 핵심 문장

- 복사는 **바구니를 새로 만드는 일**이고, 안의 칸은 01번의 이름표 그대로다. 그래서 기본이 얕다.
- 얕은 복사 네 형태(`list(x)`·`x[:]`·`copy.copy`·`x.copy()`)는 **결과가 같다.** 깊이로 고르는 것이 아니다.
- 튜플이 지키는 약속은 「**어느 객체를 가리킬지**」뿐이다. 그 객체가 스스로 변하는 것은 막지 않는다.
- `t[0] += [1]` 은 **에러를 내면서 값을 바꾼다.** 「꺼내 → 제자리에서 고쳐 → 도로 넣는다」의 세 번째 단계에서만 터지기 때문이다.
- `deepcopy` 는 「전부 새로」가 아니라 「**그래프 모양을 보존하며 새로**」다. 순환도 공유도 그대로 옮긴다.
- 파일·소켓·락·모듈은 **복사 자체가 안 된다.** 함수·클래스는 **원본을 그대로 돌려준다.** 「안 복사한다」가 두 가지 뜻이다.

## 관련 자료

- 목록: [python/syntax 주제 목록](../README.md) — 이 주제는 **03번**
- 선행: [목록의 **01번 주제**](../01-object-and-name-binding/) 「객체와 이름 바인딩 모델」 — **이 주제 전체가 그 모델의 따름정리**다. 바구니의 칸이 이름표라는 것을 모르면 「왜 얕은가」에 답할 수 없다.
- 이어지는 곳: [20-mutable-default-args](../20-mutable-default-args/2-summary.md) — 가변 객체가 **함수 정의에 붙들려** 호출 사이에 살아남는 경우. **그 정본은 그쪽**이다.
- 이어지는 곳: [02-is-vs-eq-interning](../02-is-vs-eq-interning/2-summary.md) — 「같은 객체인가」를 묻는 법. 이 문서의 `is` 판정이 전부 그쪽 규칙을 쓴다.
- 이어지는 곳: [목록의 **11번 주제**](../11-tuple-and-unpacking/) 「tuple 과 언패킹」 — 튜플 안의 가변 원소를 튜플 쪽에서 다시 본다.
- 이어지는 곳: [목록의 **12번 주제**](../12-dict-and-key-requirements/) 「dict 와 키 요건」 · [목록의 **13번 주제**](../13-set-and-frozenset/) 「set 과 frozenset」 — 여기서 본 해시 요건이 그쪽의 본문이다.
- 이어지는 곳: [목록의 **36번 주제**](../36-dataclasses/) 「`dataclasses`」 — `frozen=True` 와 `default_factory` 로 이 문제를 설계 단계에서 없애는 법.
- 기존 노트: [`cs/foundations/variables-and-memory/`](../../../../variables-and-memory/README.md) — 「2. 얕은 복사와 깊은 복사」 절이 같은 주제를 다룬다.\
  **경계**: 그쪽은 「무엇이 얕고 무엇이 깊은가」의 소개까지, 여기는 「**네 형태가 같은지 재 보고, 불변 안의 가변과 `+=` 의 세 단계를 `dis` 로 가르는 데**」부터다.
- 연혁은 여기가 아니다: [`history/python/`](../../../../../../history/python/)
- 공식 문서: [`copy`](https://docs.python.org/3.12/library/copy.html) · [3.1. Objects, values and types](https://docs.python.org/3.12/reference/datamodel.html) · [7.2.1. Augmented assignment statements](https://docs.python.org/3.12/reference/simple_stmts.html#augmented-assignment-statements)

## 용어 풀이

- **가변(mutable)**: 만들어진 뒤에도 자기 값을 바꿀 수 있는 객체.\
  `list`·`dict`·`set`·`bytearray`. 바꿔도 `id()` 가 그대로다.
- **불변(immutable)**: 만들어진 뒤 값을 못 바꾸는 객체.\
  `int`·`float`·`str`·`tuple`·`frozenset`·`bytes`. 「바꾸면」 새 객체가 생긴다.
- **얕은 복사(shallow copy)**: 새 컨테이너를 만들고 그 안에 **원본이 가리키던 객체들의 참조**를 넣는 것.\
  바구니만 새것이다.
- **깊은 복사(deep copy)**: 새 컨테이너를 만들고 그 안에 **원본 객체들의 복사본**을 재귀적으로 넣는 것.
- **`memo`**: `deepcopy` 가 「이미 복사한 객체」를 기억하는 딕셔너리.\
  순환 참조에서 무한 루프를 막고, 원본의 공유 구조를 복사본에서도 보존한다.
- **순환 참조(recursive object)**: 자기 자신을 직접·간접으로 가리키는 객체.\
  `a = [1]; a.append(a)` 가 가장 작은 예다.
- **누적 대입(augmented assignment)**: `x += y` 류.\
  명세상 **연산한 결과를 원래 대상에 다시 대입**하는 것이라 「읽고 → 고치고 → 다시 쓴다」 세 단계다.
- **`__iadd__`**: `+=` 를 만나면 불리는 메서드.\
  리스트의 것은 제자리에서 늘린 다음 **자기 자신**을 돌려준다.
- **해시 가능(hashable)**: `hash()` 를 부를 수 있고 그 값이 수명 동안 변하지 않는 것.\
  dict 키·set 원소가 되려면 필요하다. 가변 객체는 해당하지 않는다.
- **`__reduce_ex__`**: `pickle` 이 객체를 분해할 때 쓰는 프로토콜 메서드.\
  `copy` 는 `__copy__`/`__deepcopy__` 훅이 없으면 이 경로로 떨어진다. 그래서 오류 메시지가 `cannot pickle ...` 이다.
- **`__copy__` / `__deepcopy__`**: 클래스가 자기 복사 방식을 직접 정의하는 훅.\
  `__deepcopy__` 는 `memo` 를 인자로 받는다.
- **`PYTHONHASHSEED`**: 문자열 해시의 무작위 시드를 정하는 환경 변수.\
  기본이 무작위라 문자열 해시와 문자열 집합의 순회 순서가 **실행마다 다르다.**

## 더 들어가면

- **`copy` 는 클래스의 `__slots__`·`__getstate__`/`__setstate__` 도 존중한다.** 직렬화(`pickle`)와 규칙을 공유하기 때문이다.
- **얕은 복사조차 안 되는 것이 있다.** `threading.Lock` 은 `copy.copy` 에서도 같은 `TypeError` 가 났다 — 훅이 없으면 얕은 복사도 `__reduce_ex__` 로 떨어지기 때문이다.
- **불변 객체를 만들어 두는 쪽이 복사 문제를 설계 단계에서 없앤다.** `tuple`·`frozenset`·`dataclass(frozen=True)`·`types.MappingProxyType` 이 그 수단이다([목록의 **36번 주제**](../36-dataclasses/)).
