# python/syntax/21-scope-legb-global-nonlocal — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> [1-question.md](1-question.md)의 번호와 **1:1**로 대응한다. 질문 12개 = 답 12개.
>
> 이 파일의 모든 출력은 `python3` **3.12.3**(Linux)에서 실제로 돌려 나온 것이다. 지어낸 출력은 없다.
> 던지는 형태는 `python3 - <파일` 로 고정했다 — 트레이스백이 `File "<stdin>", line N` 이 된다.
> ★ **캐럿 규칙** — 실행 중 예외에는 소스 줄도 캐럿도 없고, `SyntaxError` 에는 대개 있다.
> **다만 이 주제의 `nonlocal` 오류 다섯은 전부 없다**(3번 답) — 파서가 아니라 심볼 테이블 단계가 잡기 때문이다.
> ★ **소스 펜스의 첫 줄은 캡처가 붙인 파일명 주석**이다. 트레이스백의 줄 번호는 **그 주석을 뺀 실파일 기준**이다.\
> 단 **예외 문구·제안 문구(`Did you mean:`)·`dis` 의 명령 이름과 오프셋**은 구현에 달린 것이라 다른 판에서는 달라진다(11번 답).

## 정답

### 1. 가장 안쪽이 이기고, `del` 은 내장이 아니라 이름표를 뗀다

**출력** — 첫 판.

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

둘째 판.

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

**왜 그런가**

```text
   이름을 읽을 때 —  L  →  E  →  G  →  B      먼저 찾은 곳에서 멈춘다

   inner            L 에 name 이 있다        →  "L: 지역"      (위로 안 올라간다)
   inner_no_local   L 이 비었다  →  E 에 있다  →  "E: 둘러싼 함수" (G 까지 안 간다)
   모듈 꼭대기       G 에 있다                →  "G: 전역"
   len              아무도 안 가렸다          →  B 까지 올라간다
```

★ **둘째 판은 같은 이름을 네 층에 차례로 얹은 것**이다.

| 줄 | 어느 층이 이겼나 | 왜 |
|---|---|---|
| ① | **B** | 아직 아무도 `len` 을 안 가렸다 |
| ② | **G** | 모듈 꼭대기의 `len = "…"` 이 내장을 덮었다 |
| ③ | **E** | `outer` 의 `len` 이 G 를 덮었다 |
| ④ | **L** | `inner_has_local` 의 `len` 이 E 를 덮었다 |
| ⑤ | **다시 B** | ★ `del len` 이 **G 칸의 이름표를 뗐다** |

★★ **⑤ 가 이 문항의 답이다.** `del len` 은 **내장 `len` 을 지운 것이 아니다** —
모듈 전역 칸에 붙여 놨던 이름표 하나를 뗐을 뿐이고, 그러니 사다리가 **한 칸 더 올라가 내장을 다시 찾는다.**
내장 스코프는 **다른 네임스페이스**라 모듈에서 `del` 로 닿을 수 없다.

★ 실무적 결론 하나 — **내장 이름을 가리면 에러가 그 자리에서 안 난다.**
`len = "…"` 은 **그 줄에서 아무 말도 안 하고**, 문제는 **한참 뒤** `len(xs)` 를 부를 때 드러난다.
**원인과 증상이 멀어지는** 전형적인 자리다. 실측이 보여 준 것은 ②와 ⑤ 두 줄이다 — **가려졌다가 `del` 로 되돌아왔다.**

### 2. `print` 줄(5번)에서 `UnboundLocalError` — 문구는 한 글자도 안 찍힌다

**출력**

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

**왜 그런가**

```text
   count = 10                      ← 전역에 10 이 있다

   def bump():
       print("읽기만 …", count)     ← line 5  ★ 여기서 터진다
       count = count + 1           ← line 6     대입은 여기다
       return count

   ┌ 컴파일할 때 이 블록의 지역 이름을 먼저 확정한다
   ├ count 에 대입이 있다  →  count 는 이 블록의 지역이다  (줄 순서 무관)
   └ 그러면 5번 줄의 count 도 "지역 count" 를 읽는 것이 된다  →  아직 비었다  →  예외
```

★★ **`읽기만 하려던 참이다:` 가 안 찍혔다.** `print` 는 **인자를 다 만든 뒤에** 부르는 것이라,
인자를 만들다 터지면 **아무것도 안 찍힌다.** 「앞부분은 찍히고 뒤에서 터졌겠지」가 틀린다.

★ **언어 보장이다** — 레퍼런스가 평서문으로 적는다.

