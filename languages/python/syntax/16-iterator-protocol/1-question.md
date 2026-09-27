# python/syntax/16-iterator-protocol — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
>
> 이 갈래는 **예측형**이다 — 「무엇을 아는가」가 아니라 「**이 코드의 출력을 예측할 수 있는가**」를 묻는다.
> 코드가 있는 문항은 **돌려 보기 전에** 종이에 출력을 적고 시작한다.
> ★ 이 주제에서는 **「구분이 되나 안 되나」가 답인 자리가 있다.** 「안 된다」도 답이다 —
> **어떤 검사로 안 되는지까지 대는 것**이 한 문항이다.
> 실행 환경: `python3` 3.12.3. 던지는 형태는 `python3 - <파일` 로 고정했다.

## 질문

<!-- 형식: 질문 하나 = "?" 하나 = 한 줄.
     유형 태그: (왜) / (예측) / (경계) / (연결) -->

### 1. `for` 를 세 조각으로 뜯으면 (예측)

```text
===== 소스: ex.py =====
xs = ["a", "b"]
it = iter(xs)
print("iter(xs)        ->", type(it).__name__)
print("next            ->", next(it))
print("next            ->", next(it))
try:
    next(it)
except StopIteration as e:
    print("next            -> StopIteration", repr(e.value), "| args =", e.args)
print("next(it, '기본') ->", next(it, "기본"))
print("두 번째 list(it) ->", list(it), " <- 예외가 아니다")
```

- 마지막 줄이 `[]` 인 것은 **구현의 편의인가 명세인가**, 근거는?

### 2. 열한 개 객체의 세 열 (예측)

```text
===== 소스: ex.py =====
import sys
print("python", ".".join(map(str, sys.version_info[:3])))

def gen():
    yield 1

objs = [
    ("[1, 2]", [1, 2]),
    ("iter([1, 2])", iter([1, 2])),
    ("(1, 2)", (1, 2)),
    ("'ab'", "ab"),
    ("range(3)", range(3)),
    ("iter(range(3))", iter(range(3))),
    ("gen()", gen()),
    ("enumerate('ab')", enumerate("ab")),
    ("zip('ab', 'cd')", zip("ab", "cd")),
    ("map(str, [1])", map(str, [1])),
    ("reversed([1, 2])", reversed([1, 2])),
]
print(f"{'object':<16}{'__iter__':>9}{'__next__':>10}{'iter(x) is x':>14}")
for name, o in objs:
    print(f"{name:<16}{str(hasattr(o, '__iter__')):>9}"
          f"{str(getattr(o, '__next__', None) is not None):>10}{str(iter(o) is o):>14}")
```

- **아무것도 못 가르는 열**이 하나 있다 — 어느 것이고 왜인가?
- 이 표에서 **실무 사고가 가장 많이 나는 네 줄**은 어느 것인가?

### 3. 기계와 번호표를 나눠 쓰고, 계약을 하나 어기면 (예측)

```text
===== 소스: ex.py =====
class Countdown:              # 이터러블 — 돌 때마다 새 이터레이터를 준다
    def __init__(self, n): self.n = n
    def __iter__(self): return CountdownIter(self.n)

class CountdownIter:          # 이터레이터 — 자기 자신을 돌려준다
    def __init__(self, n): self.k = n
    def __iter__(self): return self
    def __next__(self):
        if self.k <= 0:
            raise StopIteration
        self.k -= 1
        return self.k + 1

c = Countdown(3)
print("두 번 돌린다 :", list(c), list(c))
it = iter(c)
print("이터레이터를 직접 두 번 :", list(it), list(it))
print("iter(c) is c :", iter(c) is c, "| iter(it) is it :", iter(it) is it)

class Broken:                 # __iter__ 가 자기를 안 돌려주는 이터레이터
    def __iter__(self): return CountdownIter(2)
    def __next__(self): raise StopIteration

b = Broken()
print("__next__ 는 있는데 __iter__ 가 남을 주면 :", list(b))
print("  next(b) 는 :", end=" ")
try:
    next(b)
except StopIteration:
    print("StopIteration")

class NoNext:
    def __iter__(self): return self
n = NoNext()
try:
    for _ in n: pass
except TypeError as e:
    print("__next__ 없이 __iter__ 만 :", type(e).__name__ + ":", e)
```

- **두 가지 계약 위반 중 한쪽만 언어가 잡아 준다** — 어느 쪽이 안 잡히고, 왜 그쪽이 더 나쁜가?

### 4. 특수 메서드가 하나도 없는 클래스를 `for` 에 넣으면 (예측)

