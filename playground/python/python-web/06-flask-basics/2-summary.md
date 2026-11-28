# python/python-web/06 — Flask 기초 (라우트, 템플릿, Blueprint) — 정리 (힌트)

> 출처 — study-site 항목 `python/flask-basics`(항목 데이터 `data/python/web-frameworks.json`) · 정답 코드 study-practice `python/python-web/reference/flask-basics.py`\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).\
> 실행 — 실행하지 않음 — 외부 라이브러리 `flask` 가 있어야 도는 예제다 — 그것 없이 만들어 실행하지 않았다.

## 한눈에 — 쉽게 말하면

**Flask 앱은 「건물 안내 데스크」다.**
손님이 주소(URL)를 말하면 안내 데스크는 안내판을 보고 그 주소를 맡은 직원(함수)에게 손님을 보낸다.
손님은 들어올 때 보안 검색대를 지나고, 나갈 때 출구에서 도장을 받는다.
건물이 커지면 층마다 부서를 두고, 부서 안의 방 번호 앞에 층 번호를 붙인다.
Flask 도 똑같은 구조다.

| 비유 | 실체 |
|---|---|
| 안내 데스크 | `app = Flask(__name__)` |
| 안내판의 「주소 → 담당 직원」 한 줄 | `@app.route('/hello/<name>')` |
| 담당 직원 | 뷰 함수(`hello`, `posts` …) |
| 손님이 들고 온 서류 | `request` (`form` · `args` · `get_json()` · `headers`) |
| 손님에게 돌려주는 봉투 | 응답(문자열 · `render_template` · `jsonify` · `make_response`) |
| 입구 보안 검색 · 출구 도장 | `@app.before_request` · `@app.after_request` |
| 손님 한 명에게 잠깐 주는 쟁반 | `g` |
| 비상벨 · 비상 대응팀 | `abort(404)` · `@app.errorhandler(404)` |
| 층(부서)과 층 번호 | `Blueprint` 와 `url_prefix` |
| 「김 대리 방이 어디죠?」 하고 이름으로 묻기 | `url_for('posts')` |

```text
  요청 GET /user/42
        │
        ▼
  [before_request]  ── g.start_time 기록
        │
        ▼
  안내판(라우트 표)에서 '/user/<int:user_id>' 찾기
        │ 찾음
        ▼
  user_profile(user_id=42)  ── 'User ID: 42' 반환
        │
        ▼
  [after_request]   ── 응답 헤더 X-Elapsed-Time 추가
        │
        ▼
  응답이 손님에게 간다
```

## 이 주제가 답하려는 질문

1. URL 하나가 어떻게 파이썬 함수 하나에 닿는가?
2. 요청에서 값을 어떻게 꺼내고, 응답의 본문 · 헤더 · 상태 코드를 어떻게 정하는가?
3. 모든 요청에 공통으로 할 일(시간 재기 · 로그인 검사)을 어디에 끼우는가?
4. 앱이 커지면 라우트와 설정을 어떻게 나누어 관리하는가?

## 동작 방식

Flask 는 마이크로 프레임워크다.
핵심은 「URL → 함수」 연결과 요청 · 응답 처리뿐이고, 나머지는 필요한 것만 덧붙이는 것이 Flask 의 철학이다.

> **마이크로 프레임워크** — 최소한의 핵심만 주고 나머지 기능은 필요할 때 골라 붙이게 하는 프레임워크.\
> 예: Flask 자체에는 DB 도구가 없고, `SQLALCHEMY_DATABASE_URI` 같은 설정은 확장을 붙일 때 쓰인다.

### (1) 라우트 — URL 을 함수에 잇는다

**언제 쓰나** — 주소마다 할 일을 정할 때 쓴다.
모든 페이지 · API 의 출발점이다.

```text
@app.route('/user/<int:user_id>')          요청 경로
def user_profile(user_id): ...      ──▶   /user/42   → 변환기 int 통과 → user_profile(user_id=42)
                                           /user/abc  → int 변환 실패 → 이 규칙과 안 맞음
@app.route('/posts',                        GET  /posts → posts()  (request.method == 'GET')
           methods=['GET','POST'])          POST /posts → posts()  (request.method == 'POST')
```

