# python/python-libraries/06 — SQLAlchemy 관계 — 정리 (힌트)

> 출처 — study-site 항목 `python/sqlalchemy-relationships`(항목 데이터 `data/python/libraries.json`) · 정답 코드 study-practice `python/python-libraries/reference/sqlalchemy-relationships.py`\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).\
> 실행 — 실행하지 않음 — 외부 라이브러리 `sqlalchemy` 가 있어야 도는 예제다 — 그것 없이 만들어 실행하지 않았다.

## 한눈에 — 쉽게 말하면

**`relationship` 은 「주소록에 적어 둔 연락처」다.**
주소록(파이썬 객체)에는 「이 사람의 회사」, 「이 회사의 직원들」처럼 사람과 회사를 바로 잇는 칸이 있다.
실제 연결은 서류 보관함(데이터베이스)에 「회사 번호」라는 칸으로만 적혀 있다.
SQLAlchemy 의 관계도 똑같은 구조다.
테이블에는 외래키 숫자만 있고, `relationship` 이 그 숫자를 따라가 객체나 객체 목록을 꺼내 준다.

| 비유 | 실체 |
|---|---|
| 서류에 적힌 회사 번호 | `ForeignKey` 컬럼 (`department_id`) |
| 주소록의 「회사」 칸 | `Employee.department` (`relationship`) |
| 주소록의 「직원들」 칸 | `Department.employees` (`relationship`) |
| 수강 신청서 묶음 | N:M 연결 테이블 (`student_course`) |
| 칸을 열어 볼 때 보관함에 가 보기 | lazy loading |
| 처음부터 같이 가져오기 | eager loading (`joinedload` · `selectinload`) |

```text
 파이썬 객체 쪽                         데이터베이스 쪽
 ┌──────────────┐  employees  ┌────────────┐
 │ Department   │────────────▶│ [Employee, │      departments(id, name)
 │  개발팀       │◀────────────│  Employee] │      employees(id, name, department_id ─▶ departments.id)
 └──────────────┘  department └────────────┘
        relationship 이 오가는 길            ForeignKey 가 적힌 숫자
```

## 이 주제가 답하려는 질문

1. 테이블에는 숫자(외래키)만 있는데, 어떻게 `dept.employees` 처럼 객체 목록을 바로 얻나?
2. 한 학생이 여러 과목, 한 과목이 여러 학생인 다대다 관계는 어디에 저장하나?
3. 관계 속성을 「언제」 데이터베이스에서 읽어 오나, 그리고 그 시점이 왜 성능 문제(N+1)가 되나?
4. 그 문제를 막는 eager loading 전략(`joinedload` · `selectinload` 등)은 각각 어떤 관계에 맞나?

## 동작 방식

### (1) 외래키와 1:N 관계

**언제 쓰나** — 한 부서에 여러 직원이 있듯, 「하나」 쪽이 「여럿」 쪽을 거느릴 때 쓴다.
「여럿」 쪽 테이블에 「하나」 쪽의 id 를 적는 칸을 둔다.

> **외래키(ForeignKey)** — 다른 테이블의 기본키 값을 가리키는 컬럼.\
> 예: `employees.department_id` 는 `departments.id` 를 가리킨다.

> **1:N(일대다)** — 한 행이 다른 테이블의 여러 행과 이어지는 관계.\
> 예: 부서 하나 ↔ 직원 여럿.

```text
 class Employee:
   department_id = Column(Integer, ForeignKey("departments.id"))   ← 숫자 칸
   department    = relationship("Department", ...)                 ← 객체 칸
 class Department:
   employees     = relationship("Employee", ...)                   ← 목록 칸
        │
        ▼
 emp.department    → department_id 로 departments 를 찾아 Department 객체 하나
 dept.employees    → department_id == dept.id 인 employees 를 찾아 list
```