> If a name binding operation occurs anywhere within a code block, all uses of the name within
> the block are treated as references to the current block.

그리고 예외의 **종류**까지 적는다.

> If the current scope is a function scope, and the name refers to a local variable that has not yet
> been bound to a value at the point where the name is used, an UnboundLocalError exception is raised.

★ **`count = count + 1` 을 지우면** 그 블록에 `count` 의 바인딩이 하나도 없어진다 →
`count` 는 **자유 변수**가 되고 사다리가 G 칸까지 올라간다 → **안 터진다.**\
★ 그 꼴을 실제로 돌려 본 것이 **7번 답의 `just_read`** 다 — `co_varnames` 가 비어 있고 `LOAD_GLOBAL` 로 컴파일됐다.
**한 줄을 지웠는데 앞줄의 의미가 바뀌는 것**이 이 주제의 전부다.

### 3. 다섯 전부 `SyntaxError` · 전부 컴파일 시점 · 전부 캐럿 없음

**출력** — 다섯을 따로 던진 결과다.

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

**왜 그런가**

전수 표 — **메시지 본문까지 그대로.**

| # | 자리 | `SyntaxError` 메시지 본문 |
|---|---|---|
| ① | **모듈 수준** · 이미 대입된 이름 | `name 'x' is assigned to before nonlocal declaration` |
| ② | **모듈 수준** · 대입 없는 이름 | `nonlocal declaration not allowed at module level` |
| ③ | **둘러싼 함수에 그 이름이 없다** | `no binding for nonlocal 'never_bound' found` |
| ④ | **전역에만 있다** | `no binding for nonlocal 'g' found` ★ ③과 **같다** |
| ⑤ | **함수 안에서 대입 뒤에 선언** | `name 'n' is assigned to before nonlocal declaration` ★ ①과 **같다** |

★★ **읽을 것 넷.**

1. **자리는 넷인데 블록은 다섯**이다 — **모듈 수준이 두 갈래로 갈린다**(①·②).
   **앞에 대입이 있었느냐**가 문구를 정한다. 대입이 있으면 「선언이 늦었다」로, 없으면 「여기선 못 쓴다」로 답한다.
2. ★ **문구가 겹치는 짝이 둘이다** — ③④(`no binding …`)와 ①⑤(`assigned to before …`).
   ★★ 특히 **③과 ④의 겹침이 이 주제의 함정**이다. `g` 는 **분명히 존재하는 이름**인데 「없다」고 한다 —
   `nonlocal` 이 보는 후보는 **둘러싼 함수 스코프뿐**이고 **전역은 그 목록에 아예 없다.**
3. **다섯 전부 컴파일 시점**이다. `(exit 1)` 이고, **그 함수를 한 번도 안 불러도 파일이 안 뜬다.**
   ★ 실제로 ②의 판에서는 위에 있는 `def show()` 조차 **정의되지 않았다** — 파일 전체가 컴파일에 실패했다.
4. ★ **다섯 전부 캐럿이 없다.** `File "<stdin>", line N` 한 줄과 메시지뿐이다.

```text
   소스 글자 ──> 파서 ──────> AST ──> 심볼 테이블 ──> 컴파일 ──> 실행
                   │                      │
                   │                      └ ★ nonlocal 오류 5종 (캐럿 없음)
                   │                        이름들을 "다 모아 비교해야" 알 수 있어
                   │                        토큰 위치 정보가 남아 있지 않다
                   └ SyntaxError (캐럿 있음 — 토큰 배열 자체가 틀린 것)
```

★ [19번](../19-function-argument-rules/2-summary.md)의 `duplicate argument 'a'`·`keyword argument repeated` 와
**정확히 같은 부류**다. **`SyntaxError` 안에서 캐럿의 유무가 또 하나의 층**이라는 것이 두 주제의 공통 결론이다.

★ 레퍼런스가 시점까지 못 박는다 —
*"SyntaxError is raised at compile time if the given name does not exist in any enclosing function scope."*

### 4. 몸통은 둘러싼 함수를 보고, 메서드는 클래스 칸을 못 본다

**출력** — 네 판이다.

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

**왜 그런가**

```text
   def outer():
       from_enclosing = "…"          ┌ E 칸
       class C:                      │
           seen = from_enclosing     │  ★ 몸통은 E 를 본다        (된다)
           class_var = "클래스 변수"   │     └ C 의 네임스페이스에 담긴다
           def method(self):         │
               return class_var      │  ★ 메서드는 그 칸을 못 본다  (NameError)

   메서드의 사다리:   L(method) → E(outer) → G → B
                                ^^^^^^^^^
                       C 의 몸통 칸이 사슬에서 빠져 있다
```

