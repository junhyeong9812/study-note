# python/python-web-deep/10 — Flask-SQLAlchemy: 모델과 관계 — 정리 (힌트)

> 출처 — study-site 항목 `python/flask-sqlalchemy`(항목 데이터 `data/python/django-flask-deep.json`) · 정답 코드 study-practice `python/python-web-deep/reference/flask-sqlalchemy.py`\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).\
> 실행 — 원본 예제를 `Python 3.12.3` 에서 2회 돌렸다.

## 한눈에 — 쉽게 말하면

**Flask-SQLAlchemy 는 「통역사가 붙은 식당 주문서」다.**
손님은 한국어로 주문하고, 주방은 정해진 주방 용어만 알아듣는다.
통역사가 손님의 말을 주방 용어로 바꾸고, 주문은 주문서에 모았다가 한꺼번에 주방으로 넘긴다.
메뉴판이 바뀌면 「언제 무엇이 바뀌었나」를 개정 기록으로 남긴다.
Flask-SQLAlchemy 도 똑같은 구조다.
파이썬 코드가 객체로 말하면 SQLAlchemy 가 SQL 로 옮긴다.
변경은 세션에 모였다가 `commit()` 때 데이터베이스로 간다.
테이블 모양이 바뀌면 Flask-Migrate 가 그 변경을 파일로 남긴다.

> **ORM** — 데이터베이스의 행을 프로그래밍 언어의 객체로 다루게 해 주는 도구다.\
> 예: `user.email = 'a@b.c'` 라고 쓰면 ORM 이 `UPDATE users SET email=...` 로 옮긴다.

| 비유 | 실체 |
|---|---|
| 손님의 말(한국어) | 파이썬 객체 · 속성 · 메서드 호출 |
| 통역사 | SQLAlchemy |
| 메뉴판 | 모델 클래스(`db.Model` 을 상속한 클래스) |
| 주문서 | `db.session` |
| 주방 | 데이터베이스 |
| 「주문 넣어 주세요」 | `db.session.commit()` |
| 메뉴판 개정 기록 | 마이그레이션 파일(Flask-Migrate · Alembic) |

```text
 파이썬 코드                 SQLAlchemy               데이터베이스
 ───────────                ───────────              ────────────
 User(username='alice')  →  INSERT 로 옮김     ┐
 user.email = '...'      →  UPDATE 로 옮김     ├─ session 에 모임 ─ commit() ─→  테이블에 반영
 db.session.delete(u)    →  DELETE 로 옮김     ┘
 User.query.filter_by()  →  SELECT 로 옮김 ───────────────────────────────→  행 → 객체로 돌아옴
```

## 이 주제가 답하려는 질문

1. 파이썬 클래스 하나가 어떻게 테이블 하나가 되고, 컬럼의 제약(NOT NULL · UNIQUE · 기본값)은 어디에 적나?
2. 1:N · 1:1 · M:N · 자기참조 관계는 각각 무엇으로 표현하나?
3. 행을 만들고 · 읽고 · 고치고 · 지우는 일(CRUD)은 세션과 쿼리 API 로 어떻게 하나?
4. 모델이 바뀌었을 때 실제 테이블 모양은 어떻게 따라 바꾸나?

## 동작 방식

### (1) 모델 정의 — 클래스가 테이블이 된다

**언제 쓰나** — 데이터베이스에 저장할 대상(사용자 · 상품 · 주문)마다 하나씩 만든다.
`db.Model` 을 상속하고, 클래스 속성으로 `db.Column` 을 둔다.

```text
class User(db.Model):                          테이블 users
    __tablename__ = 'users'          ──→       ┌────┬──────────┬──────────┬───────────┐
    id = Column(Integer, primary_key=True)     │ id │ username │ is_active│ created_at│
    username = Column(String(80),              ├────┼──────────┼──────────┼───────────┤
        unique=True, nullable=False)           │ 1  │ alice    │ True     │ (삽입 시각)│
    is_active = Column(Boolean, default=True)  └────┴──────────┴──────────┴───────────┘
    created_at = Column(DateTime,
        default=datetime.utcnow)
```