- `ForeignKey` 는 테이블에 실제로 생기는 컬럼이고, `relationship` 은 테이블에 컬럼을 만들지 않는다.
- `relationship` 은 외래키를 따라 반대편 객체를 꺼내 주는 파이썬 쪽 속성이다.
- 「여럿」 쪽(Employee)의 `department` 는 객체 하나, 「하나」 쪽(Department)의 `employees` 는 리스트다.
- 직원 쪽에서 보면 N:1(다대일) 관계다.

> **relationship** — 모델 클래스 사이의 관계를 파이썬 속성으로 정의하는 함수.\
> 예: `employees = relationship("Employee", back_populates="department")`.

### (2) 양방향 관계 — `back_populates` 와 `backref`

**언제 쓰나** — 부서에서 직원으로, 직원에서 부서로 양쪽 모두 오가고 싶을 때 쓴다.

```text
 Department.employees = relationship("Employee",   back_populates="department")
 Employee.department  = relationship("Department", back_populates="employees")
        │      (양쪽에 적고, 서로의 속성 이름을 가리킨다)
        ▼
 두 속성이 한 관계의 두 끝으로 묶인다

 backref 를 쓰면:
 Department.employees = relationship("Employee", backref="department")
        │      (한쪽에만 적는다)
        ▼
 Employee.department 가 자동으로 생긴다
```

- `back_populates` 는 양방향을 명시하는 방법이고, 반대편에도 짝이 되는 설정을 똑같이 적어야 한다.
- `backref` 는 한쪽에만 적으면 반대편 속성을 자동으로 만들어 준다.
- `back_populates` 는 두 클래스를 읽기만 해도 양쪽 속성이 다 보인다는 점이 다르다.

> **양방향 관계** — 두 모델이 서로를 속성으로 참조하는 관계.\
> 예: `dept.employees` 와 `emp.department` 가 같은 관계의 양 끝이다.

### (3) N:M 관계 — 연결 테이블과 `secondary`

**언제 쓰나** — 학생 하나가 여러 과목을 듣고, 과목 하나를 여러 학생이 들을 때 쓴다.

```text
 students(id, name)       student_course(student_id, course_id)       courses(id, title)
                                ↑ 둘 다 FK, 둘을 묶어 PK
 Student.courses  = relationship("Course",  secondary=student_course, back_populates="students")
 Course.students  = relationship("Student", secondary=student_course, back_populates="courses")
        │
        ▼
 s1.courses.extend([c1, c2])  →  연결 테이블에 (s1, c1), (s1, c2) 행이 자동 생성
 c1.students                  →  연결 테이블에서 course_id == c1.id 인 학생들
```

- 다대다는 한쪽 테이블에 외래키 컬럼 하나로는 담을 수 없어서 별도의 연결 테이블이 필요하다.
- 연결 테이블은 클래스가 아니라 `Table` 객체로 직접 정의했다 — 두 id 만 잇는 단순 매핑일 때 권장되는 꼴이다.
- 두 외래키를 함께 기본키로 묶어, 같은 (학생, 과목) 짝이 두 번 들어가는 중복 행을 막는 것이 일반적이다.
- `relationship` 의 `secondary=` 에 연결 테이블을 넘기면 N:M 관계가 된다.
- 반대편도 같은 `secondary` 와 `back_populates` 를 설정한다.

> **N:M(다대다)** — 양쪽 행이 모두 상대편 여러 행과 이어지는 관계.\
> 예: 학생 ↔ 과목.

> **연결(association) 테이블** — 다대다의 짝을 한 행씩 적는 중간 테이블.\
> 예: `student_course` 의 한 행 `(1, 2)` 는 「학생 1 이 과목 2 를 듣는다」.

### (4) 관계로 객체 추가하기와 cascade

**언제 쓰나** — 부모와 자식을 함께 만들어 한꺼번에 저장할 때 쓴다.

