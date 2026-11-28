# python/python-patterns/20 — 데이터 검증 (Pydantic v2) — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 세 칸이 동시에 어긋난 `User` (예측)

```python
# 질문용 발췌
try:
    bad_user = User(name="A", email="invalid", age=-1)
except ValidationError as e:
    for error in e.errors():
        print(f"  {error['loc']}: {error['msg']}")
```

- `User` 의 `Field` 선언을 떠올릴 때, 이 반복문은 몇 줄을 찍고 각 줄의 `loc` 은 어느 필드인가?

### 2. 소문자 SKU 로 `Product` 만들기 (예측)

```python
# 질문용 발췌
@field_validator('sku')
@classmethod
def validate_sku(cls, v: str) -> str:
    if not v.startswith('PRD-'):
        raise ValueError('SKU는 PRD-로 시작해야 합니다')
    return v.upper()

product = Product(name="  python book  ", price=30000, discount_price=25000, sku="prd-001")
```

- 이 `Product(...)` 줄은 인스턴스를 만들어 내나, 만들어 낸다면 `sku` 는 무엇이 되고 못 만든다면 그다음 스크립트는 어떻게 되나?

### 3. `exclude_none=True` 로 뽑은 키 (예측)

- 원본의 `user`(김철수)를 `model_dump()` 한 키 목록과 견주면, `model_dump(exclude_none=True)` 에서는 어느 키가 빠지나?

### 4. `tags` 기본값을 `default_factory=list` 로 주는 까닭 (왜)

- `tags` 의 기본값을 `[]` 값이 아니라 `default_factory=list` 라는 함수로 주는 까닭은 무엇인가?

### 5. 할인가 검사를 `model_validator(mode='after')` 에 두는 까닭 (왜)

- 「할인가는 정가보다 낮아야 한다」는 검사를 `field_validator` 가 아니라 `model_validator(mode='after')` 에 두는 까닭은 무엇인가?

### 6. 되읽은 JSON 의 날짜가 다시 `datetime` 이 되는 까닭 (왜)

- `model_dump_json` 이 `created_at` 을 문자열로 적었는데도 `model_validate_json` 으로 되읽으면 `datetime` 으로 돌아오는 까닭은 무엇인가?

### 7. `discount_price` 가 `0.0` 일 때의 가격 검사 (경계)

- `Product` 에 `discount_price=0.0` 을 넘기면 `validate_prices` 의 비교 `discount_price >= price` 는 평가되나?

### 8. `frozen=True` 가 막는 범위 (경계)

- `ImmutableConfig` 에서 `frozen=True` 가 막는 것은 무엇이고, `ImmutableConfig(host="other")` 처럼 만들 때 값을 넘기는 것도 막히나?

### 9. `Field(gt=0)` 와 `PositiveInt` 의 관계 (연결)

- 필드마다 `Field(gt=0)` 를 적는 방식과 `PositiveInt = Annotated[int, Field(gt=0)]` 를 쓰는 방식은 어떻게 이어지고, 표준 `typing` 과 Pydantic 이 각각 맡는 몫은 무엇인가?

### 10. `model_json_schema()` 와 API 문서 (연결)

- `model_json_schema()` 로 뽑은 스키마는 API 문서화와 어떻게 이어지고, 검증 규칙과 문서가 어긋나지 않는 까닭은 무엇인가?

## 실습

### 실습 1. Pydantic v2 로 사용자 · 상품 검증과 직렬화 한 바퀴

**만들 것** — 사용자 · 주소 · 상품 · 통계 · 설정 모델을 정의하고, 검증 성공과 실패, dict · JSON 왕복, JSON Schema 출력, 커스텀 타입과 불변 모델까지 차례로 보이는 스크립트를 만든다.

**준비물** — 외부 라이브러리 `pydantic`(v2)이 필요하다(`pip install pydantic`).

**요구 조건**

1단계 — 기본 모델
1. `str` 과 `Enum` 을 함께 상속한 `UserRole` 에 `ADMIN` · `USER` · `GUEST` 세 값을 둔다.
2. `Address` 모델은 `street` · `city` · `zipcode` 를 갖고, `zipcode` 는 정규식으로 숫자 다섯 자리만 받는다.
3. `User` 모델은 `ConfigDict` 로 문자열 앞뒤 공백 제거와 빈 문자열 금지를 건다.
4. `User` 의 필드: `id`(고를 수 있음, 기본 `None`) · `name`(필수, 길이 2~50) · `email`(필수, 정규식 형식) · `age`(필수, 0 이상 150 이하) · `role`(기본 `USER`) · `tags`(문자열 리스트, 인스턴스마다 새 빈 리스트, 원소 10개 이하) · `address`(고를 수 있는 `Address`, 기본 `None`) · `created_at`(만든 시각이 기본값).
5. `address` 를 dict 로 넘겨 유효한 `user` 를 만들고 이름 · 이메일, 주소, 태그를 찍는다.
6. `name="A", email="invalid", age=-1` 로 만들기를 시도해 `ValidationError` 의 에러마다 `loc` 과 `msg` 를 찍는다.

2단계 — validator
7. `Product` 모델은 `name` · `price`(0 초과) · `discount_price`(고를 수 있음, 기본 `None`) · `sku` 를 갖는다.
8. `sku` 필드 검증기는 값이 `PRD-` 로 시작하지 않으면 `ValueError` 를 던지고, 통과하면 대문자로 바꿔 돌려준다.
9. `name` 필드 검증기는 앞뒤 공백을 지우고 단어 첫 글자를 대문자로 바꿔 돌려준다.
10. 모델 검증기(`mode='after'`)는 할인가가 있고 정가 이상이면 `ValueError` 를 던지고, 아니면 `self` 를 돌려준다.
11. `name="  python book  ", price=30000, discount_price=25000, sku="prd-001"` 로 `product` 를 만들고 이름 · 가격 · SKU 를 찍는다.
12. 할인가 200 · 정가 100 인 `Product` 를 `try` 안에서 만들어 첫 에러의 `msg` 를 찍는다.

