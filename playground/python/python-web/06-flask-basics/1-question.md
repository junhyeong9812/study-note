# python/python-web/06 — Flask 기초 (라우트, 템플릿, Blueprint) — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 변환기가 붙은 경로에 두 주소로 요청하면 (예측)

```python
# 질문용 발췌
@app.route('/user/<int:user_id>')
def user_profile(user_id):
    return f'User ID: {user_id}'
```

- `/user/42` 로 요청하면 응답 본문은 무엇이고, 함수 안에서 `user_id` 의 타입은 무엇인가?
- `/user/abc` 로 요청하면 `user_profile` 이 불리는가?

### 2. Blueprint 의 라우트가 닿는 주소 (예측)

```python
# 질문용 발췌
blog_bp = Blueprint('blog', __name__, url_prefix='/blog')

@blog_bp.route('/<int:post_id>')
def blog_detail(post_id): ...

app.register_blueprint(blog_bp)
```

- 어떤 주소로 요청해야 `blog_detail(post_id=7)` 이 불리는가?
- `register_blueprint` 줄을 지우면 그 주소로 요청했을 때 어떻게 되는가?

### 3. 비밀 키를 두 번 넣으면 (예측)

```python
# 질문용 발췌
app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

class Config:
    SECRET_KEY = 'dev-secret'

class ProductionConfig(Config):
    SECRET_KEY = 'production-secret-key'
    DEBUG = False

app.config.from_object(Config)
```

- 이 코드가 다 실행된 뒤 세션 서명에 쓰이는 비밀 키는 무엇인가?
- `ProductionConfig` 의 `SECRET_KEY` 와 `DEBUG` 는 앱 설정에 들어가는가?

### 4. 파일 맨 끝의 `print` 줄이 도는 때 (예측)

- `python flask-basics.py` 로 서버를 띄워 요청을 받고 있는 동안, 파일 맨 끝 `print` 줄들의 내용이 터미널에 찍혀 있는가?
- 다른 모듈이 이 파일을 `import` 하면 그 `print` 줄들은 언제 실행되는가?

### 5. `@app.route` 를 `@login_required` 보다 바깥에 두는 까닭 (왜)

- 두 데코레이터의 순서를 뒤집어 `@login_required` 를 맨 위에 두면 왜 로그인 검사가 사라지는가?

### 6. 커스텀 데코레이터에 `@wraps(f)` 가 필요한 까닭 (왜)

- `@wraps(f)` 없이 `login_required` 를 여러 뷰에 붙이면 왜 Flask 라우팅에 문제가 생기는가?

### 7. 서명만 되는 세션에서 `secret_key` 를 숨겨야 하는 까닭 (왜)

- `session` 은 내용을 숨기지 않고 서명만 하는데, 왜 `secret_key` 가 새면 로그인 검사가 무력해지는가?

### 8. `g` 에 넣은 값이 살아 있는 범위 (경계)

- 요청 A 의 `before_request` 에서 넣은 `g.start_time` 을 요청 A 의 `after_request` 에서 읽을 수 있는가?
- 그 값을 다음 요청 B 에서 읽을 수 있는가?

### 9. 원본 코드가 요청 때에야 깨지는 두 자리 (경계)

- 로그인하지 않고 `/dashboard` 에 요청하면 어느 줄에서 무엇 때문에 실패하는가?
- `/item/1` 에 요청하면 어느 줄에서 무엇 때문에 실패하는가?

### 10. `abort` · `errorhandler` 와 파이썬 예외 (연결)

- `abort(404)` 와 `@app.errorhandler(404)` 의 관계는 파이썬의 어떤 문법 짝과 같은 구조인가?

## 실습

### 실습 1. 라우트 · 요청/응답 · 에러 · 미들웨어 · Blueprint 를 갖춘 Flask 앱

**만들 것** — 기본 라우트, 요청/응답 처리, 에러 핸들링, 요청 앞뒤 처리, 로그인 데코레이터, Blueprint, 설정 클래스를 한 파일에 모은 Flask 앱을 만든다.

