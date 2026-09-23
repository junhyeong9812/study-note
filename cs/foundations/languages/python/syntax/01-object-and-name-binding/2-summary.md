# python/syntax/01-object-and-name-binding — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **이 본문은 원고가 아니라 Claude 작성이다**(문법·API 갈래는 원고 없이 공식 문서로 접지한다).
>
> **기준 소스** — 열어서 확인한 것만.
> - [3.1. Objects, values and types](https://docs.python.org/3.12/reference/datamodel.html) — 객체·정체·타입·값의 정의
> - [4.2. Naming and binding](https://docs.python.org/3.12/reference/executionmodel.html) — 무엇이 이름을 묶나, 지역 변수 규칙
> - [7.2. Assignment statements](https://docs.python.org/3.12/reference/simple_stmts.html#assignment-statements) — 대입 대상의 처리 순서
> - [7.5. The `del` statement](https://docs.python.org/3.12/reference/simple_stmts.html#the-del-statement) — `del` 이 무엇을 지우나
> - [Programming FAQ — call by reference](https://docs.python.org/3.12/faq/programming.html) — 인자 전달을 뭐라 부르나
>
> **실행 검증** — 이 문서에 실린 출력은 전부 `python3` **3.12.3**(Linux, x86_64)에서 실제로 돌려 나온 것이다. 지어낸 출력은 없다.
> 문자열 공유 실험은 **파일 실행과 대화형 두 경로에서 각각** 돌렸다 — 결과가 갈린다.
> **버전** — 이름 바인딩 모델 자체는 Python 3 전체 공통. 바이트코드 명령 이름(`LOAD_FAST_CHECK` 등)은 **3.12 의 것**이라 버전마다 다르다.
> **구현 대 명세** — 「이름표」 모델은 언어 보장이고, 「같은 값이 같은 객체가 되는 것」은 구현 세부다. 「구현 세부사항 대 언어 보장」 절에서 선을 긋는다.

## 한눈에 — 쉽게 말하면

**변수는 상자가 아니라 이름표다.**

다른 언어를 먼저 배웠으면 `x = 5` 를 「x 라는 상자에 5 를 넣는다」로 읽는다.\
파이썬은 그게 아니다 — **5 라는 객체가 따로 있고, x 는 거기에 붙이는 이름표**다.

```text
다른 언어의 그림 (틀린 모델)            파이썬의 그림 (맞는 모델)
+-------+                              +-------+
|   5   |  <- x 라는 상자 자체          |   5   |  <- 객체
+-------+                              +-------+
                                           ^
  x 에 다른 값을 넣으면                     |
  상자 안의 내용이 바뀐다                    x   <- 이름표

                                       x 에 다른 값을 대입하면
                                       이름표를 떼서 다른 객체에 붙인다.
                                       5 라는 객체는 손끝 하나 안 닿는다.
```

**비유 대응표** — 이 문서는 끝까지 이 대응을 지킨다.

| 비유 | 실체 | 확인하는 법 |
|---|---|---|
| 상자 | 객체 | `id()` 로 번호가 나온다 |
| 이름표 | 이름(변수) | `globals()`·`locals()` 에 들어 있다 |
| 이름표를 붙이는 일 | 바인딩 | `=`·`def`·`import`·`for` 가 한다 |
| 이름표를 떼는 일 | `del` | 상자는 그대로다 |
| 이름표가 몇 장 붙었나 | 참조 수 | `sys.getrefcount()` (★ 세는 행위가 한 장 더 붙인다) |

**똑같은 구조다** — 실무에서 이 모델이 드러나는 자리가 셋이다.\
함수에 리스트를 넘겼더니 바깥 리스트가 바뀐 것([목록의 **03번 주제**](../03-mutability-and-copying/)) ·\
`def f(x=[])` 가 호출마다 같은 리스트를 쓰는 것([20-mutable-default-args](../20-mutable-default-args/)) ·\
`a is b` 가 값에 따라 우연히 참이 되는 것([02-is-vs-eq-interning](../02-is-vs-eq-interning/)).\
셋 다 **「이름표 모델」 한 장으로 설명된다.** 그래서 이 주제가 이 갈래의 뿌리다.

> **객체(object)** — 값과 타입을 가지고 메모리에 실제로 놓인 것 하나.\
> 예: `[1, 2]` 를 두 번 쓰면 겉보기가 같아도 리스트 객체가 **둘** 생긴다.

> **이름(name)** — 객체에 붙이는 꼬리표. 다른 언어의 「변수」와 달리 **저장 공간이 아니다.**\
> 예: `x = 5` 뒤에 `x = "글자"` 라고 쓰면 5 를 지운 게 아니라 이름표를 옮긴 것이다.

> **바인딩(binding)** — 이름을 객체에 묶는 일.\
> 예: 언어 레퍼런스가 「이름을 묶는 구문」을 목록으로 정해 두었다 — 대입·`def`·`class`·`import`·`for` 머리·`with ... as`·`except ... as`.

## 이 주제가 답하려는 질문

1. **대입이 무엇을 복사하나** — `b = a` 다음에 `a` 를 바꾸면 `b` 에 보이나, 안 보이나.
2. **함수에 넘긴 것이 무엇인가** — 「값 전달」도 「참조 전달」도 아니면, 뭐라고 불러야 하나.
3. **이름이 어디에서 풀리나** — 같은 `x` 가 함수 안에서 전역을 읽기도 하고 `UnboundLocalError` 를 내기도 하는 이유.

## 동작 방식

> 이 절이 본문이다. 그림을 먼저 두고 그 그림을 문장으로 읽는다.
> 이 주제의 그림은 전부 **「이름 → 객체」 화살표**다.

### 1. 대입은 복사가 아니라 바인딩이다

**언제 쓰나** — 변수를 다른 변수에 넣을 때마다. 즉 거의 언제나.

```text
입력 코드                파이썬이 하는 일
---------------------   -------------------------------------------
a = [1, 2]              리스트 객체를 만들고 a 라는 이름표를 붙인다
b = a                   같은 객체에 b 라는 이름표를 하나 더 붙인다

 전 상태                          후 상태 (b.append(3) 실행)
      +--------+                       +-----------+
 a -> | [1, 2] |                  a -> | [1, 2, 3] |
 b -> +--------+                  b -> +-----------+
   이름표 둘, 상자 하나               한쪽에서 바꾼 것이 양쪽에 보인다
```

```python
a = [1, 2]
b = a
b.append(3)
print(a)          # [1, 2, 3]
print(a is b)     # True
```

그림 해설.

- `b = a` 는 **리스트를 복사하지 않는다.** 화살표를 하나 더 그릴 뿐이다.
- 그래서 `b` 로 바꾼 것이 `a` 에서 보인다. 「따로 쓰려고 대입했는데 같이 움직인다」가 여기서 난다.
- 복사가 필요하면 복사를 **따로 요청해야 한다**([목록의 **03번 주제**](../03-mutability-and-copying/)).

**비용** — 대입은 객체 크기와 무관하게 O(1)이다.\
대신 **공유가 기본값**이라는 대가를 치른다. 안 바라던 공유가 이 갈래 사고의 절반이다.

### 2. `a = b = []` 과 `a, b = [], []` — 바이트코드가 답한다

**언제 쓰나** — 두 변수를 빈 컨테이너로 한꺼번에 초기화할 때. 겉보기가 비슷해 섞어 쓰기 쉽다.

```text
a = b = []                            a, b = [], []
 리스트를 "한 번" 만들고               리스트를 "두 번" 만들고
 이름표 둘을 같이 붙인다                각각에 하나씩 붙인다

      +----+                          +----+      +----+
 a -> | [] |                     a -> | [] | b -> | [] |
 b -> +----+                          +----+      +----+
   a is b -> True                     a is b -> False
```

지어낸 그림이 아니다. 컴파일러가 낸 명령이 그대로 말해 준다.

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

실행하면 그림대로 갈린다.

```python
a = b = []
print(a is b)       # True
a.append(1)
print(a, b)         # [1] [1]

c, d = [], []
print(c is d)       # False
c.append(1)
print(c, d)         # [1] []
```

그림 해설.

- `BUILD_LIST 0` 이 **왼쪽은 한 번, 오른쪽은 두 번** 나온다. 객체 개수가 거기서 정해진다.
- `COPY 1` 은 스택 맨 위를 한 벌 더 쌓는 명령이다 — **같은 객체를 두 번 저장**하려는 것이다.
- 즉 `a = b = []` 은 「빈 리스트 둘」이 아니라 「빈 리스트 하나에 이름표 둘」이다.
- `a = b = 0` 처럼 **불변** 객체면 공유가 드러나지 않는다. 증상은 가변 객체에서만 난다.

**비용** — `a = b = []` 이 객체 하나를 아낀다.\
대신 둘을 따로 쓰려던 의도였다면 **조용히 틀린다** — 에러가 없다.

### 3. 이름은 왼쪽부터 순서대로 묶인다

**언제 쓰나** — 대상이 여럿인 대입(`i, L[i] = ...`)이나 연쇄 대입을 쓸 때.

```text
i, L[i] = 1, 5      오른쪽을 먼저 다 평가하고 (1, 5)
                    왼쪽 대상을 "왼쪽부터" 묶는다

 단계 1: i = 1          i 가 0 에서 1 로 바뀐다
 단계 2: L[i] = 5       이때 i 는 이미 1 이다  ->  L[1] = 5
```

```python
L = [0, 0]
i = 0
i, L[i] = 1, 5
print(i, L)        # 1 [0, 5]
```

연쇄 대입도 같은 규칙이다 — 오른쪽 식은 **한 번만** 평가된다.

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

그림 해설.

- 오른쪽이 먼저, 한 번만. 그다음 왼쪽 대상을 **적힌 순서대로** 묶는다.
- 그래서 `i, L[i] = 1, 5` 는 `L[0]` 이 아니라 `L[1]` 을 바꾼다.
- 스왑(`x, y = y, x`)이 되는 이유도 같다 — 오른쪽 `(y, x)` 를 먼저 만들어 놓고 왼쪽에 나눠 준다.

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

**비용** — 임시 변수가 필요 없다.\
대신 왼쪽 대상이 **서로를 참조하면** 순서에 결과가 달려 있다.

### 4. 함수 인자 — 「값 전달」도 「참조 전달」도 아니다

**언제 쓰나** — 함수에 무엇이든 넘길 때마다.

공식 문서가 이름을 정해 두었다 — 「**인자는 대입으로 전달된다**」(*arguments are passed by assignment*).\
같은 문장이 이어서 못을 박는다 — *"there's no alias between an argument name in the caller and callee, and so no call-by-reference per se."*

```text
호출 쪽                     함수 안
                 호출 시점에 매개변수 이름이 "대입"된다 (lst = L)

 L ---------+
            v
        +--------+
        | [1, 2] |   <-------- lst
        +--------+

 경우 A: lst.append(9)          경우 B: lst = [9, 9]
  같은 상자의 내용을 바꾼다        lst 이름표만 새 상자로 옮긴다
        +-----------+            +--------+        +--------+
   L -> | [1, 2, 9] |       L -> | [1, 2] |  lst ->| [9, 9] |
   lst->+-----------+            +--------+        +--------+
  바깥에 보인다                   바깥은 그대로다
```

```python
def rebind(lst):
    lst = [9, 9]
    print("  안:", lst)

def mutate(lst):
    lst.append(9)
    print("  안:", lst)

L = [1, 2]
rebind(L); print("밖:", L)
L = [1, 2]
mutate(L); print("밖:", L)
```

```text
  안: [9, 9]
밖: [1, 2]
  안: [1, 2, 9]
밖: [1, 2, 9]
```

`id()` 로 보면 무슨 일이 일어났는지 한 줄로 드러난다.

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

그림 해설.

- **들어갈 때는 같은 객체다** — 안팎의 `id` 가 같다. 여기까지는 「참조 전달」처럼 보인다.
- **재대입하면 갈라진다** — 안쪽 이름표만 새 상자로 옮겨 가고 바깥은 그대로다. 여기서는 「값 전달」처럼 보인다.
- 그래서 둘 중 어느 이름도 맞지 않는다. **묶는 것은 이름이고, 넘어간 것은 객체다.**
- 판정 한 줄: **객체를 바꾸면 바깥에 보이고, 이름을 바꾸면 안 보인다.**

> **가변(mutable) / 불변(immutable)** — 객체 자체의 값을 바꿀 수 있나 없나.\
> 예: 리스트는 `append` 로 내용이 바뀌지만, 정수 `5` 는 무슨 짓을 해도 `5` 다 — 바꾸려면 다른 객체를 만들어야 한다.

**비용** — 큰 리스트를 넘겨도 복사 비용이 없다(O(1)).\
대신 **함수가 남의 객체를 조용히 바꿀 수 있다**는 위험을 늘 안고 간다.

### 5. 이름이 풀리는 순서 — LEGB

**언제 쓰나** — 같은 이름이 여러 층에 있을 때. 중첩 함수·클로저에서 늘 나온다.

```text
   +-----------------------------------------+
   | B  Built-in   len, print, ...           |   가장 바깥
   |  +------------------------------------+ |
   |  | G  Global   모듈 최상위             | |
   |  |  +-------------------------------+ | |
   |  |  | E  Enclosing  바깥 함수의 지역 | | |
   |  |  |  +--------------------------+ | | |
   |  |  |  | L  Local  지금 이 함수    | | | |   가장 안쪽
   |  |  |  +--------------------------+ | | |
   |  |  +-------------------------------+ | |
   |  +------------------------------------+ |
   +-----------------------------------------+

   읽기는 안 -> 밖 순서로 찾는다  (L -> E -> G -> B)
   쓰기는 기본이 "지금 이 함수"다  (L 에 새로 만든다)
```

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

그림 해설.

- `inner_read` 는 자기 지역에 `x` 가 없으니 **한 칸 밖**(Enclosing)에서 찾는다 → `"enclosing"`.
- `inner_local` 의 `x = "local"` 은 **자기 지역에 새 이름표**를 만든다. 바깥은 안 건드린다.
- `nonlocal x` 는 「가장 가까운 바깥 **함수**의 그 이름을 쓰겠다」는 선언이다 → `outer` 의 `x` 가 바뀐다.
- `global x` 는 「모듈 최상위의 그 이름을 쓰겠다」는 선언이다 → `outer` 의 `x` 는 그대로고 맨 밖이 바뀐다.
- 마지막 두 줄이 그 차이의 증거다 — `outer` 의 `x` 는 `"nonlocal 이 바꿈"` 에 머물고, 맨 밖만 `"global 이 바꿈"` 이 됐다.

> **LEGB** — 이름을 찾는 순서의 머리글자. Local → Enclosing → Global → Built-in.\
> 예: 함수 안에서 `len` 을 쓰면 L·E·G 에 없으니 마지막 B 에서 내장 `len` 을 찾는다.

**비용** — 안쪽부터 찾으므로 지역 변수 접근이 가장 싸다.\
대신 **읽기 규칙과 쓰기 규칙이 다르다** — 이 비대칭이 다음 절의 오류를 만든다.

### 6. `UnboundLocalError` — 대입 한 줄이 이름을 통째로 지역으로 만든다

**언제 쓰나** — 전역 카운터를 함수 안에서 `count = count + 1` 로 올리려 할 때. 이 갈래 최고 빈도의 오류다.

언어 레퍼런스가 규칙을 그대로 적는다 —\
*"If a name binding operation occurs anywhere within a code block, all uses of the name within the block are treated as references to the current block."*

**"anywhere"** 가 핵심이다. 대입이 **아래쪽**에 있어도 위쪽 사용까지 지역이 된다.

```text
def read():            def write():
    print(x)               print(x)        <- 여기서 터진다
                           x = "지역"       <- 이 한 줄 때문에

  x 를 묶는 문이 없다        블록 안에 x 대입이 있다
       |                        |
       v                        v
  x 는 전역 이름             x 는 "통째로" 지역 이름
  LOAD_GLOBAL               LOAD_FAST_CHECK  (아직 안 묶임 -> 에러)
```

컴파일러가 낸 명령이 그대로 근거다. **같은 `print(x)` 인데 명령이 다르다.**

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

```python
read()
try:
    write()
except UnboundLocalError as e:
    print(type(e).__name__, ":", e)
```

```text
전역
UnboundLocalError : cannot access local variable 'x' where it is not associated with a value
```

그림 해설.

- `read` 는 `LOAD_GLOBAL x`, `write` 는 `LOAD_FAST_CHECK x`. **소스의 그 줄은 글자까지 같다.**
- 갈린 것은 그 줄이 아니라 **블록 전체에 대입이 있느냐**다. 컴파일 시점에 정해진다.
- `FAST` 는 지역 슬롯을 뜻하고, `CHECK` 는 「비어 있으면 에러를 내라」는 뜻이다. 그 에러가 `UnboundLocalError` 다.
- 고치는 법은 둘 — 전역을 정말 바꿀 생각이면 `global x` 를 선언하고, 아니면 **이름을 다르게 짓는다.**
- 명령 이름은 3.12 의 것이다. 3.11 이전에는 같은 자리가 `LOAD_FAST` 였고 에러만 같았다.\
  **외울 것은 명령 이름이 아니라 「대입 한 줄이 이름을 통째로 지역으로 만든다」는 성질이다.**

> **`UnboundLocalError`** — 지역 이름인데 아직 아무 객체에도 안 묶인 상태에서 읽었을 때 나는 오류.\
> 예: 함수 아래쪽에 `x = 1` 이 있으면 위쪽 `print(x)` 도 지역 `x` 를 읽으려다 여기서 터진다.

**비용** — 지역 변수를 슬롯 번호로 접근하니 빠르다(`LOAD_FAST`).\
대신 **컴파일 시점 결정**이라 「위에서는 전역, 아래에서는 지역」 같은 절충이 아예 불가능하다.

### 7. `del` 은 객체가 아니라 이름을 지운다

**언제 쓰나** — 큰 객체를 놓아 주려 할 때, 그리고 `del` 을 「삭제」로 오해할 때.

언어 레퍼런스의 표현은 *"the actual semantics are to unbind the name"* 이다. 이름을 **푸는** 것이다.

```text
 전 상태                        del box 실행            후 상태
      +--------+                  이름표 box 만          +--------+
 box->| [1, 2] |                  떼어 낸다        alias->| [1, 2] |
alias->+--------+                                        +--------+
  이름표 둘                                        이름표 하나 — 객체는 산다
```

```python
import sys
box = [1, 2]
alias = box
print("del 전 refcount:", sys.getrefcount(box))
del box
print("del 후 alias 는 살아 있다:", alias)
```

```text
del 전 refcount: 3
del 후 alias 는 살아 있다: [1, 2]
```

지워진 것은 이름이므로, 다시 읽으면 **`NameError`** 다.

```python
a = [1, 2, 3]
b = a
del a
print(b)
try:
    print(a)
except NameError as e:
    print("NameError:", e)
```

```text
[1, 2, 3]
NameError: name 'a' is not defined
```

함수 **지역** 이름을 `del` 하면 이름 자체는 여전히 지역이므로 `UnboundLocalError` 가 난다.

```python
def g2():
    v = 1
    del v
    try:
        print(v)
    except UnboundLocalError as e:
        print("  del 뒤 읽기 -> UnboundLocalError:", e)
g2()
```

```text
  del 뒤 읽기 -> UnboundLocalError: cannot access local variable 'v' where it is not associated with a value
```

그림 해설.

- `del` 은 **이름표를 떼는 가위**지 상자를 부수는 망치가 아니다.
- 마지막 이름표가 떨어지면 그때 객체가 회수된다 — 그건 `del` 의 직접 효과가 아니라 **결과**다.
- 전역 이름을 `del` 하면 `globals()` 에서 사라지고(`"h" in globals()` 가 `False`), 지역 이름을 `del` 하면 슬롯이 비어 `UnboundLocalError` 가 난다. **같은 「지움」인데 오류 이름이 다른 이유가 거기 있다.**

**비용** — `del` 은 O(1)이고, 마지막 참조였다면 메모리를 바로 돌려받는다.\
대신 **다른 이름표가 남아 있으면 아무 메모리도 안 준다** — 「지웠는데 안 줄어든다」가 여기서 난다.

### 8. 참조를 세는 두 도구 — 그리고 그 함정

**언제 쓰나** — 「이 객체를 누가 붙들고 있나」를 확인할 때.

```text
sys.getrefcount(obj)                    gc.get_referrers(obj)
 몇 장 붙어 있나 (수)                    누가 붙들고 있나 (목록)
 ★ 물어보는 행위가 한 장 더 붙인다        ★ 지금 이 프레임·모듈 dict 도 센다
```

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
print("이름 없이 바로:", sys.getrefcount(object()))
```

```text
이름 1개: 2
이름 2개: 3
리스트에도: 4
되돌림: 2
이름 없이 바로: 1
```

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

그림 해설.

- 이름이 하나인데 `2` 가 나온다. **`getrefcount` 에 넘기는 동안 인자 이름이 한 장 더 붙기 때문이다.**\
  그 증거가 마지막 줄이다 — 이름을 안 준 `object()` 는 `1` 이 나온다. 그 하나가 바로 「물어보느라 붙은 장」이다.
- 그래서 이 함수의 값은 **언제나 실제보다 1 크다.** 절댓값이 아니라 **차이**를 보는 데 쓴다.
- `gc.get_referrers` 는 수가 아니라 **누구인지**를 준다. 위에서 셋째로 나온 dict 는 모듈 전역 공간이다 — `target` 이라는 이름 자체가 거기 들어 있다.
- 두 도구 다 **CPython 의 참조 카운팅에 기댄 것**이다. 다른 구현에는 `getrefcount` 가 없거나 의미가 다르다.

**비용** — 두 도구 다 진단용이다. `gc.get_referrers` 는 힙 전체를 훑을 수 있어 느리다.\
대신 「누수 같은데 누가 잡고 있는지 모르겠다」에 답하는 거의 유일한 수단이다.

## 문법 — 형태와 규칙

```python
x = 5                 # 대입 — 이름 하나를 묶는다
a = b = []            # 연쇄 대입 — 한 객체에 이름 둘
a, b = [], []         # 언패킹 — 객체 둘에 이름 하나씩
x, y = y, x           # 스왑 — 오른쪽을 먼저 만든다
del x                 # 이름을 푼다 (객체를 지우는 게 아니다)
global x              # 이 블록의 x 는 모듈 최상위의 그것
nonlocal x            # 이 블록의 x 는 가장 가까운 바깥 함수의 그것
id(x)                 # 정체를 나타내는 정수
```

규칙은 다섯이다.

1. **이름을 묶는 구문이 정해져 있다.** 언어 레퍼런스가 목록으로 못 박는다 —\
   함수의 매개변수 · `class` · `def` · 대입식(`:=`) · 대입문의 대상 · `for` 머리 · `with ... as` · `except ... as` · `import` · `type` 문 · 타입 매개변수 목록.
2. **블록 안에 그 이름을 묶는 구문이 하나라도 있으면 그 이름은 그 블록의 지역**이다 — `global`·`nonlocal` 로 선언하지 않는 한.
3. **읽기는 LEGB, 쓰기는 지역.** 이 비대칭을 뒤집는 장치가 `global`·`nonlocal` 둘뿐이다.
4. **`del` 은 이름을 푼다.** 언어 레퍼런스가 `del` 대상도 「묶인 것으로 친다」고 적는 이유가 이것이다 — `del` 이 있는 블록에서 그 이름은 지역이 된다.
5. **`nonlocal` 은 「함수」 스코프만 본다.** 모듈 최상위나 클래스 본문은 대상이 아니다 — 그래서 최상위에서 `nonlocal` 을 쓰면 `SyntaxError` 다.

## 어디서 틀리나

### (1) 「따로 쓰려고」 대입했는데 같이 움직인다

```python
a = b = []
a.append(1)
print(a, b)      # [1] [1]
```

`a = b = 0` 으로 시험하면 증상이 안 난다. **불변 객체는 공유돼도 티가 안 나기 때문이다.**\
그래서 「리스트로 바꾸는 순간」 터진다.

### (2) 전역 카운터를 올리려다 `UnboundLocalError`

```python
count = 0
def tick():
    count = count + 1     # 이 한 줄이 count 를 통째로 지역으로 만든다
```

읽기는 되는데(`print(count)` 만 있으면 전역을 읽는다) **같은 줄에 대입을 붙이는 순간** 읽기까지 지역이 된다.\
`global count` 를 쓰거나, 애초에 전역 상태를 안 쓰는 쪽이 낫다.

### (3) `del` 로 메모리를 비웠다고 믿는다

```python
import sys
big = [0] * 1000000
ref = big
del big
print(len(ref))      # 1000000  — 하나도 안 줄었다
```

`del` 은 이름표만 뗀다. **다른 이름표가 남아 있으면 객체는 그대로 산다.**

### (4) `getrefcount` 의 값을 그대로 믿는다

```python
import sys
x = object()
print(sys.getrefcount(x))     # 2   <- 이름은 하나뿐인데
```

**세는 행위가 한 장을 더 붙인다.** 절댓값으로 결론을 내면 언제나 하나씩 틀린다.

### (5) 「같은 리터럴이니 같은 객체겠지」 — 파일과 대화형이 다르다

같은 코드가 **어디서 컴파일됐느냐**에 따라 답이 갈린다. 이 주제에서 가장 헷갈리는 자리다.

파일로 돌린 경우:

```python
a = "hello world"
b = "hello world"
print("파일 - 리터럴 둘:", a is b)
c = "hello" + " world"
print("파일 - 상수 접기:", a is c)
```

```text
파일 - 리터럴 둘: True
파일 - 상수 접기: True
```

같은 줄을 대화형에 한 줄씩 넣은 경우:

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

**같은 파이썬, 같은 버전, 같은 글자인데 답이 뒤집혔다.**\
파일은 전체가 **한 컴파일 단위**라 같은 상수가 하나로 합쳐지고, 대화형은 **한 줄이 한 컴파일 단위**라 합칠 상대가 없다.

모듈을 나누면 파일에서도 갈린다.

```python
# modA.py 와 modB.py 에 각각  S = "hello world" / N = 1000
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
# modC.py 와 modD.py 에 각각  S = "helloworld"
import modC, modD
print("다른 모듈, 식별자 모양 문자열:", modC.S is modD.S)
```

```text
다른 모듈, 식별자 모양 문자열: True
```

**두 기계가 따로 돈다는 뜻이다** — ① 한 컴파일 단위 안의 상수 합치기 ② 식별자 모양 문자열의 자동 인터닝.\
둘 다 CPython 구현 세부이고, 정본은 [02-is-vs-eq-interning](../02-is-vs-eq-interning/2-summary.md) 이다.\
여기서 기억할 것은 **바인딩 쪽 결론 하나**다 — 「이름표 둘이 같은 상자에 붙었는지」는 **내가 쓴 코드가 아니라 컴파일러가 정한다.**

### (6) 기본 인자가 호출마다 새로 만들어진다고 믿는다

```python
def add(item, bag=[]):
    bag.append(item)
    return bag
```

기본값은 **`def` 문을 실행할 때 한 번** 평가된다. 그래서 호출마다 **같은 리스트**가 건네진다.\
이 절의 「이름표 모델」이 그대로 적용된 자리다 — 함수 객체가 그 리스트에 이름표를 붙들고 있다.\
정본은 [20-mutable-default-args](../20-mutable-default-args/2-summary.md) 이고, 고치는 법은 `bag=None` 센티널이다.

## 구현 세부사항 대 언어 보장

**이 주제에서 가장 중요한 구분이다.** 세 층으로 가른다.

| 층 | 무엇인가 | 어떻게 확인했나 |
|---|---|---|
| **언어 보장** | 언어 레퍼런스가 정한 것 | 공식 문서 문장을 열어서 인용 |
| **CPython 구현** | 이 구현이 그렇게 하는 것 | 실행 + `dis`·`sys` 로 확인 |
| **이 판의 관찰** | 3.12.3 에서 그랬을 뿐 | 「관찰」로 명기 |

### 언어 보장

| 사실 | 근거 |
|---|---|
| 모든 객체는 정체·타입·값을 가지고, 정체는 만들어진 뒤 변하지 않는다 | 데이터 모델 3.1 |
| `is` 는 정체를 비교하고 `id()` 는 정체를 나타내는 정수를 돌려준다 | 데이터 모델 3.1 |
| 대입은 이름을 객체에 묶는다 — 이름을 묶는 구문의 목록이 정해져 있다 | 실행 모델 4.2 |
| 블록 안에서 이름이 묶이면 그 이름은 그 블록의 지역 변수다 | 실행 모델 4.2 |
| 블록 안 **어디에든** 바인딩이 있으면 그 블록의 모든 사용이 지역 참조로 취급된다 | 실행 모델 4.2 |
| `del` 의 의미는 이름을 **푸는** 것이다 | 실행 모델 4.2 / 7.5 |
| `global` 은 최상위 네임스페이스, `nonlocal` 은 가장 가까운 바깥 **함수** 스코프를 가리킨다 | 실행 모델 4.2 |
| 인자는 **대입으로** 전달되며 호출자와 피호출자 사이에 별칭은 없다 | Programming FAQ |
| **불변** 타입에서는 새 값을 계산하는 연산이 같은 값의 기존 객체를 돌려줘도 된다. **가변** 타입에서는 그것이 허용되지 않는다 | 데이터 모델 3.1 |

★ 마지막 줄이 이 갈래의 열쇠다. 언어는 **인터닝을 허용**할 뿐, **어떤 값을 인터닝하라고 정하지 않는다.**

### CPython 구현 세부사항

| 사실 | 어떻게 확인했나 |
|---|---|
| `id()` 가 메모리 주소다 | `id()` 문서의 "CPython implementation detail" 표시 |
| 한 컴파일 단위 안의 같은 상수가 하나의 객체로 합쳐진다 | 파일에서 `a is b` 가 `True`, 모듈을 나누면 `False` |
| 식별자 모양 문자열이 자동으로 인터닝된다 | `"helloworld"` 는 모듈이 달라도 `True`, `"hello world"` 는 `False` |
| `"hel" + "lo"` 가 컴파일 시점에 접힌다(상수 접기) | 파일에서 `a is c` 가 `True`, 대화형에서 `False` |
| `-5` \~ `256` 정수가 미리 만들어져 재사용된다 | C API 문서가 "the current implementation" 이라고 적는다 ([02번](../02-is-vs-eq-interning/2-summary.md) 정본) |
| 참조 카운팅으로 회수하므로 `sys.getrefcount` 가 존재한다 | 이 함수 자체가 CPython 전용이다 |
| 마지막 참조가 사라지면 **즉시** 회수된다 | 참조 카운팅의 결과이지 명세가 아니다 |

### 이 판(3.12.3)의 관찰 — 버전이 오르면 다시 찍어야 한다

| 관찰 | 어디가 흔들리나 |
|---|---|
| 지역 이름 읽기가 `LOAD_FAST_CHECK` 로 컴파일된다 | 3.11 이전에는 `LOAD_FAST` 였다. **에러 종류는 같다** |
| `a = b = []` 이 `BUILD_LIST` + `COPY 1` 로 컴파일된다 | 명령 이름과 개수는 컴파일러가 정한다 |
| `UnboundLocalError` 메시지가 `cannot access local variable 'x' where it is not associated with a value` 다 | 3.11 에서 문구가 바뀐 적이 있다 |
| `sys.getrefcount(object())` 가 `1` 이다 | 인터프리터가 인자를 붙드는 방식에 달려 있다 |
| `id()` 값이 `123395548539968` 같은 15자리 정수다 | **실행할 때마다 다르다.** 값 자체는 아무 의미가 없다 |

### 그래서 이렇게 적으면 틀린다

- ✗ 「파이썬에서 변수는 객체의 **주소**를 담는다」\
  → `id()` 가 주소라는 것이 CPython 구현 세부다. 「**이름이 객체에 묶인다**」가 맞는 표현이다.
- ✗ 「같은 리터럴은 같은 객체다」\
  → 파일에서는 그렇고 대화형에서는 아니다. **컴파일 단위에 달렸다.**
- ✗ 「파이썬은 참조 전달이다」\
  → 문서 자신이 *"no call-by-reference per se"* 라고 부정한다. 「**대입으로 전달된다**」가 문서의 표현이다.
- ✗ 「`del` 은 객체를 삭제한다」\
  → 이름을 푸는 것이다. 객체 회수는 **마지막 참조가 사라졌을 때 따라오는 결과**다.

**판정 기준 한 줄**: 「두 이름이 같은 객체를 가리키는가」가 코드의 정상 동작에 필요하다면, 그 코드는 **내가 직접 만든 공유**에만 기대야 한다. **컴파일러가 만들어 준 공유에 기대면 구현 세부사항에 기댄 코드다.**

## 언제 쓰고 언제 안 쓰나

| 쓰는 것 | 상황 |
|---|---|
| `b = a` | 같은 객체를 **일부러** 공유할 때 — 캐시·레지스트리·순환 구조 |
| `b = list(a)` / `copy.deepcopy(a)` | 따로 쓰고 싶을 때 ([목록의 **03번 주제**](../03-mutability-and-copying/)) |
| `a, b = [], []` | 둘을 따로 쓸 게 확실할 때. `a = b = []` 보다 이쪽이 기본값이어야 한다 |
| `global` | 모듈 수준 설정을 딱 한 곳에서 갱신할 때. **되도록 안 쓰는 게 낫다** |
| `nonlocal` | 클로저가 상태를 들고 있어야 할 때 — 카운터·누산기 |
| `del` | 이름을 정말 없애고 싶을 때(루프 변수 정리, `__del__` 시점 제어 아님) |
| `id()` | 디버깅에서 「같은 객체인가」를 눈으로 볼 때. **판정은 `is` 로 한다** |

**안 쓰는 자리**는 한 문장이다.\
**`global` 로 상태를 주고받지 마라** — 함수 안에서 `global` 을 쓰고 싶어졌다면 대개 그 값을 인자로 받거나 반환해야 한다는 신호다.

## 핵심 문장

- 파이썬의 변수는 값을 담는 상자가 아니라 객체에 붙인 **이름표**다. 대입은 복사가 아니라 이름표를 붙이는 일이다.
- 그래서 **공유가 기본값**이다. 따로 쓰고 싶으면 복사를 따로 요청해야 한다.
- 함수 인자는 「값 전달」도 「참조 전달」도 아니라 **대입으로 전달된다** — 객체를 바꾸면 바깥에 보이고, 이름을 바꾸면 안 보인다.
- 읽기는 LEGB 로 찾고 **쓰기는 언제나 지역**이다. 이 비대칭 때문에 대입 한 줄이 이름을 통째로 지역으로 만들고 `UnboundLocalError` 가 난다 — `dis` 의 `LOAD_GLOBAL` 대 `LOAD_FAST_CHECK` 가 그 증거다.
- `del` 은 이름을 푸는 것이지 객체를 지우는 것이 아니다.
- 「같은 값이면 같은 객체」는 **컴파일 단위에 달린 CPython 구현 세부**다. 파일과 대화형에서 답이 뒤집힌다.

## 관련 자료

- 목록: [python/syntax 주제 목록](../README.md) — 이 주제는 **01번**
- 이어지는 곳: [02-is-vs-eq-interning](../02-is-vs-eq-interning/2-summary.md) — 이름표 둘이 한 상자에 붙었는지 **묻는 법**(`is` 대 `==`)과 인터닝. **인터닝의 정본은 그쪽**이고, 여기서는 바인딩으로 설명만 한다.
- 이어지는 곳: [목록의 **03번 주제**](../03-mutability-and-copying/) — 공유가 기본값이라서 필요해지는 **복사**
- 이어지는 곳: [20-mutable-default-args](../20-mutable-default-args/2-summary.md) — 기본 인자가 `def` 시점에 한 번 묶이는 것. **그 정본은 그쪽**이다.
- 이어지는 곳: 목록의 **21번 주제** 「스코프 LEGB 와 `global`·`nonlocal`」 · 목록의 **22번 주제** 「클로저와 늦은 바인딩」 — 이 절의 LEGB 를 **클로저 설계**까지 끌고 간다.
- 기존 노트: [`cs/foundations/variables-and-memory/`](../../../../variables-and-memory/README.md) — 같은 모델을 참조 카운트·가비지 컬렉션 쪽에서 다룬다.\
  **경계**: 그쪽은 「메모리가 언제 회수되나」까지, 여기는 「**이름이 언제 어디에 묶이나**」부터다.\
  ★ 그 문서는 한때 「파이썬은 -5\~254 를 캐싱한다」로 **값도 틀리고 구현 세부를 언어 사실로** 적고 있었다(2026-09-21 정정됨). **이 갈래에 「구현 세부사항 대 언어 보장」 절이 있는 이유가 그 사고다.**
- 연혁은 여기가 아니다: [`history/python/`](../../../../../../history/python/)
- 공식 문서: [3.1. Objects, values and types](https://docs.python.org/3.12/reference/datamodel.html) · [4.2. Naming and binding](https://docs.python.org/3.12/reference/executionmodel.html) · [7.2. Assignment statements](https://docs.python.org/3.12/reference/simple_stmts.html#assignment-statements)

## 용어 풀이

- **객체(object)**: 값과 타입을 가지고 메모리에 실제로 놓인 것 하나.\
  파이썬에서는 숫자·문자열·함수·클래스·모듈까지 전부 객체다.
- **이름(name)**: 객체에 붙이는 꼬리표. 저장 공간이 아니다.\
  그래서 「이름을 바꾼다」와 「객체를 바꾼다」가 완전히 다른 일이 된다.
- **바인딩(binding)**: 이름을 객체에 묶는 일.\
  대입·`def`·`class`·`import`·`for` 머리·`with ... as`·`except ... as` 가 한다.
- **정체(identity)**: 「메모리에 놓인 그것 자체」를 가리키는 표.\
  `is` 로 비교하고 `id()` 로 본다. 만들어진 뒤 변하지 않는다.
- **`id()`**: 객체의 정체를 나타내는 정수.\
  수명 동안 유일하고 변하지 않는다는 것만 보장되며, 그것이 메모리 주소라는 건 CPython 구현 세부다.
- **가변(mutable)**: 객체 자체의 값을 바꿀 수 있는 것. 리스트·딕셔너리·집합.
- **불변(immutable)**: 만들어진 뒤 값을 못 바꾸는 것. 정수·문자열·튜플·frozenset.\
  「바꾼다」고 쓰면 실제로는 **새 객체를 만들어 이름표를 옮기는** 것이다.
- **네임스페이스(namespace)**: 이름 → 객체 대응을 담은 표.\
  모듈 전역은 `globals()`, 함수 지역은 `locals()` 로 들여다볼 수 있다.
- **LEGB**: 이름을 찾는 순서 — Local → Enclosing → Global → Built-in.\
  읽기에만 적용된다. 쓰기는 언제나 지역이다.
- **`global`**: 「이 블록의 이 이름은 모듈 최상위의 그것」이라는 선언.
- **`nonlocal`**: 「이 블록의 이 이름은 가장 가까운 바깥 **함수**의 그것」이라는 선언.\
  모듈 최상위에는 쓸 수 없다.
- **`UnboundLocalError`**: 지역 이름인데 아직 아무 객체에도 안 묶인 상태에서 읽었을 때 나는 오류.\
  `NameError` 의 하위 클래스다.
- **`dis`**: 파이썬 코드가 어떤 바이트코드 명령으로 컴파일됐는지 보여 주는 표준 모듈.\
  「컴파일러가 실제로 무엇을 했나」를 지어낼 수 없게 만든다.
- **컴파일 단위(compilation unit)**: 한 번에 컴파일되는 소스 덩어리.\
  파일 하나가 한 단위이고, 대화형에서는 **입력 한 줄(한 문)** 이 한 단위다. 상수 합치기가 이 경계 안에서만 일어난다.
- **상수 접기(constant folding)**: `"hel" + "lo"` 처럼 컴파일 때 계산할 수 있는 식을 미리 계산해 하나의 상수로 만드는 최적화.
- **참조 카운트(reference count)**: 한 객체에 붙은 이름표·참조의 개수.\
  CPython 은 이것이 0이 되면 객체를 회수한다. `sys.getrefcount` 로 보되 **세는 행위가 1을 더한다.**
- **구현 세부사항(implementation detail)**: 언어 명세가 보장하지 않고 특정 구현이 그렇게 만들어 둔 것.\
  버전·구현이 바뀌면 달라질 수 있으므로 코드가 여기에 기대면 안 된다.

## 더 들어가면

- **클래스 본문은 스코프가 특이하다.** 클래스 본문에서 만든 이름은 메서드의 Enclosing 스코프가 **되지 않는다** — 그래서 메서드 안에서 클래스 변수를 그냥 이름으로 못 읽고 `self.` 나 클래스 이름을 거쳐야 한다(목록의 **29번 주제**).
- **컴프리헨션도 자기 스코프를 가진다**(Python 3 부터). 그래서 컴프리헨션 안에서 만든 이름이 바깥으로 새지 않는다([14-comprehensions](../14-comprehensions/2-summary.md)).
- **순환 참조는 참조 카운팅만으로 못 푼다.** 그래서 CPython 에 세대별 가비지 컬렉터(`gc` 모듈)가 따로 있다 — 그쪽은 [`cs/foundations/memory-management/`](../../../../memory-management/) 의 몫이다.
