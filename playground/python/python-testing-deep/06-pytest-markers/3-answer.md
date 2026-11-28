# python/python-testing-deep/06 — pytest 마커 — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 통과 · 건너뜀 · XPASS · 통과 — 전체 실행은 실패하지 않는다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

- `(1, 1)`: `1 ** 2 == 1` 이 참 → 통과.
- `(0, 0)`: skip 마커 → 몸통을 실행하지 않고 건너뜀.
- `(-1, 1)`: xfail 마커지만 `(-1) ** 2 == 1` 이 참 → 통과하므로 XPASS.
- `(2, 4)`: `2 ** 2 == 4` 가 참 → 통과.
- xfail 이 strict 가 아니므로 XPASS 는 전체 실행을 실패로 만들지 않는다.

**왜 그런가**
`pytest.param(..., marks=...)` 의 마커는 그 케이스 하나에만 적용된다 (2-summary 「동작 방식 (5)」).
xfail 은 몸통을 실제로 실행하고, 통과하면 XPASS 이며 strict 가 아니면 실패로 세지 않는다 (2-summary 「동작 방식 (3)」).
「음수 미지원」이라는 이유 글과 달리 단언이 성립한다는 점은 2-summary 「어디서 틀리나 3」에 있다 (원본에 근거 없음 — 추론).

### 2. macOS 에서는 XPASS, Linux 에서는 그냥 통과

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

- macOS: 조건 `sys.platform == "darwin"` 이 참 → xfail 로 다룬다 → `assert True` 가 통과 → XPASS.
- strict 가 아니므로 실행을 깨지 않는다.
- Linux: 조건이 거짓 → 마커가 없는 것처럼 판정 → 통과.

**왜 그런가**
조건부 xfail 은 조건이 참일 때만 xfail 로 다루고, 거짓이면 평소대로 판정한다 (2-summary 「동작 방식 (3)」).

### 3. `and` 는 둘 다 가진 것만, `not` 은 없는 것 전부

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

- `-m "slow and integration"` → `test_full` 하나.
- `-m "not slow"` → `test_db` 와 `test_plain` (마커가 없는 테스트도 `slow` 가 없으므로 고른다).
- `-m "slow or integration"` → `test_heavy` · `test_db` · `test_full` 세 개.

**왜 그런가**
`-m` 은 식을 각 테스트의 마커 집합에 대 보고 참인 것만 고른다 (2-summary 「동작 방식 (4)」).
마커를 여러 개 겹쳐 붙이면 그 테스트의 집합에 모두 들어간다.

### 4. 버그가 고쳐지면 XPASS 가 실패로 보고되기 때문이다

strict 가 아닌 xfail 은 테스트가 통과해도(XPASS) 표시만 남기고 실행을 깨지 않는다.
`strict=True` 면 XPASS 가 실패로 보고된다.
버그가 고쳐지면 그 테스트가 통과하기 시작하므로 실행이 깨지고, 「xfail 표시를 떼라」는 신호가 된다.
근거: 2-summary 「동작 방식 (3)」 · 「어디서 틀리나 2」.

### 5. 경고가 나고, 오타를 알아챌 길이 없어진다

등록하지 않은 마커를 쓰면 pytest 가 경고를 낸다.
또 마커 이름에 오타가 나면 `-m` 으로 고를 때 그 테스트가 조용히 빠진다.
등록 자리는 pytest.ini · pyproject.toml 의 `markers` 목록이나 conftest.py 의 `pytest_configure` 안 `config.addinivalue_line("markers", ...)` 이다.
근거: 2-summary 「동작 방식 (4)」 · 「어디서 틀리나 1」.

### 6. 뒤 줄은 실행되지 않는다 — 몸통 안에서 생기는 값은 `pytest.skip()` 만 볼 수 있다

`pytest.skip()` 은 부르는 순간 테스트를 끝내므로 그 뒤 줄은 실행되지 않는다.
`skipif` 의 조건은 데코레이터 식이라 모듈 import 때 한 번 계산된다.
그래서 테스트 몸통이 실행되며 만들어지는 값이나 픽스처가 준비한 값처럼, 실행 중에야 알 수 있는 조건은 `pytest.skip()` 으로만 판단할 수 있다.
근거: 2-summary 「동작 방식 (1)」 · 「동작 방식 (2)」 · 「어디서 틀리나 5 · 6」.

### 7. 없거나 1.19 면 건너뛰고, 1.20 이상이면 모듈을 돌려준다

- numpy 가 없다 → import 실패 → 테스트를 건너뛴다.
- numpy 1.19 → `minversion` 보다 낮다 → 건너뛴다.
- numpy 1.20 이상 → numpy 모듈을 돌려주고 다음 줄이 실행된다.

근거: 2-summary 「동작 방식 (2)」.

### 8. CI 는 `-m "not slow"`, 야간 빌드는 전체

변경마다 도는 CI 에서는 `pytest -m "not slow"` 로 느린 테스트를 빼 빠르게 피드백을 받는다.
야간 빌드에서는 `-m` 없이 전체를 돌려 느린 테스트까지 검증한다.
이 전략은 느린 테스트마다 `slow` 마커를 빠짐없이 붙이고 등록해 두었을 때만 통한다.
근거: 2-summary 「동작 방식 (4)」 · 「어디서 틀리나 8」.