- `@app.route(경로)` 는 경로와 함수를 안내판에 한 줄로 적는 데코레이터다.
- 경로 속 `<name>` 은 URL 변수이고, 그 자리의 글자가 같은 이름의 함수 인자로 들어간다.
- `<int:user_id>` 처럼 변환기를 붙이면 그 자리가 정수일 때만 규칙이 맞고, 인자는 `int` 로 바뀌어 들어온다.
- 변환기는 `int` · `float` · `path` · `uuid` · `string`(기본)이 있다.
- 변환에 실패한 경로는 그 규칙과 맞지 않으므로, 다른 규칙도 없으면 404 가 된다.
- `methods` 를 주지 않으면 GET 만 받는다.
- 한 함수가 GET 과 POST 를 함께 받으면 함수 안에서 `request.method` 로 갈라 처리한다.

> **엔드포인트** — 라우트 하나에 붙는 이름. 따로 주지 않으면 뷰 함수의 이름이 된다.\
> 예: `@app.route('/posts')` 아래 `def posts()` 의 엔드포인트는 `'posts'` 다.

### (2) 요청에서 값을 꺼낸다

**언제 쓰나** — 폼 입력 · 쿼리스트링 · JSON 본문 · 헤더를 읽을 때 쓴다.

```text
POST /posts   (폼: title=안녕&content=...)   → request.form.get('title')      → '안녕'
GET  /posts?page=2&q=flask                   → request.args.get('page', 1, type=int) → 2
GET  /posts                                  → request.args.get('page', 1, type=int) → 1 (기본값)
POST /api/data (본문 {"name":"Kim"})         → request.get_json()             → {'name': 'Kim'}
헤더 Authorization: Bearer abc               → request.headers.get('Authorization') → 'Bearer abc'
```

- `request` 는 지금 처리 중인 요청 하나를 가리키는 객체다.
- `request.form` 은 폼 인코딩된 POST 데이터다.
- `request.args` 는 쿼리스트링이고, `get(키, 기본값, type=int)` 처럼 쓰면 값을 정수로 바꿔 준다.
- 키가 없으면 기본값이 나온다.
- `request.get_json()` 은 요청 본문의 JSON 을 파싱해 dict 로 돌려준다.
- `request.headers` 는 요청 헤더이고, `request.content_type` 은 본문의 형식이다.

> **쿼리스트링** — URL 의 `?` 뒤에 붙는 `키=값&키=값` 부분.\
> 예: `/posts?page=2&q=flask` 의 `page=2&q=flask`.

### (3) 응답을 만든다

**언제 쓰나** — 무엇을 돌려줄지, 상태 코드와 헤더를 어떻게 할지 정할 때 쓴다.

```text
return f'Hello, {name}!'                          → 본문 문자열, 상태 200
return render_template('index.html', title='홈')   → templates/index.html 을 Jinja2 로 채운 HTML
return jsonify({...}), 500                         → JSON 본문 + 상태 500  (튜플)
resp = make_response(jsonify({...}))
resp.headers['X-Custom-Header'] = 'MyValue'        → 응답 객체를 직접 만져 헤더 · 상태 변경
resp.status_code = 201
return redirect(url_for('posts'))                  → "posts 엔드포인트 주소로 다시 가라" 응답
```

- 뷰 함수가 문자열을 돌려주면 그것이 본문이 된다.
- `render_template(파일, 변수=값)` 은 Jinja2 템플릿에 변수를 채워 HTML 을 만든다(템플릿 파일은 기본으로 `templates/` 폴더에서 찾는다).
- `(본문, 상태코드)` 튜플을 돌려주면 상태 코드를 함께 정한다.
- `make_response` 는 응답 객체를 먼저 만들어 헤더 · 상태 코드를 고친 뒤 돌려주게 한다.
- `/download` 는 `Content-Type: text/csv` 와 `Content-Disposition: attachment; filename=data.csv` 를 달아 브라우저가 파일로 내려받게 유도한다.
- `redirect` 는 다른 주소로 다시 가라는 응답이고, `url_for(엔드포인트)` 는 엔드포인트 이름으로 그 주소를 만든다.
- POST 처리 뒤 `redirect(url_for('posts'))` 로 GET 페이지로 돌려보내면, 사용자가 새로고침해도 POST 가 다시 보내지지 않는다(원본에 근거 없음 — 추론).

