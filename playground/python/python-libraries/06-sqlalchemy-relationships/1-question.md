# python/python-libraries/06 — SQLAlchemy 관계 — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 부서 셋을 돌며 직원 수 세기 (예측)

```python
# 질문용 발췌 — 부서 3개가 DB 에 있고, employees 는 기본 lazy="select"
depts = session.query(Department).all()
for d in depts:
    print(d.name, len(d.employees))
```

- 이 코드가 끝날 때까지 SELECT 쿼리는 모두 몇 번 나가나?

### 2. 같은 반복에 `selectinload` 를 붙이면 (예측)

- 1번 코드의 첫 줄을 `session.query(Department).options(selectinload(Department.employees)).all()` 로 바꾸면 쿼리는 모두 몇 번 나가나?

### 3. 두 학생이 과목을 나눠 들으면 (예측)

```python
# 질문용 발췌 — Student.courses 는 secondary=student_course
s1.courses.extend([c1, c2])
s2.courses.extend([c1, c3])
session.add_all([s1, s2])
session.commit()
```

- 커밋 뒤 `c1.students` 에는 누가 들어 있나?
- 연결 테이블 `student_course` 에는 행이 몇 개 생기나?

### 4. 부모만 세션에 넣었을 때 (예측)

```python
# 질문용 발췌
dev = Department(name="개발팀")
design = Department(name="디자인팀")
dev.employees.append(Employee(name="Alice"))
design.employees.append(Employee(name="Charlie"))
session.add_all([dev, design])
session.commit()
```

- 커밋 뒤 Charlie 의 `department_id` 에는 무엇이 들어 있나?

### 5. 다대다에 연결 테이블이 필요한 까닭 (왜)

- 학생 ↔ 과목 관계를 `students` 테이블의 외래키 컬럼 하나로 담을 수 없는 까닭은 무엇인가?

### 6. `joinedload` 가 1:N 보다 N:1 에 권장되는 까닭 (왜)

- 1:N 컬렉션에 `joinedload` 를 쓰면 무엇이 비효율이 되나?

### 7. `backref` 를 쓸 때의 반대편 (경계)

- `Department.employees = relationship("Employee", backref="department")` 로만 적으면 `Employee` 클래스에 `department` 관계를 따로 적어야 하나?

### 8. 원본 예제의 `joinedload(Department.employees)` (경계)

- 1:N 관계에 `joinedload` 를 쓴 원본 예제는 잘못 동작하는 코드인가, 아니면 권장만 어긋난 코드인가?

### 9. `lazy="dynamic"` 과 세션 쿼리 (연결)

- 직원이 수만 명인 부서에서 「이름이 A 로 시작하는 직원」만 읽고 싶을 때 `lazy="dynamic"` 이 보통 컬렉션보다 나은 까닭은 무엇인가?

## 실습

### 실습 1. 부서-직원 · 학생-과목 관계를 만들고 로딩 전략 비교하기

**만들 것** — 인메모리 SQLite 에 1:N(부서-직원)과 N:M(학생-과목) 관계를 정의하고, 데이터를 넣어 양방향으로 조회한 뒤, lazy · `joinedload` · `selectinload` 세 로딩 전략으로 같은 데이터를 읽어 보는 스크립트를 만든다.

**준비물** — `sqlalchemy` 패키지가 필요하다(`pip install sqlalchemy`, `sqlalchemy.orm` 에서 `declarative_base` 를 가져올 수 있는 버전 (확인 필요)).

**요구 조건**

1단계 — 모델과 테이블
1. 학생과 과목을 잇는 연결 테이블 `student_course` 를 `Table` 로 정의한다 — 두 컬럼이 각각 `students.id` · `courses.id` 를 외래키로 가리키고, 둘을 함께 기본키로 삼는다.
2. `Department` 에 `employees` 관계를 둔다 — `Employee` 와 `back_populates` 로 짝을 맞추고, 로딩 방식을 `lazy="select"` 로 명시한다.
3. `Employee` 에 `departments.id` 를 가리키는 외래키 컬럼 `department_id` 와, 반대 방향 관계 `department` 를 둔다.
4. `Student.courses` 와 `Course.students` 를 같은 연결 테이블(`secondary`)과 `back_populates` 로 묶는다.
5. 모든 테이블을 만들고 세션 팩토리 `Session` 을 만든다.