### 9. 테스트는 하나도 불리지 않고, 요약표만 찍힌다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

- `test_` 함수는 정의(데코레이터 적용)까지만 되고 하나도 불리지 않는다.
- `__main__` 블록의 print 만 차례로 실행된다.
- 먼저 `=== 내장 마커 ===` 아래 `@pytest.mark.skip: 무조건 건너뛰기` 꼴로 여섯 줄이 찍힐 것이다.
- 이어서 `=== -m 필터 문법 ===` 아래 식 다섯 줄, `=== 마커 등록 (pyproject.toml) ===` 아래 `[tool.pytest.ini_options]` 와 `markers` 목록이 찍힐 것이다.

**왜 그런가**
테스트를 부르는 것은 `pytest` 명령이고, `python` 으로 직접 돌리면 모듈 맨 위부터 실행되며 `__main__` 블록만 동작한다 (2-summary 「동작 방식 (6)」 · 「어디서 틀리나 9」).

## 실습 정답

### 실습 1. 마커 종합 데모 파일 만들기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. 언제나 건너뜀 | `@pytest.mark.skip(reason=...)` on `test_not_implemented` |
| 2. Windows 에서만 건너뜀 | `@pytest.mark.skipif(sys.platform == "win32", ...)` on `test_unix_only` |
| 3. 3.11 미만이면 건너뜀 | `@pytest.mark.skipif(sys.version_info < (3, 11), ...)` on `test_taskgroup` |
| 4. 실패해도 XFAIL | `@pytest.mark.xfail(reason="알려진 버그 #123")` on `test_known_bug` |
| 5. 통과하면 실패로 보고 | `@pytest.mark.xfail(strict=True, ...)` on `test_strict_xfail` |
| 6. macOS 에서만 실패 예상 | `@pytest.mark.xfail(sys.platform == "darwin", ...)` on `test_platform_specific` |
| 7. `API_KEY` 없으면 실행 중 건너뜀 | `pytest.skip("API_KEY 환경 변수 필요")` in `test_runtime_skip` |
| 8. numpy 1.20 이상, 없으면 건너뜀 | `pytest.importorskip("numpy", minversion="1.20")` in `test_importorskip` |
| 9. `slow` 마커 | `@pytest.mark.slow` on `test_heavy_computation` |
| 10. `integration` 마커 | `@pytest.mark.integration` on `test_database_connection` |
| 11. 두 마커 모두 | `@pytest.mark.integration` + `@pytest.mark.slow` on `test_full_workflow` |
| 12. 케이스별 skip · xfail | `pytest.param(0, 0, marks=pytest.mark.skip(...))` · `pytest.param(-1, 1, marks=pytest.mark.xfail(...))` |
| 13. 내장 마커 6개 출력 | `for name, desc in markers.items(): print(f"  @pytest.mark.{name}: {desc}")` |
| 14. `-m` 문법 · 등록 예 출력 | `__main__` 블록 뒤쪽의 `print('  pytest -m ...')` 다섯 줄과 `print('[tool.pytest.ini_options]')` 이하 |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`python/python-testing-deep/reference/pytest-markers.py`

