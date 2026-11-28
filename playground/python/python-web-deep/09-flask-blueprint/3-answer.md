# python/python-web-deep/09 — Flask Blueprint와 팩토리 패턴 — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 세 줄 — 첫 메서드를 6칸 오른쪽 정렬, 경로는 `/` 로 끝난다

**출력**

```text
products_bp 라우트:
     GET /api/products/ -> list_products
     GET /api/products/<int:id> -> get_product
    POST /api/products/ -> create_product
```

**왜 그런가**
- 데코레이터가 붙은 차례대로 `routes` 에 쌓이므로 세 줄이 정의 순서로 나온다.
- 전체 경로는 `'/api/products' + '/'` 를 그냥 이어 붙인 것이라 `/api/products/` 처럼 `/` 로 끝난다.
- `{methods[0]:>6}` 은 6칸 오른쪽 정렬이라 `GET` 은 앞에 공백 셋이, `POST` 는 둘이 더 붙는다 — 앞의 공백 두 칸과 합쳐진다.
- `<int:id>` 는 시뮬레이션에서 그냥 문자열이라 그대로 찍힌다.
- 근거: 2-summary 「동작 방식 (1)」.

### 2. 설정 → 확장 → Blueprint 등록 둘 → 등록 목록

**출력**

```text
앱 생성:
  설정: development
  확장: ['db', 'migrate', 'cors']
  Blueprint 등록: auth (prefix=/auth)
  Blueprint 등록: products (prefix=/api/products)

등록된 Blueprint: ['auth', 'products']
```

**왜 그런가**
- `create_app` 안에서 설정을 합친 뒤 `설정:` 을 찍고, `init_extensions` 가 `확장:` 을 찍고, 그다음 `register_blueprint` 가 두 번 불리며 등록 줄을 찍는다.
- `url_prefix` 를 넘기지 않았으므로 처음 만들 때의 접두사가 그대로 찍힌다.
- `blueprints` 는 dict 라 넣은 순서대로 키가 나온다.
- 근거: 2-summary 「동작 방식 (4)」 · 「구현 세부사항 대 언어 보장」.

### 3. 등록 줄은 `/v2/auth`, 저장된 경로는 `/auth/login`

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
  Blueprint 등록: auth (prefix=/v2/auth)
/auth/login
```

**왜 그런가**
- 시뮬레이션의 `route` 는 데코레이트 순간 `'/auth' + '/login'` 을 계산해 `routes` 에 넣었다.
- `register_blueprint(bp, url_prefix='/v2/auth')` 는 `bp.url_prefix` 속성만 바꾸고 `routes` 를 다시 계산하지 않는다.
- 등록 줄은 바뀐 속성을 찍으므로 둘이 어긋난다.
- 이것은 시뮬레이션 코드의 동작이지 실제 Flask 의 동작이 아니다.
- 근거: 2-summary 「동작 방식 (3)」 · 「어디서 틀리나 1」.

### 4. 에러 없이 빈 설정의 앱이 만들어진다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
- `configs.get('staging', {})` 가 빈 dict 를 돌려주므로 `app.config.update({})` 는 아무것도 넣지 않는다.
- `app.config` 는 `{}` 그대로이고, 에러는 나지 않는다.
- `  설정: staging` 줄은 그래도 찍히고, 확장 · Blueprint 등록도 그대로 진행된다.

**왜 그런가**
- `dict.get` 의 두 번째 인자는 키가 없을 때의 기본값이다.
- 그래서 오타가 조용히 통과하고, `DATABASE_URL` 이 없다는 사실은 나중에야 드러난다.
- 근거: 2-summary 「동작 방식 (4)」 · 「어디서 틀리나 3」.

### 5. 호출마다 원하는 설정으로 새 앱을 만들 수 있어서다

- 모듈 전역 앱은 import 될 때 한 번 만들어지고 설정도 그때 굳는다.
- 팩토리는 부를 때마다 새 `Flask` 인스턴스를 만들고 넘긴 이름의 설정을 넣는다.
- 그래서 테스트는 `create_app('testing')` 으로 `TESTING: True` · `sqlite:///test.db` 를 쓰는 앱을 개발용 앱과 따로 만든다.
- 원본 팁 · 주석이 이것을 「테스트 시 다른 설정으로 앱을 만들 수 있다」 · 「테스트 격리에 필수」라고 한다.
- 근거: 2-summary 「동작 방식 (4)」 · 「어디서 틀리나 7」.

