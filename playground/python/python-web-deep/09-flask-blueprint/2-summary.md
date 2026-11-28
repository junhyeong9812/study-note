# python/python-web-deep/09 — Flask Blueprint와 팩토리 패턴 — 정리 (힌트)

> 출처 — study-site 항목 `python/flask-blueprint`(항목 데이터 `data/python/django-flask-deep.json`) · 정답 코드 study-practice `python/python-web-deep/reference/flask-blueprint.py`\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).\
> 실행 — 원본 예제를 `Python 3.12.3` 에서 2회 돌렸다.

## 한눈에 — 쉽게 말하면

**Blueprint 는 「부서별 업무 매뉴얼」이고, 앱 팩토리는 「지점 개설 절차서」다.**
인증 부서와 상품 부서는 각자 매뉴얼을 따로 쓴다.
매뉴얼에는 어떤 요청을 누가 처리하는지 적힌다.
새 지점을 열 때는 절차서를 따른다.
지점 규정(설정)을 정하고, 공용 설비(DB · CORS)를 들이고, 부서 매뉴얼을 꽂는다.
절차서가 있으니 시험용 지점도 같은 절차로 따로 열 수 있다.
Flask 앱도 똑같은 구조다.

| 비유 | 실체 |
|---|---|
| 부서별 업무 매뉴얼 | `Blueprint` (`auth_bp`, `products_bp`) |
| 매뉴얼의 한 줄 「이 요청은 이 담당」 | `@bp.route(...)` 로 등록한 라우트 |
| 지점 개설 절차서 | `create_app()` 팩토리 함수 |
| 지점 규정 | `app.config` |
| 공용 설비 | 확장(`db` · `migrate` · `cors`) |
| 매뉴얼을 지점에 꽂기 | `app.register_blueprint(bp)` |
| 시험용 지점 | `create_app('testing')` |

```text
create_app('development')
   ├─ 설정 넣기      → app.config      (DEBUG, DATABASE_URL …)
   ├─ 확장 붙이기    → app.extensions  (db, migrate, cors)
   └─ Blueprint 꽂기 → app.blueprints  (auth, products)
→ 완성된 app 을 돌려준다
```

> **Blueprint** — 라우트 · 훅 · 에러 핸들러를 기능 단위로 묶어 두었다가 앱에 꽂는 모듈 객체.\
> 예: `auth_bp = Blueprint('auth', __name__, url_prefix='/auth')`.

> **앱 팩토리** — 호출할 때마다 설정을 받아 새 앱 인스턴스를 만들어 돌려주는 함수.\
> 예: `app = create_app('testing')`.

## 이 주제가 답하려는 질문

1. 라우트가 많아질 때 한 파일에 몰지 않고 기능별로 어떻게 나누나?
2. 개발 · 운영 · 테스트 설정이 서로 다른 앱을 같은 코드로 어떻게 만들어 내나?
3. DB 같은 확장 객체를 여러 모듈이 함께 쓰면서 순환 임포트를 어떻게 피하나?
4. 큰 프로젝트의 디렉터리는 어떤 모양이 되나?

## 동작 방식

원본 예제는 실제 Flask 를 import 하지 않는다.
`Blueprint` 와 `Flask` 를 흉내 낸 작은 클래스를 직접 만들어 동작을 보인다.
아래 (1)~(4) 는 그 시뮬레이션 코드의 동작이고, (5)~(6) 은 원본이 글로 보여 주는 실제 Flask 코드의 꼴이다.

### (1) Blueprint 에 라우트 모으기 — `route` 데코레이터

**언제 쓰나** — 인증 · 상품처럼 기능 하나에 속한 엔드포인트를 한 묶음으로 모을 때 쓴다.

> **라우트** — URL 경로와 HTTP 메서드를 처리 함수에 잇는 규칙.\
> 예: `POST /auth/login` → `login()`.

> **데코레이터** — 함수 정의 위에 `@식` 으로 붙여, 정의된 함수를 그 식에 넘겨 처리하게 하는 문법.\
> 예: `@auth_bp.route('/login')` 는 `login = auth_bp.route('/login')(login)` 과 같다.

```text
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['POST'])   ①
def login(): ...                              ②

① route('/login', ['POST']) 가 먼저 실행된다 → 안쪽 함수 decorator 를 돌려준다
② decorator(login) 가 실행된다
     full_rule = self.url_prefix + rule = '/auth' + '/login' = '/auth/login'
     routes.append(('/auth/login', ['POST'], login))
     return login          ← 함수는 손대지 않고 그대로 돌려준다
```