> **Jinja2** — Flask 가 쓰는 템플릿 엔진. HTML 안의 자리에 파이썬 값을 채운다.\
> 예: `render_template('posts.html', page=page)` 면 템플릿 안에서 `page` 를 쓸 수 있다.

### (4) 에러 — `abort` 로 울리고 `errorhandler` 가 받는다

**언제 쓰나** — 찾는 것이 없거나 처리할 수 없을 때 함수를 즉시 끝내고 에러 응답을 줄 때 쓴다.

```text
get_item(3)
  item = find_item(3) → None
  abort(404)  ──(예외처럼 튀어 나감, 아래 return jsonify(item) 은 안 돈다)──┐
                                                                          ▼
                                              @app.errorhandler(404) not_found(error)
                                              → (render_template('errors/404.html'), 404)
```

- `abort(404)` 는 예외처럼 동작해 그 자리에서 함수 실행을 끊는다.
- `@app.errorhandler(코드)` 로 등록한 함수가 그 에러를 받아 응답을 만든다.
- 에러 핸들러도 `(본문, 상태코드)` 튜플로 상태 코드를 밝힌다.
- 처리 중 잡히지 않은 예외는 500 에러로 이어진다.
- 이 구조는 파이썬의 `raise` 와 `except` 와 같다 — 깊은 곳에서 던지고, 한곳에서 받는다.

### (5) 요청 앞뒤 — `before_request` · `after_request` · `g`

**언제 쓰나** — 모든 요청에 공통으로 할 일(시간 재기 · 로그 · 헤더 추가)이 있을 때 쓴다.
원본은 이것을 미들웨어라고 부른다.

```text
요청 A 시작 ─▶ before_request: g.start_time = 지금
            ─▶ 뷰 함수
            ─▶ after_request(response): elapsed = 지금 - g.start_time
                                        response.headers['X-Elapsed-Time'] = '0.0012s' 꼴
            ─▶ return response
요청 A 끝   ─▶ g 는 버려진다
요청 B 시작 ─▶ 새 g (요청 A 의 start_time 은 없다)
```

- `@app.before_request` 함수는 모든 요청에서 뷰 함수보다 먼저 돈다.
- `@app.after_request` 함수는 응답 객체를 인자로 받아 고친 뒤 **반드시 그 응답을 돌려줘야** 한다.
- `g` 는 요청 컨텍스트 안에서만 살아 있는 임시 저장소다.
- 그래서 같은 요청의 `before_request` 와 `after_request` 가 `g` 로 값을 주고받을 수 있다.
- 다음 요청에는 이전 요청의 `g` 값이 남지 않는다 — 요청을 넘어 남기려면 `session` 을 쓴다.
- `hasattr(g, 'start_time')` 검사는 `start_time` 이 없을 때를 대비한 방어다.

> **요청 컨텍스트** — 요청 하나가 처리되는 동안만 열려 있는 범위. `request` · `g` 가 이 안에서 산다.\
> 예: 요청 하나가 끝나면 그 요청의 `g.start_time` 도 사라진다.

### (6) 커스텀 데코레이터 — `login_required` · `session` · `flash`

**언제 쓰나** — 여러 뷰 함수에 같은 검사(로그인 여부)를 붙일 때 쓴다.

```text
@app.route('/dashboard')      ← 바깥: "이 경로 = 아래에서 올라온 함수"를 등록
@login_required               ← 안쪽: dashboard 를 decorated_function 으로 감쌈
def dashboard(): ...

GET /dashboard
  → decorated_function()
      'user_id' in session?  ── 아니오 → flash('로그인이 필요합니다.', 'warning')
                                        redirect(url_for('login', next=request.url))
                             ── 예    → dashboard() 실행
```