- `db.Model` 은 선언형 베이스다 — 상속한 클래스를 테이블에 대응시킨다.
- `__tablename__` 으로 테이블 이름을 직접 정한다.
- `primary_key=True` 는 그 컬럼을 기본 키로 삼는다.
- `nullable=False` 는 NOT NULL 제약이고, `unique=True` 는 UNIQUE 인덱스다.
- `default` 는 행을 만들 때 넣을 값이고, `onupdate` 는 행을 고칠 때마다 다시 넣을 값이다.
- `default=datetime.utcnow` 에는 괄호가 없다 — 함수 자체를 넘겨 두면 행을 넣을 때마다 그 함수를 불러 그때의 시각을 쓴다.

> **기본 키** — 테이블에서 행 하나를 유일하게 가리키는 컬럼이다.\
> 예: `users.id` 가 1 인 행은 하나뿐이다.

모델 클래스는 평범한 파이썬 클래스이기도 하다.
원본의 `User` 는 `__repr__` 로 `<User alice>` 꼴의 표시를 정하고, `set_password` · `check_password` 에서 `werkzeug.security` 의 해시 함수를 불러 비밀번호를 원문 대신 해시로 저장 · 확인한다.
`Product.is_available` 처럼 `@property` 로 만든 값은 컬럼이 아니다 — `stock > 0` 을 파이썬에서 계산할 뿐 테이블에 저장되지 않는다.

### (2) 1:N · 1:1 관계 — 외래 키 + `relationship`

**언제 쓰나** — 「사용자 한 명이 주문 여러 개」처럼 한쪽 행이 다른 쪽 행을 가리킬 때 쓴다.

```text
 users                       orders
 ┌────┬──────────┐           ┌────┬─────────┬─────────┐
 │ id │ username │ ◀──────── │ id │ user_id │ status  │   user_id = ForeignKey('users.id')
 ├────┼──────────┤           ├────┼─────────┼─────────┤
 │ 1  │ alice    │           │ 10 │ 1       │ pending │
 └────┴──────────┘           │ 11 │ 1       │ paid    │
                             └────┴─────────┴─────────┘
 User.orders   = relationship('Order', backref='customer', lazy='dynamic')
   user.orders      → alice 의 주문들(쿼리 객체)
   order.customer   → 그 주문의 User 객체
```

- 테이블 사이의 실제 연결은 N 쪽의 외래 키 컬럼(`Order.user_id`)이 만든다.
- `db.relationship` 은 그 연결을 파이썬 속성으로 걸어 준다 — `user.orders` 로 주문을 꺼낸다.
- `backref='customer'` 는 반대쪽에도 속성을 만든다 — `order.customer` 로 사용자를 꺼낸다.
- `lazy='dynamic'` 이면 `user.orders` 가 리스트가 아니라 **쿼리 객체**다 — `user.orders.filter(...)` 처럼 조건을 더 붙인 뒤 실행할 수 있다.
- `uselist=False` 는 「결과가 하나뿐」이라는 뜻이다 — `user.profile` 이 리스트가 아닌 객체 하나가 되어 1:1 이 된다.
- `'Order'` · `'Profile'` 처럼 대상을 문자열로 적으면 그 이름은 나중에 찾는다 — 아래쪽에 정의할 클래스도 가리킬 수 있지만, 끝까지 정의되지 않으면 관계를 설정하는 단계에서 오류가 난다(정확한 시점과 메시지는 확인 필요).

> **외래 키** — 다른 테이블의 기본 키 값을 담아 그 행을 가리키는 컬럼이다.\
> 예: `orders.user_id = 1` 은 `users.id = 1` 인 행을 가리킨다.

### (3) M:N 관계와 자기참조 — 중간 테이블 · `remote_side`

