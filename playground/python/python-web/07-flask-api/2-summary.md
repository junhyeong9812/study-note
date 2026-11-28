# python/python-web/07 — Flask RESTful API (marshmallow, JWT) — 정리 (힌트)

> 출처 — study-site 항목 `python/flask-api`(항목 데이터 `data/python/web-frameworks.json`) · 정답 코드 study-practice `python/python-web/reference/flask-api.py`\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).\
> 실행 — 실행하지 않음 — 외부 라이브러리 `flask` 가 있어야 도는 예제다 — 그것 없이 만들어 실행하지 않았다.

## 한눈에 — 쉽게 말하면

**이 API 는 「출입증을 받아야 들어가는 게시판 사무실」이다.**
처음 온 사람은 접수창구에서 서류(가입 양식)를 낸다.
창구 직원은 서류 양식이 맞는지 검사하고 맞으면 명부에 올린다.
명부에 있는 사람이 이름과 비밀번호를 대면 두 장의 증표를 받는다.
하나는 짧게 쓰는 **출입증**(1시간)이고, 다른 하나는 출입증을 다시 받을 때만 쓰는 **재발급 쿠폰**(30일)이다.
게시판에 글을 쓰거나 고치거나 지우려면 출입증을 보여야 한다.
남이 쓴 글은 출입증이 있어도 고칠 수 없다.
Flask + Flask-RESTful + marshmallow + Flask-JWT-Extended 로 만든 API 도 똑같은 구조다.

| 비유 | 실체 |
|---|---|
| 창구 (어느 창구로 갈지 안내판) | `api.add_resource(클래스, URL)` 로 등록한 `Resource` 클래스 |
| 가입 양식 검사 | marshmallow `Schema.load()` |
| 명부 | SQLAlchemy 모델 `User` · DB 테이블 |
| 비밀번호를 적지 않고 지문만 남김 | `generate_password_hash` 로 해시만 저장 |
| 출입증 | access 토큰 (`create_access_token`) |
| 재발급 쿠폰 | refresh 토큰 (`create_refresh_token`) |
| 출입증 검사원 | `@jwt_required()` |
| 「당신 글이 아니다」 | `post.author_id != int(get_jwt_identity())` → 403 |
| 외부에 보여 주는 안내문 | marshmallow `Schema.dump()` 결과 |

```text
 클라이언트                        서버
 ─────────                        ────
 POST /api/register  ──JSON──▶  load(검증) ──▶ User 저장 ──▶ dump ──▶ 201
 POST /api/login     ──JSON──▶  비밀번호 확인 ──▶ access + refresh 발급
 POST /api/posts     ──access 토큰──▶ @jwt_required ──▶ load ──▶ Post 저장 ──▶ 201
 POST /api/refresh   ──refresh 토큰──▶ @jwt_required(refresh=True) ──▶ 새 access
```

## 이 주제가 답하려는 질문

1. HTTP 요청 하나가 들어오면 어떤 클래스의 어떤 메서드가 불리고, 무엇을 돌려주나?
2. 들어오는 JSON 은 어떻게 검사하고, 나가는 JSON 에는 어떤 필드만 담나?
3. 로그인한 사람을 서버는 어떻게 알아보고, 토큰은 왜 두 종류인가?
4. 「로그인했는가」와 「이 글의 주인인가」는 어떻게 따로 확인하나?

## 동작 방식

### (1) 요청이 Resource 메서드에 닿기까지

**언제 쓰나** — URL 하나에 여러 HTTP 메서드(GET · POST · PUT · DELETE)를 한 클래스로 묶고 싶을 때 쓴다.

```text
api.add_resource(PostResource, '/api/posts/<int:post_id>')

  요청: PUT /api/posts/7
        │
        ▼
  URL 이 '/api/posts/<int:post_id>' 와 맞음 → post_id = 7 (정수로 변환)
        │
        ▼
  HTTP 메서드 이름 'PUT' → PostResource 의 put(self, post_id) 호출
        │
        ▼
  반환: {'post': {...}}            → 본문 JSON, 상태 200
  반환: {'message': '권한 없음'}, 403 → 본문 JSON, 상태 403
```

