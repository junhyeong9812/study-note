# python/syntax/18-loop-control-and-else — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
>
> 이 갈래는 **예측형**이다 — 「무엇을 아는가」가 아니라 「**이 코드의 출력을 예측할 수 있는가**」를 묻는다.
> 코드가 있는 문항은 **돌려 보기 전에** 종이에 출력을 적고 시작한다.
> ★ 이 주제에서는 **「에러가 나나 안 나나」가 답인 자리가 많다.** 자료형이 바뀌면 답도 바뀐다 —
> **리스트에서 확인하고 dict 로 옮겨 적으면 틀린다.**
> 실행 환경: `python3` 3.12.3(`zip strict` 문구는 3.11.15 로 대조). 던지는 형태는 `python3 - <파일` 로 고정했다.

## 질문

<!-- 형식: 질문 하나 = "?" 하나 = 한 줄.
     유형 태그: (왜) / (예측) / (경계) / (연결) -->

### 1. 세 번 부르면 무엇이 찍히나 (예측)

```text
===== 소스: ex.py =====
import sys
print("python", ".".join(map(str, sys.version_info[:3])))

def find(xs, target):
    for x in xs:
        if x == target:
            print("  찾음:", x)
            break
    else:
        print("  else 가 돌았다 — 끝까지 못 찾음")

print("[1,2,3] 에서 2 :"); find([1, 2, 3], 2)
print("[1,2,3] 에서 9 :"); find([1, 2, 3], 9)
print("빈 리스트에서 9 :"); find([], 9)
```

- 세 번째 호출의 답을 **「한 번도 안 돌았으니까」로 설명하면 왜 틀리는가**?

### 2. 바이트코드에서 그 절은 어디에 놓이나 (예측)

```text
===== 소스: ex.py =====
import dis
src = """
for x in xs:
    if x:
        break
else:
    found = 0
after = 1
"""
print("===== 소스: 위 for ... else =====")
dis.dis(compile(src, "<forelse>", "exec"))
```

- 출력에서 **`after = 1` 이 몇 번 나오는지** 세고, 그 개수가 무엇을 뜻하는지 말할 수 있는가?
- `break` 는 `else` 를 **「건너뛰는」 것인가 「안 보는」 것인가**?
- ★ 이 관찰 중 **언어 보장인 것과 CPython 구현인 것**을 가를 수 있는가?

### 3. 세 덩어리가 각각 무엇을 찍나 (예측)

```text
===== 소스: ex.py =====
n = 0
while n < 3:
    n += 1
else:
    print("while ... else  : 조건이 거짓이 되어 끝 -> else 돈다, n =", n)

n = 0
while n < 3:
    n += 1
    if n == 2:
        break
else:
    print("이 줄은 안 찍힌다")
print("break 로 끝난 while : else 는 안 돌았다, n =", n)

for i in range(3):
    if i == 1:
        continue
    print("  continue 는 else 를 건드리지 않는다 :", i)
else:
    print("  -> else 돌았다")
```

- 「`break` 없는 `while ... else`」가 **왜 냄새인가**?

### 4. 돌면서 지우면 (예측)

```text
===== 소스: ex.py =====
print("--- 순회 중 remove — 예외가 없다 ---")
xs = ["a", "b", "c", "d", "e"]
seen = []
for x in xs:
    seen.append(x)
    if x in ("b", "c"):
        xs.remove(x)
print("  본 것   :", seen)
print("  남은 것 :", xs, " <- c 를 못 지웠다")

print()
print("--- 왜 그런가: 리스트 이터레이터는 정수 커서다 ---")
ys = ["a", "b", "c", "d", "e"]
it = iter(ys)
print("  next ->", next(it), "| 남은 개수 힌트 :", it.__length_hint__())
print("  next ->", next(it), "| 남은 개수 힌트 :", it.__length_hint__())
ys.remove("b")
print("  'b' 를 지웠다 -> ys =", ys, "| 남은 개수 힌트 :", it.__length_hint__())
print("  next ->", next(it), " <- 'c' 가 아니라")

print()
print("--- 순회 중 append 는 안 끝난다 (3개만 보고 끊는다) ---")
zs = [1]
out = []
for v in zs:
    out.append(v)
    zs.append(v + 1)
    if len(out) == 5:
        break
print("  본 것 :", out, "| 리스트 길이 :", len(zs))

print()
print("--- dict/set 은 터진다 ---")
d = {"a": 1, "b": 2}
try:
    for k in d:
        d[k + "!"] = 0
except RuntimeError as e:
    print("  dict :", type(e).__name__ + ":", e)
s = {"a", "b"}
try:
    for v in s:
        s.add(v + "!")
except RuntimeError as e:
    print("  set  :", type(e).__name__ + ":", e)
d2 = {"a": 1, "b": 2}
d2["a"] = 99
print("  값만 바꾸는 것은 된다 :", d2)
```

