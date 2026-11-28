# python/python-testing-deep/06 — pytest 마커 — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. `pytest.param` 으로 표시한 네 케이스 (예측)

```python
# 질문용 발췌
@pytest.mark.parametrize("val, expected", [
    (1, 1),
    pytest.param(0, 0, marks=pytest.mark.skip(reason="0 케이스 스킵")),
    pytest.param(-1, 1, marks=pytest.mark.xfail(reason="음수 미지원")),
    (2, 4),
])
def test_with_param_markers(val, expected):
    assert val ** 2 == expected
```

- 네 케이스는 각각 어떤 판정(통과 · 건너뜀 · XFAIL · XPASS · 실패)을 받는가?
- 이 함수 때문에 전체 테스트 실행이 실패로 끝나는가?

### 2. 조건부 xfail 이 붙은 `assert True` (예측)

```python
# 질문용 발췌
@pytest.mark.xfail(
    sys.platform == "darwin",
    reason="macOS에서 간헐적 실패"
)
def test_platform_specific():
    assert True
```

- macOS 에서 돌리면 어떤 판정을 받는가?
- Linux 에서 돌리면 어떤 판정을 받는가?

### 3. 마커 조합과 `-m` 식 (예측)

```python
# 질문용 발췌
@pytest.mark.slow
def test_heavy(): assert True

@pytest.mark.integration
def test_db(): assert True

@pytest.mark.integration
@pytest.mark.slow
def test_full(): assert True

def test_plain(): assert True
```

- `pytest -m "slow and integration"` 은 어느 테스트를 고르는가?
- `pytest -m "not slow"` 은 어느 테스트를 고르는가?
- `pytest -m "slow or integration"` 은 몇 개를 고르는가?

### 4. `xfail` 에 `strict=True` 를 붙이는 까닭 (왜)

- 알려진 버그의 테스트에 `strict=True` 를 붙이면 왜 「버그가 고쳐졌다」를 자동으로 알 수 있는가?

### 5. 커스텀 마커를 등록해야 하는 까닭 (왜)

- `slow` 같은 커스텀 마커를 pyproject.toml 이나 conftest.py 에 등록하지 않으면 무엇이 문제인가?

### 6. `skipif` 와 `pytest.skip()` 의 갈림 (경계)

- `pytest.skip()` 을 부른 뒤의 줄은 실행되는가?
- `skipif` 로는 판단할 수 없고 `pytest.skip()` 으로만 판단할 수 있는 조건은 어떤 것인가?

### 7. `importorskip` 이 건너뛰는 경우 (경계)

- `pytest.importorskip("numpy", minversion="1.20")` 은 numpy 가 없을 때, 1.19 일 때, 1.20 이상일 때 각각 어떻게 동작하는가?

### 8. 마커로 짜는 CI 전략 (연결)

- CI 와 야간 빌드에서 `-m` 을 어떻게 다르게 쓰면 빠른 피드백과 전체 검증을 둘 다 얻는가?

### 9. 파일을 `python` 으로 직접 실행하면 (예측)

- `python pytest-markers.py` 로 원본 파일을 실행하면 테스트 함수 중 몇 개가 불리고, 화면에는 무엇이 찍히는가?

## 실습

### 실습 1. 마커 종합 데모 파일 만들기

**만들 것** — skip · skipif · xfail · 실행 중 skip · 커스텀 마커 · 케이스별 마커를 한 파일에 모으고, 직접 실행하면 마커 요약표를 찍는 pytest 테스트 파일을 만든다.

**준비물** — `pytest` 패키지가 필요하다. `numpy` 는 없어도 된다(없으면 해당 테스트가 건너뛰어진다).

**요구 조건**

1단계 — 건너뛰기
1. `test_not_implemented` 는 몸통이 `assert False` 인데 언제나 건너뛰어져 실패하지 않는다.
2. `test_unix_only` 는 Windows 에서만 건너뛰고, 다른 곳에서는 `os.name == "posix"` 를 확인한다.
3. `test_taskgroup` 은 파이썬이 3.11 보다 낮으면 건너뛰고, 아니면 `asyncio` 에 `TaskGroup` 이 있는지 확인한다.

2단계 — 예상 실패
4. `test_known_bug` 는 `assert 1 + 1 == 3` 이 실패해도 XFAIL 로 처리된다.
5. `test_strict_xfail` 은 같은 단언을 쓰되, 만약 통과하면 실패로 보고되게 한다.
6. `test_platform_specific` 은 macOS 에서만 실패를 예상하게 표시한다.

