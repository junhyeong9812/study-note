# python/python-testing-deep/10 — 코드 커버리지 — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 빈 리스트를 넣은 `process` (예측)

```python
# 질문용 발췌
def process(self, data):
    if not data:
        return None
    results = []
    # ... (반복 처리) ...
    return results

def test_process_empty(self, calc):
    assert calc.process([]) == []
```

- `calc.process([])` 는 무엇을 돌려주고, 이 테스트는 통과하는가?

### 2. 정상 경로 테스트 하나만 있는 `divide` (예측)

```python
# 질문용 발췌
def divide(self, a, b):
    if b == 0:
        raise ZeroDivisionError("0으로 나눌 수 없습니다")
    return a / b

def test_divide(self, calc):
    assert calc.divide(10, 2) == 5
```

- 테스트가 `test_divide` 하나뿐일 때 `--cov-report=term-missing` 의 미커버 줄로 나올 줄은 어느 것인가?

### 3. 음수 하나로만 테스트한 `clamp` (예측)

```python
# 질문용 발췌
def clamp(x):
    if x < 0:
        x = 0
    return x

# 테스트: clamp(-5) 하나만
```

- 이 함수의 라인 커버리지는 몇 % 이고, 브랜치 커버리지에는 무엇이 미커버로 남는가?

### 4. `test_process_mixed` 의 입력에서 `None` 을 빼면 (예측)

- 입력을 `[1, "hello", 2.5, "world"]` 로 바꾸면 `process` 의 `continue` 줄은 커버되는가?

### 5. 브랜치 커버리지를 더 의미 있다고 하는 이유 (왜)

- 라인 커버리지가 100% 인데도 브랜치 커버리지가 빈틈을 찾아낼 수 있는 까닭은 무엇인가?

### 6. 커버리지가 높아도 품질을 보장하지 못하는 이유 (왜)

- 커버리지 90% 인 프로젝트에서도 버그가 그대로 숨어 있을 수 있는 까닭은 무엇인가?

### 7. 제외 표시를 어디까지 써도 되나 (경계)

- `pragma: no cover` · `exclude_lines` 로 빼도 되는 코드와 빼면 안 되는 코드는 어떻게 가르는가?

### 8. 짧은 제외 패턴 `"pass"` 가 닿는 범위 (경계)

- 제외 패턴이 줄의 일부만 맞아도 걸린다면 `"pass"` 는 어떤 줄까지 측정에서 빼 버릴 수 있는가?

### 9. `--cov-fail-under` 와 CI (연결)

- 테스트가 모두 통과했는데도 CI 가 실패하는 경우는 `--cov-fail-under` 와 어떻게 이어지는가?

### 10. `parametrize` 와 `grade` 의 분기 (연결)

- `@pytest.mark.parametrize` 가 `grade` 의 브랜치 커버리지를 채우는 데 잘 맞는 까닭은 무엇인가?

## 실습

### 실습 1. `Calculator` 와 커버리지를 채우는 테스트 모음 만들기

**만들 것** — 분기가 여럿인 `Calculator` 클래스와, 그 모든 줄 · 갈래를 지나가도록 짠 `pytest` 테스트 모음을 한 파일에 만든다.
파일을 직접 실행하면 커버리지 명령어 · 설정 · 종류 · 목표를 안내문으로 찍는다.

**준비물** — `pytest` 와 `pytest-cov` (`pip install pytest-cov`).

**요구 조건**

1단계 — 측정 대상 `Calculator`

1. `add(a, b)` 는 두 값의 합을 돌려준다(분기 없음).
2. `divide(a, b)` 는 `b` 가 0이면 `"0으로 나눌 수 없습니다"` 메시지로 `ZeroDivisionError` 를 던지고, 아니면 `a / b` 를 돌려준다.
3. `grade(score)` 는 90 이상 `'A'`, 80 이상 `'B'`, 70 이상 `'C'`, 60 이상 `'D'`, 나머지 `'F'` 를 `if`/`elif`/`else` 사슬로 돌려준다.
4. `process(data)` 는 `data` 가 비었거나 `None` 이면 `None` 을 돌려준다.
5. `process` 는 그렇지 않으면 항목마다 숫자(`int` · `float`)는 2배, 문자열은 대문자로 바꿔 리스트에 담고, 그 밖의 값은 `continue` 로 건너뛴 뒤 리스트를 돌려준다.

2단계 — 테스트 모음 `TestCalculator`

