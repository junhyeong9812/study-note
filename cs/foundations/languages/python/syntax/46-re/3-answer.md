# python/syntax/46-re — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> [1-question.md](1-question.md)의 번호와 **1:1**로 대응한다. 질문 10개 = 답 10개.
>
> 이 파일의 모든 출력은 `python3` **3.12.3** 과 `python3.11` **3.11.15**(Linux, x86_64)에서 실제로 돌려 나온 것이다. 지어낸 출력은 없다.
> 던지는 형태는 `python3 - <파일` 로 고정했다. ★ **시간은 한 번도 재지 않았다** — 폭발은 `timeout 2` 의 참/거짓, 캐시는 `is` 로만 셌다.

## 정답

### 1. `'123\n'` 에 `match \d+$` 는 `'123'@0-3` · `\Z`·`fullmatch` 는 `None` — 갈린 입력 `1 / 3`

**출력**

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

```text
===== python3 - <e46_anchor.py =====
call              '123'             '123\n'           '12\n34'
match     \d+     '123'@0-3         '123'@0-3         '12'@0-2
match     \d+$    '123'@0-3         '123'@0-3         None
match     \d+\Z   '123'@0-3         None              None
fullmatch \d+     '123'@0-3         None              None
search    \d+$    '123'@0-3         '123'@0-3         '34'@3-5
search    \d+$ M  '123'@0-3         '123'@0-3         '12'@0-2
findall   ^\d+ M  ['123']           ['123']           ['12', '34']
match     ^34 M   None              None              None
match(\d+$) vs fullmatch(\d+), differing inputs: 1 / 3
(exit 0)
```

**왜 그런가**

* ★★★ `$` 는 **문자열 끝, 또는 끝 줄바꿈 바로 앞**에서 맞는다(문서). 그래서 `'123\n'` 이 `\d+$` 를 **통과**한다.
* ★★★ **`\Z`** 는 끝에서만, **`fullmatch`** 는 전체를 요구한다 — 둘 다 `None`. 검증에는 이쪽을 쓴다.
* ★★ `'12\n34'` — `search \d+$` 는 **마지막 줄** `'34'@3-5`, `MULTILINE` 이면 **첫 줄 끝** `'12'@0-2`(가장 앞의 매치). `findall ^\d+ M` 은 줄마다 `['12', '34']`.
* ★ `match ^34 M` 은 셋 다 `None` — `match` 는 `MULTILINE` 이어도 **문자열 맨 앞**에서만 시작한다(문서).

### 2. 탐욕 한 덩어리 · 게으름 넷 · `a*+a` 는 `None` · `a{3,5}+aa` 도 `None` · `.` 은 `re.S` 여야 줄바꿈

**출력**

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

```text
===== python3 - <e46_greedy.py =====
[1] ['<a><b></b></a>']
[2] ['<a>', '<b>', '</b>', '</a>']
[3] ['<a>', '<b>', '</b>', '</a>']
[4] ['x" v="y']
[5] ['x', 'y']
[6] <re.Match object; span=(0, 4), match='aaaa'>
[7] None
[8] <re.Match object; span=(0, 6), match='aaaaaa'> None
[9] ['abc'] ['a\nc', 'abc']
(exit 0)
```

**왜 그런가**

* ★★ `<.*>` 는 끝까지 먹고 **마지막 `>`** 까지 물러난다. `<.*?>` 는 0개부터 늘려 **첫 `>`** 에서 멈춘다. `<[^>]*>` 는 **물러날 일 없이** 같은 넷.
* ★★ `"(.*)"` 는 `'x" v="y'` — 첫 따옴표부터 **마지막 따옴표**까지.
* ★★★ `a*a` 는 `a*` 가 **하나를 도로 내놓아** 맞는다. `a*+a` 는 **내놓을 되돌이 지점이 없어** `None`. `{3,5}+` 도 같다(문서의 두 예 그대로).
* ★ `.` 은 기본으로 `\n` 을 안 먹는다 — `re.S` 를 줘야 `'a\nc'` 가 잡힌다.

