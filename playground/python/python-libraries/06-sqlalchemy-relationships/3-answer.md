# python/python-libraries/06 — SQLAlchemy 관계 — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 4번 — 목록 1번 + 부서마다 1번 (N+1)

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
첫 줄에서 부서 목록을 읽는 SELECT 가 1번 나간다.
반복 안에서 `d.employees` 에 처음 접근할 때마다 그 부서의 직원을 읽는 SELECT 가 1번씩, 부서가 셋이므로 3번 나간다.
합쳐서 1 + 3 = 4번이다.

**왜 그런가**
`lazy="select"` 는 관계 속성에 접근하는 순간에 쿼리를 쏘는 방식이라, 부모 N개를 돌면 쿼리가 1 + N 번이 된다.
근거 — 2-summary 「동작 방식 (5)」.

### 2. 2번 — 부모 SELECT 1번 + `IN (...)` SELECT 1번

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
부서를 읽는 SELECT 1번 뒤에, 부서 PK 를 모아 `WHERE department_id IN (...)` 로 직원을 한 번에 읽는 SELECT 1번이 나간다.
반복 안의 `d.employees` 접근에는 추가 쿼리가 없으므로 총 2번이다.

**왜 그런가**
`selectinload` 는 부모 수와 상관없이 자식을 쿼리 한 번으로 가져오는 eager 전략이다.
근거 — 2-summary 「동작 방식 (6)」.

### 3. `c1.students` 에는 김철수와 이영희, 연결 테이블에는 4행

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
`c1` 은 두 학생이 모두 `extend` 로 이었으므로 `c1.students` 에는 김철수(`s1`)와 이영희(`s2`) 둘이 들어 있다.
연결 테이블에는 (s1, c1) · (s1, c2) · (s2, c1) · (s2, c3) 네 행이 생긴다.
리스트 안의 순서는 `order_by` 가 없으므로 단정하지 않는다.

**왜 그런가**
N:M 컬렉션에 객체를 이으면 연결 테이블의 행이 자동으로 만들어지고, 반대편 `students` 는 같은 연결 테이블에서 `course_id` 로 찾아 읽는다.
학생만 `add_all` 해도 cascade 로 과목과 연결 행이 함께 저장된다.
근거 — 2-summary 「동작 방식 (3)」 · 「동작 방식 (4)」.

### 4. 디자인팀의 id — 직접 적지 않아도 채워진다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
Charlie 는 `design.employees` 에 들어갔으므로 `department_id` 에는 디자인팀 행의 id 가 들어 있다.
새 데이터베이스에서 두 번째로 들어간 부서라면 그 값은 2 일 것이다 — 다만 id 를 붙이는 것은 데이터베이스의 동작이라 숫자 자체는 단정하지 않는다.
Charlie 는 `add` 하지 않았지만 저장된다.

**왜 그런가**
컬렉션에 `append` 하면 저장 시점에 부모의 id 가 자식의 외래키로 자동으로 채워진다.
자식이 세션에 따라 들어가는 것은 cascade 기본 동작 덕이다.
근거 — 2-summary 「동작 방식 (4)」, 「구현 세부사항 대 언어 보장」.

### 5. 외래키 컬럼 하나는 상대 하나만 가리킬 수 있기 때문이다

학생 행 하나에 `course_id` 칸을 두면 그 학생은 과목 하나만 가리킬 수 있다.
다대다는 양쪽이 모두 여럿과 이어지므로, (학생, 과목) 짝을 한 행씩 적는 연결 테이블이 따로 있어야 한다.
SQLAlchemy 에서는 그 테이블을 `secondary=` 로 `relationship` 에 알려 준다.
근거 — 2-summary 「동작 방식 (3)」.

### 6. 부모 행이 자식 수만큼 곱해져 돌아온다

`joinedload` 는 `LEFT OUTER JOIN` 으로 한 쿼리에 부모와 자식을 붙여 가져온다.
1:N 에서는 부서 한 행이 직원 수만큼 반복된 결과가 와서, 같은 부서 데이터를 여러 번 주고받게 된다.
N:1 · 1:1 은 상대가 하나뿐이라 행이 불어나지 않으므로 JOIN 한 번이 알맞다.
1:N 에는 중복이 없는 `selectinload` 가 권장된다.
근거 — 2-summary 「동작 방식 (6)」, 「어디서 틀리나 2」.

### 7. 적지 않아도 된다 — `backref` 가 반대편을 만든다

