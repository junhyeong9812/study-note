# python/python-testing-deep/06 — pytest 마커 — 정리 (힌트)

> 출처 — study-site 항목 `python/pytest-markers`(항목 데이터 `data/python/testing-deep.json`) · 정답 코드 study-practice `python/python-testing-deep/reference/pytest-markers.py`\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).\
> 실행 — 실행하지 않음 — 실행 환경 · 바깥 네트워크에 따라 달라지는 예제다.

## 한눈에 — 쉽게 말하면

**pytest 마커는 「시험지 묶음에 붙이는 포스트잇」이다.**
채점자는 시험지를 풀기 전에 포스트잇부터 본다.
「건너뜀」이 붙은 시험지는 아예 풀지 않는다.
「틀릴 줄 안다」가 붙은 시험지는 틀려도 감점하지 않고, 맞히면 「어? 맞았네」 하고 따로 적는다.
「오래 걸림」 · 「통합」 같은 분류 포스트잇은 채점자가 「오늘은 오래 걸림만 빼고 채점」처럼 묶음을 고를 때 쓴다.
pytest 도 똑같은 구조다.

| 비유 | 실체 |
|---|---|
| 시험지 | 테스트 함수 하나 (또는 `parametrize` 케이스 하나) |
| 포스트잇 | 마커 (`@pytest.mark.이름`) |
| 「건너뜀」 포스트잇 | `skip` · `skipif` |
| 「틀릴 줄 안다」 포스트잇 | `xfail` |
| 분류 포스트잇 | 커스텀 마커 (`slow` · `integration`) |
| 「오늘은 이것만 채점」 지시 | `pytest -m "식"` |
| 채점 기록의 표시 | 판정 기호 `.` · `s` · `x` · `X` · `F` |

```text
   테스트 함수들            마커 보기               판정
 ┌──────────────┐
 │ @skip        │ ──▶ 실행 안 함          ──▶  s (skipped)
 │ @xfail       │ ──▶ 실행 → 실패하면     ──▶  x (xfailed)
 │              │         → 통과하면     ──▶  X (xpassed)
 │ @slow        │ ──▶ -m "not slow" 면 선택에서 빠짐
 │ (마커 없음)   │ ──▶ 그냥 실행          ──▶  . 또는 F
 └──────────────┘
```

## 이 주제가 답하려는 질문

1. 테스트를 실행하지 않고 건너뛰려면 어떻게 하나 — 무조건 · 조건부 · 실행 도중에?
2. 이미 알고 있는 실패를 어떻게 표시하고, 그 버그가 고쳐졌을 때 어떻게 알아채나?
3. 테스트에 분류 이름표를 붙여 일부만 골라 돌리려면 어떻게 하나?
4. `parametrize` 케이스 여럿 가운데 하나에만 skip · xfail 을 붙이려면 어떻게 하나?

## 동작 방식

### (1) `skip` · `skipif` — 데코레이터로 미리 건너뛰기

**언제 쓰나** — 아직 구현하지 않은 기능의 테스트, 또는 특정 플랫폼 · 파이썬 버전에서만 의미 있는 테스트를 돌리지 않을 때 쓴다.

```text
@pytest.mark.skip(reason="아직 구현되지 않음")
def test_not_implemented(): assert False
        │
        ▼  pytest 가 마커를 보고 함수 몸통을 부르지 않는다
        ▼
   판정: s (skipped) — assert False 는 한 번도 실행되지 않는다

@pytest.mark.skipif(sys.platform == "win32", reason=...)
        │
        ▼  모듈을 불러오는 순간 조건식이 계산된다 → True / False
        ▼
   True  → 건너뜀 (s)
   False → 평소처럼 실행 (. 또는 F)
```

- `skip` 은 조건 없이 언제나 건너뛴다.
- 그래서 몸통이 `assert False` 여도 실패하지 않는다.
- `skipif` 는 첫 인자인 조건이 참일 때만 건너뛴다.
- 조건은 데코레이터 식이므로 테스트를 모을 때(모듈 import 때) 한 번 계산된다.
- 원본은 두 가지 조건을 쓴다 — 플랫폼(`sys.platform == "win32"`)과 파이썬 버전(`sys.version_info < (3, 11)`, `asyncio.TaskGroup` 은 3.11 부터 있다).
- `reason` 은 왜 건너뛰었는지 보고에 남는 글이다.