**언제 쓰나** — 주문 하나에 상품 여럿, 상품 하나가 주문 여럿에 들어가는 경우(M:N), 또는 카테고리 안에 카테고리가 있는 트리(자기참조)에 쓴다.

```text
 orders            order_items (중간 테이블)              products
 ┌────┐           ┌──────────┬────────────┬──────────┐   ┌────┬────────┐
 │ 10 │ ◀──────── │ order_id │ product_id │ quantity │ ─▶│ 7  │ Python │
 │ 11 │           │ 10       │ 7          │ 1        │   │ 8  │ Flask  │
 └────┘           │ 10       │ 8          │ 1        │   └────┴────────┘
                  │ 11       │ 7          │ 1        │
                  └──────────┴────────────┴──────────┘
 Order.products = relationship('Product', secondary=order_items, backref='orders')
```

- 한 테이블의 외래 키 컬럼 하나는 값을 하나만 담으므로, 「여럿 대 여럿」은 두 외래 키를 짝으로 담는 중간 테이블로 푼다.
- 중간 테이블은 모델 클래스가 아니라 `db.Table(...)` 로 만든다.
- `secondary=` 에 그 중간 테이블을 넘기면 `order.products` · `product.orders` 가 중간 테이블을 거쳐 이어진다.
- `secondary` 에는 테이블 객체(`order_items`)도, 테이블 이름 문자열(`'product_tags'`)도 넘길 수 있다.

```text
 categories
 ┌────┬────────┬───────────┐
 │ id │ name   │ parent_id │  parent_id = ForeignKey('categories.id')  ← 같은 테이블을 가리킴
 │ 1  │ 책     │ NULL      │
 │ 2  │ 프로그래밍│ 1        │  children = relationship('Category',
 └────┴────────┴───────────┘      backref=db.backref('parent', remote_side=[id]))
   cat1.children → [cat2]      cat2.parent → cat1
```

- 자기참조는 외래 키가 자기 테이블을 가리킨다.
- 두 끝이 같은 테이블이라 어느 쪽이 부모인지 저절로 정해지지 않는다.
- `remote_side=[id]` 는 「`parent` 쪽에서 상대(부모)의 `id` 를 본다」고 못박아 방향을 정한다.

### (4) 세션과 쿼리 — CRUD

**언제 쓰나** — 행을 만들고 읽고 고치고 지울 때마다 쓴다.

```text
 new_user = User(...)          → 파이썬 객체만 생김
 db.session.add(new_user)      → 세션 장부에 「새 행」으로 적힘(아직 확정 아님)
 user.email = 'new@...'        → 세션이 이 변경을 추적
 db.session.commit()           → 모아 둔 변경을 SQL 로 보내고 COMMIT
 db.session.rollback()         → 확정 전 변경을 되돌림(ROLLBACK)
```

- 세션은 Unit of Work 다 — 트랜잭션 단위로 변경을 추적하다가 한꺼번에 보낸다.
- `commit()` 은 COMMIT 에, `rollback()` 은 ROLLBACK 에 대응한다.
- 객체를 만든 것만으로는 저장되지 않는다 — `add` 하고 `commit` 해야 한다.

> **트랜잭션** — 여러 변경을 「전부 반영 아니면 전부 취소」로 묶는 단위다.\
> 예: 주문 저장과 재고 차감을 한 트랜잭션으로 묶으면 하나만 반영되는 일이 없다.

```text
 User.query                       → 쿼리 객체(아직 SQL 을 보내지 않음)
   .filter_by(username='alice')   → 조건이 붙은 쿼리 객체
   .first()                       → 이때 SQL 실행 → 첫 행(없으면 None)
   .first_or_404()                → 이때 SQL 실행 → 첫 행(없으면 404 응답)
```

