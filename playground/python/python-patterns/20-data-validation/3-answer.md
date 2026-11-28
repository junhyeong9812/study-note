# python/python-patterns/20 — 데이터 검증 (Pydantic v2) — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 세 줄 — `name` · `email` · `age` 가 각각 하나씩

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
반복문은 세 줄을 찍는다.
`loc` 은 차례로 `name` · `email` · `age` 필드를 가리킨다(파이썬 튜플 꼴 `('name',)` 처럼 찍힐 것으로 본다).
`msg` 의 정확한 문구는 Pydantic 버전에 따라 다를 수 있다 (확인 필요).

**왜 그런가**
- `name="A"` 는 길이 1 이라 `min_length=2` 를 어긴다.
- `email="invalid"` 는 `@` 와 `.` 이 없어 `pattern` 정규식에 맞지 않는다.
- `age=-1` 은 `ge=0` 을 어긴다.
- `ValidationError` 는 첫 실패에서 멈추지 않고 실패한 칸을 모두 모아 한 번에 던진다 — 근거: 2-summary 「동작 방식 (1)」 · 「(2)」.

### 2. 만들지 못한다 — 검사가 대문자화보다 먼저라서

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
`Product(...)` 는 인스턴스를 만들지 못하고 `ValidationError` 가 난다.
이 줄은 `try` 안에 있지 않으므로 예외가 잡히지 않고, 스크립트는 여기서 트레이스백을 내며 멈춘다.
그 뒤의 `Product:` 출력, 가격 검증 실패, 직렬화 · JSON Schema · 고급 패턴 부분은 실행되지 않는다고 본다.

**왜 그런가**
- `validate_sku` 는 `v.startswith('PRD-')` 를 먼저 보고, 그다음 줄에서야 `v.upper()` 를 한다.
- 들어온 값은 소문자 `"prd-001"` 이라 `'PRD-'` 로 시작하지 않는다 — 대문자로 바뀔 기회가 오기 전에 `ValueError` 가 난다.
- `ValueError` 는 Pydantic 이 `ValidationError` 로 바꿔 던진다.
- 근거: 2-summary 「동작 방식 (3)」 · 「어디서 틀리나 1」.

### 3. `id` 하나가 빠진다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
`model_dump()` 의 키는 `id` · `name` · `email` · `age` · `role` · `tags` · `address` · `created_at` 여덟 개다.
`exclude_none=True` 에서는 `id` 만 빠진 일곱 개가 남는다.
(다만 2번 문항대로 스크립트가 `Product` 줄에서 멈춘다면 이 줄은 실제로는 실행되지 않는다.)

**왜 그런가**
- `user` 를 만들 때 `id` 는 넘기지 않아 기본값 `None` 이다.
- `address` 는 dict 를 넘겨 `Address` 인스턴스가 됐으므로 `None` 이 아니다.
- 나머지 필드도 값이나 기본값(`USER` · 빈 아닌 리스트 · 만든 시각)이 있다.
- 근거: 2-summary 「동작 방식 (6)」 · 「(1)」.

### 4. 인스턴스마다 새 리스트를 주려고

`default_factory=list` 는 인스턴스를 만들 때마다 `list()` 를 불러 새 빈 리스트를 준다.
리스트는 가변 객체라, 기본값 하나를 여러 인스턴스가 함께 쓰면 한 인스턴스의 변경이 다른 인스턴스에 번질 수 있다.
그래서 원본 주석도 「가변 기본값은 default_factory 사용」이라고 적는다.
근거: 2-summary 「동작 방식 (2)」 · 「어디서 틀리나 2」.

### 5. 두 필드를 함께 봐야 하는 검사라서

`field_validator` 는 자기 필드 값 `v` 하나만 받는다.
할인가 검사는 `discount_price` 와 `price` 를 맞대야 하는 교차 검증이다.
`model_validator(mode='after')` 는 모든 필드 검증이 끝난 뒤 완성된 `self` 를 받으므로 두 값을 함께 볼 수 있다.
근거: 2-summary 「동작 방식 (4)」.

### 6. 되읽기에도 검증 · 변환이 그대로 돌아서

`model_validate_json` 은 JSON 을 그냥 dict 로 풀어 두는 것이 아니라, 모델 생성과 같은 검증을 거친다.
`created_at` 칸의 타입은 `datetime` 이므로 JSON 안의 날짜 문자열이 그 칸의 검증에서 `datetime` 으로 바뀐다.
생성자에 dict 를 넣으면 `Address` 가 되는 것과 같은 원리다.
근거: 2-summary 「동작 방식 (6)」 · 「(1)」.

### 7. 평가되지 않는다 — `and` 의 왼쪽에서 걸러진다

