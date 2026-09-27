# python/syntax/13-set-and-frozenset — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
>
> 이 갈래는 **예측형**이다 — 「무엇을 아는가」가 아니라 「**이 코드의 출력을 예측할 수 있는가**」를 묻는다.
> 코드가 있는 문항은 **돌려 보기 전에** 종이에 출력을 적고 시작한다.
> ★ 이 주제에서는 **「갈리나 안 갈리나」가 답인 자리가 많다.** 한 판만 돌려 보고 답을 적지 마라 —
> **시드를 바꿔 던지는 것까지가 한 문항**이다.
> 실행 환경: `python3` 3.12.3(일부 문항은 3.11.15 로 대조).

## 질문

<!-- 형식: 질문 하나 = "?" 하나 = 한 줄.
     유형 태그: (왜) / (예측) / (경계) / (연결) -->

### 1. 시드를 바꿔 세 번 돌리면 (예측)

```text
===== 소스: ex.py =====
print("문자열 :", list({"apple", "banana", "cherry", "date", "elderberry"}))
print("정수   :", list({1, 2, 3, 4, 5, 100, 200}))
print("섞으면 :", list({1, "a", 2, "b", (3, 4)}))
print("hash('a') =", hash("a"), "| hash(1) =", hash(1), "| hash((3,4)) =", hash((3, 4)))
```

```bash
for seed in 0 1 2; do echo "PYTHONHASHSEED=$seed"; PYTHONHASHSEED=$seed python3 ex.py; done
```

- 세 줄 중 **판마다 갈리는 줄과 안 갈리는 줄**은 각각 어느 것인가?
- **안 갈리는 줄은 「보장된다」는 뜻인가**? 아니라면 그것을 어떻게 반증하는가?

### 2. 네 연산이 각각 무엇을 주나 (예측)

```python
a = {1, 2, 3, 4}
b = {3, 4, 5}
print("a & b :", sorted(a & b), "| a | b :", sorted(a | b))
print("a - b :", sorted(a - b), "| b - a :", sorted(b - a))
print("a ^ b :", sorted(a ^ b))
print("isdisjoint :", a.isdisjoint({9}), a.isdisjoint(b))
```

- 위 코드가 **출력을 전부 `sorted()` 로 감싼 이유**는 무엇인가?

### 3. 여섯 비교가 무엇을 돌려주나 (예측)

```python
x, y = {1, 2}, {1, 2, 3}
print("{1,2} <= {1,2,3} :", x <= y, "| < :", x < y, "| >= :", x >= y)
print("{1,2} <= {1,2}   :", x <= {1, 2}, "| < :", x < {1, 2})
p, q = {1, 2}, {3, 4}
print("  p < q :", p < q, "| p == q :", p == q, "| p > q :", p > q)
print("  p <= q:", p <= q, "| p >= q :", p >= q)
print("  len 은 같다 :", len(p) == len(q))
```

- `p` 와 `q` 에서 **`<`·`==`·`>` 가 셋 다 `False`** 인 것이 무엇을 뜻하고, 그 이름이 무엇인가?

### 4. 집합이 든 리스트를 정렬하면 (예측)

```python
data = [{3}, {1, 2}, {1}, {2}]
print("정렬 전 :", data)
print("sorted  :", sorted(data))
print("한 번 더 (입력 순서를 바꿔서) :", sorted([{1}, {2}, {1, 2}, {3}]))
print("{1} < {2} :", {1} < {2}, "| {2} < {1} :", {2} < {1})
```

- **예외가 나는가**? 안 난다면 **무엇이 보장되고 무엇이 안 되는지** 문서의 낱말로 말할 수 있는가?

### 5. 같은 값 셋을 한 집합에 (예측)

```python
print("{1, 1.0, True} ->", {1, 1.0, True}, [type(x).__name__ for x in {1, 1.0, True}])
print("{True, 1.0, 1} ->", {True, 1.0, 1}, [type(x).__name__ for x in {True, 1.0, 1}])
print("{1.0, 1, True} ->", {1.0, 1, True}, [type(x).__name__ for x in {1.0, 1, True}])
print("{0, False} :", {0, False}, "| {False, 0} :", {False, 0})
print("{1, 9} ->", list({1, 9}), "| {9, 1} ->", list({9, 1}), "| == :", {1, 9} == {9, 1})
```

- 마지막 줄에서 **`==` 가 `True` 인데 차례가 다른 이유**를 말할 수 있는가?

### 6. 연산자와 메서드가 다르게 받는다 (예측)

```python
try:
    set("abc") & "cbs"
except TypeError as e:
    print("set('abc') & 'cbs' ->", type(e).__name__, e)
print("set('abc').intersection('cbs') ->", sorted(set("abc").intersection("cbs")))
s = {1, 2}
try:
    s |= [4]
except TypeError as e:
    print("s |= [4] ->", type(e).__name__, e)
s.update([4])
print("s.update([4]) ->", sorted(s))
print("issubset 은 문자열도 :", set("ab").issubset("abc"))
```

- 이 비대칭이 **성능 때문인가 다른 이유인가**, 그리고 **dict 의 `|=` 와 무엇이 다른가**?

### 7. 왜 `set` 은 원소가 못 되나 (왜)

- `{{1, 2}}` 가 실패하고 `{frozenset({1, 2})}` 가 되는 이유를 **「불변이라서」가 아닌 말로** 설명하고,
  그런데도 `{1, 2} in {frozenset({1, 2})}` 가 되는 이유를 댈 수 있는가?

### 8. 섞어 쓰면 무엇이 나오나 (경계)

- `frozenset('ab') | set('bc')` 와 `set('ab') | frozenset('bc')` 의 **타입**을 말하고,
  `set('abc') == frozenset('abc')` 가 무엇인지 판정할 수 있는가?

### 9. 원소를 넣은 뒤 고치면 (경계)

- 해시가 바뀌도록 원소를 고친 뒤 같은 값을 하나 더 넣으면 **`len` 이 얼마**가 되는지 말하고,
  그것이 [12번](../12-dict-and-key-requirements/2-summary.md)의 사고와 **어떻게 같고 어떻게 다른지** 설명할 수 있는가?

### 10. 세 층 가르기 (경계)

- 이 주제에서 **언어 보장** · **CPython 구현 세부사항** · **이 판(3.12.3)·이 머신의 관찰**에 각각 해당하는 것을 나열할 수 있는가?

### 11. 조용한 실패를 막는 자리 (연결)

- 이 주제에서 **에러 없이 틀린 결과가 나오는 세 자리**를 대고, 각각을 무엇으로 막을지 판정할 수 있는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