- 쿼리는 조건을 이어 붙이는 동안 쌓이기만 하고, `.first()` · `.all()` 같은 메서드에서 실행된다.
- `filter_by(이름=값)` 은 키워드로 「같다」 조건만 쓴다.
- `filter(식)` 은 `User.is_active == True` · `Product.stock > 0` 처럼 식을 받는다.
- 식은 `and_` · `or_` 로 묶고, `between` · `contains` 같은 메서드로 범위 · 부분 문자열 조건을 만든다.
- `order_by(컬럼.desc())` · `limit(10)` 으로 정렬 · 개수를 정한다.
- `db.session.query(func.count(...), func.avg(...), func.sum(...))` 는 행 대신 집계 값을 묻는다.
- `.join(Product).group_by(Category.name)` 은 테이블을 이어 묶음별로 센다 — `.label('count')` 로 결과 이름을 붙인다.
- 한 행은 속성을 바꾸고 `commit` 하면 고쳐지고, `db.session.delete(obj)` 후 `commit` 하면 지워진다.
- `Query.filter(...).update({...})` · `.filter(...).delete()` 는 행을 하나씩 불러오지 않고 SQL 한 문장으로 일괄 처리한다 — N+1 이 없다.

> **N+1** — 목록 1번 조회 뒤 행마다 1번씩 더 조회해 질의가 N+1 번 나가는 문제다.\
> 예: 비활성 사용자 100명을 하나씩 불러 고치면 질의가 101번 나간다.

### (5) 마이그레이션 — 스키마 변경을 코드로 남긴다

**언제 쓰나** — 모델에 컬럼을 더하거나 바꿔서 실제 테이블 모양도 바꿔야 할 때 쓴다.

```text
 flask db init                    → migrations/ 디렉토리 생성(처음 한 번)
        │
 모델 수정 (예: User 에 phone 추가)
        │
 flask db migrate -m "Add phone field to User"
        │                         → 모델과 DB 를 비교해 마이그레이션 파일 생성
 생성된 파일을 사람이 읽고 고침   ← 반드시
        │
 flask db upgrade                 → DB 에 적용
 flask db downgrade               → 한 단계 되돌림(롤백)
 flask db history                 → 적용 이력 보기
```

- Flask-Migrate 는 Alembic 을 Flask 명령으로 감싼 것이다.
- Alembic 은 스키마 버전 관리 도구다 — 모델 변경을 파이썬 코드(마이그레이션 파일)로 추적한다.
- 자동 생성된 파일은 의도와 다를 수 있으므로 `upgrade` 전에 반드시 리뷰한다.

> **마이그레이션** — 테이블 구조를 한 버전에서 다음 버전으로 바꾸는 절차를 적은 파일이다.\
> 예: 「`users` 에 `phone` 컬럼 추가 · 되돌릴 때는 삭제」를 담은 파이썬 파일.

### (6) 인메모리 시뮬레이션 — `InMemoryDB`

**언제 쓰나** — 원본 예제의 5절이다. 데이터베이스 없이 CRUD 의 모양만 흉내 낸다.

```text
 tables  = {'users': [ {...}, {...} ]}     테이블별 레코드 리스트
 auto_id = {'users': 2}                    테이블별 자동 증가 카운터

 create('users', data) → 테이블 없으면 [] 와 0 으로 시작 → 카운터+1 → {'id': n, **data} 를 리스트에 붙이고 그 사전을 돌려줌
 query('users', active=True) → 조건 키마다 r.get(key) == value 인 것만 남김
 update('users', 1, data)    → id 가 같은 사전에 dict.update → 그 사전을 돌려줌(없으면 None)
 delete('users', 2)          → id 가 같은 것을 pop → True(없으면 False)
```

