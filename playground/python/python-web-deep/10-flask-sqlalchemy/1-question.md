# python/python-web-deep/10 — Flask-SQLAlchemy: 모델과 관계 — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 사용자 둘을 만들고 활성 사용자를 세면 (예측)

```python
# 질문용 발췌
db = InMemoryDB()
print("Create:")
u1 = db.create('users', {'name': 'Alice', 'email': 'alice@ex.com', 'active': True})
u2 = db.create('users', {'name': 'Bob', 'email': 'bob@ex.com', 'active': True})
print(f"  {u1}")
print(f"  {u2}")
print("\nRead:")
active = db.query('users', active=True)
print(f"  활성 사용자: {len(active)}명")
```

- 두 사전의 `id` 는 각각 무엇이고, 키는 어떤 차례로 찍히나?
- `Read:` 아래 줄에는 무엇이 찍히나?

### 2. 1번에 이어 1번을 고치고 2번을 지우면 (예측)

```python
# 질문용 발췌 — 1번 문항 코드에 이어서
print("Update:")
updated = db.update('users', 1, {'email': 'alice_new@ex.com'})
print(f"  {updated}")
print("\nDelete:")
result = db.delete('users', 2)
print(f"  삭제 성공: {result}")
print(f"  남은 사용자: {db.query('users')}")
```

- `Update:` 아래에는 어떤 사전이 찍히나?
- `남은 사용자:` 뒤에는 무엇이 찍히나?

### 3. 2번 문항이 끝난 뒤 이 두 줄을 더 부르면 (예측)

```python
# 질문용 발췌 — 2번 문항 코드에 이어서
print(u1)
print(db.update('users', 2, {'name': 'Bobby'}))
```

- `print(u1)` 의 `email` 은 처음 값과 고친 값 가운데 어느 쪽인가?
- 두 번째 줄은 무엇을 찍나?

### 4. `default=datetime.utcnow` 에 괄호가 없는 까닭 (왜)
- 괄호를 붙여 `datetime.utcnow()` 로 쓰면 무엇이 달라지나?

### 5. `lazy='dynamic'` 관계 뒤에 조건을 더 붙일 수 있는 까닭 (왜)
- `user.orders.filter(...)` 가 되는 것은 `user.orders` 가 무엇이기 때문인가?

### 6. M:N 관계와 외래 키 하나 (경계)
- 주문 ↔ 상품을 한쪽 테이블의 외래 키 컬럼 하나로 표현할 수 없는 까닭은 무엇인가?
- `secondary=` 에는 무엇을 넘기나?

### 7. 발췌한 모델을 그대로 앱에 넣을 때 (경계)
- `Profile` · `Tag` · `product_tags` 를 가리키는 관계는 무엇이 빠져서 실패하나?

### 8. `InMemoryDB.query` 와 진짜 ORM (연결)
- `query('users', active=True)` 는 SQLAlchemy 쿼리 API 의 어느 메서드와 같은 의미인가?
- 진짜 SQLAlchemy 에는 있고 이 시뮬레이션에는 없는 단계는 무엇인가?

### 9. 마이그레이션 파일을 리뷰하는 까닭 (왜)
- `flask db migrate` 와 `flask db upgrade` 사이에 사람이 파일을 읽어야 하는 까닭은 무엇인가?

### 10. 「트랜잭션 격리: 기본 READ COMMITTED」라는 주석 (연결)
- 격리 수준의 기본값은 SQLAlchemy 와 데이터베이스 가운데 어느 쪽이 정하나?

## 실습

### 실습 1. Flask-SQLAlchemy 패턴 안내서와 인메모리 ORM 데모 만들기

**만들 것** — 모델 · 관계 · CRUD 쿼리 · 마이그레이션 명령을 안내문으로 찍고, 데이터베이스 없이 CRUD 를 흉내 내는 `InMemoryDB` 를 만들어 돌리는 파이썬 스크립트 하나.

**준비물** — 표준 라이브러리만 있으면 된다. Flask · Flask-SQLAlchemy · Flask-Migrate 코드는 `print("""...""")` 로 찍는 글이고, 실제 데이터베이스 동작은 `InMemoryDB` 로 흉내 낸 것이다.

**요구 조건**