### 3. 참여 안 한 그룹은 `groups()` 에서 `None` · `findall` 과 치환에서 `''` · 반복 그룹은 마지막 `'c'` · 캡처 `split` 은 구분자까지

**출력**

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

```text
===== python3 - <e46_groups.py =====
[1] group()      : '2026-09'
[2] groups()     : ('2026', '09', None, None)
[3] groups('')   : ('2026', '09', '', '')
[4] groupdict()  : {'y': '2026', 'm': '09', 'd': None}
[5] span('m')    : (8, 10)  span('d'): (-1, -1)
[6] (\w)+ on abc : abc c
[7] findall      : [('1', 'x'), ('2', '')]
[8] sub unmatched: 'a[]c'
[9] split        : ['a', '-', 'b'] ['a', 'b']
[10] split empty : ['', 'hi', ' ', 'yo', '']
[11] sub x*      : '-a-b--d-'
(exit 0)
```

**왜 그런가**

* ★★ 선택 부분 `(-(?P<d>\d\d))?` 가 **통째로 건너뛰어져** 그룹 3·4 가 `None`, `span('d')` 가 `(-1, -1)`. `groups('')` 가 기본값을 바꾼다.
* ★★ **같은 「참여 안 함」이 자리마다 다르게** 나온다 — `groups()` 는 `None`, `findall` 은 `''`, 치환 `\1` 은 `''`(3.5 부터 — 문서).
* ★ `(\w)+` 는 그룹이 **마지막 바퀴의 `'c'`** 만 남긴다.
* ★ `re.split(r"(-)", …)` 은 **구분자를 결과에 넣고**, `\b` 같은 **빈 매치**로도 쪼갠다. `sub("x*", "-", "abxd")` 는 문서의 예 그대로 `'-a-b--d-'`.

### 4. `$&` 는 전부 글자 그대로 · 없는 그룹은 에러(`error`·`IndexError`) · `\10` 은 그룹 10 · `\0` 은 `'\x00'` · 함수 열은 전부 글자 그대로 — `36 / 52`, 에러 19

**출력**

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

```text
===== python3 - <e46_sub.py =====
python 3.12
template         escape('b')     (b)             (?P<g>b)        (?P<g>b) + fn
'[$&]'           'a[$&]c'        'a[$&]c'        'a[$&]c'        'a[$&]c'
'[\\g<0>]'       'a[b]c'         'a[b]c'         'a[b]c'         'a[\\g<0>]c'
'[\\1]'          error#1         'a[b]c'         'a[b]c'         'a[\\1]c'
'[\\g<1>0]'      error#2         'a[b0]c'        'a[b0]c'        'a[\\g<1>0]c'
'[\\10]'         error#3         error#4         error#5         'a[\\10]c'
'[\\9]'          error#6         error#7         error#8         'a[\\9]c'
'[\\g<g>]'       error#9         error#10        'a[b]c'         'a[\\g<g>]c'
'[\\g<x>]'       error#11        error#12        error#13        'a[\\g<x>]c'
'[\\n]'          'a[\n]c'        'a[\n]c'        'a[\n]c'        'a[\\n]c'
'[\\q]'          error#14        error#15        error#16        'a[\\q]c'
'[\\\\]'         'a[\\]c'        'a[\\]c'        'a[\\]c'        'a[\\\\]c'
'[\\0]'          'a[\x00]c'      'a[\x00]c'      'a[\x00]c'      'a[\\0]c'
'[\\g<\u0661>]'  error#17        error#18        error#19        'a[\\g<١>]c'

  #1 '[\\1]' | escape('b') | error: invalid group reference 1 at position 2
  #2 '[\\g<1>0]' | escape('b') | error: invalid group reference 1 at position 4
  #3 '[\\10]' | escape('b') | error: invalid group reference 10 at position 2
  #4 '[\\10]' | (b) | error: invalid group reference 10 at position 2
  #5 '[\\10]' | (?P<g>b) | error: invalid group reference 10 at position 2
  #6 '[\\9]' | escape('b') | error: invalid group reference 9 at position 2
  #7 '[\\9]' | (b) | error: invalid group reference 9 at position 2
  #8 '[\\9]' | (?P<g>b) | error: invalid group reference 9 at position 2
  #9 '[\\g<g>]' | escape('b') | IndexError: unknown group name 'g'
  #10 '[\\g<g>]' | (b) | IndexError: unknown group name 'g'
  #11 '[\\g<x>]' | escape('b') | IndexError: unknown group name 'x'
  #12 '[\\g<x>]' | (b) | IndexError: unknown group name 'x'
  #13 '[\\g<x>]' | (?P<g>b) | IndexError: unknown group name 'x'
  #14 '[\\q]' | escape('b') | error: bad escape \q at position 1
  #15 '[\\q]' | (b) | error: bad escape \q at position 1
  #16 '[\\q]' | (?P<g>b) | error: bad escape \q at position 1
  #17 '[\\g<\u0661>]' | escape('b') | error: bad character in group name '١' at position 4
  #18 '[\\g<\u0661>]' | (b) | error: bad character in group name '١' at position 4
  #19 '[\\g<\u0661>]' | (?P<g>b) | error: bad character in group name '١' at position 4

cells that differ from the template text: 36 / 52  (raised: 19 · warned: 0)
(exit 0)
```

