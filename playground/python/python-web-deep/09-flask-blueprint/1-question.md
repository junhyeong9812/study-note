# python/python-web-deep/09 — Flask Blueprint와 팩토리 패턴 — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 상품 Blueprint 의 라우트 목록을 찍으면 (예측)

```python
# 질문용 발췌
products_bp = Blueprint('products', __name__, url_prefix='/api/products')

@products_bp.route('/', methods=['GET'])
def list_products(): return {'products': []}

@products_bp.route('/<int:id>', methods=['GET'])
def get_product(id): return {'product': {'id': id}}

@products_bp.route('/', methods=['POST'])
def create_product(): return {'message': 'Product created'}

print("\nproducts_bp 라우트:")
for rule, methods, func in products_bp.routes:
    print(f"  {methods[0]:>6} {rule} -> {func.__name__}")
```

- 몇 줄이 어떤 꼴로 찍히나?
- 첫 줄의 경로 끝은 어떤 글자로 끝나나?

### 2. `create_app('development')` 이 찍는 줄의 차례 (예측)

```python
# 질문용 발췌
print("\n앱 생성:")
app = create_app('development')
print(f"\n등록된 Blueprint: {list(app.blueprints.keys())}")
```

- 「앱 생성:」 다음에 어떤 줄들이 어떤 차례로 나오나?

### 3. 라우트를 붙인 뒤 다른 접두사로 등록하면 (예측)

```python
# 질문용 발췌 — 원본의 Blueprint · Flask 시뮬레이션 클래스를 쓴다
bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/login', methods=['POST'])
def login(): return {'message': 'Login successful'}

app = Flask(__name__)
app.register_blueprint(bp, url_prefix='/v2/auth')
print(bp.routes[0][0])
```

- 등록 줄의 `prefix=` 뒤에는 무엇이 찍히나?
- 마지막 줄에는 어떤 경로가 찍히나?

### 4. 목록에 없는 설정 이름으로 팩토리를 부르면 (예측)
- `create_app('staging')` 을 부르면 에러가 나나?
- 만들어진 앱의 `app.config` 에는 무엇이 들어 있나?

### 5. 앱을 모듈 전역 대신 팩토리로 만드는 까닭 (왜)
- 모듈 맨 위의 `app = Flask(...)` 대신 `create_app(config_name)` 을 쓰면 테스트에서 무엇이 쉬워지나?

### 6. 확장을 `extensions.py` 에 두고 `init_app` 으로 묶는 까닭 (왜)
- `db` 를 `app/__init__.py` 에서 앱과 함께 만들면 모델 모듈과의 사이에 어떤 문제가 생기나?

### 7. Blueprint import 를 `create_app` 함수 안에 둔 까닭 (왜)
- 실제 Flask 코드에서 `from .auth import auth_bp` 를 패키지 맨 위가 아니라 `create_app` 안에 둔 것은 무엇을 피하려는 것인가?

### 8. 같은 이름의 Blueprint 를 두 번 등록하면 (경계)
- 시뮬레이션의 `register_blueprint` 에 이름이 `'auth'` 인 서로 다른 Blueprint 둘을 차례로 넘기면 `app.blueprints` 에는 무엇이 남나?

### 9. `before_request` · `errorhandler` 로 붙인 함수는 언제 불리나 (경계)
- 시뮬레이션에서 `@bp.before_request` 와 `@bp.errorhandler(404)` 로 등록한 함수가 실제로 실행되는 순간이 있나?

### 10. 데코레이터를 붙인 `login` 을 직접 부르기 (연결)
- `@auth_bp.route('/login', methods=['POST'])` 를 붙인 뒤에도 `login()` 을 직접 부르면 원래 함수처럼 dict 가 나오는 것은 데코레이터의 어떤 성질 때문인가?

## 실습

### 실습 1. Flask Blueprint · 앱 팩토리 시뮬레이터 만들기

**만들 것** — Flask 를 설치하지 않고 `Blueprint` · `Flask` 를 흉내 낸 클래스를 만들어, 두 Blueprint 에 라우트를 모으고 앱 팩토리로 앱을 만들어 등록 과정을 출력한다.

**준비물** — 파이썬만 있으면 된다. Flask 는 import 하지 않는다 — `Blueprint` · `Flask` 를 흉내 낸 클래스를 직접 만든다.

**요구 조건**

1단계 — `Blueprint` 클래스
1. 생성자는 `name` · `import_name` · `url_prefix`(기본 빈 문자열)를 저장하고, 빈 `routes` 리스트 · 빈 `before_request_funcs` 리스트 · 빈 `error_handlers` dict 를 만든다.
2. `route(rule, methods=None)` 는 `methods` 가 없으면 `['GET']` 으로 두고, 데코레이터를 돌려준다.
3. 그 데코레이터는 `url_prefix + rule` 로 전체 경로를 만들어 `(전체 경로, methods, func)` 를 `routes` 에 넣고 `func` 를 그대로 돌려준다.
4. `before_request(func)` 는 `func` 를 `before_request_funcs` 에 넣고 돌려준다.
5. `errorhandler(code)` 는 `error_handlers[code] = func` 로 등록하고 `func` 를 돌려주는 데코레이터를 돌려준다.

2단계 — `Flask` 클래스
6. 생성자는 `name` 을 저장하고 빈 `blueprints` · `config` · `extensions` dict 를 만든다.
7. `register_blueprint(bp, url_prefix=None)` 는 `url_prefix` 가 주어지면 `bp.url_prefix` 를 그것으로 바꾸고, `bp.name` 을 키로 `blueprints` 에 넣은 뒤 등록 줄을 출력한다.