```text
 dev = Department(name="개발팀")
 dev.employees.append(Employee(name="Alice"))
 session.add_all([dev])          ← 부모만 세션에 넣는다
 session.commit()
        │
        ▼
 cascade(기본 동작)로 Alice 도 세션에 따라 들어감
 INSERT departments … → 개발팀의 id 가 정해짐
 INSERT employees …   → Alice 의 department_id 에 그 id 가 자동으로 채워짐
```

- 자식 컬렉션에 `append` 하면 외래키 숫자를 직접 적지 않아도 저장할 때 자동으로 채워진다.
- 부모만 `add_all` 해도 자식까지 저장되는 것은 cascade 의 기본 동작 덕이다.
- N:M 에서도 학생만 `add_all` 하면 과목과 연결 테이블 행이 함께 저장된다.
- `cascade` 옵션을 바꾸면 부모를 지울 때 자식을 어떻게 처리할지 정할 수 있다.

> **cascade** — 부모 객체에 한 세션 작업(추가·삭제 등)을 관계로 이어진 자식에게도 전파하는 설정.\
> 예: 부서만 `add` 해도 소속 직원이 함께 저장된다.

### (5) lazy loading 과 N+1 문제

**언제 쓰나** — 관계 속성을 늘 쓰지는 않을 때 알맞은 기본 동작이다.

```text
 depts = session.query(Department).all()      ← 쿼리 1번 (부서 N개)
 for d in depts:
     d.employees                               ← 접근할 때마다 SELECT 1번
        │
        ▼
 총 쿼리 수 = 1 + N   ← N+1 문제
```

- `lazy="select"` 가 기본값이다.
- 부모를 읽을 때는 자식을 읽지 않고, 자식 컬렉션에 처음 접근하는 순간 SELECT 를 따로 실행한다.
- 부모 하나만 다룰 때는 문제가 없지만, 부모 N개를 돌며 자식에 접근하면 쿼리가 1 + N 번 나간다.
- 직원 → 부서 방향(`emp.department`)도 접근 시점에 SELECT 가 한 번 더 나갈 수 있다.

> **lazy loading(지연 로딩)** — 관계 속성에 실제로 접근할 때 비로소 DB 에서 읽는 방식.\
> 예: `dept.employees` 를 읽는 줄에서 SELECT 가 나간다.

> **N+1 문제** — 목록 1번 + 항목마다 1번씩, 쿼리가 항목 수만큼 불어나는 문제.\
> 예: 부서 3개를 돌며 직원을 읽으면 쿼리 4번.

### (6) eager loading — `joinedload` · `selectinload` · 그 밖의 전략

**언제 쓰나** — 부모를 읽으면서 자식도 쓸 것이 확실할 때, N+1 을 막으려고 쓴다.

```text
 query(Department).options(joinedload(Department.employees))
        │
        ▼
 SELECT … FROM departments LEFT OUTER JOIN employees …     ← 쿼리 1번
 (부서 1행이 직원 수만큼 여러 행으로 불어나 돌아옴)

 query(Department).options(selectinload(Department.employees)).all()
        │
        ▼
 ① SELECT … FROM departments                                ← 부모들
 ② SELECT … FROM employees WHERE department_id IN (1, 2, …) ← 부모 PK 를 모아 한 번에
 총 쿼리 2번, 이후 d.employees 접근에 추가 쿼리 없음
```

- `joinedload` 는 `LEFT OUTER JOIN` 을 붙여 부모와 자식을 한 쿼리로 가져온다.
- `joinedload` 는 1:1, N:1 처럼 상대가 하나뿐인 관계에 알맞다.
- 1:N 에 쓰면 부모 행이 자식 수만큼 곱해져 돌아와 비효율일 수 있다.
- `selectinload` 는 부모 PK 를 모은 뒤 `IN (...)` 한 번으로 자식을 가져온다 — 행이 중복되지 않아 1:N 에 가장 알맞다.
- `subqueryload` 는 서브쿼리로 자식을 로드하며, 원본은 「복잡한 관계에」 쓴다고 적는다.
- `lazy="dynamic"` 은 컬렉션 대신 쿼리 객체를 돌려줘서, 자식에 추가 필터링을 걸 수 있다(무한 스크롤처럼 일부만 읽을 때).
- eager 전략은 `query(...).options(...)` 로 그 쿼리에만 붙이고, `relationship(..., lazy=...)` 은 관계의 기본값을 정한다.

