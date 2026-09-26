# python/syntax/46-re — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
>
> 이 갈래는 **예측형**이다 — 「무엇을 아는가」가 아니라 「**이 코드의 출력을 예측할 수 있는가**」를 묻는다.
> 코드가 있는 문항은 **돌려 보기 전에** 종이에 출력을 적고 시작한다.
> ★★★ 1번은 **칸마다 `span` 까지**, 4번은 **에러 칸의 예외 종류까지** 적어야 맞은 것이다.
> ★★ 이 주제는 **속도를 묻지 않는다** — 한 번도 재지 않았다. 7번도 「끝나나」만 묻는다.
>
> 실행 환경: `python3` **3.12.3** · Linux(5번은 `python3.11` 3.11.15 도 함께). 던지는 형태는 `python3 - <파일` 로 고정했다.
> ★ 선행 — [06](../06-strings-bytes-unicode/1-question.md)(`str`·`bytes`) · [07](../07-string-methods/1-question.md)(정규식을 꺼내는 선).

## 질문

<!-- 형식: 질문 하나 = "?" 하나 = 한 줄.
     유형 태그: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★★ 세 입력에 건 「끝」의 여러 조합 (예측)

```python
# e46_anchor.py
import re

texts = ["123", "123\n", "12\n34"]
calls = [
    ("match     \\d+", lambda s: re.match(r"\d+", s)),
    ("match     \\d+$", lambda s: re.match(r"\d+$", s)),
    ("match     \\d+\\Z", lambda s: re.match(r"\d+\Z", s)),
    ("fullmatch \\d+", lambda s: re.fullmatch(r"\d+", s)),
    ("search    \\d+$", lambda s: re.search(r"\d+$", s)),
    ("search    \\d+$ M", lambda s: re.search(r"\d+$", s, re.M)),
    ("findall   ^\\d+ M", lambda s: re.findall(r"^\d+", s, re.M)),
    ("match     ^34 M", lambda s: re.match(r"^34", s, re.M)),
]


def cell(r):
    if r is None:
        return "None"
    if isinstance(r, list):
        return repr(r)
    return "%r@%d-%d" % (r.group(), r.start(), r.end())


print(("call".ljust(18) + "".join(repr(t).ljust(18) for t in texts)).rstrip())
for label, f in calls:
    print((label.ljust(18) + "".join(cell(f(t)).ljust(18) for t in texts)).rstrip())

rows = [(t, bool(re.match(r"\d+$", t)), bool(re.fullmatch(r"\d+", t))) for t in texts]
print("match(\\d+$) vs fullmatch(\\d+), differing inputs: %d / %d"
      % (sum(a != b for _, a, b in rows), len(rows)))
```

### 2. ★★ 같은 입력, 다른 수량자 (예측)

```python
# e46_greedy.py
import re

html = "<a><b></b></a>"
text = 'k="x" v="y"'
print("[1]", re.findall(r"<.*>", html))
print("[2]", re.findall(r"<.*?>", html))
print("[3]", re.findall(r"<[^>]*>", html))
print("[4]", re.findall(r'"(.*)"', text))
print("[5]", re.findall(r'"(.*?)"', text))
print("[6]", re.match(r"a*a", "aaaa"))
print("[7]", re.match(r"a*+a", "aaaa"))
print("[8]", re.match(r"a{3,5}aa", "aaaaaa"), re.match(r"a{3,5}+aa", "aaaaaa"))
print("[9]", re.findall(r"a.c", "a\nc abc"), re.findall(r"a.c", "a\nc abc", re.S))
```

### 3. ★★ 선택 그룹이 빠진 매치와 `split` (예측)

