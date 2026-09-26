# python/syntax/46-re — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **이 본문은 원고가 아니라 Claude 작성이다**(문법·API 갈래는 원고 없이 공식 문서로 접지한다).
>
> **기준 소스** — 열어서 확인한 것만(문서 원본 `.rst` 를 받아 문장을 찾았다).
> - [`re`(3.12)](https://docs.python.org/3.12/library/re.html) —
>   `$` 의 *"Matches the end of the string or just before the newline at the end of the string"* ·
>   `\Z` 의 *"Matches only at the end of the string."* ·
>   소유 수량자의 *"these do not allow back-tracking when the expression following it fails to match"* 와 *"versionadded 3.11"* ·
>   원자 그룹 `(?>...)` 의 *"versionadded 3.11"* ·
>   `\d` 의 *"Matches any Unicode decimal digit … This includes `[0-9]`, and also many other digit characters"* ·
>   *"Unicode strings and 8-bit strings cannot be mixed"* ·
>   `sub` 의 *"`\g<2>` is therefore equivalent to `\2`, but isn't ambiguous in a replacement such as `\g<2>0`"* · *"versionchanged 3.5: Unmatched groups are replaced with an empty string"* · *"versionchanged 3.12: Group id can only contain ASCII digits"* ·
>   컴파일 캐시의 *"The compiled versions of the most recent patterns passed to `re.compile` and the module-level matching functions are cached"* ·
>   `escape` 의 *"This function must not be used for the replacement string in `sub`"*
> - [What's New 3.11](https://docs.python.org/3.12/whatsnew/3.11.html) — *"Atomic grouping (`(?>...)`) and possessive quantifiers (`*+`, `++`, `?+`, `{m,n}+`) are now supported in regular expressions."*
> - [What's New 3.12](https://docs.python.org/3.12/whatsnew/3.12.html) — *"A backslash-character pair that is not a valid escape sequence now generates a `SyntaxWarning`, instead of `DeprecationWarning`. For example, `re.compile("\d+\.\d+")` now emits a `SyntaxWarning`"*
>
> **실행 검증** — 이 문서에 실린 출력은 전부 이 머신에서 실제로 돌려 나온 것이다. 지어낸 출력은 없다.\
> 판은 `python3` **3.12.3** 이 본판이고, 판 경계를 위해 `python3.11` **3.11.15** 로 블록 셋(치환 격자 · 판 격자 · 폭발 격자)을 더 던졌다.\
> ★★★ **이 문서는 시간을 한 번도 재지 않았다.** 백트래킹 폭발도 [JS 30번](../../../js/syntax/30-regexp-advanced/2-summary.md)이 쓴 방식 그대로 **「2초 안에 끝났나」 참/거짓**으로만 물었다.
> 컴파일 캐시도 **「같은 객체가 돌아왔나」(`is`)** 로만 셌다 — 「`re.compile` 이 빠르다」는 이 문서가 **주장하지 않는다.**\
> **버전**(문서 표기) — 소유 수량자·원자 그룹 **3.11** · 무효 이스케이프가 `SyntaxWarning` **3.12**(3.11 까지는 `DeprecationWarning`) · 치환의 그룹 번호는 ASCII 숫자만 **3.12** · 치환에서 참여 안 한 그룹이 빈 글자 **3.5** · `repl` 의 알 수 없는 `\` + 글자가 에러 **3.7**.\
> ★ **구현 대 보장 한 줄** — 위 문서 문장들이 보장이고, **예외 문구**와 **캐시의 크기·정책**은 CPython 의 것이다(캐시 정책은 3.11 과 3.12 가 실제로 갈렸다 — 동작 5).\
> ★ **흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다 | 안 흔들린다(근거로 써도 되는 칸) |
> |---|---|
> | 판이 오르면 예외·경고 **문구** · 캐시 **정책**(동작 5 의 캐시 행) | ★★ 매치 결과·`span` · 마지막 줄 **「… N / M」** |
> | 폭발 격자에서 **「끝나지 않은 칸」이 어느 n 부터인가**(머신·제한 시간에 달린다 — 이 문서는 `n = 30` 한 칸만 썼다) | 판 격자의 **경고 종류**(`DeprecationWarning` 대 `SyntaxWarning`) |
> | — (주소·시간·`set` 출력을 한 곳도 안 찍었다) | `(exit N)` |
>
> **선행** — [06-strings-bytes-unicode](../06-strings-bytes-unicode/2-summary.md)(★★ **`str` 과 `bytes` 는 다른 타입이다** — 패턴과 입력도 섞이지 않는다) ·
> [07-string-methods](../07-string-methods/2-summary.md)(★ **정규식을 꺼내는 선** — 그쪽 표가 경계다) ·
> [02-is-vs-eq-interning](../02-is-vs-eq-interning/2-summary.md)(`SyntaxWarning` 이 컴파일 시점 경고라는 것).

## 한눈에 — 쉽게 말하면

**정규식 엔진은 「갈림길마다 한쪽을 먼저 가 보는 탐험가」다.** 막히면 **마지막 갈림길로 돌아가**(되돌이) 다른 쪽을 가 본다.

* **탐욕(`*`)** — 일단 **최대한 멀리** 가 보고, 막히면 한 칸씩 물러난다.
* **게으름(`*?`)** — 일단 **최소한만** 가 보고, 막히면 한 칸씩 더 간다.
* ★ **소유(`*+`)·원자 그룹(`(?>…)`)** — 멀리 간 뒤 **돌아올 표지를 지운다.** 막히면 물러나지 않고 그 자리에서 실패한다.
* ★ 표지를 지우지 않은 채 갈림길이 **겹겹이** 쌓이면 돌아가 볼 길이 폭발한다 — 그것이 `^(a+)+$` 다.

```text
   입력   a a a a a ... a !            패턴 ^(a+)+$

   탐욕 (a+)+     바깥 + 와 안쪽 + 가 a 들을 나눠 갖는 방법마다 다시 시도 -> 갈림길이 입력 길이에 따라 불어난다
   소유 (a++)+    안쪽이 a 를 전부 가져가고 표지를 지운다 -> 나눠 갖기를 다시 시도할 길이 없다
   원자 (?>a+)+   같다                                            -> 곧바로 실패 ('!' 때문에 $ 가 안 맞는다)
```

**비유 대응표** — 이 문서는 끝까지 이 대응을 지킨다.

| 비유 | 실체 | 확인하는 법 |
|---|---|---|
| 갈림길마다 한쪽을 먼저 가 보는 탐험가 | **백트래킹 엔진** — 파이썬 `re` | 폭발 격자의 `no (exit 124)` |
| 돌아올 표지 | 되돌이 지점(백트래킹 지점) | 문서가 *"stack points"* 라고 부른다 |
| 표지를 지우고 가기 | 소유 수량자·원자 그룹 | `a*+a` 가 `'aaaa'` 에 `None` |
| 끝에 줄바꿈이 있어도 「끝」이라고 봐 주기 | `$` | `re.match(r'\d+$', '123\n')` 이 맞는다 |
| 정말 마지막 글자 뒤 | `\Z` · `fullmatch` | 같은 입력에 `None` |
| 지도를 한 번 그려 두고 다시 쓰기 | 컴파일 캐시 | 두 번 `compile` 해도 **같은 객체** |

**똑같은 구조다** — 실무에서 이게 물리는 자리도 굳어 있다.\
「**입력 검증을 `re.match(r'\d+$', s)` 로 했는데 끝에 줄바꿈이 붙은 값이 통과했다**」와
「**사용자 입력이 길어지자 정규식 한 줄에서 요청이 멈췄다**」가 그것이다.\
앞엣것은 **`$` 가 끝 줄바꿈 앞에서도 맞는 것**이고, 뒤엣것은 **겹친 수량자에 표지가 쌓인 것**이다.

> **정규식(regular expression)** — 글자열의 **모양**을 적는 작은 언어.\
> 예: `\d+` 는 「숫자가 하나 이상」이라는 모양이다.

> **백트래킹(backtracking)** — 한 갈래가 실패하면 마지막 갈림길로 돌아가 다른 갈래를 시도하는 것.\
> 예: `a*a` 는 `a*` 가 네 개를 다 먹은 뒤, 마지막 `a` 를 맞추려고 하나를 **도로 내놓는다.**

### ★★ 이 주제가 쓰는 창 / 부적용인 창

**본체는 ④ 「판 격자」다** — 같은 탐침을 `python3.11` 과 `python3` 에 던져 **두 판이 갈린 행을 스크립트가 센다**(`7 / 15`).
그리고 ③ **치환 격자**가 [JS 28번](../../../js/syntax/28-string-methods-and-template-literals/2-summary.md)의 `$` 격자와 **같은 행**으로 두 언어를 견준다.

| 창 | 무엇을 말해 주나 | 못 보는 것 |
|---|---|---|
| ① **매치 결과·`span`** | 무엇이 **어디서 어디까지** 맞았나 | 엔진이 걸은 길 |
| ② ★ **`warnings.catch_warnings(record=True)` + `compile()`** | 소스 글자가 **어떤 경고**를 내나 — stdout 으로 | 기본 필터에서 **보이나** — 그건 ④의 마지막 행이 따로 물었다 |
| ③ ★★ **치환 격자**(템플릿 × 패턴 4종) | 템플릿의 어느 칸이 **채워지나 · 에러인가** | — |
| ④ ★★★ **판 격자**(3.11 대 3.12) | 문법·경고·캐시 정책이 **몇 판부터** | 3.13 이후 |
| ⑤ ★★ **`timeout 2` 참/거짓** | 폭발 입력에서 **끝나나** | ★★ 시간 · 되돌이 수 |
| ⑥ ★ **`is` 로 캐시 적중 세기** | 캐시에서 **같은 객체가 돌아왔나** | 캐시의 **크기** — 구현이라 문서가 약속하지 않는다 |
| ★ **제5의 상태 — 창을 바꿔 물었다** | 「폭발하나」를 **시간이 아니라 끝났나/안 끝났나**로 | [JS 30번](../../../js/syntax/30-regexp-advanced/2-summary.md)은 V8 의 **되돌이 계수기**라는 둘째 창이 있었다 — **파이썬 `re` 에는 그런 계수기가 없어** 참/거짓만으로 답했다 |
| ★ **부적용인 창** — 시간 | — | 「`re.compile` 을 쓰면 빨라진다」·「`(?>…)` 가 몇 배 빠르다」를 **한 번도 재지 않았다** |

★★ **④가 이 주제의 네 번째 창이다.** 매치 결과(①)만 보면 3.11 과 3.12 는 **`a++` 까지 한 글자도 같다.**
**판을 나란히 놓아야** 「같은 소스가 한 판에서는 **조용하고** 다른 판에서는 **경고를 찍는다**」가 드러난다.

## 이 주제가 답하려는 질문

1. ★★★ **`match`·`search`·`fullmatch` 와 `$`·`\Z` 는 「끝」을 어떻게 보나** — `'123\n'` 은 어느 조합에서 통과하나.
2. ★★★ **백트래킹을 끊는 문법은 무엇이고 몇 판부터 있나** — 그것으로 고친 패턴이 폭발 입력에서 **끝나나**.
3. ★★ **치환 템플릿은 무엇을 채우고 무엇에서 에러를 내나** — JS 의 `$` 와 어디가 다르며, 무효 이스케이프 경고는 판마다 어떻게 다른가.

★ 둘째가 이 주제의 인출 목표다.
**「탐욕은 물러나고, 소유는 물러나지 않는다 — 겹친 탐욕이 물러날 길을 폭발시킨다」는 한 문장으로 폭발과 그 처방을 함께 설명할 수 있는 것**이 아는 것과 들은 것의 경계다.

## 동작 방식

> 이 절이 본문이다. 그림이 먼저 오고 문장이 그 그림을 읽어 준다.

### 1. ★★★ 「끝」을 보는 네 가지 — `$` 는 끝 줄바꿈 앞에서도 맞는다

**언제 쓰나** — 입력 **전체가** 모양에 맞는지 검증할 때.

```text
   입력 '123\n'   =  1  2  3  \n
                     0  1  2  3  4        <- 위치

   $        위치 3 (줄바꿈 바로 앞)   과 위치 4 (끝)   둘 다에서 맞는다
   \Z       위치 4 에서만
   fullmatch                               「0 부터 4 까지 전부」를 요구 -> \n 이 남아 실패

   re.match(r'\d+$', '123\n')   -> '123'@0-3   ★ 통과
   re.fullmatch(r'\d+', ...)    -> None
```

[JS 29번](../../../js/syntax/29-regexp-basics/2-summary.md) 동작 (8)이 이미 `'xa'` 에 세 함수를 던져 「**`match` 는 앞에서만 · `search` 는 어디서나 · `fullmatch` 는 전체**」를 보였다. 여기서는 그 위에 **끝 쪽** — `$`·`\Z`·`MULTILINE` — 을 얹는다.

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

그림 해설.

* ★★★ **`match \d+$` 가 `'123\n'` 에 `'123'@0-3`** — 끝에 줄바꿈이 **남았는데** 통과했다. 문서가 `$` 를 *"the end of the string or just before the newline at the end of the string"* 으로 정의하기 때문이다.
* ★★★ **`match \d+\Z` 와 `fullmatch \d+` 는 같은 입력에 `None`** — 이 둘이 「정말 끝」이다. 마지막 줄 **`differing inputs: 1 / 3`** 이 그 차이를 센다(`'123\n'` 한 칸).
* ★★ **`search \d+$` 는 `'12\n34'` 에서 `'34'@3-5`**, **`MULTILINE` 을 켜면 `'12'@0-2`** — `M` 에서 `$` 는 **줄마다의 끝**이다.
* ★ **`match ^34 M` 은 전부 `None`** — 문서: *"even in `MULTILINE` mode, `re.match` will only match at the beginning of the string and not at the beginning of each line."* `^` 에 `M` 을 줘도 `match` 는 **문자열 맨 앞**에서만 시작한다.

**비용** — 없다. 고르는 법만 있다 — **검증은 `fullmatch`**(또는 `\Z`), **찾기는 `search`**.

### 2. ★★ 탐욕 · 게으름 · 소유 — 물러나는 방향

**언제 쓰나** — `.*` 가 **너무 많이** 먹었을 때. 그리고 되돌이를 **아예 막고** 싶을 때.

```text
   '<a><b></b></a>' 에 <.*>                    <.*?>                     <[^>]*>
   .* 가 끝까지 먹고 > 를 찾아 물러난다         .*? 가 0 개부터 늘려 간다       > 가 아닌 것만 먹는다
   -> 마지막 > 에서 멈춘다 (한 덩어리)          -> 첫 > 에서 멈춘다 (넷)        -> 되돌이 없이 넷

   'aaaa' 에 a*a       a* 가 넷을 먹는다 -> 마지막 a 가 없다 -> 하나 내놓는다 -> 맞는다
             a*+a      a*+ 가 넷을 먹고 표지를 지운다 -> 마지막 a 가 없다 -> 내놓을 수 없다 -> None
```

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

그림 해설.

* ★★ **`[1]` 대 `[2]`** — 탐욕은 **한 덩어리**, 게으름은 **넷**. 문서가 드는 예 그대로다(*"`<.*>` … will match the entire string"*).
* ★ **`[3]` `<[^>]*>`** — 게으름과 **같은 넷**인데 **물러날 일 자체가 없다.** 「무엇이 **아닌** 것」으로 적으면 탐욕·게으름을 고를 필요가 없다.
* ★★ **`[4]` 대 `[5]`** — 따옴표 안을 뽑을 때 탐욕 `"(.*)"` 은 **`'x" v="y'`** 를 낸다. 첫 따옴표부터 **마지막** 따옴표까지다.
* ★★★ **`[6]` 대 `[7]`** — `a*a` 는 맞고 **`a*+a` 는 `None`**. 문서의 예 그대로다 — *"when `a*+a` is used to match `'aaaa'` … the expression cannot be backtracked and will thus fail to match."*
* ★ **`[8]`** — `{m,n}+` 도 소유다. `a{3,5}aa` 는 맞고 `a{3,5}+aa` 는 `None`(문서의 예).
* ★ **`[9]`** — `.` 은 기본으로 **줄바꿈을 안 먹는다.** `re.S`(`DOTALL`)를 줘야 `'a\nc'` 까지 잡는다.

**비용** — 소유·원자는 **답을 바꾼다**(`[7]`). 「더 빠른 탐욕」이 아니라 **다른 패턴**이다 — 되돌이가 있어야 맞는 입력에서는 실패한다.

### 3. ★★ 그룹 — 번호·이름·참여 안 한 그룹

**언제 쓰나** — 매치에서 **조각**을 꺼낼 때.

```text
   (?P<y>\d{4})-(?P<m>\d\d)(-(?P<d>\d\d))?      on 'on 2026-09 ok'
     그룹 1 = y     그룹 2 = m   그룹 3  그룹 4 = d
                                 └── ? 때문에 통째로 건너뛴다 -> 3 과 4 는 None (참여 안 함)

   (\w)+  on 'abc'   반복 안의 그룹은 마지막 한 바퀴만 남는다 -> 'c'
```

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

그림 해설.

* ★★ **`[2]` `groups()` 의 `None`** — 참여 안 한 그룹은 **`None`** 이다. **`[3]` `groups('')`** 로 기본값을 바꿀 수 있다. **`[5]` `span('d')`** 는 **`(-1, -1)`**.
* ★★ **`[7]` `findall`** 은 참여 안 한 그룹을 **`''`** 로 준다 — `match.groups()` 의 `None` 과 **다르다.** [JS 29번](../../../js/syntax/29-regexp-basics/2-summary.md) 동작 (8)이 같은 차이를 JS 의 `undefined` 와 견줬다.
* ★ **`[6]`** — 반복 안의 그룹은 **마지막 값 `'c'`** 만 남는다.
* ★★ **`[8]` 치환에서 참여 안 한 그룹은 `''`** — 문서: *"versionchanged 3.5: Unmatched groups are replaced with an empty string."* 그 전에는 에러였다.
* ★ **`[9]`** — `split` 에 **캡처 그룹**을 넣으면 **구분자도 결과에 들어간다.** **`[10]`** — 빈 매치(`\b`)로도 쪼갠다. [07번](../07-string-methods/2-summary.md)이 「`re.split` 은 빈 매치에서 3.7 부터 동작이 바뀌었다」고 넘긴 자리다. **`[11]`** 은 문서의 예 그대로다(`'-a-b--d-'`).

**비용** — 명명 그룹은 글자가 늘지만 **번호가 바뀌어도 안 깨진다.** 이름 문법은 **`(?P<n>…)`** 다 — JS 의 `(?<n>…)` 는 파이썬에서 `unknown extension`([JS 30번](../../../js/syntax/30-regexp-advanced/2-summary.md) 동작 (9)).

### 4. ★★★ 치환 격자 — JS 의 `$` 격자와 같은 행으로

**언제 쓰나** — `re.sub` 의 둘째 인자에 **찾은 글자·그룹**을 끼워 넣을 때. 그리고 **바깥에서 온 문자열**을 넣을 때.

```text
   템플릿이 읽히는 법                       JS  replace (28번)             Python  re.sub
   찾은 글자 전체                          $&                            \g<0>
   그룹 1                                  $1                            \1  또는 \g<1>
   그룹 1 뒤에 글자 0                       $10 (그룹 10 이 없으면 $1 + 0)   \g<1>0   (\10 은 그룹 10 -> 없으면 에러)
   명명 그룹                                $<g>                          \g<g>
   ★ 없는 그룹                              글자 그대로 남는다              ★ 에러
   $                                       $$ 가 $ 하나                   $ 는 아무 뜻이 없다
```

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

그림 해설.

* ★★★ **`[$&]` 는 네 열 전부 `'a[$&]c'`** — 파이썬 템플릿에서 **`$` 는 아무 뜻이 없다.** 찾은 글자는 **`\g<0>`** 이다.
* ★★★ **없는 그룹은 에러다** — `escape('b')`(그룹 없음)에 `\1` 은 **`error: invalid group reference 1`**, `\g<x>` 는 **`IndexError: unknown group name 'x'`**.
  JS 28번 격자에서는 같은 자리가 **글자 그대로** 남았다(`"a[$1]c"`) — **JS 는 조용히, 파이썬은 시끄럽게**다.
* ★★ **`\10` 은 그룹 10** — 그룹이 하나뿐이면 에러다. 「그룹 1 뒤에 `0`」은 **`\g<1>0`**(→ `'a[b0]c'`). 문서가 이 모호함을 직접 적는다.
* ★★ **`\n` 은 줄바꿈으로 바뀌고 `\q` 는 에러** — `repl` 의 알 수 없는 `\` + ASCII 글자는 **3.7 부터 에러**다(문서). **`\0` 은 `'\x00'`** — 8진 이스케이프로 읽힌다(그룹 0 이 아니다).
* ★★★ **넷째 열(함수)은 전부 템플릿 글자 그대로** — 함수가 돌려준 문자열은 **템플릿으로 읽지 않는다.** 바깥에서 온 글자를 넣을 때의 처방이 이것이다(JS 28번의 `() => price` 와 같은 처방).
* ★★ 마지막 줄 — **`36 / 52`** 칸이 템플릿 글자와 달랐고 그중 **에러 19**. 마지막 행(아라비아 숫자 `U+0661` 을 그룹 번호로)은 동작 5 에서 판이 갈린다.

같은 소스를 `python3.11` 에 던지면 **마지막 행만** 달라진다.

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

* ★★★ **3.11 은 `\g<U+0661>` 을 그룹 1 로 받아 `'a[b]c'` 를 내고 `DeprecationWarning`**(`W1`·`W2`)만 낸다. 3.12 는 **`bad character in group name`** 에러 — 문서의 *"versionchanged 3.12: Group id can only contain ASCII digits."*
  그래서 에러 칸이 **17 → 19**, 경고 칸이 **2 → 0**.

**비용** — 치환 템플릿은 **작은 언어 하나 더**다. 바깥 글자를 넣을 거면 **함수로 감싸거나** `\` 만 두 배로 만든다 — 문서: *"only backslashes should be escaped"*.

### 5. ★★★ 판 격자 — 3.11 대 3.12 (이 주제의 본체)

**언제 쓰나** — 「이 문법이 몇 판부터 되나」·「이 경고는 왜 3.12 에서 처음 보이나」를 물을 때.

```text
   같은 탐침 e46_vprobe.py        ──python3.11──▶  label;value  ─┐
                                 ──python3   ──▶  label;value  ─┴─▶ 나란히 놓고 갈린 행에 * , 마지막 줄 N / M
   + 한 행은 기본 경고 필터에 물었다  printf '…re.compile("\d+")' | python - 2>&1 >/dev/null   (stderr 만 남긴다)
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

그림 해설.

* ★★★ **`rows where the two versions differ: 7 / 15`.**
* ★★★ **소유 수량자·원자 그룹은 두 판 다 된다** — 윗 네 행이 같다. 문서의 *"versionadded 3.11"* 그대로다.
  ★ [JS 30번](../../../js/syntax/30-regexp-advanced/2-summary.md) 동작 (9)는 12패턴 격자에서 「`a++`·`(?>…)` 는 **파이썬 3.12 만** 받았다」고 적었다 — 그 격자의 비교 대상은 **V8·RE2·파이썬 세 엔진**이었고, **파이썬 판은 3.12 하나**였다. 판으로 물으면 **3.11 도 받는다.**
* ★★★ **무효 이스케이프 네 행이 `DeprecationWarning` → `SyntaxWarning`** — `"\d+"`·`"\."`·`b"\d"`·`"\477"`. ★ **정규식에서 유효한 `\d` 도 문자열 리터럴에서는 무효**다 — 경고는 `re` 가 아니라 **파서**가 낸다.
  **`r"\d+"` 와 `"\\d+"` 는 두 판 다 경고 없음** — 처방은 raw 문자열이다.
* ★★★ **마지막 행 — 기본 필터에서 보이나.** 3.11 은 **`no (stderr empty)`**, 3.12 는 **`<stdin>:2: SyntaxWarning: invalid escape sequence '\d'`**.
  같은 경고 **종류의 차이**가 「**3.11 에서는 조용했다**」로 나타난다 — `DeprecationWarning` 은 기본 필터가 대부분 숨긴다. **3.12 로 올리자 경고가 쏟아지는 이유**가 이 한 행이다.
* ★★ **`\g<U+0661>`** — 동작 4 의 마지막 행. 3.11 은 받고 3.12 는 에러.
* ★★★ **캐시 정책이 갈렸다** — 캐시를 비우고 `p0` 를 컴파일 → 상한(`re._MAXCACHE`)까지 채움 → **`p0` 를 한 번 더 부름** → 새 패턴 하나. 그 뒤 `p0` 가 **같은 객체인가**가 3.11 `False`, 3.12 `True`.
  즉 **3.11 은 먼저 들어온 것부터 버리고, 3.12 는 최근에 쓴 것을 남긴다.** 설치본 소스(`re/__init__.py`)의 주석도 3.12 에 *"`_cache` uses the LRU policy"* 를 적는다.
  ★ **이것은 구현이다** — 문서는 *"most recent patterns … are cached"* 까지만 말하고 크기도 정책도 약속하지 않는다. 판이 오르면 **또 바뀌어도 된다.**
* ★ 예외 클래스 이름은 두 판 다 `error` 다.

**비용** — 판 경계는 **조용하게** 넘어온다. 3.11 코드베이스에 raw 문자열이 빠진 곳이 있어도 **아무 말이 없다가** 3.12 에서 경고로 드러난다.

### 6. ★★★ 폭발 입력 — 소유·원자로 고친 패턴은 끝나나

**언제 쓰나** — 「사용자 입력에 정규식을 거는데 **길이 제한이 없다**」일 때.

[JS 30번](../../../js/syntax/30-regexp-advanced/2-summary.md) 동작 (7)이 `^(a+)+$` 에 `'a' * n + '!'` 를 **node18·node20·파이썬 `re`·Go RE2** 로 던져 「**백트래킹 엔진 셋은 `n = 20` 까지 끝났고 `n = 30` 부터 2초 안에 안 끝났다**」를 이미 보였다. 그 격자가 정본이다.
여기서는 **파이썬에만 있는 처방** — 소유 수량자·원자 그룹 — 이 **같은 입력에서 끝나는지**만 묻는다. 대조로 `^(a+)+$` 는 **한 칸**(3.12 · `n = 30`)만 둔다.

```text
   ^(a+)+$     'aaa…a!'   안쪽 + 가 a 몇 개를 먹을지 × 바깥 + 가 몇 바퀴 돌지 -> 나누는 방법이 전부 되돌이 후보
   ^(a++)+$    'aaa…a!'   안쪽이 전부 먹고 표지를 지운다 -> 바깥 + 가 둘째 바퀴를 못 돈다 -> $ 가 '!' 앞에서 실패 -> 끝
   ^(?>a+)+$   같다
```

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

그림 해설.

* ★★★ **`finished within 2s: 12 / 13`** — 끝나지 않은 한 칸은 **대조 칸 `^(a+)+$`**(`n = 30`)뿐이다(`exit 124` 는 `timeout` 이 죽였다는 뜻).
* ★★★ **`^(a++)+$`·`^(?>a+)+$` 는 `n = 100000` 에서도 끝났다** — 두 판 모두. **답도 맞다** — `!` 가 붙으면 `False`, 안 붙으면 `True` 로, 원래 패턴이 **답해야 할 값**과 같다.
* ★★ **경과 시간은 이 블록 어디에도 없다.** 「몇 배 빨라졌다」를 주장하지 않는다 — 「**끝나는가**」만이 근거다.
* ★ **처방이 늘 이렇게 쉽지는 않다** — 이 패턴은 안쪽이 **전부 먹어도 답이 같아서** 소유로 바꿀 수 있었다. 동작 2 의 `a*+a` 처럼 **되돌이가 있어야 맞는 패턴**은 소유로 바꾸면 **답이 바뀐다.** 가장 확실한 처방은 **겹친 수량자를 없애는 것**(`^a+$`)이다.

**비용** — 파이썬 `re` 에는 **선형 시간 보장이 없다.** JS 30번이 보인 대로 Go RE2 는 그 보장을 **역참조·둘러보기를 버리고** 샀다. 파이썬은 둘 다 갖는 대신 **패턴을 짜는 사람이 되돌이를 끊어야** 한다.

### 7. ★★ 컴파일 캐시 — 같은 객체가 돌아온다

**언제 쓰나** — 「`re.compile` 을 꼭 해 둬야 하나」를 물을 때.

```text
   re.search(r'x\d', s) ─┐
   re.compile(r'x\d')   ─┴─▶  (타입, 패턴 글자, 플래그) 로 캐시를 찾는다 ─ 있으면 ─▶ 그 객체
                                                                      └ 없으면 ─▶ 컴파일해서 넣는다
   키가 다르면 다른 칸:  r'\d+'  ≠  r'\d+' + re.I  ≠  rb'\d+'
```

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

그림 해설.

* ★★ **`[1]` 두 번 `compile` 하면 같은 객체**(`True`), **`[2]`·`[3]` 플래그나 타입이 다르면 다른 객체** — 키가 **(타입, 글자, 플래그)** 다.
* ★★ **`[4]` 모듈 수준 함수(`re.search`)도 같은 캐시를 쓴다** — 문서: *"`re.compile` and the module-level matching functions are cached"*.
* ★ **`[6]` `re.purge()` 뒤에는 새 객체**(`False`). **`[5]`** 이미 컴파일된 객체를 주면 **그 객체를 그대로** 돌려준다.
* ★★ **`[7]` 패턴 객체에는 상태가 없다** — 같은 객체로 `pos` 0·2·0 을 주면 `(1, 2)`·`(3, 4)`·`(1, 2)`. JS `g` 정규식의 `lastIndex` 같은 **책갈피가 없다**([JS 29번](../../../js/syntax/29-regexp-basics/2-summary.md) 동작 (8)).
* ★ **`[8]` 적중 `6 / 6`** — 세 패턴을 세 바퀴 돌려 **첫 컴파일과 같은 객체가 돌아온 횟수**를 셌다. ★ **시간은 안 쟀다.**

**비용** — 캐시는 **상한이 있다**(동작 5 — 넘치면 버린다, **어떤 것을 버리는지는 판마다 다르다**). 패턴을 수백 개 번갈아 쓰는 코드는 **캐시에 기대지 말고** `compile` 한 객체를 들고 있는 편이 **동작이 판에 안 매인다.** 「빠르다」는 이 문서가 잰 적이 없다.

### 8. ★★ `str` 과 `bytes` · `\d` 가 뜻하는 것 · `re.escape`

**언제 쓰나** — 파일·소켓에서 읽은 `bytes` 에 정규식을 걸 때. 그리고 **사용자 입력을 패턴에 넣을 때.**

```text
   str 패턴  ──✗──  bytes 입력            TypeError (섞을 수 없다 — 문서)
   bytes 패턴 ──✗── str 입력              TypeError

   \d on str    '0'..'9'  + 아라비아 숫자 ١٢٣ 같은 「유니코드 10진 숫자」 전부
   \d on bytes  '0'..'9'  만                 (re.ASCII 를 주면 str 도 이쪽)
```

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

그림 해설.

* ★★ **`[1]`** — `str` 패턴에 `bytes` 입력은 **`cannot use a string pattern on a bytes-like object`**, 반대도 대칭이다. [06번](../06-strings-bytes-unicode/2-summary.md)이 이 주제로 넘긴 자리다.
  ★ `re.sub(rb'1', '2', b'a1')` 처럼 **치환 문자열만** 타입이 다르면 문구가 `sequence item 1: expected a bytes-like object, str found` 로 **원인을 바로 말하지 않는다.**
* ★★★ **`[2]` `\d+` 가 아라비아-인도 숫자 `U+0661 U+0662 U+0663` 에 `True`** — 문서: *"Matches any Unicode decimal digit … and also many other digit characters."* **`re.ASCII` 를 주면 `False`.**
  ★ `int()` 도 그 글자를 **`123`** 으로 읽는다 — 「`\d+` 로 검증했으니 ASCII 숫자다」는 틀린 전제다.
* ★ `\w` 도 같다 — `str` 에서는 한글이 **글자**(`True`), UTF-8 `bytes` 에서는 **아니다**(`False`).
* ★★ **`[3]` `re.escape`** — 일곱 표본 전부 **자기 자신에 다시 맞았다**(`7 / 7`). 한글·`=` 처럼 **특수하지 않은 글자는 그대로** 둔다(문서 — 3.7 부터 *"Only characters that can have special meaning in a regular expression are escaped"*).
  이스케이프 안 한 `'('` 는 **`error: missing ), unterminated subpattern`**.
* ★★ **치환 쪽에는 `re.escape` 를 쓰지 마라** — `re.sub('x', re.escape('a.b'), 'x')` 가 **`'a\\.b'`**(역슬래시가 결과에 남았다). 문서가 직접 금지한다. 함수로 감싸면 글자 그대로다.

* ★★★ **`[4]` 유효한 이스케이프는 경고도 없이 뜻이 바뀐다** — `"\bcat\b"` 는 **길이 5**(`\b` 가 백스페이스 한 글자)이고 `'a cat'` 에 **`None`**. raw 문자열이면 단어 경계가 되어 `(2, 5)`.
  동작 5 의 판 격자가 **경고로 잡아 주는 것은 무효 이스케이프뿐**이다 — 이쪽은 3.12 도 조용하다.

**비용** — `str` 패턴의 `\d`·`\w` 는 **유니코드 전체**라 입력 검증에는 **넓다.** 검증이면 `[0-9]` 또는 `re.ASCII`.

## 문법 — 형태와 규칙

```text
   raw 문자열            r"\d+\.\d+"         파이썬 파서가 \ 를 안 건드린다 -> 정규식 엔진이 \d 를 받는다
   세 함수               re.match / re.search / re.fullmatch   (앞에서만 / 어디서나 / 전체)
   끝                    $ (끝 줄바꿈 앞도)   \Z (정말 끝)   MULTILINE 이면 ^ $ 가 줄마다
   수량자                *  +  ?  {m,n}      탐욕
                        *? +? ?? {m,n}?     게으름
                        *+ ++ ?+ {m,n}+     소유          (3.11+)
   원자 그룹             (?>…)                              (3.11+)
   그룹                  (…) 번호 · (?:…) 캡처 안 함 · (?P<n>…) 이름
   치환 템플릿            \g<0> 전체 · \1 · \g<1> · \g<n> 이름 · \\ 역슬래시 하나
   플래그                re.I  re.M  re.S  re.A  re.X     (| 로 묶는다)
```

규칙.

* ★★★ **패턴은 raw 문자열로 쓴다** — 아니면 파서가 먼저 `\` 를 읽는다. `"\d"` 는 3.12 에서 `SyntaxWarning`, `"\b"` 는 **경고 없이** 백스페이스 한 글자가 된다(유효한 이스케이프라서 — 동작 8 의 `[4]`).
* ★★ **명명 그룹은 `(?P<n>…)`** 다. 이름 참조는 패턴 안에서 `(?P=n)`, 치환에서 `\g<n>`.
* ★ 컴파일이 안 되는 형태는 표로만 적는다(동작 2·8 의 블록이 실제 에러를 싣는다).

| 쓴 꼴 | 결과 | 어느 절 |
|---|---|---|
| `re.compile("(")` | `error: missing ), unterminated subpattern` | 동작 8 |
| `re.compile("(?<n>a)")` | `unknown extension ?<n`([JS 30번](../../../js/syntax/30-regexp-advanced/2-summary.md) 동작 (9)) | 동작 3 |
| `re.compile(r"(?<=a+)b")` | `look-behind requires fixed-width pattern`(JS 30번 동작 (9)) | — |
| 치환의 `\q` | `error: bad escape \q` | 동작 4 |
| 치환의 `\g<x>`(없는 이름) | `IndexError: unknown group name 'x'` | 동작 4 |

## 어디서 틀리나

### (1) ★★★ `re.match(r'…$', s)` 로 입력 전체를 검증한다

끝에 줄바꿈이 붙은 값이 **통과한다**(동작 1 — `'123\n'` 이 `'123'@0-3`). **`fullmatch`** 또는 **`\Z`** 를 쓴다.

### (2) ★★★ raw 문자열 없이 패턴을 쓴다

3.11 까지는 **아무 말이 없었다** — 경고가 `DeprecationWarning` 이라 기본 필터가 숨겼다(동작 5 마지막 행). 3.12 에서 `SyntaxWarning` 으로 보이기 시작한다. ★ 더 나쁜 것은 **유효한 이스케이프**(`"\b"`)다 — 경고 없이 **다른 글자**가 된다.

### (3) ★★★ 사용자 입력에 겹친 수량자를 건다

`^(a+)+$` 꼴은 **두 자릿수 길이**에서 이미 안 끝난다(JS 30번 · 동작 6 의 대조 칸). **겹친 수량자를 없애거나**, 답이 같을 때만 **소유·원자**로 바꾼다.

### (4) ★★ 소유 수량자를 「빠른 탐욕」으로 안다

**답이 바뀐다** — `a*+a` 는 `'aaaa'` 에 `None`(동작 2). 되돌이가 있어야 맞는 패턴에는 못 쓴다.

### (5) ★★ JS 의 `$&`·`$1` 을 그대로 옮긴다

파이썬 템플릿에서 `$` 는 **아무 뜻이 없다**(동작 4 — 네 열 전부 `'a[$&]c'`). 찾은 글자는 `\g<0>`.

### (6) ★★ 「그룹 1 뒤에 0」을 `\10` 으로 적는다

`\10` 은 **그룹 10** 이다 — 없으면 에러. `\g<1>0` 으로 적는다.

### (7) ★★ 바깥에서 온 글자를 치환 템플릿에 넣는다

`\` 가 섞이면 해석되거나 에러가 난다. **함수로 감싼다**(동작 4 넷째 열). `re.escape` 는 **치환 쪽 처방이 아니다**(동작 8).

### (8) ★★ `\d` 로 「ASCII 숫자」를 검증한다

`str` 패턴의 `\d` 는 **유니코드 10진 숫자 전부**다(동작 8). `[0-9]` 또는 `re.ASCII`.

### (9) ★ `str` 패턴을 `bytes` 에 건다

`TypeError` — 섞을 수 없다(동작 8). 파일을 `rb` 로 읽었다면 패턴도 `rb"…"` 다.

### (10) ★ 캐시가 있으니 `compile` 은 쓸모없다고 믿는다 · 또는 반대로 「`compile` 하면 빠르다」고 적는다

캐시에는 **상한과 정책**이 있고 **판마다 다르다**(동작 5). 속도는 **이 문서가 잰 적이 없다** — 어느 쪽 주장도 이 문서로는 못 한다.

## 구현 세부사항 대 언어 보장

세 층으로 가른다 — **라이브러리 보장**(문서가 약속한 것) · **CPython 구현**(설치본 소스가 그렇게 하는 것) · **이 판의 관찰**(돌려 보니 그랬다).

### 라이브러리 보장

| 사실 | 근거 |
|---|---|
| `$` 는 **끝 줄바꿈 바로 앞**에서도 맞는다 · `\Z` 는 끝에서만 | `$`·`\Z` 절 |
| 소유 수량자·원자 그룹은 **3.11+** · 되돌이를 허용하지 않는다 | 수량자 절 · What's New 3.11 |
| 무효 이스케이프는 3.12 에서 `SyntaxWarning`(3.11 까지 `DeprecationWarning`) | What's New 3.12 · 어휘 분석 |
| `str`·`bytes` 는 **섞을 수 없다** | 모듈 첫머리 |
| `str` 패턴의 `\d` 는 **유니코드 10진 숫자 전부** · `re.ASCII` 면 `[0-9]` | `\d` 절 |
| 치환 — `\g<0>` · `\g<2>0` · 참여 안 한 그룹은 `''`(3.5) · 알 수 없는 `\`+글자는 에러(3.7) · 그룹 번호는 ASCII 숫자만(3.12) | `sub` 절 |
| **최근 패턴은 캐시된다** | `compile` 절의 note |
| `re.escape` 결과를 **치환 문자열에 쓰지 마라** | `escape` 절 |

### CPython 구현 세부사항

* ★★ **캐시의 크기와 정책** — 설치본 `re/__init__.py` 에 `_MAXCACHE = 512` 가 있고, 3.12 는 `_cache`(LRU)와 `_cache2`(FIFO) **두 층**, 3.11 은 한 층이다. **문서에 없다** — 동작 5 의 `False`/`True` 가 판마다 다른 것이 그 증거다.
* ★ 캐시 키가 **(타입, 패턴, 플래그)** 인 것 — 소스의 `key = (type(pattern), pattern, flags)`. 동작 7 의 `[2]`·`[3]` 은 그것의 관찰이다.
* ★ 엔진이 **백트래킹**이라는 것 — 문서가 수량자·원자 그룹을 **되돌이 지점**(*"stack points"*)으로 설명하니 사실상 문서도 전제하지만, **시간 복잡도는 약속하지 않는다.**
* 예외·경고 **문구 전부**(`invalid group reference 1 at position 2` · `bad character in group name` · `cannot use a string pattern on a bytes-like object`).

### 이 판(3.12.3)의 관찰

* 폭발 격자의 **`n = 30` 에서 2초 안에 안 끝남** — 머신·제한 시간에 달린다. 결론은 경계 값이 아니라 「**소유·원자로 고치면 `n = 100000` 도 끝났다**」는 쪽이다.
* **`re.sub(rb'1', '2', b'a1')` 의 문구**가 타입 불일치를 직접 말하지 않는 것.
* 3.11 이 `\g<U+0661>` 을 **그룹 1 로 읽은 것**(경고만) — 3.12 에서 사라졌다.

### 그래서 이렇게 적으면 틀린다

* ✗ 「`$` 는 문자열 끝이다」 → ○ 「**끝, 또는 끝 줄바꿈 바로 앞**이다 — 정말 끝은 `\Z`·`fullmatch`」
* ✗ 「소유 수량자는 3.12 부터」 → ○ 「**3.11 부터**」(두 판에 던져 같았다 — JS 30번의 「3.12 만」은 판이 아니라 **엔진** 비교였다)
* ✗ 「`\d` 는 3.12 부터 에러」 → ○ 「**문자열 리터럴의** `\d` 가 3.12 부터 `SyntaxWarning`, 에러는 **미래**」
* ✗ 「`re` 는 패턴 512개를 캐시한다」 → ○ 「최근 패턴을 캐시한다(문서) — 512 는 CPython 의 값」
* ✗ 「`re.compile` 을 쓰면 빠르다」 → ○ 이 문서는 **적중만 셌다**(동작 7 `6 / 6`)

## 언제 쓰고 언제 안 쓰나

| 상황 | 고를 것 |
|---|---|
| 고정된 글자 찾기·자르기·바꾸기 | **문자열 메서드**([07번](../07-string-methods/2-summary.md) — 정규식을 꺼내는 선이 그쪽 표다) |
| 입력 **전체**가 모양에 맞나 | `re.fullmatch`(또는 `\Z`) |
| 어딘가에 있나 | `re.search` |
| 여러 개를 뽑는다 | `re.finditer`(매치 객체) · `re.findall`(그룹이 있으면 그룹) |
| 찾은 것을 살려 바꾼다 | `re.sub` + `\g<0>`·`\g<n>` — 바깥 글자면 **함수** |
| 사용자 입력을 **패턴 안의 글자로** | `re.escape` |
| 길이 제한 없는 입력에 겹친 반복 | 쓰지 않는다 — 패턴을 다시 짜거나 소유·원자 |
| 중첩 괄호·HTML 파싱 | 정규식이 아니라 파서 |

## 핵심 문장

1. ★★★ **`$` 는 끝 줄바꿈 앞에서도 맞는다** — 검증은 `fullmatch`(`differing inputs: 1 / 3`).
2. ★★★ **탐욕은 물러나고 소유는 안 물러난다** — `a*+a` 는 `'aaaa'` 에 `None`. 겹친 탐욕 `^(a+)+$` 는 `n = 30` 에서 안 끝났고, 소유·원자판은 `n = 100000` 도 끝났다(`12 / 13`).
3. ★★★ **3.11 대 3.12 는 `7 / 15` 행이 갈렸다** — 소유·원자는 **3.11 부터 같고**, 무효 이스케이프가 `DeprecationWarning` → `SyntaxWarning` 이 되어 **3.12 에서 처음 보인다.**
4. ★★ **파이썬 치환 템플릿에서 `$` 는 뜻이 없고, 없는 그룹은 에러다** — JS 는 글자 그대로 둔다.
5. ★ **캐시는 같은 객체를 돌려주지만 크기·정책은 구현**이다 — 판마다 달랐다.

## 관련 자료

* 목록: [python/syntax 주제 목록](../README.md) — 이 주제는 **46번**
* 선행: [06-strings-bytes-unicode](../06-strings-bytes-unicode/2-summary.md) — `str`/`bytes` 의 정본.\
  **경계**: 두 타입의 차이는 그쪽, **정규식에서 섞이지 않는 것**과 `\d`·`\w` 의 범위는 여기.
* 선행: [07-string-methods](../07-string-methods/2-summary.md) — **정규식을 꺼내는 선**의 정본. 「문자열 메서드로 되면 그쪽」.
* 함께 보는 곳: [02-is-vs-eq-interning](../02-is-vs-eq-interning/2-summary.md) — `SyntaxWarning` 이 **컴파일 시점** 경고라는 것.
* 알고리즘 쪽 경계: [`cs/algorithm/25-string-matching/`](../../../../../algorithm/25-string-matching/2-summary.md) — ★ **그 문서는 고정된 패턴 하나를 찾는 나이브·KMP 까지다.**
  **백트래킹 정규식 엔진·폭발을 다루는 절은 거기에 없다**(확인했다). 그래서 「엔진이 어떻게 걷나」는 이 주제와 JS 30번이 맡고, **「고정 문자열 검색의 최악을 어떻게 없애나」는 그쪽**이다.
* 다른 갈래: [JS 28번](../../../js/syntax/28-string-methods-and-template-literals/2-summary.md) — `$` 치환 격자(`20 / 44`)의 정본. 동작 4 가 같은 행으로 견줬다.
* 다른 갈래: [JS 29번](../../../js/syntax/29-regexp-basics/2-summary.md) — ★ **`match`/`search`/`fullmatch` 의 뜻 · 패턴 객체에 상태가 없는 것 · `findall` 의 `''`** 를 파이썬에 이미 던졌다. 여기서는 인용만 했다.
* 다른 갈래: [JS 30번](../../../js/syntax/30-regexp-advanced/2-summary.md) — ★★★ **백트래킹 폭발 격자(엔진 × n)와 12패턴 문법 격자의 정본.** 파이썬 `re` 는 그 격자의 **한 열**이다.\
  **경계**: 「어느 엔진이 어느 n 에서 안 끝나나」·「V8 의 되돌이 수」는 그쪽, 「**파이썬의 처방(소유·원자)이 끝나나 · 몇 판부터인가**」는 여기.
* 이어지는 곳: [45번](../45-functools/2-summary.md)(`functools`) — `re` 의 치환 템플릿 캐시가 `functools.lru_cache` 로 되어 있다(설치본 소스).
* 공식 문서: [`re`](https://docs.python.org/3.12/library/re.html) · [Regular Expression HOWTO](https://docs.python.org/3.12/howto/regex.html) · [What's New 3.11 — re](https://docs.python.org/3.12/whatsnew/3.11.html) · [What's New 3.12](https://docs.python.org/3.12/whatsnew/3.12.html)

## 용어 풀이

* **정규식(regular expression)**: 글자열의 모양을 적는 작은 언어.\
  예: `\d{4}-\d\d` 는 「숫자 넷, 하이픈, 숫자 둘」.
* **raw 문자열(raw string)**: `r"…"`. 파이썬 파서가 `\` 를 이스케이프로 읽지 않는다.\
  예: `r"\d"` 는 두 글자 `\`·`d` 다.
* **무효 이스케이프(invalid escape sequence)**: 문자열 리터럴에서 뜻이 정해지지 않은 `\` + 글자.\
  예: `"\d"` — 3.12 에서 `SyntaxWarning`.
* **백트래킹(backtracking)**: 실패하면 마지막 갈림길로 돌아가 다른 갈래를 시도하는 것.\
  예: `a*a` 가 `a` 하나를 도로 내놓는 것.
* **탐욕 수량자(greedy)**: 최대한 많이 먹고 필요하면 물러나는 수량자(`*`·`+`·`?`).\
  예: `<.*>` 가 마지막 `>` 까지.
* **게으른 수량자(non-greedy)**: 최소한만 먹고 필요하면 더 먹는 수량자(`*?`).\
  예: `<.*?>` 가 첫 `>` 까지.
* **소유 수량자(possessive)**: 최대한 먹고 **되돌이 지점을 남기지 않는** 수량자(`*+`·`++`). 3.11+.\
  예: `a*+a` 는 `'aaaa'` 에 실패한다.
* **원자 그룹(atomic group)**: `(?>…)`. 안에서 맞은 뒤 **안쪽 되돌이 지점을 버린다.** 3.11+.\
  예: `x++` 는 `(?>x+)` 와 같다(문서).
* **파국적 백트래킹(catastrophic backtracking)**: 겹친 수량자 때문에 되돌이 후보가 입력 길이에 따라 폭발하는 것.\
  예: `^(a+)+$` 에 `'a' * 30 + '!'`.
* **참여 안 한 그룹(unmatched group)**: 매치에 끼지 못한 그룹.\
  예: `groups()` 에서 `None`, `findall` 에서 `''`, 치환에서 `''`.
* **치환 템플릿(replacement template)**: `re.sub` 의 둘째 인자로 준 문자열. `\g<…>`·`\숫자` 를 읽는다.\
  예: `r"[\g<0>]"` 가 찾은 글자를 대괄호로 감싼다.
* **컴파일 캐시**: 최근에 컴파일한 패턴 객체를 모아 두는 곳.\
  예: `re.compile(p) is re.compile(p)` 가 `True`.
* **`re.ASCII`**: `\d`·`\w`·`\s` 를 ASCII 범위로 좁히는 플래그.\
  예: 아라비아-인도 숫자가 `\d` 에 안 맞게 된다.

## 더 들어가면

* ★ **치환 템플릿도 캐시된다** — 설치본 3.12 소스의 `_compile_template` 이 `@functools.lru_cache(_MAXCACHE)` 로 감싸여 있다(구현). 이 문서는 그 캐시를 재지 않았다.
* **`re.VERBOSE`(`re.X`)** — 패턴 안의 공백·`#` 주석을 무시한다. 긴 패턴을 줄마다 나눠 적을 때 쓴다. 이 문서는 재지 않았다.
* 표준 `re` 는 `\p{L}` 같은 유니코드 속성을 받지 않는다 — `bad escape \p`([JS 30번](../../../js/syntax/30-regexp-advanced/2-summary.md) 동작 (9)). 이 문서는 서드파티 모듈을 재지 않았다.
* **선형 시간이 필요하면** 파이썬 표준에는 그런 엔진이 없다 — JS 30번이 Go RE2 로 보인 것이 그 설계다.
