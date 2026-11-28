# python/python-libraries/05 — SQLAlchemy 기본 — 정리 (힌트)

> 출처 — study-site 항목 `python/sqlalchemy-basics`(항목 데이터 `data/python/libraries.json`) · 정답 코드 study-practice `python/python-libraries/reference/sqlalchemy-basics.py`\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).\
> 실행 — 실행하지 않음 — 외부 라이브러리 `sqlalchemy` 가 있어야 도는 예제다 — 그것 없이 만들어 실행하지 않았다.

## 한눈에 — 쉽게 말하면

**SQLAlchemy 는 「파이썬 객체로 말하면 SQL 로 옮겨 주는 통역사」다.**
손님(파이썬 코드)은 「Alice 라는 사람을 장부에 적어 주세요」라고 말한다.
통역사(Session)는 그 말을 받아 적어 두었다가, 손님이 「확정」이라고 하면 장부 관리인(DB)에게 SQL 로 전달한다.
장부 관리인에게 가는 전화선(Engine)은 하나 깔아 두고 여러 번 쓴다.
SQLAlchemy 도 똑같은 구조다.

| 비유 | 실체 |
|---|---|
| 장부 관리인 | 데이터베이스(SQLite · PostgreSQL 등) |
| 전화선 | `Engine` (`create_engine` 으로 만든다) |
| 장부의 양식(칸 이름 · 규칙) | 모델 클래스(`User` · `Product`)와 `Column` |
| 통역사 한 명과의 한 번의 상담 | `Session` 인스턴스 |
| 「확정」이라는 말 | `session.commit()` |

```text
파이썬 객체 ──add──▶ Session(메모 보관) ──commit──▶ Engine ──SQL──▶ DB
   User(...)            pending 상태                연결 풀        INSERT/SELECT...
```

> **ORM** — Object-Relational Mapping. 테이블의 행을 파이썬 객체로, 컬럼을 객체의 속성으로 대응시키는 기법이다.\
> 예: `users` 테이블의 한 행이 `User(id=1, name='Alice', ...)` 객체 하나가 된다.

## 이 주제가 답하려는 질문

1. DB 에 연결하고 테이블을 파이썬 클래스로 정의하려면 무엇이 필요한가?
2. 객체를 만들고(`C`) · 찾고(`R`) · 고치고(`U`) · 지우는(`D`) 일은 각각 어떤 호출로 하나?
3. `Session` 은 왜 따로 있고, 언제 열고 언제 닫나?
4. 편한 방법(벌크 update · `filter_by` · 레거시 `query`)은 어디까지 되고 어디서 함정이 생기나?

> **CRUD** — Create · Read · Update · Delete. 데이터를 다루는 네 가지 기본 작업이다.\
> 예: 사용자 추가 · 목록 조회 · 나이 수정 · 사용자 삭제.

## 동작 방식

### (1) Engine — DB 로 가는 연결의 출발점

**언제 쓰나** — 프로그램이 시작할 때 한 번 만든다.
어느 DB 에 어떻게 붙을지를 URL 문자열 하나로 정한다.

```text
create_engine("sqlite:///:memory:", echo=False)
        │
        ├─ URL 을 읽어 dialect(어느 DB 의 SQL 방언인가)를 고른다
        ├─ connection pool(연결을 모아 두고 다시 쓰는 통)을 준비한다
        └─ echo=True 면 실행되는 SQL 을 로그로 찍는다
        ▼
   engine  (아직 SQL 을 하나도 보내지 않은 상태)
```

- `create_engine` 은 연결 풀과 dialect 를 하나로 감싼 객체를 돌려준다.
- `"sqlite:///:memory:"` 는 파일 없이 메모리에만 있는 SQLite DB 다.
- 인메모리 DB 는 프로세스가 끝나면 사라진다 — 그래서 테스트에 쓰기 좋다.
- 실무에서는 `"postgresql://user:pass@localhost/dbname"` 같은 URL 과 `pool_size=5` 같은 풀 옵션을 준다.
- `echo=True` 로 바꾸면 SQLAlchemy 가 내보내는 SQL 을 눈으로 확인할 수 있다.

> **dialect** — 특정 DB 종류의 SQL 문법 · 동작 차이를 맡는 SQLAlchemy 의 부품이다.\
> 예: SQLite 용 dialect 와 PostgreSQL 용 dialect 가 따로 있다.

> **connection pool** — DB 연결을 미리 열어 두고 빌려 쓰고 돌려받는 통이다.\
> 예: `pool_size=5` 면 연결을 다섯 개까지 모아 둔다.