3단계 — 직렬화 / 역직렬화
13. `user` 를 dict 로 바꿔 키 목록을 찍는다.
14. `name` · `email` · `role` 만 담은 dict 를 찍는다.
15. `None` 인 필드를 뺀 dict 의 키 목록을 찍는다.
16. `user` 를 들여쓰기 2 의 JSON 문자열로 바꿔 앞 80자를 찍는다.
17. 그 JSON 문자열을 다시 `User` 로 읽어 이름을 찍는다.
18. dict(`name` · `email` · `age` 만)를 `User` 로 읽어 이름을 찍는다.

4단계 — JSON Schema
19. `User` 의 JSON Schema 를 뽑아 한글을 그대로 둔 채 들여쓰기 2 로 문자열화해 앞 300자를 찍는다.

5단계 — 고급 패턴
20. `Annotated` 로 `PositiveInt`(정수, 0 초과)와 `Percentage`(실수, 0 이상 100 이하)를 정의하고, 두 타입을 쓰는 `Stats` 모델로 값을 만들어 찍는다.
21. `frozen=True` 인 `ImmutableConfig`(`host` 기본 `"localhost"`, `port` 기본 `8080`)를 만들고, `host` 에 대입을 시도해 `ValidationError` 의 첫 `msg` 를 찍는다.
22. 마지막에 핵심 정리 여섯 줄을 찍는다.

**시작 코드**

```python
from pydantic import (
    BaseModel, Field, field_validator, model_validator,
    ConfigDict, EmailStr, ValidationError
)
from typing import Optional, Annotated
from datetime import datetime, date
from enum import Enum
import json

# === 1. 기본 모델 ===
print("=== 기본 모델 ===")

class UserRole(str, Enum):
    # TODO: ADMIN / USER / GUEST
    pass

class Address(BaseModel):
    street: str
    city: str
    # TODO: zipcode — 숫자 5자리 정규식

class User(BaseModel):
    # TODO: model_config — 공백 제거, 빈 문자열 금지

    # TODO: id, name, email, age, role, tags, address, created_at
    pass

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

print("\n유효성 검사 실패:")
# TODO: name="A", email="invalid", age=-1 로 만들기를 시도하고 에러마다 loc / msg 출력

# === 2. field_validator / model_validator ===
print("\n=== Validator ===")

class Product(BaseModel):
    name: str
    # TODO: price (0 초과), discount_price (기본 None)
    sku: str

    # TODO: sku 필드 검증기 — PRD- 검사 후 대문자로

    # TODO: name 필드 검증기 — strip 후 title

    # TODO: 모델 검증기 (after) — 할인가 >= 정가면 에러

product = Product(name="  python book  ", price=30000, discount_price=25000, sku="prd-001")
print(f"Product: {product.name}, {product.price}, SKU: {product.sku}")

# TODO: price=100, discount_price=200, sku="PRD-002" 로 시도하고 첫 msg 출력
#       print(f"가격 검증 실패: ...")

# === 3. 직렬화 / 역직렬화 ===
print("\n=== 직렬화 ===")

user_dict = None      # TODO: dict 로
print(f"model_dump: {list(user_dict.keys())}")

partial = None        # TODO: name, email, role 만
print(f"include: {partial}")

no_none = None        # TODO: None 제외
print(f"exclude_none 키: {list(no_none.keys())}")

user_json = None      # TODO: JSON 문자열 (indent=2)
print(f"JSON: {user_json[:80]}...")

user_from_json = None # TODO: JSON -> User
print(f"From JSON: {user_from_json.name}")

user_from_dict = None # TODO: {"name": "이영희", "email": "lee@example.com", "age": 25} -> User
print(f"From dict: {user_from_dict.name}")

# === 4. JSON Schema ===
print("\n=== JSON Schema ===")
schema = None         # TODO: User 의 JSON Schema
print(json.dumps(schema, indent=2, ensure_ascii=False)[:300] + "...")

# === 5. 고급 패턴 ===
print("\n=== 고급 패턴 ===")

# TODO: PositiveInt, Percentage 를 Annotated 로

class Stats(BaseModel):
    # TODO: count, success_rate
    pass

stats = Stats(count=100, success_rate=95.5)
print(f"Stats: count={stats.count}, rate={stats.success_rate}%")

class ImmutableConfig(BaseModel):
    # TODO: frozen 설정
    host: str = "localhost"
    port: int = 8080

config = ImmutableConfig()
# TODO: config.host = "other" 를 시도하고 첫 msg 를 "Frozen: ..." 으로 출력

print("\n=== Pydantic v2 핵심 정리 ===")
print("model_dump() / model_dump_json():  직렬화")
print("model_validate() / model_validate_json():  역직렬화")
print("model_json_schema():  JSON Schema 생성")
print("field_validator:  필드 단위 검증/변환")
print("model_validator:  모델 전체 교차 검증")
print("ConfigDict:  모델 설정 (frozen, strip 등)")
```

**확인 방법** — `python data-validation.py` 로 돌려 단계별 머리줄(`=== 기본 모델 ===` 등)이 차례로 찍히는지 보고, 어느 줄에서 예외가 잡히지 않고 멈추는지도 확인한다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
