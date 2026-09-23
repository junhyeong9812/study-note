# python/syntax/07-string-methods — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
>
> 이 갈래는 **예측형**이다 — 「무엇을 아는가」가 아니라 「**이 코드의 출력을 예측할 수 있는가**」를 묻는다.
> 코드가 있는 문항은 **돌려 보기 전에** 종이에 출력을 적고 시작한다.
> ★ 이 주제에서는 **「맞은 것처럼 보이는 답」이 함정**이다. 한 줄이 맞으면 그 옆줄을 의심한다.
> 실행 환경: `python3` 3.12.3.

## 질문

<!-- 형식: 질문 하나 = "?" 하나 = 한 줄.
     유형 태그: (왜) / (예측) / (경계) / (연결) -->

### 1. 인자로 준 문자열을 무엇으로 읽나 (예측)

```python
print(repr("example.com".strip(".com")))
print(repr("hello.com".rstrip(".com")))
print(repr("mississippi".strip("mip")))
print(repr("abcba".strip("ab")), repr("abcba".strip("ba")))
print(repr("aaa".removeprefix("a")), repr("aaa".lstrip("a")))
print(repr("example.com".removesuffix(".org")))
```

- 여섯 줄의 출력은 각각 무엇이고, **첫 줄이 「맞은 것처럼」 보이는 이유**는 무엇인가?

### 2. 공백으로 나누는 두 방법 (예측)

```python
line = "  a  b  "
print(line.split(), line.split(" "))
print("".split(), "".split(" "))
print("a,,b".split(","))
print("a\nb\n".split("\n"), "a\nb\n".splitlines())
print("kv".partition("="), "a=b=c".partition("="))
```

- 다섯 줄의 출력은 각각 무엇이고, 「공백으로 나눈다」가 **두 가지 뜻**인 이유는 무엇인가?

### 3. 찾았나 못 찾았나를 `if` 로 물으면 (예측)

```python
s = "hello world"
for needle in ("hello", "world", "zz", ""):
    print(repr(needle), s.find(needle), bool(s.find(needle)), needle in s)
try:
    s.index("zz")
except ValueError as e:
    print("index:", type(e).__name__, e)
print("aaaa".count("aa"), "aaaa".count(""))
```

- 여섯 줄의 출력은 각각 무엇이고, 어느 두 줄이 **서로 반대 답**을 내는가?

### 4. 「숫자인가」를 묻는 세 메서드 (예측)

```python
for c in ("7", "\u0667", "\u00b2", "\u00bd", "\u2163", "-7", "7.5"):
    try:
        iv = repr(int(c))
    except ValueError:
        iv = "ValueError"
    print(repr(c), c.isdecimal(), c.isdigit(), c.isnumeric(), c.isascii(), iv)
```

- 일곱 줄의 출력은 각각 무엇이고, **입력 검증에 이 셋 중 무엇을 써야 하는가**?

### 5. 대소문자를 바꾸면 길이가 바뀐다 (예측)

```python
print("straße".lower() == "STRASSE".lower())
print("straße".casefold() == "STRASSE".casefold())
print(len("ß"), len("ß".upper()), repr("ß".upper().lower()))
print(len("İ"), len("İ".lower()))
print(repr("ΟΔΟΣ".lower()), repr("ΟΔΟΣ".casefold()))
print(repr("o'neill".title()))
```

- 여섯 줄의 출력은 각각 무엇이고, `casefold` 가 `lower` 의 **강화판이 아닌** 이유는 무엇인가?

### 6. 메서드가 돌려준 것이 같은 객체인가 (예측)

```python
s = "hello"
print(s.replace("l", "L") is s)
print(s.replace("z", "Z") is s)
print(s.upper().lower() is s)
print(s[:] is s)
print("abab".replace("a", "b").replace("b", "a"))
print("abab".translate(str.maketrans("ab", "ba")))
```

- 여섯 줄의 출력은 각각 무엇이고, 그중 어느 줄이 **언어 보장이 아니라 구현 세부사항**인가?

### 7. `join` 이 왜 문자열의 메서드인가 (왜)

- `["a","b"].join(",")` 이 아니라 `",".join(["a","b"])` 인 설계가 무엇을 가능하게 하고, 어떤 인자를 거부하는가?

### 8. `splitlines` 가 줄로 보는 것 (경계)

- `str.splitlines` 와 `bytes.splitlines` 가 줄바꿈으로 보는 글자 목록이 어떻게 다르고, 그 차이가 **어떤 코드에서** 드러나는가?

### 9. `translate` 가 `replace` 두 번과 다른 자리 (왜)

- `"abab"` 에서 `a` 와 `b` 를 맞바꾸려 할 때 `replace` 를 두 번 부르면 왜 안 되고, `str.maketrans` 가 만드는 표의 **키가 무엇**인가?

### 10. 세 층 가르기 (경계)

- 이 주제에서 **언어 보장** · **CPython 구현 세부사항** · **이 판(3.12.3)의 관찰**에 각각 해당하는 것을 나열할 수 있는가?

### 11. 정규식을 꺼내는 선 (연결)

- 문자열 메서드로 되는 일과 `re` 를 꺼내야 하는 일을 갈라 말하고, `strip`·`split`·`replace` 각각이 정규식으로 넘어가는 **구체적 조건**을 댈 수 있는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
