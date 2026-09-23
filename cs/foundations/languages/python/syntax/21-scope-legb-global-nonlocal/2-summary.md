# python/syntax/21-scope-legb-global-nonlocal — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **이 본문은 원고가 아니라 Claude 작성이다**(문법·API 갈래는 원고 없이 공식 문서로 접지한다).
>
> ★★ **이 주제는 사슬의 첫 고리다.** [22번](../22-closures-and-late-binding/2-summary.md)(클로저)·[23번](../23-lambda-and-higher-order-functions/2-summary.md)(`lambda`)·[24번](../24-decorators/2-summary.md)(데코레이터)이 전부 **여기서 정한 「이름이 어디서 풀리나」 위에 선다.**
> 여기가 흔들리면 그 셋이 전부 외우기가 된다.
>
> **기준 소스** — 열어서 확인한 것만.
> - [4.2. Naming and binding](https://docs.python.org/3.12/reference/executionmodel.html#naming-and-binding) — 무엇이 이름을 묶나, 지역 변수 규칙
> - [4.2.2. Resolution of names](https://docs.python.org/3.12/reference/executionmodel.html#resolution-of-names) — 이름 해소 순서 · `UnboundLocalError`
> - [4.2.3. Builtins and restricted execution](https://docs.python.org/3.12/reference/executionmodel.html#builtins-and-restricted-execution) — 내장 스코프
> - [7.12. The `global` statement](https://docs.python.org/3.12/reference/simple_stmts.html#the-global-statement) · [7.13. The `nonlocal` statement](https://docs.python.org/3.12/reference/simple_stmts.html#the-nonlocal-statement)
> - [8.8. Class definitions](https://docs.python.org/3.12/reference/compound_stmts.html#class-definitions) — 클래스 블록의 스코프
> - [PEP 227 — Statically Nested Scopes](https://peps.python.org/pep-0227/) · [PEP 3104 — Access to Names in Outer Scopes](https://peps.python.org/pep-3104/) · [PEP 709 — Inlined comprehensions](https://peps.python.org/pep-0709/)
>
> **실행 검증** — 이 문서에 실린 출력은 전부 `python3` **3.12.3**(Linux)에서 실제로 돌려 나온 것이다. 지어낸 출력은 없다.\
> ★ **던지는 형태를 하나로 고정했다** — `python3 - <파일` 로 던져 트레이스백이 `File "<stdin>", line N` 이 된다.\
> ★ **소스 펜스의 첫 줄은 캡처가 붙인 파일명 주석**이다. 트레이스백의 줄 번호는 **그 주석을 뺀 실파일 기준**이라 펜스에서는 한 줄 아래를 보면 된다.\
> **버전** — `nonlocal` 은 **3.0+**(PEP 3104), 중첩 스코프 자체는 **2.2+**(PEP 227).
> 컴프리헨션이 자기 스코프를 갖는 것은 **Python 3 전체 공통**이고, 그 **인라인화는 3.12+**(PEP 709)다.
> 바이트코드 명령 이름(`LOAD_FAST_CHECK` 등)은 **3.12 의 것**이라 판마다 다르다.\
> **구현 대 언어 보장 한 줄** — **「블록 안 어디든 대입이 있으면 그 블록 안의 모든 사용이 지역 참조가 된다」는 언어 보장**이고,
> **`LOAD_FAST_CHECK`·`co_varnames`·`dis` 출력은 CPython 구현**이다. 같은 사실을 둘이 다른 층에서 말한다.\
> **★ 흔들리는 칸 / 안 흔들리는 칸** — 제출 전 재대조에서 「고칠 것」과 「설계상 안 맞는 것」을 기계적으로 가르려고 미리 선언한다.
>
> | | 무엇 |
> |---|---|
> | **흔들린다** | `<cell at 0x…>`·`<function … at 0x…>` 의 **주소**, `id()` 값 |
> | **안 흔들린다** | 예외 **타입**과 **메시지 본문**, `File "<stdin>", line N`, **셀 개수**, `is` 판정, `co_freevars`·`co_varnames`, `__defaults__` 값, `(exit N)` |
>
> ★ **이 주제의 블록에는 주소가 한 칸도 없다** — 전부 결정적이라 같은 판에서 다시 돌리면 한 글자도 안 변한다.

```python
# v_version.py
import sys

print("version_info =", sys.version_info)
print("implementation =", sys.implementation.name)
print("platform =", sys.platform)
```

```text
===== python3 - <v_version.py =====
version_info = sys.version_info(major=3, minor=12, micro=3, releaselevel='final', serial=0)
implementation = cpython
platform = linux
(exit 0)
```

## 한눈에 — 쉽게 말하면

**이름을 찾는 일은 「사다리를 아래에서 위로 올라가는 것」이고, 대입 한 줄은 「그 사다리의 맨 아랫칸을 새로 만드는 것」이다.**

```text
   이름 하나를 읽을 때 파이썬이 훑는 순서 — 아래에서 위로

        ┌──────────────────────────────┐
     B  │ Built-in   len · print · str │   마지막
        ├──────────────────────────────┤
     G  │ Global     그 모듈의 꼭대기   │
        ├──────────────────────────────┤
     E  │ Enclosing  나를 감싼 함수들   │
        ├──────────────────────────────┤
     L  │ Local      지금 이 함수 안    │   먼저
        └──────────────────────────────┘

   먼저 찾은 곳에서 멈춘다. 끝까지 없으면 NameError.
```

★★ **그런데 이 사다리의 맨 아랫칸(L)에 무엇이 들어가는지는 「실행 중에 정해지는 것」이 아니다.**\
**함수 안 어디든 그 이름에 대입이 한 줄 있으면, 그 함수 전체에서 그 이름은 지역 변수다** — 대입보다 **앞줄에서 읽어도** 그렇다.\
그래서 아직 값이 안 들어간 채 읽으면 `NameError` 가 아니라 **`UnboundLocalError`** 가 난다.

```text
   count = 10                     ← 전역에 있다

   def bump():
       print(count)               ← ★ 여기서 터진다 (아직 값이 없다)
       count = count + 1          ← 이 한 줄 때문에 count 가 "지역"이 됐다

   사다리가 이렇게 잘린다:
        L 에 count 가 "있다" 고 못 박혀서  →  G 의 10 을 보러 올라가지 않는다
```

**비유 대응표** — 이 문서는 끝까지 이 대응을 지킨다.

| 비유 | 실체 | 확인하는 법 |
|---|---|---|
| 사다리를 아래에서 위로 | LEGB 이름 해소 | 각 층에 같은 이름을 두고 가려 본다 |
| 맨 아랫칸을 새로 만드는 일 | **블록 안의 대입** | `함수.__code__.co_varnames` 에 이름이 들어간다 |
| 칸은 있는데 아직 비었다 | **바인딩 안 된 지역** | **`UnboundLocalError`** |
| 칸 자체가 없다 | 어느 층에도 없는 이름 | `NameError` |
| "나는 G 칸에 쓴다" 선언 | `global` | 없던 전역 이름도 **만든다** |
| "나는 E 칸에 쓴다" 선언 | `nonlocal` | **이미 있어야** 한다. 없으면 `SyntaxError` |
| 사다리에서 빠지는 층계참 | **클래스 몸통** | 메서드에서 클래스 변수를 **이름만으로 못 읽는다** |
| 상자 안의 작은 방 | **컴프리헨션** | 루프 변수가 밖에 **안 남는다** |

**똑같은 구조다** — 실무에서 이게 물리는 자리도 굳어 있다.\
「**카운터를 하나 올리려고 `count += 1` 을 넣었더니 `UnboundLocalError` 가 났다**」와
「**클래스 안에서 클래스 변수를 이름으로 읽었더니 `NameError` 가 났다**」가 그것이다.
둘 다 **실행 전에 컴파일러가 이미 정해 둔 것**이고, 그래서 코드를 노려봐도 안 보인다.

> **스코프(scope)** — 한 이름이 그 이름만으로 통하는 범위.\
> 예: 함수 안에서 만든 `x` 는 그 함수 안에서만 `x` 다. 밖에서는 없는 이름이다.

> **바인딩(binding)** — 이름을 객체에 묶는 일.\
> 예: `=` 만이 아니라 `def`·`class`·`import`·`for`·`with … as`·`except … as`·함수 파라미터가 전부 바인딩이다.

## 이 주제가 답하려는 질문

1. **이름이 어느 층에서 풀리나** — 같은 이름이 네 층에 다 있으면 무엇이 이기고, `del` 로 하나를 치우면 어떻게 되나.
2. **★ 왜 대입 한 줄이 위층을 가려 버리나** — 그리고 왜 **대입한 줄이 아니라 그 앞의 읽는 줄**에서 터지나.
3. **바깥 이름을 쓰려면 무엇을 선언하나** — `global` 과 `nonlocal` 이 무엇이 다르고, `nonlocal` 이 **안 되는 자리**는 어디인가.

## 동작 방식

> 이 절이 본문이다. **그림을 먼저 두고 그 그림을 문장으로 읽는다.**\
> 이 주제의 네 번째 창은 **코드 객체**다 — `co_varnames`·`co_freevars`·`co_names` 와 `dis`.
> **어떤 이름이 어디서 풀리는지는 던져서**, **왜 그렇게 풀리는지는 코드 객체로** 본다.
> ★ 단 코드 객체와 `dis` 는 **CPython 구현**이다. 나올 때마다 표시한다.

### 1. LEGB — 네 층을 각각 가려 본다

**언제 쓰나** — 「이 이름이 어디 것이지」를 물을 때. 모든 판정의 출발점.

먼저 **L 이 있을 때와 없을 때**만 갈라 본다. 나머지 층은 그대로 둔다.

```python
# e21_legb.py
name = "G: 전역"


def outer():
    name = "E: 둘러싼 함수"

    def inner():
        name = "L: 지역"
        print("L 이 있을 때 :", name)

    def inner_no_local():
        print("L 이 없을 때 :", name)

    inner()
    inner_no_local()


outer()
print("전역에서     :", name)
print("내장에서     :", len)
```

```text
===== python3 - <e21_legb.py =====
L 이 있을 때 : L: 지역
L 이 없을 때 : E: 둘러싼 함수
전역에서     : G: 전역
내장에서     : <built-in function len>
(exit 0)
```

그림 해설 — 한 단계에 한 문장.

```text
   name = "G: 전역"                 G 칸에 하나
   def outer():
       name = "E: 둘러싼 함수"       E 칸에 하나
       def inner():
           name = "L: 지역"          L 칸에도 하나  →  L 이 이긴다
       def inner_no_local():
           print(name)               L 칸이 비었다  →  한 칸 올라가 E 를 쓴다
```

- **`inner` 는 자기 `name` 을 본다** — 같은 이름이 위에 두 개 더 있어도 **올라가지 않는다.**
- **`inner_no_local` 은 E 를 본다** — G 가 아니다. **가장 가까운 층에서 멈춘다.**
- **`len` 은 아무도 안 가려서 B 층까지 올라갔다** — `<built-in function len>`.

레퍼런스가 그 규칙을 한 문장으로 적는다 —
*"When a name is used in a code block, it is resolved using the nearest enclosing scope."*

이번에는 **네 층을 차례로 가려** 본다. 가리는 이름으로 일부러 `len` 을 썼다.

```python
# e21_legb_shadow.py
print("① 아무것도 안 가렸을 때:", len("abcd"))

len = "G 가 내장을 가렸다"


def outer():
    len = "E 가 G 를 가렸다"

    def inner_uses_enclosing():
        print("③ E:", len)

    def inner_has_local():
        len = "L 이 E 를 가렸다"
        print("④ L:", len)

    inner_uses_enclosing()
    inner_has_local()


print("② G:", len)
outer()
del len
print("⑤ del 뒤 다시 내장:", len("abcd"))
```

```text
===== python3 - <e21_legb_shadow.py =====
① 아무것도 안 가렸을 때: 4
② G: G 가 내장을 가렸다
③ E: E 가 G 를 가렸다
④ L: L 이 E 를 가렸다
⑤ del 뒤 다시 내장: 4
(exit 0)
```

그림 해설.

```text
   ①  len("abcd") = 4            아무도 안 가렸다            → B
   ②  len = "G 가 …"             모듈 꼭대기에서 가렸다        → G 가 B 를 덮는다
   ③  outer 의 len               함수가 가렸다                → E 가 G 를 덮는다
   ④  inner 의 len               더 안쪽 함수가 가렸다         → L 이 E 를 덮는다
   ⑤  del len  후 len("abcd")    G 칸의 이름표를 떼어냈다      → 다시 B 가 보인다
```

★★ **⑤ 가 이 절의 결론이다.** `del len` 은 **내장 `len` 을 지운 것이 아니라 전역 칸의 이름표를 뗀 것**이다.
그러니 사다리가 한 칸 더 올라가 **내장을 다시 찾는다.**

> **가림(shadowing)** — 아래층에 같은 이름이 있어서 위층 이름이 안 보이게 되는 것.\
> 예: 모듈 꼭대기에 `list = [1, 2]` 를 두면 그 모듈 전체에서 내장 `list` 를 못 쓴다.

**비용** — 규칙이 한 줄이라 판정이 기계적이다.\
대신 **내장 이름을 가리면 조용히 망가진다** — 가리는 그 줄은 아무 말도 안 하고, 문제는 **한참 뒤** `len(...)` 을 부를 때 드러난다. **원인과 증상이 멀어진다.**

### 2. ★★ 대입 한 줄이 지역 변수를 만든다 — 이 주제의 심장

**언제 쓰나** — 「읽기만 하려던 참인데 왜 터지지」를 물을 때.

```python
# e21_unbound.py
count = 10


def bump():
    print("읽기만 하려던 참이다:", count)
    count = count + 1
    return count


bump()
```

```text
===== python3 - <e21_unbound.py =====
Traceback (most recent call last):
  File "<stdin>", line 10, in <module>
  File "<stdin>", line 5, in bump
UnboundLocalError: cannot access local variable 'count' where it is not associated with a value
(exit 1)
```

★★ **`print` 줄에서 터졌다.** 트레이스백이 `line 5` 를 가리키는데, **대입은 6번 줄**에 있다.\
그리고 **`읽기만 하려던 참이다:` 라는 문구가 한 글자도 안 찍혔다** — 터진 자리가 바로 그 `print` 의 인자를 만드는 중이다.

```text
   def bump():
       print(count)        ← line 5  ★ 여기서 UnboundLocalError
       count = count + 1   ← line 6     대입은 여기에 있다
       return count

   읽는 줄이 먼저인데 왜?
        ┌ 파이썬은 함수를 "컴파일할 때" 이 블록의 지역 이름 목록을 먼저 확정한다
        ├ count 에 대입이 있다  →  count 는 이 블록의 지역 변수다 (줄 순서 무관)
        └ 그러면 5번 줄의 count 도 "지역 count" 를 읽는 것이 된다  →  아직 비었다
```

★ **언어 보장이다** — 레퍼런스가 평서문으로 적는다.

> If a name is bound in a block, it is a local variable of that block, unless declared as
> nonlocal or global. … If a variable is used in a code block but not defined there, it is a free variable.

그리고 **「어디든」** 이라는 낱말이 이 절의 전부다.

> If a name binding operation occurs anywhere within a code block, all uses of the name within
> the block are treated as references to the current block.

즉 **대입이 블록 안 어디에 있든** — 마지막 줄이든, 안 도는 `if` 안이든 — **그 블록의 모든 사용이 지역 참조**가 된다.

그래서 나는 예외의 **종류**도 레퍼런스에서 읽을 수 있다.

> When a name is not found at all, a NameError exception is raised. If the current scope is a
> function scope, and the name refers to a local variable that has not yet been bound to a value
> at the point where the name is used, an UnboundLocalError exception is raised.
> UnboundLocalError is a subclass of NameError.

그 **하위 관계**를 실제로 확인한 것.

```python
# e21_error_hierarchy.py
print("UnboundLocalError 의 조상:", UnboundLocalError.__mro__)
print("NameError 의 하위인가   :", issubclass(UnboundLocalError, NameError))


def f():
    try:
        print(v)
        v = 1
    except NameError as e:
        print("NameError 로 잡혔다:", type(e).__name__)
        print("메시지             :", e)
        print("e.name             :", e.name)


f()
```

```text
===== python3 - <e21_error_hierarchy.py =====
UnboundLocalError 의 조상: (<class 'UnboundLocalError'>, <class 'NameError'>, <class 'Exception'>, <class 'BaseException'>, <class 'object'>)
NameError 의 하위인가   : True
NameError 로 잡혔다: UnboundLocalError
메시지             : cannot access local variable 'v' where it is not associated with a value
e.name             : None
(exit 0)
```

그림 해설.

```text
   BaseException
     └ Exception
         └ NameError                ← "그런 이름이 없다"
             └ UnboundLocalError    ← "이름 칸은 있는데 아직 비었다"

   except NameError:  로 잡으면 둘 다 잡힌다.
```

- **`UnboundLocalError` 는 `NameError` 의 하위**다 — `except NameError` 로 **잡힌다.**
  잡아 놓고 `type(e).__name__` 을 찍어야 어느 쪽인지 안다.
- ★ **`e.name` 이 `None` 이다.** `NameError` 에는 어느 이름이 문제였는지 담는 `name` 속성이 있는데,
  **`UnboundLocalError` 쪽은 안 채워져 있었다**(3.12.3 관찰). 메시지 본문에는 `'v'` 가 들어 있다 —
  **문구를 파싱하지 않고 이름을 얻는 길이 이 경우엔 없다.**

**비용** — 규칙이 정적이라 컴파일러가 최적화할 수 있다(동작 10).\
대신 **「읽기만 할 생각이었다」가 통하지 않는다** — 같은 함수 안에서 그 이름에 손을 대는 순간 위층과의 연결이 끊긴다.

### 3. ★ 왜 그런가 — 컴파일이 이미 갈라 놓았다 (CPython 구현)

**언제 쓰나** — 위 규칙을 **눈으로** 확인하고 싶을 때. 외우지 말고 보고 싶을 때.

같은 `print(count)` 한 줄이 **함수에 대입이 있느냐 없느냐**로 다른 명령이 된다.

```python
# e21_unbound_dis.py
import dis

count = 10


def bump():
    print(count)
    count = count + 1


def just_read():
    print(count)


print("bump.__code__.co_varnames  =", bump.__code__.co_varnames)
print("just_read.__code__.co_varnames =", just_read.__code__.co_varnames)
print("--- dis.dis(bump) ---")
dis.dis(bump)
print("--- dis.dis(just_read) ---")
dis.dis(just_read)
```

```text
===== python3 - <e21_unbound_dis.py =====
bump.__code__.co_varnames  = ('count',)
just_read.__code__.co_varnames = ()
--- dis.dis(bump) ---
  6           0 RESUME                   0

  7           2 LOAD_GLOBAL              1 (NULL + print)
             12 LOAD_FAST_CHECK          0 (count)
             14 CALL                     1
             22 POP_TOP

  8          24 LOAD_FAST                0 (count)
             26 LOAD_CONST               1 (1)
             28 BINARY_OP                0 (+)
             32 STORE_FAST               0 (count)
             34 RETURN_CONST             0 (None)
--- dis.dis(just_read) ---
 11           0 RESUME                   0

 12           2 LOAD_GLOBAL              1 (NULL + print)
             12 LOAD_GLOBAL              2 (count)
             22 CALL                     1
             30 POP_TOP
             32 RETURN_CONST             0 (None)
(exit 0)
```

그림 해설 — **같은 소스 줄, 다른 명령.**

```text
   def bump():            대입이 있다
       print(count)   ->  LOAD_FAST_CHECK  0 (count)   ★ "지역 칸을 읽되 비었으면 터져라"
       count = ...    ->  STORE_FAST       0 (count)
       co_varnames = ('count',)                        ★ 지역 이름 목록에 들어 있다

   def just_read():       대입이 없다
       print(count)   ->  LOAD_GLOBAL      2 (count)   ★ 아예 전역을 보러 간다
       co_varnames = ()                                ★ 지역 이름이 하나도 없다
```

- ★ **`co_varnames` 가 판정 결과 그 자체다.** `bump` 에는 `('count',)` 가 들어 있고 `just_read` 에는 비어 있다 —
  **함수를 만들 때 이미 갈라졌다.** 실행 중에 정해지는 것이 아니다.
- ★ **명령 이름이 다르다** — `LOAD_FAST_CHECK`(지역 칸을 읽되 비었으면 예외) 대 `LOAD_GLOBAL`(전역·내장을 보러 간다).
  **`UnboundLocalError` 를 던지는 주체가 바로 `LOAD_FAST_CHECK`** 다.
- ★★ **여기서 층을 갈라라** — 「대입이 지역을 만든다」는 **언어 보장**이고,
  **`LOAD_FAST_CHECK` 라는 명령 이름과 `co_varnames` 라는 저장 위치는 CPython 3.12 의 구현**이다.
  다른 구현·다른 판은 같은 규칙을 다른 방법으로 지킬 수 있다.

**비용** — 지역 변수 접근이 **배열 인덱스 한 번**이 된다(이름 사전 조회가 아니다).\
대신 **그 대가가 이 주제의 함정 전부**다 — 목록을 미리 못 박았으니 줄 순서로 봐주지 않는다.

### 4. `global` — 모듈 칸에 쓰고, 없던 이름도 만든다

**언제 쓰나** — 함수 안에서 모듈 수준 이름을 **바꿔야** 할 때. (읽기만 할 거면 필요 없다.)

```python
# e21_global.py
count = 10


def bump_global():
    global count
    count = count + 1
    return count


print("전:", count)
print("반환:", bump_global())
print("후:", count)


def make_new():
    global freshly_made
    freshly_made = "전역에 없던 이름을 만들었다"


print("make_new 전, 전역에 있나:", "freshly_made" in globals())
make_new()
print("make_new 후, 전역에 있나:", "freshly_made" in globals())
print("값:", freshly_made)
```

```text
===== python3 - <e21_global.py =====
전: 10
반환: 11
후: 11
make_new 전, 전역에 있나: False
make_new 후, 전역에 있나: True
값: 전역에 없던 이름을 만들었다
(exit 0)
```

그림 해설.

```text
   global 없이            def bump(): count = count + 1
                          └ count 가 지역이 된다  →  UnboundLocalError (동작 2)

   global 을 쓰면         def bump_global():
                              global count          ← "이 블록에서 count 는 G 칸이다"
                              count = count + 1
                          ┌────────────┐
                          │ G: count   │ ◀── 읽기도 쓰기도 전부 이 칸
                          └────────────┘

   없던 이름도 만든다      global freshly_made ; freshly_made = "…"
                          →  globals() 에 없던 이름이 생긴다
```

- ★ **`global` 은 「선언」이지 「대입」이 아니다** — 그 줄 자체는 아무 값도 안 만든다.
  `global freshly_made` 만 써 두고 대입을 안 하면 전역에는 여전히 아무것도 안 생긴다.
- ★ **없던 전역 이름을 만들 수 있다** — 실측에서 호출 전에는 `globals()` 에 없었고 호출 뒤에 생겼다.
  이것이 뒤의 `nonlocal` 과 **정확히 갈리는 자리**다(동작 5).
- ★ 레퍼런스의 제약 하나 — *"The global statement must precede all uses of the listed names."*
  **선언이 사용보다 앞서야** 한다. 어기면 `SyntaxError` 다(문법 절의 금지 사례).

**클래스 몸통에서 쓰면** 어떻게 되나. 「클래스 안이니 클래스 속성이 되겠지」가 틀린다.

```python
# e21_global_in_class.py
tag = "모듈 것"


class C:
    global tag
    tag = "클래스 몸통에서 global 로 바꿨다"
    local_only = "이건 클래스 속성"


print("모듈 tag :", tag)
print("C 에 tag 있나:", "tag" in vars(C))
print("C.local_only :", C.local_only)
```

```text
===== python3 - <e21_global_in_class.py =====
모듈 tag : 클래스 몸통에서 global 로 바꿨다
C 에 tag 있나: False
C.local_only : 이건 클래스 속성
(exit 0)
```

- ★★ **모듈의 `tag` 가 바뀌었고, `C` 에는 `tag` 가 안 생겼다.** 클래스 몸통도 **하나의 코드 블록**이라
  `global` 이 그 블록의 이름을 G 칸으로 돌려놓은 것뿐이다. 같은 몸통의 `local_only` 는 그대로 클래스 속성이 됐다.
- **한 블록 안에서 이름마다 목적지가 다르다** — `tag` 는 모듈로, `local_only` 는 클래스 네임스페이스로.

**비용** — 바깥 상태를 고칠 수 있다.\
대신 **함수의 입출력이 시그니처에 안 보이게 된다** — 테스트가 순서에 의존하게 되는 전형적인 원인이다.

### 5. `nonlocal` — 둘러싼 **함수**의 칸에 쓴다

**언제 쓰나** — 중첩 함수가 바깥 함수의 변수를 **고쳐야** 할 때. 클로저 카운터의 정본 도구다.

```python
# e21_nonlocal.py
def outer():
    n = 0

    def without_nonlocal():
        n = 100
        return n

    def with_nonlocal():
        nonlocal n
        n = 100
        return n

    print("시작 n =", n)
    print("nonlocal 없이 부른 뒤 반환:", without_nonlocal(), "· 바깥 n =", n)
    print("nonlocal 로 부른 뒤 반환  :", with_nonlocal(), "· 바깥 n =", n)


outer()
```

```text
===== python3 - <e21_nonlocal.py =====
시작 n = 0
nonlocal 없이 부른 뒤 반환: 100 · 바깥 n = 0
nonlocal 로 부른 뒤 반환  : 100 · 바깥 n = 100
(exit 0)
```

그림 해설 — **나란히 놓고 본다.**

```text
   nonlocal 없이                         nonlocal 로

   def outer():  n = 0                   def outer():  n = 0
     def inner():                          def inner():
         n = 100      ← 새 지역 칸            nonlocal n   ← "n 은 바깥 함수 칸이다"
         return n                            n = 100      ← 그 칸을 고친다
                                             return n

     ┌ E: n = 0     ┐ 그대로              ┌ E: n = 100   ┐ 바뀌었다
     └ L: n = 100   ┘ 함수가 끝나면 사라짐  └ (L 칸 없음)  ┘
```

- **반환값은 둘 다 `100`** 이다 — 안에서는 똑같아 보인다.
- **갈리는 것은 바깥 `n`** 이다. `0` 인가 `100` 인가. ★ **호출한 쪽에서만 보이는 차이**라 함수 안만 읽으면 못 잡는다.
- 레퍼런스의 정의 — *"The nonlocal statement causes corresponding names to refer to previously bound variables
  in the nearest enclosing function scope."* **「previously bound」가 다음 절의 전부다.**

**비용** — 바깥 함수의 상태를 안에서 고칠 수 있다(카운터·누산기).\
대신 **읽는 사람이 두 함수를 동시에 들고 있어야** 한다. 값 하나를 위해 중첩이 필요하면 클래스나 `itertools.count` 쪽이 읽기 쉬울 때가 많다.

### 6. ★★ `nonlocal` 이 안 되는 자리 — 자리 넷, 실측 다섯

**언제 쓰나** — `nonlocal` 을 썼는데 파일이 아예 안 뜰 때. **전부 `SyntaxError` 이고 컴파일 시점이라 한 줄도 안 돈다.**

레퍼런스가 그 사실을 직접 적는다 —
*"SyntaxError is raised at compile time if the given name does not exist in any enclosing function scope."*

**① 모듈 수준 — 이미 대입된 이름**

```python
# e21_nonlocal_module.py
x = 1
nonlocal x
```

```text
===== python3 - <e21_nonlocal_module.py =====
  File "<stdin>", line 2
SyntaxError: name 'x' is assigned to before nonlocal declaration
(exit 1)
```

**② 모듈 수준 — 대입이 없는 이름**

```python
# e21_nonlocal_top.py
def show():
    return "이 줄은 돌지 않는다"


nonlocal never_assigned_here
```

```text
===== python3 - <e21_nonlocal_top.py =====
  File "<stdin>", line 5
SyntaxError: nonlocal declaration not allowed at module level
(exit 1)
```

★ **같은 「모듈 수준」인데 문구가 갈린다.** 앞의 대입이 있었느냐가 갈림목이다.
그리고 ②의 `def show()` 는 **정의조차 안 됐다** — 파일 전체가 컴파일에 실패했다.

**③ 둘러싼 함수에 그 이름이 없을 때**

```python
# e21_nonlocal_missing.py
def outer():
    def inner():
        nonlocal never_bound
        never_bound = 1

    inner()
```

```text
===== python3 - <e21_nonlocal_missing.py =====
  File "<stdin>", line 3
SyntaxError: no binding for nonlocal 'never_bound' found
(exit 1)
```

**④ 전역에만 있는 이름일 때 — ③과 같은 메시지가 난다**

```python
# e21_nonlocal_global.py
g = 1


def only_global_exists():
    nonlocal g
    g = 2
```

```text
===== python3 - <e21_nonlocal_global.py =====
  File "<stdin>", line 5
SyntaxError: no binding for nonlocal 'g' found
(exit 1)
```

★★ **이것이 이 절의 핵심 대조다.** `g` 는 **분명히 존재하는 이름**인데도 `no binding for nonlocal 'g' found` 다.
`nonlocal` 이 보는 것은 **둘러싼 함수 스코프뿐**이고, **전역은 그 후보에 아예 없다.**
「없는 이름」과 「전역에만 있는 이름」이 **한 문장으로 합쳐져** 나온다.

**⑤ 함수 안에서 대입 뒤에 선언했을 때**

```python
# e21_nonlocal_after_assign.py
def outer():
    n = 0

    def inner():
        n = 1
        nonlocal n
        return n

    return inner()
```

```text
===== python3 - <e21_nonlocal_after_assign.py =====
  File "<stdin>", line 6
SyntaxError: name 'n' is assigned to before nonlocal declaration
(exit 1)
```

★ ①과 **같은 문구**다 — `assigned to before nonlocal declaration`. 선언은 **그 이름을 쓰기 전에** 와야 한다.

전수 표 — **메시지 본문까지 그대로.**

| # | 자리 | 블록이 보인 것 | `SyntaxError` 메시지 본문 |
|---|---|---|---|
| ① | **모듈 수준** · 이미 대입된 이름 | `x = 1` 뒤의 `nonlocal x` | `name 'x' is assigned to before nonlocal declaration` |
| ② | **모듈 수준** · 대입 없는 이름 | 함수 밖의 `nonlocal …` | `nonlocal declaration not allowed at module level` |
| ③ | **둘러싼 함수에 그 이름이 없다** | 어디에도 안 묶인 이름 | `no binding for nonlocal 'never_bound' found` |
| ④ | **전역에만 있다** | 모듈 꼭대기에만 있는 이름 | `no binding for nonlocal 'g' found` ★ ③과 **같다** |
| ⑤ | **대입 뒤에 선언** | 함수 안 `n = 1` 다음의 `nonlocal n` | `name 'n' is assigned to before nonlocal declaration` ★ ①과 **같다** |

★★ **읽을 것 넷.**

1. **자리는 넷인데 블록은 다섯**이다 — **모듈 수준이 두 갈래로 갈린다**(①·②). 앞에 대입이 있었느냐가 문구를 정한다.
2. **넷 중 둘이 같은 메시지**다 — ③과 ④가 `no binding for nonlocal 'x' found`.
   **「없다」와 「전역에만 있다」를 문구로는 구분할 수 없다.**
3. **다섯 전부 `SyntaxError` 이고 `(exit 1)` 이다.** `TypeError` 도 `NameError` 도 아니다 —
   **그 함수를 한 번도 안 불러도 파일이 안 뜬다.**
4. ★ **다섯 전부 캐럿이 없다.** 소스 줄도 안 나오고 `File "<stdin>", line N` 한 줄뿐이다 —
   **파서가 아니라 심볼 테이블 단계가 잡기 때문**이다. [19번](../19-function-argument-rules/2-summary.md)의
   `duplicate argument` 와 **같은 부류**다.

```text
   소스 글자 ──> 파서 ──────> AST ──> 심볼 테이블 ──> 컴파일 ──> 바이트코드 ──> 실행
                   │                      │
                   │                      └ ★ nonlocal 오류 5종 (캐럿 없음)
                   │                        · no binding for nonlocal 'x' found
                   │                        · assigned to before nonlocal declaration
                   │                        · not allowed at module level
                   └ SyntaxError (캐럿 있음 — 토큰 배열이 틀린 것)
```

**비용** — **배포 전에 100% 잡힌다.** 안 도는 가지에 넣어도 잡힌다.\
대신 **한 곳만 틀려도 그 파일 전체가 안 뜬다** — import 사슬에서 나면 무관한 기능까지 멈춘다.

### 7. ★★ 클래스 본문은 스코프 규칙이 다르다

**언제 쓰나** — 클래스 몸통에서 이름이 안 보일 때. 「왜 `self.` 를 붙여야 하지」를 물을 때.

```python
# e21_class_body.py
def outer():
    from_enclosing = "둘러싼 함수의 이름"

    class C:
        seen_in_body = from_enclosing
        class_var = "클래스 변수"
        print("클래스 몸통에서 읽기:", seen_in_body)

        def method(self):
            return class_var

    return C


C = outer()
print("클래스 속성으로는 보인다:", C.class_var)
print("이제 메서드를 부른다")
C().method()
```

```text
===== python3 - <e21_class_body.py =====
클래스 몸통에서 읽기: 둘러싼 함수의 이름
클래스 속성으로는 보인다: 클래스 변수
이제 메서드를 부른다
Traceback (most recent call last):
  File "<stdin>", line 18, in <module>
  File "<stdin>", line 10, in method
NameError: name 'class_var' is not defined. Did you mean: 'self.class_var'?
(exit 1)
```

그림 해설 — **클래스 몸통은 사슬에서 빠진다.**

```text
   def outer():
       from_enclosing = "…"            ┌ E 칸
       class C:                        │
           seen = from_enclosing       │ ★ 클래스 몸통은 E 를 본다  (된다)
           class_var = "클래스 변수"     │    └ 클래스 네임스페이스에 담긴다
           def method(self):           │
               return class_var        │ ★ 메서드는 그 칸을 못 본다  (NameError)
                                       │
   메서드가 이름을 찾을 때의 사다리:
        L(method)  →  E(outer)  →  G  →  B          ← C 의 몸통 칸이 없다
                      ^^^^^^^^
                      클래스 몸통을 건너뛴다
```

- ★ **클래스 몸통에서는 `from_enclosing` 이 읽혔다** — 몸통은 둘러싼 함수를 본다.
- ★★ **메서드에서는 `class_var` 가 `NameError`** 다. **바로 두 줄 위에 있는데** 못 읽는다.
  3.12 는 친절하게 `Did you mean: 'self.class_var'?` 까지 붙여 준다 — **답이 바로 그것**이다.
- ★ **`C.class_var` 로는 읽힌다** — 이름이 사라진 것이 아니라 **클래스 네임스페이스의 속성**이 됐을 뿐이다.
  **속성 조회(`C.x`·`self.x`)와 이름 해소(LEGB)는 서로 다른 기계**다.

레퍼런스가 그대로 적는다 — **언어 보장**이다.

> The scope of names defined in a class block is limited to the class block; it does not extend to
> the code blocks of methods. This includes comprehensions and generator expressions, but it does
> not include annotation scopes, which have access to their enclosing class scopes.

★ 그 *"This includes comprehensions"* 가 다음 블록에서 그대로 터진다.

```python
# e21_class_comprehension.py
class C:
    rows = [1, 2, 3]
    factor = 10
    doubled = [r * 2 for r in rows]
    print("첫 이터러블은 보인다:", doubled)
    scaled = [r * factor for r in rows]
```

```text
===== python3 - <e21_class_comprehension.py =====
첫 이터러블은 보인다: [2, 4, 6]
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
  File "<stdin>", line 6, in C
NameError: name 'factor' is not defined
(exit 1)
```

```text
   class C:
       rows = [1, 2, 3]
       factor = 10
       doubled = [r * 2 for r in rows]      ★ 된다 —  rows 는 "첫 이터러블" 이라
                                                      바깥(클래스 몸통)에서 평가돼 넘어온다
       scaled  = [r * factor for r in rows] ✗ NameError — factor 는 컴프리헨션 안에서
                                                          읽는 이름이라 클래스 칸을 못 본다
```

- ★★ **같은 줄의 두 이름이 갈린다** — `rows` 는 보이고 `factor` 는 안 보인다.
  **첫 `for` 의 이터러블만 바깥 스코프에서 평가**되고, 나머지 식은 컴프리헨션 자신의 스코프에서 돈다.
- ★ **트레이스백의 프레임이 `in C`** 다 — `in <listcomp>` 가 **아니다.** 3.12 가 인라인했기 때문이다(동작 8).

`nonlocal` 은 클래스 몸통에서도 **된다** — 클래스 몸통이 함수 스코프가 아닌데도.

```python
# e21_nonlocal_class.py
def outer():
    v = 1

    class C:
        nonlocal v
        v = 2

    return v


print(outer())
```

```text
===== python3 - <e21_nonlocal_class.py =====
2
(exit 0)
```

- ★ **클래스 몸통에서 `nonlocal v` 가 통했고 `outer` 의 `v` 가 `2` 가 됐다.**
  `nonlocal` 이 **안 되는 자리는 모듈 수준**이지(동작 6의 ②) 클래스 몸통이 아니다.
  **찾아 올라가는 대상이 「둘러싼 함수 스코프」인 것**이지 **쓰는 자리가 함수여야 하는 것**이 아니다.

**비용** — 클래스 몸통에서 바깥 값을 그대로 끌어다 쓸 수 있다(기본값·테이블 정의).\
대신 **메서드 쪽 규칙이 직관과 반대**여서 사고가 난다. 규칙은 하나다 — **클래스 변수는 이름이 아니라 속성으로 읽는다.**

### 8. 컴프리헨션은 자기 스코프를 갖는다 — 그리고 3.12 는 그것을 인라인한다

**언제 쓰나** — 「루프 변수가 밖에 남나」를 물을 때. 트레이스백이 한 줄 짧아 보일 때.

```python
# e21_comprehension_scope.py
i = "전역 i 는 그대로다"
squares = [i * i for i in range(4)]
print("결과:", squares)
print("전역 i:", i)


def f():
    total = 0
    vals = [total + n for n in range(3)]
    return vals, total


print("함수 안에서 읽기는 된다:", f())


def g():
    doubled = [n * 2 for n in range(3)]
    print("컴프리헨션 안 이름이 밖에 남나:", "n" in locals())


g()
```

```text
===== python3 - <e21_comprehension_scope.py =====
결과: [0, 1, 4, 9]
전역 i: 전역 i 는 그대로다
함수 안에서 읽기는 된다: ([0, 1, 2], 0)
컴프리헨션 안 이름이 밖에 남나: False
(exit 0)
```

그림 해설 — **상자 안의 작은 방.**

```text
   i = "전역 i 는 그대로다"
   squares = [i * i for i in range(4)]

   ┌ 모듈 스코프 ───────────────────────────┐
   │  i = "전역 i 는 그대로다"   ← 안 더럽혀진다 │
   │                                        │
   │   ┌ 컴프리헨션의 방 ─────────────┐      │
   │   │  i = 0, 1, 2, 3             │      │
   │   │  바깥 이름은 읽을 수 있다     │      │
   │   └─────────────────────────────┘      │
   │        └ 방이 닫히면 i 는 사라진다        │
   └────────────────────────────────────────┘
```

- **`i` 가 안 더럽혀졌다** — 같은 이름인데 전역 값이 그대로다. **Python 3 의 언어 보장**이다.
- **함수 안에서 바깥 지역을 읽는 것은 된다** — `total` 을 읽어 `[0, 1, 2]` 가 나왔다. **막힌 것은 쓰기 쪽이지 읽기가 아니다.**
- **`"n" in locals()` 이 `False`** — 루프 변수는 밖에 **안 남는다.**

그 **구현**이 3.12 에서 바뀌었다. 여기부터는 **CPython 구현**이다.

```python
# e21_comprehension_inline4.py
kinds = {
    "list": "[n for n in r]",
    "set": "{n for n in r}",
    "dict": "{n: n for n in r}",
    "gen": "(n for n in r)",
}
for label, expr in kinds.items():
    src = "def f(r):\n    return " + expr + "\n"
    ns = {}
    exec(compile(src, "<probe>", "exec"), ns)
    inner = [c.co_name for c in ns["f"].__code__.co_consts
             if hasattr(c, "co_name")]
    print("%-5s %-18s 별도 코드 객체: %s" % (label, expr, inner or "없음 (인라인)"))
```

```text
===== python3 - <e21_comprehension_inline4.py =====
list  [n for n in r]     별도 코드 객체: 없음 (인라인)
set   {n for n in r}     별도 코드 객체: 없음 (인라인)
dict  {n: n for n in r}  별도 코드 객체: 없음 (인라인)
gen   (n for n in r)     별도 코드 객체: ['<genexpr>']
(exit 0)
```

★★ **실측이 흔한 요약과 다르다.** 「3.12 는 **리스트** 컴프리헨션을 인라인한다」로 알려진 자리인데,
**list·set·dict 셋 다 별도 코드 객체가 없다**. 코드 객체가 남은 것은 **제너레이터 표현식 하나뿐**이다.

| 표기 | 별도 코드 객체 | 읽는 법 |
|---|---|---|
| `[n for n in r]` | 없음 | **인라인** |
| `{n for n in r}` | 없음 | **인라인** |
| `{n: n for n in r}` | 없음 | **인라인** |
| `(n for n in r)` | `<genexpr>` | ★ **인라인 대상이 아니다** |

★ **인라인화의 정본은 [14번](../14-comprehensions/2-summary.md)** 이다(list·dict·set 로 적혀 있다).
**제너레이터 표현식이 인라인 대상이 아니라는 쪽**은 [15번](../15-generator-expressions-lazy-eval/2-summary.md)을 본다.

바이트코드로도 같은 것이 보인다.

```python
# e21_comprehension_inline.py
import dis


def listcomp():
    return [n for n in range(3)]


def setcomp():
    return {n for n in range(3)}


def genexp():
    return (n for n in range(3))


for fn in (listcomp, setcomp, genexp):
    names = [c.co_name for c in fn.__code__.co_consts
             if hasattr(c, "co_name")]
    print(fn.__name__, "-> 안에 들어 있는 코드 객체:", names)

print("--- dis.dis(listcomp) ---")
dis.dis(listcomp)
print("--- dis.dis(setcomp) ---")
dis.dis(setcomp)
```

```text
===== python3 - <e21_comprehension_inline.py =====
listcomp -> 안에 들어 있는 코드 객체: []
setcomp -> 안에 들어 있는 코드 객체: []
genexp -> 안에 들어 있는 코드 객체: ['<genexpr>']
--- dis.dis(listcomp) ---
  4           0 RESUME                   0

  5           2 LOAD_GLOBAL              1 (NULL + range)
             12 LOAD_CONST               1 (3)
             14 CALL                     1
             22 GET_ITER
             24 LOAD_FAST_AND_CLEAR      0 (n)
             26 SWAP                     2
             28 BUILD_LIST               0
             30 SWAP                     2
        >>   32 FOR_ITER                 4 (to 44)
             36 STORE_FAST               0 (n)
             38 LOAD_FAST                0 (n)
             40 LIST_APPEND              2
             42 JUMP_BACKWARD            6 (to 32)
        >>   44 END_FOR
             46 SWAP                     2
             48 STORE_FAST               0 (n)
             50 RETURN_VALUE
        >>   52 SWAP                     2
             54 POP_TOP
             56 SWAP                     2
             58 STORE_FAST               0 (n)
             60 RERAISE                  0
ExceptionTable:
  28 to 44 -> 52 [2]
--- dis.dis(setcomp) ---
  8           0 RESUME                   0

  9           2 LOAD_GLOBAL              1 (NULL + range)
             12 LOAD_CONST               1 (3)
             14 CALL                     1
             22 GET_ITER
             24 LOAD_FAST_AND_CLEAR      0 (n)
             26 SWAP                     2
             28 BUILD_SET                0
             30 SWAP                     2
        >>   32 FOR_ITER                 4 (to 44)
             36 STORE_FAST               0 (n)
             38 LOAD_FAST                0 (n)
             40 SET_ADD                  2
             42 JUMP_BACKWARD            6 (to 32)
        >>   44 END_FOR
             46 SWAP                     2
             48 STORE_FAST               0 (n)
             50 RETURN_VALUE
        >>   52 SWAP                     2
             54 POP_TOP
             56 SWAP                     2
             58 STORE_FAST               0 (n)
             60 RERAISE                  0
ExceptionTable:
  28 to 44 -> 52 [2]
(exit 0)
```

- **`BUILD_LIST`·`LIST_APPEND` 와 `BUILD_SET`·`SET_ADD` 가 바깥 함수 코드에 그대로 펴져 있다** —
  `MAKE_FUNCTION` 도 `CALL` 도 없다.
- ★ **`LOAD_FAST_AND_CLEAR` 라는 명령이 루프 변수를 감싼다** — 인라인해 놓고도 **이름 격리를 유지하려고**
  바깥의 같은 이름을 잠깐 치워 두었다가 되돌려 놓는다. **성능은 인라인, 의미는 그대로**인 이유가 이것이다.

그 결과가 **트레이스백 모양**으로 드러난다.

```python
# e21_comprehension_frame.py
def boom_listcomp():
    return [1 / n for n in (1, 0)]


boom_listcomp()
```

```text
===== python3 - <e21_comprehension_frame.py =====
Traceback (most recent call last):
  File "<stdin>", line 5, in <module>
  File "<stdin>", line 2, in boom_listcomp
ZeroDivisionError: division by zero
(exit 1)
```

```python
# e21_comprehension_frame_set.py
def boom_setcomp():
    return {1 / n for n in (1, 0)}


boom_setcomp()
```

```text
===== python3 - <e21_comprehension_frame_set.py =====
Traceback (most recent call last):
  File "<stdin>", line 5, in <module>
  File "<stdin>", line 2, in boom_setcomp
ZeroDivisionError: division by zero
(exit 1)
```

```python
# e21_comprehension_frame_gen.py
def boom_genexp():
    return list(1 / n for n in (1, 0))


boom_genexp()
```

```text
===== python3 - <e21_comprehension_frame_gen.py =====
Traceback (most recent call last):
  File "<stdin>", line 5, in <module>
  File "<stdin>", line 2, in boom_genexp
  File "<stdin>", line 2, in <genexpr>
ZeroDivisionError: division by zero
(exit 1)
```

```text
   리스트 컴프리헨션      … in <module>  /  … in boom_listcomp          2줄
   세트 컴프리헨션        … in <module>  /  … in boom_setcomp           2줄
   제너레이터 표현식      … in <module>  /  … in boom_genexp
                                        /  ★ … in <genexpr>            3줄
```

- ★ **list·set 쪽에는 `<listcomp>`·`<setcomp>` 프레임 줄이 없다.** 인라인돼서 **자기 프레임을 안 갖는다.**
- ★ **제너레이터 표현식만 `in <genexpr>` 줄이 남는다.** 인라인 대상이 아니라서다.
- ★★ **층을 갈라라** — **「컴프리헨션이 자기 스코프를 갖는다」는 언어 보장**이고,
  **「그 스코프가 프레임을 갖느냐」는 CPython 3.12 의 구현**이다. 같은 판에서 두 사실이 다르게 움직였다.

**비용** — 프레임 하나가 사라져 호출 비용이 준다(PEP 709).\
★ **여기서 수치를 적지 않는다** — 이 문서는 `timeit` 을 안 돌렸다. 잰 수치는 [14번](../14-comprehensions/2-summary.md)이 PEP 근거로 싣는다.

### 9. 층마다 무엇이 보이나 — `locals()` · `globals()` · `co_freevars`

**언제 쓰나** — 디버깅 중에 「지금 여기서 무엇이 보이나」를 확인할 때.

```python
# e21_locals_globals.py
module_level = "M"


def outer():
    enclosing = "E"

    def inner():
        local = "L"
        print("inner 의 locals() :", sorted(locals()))
        print("자유 변수 co_freevars:", inner.__code__.co_freevars)
        print("전역에 module_level 있나:", "module_level" in globals())
        print("전역에 enclosing 있나  :", "enclosing" in globals())
        return local + enclosing

    print("outer 의 locals() :", sorted(locals()))
    print("inner() 반환:", inner())


outer()
print("모듈 locals() is globals():", locals() is globals())
```

```text
===== python3 - <e21_locals_globals.py =====
outer 의 locals() : ['enclosing', 'inner']
inner 의 locals() : ['enclosing', 'inner', 'local']
자유 변수 co_freevars: ('enclosing', 'inner')
전역에 module_level 있나: True
전역에 enclosing 있나  : False
inner() 반환: LE
모듈 locals() is globals(): True
(exit 0)
```

그림 해설 — **세 창이 다른 것을 말한다.**

```text
   module_level = "M"          G 칸
   def outer():
       enclosing = "E"         E 칸
       def inner():
           local = "L"         L 칸

   inner 에서 —
     locals()      ['enclosing', 'inner', 'local']   ★ 자유 변수까지 들어 있다
     co_freevars   ('enclosing', 'inner')            ★ 바깥에서 빌려 온 이름들
     globals()     module_level 은 있고 enclosing 은 없다
```

- ★★ **`inner` 의 `locals()` 에 `enclosing` 이 들어 있다.** 「지역」이라는 낱말만 보고
  **「이 함수가 만든 이름」으로 읽으면 틀린다** — `locals()` 는 **그 프레임에서 이름으로 닿는 것**을 보여 주고,
  자유 변수도 거기 포함된다.
- ★ **`co_freevars` 에 `inner` 자신이 들어 있다** — `inner` 안에서 `inner.__code__` 를 읽기 때문이다.
  **자기 이름을 쓰는 중첩 함수는 자기 자신을 자유 변수로 빌린다.**
- ★ **`enclosing` 은 `globals()` 에 없다.** E 칸은 **전역이 아니다** — 이것이 `nonlocal` 과 `global` 을 가르는 물리적 근거다.
- ★ **모듈 수준에서는 `locals() is globals()` 가 `True`** 다. 모듈에는 L 칸과 G 칸의 구분이 없다.

> **자유 변수(free variable)** — 어떤 블록에서 **쓰는데 그 블록에서 안 묶인** 이름.\
> 예: 위 `inner` 의 `enclosing`. 레퍼런스의 표현으로 *"used in a code block but not defined there"*.

**비용** — 실행 중 상태를 이름째 들여다볼 수 있다.\
대신 **`locals()` 의 반환은 함수 스코프에서 스냅샷**이다 — 거기에 대입해도 지역 변수가 안 바뀐다.

### 10. 네 층이 명령으로 어떻게 갈리나 (CPython 구현)

**언제 쓰나** — LEGB 를 **기계 수준에서 확인**하고 싶을 때. 그리고 그것이 구현임을 확인할 때.

```python
# e21_dis_four_loads.py
import dis

G = 1


def outer():
    E = 2

    def inner():
        L = 3
        return L + E + G + len("x")

    return inner


print("co_varnames :", outer().__code__.co_varnames)
print("co_freevars :", outer().__code__.co_freevars)
print("co_names    :", outer().__code__.co_names)
print("--- dis.dis(inner) ---")
dis.dis(outer())
```

```text
===== python3 - <e21_dis_four_loads.py =====
co_varnames : ('L',)
co_freevars : ('E',)
co_names    : ('G', 'len')
--- dis.dis(inner) ---
              0 COPY_FREE_VARS           1

  9           2 RESUME                   0

 10           4 LOAD_CONST               1 (3)
              6 STORE_FAST               0 (L)

 11           8 LOAD_FAST                0 (L)
             10 LOAD_DEREF               1 (E)
             12 BINARY_OP                0 (+)
             16 LOAD_GLOBAL              0 (G)
             26 BINARY_OP                0 (+)
             30 LOAD_GLOBAL              3 (NULL + len)
             40 LOAD_CONST               2 ('x')
             42 CALL                     1
             50 BINARY_OP                0 (+)
             54 RETURN_VALUE
(exit 0)
```

그림 해설 — **네 층, 그런데 명령은 셋.**

```text
   def inner():  return L + E + G + len("x")

     L   →  LOAD_FAST    0 (L)        co_varnames = ('L',)
     E   →  LOAD_DEREF   1 (E)        co_freevars = ('E',)     ← 셀로 빌려 온다
     G   →  LOAD_GLOBAL  0 (G)        co_names    = ('G', 'len')
     B   →  LOAD_GLOBAL  3 (len)      ★ G 와 같은 명령이다
```

★★ **여기서 전제를 하나 고쳐야 한다** — **네 층이 네 명령으로 갈리지 않는다.**
`G` 와 `len` 이 **둘 다 `LOAD_GLOBAL`** 이고, `co_names` 에도 나란히 들어 있다.

```text
   LOAD_GLOBAL 이 실행 시점에 하는 일

        globals() 에 있나?  ──예──>  그 값
              │
              아니오
              ↓
        builtins 에 있나?   ──예──>  그 값
              │
              아니오
              ↓
           NameError
```

- ★★ **B 층은 컴파일 시점에 갈리지 않는다** — **`LOAD_GLOBAL` 의 실행 시점 폴백**이다.
  동작 1의 ⑤(`del len` 뒤 내장이 다시 보인 것)가 **바로 이 폴백의 관찰**이다.
  전역에서 이름이 사라지자 같은 명령이 한 칸 더 가서 내장을 찾았다.
- ★ **`COPY_FREE_VARS` 가 함수 맨 앞에 있다** — E 층은 **셀을 복사해 들고 시작**한다.
  그 셀이 [22번](../22-closures-and-late-binding/2-summary.md)의 본체다. 여기서는 **「명령이 다르다」까지만** 본다.
- ★★ **전부 CPython 구현이다.** 「네 층이 있다」는 언어 보장이고, 「L 과 E 가 다른 명령이다」는 이 구현의 이야기다.

**비용** — L·E 는 인덱스 접근이라 빠르고, G·B 는 사전 조회다.\
★ **속도를 수치로 말하지 않는다** — 이 문서는 `timeit` 을 안 돌렸다. 말할 수 있는 것은 **명령이 다르다**는 사실뿐이다.

## 문법 — 형태와 규칙

```python
x = 1                      # 모듈 수준 바인딩 → G 칸

def f():
    y = 2                  # 대입 → L 칸. 이 블록 전체에서 y 는 지역이다
    print(x)               # 대입이 없으므로 G 를 읽는다

def g():
    global x               # "이 블록에서 x 는 G 칸이다" — 사용보다 앞서야 한다
    x = 99                 # 없던 전역 이름이면 만들어진다

def outer():
    n = 0
    def inner():
        nonlocal n         # "이 블록에서 n 은 가장 가까운 둘러싼 함수 칸이다"
        n += 1             # ★ n 이 이미 outer 에 있어야 한다
    inner()
    return n
```

규칙 여덟.

1. **읽기는 LEGB 순서**로 푼다 — L → E → G → B. **먼저 찾은 곳에서 멈춘다.**
2. ★ **블록 안 어디든 대입이 있으면 그 블록 안의 모든 사용이 지역 참조**다. **줄 순서와 무관**하다.
3. **값이 들어가기 전에 읽으면 `UnboundLocalError`** — `NameError` 의 **하위**다.
4. **`global` 은 그 이름을 모듈 칸으로 돌린다.** **없던 이름도 만든다.**
5. **`nonlocal` 은 가장 가까운 둘러싼 함수 칸으로 돌린다.** 그 이름이 **이미 있어야 한다.**
   없으면 **컴파일 시점의 `SyntaxError`** 다.
6. **둘 다 사용보다 앞에 와야** 한다. 대입 뒤에 선언하면 `SyntaxError`.
7. ★ **클래스 몸통의 이름은 메서드에서 이름으로 안 보인다.** 속성(`self.x`·`C.x`)으로 읽는다.
8. **컴프리헨션은 자기 스코프를 갖는다.** 단 **첫 `for` 의 이터러블만 바깥에서 평가**된다.

**금지 사례 — 두 층으로 갈라 적는다**

```python
# ① 컴파일 시점 — SyntaxError. 그 함수를 안 불러도 파일이 안 뜬다
#    (아래 주석의 문구는 전부 동작 6에서 실제로 받아 낸 것이다)
nonlocal never_assigned_here    # nonlocal declaration not allowed at module level
x = 1
nonlocal x                      # name 'x' is assigned to before nonlocal declaration
def outer():
    def inner():
        nonlocal never_bound    # no binding for nonlocal 'never_bound' found
g = 1
def only_global_exists():
    nonlocal g                  # no binding for nonlocal 'g' found   ★ 전역은 후보가 아니다
def outer2():
    n = 0
    def inner2():
        n = 1
        nonlocal n              # name 'n' is assigned to before nonlocal declaration

# ② 실행 시점 — 그 줄에 닿아야 난다 (문구는 동작 2·7에서 받아 낸 것이다)
count = 10
def bump():
    print(count)                # UnboundLocalError: cannot access local variable 'count' …
    count = count + 1
class C:
    class_var = "클래스 변수"
    def method(self):
        return class_var        # NameError: name 'class_var' is not defined. Did you mean: 'self.class_var'?
class D:
    rows = [1, 2, 3]
    factor = 10
    scaled = [r * factor for r in rows]   # NameError: name 'factor' is not defined
```

★★ **①과 ②를 가르는 기준은 「정의냐 호출이냐」가 아니라 「컴파일러가 보느냐 실행이 보느냐」다.**
`nonlocal` 오류는 **안 도는 가지에 넣어도** 파일을 못 띄우고, `UnboundLocalError` 는 **그 줄에 닿아야** 난다.
[19번](../19-function-argument-rules/2-summary.md)의 층 구분과 **같은 축**이다.

## 어디서 틀리나

### (1) 「읽기만 하니까 괜찮겠지」

★ **안 괜찮다.** 같은 함수 안 **어딘가에** 그 이름에 대입이 있으면 **읽는 줄도 지역 참조**다.
실측에서 **대입보다 앞줄인 `print` 에서** 터졌다.

### (2) `UnboundLocalError` 를 `NameError` 와 다른 것으로 안다

**하위 클래스**다. `except NameError` 로 **잡힌다.** 갈라 잡으려면 `except UnboundLocalError` 를 **먼저** 둔다.

### (3) `count += 1` 이면 괜찮을 줄 안다

**`+=` 도 대입이다.** `count = count + 1` 과 똑같이 `count` 를 지역으로 만든다.
★ 같은 사고가 `for count in …`·`with … as count`·`except … as count`·`import count` 에도 난다 — **전부 바인딩**이다.

### (4) `global` 없이 전역을 바꿀 수 있다고 안다

**못 바꾼다.** 대입하면 **지역 이름이 하나 새로 생길 뿐**이고 전역은 그대로다.\
★ 예외 하나 — **가변 객체의 내용을 고치는 것은 대입이 아니다.** `cfg["k"] = 1`·`xs.append(1)` 은 `global` 없이 된다.
바인딩이 아니라 **객체 조작**이기 때문이다([01번](../01-object-and-name-binding/2-summary.md)의 이름표 모델).

### (5) `nonlocal` 로 전역을 고치려 한다

★★ **`no binding for nonlocal 'g' found`** 다. **전역은 `nonlocal` 의 후보가 아니다.**
이름이 **분명히 있는데도** 「없다」는 문구가 나오는 자리라 헷갈린다. 전역이면 `global` 을 쓴다.

### (6) `nonlocal` 오류가 그 함수를 부를 때 날 줄 안다

★ **`SyntaxError` 이고 컴파일 시점**이라 **한 줄도 안 돈다.** 실측 ②에서는 그 위의 `def show()` 조차 정의되지 않았다.

### (7) 선언을 대입 뒤에 쓴다

`name 'n' is assigned to before nonlocal declaration` 이다. **`global` 도 같다** —
*"The global statement must precede all uses of the listed names."*

### (8) 클래스 몸통의 이름을 메서드에서 이름으로 읽는다

★★ **`NameError`** 다. 두 줄 위에 있어도 안 보인다. **`self.x`·`C.x`** 로 읽는다.
3.12 는 `Did you mean: 'self.class_var'?` 로 답까지 알려 준다.

### (9) 클래스 몸통의 컴프리헨션이 클래스 변수를 볼 줄 안다

★ **첫 이터러블만 보인다.** `[r * factor for r in rows]` 에서 **`rows` 는 되고 `factor` 는 `NameError`** 다.
레퍼런스가 *"This includes comprehensions and generator expressions"* 로 명시한 자리다.

### (10) 컴프리헨션 루프 변수가 밖에 남는 줄 안다

**Python 3 에서는 안 남는다.** `"n" in locals()` 이 `False` 였다. 전역 `i` 도 안 더럽혀졌다.

### (11) 「3.12 는 리스트 컴프리헨션만 인라인한다」로 외운다

★★ **실측은 list·set·dict 셋 다 인라인**이다. 코드 객체가 남은 것은 **제너레이터 표현식뿐**이다.
트레이스백에서도 `<listcomp>`·`<setcomp>` 줄이 없고 `<genexpr>` 줄만 남는다.

### (12) `locals()` 를 「이 함수가 만든 이름」으로 읽는다

★ **자유 변수도 들어 있다.** 실측에서 `inner` 의 `locals()` 에 바깥의 `enclosing` 이 들어 있었다.

### (13) 내장 이름을 가린다

`list`·`len`·`id`·`type`·`dict` 를 변수 이름으로 쓰면 **그 모듈 전체에서 내장이 사라진다.**
★ 가리는 줄은 아무 말도 안 하고 **증상이 한참 뒤에** 나와 원인이 안 보인다. `del` 로 이름표를 떼면 되돌아온다(동작 1의 ⑤).

### (14) `dis` 결과를 언어 사실로 적는다

★ **`LOAD_FAST_CHECK`·`LOAD_DEREF`·`co_varnames` 는 CPython 3.12 의 것**이다.
언어가 보장하는 것은 **「대입이 지역을 만든다」와 「그러면 `UnboundLocalError` 가 난다」까지다.**

## 구현 세부사항 대 언어 보장

세 층으로 가른다. ★ **이 주제는 언어 보장이 두껍다** — 스코프 규칙·예외 종류·`nonlocal` 이 `SyntaxError` 라는 것이 전부 레퍼런스에 있다.\
구현 쪽에 남는 것은 **명령 이름·코드 객체의 모양·진단 문구·인라인 여부**다.

| 층 | 무엇인가 | 어떻게 확인했나 |
|---|---|---|
| **언어 보장** | 언어 레퍼런스·PEP 가 정한 것 | 공식 문서 문장을 열어서 인용 |
| **CPython 구현** | 이 구현이 그렇게 하는 것 | `dis`·`co_varnames`·`co_freevars`·프레임 유무 |
| **이 판(3.12.3)의 관찰** | 3.12.3 에서 그랬을 뿐 | 예외 문구 · 제안 문구 · `e.name` |

### 언어 보장

| 사실 | 근거 |
|---|---|
| 이름은 **가장 가까운 둘러싼 스코프**에서 해소된다 | 4.2.2 — *"resolved using the nearest enclosing scope"* |
| **블록 안 어디든 바인딩이 있으면 그 블록 안의 모든 사용이 지역 참조**가 된다 | 4.2 — *"If a name binding operation occurs anywhere within a code block, all uses of the name within the block are treated as references to the current block."* |
| 블록에서 **쓰는데 안 묶인** 이름은 **자유 변수**다 | 4.2 — *"used in a code block but not defined there, it is a free variable"* |
| 어디에도 없으면 **`NameError`**, 지역인데 아직 안 묶였으면 **`UnboundLocalError`** | 4.2.2 |
| **`UnboundLocalError` 는 `NameError` 의 하위**다 | 4.2.2 — *"UnboundLocalError is a subclass of NameError."* |
| **`global` 선언은 그 이름의 모든 사용보다 앞서야** 한다 | 7.12 — *"The global statement must precede all uses of the listed names."* |
| **`nonlocal` 은 가장 가까운 둘러싼 함수 스코프의 「이미 묶인」 변수**를 가리킨다 | 7.13 — *"refer to previously bound variables in the nearest enclosing function scope"* |
| 그 이름이 **어느 둘러싼 함수 스코프에도 없으면 컴파일 시점 `SyntaxError`** | 7.13 — *"SyntaxError is raised at compile time if the given name does not exist in any enclosing function scope."* |
| **클래스 블록의 이름은 메서드 코드 블록으로 확장되지 않는다** — 컴프리헨션·제너레이터 표현식 포함 | 8.8 — *"The scope of names defined in a class block is limited to the class block; it does not extend to the code blocks of methods. This includes comprehensions and generator expressions…"* |
| **내장 스코프**가 마지막 층이다 | 4.2.3 |
| **컴프리헨션이 자기 스코프를 갖는다**(Python 3) | PEP 227 의 중첩 스코프 모델 위에 선 것 — 실측으로 전역 `i` 가 안 바뀌었다 |

### CPython 구현 세부사항

| 사실 | 어떻게 확인했나 |
|---|---|
| **대입이 있으면 `LOAD_FAST_CHECK`, 없으면 `LOAD_GLOBAL`** 로 컴파일된다 | `dis` — 같은 `print(count)` 한 줄이 갈렸다 |
| **지역 이름 목록이 `co_varnames`**, 자유 변수가 `co_freevars`, 전역·내장 이름이 `co_names` | 실행 |
| **L·E·G 가 `LOAD_FAST`·`LOAD_DEREF`·`LOAD_GLOBAL`** 로 갈린다 | `dis` |
| ★ **B 층은 별도 명령이 없다** — `LOAD_GLOBAL` 의 **실행 시점 폴백**이다 | `dis` — `G` 와 `len` 이 둘 다 `LOAD_GLOBAL` 이고 `co_names` 에 나란히 있다 |
| **E 층은 `COPY_FREE_VARS` 로 셀을 복사해 들고 시작**한다 | `dis` |
| ★ **3.12 는 list·set·dict 컴프리헨션을 인라인**한다(PEP 709). 제너레이터 표현식은 **아니다** | 코드 객체 유무 4종 + `dis` |
| 인라인해도 **`LOAD_FAST_AND_CLEAR` 로 이름 격리를 유지**한다 | `dis` |
| 그래서 **트레이스백에 `<listcomp>`·`<setcomp>` 프레임이 없고 `<genexpr>` 만 남는다** | 트레이스백 3종 |
| **`nonlocal` 오류 5종에 캐럿이 없다** | 실행 — 심볼 테이블 단계가 잡는다 |
| **`inner` 의 `locals()` 에 자유 변수가 들어 있다** | 실행 |

### 이 판(3.12.3)의 관찰

| 관찰 | 어디가 흔들리나 |
|---|---|
| `cannot access local variable 'count' where it is not associated with a value` | 예외 **종류**는 명세지만 **문구**는 아니다. 3.11 이전에는 다른 문장이었다 |
| `Did you mean: 'self.class_var'?` 제안 | **제안 기능 자체가 판마다 손보는 것**이다 |
| `UnboundLocalError` 의 **`e.name` 이 `None`** | `NameError` 쪽 속성이 안 채워진 것 — 판마다 바뀔 수 있다 |
| `no binding for nonlocal 'x' found` 등 5종 문구 | 종류(`SyntaxError`)는 명세, 문장은 아니다 |
| `dis` 의 **오프셋 숫자와 명령 배열** | 판마다 바뀐다. 볼 것은 **명령 이름의 갈림**이다 |
| `co_freevars` 에 **`inner` 자신**이 들어간 것 | 그 함수가 자기 이름을 쓰기 때문 — 코드에 달린 결과다 |

### 그래서 이렇게 적으면 틀린다

- ✗ 「읽기만 하면 바깥 값을 본다」\
  ○ **그 블록 안 어디든 대입이 있으면 못 본다.** 언어 보장이다.
- ✗ 「`UnboundLocalError` 는 대입한 줄에서 난다」\
  ○ **처음 읽는 줄에서 난다.** 실측은 `print` 줄(5번)이고 대입은 6번 줄이다.
- ✗ 「`UnboundLocalError` 는 `NameError` 와 다른 예외다」\
  ○ **하위 클래스**다. `except NameError` 로 잡힌다.
- ✗ 「`nonlocal` 로 전역도 고칠 수 있다」\
  ○ **`SyntaxError`** 다. **전역은 후보가 아니다** — 「없다」는 문구가 나온다.
- ✗ 「`global` 과 `nonlocal` 은 방향만 다르고 같은 것이다」\
  ○ **`global` 은 없던 이름을 만들고 `nonlocal` 은 못 만든다.** 이 비대칭이 핵심이다.
- ✗ 「`nonlocal` 은 함수 안에서만 쓸 수 있다」\
  ○ **클래스 몸통에서도 된다.** 안 되는 곳은 **모듈 수준**이다.
- ✗ 「클래스 변수는 메서드에서 그냥 보인다」\
  ○ **안 보인다.** 속성으로 읽어야 한다.
- ✗ 「3.12 는 리스트 컴프리헨션만 인라인한다」\
  ○ ★ **실측은 list·set·dict 셋 다다.** 제너레이터 표현식만 아니다.
- ✗ 「컴프리헨션이 인라인됐으니 이름도 새어 나온다」\
  ○ **안 샌다.** `LOAD_FAST_AND_CLEAR` 로 격리를 유지한다. **스코프는 보장, 프레임은 구현**이다.
- ✗ 「`dis` 로 봤으니 어느 파이썬에서나 그렇다」\
  ○ **명령 이름은 CPython 3.12 의 것**이다. 규칙은 명세, 그 실현 방법은 아니다.

**판정 기준 한 줄**: **「이 블록에 그 이름의 대입이 있나」를 물으면 층이 갈린다.**\
**「그 이름이 둘러싼 함수에 이미 있나」를 물으면 `nonlocal` 이 갈린다.**

## 언제 쓰고 언제 안 쓰나

| 상황 | 판정 |
|---|---|
| 함수 안에서 모듈 상수를 **읽기만** 한다 | **아무것도 안 쓴다** — 그냥 읽으면 G 로 간다 |
| 함수 안에서 모듈 변수를 **바꾼다** | `global` — 다만 **먼저 「정말 바꿔야 하나」를 묻는다**. 반환값 쪽이 대개 낫다 |
| 캐시·카운터를 모듈에 둔다 | ★ **`global` 대신 가변 객체의 내용을 고친다** — `CACHE[k] = v` 는 선언이 필요 없다 |
| 중첩 함수가 바깥 함수 값을 **누적**한다 | `nonlocal` — [22번](../22-closures-and-late-binding/2-summary.md)의 카운터 관용구 |
| 중첩 함수가 바깥 값을 **읽기만** 한다 | **아무것도 안 쓴다** — 자유 변수로 그냥 읽힌다 |
| 클래스 변수를 메서드에서 쓴다 | ★ **`self.x` 또는 `C.x`** — 이름으로는 못 읽는다 |
| 클래스 몸통에서 표를 만든다 | ★ **컴프리헨션을 쓰지 않는다** — 첫 이터러블 말고는 클래스 변수가 안 보인다. `for` 루프나 모듈 수준 헬퍼로 |
| 상태를 여러 함수가 공유해야 한다 | ★ **클래스나 명시적 인자로 옮긴다** — `global` 이 늘면 테스트가 순서에 묶인다 |
| 이름이 내장과 겹친다 | ★ **바꾼다.** `list`·`id`·`type`·`dict`·`len` 은 쓰지 않는다(`items`·`idx`·`kind` 로) |

## 핵심 문장

- ★★ **읽기는 LEGB 로 올라가지만, 무엇이 L 인지는 「컴파일 시점에 이미 정해져 있다」** —
  **블록 안 어디든 대입이 있으면 그 블록 전체에서 그 이름은 지역이다.** 줄 순서로 봐주지 않는다.
- ★ **그래서 `UnboundLocalError` 는 대입한 줄이 아니라 그보다 앞서 읽는 줄에서 난다.**
  실측에서 `print` 줄(5번)이 터졌고 대입은 6번 줄이었다.
- **`UnboundLocalError` 는 `NameError` 의 하위**다 — 「칸이 없다」와 「칸은 있는데 비었다」의 차이.
- ★ **`global` 은 없던 전역 이름을 만들고, `nonlocal` 은 이미 있는 것만 가리킨다.**
  없으면 **컴파일 시점 `SyntaxError`** 라 그 함수를 한 번도 안 불러도 파일이 안 뜬다.
- ★★ **`nonlocal` 이 안 되는 자리는 넷이고 그중 둘이 같은 문구**다 —
  「둘러싼 함수에 없다」와 「전역에만 있다」가 똑같이 `no binding for nonlocal 'x' found` 로 나온다.
  **전역은 `nonlocal` 의 후보가 아니다.**
- ★ **클래스 몸통은 사슬에서 빠진다** — 몸통은 둘러싼 함수를 보는데 **메서드는 클래스 변수를 이름으로 못 본다.**
  클래스 몸통의 컴프리헨션에서는 **첫 이터러블만** 보인다.
- **컴프리헨션이 자기 스코프를 갖는 것은 언어 보장**이고, **3.12 의 인라인화는 CPython 구현**이다.
  실측은 **list·set·dict 셋 다 인라인**이고 제너레이터 표현식만 코드 객체가 남았다.
- ★ **네 층인데 명령은 셋**이다 — `LOAD_FAST`·`LOAD_DEREF`·`LOAD_GLOBAL`.
  **내장 층은 `LOAD_GLOBAL` 의 실행 시점 폴백**이라 전역에서 이름을 지우면 다시 보인다.
- ★★ **이 주제가 22·23·24 의 바닥이다** — E 층을 셀로 빌려 오는 것이 클로저이고([22번](../22-closures-and-late-binding/2-summary.md)),
  그 클로저를 한 줄로 만드는 것이 `lambda` 이고([23번](../23-lambda-and-higher-order-functions/2-summary.md)),
  그 둘을 쌓는 것이 데코레이터다([24번](../24-decorators/2-summary.md)).

## 관련 자료

- 목록: [python/syntax 주제 목록](../README.md) — 이 주제는 **21번**
- 선행: [01-object-and-name-binding](../01-object-and-name-binding/2-summary.md) — 이름표 모델과 무엇이 바인딩인가.\
  **경계**: 그쪽은 「**이름이 객체에 붙는다**」까지, 여기는 「**그 이름이 어느 칸에 붙나**」부터다.
- ★ **이어지는 곳(사슬의 다음 고리)**: [22-closures-and-late-binding](../22-closures-and-late-binding/2-summary.md) —
  **E 층을 셀로 들고 다니는 것**이 클로저다.\
  **경계**: 여기는 **`co_freevars` 에 이름이 있다**까지, **그 셀이 언제 읽히나**(늦은 바인딩)부터가 그쪽이다.
- 이어지는 곳: [23-lambda-and-higher-order-functions](../23-lambda-and-higher-order-functions/2-summary.md) —
  `lambda` 가 만드는 것도 **같은 스코프 규칙을 따르는 함수**다.
- 이어지는 곳: [24-decorators](../24-decorators/2-summary.md) — 데코레이터는 **21·22·23 을 전부 쓴다.**
- 함께 보는 곳: [14-comprehensions](../14-comprehensions/2-summary.md) — ★ **인라인화(PEP 709)의 정본은 그쪽**이다.\
  **경계**: 그쪽은 「인라인이 무엇을 바꿨나」, 여기는 「**그래도 스코프는 그대로다**」쪽이다.
- 함께 보는 곳: [15-generator-expressions-lazy-eval](../15-generator-expressions-lazy-eval/2-summary.md) —
  **제너레이터 표현식이 인라인 대상이 아니라는 것**은 그쪽에서 본다.
- 함께 보는 곳: [19-function-argument-rules](../19-function-argument-rules/2-summary.md) —
  **파라미터도 바인딩**이라 지역 이름을 만든다. **컴파일 시점 대 실행 시점의 층 구분**도 같은 축이다.
- 함께 보는 곳: [20-mutable-default-args](../20-mutable-default-args/2-summary.md) —
  기본값은 **`def` 실행 시점**에 한 번 계산된다. **그쪽이 정본**이다.
- 이어지는 곳: 목록의 **29번 주제** 「클래스와 인스턴스 속성」 — `self.x` 와 `C.x` 의 속성 조회가 그쪽이다.
- 이어지는 곳: 목록의 **33번 주제** · **34번 주제** — 이름 해소와 **속성 해소**가 다른 기계라는 것.
- 기존 노트: [`cs/foundations/python-basics/`](../../../../python-basics/) — 함수를 정의하고 부르는 것까지가 그쪽이다.\
  **경계**: 여기는 「**그 함수 안의 이름이 어디서 풀리나**」부터다.
- 공식 문서: [Naming and binding](https://docs.python.org/3.12/reference/executionmodel.html#naming-and-binding) ·
  [Resolution of names](https://docs.python.org/3.12/reference/executionmodel.html#resolution-of-names) ·
  [`global`](https://docs.python.org/3.12/reference/simple_stmts.html#the-global-statement) ·
  [`nonlocal`](https://docs.python.org/3.12/reference/simple_stmts.html#the-nonlocal-statement) ·
  [PEP 227](https://peps.python.org/pep-0227/) · [PEP 3104](https://peps.python.org/pep-3104/) · [PEP 709](https://peps.python.org/pep-0709/)

## 용어 풀이

- **스코프(scope)**: 한 이름이 그 이름만으로 통하는 범위.\
  예: 함수 안에서 만든 `y` 는 그 함수 밖에서는 없는 이름이다.
- **LEGB**: 이름을 찾는 순서 — Local → Enclosing → Global → Built-in.\
  예: 네 층에 같은 이름이 있으면 **가장 안쪽이 이긴다.**
- **바인딩(binding)**: 이름을 객체에 묶는 일.\
  예: `=`·`+=`·`def`·`class`·`import`·`for`·`with … as`·`except … as`·파라미터가 전부 바인딩이다.
- **지역 변수(local variable)**: **그 블록 안 어딘가에 바인딩이 있는** 이름.\
  예: 마지막 줄의 대입 하나가 첫 줄의 읽기까지 지역으로 만든다.
- **자유 변수(free variable)**: 그 블록에서 **쓰는데 안 묶인** 이름.\
  예: 중첩 함수가 읽는 바깥 함수의 변수. `co_freevars` 에 들어간다.
- **가림(shadowing)**: 아래층의 같은 이름이 위층을 안 보이게 하는 것.\
  예: 모듈에 `len = "…"` 을 두면 그 모듈에서 내장 `len` 이 사라진다. `del len` 으로 되돌아온다.
- **`UnboundLocalError`**: 지역 칸은 있는데 **아직 값이 안 들어간** 채 읽었을 때.\
  예: `print(count)` 다음 줄에 `count = count + 1` 이 있으면 **`print` 줄**에서 난다. `NameError` 의 **하위**다.
- **`NameError`**: 어느 층에도 그 이름이 **없을 때**.\
  예: 메서드에서 클래스 변수를 이름으로 읽으면 이쪽이다.
- **`global` 문**: 그 블록에서 이 이름은 **모듈 칸**이라는 선언.\
  예: 없던 전역 이름도 **만든다.** 사용보다 앞에 와야 한다.
- **`nonlocal` 문**: 그 블록에서 이 이름은 **가장 가까운 둘러싼 함수 칸**이라는 선언.\
  예: 그 함수에 그 이름이 **이미 없으면** 컴파일 시점 `SyntaxError` 다.
- **클래스 몸통 스코프(class block)**: 클래스 정의의 본문이 도는 블록.\
  예: 둘러싼 함수는 **보이는데**, 그 몸통이 만든 이름은 **메서드에서 안 보인다.**
- **심볼 테이블(symbol table)**: 컴파일러가 블록마다 이름의 성격을 정리해 둔 표.\
  예: `nonlocal` 오류가 **캐럿 없이** 나는 것은 파서가 아니라 이 단계가 잡기 때문이다.
- **`co_varnames` · `co_freevars` · `co_names`**: 코드 객체가 든 이름 목록 — 지역 · 자유 변수 · 전역과 내장.\
  예: `bump` 에는 `('count',)` 가 들어 있고 `just_read` 에는 비어 있다. **CPython 구현**이다.
- **인라인화(inlining)**: 별도 호출로 처리하던 것을 부르는 쪽에 펴 넣는 최적화.\
  예: 3.12 가 list·set·dict 컴프리헨션에 적용했다(PEP 709). 제너레이터 표현식은 대상이 아니다.

## 더 들어가면

- **`nonlocal` 이 생기기 전**(3.0 이전)에는 바깥 함수 변수를 고칠 방법이 **리스트 한 칸을 쓰는 것**뿐이었다 —
  `box = [0]` 을 만들고 안에서 `box[0] += 1` 을 하는 관용구. **바인딩이 아니라 객체 조작**이라 통했다.
  PEP 3104 가 그 우회를 없앴다. 오래된 코드에서 `[0]` 짜리 리스트를 보면 이 흔적이다.
- **`exec`·`eval` 은 스코프 규칙의 바깥이다** — 넘겨 준 dict 를 네임스페이스로 쓰므로
  이 주제의 정적 판정이 적용되지 않는다. 그래서 함수 안의 `exec` 로는 지역 변수를 만들 수 없다.
- **`locals()` 의 반환은 함수 스코프에서 스냅샷**이다. 거기에 대입해도 지역 변수가 안 바뀐다.
  모듈·클래스 몸통에서는 진짜 네임스페이스라 바뀐다 — 실측에서 모듈의 `locals() is globals()` 가 `True` 였다.
- **애노테이션 스코프는 예외 중의 예외다** — 레퍼런스가 클래스 스코프 규칙에서 *"it does not include annotation scopes,
  which have access to their enclosing class scopes"* 라고 따로 뺀다. 타입 힌트 쪽 이야기라 목록의 **40번 주제**에서 본다.
- **모듈 사이에는 스코프 사슬이 없다** — 다른 모듈의 전역은 아무리 올라가도 안 보인다. `import` 가 **이름을 내 칸에 만드는 것**이다.
- ★ **E 층이 「셀」이라는 물건으로 구현된다는 것**까지 가면 [22번](../22-closures-and-late-binding/2-summary.md)이다.
  여기서 본 `COPY_FREE_VARS`·`LOAD_DEREF` 가 그 입구다.
</content>
</invoke>