조건은 `if self.discount_price and self.discount_price >= self.price` 다.
`0.0` 은 거짓 취급이라 `and` 의 왼쪽에서 끝나고, 비교는 평가되지 않은 채 검사를 통과한다.
`None` 도 같은 길로 통과한다.
근거: 2-summary 「동작 방식 (4)」 · 「어디서 틀리나 3」.

### 8. 만든 뒤의 대입만 막는다 — 만들 때 값을 넘기는 것은 된다

`frozen=True` 는 이미 만들어진 인스턴스의 필드에 다시 대입하는 것(`config.host = "other"`)을 막는다.
이 대입은 `ValidationError` 로 잡힌다.
`ImmutableConfig(host="other")` 처럼 생성자에 값을 넘기는 것은 막히지 않는다.
근거: 2-summary 「동작 방식 (5)」 · 「어디서 틀리나 5」.

### 9. 같은 규칙을 타입 이름 하나로 묶은 것

`PositiveInt` 는 「`int` + `Field(gt=0)`」를 한 이름으로 묶은 별칭이다.
그래서 `count: PositiveInt` 는 `count: int = Field(gt=0)` 와 같은 규칙을 걸고, 여러 필드 · 모델에서 다시 쓸 수 있다.
타입에 메타데이터를 붙이는 문법 `Annotated` 는 표준 `typing`(PEP 593)이 맡는다.
붙은 `Field(...)` 를 검증 규칙으로 읽는 것은 Pydantic 이 맡는다.
근거: 2-summary 「동작 방식 (8)」 · 「구현 세부사항 대 언어 보장」.

### 10. 모델이 스키마의 원천이라서

`model_json_schema()` 는 필드 타입 · `Field` 제약 · 기본값을 JSON Schema 꼴로 뽑는다.
이 스키마를 OpenAPI · Swagger 같은 API 문서에 넣어 「받는 데이터의 꼴」을 알린다.
검증 규칙과 문서가 같은 모델 정의에서 나오므로, 규칙을 고치면 문서도 함께 바뀌어 어긋나지 않는다.
근거: 2-summary 「동작 방식 (7)」 · 원본 팁.

## 실습 정답

### 실습 1. Pydantic v2 로 사용자 · 상품 검증과 직렬화 한 바퀴

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. `UserRole` 세 값 | `class UserRole(str, Enum)` · `ADMIN` / `USER` / `GUEST` |
| 2. 우편번호 다섯 자리 | `Address.zipcode = Field(pattern=r'^\d{5}$')` |
| 3. 공백 제거 · 빈 문자열 금지 | `User.model_config = ConfigDict(str_strip_whitespace=True, str_min_length=1)` |
| 4. `User` 필드 여덟 개 | `id` · `name = Field(..., min_length=2, max_length=50)` · `email = Field(..., pattern=...)` · `age = Field(..., ge=0, le=150)` · `role = UserRole.USER` · `tags = Field(default_factory=list, max_length=10)` · `address: Optional[Address] = None` · `created_at = Field(default_factory=datetime.now)` |
| 5. 유효한 `user` 출력 | `user = User(...)` · `print(f"User: ...")` 세 줄 |
| 6. 실패한 칸 전부 출력 | `try: bad_user = User(...)` · `for error in e.errors()` |
| 7. `Product` 필드 | `price: float = Field(gt=0)` · `discount_price: Optional[float] = None` |
| 8. SKU 검사 후 대문자 | `@field_validator('sku')` `validate_sku` |
| 9. 이름 손질 | `@field_validator('name')` `validate_name` · `v.strip().title()` |
| 10. 할인가 교차 검증 | `@model_validator(mode='after')` `validate_prices` |
| 11. `product` 만들고 출력 | `product = Product(name="  python book  ", ..., sku="prd-001")` |
| 12. 가격 검증 실패 출력 | `try: Product(name="bad", price=100, discount_price=200, ...)` · `e.errors()[0]['msg']` |
| 13. dict 키 목록 | `user.model_dump()` |
| 14. 세 필드만 | `user.model_dump(include={'name', 'email', 'role'})` |
| 15. `None` 제외 | `user.model_dump(exclude_none=True)` |
| 16. JSON 앞 80자 | `user.model_dump_json(indent=2)` · `user_json[:80]` |
| 17. JSON → User | `User.model_validate_json(user_json)` |
| 18. dict → User | `User.model_validate({...})` |
| 19. JSON Schema 앞 300자 | `User.model_json_schema()` · `json.dumps(..., ensure_ascii=False)[:300]` |
| 20. 커스텀 타입과 `Stats` | `PositiveInt = Annotated[int, Field(gt=0)]` · `Percentage = Annotated[float, Field(ge=0, le=100)]` · `class Stats` |
| 21. 불변 모델 대입 실패 | `ImmutableConfig.model_config = ConfigDict(frozen=True)` · `config.host = "other"` in `try` |
| 22. 핵심 정리 출력 | 마지막 `print` 여섯 줄 |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`python/python-patterns/reference/data-validation.py`

