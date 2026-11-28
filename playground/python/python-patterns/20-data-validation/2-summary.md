# python/python-patterns/20 — 데이터 검증 (Pydantic v2) — 정리 (힌트)

> 출처 — study-site 항목 `python/data-validation`(항목 데이터 `data/python/patterns.json`) · 정답 코드 study-practice `python/python-patterns/reference/data-validation.py`\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).\
> 실행 — 실행하지 않음 — 외부 라이브러리 `pydantic` 가 있어야 도는 예제다 — 그것 없이 만들어 실행하지 않았다.

## 한눈에 — 쉽게 말하면

**Pydantic 모델은 「서식이 정해진 접수 창구」다.**
창구 직원은 서류(입력 데이터)를 받으면 칸마다 정해진 규칙(타입 · 길이 · 범위 · 형식)에 맞는지 본다.
틀린 칸이 있으면 하나만 지적하지 않고 틀린 칸을 모두 적은 반려 쪽지를 한 번에 돌려준다.
통과한 서류는 정리된 꼴(공백 제거 · 대문자화 같은 손질을 마친 꼴)로 보관함에 들어간다.
보관된 서류는 다시 사본(dict · JSON)으로 뽑을 수 있고, 창구는 「서식 안내서」(JSON Schema)도 내줄 수 있다.
Pydantic v2 의 `BaseModel` 도 똑같은 구조다.

| 비유 | 실체 |
|---|---|
| 서식의 칸 | 모델의 필드(`name: str` 처럼 타입 힌트가 붙은 클래스 속성) |
| 칸마다 적힌 규칙 | `Field(min_length=2, ge=0, pattern=...)` |
| 직원의 추가 확인 · 손질 | `@field_validator` |
| 서류 전체를 놓고 하는 대조 | `@model_validator(mode='after')` |
| 창구 운영 규정 | `model_config = ConfigDict(...)` |
| 반려 쪽지 | `ValidationError` 와 `e.errors()` |
| 사본 뽑기 | `model_dump()` · `model_dump_json()` |
| 사본으로 다시 접수 | `model_validate()` · `model_validate_json()` |
| 서식 안내서 | `model_json_schema()` |

```text
  입력(dict · 키워드 인자 · JSON 문자열)
          │
          ▼
  ┌─────────────────────────┐
  │ 필드마다 타입 변환·검증  │  ← Field 제약, ConfigDict
  │ field_validator          │
  │ model_validator(after)   │
  └─────────────────────────┘
      │ 통과            │ 실패
      ▼                 ▼
  모델 인스턴스     ValidationError (에러 목록)
      │
      ▼
  model_dump / model_dump_json  →  dict / JSON
```

> **모델** — `BaseModel` 을 상속해 필드를 타입 힌트로 선언한 클래스다.\
> 예: `class User(BaseModel): age: int` 는 「age 칸은 정수」라는 서식이다.

## 이 주제가 답하려는 질문

1. 들어온 데이터가 규칙에 맞는지 어디에, 어떻게 적어 두나(선언 대 코드)?
2. 한 필드만 보는 검사와 여러 필드를 맞대는 검사는 어디서 어떻게 나누나?
3. 검증된 객체를 dict · JSON 으로 바꾸고, 반대로 되읽는 길은 무엇인가?
4. 같은 규칙을 여러 모델에서 다시 쓰고, 문서(JSON Schema)로 내보내려면 어떻게 하나?

## 동작 방식

### (1) 모델을 만들면 생성자가 곧 검증이다

**언제 쓰나** — 바깥에서 들어온 데이터(요청 본문 · 설정 · 파일)를 믿고 쓰기 전에 한 번 거를 때 쓴다.

```text
User(name="김철수", age=30, address={"street": ..., "city": ..., "zipcode": "06000"})
   │
   ├─ name  : str 인가? 길이 2~50 인가?         → 통과
   ├─ age   : int 인가? 0 이상 150 이하인가?     → 통과
   ├─ address: dict → Address 모델로 검증·변환  → Address 인스턴스
   └─ 넘기지 않은 칸(id, role, tags, created_at) → 기본값으로 채움
   ▼
user  (모든 필드가 규칙을 통과한 객체)
```