> **eager loading(즉시 로딩)** — 부모를 읽을 때 관계 대상도 미리 함께 읽는 방식.\
> 예: `options(selectinload(Department.employees))`.

## 문법 — 형태와 규칙

```python
from sqlalchemy import Column, Integer, ForeignKey, Table
from sqlalchemy.orm import relationship, selectinload

class Team(Base):
    __tablename__ = "teams"
    id = Column(Integer, primary_key=True)
    players = relationship("Player", back_populates="team")      # 1:N

class Player(Base):
    __tablename__ = "players"
    id = Column(Integer, primary_key=True)
    team_id = Column(Integer, ForeignKey("teams.id"))            # 숫자 칸
    team = relationship("Team", back_populates="players")        # N:1

teams = session.query(Team).options(selectinload(Team.players)).all()
```

- `ForeignKey("테이블명.컬럼명")` — 클래스 이름이 아니라 **테이블 이름**(`__tablename__`)을 적는다.
- `relationship("클래스명", ...)` — 여기에는 **클래스 이름**을 문자열로 적는다.
- `back_populates="반대편 속성 이름"` — 양쪽에 짝을 맞춰 적는다.
- `backref="새 속성 이름"` — 한쪽에만 적으면 반대편 속성이 생긴다.
- `secondary=연결테이블` — N:M 일 때 양쪽 `relationship` 에 같은 테이블을 넘긴다.
- 연결 테이블은 `Table("이름", Base.metadata, Column(..., ForeignKey(...), primary_key=True), ...)` 꼴이다.
- `lazy="select"` 가 기본값이고, `lazy="dynamic"` 은 쿼리 객체를 돌려준다.
- 쿼리 단위 전략은 `.options(joinedload(모델.속성))` · `.options(selectinload(모델.속성))` 로 붙인다.
- 컬렉션 관계는 리스트처럼 `append` · `extend` 로 객체를 잇는다.

| 전략 | 쿼리 모양 | 알맞은 관계 |
|---|---|---|
| `lazy="select"` (기본) | 접근할 때마다 SELECT | 관계를 드물게 쓸 때 — 반복 접근하면 N+1 |
| `joinedload` | `LEFT OUTER JOIN` 1번 | 1:1, N:1 |
| `selectinload` | 부모 SELECT + `IN (...)` SELECT, 총 2번 | 1:N |
| `subqueryload` | 서브쿼리로 로드 | 복잡한 관계(원본의 표현) |
| `lazy="dynamic"` | 쿼리 객체 반환 | 자식에 추가 필터링이 필요할 때 |

## 어디서 틀리나

### 1. 목록을 돌며 관계에 접근하면 N+1 이 생긴다
기본값 `lazy="select"` 에서는 부모 N개를 돌며 `d.employees` 를 읽을 때마다 쿼리가 나간다.
N+1 문제를 막으려면 eager loading 을 쓴다.
코드에는 쿼리 줄이 한 줄뿐이라 문제가 눈에 띄지 않는다는 점이 함정이다.

### 2. `joinedload` 를 1:N 에 쓰면 행이 곱해진다
`joinedload` 는 1:1, N:1 에 알맞고, `selectinload` 는 1:N 에 알맞다.
1:N 에 JOIN 을 쓰면 부서 한 행이 직원 수만큼 반복되어 돌아온다.
원본 예제는 시연을 위해 1:N 인 `Department.employees` 에 `joinedload` 를 썼다 — 동작은 하지만 원본 팁의 권장과는 다르다.