`backref` 는 한쪽에만 적으면 반대편 속성(`Employee.department`)을 자동으로 만든다.
대신 `Employee` 클래스만 읽어서는 `department` 속성이 있다는 것이 보이지 않는다.
양쪽에 다 적어야 하는 것은 `back_populates` 쪽이다.
근거 — 2-summary 「동작 방식 (2)」.

### 8. 권장만 어긋난 코드다 — 동작은 한다

`joinedload` 는 1:N 에서도 부서와 직원을 한 쿼리로 가져오므로 결과는 맞다.
다만 행이 곱해지는 비효율이 있어, 원본 팁은 1:N 에 `selectinload` 를 권한다.
예제는 부서 하나(`first()`)에 직원 둘이라 불어나는 양이 작고, 세 전략을 나란히 보이려는 시연이다.
근거 — 2-summary 「어디서 틀리나 2」, 「동작 방식 (6)」.

### 9. 컬렉션 전체 대신 쿼리 객체를 받아 조건을 더 걸 수 있기 때문이다

보통 컬렉션은 접근하는 순간 직원 수만 명을 모두 읽어 리스트로 만든다.
`lazy="dynamic"` 은 리스트 대신 쿼리 객체를 돌려주므로, `session.query(...)` 를 다루듯 그 위에 필터를 더 걸어 필요한 행만 데이터베이스에서 읽게 할 수 있다.
근거 — 2-summary 「동작 방식 (6)」 (필터 메서드 이름 등 세부는 원본에 근거 없음 — 추론).

## 실습 정답

### 실습 1. 부서-직원 · 학생-과목 관계를 만들고 로딩 전략 비교하기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. 연결 테이블 | `student_course = Table("student_course", Base.metadata, Column("student_id", …, ForeignKey("students.id"), primary_key=True), …)` |
| 2. `Department.employees` | `relationship("Employee", back_populates="department", lazy="select")` |
| 3. 외래키와 반대 방향 | `department_id = Column(Integer, ForeignKey("departments.id"))` · `department = relationship("Department", back_populates="employees")` |
| 4. N:M 관계 | `Student.courses` · `Course.students` 의 `relationship(..., secondary=student_course, back_populates=...)` |
| 5. 테이블 · 세션 | `Base.metadata.create_all(engine)` · `Session = sessionmaker(bind=engine)` |
| 6. 관계로 직원 추가 | `dev.employees.append(Employee(name="Alice"))` 외 두 줄 |
| 7. 부모만 저장 | `session.add_all([dev, design])` · `session.commit()` |
| 8. 양방향 조회 | `filter_by(name="개발팀").first()` → `dept.employees` · `filter_by(name="Alice").first()` → `emp.department` |
| 9~10. N:M 연결과 저장 | `s1.courses.extend([c1, c2])` · `s2.courses.extend([c1, c3])` · `session.add_all([s1, s2])` |
| 11. N:M 양방향 조회 | `student.courses` · `course.students` |
| 12. lazy | `session.query(Department).first()` 뒤 `dept.employees` 접근 |
| 13. joinedload | `.options(joinedload(Department.employees)).first()` |
| 14. selectinload | `.options(selectinload(Department.employees)).all()` 과 `for d in depts:` |
| 15. 요약 줄 | 마지막 `print` 다섯 줄 |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`python/python-libraries/reference/sqlalchemy-relationships.py`

