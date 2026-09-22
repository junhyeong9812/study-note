# python/syntax/02-is-vs-eq-interning — 질문

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

### 1. (예측)

```python
a = [1, 2, 3]
b = [1, 2, 3]
print(a == b, a is b)
print(id(a) == id(b))
```

- 두 줄의 출력은 각각 무엇인가?

### 2. (예측)

```python
p = int("257"); q = int("257")
print(p == q, p is q)
r = int("100"); s = int("100")
print(r == s, r is s)
```

- 두 줄의 출력이 갈린다면 무엇이 갈리고 그 원인은 무엇인가?

### 3. (예측)

```python
h1 = "hello"
h2 = "hel" + "lo"
h3 = "".join(["h", "e", "l", "l", "o"])
print(h1 is h2)
print(h1 == h3, h1 is h3)
```

- 세 개의 `"hello"` 중 어느 것이 같은 객체이고, 그 판정이 **언제**(컴파일 때인가 실행 때인가) 결정되는가?

### 4. (왜)

```python
class Weird:
    def __eq__(self, other):
        return True

w = Weird()
print(w == None)
print(w is None)
```

- 값이 `None` 인지 물을 때 `== None` 이 아니라 `is None` 을 써야 하는 이유는 무엇인가?

### 5. (예측)

```python
nan = float("nan")
print(nan == nan)
print(nan is nan)
print(nan in [nan])
print(nan in [float("nan")])
```

- 네 줄의 출력은 각각 무엇인가?

### 6. (예측)

```python
print(id([1, 2, 3]) == id([4, 5, 6]))
a = [1, 2, 3]; b = [4, 5, 6]
print(id(a) == id(b))
print(True == 1, True is 1)
print(1 in [True])
```

- 네 줄의 출력은 각각 무엇이고, 첫 줄과 둘째 줄이 갈리는 이유는 무엇인가?

### 7. (경계)

- `is` 로 물어도 되는 값은 어떤 것들이고, 그 밖의 값에 `is` 를 쓴 코드가 **테스트는 통과하면서 틀린 상태**가 되는 이유는 무엇인가?

### 8. (경계)

- 이 주제에서 **CPython 구현 세부사항**인 것과 **언어가 보장하는 것**을 각각 나열할 수 있는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
