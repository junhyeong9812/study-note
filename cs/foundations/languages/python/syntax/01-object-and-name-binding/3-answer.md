# python/syntax/01-object-and-name-binding — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> [1-question.md](1-question.md)의 번호와 **1:1**로 대응한다. 질문 11개 = 답 11개.
>
> 이 파일의 모든 출력은 `python3` **3.12.3** 에서 실제로 돌려 나온 것이다. 지어낸 출력은 없다.
> 단 **`id()` 값·바이트코드 명령 이름·인터닝 결과는 구현 세부사항**이라 다른 구현·다른 버전에서는 달라질 수 있다(10번 답).

## 정답

### 1. 대입이 복사하는 것 (예측)

**출력**

```text
[1, 2, 3]
True
```

**왜 그런가**

- `b = a` 는 리스트를 복사하지 않는다. **같은 객체에 이름표를 하나 더 붙일 뿐이다.**
- 그래서 `b.append(3)` 이 바꾼 그 객체를 `a` 도 가리키고 있어 `print(a)` 에 보인다.
- `a is b` 가 `True` 인 것이 「같은 객체」라는 말의 정의다.

```text
 전 상태                          후 상태 (b.append(3))
      +--------+                       +-----------+
 a -> | [1, 2] |                  a -> | [1, 2, 3] |
 b -> +--------+                  b -> +-----------+
   이름표 둘, 상자 하나
```

**한 문장으로**

`b = a` 는 「**a 가 가리키던 객체에 b 라는 이름도 묶어라**」다. 언어 레퍼런스의 말로는 *바인딩*이다.

**여기서 틀리는 자리**

`b = a` 를 복사로 읽으면, 나중에 `b` 를 정렬하거나 `pop` 했을 때 **원본까지 바뀐 이유를 못 찾는다.**\
따로 쓰려면 복사를 따로 요청해야 한다([목록의 **03번 주제**](../03-mutability-and-copying/)).

### 2. 한 객체인가 두 객체인가 (예측)

**출력**

```text
True
[1] [1]
False
[1] []
```

**왜 그런가**

- `a = b = []` 은 **빈 리스트를 한 번만** 만들고 이름표 둘을 같이 붙인다 → `a is b` 가 `True`, 한쪽 변경이 양쪽에 보인다.
- `c, d = [], []` 은 **두 번** 만든다 → `c is d` 가 `False`, 각자 따로 움직인다.

```text
a = b = []                            c, d = [], []
      +----+                          +----+      +----+
 a -> | [] |                     c -> | [] | d -> | [] |
 b -> +----+                          +----+      +----+
```

**`dis` 로 보이는 법 — `BUILD_LIST` 개수를 센다**

```python
import dis
dis.dis(compile("a = b = []", "<chain>", "exec"))
```

```text
  0           0 RESUME                   0

  1           2 BUILD_LIST               0
              4 COPY                     1
              6 STORE_NAME               0 (a)
              8 STORE_NAME               1 (b)
             10 RETURN_CONST             0 (None)
```

```python
dis.dis(compile("c, d = [], []", "<tuple>", "exec"))
```

```text
  0           0 RESUME                   0

  1           2 BUILD_LIST               0
              4 BUILD_LIST               0
              6 SWAP                     2
              8 STORE_NAME               0 (c)
             10 STORE_NAME               1 (d)
             12 RETURN_CONST             0 (None)
```

- 왼쪽은 `BUILD_LIST` 가 **한 번**, 오른쪽은 **두 번**. 객체 개수가 거기서 정해진다.
- `COPY 1` 은 스택 맨 위를 한 벌 더 쌓는 명령 — **같은 객체를 두 번 저장**하려고 쓴다.
- 이것이 「지어낼 수 없는 근거」다. 그림은 이 출력을 읽은 것일 뿐이다.

**여기서 틀리는 자리**

`a = b = 0` 으로 시험하면 증상이 **안 난다.** 불변 객체는 공유돼도 티가 안 나기 때문이다.\
가변 객체로 바꾸는 순간 조용히 틀린다.

