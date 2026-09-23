# python/syntax/15-generator-expressions-lazy-eval — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
>
> 이 갈래는 **예측형**이다 — 「무엇을 아는가」가 아니라 「**이 코드의 출력을 예측할 수 있는가**」를 묻는다.
> 코드가 있는 문항은 **돌려 보기 전에** 종이에 출력을 적고 시작한다.
> ★ 이 주제에서는 **값을 맞히는 것이 답이 아닌 문항이 많다** — 두 형태는 값이 같기 때문이다.
> **「무엇을 재야 차이가 보이나」까지가 한 문항**이다.
> 실행 환경: `python3` 3.12.3(바이트코드는 3.11.15 로 대조). 던지는 형태는 `python3 - <파일` 로 고정했다.

## 질문

<!-- 형식: 질문 하나 = "?" 하나 = 한 줄.
     유형 태그: (왜) / (예측) / (경계) / (연결) -->

### 1. 같은 값을 내는 두 줄을 재면 (예측)

```text
===== 소스: ex.py =====
import sys
print("python", ".".join(map(str, sys.version_info[:3])), "|", sys.implementation.name)
N = 1_000_000
lc = [x * 2 for x in range(N)]
ge = (x * 2 for x in range(N))
print("list comp  getsizeof :", sys.getsizeof(lc))
print("gen  expr  getsizeof :", sys.getsizeof(ge))
print("배수                 :", sys.getsizeof(lc) // sys.getsizeof(ge))
print("합이 같나            :", sum(lc) == sum(x * 2 for x in range(N)))
```

- 마지막 줄이 `True` 라는 것은 **이 주제에서 무엇을 뜻하는가**?
- **다시 돌렸을 때 대조해야 할 것**은 숫자인가 아닌가?

### 2. 재는 창을 바꾸면 (예측)

```text
===== 소스: ex.py =====
import tracemalloc
N = 1_000_000
tracemalloc.start()
total = sum([x * 2 for x in range(N)])
cur, peak = tracemalloc.get_traced_memory()
print(f"[...]  합={total}  현재={cur:>9}  최대={peak:>9} 바이트")
tracemalloc.reset_peak()
total = sum(x * 2 for x in range(N))
cur, peak = tracemalloc.get_traced_memory()
print(f"(...)  합={total}  현재={cur:>9}  최대={peak:>9} 바이트")
tracemalloc.stop()
```

- **`현재`(cur)가 아니라 `최대`(peak)를 봐야 하는 이유**는 무엇인가?
- 이 수치와 1번의 `getsizeof` 수치가 어긋난다면 **어느 쪽이 틀린 것인가**?

### 3. 없는 이름을 어디에 두느냐에 따라 (예측)

```text
===== 소스: ex.py =====
print("--- 1. 이름을 갈아 끼우면 ---")
src = [1, 2, 3]
g = (n for n in src)
src = [9, 9, 9]
print("  list(g) :", list(g))

print("--- 2. 같은 객체를 고치면 ---")
src2 = [1, 2, 3]
g2 = (n for n in src2)
src2.append(4)
print("  list(g2):", list(g2))

print("--- 3. 첫 for 의 이터러블은 즉시 평가된다 ---")
try:
    g3 = (x for x in nope_first)
except NameError as e:
    print("  만드는 자리에서 NameError:", e)

print("--- 4. 둘째 for 의 이터러블은 늦다 ---")
g4 = (x for outer in [[1, 2]] for x in nope_second)
print("  만들기는 됐다 ->", type(g4).__name__)
try:
    next(g4)
except NameError as e:
    print("  next 할 때 NameError:", e)
```

- 1번 판과 2번 판이 **왜 갈리는지** 한 문장으로 말할 수 있는가?
- 3번 판과 4번 판이 **한 식 안에서 무엇이 둘로 갈린다는 것**을 보이는가?

### 4. 같은 제너레이터를 네 함수에 차례로 주면 (예측)

```text
===== 소스: ex.py =====
g = (n for n in range(5))
print("첫 판 sum :", sum(g))
print("둘째 판   :", sum(g))
print("list      :", list(g))
print("max 는?   :", max(g, default="없음"))

lst = [n for n in range(5)]
print("리스트는 몇 번이든 :", sum(lst), sum(lst), list(lst))
```

- `max` 에서 `default=` 를 **빼면** 무엇이 달라지는가?
- 같은 원인이 **함수마다 다른 얼굴로** 나온다는 것이 왜 위험한가?

### 5. 파이프라인을 세 겹 쌓고 두 번 잘라 내면 (예측)

```text
===== 소스: ex.py =====
def naturals():
    n = 0
    while True:
        yield n
        n += 1

import itertools
squares = (n * n for n in naturals())
odd = (s for s in squares if s % 2 == 1)
print("처음 다섯 개 :", list(itertools.islice(odd, 5)))
print("이어서 세 개 :", list(itertools.islice(odd, 3)))
```

- 둘째 줄이 첫 줄과 **같은 값인가 다른 값인가**, 그리고 그 이유는?
- 이 코드에서 `list(odd)` 를 쓰면 **무슨 예외가 나는가**?

### 6. 네 줄이 각각 무엇을 내나 (예측)

```text
===== 소스: ex.py =====
g = (n for n in range(5))
try:
    len(g)
except TypeError as e:
    print("len(g)       -> TypeError:", e)
try:
    g[0]
except TypeError as e:
    print("g[0]         -> TypeError:", e)
print("sorted 는 되나 :", sorted(n for n in [3, 1, 2]), " <- 속으로 리스트를 만든다")
g2 = (n for n in range(5))
print("3 in g2      :", 3 in g2, "| 남은 것 :", list(g2), " <- in 이 먹었다")
print("개수를 세려면 :", sum(1 for _ in range(5)), " <- 그 순간 다 돈다")
```

- 이 다섯 줄 중 **지연의 이점을 스스로 지우는 줄**은 어느 것들인가?

### 7. `getsizeof` 하나로는 왜 주장을 못 하나 (왜)

- 문서의 낱말로 `getsizeof` 의 범위를 말하고, 실측에서 **몇 배가 어긋났는지** 댈 수 있는가?

### 8. 제너레이터 객체의 크기를 바꾸는 것 (경계)

- 원소 5개와 100만개의 제너레이터가 **같은 크기**였는데, 그 숫자가 **달라지는 조건은 무엇인가**?

### 9. 리스트로 돌아가야 하는 자리 (경계)

- 「제너레이터로 바꿨는데 메모리가 안 줄었다」의 가장 흔한 원인 셋을 대고, 각각을 무엇으로 진단할지 말할 수 있는가?

### 10. 바이트코드가 말하는 두 가지 (연결)

- `[x for x in it]` 과 `(x for x in it)` 의 역어셈블을 나란히 놓았을 때 **한눈에 다른 것**과
  **두 판(3.11·3.12)에서 안 변한 것**을 각각 대고, 그중 **어느 것이 언어 보장인지** 가를 수 있는가?

### 11. 세 층 가르기 (경계)

- 이 주제에서 **언어 보장** · **CPython 구현 세부사항** · **이 판(3.12.3)·이 머신의 관찰**에 해당하는 것을 각각 나열할 수 있는가?

### 12. 이 측정으로 주장할 수 있는 것과 없는 것 (왜)

- 「전부 소비」 줄과 「앞 1개만」 줄의 **신뢰도가 왜 다른지** 말하고, 「제너레이터가 느리다」를 **왜 못 적는지** 설명할 수 있는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