- 생성자에 값을 넘기는 순간 필드마다 검증이 돈다.
- 중첩 모델 칸(`address: Optional[Address]`)에 dict 를 넣으면 그 dict 가 `Address` 로 검증 · 변환된다.
- 넘기지 않은 필드는 선언한 기본값으로 채워진다.
- 규칙을 어긴 칸이 있으면 인스턴스는 만들어지지 않고 `ValidationError` 가 난다.
- `ValidationError` 는 틀린 칸을 **모두** 모아 한 번에 알려 준다 — `e.errors()` 가 에러마다 `loc`(어느 칸) · `msg`(무엇이 틀렸나)를 담은 목록을 돌려준다.

> **ValidationError** — 검증이 실패했을 때 Pydantic 이 던지는 예외다. 실패한 칸 전부를 담는다.\
> 예: `User(name="A", email="invalid", age=-1)` 은 세 칸이 동시에 틀린다.

### (2) `Field` — 규칙을 선언으로 적는다

**언제 쓰나** — 타입만으로는 모자라고 길이 · 범위 · 형식까지 제한하고 싶을 때 쓴다.

```text
name: str = Field(..., min_length=2, max_length=50)
           │     │
           │     └─ 길이 규칙
           └─ ... (Ellipsis) = 기본값 없음 → 필수 필드

age: int = Field(..., ge=0, le=150)        0 ≤ age ≤ 150
price: float = Field(gt=0)                 price > 0
zipcode: str = Field(pattern=r'^\d{5}$')   숫자 정확히 5자리
tags: list[str] = Field(default_factory=list, max_length=10)
                          │                       └─ 리스트 원소 수 ≤ 10
                          └─ 만들 때마다 새 빈 리스트
created_at: datetime = Field(default_factory=datetime.now)
                          └─ 만드는 순간의 시각
```

- 첫 인자 `...` 은 「기본값이 없으니 반드시 넘겨라」는 뜻이다.
- `ge` · `le` 는 이상 · 이하, `gt` 는 초과다.
- `pattern` 은 정규식으로 문자열 형식을 거른다.
- `default_factory` 는 기본값을 **함수로** 준다 — 인스턴스를 만들 때마다 그 함수를 불러 새 값을 얻는다.
- 그래서 리스트 같은 가변 기본값은 `default_factory=list` 로 준다 — 인스턴스끼리 한 리스트를 나눠 쓰지 않게 한다.
- `created_at` 도 같은 원리로, 클래스를 정의한 시각이 아니라 인스턴스를 만든 시각이 들어간다.

> **default_factory** — 기본값 대신 「기본값을 만드는 함수」를 받는 `Field` 인자다.\
> 예: `Field(default_factory=list)` 는 인스턴스마다 새 `[]` 를 준다.

### (3) `@field_validator` — 한 필드를 검사하고 손질한다

**언제 쓰나** — `Field` 제약으로 못 적는 규칙(「`PRD-` 로 시작」)이나 값 변환(공백 제거 · 대소문자)이 필요할 때 쓴다.

```text
입력 sku="PRD-002"
   │  ① str 타입 검증
   ▼
validate_sku(cls, v="PRD-002")
   │  ② v.startswith('PRD-') ?  아니면 raise ValueError
   │  ③ return v.upper()
   ▼
product.sku = 돌려준 값
```

- `@field_validator('필드이름')` 아래에 `@classmethod` 를 붙인 메서드를 둔다.
- 메서드는 그 필드의 값 `v` 를 받는다.
- 규칙을 어기면 `ValueError` 를 던진다 — Pydantic 이 그것을 `ValidationError` 로 바꿔 알린다.
- 메서드가 **돌려준 값**이 그 필드의 최종 값이 된다 — 검사뿐 아니라 변환도 된다(`v.strip().title()`).
- 메서드 안의 문장은 위에서 아래로 차례대로 돈다 — 검사를 변환보다 먼저 쓰면 검사는 변환 전 값을 본다.

> **validator(검증기)** — 선언으로 못 적는 검증 · 변환을 코드로 덧붙이는 메서드다.\
> 예: `validate_name` 은 `"  python book  "` 을 `"Python Book"` 으로 바꾼다.

### (4) `@model_validator(mode='after')` — 여러 필드를 맞대 본다

**언제 쓰나** — 「할인가는 정가보다 낮아야 한다」처럼 두 필드 이상의 관계를 검사할 때 쓴다.