### 6. 모델과 앱 패키지가 서로를 import 하는 고리가 생긴다

- `app/__init__.py` 가 `db` 를 만들면서 모델을 import 하고, 모델이 `from app import db` 를 하면 두 모듈이 서로를 import 한다.
- 파이썬은 모듈을 위에서 아래로 실행하므로, 고리 안에서 아직 실행되지 않은 줄의 이름을 찾으면 import 가 실패한다.
- `extensions.py` 는 다른 앱 모듈을 import 하지 않는 바닥이라 모델 · 라우트가 거기서 `db` 를 가져가도 고리가 없다.
- 앱과의 결합은 앱이 생긴 뒤 `create_app` 안의 `db.init_app(app)` 이 맡는다 — 그래서 같은 `db` 를 다른 앱(테스트용)에도 다시 묶을 수 있다.
- 근거: 2-summary 「동작 방식 (5)」 · 「어디서 틀리나 6」. 고리가 실패하는 과정의 설명은 (원본에 근거 없음 — 추론).

### 7. 패키지가 다 실행되기 전에 Blueprint 모듈을 불러오는 순환 임포트

- 함수 안의 `import` 는 함수가 호출될 때 실행된다.
- `create_app` 이 불릴 때는 `app` 패키지의 `__init__.py` 가 이미 끝까지 실행된 뒤다.
- 그래서 `auth` 모듈이 `app.extensions` 나 모델을 import 해도 덜 실행된 모듈을 만나지 않는다.
- 근거: 2-summary 「동작 방식 (5)」 마지막 불릿. (원본에 근거 없음 — 추론)

### 8. 나중에 넘긴 Blueprint 하나만 남는다

- `self.blueprints[bp.name] = bp` 는 이름을 키로 쓰므로 두 번째가 첫 번째를 덮는다.
- 에러는 나지 않고 등록 줄은 두 번 찍히지만, `list(app.blueprints.keys())` 에는 `'auth'` 하나만 있다.
- 이것은 시뮬레이션의 동작이다.
- 근거: 2-summary 「동작 방식 (3)」 · 「어디서 틀리나 2」.

### 9. 없다 — 저장만 되고 불리지 않는다

- `before_request` 는 `before_request_funcs` 리스트에, `errorhandler(404)` 는 `error_handlers[404]` 에 함수를 넣을 뿐이다.
- 시뮬레이션에는 요청을 처리하는 코드가 없으므로 저장된 함수를 꺼내 부르는 곳도 없다.
- 덧붙여 같은 코드에 핸들러를 두 번 붙이면 dict 라서 나중 것만 남는다.
- 근거: 2-summary 「동작 방식 (2)」 · 「어디서 틀리나 5」.

### 10. 데코레이터가 받은 함수를 바꾸지 않고 그대로 돌려주기 때문이다

- `@auth_bp.route('/login', methods=['POST'])` 는 `login = auth_bp.route('/login', methods=['POST'])(login)` 과 같다.
- 안쪽 `decorator(func)` 는 `routes` 에 등록한 뒤 `return func` 로 원래 함수를 돌려준다.
- 그래서 `login` 이름에는 원래 함수가 다시 들어가고, `login()` 은 `{'message': 'Login successful'}` 를 돌려준다.
- 데코레이터가 감싼 새 함수를 돌려주는 경우와 대비되는 「등록만 하는 데코레이터」 꼴이다.
- 근거: 2-summary 「동작 방식 (1)」.

## 실습 정답