2단계 — 1:N 데이터
6. 부서 「개발팀」 · 「디자인팀」을 만들고, 관계 컬렉션에 `append` 해서 개발팀에 Alice · Bob, 디자인팀에 Charlie 를 넣는다.
7. 부서 두 개만 `add_all` 하고 커밋한다(직원은 따로 `add` 하지 않는다).
8. 「개발팀」을 조회해 부서 이름과 직원 목록을, 「Alice」를 조회해 그 직원의 부서를 찍는다.

3단계 — N:M 데이터
9. 학생 김철수 · 이영희, 과목 「Python 기초」 · 「데이터분석」 · 「웹개발」을 만든다.
10. `extend` 로 김철수에게 Python 기초 · 데이터분석을, 이영희에게 Python 기초 · 웹개발을 잇고, 학생 둘만 `add_all` 해 커밋한다.
11. 김철수의 과목 목록과 「Python 기초」의 수강생 목록을 찍는다.

4단계 — 로딩 전략
12. 새 세션에서 첫 부서를 기본(lazy) 방식으로 읽어 직원 목록을 찍는다.
13. 첫 부서를 `joinedload` 옵션으로 읽어 직원 목록을 찍는다.
14. 모든 부서를 `selectinload` 옵션으로 읽어, 부서마다 이름과 직원 목록을 찍는다.
15. 마지막에 다섯 로딩 전략을 요약하는 줄을 찍는다(시작 코드에 채워 둔 줄).

**시작 코드**

```python
from sqlalchemy import create_engine, Column, Integer, String  # TODO: FK 와 연결 테이블에 필요한 것도 가져온다
from sqlalchemy.orm import declarative_base, sessionmaker  # TODO: 관계 정의와 로딩 옵션에 필요한 것도 가져온다

engine = create_engine("sqlite:///:memory:", echo=False)
Base = declarative_base()

# TODO: N:M 연결 테이블 student_course

class Department(Base):
    __tablename__ = "departments"
    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    # TODO: employees 관계 (1:N, 양방향, lazy="select")

    def __repr__(self):
        return f"Department(id={self.id}, name='{self.name}')"

class Employee(Base):
    __tablename__ = "employees"
    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    # TODO: department_id 외래키
    # TODO: department 관계 (N:1, 양방향)

    def __repr__(self):
        return f"Employee(id={self.id}, name='{self.name}')"

class Student(Base):
    __tablename__ = "students"
    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    # TODO: courses 관계 (N:M)

    def __repr__(self):
        return f"Student(id={self.id}, name='{self.name}')"

class Course(Base):
    __tablename__ = "courses"
    id = Column(Integer, primary_key=True)
    title = Column(String(200))
    # TODO: students 관계 (N:M)

    def __repr__(self):
        return f"Course(id={self.id}, title='{self.title}')"

# TODO: 테이블 생성, Session 팩토리

print("=== 1:N 관계 (Department -> Employee) ===")
# TODO: 부서 · 직원 만들기, 저장, 양방향 조회

print("\n=== N:M 관계 (Student <-> Course) ===")
# TODO: 학생 · 과목 만들기, 연결, 저장, 양방향 조회

print("\n=== Loading 전략 ===")
# TODO: lazy / joinedload / selectinload 로 부서와 직원 읽기

print("\n=== Loading 전략 비교 ===")
print("lazy='select' (기본): 접근 시 개별 쿼리 -> N+1 문제")
print("joinedload:           JOIN으로 한 번에 -> 1:1, N:1에 적합")
print("selectinload:         SELECT ... IN (...) -> 1:N에 적합")
print("subqueryload:         서브쿼리로 로드 -> 복잡한 관계에")
print("lazy='dynamic':       쿼리 객체 반환 -> 추가 필터링 가능")
```

**확인 방법** — `python sqlalchemy-relationships.py` 로 돌려, 개발팀 줄에 Alice · Bob 이, Alice 의 부서 줄에 개발팀이, 김철수의 과목 줄에 Python 기초 · 데이터분석이, Python 기초 수강생 줄에 김철수 · 이영희가 보이는지, 그리고 `SelectIn:` 줄이 부서마다 하나씩 찍히는지 본다.
`echo=True` 로 바꿔 돌리면 각 전략에서 SQL 이 몇 번 나가는지도 볼 수 있다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