같은 소스를 3.11 에 던지면 마지막 행만 달라진다.

```text
===== python3.11 - <e46_sub_py311.py =====
python 3.11
template         escape('b')     (b)             (?P<g>b)        (?P<g>b) + fn
'[$&]'           'a[$&]c'        'a[$&]c'        'a[$&]c'        'a[$&]c'
'[\\g<0>]'       'a[b]c'         'a[b]c'         'a[b]c'         'a[\\g<0>]c'
'[\\1]'          error#1         'a[b]c'         'a[b]c'         'a[\\1]c'
'[\\g<1>0]'      error#2         'a[b0]c'        'a[b0]c'        'a[\\g<1>0]c'
'[\\10]'         error#3         error#4         error#5         'a[\\10]c'
'[\\9]'          error#6         error#7         error#8         'a[\\9]c'
'[\\g<g>]'       error#9         error#10        'a[b]c'         'a[\\g<g>]c'
'[\\g<x>]'       error#11        error#12        error#13        'a[\\g<x>]c'
'[\\n]'          'a[\n]c'        'a[\n]c'        'a[\n]c'        'a[\\n]c'
'[\\q]'          error#14        error#15        error#16        'a[\\q]c'
'[\\\\]'         'a[\\]c'        'a[\\]c'        'a[\\]c'        'a[\\\\]c'
'[\\0]'          'a[\x00]c'      'a[\x00]c'      'a[\x00]c'      'a[\\0]c'
'[\\g<\u0661>]'  error#17        'a[b]c' W1      'a[b]c' W2      'a[\\g<١>]c'

  #1 '[\\1]' | escape('b') | error: invalid group reference 1 at position 2
  #2 '[\\g<1>0]' | escape('b') | error: invalid group reference 1 at position 4
  #3 '[\\10]' | escape('b') | error: invalid group reference 10 at position 2
  #4 '[\\10]' | (b) | error: invalid group reference 10 at position 2
  #5 '[\\10]' | (?P<g>b) | error: invalid group reference 10 at position 2
  #6 '[\\9]' | escape('b') | error: invalid group reference 9 at position 2
  #7 '[\\9]' | (b) | error: invalid group reference 9 at position 2
  #8 '[\\9]' | (?P<g>b) | error: invalid group reference 9 at position 2
  #9 '[\\g<g>]' | escape('b') | IndexError: unknown group name 'g'
  #10 '[\\g<g>]' | (b) | IndexError: unknown group name 'g'
  #11 '[\\g<x>]' | escape('b') | IndexError: unknown group name 'x'
  #12 '[\\g<x>]' | (b) | IndexError: unknown group name 'x'
  #13 '[\\g<x>]' | (?P<g>b) | IndexError: unknown group name 'x'
  #14 '[\\q]' | escape('b') | error: bad escape \q at position 1
  #15 '[\\q]' | (b) | error: bad escape \q at position 1
  #16 '[\\q]' | (?P<g>b) | error: bad escape \q at position 1
  #17 '[\\g<\u0661>]' | escape('b') | error: invalid group reference 1 at position 4
  W1 '[\\g<\u0661>]' | (b) | DeprecationWarning: bad character in group name '١' at position 4
  W2 '[\\g<\u0661>]' | (?P<g>b) | DeprecationWarning: bad character in group name '١' at position 4

cells that differ from the template text: 36 / 52  (raised: 17 · warned: 2)
(exit 0)
```

