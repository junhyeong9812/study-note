# python/syntax/20-mutable-default-args — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
>
> 이 갈래는 **예측형**이다 — 「무엇을 아는가」가 아니라 「**이 코드의 출력을 예측할 수 있는가**」를 묻는다.
> 코드가 있는 문항은 **돌려 보기 전에** 종이에 출력을 적고 시작한다.
> 실행 환경: `python3` 3.12.3.

## 질문

<!-- 형식: 질문 하나 = "?" 하나 = 한 줄.
     유형 태그: (왜) / (예측) / (경계) / (연결) -->

### 1. 세 번 부르면 (예측)

```python
def add_item(item, bag=[]):
    bag.append(item)
    return bag

print(add_item("사과"))
print(add_item("배"))
print(add_item("감"))
```

- 세 줄의 출력은 각각 무엇인가?

### 2. 두 호출이 받는 리스트 (예측)

```python
print(add_item.__defaults__)
print(id(add_item.__defaults__[0]))
add_item("귤")
print(add_item.__defaults__)
print(id(add_item.__defaults__[0]))
```

- 두 `id` 값은 같은가 다른가, 그리고 그 답이 1번의 출력을 어떻게 설명하는가?

### 3. `side()` 가 불리는 횟수와 시점 (예측)

```python
def side():
    print("   side() 실행됨")
    return []

print("def 문 실행 전")
def g(x, acc=side()):
    acc.append(x)
    return acc
print("def 문 실행 끝")
print(g(1))
print(g(2))
```

- `side() 실행됨` 은 몇 번, 어느 줄들 사이에 찍히는가?

### 4. 나중에 바꾼 값이 보이나 (예측)

```python
LIMIT = 10
def clamp(v, top=LIMIT):
    return min(v, top)

LIMIT = 100
print(clamp(50))
```

- 출력은 무엇이고, 가변 기본값 함정과 무엇이 같고 무엇이 다른가?

### 5. `None` 센티널이 옮긴 것 (왜)

```python
def add_item_fixed(item, bag=None):
    if bag is None:
        bag = []
    bag.append(item)
    return bag
```

- 이 고침이 실제로 무엇을 옮긴 것인가?

### 6. 두 인스턴스의 상태 (예측)

```python
class Logger:
    def __init__(self, lines=[]):
        self.lines = lines
    def log(self, msg):
        self.lines.append(msg)

a = Logger(); b = Logger()
a.log("a 의 로그")
print(b.lines)
print(a.lines is b.lines)
```

- 두 줄의 출력은 각각 무엇인가?

### 7. `dataclasses` 는 거부한다 (경계)

```python
from dataclasses import dataclass

@dataclass
class Cart:
    items: list = []
```

- 이 코드는 어떻게 되고, `dataclasses` 가 주는 대안은 무엇이며 그것이 `None` 센티널과 같은 해법인 이유는 무엇인가?

### 8. 전부 언어 보장이다 (경계)

- 이 주제의 동작은 **CPython 구현 세부사항**인가 **언어가 보장하는 것**인가, 그리고 그 판단의 근거는 무엇인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
