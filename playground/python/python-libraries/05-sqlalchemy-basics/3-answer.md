# python/python-libraries/05 — SQLAlchemy 기본 — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. `ordered` 는 Charlie → Alice, `result` 는 Alice 하나

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
- `ordered` 는 `[User(id=3, name='Charlie', ...), User(id=1, name='Alice', ...)]` 꼴이다.
- `result` 는 `[User(id=1, name='Alice', ...)]` 꼴이다.
- id 숫자는 넣은 차례대로 1 · 2 · 3 이 붙는다고 가정한 것이다.

**왜 그런가**
- `order_by(User.age.desc())` 는 나이 큰 차례 — 35(Charlie) · 30(Alice) · 25(Bob) — 이고 `limit(2)` 가 앞의 둘만 남긴다.
- `filter` 에 콤마로 쓴 두 조건은 AND 다. age ≥ 30 은 Alice 와 Charlie, 그중 이름이 Charlie 가 아닌 사람은 Alice 뿐이다.
- 근거: 2-summary 「동작 방식 (6)」.

### 2. Alice 와 Bob 이 남고, Bob 은 30

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
- `remaining` 은 Alice · Bob 두 사람이다.
- Bob 의 `age` 는 30 이다.

**왜 그런가**
- 벌크 update 의 조건 `age < 30` 에 걸리는 사람은 Bob(25)뿐이다. Alice 는 이미 31 이다.
- commit 으로 UPDATE 가 확정된 뒤, Charlie 를 `delete` 하고 commit 하면 DELETE 가 나간다.
- 같은 세션에서 다시 `query(User).all()` 하면 지운 Charlie 는 빠져 있다.
- 근거: 2-summary 「동작 방식 (7)」 · 「동작 방식 (8)」.

### 3. 아직 비어 있다 — `None`

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
- `None` 이 보인다.

**왜 그런가**
- 모델 인스턴스를 만들고 `add` 한 것은 세션의 pending 목록에 올린 것뿐이고 INSERT 는 아직 없다.
- PK 는 commit(안의 flush)으로 INSERT 가 나간 뒤 DB 의 autoincrement 결과로 채워진다.
- 근거: 2-summary 「동작 방식 (5)」.

### 4. `sessionmaker` 는 세션이 아니라 세션을 찍어 내는 클래스를 준다

`sessionmaker(bind=engine)` 은 엔진에 묶인 Session **클래스(팩토리)** 를 돌려준다.
호출해야 비로소 작업 단위 하나(트랜잭션 단위)인 세션 인스턴스가 생긴다.
그래서 CRUD 마다 `SessionLocal()` 을 불러 새 세션을 따로 만들 수 있다.
근거: 2-summary 「동작 방식 (4)」 · 「어디서 틀리나 1」.

### 5. 블록이 끝나면 세션이 자동으로 닫힌다

`with` 로 열면 블록을 벗어날 때 `close` 가 자동으로 불린다.
닫는 일을 잊거나 예외로 건너뛰는 일을 막는다.
작업마다 새 세션을 열어 CREATE · READ · UPDATE · DELETE 를 서로 다른 작업 단위로 나눈다.
근거: 2-summary 「동작 방식 (4)」 · 「어디서 틀리나 3」.

### 6. 둘 다 `filter_by` 로는 안 된다

`filter_by` 는 키워드 인자 꼴이라 같다(`==`) 비교만 된다.
「30 이상」은 `filter(User.age >= 30)` 처럼 SQL 표현식으로 쓴다.
「A 또는 B」는 `or_(...)` 로 쓴다 — 콤마로 나열하면 AND 가 된다.
근거: 2-summary 「동작 방식 (6)」 · 「어디서 틀리나 4」.

### 7. 속도를 얻고 ORM 이벤트를 잃는다

벌크 update 는 객체를 불러오지 않고 UPDATE 한 번으로 여러 행을 바꾸니 빠르다.
대신 객체를 거치지 않으므로 객체 단위로 걸린 ORM 이벤트가 불리지 않는다.
속성 할당은 객체를 불러와 바꾸고 commit 하면 세션이 바뀐 것을 찾아 UPDATE 를 만든다.
둘 다 `commit` 해야 확정되는 것은 같다.
근거: 2-summary 「동작 방식 (7)」 · 「어디서 틀리나 6」.

