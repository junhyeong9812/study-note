# python/python-oop/19 — Pydantic 기초 — 정리 (힌트)

> 출처 — study-site 항목 `python/pydantic-basics`(항목 데이터 `data/python/oop.json`) · 정답 코드 study-practice `python/python-oop/reference/pydantic-basics.py`\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).\
> 실행 — 실행하지 않음 — 외부 라이브러리 `pydantic` 가 있어야 도는 예제다 — 그것 없이 만들어 실행하지 않았다.

## 한눈에 — 쉽게 말하면

**Pydantic 모델은 「서류 접수 창구」다.**
창구에는 양식(어떤 칸에 어떤 종류의 값을 적나)이 붙어 있다.
누가 서류를 내밀면 직원이 칸마다 확인한다.
「나이」 칸에 글자로 "25" 라고 적혀 있으면 숫자 25 로 고쳐 적어 준다.
「나이」 칸에 "모름" 이라고 적혀 있으면 서류를 돌려보내면서 어느 칸이 왜 틀렸는지 쪽지를 붙인다.
통과한 서류만 서랍(객체)에 들어가고, 필요하면 복사본(dict · JSON)을 뽑아 준다.
Pydantic 의 `BaseModel` 도 똑같은 구조다.

| 비유 | 실체 |
|---|---|
| 창구에 붙은 양식 | `BaseModel` 을 상속한 클래스의 타입 힌트(`age: int`) |
| 칸마다 붙은 세부 조건(「1자 이상」) | `Field(min_length=1)` 같은 제약 |
| 직원이 칸 하나를 보고 고쳐 적기 | `@field_validator` |
| 서류 전체를 보고 앞뒤가 맞는지 확인 | `@model_validator(mode='after')` |
| 돌려보낼 때 붙이는 쪽지 | `ValidationError` |
| 통과한 서류가 든 서랍 | 모델 인스턴스 |
| 복사본 뽑기 | `model_dump()` · `model_dump_json()` |
| 봉인된 서류(고칠 수 없음) | `ConfigDict(frozen=True)` |

```text
  입력 (dict · 키워드 인자 · JSON 문자열)
        │
        ▼
  ┌──────────────────────────────┐
  │ 1) 필드마다 타입 확인 · 변환   │
  │ 2) Field 제약 확인            │
  │ 3) field_validator 실행       │
  │ 4) model_validator 실행       │
  └──────────────────────────────┘
        │통과                 │실패
        ▼                     ▼
   모델 인스턴스          ValidationError
        │
        ▼
  model_dump() → dict
  model_dump_json() → JSON 문자열
```

## 이 주제가 답하려는 질문

1. 타입 힌트만 적어 둔 클래스가 어떻게 들어오는 값을 검사하고 바꿔 주나?
2. 「0보다 커야 한다」 · 「소문자로 맞춘다」 · 「시작이 끝보다 앞서야 한다」 같은 규칙은 어디에 적나?
3. 검사를 통과한 객체를 어떻게 dict · JSON 으로 내보내고, 거꾸로 JSON 에서 객체를 만드나?
4. 객체를 고칠 수 없게 하거나, 값이 없어도 되는 칸은 어떻게 표시하나?

## 동작 방식

### (1) `BaseModel` 상속 — 타입 힌트가 곧 검사 규칙이다

**언제 쓰나** — 바깥에서 들어온 데이터(요청 본문, 설정 파일, 파이프라인 한 줄)를 믿을 수 있는 객체로 바꿀 때 쓴다.

```text
class User(BaseModel):
    name: str
    age: int
    email: str
    is_active: bool = True

User(name="Bob", age="25", email="bob@test.com")
        │
        ▼
name  "Bob"   → str 이 맞다 → 그대로
age   "25"    → int 가 필요하다 → 숫자로 읽을 수 있다 → 25 로 바꾼다
email "bob@…" → str 이 맞다 → 그대로
is_active 없음 → 기본값 True 를 쓴다
        │
        ▼
user2.age == 25, type(user2.age) 은 int
```

- 클래스 몸체의 `이름: 타입` 한 줄이 필드 하나다.
- `= 값` 이 붙은 필드는 넣지 않아도 되고, 안 붙은 필드는 반드시 넣어야 한다.
- 들어온 값이 타입과 다르더라도 그 타입으로 바꿀 수 있으면 Pydantic 이 바꿔 준다(문자열 `"25"` → 정수 `25`).
- 이 변환은 Pydantic 이 하는 일이다 — 파이썬의 타입 힌트는 원래 실행 중에 아무것도 검사하지 않는다.