### 3. `back_populates` 는 양쪽에 맞춰 적어야 한다
`back_populates` 는 반대편에도 짝이 되는 설정을 똑같이 적어야 양방향이 된다.
`backref` 는 한쪽에만 적으면 반대편을 자동으로 만든다.
둘을 섞어 같은 관계를 두 번 정의하지 않도록 한 방식만 고른다.

### 4. N:M 에 외래키 컬럼 하나로 버티려 하지 않는다
다대다는 연결 테이블과 `secondary` 가 필요하다.
양쪽 `relationship` 이 같은 `secondary` 를 가리켜야 한 관계로 묶인다.

### 5. cascade 를 모르면 「왜 자식까지 저장됐지/지워졌지」에서 막힌다
부모만 `add_all` 해도 자식이 저장되는 것은 cascade 기본 동작 때문이다.
부모 삭제 시 자식을 어떻게 할지는 `cascade` 옵션으로 정한다.

### 6. 원본 주석의 cascade 기본값 표기
원본 주석은 cascade 기본값을 `save-update` 로 적는다.
SQLAlchemy 문서의 기본값은 `save-update` 하나가 아니라 `merge` 도 포함한 묶음으로 알려져 있어, 이 표기는 일부만 적은 것일 수 있다 (확인 필요).
「부모만 add 해도 자식이 저장된다」는 결론은 `save-update` 에서 나오므로 예제의 동작 설명에는 영향이 없다.

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| `lazy="select"` 가 `relationship` 의 기본값이다 | SQLAlchemy 라이브러리의 설계 (파이썬 언어와 무관) |
| `joinedload` 는 JOIN, `selectinload` 는 `IN (...)` 쿼리를 쓴다 | SQLAlchemy 라이브러리의 구현 · 문서 |
| 부모만 `add` 해도 자식이 저장된다 | SQLAlchemy 의 cascade 기본 설정 |
| 새 행의 id 가 1, 2, 3 … 으로 붙는다 | 데이터베이스(여기서는 SQLite)의 자동 증가 동작 — SQLAlchemy 가 정하지 않는다 (확인 필요) |
| `dept.employees` 리스트 안의 순서 | `order_by` 를 주지 않았으므로 데이터베이스가 돌려주는 순서 — 보장되지 않는다 (확인 필요) |
| 인메모리 SQLite 의 데이터가 다음 `with Session()` 블록에서도 보인다 | SQLAlchemy 가 `:memory:` 엔진에서 같은 연결을 재사용하는 풀 동작 (확인 필요) |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 부서 하나에 직원 여럿 | `ForeignKey` + `relationship` (1:N) | 직원 이름을 부서 테이블에 문자열로 이어 붙이기 |
| 학생 ↔ 과목 | 연결 테이블 + `secondary` | 한쪽 테이블의 외래키 하나 |
| 부서 목록과 각 부서의 직원을 함께 보여 줄 때 | `selectinload` | 기본 lazy 로 반복 접근 |
| 직원 목록과 각 직원의 부서를 보여 줄 때 | `joinedload` | 기본 lazy 로 반복 접근 |
| 부모 하나를 읽고 자식은 쓸 수도 안 쓸 수도 있을 때 | 기본 `lazy="select"` | 늘 eager loading |
| 자식이 매우 많아 일부만 걸러 읽을 때 | `lazy="dynamic"` | 컬렉션 전체 로드 |
| 양방향을 코드에 드러내고 싶을 때 | `back_populates` (양쪽) | 한쪽만 적은 `back_populates` |

## 핵심 문장

1. **테이블에는 외래키 숫자만 있고, `relationship` 이 그 숫자를 따라 객체를 꺼내 준다.**
2. **N:M 은 연결 테이블이 필요하고, 양쪽 `relationship` 에 같은 `secondary` 를 넘긴다.**
3. **기본 lazy loading 은 접근할 때 쿼리를 쏘므로, 목록을 돌면 N+1 이 된다.**
4. **N+1 은 eager loading 으로 막는다 — 단일 대상(1:1, N:1)은 `joinedload`, 컬렉션(1:N)은 `selectinload`.**
5. **양방향은 `back_populates` 로 양쪽에 명시하거나 `backref` 로 한쪽에서 자동 생성하고, 자식 처리는 cascade 가 정한다.**