- `add_resource` 가 클래스를 URL 에 묶는다.
- 요청의 HTTP 메서드 이름과 같은 이름의 메서드(`get` · `post` · `put` · `delete`)가 불린다.
- `<int:post_id>` 는 URL 조각을 정수로 바꿔 메서드 인자 `post_id` 로 넘긴다.
- 메서드가 dict 를 돌려주면 JSON 본문이 되고, `(dict, 숫자)` 튜플이면 숫자가 상태 코드가 된다.
- 상태 코드를 적지 않으면 200 이다.

> **Resource** — Flask-RESTful 에서 HTTP 메서드 이름과 같은 이름의 메서드를 가진, 한 URL 을 맡는 클래스.\
> 예: `PostListResource` 의 `get` 은 목록, `post` 는 작성이다.

> **변수 컨버터** — URL 패턴의 `<int:이름>` 처럼 URL 조각을 정해진 타입으로 바꿔 인자로 넘기는 표기.\
> 예: `/api/posts/7` → `post_id=7`.

### (2) marshmallow — `load` 는 들어올 때, `dump` 는 나갈 때

**언제 쓰나** — 요청 JSON 을 검사해 정제된 dict 로 받고, DB 객체를 응답 dict 로 바꿀 때 쓴다.

```text
 요청 JSON ──▶ schema.load(...) ──▶ 검증 통과 → 정제된 dict
                     │
                     └─ 실패 → ValidationError(err.messages) → 코드가 400 으로 돌려줌

 DB 객체 ──▶ schema.dump(obj) ──▶ dict (응답에 담을 필드만)

 UserSchema 필드       load(요청) 에서   dump(응답) 에서
 id        dump_only        ✗               ○
 username                   ○ (3~80자)      ○
 email                      ○ (이메일 꼴)   ○
 password  load_only        ○ (6자 이상)    ✗
```

- `load()` 는 입력을 검증하고 통과하면 dict 를 돌려준다.
- 검증에 실패하면 `ValidationError` 가 나고, `err.messages` 에 필드별 오류가 담긴다.
- 코드는 그것을 잡아 `{'errors': err.messages}, 400` 을 돌려준다.
- `dump_only=True` 필드는 응답에만 나온다 — 서버가 정하는 `id` · `created_at` · `author_id` 가 그렇다.
- `load_only=True` 필드는 요청에서만 받는다 — `password` 가 응답으로 새지 않는다.
- `required=True` 는 그 필드가 빠지면 검증 실패다.
- `validate=validate.Length(min=…, max=…)` 는 길이 규칙, `fields.Email` 은 이메일 꼴 검사다.
- `@validates('username')` 메서드는 그 필드에 규칙을 더 건다 — 여기서는 DB 를 조회해 같은 사용자명이 있으면 `ValidationError` 를 낸다.
- `fields.Method('get_author_name')` 은 dump 할 때 그 메서드를 불러 값을 계산한다 — 글 객체의 `author.username` 을 넣고, 작성자가 없으면 `None` 이다.
- `PostSchema(many=True)` 는 리스트 전체를 dump 하는 인스턴스다(`posts_schema`).

> **직렬화** — 파이썬 객체를 JSON 으로 보낼 수 있는 dict · 문자열로 바꾸는 일. 반대 방향은 역직렬화다.\
> 예: `user_schema.dump(user)` → `{'id': 1, 'username': 'kim', 'email': '…'}`.

> **스키마** — 어떤 필드가 있고 각 필드가 어떤 규칙을 따르는지 적은 선언.\
> 예: `PostSchema` 는 `title` 1~200자 필수, `content` 필수.

### (3) 로그인과 토큰 두 장

**언제 쓰나** — 서버가 세션을 기억하지 않고도 매 요청마다 「누가 보냈나」를 알아야 할 때 쓴다.

```text
 POST /api/login {username, password}
        │
        ▼
 User 를 username 으로 찾음 ─ 없음 ───────────┐
        │                                      ├─▶ {'message': '잘못된 인증 정보'}, 401
 check_password(입력) ─ 틀림 ─────────────────┘
        │ 맞음
        ▼
 access  = create_access_token(identity=str(user.id))    만료 1시간
 refresh = create_refresh_token(identity=str(user.id))   만료 30일
        │
        ▼
 {'access_token', 'refresh_token', 'user'}  (상태 200)

 1시간 뒤 access 만료
        │
        ▼
 POST /api/refresh  (refresh 토큰 제시)
 @jwt_required(refresh=True) 통과 → get_jwt_identity() → 새 access 발급
```