> **타입 힌트** — `age: int` 처럼 변수 · 필드에 기대하는 타입을 적은 표시.\
> 예: 보통 클래스에서는 `age: int` 라고 적어도 문자열을 넣을 수 있다.

> **자동 타입 변환** — 들어온 값을 필드의 타입으로 바꿀 수 있으면 바꿔서 받아들이는 동작.\
> 예: `age="25"` → `25`.

### (2) 검증 실패 — 틀린 칸을 모아 `ValidationError` 하나로 던진다

**언제 쓰나** — 잘못된 입력을 생성 시점에 막아, 뒤쪽 코드가 이상한 값을 만나지 않게 할 때다.

```text
User(name="Charlie", age="not_a_number", email="test")
        │
        ▼
name  "Charlie"        → str → 통과
age   "not_a_number"   → int 로 바꿀 수 없다 → 오류 1건 기록
email "test"           → 타입이 str 일 뿐이다 → 통과 (형식 검사는 없다)
        │
        ▼
ValidationError (오류 1건: age)  → 객체는 만들어지지 않는다
```

- Pydantic 은 첫 오류에서 멈추지 않고 필드를 끝까지 돌며 오류를 모은다.
- 모인 오류는 `ValidationError` 예외 하나로 던져진다.
- 예외를 `print` 하면 어느 필드가 왜 틀렸는지 적힌 설명이 나온다.
- `email: str` 은 「문자열이면 된다」는 뜻일 뿐이다 — `"test"` 처럼 `@` 가 없어도 통과한다.

> **ValidationError** — Pydantic 이 검증에 실패했을 때 던지는 예외. 틀린 필드들의 목록을 담는다.\
> 예: `age` 에 숫자가 아닌 문자열을 넣으면 생긴다.

### (3) `Field` — 타입 위에 제약을 얹는다

**언제 쓰나** — 「문자열이기만 하면」이 아니라 「1자 이상 100자 이하」 「0보다 큼」처럼 값의 범위까지 정해야 할 때다.

```text
class Product(BaseModel):
    name: str        = Field(min_length=1, max_length=100)
    price: float     = Field(gt=0, description="가격 (양수)")
    quantity: int    = Field(ge=0, default=0)
    tags: list[str]  = Field(default_factory=list)

Product(name="", price=-10)
        │
        ▼
name   ""   → 길이 0 < 1 → 오류
price  -10  → -10 > 0 이 아니다 → 오류
quantity 없음 → default 0 (ge=0 은 만족)
tags   없음 → list() 를 새로 불러 빈 리스트
        │
        ▼
ValidationError (오류 2건)
```

- `min_length` · `max_length` 는 문자열 길이를 제한한다.
- `gt` 는 「보다 크다(>)」, `ge` 는 「크거나 같다(>=)」다.
- `description` 은 검증에 쓰이지 않는 문서화용 설명이다.
- `default` 는 값이 없을 때 쓸 기본값이다.
- `default_factory` 는 기본값을 만들 함수다 — 객체를 만들 때마다 그 함수를 불러 새 값을 얻는다.

> **default_factory** — 기본값 자체 대신, 기본값을 만들어 줄 함수를 적는 자리.\
> 예: `Field(default_factory=list)` 는 객체마다 새 빈 리스트를 받는다.

### (4) `@field_validator` — 필드 하나를 직접 검사하고 고쳐 적는다

**언제 쓰나** — `Field` 의 제약으로는 표현이 안 되는 규칙(「영문 · 숫자만」)이 있거나, 값을 정규화(소문자로 맞추기)하고 싶을 때다.

```text
@field_validator('username')
@classmethod
def username_alphanumeric(cls, v):
    if not v.isalnum(): raise ValueError('영문/숫자만 허용')
    return v.lower()

Account(username="Alice123", ...)
        │
        ▼
v = "Alice123" → isalnum() 참 → 통과 → "alice123" 을 돌려준다
        │
        ▼
account.username == "alice123"   (돌려준 값이 필드에 들어간다)
```