### 3. 왼쪽 대상의 처리 순서 (예측)

**출력**

```text
1 [0, 5]
```

**왜 그런가**

대입문은 **① 오른쪽을 먼저 전부 평가하고 ② 왼쪽 대상을 왼쪽부터 순서대로** 묶는다.

```text
i, L[i] = 1, 5

 단계 0: 오른쪽 (1, 5) 를 먼저 만든다
 단계 1: i = 1          <- i 가 0 에서 1 로 바뀐다
 단계 2: L[i] = 5       <- 이 시점의 i 는 이미 1 이다
                           그래서 L[1] = 5
 결과: i=1, L=[0, 5]
```

- 「`L[i]` 의 `i` 는 문장 시작 때의 값이겠지」가 틀린다. **왼쪽 대상은 평가가 아니라 순차 저장이다.**
- 이 규칙이 스왑(`x, y = y, x`)이 되는 이유이기도 하다 — 오른쪽 `(y, x)` 를 먼저 만들어 두고 나눠 준다.

```python
import dis
dis.dis(compile("x, y = y, x", "<swap>", "exec"))
```

```text
  0           0 RESUME                   0

  1           2 LOAD_NAME                0 (y)
              4 LOAD_NAME                1 (x)
              6 SWAP                     2
              8 STORE_NAME               1 (x)
             10 STORE_NAME               0 (y)
             12 RETURN_CONST             0 (None)
```

`LOAD` 둘이 먼저, `STORE` 둘이 나중이다. 임시 변수가 필요 없는 이유가 눈에 보인다.

**오른쪽은 한 번만 평가된다 — 연쇄 대입에서도**

```python
class T:
    def __init__(self, n): self.n = n
    def __setitem__(self, k, v): print(f"  {self.n}[{k}] = {v}")

def make():
    print("  오른쪽 식 한 번만 평가")
    return "값"

a = T("A"); b = T("B")
a[0] = b[0] = make()
```

```text
  오른쪽 식 한 번만 평가
  A[0] = 값
  B[0] = 값
```

### 4. 함수에 넘긴 것은 무엇인가 (예측)

**출력**

```text
[1, 2]
[1, 2, 9]
```

**왜 그런가**

- `rebind` 는 **이름표만** 새 리스트로 옮긴다. 바깥의 `L` 은 원래 객체를 그대로 가리킨다 → 안 보인다.
- `mutate` 는 **객체 자체를** 바꾼다. 바깥도 같은 객체를 가리키므로 보인다.

```text
 호출 시점: 매개변수 이름이 "대입"된다 (lst = L)

 경우 A: lst = [9, 9]              경우 B: lst.append(9)
  +--------+       +--------+       +-----------+
L | [1, 2] |  lst  | [9, 9] |    L->| [1, 2, 9] |
  +--------+       +--------+  lst->+-----------+
  바깥 그대로                        바깥에 보인다
```

`id()` 로 같은 일을 한 줄씩 본 것이다.

```python
def show(o):
    print("  안 id:", id(o))
    o = [0]
    print("  재대입 후 id:", id(o))

M = [1, 2]
print("밖 id:", id(M))
show(M)
print("밖 id:", id(M))
```

```text
밖 id: 123395548539968
  안 id: 123395548539968
  재대입 후 id: 123395548413504
밖 id: 123395548539968
```

들어갈 때는 같은 객체이고(첫 두 줄이 같다), 재대입하면 안쪽만 갈라진다(셋째 줄).

**뭐라고 불러야 하나 — 둘 다 아니다**

공식 FAQ 가 이름을 정해 두었다 — 「**인자는 대입으로 전달된다**」(*arguments are passed by assignment*).\
같은 문단이 이어서 못을 박는다 — *"there's no alias between an argument name in the caller and callee, and so no call-by-reference per se."*

| 부르는 이름 | 맞나 | 왜 |
|---|---|---|
| 값 전달(call by value) | ✗ | 객체가 복사되지 않는다. `mutate` 의 결과가 바깥에 보인다 |
| 참조 전달(call by reference) | ✗ | 이름의 별칭이 아니다. `rebind` 의 결과가 바깥에 안 보인다 |
| **대입으로 전달** | ○ | 문서의 표현. `lst = L` 이 호출 시점에 일어난 것이 전부다 |

