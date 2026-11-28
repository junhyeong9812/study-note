# python/python-web/06 — Flask 기초 (라우트, 템플릿, Blueprint) — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. `/user/42` 는 정수 42 로 들어오고, `/user/abc` 는 규칙과 맞지 않는다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

`/user/42` → 본문은 `User ID: 42` 이고, `user_id` 는 `int` 다.
`/user/abc` → `user_profile` 은 불리지 않는다.
`abc` 는 정수로 바뀌지 않아 이 규칙과 맞지 않고, 맞는 다른 규칙도 없으므로 404 가 된다.
원본 코드라면 그 404 는 `not_found` 핸들러가 받는다.

**왜 그런가**

`<int:user_id>` 의 `int` 변환기는 그 자리가 정수일 때만 규칙을 맞추고, 값을 `int` 로 바꿔 인자로 넘긴다.
근거: 2-summary 「동작 방식 (1)」.

### 2. `/blog/7` — 등록하지 않으면 그 주소는 없다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

`/blog/7` 로 요청하면 `blog_detail(post_id=7)` 이 불린다.
`register_blueprint` 줄을 지우면 Blueprint 의 라우트가 앱에 활성화되지 않으므로 `/blog/7` 과 맞는 규칙이 없어 404 가 된다.

**왜 그런가**

`url_prefix='/blog'` 는 Blueprint 의 모든 경로 앞에 붙으므로 `'/<int:post_id>'` 는 `/blog/<int:post_id>` 가 된다.
`@blog_bp.route` 는 기록만 해 두고, 앱에 등록해야 살아난다.
근거: 2-summary 「동작 방식 (7)」.

### 3. `'dev-secret'` — 운영 설정은 들어가지 않는다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

쓰이는 비밀 키는 `'dev-secret'` 이다.
`ProductionConfig` 의 `SECRET_KEY` 와 `DEBUG` 는 앱 설정에 들어가지 않는다.

**왜 그런가**

`app.secret_key` 는 `app.config['SECRET_KEY']` 와 같은 자리를 가리킨다.
뒤에 실행된 `from_object(Config)` 가 `Config` 의 대문자 속성 `SECRET_KEY = 'dev-secret'` 을 같은 자리에 넣어 앞의 값을 덮는다.
`ProductionConfig` 는 정의만 되었고 `from_object` 에 넘겨지지 않았다.
근거: 2-summary 「동작 방식 (8)」 · 「어디서 틀리나 6」 (원본에 근거 없음 — 추론).

### 4. 서버가 도는 동안에는 안 찍히고, import 하면 바로 찍힌다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

직접 실행해 서버가 요청을 받는 동안에는 맨 끝 `print` 줄들이 아직 실행되지 않았다.
`app.run(...)` 이 서버가 멈출 때까지 돌아오지 않아서, 그 아래 줄에 닿지 못한다.
다른 모듈이 import 하면 `__name__` 이 `'__main__'` 이 아니라 `app.run` 은 건너뛰고, `print` 줄들은 import 하는 그 순간에 실행된다.

**왜 그런가**

`if __name__ == '__main__':` 은 직접 실행할 때만 참이고, `app.run` 은 막고(blocking) 도는 호출이다.
근거: 2-summary 「동작 방식 (8)」.

### 5. 데코레이터는 아래에서 위로 적용되기 때문이다

`@login_required` 가 위에 있으면 먼저 `@app.route` 가 **감싸기 전의** `dashboard` 를 경로에 등록한다.
그 뒤 `login_required` 가 감싼 함수를 만들어도, 안내판에는 이미 검사 없는 원본이 적혀 있다.
`@app.route` 를 맨 바깥에 두어야 `login_required` 가 감싼 함수가 등록된다.
근거: 2-summary 「동작 방식 (6)」 (원본에 근거 없음 — 추론; 원본 주석은 「route가 가장 바깥」이라는 순서만 밝힌다).

### 6. 엔드포인트 이름이 함수 이름에서 오기 때문이다

엔드포인트 이름은 기본으로 뷰 함수의 `__name__` 이다.
`@wraps` 가 없으면 `login_required` 로 감싼 함수가 모두 `decorated_function` 이라는 같은 이름을 갖게 된다.
그러면 여러 라우트가 같은 엔드포인트 이름을 두고 겹쳐 라우팅에 문제가 생긴다.
`@wraps(f)` 는 원본의 `__name__` 을 감싼 함수에 복사해 이 충돌을 막는다.
근거: 2-summary 「동작 방식 (6)」 · 「어디서 틀리나 5」.

### 7. 키를 알면 「진짜 서명이 붙은 가짜 세션」을 만들 수 있기 때문이다