★ **언어 보장이다.**

> The scope of names defined in a class block is limited to the class block; it does not extend to
> the code blocks of methods. This includes comprehensions and generator expressions, but it does
> not include annotation scopes, which have access to their enclosing class scopes.

- ★ **`C.class_var` 로는 읽힌다** — 이름이 사라진 게 아니라 **클래스 네임스페이스의 속성**이 됐을 뿐이다.
  **속성 조회(`C.x`·`self.x`)와 이름 해소(LEGB)는 서로 다른 기계**다. 3.12 가 `Did you mean: 'self.class_var'?` 로 답까지 준다.

★★ **둘째 판 — 같은 줄의 두 이름이 갈린다.**

```text
   class C:
       rows = [1, 2, 3]
       factor = 10
       doubled = [r * 2 for r in rows]        ★ 된다
                            ^^^^^^^^  첫 for 의 이터러블은 "바깥"(클래스 몸통)에서
                                      평가돼 컴프리헨션에 넘겨진다
       scaled = [r * factor for r in rows]    ✗ NameError: name 'factor' is not defined
                    ^^^^^^  이건 컴프리헨션 안에서 읽는 이름이라
                            클래스 칸을 못 본다 (위 인용문의 "This includes comprehensions")
```

★ 트레이스백의 프레임이 **`in C`** 다 — `in <listcomp>` 가 **아니다.** 3.12 가 인라인했기 때문이다(6번 답).

★★ **셋째 판 — 클래스 몸통의 `nonlocal` 은 된다.** `outer` 의 `v` 가 `2` 가 됐다.

```text
   nonlocal 이 요구하는 것 = "찾아 올라갈 대상이 둘러싼 함수 스코프에 있을 것"
   nonlocal 이 요구하지 않는 것 = "쓰는 자리가 함수일 것"

     함수 안의 클래스 몸통   →  둘러싼 함수(outer)가 있다   →  된다
     모듈 수준              →  둘러싼 함수가 아예 없다      →  SyntaxError (3번 답 ②)
```

★ **넷째 판 — `C` 에 `tag` 는 안 생긴다.** `global tag` 가 그 블록에서 `tag` 를 **모듈 칸으로 돌려놨기** 때문이다.
같은 몸통의 `local_only` 는 그대로 클래스 속성이 됐다 — **한 블록 안에서 이름마다 목적지가 다르다.**

### 5. 이름은 안 새고, 코드 객체는 제너레이터 표현식에만 남는다

**출력** — 첫 판.

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

둘째 판.

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

**왜 그런가**

```text
   ┌ 모듈 스코프 ────────────────────────────┐
   │  i = "전역 i 는 그대로다"   ← 안 더럽혀진다  │
   │   ┌ 컴프리헨션의 방 ──────────────┐       │
   │   │  i = 0, 1, 2, 3              │       │
   │   │  바깥 이름은 읽을 수 있다       │       │
   │   └──────────────────────────────┘       │
   │        └ 방이 닫히면 i 는 사라진다          │
   └─────────────────────────────────────────┘
```

- **전역 `i` 가 그대로다** — 같은 이름인데 안 덮였다.
- **읽기는 된다** — 함수 안에서 `total` 을 읽어 `[0, 1, 2]` 가 나왔다. **막힌 것은 쓰기 쪽이지 읽기가 아니다.**
- **`"n" in locals()` 이 `False`** — 루프 변수는 밖에 안 남는다.

★★ **둘째 판이 흔한 요약을 뒤집는다.**

| 표기 | 별도 코드 객체 | 읽는 법 |
|---|---|---|
| `[n for n in r]` | 없음 | **인라인** |
| `{n for n in r}` | 없음 | **인라인** |
| `{n: n for n in r}` | 없음 | **인라인** |
| `(n for n in r)` | `<genexpr>` | ★ **인라인 대상이 아니다** |

「3.12 는 **리스트** 컴프리헨션을 인라인한다」로 외우면 절반만 맞는다 —
**list·set·dict 셋 다 인라인**이고, 코드 객체가 남은 것은 **제너레이터 표현식 하나뿐**이다.

★★ **여기서 층을 갈라라.**

| 사실 | 층 |
|---|---|
| 컴프리헨션이 **자기 스코프를 갖는다**(루프 변수가 안 샌다) | **언어 보장** — Python 3 공통 |
| 그 스코프가 **별도 코드 객체·프레임을 갖느냐** | ★ **CPython 3.12 의 구현**(PEP 709) |
| `LOAD_FAST_AND_CLEAR` 로 **인라인해도 격리를 유지**하는 것 | ★ **CPython 구현** |

