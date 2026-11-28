# python/python-oop/19 — Pydantic 기초 — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. `age` 는 정수 25 로 바뀐다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
타입 변환: age = 25 (int)
```

**왜 그런가**
`age: int` 필드에 문자열 `"25"` 가 들어왔다.
숫자로 읽을 수 있는 문자열이라 Pydantic 이 `int` 25 로 바꿔 저장한다.
그래서 `type(user2.age).__name__` 은 `str` 이 아니라 `int` 다.
근거: 2-summary 「동작 방식 (1)」.

### 2. `ValidationError` 하나에 오류 두 건

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
Field 검증: ValidationError
```

오류는 두 건이다 — `name`(길이 0 < `min_length=1`)과 `price`(`-10` 은 `gt=0` 을 어긴다).

**왜 그런가**
Pydantic 은 첫 오류에서 멈추지 않고 필드를 끝까지 돌며 오류를 모은다.
`quantity` 는 기본값 0 이 `ge=0` 을 만족하고, `tags` 는 `default_factory` 로 빈 리스트를 받으므로 오류가 아니다.
`print` 는 예외의 타입 이름만 찍으므로 두 건이라는 사실은 출력에 드러나지 않는다.
근거: 2-summary 「동작 방식 (2)」 · 「동작 방식 (3)」.

### 3. 둘 다 소문자로 정규화된다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

- `account.username` → `"alice123"`
- `account.email` → `"alice@test.com"`
- (`password` 는 10자라 통과하고 `"securepass"` 그대로다)

**왜 그런가**
`"Alice123"` 은 영문과 숫자로만 되어 있어 `isalnum()` 이 참이다.
검증기는 `v.lower()` 를 돌려주고, 돌려준 값이 필드에 저장된다.
`email` 도 `@` 가 있어 통과하고 소문자로 바뀐다.
근거: 2-summary 「동작 방식 (4)」.

### 4. `age` 하나만 걸린다 — `email` 은 타입만 본다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
실패하는 필드는 `age` 하나다.

**왜 그런가**
`"not_a_number"` 는 정수로 읽을 수 없어 변환이 실패한다.
`email: str` 은 「문자열이면 된다」는 규칙이라 `"test"` 도 문자열이므로 통과한다.
`User` 에는 이메일 형식을 보는 검증기가 없고, import 한 `EmailStr` 도 쓰이지 않는다.
근거: 2-summary 「동작 방식 (2)」 · 「어디서 틀리나 1」.

### 5. Pydantic 이 `ValueError` 를 받아 오류 한 건으로 감싼다

검증기는 「이 값이 틀렸다」는 신호로 `ValueError` 를 던질 뿐이다.
Pydantic 이 그것을 받아 어느 필드의 오류인지 붙여 기록하고, 모든 오류를 모아 `ValidationError` 하나로 던진다.
그래서 생성하는 쪽은 어느 검증 단계에서 틀렸든 한 가지 예외만 처리하면 된다.
근거: 2-summary 「동작 방식 (4)」 · 「어디서 틀리나 3」.

### 6. 값 하나로는 비교할 상대가 없기 때문이다

`field_validator` 는 필드 하나의 값 `v` 만 받으므로 `start` 를 보는 동안 `end` 를 알 수 없다.
`model_validator(mode='after')` 는 모든 필드 검증이 끝난 뒤 완성된 인스턴스를 `self` 로 받는다.
그래서 `self.start` 와 `self.end` 가 둘 다 `datetime` 으로 확정된 상태에서 비교할 수 있다.
근거: 2-summary 「동작 방식 (5)」.

### 7. 생성은 되고, 생성 뒤 대입이 막힌다

`FrozenConfig(host="localhost", port=8080)` 은 보통 모델처럼 만들어진다.
`cfg.host = "remote"` 처럼 만든 뒤 속성에 대입하면 예외가 난다.
원본은 그 예외의 타입 이름을 출력한다.
값을 바꾸고 싶으면 새 객체를 만들어야 한다.
근거: 2-summary 「동작 방식 (8)」 · 「어디서 틀리나 7」.

### 8. `bio` 는 `None`, 결과에는 `name` 만 남는다