### (2) 모델 정의 — 클래스 하나 = 테이블 하나

**언제 쓰나** — 테이블의 모양(컬럼 · 타입 · 제약)을 파이썬 코드로 적을 때 쓴다.

```text
Base = declarative_base()
class User(Base):                       ─┐
    __tablename__ = "users"              │  Base 를 상속했으므로
    id    = Column(Integer, primary_key) │  Base.metadata 에
    name  = Column(String(100), nullable=False)  "users" 테이블 정보가
    email = Column(String(200), unique=True)     등록된다
    age   = Column(Integer, default=0)   │
    created_at = Column(DateTime, default=datetime.now) ─┘
        ▼
Base.metadata.tables  →  {"users": ..., "products": ...}
```

- `declarative_base()` 가 만든 `Base` 를 상속해야 SQLAlchemy 가 그 클래스를 추적한다.
- `__tablename__` 으로 실제 테이블 이름을 정한다 — 원본 주석에 따르면 적지 않으면 자동 추론이 되지 않는다.
- `Column(타입, 옵션...)` 하나가 컬럼 하나다.
- `primary_key=True` 는 기본 키(PK)다. `autoincrement` 의 실제 동작은 백엔드(SQLite · MySQL · Postgres)마다 다르다.
- `nullable=False` 는 NOT NULL 제약이다.
- `unique=True` 는 UNIQUE 제약이다 — 중복 값을 넣으면 `IntegrityError` 가 난다.
- `default=0` 은 **파이썬 쪽** 기본값이다. DB 서버 쪽 기본값은 `server_default` 로 따로 준다.
- `default=datetime.now` 처럼 **호출 가능한 것(함수)** 을 주면 행을 넣을 때마다 그 함수가 불린다.
- `__repr__` 은 객체를 `print` 할 때 보이는 문자열을 정한다 — 디버깅용이다.

> **PK (기본 키)** — 테이블에서 행 하나를 유일하게 가리키는 컬럼이다.\
> 예: `users.id` 가 1 인 행은 하나뿐이다.

> **metadata** — 등록된 테이블 · 컬럼 정보를 모아 둔 SQLAlchemy 의 객체다.\
> 예: `Base.metadata.tables.keys()` 로 테이블 이름 목록을 얻는다.

### (3) create_all — 테이블 실제로 만들기

**언제 쓰나** — 모델을 다 정의한 뒤, DB 에 테이블이 없을 때 한 번 부른다.

```text
Base.metadata.create_all(engine)
        │
        ├─ metadata 에 등록된 테이블을 하나씩 본다
        ├─ DB 에 없으면 CREATE TABLE 을 보낸다
        └─ 이미 있으면 건너뛴다
        ▼
   DB 안에 users · products 테이블
```

- 등록된 모든 테이블을 한 번에 만든다.
- 이미 있는 테이블은 건너뛴다(skip) — 컬럼을 바꿔 주는 도구는 아니다.
- `Base.metadata.tables` 는 dict 꼴이라 `.keys()` 로 이름을 꺼낼 수 있다.

### (4) Session — 한 번의 작업 단위, with 로 연다

**언제 쓰나** — 객체를 넣고 · 읽고 · 고치고 · 지우는 모든 일은 Session 을 거친다.

```text
SessionLocal = sessionmaker(bind=engine)   ← Session 을 찍어 내는 「틀(클래스)」
        │
with SessionLocal() as session:            ← 호출해서 인스턴스 하나를 만든다
        │  add / query / delete ...
        │  commit()  → 트랜잭션 확정
        ▼
with 블록을 벗어나면 session.close()
```

- `sessionmaker(bind=engine)` 은 엔진에 묶인 Session **클래스(팩토리)** 를 돌려준다.
- 그래서 `SessionLocal` 자체는 세션이 아니다 — `SessionLocal()` 처럼 **호출해야** 인스턴스가 생긴다.
- 인스턴스 하나가 하나의 작업 단위(트랜잭션 단위)다.
- `with` 문으로 열면 블록이 끝날 때 자동으로 `close` 된다.
- 예제는 CREATE · READ · UPDATE · DELETE 마다 **새 세션**을 연다.

> **Session** — 객체의 변경을 모아 두었다가 DB 와 주고받는 작업 단위(unit of work)다.\
> 예: `session.add(user)` 한 뒤 `session.commit()` 하면 INSERT 가 나간다.

