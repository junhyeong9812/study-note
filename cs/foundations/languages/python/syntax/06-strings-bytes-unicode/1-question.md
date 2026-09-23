# python/syntax/06-strings-bytes-unicode — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
>
> 이 갈래는 **예측형**이다 — 「무엇을 아는가」가 아니라 「**이 코드의 출력을 예측할 수 있는가**」를 묻는다.
> 코드가 있는 문항은 **돌려 보기 전에** 종이에 출력을 적고 시작한다.
> ★ 이 주제에서는 **「에러가 난다」도 답이다.** 어느 예외인지, 그리고 **어느 줄에서** 나는지까지 적는다.
> 실행 환경: `python3` 3.12.3.

## 질문

<!-- 형식: 질문 하나 = "?" 하나 = 한 줄.
     유형 태그: (왜) / (예측) / (경계) / (연결) -->

### 1. `len()` 이 세는 것 (예측)

```python
print(len("한글"), len("👍"), len("👨‍👩‍👧"), len("🇰🇷"))
print(len("한글".encode("utf-8")))
print("👨‍👩‍👧"[:3])
print([hex(ord(c)) for c in "👨‍👩‍👧"])
```

- 네 줄의 출력은 각각 무엇이고, 첫 줄의 네 값이 서로 다른 이유를 한 문장으로 말할 수 있는가?

### 2. 화면에 같은 두 문자열 (예측)

```python
import unicodedata
a = "\u00e9"
b = "e\u0301"
print(a, b, len(a), len(b))
print(a == b)
print({a: 1}.get(b, "못 찾음"), len({a, b}))
print(unicodedata.normalize("NFC", b) == a)
print(repr(unicodedata.normalize("NFKC", "Ⅳ")))
```

- 다섯 줄의 출력은 각각 무엇이고, 마지막 줄이 **앞의 정규화와 성격이 다른** 이유는 무엇인가?

### 3. `bytes` 에서 하나를 꺼내면 (예측)

```python
b = "가".encode("utf-8")
print(b, len(b))
print(b[0], type(b[0]).__name__)
print(b[0:1], type(b[0:1]).__name__)
print(list(b), list("가"))
print("가"[0], type("가"[0]).__name__)
```

- 다섯 줄의 출력은 각각 무엇이고, `str` 과 `bytes` 가 **어느 연산에서** 갈라지는가?

### 4. 섞으면 (예측)

```python
for code in ('b"a" + "a"', '"a" + b"a"', 'b"a" < "a"', '"abc" in b"abc"'):
    try:
        eval(code); print(code, "-> 통과")
    except TypeError as e:
        print(code, "->", type(e).__name__)
print(b"a" == "a", b"a" != "a")
print(bytearray(b"ab") == b"ab")
print(str(b"abc"))
```

- 일곱 줄의 출력은 각각 무엇이고, **에러가 나지 않는 줄들**이 왜 더 위험한가?

### 5. `'\ud800'` 을 만들면 (예측)

```python
s = "\ud800"
print(repr(s), len(s), hex(ord(s)))
try:
    print(s.encode("utf-8"))
except UnicodeEncodeError as e:
    print("encode:", type(e).__name__)
print(s.encode("utf-8", "surrogatepass"))
broken = "가".encode("utf-8")[:2]
print(repr(broken.decode("utf-8", "surrogateescape")))
print(broken.decode("utf-8", "surrogateescape").encode("utf-8", "surrogateescape") == broken)
```

- 다섯 줄의 출력은 각각 무엇이고, 이 값이 **어느 단계에서** 문제를 일으키는가?

### 6. 글자 수가 같은데 크기가 다르다 (예측)

```python
import sys
print(sys.getsizeof("a"*10), sys.getsizeof("한"*10), sys.getsizeof("👍"*10))
print(sys.getsizeof("a"*11), sys.getsizeof("한"*11), sys.getsizeof("👍"*11))
print(sys.getsizeof("a"*100), sys.getsizeof("a"*99 + "👍"))
print(sys.getsizeof("\u00e9"), sys.getsizeof("\u00e9"*2), sys.getsizeof("\u00e9"*3))
```

- 네 줄의 출력에서 **글자 하나를 늘릴 때 늘어나는 바이트**가 셋으로 갈리는 규칙은 무엇이고,
  마지막 줄이 그 규칙을 어기는 것처럼 보이는 이유는 무엇인가?

### 7. `latin-1` 은 왜 에러를 안 내나 (왜)

- utf-8 로 만든 한글 바이트를 `latin-1` 로 디코딩하면 예외가 안 나는데, 그 사실이 왜 「맞게 읽었다」의 근거가 될 수 없는가?

### 8. 어느 에러 핸들러를 고르나 (경계)

- `ignore`·`replace`·`backslashreplace`·`surrogateescape` 중 **되돌릴 수 있는 것**은 어느 것이고, 나머지를 쓸 때 무엇을 기록해 둬야 하는가?

### 9. `ord`/`chr` 의 경계 (경계)

- `chr` 이 받을 수 있는 정수의 범위와, `ord` 에 두 글자를 주거나 빈 문자열을 줬을 때 나는 예외의 **종류가 다른** 이유를 말할 수 있는가?

### 10. 세 층 가르기 (경계)

- 이 주제에서 **언어 보장** · **CPython 구현 세부사항** · **이 판(3.12.3)의 관찰**에 각각 해당하는 것을 나열할 수 있는가?

### 11. 「몇 글자인가」에 답이 넷이다 (연결)

- `"cafe\u0301"` 에 대해 코드 포인트 수 · 사람이 보는 글자 수 · 터미널이 먹는 칸 수 · utf-8 바이트 수를 각각 구하는 방법을 말하고, 어느 자리에 어느 답을 써야 하는지 판정할 수 있는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