- 비밀번호는 `set_password` 에서 `generate_password_hash` 로 해시만 저장한다 — 평문은 DB 에 없다.
- 로그인 때는 `check_password_hash(저장된 해시, 입력)` 로 맞는지만 확인한다.
- 사용자가 없을 때와 비밀번호가 틀릴 때 같은 메시지 · 같은 401 을 돌려준다.
- 토큰의 `identity` 에는 `str(user.id)` 를 넣는다 — 문자열이다.
- 그래서 꺼낼 때는 `int(get_jwt_identity())` 로 정수로 바꿔 `author_id` 와 비교 · 저장한다.
- 만료 시간은 `JWT_ACCESS_TOKEN_EXPIRES`(1시간) · `JWT_REFRESH_TOKEN_EXPIRES`(30일) 설정으로 정한다.
- access 토큰은 짧게 살아 새어도 피해 기간이 짧고, refresh 토큰으로 다시 로그인하지 않고 새 access 를 받는다 — 보안과 편의를 함께 얻는 구조다.
- `/api/refresh` 는 `@jwt_required(refresh=True)` 라 refresh 토큰만 받는다.
- 토큰 서명에는 `JWT_SECRET_KEY` 를 쓴다 — 이 값이 새면 누구나 토큰을 만들 수 있다.

> **JWT** — 서버가 비밀 키로 서명한, 사용자 식별자(identity)와 만료 시각을 담은 토큰 문자열.\
> 예: 로그인 응답의 `access_token` 값.

> **해시** — 원래 값으로 되돌릴 수 없게 바꾼 지문 같은 문자열.\
> 예: `password_hash` 열에는 비밀번호 대신 해시가 들어간다.

### (4) 「로그인했나」와 「주인인가」는 다른 문이다

**언제 쓰나** — 쓰기 · 수정 · 삭제처럼 사람과 객체에 따라 허용이 달라지는 엔드포인트에 쓴다.

```text
 PUT /api/posts/7  (헤더에 access 토큰)
        │
        ▼
 문 1: @jwt_required()      토큰 없음/무효 → 요청 거절 (라이브러리가 처리)
        │ 통과
        ▼
 Post.query.get_or_404(7)   글 없음 → 404
        │ 있음
        ▼
 문 2: post.author_id != int(get_jwt_identity()) → {'message': '권한 없음'}, 403
        │ 주인
        ▼
 수정 진행
```

- 문 1 은 「누구인지 증명했는가(인증)」이고 데코레이터 `@jwt_required()` 가 맡는다.
- 문 2 는 「이 글을 건드려도 되는가(인가)」이고 메서드 안의 비교가 맡는다.
- 로그인 실패는 401(인증 실패), 남의 글은 403(권한 없음)으로 상태 코드가 갈린다.
- 글 작성(`PostListResource.post`)은 작성자를 요청 본문에서 받지 않고 토큰에서 꺼내 `author_id` 에 넣는다.
- `author_id` 는 스키마에서 `dump_only` 라 요청으로 정할 수 없다.
- 목록 조회 · 단건 조회(`get`)에는 데코레이터가 없어 누구나 볼 수 있다.
- `get_or_404` 는 Flask-SQLAlchemy 가 주는 편의 메서드로, 없으면 404 응답으로 끝낸다.

> **인증 / 인가** — 인증은 「누구인가」 확인, 인가는 「그 사람이 이것을 해도 되나」 확인.\
> 예: 토큰 검사는 인증, 작성자 비교는 인가.

### (5) 부분 수정 — `partial=True`

**언제 쓰나** — 바꿀 필드만 보내는 수정 요청을 받을 때 쓴다.