```python
# e46_groups.py
import re

m = re.search(r"(?P<y>\d{4})-(?P<m>\d\d)(-(?P<d>\d\d))?", "on 2026-09 ok")
print("[1] group()      :", repr(m.group()))
print("[2] groups()     :", m.groups())
print("[3] groups('')   :", m.groups(""))
print("[4] groupdict()  :", m.groupdict())
print("[5] span('m')    :", m.span("m"), " span('d'):", m.span("d"))
r = re.match(r"(\w)+", "abc")
print("[6] (\\w)+ on abc :", r.group(0), r.group(1))
print("[7] findall      :", re.findall(r"(\d)(x)?", "1x2"))
print("[8] sub unmatched:", repr(re.sub(r"(x)?b", r"[\1]", "abc")))
print("[9] split        :", re.split(r"(-)", "a-b"), re.split(r"-", "a-b"))
print("[10] split empty :", re.split(r"\b", "hi yo"))
print("[11] sub x*      :", repr(re.sub("x*", "-", "abxd")))
```

### 4. ★★★ 치환 템플릿 격자 (예측)

```python
# e46_sub.py
import re
import sys
import warnings

templates = [r"[$&]", r"[\g<0>]", r"[\1]", r"[\g<1>0]", r"[\10]", r"[\9]",
             r"[\g<g>]", r"[\g<x>]", r"[\n]", r"[\q]", r"[\\]", r"[\0]", "[\\g<١>]"]
settings = [
    ("escape('b')", re.escape("b"), False),
    ("(b)", r"(b)", False),
    ("(?P<g>b)", r"(?P<g>b)", False),
    ("(?P<g>b) + fn", r"(?P<g>b)", True),
]
errors = []
warned = []
changed = raised = total = 0


def run(pattern, tpl, as_fn):
    if as_fn:
        return re.sub(pattern, lambda m: tpl, "abc")
    return re.sub(pattern, tpl, "abc")


print("python %d.%d" % sys.version_info[:2])
print("template".ljust(17) + "".join(name.ljust(16) for name, _, _ in settings).rstrip())
for tpl in templates:
    cells = []
    for name, pattern, as_fn in settings:
        total += 1
        try:
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                out = run(pattern, tpl, as_fn)
            if out != "a" + tpl + "c":
                changed += 1
            mark = ""
            for w in caught:
                warned.append("%s | %s | %s: %s" % (ascii(tpl), name, w.category.__name__, w.message))
                mark = " W%d" % len(warned)
            cells.append(repr(out) + mark)
        except Exception as e:
            raised += 1
            errors.append("%s | %s | %s: %s" % (ascii(tpl), name, type(e).__name__, e))
            cells.append("error#%d" % len(errors))
    print(ascii(tpl).ljust(17) + "".join(c.ljust(16) for c in cells).rstrip())
print("")
for i, line in enumerate(errors, 1):
    print("  #%d %s" % (i, line))
for i, line in enumerate(warned, 1):
    print("  W%d %s" % (i, line))
print("")
print("cells that differ from the template text: %d / %d  (raised: %d · warned: %d)"
      % (changed + raised, total, raised, len(warned)))
```

### 5. ★★★ 한 탐침을 두 판에 (예측)

```text
e46_vgrid.sh 를 돌린다 — 탐침을 python3.11 과 python3 에 각각 먹이고 나란히 놓는다. 표 전체와 마지막 줄을 적는다.
```