```python
# [디자인 패턴 & 실무] 데이터 검증 (Pydantic v2)
# 설명: Pydantic v2의 BaseModel, Field, validator, 커스텀 타입, JSON Schema
# 팁: Pydantic v2는 Rust 기반(pydantic-core)으로 v1보다 5~50배 빠르다. Field로 검증 규칙을 선언하고, validator로 커스텀 로직을 추가한다. model_config = ConfigDict(...)로 모델 동작을 세밀하게 제어할 수 있다. JSON Schema 자동 생성은 API 문서화에 유용하다.

# Pydantic v2 핵심 import: 모델/필드/검증기/설정/내장타입/예외
from pydantic import (
    BaseModel, Field, field_validator, model_validator,
    ConfigDict, EmailStr, ValidationError
)
# Annotated는 타입에 메타데이터를 부착하는 PEP 593 문법
from typing import Optional, Annotated
from datetime import datetime, date
# 문자열 enum을 위한 Enum 베이스
from enum import Enum
import json

# === 1. 기본 모델 ===
print("=== 기본 모델 ===")

# str을 상속한 Enum: 값이 문자열이라 JSON 직렬화에 친화적
class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"
    GUEST = "guest"

# 중첩 모델: User 안에 Address가 들어감
class Address(BaseModel):
    street: str
    city: str
    # 정규식으로 우편번호 5자리 검증
    zipcode: str = Field(pattern=r'^\d{5}$')  # 정규식 검증

# 사용자 모델
class User(BaseModel):
    # 모델 전체 동작 설정 (v2 신문법)
    model_config = ConfigDict(
        str_strip_whitespace=True,  # 문자열 앞뒤 공백 제거
        str_min_length=1,           # 빈 문자열 금지
    )

    # Optional + 기본값 None: 신규 생성 시 id 없음
    id: Optional[int] = None
    # ...(Ellipsis)는 필수 필드를 의미
    name: str = Field(..., min_length=2, max_length=50)
    email: str = Field(..., pattern=r'^[\w.-]+@[\w.-]+\.\w+$')
    # ge/le = greater/less than or equal (이상/이하)
    age: int = Field(..., ge=0, le=150)
    role: UserRole = UserRole.USER
    # 가변 기본값은 default_factory 사용
    tags: list[str] = Field(default_factory=list, max_length=10)
    address: Optional[Address] = None
    # 인스턴스 생성 시점의 시각을 기본값으로
    created_at: datetime = Field(default_factory=datetime.now)

# 유효한 데이터: dict로 중첩 모델도 자동 변환됨
user = User(
    name="김철수",
    email="kim@example.com",
    age=30,
    tags=["developer", "python"],
    address={"street": "강남대로 1", "city": "서울", "zipcode": "06000"}
)
print(f"User: {user.name} ({user.email})")
print(f"Address: {user.address}")
print(f"Tags: {user.tags}")

# 잘못된 데이터: ValidationError로 모든 에러를 한 번에 받음
print("\n유효성 검사 실패:")
try:
    bad_user = User(name="A", email="invalid", age=-1)
except ValidationError as e:
    # .errors()로 에러 목록을 구조화된 형태로 받음
    for error in e.errors():
        print(f"  {error['loc']}: {error['msg']}")

# === 2. field_validator / model_validator ===
print("\n=== Validator ===")

class Product(BaseModel):
    name: str
    # gt=0: greater than zero (양수만)
    price: float = Field(gt=0)
    discount_price: Optional[float] = None
    sku: str

    # 필드 단위 검증기: 'sku' 필드를 검증/변환
    @field_validator('sku')
    @classmethod
    def validate_sku(cls, v: str) -> str:
        if not v.startswith('PRD-'):
            raise ValueError('SKU는 PRD-로 시작해야 합니다')
        # 변환된 값을 반환 (Pydantic이 이 값을 사용)
        return v.upper()

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        # title()로 단어 첫 글자 대문자화
        return v.strip().title()  # 변환도 가능

    # 모델 전체 검증기 (mode='after': 필드 검증 후 호출)
    # 여러 필드 간의 관계 검증에 사용
    @model_validator(mode='after')
    def validate_prices(self) -> 'Product':
        if self.discount_price and self.discount_price >= self.price:
            raise ValueError('할인가는 정가보다 낮아야 합니다')
        return self

product = Product(name="  python book  ", price=30000, discount_price=25000, sku="prd-001")
print(f"Product: {product.name}, {product.price}, SKU: {product.sku}")

try:
    Product(name="bad", price=100, discount_price=200, sku="PRD-002")
except ValidationError as e:
    print(f"가격 검증 실패: {e.errors()[0]['msg']}")

# === 3. 직렬화 / 역직렬화 ===
print("\n=== 직렬화 ===")

# Model -> dict (v2 신메서드, v1의 .dict() 대체)
user_dict = user.model_dump()
print(f"model_dump: {list(user_dict.keys())}")

# include로 특정 필드만 직렬화 (set/dict 가능)
partial = user.model_dump(include={'name', 'email', 'role'})
print(f"include: {partial}")

# None인 필드 제외 (API 응답 최적화에 유용)
no_none = user.model_dump(exclude_none=True)
print(f"exclude_none 키: {list(no_none.keys())}")

# Model -> JSON 문자열 (datetime 등도 자동 직렬화)
user_json = user.model_dump_json(indent=2)
print(f"JSON: {user_json[:80]}...")

# JSON -> Model
user_from_json = User.model_validate_json(user_json)
print(f"From JSON: {user_from_json.name}")

# dict -> Model (v1의 parse_obj 대체)
user_from_dict = User.model_validate({
    "name": "이영희", "email": "lee@example.com", "age": 25
})
print(f"From dict: {user_from_dict.name}")

# === 4. JSON Schema ===
print("\n=== JSON Schema ===")
# OpenAPI/Swagger 등 API 문서 자동 생성에 활용
schema = User.model_json_schema()
# ensure_ascii=False로 한글 그대로 출력
print(json.dumps(schema, indent=2, ensure_ascii=False)[:300] + "...")

# === 5. 고급 패턴 ===
print("\n=== 고급 패턴 ===")

# Annotated로 재사용 가능한 커스텀 타입 정의
PositiveInt = Annotated[int, Field(gt=0)]
Percentage = Annotated[float, Field(ge=0, le=100)]

# 정의한 타입 별칭을 모델에서 사용
class Stats(BaseModel):
    count: PositiveInt
    success_rate: Percentage

stats = Stats(count=100, success_rate=95.5)
print(f"Stats: count={stats.count}, rate={stats.success_rate}%")

# 불변 모델: frozen=True로 인스턴스 수정 금지
class ImmutableConfig(BaseModel):
    model_config = ConfigDict(frozen=True)
    host: str = "localhost"
    port: int = 8080

config = ImmutableConfig()
try:
    config.host = "other"  # 에러!
except ValidationError as e:
    print(f"Frozen: {e.errors()[0]['msg']}")

print("\n=== Pydantic v2 핵심 정리 ===")
print("model_dump() / model_dump_json():  직렬화")
print("model_validate() / model_validate_json():  역직렬화")
print("model_json_schema():  JSON Schema 생성")
print("field_validator:  필드 단위 검증/변환")
print("model_validator:  모델 전체 교차 검증")
print("ConfigDict:  모델 설정 (frozen, strip 등)")
```