★ **인라인화의 정본은 [14번](../14-comprehensions/2-summary.md)** 이다(list·dict·set 로 적혀 있다).
**제너레이터 표현식이 인라인 대상이 아니라는 쪽**은 [15번](../15-generator-expressions-lazy-eval/2-summary.md)을 본다.

### 6. 제너레이터 표현식만 `in <genexpr>` 한 줄이 더 있다

**출력** — 셋을 따로 던졌다.

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

**왜 그런가**

```text
   리스트 컴프리헨션    … in <module>  /  … in boom_listcomp                    프레임 2
   세트 컴프리헨션      … in <module>  /  … in boom_setcomp                     프레임 2
   제너레이터 표현식    … in <module>  /  … in boom_genexp  /  ★ in <genexpr>   프레임 3
```

- ★ **list·set 쪽에는 `<listcomp>`·`<setcomp>` 줄이 없다.** 인라인돼서 **자기 프레임을 안 갖는다.**
- ★ **제너레이터 표현식만 한 줄이 더 있다** — 인라인 대상이 아니라 **진짜 함수 호출**이기 때문이다.
  5번 답의 `<genexpr>` 코드 객체가 **여기서 프레임으로 나타난 것**이다. 두 관찰이 같은 사실의 앞뒤다.
- ★★ **이것은 구현의 관찰이지 언어 보장이 아니다.** 3.11 이하에서는 세 판 다 프레임 줄이 하나씩 더 있었을 것이고,
  이 머신에 3.11 이하가 없어 **직접 대조하지는 못했다**(PEP 709 근거).
- ★ **디버깅 실무 결론 하나** — **트레이스백이 짧아졌다고 컴프리헨션 안이 아닌 것이 아니다.**
  `in boom_listcomp` 줄의 **줄 번호**가 컴프리헨션이 있는 줄을 가리킨다.

### 7. 「어디든」이라는 낱말이 줄 순서를 지운다

**출력** — 같은 `print(count)` 한 줄이 두 가지로 컴파일된 것.

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

**왜 그런가**

★ **규칙 자체는 언어 보장이다.**

> If a name is bound in a block, it is a local variable of that block, unless declared as
> nonlocal or global. … If a variable is used in a code block but not defined there, it is a free variable.

**「블록 안 어디든」** 이므로 **마지막 줄의 대입도, 안 도는 `if` 안의 대입도** 똑같이 센다.
스코프는 **정적 성질**이지 실행 흐름의 결과가 아니기 때문이다 — 그래야 함수를 **부르기 전에** 이름 목록을 확정할 수 있다.

★ **그 확정의 결과가 CPython 에서는 이렇게 보인다.**

```text
   def bump():            대입이 있다
       print(count)   →  LOAD_FAST_CHECK 0 (count)   "지역 칸을 읽되 비었으면 터져라"
       co_varnames = ('count',)                      ★ 지역 이름 목록에 들어 있다

   def just_read():       대입이 없다
       print(count)   →  LOAD_GLOBAL     2 (count)   아예 전역을 보러 간다
       co_varnames = ()                              ★ 지역 이름이 하나도 없다
```

- ★★ **층을 갈라라** — 「대입이 지역을 만든다」는 **언어 보장**,
  **`LOAD_FAST_CHECK`·`co_varnames` 는 CPython 3.12 의 구현**이다. 다른 구현은 같은 규칙을 다른 방법으로 지킬 수 있다.
- ★ **`UnboundLocalError` 를 던지는 주체가 `LOAD_FAST_CHECK`** 다. `LOAD_FAST` 였다면 빈 칸을 그냥 읽었을 것이다.

★ **전부 바인딩이라 전부 같은 결과가 된다.**

| 쓴 것 | 지역이 되나 |
|---|---|
| `count = …` · `count += 1` | ★ **된다** — `+=` 도 대입이다 |
| `for count in …` | ★ **된다** |
| `with … as count` · `except … as count` | ★ **된다** |
| `import count` · `from x import count` | ★ **된다** |
| `def count(): …` · `class count: …` | ★ **된다** |
| `cfg["count"] = 1` · `xs.append(1)` | **안 된다** — 이름이 아니라 **객체를 고친 것**이다 |

★ 마지막 줄이 실무의 탈출구다 — **가변 객체의 내용을 고치는 것은 바인딩이 아니라서 `global` 이 필요 없다**
([01번](../01-object-and-name-binding/2-summary.md)의 이름표 모델).