- ① `route` 는 함수를 받지 않고, 함수를 받을 `decorator` 를 만들어 돌려준다(데코레이터 팩토리).
- ② 파이썬이 `def login` 을 만든 직후 `decorator(login)` 을 부른다.
- 이때 접두사와 규칙 문자열을 그냥 이어 붙여 **전체 경로를 그 자리에서 계산해 저장**한다.
- `decorator` 가 `func` 를 그대로 돌려주므로 `login` 이름은 여전히 원래 함수다 — 직접 `login()` 을 부르면 `{'message': 'Login successful'}` 가 나온다.
- `methods` 를 주지 않으면 `methods or ['GET']` 때문에 `['GET']` 이 들어간다.
- 문자열을 이어 붙일 뿐이라 `'/api/products'` + `'/'` 는 끝에 `/` 가 붙은 `'/api/products/'` 가 된다.
- `'/<int:id>'` 도 시뮬레이션에서는 그냥 문자열이다 — 실제로 숫자를 뽑아 내지는 않는다.

라우트 목록은 이렇게 찍는다.

```python
for rule, methods, func in auth_bp.routes:
    print(f"  {methods[0]:>6} {rule} -> {func.__name__}")
```

- `methods[0]` 만 찍으므로 메서드가 여럿이어도 **첫 번째만** 보인다.
- `:>6` 은 6칸 안에서 오른쪽 정렬이라 `GET` 앞에는 공백이 셋, `POST` 앞에는 둘 더 붙는다.
- `func.__name__` 은 함수 이름 문자열(`login`)이다.

### (2) 훅과 에러 핸들러 모으기 — `before_request` · `errorhandler`

**언제 쓰나** — 그 Blueprint 의 요청마다 먼저 할 일(인증 검사 등)이나, 상태 코드별 에러 응답을 한 모듈 안에 둘 때 쓴다.

```text
@bp.before_request         → before_request(func) 가 바로 불린다
                              before_request_funcs.append(func) ; return func

@bp.errorhandler(404)      → errorhandler(404) 가 decorator 를 돌려준다
                              decorator(func) : error_handlers[404] = func ; return func
```

- `before_request` 는 괄호 인자가 없는 평범한 데코레이터다 — 함수를 바로 받는다.
- `errorhandler` 는 상태 코드를 먼저 받는 데코레이터 팩토리다 — `route` 와 같은 2단 구조다.
- `error_handlers` 는 상태 코드를 키로 하는 dict 라 같은 코드에 두 번 붙이면 나중 것이 남는다.
- 시뮬레이션은 이 둘을 **저장만 한다** — 요청을 처리하는 코드가 없으므로 저장된 함수를 부르는 곳도 없다.

### (3) 앱에 Blueprint 꽂기 — `register_blueprint`

**언제 쓰나** — 따로 만든 Blueprint 들을 한 앱에 모아 라우트를 활성화할 때 쓴다.

```text
app.register_blueprint(auth_bp)
   → url_prefix 인자 없음 → 접두사 그대로
   → app.blueprints['auth'] = auth_bp
   → 출력 "  Blueprint 등록: auth (prefix=/auth)"

app.register_blueprint(bp, url_prefix='/v2/auth')
   → bp.url_prefix = '/v2/auth' 로 속성을 바꾼다
   → bp.routes 에 이미 든 '/auth/login' 은 다시 계산하지 않는다
```

- `url_prefix` 를 넘기면 등록 시점에 접두사를 다시 정할 수 있다 — 원본 주석이 「등록 시점에 url_prefix 재정의 가능」이라고 한다.
- 하지만 시뮬레이션에서 바뀌는 것은 `bp.url_prefix` 속성 하나뿐이다.
- (1) 에서 전체 경로는 데코레이트 때 이미 계산해 `routes` 에 넣었으므로, 등록 줄의 `prefix=` 와 저장된 경로가 어긋날 수 있다.
- `blueprints` 는 `bp.name` 을 키로 하는 dict 다 — 같은 이름을 두 번 등록하면 에러 없이 나중 것으로 덮인다.

### (4) 앱 팩토리 — `create_app`

**언제 쓰나** — 환경(개발 · 운영 · 테스트)마다 다른 설정으로 앱을 만들어야 할 때 쓴다.