- `create` 가 돌려주는 사전은 리스트에 넣은 것과 **같은 객체**다 — 나중에 `update` 로 저장소를 고치면 그 변수로 보아도 바뀐 값이 보인다.
- `query` 의 `**filters` 는 `filter_by` 와 같은 의미다 — 「키 = 값」 조건만 다룬다.
- 진짜 SQLAlchemy 는 조건을 SQL 로 옮겨 데이터베이스에 보낸다.
- 이 시뮬레이션에는 세션도 `commit` 도 없다 — 호출 즉시 사전과 리스트가 바뀐다.
- 원본 1~4절의 모델 · 쿼리 · 명령은 `print("""...""")` 로 **글자 그대로 찍는 안내문**이다. 실제로 돌아가는 부분은 5절과 「핵심 정리」뿐이다.

## 문법 — 형태와 규칙

```python
class Author(db.Model):
    __tablename__ = 'authors'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    books = db.relationship('Book', backref='author', lazy='dynamic')

class Book(db.Model):
    __tablename__ = 'books'
    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey('authors.id'), nullable=False)

db.session.add(Author(name='kim')); db.session.commit()
recent = Author.query.filter_by(name='kim').first().books.filter(Book.id > 10).all()
```

- 모델은 `db.Model` 을 상속하고, 컬럼은 `db.Column(타입, 옵션...)` 으로 쓴다.
- 외래 키는 `db.ForeignKey('테이블이름.컬럼')` — **테이블 이름**을 쓴다(클래스 이름이 아니다).
- `db.relationship('클래스이름', ...)` — **클래스 이름**을 쓴다.
- 변경은 `db.session.add` · `delete` 뒤에 `commit` 해야 확정된다.

| `db.Column` 옵션 | 뜻 |
|---|---|
| `primary_key=True` | 기본 키 |
| `nullable=False` | NOT NULL 제약 |
| `unique=True` | UNIQUE 인덱스 |
| `default=값 또는 함수` | 행을 만들 때 넣을 값 |
| `onupdate=값 또는 함수` | 행을 고칠 때마다 넣을 값 |
| `db.ForeignKey('t.c')` | 외래 키(`t` 테이블의 `c` 를 가리킴) |

| `db.relationship` 옵션 | 뜻 |
|---|---|
| `backref='이름'` | 반대쪽 클래스에 속성을 만든다 |
| `lazy='dynamic'` | 결과 대신 쿼리 객체를 돌려준다 |
| `uselist=False` | 결과를 하나로(1:1) |
| `secondary=중간테이블` | M:N 을 중간 테이블로 잇는다 |
| `db.backref('이름', remote_side=[id])` | 자기참조에서 상대 쪽 컬럼을 정한다 |

| 쿼리 | 하는 일 |
|---|---|
| `Model.query.get(pk)` | 기본 키로 한 행 |
| `.filter_by(k=v)` / `.filter(식)` | 조건 |
| `.first()` · `.first_or_404()` · `.all()` | 실행해서 결과 꺼내기 |
| `.order_by(...)` · `.limit(n)` · `.offset(n)` | 정렬 · 개수 · 건너뛰기 |
| `.filter(...).update({...})` · `.delete()` | 일괄 수정 · 삭제(SQL 한 문장) |

## 어디서 틀리나

### 1. 마이그레이션 파일을 읽지 않고 `upgrade` 한다
자동 생성된 파일은 의도와 다를 수 있다.
`flask db migrate` 다음 `flask db upgrade` 사이에 반드시 파일을 리뷰한다.

### 2. `default=datetime.utcnow()` 처럼 괄호를 붙인다
괄호를 붙이면 클래스를 읽는 순간 한 번 불린 시각 값이 기본값으로 굳는다.
그러면 그 뒤 만드는 행이 모두 같은 시각을 받는다.
함수 자체(`datetime.utcnow`)를 넘겨야 행마다 새로 불린다.

### 3. `lazy='dynamic'` 관계를 리스트처럼 다룬다
`user.orders` 는 쿼리 객체라서 결과를 얻으려면 `.all()` 같은 실행 메서드를 불러야 한다.
대신 `.filter(...)` · `.order_by(...)` 를 더 붙일 수 있다는 것이 장점이다.