**실행 결과** — 실행하지 않음 — 외부 라이브러리 `pydantic` 가 있어야 도는 예제다 — 그것 없이 만들어 실행하지 않았다.

**풀이 요점**
- 규칙은 먼저 `Field` · `ConfigDict` · `Annotated` 로 선언하고, 선언으로 못 적는 것만 validator 에 둔다.
- `validate_sku` 는 검사가 대문자화보다 먼저라, 정답 코드 그대로면 `sku="prd-001"` 줄에서 잡히지 않은 `ValidationError` 로 멈출 것으로 읽힌다 — 2단계 이후를 끝까지 보려면 `v = v.upper()` 를 검사 앞으로 옮기거나 입력을 `"PRD-001"` 로 바꿔 본다 (원본에 근거 없음 — 추론).
- 실패 칸을 다 보려면 `e.errors()` 를 돌고, 한 칸만 볼 때만 `[0]` 을 쓴다.
- 직렬화 네 메서드는 짝으로 외운다 — `model_dump` ↔ `model_validate`, `model_dump_json` ↔ `model_validate_json`.
- `frozen=True` 의 대입 실패는 `ValidationError` 로 잡는다 — 정답 코드의 `except` 도 그 예외를 기다린다.
- 정답 코드의 `EmailStr` · `date` import 는 쓰이지 않는다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — 외부 라이브러리 `pydantic` 가 있어야 도는 예제다 — 그것 없이 만들어 실행하지 않았다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