`bio: Optional[str] = None` 이라 값을 넣지 않으면 기본값 `None` 이 들어간다(`age` 도 같다).
`model_dump(exclude_none=True)` 는 `None` 인 필드를 빼므로 `{'name': 'Alice'}` 꼴의 dict 가 남는다.
근거: 2-summary 「동작 방식 (7)」 · 「동작 방식 (8)」.

### 9. 「하나를 나눠 쓰는 기본값」을 「객체마다 새로 만드는 기본값」으로 바꾼다

파이썬 함수의 `def f(x=[])` 는 그 리스트 하나를 모든 호출이 나눠 써서, 한 호출에서 고친 내용이 다음 호출에 남는다.
`Field(default_factory=list)` 는 기본값 자체가 아니라 기본값을 만들 함수를 적어 두고, 객체를 만들 때마다 `list()` 를 불러 새 리스트를 준다.
그래서 한 `Product` 의 `tags` 를 고쳐도 다른 `Product` 에 번지지 않는다.
원본의 `Employee.skills = []` 는 Pydantic 이 복사해 준다는 설명이 있어 문제가 없을 수도 있다(확인 필요).
근거: 2-summary 「동작 방식 (3)」 · 「어디서 틀리나 6」.

### 10. 안쪽도 같은 검증을 거치고, 들어오는 길과 나가는 길이 짝을 이룬다

`model_validate_json` 은 JSON 문자열을 읽어 `Employee` 의 규칙대로 검증한다.
`address` 칸의 타입이 `Address` 이므로 그 안의 `{"city": "Busan"}` 도 `Address` 로 검증 · 생성되고, 빠진 `country` 에는 기본값 `"Korea"` 가 들어간다.
`model_dump_json` 은 거꾸로 검증된 모델을 JSON 문자열로 내보낸다.
즉 「JSON → 검증된 객체」(`model_validate_json`)와 「객체 → JSON」(`model_dump_json`)이 직렬화의 양방향이다.
근거: 2-summary 「동작 방식 (6)」 · 「동작 방식 (7)」.

## 실습 정답

### 실습 1. Pydantic 모델 여덟 장면 만들기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. 이름들 import | `try:` 안의 `from pydantic import ...` · `from typing import Optional` · `from datetime import datetime` |
| 2. 설치 여부 깃발 | `PYDANTIC_AVAILABLE = True` / `except ImportError:` 의 `False` 와 안내 `print` |
| 3. 설치 안 됐을 때 개념 출력 | `else:` 아래 `print` 네 줄 |
| 4. `User` 필드 넷 | `class User(BaseModel):` · `is_active: bool = True` |
| 5. 객체 · dict · JSON 출력 | `print(f"User: {user}")` · `user.model_dump()` · `user.model_dump_json()` |
| 6. 자동 변환 확인 | `User(..., age="25", ...)` · `type(user2.age).__name__` |
| 7. 검증 실패 출력 | `User(..., age="not_a_number", ...)` 를 감싼 `try`/`except` |
| 8. `Product` 제약 | `Field(min_length=1, max_length=100)` · `Field(gt=0, description=...)` · `Field(ge=0, default=0)` · `Field(default_factory=list)` |
| 9. 정상 출력 · 예외 타입 이름 | `print(f"Product: {product}")` · `type(e).__name__` |
| 10. 필드 검증기 셋 | `username_alphanumeric` · `password_strength` · `email_valid` (`@field_validator` + `@classmethod`) |
| 11. `Account` 생성 · 출력 | `Account(username="Alice123", ...)` · `print(f"Account: {account}")` |
| 12. 필드 사이 검증 | `@model_validator(mode='after')` 의 `check_dates` |
| 13. `DateRange` 생성 · 출력 | `DateRange(start=datetime(2024, 1, 1), end=datetime(2024, 12, 31))` |
| 14. 중첩 모델 둘 | `class Address` (`country: str = "Korea"`) · `class Employee` (`address: Address`, `skills: list[str] = []`) |
| 15. dict 로 넘긴 주소 | `address={"city": "Seoul"}` · `emp.address.city` |
| 16. JSON 에서 생성 | `Employee.model_validate_json(json_data)` |
| 17. 불변 모델 | `model_config = ConfigDict(frozen=True)` · `cfg.host = "remote"` 를 감싼 `try`/`except` |
| 18. `Optional` · `None` 제외 | `bio: Optional[str] = None` · `age: Optional[int] = None` · `p.model_dump(exclude_none=True)` |
| 19. 장면 제목 줄 | `print("=== 기본 모델 ===")` · `print("\n=== Field ===")` 등 |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`python/python-oop/reference/pydantic-basics.py`