서명은 키를 모르는 사람이 내용을 고치면 들통나게 하는 장치다.
키가 새면 누구나 `user_id` 를 넣은 세션 쿠키를 만들고 올바른 서명까지 붙일 수 있다.
그러면 `'user_id' not in session` 검사를 그대로 통과한다.
근거: 2-summary 「동작 방식 (6)」 (원본에 근거 없음 — 추론).

### 8. 같은 요청 안에서만 읽을 수 있다

요청 A 의 `after_request` 에서는 읽을 수 있다 — 둘은 같은 요청 컨텍스트 안에 있다.
요청 B 에서는 읽을 수 없다 — 요청 A 가 끝날 때 그 `g` 는 버려지고, B 는 새 `g` 로 시작한다.
요청을 넘어 남길 값은 `session` 에 둔다.
근거: 2-summary 「동작 방식 (5)」 · 「어디서 틀리나 4」.

### 9. `url_for('login', ...)` 과 `find_item(item_id)` 이다

`/dashboard` → `login_required` 안의 `redirect(url_for('login', next=request.url))` 에서 실패한다.
원본에 `login` 엔드포인트가 없어 `url_for` 가 주소를 만들지 못한다.
`/item/1` → `get_item` 첫 줄의 `find_item(item_id)` 에서 실패한다.
`find_item` 이 정의되지 않아 `NameError` 가 나고, 잡히지 않은 예외라 500 으로 이어진다.
둘 다 파일을 불러올 때는 드러나지 않고 그 경로에 요청이 와야 드러난다.
근거: 2-summary 「어디서 틀리나 3」.

### 10. `raise` 와 `except` 의 짝이다

`abort(404)` 는 예외처럼 그 자리에서 함수를 끊고 튀어 나간다 — `raise` 에 해당한다.
`@app.errorhandler(404)` 는 그 에러를 한곳에서 받아 응답을 만든다 — `except` 에 해당한다.
그래서 `abort` 아래의 `return jsonify(item)` 은 실행되지 않는다.
근거: 2-summary 「동작 방식 (4)」.

## 실습 정답

### 실습 1. 라우트 · 요청/응답 · 에러 · 미들웨어 · Blueprint 를 갖춘 Flask 앱

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. 앱 생성 · `secret_key` | `app = Flask(__name__)` · `app.secret_key = ...` |
| 2. `/` → `index.html` | `@app.route('/')` · `index()` |
| 3. `/hello/<name>` | `@app.route('/hello/<name>')` · `hello(name)` |
| 4. `/user/<int:user_id>` | `@app.route('/user/<int:user_id>')` · `user_profile` |
| 5. `/posts` GET · POST | `@app.route('/posts', methods=['GET', 'POST'])` |
| 6. POST → 폼 읽기 · flash · 리다이렉트 | `request.form.get(...)` · `flash(..., 'success')` · `redirect(url_for('posts'))` |
| 7. GET → `page` · `q` | `request.args.get('page', 1, type=int)` · `request.args.get('q', '')` |
| 8. `/api/data` POST · JSON 의 `name` | `methods=['POST']` · `request.get_json()` · `data.get('name', 'anonymous')` |
| 9. 헤더 · 본문 형식 읽기 | `request.headers.get('Authorization')` · `request.content_type` |
| 10. 커스텀 응답 201 | `make_response(jsonify({...}))` · `response.headers['X-Custom-Header']` · `response.status_code = 201` |
| 11. CSV 다운로드 | `download()` 의 `Content-Type` · `Content-Disposition` |
| 12. 404 핸들러 | `@app.errorhandler(404)` · `not_found` |
| 13. 500 핸들러 | `@app.errorhandler(500)` · `internal_error` |
| 14. `/item/<int:item_id>` · `abort(404)` | `get_item` 의 `if item is None: abort(404)` |
| 15. 요청 전 시각 기록 | `@app.before_request` · `g.start_time = ...` |
| 16. 응답 직전 처리 시간 헤더 | `@app.after_request` · `hasattr(g, 'start_time')` · `f'{elapsed:.4f}s'` |
| 17. `@wraps` 로 정보 보존 | `login_required` 안의 `@wraps(f)` |
| 18. 비로그인 → flash · `login` 리다이렉트 | `'user_id' not in session` · `flash(..., 'warning')` · `url_for('login', next=request.url)` |
| 19. `/dashboard` 보호 | `@app.route('/dashboard')` 아래 `@login_required` |
| 20. `blog` Blueprint 와 두 라우트 | `Blueprint('blog', __name__, url_prefix='/blog')` · `blog_list` · `blog_detail` |
| 21. `api` Blueprint 와 `/posts` | `Blueprint('api', __name__, url_prefix='/api/v1')` · `api_posts` |
| 22. Blueprint 등록 | `app.register_blueprint(blog_bp)` · `app.register_blueprint(api_bp)` |
| 23. 설정 클래스 · 상속 · 로드 | `class Config` · `class ProductionConfig(Config)` · `app.config.from_object(Config)` |
| 24. 직접 실행할 때만 서버 | `if __name__ == '__main__': app.run(debug=True, host='0.0.0.0', port=5000)` |
| 25. 핵심 정리 출력 | 파일 맨 끝의 `print(...)` 줄들 |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`python/python-web/reference/flask-basics.py`