## 관련 자료

- [sqlalchemy-basics](../05-sqlalchemy-basics/2-summary.md)
- `repository` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- 원본: study-site 항목 데이터 `data/python/libraries.json` 의 `sqlalchemy-relationships`

## 용어 풀이

- **ORM** — 테이블의 행을 파이썬 객체로 다루게 해 주는 도구. SQLAlchemy 가 그 예다.
- **외래키(ForeignKey)** — 다른 테이블의 기본키를 가리키는 컬럼.
- **기본키(PK)** — 행 하나를 유일하게 가리키는 컬럼(또는 컬럼 묶음).
- **relationship** — 모델 사이의 관계를 파이썬 속성으로 정의하는 함수.
- **1:N / N:1** — 한 행 ↔ 여러 행 관계를 각 쪽에서 본 이름.
- **N:M** — 양쪽 모두 여러 행과 이어지는 다대다 관계.
- **연결(association) 테이블** — 다대다의 짝을 한 행씩 적는 중간 테이블.
- **`secondary`** — `relationship` 에 연결 테이블을 알려 주는 인자.
- **`back_populates`** — 양쪽에 적어 두 속성을 한 관계로 묶는 인자.
- **`backref`** — 한쪽에만 적어 반대편 속성을 자동 생성하는 인자.
- **cascade** — 부모에 한 세션 작업을 자식에게 전파하는 설정.
- **세션(Session)** — 객체의 변경을 모아 DB 와 주고받는 작업 단위.
- **lazy loading** — 관계 속성에 접근할 때 DB 에서 읽는 방식.
- **eager loading** — 부모를 읽을 때 관계 대상도 미리 읽는 방식.
- **N+1 문제** — 목록 1번 + 항목마다 1번씩 쿼리가 불어나는 문제.
- **`joinedload`** — JOIN 으로 부모와 자식을 한 쿼리로 읽는 eager 옵션.
- **`selectinload`** — 부모 PK 를 모아 `IN (...)` 쿼리 한 번으로 자식을 읽는 eager 옵션.
- **`subqueryload`** — 서브쿼리로 자식을 읽는 eager 옵션.
- **`lazy="dynamic"`** — 컬렉션 대신 쿼리 객체를 돌려주는 관계 설정.

## 더 들어가면

- SQLAlchemy 2.0 에서는 `session.query(...)` 가 「레거시」 API 로 분류되고 `select(...)` + `session.execute(...)` / `session.scalars(...)` 꼴이 권장된다 (확인 필요).
- `declarative_base` 를 `sqlalchemy.orm` 에서 가져오는 꼴은 1.4 이후의 경로이고, 2.0 에서는 `DeclarativeBase` 를 상속하는 꼴도 쓴다 (확인 필요).
- 2.0 에서 `lazy="dynamic"` 은 레거시로 취급되고 `lazy="write_only"` 가 대안으로 소개된다 (확인 필요).
- 부모를 지울 때 자식도 지우려면 `cascade="all, delete-orphan"` 같은 값을 쓴다 (확인 필요).
- 컬렉션에 `joinedload` 를 쓰고 `first()` 처럼 LIMIT 을 걸면, SQLAlchemy 가 부모 쿼리를 서브쿼리로 감싸 LIMIT 이 부모 행 기준으로 걸리게 한다고 알려져 있다 (확인 필요).
- `relationship(..., order_by=...)` 로 컬렉션의 순서를 정할 수 있다 (확인 필요).
- `create_engine(..., echo=True)` 로 바꾸면 실제로 나가는 SQL 을 로그로 볼 수 있어, N+1 여부를 눈으로 확인하는 데 쓴다 (확인 필요).