**왜 그런가**

* ★★★ 파이썬 템플릿이 읽는 것은 **`\` 로 시작하는 표기뿐**이다 — `$` 는 뜻이 없어 `'a[$&]c'`.
* ★★★ **없는 그룹은 에러** — 번호는 `error: invalid group reference`, 이름은 **`IndexError: unknown group name`**(예외 종류부터 다르다).
* ★★ `\10` 은 **그룹 10** 이라 그룹이 하나뿐이면 에러. 「그룹 1 + `0`」은 `\g<1>0` → `'a[b0]c'`.
* ★★ `\n` 은 줄바꿈, **`\q` 는 에러**(3.7 부터), `\\` 는 역슬래시 하나, **`\0` 은 8진 이스케이프라 `'\x00'`**(그룹 0 은 `\g<0>`).
* ★★★ **함수를 주면 돌려준 문자열은 템플릿으로 읽히지 않는다** — 넷째 열 전부 글자 그대로. 바깥 글자를 넣을 때의 처방.
* ★★ 마지막 행 `\g<U+0661>` — 3.12 는 에러(**ASCII 숫자만** — 3.12 문서), 3.11 은 그룹 1 로 읽고 `DeprecationWarning` 만(`17 → 19` · `2 → 0`).

### 5. `7 / 15` — 소유·원자는 두 판 같고, 무효 이스케이프 넷이 `DeprecationWarning` → `SyntaxWarning`, 기본 필터에서 3.11 은 조용하고 3.12 는 찍는다, `\g<U+0661>`·캐시 행도 갈린다

**출력**

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

```text
===== cd e46_vgrid && bash e46_vgrid.sh =====
probe                                        python3.11            python3 (3.12)
  compile a++                                'a++'                 'a++'
  compile (?>a+)                             '(?>a+)'              '(?>a+)'
  match a*a on aaaa                          'aaaa'                'aaaa'
  match a*+a on aaaa                         None                  None
* literal "\d+"                              DeprecationWarning    SyntaxWarning
* literal "\."                               DeprecationWarning    SyntaxWarning
* literal b"\d"                              DeprecationWarning    SyntaxWarning
* literal "\477"                             DeprecationWarning    SyntaxWarning
  literal r"\d+"                             (none)                (none)
  literal "\\d+"                             (none)                (none)
  literal "\n"                               (none)                (none)
* sub (b) -> [\g<U+0661>]                    'a[b]c'               error(bad character in group name '١' at position 4)
  re.error.__name__                          'error'               'error'
* p0 same object after touch + 1 new         False                 True
* default filter prints the "\d+" warning    no (stderr empty)     yes: <stdin>:2: SyntaxWarning: invalid escape sequence '\d'