- 데코레이터는 아래에서 위로 적용된다.
- 그래서 `login_required` 가 먼저 `dashboard` 를 감싸고, `route` 는 **감싼 함수**를 경로에 등록한다.
- 순서를 뒤집으면 `route` 가 감싸기 전의 `dashboard` 를 등록하므로 로그인 검사가 빠진다(원본에 근거 없음 — 추론).
- `@wraps(f)` 는 감싼 함수가 원본의 `__name__` 등 메타데이터를 이어받게 한다.
- 엔드포인트 이름은 함수 이름에서 오므로, `@wraps` 가 없으면 감싼 함수가 모두 `decorated_function` 이라는 같은 이름이 되어 라우팅에 문제가 생긴다(원본 주석: 「Flask 라우팅에 필요」).
- `url_for('login', next=request.url)` 의 `next` 는 로그인 뒤 원래 페이지로 돌아오기 위한 값이다.
- `session` 은 클라이언트 쪽 쿠키에 담기는 세션이고, `secret_key` 로 **서명**된다.
- 서명은 내용을 숨기는 것이 아니라, 키를 모르는 사람이 내용을 고치면 들통나게 하는 장치다.
- 그래서 `secret_key` 가 새면 누구나 `user_id` 를 넣은 가짜 세션을 만들 수 있다(원본에 근거 없음 — 추론).
- `flash(메시지, 분류)` 는 다음 요청까지만 남는 일회성 메시지이고, 세션을 쓰므로 `secret_key` 가 필요하다.

> **데코레이터** — 함수를 받아 다른 함수로 바꿔 돌려주는 함수. `@이름` 으로 붙인다.\
> 예: `@login_required` 는 `dashboard = login_required(dashboard)` 와 같다.

### (7) Blueprint — 라우트를 부서로 묶는다

**언제 쓰나** — 앱이 커져 블로그 · API 같은 덩어리를 파일 · 모듈로 나눌 때 쓴다.

```text
blog_bp = Blueprint('blog', __name__, url_prefix='/blog')
  @blog_bp.route('/')               → (등록 전엔 기록만)
  @blog_bp.route('/<int:post_id>')
api_bp  = Blueprint('api',  __name__, url_prefix='/api/v1')
  @api_bp.route('/posts')

app.register_blueprint(blog_bp)  ──▶  /blog/        → blog_list
                                      /blog/7       → blog_detail(post_id=7)
app.register_blueprint(api_bp)   ──▶  /api/v1/posts → api_posts
```

- `Blueprint(이름, __name__, url_prefix=접두사)` 로 묶음을 만든다.
- `@blog_bp.route(...)` 로 적은 라우트는 그 자리에서 바로 살아나지 않고, `app.register_blueprint(blog_bp)` 로 앱에 등록해야 활성화된다.
- 등록되면 `url_prefix` 가 그 묶음의 모든 경로 앞에 자동으로 붙는다.
- 버전별 API(`/api/v1`)를 별도 Blueprint 로 떼는 것이 흔한 꼴이다.
- 원본은 `blog/routes.py` · `api/routes.py` 로 나눌 자리를 주석으로 표시하고 한 파일에 모아 두었다.

### (8) 설정과 실행 — `config.from_object` · `secret_key` · `app.run`

**언제 쓰나** — 개발 · 운영 환경마다 설정을 다르게 할 때, 그리고 개발 서버를 띄울 때 쓴다.

```text
app.secret_key = 'your-secret-key-here'    → app.config['SECRET_KEY'] = 'your-...'
app.config.from_object(Config)             → Config 의 대문자 속성을 config 로 복사
                                             SECRET_KEY = 'dev-secret'  (덮어씀)
                                             SQLALCHEMY_DATABASE_URI = 'sqlite:///app.db'
ProductionConfig                           → 정의만 됨, 어디에도 로드되지 않음
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)   → 서버가 여기서 계속 돈다
print(...)                                 → app.run 이 끝나야 닿는다
```

- `from_object(클래스)` 는 클래스의 대문자 속성(상속받은 것 포함)을 설정으로 읽는다.
- `app.secret_key` 는 `app.config['SECRET_KEY']` 와 같은 자리를 가리킨다(Flask 의 설계 — 확인 필요).
- 그래서 나중에 `from_object(Config)` 가 실행되면 앞서 넣은 `secret_key` 는 `'dev-secret'` 으로 덮인다(원본에 근거 없음 — 추론).
- 설정을 클래스로 두고 `ProductionConfig(Config)` 처럼 상속하면 환경별로 다른 값만 바꿀 수 있다.
- 다만 원본은 `Config` 만 로드하므로 `ProductionConfig` 의 값은 쓰이지 않는다.
- `app.run(debug=True)` 는 자동 리로드와 디버거를 켜고, `host='0.0.0.0'` 은 외부 접근을 허용한다.
- `app.run` 은 서버가 멈출 때까지 돌아오지 않는다.
- 파일을 직접 실행하면 맨 끝의 `print` 줄은 서버가 도는 동안 실행되지 않는다.
- 다른 모듈이 이 파일을 import 하면 `__name__` 이 `'__main__'` 이 아니므로 `app.run` 은 건너뛰고 `print` 줄이 import 때 바로 실행된다.