```text
create_app('development')
  1. app = Flask(__name__)                          새 인스턴스
  2. app.config.update(configs.get(name, {}))       설정 dict 를 합친다
     print "  설정: development"
  3. init_extensions(app)                           확장 3개를 넣는다
     print "  확장: ['db', 'migrate', 'cors']"
  4. register_blueprint(auth_bp)                    print "  Blueprint 등록: auth …"
     register_blueprint(products_bp)                print "  Blueprint 등록: products …"
  5. return app
```

- 1 — 함수를 부를 때마다 새 `Flask` 객체가 생긴다.
- 2 — `configs.get(config_name, {})` 는 모르는 이름이면 빈 dict 를 돌려주므로, 에러 없이 설정이 하나도 안 들어간 앱이 만들어진다. `설정:` 줄은 그래도 찍힌다.
- 3 — 시뮬레이션의 `init_extensions` 는 `app.extensions` 에 `'db'` · `'migrate'` · `'cors'` 키로 문자열을 넣고 키 목록을 찍는다.
- 4 — 등록은 확장 다음이다. 그래서 출력은 「설정 → 확장 → Blueprint 등록」 차례로 나온다.
- 5 — 완성된 앱을 돌려준다. 실제 배포에서는 `wsgi.py` 에서 `app = create_app()` 으로 받는다.

세 환경의 설정은 이렇다.

| 이름 | `DEBUG` | `TESTING` | `DATABASE_URL` |
|---|---|---|---|
| `development` | `True` | 없음 | `sqlite:///dev.db` |
| `production` | `False` | 없음 | `postgresql://...` |
| `testing` | `True` | `True` | `sqlite:///test.db` |

팩토리가 테스트에 좋은 까닭은 이렇다.
모듈 맨 위에 `app = Flask(...)` 를 두면 앱은 import 될 때 한 번 만들어지고 설정도 그때 굳는다.
팩토리를 쓰면 테스트가 `create_app('testing')` 으로 테스트 DB 를 쓰는 앱을 따로 만든다.
원본 주석은 이것을 「테스트 격리에 필수」라고 한다.

> **WSGI 진입점** — 웹 서버가 불러 갈 앱 객체를 두는 파일.\
> 예: `wsgi.py` 의 `app = create_app()`.

### (5) 확장과 `init_app` — 지연 초기화

**언제 쓰나** — DB · 마이그레이션 · CORS 같은 확장 객체를 모델 · 라우트 등 여러 모듈이 import 해 써야 할 때 쓴다.

> **확장** — Flask 에 기능(DB 연결 · 마이그레이션 · CORS 등)을 보태는 별도 라이브러리의 객체.\
> 예: `db = SQLAlchemy()`.

> **지연 초기화** — 객체는 먼저 만들어 두고, 앱과 묶는 일은 앱이 생긴 뒤로 미루는 것.\
> 예: `db.init_app(app)`.

원본이 글로 보여 주는 실제 코드의 꼴은 이렇다.

```text
extensions.py      db = SQLAlchemy()                ← 앱 없이 만든다(모듈 전역)
                   migrate = Migrate() ; cors = CORS()

models/user.py     from app.extensions import db    ← 확장은 extensions 에서 가져온다

app/__init__.py    from .extensions import db, migrate, cors
                   def create_app(config_name='development'):
                       app = Flask(__name__)
                       app.config.from_object(f'config.{config_name.capitalize()}Config')
                       db.init_app(app)              ← 앱이 생긴 뒤에 묶는다
                       migrate.init_app(app, db)
                       cors.init_app(app)
                       from .auth import auth_bp     ← 함수 안에서 import
                       from .products import products_bp
                       app.register_blueprint(auth_bp, url_prefix='/auth')
                       app.register_blueprint(products_bp, url_prefix='/api/products')
                       from .common.errors import register_error_handlers
                       register_error_handlers(app)
                       return app
```

- 확장 객체는 `extensions.py` 에서 앱 없이 모듈 전역으로 만든다.
- `create_app` 안에서 `init_app(app)` 으로 그 앱에 묶기만 한다 — 원본 주석은 이것을 「앱에 바인딩만 함」이라고 한다.
- 원본 주석에 따르면 이로써 순환 임포트를 막고, 테스트 때 다른 앱에 같은 확장을 다시 쓸 수 있다.
- `migrate.init_app(app, db)` 처럼 다른 확장을 함께 넘기는 것도 있다.
- `from_object(f'config.{config_name.capitalize()}Config')` 는 `'development'` 를 `'config.DevelopmentConfig'` 로 바꾼다 — `config.py` 에 환경별 설정 **클래스**를 두는 방식이다.
- 에러 핸들러는 `common/errors.py` 의 `register_error_handlers(app)` 로 한꺼번에 붙인다.