> **트랜잭션** — 「전부 반영하거나 전부 취소하는」 한 묶음의 DB 작업이다.\
> 예: `commit()` 이 그 묶음을 확정한다.

### (5) CREATE — add 로 등록하고 commit 으로 보낸다

**언제 쓰나** — 새 행을 넣을 때.

```text
user1 = User(name="Alice", ...)   ← 파이썬 객체일 뿐. DB 에는 없다. id 는 None
session.add(user1)                ← 세션의 pending 목록에 올린다
session.add_all([user2, user3])   ← 여럿을 한 번에 올린다
session.commit()                  ← flush(INSERT 실행) + 트랜잭션 확정
        ▼
user1.id 가 채워진다 (autoincrement 로 DB 가 정한 값)
```

- 모델 인스턴스를 만든 것만으로는 DB 에 아무것도 가지 않는다.
- `add` 는 객체 하나를, `add_all` 은 리스트를 세션의 **pending** 상태로 올린다.
- `commit` 은 쌓인 변경을 **flush**(실제 SQL 실행)하고 트랜잭션을 확정한다.
- commit 이후에는 PK 가 채워져 있다 — 그래서 그 뒤 `print(user1)` 은 `id=` 자리에 숫자가 보인다.
- 커밋 전에는 아직 INSERT 가 없었으므로 `id` 는 비어 있다(`None`).

> **flush** — 세션에 쌓인 변경을 SQL 로 DB 에 보내는 일이다. 트랜잭션 확정과는 다르다.\
> 예: `commit()` 은 안에서 flush 를 먼저 한다.

> **pending** — 세션에 등록됐지만 아직 DB 에 INSERT 되지 않은 객체의 상태다.\
> 예: `add` 직후의 `user1`.

### (6) READ — query 로 찾는 일곱 가지 꼴

**언제 쓰나** — 조건 · 정렬 · 개수 등으로 행을 꺼낼 때.

```text
session.query(User)                      → SELECT ... FROM users
   .all()                                → 결과 전부를 리스트로
   .filter(User.name == "Alice")         → WHERE name = 'Alice'   (SQL 표현식)
   .filter_by(name="Bob")                → WHERE name = 'Bob'     (키워드, == 만)
   .filter(User.age >= 30, User.name != "Charlie") → WHERE ... AND ...
   .order_by(User.age.desc()).limit(2)   → ORDER BY age DESC LIMIT 2
   .first()                              → 맨 앞 한 행 또는 None
   .count()                              → SELECT COUNT(*)
session.get(User, 1)                     → PK 로 바로 찾기
```

- `query(User).all()` 은 모든 행을 객체 리스트로 준다.
- `filter` 는 `User.name == "Alice"` 같은 **SQL 표현식**을 받는다 — 컬럼 속성에 `==` · `>=` · `!=` 를 쓰면 파이썬 불리언이 아니라 WHERE 조건이 만들어진다.
- `filter_by` 는 `name="Bob"` 같은 키워드 인자를 받는다 — **같다(==) 비교만** 된다.
- `filter` 에 조건을 콤마로 나열하면 **AND** 로 묶인다. OR 가 필요하면 `or_(...)` 를 쓴다.
- `first()` 는 0 행 또는 1 행을 준다 — 찾은 게 없으면 `None` 이다.
- `session.get(User, 1)` 은 PK 로 바로 찾는다. 세션의 **아이덴티티 맵**에 이미 있으면 그것을 쓴다.
- `order_by(컬럼.desc()).limit(n)` 은 내림차순 상위 n 개다.
- `count()` 는 `COUNT(*)` 쿼리를 보낸다.
- 예제의 `session.query(...)` 는 1.x 시절의 꼴이다. 2.0 에서 권장하는 꼴은 `session.scalars(select(User)).all()` 같은 `select()` 스타일이다.

> **아이덴티티 맵** — 세션이 「이 PK 의 행 = 이 객체」를 기억해 두는 표다.\
> 예: 같은 세션에서 `get(User, 1)` 을 두 번 하면 같은 객체가 돌아온다.

### (7) UPDATE — 속성 할당 vs 벌크 update

**언제 쓰나** — 행 하나를 객체로 고칠 때는 속성 할당, 조건에 맞는 여러 행을 한 번에 바꿀 때는 벌크 update.

```text
[속성 할당]
user = query(...).filter_by(name="Alice").first()   ← 객체를 불러온다
user.age = 31                                       ← 세션이 변경을 기억한다
session.commit()                                    ← UPDATE 가 자동으로 나간다

[벌크 update]
query(User).filter(User.age < 30).update({"age": 30})  ← 객체를 불러오지 않고
session.commit()                                        UPDATE 한 번
```