흔히 쓰이는 별칭으로 「객체 참조에 의한 전달」·「call by sharing」 이 있다 — 뜻은 같지만 **공식 문서의 말은 「대입으로 전달」이다.**

**판정 한 줄**

**객체를 바꾸면 바깥에 보이고, 이름을 바꾸면 안 보인다.**

### 5. 같은 줄인데 명령이 다르다 (예측)

**출력**

```text
전역
UnboundLocalError : cannot access local variable 'x' where it is not associated with a value
```

**왜 그런가**

언어 레퍼런스가 규칙을 그대로 적는다 —\
*"If a name binding operation occurs anywhere within a code block, all uses of the name within the block are treated as references to the current block."*

**"anywhere"** 가 전부다. `x = "지역"` 이 `print(x)` **아래**에 있어도, 그 블록에서 `x` 는 통째로 지역 이름이 된다.

```text
def read():                def write():
    print(x)                   print(x)        <- 여기서 터진다
                               x = "지역"       <- 이 한 줄 때문에

 블록에 x 대입이 없다           블록에 x 대입이 있다
      |                             |
      v                             v
 x 는 전역 이름                 x 는 "통째로" 지역 이름
 LOAD_GLOBAL                   LOAD_FAST_CHECK  (비어 있으면 에러)
```

컴파일러가 낸 명령이 그대로 근거다.\
(아래 `dis` 출력의 왼쪽 숫자는 **소스 줄 번호**다 — 이 프로그램 그대로 파일에 넣고 돌린 것이다.)

```python
import dis

x = "전역"

def read():
    print(x)

def write():
    print(x)
    x = "지역"

dis.dis(read)
```

```text
  5           0 RESUME                   0

  6           2 LOAD_GLOBAL              1 (NULL + print)
             12 LOAD_GLOBAL              2 (x)
             22 CALL                     1
             30 POP_TOP
             32 RETURN_CONST             0 (None)
```

```python
dis.dis(write)
```

```text
  8           0 RESUME                   0

  9           2 LOAD_GLOBAL              1 (NULL + print)
             12 LOAD_FAST_CHECK          0 (x)
             14 CALL                     1
             22 POP_TOP

 10          24 LOAD_CONST               1 ('지역')
             26 STORE_FAST               0 (x)
             28 RETURN_CONST             0 (None)
```

- **소스의 그 줄은 글자까지 같은데 명령이 다르다.** `LOAD_GLOBAL x` 대 `LOAD_FAST_CHECK x`.
- 갈린 것은 그 줄이 아니라 **블록 전체에 대입이 있느냐**이고, **컴파일 시점에** 정해진다.
- `FAST` 는 지역 슬롯, `CHECK` 는 「비어 있으면 에러를 내라」. 그 에러가 `UnboundLocalError` 다.

**잡지 않으면 트레이스백이 난다**

```text
Traceback (most recent call last):
  File "<stdin>", line 5, in <module>
  File "<stdin>", line 4, in g
UnboundLocalError: cannot access local variable 'v' where it is not associated with a value
```

(위는 같은 성격의 코드를 `python3 - < ex.py` 로 돌린 것이다. 파일로 돌리면 `<stdin>` 자리에 그 파일 경로가 박힌다.)

**고치는 법 둘**

1. 전역을 정말 바꿀 생각이면 `global x` 를 선언한다.
2. 그럴 생각이 아니었으면 **이름을 다르게 짓는다.** 대개 이쪽이 맞다.

**명령 이름을 외우지 마라**

`LOAD_FAST_CHECK` 는 3.12 의 명령이다. 3.11 이전에는 같은 자리가 `LOAD_FAST` 였고 **에러만 같았다.**\
외울 것은 **「대입 한 줄이 이름을 통째로 지역으로 만든다」는 성질**이다.