```text
 PUT /api/posts/7  {"title": "새 제목"}
        │
        ▼
 post_schema.load(json, partial=True)
   title: 보냄 → 규칙(1~200자) 검사 → 통과
   content: 안 보냄 → required 지만 partial 이라 오류 아님
        │
        ▼
 data = {'title': '새 제목'}
 post.title   = data.get('title',   post.title)    → '새 제목'
 post.content = data.get('content', post.content)  → 원래 값 유지
        │
        ▼
 commit → dump → 200
```

- `partial=True` 면 `required=True` 필드가 빠져도 검증 실패가 아니다.
- 보낸 필드에는 여전히 길이 같은 규칙이 걸린다.
- `data.get(키, 원래값)` 이라 보내지 않은 필드는 원래 값을 그대로 둔다.
- 여기서는 PUT 에 부분 수정을 허용했다 — 원래 PATCH 가 뜻하는 동작이다.

### (6) 목록 — 검색 · 정렬 · 페이지

**언제 쓰나** — 많은 행을 한 번에 다 주지 않고 쪽 단위로 나눠 줄 때 쓴다.

```text
 GET /api/posts?page=2&per_page=5&q=flask
        │
        ▼
 page=2, per_page=5 (int 로 변환, 없으면 1 · 10), search='flask' (없으면 '')
        │
        ▼
 search 가 있으면 Post.title.ilike('%flask%')  (대소문자 무시 부분 일치)
        │
        ▼
 order_by(created_at.desc())  최신 글 먼저
        │
        ▼
 paginate(page=2, per_page=5) → items · total · pages
        │
        ▼
 {'posts': [...], 'total': …, 'pages': …, 'current_page': 2}
```

- `request.args.get('page', 1, type=int)` 는 쿼리 문자열 값을 정수로 바꾸고, 없으면 기본값을 쓴다.
- `ilike` 는 대소문자를 무시하는 LIKE 이다.
- `paginate` 결과의 `items` 를 `posts_schema`(many=True)로 dump 한다.
- `total` 은 조건에 맞는 전체 개수, `pages` 는 전체 쪽 수다.

## 문법 — 형태와 규칙

```python
from flask import Flask, request
from flask_restful import Api, Resource
from marshmallow import Schema, fields, validate, ValidationError

app = Flask(__name__)
api = Api(app)

class NoteSchema(Schema):
    id = fields.Int(dump_only=True)
    text = fields.Str(required=True, validate=validate.Length(min=1))

class NoteResource(Resource):
    def post(self):
        try:
            data = NoteSchema().load(request.get_json())
        except ValidationError as err:
            return {'errors': err.messages}, 400
        return {'note': {'id': 1, 'text': data['text']}}, 201

api.add_resource(NoteResource, '/notes')
```

- 확장 모듈은 앱을 넘겨 만든다 — `SQLAlchemy(app)` · `Api(app)` · `JWTManager(app)`.
- 설정은 `app.config['키'] = 값` 으로, 확장을 만들기 전에 넣는다.
- `Resource` 를 상속하고 HTTP 메서드 이름으로 메서드를 정의한다.
- 반환은 dict 또는 `(dict, 상태코드)`.
- 스키마 필드 옵션 — `required` · `validate` · `dump_only` · `load_only`.
- 스키마 메서드 — `load(dict, partial=…)` · `dump(obj)`; 리스트는 `Schema(many=True)`.
- 필드 추가 검증 — `@validates('필드')` 메서드에서 `ValidationError` 를 낸다.
- 계산 필드 — `fields.Method('메서드이름')`, 메서드는 `(self, obj)` 를 받아 값을 돌려준다.
- 인증이 필요한 메서드 위에 `@jwt_required()`, refresh 전용이면 `@jwt_required(refresh=True)`.
- 토큰 발급 — `create_access_token(identity=…)` · `create_refresh_token(identity=…)`.
- 현재 사용자 — `get_jwt_identity()`.
- 모델 — `db.Column(타입, primary_key · unique · nullable · default)`, 외래 키는 `db.ForeignKey('user.id')`, 객체 연결은 `db.relationship('User', backref='posts')`.
- `backref='posts'` 로 `user.posts` 역참조가 자동으로 생긴다.
- `default=db.func.now()` 는 DB 의 현재 시각 함수를 기본값으로 쓴다.
- 테이블 생성은 앱 컨텍스트 안에서 `db.create_all()`.