```python
# [웹 프레임워크] Flask 기초 (라우트, 템플릿, Blueprint)
# 설명: Flask 앱 구조, 라우트, Jinja2 템플릿, 요청/응답, Blueprint 모듈화
# 팁: Flask는 마이크로 프레임워크로 필요한 것만 추가하는 철학이다. Blueprint로 대규모 앱을 모듈화한다. g 객체는 요청 컨텍스트 내에서 데이터를 공유한다. url_for()는 URL 하드코딩 대신 엔드포인트 이름으로 URL을 생성한다.

# Flask 기초 - 라우트, 템플릿, Blueprint
# pip install flask

# Flask 핵심 객체들 import
# Flask: WSGI 앱 클래스 (Django와 달리 동기 처리, ASGI는 Quart 등 별도 프레임워크)
from flask import (
    Flask, render_template, request, redirect,
    url_for, jsonify, abort, flash, session,
    make_response, g
)
# wraps: 데코레이터 작성 시 원본 함수의 메타데이터 보존
from functools import wraps

# WSGI 애플리케이션 인스턴스 생성
app = Flask(__name__)
# secret_key: 세션/플래시 메시지 서명에 사용 (반드시 비밀)
app.secret_key = 'your-secret-key-here'


# === 1. 기본 라우트 ===
# @app.route: URL을 함수에 매핑하는 데코레이터 (Flask의 핵심 라우팅 방식)
@app.route('/')
def index():
    # render_template: Jinja2 템플릿 렌더링
    return render_template('index.html', title='홈')


@app.route('/hello/<name>')
def hello(name):
    """URL 파라미터"""
    # <name>: URL 변수가 함수 인자로 전달
    return f'Hello, {name}!'


# 변수 컨버터: int, float, path, uuid, string(기본)
@app.route('/user/<int:user_id>')    # int, float, path, uuid 변환기
def user_profile(user_id):
    return f'User ID: {user_id}'


# methods 인자로 허용 HTTP 메서드 지정 (기본은 GET만)
@app.route('/posts', methods=['GET', 'POST'])
def posts():
    """GET/POST 처리"""
    if request.method == 'POST':
        # request.form: form 인코딩된 POST 데이터
        title = request.form.get('title')       # 폼 데이터
        content = request.form.get('content')
        # 저장 로직...
        # flash: 다음 요청까지 유지되는 일회성 메시지 (세션 사용)
        flash('게시글이 작성되었습니다!', 'success')  # 플래시 메시지
        # url_for: 함수 이름으로 URL 생성 (하드코딩 회피)
        return redirect(url_for('posts'))

    # GET: 쿼리 파라미터
    # request.args: 쿼리스트링 dict (type 인자로 자동 캐스팅)
    page = request.args.get('page', 1, type=int)
    search = request.args.get('q', '')
    return render_template('posts.html', page=page, search=search)


# === 2. 요청/응답 처리 ===
@app.route('/api/data', methods=['POST'])
def api_data():
    """JSON 요청/응답"""
    # request.get_json(): 요청 본문 JSON 파싱
    data = request.get_json()               # JSON 요청 본문
    name = data.get('name', 'anonymous')

    # 헤더 접근
    # request.headers: 요청 헤더 dict
    auth_header = request.headers.get('Authorization')
    content_type = request.content_type

    # 커스텀 응답
    # make_response: 응답 객체를 명시적으로 생성하여 헤더/상태 코드 수정 가능
    response = make_response(jsonify({
        'message': f'Hello, {name}!',
        'status': 'success'
    }))
    response.headers['X-Custom-Header'] = 'MyValue'
    response.status_code = 201
    return response


@app.route('/download')
def download():
    """파일 다운로드 응답"""
    # Content-Disposition: 첨부파일로 다운로드 유도
    response = make_response('CSV,데이터,여기')
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = 'attachment; filename=data.csv'
    return response


# === 3. 에러 핸들링 ===
# @errorhandler: 특정 HTTP 에러를 처리하는 핸들러 등록
@app.errorhandler(404)
def not_found(error):
    # 응답에 상태 코드 명시 (튜플 반환 형태)
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': '서버 오류'}), 500

@app.route('/item/<int:item_id>')
def get_item(item_id):
    item = find_item(item_id)
    if item is None:
        # abort: 즉시 HTTP 에러 발생 (예외처럼 동작)
        abort(404)  # 404 에러 발생
    return jsonify(item)


# === 4. 미들웨어 (before/after) ===
# @before_request: 모든 요청 처리 전 실행
@app.before_request
def before_request():
    # g: 요청 컨텍스트 동안 유지되는 임시 저장소
    g.start_time = __import__('time').time()  # 요청 시작 시간

# @after_request: 응답 반환 직전 실행 (응답 객체를 받아 수정)
@app.after_request
def after_request(response):
    # 처리 시간 헤더 추가
    if hasattr(g, 'start_time'):
        elapsed = __import__('time').time() - g.start_time
        response.headers['X-Elapsed-Time'] = f'{elapsed:.4f}s'
    return response


# === 5. 커스텀 데코레이터 ===
# 인증 검사 데코레이터 작성 패턴
def login_required(f):
    # @wraps로 원본 함수의 __name__ 등 보존 (Flask 라우팅에 필요)
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # session: 클라이언트 측 서명된 쿠키 기반 세션
        if 'user_id' not in session:
            flash('로그인이 필요합니다.', 'warning')
            # next 파라미터로 로그인 후 원래 페이지 복귀
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

# 데코레이터 스택: route가 가장 바깥, login_required가 안쪽
@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')


# === 6. Blueprint (모듈화) ===
# Blueprint: 라우트 그룹화 (대규모 앱 분리)
from flask import Blueprint

# blog/routes.py
# url_prefix: 이 Blueprint의 모든 라우트에 자동 적용되는 접두사
blog_bp = Blueprint('blog', __name__, url_prefix='/blog')

# Blueprint 데코레이터로 라우트 등록 (앱 등록 후 활성화)
@blog_bp.route('/')
def blog_list():
    return render_template('blog/list.html')

@blog_bp.route('/<int:post_id>')
def blog_detail(post_id):
    return render_template('blog/detail.html', post_id=post_id)


# api/routes.py
# 버전별 API를 별도 Blueprint로 분리하는 패턴
api_bp = Blueprint('api', __name__, url_prefix='/api/v1')

@api_bp.route('/posts')
def api_posts():
    return jsonify({'posts': []})


# app.py에서 등록
# register_blueprint: Blueprint를 앱에 연결
app.register_blueprint(blog_bp)
app.register_blueprint(api_bp)


# === 7. 설정 관리 ===
# 클래스 기반 설정 관리 패턴
class Config:
    SECRET_KEY = 'dev-secret'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///app.db'

# 환경별 설정 상속 (dev/prod 분리)
class ProductionConfig(Config):
    SECRET_KEY = 'production-secret-key'
    DEBUG = False

# from_object: 클래스의 대문자 속성을 config로 로드
app.config.from_object(Config)


if __name__ == '__main__':
    # debug=True: 자동 리로드 + 디버거 / host=0.0.0.0: 외부 접근 허용
    app.run(debug=True, host='0.0.0.0', port=5000)

print("Flask 기초 핵심 정리")
print("="*50)
print("@app.route: URL 매핑 데코레이터")
print("request: 요청 객체 (form, args, json, headers)")
print("render_template: Jinja2 템플릿 렌더링")
print("redirect + url_for: URL 리다이렉트")
print("Blueprint: 앱 모듈화 (url_prefix로 그룹핑)")
print("before_request/after_request: 미들웨어")
print("abort(): HTTP 에러 발생")
```

**실행 결과** — 실행하지 않음 — 외부 라이브러리 `flask` 가 있어야 도는 예제다 — 그것 없이 만들어 실행하지 않았다.

**풀이 요점**

- 라우트 하나는 「`@app.route(경로, methods=...)` + 뷰 함수」 한 쌍이고, 경로 변수는 함수 인자가 된다.
- 응답의 헤더 · 상태를 바꿀 때는 `make_response` 로 객체를 만들거나 `(본문, 상태)` 튜플을 돌려준다.
- `before_request` 와 `after_request` 는 `g` 로 같은 요청 안의 값을 주고받고, `after_request` 는 응답을 반드시 돌려준다.
- `login_required` 는 `@wraps` 와 `@app.route` 를 맨 바깥에 두는 순서가 둘 다 맞아야 제대로 동작한다.
- Blueprint 는 `register_blueprint` 로 등록해야 `url_prefix` 가 붙은 주소로 살아난다.
- `find_item` 과 `login` 엔드포인트가 정답 코드에도 없으므로, `/item/...` 과 비로그인 `/dashboard` 는 요청 때 실패한다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — 외부 라이브러리 `flask` 가 있어야 도는 예제다 — 그것 없이 만들어 실행하지 않았다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
