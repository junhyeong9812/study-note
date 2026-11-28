# python/python-web-deep/10 — Flask-SQLAlchemy: 모델과 관계 — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. `id` 는 1 · 2, 키는 `id` 가 맨 앞 · 활성 사용자 2명

**출력**

```text
Create:
  {'id': 1, 'name': 'Alice', 'email': 'alice@ex.com', 'active': True}
  {'id': 2, 'name': 'Bob', 'email': 'bob@ex.com', 'active': True}

Read:
  활성 사용자: 2명
```

**왜 그런가**
첫 `create` 때 `users` 테이블이 없으므로 리스트와 카운터 0 으로 시작하고, 카운터를 1 늘려 `id` 1 을 붙인다.
두 번째 호출은 카운터를 2 로 늘린다.
레코드는 `{'id': ..., **data}` 로 만들어 `id` 가 먼저 들어가고, 사전은 넣은 차례를 지키므로 `id` 가 맨 앞에 찍힌다.
`query('users', active=True)` 는 `active` 가 `True` 인 둘을 모두 남긴다.
근거: 2-summary 「동작 방식 (6)」 · 「구현 세부사항 대 언어 보장」.

### 2. 1번은 이메일만 바뀌고, 2번이 지워져 1번만 남는다

**출력**

```text
Update:
  {'id': 1, 'name': 'Alice', 'email': 'alice_new@ex.com', 'active': True}

Delete:
  삭제 성공: True
  남은 사용자: [{'id': 1, 'name': 'Alice', 'email': 'alice_new@ex.com', 'active': True}]
```

**왜 그런가**
`update` 는 `id` 가 1 인 사전에 `dict.update` 를 해 `email` 만 덮어쓰고 그 사전을 돌려준다.
`delete` 는 `id` 가 2 인 레코드를 `pop` 하고 `True` 를 돌려준다.
조건 없는 `query('users')` 는 남은 리스트 전체를 돌려준다.
근거: 2-summary 「동작 방식 (6)」.

