# python/python-testing-deep/02 — pytest 파라미터화 — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 3 × 2 = 6개 — 모든 짝이 생긴다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
케이스는 6개다.
`x=3, y="b"` 짝도 들어 있다.

**왜 그런가**
데코레이터를 겹치면 각 목록의 모든 조합, 곧 곱집합이 생긴다.
`x` 의 값 3개 × `y` 의 값 2개 = 6 이고, 곱집합은 빠짐없이 모든 짝을 만드므로 `(3, "b")` 도 그중 하나다.
근거: 2-summary 「동작 방식 (2)」.

### 2. `indirect=True` 면 10 · 20 을 받아 통과, 지우면 1 · 2 를 받아 실패

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
`indirect=True` 일 때 두 케이스의 `num` 은 10 과 20 이고, 두 테스트 모두 통과한다.
`indirect=True` 를 지우면 `num` 은 1 과 2 이고, 두 테스트 모두 단언이 거짓이라 실패한다.

**왜 그런가**
`indirect=True` 면 값 1 · 2 가 같은 이름의 fixture `num` 으로 가고, fixture 가 `request.param * 10` 을 돌려준다.
`indirect` 가 없으면 값이 fixture 를 거치지 않고 그대로 테스트 인자로 들어간다.
1 과 2 는 `(10, 20)` 에 없으므로 단언이 실패한다.
근거: 2-summary 「동작 방식 (4)」 · 「어디서 틀리나 3」.

### 3. 하나도 실패하지 않는다 — 2 와 3 이 목록에 없다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
열 케이스 모두 통과하고, 실패는 0개다.
변경을 드러내려면 나이 2(기대 `"infant"`)를 넣어야 하고, 전환점의 반대편 3(기대 `"child"`)도 함께 넣는 것이 경계값 분석의 꼴이다.

**왜 그런가**
`age < 2` 와 `age <= 2` 가 다른 답을 내는 나이는 2 하나뿐이다.
0 과 1 은 두 조건 모두에서 `"infant"` 이고, 12 이상은 둘째 줄과 상관없다.
원본 목록은 `infant` · `child` 사이 전환점(2 와 3)을 빠뜨렸으므로 이 버그는 숨는다.
근거: 2-summary 「동작 방식 (6)」 · 「어디서 틀리나 4」.

### 4. 실패한 케이스를 이름으로 바로 알 수 있다

이름을 붙이면 테스트가 실패했을 때 어떤 케이스인지 즉시 파악할 수 있다(원본 팁).
`ids` 목록은 케이스 목록과 **순서로만** 짝지어지므로, 케이스를 넣거나 빼면서 `ids` 를 함께 고치지 않으면 이름과 케이스가 어긋난다.
`pytest.param` 은 값과 id 를 한 덩어리로 묶어 이름표가 값 바로 옆에 있으므로 이런 어긋남이 생기기 어렵다.
근거: 2-summary 「동작 방식 (3)」 · 「어디서 틀리나 1」.

### 5. 복잡한 준비를 fixture 로 떼어 내 검사와 나누려고

`indirect=True` 는 파라미터 값을 fixture 에 전달해, 복잡한 설정을 테스트 밖으로 분리할 수 있게 한다(원본 팁).
`db_record` fixture 는 `"user"` · `"product"` 라는 짧은 값을 받아 레코드 딕셔너리를 만들고, 모르는 값이면 `ValueError` 로 막는다.
테스트 본문은 「키가 있나 · 필드가 2개 이상인가」만 검사하면 되므로 짧고 읽기 쉬워진다.
근거: 2-summary 「동작 방식 (4)」.

### 6. 둘 다 실패한다

`ValueError` 를 기대했는데 `"a" / 1` 이 `TypeError` 를 일으키면, 그 예외는 `pytest.raises(ValueError)` 에 잡히지 않고 퍼져서 테스트가 실패한다.
`4 / 2` 는 예외 없이 2.0 이 되므로, 블록 안에서 예외가 나지 않아 역시 실패한다.
`pytest.raises` 는 지정한 예외가 날 때만 통과한다.
근거: 2-summary 「동작 방식 (5)」 · 「어디서 틀리나 6」.

### 7. 테스트는 돌지 않고 요약 문장만 찍힌다

`python 파일.py` 로 실행하면 `if __name__ == '__main__':` 블록만 실행된다.
테스트 함수는 정의만 되고 아무도 호출하지 않는다 — 테스트를 모아 부르는 일은 pytest 가 한다.
그래서 「=== parametrize 패턴 ===」으로 시작하는 패턴 요약과 「=== 경계값 테스트 ===」 요약 문장들만 찍힌다.
근거: 2-summary 「어디서 틀리나 7」.

### 8. 경계 하나하나가 별도 테스트가 되어 따로 보고된다