6. `calc` fixture 가 테스트마다 새 `Calculator` 를 준다.
7. `test_add` 는 `add(2, 3)` 이 5 인지 본다.
8. `test_divide` 는 `divide(10, 2)` 가 5 인지 보고, `test_divide_by_zero` 는 `pytest.raises` 로 `divide(1, 0)` 의 예외를 확인한다.
9. `test_grade_all_branches` 는 `parametrize` 로 `(95,'A')` · `(85,'B')` · `(75,'C')` · `(65,'D')` · `(55,'F')` 다섯 쌍을 검사한다.
10. `test_process_empty` 는 빈 리스트 입력을, `test_process_none` 은 `None` 입력이 `None` 을 돌려주는지를 검사한다.
11. `test_process_mixed` 는 `[1, "hello", 2.5, None, "world"]` 를 넣어 `[2, "HELLO", 5.0, "WORLD"]` 가 나오는지 본다(`else` 갈래 포함).

3단계 — 메인 가드 안내문

12. `if __name__ == '__main__':` 안에서만 안내문을 찍어 테스트와 분리한다.
13. 기본 · HTML 리포트 · 미커버 라인 표시 · 브랜치 커버리지 · 최소 기준 · XML(CI용) 여섯 가지 명령어를 `(이름, 명령)` 리스트로 두고 반복문으로 찍는다.
14. `pyproject.toml` 꼴의 설정(`[tool.coverage.run]` 의 `source` · `branch`, `[tool.coverage.report]` 의 `fail_under` · `show_missing` · `exclude_lines` 여섯 패턴, `[tool.coverage.html]` 의 `directory`)을 찍는다.
15. 커버리지 종류 셋(라인 · 브랜치 · 함수)과 목표 기준(60~70% · 80% · 90%+ · 100%), 「커버리지는 테스트되지 않은 코드를 찾는 도구」라는 주의를 찍는다.

**시작 코드**

```python
# 설치: pip install pytest-cov
import pytest


class Calculator:
    def add(self, a, b):
        pass  # TODO: 합을 돌려준다

    def divide(self, a, b):
        # TODO: b 가 0이면 ZeroDivisionError("0으로 나눌 수 없습니다")
        # TODO: 아니면 a / b
        pass

    def grade(self, score):
        # TODO: 90/80/70/60 경계로 'A'~'D', 나머지 'F' (if/elif/else 사슬)
        pass

    def process(self, data):
        # TODO: 비었거나 None 이면 None
        results = []
        for item in data:
            # TODO: 숫자 → 2배, 문자열 → 대문자, 그 밖 → continue
            pass
        return results


class TestCalculator:
    # TODO: calc fixture — 테스트마다 새 Calculator

    def test_add(self, calc):
        pass  # TODO

    def test_divide(self, calc):
        pass  # TODO

    def test_divide_by_zero(self, calc):
        pass  # TODO: pytest.raises 로 예외 경로

    # TODO: parametrize 로 다섯 등급 쌍
    def test_grade_all_branches(self, calc, score, expected):
        pass  # TODO

    def test_process_empty(self, calc):
        pass  # TODO

    def test_process_none(self, calc):
        pass  # TODO

    def test_process_mixed(self, calc):
        pass  # TODO: [1, "hello", 2.5, None, "world"]


if __name__ == '__main__':
    print("=== 커버리지 실행 명령어 ===")
    cmds = [
        ("기본", "TODO"),
        ("HTML 리포트", "TODO"),
        ("미커버 라인 표시", "TODO"),
        ("브랜치 커버리지", "TODO"),
        ("최소 기준", "TODO"),
        ("XML (CI용)", "TODO"),
    ]
    for name, cmd in cmds:
        print(f"  {name:20s}: {cmd}")
    print()

    print("=== .coveragerc 설정 ===")
    print("# .coveragerc 또는 pyproject.toml")
    # TODO: [tool.coverage.run] · [tool.coverage.report] · [tool.coverage.html] 절을 찍는다

    print("=== 커버리지 종류 ===")
    # TODO: 라인 · 브랜치 · 함수 커버리지의 뜻, 「브랜치 > 라인」

    print("=== 커버리지 목표 ===")
    # TODO: 60~70% · 80% · 90%+ · 100% 기준과 주의 문장
```

**확인 방법** — 파일을 `test_calculator.py` 로 저장하고 `pytest --cov=. --cov-branch --cov-report=term-missing test_calculator.py` 로 돌려 어떤 테스트가 실패하는지, `Missing` 칸에 어떤 줄이 남는지 본다.
`python test_calculator.py` 로 직접 실행해 안내문 네 묶음이 찍히는지 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