- 속성 할당: 불러온 객체의 속성을 바꾸고 `commit` 하면 세션이 바뀐 것을 찾아 UPDATE 를 만든다.
- 벌크 update: `query(...).update(dict)` 는 객체를 하나도 불러오지 않고 UPDATE 한 번을 보낸다.
- 벌크 쪽은 빠르지만 **ORM 이벤트를 우회한다** — 객체 단위로 걸어 둔 처리가 불리지 않는다.
- 벌크 변경도 `commit` 해야 확정된다.

### (8) DELETE — delete 후 commit

**언제 쓰나** — 행을 지울 때.

```text
user = query(...).filter_by(name="Charlie").first()
session.delete(user)     ← 삭제 예정으로 표시
session.commit()         ← 실제 DELETE 실행
query(User).all()        ← Charlie 가 빠진 목록
```

- `session.delete(obj)` 는 객체를 삭제 예정으로 표시만 한다.
- `commit` 해야 DELETE 가 실제로 나간다.
- 지운 뒤 같은 세션에서 다시 조회하면 그 행은 빠져 있다.

## 문법 — 형태와 규칙

```python
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker

engine = create_engine("sqlite:///:memory:", echo=True)
Base = declarative_base()

class Book(Base):
    __tablename__ = "books"
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(100), nullable=False)

Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine)

with SessionLocal() as s:
    s.add(Book(title="Dune"))
    s.commit()
    print(s.query(Book).filter_by(title="Dune").first())
```

- 순서는 **engine → Base → 모델 클래스 → create_all → sessionmaker → with 세션**이다.
- 모델 클래스는 `Base` 를 상속하고 `__tablename__` 을 가진다.
- 컬럼은 `Column(타입, primary_key= / nullable= / unique= / default= / autoincrement=)` 로 쓴다.
- 쓰기(`add` · 속성 변경 · `delete` · 벌크 `update`)는 `commit()` 으로 확정한다.
- 조회 끝맺음: `.all()` 은 리스트, `.first()` 는 객체 또는 `None`, `.count()` 는 정수다.

| 쓰인 이름 | 하는 일 |
|---|---|
| `create_engine(url, echo=)` | 연결 풀 + dialect 를 가진 엔진 |
| `declarative_base()` | 모델 베이스 클래스 팩토리 (2.0 에서는 `DeclarativeBase` 권장) |
| `Base.metadata.create_all(engine)` | 등록된 테이블 생성, 있으면 건너뜀 |
| `sessionmaker(bind=engine)` | Session 클래스(팩토리) |
| `session.add` / `add_all` | 객체를 pending 으로 등록 |
| `session.commit()` | flush + 트랜잭션 확정 |
| `query(M).filter(...)` / `filter_by(...)` | WHERE 조건 |
| `order_by(col.desc())` · `limit(n)` | 정렬 · 개수 제한 |
| `session.get(M, pk)` | PK 조회 |
| `query(...).update(dict)` | 벌크 UPDATE |
| `session.delete(obj)` | 삭제 예정 표시 |
| `String(n)` · `Integer` · `Float` · `DateTime` | 컬럼 타입 (화폐는 `Float` 대신 `Numeric` 권장) |

## 어디서 틀리나

### 1. `SessionLocal` 을 세션으로 착각한다
`sessionmaker` 가 돌려주는 것은 클래스다.
`SessionLocal.add(...)` 처럼 쓰면 안 되고, `SessionLocal()` 로 인스턴스를 만든 뒤 써야 한다.

### 2. `commit` 을 빼먹는다
`add` · 속성 변경 · `delete` · 벌크 `update` 모두 `commit` 전에는 확정되지 않는다.
commit 전에는 새 객체의 `id` 도 비어 있다.

### 3. 세션을 닫지 않는다 — `with` 로 열어라
팁: Session 은 `with` 문으로 쓰면 자동으로 `close` 된다.
원본 주석은 「자동 close(rollback 은 별도)」라고 적는다.

### 4. `filter_by` 로 크기 비교를 하려 한다
`filter_by` 는 키워드 인자라 `==` 만 된다.
`>=` · `!=` · `<` 는 `filter(User.age >= 30)` 처럼 SQL 표현식으로 써야 한다.
여러 조건을 콤마로 쓰면 AND 이고, OR 는 `or_(...)` 다.

