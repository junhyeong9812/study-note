# python/syntax/24-decorators — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
>
> 이 갈래는 **예측형**이다 — 「무엇을 아는가」가 아니라 「**이 코드의 출력을 예측할 수 있는가**」를 묻는다.
> 코드가 있는 문항은 **돌려 보기 전에** 종이에 출력을 적고 시작한다.
> ★ 이 주제에서는 **「무엇이 찍히나」보다 「몇 번, 어떤 차례로 찍히나」가 답인 자리가 많다.**
> 줄의 내용만 맞히고 **차례**를 못 대면 반만 맞은 것이다.
>
> 실행 환경: `python3` **3.12.3** · Linux. 던지는 형태는 `python3 - <파일` 로 고정했다 —
> 트레이스백이 `File "<stdin>", line N` 으로 찍히고, **실행 중 예외에는 소스 줄도 캐럿도 안 나온다.**
> ★ **이 주제는 [19번](../19-function-argument-rules/2-summary.md)·[21번](../21-scope-legb-global-nonlocal/2-summary.md)·[22번](../22-closures-and-late-binding/2-summary.md)·[23번](../23-lambda-and-higher-order-functions/2-summary.md)을 전부 쓴다.**
> 막히면 그 넷 중 어느 것이 안 잡힌 것인지부터 짚어라.

## 질문

<!-- 형식: 질문 하나 = "?" 하나 = 한 줄.
     유형 태그: (왜) / (예측) / (경계) / (연결) -->

### 1. `@` 로 붙인 쪽과 손으로 푼 쪽 (예측)

```python
# e24_desugar.py
def deco(fn):
    print("  deco 가 돈다:", fn.__name__)
    return fn


print("① @ 문법")


@deco
def a():
    pass


print("② 손으로 푼 것")


def b():
    pass


b = deco(b)
print("③ 둘이 같은 일인가:", a is not None and b is not None)
```

- **몇 줄이 어떤 차례로** 찍히는가?
- `@deco` 와 `b = deco(b)` 가 **같은 일인가 다른 일인가** — 다르다면 무엇이 다른가?

### 2. 지나가기만 하고 두 번 부르면 (예측)

```python
# e24_define_time.py
def deco(fn):
    print("  [정의 시점] deco 실행 — 받은 것:", fn.__name__)

    def wrapper(*a, **k):
        print("  [호출 시점] wrapper 실행")
        return fn(*a, **k)

    return wrapper


print("① def 문을 만나기 전")


@deco
def work():
    return "결과"


print("② def 문을 지난 뒤 — 아직 한 번도 안 불렀다")
print("③ 첫 호출:", work())
print("④ 둘째 호출:", work())
```

- `[정의 시점]` 과 `[호출 시점]` 이 **각각 몇 번** 찍히는가? 순서까지 적어라.
- 이 프로그램에서 **함수 몸통이 처음 도는 것은 몇 번째 줄이 찍힌 뒤**인가?

### 3. 세 겹을 쌓으면 어떤 차례로 (예측)

```python
# e24_stack_order.py
def make(tag):
    def deco(fn):
        print("  적용:", tag)

        def wrapper(*a, **k):
            print("  들어감:", tag)
            r = fn(*a, **k)
            print("  나옴  :", tag)
            return r

        return wrapper

    return deco


print("① 적용 순서 (def 문을 지날 때)")


@make("바깥")
@make("가운데")
@make("안쪽")
def f():
    print("  몸통")
    return 1


print("② 호출 순서")
f()
```

- `적용:` 세 줄의 차례는?
- `들어감`·`나옴`·`몸통` 을 합쳐 **몇 줄**이 나오고 그 차례는 어떻게 되는가?

### 4. 괄호 안에 숫자를 주는 데코레이터 (예측)

```python
# e24_args_deco.py
import functools


def repeat(times):
    print("  [1층] repeat 가 돈다 — times =", times)

    def deco(fn):
        print("  [2층] deco 가 돈다 — fn =", fn.__name__)

        @functools.wraps(fn)
        def wrapper(*a, **k):
            print("  [3층] wrapper 가 돈다")
            out = [fn(*a, **k) for _ in range(times)]
            return out

        return wrapper

    return deco


print("① def 문을 지난다")


@repeat(3)
def hello(name):
    return "안녕 " + name


print("② 호출한다")
print("결과:", hello("파이썬"))
```

- `[1층]`·`[2층]`·`[3층]` 이 각각 **①과 ② 중 어느 쪽 뒤에** 찍히는가?
- 마지막 `결과:` 줄에는 무엇이 찍히는가?

### 5. 감싸기 전과 감싼 뒤, 일곱 칸 (예측)

```python
# e24_wraps_missing.py
def deco(fn):
    def wrapper(*a, **k):
        return fn(*a, **k)

    return wrapper


def target(a, b: int = 1) -> int:
    """이 함수가 하는 일."""
    return a + b


target.retries = 3

wrapped = deco(target)

for attr in ("__name__", "__qualname__", "__doc__", "__module__",
             "__annotations__", "__dict__"):
    print("%-15s 원본: %-34r 감싼 뒤: %r"
          % (attr, getattr(target, attr), getattr(wrapped, attr)))
print("%-15s 원본: %-34r 감싼 뒤: %r"
      % ("__wrapped__", getattr(target, "__wrapped__", "(없음)"),
         getattr(wrapped, "__wrapped__", "(없음)")))
```