```python
# e46_vprobe.py
# One line per probe: label;value. e46_vgrid.sh runs this under two interpreters.
import re
import warnings


def value(f):
    try:
        return repr(f())
    except Exception as e:
        return "%s(%s)" % (type(e).__name__, e)


def literal(src):
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        compile(src, "<probe>", "eval")
    return ",".join(w.category.__name__ for w in caught) or "(none)"


def cache_after_touch():
    re.purge()
    first = re.compile("p0")
    for i in range(1, re._MAXCACHE):
        re.compile("p%d" % i)
    re.compile("p0")
    re.compile("p-extra")
    return re.compile("p0") is first


rows = [
    ("compile a++", lambda: value(lambda: re.compile(r"a++").pattern)),
    ("compile (?>a+)", lambda: value(lambda: re.compile(r"(?>a+)").pattern)),
    ("match a*a on aaaa", lambda: value(lambda: re.match(r"a*a", "aaaa").group())),
    ("match a*+a on aaaa", lambda: value(lambda: re.match(r"a*+a", "aaaa"))),
    ('literal "\\d+"', lambda: literal(r'"\d+"')),
    ('literal "\\."', lambda: literal(r'"\."')),
    ('literal b"\\d"', lambda: literal(r'b"\d"')),
    ('literal "\\477"', lambda: literal(r'"\477"')),
    ('literal r"\\d+"', lambda: literal(r'r"\d+"')),
    ('literal "\\\\d+"', lambda: literal(r'"\\d+"')),
    ('literal "\\n"', lambda: literal(r'"\n"')),
    ("sub (b) -> [\\g<U+0661>]", lambda: value(lambda: re.sub(r"(b)", "[\\g<\u0661>]", "abc"))),
    ("re.error.__name__", lambda: repr(re.error.__name__)),
    ("p0 same object after touch + 1 new", lambda: repr(cache_after_touch())),
]
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    for label, f in rows:
        print("%s;%s" % (label, f()))
```

```sh
# e46_vgrid.sh
#!/usr/bin/env bash
# Run e46_vprobe.py under python3.11 and python3, put the two answers side by side,
# and add one row that only the default warning filter can answer (stderr kept, stdout dropped).
set -u -o pipefail
declare -A a b
order=()
while IFS=';' read -r k v; do
  [ -n "$k" ] && [ -n "$v" ] || { echo "bad row: $k"; exit 1; }
  order+=("$k"); a[$k]=$v
done < <(python3.11 e46_vprobe.py)
while IFS=';' read -r k v; do
  [ -n "${a[$k]+set}" ] || { echo "row only in 3.12: $k"; exit 1; }
  b[$k]=$v
done < <(python3 e46_vprobe.py)
k='default filter prints the "\d+" warning'
order+=("$k")
for py in python3.11 python3; do
  err=$(printf 'import re\nre.compile("\\d+")\n' | "$py" - 2>&1 >/dev/null)
  if [ -n "$err" ]; then v="yes: $err"; else v="no (stderr empty)"; fi
  if [ "$py" = python3.11 ]; then a[$k]=$v; else b[$k]=$v; fi
done
printf '%-45s%-22s%s\n' "probe" "python3.11" "python3 (3.12)"
split=0
for k in "${order[@]}"; do
  mark=" "
  [ "${a[$k]}" != "${b[$k]}" ] && { mark="*"; split=$((split + 1)); }
  printf '%s %-43s%-22s%s\n' "$mark" "$k" "${a[$k]}" "${b[$k]}"
done
echo ""
echo "rows where the two versions differ: $split / ${#order[@]}"
```

### 6. ★★ `str` 과 `bytes` · 숫자 · 이스케이프 (예측)