```python
# [테스팅 심화] pytest 마커
# 설명: mark.skip, mark.xfail, 커스텀 마커, -m 필터를 이용한 선택적 테스트 실행
# 팁: 커스텀 마커는 pytest.ini나 pyproject.toml에 등록해야 -W 경고를 방지한다. xfail(strict=True)는 실패가 수정되었는지 자동 감지한다. pytest.importorskip은 선택적 의존성이 있는 테스트에 유용하다. -m 옵션으로 CI에서는 'not slow'만 실행하고, 야간 빌드에서 전체를 실행하는 전략이 효과적이다.

# pytest: 마커와 skip 함수 제공
import pytest
# sys: 플랫폼/버전 감지용
import sys
# os: 환경 변수 확인용
import os

# === skip: 무조건 건너뛰기 ===
# @pytest.mark.skip: 항상 스킵 (구현 미완료 등)
@pytest.mark.skip(reason="아직 구현되지 않음")
def test_not_implemented():
    assert False  # 실행되지 않음

# === skipif: 조건부 건너뛰기 ===
# @pytest.mark.skipif: 조건 True일 때만 스킵 (플랫폼별 분기)
@pytest.mark.skipif(
    sys.platform == "win32",
    reason="Windows에서는 지원하지 않음"
)
def test_unix_only():
    assert os.name == "posix"

# Python 버전 분기 (TaskGroup은 3.11+)
@pytest.mark.skipif(
    sys.version_info < (3, 11),
    reason="Python 3.11+ 필요 (TaskGroup)"
)
def test_taskgroup():
    import asyncio
    assert hasattr(asyncio, 'TaskGroup')

# === xfail: 예상 실패 ===
# @pytest.mark.xfail: 실패가 예상됨 - 실패해도 테스트 전체는 통과
@pytest.mark.xfail(reason="알려진 버그 #123")
def test_known_bug():
    # 실패가 예상됨 → xfail로 표시 (실패해도 테스트 통과)
    assert 1 + 1 == 3

# strict=True: 통과하면 오히려 XPASS(실패) - 버그 수정 자동 감지
@pytest.mark.xfail(strict=True, reason="반드시 실패해야 함")
def test_strict_xfail():
    # strict=True: 만약 통과하면 오히려 XPASS(실패)로 보고
    assert 1 + 1 == 3

# 조건부 xfail (특정 플랫폼에서만 실패 예상)
@pytest.mark.xfail(
    sys.platform == "darwin",
    reason="macOS에서 간헐적 실패"
)
def test_platform_specific():
    assert True

# === 런타임 skip ===
# 테스트 함수 내에서 동적으로 스킵 결정
def test_runtime_skip():
    if not os.environ.get('API_KEY'):
        # pytest.skip(): 실행 중 스킵
        pytest.skip("API_KEY 환경 변수 필요")
    # API_KEY가 있을 때만 실행
    assert len(os.environ['API_KEY']) > 0

# importorskip: 선택적 의존성이 없으면 스킵
def test_importorskip():
    """패키지 없으면 건너뛰기"""
    np = pytest.importorskip("numpy", minversion="1.20")
    assert np.array([1, 2, 3]).sum() == 6

# === 커스텀 마커 ===
# conftest.py에 등록:
# def pytest_configure(config):
#     config.addinivalue_line("markers", "slow: 느린 테스트")
#     config.addinivalue_line("markers", "integration: 통합 테스트")

# 커스텀 마커: 테스트 분류용 - pytest -m slow 로 선택 실행
@pytest.mark.slow
def test_heavy_computation():
    result = sum(range(1000000))
    assert result > 0

@pytest.mark.integration
def test_database_connection():
    # DB 연결 테스트
    assert True

# 마커 다중 부착 - "slow AND integration" 모두 매칭
@pytest.mark.integration
@pytest.mark.slow
def test_full_workflow():
    # 여러 마커 조합 가능
    assert True

# === 파라미터별 마커 ===
# pytest.param: 개별 케이스에 마커 부착 (선택적 skip/xfail)
@pytest.mark.parametrize("val, expected", [
    (1, 1),
    pytest.param(0, 0, marks=pytest.mark.skip(reason="0 케이스 스킵")),
    pytest.param(-1, 1, marks=pytest.mark.xfail(reason="음수 미지원")),
    (2, 4),
])
def test_with_param_markers(val, expected):
    assert val ** 2 == expected

# 실행 예시:
# pytest -m slow              # slow 마커만
# pytest -m "not slow"        # slow 제외
# pytest -m "integration"     # integration만
# pytest -m "slow and integration"  # 둘 다
# pytest -m "slow or integration"   # 둘 중 하나

if __name__ == '__main__':
    print("=== 내장 마커 ===")
    markers = {
        "skip":     "무조건 건너뛰기",
        "skipif":   "조건부 건너뛰기",
        "xfail":    "예상 실패 (실패해도 OK)",
        "parametrize": "파라미터화",
        "usefixtures": "fixture 사용 선언",
        "filterwarnings": "경고 필터",
    }
    for name, desc in markers.items():
        print(f"  @pytest.mark.{name}: {desc}")
    print()
    print("=== -m 필터 문법 ===")
    print('  pytest -m "slow"           # slow만')
    print('  pytest -m "not slow"       # slow 제외')
    print('  pytest -m "a and b"        # 둘 다')
    print('  pytest -m "a or b"         # 둘 중 하나')
    print('  pytest -m "not (a or b)"   # 둘 다 아닌 것')
    print()
    print("=== 마커 등록 (pyproject.toml) ===")
    print('[tool.pytest.ini_options]')
    print('markers = [')
    print('    "slow: 느린 테스트",')
    print('    "integration: 통합 테스트",')
    print(']')
```

**실행 결과** — 실행하지 않음 — 실행 환경 · 바깥 네트워크에 따라 달라지는 예제다.

**풀이 요점**

- skip 계열(`skip` · `skipif` · `pytest.skip` · `importorskip`)은 몸통을 실행하지 않거나 중간에 끊고, `xfail` 은 몸통을 끝까지 실행한다.
- `skipif` · 조건부 `xfail` 의 조건은 import 때 계산되고, `API_KEY` 확인은 몸통 안에서 한다.
- `(-1, 1)` 케이스는 단언이 성립하므로 XPASS 가 될 것이다 — strict 가 아니라 실행을 깨지는 않는다 (원본에 근거 없음 — 추론).
- 정답 코드는 마커 등록을 주석으로만 보여 주므로, 그대로 돌리면 `slow` · `integration` 에 미등록 경고가 날 것이다 — 경고를 없애려면 pyproject.toml 이나 conftest.py 에 등록한다 (원본에 근거 없음 — 추론).
- `__main__` 블록은 요약표를 찍을 뿐 테스트를 돌리지 않는다 — 테스트는 `pytest` 로 돌린다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — 실행 환경 · 바깥 네트워크에 따라 달라지는 예제다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