### 3. `u1` 에도 고친 이메일이 보이고, 지운 2번의 `update` 는 `None`

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
{'id': 1, 'name': 'Alice', 'email': 'alice_new@ex.com', 'active': True}
None
```

**왜 그런가**
`create` 가 돌려준 `u1` 은 저장소 리스트에 들어간 사전과 같은 객체다.
`update` 가 그 사전을 제자리에서 고쳤으므로 `u1` 으로 보아도 `alice_new@ex.com` 이 보인다.
`id` 2 는 이미 지워져 `update` 의 반복문이 아무것도 찾지 못하고 `None` 을 돌려준다.
근거: 2-summary 「동작 방식 (6)」 · 「어디서 틀리나 8」.

### 4. 함수 자체를 넘겨야 행마다 그때의 시각이 들어간다

괄호 없이 넘기면 SQLAlchemy 가 행을 넣을 때마다 그 함수를 불러 그 순간의 시각을 쓴다.
괄호를 붙이면 클래스를 읽는 순간 한 번 불린 값이 기본값으로 굳어, 그 뒤 모든 행이 같은 시각을 받는다.
`onupdate=datetime.utcnow` 도 같은 까닭으로 함수를 넘긴다.
근거: 2-summary 「동작 방식 (1)」 · 「어디서 틀리나 2」.

### 5. `user.orders` 가 리스트가 아니라 쿼리 객체이기 때문이다

`lazy='dynamic'` 관계는 결과 대신 아직 실행하지 않은 쿼리 객체를 돌려준다.
쿼리 객체는 조건을 이어 붙여도 쌓이기만 하므로 `.filter(...)` · `.order_by(...)` 를 더 붙인 뒤 `.all()` 같은 실행 메서드로 결과를 꺼낸다.
근거: 2-summary 「동작 방식 (2)」 · 「동작 방식 (4)」 · 「어디서 틀리나 3」.

### 6. 외래 키 하나는 값을 하나만 담기 때문이다 — 중간 테이블을 `secondary` 로 넘긴다

`orders` 에 상품 외래 키를 두면 주문 하나가 상품 하나밖에 못 가리키고, 반대도 마찬가지다.
그래서 (주문 id, 상품 id) 짝을 행으로 담는 중간 테이블 `order_items` 를 `db.Table` 로 만든다.
`secondary=` 에는 그 중간 테이블 객체(`order_items`)나 테이블 이름 문자열(`'product_tags'`)을 넘긴다.
근거: 2-summary 「동작 방식 (3)」.

### 7. 가리킨 클래스와 중간 테이블의 정의가 빠져 있다

`relationship` 의 `'Profile'` · `'Tag'` 와 `secondary='product_tags'` 는 이름으로만 가리키고, 그 이름은 나중에 찾는다.
발췌 코드에는 `Profile` · `Tag` 클래스도, `product_tags` 테이블도 정의되어 있지 않다.
그래서 관계를 설정하는 단계에서 이름을 찾지 못해 실패한다(정확한 시점과 메시지는 확인 필요).
근거: 2-summary 「동작 방식 (2)」 · 「어디서 틀리나 4」.

### 8. `filter_by` 와 같은 의미다 — SQL 생성과 세션 · `commit` 단계가 없다

`**filters` 의 「키 = 값」 조건만 다루므로 `filter_by(active=True)` 에 해당한다.
진짜 SQLAlchemy 는 조건을 SQL 로 옮겨 데이터베이스에 보내고, 변경은 세션에 모았다가 `commit()` 때 확정한다.
`InMemoryDB` 는 호출 즉시 파이썬 사전과 리스트를 바꾼다.
근거: 2-summary 「동작 방식 (4)」 · 「동작 방식 (6)」.

### 9. 자동 생성된 파일이 의도와 다를 수 있기 때문이다

`flask db migrate` 는 모델과 데이터베이스를 비교해 파일을 만들 뿐, 의도를 정확히 읽는다는 보장이 없다.
`upgrade` 는 그 파일을 실제 데이터베이스에 적용하므로, 적용 전에 사람이 읽고 고쳐야 한다.
근거: 2-summary 「동작 방식 (5)」 · 「어디서 틀리나 1」 · 「구현 세부사항 대 언어 보장」.

### 10. 데이터베이스 제품과 그 설정이 정한다

원본 주석은 「기본 READ COMMITTED」라고 단정하지만, 격리 수준의 기본값은 SQLAlchemy 가 아니라 데이터베이스 쪽이 정한다.
제품마다 기본값이 다를 수 있으므로 그 주석을 일반 규칙으로 믿으면 안 된다(제품별 값은 확인 필요).
근거: 2-summary 「어디서 틀리나 7」 · 「구현 세부사항 대 언어 보장」.

## 실습 정답

### 실습 1. Flask-SQLAlchemy 패턴 안내서와 인메모리 ORM 데모 만들기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1단계 — 가져오기 | `from datetime import datetime` · `from typing import List, Optional` |
| 2단계 — `User` 모델 안내문 | `print("=== 1. 모델 정의 ===")` 와 `class User(db.Model)` 를 담은 `print("""...""")` |
| 3단계 — 관계 안내문 | `print("=== 2. 관계 정의 ===")` 와 `order_items` · `Product` · `Order` · `Category` 를 담은 문자열 |
| 4단계 — CRUD 안내문 | `print("=== 3. CRUD 쿼리 패턴 ===")` 와 `# Create` ~ `# 일괄 삭제` 문자열 |
| 5단계 — 마이그레이션 안내문 | `print("=== 4. Flask-Migrate (Alembic) ===")` 와 `flask db ...` 문자열 |
| 6단계 — `InMemoryDB` | `__init__`(`tables` · `auto_id`) · `create` · `query` · `update` · `delete` |
| 7단계 — 데모 | `db = InMemoryDB()` 뒤 `u1` · `u2` · `active` · `updated` · `result` 와 각 `print` |
| 8단계 — 핵심 정리 | `print("\n=== 핵심 정리 ===")` 아래 다섯 `print` |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`python/python-web-deep/reference/flask-sqlalchemy.py`