- `@field_validator('필드이름')` 아래에 `@classmethod` 를 겹쳐 단다 — 메서드는 `cls` 와 값 `v` 를 받는다.
- 메서드가 **돌려준 값**이 필드에 저장된다 — 그래서 검사와 정규화를 한 번에 할 수 있다.
- 규칙을 어기면 `ValueError` 를 던진다 — Pydantic 이 그것을 받아 `ValidationError` 의 오류 한 건으로 바꾼다.
- 원본 예제의 `Account` 는 세 개를 둔다: `username`(영문 · 숫자만, 소문자로), `password`(8자 이상), `email`(`@` 필수, 소문자로).

> **정규화** — 같은 뜻의 값을 한 가지 꼴로 맞추는 일.\
> 예: `"Alice@Test.COM"` → `"alice@test.com"`.

### (5) `@model_validator(mode='after')` — 필드끼리의 관계를 검사한다

**언제 쓰나** — 규칙이 필드 둘 이상에 걸쳐 있을 때다(「시작일이 종료일보다 앞」).

```text
class DateRange(BaseModel):
    start: datetime
    end: datetime
    @model_validator(mode='after')
    def check_dates(self):
        if self.start >= self.end: raise ValueError(...)
        return self

DateRange(start=datetime(2024,1,1), end=datetime(2024,12,31))
        │
        ▼
1) start · end 각각 datetime 으로 검증 (필드 단계)
2) 다 끝난 뒤 check_dates(self) 호출 — self 에 두 값이 다 있다
3) 1월 1일 >= 12월 31일 ? 아니다 → return self
        │
        ▼
dr 생성 성공
```

- `field_validator` 는 필드 하나만 보므로 「start 와 end 를 비교」할 수 없다.
- `mode='after'` 는 모든 필드 검증이 끝난 뒤에 돈다는 뜻이다 — 그래서 `self` 로 완성된 인스턴스를 받는다.
- 끝에서 `self` 를 돌려줘야 한다.

### (6) 중첩 모델과 JSON 에서 만들기

**언제 쓰나** — 데이터가 층층이 들어 있을 때(직원 안에 주소), 그리고 JSON 문자열을 바로 객체로 바꿀 때다.

```text
class Address(BaseModel): city: str; country: str = "Korea"
class Employee(BaseModel): ...; address: Address; skills: list[str] = []

Employee(..., address={"city": "Seoul"})
        │
        ▼
address 칸의 타입이 Address → dict 를 Address 로 검증 · 생성
  city "Seoul", country 없음 → "Korea"
        │
        ▼
emp.address.city == "Seoul"

Employee.model_validate_json('{"name": "Bob", "age": 25, "address": {"city": "Busan"}}')
        │
        ▼
JSON 해석 → 같은 검증 과정 → Employee 인스턴스 (skills 는 기본값 [])
```

- 필드의 타입으로 다른 `BaseModel` 을 쓰면 그 안쪽도 같은 방식으로 검증된다.
- 안쪽 모델 자리에 dict 를 넘기면 Pydantic 이 안쪽 모델로 바꿔 준다.
- `model_validate_json(문자열)` 은 JSON 문자열을 읽어 곧바로 모델로 검증한다.

### (7) 직렬화 — `model_dump` · `model_dump_json` · `exclude_none`

**언제 쓰나** — 검증된 객체를 저장하거나 응답으로 보낼 때다.

```text
user = User(name="Alice", age=30, email="alice@test.com")
        │
        ├─ user.model_dump()       → 파이썬 dict
        └─ user.model_dump_json()  → JSON 문자열

p = Profile(name="Alice")          # bio · age 는 None
p.model_dump(exclude_none=True)    → None 인 칸을 뺀 dict
```

- `model_dump()` 는 v2 의 이름이다 — v1 의 `.dict()` 를 대신한다.
- `model_dump_json()` 은 JSON 문자열을 돌려준다.
- `exclude_none=True` 를 주면 값이 `None` 인 필드는 결과에서 빠진다.

> **직렬화** — 객체를 dict · JSON 처럼 저장 · 전송할 수 있는 꼴로 바꾸는 일.\
> 예: `user.model_dump_json()`.

### (8) 모델 설정 — `frozen` 과 `Optional`

**언제 쓰나** — 설정값처럼 만든 뒤 바뀌면 안 되는 객체, 그리고 비어 있어도 되는 칸을 표시할 때다.