```text
모든 필드 검증 끝(name, price, discount_price, sku)
   ▼
validate_prices(self)
   │  self.discount_price 가 참이고 self.discount_price >= self.price 이면
   │      raise ValueError('할인가는 정가보다 낮아야 합니다')
   │  return self
   ▼
인스턴스 확정
```

- `mode='after'` 는 필드 검증이 다 끝난 뒤에 부른다는 뜻이다.
- 그래서 메서드는 `cls` 와 값 하나가 아니라 완성된 `self` 를 받는다 — 모든 필드를 한꺼번에 볼 수 있다.
- 검사를 마치면 `self` 를 돌려준다.
- 필드 검증기는 자기 필드 하나만 보므로 이런 교차 검사에 맞지 않는다.
- 이 예의 조건 `if self.discount_price and ...` 는 `discount_price` 가 거짓 취급되는 값(`None` · `0.0`)이면 비교를 아예 건너뛴다.

> **교차 검증** — 서로 다른 필드 값의 관계를 따지는 검증이다.\
> 예: `discount_price < price`.

### (5) `ConfigDict` — 모델 전체의 동작을 정한다

**언제 쓰나** — 필드 하나가 아니라 모델 전체에 같은 규칙을 걸거나, 모델의 성질(불변)을 바꿀 때 쓴다.

```text
model_config = ConfigDict(
    str_strip_whitespace=True,   이 모델의 문자열 앞뒤 공백 제거
    str_min_length=1,            이 모델의 문자열은 빈 문자열 금지
)

model_config = ConfigDict(frozen=True)
    config = ImmutableConfig()        만들기 → 됨
    config.host = "other"             대입   → ValidationError
```

- 클래스 속성 `model_config` 에 `ConfigDict(...)` 를 넣는 것이 v2 의 설정 문법이다.
- `str_strip_whitespace=True` 와 `str_min_length=1` 은 필드마다 적지 않아도 모델의 문자열 필드에 함께 걸린다.
- `frozen=True` 는 만들어진 인스턴스의 필드에 다시 대입하는 것을 막는다.
- 막히는 것은 **만든 뒤의 대입**이다 — 만들 때 값을 넘기는 것은 평소대로 된다.
- 막힌 대입은 이 예에서 `ValidationError` 로 잡힌다.

> **불변(frozen) 모델** — 만든 뒤에 필드를 바꿀 수 없는 모델이다.\
> 예: 설정 객체를 실수로 덮어쓰지 못하게 한다.

### (6) 직렬화와 역직렬화 — 객체 ↔ dict ↔ JSON

**언제 쓰나** — 검증된 객체를 API 응답 · 파일로 내보내거나, 받은 JSON · dict 를 다시 모델로 들일 때 쓴다.

```text
           model_dump()                 model_dump_json(indent=2)
 user ──────────────────▶ dict    user ─────────────────────────▶ JSON 문자열
   ▲                                ▲                                │
   │ User.model_validate(dict)      │ User.model_validate_json(str)  │
   └──────────────── dict           └────────────────────────────────┘
```

- `model_dump()` 는 모델을 dict 로 바꾼다 — v1 의 `.dict()` 자리다.
- `model_dump(include={'name', 'email', 'role'})` 는 고른 필드만 담는다.
- `model_dump(exclude_none=True)` 는 값이 `None` 인 필드를 뺀다 — API 응답을 가볍게 할 때 쓴다.
- `model_dump_json()` 은 곧장 JSON 문자열을 만든다 — `datetime` 같은 값도 알아서 문자열로 바꾼다.
- `Model.model_validate(dict)` 는 dict 를 검증해 모델로 만든다 — v1 의 `parse_obj` 자리다.
- `Model.model_validate_json(str)` 는 JSON 문자열을 검증해 모델로 만든다.
- 되읽을 때도 (1)의 검증이 그대로 돈다 — 그래서 JSON 안의 날짜 문자열이 `datetime` 칸에서 다시 `datetime` 이 된다.

> **직렬화** — 객체를 dict · JSON 같은 전달 가능한 꼴로 바꾸는 일이다. 반대가 역직렬화다.\
> 예: `user.model_dump_json()` 은 직렬화, `User.model_validate_json(...)` 은 역직렬화다.

### (7) JSON Schema — 모델이 곧 문서다

**언제 쓰나** — API 문서(OpenAPI · Swagger)나 다른 언어 쪽 클라이언트에 「이 데이터의 꼴」을 알려 줄 때 쓴다.