### 8. `global` 은 없는 이름을 만들고, `nonlocal` 은 못 만든다

**출력** — `global` 쪽.

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

`nonlocal` 쪽.

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

**왜 그런가**

```text
   ┌ B: 내장 ─────────────┐
   ├ G: 모듈 ─────────────┤  ◀── global x      없으면 ★ 만든다
   ├ E: 둘러싼 함수 ───────┤  ◀── nonlocal x    없으면 ★ SyntaxError
   └ L: 지금 이 함수 ──────┘      (선언이 없으면) 대입은 여기로 간다
```

★★ **한 표로 가른다.**

| | `global` | `nonlocal` |
|---|---|---|
| 가리키는 칸 | **모듈(G)** | **가장 가까운 둘러싼 함수(E)** |
| 그 이름이 없어도 되나 | ★ **된다 — 만든다** | ★ **안 된다 — `SyntaxError`** |
| 전역을 가리킬 수 있나 | 그것이 본업이다 | ★ **못 한다** — 후보 목록에 없다 |
| 클래스 몸통에서 쓸 수 있나 | **된다**(4번 답 넷째 판) | **된다**(4번 답 셋째 판) |
| 모듈 수준에서 쓸 수 있나 | 된다(효과는 없다) | ★ **`SyntaxError`** |
| 선언 위치 | **사용보다 앞** | **사용보다 앞** |
| 어길 때 | 컴파일 시점 `SyntaxError` | 컴파일 시점 `SyntaxError` |

- ★ **`global` 이 없던 이름을 만들었다** — 호출 전에는 `globals()` 에 없었고 호출 뒤에 생겼다.
  **`global` 줄 자체가 만드는 것이 아니라 그 뒤의 대입이 만든다** — 선언은 「어느 칸에 쓸지」만 정한다.
- ★ **`nonlocal` 없이 쓰면 바깥이 안 바뀐다** — 반환값은 둘 다 `100` 인데 **바깥 `n` 이 `0` 과 `100` 으로 갈렸다.**
  ★★ **함수 안만 읽어서는 못 잡는 차이**라 이 주제에서 가장 조용히 틀리는 자리다.

★★ **`nonlocal` 로 전역을 고치려 하면 `no binding for nonlocal 'g' found`** 다(3번 답 ④).
**문구가 헷갈리는 이유** — `g` 는 **있는 이름**인데 「없다」고 말한다.
`nonlocal` 에게 「있다」는 **둘러싼 함수 스코프에 있다**는 뜻이고, 전역은 그 문장의 주어가 아니다.

- 레퍼런스의 표현 — *"refer to previously bound variables in the nearest enclosing function scope"*.
  **`previously bound`** 가 「만들지 않는다」를, **`function scope`** 가 「전역은 아니다」를 각각 말한다.

### 9. 「칸이 없다」와 「칸은 있는데 비었다」

**출력**

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

**왜 그런가**

```text
   BaseException
     └ Exception
         └ NameError                ← 어느 층에도 그 이름이 없다
             └ UnboundLocalError    ← 지역 칸은 있는데 아직 값이 안 들어갔다

   except NameError:       ★ 둘 다 잡힌다
   except UnboundLocalError:  갈라 잡으려면 이쪽을 "먼저" 둔다
```

- ★ **하위 클래스**다 — 레퍼런스가 직접 적는다: *"UnboundLocalError is a subclass of NameError."*
  실측의 `__mro__` 와 `issubclass` 가 그대로 보여 준다.
- ★ **그래서 `except NameError` 로 잡힌다.** 잡아 놓고 `type(e).__name__` 을 찍어야 어느 쪽인지 안다 —
  실측에서 `NameError` 로 잡았는데 이름은 `UnboundLocalError` 였다.

★★ **문제가 된 이름을 문구 파싱 없이 얻을 수 있나 — 이 경우엔 못 얻는다.**

- `NameError` 에는 어느 이름이 문제였는지 담는 **`name` 속성**이 있는데,
  **`UnboundLocalError` 쪽은 `None` 이었다**(3.12.3 관찰).
- 메시지 본문에는 `'v'` 가 들어 있다 — **문구를 파싱하지 않고는 이름을 못 얻는다.**
- ★ 그리고 **문구는 판마다 손보는 것**이라 그 파싱에 기대면 안 된다.
  잡아야 할 것은 **예외 종류**이지 문장이 아니다([19번](../19-function-argument-rules/2-summary.md)과 같은 결론).

### 10. `locals()` 에는 자유 변수까지 들어 있다

**출력**

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