### 6. `del` 과 스코프가 만나는 자리 (예측)

**출력**

```text
[1, 2, 3]
False
UnboundLocalError : cannot access local variable 'v' where it is not associated with a value
```

**왜 그런가 — 한 줄씩**

- `print(b)` → `[1, 2, 3]`.\
  `del a` 는 **이름표 `a` 만** 뗐다. 객체는 `b` 가 잡고 있어 멀쩡하다.\
  언어 레퍼런스의 표현이 정확히 이것이다 — *"the actual semantics are to unbind the name"*.
- `"a" in globals()` → `False`.\
  모듈 네임스페이스의 표에서 그 항목이 사라졌다. **이게 `del` 이 한 일의 전부다.**
- 함수 안의 `print(v)` → `UnboundLocalError`.\
  `v` 는 여전히 **지역 이름**이다(`del` 대상도 바인딩으로 친다). 슬롯이 비었을 뿐이라 `NameError` 가 아니라 이쪽이 난다.

```text
 전 상태                     del a 실행            후 상태
      +-----------+            이름표 a 만            +-----------+
 a -> | [1, 2, 3] |            떼어 낸다         b -> | [1, 2, 3] |
 b -> +-----------+                                   +-----------+
   이름표 둘                                     이름표 하나 — 객체는 산다
```

**전역과 지역에서 오류 이름이 갈리는 이유**

| 어디 | 다시 읽으면 | 왜 |
|---|---|---|
| 모듈 전역 | `NameError: name 'a' is not defined` | 표에서 항목이 아예 사라졌다 |
| 함수 지역 | `UnboundLocalError` | 이름은 여전히 지역 슬롯이고, 그 슬롯이 비었다 |

```python
a = [1, 2, 3]
b = a
del a
try:
    print(a)
except NameError as e:
    print("NameError:", e)
```

```text
NameError: name 'a' is not defined
```

**`del` 이 지운 것 — 한 문장**

**이름이다.** 객체는 마지막 이름표가 떨어졌을 때 회수되고, 그건 `del` 의 직접 효과가 아니라 **결과**다.

### 7. LEGB 와 `global`·`nonlocal` (왜)

**어느 층을 가리키나**

```text
   +-----------------------------------------+
   | B  Built-in   len, print, ...           |
   |  +------------------------------------+ |
   |  | G  Global   모듈 최상위   <---------|-|--- global 이 가리키는 곳
   |  |  +-------------------------------+ | |
   |  |  | E  Enclosing 바깥 함수 <------|-|-|--- nonlocal 이 가리키는 곳
   |  |  |  +--------------------------+ | | |
   |  |  |  | L  Local  지금 이 함수    | | | |  <- 선언이 없으면 대입은 여기
   |  |  |  +--------------------------+ | | |
   |  |  +-------------------------------+ | |
   |  +------------------------------------+ |
   +-----------------------------------------+
```

- **`global x`** — *"all uses of the names specified in the statement refer to the bindings of those names in the top-level namespace."* 모듈 최상위다. 중간에 낀 함수는 건너뛴다.
- **`nonlocal x`** — *"causes corresponding names to refer to previously bound variables in the nearest enclosing function scope."* **가장 가까운 바깥 함수**다.\
  ★ 「함수」라는 말이 중요하다 — 모듈 최상위나 클래스 본문은 대상이 아니다. 그래서 최상위에서 `nonlocal` 을 쓰면 `SyntaxError` 가 난다.
- **둘 다 안 쓰고 `x = ...`** — 그 이름은 **이 블록의 지역**이 된다. 바깥은 한 글자도 안 바뀐다.\
  그리고 5번의 규칙 때문에 **그 블록 안의 모든 `x` 읽기까지** 지역 참조가 된다.

**한 실험으로 셋을 같이 본다**