**준비물** — `pip install flask` 로 Flask 가 필요하다.
템플릿을 쓰는 라우트를 확인하려면 `templates/` 폴더에 `index.html` · `posts.html` · `dashboard.html` · `errors/404.html` · `blog/list.html` · `blog/detail.html` 을 직접 만들어 둔다.
`find_item` 함수와 `login` 엔드포인트는 이 과제에서도 정의하지 않는다(정답 코드에도 없다).

**요구 조건**

1단계 — 앱과 기본 라우트

1. `Flask(__name__)` 로 앱을 만들고 `secret_key` 를 넣는다.
2. `/` 는 `index.html` 을 `title='홈'` 으로 렌더링한다.
3. `/hello/<name>` 은 `Hello, {name}!` 문자열을 돌려준다.
4. `/user/<int:user_id>` 는 `User ID: {user_id}` 를 돌려준다.
5. `/posts` 는 GET 과 POST 를 받는다.
6. POST 면 폼의 `title` · `content` 를 읽고, `'success'` 분류의 플래시 메시지를 남긴 뒤 `url_for` 로 `posts` 에 리다이렉트한다.
7. GET 이면 쿼리스트링 `page`(정수, 기본 1)와 `q`(기본 빈 문자열)를 읽어 `posts.html` 에 `page` · `search` 로 넘긴다.

2단계 — 요청/응답

8. `/api/data` 는 POST 만 받고, JSON 본문의 `name`(기본 `'anonymous'`)을 읽는다.
9. 같은 함수에서 `Authorization` 헤더와 `content_type` 을 읽는다.
10. `make_response` 와 `jsonify` 로 `message` · `status` 를 담은 응답을 만들고, `X-Custom-Header` 헤더를 달고, 상태 코드를 201 로 한다.
11. `/download` 는 `make_response` 로 CSV 문자열 응답을 만들고 `Content-Type` 을 `text/csv` 로, `Content-Disposition` 을 첨부파일 `data.csv` 로 한다.

3단계 — 에러 핸들링

12. 404 핸들러는 `errors/404.html` 을 상태 404 로 돌려준다.
13. 500 핸들러는 `{'error': '서버 오류'}` JSON 을 상태 500 으로 돌려준다.
14. `/item/<int:item_id>` 는 `find_item(item_id)` 결과가 `None` 이면 `abort(404)` 하고, 아니면 JSON 으로 돌려준다.

4단계 — 요청 앞뒤 처리

15. 모든 요청 전에 `g.start_time` 에 현재 시각을 넣는다.
16. 모든 응답 직전에 `g.start_time` 이 있으면 걸린 시간을 소수 넷째 자리까지 `X-Elapsed-Time` 헤더(`'…s'` 꼴)로 달고 응답을 돌려준다.

5단계 — 커스텀 데코레이터

17. `login_required` 데코레이터는 `@wraps` 로 원본 함수 정보를 보존한다.
18. 세션에 `user_id` 가 없으면 `'warning'` 분류의 플래시 메시지를 남기고 `login` 엔드포인트로 `next=request.url` 을 붙여 리다이렉트한다.
19. `/dashboard` 에 `login_required` 를 붙이고 `dashboard.html` 을 렌더링한다.

6단계 — Blueprint

20. 이름 `'blog'`, 접두사 `/blog` 인 Blueprint 에 목록(`/`)과 상세(`/<int:post_id>`) 라우트를 둔다.
21. 이름 `'api'`, 접두사 `/api/v1` 인 Blueprint 에 `/posts` 라우트를 두고 `{'posts': []}` 를 JSON 으로 돌려준다.
22. 두 Blueprint 를 앱에 등록한다.

7단계 — 설정과 실행

23. `Config` 클래스와 그것을 상속한 `ProductionConfig` 클래스를 만들고, `Config` 를 앱 설정으로 읽는다.
24. 직접 실행할 때만 디버그 모드 · `0.0.0.0` · 5000 포트로 서버를 띄운다.
25. 파일 맨 끝에서 핵심 정리 문장들을 `print` 한다.

**시작 코드**

