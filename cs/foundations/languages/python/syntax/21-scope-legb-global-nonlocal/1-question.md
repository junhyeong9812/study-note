# python/syntax/21-scope-legb-global-nonlocal — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
>
> 이 갈래는 **예측형**이다 — 「무엇을 아는가」가 아니라 「**이 코드의 출력을 예측할 수 있는가**」를 묻는다.
> 코드가 있는 문항은 **돌려 보기 전에** 종이에 출력을 적고 시작한다.
> ★ 이 주제에서는 **「무슨 예외인가」보다 「어느 줄에서 나는가」가 답인 자리가 많다.**
> 예외 이름만 맞히고 **줄 번호**를 못 대면 반만 맞은 것이다.
>
> ★★ **이 주제는 사슬의 첫 고리다** — [22번](../22-closures-and-late-binding/1-question.md)(클로저)·[23번](../23-lambda-and-higher-order-functions/1-question.md)(`lambda`)·[24번](../24-decorators/1-question.md)(데코레이터)이 전부 여기 위에 선다.
> 여기서 틀린 것은 그 셋에서 그대로 다시 틀린다.
>
> 실행 환경: `python3` **3.12.3**(Linux). 던지는 형태는 `python3 - <파일` 로 고정했다 —
> 트레이스백이 `File "<stdin>", line N` 이 된다.
> ★ **캐럿 규칙** — 실행 중 예외에는 소스 줄도 캐럿도 안 나오고, `SyntaxError` 에는 대개 나온다.
> **다만 이 주제의 `SyntaxError` 다섯은 전부 캐럿이 안 나온다** — 그것이 3번 문항의 답 절반이다.
> ★ **소스 펜스의 첫 줄은 캡처가 붙인 파일명 주석**이다. 줄 번호를 셀 때는 그 주석을 빼고 센다.

## 질문

<!-- 형식: 질문 하나 = "?" 하나 = 한 줄.
     유형 태그: (왜) / (예측) / (경계) / (연결) -->

### 1. 네 층에 같은 이름을 두고 차례로 가리면 (예측)

먼저 이쪽.

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

그리고 따로 던진 이쪽. 가리는 이름으로 일부러 내장 `len` 을 썼다.

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

- 두 판의 출력을 **한 줄씩 다 적을 수 있는가**?
- ⑤ 의 `del len` 이 **무엇을 지운 것인지** 한 문장으로 말할 수 있는가?

### 2. 읽기만 하려던 참이었다 (예측)

```python
# e21_unbound.py
count = 10


def bump():
    print("읽기만 하려던 참이다:", count)
    count = count + 1
    return count


bump()
```

- 무엇이 **몇 번 줄에서** 나는가? 그리고 `읽기만 하려던 참이다:` 가 **찍히는가**?
- 이 함수에서 `count = count + 1` 한 줄을 지우면 출력이 어떻게 달라지는가?

### 3. `nonlocal` 다섯 자리 (예측)

다섯 개를 **따로따로** 던졌다.

```python
# e21_nonlocal_module.py
x = 1
nonlocal x
```

```python
# e21_nonlocal_top.py
def show():
    return "이 줄은 돌지 않는다"


nonlocal never_assigned_here
```

```python
# e21_nonlocal_missing.py
def outer():
    def inner():
        nonlocal never_bound
        never_bound = 1

    inner()
```

```python
# e21_nonlocal_global.py
g = 1


def only_global_exists():
    nonlocal g
    g = 2
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

- 다섯의 **예외 종류**와 **메시지 본문**을 각각 댈 수 있는가?
- 다섯 중 **문구가 겹치는 짝**은 어느 것들인가?
- 이 다섯은 **언제** 나는가 — 그 함수를 부를 때인가, 부르지 않아도 나는가?
- 두 번째 판의 `def show()` 는 **정의되는가**?

### 4. 클래스 몸통이 보는 것과 메서드가 보는 것 (예측)

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

```python
# e21_class_comprehension.py
class C:
    rows = [1, 2, 3]
    factor = 10
    doubled = [r * 2 for r in rows]
    print("첫 이터러블은 보인다:", doubled)
    scaled = [r * factor for r in rows]
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