## 문법 — 형태와 규칙

```python
from flask import Flask, request, jsonify, abort, g

app = Flask(__name__)

@app.before_request
def mark():
    g.who = request.headers.get('X-User', 'guest')

@app.route('/sq/<int:n>', methods=['GET'])
def square(n):
    if n > 1000:
        abort(400)
    return jsonify({'n': n, 'sq': n * n, 'by': g.who}), 200
```

- 경로 규칙: `'/고정/<변수>'` · `'/고정/<변환기:변수>'` — 변환기는 `int` · `float` · `path` · `uuid` · `string`(기본).
- `methods=[...]` 를 생략하면 GET 만 받는다.
- 반환 꼴: 문자열 · `render_template(...)` · `jsonify(...)` · `(본문, 상태)` 튜플 · `make_response(...)` 로 만든 응답 객체 · `redirect(...)`.
- `request.form` · `request.args` · `request.get_json()` · `request.headers` · `request.method` · `request.url` · `request.content_type` 으로 요청을 읽는다.
- `@app.after_request` 함수는 `response` 를 받아 돌려준다.
- 데코레이터를 겹칠 때는 `@app.route` 를 맨 위(바깥)에 둔다.
- Blueprint 는 `Blueprint(이름, __name__, url_prefix=...)` → `@bp.route(...)` → `app.register_blueprint(bp)` 차례로 쓴다.
- 설치는 `pip install flask` 다.

## 어디서 틀리나

### 1. 마이크로 프레임워크라서 「없는 것」이 많다

Flask 는 필요한 것만 덧붙이는 철학이다.
DB 연결 · 폼 검증 같은 것은 기본으로 없다.
`SQLALCHEMY_DATABASE_URI` 를 설정에 넣어도, 그것을 읽는 확장을 붙이지 않으면 아무 일도 일어나지 않는다.

### 2. URL 을 문자열로 박지 말고 `url_for` 를 쓴다

`redirect('/posts')` 처럼 주소를 박아 두면 경로를 바꿀 때 모든 곳을 고쳐야 한다.
`url_for('posts')` 는 엔드포인트 이름으로 주소를 만들어서, 경로가 바뀌어도 코드는 그대로다.
`url_for('login', next=...)` 처럼 경로 변수에 없는 인자는 쿼리스트링으로 붙는다(원본에 근거 없음 — 추론).

### 3. 없는 엔드포인트 · 없는 함수는 요청 때 터진다

원본에는 `login` 이라는 엔드포인트가 없다.
그래서 로그인하지 않고 `/dashboard` 에 가면 `url_for('login', ...)` 이 주소를 만들지 못해 에러가 난다.
`find_item` 도 원본 어디에도 정의되지 않았다.
`/item/1` 에 요청하면 `NameError` 가 나고, 잡히지 않은 예외라 500 으로 이어진다.
둘 다 파일을 불러올 때는 멀쩡하고, 그 경로에 요청이 왔을 때에야 드러난다.

### 4. `g` 는 요청 하나 동안만 산다

`g` 는 요청 컨텍스트 안에서 데이터를 공유하는 곳이다.
요청 사이에 값을 이어 가려고 `g` 에 넣으면 다음 요청에서는 사라져 있다.
요청을 넘어 남길 값은 `session` 에 넣는다.

### 5. 데코레이터 순서와 `@wraps`

`@app.route` 가 맨 바깥이어야 감싼(검사가 붙은) 함수가 등록된다.
`@wraps(f)` 를 빼면 감싼 함수의 이름이 모두 `decorated_function` 이 되어 엔드포인트 이름이 겹친다.

### 6. `secret_key` 는 비밀이고, 덮일 수도 있다