rows where the two versions differ: 7 / 15
(exit 0)
```

**왜 그런가**

* ★★★ `a++`·`(?>a+)`·`a*+a` 는 **3.11 에서 이미** 같다 — *"versionadded 3.11"*.
* ★★★ 무효 이스케이프(`"\d+"`·`"\."`·`b"\d"`·`"\477"`)는 **파서**가 경고한다 — 3.11 `DeprecationWarning`, 3.12 `SyntaxWarning`(What's New 3.12). raw 문자열과 `\\` 는 두 판 다 경고 없음.
* ★★★ **기본 필터 행** — 3.11 은 `no (stderr empty)`. `DeprecationWarning` 은 기본으로 거의 숨겨지므로 **같은 코드가 3.11 에서는 조용했다.** 3.12 는 `<stdin>:2: SyntaxWarning: invalid escape sequence '\d'` 를 stderr 에 찍는다.
* ★★ `\g<U+0661>` — 4번의 마지막 행.
* ★★ **캐시 행** — 상한까지 채운 뒤 `p0` 를 한 번 더 쓰고 새 패턴 하나를 넣었다. 3.11 은 `p0` 를 **버렸고**(먼저 들어온 것부터), 3.12 는 **남겼다**(최근에 쓴 것을 남긴다). 8번에서 층을 가른다.

### 6. 섞으면 `TypeError` · `\d+` 는 아라비아-인도 숫자에 `True`(`re.ASCII` 면 `False`) · `re.escape` 는 `7 / 7` · 치환의 `re.escape` 는 역슬래시가 남는다 · `"\bcat\b"` 는 길이 5 에 `None`

**출력**

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

```text
===== python3 - <e46_types.py =====
[1] str and bytes
re.search(r'\d', b'a1')                      TypeError: cannot use a string pattern on a bytes-like object
re.search(rb'\d', 'a1')                      TypeError: cannot use a bytes pattern on a string-like object
re.sub(rb'1', '2', b'a1')                    TypeError: sequence item 1: expected a bytes-like object, str found
re.search(rb'\d', b'a1').group()             b'1'
[2] what \d and \w mean
fullmatch(r'\d+', U+0661 U+0662 U+0663)      True
  same with re.ASCII                         False
  int() of that text                         123
fullmatch(r'\w+', '한글')                      True
fullmatch(rb'\w+', '한글'.encode())            False
[3] re.escape
   'a.b'    -> 'a\\.b'        fullmatch itself: True
   '1+1=2'  -> '1\\+1=2'      fullmatch itself: True
   '[x]'    -> '\\[x\\]'      fullmatch itself: True
   '$5'     -> '\\$5'         fullmatch itself: True
   'a b'    -> 'a\\ b'        fullmatch itself: True
   '_-~'    -> '_\\-\\~'      fullmatch itself: True
   '한글'     -> '한글'           fullmatch itself: True
   escaped patterns that match their own text: 7 / 7
re.search('(', 'f(x)')                       error: missing ), unterminated subpattern at position 0
re.search(re.escape('('), 'f(x)').span()     (1, 2)
re.sub('x', re.escape('a.b'), 'x')           'a\\.b'
re.sub('x', lambda m: 'a\\d', 'x')           'a\\d'
[4] a valid string escape inside a pattern
len("\bcat\b")                               5
re.search("\bcat\b", "a cat")                None
re.search(r"\bcat\b", "a cat").span()        (2, 5)
(exit 0)
```

**왜 그런가**

* ★★ **`str` 과 `bytes` 는 섞을 수 없다**(문서). 치환 문자열만 다른 타입이면 문구가 `sequence item 1: expected a bytes-like object, str found` 로 **원인을 돌려 말한다.**
* ★★★ `str` 패턴의 `\d` 는 **유니코드 10진 숫자 전부**다(문서) — `U+0661 U+0662 U+0663` 이 맞고, `int()` 도 `123` 으로 읽는다. `re.ASCII` 가 `[0-9]` 로 좁힌다. `\w` 도 `str` 에서는 한글을 받는다.
* ★★ `re.escape` 는 **특수한 글자만** 이스케이프하고 자기 자신에 다시 맞는다(`7 / 7`). 치환 쪽에 쓰면 **`\` 가 결과에 남는다**(`'a\\.b'`) — 문서가 금지한다.
* ★★★ `"\bcat\b"` 는 **유효한** 문자열 이스케이프(백스페이스)라 **경고 없이** 다섯 글자가 된다 — `None`. raw 로 쓰면 단어 경계 `(2, 5)`.

### 7. 안쪽이 전부 먹고 되돌이 지점을 버리니 「나눠 갖기」를 다시 시도할 길이 없다 — 대조 칸만 `no`, `12 / 13` · 답은 `!` 유무대로 · 되돌이가 필요한 패턴에는 못 쓴다

**출력**

```python
# e46_xprobe.py
# argv: pattern, n, tail -> print whether re.match(pattern, "a" * n + tail) matched.
import re
import sys

