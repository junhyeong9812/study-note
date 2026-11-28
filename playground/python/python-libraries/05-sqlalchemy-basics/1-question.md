# python/python-libraries/05 — SQLAlchemy 기본 — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 나이 내림차순 상위 둘과 복합 조건 (예측)

```python
# 질문용 발췌 — users 에 Alice(30), Bob(25), Charlie(35) 가 이 차례로 들어 있다
ordered = session.query(User).order_by(User.age.desc()).limit(2).all()
result = session.query(User).filter(User.age >= 30, User.name != "Charlie").all()
```

- `ordered` 에는 누가 어떤 차례로 들어 있나?
- `result` 에는 누가 들어 있나?

### 2. 벌크 update 뒤 Charlie 를 지우면 (예측)

```python
# 질문용 발췌 — Alice(31), Bob(25), Charlie(35) 인 상태에서 시작한다
session.query(User).filter(User.age < 30).update({"age": 30})
session.commit()
user = session.query(User).filter_by(name="Charlie").first()
session.delete(user)
session.commit()
remaining = session.query(User).all()
```

- `remaining` 에는 누가 남고, Bob 의 `age` 는 얼마인가?

### 3. add 만 하고 commit 하기 전의 id (예측)

- `user1 = User(name="Alice", ...)` 을 만들고 `session.add(user1)` 만 한 상태에서 `user1.id` 를 찍으면 무엇이 보이나?

### 4. `sessionmaker` 의 결과에 괄호를 또 붙이는 까닭 (왜)

- `SessionLocal = sessionmaker(bind=engine)` 뒤에 왜 `SessionLocal()` 처럼 한 번 더 호출해야 하나?

### 5. 세션을 `with` 로 여는 까닭 (왜)

- 예제가 CRUD 마다 `with SessionLocal() as session:` 으로 세션을 여는 것은 무엇을 얻으려는 것인가?

### 6. `filter_by` 가 닿는 범위 (경계)

- `filter_by` 로 「나이가 30 이상」이나 「이름이 A 또는 B」를 쓸 수 있나?

### 7. 벌크 update 가 건너뛰는 것 (경계)

- `query(...).update({...})` 는 속성 할당 방식과 비교해 무엇을 얻고 무엇을 잃나?

### 8. `first()` 가 아무것도 못 찾으면 (경계)

- `filter_by(name="Alice").first()` 가 행을 못 찾았는데 바로 `user.age = 31` 을 하면 어떻게 되나?

### 9. 레거시 `query` 와 2.0 의 `select()` (연결)

- 예제의 `session.query(User).all()` 을 2.0 권장 꼴로 바꾸면 어떻게 쓰고, 모델 베이스 쪽에서는 무엇이 권장되나?

### 10. `default` 와 `server_default`, 그리고 `echo` (연결)

- `age = Column(Integer, default=0)` 의 기본값은 어느 쪽(파이썬 · DB)에서 채워지며, 실제로 어떤 SQL 이 나가는지 보려면 무엇을 켜나?

## 실습

### 실습 1. 인메모리 SQLite 로 사용자 CRUD 한 바퀴

**만들 것** — 인메모리 SQLite 에 `users` · `products` 두 테이블을 만들고, 사용자 셋을 넣고 · 여러 방식으로 조회하고 · 고치고 · 지우는 스크립트를 만든다.

**준비물** — `sqlalchemy` 패키지(`pip install sqlalchemy`)가 필요하다. 외부 DB 서버는 필요 없다.

**요구 조건**

1단계 — 엔진과 모델
1. `create_engine` 으로 인메모리 SQLite 엔진을 만들고 `echo` 는 끈다.
2. `declarative_base()` 로 `Base` 를 만든다.
3. `User` 모델(`users` 테이블): `id` 는 자동 증가 PK, `name` 은 필수, `email` 은 필수 · 중복 금지, `age` 는 기본값 0, `created_at` 은 생성 시각을 매번 자동 기록한다.
4. `Product` 모델(`products` 테이블): `id` 는 자동 증가 PK, `name` · `price` 는 필수, `stock` 은 기본값 0.
5. 두 모델 모두 `__repr__` 로 id · 이름 등을 보여 준다.