`secret_key` 는 세션 · 플래시 서명에 쓰이므로 코드에 박아 저장소에 올리면 안 된다.
원본은 `'your-secret-key-here'` 를 넣은 뒤 `from_object(Config)` 로 `SECRET_KEY` 를 다시 넣어, 실제로 쓰이는 값은 `'dev-secret'` 이 된다.
`ProductionConfig` 를 만들어도 `from_object` 에 넘기지 않으면 운영 설정은 적용되지 않는다.

### 7. 템플릿 파일이 없으면 템플릿을 쓰는 라우트가 모두 실패한다

`render_template('index.html', ...)` 은 `templates/` 폴더의 파일을 찾는다.
원본에는 템플릿 파일이 없으므로 `/` · `/posts` (GET) · `/dashboard` · `/blog/...` 와 404 핸들러는 템플릿을 만들어 두어야 동작한다.

### 8. `request.get_json()` 이 dict 를 준다고 믿지 않는다

`api_data` 는 `data.get('name', ...)` 을 바로 부른다.
본문이 JSON 이 아니면 `get_json()` 이 dict 를 주지 않으므로 이 줄에서 깨질 수 있다(어떻게 깨지는지는 Flask 버전마다 다르다 — 확인 필요).

### 9. 원본 주석의 주장: 「Flask 는 Django 와 달리 동기 처리」

원본의 주장 → 「Flask: WSGI 앱 클래스 (Django와 달리 동기 처리, ASGI는 Quart 등 별도 프레임워크)」.
왜 의심스러운가 → 이 문장은 Django 는 동기가 아니라는 뜻으로 읽히는데, Django 도 WSGI 로 동기 처리를 하며 ASGI 도 지원한다(확인 필요).
또 Flask 도 2.0 이후 `async def` 뷰를 받는다고 알려져 있다(확인 필요).
「Flask 는 WSGI 앱이다」까지만 믿고, Django 와의 비교는 따로 확인한다.

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| 데코레이터는 아래에서 위로 적용된다 | 파이썬 언어 |
| `if __name__ == '__main__':` 은 직접 실행할 때만 참이다 | 파이썬 언어 |
| `@wraps` 가 `__name__` 등을 복사한다 | 파이썬 표준 라이브러리(`functools`) |
| 엔드포인트 이름은 기본으로 함수 이름이다 | Flask |
| 변환기 종류(`int` · `float` · `path` · `uuid` · `string`) · `methods` 기본값 GET | Flask (경로 매칭은 Flask 가 쓰는 Werkzeug) |
| `session` 이 서명된 쿠키에 담긴다 | Flask 의 기본 세션 구현 (바꿔 끼울 수 있다 — 확인 필요) |
| `app.secret_key` 와 `config['SECRET_KEY']` 가 같은 자리다 | Flask (확인 필요) |
| `get_json()` 이 JSON 이 아닌 본문을 만났을 때의 동작 | Flask · Werkzeug 의 버전별 동작 (확인 필요) |
| Flask 는 동기 · Django 와 다르다 | 원본의 주장 — 근거 의심 (확인 필요) |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 다른 페이지로 보내기 | `redirect(url_for('엔드포인트'))` | `redirect('/박은/주소')` |
| 같은 요청 안에서 값 넘기기 | `g` | 전역 변수 |
| 다음 요청까지 값 남기기 | `session` · `flash` | `g` |
| 여러 뷰에 같은 검사 | 커스텀 데코레이터(`@wraps` 포함) | 뷰마다 같은 `if` 복사 |
| 모든 요청에 공통 처리 | `before_request` · `after_request` | 뷰마다 시간 재기 코드 |
| 헤더 · 상태 코드를 바꿔야 할 때 | `make_response` 또는 `(본문, 상태)` 튜플 | 문자열만 반환 |
| 없는 자원 | `abort(404)` + `errorhandler(404)` | 빈 문자열에 200 |
| 앱이 커짐 | `Blueprint` + `url_prefix` | 한 파일에 라우트 수백 개 |
| 환경별 설정 | 설정 클래스 상속 + `from_object` | 코드 곳곳에 값 박기 |

## 핵심 문장