순환 임포트가 왜 생기는지는 이렇다(파이썬 import 동작에서 끌어낸 설명이다).

> **순환 임포트** — 모듈 A 가 B 를 import 하고 B 가 다시 A 를 import 해, 한쪽이 덜 실행된 상태에서 이름을 찾는 일.\
> 예: `app/__init__.py` ↔ `models/user.py`.

```text
나쁜 꼴
app/__init__.py : db = SQLAlchemy(app) 를 여기 둔다 ; from .models import user
models/user.py  : from app import db
                  → app/__init__.py 는 아직 위에서 아래로 실행되는 중이다
                  → 그 시점에 찾는 이름이 아직 없으면 import 가 실패한다

좋은 꼴
models/user.py  : from app.extensions import db
                  → extensions.py 는 다른 app 모듈을 import 하지 않으므로 고리가 없다
```

- 파이썬은 모듈을 처음 import 할 때 위에서 아래로 실행한다.
- 고리 안에서 아직 실행되지 않은 줄의 이름을 가져가려 하면 실패한다.
- `extensions.py` 는 다른 앱 모듈에 기대지 않는 「바닥」이라 누구든 안전하게 가져다 쓴다.
- Blueprint import 를 `create_app` **함수 안**에 둔 것도 같은 결이다 — 함수가 호출될 때에야 실행되므로, 그때는 `app` 패키지가 이미 다 실행된 뒤다.

### (6) 대규모 프로젝트 구조

**언제 쓰나** — 기능이 늘어 한 파일 · 한 폴더로 감당이 안 될 때 기능(도메인) 단위로 패키지를 나눈다.

```text
myproject/
├── app/
│   ├── __init__.py      create_app() 팩토리
│   ├── extensions.py    db, migrate, cors
│   ├── models/          user.py, product.py
│   ├── auth/            __init__(bp 생성) · routes · services · schemas
│   ├── products/        같은 네 파일
│   ├── common/          decorators.py(공통 데코레이터) · errors.py(에러 핸들러)
│   └── templates/
├── config.py            설정 클래스
├── tests/               conftest.py(pytest fixture) · test_auth.py · test_products.py
├── migrations/
├── requirements.txt
└── wsgi.py              app = create_app()
```

- 기능 패키지 하나 = Blueprint 하나다. `__init__.py` 에서 `auth_bp = Blueprint('auth', ...)` 를 만들고 `routes.py` 에서 `@auth_bp.route(...)` 를 붙인다.
- `services.py` 에는 비즈니스 로직, `schemas.py` 에는 마시멜로/Pydantic 스키마를 둔다 — 라우트 함수는 얇게 남는다.
- `tests/conftest.py` 의 fixture 가 팩토리로 테스트용 앱을 만든다.

> **fixture** — pytest 가 테스트 함수에 미리 준비해 넘겨 주는 값.\
> 예: 테스트용 `app` 을 만들어 주는 함수.

## 문법 — 형태와 규칙

```python
# app/auth/__init__.py
from flask import Blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['POST'])
def login():
    return {'message': 'ok'}

# app/__init__.py
from flask import Flask
def create_app(config_name='development'):
    app = Flask(__name__)
    from .auth import auth_bp          # 함수 안에서 import
    app.register_blueprint(auth_bp)
    return app
```

- `Blueprint(이름, import_name, url_prefix=…)` — 이름은 앱 안에서 이 Blueprint 를 가리키는 키다. `import_name` 에는 보통 `__name__` 을 넘긴다.
- `@bp.route(규칙, methods=[…])` — `methods` 를 빼면 `GET` 이다.
- `@bp.before_request` — 괄호 없이 붙인다.
- `@bp.errorhandler(코드)` — 상태 코드를 괄호 안에 넣는다.
- `app.register_blueprint(bp, url_prefix=…)` — 접두사를 등록 시점에 다시 정할 수 있다.
- 팩토리는 설정 → 확장 → Blueprint → (에러 핸들러) → `return app` 차례가 원본의 꼴이다.
- 확장은 `extensions.py` 에 `객체 = 확장클래스()` 로 두고, 팩토리에서 `객체.init_app(app)` 을 부른다.