### 실습 1. Flask Blueprint · 앱 팩토리 시뮬레이터 만들기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. 생성자 · 빈 목록 셋 | `Blueprint.__init__` 의 `self.routes` · `self.before_request_funcs` · `self.error_handlers` |
| 2. 기본 `['GET']` · 데코레이터 반환 | `route` 의 `methods = methods or ['GET']` · `return decorator` |
| 3. 전체 경로 저장 · `func` 반환 | `decorator` 의 `full_rule = self.url_prefix + rule` · `self.routes.append(...)` · `return func` |
| 4. 요청 전 훅 | `before_request` 의 `self.before_request_funcs.append(func)` |
| 5. 에러 핸들러 | `errorhandler` 의 `self.error_handlers[code] = func` |
| 6. 앱 저장소 셋 | `Flask.__init__` 의 `self.blueprints` · `self.config` · `self.extensions` |
| 7. 접두사 재정의 · 이름으로 저장 · 출력 | `register_blueprint` 의 `if url_prefix: bp.url_prefix = url_prefix` · `self.blueprints[bp.name] = bp` |
| 8. 인증 라우트 셋 | `auth_bp = Blueprint('auth', ...)` · `login` · `register` · `logout` |
| 9. 상품 라우트 셋 | `products_bp = Blueprint('products', ...)` · `list_products` · `get_product` · `create_product` |
| 10. 라우트 목록 출력 | `for rule, methods, func in auth_bp.routes:` 두 반복문 |
| 11. 새 앱 · 설정 합치기 | `create_app` 의 `configs` · `app.config.update(configs.get(config_name, {}))` |
| 12. 설정 출력 → 확장 → 등록 → 반환 | `print(f"  설정: …")` · `init_extensions(app)` · `app.register_blueprint(...)` 두 번 · `return app` |
| 13. 확장 셋 · 키 목록 출력 | `init_extensions` 의 `app.extensions['db']` 등 |
| 14. 개발용 앱 · 목록 출력 | `app = create_app('development')` · `list(app.blueprints.keys())` |
| 15. 나머지 출력 | `structure` · 실제 Flask 코드 문자열 · 핵심 정리 `print` |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`python/python-web-deep/reference/flask-blueprint.py`

