# python/python-testing-deep/10 — 코드 커버리지 — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. `None` 을 돌려주고, 테스트는 실패한다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

`process([])` 는 `None` 을 돌려준다.
`assert None == []` 은 거짓이므로 `test_process_empty` 는 실패한다.

**왜 그런가**

빈 리스트는 거짓으로 취급되어 `not []` 이 참이 된다.
그래서 첫 줄의 `if not data:` 에서 곧바로 `return None` 으로 빠져나간다.
테스트의 기대값 `[]` 은 구현과 맞지 않는다 — 원본 테스트의 기대값이 틀린 것으로 보인다.
그래도 이 테스트는 `return None` 줄을 지나가므로 커버리지에는 「커버됨」으로 보태진다.
근거: 2-summary 「어디서 틀리나 4」.

### 2. `raise ZeroDivisionError(...)` 줄 하나

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

`raise ZeroDivisionError("0으로 나눌 수 없습니다")` 줄이 미커버로 남는다.
`if b == 0:` 줄과 `return a / b` 줄은 실행된다.

**왜 그런가**

`divide(10, 2)` 에서 `b` 는 2 라 조건이 거짓이다.
조건 줄은 평가되었으니 실행됨이고, `raise` 를 건너뛰어 `return` 으로 간다.
예외 경로를 지나가는 `test_divide_by_zero` 가 있어야 `raise` 줄이 채워진다.
`5.0 == 5` 는 참이라 테스트 자체는 통과한다.
근거: 2-summary 「동작 방식 (2)」.

### 3. 라인 100% — 「조건이 거짓인 갈래」가 미커버

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

`clamp(-5)` 는 `if`, `x = 0`, `return x` 세 줄을 모두 지나가므로 라인 커버리지는 100% 다.
브랜치 커버리지에는 `if x < 0` 이 거짓이 되어 곧바로 `return x` 로 가는 갈래가 미커버로 남는다.

**왜 그런가**

`else` 가 없는 `if` 도 「참 쪽」과 「건너뛰는 쪽」 두 갈래를 가진다.
음수 하나로는 참 쪽만 지나가므로, 0 이상의 값을 넣는 테스트가 없으면 거짓 갈래는 검사되지 않는다.
근거: 2-summary 「동작 방식 (3)」.

### 4. 커버되지 않는다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

`continue` 줄은 실행되지 않아 미커버로 남는다.

**왜 그런가**

`1` · `2.5` 는 숫자 갈래로, `"hello"` · `"world"` 는 문자열 갈래로 간다.
숫자도 문자열도 아닌 값이 없으니 `else` 로 가는 항목이 하나도 없다.
원래 입력의 `None` 이 바로 `continue` 를 지나가게 하는 값이었다.
근거: 2-summary 「동작 방식 (3)」의 `process` 그림.

### 5. 줄은 다 지나도 갈래는 남을 수 있어서다

라인 커버리지는 「줄이 한 번이라도 실행됐나」만 본다.
`else` 없는 `if` 처럼 참 쪽만 지나가도 모든 줄이 실행되는 구조에서는 거짓 쪽 동작이 한 번도 검사되지 않는다.
브랜치 커버리지는 분기의 갈래마다 지나갔는지를 따지므로 이 빈틈을 드러낸다.
그래서 원본은 「브랜치 > 라인: 더 엄격하고 더 유용」이라고 적었다.
근거: 2-summary 「동작 방식 (3)」 · 「어디서 틀리나 2」.

### 6. 「실행됐다」와 「맞는지 확인했다」가 다르기 때문이다

커버리지는 테스트가 코드를 지나갔는지만 기록한다.
`assert` 가 없거나 의미 없는 `assert` 뿐이어도 줄은 「실행됨」이 된다.
기대값이 틀린 테스트(원본의 `test_process_empty`)도 줄을 지나가는 한 비율을 올린다.
그래서 커버리지는 테스트되지 않은 코드를 찾는 도구이지 품질의 척도가 아니다.
근거: 2-summary 「어디서 틀리나 1 · 4」 · 「핵심 문장 1 · 5」.

