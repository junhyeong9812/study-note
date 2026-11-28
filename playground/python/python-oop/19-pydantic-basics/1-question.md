# python/python-oop/19 — Pydantic 기초 — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 문자열 `"25"` 를 `int` 필드에 넣으면 (예측)

```python
# 질문용 발췌
class User(BaseModel):
    name: str
    age: int
    email: str
    is_active: bool = True

user2 = User(name="Bob", age="25", email="bob@test.com")
print(f"타입 변환: age = {user2.age} ({type(user2.age).__name__})")
```

- 이 `print` 는 어떤 줄을 찍는가?

### 2. 이름은 빈 문자열, 가격은 음수인 `Product` (예측)

```python
# 질문용 발췌
class Product(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    price: float = Field(gt=0, description="가격 (양수)")
    quantity: int = Field(ge=0, default=0)
    tags: list[str] = Field(default_factory=list)

try:
    Product(name="", price=-10)
except Exception as e:
    print(f"Field 검증: {type(e).__name__}")
```

- 무엇이 찍히는가?
- 잡힌 예외 안에는 오류가 몇 건 들어 있는가?

### 3. 대소문자가 섞인 입력을 받은 `Account` (예측)

```python
# 질문용 발췌
@field_validator('username')
@classmethod
def username_alphanumeric(cls, v):
    if not v.isalnum():
        raise ValueError('영문/숫자만 허용')
    return v.lower()
# email_valid 도 '@' 를 확인한 뒤 v.lower() 를 돌려준다

account = Account(username="Alice123", password="securepass", email="Alice@Test.COM")
```

- 만들어진 `account` 의 `username` · `email` 값은 각각 무엇인가?

### 4. `User(name="Charlie", age="not_a_number", email="test")` 에서 걸리는 필드 (예측)
- 세 필드 중 검증에 실패하는 필드는 어느 것이고, `email="test"` 는 왜 그렇게 되는가?

### 5. 검증기는 `ValueError` 를 던지는데 바깥에서 받는 예외가 다른 까닭 (왜)
- `field_validator` 안에서 `ValueError` 를 던졌는데, 생성하는 쪽은 왜 `ValidationError` 로 받게 되는가?

### 6. `start < end` 검사를 `model_validator(mode='after')` 에 두는 까닭 (왜)
- 이 규칙은 왜 `field_validator` 로는 쓸 수 없고, `mode='after'` 여야 하는 까닭은 무엇인가?

### 7. `frozen=True` 모델이 막는 것과 막지 않는 것 (경계)
- `FrozenConfig(host="localhost", port=8080)` 생성과 `cfg.host = "remote"` 대입 가운데 어느 쪽이 막히는가?

### 8. 값을 빼먹은 `Optional` 칸과 `exclude_none` (경계)
- `Profile(name="Alice")` 의 `bio` 는 무엇이 되고, `model_dump(exclude_none=True)` 결과에는 어떤 키가 남는가?

### 9. `Field(default_factory=list)` 와 파이썬 함수의 가변 기본 인자 (연결)
- `def f(x=[])` 의 문제와 `default_factory=list` 는 어떻게 이어지는가?

### 10. 중첩 모델 · `model_validate_json` · `model_dump_json` 의 짝 (연결)
- JSON 문자열에서 `Employee` 를 만들 때 `address` 안쪽은 어떻게 검증되며, 이것이 `model_dump_json` 과 어떤 짝을 이루는가?

## 실습

### 실습 1. Pydantic 모델 여덟 장면 만들기

**만들 것** — 기본 모델 · `Field` 제약 · 필드 검증기 · 모델 검증기 · 중첩 모델 · 불변 모델 · `Optional` 필드를 차례로 만들고, 각 장면의 결과를 출력하는 스크립트 하나.

**준비물** — `pip install pydantic` 으로 Pydantic(v2)을 설치한다. 설치되지 않은 환경에서도 스크립트가 죽지 않아야 한다.

**요구 조건**

1단계 — 준비
1. `pydantic` 에서 `BaseModel` · `Field` · `field_validator` · `model_validator` · `ConfigDict` · `EmailStr` 를, `typing` 에서 `Optional` 을, `datetime` 에서 `datetime` 을 `try` 안에서 import 한다.
2. import 에 성공하면 `PYDANTIC_AVAILABLE = True`, `ImportError` 면 `False` 로 두고 설치 안내를 출력한다.
3. `PYDANTIC_AVAILABLE` 이 거짓이면 Pydantic 의 개념(타입 힌트 기반 검증 · 자동 변환 · 직렬화 · 설치 명령)을 문장으로 출력한다.

2단계 — 기본 모델
4. `User` 모델: `name: str` · `age: int` · `email: str` · `is_active: bool` (기본값 `True`).
5. `User` 하나를 만들어 객체 자체, `model_dump()` 결과, `model_dump_json()` 결과를 출력한다.
6. `age="25"` 로 만든 `User` 의 `age` 값과 그 타입 이름을 출력한다.
7. `age="not_a_number"` 로 만들려다 생긴 예외를 잡아 내용을 출력한다.

3단계 — `Field`
8. `Product` 모델: `name` 은 길이 1~100, `price` 는 0보다 크고 설명을 단다, `quantity` 는 0 이상이고 기본값 0, `tags` 는 문자열 리스트로 객체마다 새 빈 리스트가 기본값.
9. 정상 `Product` 하나를 출력하고, `name=""` · `price=-10` 으로 만들려다 생긴 예외의 **타입 이름**을 출력한다.