### 8. `None` 에 속성을 넣으려다 에러가 난다

`first()` 는 맞는 행이 없으면 `None` 을 준다.
`None.age = 31` 은 파이썬에서 속성 오류가 된다.
조회 결과가 `None` 인지 먼저 확인해야 한다.
근거: 2-summary 「어디서 틀리나 5」.

### 9. `session.scalars(select(User)).all()` · `DeclarativeBase`

2.0 에서 권장하는 꼴은 `select()` 스타일이다 — 예: `session.scalars(select(User)).all()`.
모델 베이스는 `declarative_base()` 대신 `DeclarativeBase` 가 권장된다.
예제는 제목이 「2.0 스타일」이지만 `session.query` 라는 1.x 꼴이 섞여 있다.
근거: 2-summary 「동작 방식 (6)」 · 「어디서 틀리나 8」.

### 10. 파이썬 쪽에서 채우고, SQL 은 `echo=True` 로 본다

`default=0` 은 파이썬 쪽 기본값이다 — SQLAlchemy 가 INSERT 할 때 값을 채운다.
DB 테이블 정의에 기본값을 두려면 `server_default` 를 쓴다.
실제로 나가는 SQL(INSERT 안의 `age` 값 등)을 보려면 엔진을 `echo=True` 로 만든다.
근거: 2-summary 「동작 방식 (1)」 · 「동작 방식 (2)」 · 「어디서 틀리나 7」 · 「어디서 틀리나 12」.

## 실습 정답

### 실습 1. 인메모리 SQLite 로 사용자 CRUD 한 바퀴

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. 인메모리 엔진, echo 끔 | `create_engine("sqlite:///:memory:", echo=False)` |
| 2. Base | `Base = declarative_base()` |
| 3. User 모델 | `class User(Base)` · `__tablename__ = "users"` · `Column(... primary_key=True, autoincrement=True)` · `nullable=False` · `unique=True` · `default=0` · `default=datetime.now` |
| 4. Product 모델 | `class Product(Base)` · `__tablename__ = "products"` · `Float, nullable=False` · `stock ... default=0` |
| 5. `__repr__` | `User.__repr__` · `Product.__repr__` |
| 6. 테이블 생성 · 이름 목록 | `Base.metadata.create_all(engine)` · `list(Base.metadata.tables.keys())` |
| 7. 세션 팩토리 | `SessionLocal = sessionmaker(bind=engine)` |
| 8. 세 사용자 등록 · commit | `session.add(user1)` · `session.add_all([user2, user3])` · `session.commit()` |
| 9. 생성 결과 출력 | `print(f"생성: {user1}")` 등 |
| 10. 전체 · filter · filter_by · get | `query(User).all()` · `filter(User.name == "Alice").first()` · `filter_by(name="Bob").first()` · `session.get(User, 1)` |
| 11. 복합 조건 | `filter(User.age >= 30, User.name != "Charlie").all()` |
| 12. 상위 2 · 개수 | `order_by(User.age.desc()).limit(2).all()` · `query(User).count()` |
| 13. Alice 수정 | `user.age = 31` · `session.commit()` |
| 14. 벌크 update | `query(User).filter(User.age < 30).update({"age": 30})` · `session.commit()` |
| 15. Charlie 삭제 | `session.delete(user)` · `session.commit()` |
| 16. 남은 사용자 | `remaining = session.query(User).all()` |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`python/python-libraries/reference/sqlalchemy-basics.py`