### 7. 「테스트할 의미가 적은 코드」만 뺀다

`__repr__` · 로깅 · 디버그 출력 · 메인 가드 · `raise NotImplementedError` · 빈 구현 · 타입 스텁의 `...` 처럼 동작 검증의 의미가 적은 코드는 빼도 된다.
실제 분기 · 계산 로직을 테스트하기 귀찮다는 이유로 빼면 안 된다.
그렇게 빼면 분모에서도 빠져 비율은 오르지만, 테스트되지 않은 코드는 그대로 숨는다.
근거: 2-summary 「동작 방식 (5)」 · 「어디서 틀리나 3」.

### 8. `pass` 가 들어간 다른 줄까지 빠질 수 있다

패턴이 줄의 일부만 맞아도 걸리면 `password = ...` · `bypass(...)` 처럼 글자 `pass` 를 품은 줄도 제외된다.
그 줄이 블록을 여는 줄이라면 블록 전체가 빠진다.
그래서 짧은 패턴일수록 뜻하지 않은 코드가 측정에서 사라질 위험이 크다(확인 필요).
근거: 2-summary 「동작 방식 (5)」 · 「어디서 틀리나 3」.

### 9. 비율이 기준 아래면 테스트 통과와 별개로 실패한다

`--cov-fail-under=80`(또는 설정의 `fail_under = 80`)을 걸면 테스트가 전부 통과해도 커버리지가 80% 미만일 때 `pytest` 가 실패로 끝난다.
CI 는 그 실패를 빨간불로 보고 병합을 막는다.
그래서 테스트 없이 새 코드를 더해 비율을 떨어뜨리는 변경이 드러난다.
근거: 2-summary 「동작 방식 (6)」 · 「어디서 틀리나 7」.

### 10. 갈래마다 다른 입력이 필요한데, 한 테스트로 여러 입력을 돌릴 수 있어서다

`grade` 는 결과가 `'A'` ~ `'F'` 다섯 갈래라, 모든 갈래를 지나가려면 각 구간의 점수가 하나씩 필요하다.
`parametrize` 는 한 테스트 함수를 `(점수, 기대 등급)` 쌍 다섯 개로 되풀이해 돌린다.
같은 테스트를 다섯 번 복붙하지 않고도 다섯 갈래를 모두 채울 수 있다.
근거: 2-summary 「동작 방식 (3)」 · 「언제 쓰고 언제 안 쓰나」.

## 실습 정답

### 실습 1. `Calculator` 와 커버리지를 채우는 테스트 모음 만들기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. 합 | `Calculator.add` 의 `return a + b` |
| 2. 0 분모 예외 · 나눗셈 | `Calculator.divide` 의 `if b == 0: raise ZeroDivisionError(...)` · `return a / b` |
| 3. 등급 사슬 | `Calculator.grade` 의 `if score >= 90` … `else: return 'F'` |
| 4. 빈 입력 가드 | `Calculator.process` 의 `if not data: return None` |
| 5. 타입별 처리 | `process` 의 `isinstance(item, (int, float))` · `isinstance(item, str)` · `else: continue` |
| 6. fixture | `@pytest.fixture def calc(self)` |
| 7. 덧셈 테스트 | `test_add` |
| 8. 나눗셈 두 경로 | `test_divide` · `test_divide_by_zero` 의 `pytest.raises` |
| 9. 다섯 등급 | `@pytest.mark.parametrize("score, expected", [...])` · `test_grade_all_branches` |
| 10. 빈 입력 · `None` 입력 | `test_process_empty` · `test_process_none` |
| 11. 혼합 입력 | `test_process_mixed` |
| 12. 메인 가드 | `if __name__ == '__main__':` |
| 13. 여섯 명령어 | `cmds` 리스트 · `for name, cmd in cmds:` |
| 14. 설정 | `[tool.coverage.run]` · `[tool.coverage.report]` · `[tool.coverage.html]` 을 찍는 `print` 들 |
| 15. 종류 · 목표 · 주의 | `=== 커버리지 종류 ===` · `=== 커버리지 목표 ===` 아래 `print` 들 |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`python/python-testing-deep/reference/coverage.py`