> **마커** — 테스트 함수에 붙이는 이름표. `@pytest.mark.이름` 꼴의 데코레이터다.\
> 예: `@pytest.mark.slow` 는 `slow` 라는 이름표를 붙인다.

> **수집(collection)** — pytest 가 파일을 import 해 테스트 함수를 찾아 모으는 단계.\
> 예: `skipif` 의 조건식은 이 단계에서 계산된다.

### (2) 실행 도중 건너뛰기 — `pytest.skip()` · `pytest.importorskip()`

**언제 쓰나** — 건너뛸지를 테스트 몸통 안에서 정하고 싶을 때(환경 변수 확인 등), 그리고 설치되지 않았을 수도 있는 선택적 패키지를 쓰는 테스트에 쓴다.

```text
def test_runtime_skip():
    if not os.environ.get('API_KEY'):
        pytest.skip("API_KEY 환경 변수 필요")   ← 여기서 예외가 던져진다
    assert len(os.environ['API_KEY']) > 0       ← API_KEY 가 없으면 여기까지 오지 않는다
        │
        ▼
   API_KEY 없음 → s (skipped)
   API_KEY 있음 → assert 실행 → . 또는 F

np = pytest.importorskip("numpy", minversion="1.20")
        │
        ├─ numpy 를 import 할 수 없다        → s (skipped)
        ├─ numpy 버전이 1.20 보다 낮다        → s (skipped)
        └─ 둘 다 아니다                       → numpy 모듈을 돌려준다 → 아래 줄 실행
```

- `pytest.skip()` 은 부르는 순간 테스트를 끝낸다.
- 그 뒤의 줄은 실행되지 않는다.
- 데코레이터와 달리 몸통 안의 어떤 값이든 보고 정할 수 있다.
- `pytest.importorskip("이름")` 은 import 가 되면 모듈을 돌려주고, 안 되면 테스트를 건너뛴다.
- `minversion` 을 주면 버전이 그보다 낮을 때도 건너뛴다.
- 그래서 선택적 의존성(없어도 프로젝트는 돌아가는 패키지)이 있는 테스트에 알맞다.

> **선택적 의존성** — 있으면 쓰고 없어도 핵심 기능은 돌아가는 외부 패키지.\
> 예: 계산 가속용으로만 쓰는 `numpy`.

### (3) `xfail` — 실패할 줄 아는 테스트

**언제 쓰나** — 이미 알려진 버그가 있어 지금은 실패하는 테스트를 지우지 않고 남겨 둘 때 쓴다.

```text
@pytest.mark.xfail(reason="알려진 버그 #123")
def test_known_bug(): assert 1 + 1 == 3
        │
        ▼  테스트를 실제로 실행한다 (skip 과 다르다)
        ▼
   실패 → x (XFAIL)  : 예상대로. 실패로 세지 않는다
   통과 → X (XPASS)  : 예상 밖. strict 가 아니면 실패로 세지 않는다

@pytest.mark.xfail(strict=True, reason=...)
        │
   실패 → x (XFAIL)
   통과 → 실패(F)로 보고된다  ← "버그가 고쳐졌다"는 신호

@pytest.mark.xfail(sys.platform == "darwin", reason=...)
        │
   조건 True  → xfail 처럼 다룬다
   조건 False → 마커가 없는 것처럼 평소대로 판정한다
```

- `xfail` 은 테스트를 건너뛰지 않고 실행한다.
- 실패하면 XFAIL 로 적히고, 전체 테스트 실행을 실패로 만들지 않는다.
- 통과하면 XPASS 로 적힌다.
- 기본(strict 아님)에서는 XPASS 도 전체 실행을 실패로 만들지 않는다 — 보고에 표시만 남는다.
- `strict=True` 면 XPASS 를 실패로 보고한다.
- 그래서 누군가 버그를 고쳐 테스트가 통과하기 시작하면, 실행이 깨지며 「xfail 표시를 떼라」고 자동으로 알려 준다.
- 첫 인자로 조건을 주면 그 조건이 참일 때만 xfail 로 다룬다.
- 원본의 `test_platform_specific` 은 몸통이 `assert True` 이므로 macOS 에서는 XPASS, 다른 플랫폼에서는 그냥 통과다.