**왜 그런가**

```text
   module_level = "M"           G 칸
   def outer():
       enclosing = "E"          E 칸
       def inner():
           local = "L"          L 칸

   inner 에서 —
     locals()      ['enclosing', 'inner', 'local']   ★ 자유 변수까지 들어 있다
     co_freevars   ('enclosing', 'inner')            ★ 바깥에서 빌려 온 이름들
     globals()     module_level 은 있고 enclosing 은 없다
```

- ★★ **`inner` 의 `locals()` 에 `enclosing` 이 들어 있다.** 「지역」이라는 낱말만 보고
  **「이 함수가 만든 이름」으로 읽으면 틀린다** — `locals()` 는 **그 프레임에서 이름으로 닿는 것**을 보여 주고,
  **자유 변수도 그 프레임이 셀로 들고 있으므로** 포함된다.
- ★ **`co_freevars` 에 `inner` 자신이 들어 있다** — `inner` 안에서 `inner.__code__` 를 읽기 때문이다.
  **자기 이름을 쓰는 중첩 함수는 자기 자신을 자유 변수로 빌린다.** (재귀 중첩 함수가 다 이 모양이다.)
- ★★ **`enclosing` 은 `globals()` 에 없다.** 이것이 `global` 과 `nonlocal` 을 가르는 **물리적 근거**다 —
  E 칸은 **어느 모듈 사전에도 들어 있지 않고** 프레임과 셀에만 있다(8번 답의 표).
- ★ **모듈 수준에서는 `locals() is globals()` 가 `True`** 다. 모듈에는 L 칸과 G 칸의 구분이 없다.
  그래서 모듈 수준의 `global` 선언은 **아무 효과가 없다.**

> **자유 변수(free variable)** — 어떤 블록에서 **쓰는데 그 블록에서 안 묶인** 이름.\
> 예: 위 `inner` 의 `enclosing`. 레퍼런스의 표현으로 *"used in a code block but not defined there"*.

### 11. 세 층 — 그리고 「네 층이 네 명령」은 틀리다

**출력** — 층을 가르는 근거로 쓴 것.

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

**왜 그런가**

★★ **먼저 둘째 질문부터. 네 층은 네 명령으로 갈리지 않는다 — 명령은 셋이다.**

```text
   def inner():  return L + E + G + len("x")

     L  →  LOAD_FAST   0 (L)      co_varnames = ('L',)
     E  →  LOAD_DEREF  1 (E)      co_freevars = ('E',)    ← COPY_FREE_VARS 로 셀을 받아 온다
     G  →  LOAD_GLOBAL 0 (G)      co_names = ('G', 'len')
     B  →  LOAD_GLOBAL 3 (len)    ★ G 와 같은 명령이고 같은 목록에 있다

   LOAD_GLOBAL 이 실행 시점에 하는 일
        globals() 에 있나? ─예→ 그 값
              └ 아니오 → builtins 에 있나? ─예→ 그 값
                            └ 아니오 → NameError
```

★ **B 층은 컴파일 시점에 갈리지 않는다** — `LOAD_GLOBAL` 의 **실행 시점 폴백**이다.
1번 답의 ⑤(`del len` 뒤 내장이 다시 보인 것)가 **바로 이 폴백의 관찰**이다.

**언어 보장**

| 사실 | 근거 |
|---|---|
| 이름은 **가장 가까운 둘러싼 스코프**에서 해소된다 | 4.2.2 Resolution of names |
| **블록 안 어디든 바인딩이 있으면 그 블록의 모든 사용이 지역 참조**다 | 4.2 Naming and binding |
| 없으면 **`NameError`**, 지역인데 안 묶였으면 **`UnboundLocalError`** · 후자는 전자의 **하위** | 4.2.2 |
| **`global` 선언은 그 이름의 모든 사용보다 앞서야** 한다 | 7.12 |
| **`nonlocal` 은 둘러싼 함수 스코프의 「이미 묶인」 이름**만 가리키고, 없으면 **컴파일 시점 `SyntaxError`** | 7.13 |
| **클래스 블록의 이름은 메서드로 확장되지 않는다** — 컴프리헨션·제너레이터 표현식 포함 | 8.8 Class definitions |
| **내장 스코프**가 마지막 층이다 | 4.2.3 |
| **컴프리헨션이 자기 스코프를 갖는다**(Python 3) | 실측 — 전역 `i` 가 안 바뀌었다 |

**CPython 구현 세부사항**