```python
# [웹 프레임워크 심화] Flask-SQLAlchemy: 모델과 관계
# 설명: Flask-SQLAlchemy 모델 정의, 관계(1:N, M:N), 마이그레이션
# 팁: Flask-SQLAlchemy는 db.Model을 상속하여 모델을 정의하고, db.relationship으로 관계를 설정한다. lazy='dynamic'은 쿼리 객체를 반환하여 추가 필터링이 가능하다. Flask-Migrate(Alembic)로 스키마 변경을 코드로 관리하며, 마이그레이션 파일은 반드시 리뷰한다.

"""Flask-SQLAlchemy: 모델 정의, 관계, 쿼리"""
# 날짜/시간: 모델의 created_at, updated_at 기본값
from datetime import datetime
# 타입 힌트
from typing import List, Optional

# === SQLAlchemy 모델 패턴 (순수 Python 시뮬레이션 + 실제 코드) ===

# === 1. 모델 정의 ===
print("=== 1. 모델 정의 ===")
# db.Model: 선언형 베이스. __tablename__으로 테이블명 명시
# nullable=False: NOT NULL 제약, unique=True: UNIQUE 인덱스
# default vs onupdate: 생성 시 vs 수정 시 자동 갱신
print("""
from app.extensions import db
from datetime import datetime

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 관계: 1:N (User -> Orders)
    orders = db.relationship('Order', backref='customer', lazy='dynamic')
    # 관계: 1:1 (User -> Profile)
    profile = db.relationship('Profile', backref='user', uselist=False)

    def __repr__(self):
        return f'<User {self.username}>'

    def set_password(self, password):
        from werkzeug.security import generate_password_hash
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        from werkzeug.security import check_password_hash
        return check_password_hash(self.password_hash, password)
""")

# === 2. 관계 (1:N, M:N) ===
print("=== 2. 관계 정의 ===")
# M:N: 중간 테이블(association table)로 표현, secondary로 지정
# 자기참조: remote_side로 부모 컬럼 명시 (트리/계층 구조)
print("""
# M:N 중간 테이블
order_items = db.Table('order_items',
    db.Column('order_id', db.Integer, db.ForeignKey('orders.id')),
    db.Column('product_id', db.Integer, db.ForeignKey('products.id')),
    db.Column('quantity', db.Integer, default=1),
)

class Product(db.Model):
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    stock = db.Column(db.Integer, default=0)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))

    # 관계
    category = db.relationship('Category', backref='products')
    tags = db.relationship('Tag', secondary='product_tags', backref='products')

    @property
    def is_available(self):
        return self.stock > 0

class Order(db.Model):
    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')
    total = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # M:N 관계
    products = db.relationship('Product', secondary=order_items, backref='orders')

class Category(db.Model):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('categories.id'))  # 자기참조

    children = db.relationship('Category', backref=db.backref('parent', remote_side=[id]))
""")

# === 3. CRUD 쿼리 패턴 ===
print("=== 3. CRUD 쿼리 패턴 ===")
# session: Unit of Work — 트랜잭션 단위로 변경 추적
# commit() = COMMIT, rollback() = ROLLBACK (트랜잭션 격리: 기본 READ COMMITTED)
# update/delete를 .filter().update()로 호출하면 N+1 없이 단일 SQL로 일괄 처리
print("""
# Create
new_user = User(username='alice', email='alice@ex.com')
new_user.set_password('secret123')
db.session.add(new_user)
db.session.commit()

# Read
user = User.query.get(1)                               # PK로 조회
user = User.query.filter_by(username='alice').first()   # 조건 조회
user = User.query.filter_by(username='alice').first_or_404()  # 없으면 404
users = User.query.filter(User.is_active == True).all() # 필터
users = User.query.order_by(User.created_at.desc()).limit(10).all()

# 고급 필터링
from sqlalchemy import or_, and_, func

products = Product.query.filter(
    and_(
        Product.price.between(10000, 50000),
        or_(Product.name.contains('Python'), Product.name.contains('Flask')),
        Product.stock > 0
    )
).order_by(Product.price.asc()).all()

# 집계
from sqlalchemy import func
stats = db.session.query(
    func.count(Product.id),
    func.avg(Product.price),
    func.sum(Product.stock)
).first()

# 그룹화
category_counts = db.session.query(
    Category.name,
    func.count(Product.id).label('count')
).join(Product).group_by(Category.name).all()

# Update
user.email = 'new@example.com'
db.session.commit()

# 일괄 업데이트
User.query.filter(User.is_active == False).update({'is_active': True})
db.session.commit()

# Delete
db.session.delete(user)
db.session.commit()

# 일괄 삭제
Order.query.filter(Order.status == 'cancelled').delete()
db.session.commit()
""")

# === 4. 마이그레이션 ===
print("=== 4. Flask-Migrate (Alembic) ===")
# Alembic: 스키마 버전 관리 도구. 모델 변경을 Python 코드로 추적
# 실무: migrate 파일을 반드시 리뷰 (자동 생성된 SQL이 의도와 다를 수 있음)
print("""
# 초기 설정
flask db init          # migrations/ 디렉토리 생성
flask db migrate -m "Initial migration"  # 마이그레이션 파일 생성
flask db upgrade       # 데이터베이스에 적용
flask db downgrade     # 롤백
flask db history       # 마이그레이션 이력

# 모델 변경 후
# 1. 모델 수정 (컬럼 추가 등)
# 2. flask db migrate -m "Add phone field to User"
# 3. 생성된 마이그레이션 파일 검토
# 4. flask db upgrade
""")

# === 5. 실행 가능한 데모 ===
print("=== 5. ORM 패턴 데모 ===")

# 인메모리 DB: SQLAlchemy 동작을 단순화한 시뮬레이션
class InMemoryDB:
    def __init__(self):
        # 테이블별 레코드 리스트
        self.tables = {}
        # 자동 증가 PK 카운터
        self.auto_id = {}

    # CREATE: 테이블이 없으면 생성하고 ID 자동 증가
    def create(self, table: str, data: dict) -> dict:
        if table not in self.tables:
            self.tables[table] = []
            self.auto_id[table] = 0
        self.auto_id[table] += 1
        record = {'id': self.auto_id[table], **data}
        self.tables[table].append(record)
        return record

    # READ: 단순 필터 (실제 SQLAlchemy는 SQL 생성)
    def query(self, table: str, **filters) -> list:
        records = self.tables.get(table, [])
        for key, value in filters.items():
            records = [r for r in records if r.get(key) == value]
        return records

    # UPDATE: PK로 찾아서 dict.update
    def update(self, table: str, record_id: int, data: dict) -> dict:
        for r in self.tables.get(table, []):
            if r['id'] == record_id:
                r.update(data)
                return r
        return None

    # DELETE: PK로 찾아서 제거
    def delete(self, table: str, record_id: int) -> bool:
        records = self.tables.get(table, [])
        for i, r in enumerate(records):
            if r['id'] == record_id:
                records.pop(i)
                return True
        return False

# 데모 DB 인스턴스
db = InMemoryDB()

# CRUD 데모
print("Create:")
u1 = db.create('users', {'name': 'Alice', 'email': 'alice@ex.com', 'active': True})
u2 = db.create('users', {'name': 'Bob', 'email': 'bob@ex.com', 'active': True})
print(f"  {u1}")
print(f"  {u2}")

print("\nRead:")
# active=True 필터링 (filter_by와 동일 의미)
active = db.query('users', active=True)
print(f"  활성 사용자: {len(active)}명")

print("\nUpdate:")
# id=1 사용자의 email 변경
updated = db.update('users', 1, {'email': 'alice_new@ex.com'})
print(f"  {updated}")

print("\nDelete:")
result = db.delete('users', 2)
print(f"  삭제 성공: {result}")
print(f"  남은 사용자: {db.query('users')}")

print("\n=== 핵심 정리 ===")
print("db.Model: 모델 클래스 상속")
print("db.relationship: 관계 정의 (1:1, 1:N, M:N)")
print("db.session: add/commit/rollback/delete")
print("Query API: filter/filter_by/order_by/limit/offset")
print("Flask-Migrate: 스키마 변경을 코드로 관리")
```