> **XFAIL** — xfail 표시한 테스트가 예상대로 실패한 판정.\
> 예: `assert 1 + 1 == 3` 에 xfail 을 붙인 테스트.

> **XPASS** — xfail 표시한 테스트가 예상과 달리 통과한 판정.\
> 예: `assert True` 에 xfail 을 붙인 테스트.

### (4) 커스텀 마커와 `-m` 필터

**언제 쓰나** — 느린 테스트 · 통합 테스트처럼 성격이 다른 테스트를 분류해, 상황에 따라 일부만 돌릴 때 쓴다.

```text
@pytest.mark.slow                      → {slow}
def test_heavy_computation(): ...

@pytest.mark.integration               → {integration}
def test_database_connection(): ...

@pytest.mark.integration
@pytest.mark.slow                      → {integration, slow}
def test_full_workflow(): ...
        │
        ▼  pytest -m "식"  — 식을 각 테스트의 마커 집합에 대 본다
        ▼
   -m slow                    → heavy, full
   -m "not slow"              → database (그리고 마커 없는 테스트 전부)
   -m "slow and integration"  → full
   -m "slow or integration"   → heavy, database, full
   -m "not (a or b)"          → a 도 b 도 없는 테스트
```

- `slow` · `integration` 같은 이름은 pytest 가 미리 아는 것이 아니다 — 직접 지어 붙인다.
- 한 테스트에 마커를 여럿 겹쳐 붙일 수 있다.
- `-m` 뒤의 식은 마커 이름에 `and` · `or` · `not` · 괄호를 써서 만든다.
- 식이 참인 테스트만 골라 실행한다.
- 커스텀 마커는 등록해야 한다.
- 등록하지 않은 마커를 쓰면 pytest 가 경고를 낸다.
- 등록하는 자리는 세 가지다.

```text
pytest.ini / pyproject.toml 의 markers 목록
conftest.py 의 pytest_configure 훅 안 config.addinivalue_line("markers", "slow: 느린 테스트")
```

- 등록 글의 꼴은 `"이름: 설명"` 이다.
- 활용 전략: CI 에서는 `-m "not slow"` 로 빠른 테스트만 돌리고, 야간 빌드에서 전체를 돌린다.

> **CI** — 코드를 올릴 때마다 자동으로 빌드 · 테스트하는 체계.\
> 예: 풀 리퀘스트마다 `pytest -m "not slow"` 를 돌린다.

> **conftest.py** — pytest 가 자동으로 읽는 설정 · 픽스처 파일.\
> 예: 여기에 `pytest_configure` 를 정의해 마커를 등록한다.

### (5) `pytest.param` — 케이스 하나에만 마커 붙이기

**언제 쓰나** — `parametrize` 로 여러 입력을 돌리는데, 그중 일부 입력만 건너뛰거나 실패를 예상할 때 쓴다.

```text
@pytest.mark.parametrize("val, expected", [
    (1, 1),                                              → 보통 케이스
    pytest.param(0, 0, marks=pytest.mark.skip(...)),     → 이 케이스만 skip
    pytest.param(-1, 1, marks=pytest.mark.xfail(...)),   → 이 케이스만 xfail
    (2, 4),                                              → 보통 케이스
])
def test_with_param_markers(val, expected):
    assert val ** 2 == expected
        │
        ▼  케이스마다 테스트가 하나씩 생기고, 마커도 케이스마다 따로 적용된다
```

- 보통 케이스는 튜플로 쓴다.
- 마커를 붙일 케이스만 `pytest.param(값들..., marks=마커)` 로 감싼다.
- 마커는 그 케이스 하나에만 적용되고, 같은 함수의 다른 케이스는 영향을 받지 않는다.
- xfail 이 붙은 케이스도 실제로 실행되므로, (3) 의 XFAIL / XPASS 규칙이 그대로 적용된다.

> **parametrize** — 한 테스트 함수를 여러 입력으로 여러 번 돌리는 내장 마커.\
> 예: `@pytest.mark.parametrize("val, expected", [(1, 1), (2, 4)])`.

### (6) `if __name__ == '__main__':` 블록 — 파일을 직접 실행할 때

**언제 쓰나** — 원본은 이 블록으로 마커 요약표를 찍는다.