- 일곱 칸 각각 **원본과 감싼 뒤가 같은가 다른가**? 다르면 감싼 쪽이 무엇이 되는가?
- ★ 원본과 **같은 값이 나오는 칸이 있는가**? 있다면 어느 칸이고 왜 그런가?

### 6. `inspect.signature` 가 감싼 함수를 보면 (예측)

```python
# e24_signature.py
import functools
import inspect


def plain_deco(fn):
    def wrapper(*a, **k):
        return fn(*a, **k)

    return wrapper


def wraps_deco(fn):
    @functools.wraps(fn)
    def wrapper(*a, **k):
        return fn(*a, **k)

    return wrapper


def target(a, b=1, *, c):
    return a + b


print("원본                :", inspect.signature(target))
print("wraps 없이 감싼 것    :", inspect.signature(plain_deco(target)))
print("wraps 로 감싼 것      :", inspect.signature(wraps_deco(target)))
print("follow_wrapped=False :", inspect.signature(wraps_deco(target), follow_wrapped=False))
print("unwrap 으로 벗기면    :", inspect.unwrap(wraps_deco(target)) is target)
print("도움말이 보는 이름    :", wraps_deco(target).__name__, "대", plain_deco(target).__name__)
```

- 여섯 줄이 각각 무엇을 찍는가?
- ★ `follow_wrapped=False` 줄은 **앞의 세 줄 중 어느 것과 같은가**? 그것이 `wraps` 에 대해 무엇을 증명하는가?

### 7. `functools.wraps` 가 옮기는 것과 새로 붙이는 것 (왜)

- `wraps` 를 빼면 잃는 것을 **속성 이름으로 전부** 댈 수 있는가?
- ★ 그중 **`__wrapped__` 는 왜 「잃는 것」 목록에 넣으면 안 되는가**?
- ★ `__dict__` 한 칸만 **다른 방식**으로 처리되는 것은 어느 상수가 말해 주는가?

### 8. 괄호를 빠뜨리면 어디서 터지나 (경계)

```python
# e24_missing_call.py
import functools


def repeat(times):
    def deco(fn):
        @functools.wraps(fn)
        def wrapper(*a, **k):
            return [fn(*a, **k) for _ in range(times)]

        return wrapper

    return deco


@repeat
def hello(name):
    return "안녕 " + name


print("hello 의 정체 :", hello.__name__, "·", type(hello).__name__)
print("한 번 부르면  :", hello("파이썬").__qualname__)
print("그것을 또 부르면 —")
hello("파이썬")()
```

- `@repeat` 를 괄호 없이 붙였다. **정의하는 순간에 터지는가**?
- 이름 `hello` 는 무엇을 가리키게 되며, **예외는 몇 번째 호출에서 어느 줄** 때문에 나는가?

### 9. 데코레이터가 함수가 아닌 것을 돌려주면 (경계)

- 데코레이터가 문자열을 `return` 했다. **정의가 통과하는가**?
- 통과한다면 **언제** 무엇이 나는가? 레퍼런스의 "The result must be a callable" 은 **무엇에 대한 제약**인가?

### 10. 두 겹을 쌓았을 때 원본 꺼내기 (경계)

- `@tag("바깥")` 과 `@tag("안쪽")` 을 쌓았다. `__wrapped__` 를 **몇 번** 따라가야 원본에 닿는가?
- `inspect.unwrap` 이 하는 일을 한 줄로 말하고, **그것으로 꺼낸 함수를 그냥 부르면 무엇이 사라지는지** 댈 수 있는가?
- 겹 중 하나가 `wraps` 를 안 붙였다면 이 체인은 어떻게 되는가?

### 11. 데코레이터의 실체는 무엇인가 (연결)

- 감싼 함수의 `co_freevars` 에는 **어떤 이름들**이 들어 있고 **셀은 몇 개**인가?
- ★ `fn` 셀에 들어 있는 것과 `__wrapped__` 는 **같은 객체인가**?
- 이것이 [22번](../22-closures-and-late-binding/2-summary.md)의 무엇과 같은 이야기인지 한 줄로 이을 수 있는가?

### 12. 세 층 가르기와 이웃 경계 (경계)

- 이 주제에서 **언어 보장** · **CPython 구현 세부사항** · **이 판(3.12.3)의 관찰**에 해당하는 것을 각각 둘 이상 댈 수 있는가?
- **「`def` 문이 돌 때 한 번」이 어디까지 이 주제이고 어디부터 [20번](../20-mutable-default-args/2-summary.md)인지** 한 줄로 그을 수 있는가?
- 클래스에 붙는 데코레이터는 **문법이 다른가**, 그리고 그 정본은 어디인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