### 4. 문자열로 가리킨 대상이 정의되어 있지 않다
원본 발췌의 `Profile` · `Tag` 클래스와 `product_tags` 테이블은 발췌 어디에도 정의되어 있지 않다.
그대로 앱에 넣으면 관계를 설정하는 단계에서 이름을 찾지 못해 실패한다(정확한 시점과 메시지는 확인 필요).
쓰려면 그 클래스와 중간 테이블을 함께 정의해야 한다.

### 5. `add` 만 하고 `commit` 을 빼먹는다
세션에 적힌 변경은 `commit()` 해야 확정된다.

### 6. 자기참조에서 `remote_side` 를 빼먹는다
두 끝이 같은 테이블이라 부모 방향이 정해지지 않는다.

### 7. 트랜잭션 격리 수준을 「기본 READ COMMITTED」로 단정한다
원본 주석의 주장: 「트랜잭션 격리: 기본 READ COMMITTED」.
왜 의심스러운가: 격리 수준의 기본값은 SQLAlchemy 가 아니라 데이터베이스 제품과 그 설정이 정한다.
제품마다 기본값이 다를 수 있다(제품별 값은 확인 필요).

### 8. 시뮬레이션이 돌려준 사전을 고치면 저장소도 바뀐다
`InMemoryDB.create` · `update` 는 리스트 안의 사전을 그대로 돌려준다.
`query` 도 조건이 없으면 내부 리스트를 그대로 돌려준다.
돌려받은 것을 고치면 「DB」도 함께 바뀐다.

### 9. 같은 이름 `db` 를 다시 쓴다
원본 5절은 `db = InMemoryDB()` 로 이름 `db` 를 새로 묶는다.
1~4절은 문자열이라 문제가 없지만, 실제 앱에서 이러면 Flask-SQLAlchemy 확장 객체가 가려진다.

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| `db.Model` · `Model.query` · `first_or_404` | Flask-SQLAlchemy 확장(파이썬 언어가 아님) |
| `relationship` · `secondary` · `remote_side` · `lazy='dynamic'` | SQLAlchemy 라이브러리 — 권장 API 는 버전마다 바뀔 수 있다(확인 필요) |
| 「트랜잭션 격리 기본 READ COMMITTED」(원본 주석) | 데이터베이스 제품 · 설정 — 원본의 단정은 의심스럽다 |
| `unique=True` → UNIQUE 인덱스 | 실제로 만드는 것은 데이터베이스다 — 제약 · 인덱스의 정확한 형태는 제품마다 다를 수 있다(확인 필요) |
| `flask db migrate` 가 변경을 알아챈다 | Alembic 의 자동 비교 기능 — 모든 변경을 잡는다는 보장이 없어 리뷰가 필요하다 |
| 데모 출력의 사전 키 순서(`id` 가 먼저) | 파이썬 언어 명세의 「사전은 삽입 순서를 지킨다」(도입 버전은 확인 필요) |
| `{'id': ..., **data}` 의 펼치기 | 파이썬 언어 문법 |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 사용자 한 명의 주문 중 일부만 골라 보기 | `lazy='dynamic'` + `.filter(...)` | 전체를 리스트로 받아 파이썬에서 거르기 |
| 1:1 관계 | `uselist=False` | 매번 `[0]` 으로 꺼내기 |
| 주문 ↔ 상품 | `db.Table` 중간 테이블 + `secondary` | 한쪽 테이블에 외래 키 하나 |
| 카테고리 트리 | 자기참조 외래 키 + `remote_side` | 깊이마다 테이블 하나씩 |
| 조건에 맞는 행을 한꺼번에 수정 · 삭제 | `.filter(...).update()` · `.delete()` | 하나씩 불러 고치는 반복문(N+1) |
| 컬럼 추가 · 변경 | `flask db migrate` → 리뷰 → `upgrade` | 운영 DB 에 손으로 `ALTER TABLE` |
| 생성 시각 · 수정 시각 | `default=` · `onupdate=` 에 함수 | 괄호 붙인 호출 결과 |