```python
# [테스팅 심화] 코드 커버리지
# 설명: pytest-cov로 라인/브랜치 커버리지를 측정하고 제외 패턴과 목표를 설정
# 팁: 커버리지는 테스트되지 않은 코드를 찾는 도구이지 품질의 척도는 아니다. 브랜치 커버리지가 라인 커버리지보다 더 의미 있다. pragma: no cover로 테스트 불필요한 코드(repr, 로깅 등)를 제외한다. CI에서 --cov-fail-under로 최소 기준을 강제하면 커버리지 저하를 방지할 수 있다.

# === pytest-cov 사용법 ===
# 설치: pip install pytest-cov

# --- 기본 실행 ---
# pytest --cov=my_package tests/
# pytest --cov=src --cov-report=html tests/
# pytest --cov=. --cov-report=term-missing tests/

# === 테스트 대상 코드 ===
# file: calculator.py
# Calculator: 커버리지 측정 대상 클래스
class Calculator:
    # 단순 덧셈 (분기 없음 - 라인 커버리지 1줄)
    def add(self, a, b):
        return a + b

    # 분기 있음: 0 분모 시 예외 (브랜치 2개)
    def divide(self, a, b):
        if b == 0:
            raise ZeroDivisionError("0으로 나눌 수 없습니다")
        return a / b

    # 다중 분기 (브랜치 5개) - 모든 분기 테스트가 브랜치 커버리지 100%
    def grade(self, score):
        if score >= 90:
            return 'A'
        elif score >= 80:
            return 'B'
        elif score >= 70:
            return 'C'
        elif score >= 60:
            return 'D'
        else:
            return 'F'

    # 복합 분기: 빈 입력 + 타입별 처리
    def process(self, data):
        # 빈 데이터 가드
        if not data:
            return None

        results = []
        for item in data:
            # 숫자: 2배
            if isinstance(item, (int, float)):
                results.append(item * 2)
            # 문자열: 대문자
            elif isinstance(item, str):
                results.append(item.upper())
            else:
                continue  # 이 라인이 커버되는지?
        return results

# === 테스트 코드 ===
# pytest: 테스트 프레임워크 임포트
import pytest

# TestCalculator: 커버리지를 높이는 테스트 모음
class TestCalculator:
    # fixture: 각 테스트마다 새 Calculator 인스턴스 제공
    @pytest.fixture
    def calc(self):
        return Calculator()

    # --- 라인 커버리지를 높이는 테스트 ---
    # add 메서드 라인 커버
    def test_add(self, calc):
        assert calc.add(2, 3) == 5

    # divide 정상 경로 커버
    def test_divide(self, calc):
        assert calc.divide(10, 2) == 5

    # divide 예외 경로 커버 (브랜치 커버리지)
    def test_divide_by_zero(self, calc):
        with pytest.raises(ZeroDivisionError):
            calc.divide(1, 0)

    # --- 브랜치 커버리지: 모든 분기 테스트 ---
    # parametrize: 모든 등급 분기를 한 번에 검증
    @pytest.mark.parametrize("score, expected", [
        (95, 'A'),
        (85, 'B'),
        (75, 'C'),
        (65, 'D'),
        (55, 'F'),
    ])
    def test_grade_all_branches(self, calc, score, expected):
        assert calc.grade(score) == expected

    # 빈 리스트 분기
    def test_process_empty(self, calc):
        assert calc.process([]) == []

    # None 입력 분기
    def test_process_none(self, calc):
        assert calc.process(None) is None

    # 다양한 타입 혼합 (else 분기 포함)
    def test_process_mixed(self, calc):
        result = calc.process([1, "hello", 2.5, None, "world"])
        assert result == [2, "HELLO", 5.0, "WORLD"]

# 메인 가드: 직접 실행 시 안내문 출력 (테스트와 분리)
if __name__ == '__main__':
    print("=== 커버리지 실행 명령어 ===")
    cmds = [
        ("기본", "pytest --cov=my_package"),
        ("HTML 리포트", "pytest --cov=src --cov-report=html"),
        ("미커버 라인 표시", "pytest --cov=. --cov-report=term-missing"),
        ("브랜치 커버리지", "pytest --cov=. --cov-branch"),
        ("최소 기준", "pytest --cov=. --cov-fail-under=80"),
        ("XML (CI용)", "pytest --cov=. --cov-report=xml"),
    ]
    for name, cmd in cmds:
        print(f"  {name:20s}: {cmd}")
    print()

    print("=== .coveragerc 설정 ===")
    print("# .coveragerc 또는 pyproject.toml")
    print("[tool.coverage.run]")
    print('source = ["src"]')
    print("branch = true")
    print()
    print("[tool.coverage.report]")
    print("fail_under = 80")
    print("show_missing = true")
    print("exclude_lines = [")
    print('    "pragma: no cover",     # 커버리지 제외 표시')
    print('    "def __repr__",         # repr은 제외')
    print('    "if __name__",          # 메인 가드 제외')
    print('    "raise NotImplementedError",')
    print('    "pass",                 # 빈 구현 제외')
    print('    "\\.\\.\\.",            # 타입 스텁 제외')
    print("]")
    print()
    print("[tool.coverage.html]")
    print('directory = "htmlcov"')
    print()

    print("=== 커버리지 종류 ===")
    print("라인 커버리지:    실행된 라인 비율")
    print("브랜치 커버리지:  if/else 모든 분기 실행 비율")
    print("함수 커버리지:    호출된 함수 비율")
    print()
    print("브랜치 > 라인: 더 엄격하고 더 유용")
    print()

    print("=== 커버리지 목표 ===")
    print("일반적 기준:")
    print("  60~70%: 최소 (레거시 프로젝트)")
    print("  80%:    권장 (대부분의 프로젝트)")
    print("  90%+:   높은 신뢰성 필요 (금융, 의료)")
    print("  100%:   비현실적, 커버리지≠품질")
    print()
    print("주의: 커버리지가 높아도 의미 없는 assert가 많으면 무의미")
    print("→ 커버리지는 '테스트되지 않은 코드'를 찾는 도구")
```