parametrize 에서는 튜플 하나가 테스트 하나이므로, 한 경계에서 실패해도 다른 경계 케이스는 계속 돌고 결과가 따로 기록된다.
`assert` 여러 줄을 한 함수에 몰아 두면 첫 실패에서 함수가 멈춰 뒤쪽 경계는 검사조차 되지 않는다.
경계값 분석이 고른 「전환점 양쪽 값」을 목록에 한 줄씩 넣으면 어느 경계가 깨졌는지 한눈에 보인다.
근거: 2-summary 「동작 방식 (1)」 · 「동작 방식 (6)」. (함수가 첫 `assert` 실패에서 멈춘다는 점은 원본에 근거 없음 — 추론)

### 9. 사실상 실패하지 않는다 — 곱집합 생성을 보이는 예일 뿐이다

`base ** exp` 와 `pow(base, exp)` 는 같은 거듭제곱 계산이므로 단언은 사실상 언제나 참이다.
그래서 이 테스트는 내가 쓴 코드의 버그를 잡지 못한다.
이 테스트가 보여 주는 것은 데코레이터 두 개를 겹치면 2 × 4 = 8케이스가 자동으로 생긴다는 점이다.
실제로 검증하려면 기대값을 계산과 따로 적어야 한다(예: `(2, 3, 8)`).
근거: 2-summary 「어디서 틀리나 5」 · 「동작 방식 (2)」.

## 실습 정답

### 실습 1. 일곱 가지 parametrize 패턴을 한 파일에 모으기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1단계 제곱 여섯 케이스 | `@pytest.mark.parametrize("input_val, expected", [...])` + `test_square` |
| 2단계 곱집합 8케이스 | `@pytest.mark.parametrize("base", [2, 10])` · `@pytest.mark.parametrize("exp", [0, 1, 2, 3])` + `test_power` |
| 3단계 이메일 + ids | `@pytest.mark.parametrize("email, is_valid", [...], ids=[...])` + `test_email_validation` |
| 4단계 예외 클래스 파라미터 | `@pytest.mark.parametrize("a, b, expected_error", [...])` + `with pytest.raises(expected_error)` |
| 5단계 `pytest.param` 과 바깥 변수 | `test_users = [pytest.param(..., id="admin_user"), ...]` + `test_user_validation` |
| 6단계 indirect fixture | `db_record(request)` 의 `record_type = request.param` · `indirect=True` + `test_db_record` |
| 7단계 경계값 열 케이스 | `@pytest.mark.parametrize("age, category", [...])` + 안쪽 `categorize` |
| 8단계 직접 실행 시 요약 | `if __name__ == '__main__':` 블록의 `print` 들 |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`python/python-testing-deep/reference/pytest-parametrize.py`