3단계 — 두 Blueprint
8. `auth_bp`(이름 `'auth'`, 접두사 `/auth`)에 POST 라우트 `/login` · `/register` · `/logout` 을 붙인다 — 각각 `login` · `register` · `logout` 함수가 메시지 dict 를 돌려준다.
9. `products_bp`(이름 `'products'`, 접두사 `/api/products`)에 GET `/` → `list_products`, GET `/<int:id>` → `get_product(id)`, POST `/` → `create_product` 를 붙인다.
10. 두 Blueprint 의 `routes` 를 차례로 돌며 첫 메서드 · 전체 경로 · 함수 이름을 한 줄씩 출력한다.

4단계 — 앱 팩토리
11. `create_app(config_name='development')` 는 새 `Flask` 를 만들고, `development` · `production` · `testing` 설정 dict 중 이름에 맞는 것을 `app.config` 에 합친다(모르는 이름이면 빈 dict).
12. 설정 이름을 출력한 뒤 `init_extensions(app)` 을 부르고, `auth_bp` · `products_bp` 를 등록하고, 앱을 돌려준다.
13. `init_extensions(app)` 은 `app.extensions` 에 `'db'` · `'migrate'` · `'cors'` 를 넣고 키 목록을 출력한다.
14. `'development'` 로 앱을 하나 만들고 등록된 Blueprint 이름 목록을 출력한다.

5단계 — 나머지 출력
15. 프로젝트 구조 · 실제 Flask 코드 · 핵심 정리 출력은 시작 코드에 채워져 있다 — 그대로 둔다.

**시작 코드**

```python
"""Flask Blueprint와 팩토리 패턴"""

# === Flask 시뮬레이션 ===
class Blueprint:
    """Flask Blueprint 시뮬레이션"""
    def __init__(self, name: str, import_name: str, url_prefix: str = ''):
        # TODO: name · import_name · url_prefix 저장
        # TODO: routes · before_request_funcs (빈 리스트), error_handlers (빈 dict)
        pass

    def route(self, rule: str, methods=None):
        # TODO: methods 가 없으면 ['GET']
        # TODO: decorator(func) — 전체 경로를 만들어 (경로, methods, func) 를 routes 에 넣고 func 반환
        # TODO: decorator 반환
        pass

    def before_request(self, func):
        # TODO
        pass

    def errorhandler(self, code):
        # TODO: code → func 를 등록하는 데코레이터 반환
        pass

class Flask:
    def __init__(self, name: str):
        self.name = name
        # TODO: blueprints · config · extensions (빈 dict)

    def register_blueprint(self, bp: Blueprint, url_prefix: str = None):
        # TODO: url_prefix 가 주어지면 bp.url_prefix 를 바꾼다
        # TODO: bp.name 을 키로 저장
        print(f"  Blueprint 등록: {bp.name} (prefix={bp.url_prefix})")

# === 1. Blueprint 모듈화 ===
print("=== 1. Blueprint 모듈화 ===")

# TODO: auth_bp 만들기 ('auth', 접두사 '/auth')
# TODO: POST /login    → login()    : {'message': 'Login successful'}
# TODO: POST /register → register() : {'message': 'User registered'}
# TODO: POST /logout   → logout()   : {'message': 'Logged out'}

# TODO: products_bp 만들기 ('products', 접두사 '/api/products')
# TODO: GET  /          → list_products()  : {'products': []}
# TODO: GET  /<int:id>  → get_product(id)  : {'product': {'id': id}}
# TODO: POST /          → create_product() : {'message': 'Product created'}

print("auth_bp 라우트:")
# TODO: auth_bp.routes 를 돌며 출력 — 한 줄의 꼴:
#   print(f"  {methods[0]:>6} {rule} -> {func.__name__}")

print("\nproducts_bp 라우트:")
# TODO: products_bp.routes 도 같은 꼴로

# === 2. 앱 팩토리 패턴 ===
print("\n=== 2. 앱 팩토리 패턴 ===")

def create_app(config_name: str = 'development') -> Flask:
    """Flask 앱 팩토리"""
    # TODO: 새 Flask 인스턴스 (이름은 __name__)

    configs = {
        'development': {'DEBUG': True, 'DATABASE_URL': 'sqlite:///dev.db'},
        'production': {'DEBUG': False, 'DATABASE_URL': 'postgresql://...'},
        'testing': {'DEBUG': True, 'TESTING': True, 'DATABASE_URL': 'sqlite:///test.db'},
    }
    # TODO: config_name 에 맞는 설정을 app.config 에 합친다 (모르는 이름이면 빈 dict)
    # TODO: print(f"  설정: {config_name}")
    # TODO: 확장 초기화
    # TODO: auth_bp · products_bp 등록
    # TODO: app 반환

def init_extensions(app: Flask):
    """확장 초기화"""
    # TODO: 'db' → 'SQLAlchemy initialized', 'migrate' → 'Migrate initialized', 'cors' → 'CORS initialized'
    print(f"  확장: {list(app.extensions.keys())}")

print("\n앱 생성:")
# TODO: 'development' 로 앱 만들기
# TODO: print(f"\n등록된 Blueprint: {list(app.blueprints.keys())}")

# === 3. 프로젝트 구조 === (채워져 있음)
print("\n=== 3. 대규모 프로젝트 구조 ===")
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

# === 4. 실제 Flask 코드 패턴 === (채워져 있음)
print("=== 4. 실제 Flask 코드 ===")
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

**확인 방법** — `python flask-blueprint.py` 로 돌려, 1절의 라우트 여섯 줄(POST 셋 · GET 둘 · POST 하나)과 2절의 「설정 → 확장 → Blueprint 등록 두 줄 → 등록된 Blueprint 목록」 차례가 나오는지 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
