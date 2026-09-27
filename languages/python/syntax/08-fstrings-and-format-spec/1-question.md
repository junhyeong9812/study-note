# python/syntax/08-fstrings-and-format-spec — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
>
> 이 갈래는 **예측형**이다 — 「무엇을 아는가」가 아니라 「**이 코드의 출력을 예측할 수 있는가**」를 묻는다.
> 코드가 있는 문항은 **돌려 보기 전에** 종이에 출력을 적고 시작한다.
> ★ 이 주제에는 창이 하나 더 있다 — **`dis`**. 「소스에 뭐라 썼나」와 「무엇으로 컴파일됐나」가 다르다.
> ★ **「아무 출력이 없다」도 답이다**(8번).
> 실행 환경: `python3` 3.12.3.

## 질문

<!-- 형식: 질문 하나 = "?" 하나 = 한 줄.
     유형 태그: (왜) / (예측) / (경계) / (연결) -->

### 1. 만든 뒤에 값을 바꾸면 (예측)

```python
x = 1
s = f"x 는 {x}"
t = "x 는 {x}"
x = 2
print(s)
print(t.format(x=x))

def f(v=f"기본 {x}"):
    return v
x = 99
print(f())
```

### 2. `dis` 가 보여 주는 것 (예측)

```python
import dis
for src in ('r = f"{a}-{b}"', 'r = "%s-%s" % (a, b)', 'r = "{}-{}".format(a, b)'):
    ops = [i.opname for i in dis.get_instructions(compile(src, "<x>", "exec"))
           if i.opname in ("FORMAT_VALUE", "BINARY_OP", "BUILD_STRING", "CALL", "LOAD_ATTR")]
    print(f"{src:26} {ops}")
```

- 세 줄의 출력은 각각 무엇이고, 그중 **둘이 거의 같은 이유**는 무엇인가?

### 3. `{p}` 가 무엇을 부르나 (예측)

```python
class P:
    def __str__(self):  return "str 판"
    def __repr__(self): return "repr 판"
    def __format__(self, spec): return f"format 판(spec={spec!r})"

p = P()
print(f"{p}")
print(f"{p!s}")
print(f"{p!r}")
print(f"{p:>8}")
print(f"{p!r:>12}")
print("%s" % (p,))
```

- 여섯 줄의 출력은 각각 무엇이고, 마지막 줄이 첫 줄이 아니라 **어느 줄과 같은가**?

### 4. 포맷 스펙 조각들 (예측)

```python
print(repr(f"{-42:=10}"), repr(f"{-42:010}"))
print(repr(f"{1234567:,}"), repr(f"{-1234.5678:,.2f}"))
print(repr(f"{-1234.5678:.3}"), repr(f"{'abcdef':.3s}"))
print(repr(f"{255:#010x}"), repr(f"{44032:c}"))
print(repr(f"{42:10}"), repr(f"{'ab':10}"), repr(f"{True:10}"))
```

### 5. 스펙을 못 받는 타입 (예측)

```python
for v in (42, "ab", 3.5, None, [1]):
    try:
        print(f"{type(v).__name__:8} |{v:10}|")
    except TypeError as e:
        print(f"{type(v).__name__:8} TypeError: {e}")

class OnlyStr:
    def __str__(self): return "내 str"
o = OnlyStr()
print(f"{o}")
```

- 일곱 줄의 출력은 각각 무엇이고, 마지막 줄은 되는데 `f"{o:>10}"` 이 안 되는 이유는 무엇인가?

### 6. `=` 디버그 표기 (예측)

```python
x = 42
name = "값"
print(f"{x=}")
print(f"{x = }")
print(f"{x=:05d}")
print(f"{name=}")
print(f"{ x  +  1 = }")
```

### 7. 3.12 에서 새로 되는 것 (예측)

```python
d = {"key": "값"}
print(f"{d["key"]}")
print(f"{'a\nb'.split('\n')}")
print(f"{f"{f"{1+1}"}"}")
for src in ('f"{}"', 'f"{x!z}"'):
    try:
        compile(src, "<x>", "eval"); print(src, "-> 컴파일됨")
    except SyntaxError as e:
        print(src, "->", e.msg)
```

- 다섯 줄의 출력은 각각 무엇이고, 이 코드가 **3.11 에서는 어디서 멈추는가**?

### 8. `%` 포맷의 오른쪽 (왜)

- `"%s" % x` 에서 `x` 가 튜플일 때와 리스트일 때 동작이 갈리는 이유를 말하고, 그 함정을 없애는 한 가지 습관을 댈 수 있는가?

### 9. 로그에 f-string 을 쓰면 (경계)

- `log.debug(f"...")` 와 `log.debug("%s", obj)` 중 무엇이 무엇을 지연시키고 **무엇은 지연시키지 못하는지** 갈라 말할 수 있는가?

### 10. 사용자가 준 템플릿 (연결)

- `str.format` 은 할 수 있지만 f-string 은 원리적으로 못 하는 일이 무엇이고, 그 「못 함」이 어떤 공격을 막는가?

### 11. 세 층 가르기 (경계)

- 이 주제에서 **언어 보장** · **CPython 구현 세부사항** · **이 판(3.12.3)의 관찰**에 각각 해당하는 것을 나열할 수 있는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