### 5. `first()` 의 `None` 을 잊는다
조건에 맞는 행이 없으면 `first()` 는 `None` 을 준다.
그 뒤에 곧바로 `user.age = 31` 을 하면 `None` 에 속성을 넣으려다 에러가 난다.

### 6. 벌크 update 가 ORM 이벤트를 건너뛴다
`query().update(dict)` 는 객체를 불러오지 않으므로 빠르다.
대신 객체 단위의 ORM 이벤트가 불리지 않는다 — 원본 주석이 「함정」이라 부르는 자리다.

### 7. `default` 를 DB 기본값으로 착각한다
`default=` 는 파이썬 쪽에서 INSERT 할 때 채우는 값이다.
DB 테이블 정의에 기본값을 두려면 `server_default` 를 쓴다.
`default=datetime.now` 처럼 함수 자체를 주어야 매번 호출된다 — `datetime.now()` 처럼 괄호를 붙이면 모델을 정의하는 순간의 시각 하나로 굳는다(원본에 근거 없음 — 추론).

### 8. 「2.0 스타일」이라는 제목과 레거시 query
팁: SQLAlchemy 2.0 에서는 `select()` 스타일 쿼리가 권장된다.
그런데 예제 본문은 대부분 `session.query(...)` 를 쓴다 — 이것은 1.x 꼴이다.
`declarative_base` 도 2.0 에서는 `DeclarativeBase` 가 권장된다(원본 주석).
예제가 「2.0 스타일 기본」이라 이름 붙었어도 쓰인 API 는 섞여 있다고 보고 읽어야 한다.

### 9. 돈을 `Float` 로 둔다
`Product.price` 는 `Float` 다.
원본 주석은 화폐에는 `Numeric` 을 권장한다 — 부동소수점은 오차가 생긴다.

### 10. `unique=True` 를 어긴다
같은 `email` 로 두 번 INSERT 하면 `IntegrityError` 가 난다.

### 11. 쓰지 않는 import
예제는 `text` 와 `Session` 을 import 하지만 본문에서 쓰지 않는다.
`text` 는 원시 SQL 실행용, `Session` 은 타입 이름이다 — 예제를 읽을 때 무엇에 쓰였나 찾지 않아도 된다.

### 12. SQL 이 궁금하면 `echo=True`
팁: `echo=True` 로 엔진을 만들면 실제로 실행되는 SQL 을 볼 수 있다.
벌크 update 가 정말 한 번의 UPDATE 인지 같은 것을 확인할 때 쓴다.

### 13. 인메모리 SQLite 는 테스트용이다
팁: `sqlite:///:memory:` 는 테스트에 매우 유용하다.
프로세스가 끝나면 데이터가 사라지므로 실제 데이터 보관에는 쓰지 않는다.

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| 인메모리 DB 는 프로세스가 끝나면 사라진다 | SQLite 의 `:memory:` 동작 |
| `autoincrement` 로 id 가 1, 2, 3 … 으로 채워진다 | DB 백엔드(SQLite · MySQL · Postgres 마다 다름) |
| `unique` 위반 시 `IntegrityError` | DB 가 제약을 거부하고 SQLAlchemy 가 예외로 감싼다 |
| `default=` 는 파이썬 쪽 기본값, `server_default` 는 DB 쪽 | SQLAlchemy 의 설계 |
| `filter(A, B)` 는 AND, `first()` 는 없으면 `None` | SQLAlchemy API |
| 2.0 에서 `select()` · `DeclarativeBase` 권장 | SQLAlchemy 라이브러리 버전 정책(파이썬 언어와 무관) |
| `Base.metadata.tables.keys()` 가 정의한 차례로 나온다 | SQLAlchemy 의 등록 방식 + 파이썬 dict 의 삽입 순서 (확인 필요) |
| `with` 문이 블록 끝에 `close` 를 부른다 | 파이썬 언어(컨텍스트 관리자 규약) + Session 의 `__exit__` 구현 |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 행 하나를 고친다 | 불러와서 속성 할당 → `commit` | 벌크 `update` (이벤트 우회) |
| 조건에 맞는 수천 행을 한 번에 바꾼다 | `query().update(dict)` → `commit` | 하나씩 불러와 할당 |
| 같다 비교 하나 | `filter_by(name=...)` | — |
| 크기 비교 · 같지 않음 · 여러 조건 | `filter(표현식, ...)` · `or_` | `filter_by` |
| PK 를 안다 | `session.get(Model, pk)` | `filter(Model.id == pk).first()` 로 돌아가기 |
| 새 코드를 짠다 | `select()` 스타일 · `DeclarativeBase` | 레거시 `session.query` |
| 단위 테스트 | `sqlite:///:memory:` | 실제 운영 DB |
| 돈 | `Numeric` | `Float` |