3단계 — 실행 중 건너뛰기
7. `test_runtime_skip` 은 환경 변수 `API_KEY` 가 없으면 몸통 안에서 건너뛰고, 있으면 그 길이가 0보다 큰지 확인한다.
8. `test_importorskip` 은 numpy 1.20 이상을 가져오되 없거나 낮으면 건너뛰고, 가져온 모듈로 `[1, 2, 3]` 의 합이 6인지 확인한다.

4단계 — 커스텀 마커
9. `test_heavy_computation` 에 `slow` 마커를 붙인다.
10. `test_database_connection` 에 `integration` 마커를 붙인다.
11. `test_full_workflow` 에 `integration` 과 `slow` 를 둘 다 붙인다.

5단계 — 케이스별 마커
12. `test_with_param_markers` 의 네 케이스 중 `(0, 0)` 은 건너뛰고, `(-1, 1)` 은 실패를 예상하게 케이스 단위로 표시한다.

6단계 — 직접 실행
13. `python` 으로 직접 실행하면 내장 마커 6개를 `@pytest.mark.이름: 설명` 꼴로 찍는다.
14. 이어서 `-m` 필터 문법 다섯 줄과 pyproject.toml 마커 등록 예를 찍는다.

**시작 코드**

```python
import pytest
import sys
import os

# === skip ===
# TODO: 무조건 건너뛰기 (reason="아직 구현되지 않음")
def test_not_implemented():
    assert False

# === skipif ===
# TODO: sys.platform 이 "win32" 이면 건너뛰기 (reason="Windows에서는 지원하지 않음")
def test_unix_only():
    assert os.name == "posix"

# TODO: sys.version_info 가 (3, 11) 보다 작으면 건너뛰기 (reason="Python 3.11+ 필요 (TaskGroup)")
def test_taskgroup():
    import asyncio
    assert hasattr(asyncio, 'TaskGroup')

# === xfail ===
# TODO: 예상 실패 표시 (reason="알려진 버그 #123")
def test_known_bug():
    assert 1 + 1 == 3

# TODO: 통과하면 실패로 보고되는 예상 실패 (reason="반드시 실패해야 함")
def test_strict_xfail():
    assert 1 + 1 == 3

# TODO: sys.platform 이 "darwin" 일 때만 예상 실패 (reason="macOS에서 간헐적 실패")
def test_platform_specific():
    assert True

# === 런타임 skip ===
def test_runtime_skip():
    if not os.environ.get('API_KEY'):
        pass  # TODO: 여기서 건너뛰기 ("API_KEY 환경 변수 필요")
    assert len(os.environ['API_KEY']) > 0

def test_importorskip():
    """패키지 없으면 건너뛰기"""
    np = None  # TODO: numpy 1.20 이상을 가져오고, 없으면 건너뛰기
    assert np.array([1, 2, 3]).sum() == 6

# === 커스텀 마커 ===
# TODO: slow
def test_heavy_computation():
    result = sum(range(1000000))
    assert result > 0

# TODO: integration
def test_database_connection():
    assert True

# TODO: integration 과 slow 둘 다
def test_full_workflow():
    assert True

# === 파라미터별 마커 ===
@pytest.mark.parametrize("val, expected", [
    (1, 1),
    # TODO: (0, 0) 케이스 — skip 마커 (reason="0 케이스 스킵")
    # TODO: (-1, 1) 케이스 — xfail 마커 (reason="음수 미지원")
    (2, 4),
])
def test_with_param_markers(val, expected):
    assert val ** 2 == expected

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
    # TODO: 각 마커를 "  @pytest.mark.이름: 설명" 꼴로 찍기
    print()
    print("=== -m 필터 문법 ===")
    # TODO: "slow" · "not slow" · "a and b" · "a or b" · "not (a or b)" 다섯 줄
    print()
    print("=== 마커 등록 (pyproject.toml) ===")
    # TODO: [tool.pytest.ini_options] 와 markers 목록(slow, integration)
```

**확인 방법** — `pytest 파일이름.py -v -rsxX` 로 돌려 각 테스트의 판정(건너뜀 · XFAIL · XPASS 등)과 이유를 본다. `pytest 파일이름.py -m slow` · `-m "not slow"` 로 골라지는 테스트가 바뀌는지 본다. `python 파일이름.py` 로 요약표가 찍히는지 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