1. 1단계 — 맨 위에서 `datetime` 과 `typing` 의 `List` · `Optional` 을 가져온다.
2. 2단계 — `=== 1. 모델 정의 ===` 를 찍고, `User` 모델 코드를 여러 줄 문자열로 찍는다: 테이블 이름 `users`, 컬럼 `id`(기본 키) · `username` · `email`(둘 다 UNIQUE · NOT NULL) · `password_hash`(NOT NULL) · `is_active`(기본 참) · `created_at`(생성 시각) · `updated_at`(생성 · 수정 시각), 1:N `orders`(`backref='customer'`, `lazy='dynamic'`), 1:1 `profile`(`uselist=False`), `__repr__` · `set_password` · `check_password`.
3. 3단계 — `=== 2. 관계 정의 ===` 를 찍고, 중간 테이블 `order_items`(주문 · 상품 외래 키와 수량), `Product`(카테고리 외래 키 · `category` 관계 · `tags` M:N · `is_available` 속성), `Order`(사용자 외래 키 · 상태 · 합계 · 생성 시각 · `products` M:N), `Category`(자기참조 `parent_id` · `children` 과 `remote_side` 를 쓴 `parent`)를 문자열로 찍는다.
4. 4단계 — `=== 3. CRUD 쿼리 패턴 ===` 을 찍고, Create · Read(`get` · `filter_by` · `first_or_404` · `filter` · `order_by`/`limit`) · 고급 필터(`and_` · `or_` · `between` · `contains`) · 집계(`func.count/avg/sum`) · 그룹화(`join` · `group_by`) · Update · 일괄 업데이트 · Delete · 일괄 삭제 코드를 문자열로 찍는다.
5. 5단계 — `=== 4. Flask-Migrate (Alembic) ===` 을 찍고, `init` · `migrate` · `upgrade` · `downgrade` · `history` 명령과 「모델 변경 후」 네 단계를 문자열로 찍는다.
6. 6단계 — `InMemoryDB` 클래스를 만든다: `tables`(테이블별 리스트) · `auto_id`(테이블별 카운터)를 갖고, `create` 는 테이블이 없으면 만들고 `id` 를 1씩 늘려 붙인 사전을 저장 · 반환한다. `query` 는 키워드 조건이 모두 같은 레코드만 돌려준다. `update` 는 `id` 로 찾아 고친 레코드를(없으면 `None`), `delete` 는 `id` 로 찾아 지우고 `True`(없으면 `False`)를 돌려준다.
7. 7단계 — `=== 5. ORM 패턴 데모 ===` 을 찍고, Alice · Bob 을 만들어 찍고, 활성 사용자 수를 찍고, 1번의 이메일을 `alice_new@ex.com` 으로 고쳐 찍고, 2번을 지운 결과와 남은 사용자를 찍는다.
8. 8단계 — `=== 핵심 정리 ===` 아래에 `db.Model` · `db.relationship` · `db.session` · Query API · Flask-Migrate 를 한 줄씩 요약해 찍는다.

**시작 코드**

```python
"""Flask-SQLAlchemy: 모델 정의, 관계, 쿼리"""
from datetime import datetime
from typing import List, Optional

print("=== 1. 모델 정의 ===")
print("""
from app.extensions import db
from datetime import datetime

# TODO: class User(db.Model) — 테이블 이름, 컬럼 7개, orders/profile 관계, 메서드 3개
""")

print("=== 2. 관계 정의 ===")
print("""
# TODO: order_items 중간 테이블
# TODO: Product / Order / Category 모델 (외래 키 · relationship · secondary · remote_side)
""")

print("=== 3. CRUD 쿼리 패턴 ===")
print("""
# TODO: Create / Read / 고급 필터링 / 집계 / 그룹화 / Update / 일괄 업데이트 / Delete / 일괄 삭제
""")

print("=== 4. Flask-Migrate (Alembic) ===")
print("""
# TODO: flask db 명령 다섯 개와 「모델 변경 후」 네 단계
""")

print("=== 5. ORM 패턴 데모 ===")

class InMemoryDB:
    def __init__(self):
        self.tables = {}
        self.auto_id = {}

    def create(self, table: str, data: dict) -> dict:
        pass  # TODO: 테이블이 없으면 만들고, id 를 늘려 붙인 레코드를 저장하고 돌려준다

    def query(self, table: str, **filters) -> list:
        pass  # TODO: 조건마다 r.get(key) == value 인 레코드만 남긴다

    def update(self, table: str, record_id: int, data: dict) -> dict:
        pass  # TODO: id 로 찾아 고치고 돌려준다, 없으면 None

    def delete(self, table: str, record_id: int) -> bool:
        pass  # TODO: id 로 찾아 지우고 True, 없으면 False

db = InMemoryDB()

print("Create:")
# TODO: Alice, Bob 생성 후 각각 출력

print("\nRead:")
# TODO: active=True 인 사용자 수 출력

print("\nUpdate:")
# TODO: id 1 의 email 변경 후 출력

print("\nDelete:")
# TODO: id 2 삭제 결과와 남은 사용자 출력

print("\n=== 핵심 정리 ===")
# TODO: 다섯 줄 요약
```

**확인 방법** — `python flask-sqlalchemy.py` 로 돌려, 1~4절이 안내문으로 찍히고 5절 데모가 `id` 1 · 2 생성 → 활성 2명 → 1번 이메일 변경 → 2번 삭제 후 1번만 남는 차례로 찍히는지 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