```text
python pytest-markers.py
        │
        ▼  모듈 맨 위부터 실행: import, 함수 정의(데코레이터 적용)까지만
        ▼  test_ 함수는 정의만 되고 불리지 않는다
        ▼
   __main__ 블록 실행 → print 만 차례로 실행된다
     1) "=== 내장 마커 ===" + 마커 6개 (skip, skipif, xfail, parametrize, usefixtures, filterwarnings)
     2) "=== -m 필터 문법 ===" + 식 5줄
     3) "=== 마커 등록 (pyproject.toml) ===" + 등록 예
```

- 테스트를 실행하는 것은 `pytest` 명령이지, `python` 으로 파일을 돌리는 것이 아니다.
- `python` 으로 직접 돌리면 테스트 함수는 하나도 불리지 않는다.
- 이 블록이 소개하는 내장 마커는 여섯 개다 — `skip`(무조건 건너뛰기) · `skipif`(조건부 건너뛰기) · `xfail`(예상 실패) · `parametrize`(파라미터화) · `usefixtures`(fixture 사용 선언) · `filterwarnings`(경고 필터).

## 문법 — 형태와 규칙

```python
import pytest, sys

@pytest.mark.skip(reason="미구현")
def test_a(): ...

@pytest.mark.skipif(sys.version_info < (3, 11), reason="3.11+ 필요")
def test_b(): ...

@pytest.mark.xfail(strict=True, reason="버그 #1")
def test_c(): assert 1 == 2

@pytest.mark.slow
def test_d(): ...

def test_e():
    mod = pytest.importorskip("numpy", minversion="1.20")
    if mod is None:
        pytest.skip("여기 오지 않는다")
```

| 꼴 | 하는 일 |
|---|---|
| `@pytest.mark.skip(reason=...)` | 언제나 건너뜀 |
| `@pytest.mark.skipif(조건, reason=...)` | 조건이 참이면 건너뜀 |
| `@pytest.mark.xfail(reason=...)` | 실패를 예상. 실패 → XFAIL, 통과 → XPASS |
| `@pytest.mark.xfail(strict=True, ...)` | 통과하면 실패로 보고 |
| `@pytest.mark.xfail(조건, reason=...)` | 조건이 참일 때만 xfail |
| `pytest.skip("이유")` | 몸통 안에서 즉시 건너뜀 |
| `pytest.importorskip("모듈", minversion="x")` | 모듈을 돌려주거나 건너뜀 |
| `@pytest.mark.이름` | 커스텀 마커 (등록 필요) |
| `pytest.param(값..., marks=마커)` | `parametrize` 케이스 하나에 마커 |
| `pytest -m "식"` | 식에 맞는 마커의 테스트만 실행 |

- 마커 데코레이터는 여러 개 겹쳐 붙일 수 있다.
- `-m` 식에는 `and` · `or` · `not` · 괄호를 쓴다.
- 식에 공백이 들어가면 셸에서 따옴표로 감싼다.
- 커스텀 마커 등록 (pyproject.toml):

```text
[tool.pytest.ini_options]
markers = [
    "slow: 느린 테스트",
    "integration: 통합 테스트",
]
```

## 어디서 틀리나

### 1. 커스텀 마커를 등록하지 않는다

등록하지 않은 마커를 쓰면 pytest 가 경고를 낸다.
마커 이름에 오타가 나도 그 경고 말고는 알아챌 길이 없다 — `-m slow` 로 골랐는데 `@pytest.mark.slwo` 가 붙은 테스트는 조용히 빠진다.
원본 팁은 이를 「-W 경고를 방지」라고 적었다.
`-W` 는 경고를 다루는 명령줄 옵션의 이름이라 표현이 정확하지 않다 — 등록하면 미등록 마커 경고가 나지 않는다는 뜻으로 읽어야 한다 (원본에 근거 없음 — 추론).
원본 정답 코드도 등록을 주석으로만 보여 주므로, 그대로 돌리면 `slow` · `integration` 에 대한 경고가 날 것이다 (원본에 근거 없음 — 추론).

### 2. xfail 을 붙여 놓고 잊는다

strict 가 아닌 xfail 은 테스트가 통과해도(XPASS) 실행을 깨지 않는다.
버그가 고쳐졌는데도 아무도 모르고, xfail 표시가 계속 남는다.
`strict=True` 를 붙이면 XPASS 가 실패로 보고되어 고쳐진 것을 자동으로 감지한다.