```python
# [웹 프레임워크 심화] Flask Blueprint와 팩토리 패턴
# 설명: Blueprint로 모듈화, 앱 팩토리 패턴, 대규모 프로젝트 구조
# 팁: Flask Blueprint는 라우트와 에러 핸들러를 모듈로 분리하는 패턴이다. App Factory(create_app)로 앱을 생성하면 테스트 시 다른 설정으로 앱을 만들 수 있다. 확장은 extensions.py에 정의하고 init_app()으로 지연 초기화하여 순환 임포트를 방지한다.

"""Flask Blueprint와 팩토리 패턴"""

# === Flask 시뮬레이션 ===
# Blueprint: 기능 단위로 라우트/핸들러를 묶는 모듈
class Blueprint:
    """Flask Blueprint 시뮬레이션"""
    # 이름, import 위치, URL 접두사
    def __init__(self, name: str, import_name: str, url_prefix: str = ''):
        self.name = name
        self.import_name = import_name
        self.url_prefix = url_prefix
        # 등록된 라우트들
        self.routes = []
        # before_request 훅 함수들
        self.before_request_funcs = []
        # 에러 핸들러: status code → handler
        self.error_handlers = {}

    # 라우트 등록 데코레이터
    def route(self, rule: str, methods=None):
        methods = methods or ['GET']
        def decorator(func):
            # url_prefix와 결합한 전체 경로
            full_rule = self.url_prefix + rule
            self.routes.append((full_rule, methods, func))
            return func
        return decorator

    # 요청 전 훅 (인증/검증 등)
    def before_request(self, func):
        self.before_request_funcs.append(func)
        return func

    # 에러 핸들러 등록 (404, 500 등)
    def errorhandler(self, code):
        def decorator(func):
            self.error_handlers[code] = func
            return func
        return decorator

# Flask 앱 본체 시뮬레이션
class Flask:
    def __init__(self, name: str):
        self.name = name
        # 등록된 Blueprint들
        self.blueprints = {}
        # 설정 딕셔너리
        self.config = {}
        # 확장(SQLAlchemy 등) 저장소
        self.extensions = {}

    # Blueprint 등록 (확장 패턴: 모듈을 앱에 플러그인)
    def register_blueprint(self, bp: Blueprint, url_prefix: str = None):
        # 등록 시점에 url_prefix 재정의 가능
        if url_prefix:
            bp.url_prefix = url_prefix
        self.blueprints[bp.name] = bp
        print(f"  Blueprint 등록: {bp.name} (prefix={bp.url_prefix})")

# === 1. Blueprint 모듈화 ===
print("=== 1. Blueprint 모듈화 ===")

# auth 블루프린트: 인증 관련 라우트 모음
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

# 로그인 엔드포인트
@auth_bp.route('/login', methods=['POST'])
def login():
    return {'message': 'Login successful'}

# 회원가입 엔드포인트
@auth_bp.route('/register', methods=['POST'])
def register():
    return {'message': 'User registered'}

# 로그아웃 엔드포인트
@auth_bp.route('/logout', methods=['POST'])
def logout():
    return {'message': 'Logged out'}

# products 블루프린트: 상품 도메인 라우트
products_bp = Blueprint('products', __name__, url_prefix='/api/products')

# 상품 목록
@products_bp.route('/', methods=['GET'])
def list_products():
    return {'products': []}

# 상품 단건 조회 (URL 파라미터)
@products_bp.route('/<int:id>', methods=['GET'])
def get_product(id):
    return {'product': {'id': id}}

# 상품 생성
@products_bp.route('/', methods=['POST'])
def create_product():
    return {'message': 'Product created'}

# 등록된 라우트 확인
print("auth_bp 라우트:")
for rule, methods, func in auth_bp.routes:
    print(f"  {methods[0]:>6} {rule} -> {func.__name__}")

print("\nproducts_bp 라우트:")
for rule, methods, func in products_bp.routes:
    print(f"  {methods[0]:>6} {rule} -> {func.__name__}")

# === 2. 앱 팩토리 패턴 ===
print("\n=== 2. 앱 팩토리 패턴 ===")

# 팩토리 함수: 환경별 설정으로 앱 인스턴스 생성 (테스트 격리에 필수)
def create_app(config_name: str = 'development') -> Flask:
    """Flask 앱 팩토리"""
    app = Flask(__name__)

    # 환경별 설정 로드
    configs = {
        'development': {'DEBUG': True, 'DATABASE_URL': 'sqlite:///dev.db'},
        'production': {'DEBUG': False, 'DATABASE_URL': 'postgresql://...'},
        'testing': {'DEBUG': True, 'TESTING': True, 'DATABASE_URL': 'sqlite:///test.db'},
    }
    app.config.update(configs.get(config_name, {}))
    print(f"  설정: {config_name}")

    # 확장 초기화 (DB, Migrate, CORS 등)
    init_extensions(app)

    # Blueprint 등록 (모든 라우트 활성화)
    app.register_blueprint(auth_bp)
    app.register_blueprint(products_bp)

    return app

# 확장 초기화: init_app() 패턴 — extension은 모듈 전역에서 생성하고 앱에 바인딩만 함
def init_extensions(app: Flask):
    """확장 초기화"""
    # 실제로는 db.init_app(app), migrate.init_app(app, db) 등
    app.extensions['db'] = 'SQLAlchemy initialized'
    app.extensions['migrate'] = 'Migrate initialized'
    app.extensions['cors'] = 'CORS initialized'
    print(f"  확장: {list(app.extensions.keys())}")

# 앱 생성 데모
print("\n앱 생성:")
app = create_app('development')
print(f"\n등록된 Blueprint: {list(app.blueprints.keys())}")

# === 3. 프로젝트 구조 ===
print("\n=== 3. 대규모 프로젝트 구조 ===")
# 도메인 단위 디렉토리 구조 (확장 패턴: 기능별 패키지)
structure = """
myproject/
├── app/
│   ├── __init__.py          # create_app() 팩토리
│   ├── extensions.py        # db, migrate, cors 등
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   └── product.py
│   ├── auth/
│   │   ├── __init__.py      # auth_bp = Blueprint('auth', ...)
│   │   ├── routes.py        # @auth_bp.route(...)
│   │   ├── services.py      # 비즈니스 로직
│   │   └── schemas.py       # 마시멜로/Pydantic 스키마
│   ├── products/
│   │   ├── __init__.py
│   │   ├── routes.py
│   │   ├── services.py
│   │   └── schemas.py
│   ├── common/
│   │   ├── decorators.py    # 공통 데코레이터
│   │   └── errors.py        # 에러 핸들러
│   └── templates/
├── config.py                # 설정 클래스
├── tests/
│   ├── conftest.py          # pytest fixture
│   ├── test_auth.py
│   └── test_products.py
├── migrations/
├── requirements.txt
└── wsgi.py                  # app = create_app()
"""
print(structure)

# === 4. 실제 Flask 코드 패턴 ===
print("=== 4. 실제 Flask 코드 ===")
# extensions.py에서 확장 인스턴스를 모듈 전역으로 만들고 init_app으로 지연 바인딩
# → 순환 임포트 방지 + 테스트 시 다른 앱에 같은 확장 재사용 가능
print("""
# app/__init__.py
from flask import Flask
from .extensions import db, migrate, cors

def create_app(config_name='development'):
    app = Flask(__name__)
    app.config.from_object(f'config.{config_name.capitalize()}Config')

    # 확장 초기화
    db.init_app(app)
    migrate.init_app(app, db)
    cors.init_app(app)

    # Blueprint 등록
    from .auth import auth_bp
    from .products import products_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(products_bp, url_prefix='/api/products')

    # 에러 핸들러
    from .common.errors import register_error_handlers
    register_error_handlers(app)

    return app

# extensions.py
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS

db = SQLAlchemy()
migrate = Migrate()
cors = CORS()
""")

print("=== 핵심 정리 ===")
print("Blueprint: 라우트/에러핸들러를 모듈로 분리")
print("App Factory: create_app()으로 앱 인스턴스 생성")
print("Extensions: init_app() 패턴으로 지연 초기화")
print("구조: 기능별 디렉토리 (auth/, products/ 등)")
print("장점: 테스트 용이, 순환 임포트 방지, 설정 분리")
```