```python
# [주요 라이브러리] SQLAlchemy 관계
# 설명: 1:N, N:M 관계, lazy loading, eager loading 전략
# 팁: N+1 문제를 방지하려면 eager loading을 사용한다. joinedload는 1:1, N:1에, selectinload는 1:N에 적합하다. back_populates는 양방향 관계를 명시하고, backref는 자동으로 역방향을 생성한다. cascade 옵션으로 부모 삭제 시 자식 처리를 설정할 수 있다.

# 핵심 임포트: 컬럼, FK, 그리고 N:M 연결 테이블 작성에 쓰이는 Table
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Table
# relationship: 객체 간 관계 정의. joinedload/selectinload: 즉시 로딩 옵션
from sqlalchemy.orm import declarative_base, sessionmaker, relationship, joinedload, selectinload

# 인메모리 SQLite 엔진(테스트용)
engine = create_engine("sqlite:///:memory:", echo=False)
# ORM 베이스 클래스
Base = declarative_base()

# === N:M 관계를 위한 연결 테이블 ===
# 다대다 관계는 별도의 연결(association) 테이블이 필요
# Table 객체로 직접 정의(클래스 X) → 단순 매핑일 때 권장
# 두 외래키를 PK로 묶어 중복 행을 막는 것이 일반적
student_course = Table(
    "student_course", Base.metadata,
    Column("student_id", Integer, ForeignKey("students.id"), primary_key=True),
    Column("course_id", Integer, ForeignKey("courses.id"), primary_key=True)
)

# === 1:N 관계 (Department -> Employee) ===
# 부서 모델: 한 부서에 여러 직원이 속함
class Department(Base):
    # 테이블명
    __tablename__ = "departments"
    # PK
    id = Column(Integer, primary_key=True)
    # 부서명
    name = Column(String(100))
    # 1:N - 한 부서에 여러 직원
    # back_populates는 양방향 명시(반대편에 동일하게 설정해야 함)
    # lazy="select"는 기본값(접근 시 SELECT 실행 → N+1 위험)
    employees = relationship("Employee", back_populates="department", lazy="select")

    # 디버깅 출력
    def __repr__(self):
        return f"Department(id={self.id}, name='{self.name}')"

# 직원 모델
class Employee(Base):
    # 테이블명
    __tablename__ = "employees"
    # PK
    id = Column(Integer, primary_key=True)
    # 이름
    name = Column(String(100))
    # 부서 FK
    department_id = Column(Integer, ForeignKey("departments.id"))
    # N:1 - 직원은 한 부서에 소속
    # 반대편 employees와 짝을 이룸(back_populates)
    department = relationship("Department", back_populates="employees")

    # 디버깅 출력
    def __repr__(self):
        return f"Employee(id={self.id}, name='{self.name}')"

# === N:M 관계 (Student <-> Course) ===
# 학생 모델: 여러 과목을 수강
class Student(Base):
    # 테이블명
    __tablename__ = "students"
    # PK
    id = Column(Integer, primary_key=True)
    # 이름
    name = Column(String(100))
    # secondary로 연결 테이블 지정 → N:M 관계 형성
    courses = relationship("Course", secondary=student_course, back_populates="students")

    # 디버깅 출력
    def __repr__(self):
        return f"Student(id={self.id}, name='{self.name}')"

# 과목 모델: 여러 학생이 수강
class Course(Base):
    # 테이블명
    __tablename__ = "courses"
    # PK
    id = Column(Integer, primary_key=True)
    # 과목명
    title = Column(String(200))
    # 반대편도 동일한 secondary와 back_populates를 설정
    students = relationship("Student", secondary=student_course, back_populates="courses")

    # 디버깅 출력
    def __repr__(self):
        return f"Course(id={self.id}, title='{self.title}')"

# 모든 테이블 생성(메타데이터 일괄 생성)
Base.metadata.create_all(engine)
# 세션 팩토리(Session 클래스 생성)
Session = sessionmaker(bind=engine)

# === 1:N 데이터 삽입 및 조회 ===
# 섹션 헤더 출력: 1:N 관계 시연
print("=== 1:N 관계 (Department -> Employee) ===")
# with문으로 트랜잭션 단위 관리
with Session() as session:
    # 부모 객체 생성
    dev = Department(name="개발팀")
    # 두 번째 부서
    design = Department(name="디자인팀")

    # 관계를 통한 추가
    # 자식 컬렉션에 append하면 FK가 자동으로 채워짐(편한 이유)
    dev.employees.append(Employee(name="Alice"))
    # 같은 부서에 또 다른 직원
    dev.employees.append(Employee(name="Bob"))
    # 다른 부서에 직원
    design.employees.append(Employee(name="Charlie"))

    # 부모만 add_all해도 cascade 기본값(save-update)으로 자식까지 저장됨
    session.add_all([dev, design])
    # 커밋
    session.commit()

    # 조회: 부서 -> 직원들
    # filter_by → first()로 단일 부서 조회
    dept = session.query(Department).filter_by(name="개발팀").first()
    # employees 컬렉션 접근 시점에 추가 SELECT 발생(lazy)
    print(f"{dept.name}: {dept.employees}")

    # 조회: 직원 -> 부서
    # 반대 방향 탐색: 직원에서 부서로
    emp = session.query(Employee).filter_by(name="Alice").first()
    # department 속성 접근 → SELECT 한 번 더 실행 가능
    print(f"{emp.name}의 부서: {emp.department}")

# === N:M 데이터 삽입 및 조회 ===
# 섹션 헤더 출력: N:M 관계 시연
print("\n=== N:M 관계 (Student <-> Course) ===")
with Session() as session:
    # 학생 두 명 생성
    s1 = Student(name="김철수")
    # 두 번째 학생
    s2 = Student(name="이영희")
    # 과목 세 개 생성
    c1 = Course(title="Python 기초")
    # 두 번째 과목
    c2 = Course(title="데이터분석")
    # 세 번째 과목
    c3 = Course(title="웹개발")

    # 관계 설정
    # extend로 컬렉션에 여러 과목 한꺼번에 연결(연결 테이블 행이 자동 생성됨)
    s1.courses.extend([c1, c2])      # 철수: Python, 데이터분석
    # 영희도 두 과목 수강(c1은 두 학생 공유)
    s2.courses.extend([c1, c3])      # 영희: Python, 웹개발

    # 학생만 추가해도 cascade로 과목과 연결행이 함께 저장됨
    session.add_all([s1, s2])
    # 커밋
    session.commit()

    # 학생 -> 수강 과목
    # 단일 학생 조회 후 courses 컬렉션 접근
    student = session.query(Student).filter_by(name="김철수").first()
    # 수강 과목 목록 출력
    print(f"{student.name}의 과목: {student.courses}")

    # 과목 -> 수강 학생
    # 반대 방향: 과목 → 학생
    course = session.query(Course).filter_by(title="Python 기초").first()
    # 수강생 목록 출력
    print(f"{course.title} 수강생: {course.students}")

# === Loading 전략 ===
# 섹션 헤더 출력: lazy/eager 로딩 비교
print("\n=== Loading 전략 ===")
with Session() as session:
    # 1. Lazy Loading (기본) - 접근 시 쿼리 실행
    # 부모 1건 조회 후, 자식 컬렉션 접근 시점에 추가 쿼리 → N+1 문제 발생 가능
    dept = session.query(Department).first()
    # dept.employees 접근 시 SELECT 쿼리 발생 (N+1 문제 가능)
    print(f"Lazy: {dept.name} -> {dept.employees}")

    # 2. Eager Loading - joinedload (JOIN으로 한 번에)
    # options(joinedload(...))로 LEFT OUTER JOIN을 추가해 한 번에 로드
    # 1:1, N:1 같은 단일 관계에 적합. 1:N에서는 결과 행이 곱해져 비효율 가능
    dept = session.query(Department).options(
        joinedload(Department.employees)
    ).first()
    # 단일 쿼리로 자식 포함
    print(f"Joined: {dept.name} -> {dept.employees}")

    # 3. Eager Loading - selectinload (별도 SELECT IN 쿼리)
    # 부모 PK를 모은 뒤 IN (...)으로 자식을 한 번에 가져옴
    # 1:N에 가장 적합(중복 없음)
    depts = session.query(Department).options(
        selectinload(Department.employees)
    ).all()
    # 부모 N건 + 자식 1건 → 총 2회 쿼리로 모든 데이터 로드
    for d in depts:
        # 자식 컬렉션 접근에도 추가 쿼리 없음
        print(f"SelectIn: {d.name} -> {d.employees}")

# 섹션 헤더 출력: 로딩 전략 요약
print("\n=== Loading 전략 비교 ===")
# 기본 lazy 동작과 함정 안내
print("lazy='select' (기본): 접근 시 개별 쿼리 -> N+1 문제")
# joinedload 가이드
print("joinedload:           JOIN으로 한 번에 -> 1:1, N:1에 적합")
# selectinload 가이드
print("selectinload:         SELECT ... IN (...) -> 1:N에 적합")
# subqueryload 가이드
print("subqueryload:         서브쿼리로 로드 -> 복잡한 관계에")
# dynamic 모드: 컬렉션이 아닌 Query 객체를 반환(추가 필터링 가능, 무한 스크롤 등)
print("lazy='dynamic':       쿼리 객체 반환 -> 추가 필터링 가능")
```

**실행 결과** — 실행하지 않음 — 외부 라이브러리 `sqlalchemy` 가 있어야 도는 예제다 — 그것 없이 만들어 실행하지 않았다.

**풀이 요점**
- `ForeignKey` 에는 테이블 이름(`"departments.id"`), `relationship` 에는 클래스 이름(`"Department"`)을 적는다.
- `back_populates` 는 양쪽 관계에 서로의 속성 이름을 적어 짝을 맞춘다.
- N:M 은 `Table` 로 만든 연결 테이블을 양쪽 `relationship` 의 `secondary` 에 똑같이 넘긴다.
- 컬렉션에 `append` · `extend` 하고 부모만 `add_all` 해도, 외래키와 연결 행은 저장 시점에 자동으로 채워진다(cascade).
- 같은 데이터를 lazy · `joinedload` · `selectinload` 로 읽으면 결과 객체는 같고 쿼리 수와 모양만 다르다 — 차이는 `echo=True` 로 SQL 을 볼 때 드러난다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — 외부 라이브러리 `sqlalchemy` 가 있어야 도는 예제다 — 그것 없이 만들어 실행하지 않았다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