| 사실 | 어떻게 확인했나 |
|---|---|
| 대입이 있으면 **`LOAD_FAST_CHECK`**, 없으면 **`LOAD_GLOBAL`** 로 컴파일된다 | `dis` — 같은 한 줄이 갈렸다 |
| 지역이 `co_varnames`, 자유 변수가 `co_freevars`, 전역·내장이 `co_names` | 실행 |
| L·E·G 가 `LOAD_FAST`·`LOAD_DEREF`·`LOAD_GLOBAL` 로 갈린다 | `dis` |
| ★ **B 층에 별도 명령이 없다** — `LOAD_GLOBAL` 의 실행 시점 폴백 | `dis` — `G` 와 `len` 이 같은 명령 |
| E 층은 **`COPY_FREE_VARS`** 로 셀을 받아 온다 | `dis` |
| ★ **3.12 는 list·set·dict 컴프리헨션을 인라인**한다(PEP 709). 제너레이터 표현식은 **아니다** | 코드 객체 4종 + `dis` |
| 인라인해도 **`LOAD_FAST_AND_CLEAR` 로 이름 격리를 유지**한다 | `dis` |
| **트레이스백에 `<listcomp>`·`<setcomp>` 프레임이 없고 `<genexpr>` 만 남는다** | 트레이스백 3종 |
| **`nonlocal` 오류 5종에 캐럿이 없다** | 실행 |
| **`locals()` 에 자유 변수가 들어 있다** | 실행 |

**이 판(3.12.3)의 관찰**

| 관찰 | 어디가 흔들리나 |
|---|---|
| `cannot access local variable 'count' where it is not associated with a value` | 예외 **종류**는 명세, **문구**는 아니다. 3.11 이전은 다른 문장이었다 |
| `Did you mean: 'self.class_var'?` 제안 | **제안 기능 자체가 판마다 손보는 것**이다 |
| `UnboundLocalError` 의 **`e.name` 이 `None`** | `NameError` 쪽 속성이 안 채워진 것 |
| `no binding for nonlocal 'x' found` 등 5종 문구 | 종류는 명세, 문장은 아니다 |
| `dis` 의 **오프셋 숫자와 명령 배열** | 판마다 바뀐다. 볼 것은 **명령 이름의 갈림**이다 |
| `co_freevars` 에 **`inner` 자신**이 들어간 것 | 그 함수가 자기 이름을 쓰기 때문 — 코드에 달린 결과다 |

★ **판정 기준 한 줄** — **규칙과 예외 종류는 명세이고, 「그 규칙을 어떻게 실현하나」와 「어겼을 때 무슨 문장이 나오나」는 이 구현이다.**

### 12. 이 주제가 떠받치는 것 — 사슬의 첫 고리

이 문항은 **연결**이다 — 새 출력 없이, 앞 답들이 이미 보인 것을 이어 붙인다.
근거로 쓰는 것은 **8번 답의 `nonlocal` 블록**(E 칸이 따로 있다는 것)과
**11번 답의 `COPY_FREE_VARS`·`LOAD_DEREF`**(그 칸을 셀로 받아 온다는 것) 둘이다.

**왜 그런가**

```text
   21 (여기)   이름이 어느 칸에서 풀리나 · E 칸이 따로 있다 · nonlocal 로 고친다
        ↓
   22          그 E 칸이 "셀" 이라는 물건이고, 함수가 그것을 들고 다닌다   → 늦은 바인딩
        ↓
   23          lambda 도 같은 규칙을 따르는 함수다                        → 루프 안의 lambda
        ↓
   24          데코레이터는 21·22·23 을 전부 쓴다                        → 래퍼가 원본을 자유 변수로 든다
```

| 주제 | 이 주제가 떠받치는 것 |
|---|---|
| [22번](../22-closures-and-late-binding/2-summary.md) | **E 층이 따로 있다**는 것. 그 칸을 셀로 들고 다니는 함수가 클로저이고, **셀을 「언제 읽나」가 늦은 바인딩**이다 |
| [23번](../23-lambda-and-higher-order-functions/2-summary.md) | `lambda` 도 **같은 스코프 규칙을 따르는 함수**다. 루프 안의 `lambda` 가 같은 값을 내는 이유가 21·22 에 있다 |
| [24번](../24-decorators/2-summary.md) | 래퍼가 **원본 함수를 자유 변수로 든다**. `nonlocal` 로 호출 횟수를 세는 것도 여기서 온다 |

★ **경계를 한 줄씩 긋는다.**