## 어디서 틀리나

### 1. `dump_only` 와 `load_only` 의 방향을 뒤집는다

`dump_only` 는 응답에만, `load_only` 는 요청에만 쓰인다.
`password` 에 `dump_only` 를 걸면 가입 때 비밀번호를 받지 못하고, 아무 옵션도 없으면 응답에 비밀번호가 실린다.
`id` 처럼 서버가 정하는 값은 `dump_only` 로 둬야 요청으로 바꿀 수 없다.

### 2. 부분 수정인데 `partial=True` 를 빠뜨린다

`PostSchema` 의 `title` · `content` 는 둘 다 `required=True` 다.
`partial=True` 없이 제목만 보내면 `content` 가 빠졌다는 검증 오류로 400 이 된다.
그리고 `data['content']` 처럼 꺼내면 안 되고 `data.get('content', post.content)` 처럼 원래 값을 기본으로 둬야 한다.

### 3. access 와 refresh 를 섞어 쓴다

`/api/refresh` 는 refresh 토큰만 받는다.
반대로 `@jwt_required()` 엔드포인트에는 access 토큰을 보내야 한다.
refresh 토큰을 오래 살려 두는 대신 그것으로는 글을 쓸 수 없게 하는 것이 이 구조의 요점이다.

### 4. identity 의 타입을 잊는다

토큰에는 `str(user.id)` 로 문자열을 넣었다.
`post.author_id != get_jwt_identity()` 처럼 정수와 문자열을 바로 비교하면 언제나 「다르다」가 되어 주인도 403 을 받는다.
그래서 코드는 `int(get_jwt_identity())` 로 바꾼 뒤 비교한다.

### 5. 401 과 403 을 섞는다

401 은 인증 실패(로그인 정보가 틀림 · 토큰 문제), 403 은 인증은 됐지만 그 일을 할 권한이 없음이다.
남의 글 수정 · 삭제는 403 이다.

### 6. 검증과 DB 제약이 다른 층이라는 것을 잊는다

`username` 은 `@validates` 로 DB 를 먼저 조회하므로 중복이면 400 과 오류 메시지가 나간다.
`email` 도 모델에 `unique=True` 가 있지만 스키마에는 중복 검사가 없다.
그래서 같은 이메일로 가입하면 검증은 통과하고, `db.session.commit()` 에서 DB 의 유일 제약에 걸려 예외가 난다.
코드가 그 예외를 잡지 않으므로 400 이 아닌 서버 오류(500)가 된다. (원본에 근거 없음 — 추론)

### 7. 비밀 키를 코드에 박아 둔다

`JWT_SECRET_KEY = 'super-secret-key'` 는 학습용이다.
이 키를 아는 사람은 아무 identity 로 유효한 토큰을 만들 수 있다.
실제 서비스에서는 코드 밖(환경 변수 등)에 두고 절대 노출하지 않는다.

### 8. 로그인 요청에 JSON 본문이 없으면

`LoginResource` 는 `data = request.get_json()` 뒤에 바로 `data.get(...)` 을 부른다.
JSON 이 아니라 `data` 가 `None` 으로 오는 경우라면 `None.get` 에서 `AttributeError` 가 나 서버 오류가 된다.
요청이 JSON 이 아닐 때 Flask 가 `None` 을 주는지 오류 응답을 바로 주는지는 버전에 따라 다르다. (확인 필요)

### 9. 파일 끝의 `print` 가 언제 실행되나

`print` 줄들은 `if __name__ == '__main__':` 블록 **밖**, 모듈 맨 끝에 있다.
다른 모듈이 이 파일을 import 하면 import 하는 순간 바로 찍힌다.
직접 실행하면 그 앞의 `app.run(debug=True)` 가 서버를 띄운 채 돌아오지 않으므로, 서버가 끝나야 그 뒤 줄에 닿는다.
`debug=True` 의 자동 리로드가 모듈을 한 번 더 읽는 방식 때문에 찍히는 횟수는 상황마다 다를 수 있다. (확인 필요)

### 10. 쓰지 않는 import