```python
# Flask 기초 - 라우트, 템플릿, Blueprint
# pip install flask
from flask import (
    Flask, render_template, request, redirect,
    url_for, jsonify, abort, flash, session,
    make_response, g, Blueprint
)
from functools import wraps

app = None  # TODO: 앱 만들기
# TODO: secret_key = 'your-secret-key-here'


# === 1. 기본 라우트 ===
# TODO: '/' 라우트
def index():
    return  # TODO: index.html, title='홈'

# TODO: '/hello/<name>' 라우트
def hello(name):
    return  # TODO

# TODO: '/user/<int:user_id>' 라우트
def user_profile(user_id):
    return  # TODO

# TODO: '/posts' 라우트 (GET, POST)
def posts():
    # TODO: POST 면 title/content 읽기 → flash('게시글이 작성되었습니다!', 'success') → posts 로 리다이렉트
    # TODO: GET 이면 page(int, 기본 1), q(기본 '') 읽기 → posts.html
    pass


# === 2. 요청/응답 처리 ===
# TODO: '/api/data' 라우트 (POST)
def api_data():
    # TODO: JSON 본문에서 name 읽기, Authorization 헤더와 content_type 읽기
    # TODO: make_response(jsonify({'message': f'Hello, {name}!', 'status': 'success'}))
    # TODO: X-Custom-Header = 'MyValue', 상태 201
    pass

# TODO: '/download' 라우트
def download():
    response = None  # TODO: make_response('CSV,데이터,여기')
    # TODO: Content-Type, Content-Disposition('attachment; filename=data.csv')
    return response


# === 3. 에러 핸들링 ===
# TODO: 404 핸들러
def not_found(error):
    return  # TODO: errors/404.html, 404

# TODO: 500 핸들러
def internal_error(error):
    return  # TODO: {'error': '서버 오류'}, 500

# TODO: '/item/<int:item_id>' 라우트
def get_item(item_id):
    item = find_item(item_id)
    # TODO: None 이면 404
    return jsonify(item)


# === 4. 미들웨어 (before/after) ===
# TODO: 모든 요청 전
def before_request():
    pass  # TODO: g.start_time = __import__('time').time()

# TODO: 모든 응답 직전
def after_request(response):
    # TODO: g.start_time 이 있으면 X-Elapsed-Time 헤더 (f'{elapsed:.4f}s')
    return response


# === 5. 커스텀 데코레이터 ===
def login_required(f):
    # TODO: 원본 함수 정보 보존
    def decorated_function(*args, **kwargs):
        # TODO: session 에 user_id 가 없으면 flash('로그인이 필요합니다.', 'warning') → login 으로 (next=request.url)
        return f(*args, **kwargs)
    return decorated_function

# TODO: '/dashboard' 라우트 + login_required (순서 주의)
def dashboard():
    return render_template('dashboard.html')


# === 6. Blueprint (모듈화) ===
blog_bp = None  # TODO: 이름 'blog', 접두사 '/blog'

# TODO: 목록 라우트 '/'
def blog_list():
    return render_template('blog/list.html')

# TODO: 상세 라우트 '/<int:post_id>'
def blog_detail(post_id):
    return render_template('blog/detail.html', post_id=post_id)

api_bp = None  # TODO: 이름 'api', 접두사 '/api/v1'

# TODO: '/posts' 라우트
def api_posts():
    return jsonify({'posts': []})

# TODO: 두 Blueprint 등록


# === 7. 설정 관리 ===
class Config:
    SECRET_KEY = 'dev-secret'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///app.db'

# TODO: Config 를 상속한 ProductionConfig (SECRET_KEY = 'production-secret-key', DEBUG = False)

# TODO: Config 를 앱 설정으로 읽기


# TODO: 직접 실행할 때만 app.run(debug=True, host='0.0.0.0', port=5000)

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

**확인 방법** — `python flask-basics.py` 로 서버를 띄운 뒤 다른 터미널에서 요청해 본다.
`curl -i http://localhost:5000/hello/Kim` · `curl -i http://localhost:5000/user/42` 의 본문과 `X-Elapsed-Time` 헤더를 본다.
`curl -i -X POST -H "Content-Type: application/json" -d '{"name":"Kim"}' http://localhost:5000/api/data` 의 상태 201 과 `X-Custom-Header` 를 본다.
`curl -i http://localhost:5000/download` 의 `Content-Disposition` 과 `curl -i http://localhost:5000/api/v1/posts` 의 JSON 을 본다.
`curl -i http://localhost:5000/dashboard` 가 실패하는 것(`login` 엔드포인트 없음)도 확인한다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
