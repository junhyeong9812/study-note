# python/python-testing-deep/02 — pytest 파라미터화 — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 데코레이터 두 개를 겹친 테스트 (예측)

```python
# 질문용 발췌
@pytest.mark.parametrize("x", [1, 2, 3])
@pytest.mark.parametrize("y", ["a", "b"])
def test_pair(x, y):
    assert x > 0
```

- pytest 는 이 함수로 테스트 케이스를 몇 개 만드는가?
- `x=3, y="b"` 짝은 그 케이스들 안에 있는가?

### 2. 같은 이름의 fixture 와 `indirect` (예측)

```python
# 질문용 발췌
@pytest.fixture
def num(request):
    return request.param * 10

@pytest.mark.parametrize("num", [1, 2], indirect=True)
def test_num(num):
    assert num in (10, 20)
```

- 두 케이스에서 `test_num` 이 받는 `num` 값은 각각 무엇이고, 테스트는 어떻게 되는가?
- 같은 코드에서 `indirect=True` 만 지우면 `test_num` 은 무엇을 받고, 테스트는 어떻게 되는가?

### 3. 조건 하나를 바꾼 `categorize` (예측)

```python
# 질문용 발췌 — 원본에서 둘째 줄만 바꿨다
def categorize(age):
    if age < 0: return "invalid"
    if age < 2: return "infant"      # 원본은 age <= 2
    if age <= 12: return "child"
    if age <= 17: return "teen"
    if age <= 64: return "adult"
    return "senior"
```

- 원본 `test_age_category` 의 열 케이스(-1, 0, 1, 12, 13, 17, 18, 64, 65, 150)로 이 함수를 검사하면 몇 개가 실패하는가?
- 이 변경을 드러내려면 목록에 어떤 나이를 넣어야 하는가?

### 4. 케이스에 이름표를 붙이는 까닭 (왜)

- `ids` 나 `pytest.param(…, id=…)` 로 케이스에 이름을 붙이면 무엇이 좋아지는가?
- 케이스가 자주 늘고 줄 때 `ids` 목록보다 `pytest.param` 의 id 가 덜 어긋나는 까닭은 무엇인가?

### 5. `indirect=True` 로 fixture 를 거치는 까닭 (왜)

- 원본 `test_db_record` 는 왜 테스트 본문에서 딕셔너리를 만들지 않고 fixture 를 거치게 했는가?

### 6. 기대 예외를 잘못 적은 케이스 (경계)

- `test_division_errors` 의 `("a", 1, TypeError)` 를 `("a", 1, ValueError)` 로 바꾸면 그 케이스는 통과하는가, 실패하는가?
- `(4, 2, ZeroDivisionError)` 처럼 예외가 아예 나지 않는 케이스를 넣으면 어떻게 되는가?

### 7. 테스트 파일을 `python` 으로 실행하면 (경계)

- 원본 파일을 `python 파일.py` 로 실행하면 테스트 함수들이 돌아가는가?
- 그때 화면에는 무엇이 찍히는가?

### 8. 경계값 분석과 parametrize 의 만남 (연결)

- 경계값 분석으로 고른 값들을 한 테스트 안의 `assert` 여러 줄 대신 parametrize 목록의 케이스로 넣으면 무엇이 달라지는가?

### 9. `test_power` 가 잡아낼 수 있는 버그 (경계)

- 원본 `test_power` 의 단언 `base ** exp == pow(base, exp)` 가 실패할 수 있는 경우가 있는가?
- 이 테스트가 실제로 보여 주는 것은 무엇인가?

## 실습

### 실습 1. 일곱 가지 parametrize 패턴을 한 파일에 모으기

**만들 것** — 제곱 · 거듭제곱 · 이메일 · 나눗셈 예외 · 사용자 검증 · DB 레코드 · 나이 분류를 각각 parametrize 로 검사하는 pytest 파일을 만든다.
직접 실행하면 패턴 요약을 찍는다.

**준비물** — `pytest` 가 설치된 Python 환경.

**요구 조건**