```text
User.model_json_schema()
   ▼
{ "title": "User", "type": "object",
  "properties": { "name": {..., "minLength": 2, ...}, "age": {...}, ... },
  "required": [...] , ... }      (꼴의 예 — 실제 키 구성은 확인 필요)
```

- `model_json_schema()` 는 필드 타입 · `Field` 제약 · 기본값을 JSON Schema 꼴의 dict 로 뽑는다.
- 검증 규칙을 한 곳(모델)에 적었으니 문서가 코드와 어긋나지 않는다.
- 예제는 `json.dumps(schema, indent=2, ensure_ascii=False)` 로 찍는다 — `ensure_ascii=False` 는 한글을 `\uXXXX` 로 바꾸지 않고 그대로 둔다.

> **JSON Schema** — JSON 데이터의 꼴(타입 · 필수 키 · 제약)을 JSON 으로 적는 표준 형식이다.\
> 예: `{"type": "integer", "minimum": 0}`.

### (8) `Annotated` — 규칙 붙은 타입을 이름 하나로

**언제 쓰나** — 같은 제약(「양의 정수」 · 「0~100 퍼센트」)을 여러 필드 · 여러 모델에서 되풀이할 때 쓴다.

```text
PositiveInt = Annotated[int, Field(gt=0)]
Percentage  = Annotated[float, Field(ge=0, le=100)]
               │         └─ 덧붙인 메타데이터(검증 규칙)
               └─ 바탕 타입
class Stats(BaseModel):
    count: PositiveInt          ← int + gt=0
    success_rate: Percentage    ← float + 0~100
```

- `Annotated[타입, 메타데이터]` 는 타입에 정보를 덧붙이는 표준 `typing` 문법(PEP 593)이다.
- Pydantic 은 거기 붙은 `Field(...)` 를 검증 규칙으로 읽는다.
- 이렇게 만든 별칭은 커스텀 타입처럼 어느 모델에서나 다시 쓸 수 있다.

## 문법 — 형태와 규칙

```python
from typing import Annotated, Optional
from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator

Score = Annotated[int, Field(ge=0, le=100)]

class Exam(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    title: str = Field(..., min_length=1)
    score: Score
    retake: Optional[Score] = None

    @field_validator('title')
    @classmethod
    def upper_title(cls, v: str) -> str:
        return v.upper()

    @model_validator(mode='after')
    def check_retake(self) -> 'Exam':
        if self.retake is not None and self.retake < self.score:
            raise ValueError('재시험 점수는 본시험보다 낮을 수 없다')
        return self
```

- 필드는 `이름: 타입` 또는 `이름: 타입 = 기본값 | Field(...)` 로 적는다.
- 기본값이 없거나 `Field(...)` 의 첫 인자가 `...` 이면 필수 필드다.
- 고를 수 있는 칸은 `Optional[타입] = None` 처럼 기본값 `None` 을 함께 준다.
- 문자열 고정 선택지는 `class Role(str, Enum)` 처럼 `str` 을 함께 상속한 `Enum` 으로 둔다 — 값이 문자열이라 JSON 으로 내보내기 쉽다.
- `field_validator` 는 `@field_validator('필드')` + `@classmethod` + `(cls, v)` 꼴, 돌려준 값이 최종 값이다.
- `model_validator(mode='after')` 는 `(self)` 를 받고 `self` 를 돌려준다.
- 모델 설정은 `model_config = ConfigDict(...)` 하나로 모은다.

| 도구 | 하는 일 | 원본 예 |
|---|---|---|
| `Field(min_length, max_length)` | 문자열 길이 · 리스트 원소 수 | `name`, `tags` |
| `Field(ge, le, gt)` | 수의 범위 | `age`, `price` |
| `Field(pattern=...)` | 정규식 형식 | `email`, `zipcode` |
| `Field(default_factory=...)` | 인스턴스마다 새 기본값 | `tags`, `created_at` |
| `ConfigDict(str_strip_whitespace, str_min_length)` | 모델 문자열 일괄 규칙 | `User` |
| `ConfigDict(frozen=True)` | 만든 뒤 대입 금지 | `ImmutableConfig` |
| `model_dump(include=..., exclude_none=...)` | dict 로 내보내기 | `user` |
| `model_dump_json(indent=...)` | JSON 문자열로 내보내기 | `user_json` |
| `model_validate` · `model_validate_json` | dict · JSON 들이기 | `user_from_dict` · `user_from_json` |
| `model_json_schema()` | JSON Schema 뽑기 | `schema` |