### 3. xfail 케이스가 실제로는 통과한다

원본의 `pytest.param(-1, 1, marks=pytest.mark.xfail(reason="음수 미지원"))` 을 보자.
`(-1) ** 2` 는 `1` 이므로 `assert val ** 2 == expected` 는 참이다.
따라서 이 케이스는 XFAIL 이 아니라 XPASS 가 된다 (원본에 근거 없음 — 추론).
원본의 주장(「음수 미지원」이라 실패할 것) → 의심스러운 까닭: 단언 자체가 음수에서 성립한다.
strict 가 아니므로 실행이 깨지지는 않지만, 표시와 실제가 어긋난다.

### 4. skip 과 xfail 을 헷갈린다

`skip` 은 몸통을 실행하지 않는다.
`xfail` 은 몸통을 실행한다.
그래서 xfail 테스트가 무한 루프에 빠지거나 오래 걸리면 그 시간은 그대로 든다.
「실패해도 된다」와 「돌리지 않는다」는 다른 말이다.

### 5. `pytest.skip()` 뒤에 코드가 실행될 거라 생각한다

`pytest.skip()` 은 그 자리에서 테스트를 끝낸다.
그 뒤 줄은 실행되지 않는다.

### 6. `skipif` 조건이 테스트 실행 때 계산될 거라 생각한다

조건식은 데코레이터 식이라 모듈 import 때 계산된다.
테스트 몸통에서 만들어지는 값이나 픽스처가 준비한 값을 볼 수 없다.
그런 판단은 몸통 안의 `pytest.skip()` 으로 한다.

### 7. 선택적 의존성을 그냥 `import` 한다

파일 맨 위에서 `import numpy` 를 하면 numpy 가 없는 환경에서 파일 전체가 import 오류로 깨진다.
원본 팁대로 `pytest.importorskip` 을 쓰면 그 테스트만 건너뛴다.

### 8. 느린 테스트를 매번 다 돌린다

원본 팁: CI 에서는 `-m "not slow"` 만 돌리고, 야간 빌드에서 전체를 돌리는 전략이 효과적이다.
이 전략은 느린 테스트에 `slow` 마커를 빠짐없이 붙였을 때만 통한다.

### 9. `python 파일.py` 로 테스트를 돌렸다고 생각한다

`python` 으로 직접 실행하면 `test_` 함수는 정의만 되고 불리지 않는다.
원본에서는 `__main__` 블록의 print 만 실행된다.

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| 데코레이터 식(`skipif` 조건)은 함수 정의 때 계산된다 | 파이썬 언어 |
| `sys.version_info < (3, 11)` 은 튜플을 앞에서부터 비교한다 | 파이썬 언어 |
| Windows 에서 `sys.platform` 이 `"win32"`, macOS 에서 `"darwin"` 이다 | 파이썬 표준 라이브러리 문서 (확인 필요) |
| `asyncio.TaskGroup` 은 3.11 부터 있다 | 파이썬 표준 라이브러리 (버전별) |
| skip · xfail 판정, XFAIL · XPASS, `strict` 의 의미 | pytest (라이브러리) — 언어와 무관 |
| 미등록 마커에 경고를 낸다 | pytest — 경고의 정확한 이름 · 동작은 버전에 따라 다를 수 있다 (확인 필요) |
| `-m` 식의 문법 (`and` · `or` · `not` · 괄호) | pytest |
| `importorskip` 의 `minversion` 비교 | pytest |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 아직 구현 안 된 기능 | `skip` | 테스트 함수를 주석 처리 |
| 특정 OS · 파이썬 버전 전용 | `skipif` | 몸통 안의 `if` 로 그냥 `return` (통과로 보인다) |
| 몸통 안에서야 알 수 있는 조건 | `pytest.skip()` | `skipif` |
| 없을 수도 있는 패키지 | `pytest.importorskip` | 파일 맨 위 `import` |
| 알려진 버그, 고쳐지면 알고 싶다 | `xfail(strict=True)` | 테스트 삭제 · strict 없는 xfail 방치 |
| 느린 · 통합 테스트 분류 | 등록한 커스텀 마커 + `-m` | 등록 안 한 마커 |
| `parametrize` 의 일부 케이스만 예외 | `pytest.param(..., marks=...)` | 함수 전체에 skip · xfail |