```python
x = "global"

def outer():
    x = "enclosing"
    def inner_read():
        print("  읽기:", x)
    def inner_local():
        x = "local"
        print("  지역:", x)
    def inner_nonlocal():
        nonlocal x
        x = "nonlocal 이 바꿈"
    def inner_global():
        global x
        x = "global 이 바꿈"
    inner_read()
    inner_local()
    print("  inner_local 뒤 outer 의 x:", x)
    inner_nonlocal()
    print("  inner_nonlocal 뒤 outer 의 x:", x)
    inner_global()
    print("  inner_global 뒤 outer 의 x:", x)

outer()
print("맨 밖 x:", x)
```

```text
  읽기: enclosing
  지역: local
  inner_local 뒤 outer 의 x: enclosing
  inner_nonlocal 뒤 outer 의 x: nonlocal 이 바꿈
  inner_global 뒤 outer 의 x: nonlocal 이 바꿈
맨 밖 x: global 이 바꿈
```

**읽기 세 줄이 결론이다**

- `inner_local` 뒤에도 `outer` 의 `x` 는 `"enclosing"` — **선언 없는 대입은 바깥을 안 건드린다.**
- `inner_nonlocal` 뒤에 `outer` 의 `x` 가 바뀌었다 — **한 칸 밖**을 잡았다.
- `inner_global` 뒤에도 `outer` 의 `x` 는 그대로고 **맨 밖만** 바뀌었다 — **중간을 건너뛰었다.**

**핵심 비대칭**

**읽기는 LEGB 로 밖을 찾아 나가고, 쓰기는 언제나 지역이다.**\
이 비대칭을 뒤집는 장치가 `global`·`nonlocal` 둘뿐이다.

### 8. 참조를 세는 도구의 함정 (예측)

**출력**

```text
2
1
```

**왜 그런가**

이름은 `obj` 하나뿐인데 `2` 가 나온다. **`getrefcount` 를 부르는 동안 인자 이름이 한 장 더 붙기 때문이다.**

```text
 sys.getrefcount(obj) 를 평가하는 순간

   obj ----+
           v
       +--------+
       | object |  <---- getrefcount 의 매개변수 이름
       +--------+
   이름표 둘 -> 2 가 나온다
```

둘째 줄이 그 증거다 — 이름을 안 준 `object()` 는 `1` 이 나온다.\
**그 하나가 바로 「물어보느라 붙은 장」이다.** 실제 이름표는 0장이다.

붙였다 떼면서 보면 움직임이 그대로 보인다.

```python
import sys
obj = object()
print("이름 1개:", sys.getrefcount(obj))
alias = obj
print("이름 2개:", sys.getrefcount(obj))
lst = [obj]
print("리스트에도:", sys.getrefcount(obj))
del alias, lst
print("되돌림:", sys.getrefcount(obj))
```

```text
이름 1개: 2
이름 2개: 3
리스트에도: 4
되돌림: 2
```

**그래서 쓰는 법**

이 함수의 값은 **언제나 실제보다 1 크다.** 절댓값이 아니라 **차이**를 보는 데 쓴다 —\
「이 코드를 돌리기 전후로 2가 늘었다」가 유효한 관찰이고, 「지금 3장 붙어 있다」는 틀린 관찰이다.

**수 말고 누구인지가 궁금하면**

```python
import gc
target = ["내용"]
holder = {"key": target}
also = [target]

refs = gc.get_referrers(target)
print("참조자 수:", len(refs))
for r in refs:
    print("  -", type(r).__name__, repr(r)[:60])
```

```text
참조자 수: 3
  - dict {'key': ['내용']}
  - list [['내용']]
  - dict {'__name__': '__main__', '__doc__': None, '__package__': Non
```

셋째로 나온 dict 는 **모듈 전역 네임스페이스**다 — `target` 이라는 이름 자체가 거기 들어 있다.\
「이름도 참조다」가 눈에 보이는 자리다.

> **주의** — `sys.getrefcount` 와 `gc.get_referrers` 는 **CPython 의 참조 카운팅에 기댄 진단 도구**다.\
> 다른 구현에는 없거나 의미가 다르다. 프로그램 로직이 이 값에 기대면 안 된다.

### 9. 컴파일 단위가 답을 바꾼다 (경계)

**파일로 돌린 출력**