## 어디서 틀리나

### 1. 검사를 변환보다 먼저 쓰면 변환 전 값으로 검사한다
원본의 `validate_sku` 는 `v.startswith('PRD-')` 를 먼저 보고, 통과한 뒤에야 `v.upper()` 를 한다.
그런데 예제는 `sku="prd-001"` 로 `Product` 를 만든다.
소문자 `"prd-001"` 은 `'PRD-'` 로 시작하지 않으므로 대문자로 바뀌기 전에 `ValueError` 가 난다.
그 줄은 `try` 밖이라 `ValidationError` 가 잡히지 않고 스크립트가 거기서 멈춘다고 읽힌다.
의도가 「소문자도 받아 대문자로 맞춘다」였다면 `v = v.upper()` 를 검사보다 먼저 두어야 한다.

### 2. 가변 기본값을 그냥 쓰지 않는다
리스트 같은 가변 기본값은 `default_factory=list` 로 준다.
원본 주석도 「가변 기본값은 default_factory 사용」이라고 적는다.

### 3. `if self.discount_price and ...` 는 `0.0` 을 건너뛴다
`and` 의 왼쪽은 값이 「참으로 취급되나」를 본다.
`discount_price=0.0` 은 거짓 취급이라 비교 없이 통과한다.
「`None` 이 아닐 때만」을 뜻했다면 `is not None` 으로 적는 편이 뜻이 분명하다.

### 4. `ValidationError` 는 에러 하나가 아니다
`e.errors()[0]['msg']` 처럼 첫 에러만 찍으면 나머지 실패를 놓친다.
여러 칸을 함께 검사할 때는 원본의 첫 예처럼 `for error in e.errors()` 로 전부 본다.

### 5. `frozen` 은 만들기를 막지 않는다
`frozen=True` 는 만든 뒤의 대입만 막는다.
생성자에 값을 넘겨 다른 설정 객체를 만드는 것은 된다.

### 6. 쓰지 않는 import
원본은 `EmailStr` 과 `date` 를 import 하지만 쓰지 않는다.
`email` 칸은 `EmailStr` 대신 `pattern` 정규식으로 거른다.

### 7. 원본 팁 — 그대로 옮긴 것
- Pydantic v2 는 Rust 기반(`pydantic-core`)으로 v1 보다 5~50배 빠르다(원본의 주장 — 아래 표 참고).
- `Field` 로 검증 규칙을 선언하고, validator 로 커스텀 로직을 덧붙인다.
- `model_config = ConfigDict(...)` 로 모델 동작을 세밀하게 정한다.
- JSON Schema 자동 생성은 API 문서화에 쓸모 있다.

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| `Annotated[타입, 메타데이터]` 로 타입에 정보를 붙인다 | Python 표준 `typing`(PEP 593) |
| 그 메타데이터의 `Field(...)` 를 검증 규칙으로 읽는다 | Pydantic 라이브러리 |
| `default_factory` 함수를 인스턴스마다 부른다 | Pydantic 라이브러리 |
| `pydantic-core` 가 Rust 로 쓰였다 | Pydantic v2 의 구현 |
| v1 보다 5~50배 빠르다 | 원본의 주장 — 측정 조건 · 버전이 적혀 있지 않다 (확인 필요) |
| `e.errors()` 의 `msg` 문구 | Pydantic 버전마다 다를 수 있다 (확인 필요) |
| frozen 모델 대입이 `ValidationError` 로 난다 | Pydantic v2 의 동작(원본 코드가 이를 전제한다) |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 한 필드의 길이 · 범위 · 형식 | `Field(...)` 제약 | 같은 일을 하는 `field_validator` 코드 |
| 한 필드의 특수 규칙 · 변환 | `field_validator` | `model_validator` |
| 두 필드 이상의 관계 | `model_validator(mode='after')` | 필드마다 따로 쓴 `field_validator` |
| 모델 전체 문자열 규칙 · 불변 | `ConfigDict` | 필드마다 같은 제약 반복 |
| 같은 제약을 여러 곳에서 | `Annotated` 별칭 | 복사한 `Field(...)` |
| API 응답에서 빈 칸 빼기 | `model_dump(exclude_none=True)` | 손으로 dict 에서 지우기 |
| 받은 JSON 문자열 들이기 | `model_validate_json` | `json.loads` 뒤 손 검증 |