## 핵심 문장

1. **모델 = `db.Model` 을 상속한 클래스, 컬럼 = `db.Column`** — 제약은 `nullable` · `unique` · `default` · `onupdate` 로 적는다.
2. **테이블 연결은 외래 키가, 파이썬 속성은 `db.relationship` 이 만든다** — `backref` 는 반대쪽 속성이다.
3. **M:N 은 중간 테이블 + `secondary`, 자기참조는 `remote_side`** 로 푼다.
4. **변경은 세션에 모였다가 `commit()` 에 확정된다** — 쿼리는 실행 메서드에서야 SQL 이 나간다.
5. **스키마 변경은 Flask-Migrate 로 파일을 만들고, 그 파일은 반드시 리뷰한다.**

## 관련 자료

- [flask-blueprint](../09-flask-blueprint/2-summary.md)
- [flask-auth](../11-flask-auth/2-summary.md)
- `django-queryset` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- 원본: study-site 항목 데이터 `data/python/django-flask-deep.json` 의 `flask-sqlalchemy`

## 용어 풀이

- **ORM** — 데이터베이스 행을 객체로 다루게 해 주는 도구.
- **모델** — 테이블 하나에 대응하는 클래스.
- **선언형 베이스** — 상속하면 클래스를 테이블에 대응시켜 주는 부모 클래스(`db.Model`).
- **기본 키** — 행 하나를 유일하게 가리키는 컬럼.
- **외래 키** — 다른 행의 기본 키를 담아 그 행을 가리키는 컬럼.
- **backref** — 관계를 걸 때 반대쪽 클래스에 자동으로 생기는 속성.
- **쿼리 객체** — 조건을 쌓아 두었다가 실행 메서드에서 SQL 을 보내는 객체.
- **중간 테이블(association table)** — M:N 의 두 외래 키를 짝으로 담는 테이블.
- **자기참조** — 외래 키가 자기 테이블을 가리키는 관계.
- **세션 · Unit of Work** — 변경을 추적해 두었다가 트랜잭션 단위로 보내는 장부.
- **트랜잭션** — 「전부 반영 아니면 전부 취소」로 묶인 변경의 단위.
- **격리 수준** — 동시에 도는 트랜잭션끼리 서로의 변경을 얼마나 보나를 정한 등급.
- **N+1** — 목록 1번 + 행마다 1번씩 질의가 나가는 문제.
- **마이그레이션** — 테이블 구조 변경을 적은 파일.
- **Alembic** — SQLAlchemy 용 스키마 버전 관리 도구, Flask-Migrate 가 감싼다.

## 더 들어가면

- 원본의 `order_items` 에는 `quantity` 컬럼이 있지만, `secondary` 관계는 두 외래 키만 채운다 — 수량을 다루려면 중간 테이블을 모델 클래스로 만드는 「연관 객체」 방식이 필요하다(확인 필요).
- `Model.query.get(pk)` 는 SQLAlchemy 2.0 계열에서 낡은 방식으로 분류되고 `db.session.get(Model, pk)` 가 권장된다고 알려져 있다(확인 필요).
- `lazy='dynamic'` 도 SQLAlchemy 2.0 계열에서는 `lazy='write_only'` 등으로 대체가 권장된다(확인 필요).
- `datetime.utcnow` 는 최근 파이썬 버전에서 폐기 예정 경고가 붙었고, `datetime.now(timezone.utc)` 가 권장된다(확인 필요).
- `Query.update()` · `delete()` 의 일괄 처리는 세션이 이미 들고 있는 객체와 어긋날 수 있어 `synchronize_session` 옵션이 있다(확인 필요).
- `User.is_active == True` 가 참 · 거짓이 아니라 SQL 조건 객체가 되는 것은 SQLAlchemy 가 컬럼 속성의 비교 연산자를 다시 정의했기 때문이다(확인 필요).