**실행 결과** — 실행하지 않음 — 외부 라이브러리 `pytest` 가 있어야 도는 예제다 — 그것 없이 만들어 실행하지 않았다.

**풀이 요점**

- `divide` 는 정상 경로와 예외 경로를 따로 테스트해야 `raise` 줄과 두 갈래가 모두 채워진다.
- `grade` 의 다섯 갈래는 `parametrize` 한 함수로 덮는다.
- `test_process_mixed` 의 `None` 이 `else` → `continue` 갈래를 지나가게 하는 값이다.
- 정답 코드의 `test_process_empty` 는 `process([])` 가 `None` 을 돌려주는 구현과 기대값 `[]` 이 어긋나 실패할 것으로 읽힌다 — 커버리지는 채워도 검증은 틀릴 수 있다는 예다(원본에 근거 없음 — 추론).
- 안내문은 메인 가드 안에만 두어 `pytest` 가 파일을 불러올 때는 찍히지 않게 하고, 설정의 `"if __name__"` 패턴으로 측정에서도 뺄 수 있다.
- 파일 이름을 `coverage.py` 로 두면 측정 라이브러리 이름과 겹쳐 불러오기가 꼬일 수 있으니 `test_calculator.py` 같은 이름이 안전하다(확인 필요).

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — 외부 라이브러리 `pytest` 가 있어야 도는 예제다 — 그것 없이 만들어 실행하지 않았다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