```text
파일 - 리터럴 둘: True
파일 - 상수 접기: True
```

**대화형에 한 줄씩 넣은 출력**

```text
>>> a = "hello world"
>>> b = "hello world"
>>> print(a is b)
False
>>> c = "hello" + " world"
>>> print(a is c)
False
>>> x = 1000
>>> y = 1000
>>> print(x is y)
False
```

**같은 파이썬, 같은 버전, 같은 글자인데 답이 뒤집혔다.**

**왜 그런가**

```text
파일 실행                              대화형
+-----------------------------+        +-------------+  한 줄 = 한 단위
| a = "hello world"           |        | a = "..."   |
| b = "hello world"           |        +-------------+
| ...                         |        +-------------+
+-----------------------------+        | b = "..."   |
   전체가 "한 컴파일 단위"                +-------------+
   같은 상수를 하나로 합친다                합칠 상대가 아예 없다
   -> a is b  True                       -> a is b  False
```

- 파일은 전체가 한 번에 컴파일되므로, 컴파일러가 **같은 상수를 하나로 합친다.**
- 대화형은 **입력 한 줄(한 문)이 한 컴파일 단위**라 합칠 상대가 존재하지 않는다.

모듈을 나누면 파일에서도 갈린다.

```python
# modA.py, modB.py 에 각각  S = "hello world" / N = 1000
import modA, modB
print("다른 모듈, 같은 문자열:", modA.S is modB.S)
print("다른 모듈, 같은 정수:", modA.N is modB.N)
```

```text
다른 모듈, 같은 문자열: False
다른 모듈, 같은 정수: False
```

그런데 **식별자 모양 문자열**(공백·기호 없는 것)은 모듈이 달라도 합쳐진다.

```python
# modC.py, modD.py 에 각각  S = "helloworld"
import modC, modD
print("다른 모듈, 식별자 모양 문자열:", modC.S is modD.S)
```

```text
다른 모듈, 식별자 모양 문자열: True
```

**두 기계가 따로 돈다**

| 기계 | 경계 | 확인 |
|---|---|---|
| 한 컴파일 단위 안의 상수 합치기 | 파일 하나 / 대화형 한 줄 | `"hello world"` 가 한 파일 안에서는 `True`, 모듈이 다르면 `False` |
| 식별자 모양 문자열의 자동 인터닝 | 프로세스 전체 | `"helloworld"` 는 모듈이 달라도 `True` |

둘 다 **CPython 구현 세부**다. 인터닝의 정본은 [02-is-vs-eq-interning](../02-is-vs-eq-interning/2-summary.md) 이다.

**그 사실이 뜻하는 것**

「같은 값이면 같은 객체」는 **참도 거짓도 아니라, 내가 통제하지 못하는 조건에 달린 문장**이다.\
REPL 에서 확인한 것이 파일에서 다르고, 한 파일에서 확인한 것이 모듈을 쪼개면 다르다.\
**그래서 `is` 로 값을 묻지 않는다.** 바인딩 쪽 결론으로 적으면 이렇다 —\
**「이름표 둘이 같은 상자에 붙었는지」는 내가 쓴 코드가 아니라 컴파일러가 정한다.**

### 10. 세 층 가르기 (경계)

**① 언어 보장** — 언어 레퍼런스가 정한 것. 어떤 구현에서도 성립한다.

| 사실 | 근거 |
|---|---|
| 모든 객체는 정체·타입·값을 가지며 정체는 변하지 않는다 | 데이터 모델 3.1 |
| `is` 는 정체를 비교하고 `id()` 는 정체를 나타내는 정수를 돌려준다 | 데이터 모델 3.1 |
| 이름을 묶는 구문의 목록이 정해져 있다(대입·`def`·`class`·`import`·`for`·`as` 등) | 실행 모델 4.2 |
| 블록 안 **어디에든** 바인딩이 있으면 그 블록의 모든 사용이 지역 참조가 된다 | 실행 모델 4.2 |
| `del` 의 의미는 이름을 **푸는** 것이다 | 실행 모델 4.2 |
| `global` 은 최상위, `nonlocal` 은 가장 가까운 바깥 **함수** 스코프 | 실행 모델 4.2 |
| 인자는 **대입으로** 전달되며 호출자·피호출자 사이에 별칭은 없다 | Programming FAQ |
| **불변** 타입에서는 새 값을 계산하는 연산이 기존 객체를 돌려줘도 되고, **가변** 타입에서는 안 된다 | 데이터 모델 3.1 |