## 핵심 문장

1. **skip 은 실행하지 않고, xfail 은 실행한다** — xfail 은 실패하면 XFAIL, 통과하면 XPASS 다.
2. **`strict=True` 는 XPASS 를 실패로 바꾼다** — 그래서 버그가 고쳐진 순간을 자동으로 알려 준다.
3. **`skipif` 는 import 때, `pytest.skip()` 은 실행 중에 정한다.**
4. **커스텀 마커는 이름표다** — 등록하고, `-m` 의 `and` · `or` · `not` 식으로 골라 돌린다.
5. **`pytest.param(marks=...)` 는 마커를 케이스 하나에만 붙인다.**

## 관련 자료

- [pytest-parametrize](../02-pytest-parametrize/2-summary.md)
- `pytest-conftest` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- `pytest-fixtures` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- 원본: study-site 항목 데이터 `data/python/testing-deep.json` 의 `pytest-markers`

## 용어 풀이

- **마커** — 테스트에 붙이는 이름표 데코레이터 (`@pytest.mark.이름`).
- **skip** — 테스트를 실행하지 않고 건너뛰는 마커.
- **skipif** — 조건이 참일 때만 건너뛰는 마커.
- **xfail** — 실패를 예상한다고 표시하는 마커. 테스트는 실행된다.
- **XFAIL** — xfail 테스트가 예상대로 실패한 판정.
- **XPASS** — xfail 테스트가 예상과 달리 통과한 판정.
- **strict** — xfail 의 인자. 참이면 XPASS 를 실패로 보고한다.
- **커스텀 마커** — 사용자가 이름을 지어 붙이는 분류 마커 (`slow` · `integration`).
- **마커 등록** — 커스텀 마커 이름을 설정 파일이나 conftest.py 에 알려 두는 일.
- **`-m` 필터** — 마커 식에 맞는 테스트만 고르는 pytest 명령줄 옵션.
- **`pytest.skip()`** — 테스트 몸통 안에서 즉시 건너뛰게 하는 함수.
- **`pytest.importorskip()`** — 모듈 import 를 시도해, 안 되면 건너뛰는 함수.
- **`pytest.param`** — `parametrize` 케이스 하나를 감싸 마커 등을 붙이는 함수.
- **parametrize** — 한 테스트를 여러 입력으로 돌리는 내장 마커.
- **usefixtures** — 테스트가 쓸 fixture 를 선언하는 내장 마커.
- **filterwarnings** — 테스트 안 경고를 거르는 내장 마커.
- **수집(collection)** — pytest 가 테스트를 찾아 모으는 단계.
- **conftest.py** — pytest 가 자동으로 읽는 설정 · 픽스처 파일.
- **선택적 의존성** — 없어도 핵심 기능은 도는 외부 패키지.
- **CI** — 변경마다 자동으로 빌드 · 테스트하는 체계.
- **야간 빌드** — 하루 한 번 등 정해진 때 전체를 빌드 · 테스트하는 일.

## 더 들어가면

- `-m` 은 마커로 고르고, `-k` 는 테스트 이름(함수 · 클래스 이름 등)의 부분 문자열 식으로 고른다 (확인 필요).
- `--strict-markers` 옵션을 주면 미등록 마커가 경고가 아니라 오류가 된다 (확인 필요).
- 설정 파일의 `xfail_strict = true` 로 모든 xfail 의 기본을 strict 로 바꿀 수 있다 (확인 필요).
- `--runxfail` 을 주면 xfail 표시를 무시하고 보통 테스트처럼 판정한다 (확인 필요).
- `xfail(raises=SomeError)` 로 특정 예외로 실패할 때만 XFAIL 로 인정하게 할 수 있다 (확인 필요).
- `xfail(run=False)` 는 몸통을 실행하지 않고 xfail 로 표시한다 (확인 필요).
- `pytest --markers` 는 등록된 마커 목록을 보여 준다 (확인 필요).
- `pytest -rsxX` 처럼 `-r` 뒤 글자를 주면 건너뜀 · XFAIL · XPASS 의 이유를 요약에 보여 준다.
- 파일 이름이 기본 수집 규칙(`test_*.py` · `*_test.py`)에 맞지 않아도, 명령줄에 파일 경로를 직접 주면 수집된다 (확인 필요).