`jsonify` · `reqparse` · `get_jwt` 는 import 했지만 본문에서 쓰지 않는다.
Flask-RESTful 은 dict 반환을 JSON 으로 바꿔 주므로 `jsonify` 가 필요 없다.

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| HTTP 메서드 이름과 같은 이름의 메서드가 불린다 | Flask-RESTful (라이브러리 동작, 파이썬 언어와 무관) |
| `(dict, 숫자)` 반환이 본문 · 상태 코드가 된다 | Flask-RESTful |
| `get_or_404` 가 없으면 404 로 끝낸다 | Flask-SQLAlchemy (원본 팁) |
| `dump_only` · `load_only` · `partial` 의 의미 | marshmallow |
| `@jwt_required(refresh=True)` 는 refresh 토큰만 받는다 | Flask-JWT-Extended |
| 토큰 검사 실패 때의 상태 코드 · 메시지 | Flask-JWT-Extended 기본 오류 처리 — 버전에 따라 다를 수 있음 (확인 필요) |
| `ilike` 가 대소문자를 무시한다 | SQLAlchemy 가 DB 별 SQL 로 바꿔 구현 |
| `default=db.func.now()` 가 DB 시각 함수로 채워진다 | SQLAlchemy + 쓰는 DB |
| 해시 문자열의 형식 · 알고리즘 | werkzeug 버전 (확인 필요) |
| 응답 dict 의 키 순서가 넣은 순서대로다 | 파이썬 언어 (3.7 이상 dict 삽입 순서 보장) |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 요청 JSON 검사 | `schema.load()` + `ValidationError` 처리 | `request.get_json()['키']` 를 검사 없이 바로 씀 |
| 응답에서 비밀번호 숨기기 | `load_only=True` | 응답 dict 를 손으로 만들다 빠뜨리기 |
| 서버가 정하는 값(id · 작성자 · 시각) | `dump_only=True` + 서버에서 채움 | 요청 본문의 값을 그대로 믿기 |
| 일부 필드만 수정 | `load(…, partial=True)` + `data.get(키, 원래값)` | 전체 필드를 요구하는 load |
| 오래 로그인 유지 | 짧은 access + 긴 refresh | 만료가 긴 access 토큰 하나 |
| 남의 글 보호 | 메서드 안 작성자 비교 → 403 | `@jwt_required()` 만으로 끝내기 |
| 단건 조회 | `get_or_404` | `None` 을 dump 하기 |
| 비밀번호 저장 | `generate_password_hash` / `check_password_hash` | 평문 저장 · 평문 비교 |

## 핵심 문장

1. **`Resource` 클래스의 메서드 이름이 곧 HTTP 메서드다** — `add_resource` 로 URL 에 묶고, dict 나 `(dict, 상태)` 를 돌려준다.
2. **marshmallow 는 `load` 로 들어오는 것을 검사하고 `dump` 로 나가는 것을 고른다** — `dump_only` 는 응답에만, `load_only` 는 요청에만.
3. **access 토큰은 짧게, refresh 토큰은 길게** — refresh 로 새 access 를 받아 보안과 편의를 함께 얻는다.
4. **인증(`@jwt_required`)과 인가(작성자 비교)는 다른 문이다** — 401 과 403 으로 갈린다.
5. **`partial=True` 와 `data.get(키, 원래값)` 이 짝을 이뤄 부분 수정이 된다.**

## 관련 자료

- [flask-basics](../06-flask-basics/2-summary.md)
- [django-rest](../05-django-rest/2-summary.md)
- [oauth-jwt](../14-oauth-jwt/2-summary.md)
- 원본: study-site 항목 데이터 `data/python/web-frameworks.json` 의 `flask-api`

## 용어 풀이