```python
# [주요 라이브러리] SQLAlchemy 기본
# 설명: engine, Session, declarative_base, 기본 CRUD 작업
# 팁: SQLAlchemy 2.0에서는 select() 스타일 쿼리가 권장된다. Session은 with문으로 사용하면 자동 close. echo=True로 실행되는 SQL을 확인할 수 있다. 인메모리 SQLite(sqlite:///:memory:)는 테스트에 매우 유용하다.

# SQLAlchemy 2.0 스타일 기본
# create_engine: DB 연결 풀, Column/타입: 스키마 정의 도구, text: 원시 SQL 실행
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, text
# declarative_base: ORM 베이스 클래스 팩토리(2.0에서는 DeclarativeBase 권장)
# sessionmaker: Session 팩토리, Session: 단위 작업(unit of work)
from sqlalchemy.orm import declarative_base, sessionmaker, Session
# 기본 타임스탬프 용도
from datetime import datetime

# === Engine 생성 (SQLite 인메모리) ===
# create_engine은 connection pool과 dialect를 캡슐화
# 인메모리 SQLite는 프로세스가 끝나면 사라짐(테스트 용)
engine = create_engine(
    "sqlite:///:memory:",  # 인메모리 DB (실행 가능!)
    echo=False              # SQL 로그 출력 여부
)
# 실무에서는:
# engine = create_engine("postgresql://user:pass@localhost/dbname", pool_size=5)

# === 모델 정의 ===
# Base 클래스를 상속해야 SQLAlchemy가 메타데이터를 추적
Base = declarative_base()

# User 테이블 모델 클래스 정의
class User(Base):
    # 실제 테이블명을 지정(미지정 시 자동 추론 안 됨)
    __tablename__ = "users"

    # primary_key=True가 PK. autoincrement는 SQLite/MySQL/Postgres 등 백엔드별 상이
    id = Column(Integer, primary_key=True, autoincrement=True)
    # nullable=False는 NOT NULL 제약
    name = Column(String(100), nullable=False)
    # unique=True는 UNIQUE 제약(중복 시 IntegrityError)
    email = Column(String(200), unique=True, nullable=False)
    # default는 파이썬 레벨 기본값(서버 기본값은 server_default)
    age = Column(Integer, default=0)
    # 생성 시각 자동 기록(callable을 default로 주면 매번 호출됨)
    created_at = Column(DateTime, default=datetime.now)

    # repr은 디버깅 출력에 유용
    def __repr__(self):
        return f"User(id={self.id}, name='{self.name}', email='{self.email}')"

# Product 테이블 모델 클래스
class Product(Base):
    # 테이블명
    __tablename__ = "products"

    # PK
    id = Column(Integer, primary_key=True, autoincrement=True)
    # 상품명(필수)
    name = Column(String(200), nullable=False)
    # 가격(부동소수점 - 화폐는 Numeric 권장)
    price = Column(Float, nullable=False)
    # 재고
    stock = Column(Integer, default=0)

    # 디버깅 출력
    def __repr__(self):
        return f"Product(id={self.id}, name='{self.name}', price={self.price})"

# === 테이블 생성 ===
# metadata.create_all은 등록된 모든 테이블을 한 번에 생성(이미 있으면 skip)
Base.metadata.create_all(engine)
# 생성 결과 안내 출력
print("=== 테이블 생성 완료 ===")
# metadata.tables는 dict 형태로 등록된 테이블 정보 보유
print(f"생성된 테이블: {list(Base.metadata.tables.keys())}")

# === Session 팩토리 ===
# bind=engine으로 엔진과 연결된 Session 클래스 생성
# 함정: SessionLocal은 클래스이며, 호출하면 인스턴스(트랜잭션 단위)가 생성됨
SessionLocal = sessionmaker(bind=engine)

# === CREATE (생성) ===
# 섹션 헤더 출력: INSERT 작업
print("\n=== CREATE ===")
# with문으로 Session을 열면 종료 시 자동 close(rollback은 별도)
with SessionLocal() as session:
    # 모델 인스턴스 생성(아직 DB에는 없음)
    user1 = User(name="Alice", email="alice@example.com", age=30)
    # 두 번째 사용자
    user2 = User(name="Bob", email="bob@example.com", age=25)
    # 세 번째 사용자
    user3 = User(name="Charlie", email="charlie@example.com", age=35)

    # add는 단일 객체를 세션의 pending 상태에 등록
    session.add(user1)            # 단일 추가
    # add_all은 여러 객체를 한 번에 등록
    session.add_all([user2, user3])  # 여러 개 추가
    # commit으로 트랜잭션 확정 + flush(실제 INSERT 실행)
    session.commit()
    # commit 이후에는 PK가 채워져 있음(autoincrement 결과)
    print(f"생성: {user1}")
    # 두 번째 사용자 출력
    print(f"생성: {user2}")
    # 세 번째 사용자 출력
    print(f"생성: {user3}")

# === READ (조회) ===
# 섹션 헤더 출력: SELECT 다양한 패턴
print("\n=== READ ===")
# 새 세션을 열어 별도 트랜잭션으로 조회
with SessionLocal() as session:
    # query(...).all(): 전체 SELECT(2.0에서는 session.scalars(select(User)).all() 권장)
    users = session.query(User).all()
    # 결과 출력
    print(f"전체 조회: {users}")

    # filter는 SQL 표현식(컬럼 == 값) 사용. first()는 0 또는 1행
    alice = session.query(User).filter(User.name == "Alice").first()
    # 단일 결과 출력
    print(f"filter: {alice}")

    # filter_by는 키워드 인자 형태(== 비교만 가능)
    bob = session.query(User).filter_by(name="Bob").first()
    # 결과 출력
    print(f"filter_by: {bob}")

    # session.get(Model, pk)는 PK로 직접 조회(아이덴티티 맵 활용)
    user_by_id = session.get(User, 1)
    # 결과 출력
    print(f"get(1): {user_by_id}")

    # 여러 조건은 콤마로 나열하면 AND. OR는 or_(...)
    result = session.query(User).filter(
        User.age >= 30,
        User.name != "Charlie"
    ).all()
    # 결과 출력
    print(f"age >= 30, name != Charlie: {result}")

    # 정렬, 제한
    # order_by(컬럼.desc()).limit(n)으로 상위 N개 조회
    ordered = session.query(User).order_by(User.age.desc()).limit(2).all()
    # 결과 출력
    print(f"나이 내림차순 상위 2: {ordered}")

    # count는 COUNT(*) 쿼리
    count = session.query(User).count()
    # 총 사용자 수 출력
    print(f"총 사용자 수: {count}")

# === UPDATE (수정) ===
# 섹션 헤더 출력: 객체 변경 후 commit / 벌크 update
print("\n=== UPDATE ===")
# 새 세션
with SessionLocal() as session:
    # 객체 조회 후 속성 변경 → commit이 자동 UPDATE 발급
    user = session.query(User).filter_by(name="Alice").first()
    # 단순 속성 할당
    user.age = 31  # 직접 수정
    # 트랜잭션 확정
    session.commit()
    # 갱신된 객체 확인
    print(f"수정 후: {user}")

    # 벌크 업데이트
    # query().update(dict)는 객체 로드 없이 한 번의 UPDATE 실행(빠르지만 ORM 이벤트 우회 함정)
    session.query(User).filter(User.age < 30).update({"age": 30})
    # 벌크 변경도 commit 필요
    session.commit()
    # 벌크 동작 안내
    print("벌크 업데이트: age < 30인 사용자 -> age = 30")

# === DELETE (삭제) ===
# 섹션 헤더 출력: 삭제 패턴
print("\n=== DELETE ===")
# 새 세션
with SessionLocal() as session:
    # 삭제할 객체 조회
    user = session.query(User).filter_by(name="Charlie").first()
    # session.delete(obj) 호출 후 commit으로 실제 DELETE 실행
    session.delete(user)
    # 트랜잭션 확정
    session.commit()
    # 삭제 안내
    print(f"삭제: Charlie")

    # 삭제 후 잔여 데이터 확인
    remaining = session.query(User).all()
    # 결과 출력
    print(f"남은 사용자: {remaining}")
```

**실행 결과** — 실행하지 않음 — 외부 라이브러리 `sqlalchemy` 가 있어야 도는 예제다 — 그것 없이 만들어 실행하지 않았다.

**풀이 요점**
- 뼈대 순서는 엔진 → `Base` · 모델 → `create_all` → `sessionmaker` → 작업마다 `with SessionLocal() as session:` 이다.
- `default=datetime.now` 는 괄호 없이 함수 자체를 넘겨야 행마다 호출된다.
- 쓰기 작업(`add` · 속성 변경 · 벌크 `update` · `delete`)은 모두 `commit` 으로 확정한다.
- `filter` 는 표현식(`>=` · `!=` 가능, 콤마는 AND), `filter_by` 는 `==` 키워드만이다.
- 벌크 update 는 객체를 불러오지 않는다 — 빠르지만 ORM 이벤트가 없다.
- 예제의 `session.query` 는 레거시 꼴이다 — 새로 쓴다면 `select()` 스타일로 옮길 수 있다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — 외부 라이브러리 `sqlalchemy` 가 있어야 도는 예제다 — 그것 없이 만들어 실행하지 않았다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