## 어디서 틀리나

### 1. 등록 때 바꾼 접두사가 이미 만든 경로에 반영되지 않는다 (시뮬레이션)
시뮬레이션의 `route` 는 데코레이트 순간 `url_prefix + rule` 을 계산해 저장한다.
`register_blueprint(bp, url_prefix='/v2')` 는 속성만 바꾸므로 `routes` 의 경로는 옛 접두사 그대로다.
등록 줄에는 새 접두사가 찍혀서 둘이 어긋나 보인다.

### 2. 같은 이름의 Blueprint 는 조용히 덮인다 (시뮬레이션)
`app.blueprints[bp.name] = bp` 이므로 이름이 같으면 앞의 것이 사라진다.
에러가 나지 않으니 Blueprint 이름은 앱 안에서 겹치지 않게 짓는다.

### 3. 모르는 설정 이름은 에러 없이 빈 설정이 된다
`configs.get(config_name, {})` 때문에 `'staging'` 같은 오타도 통과한다.
`DATABASE_URL` 없는 앱이 만들어지고, 문제는 나중에 DB 를 쓸 때에야 드러난다.

### 4. 라우트 출력은 첫 메서드만 보여 준다
`methods[0]` 만 찍으므로 `['GET', 'POST']` 를 준 라우트도 `GET` 으로만 보인다.
목록이 틀린 게 아니라 출력이 줄인 것이다.

### 5. 훅과 에러 핸들러는 모으기만 한다 (시뮬레이션)
`before_request_funcs` · `error_handlers` 에 저장할 뿐 부르는 코드가 없다.
시뮬레이션에서 훅이 실행되리라 기대하면 안 된다.

### 6. 확장을 앱과 같은 곳에서 만들면 순환 임포트가 난다 (원본 팁)
원본 팁: 확장은 `extensions.py` 에 정의하고 `init_app()` 으로 지연 초기화해 순환 임포트를 막는다.
`app/__init__.py` 에 `db` 를 두고 모델이 `from app import db` 를 하면 고리가 생긴다.

### 7. 앱을 모듈 전역으로 만들면 테스트 설정을 바꾸기 어렵다 (원본 팁)
원본 팁: `create_app` 으로 앱을 생성하면 테스트 때 다른 설정으로 앱을 만들 수 있다.
전역 앱은 import 때 설정이 굳어 테스트 DB 로 갈아 끼우기 어렵다.

### 8. Blueprint 가 나누는 것은 라우트와 에러 핸들러다 (원본 팁)
원본 팁: Blueprint 는 라우트와 에러 핸들러를 모듈로 분리하는 패턴이다.
설정 · 확장은 Blueprint 가 아니라 팩토리와 `extensions.py` 가 맡는다.

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| `@식` 아래 `def` 는 정의 직후 그 식에 함수가 넘겨진다 | 파이썬 언어 |
| `methods or ['GET']` 는 `None` 이면 `['GET']` 이 된다 | 파이썬 언어 |
| `f"{x:>6}"` 는 6칸 오른쪽 정렬이다 | 파이썬 언어(형식 지정) |
| `list(dict.keys())` 가 넣은 순서대로 나온다 | 파이썬 언어 (3.7 이후 — 확인 필요) |
| 모듈은 처음 import 때 위에서 아래로 한 번 실행된다 | 파이썬 언어(import 시스템) |
| 전체 경로가 데코레이트 시점에 굳는다 | 이 시뮬레이션 코드 — 실제 Flask 의 동작이 아니다 |
| 같은 이름 Blueprint 가 덮인다 | 이 시뮬레이션 코드 — 실제 Flask 의 동작이 아니다 |
| 훅이 저장만 되고 불리지 않는다 | 이 시뮬레이션 코드 |
| 확장을 `init_app(app)` 으로 나중에 묶는다 | Flask 확장 라이브러리들의 관례 — 언어가 아니다 |
| 팩토리 이름이 `create_app` 이다 | 관례 |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 라우트가 기능별로 여럿 | 기능마다 Blueprint 하나 | 한 파일에 전부 `@app.route` |
| 개발 · 운영 · 테스트 설정이 다르다 | `create_app(config_name)` | 모듈 전역 `app = Flask(...)` |
| 여러 모듈이 `db` 를 쓴다 | `extensions.py` + `init_app` | `app/__init__.py` 에서 `SQLAlchemy(app)` |
| 팩토리가 Blueprint 를 가져온다 | `create_app` 안에서 import | 패키지 맨 위에서 import |
| 파일 몇 개짜리 작은 실험 | 앱 하나에 바로 라우트 | 디렉터리 구조 전부 |