**실행 결과** — 원본 예제(`component`)를 실제로 돌린 출력이다. 환경 `Python 3.12.3` · 2026-11-28 · exit 0 · 두 번 돌려 출력이 같았다.

````text
$ python3 -I example.py
=== 1. Blueprint 모듈화 ===
auth_bp 라우트:
    POST /auth/login -> login
    POST /auth/register -> register
    POST /auth/logout -> logout

products_bp 라우트:
     GET /api/products/ -> list_products
     GET /api/products/<int:id> -> get_product
    POST /api/products/ -> create_product

=== 2. 앱 팩토리 패턴 ===

앱 생성:
  설정: development
  확장: ['db', 'migrate', 'cors']
  Blueprint 등록: auth (prefix=/auth)
  Blueprint 등록: products (prefix=/api/products)

등록된 Blueprint: ['auth', 'products']

=== 3. 대규모 프로젝트 구조 ===

myproject/
├── app/
│   ├── __init__.py          # create_app() 팩토리
│   ├── extensions.py        # db, migrate, cors 등
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   └── product.py
│   ├── auth/
│   │   ├── __init__.py      # auth_bp = Blueprint('auth', ...)
│   │   ├── routes.py        # @auth_bp.route(...)
│   │   ├── services.py      # 비즈니스 로직
│   │   └── schemas.py       # 마시멜로/Pydantic 스키마
│   ├── products/
│   │   ├── __init__.py
│   │   ├── routes.py
│   │   ├── services.py
│   │   └── schemas.py
│   ├── common/
│   │   ├── decorators.py    # 공통 데코레이터
│   │   └── errors.py        # 에러 핸들러
│   └── templates/
├── config.py                # 설정 클래스
├── tests/
│   ├── conftest.py          # pytest fixture
│   ├── test_auth.py
│   └── test_products.py
├── migrations/
├── requirements.txt
└── wsgi.py                  # app = create_app()

=== 4. 실제 Flask 코드 ===

# app/__init__.py
from flask import Flask
from .extensions import db, migrate, cors

def create_app(config_name='development'):
    app = Flask(__name__)
    app.config.from_object(f'config.{config_name.capitalize()}Config')

    # 확장 초기화
    db.init_app(app)
    migrate.init_app(app, db)
    cors.init_app(app)

    # Blueprint 등록
    from .auth import auth_bp
    from .products import products_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(products_bp, url_prefix='/api/products')

    # 에러 핸들러
    from .common.errors import register_error_handlers
    register_error_handlers(app)

    return app

# extensions.py
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS

db = SQLAlchemy()
migrate = Migrate()
cors = CORS()

=== 핵심 정리 ===
Blueprint: 라우트/에러핸들러를 모듈로 분리
App Factory: create_app()으로 앱 인스턴스 생성
Extensions: init_app() 패턴으로 지연 초기화
구조: 기능별 디렉토리 (auth/, products/ 등)
장점: 테스트 용이, 순환 임포트 방지, 설정 분리
````

**풀이 요점**
- `route` · `errorhandler` 는 「인자 → 데코레이터 → 함수」 2단 구조이고, `before_request` 는 함수를 바로 받는 1단 구조다.
- 데코레이터는 등록만 하고 `func` 를 그대로 돌려줘야 함수 이름이 원래 함수로 남는다.
- 전체 경로를 데코레이트 때 계산하므로, 이 시뮬레이션에서는 등록 시 접두사를 바꿔도 저장된 경로가 따라오지 않는다.
- 팩토리 안의 차례(설정 → 확장 → Blueprint → 반환)가 곧 2절 출력의 차례다.
- `configs.get(config_name, {})` 는 모르는 이름을 에러 없이 빈 설정으로 넘긴다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 원본 예제를 `Python 3.12.3` 에서 2회 돌렸다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