pattern, n, tail = sys.argv[1], int(sys.argv[2]), sys.argv[3]
print(re.match(pattern, "a" * n + tail) is not None)
```

```sh
# e46_explode.sh
#!/usr/bin/env bash
# Does each run finish within the limit? Only yes/no (and the answer) is printed -- no elapsed time.
# The control column ^(a+)+$ gets one cell; its full n-by-engine grid belongs to JS topic 30.
set -u -o pipefail
LIMIT=2
cells=0; done_cells=0
cell() {  # interpreter pattern n tail
  local out rc
  out=$(timeout "$LIMIT" "$1" e46_xprobe.py "$2" "$3" "$4" 2>&1); rc=$?
  cells=$((cells + 1))
  if [ $rc -eq 0 ]; then done_cells=$((done_cells + 1)); printf '%s' "yes ($out)"; else printf '%s' "no (exit $rc)"; fi
}
printf '%-12s%-12s%-8s%-8s%s\n' "interpreter" "pattern" "n" "tail" "finished? (answer)"
for py in python3.11 python3; do
  for spec in '^(a+)+$;30;!' '^(a++)+$;30;!' '^(a++)+$;100000;!' '^(a++)+$;100000;' '^(?>a+)+$;30;!' '^(?>a+)+$;100000;!' '^(?>a+)+$;100000;'; do
    IFS=';' read -r pat n tail <<< "$spec"
    [ "$py" = python3.11 ] && [ "$pat" = '^(a+)+$' ] && continue
    printf '%-12s%-12s%-8s%-8s' "$py" "$pat" "$n" "${tail:-(none)}"
    cell "$py" "$pat" "$n" "$tail"
    echo ""
  done
done
echo ""
echo "finished within ${LIMIT}s: $done_cells / $cells"
```

```text
===== cd e46_explode && bash e46_explode.sh =====
interpreter pattern     n       tail    finished? (answer)
python3.11  ^(a++)+$    30      !       yes (False)
python3.11  ^(a++)+$    100000  !       yes (False)
python3.11  ^(a++)+$    100000  (none)  yes (True)
python3.11  ^(?>a+)+$   30      !       yes (False)
python3.11  ^(?>a+)+$   100000  !       yes (False)
python3.11  ^(?>a+)+$   100000  (none)  yes (True)
python3     ^(a+)+$     30      !       no (exit 124)
python3     ^(a++)+$    30      !       yes (False)
python3     ^(a++)+$    100000  !       yes (False)
python3     ^(a++)+$    100000  (none)  yes (True)
python3     ^(?>a+)+$   30      !       yes (False)
python3     ^(?>a+)+$   100000  !       yes (False)
python3     ^(?>a+)+$   100000  (none)  yes (True)

finished within 2s: 12 / 13
(exit 0)
```

**왜 그런가**

* ★★★ `^(a+)+$` 는 `a` 들을 **안쪽 `+` 와 바깥 `+` 가 나눠 갖는 방법마다** 되돌이 지점을 남긴다. 끝의 `!` 때문에 `$` 가 늘 실패하니 **그 방법을 전부** 시도한다 — `n = 30` 에서 2초 안에 안 끝났다(`exit 124`).
* ★★★ `a++`·`(?>a+)` 는 안쪽이 **전부 먹고 되돌이 지점을 버린다** — 나눠 갖기를 다시 시도할 길이 없어 곧바로 실패한다. `n = 100000` 도 끝났다(두 판 모두).
* ★★ **같은 답** — 각 칸이 답을 함께 찍는다. `!` 가 있으면 `False`, 없으면 `True` — 원래 패턴이 내야 할 값과 같다.
* ★★ **아무 패턴에나 못 쓰는 이유** — 소유는 **답을 바꿀 수 있다**(2번 `a*+a` 가 `None`). 이 패턴은 **안쪽이 전부 먹어도 답이 같아서** 바꿀 수 있었다. 가장 확실한 것은 겹친 수량자를 없애는 것(`^a+$`).
* ★ 대조 칸은 **한 칸**만 뒀다 — 엔진 × n 의 전체 격자는 [JS 30번](../../../js/syntax/30-regexp-advanced/2-summary.md) 동작 (7)이 정본이다(백트래킹 엔진 셋이 `n = 20` 까지 끝나고 `n = 30` 부터 안 끝났다).

### 8. 「최근 패턴은 캐시된다」까지가 약속 · 키·크기·정책은 구현(판마다 달랐다) · 시간은 재지 않았다

**출력**

```python
# e46_cache.py
import re