★ 마지막 줄이 열쇠다. 언어는 **인터닝을 허용**할 뿐 **어떤 값을 인터닝하라고 정하지 않는다.**

**② CPython 구현 세부사항** — 이 구현이 그럴 뿐이다.

| 사실 | 어떻게 확인했나 |
|---|---|
| `id()` 가 메모리 주소다 | `id()` 문서의 "CPython implementation detail" 표시 |
| 한 컴파일 단위 안의 같은 상수가 하나로 합쳐진다 | 9번의 파일 대 모듈 대조 |
| 식별자 모양 문자열이 자동 인터닝된다 | 9번의 `"helloworld"` 대조 |
| `"hel" + "lo"` 가 컴파일 시점에 접힌다 | 9번의 파일 대 대화형 대조 |
| `-5` \~ `256` 정수가 미리 만들어져 재사용된다 | C API 문서가 "the current implementation" 이라고 적는다 |
| 참조 카운팅으로 회수하므로 `sys.getrefcount` 가 존재한다 | 이 함수 자체가 CPython 전용이다 |

**③ 이 판(3.12.3)의 관찰** — 버전이 오르면 다시 찍어야 한다.

| 관찰 | 어디가 흔들리나 |
|---|---|
| 지역 이름 읽기가 `LOAD_FAST_CHECK` 로 컴파일된다 | 3.11 이전에는 `LOAD_FAST` 였다. **에러 종류는 같다** |
| `a = b = []` 이 `BUILD_LIST` + `COPY 1` 이다 | 명령 이름·개수는 컴파일러가 정한다 |
| `UnboundLocalError` 메시지 문구 | 판마다 바뀐 전례가 있다 |
| `sys.getrefcount(object())` 가 `1` 이다 | 인터프리터가 인자를 붙드는 방식에 달렸다 |
| `id()` 가 `123395548539968` 같은 15자리 정수다 | **실행할 때마다 다르다.** 값 자체는 의미가 없다 |

**이렇게 쓰면 틀린다**

- ✗ 「파이썬에서 변수는 객체의 **주소**를 담는다」\
  ○ 「이름이 객체에 **묶인다**」. `id()` 가 주소라는 것은 CPython 구현 세부다.
- ✗ 「같은 리터럴은 같은 객체다」\
  ○ 「**컴파일 단위에 달렸다.** 파일에서는 그렇고 대화형에서는 아니다」.
- ✗ 「파이썬은 참조 전달이다」\
  ○ 「**대입으로 전달된다.**」 문서 자신이 *"no call-by-reference per se"* 라고 부정한다.
- ✗ 「`del` 은 객체를 삭제한다」\
  ○ 「이름을 **푼다.**」 객체 회수는 마지막 참조가 사라졌을 때 따라오는 결과다.

> **구현 세부사항(implementation detail)** — 언어 명세가 보장하지 않고 특정 구현이 그렇게 만들어 둔 것.\
> 예: 문서에 "CPython implementation detail" 표시가 있거나 "the current implementation" 이라는 한정어가 붙어 있으면 그것이다.

**판정 기준 한 줄**

「두 이름이 같은 객체를 가리키는가」가 코드의 정상 동작에 필요하다면, 그 코드는 **내가 직접 만든 공유**에만 기대야 한다.\
**컴파일러가 만들어 준 공유에 기대면 구현 세부사항에 기댄 코드다.**

### 11. 뿌리에서 갈라져 나온 것들 (연결)

세 주제가 전부 **「이름표 모델」 한 장**으로 설명된다.