## 핵심 문장

1. **Blueprint 는 기능 단위로 라우트 · 훅 · 에러 핸들러를 모아 두었다가 `register_blueprint` 로 앱에 꽂는다.**
2. **`route` 는 데코레이터 팩토리다** — 규칙을 받아 데코레이터를 돌려주고, 그 데코레이터는 함수를 등록한 뒤 그대로 돌려준다.
3. **앱 팩토리는 호출마다 설정을 받아 새 앱을 만든다** — 그래서 테스트용 앱을 따로 만들 수 있다.
4. **확장은 `extensions.py` 에서 앱 없이 만들고 `init_app` 으로 나중에 묶는다** — 순환 임포트를 피한다.
5. **큰 프로젝트는 기능별 패키지(`auth/` · `products/`)로 나누고 팩토리 · 확장 · 설정 · 테스트를 제자리에 둔다.**

## 관련 자료

- [flask-sqlalchemy](../10-flask-sqlalchemy/2-summary.md)
- [flask-auth](../11-flask-auth/2-summary.md)
- [flask-testing](../12-flask-testing/2-summary.md)
- 원본: study-site 항목 데이터 `data/python/django-flask-deep.json` 의 `flask-blueprint`

## 용어 풀이

- **Blueprint** — 기능 단위로 라우트 · 훅 · 에러 핸들러를 묶는 모듈 객체.
- **라우트** — URL 경로 + HTTP 메서드를 처리 함수에 잇는 규칙.
- **엔드포인트** — 라우트 하나가 가리키는 처리 지점(`/auth/login` 등).
- **`url_prefix`** — Blueprint 의 모든 경로 앞에 붙는 공통 접두사.
- **데코레이터** — `@식` 으로 함수 정의를 감싸 처리하는 문법.
- **데코레이터 팩토리** — 인자를 받아 데코레이터를 돌려주는 함수(`route` · `errorhandler`).
- **훅(before_request)** — 요청을 처리하기 전에 부르도록 등록하는 함수.
- **에러 핸들러** — 상태 코드(404 · 500 등)에 맞춰 응답을 만드는 함수.
- **앱 팩토리** — 설정을 받아 새 앱 인스턴스를 만들어 돌려주는 함수.
- **확장** — Flask 에 DB · 마이그레이션 · CORS 같은 기능을 보태는 객체.
- **`init_app`** — 미리 만든 확장 객체를 앱에 묶는 메서드.
- **지연 초기화** — 객체 생성과 앱 결합을 나눠 결합을 뒤로 미루는 것.
- **순환 임포트** — 모듈끼리 서로 import 해 덜 실행된 모듈에서 이름을 찾는 일.
- **`app.config`** — 앱 설정을 담는 dict.
- **fixture** — pytest 가 테스트에 준비해 넘기는 값.
- **WSGI 진입점** — 웹 서버가 불러 갈 앱 객체를 두는 파일(`wsgi.py`).
- **services / schemas** — 비즈니스 로직 / 입출력 데이터 모양을 정의하는 파일.

## 더 들어가면

- 실제 Flask 는 Blueprint 의 라우트를 바로 앱에 넣지 않고, 등록할 때 접두사를 적용해 넣는다고 알려져 있다 — 그래서 등록 시 `url_prefix` 재정의가 경로에 반영된다 (확인 필요).
- 실제 Flask 는 이름이 같은 다른 Blueprint 를 등록하면 에러를 낸다고 알려져 있다 (확인 필요).
- 실제 Flask 에서 Blueprint 안의 엔드포인트 이름은 `'auth.login'` 처럼 Blueprint 이름이 앞에 붙고, `url_for('auth.login')` 으로 URL 을 만든다 (확인 필요).
- `flask` 명령은 `create_app` 이라는 이름의 팩토리를 자동으로 찾아 부를 수 있다 (확인 필요).
- 팩토리 패턴에서는 전역 `app` 이 없으므로, 라우트 함수 안에서 현재 앱은 `current_app` 으로 꺼낸다 (확인 필요).
- `bp.before_request` 는 그 Blueprint 의 요청에만, `app.before_request` 는 모든 요청에 걸린다 (확인 필요).