2단계 — 테이블과 세션 팩토리
6. `Base.metadata.create_all` 로 테이블을 만들고, 생성된 테이블 이름 목록을 찍는다.
7. `sessionmaker` 로 엔진에 묶인 `SessionLocal` 을 만든다.

3단계 — CREATE
8. 새 세션(`with`)에서 Alice(30) · Bob(25) · Charlie(35) 세 사용자를 만들고, 하나는 `add`, 둘은 `add_all` 로 등록한 뒤 `commit` 한다.
9. commit 뒤 세 사용자를 찍는다.

4단계 — READ (새 세션)
10. 전체 조회, `filter` 로 Alice, `filter_by` 로 Bob, `session.get` 으로 PK 1 을 찍는다.
11. 「age ≥ 30 이고 이름이 Charlie 가 아님」 조건 결과를 찍는다.
12. 나이 내림차순 상위 2 명과 전체 사용자 수를 찍는다.

5단계 — UPDATE (새 세션)
13. Alice 를 불러와 `age` 를 31 로 바꾸고 commit 한 뒤 찍는다.
14. 벌크 update 로 `age < 30` 인 사용자의 `age` 를 30 으로 바꾸고 commit 한 뒤 안내문을 찍는다.

6단계 — DELETE (새 세션)
15. Charlie 를 불러와 삭제하고 commit 한 뒤 안내문을 찍는다.
16. 남은 사용자 전체를 찍는다.

**시작 코드**

```python
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, text
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from datetime import datetime

# TODO: 인메모리 SQLite 엔진 (echo 끔)
engine = None

# TODO: Base 만들기
Base = None

class User(Base):
    # TODO: 테이블 이름
    # TODO: id, name, email, age, created_at 컬럼

    def __repr__(self):
        return f"User(id={self.id}, name='{self.name}', email='{self.email}')"

class Product(Base):
    # TODO: 테이블 이름
    # TODO: id, name, price, stock 컬럼

    def __repr__(self):
        return f"Product(id={self.id}, name='{self.name}', price={self.price})"

# TODO: 테이블 생성
print("=== 테이블 생성 완료 ===")
print(f"생성된 테이블: {...}")  # TODO: 테이블 이름 목록

# TODO: 세션 팩토리
SessionLocal = None

print("\n=== CREATE ===")
# TODO: 세션을 열고 Alice / Bob / Charlie 를 add · add_all · commit
#       commit 뒤 print(f"생성: {user1}") 처럼 셋을 찍는다

print("\n=== READ ===")
# TODO: 새 세션에서
#   print(f"전체 조회: {users}")
#   print(f"filter: {alice}")
#   print(f"filter_by: {bob}")
#   print(f"get(1): {user_by_id}")
#   print(f"age >= 30, name != Charlie: {result}")
#   print(f"나이 내림차순 상위 2: {ordered}")
#   print(f"총 사용자 수: {count}")

print("\n=== UPDATE ===")
# TODO: 새 세션에서 Alice age=31 → commit → print(f"수정 후: {user}")
#       벌크 update age<30 → 30 → commit
#       print("벌크 업데이트: age < 30인 사용자 -> age = 30")

print("\n=== DELETE ===")
# TODO: 새 세션에서 Charlie 삭제 → commit → print(f"삭제: Charlie")
#       print(f"남은 사용자: {remaining}")
```

**확인 방법** — `python sqlalchemy-basics.py` 로 돌려, 절 헤더(`=== CREATE ===` 등) 아래 찍힌 줄이 요구 조건 9~16 이 말하는 내용(누가 · 몇 명 · 어떤 나이)과 맞는지 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