```python
# e46_types.py
import re


def show(label, f):
    try:
        print(label.ljust(44), repr(f()))
    except Exception as e:
        print(label.ljust(44), "%s: %s" % (type(e).__name__, e))


print("[1] str and bytes")
show("re.search(r'\\d', b'a1')", lambda: re.search(r"\d", b"a1"))
show("re.search(rb'\\d', 'a1')", lambda: re.search(rb"\d", "a1"))
show("re.sub(rb'1', '2', b'a1')", lambda: re.sub(rb"1", "2", b"a1"))
show("re.search(rb'\\d', b'a1').group()", lambda: re.search(rb"\d", b"a1").group())

print("[2] what \\d and \\w mean")
digits = "١٢٣"
show("fullmatch(r'\\d+', U+0661 U+0662 U+0663)", lambda: bool(re.fullmatch(r"\d+", digits)))
show("  same with re.ASCII", lambda: bool(re.fullmatch(r"\d+", digits, re.ASCII)))
show("  int() of that text", lambda: int(digits))
show("fullmatch(r'\\w+', '한글')", lambda: bool(re.fullmatch(r"\w+", "한글")))
show("fullmatch(rb'\\w+', '한글'.encode())", lambda: bool(re.fullmatch(rb"\w+", "한글".encode())))

print("[3] re.escape")
samples = ["a.b", "1+1=2", "[x]", "$5", "a b", "_-~", "한글"]
ok = 0
for s in samples:
    esc = re.escape(s)
    back = re.fullmatch(esc, s) is not None
    ok += back
    print("   %-8s -> %-14s fullmatch itself: %s" % (repr(s), repr(esc), back))
print("   escaped patterns that match their own text: %d / %d" % (ok, len(samples)))
show("re.search('(', 'f(x)')", lambda: re.search("(", "f(x)"))
show("re.search(re.escape('('), 'f(x)').span()", lambda: re.search(re.escape("("), "f(x)").span())
show("re.sub('x', re.escape('a.b'), 'x')", lambda: re.sub("x", re.escape("a.b"), "x"))
show("re.sub('x', lambda m: 'a\\\\d', 'x')", lambda: re.sub("x", lambda m: "a\\d", "x"))

print("[4] a valid string escape inside a pattern")
show('len("\\bcat\\b")', lambda: len("\bcat\b"))
show('re.search("\\bcat\\b", "a cat")', lambda: re.search("\bcat\b", "a cat"))
show('re.search(r"\\bcat\\b", "a cat").span()', lambda: re.search(r"\bcat\b", "a cat").span())
```

### 7. ★★★ 소유 수량자·원자 그룹으로 바꾼 패턴은 폭발 입력에서도 끝난다 (왜)

* `^(a+)+$` 에 `'a' * 30 + '!'` 를 주면 2초 안에 안 끝나는데, `^(a++)+$`·`^(?>a+)+$` 는 `n = 100000` 에서도 끝난다 — **되돌이 지점**으로 설명하면?
* 바꾼 패턴이 **같은 답**을 낸다는 것은 어떻게 확인하나? 그리고 이 처방을 **아무 패턴에나** 쓸 수 없는 이유는?

### 8. ★★ 컴파일 캐시 — 무엇이 약속이고 무엇이 판의 사정인가 (경계)

* `re.compile(p) is re.compile(p)` 가 참인 것, 플래그만 다르면 거짓인 것, `re.purge()` 뒤에 거짓인 것 중 **문서가 약속한 것**은?
* 5번 표의 캐시 행을 두 판에서 견주면 무엇을 말해 주나 — 그리고 「`re.compile` 이 빠르다」를 이 문서가 **왜 적지 않나**?

### 9. 층 가르기 (경계)

* 「`$` 는 끝 줄바꿈 앞에서도 맞는다」·「캐시 상한 512」·「`invalid group reference 1 at position 2`」·「무효 이스케이프가 내는 경고의 종류」 —
  각각 **라이브러리 보장 · CPython 구현** 중 어디인가?
* ★ 폭발 격자의 「`n = 30` 에서 안 끝났다」는 어느 층이고, 이 문서가 그 위에 **무엇을** 결론으로 세웠나?

### 10. 이웃 주제와의 경계 (연결)

* ★ [JS 28번](../../../js/syntax/28-string-methods-and-template-literals/2-summary.md)의 `$` 격자와 4번을 나란히 놓으면 **없는 그룹**에서 두 언어가 어떻게 갈리나?
* ★ [JS 30번](../../../js/syntax/30-regexp-advanced/2-summary.md)이 적은 「`a++`·`(?>…)` 는 파이썬 3.12 만 받았다」를 5번 표와 어떻게 맞춰 읽나? 그리고 [`cs/algorithm/25-string-matching/`](../../../../../algorithm/25-string-matching/2-summary.md)과는 무엇을 나눠 맡나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|---|---|---|---|
|  |  |  |  |
|  |  |  |  |
|  |  |  |  |