## 핵심 문장

1. **Engine 은 연결, 모델은 테이블 양식, Session 은 작업 단위다** — 셋을 만드는 순서는 engine → Base · 모델 → `create_all` → `sessionmaker`.
2. **쓰기는 `commit` 해야 DB 에 간다** — `add` 는 pending 에 올릴 뿐이고, id 는 commit 뒤에 채워진다.
3. **`filter` 는 표현식, `filter_by` 는 `==` 키워드** — 콤마는 AND, OR 는 `or_`.
4. **속성 할당은 객체를 거치고, 벌크 update 는 객체를 건너뛴다** — 빠른 대신 ORM 이벤트가 없다.
5. **Session 은 `with` 로 열고, 새 코드는 2.0 의 `select()` 스타일로 쓴다.**

## 관련 자료

- [sqlalchemy-relationships](../06-sqlalchemy-relationships/2-summary.md)
- `repository` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- 원본: study-site 항목 데이터 `data/python/libraries.json` 의 `sqlalchemy-basics`

## 용어 풀이

- **SQLAlchemy** — 파이썬의 DB 도구 모음. SQL 표현식 층과 ORM 층을 함께 준다.
- **ORM** — 테이블 행 ↔ 파이썬 객체를 대응시키는 기법.
- **Engine** — DB URL 로 만든, 연결 풀과 dialect 를 가진 객체.
- **dialect** — DB 종류별 SQL 차이를 맡는 부품.
- **connection pool** — 연결을 모아 두고 다시 쓰는 통.
- **모델** — `Base` 를 상속해 테이블 하나를 나타내는 클래스.
- **Column** — 모델 안에서 컬럼 하나를 정의하는 객체.
- **metadata** — 등록된 테이블 정보 모음.
- **PK** — 행을 유일하게 가리키는 기본 키.
- **NOT NULL / UNIQUE** — 빈 값 금지 / 중복 금지 제약.
- **Session** — 변경을 모아 DB 와 주고받는 작업 단위.
- **sessionmaker** — Session 클래스를 찍어 내는 팩토리.
- **트랜잭션** — 전부 반영 또는 전부 취소되는 작업 묶음.
- **commit** — 트랜잭션 확정.
- **flush** — 쌓인 변경을 SQL 로 보내는 일.
- **pending** — 등록됐으나 아직 INSERT 전인 상태.
- **아이덴티티 맵** — 세션이 PK ↔ 객체를 기억하는 표.
- **벌크 update** — 객체를 불러오지 않고 UPDATE 한 번으로 여러 행을 바꾸는 일.
- **ORM 이벤트** — 객체 단위 작업에 걸어 두는 후크.
- **CRUD** — 생성 · 조회 · 수정 · 삭제.

## 더 들어가면

- 인메모리 SQLite 는 연결마다 별개의 DB 가 된다. 예제처럼 여러 세션에 걸쳐 데이터가 남으려면 같은 연결을 다시 써야 하는데, SQLAlchemy 가 `:memory:` 에 대해 연결을 재사용하는 풀을 고른다고 알려져 있다. 스레드가 여럿이면 `StaticPool` 을 직접 지정하기도 한다(확인 필요).
- `Session` 의 `expire_on_commit` 기본값이 켜져 있어, commit 뒤 객체 속성을 읽으면 DB 에서 다시 불러온다고 알려져 있다. 세션을 닫은 뒤 만료된 속성을 읽으면 `DetachedInstanceError` 가 날 수 있다(확인 필요).
- `Session.close()` 는 남은 트랜잭션을 정리(롤백)하고 연결을 풀에 돌려준다고 알려져 있다. 원본 주석의 「rollback 은 별도」 → close 가 진행 중 트랜잭션을 롤백하지 않는다는 뜻이라면 의심스럽다(확인 필요).
- 2.0 의 타입 힌트 꼴 모델은 `class Base(DeclarativeBase): pass` 와 `Mapped[int] = mapped_column(primary_key=True)` 로 쓴다(확인 필요).
- 2.0 에서 벌크 갱신은 `session.execute(update(User).where(User.age < 30).values(age=30))` 꼴로 쓴다(확인 필요).
- 테이블 구조 변경(마이그레이션)은 `create_all` 이 아니라 Alembic 같은 도구가 맡는다(확인 필요).