4단계 — `field_validator`
10. `Account` 모델(`username` · `password` · `email`)에 필드 검증기 셋: `username` 은 영문 · 숫자만 허용하고 소문자로 돌려준다, `password` 는 8자 미만이면 거부한다, `email` 은 `@` 가 없으면 거부하고 소문자로 돌려준다.
11. `username="Alice123"` · `password="securepass"` · `email="Alice@Test.COM"` 으로 만들어 출력한다.

5단계 — `model_validator`
12. `DateRange` 모델(`start` · `end` 모두 `datetime`)에 모든 필드 검증 뒤 도는 검증기를 달아, `start` 가 `end` 보다 앞서지 않으면 거부한다.
13. 2024년 1월 1일 ~ 12월 31일로 만들어 출력한다.

6단계 — 중첩 모델
14. `Address`(`city`, `country` 기본값 `"Korea"`)와, 그것을 `address` 필드로 가진 `Employee`(`name` · `age` · `address` · `skills` 기본값 빈 리스트)를 만든다.
15. `address` 에 dict `{"city": "Seoul"}` 을 넘겨 만든 `Employee` 와 그 `address.city` 를 출력한다.
16. JSON 문자열 `{"name": "Bob", "age": 25, "address": {"city": "Busan"}}` 에서 `Employee` 를 만들어 출력한다.

7단계 — 불변 모델과 `Optional`
17. `FrozenConfig`(`host` · `port`)를 불변으로 설정하고, 만든 뒤 `host` 를 바꾸려다 생긴 예외의 타입 이름을 출력한다.
18. `Profile`(`name`, `bio` · `age` 는 `None` 허용 · 기본값 `None`)을 `name` 만으로 만들어 출력하고, `None` 필드를 뺀 dict 를 출력한다.
19. 장면마다 `=== 기본 모델 ===` 꼴의 제목 줄을 먼저 출력한다.

**시작 코드**

```python
# Pydantic 기초 — 연습

try:
    # TODO: pydantic · typing · datetime 에서 필요한 이름을 import 한다
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False
    print("pydantic이 설치되지 않음. pip install pydantic")

if PYDANTIC_AVAILABLE:
    print("=== 기본 모델 ===")

    class User:  # TODO: BaseModel 상속 · 필드 넷
        pass

    user = User(name="Alice", age=30, email="alice@test.com")
    print(f"User: {user}")
    # TODO: dict 로, JSON 문자열로 바꿔 출력

    user2 = User(name="Bob", age="25", email="bob@test.com")
    print(f"타입 변환: age = {user2.age} ({type(user2.age).__name__})")

    try:
        User(name="Charlie", age="not_a_number", email="test")
    except Exception as e:
        print(f"검증 에러: {e}")

    print("\n=== Field ===")

    class Product:  # TODO: BaseModel 상속 · Field 제약 넷
        pass

    product = Product(name="Widget", price=9.99, quantity=100)
    print(f"Product: {product}")

    try:
        Product(name="", price=-10)
    except Exception as e:
        print(f"Field 검증: {type(e).__name__}")

    print("\n=== Validators ===")

    class Account:  # TODO: BaseModel 상속 · 필드 셋 · field_validator 셋
        pass

    account = Account(
        username="Alice123",
        password="securepass",
        email="Alice@Test.COM"
    )
    print(f"Account: {account}")

    print("\n=== Model Validator ===")

    class DateRange:  # TODO: BaseModel 상속 · start/end · model_validator
        pass

    dr = DateRange(
        start=datetime(2024, 1, 1),
        end=datetime(2024, 12, 31)
    )
    print(f"DateRange: {dr}")

    print("\n=== 중첩 모델 ===")

    class Address:  # TODO
        pass

    class Employee:  # TODO: address 필드의 타입은 Address
        pass

    emp = Employee(
        name="Alice",
        age=30,
        address={"city": "Seoul"},
        skills=["Python", "SQL"]
    )
    print(f"Employee: {emp}")
    print(f"city: {emp.address.city}")

    json_data = '{"name": "Bob", "age": 25, "address": {"city": "Busan"}}'
    emp2 = None  # TODO: JSON 문자열에서 Employee 생성
    print(f"from JSON: {emp2}")

    print("\n=== 불변 모델 ===")

    class FrozenConfig:  # TODO: 불변 설정 · host/port
        pass

    cfg = FrozenConfig(host="localhost", port=8080)
    try:
        cfg.host = "remote"
    except Exception as e:
        print(f"frozen 에러: {type(e).__name__}")

    print("\n=== Optional ===")

    class Profile:  # TODO: name · bio · age
        pass

    p = Profile(name="Alice")
    print(f"Profile: {p}")
    # TODO: None 필드를 뺀 dict 출력
else:
    print("\n=== Pydantic 개념 (코드만) ===")
    # TODO: 개념 설명 세 줄
```

**확인 방법** — `python pydantic-basics.py` 로 돌린다. 장면 제목 일곱 개가 차례로 찍히는지, `age` 가 `int` 로 찍히는지, `Field 검증:` 과 `frozen 에러:` 뒤에 예외 타입 이름이 찍히는지, `Account` 의 `username` · `email` 이 소문자인지, 마지막 dict 에 `name` 만 남는지 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