```python
# [테스팅 심화] pytest 파라미터화
# 설명: @pytest.mark.parametrize로 여러 입력 조합을 테스트하고, 간접 파라미터와 ids로 가독성 향상
# 팁: parametrize의 ids를 지정하면 테스트 실패 시 어떤 케이스인지 즉시 파악할 수 있다. 여러 @parametrize를 중첩하면 모든 조합의 곱집합이 생성된다. indirect=True는 파라미터 값을 fixture에 전달하여 복잡한 설정을 분리할 수 있다. 경계값 분석은 버그가 가장 많이 발생하는 경계 지점을 체계적으로 테스트한다.

# pytest: parametrize 마커 제공
import pytest
# math: 수학 함수 사용 (현재 미사용이지만 임포트 유지)
import math

# === 기본 parametrize ===
# @pytest.mark.parametrize("이름, ...", [(값, ...), ...])
# 각 튜플마다 별도 테스트 케이스로 실행됨
@pytest.mark.parametrize("input_val, expected", [
    (1, 1),
    (2, 4),
    (3, 9),
    (4, 16),
    (-1, 1),
    (0, 0),
])
def test_square(input_val, expected):
    assert input_val ** 2 == expected

# === 여러 파라미터 조합 ===
# 중첩 parametrize: 모든 조합의 곱집합 생성 (2 x 4 = 8 케이스)
@pytest.mark.parametrize("base", [2, 10])
@pytest.mark.parametrize("exp", [0, 1, 2, 3])
def test_power(base, exp):
    """2x4 = 8가지 조합 자동 생성"""
    result = base ** exp
    assert result == pow(base, exp)

# === ids로 테스트 케이스 이름 지정 ===
# ids: 실패 시 어떤 케이스인지 명시 (한국어 가능)
@pytest.mark.parametrize("email, is_valid", [
    ("user@test.com", True),
    ("invalid", False),
    ("", False),
    ("a@b.c", True),
    ("user@.com", False),
], ids=[
    "정상_이메일",
    "@_없음",
    "빈_문자열",
    "최소_형식",
    "도메인_오류",
])
def test_email_validation(email, is_valid):
    import re
    pattern = r'^[^@]+@[^@]+\.[^@]+$'
    assert bool(re.match(pattern, email)) == is_valid

# === 예외 테스트와 parametrize ===
# 각 케이스마다 다른 예외 클래스 검증
@pytest.mark.parametrize("a, b, expected_error", [
    (1, 0, ZeroDivisionError),
    ("a", 1, TypeError),
])
def test_division_errors(a, b, expected_error):
    with pytest.raises(expected_error):
        a / b

# === 딕셔너리 파라미터 (복잡한 데이터) ===
# pytest.param: 개별 케이스에 id 지정 (또는 마커 부착)
test_users = [
    pytest.param(
        {"name": "Alice", "age": 30, "role": "admin"},
        True,
        id="admin_user"
    ),
    pytest.param(
        {"name": "Bob", "age": 17, "role": "user"},
        False,
        id="underage_user"
    ),
    pytest.param(
        {"name": "", "age": 25, "role": "user"},
        False,
        id="empty_name"
    ),
]

# 테스트 데이터를 외부 변수로 분리하여 가독성 향상
@pytest.mark.parametrize("user, expected_valid", test_users)
def test_user_validation(user, expected_valid):
    is_valid = bool(user.get("name")) and user.get("age", 0) >= 18
    assert is_valid == expected_valid

# === indirect parametrize (fixture를 통한 파라미터) ===
# fixture에서 request.param으로 파라미터 값 사용
@pytest.fixture
def db_record(request):
    """파라미터에 따라 다른 DB 레코드 fixture 생성"""
    record_type = request.param
    if record_type == "user":
        return {"type": "user", "table": "users", "fields": ["name", "email"]}
    elif record_type == "product":
        return {"type": "product", "table": "products", "fields": ["name", "price"]}
    raise ValueError(f"Unknown type: {record_type}")

# indirect=True: 파라미터를 fixture를 거쳐 변환된 값으로 받음
@pytest.mark.parametrize("db_record", ["user", "product"], indirect=True)
def test_db_record(db_record):
    assert "type" in db_record
    assert "table" in db_record
    assert len(db_record["fields"]) >= 2

# === 경계값 테스트 패턴 ===
# 경계값 분석: 버그가 자주 발생하는 경계 지점 체계적 검증
@pytest.mark.parametrize("age, category", [
    # 경계값 분석
    (-1, "invalid"),   # 하한 아래
    (0, "infant"),     # 하한
    (1, "infant"),     # 하한 위
    (12, "child"),     # 경계
    (13, "teen"),      # 경계 직후
    (17, "teen"),      # 경계 직전
    (18, "adult"),     # 경계
    (64, "adult"),     # 경계 직전
    (65, "senior"),    # 경계
    (150, "senior"),   # 상한
])
def test_age_category(age, category):
    # 분류 함수 - 경계 조건 다수
    def categorize(age):
        if age < 0: return "invalid"
        if age <= 2: return "infant"
        if age <= 12: return "child"
        if age <= 17: return "teen"
        if age <= 64: return "adult"
        return "senior"
    assert categorize(age) == category

# 실행: pytest test_parametrize.py -v
# 출력에서 각 파라미터 조합이 별도 테스트로 표시됨

if __name__ == '__main__':
    print("=== parametrize 패턴 ===")
    print("기본:      @pytest.mark.parametrize('x, y', [(1,2), (3,4)])")
    print("다중:      여러 @parametrize → 모든 조합 (곱집합)")
    print("ids:       ids=['case1', 'case2'] → 테스트 이름 지정")
    print("pytest.param: pytest.param(val, id='name') → 개별 id")
    print("indirect:  indirect=True → fixture에 param 전달")
    print()
    print("=== 경계값 테스트 ===")
    print("하한값, 하한-1, 하한+1")
    print("상한값, 상한-1, 상한+1")
    print("경계 전환점 양쪽 값")
```

**실행 결과** — 실행하지 않음 — 외부 라이브러리 `pytest` 가 있어야 도는 예제다 — 그것 없이 만들어 실행하지 않았다.

**풀이 요점**
- 이름이 둘 이상이면 케이스는 튜플, 이름이 하나면 값을 그대로 나열한다(`["user", "product"]`).
- 곱집합이 필요하면 데코레이터를 따로 겹치고, 정해진 짝만 필요하면 한 데코레이터에 튜플로 적는다.
- 이름표는 `ids` 목록(순서로 짝지음)이나 `pytest.param(..., id=...)`(값 옆에 붙음) 둘 중 하나로 붙인다.
- `indirect=True` 가 있어야 fixture 의 `request.param` 으로 값이 들어가고, 테스트는 fixture 가 돌려준 딕셔너리를 받는다.
- 경계값 목록은 `categorize` 의 조건문에서 전환점을 찾아 고른다 — 이 정답에서는 2 와 3 이 빠져 있다는 점도 함께 본다.
- 테스트는 `pytest` 로 돌린다. `python` 으로 돌리면 요약 문장만 찍힌다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — 외부 라이브러리 `pytest` 가 있어야 도는 예제다 — 그것 없이 만들어 실행하지 않았다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