```text
class FrozenConfig(BaseModel):
    model_config = ConfigDict(frozen=True)
    host: str; port: int

cfg = FrozenConfig(host="localhost", port=8080)   → 생성은 된다
cfg.host = "remote"                               → 예외 (고칠 수 없다)

class Profile(BaseModel):
    name: str
    bio: Optional[str] = None

Profile(name="Alice")   → bio 는 None
```

- v2 에서는 클래스 안에 `model_config = ConfigDict(...)` 로 모델 설정을 적는다.
- `frozen=True` 면 생성 때 값을 넣는 것은 되고, 생성 뒤 속성에 대입하면 예외가 난다.
- `Optional[str]` 은 「str 또는 None」이고, `= None` 은 「안 넣으면 None」이다 — 원본은 둘을 함께 쓴다.

> **불변(frozen) 모델** — 만든 뒤 필드 값을 바꿀 수 없는 모델.\
> 예: 서버 주소 설정 객체.

## 문법 — 형태와 규칙

```python
from typing import Optional
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict

class Order(BaseModel):
    model_config = ConfigDict(frozen=True)          # 모델 설정
    item: str = Field(min_length=1)                 # 제약 붙은 필수 필드
    count: int = Field(ge=1, default=1)             # 제약 + 기본값
    notes: list[str] = Field(default_factory=list)  # 가변 기본값
    memo: Optional[str] = None                      # 없어도 되는 칸

    @field_validator('item')
    @classmethod
    def strip_item(cls, v):
        return v.strip()                            # 돌려준 값이 저장된다

    @model_validator(mode='after')
    def check(self):
        return self                                 # 끝에서 self 를 돌려준다
```

- 모델: `class 이름(BaseModel):` 몸체에 `필드: 타입 [= 기본값]`.
- 기본값이 없는 필드는 필수다.
- `Field(...)` 인자 — `min_length` · `max_length`(길이), `gt` · `ge`(크기 하한), `default`, `default_factory`, `description`.
- 필드 검증기 — `@field_validator('필드')` 위, `@classmethod` 아래, `(cls, v)` 를 받고 값을 돌려준다. 어기면 `ValueError`.
- 모델 검증기 — `@model_validator(mode='after')`, `(self)` 를 받고 `self` 를 돌려준다.
- 생성 — `모델(키=값, ...)` 또는 `모델.model_validate_json(JSON문자열)`.
- 내보내기 — `.model_dump()`, `.model_dump(exclude_none=True)`, `.model_dump_json()`.
- 설정 — `model_config = ConfigDict(frozen=True)`.
- 설치 — `pip install pydantic` (표준 라이브러리가 아니다).

## 어디서 틀리나

### 1. 타입 힌트가 형식까지 검사한다고 믿기
`email: str` 은 문자열인지만 본다.
`"test"` 도 통과한다.
형식이 필요하면 `field_validator` 로 직접 검사한다(원본의 `Account.email_valid` 처럼).
원본은 `EmailStr` 을 import 하지만 어느 모델에서도 쓰지 않는다.

### 2. 「변환해 준다」를 「무엇이든 받아 준다」로 읽기
`"25"` 는 `int` 로 바뀌지만 `"not_a_number"` 는 바뀌지 않고 오류가 된다.
변환은 그 타입으로 읽을 수 있을 때만 일어난다.

### 3. 검증기에서 `ValidationError` 를 직접 던지려 하기
검증기 안에서는 `ValueError` 를 던진다.
바깥에서 받는 것은 그것을 감싼 `ValidationError` 다.

### 4. 검증기에서 값을 돌려주지 않기
`field_validator` 가 돌려준 값이 필드에 들어간다.
`return v` 를 빠뜨리면 원래 값이 아닌 `None` 이 들어가거나 검증이 실패한다(원본에 근거 없음 — 추론).
`model_validator(mode='after')` 도 `self` 를 돌려줘야 한다.

### 5. 필드 둘을 비교하는 규칙을 `field_validator` 에 넣기
`field_validator` 는 값 하나만 받는다.
`start` 와 `end` 를 비교하는 일은 모든 필드가 끝난 뒤 도는 `model_validator(mode='after')` 의 몫이다.

