# python/syntax/05-truthiness-and-short-circuit — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
>
> 이 갈래는 **예측형**이다 — 「무엇을 아는가」가 아니라 「**이 코드의 출력을 예측할 수 있는가**」를 묻는다.
> 코드가 있는 문항은 **돌려 보기 전에** 종이에 출력을 적고 시작한다.
> ★ 이 주제에서는 **「아무것도 안 찍혔다」도 답이다.** 몇 줄이 나오는지까지 적는다.
> 실행 환경: `python3` 3.12.3.

## 질문

<!-- 형식: 질문 하나 = "?" 하나 = 한 줄.
     유형 태그: (왜) / (예측) / (경계) / (연결) -->

### 1. `__bool__` 과 `__len__` 중 누가 먼저인가 (예측)

```python
class Both:
    def __bool__(self):
        print("  __bool__ 불림"); return False
    def __len__(self):
        print("  __len__ 불림"); return 10

class Neither:
    pass

print("Both:", bool(Both()))
print("Neither:", bool(Neither()))
```

- 출력이 **몇 줄**이고 각각 무엇이며, 판정 순서를 세 단계로 말할 수 있는가?

### 2. 무엇이 거짓인가 (예측)

```python
print([bool(v) for v in (0, 0.0, "", [], (), {}, set(), range(0), None, False)])
print([bool(v) for v in ("0", "False", [0], (0,), {0: 0}, range(1))])
print(1 == True, [1] == True, bool([1]))
```

- 세 줄의 출력은 각각 무엇이고, 셋째 줄에서 `[1] == True` 와 `bool([1])` 이 갈리는 이유는 무엇인가?

### 3. `and`/`or` 가 돌려주는 것 (예측)

```python
print(1 and 2)
print(0 or 2)
print(repr('a' and 'b' and '' and 'd'))
print(repr(None or 0 or ''))
print(type(1 and 2).__name__, type(not 1).__name__)
```

- 다섯 줄의 출력은 각각 무엇이고, `and`/`or` 와 `not` 이 갈리는 지점은 무엇인가?

### 4. `x or 기본값` 은 언제 배신하나 (예측)

```python
def bad(x):  return x or "기본값"
def good(x): return x if x is not None else "기본값"

for v in (None, 0, "", [], "값", 5):
    print(repr(v), bad(v), repr(good(v)))
```

- 여섯 줄 중 **두 판의 답이 갈리는 줄**은 어느 것이고, 그 관용구를 고치려면 질문을 어떻게 바꿔야 하는가?

### 5. 단축 평가가 건너뛰는 것 (예측)

```python
def loud(name, ret):
    print(f"  {name} 평가됨")
    return ret

print("A:", False and loud("A", True))
print("B:", True or loud("B", True))
print("C:", True and loud("C", "C결과"))

a = None
print("D:", a is not None and len(a))
```

- 출력이 **몇 줄**이고 각각 무엇이며, `len(None)` 이 `TypeError` 인데 D 줄이 안 터지는 이유는 무엇인가?

### 6. 비교 체이닝 (예측)

```python
def loud(v):
    print("  b 평가됨")
    return v

print(" 결과:", 3 < loud(5) < 100)
print(" 결과:", 3 < loud(5) and loud(5) < 100)
print(False == False in [False])
print((False == False) in [False], False == (False in [False]))
```

- 출력이 **몇 줄**이고 각각 무엇이며, 셋째 줄이 넷째 줄의 어느 괄호와도 같지 않은 이유는 무엇인가?

### 7. `dis` 가 보여 주는 것 (왜)

- `a and b` 를 `dis` 로 풀었을 때 **어떤 명령이 없다는 사실**이 「`and` 는 불린을 안 돌려준다」의 증거가 되는가?

### 8. `in` 은 무엇을 먼저 보나 (경계)

- `x in [a, b, c]` 가 비교를 **언제 멈추고**, `__eq__` 가 **어느 쪽 객체**의 것이 불리는가 — 그리고 그 호출 순서는 언어 보장인가 구현 관찰인가?

### 9. `all([])` 이 `True` 인 것 (경계)

- `all([])` 이 `True` 이고 `any([])` 가 `False` 인 이유를 정의에서 유도하고, 그 성질이 검증 코드에서 무엇을 위험하게 만드는지 말할 수 있는가?

### 10. 세 층 가르기 (경계)

- 이 주제에서 **언어 보장** · **CPython 구현 세부사항** · **이 판(3.12.3)의 관찰**에 각각 해당하는 것을 나열할 수 있는가?

### 11. 「참인가」와 「있는가」 (연결)

- `if x:` · `if x is not None:` · `if x == True:` 세 검사가 각각 무엇을 묻는지 갈라 말하고, 어느 자리에 무엇을 쓸지 판정할 수 있는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