## 핵심 문장

1. **모델의 생성자가 곧 검증이다** — 통과하면 인스턴스, 실패하면 모든 실패를 담은 `ValidationError`.
2. **규칙은 선언(`Field` · `ConfigDict` · `Annotated`)이 먼저, 코드(`validator`)는 그다음이다.**
3. **`field_validator` 는 한 칸을, `model_validator(mode='after')` 는 완성된 모델 전체를 본다** — validator 가 돌려준 값이 최종 값이다.
4. **`model_dump` · `model_dump_json` 으로 내보내고, `model_validate` · `model_validate_json` 으로 들인다** — 들일 때도 검증이 돈다.
5. **모델에서 JSON Schema 가 나오므로 검증 규칙과 문서가 한 곳에 있다.**

## 관련 자료

- [fastapi-basics](../../python-libraries/03-fastapi-basics/2-summary.md)
- [config-management](../11-config-management/2-summary.md)
- `error-handling` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- 원본: study-site 항목 데이터 `data/python/patterns.json` 의 `data-validation`

## 용어 풀이

- **Pydantic** — 타입 힌트로 데이터 검증 · 직렬화를 하는 Python 라이브러리다.
- **BaseModel** — Pydantic 모델이 상속하는 바탕 클래스다.
- **필드** — 모델에 타입 힌트로 선언한 속성 하나다.
- **Field** — 필드의 기본값 · 제약을 적는 함수다.
- **Ellipsis (`...`)** — `Field` 첫 인자로 쓰면 「기본값 없음 = 필수」다.
- **default_factory** — 인스턴스마다 기본값을 새로 만드는 함수다.
- **field_validator** — 한 필드를 검사 · 변환하는 메서드를 등록하는 데코레이터다.
- **model_validator** — 모델 전체를 검사하는 메서드를 등록하는 데코레이터다.
- **mode='after'** — 필드 검증이 다 끝난 뒤에 부르라는 뜻이다.
- **ConfigDict** — 모델 설정을 담는 dict 꼴 객체다.
- **frozen** — 만든 뒤 대입을 막는 설정이다.
- **ValidationError** — 검증 실패 예외. `.errors()` 로 실패 목록을 준다.
- **loc · msg** — 에러 항목의 위치(어느 필드)와 설명이다.
- **직렬화 · 역직렬화** — 객체 → dict/JSON, dict/JSON → 객체.
- **JSON Schema** — JSON 데이터의 꼴을 적는 표준 형식이다.
- **Annotated** — 타입에 메타데이터를 붙이는 `typing` 문법이다.
- **str Enum** — `str` 과 `Enum` 을 함께 상속해 값이 문자열인 열거형이다.

## 더 들어가면

- Pydantic v2 에서 `Optional[int]` 는 「`None` 도 허용」일 뿐 기본값을 주지 않는다 — 기본값 `= None` 을 따로 적지 않으면 필수 필드가 된다 (확인 필요).
- `field_validator` 의 기본 모드는 `'after'` 로, 타입 검증을 마친 값을 받는다. `mode='before'` 로 타입 변환 전의 날것을 받을 수도 있다 (확인 필요).
- validator 안에서 던진 `ValueError` 는 `msg` 앞에 `"Value error, "` 같은 머리말이 붙어 나온다고 알려져 있다 (확인 필요).
- `ConfigDict` 의 설정은 중첩 모델(`Address`)로 넘어가지 않고, 중첩 모델은 자기 설정을 따른다 (확인 필요).
- `EmailStr` 를 실제 필드에 쓰려면 `email-validator` 패키지가 따로 필요하다 (확인 필요).
- 숫자 칸은 기본(lax) 모드에서 `30000` 같은 정수를 `float` 칸에 받아 `30000.0` 으로 바꾼다. `strict=True` 설정으로 이런 변환을 막을 수 있다 (확인 필요).
- frozen 모델에서 바뀐 값이 필요하면 `model_copy(update={...})` 로 새 인스턴스를 만든다 (확인 필요).
- `model_dump(mode='json')` 은 `Enum` · `datetime` 을 JSON 친화 값으로 바꾼 dict 를 준다 (확인 필요).