### 6. 가변 기본값
파이썬 함수에서 `def f(x=[])` 처럼 리스트를 기본값으로 두면 그 리스트 하나를 모든 호출이 나눠 쓴다.
원본 주석은 이 문제를 피하려고 `Field(default_factory=list)` 를 쓴다고 설명한다 — 객체마다 `list()` 를 새로 부르기 때문이다.
그런데 같은 원본의 `Employee` 는 `skills: list[str] = []` 를 그대로 쓴다.
원본의 주장 → 「가변 기본값은 `default_factory` 로 안전하게 처리한다」.
의심스러운 점 → Pydantic 은 `= []` 기본값을 객체마다 복사해 준다는 설명이 있어, 이 경우 `= []` 도 공유 문제가 없을 수 있다(확인 필요).
어느 쪽이든 `default_factory` 는 뜻이 분명한 쓰기다.

### 7. frozen 모델을 고쳐 쓰려 하기
`frozen=True` 모델에 `cfg.host = "remote"` 를 하면 예외가 난다.
값을 바꾸고 싶으면 새 객체를 만든다.

### 8. v1 이름 쓰기
v2 에서는 `.dict()` 대신 `.model_dump()` 다.
설정도 `model_config = ConfigDict(...)` 로 적는다(원본 주석이 「v2 방식」이라고 밝힌다).

### 9. 「Rust 기반이라 매우 빠르다」 (원본 팁)
원본 팁은 Pydantic v2 가 Rust 기반이라 매우 빠르다고 한다.
원본은 얼마나 빠른지 수치를 주지 않는다 — 속도를 근거로 설계를 정할 때는 직접 재야 한다(확인 필요).
빠르다는 것은 검증 비용이 작다는 뜻이지, 검증을 줄여도 된다는 뜻이 아니다.

### 10. 쓸 자리 (원본 팁)
원본 팁은 API 입력 검증 · 설정 관리 · 데이터 파이프라인에 알맞다고 한다.
FastAPI 와 함께 쓰면 강력하다고도 한다 — 요청 본문을 Pydantic 모델로 받는 방식이다(원본에 근거 없음 — 추론).
반대로 프로그램 안에서만 오가고 이미 믿을 수 있는 값이라면 검증이 짐이 될 수 있다.

### 11. 설치되지 않은 환경
Pydantic 은 따로 설치해야 한다.
원본은 `try`/`except ImportError` 로 import 를 감싸 `PYDANTIC_AVAILABLE` 깃발을 세우고, 없으면 개념 설명만 출력한다.

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| 타입 힌트대로 값을 검사 · 변환한다 | Pydantic 라이브러리 — 파이썬 언어는 타입 힌트를 실행 중에 강제하지 않는다 |
| `"25"` → `25` 자동 변환 | Pydantic 의 기본 변환 규칙 (설정에 따라 달라질 수 있다 — 확인 필요) |
| v2 는 Rust 기반이다 | Pydantic v2 의 구현 (원본 팁) |
| 「매우 빠르다」 | 원본의 주장 — 수치 근거 없음 (확인 필요) |
| `.model_dump()` 가 `.dict()` 를 대신한다 | Pydantic v2 의 API (v1 과 다르다) |
| frozen 모델에 대입하면 예외 | Pydantic 의 동작 — 예외의 정확한 종류는 버전에 따라 확인 필요 |
| 함수 기본 인자의 가변 객체를 호출끼리 나눠 쓴다 | 파이썬 언어 |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| API 요청 본문 받기 | `BaseModel` + `Field` 제약 | 손으로 쓴 `if` 검사 줄줄이 |
| 값을 한 꼴로 맞추기(소문자 등) | `field_validator` 에서 고친 값 돌려주기 | 생성 뒤에 따로 고치기 |
| 필드 사이 관계(시작 < 끝) | `model_validator(mode='after')` | `field_validator` |
| 기본값이 리스트 · dict | `Field(default_factory=list)` | 함수 기본 인자처럼 하나를 나눠 쓰는 설계 |
| 바뀌면 안 되는 설정 | `ConfigDict(frozen=True)` | 보통 모델 + 「고치지 말 것」 주석 |
| 비어 있어도 되는 칸 | `Optional[타입] = None` | 빈 문자열로 「없음」 흉내 |
| JSON 문자열 받기 | `model_validate_json` | `json.loads` 뒤 손으로 검사 |
| 이미 믿을 수 있는 내부 값 | 보통 클래스 · `dataclass` (원본에 근거 없음 — 추론) | 불필요한 검증 층 |