- **Flask** — 파이썬 웹 프레임워크, 요청을 받아 응답을 돌려주는 앱을 만든다.
- **Flask-RESTful** — Flask 위에 `Resource` 클래스 방식 라우팅을 얹는 확장.
- **Resource** — 한 URL 을 맡고 HTTP 메서드 이름의 메서드를 가진 클래스.
- **add_resource** — `Resource` 클래스를 URL 패턴에 묶는 호출.
- **변수 컨버터** — `<int:post_id>` 처럼 URL 조각을 타입 변환해 인자로 넘기는 표기.
- **marshmallow** — 스키마로 직렬화와 입력 검증을 하는 라이브러리.
- **스키마** — 필드와 규칙을 적은 선언(`Schema` 하위 클래스).
- **load / dump** — load 는 입력을 검증해 dict 로, dump 는 객체를 응답용 dict 로.
- **직렬화** — 객체를 전송 가능한 형태로 바꾸는 일.
- **dump_only / load_only** — 응답에만 / 요청에만 쓰는 필드 표시.
- **partial** — 필수 필드가 빠져도 오류로 보지 않게 하는 load 옵션.
- **ValidationError** — 검증 실패 때 나는 예외, `messages` 에 필드별 오류가 있다.
- **@validates** — 특정 필드에 추가 검증을 다는 데코레이터.
- **fields.Method** — 스키마 메서드로 값을 계산하는 필드.
- **JWT** — 비밀 키로 서명한 identity · 만료 시각을 담은 토큰.
- **access 토큰** — 보호된 엔드포인트에 쓰는 짧은 수명의 토큰.
- **refresh 토큰** — 새 access 토큰을 받을 때만 쓰는 긴 수명의 토큰.
- **identity** — 토큰에 넣은 사용자 식별자, `get_jwt_identity()` 로 꺼낸다.
- **@jwt_required** — 유효한 토큰이 있어야 메서드를 부르게 하는 데코레이터.
- **해시** — 되돌릴 수 없는 지문 문자열, 비밀번호 저장에 쓴다.
- **인증 / 인가** — 누구인지 확인 / 해도 되는지 확인.
- **401 / 403 / 404** — 인증 실패 / 권한 없음 / 없음.
- **get_or_404** — Flask-SQLAlchemy 의 「없으면 404」 조회 메서드.
- **ORM** — DB 행을 파이썬 객체로 다루게 해 주는 층(SQLAlchemy).
- **relationship / backref** — 객체 사이 연결과 그 반대쪽 속성 자동 생성.
- **페이지네이션** — 결과를 쪽 단위로 나눠 주는 것.
- **ilike** — 대소문자를 무시하는 부분 일치 조건.
- **앱 컨텍스트** — 현재 앱 설정 · 확장에 접근할 수 있는 실행 범위.

## 더 들어가면

- SQLAlchemy 2.x 에서 `Query.get` 계열은 낡은(legacy) API 로 분류되고, Flask-SQLAlchemy 3.x 는 `db.get_or_404(Post, post_id)` 꼴을 권한다. (확인 필요)
- marshmallow 3 은 기본적으로 스키마에 없는 키(`unknown`)를 만나면 오류를 낸다. `dump_only` 필드를 요청에 넣는 것도 알 수 없는 키로 취급되어 오류가 될 수 있다. (확인 필요)
- `fields.Method` 에 역직렬화 메서드를 주지 않으면 load 때 그 필드는 사실상 무시되거나 dump 전용처럼 다뤄진다. (확인 필요)
- marshmallow 4 에서는 `@validates` 메서드가 받는 인자 꼴이 바뀌었다는 변경이 있다. (확인 필요)
- Flask-JWT-Extended 최신 판은 `identity`(JWT 의 `sub`)를 문자열로 요구하는 쪽으로 바뀌었다 — 이 코드가 `str(user.id)` 로 넣는 것과 맞물린다. (확인 필요)
- 기본 설정에서 토큰이 없으면 401, refresh 토큰을 access 자리에 내면 422 같은 다른 코드가 나온다고 알려져 있다. (확인 필요)
- `paginate` 는 기본값으로 범위를 벗어난 쪽 번호에 404 를 낸다(`error_out=True`). (확인 필요)
- Flask-RESTful 은 오래 업데이트가 뜸해, 최근에는 Flask 의 `MethodView` 나 다른 확장(예: flask-smorest)을 쓰는 경우도 많다. (확인 필요)
- 로그아웃 · 토큰 폐기는 이 코드에 없다 — Flask-JWT-Extended 는 차단 목록(blocklist) 콜백으로 폐기한 토큰을 거절하는 방법을 제공한다. (확인 필요)