**실행 결과** — 원본 예제(`component`)를 실제로 돌린 출력이다. 환경 `Python 3.12.3` · 2026-11-28 · exit 0 · 두 번 돌려 출력이 같았다.

````text
$ python3 -I example.py
=== 1. 모델 정의 ===

from app.extensions import db
from datetime import datetime

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 관계: 1:N (User -> Orders)
    orders = db.relationship('Order', backref='customer', lazy='dynamic')
    # 관계: 1:1 (User -> Profile)
    profile = db.relationship('Profile', backref='user', uselist=False)

    def __repr__(self):
        return f'<User {self.username}>'

    def set_password(self, password):
        from werkzeug.security import generate_password_hash
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        from werkzeug.security import check_password_hash
        return check_password_hash(self.password_hash, password)

=== 2. 관계 정의 ===

# M:N 중간 테이블
order_items = db.Table('order_items',
    db.Column('order_id', db.Integer, db.ForeignKey('orders.id')),
    db.Column('product_id', db.Integer, db.ForeignKey('products.id')),
    db.Column('quantity', db.Integer, default=1),
)

class Product(db.Model):
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    stock = db.Column(db.Integer, default=0)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))

    # 관계
    category = db.relationship('Category', backref='products')
    tags = db.relationship('Tag', secondary='product_tags', backref='products')

    @property
    def is_available(self):
        return self.stock > 0