## 핵심 문장

1. **`BaseModel` 을 상속하면 타입 힌트가 검사 규칙이 된다** — 바꿀 수 있는 값은 바꾸고, 못 바꾸면 `ValidationError`.
2. **제약은 층으로 쌓인다** — 타입 → `Field` → `field_validator` → `model_validator(mode='after')`.
3. **검증기가 돌려준 값이 저장된다** — 그래서 검사와 정규화를 한 자리에서 한다.
4. **객체는 dict · JSON 으로 나가고, JSON 에서 들어온다** — `model_dump` · `model_dump_json` · `model_validate_json`.
5. **모델 설정은 `model_config = ConfigDict(...)`** — `frozen=True` 면 만든 뒤 바꿀 수 없다.

## 관련 자료

- `dataclasses` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- `type-hints` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- `class-basics` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- `properties` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- 원본: study-site 항목 데이터 `data/python/oop.json` 의 `pydantic-basics`

## 용어 풀이

- **Pydantic** — 타입 힌트를 바탕으로 데이터를 검증 · 변환 · 직렬화하는 파이썬 라이브러리.
- **BaseModel** — Pydantic 모델의 베이스 클래스. 상속하면 검증 · 직렬화가 붙는다.
- **필드** — 모델 몸체의 `이름: 타입` 한 줄로 선언한 칸.
- **타입 힌트** — 기대하는 타입을 적은 표시. 파이썬 자체는 실행 중에 강제하지 않는다.
- **검증** — 들어온 값이 규칙에 맞는지 확인하는 일.
- **자동 타입 변환** — 필드 타입으로 읽을 수 있는 값을 그 타입으로 바꾸는 일.
- **ValidationError** — 검증 실패 시 Pydantic 이 던지는 예외. 틀린 필드 목록을 담는다.
- **Field** — 필드에 제약(`gt` · `min_length` 등)과 메타데이터(`description`)를 붙이는 함수.
- **gt / ge** — 「보다 크다」 / 「크거나 같다」.
- **default_factory** — 객체마다 불러 기본값을 새로 만드는 함수.
- **field_validator** — 필드 하나에 붙는 사용자 정의 검증 메서드.
- **model_validator** — 모델 전체에 붙는 검증 메서드. `mode='after'` 면 필드 검증 뒤에 돈다.
- **정규화** — 같은 뜻의 값을 한 꼴로 맞추는 일.
- **중첩 모델** — 다른 모델을 필드 타입으로 가진 모델.
- **직렬화** — 객체를 dict · JSON 처럼 내보낼 수 있는 꼴로 바꾸는 일.
- **model_dump / model_dump_json** — 모델을 dict / JSON 문자열로 바꾸는 메서드.
- **model_validate_json** — JSON 문자열에서 모델을 검증해 만드는 클래스 메서드.
- **exclude_none** — 직렬화할 때 `None` 인 필드를 빼라는 옵션.
- **ConfigDict** — v2 에서 모델 설정을 담는 딕셔너리.
- **frozen** — 만든 뒤 필드를 바꿀 수 없게 하는 설정.
- **Optional[T]** — `T` 또는 `None`.
- **가변 기본값** — 리스트 · dict 처럼 고칠 수 있는 객체를 기본값으로 둔 것.

## 더 들어가면

- `model_validator` 에는 `mode='before'` 도 있어, 타입 변환 전에 원본 입력(dict 등)을 받아 손볼 수 있다(확인 필요).
- 자동 변환을 끄고 타입이 정확히 맞을 때만 받는 엄격(strict) 모드가 있다(확인 필요).
- `EmailStr` 은 쓰려면 `email-validator` 패키지가 추가로 필요하다는 설명이 있다(확인 필요).
- v1 의 `@validator` · `@root_validator` 는 v2 에서 `@field_validator` · `@model_validator` 로 바뀌었다(확인 필요).
- 환경 변수에서 설정을 읽는 `BaseSettings` 는 v2 에서 별도 패키지(`pydantic-settings`)로 나뉘었다(확인 필요).
- `model_json_schema()` 로 모델의 JSON Schema 를 뽑을 수 있고, FastAPI 는 이것으로 API 문서를 만든다(확인 필요).
- `model_copy(update={...})` 로 frozen 모델의 바뀐 사본을 만들 수 있다(확인 필요).