| 주제 | 경계 |
|---|---|
| [22번](../22-closures-and-late-binding/2-summary.md) | 여기는 **`co_freevars` 에 이름이 있다**까지. **그 셀이 언제 읽히나**부터가 그쪽 |
| [14번](../14-comprehensions/2-summary.md) | ★ **인라인화(PEP 709)의 정본은 그쪽.** 여기는 **「인라인돼도 스코프는 그대로다」** 쪽만 본다 |
| [15번](../15-generator-expressions-lazy-eval/2-summary.md) | **제너레이터 표현식이 인라인 대상이 아니라는 것**은 그쪽 |
| [19번](../19-function-argument-rules/2-summary.md) | **파라미터가 바인딩이라는 것**과 **컴파일 시점 대 실행 시점의 층 구분**이 같은 축 |
| [20번](../20-mutable-default-args/2-summary.md) | **기본값이 `def` 실행 때 한 번**인 것은 그쪽이 정본 |
| [01번](../01-object-and-name-binding/2-summary.md) | 「이름이 객체에 붙는다」까지가 그쪽, 「어느 칸에 붙나」부터가 여기 |
| [목록의 **29번 주제**](../29-classes-and-attribute-lookup/) | `self.x`·`C.x` 의 **속성 조회**는 그쪽 — 이름 해소와 다른 기계다 |

★★ **한 줄로 외운다** — **21 은 「이름이 어디서 풀리나」이고, 22 는 「그 칸을 언제 읽나」다.**

## 실행 검증

이 문서와 [2-summary.md](2-summary.md)에 실린 출력은 전부 아래처럼 돌려서 얻었다.

| 무엇을 | 어떻게 | 몇 번 | 어디에 |
|---|---|---|---|
| 버전 확인 | `python3 - <v_version.py` · 3.12.3 | 1회 | 2-summary 머리말 |
| LEGB 네 층 2종 | `python3 - <ex.py` · 3.12.3 | 2회 | 1번 답 |
| `UnboundLocalError` 1종 | 〃 | 1회 | 2번 답 |
| `co_varnames`·`dis` 대조 | 〃 | 1회 | 7번 답 |
| `UnboundLocalError` 의 MRO·`e.name` | 〃 | 1회 | 9번 답 |
| `nonlocal` 오류 **5종** | 〃 — **각각 따로** | 5회 | 3번 답 |
| `global` 2종(바꾸기·만들기) | 〃 — 한 파일 | 1회 | 8번 답 |
| `nonlocal` 있고 없고 | 〃 | 1회 | 8번 답 |
| 클래스 몸통 4종 | 〃 — **각각 따로** | 4회 | 4번 답 |
| 컴프리헨션 스코프 3종 | 〃 — 한 파일 | 1회 | 5번 답 |
| 컴프리헨션 인라인 4표기 | 〃 | 1회 | 5번 답 |
| 컴프리헨션 `dis` 2종 | 〃 | 1회 | 11번 답 |
| 트레이스백 프레임 **3종** | 〃 — **각각 따로** | 3회 | 6번 답 |
| `locals()`·`globals()`·`co_freevars` | 〃 | 1회 | 10번 답 |
| 네 층의 바이트코드 | 〃 | 1회 | 11번 답 |

★ **재대조 기준** — 이 주제의 블록에는 **주소도 `id()` 값도 한 칸이 없다.**
같은 판에서 다시 돌리면 **한 글자도 안 변해야** 한다. 달라졌다면 그것은 「흔들림」이 아니라 **「고칠 것」이다.**

**구현 의존 항목 — 버전이 오르면 다시 돌려야 할 것**

- **예외 문구 전부**(2·3·4·9번 답) — 종류는 명세, 문구는 아니다.
  특히 `cannot access local variable …` 은 3.11 에서 손본 문장이다.
- **`Did you mean: 'self.class_var'?` 제안**(4번 답) — 제안 기능 자체가 판에 달렸다.
- **`UnboundLocalError` 의 `e.name` 이 `None` 인 것**(9번 답) — 채워질 수도 있다.
- **`dis` 의 명령 이름·오프셋**(7·11번 답) — `LOAD_FAST_CHECK`·`LOAD_FAST_AND_CLEAR`·`COPY_FREE_VARS` 는 3.12 의 것이다.
- ★ **컴프리헨션 인라인 여부와 트레이스백 프레임 수**(5·6번 답) — **PEP 709 는 3.12 의 변화**다.
  3.11 이하에서는 세 판 다 프레임이 하나씩 더 있다(**이 머신에 3.11 이하가 없어 직접 대조하지 못했다** — PEP 근거).
- **`nonlocal` 오류에 캐럿이 없는 것**(3번 답) — 진단 표시 방식이다.
</content>