1. **`@app.route` 가 URL 을 함수에 잇는다** — 경로 변수는 함수 인자로, 변환기는 타입과 매칭 조건을 정한다.
2. **요청은 `request` 로 읽고 응답은 반환값으로 정한다** — 헤더 · 상태를 바꾸려면 튜플이나 `make_response`.
3. **`abort` 는 던지고 `errorhandler` 는 받는다** — 예외와 같은 구조다.
4. **`before_request` · `after_request` 는 모든 요청을 감싸고, `g` 는 그 한 요청 동안만 산다.**
5. **Blueprint 는 등록해야 살아나고, `url_prefix` 가 묶음 전체의 경로 앞에 붙는다.**

## 관련 자료

- [flask-api](../07-flask-api/2-summary.md)
- [jinja2](../12-jinja2/2-summary.md)
- [django-views](../02-django-views/2-summary.md)
- 원본: study-site 항목 데이터 `data/python/web-frameworks.json` 의 `flask-basics`

## 용어 풀이

- **Flask** — 파이썬 마이크로 웹 프레임워크. `Flask(__name__)` 로 앱을 만든다.
- **WSGI** — 파이썬 웹 서버와 웹 앱이 주고받는 표준 약속.
- **마이크로 프레임워크** — 핵심만 두고 나머지는 골라 붙이는 프레임워크.
- **라우트** — URL 경로와 뷰 함수의 연결 한 줄.
- **뷰 함수** — 요청 하나를 받아 응답을 돌려주는 함수.
- **엔드포인트** — 라우트의 이름. 기본은 함수 이름이다.
- **변환기** — 경로 변수의 타입을 정하는 표시(`<int:...>`).
- **쿼리스트링** — URL 의 `?` 뒤 `키=값` 들.
- **Jinja2** — Flask 의 템플릿 엔진.
- **`make_response`** — 응답 객체를 직접 만드는 함수.
- **`jsonify`** — dict 를 JSON 응답으로 바꾸는 함수.
- **`abort`** — HTTP 에러를 예외처럼 일으키는 함수.
- **`errorhandler`** — 특정 에러 코드를 받아 응답을 만드는 함수를 등록하는 데코레이터.
- **미들웨어** — 모든 요청의 앞뒤에 끼는 공통 처리. 원본에서는 `before_request` · `after_request`.
- **요청 컨텍스트** — 요청 하나가 처리되는 동안의 범위.
- **`g`** — 요청 컨텍스트 동안만 쓰는 임시 저장소.
- **`session`** — 서명된 쿠키에 담겨 요청을 넘어 유지되는 값.
- **서명** — 비밀 키로 만든 표시. 내용이 바뀌면 들통난다. 내용을 숨기지는 않는다.
- **`flash`** — 다음 요청까지 한 번만 보여 줄 메시지.
- **데코레이터** — 함수를 감싸 바꾸는 함수.
- **`@wraps`** — 감싼 함수에 원본 함수의 이름 등 메타데이터를 복사하는 도구.
- **Blueprint** — 라우트를 묶어 앱에 한꺼번에 등록하는 단위.
- **`url_prefix`** — Blueprint 의 모든 경로 앞에 붙는 접두사.
- **`from_object`** — 객체의 대문자 속성을 설정으로 읽는 메서드.

## 더 들어가면

- Blueprint 안의 엔드포인트 이름에는 Blueprint 이름이 앞에 붙는다 — `url_for('blog.blog_detail', post_id=7)` 꼴로 부른다(확인 필요).
- `debug=True` 의 디버거는 브라우저에서 파이썬 코드를 실행할 수 있게 하므로, `host='0.0.0.0'` 과 함께 바깥에 열면 위험하다고 알려져 있다(확인 필요).
- 디버그 모드에서는 잡히지 않은 예외가 500 핸들러 대신 디버거 화면으로 갈 수 있다(확인 필요).
- `app.run` 은 개발용 서버이고, 운영에서는 별도의 WSGI 서버(gunicorn 등)로 띄우는 것이 보통이다(확인 필요).
- 요즘은 `python 파일.py` 대신 `flask --app 파일 run` 으로 띄우는 방식도 쓴다 — 이때는 `__name__` 이 `'__main__'` 이 아니다(확인 필요).
- 디버그 모드의 자동 리로드는 모듈을 한 번 더 불러올 수 있어서, 모듈 최상위의 `print` 가 두 번 찍힐 수 있다(확인 필요).
- 최신 Werkzeug 에서는 JSON 이 아닌 본문에 `get_json()` 을 부르면 415 에러가 난다고 알려져 있다(확인 필요).