1. 1단계 기본 — `test_square` 는 입력 1 · 2 · 3 · 4 · -1 · 0 과 그 제곱을 `(input_val, expected)` 튜플 여섯 개로 받아 `input_val ** 2 == expected` 를 검사한다.
2. 2단계 곱집합 — `test_power` 는 `base` 를 `[2, 10]`, `exp` 를 `[0, 1, 2, 3]` 으로 **데코레이터 두 개에 따로** 파라미터화해 8케이스를 만들고, `base ** exp` 를 `pow(base, exp)` 와 비교한다.
3. 3단계 ids — `test_email_validation` 은 다섯 이메일(`"user@test.com"` 참, `"invalid"` 거짓, `""` 거짓, `"a@b.c"` 참, `"user@.com"` 거짓)을 받고, `ids` 로 `정상_이메일` · `@_없음` · `빈_문자열` · `최소_형식` · `도메인_오류` 이름을 붙인다. 정규식 `^[^@]+@[^@]+\.[^@]+$` 의 일치 여부를 기대값과 비교한다.
4. 4단계 예외 — `test_division_errors` 는 `(1, 0)` 에서 `ZeroDivisionError`, `("a", 1)` 에서 `TypeError` 를 예외 클래스 파라미터로 받아 `pytest.raises` 로 `a / b` 를 검사한다.
5. 5단계 `pytest.param` — 바깥 변수 `test_users` 에 사용자 딕셔너리 셋(Alice 30 admin → 참, Bob 17 user → 거짓, 이름 빈 문자열 25 user → 거짓)을 `pytest.param` 으로 담고 id `admin_user` · `underage_user` · `empty_name` 을 붙인다. `test_user_validation` 은 「이름이 비어 있지 않고 나이 18 이상」을 기대값과 비교한다.
6. 6단계 indirect — fixture `db_record` 는 `request.param` 이 `"user"` 면 users 레코드, `"product"` 면 products 레코드 딕셔너리를 돌려주고, 그 밖이면 `ValueError` 를 일으킨다. `test_db_record` 는 `["user", "product"]` 를 `indirect=True` 로 받아 `type` · `table` 키가 있고 `fields` 가 2개 이상인지 검사한다.
7. 7단계 경계값 — `test_age_category` 는 나이 -1 · 0 · 1 · 12 · 13 · 17 · 18 · 64 · 65 · 150 과 기대 분류를 받아, 안쪽 함수 `categorize` 의 결과와 비교한다.
8. 8단계 — 파일을 직접 실행하면 parametrize 패턴 요약과 경계값 요약을 찍는다(시작 코드에 채워 둠).

**시작 코드**

```python
import pytest
import math

# 1단계 — TODO: parametrize 로 (input_val, expected) 여섯 케이스
def test_square(input_val, expected):
    assert input_val ** 2 == expected

# 2단계 — TODO: base 와 exp 를 데코레이터 두 개로 따로 파라미터화
def test_power(base, exp):
    """2x4 = 8가지 조합 자동 생성"""
    result = base ** exp
    assert result == pow(base, exp)

# 3단계 — TODO: 다섯 케이스 + ids
def test_email_validation(email, is_valid):
    import re
    pattern = r'^[^@]+@[^@]+\.[^@]+$'
    assert bool(re.match(pattern, email)) == is_valid

# 4단계 — TODO: (a, b, expected_error) 두 케이스
def test_division_errors(a, b, expected_error):
    # TODO: a / b 가 expected_error 를 일으키는지 검사
    pass

# 5단계 — TODO: pytest.param 세 개 (id 포함)
test_users = [
    # {"name": "Alice", "age": 30, "role": "admin"}, True
    # {"name": "Bob", "age": 17, "role": "user"}, False
    # {"name": "", "age": 25, "role": "user"}, False
]

# TODO: test_users 로 파라미터화
def test_user_validation(user, expected_valid):
    is_valid = bool(user.get("name")) and user.get("age", 0) >= 18
    assert is_valid == expected_valid

# 6단계
@pytest.fixture
def db_record(request):
    """파라미터에 따라 다른 DB 레코드 fixture 생성"""
    record_type = None  # TODO: 넘어온 파라미터 값을 꺼낸다
    if record_type == "user":
        return {"type": "user", "table": "users", "fields": ["name", "email"]}
    elif record_type == "product":
        return {"type": "product", "table": "products", "fields": ["name", "price"]}
    raise ValueError(f"Unknown type: {record_type}")

# TODO: "user", "product" 를 fixture 를 거쳐 받도록 파라미터화
def test_db_record(db_record):
    assert "type" in db_record
    assert "table" in db_record
    assert len(db_record["fields"]) >= 2

# 7단계 — TODO: 나이와 기대 분류 열 케이스
def test_age_category(age, category):
    def categorize(age):
        if age < 0: return "invalid"
        if age <= 2: return "infant"
        if age <= 12: return "child"
        if age <= 17: return "teen"
        if age <= 64: return "adult"
        return "senior"
    assert categorize(age) == category

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

**확인 방법** — 파일을 `test_parametrize.py` 로 저장하고 `pytest test_parametrize.py -v` 를 돌린다.
케이스마다 테스트가 한 줄씩 표시되고, 모두 통과하며, 개수가 6 + 8 + 5 + 2 + 3 + 2 + 10 = 36 인지 본다(코드에서 센 수).
이메일과 사용자 테스트 이름에 붙인 id 가 보이는지도 본다.
`python test_parametrize.py` 로 돌리면 요약 문장만 찍히는지 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