- 첫 덩어리에서 **`본 것` 에 무엇이 빠졌는지**, 그리고 그 빠짐이 왜 예외가 아닌지 말할 수 있는가?
- **`dict` 의 값만 바꾸는 것은 왜 통과하는가**?

### 5. 왼쪽 이터레이터에 남는 것 (예측)

```text
===== 소스: ex.py =====
print("--- zip 이 삼킨 원소 ---")
left = iter([1, 2, 3, 4])
print("  zip 결과      :", list(zip(left, "ab")))
print("  왼쪽에 남은 것 :", list(left), " <- 3 이 사라졌다")
```

- 문서의 낱말 「**ignore**」와 실제로 일어난 일이 **어떻게 어긋나는가**?

### 6. 세 도구의 성질을 가르면 (예측)

```text
===== 소스: ex.py =====
import sys, itertools
print("python", ".".join(map(str, sys.version_info[:3])))

print("--- enumerate ---")
print("  기본      :", list(enumerate("abc")))
print("  start=1   :", list(enumerate("abc", start=1)))
print("  세는 수만 바뀐다 :", list(enumerate(["x", "y"], 1)))
e = enumerate("ab")
print("  iter(e) is e :", iter(e) is e, " <- 이터레이터다")

print()
print("--- zip 은 짧은 쪽에서 끊는다 ---")
print("  zip        :", list(zip([1, 2, 3], "ab")))
print("  zip_longest:", list(itertools.zip_longest([1, 2, 3], "ab", fillvalue="-")))

print()
print("--- range 는 이터레이터가 아니라 시퀀스다 ---")
r = range(5)
print("  iter(r) is r :", iter(r) is r)
print("  두 번 돌아도 :", list(r), list(r))
print("  len          :", len(r), "| r[2] :", r[2], "| r[-1] :", r[-1], "| r[1:3] :", r[1:3])
print("  4999999 in range(10_000_000) :", 4_999_999 in range(10_000_000))
print("  getsizeof(range(10_000_000)) :", sys.getsizeof(range(10_000_000)))
print("  == 는 값 비교 :", range(0, 5) == range(0, 5, 1), "|", range(0) == range(5, 0))
print("  타입들       :", type(r).__name__, "/", type(iter(r)).__name__)
```

- `enumerate(xs, 1)` 로 얻은 수를 **`xs[i]` 에 그대로 넣으면** 무엇이 일어나는가?
- 마지막에서 두 번째 줄의 `True` 두 개는 **각각 무엇을 말하는가**?

### 7. 이름이 왜 오독을 부르나 (왜)

- `else` 라는 낱말이 **무엇을 암시해서** 틀리게 읽히는지, 그리고 **무엇으로 바꿔 읽으면** 안 틀리는지 말할 수 있는가?

### 8. 터지는 것과 조용한 것 (경계)

- 순회 중 변경에서 **`RuntimeError` 가 나는 경우와 안 나는 경우**를 자료형·연산으로 갈라 말하고, 왜 그렇게 갈리는지 댈 수 있는가?

### 9. 세 갈래를 고르는 기준 (경계)

- 길이가 다를 수 있는 두 목록을 묶을 때 **기본 `zip`·`strict=True`·`zip_longest`** 중 무엇을 언제 쓰는지, 그리고 `strict` 가 **언제부터**인지 말할 수 있는가?

### 10. 한 묶음으로 외우면 틀리는 자리 (연결)

- `range`·`enumerate`·`zip`·제너레이터 표현식을 「지연되는 것들」로 묶어 외우면 **어디서 틀리는지** 실행 가능한 한 줄로 반증할 수 있는가?

### 11. 세 층 가르기 (경계)

- 이 주제에서 **언어 보장** · **CPython 구현 세부사항** · **이 판(3.12.3)·이 머신의 관찰**에 해당하는 것을 각각 나열할 수 있는가?

### 12. 언제 터지나 — 시작 전인가 도는 중인가 (연결)

- 이 주제에서 **프로그램이 시작조차 못 하는 오류**는 무엇이고, 그것이 [19번](../19-function-argument-rules/2-summary.md)의 층 구분과 어떻게 이어지는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