```python
# [객체지향 프로그래밍] Pydantic 기초
# 설명: Pydantic BaseModel, Field, validator, 데이터 검증
# 팁: Pydantic v2는 Rust 기반으로 매우 빠르다. API 입력 검증, 설정 관리, 데이터 파이프라인에 적합하다. FastAPI와 함께 사용하면 강력하다.

# Pydantic v2 - 데이터 검증 라이브러리
# pip install pydantic

# pydantic이 없는 환경에서도 동작하도록 try/except로 import
try:
    # BaseModel: 모델 베이스, Field: 필드 메타정보, field_validator/model_validator: 검증
    from pydantic import BaseModel, Field, field_validator, model_validator
    # ConfigDict: 모델 설정 딕셔너리, EmailStr: 이메일 타입
    from pydantic import ConfigDict, EmailStr
    from typing import Optional
    from datetime import datetime
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False
    print("pydantic이 설치되지 않음. pip install pydantic")

if PYDANTIC_AVAILABLE:
    # === 기본 모델 ===
    print("=== 기본 모델 ===")

    # BaseModel을 상속하면 타입 힌트 기반 검증/직렬화가 자동
    class User(BaseModel):
        name: str
        age: int
        email: str
        is_active: bool = True

    user = User(name="Alice", age=30, email="alice@test.com")
    print(f"User: {user}")
    # model_dump: dict로 변환 (v1의 .dict() 대체)
    print(f"dict: {user.model_dump()}")
    # model_dump_json: JSON 문자열로 직렬화
    print(f"json: {user.model_dump_json()}")

    # 자동 타입 변환: 문자열 "25"가 int 25로 자동 변환됨
    user2 = User(name="Bob", age="25", email="bob@test.com")  # str -> int
    print(f"타입 변환: age = {user2.age} ({type(user2.age).__name__})")

    # 검증 실패 → ValidationError
    try:
        User(name="Charlie", age="not_a_number", email="test")
    except Exception as e:
        print(f"검증 에러: {e}")

    # === Field ===
    print("\n=== Field ===")

    # Field: 필드에 제약 조건과 메타데이터 지정
    class Product(BaseModel):
        # min_length/max_length: 문자열 길이 제약
        name: str = Field(min_length=1, max_length=100)
        # gt: greater than (>0). description은 문서화용
        price: float = Field(gt=0, description="가격 (양수)")
        # ge: greater or equal (>=0). default 지정
        quantity: int = Field(ge=0, default=0)
        # default_factory: 가변 기본값 안전하게 처리
        tags: list[str] = Field(default_factory=list)

    product = Product(name="Widget", price=9.99, quantity=100)
    print(f"Product: {product}")

    # Field 제약 위반 → 검증 에러
    try:
        Product(name="", price=-10)
    except Exception as e:
        print(f"Field 검증: {type(e).__name__}")

    # === field_validator ===
    print("\n=== Validators ===")

    class Account(BaseModel):
        username: str
        password: str
        email: str

        # field_validator: 특정 필드에 대한 커스텀 검증
        @field_validator('username')
        @classmethod
        def username_alphanumeric(cls, v):
            # 영문/숫자만 허용
            if not v.isalnum():
                raise ValueError('영문/숫자만 허용')
            # 정규화도 함께 (소문자로)
            return v.lower()

        @field_validator('password')
        @classmethod
        def password_strength(cls, v):
            # 비밀번호 강도 검증
            if len(v) < 8:
                raise ValueError('8자 이상 필요')
            return v

        @field_validator('email')
        @classmethod
        def email_valid(cls, v):
            if '@' not in v:
                raise ValueError('유효한 이메일 필요')
            return v.lower()

    account = Account(
        username="Alice123",
        password="securepass",
        email="Alice@Test.COM"
    )
    print(f"Account: {account}")

    # === model_validator ===
    print("\n=== Model Validator ===")

    class DateRange(BaseModel):
        start: datetime
        end: datetime

        # model_validator(mode='after'): 모든 필드 검증 완료 후 모델 전체 검증
        @model_validator(mode='after')
        def check_dates(self):
            # 필드 간 관계 검증 (단일 필드 검증으로는 불가능)
            if self.start >= self.end:
                raise ValueError('start는 end보다 이전이어야 함')
            return self

    dr = DateRange(
        start=datetime(2024, 1, 1),
        end=datetime(2024, 12, 31)
    )
    print(f"DateRange: {dr}")

    # === 중첩 모델 ===
    print("\n=== 중첩 모델 ===")

    class Address(BaseModel):
        city: str
        country: str = "Korea"

    # 다른 BaseModel을 필드로 가질 수 있음 (자동으로 중첩 검증)
    class Employee(BaseModel):
        name: str
        age: int
        address: Address
        skills: list[str] = []

    # dict를 넘기면 Address가 자동 생성됨
    emp = Employee(
        name="Alice",
        age=30,
        address={"city": "Seoul"},
        skills=["Python", "SQL"]
    )
    print(f"Employee: {emp}")
    print(f"city: {emp.address.city}")

    # JSON 문자열에서 직접 생성
    json_data = '{"name": "Bob", "age": 25, "address": {"city": "Busan"}}'
    # model_validate_json: JSON → 모델 인스턴스
    emp2 = Employee.model_validate_json(json_data)
    print(f"from JSON: {emp2}")

    # === 불변 모델 ===
    print("\n=== 불변 모델 ===")

    class FrozenConfig(BaseModel):
        # ConfigDict로 모델 설정 지정 (v2 방식)
        model_config = ConfigDict(frozen=True)

        host: str
        port: int

    cfg = FrozenConfig(host="localhost", port=8080)
    # frozen 모델은 변경 시도 시 에러
    try:
        cfg.host = "remote"
    except Exception as e:
        print(f"frozen 에러: {type(e).__name__}")

    # === Optional 필드 ===
    print("\n=== Optional ===")

    class Profile(BaseModel):
        name: str
        # Optional[str] = None: None 허용 + 기본값 None
        bio: Optional[str] = None
        age: Optional[int] = None

    p = Profile(name="Alice")
    print(f"Profile: {p}")
    # exclude_none: 직렬화 시 None 필드 제외
    print(f"dict (exclude_none): {p.model_dump(exclude_none=True)}")
else:
    # pydantic 없이 기본 개념 설명
    print("\n=== Pydantic 개념 (코드만) ===")
    print("Pydantic은 타입 힌트 기반 데이터 검증 라이브러리")
    print("주요 기능: 자동 타입 변환, 검증, 직렬화")
    print("설치: pip install pydantic")
```

**실행 결과** — 실행하지 않음 — 외부 라이브러리 `pydantic` 가 있어야 도는 예제다 — 그것 없이 만들어 실행하지 않았다.

**풀이 요점**
- 필드는 타입 힌트 한 줄이고, 기본값이 없는 필드는 필수다 — `User` 의 `is_active` 만 생략할 수 있다.
- 제약은 층으로 쌓인다: 타입 → `Field` → `field_validator` → `model_validator(mode='after')`.
- 검증기는 규칙을 어기면 `ValueError` 를 던지고, 통과하면 저장할 값(`v.lower()`, `self`)을 돌려준다.
- 중첩 모델에는 dict 를 넘겨도 되고, `model_validate_json` 은 JSON 문자열에서 같은 검증을 거쳐 객체를 만든다.
- 설정은 `model_config = ConfigDict(frozen=True)` 로 적고, `None` 을 빼고 내보낼 때는 `exclude_none=True` 를 준다.
- `try`/`except ImportError` 와 깃발 하나로, Pydantic 이 없는 환경에서도 스크립트가 끝까지 돈다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — 외부 라이브러리 `pydantic` 가 있어야 도는 예제다 — 그것 없이 만들어 실행하지 않았다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
