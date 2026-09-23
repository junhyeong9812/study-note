# python/syntax/03-mutability-and-copying — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
>
> 이 갈래는 **예측형**이다 — 「무엇을 아는가」가 아니라 「**이 코드의 출력을 예측할 수 있는가**」를 묻는다.
> 코드가 있는 문항은 **돌려 보기 전에** 종이에 출력을 적고 시작한다.
> 실행 환경: `python3` 3.12.3.
> 선행: [목록의 **01번 주제**](../01-object-and-name-binding/) — 「변수는 이름표」를 먼저 답할 수 있어야 4·11번이 풀린다.

## 질문

<!-- 형식: 질문 하나 = "?" 하나 = 한 줄.
     유형 태그: (왜) / (예측) / (경계) / (연결) -->

### 1. 얕은 복사 네 형태는 다른가 (예측)

```python
import copy
orig = [[1, 2], [3, 4]]
for name, c in {
    "list(x)":   list(orig),
    "x[:]":      orig[:],
    "copy.copy": copy.copy(orig),
    "x.copy()":  orig.copy(),
}.items():
    print(f"{name:11} {c is orig} {c[0] is orig[0]}")
```

- 네 줄의 출력은 각각 무엇이고, 네 형태 중 「더 깊은」 것이 있는가?

### 2. `+=` 와 `= x + y` 가 갈리는 자리 (예측)

```python
p = [1]; q = p
p += [2]
print(q)

p = [1]; q = p
p = p + [2]
print(q)

s = "ab"; before = id(s)
s += "c"
print(id(s) == before)
```

- 세 줄의 출력은 각각 무엇이고, 리스트와 문자열에서 `+=` 의 의미가 어떻게 달라지는가?

### 3. 불변 안의 가변 (예측)

```python
t = ([], "고정")
before = id(t)
t[0].append(1)
print(t)
print(id(t) == before)
```

- 두 줄의 출력은 각각 무엇이고, 「튜플은 불변」이라는 말이 정확히 무엇을 보장하는가?

### 4. 에러가 났는데 값이 바뀌어 있다 (예측)

```python
u = ([1], "x")
try:
    u[0] += [3]
except TypeError as e:
    print("TypeError:", e)
print(u)

t = (1, "x")
try:
    t[0] += 1
except TypeError as e:
    print("TypeError:", e)
print(t)
```

- 네 줄의 출력은 각각 무엇이고, 같은 오류 메시지인데 결과가 갈리는 이유를 `dis` 로 어떻게 보이는가?

### 5. 깊은 복사와 순환·공유 (예측)

```python
import copy
a = [1, 2]
a.append(a)
b = copy.deepcopy(a)
print(b[2] is b, b is a)

shared = [0]
src = [shared, shared]
dst = copy.deepcopy(src)
print(dst[0] is dst[1], dst[0] is src[0])
```

- 두 줄의 출력은 각각 무엇이고, `deepcopy` 가 「전부 새로 만든다」와 어떻게 다른가?

### 6. 복사가 안 되는 것 (예측)

```python
import copy, threading, math
def fn(): pass

try:
    copy.deepcopy(threading.Lock())
except TypeError as e:
    print("Lock:", e)
print("함수:", copy.deepcopy(fn) is fn)
try:
    copy.deepcopy(math)
except TypeError as e:
    print("모듈:", e)
```

- 세 줄의 출력은 각각 무엇이고, 문서의 「이 모듈은 \~를 복사하지 않는다」가 뜻하는 결과가 몇 가지인가?

### 7. 왜 기본이 얕은가 (왜)

- 파이썬의 복사가 **기본적으로 얕은** 이유를 [01번](../01-object-and-name-binding/2-summary.md)의 「이름표」 모델로 한 문장으로 설명할 수 있는가?

### 8. 무엇을 dict 키로 쓸 수 있나 (경계)

- `hash(([1], 2))` 가 실패하는데 `hash(((1,), 2))` 는 되는 이유는 무엇이고, 그 오류가 `tuple` 이 아니라 `list` 를 가리키는 것은 무엇을 뜻하는가?

### 9. 불변이면 복사가 자기 자신인가 (경계)

- `copy.deepcopy(x) is x` 가 `int`·`str`·`tuple` 에서는 참인데 `frozenset` 에서는 거짓이었다 — 이것을 「규칙」으로 적어도 되는가, 「관찰」로 적어야 하는가?

### 10. 세 층 가르기 (경계)

- 이 주제에서 **언어 보장** · **CPython 구현 세부사항** · **이 판(3.12.3)의 관찰**에 각각 해당하는 것을 나열할 수 있는가?

### 11. 실무에서 물리는 자리 (연결)

- 설정 딕셔너리를 `.copy()` 로 나눠 줬는데 **한 요청의 변경이 다음 요청에 남는** 버그를 진단하고, 고치는 선택지 셋을 비용과 함께 댈 수 있는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
