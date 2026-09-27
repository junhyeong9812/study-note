# python/syntax/12-dict-and-key-requirements — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
>
> 이 갈래는 **예측형**이다 — 「무엇을 아는가」가 아니라 「**이 코드의 출력을 예측할 수 있는가**」를 묻는다.
> 코드가 있는 문항은 **돌려 보기 전에** 종이에 출력을 적고 시작한다.
> ★ 이 주제에서는 **「몇 개가 남나」와 「어느 쪽이 남나」가 답인 자리가 많다.** 키인지 값인지까지 적는다.
> 실행 환경: `python3` 3.12.3(일부 문항은 3.11.15 로 대조).

## 질문

<!-- 형식: 질문 하나 = "?" 하나 = 한 줄.
     유형 태그: (왜) / (예측) / (경계) / (연결) -->

### 1. 세 번 넣고 출력하면 (예측)

```python
d = {}
d["c"] = 1; d["a"] = 2; d["b"] = 3
print("세 번 넣고 출력     :", d, "|", list(d))
d["c"] = 99
print("있는 키에 다시 대입 :", list(d))
del d["c"]; d["c"] = 1
print("지우고 다시 넣으면  :", list(d))
print("== 는 순서를 안 본다:", {"a":1,"b":2} == {"b":2,"a":1})
print("list()는 순서를 본다:", list({"a":1,"b":2}) == list({"b":2,"a":1}))
print("reversed(d)         :", list(reversed(d)))
print("popitem()           :", dict(x=1,y=2,z=3).popitem())
```

- 위 결과 중 **언어가 약속한 것은 어디까지**이고, 그 약속은 **어느 판부터** 있었는가?

### 2. 네 가지 수를 키로 쓰면 (예측)

```python
print("hash :", hash(1), hash(1.0), hash(True), hash(1+0j))
d = {1: "정수", 1.0: "실수", True: "불리언"}
print("d =", d, "| len =", len(d), "| 키의 타입 =", [type(k).__name__ for k in d])
d2 = {True: "먼저 불리언", 1: "나중 정수"}
print("d2 =", d2, "| 키 타입:", [type(k).__name__ for k in d2], "| d2[1.0] =", d2[1.0])
print("0 과 False :", {0: "영", False: "거짓"})
print("'1' 은     :", {1: "정수", "1": "문자열"})
from decimal import Decimal
print("Decimal    :", {1: "a", Decimal("1"): "c"})
```

- **남는 키**와 **남는 값**이 각각 어느 쪽에서 오는지 한 문장으로 말할 수 있는가?

### 3. 뷰를 먼저 받아 두면 (예측)

```python
d = {"a": 1, "b": 2}
ks, vs, its = d.keys(), d.values(), d.items()
print("받아 둔 직후 :", ks, vs, its)
d["c"] = 3
del d["a"]
print("원본을 바꾼 뒤:", ks, vs, its, "| len(ks) =", len(ks))
try:
    ks[0]
except TypeError as e:
    print("ks[0] ->", type(e).__name__, e)
print("집합 연산 :", sorted(d.keys() & {"b", "z"}), d.items() & {("b", 2)})
try:
    d.values() & {1}
except TypeError as e:
    print("values() & {1} ->", type(e).__name__, e)
print("values 끼리 == :", {"a": 1}.values() == {"a": 1}.values())
```

- **`keys()` 는 되는데 `values()` 는 안 되는 연산**이 있는 이유는 무엇인가?

### 4. 도는 중에 건드리면 (예측)

```python
# (가)
d = {"a": 1, "b": 2, "c": 3}
for k in d:
    if k == "a":
        d["d"] = 4

# (나)
d = {"a": 1, "b": 2, "c": 3}
for k in d:
    if k == "a":
        del d["c"]
        d["z"] = 9
    print("돌았다:", k)
print("끝:", d)
```

- 두 조각 중 **터지는 쪽은 어디**이고, **안 터지는 쪽은 무엇을 돌았는가**?
- 예외가 난다면 **어느 줄**에서 나고 **전문**이 어떻게 생겼는가?

### 5. 세 가지 병합의 결과 (예측)

```python
a = {"x": 1, "y": 2}
b = {"y": 20, "z": 30}
print("a | b :", a | b)
print("b | a :", b | a)
print("{**a,**b} :", {**a, **b})
c = dict(a); c |= [("k", 9), ("y", 0)]
print("c |= [(k,9),(y,0)] :", c)
try:
    a | [("k", 9)]
except TypeError as e:
    print("a | [...] ->", type(e).__name__, e)
```

- `b | a` 에서 `y` 의 **자리와 값이 각각 어디서 오는지** 말할 수 있는가?

### 6. 네 클래스 중 무엇이 키가 되나 (예측)

```python
class Plain:
    def __init__(self, v): self.v = v
class OnlyEq:
    def __init__(self, v): self.v = v
    def __eq__(self, o): return isinstance(o, OnlyEq) and self.v == o.v
class Both:
    def __init__(self, v): self.v = v
    def __eq__(self, o): return isinstance(o, Both) and self.v == o.v
    def __hash__(self): return hash(self.v)
    def __repr__(self): return f"Both({self.v})"
class Liar:
    def __init__(self, v): self.v = v
    def __eq__(self, o): return isinstance(o, Liar) and self.v == o.v
    def __hash__(self): return 0
    def __repr__(self): return f"Liar({self.v})"

print("Plain  :", len({Plain(1): 0, Plain(1): 0}))
print("OnlyEq : __hash__ =", OnlyEq.__hash__)
print("Both   :", {Both(1): "첫째", Both(1): "둘째"})
print("Liar   :", len({Liar(1): 0, Liar(2): 0}))
```

- **`Liar` 가 합법인 이유**를 계약 한 문장으로 말할 수 있는가?

### 7. 이 순서를 누가 약속하나 (왜)

- 「dict 는 삽입 순서를 유지한다」가 **언제 CPython 구현 세부였고 언제 언어 보장이 되었는지** 말하고,
  그 근거 문장이 **어느 문서의 어디**에 있는지 댈 수 있는가?

### 8. 키를 만드는 것과 안 만드는 것 (경계)

- `d.get(k)` · `d.setdefault(k, [])` · `defaultdict(list)[k]` · `defaultdict(list).get(k)` 중
  **키를 만드는 것은 어느 것**이고, 그 차이가 어떤 사고를 내는가?

### 9. 키로 쓴 객체를 나중에 고치면 (경계)

- `__hash__` 가 바뀌도록 키를 고친 뒤 `len(d)` · `list(d)` · `d[k]` 가 각각 무엇을 돌려주는지 말하고,
  **그것이 왜 예외가 아닌지** 설명할 수 있는가?

### 10. 세 층 가르기 (경계)

- 이 주제에서 **언어 보장** · **CPython 구현 세부사항** · **이 판(3.12.3)·이 머신의 관찰**에 각각 해당하는 것을 나열할 수 있는가?

### 11. 조용한 실패를 막는 자리 (연결)

- 이 주제에서 **에러 없이 틀린 결과가 나오는 세 자리**를 대고, 각각을 무엇으로 막을지 판정할 수 있는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