class Order(db.Model):
    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')
    total = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # M:N 관계
    products = db.relationship('Product', secondary=order_items, backref='orders')

class Category(db.Model):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('categories.id'))  # 자기참조

    children = db.relationship('Category', backref=db.backref('parent', remote_side=[id]))

=== 3. CRUD 쿼리 패턴 ===

# Create
new_user = User(username='alice', email='alice@ex.com')
new_user.set_password('secret123')
db.session.add(new_user)
db.session.commit()

# Read
user = User.query.get(1)                               # PK로 조회
user = User.query.filter_by(username='alice').first()   # 조건 조회
user = User.query.filter_by(username='alice').first_or_404()  # 없으면 404
users = User.query.filter(User.is_active == True).all() # 필터
users = User.query.order_by(User.created_at.desc()).limit(10).all()

# 고급 필터링
from sqlalchemy import or_, and_, func

products = Product.query.filter(
    and_(
        Product.price.between(10000, 50000),
        or_(Product.name.contains('Python'), Product.name.contains('Flask')),
        Product.stock > 0
    )
).order_by(Product.price.asc()).all()

# 집계
from sqlalchemy import func
stats = db.session.query(
    func.count(Product.id),
    func.avg(Product.price),
    func.sum(Product.stock)
).first()

# 그룹화
category_counts = db.session.query(
    Category.name,
    func.count(Product.id).label('count')
).join(Product).group_by(Category.name).all()

# Update
user.email = 'new@example.com'
db.session.commit()

# 일괄 업데이트
User.query.filter(User.is_active == False).update({'is_active': True})
db.session.commit()

# Delete
db.session.delete(user)
db.session.commit()

# 일괄 삭제
Order.query.filter(Order.status == 'cancelled').delete()
db.session.commit()

=== 4. Flask-Migrate (Alembic) ===

# 초기 설정
flask db init          # migrations/ 디렉토리 생성
flask db migrate -m "Initial migration"  # 마이그레이션 파일 생성
flask db upgrade       # 데이터베이스에 적용
flask db downgrade     # 롤백
flask db history       # 마이그레이션 이력

# 모델 변경 후
# 1. 모델 수정 (컬럼 추가 등)
# 2. flask db migrate -m "Add phone field to User"
# 3. 생성된 마이그레이션 파일 검토
# 4. flask db upgrade

=== 5. ORM 패턴 데모 ===
Create:
  {'id': 1, 'name': 'Alice', 'email': 'alice@ex.com', 'active': True}
  {'id': 2, 'name': 'Bob', 'email': 'bob@ex.com', 'active': True}

Read:
  활성 사용자: 2명

Update:
  {'id': 1, 'name': 'Alice', 'email': 'alice_new@ex.com', 'active': True}

Delete:
  삭제 성공: True
  남은 사용자: [{'id': 1, 'name': 'Alice', 'email': 'alice_new@ex.com', 'active': True}]

=== 핵심 정리 ===
db.Model: 모델 클래스 상속
db.relationship: 관계 정의 (1:1, 1:N, M:N)
db.session: add/commit/rollback/delete
Query API: filter/filter_by/order_by/limit/offset
Flask-Migrate: 스키마 변경을 코드로 관리
````

**풀이 요점**
- 1~4절은 `print("""...""")` 로 찍는 안내문이라, 문자열 첫 줄의 줄바꿈 때문에 절 제목 바로 아래에 빈 줄이 하나 생긴다.
- `create` 는 테이블별 카운터를 따로 두어 `users` 의 `id` 가 1 부터 늘어난다.
- `query` 의 `**filters` 는 `filter_by` 처럼 「키 = 값」만 다루고, 조건이 없으면 내부 리스트를 그대로 돌려준다.
- `update` · `delete` 는 찾지 못했을 때 `None` · `False` 로 결과를 알린다.
- 데모의 `db = InMemoryDB()` 는 이름 `db` 를 새로 묶는다 — 실제 앱에서는 확장 객체를 가리지 않도록 다른 이름을 쓴다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 원본 예제를 `Python 3.12.3` 에서 2회 돌렸다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
