# python/syntax/39-match-statement — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **이 본문은 원고가 아니라 Claude 작성이다**(문법·API 갈래는 원고 없이 공식 문서로 접지한다).
>
> **기준 소스** — 열어서 확인한 것만.
> - [언어 레퍼런스 — 복합문 · `match` 문(3.12)](https://docs.python.org/3.12/reference/compound_stmts.html#the-match-statement) —
>   *"A match statement may have at most one irrefutable case block, and it must be last."* ·
>   반박 불가(irrefutable) 패턴 목록 · *"A single underscore `_` is not a capture pattern"* ·
>   값 패턴의 *"compares equal to the subject value (using the `==` equality operator)"* ·
>   *"If the subject value is an instance of `str`, `bytes` or `bytearray` the sequence pattern fails."* ·
>   `None`·`True`·`False` 는 *"the `is` operator is used"* · 클래스 패턴의 `__match_args__` 와 **내장 타입 열한 개** 문단
> - [PEP 634](https://peps.python.org/pep-0634/)(명세) · [PEP 636](https://peps.python.org/pep-0636/)(튜토리얼)
>
> **실행 검증** — 이 문서에 실린 출력은 전부 `python3` **3.12.3**(Linux, x86_64)에서 실제로 돌려 나온 것이다. 지어낸 출력은 없다.\
> ★ 던지는 형태는 `python3 - <파일` 하나로 고정했다 — 트레이스백이 `File "<stdin>", line N` 이 된다.\
> ★★★ **이 주제는 `SyntaxError` 전문을 다섯 블록 싣는다(하나는 3.11 판).** `match` 의 규칙 위반은 **실행 전에** 잡히므로 스택이 없고,
> **절대 경로도 안 박힌다.** 그래서 트레이스백을 **줄이지 않고 그대로** 실었다.\
> ★★ **캐럿이 있는 것과 없는 것이 섞여 있다 — 옮겨 적은 실수가 아니다.**
> 파서가 잡는 것(`**_`)은 **소스 줄 + 캐럿**이 나오고, 파서를 통과한 뒤 **컴파일 단계가 잡는 것**(캡처 뒤 도달 불가 ·
> OR 의 이름 불일치)은 **`File … line N` 과 메시지 두 줄뿐**이다(동작 3).\
> **버전** — `match` 문은 **3.10**(PEP 634) 부터다. 이 판은 3.12.3 이다.\
> ★ **구현 대 언어 보장 한 줄** — **패턴 종류·매치 규칙·「반박 불가 case 는 마지막에만」까지가 언어 레퍼런스의 보장**이고,
> **`SyntaxError` 의 문구와 캐럿 유무**는 CPython 쪽이다.\
> ★ **흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다 | 안 흔들린다(근거로 써도 되는 칸) |
> |---|---|
> | 판이 오르면 `SyntaxError` 의 **문구**(`name capture 'red' makes remaining patterns unreachable`) | ★★ `SyntaxError` 의 **종류와 `line N`** · `(exit 1)` |
> | ★ 판이 오르면 **캐럿이 붙느냐** — 이 판에서는 컴파일 단계 진단에 없다 | 어느 `case` 가 **골라졌나** · 캡처된 **값** |
> | — (주소·시간·순서 비보장 출력을 한 곳도 안 찍었다) | 「잡힌 경고 수」 |
>
> ★ **이 주제의 블록에는 주소도 시간도 절대 경로도 한 곳도 안 찍힌다.** 재대조 전부 동일.\
> **선행** — [11-tuple-and-unpacking](../11-tuple-and-unpacking/2-summary.md)(★★ **시퀀스 패턴은 언패킹의 확장**) ·
> [16-iterator-protocol](../16-iterator-protocol/2-summary.md)·[32-container-protocol](../32-container-protocol/2-summary.md)(★ **시퀀스 패턴이 요구하는 것은 프로토콜이 아니라 `Sequence` 인가**) ·
> [21-scope-legb-global-nonlocal](../21-scope-legb-global-nonlocal/2-summary.md)(★ **캡처는 대입이다 — 지역 이름을 만든다**) ·
> [36-dataclasses](../36-dataclasses/2-summary.md)(★ **`__match_args__` 를 자동으로 만든다**) ·
> [37-enum](../37-enum/2-summary.md)(★ **`case Color.RED:` 의 그 멤버**).

## 한눈에 — 쉽게 말하면

**`match` 는 「틀에 대어 보기」다.** 대상을 틀마다 차례로 대어 보고, **처음 맞는 틀**에서 멈춘다.
틀에 **빈칸**이 있으면 맞춰 보면서 그 자리의 값을 **이름에 담는다.**

* 틀 — `case` 뒤의 **패턴**.
* 빈칸 — **점 없는 맨 이름**(`x`·`red`·`RED`). ★ **무엇이든 맞고, 그 이름에 값을 담는다.**
* 견주는 값 — **점 있는 이름**(`Color.RED`)·리터럴(`"red"`·`1`). **`==` 로 견준다.**

```text
   match color:                     color = "blue"
       case "green":    ----------> "blue" == "green" ?  아니다 -> 다음 틀
       case Color.RED:  ----------> "blue" == Color.RED ? 아니다 -> 다음 틀
       case red:        ----------> ★ 빈칸이다. 무엇이든 맞는다. red = "blue" 를 대입한다
       (여기서 멈춘다)

   ★ 소문자냐 대문자냐가 아니다. 점이 있느냐 없느냐가 "견주기" 와 "빈칸" 을 가른다
   ★ 빈칸 뒤에 case 가 더 있으면 컴파일러가 SyntaxError 로 막는다 — 마지막이면 안 막는다
```

**비유 대응표** — 이 문서는 끝까지 이 대응을 지킨다.

| 비유 | 실체 | 확인하는 법 |
|---|---|---|
| 틀 | 패턴 | `case` 뒤에 쓴 것 |
| 틀에 대어 보기 | 매치 | 위에서 아래로, **처음 맞는 곳**에서 멈춘다 |
| ★ 빈칸 | **캡처 패턴**(점 없는 맨 이름) | 무엇이든 맞고 **그 이름에 대입**된다 |
| 이름을 안 적은 빈칸 | 와일드카드 `_` | 무엇이든 맞고 **대입하지 않는다** |
| ★ 견줄 견본 | **값 패턴**(점 있는 이름) · 리터럴 | `==` 로 견준다(`None`·`True`·`False` 만 `is`) |
| 틀 모양 | 시퀀스·매핑·클래스 패턴 | `Sequence`·`Mapping`·`isinstance` 를 먼저 본다 |
| 틀 옆의 조건 쪽지 | 가드(`if`) | 틀이 맞은 **뒤에** 따진다 |
| ★ 모든 경우를 다 대어 봤는지 세는 검사원 | 완결성 검사 | ★ **파이썬에는 없다** — Rust·Kotlin 에는 있다 |

**똑같은 구조다** — 실무에서 이게 물리는 자리도 굳어 있다.\
「**상수 `DEFAULT` 와 같으면 분기하려고 `case DEFAULT:` 를 썼더니 모든 값이 그 갈래로 가고, `DEFAULT` 가 바뀌었다**」가 그것이다.\
**`DEFAULT` 가 대문자여도 점이 없으면 빈칸**이다. 고치는 법은 **점을 만드는 것**(`Config.DEFAULT`) 하나다.

> **패턴(pattern)** — `case` 뒤에 쓰는 **모양 기술**. 식(expression)처럼 보이지만 **식이 아니다.**\
> 예: `case red:` 의 `red` 는 **변수를 읽는 것이 아니라 대입할 자리**다.

> **캡처 패턴(capture pattern)** — 점 없는 맨 이름. **반드시 맞고** 대상을 그 이름에 묶는다.\
> 예: `case x:` 뒤에 `x` 에는 대상이 들어 있다.

> **반박 불가 패턴(irrefutable pattern)** — **문법만 보고도 반드시 맞는다**고 증명되는 패턴. 캡처·와일드카드 등.\
> 예: 레퍼런스 — *"A match statement may have at most one irrefutable case block, and it must be last."*

### ★★ 이 주제가 쓰는 창 / 부적용인 창

**본체는 ① 「어느 `case` 가 골라졌나」 창이다.** 각 `case` 가 **자기 이름을 돌려주게** 하고
**대상 열한 개**를 차례로 넣어 **패턴 종류 표**를 실행으로 채운다.

| 창 | 무엇을 말해 주나 | 못 보는 것 |
|---|---|---|
| ① ★★★ **골라진 `case` 의 이름** | 어느 틀이 **먼저 맞았나** | 뒤 틀이 맞을 수 있었는지 |
| ② ★★★ **`match` 뒤의 이름 값** | 캡처가 **무엇을 덮어썼나** | — |
| ③ ★★ **`SyntaxError` 전문** | 컴파일러가 **어디서 막나** — `line N` 과 캐럿 유무 | 막지 않는 자리 |
| ④ ★ **`co_varnames`** | 캡처가 **지역 이름을 만들었나** | — |
| ⑤ ★ **`isinstance(s, collections.abc.Sequence)`** | 시퀀스 패턴이 **무엇을 요구하나** | — |
| ★ **부적용인 창** — 완결성 경고 | — | ★★ **파이썬에는 그런 검사가 없다** — 「경고 0건」을 블록으로 찍었다(동작 7) |
| ★ **부적용인 창** — 속도 | — | 이 문서는 **한 번도 안 쟀다**. `match` 가 `if` 사슬보다 빠르다·느리다를 적지 않았다 |

★★ **③이 이 주제의 네 번째 창이다.** 캡처 함정은 **「막히는 자리」와 「안 막히는 자리」** 둘로 나뉘는데,
**값 창(①②)만 보면 안 막히는 자리만 보인다** — 막히는 자리는 **아예 실행이 안 되기** 때문이다.
★ 그리고 **③ 안에서도 캐럿 유무가 갈린다**(동작 3) — 파서 단계인지 컴파일 단계인지를 그것이 말한다.

★★ **제5의 상태 — 「같은 질문을 다른 창으로 물었다」.**
「이 `match` 는 모든 경우를 다뤘나」를 **컴파일러 진단으로 물을 수 없다**(파이썬은 안 센다).
그래서 **모든 멤버를 실제로 흘려 보내 `None` 이 나오는 자리를 찾는 창**으로 바꿔 물었다(동작 7).
★ 바꾼 창이 못 보는 것 — **흘려 보낸 값들만** 본다. 「다른 타입이 들어오면」은 그 창 밖이다.

먼저 판을 박아 둔다.

```python
# e39_version.py
import keyword
import sys

print("version_info   =", sys.version_info)
print("implementation =", sys.implementation.name)
print("match 는 예약어인가     :", keyword.iskeyword("match"))
print("match 는 소프트 키워드인가:", keyword.issoftkeyword("match"))
print("case 는 소프트 키워드인가 :", keyword.issoftkeyword("case"))
match = [1, 2]
case = "이름으로 쓸 수 있다"
print("match =", match, "/ case =", case)
```

```text
===== python3 - <e39_version.py =====
version_info   = sys.version_info(major=3, minor=12, micro=3, releaselevel='final', serial=0)
implementation = cpython
match 는 예약어인가     : False
match 는 소프트 키워드인가: True
case 는 소프트 키워드인가 : True
match = [1, 2] / case = 이름으로 쓸 수 있다
(exit 0)
```

★ `match`·`case` 는 **예약어가 아니라 소프트 키워드**다 — 문장 머리에서 `match … :` 꼴일 때만 키워드이고,
그 밖에서는 **그냥 이름**이다. `match = [1, 2]` 가 된다. **3.10 전 코드의 `match` 변수를 안 깨려고** 그렇게 만들었다.

## 이 주제가 답하려는 질문

1. ★★★ **맨 이름이 왜 비교가 아니라 캡처가 되나** — 무엇을 덮어쓰고, **컴파일러는 어디서 막고 어디서 안 막나.**
2. ★★ **패턴 종류는 몇 가지이고 각각 무엇으로 견주나** — `==`·`is`·`isinstance`·`Sequence`·`Mapping`·`__match_args__`.
3. **모든 경우를 다뤘는지 누가 확인하나** — 파이썬과 Rust·Kotlin 의 차이.

★ 첫째가 이 주제의 인출 목표다.
**「대소문자가 아니라 점이 가른다」와 「캡처가 마지막 `case` 면 안 막힌다」를 실행으로 댈 수 있는 것**이 아는 것과 들은 것의 경계다.

## 동작 방식

> 이 절이 본문이다. 그림이 먼저 오고 문장이 그 그림을 읽어 준다.

### 1. ★★★ 캡처 함정 — 무엇이든 맞고, 이름을 덮어쓴다

**언제 쓰나** — 상수와 같은지 보려고 `case 상수이름:` 을 쓸 때. **이 주제에서 가장 자주 나는 사고다.**

```text
   red = "red"                          red = "red"
   color = "blue"                       color = "blue"
   match color:                         match color:
       case red:          <-- 빈칸          case Palette.RED:   <-- 견본 (점이 있다)
           ...                                  ...
                                            case _:
                                                ...
   결과: 갈래에 들어간다                  결과: _ 갈래
         red 가 "blue" 로 바뀐다                red 는 그대로

   ★ 왼쪽의 case red: 는 "red 와 같은가" 가 아니라 "red = color" 다
```

```python
# e39_capture.py
red = "red"
RED = "red"


class Palette:
    RED = "red"


print("① 모듈 수준에서 bare 이름 red 로 비교하려 했다")
color = "blue"
match color:
    case red:
        print("   red 갈래에 들어왔다")
print("   match 뒤의 red :", repr(red))

print("② 대문자 RED 도 똑같이 써 본다")
color = "green"
match color:
    case RED:
        print("   RED 갈래에 들어왔다")
print("   match 뒤의 RED :", repr(RED))

print("③ 점이 있는 이름 Palette.RED")
for color in ("red", "blue"):
    match color:
        case Palette.RED:
            print("   %-5s -> Palette.RED 갈래" % color)
        case _:
            print("   %-5s -> _ 갈래" % color)

print("④ 함수 안에서")
LIMIT = 10


def check(n):
    match n:
        case LIMIT:
            return "LIMIT 갈래, LIMIT=%r" % LIMIT


print("   check(3)  :", check(3))
print("   전역 LIMIT :", LIMIT)
print("   check 의 지역 이름 :", check.__code__.co_varnames)

print("⑤ 캡처에 가드를 붙이고 뒤에 case 를 하나 더")


def guarded(n):
    match n:
        case x if x == LIMIT:
            return "가드 갈래"
        case _:
            return "_ 갈래"


print("   guarded(10) :", guarded(10), "/ guarded(3) :", guarded(3))
```

```text
===== python3 - <e39_capture.py =====
① 모듈 수준에서 bare 이름 red 로 비교하려 했다
   red 갈래에 들어왔다
   match 뒤의 red : 'blue'
② 대문자 RED 도 똑같이 써 본다
   RED 갈래에 들어왔다
   match 뒤의 RED : 'green'
③ 점이 있는 이름 Palette.RED
   red   -> Palette.RED 갈래
   blue  -> _ 갈래
④ 함수 안에서
   check(3)  : LIMIT 갈래, LIMIT=3
   전역 LIMIT : 10
   check 의 지역 이름 : ('n', 'LIMIT')
⑤ 캡처에 가드를 붙이고 뒤에 case 를 하나 더
   guarded(10) : 가드 갈래 / guarded(3) : _ 갈래
(exit 0)
```

그림 해설.

* ★★★ **①** — `color` 가 `"blue"` 인데 **`red` 갈래에 들어왔다.** 그리고 **`match` 뒤의 `red` 가 `'blue'`** 다.
  `case red:` 는 **비교가 아니라 대입**이다 — 모듈 수준이라 **전역 `red` 를 덮어썼다.**
* ★★★ **②가 흔한 설명을 뒤집는다** — **대문자 `RED` 도 똑같이** 무엇이든 맞고 덮어써진다(`'green'`).
  README 행도 「소문자 이름이 캡처가 되는 함정」이라 적었지만, **실제로 가르는 것은 대소문자가 아니라 점**이다.
  ★ 레퍼런스의 문법이 그렇다 — 캡처 패턴은 **점 없는 이름**, 값 패턴은 **점 있는 이름**(`NAME1.NAME2`)이다.
* ★★ **③** — **`Palette.RED` 는 점이 있어 값 패턴**이다. `"red" == Palette.RED` 일 때만 맞고 `"blue"` 는 `_` 로 간다.
  레퍼런스 — *"The pattern succeeds if the value found compares equal to the subject value (using the `==` equality operator)."*
* ★★ **④ — 함수 안에서는 전역을 안 덮는 대신 지역 이름이 생긴다.** `check(3)` 이 `LIMIT` 갈래로 가서 **`LIMIT=3`** 을 돌려주고,
  **전역 `LIMIT` 은 `10` 그대로**다. `co_varnames` 에 **`LIMIT` 이 지역 변수로** 들어 있다.
  ★ [21번](../21-scope-legb-global-nonlocal/2-summary.md)의 규칙 그대로다 — **함수 안에서 대입되는 이름은 지역**이다. 캡처는 대입이다.
* ★ **⑤** — 캡처에 **가드**를 붙이면 **반박 가능**해져서 뒤에 `case` 를 둘 수 있다. `x if x == LIMIT` 은 비교를 **가드로 옮긴 것**이다.

**비용** — 캡처는 **공짜로 값을 꺼내 주는** 문법이다. 대가는 **비교하려던 자리와 모양이 같다**는 것 —
그래서 **상수 비교는 반드시 점 있는 이름**(클래스 속성·열거형 멤버·모듈 속성)으로 쓴다.

### 2. ★★★ 컴파일러가 막는 자리 — 캡처 뒤에 `case` 가 더 있으면

**언제 쓰나** — 1절의 사고가 **어떤 모양일 때 실행 전에 잡히나**를 알고 싶을 때.

```text
   case red:          <-- 반박 불가 (무엇이든 맞는다)
       ...
   case "blue":       <-- 여기는 영영 못 온다
       ...
        |
        v  컴파일러: "반박 불가 case 는 마지막에만"
   SyntaxError 「name capture 'red' makes remaining patterns unreachable」

   ★ 1절의 ① 은 case red: 가 마지막이라 안 막혔다 — 같은 실수가 자리만 다르다
```

```python
# e39_unreachable.py
red = "red"
color = "blue"
match color:
    case red:
        print("red 갈래")
    case "blue":
        print("blue 갈래")
```

```text
===== python3 - <e39_unreachable.py =====
  File "<stdin>", line 4
SyntaxError: name capture 'red' makes remaining patterns unreachable
(exit 1)
```

```text
===== python3.11 - <e39_unreachable_py311.py =====
  File "<stdin>", line 4
SyntaxError: name capture 'red' makes remaining patterns unreachable
(exit 1)
```

```python
# e39_wildcard_first.py
match "blue":
    case _:
        print("_ 갈래")
    case "blue":
        print("blue 갈래")
```

```text
===== python3 - <e39_wildcard_first.py =====
  File "<stdin>", line 2
SyntaxError: wildcard makes remaining patterns unreachable
(exit 1)
```

그림 해설.

* ★★★ **첫 블록** — `SyntaxError: name capture 'red' makes remaining patterns unreachable`, **`line 4`**(`case red:` 의 줄), `(exit 1)`.
  **한 줄도 실행되지 않았다** — `red = "red"` 조차 안 돌았다. 컴파일에서 막혔기 때문이다.
  ★ **`python3.11` 로 던진 둘째 블록이 한 글자도 같다**(소스도 같다 — 파일 이름만 `e39_unreachable_py311.py`). 캐럿이 없는 것도 **두 판 공통**이다.
* ★★ **둘째 블록** — `_` 가 먼저 오면 **`wildcard makes remaining patterns unreachable`** 이다. 같은 규칙의 다른 문구다.
* ★★★ **막는 자리와 안 막는 자리** —
  **막는다**: 반박 불가 패턴 **뒤에** `case` 가 더 있을 때(이 두 블록).
  **안 막는다**: 반박 불가 패턴이 **마지막** `case` 일 때(1절의 ①·②·④) · 캡처에 **가드**가 붙었을 때(1절의 ⑤).
  ★ 레퍼런스 한 문장이 전부다 — *"at most one irrefutable case block, and it must be last."*
* ★★ 그래서 **가장 위험한 모양**은 「`case 상수:` 하나에 `case _:` 없이 끝나는 것」이다.
  컴파일러가 **못 막고**, 모든 값이 그 갈래로 가고, 이름까지 덮어쓴다.

**비용** — 컴파일 에러는 **공짜 안전망**이다. 다만 **마지막 자리**에서는 그 망이 **원리상 없다** — 마지막 캡처는 「그 밖 전부」라는 정당한 쓰임이기 때문이다.

### 3. ★★ `SyntaxError` 두 종류 — 캐럿이 있는 것과 없는 것

**언제 쓰나** — 진단을 읽을 때 **어느 단계가 막았나**를 가르고 싶을 때. 그리고 **이 문서의 블록이 왜 모양이 다른가**.

```text
   소스 --> [파서] --> 구문 트리 --> [컴파일러: 심볼·패턴 검사] --> 바이트코드
              |                              |
              v                              v
     SyntaxError + 소스 줄 + 캐럿       SyntaxError, 소스 줄·캐럿 없음
     (**_ 는 문법에 없다)               (도달 불가 · OR 의 이름 불일치)
```

```python
# e39_or_names.py
match (1, 2):
    case (a, 0) | (0, b):
        print(a, b)
```

```text
===== python3 - <e39_or_names.py =====
  File "<stdin>", line 2
SyntaxError: alternative patterns bind different names
(exit 1)
```

```python
# e39_double_star_underscore.py
match {"k": 1}:
    case {"k": 1, **_}:
        print("k 갈래")
```

```text
===== python3 - <e39_double_star_underscore.py =====
  File "<stdin>", line 2
    case {"k": 1, **_}:
                    ^
SyntaxError: invalid syntax
(exit 1)
```

그림 해설.

* ★★ **첫 블록** — `alternative patterns bind different names`. `(a, 0) | (0, b)` 는 **한쪽은 `a` 만, 한쪽은 `b` 만** 묶는다.
  어느 쪽이 맞았는지에 따라 **없는 이름이 생기므로** 막는다. ★ **소스 줄도 캐럿도 없다** — 2절의 두 블록과 같은 모양이다.
* ★★ **둘째 블록** — `{"k": 1, **_}` 는 **`invalid syntax`** 이고 **소스 줄과 캐럿**이 나온다. `**rest` 는 되는데 **`**_` 는 문법에 없다**
  (남는 키는 어차피 무시되므로 `**_` 는 의미가 없다 — 동작 5).
* ★★★ **캐럿 유무가 단계를 말한다.** 파서가 잡는 것은 **캐럿이 있고**, 파서를 통과한 뒤 컴파일러가 잡는 것은 **없다.**
  ★ 이 문서의 `SyntaxError` 다섯 블록 중 **캐럿이 있는 것은 이것 하나**다 — **옮겨 적다 빠뜨린 게 아니다.**

**비용** — 없다. 다만 캐럿이 없는 진단은 **`line N` 만 믿고 읽어야** 한다.

### 4. ★★★ 패턴 종류 전수 — 열한 가지

**언제 쓰나** — `case` 뒤에 무엇을 쓸 수 있고 **각각 무엇으로 견주나**를 한 번에 볼 때. **이 주제의 본체 표다.**

| 종류 | 쓴 꼴 | 견주는 법 | 이름을 묶나 |
|---|---|---|---|
| 리터럴 | `1` · `"g"` · `None` | `==` — ★ `None`·`True`·`False` 만 **`is`** | 아니다 |
| ★ 캡처 | `x` · `red` · `RED` | **무조건 맞는다** | ★ 묶는다 |
| 와일드카드 | `_` | 무조건 맞는다 | ★ **안 묶는다** |
| ★ 값 | `Color.RED` · `mod.CONST` | **`==`** | 아니다 |
| 그룹 | `("g")` | 괄호 안 패턴 그대로 | 안의 것에 따라 |
| 시퀀스 | `[a, *rest]` · `(a, b)` | `Sequence` 인가 + 길이 + 원소 — ★ **`str`·`bytes`·`bytearray` 제외** | 원소 자리마다 |
| 매핑 | `{"op": op, **rest}` | `Mapping` 인가 + **적은 키만** | 값 자리마다 |
| 클래스 | `Pt(0, y)` · `Pt(x=0)` | **`isinstance`** + 속성(위치는 `__match_args__` 로) | 속성 자리마다 |
| OR | `0 \| 1` | 왼쪽부터 하나라도 | ★ **갈래마다 같은 이름**이어야 한다 |
| AS | `str() as text` | 안쪽 패턴 + 전체를 이름에 | 묶는다 |
| 가드 | `case p if 조건:` | 패턴이 맞은 **뒤** 조건 | 패턴에 따라 |

```text
   kind(subject) 의 case 순서 = 위 표의 순서 (캡처를 맨 마지막에 둬야 컴파일된다)

   None -> 리터럴    1 -> OR    Color.RED -> 값    "g" -> 그룹
   (7,8,9) -> 시퀀스   {"op": ..} -> 매핑   Pt(0,5) -> 클래스(위치)   Pt(4,0) -> 클래스(키워드)
   "hello" -> AS    -2.5 -> 가드    2.5 -> 캡처
```

```python
# e39_kinds.py
from dataclasses import dataclass
from enum import Enum


class Color(Enum):
    RED = 1


@dataclass
class Pt:
    x: int
    y: int


def kind(subject):
    match subject:
        case None:
            return "리터럴(None)"
        case 0 | 1:
            return "OR(리터럴 0 | 1)"
        case Color.RED:
            return "값(Color.RED)"
        case ("g"):
            return "그룹((\"g\"))"
        case [first, *rest]:
            return "시퀀스 first=%r rest=%r" % (first, rest)
        case {"op": op}:
            return "매핑 op=%r" % op
        case Pt(0, y):
            return "클래스(위치) y=%r" % y
        case Pt(x=x, y=0):
            return "클래스(키워드) x=%r" % x
        case str() as text:
            return "AS text=%r" % text
        case float(v) if v < 0:
            return "가드 v=%r" % v
        case other:
            return "캡처 other=%r" % other


subjects = [None, 1, Color.RED, "g", (7, 8, 9), {"op": "+", "z": 0},
            Pt(0, 5), Pt(4, 0), "hello", -2.5, 2.5]
for s in subjects:
    print("%-22r -> %s" % (s, kind(s)))

print("--- match 42 / case _ 뒤 ---")
match 42:
    case _:
        pass
print("'_' in globals() :", "_" in globals())
```

```text
===== python3 - <e39_kinds.py =====
None                   -> 리터럴(None)
1                      -> OR(리터럴 0 | 1)
<Color.RED: 1>         -> 값(Color.RED)
'g'                    -> 그룹(("g"))
(7, 8, 9)              -> 시퀀스 first=7 rest=[8, 9]
{'op': '+', 'z': 0}    -> 매핑 op='+'
Pt(x=0, y=5)           -> 클래스(위치) y=5
Pt(x=4, y=0)           -> 클래스(키워드) x=4
'hello'                -> AS text='hello'
-2.5                   -> 가드 v=-2.5
2.5                    -> 캡처 other=2.5
--- match 42 / case _ 뒤 ---
'_' in globals() : False
(exit 0)
```

그림 해설.

* ★ **열한 대상이 열한 갈래로 갔다** — 표의 열한 종류가 실제로 전부 한 번씩 골라졌다.
* ★★ **`'hello'` 가 시퀀스 갈래(`[first, *rest]`)가 아니라 AS 갈래로 갔다.** 문자열은 시퀀스 패턴에 **안 맞는다**(동작 5).
* ★ **`2.5` 는 가드에서 떨어져(`v < 0` 이 거짓) 마지막 캡처로** 갔다. **가드는 패턴이 맞은 뒤에** 따진다.
* ★ **`'_' in globals()` 가 `False`** — `_` 는 **이름을 묶지 않는다.** 레퍼런스 — *"A single underscore `_` is not a capture pattern"*.
* ★ **`Pt(0, 5)` 가 위치 패턴 `Pt(0, y)` 로 풀린 것**은 dataclass 가 만든 **`__match_args__ = ('x', 'y')`** 덕이다(동작 6).

**비용** — `case` 는 **위에서 아래로 차례로** 대어 본다. 순서가 곧 의미다 — **넓은 틀을 위에 두면 아래 틀이 안 불린다.**

### 5. ★★ 시퀀스·매핑 패턴 — 무엇을 요구하나

**언제 쓰나** — 리스트·튜플·dict 를 `match` 로 가를 때. 그리고 「왜 문자열이 안 맞지」·「왜 남는 키가 있어도 맞지」가 막힐 때.

```text
   시퀀스 패턴 [a, b] 이 맞으려면
      isinstance(s, collections.abc.Sequence)     ★ 프로토콜(__getitem__·__len__)이 아니라 ABC 명부
      and not isinstance(s, (str, bytes, bytearray))
      and len(s) == 2

   매핑 패턴 {"id": i, **rest} 이 맞으려면
      isinstance(m, collections.abc.Mapping)
      and "id" 키가 있다                           ★ 남는 키는 상관없다 -> rest 로 모인다
```

```python
# e39_sequence.py
import collections.abc


class Bag:
    def __init__(self, *items):
        self.items = list(items)

    def __len__(self):
        return len(self.items)

    def __getitem__(self, i):
        return self.items[i]


class RegBag(Bag):
    pass


collections.abc.Sequence.register(RegBag)


def two(s):
    match s:
        case [a, b]:
            return "시퀀스 a=%r b=%r" % (a, b)
        case _:
            return "안 맞음"


subjects = [[1, 2], (1, 2), range(2), "ab", b"ab", bytearray(b"ab"),
            {1, 2}, iter([1, 2]), (x for x in [1, 2]), Bag(1, 2), RegBag(1, 2)]
for s in subjects:
    label = type(s).__name__
    print("%-10s abc.Sequence=%-5s -> %s"
          % (label, isinstance(s, collections.abc.Sequence), two(s)))
```

```text
===== python3 - <e39_sequence.py =====
list       abc.Sequence=True  -> 시퀀스 a=1 b=2
tuple      abc.Sequence=True  -> 시퀀스 a=1 b=2
range      abc.Sequence=True  -> 시퀀스 a=0 b=1
str        abc.Sequence=True  -> 안 맞음
bytes      abc.Sequence=True  -> 안 맞음
bytearray  abc.Sequence=True  -> 안 맞음
set        abc.Sequence=False -> 안 맞음
list_iterator abc.Sequence=False -> 안 맞음
generator  abc.Sequence=False -> 안 맞음
Bag        abc.Sequence=False -> 안 맞음
RegBag     abc.Sequence=True  -> 시퀀스 a=1 b=2
(exit 0)
```

그림 해설 — 시퀀스.

* ★★★ **`str`·`bytes`·`bytearray` 는 `abc.Sequence` 가 참인데도 안 맞는다.** 레퍼런스가 셋을 **이름으로** 뺀다.
  ★ `"ab"` 를 `[a, b]` 로 쪼개 주면 편할 것 같지만, 문자열 하나를 **글자 시퀀스로 오인하는 사고**가 더 흔해서 막은 것이다.
* ★★ **`Bag` 은 `__len__`·`__getitem__` 을 다 가졌는데 안 맞는다.** 시퀀스 패턴이 보는 것은
  **[16번](../16-iterator-protocol/2-summary.md)·[32번](../32-container-protocol/2-summary.md)의 프로토콜이 아니라 `collections.abc.Sequence` 명부**다.
  **`RegBag` 은 `Sequence.register` 로 명부에 올리자 맞았다** — 메서드는 같다. ★ [35번](../35-abc-and-protocol/2-summary.md)의 `register` 가 여기서 쓰인다.
* ★ `set`·이터레이터·제너레이터도 안 맞는다 — **길이를 모르거나 순서가 없는 것**은 시퀀스 명부에 없다.

```python
# e39_mapping.py
from collections import defaultdict


def pick(m):
    match m:
        case {"id": i, **rest}:
            return "id=%r rest=%r" % (i, rest)
        case _:
            return "안 맞음"


print("① 남는 키")
print("   ", pick({"id": 1}))
print("   ", pick({"id": 1, "name": "a", "tags": []}))
print("   ", pick({"name": "a"}))

print("② defaultdict 에 없는 키를 물으면")
d = defaultdict(list, {"name": "a"})
print("   ", pick(d))
print("    match 뒤의 키 목록 :", sorted(d))
print("    d['id'] 로 직접 읽은 뒤 :", d["id"], sorted(d))

print("③ 키 개수로 끊고 싶으면")


def exactly_id(m):
    match m:
        case {"id": i, **rest} if not rest:
            return "id 하나뿐 i=%r" % i
        case _:
            return "안 맞음"


print("   ", exactly_id({"id": 1}), "/", exactly_id({"id": 1, "x": 0}))
```

```text
===== python3 - <e39_mapping.py =====
① 남는 키
    id=1 rest={}
    id=1 rest={'name': 'a', 'tags': []}
    안 맞음
② defaultdict 에 없는 키를 물으면
    안 맞음
    match 뒤의 키 목록 : ['name']
    d['id'] 로 직접 읽은 뒤 : [] ['id', 'name']
③ 키 개수로 끊고 싶으면
    id 하나뿐 i=1 / 안 맞음
(exit 0)
```

그림 해설 — 매핑.

* ★★ **①** — **남는 키가 있어도 맞는다.** `name`·`tags` 는 **`rest` 로 모였다.** 적은 키(`id`)가 없을 때만 떨어진다.
  ★ 시퀀스 패턴은 **길이까지** 맞아야 하는데 매핑 패턴은 **적은 키만** 본다 — **둘의 엄격함이 다르다.**
* ★★ **②** — `defaultdict` 에 없는 키 `id` 를 물었는데 **안 맞고, 키도 안 생겼다**(`['name']`).
  `d['id']` 로 **직접 읽으면 그제야 `[]` 가 생긴다.** 매핑 패턴은 **`d[key]` 로 읽지 않는다** — 기본값 공장을 안 부른다.
* ★ **③** — 「키가 정확히 이것뿐」을 원하면 **`**rest` 로 받고 가드에서 `not rest`** 를 본다.

**비용** — 매핑 패턴의 관대함은 **JSON 을 다루기 좋게** 한 선택이다. 대가는 **오타 난 키가 섞여도 맞는다**는 것이다.

### 6. ★★ 클래스 패턴 — `isinstance` + `__match_args__`

**언제 쓰나** — 객체를 **타입과 속성으로** 가를 때. dataclass·`NamedTuple` 이 여기서 빛난다.

```text
   case Pt(0, y):
        |
        v   isinstance(subject, Pt) ?
        v   위치 부분 패턴 -> Pt.__match_args__ = ('x', 'y') 로 키워드로 바꾼다
        v   subject.x == 0 ?  y = subject.y

   __match_args__ 가 없으면 위치 부분 패턴은 TypeError (키워드는 된다)
   int(n) · str(s) · float(n) 등 내장 열한 개는 위치 하나가 "대상 전체" 다
```

```python
# e39_class.py
from dataclasses import dataclass
from typing import NamedTuple


@dataclass
class DPt:
    x: int
    y: int


class NPt(NamedTuple):
    x: int
    y: int


class Plain:
    def __init__(self, x, y):
        self.x = x
        self.y = y


print("① __match_args__")
print("   DPt  :", DPt.__match_args__)
print("   NPt  :", NPt.__match_args__)
print("   Plain:", getattr(Plain, "__match_args__", "없음"))

print("② 위치 부분 패턴")
for obj in (DPt(1, 2), NPt(1, 2), Plain(1, 2)):
    try:
        match obj:
            case DPt(a, b) | NPt(a, b) | Plain(a, b):
                print("   %-5s a=%r b=%r" % (type(obj).__name__, a, b))
    except TypeError as exc:
        print("   %-5s %s: %s" % (type(obj).__name__, type(exc).__name__, exc))

print("③ 키워드 부분 패턴")
match Plain(1, 2):
    case Plain(x=1, y=b):
        print("   Plain(x=1, y=b) b=%r" % b)

print("④ 내장 타입 하나짜리 위치 패턴")
for v in (5, 5.0, True, "5"):
    match v:
        case int(n):
            print("   %-5r -> int(n) n=%r" % (v, n))
        case float(n):
            print("   %-5r -> float(n) n=%r" % (v, n))
        case _:
            print("   %-5r -> _" % (v,))

print("⑤ 리터럴 1 과 True")
for v in (1, 1.0, True):
    match v:
        case True:
            print("   %-5r -> case True" % (v,))
        case 1:
            print("   %-5r -> case 1" % (v,))

print("⑥ 순서를 바꿔 case 1 을 위에")
for v in (1, True):
    match v:
        case 1:
            print("   %-5r -> case 1" % (v,))
        case True:
            print("   %-5r -> case True" % (v,))

print("⑦ 값 패턴에 IntEnum 멤버")
from enum import IntEnum


class Level(IntEnum):
    LOW = 1


for v in (1, 1.0, Level.LOW):
    match v:
        case Level.LOW:
            print("   %-12r -> case Level.LOW" % (v,))
        case _:
            print("   %-12r -> _" % (v,))
```

```text
===== python3 - <e39_class.py =====
① __match_args__
   DPt  : ('x', 'y')
   NPt  : ('x', 'y')
   Plain: 없음
② 위치 부분 패턴
   DPt   a=1 b=2
   NPt   a=1 b=2
   Plain TypeError: Plain() accepts 0 positional sub-patterns (2 given)
③ 키워드 부분 패턴
   Plain(x=1, y=b) b=2
④ 내장 타입 하나짜리 위치 패턴
   5     -> int(n) n=5
   5.0   -> float(n) n=5.0
   True  -> int(n) n=True
   '5'   -> _
⑤ 리터럴 1 과 True
   1     -> case 1
   1.0   -> case 1
   True  -> case True
⑥ 순서를 바꿔 case 1 을 위에
   1     -> case 1
   True  -> case 1
⑦ 값 패턴에 IntEnum 멤버
   1            -> case Level.LOW
   1.0          -> case Level.LOW
   <Level.LOW: 1> -> case Level.LOW
(exit 0)
```

그림 해설.

* ★ **①** — dataclass 와 `NamedTuple` 은 **`__match_args__ = ('x', 'y')`** 를 **자동으로** 갖는다([36번](../36-dataclasses/2-summary.md)의 동작 1 에 이미 찍혀 있다).
  손으로 쓴 `Plain` 은 **없다.**
* ★★ **②** — `Plain(a, b)` 는 **`TypeError: Plain() accepts 0 positional sub-patterns (2 given)`** 이다.
  ★ **`SyntaxError` 가 아니라 실행 중 `TypeError`** 다 — 그 `case` 에 **실제로 대어 볼 때** 난다.
* ★ **③** — **키워드 부분 패턴**(`Plain(x=1, y=b)`)은 `__match_args__` 없이도 된다. 속성 이름을 직접 적었기 때문이다.
* ★★ **④** — `int(n)` 은 **대상 전체**를 `n` 에 묶는다. `5.0` 은 `float(n)` 으로 갔다. ★ **`True` 가 `int(n)` 으로 갔다** — `bool` 은 `int` 의 하위다.
* ★★★ **⑤** — `1.0` 이 **`case 1`** 에 맞았다(`1.0 == 1`). 그런데 **`1` 은 `case True` 에 안 맞았다** —
  `True` 리터럴은 **`is`** 로 비교하기 때문이다. 레퍼런스 — *"For the singletons `None`, `True` and `False`, the `is` operator is used."*
* ★★ **⑥ — 순서를 바꾸면 `True` 도 `case 1` 에 걸린다**(`True == 1`). **`case True` 를 위에 둬야** 둘이 갈린다.
* ★ **⑦** — 값 패턴에 **`IntEnum` 멤버**를 쓰면 **정수 `1` 도 실수 `1.0` 도 맞는다.** 값 패턴이 `==` 이고
  [37번](../37-enum/2-summary.md)의 격자가 보인 대로 `IntEnum` 은 **`int` 로서 답하기** 때문이다. 평범한 `Enum` 멤버라면 안 맞는다.

**비용** — 클래스 패턴은 `isinstance` 한 번 + 속성 읽기다. **`__match_args__` 순서가 곧 위치 패턴의 계약**이 되므로,
dataclass 필드 순서를 바꾸면 **위치 패턴의 의미가 조용히 바뀐다.**

### 7. ★★★ 완결성 검사가 없다 — 빠진 경우는 `None` 으로 조용히

**언제 쓰나** — 열거형·유한 집합을 `match` 로 다룰 때. **멤버를 하나 늘렸을 때 누가 알려 주나.**

```text
   Light = RED | YELLOW | GREEN

   match light:                Rust match              Kotlin when (식 · enum 주체)
       case Light.RED: ...     E0004 non-exhaustive     컴파일 에러
       case Light.GREEN: ...   (컴파일이 안 된다)        (빠진 가지 이름을 대 준다)
   (YELLOW 가 빠졌다)
        |
        v
   파이썬: 경고 0건 · 컴파일 통과 · YELLOW 가 들어오면 아무 case 도 안 맞고 지나간다 -> 함수가 None
```

```python
# e39_exhaust.py
import warnings
from enum import Enum


class Light(Enum):
    RED = 1
    YELLOW = 2
    GREEN = 3


def action(light):
    match light:
        case Light.RED:
            return "정지"
        case Light.GREEN:
            return "진행"


with warnings.catch_warnings(record=True) as caught:
    warnings.simplefilter("always")
    for light in Light:
        print("%-12s -> %r" % (light.name, action(light)))
print("잡힌 경고 수 :", len(caught))
```

```text
===== python3 - <e39_exhaust.py =====
RED          -> '정지'
YELLOW       -> None
GREEN        -> '진행'
잡힌 경고 수 : 0
(exit 0)
```

그림 해설.

* ★★★ **`YELLOW` 가 `None` 을 돌려줬다.** 어느 `case` 에도 안 맞으면 **`match` 문은 아무 일도 안 하고 지나간다.**
  함수 끝까지 가서 **암묵적 `None`** 이 나왔다.
* ★★★ **「잡힌 경고 수 : 0」** 과 **`(exit 0)`** — 이 블록의 결론은 **침묵**이다.
  **세 멤버를 전부 흘려 보냈고 그중 하나가 조용히 빠졌다** — 규칙 18-A 대로 「몇 군데 물었나」를 적으면 **셋 중 하나**다.
* ★★ **Rust 대비** — [Rust 18번](../../../rust/syntax/18-match-and-exhaustiveness/2-summary.md)은 같은 모양을 **E0004 `non-exhaustive patterns`** 로 **컴파일에서** 막는다고 실측했다.
  ★ **Kotlin 대비** — [Kotlin 23번](../../../kotlin/syntax/23-sealed-classes-and-when-exhaustiveness/2-summary.md)은 `enum`·`sealed` 주체의 `when` 이 **문에서도 완결을 요구**한다고 실측했다.
  **파이썬은 문법 차원에서 그런 검사가 없다.** 이 판의 인터프리터가 말하는 것은 **아무것도 없다**(경고 0).
* ★ 처방 — **마지막에 `case _: raise …`** 를 둔다. 빠진 경우가 **실행 중에라도 시끄럽게** 드러난다.
  ★ 정적 도구가 이 자리를 잡는지는 **이 머신에 타입 검사기가 없어 못 쟀다**([35번](../35-abc-and-protocol/2-summary.md)).

**비용** — 없다. 그리고 **그것이 문제다** — 멤버를 늘려도 **누구도 알려 주지 않는다.**

### 8. ★★ Rust 와 견주면 — 같은 함정이 있나

```text
                         맨 이름의 뜻            변형과 이름이 같으면           뒤 팔을 못 닿게 하면
   Python match          캡처(무엇이든 맞음)     -- (변형 개념 없음)              SyntaxError (마지막이 아니면)
   Rust match            변수 바인딩(무엇이든)   E0170 (기본 deny — 에러)         unreachable pattern 경고
```

* ★★★ **Rust 에도 같은 함정이 있다** — [Rust 18번](../../../rust/syntax/18-match-and-exhaustiveness/2-summary.md)의 실측에서
  `Event::` 를 빼먹은 **`Click =>`** 이 **새 변수를 묶는 팔**이 됐다. 그 편이 「**대문자 이름도 변수 패턴이다**」라고 적었다 —
  **파이썬과 똑같이 대소문자가 아니라 경로(점·`::`)가 가른다.**
* ★★ **다른 점은 안전망의 두께**다. Rust 는 그 이름이 **변형 이름과 같으면 E0170 을 에러로** 내고,
  뒤 팔마다 **`unreachable pattern`** 경고를 붙이고, 거기에 **완결성 검사(E0004)** 까지 있다.
  파이썬은 **「마지막이 아니면 `SyntaxError`」 하나**뿐이다.
* ★ 그 편이 적은 대로 Rust 도 **`use Event::*;` 로 변형을 열어 두면 E0170 조차 안 난다** — 그때는 진짜로 변형을 짚은 것이 되기 때문이다.
  **파이썬에는 이런 「열어 두기」가 없다** — 맨 이름은 **언제나** 캡처다.

## 문법 — 형태와 규칙

**형태**

```text
match subject:                          # match·case 는 소프트 키워드 (3.10+)
    case 0 | 1:                         # OR — 갈래마다 같은 이름을 묶어야 한다
    case None:                          # None·True·False 는 is 로
    case Color.RED:                     # ★ 값 패턴 — 점이 있어야 한다. == 로
    case [first, *rest]:                # 시퀀스 — str·bytes·bytearray 는 안 맞는다
    case {"op": op, **rest}:            # 매핑 — 남는 키 허용 · **_ 는 문법에 없다
    case Pt(0, y) | Pt(x=0, y=y):       # 클래스 — 위치는 __match_args__ 로
    case str() as text:                 # AS — 전체를 이름에
    case n if n > 100:                  # 가드 — 패턴이 맞은 뒤
    case other:                         # ★ 캡처 — 반박 불가. 마지막에만
    case _:                             # 와일드카드 — 이름을 안 묶는다 (캡처와 둘 다 둘 수는 없다)
```

규칙 열.

1. ★★★ **점 없는 맨 이름은 캡처**다 — 대소문자 무관. **무엇이든 맞고 그 이름에 대입**한다.
2. ★★★ **상수와 견주려면 점 있는 이름**(값 패턴)을 쓴다. `==` 로 비교한다.
3. ★★ **반박 불가 `case` 는 하나, 마지막에만** — 어기면 `SyntaxError`(소스 줄·캐럿 없음).
4. ★★ **마지막 캡처는 안 막힌다** — 그 자리의 사고는 컴파일러가 못 잡는다.
5. ★ **캡처는 대입**이다 — 모듈에서는 전역을 덮고, 함수에서는 지역 이름을 만든다.
6. ★ **`None`·`True`·`False` 는 `is`**, 나머지 리터럴은 `==`. `1.0` 은 `case 1` 에 맞고 `1` 은 `case True` 에 안 맞는다.
7. ★★ **시퀀스 패턴은 `abc.Sequence` 명부**를 본다 — `str`·`bytes`·`bytearray` 는 이름으로 빠진다.
8. ★★ **매핑 패턴은 적은 키만** 본다 — 남는 키 허용, `defaultdict` 의 기본값 공장을 안 부른다.
9. ★ **클래스 위치 패턴은 `__match_args__`** 가 있어야 한다 — 없으면 **실행 중 `TypeError`**.
10. ★★★ **완결성 검사가 없다** — 안 맞으면 **조용히 지나간다.**

**금지 사례 — 컴파일되지 않는 꼴**(코드 펜스가 아니라 표로 적는다 — 전문은 동작 2·3 의 블록)

| 쓴 꼴 | 진단 | 어느 단계 |
|---|---|---|
| `case red:` 뒤에 `case "blue":` | `SyntaxError: name capture 'red' makes remaining patterns unreachable` | 컴파일(캐럿 없음) |
| `case _:` 뒤에 `case "blue":` | `SyntaxError: wildcard makes remaining patterns unreachable` | 컴파일(캐럿 없음) |
| `case (a, 0) \| (0, b):` | `SyntaxError: alternative patterns bind different names` | 컴파일(캐럿 없음) |
| `case {"k": 1, **_}:` | `SyntaxError: invalid syntax` | ★ 파서(캐럿 있음) |

**금지 사례 — 컴파일은 되는데 조용히 어긋나는 꼴**

| 쓴 꼴 | 무슨 일이 나나 |
|---|---|
| `case LIMIT:` 하나로 끝나는 `match` | ★★ **모든 값이 그 갈래** · 이름 덮어씀 |
| `case [a, b]:` 에 문자열 `"ab"` 를 기대 | 안 맞는다 |
| `case {"id": i}:` 로 「`id` 만 있는 dict」를 기대 | 남는 키가 있어도 맞는다 |
| 열거형 멤버 하나를 빼먹음 | `None` 으로 지나간다 · 경고 0 |
| `case 1:` 을 `case True:` 위에 둠 | `True` 가 `case 1` 에 걸린다 |

## 어디서 틀리나

### (1) ★★★ 「소문자 이름이 캡처가 된다」로 외운다

**대소문자가 아니라 점이다**(동작 1 의 ②). `RED`·`DEFAULT`·`MAX_SIZE` 도 **점이 없으면 캡처**다.

### (2) ★★★ `case 상수:` 를 마지막에 두고 안심한다

**컴파일러가 못 막는다**(동작 2). 모든 값이 그 갈래로 가고 **이름이 덮어써진다.**\
★ 고치는 법은 **점을 만드는 것** — 클래스 속성·열거형 멤버·`import mod` 뒤의 `mod.CONST`.

### (3) ★★ 함수 안에서 전역 상수를 `case` 에 썼다

**지역 이름이 생긴다**(동작 1 의 ④). 그 함수의 **다른 자리에서 그 상수를 먼저 읽으면** [21번](../21-scope-legb-global-nonlocal/2-summary.md)의 `UnboundLocalError` 꼴이 된다.

### (4) ★★ `SyntaxError` 에 캐럿이 없어서 옮겨 적다 빠뜨렸다고 의심한다

**컴파일 단계 진단은 원래 캐럿이 없다**(동작 3). 파서 진단만 있다.

### (5) ★★ 문자열을 시퀀스 패턴으로 쪼개려 한다

**안 맞는다**(동작 5). 글자로 쪼개려면 `list(s)` 를 대상으로 준다.

### (6) ★ `__len__`·`__getitem__` 을 구현했으니 시퀀스 패턴에 맞을 거라 믿는다

**`abc.Sequence` 명부에 있어야** 맞는다(동작 5 의 `Bag` 대 `RegBag`).

### (7) ★ 매핑 패턴이 키 집합을 정확히 맞춘다고 믿는다

**적은 키만** 본다. 정확히 맞추려면 `**rest` + 가드.

### (8) ★ `__match_args__` 없는 클래스에 위치 패턴을 쓴다

**그 `case` 에 닿을 때** `TypeError` 다 — **컴파일은 통과한다.**

### (9) ★★★ 「`match` 가 빠진 경우를 알려 줄 것이다」

**아무 말도 안 한다**(동작 7). **`case _: raise`** 를 습관으로 둔다.

### (10) ★ `case True:` 와 `case 1:` 의 순서를 가볍게 본다

`True == 1` 이라 **`case 1` 이 먼저면 `True` 가 거기 걸린다.** `case True` 는 `is` 라 `1` 을 안 받는다.

## 구현 세부사항 대 언어 보장

| 층 | 무엇인가 | 어떻게 확인했나 |
|---|---|---|
| **언어 보장** | 언어 레퍼런스 · PEP 634 가 정한 것 | 문서 문장을 열어서 인용 |
| **CPython 구현** | 이 구현이 그렇게 하는 것 | 실행 |
| **이 판(3.12.3)의 관찰** | 이 판에서 그랬을 뿐 | 진단 문구 · 캐럿 |

### 언어 보장

| 사실 | 근거 |
|---|---|
| 캡처 패턴은 대상을 **이름에 묶는다** | 레퍼런스 — *"A capture pattern binds the subject value to a name."* |
| `_` 는 캡처가 아니라 **와일드카드** | 레퍼런스 |
| 값 패턴은 **점 있는 이름**이고 **`==`** 로 견준다 | 레퍼런스 |
| 반박 불가 `case` 는 **하나, 마지막** | 레퍼런스 |
| `None`·`True`·`False` 는 **`is`** | 레퍼런스 |
| 시퀀스 패턴은 **`str`·`bytes`·`bytearray` 에 실패** | 레퍼런스 |
| 매핑 패턴은 **적은 키만** 본다 | 레퍼런스 |
| 클래스 위치 패턴은 **`__match_args__`** 로 바뀐다 · 내장 열한 개는 대상 전체 | 레퍼런스 |
| 한 패턴에서 **한 이름은 한 번만** 묶는다 · OR 갈래는 **같은 이름 집합** | 레퍼런스 |
| `match`·`case` 는 **소프트 키워드** | 레퍼런스 · `keyword.issoftkeyword` |

### CPython 구현 세부사항

| 사실 | 어떻게 확인했나 |
|---|---|
| ★ 반박 불가 위반이 **파서가 아니라 컴파일 단계**에서 잡힌다 | 실행 — 소스 줄·캐럿이 없다 |
| 매핑 패턴이 **`defaultdict` 의 기본값 공장을 안 부른다** | 실행 — 키가 안 생겼다 |
| 진단 **문구** 전부 | 실행 |

### 이 판의 관찰

| 관찰 | 어디가 흔들리나 |
|---|---|
| `name capture 'red' makes remaining patterns unreachable` 등 **문구** | 판이 오르면 바뀔 수 있다 |
| ★ 컴파일 단계 `SyntaxError` 에 **캐럿이 없는 것** | **다음 판에서 다시 찍을 자리**(판이 오르면 바뀔 수 있다) |

### 그래서 이렇게 적으면 틀린다

* ✗ 「소문자 이름은 캡처, 대문자 이름은 상수 비교」\
  ○ ★★★ **둘 다 캡처다.** 점이 가른다.
* ✗ 「캡처 함정은 컴파일러가 잡아 준다」\
  ○ **마지막 `case` 가 아닐 때만** 잡는다.
* ✗ 「`match` 는 빠진 경우를 경고한다」\
  ○ **경고 0건**이다(동작 7). Rust·Kotlin 과 다르다.

## 언제 쓰고 언제 안 쓰나

| 상황 | 고를 것 | 이유 |
|---|---|---|
| **모양**으로 가른다(길이·키·타입·속성) | ★ `match` | 분해와 조건이 한 줄에 온다 |
| 값 하나를 **상수 몇 개**와 견준다 | `match` + **점 있는 이름**, 또는 `dict` 조회 | 맨 이름을 쓰는 순간 캡처다 |
| 조건이 **범위·복합 비교**뿐이다 | `if`/`elif` | `match` 로 쓰면 가드만 줄줄이 붙는다 |
| 유한 집합을 **빠짐없이** 다뤄야 한다 | `match` + **`case _: raise`** | 파이썬은 완결성을 안 센다 |

## 핵심 문장

1. **점 없는 맨 이름은 캡처**다 — 대소문자와 무관하게 **무엇이든 맞고 그 이름을 덮어쓴다.**
2. **컴파일러는 캡처 뒤에 `case` 가 더 있을 때만 막는다** — 마지막 캡처는 **원리상 못 막는다.**
3. 컴파일 단계 `SyntaxError` 에는 **소스 줄도 캐럿도 없다** — 파서 진단(`**_`)에만 있다.
4. **시퀀스 패턴은 `abc.Sequence` 명부**를 보고 문자열을 뺀다. **매핑 패턴은 적은 키만** 본다.
5. **완결성 검사가 없다** — 빠진 경우는 경고 0건으로 `None` 이 된다. Rust 는 E0004 로 막는다.

## 관련 자료

* 선행: [11-tuple-and-unpacking](../11-tuple-and-unpacking/2-summary.md) — ★ **경계**: 언패킹 규칙은 그쪽, 여기는 **그것이 패턴이 될 때 무엇이 더해지나**(길이·`Sequence` 검사).
* 선행: [16-iterator-protocol](../16-iterator-protocol/2-summary.md) · [32-container-protocol](../32-container-protocol/2-summary.md) —
  ★ **경계**: 프로토콜은 그쪽. 여기서는 **시퀀스 패턴이 프로토콜이 아니라 ABC 명부를 본다**는 대비만(동작 5).
* 선행: [21-scope-legb-global-nonlocal](../21-scope-legb-global-nonlocal/2-summary.md) — 캡처가 지역 이름을 만드는 이유.
* 선행: [35-abc-and-protocol](../35-abc-and-protocol/2-summary.md) — `register` 가 명부에 올리는 것(동작 5 의 `RegBag`).
* 선행: [36-dataclasses](../36-dataclasses/2-summary.md) — `__match_args__` 를 만드는 쪽.
* 선행: [37-enum](../37-enum/2-summary.md) — `case Color.RED:` 의 멤버. ★ 멤버는 **싱글턴**이지만 값 패턴은 `is` 가 아니라 **`==`** 로 견준다.
* 옆: [38-namedtuple-and-typeddict](../38-namedtuple-and-typeddict/2-summary.md) — `NamedTuple` 도 `__match_args__` 를 갖는다(동작 6 의 ①).
* 대비: [Rust 18번 — `match` 와 완전성](../../../rust/syntax/18-match-and-exhaustiveness/2-summary.md) ·
  [Rust 19번 — 패턴 문법](../../../rust/syntax/19-pattern-syntax-guards-bindings-and-match-ergonomics/2-summary.md) ·
  [Kotlin 06번 — `when`](../../../kotlin/syntax/06-when-expression/2-summary.md) ·
  [Kotlin 23번 — `sealed` 와 `when` 완결성](../../../kotlin/syntax/23-sealed-classes-and-when-exhaustiveness/2-summary.md) ·
  [자바 23번 — `switch` 패턴 매칭](../../../java/syntax/23-switch-pattern-matching/2-summary.md).
  **경계**: 그쪽 진단 전문은 전부 그쪽이고 여기서는 인용만 했다.
* 공식 문서: [`match` 문](https://docs.python.org/3.12/reference/compound_stmts.html#the-match-statement) ·
  [PEP 634](https://peps.python.org/pep-0634/) · [PEP 636](https://peps.python.org/pep-0636/)

## 용어 풀이

* **패턴(pattern)**: `case` 뒤에 쓰는 모양 기술. **식이 아니다.**\
  예: `case red:` 의 `red` 는 읽는 게 아니라 대입할 자리다.
* **대상(subject)**: `match` 뒤에 쓴 값.
* **캡처 패턴**: 점 없는 맨 이름. **반드시 맞고** 대상을 그 이름에 묶는다.
* **와일드카드 패턴**: `_`. 반드시 맞고 **이름을 안 묶는다.**
* **값 패턴(value pattern)**: **점 있는 이름**(`Color.RED`). `==` 로 견준다.
* **리터럴 패턴**: 숫자·문자열·`None`·`True`·`False`. `None`·`True`·`False` 만 `is`.
* **반박 불가(irrefutable)**: 문법만 보고도 **반드시 맞는다**고 증명되는 것.\
  예: 캡처·와일드카드. **마지막 `case` 에만** 둘 수 있다.
* **가드(guard)**: `case 패턴 if 조건:` 의 조건. 패턴이 맞은 **뒤**에 따진다.
* **`__match_args__`**: 클래스 **위치 부분 패턴**을 어느 속성 이름으로 바꿀지 적은 튜플.\
  예: dataclass 가 `('x', 'y')` 를 자동으로 만든다.
* **소프트 키워드(soft keyword)**: 특정 자리에서만 키워드이고 나머지에서는 **보통 이름**인 낱말.\
  예: `match = [1, 2]` 가 된다.
* **완결성 검사(exhaustiveness check)**: 모든 경우를 다뤘는지 **컴파일러가 세는 것**. ★ **파이썬 `match` 에는 없다.**

## 더 들어가면

* ★ **중첩 패턴** — 패턴은 서로 안에 들어간다. `case {"pos": [x, y], "kind": Kind.A as k}:` 처럼 **매핑 안의 시퀀스 안의 캡처**가 된다.
  이 문서의 열한 종류가 전부 **다른 패턴의 부분 자리**에 올 수 있다.
* ★ **`__match_args__` 를 손으로 쓰기** — 일반 클래스에 `__match_args__ = ("x", "y")` 를 적으면 동작 6 의 `Plain(a, b)` 가 된다.
  **순서가 곧 계약**이다.
* ★ **값 패턴의 비교는 `==`** 라 [30번](../30-repr-eq-hash-contracts/2-summary.md)의 `__eq__` 를 재정의한 객체는 **그 규칙대로** 맞는다.
  [37번](../37-enum/2-summary.md)의 `IntEnum` 멤버를 값 패턴에 쓰면 **정수 `1` 도 맞는다**(동작 6 의 ⑦) — 그 편의 격자가 말한 「`int` 로서 답한다」가 여기서도 선다.