re.purge()
a = re.compile(r"\d+")
print("[1] compile twice, same object     :", re.compile(r"\d+") is a)
print("[2] same text, flag re.I           :", re.compile(r"\d+", re.I) is a)
print("[3] same text as bytes             :", re.compile(rb"\d+") is a)
re.search(r"x\d", "x1")
print("[4] after re.search(r'x\\d', ...)   :", re.compile(r"x\d") is re.compile(r"x\d"))
print("[5] compile(a) returns a itself    :", re.compile(a) is a)
re.purge()
print("[6] after re.purge()               :", re.compile(r"\d+") is a)

p = re.compile(r"(\d)")
print("[7] one object, search at pos 0, 2, 0 :", [p.search("a1b2", pos).span() for pos in (0, 2, 0)])

hits = 0
first = {}
for round_no in range(3):
    for word in ("cat", "dog", "cow"):
        obj = re.compile(word)
        if word in first and obj is first[word]:
            hits += 1
        first.setdefault(word, obj)
print("[8] 3 rounds x 3 patterns, same object as the first compile: %d / 6" % hits)
```

```text
===== python3 - <e46_cache.py =====
[1] compile twice, same object     : True
[2] same text, flag re.I           : False
[3] same text as bytes             : False
[4] after re.search(r'x\d', ...)   : True
[5] compile(a) returns a itself    : True
[6] after re.purge()               : False
[7] one object, search at pos 0, 2, 0 : [(1, 2), (3, 4), (1, 2)]
[8] 3 rounds x 3 patterns, same object as the first compile: 6 / 6
(exit 0)
```

**왜 그런가**

* ★★ **문서가 약속한 것** — *"The compiled versions of the most recent patterns passed to `re.compile` and the module-level matching functions are cached"* 와 `re.purge()` 가 **캐시를 비운다**는 것. 그래서 `[1]`·`[4]` 가 `True`, `[6]` 이 `False` 인 것은 약속 위에 선다.
* ★★ `[2]`·`[3]`(플래그·타입이 다르면 다른 객체)은 **키가 (타입, 글자, 플래그)** 라는 **CPython 소스의 사정**이다 — 다른 객체가 나와도 결과는 같다.
* ★★★ 5번의 캐시 행 — **같은 호출 순서에 3.11 `False` · 3.12 `True`.** 캐시의 **정책이 판마다 다르다** — 문서가 크기도 정책도 약속하지 않으니 판이 오르면 또 바뀌어도 된다.
* ★★★ 「빠르다」를 적지 않는 이유 — 이 문서가 **잰 것은 같은 객체가 돌아온 횟수**(`6 / 6`)뿐이다. 시간은 재지 않았다.

### 9. 보장 · 구현 · 구현(문구) · 보장 — 「`n = 30`」은 이 판의 관찰, 결론은 「소유·원자판이 `n = 100000` 도 끝났다」

**왜 그런가**

| 사실 | 층 | 근거 |
|---|---|---|
| `$` 는 끝 줄바꿈 앞에서도 맞는다 | **라이브러리 보장** | `$` 절 |
| 캐시 상한 512 | **CPython 구현** | 설치본 `re/__init__.py` 의 `_MAXCACHE` — 문서에 없다 |
| `invalid group reference 1 at position 2` | **CPython 구현**(문구) | 실행 — 에러가 나는 것 자체는 없는 그룹이라서다 |
| 무효 이스케이프 경고의 종류(3.11 `DeprecationWarning` · 3.12 `SyntaxWarning`) | **언어 보장** | What's New 3.12 · 어휘 분석 절 |

* ★★ 「`n = 30` 에서 안 끝났다」는 **이 판·이 머신·제한 시간 2초의 관찰**이다 — 머신이 빠르면 경계가 옮겨 간다.
  그래서 결론을 그 경계 **값**에 세우지 않고, 「**겹친 탐욕은 두 자릿수 n 에서 안 끝나고, 소유·원자판은 `n = 100000` 에서도 끝났다**」는 대비에 세웠다.

### 10. JS 는 없는 그룹을 글자 그대로, 파이썬은 에러 — 「3.12 만」은 엔진 비교였고 판으로는 3.11 부터 — 25번은 고정 문자열 검색(나이브·KMP)까지, 정규식 엔진은 여기와 JS 30

**왜 그런가**

* ★★★ JS 28번 격자에서 `$9`·`$0`·문자열 패턴의 `$1` 은 **글자 그대로** 남았다(`"a[$9]c"`). 파이썬은 같은 자리가 **`error: invalid group reference`**. **JS 는 조용한 쪽, 파이썬은 시끄러운 쪽**이다. 그리고 파이썬의 `$` 는 아예 뜻이 없다.
* ★★★ JS 30번 동작 (9)의 12패턴 격자는 **V8·RE2·파이썬 세 엔진**을 견줬고 **파이썬 판은 3.12 하나**였다. 「파이썬 3.12 만 받았다」는 「세 엔진 중 파이썬만」이라는 뜻으로 읽어야 한다 — **판으로 물으면 3.11 도 받는다**(5번 윗 네 행).
* ★★ [`cs/algorithm/25-string-matching/`](../../../../../algorithm/25-string-matching/2-summary.md)은 **고정된 패턴 하나를 찾는 나이브·KMP** 까지다 — 백트래킹 정규식 엔진이나 폭발을 다루는 절이 **없다.** 「엔진이 어떻게 걷고 언제 폭발하나」는 JS 30번과 이 주제가, 「고정 문자열 검색의 최악을 어떻게 없애나」는 그쪽이 맡는다.

## 실행 검증

| 무엇을 | 어떻게 | 몇 번 | 결과 |
|---|---|---|---|
| 끝 네 가지 | `python3 - <e46_anchor.py` | 3(캡처 + 재대조 + `PYTHONHASHSEED` 바꾼 재캡처) | **1 / 3** |
| 수량자 | `python3 - <e46_greedy.py` | 3 | `a*+a` → `None` |
| 그룹 | `python3 - <e46_groups.py` | 3 | `None` · `''` · `'c'` |
| 치환 격자 | `python3 - <e46_sub.py` · `python3.11 - <e46_sub_py311.py` | 3씩 | **36 / 52** · 에러 19 대 17 |
| 판 격자 | `cd e46_vgrid && bash e46_vgrid.sh` | 3 | **7 / 15** |
| 폭발 | `cd e46_explode && bash e46_explode.sh` | 3 | **12 / 13** |
| 캐시 | `python3 - <e46_cache.py` | 3 | **6 / 6** |
| 타입·숫자·이스케이프 | `python3 - <e46_types.py` | 3 | `7 / 7` |

**구현 의존 항목** — 판이 오르면 다시 돌려야 하는 것.

| 항목 | 왜 |
|---|---|
| ★★ 판 격자의 캐시 행 | 캐시 크기·정책은 구현이다 — 3.11 과 3.12 가 이미 갈렸다 |
| ★ 무효 이스케이프 | 문서가 미래에 `SyntaxError` 가 된다고 적는다 |
| 폭발 격자의 대조 칸 | 머신·제한 시간에 달린다 |
| 예외·경고 **문구** | 구현이다 |

★ **안 흔들리는 칸** — 매치 결과·`span` · **「1 / 3」·「36 / 52」·「7 / 15」·「12 / 13」·「6 / 6」·「7 / 7」** · 경고 **종류** · `(exit N)`.
★★ **이 주제가 한 번도 안 잰 것** — **시간**(부적용) · **3.13 이후**(판 없음 — 못 잰 것).