- 네 판이 각각 무엇을 찍고 어디서 터지는가?
- 둘째 판에서 **같은 줄의 두 이름**(`rows` 와 `factor`)이 갈리는 이유는?
- 셋째 판이 **되는데** 모듈 수준의 `nonlocal` 은 안 되는 것을 한 문장으로 설명할 수 있는가?
- 넷째 판에서 `C` 에 `tag` 라는 속성이 **생기는가**?

### 5. 컴프리헨션 안의 이름은 어디까지 가나 (예측)

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

그리고 네 표기를 한 번에 재 본 이쪽.

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

- 첫 판의 네 줄을 적을 수 있는가?
- 둘째 판에서 **별도 코드 객체가 남는 것**은 몇 개이고 어느 것인가?
- 그중 **언어가 보장하는 것**과 **CPython 3.12 의 구현**은 각각 어디까지인가?

### 6. 세 표기를 같은 방식으로 터뜨려 보면 (예측)

셋을 따로 던졌다.

```python
# e21_comprehension_frame.py
def boom_listcomp():
    return [1 / n for n in (1, 0)]


boom_listcomp()
```

```python
# e21_comprehension_frame_set.py
def boom_setcomp():
    return {1 / n for n in (1, 0)}


boom_setcomp()
```

```python
# e21_comprehension_frame_gen.py
def boom_genexp():
    return list(1 / n for n in (1, 0))


boom_genexp()
```

- 세 트레이스백의 **줄 수**가 같은가? 다르다면 어느 것이 다르고 그 줄에 무엇이 적히는가?
- 그 차이를 **5번 문항의 두 번째 판**과 이어서 설명할 수 있는가?

### 7. 왜 대입한 줄이 아니라 그 앞줄에서 나나 (왜)

- 「블록 안 **어디든** 바인딩이 있으면 그 블록의 모든 사용이 지역 참조다」라는 규칙이
  **왜 줄 순서를 안 봐주는지**, 그리고 그것이 **언어 보장인지 CPython 구현인지** 말할 수 있는가?
- `count += 1` 로 바꾸면 달라지는가? `for count in …` 이면? `import count` 면?

### 8. `global` 과 `nonlocal` 의 비대칭 (경계)

- 둘을 **한 표로** 가를 수 있는가 — 어느 칸을 가리키나, **없는 이름을 만들 수 있나**, 못 쓰는 자리는 어디인가, 어기면 언제 무엇이 나나?
- `nonlocal` 로 **전역 이름**을 고치려 하면 무엇이 나는가? 그 문구가 **헷갈리는 이유**는?

### 9. 칸이 없는 것과 칸이 빈 것 (경계)

- `NameError` 와 `UnboundLocalError` 의 **관계**를 말하고, `except NameError` 로 **둘 다 잡히는지** 답할 수 있는가?
- 잡은 예외에서 **문제가 된 이름**을 문구 파싱 없이 얻을 수 있는가?

### 10. 층마다 무엇이 보이나 (경계)

- 중첩 함수 안에서 `locals()` 를 부르면 **바깥 함수의 이름이 들어 있는가**? 그 이유는?
- `co_freevars` 에는 무엇이 들어가고, 그것이 `globals()` 와 어떻게 갈리는가?
- 모듈 수준에서 `locals() is globals()` 는 무엇인가?

### 11. 세 층 가르기 (경계)

- 이 주제에서 **언어 보장** · **CPython 구현 세부사항** · **이 판(3.12.3)의 관찰**에 해당하는 것을 각각 나열할 수 있는가?
- **네 층(LEGB)이 네 가지 바이트코드 명령으로 갈리는가**? 답과 그 근거를 댈 수 있는가?

### 12. 사슬의 첫 고리 (연결)

- 이 주제가 [22번](../22-closures-and-late-binding/2-summary.md)·[23번](../23-lambda-and-higher-order-functions/2-summary.md)·[24번](../24-decorators/2-summary.md)의 **무엇을 떠받치는지** 한 줄씩 말할 수 있는가?
- 인라인화 이야기는 **어디까지가 이 주제이고 어디부터가 [14번](../14-comprehensions/2-summary.md)·[15번](../15-generator-expressions-lazy-eval/2-summary.md)인지** 선을 그을 수 있는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
</content>