```text
===== 소스: ex.py =====
class Old:
    def __init__(self, data): self.data = data
    def __getitem__(self, i):
        print("   __getitem__", i)
        return self.data[i]

o = Old(["x", "y"])
print("__iter__ 가 있나 :", hasattr(o, "__iter__"))
print("__next__ 가 있나 :", getattr(o, "__next__", None) is not None)
print("for 가 도나 :")
for v in o:
    print("  받음:", v)
print("iter(o) ->", type(iter(o)).__name__)
print("list(o) ->", list(o))
print("'x' in o ->", "x" in o)
print("reversed 는?")
try:
    print(list(reversed(o)))
except TypeError as e:
    print("   TypeError:", e)
```

- `__getitem__` 이 **몇 번** 불렸고, 그 개수가 **무엇을 증명**하는가?
- 이 객체에 `hasattr(o, '__iter__')` 검사를 쓰면 무엇이 잘못되는가?

### 5. 제너레이터 안에서 `next` 를 맨손으로 쓰면 (예측)

```text
===== 소스: ex.py =====
def take_two(it):
    yield next(it)
    yield next(it)

print(list(take_two(iter([1, 2]))))
print(list(take_two(iter([1]))))
```

- **3.6 이전이었다면 둘째 줄이 무엇이었을지** 말하고, 그 변화가 무엇을 무엇으로 바꾼 것인지 설명할 수 있는가?

### 6. 넷을 바깥에서 가를 수 있나 (예측)

```text
===== 소스: ex.py =====
def src():
    yield 1
    yield 2

full  = src()
spent = src(); list(spent)
empty = iter([])
worn  = iter([1]); next(worn)

print("--- 바깥에서 보이는 것만으로 넷을 가를 수 있나 ---")
rows = [("아직 안 돈 제너레이터", full), ("소진된 제너레이터", spent),
        ("처음부터 빈 이터레이터", empty), ("소진된 리스트 이터레이터", worn)]
for name, o in rows:
    print("  bool={0!s:<5} iter(x) is x={1!s:<5} next(x,'없음')={2!r:<8} <- {3}".format(
        bool(o), iter(o) is o, next(o, "없음"), name))

print()
print("--- 제너레이터만은 안이 보인다 (CPython 내성) ---")
a = src()
def snap(tag, g):
    print("  {0:<10} gi_frame={1!s:<6} gi_running={2!s:<6} gi_suspended={3!s:<6}".format(
        tag, g.gi_frame is not None, g.gi_running, g.gi_suspended))
snap("만든 직후", a); next(a); snap("next 1회", a); list(a); snap("소진 후", a)

print()
print("--- 남은 개수 힌트도 둘을 못 가른다 ---")
b = iter([1, 2])
print("  소진 전 iter([1,2]).__length_hint__() =", b.__length_hint__())
list(b)
print("  소진 후                               =", b.__length_hint__())
print("  iter([]).__length_hint__()            =", iter([]).__length_hint__())
```

- 첫 덩어리에서 **검사하는 행위 자체가 무엇을 했는가**?
- `gi_frame` 으로 알 수 있는 것과 **여전히 알 수 없는 것**은 각각 무엇인가?

### 7. 왜 `__iter__` 가 `self` 여야 하나 (왜)

- 이 계약이 없으면 **`for` 문 쪽 코드가 무엇을 못 하게 되는지** 한 문장으로 말할 수 있는가?

### 8. 센티널이 결과에 들어가나 (경계)

- `iter([3, 1, 0, 9].pop, 0)` 이 무엇을 내는지 말하고, **왜 그 개수인지** 설명할 수 있는가?

### 9. 「이터러블인가」를 바르게 검사하는 법 (경계)

- `hasattr(x, '__iter__')` 와 `isinstance(x, collections.abc.Iterable)` 이 **둘 다 놓치는 것**을 대고, 바른 검사를 말할 수 있는가?

### 10. 조용한 실패를 어디서 막나 (연결)

- 「함수에 넘긴 이터러블이 두 번째 루프에서 비어 있었다」를 **호출하는 쪽**과 **받는 쪽** 각각에서 어떻게 막는가?

### 11. 세 층 가르기 (경계)

- 이 주제에서 **언어 보장** · **CPython 구현 세부사항** · **이 판(3.12.3)의 관찰**에 해당하는 것을 각각 나열할 수 있는가?

### 12. 이웃 주제와의 경계 (연결)

- [15번](../15-generator-expressions-lazy-eval/2-summary.md)·[17번](../17-generators-yield/2-summary.md)·[18번](../18-loop-control-and-else/2-summary.md)이 각각 **어디까지**이고 이 주제가 **어디부터**인지 한 줄씩 그을 수 있는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