```text
                「변수는 이름표, 대입은 바인딩」
                            |
        +-------------------+--------------------+
        v                   v                    v
   20번 가변 기본 인자    03번 얕은 복사       02번 is 와 인터닝
   함수 객체가 기본값에    새 바구니에 옛      컴파일러가 같은 상자에
   이름표를 붙들고 있다    이름표를 옮겨 담는다  이름표 둘을 붙여 버린다
```

| 주제 | 이름표 모델로 읽으면 | 증상 | 정본 |
|---|---|---|---|
| 가변 기본 인자 | `def` 를 실행할 때 기본값 객체가 **한 번** 만들어지고, **함수 객체가** 그 이름표를 들고 있다. 호출마다 같은 상자가 건네진다 | 호출할수록 리스트가 쌓인다 | [20-mutable-default-args](../20-mutable-default-args/2-summary.md) |
| 얕은 복사 | 복사는 **바구니를 새로** 만들고 **안의 이름표를 그대로 옮겨 담는** 것이다. 안쪽 상자는 여전히 하나다 | 복사본의 안쪽을 바꿨는데 원본이 바뀐다 | [목록의 **03번 주제**](../03-mutability-and-copying/) |
| `is` 와 인터닝 | 컴파일러·정수 캐시가 **내가 시키지 않은 공유**를 만든다. 이름표 둘이 한 상자에 붙는다 | 작은 값에서만 `is` 가 참이라 테스트가 통과한다 | [02-is-vs-eq-interning](../02-is-vs-eq-interning/2-summary.md) |

**한 문장으로**

세 증상의 원인은 전부 같다 — **파이썬에서 공유는 기본값이고, 분리가 명시적 요청이다.**\
다른 언어에서 온 사람이 반대로 알고 있어서 이 세 자리가 전부 「조용히 틀리는 자리」가 된다.

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
| 1·2 | `b = a` 공유, `a = b = []` 대 `c, d = [], []`, `dis` 두 판 | 각 1회 |
| 3 | `i, L[i] = 1, 5`, `x, y = y, x` 의 `dis`, `__setitem__` 추적 | 각 1회 |
| 4 | `rebind`/`mutate`, 함수 안팎 `id()` 3점 | 각 1회 |
| 5 | `read`/`write` 의 `dis` 와 `UnboundLocalError`, 트레이스백 판(`python3 - < ex.py`) | 각 1회 |
| 6 | `del` 뒤의 `NameError`·`UnboundLocalError`·`globals()` | 각 1회 |
| 7 | `global`/`nonlocal` 4중첩 실험 | 1회 |
| 8 | `sys.getrefcount` 4단계, `gc.get_referrers` | 각 1회 |
| 9 | 문자열·정수 공유 — **파일 실행 / 대화형(`script -qc python3`) / 모듈 분리 세 경로** | 경로당 1회 |

**여러 번 돌려 갈린 것**

- `id()` 값은 **실행할 때마다 다르다.** 4번 답의 15자리 숫자는 그 판의 값일 뿐이다 — 같은 줄의 `id` 가 **서로 같은지**만 근거로 쓴다.
- `sys.getrefcount` 의 절댓값은 그 시점의 참조 수에 달렸다. 근거로 쓴 것은 **증감 폭**이다.
- 9번의 문자열 공유는 **경로에 따라 답이 뒤집혔다.** 「파일에서 True 였다」를 세 번 반복해도 보장이 되지 않는 이유다.

**구현 의존 항목 — 버전이 오르면 다시 찍을 것**

| 다시 찍을 것 | 왜 |
|---|---|
| 2·5번의 `dis` 출력 | 바이트코드 명령 이름·개수는 판마다 바뀐다 |
| 5·6번의 오류 메시지 문구 | 문구가 바뀐 전례가 있다 |
| 9번의 `is` 결과 전부 | 상수 합치기·자동 인터닝 범위는 구현 세부다 |
| 8번의 `getrefcount` 값 | 인터프리터 내부 사정에 달렸다 |

나머지(바인딩·스코프·`del`·인자 전달)는 **언어 보장**이므로 어떤 구현에서도 같아야 한다.
